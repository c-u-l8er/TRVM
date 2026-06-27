"""
iceg.py -- an INTERACTION-CALCULUS-AWARE e-graph (the named frontier).

The open step from idtest: carry rewrite-rule + congruence reasoning over IC terms
that contain dup/sup BINDERS. Two parts:

  IDENTITY (the IC-aware part): e-node keys are de Bruijn over BOTH lambda and dup
  binders, plus duplication-label renaming. So church(6) built on two machines with
  different labels is ONE e-class -- congruence for free, dups and all.

  SEMANTICS: a church-arithmetic rewrite rule (mult fold) + congruence recognizes
  mult(2,3) == church(6) -- on the real dup-bearing terms, across label namespaces,
  WITHOUT reducing. This is incrdt6's cheap recognition, now lifted onto IC terms
  with binders (which incrdt7 had only done for pure lambda).

Run: python3 iceg.py
"""
import sys, ic_float
sys.setrecursionlimit(100000)
from incrdt import parse_tree, NOT, FALSE

def church(n, base=1000):
    if n == 0: return "λf.λx.x"
    if n == 1: return "λf.λx.(f x)"
    cs = [f"c{i}" for i in range(n)]; src = []; cur = "f"
    for i in range(n - 1):
        L = base + n * 1000 + i; nxt = f"t{i}" if i < n - 2 else cs[-1]
        src.append(f"!&{L}{{{cs[i]},{nxt}}}={cur};"); cur = nxt
    body = "x"
    for c in reversed(cs): body = f"({c} {body})"
    return "λf.λx." + "".join(src) + body
MULT = "λm.λn.λf.(m (n f))"
def mult(a, b, base=1000): return f"(({MULT} {church(a, base)}) {church(b, base)})"

# ---- canonical AST: de Bruijn over lambda AND dup binders + label renumbering -----
def to_db(t, env=None, depth=0, lab=None, ln=None):
    if env is None: env = {}; lab = {}; ln = [0]
    g = t[0]
    if g == "var":
        return ("v", depth - 1 - env[t[1]]) if t[1] in env else ("f", t[1])
    if g == "era": return ("e",)
    if g == "lam":
        e = dict(env); e[t[1]] = depth
        return ("lam", to_db(t[2], e, depth + 1, lab, ln))
    if g == "app":
        return ("app", to_db(t[1], env, depth, lab, ln), to_db(t[2], env, depth, lab, ln))
    if g == "sup":
        if t[1] not in lab: lab[t[1]] = ln[0]; ln[0] += 1
        return ("sup", lab[t[1]], to_db(t[2], env, depth, lab, ln), to_db(t[3], env, depth, lab, ln))
    if g == "dup":
        if t[1] not in lab: lab[t[1]] = ln[0]; ln[0] += 1
        v = to_db(t[4], env, depth, lab, ln)
        e = dict(env); e[t[2]] = depth; e[t[3]] = depth + 1
        return ("dup", lab[t[1]], v, to_db(t[5], e, depth + 2, lab, ln))
def db(src): return to_db(parse_tree(src))

