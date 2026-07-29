"""wrl_spans.py v0.1 -- Phase 3B-1: source spans + origin mapping.

GPT-5.6's 3B priority ruling leads broad 3B with "canonical formatter + source
spans". 3B-1 is the span layer: parsing produces source information ALONGSIDE --
but strictly OUTSIDE -- the semantic graph.

    SourceSpan   {file_id, start_offset, end_offset,
                  start_line, start_column, end_line, end_column}
    SourceOrigin {canonical_object_id, construct_kind, span}
    WrlSourceMap keyed by canonical object_id / canonical edge key / claim key

HARD INVARIANT (the whole point of the sidecar): spans and filenames NEVER enter
the SemanticArtifactID / CompilePlanDigest / BackendArtifactID. This module does
NOT touch wrl_ir's parsers or the canonical graph -- the authoritative graph is
still built by the untouched `parse_wrl_bootstrap` / `parse_wrl_core`, and the
span pass is an INDEPENDENT scan over the same text. Because the graph is built
by the identity-critical path with zero changes, capturing spans provably cannot
perturb any identity (proven in binding_run8, S1-S12).

Bridge: a canonical object_id keys the SAME element across all four surfaces --
    source span  <->  WrlGraph node/edge  <->  Forge IR object/edge  <->  canvas
because the IR object carries `object_id`/`role` and the canvas node carries
`object_id` at its semantic top level. So `origin_for_object(oid)` and
`origin_for_edge(kind, src, dst)` resolve straight through to the IR and canvas
by shared key; no separate cross-index is needed.
"""
import os
import re
import sys
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wrl_ir as W
from wrl_ir import (
    parse_wrl_bootstrap, parse_wrl_core, parse_wrl_legacy_document, lower_graph,
    _ROLE_TOKEN, _EDGE_TAG, _EPOCH_RE, _EDGE_RE, _NODE_RE,
)

SPANS_VERSION = "spans.v1"

# construct kinds carried by a SourceOrigin
NODE = "node"
EDGE = "edge"
CLAIM = "claim"
DIRECTIVE = "directive"

DEFAULT_FILE_ID = "<wrl>"


# --------------------------------------------------------- value objects
class SourceSpan(namedtuple(
        "SourceSpan",
        "file_id start_offset end_offset "
        "start_line start_column end_line end_column")):
    """A half-open character range in one source file. `file_id` is an opaque
    label (filename/handle); it is presentation metadata and MUST NOT enter any
    identity. Offsets are 0-based absolute character indices into the file text;
    lines are 1-based; columns are 0-based within a physical line."""
    __slots__ = ()

    def contains(self, offset):
        return self.start_offset <= offset < self.end_offset


class SourceOrigin(namedtuple(
        "SourceOrigin", "canonical_object_id construct_kind span")):
    """Ties a canonical key (object_id, canonical edge key, claim key, or
    directive head) to the SourceSpan it was parsed from. `construct_kind` is
    one of NODE / EDGE / CLAIM / DIRECTIVE."""
    __slots__ = ()


def edge_key(kind, src, dst):
    """The canonical, deterministic key for an edge origin. Mirrors the
    canonical edge triple used by graph_to_ir (kind, src, dst)."""
    return "%s:%s->%s" % (kind, src, dst)


# ----------------------------------------------------------- the source map
class WrlSourceMap(object):
    """Read-only sidecar: the origins captured for one parse, indexed by their
    canonical keys. Lives entirely outside the semantic graph."""

    __slots__ = ("file_id", "_origins", "_by_object", "_by_edge",
                 "_by_claim", "_by_directive")

    def __init__(self, file_id, origins):
        object.__setattr__(self, "file_id", file_id)
        object.__setattr__(self, "_origins", tuple(origins))
        by_object, by_edge, by_claim, by_directive = {}, {}, {}, {}
        for o in origins:
            if o.construct_kind == NODE:
                by_object[o.canonical_object_id] = o
            elif o.construct_kind == EDGE:
                by_edge[o.canonical_object_id] = o
            elif o.construct_kind == CLAIM:
                by_claim[o.canonical_object_id] = o
            elif o.construct_kind == DIRECTIVE:
                by_directive[o.canonical_object_id] = o
        object.__setattr__(self, "_by_object", by_object)
        object.__setattr__(self, "_by_edge", by_edge)
        object.__setattr__(self, "_by_claim", by_claim)
        object.__setattr__(self, "_by_directive", by_directive)

    def __setattr__(self, n, v):
        raise AttributeError("WrlSourceMap is read-only (cannot set %r)" % (n,))

    def __delattr__(self, n):
        raise AttributeError("WrlSourceMap is read-only (cannot del %r)" % (n,))

    # -- lookups -------------------------------------------------------------
    @property
    def origins(self):
        return self._origins

    def origin_for_object(self, object_id):
        return self._by_object.get(object_id)

    def origin_for_edge(self, kind, src, dst):
        return self._by_edge.get(edge_key(kind, src, dst))

    def origin_for_claim(self, claim_key):
        return self._by_claim.get(claim_key)

    def origin_for_directive(self, head):
        return self._by_directive.get(head)

    def objects(self):
        return dict(self._by_object)

    def edges(self):
        return dict(self._by_edge)

    def origin_at(self, offset):
        """Reverse lookup: the (first) origin whose span covers `offset` --
        the primitive behind canvas-click/cursor -> canonical element."""
        for o in self._origins:
            if o.span.contains(offset):
                return o
        return None


