"""binding_run23.py -- v0.5-0 Source Surface Closure THROUGH THE LIVE ENDPOINTS
(Spinner Bench).

v0.4-5 closed the editing UI (source -> commit -> run). GPT-5.6 then ruled a
correctness gap first: the editor seed shipped run-input syntax (`periods N`) and
the ergonomic WRL sugar (`every 2`, `rotor=quarter_turn_z`) that the Apply path
parsed WITHOUT desugaring, so pasting the seed back leaked a raw `KeyError` instead
of Applying. v0.5-0 makes the world source a CLOSED surface:

  * the editor seed (DEMO_WORLD_SOURCE) is WORLD-ONLY -- it carries no `periods` /
    `[epoch:N]` run-input syntax; run inputs live in the two named ScenarioV1
    documents (GOLDEN_DEMO_SCENARIO / ACCEPTANCE_BENCH_SCENARIO);
  * `replace_world_source` SCANS the raw source for forbidden run-input syntax
    FIRST, then DESUGARS approved WRL sugar (a source-to-source pre-pass, NOT a
    compiler gate), then parses the desugared core, then seals -- so a sugar
    spelling and its numeric expansion seal to the SAME SemanticArtifactID;
  * every desugar/parse failure crosses the endpoint as a stable TYPED diagnostic
    (WRL_SUGAR_MALFORMED / a WrlUnsupported code), never a raw Python exception.

This battery drives the ACTUAL endpoint helpers (`spinner_bench._draft_*_payload`),
the same server path an operator's clicks take (M1-M5):

  M1  the default editor world source is WORLD-ONLY (no scenario syntax) and
      round-trips through Apply as a semantic no-op;
  M2  a sugar Apply and the canonical numeric Apply of the SAME edited world
      produce the SAME candidate SemanticArtifactID (both valid, both != demo id);
  M3  a sugar-only re-expression of the current graph is a genuine semantic no-op
      (status semantic_noop, revision unchanged);
  M4  invalid sugar returns a TYPED WRL diagnostic through the endpoint and NEVER a
      raw Python exception (the endpoint stays ok:True with status syntax_error);
  M5  NATIVE -- the sugar-Applied edited world (re-lowered from its canonical view
      text) folds ic_ref == ic32 == the independent Fixture oracle over its demo
      scenario.

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
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
import wrl_sugar as SG
import wrl_scenario as SC
import wrl_draft as D
import spinner_bench as SB
from admit import film_hash_v7
from fixture import init_state_v6, state_to_film_args_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

# a WORLD-ONLY edit (drops the once-at-1 pulser + its door) that KEEPS the
# ergonomic sugar (`every 2`, `rotor=quarter_turn_z`). Its numeric twin is the
# desugared core -- they must seal to the same candidate id (M2).
SUGAR_EDIT = """profile forge.world.core.v1

[pulser:p0](every 2){sig_out}
[relay:r0]{sig_in, sig_out}
[spinner:sp](w=16, n=8, rotor=quarter_turn_z, configurable){sig_in, socket}
[orb:ob]{pose}

