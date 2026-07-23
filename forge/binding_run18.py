"""binding_run18.py -- v0.4-2 topology edits (Spinner Bench v0.4).

v0.4-1 made a world editable through a revisioned WorldDraft admitting exactly
`SetObjectConfig`. v0.4-2 extends `GraphEditV1` with the three TOPOLOGY ops --
`AddEdge` / `RemoveEdge` / `ReconnectEdge` -- over the SAME exact-CAS +
candidate-sealing + explicit-commit + monotone-undo contract, still with NO new
runtime construct. A topology op enforces only its OWN precondition (the edge
is / isn't already present); structural legality of the RESULT (unknown
endpoint, illegal port pair, or a controller conflict -- >1 signal-wire / socket
into one node) is DEFERRED to the seal exactly like a bad static_config, so an
illegal rewire yields an invalid-but-editable candidate, never a raise. This
battery proves the ops + the contract they inherit + two native gates (G1-G8):

  G1  AddEdge: adding a wire that creates a controller conflict (a second
      SignalWire into `r0`) seals INVALID (candidate None + typed
      WRL_CONTROLLER_CONFLICT) yet leaves the draft editable and undoes clean;
      re-adding an edge that already exists is refused WRL_BAD_EDIT
      (precondition), never reaching the seal.
  G2  RemoveEdge: removing an existing wire MOVES the candidate to exactly the
      independently-lowered world; removing an edge that is not present is
      refused WRL_BAD_EDIT.
  G3  ReconnectEdge: re-pointing an existing wire to a legal new endpoint moves
      the candidate to exactly the independently-lowered rewired world;
      reconnecting a MISSING source edge, or reconnecting ONTO an edge that
      already exists, are both refused WRL_BAD_EDIT.
  G4  validate_edit_v1 edge-spec gate: AddEdge with no `edge`, an `edge` missing
      a field, an `edge` with an unknown field, and ReconnectEdge with no `to`
      all raise WRL_BAD_EDIT; `AddObject` stays frozen-but-DEFERRED (its error
      names the deferral); `RemoveObject` likewise.
  G5  The inherited draft contract holds for topology ops: an edge edit on a
      stale base -> WRL_STALE_DRAFT; an idempotent edit_id retry no-ops; undo
      restores the EXACT prior SemanticArtifactID while the revision increments;
      commit requires the expected candidate (WRL_COMMIT_MISMATCH) then advances
      active.
  G6  An illegal rewire never commits: an AddEdge that overloads `r0` leaves the
      candidate invalid, `commit_draft` refuses it WRL_INVALID_CANDIDATE, and an
      undo repairs the candidate back to valid.
  G7  Native rewired-world gate: committing a legal pulser SWAP (two
      ReconnectEdges, p0<->p1 across r0 and d0) yields a NEW active
      SemanticArtifactID, and a scenario bound to that world folds through the
      unchanged plan/view path at ic_ref == ic32 -- a REWIRED world born from the
      editing path is natively runnable.
  G8  Native identity round-trip: RemoveEdge(p0->r0) then AddEdge(p0->r0)
      restores the EXACT original topology, so the candidate returns to the demo
      SemanticArtifactID; committing the round-tripped world leaves active == the
      demo id and reproduces the golden SCRIPT films byte-for-byte, ic_ref ==
      ic32.

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
import wrl_scenario as SC
import wrl_draft as D
import spinner_bench as SB
from admit import film_hash_v7
from fixture import init_state_v6, state_to_film_args_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

# demo edges, as {kind, src, dst} specs
E_P0_R0 = {"kind": "SignalWire", "src": "p0", "dst": "r0"}
E_P1_D0 = {"kind": "SignalWire", "src": "p1", "dst": "d0"}
E_P1_R0 = {"kind": "SignalWire", "src": "p1", "dst": "r0"}
E_P0_D0 = {"kind": "SignalWire", "src": "p0", "dst": "d0"}


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


def _eedit(edit_id, base, kind, edge, to=None, draft_id="dr"):
    op = {"kind": kind, "edge": copy.deepcopy(edge)}
    if to is not None:
        op["to"] = copy.deepcopy(to)
    return {"edit_version": D.EDIT_VERSION, "edit_id": edit_id,
            "draft_id": draft_id, "base_revision": base, "operation": op}


def _commit(base_revision, expected, draft_id="dr"):
    return {"commit_version": D.COMMIT_VERSION, "draft_id": draft_id,
            "base_revision": base_revision,
            "expected_candidate_semantic_id": expected}


def _indep(draft):
    return W.lower_graph(
        D._graph_from(copy.deepcopy(draft.objects), copy.deepcopy(draft.edges),
                      draft.profile_id)).semantic_artifact_id


def _raises(code, thunk):
    try:
        thunk()
        return False
    except WC.WrlValidationError as e:
        return e.code == code
    except WC.WrlUnsupported as e:
        return getattr(e, "code", None) == code


def main():
    print("[BINDING wrl-v0.4-2] topology edits (G1-G8)")
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

    # ---- G1 AddEdge: conflict -> invalid-but-editable; dup -> WRL_BAD_EDIT ----
    d = D.new_draft(prog, "dr")
    D.apply_edit(d, _eedit("a1", 0, "AddEdge", E_P1_R0))   # 2nd wire into r0
    g1_invalid = (d.candidate_semantic_id is None
                  and d.candidate_error is not None
                  and "WRL_CONTROLLER_CONFLICT" in d.candidate_error
                  and d.semantic_revision == 1)             # revision still moved
    D.undo(d)                                               # repairs
    g1_repaired = (d.candidate_semantic_id == sem
                   and d.candidate_error is None)
    g1_dup = _raises(D.WRL_BAD_EDIT,
                     lambda: D.apply_edit(
                         d, _eedit("a2", d.semantic_revision, "AddEdge",
                                   E_P0_R0)))               # already an edge
    rep(g1_invalid and g1_repaired and g1_dup, None,
        "G1) AddEdge overloading r0 seals invalid (WRL_CONTROLLER_CONFLICT) yet "
        "stays editable + undoes clean; re-adding an existing edge -> "
        "WRL_BAD_EDIT (precondition, never reaches the seal)")

    # ---- G2 RemoveEdge: moves the candidate; missing edge -> WRL_BAD_EDIT -----
    d2 = D.new_draft(prog, "dr")
    D.apply_edit(d2, _eedit("r1", 0, "RemoveEdge", E_P0_R0))
    g2_move = (d2.candidate_error is None
               and d2.candidate_semantic_id != sem
               and d2.candidate_semantic_id == _indep(d2))
    g2_missing = _raises(D.WRL_BAD_EDIT,
                         lambda: D.apply_edit(
                             d2, _eedit("r2", d2.semantic_revision,
                                        "RemoveEdge", E_P0_R0)))  # already gone
    rep(g2_move and g2_missing, None,
        "G2) RemoveEdge moves the candidate to exactly the independently-lowered "
        "world; removing an absent edge -> WRL_BAD_EDIT")

    # ---- G3 ReconnectEdge: legal move; missing src / onto-existing -> BAD -----
    d3 = D.new_draft(prog, "dr")
    D.apply_edit(d3, _eedit("c1", 0, "ReconnectEdge", E_P0_R0, to=E_P1_R0))
    g3_move = (d3.candidate_error is None
               and d3.candidate_semantic_id != sem
               and d3.candidate_semantic_id == _indep(d3))
    g3_missing = _raises(D.WRL_BAD_EDIT,
                         lambda: D.apply_edit(
                             d3, _eedit("c2", d3.semantic_revision,
                                        "ReconnectEdge", E_P0_R0, to=E_P0_D0)))
    # onto an edge that already exists (reconnect r0->sp's wire onto p1->d0 which
    # is present): use a fresh draft so state is clean
    d3b = D.new_draft(prog, "dr")
    g3_onto = _raises(D.WRL_BAD_EDIT,
                      lambda: D.apply_edit(
                          d3b, _eedit("c3", 0, "ReconnectEdge", E_P0_R0,
                                      to=E_P1_D0)))          # to already exists
    rep(g3_move and g3_missing and g3_onto, None,
        "G3) ReconnectEdge re-points a wire to exactly the independently-lowered "
        "rewired world; a missing source edge or a target that already exists -> "
        "WRL_BAD_EDIT")

    # ---- G4 edge-spec structural gate + deferred object ops ------------------
    g4_no_edge = _raises(D.WRL_BAD_EDIT, lambda: D.validate_edit_v1(
        {"edit_version": D.EDIT_VERSION, "edit_id": "x", "draft_id": "dr",
         "base_revision": 0, "operation": {"kind": "AddEdge"}}))
    g4_bad_field = _raises(D.WRL_BAD_EDIT, lambda: D.validate_edit_v1(
        _eedit("x", 0, "AddEdge", {"kind": "SignalWire", "src": "p0"})))
    g4_unknown = _raises(D.WRL_BAD_EDIT, lambda: D.validate_edit_v1(
        _eedit("x", 0, "AddEdge",
               {"kind": "SignalWire", "src": "p0", "dst": "r0", "z": 1})))
    g4_no_to = _raises(D.WRL_BAD_EDIT, lambda: D.validate_edit_v1(
        {"edit_version": D.EDIT_VERSION, "edit_id": "x", "draft_id": "dr",
         "base_revision": 0,
         "operation": {"kind": "ReconnectEdge", "edge": E_P0_R0}}))
    g4_addobj = _raises(D.WRL_BAD_EDIT, lambda: D.validate_edit_v1(
        {"edit_version": D.EDIT_VERSION, "edit_id": "x", "draft_id": "dr",
         "base_revision": 0, "operation": {"kind": "AddObject"}}))
    g4_rmobj = _raises(D.WRL_BAD_EDIT, lambda: D.validate_edit_v1(
        {"edit_version": D.EDIT_VERSION, "edit_id": "x", "draft_id": "dr",
         "base_revision": 0, "operation": {"kind": "RemoveObject"}}))
    rep(g4_no_edge and g4_bad_field and g4_unknown and g4_no_to and g4_addobj
        and g4_rmobj, None,
        "G4) validate_edit_v1 rejects a missing/malformed/unknown-field `edge`, "
        "a missing ReconnectEdge `to`, and the DEFERRED AddObject/RemoveObject "
        "-- all typed WRL_BAD_EDIT")

    # ---- G5 the inherited draft contract holds for topology ops --------------
    d5 = D.new_draft(prog, "dr")
    D.apply_edit(d5, _eedit("e1", 0, "ReconnectEdge", E_P0_R0, to=E_P1_R0))
    cand5 = d5.candidate_semantic_id
    g5_stale = _raises(D.WRL_STALE_DRAFT, lambda: D.apply_edit(
        d5, _eedit("e2", 0, "RemoveEdge", E_P1_D0)))         # stale base 0 (now 1)
    res_first = dict(d5._applied["e1"])
    res_retry = D.apply_edit(
        d5, _eedit("e1", 0, "ReconnectEdge", E_P0_R0, to=E_P1_R0))  # same id
    g5_idem = (res_retry == res_first and d5.semantic_revision == 1
               and d5.candidate_semantic_id == cand5)
    D.undo(d5)
    g5_undo = (d5.candidate_semantic_id == sem            # exact prior id
               and d5.semantic_revision == 2)             # revision increments
    # commit a fresh legal reconnect and confirm the content-checked promotion
    d5b = D.new_draft(prog, "dr")
    D.apply_edit(d5b, _eedit("e", 0, "ReconnectEdge", E_P0_R0, to=E_P1_R0))
    cb = d5b.candidate_semantic_id
    g5_mismatch = _raises(D.WRL_COMMIT_MISMATCH, lambda: D.commit_draft(
        d5b, _commit(d5b.semantic_revision, "sem-wrong")))
    res5 = D.commit_draft(d5b, _commit(d5b.semantic_revision, cb))
    g5_commit = (d5b.active_semantic_id == cb
                 and res5["sealed_artifact"].semantic_id == cb)
    rep(g5_stale and g5_idem and g5_undo and g5_mismatch and g5_commit, None,
        "G5) topology ops inherit the contract: stale base -> WRL_STALE_DRAFT; "
        "idempotent edit_id no-ops; undo restores the exact prior id (revision "
        "increments); commit needs the expected candidate then advances active")

    # ---- G6 an illegal rewire never commits ----------------------------------
    d6 = D.new_draft(prog, "dr")
    D.apply_edit(d6, _eedit("bad", 0, "AddEdge", E_P1_R0))   # overload r0
    g6_invalid = (d6.candidate_semantic_id is None
                  and d6.candidate_error is not None)
    g6_refuse = _raises(D.WRL_INVALID_CANDIDATE, lambda: D.commit_draft(
        d6, _commit(d6.semantic_revision, "anything")))
    D.undo(d6)
    g6_repair = (d6.candidate_error is None
                 and d6.candidate_semantic_id == sem)
    rep(g6_invalid and g6_refuse and g6_repair, None,
        "G6) an illegal rewire leaves the candidate invalid; commit refuses it "
        "WRL_INVALID_CANDIDATE; an undo repairs it")

    # ---- G7 native rewired-world gate: a pulser SWAP folds ic_ref == ic32 -----
    d7 = D.new_draft(prog, "dr")
    D.apply_edit(d7, _eedit("s1", 0, "ReconnectEdge", E_P0_R0, to=E_P1_R0))
    D.apply_edit(d7, _eedit("s2", 1, "ReconnectEdge", E_P1_D0, to=E_P0_D0))
    cand7 = d7.candidate_semantic_id
    g7_new = (d7.candidate_error is None and cand7 != sem
              and cand7 == _indep(d7))
    res7 = D.commit_draft(d7, _commit(d7.semantic_revision, cand7))
    sealed7 = res7["sealed_artifact"]
    view7 = P.plan_view(P.artifact_to_compile_plan_v1(sealed7))
    demo7 = SC.demo_scenario(sealed7.semantic_id)
    ifa7, scr7 = SC.scenario_to_script(demo7)
    got7 = _fold_films(view7, O.norm, ifa7, scr7)
    g7r = (g7_new and sealed7.semantic_id == cand7)
    g7n = None
    if not SKIP_NATIVE:
        g7n = (_fold_films(view7, O.native, ifa7, scr7) == got7)
    rep(g7r, g7n,
        "G7) committing a legal pulser SWAP (two ReconnectEdges) yields a NEW "
        "active SemanticArtifactID; a scenario bound to that rewired world folds "
        "through the plan/view path at ic_ref == ic32 (a rewired world is "
        "natively runnable)")

    # ---- G8 native identity round-trip: Remove then Add restores the demo id --
    d8 = D.new_draft(prog, "dr")
    D.apply_edit(d8, _eedit("rm", 0, "RemoveEdge", E_P0_R0))
    g8_left = (d8.candidate_semantic_id != sem)
    D.apply_edit(d8, _eedit("re", 1, "AddEdge", E_P0_R0))     # exact same wire
    g8_back = (d8.candidate_error is None
               and d8.candidate_semantic_id == sem)           # round-trip to demo
    res8 = D.commit_draft(d8, _commit(d8.semantic_revision, sem))
    sealed8 = res8["sealed_artifact"]
    view8 = P.plan_view(P.artifact_to_compile_plan_v1(sealed8))
    demo8 = SC.demo_scenario(sealed8.semantic_id)
    ifa8, scr8 = SC.scenario_to_script(demo8)
    ref_films = _fold_films(view8, O.norm, ("ob",), SB.SCRIPT)
    got8 = _fold_films(view8, O.norm, ifa8, scr8)
    g8r = (g8_left and g8_back and d8.active_semantic_id == sem
           and got8 == ref_films)
    g8n = None
    if not SKIP_NATIVE:
        g8n = (_fold_films(view8, O.native, ifa8, scr8) == got8)
    rep(g8r, g8n,
        "G8) RemoveEdge then AddEdge of the same wire round-trips to the EXACT "
        "demo SemanticArtifactID; the committed round-tripped world reproduces "
        "the golden SCRIPT films, ic_ref == ic32")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.4-2] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.4-2 adds AddEdge/RemoveEdge/ReconnectEdge over the SAME "
          "exact-CAS + candidate-sealing + explicit-commit + monotone-undo "
          "contract as v0.4-1, with NO new runtime construct. A topology op "
          "enforces only its own precondition; the seal is the sole judge of "
          "structural legality (unknown endpoint / illegal port pair / "
          "controller conflict), so an illegal rewire is an invalid-but-editable "
          "candidate that never commits. A committed rewire -- swapped OR round-"
          "tripped -- folds through the unchanged plan/view path at ic_ref == "
          "ic32; the round-trip returns to the EXACT demo SemanticArtifactID.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
