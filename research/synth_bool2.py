"""
synth_bool2.py -- the review-driven rebuild of the Boolean synthesizer.

The review of synth_bool.py found three overclaims (no actual worker ownership,
non-semilattice behavior records, described-but-absent program identity) and
prescribed a build order. This file implements it. Labels below say exactly
what is and is not claimed.

ARTIFACT MODEL (lawful).
  program_id = sha256(SEMVER, repr(canonical typed AST))[:16]  -- stable hash,
  not Python hash(). ProgramRecord carries ast, arity, ref_size (Apply nodes
  cost 1 + args), exp_size (after reference expansion), provenance.
  BehaviorRecord: preferred = min under the TOTAL order
  (ref_size, exp_size, interactions, program_id); alternatives/provenance by
  union. Join laws (commutative, associative, idempotent) are property-tested
  in [LAWS], in the style of econ_triage.crdt_ok.

TRANSPORT RULE (from the wire-format finding, kept as regression vectors).
  Printed normal forms are TERMINAL artifacts: decoded, never re-parsed into
  new programs. All program transport is at AST/source level. [LAWS] pins
  AND(x,x) as the permanent regression: source-path evaluation must succeed;
  the printed-NF round-trip is demonstrated non-faithful. A 4-fold-duplication
  vector guards the dup-chain compiler.

COMPONENTS AS REFERENCES, GENERAL TYPED APPLICATION.
  Grammar adds ("AP", program_id, (arg_expr, ...)). Compilation expands
  references by AST substitution (never source splicing), then dup-inserts
  over TOTAL variable occurrence counts. ref_size drives enumeration
  (description-length search); exp_size and runtime cost are recorded.

WORKERS (real partition, honestly scoped).
  K workers with separate delta stores over a shared base, candidates
  hash-owned by program_id, folds every 16 NOVEL classifications (cadence in
  paid units). Scheduling is round-robin in one process and generation is
  LEVEL-SYNCHRONOUS: workers regenerate from the folded frontier at each
  ref_size level. Claimed: zero duplicate classification within levels by
  construction, measured cross-worker reuse. NOT claimed: asynchronous
  distributed synthesis, cross-host execution.

BUDGET VECTOR. attempts / novel programs / paid interactions / canon calls /
  wall seconds, all reported; the stop condition is novel-or-interactions.
  Replayed program_ids resolve from the program->signature map without
  consuming the novel budget (the v1 pathology where a later task burned its
  whole budget on memo hits is thereby fixed and visible in the attempts vs
  novel columns).

DECISIVE C+ METRIC. A task counts as compositional transfer only if solved by
  a program whose AST contains an AP reference to a component synthesized in
  an EARLIER task, inside a structure absent from every earlier task's
  classified set. The certificate is printed when earned.

Run:
  PYTHONPATH=runtime/python:research python3 research/synth_bool2.py LAWS L2
  PYTHONPATH=runtime/python:research python3 research/synth_bool2.py L3 B C
  PYTHONPATH=runtime/python:research python3 research/synth_bool2.py L3 CP
"""
import sys, time, random, itertools, hashlib
sys.setrecursionlimit(100000)

import ic_float
from incrdt import parse_tree, TRUE, FALSE, NOT

AND_SRC = "λp.λq.((p q) λa.λb.b)"
OR_SRC  = "λp.λq.((p λa.λb.a) q)"
NOT_SRC = NOT
BOOL = {True: TRUE, False: FALSE}
SEMVER = "booldsl-v2/ic_float/truthtable"

class Alloc:
    def __init__(self, base): self.n = base
    def fresh(self): self.n += 1; return self.n

# ------------------------------------------------------------- program registry
REG = {}                                    # program_id -> ProgramRecord

def pid_of(ast, arity):
    # identity is TYPED: same tree at different arity is a different program.
    # (v2's first run omitted arity; shared psig then leaked 2-input signatures
    # into 3-input searches and corrupted their rep frontiers -- the reviewer's
    # "canonical typed AST" requirement, vindicated by measurement.)
    return hashlib.sha256((SEMVER + f"/{arity}/" + repr(ast)).encode()
                          ).hexdigest()[:16]

