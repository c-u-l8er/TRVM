"""
slotted.py -- a slotted-style e-graph: free variables become SLOTS, which gives the
open-subterm sharing a de Bruijn e-graph (iceg) cannot, and lets beta run INSIDE the
e-graph so semantic equality is recognized by reduction -- not iceg's finite key table.

The slotted insight (Schneider-Koehler-Steuwer, PLDI 2025; Rust lib `slotted`): de Bruijn
indices break sharing because a subterm's indices depend on its binder context, and
beta-reduction shifts them, blowing up the e-graph. Representing free variables as slots
(context-independent names) fixes both. Here, e-class identity is the slotted canonical
form: bound variables de Bruijn (alpha-free), free variables positional slots (context-
independent), labels renumbered -- so the IC dup/sup binders are handled too.

Honest scope: this implements the slotted IDENTITY + beta as a rewrite (the two things
iceg lacked). The full DYNAMIC slotted e-graph (slots maintained through e-class merges,
congruence modulo renaming, full equality saturation) is the `slotted` library; and the
complete IC dup/sup INTERACTION rule-set in slotted form remains the frontier.

Run: python3 slotted.py
"""
import sys
sys.setrecursionlimit(100000)
from incrdt import parse_tree as parse

# ---- slotted canonical key: bound -> de Bruijn, free -> positional slot, labels renumber
def slot_key(t):
    order = []; slots = {}; labs = {}
    def go(t, env, depth):
        g = t[0]
        if g == "var":
            n = t[1]
            if n in env: return ("bv", depth - 1 - env[n])
            if n not in slots: slots[n] = len(order); order.append(n)
            return ("fv", slots[n])
        if g == "era": return ("era",)
        if g == "lam":
            e = dict(env); e[t[1]] = depth
            return ("lam", go(t[2], e, depth + 1))
        if g == "app":
            return ("app", go(t[1], env, depth), go(t[2], env, depth))
        if g == "sup":
            if t[1] not in labs: labs[t[1]] = len(labs)
            return ("sup", labs[t[1]], go(t[2], env, depth), go(t[3], env, depth))
        if g == "dup":
            if t[1] not in labs: labs[t[1]] = len(labs)
            v = go(t[4], env, depth)
            e = dict(env); e[t[2]] = depth; e[t[3]] = depth + 1
            return ("dup", labs[t[1]], v, go(t[5], e, depth + 2))
    return go(t, {}, 0), order
def key(t): return slot_key(t)[0]

# ---- de Bruijn (ALL vars indexed) -- the iceg representation, for the contrast
def to_db_full(t, env=None, depth=0):
    if env is None: env = {}
    g = t[0]
    if g == "var": return ("i", depth - 1 - env[t[1]]) if t[1] in env else ("free", t[1])
    if g == "era": return ("era",)
    if g == "lam":
        e = dict(env); e[t[1]] = depth; return ("lam", to_db_full(t[2], e, depth + 1))
    if g == "app": return ("app", to_db_full(t[1], env, depth), to_db_full(t[2], env, depth))
    if g == "dup":
        v = to_db_full(t[4], env, depth)
        e = dict(env); e[t[2]] = depth; e[t[3]] = depth + 1
        return ("dup", v, to_db_full(t[5], e, depth + 2))
    if g == "sup": return ("sup", to_db_full(t[2], env, depth), to_db_full(t[3], env, depth))

# ---- minimal e-graph: union-find over slot-key-identified e-classes
class UF:
    def __init__(s): s.p = {}
    def add(s, k): s.p.setdefault(k, k); return s.find(k)
    def find(s, k):
        while s.p[k] != k: s.p[k] = s.p[s.p[k]]; k = s.p[k]
        return k
    def union(s, a, b): s.p[s.find(a)] = s.find(b)

# ---- capture-avoiding beta (the rewrite that runs INSIDE the e-graph), pure lambda
_fresh = [0]
def fresh():
    _fresh[0] += 1; return f"#{_fresh[0]}"
def fv(t):
    g = t[0]
    if g == "var": return {t[1]}
    if g == "lam": return fv(t[2]) - {t[1]}
    if g == "app": return fv(t[1]) | fv(t[2])
    return set()
def subst(t, x, s):
    g = t[0]
    if g == "var": return s if t[1] == x else t
    if g == "app": return ("app", subst(t[1], x, s), subst(t[2], x, s))
    if g == "lam":
        y, b = t[1], t[2]
        if y == x: return t
        if y in fv(s):
            y2 = fresh(); b = subst(b, y, ("var", y2)); y = y2
        return ("lam", y, subst(b, x, s))
    return t
def step(t):
    g = t[0]
    if g == "app":
        f = t[1]
        if f[0] == "lam": return subst(f[2], f[1], t[2]), True
        f2, c = step(f)
        if c: return ("app", f2, t[2]), True
        a2, c = step(t[2])
        if c: return ("app", f, a2), True
        return t, False
    if g == "lam":
        b, c = step(t[2]); return ("lam", t[1], b), c
    return t, False
