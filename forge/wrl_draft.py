"""wrl_draft.py v0.1 -- WorldDraftV1: the revisioned world-editing draft store
(Spinner Bench v0.4-1, GPT-5.6's frozen v0.4 edit semantics).

v0.4-0 separated the three documents at the identity layer. v0.4-1 makes the
WORLD editable through a draft, WITHOUT ever silently replacing the active sealed
world. The contract is deliberately conservative (GPT-5.6):

  * WorldDraftV1  -- a mutable working copy of a world's objects + edges, carrying
    its own monotonic `semantic_revision` and a pointer to the last COMMITTED
    world (`active_semantic_id`). It is NOT itself an identity; the identity is
    still the sealed SemanticArtifactID of whatever graph it currently holds.
  * GraphEditV1   -- one edit against a specific `base_revision`. The full v0.4
    op set is now open: `SetObjectConfig` (v0.4-1, replace one object's
    static_config); the three TOPOLOGY ops (v0.4-2) `AddEdge` / `RemoveEdge` /
    `ReconnectEdge` (each carries an `edge` = {kind, src, dst}; ReconnectEdge also
    a `to` edge); and the OBJECT-LIFECYCLE ops (v0.4-3) `AddObject` (carries an
    `object` = {object_id, role, static_config}) / `RemoveObject` (carries a
    `target` object_id). Every op only enforces its OWN precondition (the object/
    edge is / isn't already present); structural legality of the RESULT -- an
    unknown role, a bad static_config, an unknown endpoint, an illegal port pair,
    a controller conflict, or an edge left DANGLING by a non-cascading
    RemoveObject -- is deferred to the seal, so an illegal edit yields an
    invalid-but-editable candidate rather than a raise. RemoveObject is
    deliberately NON-cascading: it drops only the object, so removing a still-
    wired node leaves a dangling edge the seal rejects (`WRL_UNKNOWN_ENDPOINT`);
    the honest way to delete a connected node is to RemoveEdge its wires first.
  * CommitDraftV1 -- the EXPLICIT promotion of the draft's current candidate to
    become the new active sealed world. Editing never auto-commits.

Load-bearing rules (all proven in binding_run17):

  1. Exact CAS. `apply_edit`/`commit_draft` require `base_revision == current
     semantic_revision`; a stale base is rejected `WRL_STALE_DRAFT` with NO
     auto-merge.
  2. Idempotent edit_id. Re-applying the SAME `edit_id` (a client retry) returns
     the ORIGINAL result and does NOT advance the revision a second time -- the
     idempotency check runs BEFORE the CAS check, so a retry of an
     already-applied edit is a no-op even though the revision has moved on.
  3. Candidate sealing. Every applied edit re-seals the working graph and records
     the resulting `candidate_semantic_id` (or, if the edit makes the graph
     invalid, marks the candidate invalid + records the typed error). An invalid
     draft REMAINS EDITABLE -- you can keep editing to repair it -- but it can
     never be committed and never replaces the active sealed world.
  4. Explicit, checked commit. `commit_draft` requires the CAS base_revision AND
     an `expected_candidate_semantic_id` that matches the current candidate
     (optimistic concurrency on the *content*, not just the counter); it refuses
     an invalid candidate. Only then does `active_semantic_id` advance.
  5. Monotone undo to the exact prior id. `undo` restores the working graph to
     its state before the last edit, so `candidate_semantic_id` returns to the
     EXACT prior SemanticArtifactID -- but `semantic_revision` still INCREMENTS
     (undo is a forward revision that happens to restore old bytes; the counter
     never decrements, so a concurrent stale base can never alias a revived one).

The store is a pure DATA structure over the existing identity spine
(`wrl_ir.lower_graph` / `wrl_canonical`); it introduces NO runtime construct and
cannot perturb any sealed world it does not explicitly commit.

v0.4-4b adds ONE new draft transaction, `ReplaceWorldSourceV1` (GPT-5.6's ruling):
a free-form multi-change WRL Core TEXT edit, kept DELIBERATELY SEPARATE from the
small typed `GraphEditV1` ops (there is NO `GraphEditV1.ReplaceGraph`). A text edit
begins as source, may fail syntactically before any graph exists, may alter many
objects/edges at once, carries source spans + diagnostics, and a user expects one
paste to equal one undo. `replace_world_source` therefore:
  * is idempotent on `replace_id` (checked BEFORE the CAS) and CASes exactly on
    `base_revision` (WRL_STALE_DRAFT, no auto-merge / no decomposition);
  * REJECTS legacy run-input syntax (`periods N`, `[epoch:N] ...`) with a typed
    `WRL_WORLD_SOURCE_HAS_SCENARIO` (world authoring and ScenarioV1 authoring are
    now separate surfaces -- it never silently discards or relocates scenario
    data; the compat importer may still accept those forms);
  * on a SYNTAX failure leaves the draft, its ids, revision, and layout UNTOUCHED
    (the raw editor buffer is not the authoritative graph);
  * detects a semantic NO-OP (formatting / comments only -> identical canonical
    bytes) and does NOT advance the revision or create an undo entry;
  * otherwise replaces the whole working graph ATOMICALLY -- one snapshot, one
    revision increment, one undo entry -- then seals a candidate. A source that
    parses but produces an ILLEGAL graph (dangling endpoint, controller conflict)
    still advances once, keeps the invalid-but-editable working graph, returns a
    null candidate + typed diagnostics, and leaves the active sealed world
    runnable, exactly as the GraphEditV1 invalid-candidate model.

v0.5-0 (Source Surface Closure, GPT-5.6's ruling) closes a correctness gap in the
above: `replace_world_source` now DESUGARS approved WRL sugar (concise clocks,
named rotors) before parsing, so a paste of the ergonomic surface Applies directly
instead of leaking a raw `KeyError: 'period'`. The order is load-bearing: SCAN the
RAW source for forbidden run-input syntax FIRST, THEN desugar, THEN parse the
desugared core, THEN seal -- the scenario scan runs before desugaring so run-input
tokens are never lost by a source-to-source rewrite. Every desugar/parse failure is
converted to a stable TYPED diagnostic (WRL_SUGAR_MALFORMED / a WrlUnsupported
code); no raw Python exception may cross the endpoint. Desugar is a source pre-pass,
NOT a compiler gate: a sugar spelling and its numeric expansion seal to the SAME
candidate SemanticArtifactID, so a sugar-only re-expression of the current graph is
a genuine semantic no-op.
"""
import copy

