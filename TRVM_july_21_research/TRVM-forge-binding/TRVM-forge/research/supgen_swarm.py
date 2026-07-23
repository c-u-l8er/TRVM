"""
supgen_swarm.py -- does the computational memory pay for itself on a SEARCH workload?

FINDINGS.md reports the deflating generic numbers honestly: ~18% memoization across a
mixed corpus, ~6% early convergence (World 1). This experiment asks the question those
numbers leave open: on an ENUMERATION workload -- the SupGen / bottom-up-synthesis shape,
where candidates share sub-derivations BY CONSTRUCTION -- what does a coordination-free
content-addressed memory buy ACROSS NODES?

The workload (deliberately the classic bottom-up synthesis loop):
  synthesize arithmetic expressions over atoms {1,2,3} and ops {ADD, MUL}, up to
  MAX_LEAVES leaves; spec = "reaches target value T" (T in {12, 36}). Every candidate is
  evaluated ON THE REAL RUNTIME (ic_float) as an interaction-calculus term; every
  (sub)evaluation is content-addressed by ic_canon (the incrdt4 key: de Bruijn over lambda
  AND dup binders, alpha over dup labels) into the compmem-style store; the store is the
  CvRDT: merge = union, conflicts impossible by confluence (asserted on every merge).

Deliberate design choices (the honesty constraints):
  * NO superpositions. Sup-sharing is intra-net (SupGen's own trick); sharding candidates
    across nodes WITHOUT sups isolates exactly the CROSS-node contribution of the memory.
  * Each node constructs terms in its OWN label namespace (base 10000*(k+1)), so a
    cross-node hit is only possible THROUGH the canonical-identity layer -- string
    equality would miss it. The identity layer is load-bearing, in anger.
  * Compound tasks are keyed by the COMPACT recipe ((OP nf_l) nf_r) over already-canonical
    operand normal forms -- content-addressing computations by (op, address(inputs)),
    i.e. distributed hash-consing where the hash-cons table is a CRDT.
  * Self-hits (a node reusing its own work) are just local hash-consing and are NOT the
    claim. The claim lives in: cross-node hits, interactions saved vs solo, and
    merge-order invariance. All three are measured separately.

What is measured:
  (1) ORACLE agreement: every distinct task's runtime NF equals church(python-arithmetic
      value) up to ic_canon. (Runtime correctness across the whole task space.)
  (2) IDENTITY across namespaces: identical expressions built on different nodes collapse
      to the same key.
  (3) The sweep: K nodes x {solo (never merge), shared (merge every M candidates)}:
      interactions paid, self/cross hit counts, savings vs solo, distance to the
      single-evaluation floor.
  (4) CvRDT sanity under the workload: 3 randomized merge orders -> byte-identical final
      store and identical solution sets (monotone => coordination-free, CALM).
  (5) The semantic layer: distinct structural keys vs distinct normal forms among all
      evaluated tasks = the observational-equivalence headroom a pruning search would
      additionally harvest (measured as headroom, not implemented as pruning).

Run:  PYTHONPATH=runtime/python:research python3 research/supgen_swarm.py
"""
import sys, random
from collections import deque

sys.setrecursionlimit(100000)
import ic_float
from incrdt import parse_tree, canon

# ------------------------------------------------------------------ identity layer
# (inlined from compmem_ic.py, which runs a demo at import time)
def label_renumber(t, m=None, nxt=None):
    if m is None: m = {}; nxt = [0]
    g = t[0]
    if g in ("var", "era"): return t
    if g == "lam": return ("lam", t[1], label_renumber(t[2], m, nxt))
    if g == "app": return ("app", label_renumber(t[1], m, nxt), label_renumber(t[2], m, nxt))
    if g == "sup":
        if t[1] not in m: m[t[1]] = nxt[0]; nxt[0] += 1
        return ("sup", m[t[1]], label_renumber(t[2], m, nxt), label_renumber(t[3], m, nxt))
    if g == "dup":
        if t[1] not in m: m[t[1]] = nxt[0]; nxt[0] += 1
        return ("dup", m[t[1]], t[2], t[3], label_renumber(t[4], m, nxt),
                label_renumber(t[5], m, nxt))

def ic_canon(src):
    return canon(label_renumber(parse_tree(src)))

# ------------------------------------------------------------------ term builders
class Alloc:
    """Per-node duplication-label namespace: the 'independent machine' condition."""
    def __init__(self, base): self.base = base; self.n = 0
    def fresh(self): self.n += 1; return self.base + self.n

