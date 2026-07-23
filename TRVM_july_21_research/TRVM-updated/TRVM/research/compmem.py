"""
compmem.py -- CAPSTONE: a replicated computational memory.

Assembles the whole IN-CRDT thread into one artifact: a content-addressed store of
computations whose MERGE is a confluent CRDT, with two tiers of identity:
  - STRUCTURAL (free, via de Bruijn: alpha-equivalent / relabelled terms collapse)
  - SEMANTIC   (same function, different derivation: collapsed after evaluation by NF;
               or, cheaply, by an algebra of rewrite rules -- see incrdt6)

Demonstrates: two agents with overlapping knowledge merge coordination-free (any
order, idempotent), structurally-shared computation is reduced ONCE not per-agent,
and different derivations of the same fact collapse to one semantic fact.

Run: python3 compmem.py
"""
# ----------------------------------------------------------------- de Bruijn lambda
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
def beta_step(t):
    if t[0] == "app":
        if t[1][0] == "lam": return shift(subst(t[1][1], 0, shift(t[2], 1)), -1), True
        f, c = beta_step(t[1])
        if c: return ("app", f, t[2]), True
        a, c = beta_step(t[2])
        if c: return ("app", t[1], a), True
        return t, False
    if t[0] == "lam":
        b, c = beta_step(t[1]); return ("lam", b), c
    return t, False
def normalize(t, fuel=100000):
    n = 0
    while n < fuel:
        t, c = beta_step(t)
        if not c: return t, n
        n += 1
    return t, n
def is_closed(t, d=0):
    k = t[0]
    if k == "var": return t[1] < d
    if k == "lam": return is_closed(t[1], d + 1)
    return is_closed(t[1], d) and is_closed(t[2], d)
def show(t, d=0):
    k = t[0]
    if k == "var": return chr(97 + d - 1 - t[1]) if 0 <= d - 1 - t[1] < 26 else f"#{t[1]}"
    if k == "lam": return f"λ{chr(97 + d)}.{show(t[1], d + 1)}"
    return f"({show(t[1], d)} {show(t[2], d)})"

def church(n):
    b = ("var", 0)
    for _ in range(n): b = ("app", ("var", 1), b)
    return ("lam", ("lam", b))
MULT = ("lam", ("lam", ("lam", ("app", ("var", 2), ("app", ("var", 1), ("var", 0))))))
def mult(a, b): return ("app", ("app", MULT, a), b)
ID = ("lam", ("var", 0))

# ----------------------------------------------------------------- the store
class Store:
    """Content-addressed computational memory. Entries are de Bruijn terms (so the
       key IS the alpha-canonical computation). Merge is set-union (a CRDT). A shared
       memo means a given computation is reduced at most once across the whole store."""
    def __init__(self, memo=None):
        self.E = {}; self.memo = memo if memo is not None else {}
    def insert(self, t): self.E.setdefault(t, {"nf": None})
    def merge(self, other):
        for t in other.E: self.insert(t)
        return self
    def copy(self):
        n = Store(self.memo); n.E = {t: dict(v) for t, v in self.E.items()}; return n
    def evaluate(self):
        """Reduce each DISTINCT entry to normal form, memoized => shared computation is
           paid for once. Returns beta-steps actually spent."""
        work = 0
        for t in self.E:
            if is_closed(t) and t in self.memo:
                self.E[t]["nf"] = self.memo[t]; continue
            nf, steps = normalize(t); work += steps
            self.E[t]["nf"] = nf
            if is_closed(t): self.memo[t] = nf
        return work
    def semantic_facts(self):
        cls = {}
        for t, v in self.E.items(): cls.setdefault(v["nf"], []).append(t)
        return cls

def agent(*terms):
    s = Store()
    for t in terms: s.insert(t)
    return s

# ============================================================ demonstration
# Two agents. Overlap: both derived mult(2,3) and ID. Agent B also has mult(3,2),
# which is a DIFFERENT derivation of the same value as A's mult(2,3).
A = agent(mult(church(2), church(3)), mult(church(2), church(4)), ID)
B = agent(mult(church(2), church(3)), mult(church(3), church(2)), ID)

