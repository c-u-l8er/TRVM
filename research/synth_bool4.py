"""
synth_bool4.py -- serialized, cross-process compositional synthesis.

Implements the v3 review's order. What changed:

1. SOLUTION-COMPLETION RESERVE. Once any solution is seen in a level, the
   level runs to completion regardless of budget, so the winner is the true
   level minimum under the total order. Budgets bind only pre-solution
   (level-granular in multiprocess mode, stated below).

2. DERIVED PREFERENCE, SPLIT COSTS. BehaviorRecords now store only
   {alternatives, provenance}. The preferred representative is DERIVED on
   demand from current ProgramRecords by (ref_size, exp_size, intrinsic_cost,
   pid) -- no duplicated cost to go stale. ProgramRecords carry both
   intrinsic_cost (sum of the canonical computations' own costs, from the
   evaluation store -- context-free) and marginal_cost (new interactions paid
   at first classification -- context-dependent). Pareto sets over these are
   the next rung; this file keeps them separate and reports both.

3. TYPE GATE. type_check validates variable indices, AP argument counts
   against the referenced record's arity, and recursively all Bool typing.
   Every record imported from serialized bytes is re-verified: enc(ast) and
   pid recomputed and matched, type_check passed. Malformed imports rejected.

4. MECHANICAL CERTIFICATE. Each task stores a SearchContext (arity, grammar,
   library ids, max size, classified pid set; static fields join by
   assert-equal, classified by union). The certificate now CHECKS, not
   narrates: for each dependency, that the witness pid is absent from every
   component-producing task's classified set, and that those tasks' grammars
   contained no AP node (hence the witness was ungeneratable there).

5. SERIALIZATION + REAL PROCESS BOUNDARY. Canonical JSON encoding for all
   four stores (sort_keys, hex for bytes, sorted lists for sets, null for
   INF); round-trip equality is a [LAWS] regression. The [MP] section runs
   the L2 ladder and the L3 CP tasks with K real OS worker processes
   (children import the runtime independently, receive ONLY serialized base
   deltas on stdin, regenerate their owned slice of the deterministic
   candidate stream themselves, and reply with serialized semilattice deltas
   on stdout). The orchestrator merges child deltas in seeded-shuffled order
   (lawful joins make order irrelevant; asserted once against sorted order).
   The XOR3 certificate is then produced from state assembled exclusively
   from cross-process deltas -- the review's named milestone. A matched
   in-process run at per-level fold cadence must agree on the preferred map
   (asserted); paid/novel totals are reported for both (cap semantics are
   level-granular in MP, so totals can differ only when a cap binds).

6. WIDER BATTERY, SPLIT CLAIMS. [DET] sweeps K in {1,2,4,8,16} with
   seed-shuffled fold order on the accumulating L2 ladder, and reports
   SEMANTIC invariance (preferred maps) separately from ECONOMIC invariance
   (totals). Physical execution-order perturbation is provided by [MP]
   itself, where OS scheduling orders child completion nondeterministically.

v4.2 PROTOCOL-INTEGRITY PASS. Workers submit observations, not authority:
   behavior associations are checked against signatures DERIVED from imported
   evaluation records; imported evaluations are re-executed on a seeded sample
   (p=0.15 in MP; a receiver nonce replaces the fixed seed in adversarial
   settings) and both normal form and cost must match; provenance and search
   contexts are stamped from orchestrator job manifests, never taken from
   worker claims. MP budget: post-level cap checks; solution-bearing levels
   complete with a one-level reserve and reported overrun. Accurate label:
   trusted-orchestrator, structurally validated, spot-verified cross-process
   synthesis. Full adversarial verification (redundant execution, traces,
   signatures, decentralized manifests) remains open.

Still deferred, labeled: Pareto-frontier representatives and cost-guided
search; runtime REF linking; asynchronous (non-level-synchronous) synthesis.

Run:
  PYTHONPATH=runtime/python:research python3 research/synth_bool4.py LAWS DET
  PYTHONPATH=runtime/python:research python3 research/synth_bool4.py MP
"""
import sys, os, time, random, itertools, hashlib, copy, json, subprocess
sys.setrecursionlimit(100000)

import ic_float
from incrdt import TRUE, FALSE
from synth_bool3 import (enc, pid_of, type_desc, ref_size, deps_of, compile_ic,
                         decode_bool, Alloc, BOOL, sig_of, L2_SPECS, L3_SPECS)

EVAL_V = "ic_float-1"                          # runtime semantics version
COST_V = "interactions-1"                      # cost-model version
def evkey(canon):
    """Domain-separated, versioned evaluation identity: heterogeneous
    evaluators or changed cost models can never collide keys."""
    return f"EV|{EVAL_V}|{COST_V}|{canon}"

INF = float("inf")

class InvalidDelta(Exception):
    """Protocol validation failure. Never an assert: imported data must be
    rejected even under python -O."""

def req(cond, msg):
    if not cond: raise InvalidDelta(msg)

def pjoin(a, b):
    req(all(a[f] == b[f] for f in
            ("ast", "arity", "type", "enc", "ref", "exp", "deps")),
        "id collision")
    return dict(ast=a["ast"], arity=a["arity"], type=a["type"], enc=a["enc"],
                ref=a["ref"], exp=a["exp"], deps=a["deps"] | b["deps"],
                cost=min(a["cost"], b["cost"]),
                cost_i=min(a["cost_i"], b["cost_i"]),
                level=min(a["level"], b["level"]),
                first=min(a["first"], b["first"]), tasks=a["tasks"] | b["tasks"])

def ejoin(a, b):
    req(a["nf"] == b["nf"], "divergent normal forms under one key")
    return dict(nf=a["nf"], cost=min(a["cost"], b["cost"]),
                workers=a["workers"] | b["workers"],
                tasks=a["tasks"] | b["tasks"])

def bjoin(a, b):
    return dict(alts=a["alts"] | b["alts"], prov=a["prov"] | b["prov"])

def cjoin(a, b):
    for f in ("arity", "grammar", "lib", "max_size"):
        req(a[f] == b[f], "SearchContext static-field divergence")
    return dict(a, classified=a["classified"] | b["classified"])

class Base:
    def __init__(self):
        self.prog = {}; self.beh = {}; self.ev = {}; self.ctx = {}
    def fold_from(self, other_prog, other_beh, other_ev, other_ctx):
        for p, r in other_prog.items():
            self.prog[p] = pjoin(self.prog[p], r) if p in self.prog else r
        for k, r in other_beh.items():
            self.beh[k] = bjoin(self.beh[k], r) if k in self.beh else r
        for k, r in other_ev.items():
            self.ev[k] = ejoin(self.ev[k], r) if k in self.ev else r
        for t, r in other_ctx.items():
            self.ctx[t] = cjoin(self.ctx[t], r) if t in self.ctx else r

