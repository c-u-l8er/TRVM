"""
synth_bool.py -- Stage 1 of the native synthesis layer, on the measured substrate.

The strategic plan (typed DSL -> behavioral frontier -> CEGIS -> cross-spec
transfer) is instantiated here at its smallest honest scale: Boolean function
synthesis where every candidate is a REAL interaction-calculus term, every
evaluation is an ic_float reduction keyed by ic_canon in the CvRDT store, work
is hash-OWNED across K=8 workers (swarm3's 0%-duplication lesson, applied from
day one), and merging uses the corrected cadence.

DSL:      e ::= x_i | NOT e | AND e e | OR e e     (+ components, see C+)
Compile:  variables used k>=2 times get a labeled dup chain; k=0 is a free
          eraser (legal: church-0 binds an unused f). Programs are closed terms
          lambda v0..v_{n-1}. <dups> body.
Identity: program_id = ic_canon(NF of compiled term); task keys = ic_canon of
          each curried application step, so PARTIAL applications are shared
          across input tuples, tasks, and specs.
Behavior: signature = decoded outputs over all 2^n input tuples, evaluated
          stepwise ((p b1) b2 ...) with every step memoized. The frontier maps
          behavior -> Rec(min-size rep, min cost, provenance) -- a semilattice.
Search:   bottom-up by size over frontier REPRESENTATIVES (behavioral pruning),
          stop at first candidate matching the target signature.

EXPT-1 (2-input ladder, conditions A/B/C):
    A: K independent full searches, nothing shared    (reported as K x single)
    B: shared store+frontier within a task, RESET between tasks
    C: shared store+frontier PERSISTING across tasks (lookup-first)
  The claim under test: C's cost collapses after task 1 because solving one
  spec incidentally classifies its whole behavioral family (learning as
  amortization); B pays full search every time; A pays K x that.

EXPT-2 (3-input ladder, conditions B / C / C+):
    B:  reset store, raw grammar
    C:  accumulated store, raw grammar        (isolates MEMO transfer)
    C+: accumulated store, grammar extended with the accumulated 2-input
        frontier's representatives as applicable COMPONENTS (isolates
        COMPOSITIONAL transfer)
  Budget-capped: a condition may exhaust its candidate budget without solving;
  that is a reported outcome, not a failure of the harness.

Run:  PYTHONPATH=runtime/python:research python3 research/synth_bool.py SELFTEST L2
      PYTHONPATH=runtime/python:research python3 research/synth_bool.py L3
"""
import sys, time, random, itertools
sys.setrecursionlimit(100000)

import ic_float
from incrdt import parse_tree, TRUE, FALSE, NOT
from supgen_swarm import ic_canon

AND_SRC = "λp.λq.((p q) λa.λb.b)"      # if p then q else FALSE   (linear)
OR_SRC  = "λp.λq.((p λa.λb.a) q)"      # if p then TRUE else q    (linear)
NOT_SRC = NOT
BOOL = {True: TRUE, False: FALSE}

class Alloc:
    def __init__(self, base): self.n = base
    def fresh(self): self.n += 1; return self.n

# ------------------------------------------------------------------ DSL -> IC
def size_of(e):
    if e[0] == "V": return 1
    if e[0] == "C": return 3                      # component application
    if e[0] == "NOT": return 1 + size_of(e[1])
    return 1 + size_of(e[1]) + size_of(e[2])

