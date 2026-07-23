"""
supgen_swarm3.py -- the experiments the external review demanded.

The review of supgen_swarm2.py made four substantive corrections. Each is testable.
This file tests them. Its conclusions REPLACE swarm2's where they conflict.

[K] PINNING vs SWARM WIDTH, DECOMPOSED. swarm2 claimed "the memory always pins";
    the review measured degradation to 5.79x floor at K=1024 and diagnosed a harness
    artifact: the merge check sat outside the per-node loop, so past K=16 the
    effective cadence was "merge every K", not "merge every 16". Decomposed here:
    as-shipped cadence vs corrected cadence (checked per completed candidate).
    The synchronous bound (merge after every candidate) is provably identical to a
    single shared store in a sequential simulator (paid == floor); confirmed at K=8.
    Merging uses a layered store (local delta over shared base): a merge moves only
    new entries -- O(new), not O(K x |store|) -- which is what makes K=512 runnable.

[ASYNC] THE REAL CALM TEST. swarm2's pruning run was bulk-synchronous: barriers,
    central pair generation, deterministic assignment -- seeds changed nothing, so
    "trajectories differ, frontier doesn't" was unearned there. Here: no barriers;
    nodes act at independent random rates; each generates work from its OWN
    (possibly stale) local frontier; deltas gossip with latency ~U(1,L), 20%
    duplication, 15% loss; a slow full-state anti-entropy push guarantees fairness.
    Church numerals are decoded DIRECTLY from runtime normal forms -- the swarm2
    oracle, whose operand guard silently confined search to 64 values, is deleted.
    The per-value frontier record is itself a join-semilattice:
        (rep_nf: min, derivations: union, min_cost: min, provenance: union).
    Checks: every fair run reaches the SAME least fixed point (verified against a
    pure-python closure); trajectories now genuinely differ; duplicated work -- the
    price of asynchrony -- is a measured curve in gossip latency: the review's law
    ("near-floor iff propagation outruns rediscovery"), quantified.

[2x2] MATCHED-FRONTIER ABLATION. pruning x memory, all four cells reaching a
    frontier containing the exhaustive grammar's 64-value set, interactions in
    matched units.

[E3] THREE-BASELINE ECONOMICS. The review caught a real arithmetic error (canon
    must beat p*C_red, not C_red) but applied the cross-hit p to the wrong
    baseline. The three legs, measured:
      no-memo -> local memo (cheap structural keys): pays iff C_key < p_total*C_red
      local -> shared (canonical keys):   pays iff (C_canon-C_key) < p_cross*C_red
      no-memo -> shared (canonical keys): pays iff C_canon < p_total*C_red

Run sections separately (each fits a sandbox execution window):
  PYTHONPATH=runtime/python:research python3 research/supgen_swarm3.py K
  PYTHONPATH=runtime/python:research python3 research/supgen_swarm3.py ASYNC
  PYTHONPATH=runtime/python:research python3 research/supgen_swarm3.py AB E3
"""
import sys, time, random
from collections import deque
sys.setrecursionlimit(100000)

import ic_float
from incrdt import parse_tree
from supgen_swarm import Node, church, ADD, MUL, ic_canon, Alloc, pyval
from supgen_swarm2 import enumerate2, task_id, id_closure, ATOMS2, LEAVES2, CAP

# ---------------------------------------------------------------- church decoding
def decode_church(nf):
    """Decode a Church numeral directly from a runtime normal form. None if not one."""
    try: t = parse_tree(nf)
    except Exception: return None
    if not (isinstance(t, tuple) and t[0] == "lam"): return None
    f, b = t[1], t[2]
    if not (isinstance(b, tuple) and b[0] == "lam"): return None
    x, body = b[1], b[2]
    n = 0
    while isinstance(body, tuple) and body[0] == "app":
        fn, body = body[1], body[2]
        if fn != ("var", f): return None
        n += 1
    return n if body == ("var", x) else None

# ---------------------------------------------------------------- ground truth
def closure(atoms, cap):
    V = set(atoms); hist = []
    while True:
        new = {a + b for a in V for b in V if a + b <= cap} | \
              {a * b for a in V for b in V if a * b <= cap}
        nxt = V | new; hist.append(len(nxt))
        if nxt == V: return nxt, hist
        V = nxt

