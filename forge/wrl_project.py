"""wrl_project.py v0.6-0 -- ForgeProjectV1/V2 + RecoveryJournalV1: the per-project
document store + crash-recovery overlay (Forge World Library, phases 2-6).

v0.6-0 adds a SEPARATE, non-authoritative RecoveryJournalV1 (its own `.recovery/`
store, keyed by project_id) that checkpoints the COMPLETE unsaved workspace so an
unexpected exit does not silently lose in-progress authoring. It is emergency
overlay, NOT saved project state: writing a checkpoint never modifies the durable
project, never advances `project_revision`, never moves a semantic identity, never
activates a candidate, and never appears in Fork Saved or normal project bundles.
On reopen it is NEVER auto-applied -- the cache reports it, `recover` loads it as an
unsaved dirty workspace (the user must still Save), `discard` drops it, and a stale
journal is offered only as an open-as-recovered-copy. A successful Save/Commit
clears the journal ONLY after the durable project write. See `RecoveryJournalStore`
+ `ProjectSessionCache.checkpoint/recovery_status/recover/inspect_recovery/
discard_recovery/open_as_recovered_copy`.

v0.5.1 added ForgeProjectV2: unlike V1 (which persists only the last committed
world by reference), a V2 project persists the COMPLETE editing workspace -- the
exact draft (valid OR invalid), the raw editor buffer, the paired layout + semantic
undo stacks, the scenario selection + compatibility, and the commit log -- so an
explicit Save (not just Commit) is fully durable and a reopened V2 project
reconstructs the entire workspace, undo history and all. Version is dispatched
throughout (`project_version_of`, `canonicalize_project`, `_revision_of`, ...), so a
V2 cache still reads any pre-existing V1 project on disk.

v0.5-4 adds Library management over the store + cache: `list_project_infos`
(named summaries), `rename` (display name only, project_id immutable, exact-CAS),
`fork` (copy the SAVED state into a new id at revision 0, world/scenarios shared
by reference), and `trash` (SOFT-delete a project doc into a `.trash/` subdir --
reversible, a single mutable-file op distinct from the DEFERRED multi-op atomic
graph-object deletion). `ProjectSessionCache` gains matching `list_infos`,
`create_new`, `fork`, `rename`, `trash` so the browser Library panel can name,
switch, fork, rename and trash multiple persisted worlds.

v0.5-1 laid the IMMUTABLE substrate (content-addressed WorldObjectStore /
ScenarioRuntimeStore / ReplayBundleStore). v0.5-2 layers the MUTABLE, named,
per-project document OVER it. A `ForgeProjectV1` is the durable, reopenable state
of one editing project:

    {project_version, project_id, name, revision,
     active_world_semantic_id,   # the project's world (a WorldObjectStore key)
     world_source,               # canonical WRL Core of that world (reopenable)
     layout,                     # CanvasLayoutV1 presentation (non-identity)
     scenarios[{name, scenario_digest, scenario}],   # editable ScenarioV1 docs
     commits[{index, semantic_revision, previous_active, active_semantic_id}]}

The project document is NOT content-addressed -- it is a NAMED, mutable record,
so it needs optimistic-concurrency control instead. `ForgeProjectStore` gives it:

  * ATOMIC WRITES via the same persistence law as the object stores (validate ->
    serialize -> temp file -> flush + fsync -> atomic rename), reusing
    `wrl_store._atomic_write`;

  * PER-PROJECT EXACT-CAS revision -- `save(doc, expected_revision)` refuses to
    write unless the on-disk revision is EXACTLY `expected_revision`
    (WRL_PROJECT_STALE, no auto-merge, mirroring the WorldDraft's exact-CAS), then
    bumps the revision by one. `create` refuses to clobber (WRL_PROJECT_EXISTS);
    `load` of an absent id is WRL_PROJECT_MISSING.

Identity discipline is unchanged: the project stores the world by REFERENCE (its
SemanticArtifactID + the reopenable source); the world's identity still comes
ONLY from the sealed graph, presentation stays in the layout, and run inputs stay
in the ScenarioV1 documents. NO new identity, NO new runtime construct.

Reopening is deterministic. For a V1 project, `open_session_from_project` re-lowers
`world_source` to a fresh `CanvasSession`, asserts it reproduces
`active_world_semantic_id` (closure), and restores the persisted layout + commit
log; a V1 reopen DELIBERATELY drops the session-local undo stack (it starts at
undo_depth 0 over its persisted world -- the working graph itself is durable via
`world_source`). For a V2 project, `open_session_from_project_v2` reconstructs the
COMPLETE saved workspace, undo history included, via `wrl_converge.restore_session`
(so the V1 "undo is session-local, only committed state is durable" statement is a
V1-only rule -- it does NOT apply to V2 Save). `open_session_from_project_any`
version-dispatches between the two.
"""
import copy
import os
import re
import time

import wrl_canonical as WC
import wrl_canvas as CV
import wrl_scenario as SC
import wrl_converge as CG
import wrl_draft as D
import wrl_sugar as SG
import wrl_ir as W
import wrl_store as ST

PROJECT_VERSION = "forge.project.v1"
PROJECT_V2_VERSION = "forge.project.v2"    # v0.5.1 full-workspace project doc

WRL_BAD_PROJECT = "WRL_BAD_PROJECT"        # malformed project document
WRL_PROJECT_EXISTS = "WRL_PROJECT_EXISTS"  # create over an existing id
WRL_PROJECT_MISSING = "WRL_PROJECT_MISSING"  # load/save of an absent id
WRL_PROJECT_STALE = "WRL_PROJECT_STALE"    # save with a stale expected revision
WRL_BAD_TRASH = "WRL_BAD_TRASH"            # malformed trash entry
WRL_TRASH_MISSING = "WRL_TRASH_MISSING"    # restore of an absent trash entry
WRL_BAD_SESSION_POINTER = "WRL_BAD_SESSION_POINTER"  # malformed last-session pointer
WRL_PROJECT_MIGRATION = "WRL_PROJECT_MIGRATION"  # forward-only project-doc migration fault

# --------------------------------------------------------- LastSessionPointerV1 (v0.6-2)
# The "where did I leave off" pointer: a single, non-authoritative record of the
# LAST project the author opened, so a reload lands back in that project instead
# of dumping the demo. It is pure startup UX -- NOT authored state: it advances no
# project revision, moves no SemanticArtifactID, and is version-agnostic about the
# project it names (it stores only the id + a wall clock). It self-heals: a pointer
# at a project that was trashed/removed resolves to None (see `resolve_last_session`)
# rather than crashing startup. Stored as ONE dotted `.last_session.json` in the
# project root (a leading dot keeps `ForgeProjectStore.list_projects` from ever
# mistaking it for a project). See `LastSessionStore`.
LAST_SESSION_VERSION = "forge.last_session.v1"
_LAST_SESSION_TOP = ("last_session_version", "last_project_id", "updated_at")

TRASH_ENTRY_VERSION = "forge.trash.v1"     # v0.5.1 restorable trash tombstone
_TRASH_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")
_TRASH_ENTRY = ("trash_entry_version", "trash_id", "original_project_id",
                "deleted_project_revision", "deleted_at", "project_document")

# --------------------------------------------------------- RecoveryJournalV1 (v0.6-0)
# A RecoveryJournalV1 is a SEPARATE, non-authoritative crash-recovery overlay
# (GPT-5.6's v0.6-0 ruling): it checkpoints the COMPLETE unsaved workspace so an
# unexpected exit does not silently lose in-progress authoring -- WITHOUT ever
# modifying the durable ForgeProjectV2, advancing its project_revision, moving any
# semantic identity, activating a candidate, or weakening explicit Save. It is NOT
# a saved project: it lives in its own `.recovery/` store keyed by project_id (one
# overlay per project), never appears in Fork Saved or normal project bundles, and
# is never auto-applied on reopen. `session_state` REUSES the exact lossless
# `wrl_converge.session_state` serialization; `scenario_documents` /
# `selected_scenario_document_id` mirror the V2 project's authored-scenario shape.
RECOVERY_VERSION = "forge.recovery.v1"
WRL_BAD_RECOVERY = "WRL_BAD_RECOVERY"          # malformed recovery journal
WRL_RECOVERY_MISSING = "WRL_RECOVERY_MISSING"  # recover/inspect of an absent journal
WRL_RECOVERY_STALE = "WRL_RECOVERY_STALE"      # journal base rev != saved project rev
_RECOVERY_TOP = ("recovery_version", "project_id", "base_project_revision",
                 "recovery_revision", "checkpointed_at", "session_state",
                 "scenario_documents", "selected_scenario_document_id",
                 "dirty_reasons")
# the authoring changes that legitimately warrant a checkpoint (view-only,
# film-scrub, completion, diagnostics and runtime-verification reads do NOT)
_DIRTY_REASONS = frozenset({"text", "graph", "presentation", "scenario",
                            "undo", "selection", "compatibility"})

_PROJECT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_SCEN_ID_RE = re.compile(r"^scen-[0-9a-f]{64}$")

_TOP = ("project_version", "project_id", "name", "revision",
        "active_world_semantic_id", "world_source", "layout", "scenarios",
        "commits")
_SCEN_ENTRY = ("name", "scenario_digest", "scenario")
_COMMIT_ENTRY = ("index", "semantic_revision", "previous_active",
                 "active_semantic_id")


# --------------------------------------------------------------- validation
def _req(cond, msg, field=None):
    if not cond:
        WC._fail(WRL_BAD_PROJECT, msg, field_path=field)


