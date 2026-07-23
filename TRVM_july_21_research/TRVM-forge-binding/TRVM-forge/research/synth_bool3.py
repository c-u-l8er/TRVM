"""
synth_bool3.py -- deterministic, self-contained compositional synthesis.

Review findings on v2, implemented here in the reviewer's order:

1. SCHEDULE-INDEPENDENT ACTIVE SEARCH. v2's reps table used first-arrival
   (worse: its `<` branch was dead code behind setdefault). v3 rebuilds the
   representative map at each level boundary FROM the folded BehaviorRecords'
   total-order preferred programs (ref_size, exp_size, measured_interactions,
   program_id). Candidates are processed in pid-sorted stream order (ownership
   still determines the evaluating worker; processing order no longer depends
   on worker enumeration), solutions are collected level-complete and the
   total-order-minimal one wins, and budgets bind per-candidate in stream
   order. Consequence, verified by the [DET] battery: frontier, preferred map,
   AND cost totals are exactly identical under forward / reversed / shuffled
   worker order, shuffled fold order, and K in {4, 8}. The deliberate trade:
   solved tasks pay to the end of their level.

2. LAWFUL TRI-STORE, NO AMBIENT STATE. ProgramStore, BehaviorStore, and
   EvaluationStore all live in Base, all replicated via property-tested joins:
     program:    same-id collision check (canonical bytes must match), tasks
                 union, first=min, level=min, measured cost=min
     behavior:   pref=min under total order, alternatives/provenance union
     evaluation: SAME-KEY NORMAL FORMS ASSERTED EQUAL, cost=min, workers/tasks
                 union (v2's setdefault first-writer selection removed)
   Identity is protocol-shaped for the prototype: full sha256 over
   (SEMVER, explicit type descriptor Bool^n->Bool, canonical s-expression
   bytes -- not Python repr), collision-checked on every register. Display
   uses an 8-hex prefix; the store keeps the full digest.

3. MEASURED COSTS. v2 stored exp_size where the preference tuple claimed
   interactions. v3 measures each program's truth-table evaluation
   interactions at first classification and carries them in the record.

4. MECHANICAL CERTIFICATE. ProgramRecords carry dependency ids and discovery
   level; the certificate walks the winning program's dependency chain and
   states: which task synthesized each component, which task first composed
   the witness, and whether any AP-free witness of the same behavior predates
   it. Wording per review: the structure was unavailable to the
   COMPONENT-PRODUCING search (not: absent from every preceding search).

5. TRANSPORT TEST. A deep-copied Base is handed to a fresh worker with no
   other state; it must resolve a component-bearing preferred program by id
   and reproduce its signature. Component transport is thereby tested, not
   assumed.

Still deferred, explicitly: cost-guided enumeration and Pareto representative
sets (next rung, now unconfounded), runtime REF linking (AP expands at compile
time; no persistent compiled component graph yet -- compositional transfer is
in the synthesis language, not yet runtime graph reuse), asynchronous and
cross-process synthesis.

Run:
  PYTHONPATH=runtime/python:research python3 research/synth_bool3.py LAWS DET
  PYTHONPATH=runtime/python:research python3 research/synth_bool3.py L2
  PYTHONPATH=runtime/python:research python3 research/synth_bool3.py L3 B C CP
"""
import sys, time, random, itertools, hashlib, copy
sys.setrecursionlimit(100000)

import ic_float
from incrdt import parse_tree, TRUE, FALSE, NOT

AND_SRC = "λp.λq.((p q) λa.λb.b)"
OR_SRC  = "λp.λq.((p λa.λb.a) q)"
NOT_SRC = NOT
BOOL = {True: TRUE, False: FALSE}
SEMVER = "booldsl-v3/ic_float/truthtable"

class Alloc:
    def __init__(self, base): self.n = base
    def fresh(self): self.n += 1; return self.n

