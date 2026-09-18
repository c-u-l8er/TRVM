#!/usr/bin/env python3
"""battery_bend.py -- admission of the Bend backend (`emit_bend.py`) by the same oracle as the C backend.

    PYTHONDONTWRITEBYTECODE=1 python3 -B battery_bend.py [--quick] [--controls] [--bench] [--out results-bend-backend.json]

For every (world, scenario) pair of `battery.py`'s battery: the production fold `spinner_bench._run_traj` under the same
reducer plan as the C battery (ic_ref; ic32 on the ~10 MB-epoch worlds) gives the reference FILMS; `fold.compiled_fold`
(the admitted C step) gives a STATE twin; the Bend fold gives both. The verdict per pair is film-equal to the calculus's
production films AND state-equal to the C twin on every epoch. A world the Bend emitter refuses (a lane width over 24:
Bend's Nat is 48 bits) is recorded as REFUSED, not folded and not counted as agreeing.

Reference films are cached under `~/.cache/trvm-compiled/refs/` keyed by (sem, scenario digest, reducer), because they cost
the calculus ~45 min per full run and are the same bytes whichever backend is being admitted.

`--controls`: textual mutants of the Bend emitter -- the C battery's mutants translated where the law has the same shape in
Bend, plus one Bend-specific mutant (`affine-double-use`, a slot read twice without `+`), which is predicted to be refused by
Bend's checker before any fold. Every mutant over every pair; full catch sets; a mutant nothing catches fails.

`--bench`: the Bend step's cost per epoch as the slope of wall time against TRVM_REPS (1, 2000, 20000 folds of the same
control inside one process), so process launch and parsing are subtracted; beside it the C step's per-epoch figure from
`results-battery.json` and the calculus's. Development reading on the shared laptop."""
import argparse
import hashlib
import importlib.util
import json
import os
import statistics as st
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import fold as F                       # noqa: E402
import battery as B                    # noqa: E402
import emit_bend as EB                 # noqa: E402
SB, O, P = F.SB, F.O, F.P
REFS = os.path.join(os.environ.get("TRVM_COMPILED_CACHE") or os.path.expanduser("~/.cache/trvm-compiled"), "refs")


def reference(name, src, label, scen, quick):
    """Production films under the C battery's reducer plan, cached by (sem, scenario digest, reducer)."""
    wide = name in B.WIDE_WORLDS
    native_name = "ic32-reparse" if wide else "ic32"
    use_native_only = (name in B.LARGE_WORLDS or wide) and (quick or label != "demo")
    reducer_name = native_name if use_native_only else "ic_ref"
    prog, s = SB._resolve_scenario(src, scen)
    key = hashlib.sha256(("%s\n%s\n%s" % (prog.semantic_artifact_id, SB.SC.scenario_digest(s), reducer_name)).encode()).hexdigest()
    os.makedirs(REFS, exist_ok=True)
    path = os.path.join(REFS, key + ".json")
    if os.path.exists(path):
        d = json.load(open(path))
        return d["films"], reducer_name, True
    t0 = time.perf_counter()
    _, _, films = F.reference_films(src, reducer_name, scen)
    with open(path, "w") as f:
        json.dump({"world": name, "scenario": label, "reducer": reducer_name, "films": films, "wall_s": round(time.perf_counter() - t0, 3)}, f)
    return films, reducer_name, False