def validate_project_v1(doc):
    """Structural gate for a ForgeProjectV1. Raises WrlValidationError
    (WRL_BAD_PROJECT) on any violation; returns the document on success."""
    _req(isinstance(doc, dict), "project must be an object")
    _req(doc.get("project_version") == PROJECT_VERSION,
         "unknown project_version %r (only %s)"
         % (doc.get("project_version"), PROJECT_VERSION))
    missing = [k for k in _TOP if k not in doc]
    _req(not missing, "project missing field(s) %s" % missing)
    extra = [k for k in doc if k not in _TOP]
    _req(not extra, "project has unknown field(s) %s" % sorted(extra))

    _req(isinstance(doc["project_id"], str)
         and _PROJECT_ID_RE.match(doc["project_id"]),
         "project_id must match %s, got %r"
         % (_PROJECT_ID_RE.pattern, doc.get("project_id")), "project_id")
    _req(isinstance(doc["name"], str) and doc["name"] != "",
         "name must be a non-empty string", "name")
    _req(isinstance(doc["revision"], int) and not isinstance(doc["revision"], bool)
         and doc["revision"] >= 0, "revision must be a non-negative int",
         "revision")
    _req(isinstance(doc["active_world_semantic_id"], str)
         and WC._SEM_ID_RE.match(doc["active_world_semantic_id"]),
         "bad active_world_semantic_id %r"
         % (doc.get("active_world_semantic_id"),), "active_world_semantic_id")
    _req(isinstance(doc["world_source"], str) and doc["world_source"] != "",
         "world_source must be a non-empty string", "world_source")

    CV.validate_layout_v1(doc["layout"])   # raises typed on any layout violation

    _req(isinstance(doc["scenarios"], list), "scenarios must be a list",
         "scenarios")
    names = []
    for i, s in enumerate(doc["scenarios"]):
        loc = "scenarios[%d]" % i
        _req(isinstance(s, dict), "%s must be an object" % loc, loc)
        s_extra = [k for k in s if k not in _SCEN_ENTRY]
        _req(not s_extra, "%s has unknown field(s) %s" % (loc, sorted(s_extra)),
             loc)
        _req(isinstance(s.get("name"), str) and s["name"] != "",
             "%s.name must be a non-empty string" % loc, loc)
        names.append(s["name"])
        _req(isinstance(s.get("scenario_digest"), str)
             and _SCEN_ID_RE.match(s["scenario_digest"]),
             "%s.scenario_digest malformed" % loc, loc)
        SC.validate_scenario_v1(s.get("scenario"))
        _req(SC.scenario_digest(s["scenario"]) == s["scenario_digest"],
             "%s.scenario_digest does not match its scenario" % loc, loc)
    _req(len(set(names)) == len(names), "scenario names must be unique",
         "scenarios")

    _req(isinstance(doc["commits"], list), "commits must be a list", "commits")
    for i, c in enumerate(doc["commits"]):
        loc = "commits[%d]" % i
        _req(isinstance(c, dict), "%s must be an object" % loc, loc)
        c_extra = [k for k in c if k not in _COMMIT_ENTRY]
        _req(not c_extra, "%s has unknown field(s) %s" % (loc, sorted(c_extra)),
             loc)
        _req(c.get("index") == i, "%s.index must be %d" % (loc, i), loc)
        _req(isinstance(c.get("semantic_revision"), int)
             and not isinstance(c["semantic_revision"], bool),
             "%s.semantic_revision must be an int" % loc, loc)
        for k in ("previous_active", "active_semantic_id"):
            v = c.get(k)
            _req(v is None or (isinstance(v, str) and WC._SEM_ID_RE.match(v)),
                 "%s.%s must be null or a SemanticArtifactID" % (loc, k), loc)
    return doc


def canonicalize_project_v1(doc):
    """Validate then return the CANONICAL project form: scenarios sorted by name
    (each scenario canonicalized + its digest recomputed), commits in index
    order, layout validated. Two projects that differ only in scenario order (or
    a scenario's claim order) canonicalize identically."""
    validate_project_v1(doc)
    scenarios = sorted(doc["scenarios"], key=lambda s: s["name"])
    scen_out = []
    for s in scenarios:
        canon = SC.canonicalize_scenario_v1(s["scenario"])
        scen_out.append({"name": s["name"],
                         "scenario_digest": SC.scenario_digest(canon),
                         "scenario": canon})
    return {
        "project_version": PROJECT_VERSION,
        "project_id": doc["project_id"],
        "name": doc["name"],
        "revision": doc["revision"],
        "active_world_semantic_id": doc["active_world_semantic_id"],
        "world_source": doc["world_source"],
        "layout": CV.validate_layout_v1(copy.deepcopy(doc["layout"])),
        "scenarios": scen_out,
        "commits": [WC._plain(c) for c in doc["commits"]],
    }


def serialize_project(doc):
    """Deterministic canonical bytes of a project document."""
    return WC.serialize_artifact(canonicalize_project_v1(doc))


# ===================================================================== V2
# ForgeProjectV2 (v0.5.1 Workspace Persistence Closure). A V2 document persists
# the COMPLETE authoring workspace -- not just the last committed world -- so the
# invalid / uncommitted draft, the raw editor buffer, the undo + idempotency
# state, and the scenario selection / compatibility all survive a restart. It is
# a PROJECT-DOC version bump (NOT a semantic-world version bump): it moves NO
# SemanticArtifactID. Every added field is a non-identity workspace sidecar; the
# world's identity is still earned solely by the draft's sealed working graph
# (re-sealed on load inside `wrl_draft.validate_draft_state`) and the active
# world's retained canonical source (closure-checked at open). Shape:
#
#   {project_version, project_id, name, project_revision,
#    active_world { semantic_id, canonical_source },
#    draft { ...draft_state..., layout_undo_history },
#    source_document { raw_source, source_revision, parse_status, diagnostics },
#    canvas_layout, scenario_documents, selected_scenario_document_id,
#    scenario_compatibility, commit_history}
#
# The one deviation from the ruling's field sketch is that the parallel LAYOUT
# undo stack is stored as `draft.layout_undo_history` -- folded INTO the draft
# block alongside the semantic `undo_history` it is paired with (equal depth), per
# the ruling's own "fold each paired layout snapshot into the undo_history
# entries" instruction, so a reopen-then-undo restores the exact prior
# (semantic id, presentation) pair (W9) while keeping the two undo stacks
# physically together.
_TOP_V2 = ("project_version", "project_id", "name", "project_revision",
           "active_world", "draft", "source_document", "canvas_layout",
           "scenario_documents", "selected_scenario_document_id",
           "scenario_compatibility", "commit_history")
_ACTIVE_WORLD = ("semantic_id", "canonical_source")
_SOURCE_DOC = ("raw_source", "source_revision", "parse_status", "diagnostics")


def validate_project_v2(doc):
    """Structural gate for a ForgeProjectV2. Raises WrlValidationError
    (WRL_BAD_PROJECT) on any violation; returns the document on success. The draft
    sub-block is delegated to `wrl_draft.validate_draft_state` (which re-seals the
    stored working graph, catching sub-id tampering); the paired layout undo stack
    must be exactly as deep as the semantic undo history."""
    _req(isinstance(doc, dict), "project must be an object")
    _req(doc.get("project_version") == PROJECT_V2_VERSION,
         "unknown project_version %r (only %s)"
         % (doc.get("project_version"), PROJECT_V2_VERSION))
    missing = [k for k in _TOP_V2 if k not in doc]
    _req(not missing, "project missing field(s) %s" % missing)
    extra = [k for k in doc if k not in _TOP_V2]
    _req(not extra, "project has unknown field(s) %s" % sorted(extra))

    _req(isinstance(doc["project_id"], str)
         and _PROJECT_ID_RE.match(doc["project_id"]),
         "project_id must match %s, got %r"
         % (_PROJECT_ID_RE.pattern, doc.get("project_id")), "project_id")
    _req(isinstance(doc["name"], str) and doc["name"] != "",
         "name must be a non-empty string", "name")
    _req(isinstance(doc["project_revision"], int)
         and not isinstance(doc["project_revision"], bool)
         and doc["project_revision"] >= 0,
         "project_revision must be a non-negative int", "project_revision")

    aw = doc["active_world"]
    _req(isinstance(aw, dict), "active_world must be an object", "active_world")
    aw_extra = [k for k in aw if k not in _ACTIVE_WORLD]
    _req(not aw_extra, "active_world has unknown field(s) %s" % sorted(aw_extra),
         "active_world")
    _req(isinstance(aw.get("semantic_id"), str)
         and WC._SEM_ID_RE.match(aw["semantic_id"]),
         "bad active_world.semantic_id %r" % (aw.get("semantic_id"),),
         "active_world")
    _req(isinstance(aw.get("canonical_source"), str) and aw["canonical_source"],
         "active_world.canonical_source must be a non-empty string",
         "active_world")

    draft = doc["draft"]
    _req(isinstance(draft, dict), "draft must be an object", "draft")
    _req("layout_undo_history" in draft,
         "draft missing layout_undo_history", "draft")
    bare = {k: v for k, v in draft.items() if k != "layout_undo_history"}
    D.validate_draft_state(bare)   # re-seals the working graph (sub-id tamper)
    luh = draft["layout_undo_history"]
    _req(isinstance(luh, list), "draft.layout_undo_history must be a list",
         "draft")
    for snap in luh:
        CV.validate_layout_v1(copy.deepcopy(snap))
    _req(len(luh) == len(bare["undo_history"]),
         "draft.layout_undo_history depth %d != draft.undo_history depth %d "
         "(the layout and semantic undo stacks must stay paired)"
         % (len(luh), len(bare["undo_history"])), "draft")
    # the active world is the last committed world -- its id must equal the
    # draft's last-committed id (a coherence law, NOT a new identity).
    _req(aw["semantic_id"] == bare["active_semantic_id"],
         "active_world.semantic_id %r != draft.active_semantic_id %r"
         % (aw["semantic_id"], bare["active_semantic_id"]), "active_world")

    sd = doc["source_document"]
    _req(isinstance(sd, dict), "source_document must be an object",
         "source_document")
    sd_missing = [k for k in _SOURCE_DOC if k not in sd]
    _req(not sd_missing, "source_document missing field(s) %s" % sd_missing,
         "source_document")
    _req(isinstance(sd["source_revision"], int)
         and not isinstance(sd["source_revision"], bool)
         and sd["source_revision"] >= 0,
         "source_document.source_revision must be a non-negative int",
         "source_document")
    _req(isinstance(sd["raw_source"], str),
         "source_document.raw_source must be a string", "source_document")
    _req(isinstance(sd["diagnostics"], list),
         "source_document.diagnostics must be a list", "source_document")

    CV.validate_layout_v1(doc["canvas_layout"])

    _req(isinstance(doc["scenario_documents"], list),
         "scenario_documents must be a list", "scenario_documents")
    names = []
    for i, s in enumerate(doc["scenario_documents"]):
        loc = "scenario_documents[%d]" % i
        _req(isinstance(s, dict), "%s must be an object" % loc, loc)
        s_extra = [k for k in s if k not in _SCEN_ENTRY]
        _req(not s_extra, "%s has unknown field(s) %s" % (loc, sorted(s_extra)),
             loc)
        _req(isinstance(s.get("name"), str) and s["name"] != "",
             "%s.name must be a non-empty string" % loc, loc)
        names.append(s["name"])
        _req(isinstance(s.get("scenario_digest"), str)
             and _SCEN_ID_RE.match(s["scenario_digest"]),
             "%s.scenario_digest malformed" % loc, loc)
        SC.validate_scenario_v1(s.get("scenario"))
        _req(SC.scenario_digest(s["scenario"]) == s["scenario_digest"],
             "%s.scenario_digest does not match its scenario" % loc, loc)
    _req(len(set(names)) == len(names),
         "scenario_documents names must be unique", "scenario_documents")

    sel = doc["selected_scenario_document_id"]
    _req(sel is None or (isinstance(sel, str) and sel in names),
         "selected_scenario_document_id must be null or a present scenario name",
         "selected_scenario_document_id")

    _req(isinstance(doc["commit_history"], list),
         "commit_history must be a list", "commit_history")
    for i, c in enumerate(doc["commit_history"]):
        loc = "commit_history[%d]" % i
        _req(isinstance(c, dict), "%s must be an object" % loc, loc)
        c_extra = [k for k in c if k not in _COMMIT_ENTRY]
        _req(not c_extra, "%s has unknown field(s) %s" % (loc, sorted(c_extra)),
             loc)
        _req(c.get("index") == i, "%s.index must be %d" % (loc, i), loc)
        _req(isinstance(c.get("semantic_revision"), int)
             and not isinstance(c["semantic_revision"], bool),
             "%s.semantic_revision must be an int" % loc, loc)
        for k in ("previous_active", "active_semantic_id"):
            v = c.get(k)
            _req(v is None or (isinstance(v, str) and WC._SEM_ID_RE.match(v)),
                 "%s.%s must be null or a SemanticArtifactID" % (loc, k), loc)
    return doc


