"""wrl_converge.py v0.1 -- the CanvasLayoutV1 <-> WorldDraftV1 binding
(Spinner Bench v0.4-4a: interactive canvas/text convergence, canvas->semantic
direction).

v0.4-3 completed the GraphEditV1 op set on the semantic WorldDraft. v0.4-4 binds
the PRESENTATION surface (CanvasLayoutV1) to that semantic draft so an editor can
work on the canvas OR the text and both converge on the SAME candidate
SemanticArtifactID, with presentation staying STRICTLY non-identity. This module
delivers the unambiguous half of that convergence -- the canvas->semantic->text
direction -- entirely over the existing identity + draft spine, with NO new
runtime construct and NO new draft-contract construct:

  * A `CanvasSession` binds one `wrl_draft.WorldDraft` (the semantic source of
    truth, which alone earns the SemanticArtifactID) to one CanvasLayoutV1 (pure
    presentation, keyed by object_id / edge_key). The candidate id is ALWAYS
    `session.candidate_semantic_id == session.draft.candidate_semantic_id`; the
    layout never feeds it.
  * A SEMANTIC gesture (`add_node` / `remove_node` / `add_wire` / `remove_wire`
    / `reconnect_wire` / `set_config`) is translated 1:1 by `gesture_to_edit`
    into a frozen `GraphEditV1` op and applied through the UNCHANGED
    `wrl_draft.apply_edit` -- so every draft rule (exact CAS, idempotent edit_id,
    typed candidate sealing, monotone undo) holds verbatim. After the edit the
    layout is RECONCILED to the draft's working graph: one presentation node per
    object, one presentation edge per edge, survivors keeping their presentation,
    newcomers getting the deterministic default. An illegal semantic gesture
    (e.g. removing a still-wired node) seals an invalid-but-editable candidate
    exactly as at the module layer; the layout still reconciles to the working
    graph.
  * A PRESENTATION gesture (`set_presentation`, a patch of a node's presentation
    block -- move / recolor / collapse / ...) mutates ONLY the layout. The draft,
    the candidate id, and the revision are all UNTOUCHED, which is the concrete
    proof that presentation is non-identity.
  * `to_text()` serializes the draft's current graph to canonical WRL Core
    (`wrl_format.format_wrl_core`); re-parsing that text (`wrl_ir.parse_wrl_core`
    -> `lower_graph`) reproduces the EXACT candidate SemanticArtifactID -- the
    canvas and the text are two views of one identity.
  * `undo()` routes through the draft's monotone undo and restores the exact
    pre-edit layout snapshot, so a semantic undo is exact in BOTH the semantic id
    and the presentation.

v0.4-4b adds the reverse `text -> canvas` direction (GPT-5.6's ruling): a
free-form multi-change text edit is applied by `apply_text`, which routes the raw
source through the ATOMIC `wrl_draft.replace_world_source` transaction (a separate
`ReplaceWorldSourceV1`, NOT a multi-op GraphEditV1). One paste = one revision =
one DraftDiff = one undo entry. The session snapshots the layout in lock-step with
the draft's own history -- a layout snapshot is pushed IFF the replace advances the
revision (candidate_valid / semantic_invalid), so a syntax_error, a semantic_noop,
and an idempotent re-application leave both the draft AND the layout untouched, and
`undo()` restores matching (semantic id, presentation) pairs. After a MUTATING
text replacement the layout is reconciled to the new working graph: surviving
object ids keep their node presentation, surviving edge keys keep their route
presentation, newcomers get deterministic defaults, removed disappear -- exactly
as for a semantic gesture. A parseable-but-invalid replacement still advances the
revision once and reconciles the layout over the invalid-but-editable working
graph (candidate id null), so the canvas keeps tracking the text while it is
repaired.
"""
import copy

import wrl_canonical as WC
import wrl_canvas as CV
import wrl_draft as D
import wrl_format as F
import wrl_ir as W

CONVERGE_VERSION = "canvas-session.v1"
GESTURE_VERSION = "canvas-gesture.v1"

WRL_BAD_GESTURE = "WRL_BAD_GESTURE"
WRL_BAD_SESSION = "WRL_BAD_SESSION"