def church(n, alloc):
    if n == 0: return "λf.λx.x"
    if n == 1: return "λf.λx.(f x)"
    cs = [f"c{i}" for i in range(n)]; src = []; cur = "f"
    for i in range(n - 1):
        L = alloc.fresh(); nxt = f"t{i}" if i < n - 2 else cs[-1]
        src.append(f"!&{L}{{{cs[i]},{nxt}}}={cur};"); cur = nxt
    body = "x"
    for c in reversed(cs): body = f"({c} {body})"
    return "λf.λx." + "".join(src) + body

MUL = "λm.λn.λf.(m (n f))"                       # dup-free
def ADD(alloc):                                   # one labeled dup on f
    L = alloc.fresh()
    return f"λm.λn.λf.!&{L}{{f0,f1}}=f;λx.((m f0) ((n f1) x))"

# ------------------------------------------------------------------ expression space
ATOMS = (1, 2, 3)
OPS = ("ADD", "MUL")
MAX_LEAVES = 4
TARGETS = (12, 36)

def enumerate_exprs(max_leaves):
    by = {1: [("N", a) for a in ATOMS]}
    for k in range(2, max_leaves + 1):
        acc = []
        for i in range(1, k):
            for l in by[i]:
                for r in by[k - i]:
                    for op in OPS:
                        acc.append((op, l, r))
        by[k] = acc
    out = []
    for k in range(1, max_leaves + 1): out += by[k]
    return out

def pyval(e):
    if e[0] == "N": return e[1]
    v = pyval(e[1]), pyval(e[2])
    return v[0] + v[1] if e[0] == "ADD" else v[0] * v[1]

# ------------------------------------------------------------------ node + store
class Node:
    def __init__(self, k, shard):
        self.k = k
        self.alloc = Alloc(10000 * (k + 1))
        self.store = {}                # key -> {nf, cost, origin}
        self.computed = set()          # keys this node paid for itself
        self.queue = deque(shard)
        self.paid = 0                  # interactions actually spent
        self.tasks = 0                 # task attempts (atoms + compounds)
        self.self_hits = 0
        self.cross_hits = 0

    def eval_expr(self, e):
        """Bottom-up evaluation against the (possibly merged) store. Returns (key, nf)."""
        if e[0] == "N":
            src = church(e[1], self.alloc)
            return self._task(src, atom=True)
        _, kl_nf = self.eval_expr(e[1])
        _, kr_nf = self.eval_expr(e[2])
        op_src = ADD(self.alloc) if e[0] == "ADD" else MUL
        src = f"(({op_src} {kl_nf}) {kr_nf})"
        return self._task(src, atom=False)

    def _task(self, src, atom):
        self.tasks += 1
        key = ic_canon(src)
        hit = self.store.get(key)
        if hit is not None:
            if key in self.computed: self.self_hits += 1
            else: self.cross_hits += 1
            return key, hit["nf"]
        nf, cost, _ = ic_float.run(src)
        self.paid += cost
        self.store[key] = {"nf": nf, "cost": cost, "origin": self.k}
        self.computed.add(key)
        return key, nf

def merge_all(nodes, rng):
    """All-to-all union in a randomized order; assert confluence on every collision."""
    order = list(range(len(nodes))); rng.shuffle(order)
    U = {}
    for i in order:
        for key, v in nodes[i].store.items():
            w = U.get(key)
            if w is None: U[key] = v
            else: assert w["nf"] == v["nf"], "CvRDT violation: same key, different NF"
    for n in nodes: n.store = dict(U)

# ------------------------------------------------------------------ the swarm run
def run_swarm(K, candidates, merge_every=None, seed=0):
    """merge_every=None -> solo (never merge during work). Returns nodes + final union."""
    rng = random.Random(seed)
    nodes = [Node(k, candidates[k::K]) for k in range(K)]
    done = 0
    while any(n.queue for n in nodes):
        for n in nodes:
            if n.queue:
                n.eval_expr(n.queue.popleft()); done += 1
        if merge_every and done >= merge_every:
            merge_all(nodes, rng); done = 0
    final = {}
    for n in nodes:
        for key, v in n.store.items():
            w = final.get(key)
            if w is None: final[key] = v
            else: assert w["nf"] == v["nf"]
    return nodes, final

def solutions(final, church_nf_canon):
    sols = {t: 0 for t in TARGETS}
    for v in final.values():
        c = ic_canon(v["nf"])
        for t in TARGETS:
            if c == church_nf_canon[t]: sols[t] += 1
    return sols

