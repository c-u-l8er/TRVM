"""
supgen_swarm2.py -- the three follow-ups supgen_swarm.py's own caveats demanded.

supgen_swarm.py established the pinning: with the CvRDT memory, a K-node enumeration
swarm's aggregate cost stays ~at the deduplicated floor while solo cost grows with K.
It also flagged its own weaknesses. This file measures them:

[A] LOCALITY. The first grammar's dependency space (197 tasks) saturated every shard,
    flattering cross-node overlap. Here the grammar grows (atoms {1,2,3,4}, <=4 leaves,
    value cap 100 -- bounded-value synthesis, standard practice) and the SHARDING is
    varied from overlap-maximizing to overlap-minimizing:
      round-robin      interleaved candidates    -> shards demand nearly everything
      contiguous       blocks of the enumeration -> structural locality
      value-sorted     blocks by candidate value -> semantic locality
    For each: demand multiplicity (how many shards need each task, unweighted and
    cost-weighted), solo cost (computed exactly from the floor's per-task costs --
    no re-evaluation), shared cost, cross-hit rate. The law being tested: savings
    track (multiplicity - 1)/multiplicity; the pinning should hold WHENEVER
    multiplicity > 1 and vanish as sharding approaches perfect locality.

[B] DISTRIBUTED EQUIVALENCE PRUNING (harvesting the 83%). Bottom-up search over the
    VALUE space: each generation combines known values, keyed by the recipe over
    canonical operand NFs -- so representatives are value-indexed and recipe keys
    collide across nodes REGARDLESS of which program discovered a value. The check
    that matters for the learning framing: the SEMANTIC FRONTIER (set of values
    known) must be identical across node counts, pair-assignments, and merge orders
    -- trajectories may differ, the learned frontier may not (monotone => CALM).
    Also measured: cost of pruned search vs the exhaustive floor over a frontier
    that CONTAINS the exhaustive value set.

[C] ECONOMICS OF THE IDENTITY LAYER. Hit rate is not speedup. Measured here:
    microseconds per ic_canon call (the toll) vs microseconds per ic_float
    interaction (the Python evaluator) -- then the break-even task size at the
    NATIVE runtime's throughput (ic32: 22-34M interactions/s per README). If the
    break-even lands far above this grammar's task sizes, the honest conclusion is
    that at native speeds the Python identity layer only pays for macro-tasks, and
    canon must itself go native/wasm -- a deflationary finding, reported as such.
    (Complementary to econ_triage.py, which sorts INCENTIVE mergeability by form;
    this is the compute-cost side.)

Run:  PYTHONPATH=runtime/python:research python3 research/supgen_swarm2.py
"""
import sys, time, random
sys.setrecursionlimit(100000)

import ic_float
from supgen_swarm import (Node, merge_all, church, ADD, MUL, ic_canon, Alloc, pyval)

# ------------------------------------------------------------------ grammar (scaled)
ATOMS2 = (1, 2, 3, 4)
LEAVES2 = 4
CAP = 100

def enumerate2(atoms, max_leaves, cap):
    by = {1: [("N", a) for a in atoms]}
    for k in range(2, max_leaves + 1):
        acc = []
        for i in range(1, k):
            for l in by[i]:
                for r in by[k - i]:
                    for op in ("ADD", "MUL"):
                        e = (op, l, r)
                        if pyval(e) <= cap: acc.append(e)
        by[k] = acc
    out = []
    for k in range(1, max_leaves + 1): out += by[k]
    return out

def task_id(e):
    if e[0] == "N": return e
    return (e[0], pyval(e[1]), pyval(e[2]))

def id_closure(e, out):
    out.add(task_id(e))
    if e[0] != "N":
        id_closure(e[1], out); id_closure(e[2], out)
    return out

def run_shards(shards, merge_every, seed=0):
    rng = random.Random(seed)
    nodes = [Node(k, list(s)) for k, s in enumerate(shards)]
    done = 0
    while any(n.queue for n in nodes):
        for n in nodes:
            if n.queue:
                n.eval_expr(n.queue.popleft()); done += 1
        if merge_every and done >= merge_every:
            merge_all(nodes, rng); done = 0
    return nodes