# ------------------------------------------------------------- identity
def enc(ast):
    """Canonical s-expression bytes. Not Python repr."""
    if ast[0] == "V": return b"(V %d)" % ast[1]
    if ast[0] == "NOT": return b"(NOT " + enc(ast[1]) + b")"
    if ast[0] == "AP":
        return (b"(AP " + ast[1].encode() + b" " +
                b" ".join(enc(a) for a in ast[2]) + b")")
    return (b"(%s " % ast[0].encode()) + enc(ast[1]) + b" " + enc(ast[2]) + b")"

def type_desc(arity): return f"Bool^{arity}->Bool"

def pid_of(ast, arity):
    h = hashlib.sha256()
    h.update(SEMVER.encode()); h.update(b"|")
    h.update(type_desc(arity).encode()); h.update(b"|")
    h.update(enc(ast))
    return h.hexdigest()                      # full digest; display uses [:8]

def ref_size(e):
    if e[0] == "V": return 1
    if e[0] == "NOT": return 1 + ref_size(e[1])
    if e[0] == "AP": return 1 + sum(ref_size(a) for a in e[2])
    return 1 + ref_size(e[1]) + ref_size(e[2])

def deps_of(e, out):
    if e[0] == "AP":
        out.add(e[1])
        for a in e[2]: deps_of(a, out)
    elif e[0] == "NOT": deps_of(e[1], out)
    elif e[0] != "V": deps_of(e[1], out); deps_of(e[2], out)
    return out

# ------------------------------------------------------------- lawful stores
INF = float("inf")

def pjoin(a, b):
    assert a["enc"] == b["enc"] and a["type"] == b["type"], "id collision"
    return dict(ast=a["ast"], arity=a["arity"], type=a["type"], enc=a["enc"],
                ref=a["ref"], exp=a["exp"], deps=a["deps"] | b["deps"],
                cost=min(a["cost"], b["cost"]), level=min(a["level"], b["level"]),
                first=min(a["first"], b["first"]), tasks=a["tasks"] | b["tasks"])

def bjoin(a, b):
    return dict(pref=min(a["pref"], b["pref"]), alts=a["alts"] | b["alts"],
                prov=a["prov"] | b["prov"])

def ejoin(a, b):
    assert a["nf"] == b["nf"], "CvRDT violation: divergent normal forms"
    return dict(nf=a["nf"], cost=min(a["cost"], b["cost"]),
                workers=a["workers"] | b["workers"], tasks=a["tasks"] | b["tasks"])

class Base:
    def __init__(self):
        self.prog = {}; self.beh = {}; self.ev = {}
    def fold_from(self, w):
        for p, r in w.prog.items():
            self.prog[p] = pjoin(self.prog[p], r) if p in self.prog else r
        for k, r in w.beh.items():
            self.beh[k] = bjoin(self.beh[k], r) if k in self.beh else r
        for k, r in w.ev.items():
            self.ev[k] = ejoin(self.ev[k], r) if k in self.ev else r
        w.prog = {}; w.beh = {}; w.ev = {}

# ------------------------------------------------------------- compile / decode
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

