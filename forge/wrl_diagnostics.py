"""wrl_diagnostics.py v0.1 -- Phase 3B-3: stable diagnostics.

GPT-5.6's 3B priority ruling leads broad 3B with "canonical formatter + source
spans". 3B-1 shipped the span sidecar (wrl_spans), 3B-2 the canonical formatter
(wrl_format); 3B-3 is STABLE DIAGNOSTICS -- a typed rejection rendered as a
portable record:

    Diagnostic {code, message, primary_span, related_span, canonical_object_id}

A diagnostic is a PURE SIDECAR, exactly like the 3B-1 span map. The authoritative
accept/reject verdict is STILL owned by the untouched validators in wrl_canonical
(`validate_graph`, `_validate_config`) and the parsers in wrl_ir -- this module
never re-decides anything. It only DECORATES an already-authoritative
`WrlValidationError` with the source spans that 3B-1 captured, by locating the
offending object/edge in the parsed graph. Because the code and message come
straight from the real exception (never re-worded) and the spans come from the
independent 3B-1 scan, a diagnostic can never perturb any identity, and its
`code`/`canonical_object_id` are STABLE under reformatting (only the spans move).

If a locator cannot pin the offending element (e.g. a parse-time rejection before
a graph exists), the span/object-id degrade to None -- the diagnostic is still a
valid record (code + message), honest about what it could resolve.
"""
import os
import sys
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wrl_ir as W
import wrl_canonical as WC
import wrl_spans as S
import wrl_sugar as SG

DIAG_VERSION = "diag.v1"
DEFAULT_FILE_ID = S.DEFAULT_FILE_ID


# ------------------------------------------------------------ the record
class Diagnostic(namedtuple(
        "Diagnostic",
        "code message primary_span related_span canonical_object_id "
        "primary_locator related_locator field_path")):
    """One typed rejection with its source location. `code` is a STABLE machine
    code (the wrl_canonical validation contract); `message` is the authoritative
    human message VERBATIM from the validator; `primary_span` locates the
    offending construct; `related_span` optionally locates a second construct
    that co-defines the error (e.g. the first declaration of a duplicated id, or
    the competing controller edge); `canonical_object_id` is the canonical key
    of the element the diagnostic is about (stable across reformatting).

    Phase 3B.5.1: the record ALSO carries the CANONICAL SEMANTIC LOCATORS the
    validator attached to its WrlValidationError -- `primary_locator` /
    `related_locator` are `wrl_canonical.ObjectKey` / `EdgeKey` (or None) and
    `field_path` is a dotted canonical path like `static_config.rotor`. The spans
    above are these locators MAPPED through the WrlSourceMap; a canvas consumer
    (e.g. Spinner Bench) can highlight directly from the locator without a span."""
    __slots__ = ()

    def render(self):
        """A stable, deterministic one-line rendering (same source -> identical
        string). Spans render as file:line:col (1-based line, 0-based col)."""
        out = "%s: %s" % (self.code, self.message)
        if self.primary_span is not None:
            out += " [%s]" % _fmt_span(self.primary_span)
        if self.canonical_object_id is not None:
            out += " (object %s)" % (self.canonical_object_id,)
        if self.related_span is not None:
            out += "; related [%s]" % _fmt_span(self.related_span)
        return out


def _fmt_span(sp):
    return "%s:%d:%d" % (sp.file_id, sp.start_line, sp.start_column)


# ------------------------------------------------------------- locators
# Each locator re-finds the FIRST offending element for one stable code, over
# the already-parsed graph + the 3B-1 source map. It DECORATES; it never alters
# the verdict (which the authoritative validator already delivered). Returns
# (canonical_object_id, primary_span, related_span); any field may be None.
def _node_origins(sm, name):
    return [o for o in sm.origins
            if o.construct_kind == S.NODE and o.canonical_object_id == name]


def _loc_duplicate_id(g, sm):
    seen = set()
    for _role, name, _cfg in g.nodes:
        if name in seen:
            occ = _node_origins(sm, name)
            primary = occ[1].span if len(occ) > 1 else (
                occ[0].span if occ else None)
            related = occ[0].span if occ else None
            return name, primary, related
        seen.add(name)
    return None, None, None


def _loc_unknown_endpoint(g, sm):
    names = {n for _r, n, _c in g.nodes}
    for kind, s, d in g.edges:
        miss = s if s not in names else (d if d not in names else None)
        if miss is not None:
            o = sm.origin_for_edge(kind, s, d)
            return miss, (o.span if o else None), None
    return None, None, None