SESSION_STATE_VERSION = "canvas-session-state.v1"

# a semantic gesture maps 1:1 to a frozen GraphEditV1 op; a presentation gesture
# never emits an edit (it is the concrete witness that presentation is
# non-identity).
_SEMANTIC_GESTURES = ("add_node", "remove_node", "add_wire", "remove_wire",
                      "reconnect_wire", "set_config")
_PRESENTATION_GESTURES = ("set_presentation",)
GESTURE_KINDS = _SEMANTIC_GESTURES + _PRESENTATION_GESTURES


def _req(cond, msg, field=None):
    if not cond:
        WC._fail(WRL_BAD_GESTURE, msg, field_path=field)


# ------------------------------------------------------- gesture -> GraphEditV1
def gesture_to_edit(gesture, base_revision, draft_id):
    """Translate a SEMANTIC canvas gesture into a frozen GraphEditV1 op targeting
    `base_revision` on `draft_id`. Returns the edit dict; a presentation gesture
    has no edit and raises WRL_BAD_GESTURE if passed here (callers gate on
    `is_semantic` first). Shape-only: structural legality of the resulting graph
    is still the seal's job -- this only builds the op envelope."""
    _req(isinstance(gesture, dict), "gesture must be an object")
    _req(gesture.get("gesture_version") == GESTURE_VERSION,
         "unknown gesture_version %r (only %s)"
         % (gesture.get("gesture_version"), GESTURE_VERSION), "gesture_version")
    _req(isinstance(gesture.get("gesture_id"), str) and gesture["gesture_id"],
         "gesture_id must be a non-empty string", "gesture_id")
    kind = gesture.get("kind")
    _req(kind in _SEMANTIC_GESTURES,
         "kind %r is not a semantic gesture (semantic %s; presentation %s)"
         % (kind, list(_SEMANTIC_GESTURES), list(_PRESENTATION_GESTURES)),
         "kind")
    if kind == "add_node":
        _req(isinstance(gesture.get("object"), dict),
             "add_node needs an `object` = {object_id, role, static_config}",
             "object")
        op = {"kind": "AddObject", "object": copy.deepcopy(gesture["object"])}
    elif kind == "remove_node":
        _req(isinstance(gesture.get("target"), str) and gesture["target"],
             "remove_node needs a non-empty `target` object_id", "target")
        op = {"kind": "RemoveObject", "target": gesture["target"]}
    elif kind == "add_wire":
        _req(isinstance(gesture.get("edge"), dict),
             "add_wire needs an `edge` = {kind, src, dst}", "edge")
        op = {"kind": "AddEdge", "edge": copy.deepcopy(gesture["edge"])}
    elif kind == "remove_wire":
        _req(isinstance(gesture.get("edge"), dict),
             "remove_wire needs an `edge` = {kind, src, dst}", "edge")
        op = {"kind": "RemoveEdge", "edge": copy.deepcopy(gesture["edge"])}
    elif kind == "reconnect_wire":
        _req(isinstance(gesture.get("edge"), dict)
             and isinstance(gesture.get("to"), dict),
             "reconnect_wire needs `edge` and `to` edge specs", "edge")
        op = {"kind": "ReconnectEdge", "edge": copy.deepcopy(gesture["edge"]),
              "to": copy.deepcopy(gesture["to"])}
    else:  # set_config
        _req(isinstance(gesture.get("target"), str) and gesture["target"],
             "set_config needs a non-empty `target` object_id", "target")
        _req(isinstance(gesture.get("static_config"), dict),
             "set_config needs a `static_config` object", "static_config")
        op = {"kind": "SetObjectConfig", "target": gesture["target"],
              "static_config": copy.deepcopy(gesture["static_config"])}
    return {"edit_version": D.EDIT_VERSION, "edit_id": gesture["gesture_id"],
            "draft_id": draft_id, "base_revision": base_revision,
            "operation": op}


def is_semantic(gesture):
    return isinstance(gesture, dict) and gesture.get("kind") in _SEMANTIC_GESTURES