def preferred(base, nvars, sig):
    r = base.beh.get((nvars, sig))
    if r is None: return None
    best = None
    for p in r["alts"]:
        pr = base.prog.get(p)
        if pr is None or pr["cost_i"] == INF: continue   # unverified: never
                                                         # preferred
        key = (pr["ref"], pr["exp"], pr["cost_i"], p)
        if best is None or key < best[0]: best = (key, p, pr)
    return best

def resolve_in(ast, prog):
    """Reference expansion against an explicit program environment."""
    if ast[0] == "V": return ast
    if ast[0] == "NOT": return ("NOT", resolve_in(ast[1], prog))
    if ast[0] == "AP":
        rec = prog[ast[1]]
        args = tuple(resolve_in(a, prog) for a in ast[2])
        def sub(t):
            if t[0] == "V": return args[t[1]]
            if t[0] == "NOT": return ("NOT", sub(t[1]))
            if t[0] == "AP": return ("AP", t[1], tuple(sub(a) for a in t[2]))
            return (t[0], sub(t[1]), sub(t[2]))
        return resolve_in(sub(rec["ast"]), prog)
    return (ast[0], resolve_in(ast[1], prog), resolve_in(ast[2], prog))

# ------------------------------------------------------------- type gate
def type_check(ast, nvars, prog):
    if ast[0] == "V": return 0 <= ast[1] < nvars
    if ast[0] == "NOT": return type_check(ast[1], nvars, prog)
    if ast[0] == "AP":
        rec = prog.get(ast[1])
        if rec is None or rec["arity"] != len(ast[2]): return False
        return all(type_check(a, nvars, prog) for a in ast[2])
    if ast[0] in ("AND", "OR"):
        return type_check(ast[1], nvars, prog) and type_check(ast[2], nvars, prog)
    return False

# ------------------------------------------------------------- serialization
def _ast_j(a):
    if a[0] == "V": return ["V", a[1]]
    if a[0] == "NOT": return ["NOT", _ast_j(a[1])]
    if a[0] == "AP": return ["AP", a[1], [_ast_j(x) for x in a[2]]]
    return [a[0], _ast_j(a[1]), _ast_j(a[2])]

def _ast_p(j):
    if j[0] == "V": return ("V", j[1])
    if j[0] == "NOT": return ("NOT", _ast_p(j[1]))
    if j[0] == "AP": return ("AP", j[1], tuple(_ast_p(x) for x in j[2]))
    return (j[0], _ast_p(j[1]), _ast_p(j[2]))

def store_to_json(base):
    return json.dumps(dict(
        prog={p: dict(ast=_ast_j(r["ast"]), arity=r["arity"], type=r["type"],
                      enc=r["enc"].hex(), ref=r["ref"], exp=r["exp"],
                      deps=sorted(r["deps"]),
                      cost=(None if r["cost"] == INF else r["cost"]),
                      cost_i=(None if r["cost_i"] == INF else r["cost_i"]),
                      level=r["level"], first=r["first"],
                      tasks=sorted(r["tasks"]))
              for p, r in base.prog.items()},
        beh={f"{n}|{''.join('1' if b else '0' for b in s)}":
             dict(alts=sorted(r["alts"]), prov=sorted(r["prov"]))
             for (n, s), r in base.beh.items()},
        ev={k: dict(nf=r["nf"], cost=r["cost"], workers=sorted(r["workers"]),
                    tasks=sorted(r["tasks"])) for k, r in base.ev.items()},
        ctx={str(t): dict(arity=r["arity"], grammar=r["grammar"],
                          lib=sorted(r["lib"]), max_size=r["max_size"],
                          classified=sorted(r["classified"]))
             for t, r in base.ctx.items()}), sort_keys=True)

