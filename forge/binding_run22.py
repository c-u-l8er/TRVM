"""binding_run22.py -- v0.4-5 native + golden closure THROUGH THE LIVE ENDPOINTS
(Spinner Bench).

v0.4-4c wired the text->canvas convergence transaction to the running SPA
(POST /api/draft/source + browser reconciliation). v0.4-5 closes the editing UI:
it proves the LIVE endpoint path -- source -> commit -> run -- yields a natively
runnable world, adds a commit/undo history log and a scenario-compatibility
surfacing to the commit endpoint, and re-asserts golden-preset byte invariance
across the whole editing surface. This battery drives the ACTUAL endpoint helper
functions (`spinner_bench._draft_*_payload`), not the library directly, so it
covers the server path an operator's clicks take (K1-K8):

  K1  the reset/open endpoint yields a clean view (rev 0, active == candidate ==
      demo id, 6 nodes / 4 edges, empty commit log, undo_depth 0);
  K2  the source endpoint applies a valid free-form edit (candidate_valid, rev 1,
      undo_depth 1, candidate id != demo id);
  K3  the commit endpoint promotes the candidate (new active == candidate,
      previous_active == demo id), logs exactly one commit, and surfaces the
      scenario-compatibility law (ScenarioDigest invariant, ReplayBundleID moved);
  K4  NATIVE -- the endpoint-committed world (re-lowered from the view text) folds
      ic_ref == ic32 == the independent Fixture oracle;
  K5  golden invariance -- an UNEDITED commit leaves active == the demo id, its
      scenario-compat is a no-op (digest invariant, ReplayBundleID NOT moved), and
      the demo world still reproduces the golden SCRIPT films ic_ref == ic32;
  K6  the commit log is append-only and monotone -- two successive commits append
      two entries whose previous_active chains to the prior active_semantic_id;
  K7  the undo endpoint restores the exact prior candidate id (monotone revision
      increment), and reports undo_depth honestly;
  K8  NATIVE -- the Golden Demo and nine-epoch Acceptance Bench presets are
      unperturbed (still fold ic_ref == ic32; demo still reproduces golden films).

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import os
import sys
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
import wrl_canvas as CV
import wrl_format as F
import wrl_scenario as SC
import wrl_draft as D
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


def _source_req(session_id, replace_id, source, base_revision=None):
    r = {"session_id": session_id, "replace_id": replace_id, "source": source}
    if base_revision is not None:
        r["base_revision"] = base_revision
    return r


def main():
    print("[BINDING wrl-v0.4-5] native + golden closure via live endpoints (K1-K8)")
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

    prog = SB._prog(SB.DEMO_WORLD_SOURCE)
    sem = prog.semantic_artifact_id

    # canonical object/edge lists (from a fresh draft) for a valid multi-change edit
    dref = D.new_draft(prog, "dr")
    demo_objs = [dict(o) for o in dref.objects]
    demo_edges = [dict(e) for e in dref.edges]
    profile = dref.profile_id
    drop = {"p1", "d0"}
    valid_objs = [o for o in demo_objs if o["object_id"] not in drop]
    valid_edges = [e for e in demo_edges
                   if e["src"] not in drop and e["dst"] not in drop]
    VALID_SRC = F.format_wrl_core(D._graph_from(valid_objs, valid_edges, profile))

    # ---- K1 reset/open endpoint yields a clean view --------------------------
    p = SB._draft_reset_payload("k1")
    v = p["view"]
    k1 = (p["ok"] and v["semantic_revision"] == 0
          and v["active_semantic_id"] == sem
          and v["candidate_semantic_id"] == sem and v["candidate_valid"]
          and len(v["nodes"]) == 6 and len(v["edges"]) == 4
          and v["commits"] == [] and v["undo_depth"] == 0)
    rep(k1, None,
        "K1) the reset endpoint yields a clean view (rev 0, active == candidate "
        "== demo id, 6 nodes / 4 edges, empty commit log, undo_depth 0)")

    # ---- K2 source endpoint applies a valid free-form edit -------------------
    SB._draft_reset_payload("k2")
    r = SB._draft_source_payload(_source_req("k2", "k2-1", VALID_SRC))
    v = r["view"]
    k2 = (r["ok"] and r["apply"]["status"] == "candidate_valid"
          and v["semantic_revision"] == 1 and v["undo_depth"] == 1
          and v["candidate_valid"] and v["candidate_semantic_id"] != sem
          and r["apply"]["draft_diff"]["objects_removed"] == ["d0", "p1"])
    rep(k2, None,
        "K2) the source endpoint applies a valid free-form edit (candidate_valid, "
        "rev 1, undo_depth 1, candidate id != demo id)")

    # ---- K3 commit endpoint promotes + logs + surfaces scenario-compat -------
    SB._draft_reset_payload("k3")
    SB._draft_source_payload(_source_req("k3", "k3-1", VALID_SRC))
    cand3 = SB._draft_payload("k3")["view"]["candidate_semantic_id"]
    rc = SB._draft_commit_payload({"session_id": "k3"})
    co = rc["commit"]
    cmp3 = rc["scenario_compat"]
    v = rc["view"]
    k3 = (rc["ok"] and co["active_semantic_id"] == cand3
          and co["previous_active"] == sem
          and v["active_semantic_id"] == cand3
          and len(v["commits"]) == 1 and v["commits"][0]["previous_active"] == sem
          and cmp3["changed"] and cmp3["digest_invariant"]
          and cmp3["replay_bundle_moved"]
          and cmp3["replay_bundle_old"] != cmp3["replay_bundle_new"])
    rep(k3, None,
        "K3) the commit endpoint promotes the candidate (new active == candidate, "
        "previous_active == demo id), logs one commit, and surfaces the "
        "scenario-compat law (digest invariant, ReplayBundleID moved)")

    # ---- K4 NATIVE endpoint-committed world folds ic_ref == ic32 == oracle ---
    txt4 = SB._draft_payload("k3")["view"]["text"]
    prog4 = W.lower_program(txt4, W.parse_wrl_core)
    view4 = P.plan_view(P.artifact_to_compile_plan_v1(prog4.sealed_artifact))
    fx4 = prog4.as_fixture_for_test()
    demo4 = SC.demo_scenario(prog4.semantic_artifact_id)
    ifa4, scr4 = SC.scenario_to_script(demo4)
    ref4 = _fold_films(view4, O.norm, ifa4, scr4)
    orc4 = _fold_fixture(fx4, view4, O.norm, ifa4, scr4)
    k4r = (prog4.semantic_artifact_id == cand3 and ref4 == orc4)
    k4n = None
    if not SKIP_NATIVE:
        k4n = (_fold_films(view4, O.native, ifa4, scr4) == ref4)
    rep(k4r, k4n,
        "K4) NATIVE -- the endpoint-committed world (re-lowered from the view "
        "text) folds ic_ref == ic32 == the independent Fixture oracle")

    # ---- K5 golden invariance: an unedited commit is a no-op -----------------
    SB._draft_reset_payload("k5")
    rc5 = SB._draft_commit_payload({"session_id": "k5"})
    cmp5 = rc5["scenario_compat"]
    view5 = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
    golden5 = _fold_films(view5, O.norm, ("ob",), SB.SCRIPT)
    demo5 = SC.demo_scenario(sem)
    ifa5, scr5 = SC.scenario_to_script(demo5)
    demo_ref5 = _fold_films(view5, O.norm, ifa5, scr5)
    k5r = (rc5["commit"]["active_semantic_id"] == sem
           and cmp5["changed"] is False and cmp5["digest_invariant"]
           and cmp5["replay_bundle_moved"] is False
           and demo_ref5 == golden5)
    k5n = None
    if not SKIP_NATIVE:
        k5n = (_fold_films(view5, O.native, ifa5, scr5) == demo_ref5)
    rep(k5r, k5n,
        "K5) golden invariance -- an UNEDITED commit leaves active == the demo "
        "id, scenario-compat is a no-op (digest invariant, replay bundle NOT "
        "moved), and the demo world still reproduces the golden SCRIPT films")

    # ---- K6 commit log is append-only + monotone -----------------------------
    SB._draft_reset_payload("k6")
    SB._draft_source_payload(_source_req("k6", "k6-1", VALID_SRC))
    r6a = SB._draft_commit_payload({"session_id": "k6"})
    # a second edit: append a disconnected Orb on the (now-committed) world
    add_objs = valid_objs + [{"object_id": "orbX", "role": "Orb",
                              "static_config": {}}]
    ADD_SRC = F.format_wrl_core(D._graph_from(add_objs, valid_edges, profile))
    SB._draft_source_payload(_source_req("k6", "k6-2", ADD_SRC))
    r6b = SB._draft_commit_payload({"session_id": "k6"})
    hist = SB._draft_history_payload("k6")["history"]
    commits = hist["commits"]
    k6 = (len(commits) == 2 and commits[0]["index"] == 0
          and commits[1]["index"] == 1
          and commits[0]["previous_active"] == sem
          and commits[1]["previous_active"] == commits[0]["active_semantic_id"]
          and r6b["commit"]["active_semantic_id"]
          == commits[1]["active_semantic_id"])
    rep(k6, None,
        "K6) the commit log is append-only + monotone (two commits, indices 0/1, "
        "previous_active chains to the prior active_semantic_id)")

    # ---- K7 undo endpoint restores exact prior candidate id ------------------
    SB._draft_reset_payload("k7")
    SB._draft_source_payload(_source_req("k7", "k7-1", VALID_SRC))
    rev_after = SB._draft_payload("k7")["view"]["semantic_revision"]
    ru = SB._draft_undo_payload("k7")
    vu = ru["view"]
    k7 = (ru["undone"] and vu["candidate_semantic_id"] == sem
          and vu["candidate_valid"]
          and vu["semantic_revision"] == rev_after + 1   # monotone increment
          and vu["undo_depth"] == 0)
    rep(k7, None,
        "K7) the undo endpoint restores the EXACT prior candidate id (monotone "
        "revision increment) and reports undo_depth honestly")

    # ---- K8 NATIVE Golden Demo + Acceptance Bench presets unperturbed --------
    view8 = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
    demo8 = SC.demo_scenario(sem)
    ifa_d, scr_d = SC.scenario_to_script(demo8)
    golden8 = _fold_films(view8, O.norm, ("ob",), SB.SCRIPT)
    demo_ref8 = _fold_films(view8, O.norm, ifa_d, scr_d)
    bench8 = SC.bench_scenario(sem)
    ifa_b, scr_b = SC.scenario_to_script(bench8)
    bench_ref8 = _fold_films(view8, O.norm, ifa_b, scr_b)
    k8r = (demo_ref8 == golden8 and len(scr_b) == 9)
    k8n = None
    if not SKIP_NATIVE:
        k8n = (_fold_films(view8, O.native, ifa_d, scr_d) == demo_ref8
               and _fold_films(view8, O.native, ifa_b, scr_b) == bench_ref8)
    rep(k8r, k8n,
        "K8) NATIVE -- the Golden Demo reproduces the golden SCRIPT films and the "
        "nine-epoch Acceptance Bench still folds ic_ref == ic32 (v0.4-5 did not "
        "perturb the presets)")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.4-5] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.4-5 closes the editing UI: the LIVE endpoint path "
          "source -> commit -> run yields a natively runnable world (K4); the "
          "commit endpoint adds an append-only commit log and surfaces the "
          "scenario-compatibility law -- a committed world change keeps the "
          "ScenarioDigest invariant while moving only the ReplayBundleID (K3), "
          "and an UNEDITED commit is a no-op leaving the demo id and golden films "
          "intact (K5). The commit log is monotone (K6), undo stays exact and "
          "monotone (K7), and the Golden/Bench presets are unperturbed (K8). NO "
          "new runtime construct; the commit log is pure session bookkeeping.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
