"""
incrdt7.py -- e-graphs WITH BINDERS: semantic identity on real lambda terms.

incrdt6 recognized semantic equality over a hand-supplied symbolic algebra (Cn, Mul).
The gap: those weren't the real terms. Here the e-graph operates DIRECTLY on lambda
terms in de Bruijn form (so alpha-equivalence is automatic) with the GENERAL rules
beta and eta -- the known-hard "e-graphs with binders" setting.

Tests:
  - de Bruijn beta reducer self-check (ground truth)
  - e-graph congruence self-check
  - alpha-equivalence for free (different names -> same de Bruijn -> same e-class)
  - beta saturation recognizes church(6) == mult(church2,church3) == mult(church3,church2)
  - eta recognizes  (λ. f 0) == f   -- a NON-beta equality reduction alone won't find
  - honest cost: general beta vs reduction (the no-free-lunch point vs incrdt6's algebra)

Run: python3 incrdt7.py
"""

# ----------------------------------------------------------------- de Bruijn lambda
def shift(t, d, c=0):
    k = t[0]
    if k == "var": return ("var", t[1] + d) if t[1] >= c else t
    if k == "lam": return ("lam", shift(t[1], d, c + 1))
    if k == "app": return ("app", shift(t[1], d, c), shift(t[2], d, c))
def subst(t, j, s):
    k = t[0]
    if k == "var": return s if t[1] == j else t
    if k == "lam": return ("lam", subst(t[1], j + 1, shift(s, 1)))
    if k == "app": return ("app", subst(t[1], j, s), subst(t[2], j, s))
def beta_db(body, arg):                       # (λ.body) arg
    return shift(subst(body, 0, shift(arg, 1)), -1)
def uses(t, i):
    k = t[0]
    if k == "var": return t[1] == i
    if k == "lam": return uses(t[1], i + 1)
    if k == "app": return uses(t[1], i) or uses(t[2], i)
def beta_step(t):
    if t[0] == "app":
        if t[1][0] == "lam": return beta_db(t[1][1], t[2]), True
        f, c = beta_step(t[1])
        if c: return ("app", f, t[2]), True
        a, c = beta_step(t[2])
        if c: return ("app", t[1], a), True
        return t, False
    if t[0] == "lam":
        b, c = beta_step(t[1]); return ("lam", b), c
    return t, False
def normalize_db(t, fuel=100000):
    n = 0
    while n < fuel:
        t, c = beta_step(t)
        if not c: return t, n
        n += 1
    return t, n
def tsize(t):
    return 1 if t[0] == "var" else 1 + tsize(t[1]) if t[0] == "lam" else 1 + tsize(t[1]) + tsize(t[2])

# pure-lambda church numerals + multiplication (no dups)
def church(n):
    body = ("var", 0)
    for _ in range(n): body = ("app", ("var", 1), body)
    return ("lam", ("lam", body))
MULT = ("lam", ("lam", ("lam", ("app", ("var", 2), ("app", ("var", 1), ("var", 0))))))
def mult(a, b): return ("app", ("app", MULT, a), b)

# ----------------------------------------------------------------- e-graph (binders)
class EGraph:
    def __init__(s): s.p = {}; s.cl = {}; s.hc = {}; s.n = 0
    def find(s, x):
        while s.p[x] != x: s.p[x] = s.p[s.p[x]]; x = s.p[x]
        return x
    def add(s, op, args=()):
        en = (op, tuple(s.find(a) for a in args))
        if en in s.hc: return s.find(s.hc[en])
        e = s.n; s.n += 1; s.p[e] = e; s.cl[e] = {en}; s.hc[en] = e; return e
    def add_term(s, t):
        if t[0] == "var": return s.add("Var:%d" % t[1])
        if t[0] == "lam": return s.add("Lam", (s.add_term(t[1]),))
        return s.add("App", (s.add_term(t[1]), s.add_term(t[2])))
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
        stk2 = stk | {eid}; best = None
        for en in s.cl.get(eid, ()):
            if en[0].startswith("Var:"): cand = ("var", int(en[0][4:]))
            elif en[0] == "Lam":
                b = s.extract(en[1][0], memo, stk2); cand = ("lam", b) if b else None
            else:
                f = s.extract(en[1][0], memo, stk2); a = s.extract(en[1][1], memo, stk2)
                cand = ("app", f, a) if f and a else None
            if cand and (best is None or tsize(cand) < tsize(best)): best = cand
        if best is not None: memo[eid] = best
        return best

def rule_beta(eg):
    fired = 0
    for eid in list(eg.cl):
        for en in list(eg.cl.get(eid, ())):
            if en[0] == "App":
                l, a = en[1]
                for ln in list(eg.cl.get(eg.find(l), ())):
                    if ln[0] == "Lam":
                        body = eg.extract(ln[1][0]); arg = eg.extract(a)
                        if body is None or arg is None: continue
                        rid = eg.add_term(beta_db(body, arg))
                        if not eg.eq(rid, eid): eg.merge(rid, eid); fired += 1
    return fired