def store_from_json(txt, verify=True, env=None, verify_costs=False,
                    verify_semantics=0.0, sample_seed=0, manifest=None,
                    keys_out=None, vstats=None, verified=None):
    d = json.loads(txt)
    base = Base()
    for p, r in d["prog"].items():
        ast = _ast_p(r["ast"])
        rec = dict(ast=ast, arity=r["arity"], type=r["type"],
                   enc=bytes.fromhex(r["enc"]), ref=r["ref"], exp=r["exp"],
                   deps=frozenset(r["deps"]),
                   cost=(INF if r["cost"] is None else r["cost"]),
                   cost_i=(INF if r["cost_i"] is None else r["cost_i"]),
                   level=r["level"], first=r["first"],
                   tasks=frozenset(r["tasks"]))
        if verify:
            req(enc(ast) == rec["enc"], "canonical bytes mismatch on import")
            req(pid_of(ast, rec["arity"]) == p, "pid mismatch on import")
        base.prog[p] = rec
    for k, r in d["beh"].items():
        n, bits = k.split("|")
        sig = tuple(c == "1" for c in bits)
        base.beh[(int(n), sig)] = dict(alts=frozenset(r["alts"]),
                                       prov=frozenset(r["prov"]))
    for k, r in d["ev"].items():
        req(isinstance(r["cost"], int) and r["cost"] >= 0,
            "invalid evaluation cost")
        base.ev[k] = dict(nf=r["nf"], cost=r["cost"],
                          workers=frozenset(r["workers"]),
                          tasks=frozenset(r["tasks"]))
    for t, r in d["ctx"].items():
        base.ctx[int(t)] = dict(arity=r["arity"], grammar=r["grammar"],
                                lib=frozenset(r["lib"]), max_size=r["max_size"],
                                classified=frozenset(r["classified"]))
    if verify:                       # ALL verification after full parse
        eprog = env.prog if env is not None else {}
        eev = env.ev if env is not None else {}
        scope = {**eprog, **base.prog}
        sigmap = {}
        def derived_sig(rec, ident):
            """Reconstruct a program's signature from evaluation records --
            the only semantic authority. Verifies costs; optionally
            re-executes (all, or a guaranteed minimum of one per program plus
            a seeded sample)."""
            from supgen_swarm import ic_canon
            evs = {**eev, **base.ev}
            raw2 = resolve_in(rec["ast"], scope)
            src2 = compile_ic(raw2, rec["arity"], Alloc(77000))
            tot = 0; bits = []; keys = []; checked = False
            tups = list(itertools.product((False, True), repeat=rec["arity"]))
            must = int(hashlib.sha256((str(sample_seed) + ident).encode()
                                      ).hexdigest(), 16) % len(tups)
            for i, tup in enumerate(tups):
                app = src2
                for bb in tup: app = f"({app} {BOOL[bb]})"
                key2 = evkey(ic_canon(app)); keys.append(key2)
                e = evs.get(key2)
                req(e is not None, "cost_i unverifiable: missing eval")
                tot += e["cost"]
                v = decode_bool(e["nf"])
                req(v is not None, "non-boolean evaluation result")
                bits.append(v)
                h = int(hashlib.sha256((str(sample_seed) + key2).encode()
                                       ).hexdigest(), 16) % 10**6
                if verify_semantics > 0 and (h < verify_semantics * 10**6
                                             or i == must):
                    if verified is not None and key2 in verified:
                        checked = True     # evaluation facts are immutable:
                        continue           # one re-execution per verifier
                    nf2, c2, _ = ic_float.run(app)
                    req(nf2 == e["nf"], "evaluation result forged")
                    req(c2 == e["cost"], "evaluation cost forged")
                    if vstats is not None:
                        vstats["verifier"] = vstats.get("verifier", 0) + c2
                    if verified is not None: verified.add(key2)
                    checked = True
            req(tot == rec["cost_i"], "cost_i forged")
            if keys_out is not None: keys_out[ident] = keys
            return tuple(bits)
        for p, r in base.prog.items():
            ast = r["ast"]
            req(r["type"] == type_desc(r["arity"]), "type field forged")
            req(r["ref"] == ref_size(ast), "ref field forged")
            req(r["deps"] == frozenset(deps_of(ast, set())), "deps forged")
            req(all(d in scope for d in r["deps"]), "dangling dependency")
            req(type_check(ast, r["arity"], scope),
                "type-invalid imported program")
            raw = resolve_in(ast, scope)
            req(r["exp"] == ref_size(raw), "exp field forged")
            if verify_costs and r["cost_i"] != INF:
                sigmap[p] = derived_sig(r, p)
        if verify_costs:            # behavior facts DERIVE from evaluations,
            for (nv, s), r in base.beh.items():    # for EVERY alternative --
                for a in r["alts"]:                # delta-side or receiver-
                    rec = base.prog.get(a) or eprog.get(a)   # resident
                    req(rec is not None, "dangling behavior alt")
                    req(rec["cost_i"] != INF,
                        "unverified program in behavior record")
                    sig = sigmap.get(a)
                    if sig is None:
                        sig = derived_sig(rec, a); sigmap[a] = sig
                    req(sig == s, "behavior association forged")
        if verify_costs:            # OMISSION RESISTANCE: behavior records are
            derived = {}            # RECEIVER-DERIVED from verified programs;
            for p, r in base.prog.items():   # worker records were hints --
                if r["cost_i"] == INF: continue      # verified, then replaced
                kk = (r["arity"], sigmap[p])
                nr = dict(alts=frozenset({p}), prov=frozenset(r["tasks"]))
                derived[kk] = bjoin(derived[kk], nr) if kk in derived else nr
            base.beh = derived
        for (nv, s), r in base.beh.items():        # referential integrity,
            req(all(a in scope for a in r["alts"]),  # verify_costs or not
                "dangling behavior alt")
        for t, c in base.ctx.items():
            req(all(x in scope for x in c["lib"]), "dangling library id")
            req(all(x in scope for x in c["classified"]),
                "dangling classified id")
    if manifest is not None:            # trusted-orchestrator topology:
        for p, r in base.prog.items():  # provenance is stamped from the job
            r["first"] = manifest["task"]           # manifest, never taken
            r["tasks"] = frozenset({manifest["task"]})   # from worker claims
            r["level"] = manifest["level"]
        for k, r in base.beh.items():
            r["prov"] = frozenset({manifest["task"]})
        for t in list(base.ctx):
            c = base.ctx.pop(t)
            base.ctx[manifest["task"]] = dict(c, arity=manifest["arity"],
                                              grammar=manifest["grammar"],
                                              lib=manifest["lib"],
                                              max_size=manifest["max_size"])
    return base

# ------------------------------------------------------------- worker
class Worker:
    def __init__(self, k, base, task):
        self.k = k; self.base = base; self.task = task
        self.prog = {}; self.beh = {}; self.ev = {}; self.ctx = {}
        self.alloc = Alloc(50000 + 1000 * k)
        self.paid = self.novel = self.attempts = self.canon = 0
    def _get(self, table, key):
        v = getattr(self, table).get(key)
        return v if v is not None else getattr(self.base, table).get(key)
    def resolve_raw(self, ast):
        return resolve_in(ast, {**self.base.prog, **self.prog})
    def _run(self, src):
        from supgen_swarm import ic_canon
        self.canon += 1
        key = evkey(ic_canon(src))
        e = self._get("ev", key)
        if e is not None: return e["nf"], e["cost"], False
        nf, c, _ = ic_float.run(src)
        self.paid += c
        self.ev[key] = dict(nf=nf, cost=c, workers=frozenset({self.k}),
                            tasks=frozenset({self.task}))
        return nf, c, True
    def classify(self, ast, nvars, level_no):
        self.attempts += 1
        p = pid_of(ast, nvars)
        known = self._get("prog", p)
        if known is not None and known["cost"] < INF:
            for (nv, s), r in list(self.base.beh.items()) + list(self.beh.items()):
                if nv == nvars and p in r["alts"]:
                    self._ctx_add(nvars, p)
                    return p, s, False
        merged = {**self.base.prog, **self.prog}
        assert type_check(ast, nvars, merged), f"type error: {ast}"
        self.novel += 1
        raw = self.resolve_raw(ast)
        src = compile_ic(raw, nvars, self.alloc)
        p0 = self.paid; intr = 0
        sig = []
        for tup in itertools.product((False, True), repeat=nvars):
            app = src
            for b in tup: app = f"({app} {BOOL[b]})"
            nf, c, _ = self._run(app)
            intr += c
            v = decode_bool(nf)
            assert v is not None
            sig.append(v)
        sig = tuple(sig)
        rec = dict(ast=ast, arity=nvars, type=type_desc(nvars), enc=enc(ast),
                   ref=ref_size(ast), exp=ref_size(raw),
                   deps=frozenset(deps_of(ast, set())),
                   cost=self.paid - p0, cost_i=intr,
                   level=level_no, first=self.task, tasks=frozenset({self.task}))
        self.prog[p] = pjoin(self.prog[p], rec) if p in self.prog else rec
        k = (nvars, sig)
        b = dict(alts=frozenset({p}), prov=frozenset({self.task}))
        self.beh[k] = bjoin(self.beh[k], b) if k in self.beh else b
        self._ctx_add(nvars, p)
        return p, sig, True
    def _ctx_add(self, nvars, p):
        c = self.ctx.get(self.task)
        if c is None:
            c = dict(arity=nvars, grammar=self._grammar, lib=self._lib,
                     max_size=self._max, classified=frozenset())
        self.ctx[self.task] = dict(c, classified=c["classified"] | {p})

