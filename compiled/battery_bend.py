#!/usr/bin/env python3
"""battery_bend.py -- admission of a backend step (`--emitter v1|v2|c2`: Bend v1, Bend v2, the packed C step) by the same oracle as the C backend.

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
import emit_bend2 as EB2               # noqa: E402
import emit_c2 as EC2                  # noqa: E402
SB, O, P = F.SB, F.O, F.P
EMITTERS = {"v1": ("emit_bend.py", EB.BendStep, EB.emit_step_bend), "v2": ("emit_bend2.py", EB2.BendStep2, lambda v: EB2.emit_step_bend2(v)[0]),
            "c2": ("emit_c2.py", EC2.CompiledStep2, lambda v: EC2.emit_step_c2(v)[0])}
EMITTER = "v1"


def reference(name, src, label, scen, quick):
    """Production films under the C battery's reducer plan, through fold.cached_reference_films."""
    wide = name in B.WIDE_WORLDS
    native_name = "ic32-reparse" if wide else "ic32"
    use_native_only = (name in B.LARGE_WORLDS or wide) and (quick or label != "demo") and name not in B.HUGE_WORLDS  # ic_ref only for the gated world (battery.py says why)
    reducer_name = native_name if use_native_only else "ic_ref"
    films, cached = F.cached_reference_films(src, reducer_name, scen)
    return films, reducer_name, cached


def bend_fold(src, scen, step_cls=None):
    step_cls = step_cls or EMITTERS[EMITTER][1]
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
    ap.add_argument("--out", default=None)
    ap.add_argument("--worlds", default=None)
    ap.add_argument("--emitter", default="v1", choices=list(EMITTERS), help="v1: one cons per slot, sign-magnitude MAC; v2: bit-packed signal words, biased branch-free MAC")
    a = ap.parse_args()
    global EMITTER
    EMITTER = a.emitter
    a.out = a.out or os.path.join(HERE, {"v1": "results-bend-backend.json", "v2": "results-bend2-backend.json", "c2": "results-c2-backend.json"}[EMITTER])
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
    receipt = {"measured": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "quick": a.quick, "emitter": EMITTER, "loadavg": os.getloadavg(), "bend": ver,
               "ic32_path": O.IC32, "pairs": [], "worlds": {}, "refused": {}, "controls": None, "bench": None}
    refs, all_ok = {}, True
    for name, src, label, scen in B.pairs(a.quick):
        try:                                     # the emitter's own refusal (lane width) comes before any reference is computed
            prog, _ = SB._resolve_scenario(src, scen)
            EMITTERS[EMITTER][2](P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact)))
        except ValueError as e:
            receipt["refused"][name] = str(e)
            print("%-22s %-14s REFUSED by the Bend emitter: %s" % (name, label, str(e)[:90]), flush=True)
            continue
        films_ref, rname, cached = reference(name, src, label, scen, a.quick)
        refs[(name, label)] = films_ref
        t0 = time.perf_counter()
        sem, dig, rows_b, bs = bend_fold(src, scen)
        t_b = time.perf_counter() - t0
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
        # a mutant caught by a world its widening did not add, or by the wrong kind, fails the run like a survivor does
        caught = all(c["caught"] and c["as_predicted"] for c in receipt["controls"])
        print("CONTROLS:", "ALL CAUGHT, AS PREDICTED" if caught else "A MUTANT SURVIVED, OR WAS CAUGHT BY THE WRONG WORLD OR KIND")
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
# ----------------------------------------------------------------------------------------------- mutants
# Since 2026-09-19 (T7) the LAW mutants are derived from `laws.py` -- (law id, name), the same clause flip in every
# backend that renders it (`laws.mutant`); the equivalence of each old string-edit mutant to its law mutant was checked
# on every admitted world before the old lists were retired (README §2f). What stays textual is a REPRESENTATION mutant,
# scoped to one function of one file: Bend's affine pattern, v2's run masks and its sign-magnitude `fin` argument order,
# the C v2 step's two MAC paths and their selector, and the emitter's width bound.
import laws as LAW
from battery import LAW_MUTANTS, scoped_replace

