"""binding_run25.py -- v0.5-2 ForgeProjectV1 project document store
(Forge World Library, phase 2).

v0.5-1 (binding_run24) laid the IMMUTABLE, content-addressed substrate. v0.5-2
layers the MUTABLE, named, per-project document OVER it: a `ForgeProjectV1` is
the durable, reopenable state of one editing project (name, active world sem-id,
reopenable world_source, layout, scenarios, commit log). It is NOT content-
addressed, so `ForgeProjectStore` gives it atomic writes (the same persistence
law as the object stores) + PER-PROJECT EXACT-CAS revision. NO new identity, NO
new runtime construct.

Battery O1-O8:

  O1  create + load round-trip -- a project built from a CanvasSession persists
      and reloads to byte-identical canonical bytes at revision 0;
  O2  EXACT-CAS -- save(doc, expected_revision) bumps the revision by one on a
      matching expectation, and a STALE expected revision is a TYPED
      WRL_PROJECT_STALE (no auto-merge, on-disk untouched);
  O3  durability -- a FRESH store instance over the same root reloads the saved
      revision (no in-memory index);
  O4  create-clobber is a TYPED WRL_PROJECT_EXISTS and load-missing is a TYPED
      WRL_PROJECT_MISSING (never a raw OSError);
  O5  a malformed project document is a TYPED WRL_BAD_PROJECT (bad id, unknown
      field, mismatched scenario digest, and a world_source that lowers to a
      different sem id are each caught);
  O6  closure -- sync_project_objects puts the project's world + scenarios into
      the immutable stores so every reference resolves (idempotent);
  O7  reopen -- open_session_from_project re-lowers world_source, reproduces the
      active sem id (closure) and restores layout + commit log;
  O8  NATIVE -- a world persisted THROUGH a project (create -> load -> reopened
      session -> re-lowered) folds ic_ref == ic32 == the Fixture oracle.

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
import wrl_store as ST
import wrl_project as PR
import wrl_converge as CG
import spinner_bench as SB
from admit import film_hash_v7
from fixture import init_state_v6, state_to_film_args_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"


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


def _raises(fn, code):
    """True iff `fn()` raises a TYPED WrlValidationError with the given code
    (NOT a raw Python exception)."""
    try:
        fn()
        return False
    except WC.WrlValidationError as ex:
        return ex.code == code
    except Exception:
        return False


def main():
    print("[BINDING wrl-v0.5-2] ForgeProjectV1 project document store (O1-O8)")
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

    root = tempfile.mkdtemp(prefix="wrl_project_")
    try:
        prog = SB._prog(SB.DEMO_WORLD_SOURCE)     # desugar -> lower -> sealed
        sem = prog.semantic_artifact_id
        session = CG.new_session(prog, "main")
        scen_entry = PR.make_scenario_entry("demo", SC.demo_scenario(sem))
        doc = PR.session_to_project(session, "spinner-demo", "Spinner Demo",
                                    scenarios=[scen_entry])

        # ---- O1 create + load round-trip ------------------------------------
        store = PR.ForgeProjectStore(os.path.join(root, "projects"))
        created = store.create(doc)
        loaded = store.load("spinner-demo")
        o1 = (created["revision"] == 0
              and created["active_world_semantic_id"] == sem
              and store.exists("spinner-demo")
              and store.list_projects() == ["spinner-demo"]
              and PR.serialize_project(loaded) == PR.serialize_project(created)
              and loaded["revision"] == 0
              and [s["name"] for s in loaded["scenarios"]] == ["demo"])
        rep(o1, None,
            "O1) a project built from a CanvasSession persists and reloads to "
            "byte-identical canonical bytes at revision 0")

        # ---- O2 EXACT-CAS revision ------------------------------------------
        edited = dict(loaded)
        edited["name"] = "Spinner Demo (renamed)"
        saved = store.save(edited, expected_revision=0)
        # a STALE save (expected 0 again, on-disk is now 1) is typed + inert
        stale_ok = _raises(lambda: store.save(dict(saved), expected_revision=0),
                           PR.WRL_PROJECT_STALE)
        after = store.load("spinner-demo")
        o2 = (saved["revision"] == 1 and saved["name"] == "Spinner Demo (renamed)"
              and stale_ok
              and after["revision"] == 1          # on-disk untouched by the stale save
              and after["name"] == "Spinner Demo (renamed)")
        rep(o2, None,
            "O2) save bumps the revision by one on a matching expectation; a STALE "
            "expected revision is a TYPED WRL_PROJECT_STALE (no auto-merge)")

        # ---- O3 durability across a fresh store instance --------------------
        store_reopened = PR.ForgeProjectStore(os.path.join(root, "projects"))
        reloaded = store_reopened.load("spinner-demo")
        o3 = (reloaded["revision"] == 1
              and reloaded["name"] == "Spinner Demo (renamed)"
              and PR.serialize_project(reloaded) == PR.serialize_project(after))
        rep(o3, None,
            "O3) a FRESH store instance over the same root reloads the saved "
            "revision (no in-memory index)")

        # ---- O4 create-clobber / load-missing are typed ---------------------
        o4 = (_raises(lambda: store.create(doc), PR.WRL_PROJECT_EXISTS)
              and _raises(lambda: store.load("no-such-project"),
                          PR.WRL_PROJECT_MISSING)
              and _raises(lambda: store.save(
                  dict(after, project_id="ghost"), expected_revision=0),
                  PR.WRL_PROJECT_MISSING))
        rep(o4, None,
            "O4) create-clobber is a TYPED WRL_PROJECT_EXISTS and load/save of an "
            "absent id is a TYPED WRL_PROJECT_MISSING (never a raw OSError)")

        # ---- O5 malformed project documents are typed -----------------------
        bad_id = dict(loaded); bad_id["project_id"] = "bad id!"
        unknown = dict(loaded); unknown["surprise"] = 1
        bad_digest = copy.deepcopy(loaded)
        bad_digest["scenarios"][0]["scenario_digest"] = "scen-" + ("0" * 64)
        wrong_world = copy.deepcopy(loaded)
        wrong_world["active_world_semantic_id"] = "sem-" + ("0" * 64)
        o5 = (_raises(lambda: PR.validate_project_v1(bad_id), PR.WRL_BAD_PROJECT)
              and _raises(lambda: PR.validate_project_v1(unknown),
                          PR.WRL_BAD_PROJECT)
              and _raises(lambda: PR.validate_project_v1(bad_digest),
                          PR.WRL_BAD_PROJECT)
              # a world_source that lowers to a different sem id fails ON REOPEN
              and _raises(lambda: PR.open_session_from_project(wrong_world),
                          PR.WRL_BAD_PROJECT))
        rep(o5, None,
            "O5) malformed project documents are TYPED WRL_BAD_PROJECT (bad id, "
            "unknown field, mismatched scenario digest, world/id mismatch)")

        # ---- O6 closure into the immutable stores ---------------------------
        ws = ST.WorldObjectStore(os.path.join(root, "worlds"))
        ss = ST.ScenarioRuntimeStore(os.path.join(root, "scenarios"))
        synced = PR.sync_project_objects(loaded, ws, ss)
        scen_digest = loaded["scenarios"][0]["scenario_digest"]
        o6 = (synced == sem and ws.has(sem) and ss.has(scen_digest)
              # idempotent -- a second sync adds no files
              and PR.sync_project_objects(loaded, ws, ss) == sem
              and ws.ids() == [sem] and ss.ids() == [scen_digest])
        rep(o6, None,
            "O6) sync_project_objects puts the project's world + scenarios into "
            "the immutable stores so every reference resolves (idempotent)")

        # ---- O7 reopen reproduces active id + layout + commits --------------
        reopened = PR.open_session_from_project(loaded, "main")
        o7 = (reopened.candidate_semantic_id == sem
              and reopened.candidate_error is None
              and CV_ok(reopened.layout, loaded["layout"])
              and reopened.commits == loaded["commits"]
              and reopened.to_text() == session.to_text())
        rep(o7, None,
            "O7) open_session_from_project re-lowers world_source, reproduces the "
            "active sem id (closure) and restores layout + commit log")

        # ---- O8 NATIVE: a world persisted through a project still folds ------
        reopened8 = PR.open_session_from_project(store.load("spinner-demo"), "main")
        prog8 = W.lower_program(SG.desugar_core(reopened8.to_text()),
                                W.parse_wrl_core)
        view8 = P.plan_view(P.artifact_to_compile_plan_v1(prog8.sealed_artifact))
        fx8 = prog.as_fixture_for_test()          # independent oracle
        scen8 = SC.demo_scenario(sem)
        ifa8, scr8 = SC.scenario_to_script(scen8)
        ref8 = _fold_films(view8, O.norm, ifa8, scr8)
        orc8 = _fold_fixture(fx8, view8, O.norm, ifa8, scr8)
        n8r = (prog8.semantic_artifact_id == sem and ref8 == orc8)
        n8n = None
        if not SKIP_NATIVE:
            n8n = (_fold_films(view8, O.native, ifa8, scr8) == ref8)
        rep(n8r, n8n,
            "O8) NATIVE -- a world persisted THROUGH a project (create -> load -> "
            "reopened session -> re-lowered) folds ic_ref == ic32 == the oracle")
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
    print(f"\n[wrl-v0.5-2] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.5-2 layers the MUTABLE, named, per-project document OVER "
          "the immutable substrate: a ForgeProjectV1 is written atomically (the "
          "same temp -> fsync -> rename law) with PER-PROJECT EXACT-CAS revision "
          "(WRL_PROJECT_STALE, no auto-merge). The project stores its world by "
          "REFERENCE (active sem-id + reopenable world_source); reopening re-"
          "lowers to the SAME sem id (closure) and stays natively runnable "
          "ic_ref == ic32 == oracle (O8). NO new identity, NO new runtime "
          "construct; RemoveObject stays non-cascading, multi-op atomic deletion "
          "DEFERRED.")
    return 0 if allok else 1


def CV_ok(a, b):
    """Layouts equal after canonical validation (presentation-only)."""
    import wrl_canvas as CV
    return CV.validate_layout_v1(copy.deepcopy(a)) \
        == CV.validate_layout_v1(copy.deepcopy(b))


if __name__ == "__main__":
    sys.exit(main())
