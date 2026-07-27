#!/usr/bin/env python3
"""Throughput of HVM4 vs TRVM ic32 on IDENTICAL programs.

Both engines perform exactly the same number of interactions on the cnot_N
family (see `hvm4_families.py`), so wall time here is a pure engine comparison
-- no encoding or strategy difference is folded into the number.

Method: fit wall_ms against interactions and take the slope as marginal
throughput; the intercept is process startup, which therefore cancels instead
of being estimated and subtracted.

The trap this script exists to avoid: HVM4 starts up in ~115 ms, which is
longer than the ENTIRE reduction at every size TRVM can reach. Fitting both
engines over the same sizes fits HVM4's launch noise and reports a wildly
inflated rate (754 M/s in one run). So each engine is fitted over the range
where its own reduction dominates its own startup, those ranges are printed,
and fit quality is reported so a bad fit is visible rather than silent.

TRVM cannot go past N=19: N=20 exhausts its 16M-slot heap. HVM4 has no
comparable ceiling, so its range extends further -- legitimate, because a slope
is a per-interaction rate and needs a linear regime, not equal sizes.
"""
import os, re, subprocess, time, resource, sys

HERE = os.path.dirname(os.path.abspath(__file__))
IC32 = os.environ.get("IC32", os.path.join(os.path.dirname(HERE), "runtime", "c", "ic32"))
HVM4 = os.environ.get("HVM4", "/tmp/hvm4")
WORK = os.environ.get("HVM4_WORK", "/tmp/cnot")

TRVM_SIZES = [14, 15, 16, 17, 18, 19]     # 19 is the last size below the heap cap
HVM4_SIZES = [18, 19, 20, 21, 22]         # below 18, startup dominates
REPS = 7
MIN_DOMINANCE = 2.0    # trust a fit only if reduce time >= this x startup


def bigstack():
    """ic32 recurses during reduction and segfaults on the default 8 MB stack
    around 10^6 interactions. Give it room so this measures the engine rather
    than the stack limit."""
    resource.setrlimit(resource.RLIMIT_STACK, (1 << 30, resource.RLIM_INFINITY))


def best(cmd, stdin_bytes=None, pre=None):
    """Minimum of REPS -- launch noise is one-sided, so the fastest run is the
    best estimate and by far the most stable."""
    ts = []
    for _ in range(REPS):
        t = time.perf_counter()
        p = subprocess.run(cmd, input=stdin_bytes, capture_output=True,
                           preexec_fn=pre)
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


def measure(sizes, runner):
    out = []
    for n in sizes:
        f = os.path.join(WORK, f"cnot_{n:02d}.hvm")
        itr, ms = runner(f)
        if itr is None:
            print(f"  N={n:<3} did not complete -- excluded")
            continue
        out.append((n, itr, ms))
        print(f"  N={n:<3} itrs={itr:>10}  {ms:9.2f} ms")
    return out


def run_hvm4(f):
    ms, p = best([HVM4, f, "-s"])
    m = re.search(rb"Itrs:\s*([\d_]+)", p.stdout)
    return (int(m.group(1).replace(b"_", b"")) if m else None), ms


def run_trvm(f):
    term = subprocess.run(
        [sys.executable, os.path.join(HERE, "hvm4_translate.py"), f, "verbatim"],
        capture_output=True).stdout
    ms, p = best([IC32, "-v"], stdin_bytes=term, pre=bigstack)
    m = re.search(rb"interactions=(\d+)", p.stderr)
    return (int(m.group(1)) if m else None), ms


def report(name, rows):
    xs = [r[1] for r in rows]
    ys = [r[2] for r in rows]
    slope, icept, r2 = fit(xs, ys)
    dom = (max(ys) - max(icept, 0.0)) / icept if icept > 0 else float("inf")
    return {"name": name, "mips": 1.0 / slope / 1000, "startup": icept,
            "r2": r2, "dom": dom, "ok": dom >= MIN_DOMINANCE and r2 >= 0.98,
            "range": f"N={rows[0][0]}..{rows[-1][0]}"}


def main():
    print("HVM4:")
    h = measure(HVM4_SIZES, run_hvm4)
    print("TRVM ic32:")
    t = measure(TRVM_SIZES, run_trvm)

    # If the counts ever diverge, wall time is not comparing the same work.
    hc = {n: i for n, i, _ in h}
    for n, i, _ in t:
        if n in hc:
            assert hc[n] == i, f"N={n}: counts differ {hc[n]} vs {i}"

    rs = [report("HVM4", h), report("TRVM ic32", t)]
    print(f"\n{'engine':<12}{'M interactions/s':>18}{'startup ms':>12}"
          f"{'fit R^2':>9}{'reduce/startup':>16}{'range':>10}")
    print("-" * 77)
    for r in rs:
        flag = "" if r["ok"] else "   <- UNTRUSTWORTHY FIT"
        print(f"{r['name']:<12}{r['mips']:>18.1f}{r['startup']:>12.1f}"
              f"{r['r2']:>9.4f}{r['dom']:>16.1f}{r['range']:>10}{flag}")

    if all(r["ok"] for r in rs):
        a, b = rs
        print(f"\nInteraction counts are identical at every shared size, so the "
              f"{a['mips'] / b['mips']:.1f}x gap is a pure engine comparison "
              f"on this workload.")
    else:
        print("\nAt least one fit is untrustworthy; widen its size range rather "
              "than quoting the number.")


if __name__ == "__main__":
    main()
