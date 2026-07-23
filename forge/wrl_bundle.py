"""wrl_bundle.py v0.5-5 -- ForgeBundleV1: self-contained project import/export
with closure + identity verification (Forge World Library, phase 5).

v0.5-1..4 built the substrate: content-addressed immutable object stores
(wrl_store.py), the mutable named ForgeProjectV1 document store, a session cache,
and the browser Library panel. v0.5-5 makes a project PORTABLE: a `ForgeBundleV1`
packs one project document TOGETHER WITH every immutable object it references, so
it can be handed to a fresh store on another machine and reopened with no dangling
reference.

    ForgeBundleV1 = {
      bundle_version,                    # "forge.bundle.v1"
      project,                           # a canonical ForgeProjectV1 document
      worlds   {sem-<64hex>:  <b64 SealedArtifact canonical bytes>},
      scenarios{scen-<64hex>: <b64 ScenarioDigest-domain bytes>},
    }

A bundle carries its own CONTENT identity, ForgeBundleID = `bundle-` + sha256 over
its canonical bytes -- purely the hash of an export artifact, NOT a new runtime or
semantic construct (the world's SemanticArtifactID and each ScenarioDigest are
unchanged and still the ONLY identities that matter). Two byte-identical exports
collapse to the same id.

Three laws hold end to end:

  * SELF-SUFFICIENCY -- export derives the REQUIRED immutable objects straight
    from the project document (the active world by re-lowering `world_source`,
    each scenario runtime from its ScenarioV1 doc), so a bundle is complete even
    if the source stores were never populated. An optional source WorldObjectStore
    lets export ALSO carry historical commit-log worlds best-effort (those have no
    reopenable source, so they can only be copied when already present).

  * CLOSURE -- the REQUIRED reference set is {active_world_semantic_id} together
    with every scenario's ScenarioDigest. `verify_bundle_closure` refuses a bundle
    (WRL_BUNDLE_UNRESOLVED) unless every one of those resolves in the target
    stores. Historical commit worlds are NOT required for closure -- `world_source`
    only reproduces the ACTIVE world -- so a bundle without them still imports.

  * IDENTITY -- import re-lowers the imported `world_source` and asserts it
    reproduces `active_world_semantic_id` (WRL_BUNDLE_IDENTITY); every bundled
    object is content-addressed, so `_put_bytes` re-hashes it against its claimed
    key on the way in (a tampered object is WRL_STORE_ID_MISMATCH), and the bundle
    itself is checked key-vs-bytes before any store write (WRL_BUNDLE_CORRUPT).

Import writes the objects first (idempotent, content-addressed), verifies closure
+ identity, then CREATES the project at revision 0 (a fresh copy, never clobbering
-- WRL_PROJECT_EXISTS). A project_id / name override lets a bundle land under a new
name. NO new identity that governs a run, NO new runtime construct.

Only LIVE projects export: `export_project` loads through the ForgeProjectStore,
which never sees `.trash/` tombstones, so a trashed project is excluded by
construction (soft-deletion stays a local, reversible concern).
"""
import base64
import copy

import wrl_canonical as WC
import wrl_scenario as SC
import wrl_sugar as SG
import wrl_ir as W
import wrl_project as PR
import wrl_store as ST
import wrl_draft as D
import wrl_format as F

BUNDLE_VERSION = "forge.bundle.v1"
BUNDLE_V2_VERSION = "forge.bundle.v2"     # v0.5.1 workspace-carrying bundle
EXPORT_MODES = ("full", "thin")

WRL_BAD_BUNDLE = "WRL_BAD_BUNDLE"                # malformed bundle document
WRL_BUNDLE_CORRUPT = "WRL_BUNDLE_CORRUPT"        # bundled object != its claimed key
WRL_BUNDLE_UNRESOLVED = "WRL_BUNDLE_UNRESOLVED"  # a required reference is absent
WRL_BUNDLE_IDENTITY = "WRL_BUNDLE_IDENTITY"      # world_source != active id

_TOP = ("bundle_version", "project", "worlds", "scenarios")
_TOP_V2 = ("bundle_version", "export_mode", "shallow_history",
           "project", "worlds", "scenarios")


# ------------------------------------------------------------------ helpers
def _b64(blob):
    return base64.b64encode(blob).decode("ascii")


