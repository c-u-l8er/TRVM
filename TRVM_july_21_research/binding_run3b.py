"""binding_run3b.py -- Slice 3b.1/3b.2: fixed-width binary arithmetic on
the real reducers (review round 7 ladder).

3b.1 unsigned: add-with-carry (+carry-into-MSB), sub-with-borrow, ltu,
eq, widen, trunc. 3b.2 signed core: neg (wraps; ovf at MIN), slt,
saturating add/sub with specified clamp direction. Policies are in
binlib's docstring, written before the circuits.

Testing: exhaustive at 4 bits (every op), exhaustive-or-declared at 8
bits (self-timed: full 65,536x{add,sub,ltu} if the projected budget
allows, else exhaustive add + 8,192 random sub/ltu -- the path taken is
PRINTED), boundary-grid + randomized at 16 bits, widen/trunc round
trips, signed edge battery, ic32 spot batches, and cost distributions
by input class and named strategy.
"""
import os, sys, time, random, statistics, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import binlib as BL
from compiler import TUPN
from lower_e2a import _spine, _dec_bool
from ic_ref import parse, normal, reset_runtime, ctr
import random_order as RO

IC32 = os.path.join(HERE, "..", "runtime", "c", "ic32")

def norm(src, budget=8_000_000):
    reset_runtime()
    return normal(parse(src), budget=budget)

def batch(cases):
    return TUPN(cases)

def dec_batch(t, n, per):
    return [per(x) for x in _spine(t, n)]

def s_of(v, w):
    return v - (1 << w) if v >= (1 << (w - 1)) else v

def golden(op, w, a, b):
    if op == "add":
        return ((a + b) & ((1 << w) - 1), (a + b) >> w)
    if op == "sub":
        return ((a - b) & ((1 << w) - 1), int(a < b))
    if op == "ltu":
        return int(a < b)
    if op == "eq":
        return int(a == b)
    if op == "sadd" or op == "ssub":
        t = s_of(a, w) + (s_of(b, w) if op == "sadd" else -s_of(b, w))
        lo, hi = -(1 << (w - 1)), (1 << (w - 1)) - 1
        return (max(lo, min(hi, t)), int(not lo <= t <= hi))
    if op == "slt":
        return int(s_of(a, w) < s_of(b, w))

CASE = {"add": (BL.add_case, 2), "sub": (BL.sub_case, 1),
        "ltu": (BL.ltu_case, 1), "eq": (BL.eq_case, 1)}

def run_pairs(op, w, pairs, bsz=64, runner="ref"):
    mk, nfl = CASE.get(op, (None, None))
    bad = []
    for i in range(0, len(pairs), bsz):
        chunk = pairs[i:i + bsz]
        if op in CASE:
            srcs = [mk(w, a, b) for a, b in chunk]
        elif op in ("sadd", "ssub"):
            f = BL.sadd_case if op == "sadd" else BL.ssub_case
            srcs = [f(w, a, b) for a, b in chunk]
        else:
            srcs = [BL.slt_case(w, a, b) for a, b in chunk]
        src = batch(srcs)
        if runner == "ref":
            t = norm(src)
        else:
            r = subprocess.run([IC32], input=src.encode(),
                               capture_output=True, timeout=60)
            out = r.stdout.decode().strip().splitlines()
            reset_runtime()
            t = parse(out[0])
        xs = _spine(t, len(chunk))
        for (a, b), x in zip(chunk, xs):
            if op in ("add",):
                v, fl = BL.dec_flat(x, w, 2)
                g = golden(op, w, a, b)
                okc = (v, fl[0]) == g
            elif op in ("sub",):
                v, fl = BL.dec_flat(x, w, 1)
                okc = (v, fl[0]) == golden(op, w, a, b)
            elif op in ("ltu", "eq", "slt"):
                okc = int(_dec_bool(_spine(x, 1)[0])) == golden(op, w, a, b)
            else:
                v, ovf = BL.dec_val_flag(x, w)
                g = golden(op, w, a, b)
                okc = (s_of(v, w), ovf) == g
            if not okc:
                bad.append((a, b))
    return bad

