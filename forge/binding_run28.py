"""binding_run28.py -- v0.5-5 project import/export + closure: a portable,
self-contained ForgeBundleV1 (Forge World Library, phase 5).

v0.5-1..4 built the substrate (immutable content-addressed object stores, the
mutable ForgeProjectV1 document store, a session cache, the browser Library
panel). v0.5-5 makes a project PORTABLE: `wrl_bundle.build_bundle` packs a project
document TOGETHER WITH every immutable object it references, and `import_bundle`
unpacks it into a FRESH store family, verifying closure (every reference resolves)
and identity (the imported world_source re-lowers to active_world_semantic_id).

Design choices (defensible minimums, consistent with prior GPT-5.6 rulings):
  * a bundle is SELF-SUFFICIENT -- the REQUIRED objects (active world + each
    scenario runtime) are derived straight from the document, so an export is
    complete even if the source stores were never populated; an optional source
    WorldObjectStore lets a bundle ALSO carry historical commit-log worlds
    best-effort (they have no reopenable source);
  * CLOSURE's required set is {active_world} + {scenario digests}; historical
    commit worlds are NOT required (world_source only reproduces the active world);
  * the bundle carries its own CONTENT id (bundle-<64hex>) -- just the hash of an
    export artifact, NOT a new runtime/semantic construct; import CREATES the
    project at revision 0 and never clobbers (WRL_PROJECT_EXISTS);
  * only LIVE projects export -- trashed tombstones live under `.trash/` and are
    invisible to the store, so they are excluded by construction.

Battery R1-R8:

  R1  build_bundle packs a self-contained bundle (active world + every scenario
      object present; validates; bundle_id is deterministic/content-addressed);
  R2  export -> import into a FRESH store family reproduces the project (identical
      canonical bytes) and the reopened session re-lowers to the active world;
  R3  CLOSURE -- verify_bundle_closure passes after import; empty target stores
      make it WRL_BUNDLE_UNRESOLVED;
  R4  a tampered bundled object is WRL_BUNDLE_CORRUPT, non-base64 is
      WRL_BAD_BUNDLE, and an unknown bundle_version is WRL_BAD_BUNDLE;
  R5  IDENTITY -- a project whose world_source no longer lowers to its active id
      is WRL_BUNDLE_IDENTITY at build time;
  R6  import refuses to clobber (WRL_PROJECT_EXISTS); a project_id/name override
      lands under a new id; content-addressed object writes are idempotent (no
      duplicate world/scenario files);
  R7  an EDITED + committed project exports/imports and reopens to the EDITED
      world; the bundle closes WITHOUT history; a source WorldObjectStore lets it
      ALSO carry the historical commit world;
  R8  NATIVE -- a world routed THROUGH export -> import folds ic_ref == ic32 ==
      the independent Fixture oracle over its demo scenario.

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import copy
import os
import sys
import shutil
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import wrl_ir as W
import wrl_plan as P
import compiler as C
import admit as AD
import binding_run3o as O
import wrl_canonical as WC
import wrl_scenario as SC
import wrl_sugar as SG
import wrl_draft as D
import wrl_project as PR
import wrl_store as ST
import wrl_bundle as B
import spinner_bench as SB
from admit import film_hash_v7
from fixture import init_state_v6, state_to_film_args_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

# a valid EDITED world (drop the once-at-1 pulser + door) -- a real world change
EDITED_SRC = """profile forge.world.core.v1

[pulser:p0](every 2){sig_out}
[relay:r0]{sig_in, sig_out}
[spinner:sp](w=16, n=8, rotor=quarter_turn_z, configurable){sig_in, socket}
[orb:ob]{pose}

