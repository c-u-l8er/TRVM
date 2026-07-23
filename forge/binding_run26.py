"""binding_run26.py -- v0.5-3 session migration: the ProjectSessionCache
(Forge World Library, phase 3).

v0.5-2 (binding_run25) built the durable `ForgeProjectV1` document + store.
v0.5-3 migrates the live server's ephemeral `_DRAFT_SESSIONS` dict onto that
store via `wrl_project.ProjectSessionCache`: each `project_id` maps to ONE live
CanvasSession backed by a persisted project document. A COMMIT is the
persistence boundary -- `persist` writes the session's now-active world back to
the store with per-project exact-CAS -- so committed edits survive a restart,
while uncommitted draft edits + the undo stack stay session-local (the v0.5-2
rule). `reset` reverts a session to its saved state (never wipes the project).

Battery P1-P8:

  P1  first access lazily CREATES a default project from the demo world at
      revision 0; the opened session reproduces the demo SemanticArtifactID;
  P2  an UNCOMMITTED apply_text edit moves the candidate but does NOT persist --
      the on-disk project is untouched (still the demo world, revision 0);
  P3  commit + persist writes the committed world (revision bumps to 1,
      active_world_semantic_id moves to the committed id) and a FRESH cache over
      the same store reopens the session at exactly that world (restart-durable);
  P4  exact-CAS is monotone -- a second edit + commit + persist bumps the
      revision to 2 and the cache tracks it;
  P5  reset after an uncommitted edit reverts the session to the persisted
      (committed) world, NOT the demo, leaving the on-disk project unchanged;
  P6  the demo scenario presets (golden + bench) persist + survive reload
      (validate, digests match);
  P7  the reopened session's commit log is restored (length + last active id);
  P8  NATIVE -- the committed-then-persisted-then-reopened world folds
      ic_ref == ic32 == the independent Fixture oracle over its demo scenario.

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

# a SECOND valid edit (add a disconnected orb) -- distinct from EDITED_SRC
EDITED_SRC2 = """profile forge.world.core.v1

