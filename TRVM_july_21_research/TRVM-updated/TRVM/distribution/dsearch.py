"""
dsearch.py -- Distributed superposed search on the correct IC core (ic_ref.py).

Arc:
  step 1 (ic_ref.py) : a CORRECT Interaction Calculus reducer (higher-order
                       duplication works) -- the prerequisite for superposition.
  step 2 (this file) : SUPERPOSED SEARCH as the workload, then DISTRIBUTED
                       across real threads, coordination-free.

Two claims, each checked against a brute-force oracle:

 (A) Superposition evaluates many candidates in ONE reduction, sharing the work
     that's common across them (HVM's "discrete program search" idea).

 (B) Search is MONOTONE (solutions only accumulate; candidates independent).
     By CALM, monotone => coordination-free. Partition the space across threads,
     each writes a grow-only set (G-Set CRDT, join = union); the result is
     identical for every schedule. Termination is a plain join -- the workload is
     so cleanly monotone that the Safra detector p2.py needed for the
     boundary-crossing reducer isn't required here.

Design note (why it's encoded this way):
  A predicate that DUPLICATES a higher-order candidate and applies a copy to
  another lambda makes this reducer diverge (a real limitation of the simple
  body-carrying representation; the packed floating-dup runtime handles it). So
  each candidate is a PAIR (numeral, tag) consumed LINEARLY by a dup-free
  selector: the numeral is applied to NOT directly (never as a dup-copy), and the
  only thing duplicated is the linear selector (clean -- no internal labels).

Toy problem: domain = 0..N-1, predicate = "n is odd" via ((n NOT) FALSE).
Each candidate carries a tag T<n>; survivors collapse to their tags => recover n.
"""

import ic_ref as ic
from ic_ref import App, Var, Era, Sup, parse, normal, show, reset_runtime, ctr

FAN = 7                       # shared search-fan label (aligns/duplicates branches)
_lab = [1000]
def nlab():
    _lab[0] += 1; return _lab[0]

def church(n):
    if n == 0: return 'λf.λx.x'
    if n == 1: return 'λf.λx.(f x)'
    cs = [f'c{i}' for i in range(n)]; src = []; cur = 'f'
    for i in range(n-1):
        L = nlab(); nxt = f't{i}' if i < n-2 else cs[-1]
        src.append(f'!&{L}{{{cs[i]},{nxt}}}={cur};'); cur = nxt
    body = 'x'
    for c in reversed(cs): body = f'({c} {body})'
    return 'λf.λx.' + ''.join(src) + body

NOT   = 'λp.λt.λf.((p f) t)'
TRUE  = 'λa.λb.a'
FALSE = 'λa.λb.b'

# selector receives (num, tag) separately from a pair; num used once (parity),
# tag used once (output). is_odd(num)=((num NOT) FALSE); body=((is_odd tag) *).
SELECTOR = f'λnum.λtag.(((( num {NOT}) {FALSE}) tag) *)'

def candidate(i):
    """A pair holding church(i) and a free-var tag T<i>, applied to a selector."""
    return f'λs.((s {church(i)}) T{i})'

def sup_tree(srcs, lab):
    if len(srcs) == 1: return srcs[0]
    out = srcs[-1]
    for s in reversed(srcs[:-1]):
        out = f'&{lab}{{{s},{out}}}'
    return out

def _flatten_tags(t, out, junk):
    if isinstance(t, Era):
        return
    if isinstance(t, Sup):
        _flatten_tags(t.lft, out, junk); _flatten_tags(t.rgt, out, junk); return
    if isinstance(t, Var) and isinstance(t.nam, tuple) and t.nam[0] == 'free' \
       and t.nam[1].startswith('T'):
        out.append(int(t.nam[1][1:])); return
    junk.append(show(t))

def search_superposed(slice_ints):
    """All candidates in ONE reduction. Returns (solset, interactions, junk)."""
    reset_runtime()
    fan = sup_tree([candidate(i) for i in slice_ints], FAN)
    nf = normal(parse(f'({fan} {SELECTOR})'))
    out, junk = [], []
    _flatten_tags(nf, out, junk)
    return set(out), sum(ctr.values()), junk

def search_separate(slice_ints):
    """Baseline: each candidate its own reduction. Returns (solset, interactions)."""
    sols = set(); total = 0
    for i in slice_ints:
        reset_runtime()
        nf = normal(parse(f'({candidate(i)} {SELECTOR})'))
        out, junk = [], []
        _flatten_tags(nf, out, junk)
        sols |= set(out); total += sum(ctr.values())
    return sols, total