REPRESENTATION = {
    "v1": [("affine-double-use", "emit_bend.py", None, 's_pat = "".join("Con{+s%d, "', 's_pat = "".join("Con{s%d, "', "refused", None)],
    "v2": [("mac-sign-flipped", "laws.py", "_b2_react", "fin((p_%d_%d, m_%d_%d), den_%d", "fin((m_%d_%d, p_%d_%d), den_%d", "film", None),
           ("run-mask-dropped", "emit_bend2.py", None, 'parts.append("U32.shln(U32.and(n%d, %d), %dn)" % (sw, mask, disp))', 'parts.append("U32.shln(n%d, %dn)" % (sw, disp))', "film", None),
           ("affine-double-use", "emit_bend2.py", None, 's_pat = "".join("Con{+s%d, "', 's_pat = "".join("Con{s%d, "', "refused", None)],
    "c2": [("floor-shift-128", "laws.py", "_c2_mac", '"  i128 q = %s;" % shift128', '"  i128 q = acc >> n;"', "film", None),
           ("no-saturation-128", "laws.py", "_c2_mac", '"  i128 s = %s;" % sat128', '"  i128 s = q;"', "film", None),
           ("floor-shift-64", "laws.py", "_c2_mac", '"  i64 q = %s;" % shift64', '"  i64 q = acc >> n;"', "film", None),
           ("no-saturation-64", "laws.py", "_c2_mac", '"  i64 s = %s;" % sat64', '"  i64 s = q;"', "film", None),
           ("wide-on-narrow-path", "laws.py", "_c2_mac", '"  if (w <= 31) { for', '"  if (w <= 63) { for', "film", None),
           # the path selector taken from the WORLD's narrowest spinner instead of the row's own width: exact on every
           # single-width world and on two-spinners (both narrow); wrong only where a wide spinner shares a step with a
           # narrow one -- `mixed-w8-w33`, and no other world may catch it.
           ("path-from-min-width", "laws.py", "_c2_mac", '"  if (w <= 31) { for (int c = 0; c < 4; c++) fault |= mac_row64(w, n, c, rotor, pose, &out[c]); }"',
            '"  if (%d <= 31) { for (int c = 0; c < 4; c++) fault |= mac_row64(w, n, c, rotor, pose, &out[c]); }" % f["min_w"]', "film", ("mixed-w8-w33",)),
           ("run-mask-dropped", "emit_c2.py", None, 'parts.append("((n%d & 0x%xULL) %s %d)" % (sw, mask, "<<" if disp >= 0 else ">>", abs(disp)))', 'parts.append("(n%d %s %d)" % (sw, "<<" if disp >= 0 else ">>", abs(disp)))', "film", None)],
}
if os.environ.get("TRVM_BATTERY_HUGE"):
    # the same bound mutant as battery.py's, for the v2 step's identical `sx`; only the 63-lane world may catch it
    REPRESENTATION["c2"].append(("sx-subtrahend-i64", "laws.py", "_c2_mac", "x - ((i128)1 << w) : x; }", "x - (i128)((i64)1 << w) : x; }", "film", tuple(B.HUGE_WORLDS)))
# Bend's MAC is sign-magnitude, so the toward-zero and saturation laws render in `fin` and their flips apply (the old
# `neg-round-away` / `no-saturation`); every law mutant renders in every backend here.
EMITTER_MODULE = {"v1": EB, "v2": EB2, "c2": EC2}


def all_mutants():
    """[(name, kind, spec, predicted, only_by)] for the selected emitter: law mutants then representation mutants."""
    out = [(name, "law", (name, law), "film", None) for name, law in LAW_MUTANTS]
    out += [(m[0], "text", m, m[5], m[6]) for m in REPRESENTATION[EMITTER]]
    return out