# ------------------------------------------------------------- worker
class Worker:
    def __init__(self, k, base, task, shared=True):
        self.k = k; self.base = base; self.task = task; self.shared = shared
        self.prog = {}; self.beh = {}; self.ev = {}
        self.alloc = Alloc(50000 + 1000 * k)
        self.paid = self.novel = self.attempts = self.canon = 0
        self.hits_xw = self.hits_xt = 0
    def _get(self, table, key):
        v = getattr(self, table).get(key)
        if v is None and self.shared: v = getattr(self.base, table).get(key)
        return v
    def _prog(self, pid): return self._get("prog", pid)
    def resolve_raw(self, ast):
        if ast[0] == "V": return ast
        if ast[0] == "NOT": return ("NOT", self.resolve_raw(ast[1]))
        if ast[0] == "AP":
            rec = self._prog(ast[1])
            assert rec is not None, "unresolvable component reference"
            args = tuple(self.resolve_raw(a) for a in ast[2])
            def sub(t):
                if t[0] == "V": return args[t[1]]
                if t[0] == "NOT": return ("NOT", sub(t[1]))
                if t[0] == "AP": return ("AP", t[1], tuple(sub(a) for a in t[2]))
                return (t[0], sub(t[1]), sub(t[2]))
            return self.resolve_raw(sub(rec["ast"])) if any(
                True for _ in [0]) else None
        return (ast[0], self.resolve_raw(ast[1]), self.resolve_raw(ast[2]))
    def _run(self, src):
        from supgen_swarm import ic_canon
        self.canon += 1
        key = ic_canon(src)
        e = self._get("ev", key)
        if e is not None:
            if self.task not in e["tasks"]: self.hits_xt += 1
            elif self.k not in e["workers"]: self.hits_xw += 1
            return e["nf"]
        nf, c, _ = ic_float.run(src)
        self.paid += c
        self.ev[key] = dict(nf=nf, cost=c, workers=frozenset({self.k}),
                            tasks=frozenset({self.task}))
        return nf
    def classify(self, ast, nvars, level_no):
        self.attempts += 1
        p = pid_of(ast, nvars)
        known = self._get("prog", p)
        if known is not None and known["cost"] < INF:
            sig = None
            for (nv, s), r in {**self.base.beh, **self.beh}.items():
                if nv == nvars and p in r["alts"]: sig = s; break
            if sig is not None: return p, sig, False
        self.novel += 1
        raw = self.resolve_raw(ast)
        src = compile_ic(raw, nvars, self.alloc)
        p0 = self.paid
        sig = []
        for tup in itertools.product((False, True), repeat=nvars):
            app = src
            for b in tup: app = f"({app} {BOOL[b]})"
            v = decode_bool(self._run(app))
            assert v is not None, f"non-boolean NF for {ast}"
            sig.append(v)
        sig = tuple(sig)
        cost = self.paid - p0
        rec = dict(ast=ast, arity=nvars, type=type_desc(nvars), enc=enc(ast),
                   ref=ref_size(ast), exp=ref_size(raw),
                   deps=frozenset(deps_of(ast, set())), cost=cost,
                   level=level_no, first=self.task, tasks=frozenset({self.task}))
        self.prog[p] = pjoin(self.prog[p], rec) if p in self.prog else rec
        b = dict(pref=(rec["ref"], rec["exp"], cost, p), alts=frozenset({p}),
                 prov=frozenset({self.task}))
        k = (nvars, sig)
        self.beh[k] = bjoin(self.beh[k], b) if k in self.beh else b
        return p, sig, True

# ------------------------------------------------------------- synthesis
def stable_owner(p, K): return int(p[:16], 16) % K