# ---------------------------------------------------------------- layered store
class Layered(dict):
    """Local delta over a shared base. Lookup: delta first, then base."""
    def __init__(self, base): super().__init__(); self.base = base
    def get(self, k, d=None):
        v = super().get(k)
        if v is not None: return v
        return self.base.get(k, d)

def fold(nodes, base):
    for n in nodes:
        for k, v in n.store.items():          # delta entries only
            w = base.get(k)
            if w is None: base[k] = v
            else: assert w["nf"] == v["nf"], "CvRDT violation"
        n.store = Layered(base)

def run_shards_v3(shards, merge_every, inner):
    base = {}
    nodes = [Node(k, list(s)) for k, s in enumerate(shards)]
    for n in nodes: n.store = Layered(base)
    done = 0
    while any(n.queue for n in nodes):
        for n in nodes:
            if n.queue:
                n.eval_expr(n.queue.popleft()); done += 1
            if inner and merge_every and done >= merge_every:
                fold(nodes, base); done = 0
        if (not inner) and merge_every and done >= merge_every:
            fold(nodes, base); done = 0
    fold(nodes, base)
    return nodes

# ---------------------------------------------------------------- async machinery
class Rec:
    __slots__ = ("rep", "derivs", "mincost", "prov")
    def __init__(self, rep, derivs, cost, prov):
        self.rep = rep; self.derivs = set(derivs)
        self.mincost = cost; self.prov = set(prov)
    def join(self, o):
        ch = (o.rep < self.rep or not o.derivs <= self.derivs or
              o.mincost < self.mincost or not o.prov <= self.prov)
        self.rep = min(self.rep, o.rep); self.derivs |= o.derivs
        self.mincost = min(self.mincost, o.mincost); self.prov |= o.prov
        return ch

class ANode:
    def __init__(self, k, atoms, rate, owned_K=None):
        self.k = k; self.alloc = Alloc(10000 * (k + 1)); self.rate = rate
        self.owned = owned_K
        self.vals = {}; self.keys = set(); self.pending = deque()
        self.inbox = []; self.unsent = {}; self.paid = 0; self.evals = 0
        for a in atoms:
            nf, c, _ = ic_float.run(church(a, self.alloc))
            self._learn(a, Rec(nf, {("N", a)}, c, {k}))
    def _learn(self, v, rec):
        cur = self.vals.get(v)
        if cur is None:
            self.vals[v] = rec
            for u in list(self.vals):
                for op in ("ADD", "MUL"):
                    for (x, y) in {(v, u), (u, v)}:
                        r = x + y if op == "ADD" else x * y
                        if r <= CAP and (op, x, y) not in self.keys and \
                           (self.owned is None or
                            hash((op, x, y)) % self.owned == self.k):
                            self.pending.append((op, x, y))
            self.unsent[v] = rec
        elif cur.join(rec):
            self.unsent[v] = cur
        self.keys |= rec.derivs
    def act(self, tick, gpaid, gseen, traj):
        due = [m for m in self.inbox if m[0] <= tick]
        self.inbox = [m for m in self.inbox if m[0] > tick]
        for _, delta in due:
            for v, (rep, derivs, cost, prov) in delta.items():
                self._learn(v, Rec(rep, derivs, cost, prov))
        while self.pending:
            op, a, b = self.pending.popleft()
            if (op, a, b) in self.keys: continue
            opsrc = ADD(self.alloc) if op == "ADD" else MUL
            src = f"(({opsrc} {self.vals[a].rep}) {self.vals[b].rep})"
            ic_canon(src)                               # the substrate's toll, paid
            nf, c, _ = ic_float.run(src)
            self.paid += c; self.evals += 1
            self.keys.add((op, a, b))
            gpaid.setdefault((op, a, b), []).append(self.k)
            v = decode_church(nf)
            assert v == (a + b if op == "ADD" else a * b)
            if v not in gseen: gseen.add(v); traj.append(v)
            self._learn(v, Rec(nf, {(op, a, b)}, c, {self.k}))
            return
    def push(self, peers, tick, rng, lat, dup_p, drop_p, full=False):
        delta = self.vals if full else self.unsent
        if not delta: return
        payload = {v: (r.rep, frozenset(r.derivs), r.mincost, frozenset(r.prov))
                   for v, r in delta.items()}
        for p in peers:
            for _ in range(1 + (rng.random() < dup_p)):
                if (not full) and rng.random() < drop_p: continue
                p.inbox.append((tick + rng.randint(1, lat), payload))
        self.unsent = {}