# ==================================================================== run
if __name__ == "__main__":
    cands = enumerate_exprs(MAX_LEAVES)
    print(f"supgen_swarm: {len(cands)} candidates  (atoms {ATOMS}, ops {OPS}, "
          f"<= {MAX_LEAVES} leaves)  spec targets {TARGETS}")
    print("=" * 78)

    # ---- [2] identity across independent label namespaces (load-bearing check) ----
    a, b = Alloc(10000), Alloc(70000)
    same = ic_canon(church(6, a)) == ic_canon(church(6, b))
    add_a = f"(({ADD(a)} λf.λx.(f x)) λf.λx.(f x))"
    add_b = f"(({ADD(b)} λf.λx.(f x)) λf.λx.(f x))"
    same_add = ic_canon(add_a) == ic_canon(add_b)
    print(f"[identity] church(6) across namespaces collapses : {same}")
    print(f"[identity] (ADD 1 1) across namespaces collapses : {same_add}")
    assert same and same_add

    # ---- [floor + oracle 1] single node evaluates every distinct task once --------
    floor_nodes, floor_final = run_swarm(1, cands)
    floor_paid = floor_nodes[0].paid
    oracle_alloc = Alloc(90000)
    church_nf = {}
    for key, v in floor_final.items():
        pass
    # oracle: every candidate's runtime value == python arithmetic, via ic_canon(NF)
    val_canon = {}
    def church_canon(v):
        if v not in val_canon:
            nf, _, _ = ic_float.run(church(v, oracle_alloc))
            val_canon[v] = ic_canon(nf)
        return val_canon[v]
    probe = Node(99, [])
    ok = 0
    for e in cands:
        _, nf = probe.eval_expr(e)          # hits the probe's own store; cheap
        assert ic_canon(nf) == church_canon(pyval(e)), f"oracle mismatch on {e}"
        ok += 1
    print(f"[oracle]   runtime NF == church(python value) for all {ok} candidates")
    church_nf_canon = {t: church_canon(t) for t in TARGETS}
    distinct_tasks = len(floor_final)
    print(f"[floor]    distinct tasks {distinct_tasks}   single-evaluation cost "
          f"{floor_paid} interactions")
    print("=" * 78)

    # ---- [3] the sweep -------------------------------------------------------------
    print(f"{'K':>3} {'mode':>7} {'paid':>9} {'vs solo':>8} {'vs floor':>9} "
          f"{'self-hit':>9} {'cross-hit':>10} {'x-hit rate':>11}")
    summary = {}
    for K in (2, 4, 8):
        solo_nodes, _ = run_swarm(K, cands, merge_every=None)
        solo = sum(n.paid for n in solo_nodes)
        for label, me in (("solo", None), ("shared", 2 * K)):
            nodes, final = run_swarm(K, cands, merge_every=me)
            paid = sum(n.paid for n in nodes)
            tasks = sum(n.tasks for n in nodes)
            sh = sum(n.self_hits for n in nodes)
            xh = sum(n.cross_hits for n in nodes)
            sav = 1 - paid / solo
            summary[(K, label)] = (paid, xh, tasks)
            print(f"{K:>3} {label:>7} {paid:>9} {sav:>7.0%} {paid/floor_paid:>8.2f}x "
                  f"{sh:>9} {xh:>10} {xh/tasks:>10.1%}")
    print(f"    (floor = every distinct task evaluated exactly once, anywhere = "
          f"{floor_paid} interactions)")
    print("=" * 78)

    # ---- [4] CvRDT sanity under the workload: merge order cannot matter ------------
    finals, sols = [], []
    for seed in (0, 1, 2):
        nodes, final = run_swarm(4, cands, merge_every=8, seed=seed)
        finals.append({k: v["nf"] for k, v in final.items()})
        sols.append(solutions(final, church_nf_canon))
    same_store = finals[0] == finals[1] == finals[2]
    same_sols = sols[0] == sols[1] == sols[2]
    print(f"[CvRDT]    3 randomized merge orders -> identical final store : {same_store}")
    print(f"[CALM]     identical solution sets                            : {same_sols}")
    print(f"[spec]     programs reaching each target: " +
          ", ".join(f"{t}: {sols[0][t]}" for t in TARGETS))
    assert same_store and same_sols

    # ---- [5] the semantic layer: equivalence-pruning headroom ----------------------
    nfs = {}
    for key, v in floor_final.items():
        nfs.setdefault(ic_canon(v["nf"]), []).append(key)
    classes = len(nfs)
    top = sorted(nfs.values(), key=len, reverse=True)[:3]
    print("=" * 78)
    print(f"[semantic] {distinct_tasks} structural tasks -> {classes} semantic classes "
          f"(headroom for equivalence pruning: {1 - classes/distinct_tasks:.0%})")
    print(f"[semantic] largest classes have {[len(t) for t in top]} distinct derivations "
          f"collapsing to one value each")
    print("=" * 78)
    print("VERDICT: read the cross-hit column. Solo = the memory off; shared = the memory")
    print("as a CvRDT merged mid-search. Savings are interactions not re-paid across")
    print("nodes; the merge-order check ties the result to the semilattice claim.")
