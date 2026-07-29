"""wrl_diff.py v0.1 -- Phase 3B-5: SemanticDiff over canonical WRL artifacts.

GPT-5.6's 3B sequence closes ergonomics with SemanticDiff + completion metadata.
This module is the SemanticDiff half: a STRUCTURED, canonical difference between
two Forge Semantic artifacts, keyed by the same canonical keys the rest of 3B
uses (object_id, edge triple).

The design mirror of every 3B slice: the diff is a PURE FUNCTION of two CANONICAL
artifacts and touches no identity. Phase 3B.5.1 splits it into two modes that
share one canonical structural core (`_diff_canonical`):

  * `semantic_diff(a, b)` -- SEALED. Both inputs are validated + canonicalized on
    the identity path (or accepted as SealedArtifacts); an invalid/unsupported
    artifact is REJECTED. Because both sides seal exactly as the identity spine
    does, the headline bridge law holds (proven in binding_run13):

        semantic_diff(a, b).is_empty() <=> semantic_artifact_id(a) == semantic_artifact_id(b)

    It covers EVERY top-level key that feeds the sealed bytes (ir_version,
    profile_id, semantic_policies, schemas, objects, edges), so an empty diff
    means identical deterministic bytes -> identical id.

  * `draft_diff(a, b)` -- TOLERANT. Canonicalizes for order/surface independence
    but does NOT validate legality, so it can diff drafts and future/unsupported
    profiles (reporting PROFILE_CHANGED / IR_VERSION_CHANGED). It makes NO
    identity claim.

Run inputs (claim batches) are NOT part of the semantic artifact (D3), so a
run-input-only edit yields an EMPTY diff in both modes.
"""
import os
import sys
from collections import namedtuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wrl_canonical as WC
import wrl_ir as W

DIFF_VERSION = "wrldiff.v1"

# ------------------------------------------------------------- change kinds
IR_VERSION_CHANGED = "IR_VERSION_CHANGED"
PROFILE_CHANGED = "PROFILE_CHANGED"
POLICY_CHANGED = "POLICY_CHANGED"
SCHEMA_CHANGED = "SCHEMA_CHANGED"
OBJECT_ADDED = "OBJECT_ADDED"
OBJECT_REMOVED = "OBJECT_REMOVED"
OBJECT_CHANGED = "OBJECT_CHANGED"
EDGE_ADDED = "EDGE_ADDED"
EDGE_REMOVED = "EDGE_REMOVED"


class Change(namedtuple("Change", "kind key detail")):
    """One semantic change. `key` is the canonical object_id (objects), the
    canonical `kind:src->dst` edge key (edges), or a directive/policy name.
    `detail` is a tuple of changed sub-field names (empty for add/remove)."""
    __slots__ = ()

    def render(self):
        base = "%s %s" % (self.kind, self.key)
        if self.detail:
            base += ": " + ", ".join(self.detail)
        return base


class SemanticDiff(namedtuple("SemanticDiff", "changes")):
    """The full ordered, deterministic set of semantic changes from a -> b."""
    __slots__ = ()

    def is_empty(self):
        return len(self.changes) == 0

    def of_kind(self, kind):
        return tuple(c for c in self.changes if c.kind == kind)

    def keys_of_kind(self, kind):
        return tuple(c.key for c in self.changes if c.kind == kind)

    def render(self):
        if not self.changes:
            return "(no semantic change)"
        return "\n".join(c.render() for c in self.changes)


def _edge_key(e):
    return "%s:%s->%s" % (e["kind"], e["src"], e["dst"])


def _object_field_changes(oa, ob):
    """The sorted tuple of changed field names between two object dicts (same
    object_id). `static_config` is compared per sub-key so a rotor edit reports
    `static_config.rotor`, not the whole config."""
    changed = []
    if oa.get("role") != ob.get("role"):
        changed.append("role")
    if oa.get("state_schema_ref") != ob.get("state_schema_ref"):
        changed.append("state_schema_ref")
    if oa.get("ports") != ob.get("ports"):
        changed.append("ports")
    ca = oa.get("static_config", {}) or {}
    cb = ob.get("static_config", {}) or {}
    for k in sorted(set(ca) | set(cb)):
        if ca.get(k) != cb.get(k):
            changed.append("static_config.%s" % (k,))
    return tuple(changed)