import wrl_canonical as WC
import wrl_format as F
import wrl_ir as W
import wrl_spans as SP
import wrl_sugar as SG

DRAFT_VERSION = "world-draft.v1"
EDIT_VERSION = "graph-edit.v1"
COMMIT_VERSION = "commit-draft.v1"
REPLACE_VERSION = "replace-world-source.v1"

WRL_BAD_DRAFT = "WRL_BAD_DRAFT"
WRL_BAD_EDIT = "WRL_BAD_EDIT"
WRL_STALE_DRAFT = "WRL_STALE_DRAFT"
WRL_COMMIT_MISMATCH = "WRL_COMMIT_MISMATCH"
WRL_INVALID_CANDIDATE = "WRL_INVALID_CANDIDATE"
WRL_WORLD_SOURCE_HAS_SCENARIO = "WRL_WORLD_SOURCE_HAS_SCENARIO"
WRL_SUGAR_MALFORMED = "WRL_SUGAR_MALFORMED"
# Slice B commit 3. A WorldDraft represents a world as two plain lists --
# `objects` and `edges` -- and that pair is what the whole authoring workspace is
# built on: the undo snapshots, the ForgeProjectV2 `draft` block, the v0.6-0
# recovery journal, the canvas reconciliation in wrl_converge. World content that
# is NEITHER an object NOR an edge is invisible to all of it.
#
# Commit 2 could leave this alone: no surface could put a route into a draft, so
# the gap was unreachable. Commit 3 opens the `~~` surface and makes it
# reachable, and the failure takes the worst available shape -- opening a
# route-bearing world as a draft does not crash and does not error, it quietly
# yields the route-FREE world, which is itself a perfectly legal world with a
# perfectly good (different) SemanticArtifactID. Measured before the guard was
# written: the one-route world dropped to `sem-d3e555be...`, which is exactly
# binding_run47's route-free 1-mailbox pin. So commit 3 closes the gap in the
# same commit that opens it.
#
# The guard REFUSES rather than widening the draft. Widening would mean a new
# revision of every persisted authoring document (ForgeProjectV2, the recovery
# journal, the draft-state ledger) and that is a document-format change, not a
# language change -- flagged to GPT-5.6 rather than taken here.
WRL_DRAFT_LOSSY_WORLD = "WRL_DRAFT_LOSSY_WORLD"

# the four terminal states of a ReplaceWorldSourceV1 transaction
REPLACE_STATUS = ("syntax_error", "semantic_noop", "semantic_invalid",
                  "candidate_valid")

# v0.4-1: SetObjectConfig · v0.4-2: the three TOPOLOGY edits · v0.4-3: object
# lifecycle (AddObject/RemoveObject). The full v0.4 GraphEditV1 op set is now open.
EDIT_OPERATIONS = ("SetObjectConfig", "AddEdge", "RemoveEdge", "ReconnectEdge",
                   "AddObject", "RemoveObject")
_DEFERRED_OPERATIONS = ()

_EDGE_SPEC_FIELDS = ("kind", "src", "dst")
_OBJECT_SPEC_FIELDS = ("object_id", "role", "static_config")


# ------------------------------------------------------------ graph <-> lists
def _graph_from(objects, edges, profile):
    """Build a WrlGraph from the draft's plain object/edge lists (no run
    inputs). static_config tuples are rebuilt from JSON-plain lists by the
    canonicalizer, so we hand the config through verbatim."""
    g = W.WrlGraph()
    g.profile = profile
    g.nodes = [(o["role"], o["object_id"], dict(o["static_config"]))
               for o in objects]
    g.edges = [(e["kind"], e["src"], e["dst"]) for e in edges]
    return g


def _seal(objects, edges, profile):
    """Seal the working graph. Returns (candidate_semantic_id, None) when valid,
    or (None, error_string) when the graph is not a legal world -- an invalid
    candidate never raises here; it is recorded so the draft stays editable."""
    try:
        prog = W.lower_graph(_graph_from(objects, edges, profile))
        return prog.semantic_artifact_id, None
    except WC.WrlUnsupported as ex:
        code = getattr(ex, "code", "WRL_UNSUPPORTED_FEATURE")
        return None, "%s: %s" % (code, ex)


def _draft_loss(g, objects, edges, profile):
    """Does the draft's `(objects, edges)` representation hold everything the
    graph `g` says? Returns a diagnostic dict when it does NOT, else None.

    A COMPUTED round-trip, deliberately naming no construct. The alternative --
    `if g.routes: refuse` -- would be a hand-listed inventory of what the draft
    cannot hold, i.e. a fork of the graph's own field set, and it would go stale
    silently: the next world construct that is neither an object nor an edge
    would be dropped exactly as routes were, and this guard would say nothing.
    Asking "does what we kept still seal to what we were given?" cannot go
    stale, because it is the loss itself that is being measured.

    It is the same door `wrl_legacy.export_canvas_graph_v1` uses to refuse a
    lossy canvas export, and for the same reason: that door learned about routes
    in commit 2 without being edited at all.

    A graph that is not a LEGAL world is not this function's business -- the
    seal reports that, with a better diagnostic than "something was lost". So an
    unlowerable `g` returns None and the ordinary rejection path runs."""
    try:
        want = W.lower_graph(g).semantic_artifact_id
    except WC.WrlUnsupported:
        return None
    got, err = _seal(objects, edges, profile)
    if err is None and got == want:
        return None
    return {"code": WRL_DRAFT_LOSSY_WORLD,
            "message": "this world does not survive the draft representation: "
                       "it seals to %s, but the draft holds only objects and "
                       "edges and what it holds seals to %s. The draft is "
                       "REFUSED rather than silently editing a different world."
                       % (want, got if err is None else "(%s)" % err)}


def _objects_from_artifact(art):
    return [{"object_id": o["object_id"], "role": o["role"],
             "static_config": copy.deepcopy(o["static_config"])}
            for o in art["objects"]]


def _edges_from_artifact(art):
    return [{"kind": e["kind"], "src": e["src"], "dst": e["dst"]}
            for e in art["edges"]]