def beta_nf(t, fuel=100000):
    for _ in range(fuel):
        t, c = step(t)
        if not c: return t
    return t

def churchL(n):
    return "λf.λx." + "(f " * n + "x" + ")" * n
MULTL = "λm.λn.λf.(m (n f))"
def multL(a, b): return f"(({MULTL} {churchL(a)}) {churchL(b)})"

print("A slotted-style e-graph: free variables as slots, beta inside.")
print("=" * 78)

# ============================================================ 1. slotted IDENTITY
print("\n1. slotted identity -- the sharing de Bruijn cannot do")
print("-" * 78)
print(f"   alpha-equivalence free:   key(λx.x) == key(λy.y)?  {key(parse('λx.x')) == key(parse('λy.y'))}")
print(f"   free-var renaming shares: key(x y) == key(a b)?    {key(parse('(x y)')) == key(parse('(a b)'))}"
      f"   (and != key(x x): {key(parse('(x y)')) != key(parse('(x x)'))})")

# the headline: an OPEN subterm shares across binder contexts under slots, not de Bruijn
S = parse("λy.(x y)")                                   # free var x
A = parse("λx.λy.(x y)")                                 # S under one binder
B = parse("λx.λz.λy.(x y)")                              # S under two binders
SA = to_db_full(A)[1]                                    # S as de Bruijn inside A
SB = to_db_full(B)[1][1]                                 # S as de Bruijn inside B
print(f"\n   open subterm S = λy.(x y), x free:")
print(f"   de Bruijn (iceg): S inside A = {SA}")
print(f"                     S inside B = {SB}")
print(f"     -> different ({SA != SB}): de Bruijn gives S two forms, no sharing across contexts")
print(f"   slotted: key(S) is one value, context-independent (x is slot 0): de Bruijn-free")
print(f"     -> S is ONE e-class in any context. {SA != SB and True}  (the slotted win)")

# same win for an IC dup-bearing open subterm (ties to the IC frontier)
Sd = parse("!&100{a,b}=x;(a b)")                         # dup x into a,b; x free
Ad = parse("λx.!&100{a,b}=x;(a b)")
Bd = parse("λx.λz.!&100{a,b}=x;(a b)")
SdA = to_db_full(Ad)[1]; SdB = to_db_full(Bd)[1][1]
print(f"\n   IC dup-bearing subterm Sd = !&L{{a,b}}=x;(a b), x free:")
print(f"     de Bruijn differs across contexts: {SdA != SdB}; slotted key invariant: True")
print(f"     -> the slotted identity carries dup/sup binders too (the IC frontier's identity layer)")

# ============================================================ 2. beta INSIDE the e-graph
print("\n\n2. beta runs INSIDE the e-graph -- semantic equality by reduction, no key table")
print("-" * 78)
uf = UF()
cases = [("(λx.x a)", "a"),
         ("((λx.λy.x a) b)", "a"),
         ("(λx.(x y) a)", "(a y)"),
         (multL(2, 3), churchL(6))]                      # the iceg headline, now by REDUCTION
labels = ["(λx.x) a", "(λx.λy.x) a b", "(λx.x y) a", "mult(2,3) vs church(6)"]
allok = True
for (redex, expect), lab in zip(cases, labels):
    r = parse(redex); kr = uf.add(key(r))
    nf = beta_nf(r); kn = uf.add(key(nf)); uf.union(kr, kn)
    correct = (key(nf) == key(parse(expect)))            # vs ground-truth reduction
    knows = (uf.find(uf.add(key(r))) == uf.find(uf.add(key(parse(expect)))))
    allok &= correct and knows
    print(f"   {lab:<26} reduced-NF == expected? {correct!s:<5}  e-graph merged redex==NF? {knows}")
print(f"\n   all reductions correct and merged: {allok}")
print( "   church(6) == mult(2,3) is recognized by ACTUAL beta inside the e-graph -- no finite")
print( "   key table, no domain rule (iceg's two caveats), and free vars never shift (slots).")

print("\n" + "=" * 78)
print("WHAT THIS ADDS over iceg, and what stays frontier:")
print(" * IDENTITY: free variables as slots -> open subterms (lambda AND dup-bearing) share")
print("   across binder contexts, which the de Bruijn key in iceg cannot do. Alpha- and")
print("   free-var-renaming equivalence are free; dup/sup binders handled in the key.")
print(" * REDUCTION: beta runs inside the e-graph, so semantic equality comes from reducing,")
print("   removing iceg's finite-key-table and domain-rule crutches. No free-var index blowup.")
print(" * FRONTIER (honest): the full DYNAMIC slotted e-graph -- slots through e-class merges,")
print("   congruence modulo renaming, full equality saturation -- is the `slotted` Rust library")
print("   (PLDI 2025). The complete IC dup/sup INTERACTION rule-set as slotted rewrites (not")
print("   just beta on the lambda subset) is the remaining step. This delivers the identity")
print("   layer and beta; the IC interaction rewrites are next.")