def _unb64(text):
    try:
        return base64.b64decode(text.encode("ascii"), validate=True)
    except Exception:
        WC._fail(WRL_BAD_BUNDLE, "object payload is not valid base64")


def _relower(world_source, active_id, code):
    """Re-lower a project's world_source and assert it reproduces active_id."""
    prog = W.lower_program(SG.desugar_core(world_source), W.parse_wrl_core)
    if prog.semantic_artifact_id != active_id:
        WC._fail(code, "world_source lowers to %r but active id is %r"
                 % (prog.semantic_artifact_id, active_id))
    return prog


def _world_from_graph(objects, edges, profile, expected_id):
    """Re-seal a world DIRECTLY from a draft's plain object/edge lists (a valid
    working graph or a valid undo snapshot) and assert it reproduces
    `expected_id`. Returns the SealedArtifact canonical bytes. This is the V2
    self-sufficiency seam: a candidate / historical draft world has no reopenable
    `world_source`, but its graph IS embedded in the project document, so the
    bundle can carry the world without any source world store."""
    prog = W.lower_graph(D._graph_from(objects, edges, profile))
    if prog.semantic_artifact_id != expected_id:
        WC._fail(WRL_BUNDLE_IDENTITY,
                 "draft graph lowers to %r but recorded id is %r"
                 % (prog.semantic_artifact_id, expected_id))
    return prog.sealed_artifact.canonical_bytes


# ------------------------------------------------------------- validation
def validate_bundle_v1(bundle):
    """Structural gate for a ForgeBundleV1. Also checks every bundled object's
    key AGAINST its bytes (WRL_BUNDLE_CORRUPT) and that the project references
    are shaped like store keys. Raises WrlValidationError; returns the bundle."""
    if not isinstance(bundle, dict):
        WC._fail(WRL_BAD_BUNDLE, "bundle must be an object")
    if bundle.get("bundle_version") != BUNDLE_VERSION:
        WC._fail(WRL_BAD_BUNDLE, "unknown bundle_version %r (only %s)"
                 % (bundle.get("bundle_version"), BUNDLE_VERSION))
    missing = [k for k in _TOP if k not in bundle]
    if missing:
        WC._fail(WRL_BAD_BUNDLE, "bundle missing field(s) %s" % missing)
    extra = [k for k in bundle if k not in _TOP]
    if extra:
        WC._fail(WRL_BAD_BUNDLE, "bundle has unknown field(s) %s" % sorted(extra))

    PR.validate_project_v1(bundle["project"])

    for label, keyre, prefix in (("worlds", WC._SEM_ID_RE, "sem-"),
                                 ("scenarios", ST._SCEN_ID_RE, "scen-")):
        section = bundle[label]
        if not isinstance(section, dict):
            WC._fail(WRL_BAD_BUNDLE, "%s must be an object" % label, field_path=label)
        for key, payload in section.items():
            if not (isinstance(key, str) and keyre.match(key)):
                WC._fail(WRL_BAD_BUNDLE, "%s key %r is not a %s id"
                         % (label, key, prefix), field_path=label)
            if not isinstance(payload, str):
                WC._fail(WRL_BAD_BUNDLE, "%s[%s] payload must be a string"
                         % (label, key), field_path=label)
            blob = _unb64(payload)
            computed = prefix + WC._sha(blob)
            if computed != key:
                WC._fail(WRL_BUNDLE_CORRUPT,
                         "%s object %r hashes to %r" % (label, key, computed),
                         field_path=label)
    return bundle


def canonicalize_bundle_v1(bundle):
    """Validate then return the canonical bundle form (project canonicalized;
    object maps are order-independent under sort_keys serialization)."""
    validate_bundle_v1(bundle)
    return {
        "bundle_version": BUNDLE_VERSION,
        "project": PR.canonicalize_project_v1(bundle["project"]),
        "worlds": dict(bundle["worlds"]),
        "scenarios": dict(bundle["scenarios"]),
    }