def oracle(slice_ints):
    return {i for i in slice_ints if i % 2 == 1}

if __name__ == "__main__":
    print("=== Part A: superposed search vs brute-force oracle ===\n")
    allok = True
    for N in (4, 6, 8, 10):
        dom = list(range(N))
        s_sol, s_ic, junk = search_superposed(dom)
        b_sol, b_ic = search_separate(dom)
        exp = oracle(dom)
        ok = (s_sol == exp == b_sol) and not junk
        allok &= ok
        print(f"domain 0..{N-1}:  oracle={sorted(exp)}")
        print(f"  superposed : {sorted(s_sol)}   [{s_ic} interactions]"
              + (f"  JUNK={junk}" if junk else ""))
        print(f"  separate   : {sorted(b_sol)}   [{b_ic} interactions]")
        print(f"  {'OK' if ok else 'MISMATCH'}\n")
    print("PART A: ALL OK" if allok else "PART A: FAILURES")

# ===========================================================================
# Part B: coordination-free distribution
# ===========================================================================
# Each "node" gets its OWN reducer heap by running in its OWN process (faithful
# to "node = isolated heap"; cf. p2.py which gave each worker its own heap for
# the boundary-crossing reducer). Per-node solution sets are merged with a
# grow-only-set (G-Set) union -- a CRDT join: commutative, idempotent, monotone.
# CALM: monotone => coordination-free => the merge order cannot change the result.
import multiprocessing as mp
import random, time

def _slice_solve(args):
    slice_ints, use_sup = args
    if use_sup:
        sols, _, _ = search_superposed(slice_ints)
    else:
        sols, _ = search_separate(slice_ints)
    return frozenset(sols)

def run_distributed(N, W, use_sup=True, merge_seed=0):
    """Partition 0..N-1 across W processes; union the per-node solution sets in a
    randomized order. Returns (solution_set, slices)."""
    domain = list(range(N))
    slices = [domain[i::W] for i in range(W)]      # round-robin partition
    slices = [s for s in slices if s]
    with mp.Pool(processes=len(slices)) as pool:
        partial = pool.map(_slice_solve, [(s, use_sup) for s in slices])
    rng = random.Random(merge_seed)
    order = list(range(len(partial))); rng.shuffle(order)
    gset = set()
    for k in order:                                 # G-Set join = union
        gset |= partial[k]
    return gset, slices

def _timed(N, W, use_sup=True):
    t0 = time.time()
    sol, _ = run_distributed(N, W, use_sup)
    return sol, time.time() - t0

if __name__ == "__main__" and __import__('sys').argv[-1] == 'dist':
    print("=== Part B: coordination-free distributed search ===\n")
    N = 16
    exp = oracle(range(N))
    print(f"domain 0..{N-1}   oracle (odds) = {sorted(exp)}\n")

    # (1) correctness + schedule-independence across node counts and merge orders
    results = {}
    for W in (1, 2, 3, 4, 6, 8):
        for seed in (0, 1, 2):
            sol, slices = run_distributed(N, W, use_sup=True, merge_seed=seed)
            results[(W, seed)] = frozenset(sol)
    matches = all(v == exp for v in results.values())
    distinct = {v for v in results.values()}
    print(f"  ran {len(results)} configs  (W in 1..8) x (3 merge orders)")
    print(f"  every result == oracle : {matches}")
    print(f"  distinct results       : {len(distinct)}  (1 => schedule-independent)")
    print(f"  example partition (W=4): {[s for s in (lambda d:[d[i::4] for i in range(4)])(list(range(N)))]}")

    # (2) real parallel speedup across processes (reduction is CPU-bound)
    print("\n  wall-clock, same domain, more nodes:")
    base = None
    for W in (1, 2, 4):
        sol, dt = _timed(N, W, use_sup=False)   # separate-per-candidate = heavier per node
        assert sol == exp
        if base is None: base = dt
        print(f"    W={W}:  {dt*1000:7.1f} ms   speedup {base/dt:4.2f}x")

    print("\n  Termination: a plain join() -- no in-flight cross-node messages, so the")
    print("  Safra detector p2.py needed for the boundary-crossing reducer is unnecessary.")
    print("  The workload is *embarrassingly* monotone: the strongest form of CALM-safe.")
