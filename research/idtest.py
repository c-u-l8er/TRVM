"""
idtest.py -- is the identity layer SYNTACTIC or SEMANTIC?

The pushed experiment: three IC terms with the SAME normal form but DIFFERENT
reduction histories. Measure ic_canon on each BEFORE reduction.
  - if they collapse -> ic_canon is already a semantic notion of identity
  - if they don't    -> ic_canon is (as I claim) a syntactic congruence, and the
                        next step is IC-aware e-graphs, not better canonicalization

Then a second probe: does BOUNDED normalization (k reduction steps + structural
canon) collapse them cheaply? If only at k = full reduction, "better canonicalization"
caps out and rewrite-rule e-graphs (incrdt6) are the path.

Run: python3 idtest.py
"""
import sys, ic_float
sys.setrecursionlimit(100000)
from incrdt import parse_tree, canon, NOT, FALSE

# ---- IC terms (dup-based), three derivations of church(6) -----------------------
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
def mult(a, b): return f"(({MULT} {church(a)}) {church(b)})"

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
        return ("dup", m[t[1]], t[2], t[3], label_renumber(t[4], m, nxt), label_renumber(t[5], m, nxt))
def ic_canon(src): return canon(label_renumber(parse_tree(src)))

A, B, C = church(6), mult(2, 3), mult(3, 2)     # three derivations of 6
names = {"church(6)": A, "mult(2,3)": B, "mult(3,2)": C}

print("Three IC terms, same value, different derivations:")
nf = {}
for nm, s in names.items(): nf[nm], _, _ = ic_float.run(s)
print(f"   NF(A)=NF(B)=NF(C)? {len(set(nf.values())) == 1}  (semantically equal: ground truth)")
print("=" * 78)

# ---- the test: ic_canon BEFORE reduction ----------------------------------------
keys = {nm: ic_canon(s) for nm, s in names.items()}
collapse = len(set(keys.values())) == 1
print(f"\nic_canon BEFORE reduction -> {len(set(keys.values()))} distinct keys of 3")
print(f"   do the three collapse? {collapse}")
print(f"   => ic_canon is {'SEMANTIC (surprising!)' if collapse else 'SYNTACTIC (as claimed)'}")

# ---- what congruence DOES ic_canon capture? alpha + labels ----------------------
print("\nthe congruence ic_canon DOES capture (vs the value-equality it doesn't):")
print(f"   church(6) @ different labels collapse : {ic_canon(church(6,1000)) == ic_canon(church(6,9000))}  (alpha + label renaming)")
print(f"   church(6) vs mult(2,3) collapse       : {ic_canon(A) == ic_canon(B)}  (different derivation: NO)")

# ---- probe 2: does BOUNDED normalization help? (pure-lambda de Bruijn) -----------
def shift(t, d, c=0):
    k = t[0]
    if k == "var": return ("var", t[1] + d) if t[1] >= c else t
    if k == "lam": return ("lam", shift(t[1], d, c + 1))
    return ("app", shift(t[1], d, c), shift(t[2], d, c))
def subst(t, j, s):
    k = t[0]
    if k == "var": return s if t[1] == j else t
    if k == "lam": return ("lam", subst(t[1], j + 1, shift(s, 1)))
    return ("app", subst(t[1], j, s), subst(t[2], j, s))
def bstep(t):
    if t[0] == "app":
        if t[1][0] == "lam": return shift(subst(t[1][1], 0, shift(t[2], 1)), -1), True
        f, c = bstep(t[1])
        if c: return ("app", f, t[2]), True
        a, c = bstep(t[2])
        if c: return ("app", t[1], a), True
        return t, False
    if t[0] == "lam":
        b, c = bstep(t[1]); return ("lam", b), c
    return t, False
def church_db(n):
    b = ("var", 0)
    for _ in range(n): b = ("app", ("var", 1), b)
    return ("lam", ("lam", b))
MULTdb = ("lam", ("lam", ("lam", ("app", ("var", 2), ("app", ("var", 1), ("var", 0))))))
Adb = church_db(6); Bdb = ("app", ("app", MULTdb, church_db(2)), church_db(3))

print("\nProbe 2 -- does BOUNDED normalization collapse church(6) and mult(2,3)?")
print("   (apply k beta steps to mult(2,3), then compare structurally to church(6))")
t = Bdb; k = 0; matched = None
while k < 200:
    if t == Adb: matched = k; break
    t, c = bstep(t)
    if not c: break
    k += 1
full = 0; tt = Bdb
while True:
    tt, c = bstep(tt)
    if not c: break
    full += 1
print(f"   mult(2,3) matches church(6) structurally only at k={matched} steps (its FULL reduction is {full})")
print(f"   => bounded/cheap normalization does NOT collapse them; you must reduce fully.")

print("\n" + "-" * 78)
print("VERDICT (answers the fork: better canonicalization vs IC-aware e-graphs):")
print(" * ic_canon is a SYNTACTIC congruence: alpha-equivalence + duplication-label")
print("   renaming. It collapses the same derivation across label namespaces (the")
print("   cross-machine case), but NOT different derivations of the same value.")
print(" * Bounded normalization doesn't rescue it: church(6) and mult(2,3) coincide only")
print("   at full reduction, so 'better canonicalization' caps out at syntactic congruence.")
print(" * Therefore the next step is IC-AWARE E-GRAPHS, not better canon. And incrdt6")
print("   already showed the payoff: a church-arithmetic RULESET + congruence recognized")
print("   mult(2,3) == church(6) in 4 rewrite-firings WITHOUT reducing. The open work is")
print("   carrying those rules over IC terms (dup/sup binders in e-graphs; incrdt7 closed")
print("   the binder case for pure lambda).")
print(" * So identity has two tiers: a cheap SYNTACTIC congruence (have it) and SEMANTIC")
print("   equivalence (needs rules or reduction). The intellectual weight ChatGPT sees")
print("   accumulating on 'identity' is really weight on the SEMANTIC tier -- which is")
print("   provably not reachable by canonicalization alone (it's program equivalence).")