def canonicalize_project_v2(doc):
    """Validate then return the CANONICAL V2 form: scenario_documents sorted by
    name (each canonicalized + digest recomputed), commit_history in index order,
    layouts validated, draft + source_document + active_world plainified. The
    draft's object/edge ORDER is preserved verbatim (it is identity-bearing --
    `wrl_draft` seals a canonical projection of it)."""
    validate_project_v2(doc)
    scenarios = sorted(doc["scenario_documents"], key=lambda s: s["name"])
    scen_out = []
    for s in scenarios:
        canon = SC.canonicalize_scenario_v1(s["scenario"])
        scen_out.append({"name": s["name"],
                         "scenario_digest": SC.scenario_digest(canon),
                         "scenario": canon})
    return {
        "project_version": PROJECT_V2_VERSION,
        "project_id": doc["project_id"],
        "name": doc["name"],
        "project_revision": doc["project_revision"],
        "active_world": {"semantic_id": doc["active_world"]["semantic_id"],
                         "canonical_source":
                             doc["active_world"]["canonical_source"]},
        "draft": WC._plain(doc["draft"]),
        "source_document": WC._plain(doc["source_document"]),
        "canvas_layout": CV.validate_layout_v1(
            copy.deepcopy(doc["canvas_layout"])),
        "scenario_documents": scen_out,
        "selected_scenario_document_id": doc["selected_scenario_document_id"],
        "scenario_compatibility": WC._plain(doc["scenario_compatibility"]),
        "commit_history": [WC._plain(c) for c in doc["commit_history"]],
    }


def serialize_project_v2(doc):
    """Deterministic canonical bytes of a V2 project document."""
    return WC.serialize_artifact(canonicalize_project_v2(doc))


# --------------------------------------------------- version dispatch helpers
_REV_FIELD = {PROJECT_VERSION: "revision", PROJECT_V2_VERSION: "project_revision"}


def project_version_of(doc):
    """The project_version of a document, or WRL_BAD_PROJECT if unknown."""
    _req(isinstance(doc, dict), "project must be an object")
    v = doc.get("project_version")
    _req(v in (PROJECT_VERSION, PROJECT_V2_VERSION),
         "unknown project_version %r (only %s / %s)"
         % (v, PROJECT_VERSION, PROJECT_V2_VERSION), "project_version")
    return v


def canonicalize_project(doc):
    """Version-dispatched canonicalization (V1 or V2)."""
    return (canonicalize_project_v1(doc)
            if project_version_of(doc) == PROJECT_VERSION
            else canonicalize_project_v2(doc))


def serialize_project_doc(doc):
    """Version-dispatched deterministic canonical bytes (V1 or V2)."""
    return WC.serialize_artifact(canonicalize_project(doc))


def _revision_of(doc):
    return doc[_REV_FIELD[project_version_of(doc)]]


def _with_revision(doc, rev):
    out = dict(doc)
    out[_REV_FIELD[project_version_of(doc)]] = rev
    return out


def _scenarios_of(doc):
    return (doc["scenario_documents"]
            if project_version_of(doc) == PROJECT_V2_VERSION
            else doc["scenarios"])


def _active_world_id_of(doc):
    return (doc["active_world"]["semantic_id"]
            if project_version_of(doc) == PROJECT_V2_VERSION
            else doc["active_world_semantic_id"])


# --------------------------------------------------------- TrashEntryV1 (v0.5.1)
def validate_trash_entry(entry):
    """Structural gate for a TrashEntryV1 tombstone (typed WRL_BAD_TRASH). The
    embedded project document is validated with the version-dispatched project
    validator (V1 or V2); the recorded revision must match the document's own."""
    _req(isinstance(entry, dict), "trash entry must be an object")
    _req(entry.get("trash_entry_version") == TRASH_ENTRY_VERSION,
         "unknown trash_entry_version %r (only %s)"
         % (entry.get("trash_entry_version"), TRASH_ENTRY_VERSION))
    missing = [k for k in _TRASH_ENTRY if k not in entry]
    _req(not missing, "trash entry missing field(s) %s" % missing)
    extra = [k for k in entry if k not in _TRASH_ENTRY]
    _req(not extra, "trash entry has unknown field(s) %s" % sorted(extra))
    _req(isinstance(entry["trash_id"], str)
         and bool(_TRASH_ID_RE.match(entry["trash_id"])),
         "trash_id must match %s, got %r"
         % (_TRASH_ID_RE.pattern, entry.get("trash_id")), "trash_id")
    _req(isinstance(entry["original_project_id"], str)
         and bool(_PROJECT_ID_RE.match(entry["original_project_id"])),
         "original_project_id malformed", "original_project_id")
    _req(isinstance(entry["deleted_project_revision"], int)
         and not isinstance(entry["deleted_project_revision"], bool)
         and entry["deleted_project_revision"] >= 0,
         "deleted_project_revision must be a non-negative int",
         "deleted_project_revision")
    _req(isinstance(entry["deleted_at"], (int, float))
         and not isinstance(entry["deleted_at"], bool),
         "deleted_at must be a number", "deleted_at")
    doc = canonicalize_project(entry["project_document"])
    _req(_revision_of(doc) == entry["deleted_project_revision"],
         "deleted_project_revision %d != project_document revision %d"
         % (entry["deleted_project_revision"], _revision_of(doc)),
         "deleted_project_revision")
    return entry


def serialize_trash_entry(entry):
    """Deterministic canonical bytes of a trash tombstone (the embedded document
    is canonicalized; the tombstone is NOT content-addressed -- it carries a wall
    clock -- so its bytes are simply a stable serialization, not an identity)."""
    validate_trash_entry(entry)
    return WC.serialize_artifact({
        "trash_entry_version": TRASH_ENTRY_VERSION,
        "trash_id": entry["trash_id"],
        "original_project_id": entry["original_project_id"],
        "deleted_project_revision": entry["deleted_project_revision"],
        "deleted_at": entry["deleted_at"],
        "project_document": canonicalize_project(entry["project_document"]),
    })


# --------------------------------------------------------- RecoveryJournalV1 (v0.6-0)
def _reqr(cond, msg, field=None):
    if not cond:
        WC._fail(WRL_BAD_RECOVERY, msg, field_path=field)


def _canonical_scenario_docs(docs, field):
    """Validate + canonicalize a list of authored scenario-document entries
    (`{name, scenario_digest, scenario}`), mirroring the V2 project shape: names
    unique + non-empty, each digest recomputed from its scenario. Returns the list
    sorted by name. Shared by the recovery journal and (indirectly) the V2 doc."""
    _reqr(isinstance(docs, list), "%s must be a list" % field, field)
    names = []
    out = []
    for i, s in enumerate(docs):
        loc = "%s[%d]" % (field, i)
        _reqr(isinstance(s, dict), "%s must be an object" % loc, loc)
        s_extra = [k for k in s if k not in _SCEN_ENTRY]
        _reqr(not s_extra, "%s has unknown field(s) %s" % (loc, sorted(s_extra)),
              loc)
        _reqr(isinstance(s.get("name"), str) and s["name"] != "",
              "%s.name must be a non-empty string" % loc, loc)
        names.append(s["name"])
        canon = SC.canonicalize_scenario_v1(s.get("scenario"))
        dig = SC.scenario_digest(canon)
        _reqr(isinstance(s.get("scenario_digest"), str)
              and _SCEN_ID_RE.match(s["scenario_digest"]),
              "%s.scenario_digest malformed" % loc, loc)
        _reqr(s["scenario_digest"] == dig,
              "%s.scenario_digest does not match its scenario" % loc, loc)
        out.append({"name": s["name"], "scenario_digest": dig,
                    "scenario": canon})
    _reqr(len(set(names)) == len(names),
          "%s names must be unique" % field, field)
    return sorted(out, key=lambda s: s["name"]), names