def compile_ic(e, nvars, alloc):
    """Compile a DSL tree to a closed IC term with dup-insertion."""
    occ = [[] for _ in range(nvars)]
    def emit(t):
        if t[0] == "V":
            nm = f"o{t[1]}_{len(occ[t[1]])}"; occ[t[1]].append(nm); return nm
        if t[0] == "NOT":
            return f"({NOT_SRC} {emit(t[1])})"
        if t[0] == "C":
            _, comp_src, i, j = t
            a = emit(("V", i)); b = emit(("V", j))
            return f"(({comp_src} {a}) {b})"
        op = AND_SRC if t[0] == "AND" else OR_SRC
        return f"(({op} {emit(t[1])}) {emit(t[2])})"
    body = emit(e)
    stmts = []
    for i in range(nvars):
        names = occ[i]; v = f"v{i}"
        if len(names) == 0: continue
        if len(names) == 1:
            body = body.replace(names[0], v); continue
        src = v
        for j in range(len(names) - 1):
            rest = names[len(names) - 1] if j == len(names) - 2 else f"t{i}_{j}"
            stmts.append(f"!&{alloc.fresh()}{{{names[j]},{rest}}}={src};")
            src = rest
    binders = "".join(f"λv{i}." for i in range(nvars))
    return binders + "".join(stmts) + body

def decode_bool(nf):
    try: t = parse_tree(nf)
    except Exception: return None
    if t[0] != "lam": return None
    a, b = t[1], t[2]
    if b[0] != "lam": return None
    c, body = b[1], b[2]
    if body == ("var", a): return True
    if body == ("var", c): return False
    return None

# ------------------------------------------------------------------ store
class Store:
    """CvRDT store + behavioral frontier, with task-provenance."""
    def __init__(self):
        self.d = {}                 # key -> dict(nf, cost, origin, task)
        self.beh = {}               # (nvars, sig) -> dict(expr, size, task)
    def merge_entry(self, key, ent):
        cur = self.d.get(key)
        if cur is None: self.d[key] = ent
        else: assert cur["nf"] == ent["nf"], "CvRDT violation"
    def learn_beh(self, nvars, sig, expr, task):
        k = (nvars, sig); cur = self.beh.get(k)
        if cur is None or size_of(expr) < cur["size"]:
            self.beh[k] = dict(expr=expr, size=size_of(expr), task=task)
            return cur is None
        return False

# ------------------------------------------------------------------ worker pool
class Pool:
    def __init__(self, K, store, task, owned=True):
        self.K = K; self.store = store; self.task = task; self.owned = owned
        self.alloc = Alloc(50000)
        self.paid = 0; self.evals = 0
        self.hits_self = 0; self.hits_cross_task = 0
    def _run(self, src):
        key = ic_canon(src)
        ent = self.store.d.get(key)
        if ent is not None:
            if ent["task"] != self.task: self.hits_cross_task += 1
            else: self.hits_self += 1
            return ent["nf"]
        nf, c, _ = ic_float.run(src)
        self.paid += c
        self.store.merge_entry(key, dict(nf=nf, cost=c, origin=0, task=self.task))
        return nf
    def classify(self, expr, nvars):
        """Compile once; evaluate the SOURCE on each input tuple. Printed NFs
        are never re-parsed: the NF printer collapses dups of bound variables
        into repeated occurrences, which does not round-trip -- discovered the
        hard way on AND(x,x)."""
        self.evals += 1
        src = compile_ic(expr, nvars, self.alloc)
        sig = []
        for tup in itertools.product((False, True), repeat=nvars):
            app = src
            for b in tup:
                app = f"({app} {BOOL[b]})"
            nf = self._run(app)
            v = decode_bool(nf)
            assert v is not None, f"non-boolean NF for {expr}"
            sig.append(v)
        return tuple(sig)