def _canonical_for_semantic(x):
    """The CANONICAL, VALIDATED dict of a raw artifact or a SealedArtifact for
    the sealed diff path. A raw dict is sealed (validate -> canonicalize ->
    validate), so an invalid or unsupported artifact is REJECTED here with its
    typed WrlValidationError -- the sealed diff never compares something that
    could not itself earn a SemanticArtifactID (Phase 3B.5.1)."""
    if isinstance(x, WC.SealedArtifact):
        return x.artifact
    canon, _blob = WC._seal(x)
    return canon


def _diff_canonical(ca, cb):
    """The pure structural diff of two ALREADY-CANONICAL artifact dicts. Covers
    every identity-bearing top-level key (ir_version, profile_id,
    semantic_policies, schemas, objects, edges)."""
    changes = []

    if ca.get("ir_version") != cb.get("ir_version"):
        changes.append(Change(IR_VERSION_CHANGED, "ir_version", ()))
    if ca.get("profile_id") != cb.get("profile_id"):
        changes.append(Change(PROFILE_CHANGED, "profile_id", ()))

    pa = ca.get("semantic_policies", {}) or {}
    pb = cb.get("semantic_policies", {}) or {}
    pol = tuple(k for k in sorted(set(pa) | set(pb)) if pa.get(k) != pb.get(k))
    if pol:
        changes.append(Change(POLICY_CHANGED, "semantic_policies", pol))

    sa = ca.get("schemas", {}) or {}
    sb = cb.get("schemas", {}) or {}
    sch = tuple(k for k in sorted(set(sa) | set(sb)) if sa.get(k) != sb.get(k))
    if sch:
        changes.append(Change(SCHEMA_CHANGED, "schemas", sch))

    oa = {o["object_id"]: o for o in ca.get("objects", [])}
    ob = {o["object_id"]: o for o in cb.get("objects", [])}
    for oid in sorted(set(oa) - set(ob)):
        changes.append(Change(OBJECT_REMOVED, oid, ()))
    for oid in sorted(set(ob) - set(oa)):
        changes.append(Change(OBJECT_ADDED, oid, ()))
    for oid in sorted(set(oa) & set(ob)):
        fc = _object_field_changes(oa[oid], ob[oid])
        if fc:
            changes.append(Change(OBJECT_CHANGED, oid, fc))

    ea = {_edge_key(e): e for e in ca.get("edges", [])}
    eb = {_edge_key(e): e for e in cb.get("edges", [])}
    for k in sorted(set(ea) - set(eb)):
        changes.append(Change(EDGE_REMOVED, k, ()))
    for k in sorted(set(eb) - set(ea)):
        changes.append(Change(EDGE_ADDED, k, ()))

    return SemanticDiff(tuple(changes))


# ---------------------------------------------------------- the two diff modes
def semantic_diff(a, b):
    """SEALED SemanticDiff: both inputs are validated + canonicalized on the
    identity path (or accepted as SealedArtifacts). An invalid or unsupported
    artifact is REJECTED with its typed WrlValidationError. Because both sides go
    through exactly the sealing canonicalization, the headline bridge law holds:

        semantic_diff(a, b).is_empty()  <=>  semantic_artifact_id(a) == semantic_artifact_id(b)

    Use this whenever the diff must speak about identity ("why did the id move?").
    It only ever compares artifacts that could themselves earn an id."""
    ca = _canonical_for_semantic(a)
    cb = _canonical_for_semantic(b)
    return _diff_canonical(ca, cb)


def draft_diff(a, b):
    """TOLERANT DraftDiff: both inputs are canonicalized for ORDER/surface
    independence but NOT validated for semantic legality, so it can diff drafts,
    future/unsupported profiles (reports PROFILE_CHANGED), unsupported ir_versions
    (IR_VERSION_CHANGED), and otherwise-unsealed edits. It makes NO identity
    claim -- an empty draft_diff does not imply a shared SemanticArtifactID for
    artifacts that would not seal. Use this for editor previews and pre-seal
    drafts."""
    ca = WC.canonicalize_artifact_v1(a)
    cb = WC.canonicalize_artifact_v1(b)
    return _diff_canonical(ca, cb)