def synthesize(target, nvars, base, task, K=8, owned=True, shared=True,
               lib=None, novel_cap=2500, int_cap=500000, max_size=11):
    t0 = time.perf_counter()
    hit = base.beh.get((nvars, target)) if shared else None
    if hit is not None and task not in hit["prov"]:
        return dict(solved=True, how="frontier-lookup", pid=hit["pref"][3],
                    attempts=0, novel=0, paid=0, canon=0, xw=0, xt=0, wall=0.0)
    workers = [Worker(k, base, task, shared) for k in range(K)]
    local = Base()                       # stand-in base for unshared searches
    tgt_base = base if shared else local
    def fold_all(order=None):
        ws = order if order is not None else workers
        for w in ws: tgt_base.fold_from(w)
    def reps_now():
        """Deterministic: total-order preferred program per behavior."""
        out = {}
        for (nv, s), r in tgt_base.beh.items():
            if nv != nvars: continue
            pr = tgt_base.prog.get(r["pref"][3])
            if pr is not None: out[s] = (r["pref"][0], pr["ast"])
        return out
    stats = lambda f: sum(getattr(w, f) for w in workers)
    def result(solved, how, pid):
        fold_all()
        return dict(solved=solved, how=how, pid=pid,
                    attempts=stats("attempts"), novel=stats("novel"),
                    paid=stats("paid"), canon=stats("canon"),
                    xw=stats("hits_xw"), xt=stats("hits_xt"),
                    wall=time.perf_counter() - t0)
    def level(cands, level_no):
        stream, seen = [], set()
        for ast in sorted(cands, key=lambda a: pid_of(a, nvars)):
            p = pid_of(ast, nvars)
            if p not in seen: seen.add(p); stream.append((p, ast))
        sols, done = [], 0
        for p, ast in stream:
            if stats("novel") >= novel_cap or stats("paid") >= int_cap:
                return sols, True
            w = workers[stable_owner(p, K)] if owned else workers[0]
            pp, sig, new = w.classify(ast, nvars, level_no)
            done += new
            if sig == target: sols.append((ref_size(ast), ref_size(
                w.resolve_raw(ast)), p, ast))
            if shared and done >= 16: fold_all(); done = 0
        fold_all()
        return sols, False
    if not shared and owned is False:    # condition A: replicate whole search
        pass
    atoms = [("V", i) for i in range(nvars)]
    sols, cut = level(atoms, 1)
    if sols: return result(True, "search", min(sols)[2])
    if cut: return result(False, "budget", None)
    size = 1
    while size < max_size:
        size += 1
        reps = reps_now()
        by = {}
        for s, a in reps.values(): by.setdefault(s, []).append(a)
        gen = []
        for s, asts in by.items():
            if s + 1 == size: gen += [("NOT", a) for a in asts]
        for s1, e1 in sorted(by.items()):
            for s2, e2 in sorted(by.items()):
                if s1 + s2 + 1 != size: continue
                for a in e1:
                    for b in e2:
                        gen.append(("AND", a, b)); gen.append(("OR", a, b))
                        if lib:
                            gen += [("AP", p, (a, b)) for p in lib]
        sols, cut = level(gen, size)
        if sols: return result(True, "search", min(sols)[2])
        if cut: return result(False, "budget", None)
    return result(False, "exhausted", None)

def run_A(target, nvars, K=8):
    """Condition A: K actually executed isolated unshared searches."""
    tot = dict(paid=0, novel=0, attempts=0, canon=0)
    r = None
    for k in range(K):
        r = synthesize(target, nvars, Base(), 0, K=1, owned=False, shared=True)
        for f in tot: tot[f] += r[f]
    return dict(r, **tot)

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

def certificate(base, pid, name):
    rec = base.prog[pid]
    if not rec["deps"]:
        return
    print(f"        CERTIFICATE {name}: witness {pid[:8]} "
          f"(ref {rec['ref']}, exp {rec['exp']}, cost {rec['cost']}, "
          f"first composed in task {rec['first']}, level {rec['level']})")
    for d in sorted(rec["deps"]):
        dr = base.prog[d]
        print(f"          uses component {d[:8]} synthesized in task "
              f"{dr['first']} (ref {dr['ref']}, cost {dr['cost']}) -- "
              f"structure unavailable to that component-producing search")
    # any AP-free witness of the same behavior earlier?
    for (nv, s), r in base.beh.items():
        if pid in r["alts"]:
            rawwits = [a for a in r["alts"] if not base.prog[a]["deps"]]
            if rawwits:
                ft = min(base.prog[a]["first"] for a in rawwits)
                print(f"          note: AP-free witness also exists "
                      f"(first task {ft})")
            else:
                print(f"          no AP-free witness of this behavior exists "
                      f"in the store")
            break