# ------------------------------------------------------------- the session type
class CanvasSession:
    """A canvas editing session over ONE world: a WorldDraft (semantic identity)
    bound to a CanvasLayoutV1 (presentation). Construct via `new_session`."""

    def __init__(self, draft, layout=None):
        self.draft = draft
        # `layout` (optional) is a curated CanvasLayoutV1 to SEED the presentation
        # from -- e.g. a template's manifest layout. It is reconciled onto the
        # draft's working graph exactly like any prior layout: surviving objects /
        # edges keep the seeded presentation, newcomers get the deterministic
        # default, and anything not in the graph is dropped. Presentation NEVER
        # feeds the semantic id, so seeding a layout moves no identity.
        #
        # The session OWNS the seed contract: it deep-copies (so a caller can
        # never share a mutable presentation object with the session) and
        # validates (`validate_layout_v1`) at THIS API boundary, so a malformed
        # curated layout fails closed here rather than silently reconciling. A
        # caller need not pre-copy or pre-validate.
        seed = (CV.validate_layout_v1(copy.deepcopy(layout))
                if layout is not None else None)
        self.layout = self._layout_from_draft(seed=seed)
        self._layout_history = []      # pre-edit layout snapshots, parallel undo
        self.commits = []              # append-only commit log (session bookkeeping)
        # v0.5.1 workspace state (all non-identity sidecars):
        #  * source_document -- the raw editor buffer + its last parse status +
        #    diagnostics, tracked EVEN when a text edit was a syntax_error (the
        #    draft is untouched then, but the buffer the author is repairing must
        #    survive a restart).
        #  * active_world_source -- the canonical WRL of the last COMMITTED world,
        #    retained independently of the (possibly diverged / invalid) working
        #    graph so the active sealed world stays runnable beside an invalid
        #    draft.
        #  * selected_scenario / scenario_compatibility -- which run-input document
        #    the author has selected and whether it still binds to the active world.
        self.source_document = {"raw_source": self.to_text(),
                                "source_revision": 0,
                                "parse_status": "clean", "diagnostics": []}
        self.active_world_source = self.to_text()
        self.selected_scenario = None
        self.scenario_compatibility = None

    # -- layout reconciliation --------------------------------------------
    def _layout_from_draft(self, seed):
        """Build a CanvasLayoutV1 matching the draft's working graph: one node
        per object (draft order), one edge per edge, keyed by object_id /
        edge_key. `seed` (the prior layout) supplies surviving presentation;
        newcomers get the deterministic default. Presentation NEVER influences
        the semantic id -- this is a pure view over draft.objects / draft.edges."""
        prev_n = ({n["object_id"]: n["presentation"] for n in seed["nodes"]}
                  if seed else {})
        prev_e = ({e["edge_key"]: e["presentation"] for e in seed["edges"]}
                  if seed else {})
        nodes = []
        for i, o in enumerate(self.draft.objects):
            oid = o["object_id"]
            nodes.append({"object_id": oid,
                          "presentation": prev_n.get(
                              oid, CV._node_presentation(i, o["role"]))})
        edges = []
        for e in self.draft.edges:
            k = CV.edge_key(e["kind"], e["src"], e["dst"])
            edges.append({"edge_key": k,
                          "presentation": prev_e.get(
                              k, CV._conn_presentation(e["kind"]))})
        return {"layout_version": CV.LAYOUT_VERSION,
                "profile_id": self.draft.profile_id,
                "nodes": nodes, "edges": edges}

    def _reconcile(self):
        self.layout = self._layout_from_draft(seed=self.layout)

    # -- read-only projections --------------------------------------------
    @property
    def candidate_semantic_id(self):
        return self.draft.candidate_semantic_id

    @property
    def candidate_error(self):
        return self.draft.candidate_error

    @property
    def semantic_revision(self):
        return self.draft.semantic_revision

    def to_text(self):
        """Canonical WRL Core text of the draft's current graph. Re-parsing it
        reproduces the EXACT candidate SemanticArtifactID (canvas == text)."""
        return F.format_wrl_core(
            D._graph_from(self.draft.objects, self.draft.edges,
                          self.draft.profile_id))

    def to_document(self):
        """The public session document: the frozen WorldDraftV1 + the reconciled
        CanvasLayoutV1 (validated) + the current WRL Core text view."""
        return {"session_version": CONVERGE_VERSION,
                "world": self.draft.to_document(),
                "layout": CV.validate_layout_v1(copy.deepcopy(self.layout)),
                "text": self.to_text()}

    # -- the one mutation entry point -------------------------------------
    def apply_gesture(self, gesture):
        """Apply a canvas gesture. A SEMANTIC gesture is translated to a
        GraphEditV1 and applied through the unchanged `wrl_draft.apply_edit`
        (all draft rules hold), then the layout is reconciled to the new working
        graph. A PRESENTATION gesture patches ONLY the layout -- the draft,
        candidate id, and revision are untouched. `base_revision` defaults to the
        current revision (auto-base) but a gesture may pin one to exercise CAS."""
        _req(isinstance(gesture, dict) and gesture.get("kind") in GESTURE_KINDS,
             "gesture kind must be one of %s" % list(GESTURE_KINDS), "kind")
        kind = gesture["kind"]
        if kind in _SEMANTIC_GESTURES:
            base = gesture.get("base_revision", self.draft.semantic_revision)
            edit = gesture_to_edit(gesture, base, self.draft.draft_id)
            self._layout_history.append(copy.deepcopy(self.layout))
            res = D.apply_edit(self.draft, edit)
            self._reconcile()
            return {"gesture": "semantic", "edit": edit,
                    "semantic_revision": res["semantic_revision"],
                    "candidate_semantic_id": res["candidate_semantic_id"],
                    "candidate_valid": res["candidate_valid"],
                    "candidate_error": res["candidate_error"],
                    "layout": copy.deepcopy(self.layout)}
        # presentation gesture: layout only
        _req(isinstance(gesture.get("object_id"), str) and gesture["object_id"],
             "set_presentation needs a non-empty `object_id`", "object_id")
        _req(isinstance(gesture.get("presentation"), dict),
             "set_presentation needs a `presentation` patch object",
             "presentation")
        found = False
        for n in self.layout["nodes"]:
            if n["object_id"] == gesture["object_id"]:
                n["presentation"] = {**n["presentation"],
                                     **copy.deepcopy(gesture["presentation"])}
                found = True
                break
        _req(found, "set_presentation target %r is not a node in this layout"
             % gesture["object_id"], "object_id")
        return {"gesture": "presentation",
                "semantic_revision": self.draft.semantic_revision,
                "candidate_semantic_id": self.draft.candidate_semantic_id,
                "candidate_valid": self.draft.candidate_error is None,
                "candidate_error": self.draft.candidate_error,
                "layout": copy.deepcopy(self.layout)}

    def apply_text(self, request):
        """Apply a free-form WRL Core text replacement (a `ReplaceWorldSourceV1`).
        The raw source is routed through the ATOMIC `wrl_draft.replace_world_source`
        transaction (idempotency-before-CAS, exact-revision CAS, scenario-syntax
        rejection, semantic-no-op detection, one atomic swap). The layout is kept
        in lock-step with the draft's own history: a layout snapshot is pushed and
        the layout reconciled IFF the replace advanced the revision -- so a
        syntax_error, a semantic_noop, and an idempotent re-application leave BOTH
        the draft and the layout untouched (no undo entry), while a candidate_valid
        or a (parseable-but-invalid) semantic_invalid replacement advances exactly
        one revision, pushes exactly one paired layout snapshot, and reconciles the
        canvas over the new working graph. `undo()` then restores the matching
        (semantic id, presentation) pair."""
        _req(isinstance(request, dict), "text request must be an object")
        rev_before = self.draft.semantic_revision
        snap = copy.deepcopy(self.layout)
        res = D.replace_world_source(self.draft, request)
        if self.draft.semantic_revision > rev_before:   # mutating replace only
            self._layout_history.append(snap)
            self._reconcile()
        # record the raw editor buffer + its parse status regardless of outcome:
        # a syntax_error leaves the draft untouched but the buffer the author is
        # repairing MUST survive a restart (v0.5.1 W3).
        self.source_document = {
            "raw_source": request.get("source", ""),
            "source_revision": self.source_document["source_revision"] + 1,
            "parse_status": res["status"],
            "diagnostics": copy.deepcopy(res["diagnostics"])}
        return {"gesture": "text", "replace": res,
                "semantic_revision": self.draft.semantic_revision,
                "candidate_semantic_id": self.draft.candidate_semantic_id,
                "candidate_valid": self.draft.candidate_error is None,
                "candidate_error": self.draft.candidate_error,
                "layout": copy.deepcopy(self.layout)}

    def undo(self):
        """Undo the last SEMANTIC gesture: the draft's monotone undo restores the
        exact prior SemanticArtifactID (revision increments) and the parallel
        layout snapshot restores the exact prior presentation. Presentation
        gestures are view-only and not on the undo stack."""
        _req(bool(self._layout_history), "nothing to undo")
        res = D.undo(self.draft)
        self.layout = self._layout_history.pop()
        return {"gesture": "undo",
                "semantic_revision": res["semantic_revision"],
                "candidate_semantic_id": res["candidate_semantic_id"],
                "candidate_valid": res["candidate_valid"],
                "candidate_error": res["candidate_error"],
                "layout": copy.deepcopy(self.layout)}

    def commit(self, commit):
        """Promote the current candidate to the active world (draft commit) and
        record it in the append-only session commit log. The log is pure session
        bookkeeping -- a projection of what the draft already did -- and never
        feeds any identity: each entry is {index, semantic_revision,
        previous_active, active_semantic_id}."""
        prev = self.draft.active_semantic_id
        res = D.commit_draft(self.draft, commit)
        # retain the canonical source of the just-committed world so the active
        # sealed world stays reopenable/runnable even if the working graph later
        # diverges into an invalid draft (v0.5.1 W4).
        self.active_world_source = self.to_text()
        self.commits.append({"index": len(self.commits),
                             "semantic_revision": res["semantic_revision"],
                             "previous_active": prev,
                             "active_semantic_id": res["active_semantic_id"]})
        return res

    def select_scenario(self, scenario_document_id, compatibility=None):
        """Record which run-input document is selected + its compatibility status
        with the active world (both non-identity workspace sidecars)."""
        self.selected_scenario = scenario_document_id
        self.scenario_compatibility = copy.deepcopy(compatibility)
        return {"selected_scenario": self.selected_scenario,
                "scenario_compatibility": copy.deepcopy(self.scenario_compatibility)}

    def history(self):
        """Read-only session history: the append-only commit log plus the current
        undo depth (parallel layout/draft undo stack). Pure projection."""
        return {"commits": copy.deepcopy(self.commits),
                "undo_depth": len(self._layout_history),
                "can_undo": bool(self._layout_history)}