def validate_recovery_journal(journal):
    """Structural gate for a RecoveryJournalV1 (typed WRL_BAD_RECOVERY). The
    embedded `session_state` is delegated to `wrl_converge.validate_session_state`
    (which re-seals the working graph, catching sub-id tampering below the overlay);
    the scenario documents mirror the V2 authored-scenario contract. This validator
    NEVER re-derives or moves any semantic identity -- it only checks structure, so
    a checkpoint can carry a valid OR invalid draft verbatim."""
    _reqr(isinstance(journal, dict), "recovery journal must be an object")
    _reqr(journal.get("recovery_version") == RECOVERY_VERSION,
          "unknown recovery_version %r (only %s)"
          % (journal.get("recovery_version"), RECOVERY_VERSION))
    missing = [k for k in _RECOVERY_TOP if k not in journal]
    _reqr(not missing, "recovery journal missing field(s) %s" % missing)
    extra = [k for k in journal if k not in _RECOVERY_TOP]
    _reqr(not extra, "recovery journal has unknown field(s) %s" % sorted(extra))

    _reqr(isinstance(journal["project_id"], str)
          and bool(_PROJECT_ID_RE.match(journal["project_id"])),
          "project_id must match %s, got %r"
          % (_PROJECT_ID_RE.pattern, journal.get("project_id")), "project_id")
    for k in ("base_project_revision", "recovery_revision"):
        _reqr(isinstance(journal[k], int) and not isinstance(journal[k], bool)
              and journal[k] >= 0, "%s must be a non-negative int" % k, k)
    _reqr(isinstance(journal["checkpointed_at"], (int, float))
          and not isinstance(journal["checkpointed_at"], bool),
          "checkpointed_at must be a number", "checkpointed_at")
    CG.validate_session_state(journal["session_state"])   # re-seals working graph
    _, names = _canonical_scenario_docs(journal["scenario_documents"],
                                        "scenario_documents")
    sel = journal["selected_scenario_document_id"]
    _reqr(sel is None or (isinstance(sel, str) and sel in names),
          "selected_scenario_document_id must be null or a present scenario name",
          "selected_scenario_document_id")
    dr = journal["dirty_reasons"]
    _reqr(isinstance(dr, list), "dirty_reasons must be a list", "dirty_reasons")
    for r in dr:
        _reqr(isinstance(r, str) and r in _DIRTY_REASONS,
              "dirty_reasons entries must be one of %s, got %r"
              % (sorted(_DIRTY_REASONS), r), "dirty_reasons")
    return journal


def canonicalize_recovery_journal(journal):
    """Validate then return the CANONICAL journal form: scenario_documents sorted
    by name (digests recomputed), dirty_reasons de-duplicated + sorted,
    session_state plainified. Pure projection; never moves identity."""
    validate_recovery_journal(journal)
    scen_out, _ = _canonical_scenario_docs(journal["scenario_documents"],
                                           "scenario_documents")
    return {
        "recovery_version": RECOVERY_VERSION,
        "project_id": journal["project_id"],
        "base_project_revision": journal["base_project_revision"],
        "recovery_revision": journal["recovery_revision"],
        "checkpointed_at": journal["checkpointed_at"],
        "session_state": WC._plain(journal["session_state"]),
        "scenario_documents": scen_out,
        "selected_scenario_document_id":
            journal["selected_scenario_document_id"],
        "dirty_reasons": sorted(set(journal["dirty_reasons"])),
    }


def serialize_recovery_journal(journal):
    """Deterministic canonical bytes of a recovery journal (NOT content-addressed
    -- it carries a wall clock + a per-journal recovery_revision -- so its bytes are
    a stable serialization, never an identity)."""
    return WC.serialize_artifact(canonicalize_recovery_journal(journal))