# ------------------------------------------------------------- the draft type
class WorldDraft:
    """A revisioned, in-memory editing session for ONE world. Construct via
    `new_draft`. All mutation goes through `apply_edit` / `commit_draft` /
    `undo`; `to_document()` projects the frozen WorldDraftV1 public shape."""

    def __init__(self, draft_id, profile_id, base_semantic_id, objects, edges):
        self.draft_id = draft_id
        self.profile_id = profile_id
        self.base_semantic_id = base_semantic_id
        self.active_semantic_id = base_semantic_id      # last COMMITTED world
        self.semantic_revision = 0
        self.objects = objects
        self.edges = edges
        cand, err = _seal(objects, edges, profile_id)
        self.candidate_semantic_id = cand
        self.candidate_error = err
        # undo history: snapshots taken BEFORE each applied edit
        self._history = []
        # idempotency ledger: edit_id -> the recorded result of its FIRST apply
        self._applied = {}
        # idempotency ledger for ReplaceWorldSourceV1 transactions that MUTATED
        # (a syntax-error / no-op replace advances nothing and is not recorded)
        self._replaced = {}

    # -- snapshots ---------------------------------------------------------
    def _snapshot(self):
        return {"semantic_revision": self.semantic_revision,
                "objects": copy.deepcopy(self.objects),
                "edges": copy.deepcopy(self.edges),
                "candidate_semantic_id": self.candidate_semantic_id,
                "candidate_error": self.candidate_error}

    def _result(self):
        """The public per-operation result (also the idempotency-cached value)."""
        return {"draft_id": self.draft_id,
                "semantic_revision": self.semantic_revision,
                "candidate_semantic_id": self.candidate_semantic_id,
                "candidate_valid": self.candidate_error is None,
                "candidate_error": self.candidate_error,
                "active_semantic_id": self.active_semantic_id}

    # -- projection --------------------------------------------------------
    def to_document(self):
        """The frozen WorldDraftV1 public document (no private history/ledger)."""
        return {"draft_version": DRAFT_VERSION,
                "draft_id": self.draft_id,
                "semantic_revision": self.semantic_revision,
                "base_semantic_id": self.base_semantic_id,
                "active_semantic_id": self.active_semantic_id,
                "candidate_semantic_id": self.candidate_semantic_id,
                "candidate_valid": self.candidate_error is None,
                "profile_id": self.profile_id,
                "objects": copy.deepcopy(self.objects),
                "edges": copy.deepcopy(self.edges)}


# ------------------------------------------------------------- construction
def new_draft(program_or_artifact, draft_id):
    """Open a WorldDraftV1 over a sealed world. Accepts a LoweredProgram (uses
    its sealed artifact) or a raw artifact dict. The draft starts at revision 0
    with the world's exact SemanticArtifactID as both base and active id."""
    if hasattr(program_or_artifact, "sealed_artifact"):
        sealed = program_or_artifact.sealed_artifact
        art = sealed.artifact
        base = program_or_artifact.semantic_artifact_id
    else:
        art = program_or_artifact
        base = WC.SealedArtifact(art).semantic_id
    draft = WorldDraft(draft_id, art["profile_id"], base,
                       _objects_from_artifact(art), _edges_from_artifact(art))
    # The loss check is FREE here: the constructor already sealed the
    # reconstructed lists, so "did the draft keep this world?" is just "is the
    # candidate of an UNEDITED draft its own base?". Stating it costs one
    # comparison and turns a silent world substitution into a typed refusal.
    if draft.candidate_error is not None \
            or draft.candidate_semantic_id != base:
        WC._fail(WRL_DRAFT_LOSSY_WORLD,
                 "world %s does not survive the draft representation (the "
                 "reconstructed draft seals to %s); the draft holds only "
                 "objects and edges, so this world cannot be opened for "
                 "editing without silently becoming a different one"
                 % (base, draft.candidate_semantic_id
                    if draft.candidate_error is None
                    else "(%s)" % draft.candidate_error),
                 field_path="base_semantic_id")
    return draft


# ------------------------------------------------------------- edit validation
def _req(cond, code, msg, field=None):
    if not cond:
        WC._fail(code, msg, field_path=field)


def validate_edit_v1(edit):
    """Structural gate for a GraphEditV1 (typed WRL_BAD_EDIT). Checks the
    envelope + that the operation is one of the open v0.4 ops (SetObjectConfig,
    the three topology edits, AddObject/RemoveObject) and that its per-op payload
    is well SHAPED; structural legality of the resulting graph is the seal's job.
    """
    _req(isinstance(edit, dict), WRL_BAD_EDIT, "edit must be an object")
    _req(edit.get("edit_version") == EDIT_VERSION, WRL_BAD_EDIT,
         "unknown edit_version %r (only %s)"
         % (edit.get("edit_version"), EDIT_VERSION))
    for k in ("edit_id", "draft_id", "base_revision", "operation"):
        _req(k in edit, WRL_BAD_EDIT, "edit missing field %r" % k, k)
    _req(isinstance(edit["edit_id"], str) and edit["edit_id"], WRL_BAD_EDIT,
         "edit_id must be a non-empty string", "edit_id")
    _req(isinstance(edit["base_revision"], int)
         and not isinstance(edit["base_revision"], bool)
         and edit["base_revision"] >= 0, WRL_BAD_EDIT,
         "base_revision must be a non-negative int", "base_revision")
    op = edit["operation"]
    _req(isinstance(op, dict) and isinstance(op.get("kind"), str), WRL_BAD_EDIT,
         "operation must be an object with a string kind", "operation")
    kind = op["kind"]
    if kind in _DEFERRED_OPERATIONS:
        _req(False, WRL_BAD_EDIT,
             "operation %r is frozen in the v0.4 model but deferred past v0.4-1 "
             "(v0.4-1 admits only %s)" % (kind, list(EDIT_OPERATIONS)),
             "operation.kind")
    _req(kind in EDIT_OPERATIONS, WRL_BAD_EDIT,
         "unknown operation kind %r (v0.4-1 admits %s)"
         % (kind, list(EDIT_OPERATIONS)), "operation.kind")
    if kind == "SetObjectConfig":
        _req(isinstance(op.get("target"), str) and op["target"], WRL_BAD_EDIT,
             "SetObjectConfig.target must be a non-empty object_id",
             "operation.target")
        _req(isinstance(op.get("static_config"), dict), WRL_BAD_EDIT,
             "SetObjectConfig.static_config must be an object",
             "operation.static_config")
    elif kind in ("AddEdge", "RemoveEdge"):
        _validate_edge_spec(op.get("edge"), "operation.edge")
    elif kind == "ReconnectEdge":
        _validate_edge_spec(op.get("edge"), "operation.edge")
        _validate_edge_spec(op.get("to"), "operation.to")
    elif kind == "AddObject":
        _validate_object_spec(op.get("object"), "operation.object")
    elif kind == "RemoveObject":
        _req(isinstance(op.get("target"), str) and op["target"], WRL_BAD_EDIT,
             "RemoveObject.target must be a non-empty object_id",
             "operation.target")
    return edit