def rule_eta(eg):
    fired = 0
    for eid in list(eg.cl):
        for en in list(eg.cl.get(eid, ())):
            if en[0] == "Lam":
                for bn in list(eg.cl.get(eg.find(en[1][0]), ())):
                    if bn[0] == "App":
                        g, x = bn[1]
                        if eg.extract(x) == ("var", 0):
                            gt = eg.extract(g)
                            if gt and not uses(gt, 0):
                                rid = eg.add_term(shift(gt, -1))
                                if not eg.eq(rid, eid): eg.merge(rid, eid); fired += 1
    return fired
def saturate(eg, rules, fuel=60):
    tot = 0
    for _ in range(fuel):
        eg.rebuild(); f = sum(r(eg) for r in rules); tot += f
        if f == 0: break
    eg.rebuild(); return tot

# ----------------------------------------------------------------- self-tests
nf23, steps23 = normalize_db(mult(church(2), church(3)))
ok_db = (nf23 == church(6))
eg = EGraph()
fa = eg.add_term(("app", ("var", 5), ("var", 0))); fb = eg.add_term(("app", ("var", 5), ("var", 1)))
eg.merge(eg.add_term(("var", 0)), eg.add_term(("var", 1))); eg.rebuild()
ok_cong = eg.eq(fa, fb)
print("de Bruijn beta self-test  (mult(2,3) -> church(6)) :", "PASS" if ok_db else "FAIL")
print("e-graph congruence self-test                       :", "PASS" if ok_cong else "FAIL")
print("=" * 78)

# alpha-equivalence for free: λx.λy.(x y) vs λa.λb.(a b) are the SAME de Bruijn term
t1 = ("lam", ("lam", ("app", ("var", 1), ("var", 0))))   # λx.λy. x y
t2 = ("lam", ("lam", ("app", ("var", 1), ("var", 0))))   # λa.λb. a b  (identical in de Bruijn)
eg = EGraph(); i1 = eg.add_term(t1); i2 = eg.add_term(t2)
print(f"\nalpha-equivalence is FREE: two alpha-variants share one e-class on insert: {eg.eq(i1,i2)}")

# ----------------------------------------------------------------- beta saturation
print("\nSEMANTIC IDENTITY by beta saturation, directly on lambda terms with binders:")
derivs = {"church(6)": church(6), "mult(2,3)": mult(church(2), church(3)),
          "mult(3,2)": mult(church(3), church(2))}
eg = EGraph()
ids = {k: eg.add_term(v) for k, v in derivs.items()}
fires = saturate(eg, [rule_beta])
one = len(set(eg.find(i) for i in ids.values())) == 1
red_total = sum(normalize_db(v)[1] for v in derivs.values())
print(f"   inserted 3 derivations; beta saturation firings: {fires}")
print(f"   all three in ONE e-class (recognized equal): {one}")
print(f"   cost: e-graph {fires} beta-firings  vs  reducing all three = {red_total} beta-steps")

# ----------------------------------------------------------------- eta (non-beta eq)
print("\nETA -- a NON-beta equality (reduction-to-normal-form alone won't find it):")
lam_f0 = ("lam", ("app", ("var", 1), ("var", 0)))   # λ. f 0   (f = free var, index 1)
just_f = ("var", 0)                                  # f        (index 0 outside the λ)
eg = EGraph(); a = eg.add_term(lam_f0); b = eg.add_term(just_f)
before = eg.eq(a, b); saturate(eg, [rule_beta, rule_eta]); after = eg.eq(a, b)
nf_lam, _ = normalize_db(lam_f0)
print(f"   (λ. f 0) is its own beta-normal form: {nf_lam == lam_f0}  (beta gives nothing)")
print(f"   e-graph with eta equates (λ. f 0) == f : before={before}  after={after}")

print("\n" + "-" * 78)
print("READING:")
print(" * The e-graph runs DIRECTLY on lambda terms with binders (de Bruijn), not a")
print("   hand-built algebra -- closing incrdt6's gap. Alpha-equivalence is free.")
print(f" * Beta saturation recognizes the structurally-different derivations as equal,")
print(f"   but at ~reduction cost ({fires} firings vs {red_total} steps): with GENERAL rules,")
print("   semantic recognition costs about as much as reducing. The cheap recognition in")
print("   incrdt6 came from DOMAIN rules (an algebra) -- no free lunch from beta alone.")
print(" * Eta shows the e-graph's genuine edge even here: it equates terms that are each")
print("   already beta-normal -- a non-confluent equality a one-way reducer cannot find,")
print("   because the e-graph keeps ALL equal forms rather than committing to one.")
print("\nSO, on the real terms: structural identity is free (de Bruijn), domain-rule")
print("semantic identity is cheap (incrdt6), general-rule semantic identity costs")
print("reduction (here) but buys non-confluent equalities (eta). The binder problem is")
print("handled by de Bruijn for pure lambda; interaction-calculus dup/sup binders are the")
print("next extension, and substitution-in-e-graphs (slotted e-graphs) is the scaling path.")