# ------------------------------------------------------------- the store
class ForgeProjectStore:
    """A directory of named `<project_id>.json` project documents with atomic
    writes and per-project exact-CAS revision."""

    def __init__(self, root):
        self._root = root
        os.makedirs(root, exist_ok=True)

    def _path(self, pid):
        return os.path.join(self._root, pid + ".json")

    def exists(self, pid):
        return isinstance(pid, str) and bool(_PROJECT_ID_RE.match(pid)) \
            and os.path.exists(self._path(pid))

    def list_projects(self):
        try:
            names = os.listdir(self._root)
        except OSError:
            return []
        return sorted(n[:-5] for n in names if n.endswith(".json")
                      and _PROJECT_ID_RE.match(n[:-5]))

    def list_project_infos(self):
        """A lightweight per-project summary for the Library panel:
        `[{project_id, name, project_version, revision, active_world_semantic_id,
        scenarios, commits}]`, sorted by name then id. Version-agnostic (reads V1 or
        V2) and surfaces each project's `project_version` so the Library can offer a
        forward migration for a legacy V1 project (v0.6-3). Reads each document
        (cheap: no re-lowering). A project that fails to load is skipped rather than
        breaking the whole listing."""
        out = []
        for pid in self.list_projects():
            try:
                doc = self.load(pid)
            except Exception:
                continue
            ver = project_version_of(doc)
            commits = (doc["commit_history"] if ver == PROJECT_V2_VERSION
                       else doc["commits"])
            out.append({"project_id": doc["project_id"], "name": doc["name"],
                        "project_version": ver,
                        "revision": _revision_of(doc),
                        "active_world_semantic_id": _active_world_id_of(doc),
                        "scenarios": len(_scenarios_of(doc)),
                        "commits": len(commits)})
        return sorted(out, key=lambda d: (d["name"], d["project_id"]))

    def create(self, doc):
        """Create a NEW project (V1 or V2) at revision 0. Refuses to clobber an
        existing id (WRL_PROJECT_EXISTS). The stored revision is forced to 0
        regardless of the input."""
        doc = canonicalize_project(_with_revision(canonicalize_project(doc), 0))
        pid = doc["project_id"]
        if self.exists(pid):
            WC._fail(WRL_PROJECT_EXISTS, "project %r already exists" % pid)
        ST._atomic_write(self._path(pid), serialize_project_doc(doc))
        return doc

    def load(self, pid):
        """Load + validate a project (V1 or V2). WRL_PROJECT_MISSING if absent."""
        if not self.exists(pid):
            WC._fail(WRL_PROJECT_MISSING, "no project %r" % (pid,))
        with open(self._path(pid), "rb") as f:
            blob = f.read()
        return canonicalize_project(WC.deserialize_artifact(blob))

    def save(self, doc, expected_revision):
        """Persist an updated project (V1 or V2) with EXACT-CAS on the revision.
        The on-disk revision must equal `expected_revision` (else
        WRL_PROJECT_STALE, no auto-merge); the saved revision is bumped to
        `expected_revision + 1`. The saved version must match the on-disk version
        (a project doc is not silently up/down-graded on save)."""
        doc = canonicalize_project(doc)
        pid = doc["project_id"]
        if not self.exists(pid):
            WC._fail(WRL_PROJECT_MISSING, "no project %r to save" % (pid,))
        current = self.load(pid)
        if project_version_of(current) != project_version_of(doc):
            WC._fail(WRL_BAD_PROJECT,
                     "cannot save a %s document over an on-disk %s project %r"
                     % (project_version_of(doc), project_version_of(current), pid))
        cur_rev = _revision_of(current)
        if cur_rev != expected_revision:
            WC._fail(WRL_PROJECT_STALE,
                     "stale save of %r: expected on-disk revision %d, found %d"
                     % (pid, expected_revision, cur_rev),
                     field_path=_REV_FIELD[project_version_of(doc)])
        out = canonicalize_project(_with_revision(doc, expected_revision + 1))
        ST._atomic_write(self._path(pid), serialize_project_doc(out))
        return out

    def rename(self, pid, new_name, expected_revision):
        """Rename a project's DISPLAY name (the `project_id` identity key is
        immutable). Exact-CAS on the revision like any other save; the world,
        layout, scenarios and commit log are untouched."""
        doc = self.load(pid)
        doc = dict(doc)
        doc["name"] = new_name
        return self.save(doc, expected_revision)

    def fork(self, src_pid, new_pid, new_name=None):
        """Copy a project's SAVED state (world reference + source, layout,
        scenarios, commit log) into a NEW project at revision 0. The world and
        scenario objects are shared by REFERENCE -- they are content-addressed in
        the immutable substrate, so nothing is duplicated there. Refuses to
        clobber an existing `new_pid` (WRL_PROJECT_EXISTS via create)."""
        src = self.load(src_pid)
        doc = _with_revision(src, 0)   # version-correct rev field (create re-zeros)
        doc["project_id"] = new_pid
        doc["name"] = new_name if new_name else (src["name"] + " (fork)")
        return self.create(doc)

    # ------------------------------------------------- v0.6-3 project migration
    def project_version(self, pid):
        """The persisted `project_version` of a stored project (WRL_PROJECT_MISSING
        if absent). A cheap read for deciding whether a migration is available."""
        return project_version_of(self.load(pid))

    def migrate(self, pid):
        """Forward-only, identity-preserving upgrade of a stored ForgeProjectV1 to
        ForgeProjectV2, rewriting the on-disk document atomically at the SAME
        revision (a representation upgrade is not a workspace edit, so it does NOT
        advance `project_revision` and moves NO SemanticArtifactID). Raises
        WRL_PROJECT_MISSING if absent, or WRL_PROJECT_MIGRATION if the on-disk
        project is not a V1 (an already-V2 project has nothing to migrate). Returns
        the migrated, canonicalized V2 document. Because the store's exact-CAS
        `save` refuses to write a V2 document over an on-disk V1 one, this is the
        ONLY path that moves a project across the version boundary."""
        current = self.load(pid)   # WRL_PROJECT_MISSING if absent
        if project_version_of(current) != PROJECT_VERSION:
            WC._fail(WRL_PROJECT_MIGRATION,
                     "project %r is already %s -- nothing to migrate"
                     % (pid, project_version_of(current)))
        v2 = migrate_project_v1_to_v2(current)
        ST._atomic_write(self._path(pid), serialize_project_doc(v2))
        return v2

    # ------------------------------------------------- v0.5.1 restorable trash
    def _trash_dir(self):
        return os.path.join(self._root, ".trash")

    def _trash_path(self, trash_id):
        return os.path.join(self._trash_dir(), trash_id + ".json")

    def trash(self, pid, now=None):
        """Move a project into NON-DESTRUCTIVE trash storage as a restorable
        `TrashEntryV1` tombstone. The tombstone records the FULL project document
        plus its original id + revision + a deletion timestamp, so `restore` can
        bring the project back verbatim. The shared immutable world/scenario
        objects are never touched (a project references them; deletion drops only
        the mutable named document). Whole-project deletion stays a single
        mutable-file operation, distinct from the DEFERRED multi-op atomic
        graph-object deletion. Returns the tombstone path. WRL_PROJECT_MISSING if
        the project is absent."""
        if not self.exists(pid):
            WC._fail(WRL_PROJECT_MISSING, "no project %r to trash" % (pid,))
        doc = self.load(pid)
        os.makedirs(self._trash_dir(), exist_ok=True)
        n = 0
        while True:
            trash_id = "%s.%d" % (pid, n)
            dst = self._trash_path(trash_id)
            if not os.path.exists(dst):
                break
            n += 1
        entry = {
            "trash_entry_version": TRASH_ENTRY_VERSION,
            "trash_id": trash_id,
            "original_project_id": pid,
            "deleted_project_revision": _revision_of(doc),
            "deleted_at": float(now) if now is not None else time.time(),
            "project_document": doc,
        }
        validate_trash_entry(entry)
        # write the tombstone FIRST, then drop the live document -- so a crash
        # between the two leaves the project recoverable (tombstone present) or
        # intact (tombstone absent), never lost.
        ST._atomic_write(dst, serialize_trash_entry(entry))
        os.remove(self._path(pid))
        return dst

    def list_trash(self):
        """Restorable trash tombstones as lightweight summaries, newest deletion
        first: `[{trash_id, original_project_id, deleted_project_revision,
        deleted_at, name, project_version}]`. A tombstone that fails to load is
        skipped rather than breaking the whole listing."""
        try:
            names = os.listdir(self._trash_dir())
        except OSError:
            return []
        out = []
        for fn in names:
            if not fn.endswith(".json"):
                continue
            try:
                with open(os.path.join(self._trash_dir(), fn), "rb") as f:
                    entry = validate_trash_entry(WC.deserialize_artifact(f.read()))
            except Exception:
                continue
            doc = entry["project_document"]
            out.append({"trash_id": entry["trash_id"],
                        "original_project_id": entry["original_project_id"],
                        "deleted_project_revision":
                            entry["deleted_project_revision"],
                        "deleted_at": entry["deleted_at"],
                        "name": doc["name"],
                        "project_version": doc["project_version"]})
        return sorted(out, key=lambda d: (-d["deleted_at"], d["trash_id"]))

    def load_trash(self, trash_id):
        """Load + validate a trash tombstone. WRL_TRASH_MISSING if absent."""
        if not (isinstance(trash_id, str) and _TRASH_ID_RE.match(trash_id)
                and os.path.exists(self._trash_path(trash_id))):
            WC._fail(WRL_TRASH_MISSING, "no trash entry %r" % (trash_id,))
        with open(self._trash_path(trash_id), "rb") as f:
            return validate_trash_entry(WC.deserialize_artifact(f.read()))

    def restore(self, trash_id, new_project_id=None):
        """Restore a trashed project from its tombstone. Restores under the
        ORIGINAL project id when that id is free; a caller may supply
        `new_project_id` to restore under a different id (its project_id is
        rewritten to match). Restoration is NON-DESTRUCTIVE: it refuses to
        overwrite a live project (WRL_PROJECT_EXISTS) -- never a silent clobber.
        The restored document is written FIRST (durable) and only THEN is the
        tombstone removed, so a crash mid-restore leaves the project recoverable.
        The immutable world/scenario objects are untouched. Returns the restored,
        canonicalized document."""
        entry = self.load_trash(trash_id)
        doc = entry["project_document"]
        target = new_project_id if new_project_id is not None \
            else entry["original_project_id"]
        _req(isinstance(target, str) and bool(_PROJECT_ID_RE.match(target)),
             "restore target id must match %s, got %r"
             % (_PROJECT_ID_RE.pattern, target), "project_id")
        if self.exists(target):
            WC._fail(WRL_PROJECT_EXISTS,
                     "cannot restore over live project %r (choose a new id)"
                     % (target,))
        out = dict(doc)
        out["project_id"] = target
        out = canonicalize_project(out)   # preserves the deleted revision + version
        ST._atomic_write(self._path(target), serialize_project_doc(out))
        os.remove(self._trash_path(trash_id))   # drop tombstone only after durable
        return out


# ------------------------------------------------- v0.6-0 RecoveryJournalStore
class RecoveryJournalStore:
    """A directory of `<project_id>.json` crash-recovery journals -- ONE overlay
    per project, keyed by project_id (mutable, last-writer-wins), NOT
    content-addressed. It is intentionally a SIBLING of the project store (its own
    `.recovery/` root), never nested in a project bundle: a journal is emergency
    overlay, not durable project state. Writes obey the same atomic-write law as
    every other store (validate -> serialize -> temp -> flush+fsync -> atomic
    rename), so a crash mid-checkpoint leaves at most a `.tmp-*` stub, never a torn
    journal. Delete is idempotent (clearing an absent journal is a no-op)."""

    def __init__(self, root):
        self._root = root
        os.makedirs(root, exist_ok=True)

    def _path(self, pid):
        return os.path.join(self._root, pid + ".json")

    def exists(self, pid):
        return isinstance(pid, str) and bool(_PROJECT_ID_RE.match(pid)) \
            and os.path.exists(self._path(pid))

    def write(self, journal):
        """Persist (overwrite) a project's recovery journal atomically; returns the
        canonicalized journal. Refuses a project_id that is not a valid id."""
        journal = canonicalize_recovery_journal(journal)
        pid = journal["project_id"]
        _reqr(bool(_PROJECT_ID_RE.match(pid)), "bad project_id %r" % (pid,),
              "project_id")
        ST._atomic_write(self._path(pid), serialize_recovery_journal(journal))
        return journal

    def load(self, pid):
        """Load + validate a journal. WRL_RECOVERY_MISSING if absent."""
        if not self.exists(pid):
            WC._fail(WRL_RECOVERY_MISSING, "no recovery journal %r" % (pid,))
        with open(self._path(pid), "rb") as f:
            return canonicalize_recovery_journal(WC.deserialize_artifact(f.read()))

    def delete(self, pid):
        """Drop a project's recovery journal (idempotent -- absent is a no-op)."""
        try:
            os.remove(self._path(pid))
        except OSError:
            pass

    def list_ids(self):
        """Every project id with a live recovery journal, sorted."""
        try:
            names = os.listdir(self._root)
        except OSError:
            return []
        return sorted(n[:-5] for n in names if n.endswith(".json")
                      and _PROJECT_ID_RE.match(n[:-5]))


# ------------------------------------------------- session <-> project bridge
def session_to_project(session, project_id, name, scenarios=None, revision=0):
    """Build a ForgeProjectV1 from a CanvasSession's durable state. The session's
    working graph must be VALID (a project references a real sealed world); the
    persisted `active_world_semantic_id` is that valid working graph's id and the
    `world_source` is its canonical WRL Core (reopenable)."""
    if session.draft.candidate_error is not None:
        WC._fail(WRL_BAD_PROJECT,
                 "cannot persist a project over an invalid world: %s"
                 % (session.draft.candidate_error,))
    doc = {
        "project_version": PROJECT_VERSION,
        "project_id": project_id,
        "name": name,
        "revision": revision,
        "active_world_semantic_id": session.draft.candidate_semantic_id,
        "world_source": session.to_text(),
        "layout": CV.validate_layout_v1(copy.deepcopy(session.layout)),
        "scenarios": [dict(s) for s in (scenarios or [])],
        "commits": copy.deepcopy(session.commits),
    }
    return canonicalize_project_v1(doc)


def session_to_project_v2(session, project_id, name, scenarios=None,
                          project_revision=0, selected_scenario_document_id=None,
                          scenario_compatibility=None):
    """Build a ForgeProjectV2 from a CanvasSession's COMPLETE workspace (the
    v0.5.1 Save contract). Unlike `session_to_project` (V1) this does NOT require
    the working graph to be valid: an invalid / uncommitted draft, the raw editor
    buffer, the undo + idempotency state, and the scenario selection are all
    persisted verbatim. The `active_world` is the last COMMITTED world -- its
    retained canonical source and id, independent of the (possibly diverged)
    working graph -- so the active sealed world stays runnable beside an invalid
    draft. This moves NO SemanticArtifactID."""
    ws = CG.session_state(session)
    draft_block = dict(ws["draft"])
    draft_block["layout_undo_history"] = ws["layout_history"]
    sel = (selected_scenario_document_id
           if selected_scenario_document_id is not None
           else session.selected_scenario)
    compat = (scenario_compatibility if scenario_compatibility is not None
              else session.scenario_compatibility)
    doc = {
        "project_version": PROJECT_V2_VERSION,
        "project_id": project_id,
        "name": name,
        "project_revision": project_revision,
        "active_world": {"semantic_id": session.draft.active_semantic_id,
                         "canonical_source": session.active_world_source},
        "draft": draft_block,
        "source_document": copy.deepcopy(session.source_document),
        "canvas_layout": CV.validate_layout_v1(copy.deepcopy(session.layout)),
        "scenario_documents": [dict(s) for s in (scenarios or [])],
        "selected_scenario_document_id": sel,
        "scenario_compatibility": copy.deepcopy(compat),
        "commit_history": copy.deepcopy(session.commits),
    }
    return canonicalize_project_v2(doc)


