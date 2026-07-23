"""binding_run19.py -- v0.4-3 object lifecycle (Spinner Bench v0.4).

v0.4-1 made a world editable through a revisioned WorldDraft admitting
`SetObjectConfig`; v0.4-2 added the three TOPOLOGY ops. v0.4-3 completes the
frozen GraphEditV1 op set with the OBJECT-LIFECYCLE ops -- `AddObject` (carries
an `object` = {object_id, role, static_config}) and `RemoveObject` (carries a
`target` object_id) -- over the SAME exact-CAS + candidate-sealing +
explicit-commit + monotone-undo contract, still with NO new runtime construct. A
lifecycle op enforces only its OWN precondition (the object_id is / isn't
already present); structural legality of the RESULT (an unknown role, a bad
static_config, or an edge left DANGLING by a NON-cascading RemoveObject) is
DEFERRED to the seal, so an illegal lifecycle edit yields an invalid-but-editable
candidate, never a raise. RemoveObject is deliberately non-cascading: it drops
ONLY the object, so removing a still-wired node leaves a dangling edge the seal
rejects (WRL_UNKNOWN_ENDPOINT); the honest way to delete a connected node is to
RemoveEdge its wires first. This battery proves the ops + the contract they
inherit + two native gates (H1-H9):

  H1  AddObject: adding a disconnected `Orb` MOVES the candidate to exactly the
      independently-lowered world (a new SemanticArtifactID); re-adding an
      already-present object_id is refused WRL_BAD_EDIT (precondition, never
      reaching the seal).
  H2  RemoveObject NON-cascade: removing a still-wired node (`ob`) leaves its
      socket wire dangling, so the graph seals INVALID (candidate None + typed
      WRL_UNKNOWN_ENDPOINT) yet stays editable and undoes clean; removing an
      absent target is refused WRL_BAD_EDIT.
  H3  Honest deletion composes: RemoveEdge(sp->ob) then RemoveObject(ob) moves
      the candidate to exactly the independently-lowered world -- node AND wire
      both gone, valid.
  H4  validate_edit_v1 object-spec gate: AddObject with no `object`, an `object`
      missing a field, an `object` with an unknown field, and RemoveObject with
      no `target` all raise WRL_BAD_EDIT.
  H5  Seal-deferred role legality: AddObject with an unknown `role` seals INVALID
      (candidate None + typed WRL_UNSUPPORTED_FEATURE) yet stays editable and
      undoes clean -- role legality is the seal's job, not the op's.
  H6  The inherited draft contract holds for lifecycle ops: an object edit on a
      stale base -> WRL_STALE_DRAFT; an idempotent edit_id retry no-ops; undo
      restores the EXACT prior SemanticArtifactID while the revision increments;
      commit requires the expected candidate (WRL_COMMIT_MISMATCH) then advances
      active.
  H7  An invalid lifecycle edit never commits: a non-cascading RemoveObject that
      leaves a dangling edge keeps the candidate invalid, `commit_draft` refuses
      it WRL_INVALID_CANDIDATE, and an undo repairs the candidate back to valid.
  H8  Native added-world gate: committing a disconnected AddObject(`Orb`) yields
      a NEW active SemanticArtifactID, and a scenario bound to that world folds
      through the unchanged plan/view path at ic_ref == ic32 -- a world with an
      added node is natively runnable.
  H9  Native identity round-trip: unwire+RemoveObject(ob) then AddObject(ob)
      +rewire restores the EXACT original graph, so the candidate returns to the
      demo SemanticArtifactID; committing the round-tripped world leaves active
      == the demo id and reproduces the golden SCRIPT films byte-for-byte,
      ic_ref == ic32.

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

# the demo socket wire that binds the spinner to its orb
E_SP_OB = {"kind": "SocketControl", "src": "sp", "dst": "ob"}
# a disconnected orb, a legal standalone object
OBJ_ORBX = {"object_id": "orbX", "role": "Orb", "static_config": {}}
OBJ_OB = {"object_id": "ob", "role": "Orb", "static_config": {}}


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


def _aedit(edit_id, base, obj, draft_id="dr"):
    return {"edit_version": D.EDIT_VERSION, "edit_id": edit_id,
            "draft_id": draft_id, "base_revision": base,
            "operation": {"kind": "AddObject", "object": copy.deepcopy(obj)}}


def _redit(edit_id, base, target, draft_id="dr"):
    return {"edit_version": D.EDIT_VERSION, "edit_id": edit_id,
            "draft_id": draft_id, "base_revision": base,
            "operation": {"kind": "RemoveObject", "target": target}}


def _eedit(edit_id, base, kind, edge, draft_id="dr"):
    return {"edit_version": D.EDIT_VERSION, "edit_id": edit_id,
            "draft_id": draft_id, "base_revision": base,
            "operation": {"kind": kind, "edge": copy.deepcopy(edge)}}


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
    print("[BINDING wrl-v0.4-3] object lifecycle (H1-H9)")
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

    # ---- H1 AddObject: disconnected Orb moves candidate; dup id -> BAD --------
    d = D.new_draft(prog, "dr")
    D.apply_edit(d, _aedit("a1", 0, OBJ_ORBX))
    h1_move = (d.candidate_error is None
               and d.candidate_semantic_id != sem
               and d.candidate_semantic_id == _indep(d)
               and d.semantic_revision == 1)
    h1_dup = _raises(D.WRL_BAD_EDIT,
                     lambda: D.apply_edit(
                         d, _aedit("a2", d.semantic_revision, OBJ_ORBX)))
    rep(h1_move and h1_dup, None,
        "H1) AddObject(disconnected Orb) moves the candidate to exactly the "
        "independently-lowered world (a new id); re-adding an existing object_id "
        "-> WRL_BAD_EDIT (precondition, never reaches the seal)")

    # ---- H2 RemoveObject non-cascade: dangling -> invalid-but-editable -------
    d2 = D.new_draft(prog, "dr")
    D.apply_edit(d2, _redit("r1", 0, "ob"))            # ob is still wired by sp
    h2_invalid = (d2.candidate_semantic_id is None
                  and d2.candidate_error is not None
                  and "WRL_UNKNOWN_ENDPOINT" in d2.candidate_error
                  and d2.semantic_revision == 1)       # revision still moved
    D.undo(d2)                                          # repairs
    h2_repaired = (d2.candidate_semantic_id == sem
                   and d2.candidate_error is None)
    h2_missing = _raises(D.WRL_BAD_EDIT,
                         lambda: D.apply_edit(
                             d2, _redit("r2", d2.semantic_revision, "nope")))
    rep(h2_invalid and h2_repaired and h2_missing, None,
        "H2) RemoveObject of a still-wired node leaves a dangling edge -> seals "
        "invalid (WRL_UNKNOWN_ENDPOINT) yet stays editable + undoes clean; "
        "removing an absent target -> WRL_BAD_EDIT")

    # ---- H3 honest deletion composes: unwire then remove -> valid removal -----
    d3 = D.new_draft(prog, "dr")
    D.apply_edit(d3, _eedit("u1", 0, "RemoveEdge", E_SP_OB))
    D.apply_edit(d3, _redit("u2", 1, "ob"))
    h3 = (d3.candidate_error is None
          and d3.candidate_semantic_id != sem
          and d3.candidate_semantic_id == _indep(d3))
    rep(h3, None,
        "H3) RemoveEdge(sp->ob) then RemoveObject(ob) moves the candidate to "
        "exactly the independently-lowered world -- node AND wire both gone")

    # ---- H4 object-spec structural gate --------------------------------------
    h4_no_obj = _raises(D.WRL_BAD_EDIT, lambda: D.validate_edit_v1(
        {"edit_version": D.EDIT_VERSION, "edit_id": "x", "draft_id": "dr",
         "base_revision": 0, "operation": {"kind": "AddObject"}}))
    h4_bad_field = _raises(D.WRL_BAD_EDIT, lambda: D.validate_edit_v1(
        _aedit("x", 0, {"object_id": "q", "role": "Orb"})))       # no config
    h4_unknown = _raises(D.WRL_BAD_EDIT, lambda: D.validate_edit_v1(
        _aedit("x", 0, {"object_id": "q", "role": "Orb",
                        "static_config": {}, "z": 1})))
    h4_no_target = _raises(D.WRL_BAD_EDIT, lambda: D.validate_edit_v1(
        {"edit_version": D.EDIT_VERSION, "edit_id": "x", "draft_id": "dr",
         "base_revision": 0, "operation": {"kind": "RemoveObject"}}))
    rep(h4_no_obj and h4_bad_field and h4_unknown and h4_no_target, None,
        "H4) validate_edit_v1 rejects a missing/malformed/unknown-field "
        "AddObject `object` and a missing RemoveObject `target` -- all typed "
        "WRL_BAD_EDIT")

    # ---- H5 seal-deferred role legality --------------------------------------
    d5 = D.new_draft(prog, "dr")
    D.apply_edit(d5, _aedit("k1", 0,
                            {"object_id": "zz", "role": "Frob",
                             "static_config": {}}))
    h5_invalid = (d5.candidate_semantic_id is None
                  and d5.candidate_error is not None
                  and "WRL_UNSUPPORTED_FEATURE" in d5.candidate_error
                  and d5.semantic_revision == 1)
    D.undo(d5)
    h5_repaired = (d5.candidate_semantic_id == sem
                   and d5.candidate_error is None)
    rep(h5_invalid and h5_repaired, None,
        "H5) AddObject with an unknown role seals invalid "
        "(WRL_UNSUPPORTED_FEATURE) yet stays editable + undoes clean -- role "
        "legality is the seal's job, not the op's")

    # ---- H6 the inherited draft contract holds for lifecycle ops -------------
    d6 = D.new_draft(prog, "dr")
    D.apply_edit(d6, _aedit("e1", 0, OBJ_ORBX))
    cand6 = d6.candidate_semantic_id
    h6_stale = _raises(D.WRL_STALE_DRAFT, lambda: D.apply_edit(
        d6, _aedit("e2", 0, {"object_id": "orbY", "role": "Orb",
                             "static_config": {}})))     # stale base 0 (now 1)
    res_first = dict(d6._applied["e1"])
    res_retry = D.apply_edit(d6, _aedit("e1", 0, OBJ_ORBX))    # same edit_id
    h6_idem = (res_retry == res_first and d6.semantic_revision == 1
               and d6.candidate_semantic_id == cand6)
    D.undo(d6)
    h6_undo = (d6.candidate_semantic_id == sem            # exact prior id
               and d6.semantic_revision == 2)             # revision increments
    # commit a fresh legal AddObject and confirm the content-checked promotion
    d6b = D.new_draft(prog, "dr")
    D.apply_edit(d6b, _aedit("e", 0, OBJ_ORBX))
    cb = d6b.candidate_semantic_id
    h6_mismatch = _raises(D.WRL_COMMIT_MISMATCH, lambda: D.commit_draft(
        d6b, _commit(d6b.semantic_revision, "sem-wrong")))
    res6 = D.commit_draft(d6b, _commit(d6b.semantic_revision, cb))
    h6_commit = (d6b.active_semantic_id == cb
                 and res6["sealed_artifact"].semantic_id == cb)
    rep(h6_stale and h6_idem and h6_undo and h6_mismatch and h6_commit, None,
        "H6) lifecycle ops inherit the contract: stale base -> WRL_STALE_DRAFT; "
        "idempotent edit_id no-ops; undo restores the exact prior id (revision "
        "increments); commit needs the expected candidate then advances active")

    # ---- H7 an invalid lifecycle edit never commits --------------------------
    d7 = D.new_draft(prog, "dr")
    D.apply_edit(d7, _redit("bad", 0, "ob"))              # dangling socket wire
    h7_invalid = (d7.candidate_semantic_id is None
                  and d7.candidate_error is not None)
    h7_refuse = _raises(D.WRL_INVALID_CANDIDATE, lambda: D.commit_draft(
        d7, _commit(d7.semantic_revision, "anything")))
    D.undo(d7)
    h7_repair = (d7.candidate_error is None
                 and d7.candidate_semantic_id == sem)
    rep(h7_invalid and h7_refuse and h7_repair, None,
        "H7) a non-cascading RemoveObject that dangles an edge leaves the "
        "candidate invalid; commit refuses it WRL_INVALID_CANDIDATE; an undo "
        "repairs it")

    # ---- H8 native added-world gate: a disconnected Orb folds ic_ref == ic32 --
    d8 = D.new_draft(prog, "dr")
    D.apply_edit(d8, _aedit("add", 0, OBJ_ORBX))
    cand8 = d8.candidate_semantic_id
    h8_new = (d8.candidate_error is None and cand8 != sem
              and cand8 == _indep(d8))
    res8 = D.commit_draft(d8, _commit(d8.semantic_revision, cand8))
    sealed8 = res8["sealed_artifact"]
    view8 = P.plan_view(P.artifact_to_compile_plan_v1(sealed8))
    demo8 = SC.demo_scenario(sealed8.semantic_id)
    ifa8, scr8 = SC.scenario_to_script(demo8)
    got8 = _fold_films(view8, O.norm, ifa8, scr8)
    h8r = (h8_new and sealed8.semantic_id == cand8)
    h8n = None
    if not SKIP_NATIVE:
        h8n = (_fold_films(view8, O.native, ifa8, scr8) == got8)
    rep(h8r, h8n,
        "H8) committing a disconnected AddObject(Orb) yields a NEW active "
        "SemanticArtifactID; a scenario bound to that world folds through the "
        "plan/view path at ic_ref == ic32 (a world with an added node is "
        "natively runnable)")

    # ---- H9 native identity round-trip: remove+re-add node restores the id ----
    d9 = D.new_draft(prog, "dr")
    D.apply_edit(d9, _eedit("e1", 0, "RemoveEdge", E_SP_OB))
    D.apply_edit(d9, _redit("e2", 1, "ob"))
    h9_left = (d9.candidate_semantic_id != sem)
    D.apply_edit(d9, _aedit("e3", 2, OBJ_OB))            # re-add the same node
    D.apply_edit(d9, _eedit("e4", 3, "AddEdge", E_SP_OB))  # re-wire it
    h9_back = (d9.candidate_error is None
               and d9.candidate_semantic_id == sem)        # round-trip to demo
    res9 = D.commit_draft(d9, _commit(d9.semantic_revision, sem))
    sealed9 = res9["sealed_artifact"]
    view9 = P.plan_view(P.artifact_to_compile_plan_v1(sealed9))
    demo9 = SC.demo_scenario(sealed9.semantic_id)
    ifa9, scr9 = SC.scenario_to_script(demo9)
    ref_films = _fold_films(view9, O.norm, ("ob",), SB.SCRIPT)
    got9 = _fold_films(view9, O.norm, ifa9, scr9)
    h9r = (h9_left and h9_back and d9.active_semantic_id == sem
           and got9 == ref_films)
    h9n = None
    if not SKIP_NATIVE:
        h9n = (_fold_films(view9, O.native, ifa9, scr9) == got9)
    rep(h9r, h9n,
        "H9) unwire+RemoveObject(ob) then AddObject(ob)+rewire round-trips to "
        "the EXACT demo SemanticArtifactID; the committed round-tripped world "
        "reproduces the golden SCRIPT films, ic_ref == ic32")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.4-3] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.4-3 adds AddObject/RemoveObject over the SAME exact-CAS + "
          "candidate-sealing + explicit-commit + monotone-undo contract as "
          "v0.4-1/2, with NO new runtime construct. A lifecycle op enforces only "
          "its own precondition (object_id present / absent); the seal is the "
          "sole judge of structural legality (unknown role, bad config, dangling "
          "edge). RemoveObject is NON-cascading, so removing a wired node yields "
          "an invalid-but-editable candidate (WRL_UNKNOWN_ENDPOINT) that never "
          "commits -- the honest deletion is RemoveEdge then RemoveObject. A "
          "committed added-node world folds through the unchanged plan/view path "
          "at ic_ref == ic32; a remove+re-add round-trip returns to the EXACT "
          "demo SemanticArtifactID and reproduces the golden films.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