def bend_fold(src, scen, step_cls=EB.BendStep):
    prog, _ = SB._resolve_scenario(src, scen)
    view = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
    bs = step_cls(view, prog.semantic_artifact_id)
    sem, dig, rows = F._loop(src, scen, lambda v, w, cfg, rs: bs.step(w, cfg, rs))
    return sem, dig, rows, bs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--controls", action="store_true")
    ap.add_argument("--bench", action="store_true")
    ap.add_argument("--bench-only", action="store_true", help="redo the bench rows into the existing results file; no admission")
    ap.add_argument("--out", default=os.path.join(HERE, "results-bend-backend.json"))
    ap.add_argument("--worlds", default=None)
    a = ap.parse_args()
    if a.worlds:
        keep = set(a.worlds.split(","))
        for k in list(B.WORLDS):
            if k not in keep:
                del B.WORLDS[k]
    if a.bench_only:
        r = json.load(open(a.out))
        r["bench"] = bench()
        r["bench_measured"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        with open(a.out, "w") as f:
            json.dump(r, f, indent=1)
        print("wrote", a.out)
        return 0
    t_start = time.time()
    env = dict(os.environ, BEND_NO_TELEMETRY="1", PATH=os.path.expanduser("~/.bun/bin") + ":" + os.environ.get("PATH", ""))
    import subprocess
    ver = subprocess.run([EB.BEND, "--version"], capture_output=True, text=True, env=env).stdout.strip()
    receipt = {"measured": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "quick": a.quick, "loadavg": os.getloadavg(), "bend": ver,
               "ic32_path": O.IC32, "pairs": [], "worlds": {}, "refused": {}, "controls": None, "bench": None}
    refs, all_ok = {}, True
    for name, src, label, scen in B.pairs(a.quick):
        films_ref, rname, cached = reference(name, src, label, scen, a.quick)
        refs[(name, label)] = films_ref
        try:
            t0 = time.perf_counter()
            sem, dig, rows_b, bs = bend_fold(src, scen)
            t_b = time.perf_counter() - t0
        except ValueError as e:                 # the emitter's own refusal (lane width)
            receipt["refused"][name] = str(e)
            print("%-22s %-14s REFUSED by the Bend emitter: %s" % (name, label, str(e)[:90]), flush=True)
            continue
        _, _, rows_c, cs = F.compiled_fold(src, scen)
        v = B.compare(name, label, rows_b, films_ref, rows_c)
        v.update({"sem": sem, "scenario_digest": dig, "backend_id": bs.backend_id, "reference": rname, "reference_cached": cached,
                  "bend_epoch_wall_ms_p50": round(st.median(r["step_s"] for r in rows_b) * 1e3, 2),
                  "c_step_us_p50": round(st.median(r["step_s"] for r in rows_c) * 1e6, 2), "wall_s": round(t_b, 3)})
        ok = v["films_equal"] and v["states_equal"]
        all_ok &= ok
        receipt["pairs"].append(v)
        receipt["worlds"].setdefault(name, {"sem": sem, "backend_id": bs.backend_id, "source_sha256": bs.source_sha256, "state_width": bs.width, "source_bytes": len(bs.source)})
        print("%-22s %-14s epochs %3d  ref %-12s  bend %6.2f ms/epoch (process)  C %6.2f us  %s" % (
            name, label, v["epochs"], rname, v["bend_epoch_wall_ms_p50"], v["c_step_us_p50"], "AGREE" if ok else "DIVERGE %s" % v["first_divergence"]), flush=True)
    receipt["all_agree"] = all_ok and bool(receipt["pairs"])
    print("BEND BATTERY:", "ALL AGREE" if receipt["all_agree"] else "DIVERGENCE", "(%d pairs, %d worlds refused, %.0f s)" % (len(receipt["pairs"]), len(receipt["refused"]), time.time() - t_start))

    if a.controls:
        receipt["controls"] = run_controls(refs, a.quick)
        caught = all(c["caught"] for c in receipt["controls"])
        print("CONTROLS:", "ALL CAUGHT" if caught else "A MUTANT SURVIVED")
        all_ok &= caught
    if a.bench:
        receipt["bench"] = bench()
    receipt["loadavg_after"] = os.getloadavg()
    with open(a.out, "w") as f:
        json.dump(receipt, f, indent=1)
    print("wrote", a.out)
    return 0 if (all_ok and receipt["all_agree"]) else 1


# ----------------------------------------------------------------------------------------------- mutants
CONTROL_SKIP = ("chain120",)
# (name, old, new, predicted): the C battery's mutants where the Bend law has the same shape, plus Bend's own.
MUTANTS = [
    ("react-before-commit", "sx(eff_%d_%d, %s, %s), sx(s%d, %s, %s), %s)\" % (\"True{}\" if sg < 0 else \"False{}\", po, ii, half, full, po + jj",
     "sx(s%d, %s, %s), sx(s%d, %s, %s), %s)\" % (\"True{}\" if sg < 0 else \"False{}\", ro + ii, half, full, po + jj", "film"),
    ("reset-ignored", "+fbase_%d = sel(nz(c%d), 0n, s%d)  # COMMIT fault reset\" % (fo, reset_slot, fo)",
     "+fbase_%d = sel(nz(c%d), s%d, s%d)  # COMMIT fault reset\" % (fo, reset_slot, fo, fo)", "film"),
    ("no-saturation", "pack(Nat.min(q, hi), Nat.is_gt(q, hi), full)", "pack(Nat.mod(q, full), Nat.is_gt(q, hi), full)", "film"),
    ("neg-round-away", "sat_neg(Nat.div((neg - pos : Nat), den), lomag, full)", "sat_neg(Nat.div((neg - pos + den - 1n : Nat), den), lomag, full)", "film"),
    ("wire-cur-stale", 'emit("      o%d = s%d" % (o, o + 1))\n        emit("      o%d = hot_%s  # wire %s"', 'emit("      o%d = s%d" % (o, o))\n        emit("      o%d = hot_%s  # wire %s"', "film"),
    ("relay-hot-from-cur", '+hot_%s = s%d  # relay %s nxt" % (_cid(r), off[("relay", r)] + 1, r)', '+hot_%s = s%d  # relay %s nxt" % (_cid(r), off[("relay", r)], r)', "film"),
    ("once-no-latch", "b2n(Bool.and(Nat.is_eq(s%d, 0n), Nat.is_eq(s%d, %s)))\" % (o, o, o + 1, lit(e))", "b2n(Nat.is_eq(s%d, %s))\" % (o, o + 1, lit(e))", "film"),
    ("onehot-phase-off-by-one", 'b2n(Nat.is_eq(s%d, %s))" % (o, o, lit(ph)))\n            emit("      o%d = Nat.mod((s%d + 1n : Nat), %s)" % (o, o, lit(p)))',
     'b2n(Nat.is_eq(s%d, %s))" % (o, o, lit((ph + 1) % p)))\n            emit("      o%d = Nat.mod((s%d + 1n : Nat), %s)" % (o, o, lit(p)))', "film"),
    ("binary-phase-off-by-one", 'b2n(Nat.is_eq(s%d, %s))" % (o, o, lit(ph)))\n            emit("      +sum_%d', 'b2n(Nat.is_eq(s%d, %s))" % (o, o, lit((ph + 1) % p)))\n            emit("      +sum_%d', "film"),
    ("fault-not-sticky", "sel(nz((fbase_%d + b2n(ov_%d) : Nat)), 1n, 0n), fbase_%d)  # sticky fault\" % (fo, po, fo, po, fo)",
     "b2n(ov_%d), fbase_%d)  # sticky fault\" % (fo, po, po, fo)", "film"),
    ("react-without-fire", "+sel_%d = nz(%s)  # spinner %s merged input\" % (po, merge_in(s), s)", "+sel_%d = Bool.or(True{}, nz(%s))  # spinner %s merged input\" % (po, merge_in(s), s)", "film"),
    ("affine-double-use", 's_pat = "".join("Con{+s%d, "', 's_pat = "".join("Con{s%d, "', "refused"),
]


def load_mutant(name, old, new):
    src = open(os.path.join(HERE, "emit_bend.py")).read()
    if src.count(old) != 1:
        raise RuntimeError("mutant %s: pattern found %d times, refusing" % (name, src.count(old)))
    path = os.path.join(os.path.expanduser("~/.cache/trvm-compiled"), "mutant_bend_%s.py" % name.replace("-", "_"))
    with open(path, "w") as f:
        f.write(src.replace(old, new))
    spec = importlib.util.spec_from_file_location("emit_bend_mutant_" + name.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_controls(refs, quick):
    results = []
    # chain120 is skipped under mutants only: Bend's checker takes 211 s on its 485-slot pattern, per mutant; its laws are chain30's
    plist = [(n, s, l, sc) for n, s, l, sc in B.pairs(quick) if n not in B.WIDE_WORLDS and n not in CONTROL_SKIP]
    for name, old, new, predicted in MUTANTS:
        mod = load_mutant(name, old, new)
        first, catches, folded = None, [], 0
        for wname, src, label, scen in plist:
            folded += 1
            try:
                _, _, rows_b, _ = bend_fold(src, scen, mod.BendStep)
            except Exception as e:
                hit = {"world": wname, "scenario": label, "epoch": None, "kind": "refused", "error": "%s: %s" % (type(e).__name__, str(e)[:160])}
                catches.append(hit)
                first = first or hit
                continue
            for r, f in zip(rows_b, refs[(wname, label)]):
                if r["film"] != f:
                    hit = {"world": wname, "scenario": label, "epoch": r["t"], "kind": "film"}
                    catches.append(hit)
                    first = first or hit
                    break
        kinds = sorted({c["kind"] for c in catches})
        worlds = sorted({c["world"] for c in catches})
        results.append({"mutant": name, "predicted": predicted, "caught": bool(catches), "kinds": kinds, "caught_at": first, "caught_by_worlds": worlds,
                        "caught_pairs": len(catches), "pairs_folded": folded, "as_predicted": bool(catches) and (predicted in kinds)})
        print("control=%-26s %s %s  by %d worlds, kinds %s%s" % (name, "CAUGHT" if catches else "NOT CAUGHT", json.dumps(first) if first else "", len(worlds), kinds,
                                                                "" if results[-1]["as_predicted"] else "  ** not as predicted (%s)" % predicted), flush=True)
    return results


# ----------------------------------------------------------------------------------------------- bench
BENCH_WORLDS = ("golden-demo", "two-spinners", "chain120", "chain30", "spinner-w8-n4", "mailbox-routes", "pulser-relay")

C_DRIVER = r"""
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
typedef int64_t i64;
int state_width(void); int control_width(void); void step_v6(const i64 *st, const i64 *ctl, i64 *out);
/* the same loop the Bend program runs under TRVM_REPS: the state of epoch k is the input of epoch k+1, one control throughout */
int main(int argc, char **argv) {
  long reps = atol(argv[1]); int W = state_width(), C = control_width();
  i64 *a = calloc(W, sizeof(i64)), *b = calloc(W, sizeof(i64)), *c = calloc(C ? C : 1, sizeof(i64));
  for (int i = 0; i < W; i++) if (scanf("%lld", (long long *)&a[i]) != 1) return 2;
  for (int i = 0; i < C; i++) if (scanf("%lld", (long long *)&c[i]) != 1) return 2;
  struct timespec t0, t1; clock_gettime(CLOCK_MONOTONIC, &t0);
  for (long r = 0; r < reps; r++) { step_v6(a, c, b); i64 *t = a; a = b; b = t; }
  clock_gettime(CLOCK_MONOTONIC, &t1);
  for (int i = 0; i < W; i++) printf("%lld ", (long long)a[i]);
  printf("\n"); fprintf(stderr, "%.1f\n", (t1.tv_sec - t0.tv_sec) * 1e9 + (t1.tv_nsec - t0.tv_nsec));
  return 0;
}
"""


def c_reps(cs, a, c, reps):
    """The C step folded `reps` times in one process by the driver above: (final state, ns per epoch inside the process)."""
    import subprocess, tempfile
    d = os.path.join(os.path.expanduser("~/.cache/trvm-compiled"), "cbench")
    os.makedirs(d, exist_ok=True)
    binp = os.path.join(d, cs.source_sha256 + ".bench")
    if not os.path.exists(binp):
        with tempfile.TemporaryDirectory(dir=d) as td:
            with open(os.path.join(td, "step.c"), "w") as f:
                f.write(cs.source)
            with open(os.path.join(td, "driver.c"), "w") as f:
                f.write(C_DRIVER)
            subprocess.run(["gcc", "-O2", "-o", binp, os.path.join(td, "driver.c"), os.path.join(td, "step.c")], check=True, capture_output=True)
    inp = " ".join(str(int(v)) for v in a) + " " + " ".join(str(int(v)) for v in c) + "\n"
    r = subprocess.run([binp, str(reps)], input=inp, capture_output=True, text=True, timeout=600, check=True)
    return [int(x) for x in r.stdout.split()], float(r.stderr.strip()) / reps


def bench():
    """Per-epoch cost of the Bend step and of the C step, each folded K times INSIDE one process on each world's demo
    scenario's epoch-1 input (the control of epoch 1 applied K times; the state chains). Bend: the slope of wall time
    between K=2,000 and K=20,000, minimum of 5 runs per point (process launch and string parsing cancel in the slope). C: the
    driver's own clock around K=1,000,000 steps, minimum of 5. The two folds must end in the same state (`reps_states_equal`,
    at K=2000). The `python_roundtrip_us` column is what `battery.py` reports as the C step's cost: the ctypes call with
    encode/decode around it, which is why it reads 10-100x the C figure here."""
    cb = json.load(open(os.path.join(HERE, "results-battery.json")))
    py_us = {p["world"]: p["compiled_step_us_p50"] for p in cb["pairs"] if p["scenario"] == "demo"}
    ic_s = {p["world"]: (p["ic_reduce_s_p50"], p["ic_reducer"]) for p in cb["pairs"] if p["scenario"] == "demo"}
    rows = []
    for name in BENCH_WORLDS:
        if name not in B.WORLDS:
            continue
        src = B.WORLDS[name]
        sem, view, dig, script, world, claim, seams = F._prepare(src, None)
        bs = EB.BendStep(view, sem)
        cs = F.CompiledStep(view, sem)
        claim, cfg, resets = F.FD.admit_step_sealed(claim, script[0][1], 1, view, seams)
        a, c = list(bs.encode(world)), list(bs.control(cfg, resets))
        pts, final_b = [], None
        for reps in (1, 2000, 20000):        # 20,000 so that a 1 ns step is still above the slope's noise
            best = None
            for _ in range(5):
                final_b = bs.run_raw(a, c, reps)
                best = bs.last_wall_s if best is None else min(best, bs.last_wall_s)
            pts.append((reps, best))
        (r1, t1), (r2, t2), (r3, t3) = pts
        slope_us = (t3 - t2) / (r3 - r2) * 1e6
        final_c, _ = c_reps(cs, a, c, 2000)
        c_ns = min(c_reps(cs, a, c, 1000000)[1] for _ in range(5))
        rows.append({"world": name, "state_width": bs.width, "process_ms_reps1": round(t1 * 1e3, 2), "wall_ms_reps2000": round(t2 * 1e3, 2), "wall_ms_reps20000": round(t3 * 1e3, 2),
                     "bend_step_us": round(slope_us, 3), "c_step_us": round(c_ns / 1e3, 4), "bend_over_c": round(slope_us * 1e3 / c_ns, 1) if c_ns else None,
                     "python_roundtrip_us": py_us.get(name), "ic_reduce_s": ic_s.get(name, (None, None))[0], "ic_reducer": ic_s.get(name, (None, None))[1],
                     "reps_states_equal": final_b == final_c})
        print("bench %-16s width %3d  Bend %8.3f us/epoch   C %8.4f us/epoch  (Bend/C %5.1fx)   python round trip %6.2f us   %s %s s   reps-states %s" % (
            name, bs.width, slope_us, c_ns / 1e3, rows[-1]["bend_over_c"] or -1, py_us.get(name) or -1, ic_s.get(name, (None, "?"))[1], ic_s.get(name, (None, None))[0],
            "EQUAL" if final_b == final_c else "DIFFER"), flush=True)
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