def make_scenario_entry(name, scenario):
    """A `{name, scenario_digest, scenario}` project scenario entry (digest
    computed from the scenario)."""
    SC.validate_scenario_v1(scenario)
    return {"name": name,
            "scenario_digest": SC.scenario_digest(scenario),
            "scenario": SC.canonicalize_scenario_v1(scenario)}


def open_session_from_project(doc, draft_id="main"):
    """Re-lower a persisted project's `world_source` into a fresh CanvasSession,
    assert it reproduces `active_world_semantic_id` (closure), and restore the
    persisted layout + commit log. The undo stack starts empty (session-local)."""
    doc = canonicalize_project_v1(doc)
    prog = W.lower_program(SG.desugar_core(doc["world_source"]), W.parse_wrl_core)
    if prog.semantic_artifact_id != doc["active_world_semantic_id"]:
        WC._fail(WRL_BAD_PROJECT,
                 "world_source lowers to %r but active_world_semantic_id is %r"
                 % (prog.semantic_artifact_id, doc["active_world_semantic_id"]))
    session = CG.new_session(prog, draft_id)
    session.layout = CV.validate_layout_v1(copy.deepcopy(doc["layout"]))
    session.commits = copy.deepcopy(doc["commits"])
    return session


def open_session_from_project_v2(doc, draft_id="main"):
    """Reconstruct the COMPLETE CanvasSession workspace from a ForgeProjectV2 (the
    inverse of `session_to_project_v2`): the exact draft (valid OR invalid), the
    paired layout undo stack, the presentation, the raw editor buffer, the
    retained active-world source, the commit log, and the scenario selection all
    come back verbatim. The draft's `draft_id` is taken from the persisted state
    (NOT `draft_id`, which is kept only for signature parity with the V1 opener).
    Closure: the retained active-world canonical source MUST re-lower to its stored
    id -- otherwise the persisted active world is corrupt (WRL_BAD_PROJECT)."""
    doc = canonicalize_project_v2(doc)
    aw = doc["active_world"]
    prog = W.lower_program(SG.desugar_core(aw["canonical_source"]),
                           W.parse_wrl_core)
    if prog.semantic_artifact_id != aw["semantic_id"]:
        WC._fail(WRL_BAD_PROJECT,
                 "active_world canonical_source lowers to %r but semantic_id is %r"
                 % (prog.semantic_artifact_id, aw["semantic_id"]))
    draft_state = {k: v for k, v in doc["draft"].items()
                   if k != "layout_undo_history"}
    ws = {
        "session_state_version": CG.SESSION_STATE_VERSION,
        "draft": draft_state,
        "layout": copy.deepcopy(doc["canvas_layout"]),
        "layout_history": copy.deepcopy(doc["draft"]["layout_undo_history"]),
        "commits": copy.deepcopy(doc["commit_history"]),
        "source_document": copy.deepcopy(doc["source_document"]),
        "active_world_source": aw["canonical_source"],
        "selected_scenario": doc["selected_scenario_document_id"],
        "scenario_compatibility": copy.deepcopy(doc["scenario_compatibility"]),
    }
    return CG.restore_session(ws)


def open_session_from_project_any(doc, draft_id="main"):
    """Version-dispatched project opener (V1 committed-world reopen or V2 full
    workspace reconstruction)."""
    return (open_session_from_project(doc, draft_id)
            if project_version_of(doc) == PROJECT_VERSION
            else open_session_from_project_v2(doc, draft_id))


# ------------------------------------------ v0.6-3 project-doc migration (V1->V2)
# A ForgeProjectV1 document is the committed-world-only durability of v0.5-2..v0.5-4;
# ForgeProjectV2 (v0.5.1) persists the COMPLETE authoring workspace. A V2 cache can
# READ a legacy V1 project (opening is version-dispatched), but a SAVE re-serializes
# the session as V2 and the store refuses to write a V2 document over an on-disk V1
# one (a project is never silently up/down-graded on save) -- so without a migration
# a pre-existing V1 project is effectively read-only under the current package. The
# migration closes that gap. It is FORWARD-ONLY (V1 -> V2, never the reverse) and
# IDENTITY-PRESERVING: it re-opens the V1 project through the SAME validated seam a
# reopen uses (`open_session_from_project`, which re-lowers `world_source` and
# asserts it reproduces `active_world_semantic_id`) and then re-serializes that exact
# session as V2 (`session_to_project_v2`). Because a V1 project always references a
# VALID committed world, the resulting V2 draft is that same clean committed world
# (no divergence), `active_world.semantic_id` is the V1 `active_world_semantic_id`
# unchanged, `world_source` becomes `active_world.canonical_source`, and the V1
# `scenarios` become the V2 `scenario_documents`. It moves NO SemanticArtifactID and
# preserves the project_revision (a representation upgrade, not a workspace edit).
def migrate_project_v1_to_v2(doc):
    """Upgrade a ForgeProjectV1 document to a ForgeProjectV2 one, forward-only and
    identity-preserving (see the block comment). Raises WRL_PROJECT_MIGRATION if the
    document is not a V1 project (an already-V2 doc has nothing to migrate). The
    returned V2 document keeps the same `project_id`, display `name`, and revision;
    its `active_world.semantic_id` is byte-for-byte the V1 `active_world_semantic_id`
    (asserted below), and its `scenario_documents` are the V1 `scenarios`."""
    if not isinstance(doc, dict) or doc.get("project_version") != PROJECT_VERSION:
        WC._fail(WRL_PROJECT_MIGRATION,
                 "not a %s project to migrate (got project_version %r)"
                 % (PROJECT_VERSION, (doc.get("project_version")
                                      if isinstance(doc, dict) else None)),
                 field_path="project_version")
    v1 = canonicalize_project_v1(doc)
    session = open_session_from_project(v1, v1["project_id"])
    v2 = session_to_project_v2(session, v1["project_id"], v1["name"],
                               scenarios=v1["scenarios"],
                               project_revision=v1["revision"])
    if v2["active_world"]["semantic_id"] != v1["active_world_semantic_id"]:
        WC._fail(WRL_PROJECT_MIGRATION,
                 "migration moved the active world identity %r -> %r"
                 % (v1["active_world_semantic_id"],
                    v2["active_world"]["semantic_id"]))
    return v2


def sync_project_objects(doc, world_store, scenario_store):
    """Tie a project to the IMMUTABLE substrate: put the project's world into the
    WorldObjectStore and each scenario's runtime into the ScenarioRuntimeStore,
    so the project's references are all resolvable (closure). Returns the world
    SemanticArtifactID. Idempotent (the stores are content-addressed)."""
    doc = canonicalize_project_v1(doc)
    prog = W.lower_program(SG.desugar_core(doc["world_source"]), W.parse_wrl_core)
    if prog.semantic_artifact_id != doc["active_world_semantic_id"]:
        WC._fail(WRL_BAD_PROJECT,
                 "world_source lowers to %r but active_world_semantic_id is %r"
                 % (prog.semantic_artifact_id, doc["active_world_semantic_id"]))
    sem = world_store.put(prog.sealed_artifact)
    for s in doc["scenarios"]:
        scenario_store.put(s["scenario"])
    return sem


