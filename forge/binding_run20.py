"""binding_run20.py -- v0.4-4a canvas<->semantic binding (Spinner Bench v0.4).

v0.4-3 completed the GraphEditV1 op set on the semantic WorldDraft. v0.4-4a binds
the PRESENTATION surface (CanvasLayoutV1) to that draft through a `CanvasSession`
(`wrl_converge`), delivering the unambiguous CANVAS -> SEMANTIC -> TEXT direction
of the v0.4-4 convergence, over the existing identity + draft spine with NO new
runtime construct and NO new draft-contract construct. A SEMANTIC gesture is
translated 1:1 into a frozen GraphEditV1 and applied through the UNCHANGED
`wrl_draft.apply_edit` (all draft rules hold), then the layout is reconciled to
the working graph; a PRESENTATION gesture mutates ONLY the layout, proving
presentation is non-identity. `to_text()` serializes the draft to canonical WRL
Core that re-parses to the EXACT candidate id (canvas == text). This battery
proves the binding + native runnability (I1-I9):

  I1  A semantic `add_node` gesture emits the correct AddObject GraphEditV1, moves
      the candidate to exactly the independently-lowered world, and the layout
      gains a default-presentation node -- the candidate id is independent of the
      layout.
  I2  A presentation `set_presentation` gesture leaves the draft, the candidate
      id, and the revision UNTOUCHED, mutating only the node's presentation
      block.
  I3  Layout lockstep: after add/remove object + edge, the layout's node set ==
      the draft's object ids and its edge set == the draft's edge keys; a
      survivor keeps its presentation across an unrelated semantic edit.
  I4  Canvas -> text identity: `to_text()` re-parses (`parse_wrl_core` ->
      `lower_graph`) to the EXACT candidate SemanticArtifactID.
  I5  `gesture_to_edit` maps every semantic gesture to the right GraphEditV1 op
      (add_node->AddObject, remove_node->RemoveObject, add_wire->AddEdge,
      remove_wire->RemoveEdge, reconnect_wire->ReconnectEdge,
      set_config->SetObjectConfig); a presentation gesture is not semantic and a
      malformed gesture raises WRL_BAD_GESTURE.
  I6  Presentation is STRICTLY non-identity: injecting arbitrary x/y/color/
      collapsed into a node's presentation never changes the candidate id, and
      the layout still passes `validate_layout_v1`.
  I7  The inherited draft contract holds through the session: an illegal semantic
      gesture (removing a still-wired node) seals an invalid-but-editable
      candidate (WRL_UNKNOWN_ENDPOINT) yet the layout reconciles to the working
      graph; a session `undo` restores the EXACT prior candidate id AND the exact
      prior presentation; a stale pinned base_revision -> WRL_STALE_DRAFT.
  I8  Native added-world gate: committing a session that added a disconnected Orb
      yields a NEW active SemanticArtifactID and a scenario bound to it folds
      through the plan/view path at ic_ref == ic32.
  I9  Native identity gate: committing a session that made ONLY presentation
      gestures leaves active == the demo SemanticArtifactID and reproduces the
      golden SCRIPT films byte-for-byte, ic_ref == ic32 -- presentation never
      perturbs the runnable identity.

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
import wrl_scenario as SC
import wrl_draft as D
import spinner_bench as SB
from admit import film_hash_v7
from fixture import init_state_v6, state_to_film_args_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

E_SP_OB = {"kind": "SocketControl", "src": "sp", "dst": "ob"}
E_P0_R0 = {"kind": "SignalWire", "src": "p0", "dst": "r0"}
OBJ_ORBX = {"object_id": "orbX", "role": "Orb", "static_config": {}}


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


def _g(gesture_id, kind, **kw):
    d = {"gesture_version": CG.GESTURE_VERSION, "gesture_id": gesture_id,
         "kind": kind}
    d.update(kw)
    return d


def _commit(base_revision, expected, draft_id="dr"):
    return {"commit_version": D.COMMIT_VERSION, "draft_id": draft_id,
            "base_revision": base_revision,
            "expected_candidate_semantic_id": expected}


def _indep(session):
    return W.lower_graph(
        D._graph_from(copy.deepcopy(session.draft.objects),
                      copy.deepcopy(session.draft.edges),
                      session.draft.profile_id)).semantic_artifact_id


def _raises(code, thunk):
    try:
        thunk()
        return False
    except WC.WrlValidationError as e:
        return e.code == code
    except WC.WrlUnsupported as e:
        return getattr(e, "code", None) == code


def main():
    print("[BINDING wrl-v0.4-4a] canvas<->semantic binding (I1-I9)")
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

    # ---- I1 semantic add_node emits AddObject, moves candidate, layout node ---
    s = CG.new_session(prog, "dr")
    i1_start = (s.candidate_semantic_id == sem and s.semantic_revision == 0
                and len(s.layout["nodes"]) == 6 and len(s.layout["edges"]) == 4)
    r = s.apply_gesture(_g("a1", "add_node", object=OBJ_ORBX))
    i1_edit = (r["edit"]["operation"]["kind"] == "AddObject")
    i1_move = (r["candidate_valid"] and r["candidate_semantic_id"] != sem
               and r["candidate_semantic_id"] == _indep(s))
    i1_layout = (len(s.layout["nodes"]) == 7
                 and any(n["object_id"] == "orbX" for n in s.layout["nodes"]))
    rep(i1_start and i1_edit and i1_move and i1_layout, None,
        "I1) a semantic add_node emits the correct AddObject GraphEditV1, moves "
        "the candidate to exactly the independently-lowered world, and the layout "
        "gains a default-presentation node")

    # ---- I2 presentation gesture leaves the semantic side untouched ----------
    cand2 = s.candidate_semantic_id
    rev2 = s.semantic_revision
    r = s.apply_gesture(_g("p1", "set_presentation", object_id="orbX",
                           presentation={"x": 999, "y": 111, "color": "#abc"}))
    px = [n for n in s.layout["nodes"] if n["object_id"] == "orbX"][0]
    i2 = (r["gesture"] == "presentation"
          and s.candidate_semantic_id == cand2
          and s.semantic_revision == rev2
          and px["presentation"]["x"] == 999
          and px["presentation"]["color"] == "#abc")
    rep(i2, None,
        "I2) a presentation set_presentation gesture leaves the draft, candidate "
        "id, and revision untouched, mutating only the node's presentation")

    # ---- I3 layout lockstep + survivor presentation persistence --------------
    s3 = CG.new_session(prog, "dr")
    s3.apply_gesture(_g("mv", "set_presentation", object_id="sp",
                        presentation={"x": 1234}))
    s3.apply_gesture(_g("add", "add_node", object=OBJ_ORBX))
    s3.apply_gesture(_g("rm", "remove_wire", edge=E_P0_R0))
    lnodes = sorted(n["object_id"] for n in s3.layout["nodes"])
    dnodes = sorted(o["object_id"] for o in s3.draft.objects)
    ledges = sorted(e["edge_key"] for e in s3.layout["edges"])
    dedges = sorted(CV.edge_key(e["kind"], e["src"], e["dst"])
                    for e in s3.draft.edges)
    spx = [n for n in s3.layout["nodes"]
           if n["object_id"] == "sp"][0]["presentation"]["x"]
    i3 = (lnodes == dnodes and ledges == dedges and spx == 1234)
    rep(i3, None,
        "I3) layout lockstep: the layout node/edge sets exactly match the "
        "draft's objects/edge-keys after add/remove; a survivor keeps its "
        "presentation across an unrelated semantic edit")

    # ---- I4 canvas -> text identity round-trip -------------------------------
    txt = s3.to_text()
    reparsed = W.lower_graph(W.parse_wrl_core(txt)).semantic_artifact_id
    i4 = (reparsed == s3.candidate_semantic_id)
    rep(i4, None,
        "I4) to_text() serializes the draft to canonical WRL Core that re-parses "
        "to the EXACT candidate SemanticArtifactID (canvas == text)")

    # ---- I5 gesture_to_edit op mapping + gesture typing ----------------------
    maps = [("add_node", {"object": OBJ_ORBX}, "AddObject"),
            ("remove_node", {"target": "ob"}, "RemoveObject"),
            ("add_wire", {"edge": E_P0_R0}, "AddEdge"),
            ("remove_wire", {"edge": E_P0_R0}, "RemoveEdge"),
            ("reconnect_wire",
             {"edge": E_P0_R0, "to": {"kind": "SignalWire", "src": "p1",
                                      "dst": "r0"}}, "ReconnectEdge"),
            ("set_config", {"target": "sp", "static_config": {}},
             "SetObjectConfig")]
    i5_map = all(
        CG.gesture_to_edit(_g("x", k, **kw), 0, "dr")["operation"]["kind"] == op
        for k, kw, op in maps)
    i5_pres_not_semantic = (not CG.is_semantic(
        _g("x", "set_presentation", object_id="sp", presentation={})))
    i5_bad = _raises(CG.WRL_BAD_GESTURE, lambda: CG.gesture_to_edit(
        _g("x", "add_node"), 0, "dr"))          # add_node with no object
    i5_bad_kind = _raises(CG.WRL_BAD_GESTURE, lambda: CG.gesture_to_edit(
        _g("x", "set_presentation", object_id="sp", presentation={}), 0, "dr"))
    rep(i5_map and i5_pres_not_semantic and i5_bad and i5_bad_kind, None,
        "I5) gesture_to_edit maps every semantic gesture to the right op; a "
        "presentation gesture is not semantic; a malformed/presentation gesture "
        "-> WRL_BAD_GESTURE")

    # ---- I6 presentation is STRICTLY non-identity ----------------------------
    s6 = CG.new_session(prog, "dr")
    base6 = s6.candidate_semantic_id
    for oid, patch in [("p0", {"x": -5}), ("sp", {"color": "#000"}),
                       ("ob", {"collapsed": True, "y": 4242})]:
        s6.apply_gesture(_g("z" + oid, "set_presentation", object_id=oid,
                            presentation=patch))
    i6 = (s6.candidate_semantic_id == base6
          and CV.validate_layout_v1(copy.deepcopy(s6.layout)) is not None)
    rep(i6, None,
        "I6) presentation is strictly non-identity: injecting arbitrary "
        "x/y/color/collapsed never changes the candidate id, and the layout "
        "still passes validate_layout_v1")

    # ---- I7 inherited contract: invalid gesture + undo + stale base ----------
    s7 = CG.new_session(prog, "dr")
    s7.apply_gesture(_g("mv", "set_presentation", object_id="ob",
                        presentation={"x": 77}))
    r = s7.apply_gesture(_g("rm", "remove_node", target="ob"))  # still wired
    i7_invalid = (not r["candidate_valid"]
                  and "WRL_UNKNOWN_ENDPOINT" in (r["candidate_error"] or "")
                  and len(s7.layout["nodes"]) == 5      # working graph, node gone
                  and len(s7.layout["edges"]) == 4)     # dangling wire kept
    s7.undo()
    obx = [n for n in s7.layout["nodes"] if n["object_id"] == "ob"]
    i7_undo = (s7.candidate_semantic_id == sem and s7.candidate_error is None
               and len(obx) == 1 and obx[0]["presentation"]["x"] == 77)
    i7_stale = _raises(D.WRL_STALE_DRAFT, lambda: s7.apply_gesture(
        _g("st", "add_node", object=OBJ_ORBX, base_revision=0)))  # rev now 2
    rep(i7_invalid and i7_undo and i7_stale, None,
        "I7) inherited contract through the session: an illegal remove_node "
        "seals invalid (WRL_UNKNOWN_ENDPOINT) yet the layout reconciles; undo "
        "restores the exact prior candidate AND presentation; a stale pinned "
        "base_revision -> WRL_STALE_DRAFT")

    # ---- I8 native added-world gate ------------------------------------------
    s8 = CG.new_session(prog, "dr")
    s8.apply_gesture(_g("add", "add_node", object=OBJ_ORBX))
    cand8 = s8.candidate_semantic_id
    i8_new = (s8.candidate_error is None and cand8 != sem and cand8 == _indep(s8))
    res8 = s8.commit(_commit(s8.semantic_revision, cand8))
    sealed8 = res8["sealed_artifact"]
    view8 = P.plan_view(P.artifact_to_compile_plan_v1(sealed8))
    demo8 = SC.demo_scenario(sealed8.semantic_id)
    ifa8, scr8 = SC.scenario_to_script(demo8)
    got8 = _fold_films(view8, O.norm, ifa8, scr8)
    i8r = (i8_new and sealed8.semantic_id == cand8)
    i8n = None
    if not SKIP_NATIVE:
        i8n = (_fold_films(view8, O.native, ifa8, scr8) == got8)
    rep(i8r, i8n,
        "I8) committing a session that added a disconnected Orb yields a NEW "
        "active SemanticArtifactID; a scenario bound to it folds ic_ref == ic32")

    # ---- I9 native identity gate: presentation-only session == demo id -------
    s9 = CG.new_session(prog, "dr")
    s9.apply_gesture(_g("m1", "set_presentation", object_id="ob",
                        presentation={"x": 7, "color": "#123"}))
    s9.apply_gesture(_g("m2", "set_presentation", object_id="sp",
                        presentation={"y": 9}))
    cand9 = s9.candidate_semantic_id
    i9_same = (cand9 == sem)
    res9 = s9.commit(_commit(s9.semantic_revision, cand9))
    sealed9 = res9["sealed_artifact"]
    view9 = P.plan_view(P.artifact_to_compile_plan_v1(sealed9))
    demo9 = SC.demo_scenario(sealed9.semantic_id)
    ifa9, scr9 = SC.scenario_to_script(demo9)
    ref_films = _fold_films(view9, O.norm, ("ob",), SB.SCRIPT)
    got9 = _fold_films(view9, O.norm, ifa9, scr9)
    i9r = (i9_same and s9.draft.active_semantic_id == sem
           and got9 == ref_films)
    i9n = None
    if not SKIP_NATIVE:
        i9n = (_fold_films(view9, O.native, ifa9, scr9) == got9)
    rep(i9r, i9n,
        "I9) a session that made ONLY presentation gestures commits with active "
        "== the demo SemanticArtifactID and reproduces the golden SCRIPT films, "
        "ic_ref == ic32 (presentation never perturbs the runnable identity)")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.4-4a] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.4-4a binds CanvasLayoutV1 (presentation) to WorldDraftV1 "
          "(semantic) through a CanvasSession, delivering the CANVAS -> SEMANTIC "
          "-> TEXT direction of the v0.4-4 convergence with NO new runtime "
          "construct and NO new draft-contract construct. A semantic gesture is "
          "translated 1:1 to a frozen GraphEditV1 and applied through the "
          "unchanged apply_edit; a presentation gesture touches ONLY the layout "
          "(the candidate id comes purely from the draft). to_text() re-parses "
          "to the exact candidate id (canvas == text). DEFERRED to v0.4-4b (a "
          "contract fork raised to GPT-5.6): the text -> canvas reconciliation "
          "of a free-form multi-change text edit -- decompose into a SEQUENCE of "
          "single-op GraphEditV1 edits (existing constructs, non-atomic, per-op "
          "undo) vs a single atomic re-base edit (cleaner UX, a NEW draft-contract "
          "op). That awaits a ruling before apply_text is built.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