# ------------------------------------------------------------- construction
def new_session(program_or_artifact, draft_id, layout=None):
    """Open a CanvasSession over a sealed world: a fresh WorldDraft plus a
    CanvasLayoutV1 for its graph. With no `layout` the deterministic default
    layout is used; a curated `layout` (e.g. a template manifest's) is reconciled
    onto the draft's working graph (presentation only -- moves no identity)."""
    return CanvasSession(D.new_draft(program_or_artifact, draft_id), layout=layout)


# ------------------------------------------------- workspace serialization (v0.5.1)
# `session_state` / `restore_session` are the CanvasSession-level lossless
# serialization roundtrip demanded by GPT-5.6's v0.5.1 ruling: the COMPLETE
# authoring workspace -- the semantic draft (valid OR invalid), the parallel
# layout undo stack, the current presentation, the append-only commit log, the
# raw editor buffer with its last parse status, the retained active-world source,
# and the scenario selection / compatibility -- must survive a restart. Every
# field is a non-identity sidecar; the semantic id is still earned solely by the
# draft's working graph (re-sealed on restore inside `D.restore_draft`). NO new
# runtime construct, NO new draft-contract construct -- pure projection +
# reconstruction over the existing draft + layout spine. The layout undo stack is
# serialized IN LOCK-STEP with the draft's own undo history (equal depth), so an
# `undo()` after a reopen restores the exact matching (semantic id, presentation)
# pair (W9).