def _validate_object_spec(spec, path):
    """Structural gate for an object record {object_id, role, static_config}
    (typed WRL_BAD_EDIT). The role need not be a supported role + the config
    need not be legal here -- that is the seal's job -- so this only checks the
    record's SHAPE: string object_id/role + dict static_config, no stray keys."""
    _req(isinstance(spec, dict), WRL_BAD_EDIT, "%s must be an object" % path,
         path)
    for k in ("object_id", "role"):
        _req(isinstance(spec.get(k), str) and spec[k], WRL_BAD_EDIT,
             "%s.%s must be a non-empty string" % (path, k), "%s.%s" % (path, k))
    _req(isinstance(spec.get("static_config"), dict), WRL_BAD_EDIT,
         "%s.static_config must be an object" % path, "%s.static_config" % path)
    _req(set(spec) == set(_OBJECT_SPEC_FIELDS), WRL_BAD_EDIT,
         "%s has unknown field(s) %s (object = {object_id, role, static_config})"
         % (path, sorted(set(spec) - set(_OBJECT_SPEC_FIELDS))), path)


def _validate_edge_spec(spec, path):
    """Structural gate for an edge record {kind, src, dst} (typed WRL_BAD_EDIT).
    The endpoints need not exist yet + the port pair need not be legal here --
    that is the seal's job -- so this only checks the record's SHAPE."""
    _req(isinstance(spec, dict), WRL_BAD_EDIT, "%s must be an object" % path,
         path)
    for k in _EDGE_SPEC_FIELDS:
        _req(k in spec, WRL_BAD_EDIT, "%s missing field %r" % (path, k), path)
        _req(isinstance(spec[k], str) and spec[k], WRL_BAD_EDIT,
             "%s.%s must be a non-empty string" % (path, k), "%s.%s" % (path, k))
    _req(set(spec) == set(_EDGE_SPEC_FIELDS), WRL_BAD_EDIT,
         "%s has unknown field(s) %s (edge = {kind, src, dst})"
         % (path, sorted(set(spec) - set(_EDGE_SPEC_FIELDS))), path)


def _edge_tuple(spec):
    return (spec["kind"], spec["src"], spec["dst"])


def _edge_present(edges, spec):
    t = _edge_tuple(spec)
    return any((e["kind"], e["src"], e["dst"]) == t for e in edges)


def _apply_operation(objects, edges, op):
    """Apply a validated operation to COPIES of the object + edge lists, returning
    the new (objects, edges). Structural legality of the RESULT (unknown config
    keys, unknown endpoints, illegal port pairs, controller conflicts, ...) is
    deferred to the seal, so this only enforces each op's OWN precondition (the
    target/edge is or is not already present)."""
    kind = op["kind"]
    if kind == "SetObjectConfig":
        target = op["target"]
        new = []
        found = False
        for o in objects:
            if o["object_id"] == target:
                found = True
                new.append({"object_id": o["object_id"], "role": o["role"],
                            "static_config": copy.deepcopy(op["static_config"])})
            else:
                new.append(copy.deepcopy(o))
        _req(found, WRL_BAD_EDIT,
             "SetObjectConfig target %r is not an object in this draft" % target,
             "operation.target")
        return new, copy.deepcopy(edges)
    if kind == "AddEdge":
        _req(not _edge_present(edges, op["edge"]), WRL_BAD_EDIT,
             "AddEdge %s is already an edge in this draft"
             % (_edge_tuple(op["edge"]),), "operation.edge")
        return copy.deepcopy(objects), [copy.deepcopy(e) for e in edges] + [
            {"kind": op["edge"]["kind"], "src": op["edge"]["src"],
             "dst": op["edge"]["dst"]}]
    if kind == "RemoveEdge":
        _req(_edge_present(edges, op["edge"]), WRL_BAD_EDIT,
             "RemoveEdge %s is not an edge in this draft"
             % (_edge_tuple(op["edge"]),), "operation.edge")
        t = _edge_tuple(op["edge"])
        kept = [copy.deepcopy(e) for e in edges
                if (e["kind"], e["src"], e["dst"]) != t]
        return copy.deepcopy(objects), kept
    if kind == "ReconnectEdge":
        _req(_edge_present(edges, op["edge"]), WRL_BAD_EDIT,
             "ReconnectEdge source edge %s is not an edge in this draft"
             % (_edge_tuple(op["edge"]),), "operation.edge")
        old, to = _edge_tuple(op["edge"]), _edge_tuple(op["to"])
        _req(old == to or not _edge_present(edges, op["to"]), WRL_BAD_EDIT,
             "ReconnectEdge target edge %s is already an edge in this draft"
             % (to,), "operation.to")
        kept = [copy.deepcopy(e) for e in edges
                if (e["kind"], e["src"], e["dst"]) != old]
        kept.append({"kind": op["to"]["kind"], "src": op["to"]["src"],
                     "dst": op["to"]["dst"]})
        return copy.deepcopy(objects), kept
    if kind == "AddObject":
        oid = op["object"]["object_id"]
        _req(not any(o["object_id"] == oid for o in objects), WRL_BAD_EDIT,
             "AddObject object_id %r is already an object in this draft" % oid,
             "operation.object")
        added = {"object_id": oid, "role": op["object"]["role"],
                 "static_config": copy.deepcopy(op["object"]["static_config"])}
        return [copy.deepcopy(o) for o in objects] + [added], copy.deepcopy(edges)
    if kind == "RemoveObject":
        # NON-cascading: drop ONLY the object. Any edge left dangling is caught
        # by the seal (WRL_UNKNOWN_ENDPOINT), keeping the op's precondition to
        # its own concern -- the target must exist.
        target = op["target"]
        _req(any(o["object_id"] == target for o in objects), WRL_BAD_EDIT,
             "RemoveObject target %r is not an object in this draft" % target,
             "operation.target")
        kept = [copy.deepcopy(o) for o in objects if o["object_id"] != target]
        return kept, copy.deepcopy(edges)
    # unreachable: validate_edit_v1 already gated the kind
    WC._fail(WRL_BAD_EDIT, "unhandled operation kind %r" % kind)