# --------------------------------------------------------- span arithmetic
def _line_starts(text):
    starts, off = [], 0
    for ln in text.splitlines(keepends=True):
        starts.append(off)
        off += len(ln)
    return starts


def _content_span(file_id, raw_line, line_no, line_off, comment_marker):
    """Span of the meaningful content of one physical line (comment stripped,
    surrounding whitespace excluded). Returns None for blank/comment-only
    lines. `#` is NEVER a comment marker for the core surface (it is content),
    so the caller passes comment_marker accordingly."""
    code = raw_line.split(comment_marker, 1)[0] if comment_marker else raw_line
    stripped = code.strip()
    if not stripped:
        return None
    start_col = len(code) - len(code.lstrip())
    end_col = start_col + len(stripped)
    return SourceSpan(file_id, line_off + start_col, line_off + end_col,
                      line_no, start_col, line_no, end_col), stripped


# ----------------------------------------------------- bootstrap span scan
def _scan_bootstrap_spans(text, file_id):
    """Independent span pass over the bootstrap surface. Mirrors the head
    dispatch of parse_wrl_bootstrap ONLY to classify a line and recover its
    canonical key; it never builds or mutates the graph. Lines it cannot map
    are skipped (the authoritative parser has already validated the text)."""
    starts = _line_starts(text)
    raw_lines = text.splitlines()
    origins = []
    epoch_counter = {}
    for i, raw in enumerate(raw_lines):
        got = _content_span(file_id, raw, i + 1, starts[i], "#")
        if got is None:
            continue
        span, line = got
        tok = line.split()
        head = tok[0]
        if head in ("profile", "periods"):
            origins.append(SourceOrigin(head, DIRECTIVE, span))
        elif head in ("pulser", "relay", "door", "spinner", "orb"):
            origins.append(SourceOrigin(tok[1], NODE, span))
        elif head == "wire":
            origins.append(SourceOrigin(
                edge_key("SignalWire", tok[1], tok[3]), EDGE, span))
        elif head == "socket":
            origins.append(SourceOrigin(
                edge_key("SocketControl", tok[1], tok[3]), EDGE, span))
        elif head == "epoch":
            m = re.match(r"epoch\s+(\d+)\s*:", line)
            if m:
                ep = int(m.group(1))
                idx = epoch_counter.get(ep, 0)
                epoch_counter[ep] = idx + 1
                origins.append(SourceOrigin(
                    "claim:e%d:i%d" % (ep, idx), CLAIM, span))
    return WrlSourceMap(file_id, origins)


# --------------------------------------------------------- core span scan
def _scan_core_spans(text, file_id):
    """Independent span pass over the WRL Core surface. `;` is the comment
    marker; `#` is preserved as content."""
    starts = _line_starts(text)
    raw_lines = text.splitlines()
    origins = []
    epoch_counter = {}
    for i, raw in enumerate(raw_lines):
        got = _content_span(file_id, raw, i + 1, starts[i], ";")
        if got is None:
            continue
        span, line = got
        if line.startswith("profile "):
            origins.append(SourceOrigin("profile", DIRECTIVE, span))
            continue
        if line.startswith("periods "):
            origins.append(SourceOrigin("periods", DIRECTIVE, span))
            continue
        me = _EPOCH_RE.match(line)
        if me:
            ep = int(me.group(1))
            idx = epoch_counter.get(ep, 0)
            epoch_counter[ep] = idx + 1
            origins.append(SourceOrigin(
                "claim:e%d:i%d" % (ep, idx), CLAIM, span))
            continue
        if "-->" in line:
            m = _EDGE_RE.match(line)
            if m and m.group(2) in _EDGE_TAG:
                origins.append(SourceOrigin(
                    edge_key(_EDGE_TAG[m.group(2)], m.group(1), m.group(3)),
                    EDGE, span))
            continue
        m = _NODE_RE.match(line)
        if m and m.group(1) in _ROLE_TOKEN:
            origins.append(SourceOrigin(m.group(2), NODE, span))
    return WrlSourceMap(file_id, origins)