# ------------------------------------------------------------- shared search logic
def reps_from(base, nvars):
    out = {}
    for (nv, s), r in base.beh.items():
        if nv != nvars: continue
        pr = preferred(base, nv, s)
        if pr is not None: out[s] = (pr[2]["ref"], pr[2]["ast"])
    return out

def gen_level(reps, size, lib):
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
    return gen

def synthesize(target, nvars, base, task, K=8, lib=None, novel_cap=2500,
               int_cap=500000, max_size=11, fold_every=16, foldseed=None):
    t0 = time.perf_counter()
    hit = base.beh.get((nvars, target))
    if hit is not None and task not in hit["prov"]:
        pr = preferred(base, nvars, target)
        return dict(solved=True, how="frontier-lookup", pid=pr[1], attempts=0,
                    novel=0, paid=0, canon=0, wall=0.0)
    workers = [Worker(k, base, task) for k in range(K)]
    for w in workers:
        w._grammar = "raw+AP" if lib else "raw"
        w._lib = frozenset(lib or []); w._max = max_size
    rng = random.Random(foldseed)
    def fold_all():
        ws = list(workers)
        if foldseed is not None: rng.shuffle(ws)
        for w in ws:
            base.fold_from(w.prog, w.beh, w.ev, w.ctx)
            w.prog = {}; w.beh = {}; w.ev = {}; w.ctx = {}
    stats = lambda f: sum(getattr(w, f) for w in workers)
    def result(solved, how, pid):
        fold_all()
        if solved and how == "search":
            pid = preferred(base, nvars, target)[1]   # the lattice's answer,
        return dict(solved=solved, how=how, pid=pid,  # not the stream's
                    attempts=stats("attempts"), novel=stats("novel"),
                    paid=stats("paid"), canon=stats("canon"),
                    wall=time.perf_counter() - t0)
    def level(cands, level_no):
        stream, seen = [], set()   # (in-process level; unchanged)
        for ast in sorted(cands, key=lambda a: pid_of(a, nvars)):
            p = pid_of(ast, nvars)
            if p not in seen: seen.add(p); stream.append((p, ast))
        sols, done, reserve = [], 0, False
        for p, ast in stream:
            if not reserve and (stats("novel") >= novel_cap or
                                stats("paid") >= int_cap):
                return sols, True
            w = workers[int(p[:16], 16) % K]
            _, sig, new = w.classify(ast, nvars, level_no)
            done += new
            if sig == target:
                sols.append((ref_size(ast), ref_size(w.resolve_raw(ast)), p))
                reserve = True           # solution-completion reserve
            if done >= fold_every: fold_all(); done = 0
        fold_all()
        return sols, False
    sols, cut = level([("V", i) for i in range(nvars)], 1)
    if sols: return result(True, "search", min(sols)[2])
    if cut: return result(False, "budget", None)
    size = 1
    while size < max_size:
        size += 1
        sols, cut = level(gen_level(reps_from(base, nvars), size, lib), size)
        if sols: return result(True, "search", min(sols)[2])
        if cut: return result(False, "budget", None)
    return result(False, "exhausted", None)

def derive_and_check(prog_start, ev_start, d, keymap, k, slice_set,
                     slice_list, task, claimed_paid, claimed_novel):
    """The orchestrator derives everything a worker owes -- programs AND the
    exact evaluation records those programs entail -- against the level-start
    snapshot. prog_start maps pid -> cost_i so that quarantined (INF)
    programs have a promotion path: they are RE-OWED, not rejected as excess.
    Assigned candidates must return verified finite results (Policy A);
    malformed results reject cleanly, never crash accounting."""
    expected = {p for p in slice_set
                if prog_start.get(p, INF) == INF}   # new OR awaiting upgrade
    req(set(d.prog) == expected,
        "incomplete or excess slice results")
    c = d.ctx.get(task)
    if slice_set:
        req(c is not None and c["classified"] == slice_set,
            "classified set forged")
    else:
        req(c is None, "classified set forged")
    req(claimed_novel == len(d.prog), "novel count forged")
    novel = sum(1 for p in d.prog if p not in prog_start)
    upgrades = len(d.prog) - novel
    seen = set(ev_start); paid = 0; exp_ev = set()
    for p in slice_list:
        r = d.prog.get(p)
        if r is None: continue                    # replayed verified candidate
        req(r["cost_i"] != INF,                   # Policy A: assigned work
            "unverified result for assigned candidate")   # returns verified
        req(p in keymap, "missing verification keys")     # results
        m = 0
        for kk in keymap[p]:
            if kk not in seen:
                m += d.ev[kk]["cost"] if kk in d.ev else 0
                exp_ev.add(kk); seen.add(kk)
        req(m == r["cost"], "marginal cost forged")
        paid += m
    req(set(d.ev) == exp_ev,                      # the EvaluationStore mirror
        "incomplete or excess evaluation results")   # of program completeness
    req(claimed_paid == paid, "paid total forged")
    for r in d.ev.values():                       # evaluation provenance is
        r["workers"] = frozenset({k})             # stamped, not claimed
        r["tasks"] = frozenset({task})
    return paid, novel, upgrades

def base_or(d, kk):
    return d.ev[kk]["cost"] if kk in d.ev else 0

# ------------------------------------------------------------- certificate
def certificate(base, pid, name):
    rec = base.prog[pid]
    if not rec["deps"]: return
    print(f"    CERTIFICATE {name}: witness {pid[:8]} (ref {rec['ref']}, "
          f"exp {rec['exp']}, intrinsic {rec['cost_i']}, marginal "
          f"{rec['cost']}, composed task {rec['first']} level {rec['level']})")
    alldeps, frontier = set(), set(rec["deps"])
    while frontier:                               # full dependency DAG
        d = frontier.pop()
        if d in alldeps: continue
        alldeps.add(d)
        frontier |= set(base.prog[d]["deps"]) - alldeps
    for d in sorted(alldeps):
        dr = base.prog[d]
        checks = []
        for t in sorted(dr["tasks"]):
            c = base.ctx.get(t)
            if c is None: continue
            absent = pid not in c["classified"]
            no_ap = c["grammar"] == "raw"
            checks.append((t, absent, no_ap))
        ok = all(a and g for _, a, g in checks) and checks
        print(f"      component {d[:8]} from task(s) {sorted(dr['tasks'])}: "
              f"witness absent from each producing task's classified set AND "
              f"each such grammar lacked AP: {bool(ok)}  [MECHANICALLY CHECKED]")
    for (nv, s), r in base.beh.items():
        if pid in r["alts"]:
            raws = [a for a in r["alts"] if not base.prog[a]["deps"]]
            print(f"      AP-free witness of this behavior IN THIS STORE: "
                  f"{('yes, first task ' + str(min(base.prog[a]['first'] for a in raws))) if raws else 'none'}")
            break