# ------------------------------------------------------------------- apply
def apply_edit(draft, edit):
    """Apply a GraphEditV1 to a WorldDraft. Order of checks (load-bearing):

      1. structural validation (typed WRL_BAD_EDIT);
      2. draft_id match;
      3. IDEMPOTENCY -- if this edit_id was already applied, return its ORIGINAL
         recorded result verbatim (a retry never advances the revision twice),
         checked BEFORE the CAS so a retry of a now-old base still no-ops;
      4. exact CAS -- base_revision must equal the current semantic_revision,
         else WRL_STALE_DRAFT (no auto-merge);
      5. apply the operation, re-seal, advance the monotone revision, and record
         the candidate id (valid) or the typed error (invalid -- draft stays
         editable).

    Returns the per-operation result dict."""
    validate_edit_v1(edit)
    _req(edit["draft_id"] == draft.draft_id, WRL_BAD_EDIT,
         "edit targets draft %r but this is draft %r"
         % (edit["draft_id"], draft.draft_id), "draft_id")
    # (3) idempotency BEFORE CAS
    if edit["edit_id"] in draft._applied:
        return dict(draft._applied[edit["edit_id"]])
    # (4) exact CAS
    if edit["base_revision"] != draft.semantic_revision:
        WC._fail(WRL_STALE_DRAFT,
                 "edit base_revision %d != current semantic_revision %d "
                 "(no auto-merge; re-base the edit on the current revision)"
                 % (edit["base_revision"], draft.semantic_revision),
                 field_path="base_revision")
    # (5) snapshot for undo, then apply + re-seal + advance
    draft._history.append(draft._snapshot())
    draft.objects, draft.edges = _apply_operation(
        draft.objects, draft.edges, edit["operation"])
    cand, err = _seal(draft.objects, draft.edges, draft.profile_id)
    draft.candidate_semantic_id = cand
    draft.candidate_error = err
    draft.semantic_revision += 1
    res = draft._result()
    draft._applied[edit["edit_id"]] = dict(res)
    return res


# ------------------------------------------------------------------- undo
def undo(draft):
    """Restore the working graph to its state BEFORE the last applied edit. The
    candidate id returns to the EXACT prior SemanticArtifactID, but the
    semantic_revision INCREMENTS (undo is a forward revision that restores old
    bytes; the counter is monotone and never decrements). Raises WRL_BAD_DRAFT
    if there is nothing to undo."""
    _req(bool(draft._history), WRL_BAD_DRAFT, "nothing to undo")
    snap = draft._history.pop()
    draft.objects = snap["objects"]
    draft.edges = snap["edges"]
    draft.candidate_semantic_id = snap["candidate_semantic_id"]
    draft.candidate_error = snap["candidate_error"]
    draft.semantic_revision += 1                    # monotone; never decrements
    return draft._result()


# ------------------------------------------------------------------- commit
def validate_commit_v1(commit):
    _req(isinstance(commit, dict), WRL_BAD_EDIT, "commit must be an object")
    _req(commit.get("commit_version") == COMMIT_VERSION, WRL_BAD_EDIT,
         "unknown commit_version %r (only %s)"
         % (commit.get("commit_version"), COMMIT_VERSION))
    for k in ("draft_id", "base_revision", "expected_candidate_semantic_id"):
        _req(k in commit, WRL_BAD_EDIT, "commit missing field %r" % k, k)
    return commit


def commit_draft(draft, commit):
    """Promote the draft's current candidate to become the new active sealed
    world. Requires (a) draft_id match, (b) exact CAS on base_revision, (c) a
    VALID candidate, and (d) `expected_candidate_semantic_id` equal to the
    current candidate id (optimistic concurrency on CONTENT, so a caller can
    never commit a candidate different from the one they reviewed). On success
    `active_semantic_id` advances to the candidate and the sealed world is
    returned; the draft stays open for further editing atop the same revision.
    Raises WRL_STALE_DRAFT / WRL_INVALID_CANDIDATE / WRL_COMMIT_MISMATCH."""
    validate_commit_v1(commit)
    _req(commit["draft_id"] == draft.draft_id, WRL_BAD_EDIT,
         "commit targets draft %r but this is draft %r"
         % (commit["draft_id"], draft.draft_id), "draft_id")
    if commit["base_revision"] != draft.semantic_revision:
        WC._fail(WRL_STALE_DRAFT,
                 "commit base_revision %d != current semantic_revision %d"
                 % (commit["base_revision"], draft.semantic_revision),
                 field_path="base_revision")
    if draft.candidate_error is not None:
        WC._fail(WRL_INVALID_CANDIDATE,
                 "cannot commit an invalid candidate (%s); repair the draft first"
                 % draft.candidate_error, field_path="candidate_semantic_id")
    if commit["expected_candidate_semantic_id"] != draft.candidate_semantic_id:
        WC._fail(WRL_COMMIT_MISMATCH,
                 "commit expected candidate %r but the current candidate is %r"
                 % (commit["expected_candidate_semantic_id"],
                    draft.candidate_semantic_id),
                 field_path="expected_candidate_semantic_id")
    draft.active_semantic_id = draft.candidate_semantic_id
    sealed = WC.SealedArtifact(
        W.lower_graph(_graph_from(draft.objects, draft.edges,
                                  draft.profile_id)).sealed_artifact.artifact)
    return {"draft_id": draft.draft_id,
            "semantic_revision": draft.semantic_revision,
            "active_semantic_id": draft.active_semantic_id,
            "sealed_artifact": sealed}