# --------------------------------------------- v0.5-3 project session cache
class ProjectSessionCache:
    """An in-memory cache of open CanvasSessions backed by a ForgeProjectStore.

    Each `project_id` maps to ONE live editing session. Durability depends on the
    cache's project version:

      * V1 cache -- only the COMMITTED state of a session is durable (a project
        stores its world by reference: `world_source` + `active_world_semantic_id`
        + layout + commit log); the uncommitted draft working graph and undo stack
        are session-local (the v0.5-2 rule). A commit is the persistence boundary.

      * V2 cache -- `persist` (Save) writes the COMPLETE workspace: the exact draft
        (valid OR invalid), the raw editor buffer, the paired layout + semantic undo
        stacks, the retained last-committed active world, and the scenario selection
        (the v0.5.1 rule). A FRESH cache over the same store reconstructs the whole
        saved workspace (unsaved-but-Saved edits survive a restart).

    Both versions persist only on EXPLICIT Save/Commit -- `persist` uses per-project
    exact-CAS on the revision. A first access to an unknown `project_id` lazily
    CREATES a default project from `default_world_source` (+ optional
    `scenarios_for(sem_id)` entries), so the server has no separate bootstrap step.
    `reset` discards unsaved edits by re-opening the session from the persisted
    document (revert-to-saved) without wiping the stored project.

    v0.6-0 crash recovery: the cache ALSO drives a separate, non-authoritative
    `RecoveryJournalStore` (its own `.recovery/` root, a sibling of the project
    store). `checkpoint` writes the current unsaved workspace to a per-project
    journal WITHOUT touching the durable project, advancing its revision, moving any
    identity, or activating a candidate. A successful Save/Commit CLEARS the journal
    only AFTER the durable project write; a FAILED Save leaves it intact. On reopen
    the journal is NEVER auto-applied -- `recovery_status` reports it, `recover`
    loads it as an unsaved dirty workspace (the user must still Save), `discard`
    drops it, and a stale journal (its `base_project_revision` != the saved
    `project_revision`) is offered only as an `open_as_recovered_copy` (a brand-new
    project, never an auto-merge)."""

    def __init__(self, store, default_world_source, scenarios_for=None,
                 project_version=PROJECT_VERSION, recovery_store=None):
        self._store = store
        self._default_src = default_world_source
        self._scenarios_for = scenarios_for      # sem_id -> [scenario entry] | None
        self._sessions = {}                      # project_id -> CanvasSession
        self._revisions = {}                     # project_id -> known on-disk rev
        self._recovery_revs = {}                 # project_id -> last recovery_revision
        # which project-doc version this cache CREATES + persists. V1 (default)
        # keeps the committed-world-only durability (the accepted v0.5-4
        # batteries); V2 persists the COMPLETE workspace (v0.5.1). Opening is
        # always version-dispatched, so a V2 cache still reads any pre-existing
        # V1 project on disk.
        if project_version not in (PROJECT_VERSION, PROJECT_V2_VERSION):
            WC._fail(WRL_BAD_PROJECT,
                     "unknown cache project_version %r" % (project_version,))
        self._version = project_version
        # the crash-recovery overlay store -- a SIBLING of the project store by
        # default (`<store-parent>/.recovery`), never nested inside `projects/`.
        if recovery_store is None:
            parent = os.path.dirname(os.path.abspath(self._store._root))
            recovery_store = RecoveryJournalStore(os.path.join(parent, ".recovery"))
        self._recovery = recovery_store

    def _default_doc(self, project_id, name=None):
        prog = W.lower_program(SG.desugar_core(self._default_src),
                               W.parse_wrl_core)
        session = CG.new_session(prog, project_id)
        scen = (self._scenarios_for(prog.semantic_artifact_id)
                if self._scenarios_for else None)
        if self._version == PROJECT_V2_VERSION:
            return session_to_project_v2(session, project_id, name or project_id,
                                         scenarios=scen)
        return session_to_project(session, project_id, name or project_id,
                                  scenarios=scen)

    def ensure(self, project_id, name=None):
        """Ensure a project exists on disk (create it from the default world if
        absent) and return its loaded, canonicalized document."""
        if not self._store.exists(project_id):
            self._store.create(self._default_doc(project_id, name))
        return self._store.load(project_id)

    def open(self, project_id, name=None):
        """Return the live CanvasSession for `project_id`, opening it from the
        persisted project (lazily creating a default project if none exists).
        Version-dispatched: a V1 project reopens at its last committed world; a V2
        project reconstructs the complete saved workspace."""
        if project_id not in self._sessions:
            doc = self.ensure(project_id, name)
            self._sessions[project_id] = open_session_from_project_any(
                doc, project_id)
            self._revisions[project_id] = _revision_of(doc)
        return self._sessions[project_id]

    def persist(self, project_id):
        """SAVE the session's workspace back to the store with exact-CAS on the
        project revision. In a V1 cache this persists only the COMMITTED state and
        requires a valid working graph (a commit leaves it valid). In a V2 cache
        this is the full Save-workspace contract: the exact draft (valid OR
        invalid), the raw editor buffer, undo + idempotency state and scenario
        selection are all written, and the last-committed world stays retained as
        `active_world`. Returns the saved document."""
        session = self._sessions[project_id]
        current = self._store.load(project_id)
        scen = _scenarios_of(current)
        if self._version == PROJECT_V2_VERSION:
            updated = session_to_project_v2(
                session, project_id, current["name"], scenarios=scen,
                project_revision=self._revisions[project_id])
        else:
            updated = session_to_project(session, project_id, current["name"],
                                         scenarios=scen,
                                         revision=self._revisions[project_id])
        saved = self._store.save(updated,
                                 expected_revision=self._revisions[project_id])
        # the durable project write SUCCEEDED (save raises WRL_PROJECT_STALE /
        # WRL_PROJECT_MISSING on failure, so control only reaches here on a durable
        # write). Only NOW clear the recovery journal: a failed Save keeps it.
        self._revisions[project_id] = _revision_of(saved)
        self._clear_recovery(project_id)
        return saved

    def reset(self, project_id, name=None):
        """Re-open the session from the persisted project document (revert-to-saved,
        discarding IN-MEMORY unsaved edits). In a V2 cache this reverts to the last
        SAVED workspace (which may itself hold an invalid draft), not merely the last
        committed world. Never wipes the stored project. The on-disk recovery
        journal is DELIBERATELY left intact: revert-to-saved is also the server's
        boot/reopen path, and a reopen must NEVER auto-clear (or auto-apply) a
        crash-recovery journal -- the journal is cleared only by an explicit
        Save/Commit (after a durable write) or an explicit Discard."""
        doc = self.ensure(project_id, name)
        self._sessions[project_id] = open_session_from_project_any(doc,
                                                                   project_id)
        self._revisions[project_id] = _revision_of(doc)
        return self._sessions[project_id]

    def revision(self, project_id):
        """The last-known on-disk revision for an OPEN session (or None)."""
        return self._revisions.get(project_id)

    # ----------------------------------------- v0.5-4 Library management
    def list_infos(self):
        """Per-project summaries for the Library panel (delegates to the store)."""
        return self._store.list_project_infos()

    def create_new(self, project_id, name=None):
        """Create a BRAND-NEW project seeded with the default world (refuses to
        clobber an existing id, WRL_PROJECT_EXISTS) and open its session."""
        self._store.create(self._default_doc(project_id, name))
        return self.open(project_id, name)

    def create_from_source(self, project_id, name, world_source,
                           scenarios=None, selected_scenario_document_id=None):
        """Create a BRAND-NEW project seeded from an EXPLICIT world source +
        scenario documents (the v0.7-3 "Use Template" instantiation path). Mirrors
        `create_new` but lowers `world_source` instead of the cache default, and
        seeds the given `scenarios` ({name, scenario_digest, scenario} entries)
        with an initial `selected_scenario_document_id`. Refuses to clobber an
        existing id (WRL_PROJECT_EXISTS). The new project is a fully-independent
        ForgeProjectV2 whose subsequent mutable state never touches the source it
        was seeded from."""
        prog = W.lower_program(SG.desugar_core(world_source), W.parse_wrl_core)
        session = CG.new_session(prog, project_id)
        if self._version == PROJECT_V2_VERSION:
            doc = session_to_project_v2(
                session, project_id, name or project_id, scenarios=scenarios,
                selected_scenario_document_id=selected_scenario_document_id)
        else:
            doc = session_to_project(session, project_id, name or project_id,
                                     scenarios=scenarios)
        self._store.create(doc)
        return self.open(project_id, name)

    def fork(self, source_id, project_id, name=None):
        """Fork a project's SAVED state into a new project id and open it. The
        forked session reflects the source's last committed world (uncommitted
        edits in an open source session are NOT forked)."""
        self._store.fork(source_id, project_id, name)
        return self.open(project_id)

    def rename(self, project_id, name):
        """Rename a project's display name with exact-CAS on its revision; keeps
        the in-memory revision (and any open session's working graph) coherent."""
        expected = self._revisions.get(project_id)
        if expected is None:
            expected = _revision_of(self._store.load(project_id))
        saved = self._store.rename(project_id, name, expected)
        if project_id in self._sessions:
            self._revisions[project_id] = _revision_of(saved)
        return saved

    def trash(self, project_id):
        """Move a project into non-destructive trash storage (a restorable
        TrashEntryV1 tombstone) and drop any open session for it. Any live recovery
        journal is cleared -- the trashed project's overlay is no longer meaningful
        (a later Restore reopens the SAVED workspace, not an unsaved overlay)."""
        path = self._store.trash(project_id)
        self._sessions.pop(project_id, None)
        self._revisions.pop(project_id, None)
        self._clear_recovery(project_id)
        return path

    def list_trash(self):
        """Restorable trash tombstones for the Library panel (delegates to the
        store)."""
        return self._store.list_trash()

    def restore(self, trash_id, new_project_id=None):
        """Restore a trashed project from its tombstone (original id when free,
        else a caller-supplied id; never a silent clobber) and open its session.
        A V2 tombstone reconstructs the complete saved workspace on open."""
        restored = self._store.restore(trash_id, new_project_id)
        return self.open(restored["project_id"])

    # ----------------------------------------- v0.6-3 project-doc migration
    def project_version(self, project_id):
        """The persisted project_version of a stored project (WRL_PROJECT_MISSING
        if absent) -- lets the Library surface a "migrate to v2" affordance for a
        legacy project without opening a session."""
        return self._store.project_version(project_id)

    def migrate(self, project_id):
        """Forward-only, identity-preserving upgrade of a stored ForgeProjectV1 to
        ForgeProjectV2 (delegates to the store), then re-open the migrated project
        so the live session + tracked revision are coherent. Raises
        WRL_PROJECT_MIGRATION if the project is not a V1. After migration a V2 cache
        can Save the project normally (the pre-migration read-only gap is closed).
        Any open session is dropped and re-opened from the migrated document; the
        recovery journal is left intact (a migration is not a Save)."""
        migrated = self._store.migrate(project_id)   # atomic V1 -> V2 rewrite
        self._sessions.pop(project_id, None)
        self._sessions[project_id] = open_session_from_project_any(migrated,
                                                                   project_id)
        self._revisions[project_id] = _revision_of(migrated)
        return migrated

    # ----------------------------------------- v0.6-0 crash recovery journal
    def _clear_recovery(self, project_id):
        """Drop a project's recovery journal + reset its per-project revision
        counter (idempotent)."""
        self._recovery.delete(project_id)
        self._recovery_revs.pop(project_id, None)

    def checkpoint(self, project_id, scenario_documents=None,
                   selected_scenario_document_id=None, dirty_reasons=None,
                   now=None):
        """Write a RecoveryJournalV1 for the current UNSAVED workspace. This is a
        pure overlay write: it NEVER calls the project store, so it cannot advance
        `project_revision`, move any semantic identity, activate a candidate, or
        touch Fork/export. `session_state` is the exact `wrl_converge.session_state`
        of the live session (valid OR invalid draft); the scenario documents +
        selection come from the caller (the client's working scenario author) and
        default to the project's SAVED scenario_documents when omitted. Returns the
        canonicalized journal."""
        session = self.open(project_id)
        base_rev = self._revisions[project_id]
        if scenario_documents is None:
            scenario_documents = _scenarios_of(self._store.load(project_id))
        rr = self._recovery_revs.get(project_id, -1) + 1
        journal = {
            "recovery_version": RECOVERY_VERSION,
            "project_id": project_id,
            "base_project_revision": base_rev,
            "recovery_revision": rr,
            "checkpointed_at": float(now) if now is not None else time.time(),
            "session_state": CG.session_state(session),
            "scenario_documents": scenario_documents,
            "selected_scenario_document_id": selected_scenario_document_id,
            "dirty_reasons": list(dirty_reasons or []),
        }
        written = self._recovery.write(journal)
        self._recovery_revs[project_id] = rr
        return written

    def recovery_status(self, project_id):
        """The PERSISTED recovery state for `project_id` -- what a fresh restart
        would find on disk (never in-memory dirtiness). One of: `saved` (no
        journal), `recovery_available` (a journal whose base matches the saved
        project revision) or `recovery_stale` (a journal whose base != the saved
        revision, offered only as an open-as-copy). Includes the checkpoint's age +
        validity for the reopen prompt."""
        if not self._store.exists(project_id):
            return {"state": "saved", "has_journal": False,
                    "project_exists": False}
        saved_rev = _revision_of(self._store.load(project_id))
        if not self._recovery.exists(project_id):
            return {"state": "saved", "has_journal": False,
                    "project_exists": True, "saved_project_revision": saved_rev}
        journal = self._recovery.load(project_id)
        stale = journal["base_project_revision"] != saved_rev
        return {
            "state": "recovery_stale" if stale else "recovery_available",
            "has_journal": True,
            "project_exists": True,
            "stale": stale,
            "saved_project_revision": saved_rev,
            "base_project_revision": journal["base_project_revision"],
            "recovery_revision": journal["recovery_revision"],
            "checkpointed_at": journal["checkpointed_at"],
            "dirty_reasons": journal["dirty_reasons"],
        }

    def inspect_recovery(self, project_id):
        """A non-destructive summary of a recovery journal for the Inspect action:
        checkpoint age, draft validity, active-vs-candidate semantic id, whether the
        candidate differs from the saved active world, source parse status, undo
        depth, scenario-document count + selection, and staleness. Reads only -- it
        never applies the journal. WRL_RECOVERY_MISSING if none."""
        journal = self._recovery.load(project_id)
        ss = journal["session_state"]
        draft = ss["draft"]
        saved_rev = (_revision_of(self._store.load(project_id))
                     if self._store.exists(project_id) else None)
        active_id = draft["active_semantic_id"]
        candidate_id = draft.get("candidate_semantic_id")
        return {
            "project_id": project_id,
            "checkpointed_at": journal["checkpointed_at"],
            "recovery_revision": journal["recovery_revision"],
            "base_project_revision": journal["base_project_revision"],
            "saved_project_revision": saved_rev,
            "stale": saved_rev is not None
            and journal["base_project_revision"] != saved_rev,
            "draft_valid": draft.get("candidate_error") is None,
            "candidate_error": draft.get("candidate_error"),
            "active_semantic_id": active_id,
            "candidate_semantic_id": candidate_id,
            "candidate_differs": bool(candidate_id and candidate_id != active_id),
            "source_parse_status": ss["source_document"].get("parse_status"),
            "undo_depth": len(draft.get("undo_history", [])),
            "scenario_document_count": len(journal["scenario_documents"]),
            "selected_scenario_document_id":
                journal["selected_scenario_document_id"],
            "dirty_reasons": journal["dirty_reasons"],
        }

    def recover(self, project_id):
        """Load a recovery journal as the live, UNSAVED, dirty in-memory workspace.
        NEVER auto-applied: the saved project on disk is untouched, its revision is
        NOT advanced, and the candidate is NOT activated -- the recovered draft (a
        valid OR invalid candidate) simply becomes the open session and the user
        must still explicitly Save. A stale journal is refused (WRL_RECOVERY_STALE);
        use `open_as_recovered_copy` for that. Returns
        `(session, journal)` so the caller can rehydrate the scenario author."""
        journal = self._recovery.load(project_id)
        saved_rev = _revision_of(self._store.load(project_id))
        if journal["base_project_revision"] != saved_rev:
            WC._fail(WRL_RECOVERY_STALE,
                     "recovery journal for %r has base revision %d but the saved "
                     "project is at revision %d (open as a recovered copy instead)"
                     % (project_id, journal["base_project_revision"], saved_rev))
        session = CG.restore_session(journal["session_state"])
        self._sessions[project_id] = session          # the live dirty workspace
        self._revisions[project_id] = saved_rev        # revision is NOT advanced
        self._recovery_revs[project_id] = journal["recovery_revision"]
        return session, journal

    def discard_recovery(self, project_id):
        """Drop a project's recovery journal (the explicit Discard action). The
        saved project + any open session are untouched. Idempotent."""
        self._clear_recovery(project_id)

    def open_as_recovered_copy(self, project_id, new_project_id, name=None):
        """Materialize a STALE (or any) recovery journal into a BRAND-NEW saved
        project (never an auto-merge into the diverged saved project). The recovered
        workspace becomes a fresh V2 project under `new_project_id`; the original
        project + its (now-consumed) journal are cleared. Returns the new session."""
        journal = self._recovery.load(project_id)
        session = CG.restore_session(journal["session_state"])
        scen = journal["scenario_documents"]
        doc = session_to_project_v2(session, new_project_id, name or new_project_id,
                                    scenarios=scen)
        self._store.create(doc)
        self._clear_recovery(project_id)
        return self.open(new_project_id)