def _check_object_maps(bundle):
    """Shared V1/V2 object-map corruption check: every bundled world / scenario
    key must hash from its own bytes (WRL_BUNDLE_CORRUPT), and keys must be shaped
    like store ids."""
    for label, keyre, prefix in (("worlds", WC._SEM_ID_RE, "sem-"),
                                 ("scenarios", ST._SCEN_ID_RE, "scen-")):
        section = bundle[label]
        if not isinstance(section, dict):
            WC._fail(WRL_BAD_BUNDLE, "%s must be an object" % label,
                     field_path=label)
        for key, payload in section.items():
            if not (isinstance(key, str) and keyre.match(key)):
                WC._fail(WRL_BAD_BUNDLE, "%s key %r is not a %s id"
                         % (label, key, prefix), field_path=label)
            if not isinstance(payload, str):
                WC._fail(WRL_BAD_BUNDLE, "%s[%s] payload must be a string"
                         % (label, key), field_path=label)
            blob = _unb64(payload)
            computed = prefix + WC._sha(blob)
            if computed != key:
                WC._fail(WRL_BUNDLE_CORRUPT,
                         "%s object %r hashes to %r" % (label, key, computed),
                         field_path=label)


def validate_bundle_v2(bundle):
    """Structural gate for a ForgeBundleV2 (the v0.5.1 workspace-carrying bundle).
    Like V1 but the embedded document is a ForgeProjectV2 (a complete authoring
    workspace) and the bundle declares its `export_mode` + `shallow_history`.
    Raises WrlValidationError; returns the bundle."""
    if not isinstance(bundle, dict):
        WC._fail(WRL_BAD_BUNDLE, "bundle must be an object")
    if bundle.get("bundle_version") != BUNDLE_V2_VERSION:
        WC._fail(WRL_BAD_BUNDLE, "unknown bundle_version %r (only %s)"
                 % (bundle.get("bundle_version"), BUNDLE_V2_VERSION))
    missing = [k for k in _TOP_V2 if k not in bundle]
    if missing:
        WC._fail(WRL_BAD_BUNDLE, "bundle missing field(s) %s" % missing)
    extra = [k for k in bundle if k not in _TOP_V2]
    if extra:
        WC._fail(WRL_BAD_BUNDLE, "bundle has unknown field(s) %s" % sorted(extra))

    mode = bundle["export_mode"]
    if mode not in EXPORT_MODES:
        WC._fail(WRL_BAD_BUNDLE, "unknown export_mode %r (only %s)"
                 % (mode, EXPORT_MODES))
    if not isinstance(bundle["shallow_history"], bool):
        WC._fail(WRL_BAD_BUNDLE, "shallow_history must be a boolean")
    # a full bundle closes over history (shallow_history=false); a thin bundle
    # explicitly declares its history is stripped (shallow_history=true).
    if mode == "full" and bundle["shallow_history"] is not False:
        WC._fail(WRL_BAD_BUNDLE, "full export must set shallow_history=false")
    if mode == "thin" and bundle["shallow_history"] is not True:
        WC._fail(WRL_BAD_BUNDLE, "thin export must set shallow_history=true")

    PR.validate_project_v2(bundle["project"])
    _check_object_maps(bundle)
    return bundle


def canonicalize_bundle_v2(bundle):
    """Validate then return the canonical V2 bundle form (project canonicalized
    as a ForgeProjectV2; object maps are order-independent under sort_keys)."""
    validate_bundle_v2(bundle)
    return {
        "bundle_version": BUNDLE_V2_VERSION,
        "export_mode": bundle["export_mode"],
        "shallow_history": bundle["shallow_history"],
        "project": PR.canonicalize_project_v2(bundle["project"]),
        "worlds": dict(bundle["worlds"]),
        "scenarios": dict(bundle["scenarios"]),
    }


def _bundle_version_of(bundle):
    if not isinstance(bundle, dict):
        WC._fail(WRL_BAD_BUNDLE, "bundle must be an object")
    v = bundle.get("bundle_version")
    if v not in (BUNDLE_VERSION, BUNDLE_V2_VERSION):
        WC._fail(WRL_BAD_BUNDLE, "unknown bundle_version %r (only %s / %s)"
                 % (v, BUNDLE_VERSION, BUNDLE_V2_VERSION))
    return v


