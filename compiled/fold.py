"""fold.py -- the compiled fold beside the interaction-calculus fold, over Forge's own scenario, admission and film code.

`compiled_fold` is `spinner_bench._run_traj` with ONE substitution: where the production loop reduces
`((step cfg) state)` and decodes the normal form, this calls the compiled C step on the state dict. Everything else --
scenario resolution, the sealed admission seams, the claim state, the EpochControl, `film_hash_v7` -- is imported from
Forge unchanged, so a film computed here and a film computed by `_run_traj` differ only if the STEP differs.

`ic_fold` is the same loop with the calculus in the step (a twin of `_run_traj` that also returns the decoded state per
epoch), so the battery can compare states field by field, not only film hashes. `reference_films` is the production
`_run_traj` itself: the oracle that exists before the backend does.
"""
import os
import sys
import time

TRVM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(TRVM, "forge"), os.path.join(TRVM, "runtime", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
sys.dont_write_bytecode = True

import spinner_bench as SB          # noqa: E402
import forge_runtime as O           # noqa: E402
import compiler as C                # noqa: E402
import wrl_plan as P                # noqa: E402
import wrl_fold as FD               # noqa: E402
import admit as AD                  # noqa: E402
from forge_state import init_state_v6, state_to_film_args_v6   # noqa: E402
from admit import film_hash_v7      # noqa: E402
from emit_c import CompiledStep     # noqa: E402


def _prepare(src, scenario):
    prog, scen = SB._resolve_scenario(src, scenario)
    sem = prog.semantic_artifact_id
    view = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
    scen_dig = SB.SC.scenario_digest(scen)
    initial_faults, script = SB._script_for(prog, scen)
    world = init_state_v6(view)
    for o in initial_faults:
        if ("fault_" + o) in world:
            world["fault_" + o] = 1
    claim = AD.init_claimstate(view)
    seams = FD.runtime_seams(view, view)
    return sem, view, scen_dig, script, world, claim, seams


def _loop(src, scenario, step_fn):
    """The epoch loop shared by both folds; `step_fn(view, world, cfg_map, resets) -> world'` and its own timing."""
    sem, view, scen_dig, script, world, claim, seams = _prepare(src, scenario)
    rows = []
    for e, (label, batch) in enumerate(script):
        ep = 1 + e
        claim, cfg_map, resets = FD.admit_step_sealed(claim, batch, ep, view, seams)
        t0 = time.perf_counter()
        world = step_fn(view, world, cfg_map, resets)
        dt = time.perf_counter() - t0
        film = film_hash_v7(*state_to_film_args_v6(view, world, ep), state=claim, mailboxes=seams.film_mailboxes)
        rows.append({"t": ep, "film": film, "state": dict(world), "step_s": dt})
    return sem, scen_dig, rows


def compiled_fold(src, scenario=None):
    """(sem, scenario_digest, rows, CompiledStep). Each row: t, film, state, step_s."""
    prog, _ = SB._resolve_scenario(src, scenario)
    view = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
    cs = CompiledStep(view, prog.semantic_artifact_id)
    sem, dig, rows = _loop(src, scenario, lambda v, w, cfg, rs: cs.step(w, cfg, rs))
    return sem, dig, rows, cs


def ic_fold(src, reducer, scenario=None):
    """The calculus twin: enc -> reduce -> dec per epoch; rows also carry the epoch term size."""
    sizes, reduce_s, cache = [], [], {}

    def step_fn(view, world, cfg_map, resets):
        if "step" not in cache:                      # the step term is generated ONCE per world, as _run_traj does
            cache["step"], _ = C.compile_step_v6(view)
        ec = C.enc_config_bundle(view, cfg_map, resets)
        term = f"(({cache['step']} {ec}) {C.enc_state_v6(view, world)})"
        sizes.append(len(term.encode()))
        t0 = time.perf_counter()
        nf = reducer(term)
        reduce_s.append(time.perf_counter() - t0)
        return C.dec_state_v6(view, nf)

    sem, dig, rows = _loop(src, scenario, step_fn)
    for r, n, t in zip(rows, sizes, reduce_s):
        r["term_bytes"], r["reduce_s"] = n, t
    return sem, dig, rows


def reference_films(src, reducer_name="ic_ref", scenario=None):
    """The production oracle: `spinner_bench._run_traj` with Forge's own reducer adapter."""
    reducer = O.ref_reduce if reducer_name == "ic_ref" else O.native_reduce
    sem, dig, rows = SB._run_traj(src, reducer, reducer_name, scenario=scenario)
    return sem, dig, [r["film"] for r in rows]
