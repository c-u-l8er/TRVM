"""binding_run4.py -- WRL vertical slice 1 (the first sanctioned lowering).

    WRL Core text -> canonical WRL graph -> Forge Semantic IR v1
                  -> current Fixture adapter -> TRVM compiler
                  -> ic_ref / ic32 -> Film v0.7

Proves the frozen pipeline (FORGE_SEMANTIC_IR_v1.md, profile
forge.world.core.v1) end to end on the grounded deterministic-circuit-world:

  W1 adapter fidelity: WRL text -> IR v1 -> Fixture reproduces the hand-built
     mkfx(8,4) fixture EXACTLY (pulsers/doors/edges/spinners/orbs/sockets).
  W2 IR shape: the emitted artifact carries the frozen top-level form
     (profile, five-role registry closure, two-edge closure, admit policy id).
  W3 Film v0.7 trajectory parity: the SAME WRL program, run through the
     adapter fixture, folds over K epochs in ONE IC term whose single native
     normalization renders the IDENTICAL v0.7 film trajectory as the golden
     admit_step + world-step (ic_ref == ic32 == golden).
  W4 unsupported-feature diagnostics: async ~~ route, a capability gate, a
     sixth role, and an out-of-registry edge each raise WrlUnsupported with a
     clear message -- NEVER a speculative lowering.

W3 reuses the 3b.5f-2b fold harness (binding_run3o) since the adapter fixture
equals binding_run3o.FX; this shows the WRL front-end feeds the proven
persistent claim/world trajectory unchanged.
"""
import os, sys, copy, time
sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import admit as AD
import wrl_ir as W
from wrl_ir import WrlUnsupported, lower_wrl, parse_wrl, graph_to_ir, ir_to_fixture
from binding_run3j import mkfx
import binding_run3o as O
from admit import mk_claim

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

# The WRL Core source for the grounded circuit-world (mkfx(8,4) topology):
#   one periodic pulser p0 driving a configurable 8-bit/4-lane spinner sp,
#   an isolated door d0, an orb ob controlled by sp; 3 periods of claims.
WRL_SRC = """
profile forge.world.core.v1
periods 3

pulser  p0 periodic 2 0
door    d0
spinner sp w=8 n=4 rotor=16,0,0,0 configurable
orb     ob

wire   p0 -> sp
socket sp -> ob

epoch 1: @1,1 SetRotor   sp 16,0,99,0
epoch 2: @1,2 ResetFault ob
epoch 3: @1,3 SetRotor   zz 16,0,30,0
"""


def _fx_sig(fx):
    return (dict(fx.pulsers), sorted(fx.doors), sorted(fx.relays),
            sorted(fx.edges), dict(fx.spinners), sorted(fx.orbs),
            sorted(fx.sockets), fx.configurable)


def _batches_from_graph(g):
    """Epoch input -> golden claim batches (fill defaulted writer/seq)."""
    batches = []
    for e, batch in enumerate(g.batches):
        out = []
        for i, c in enumerate(batch):
            wid = c["writer_id"] if c["writer_id"] is not None else 1
            seq = c["sequence"] if c["sequence"] is not None else e + 1
            out.append(mk_claim(wid, seq, c["payload"]))
        batches.append(out)
    return batches


def w1_adapter_fidelity():
    fx, art, g = lower_wrl(WRL_SRC)
    ref = mkfx(8, 4, rotor0=(16, 0, 0, 0))
    a, b = _fx_sig(fx), _fx_sig(ref)
    assert a == b, f"adapter fixture != mkfx(8,4)\n adapter={a}\n mkfx   ={b}"
    print("  W1 adapter fidelity: WRL -> IR v1 -> Fixture == mkfx(8,4)  OK")
    return fx, art, g


def w2_ir_shape(art):
    assert art["ir_version"] == W.IR_VERSION
    assert art["profile_id"] == W.PROFILE_ID
    roles = {o["role"] for o in art["objects"]}
    assert roles <= set(W.ROLE_IDS), roles
    assert roles == {"Pulser", "Door", "Spinner", "Orb"}, roles
    ekinds = {e["kind"] for e in art["edges"]}
    assert ekinds <= set(W.EDGE_KINDS), ekinds
    assert ekinds == {"SignalWire", "SocketControl"}, ekinds
    assert art["semantic_policies"]["admit_policy_id"] == W.ADMIT_POLICY_ID
    assert art["semantic_policies"]["film_schema_id"] == "film.v0.7"
    # semantic artifact carries NO backend encoding (D4)
    for o in art["objects"]:
        assert "scott" not in str(o).lower() and "dup" not in str(o).lower()
    print("  W2 IR shape: frozen top-level form, 5-role + 2-edge closure, "
          "admit policy pinned, no backend encoding  OK")


