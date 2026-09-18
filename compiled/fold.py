"""fold.py -- the compiled fold beside the interaction-calculus fold, over Forge's own scenario, admission and film code.

`compiled_fold` is `spinner_bench._run_traj` with ONE substitution: where the production loop reduces
`((step cfg) state)` and decodes the normal form, this calls the compiled C step on the state dict. Everything else --
scenario resolution, the sealed admission seams, the claim state, the EpochControl, `film_hash_v7` -- is imported from
Forge unchanged, so a film computed here and a film computed by `_run_traj` differ only if the STEP differs.

`ic_fold` is the same loop with the calculus in the step (a twin of `_run_traj` that also returns the decoded state per
epoch), so the battery can compare states field by field, not only film hashes. `reference_films` is the production
`_run_traj` itself: the oracle that exists before the backend does.
"""
import hashlib
import os
import subprocess
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


def ic_fold(src, reducer, scenario=None, split=None):
    """The calculus twin: enc -> reduce -> dec per epoch; rows also carry the epoch term size.

    `reducer(term)` is Forge's adapter (ic_ref or ic32 over stdin). `split(step, ec, st)`, when given, is used instead:
    the three pieces of the same term handed to ic32's file mode (`ic32_reparse`), for worlds whose epoch term is over
    the 16 MiB ic32 reads from stdin -- the text ic32 reduces is `((step ec) st)` either way."""
    sizes, reduce_s, cache = [], [], {}

    def step_fn(view, world, cfg_map, resets):
        if "step" not in cache:                      # the step term is generated ONCE per world, as _run_traj does
            cache["step"], _ = C.compile_step_v6(view)
        ec = C.enc_config_bundle(view, cfg_map, resets)
        st = C.enc_state_v6(view, world)
        term = f"(({cache['step']} {ec}) {st})"
        sizes.append(len(term.encode()))
        t0 = time.perf_counter()
        nf = split(cache["step"], ec, st) if split else reducer(term)
        reduce_s.append(time.perf_counter() - t0)
        return C.dec_state_v6(view, nf)

    sem, dig, rows = _loop(src, scenario, step_fn)
    for r, n, t in zip(rows, sizes, reduce_s):
        r["term_bytes"], r["reduce_s"] = n, t
    return sem, dig, rows


def reference_films(src, reducer_name="ic_ref", scenario=None):
    """The production oracle: `spinner_bench._run_traj` with Forge's own reducer adapter (`ic_ref`, `ic32`), or with
    `ic32-reparse`: the same loop handing the same term text to ic32's file mode, for terms over its 16 MiB stdin buffer
    (`runtime/c/ic32.c`, `static char buf[1<<24]`; a wider term is silently truncated and refused as a parse error)."""
    if reducer_name == "ic32-reparse":
        reducer = reparse_reducer()
    else:
        reducer = O.ref_reduce if reducer_name == "ic_ref" else O.native_reduce
    sem, dig, rows = SB._run_traj(src, reducer, reducer_name, scenario=scenario)
    return sem, dig, [r["film"] for r in rows]


# ----------------------------------------------------------------------------------- ic32 file mode
# ic32 reads a one-shot term from stdin into a fixed 16 MiB buffer; a spinner at w=33 lowers to a 39 MB step term, so its
# epochs cannot reach ic32 that way. ic32's `-reparse STEP ARGS` mode reads the step from a file and, per epoch, a config
# and a state line from ARGS, then parses and reduces the text `((STEP CONFIG) STATE)` -- byte for byte the stdin term --
# and prints one normal form per epoch. That is the reducer used here for wide worlds; ic32.c is the checked-host lane's
# file and is not changed.
REPARSE_DIR = os.path.join(os.environ.get("TRVM_COMPILED_CACHE") or os.path.expanduser("~/.cache/trvm-compiled"), "reparse")


def ic32_reparse(step, ec, st):
    """Reduce `((step ec) st)` through `ic32 -reparse`; returns the parsed normal form like `O.native_reduce`."""
    os.makedirs(REPARSE_DIR, exist_ok=True)
    key = hashlib.sha256(step.encode()).hexdigest()
    step_path = os.path.join(REPARSE_DIR, key + ".step.ic")
    if not os.path.exists(step_path):
        tmp = step_path + ".tmp.%d" % os.getpid()
        with open(tmp, "w") as f:
            f.write(step)
        os.replace(tmp, step_path)
    args_path = os.path.join(REPARSE_DIR, "args.%d.txt" % os.getpid())
    with open(args_path, "w") as f:
        f.write("1\n" + ec + "\n" + st + "\n")
    r = subprocess.run([O.IC32, "-reparse", step_path, args_path], capture_output=True, timeout=600)
    out = r.stdout.decode().strip().splitlines()
    if r.returncode != 0 or len(out) != 1:
        raise RuntimeError("ic32 -reparse rc=%s lines=%d stderr=%r" % (r.returncode, len(out), r.stderr[:200]))
    O.reset_runtime()
    return O.parse(out[0])


def split_term(term):
    """`((step ec) st)` -> (step, ec, st). The step cannot be regenerated to find the boundary: Forge names binders from a
    process-global counter, so `compile_step_v6` returns a different text on every call. The two tails are found from the
    END instead -- `ec` and `st` are balanced and small (kilobytes), so a backward paren-depth scan stops at the first
    space at depth 1 (before `st`) and the first space at depth 2 (before `ec`) without touching the megabytes of step."""
    if not (term.startswith("((") and term.endswith(")")):
        raise ValueError("split_term: not of the shape ((step ec) st)")
    depth, i, st_at, ec_at = 0, len(term) - 1, None, None
    while i >= 0:
        ch = term[i]
        if ch == ")":
            depth += 1
        elif ch == "(":
            depth -= 1
        elif ch == " ":
            if depth == 1 and st_at is None:
                st_at = i
            elif depth == 2 and st_at is not None:
                ec_at = i
                break
        i -= 1
    if st_at is None or ec_at is None:
        raise ValueError("split_term: could not find the two tails")
    step, ec, st = term[2:ec_at], term[ec_at + 1:st_at - 1], term[st_at + 1:-1]
    if term != f"(({step} {ec}) {st})":
        raise ValueError("split_term: the pieces do not reassemble the term")
    return step, ec, st


def reparse_reducer():
    """A `reducer(term)` for `_run_traj` that splits the production loop's term and reduces it through ic32's file mode."""
    def reducer(term):
        step, ec, st = split_term(term)
        return ic32_reparse(step, ec, st)
    return reducer