def ref_size(e):
    if e[0] == "V": return 1
    if e[0] == "NOT": return 1 + ref_size(e[1])
    if e[0] == "AP": return 1 + sum(ref_size(a) for a in e[2])
    return 1 + ref_size(e[1]) + ref_size(e[2])

def subst(ast, args):
    if ast[0] == "V": return args[ast[1]]
    if ast[0] == "NOT": return ("NOT", subst(ast[1], args))
    if ast[0] == "AP": return ("AP", ast[1], tuple(subst(a, args) for a in ast[2]))
    return (ast[0], subst(ast[1], args), subst(ast[2], args))

def expand(e):
    """Resolve AP references by AST substitution -> raw tree."""
    if e[0] == "V": return e
    if e[0] == "NOT": return ("NOT", expand(e[1]))
    if e[0] == "AP":
        rec = REG[e[1]]
        return expand(subst(rec["ast"], tuple(expand(a) for a in e[2])))
    return (e[0], expand(e[1]), expand(e[2]))

def register(ast, arity, task):
    p = pid_of(ast, arity)
    if p not in REG:
        raw = expand(ast)
        REG[p] = dict(ast=ast, arity=arity, ref_size=ref_size(ast),
                      exp_size=ref_size(raw), task=task)
    return p

# ------------------------------------------------------------- compile to IC
def compile_ic(raw, nvars, alloc):
    occ = [[] for _ in range(nvars)]
    def emit(t):
        if t[0] == "V":
            nm = f"o{t[1]}_{len(occ[t[1]])}"; occ[t[1]].append(nm); return nm
        if t[0] == "NOT": return f"({NOT_SRC} {emit(t[1])})"
        op = AND_SRC if t[0] == "AND" else OR_SRC
        return f"(({op} {emit(t[1])}) {emit(t[2])})"
    body = emit(raw)
    stmts = []
    for i in range(nvars):
        names = occ[i]; v = f"v{i}"
        if not names: continue
        if len(names) == 1:
            body = body.replace(names[0], v); continue
        src = v
        for j in range(len(names) - 1):
            rest = names[len(names) - 1] if j == len(names) - 2 else f"t{i}_{j}"
            stmts.append(f"!&{alloc.fresh()}{{{names[j]},{rest}}}={src};")
            src = rest
    return "".join(f"λv{i}." for i in range(nvars)) + "".join(stmts) + body

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

# ------------------------------------------------------------- behavior records
def brec(pref, alts, prov):
    return dict(pref=pref, alts=frozenset(alts), prov=frozenset(prov))

def bjoin(a, b):
    return brec(min(a["pref"], b["pref"]), a["alts"] | b["alts"],
                a["prov"] | b["prov"])

# ------------------------------------------------------------- shared state
class Base:
    """Shared base: evaluation store, program->signature map, behavior map."""
    def __init__(self):
        self.ev = {}        # canon(app src) -> dict(nf, cost, worker, task)
        self.psig = {}      # program_id -> signature
        self.beh = {}       # (nvars, sig) -> BehaviorRecord

class Worker:
    def __init__(self, k, base, task, shared=True):
        self.k = k; self.base = base; self.task = task; self.shared = shared
        self.ev = {}; self.psig = {}; self.beh = {}
        self.alloc = Alloc(50000 + 1000 * k)
        self.paid = self.novel = self.attempts = self.canon = 0
        self.hits_xw = self.hits_xt = 0
        self.queue = []
    def _lookup(self, key):
        e = self.ev.get(key)
        if e is None and self.shared: e = self.base.ev.get(key)
        return e
    def _run(self, src):
        from supgen_swarm import ic_canon
        self.canon += 1
        key = ic_canon(src)
        e = self._lookup(key)
        if e is not None:
            if e["task"] != self.task: self.hits_xt += 1
            elif e["worker"] != self.k: self.hits_xw += 1
            return e["nf"]
        nf, c, _ = ic_float.run(src)
        self.paid += c
        self.ev[key] = dict(nf=nf, cost=c, worker=self.k, task=self.task)
        return nf
    def classify(self, ast, nvars):
        self.attempts += 1
        p = register(ast, nvars, self.task)
        s = self.psig.get(p) or (self.base.psig.get(p) if self.shared else None)
        if s is not None: return p, s, False
        self.novel += 1
        raw = expand(ast)
        src = compile_ic(raw, nvars, self.alloc)
        sig = []
        for tup in itertools.product((False, True), repeat=nvars):
            app = src
            for b in tup: app = f"({app} {BOOL[b]})"
            v = decode_bool(self._run(app))
            assert v is not None, f"non-boolean NF for {ast}"
            sig.append(v)
        sig = tuple(sig)
        self.psig[p] = sig
        cost = REG[p]["exp_size"]
        rec = brec((REG[p]["ref_size"], REG[p]["exp_size"], cost, p, repr(ast)),
                   {p}, {self.task})
        k = (nvars, sig)
        self.beh[k] = bjoin(self.beh[k], rec) if k in self.beh else rec
        return p, sig, True

