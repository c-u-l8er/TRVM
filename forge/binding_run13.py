"""binding_run13.py -- Phase 3B.5.1: tooling-contract closure (H1-H15).

The 3B.5.1 hardening slice (GPT-5.6's pre-Spinner-Bench ruling) tightens the four
seams the 3B ergonomics tools leaned on but never sealed:

  1. EXACT KEY SETS. A sealed ForgeSemanticArtifactV1 / semantic_policies / object
     record / edge record / per-role static_config must reveal EXACTLY its frozen
     fields. An unknown field is a typed WRL_UNKNOWN_ARTIFACT_FIELD rejection
     BEFORE sealing -- never silently dropped by canonicalization (H1-H6).
  2. SEALED vs TOLERANT DIFF. `wrl_diff.semantic_diff` seals+validates both sides
     and guarantees the SemanticArtifactID bridge (rejecting invalid/unsupported
     artifacts); `wrl_diff.draft_diff` is tolerant and makes NO identity claim,
     so it can preview future/unsupported profiles (H7-H10).
  3. AUTHORITATIVE REGISTRIES. Config keys (`wrl_canonical.ROLE_CONFIG_SCHEMA`),
     the named-rotor table and the concise-clock forms (`wrl_sugar`) are single-
     sourced; every layer (validator/formatter/sugar/completion) consumes them,
     so completion reads the grammar rather than mirroring it (H11-H12).
  4. CANONICAL SEMANTIC LOCATORS. A WrlValidationError now carries ObjectKey /
     EdgeKey locators + a dotted field_path on the IDENTITY SPINE (no spans/
     filenames); wrl_diagnostics maps them through the WrlSourceMap to spans/
     canvas, keeping the 3B-1 sidecar the only holder of source geometry (H13-H14).

  H1  unknown top-level artifact field -> WRL_UNKNOWN_ARTIFACT_FIELD before seal
  H2  unknown semantic_policies field -> rejected (field_path semantic_policies.*)
  H3  unknown object-record field -> rejected, carries ObjectKey locator
  H4  unknown per-role static_config field (Pulser clock-only / Spinner w,n,...)
  H5  unknown edge-record field -> rejected
  H6  every valid world still seals; the id is stable across a re-seal / SealedArtifact
  H7  semantic_diff bridge: is_empty() == (sem_a == sem_b) over an edit matrix
  H8  semantic_diff REJECTS a v2/unknown-field artifact; draft_diff TOLERATES v2
  H9  semantic_diff accepts a SealedArtifact and agrees with the raw-dict path
  H10 on two SEALABLE artifacts draft_diff == semantic_diff; diff_artifacts alias
  H11 ROLE_CONFIG_SCHEMA is single-sourced (completion == schema; worlds subset)
  H12 NAMED_ROTOR_TABLE / CLOCK_SUGAR_FORMS single-sourced across sugar+completion
  H13 structural rejects carry canonical ObjectKey/EdgeKey locators + field_path
  H14 wrl_diagnostics maps locators -> spans, carries them, stable under reformat
  H15 the hardened pipeline still runs ic_ref == ic32 == golden        (native)

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
import wrl_diff as DF
import wrl_complete as CP
import wrl_sugar as SG
import wrl_diagnostics as DG
import wrl_plan as P
import compiler as C
import admit as AD
import binding_run3o as O
import binding_run7 as B7
from admit import mk_claim
from fixture import init_state_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"


def _rejects(fn, code):
    """True iff `fn()` raises a WrlValidationError with `code`; returns the
    exception too so the caller can inspect its locators."""
    try:
        fn()
        return False, None
    except WC.WrlValidationError as e:
        return e.code == code, e


# small crafted worlds that PARSE but fail validate_graph (for the locators)
BAD_CLOCK = ("profile forge.world.core.v1; periods 1\n"
             "[pulser:p0](mode=periodic, period=0, phase=0){sig_out}\n"
             "[door:d0]{sig_in}\n"
             "[p0] --sig--> [d0]\n")
UNKNOWN_EP = ("profile forge.world.core.v1; periods 1\n"
              "[pulser:p0](mode=periodic, period=1, phase=0){sig_out}\n"
              "[door:d0]{sig_in}\n"
              "[p0] --sig--> [dX]\n")
WIRE_ORB = ("profile forge.world.core.v1; periods 1\n"
            "[pulser:p0](mode=periodic, period=1, phase=0){sig_out}\n"
            "[orb:ob]{pose}\n"
            "[p0] --sig--> [ob]\n")


def main():
    print("[BINDING wrl-3b5.1] tooling-contract closure")
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

    WORLDS = B7.WORLDS
    base = W.parse_wrl_legacy_document(B7.W_CORE)
    art = W.graph_to_ir(base)

    # ---- H1 unknown top-level field -> rejected BEFORE sealing
    a = copy.deepcopy(art); a["bogus"] = 1
    ok1a, _ = _rejects(lambda: WC.validate_artifact_v1(a),
                       WC.WRL_UNKNOWN_ARTIFACT_FIELD)
    ok1b, _ = _rejects(lambda: WC.semantic_artifact_id(a),
                       WC.WRL_UNKNOWN_ARTIFACT_FIELD)   # id path rejects too
    rep(ok1a and ok1b, None, "H1) unknown top-level artifact field -> "
                             "WRL_UNKNOWN_ARTIFACT_FIELD before sealing")

    # ---- H2 unknown policy field -> rejected with a policy field_path
    a = copy.deepcopy(art); a["semantic_policies"]["extra"] = 1
    ok2, e2 = _rejects(lambda: WC.validate_artifact_v1(a),
                       WC.WRL_UNKNOWN_ARTIFACT_FIELD)
    ok2 = ok2 and e2.field_path == "semantic_policies.extra"
    rep(ok2, None, "H2) unknown semantic_policies field -> rejected "
                   "(field_path semantic_policies.extra)")

    # ---- H3 unknown object field -> rejected, carries ObjectKey locator
    a = copy.deepcopy(art); a["objects"][0]["color"] = "red"
    ok3, e3 = _rejects(lambda: WC.validate_artifact_v1(a),
                       WC.WRL_UNKNOWN_ARTIFACT_FIELD)
    ok3 = ok3 and isinstance(e3.primary_locator, WC.ObjectKey)
    rep(ok3, None, "H3) unknown object-record field -> rejected, carries "
                   "an ObjectKey locator")

    # ---- H4 unknown per-role static_config field (Pulser vs Spinner)
    def add_sc(a, role, key):
        for o in a["objects"]:
            if o["role"] == role:
                o["static_config"][key] = 1
                return
    ap = copy.deepcopy(art); add_sc(ap, "Pulser", "period")   # clock-only role
    ok4p, e4p = _rejects(lambda: WC.validate_artifact_v1(ap),
                         WC.WRL_UNKNOWN_ARTIFACT_FIELD)
    ok4p = ok4p and e4p.field_path == "static_config.period"
    asp = copy.deepcopy(art); add_sc(asp, "Spinner", "gain")
    ok4s, e4s = _rejects(lambda: WC.validate_artifact_v1(asp),
                         WC.WRL_UNKNOWN_ARTIFACT_FIELD)
    ok4s = ok4s and e4s.field_path == "static_config.gain"
    rep(ok4p and ok4s, None, "H4) unknown per-role static_config field -> "
                             "rejected (Pulser clock-only / Spinner w,n,...)")

    # ---- H5 unknown edge-record field -> rejected
    a = copy.deepcopy(art); a["edges"][0]["weight"] = 9
    ok5, _ = _rejects(lambda: WC.validate_artifact_v1(a),
                      WC.WRL_UNKNOWN_ARTIFACT_FIELD)
    rep(ok5, None, "H5) unknown edge-record field -> rejected")

    # ---- H6 every valid world still seals; id stable across re-seal + Sealed
    ok6 = True
    for _n, src in WORLDS:
        av = W.graph_to_ir(W.parse_wrl_legacy_document(src))
        sid = WC.semantic_artifact_id(av)
        if (WC.semantic_artifact_id(av) != sid
                or WC.SealedArtifact(av).semantic_id != sid):
            ok6 = False
    rep(ok6, None, "H6) every valid world still seals; id stable across "
                   "re-seal / SealedArtifact")

    # ---- H7 semantic_diff bridge law over an edit matrix
    rotor_edit = W.parse_wrl_legacy_document(B7.W_CORE.replace("rotor=16.0.0.0",
                                                    "rotor=0.16.0.0"))
    no_socket = W.parse_wrl_legacy_document("\n".join(
        ln for ln in B7.W_CORE.splitlines() if "--socket--" not in ln))
    arts = [art, W.graph_to_ir(rotor_edit), W.graph_to_ir(no_socket)]
    ok7 = True
    for ga in arts:
        for gb in arts:
            empty = DF.semantic_diff(ga, gb).is_empty()
            same = (WC.semantic_artifact_id(ga) == WC.semantic_artifact_id(gb))
            if empty != same:
                ok7 = False
    rep(ok7, None, "H7) semantic_diff bridge: is_empty() == (sem_a == sem_b) "
                   "over an edit matrix")

    # ---- H8 semantic_diff rejects v2/unknown-field; draft_diff tolerates v2
    v2 = copy.deepcopy(art); v2["profile_id"] = "forge.world.core.v2"
    ok8a, _ = _rejects(lambda: DF.semantic_diff(art, v2),
                       WC.WRL_UNSUPPORTED_FEATURE)
    bad = copy.deepcopy(art); bad["bogus"] = 1
    ok8b, _ = _rejects(lambda: DF.semantic_diff(art, bad),
                       WC.WRL_UNKNOWN_ARTIFACT_FIELD)
    dd = DF.draft_diff(art, v2)
    ok8c = ([c.kind for c in dd.changes] == [DF.PROFILE_CHANGED])
    rep(ok8a and ok8b and ok8c, None, "H8) semantic_diff REJECTS v2/unknown-"
                                      "field; draft_diff TOLERATES v2 (PROFILE_CHANGED)")

    # ---- H9 semantic_diff accepts a SealedArtifact and agrees with raw dict
    sealed = WC.SealedArtifact(art)
    sealed2 = WC.SealedArtifact(arts[1])
    ok9 = (DF.semantic_diff(sealed, sealed2).changes
           == DF.semantic_diff(art, arts[1]).changes
           and DF.semantic_diff(sealed, sealed).is_empty())
    rep(bool(ok9), None, "H9) semantic_diff accepts a SealedArtifact and agrees "
                         "with the raw-dict path")

    # ---- H10 on two sealable artifacts draft_diff == semantic_diff (+ alias)
    ok10 = (DF.draft_diff(art, arts[1]).changes
            == DF.semantic_diff(art, arts[1]).changes
            == DF.diff_artifacts(art, arts[1]).changes)
    rep(ok10, None, "H10) on two sealable artifacts draft_diff == semantic_diff "
                    "== diff_artifacts alias")

    # ---- H11 ROLE_CONFIG_SCHEMA single-sourced
    ok11 = True
    for rid in WC.ROLE_IDS:
        want = tuple(WC.ROLE_CONFIG_SCHEMA[rid]["surface_keys"])
        if tuple(CP.config_key_completions(rid)) != want:
            ok11 = False
    for _n, src in WORLDS:
        av = W.graph_to_ir(W.parse_wrl_legacy_document(src))
        for o in av["objects"]:
            allowed = set(WC.ROLE_CONFIG_SCHEMA[o["role"]]["static_config_keys"])
            if not set(o["static_config"]) <= allowed:
                ok11 = False
    rep(ok11, None, "H11) ROLE_CONFIG_SCHEMA single-sourced (completion == "
                    "schema; every world's static_config keys subset)")

    # ---- H12 NAMED_ROTOR_TABLE / CLOCK_SUGAR_FORMS single-sourced
    ok12 = (SG.ROTOR_TABLE_NAMES == tuple(SG.NAMED_ROTOR_TABLE)
            and set(CP.named_rotor_completions()) == set(SG.ALL_ROTOR_NAMES)
            and tuple(CP.clock_form_completions()) == tuple(SG.CLOCK_SUGAR_FORMS))
    for nm in SG.NAMED_ROTOR_TABLE:
        for n in (4, 8, 16):
            if SG.NAMED_ROTOR_TABLE[nm](n) != SG.named_rotor(nm, n):
                ok12 = False
    rep(ok12, None, "H12) NAMED_ROTOR_TABLE / CLOCK_SUGAR_FORMS single-sourced "
                    "across sugar + completion")

    # ---- H13 structural rejects carry canonical locators + field_path
    okc, ec = _rejects(lambda: WC.validate_graph(W.parse_wrl_legacy_document(BAD_CLOCK)),
                       WC.WRL_CLOCK_RANGE)
    okc = okc and ec.primary_locator == WC.ObjectKey("p0") \
        and ec.field_path == "static_config.clock"
    oke, ee = _rejects(lambda: WC.validate_graph(W.parse_wrl_legacy_document(UNKNOWN_EP)),
                       WC.WRL_UNKNOWN_ENDPOINT)
    oke = oke and isinstance(ee.primary_locator, WC.EdgeKey) \
        and ee.field_path == "dst"
    okp, ep = _rejects(lambda: WC.validate_graph(W.parse_wrl_legacy_document(WIRE_ORB)),
                       WC.WRL_ILLEGAL_PORT_PAIR)
    okp = okp and isinstance(ep.primary_locator, WC.EdgeKey) \
        and ep.related_locator == WC.ObjectKey("ob")
    rep(okc and oke and okp, None, "H13) structural rejects carry canonical "
                                   "ObjectKey/EdgeKey locators + field_path")

    # ---- H14 diagnostics maps locators -> spans, carries them, stable reformat
    dc = DG.diagnose_core(BAD_CLOCK)[0]
    de = DG.diagnose_core(UNKNOWN_EP)[0]
    dp = DG.diagnose_core(WIRE_ORB)[0]
    ok14 = (dc.primary_locator == WC.ObjectKey("p0")
            and dc.field_path == "static_config.clock"
            and dc.canonical_object_id == "p0" and dc.primary_span is not None
            and de.canonical_object_id == "dX" and de.field_path == "dst"
            and isinstance(de.primary_locator, WC.EdgeKey)
            and de.primary_span is not None
            and dp.canonical_object_id == "ob" and dp.primary_span is not None)
    # locators/oid are STABLE under a reformat (only spans may move). The world
    # rejects, so the canonical formatter (which validates) cannot touch it; a
    # textual reflow -- extra blank/comment lines shifting every span -- serves.
    r1 = DG.diagnose_core(BAD_CLOCK)[0]
    r2 = DG.diagnose_core("\n; leading note\n\n" + BAD_CLOCK)[0]
    ok14 = ok14 and (r1.primary_locator == r2.primary_locator
                     and r1.field_path == r2.field_path
                     and r1.canonical_object_id == r2.canonical_object_id
                     and r1.primary_span.start_line != r2.primary_span.start_line)
    rep(ok14, None, "H14) diagnostics maps locators -> spans, carries them, "
                    "stable under reformat")

    # ---- H15 the hardened pipeline still runs ic_ref == ic32 == golden
    prog = W.lower_program(B7.W_CORE, W.parse_wrl_legacy_document)
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
    h15r = all(ref[e] == gold[e][0] for e in range(len(batches)))
    h15n = None
    if not SKIP_NATIVE:
        nat = _traj(O.native)
        h15n = all(nat[e] == gold[e][0] for e in range(len(batches)))
    rep(h15r, h15n, "H15) the hardened pipeline runs ic_ref == ic32 == golden")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-3b5.1] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] exact key sets reject stray fields before sealing; the diff "
          "is split into a sealed identity-bridge mode and a tolerant draft mode; "
          "config/rotor/clock vocabularies are single-sourced; and rejections "
          "carry canonical ObjectKey/EdgeKey locators the sidecar maps to spans "
          "-- all four seams close with the identity spine untouched.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
