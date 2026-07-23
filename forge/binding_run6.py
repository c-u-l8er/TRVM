"""binding_run6.py -- Phase 3C: canvas <-> text <-> runtime isomorphism.

GPT-5.6's Phase 3C ruling: build CanvasGraphV1 as presentation metadata AROUND
the canonical WRL graph, and prove text, bootstrap and canvas surfaces converge
on the SAME artifact bytes and runtime films -- while presentation NEVER enters
the SemanticArtifactID. This battery is the convergence proof (V1-V12):

  V1  text -> graph -> canvas -> graph -> ir retains the SemanticArtifactID
      (and the artifact bytes, and the canonical claim batches).
  V2  canvas -> graph -> WRL text -> graph -> ir retains the SemanticArtifactID.
  V3  MOVING a node (presentation x/y) does NOT change the identity.
  V4  changing a connection's LINE GEOMETRY does NOT change the identity.
  V5  RECOLORING a node/edge does NOT change the identity.
  V6  changing a Spinner's ROTOR (static_config) DOES change the identity.
  V7  RECONNECTING an edge (a semantic endpoint) DOES change the identity.
  V8  a duplicate Orb controller in the canvas is a TYPED rejection
      (WRL_CONTROLLER_CONFLICT) -- the same law the text surface enforces.
  V9  canvas and text agree on the FROZEN port signature: a canvas derives its
      ports from the role registry (a bogus/absent presentation or injected
      `ports` key is structurally inert), while a WRL text with the WRONG ports
      is WRL_PORT_SIGNATURE. Corrupting/deleting the entire presentation block
      cannot override the semantic identity.
  V10 bootstrap text, WRL process notation, and canvas all lower to IDENTICAL
      artifact bytes (three-surface equivalence).
  V11 every presented canvas node/connection is anchored to a real object id in
      the artifact -- no orphan presentation, no dangling visual endpoint.
  V12 ic_ref == ic32 == golden over the whole trajectory, lowered FROM A CANVAS
      (the runtime film is surface-independent), reusing the proven fold harness.

V12 reuses the 3b.5f-2b fold harness (binding_run3o); the canvas-lowered
fixture equals its mkfx(8,4).
"""
import os
import sys
import copy
import time

sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import admit as AD
import wrl_ir as W
import wrl_canonical as WC
import wrl_canvas as CV
import binding_run3o as O
import binding_run5 as B5
from admit import mk_claim  # noqa: F401 (parity with the slice-2 harness)
from fixture import init_state_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

CORE_SRC = B5.CORE_SRC
BOOTSTRAP_SRC = B5.BOOTSTRAP_SRC


def _sid(prog):
    return WC.semantic_artifact_id(prog.artifact)


def _core_prog():
    return W.lower_program(CORE_SRC, W.parse_wrl_core)


# ------------------------------------------------------------------- checks
def v1_text_to_canvas(base):
    sid0 = _sid(base)
    canvas = CV.graph_to_canvas(base.graph)
    prog2 = CV.lower_canvas(canvas)
    assert _sid(prog2) == sid0, "text->canvas->graph changed the identity"
    assert (WC.serialize_artifact(base.artifact)
            == WC.serialize_artifact(prog2.artifact)), "artifact bytes differ"
    assert base.graph.batches == prog2.graph.batches, "claim batches differ"
    print("  V1 text->graph->canvas->graph retains SemanticArtifactID  OK")
    return sid0, canvas


def v2_canvas_to_text(sid0, base, canvas):
    g = CV.canvas_to_graph(canvas)
    text = CV.graph_to_wrl_core(g)
    prog3 = W.lower_program(text, W.parse_wrl_core)
    assert _sid(prog3) == sid0, "canvas->graph->WRL text->graph changed identity"
    assert base.graph.batches == prog3.graph.batches, "claim batches differ"
    print("  V2 canvas->graph->WRL text->graph retains SemanticArtifactID  OK")


def v3_move_node(sid0, canvas):
    c = copy.deepcopy(canvas)
    c["nodes"][0]["presentation"]["x"] += 999
    c["nodes"][0]["presentation"]["y"] -= 37
    assert _sid(CV.lower_canvas(c)) == sid0, "moving a node moved the identity"
    print("  V3 moving a node (x/y) does NOT change the identity  OK")


def v4_line_geometry(sid0, canvas):
    c = copy.deepcopy(canvas)
    p = c["connections"][0]["presentation"]
    p["control_points"] = [[10, 10], [20, 30], [40, 5]]
    p["line_length"] = 12345
    assert _sid(CV.lower_canvas(c)) == sid0, "line geometry moved the identity"
    print("  V4 changing a connection's line geometry does NOT change it  OK")