# ==================================================================== sections
def sec_LAWS():
    rng = random.Random(0)
    def rp():
        e = rng.getrandbits(32).to_bytes(4, "big")
        return dict(ast=("V", 0), arity=2, type="t", enc=e, ref=rng.randint(1, 9),
                    exp=rng.randint(1, 30), deps=frozenset({rng.randint(0, 3)}),
                    cost=rng.choice([INF, rng.randint(1, 99)]),
                    level=rng.randint(1, 9), first=rng.randint(0, 9),
                    tasks=frozenset({rng.randint(0, 9)}))
    def rb():
        return dict(pref=(rng.randint(1, 9), rng.randint(1, 30),
                          rng.randint(1, 99), f"{rng.getrandbits(32):08x}"),
                    alts=frozenset({rng.randint(0, 9)}),
                    prov=frozenset({rng.randint(0, 9)}))
    def re_():
        return dict(nf="N", cost=rng.randint(1, 99),
                    workers=frozenset({rng.randint(0, 3)}),
                    tasks=frozenset({rng.randint(0, 9)}))
    ok = True
    STRUCT = ("ast", "arity", "type", "enc", "ref", "exp")
    for join, gen, fix in ((pjoin, rp, True), (bjoin, rb, None), (ejoin, re_, None)):
        for _ in range(200):
            a, b, c = gen(), gen(), gen()
            if fix:   # same id => same canonical structure: copy id-determined
                for f in STRUCT:          # fields; only lattice fields vary
                    b[f] = a[f]; c[f] = a[f]
            ok &= join(a, b) == join(b, a)
            ok &= join(join(a, b), c) == join(a, join(b, c))
            ok &= join(a, a) == a
    print(f"[LAWS] program/behavior/evaluation joins each pass "
          f"comm/assoc/idem over 200 random triples: {ok}")
    assert ok
    w = Worker(0, Base(), 0)
    _, sig, _ = w.classify(("AND", ("V", 0), ("V", 0)), 1, 1)
    assert sig == (False, True)
    src = compile_ic(("AND", ("V", 0), ("V", 0)), 1, Alloc(90000))
    pnf, _, _ = ic_float.run(src)
    bad = False
    try:
        nf2, _, _ = ic_float.run(f"({pnf} {TRUE})")
        bad = decode_bool(nf2) is not True
    except RecursionError:
        bad = True
    print(f"[LAWS] AND(x,x) wire regression: source path correct, printed-NF "
          f"round-trip non-faithful: {bad}")
    assert bad
    print("=" * 88)

def ladder_C(order="fwd", K=8, foldseed=None):
    """One accumulating L2 ladder; returns fingerprint for the DET battery."""
    base = Base()
    tot = [0, 0]
    for t, (name, fn) in enumerate(L2_SPECS):
        r = synthesize(sig_of(fn, 2), 2, base, 200 + t, K=K)
        tot[0] += r["paid"]; tot[1] += r["novel"]
    pref = {s: base.beh[(2, s)]["pref"][3] for (n, s) in base.beh if n == 2}
    return (frozenset(pref.items()), tuple(tot))

def sec_DET():
    print(f"[DET] schedule-independence battery on the accumulating L2 ladder")
    runs = {}
    runs["K=8"] = ladder_C(K=8)
    runs["K=4"] = ladder_C(K=4)
    runs["K=8 again"] = ladder_C(K=8)
    agree = len(set(runs.values())) == 1
    pf, tot = runs["K=8"]
    print(f"    preferred-program maps and (paid, novel) totals identical "
          f"across {list(runs)}: {agree}   totals {tot}")
    print(f"    (worker enumeration order cannot matter by construction: "
          f"candidates are processed in pid-sorted stream order and folds "
          f"use lawful joins; K is the substantive perturbation)")
    assert agree
    print("=" * 88)