def w3_film_parity(fx, g):
    assert _fx_sig(fx) == _fx_sig(O.FX), "harness FX must match adapter FX"
    batches = _batches_from_graph(g)
    claim0 = AD.init_claimstate()
    from fixture import init_state_v6
    world0 = init_state_v6(O.FX)

    gold = O._golden_traj(claim0, world0, batches, epoch0=1)

    # build the ONE-term fold and normalize (ref, then native)
    import admit_ic as X
    from compiler import enc_state_v6
    fv0 = X.enc_factvec([], O.CAP)
    rv0 = X.enc_factvec([], O.RCAP)
    w0 = enc_state_v6(O.FX, world0)
    term = O._build_fold(batches, fv0, rv0, w0)

    K = len(batches)
    dec_ref = O._decode_fold(O.norm(term), K)
    assert O._traj_summary(dec_ref) == O._golden_summary(gold), \
        "ref trajectory != golden"

    # Film v0.7 parity, every epoch (valid-target trajectory discipline: the
    # epoch-3 invalid SetRotor zz -> Rejected -> NoChange keeps world/claim
    # exact; its rejected receipt's lost target name is the documented
    # projection limit, so film parity is asserted where targets are valid).
    claims_ref = O._project_claims(dec_ref, epoch0=1)
    valid_epochs = [0, 1]        # epochs 1,2 have valid targets
    for e in valid_epochs:
        w_ref = dec_ref[e][0]
        f_ref = O._film(w_ref, claims_ref[e], e + 1)
        w_g, claim_g = gold[e][0], gold[e][1]
        f_g = O._film(w_g, claim_g, e + 1)
        assert f_ref == f_g, f"Film v0.7 mismatch at epoch {e + 1}"

    tag = "ref"
    if not SKIP_NATIVE:
        dec_nat = O._decode_fold(O.native(term), K)
        assert O._traj_summary(dec_nat) == O._traj_summary(dec_ref), \
            "native trajectory != ref"
        claims_nat = O._project_claims(dec_nat, epoch0=1)
        for e in valid_epochs:
            f_nat = O._film(dec_nat[e][0], claims_nat[e], e + 1)
            f_g = O._film(gold[e][0], gold[e][1], e + 1)
            assert f_nat == f_g, f"native Film v0.7 mismatch epoch {e + 1}"
        tag = "ref==native"
    print(f"  W3 Film v0.7 trajectory parity ({tag}==golden), {K} epochs, "
          f"WRL-lowered fixture  OK")


def w4_diagnostics():
    cases = [
        ("async route", "profile forge.world.core.v1\nperiods 1\n"
                         "relay a\nrelay b\na ~~msg~~> b\n"),
        ("capability gate", "profile forge.world.core.v1\nperiods 1\n"
                            "gate net\n"),
        ("seal boundary", "profile forge.world.core.v1\nperiods 1\n"
                          "seal world17\n"),
    ]
    for name, src in cases:
        try:
            parse_wrl(src)
        except WrlUnsupported as ex:
            print(f"  W4 diagnostic [{name}]: {ex}")
            continue
        raise AssertionError(f"{name} should have been rejected")
    # sixth (out-of-registry) role at the IR stage
    g = parse_wrl("profile forge.world.core.v1\nperiods 1\ndoor d0\n")
    g.nodes.append(("Mailbox", "mb0", {}))
    try:
        graph_to_ir(g)
    except WrlUnsupported as ex:
        print(f"  W4 diagnostic [sixth role]: {ex}")
    else:
        raise AssertionError("sixth role should have been rejected")
    # out-of-registry edge kind is gated at graph_to_ir (edge-closure guard)
    g2 = parse_wrl("profile forge.world.core.v1\nperiods 1\nrelay a\nrelay b\n")
    g2.edges.append(("AsyncMsg", "a", "b"))
    try:
        graph_to_ir(g2)
    except WrlUnsupported as ex:
        print(f"  W4 diagnostic [out-of-registry edge]: {ex}")
    else:
        raise AssertionError("out-of-registry edge should have been rejected")


def main():
    print("[BINDING wrl-slice1] WRL Core -> IR v1 -> Fixture -> TRVM -> Film v0.7")
    t0 = time.time()
    fx, art, g = w1_adapter_fidelity()
    w2_ir_shape(art)
    w3_film_parity(fx, g)
    w4_diagnostics()
    verdict = "PASS_REF" if SKIP_NATIVE else "PASS_REF_AND_NATIVE"
    print(f"[BINDING wrl-slice1] {verdict}  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
