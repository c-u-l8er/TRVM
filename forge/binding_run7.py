"""binding_run7.py -- Phase 3D / 3D.1 / 3D.1.1: the CompilePlanV1 convergence +
Backend Identity Closure + Sealed Object Integrity battery (D1-D36).

GPT-5.6's Phase 3D ruling: extract a deterministic `CompilePlanV1` consumed by
the EXISTING backend machinery; make both the frozen Forge IR and the legacy
Fixture produce that SAME plan; prove complete plan/state/film/native/cost
parity; then remove Fixture construction from `lower_graph`, keeping the Fixture
only as an independent test oracle.

GPT-5.6's Phase 3D.1 correction (Backend Identity Closure): make the lowering
profile OPERATIVELY select the counter representation, keep the plan (and its
digest) representation-NEUTRAL, put the representation into COMPILE-time backend
fingerprints, and cryptographically SEAL+BIND the plan to its semantic artifact.

  D1  Fixture-built plan == IR-built plan (byte-identical), every world
  D2  a reorder-equivalent artifact yields the IDENTICAL plan
  D3  a JSON round-trip of the plan yields the IDENTICAL plan digest
  D4  bootstrap / WRL text / canvas all lower to the IDENTICAL plan
  D5  the plan-view initial state == the Fixture initial state
  D6  the plan-fed epoch trajectory == the golden trajectory   (native)
  D7  the plan-view Film v0.7 == the Fixture Film v0.7, every epoch
  D8  the plan-fed step is ic_ref == ic32 == golden             (native)
  D9  plan-fed and Fixture-fed compiled steps are BEHAVIORALLY identical (native)
  D10 unknown SEMANTIC fields (canvas key / static_config key) are typed rejects
  D11 a presentation-only edit moves NEITHER the plan digest NOR the backend id
  D12 a semantic edit moves BOTH the plan digest AND the BackendArtifactID
  D13 a lowering-profile change keeps the SemanticArtifactID, moves the backend id
  D14 the production frontend imports no Fixture (and no compiler) on lowering
  D15 the Fixture oracle still agrees with the plan under the full fold (native)
  D16 forced one-hot vs binary -> DIFFERENT backend terms (content + layout)
  D17 forced one-hot vs binary -> IDENTICAL films, every epoch
  D18 a lowering-profile change does NOT move the CompilePlanDigest
  D19 a lowering-profile change DOES move the BackendArtifactID
  D20 onehot_max under `auto` moves the backend id/content, NOT the semantic id
  D21 mutating a returned sealed plan cannot affect the sealed plan
  D22 a raw plan tampered below the signatures (stale semantic id) is rejected
  D23 a raw plan with a stale signature is rejected at seal
  D24 a raw plan with an incorrect object_index bijection is rejected
  D25 the production COMPILE path imports no Fixture module
  D26 same artifact+profile reproduce identical backend bytes/hash/layout id
  D27 the Fixture oracle and the production sealed-plan path are film-identical

GPT-5.6's Phase 3D.1.1 correction (Sealed Object Integrity): the sealed wrappers
must store CANONICAL BYTES rather than a mutable dictionary, derive their ids
internally, be truly immutable, reject counterfeit sealed-plan-shaped objects,
and re-verify plan/semantic integrity at the compilation boundary.

  D28 mutating the ORIGINAL artifact after sealing has no effect
  D29 mutating sealed.artifact affects only a returned copy
  D30 reassigning a sealed semantic id / body is impossible
  D31 mutating a returned sealed plan affects only the copy
  D32 reassigning a sealed plan id / digest is impossible
  D33 a counterfeit sealed-plan-shaped object is rejected at compile
  D34 tampered canonical plan bytes fail at compile time
  D35 semantic_artifact_id(sealed) agrees with its canonical bytes
  D36 same sealed bytes reproduce identical ids + backend content

Native is gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import os
import sys
import copy
import json
import time
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import wrl_ir as W
import wrl_canonical as WC
import wrl_canvas as CV
import wrl_plan as P
import compiler as C
import admit as AD
import binding_run5 as B5
import binding_run3o as O
from admit import mk_claim, film_bytes_v7
from fixture import init_state_v6, state_to_film_args_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

def _prof(enc, om=32):
    return {"counter_encoding": enc, "onehot_max": om, "numeric_backend": "ic",
            "compiler_hash": "a" * 64, "target": "ic32",
            "lowering_profile_version": "1.0"}


LP1 = _prof("one_hot")
LP2 = _prof("binary")

S = lambda rot: ("SetRotor", "sp", rot)
Rf = ("ResetFault", "ob")

# ------------------------------------------------------------- test worlds
# structural variety: a normal spinner, a two-door graph, two independent
# controllers, once+binary clocks, fixed+configurable spinners, a small graph.
W_CORE = B5.CORE_SRC
W_TWODOOR = (
    "profile forge.world.core.v1\nperiods 1\n"
    "[pulser:p0](mode=periodic, period=2, phase=0)\n"
    "[door:d0]\n[door:d1]\n"
    "[p0] --sig--> [d0]\n")
W_MULTI = (
    "profile forge.world.core.v1\nperiods 1\n"
    "[pulser:p0](mode=periodic, period=2, phase=0)\n"
    "[pulser:p1](mode=periodic, period=3, phase=1)\n"
    "[spinner:sa](w=8, n=4, rotor=16.0.0.0)\n"
    "[spinner:sb](w=8, n=4, rotor=8.0.0.0)\n"
    "[orb:oa]\n[orb:ob]\n"
    "[p0] --sig--> [sa]\n[p1] --sig--> [sb]\n"
    "[sa] --socket--> [oa]\n[sb] --socket--> [ob]\n")
W_CLOCKS = (
    "profile forge.world.core.v1\nperiods 1\n"
    "[pulser:p0](mode=once, epoch=3)\n"
    "[pulser:p1](mode=periodic, period=40, phase=5)\n"
    "[door:d0]\n[door:d1]\n"
    "[p0] --sig--> [d0]\n[p1] --sig--> [d1]\n")
W_FIXEDCONF = (
    "profile forge.world.core.v1\nperiods 1\n"
    "[pulser:p0](mode=periodic, period=2, phase=0)\n"
    "[spinner:sf](w=8, n=4, rotor=16.0.0.0)\n"
    "[spinner:sc](w=8, n=4, rotor=8.0.0.0, configurable)\n"
    "[orb:of]\n[orb:oc]\n"
    "[p0] --sig--> [sf]\n[p0] --sig--> [sc]\n"
    "[sf] --socket--> [of]\n[sc] --socket--> [oc]\n")
W_SMALL = (
    "profile forge.world.core.v1\nperiods 1\n"
    "[pulser:p0](mode=periodic, period=5, phase=2)\n"
    "[door:d0]\n[p0] --sig--> [d0]\n")

WORLDS = [("core", W_CORE), ("twodoor", W_TWODOOR), ("multi", W_MULTI),
          ("clocks", W_CLOCKS), ("fixedconf", W_FIXEDCONF), ("small", W_SMALL)]


def _plans(text):
    prog = W.lower_program(text, W.parse_wrl_legacy_document)
    sealed = prog.sealed_artifact
    plan_ir = P.artifact_to_compile_plan_v1(sealed)
    fx = prog.as_fixture_for_test()
    plan_fx = P.fixture_to_compile_plan_v1(fx, sealed.semantic_id)
    return prog, sealed, plan_ir, fx, plan_fx


def _traj_for_view(view, fx, batches, world0, reducer):
    """Fold `batches` through a compiled step over any Fixture-shaped view (the
    profile-driven `_PlanView` OR the Fixture oracle itself), returning
    [(decoded_world, claimstate)] per epoch. The decoded world is representation-
    independent, so two views that differ only in counter representation yield
    identical worlds (D17) -- the whole point of the neutral plan."""
    claim = AD.init_claimstate()
    world = copy.deepcopy(world0)
    out = []
    step, _ = C.compile_step_v6(view)
    for e, batch in enumerate(batches):
        claim, cfg_map, resets = AD.admit_step(claim, batch, 1 + e, fx)
        ec = C.enc_config_bundle(view, cfg_map, resets)
        world = C.dec_state_v6(view, reducer(
            f"(({step} {ec}) {C.enc_state_v6(view, world)})"))
        out.append((copy.deepcopy(world), copy.deepcopy(claim)))
    return out


# ---------------------------------------------------------------- driver
def main():
    print("[BINDING wrl-3d] CompilePlanV1 convergence + Fixture retirement")
    allok = True
    native_ok = True
    t0 = time.time()

    def rep(ok, okn, label):
        nonlocal allok, native_ok
        allok &= ok
        tag = "PASS" if ok else "FAIL"
        if okn is False:
            native_ok = False
            tag = "FAIL(native)"
        print(f"  [{tag}] {label}")

    # ---- D1 Fixture plan == IR plan (all worlds)
    d1 = True
    for nm, txt in WORLDS:
        _, _, plan_ir, _, plan_fx = _plans(txt)
        if plan_ir != plan_fx:
            d1 = False
    rep(d1, None, "D1) Fixture-built plan == IR-built plan (byte-identical), "
                  f"{len(WORLDS)} worlds")

    # ---- D2 reorder-equivalent artifact -> identical plan
    d2 = True
    for nm, txt in WORLDS:
        prog, sealed, plan_ir, _, _ = _plans(txt)
        art2 = copy.deepcopy(sealed.artifact)
        art2["objects"].reverse()
        art2["edges"].reverse()
        for pol in ("numeric_policy_ids",):
            art2["semantic_policies"][pol] = list(
                reversed(art2["semantic_policies"][pol]))
        if P.artifact_to_compile_plan_v1(art2) != plan_ir:
            d2 = False
    rep(d2, None, "D2) reorder-equivalent artifact -> IDENTICAL plan")

    # ---- D3 JSON round-trip -> identical plan digest
    d3 = True
    for nm, txt in WORLDS:
        _, _, plan_ir, _, _ = _plans(txt)
        rt = json.loads(json.dumps(plan_ir))
        if P.compile_plan_digest(rt) != P.compile_plan_digest(plan_ir):
            d3 = False
    rep(d3, None, "D3) JSON round-trip -> IDENTICAL plan digest")

    # ---- D4 bootstrap / WRL text / canvas -> identical plan
    boot = W.lower_program(B5.BOOTSTRAP_SRC)
    core = W.lower_program(B5.CORE_SRC, W.parse_wrl_legacy_document)
    canvas = CV.graph_to_canvas(core.graph)
    canv = CV.lower_canvas(canvas)
    p_boot = P.artifact_to_compile_plan_v1(boot.sealed_artifact)
    p_core = P.artifact_to_compile_plan_v1(core.sealed_artifact)
    p_canv = P.artifact_to_compile_plan_v1(canv.sealed_artifact)
    rep(p_boot == p_core == p_canv, None,
        "D4) bootstrap / WRL text / canvas -> IDENTICAL CompilePlanV1")

    # ---- D5 plan-view initial state == Fixture initial state (all worlds)
    d5 = True
    for nm, txt in WORLDS:
        _, _, plan_ir, fx, _ = _plans(txt)
        if init_state_v6(P.plan_view(plan_ir)) != init_state_v6(fx):
            d5 = False
    rep(d5, None, "D5) plan-view initial state == Fixture initial state")

    # ---- D6/D8 plan-fed trajectory == golden; ic_ref == ic32 == golden (CORE)
    _, _, plan_core, fxC, _ = _plans(W_CORE)
    view = P.plan_view(plan_core)
    batches = [[mk_claim(1, 1, S((16, 0, 10, 0)))],
               [mk_claim(2, 2, S((16, 0, 20, 0))), mk_claim(3, 3, Rf)],
               [mk_claim(4, 4, S((16, 0, 30, 0)))]]
    world0 = init_state_v6(O.FX)
    world0["fault_ob"] = 1
    gold = O._golden_traj(AD.init_claimstate(), world0, batches, 1)

    def _plan_traj(reducer):
        claim = AD.init_claimstate()
        world = copy.deepcopy(world0)
        out = []
        step, _ = C.compile_step_v6(view)
        for e, batch in enumerate(batches):
            claim, cfg_map, resets = AD.admit_step(claim, batch, 1 + e, fxC)
            ec = C.enc_config_bundle(view, cfg_map, resets)
            world = C.dec_state_v6(view, reducer(
                f"(({step} {ec}) {C.enc_state_v6(view, world)})"))
            out.append((copy.deepcopy(world), copy.deepcopy(claim)))
        return out

    ref_traj = _plan_traj(O.norm)
    d6r = all(ref_traj[e][0] == gold[e][0] for e in range(len(batches)))
    d6n = None
    if not SKIP_NATIVE:
        nat_traj = _plan_traj(O.native)
        d6n = all(nat_traj[e][0] == gold[e][0] for e in range(len(batches)))
    rep(d6r, d6n, "D6) plan-fed epoch trajectory == golden trajectory")
    rep(d6r, d6n, "D8) plan-fed step ic_ref == ic32 == golden (direct IR path)")

    # ---- D7 plan-view Film v0.7 == Fixture Film v0.7, every epoch (CORE)
    d7 = True
    for e in range(len(batches)):
        gw, gc = gold[e][0], gold[e][1]
        gf = film_bytes_v7(*state_to_film_args_v6(fxC, gw, 1 + e), state=gc)
        pf = film_bytes_v7(*state_to_film_args_v6(view, gw, 1 + e), state=gc)
        if gf != pf:
            d7 = False
    rep(d7, None, "D7) plan-view Film v0.7 == Fixture Film v0.7, every epoch")

    # ---- D9 plan-fed and Fixture-fed compiled steps are the SAME function
    d9r, d9n = True, (None if SKIP_NATIVE else True)
    for nm, txt in WORLDS:
        _, _, plan_ir, fx, _ = _plans(txt)
        v = P.plan_view(plan_ir)
        step_v, _ = C.compile_step_v6(v)
        step_f, _ = C.compile_step_v6(fx)
        st = init_state_v6(v)
        for _k in range(3):
            ec_v = C.enc_config_bundle(v, {}, {})
            ec_f = C.enc_config_bundle(fx, {}, {})
            tv = f"(({step_v} {ec_v}) {C.enc_state_v6(v, st)})"
            tf = f"(({step_f} {ec_f}) {C.enc_state_v6(fx, st)})"
            ov = C.dec_state_v6(v, O.norm(tv))
            of = C.dec_state_v6(fx, O.norm(tf))
            if ov != of:
                d9r = False
            if nm == "core" and not SKIP_NATIVE:
                if C.dec_state_v6(v, O.native(tv)) != of:
                    d9n = False
            st = ov
    rep(d9r, d9n, "D9) plan-fed and Fixture-fed compiled steps are "
                  "BEHAVIORALLY identical (same decoded outputs over reachable "
                  "states)")

    # ---- D10 unknown SEMANTIC fields are typed rejections
    d10 = True
    bad_canvas = copy.deepcopy(canvas)
    bad_canvas["nodes"][0]["mystery"] = 1
    try:
        CV.lower_canvas(bad_canvas)
        d10 = False
    except W.WrlValidationError as ex:
        d10 &= (ex.code == WC.WRL_UNSUPPORTED_FEATURE)
    bad_cfg = copy.deepcopy(canvas)
    for n in bad_cfg["nodes"]:
        if n["role"] == "Pulser":
            n["static_config"]["overclock"] = True
    try:
        CV.lower_canvas(bad_cfg)
        d10 = False
    except W.WrlValidationError as ex:
        d10 &= (ex.code == WC.WRL_UNSUPPORTED_FEATURE)
    rep(d10, None, "D10) unknown canvas key AND unknown static_config field are "
                   "typed WRL_UNSUPPORTED_FEATURE rejections")

    # ---- D11 presentation-only edit moves neither plan digest nor backend id
    pres = copy.deepcopy(canvas)
    for n in pres["nodes"]:
        n["presentation"]["x"] = 9999
        n["presentation"]["color"] = "#000000"
    p_pres = P.artifact_to_compile_plan_v1(CV.lower_canvas(pres).sealed_artifact)
    d11 = (P.compile_plan_digest(p_pres) == P.compile_plan_digest(p_core)
           and WC.backend_artifact_id(p_pres["semantic_artifact_id"], LP1)
           == WC.backend_artifact_id(p_core["semantic_artifact_id"], LP1))
    rep(d11, None, "D11) presentation-only edit moves NEITHER plan digest NOR "
                   "BackendArtifactID")

    # ---- D12 semantic edit moves both plan digest and BackendArtifactID
    sem = copy.deepcopy(canvas)
    for n in sem["nodes"]:
        if n["role"] == "Spinner":
            n["static_config"]["rotor"] = [7, 0, 0, 0]
    p_sem = P.artifact_to_compile_plan_v1(CV.lower_canvas(sem).sealed_artifact)
    d12 = (P.compile_plan_digest(p_sem) != P.compile_plan_digest(p_core)
           and WC.backend_artifact_id(p_sem["semantic_artifact_id"], LP1)
           != WC.backend_artifact_id(p_core["semantic_artifact_id"], LP1))
    rep(d12, None, "D12) semantic edit moves BOTH plan digest AND "
                   "BackendArtifactID")

    # ---- D13 lowering-profile change keeps semantic id, moves backend id
    sem_id = p_core["semantic_artifact_id"]
    b1 = WC.backend_artifact_id(sem_id, LP1)
    b2 = WC.backend_artifact_id(sem_id, LP2)
    cp1 = W.compile_program(core, LP1)
    cp2 = W.compile_program(core, LP2)
    d13 = (cp1.sealed_plan.semantic_artifact_id
           == cp2.sealed_plan.semantic_artifact_id == sem_id and b1 != b2
           and cp1.backend_artifact_id == b1 and cp2.backend_artifact_id == b2)
    rep(d13, None, "D13) lowering-profile change preserves SemanticArtifactID, "
                   "moves BackendArtifactID")

    # ---- D14 production frontend imports no Fixture (and no compiler)
    probe = (
        "import sys; import wrl_ir as W;"
        "p=W.lower_program('profile forge.world.core.v1\\nperiods 1\\n"
        "pulser p0 periodic 2 0\\ndoor d0\\nwire p0 -> d0\\n');"
        "assert 'fixture' not in sys.modules, 'fixture imported on lowering';"
        "assert 'compiler' not in sys.modules, 'compiler imported on lowering';"
        "fx=p.as_fixture_for_test();"
        "assert 'fixture' in sys.modules;"
        "print('OK')")
    r = subprocess.run([sys.executable, "-c", probe], cwd=HERE,
                       capture_output=True, text=True)
    rep(r.returncode == 0 and r.stdout.strip() == "OK", None,
        "D14) production lowering imports NO Fixture and NO compiler "
        "(oracle is lazy)")

    # ---- D15 Fixture oracle agrees with the plan under the full fold (native)
    fv0 = O.X.enc_factvec([], O.CAP)
    rv0 = O.X.enc_factvec([], O.RCAP)
    term = O._build_fold(batches, fv0, rv0, C.enc_state_v6(fxC, world0))
    gsum = O._golden_summary(gold)
    d15r = (O._traj_summary(O._decode_fold(O.norm(term), len(batches))) == gsum)
    d15n = None
    if not SKIP_NATIVE:
        d15n = (O._traj_summary(O._decode_fold(O.native(term), len(batches)))
                == gsum)
    rep(d15r, d15n, "D15) Fixture oracle folds to the golden trajectory (the "
                    "retained oracle stays valid)")

    # ================= Phase 3D.1 -- Backend Identity Closure (D16-D27) =====
    cp_oh = W.compile_program(core, LP1)     # forced one-hot
    cp_bin = W.compile_program(core, LP2)    # forced binary

    # ---- D16 forced one-hot vs binary -> different backend terms
    d16 = (cp_oh.backend_content_hash != cp_bin.backend_content_hash
           and cp_oh.backend_layout_signature != cp_bin.backend_layout_signature)
    rep(d16, None, "D16) forced one-hot vs binary -> DIFFERENT backend content "
                   "hash AND backend layout signature")

    # ---- D17 forced one-hot vs binary -> identical films, every epoch
    view_oh = P.plan_view(plan_core, LP1)
    view_bin = P.plan_view(plan_core, LP2)
    traj_oh = _traj_for_view(view_oh, fxC, batches, world0, O.norm)
    traj_bin = _traj_for_view(view_bin, fxC, batches, world0, O.norm)
    d17r = True
    for e in range(len(batches)):
        if traj_oh[e][0] != traj_bin[e][0]:
            d17r = False
        fo = film_bytes_v7(*state_to_film_args_v6(view_oh, traj_oh[e][0],
                                                  1 + e), state=traj_oh[e][1])
        fb = film_bytes_v7(*state_to_film_args_v6(view_bin, traj_bin[e][0],
                                                  1 + e), state=traj_bin[e][1])
        if fo != fb:
            d17r = False
    d17n = None
    if not SKIP_NATIVE:
        nat_oh = _traj_for_view(view_oh, fxC, batches, world0, O.native)
        nat_bin = _traj_for_view(view_bin, fxC, batches, world0, O.native)
        d17n = all(nat_oh[e][0] == nat_bin[e][0] == traj_oh[e][0]
                   for e in range(len(batches)))
    rep(d17r, d17n, "D17) forced one-hot vs binary -> IDENTICAL films/worlds, "
                    "every epoch")

    # ---- D18 profile change does NOT move the CompilePlanDigest
    d18 = (cp_oh.sealed_plan.compile_plan_digest
           == cp_bin.sealed_plan.compile_plan_digest
           == P.compile_plan_digest(plan_core))
    rep(d18, None, "D18) lowering-profile change does NOT move the "
                   "CompilePlanDigest (plan is representation-neutral)")

    # ---- D19 profile change DOES move the BackendArtifactID
    d19 = (cp_oh.backend_artifact_id != cp_bin.backend_artifact_id)
    rep(d19, None, "D19) lowering-profile change DOES move the "
                   "BackendArtifactID")

    # ---- D20 onehot_max under `auto` moves backend, not semantic (W_SMALL p5)
    prog_small, _, _, _, _ = _plans(W_SMALL)
    a32 = W.compile_program(prog_small, _prof("auto", 32))   # 5 <= 32 -> onehot
    a4 = W.compile_program(prog_small, _prof("auto", 4))     # 5 >  4  -> binp
    d20 = (a32.backend_artifact_id != a4.backend_artifact_id
           and a32.backend_content_hash != a4.backend_content_hash
           and a32.sealed_plan.semantic_artifact_id
           == a4.sealed_plan.semantic_artifact_id
           and a32.sealed_plan.compile_plan_digest
           == a4.sealed_plan.compile_plan_digest)
    rep(d20, None, "D20) onehot_max under `auto` moves BackendArtifactID + "
                   "content, NOT SemanticArtifactID/CompilePlanDigest")

    # ---- D21 mutating a returned sealed plan cannot affect it
    sp21 = P.seal_compile_plan(
        P.artifact_to_compile_plan_v1(core.sealed_artifact), core.sealed_artifact)
    snap = sp21.compile_plan_digest
    leak = sp21.canonical_plan
    leak["orbs"].append("HACK")
    leak["spinners"] = []
    leak["semantic_artifact_id"] = "sem-" + "0" * 64
    d21 = (sp21.compile_plan_digest == snap
           and "HACK" not in sp21.canonical_plan["orbs"]
           and P.compile_plan_digest(sp21.canonical_plan) == snap)
    rep(d21, None, "D21) mutating a returned sealed plan cannot affect the "
                   "sealed plan (isolated deep copy)")

    # ---- D22 raw plan tampered BELOW the signatures (rotor lanes) is rejected
    # rotor lanes are in NO neutral signature, so signatures still recompute --
    # only the plan->IR->SemanticArtifactID rebinding catches it.
    plan22 = P.artifact_to_compile_plan_v1(core.sealed_artifact)
    plan22["spinners"][0]["rotor"] = [7, 0, 0, 0]
    try:
        P.seal_compile_plan(plan22)
        d22 = False
    except W.WrlValidationError as ex:
        d22 = (ex.code == P.WRL_BAD_COMPILE_PLAN)
    rep(d22, None, "D22) raw plan tampered below the signatures (stale semantic "
                   "id) is rejected at seal")

    # ---- D23 raw plan with a stale signature is rejected at seal
    plan23 = P.artifact_to_compile_plan_v1(core.sealed_artifact)
    plan23["observable_signature"] = "obsv-" + "0" * 64
    try:
        P.seal_compile_plan(plan23)
        d23 = False
    except W.WrlValidationError as ex:
        d23 = (ex.code == P.WRL_BAD_COMPILE_PLAN)
    rep(d23, None, "D23) raw plan with a stale signature is rejected at seal")

    # ---- D24 raw plan with an incorrect object_index bijection is rejected
    plan24 = P.artifact_to_compile_plan_v1(core.sealed_artifact)
    plan24["object_index"][plan24["object_order"][0]] = 999
    try:
        P.seal_compile_plan(plan24)
        d24 = False
    except W.WrlValidationError as ex:
        d24 = (ex.code == P.WRL_BAD_COMPILE_PLAN)
    rep(d24, None, "D24) raw plan with an incorrect object_index bijection is "
                   "rejected")

    # ---- D25 production COMPILE path imports no Fixture module
    probe25 = (
        "import sys; import wrl_ir as W;"
        "prof={'counter_encoding':'auto','onehot_max':32,"
        "'numeric_backend':'ic','compiler_hash':'a'*64,'target':'ic32',"
        "'lowering_profile_version':'1.0'};"
        "p=W.lower_program('profile forge.world.core.v1\\nperiods 1\\n"
        "pulser p0 periodic 2 0\\ndoor d0\\nwire p0 -> d0\\n');"
        "cp=W.compile_program(p, prof);"
        "assert cp.backend_content_hash.startswith('bcnt-');"
        "assert cp.backend_artifact_id.startswith('bknd-');"
        "assert 'fixture' not in sys.modules, 'fixture imported on compile';"
        "print('OK')")
    r25 = subprocess.run([sys.executable, "-c", probe25], cwd=HERE,
                         capture_output=True, text=True)
    rep(r25.returncode == 0 and r25.stdout.strip() == "OK", None,
        "D25) production lower+seal+COMPILE imports NO Fixture module")

    # ---- D26 same artifact+profile reproduce identical backend bytes/hash
    r1 = W.compile_program(core, LP1)
    r2 = W.compile_program(core, LP1)
    d26 = (r1.backend_content_hash == r2.backend_content_hash
           and r1.backend_layout_signature == r2.backend_layout_signature
           and r1.backend_artifact_id == r2.backend_artifact_id)
    rep(d26, None, "D26) same artifact+profile reproduce identical backend "
                   "content hash / layout signature / BackendArtifactID")

    # ---- D27 Fixture oracle and production sealed-plan path are film-identical
    cp_prod = W.compile_program(core, _prof("auto"))
    view_prod = P.plan_view(cp_prod.sealed_plan.canonical_plan, _prof("auto"))
    traj_prod = _traj_for_view(view_prod, fxC, batches, world0, O.norm)
    traj_fx = _traj_for_view(fxC, fxC, batches, world0, O.norm)
    d27r = True
    for e in range(len(batches)):
        if traj_prod[e][0] != traj_fx[e][0]:
            d27r = False
        fp = film_bytes_v7(*state_to_film_args_v6(view_prod, traj_prod[e][0],
                                                  1 + e), state=traj_prod[e][1])
        ff = film_bytes_v7(*state_to_film_args_v6(fxC, traj_fx[e][0],
                                                  1 + e), state=traj_fx[e][1])
        if fp != ff:
            d27r = False
    rep(d27r, None, "D27) Fixture oracle and production sealed-plan path are "
                    "film-identical, every epoch")

    # ============= Phase 3D.1.1 -- Sealed Object Integrity (D28-D36) =========
    sealC = core.sealed_artifact
    prof_auto = _prof("auto")

    def _blocked(fn):
        try:
            fn()
            return False
        except WC.WrlValidationError as ex:
            return ex.code == WC.WRL_SEALED_IMMUTABLE

    # ---- D28 mutating the ORIGINAL artifact after sealing has no effect
    raw = sealC.artifact                                # a fresh mutable dict
    seal28 = WC.SealedArtifact(raw)
    id_before = seal28.semantic_id
    raw["objects"][0]["object_id"] = "MUTATED"
    raw["semantic_policies"]["rulepack_id"] = "tampered"
    d28 = (seal28.semantic_id == id_before
           and seal28.artifact["objects"][0]["object_id"] != "MUTATED"
           and WC.semantic_artifact_id(seal28) == id_before)
    rep(d28, None, "D28) mutating the original artifact after sealing has no "
                   "effect")

    # ---- D29 mutating sealed.artifact affects only a returned copy
    a = sealC.artifact
    a["objects"][0]["object_id"] = "MUTATED"
    d29 = (sealC.artifact["objects"][0]["object_id"] != "MUTATED"
           and sealC.artifact is not a)
    rep(d29, None, "D29) mutating sealed.artifact affects only a returned copy")

    # ---- D30 reassigning a sealed semantic id / body is impossible
    def _set_semid():
        sealC.semantic_id = "sem-" + "0" * 64

    def _set_body():
        sealC.artifact = {}
    d30 = _blocked(_set_semid) and _blocked(_set_body)
    rep(d30, None, "D30) reassigning a sealed semantic id / body is impossible")

    # ---- a sealed plan for the plan-side checks
    cp = W.compile_program(core, prof_auto)
    sp = cp.sealed_plan

    # ---- D31 mutating a returned sealed plan affects only the copy
    pl = sp.canonical_plan
    pl["pulsers"][0]["id"] = "ZZ"
    d31 = (sp.canonical_plan["pulsers"][0]["id"] != "ZZ"
           and sp.canonical_plan is not pl)
    rep(d31, None, "D31) mutating a returned sealed plan affects only the copy")

    # ---- D32 reassigning a sealed plan id / digest is impossible
    def _set_digest():
        sp.compile_plan_digest = "plan-" + "0" * 64

    def _set_semplan():
        sp.semantic_artifact_id = "sem-" + "0" * 64
    d32 = _blocked(_set_digest) and _blocked(_set_semplan)
    rep(d32, None, "D32) reassigning a sealed plan id/digest is impossible")

    # ---- D33 a counterfeit sealed-plan-shaped object is rejected at compile
    good_plan = P.artifact_to_compile_plan_v1(sealC)

    class _Counterfeit:
        canonical_plan = good_plan
        semantic_artifact_id = good_plan["semantic_artifact_id"]
        compile_plan_digest = P.compile_plan_digest(good_plan)
    d33 = False
    try:
        P.compile_sealed_plan(_Counterfeit(), prof_auto)
    except WC.WrlValidationError as ex:
        d33 = ex.code == P.WRL_BAD_COMPILE_PLAN
    rep(d33, None, "D33) a counterfeit sealed-plan-shaped object is rejected")

    # ---- D34 tampered canonical plan bytes fail at compile time
    sp34 = P.seal_compile_plan(P.artifact_to_compile_plan_v1(sealC), sealC)
    tampered = sp34.canonical_plan
    tampered["spinners"][0]["rotor"] = [9, 9, 9, 9]     # below every signature
    object.__setattr__(sp34, "_canonical_bytes",
                       WC.serialize_artifact(tampered))
    d34 = False
    try:
        P.compile_sealed_plan(sp34, prof_auto)
    except WC.WrlValidationError as ex:
        d34 = ex.code == P.WRL_BAD_COMPILE_PLAN
    rep(d34, None, "D34) tampered canonical plan bytes fail at compile time")

    # ---- D35 semantic_artifact_id(sealed) agrees with its canonical bytes
    d35 = (WC.semantic_artifact_id(sealC)
           == "sem-" + WC._sha(sealC.canonical_bytes)
           == sealC.semantic_id)
    rep(d35, None, "D35) semantic_artifact_id(sealed) agrees with its canonical "
                   "bytes")

    # ---- D36 same sealed bytes reproduce identical ids + backend content
    spa = W.compile_program(core, prof_auto).sealed_plan
    spb = W.compile_program(core, prof_auto).sealed_plan
    ca = P.compile_sealed_plan(spa, LP1)
    cb = P.compile_sealed_plan(spb, LP1)
    d36 = (spa.canonical_bytes == spb.canonical_bytes
           and spa.semantic_artifact_id == spb.semantic_artifact_id
           and spa.compile_plan_digest == spb.compile_plan_digest
           and ca.backend_artifact_id == cb.backend_artifact_id
           and ca.backend_content_hash == cb.backend_content_hash
           and ca.backend_layout_signature == cb.backend_layout_signature)
    rep(d36, None, "D36) same sealed bytes reproduce identical ids + backend "
                   "content")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-3d] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] Fixture is retired as the production lowering contract "
          "(CompilePlanV1 replaces it) and retained as an independent oracle.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
