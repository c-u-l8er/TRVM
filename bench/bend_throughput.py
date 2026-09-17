#!/usr/bin/env python3
"""Bend 2 beside TRVM ic32, HVM4 and C on ONE computation: the parity of 2^N, i.e. NOT applied 2^N
times to TRUE by an N-level doubling recursion.

Why this is NOT the cnot_N head-to-head and must not be read as one. HVM4 and ic32 run the same
interaction-calculus program (cnot_N: a doubling chain of a shared, labelled duplicator) and perform
the same number of interactions, so their comparison is a pure engine comparison per interaction.
Bend 2 (2.0.x, bend-lang.com) is no longer an interaction-net runtime: its guide states a term is one
64-bit word, a def compiles to a segment of a flat state machine, a call is a jump, values are affine
and a closure may be called at most once. It has no duplicator labels, no superposition, no
interaction count to report, and cannot express cnot_N at all (a function value cannot be copied).
What it CAN run is the same COMPUTATION written as recursion over a Nat:

    def par(+n: Nat, b: Bool):  match n:  0n -> flip(b);  1n+p -> par(p, par(p, b))

So the unit compared here is a FLIP (one NOT application), the only unit all four rows share, and
the number is wall time per flip from the slope of wall_ms against 2^N (the intercept is startup and
cancels). For the IC rows a flip costs ~14 interactions of graph rewriting; that ratio is printed,
not hidden, because it IS the finding: an interaction-calculus runtime pays for sharing and
provenance per rewrite, a compiled affine state machine pays a jump.

Rows:
  bend-native   bend par_N.bend -o par_N  (clang), ./par_N, one thread
  c-recursion   gcc -O2 of the same doubling recursion in C (the "class C" reference)
  trvm-ic32     ic32 -v on the translated cnot_N (interactions AND wall)
  hvm4          hvm cnot_N.hvm -s        (interactions AND wall)

Every row is run interleaved, min of REPS per size, on the same host in one sitting; the host and
its load are recorded. On a shared host the numbers are development readings, and the JSON says so.

    IC32=... HVM4=... HVM4_WORK=... BEND=... python3 bench/bend_throughput.py [--json out.json]
"""
import json
import os
import re
import resource
import subprocess
import sys
import time
import platform

HERE = os.path.dirname(os.path.abspath(__file__))
IC32 = os.environ.get("IC32", os.path.join(os.path.dirname(HERE), "runtime", "c", "ic32"))
HVM4 = os.environ.get("HVM4", os.path.expanduser("~/hvm4/src/hvm"))
WORK = os.environ.get("HVM4_WORK", os.path.expanduser("~/.cache/bench/cnot"))
BEND = os.environ.get("BEND", os.path.expanduser("~/.bend/bin/bend"))
BWORK = os.environ.get("BEND_WORK", os.path.expanduser("~/.cache/bench/bend"))
REPS = 7
BEND_SIZES = [22, 24, 26, 28, 30]      # 2^22 .. 2^30 flips: 7 ms .. 1 s
C_SIZES = [22, 24, 26, 28, 30]
IC32_SIZES = [14, 15, 16, 17, 18, 19]  # 19 is the last size below ic32's heap cap
HVM4_SIZES = [18, 19, 20, 21, 22]      # below 18 HVM4's ~100 ms startup dominates

BEND_SRC = """import Base

def flip(b: Bool) -> Bool:
  match b:
    case True{}:
      False{}
    case False{}:
      True{}

# NOT applied 2^n times to b, by an n-level doubling recursion
def par(+n: Nat, b: Bool) -> Bool:
  match n:
    case 0n:
      flip(b)
    case 1n+p:
      par(p, par(p, b))

def main() -> IO(Unit):
  IO.print(Bool.show(par(%dn, True{})))
"""

C_SRC = r"""#include <stdio.h>
#include <stdlib.h>
/* the same doubling recursion; `volatile` on the base flip keeps -O2 from folding 2^N NOTs into a parity bit */
static volatile int SINK;
static int flip(int b) { SINK = b; return !b; }
static int par(int n, int b) { if (n == 0) return flip(b); return par(n - 1, par(n - 1, b)); }
int main(int argc, char **argv) { int n = atoi(argv[1]); printf("%s\n", par(n, 1) ? "True" : "False"); return 0; }
"""


def bigstack():
    resource.setrlimit(resource.RLIMIT_STACK, (1 << 30, resource.RLIM_INFINITY))


def best(cmd, stdin_bytes=None, pre=None, env=None):
    ts, p = [], None
    for _ in range(REPS):
        t = time.perf_counter()
        p = subprocess.run(cmd, input=stdin_bytes, capture_output=True, preexec_fn=pre, env=env)
        ts.append((time.perf_counter() - t) * 1000)
    return min(ts), p