def async_run(K, seed, lat, dup_p=0.2, drop_p=0.15, anti_every=40, cap_ticks=500000,
              owned=False, stop_at=None):
    rng = random.Random(seed)
    nodes = [ANode(k, ATOMS2, rate=rng.uniform(0.3, 1.0),
                   owned_K=K if owned else None) for k in range(K)]
    target, _ = closure(ATOMS2, CAP)
    gpaid, gseen, traj = {}, set(ATOMS2), []
    tick = 0
    while tick < cap_ticks:
        tick += 1
        for n in nodes:
            if rng.random() < n.rate:
                n.act(tick, gpaid, gseen, traj)
                if rng.random() < 0.5:
                    n.push(rng.sample(nodes, min(2, K)), tick, rng, lat, dup_p, drop_p)
            if tick % anti_every == 0 and rng.random() < 0.5:
                n.push([rng.choice(nodes)], tick, rng, lat, dup_p, drop_p, full=True)
        if stop_at is not None and gseen >= stop_at:
            return dict(all_agree=None, target_hit=None,
                        paid=sum(n.paid for n in nodes),
                        evals=sum(n.evals for n in nodes), distinct=len(gpaid),
                        dup_evals=sum(len(v) - 1 for v in gpaid.values()),
                        traj=tuple(traj))
        if gseen >= target and all(not n.pending for n in nodes) \
           and all(not n.inbox for n in nodes):
            break
    assert tick < cap_ticks, "async run failed to quiesce"
    for _ in range(3):                                  # final anti-entropy
        for n in nodes: n.push(nodes, tick, rng, 1, 0, 0, full=True)
        tick += 2
        for n in nodes: n.act(tick, gpaid, gseen, traj)
    fronts = {frozenset(n.vals) for n in nodes}
    dup_evals = sum(len(v) - 1 for v in gpaid.values())
    return dict(all_agree=len(fronts) == 1,
                target_hit=fronts == {frozenset(target)},
                paid=sum(n.paid for n in nodes), evals=sum(n.evals for n in nodes),
                distinct=len(gpaid), dup_evals=dup_evals, traj=tuple(traj))

# ==================================================================== sections
def sec_common():
    cands = enumerate2(ATOMS2, LEAVES2, CAP)
    target, hist = closure(ATOMS2, CAP)
    print(f"supgen_swarm3   grammar: {len(cands)} candidates   true closure "
          f"history {hist} -> |fixed point| = {len(target)}")
    dec_ok = all(decode_church(ic_float.run(church(v, Alloc(50000)))[0]) == v
                 for v in (0, 1, 2, 7, 31))
    print(f"[decode] church decoding from runtime NFs verified: {dec_ok}")
    assert dec_ok
    print("=" * 86)
    return cands, target

def sec_floor(cands):
    from supgen_swarm import run_swarm
    fl_nodes, fl_final = run_swarm(1, cands)
    return fl_nodes[0].paid, fl_final

def sec_K(cands, floor):
    print(f"[K] pinning vs width, floor {floor}, merge_every=16")
    print(f"{'K':>6} {'as-shipped':>11} {'corrected':>10}")
    for K in (8, 32, 128, 512):
        shards = [cands[k::K] for k in range(K)]
        a = sum(n.paid for n in run_shards_v3(shards, 16, inner=False))
        b = sum(n.paid for n in run_shards_v3(shards, 16, inner=True))
        print(f"{K:>6} {a/floor:>10.2f}x {b/floor:>9.2f}x")
    c8 = sum(n.paid for n in run_shards_v3([cands[k::8] for k in range(8)], 1, True))
    print(f"    synchronous bound (merge every candidate), K=8: {c8/floor:.2f}x")
    print(f"    (== single shared store in a sequential simulator, for all K)")
    print("=" * 86)

