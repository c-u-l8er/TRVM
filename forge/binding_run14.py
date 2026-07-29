"""binding_run14.py -- quarter_turn_z under forge_named_rotor_rne_sym_v1 (P1-P11).

GPT-5.6 ruling (follow-on to 3B.5.1): implement `quarter_turn_z` as the
geometry-dependent SYMMETRIC INTEGER projection of a 90-degree turn about z under
the named policy `forge_named_rotor_rne_sym_v1`:

    quarter_turn_z(n) = (round(2^n / sqrt(2)), 0, 0, round(2^n / sqrt(2)))

with NO residual redistribution (each equal lane rounded to nearest INDEPENDENTLY;
the norm is NOT renormalized), computed by EXACT integer arithmetic, canonical sign
scalar>0. Because the value depends on the spinner's n, the SemanticArtifactID is
GEOMETRY-DEPENDENT. The policy id is BUILD PROVENANCE only -- it does NOT enter the
artifact bytes, so a quarter_turn_z rotor and its numeric twin still seal to
identical bytes (the sugar-washes-out pre-pass discipline is preserved).

  P1  the pinned projection values   q4=(11,0,0,11) q8=(181,0,0,181)
      q16=(46341,0,0,46341), and the exact-integer round matches a high-precision
      round(2^n/sqrt(2)) for every n in 0..24
  P2  the projection is SYMMETRIC (lane0==lane3, lanes1,2==0) with NO residual
      redistribution (norm^2 = 2*q^2 is NOT forced back to 2^2n) and scalar>0
  P3  a quarter_turn_z world == its numeric twin (sealed bytes + SemanticArtifactID)
      -- sugar washes out; the policy id never enters the artifact
  P4  the identity is GEOMETRY-DEPENDENT: quarter_turn_z at two different spinner n
      lowers to DIFFERENT numeric rotors and DIFFERENT SemanticArtifactIDs
  P5  quarter_turn_z is now ACCEPTED (was a typed reject in 3B-4); an unknown name
      still rejects, and quarter_turn_z with no spinner n still rejects
  P6  provenance: named_rotor_policy('quarter_turn_z') == the policy id, an exact
      name has policy None, an unknown name rejects
  P7  the accepted vocabulary is single-sourced: ALL_ROTOR_NAMES == exact + policy,
      and completion offers exactly it (drift-free with the desugarer)
  P8  the desugarer is idempotent and the formatter emits the numeric surface
      (quarter_turn_z washes out of the canonical text)
  P9  3B-3 diagnostics fire through a quarter_turn_z desugar (a dup id is still
      located on the sugared source)
  P10 the SemanticDiff bridge holds across a quarter_turn_z <-> exact rotor edit
      (semantic_diff.is_empty() == same SemanticArtifactID)
  P11 a quarter_turn_z world runs ic_ref == ic32 == golden               (native)

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import os
import sys
import copy
import time
from decimal import Decimal, getcontext

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import wrl_ir as W
import wrl_canonical as WC
import wrl_sugar as SG
import wrl_format as F
import wrl_complete as CP
import wrl_diagnostics as DG
import wrl_diff as DF
import wrl_plan as P
import compiler as C
import admit as AD
import binding_run3o as O
import binding_run7 as B7
from admit import mk_claim
from fixture import init_state_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"


def _spinner_world(rotor_expr, w, n):
    return ("profile forge.world.core.v1\nperiods 1\n"
            "[pulser:p0](mode=periodic, period=2, phase=0)\n"
            "[spinner:sp](w=%d, n=%d, rotor=%s)\n"
            "[orb:ob]\n"
            "[p0] --sig--> [sp]\n"
            "[sp] --socket--> [ob]\n" % (w, n, rotor_expr))


def _ref_round(n):
    """A high-precision reference for round(2^n/sqrt(2)) (half-up; the argument is
    irrational so there is never an exact .5 tie)."""
    getcontext().prec = 80
    return int(Decimal(1 << n) / Decimal(2).sqrt() + Decimal("0.5"))


def main():
    print("[BINDING wrl-qtz] quarter_turn_z under forge_named_rotor_rne_sym_v1")
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

    QTZ = "quarter_turn_z"

    # ---- P1 pinned projection values + high-precision round(2^n/sqrt(2)) 0..24
    p1 = (SG.named_rotor(QTZ, 4) == (11, 0, 0, 11)
          and SG.named_rotor(QTZ, 8) == (181, 0, 0, 181)
          and SG.named_rotor(QTZ, 16) == (46341, 0, 0, 46341))
    for n in range(0, 25):
        if SG._round_u_over_sqrt2(n) != _ref_round(n):
            p1 = False
    rep(p1, None, "P1) q4=(11..) q8=(181..) q16=(46341..); exact-int round == "
                  "round(2^n/sqrt2) for n in 0..24")

    # ---- P2 symmetric, no residual redistribution, scalar>0
    p2 = True
    for n in (4, 8, 16):
        s, x, y, z = SG.named_rotor(QTZ, n)
        norm2 = s * s + x * x + y * y + z * z
        unit2 = (1 << n) ** 2
        if not (s == z > 0 and x == 0 and y == 0 and norm2 != unit2):
            p2 = False
    rep(p2, None, "P2) symmetric (lane0==lane3>0, lanes1,2==0), NO residual "
                  "redistribution (norm^2 != 2^2n), scalar>0")

    # ---- P3 quarter_turn_z world == its numeric twin (bytes + sem id)
    p3 = True
    for w, n in [(8, 4), (16, 8), (32, 16)]:
        numeric = ".".join(str(v) for v in SG.named_rotor(QTZ, n))
        a = W.lower_program(SG.desugar_core(_spinner_world(QTZ, w, n)),
                            W.parse_wrl_legacy_document)
        b = W.lower_program(_spinner_world(numeric, w, n), W.parse_wrl_legacy_document)
        if (a.semantic_artifact_id != b.semantic_artifact_id
                or a.sealed_artifact.artifact != b.sealed_artifact.artifact):
            p3 = False
        # the policy id is provenance ONLY -- it must NOT appear in the bytes
        if SG.NAMED_ROTOR_RNE_SYM_POLICY.encode() in WC.serialize_artifact(
                a.sealed_artifact.artifact):
            p3 = False
    rep(p3, None, "P3) quarter_turn_z world == numeric twin (bytes + sem id); "
                  "policy id never enters the artifact")

    # ---- P4 identity is GEOMETRY-DEPENDENT (different n -> different sem id)
    a4 = W.lower_program(SG.desugar_core(_spinner_world(QTZ, 8, 4)),
                         W.parse_wrl_legacy_document)
    a8 = W.lower_program(SG.desugar_core(_spinner_world(QTZ, 16, 8)),
                         W.parse_wrl_legacy_document)
    p4 = a4.semantic_artifact_id != a8.semantic_artifact_id
    rep(p4, None, "P4) geometry-dependent: quarter_turn_z at n=4 vs n=8 -> "
                  "different SemanticArtifactID")

    # ---- P5 acceptance: qtz accepted; unknown + missing-n still reject
    p5 = True
    try:
        SG.parse_legacy_sugared(_spinner_world(QTZ, 8, 4))     # now accepted
    except Exception:
        p5 = False
    for bad, expect in [(_spinner_world("barrel_roll", 8, 4), True),
                        ("profile forge.world.core.v1\nperiods 1\n"
                         "[spinner:sp](w=8, rotor=quarter_turn_z)\n", True)]:
        try:
            SG.desugar_core(bad)
            p5 = False
        except WC.WrlValidationError as e:
            p5 = p5 and (e.code == WC.WRL_UNSUPPORTED_FEATURE) == expect
    rep(p5, None, "P5) quarter_turn_z ACCEPTED; unknown name + missing-n still "
                  "typed WRL_UNSUPPORTED_FEATURE rejects")

    # ---- P6 provenance policy accessor
    p6 = True
    try:
        p6 = (SG.named_rotor_policy(QTZ) == SG.NAMED_ROTOR_RNE_SYM_POLICY
              and SG.named_rotor_policy("identity") is None)
    except Exception:
        p6 = False
    try:
        SG.named_rotor_policy("barrel_roll")
        p6 = False
    except WC.WrlValidationError as e:
        p6 = p6 and e.code == WC.WRL_UNSUPPORTED_FEATURE
    rep(p6, None, "P6) named_rotor_policy: qtz->policy id, exact->None, unknown->reject")

    # ---- P7 single-sourced accepted vocabulary; completion offers exactly it
    p7 = (SG.ALL_ROTOR_NAMES == SG.ROTOR_TABLE_NAMES + SG.POLICY_ROTOR_NAMES
          and QTZ in SG.POLICY_ROTOR_NAMES
          and set(CP.named_rotor_completions()) == set(SG.ALL_ROTOR_NAMES))
    # every offered name desugars + parses at n=4
    for nm in CP.named_rotor_completions():
        try:
            SG.parse_legacy_sugared(_spinner_world(nm, 8, 4))
        except Exception:
            p7 = False
    rep(p7, None, "P7) ALL_ROTOR_NAMES single-sourced (exact+policy); completion "
                  "offers exactly it and every name parses")

    # ---- P8 desugar idempotent + formatter emits numeric surface (qtz washes out)
    src = _spinner_world(QTZ, 16, 8)
    d1 = SG.desugar_core(src)
    d2 = SG.desugar_core(d1)
    fmt = F.format_wrl_core(W.parse_wrl_legacy_document(d1))
    p8 = (d1 == d2 and QTZ not in d1 and QTZ not in fmt
          and "181.0.0.181" in d1)
    rep(p8, None, "P8) desugar idempotent; formatter emits numeric surface "
                  "(quarter_turn_z washes out)")

    # ---- P9 3B-3 diagnostics fire through a quarter_turn_z desugar
    dup = ("profile forge.world.core.v1\nperiods 1\n"
           "[pulser:p0](mode=periodic, period=2, phase=0)\n"
           "[spinner:sp](w=16, n=8, rotor=quarter_turn_z)\n"
           "[spinner:sp](w=16, n=8, rotor=quarter_turn_z)\n"
           "[orb:ob]\n[p0] --sig--> [sp]\n[sp] --socket--> [ob]\n")
    dg = DG.diagnose_legacy_document(SG.desugar_core(dup))
    p9 = (len(dg) == 1 and dg[0].code == WC.WRL_DUPLICATE_ID
          and dg[0].canonical_object_id == "sp")
    rep(p9, None, "P9) 3B-3 diagnostics fire through a quarter_turn_z desugar")

    # ---- P10 SemanticDiff bridge across a quarter_turn_z <-> exact rotor edit
    qtz_g = W.parse_wrl_legacy_document(SG.desugar_core(_spinner_world(QTZ, 16, 8)))
    idn_g = W.parse_wrl_legacy_document(SG.desugar_core(_spinner_world("identity", 16, 8)))
    same_g = W.parse_wrl_legacy_document(SG.desugar_core(_spinner_world(QTZ, 16, 8)))
    d_move = DF.diff_graphs(qtz_g, idn_g)
    d_same = DF.diff_graphs(qtz_g, same_g)
    p10 = (d_same.is_empty()
           and not d_move.is_empty()
           and d_move.is_empty() ==
           (W.graph_to_ir(qtz_g) == W.graph_to_ir(idn_g)))
    rep(p10, None, "P10) SemanticDiff bridge across quarter_turn_z <-> identity "
                   "(is_empty == same SemanticArtifactID)")

    # ---- P11 a quarter_turn_z world runs ic_ref == ic32 == golden (native)
    named_full = B7.W_CORE.replace("rotor=16.0.0.0", "rotor=quarter_turn_z")
    prog = W.lower_program(SG.desugar_core(named_full), W.parse_wrl_legacy_document)
    plan = P.artifact_to_compile_plan_v1(prog.sealed_artifact)
    view = P.plan_view(plan)
    fx = prog.as_fixture_for_test()
    batches = [[mk_claim(1, 1, B7.S((16, 0, 10, 0)))],
               [mk_claim(2, 2, B7.S((16, 0, 20, 0))), mk_claim(3, 3, B7.Rf)],
               [mk_claim(4, 4, B7.S((16, 0, 30, 0)))]]
    world0 = init_state_v6(O.FX)
    world0["fault_ob"] = 1
    gold = O._golden_traj(AD.init_claimstate(), world0, batches, 1)

    def _traj(reducer):
        claim = AD.init_claimstate()
        world = copy.deepcopy(world0)
        out = []
        step, _ = C.compile_step_v6(view)
        for e, batch in enumerate(batches):
            claim, cfg_map, resets = AD.admit_step(claim, batch, 1 + e, fx)
            ec = C.enc_config_bundle(view, cfg_map, resets)
            world = C.dec_state_v6(view, reducer(
                f"(({step} {ec}) {C.enc_state_v6(view, world)})"))
            out.append(copy.deepcopy(world))
        return out

    ref = _traj(O.norm)
    p11r = all(ref[e] == gold[e][0] for e in range(len(batches)))
    p11n = None
    if not SKIP_NATIVE:
        nat = _traj(O.native)
        p11n = all(nat[e] == gold[e][0] for e in range(len(batches)))
    rep(p11r, p11n, "P11) a quarter_turn_z world runs ic_ref == ic32 == golden")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-qtz] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] quarter_turn_z is the geometry-dependent symmetric integer "
          "projection (round(2^n/sqrt2),0,0,round(2^n/sqrt2)) under "
          "forge_named_rotor_rne_sym_v1 -- no residual, exact-integer round, "
          "scalar>0. The policy id is build provenance; the projected rotor (not "
          "the name) enters the identity, so the id is geometry-dependent while "
          "the sugar still washes out to its numeric twin.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