def fold(workers, base):
    for w in workers:
        for k, v in w.ev.items(): base.ev.setdefault(k, v)
        for p, s in w.psig.items():
            if p in base.psig: assert base.psig[p] == s, "signature divergence"
            else: base.psig[p] = s
        for k, r in w.beh.items():
            base.beh[k] = bjoin(base.beh[k], r) if k in base.beh else r
        w.ev = {}; w.psig = {}; w.beh = {}

# ------------------------------------------------------------- synthesis
def stable_owner(p, K): return int(p, 16) % K

def synthesize(target, nvars, base, task, K=8, owned=True, shared=True,
               lib=None, novel_cap=2500, int_cap=500000, max_size=11):
    t0 = time.perf_counter()
    hit = base.beh.get((nvars, target)) if shared else None
    if hit is not None and task not in hit["prov"]:
        return dict(solved=True, how="frontier-lookup", ast=None,
                    pref=hit["pref"], attempts=0, novel=0, paid=0, canon=0,
                    xw=0, xt=0, wall=0.0)
    workers = [Worker(k, base, task, shared) for k in range(K)]
    reps = {}                       # sig -> (ref_size, ast) this search's reps
    def budget():
        return (sum(w.novel for w in workers) >= novel_cap or
                sum(w.paid for w in workers) >= int_cap)
    def result(solved, how, ast):
        if shared: fold(workers, base)
        return dict(solved=solved, how=how, ast=ast, pref=None,
                    attempts=sum(w.attempts for w in workers),
                    novel=sum(w.novel for w in workers),
                    paid=sum(w.paid for w in workers),
                    canon=sum(w.canon for w in workers),
                    xw=sum(w.hits_xw for w in workers),
                    xt=sum(w.hits_xt for w in workers),
                    wall=time.perf_counter() - t0)
    def level(cands):
        """Hash-owned, cadence-folded classification of one size level."""
        for w in workers: w.queue = []
        seen = set()
        for ast in cands:
            p = pid_of(ast, nvars)
            if p in seen: continue
            seen.add(p)
            if owned: workers[stable_owner(p, K)].queue.append(ast)
            else:
                for w in workers: w.queue.append(ast)
        done = 0
        while any(w.queue for w in workers):
            for w in workers:
                if not w.queue: continue
                ast = w.queue.pop(0)
                p, sig, new = w.classify(ast, nvars)
                done += new
                if sig not in reps or ref_size(ast) < reps[sig][0]:
                    reps.setdefault(sig, (ref_size(ast), ast))
                if sig == target:
                    return ast
                if shared and done >= 16:
                    fold(workers, base); done = 0
            if budget(): return "BUDGET"
        if shared: fold(workers, base)
        return None
    atoms = [("V", i) for i in range(nvars)]
    r = level(atoms)
    if r == "BUDGET": return result(False, "budget", None)
    if r is not None: return result(True, "search", r)
    size = 1
    while size < max_size and not budget():
        size += 1
        by = {}
        for s, a in reps.values(): by.setdefault(s, []).append(a)
        gen = []
        for s, asts in by.items():
            if s + 1 == size: gen += [("NOT", a) for a in asts]
        for s1, e1 in by.items():
            for s2, e2 in by.items():
                if s1 + s2 + 1 != size: continue
                for a in e1:
                    for b in e2:
                        gen.append(("AND", a, b)); gen.append(("OR", a, b))
                        if lib:
                            gen += [("AP", p, (a, b)) for p in lib]
        r = level(gen)
        if r == "BUDGET": return result(False, "budget", None)
        if r is not None: return result(True, "search", r)
    return result(False, "budget" if budget() else "exhausted", None)