[pulser:p0] --sig--> [relay:r0]
[relay:r0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]
"""

_SEQ = [0]


def _lower(src):
    return W.lower_program(SG.desugar_core(src), W.parse_wrl_core)


def _apply_text(sess, src):
    _SEQ[0] += 1
    req = {"replace_version": D.REPLACE_VERSION,
           "replace_id": "e-%d-%d" % (int(time.time()), _SEQ[0]),
           "draft_id": sess.draft.draft_id,
           "base_revision": sess.draft.semantic_revision,
           "source": src}
    return sess.apply_text(req)


def _commit(sess):
    commit = {"commit_version": D.COMMIT_VERSION,
              "draft_id": sess.draft.draft_id,
              "base_revision": sess.draft.semantic_revision,
              "expected_candidate_semantic_id": sess.draft.candidate_semantic_id}
    return sess.commit(commit)


def _raises(fn, code):
    try:
        fn()
    except WC.WrlUnsupported as ex:
        return getattr(ex, "code", None) == code
    except Exception:
        return False
    return False


def _fold_films(view, reducer, initial_faults, script):
    world = init_state_v6(view)
    for o in initial_faults:
        if ("fault_" + o) in world:
            world["fault_" + o] = 1
    claim = AD.init_claimstate()
    step, _ = C.compile_step_v6(view)
    films = []
    for e, (label, batch) in enumerate(script):
        ep = 1 + e
        claim, cfg_map, resets = AD.admit_step(claim, batch, ep, view)
        ec = C.enc_config_bundle(view, cfg_map, resets)
        world = C.dec_state_v6(view, reducer(
            f"(({step} {ec}) {C.enc_state_v6(view, world)})"))
        films.append(film_hash_v7(*state_to_film_args_v6(view, world, ep),
                                  state=claim))
    return films


def _fold_fixture(fx, view, reducer, initial_faults, script):
    world = init_state_v6(fx)
    for o in initial_faults:
        if ("fault_" + o) in world:
            world["fault_" + o] = 1
    claim = AD.init_claimstate()
    step, _ = C.compile_step_v6(view)
    films = []
    for e, (label, batch) in enumerate(script):
        ep = 1 + e
        claim, cfg_map, resets = AD.admit_step(claim, batch, ep, fx)
        ec = C.enc_config_bundle(view, cfg_map, resets)
        world = C.dec_state_v6(view, reducer(
            f"(({step} {ec}) {C.enc_state_v6(view, world)})"))
        films.append(film_hash_v7(*state_to_film_args_v6(fx, world, ep),
                                  state=claim))
    return films


def _cache(root):
    return PR.ProjectSessionCache(
        PR.ForgeProjectStore(os.path.join(root, "projects")),
        SB.DEMO_WORLD_SOURCE, scenarios_for=SB._default_scenarios)


def _stores(root, tag):
    """A fresh (project, world, scenario) store family under root/tag."""
    return (PR.ForgeProjectStore(os.path.join(root, tag, "projects")),
            ST.WorldObjectStore(os.path.join(root, tag, "worlds")),
            ST.ScenarioRuntimeStore(os.path.join(root, tag, "scen")))


def main():
    print("[BINDING wrl-v0.5-5] project import/export + closure (R1-R8)")
    allok = True
    native_ok = True
    t0 = time.time()

    def rep(ok, okn, label):
        nonlocal allok, native_ok
        allok &= bool(ok)
        tag = "PASS" if ok else "FAIL"
        if okn is False:
            native_ok = False
            tag = "FAIL(native)"
        print(f"  [{tag}] {label}")

    root = tempfile.mkdtemp(prefix="wrl_bundle_")
    try:
        demo_sem = SB.DEMO_WORLD_SEMANTIC_ID
        edited_sem = _lower(EDITED_SRC).semantic_artifact_id
        store = PR.ForgeProjectStore(os.path.join(root, "projects"))
        cache = _cache(root)
        cache.open("main")                               # the default demo project
        doc = store.load("main")

        # ---- R1 build_bundle packs a self-contained bundle ------------------
        bundle = B.build_bundle(doc)
        scen_digests = set(s["scenario_digest"] for s in doc["scenarios"])
        r1 = (bundle["bundle_version"] == B.BUNDLE_VERSION
              and doc["active_world_semantic_id"] in bundle["worlds"]
              and scen_digests <= set(bundle["scenarios"])
              and len(bundle["scenarios"]) == len(scen_digests)
              and B.validate_bundle_v1(bundle) is bundle
              and B.bundle_id(bundle).startswith("bundle-")
              and B.bundle_id(bundle) == B.bundle_id(B.build_bundle(doc)))
        rep(r1, None,
            "R1) build_bundle packs a self-contained bundle (active world + "
            "every scenario object present; validates; bundle_id deterministic)")

        # ---- R2 export -> import into a FRESH store family reproduces it -----
        tp2, tw2, ts2 = _stores(root, "tgt2")
        created = B.import_bundle(bundle, tp2, tw2, ts2)
        sess2 = PR.open_session_from_project(created)
        r2 = (PR.serialize_project(created) == PR.serialize_project(doc)
              and tp2.load("main")["active_world_semantic_id"] == demo_sem
              and sess2.draft.active_semantic_id == demo_sem)
        rep(r2, None,
            "R2) export -> import into a FRESH store family reproduces the "
            "project (identical canonical bytes) and reopens to the active world")

        # ---- R3 CLOSURE -----------------------------------------------------
        ep_w = ST.WorldObjectStore(os.path.join(root, "empty", "worlds"))
        ep_s = ST.ScenarioRuntimeStore(os.path.join(root, "empty", "scen"))
        r3 = (B.verify_bundle_closure(created, tw2, ts2) == demo_sem
              and _raises(lambda: B.verify_bundle_closure(created, ep_w, ep_s),
                          B.WRL_BUNDLE_UNRESOLVED))
        rep(r3, None,
            "R3) CLOSURE -- verify_bundle_closure passes after import; empty "
            "target stores make it WRL_BUNDLE_UNRESOLVED")

        # ---- R4 tampered / malformed bundles --------------------------------
        sid = doc["active_world_semantic_id"]
        bad_corrupt = copy.deepcopy(bundle)
        bad_corrupt["worlds"][sid] = B._b64(b"not the sealed world bytes")
        bad_b64 = copy.deepcopy(bundle)
        bad_b64["worlds"][sid] = "!!! not base64 !!!"
        bad_ver = copy.deepcopy(bundle)
        bad_ver["bundle_version"] = "forge.bundle.v2"
        r4 = (_raises(lambda: B.validate_bundle_v1(bad_corrupt),
                      B.WRL_BUNDLE_CORRUPT)
              and _raises(lambda: B.validate_bundle_v1(bad_b64), B.WRL_BAD_BUNDLE)
              and _raises(lambda: B.validate_bundle_v1(bad_ver), B.WRL_BAD_BUNDLE))
        rep(r4, None,
            "R4) a tampered bundled object is WRL_BUNDLE_CORRUPT, non-base64 is "
            "WRL_BAD_BUNDLE, an unknown bundle_version is WRL_BAD_BUNDLE")

        # ---- R5 IDENTITY at build time --------------------------------------
        forged = copy.deepcopy(doc)
        forged["world_source"] = EDITED_SRC        # lowers to edited_sem, not demo
        r5 = _raises(lambda: B.build_bundle(forged), B.WRL_BUNDLE_IDENTITY)
        rep(r5, None,
            "R5) IDENTITY -- a project whose world_source no longer lowers to "
            "its active id is WRL_BUNDLE_IDENTITY at build time")

        # ---- R6 import: no clobber, override id, idempotent objects ----------
        world_ids_before = set(tw2.ids())
        scen_ids_before = set(ts2.ids())
        clobber = _raises(
            lambda: B.import_bundle(bundle, tp2, tw2, ts2), PR.WRL_PROJECT_EXISTS)
        copied = B.import_bundle(bundle, tp2, tw2, ts2,
                                 project_id="copy", name="Imported Copy")
        r6 = (clobber
              and copied["project_id"] == "copy"
              and copied["name"] == "Imported Copy"
              and copied["revision"] == 0
              and copied["active_world_semantic_id"] == demo_sem
              and set(tw2.ids()) == world_ids_before       # no duplicate objects
              and set(ts2.ids()) == scen_ids_before
              and tp2.load("copy")["active_world_semantic_id"] == demo_sem)
        rep(r6, None,
            "R6) import refuses to clobber (WRL_PROJECT_EXISTS); a "
            "project_id/name override lands under a new id; content-addressed "
            "object writes are idempotent (no duplicate world/scenario files)")

        # ---- R7 EDITED + committed round-trip + history ---------------------
        cache.create_new("ed", "Edited")
        s_ed = cache.open("ed")
        _apply_text(s_ed, EDITED_SRC)
        _commit(s_ed)
        cache.persist("ed")
        ed_doc = store.load("ed")

        tp7, tw7, ts7 = _stores(root, "tgt7")
        b_ed = B.build_bundle(ed_doc)                     # NO source world store
        created_ed = B.import_bundle(b_ed, tp7, tw7, ts7)
        sess_ed = PR.open_session_from_project(created_ed)

        # a source world store carrying the previous (demo) world -> history
        src_world = ST.WorldObjectStore(os.path.join(root, "srcworlds"))
        src_scen = ST.ScenarioRuntimeStore(os.path.join(root, "srcscen"))
        PR.sync_project_objects(doc, src_world, src_scen)  # puts the demo world
        b_ed_hist = B.build_bundle(ed_doc, world_store=src_world)
        prev_actives = set(c["previous_active"] for c in ed_doc["commits"]
                           if c["previous_active"])
        r7 = (ed_doc["active_world_semantic_id"] == edited_sem
              and len(ed_doc["commits"]) >= 1
              and sess_ed.draft.active_semantic_id == edited_sem     # reopened EDITED
              and B.verify_bundle_closure(created_ed, tw7, ts7) == edited_sem
              and edited_sem in b_ed["worlds"]
              and prev_actives <= set(b_ed_hist["worlds"])           # history carried
              and demo_sem in b_ed_hist["worlds"])
        rep(r7, None,
            "R7) an EDITED + committed project exports/imports and reopens to "
            "the EDITED world; closes WITHOUT history; a source WorldObjectStore "
            "lets it ALSO carry the historical commit world")

        # ---- R8 NATIVE: a world routed THROUGH export -> import folds --------
        sealed8 = tw2.get(demo_sem)                       # the IMPORTED world object
        view8 = P.plan_view(P.artifact_to_compile_plan_v1(sealed8))
        fx8 = _lower(SB.DEMO_WORLD_SOURCE).as_fixture_for_test()
        scen8 = SC.demo_scenario(demo_sem)
        ifa8, scr8 = SC.scenario_to_script(scen8)
        ref8 = _fold_films(view8, O.norm, ifa8, scr8)
        orc8 = _fold_fixture(fx8, view8, O.norm, ifa8, scr8)
        n8r = (sealed8.semantic_id == demo_sem and ref8 == orc8)
        n8n = None
        if not SKIP_NATIVE:
            n8n = (_fold_films(view8, O.native, ifa8, scr8) == ref8)
        rep(n8r, n8n,
            "R8) NATIVE -- a world routed THROUGH export -> import folds "
            "ic_ref == ic32 == the independent Fixture oracle")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.5-5] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.5-5 makes a project PORTABLE: a self-contained "
          "ForgeBundleV1 packs the project document TOGETHER WITH every "
          "immutable object it references. The bundle is SELF-SUFFICIENT (the "
          "active world + scenario runtimes are derived from the document, R1); "
          "export -> import into a FRESH store family reproduces the project "
          "byte-for-byte and reopens to the active world (R2); CLOSURE is "
          "verified (every required reference resolves, R3) with typed "
          "WRL_BUNDLE_CORRUPT/WRL_BAD_BUNDLE/WRL_BUNDLE_IDENTITY guards "
          "(R4/R5); import never clobbers and object writes are idempotent "
          "(R6); an edited+committed world round-trips and history is carried "
          "best-effort (R7). NO new identity that governs a run, NO new runtime "
          "construct; a bundled world stays natively runnable (R8).")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