# Backward-compatible tolerant alias (pre-3B.5.1 name). `diff_artifacts` is the
# DRAFT (tolerant) diff; prefer `semantic_diff`/`draft_diff` explicitly.
def diff_artifacts(a, b):
    """Deprecated alias for `draft_diff` (tolerant). Kept for callers written
    before the 3B.5.1 sealed/tolerant split."""
    return draft_diff(a, b)


def diff_graphs(ga, gb):
    """SEALED SemanticDiff between two canonical WRL graphs. `graph_to_ir` already
    seals each graph, so the identity bridge holds over graphs."""
    return semantic_diff(W.graph_to_ir(ga), W.graph_to_ir(gb))


def diff_sources(sa, sb, parser=W.parse_wrl_core):
    """SEALED SemanticDiff between two WRL source strings under one parser."""
    return diff_graphs(parser(sa), parser(sb))


def draft_diff_sources(sa, sb, parser=W.parse_wrl_core):
    """TOLERANT DraftDiff between two WRL source strings (no identity claim)."""
    return draft_diff(W.graph_to_ir(parser(sa)), W.graph_to_ir(parser(sb)))


# ------------------------------------------------------------ change locators
# A SemanticDiff answers "what changed"; an editor also needs "where". No new
# key plumbing is required for this, and that is not an accident: `Change.key`
# is ALREADY the canonical object_id / `kind:src->dst` edge key, which is
# exactly what `wrl_spans.WrlSourceMap` indexes on. The two modules were built
# against the same canonical vocabulary, so they compose directly.
#
# The location is a PURE SIDECAR (the 3B-1/3B-3 discipline): `Change` itself is
# unchanged and still carries no span, so nothing here can perturb a diff, a
# bridge law, or an identity. Hand these functions an AUTHORED-coordinate source
# map (see `wrl_sugar.authored_source_map`) and every located change is reported
# in authored coordinates -- the locator needs no sugar awareness of its own.
LocatedChange = namedtuple("LocatedChange", "change span origin side")

# which SIDE of the diff a change can be pointed at. A removal exists only in
# the BEFORE text; an addition only in the AFTER text. Pointing a removal at the
# after-text would be a category error -- the construct is not there any more.
BEFORE = "before"
AFTER = "after"

_REMOVED_KINDS = (OBJECT_REMOVED, EDGE_REMOVED)
# the diff names identity-bearing top-level KEYS; the span scan names the
# surface DIRECTIVE that carries them. Only `profile` has a surface line.
_DIRECTIVE_OF = {"profile_id": "profile"}


def _origin_for(change, source_map):
    if source_map is None:
        return None
    if change.kind in (OBJECT_ADDED, OBJECT_REMOVED, OBJECT_CHANGED):
        return source_map.origin_for_object(change.key)
    if change.kind in (EDGE_ADDED, EDGE_REMOVED):
        # Change.key is ALREADY the canonical `kind:src->dst` edge key, which is
        # precisely how WrlSourceMap indexes edges -- no reconstruction needed.
        return source_map.edges().get(change.key)
    head = _DIRECTIVE_OF.get(change.key)
    return source_map.origin_for_directive(head) if head else None


def locate_changes(diff, before_map=None, after_map=None):
    """Every Change in `diff`, paired with the SourceSpan it should be reported
    against, as a tuple of `LocatedChange`.

    Removals are located in `before_map`, everything else in `after_map`. A
    change whose construct has no origin (or whose side was not supplied) still
    appears, with `span=None` -- a diff must never silently drop a change just
    because it could not be located.

    If the supplied maps are in AUTHORED coordinates, so is every span returned;
    this function is deliberately unaware of sugar."""
    out = []
    for c in diff.changes:
        side = BEFORE if c.kind in _REMOVED_KINDS else AFTER
        sm = before_map if side == BEFORE else after_map
        o = _origin_for(c, sm)
        out.append(LocatedChange(c, o.span if o else None, o, side))
    return tuple(out)