def load_mutant(name, fname, fn, old, new):
    src = scoped_replace(open(os.path.join(HERE, fname)).read(), fn, old, new)
    path = os.path.join(os.path.expanduser("~/.cache/trvm-compiled"), "mutant_bend_%s_%s.py" % (EMITTER, name.replace("-", "_")))
    with open(path, "w") as f:
        f.write(src)
    spec = importlib.util.spec_from_file_location("emit_bend_mutant_%s_%s" % (EMITTER, name.replace("-", "_")), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class installed:
    """One mutant for the duration: a law mutant through laws.mutant; a laws.py edit by swapping the emitter's LAW
    module; an emitter-file edit by loading the mutated copy as the step class. `.step_cls` is what to fold with."""

    def __init__(self, kind, spec):
        self.kind, self.spec, self.module = kind, spec, None
        self.step_cls = EMITTERS[EMITTER][1]

    def __enter__(self):
        mod = EMITTER_MODULE[EMITTER]
        if self.kind == "law":
            self.cm = LAW.mutant(self.spec[1], self.spec[0])
            self.cm.__enter__()
        else:
            name, fname, fn, old, new = self.spec[:5]
            m = self.module = load_mutant(name, fname, fn, old, new)
            if fname == "laws.py":
                self.saved, mod.LAW = mod.LAW, m
            else:
                self.step_cls = getattr(m, {"v1": "BendStep", "v2": "BendStep2", "c2": "CompiledStep2"}[EMITTER])
        return self

    def __exit__(self, *a):
        mod = EMITTER_MODULE[EMITTER]
        if self.kind == "law":
            self.cm.__exit__(*a)
        elif self.spec[1] == "laws.py":
            mod.LAW = self.saved


def run_controls(refs, quick):
    results = []
    # a world the emitter refuses cannot be folded under a mutant; every admitted world is -- the wide world is what
    # exercises the i128 path of the C step, and the first c2 control run without it let three mutants survive (2026-09-18).
    # chain120 is skipped for Bend v1 only: its checker takes 211 s on the 485-slot pattern, per mutant; its laws are chain30's.
    emit_fn = EMITTERS[EMITTER][2]
    def admitted(name):
        prog, _ = SB._resolve_scenario(B.WORLDS[name], None)
        try:
            emit_fn(P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact)))
            return True
        except ValueError:
            return False
    plist = [(n, s, l, sc) for n, s, l, sc in B.pairs(quick) if admitted(n) and not (EMITTER == "v1" and n in CONTROL_SKIP)]
    for name, kind, mspec, predicted, only in all_mutants():
        first, catches, folded = None, [], 0
        with installed(kind, mspec) as inst:
            for wname, src, label, scen in plist:
                folded += 1
                try:
                    _, _, rows_b, _ = bend_fold(src, scen, inst.step_cls)
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
        as_expected = only is None or (bool(catches) and set(worlds) <= set(only))
        results.append({"mutant": name, "kind": kind, "law": mspec[1] if kind == "law" else None, "predicted": predicted, "caught": bool(catches), "kinds": kinds, "caught_at": first, "caught_by_worlds": worlds,
                        "caught_pairs": len(catches), "pairs_folded": folded, "only_by": list(only) if only else None,
                        "as_predicted": bool(catches) and (predicted in kinds) and as_expected})
        print("control=%-26s %s %s  by %d worlds, kinds %s%s%s" % (name, "CAUGHT" if catches else "NOT CAUGHT", json.dumps(first) if first else "", len(worlds), kinds,
                                                                  "" if results[-1]["as_predicted"] else "  ** not as predicted (%s)" % predicted,
                                                                  "" if as_expected else "  ** NOT AS EXPECTED (only %s may catch this)" % list(only)), flush=True)
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