[pulser:p0](every 2){sig_out}
[relay:r0]{sig_in, sig_out}
[spinner:sp](w=16, n=8, rotor=quarter_turn_z, configurable){sig_in, socket}
[orb:ob]{pose}
[orb:ob2]{pose}

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
    print("[BINDING wrl-v0.5-3] ProjectSessionCache session migration (P1-P8)")
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

    root = tempfile.mkdtemp(prefix="wrl_projcache_")
    try:
        demo_sem = SB.DEMO_WORLD_SEMANTIC_ID
        edited_sem = _lower(EDITED_SRC).semantic_artifact_id
        edited_sem2 = _lower(EDITED_SRC2).semantic_artifact_id
        store = PR.ForgeProjectStore(os.path.join(root, "projects"))
        cache = _cache(root)

        # ---- P1 first access creates a default project at revision 0 --------
        sess = cache.open("main")
        p1 = (store.exists("main")
              and cache.revision("main") == 0
              and store.load("main")["revision"] == 0
              and sess.draft.active_semantic_id == demo_sem
              and store.load("main")["active_world_semantic_id"] == demo_sem)
        rep(p1, None,
            "P1) first access lazily CREATES a default project from the demo "
            "world at revision 0; the session reproduces the demo sem id")

        # ---- P2 an uncommitted edit does NOT persist ------------------------
        res = _apply_text(sess, EDITED_SRC)
        on_disk = store.load("main")
        p2 = (res["replace"]["candidate_valid"]
              and sess.draft.candidate_semantic_id == edited_sem
              and cache.revision("main") == 0
              and on_disk["revision"] == 0
              and on_disk["active_world_semantic_id"] == demo_sem)
        rep(p2, None,
            "P2) an UNCOMMITTED apply_text edit moves the candidate but does NOT "
            "persist -- the on-disk project is untouched (demo world, revision 0)")

        # ---- P3 commit + persist writes the committed world -----------------
        _commit(sess)
        saved = cache.persist("main")
        # a FRESH cache over the same store == a server restart
        cache2 = _cache(root)
        sess3 = cache2.open("main")
        reloaded = store.load("main")
        p3 = (saved["revision"] == 1
              and reloaded["revision"] == 1
              and reloaded["active_world_semantic_id"] == edited_sem
              and cache.revision("main") == 1
              and sess3.draft.active_semantic_id == edited_sem
              and _lower(sess3.to_text()).semantic_artifact_id == edited_sem)
        rep(p3, None,
            "P3) commit + persist writes the committed world (revision -> 1, "
            "active moves) and a FRESH cache reopens it (restart-durable)")

        # ---- P4 exact-CAS is monotone across a second commit ----------------
        _apply_text(sess, EDITED_SRC2)
        _commit(sess)
        saved2 = cache.persist("main")
        reloaded2 = store.load("main")
        p4 = (saved2["revision"] == 2
              and reloaded2["revision"] == 2
              and reloaded2["active_world_semantic_id"] == edited_sem2
              and cache.revision("main") == 2)
        rep(p4, None,
            "P4) exact-CAS is monotone -- a second edit + commit + persist bumps "
            "the revision to 2 and the cache tracks it")

        # ---- P5 reset reverts to the persisted (committed) world ------------
        _apply_text(sess, SB.DEMO_WORLD_SOURCE)     # an uncommitted revert-ish edit
        before = store.load("main")
        sess5 = cache.reset("main")
        after = store.load("main")
        p5 = (sess5.draft.active_semantic_id == edited_sem2   # saved, not demo
              and sess5.draft.candidate_error is None
              and cache.revision("main") == 2
              and before["revision"] == after["revision"] == 2  # store untouched
              and after["active_world_semantic_id"] == edited_sem2)
        rep(p5, None,
            "P5) reset after an uncommitted edit reverts the session to the "
            "persisted (committed) world, NOT the demo; store unchanged")

        # ---- P6 the scenario presets persist + survive reload ---------------
        doc6 = store.load("main")
        names6 = [s["name"] for s in doc6["scenarios"]]
        # digests recompute + match after reload
        digest_ok = all(SC.scenario_digest(s["scenario"]) == s["scenario_digest"]
                        for s in doc6["scenarios"])
        p6 = (sorted(names6) == ["bench", "golden"] and digest_ok)
        rep(p6, None,
            "P6) the demo scenario presets (golden + bench) persist + survive "
            "reload (validate, digests match)")

        # ---- P7 the reopened session's commit log is restored ---------------
        cache7 = _cache(root)
        sess7 = cache7.open("main")
        p7 = (len(sess7.commits) == len(sess5.commits)
              and len(sess7.commits) >= 2
              and sess7.commits[-1]["active_semantic_id"] == edited_sem2)
        rep(p7, None,
            "P7) the reopened session's commit log is restored (length + last "
            "active id)")

        # ---- P8 NATIVE: the persisted-then-reopened world still folds --------
        prog8 = _lower(sess7.to_text())
        view8 = P.plan_view(P.artifact_to_compile_plan_v1(prog8.sealed_artifact))
        fx8 = _lower(EDITED_SRC2).as_fixture_for_test()      # independent oracle
        scen8 = SC.demo_scenario(edited_sem2)
        ifa8, scr8 = SC.scenario_to_script(scen8)
        ref8 = _fold_films(view8, O.norm, ifa8, scr8)
        orc8 = _fold_fixture(fx8, view8, O.norm, ifa8, scr8)
        n8r = (prog8.semantic_artifact_id == edited_sem2 and ref8 == orc8)
        n8n = None
        if not SKIP_NATIVE:
            n8n = (_fold_films(view8, O.native, ifa8, scr8) == ref8)
        rep(n8r, n8n,
            "P8) NATIVE -- the committed-then-persisted-then-reopened world folds "
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
    print(f"\n[wrl-v0.5-3] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.5-3 migrates the live server's ephemeral session dict onto "
          "the durable ForgeProjectV1 store via ProjectSessionCache: each "
          "project_id maps to one CanvasSession backed by a persisted document, a "
          "COMMIT persists the session's now-active world (per-project exact-CAS) "
          "so committed edits survive a restart (P3/P7), uncommitted draft edits + "
          "the undo stack stay session-local (P2), and reset reverts to the saved "
          "state (P5). NO new identity, NO new runtime construct; the reopened "
          "world stays natively runnable ic_ref == ic32 == oracle (P8).")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