print("A replicated computational memory: two agents merge their knowledge.")
print("=" * 78)
print("Agent A entries:")
for t in A.E: print("   ", show(t))
print("Agent B entries:")
for t in B.E: print("   ", show(t))

# ---- merge is a CRDT: commutative, associative, idempotent ----
AB = A.copy().merge(B); BA = B.copy().merge(A)
C = agent(mult(church(4), church(2)), ID)
assoc_l = A.copy().merge(B).merge(C); assoc_r = A.copy().merge(B.copy().merge(C))
print("\nMERGE IS A CRDT (on the content-addressed store):")
print(f"   commutative  A∪B == B∪A           : {set(AB.E) == set(BA.E)}")
print(f"   associative  (A∪B)∪C == A∪(B∪C)   : {set(assoc_l.E) == set(assoc_r.E)}")
print(f"   idempotent   A∪A == A             : {set(A.copy().merge(A).E) == set(A.E)}")

# ---- structural identity is free: dedup on merge ----
raw = len(A.E) + len(B.E)
print(f"\nSTRUCTURAL IDENTITY (free, via de Bruijn):")
print(f"   {raw} raw entries across the two agents -> {len(AB.E)} after merge "
      f"(ID and mult(2,3) collapse: same computation)")

# ---- shared computation is paid for ONCE ----
# naive: each agent evaluates independently (own memo)
A_solo = agent(*A.E); B_solo = agent(*B.E)
naive = A_solo.evaluate() + B_solo.evaluate()
merged = AB.copy(); merged.memo = {}; shared = merged.evaluate()
print(f"\nNO PAYING TWICE (shared reduction):")
print(f"   agents evaluating independently : {naive} beta-steps "
      f"(mult(2,3) reduced in BOTH agents)")
print(f"   merged store evaluating once    : {shared} beta-steps "
      f"(mult(2,3) reduced once) -> saved {naive - shared}")

# ---- semantic identity: different derivations collapse to one fact ----
facts = merged.semantic_facts()
print(f"\nSEMANTIC IDENTITY (same function, different derivation):")
print(f"   {len(merged.E)} structural entries -> {len(facts)} semantic facts")
for nf, ts in facts.items():
    print(f"     {show(nf):20} <= {', '.join(show(t) for t in ts)}")

# ---- coordination-free: merge order doesn't change the facts ----
m1 = A.copy().merge(B); m1.memo = {}; m1.evaluate()
m2 = B.copy().merge(A); m2.memo = {}; m2.evaluate()
print(f"\nCOORDINATION-FREE: same semantic facts regardless of merge order: "
      f"{set(m1.semantic_facts()) == set(m2.semantic_facts())}")

print("\n" + "-" * 78)
print("WHAT THIS IS:")
print(" * A replicated COMPUTATIONAL memory: the merged object is partially-evaluated")
print("   computation, not facts-as-data. Merge is a confluent CRDT (commutative,")
print("   associative, idempotent), so replicas combine with no coordination.")
print(" * Structural identity is free (de Bruijn): alpha-equivalent / relabelled")
print("   computations collapse on insert, and shared work is reduced ONCE, not per agent.")
print(" * Semantic identity (different derivations of the same value) collapses after")
print("   evaluation, by normal form. The remaining inefficiency: mult(3,2) is reduced")
print("   even though it equals mult(2,3) -- they collapse only AFTER reduction.")
print("   Recognizing that BEFORE reducing is exactly the cheap algebra-rule path")
print("   (incrdt6) or the e-graph (incrdt7); plugging it in turns reduce-then-dedup")
print("   into dedup-then-reduce, the last efficiency on the semantic tier.")
print(" * This is the thread's destination as one running artifact: structurally (and,")
print("   with a ruleset, semantically) content-addressed computation with confluent")
print("   merge -- a coordination-free substrate for accumulated agent memory.")