def serialize_bundle(bundle):
    """Deterministic canonical bytes of a bundle (V1 or V2)."""
    if _bundle_version_of(bundle) == BUNDLE_V2_VERSION:
        return WC.serialize_artifact(canonicalize_bundle_v2(bundle))
    return WC.serialize_artifact(canonicalize_bundle_v1(bundle))


def bundle_id(bundle):
    """ForgeBundleID = `bundle-` + sha256 over the bundle's canonical bytes."""
    return "bundle-" + WC._sha(serialize_bundle(bundle))


# ------------------------------------------------------------------- export
def _bundle_scenarios(scenario_entries):
    """The `scenarios` object map (scen-<hash> -> b64 digest-domain bytes) for a
    project's scenario list. Shared by the V1 and V2 exporters."""
    scenarios = {}
    for s in scenario_entries:
        canon = SC.canonicalize_scenario_v1(s["scenario"])
        blob = WC.serialize_artifact(SC._digest_domain(canon))
        scenarios["scen-" + WC._sha(blob)] = _b64(blob)
    return scenarios


def build_bundle_v1(doc, world_store=None):
    """Pack a ForgeProjectV1 document into a self-contained ForgeBundleV1.

    The REQUIRED objects are derived directly from the document (self-sufficient):
    the active world by re-lowering `world_source` (identity-checked), and each
    scenario's runtime domain from its ScenarioV1 doc. If `world_store` is given,
    historical commit-log worlds it can resolve are ALSO carried (best-effort --
    they have no reopenable source)."""
    doc = PR.canonicalize_project_v1(doc)
    prog = _relower(doc["world_source"], doc["active_world_semantic_id"],
                    WRL_BUNDLE_IDENTITY)

    worlds = {doc["active_world_semantic_id"]:
              _b64(prog.sealed_artifact.canonical_bytes)}
    if world_store is not None:
        for c in doc["commits"]:
            for k in ("previous_active", "active_semantic_id"):
                sid = c.get(k)
                if sid and sid not in worlds and world_store.has(sid):
                    worlds[sid] = _b64(world_store._get_bytes(sid))

    return canonicalize_bundle_v1({
        "bundle_version": BUNDLE_VERSION,
        "project": doc,
        "worlds": worlds,
        "scenarios": _bundle_scenarios(doc["scenarios"]),
    })


def build_bundle_v2(doc, export_mode="full", world_store=None):
    """Pack a ForgeProjectV2 (a COMPLETE authoring workspace) into a
    self-contained ForgeBundleV2. Two frozen export modes (GPT-5.6 v0.5.1):

      * "full" (default) -- closes over EVERY world the workspace references:
        the active world (re-lowered from active_world.canonical_source), the
        candidate world when the draft is valid, every valid undo-history
        snapshot world, and every commit-history world. The candidate + snapshot
        worlds are self-derivable from the graphs embedded in the document (no
        source store needed); the commit-history worlds have no reopenable source,
        so a `world_store` MUST resolve each one or export fails
        WRL_BUNDLE_UNRESOLVED (never a silent downgrade). shallow_history=false.

      * "thin" (explicit) -- carries ONLY the active world + the scenario runtime
        objects + the reopenable project document. History is deliberately not
        closed over, so the bundle declares shallow_history=true. The embedded
        document still carries the complete workspace (invalid draft included), so
        the project reopens identically; only the historical WORLD OBJECTS are
        omitted."""
    if export_mode not in EXPORT_MODES:
        WC._fail(WRL_BAD_BUNDLE, "unknown export_mode %r (only %s)"
                 % (export_mode, EXPORT_MODES))
    doc = PR.canonicalize_project_v2(doc)
    draft = doc["draft"]
    profile = draft["profile_id"]

    active = doc["active_world"]["semantic_id"]
    prog = _relower(doc["active_world"]["canonical_source"], active,
                    WRL_BUNDLE_IDENTITY)
    worlds = {active: _b64(prog.sealed_artifact.canonical_bytes)}

    shallow = (export_mode == "thin")
    if export_mode == "full":
        # the candidate world (only when the draft is valid)
        cand = draft["candidate_semantic_id"]
        if cand and cand not in worlds:
            worlds[cand] = _b64(_world_from_graph(
                draft["objects"], draft["edges"], profile, cand))
        # every valid undo-history snapshot world (self-derivable)
        for snap in draft["undo_history"]:
            sid = snap.get("candidate_semantic_id")
            if sid and sid not in worlds:
                worlds[sid] = _b64(_world_from_graph(
                    snap["objects"], snap["edges"], profile, sid))
        # every commit-history world -- NOT embedded, so it MUST resolve in the
        # source world store or the full export fails (never silently downgrade).
        for c in doc["commit_history"]:
            for k in ("previous_active", "active_semantic_id"):
                sid = c.get(k)
                if sid and sid not in worlds:
                    if world_store is None or not world_store.has(sid):
                        WC._fail(WRL_BUNDLE_UNRESOLVED,
                                 "full export cannot resolve commit-history world "
                                 "%r (no source world store carries it)" % (sid,))
                    worlds[sid] = _b64(world_store._get_bytes(sid))

    return canonicalize_bundle_v2({
        "bundle_version": BUNDLE_V2_VERSION,
        "export_mode": export_mode,
        "shallow_history": shallow,
        "project": doc,
        "worlds": worlds,
        "scenarios": _bundle_scenarios(doc["scenario_documents"]),
    })