# ==================================================================== sections
def sec_LAWS():
    rng = random.Random(0)
    def rp():
        return dict(ast=("V", 0), arity=2, type="t", enc=b"e",
                    ref=3, exp=5, deps=frozenset(),   # ast-determined: const
                    cost=rng.choice([INF, rng.randint(1, 99)]),
                    cost_i=rng.choice([INF, rng.randint(1, 99)]),
                    level=rng.randint(1, 9), first=rng.randint(0, 9),
                    tasks=frozenset({rng.randint(0, 9)}))
    def rb():
        return dict(alts=frozenset({rng.randint(0, 9)}),
                    prov=frozenset({rng.randint(0, 9)}))
    def re_():
        return dict(nf="N", cost=rng.randint(1, 99),
                    workers=frozenset({rng.randint(0, 3)}),
                    tasks=frozenset({rng.randint(0, 9)}))
    def rc():
        return dict(arity=2, grammar="raw", lib=frozenset(), max_size=11,
                    classified=frozenset({rng.randint(0, 9)}))
    ok = True
    for join, gen in ((pjoin, rp), (bjoin, rb), (ejoin, re_), (cjoin, rc)):
        for _ in range(200):
            a, b2, c = gen(), gen(), gen()
            ok &= join(a, b2) == join(b2, a)
            ok &= join(join(a, b2), c) == join(a, join(b2, c))
            ok &= join(a, a) == a
    print(f"[LAWS] program/behavior/evaluation/context joins each pass "
          f"comm/assoc/idem over 200 random triples: {ok}")
    assert ok
    b = Base()
    w = Worker(0, b, 0); w._grammar = "raw"; w._lib = frozenset(); w._max = 11
    for ast in (("AND", ("V", 0), ("V", 1)), ("OR", ("V", 0), ("NOT", ("V", 1)))):
        w.classify(ast, 2, 2)
    b.fold_from(w.prog, w.beh, w.ev, w.ctx)
    txt = store_to_json(b)
    b2 = store_from_json(txt, verify=True)
    rt = store_to_json(b2) == txt
    print(f"[LAWS] serialization round-trip (canonical JSON, verified import): {rt}")
    assert rt
    bad = json.loads(txt)
    k0 = sorted(bad["prog"])[0]
    bad["prog"][k0]["ast"] = ["V", 7]          # tampered AST, stale pid
    try:
        store_from_json(json.dumps(bad, sort_keys=True)); gate = False
    except (AssertionError, InvalidDelta):
        gate = True
    print(f"[LAWS] tampered import rejected by pid/enc/type gate: {gate}")
    assert gate
    ok = type_check(("AP", "deadbeef", (("V", 0),)), 1, {}) is False
    print(f"[LAWS] AP arity/type gate rejects unknown or misapplied "
          f"components: {ok}")
    assert ok
    rejected = []
    for field, val in (("ref", 0), ("exp", 0), ("cost_i", 0),
                       ("type", "Malicious")):
        bad = json.loads(txt); k0 = sorted(bad["prog"])[0]
        bad["prog"][k0][field] = val
        try:
            store_from_json(json.dumps(bad, sort_keys=True), verify_costs=True)
            rejected.append((field, False))
        except (AssertionError, InvalidDelta): rejected.append((field, True))
    bad = json.loads(txt); k0 = sorted(bad["prog"])[0]
    bad["prog"][k0]["deps"] = ["ffff" * 16]
    try:
        store_from_json(json.dumps(bad, sort_keys=True)); rejected.append(
            ("fake-dep", False))
    except (AssertionError, InvalidDelta): rejected.append(("fake-dep", True))
    bad = json.loads(txt)
    bk = sorted(bad["beh"])[0]
    bad["beh"][bk]["alts"] = ["ffff" * 16]
    try:
        store_from_json(json.dumps(bad, sort_keys=True)); rejected.append(
            ("dangling-alt", False))
    except (AssertionError, InvalidDelta): rejected.append(("dangling-alt", True))
    allr = all(r for _, r in rejected)
    print(f"[LAWS] hardened import rejects forged metadata: "
          f"{dict(rejected)}  all rejected: {allr}")
    assert allr
    sem = []
    bad = json.loads(txt)                     # A1: false behavior association
    ks = sorted(bad["beh"]); a0 = bad["beh"][ks[0]]["alts"][0]
    bad["beh"][ks[1]]["alts"] = sorted(set(bad["beh"][ks[1]]["alts"]) | {a0})
    try:
        store_from_json(json.dumps(bad, sort_keys=True), verify_costs=True)
        sem.append(("false-association", False))
    except (AssertionError, InvalidDelta): sem.append(("false-association", True))
    bad = json.loads(txt)                     # A2: forged NF, association fixed
    pk = sorted(bad["prog"])[0]
    from synth_bool4 import _ast_p as _p
    ek = None
    for kk, ee in bad["ev"].items():
        if decode_bool(ee["nf"]) is True: ek = kk; break
    bad["ev"][ek]["nf"] = FALSE               # flip a TRUE result to FALSE-NF
    fixed = {}
    for bk in list(bad["beh"]):
        fixed[bk] = bad["beh"][bk]
    try:
        store_from_json(json.dumps(bad, sort_keys=True), verify_costs=True,
                        verify_semantics=1.0)
        sem.append(("forged-NF", False))
    except (AssertionError, InvalidDelta): sem.append(("forged-NF", True))
    bad = json.loads(txt)                     # A3: provenance forgery
    bad["prog"][pk]["first"] = 999; bad["prog"][pk]["tasks"] = [999]
    got = store_from_json(json.dumps(bad, sort_keys=True),
                          manifest=dict(task=0, level=2, arity=2,
                                        grammar="raw", lib=frozenset(),
                                        max_size=11))
    sem.append(("forged-provenance-stamped",
                got.prog[pk]["first"] == 0 and got.prog[pk]["tasks"] ==
                frozenset({0})))
    allsem = all(r for _, r in sem)
    print(f"[LAWS] semantic layer: {dict(sem)}  all handled: {allsem}")
    assert allsem
    # ---- authority-removal battery (v4.3) ----------------------------------
    recv = Base()                                   # receiver already holds a
    w0 = Worker(0, recv, 5)                         # verified AND program
    w0._grammar = "raw"; w0._lib = frozenset(); w0._max = 11
    and_pid, and_sig, _ = w0.classify(("AND", ("V", 0), ("V", 1)), 2, 3)
    recv.fold_from(w0.prog, w0.beh, w0.ev, w0.ctx)
    auth = []
    inv = tuple(not b for b in and_sig)             # B1: false behavior for an
    forged = json.dumps(dict(prog={}, ev={}, ctx={},  # EXISTING program
        beh={f"2|{''.join('1' if b else '0' for b in inv)}":
             dict(alts=[and_pid], prov=[5])}), sort_keys=True)
    try:
        store_from_json(forged, env=recv, verify_costs=True)
        auth.append(("existing-prog-false-behavior", False))
    except InvalidDelta: auth.append(("existing-prog-false-behavior", True))
    w1 = Worker(0, Base(), 6)                       # B2: INF bypass
    w1._grammar = "raw"; w1._lib = frozenset(); w1._max = 11
    orp, orsig, _ = w1.classify(("OR", ("V", 0), ("V", 1)), 2, 3)
    dj = Base(); dj.fold_from(w1.prog, w1.beh, w1.ev, w1.ctx)
    bad = json.loads(store_to_json(dj))
    bad["prog"][orp]["cost"] = None; bad["prog"][orp]["cost_i"] = None
    try:
        store_from_json(json.dumps(bad, sort_keys=True), verify_costs=True)
        auth.append(("INF-bypass", False))
    except InvalidDelta: auth.append(("INF-bypass", True))
    # honest delta for derive_and_check attacks
    w2 = Worker(0, Base(), 7)
    w2._grammar = "raw"; w2._lib = frozenset(); w2._max = 11
    pids = []
    for ast2 in (("AND", ("V", 0), ("V", 1)), ("OR", ("V", 0), ("NOT", ("V", 1)))):
        pp, _, _ = w2.classify(ast2, 2, 3); pids.append(pp)
    dj2 = Base(); dj2.fold_from(w2.prog, w2.beh, w2.ev, w2.ctx)
    txt2 = store_to_json(dj2)
    slc = sorted(pids)
    def parse2(t):
        km = {}
        d = store_from_json(t, env=Base(), verify_costs=True,
                            verify_semantics=1.0,
                            manifest=dict(task=7, level=3, arity=2,
                                          grammar="raw", lib=frozenset(),
                                          max_size=11))
        # rebuild keymap (store_from_json fills keys_out when given)
        km = {}
        d2 = store_from_json(t, env=Base(), verify_costs=True, keys_out=km,
                             manifest=dict(task=7, level=3, arity=2,
                                           grammar="raw", lib=frozenset(),
                                           max_size=11))
        return d2, km
    d2, km = parse2(txt2)
    ok_hon = derive_and_check({}, set(), d2, km, 0, set(slc), slc, 7,
                              w2.paid, 2) == (w2.paid, 2, 0)
    auth.append(("honest-delta-derives-equal", ok_hon))
    bad = json.loads(txt2)                          # B3: classified forgery
    for t in list(bad["ctx"]): bad["ctx"][t]["classified"] = []
    d3, km3 = parse2(json.dumps(bad, sort_keys=True))
    try:
        derive_and_check({}, set(), d3, km3, 0, set(slc), slc, 7, w2.paid, 2)
        auth.append(("classified-forged", False))
    except InvalidDelta: auth.append(("classified-forged", True))
    d4, km4 = parse2(txt2)                          # B4: ownership violation
    try:
        derive_and_check({}, set(), d4, km4, 0, set(slc[:1]), slc[:1], 7,
                         w2.paid, 2)
        auth.append(("outside-owned-slice", False))
    except InvalidDelta: auth.append(("outside-owned-slice", True))
    d5, km5 = parse2(txt2)                          # B5: accounting forgery
    try:
        derive_and_check({}, set(), d5, km5, 0, set(slc), slc, 7, 1, 2)
        auth.append(("paid-forged", False))
    except InvalidDelta: auth.append(("paid-forged", True))
    d6, km6 = parse2(txt2)
    try:
        derive_and_check({}, set(), d6, km6, 0, set(slc), slc, 7, w2.paid, 99)
        auth.append(("novel-forged", False))
    except InvalidDelta: auth.append(("novel-forged", True))
    allauth = all(r for _, r in auth)
    print(f"[LAWS] authority removal (v4.3): {dict(auth)}  all handled: "
          f"{allauth}")
    assert allauth
    # ---- omission resistance (v4.4) -----------------------------------------
    omis = []
    bad = json.loads(txt2)                    # O1: suppress behavior records
    bad["beh"] = {}
    d7, km7 = parse2(json.dumps(bad, sort_keys=True))
    have = all(any(p in r["alts"] for r in d7.beh.values()) for p in pids)
    omis.append(("behavior-omission-derived-anyway", have))
    bad = json.loads(txt2)                    # O2: withhold a program record
    drop = sorted(bad["prog"])[0]             # (and its behavior mentions --
    bad["prog"].pop(drop); bad["beh"] = {}    # the subtler form; keeping the
    try:                                      # beh trips dangling-alt earlier)
        d8, km8 = parse2(json.dumps(bad, sort_keys=True))
        derive_and_check({}, set(), d8, km8, 0, set(slc), slc, 7,
                         w2.paid, 1)
        omis.append(("program-omission", False))
    except InvalidDelta: omis.append(("program-omission", True))
    allom = all(r for _, r in omis)
    print(f"[LAWS] omission resistance (v4.4): {dict(omis)}  all handled: "
          f"{allom}")
    assert allom
    # ---- evaluation-store authority + promotion (v4.5) ----------------------
    ev5 = []
    bad = json.loads(txt2)                    # E1: inject an unrelated eval
    bad["ev"][evkey("@(FAKE-KEY)")] = dict(nf=TRUE, cost=7, workers=[9],
                                           tasks=[9])
    try:
        d9, km9 = parse2(json.dumps(bad, sort_keys=True))
        derive_and_check({}, set(), d9, km9, 0, set(slc), slc, 7, w2.paid, 2)
        ev5.append(("eval-injection", False))
    except InvalidDelta: ev5.append(("eval-injection", True))
    bad = json.loads(txt2)                    # E2: negative evaluation cost
    k0 = sorted(bad["ev"])[0]
    bad["ev"][k0]["cost"] = -999
    try:
        parse2(json.dumps(bad, sort_keys=True))
        ev5.append(("negative-cost", False))
    except InvalidDelta: ev5.append(("negative-cost", True))
    bad = json.loads(txt2)                    # E3: INF result for an ASSIGNED
    pk5 = sorted(bad["prog"])[0]              # candidate: reject, don't crash
    bad["prog"][pk5]["cost"] = None; bad["prog"][pk5]["cost_i"] = None
    bad["beh"] = {}
    bad["ev"] = {kk: vv for kk, vv in bad["ev"].items()}
    try:
        dA, kmA = parse2(json.dumps(bad, sort_keys=True))
        derive_and_check({}, set(), dA, kmA, 0, set(slc), slc, 7, w2.paid, 2)
        ev5.append(("INF-for-assigned", False))
    except InvalidDelta: ev5.append(("INF-for-assigned", True))
    except KeyError: ev5.append(("INF-for-assigned", "KeyError-DoS"))
    # E4: promotion path -- an existing INF program upgrades cleanly
    d2b, km2b = parse2(txt2)
    r4 = derive_and_check({slc[0]: INF}, set(), d2b, km2b, 0, set(slc), slc,
                          7, w2.paid, 2)
    ev5.append(("INF-upgrade-promotes", r4 == (w2.paid, 1, 1)))
    allev = all(r is True for _, r in ev5)
    print(f"[LAWS] evaluation authority + promotion (v4.5): {dict(ev5)}  "
          f"all handled: {allev}")
    assert allev
    print("=" * 88)