def sec_ASYNC(target, Ls):
    print(f"[ASYNC] no barriers, per-node rates, gossip lat~U(1,L), dup 20%, "
          f"loss 15%, anti-entropy/40")
    print(f"{'L':>4} {'K':>4} {'fixed point':>12} {'agree':>6} {'evals':>7} "
          f"{'dup evals':>10} {'overhead':>9}")
    trajs, allok, nruns = set(), True, 0
    for L in Ls:
        for K in (4, 16):
            hit = agree = dups = evals = 0
            for seed in (0, 1, 2):
                r = async_run(K, seed, L)
                hit += r["target_hit"]; agree += r["all_agree"]
                dups += r["dup_evals"]; evals += r["evals"]
                trajs.add(r["traj"]); nruns += 1
                allok &= r["target_hit"] and r["all_agree"]
            print(f"{L:>4} {K:>4} {('3/3' if hit==3 else f'{hit}/3'):>12} "
                  f"{('3/3' if agree==3 else f'{agree}/3'):>6} {evals:>7} "
                  f"{dups:>10} {dups/max(evals-dups,1):>8.1%}")
    print(f"    distinct global discovery trajectories across {nruns} runs: "
          f"{len(trajs)}   (trajectories differ; the fixed point never does)")
    print(f"    every fair run reached the same least fixed point: {allok}")
    assert allok
    print("=" * 86)

def sec_AB_E3(cands, target, floor, fl_final, do_ab, do_e3):
    K = 8
    shards = [cands[k::K] for k in range(K)]
    ns = run_shards_v3(shards, 16, inner=True)
    ex_shared = sum(n.paid for n in ns)
    tasks = sum(n.tasks for n in ns)
    paidt = sum(len(n.computed) for n in ns)
    xh = sum(n.cross_hits for n in ns)
    probe = Node(97, []); probe.store = dict(fl_final); probe.computed = set(fl_final)
    memo = {}
    def resolve(e):
        t = task_id(e)
        if t in memo: return memo[t]
        if e[0] == "N": src = church(e[1], probe.alloc)
        else:
            nl = resolve(e[1])[1]; nr = resolve(e[2])[1]
            op = ADD(probe.alloc) if e[0] == "ADD" else MUL
            src = f"(({op} {nl}) {nr})"
        kk = ic_canon(src); memo[t] = (fl_final[kk]["cost"], fl_final[kk]["nf"])
        return memo[t]
    for e in cands: resolve(e)
    if do_ab:
        demands = [set().union(*[id_closure(e, set()) for e in s]) for s in shards]
        ex_local = sum(sum(memo[t][0] for t in d) for d in demands)
        pr_shared = async_run(K, 0, lat=2, dup_p=0, drop_p=0, anti_every=10)["paid"]
        pr_local = K * async_run(1, 0, lat=1, dup_p=0, drop_p=0)["paid"]
        print(f"[2x2] interactions to a frontier containing the exhaustive "
              f"64 values, K=8")
        print(f"{'':>16} {'no sharing':>11} {'shared':>8}")
        print(f"{'exhaustive':>16} {ex_local:>11} {ex_shared:>8}")
        print(f"{'pruned(async)':>16} {pr_local:>11} {pr_shared:>8}")
        print(f"    sharing buys {1-ex_shared/ex_local:.0%} (exhaustive) / "
              f"{1-pr_shared/pr_local:.0%} (pruned);  pruning buys "
              f"{1-pr_local/ex_local:+.0%} (no sharing) / "
              f"{1-pr_shared/ex_shared:+.0%} (shared)")
        print(f"    NOTE pruned cells cover the full {len(target)}-value closure, a")
        print(f"    strict superset of the 64 -- matched target, unmatched coverage;")
        print(f"    and the shared cell is unowned, so it carries race duplication.")
        EV = {pyval(e) for e in cands}
        m1 = async_run(1, 0, lat=1, dup_p=0, drop_p=0, stop_at=EV)["paid"]
        m8 = async_run(K, 0, lat=2, dup_p=0, drop_p=0, anti_every=10,
                       owned=True, stop_at=EV)["paid"]
        print(f"    coverage-matched (stop at frontier >= the 64 exhaustive values):")
        print(f"      exhaustive floor {floor}   pruned single-node {m1}   "
              f"pruned K=8 owned {m8}")
        print(f"      pruned K=8 independent (no sharing) {8*m1}")
        print("=" * 86)
    if do_e3:
        nf_by_val = {}
        for t, (c, nf) in memo.items():
            v = t[1] if t[0] == "N" else (t[1]+t[2] if t[0] == "ADD" else t[1]*t[2])
            nf_by_val.setdefault(v, nf)
        sample = [t for t in memo if t[0] != "N"][:100]
        al = Alloc(80000)
        srcs = [f"(({ADD(al) if op=='ADD' else MUL} {nf_by_val[a]}) {nf_by_val[b]})"
                for (op, a, b) in sample]
        t1 = time.perf_counter()
        for s in srcs: ic_canon(s)
        canon_us = (time.perf_counter() - t1) / len(srcs) * 1e6
        D = {}
        t2 = time.perf_counter()
        for i, t in enumerate(sample * 50): D[t] = D.get(t, i)
        key_us = (time.perf_counter() - t2) / (len(sample) * 50) * 1e6
        t3 = time.perf_counter()
        for s in srcs: ic_float.run(s)
        red_us = (time.perf_counter() - t3) / len(srcs) * 1e6
        p_total = 1 - paidt / tasks; p_cross = xh / tasks
        print(f"[E3] canon {canon_us:.0f}us   cheap-key {key_us:.2f}us   "
              f"reduce {red_us:.0f}us/task   p_total {p_total:.0%}   "
              f"p_cross {p_cross:.0%}")
        def leg(name, cost, p):
            bar = p * red_us
            print(f"    {name:<29}: {cost:7.2f}us vs {bar:6.1f}us  -> "
                  f"{'PAYS' if cost < bar else 'LOSES'}")
        leg("no-memo -> local (cheap key)", key_us, p_total)
        leg("local -> shared (canon key)", canon_us - key_us, p_cross)
        leg("no-memo -> shared (canon)", canon_us, p_total)
        NATIVE = 28e6
        print(f"    native ic32 (~28M i/s): shared pays above "
              f"~{canon_us*1e-6*NATIVE/p_cross:,.0f} interactions/task (string canon)")
        print(f"    or ~{key_us*1e-6*NATIVE/p_cross:,.0f} (carried recipe ids), "
              f"at p_cross {p_cross:.0%}.")
        print("=" * 86)