# ============================================ ReplaceWorldSourceV1 (v0.4-4b)
def validate_replace_v1(request):
    """Structural gate for a ReplaceWorldSourceV1 request (typed WRL_BAD_EDIT).
    Checks only the envelope shape -- the SOURCE itself is parsed + judged by
    `replace_world_source` (syntax / scenario / semantic legality are its job)."""
    _req(isinstance(request, dict), WRL_BAD_EDIT, "replace request must be an "
         "object")
    _req(request.get("replace_version") == REPLACE_VERSION, WRL_BAD_EDIT,
         "unknown replace_version %r (only %s)"
         % (request.get("replace_version"), REPLACE_VERSION))
    for k in ("replace_id", "draft_id", "base_revision", "source"):
        _req(k in request, WRL_BAD_EDIT, "replace request missing field %r" % k,
             k)
    _req(isinstance(request["replace_id"], str) and request["replace_id"],
         WRL_BAD_EDIT, "replace_id must be a non-empty string", "replace_id")
    _req(isinstance(request["base_revision"], int)
         and not isinstance(request["base_revision"], bool)
         and request["base_revision"] >= 0, WRL_BAD_EDIT,
         "base_revision must be a non-negative int", "base_revision")
    _req(isinstance(request["source"], str), WRL_BAD_EDIT,
         "source must be a string", "source")
    return request


def _lists_from_graph(g):
    """Parsed WrlGraph -> the draft's plain object/edge lists (no run inputs).
    The static_config is handed through verbatim; the seal canonicalizes it, so
    a freshly-parsed graph seals to the SAME id as the canonical artifact form."""
    objects = [{"object_id": name, "role": role,
                "static_config": copy.deepcopy(cfg)}
               for (role, name, cfg) in g.nodes]
    edges = [{"kind": k, "src": s, "dst": d} for (k, s, d) in g.edges]
    return objects, edges


def _scan_world_source_scenario(source):
    """Detect legacy run-input (scenario) syntax in WORLD source. Returns a
    diagnostic dict when found, else None. Strips `;` comments exactly like
    `parse_wrl_core`, so scenario tokens inside comments never trip it."""
    for i, raw in enumerate(source.splitlines(), start=1):
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        head = line.split()[0]
        if head == "periods":
            return {"code": WRL_WORLD_SOURCE_HAS_SCENARIO, "line": i,
                    "message": "line %d: world source must not carry the "
                    "run-input `periods` directive -- author run duration in a "
                    "ScenarioV1, not the world source" % i}
        if W._EPOCH_RE.match(line):
            return {"code": WRL_WORLD_SOURCE_HAS_SCENARIO, "line": i,
                    "message": "line %d: world source must not carry a run-input "
                    "`[epoch:N]` claim -- author claims in a ScenarioV1, not the "
                    "world source" % i}
    return None


def _err_diag(err):
    """Turn a `CODE: message` seal-error string into a diagnostic record."""
    code, _, msg = err.partition(": ")
    return {"code": code, "message": msg or err}


def _exc_diag(ex):
    return {"code": getattr(ex, "code", "WRL_UNSUPPORTED_FEATURE"),
            "message": getattr(ex, "message", str(ex))}


def _draft_diff_lists(old_objs, old_edges, new_objs, new_edges):
    """A tolerant structural DraftDiff over the plain object/edge lists (makes NO
    identity claim; safe on invalid graphs). Reports added/removed/config-changed
    object ids and added/removed edge keys."""
    om = {o["object_id"]: o for o in old_objs}
    nm = {o["object_id"]: o for o in new_objs}
    changed = sorted(oid for oid in (set(om) & set(nm))
                     if (om[oid]["role"], om[oid]["static_config"])
                     != (nm[oid]["role"], nm[oid]["static_config"]))
    oek = {(e["kind"], e["src"], e["dst"]) for e in old_edges}
    nek = {(e["kind"], e["src"], e["dst"]) for e in new_edges}
    return {"objects_added": sorted(set(nm) - set(om)),
            "objects_removed": sorted(set(om) - set(nm)),
            "objects_changed": changed,
            "edges_added": sorted(list(e) for e in (nek - oek)),
            "edges_removed": sorted(list(e) for e in (oek - nek))}


def _spans_for(source):
    """Best-effort source map for a successfully-parsed world source (a pure
    sidecar; never on the identity path). Returns the WrlSourceMap or None."""
    try:
        _, smap = SP.parse_core_with_spans(source)
        return smap
    except WC.WrlUnsupported:
        return None


def _canonical_wrl(draft):
    return F.format_wrl_core(_graph_from(draft.objects, draft.edges,
                                         draft.profile_id))


def _replace_result(draft, status, candidate, diagnostics, draft_diff,
                    source_map, canonical_wrl):
    return {"replace_version": REPLACE_VERSION,
            "replace_id": None,          # filled by replace_world_source
            "draft_id": draft.draft_id,
            "semantic_revision": draft.semantic_revision,
            "status": status,
            "semantic_noop": status == "semantic_noop",
            "candidate_semantic_id": candidate,
            "candidate_valid": (status in ("semantic_noop", "candidate_valid")),
            "canonical_wrl": canonical_wrl,
            "diagnostics": diagnostics,
            "draft_diff": draft_diff,
            "source_map": source_map,
            "active_semantic_id": draft.active_semantic_id}