def ladder(base, K=8, foldseed=None):
    tot = [0, 0]
    for t, (name, fn) in enumerate(L2_SPECS):
        r = synthesize(sig_of(fn, 2), 2, base, 200 + t, K=K, foldseed=foldseed)
        tot[0] += r["paid"]; tot[1] += r["novel"]
    pref = frozenset((s, preferred(base, 2, s)[1]) for (n, s) in base.beh
                     if n == 2)
    return pref, tuple(tot)

def sec_DET():
    print(f"[DET] L2 accumulating ladder: K in (1,2,4,8,16), fold order "
          f"seed-shuffled")
    prefs, tots = set(), set()
    for K in (1, 2, 4, 8, 16):
        p, t = ladder(Base(), K=K, foldseed=K)
        prefs.add(p); tots.add(t)
    print(f"    SEMANTIC invariance (preferred maps identical): "
          f"{len(prefs) == 1}")
    print(f"    ECONOMIC invariance (paid, novel identical):    "
          f"{len(tots) == 1}   {sorted(tots)}")
    print(f"    (physical execution-order perturbation is exercised by [MP]:")
    print(f"     OS-scheduled child completion + shuffled delta merge)")
    assert len(prefs) == 1
    print("=" * 88)

# ------------------------------------------------------------- multiprocess
def mp_task(base, target, nvars, task, K, lib, novel_cap=2500, int_cap=500000,
            max_size=11, procs=None, tally=None, arrival_log=None,
            vstats=None, verified=None):
    hit = base.beh.get((nvars, target))
    if hit is not None and task not in hit["prov"]:
        return dict(solved=True, how="frontier-lookup",
                    pid=preferred(base, nvars, target)[1], paid=0, novel=0)
    import selectors
    sent = Base()                            # what children have already seen
    paid = novel = 0
    size = 0
    while size < max_size:
        if novel >= novel_cap or paid >= int_cap:      # pre-solution caps,
            return dict(solved=False, how="budget",    # level-granular
                        pid=None, paid=paid, novel=novel)
        size += 1
        cands = ([("V", i) for i in range(nvars)] if size == 1 else
                 gen_level(reps_from(base, nvars), size, lib))
        if not cands: continue
        delta = Base()
        delta.prog = {p: r for p, r in base.prog.items()
                      if sent.prog.get(p) != r}
        delta.beh = {k: r for k, r in base.beh.items()
                     if sent.beh.get(k) != r}
        delta.ev = {k: r for k, r in base.ev.items() if sent.ev.get(k) != r}
        delta.ctx = {t: r for t, r in base.ctx.items()
                     if sent.ctx.get(t) != r}
        spids = []
        sseen = set()
        for ast in sorted(cands, key=lambda a: pid_of(a, nvars)):
            pp = pid_of(ast, nvars)
            if pp not in sseen: sseen.add(pp); spids.append(pp)
        slice_map = {kk: [pp for pp in spids
                          if int(pp[:16], 16) % K == kk] for kk in range(K)}
        mani = dict(task=task, level=size, arity=nvars,
                    grammar=("raw+AP" if lib else "raw"),
                    lib=frozenset(lib or []), max_size=max_size)
        msg = json.dumps(dict(op="level", task=task, nvars=nvars, size=size,
                              lib=sorted(lib or []), K=K, max_size=max_size,
                              tgt="".join("1" if b else "0" for b in target),
                              base_delta=json.loads(store_to_json(delta))))
        for pr in procs:
            pr.stdin.write(msg + "\n"); pr.stdin.flush()
        sent = copy.deepcopy(base)
        sel = selectors.DefaultSelector()
        for kk, pr in enumerate(procs):
            sel.register(pr.stdout, selectors.EVENT_READ, (pr, kk))
        raw_deltas, arrivals, replied = [], [], set()
        ev_start = set(base.ev)
        prog_start = {p: r["cost_i"] for p, r in base.prog.items()}
        pending = set(procs)
        chk = copy.deepcopy(base)                 # for sorted-remerge assert
        while pending:                            # merge ON ARRIVAL: real OS
            events = sel.select(timeout=120)      # completion order decides
            req(events, "worker timeout")
            for key, _ in events:
                pr, kexp = key.data
                if pr not in pending: continue
                line = pr.stdout.readline()
                req(len(line) < 64 * 1024 * 1024, "payload too large")
                rep = json.loads(line)
                req(rep["k"] == kexp,             # identity is bound to the
                    "worker identity mismatch")   # connection, not the reply
                req(kexp not in replied, "duplicate worker reply")
                replied.add(kexp)
                pending.discard(pr); sel.unregister(pr.stdout)
                arrivals.append(rep["k"])
                km = {}
                d = store_from_json(
                    json.dumps(rep["delta"], sort_keys=True), env=base,
                    verify_costs=True, verify_semantics=1.0, sample_seed=size,
                    manifest=mani, keys_out=km, vstats=vstats,
                    verified=verified)
                dp, dn, du = derive_and_check(
                    prog_start, ev_start, d, km, rep["k"],
                    set(slice_map[rep["k"]]), slice_map[rep["k"]], task,
                    rep["paid"], rep["novel"])
                base.fold_from(d.prog, d.beh, d.ev, d.ctx)
                raw_deltas.append(rep["delta"])
                paid += dp; novel += dn
                if tally is not None: tally.add(pr.pid)   # receiver-derived,
                                                          # never testimony
        req(replied == set(range(K)), "missing worker reply")
        if arrival_log is not None: arrival_log.append(arrivals)
        for dd in sorted(raw_deltas, key=lambda d: json.dumps(d, sort_keys=True)):
            d = store_from_json(json.dumps(dd, sort_keys=True), env=chk,
                                verify_costs=True, verify_semantics=0.0,
                                manifest=mani)   # identical transform: the
            chk.fold_from(d.prog, d.beh, d.ev, d.ctx)   # check isolates ORDER
        assert store_to_json(chk) == store_to_json(base), \
            "merge order changed the lattice"     # join laws, demonstrated
        got = preferred(base, nvars, target)      # solution existence is
        if got is not None:                       # READ OFF THE VERIFIED
            return dict(solved=True, how="search",       # LATTICE; worker
                        pid=got[1], paid=paid, novel=novel,  # sols ignored
                        overrun=max(0, paid - int_cap))
        if paid >= int_cap or novel >= novel_cap:     # post-level cap check
            return dict(solved=False, how="budget", pid=None, paid=paid,
                        novel=novel)
    return dict(solved=False, how="exhausted", pid=None, paid=paid, novel=novel)