def c_reps(cs, a, c, reps, flags=("-O2",)):
    """The C step folded `reps` times in one process by the driver above: (final state, ns per epoch inside the process).
    `a` is the vector the .so speaks (v1: the slot vector; v2: the packed one) -- the caller packs and unpacks."""
    import subprocess, tempfile
    d = os.path.join(os.path.expanduser("~/.cache/trvm-compiled"), "cbench")
    os.makedirs(d, exist_ok=True)
    binp = os.path.join(d, hashlib.sha256((" ".join(flags) + cs.source_sha256).encode()).hexdigest() + ".bench")
    if not os.path.exists(binp):
        with tempfile.TemporaryDirectory(dir=d) as td:
            with open(os.path.join(td, "step.c"), "w") as f:
                f.write(cs.source)
            with open(os.path.join(td, "driver.c"), "w") as f:
                f.write(C_DRIVER)
            subprocess.run(["gcc"] + list(flags) + ["-o", binp, os.path.join(td, "driver.c"), os.path.join(td, "step.c")], check=True, capture_output=True)
    inp = " ".join(str(int(v)) for v in a) + " " + " ".join(str(int(v)) for v in c) + "\n"
    r = subprocess.run([binp, str(reps)], input=inp, capture_output=True, text=True, timeout=600, check=True)
    return [int(x) for x in r.stdout.split()], float(r.stderr.strip()) / reps


C_VARIANTS = (("c1", ("-O2",)), ("c1-O3-native", ("-O3", "-march=native")), ("c2", ("-O2",)), ("c2-O3-native", ("-O3", "-march=native")))


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
        cs = F.CompiledStep(view, sem)
        claim, cfg, resets = F.FD.admit_step_sealed(claim, script[0][1], 1, view, seams)
        a, c = list(cs.encode(world)), list(cs.control(cfg, resets))
        final_c, _ = c_reps(cs, a, c, 2000)
        c_ns = min(c_reps(cs, a, c, 1000000)[1] for _ in range(5))
        row = {"world": name, "state_width": cs.width, "c_step_us": round(c_ns / 1e3, 4), "python_roundtrip_us": py_us.get(name),
               "ic_reduce_s": ic_s.get(name, (None, None))[0], "ic_reducer": ic_s.get(name, (None, None))[1]}
        line = "bench %-16s width %3d  C %8.4f us" % (name, cs.width, c_ns / 1e3)
        for tag, flags in C_VARIANTS[1:]:
            try:
                step = cs if tag.startswith("c1") else EC2.CompiledStep2(view, sem)
            except ValueError:
                row[tag] = "refused"
                continue
            vin = a if tag.startswith("c1") else step.pack(a)
            fin_, _ = c_reps(step, vin, c, 2000, flags)
            fin_ = fin_ if tag.startswith("c1") else step.unpack(fin_)
            ns = min(c_reps(step, vin, c, 1000000, flags)[1] for _ in range(5))
            row[tag] = {"step_us": round(ns / 1e3, 4), "over_c1": round(ns / c_ns, 2) if c_ns else None, "reps_states_equal": fin_ == final_c}
            line += "   %s %8.4f us (%4.2fx) %s" % (tag, ns / 1e3, row[tag]["over_c1"] or -1, "EQ" if fin_ == final_c else "DIFFER")
        for tag, (_, step_cls, _emit) in EMITTERS.items():
            if tag == "c2":
                continue
            try:
                bs = step_cls(view, sem)
            except ValueError:
                row[tag] = "refused"
                continue
            pts, final_b = [], None
            for reps in (1, 2000, 20000):        # 20,000 so that a 1 ns step is still above the slope's noise
                best = None
                for _ in range(5):
                    final_b = bs.run_raw(a, c, reps)
                    best = bs.last_wall_s if best is None else min(best, bs.last_wall_s)
                pts.append((reps, best))
            (r1, t1), (r2, t2), (r3, t3) = pts
            slope_us = (t3 - t2) / (r3 - r2) * 1e6
            row[tag] = {"packed_width": getattr(bs, "packed_width", bs.width), "process_ms_reps1": round(t1 * 1e3, 2), "wall_ms_reps2000": round(t2 * 1e3, 2), "wall_ms_reps20000": round(t3 * 1e3, 2),
                        "bend_step_us": round(slope_us, 3), "bend_over_c": round(slope_us * 1e3 / c_ns, 1) if c_ns else None, "reps_states_equal": final_b == final_c}
            line += "   %s %8.3f us (%5.1fx) %s" % (tag, slope_us, row[tag]["bend_over_c"] or -1, "EQ" if final_b == final_c else "DIFFER")
        rows.append(row)
        print(line, flush=True)
    return rows


if __name__ == "__main__":
    raise SystemExit(main())