[pulser:p0] --sig--> [relay:r0]
[relay:r0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]
"""
NUMERIC_EDIT = SG.desugar_core(SUGAR_EDIT)

# malformed sugar spellings -- each must become a TYPED diagnostic, never a raise
BAD_ROTOR = SUGAR_EDIT.replace("rotor=quarter_turn_z", "rotor=totally_unknown")
BAD_CLOCK = SUGAR_EDIT.replace("(every 2)", "(every)")


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


def _source_req(session_id, replace_id, source):
    return {"session_id": session_id, "replace_id": replace_id, "source": source}


def main():
    print("[BINDING wrl-v0.5-0] Source Surface Closure via live endpoints (M1-M5)")
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

    sem = SB.DEMO_WORLD_SEMANTIC_ID

    # ---- M1 the default editor world source is WORLD-ONLY --------------------
    scan = D._scan_world_source_scenario(SB.DEMO_WORLD_SOURCE)
    SB._draft_reset_payload("m1")
    r1 = SB._draft_source_payload(_source_req("m1", "m1-1", SB.DEMO_WORLD_SOURCE))
    m1 = (scan is None and r1["ok"]
          and r1["apply"]["status"] == "semantic_noop"
          and r1["apply"]["candidate_semantic_id"] == sem
          and r1["view"]["semantic_revision"] == 0)
    rep(m1, None,
        "M1) the default editor world source is WORLD-ONLY (no scenario syntax) "
        "and round-trips through Apply as a semantic no-op")

    # ---- M2 sugar Apply == canonical numeric Apply (same id) -----------------
    SB._draft_reset_payload("m2a")
    ra = SB._draft_source_payload(_source_req("m2a", "m2a-1", SUGAR_EDIT))
    SB._draft_reset_payload("m2b")
    rb = SB._draft_source_payload(_source_req("m2b", "m2b-1", NUMERIC_EDIT))
    ca = ra["apply"]["candidate_semantic_id"]
    cb = rb["apply"]["candidate_semantic_id"]
    m2 = (ra["ok"] and rb["ok"]
          and ra["apply"]["status"] == "candidate_valid"
          and rb["apply"]["status"] == "candidate_valid"
          and ca is not None and ca == cb and ca != sem
          and "period" in NUMERIC_EDIT      # the desugar actually expanded sugar
          and "every 2" not in NUMERIC_EDIT)
    rep(m2, None,
        "M2) a sugar Apply and the canonical numeric Apply of the SAME edited "
        "world produce the SAME candidate id (both valid, both != demo id)")

    # ---- M3 sugar-only re-expression of the current graph is a no-op ---------
    SB._draft_reset_payload("m3")
    r3 = SB._draft_source_payload(_source_req("m3", "m3-1", SB.DEMO_WORLD_SOURCE))
    m3 = (r3["ok"] and r3["apply"]["status"] == "semantic_noop"
          and r3["apply"]["semantic_noop"] is True
          and r3["apply"]["candidate_semantic_id"] == sem
          and r3["view"]["semantic_revision"] == 0)
    rep(m3, None,
        "M3) a sugar-only re-expression of the current graph is a genuine "
        "semantic no-op (status semantic_noop, revision unchanged)")

    # ---- M4 invalid sugar -> TYPED diagnostic, NEVER a Python exception ------
    SB._draft_reset_payload("m4")
    r4a = SB._draft_source_payload(_source_req("m4", "m4-1", BAD_ROTOR))
    r4b = SB._draft_source_payload(_source_req("m4", "m4-2", BAD_CLOCK))
    typed = {D.WRL_SUGAR_MALFORMED, "WRL_UNSUPPORTED_FEATURE"}
    ok4a = (r4a["ok"] and r4a["apply"]["status"] == "syntax_error"
            and r4a["apply"]["diagnostics"]
            and r4a["apply"]["diagnostics"][0]["code"] in typed
            # draft untouched: still the demo id, revision 0
            and r4a["view"]["semantic_revision"] == 0
            and r4a["view"]["candidate_semantic_id"] == sem)
    ok4b = (r4b["ok"] and r4b["apply"]["status"] == "syntax_error"
            and r4b["apply"]["diagnostics"]
            and r4b["apply"]["diagnostics"][0]["code"] in typed
            and r4b["view"]["semantic_revision"] == 0)
    m4 = ok4a and ok4b
    rep(m4, None,
        "M4) invalid sugar returns a TYPED WRL diagnostic through the endpoint "
        "and NEVER a raw Python exception (endpoint stays ok:True, syntax_error, "
        "draft untouched)")

    # ---- M5 NATIVE: the sugar-Applied world folds ic_ref == ic32 == oracle ---
    txt5 = SB._draft_payload("m2a")["view"]["text"]       # canonical numeric WRL
    prog5 = W.lower_program(txt5, W.parse_wrl_core)
    view5 = P.plan_view(P.artifact_to_compile_plan_v1(prog5.sealed_artifact))
    fx5 = prog5.as_fixture_for_test()
    scen5 = SC.demo_scenario(prog5.semantic_artifact_id)
    ifa5, scr5 = SC.scenario_to_script(scen5)
    ref5 = _fold_films(view5, O.norm, ifa5, scr5)
    orc5 = _fold_fixture(fx5, view5, O.norm, ifa5, scr5)
    m5r = (prog5.semantic_artifact_id == ca and ref5 == orc5)
    m5n = None
    if not SKIP_NATIVE:
        m5n = (_fold_films(view5, O.native, ifa5, scr5) == ref5)
    rep(m5r, m5n,
        "M5) NATIVE -- the sugar-Applied edited world (re-lowered from its "
        "canonical view text) folds ic_ref == ic32 == the Fixture oracle")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.5-0] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.5-0 closes the world SOURCE surface: the editor seed is "
          "world-only (M1), the Apply path desugars approved WRL sugar as a "
          "source pre-pass so a sugar spelling and its numeric twin seal to the "
          "SAME id (M2) and a sugar-only re-expression is a true no-op (M3), and "
          "every malformed spelling crosses the endpoint as a TYPED diagnostic "
          "rather than a raw Python exception (M4). The sugar-Applied world stays "
          "natively runnable ic_ref == ic32 == oracle (M5). NO new runtime "
          "construct; desugar is a source-to-source pre-pass, not a compiler gate.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