# ---- e-graph (binder-canonical e-nodes) -----------------------------------------
class EGraph:
    def __init__(s): s.p = {}; s.cl = {}; s.hc = {}; s.n = 0
    def find(s, x):
        while s.p[x] != x: s.p[x] = s.p[s.p[x]]; x = s.p[x]
        return x
    def add(s, op, args=()):
        en = (op, tuple(s.find(a) for a in args))
        if en in s.hc: return s.find(s.hc[en])
        e = s.n; s.n += 1; s.p[e] = e; s.cl[e] = {en}; s.hc[en] = e; return e
    def add_ast(s, t):
        g = t[0]
        if g == "v": return s.add("v:%d" % t[1])
        if g == "f": return s.add("f:%s" % t[1])
        if g == "e": return s.add("e")
        if g == "lam": return s.add("lam", (s.add_ast(t[1]),))
        if g == "app": return s.add("app", (s.add_ast(t[1]), s.add_ast(t[2])))
        if g == "sup": return s.add("sup:%d" % t[1], (s.add_ast(t[2]), s.add_ast(t[3])))
        if g == "dup": return s.add("dup:%d" % t[1], (s.add_ast(t[2]), s.add_ast(t[3])))
    def merge(s, a, b):
        a, b = s.find(a), s.find(b)
        if a == b: return a
        s.p[b] = a; s.cl[a] = s.cl.get(a, set()) | s.cl.pop(b, set()); return a
    def rebuild(s):
        while True:
            seen = {}; m = False
            for en in list(s.hc):
                cen = (en[0], tuple(s.find(a) for a in en[1])); e = s.find(s.hc[en])
                if cen in seen:
                    if s.find(seen[cen]) != e: s.merge(seen[cen], e); m = True
                else: seen[cen] = e
            if not m: break
        s.hc = {}; s.cl = {}
        for en in list(seen):
            cen = (en[0], tuple(s.find(a) for a in en[1])); r = s.find(seen[en])
            s.hc[cen] = r; s.cl.setdefault(r, set()).add(cen)
    def eq(s, a, b): return s.find(a) == s.find(b)
    def extract(s, eid, memo=None, stk=frozenset()):
        eid = s.find(eid)
        if memo is None: memo = {}
        if eid in memo: return memo[eid]
        if eid in stk: return None
        st = stk | {eid}; best = None
        for en in s.cl.get(eid, ()):
            op = en[0]
            if op.startswith("v:"): c = ("v", int(op[2:]))
            elif op.startswith("f:"): c = ("f", op[2:])
            elif op == "e": c = ("e",)
            elif op == "lam":
                b = s.extract(en[1][0], memo, st); c = ("lam", b) if b else None
            elif op == "app":
                f = s.extract(en[1][0], memo, st); a = s.extract(en[1][1], memo, st)
                c = ("app", f, a) if f and a else None
            elif op.startswith("sup:"):
                l = s.extract(en[1][0], memo, st); r = s.extract(en[1][1], memo, st)
                c = ("sup", int(op[4:]), l, r) if l and r else None
            elif op.startswith("dup:"):
                v = s.extract(en[1][0], memo, st); b = s.extract(en[1][1], memo, st)
                c = ("dup", int(op[4:]), v, b) if v and b else None
            else: c = None
            if c is not None and (best is None or len(repr(c)) < len(repr(best))): best = c
        if best is not None: memo[eid] = best
        return best

# ---- recognizers: church numerals + MULT, by canonical key with labels renumbered
# ---- LOCALLY (an embedded numeral inherits the whole term's label counter, so it
# ---- must be relabeled from 0 to match a standalone numeral's key) ---------------
def relabel(t, lab=None, ln=None):
    if lab is None: lab = {}; ln = [0]
    g = t[0]
    if g in ("v", "f", "e"): return t
    if g == "lam": return ("lam", relabel(t[1], lab, ln))
    if g == "app": return ("app", relabel(t[1], lab, ln), relabel(t[2], lab, ln))
    if g == "sup":
        if t[1] not in lab: lab[t[1]] = ln[0]; ln[0] += 1
        return ("sup", lab[t[1]], relabel(t[2], lab, ln), relabel(t[3], lab, ln))
    if g == "dup":
        if t[1] not in lab: lab[t[1]] = ln[0]; ln[0] += 1
        return ("dup", lab[t[1]], relabel(t[2], lab, ln), relabel(t[3], lab, ln))
MAXN = 16
CHURCH_KEY = {relabel(db(church(k))): k for k in range(MAXN + 1)}
MULT_AST = relabel(db(MULT))
def as_church(ast): return None if ast is None else CHURCH_KEY.get(relabel(ast))

def rule_mult_fold(eg):
    fired = 0
    for eid in list(eg.cl):
        for en in list(eg.cl.get(eid, ())):
            if en[0] == "app":
                xid, bid = en[1]
                bk = as_church(eg.extract(bid))
                if bk is None: continue
                for xen in list(eg.cl.get(eg.find(xid), ())):
                    if xen[0] == "app":
                        mid, aid = xen[1]
                        if relabel(eg.extract(mid) or ("e",)) == MULT_AST:
                            ak = as_church(eg.extract(aid))
                            if ak is not None:
                                cid = eg.add_ast(db(church(ak * bk)))
                                if not eg.eq(cid, eid): eg.merge(cid, eid); fired += 1
    return fired
def saturate(eg, rules, fuel=40):
    tot = 0
    for _ in range(fuel):
        eg.rebuild(); f = sum(r(eg) for r in rules); tot += f
        if f == 0: break
    eg.rebuild(); return tot

# ============================================================ demonstration
print("An interaction-calculus-aware e-graph: rules + congruence over dup-bearing terms.")
print("=" * 78)