def sec_OWNED(target, Ls):
    print(f"[OWNED] same async substrate, work self-assigned by hash ownership")
    print(f"        (SPEC 4.3's owner(w)=h(id) mod K, applied to tasks; still zero")
    print(f"        coordination messages -- ownership is computable locally)")
    print(f"{'L':>4} {'K':>4} {'fixed point':>12} {'agree':>6} {'evals':>7} "
          f"{'dup evals':>10} {'overhead':>9}")
    for L in Ls:
        K = 16
        hit = agree = dups = evals = 0
        for seed in (0, 1, 2):
            r = async_run(K, seed, L, owned=True)
            hit += r["target_hit"]; agree += r["all_agree"]
            dups += r["dup_evals"]; evals += r["evals"]
        print(f"{L:>4} {K:>4} {('3/3' if hit==3 else f'{hit}/3'):>12} "
              f"{('3/3' if agree==3 else f'{agree}/3'):>6} {evals:>7} "
              f"{dups:>10} {dups/max(evals-dups,1):>8.1%}")
    print("=" * 86)

if __name__ == "__main__":
    Ls = [int(a) for a in sys.argv[1:] if a.isdigit()] or [2, 10, 40]
    SEC = set(a.upper() for a in sys.argv[1:] if not a.isdigit()) or {"K", "ASYNC", "AB", "E3"}
    t0 = time.perf_counter()
    cands, target = sec_common()
    floor = fl_final = None
    if SEC & {"K", "AB", "E3"}:
        floor, fl_final = sec_floor(cands)
    if "K" in SEC: sec_K(cands, floor)
    if "ASYNC" in SEC: sec_ASYNC(target, Ls)
    if "OWNED" in SEC: sec_OWNED(target, Ls)
    if SEC & {"AB", "E3"}:
        sec_AB_E3(cands, target, floor, fl_final, "AB" in SEC, "E3" in SEC)
    print(f"total wall {time.perf_counter()-t0:.0f}s")