def replace_world_source(draft, request):
    """Apply a ReplaceWorldSourceV1 (a free-form multi-change TEXT edit) to a
    WorldDraft. Order of checks (load-bearing, mirroring apply_edit):

      1. envelope validation (typed WRL_BAD_EDIT) + draft_id match;
      2. IDEMPOTENCY -- a repeated `replace_id` (only recorded for a MUTATING
         transaction) returns its ORIGINAL result verbatim, checked BEFORE CAS;
      3. exact CAS -- base_revision must equal the current semantic_revision
         (WRL_STALE_DRAFT; no auto-merge / no decomposition);
      4. process the COMPLETE source (scan raw -> desugar -> parse core):
           * legacy run-input syntax in the RAW source -> `syntax_error` +
             WRL_WORLD_SOURCE_HAS_SCENARIO, draft UNTOUCHED (scanned BEFORE
             desugar so run-input tokens are never lost by a rewrite);
           * a desugar or parse failure -> `syntax_error` (typed
             WRL_SUGAR_MALFORMED / WRL_UNSUPPORTED_FEATURE, never a raw Python
             exception), draft UNTOUCHED (the raw buffer is not the graph);
             approved WRL sugar (concise clocks, named rotors) applies DIRECTLY
             via a source-to-source pre-pass -- sugar and its numeric twin seal
             to the SAME candidate;
      5. semantic NO-OP (identical canonical bytes) -> `semantic_noop`, draft
         UNTOUCHED (formatting/comments are genuinely non-semantic);
      6. otherwise replace the working graph ATOMICALLY -- one snapshot, one undo
         entry, one revision increment -- then seal a candidate:
           * valid   -> `candidate_valid`  + candidate id;
           * invalid -> `semantic_invalid` + null candidate + typed diagnostics
             (draft stays editable; the active sealed world stays runnable).

    Returns a ReplaceWorldSourceResult dict."""
    validate_replace_v1(request)
    _req(request["draft_id"] == draft.draft_id, WRL_BAD_EDIT,
         "replace targets draft %r but this is draft %r"
         % (request["draft_id"], draft.draft_id), "draft_id")
    # (2) idempotency BEFORE CAS -- only MUTATING replaces are recorded, so a
    # retry of a mutating replace (whose base is now stale) still no-ops here.
    # v0.6-0 cleanup (GPT-5.6): an idempotent REPLAY returns the recorded SEMANTIC
    # result but DELIBERATELY drops the `source_map` -- a read-only, non-identity,
    # regenerable presentation sidecar. The client already received the map on the
    # ORIGINAL mutating response; a replay is a defensive no-op. Nulling it here
    # makes a replay STRUCTURALLY IDENTICAL whether it happens in-memory (the map
    # is still live) or after a Save + restart (the durable ledger already stripped
    # it via `_durable_replace_ledger`) -- one frozen replay shape, no
    # before/after-restart divergence.
    if request["replace_id"] in draft._replaced:
        replay = dict(draft._replaced[request["replace_id"]])
        if "source_map" in replay:
            replay["source_map"] = None
        return replay
    # (3) exact CAS
    if request["base_revision"] != draft.semantic_revision:
        WC._fail(WRL_STALE_DRAFT,
                 "replace base_revision %d != current semantic_revision %d "
                 "(no auto-merge; re-base the replacement on the current "
                 "revision)" % (request["base_revision"], draft.semantic_revision),
                 field_path="base_revision")
    source = request["source"]

    def finish(res):
        res["replace_id"] = request["replace_id"]
        return res

    # (4a) SCAN the RAW source for run-input (scenario) syntax FIRST -- before
    # desugaring -- so forbidden run-input tokens can never be silently lost by a
    # source-to-source rewrite. Draft UNTOUCHED.
    scen = _scan_world_source_scenario(source)
    if scen is not None:
        return finish(_replace_result(
            draft, "syntax_error", draft.candidate_semantic_id, [scen],
            None, None, None))
    # (4b) DESUGAR the raw world source, then PARSE the desugared core. Approved
    # WRL sugar (concise clocks, named rotors) applies DIRECTLY -- desugar is a
    # source-to-source pre-pass, NOT a compiler gate; a sugar spelling and its
    # numeric expansion seal to the same candidate. Every desugar/parse failure
    # becomes a stable TYPED diagnostic -- no raw Python exception (KeyError,
    # ValueError, IndexError) may cross this endpoint. Draft UNTOUCHED on failure.
    try:
        core = SG.desugar_core(source)
    except WC.WrlUnsupported as ex:
        return finish(_replace_result(
            draft, "syntax_error", draft.candidate_semantic_id, [_exc_diag(ex)],
            None, None, None))
    except (ValueError, KeyError, IndexError) as ex:
        return finish(_replace_result(
            draft, "syntax_error", draft.candidate_semantic_id,
            [{"code": WRL_SUGAR_MALFORMED,
              "message": "malformed WRL sugar: %s" % ex}],
            None, None, None))
    try:
        g = W.parse_wrl_core(core)
    except WC.WrlUnsupported as ex:
        return finish(_replace_result(
            draft, "syntax_error", draft.candidate_semantic_id, [_exc_diag(ex)],
            None, None, None))
    except (ValueError, KeyError, IndexError) as ex:
        return finish(_replace_result(
            draft, "syntax_error", draft.candidate_semantic_id,
            [{"code": WRL_SUGAR_MALFORMED,
              "message": "malformed WRL source: %s" % ex}],
            None, None, None))
    # spans over the DESUGARED core; desugar_core is line-preserving, so span line
    # numbers still index the raw source the user typed.
    smap = _spans_for(core)
    new_objects, new_edges = _lists_from_graph(g)
    # (4c) LOSS GUARD. The source parsed into a legal world; the question here is
    # whether the DRAFT can hold it. Refused with the draft UNTOUCHED -- no
    # snapshot, no revision, no undo entry -- because nothing about the author's
    # text is wrong and there is nothing for them to repair in it.
    #
    # `syntax_error` is the reported status and it is an imperfect name, chosen
    # because it is the only one of the four frozen terminal states whose
    # BEHAVIOUR is exactly this (refused, draft untouched) and because inventing
    # a fifth status is a change to a published contract, not a language
    # decision. The diagnostic carries the honest code. Flagged to GPT-5.6.
    loss = _draft_loss(g, new_objects, new_edges, draft.profile_id)
    if loss is not None:
        return finish(_replace_result(
            draft, "syntax_error", draft.candidate_semantic_id, [loss],
            None, smap, None))
    new_cand, new_err = _seal(new_objects, new_edges, draft.profile_id)
    # (5) semantic no-op: identical canonical bytes to the current valid candidate
    if (new_err is None and draft.candidate_error is None
            and new_cand == draft.candidate_semantic_id):
        return finish(_replace_result(
            draft, "semantic_noop", new_cand, [], None, smap,
            _canonical_wrl(draft)))
    # (6) atomic replace: one snapshot + one undo entry + one revision
    old_objs, old_edges = draft.objects, draft.edges
    draft._history.append(draft._snapshot())
    draft.objects, draft.edges = new_objects, new_edges
    draft.candidate_semantic_id = new_cand
    draft.candidate_error = new_err
    draft.semantic_revision += 1
    ddiff = _draft_diff_lists(old_objs, old_edges, new_objects, new_edges)
    if new_err is None:
        res = _replace_result(draft, "candidate_valid", new_cand, [], ddiff,
                              smap, _canonical_wrl(draft))
    else:
        res = _replace_result(draft, "semantic_invalid", None, [_err_diag(new_err)],
                              ddiff, smap, None)
    res = finish(res)
    draft._replaced[request["replace_id"]] = dict(res)
    return res