def fit(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    icept = my - slope * mx
    ss_res = sum((y - (slope * x + icept)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    return slope, icept, (1 - ss_res / ss_tot if ss_tot else float("nan"))


def build_bend():
    os.makedirs(BWORK, exist_ok=True)
    env = dict(os.environ, BEND_NO_TELEMETRY="1", PATH=os.path.expanduser("~/.bun/bin") + ":" + os.environ.get("PATH", ""))
    ver = subprocess.run([BEND, "--version"], capture_output=True, text=True, env=env).stdout.strip()
    bins = {}
    for n in BEND_SIZES:
        src = os.path.join(BWORK, f"par{n}.bend")
        open(src, "w").write(BEND_SRC % n)
        out = os.path.join(BWORK, f"par{n}")
        r = subprocess.run([BEND, src, "-o", out], capture_output=True, text=True, env=env, cwd=BWORK)
        if r.returncode:
            raise SystemExit(f"bend build N={n} failed: {r.stderr[:300]}")
        bins[n] = out
    return ver, bins


def build_c():
    os.makedirs(BWORK, exist_ok=True)
    src, out = os.path.join(BWORK, "par.c"), os.path.join(BWORK, "par_c")
    open(src, "w").write(C_SRC)
    r = subprocess.run(["gcc", "-O2", "-o", out, src], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"gcc failed: {r.stderr[:300]}")
    return out


def run_rows():
    ver, bend_bins = build_bend()
    c_bin = build_c()
    rows = {"bend-native": [], "c-recursion": [], "trvm-ic32": [], "hvm4": []}
    # interleave: one size of every row per pass, so drift hits all rows alike
    for i in range(max(len(BEND_SIZES), len(IC32_SIZES), len(HVM4_SIZES))):
        if i < len(BEND_SIZES):
            n = BEND_SIZES[i]
            ms, p = best([bend_bins[n]])
            assert p.stdout.strip() == b"True", p.stdout
            rows["bend-native"].append((n, 2 ** n, None, ms))
        if i < len(C_SIZES):
            n = C_SIZES[i]
            ms, p = best([c_bin, str(n)])
            assert p.stdout.strip() == b"True", p.stdout
            rows["c-recursion"].append((n, 2 ** n, None, ms))
        if i < len(IC32_SIZES):
            n = IC32_SIZES[i]
            f = os.path.join(WORK, f"cnot_{n:02d}.hvm")
            term = subprocess.run([sys.executable, os.path.join(HERE, "hvm4_translate.py"), f, "verbatim"], capture_output=True).stdout
            ms, p = best([IC32, "-v"], stdin_bytes=term, pre=bigstack)
            m = re.search(rb"interactions=(\d+)", p.stderr)
            rows["trvm-ic32"].append((n, 2 ** n, int(m.group(1)) if m else None, ms))
        if i < len(HVM4_SIZES):
            n = HVM4_SIZES[i]
            ms, p = best([HVM4, os.path.join(WORK, f"cnot_{n:02d}.hvm"), "-s"])
            m = re.search(rb"Itrs:\s*([\d_]+)", p.stdout)
            rows["hvm4"].append((n, 2 ** n, int(m.group(1).replace(b"_", b"")) if m else None, ms))
        print(f"  pass {i} done", flush=True)
    return ver, rows


def report(name, rows):
    xs = [r[1] for r in rows]
    ys = [r[3] for r in rows]
    slope, icept, r2 = fit(xs, ys)
    out = {"row": name, "ns_per_flip": slope * 1e6, "M_flips_per_s": 1.0 / slope / 1000, "startup_ms": icept, "r2": r2,
           "range": f"N={rows[0][0]}..{rows[-1][0]}", "points": [{"N": n, "flips": f, "interactions": it, "wall_ms": ms} for n, f, it, ms in rows]}
    its = [(it, f) for _, f, it, _ in rows if it]
    if its:
        out["interactions_per_flip"] = sum(i for i, _ in its) / sum(f for _, f in its)
        s2, _, _ = fit([it for _, _, it, _ in rows], ys)
        out["M_interactions_per_s"] = 1.0 / s2 / 1000
    return out


def main():
    ver, rows = run_rows()
    rs = [report(k, v) for k, v in rows.items()]
    load = os.getloadavg()[0]
    cpu = [l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name")][0]
    print(f"\nhost {platform.node()} · {cpu} · load {load:.2f} · bend {ver} · gcc {subprocess.run(['gcc','--version'],capture_output=True,text=True).stdout.splitlines()[0]}")
    print(f"{'row':<14}{'ns/flip':>9}{'M flips/s':>11}{'itr/flip':>10}{'M itr/s':>9}{'startup ms':>12}{'R^2':>8}{'range':>11}")
    for r in rs:
        print(f"{r['row']:<14}{r['ns_per_flip']:>9.2f}{r['M_flips_per_s']:>11.1f}{r.get('interactions_per_flip', float('nan')):>10.1f}{r.get('M_interactions_per_s', float('nan')):>9.1f}{r['startup_ms']:>12.1f}{r['r2']:>8.4f}{r['range']:>11}")
    doc = {"schema": "trvm-bench-bend/1", "stamp": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()), "host": platform.node(), "cpu": cpu, "load1": load,
           "bend_version": ver, "note": "development reading on a shared host unless the host line says otherwise; the unit compared is a FLIP; IC rows pay ~14 interactions per flip by design (see module docstring)",
           "rows": rs}
    if "--json" in sys.argv:
        p = sys.argv[sys.argv.index("--json") + 1]
        json.dump(doc, open(p, "w"), indent=1)
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