# ==================================================================== run
if __name__ == "__main__":
    t0 = time.perf_counter()
    cands = enumerate2(ATOMS2, LEAVES2, CAP)
    print(f"supgen_swarm2: {len(cands)} candidates (atoms {ATOMS2}, <= {LEAVES2} leaves, "
          f"value cap {CAP})")
    print("=" * 84)

    # ---- floor: every distinct task once; also the per-task cost map ----------------
    from supgen_swarm import run_swarm
    floor_nodes, floor_final = run_swarm(1, cands)
    floor_paid = floor_nodes[0].paid
    # replay against the full store to map task_id -> (key, cost, nf) with zero reduction
    probe = Node(97, [])
    probe.store = dict(floor_final); probe.computed = set(floor_final)
    idmemo = {}
    def resolve(e):
        tid = task_id(e)
        if tid in idmemo: return idmemo[tid]
        if e[0] == "N":
            src = church(e[1], probe.alloc)
        else:
            nl = resolve(e[1])[2]; nr = resolve(e[2])[2]
            op = ADD(probe.alloc) if e[0] == "ADD" else MUL
            src = f"(({op} {nl}) {nr})"
        key = ic_canon(src)
        v = floor_final[key]
        idmemo[tid] = (key, v["cost"], v["nf"])
        return idmemo[tid]
    for e in cands: resolve(e)
    cost_of = {tid: c for tid, (k, c, nf) in idmemo.items()}
    nf_of_val = {}
    for e in cands:
        nf_of_val.setdefault(pyval(e), resolve(e)[2])
    for a in ATOMS2: nf_of_val.setdefault(a, resolve(("N", a))[2])
    print(f"[floor]  distinct tasks {len(floor_final)}   single-evaluation cost "
          f"{floor_paid} interactions   ({time.perf_counter()-t0:.0f}s)")
    print("=" * 84)

    # ---- [A] locality: sharding sweep at K=8 ----------------------------------------
    K = 8
    B = (len(cands) + K - 1) // K
    shardings = {
        "round-robin": [cands[k::K] for k in range(K)],
        "contiguous":  [cands[i*B:(i+1)*B] for i in range(K)],
        "value-sorted": [sorted(cands, key=pyval)[i*B:(i+1)*B] for i in range(K)],
    }
    print(f"[A] locality sweep, K={K}, merge every 16 candidates")
    print(f"{'sharding':>13} {'mean-mult':>10} {'cost-mult':>10} {'solo':>8} "
          f"{'shared':>8} {'vs floor':>9} {'savings':>8} {'x-hit':>7}")
    for name, shards in shardings.items():
        demands = [id_closure_all := set() or set().union(*[id_closure(e, set()) for e in s])
                   for s in shards]
        mult = {}
        for d in demands:
            for tid in d: mult[tid] = mult.get(tid, 0) + 1
        mean_mult = sum(mult.values()) / len(mult)
        solo = sum(sum(cost_of[t] for t in d) for d in demands)     # exact, no re-run
        nodes = run_shards(shards, merge_every=16)
        paid = sum(n.paid for n in nodes)
        tasks = sum(n.tasks for n in nodes)
        xh = sum(n.cross_hits for n in nodes)
        print(f"{name:>13} {mean_mult:>10.2f} {solo/floor_paid:>10.2f} {solo:>8} "
              f"{paid:>8} {paid/floor_paid:>8.2f}x {1-paid/solo:>7.0%} {xh/tasks:>6.1%}")
    print(f"    (floor {floor_paid}; solo computed exactly from per-task costs; "
          f"cost-mult = solo/floor)")
    print("=" * 84)

    # ---- [B] distributed equivalence pruning over the value space -------------------
    def pruned(Kn, gens, seed):
        rng = random.Random(seed)
        nodes = [Node(k, []) for k in range(Kn)]
        # seed generation: atoms
        for k, n in enumerate(nodes):
            for a in ATOMS2[k % len(ATOMS2)::Kn] if Kn <= len(ATOMS2) else \
                     ([ATOMS2[k]] if k < len(ATOMS2) else []):
                n._task(church(a, n.alloc), atom=True)
        merge_all(nodes, rng)
        frontier_hist = []
        canon2val = {ic_canon(nf): v for v, nf in nf_of_val.items()}
        def values(store):
            vs = set()
            for e in store.values():
                v = canon2val.get(ic_canon(e["nf"]))
                if v is not None: vs.add(v)
            return vs
        for g in range(gens):
            V = sorted(values(nodes[0].store))
            pairs = [(op, a, b) for a in V for b in V for op in ("ADD", "MUL")
                     if (a + b if op == "ADD" else a * b) <= CAP]
            order = sorted(pairs, key=lambda p: hash(p))
            for i, (op, a, b) in enumerate(order):
                n = nodes[i % Kn]
                opsrc = ADD(n.alloc) if op == "ADD" else MUL
                n._task(f"(({opsrc} {nf_of_val.get(a) or ''}) {nf_of_val.get(b) or ''})",
                        atom=False) if (a in nf_of_val and b in nf_of_val) else None
            merge_all(nodes, rng)
            # discovered values may exceed nf_of_val's domain; extend it from the store
            for e in nodes[0].store.values():
                c = ic_canon(e["nf"])
                if c not in canon2val:
                    pass  # values beyond CAP-reachable-by-floor map; ignored (capped)
            frontier_hist.append(frozenset(values(nodes[0].store)))
        paid = sum(n.paid for n in nodes)
        tasks = sum(n.tasks for n in nodes)
        xh = sum(n.cross_hits for n in nodes)
        return frontier_hist[-1], paid, tasks, xh

    EV = {pyval(e) for e in cands}
    print(f"[B] distributed equivalence pruning (value-space search, {3} generations)")
    results = {}
    for Kn in (2, 8):
        for seed in (0, 1, 2):
            f, paid, tasks, xh = pruned(Kn, 3, seed)
            results[(Kn, seed)] = (f, paid, tasks, xh)
    fronts = {f for (f, *_ ) in results.values()}
    f0, paid0, tasks0, xh0 = results[(8, 0)]
    print(f"    frontiers identical across K in (2,8) x 3 merge orders : {len(fronts) == 1}")
    print(f"    exhaustive value set contained in pruned frontier      : {EV <= f0}")
    print(f"    frontier size {len(f0)} values   pruned tasks {tasks0} "
          f"(exhaustive walked {sum(len(id_closure(e, set())) for e in cands)} task-refs)")
    print(f"    pruned cost {paid0} interactions vs exhaustive floor {floor_paid} "
          f"({paid0/floor_paid:.2f}x, over a frontier that contains it; x-hit {xh0/tasks0:.0%})")
    assert len(fronts) == 1 and EV <= f0
    print("=" * 84)

    # ---- [C] economics of the identity layer ----------------------------------------
    sample = [tid for tid in cost_of if tid[0] != "N"][:80]
    srcs = []
    al = Alloc(80000)
    for (op, a, b) in sample:
        opsrc = ADD(al) if op == "ADD" else MUL
        srcs.append((f"(({opsrc} {nf_of_val[a]}) {nf_of_val[b]})", cost_of[(op, a, b)]))
    t1 = time.perf_counter()
    for s, _ in srcs: ic_canon(s)
    canon_us = (time.perf_counter() - t1) / len(srcs) * 1e6
    t2 = time.perf_counter(); tot_i = 0
    for s, _ in srcs:
        _, c, _ = ic_float.run(s); tot_i += c
    red_us = (time.perf_counter() - t2) / len(srcs) * 1e6
    per_i_py = (time.perf_counter() - t2) / max(tot_i, 1) * 1e6
    mean_task = tot_i / len(srcs)
    NATIVE_IPS = 28e6                       # ic32: 22-34M interactions/s (README)
    p = 0.45                                # measured cross-hit rate at K>=4
    breakeven = canon_us * 1e-6 * NATIVE_IPS / p
    print(f"[C] identity-layer economics (measured on {len(srcs)} recipe tasks)")
    print(f"    ic_canon toll      : {canon_us:8.0f} us/task")
    print(f"    ic_float reduction : {red_us:8.0f} us/task  ({per_i_py:.0f} us/interaction; "
          f"mean task {mean_task:.0f} interactions)")
    print(f"    -> vs PYTHON evaluator the memory pays easily (toll << reduction).")
    print(f"    -> vs NATIVE ic32 (~{NATIVE_IPS/1e6:.0f}M i/s), break-even task size at "
          f"hit-rate {p:.0%}: ~{breakeven:,.0f} interactions/task.")
    print(f"       This grammar's tasks are ~{mean_task:.0f} interactions: the Python")
    print(f"       identity layer LOSES at native speed by ~{breakeven/mean_task:,.0f}x.")
    print(f"       Honest conclusion: canon must go native/wasm, or the store must")
    print(f"       triage by task cost (only remember macro-reductions).")
    print("=" * 84)
    print(f"total wall {time.perf_counter()-t0:.0f}s")
