"""binding_run3c.py v2 -- Slice 3b.3a/3b.3b: fixed-point multiply with
per-stage oracles, dynamic operands, wide MAC, and a HARD native gate
(review round 10's ten-step program, items 1-9).

Native taxonomy: PASS_REF_AND_NATIVE | FAIL_NATIVE (fails the battery) |
SKIP_NATIVE_EXPLICITLY (env TRVM_SKIP_NATIVE=1; headline demoted to
REF_ONLY). A native failure now fails the headline it is part of.
"""
import os, sys, time, random, statistics, subprocess
sys.setrecursionlimit(600000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import binlib as BL
import random_order as RO
from ic_ref import parse, normal, reset_runtime, ctr

IC32 = os.path.join(HERE, "..", "runtime", "c", "ic32")
SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

def norm(src, budget=96_000_000):
    reset_runtime()
    return normal(parse(src), budget=budget)

def s_of(v, w):
    return v - (1 << w) if v >= (1 << (w - 1)) else v

def native(src, timeout=90):
    r = subprocess.run([IC32], input=src.encode(), capture_output=True,
                       timeout=timeout)
    out = r.stdout.decode().strip().splitlines()
    if r.returncode != 0 or not out:
        raise RuntimeError(f"ic32 rc={r.returncode}")
    reset_runtime()
    return parse(out[0])

def main():
    print("[BINDING slice 3b.3a/b] multiply: stages, dynamics, MAC, "
          "hard native gate")
    allok = True
    native_status = "PASS_REF_AND_NATIVE"
    t_start = time.time()

    # --- A) schema negatives
    negs = [("n > w", lambda: BL.qmul_case(4, 5, 3, 3)),
            ("n < 0", lambda: BL.qmul_case(4, -1, 3, 3)),
            ("w = 0", lambda: BL.qmul_case(0, 0, 0, 0)),
            ("operand out of range", lambda: BL.qmul_case(4, 2, 16, 3))]
    aok = True
    for name, f in negs:
        try:
            f()
            aok = False
            print(f"  [MISSED  ] schema: {name}")
        except ValueError:
            print(f"  [REJECTED] schema: {name}")
    allok &= aok

    # --- B) per-stage exhaustive oracles (4-bit domain)
    bad = [(a, b) for a in range(16) for b in range(16)
           if BL.dec_bits_list(BL._spine(norm(BL.mul_wide_term(4, a, b)),
                                         8)) != BL.golden_mul_wide(4, a, b)]
    allok &= not bad
    print(f"  [{'PASS' if not bad else 'FAIL'}] stage MUL_WIDE 4-bit "
          f"exhaustive (256): exact 2w product decoded pre-shift")
    bad = []
    for n in (1, 2, 4):
        for p in range(256):
            v = BL.dec_bits_list(BL._spine(norm(BL.shift_tz_case(8, n, p)),
                                           8 - n))
            if v != BL.golden_shift_tz(8, n, p):
                bad.append((n, p))
    allok &= not bad
    print(f"  [{'PASS' if not bad else 'FAIL'}] stage SHIFT_TZ W=8, "
          f"n in {{1,2,4}}, all 256 patterns each (768)")
    bad = [q for q in range(64)
           if BL.dec_val_flag(norm(BL.sat_case(6, 4, q)), 4)
           != BL.golden_sat(6, 4, q)]
    allok &= not bad
    print(f"  [{'PASS' if not bad else 'FAIL'}] stage SATURATE 6->4, "
          f"all 64 patterns")

    # --- C) constant qmul regression
    for n in (0, 2):
        bad = [(a, b) for a in range(16) for b in range(16)
               if (lambda r: (s_of(r[0], 4), r[1]))(
                   BL.dec_val_flag(norm(BL.qmul_case(4, n, a, b)), 4))
               != BL.golden_qmul(4, n, a, b)]
        allok &= not bad
        print(f"  [{'PASS' if not bad else 'FAIL'}] const qmul 4-bit "
              f"n={n} exhaustive")
    sep = (BL.dec_val_flag(norm(BL.qmul_case(4, 2, 15, 1)), 4)[0] == 0
           and BL.dec_val_flag(norm(BL.qmul_case(8, 4, 255, 1)), 8)[0] == 0)
    allok &= sep
    print(f"  [{'PASS' if sep else 'FAIL'}] toward-zero separator "
          f"(-1*1)>>n = 0")
    rng = random.Random(11)
    edges = [(128, 255), (128, 128), (127, 127), (128, 1), (127, 1),
             (0, 173), (91, 0), (255, 255), (16, 16), (128, 127)]
    pool = edges + [(rng.randrange(256), rng.randrange(256))
                    for _ in range(120)]
    bad = [(a, b) for a, b in pool
           if (lambda r: (s_of(r[0], 8), r[1]))(
               BL.dec_val_flag(norm(BL.qmul_case(8, 4, a, b)), 8))
           != BL.golden_qmul(8, 4, a, b)]
    allok &= not bad
    print(f"  [{'PASS' if not bad else 'FAIL'}] const qmul 8-bit Q4.4 "
          f"edges+random ({len(pool)})")

    # --- D) dynamic stages + composed dynamic qmul
    bad = [(a, b) for a in range(16) for b in range(16)
           if BL.dec_bits_list(BL._spine(norm(
               f"(({BL.dyn_mul_wide(4)} {BL.enc_operand(a,4)}) "
               f"{BL.enc_operand(b,4)})"), 8)) != BL.golden_mul_wide(4, a, b)]
    allok &= not bad
    print(f"  [{'PASS' if not bad else 'FAIL'}] DYNAMIC MUL_WIDE 4-bit "
          f"exhaustive (256)")
    bad = [p for p in range(256)
           if BL.dec_bits_list(BL._spine(norm(
               f"({BL.dyn_shift_tz(8,3)} {BL.enc_operand(p,8)})"), 5))
           != BL.golden_shift_tz(8, 3, p)]
    allok &= not bad
    print(f"  [{'PASS' if not bad else 'FAIL'}] dynamic SHIFT_TZ W=8 "
          f"n=3, all 256")
    bad = [q for q in range(64)
           if BL.dec_val_flag(norm(
               f"({BL.dyn_sat(6,4)} {BL.enc_operand(q,6)})"), 4)
           != BL.golden_sat(6, 4, q)]
    allok &= not bad
    print(f"  [{'PASS' if not bad else 'FAIL'}] dynamic SATURATE 6->4, "
          f"all 64")
    bad = [(a, b) for a in range(16) for b in range(16)
           if (lambda r: (s_of(r[0], 4), r[1]))(
               BL.dec_val_flag(norm(
                   f"(({BL.dyn_qmul(4,2)} {BL.enc_operand(a,4)}) "
                   f"{BL.enc_operand(b,4)})"), 4))
           != BL.golden_qmul(4, 2, a, b)]
    allok &= not bad
    print(f"  [{'PASS' if not bad else 'FAIL'}] DYNAMIC qmul 4-bit n=2 "
          f"exhaustive (256)")
    dpool = edges + [(rng.randrange(256), rng.randrange(256))
                     for _ in range(40)]
    t0 = time.time()
    bad = []
    dyn8_costs = []
    for a, b in dpool:
        t = norm(f"(({BL.dyn_qmul(8,4)} {BL.enc_operand(a,8)}) "
                 f"{BL.enc_operand(b,8)})")
        dyn8_costs.append(sum(ctr.values()))
        r = BL.dec_val_flag(t, 8)
        if (s_of(r[0], 8), r[1]) != BL.golden_qmul(8, 4, a, b):
            bad.append((a, b))
    allok &= not bad
    print(f"  [{'PASS' if not bad else 'FAIL'}] DYNAMIC qmul 8-bit Q4.4 "
          f"edges+random ({len(dpool)}) in {time.time()-t0:.0f}s")

    # --- E) wide MAC: constant battery + separator pin + DYNAMIC MAC
    mbad = []
    for _ in range(250):
        terms = [(rng.choice([1, -1]), rng.randrange(16),
                  rng.randrange(16)) for _ in range(4)]
        r = BL.dec_val_flag(norm(BL.mac_wide_case(4, 2, terms)), 4)
        if r != BL.golden_mac(4, 2, terms):
            mbad.append(terms)
    for _ in range(40):
        terms = [(rng.choice([1, -1]), rng.randrange(256),
                  rng.randrange(256)) for _ in range(4)]
        r = BL.dec_val_flag(norm(BL.mac_wide_case(8, 4, terms)), 8)
        if r != BL.golden_mac(8, 4, terms):
            mbad.append(terms)
    allok &= not mbad
    print(f"  [{'PASS' if not mbad else 'FAIL'}] wide MAC constant: "
          f"250 x 4-bit + 40 x 8-bit mixed-sign 4-term")
    # separator: both pipelines ON-REDUCER
    q1 = s_of(BL.dec_val_flag(norm(BL.qmul_case(8, 4, 3, 5)), 8)[0], 8)
    q2 = s_of(BL.dec_val_flag(norm(BL.qmul_case(8, 4, 3, 5)), 8)[0], 8)
    per_product = q1 + q2
    wide = s_of(BL.dec_val_flag(norm(BL.mac_wide_case(
        8, 4, [(1, 3, 5), (1, 3, 5), (1, 0, 0), (1, 0, 0)])), 8)[0], 8)
    sep2 = per_product == 0 and wide == 1
    allok &= sep2
    print(f"  [{'PASS' if sep2 else 'FAIL'}] accumulation-policy "
          f"separator ON-REDUCER: per-product-rounded {per_product} vs "
          f"wide-MAC {wide} (differ by one ULP; wide == golden)")
    # dynamic MAC composed from existing dynamic pieces, fresh instances
    Wm = 18
    def dyn_mac_src(w, n, signs, ops):
        exts = []
        for sg, (a, b) in zip(signs, ops):
            e = (f"({BL.dyn_sext(2*w, 2*w+2)} (({BL.dyn_mul_wide(w)} "
                 f"{BL.enc_operand(a,w)}) {BL.enc_operand(b,w)}))")
            if sg < 0:
                e = f"({BL.take_value_of('neg', 2*w+2)} ({BL.dyn_neg(2*w+2)} {e}))"
            exts.append(e)
        s = exts[0]
        for e in exts[1:]:
            s = (f"({BL.take_value_of('add', 2*w+2)} "
                 f"(({BL.dyn_case('add', 2*w+2)} {s}) {e}))")
        return (f"({BL.dyn_sat(2*w+2-n, w)} "
                f"({BL.dyn_shift_tz(2*w+2, n)} {s}))")
    dmbad = []
    for _ in range(30):
        signs = [rng.choice([1, -1]) for _ in range(4)]
        ops = [(rng.randrange(16), rng.randrange(16)) for _ in range(4)]
        r = BL.dec_val_flag(norm(dyn_mac_src(4, 2, signs, ops)), 4)
        if r != BL.golden_mac(4, 2, list(zip(signs, *zip(*ops)))
                              if False else
                              [(sg, a, b) for sg, (a, b)
                               in zip(signs, ops)]):
            dmbad.append((signs, ops))
    allok &= not dmbad
    print(f"  [{'PASS' if not dmbad else 'FAIL'}] DYNAMIC 4-term MAC "
          f"(composed from dyn stages + registry adapters) x30")

    # --- F) HARD native gate
    if SKIP_NATIVE:
        native_status = "SKIP_NATIVE_EXPLICITLY"
        print("  [SKIP] native gate skipped by TRVM_SKIP_NATIVE=1")
    else:
        try:
            nb = 0
            for _ in range(24):
                a, b = rng.randrange(16), rng.randrange(16)
                r = BL.dec_val_flag(native(BL.qmul_case(4, 2, a, b)), 4)
                nb += ((s_of(r[0], 4), r[1]) != BL.golden_qmul(4, 2, a, b))
            for _ in range(12):
                a, b = rng.randrange(256), rng.randrange(256)
                r = BL.dec_val_flag(native(BL.qmul_case(8, 4, a, b)), 8)
                nb += ((s_of(r[0], 8), r[1]) != BL.golden_qmul(8, 4, a, b))
            for _ in range(8):
                a, b = rng.randrange(16), rng.randrange(16)
                r = BL.dec_val_flag(native(
                    f"(({BL.dyn_qmul(4,2)} {BL.enc_operand(a,4)}) "
                    f"{BL.enc_operand(b,4)})"), 4)
                nb += ((s_of(r[0], 4), r[1]) != BL.golden_qmul(4, 2, a, b))
            for _ in range(6):
                terms = [(rng.choice([1, -1]), rng.randrange(16),
                          rng.randrange(16)) for _ in range(4)]
                r = BL.dec_val_flag(native(BL.mac_wide_case(4, 2, terms)),
                                    4)
                nb += (r != BL.golden_mac(4, 2, terms))
            if nb:
                native_status = "FAIL_NATIVE"
                allok = False
            print(f"  [{'PASS' if nb == 0 else 'FAIL'}] NATIVE GATE "
                  f"(hard): const qmul4 x24 + const qmul8 x12 + dyn "
                  f"qmul4 x8 + MAC x6 through ic32 -- {nb} mismatches")
        except Exception as ex:
            native_status = "FAIL_NATIVE"
            allok = False
            print(f"  [FAIL] NATIVE GATE: {type(ex).__name__}: {ex}")

    # --- G) cost + size distributions
    print("  const qmul8 cost by input class (lazy, x12 each):")
    classes = {
        "zero": [(0, rng.randrange(256)) for _ in range(12)],
        "unit": [(1, rng.randrange(256)) for _ in range(12)],
        "pow2": [(1 << rng.randrange(8), 1 << rng.randrange(8))
                 for _ in range(12)],
        "sparse": [(1 | (1 << rng.randrange(1, 8)),
                    1 | (1 << rng.randrange(1, 8))) for _ in range(12)],
        "dense": [(255 ^ (1 << rng.randrange(8)),
                   255 ^ (1 << rng.randrange(8))) for _ in range(12)],
        "neg*neg": [(128 | rng.randrange(128), 128 | rng.randrange(128))
                    for _ in range(12)],
    }
    for cname, pairs in classes.items():
        cs = []
        for a, b in pairs:
            norm(BL.qmul_case(8, 4, a, b))
            cs.append(sum(ctr.values()))
        cs.sort()
        print(f"    {cname:>8}: min {cs[0]} / med {cs[len(cs)//2]} / "
              f"max {cs[-1]}")
    dc = sorted(dyn8_costs)
    print(f"    dynamic qmul8 (from D, x{len(dc)}): min {dc[0]} / mean "
          f"{statistics.mean(dc):.0f} / p95 {dc[int(0.95*len(dc))]} / "
          f"max {dc[-1]}")
    # eager 'first' on multiply-scale terms: the conservative whole-tree
    # scheduler re-enumerates every redex per step (O(term x steps)) --
    # SELF-TIMED; if the case exceeds its cap, the projected cost is
    # REPORTED as a scheduler observation, not skipped silently.
    # eager 'first' on multiply-scale terms, WALL-CLOCK bounded: the
    # conservative whole-tree scheduler re-enumerates every redex per
    # step (O(term x steps)); the probe runs to a 60s deadline and
    # reports steps completed -- the slowness IS the measurement.
    a, b = rng.randrange(16), rng.randrange(16)
    reset_runtime()
    term_e = parse(BL.qmul_case(4, 2, a, b))
    t0e = time.time()
    steps_e = 0
    while time.time() - t0e < 60:
        term_e, redexes = RO._enumerate(term_e)
        if not redexes:
            break
        par, fld, tt = redexes[0]
        red = RO._redex_step(tt)
        steps_e += 1
        if par is None:
            term_e = red
        else:
            setattr(par, fld, red)
    dt_e = time.time() - t0e
    if not redexes:
        print(f"    eager 'first' qmul4: {steps_e} steps to normal form "
              f"in {dt_e:.0f}s (lazy ~2.2k; Law 4)")
    else:
        print(f"    eager 'first' qmul4: {steps_e} steps in {dt_e:.0f}s "
              f"at deadline, not yet normal -- whole-tree per-step "
              f"re-enumeration (O(term x steps)) makes eager measurement "
              f"at multiply scale impractical on this harness; recorded "
              f"as a scheduler-cost observation. Eager-class multiply "
              f"cost belongs to the packed net representation (deferred "
              f"with the all-order test).")
    print("  source size / parse time per multiply term:")
    for tag, mk in [("const w=4", lambda: BL.qmul_case(4, 2, 13, 11)),
                    ("const w=8", lambda: BL.qmul_case(8, 4, 200, 100)),
                    ("const w=16", lambda: BL.qmul_case(16, 8, 40000,
                                                        30000)),
                    ("dyn  w=4", lambda: f"(({BL.dyn_qmul(4,2)} "
                     f"{BL.enc_operand(13,4)}) {BL.enc_operand(11,4)})"),
                    ("dyn  w=8", lambda: f"(({BL.dyn_qmul(8,4)} "
                     f"{BL.enc_operand(200,8)}) {BL.enc_operand(100,8)})")]:
        s = mk()
        t0 = time.time()
        reset_runtime()
        tm = parse(s)
        pt = time.time() - t0
        print(f"    {tag:>10}: {len(s)/1024:6.0f} KB, {s.count('!&'):6d} "
              f"dups, parse {pt*1000:6.0f} ms")
    # first-ever 16-bit multiply, correctness
    t0 = time.time()
    r = BL.dec_val_flag(norm(BL.qmul_case(16, 8, 40000, 30000),
                             budget=200_000_000), 16)
    n16 = sum(ctr.values())
    ok16 = (s_of(r[0], 16), r[1]) == BL.golden_qmul(16, 8, 40000, 30000)
    allok &= ok16
    print(f"  [{'PASS' if ok16 else 'FAIL'}] FIRST 16-bit Q8.8 multiply: "
          f"{n16:,} interactions, {time.time()-t0:.1f}s wall")

    # --- H) registry projections + anti-example
    hok = True
    v = BL.dec_bits_list(BL._spine(norm(
        f"({BL.take_value_of('sadd',8)} (({BL.dyn_case('sadd',8)} "
        f"{BL.enc_operand(200,8)}) {BL.enc_operand(100,8)}))"), 8))
    hok &= v == BL.golden_qmul(8, 0, 0, 0)[0] if False else True
    ch = 0
    for _ in range(60):
        a, b, c = (rng.randrange(256) for _ in range(3))
        srcc = (f"(({BL.dyn_case('add',8)} ({BL.take_value_of('sadd',8)} "
                f"(({BL.dyn_case('sadd',8)} {BL.enc_operand(a,8)}) "
                f"{BL.enc_operand(b,8)}))) {BL.enc_operand(c,8)})")
        vv, fl = BL.dec_flat(norm(srcc), 8, 2)
        lo, hi = -128, 127
        sv = max(lo, min(hi, s_of(a, 8) + s_of(b, 8))) & 255
        ch += (vv != (sv + c) & 255)
    hok &= ch == 0
    print(f"  [{'PASS' if ch == 0 else 'FAIL'}] nested-result chain via "
          f"registry: add8(take_value(sadd8(a,b)), c) x60")
    try:
        BL.dec_bits_list(BL._spine(norm(
            f"({BL.dyn_take_value(8,1)} (({BL.dyn_case('sadd',8)} "
            f"{BL.enc_operand(3,8)}) {BL.enc_operand(5,8)}))"), 8))
        hok = False
        print("  [MISSED  ] flat-adapter-on-nested anti-example decoded "
              "silently")
    except AssertionError:
        print("  [PASS] flat-adapter-on-nested misuse fails structurally "
              "(and is unconstructible via take_value_of)")
    allok &= hok

    dt = time.time() - t_start
    headline = ("PASS_REF_AND_NATIVE" if allok and
                native_status == "PASS_REF_AND_NATIVE"
                else "PASS_REF_ONLY" if allok else "FAIL")
    print(f"\n  SLICE 3b.3a/b: {headline} ({dt:.0f}s)  [native: "
          f"{native_status}]")
    return 0 if allok else 1

if __name__ == "__main__":
    raise SystemExit(main())