def main():
    print("[BINDING slice 3b] fixed-width binary arithmetic")
    allok = True
    t_start = time.time()

    # --- A) 4-bit exhaustive, every op
    allp = [(a, b) for a in range(16) for b in range(16)]
    for op in ("add", "sub", "ltu", "eq", "sadd", "ssub", "slt"):
        bad = run_pairs(op, 4, allp)
        ok = not bad
        allok &= ok
        print(f"  [{'PASS' if ok else 'FAIL'}] 4-bit {op} exhaustive "
              f"(256){'' if ok else ' bad=' + str(bad[:3])}")
    negbad = []
    for a in range(16):
        v, fl = BL.dec_flat(norm(BL.neg_case(4, a)), 4, 1)
        if (v, fl[0]) != (((-a) & 15), int(a == 8)):
            negbad.append(a)
    allok &= not negbad
    print(f"  [{'PASS' if not negbad else 'FAIL'}] 4-bit neg exhaustive "
          f"(16, wrap at MIN flagged)")

    # --- B) 8-bit: BUDGET-BOUNDED coverage (review round 8: the old
    # fallback still ran past its own budget; now coverage is computed
    # from the measured rate and reported exactly)
    BUDGET = 240.0
    t0 = time.time()
    probe = [(a, b) for a in range(16) for b in range(0, 256, 16)]
    run_pairs("add", 8, probe, bsz=128)
    rate = (time.time() - t0) / len(probe)
    fit = int((BUDGET - (time.time() - t0)) / rate)
    full3 = 3 * 65536
    print(f"  8-bit: {rate*1000:.2f} ms/case; budget {BUDGET:.0f}s fits "
          f"{fit:,} cases ({min(100.0, 100.0*fit/full3):.0f}% of full "
          f"exhaustive x3)")
    rng = random.Random(1)
    if fit >= full3:
        plan = [("add", [(a, b) for a in range(256) for b in range(256)]),
                ("sub", [(a, b) for a in range(256) for b in range(256)]),
                ("ltu", [(a, b) for a in range(256) for b in range(256)])]
        print("    coverage: FULL exhaustive add+sub+ltu (65,536 each)")
    else:
        n_add = min(65536, max(0, fit - 2 * 4096))
        n_each = max(2048, (fit - n_add) // 2)
        allp8 = [(a, b) for a in range(256) for b in range(256)]
        plan = [("add", allp8[:n_add] if n_add < 65536 else allp8),
                ("sub", [(rng.randrange(256), rng.randrange(256))
                         for _ in range(n_each)]),
                ("ltu", [(rng.randrange(256), rng.randrange(256))
                         for _ in range(n_each)])]
        print(f"    coverage: add {len(plan[0][1]):,}/65,536 "
              f"({100*len(plan[0][1])/65536:.0f}%), sub/ltu random "
              f"{n_each:,} each -- exact counts, not a nominal budget")
    for op, pairs in plan:
        bad = run_pairs(op, 8, pairs, bsz=128)
        allok &= not bad
        print(f"  [{'PASS' if not bad else 'FAIL'}] 8-bit {op} "
              f"x{len(pairs):,}")

    # --- C) 16-bit boundaries + random; widen/trunc round trips
    V = [0, 1, 2, 3, 0x7FFF, 0x8000, 0x8001, 0xFFFE, 0xFFFF,
         0x5555, 0xAAAA, 0x0100]
    grid = [(a, b) for a in V for b in V]
    rng = random.Random(2)
    rnd = [(rng.randrange(1 << 16), rng.randrange(1 << 16))
           for _ in range(1500)]
    for op in ("add", "sub", "ltu"):
        bad = run_pairs(op, 16, grid + rnd, bsz=32)
        allok &= not bad
        print(f"  [{'PASS' if not bad else 'FAIL'}] 16-bit {op} "
              f"boundaries({len(grid)}) + random({len(rnd)})")
    wt = True
    for v in range(256):
        t = norm(BL.widen_case(8, 16, v))
        wv = BL.dec_bits_list(_spine(t, 16))
        t2 = norm(BL.trunc_case(16, 8, wv))
        wt &= (wv == v and BL.dec_bits_list(_spine(t2, 8)) == v)
    allok &= wt
    print(f"  [{'PASS' if wt else 'FAIL'}] widen(8->16)/trunc(16->8) "
          f"round trip, all 256")

    # --- D) signed edges at 8/16 (reviewer's list; MUL items -> 3b.3)
    edges = []
    for w in (8, 16):
        MAX = (1 << (w - 1)) - 1
        MIN = 1 << (w - 1)
        edges += [("sadd", w, MAX, 1), ("ssub", w, MIN, 1),
                  ("sadd", w, MIN, MIN), ("sadd", w, MAX, MAX),
                  ("ssub", w, MIN, MAX), ("sadd", w, 0, 0),
                  ("slt", w, MIN, MAX), ("slt", w, MAX, MIN),
                  ("slt", w, MIN, MIN)]
    ebad = []
    for op, w, a, b in edges:
        if run_pairs(op, w, [(a, b)], bsz=1):
            ebad.append((op, w, a, b))
    for w in (8, 16):
        MINp = 1 << (w - 1)
        v, fl = BL.dec_flat(norm(BL.neg_case(w, MINp)), w, 1)
        if (v, fl[0]) != (MINp, 1):
            ebad.append(("neg-MIN", w))
        v, fl = BL.dec_flat(norm(BL.neg_case(w, 0)), w, 1)
        if (v, fl[0]) != (0, 0):
            ebad.append(("neg-0", w))
    allok &= not ebad
    print(f"  [{'PASS' if not ebad else 'FAIL'}] signed edge battery "
          f"8/16-bit ({len(edges) + 4} cases: MAX+1, MIN-1, MIN+MIN, "
          f"MAX+MAX, -MIN, -0, sign compares)"
          f"{'' if not ebad else ' bad=' + str(ebad)}")

    # --- E) ic32 spot batches
    rng = random.Random(3)
    cok = True
    for op, w in [("add", 4), ("sub", 8), ("sadd", 8), ("ltu", 16)]:
        pairs = [(rng.randrange(1 << w), rng.randrange(1 << w))
                 for _ in range(96)]
        bad = run_pairs(op, w, pairs, bsz=48, runner="c")
        cok &= not bad
        print(f"  [{'PASS' if not bad else 'FAIL'}] ic32 spot: {op} "
              f"w={w} x96")
    allok &= cok

    # --- F) cost distributions (review round 8: the old generator
    # reseeded per iteration, so all 48 "random" pairs were ONE pair;
    # census now exhaustive at 4 bits and asserted, persistent RNG above)
    print("  cost census, 4-bit add EXHAUSTIVE (lazy):")
    cen = {}
    for a in range(16):
        for b in range(16):
            norm(BL.add_case(4, a, b))
            cen[(a, b)] = sum(ctr.values())
    cs = sorted(cen.values())
    mx = max(cen.values())
    am = [k for k, v in cen.items() if v == mx]
    print(f"    min {cs[0]} / mean {statistics.mean(cs):.1f} / median "
          f"{cs[len(cs)//2]} / p95 {cs[int(0.95*len(cs))]} / max {mx} "
          f"({len(set(cs))} unique); max attained at {am}")
    allok &= (cs[0], round(statistics.mean(cs)), mx,
              len(set(cs))) == (86, 94, 102, 9) and (15, 15) in am
    print("  cost distributions, PROPER random samples (lazy):")
    for w, n in [(8, 2000), (16, 500)]:
        rngc = random.Random(50 + w)
        costs = []
        argmx = None
        for _ in range(n):
            a, b = rngc.randrange(1 << w), rngc.randrange(1 << w)
            norm(BL.add_case(w, a, b))
            c = sum(ctr.values())
            if argmx is None or c > argmx[0]:
                argmx = (c, a, b)
            costs.append(c)
        costs.sort()
        print(f"    w={w:>2} add x{n}: min {costs[0]} / mean "
              f"{statistics.mean(costs):.1f} / median {costs[n//2]} / "
              f"p95 {costs[int(0.95*n)]} / p99 {costs[int(0.99*n)]} / "
              f"max {costs[-1]} (max at a={argmx[1]},b={argmx[2]})")
    eager = []
    rngc = random.Random(99)
    for _ in range(8):
        a, b = rngc.randrange(16), rngc.randrange(16)
        reset_runtime()
        _, n2 = RO.strategy_normal(parse(BL.add_case(4, a, b)),
                                   lambda rs: rs[0])
        eager.append(n2)
    print(f"    strategy sample, 4-bit add x8 under 'first': "
          f"min {min(eager)} max {max(eager)} (Law 4)")

    # --- G) 3b.2c DYNAMIC OPERANDS (review round 8): reusable
    # combinators fed runtime-encoded values, incl. chaining
    print("  dynamic combinators (runtime operands, not literals):")
    def run_dyn(op, w, pairs, bsz=48, runner="ref"):
        bad = []
        for i in range(0, len(pairs), bsz):
            chunk = pairs[i:i + bsz]
            if op == "neg":
                srcs = [f"({BL.dyn_neg(w)} {BL.enc_operand(a, w)})"
                        for a, _ in chunk]
            else:
                srcs = [f"(({BL.dyn_case(op, w)} {BL.enc_operand(a, w)})"
                        f" {BL.enc_operand(b, w)})" for a, b in chunk]
            t = None
            src2 = batch(srcs)
            if runner == "ref":
                t = norm(src2)
            else:
                r = subprocess.run([IC32], input=src2.encode(),
                                   capture_output=True, timeout=90)
                out = r.stdout.decode().strip().splitlines()
                reset_runtime()
                t = parse(out[0])
            for (a, b), x in zip(chunk, _spine(t, len(chunk))):
                if op == "add":
                    v, fl = BL.dec_flat(x, w, 2)
                    okc = (v, fl[0]) == golden(op, w, a, b)
                elif op == "sub":
                    v, fl = BL.dec_flat(x, w, 1)
                    okc = (v, fl[0]) == golden(op, w, a, b)
                elif op == "neg":
                    v, fl = BL.dec_flat(x, w, 1)
                    okc = (v, fl[0]) == (((-a) & ((1 << w) - 1)),
                                         int(a == 1 << (w - 1)))
                elif op in ("ltu", "eq", "slt"):
                    okc = int(_dec_bool(_spine(x, 1)[0])) ==                         golden(op, w, a, b)
                else:
                    v, ovf = BL.dec_val_flag(x, w)
                    okc = (s_of(v, w), ovf) == golden(op, w, a, b)
                if not okc:
                    bad.append((a, b))
        return bad
    for op in ("add", "sub", "ltu", "eq", "sadd", "ssub", "slt", "neg"):
        pairs = allp if op != "neg" else [(a, 0) for a in range(16)]
        bad = run_dyn(op, 4, pairs)
        allok &= not bad
        print(f"  [{'PASS' if not bad else 'FAIL'}] dynamic 4-bit {op} "
              f"exhaustive")
    rngd = random.Random(7)
    for op in ("add", "sub"):
        pairs = [(rngd.randrange(256), rngd.randrange(256))
                 for _ in range(1500)]
        bad = run_dyn(op, 8, pairs, bsz=64)
        allok &= not bad
        print(f"  [{'PASS' if not bad else 'FAIL'}] dynamic 8-bit {op} "
              f"random x1500")
    V16 = [0, 1, 0x7FFF, 0x8000, 0xFFFF, 0x5555]
    g16 = [(a, b) for a in V16 for b in V16] +           [(rngd.randrange(1 << 16), rngd.randrange(1 << 16))
           for _ in range(300)]
    for op in ("add", "sub", "ltu"):
        bad = run_dyn(op, 16, g16, bsz=24)
        allok &= not bad
        print(f"  [{'PASS' if not bad else 'FAIL'}] dynamic 16-bit {op} "
              f"boundaries+random x{len(g16)}")
    wt_ok = True
    wcost = tcost = 0
    for v in range(256):
        t = norm(f"({BL.dyn_widen(8, 16)} {BL.enc_operand(v, 8)})")
        wcost = sum(ctr.values())
        wv = BL.dec_bits_list(_spine(t, 16))
        t = norm(f"({BL.dyn_trunc(16, 8)} {BL.enc_operand(wv, 16)})")
        tcost = sum(ctr.values())
        wt_ok &= BL.dec_bits_list(_spine(t, 8)) == v
    allok &= wt_ok and wcost > 0 and tcost > 0
    print(f"  [{'PASS' if wt_ok else 'FAIL'}] dynamic widen/trunc as "
          f"REDUCER ops, all 256 ({wcost}/{tcost} interactions -- "
          f"circuits now, not encoders)")
    ch_ok = True
    for _ in range(300):
        a, b, c = (rngd.randrange(256) for _ in range(3))
        srcc = (f"(({BL.dyn_case('add', 8)} ({BL.dyn_take_value(8, 2)} "
                f"(({BL.dyn_case('add', 8)} {BL.enc_operand(a, 8)}) "
                f"{BL.enc_operand(b, 8)}))) {BL.enc_operand(c, 8)})")
        v, _ = BL.dec_flat(norm(srcc), 8, 2)
        ch_ok &= v == (a + b + c) & 255
    for _ in range(300):
        a, b = rngd.randrange(256), rngd.randrange(256)
        srcc = (f"(({BL.dyn_case('sadd', 8)} ({BL.dyn_take_value(8, 1)} "
                f"({BL.dyn_neg(8)} {BL.enc_operand(a, 8)}))) "
                f"{BL.enc_operand(b, 8)})")
        v, ovf = BL.dec_val_flag(norm(srcc), 8)
        tg = -s_of(a, 8) if a != 128 else -128
        tt = tg + s_of(b, 8)
        exp = (max(-128, min(127, tt)), int(not -128 <= tt <= 127))
        ch_ok &= (s_of(v, 8), ovf) == exp
    allok &= ch_ok
    print(f"  [{'PASS' if ch_ok else 'FAIL'}] CHAINED dynamics x600: "
          f"add8(add8(a,b),c) and sadd8(neg8(a),b) -- fresh instances "
          f"per occurrence, flag-strip adapters between stages")
    dbad = run_dyn("add", 8, [(rngd.randrange(256), rngd.randrange(256))
                              for _ in range(96)], bsz=48, runner="c")
    allok &= not dbad
    print(f"  [{'PASS' if not dbad else 'FAIL'}] ic32 dynamic add8 x96")
    for w in (4, 8, 16):
        rngc = random.Random(70 + w)
        dc, cc = [], []
        for _ in range(24):
            a, b = rngc.randrange(1 << w), rngc.randrange(1 << w)
            norm(f"(({BL.dyn_case('add', w)} {BL.enc_operand(a, w)}) "
                 f"{BL.enc_operand(b, w)})")
            dc.append(sum(ctr.values()))
            norm(BL.add_case(w, a, b))
            cc.append(sum(ctr.values()))
        print(f"    dynamic-vs-constant add w={w}: dyn mean "
              f"{statistics.mean(dc):.0f} vs const mean "
              f"{statistics.mean(cc):.0f} (the operand-plumbing tax)")

    # --- H) round-9 pins: convention witness + dynamic signed
    # sign-class battery (permanent; adjudicates any source-level
    # convention disagreement by execution)
    assert BL.convention_witness(lambda s: norm(s)), \
        "Scott convention shifted -- every clamp reading is now suspect"
    print(f"  convention witness: {BL.CONVENTION}  [ASSERTED]")
    sc_ok = True
    for w in (8, 16):
        MAXv = (1 << (w - 1)) - 1
        MINv = 1 << (w - 1)
        NEG1 = (1 << w) - 1
        for op, a, b in [("ssub", MAXv, NEG1), ("ssub", MINv, 1),
                         ("ssub", NEG1, MINv), ("ssub", 0, MINv),
                         ("sadd", MAXv, 1), ("sadd", MINv, NEG1),
                         ("sadd", MAXv, MAXv), ("sadd", MINv, MINv)]:
            if run_dyn(op, w, [(a, b)], bsz=1):
                sc_ok = False
                print(f"  [FAIL] sign-class {op} w={w} a={a} b={b}")
    allok &= sc_ok
    print(f"  [{'PASS' if sc_ok else 'FAIL'}] dynamic signed sign-class "
          f"battery (16 named cases incl. the 127-(-1) class, 0-MIN, "
          f"MIN+MIN) -- pinned per round 9")

    dt = time.time() - t_start
    print(f"\n  {'SLICE 3b.1+3b.2: PASS' if allok else 'SLICE 3b: FAIL'} "
          f"({dt:.0f}s)  -- unsigned+signed fixed-width arithmetic "
          f"verified on the real reducers; 3b.3 (fixed-point multiply) "
          f"unblocked")
    return 0 if allok else 1

if __name__ == "__main__":
    raise SystemExit(main())