# ================================ workspace persistence (v0.5.1, GPT-5.6 ruling)
# A WorldDraft is an in-memory editing session. v0.5.1 requires the COMPLETE
# authoring workspace -- including an invalid-but-editable working graph, the undo
# history, and the idempotency ledgers -- to survive a restart. `draft_state` /
# `restore_draft` are a pure, lossless serialization roundtrip over the draft's
# mutable state. They add NO new identity and NO new runtime construct: the state
# is exactly the same plain object/edge lists + ids the draft already holds, plus
# its private undo snapshots and retry ledgers, so a restored draft is BYTE-for-BYTE
# the draft that was saved (same candidate id or same typed candidate_error, same
# undo depth, same accepted edit_id / replace_id sets).
DRAFT_STATE_VERSION = "world-draft-state.v1"


def _durable_replace_ledger(replaced):
    """A JSON-safe projection of the replace idempotency ledger. Every recorded
    result is preserved verbatim EXCEPT its `source_map`, which is a read-only,
    non-identity, REGENERABLE presentation sidecar (WrlSourceMap -- explicitly
    "MUST NOT enter any identity") and is not JSON-serializable. It is nulled for
    persistence: a retry of the same replace_id across a restart still no-ops and
    returns the identical SEMANTIC result (status, candidate id, draft_diff,
    active id), just without a live span map -- idempotency (W7) is preserved.
    v0.6-0 (GPT-5.6 cleanup): the idempotent-replay path in `replace_world_source`
    ALSO nulls `source_map`, so a replay is byte-identical BEFORE and AFTER a
    restart -- one frozen replay shape, never a rich-then-stripped divergence."""
    out = {}
    for rid, res in replaced.items():
        entry = dict(res)
        if "source_map" in entry:
            entry["source_map"] = None
        out[rid] = copy.deepcopy(entry)
    return out


def draft_state(draft):
    """Serialize a WorldDraft's COMPLETE mutable state (lossless up to the
    non-identity, regenerable source-map sidecar). Includes the working graph
    (which may be invalid), the ids, the monotone revision, the undo snapshots,
    and the idempotency ledgers (accepted edit_id / replace_id sets -> their
    recorded results, so a retry across a restart still no-ops and returns the
    original SEMANTIC result). Pure projection -- never mutates the draft."""
    return {
        "draft_state_version": DRAFT_STATE_VERSION,
        "draft_id": draft.draft_id,
        "profile_id": draft.profile_id,
        "base_semantic_id": draft.base_semantic_id,
        "active_semantic_id": draft.active_semantic_id,
        "semantic_revision": draft.semantic_revision,
        "objects": copy.deepcopy(draft.objects),
        "edges": copy.deepcopy(draft.edges),
        "candidate_semantic_id": draft.candidate_semantic_id,
        "candidate_error": draft.candidate_error,
        "undo_history": copy.deepcopy(draft._history),
        "accepted_edit_ids": copy.deepcopy(draft._applied),
        "accepted_replace_ids": _durable_replace_ledger(draft._replaced),
    }


def validate_draft_state(state):
    """Structural gate for a serialized draft state (typed WRL_BAD_DRAFT)."""
    _req(isinstance(state, dict), WRL_BAD_DRAFT, "draft state must be an object")
    _req(state.get("draft_state_version") == DRAFT_STATE_VERSION, WRL_BAD_DRAFT,
         "unknown draft_state_version %r (only %s)"
         % (state.get("draft_state_version"), DRAFT_STATE_VERSION))
    for k in ("draft_id", "profile_id", "base_semantic_id", "active_semantic_id",
              "semantic_revision", "objects", "edges", "candidate_semantic_id",
              "candidate_error", "undo_history", "accepted_edit_ids",
              "accepted_replace_ids"):
        _req(k in state, WRL_BAD_DRAFT, "draft state missing field %r" % k, k)
    _req(isinstance(state["semantic_revision"], int)
         and not isinstance(state["semantic_revision"], bool)
         and state["semantic_revision"] >= 0, WRL_BAD_DRAFT,
         "semantic_revision must be a non-negative int", "semantic_revision")
    for k in ("objects", "edges", "undo_history"):
        _req(isinstance(state[k], list), WRL_BAD_DRAFT,
             "%s must be a list" % k, k)
    for k in ("accepted_edit_ids", "accepted_replace_ids"):
        _req(isinstance(state[k], dict), WRL_BAD_DRAFT,
             "%s must be an object" % k, k)
    _req(state["candidate_error"] is None
         or isinstance(state["candidate_error"], str), WRL_BAD_DRAFT,
         "candidate_error must be null or a string", "candidate_error")
    # a valid stored candidate must re-seal to the SAME id / error from the stored
    # working graph -- the sealing is deterministic, so this catches tampering of a
    # saved / imported workspace below the id.
    cand, err = _seal(state["objects"], state["edges"], state["profile_id"])
    _req(cand == state["candidate_semantic_id"] and err == state["candidate_error"],
         WRL_BAD_DRAFT,
         "draft state working graph re-seals to (%r, %r) but stores (%r, %r)"
         % (cand, err, state["candidate_semantic_id"], state["candidate_error"]),
         "candidate_semantic_id")
    return state


def restore_draft(state):
    """Reconstruct a WorldDraft from a serialized draft state (the inverse of
    `draft_state`). Validates the state, rebuilds the exact working graph (valid or
    invalid), and restores the ids, revision, undo history and idempotency ledgers
    verbatim. The restored draft is indistinguishable from the one that was saved."""
    validate_draft_state(state)
    draft = WorldDraft(state["draft_id"], state["profile_id"],
                       state["base_semantic_id"],
                       copy.deepcopy(state["objects"]),
                       copy.deepcopy(state["edges"]))
    draft.active_semantic_id = state["active_semantic_id"]
    draft.semantic_revision = state["semantic_revision"]
    draft.candidate_semantic_id = state["candidate_semantic_id"]
    draft.candidate_error = state["candidate_error"]
    draft._history = copy.deepcopy(state["undo_history"])
    draft._applied = copy.deepcopy(state["accepted_edit_ids"])
    draft._replaced = copy.deepcopy(state["accepted_replace_ids"])
    return draft
