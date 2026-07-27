#!/usr/bin/env python3
"""
TRVM cross-runtime benchmark.

Runs the same bytes -- one IC surface term -- through every available TRVM
runtime and compares them on correctness first, then cost.

    python3 bench/bench.py               # full suite
    python3 bench/bench.py --quick       # small sizes only
    python3 bench/bench.py --json out.json

Backends all speak the conformance CLI (`spec/conformance/README.md`): term on
stdin, normal form on stdout. `-v` additionally reports `interactions=N`.

Three things are measured, and they are not the same thing:

  * **normal form** -- the only thing that is *normative* across runtimes. Every
    backend must produce identical bytes. A disagreement is a conformance bug.
  * **interactions** -- the machine-independent work count. NOT normative across
    runtimes (a different strategy may take a different count), so it is
    reported and cross-checked, never asserted.
  * **wall time** -- machine-dependent. Reported as median-of-reps with the
    backend's own process-startup baseline subtracted, because otherwise a 30 ms
    Python interpreter launch swamps a 0.05 ms reduction and the table measures
    `execve` rather than the runtime.

Correctness is checked against ground truth computed in ordinary Python
arithmetic, not against another runtime -- so all six can be wrong together and
it will still show.
"""
import argparse, json, os, statistics, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import terms as T                                                  # noqa: E402
from terms import Labels                                           # noqa: E402

# ---------------------------------------------------------------------------
# Backends -- discovered, never assumed. A backend that is not built is reported
# as skipped with the missing path named, never silently counted as passing.
# ---------------------------------------------------------------------------
#
# The `family` tag matters for the verdict. Five of the six implement the same
# IC32 typed-node, floating-dup model, so they are required to agree on the
# normal form bit-for-bit -- a disagreement there is a conformance bug.
# `ic_ref` is a different reduction model (the simple, non-floating core), kept
# as the historical reference; its own IC_REF.md scopes it to first-order and
# single-level higher-order duplication. It is benchmarked alongside, but its
# divergences are reported as model differences, not scored as conformance bugs.
#
IC32 = "ic32-floating-dup"
REF = "reference-simple-core"

BACKENDS = [
    ("ic32 (C)",      [os.path.join(REPO, "runtime", "c", "ic32"), "-v"],
     os.path.join(REPO, "runtime", "c", "ic32"), IC32),
    ("ic32 (Zig)",    [os.path.join(REPO, "runtime", "zig", "ic32z"), "-v"],
     os.path.join(REPO, "runtime", "zig", "ic32z"), IC32),
    ("ic32 (Mojo)",   [os.path.join(REPO, "runtime", "mojo", "ic32m"), "-v"],
     os.path.join(REPO, "runtime", "mojo", "ic32m"), IC32),
    ("ic32.wasm",     ["node", os.path.join(REPO, "runtime", "wasm", "wrun.js")],
     os.path.join(REPO, "runtime", "wasm", "ic32.wasm"), IC32),
    ("ic_float (py)", [sys.executable, os.path.join(HERE, "pyrun.py"), "ic_float"],
     os.path.join(REPO, "runtime", "python", "ic_float.py"), IC32),
    ("ic_ref (py)",   [sys.executable, os.path.join(HERE, "pyrun.py"), "ic_ref"],
     os.path.join(REPO, "runtime", "python", "ic_ref.py"), REF),
]

FAMILY = {label: fam for label, _, _, fam in BACKENDS}


def available():
    live, skipped = [], []
    for label, argv, path, _fam in BACKENDS:
        if not os.path.exists(path):
            skipped.append((label, path))
            continue
        if argv[0] == "node" and not _has_node():
            skipped.append((label, "node not on PATH"))
            continue
        live.append((label, argv))
    return live, skipped


def _has_node():
    try:
        subprocess.run(["node", "--version"], capture_output=True, timeout=10)
        return True
    except (OSError, subprocess.TimeoutExpired):
        return False