def build_bundle(doc, world_store=None, export_mode="full"):
    """Version-dispatched export. A ForgeProjectV1 document builds a V1 bundle
    (byte-identical to before; `export_mode` is ignored -- V1 has no thin mode);
    a ForgeProjectV2 builds a V2 bundle in the requested `export_mode`."""
    if PR.project_version_of(doc) == PR.PROJECT_V2_VERSION:
        return build_bundle_v2(doc, export_mode=export_mode,
                               world_store=world_store)
    return build_bundle_v1(doc, world_store=world_store)


def export_project(project_id, project_store, world_store=None,
                   export_mode="full"):
    """Load a LIVE project by id and build its bundle. Trashed projects are not
    visible to the store, so they are excluded by construction. `world_store` is
    optional for V1 (historical commit worlds are best-effort) but REQUIRED for a
    V2 full export whenever the commit history references worlds with no
    reopenable source. `export_mode` selects full (default) or thin for V2."""
    doc = project_store.load(project_id)
    return build_bundle(doc, world_store=world_store, export_mode=export_mode)


# ------------------------------------------------------------------- closure
def verify_bundle_closure(doc, world_store, scenario_store, require_history=False):
    """Assert every REQUIRED project reference resolves in the given stores:
    the active world (hash-verified read + world_source re-lowers to it) and each
    scenario's ScenarioDigest. Historical commit worlds are checked ONLY when
    `require_history` is set. Returns the active SemanticArtifactID."""
    doc = PR.canonicalize_project_v1(doc)
    active = doc["active_world_semantic_id"]
    if not world_store.has(active):
        WC._fail(WRL_BUNDLE_UNRESOLVED,
                 "active world %r not in store" % (active,))
    world_store.get(active)                       # hash-verified read + re-seal
    _relower(doc["world_source"], active, WRL_BUNDLE_IDENTITY)

    for s in doc["scenarios"]:
        d = s["scenario_digest"]
        if not scenario_store.has(d):
            WC._fail(WRL_BUNDLE_UNRESOLVED,
                     "scenario %r (%s) not in store" % (s["name"], d))
        scenario_store.get(d)                     # hash-verified read

    if require_history:
        for c in doc["commits"]:
            for k in ("previous_active", "active_semantic_id"):
                sid = c.get(k)
                if sid and not world_store.has(sid):
                    WC._fail(WRL_BUNDLE_UNRESOLVED,
                             "historical world %r not in store" % (sid,))
    return active