# ground truth
nf6, c6, _ = ic_float.run(church(6))
nfm, cm, _ = ic_float.run(mult(2, 3))
print(f"ground truth: NF(church(6)) == NF(mult(2,3))? {nf6 == nfm}   (mult(2,3) reduces in {cm} interactions)")

# IDENTITY: dup/sup binders + labels handled in e-node keys
eg = EGraph()
i6a = eg.add_ast(db(church(6, 1000)))
i6b = eg.add_ast(db(church(6, 9000)))   # same computation, DIFFERENT labels
eg.rebuild()
print(f"\nIDENTITY (the IC-aware part): church(6) on two machines (different labels)")
print(f"   share ONE e-class with NO rules -- de Bruijn over lambda+dup binders + label")
print(f"   renaming: {eg.eq(i6a, i6b)}")

# SEMANTICS: recognize mult(2,3) == church(6) across label namespaces, no reduction
eg = EGraph()
i_mult = eg.add_ast(db(mult(2, 3, 5000)))     # machine X derived mult(2,3)
i_ch6 = eg.add_ast(db(church(6, 1000)))       # machine Y derived church(6) (diff labels)
eg.rebuild()
before = eg.eq(i_mult, i_ch6)
fires = saturate(eg, [rule_mult_fold])
after = eg.eq(i_mult, i_ch6)
print(f"\nSEMANTICS: mult(2,3) [machine X] vs church(6) [machine Y, different labels]")
print(f"   same e-class BEFORE rules : {before}   (different derivations: no)")
print(f"   after church-arith rule   : {after}   in {fires} rewrite-firing(s)")
print(f"   recognized equal in {fires} firing(s) vs {cm} interactions to reduce mult(2,3)")

# a small chain, to show congruence propagating
eg = EGraph()
terms = {"church(6)": church(6, 1), "mult(2,3)": mult(2, 3, 2),
         "mult(3,2)": mult(3, 2, 3), "mult(6,1)": mult(6, 1, 4)}
ids = {k: eg.add_ast(db(v)) for k, v in terms.items()}
eg.rebuild(); f2 = saturate(eg, [rule_mult_fold])
one = len(set(eg.find(i) for i in ids.values())) == 1
print(f"\nfour derivations of 6 (all different labels): one e-class after {f2} firings: {one}")

# soundness: the rule must merge EXACTLY the NF-equal pairs and no others
def _merged(a, b):
    g = EGraph(); ia = g.add_ast(db(a)); ib = g.add_ast(db(b)); g.rebuild()
    saturate(g, [rule_mult_fold]); return g.eq(ia, ib)
def _nfeq(a, b):
    x, _, _ = ic_float.run(a); y, _, _ = ic_float.run(b); return x == y
_probes = [(mult(2, 3, 100), church(6, 200)), (mult(2, 3, 100), church(5, 200)),
           (mult(3, 3, 100), church(9, 200)), (mult(3, 3, 100), church(8, 200)),
           (mult(2, 4, 100), mult(4, 2, 200)), (mult(2, 4, 100), mult(3, 3, 200))]
_sound = all(_merged(a, b) == _nfeq(a, b) for a, b in _probes)
print(f"soundness: across {len(_probes)} probes it merges EXACTLY the NF-equal pairs and no")
print(f"   others (cross-checked against ic_float reduction): {_sound}")

print("\n" + "-" * 78)
print("WHAT THIS SHOWS (and doesn't):")
print(" * The e-graph is IC-AWARE: dup and sup binders (and labels) are handled in e-node")
print("   identity via de Bruijn + label renaming, so the same computation across machines")
print("   collapses for free -- the syntactic congruence idtest measured, now inside the e-graph.")
print(" * A rewrite rule + congruence then recognizes semantic equality (mult(a,b)==church(a*b))")
print("   on the REAL dup-bearing terms, across label namespaces, WITHOUT reducing -- the")
print("   dedup-then-reduce inversion, lifted from pure lambda (incrdt7) onto IC terms.")
print(" * HONEST LIMITS: the rule is the church-arithmetic algebra (domain-specific), and")
print("   church numerals are recognized via a precomputed canonical-key table (sound, but")
print("   finite). The SUBSTITUTION-heavy interaction rules (full IC reduction inside the")
print("   e-graph -- the slotted-e-graph problem) are NOT done here; the algebra rule")
print("   sidesteps substitution. And semantic equivalence in general remains undecidable")
print("   -- this buys exactly what the ruleset spans, the egg bargain, now on IC terms.")