# ---------------------------------------------------------------------------
# One run of one backend
# ---------------------------------------------------------------------------
def run_once(argv, term, timeout):
    """-> (nf, interactions, wall_ms, status)."""
    t0 = time.perf_counter()
    try:
        r = subprocess.run(argv, input=term, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, None, timeout * 1000.0, "TIMEOUT"
    except OSError as e:
        return None, None, 0.0, f"OSERR {e}"
    wall = (time.perf_counter() - t0) * 1000.0

    if r.returncode != 0:
        detail = (r.stderr or "").strip().splitlines()
        return None, None, wall, "ERR " + (detail[-1][:60] if detail else f"exit {r.returncode}")

    # Interactions may arrive on stderr (C/Zig/wasm/python) or, because Mojo's
    # `emit` writes to stdout, interleaved into stdout. Harvest from both and
    # strip the line out of the normal form either way.
    inter = None
    nf_lines = []
    for line in r.stdout.splitlines():
        if line.startswith("interactions="):
            inter = _first_int(line)
        else:
            nf_lines.append(line)
    for line in (r.stderr or "").splitlines():
        if line.startswith("interactions="):
            inter = _first_int(line)

    return "\n".join(nf_lines).strip(), inter, wall, "OK"


def _first_int(line):
    for tok in line.split():
        if tok.startswith("interactions="):
            try:
                return int(tok.split("=", 1)[1])
            except ValueError:
                return None
    return None


def measure(argv, term, reps, timeout):
    """Run reps times, keep the MINIMUM wall time.

    Minimum, not mean or median: process-launch timing noise is one-sided --
    scheduler preemption, page faults and cache misses can only ever make a run
    slower, never faster. The fastest observed run is therefore the best estimate
    of the true cost, and it is far more stable across repetitions than a median.
    Every repetition must also agree on the normal form, which catches
    nondeterminism for free.
    """
    nf = inter = None
    walls = []
    for i in range(reps):
        n, it, w, st = run_once(argv, term, timeout)
        if st != "OK":
            return n, it, w, st
        if i == 0:
            nf, inter = n, it
        elif n != nf:
            return nf, inter, w, "NONDETERMINISTIC"
        walls.append(w)
    return nf, inter, min(walls), "OK"


# ---------------------------------------------------------------------------
# Workload suite -- famous problems, each with independently-computed truth
# ---------------------------------------------------------------------------
def church_readback(nf):
    """Count s^k in a readback `(s (s ... z))`."""
    return nf.count("(s ")


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def fact(n):
    r = 1
    for i in range(1, n + 1):
        r *= i
    return r


def build_suite(quick):
    """-> list of dicts {name, group, term, check, want, note}

    `check` is 'church' (count s^k and compare to `want`) or 'nf' (exact bytes)
    or 'diverge' (every backend must fail to produce a normal form).
    """
    L = Labels()
    S = []

    def church(name, group, term, want, note="", timed=False):
        S.append(dict(name=name, group=group, term=term, check="church",
                      want=want, note=note, timed=timed))

    def exact(name, group, term, want, note="", timed=False):
        S.append(dict(name=name, group=group, term=term, check="nf",
                      want=want, note=note, timed=timed))

    # --- 1. Multiplication ------------------------------------------------
    for n, m in ([(12, 12), (20, 20)] if quick else [(12, 12), (20, 20), (50, 50), (80, 80)]):
        church(f"mult {n}x{m}", "arithmetic", T.w_mult(n, m, L), n * m)

    # --- 2. Exponentiation -- readback forces an output of size b^a --------
    exps = [(3, 2), (5, 3), (8, 2)] if quick else [(3, 2), (5, 3), (8, 2), (10, 3), (12, 2), (16, 2)]
    for a, b in exps:
        church(f"exp {b}^{a}", "arithmetic", T.w_exp(a, b, L), b ** a)

    # --- 3. Tetration -- the power tower ----------------------------------
    tets = [(2, 3)] if quick else [(2, 3), (3, 2), (2, 4)]
    for base, h in tets:
        tower = base
        for _ in range(h - 1):
            tower = base ** tower
        church(f"tetration {base}^^{h}", "arithmetic", T.w_tetration(base, h, L), tower)

    # --- 4. Gauss triangular numbers --------------------------------------
    for n in ([10, 30] if quick else [10, 30, 60]):
        church(f"gauss T({n})", "arithmetic", T.w_sum_to_n(n, L), n * (n + 1) // 2)

    # --- 5. Fibonacci via Church pairs ------------------------------------
    for n in ([10, 15] if quick else [10, 15, 20, 22]):
        church(f"fib({n})", "recursion", T.w_fib(n, L), fib(n),
               "step function contains a duplicator")

    # --- 6. Factorial via Church pairs ------------------------------------
    for n in ([5, 6] if quick else [5, 6, 7, 8]):
        church(f"fact({n})", "recursion", T.w_fact(n, L), fact(n),
               "step function contains a duplicator")

    # --- 7. Kleene predecessor --------------------------------------------
    for n in ([10, 50] if quick else [10, 50, 150]):
        church(f"pred({n})", "recursion", T.w_pred(n, L), n - 1)

    # --- 8. Ackermann -- safe rung only, plus the divergent rung ----------
    for m, n in [(0, 3), (1, 4)]:
        want = n + 1 if m == 0 else n + 2
        church(f"ackermann({m},{n})", "recursion", T.w_ackermann(m, n, L), want)
    S.append(dict(name="ackermann(2,2)", group="recursion", timed=False,
                  term=T.w_ackermann(2, 2, L), check="diverge", want=None,
                  note="outside IC's safe labelling fragment - must diverge everywhere"))

    # --- 9. Optimal sharing: parity of 2^N --------------------------------
    Ns = [4, 8, 12] if quick else [4, 8, 12, 16, 20, 24]
    for N in Ns:
        exact(f"parity 2^{N}", "sharing", T.w_parity_pow2(N, L), "λa.λb.a",
              f"{2**N:,} negations")

    # --- 10. Raw duplication stress ---------------------------------------
    for d in ([8] if quick else [8, 16, 24]):
        exact(f"dup depth {d}", "sharing", T.w_dup_stress(d, L), "λa.a")

    # --- 11. Throughput tier ----------------------------------------------
    # Everything above is small enough that process startup is a large fraction
    # of the measurement, so those timings rank launchers, not runtimes. These
    # are sized so that reduction dominates startup by orders of magnitude, and
    # they are the only workloads the speed ranking is computed from. A backend
    # that cannot finish one inside the timeout is reported as such rather than
    # excluded -- "the Python reference cannot reach this scale" is a result.
    heavy = ([(14, 2)] if quick else [(14, 2), (16, 2), (12, 3), (20, 2)])
    for a, b in heavy:
        church(f"exp {b}^{a}", "throughput", T.w_exp(a, b, L), b ** a, timed=True)
    for n, m in ([(300, 300)] if quick else [(300, 300), (700, 700)]):
        church(f"mult {n}x{m}", "throughput", T.w_mult(n, m, L), n * m, timed=True)
    for n in ([22] if quick else [22, 25]):
        church(f"fib({n})", "throughput", T.w_fib(n, L), fib(n), timed=True)
    church("tetration 2^^4", "throughput", T.w_tetration(2, 4, L), 2 ** 16, timed=True)

    return S


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
G, R, Y, D, RS = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"


def fmt_ms(x):
    if x is None:
        return "-"
    if x >= 1000:
        return f"{x/1000:.2f}s"
    if x >= 10:
        return f"{x:.0f}ms"
    return f"{x:.2f}ms"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=25.0)
    ap.add_argument("--json", default=None)
    ap.add_argument("--no-depth", action="store_true", help="skip the depth-ceiling probe")
    args = ap.parse_args()

    live, skipped = available()
    suite = build_suite(args.quick)

    print(f"\nTRVM cross-runtime benchmark  --  {len(suite)} workloads x {len(live)} runtimes"
          f"  (min of {args.reps}, timeout {args.timeout:g}s)\n")
    for label, _ in live:
        print(f"  live    {label}")
    for label, why in skipped:
        print(f"  {Y}SKIP{RS}    {label}   ({why})")
    print()

    # Process-startup baseline: the cost of `execve` + interpreter/VM boot,
    # measured on a term that reduces in zero interactions. Subtracted from every
    # reported reduce time so the table measures the runtime, not the launcher.
    print("calibrating process-startup baseline...")
    base = {}
    for label, argv in live:
        _, _, ms, st = measure(argv, "λx.x", max(args.reps, 5), args.timeout)
        base[label] = ms if st == "OK" else 0.0
        print(f"  {label:16s} {fmt_ms(base[label])}")
    print()

    results = []
    conformance_failures = 0
    correctness_failures = 0

    group_now = None
    for w in suite:
        if w["group"] != group_now:
            group_now = w["group"]
            print(f"\n{'='*100}\n{group_now.upper()}\n{'='*100}")
            hdr = f"{'workload':<20}" + "".join(f"{lb.split()[0][:13]:>14}" for lb, _ in live)
            print(D + hdr + RS)

        row = dict(name=w["name"], group=w["group"], check=w["check"],
                   want=w["want"], note=w["note"], term_bytes=len(w["term"]),
                   timed=w.get("timed", False), backends={})

        nfs = {}
        line = f"{w['name']:<20}"
        for label, argv in live:
            nf, inter, ms, st = measure(argv, w["term"], args.reps, args.timeout)
            red = None if st != "OK" else max(0.0, ms - base[label])
            row["backends"][label] = dict(status=st, interactions=inter,
                                          wall_ms=ms, reduce_ms=red)
            if st == "OK":
                nfs[label] = nf
                row["backends"][label]["readback"] = church_readback(nf)
                cell = fmt_ms(red)
            else:
                cell = st.split()[0][:13]
            line += f"{cell:>14}"
        print(line)

        # -- correctness against independently computed truth
        if w["check"] == "diverge":
            produced = [lb for lb in nfs]
            if produced:
                correctness_failures += 1
                print(f"  {R}UNEXPECTED NF{RS} {w['name']}: {produced} produced a normal form "
                      f"(expected divergence everywhere)")
            else:
                print(f"  {G}ok{RS} diverges on all {len(live)} runtimes (as encoded) "
                      f"{D}-- {w['note']}{RS}")
            row["verdict"] = "diverge-agreed" if not produced else "diverge-violated"
        else:
            bad, bad_ref = [], []
            for lb, nf in nfs.items():
                if w["check"] == "church":
                    got = church_readback(nf)
                    wrong = got != w["want"]
                    detail = f"{lb}=s^{got}"
                else:
                    wrong = nf != w["want"]
                    detail = f"{lb}={nf[:24]!r}"
                if wrong:
                    (bad_ref if FAMILY[lb] == REF else bad).append(detail)
            want = f"s^{w['want']}" if w["check"] == "church" else repr(w["want"])
            if bad:
                correctness_failures += 1
                print(f"  {R}WRONG ANSWER{RS} {w['name']}: want {want}, got {', '.join(bad)}")
            if bad_ref:
                row["ref_wrong"] = bad_ref
                print(f"  {Y}outside ic_ref's model{RS} {w['name']}: want {want}, "
                      f"ic_ref gave {', '.join(bad_ref)}")
            row["verdict"] = "correct" if not bad else "wrong"

        # -- normal-form agreement WITHIN the IC32 family (the normative check)
        fam_nfs = {lb: nf for lb, nf in nfs.items() if FAMILY[lb] == IC32}
        if len(set(fam_nfs.values())) > 1:
            conformance_failures += 1
            print(f"  {R}NF DISAGREEMENT{RS} {w['name']}: "
                  f"{ {lb: nf[:30] for lb, nf in fam_nfs.items()} }")
            row["nf_agreement"] = False
        else:
            row["nf_agreement"] = True
        row["ref_diverges_from_family"] = bool(
            fam_nfs and any(FAMILY[lb] == REF and nf not in set(fam_nfs.values())
                            for lb, nf in nfs.items()))

        # -- interaction counts (reported, never asserted)
        counts = {lb: b["interactions"] for lb, b in row["backends"].items()
                  if b["status"] == "OK" and b["interactions"] is not None}
        row["interactions_agree"] = len(set(counts.values())) <= 1
        if counts:
            row["interactions"] = counts

        results.append(row)

    # -----------------------------------------------------------------
    ceilings = {} if args.no_depth else depth_ceiling(live, args.timeout)
    summary(results, live, base, conformance_failures, correctness_failures)

    if args.json:
        with open(args.json, "w") as f:
            json.dump(dict(backends=[lb for lb, _ in live],
                           families={lb: FAMILY[lb] for lb, _ in live},
                           startup_ms=base, depth_ceiling=ceilings,
                           results=results), f, indent=2)
        print(f"\nwrote {args.json}")

    return 1 if (conformance_failures or correctness_failures) else 0


def summary(results, live, base, conf_fail, corr_fail):
    print(f"\n\n{'='*100}\nSUMMARY\n{'='*100}\n")

    # --- interaction counts, the machine-independent work metric
    print("Interaction counts (machine-independent work; NOT normative across runtimes):\n")
    hdr = f"{'workload':<20}" + "".join(f"{lb.split()[0][:13]:>14}" for lb, _ in live) + "   agree"
    print(D + hdr + RS)
    for r in results:
        if not r.get("interactions"):
            continue
        line = f"{r['name']:<20}"
        for lb, _ in live:
            b = r["backends"].get(lb, {})
            v = b.get("interactions")
            line += f"{(str(v) if v is not None else '-'):>14}"
        line += f"   {G+'yes'+RS if r['interactions_agree'] else Y+'NO'+RS}"
        print(line)

    # --- speed, measured only where reduction dominates process startup
    timed = [r for r in results if r.get("timed")]
    print("\n\nThroughput tier -- reduce time (startup subtracted), per workload:\n")
    hdr = f"{'workload':<20}" + "".join(f"{lb.split()[0][:13]:>14}" for lb, _ in live)
    print(D + hdr + RS)
    for r in timed:
        line = f"{r['name']:<20}"
        for lb, _ in live:
            b = r["backends"][lb]
            line += f"{(fmt_ms(b['reduce_ms']) if b['status'] == 'OK' else b['status'].split()[0][:13]):>14}"
        print(line)

    print("\n\nReduction throughput (interactions / second, higher is better):\n")
    print(D + hdr + RS)
    # A rate is only trustworthy when the reduction it is derived from is large
    # compared to the startup cost that was subtracted off. Zig and Mojo eagerly
    # zero a 128 MB heap before doing any work, so their baseline is ~30-40 ms;
    # subtracting that from a 40 ms measurement leaves a number dominated by its
    # own error bar. Rates below that bar are shown in parentheses and excluded
    # from the ranking rather than quietly averaged in.
    rate = {lb: [] for lb, _ in live}
    for r in timed:
        line = f"{r['name']:<20}"
        for lb, _ in live:
            b = r["backends"][lb]
            v = "-"
            if b["status"] == "OK" and b["interactions"] and b["reduce_ms"]:
                ips = b["interactions"] / (max(b["reduce_ms"], 0.001) / 1000.0)
                trusted = b["reduce_ms"] >= max(10.0, base[lb])
                if trusted:
                    rate[lb].append(ips)
                    v = f"{ips/1e6:.2f}M/s"
                else:
                    v = f"({ips/1e6:.1f}M/s)"
            elif b["status"] != "OK":
                v = b["status"].split()[0][:9]
            line += f"{v:>14}"
        print(line)
    print(f"\n  {D}(parenthesised) = reduce time below the startup-subtraction error bar; "
          f"excluded from the ranking.{RS}")

    print("\n\nRanking (geometric mean of interactions/sec over the throughput tier):\n")
    scored = sorted(((statistics.geometric_mean(xs), lb) for lb, xs in rate.items() if xs),
                    reverse=True)
    if scored:
        best = scored[0][0]
        print(f"  {'runtime':<18}{'interactions/sec':>18}{'vs best':>10}{'completed':>11}{'startup':>10}")
        for gm, lb in scored:
            done = sum(1 for r in timed if r['backends'][lb]['status'] == 'OK')
            print(f"  {lb:<18}{gm/1e6:>15.2f}M/s{best/gm:>9.1f}x{done:>8}/{len(timed)}{fmt_ms(base[lb]):>10}")
    for lb, _ in live:
        if not rate[lb]:
            done = sum(1 for r in timed if r['backends'][lb]['status'] == 'OK')
            print(f"  {lb:<18}{'unranked':>18}{'':>10}{done:>8}/{len(timed)}{fmt_ms(base[lb]):>10}")
    print(f"\n  {D}Ranked only on throughput workloads whose reduce time clears the")
    print(f"  startup-subtraction error bar. The small workloads above are for correctness,")
    print(f"  not speed -- at that size the timings measure execve, not the runtime.{RS}")

    print("\n\nStartup cost -- and why it differs by 100x:\n")
    print("  All three native runtimes reserve the same 16M-slot (128 MB) heap. The cost of")
    print("  doing so is not the same, and it is the whole startup gap:\n")
    print("    ic32 (C)     calloc()                      -> kernel lazy zero pages, untouched")
    print("    ic32 (Zig)   gpa.alloc + @memset(heap, 0)  -> eagerly writes all 128 MB")
    print("    ic32 (Mojo)  List[UInt64](.., fill=0)      -> eagerly writes all 128 MB")
    print(f"\n  measured: " + ", ".join(f"{lb.split(maxsplit=1)[-1]} {fmt_ms(base[lb])}"
                                        for lb, _ in live if FAMILY[lb] == IC32 and "py" not in lb))
    print(f"  {D}A workload touching a few thousand slots pays for 128 MB of zeroing it never")
    print(f"  reads. This is a fixed per-process cost, invisible in interactions/sec but the")
    print(f"  dominant term for short reductions -- which is most of them.{RS}")

    # --- completion matrix
    print("\n\nCompletion (workloads finished / attempted):\n")
    for lb, _ in live:
        okc = sum(1 for r in results if r["backends"][lb]["status"] == "OK")
        print(f"  {lb:<18}{okc:>3} / {len(results)}")

    # --- where each backend's model departs from the IC32 family
    ref_diff = [r["name"] for r in results if r.get("ref_wrong")]
    if ref_diff:
        print("\n\nModel differences (not conformance bugs):\n")
        print(f"  ic_ref (py) is the simple, non-floating reference core. It returned a")
        print(f"  different result from the IC32 family on {len(ref_diff)} workload(s):")
        print(f"    {', '.join(ref_diff)}")
        print(f"  {D}Its failure mode is worth naming: on these it does not error or hang, it")
        print(f"  returns a residual superposition (e.g. `(s (s &81{{a,b}}))`) that reads back")
        print(f"  as a smaller Church numeral -- a silently wrong answer, not a crash.{RS}")

    # --- verdict
    print()
    fam = [lb for lb, _ in live if FAMILY[lb] == IC32]
    if conf_fail == 0:
        print(f"  {G}PASS{RS}  normal-form agreement across the {len(fam)} IC32-model runtimes "
              f"on every workload")
    else:
        print(f"  {R}FAIL{RS}  {conf_fail} workload(s) with NF disagreement inside the IC32 family")
    if corr_fail == 0:
        print(f"  {G}PASS{RS}  every IC32-model normal form matches independently computed truth")
    else:
        print(f"  {R}FAIL{RS}  {corr_fail} workload(s) with a wrong answer")
    print()


def depth_ceiling(live, timeout):
    """Find each backend's maximum readback depth by doubling until it breaks.

    The runtimes differ far more in *reach* than in speed: a recursive readback
    is bounded by the host's call stack, and the hosts are wildly different (a
    native 8MB stack, V8's WASM call-depth cap, CPython's frame limit). This
    measures that ceiling instead of assuming it -- `exp 2^k` normalizes to a
    term nested 2^k deep, so k is a direct handle on depth.
    """
    print(f"\n\n{'='*100}\nDEPTH CEILING -- how deep a normal form each runtime can read back\n{'='*100}\n")
    print(f"  {D}workload `exp 2^k` normalizes to s^(2^k), i.e. a term nested 2^k deep{RS}\n")
    print(f"  {'runtime':<18}{'deepest OK':>14}{'first failure':>16}  reason")
    ceilings = {}
    for label, argv in live:
        L = Labels()
        best, firstfail, why = None, None, ""
        for k in range(1, 22):
            term = T.w_exp(k, 2, L)
            nf, _inter, _ms, st = run_once(argv, term, timeout)
            if st == "OK" and nf is not None and church_readback(nf) == 2 ** k:
                best = 2 ** k
            else:
                firstfail = 2 ** k
                why = st if st != "OK" else "wrong readback"
                break
        ceilings[label] = dict(deepest_ok=best, first_failure=firstfail, reason=why)
        print(f"  {label:<18}{(str(best) if best else '-'):>14}"
              f"{(str(firstfail) if firstfail else 'none <= 2^21'):>16}  {why[:44]}")
    return ceilings


if __name__ == "__main__":
    sys.exit(main())