def verify_bundle_v2_closure(bundle):
    """Assert a ForgeBundleV2 is SELF-CONTAINED for its declared export mode --
    i.e. the object maps carry every world / scenario the bundle promises. A V2
    project document is already reopenable from its own embedded graphs, so
    closure is verified against the bundle's OWN object maps (no external stores):

      * always -- the active world is carried and its canonical_source re-lowers
        to it (WRL_BUNDLE_IDENTITY), and every scenario digest is carried.
      * full  -- ADDITIONALLY the candidate world (when valid), every valid
        undo-history snapshot world, and every commit-history world are carried;
        any missing one is WRL_BUNDLE_UNRESOLVED (this is what makes W17/W18 bite).
      * thin  -- history is NOT required (shallow_history=true was declared).

    Returns the active SemanticArtifactID."""
    bundle = canonicalize_bundle_v2(bundle)
    doc = bundle["project"]
    worlds = bundle["worlds"]
    draft = doc["draft"]

    active = doc["active_world"]["semantic_id"]
    if active not in worlds:
        WC._fail(WRL_BUNDLE_UNRESOLVED, "active world %r not carried" % (active,))
    _relower(doc["active_world"]["canonical_source"], active, WRL_BUNDLE_IDENTITY)

    for s in doc["scenario_documents"]:
        d = s["scenario_digest"]
        if d not in bundle["scenarios"]:
            WC._fail(WRL_BUNDLE_UNRESOLVED,
                     "scenario %r (%s) not carried" % (s["name"], d))

    if bundle["export_mode"] == "full":
        cand = draft["candidate_semantic_id"]
        if cand and cand not in worlds:
            WC._fail(WRL_BUNDLE_UNRESOLVED,
                     "candidate world %r not carried" % (cand,))
        for snap in draft["undo_history"]:
            sid = snap.get("candidate_semantic_id")
            if sid and sid not in worlds:
                WC._fail(WRL_BUNDLE_UNRESOLVED,
                         "undo-history world %r not carried" % (sid,))
        for c in doc["commit_history"]:
            for k in ("previous_active", "active_semantic_id"):
                sid = c.get(k)
                if sid and sid not in worlds:
                    WC._fail(WRL_BUNDLE_UNRESOLVED,
                             "commit-history world %r not carried" % (sid,))
    return active


# ------------------------------------------------------------------- import
def import_bundle_v1(bundle, project_store, world_store, scenario_store,
                     project_id=None, name=None):
    """Unpack a V1 bundle into fresh stores: write every bundled object (idempotent,
    content-addressed, hash-verified on the way in), verify closure + identity,
    then CREATE the project at revision 0 (never clobbers -- WRL_PROJECT_EXISTS).

    `project_id` / `name` override where the project lands, so a bundle can be
    imported under a new id without colliding with the original."""
    bundle = canonicalize_bundle_v1(bundle)

    for sid, payload in bundle["worlds"].items():
        world_store._put_bytes(sid, _unb64(payload))
    for d, payload in bundle["scenarios"].items():
        scenario_store._put_bytes(d, _unb64(payload))

    doc = copy.deepcopy(bundle["project"])
    if project_id is not None:
        doc["project_id"] = project_id
    if name is not None:
        doc["name"] = name
    doc["revision"] = 0
    doc = PR.canonicalize_project_v1(doc)

    verify_bundle_closure(doc, world_store, scenario_store)
    return project_store.create(doc)


def import_bundle_v2(bundle, project_store, world_store, scenario_store,
                     project_id=None, name=None):
    """Unpack a V2 bundle: verify the bundle's self-closure for its export mode,
    write every carried object (idempotent, content-addressed, hash-verified),
    then CREATE the ForgeProjectV2 at project_revision 0 (never clobbers). The
    embedded document carries the COMPLETE workspace, so the project reopens
    identically -- an invalid, editable draft survives export/import (W20)."""
    bundle = canonicalize_bundle_v2(bundle)
    verify_bundle_v2_closure(bundle)

    for sid, payload in bundle["worlds"].items():
        world_store._put_bytes(sid, _unb64(payload))
    for d, payload in bundle["scenarios"].items():
        scenario_store._put_bytes(d, _unb64(payload))

    doc = copy.deepcopy(bundle["project"])
    if project_id is not None:
        doc["project_id"] = project_id
    if name is not None:
        doc["name"] = name
    doc["project_revision"] = 0
    doc = PR.canonicalize_project_v2(doc)
    return project_store.create(doc)


def import_bundle(bundle, project_store, world_store, scenario_store,
                  project_id=None, name=None):
    """Version-dispatched import (V1 or V2 bundle)."""
    if _bundle_version_of(bundle) == BUNDLE_V2_VERSION:
        return import_bundle_v2(bundle, project_store, world_store,
                                scenario_store, project_id=project_id, name=name)
    return import_bundle_v1(bundle, project_store, world_store, scenario_store,
                            project_id=project_id, name=name)