# ---------------------------------------------------------- public parsers
def parse_bootstrap_with_spans(text, file_id=DEFAULT_FILE_ID):
    """Bootstrap surface -> (canonical WrlGraph, WrlSourceMap). The graph is
    produced by the UNTOUCHED authoritative parser; the source map is a
    separate scan. Spans/file_id never reach the graph."""
    return parse_wrl_bootstrap(text), _scan_bootstrap_spans(text, file_id)


def parse_core_with_spans(text, file_id=DEFAULT_FILE_ID):
    """WRL Core surface -> (canonical WrlGraph, WrlSourceMap)."""
    return parse_wrl_core(text), _scan_core_spans(text, file_id)


def lower_bootstrap_with_spans(text, file_id=DEFAULT_FILE_ID):
    """Bootstrap text -> (LoweredProgram, WrlSourceMap). The LoweredProgram is
    byte-identical to `lower_program(text)` (S1); the source map rides
    alongside it, outside the sealed artifact."""
    g, sm = parse_bootstrap_with_spans(text, file_id)
    return lower_graph(g), sm


def lower_core_with_spans(text, file_id=DEFAULT_FILE_ID):
    """WRL Core text -> (LoweredProgram, WrlSourceMap)."""
    g, sm = parse_core_with_spans(text, file_id)
    return lower_graph(g), sm


# ----------------------------------------------------- legacy document mouths
# Mirrors of the two above for pre-v0.4-0 COMBINED documents. Every layer that
# exposes a "core" mouth gets an explicitly-named legacy twin (L-0 Q2), so a
# caller that needs run-input syntax has to ask for it by name. The span scan is
# unchanged -- only the parser mouth differs.
def parse_legacy_document_with_spans(text, file_id=DEFAULT_FILE_ID):
    """Pre-v0.4-0 COMBINED document -> (canonical WrlGraph, WrlSourceMap)."""
    return (parse_wrl_legacy_document(text), _scan_core_spans(text, file_id))


def lower_legacy_document_with_spans(text, file_id=DEFAULT_FILE_ID):
    """Pre-v0.4-0 COMBINED document -> (LoweredProgram, WrlSourceMap)."""
    g, sm = parse_legacy_document_with_spans(text, file_id)
    return lower_graph(g), sm


# ------------------------------------------------- origin <-> IR resolvers
def resolve_ir_object(artifact, source_map, object_id):
    """(IR object dict, SourceOrigin) for a canonical object_id -- the concrete
    span <-> Forge IR object bridge. Returns (obj, origin); either may be None
    if absent."""
    obj = next((o for o in artifact["objects"]
                if o["object_id"] == object_id), None)
    return obj, source_map.origin_for_object(object_id)


def resolve_ir_edge(artifact, source_map, kind, src, dst):
    """(IR edge dict, SourceOrigin) for a canonical edge triple."""
    e = next((e for e in artifact["edges"]
              if (e["kind"], e["src"], e["dst"]) == (kind, src, dst)), None)
    return e, source_map.origin_for_edge(kind, src, dst)


def unresolved_ir_elements(artifact, source_map):
    """Every canonical IR object_id / edge triple that has NO origin span --
    empty tuple means the source map fully covers the artifact's identity
    surface (the S6/S7 completeness check)."""
    missing = []
    for o in artifact["objects"]:
        if source_map.origin_for_object(o["object_id"]) is None:
            missing.append(("object", o["object_id"]))
    for e in artifact["edges"]:
        if source_map.origin_for_edge(e["kind"], e["src"], e["dst"]) is None:
            missing.append(("edge", edge_key(e["kind"], e["src"], e["dst"])))
    return tuple(missing)