# ------------------------------------------------------- LastSessionPointerV1 (v0.6-2)
def _reqs(cond, msg, field=None):
    if not cond:
        WC._fail(WRL_BAD_SESSION_POINTER, msg, field_path=field)


def validate_last_session(ptr):
    """Structural gate for a LastSessionPointerV1 (typed WRL_BAD_SESSION_POINTER):
    exactly {last_session_version, last_project_id, updated_at}; the id is a valid
    project id; updated_at is a (non-bool) wall clock. It carries NO project state."""
    _reqs(isinstance(ptr, dict), "session pointer must be an object")
    _reqs(ptr.get("last_session_version") == LAST_SESSION_VERSION,
          "unknown last_session_version %r (only %s)"
          % (ptr.get("last_session_version"), LAST_SESSION_VERSION))
    missing = [k for k in _LAST_SESSION_TOP if k not in ptr]
    _reqs(not missing, "session pointer missing field(s) %s" % missing)
    extra = [k for k in ptr if k not in _LAST_SESSION_TOP]
    _reqs(not extra, "session pointer has unknown field(s) %s" % sorted(extra))
    _reqs(isinstance(ptr["last_project_id"], str)
          and bool(_PROJECT_ID_RE.match(ptr["last_project_id"])),
          "last_project_id must match %s (got %r)"
          % (_PROJECT_ID_RE.pattern, ptr.get("last_project_id")), "last_project_id")
    _reqs(isinstance(ptr["updated_at"], (int, float))
          and not isinstance(ptr["updated_at"], bool),
          "updated_at must be a wall clock number", "updated_at")
    return ptr


def canonicalize_last_session(ptr):
    """Validate then return the canonical pointer form (fixed key order)."""
    validate_last_session(ptr)
    return {
        "last_session_version": LAST_SESSION_VERSION,
        "last_project_id": ptr["last_project_id"],
        "updated_at": ptr["updated_at"],
    }


def serialize_last_session(ptr):
    """Deterministic canonical bytes of a session pointer (NOT content-addressed --
    it carries a wall clock -- so its bytes are not a stable identity)."""
    return WC.serialize_artifact(canonicalize_last_session(ptr))


class LastSessionStore:
    """A single dotted `.last_session.json` pointer in the project root recording
    the LAST opened project id. Non-authoritative startup UX: `set` overwrites it
    atomically, `get` returns the canonical pointer (or None if absent -- never
    raises on absence), `clear` is idempotent. The leading dot keeps it out of
    `ForgeProjectStore.list_projects`."""

    _NAME = ".last_session.json"

    def __init__(self, root):
        self._root = root
        os.makedirs(root, exist_ok=True)

    def _path(self):
        return os.path.join(self._root, self._NAME)

    def set(self, project_id, now=None):
        """Record `project_id` as the last opened project (atomic overwrite).
        Refuses an id that is not a valid project id."""
        ptr = canonicalize_last_session({
            "last_session_version": LAST_SESSION_VERSION,
            "last_project_id": project_id,
            "updated_at": time.time() if now is None else now,
        })
        ST._atomic_write(self._path(), serialize_last_session(ptr))
        return ptr

    def get(self):
        """The canonical pointer, or None when no pointer has been written."""
        path = self._path()
        if not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return canonicalize_last_session(WC.deserialize_artifact(f.read()))

    def clear(self):
        """Drop the pointer (idempotent -- absent is a no-op)."""
        try:
            os.remove(self._path())
        except OSError:
            pass


def resolve_last_session(session_store, project_store):
    """Resolve the last-session pointer against the live project store, SELF-HEALING
    a dangling pointer. Returns the last_project_id ONLY if that project still
    exists; if the pointer names a trashed/removed project it is cleared and None is
    returned, so startup never tries to reopen a project that is gone."""
    ptr = session_store.get()
    if ptr is None:
        return None
    pid = ptr["last_project_id"]
    if project_store.exists(pid):
        return pid
    session_store.clear()
    return None
