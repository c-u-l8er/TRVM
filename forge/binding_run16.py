"""binding_run16.py -- v0.4-0 document-boundary preflight (Spinner Bench v0.4).

GPT-5.6's v0.4 ruling froze the edit semantics, then ordered the migration slice
FIRST: v0.4-0 separates the three documents cleanly at the IDENTITY layer before
any editing UI is built. This battery proves the three v0.4-0 corrections plus the
two identity-preservation guards from the required v0.4 battery (E1-E4, E17, E21):

  E1  CanvasLayoutV1 carries NO run inputs and NO semantic config. `graph_to_
      layout` emits only {layout_version, profile_id, nodes[object_id,
      presentation], edges[edge_key, presentation]}; `validate_layout_v1` is a
      typed structural gate that REJECTS an injected `periods`, an injected
      per-node `static_config`, and an injected batch field (they are unknown
      here -- run inputs belong to ScenarioV1, semantic config to WorldDraftV1);
      the `layout_from_canvas_v1` compatibility loader projects a legacy
      `canvas.v1` (which DOES carry periods/batches/static_config) down to the
      presentation-only layout, dropping every run input + semantic key, and the
      result validates.
  E2  A LABEL-ONLY ScenarioV1 edit preserves the ScenarioDigest: relabelling
      every epoch (identical runtime inputs) leaves `scenario_digest` fixed,
      while a CLAIM edit still moves it (labels are documentation, not runtime
      identity -- v0.4-0 ruling #2).
  E3  A label-only edit UPDATES the displayed labels even though the trajectory
      cache HITS on the label-free digest: a cold `_run_traj` populates the cache
      keyed by (sem, reducer, ScenarioDigest); a warm run with a relabelled (but
      runtime-identical) scenario returns the SAME digest and byte-identical
      films from the cache, yet the rows carry the NEW labels (else a label edit
      would show stale cached labels -- v0.4-0 ruling #2 read path).
  E4  Scenario/world binding is ENFORCED at run time: `_resolve_scenario` (and
      `check_world_binding`) refuse a scenario authored against a DIFFERENT world
      with a typed WRL_SCENARIO_WORLD_MISMATCH, while a correctly-bound scenario
      resolves and folds normally (v0.4-0 ruling #3). Structural validation still
      ACCEPTS the out-of-world CLAIM target (`zz`) -- that is a Rejected-receipt
      case, not a world mismatch.
  E17 A pre-existing unknown-target claim (`zz`) remains a VALID scenario: it
      passes structural validation and folds to a Rejected(unknown_spinner)
      receipt at ep7 -- the migration did not break the intentional-rejection
      path.
  E21 The Golden ADMIT Demo and the ADMIT Acceptance Bench are UNCHANGED by the
      migration: demo_scenario folded via the plan/view path still reproduces the
      historical hard-coded SCRIPT films byte-for-byte; bench_scenario still
      latches the orb fault on the [0,0,0,0,0,1,0,1,1] schedule; both are
      ic_ref == ic32 (native). Identity-preservation of the format change is
      proved directly: canonical WORLD formatting now OMITS the `periods` line
      and the inline claim batches, yet re-parses to the SAME SemanticArtifactID,
      and adding/removing an explicit `periods` line never moves the id (periods
      and batches never entered the SemanticArtifactID -- D3).

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
import wrl_sugar as SG
import wrl_plan as P
import wrl_format as F
import compiler as C
import admit as AD
import binding_run3o as O
import wrl_canonical as WC
import wrl_canvas as CV
import wrl_scenario as SC
import spinner_bench as SB
from admit import film_hash_v7
from fixture import init_state_v6, state_to_film_args_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"


def _fold_films(view, reducer, initial_faults, script):
    """Fold a (initial_faults, script) through the compiled step over the plan
    VIEW -- the production contract spinner_bench._run_traj uses -- returning
    (films, worlds). No Fixture is reconstructed."""
    world = init_state_v6(view)
    for o in initial_faults:
        if ("fault_" + o) in world:
            world["fault_" + o] = 1
    claim = AD.init_claimstate()
    step, _ = C.compile_step_v6(view)
    films, worlds = [], []
    for e, (label, batch) in enumerate(script):
        ep = 1 + e
        claim, cfg_map, resets = AD.admit_step(claim, batch, ep, view)
        ec = C.enc_config_bundle(view, cfg_map, resets)
        world = C.dec_state_v6(view, reducer(
            f"(({step} {ec}) {C.enc_state_v6(view, world)})"))
        films.append(film_hash_v7(*state_to_film_args_v6(view, world, ep),
                                  state=claim))
        worlds.append({k: (list(v) if isinstance(v, tuple) else v)
                       for k, v in world.items()})
    return films, worlds


def _relabel(scn):
    """Return a deep copy of a ScenarioV1 with every epoch label rewritten (a
    pure label-only edit -- runtime inputs untouched)."""
    out = copy.deepcopy(scn)
    for e in out["epochs"]:
        e["label"] = "EDITED LABEL @ epoch %d" % e["epoch"]
    return out


def main():
    print("[BINDING wrl-v0.4-0] document-boundary preflight (E1-E4, E17, E21)")
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

    # the world under test and its (constant) identity
    prog = SB._prog(SB.DEMO_WORLD_SOURCE)
    sem = prog.semantic_artifact_id
    view = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
    core = SG.desugar_core(SB.DEMO_WORLD_SOURCE)
    g = W.parse_wrl_core(core)

    # ---- E1 CanvasLayoutV1 has no run inputs / no semantic config -----------
    layout = CV.graph_to_layout(g)
    e1_shape = (set(layout) == {"layout_version", "profile_id", "nodes", "edges"}
                and layout["layout_version"] == CV.LAYOUT_VERSION
                and "periods" not in layout and "batches" not in layout)
    e1_nodes = all(set(n) == {"object_id", "presentation"}
                   for n in layout["nodes"])
    e1_edges = all(set(ed) == {"edge_key", "presentation"}
                   for ed in layout["edges"])
    e1_valid = True
    try:
        CV.validate_layout_v1(layout)
    except Exception:
        e1_valid = False

    def _rejects_layout(mutate):
        lay = copy.deepcopy(layout)
        mutate(lay)
        try:
            CV.validate_layout_v1(lay)
            return False
        except WC.WrlValidationError:
            return True

    e1_no_periods = _rejects_layout(
        lambda l: l.__setitem__("periods", 7))
    e1_no_batches = _rejects_layout(
        lambda l: l.__setitem__("batches", [[]]))
    e1_no_semcfg = _rejects_layout(
        lambda l: l["nodes"][0].__setitem__("static_config", {"w": 16}))
    # compat loader: legacy canvas.v1 DOES carry run inputs + semantic config;
    # the loader must drop every one and yield a valid presentation-only layout.
    old_canvas = CV.graph_to_canvas(g)
    e1_old_had = ("periods" in old_canvas and "batches" in old_canvas
                  and all("static_config" in n for n in old_canvas["nodes"]))
    lay2 = CV.layout_from_canvas_v1(old_canvas)
    e1_compat = ("periods" not in lay2 and "batches" not in lay2
                 and all(set(n) == {"object_id", "presentation"}
                         for n in lay2["nodes"])
                 and all(set(ed) == {"edge_key", "presentation"}
                         for ed in lay2["edges"]))
    try:
        CV.validate_layout_v1(lay2)
    except Exception:
        e1_compat = False
    rep(e1_shape and e1_nodes and e1_edges and e1_valid and e1_no_periods
        and e1_no_batches and e1_no_semcfg and e1_old_had and e1_compat, None,
        "E1) CanvasLayoutV1 = presentation only (no periods/batches/semantic "
        "config); validate_layout_v1 rejects injected periods/batches/"
        "static_config; layout_from_canvas_v1 drops legacy run inputs + config")

    # ---- E2 label-only scenario edit preserves the ScenarioDigest -----------
    base = SC.demo_scenario(sem)
    relabeled = _relabel(base)
    dig0 = SC.scenario_digest(base)
    dig_lbl = SC.scenario_digest(relabeled)
    # a real claim edit still moves the digest (idle ep2 -> gets a claim)
    claim_edit = copy.deepcopy(base)
    claim_edit["epochs"][1]["claims"] = [
        {"writer_id": 7, "sequence": 7, "operation": "SetRotor",
         "target": "sp", "payload": {"rotor": [200, 0, 0, 0]}}]
    dig_claim = SC.scenario_digest(claim_edit)
    e2 = (dig_lbl == dig0 and dig_claim != dig0)
    rep(e2, None, "E2) label-only ScenarioV1 edit preserves the ScenarioDigest "
                  "(a claim edit still moves it)")

    # ---- E3 label-only edit updates displayed labels despite a cache HIT ----
    SB._TRAJ_CACHE.clear()
    _, dig_a, rows_a = SB._run_traj(SB.DEMO_WORLD_SOURCE, O.norm, "ic_ref", base)  # cold
    _, dig_b, rows_b = SB._run_traj(SB.DEMO_WORLD_SOURCE, O.norm, "ic_ref",
                                    relabeled)                            # warm
    labels_a = [r["label"] for r in rows_a]
    labels_b = [r["label"] for r in rows_b]
    # the canonical labels the two scenarios lower to (order the display shows)
    exp_a = [lbl for lbl, _ in SC.scenario_to_script(base)[1]]
    exp_b = [lbl for lbl, _ in SC.scenario_to_script(relabeled)[1]]
    e3 = (dig_a == dig_b                                   # same digest (cache)
          and [r["film"] for r in rows_a] == [r["film"] for r in rows_b]
          and labels_a == exp_a and labels_b == exp_b     # each shows its own
          and labels_a != labels_b)                       # and they differ
    rep(e3, None, "E3) label-only edit updates displayed labels despite the "
                  "trajectory cache hit (same digest + same films, new labels)")

    # ---- E4 scenario/world binding enforced at run time ---------------------
    # a second, genuinely different world (identity-moving edit) and its id
    src2 = SB.DEMO_WORLD_SOURCE.replace("rotor=quarter_turn_z", "rotor=identity")
    sem2 = SB._prog(src2).semantic_artifact_id
    e4_ok = (sem2 != sem)
    # a scenario bound to sem2 must be REFUSED against the DEMO_WORLD_SOURCE world ...
    mis = SC.demo_scenario(sem2)
    try:
        SB._resolve_scenario(SB.DEMO_WORLD_SOURCE, mis)
        e4_rej = False
    except WC.WrlValidationError as e:
        e4_rej = (e.code == SC.WRL_SCENARIO_WORLD_MISMATCH)
    # ... while the correctly-bound scenario resolves fine.
    _prog_ok, scen_ok = SB._resolve_scenario(SB.DEMO_WORLD_SOURCE, SC.demo_scenario(sem))
    e4_bind = (scen_ok["world_semantic_id"] == sem)
    # direct check_world_binding: matching passes, mismatched raises typed error
    e4_direct = True
    try:
        SC.check_world_binding(SC.demo_scenario(sem), sem)
    except Exception:
        e4_direct = False
    try:
        SC.check_world_binding(mis, sem)
        e4_direct = False
    except WC.WrlValidationError as e:
        e4_direct &= (e.code == SC.WRL_SCENARIO_WORLD_MISMATCH)
    rep(e4_ok and e4_rej and e4_bind and e4_direct, None,
        "E4) scenario/world binding enforced: a scenario bound to a different "
        "world -> WRL_SCENARIO_WORLD_MISMATCH; correctly-bound resolves + folds")

    # ---- E17 pre-existing unknown-target (`zz`) claim stays valid -----------
    demo = SC.demo_scenario(sem)
    e17_valid = True
    try:
        SC.validate_scenario_v1(demo)                # `zz` claim passes structure
    except Exception:
        e17_valid = False
    # fold the demo through the SAME projection path the Film panel renders and
    # confirm the ep7 `zz` claim produced a Rejected(unknown_spinner) receipt.
    ifaults, script = SC.scenario_to_script(demo)
    claimst = AD.init_claimstate()
    p7 = None
    for e, (label, batch) in enumerate(script):
        claimst, cfg_map, resets = AD.admit_step(claimst, batch, 1 + e, view)
        p7 = SB._admit_projection(view, claimst, cfg_map, resets)
    outcomes = sorted(r["outcome"] for r in p7["receipts"])
    e17_reject = (outcomes == sorted(["Applied"] * 5
                                     + ["Rejected(unknown_spinner)"])
                  and p7["capacity_fault"] == 0)
    rep(e17_valid and e17_reject, None,
        "E17) unknown-target `zz` claim stays a VALID scenario and folds to a "
        "Rejected(unknown_spinner) receipt (intentional-rejection path intact)")

    # ---- E21 golden demo + bench unchanged; format is identity-preserving ---
    # (a) demo_scenario reproduces the historical hard-coded SCRIPT films
    ref_films, ref_worlds = _fold_films(view, O.norm, ("ob",), SB.SCRIPT)
    d_films, d_worlds = _fold_films(view, O.norm, ifaults, script)
    e21_demo_r = (d_films == ref_films and d_worlds == ref_worlds)
    # (b) bench_scenario still latches the orb fault on the fixed schedule
    bench = SC.bench_scenario(sem)
    b_faults, b_script = SC.scenario_to_script(bench)
    b_films, b_worlds = _fold_films(view, O.norm, b_faults, b_script)
    fault_at = [w["fault_ob"] for w in b_worlds]
    e21_bench_r = (fault_at == [0, 0, 0, 0, 0, 1, 0, 1, 1])
    # (c) canonical WORLD formatting omits periods + inline batches, yet the
    # formatted text re-parses to the SAME SemanticArtifactID; and an explicit
    # `periods` line never moves the id (periods/batches never entered it, D3).
    formatted = F.format_wrl_core(g)
    e21_fmt_omit = ("periods" not in formatted and "[epoch:" not in formatted)
    sem_fmt = W.lower_program(formatted, W.parse_wrl_core).semantic_artifact_id
    core_no_periods = "\n".join(l for l in core.splitlines()
                                if not l.strip().startswith("periods"))
    sem_np = W.lower_program(core_no_periods,
                             W.parse_wrl_core).semantic_artifact_id
    e21_fmt_id = (sem_fmt == sem and sem_np == sem)
    e21r = e21_demo_r and e21_bench_r and e21_fmt_omit and e21_fmt_id
    e21n = None
    if not SKIP_NATIVE:
        nd_films, nd_worlds = _fold_films(view, O.native, ifaults, script)
        nb_films, nb_worlds = _fold_films(view, O.native, b_faults, b_script)
        e21n = (nd_films == ref_films and nd_worlds == ref_worlds
                and nb_films == b_films
                and [w["fault_ob"] for w in nb_worlds] == fault_at)
    rep(e21r, e21n,
        "E21) migration is identity-preserving: demo reproduces the golden "
        "SCRIPT films; bench latches [0,0,0,0,0,1,0,1,1]; canonical world format "
        "omits periods+batches yet re-parses to the SAME SemanticArtifactID "
        "(periods/batches never entered it), ic_ref == ic32")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.4-0] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.4-0 draws the three-document boundary at the IDENTITY "
          "layer: CanvasLayoutV1 is presentation-only (no run inputs, no "
          "semantic config), the ScenarioDigest excludes UI labels AND the "
          "world id, and scenario/world binding is enforced at run time. None "
          "of this touches the SemanticArtifactID -- the golden demo and the "
          "acceptance bench fold to byte-identical films.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