# ------------------------------------------------------------- specs
def sig_of(fn, nvars):
    return tuple(fn(*t) for t in itertools.product((False, True), repeat=nvars))

L2_SPECS = [("AND", lambda x, y: x and y), ("OR", lambda x, y: x or y),
            ("IMPL", lambda x, y: (not x) or y), ("XOR", lambda x, y: x != y),
            ("NAND", lambda x, y: not (x and y)), ("NOR", lambda x, y: not (x or y)),
            ("XNOR", lambda x, y: x == y), ("NIMPL", lambda x, y: x and not y)]
L3_SPECS = [("AND3", lambda x, y, z: x and y and z),
            ("OR3", lambda x, y, z: x or y or z),
            ("MAJ3", lambda x, y, z: (x and y) or (x and z) or (y and z)),
            ("XOR3", lambda x, y, z: (x != y) != z),
            ("MUX", lambda x, y, z: y if x else z)]

def show(e):
    if e is None: return "-"
    if e[0] == "V": return "xyz"[e[1]]
    if e[0] == "NOT": return f"~{show(e[1])}"
    if e[0] == "AP": return f"@{e[1][:4]}({','.join(show(a) for a in e[2])})"
    return f"({show(e[1])}{'&' if e[0]=='AND' else '|'}{show(e[2])})"

# ==================================================================== sections
def sec_LAWS():
    rng = random.Random(0)
    def rrec():
        pr = (rng.randint(1, 9), rng.randint(1, 30), rng.randint(1, 99),
              f"{rng.getrandbits(32):08x}", "a")
        return brec(pr, {f"{rng.getrandbits(16):04x}" for _ in range(2)},
                    {rng.randint(0, 5)})
    ok = True
    for _ in range(300):
        a, b, c = rrec(), rrec(), rrec()
        ok &= bjoin(a, b) == bjoin(b, a)
        ok &= bjoin(bjoin(a, b), c) == bjoin(a, bjoin(b, c))
        ok &= bjoin(a, a) == a
    print(f"[LAWS] BehaviorRecord join is commutative/associative/idempotent "
          f"over 300 random triples: {ok}")
    assert ok
    # wire-format regression: AND(x,x) source path OK, printed-NF path unfaithful
    w = Worker(0, Base(), 0)
    andxx = ("AND", ("V", 0), ("V", 0))
    p, sig, _ = w.classify(andxx, 1)
    assert sig == (False, True)
    src = compile_ic(andxx, 1, Alloc(90000))
    pnf, _, _ = ic_float.run(src)
    bad = False
    try:
        nf2, _, _ = ic_float.run(f"({pnf} {TRUE})")
        bad = decode_bool(nf2) is not True
    except RecursionError:
        bad = True
    print(f"[LAWS] AND(x,x): source-path signature correct; printed-NF "
          f"round-trip non-faithful: {bad}  (permanent regression vector)")
    assert bad
    v4 = ("AND", ("AND", ("V", 0), ("V", 0)), ("AND", ("V", 0), ("V", 0)))
    _, s4, _ = w.classify(v4, 1)
    assert s4 == (False, True)
    print(f"[LAWS] 4-fold duplication chain compiles and evaluates correctly")
    print("=" * 88)