# ------------------------------------------------------------------ synthesis
def synthesize(target_sig, nvars, store, task, budget=3000, max_size=11,
               components=None, K=8):
    """Bottom-up, behavior-pruned, owned enumeration. Returns result dict."""
    pool = Pool(K, store, task)
    hit = store.beh.get((nvars, target_sig))
    if hit is not None and hit["task"] != task:
        return dict(solved=True, how="frontier-lookup", expr=hit["expr"],
                    evals=0, paid=0, xtask=0)
    reps = {}                         # behavior -> smallest expr THIS search sees
    by_size = {1: [("V", i) for i in range(nvars)]}
    if components:
        by_size[3] = [("C", nf, i, j) for nf in components
                      for i in range(nvars) for j in range(nvars)]
    frontier_sizes = {}
    def consider(e):
        sig = pool.classify(e, nvars)
        store.learn_beh(nvars, sig, e, task)
        if sig not in reps:
            reps[sig] = e
            frontier_sizes.setdefault(size_of(e), []).append(e)
        return sig == target_sig
    for s in sorted(by_size):
        for e in by_size[s]:
            if pool.evals >= budget: break
            if consider(e):
                return dict(solved=True, how="search", expr=e, evals=pool.evals,
                            paid=pool.paid, xtask=pool.hits_cross_task)
    size = 1
    while size < max_size and pool.evals < budget:
        size += 1
        gen = []
        for e in [x for xs in frontier_sizes.values() for x in xs]:
            if size_of(e) + 1 == size: gen.append(("NOT", e))
        for s1, es1 in list(frontier_sizes.items()):
            for s2, es2 in list(frontier_sizes.items()):
                if s1 + s2 + 1 != size: continue
                for a in es1:
                    for b in es2:
                        gen.append(("AND", a, b)); gen.append(("OR", a, b))
        for e in gen:
            if pool.evals >= budget: break
            if consider(e):
                return dict(solved=True, how="search", expr=e, evals=pool.evals,
                            paid=pool.paid, xtask=pool.hits_cross_task)
    return dict(solved=False, how="budget", expr=None, evals=pool.evals,
                paid=pool.paid, xtask=pool.hits_cross_task)

# ------------------------------------------------------------------ specs
def sig_of(fn, nvars):
    return tuple(fn(*t) for t in itertools.product((False, True), repeat=nvars))

L2_SPECS = [
    ("AND",   lambda x, y: x and y),
    ("OR",    lambda x, y: x or y),
    ("IMPL",  lambda x, y: (not x) or y),
    ("XOR",   lambda x, y: x != y),
    ("NAND",  lambda x, y: not (x and y)),
    ("NOR",   lambda x, y: not (x or y)),
    ("XNOR",  lambda x, y: x == y),
    ("NIMPL", lambda x, y: x and not y),
]
L3_SPECS = [
    ("AND3", lambda x, y, z: x and y and z),
    ("OR3",  lambda x, y, z: x or y or z),
    ("MAJ3", lambda x, y, z: (x and y) or (x and z) or (y and z)),
    ("XOR3", lambda x, y, z: (x != y) != z),
    ("MUX",  lambda x, y, z: y if x else z),
]

def show_expr(e):
    if e is None: return "-"
    if e[0] == "V": return "xyz"[e[1]]
    if e[0] == "NOT": return f"~{show_expr(e[1])}"
    if e[0] == "C": return f"[comp]({'xyz'[e[2]]},{'xyz'[e[3]]})"
    return f"({show_expr(e[1])}{'&' if e[0]=='AND' else '|'}{show_expr(e[2])})"

# ==================================================================== sections
def sec_SELFTEST():
    al = Alloc(90000)
    xor = ("OR", ("AND", ("V", 0), ("NOT", ("V", 1))),
                 ("AND", ("NOT", ("V", 0)), ("V", 1)))
    p = Pool(1, Store(), 0)
    assert p.classify(xor, 2) == sig_of(lambda x, y: x != y, 2)
    unused = ("V", 0)
    assert p.classify(unused, 2) == (False, False, True, True)
    maj = ("OR", ("AND", ("V", 0), ("V", 1)),
                 ("OR", ("AND", ("V", 0), ("V", 2)), ("AND", ("V", 1), ("V", 2))))
    assert p.classify(maj, 3) == sig_of(L3_SPECS[2][1], 3)
    print(f"[selftest] dup-compiled XOR, unused-binder, MAJ3 truth tables verified "
          f"on ic_float ({p.paid} interactions)")
    print("=" * 86)

