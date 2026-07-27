"""binding_run11.py -- Phase 3B-4: named rotor constants + concise clocks (N1-N9).

3B-4 adds surface SUGAR that canonicalizes to the frozen numeric values via a
source-to-source PRE-PASS (`wrl_sugar.desugar_core`) in front of the UNTOUCHED
`parse_wrl_legacy_document`. So a sugared program and its numeric twin lower to identical
bytes -- sugar can never introduce a new identity, and the canonical formatter
(3B-2) still emits the numeric surface, so sugar washes out like whitespace.

  N1  each EXACT named rotor lowers to the same SemanticArtifactID as its
      numeric twin (over two spinner geometries -- shows the n-dependence)
  N2  each concise clock lowers to the same SemanticArtifactID as its verbose form
  N3  the frozen exact table values (identity + axis 180-degree reversals)
  N4  desugar is idempotent and a no-op on already-numeric source
  N5  the formatter emits the numeric surface (named sugar washes out)
  N6  an unknown named rotor and a named rotor with no spinner n are typed
      WRL_UNSUPPORTED_FEATURE rejections (never guessed). NOTE quarter_turn_z is
      now an ACCEPTED policy-governed rotor -- its parity lives in binding_run14.
  N7  3B-3 diagnostics still fire through desugar (a dup id in a sugared source)
  N8  a full sugared world (named rotor + concise clock) == its numeric twin
      (sealed bytes + sem id)
  N9  a sugared world runs ic_ref == ic32 == golden                (native)

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import os
import sys
import copy
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import wrl_ir as W
import wrl_canonical as WC
import wrl_sugar as SG
import wrl_format as F
import wrl_diagnostics as DG
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


def _pulser_world(clock_expr):
    return ("profile forge.world.core.v1\nperiods 1\n"
            "[pulser:p0](%s)\n[door:d0]\n[p0] --sig--> [d0]\n" % (clock_expr,))


def _sem(src, sugared):
    parse = SG.parse_legacy_sugared if sugared else W.parse_wrl_legacy_document
    return W.lower_program(src if sugared else src, parse).semantic_artifact_id


def main():
    print("[BINDING wrl-3b4] named rotor constants + concise clocks")
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

    GEOM = [(8, 4), (16, 8)]
    NAMES = ["identity", "reverse_x", "reverse_y", "reverse_z"]

    # ---- N1 named rotor == numeric twin (per name, per geometry)
    n1 = True
    for w, n in GEOM:
        for name in NAMES:
            lanes = SG.named_rotor(name, n)
            numeric = ".".join(str(v) for v in lanes)
            a = W.lower_program(SG.desugar_core(_spinner_world(name, w, n)),
                                W.parse_wrl_legacy_document)
            b = W.lower_program(_spinner_world(numeric, w, n), W.parse_wrl_legacy_document)
            if (a.semantic_artifact_id != b.semantic_artifact_id
                    or a.sealed_artifact.artifact != b.sealed_artifact.artifact):
                n1 = False
    rep(n1, None, "N1) each exact named rotor == its numeric twin "
                  "(4 names x 2 geometries)")

    # ---- N2 concise clock == verbose form
    n2 = True
    clock_pairs = [("every 2", "mode=periodic, period=2, phase=0"),
                   ("every 3, phase 1", "mode=periodic, period=3, phase=1"),
                   ("once at 5", "mode=once, epoch=5")]
    for concise, verbose in clock_pairs:
        a = W.lower_program(SG.desugar_core(_pulser_world(concise)),
                            W.parse_wrl_legacy_document)
        b = W.lower_program(_pulser_world(verbose), W.parse_wrl_legacy_document)
        if (a.semantic_artifact_id != b.semantic_artifact_id
                or a.sealed_artifact.artifact != b.sealed_artifact.artifact):
            n2 = False
    rep(n2, None, "N2) each concise clock == its verbose form")

    # ---- N3 the frozen exact table values
    n3 = (SG.named_rotor("identity", 4) == (16, 0, 0, 0)
          and SG.named_rotor("reverse_x", 4) == (0, 16, 0, 0)
          and SG.named_rotor("reverse_y", 4) == (0, 0, 16, 0)
          and SG.named_rotor("reverse_z", 4) == (0, 0, 0, 16)
          and SG.named_rotor("identity", 8) == (256, 0, 0, 0)
          and SG.named_rotor("reverse_x", 8) == (0, 256, 0, 0))
    rep(n3, None, "N3) frozen exact table (identity + axis 180-degree reversals) "
                  "= (2^n,0,0,0) etc.")

    # ---- N4 idempotent + no-op on numeric
    n4 = True
    for w, n in GEOM:
        named = _spinner_world("identity", w, n)
        d1 = SG.desugar_core(named)
        d2 = SG.desugar_core(d1)
        numeric = _spinner_world(".".join(str(v) for v in
                                          SG.named_rotor("identity", n)), w, n)
        if d1 != d2 or SG.desugar_core(numeric) != numeric:
            n4 = False
    rep(n4, None, "N4) desugar is idempotent and a no-op on numeric source")

    # ---- N5 the formatter emits the numeric surface (named washes out)
    n5 = True
    for w, n in GEOM:
        lanes = ".".join(str(v) for v in SG.named_rotor("reverse_z", n))
        fa = F.format_wrl_core(SG.parse_legacy_sugared(_spinner_world("reverse_z",
                                                                    w, n)))
        fb = F.format_wrl_core(W.parse_wrl_legacy_document(_spinner_world(lanes, w, n)))
        if fa != fb or "reverse_z" in fa:
            n5 = False
    rep(n5, None, "N5) the formatter emits the numeric surface (named sugar "
                  "washes out)")

    # ---- N6 unknown named rotor + missing-n are typed rejects
    # (quarter_turn_z is now an ACCEPTED policy-governed rotor -- see binding_run14;
    # the reject cases here are a genuinely-unknown name + a missing spinner n.)
    n6 = True
    try:
        SG.parse_legacy_sugared(_spinner_world("barrel_roll", 8, 4))
        n6 = False
    except WC.WrlValidationError as e:
        n6 = n6 and e.code == WC.WRL_UNSUPPORTED_FEATURE
    # a named rotor with no n on the declaration
    try:
        SG.desugar_core("profile forge.world.core.v1\nperiods 1\n"
                        "[spinner:sp](w=8, rotor=identity)\n")
        n6 = False
    except WC.WrlValidationError as e:
        n6 = n6 and e.code == WC.WRL_UNSUPPORTED_FEATURE
    rep(n6, None, "N6) unknown name + missing-n are typed "
                  "WRL_UNSUPPORTED_FEATURE rejects (never guessed)")

    # ---- N7 3B-3 diagnostics fire through desugar
    dup = ("profile forge.world.core.v1\nperiods 1\n"
           "[pulser:p0](every 2)\n"
           "[spinner:sp](w=8, n=4, rotor=identity)\n"
           "[spinner:sp](w=8, n=4, rotor=identity)\n"
           "[orb:ob]\n[p0] --sig--> [sp]\n[sp] --socket--> [ob]\n")
    d = DG.diagnose_legacy_document(SG.desugar_core(dup))
    n7 = (len(d) == 1 and d[0].code == WC.WRL_DUPLICATE_ID
          and d[0].canonical_object_id == "sp")
    rep(n7, None, "N7) 3B-3 diagnostics fire through desugar (dup id in a "
                  "sugared source)")

    # ---- N8 a full sugared world == its numeric twin (bytes + sem id)
    named_full = B7.W_CORE.replace("rotor=16.0.0.0", "rotor=identity") \
        .replace("(mode=periodic, period=2, phase=0)", "(every 2)")
    a = W.lower_program(SG.desugar_core(named_full), W.parse_wrl_legacy_document)
    b = W.lower_program(B7.W_CORE, W.parse_wrl_legacy_document)
    n8 = (a.semantic_artifact_id == b.semantic_artifact_id
          and a.sealed_artifact.artifact == b.sealed_artifact.artifact)
    rep(n8, None, "N8) a full sugared world (named rotor + concise clock) == "
                  "its numeric twin (bytes + sem id)")

    # ---- N9 a sugared world runs ic_ref == ic32 == golden (native)
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
    n9r = all(ref[e] == gold[e][0] for e in range(len(batches)))
    n9n = None
    if not SKIP_NATIVE:
        nat = _traj(O.native)
        n9n = all(nat[e] == gold[e][0] for e in range(len(batches)))
    rep(n9r, n9n, "N9) a sugared world runs ic_ref == ic32 == golden")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-3b4] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] sugar is a source-to-source pre-pass in front of the "
          "untouched parser; it canonicalizes to frozen numerics, so it can "
          "never move an identity. The policy-governed rotor quarter_turn_z "
          "(forge_named_rotor_rne_sym_v1) is exercised in binding_run14.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