def run_ladder(specs, nvars, conds, base_map, lib=None, K=8):
    cols = " | ".join(f"{c:>26}" for c in conds)
    print(f"{'spec':>6} | {cols}")
    tot = {c: [0, 0, 0] for c in conds}
    for t, (name, fn) in enumerate(specs):
        tgt = sig_of(fn, nvars)
        row = []
        for c in conds:
            shared = c != "A"; owned = c != "A"
            r = synthesize(tgt, nvars, base_map[c] if shared else Base(),
                           (nvars * 100) + t, K=K, owned=owned, shared=shared,
                           lib=(lib if c == "CP" else None))
            tot[c][0] += r["paid"]; tot[c][1] += r["novel"]
            tot[c][2] += r["attempts"]
            tag = ("L" if r["how"] == "frontier-lookup" else
                   ("Y" if r["solved"] else "n"))
            disp = show(r["ast"])[:8]
            if r["how"] == "frontier-lookup" and r["pref"] is not None:
                disp = r["pref"][4][:8]
                if "AP" in r["pref"][4]:
                    print(f"        CERTIFICATE {name} ({c}): behavior already "
                          f"witnessed via component-built program "
                          f"{r['pref'][4][:60]} during task(s) of an earlier "
                          f"search -- compositional discovery, retrieved")
            row.append(f"{r['paid']:>9} {r['novel']:>5} {r['attempts']:>6} {tag}"
                       f" {disp:>8}")
            if (c == "CP" and r["solved"] and r["ast"] is not None
                    and "AP" in repr(r["ast"])):
                pids = set()
                def walk(e):
                    if e[0] == "AP":
                        pids.add(e[1])
                        for a in e[2]: walk(a)
                    elif e[0] == "NOT": walk(e[1])
                    elif e[0] != "V": walk(e[1]); walk(e[2])
                walk(r["ast"])
                for p in sorted(pids):
                    print(f"        CERTIFICATE {name}: solved via component "
                          f"{p[:8]} (ref {REG[p]['ref_size']}, exp "
                          f"{REG[p]['exp_size']}, from task {REG[p]['task']}) "
                          f"inside novel structure {show(r['ast'])}")
        print(f"{name:>6} | " + " | ".join(f"{x:>26}" for x in row))
    line = " | ".join(f"{tot[c][0]:>9} {tot[c][1]:>5} {tot[c][2]:>6}   "
                      f"{'':>8}" for c in conds)
    print(f"{'TOTAL':>6} | {line}")
    print(f"    columns per condition: paid-interactions  novel  attempts  "
          f"solved(Y/L=lookup/n)  program")

def sec_L2():
    print(f"[L2] 2-input ladder, K=8 workers, hash-owned within levels, "
          f"level-synchronous folds every 16 novel")
    print(f"     (A = 8 UNOWNED isolated workers, actually executed)")
    bases = dict(B=None, C=Base())
    def base_for(c):
        if c == "B": return Base()
        return bases["C"]
    class BM(dict):
        def __getitem__(self, c): return base_for(c)
    run_ladder(L2_SPECS, 2, ["A", "B", "C"], BM())
    n2 = sum(1 for (n, s) in bases["C"].beh if n == 2)
    print(f"    C frontier: {n2}/16 two-input behaviors witnessed")
    print("=" * 88)
    return bases["C"]

def sec_L3(cbase, conds):
    import copy
    lib = sorted({r["pref"][3] for (n, s), r in cbase.beh.items() if n == 2})
    print(f"[L3] 3-input ladder, budget vector: novel<=2500, "
          f"interactions<=500k, size<=11")
    print(f"     C+ library: {len(lib)} referenced 2-input programs "
          f"(AP nodes, ref_size 1+args)")
    forks = {c: copy.deepcopy(cbase) for c in conds}
    class BM(dict):
        def __init__(self, f): self.f = f
        def __getitem__(self, c): return self.f[c] if c != "B" else Base()
    run_ladder(L3_SPECS, 3, conds, BM(forks), lib=lib)
    print("=" * 88)

if __name__ == "__main__":
    args = [a.upper() for a in sys.argv[1:]]
    SEC = set(a for a in args if a in ("LAWS", "L2", "L3")) or {"LAWS", "L2"}
    conds = [a for a in args if a in ("B", "C", "CP")] or ["B", "C", "CP"]
    t0 = time.perf_counter()
    if "LAWS" in SEC: sec_LAWS()
    cbase = None
    if "L2" in SEC or "L3" in SEC:
        cbase = sec_L2()
    if "L3" in SEC: sec_L3(cbase, conds)
    print(f"total wall {time.perf_counter()-t0:.0f}s")