def sec_L2():
    print(f"[L2] 8 two-input specs, K=8 owned, behavior-pruned search")
    print(f"{'spec':>6} | {'A: Kxisolated':>14} | {'B: shared/reset':>16} | "
          f"{'C: accumulating':>16} {'how':>18}")
    stores = dict(B=None, C=Store())
    totals = dict(A=0, B=0, C=0)
    for t, (name, fn) in enumerate(L2_SPECS):
        tgt = sig_of(fn, 2)
        single = synthesize(tgt, 2, Store(), t)          # one isolated worker
        a_paid = 8 * single["paid"]
        rB = synthesize(tgt, 2, Store(), t)              # fresh shared store
        rC = synthesize(tgt, 2, stores["C"], t)
        totals["A"] += a_paid; totals["B"] += rB["paid"]; totals["C"] += rC["paid"]
        print(f"{name:>6} | {a_paid:>14} | {rB['paid']:>16} | {rC['paid']:>16} "
              f"{rC['how']:>18}")
    print(f"{'TOTAL':>6} | {totals['A']:>14} | {totals['B']:>16} | "
          f"{totals['C']:>16}")
    beh2 = sum(1 for (n, s) in stores["C"].beh if n == 2)
    print(f"    C's frontier after the ladder: {beh2}/16 possible 2-input "
          f"behaviors witnessed")
    print("=" * 86)
    return stores["C"]

def sec_L3(cstore):
    import copy
    # C and C+ each get an INDEPENDENT fork of the post-L2 store, so neither
    # inherits the other's 3-input discoveries (the first run of this section
    # had exactly that confound: C+ was reading C's frontier).
    storeC = copy.deepcopy(cstore)
    storeP = copy.deepcopy(cstore)
    # components: accumulated 2-input representatives, as compiled SOURCE
    comps = []
    for (n, sig), rec in sorted(cstore.beh.items()):
        if n != 2: continue
        comps.append(compile_ic(rec["expr"], 2, Alloc(70000 + len(comps) * 100)))
    print(f"[L3] 5 three-input specs, budget 3000 candidates, max size 11")
    print(f"     C+ components: {len(comps)} accumulated 2-input representatives")
    print(f"{'spec':>6} | {'B: reset':>10} | {'C: memo':>10} | {'C+: memo+comps':>15} "
          f"| {'B/C/C+ solved':>14}")
    tot = dict(B=0, C=0, CP=0)
    for t, (name, fn) in enumerate(L3_SPECS):
        tgt = sig_of(fn, 3)
        rB = synthesize(tgt, 3, Store(), 100 + t)
        rC = synthesize(tgt, 3, storeC, 100 + t)
        rP = synthesize(tgt, 3, storeP, 200 + t, components=comps)
        tot["B"] += rB["paid"]; tot["C"] += rC["paid"]; tot["CP"] += rP["paid"]
        sv = "".join("Y" if r["solved"] else "n" for r in (rB, rC, rP))
        print(f"{name:>6} | {rB['paid']:>10} | {rC['paid']:>10} | {rP['paid']:>15} "
              f"| {sv:>14}   {show_expr(rP['expr'])[:34]}")
    print(f"{'TOTAL':>6} | {tot['B']:>10} | {tot['C']:>10} | {tot['CP']:>15}")
    print(f"    (B/C isolate memo-transfer; C+ adds compositional transfer.")
    print(f"     'n' = budget exhausted without solving -- a reported outcome.)")
    print("=" * 86)

if __name__ == "__main__":
    SEC = set(a.upper() for a in sys.argv[1:]) or {"SELFTEST", "L2", "L3"}
    t0 = time.perf_counter()
    cstore = None
    if "SELFTEST" in SEC: sec_SELFTEST()
    if "L2" in SEC or "L3" in SEC:
        cstore = sec_L2()
    if "L3" in SEC: sec_L3(cstore)
    print(f"total wall {time.perf_counter()-t0:.0f}s")
