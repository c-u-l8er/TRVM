"""
tiers.py -- running invariants through the three-tier sort, on the IC substrate.

  tier 1 STRUCTURAL          -- baked into the representation, unviolatable, no check
  tier 2 REDUCTION-CHECKABLE -- not structural, but settled by reducing + inspecting
  tier 3 ORACLE-NEEDED       -- behavioral/semantic; no reduction settles it

Anchors: beta (cost/persistence) -> tier 1 (+ the representation change that gets it there);
NF-equality -> tier 2; termination -> tier 3.

Run: python3 tiers.py
"""
import sys, ic_float
sys.setrecursionlimit(100000)
from incrdt import parse_tree

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
def key(src): return repr(parse_tree(src))          # structural computation-identity
def run(src):
    nf, beta, _ = ic_float.run(src); return nf, beta

print("Running invariants through the tier sort, on the IC substrate.")
print("=" * 78)

# ======================================================== TIER 1: beta is STRUCTURAL
print("\nTIER 1 -- beta (cost / persistence): STRUCTURAL")
print("-" * 78)
nf6, b6 = run(church(6)); nfm, bm = run(mult(2, 3)); _, bm2 = run(mult(2, 3))
print("(a) conservation -- beta is carried OUT of every reduction, not asserted after:")
print(f"    church(6): beta={b6}   mult(2,3): beta={bm}   (mult(2,3) again: beta={bm2}, deterministic)")
print( "    beta is the interaction count the loop increments; no reduction path omits the")
print( "    increment, so beta-conservation is structural -- there is nothing to check.")

def store(*srcs):
    s = {}
    for src in srcs:
        _, b = run(src); s[key(src)] = b
    return s
def merge(a, b):
    m = dict(a); m.update(b); return m              # union; same computation-key idempotent
def beta_total(s): return sum(s.values())           # sum over DISTINCT computations
A = store(church(6), mult(2, 3))
B = store(mult(2, 3), mult(3, 2))                    # mult(2,3) shared across replicas
C = store(mult(3, 3))
print("\n(b) under merge -- beta over a content-addressed store is a G-Counter:")
print( "    replica A did {church(6), mult(2,3)}, B did {mult(2,3), mult(3,2)} (overlap)")
print(f"    commutative {beta_total(merge(A,B)) == beta_total(merge(B,A))}   "
      f"associative {beta_total(merge(merge(A,B),C)) == beta_total(merge(A,merge(B,C)))}   "
      f"idempotent {merge(A,A) == A}")
print(f"    merged beta_total = {beta_total(merge(A,B))}  (mult(2,3) counted ONCE, not twice)")
print( "    => REPRESENTATION CHANGE: beta moves from a predicate asserted after reducing to")
print( "       a maintained count that merges as a counter -- structural, and itself a CRDT.")

# ======================================================== TIER 2: NF-equality
print("\n\nTIER 2 -- NF-equality (same meaning): REDUCTION-CHECKABLE")
print("-" * 78)
struct_eq = key(church(6)) == key(mult(2, 3))
nf_eq = run(church(6))[0] == run(mult(2, 3))[0]
print(f"    church(6) vs mult(2,3):")
print(f"    structural check (representation keys): equal? {struct_eq}   (not visible structurally)")
print(f"    reduction check (compare normal forms): equal? {nf_eq}   (settled by reducing both)")
print(f"    => not structural, not an oracle: REDUCTION settles it, cost = the reduction (~{bm}")
print(f"       interactions). iceg pulled THIS instance to a 1-firing rule, but general")
print(f"       NF-equality stays tier 2 -- and full program equivalence is tier 3.")

# ======================================================== TIER 3: termination
print("\n\nTIER 3 -- termination (does it halt?): ORACLE-NEEDED")
print("-" * 78)
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
def reaches_nf(t, budget):
    for i in range(budget):
        t, c = bstep(t)
        if not c: return True, i
    return False, budget
omega = ("app", ("lam", ("app", ("var", 0), ("var", 0))), ("lam", ("app", ("var", 0), ("var", 0))))
MULTdb = ("lam", ("lam", ("lam", ("app", ("var", 2), ("app", ("var", 1), ("var", 0))))))
halts = ("app", ("app", MULTdb, church_db(2)), church_db(3))   # mult(2,3), terminating
for bud in (5, 20, 100):
    oh, _ = reaches_nf(omega, bud); th, ts = reaches_nf(halts, bud)
    print(f"    budget {bud:>3}:  omega at NF? {oh!s:<5}   mult(2,3) at NF? {th!s:<5}"
          + (f" (halted at {ts})" if th else " (still going)"))
print( "    => bounded reduction certifies halting (YES, when NF is reached) but NEVER")
print( "       non-halting. omega is unsettled at every budget and indistinguishable from")
print( "       'slow but halting' at any finite one. Termination needs an ORACLE; reduction")
print( "       is a semi-decision procedure (halts-yes only). Undecidable in general.")

# ======================================================== summary
print("\n" + "=" * 78)
print("THE SORT:")
print("  invariant      tier  settled by           cost           representation note")
print("  beta (cost)     1    nothing (structural) zero           maintained count + counter merge")
print("  NF-equality     2    reduction            one reduction  some instances -> rule (iceg)")
print("  termination     3    an external oracle   unbounded      reduction = halts-yes only")
print("\n  The engineering move is to push an invariant DOWN a tier. beta reached tier 1 by a")
print("  representation change (carry the count; merge it as a counter). NF-equality cannot")
print("  go structural (idtest), but iceg pulls chosen instances toward cheap rules.")
print("  Termination cannot leave tier 3 -- 'eventually' is not representable.")
print("\n  (kappa, sigma from the periodic table need their definitions to sort; the test for")
print("   each: expressible as 'unrepresentable to violate' [1], 'computable from the normal")
print("   form' [2], or genuinely behavioral [3].)")