def v5_recolor(sid0, canvas):
    c = copy.deepcopy(canvas)
    c["nodes"][0]["presentation"]["color"] = "#000000"
    c["connections"][0]["presentation"]["paint"] = "#ffffff"
    assert _sid(CV.lower_canvas(c)) == sid0, "recoloring moved the identity"
    print("  V5 recoloring a node/edge does NOT change the identity  OK")


def v6_rotor_changes(sid0, canvas):
    c = copy.deepcopy(canvas)
    hit = False
    for n in c["nodes"]:
        if n["role"] == "Spinner":
            n["static_config"]["rotor"] = [16, 0, 50, 0]
            hit = True
    assert hit, "no spinner in the fixture"
    assert _sid(CV.lower_canvas(c)) != sid0, "a rotor change did NOT move it"
    print("  V6 changing a Spinner rotor DOES change the identity  OK")


def v7_reconnect():
    # a small valid two-door topology so a reconnect stays legal (a door has no
    # merge/controller constraint) while the endpoint change moves the identity.
    src = ("profile forge.world.core.v1\nperiods 0\n"
           "[pulser:p0](mode=periodic, period=2, phase=0){sig_out}\n"
           "[door:d0]{sig_in}\n[door:d1]{sig_in}\n"
           "[pulser:p0] --sig--> [door:d0]\n")
    prog = W.lower_program(src, W.parse_wrl_core)
    sid0 = _sid(prog)
    c = CV.graph_to_canvas(prog.graph)
    for conn in c["connections"]:
        if conn["kind"] == "SignalWire":
            conn["dst"] = "d1"          # re-point the wire onto the other door
    assert _sid(CV.lower_canvas(c)) != sid0, "a reconnect did NOT move it"
    print("  V7 reconnecting an edge DOES change the identity  OK")


def v8_dup_controller(canvas):
    c = copy.deepcopy(canvas)
    c["nodes"].append({"object_id": "sp2", "role": "Spinner",
                       "static_config": {"w": 8, "n": 4, "rotor": [16, 0, 0, 0],
                                         "configurable": False},
                       "presentation": CV._node_presentation(9, "Spinner")})
    c["connections"].append({"kind": "SocketControl", "src": "sp2", "dst": "ob",
                             "presentation": CV._conn_presentation(
                                 "SocketControl")})
    try:
        CV.lower_canvas(c)
    except W.WrlValidationError as ex:
        assert ex.code == WC.WRL_CONTROLLER_CONFLICT, ex.code
        print("  V8 duplicate Orb controller -> %s  OK" % ex.code)
        return
    raise AssertionError("a second orb controller was not rejected")


def v9_ports_and_inertness(sid0, canvas):
    # (a) corrupt/delete the WHOLE presentation block (arbitrary garbage under
    #     the OPEN `presentation` key) -- canvas_to_graph reads none of it, so
    #     identity is unchanged.
    c = copy.deepcopy(canvas)
    for n in c["nodes"]:
        n["presentation"] = {"x": "NaN", "garbage": [1, 2, 3], "ports": ["x"]}
    del c["connections"][0]["presentation"]
    assert _sid(CV.lower_canvas(c)) == sid0, \
        "presentation leaked into the semantic identity"
    # (a2) 3D-0 strictness: a bogus SEMANTIC key (a top-level `ports` on a node
    #      or connection) is no longer silently ignored -- it is a TYPED
    #      rejection, so the semantic boundary is ENFORCED, not conventional.
    for inject in (lambda cc: cc["nodes"][0].__setitem__("ports", ["nope"]),
                   lambda cc: cc["connections"][0].__setitem__("ports", ["no"])):
        bad_c = copy.deepcopy(canvas)
        inject(bad_c)
        try:
            CV.lower_canvas(bad_c)
        except W.WrlValidationError as ex:
            assert ex.code == WC.WRL_UNSUPPORTED_FEATURE, ex.code
        else:
            raise AssertionError("a bogus top-level semantic key was accepted")
    # (b) the emitted WRL text ports are the SAME frozen signature the canvas
    #     derives; a text with the WRONG ports is a typed rejection.
    text = CV.graph_to_wrl_core(CV.canvas_to_graph(canvas))
    assert _sid(W.lower_program(text, W.parse_wrl_core)) == sid0
    bad = text.replace("[orb:ob]{pose}", "[orb:ob]{sig_in}")
    try:
        W.lower_program(bad, W.parse_wrl_core)
    except W.WrlValidationError as ex:
        assert ex.code == WC.WRL_PORT_SIGNATURE, ex.code
    else:
        raise AssertionError("wrong text ports were not rejected")
    print("  V9 canvas derives / text checks the SAME frozen port signature; "
          "presentation is semantically inert  OK")


