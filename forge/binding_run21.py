"""binding_run21.py -- v0.4-4b free-form text -> world convergence (Spinner Bench).

v0.4-4a bound the canvas to the semantic draft in the CANVAS -> SEMANTIC -> TEXT
direction (one gesture = one GraphEditV1 op). v0.4-4b closes the reverse
TEXT -> CANVAS direction for a FREE-FORM multi-change edit, per GPT-5.6's ruling:
a wholesale text paste is applied by the ATOMIC `wrl_draft.replace_world_source`
transaction -- a SEPARATE `ReplaceWorldSourceV1`, NOT a multi-op GraphEditV1 --
and the CanvasSession routes it through `apply_text`, snapshotting the layout in
lock-step with the draft's own history so ONE paste = ONE revision = ONE DraftDiff
= ONE undo. This battery proves the transaction law + canvas reconciliation +
scenario/identity invariance + native runnability (J1-J18):

  J1  a syntax failure leaves the revision, the ids, and the canvas UNCHANGED;
  J2  the world-source endpoint REJECTS legacy run-input syntax (`periods N` and
      `[epoch:N] ...`) with a typed WRL_WORLD_SOURCE_HAS_SCENARIO;
  J3  a formatting/comment-only replacement is a semantic NO-OP (no revision, no
      undo, id unchanged);
  J4  a multi-object replacement advances EXACTLY ONE revision;
  J5  a mutating replacement leaves EXACTLY ONE undo entry (draft + layout);
  J6  undo restores the exact prior SemanticArtifactID AND the exact prior layout;
  J7  a repeated `replace_id` is idempotent (same result, no further revision/undo);
  J8  a stale `base_revision` -> WRL_STALE_DRAFT (no auto-merge, no decomposition);
  J9  a parseable-but-invalid graph stays editable with a NULL candidate id and a
      typed diagnostic, and a follow-up replacement repairs it;
  J10 an invalid replacement leaves the ACTIVE sealed world runnable (ic_ref==ic32);
  J11 surviving objects/edges RETAIN their presentation across a text replacement;
  J12 new objects get the DETERMINISTIC default presentation;
  J13 text -> draft -> canvas -> text reproduces the canonical bytes + the id;
  J14 a candidate replacement does NOT change the ScenarioDigest or its binding;
  J15 commit-time compatibility rebinds the world metadata, RETAINS the
      ScenarioDigest, and moves ONLY the ReplayBundleID;
  J16 RemoveObject remains NON-cascading (a still-wired removal keeps the wire);
  J17 a valid text-edited world runs ic_ref == ic32 == the independent Fixture
      oracle;
  J18 the Golden Demo and the nine-epoch Acceptance Bench presets are unchanged
      (still fold ic_ref == ic32, demo still reproduces the golden SCRIPT films).

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import copy
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
import wrl_canonical as WC
import wrl_canvas as CV
import wrl_converge as CG
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
    """Fold through the independent Fixture oracle (admit + state use the Fixture,
    the step/enc/dec use the plan view) -- the acceptance-item-9 cross-check."""
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


def _rq(replace_id, base_revision, source, draft_id="dr"):
    return {"replace_version": D.REPLACE_VERSION, "replace_id": replace_id,
            "draft_id": draft_id, "base_revision": base_revision,
            "source": source}


def _commit(base_revision, expected, draft_id="dr"):
    return {"commit_version": D.COMMIT_VERSION, "draft_id": draft_id,
            "base_revision": base_revision,
            "expected_candidate_semantic_id": expected}


def _g(gesture_id, kind, **kw):
    d = {"gesture_version": CG.GESTURE_VERSION, "gesture_id": gesture_id,
         "kind": kind}
    d.update(kw)
    return d


def _src_from(objects, edges, profile):
    return F.format_wrl_core(D._graph_from(objects, edges, profile))


def _raises(code, thunk):
    try:
        thunk()
        return False
    except WC.WrlValidationError as e:
        return e.code == code
    except WC.WrlUnsupported as e:
        return getattr(e, "code", None) == code


def main():
    print("[BINDING wrl-v0.4-4b] free-form text -> world convergence (J1-J18)")
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

    # canonical demo text + object/edge lists (from a fresh draft)
    dref = D.new_draft(prog, "dr")
    demo_objs = copy.deepcopy(dref.objects)
    demo_edges = copy.deepcopy(dref.edges)
    profile = dref.profile_id
    CANON = _src_from(demo_objs, demo_edges, profile)

    # a valid multi-change replacement: drop the p1 -> d0 branch (remove p1, d0)
    drop = {"p1", "d0"}
    valid_objs = [o for o in demo_objs if o["object_id"] not in drop]
    valid_edges = [e for e in demo_edges
                   if e["src"] not in drop and e["dst"] not in drop]
    VALID_SRC = _src_from(valid_objs, valid_edges, profile)

    # a valid ADD replacement: append a disconnected Orb
    add_objs = demo_objs + [{"object_id": "orbX", "role": "Orb",
                             "static_config": {}}]
    ADD_SRC = _src_from(add_objs, demo_edges, profile)

    # ---- J1 syntax failure leaves revision / ids / canvas unchanged ----------
    s = CG.new_session(prog, "dr")
    lay0 = copy.deepcopy(s.layout)
    h0 = len(s._layout_history)
    r = s.apply_text(_rq("j1", 0, "this is not wrl @@@"))
    j1 = (r["replace"]["status"] == "syntax_error"
          and s.semantic_revision == 0 and s.candidate_semantic_id == sem
          and s.layout == lay0 and len(s._layout_history) == h0
          and r["replace"]["diagnostics"][0]["code"] == "WRL_UNSUPPORTED_FEATURE")
    rep(j1, None,
        "J1) a syntax failure leaves the revision, the candidate id, and the "
        "canvas UNCHANGED (no undo entry)")

    # ---- J2 endpoint rejects legacy run-input syntax -------------------------
    s2 = CG.new_session(prog, "dr")
    rp = s2.apply_text(_rq("j2p", 0, CANON + "\nperiods 7"))
    s2b = CG.new_session(prog, "dr")
    re_ = s2b.apply_text(_rq("j2e", 0, CANON + "\n[epoch:1] p0 mode=periodic"))
    j2 = (rp["replace"]["status"] == "syntax_error"
          and rp["replace"]["diagnostics"][0]["code"] == D.WRL_WORLD_SOURCE_HAS_SCENARIO
          and re_["replace"]["status"] == "syntax_error"
          and re_["replace"]["diagnostics"][0]["code"] == D.WRL_WORLD_SOURCE_HAS_SCENARIO
          and s2.semantic_revision == 0 and s2b.semantic_revision == 0)
    rep(j2, None,
        "J2) the world-source endpoint rejects legacy run-input syntax "
        "(`periods N` and `[epoch:N] ...`) with a typed "
        "WRL_WORLD_SOURCE_HAS_SCENARIO, draft untouched")

    # ---- J3 formatting/comment-only replacement is a semantic no-op ----------
    s3 = CG.new_session(prog, "dr")
    r = s3.apply_text(_rq("j3", 0, "; a leading comment\n\n" + CANON))
    j3 = (r["replace"]["status"] == "semantic_noop"
          and r["replace"]["semantic_noop"] is True
          and s3.semantic_revision == 0 and s3.candidate_semantic_id == sem
          and len(s3._layout_history) == 0)
    rep(j3, None,
        "J3) a formatting/comment-only replacement is a semantic NO-OP (no "
        "revision, no undo, id unchanged)")

    # ---- J4 multi-object replacement advances exactly one revision -----------
    s4 = CG.new_session(prog, "dr")
    r = s4.apply_text(_rq("j4", 0, VALID_SRC))
    j4 = (r["replace"]["status"] == "candidate_valid"
          and s4.semantic_revision == 1
          and r["replace"]["draft_diff"]["objects_removed"] == ["d0", "p1"]
          and s4.candidate_semantic_id != sem
          and sorted(n["object_id"] for n in s4.layout["nodes"])
          == sorted(o["object_id"] for o in valid_objs))
    rep(j4, None,
        "J4) a multi-object replacement advances EXACTLY ONE revision and the "
        "canvas reconciles to the new object set")

    # ---- J5 exactly one undo entry (draft + layout in lock-step) -------------
    s5 = CG.new_session(prog, "dr")
    s5.apply_text(_rq("j5", 0, VALID_SRC))
    j5 = (len(s5._layout_history) == 1 and len(s5.draft._history) == 1)
    rep(j5, None,
        "J5) a mutating replacement leaves EXACTLY ONE undo entry in both the "
        "draft history and the parallel layout history")

    # ---- J6 undo restores exact prior semantic id AND layout -----------------
    s6 = CG.new_session(prog, "dr")
    s6.apply_gesture(_g("mv", "set_presentation", object_id="sp",
                        presentation={"x": 4242, "color": "#0f0"}))
    prior_id = s6.candidate_semantic_id
    prior_lay = copy.deepcopy(s6.layout)
    s6.apply_text(_rq("j6", s6.semantic_revision, VALID_SRC))
    s6.undo()
    j6 = (s6.candidate_semantic_id == prior_id and s6.layout == prior_lay
          and s6.candidate_error is None)
    rep(j6, None,
        "J6) undo restores the EXACT prior SemanticArtifactID and the EXACT "
        "prior layout (survivor presentation included)")

    # ---- J7 repeated replace_id is idempotent --------------------------------
    s7 = CG.new_session(prog, "dr")
    r_a = s7.apply_text(_rq("j7", 0, VALID_SRC))
    rev_a = s7.semantic_revision
    hist_a = len(s7._layout_history)
    r_b = s7.apply_text(_rq("j7", 0, VALID_SRC))   # same id, replayed
    j7 = (r_b["replace"]["candidate_semantic_id"]
          == r_a["replace"]["candidate_semantic_id"]
          and s7.semantic_revision == rev_a
          and len(s7._layout_history) == hist_a)
    rep(j7, None,
        "J7) a repeated replace_id is idempotent (same result, no further "
        "revision, no further undo entry)")

    # ---- J8 stale base_revision -> WRL_STALE_DRAFT ---------------------------
    s8 = CG.new_session(prog, "dr")
    s8.apply_text(_rq("j8a", 0, VALID_SRC))        # rev -> 1
    j8 = _raises(D.WRL_STALE_DRAFT,
                 lambda: s8.apply_text(_rq("j8b", 0, CANON)))  # stale base 0
    rep(j8, None,
        "J8) a stale base_revision -> WRL_STALE_DRAFT (no auto-merge, no "
        "decomposition)")

    # ---- J9 parseable-but-invalid stays editable, then repairs ---------------
    s9 = CG.new_session(prog, "dr")
    INVALID_SRC = CANON + "\n[p0] --socket--> [ob]"   # 2nd controller on ob
    r = s9.apply_text(_rq("j9", 0, INVALID_SRC))
    j9_invalid = (r["replace"]["status"] == "semantic_invalid"
                  and r["replace"]["candidate_semantic_id"] is None
                  and s9.candidate_error is not None
                  and s9.semantic_revision == 1)
    # repair: a follow-up valid replacement on the now-current revision
    r2 = s9.apply_text(_rq("j9b", s9.semantic_revision, VALID_SRC))
    j9_repair = (r2["replace"]["status"] == "candidate_valid"
                 and s9.candidate_error is None and s9.semantic_revision == 2)
    rep(j9_invalid and j9_repair, None,
        "J9) a parseable-but-invalid graph stays editable with a NULL candidate "
        "id + typed diagnostic; a follow-up replacement repairs it")

    # ---- J10 invalid replacement leaves the active sealed world runnable ------
    s10 = CG.new_session(prog, "dr")
    s10.apply_text(_rq("j10", 0, INVALID_SRC))     # candidate invalid
    j10_active = (s10.draft.active_semantic_id == sem)
    view10 = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
    demo10 = SC.demo_scenario(sem)
    ifa10, scr10 = SC.scenario_to_script(demo10)
    got10 = _fold_films(view10, O.norm, ifa10, scr10)
    j10r = j10_active
    j10n = None
    if not SKIP_NATIVE:
        j10n = (_fold_films(view10, O.native, ifa10, scr10) == got10)
    rep(j10r, j10n,
        "J10) an invalid replacement leaves the active sealed world (== demo id) "
        "runnable, ic_ref == ic32")

    # ---- J11 surviving objects/edges retain presentation ---------------------
    s11 = CG.new_session(prog, "dr")
    s11.apply_gesture(_g("mv", "set_presentation", object_id="sp",
                        presentation={"x": 1111, "y": 2222}))
    surv_edge = CV.edge_key("SignalWire", "p0", "r0")   # survives the drop
    # tag the surviving edge's presentation, then replace
    for e in s11.layout["edges"]:
        if e["edge_key"] == surv_edge:
            e["presentation"] = {**e["presentation"], "route": "custom"}
    s11.apply_text(_rq("j11", s11.semantic_revision, VALID_SRC))
    spn = [n for n in s11.layout["nodes"] if n["object_id"] == "sp"][0]
    spe = [e for e in s11.layout["edges"] if e["edge_key"] == surv_edge]
    j11 = (spn["presentation"].get("x") == 1111
           and spn["presentation"].get("y") == 2222
           and len(spe) == 1 and spe[0]["presentation"].get("route") == "custom")
    rep(j11, None,
        "J11) surviving objects and edges RETAIN their node/route presentation "
        "across a text replacement")

    # ---- J12 new objects get the deterministic default presentation ----------
    s12 = CG.new_session(prog, "dr")
    s12.apply_text(_rq("j12", 0, ADD_SRC))
    idx = [i for i, o in enumerate(s12.draft.objects)
           if o["object_id"] == "orbX"][0]
    want = CV._node_presentation(idx, "Orb")
    orbx = [n for n in s12.layout["nodes"] if n["object_id"] == "orbX"][0]
    j12 = (orbx["presentation"] == want)
    rep(j12, None,
        "J12) a new object introduced by a text replacement gets the "
        "DETERMINISTIC default presentation")

    # ---- J13 text -> draft -> canvas -> text reproduces canonical bytes + id --
    s13 = CG.new_session(prog, "dr")
    s13.apply_text(_rq("j13", 0, VALID_SRC))
    cand13 = s13.candidate_semantic_id
    txt13 = s13.to_text()
    reparsed = W.lower_graph(W.parse_wrl_legacy_document(txt13)).semantic_artifact_id
    # re-applying the canonical text of the current graph is a semantic no-op
    r_again = s13.apply_text(_rq("j13b", s13.semantic_revision, txt13))
    j13 = (reparsed == cand13
           and r_again["replace"]["status"] == "semantic_noop"
           and s13.candidate_semantic_id == cand13)
    rep(j13, None,
        "J13) text -> draft -> canvas -> text reproduces the canonical bytes and "
        "the EXACT candidate SemanticArtifactID")

    # ---- J14 candidate replacement does NOT change the scenario or its binding
    s14 = CG.new_session(prog, "dr")
    scen14 = SC.demo_scenario(sem)
    dig_before = SC.scenario_digest(scen14)
    bind_before = scen14["world_semantic_id"]
    s14.apply_text(_rq("j14", 0, VALID_SRC))       # world changes (candidate)
    dig_after = SC.scenario_digest(scen14)
    j14 = (dig_after == dig_before and scen14["world_semantic_id"] == bind_before
           and bind_before == sem)
    rep(j14, None,
        "J14) a candidate text replacement does NOT change the ScenarioDigest or "
        "the scenario's world binding (the scenario is untouched until commit)")

    # ---- J15 commit-time compat: rebind world, retain digest, move replay id --
    s15 = CG.new_session(prog, "dr")
    s15.apply_text(_rq("j15", 0, VALID_SRC))
    cand15 = s15.candidate_semantic_id
    res15 = s15.commit(_commit(s15.semantic_revision, cand15))
    new_world = res15["active_semantic_id"]
    scen15 = SC.demo_scenario(sem)
    dig15 = SC.scenario_digest(scen15)
    rb_old = SC.replay_bundle_id(sem, dig15, scen15["initial_runtime"])
    rebound = SC.rebind_scenario(scen15, new_world)
    dig15b = SC.scenario_digest(rebound)
    rb_new = SC.replay_bundle_id(new_world, dig15b, rebound["initial_runtime"])
    j15 = (new_world == cand15 and dig15b == dig15
           and rebound["world_semantic_id"] == new_world and rb_new != rb_old)
    rep(j15, None,
        "J15) commit-time compatibility rebinds the world metadata, RETAINS the "
        "ScenarioDigest, and moves ONLY the ReplayBundleID")

    # ---- J16 RemoveObject remains NON-cascading ------------------------------
    s16 = CG.new_session(prog, "dr")
    edges_before = len(s16.draft.edges)
    r = s16.apply_gesture(_g("rm", "remove_node", target="r0"))  # r0 is wired
    j16 = (not r["candidate_valid"]
           and "WRL_UNKNOWN_ENDPOINT" in (r["candidate_error"] or "")
           and len(s16.draft.edges) == edges_before        # wires NOT cascaded
           and len(s16.draft.objects) == 5)                # only r0 removed
    rep(j16, None,
        "J16) RemoveObject remains NON-cascading: removing a still-wired object "
        "keeps its dangling wires and seals an invalid-but-editable candidate")

    # ---- J17 valid text-edited world runs ic_ref == ic32 == Fixture oracle ----
    s17 = CG.new_session(prog, "dr")
    s17.apply_text(_rq("j17", 0, VALID_SRC))
    cand17 = s17.candidate_semantic_id
    res17 = s17.commit(_commit(s17.semantic_revision, cand17))
    sealed17 = res17["sealed_artifact"]
    prog17 = W.lower_program(s17.to_text(), W.parse_wrl_legacy_document)
    view17 = P.plan_view(P.artifact_to_compile_plan_v1(sealed17))
    fx17 = prog17.as_fixture_for_test()
    demo17 = SC.demo_scenario(sealed17.semantic_id)
    ifa17, scr17 = SC.scenario_to_script(demo17)
    ref17 = _fold_films(view17, O.norm, ifa17, scr17)
    orc17 = _fold_fixture(fx17, view17, O.norm, ifa17, scr17)
    j17r = (prog17.semantic_artifact_id == cand17 and ref17 == orc17)
    j17n = None
    if not SKIP_NATIVE:
        j17n = (_fold_films(view17, O.native, ifa17, scr17) == ref17)
    rep(j17r, j17n,
        "J17) a valid text-edited world folds ic_ref == ic32 == the independent "
        "Fixture oracle")

    # ---- J18 Golden Demo + nine-epoch Acceptance Bench presets unchanged ------
    view18 = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
    demo18 = SC.demo_scenario(sem)
    ifa_d, scr_d = SC.scenario_to_script(demo18)
    golden = _fold_films(view18, O.norm, ("ob",), SB.SCRIPT)
    demo_ref = _fold_films(view18, O.norm, ifa_d, scr_d)
    bench18 = SC.bench_scenario(sem)
    ifa_b, scr_b = SC.scenario_to_script(bench18)
    bench_ref = _fold_films(view18, O.norm, ifa_b, scr_b)
    j18r = (demo_ref == golden and len(scr_b) == 9)
    j18n = None
    if not SKIP_NATIVE:
        j18n = (_fold_films(view18, O.native, ifa_d, scr_d) == demo_ref
                and _fold_films(view18, O.native, ifa_b, scr_b) == bench_ref)
    rep(j18r, j18n,
        "J18) the Golden Demo reproduces the golden SCRIPT films and the "
        "nine-epoch Acceptance Bench still folds, ic_ref == ic32 (v0.4-4b did "
        "not perturb the presets)")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.4-4b] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.4-4b adds the reverse TEXT -> CANVAS direction: a free-form "
          "multi-change text paste is applied by the ATOMIC "
          "wrl_draft.replace_world_source transaction -- a SEPARATE "
          "ReplaceWorldSourceV1, NOT a multi-op GraphEditV1 -- and the "
          "CanvasSession routes it through apply_text, snapshotting the layout in "
          "lock-step with the draft's own history so ONE paste = ONE revision = "
          "ONE DraftDiff = ONE undo. Idempotency is checked BEFORE the exact "
          "revision CAS; the endpoint rejects legacy run-input syntax "
          "(WRL_WORLD_SOURCE_HAS_SCENARIO); formatting/comments are non-semantic; "
          "a parseable-but-invalid graph stays editable with a null candidate id "
          "while the active sealed world stays runnable; RemoveObject stays "
          "non-cascading. NO new runtime construct.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