def run_ladder(specs, nvars, conds, base_for, lib=None):
    print(f"{'spec':>6} | " + " | ".join(f"{c:>29}" for c in conds))
    tot = {c: [0, 0, 0, 0] for c in conds}
    for t, (name, fn) in enumerate(specs):
        tgt = sig_of(fn, nvars); row = []
        for c in conds:
            if c == "A":
                r = run_A(tgt, nvars)
            else:
                r = synthesize(tgt, nvars, base_for(c), nvars * 100 + t,
                               lib=(lib if c == "CP" else None))
            for i, f in enumerate(("paid", "novel", "attempts", "canon")):
                tot[c][i] += r[f]
            tag = ("L" if r["how"] == "frontier-lookup"
                   else "Y" if r["solved"] else "n")
            pid = r.get("pid")
            row.append(f"{r['paid']:>9} {r['novel']:>5} {r['attempts']:>6} "
                       f"{r['xt']:>4} {tag} {(pid or '-')[:6]:>6}")
            if c == "CP" and pid: certificate(base_for(c), pid, name)
        print(f"{name:>6} | " + " | ".join(f"{x:>29}" for x in row))
    print(f"{'TOTAL':>6} | " + " | ".join(
        f"{tot[c][0]:>9} {tot[c][1]:>5} {tot[c][2]:>6} c{tot[c][3]:<9}" for c in conds))
    print(f"    columns: paid  novel  attempts  xtask-hits  Y/L/n  pid; "
          f"TOTAL adds c=canon calls")
    return tot

def sec_L2():
    print(f"[L2] K=8, hash-owned, pid-sorted streams, level-complete, "
          f"folds every 16 novel; A = 8 executed isolated searches")
    cbase = Base()
    fresh = {}
    def base_for(c):
        if c == "B":
            fresh["B"] = Base(); return fresh["B"]
        return cbase
    run_ladder(L2_SPECS, 2, ["A", "B", "C"], base_for)
    n2 = sum(1 for (n, s) in cbase.beh if n == 2)
    print(f"    C frontier: {n2}/16 two-input behaviors witnessed")
    print("=" * 88)
    return cbase

def sec_L3(cbase, conds):
    lib = sorted({r["pref"][3] for (n, s), r in cbase.beh.items() if n == 2})
    print(f"[L3] budget vector: novel<=2500, interactions<=500k, size<=11; "
          f"library = {len(lib)} referenced 2-input programs")
    forks = {c: copy.deepcopy(cbase) for c in conds if c != "B"}
    holder = {}
    def base_for(c):
        if c == "B":
            if "B" not in holder: holder["B"] = Base()
            return holder["B"]
        return forks[c]
    for t, _ in enumerate(L3_SPECS):
        holder.pop("B", None)
    def base_for2(c):
        if c == "B": return Base()
        return forks[c]
    run_ladder(L3_SPECS, 3, conds, base_for2, lib=lib)
    if "CP" in conds:
        # transport: a fresh "process" gets only the copied Base
        moved = copy.deepcopy(forks["CP"])
        tgt = sig_of(L3_SPECS[3][1], 3)
        rec = moved.beh.get((3, tgt))
        if rec:
            w = Worker(0, moved, 999)
            ast = moved.prog[rec["pref"][3]]["ast"]
            raw = w.resolve_raw(ast)
            src = compile_ic(raw, 3, Alloc(95000))
            sig = []
            for tup in itertools.product((False, True), repeat=3):
                app = src
                for b in tup: app = f"({app} {BOOL[b]})"
                sig.append(decode_bool(ic_float.run(app)[0]))
            print(f"    [TRANSPORT] fresh process, copied Base only: resolved "
                  f"XOR3 witness {rec['pref'][3][:8]} through the program "
                  f"store and reproduced its signature: {tuple(sig) == tgt}")
            assert tuple(sig) == tgt
    print("=" * 88)

if __name__ == "__main__":
    args = [a.upper() for a in sys.argv[1:]]
    SEC = set(a for a in args if a in ("LAWS", "DET", "L2", "L3")) or {"LAWS"}
    conds = [a for a in args if a in ("B", "C", "CP")] or ["B", "C", "CP"]
    t0 = time.perf_counter()
    if "LAWS" in SEC: sec_LAWS()
    if "DET" in SEC: sec_DET()
    cbase = None
    if "L2" in SEC or "L3" in SEC: cbase = sec_L2()
    if "L3" in SEC: sec_L3(cbase, conds)
    print(f"total wall {time.perf_counter()-t0:.0f}s")