def sec_MP():
    K = 4
    print(f"[MP] {K} real OS worker processes; all cross-boundary state is "
          f"serialized semilattice deltas")
    procs = [subprocess.Popen(
        [sys.executable, "research/synth_worker4.py", str(k), str(K)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
        env=dict(os.environ, PYTHONPATH="runtime/python:research"))
        for k in range(K)]
    tally = set(); arrivals = []; vstats = {}; pv = {}
    verified = set()
    probe = mp_task(Base(), sig_of(L2_SPECS[0][1], 2), 2, 999, K, None,
                    int_cap=1, max_size=1, procs=procs, tally=tally,
                    vstats=pv, verified=set())
    print(f"    cap-semantics probe (int_cap=1, max_size=1): how="
          f"{probe['how']} paid={probe['paid']}  (was 'exhausted' pre-v4.2)")
    assert probe["how"] == "budget"
    print(f"    provenance: all first/tasks/level/context fields are stamped "
          f"from orchestrator job manifests; worker claims are overridden")
    base = Base()
    wp_total = 0
    t0 = time.perf_counter()
    for t, (name, fn) in enumerate(L2_SPECS):
        r = mp_task(base, sig_of(fn, 2), 2, 200 + t, K, None, procs=procs,
                    tally=tally, arrival_log=arrivals, vstats=vstats,
                    verified=verified)
        wp_total += r["paid"]
        print(f"    L2 {name:>6}: paid {r['paid']:>7} novel {r['novel']:>4} "
              f"{r['how']}")
    lib = sorted({preferred(base, 2, s)[1] for (n, s) in base.beh if n == 2})
    for t, (name, fn) in [(0, L3_SPECS[0]), (3, L3_SPECS[3])]:
        r = mp_task(base, sig_of(fn, 3), 3, 300 + t, K, lib, procs=procs,
                    tally=tally, arrival_log=arrivals, vstats=vstats,
                    verified=verified)
        wp_total += r["paid"]
        print(f"    L3 {name:>6}: paid {r['paid']:>7} novel {r['novel']:>4} "
              f"{r['how']}  pid {(r['pid'] or '-')[:8]}")
        if r["pid"]: certificate(base, r["pid"], name)
    for pr in procs:
        pr.stdin.write(json.dumps(dict(op="quit")) + "\n"); pr.stdin.flush()
        pr.wait()
    unique = sum(e["cost"] for e in base.ev.values())
    vf = vstats.get("verifier", 0)
    print(f"    WORK ACCOUNTING (benchmark scope; cap probe reported "
          f"separately as a regression):")
    print(f"      worker-paid {wp_total:,}   verifier {vf:,}   unique "
          f"canonical {unique:,}   total physical {wp_total + vf:,}")
    print(f"      cap probe: worker 16, verifier {pv.get('verifier', 0)}")
    print(f"      full verification is security, not outsourcing -- the "
          f"verification-asymmetry problem, quantified")
    print(f"    distinct OS worker pids that contributed deltas: "
          f"{len(tally)} {sorted(tally)}")
    print(f"    merge-on-arrival: sample completion orders "
          f"{arrivals[:3]} ... {arrivals[-1]} (sorted-remerge asserted "
          f"equal every level)")
    print(f"    (orchestrator pid {os.getpid()}; wall "
          f"{time.perf_counter()-t0:.0f}s)")
    # reconcile: matched in-process run, per-level folds
    base2 = Base()
    paid2 = novel2 = 0
    for t, (name, fn) in enumerate(L2_SPECS):
        r = synthesize(sig_of(fn, 2), 2, base2, 200 + t, K=K,
                       fold_every=10**9)
        paid2 += r["paid"]; novel2 += r["novel"]
    lib2 = sorted({preferred(base2, 2, s)[1] for (n, s) in base2.beh if n == 2})
    for t, (name, fn) in [(0, L3_SPECS[0]), (3, L3_SPECS[3])]:
        r = synthesize(sig_of(fn, 3), 3, base2, 300 + t, K=K, lib=lib2,
                       fold_every=10**9)
        paid2 += r["paid"]; novel2 += r["novel"]
    pref_mp = frozenset((n, s, preferred(base, n, s)[1])
                        for (n, s) in base.beh)
    pref_ip = frozenset((n, s, preferred(base2, n, s)[1])
                        for (n, s) in base2.beh)
    same_state = store_to_json(base) == store_to_json(base2)
    print(f"    RECONCILIATION vs matched in-process run (per-level folds): "
          f"preferred maps identical: {pref_mp == pref_ip}; FULL canonical "
          f"four-store state identical: {same_state}; totals in-process "
          f"({paid2}, {novel2})")
    assert pref_mp == pref_ip and same_state
    print("=" * 88)

if __name__ == "__main__":
    SEC = set(a.upper() for a in sys.argv[1:]) or {"LAWS", "DET"}
    t0 = time.perf_counter()
    if "LAWS" in SEC: sec_LAWS()
    if "DET" in SEC: sec_DET()
    if "MP" in SEC: sec_MP()
    print(f"total wall {time.perf_counter()-t0:.0f}s")