def session_state(session):
    """Serialize a CanvasSession's COMPLETE mutable workspace (lossless). Pure
    projection -- never mutates the session."""
    return {
        "session_state_version": SESSION_STATE_VERSION,
        "draft": D.draft_state(session.draft),
        "layout": copy.deepcopy(session.layout),
        "layout_history": copy.deepcopy(session._layout_history),
        "commits": copy.deepcopy(session.commits),
        "source_document": copy.deepcopy(session.source_document),
        "active_world_source": session.active_world_source,
        "selected_scenario": session.selected_scenario,
        "scenario_compatibility": copy.deepcopy(session.scenario_compatibility),
    }


def validate_session_state(state):
    """Structural gate for a serialized session state (typed WRL_BAD_SESSION).
    Delegates the draft state to `wrl_draft.validate_draft_state` (which re-seals
    the working graph, catching sub-id tampering) and checks the presentation +
    workspace sidecars. The layout undo stack MUST be exactly as deep as the
    draft's undo history so reopen-then-undo restores paired (id, layout)."""
    _req(isinstance(state, dict), "session state must be an object")
    _req(state.get("session_state_version") == SESSION_STATE_VERSION,
         "unknown session_state_version %r (only %s)"
         % (state.get("session_state_version"), SESSION_STATE_VERSION),
         "session_state_version")
    for k in ("draft", "layout", "layout_history", "commits", "source_document",
              "active_world_source", "selected_scenario",
              "scenario_compatibility"):
        _req(k in state, "session state missing field %r" % k, k)
    D.validate_draft_state(state["draft"])
    CV.validate_layout_v1(copy.deepcopy(state["layout"]))
    _req(isinstance(state["layout_history"], list),
         "layout_history must be a list", "layout_history")
    for snap in state["layout_history"]:
        CV.validate_layout_v1(copy.deepcopy(snap))
    _req(len(state["layout_history"]) == len(state["draft"]["undo_history"]),
         "layout_history depth %d != draft undo_history depth %d "
         "(the layout and semantic undo stacks must stay paired)"
         % (len(state["layout_history"]), len(state["draft"]["undo_history"])),
         "layout_history")
    _req(isinstance(state["commits"], list), "commits must be a list", "commits")
    sd = state["source_document"]
    _req(isinstance(sd, dict), "source_document must be an object",
         "source_document")
    for k in ("raw_source", "source_revision", "parse_status", "diagnostics"):
        _req(k in sd, "source_document missing field %r" % k, "source_document")
    _req(isinstance(sd["source_revision"], int)
         and not isinstance(sd["source_revision"], bool)
         and sd["source_revision"] >= 0,
         "source_revision must be a non-negative int", "source_document")
    _req(isinstance(sd["diagnostics"], list),
         "source_document.diagnostics must be a list", "source_document")
    _req(isinstance(state["active_world_source"], str),
         "active_world_source must be a string", "active_world_source")
    _req(state["selected_scenario"] is None
         or isinstance(state["selected_scenario"], str),
         "selected_scenario must be null or a string", "selected_scenario")
    return state


def restore_session(state):
    """Reconstruct a CanvasSession from a serialized session state (the inverse of
    `session_state`). Validates the state, rebuilds the exact semantic draft (valid
    or invalid) via `wrl_draft.restore_draft`, then restores the presentation, the
    paired layout undo stack, the commit log, the raw editor buffer, the retained
    active-world source, and the scenario selection / compatibility verbatim. The
    restored session is indistinguishable from the one that was saved."""
    validate_session_state(state)
    session = CanvasSession(D.restore_draft(state["draft"]))
    session.layout = copy.deepcopy(state["layout"])
    session._layout_history = copy.deepcopy(state["layout_history"])
    session.commits = copy.deepcopy(state["commits"])
    session.source_document = copy.deepcopy(state["source_document"])
    session.active_world_source = state["active_world_source"]
    session.selected_scenario = state["selected_scenario"]
    session.scenario_compatibility = copy.deepcopy(state["scenario_compatibility"])
    return session