def _loc_illegal_port_pair(g, sm):
    role_of = {n: r for r, n, _c in g.nodes}
    for kind, s, d in g.edges:
        if s not in role_of or d not in role_of:
            continue
        out_port, in_port = WC.EDGE_PORTS[kind]
        edge_o = sm.origin_for_edge(kind, s, d)
        edge_span = edge_o.span if edge_o else None
        if out_port not in WC.PORTS[role_of[s]]["out"]:
            no = sm.origin_for_object(s)
            return s, edge_span, (no.span if no else None)
        if in_port not in WC.PORTS[role_of[d]]["in"]:
            no = sm.origin_for_object(d)
            return d, edge_span, (no.span if no else None)
    return None, None, None


def _loc_controller_conflict(g, sm):
    first = {}
    for kind, s, d in g.edges:
        key = (kind, d)
        if key in first:
            o = sm.origin_for_edge(kind, s, d)
            fk, fs, fd = first[key]
            fo = sm.origin_for_edge(fk, fs, fd)
            return d, (o.span if o else None), (fo.span if fo else None)
        first[key] = (kind, s, d)
    return None, None, None


def _loc_bad_config(g, sm):
    """Reuse the AUTHORITATIVE per-node validator to find the offending node --
    no logic is duplicated: the node that raises IS the one the graph validator
    flagged (WRL_CLOCK_RANGE / WRL_NUMERIC_RANGE / config WRL_UNSUPPORTED_FEATURE)."""
    for role, name, cfg in g.nodes:
        try:
            WC._validate_config(role, name, cfg)
        except WC.WrlValidationError:
            o = sm.origin_for_object(name)
            return name, (o.span if o else None), None
    return None, None, None


_LOCATORS = {
    WC.WRL_DUPLICATE_ID: _loc_duplicate_id,
    WC.WRL_UNKNOWN_ENDPOINT: _loc_unknown_endpoint,
    WC.WRL_ILLEGAL_PORT_PAIR: _loc_illegal_port_pair,
    WC.WRL_CONTROLLER_CONFLICT: _loc_controller_conflict,
    WC.WRL_CLOCK_RANGE: _loc_bad_config,
    WC.WRL_NUMERIC_RANGE: _loc_bad_config,
}


def _locate(code, g, sm):
    loc = _LOCATORS.get(code)
    if loc is None or g is None:
        return None, None, None
    try:
        return loc(g, sm)
    except Exception:            # a decorator must never mask the real verdict
        return None, None, None


# ------------------------------------------------- 3B.5.1 locator-driven maps
# The validator now attaches CANONICAL semantic locators to its error. For most
# codes we map those directly through the source map -- diagnostics consumes the
# grammar's locators rather than re-deriving them. Two codes (DUPLICATE_ID,
# CONTROLLER_CONFLICT) need spans for TWO elements of the SAME canonical kind
# (two occurrences of one id / two competing edges into one target), which a
# single ObjectKey/EdgeKey cannot express, so they keep the dedicated scan.
_SCAN_ONLY = {WC.WRL_DUPLICATE_ID, WC.WRL_CONTROLLER_CONFLICT}


def _map_locator(loc, sm):
    """A canonical ObjectKey/EdgeKey -> its source span (or None)."""
    if isinstance(loc, WC.ObjectKey):
        o = sm.origin_for_object(loc.object_id)
        return o.span if o else None
    if isinstance(loc, WC.EdgeKey):
        o = sm.origin_for_edge(loc.kind, loc.src, loc.dst)
        return o.span if o else None
    return None


def _oid_from_locators(e):
    """The canonical object id a diagnostic is 'about', from its locators: the
    primary object, else a related object, else the endpoint named by an edge
    locator's src/dst field path."""
    p, r = e.primary_locator, e.related_locator
    if isinstance(p, WC.ObjectKey):
        return p.object_id
    if isinstance(r, WC.ObjectKey):
        return r.object_id
    if isinstance(p, WC.EdgeKey) and e.field_path in ("src", "dst"):
        return getattr(p, e.field_path)
    return None


def _resolve(e, g, sm):
    """(canonical_object_id, primary_span, related_span) for an error. Prefers
    the validator's attached locators; falls back to the graph scan for the two
    two-element codes and for any error that carries no locator (parse-time)."""
    if e.code in _SCAN_ONLY or getattr(e, "primary_locator", None) is None:
        return _locate(e.code, g, sm)
    return (_oid_from_locators(e),
            _map_locator(e.primary_locator, sm),
            _map_locator(e.related_locator, sm))