def v10_three_surface(sid0, canvas):
    boot = W.lower_program(BOOTSTRAP_SRC)
    core = W.lower_program(CORE_SRC, W.parse_wrl_core)
    canv = CV.lower_canvas(canvas)
    b = WC.serialize_artifact(boot.artifact)
    assert b == WC.serialize_artifact(core.artifact) == \
        WC.serialize_artifact(canv.artifact), "three surfaces differ in bytes"
    assert WC.semantic_artifact_id(boot.artifact) == sid0
    print("  V10 bootstrap / WRL text / canvas lower to IDENTICAL bytes  OK")


def v11_provenance(canvas):
    prog = CV.lower_canvas(canvas)
    node_ids = {n["object_id"] for n in canvas["nodes"]}
    art_ids = {o["object_id"] for o in prog.artifact["objects"]}
    assert node_ids == art_ids, "canvas nodes are not exactly the objects"
    for conn in canvas["connections"]:
        assert conn["src"] in node_ids and conn["dst"] in node_ids, \
            "a connection references an undeclared endpoint"
    print("  V11 every presented node/connection is anchored to a real "
          "object id  OK")


def v12_trajectory(canvas):
    prog = CV.lower_canvas(canvas)
    fx = prog.fixture
    assert B5._fx_sig(fx) == B5._fx_sig(O.FX), \
        "canvas-lowered fixture must match mkfx(8,4)"
    batches = B5._batches_from_program(prog)

    world0 = init_state_v6(O.FX)
    world0["fault_ob"] = 1
    claim0 = AD.init_claimstate()
    gold = O._golden_traj(claim0, world0, batches, epoch0=1)

    import admit_ic as X
    from compiler import enc_state_v6
    fv0 = X.enc_factvec([], O.CAP)
    rv0 = X.enc_factvec([], O.RCAP)
    term = O._build_fold(batches, fv0, rv0, enc_state_v6(O.FX, world0))
    K = len(batches)

    dec_ref = O._decode_fold(O.norm(term), K)
    assert O._traj_summary(dec_ref) == O._golden_summary(gold), \
        "ref trajectory != golden (canvas surface)"
    claims_ref = O._project_claims(dec_ref, epoch0=1)
    for e in range(K):
        f_ref = O._film(dec_ref[e][0], claims_ref[e], e + 1)
        f_g = O._film(gold[e][0], gold[e][1], e + 1)
        assert f_ref == f_g, "Film v0.7 mismatch (canvas) epoch %d" % (e + 1)

    tag = "ref"
    if not SKIP_NATIVE:
        dec_nat = O._decode_fold(O.native(term), K)
        assert O._traj_summary(dec_nat) == O._traj_summary(dec_ref), \
            "native trajectory != ref (canvas surface)"
        claims_nat = O._project_claims(dec_nat, epoch0=1)
        for e in range(K):
            f_nat = O._film(dec_nat[e][0], claims_nat[e], e + 1)
            f_g = O._film(gold[e][0], gold[e][1], e + 1)
            assert f_nat == f_g, "native Film mismatch (canvas) epoch %d" \
                % (e + 1)
        tag = "ref==native"
    print("  V12 ic_ref==ic32==golden trajectory FROM A CANVAS (%s), %d "
          "epochs  OK" % (tag, K))


def main():
    print("[BINDING wrl-3c] canvas <-> text <-> runtime isomorphism")
    t0 = time.time()
    base = _core_prog()
    sid0, canvas = v1_text_to_canvas(base)
    v2_canvas_to_text(sid0, base, canvas)
    v3_move_node(sid0, canvas)
    v4_line_geometry(sid0, canvas)
    v5_recolor(sid0, canvas)
    v6_rotor_changes(sid0, canvas)
    v7_reconnect()
    v8_dup_controller(canvas)
    v9_ports_and_inertness(sid0, canvas)
    v10_three_surface(sid0, canvas)
    v11_provenance(canvas)
    v12_trajectory(canvas)
    verdict = "PASS_REF" if SKIP_NATIVE else "PASS_REF_AND_NATIVE"
    print("[BINDING wrl-3c] %s  (%.0fs)" % (verdict, time.time() - t0))


if __name__ == "__main__":
    main()
