"""binding_run27.py -- v0.5-4 Library management: multiple named, persisted
worlds over the ProjectSessionCache (Forge World Library, phase 4).

v0.5-3 (binding_run26) migrated the live session onto ONE durable project.
v0.5-4 makes the Library plural: the store + cache gain `list_project_infos`,
`create_new`, `rename`, `fork` and `trash` so a user can name, switch between,
fork, rename and trash multiple persisted worlds.

Design choices (defensible minimums, consistent with prior GPT-5.6 rulings):
  * project_id is the immutable identity key; `rename` only changes the display
    `name` (exact-CAS on the revision, world/layout/scenarios/commits untouched);
  * `fork` copies a project's SAVED state (world reference + source, layout,
    scenarios, commit log) into a NEW id at revision 0 -- the world + scenario
    objects are shared by REFERENCE (content-addressed in the immutable
    substrate), and UNCOMMITTED edits in an open source session are NOT forked;
  * `trash` is a SOFT-delete (move the mutable `<id>.json` into `.trash/`) --
    reversible, a single mutable-file op, distinct from the DEFERRED multi-op
    atomic graph-object deletion; it never touches shared immutable objects.

Battery Q1-Q8:

  Q1  create_new mints a NEW project (distinct id, demo world, revision 0),
      listed by list_project_infos with its display name;
  Q2  create_new refuses to clobber an existing id (WRL_PROJECT_EXISTS);
  Q3  rename changes the display name only (project_id + world invariant),
      exact-CAS bumps the revision, list_infos reflects the new name;
  Q4  fork copies the SAVED state into a new id at revision 0 (same world +
      source + layout + scenarios + commit log); the source is untouched; a
      second fork onto the same id refuses (WRL_PROJECT_EXISTS);
  Q5  fork forks the COMMITTED state, NOT an open source session's uncommitted
      edit (the fork reproduces the last committed world);
  Q6  trash soft-deletes -- the id leaves list_projects, its file is under
      `.trash/`, the shared immutable world object stays resolvable, and a
      trash of an absent id is WRL_PROJECT_MISSING;
  Q7  list_project_infos summarizes each project (name, revision, world id,
      scenario + commit counts), sorted by (name, id);
  Q8  NATIVE -- a FORKED world folds ic_ref == ic32 == the independent Fixture
      oracle over its demo scenario.

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
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


def main():
    print("[BINDING wrl-v0.5-4] Library management (New/Open/Fork/Rename/Trash) "
          "(Q1-Q8)")
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

    root = tempfile.mkdtemp(prefix="wrl_library_")
    try:
        demo_sem = SB.DEMO_WORLD_SEMANTIC_ID
        edited_sem = _lower(EDITED_SRC).semantic_artifact_id
        store = PR.ForgeProjectStore(os.path.join(root, "projects"))
        cache = _cache(root)

        # ---- Q1 create_new mints a NEW project ------------------------------
        cache.open("main")                               # the default project
        s_alpha = cache.create_new("alpha", "Alpha World")
        infos1 = {d["project_id"]: d for d in cache.list_infos()}
        q1 = (store.exists("alpha")
              and store.load("alpha")["revision"] == 0
              and s_alpha.draft.active_semantic_id == demo_sem
              and infos1.get("alpha", {}).get("name") == "Alpha World"
              and set(infos1) == {"main", "alpha"})
        rep(q1, None,
            "Q1) create_new mints a NEW project (distinct id, demo world, "
            "revision 0) listed by list_project_infos with its display name")

        # ---- Q2 create_new refuses to clobber -------------------------------
        q2 = _raises(lambda: cache.create_new("alpha", "again"),
                     PR.WRL_PROJECT_EXISTS)
        rep(q2, None,
            "Q2) create_new refuses to clobber an existing id "
            "(WRL_PROJECT_EXISTS)")

        # ---- Q3 rename changes the display name only ------------------------
        world_before = store.load("alpha")["active_world_semantic_id"]
        saved = cache.rename("alpha", "Renamed World")
        doc3 = store.load("alpha")
        infos3 = {d["project_id"]: d for d in cache.list_infos()}
        q3 = (saved["name"] == "Renamed World"
              and saved["revision"] == 1
              and doc3["project_id"] == "alpha"
              and doc3["active_world_semantic_id"] == world_before
              and cache.revision("alpha") == 1
              and infos3["alpha"]["name"] == "Renamed World")
        rep(q3, None,
            "Q3) rename changes the display name only (project_id + world "
            "invariant); exact-CAS bumps the revision; list_infos reflects it")

        # ---- Q4 fork copies the SAVED state into a new id at revision 0 ------
        src_doc = store.load("alpha")
        s_fork = cache.fork("alpha", "beta")
        fork_doc = store.load("beta")
        untouched = store.load("alpha")
        q4 = (store.exists("beta")
              and fork_doc["revision"] == 0
              and fork_doc["active_world_semantic_id"]
              == src_doc["active_world_semantic_id"]
              and fork_doc["world_source"] == src_doc["world_source"]
              and fork_doc["layout"] == src_doc["layout"]
              and fork_doc["scenarios"] == src_doc["scenarios"]
              and fork_doc["commits"] == src_doc["commits"]
              and fork_doc["name"] == "Renamed World (fork)"
              and s_fork.draft.active_semantic_id
              == src_doc["active_world_semantic_id"]
              and untouched["revision"] == src_doc["revision"]   # source intact
              and _raises(lambda: cache.fork("alpha", "beta"),
                          PR.WRL_PROJECT_EXISTS))
        rep(q4, None,
            "Q4) fork copies the SAVED state into a new id at revision 0 (same "
            "world/source/layout/scenarios/commits); source intact; re-fork "
            "onto the same id refuses (WRL_PROJECT_EXISTS)")

        # ---- Q5 fork forks the COMMITTED state, not uncommitted edits -------
        s_alpha2 = cache.open("alpha")
        res5 = _apply_text(s_alpha2, EDITED_SRC)        # uncommitted, NOT saved
        cache.fork("alpha", "gamma")
        gamma = store.load("gamma")
        q5 = (res5["replace"]["candidate_valid"]
              and s_alpha2.draft.candidate_semantic_id == edited_sem
              and gamma["active_world_semantic_id"] == demo_sem   # committed, not edit
              and gamma["active_world_semantic_id"] != edited_sem)
        rep(q5, None,
            "Q5) fork forks the COMMITTED state, NOT an open source session's "
            "uncommitted edit (the fork reproduces the last committed world)")

        # ---- Q6 trash soft-deletes ------------------------------------------
        # sync gamma's world into an immutable store first, so we can prove the
        # shared object survives a project trash.
        wstore = ST.WorldObjectStore(os.path.join(root, "worlds"))
        sstore = ST.ScenarioRuntimeStore(os.path.join(root, "scen"))
        world_sem = PR.sync_project_objects(gamma, wstore, sstore)
        trash_path = cache.trash("gamma")
        after_ids = set(store.list_projects())
        q6 = (not store.exists("gamma")
              and "gamma" not in after_ids
              and os.path.exists(trash_path)
              and os.path.sep + ".trash" + os.path.sep in trash_path
              and wstore.get(world_sem) is not None        # shared world survives
              and _raises(lambda: cache.trash("gamma"), PR.WRL_PROJECT_MISSING))
        rep(q6, None,
            "Q6) trash soft-deletes (id leaves list_projects, file under "
            ".trash/, shared immutable world survives); absent trash is "
            "WRL_PROJECT_MISSING")

        # ---- Q7 list_project_infos summarizes + sorts -----------------------
        infos7 = cache.list_infos()
        ids7 = [d["project_id"] for d in infos7]
        by_id = {d["project_id"]: d for d in infos7}
        names7 = [d["name"] for d in infos7]
        q7 = (set(ids7) == {"main", "alpha", "beta"}       # gamma trashed
              and names7 == sorted(names7)                  # sorted by name
              and by_id["alpha"]["scenarios"] == 2
              and by_id["beta"]["scenarios"] == 2
              and all(isinstance(d["commits"], int) for d in infos7)
              and by_id["alpha"]["active_world_semantic_id"]
              == by_id["beta"]["active_world_semantic_id"])  # fork shares world
        rep(q7, None,
            "Q7) list_project_infos summarizes each project (name, revision, "
            "world id, scenario + commit counts), sorted by (name, id)")

        # ---- Q8 NATIVE: a FORKED world folds --------------------------------
        s_beta = cache.open("beta")
        prog8 = _lower(s_beta.to_text())
        view8 = P.plan_view(P.artifact_to_compile_plan_v1(prog8.sealed_artifact))
        fx8 = _lower(SB.DEMO_WORLD_SOURCE).as_fixture_for_test()
        scen8 = SC.demo_scenario(demo_sem)
        ifa8, scr8 = SC.scenario_to_script(scen8)
        ref8 = _fold_films(view8, O.norm, ifa8, scr8)
        orc8 = _fold_fixture(fx8, view8, O.norm, ifa8, scr8)
        n8r = (prog8.semantic_artifact_id == demo_sem and ref8 == orc8)
        n8n = None
        if not SKIP_NATIVE:
            n8n = (_fold_films(view8, O.native, ifa8, scr8) == ref8)
        rep(n8r, n8n,
            "Q8) NATIVE -- a FORKED world folds ic_ref == ic32 == the "
            "independent Fixture oracle over its demo scenario")
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
    print(f"\n[wrl-v0.5-4] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.5-4 makes the Forge World Library plural: the store + "
          "cache gain list_project_infos/create_new/rename/fork/trash so a user "
          "can name, switch, fork, rename and trash multiple persisted worlds. "
          "project_id is the immutable identity key (rename changes only the "
          "display name, Q3); fork copies the SAVED state into a new id at "
          "revision 0 with world + scenario objects shared by REFERENCE (Q4) "
          "and forks the COMMITTED not uncommitted world (Q5); trash is a "
          "reversible SOFT-delete of the mutable project doc that never touches "
          "the shared immutable objects (Q6). NO new identity, NO new runtime "
          "construct; a forked world stays natively runnable (Q8).")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