def _diag(e, g, sm):
    """Build the Diagnostic for an authoritative error: spans resolved via
    `_resolve`, the raw canonical locators carried straight from the error."""
    oid, prim, rel = _resolve(e, g, sm)
    return Diagnostic(e.code, e.message, prim, rel, oid,
                      getattr(e, "primary_locator", None),
                      getattr(e, "related_locator", None),
                      getattr(e, "field_path", None))


# ------------------------------------------------------------- public API
def _diagnose(src, parser, scanner, file_id):
    sm = scanner(src, file_id)                 # 3B-1 scan is verdict-independent
    try:
        g = parser(src)
    except WC.WrlValidationError as e:          # parse-time reject (no graph yet)
        return (_diag(e, None, sm),)
    try:
        WC.validate_graph(g)
    except WC.WrlValidationError as e:          # authoritative structural reject
        return (_diag(e, g, sm),)
    return ()                                   # clean: no diagnostics


def diagnose_core(src, file_id=DEFAULT_FILE_ID):
    """WRL Core surface -> a tuple of Diagnostics (empty == clean). The graph is
    built by the UNTOUCHED authoritative parser/validator; spans come from the
    3B-1 scan. Never enters any identity."""
    return _diagnose(src, W.parse_wrl_core, S._scan_core_spans, file_id)


def diagnose_bootstrap(src, file_id=DEFAULT_FILE_ID):
    """Bootstrap surface -> a tuple of Diagnostics (empty == clean)."""
    return _diagnose(src, W.parse_wrl_bootstrap, S._scan_bootstrap_spans, file_id)


# ------------------------------------------------- the sugar-aware surface
# A generated-coordinate diagnostic is not a smaller problem than a missing
# one -- it is a WORSE one, because it looks authoritative while pointing at a
# line the author never wrote (and, after value sugar, frequently at a column
# past the end of that line). So the sugared mouth does not merely CARRY the
# remapping seam, it is defined by it: every span leaves this module in
# AUTHORED coordinates or not at all.
#
# The verdict is still owned entirely by the untouched validators. Remapping
# moves only `primary_span` / `related_span`; `code`, `message`, the canonical
# locators and `canonical_object_id` are all identity-side and pass through
# verbatim, which is why a sugared diagnostic and its explicit twin agree on
# everything except where they point.
def _remapped(diags, sugar_map):
    """Every Diagnostic's spans, moved from GENERATED to AUTHORED coordinates."""
    return tuple(d._replace(
        primary_span=(None if d.primary_span is None
                      else sugar_map.remap_span(d.primary_span)),
        related_span=(None if d.related_span is None
                      else sugar_map.remap_span(d.related_span)))
        for d in diags)


def _sugar_diag(e, src, file_id):
    """A PREPASS rejection -> a Diagnostic located on the authored line.

    There is no graph and no desugared text at this point, so there are no
    canonical locators to carry; the record degrades honestly to code + message
    + the authored span, exactly as a parse-time rejection already does."""
    span = SG.authored_span_for_line(src, SG.sugar_failure_line(src), file_id)
    return Diagnostic(e.code, e.message, span, None, None, None, None, None)


def diagnose_sugared(src, file_id=DEFAULT_FILE_ID):
    """SUGARED WRL Core surface -> a tuple of Diagnostics in AUTHORED
    coordinates (empty == clean).

    Three failure tiers, all typed, none of them re-decided here:

      prepass   the sugar itself is malformed or out of bounds. Located by
                `wrl_sugar.sugar_failure_line`; no graph exists yet.
      parse     the DESUGARED text is not parseable.
      structural  the graph is built but the authoritative validator rejects it
                -- including a rejection CAUSED by an expansion (a generated id
                colliding with an explicit one, a fan-out that becomes an
                illegal fan-in). Those are the interesting ones: the offending
                element is text the author never typed, so without the remap the
                diagnostic points into generated coordinates."""
    try:
        dtext, sugar_map = SG.desugar_core_mapped(src)
    except WC.WrlValidationError as e:
        return (_sugar_diag(e, src, file_id),)
    return _remapped(
        _diagnose(dtext, W.parse_wrl_core, S._scan_core_spans, file_id),
        sugar_map)


def diagnose_legacy_document(src, file_id=DEFAULT_FILE_ID):
    """Pre-v0.4-0 COMBINED document -> a tuple of Diagnostics.

    The legacy twin of `diagnose_core` (L-0 Q2). Without it, diagnosing a
    combined document would report the document-boundary rejection INSTEAD of
    the duplicate id or bad port the author actually wants to see -- one
    structural complaint masking every real one."""
    return _diagnose(src, W.parse_wrl_legacy_document, S._scan_core_spans,
                     file_id)
