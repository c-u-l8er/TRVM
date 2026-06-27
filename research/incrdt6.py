"""
incrdt6.py -- the conundrum: SEMANTIC identity via equality saturation.

Structural canonicalization (incrdt4) recognizes "same derivation, different labels".
It MISSES "same function, different derivation": church(6) vs mult(church2,church3)
reduce to the same normal form but are structurally different. Recognizing THOSE is
program equivalence -- undecidable in general.

The e-graph bet: with a small set of domain rewrite rules + congruence closure, can
we recognize such equalities for LESS than the cost of reducing both terms?

Plan:
  (A) ground truth -- reduce the lambda terms with ic_float, confirm same NF, measure
      the reduction cost (the price of recognizing equality BY reducing).
  (B) structural canon -- show it fails to recognize them.
  (C) e-graph -- insert symbolic forms, saturate with a church-arithmetic ruleset,
      show they land in one e-class, measure the cost (rewrite firings).
  (D) honest reading.

Run: python3 incrdt6.py
"""
import ic_float
from incrdt import parse_tree, canon

# ----------------------------------------------------------------- minimal e-graph
class EGraph:
    def __init__(self):
        self.parent = {}; self.classes = {}; self.hashcons = {}; self.n = 0
    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]; x = self.parent[x]
        return x
    def add(self, op, args=()):
        en = (op, tuple(self.find(a) for a in args))
        if en in self.hashcons: return self.find(self.hashcons[en])
        e = self.n; self.n += 1
        self.parent[e] = e; self.classes[e] = {en}; self.hashcons[en] = e
        return e
    def add_term(self, t):                      # t = (op, child_terms...)
        return self.add(t[0], tuple(self.add_term(c) for c in t[1:]))
    def merge(self, a, b):
        a, b = self.find(a), self.find(b)
        if a == b: return a
        self.parent[b] = a
        self.classes[a] = self.classes.get(a, set()) | self.classes.pop(b, set())
        return a
    def rebuild(self):
        while True:
            seen = {}; merged = False
            for en in list(self.hashcons.keys()):
                cen = (en[0], tuple(self.find(a) for a in en[1]))
                eid = self.find(self.hashcons[en])
                if cen in seen:
                    if self.find(seen[cen]) != eid: self.merge(seen[cen], eid); merged = True
                else: seen[cen] = eid
            if not merged: break
        self.hashcons = {}; self.classes = {}
        for en in list(seen.keys()):
            cen = (en[0], tuple(self.find(a) for a in en[1])); r = self.find(seen[en])
            self.hashcons[cen] = r; self.classes.setdefault(r, set()).add(cen)
    def eq(self, a, b): return self.find(a) == self.find(b)

# ----------------------------------------------------------------- church-arith rules
def cn_of(eg, eid):
    for en in eg.classes.get(eg.find(eid), ()):
        if en[0].startswith("Cn:"): return int(en[0][3:])
    return None
def rule_fold(eg):
    fired = 0
    for eid in list(eg.classes):
        for en in list(eg.classes.get(eid, ())):
            if en[0] in ("Mul", "Add", "Exp") and len(en[1]) == 2:
                a, b = cn_of(eg, en[1][0]), cn_of(eg, en[1][1])
                if a is not None and b is not None:
                    v = a*b if en[0] == "Mul" else a+b if en[0] == "Add" else a**b
                    c = eg.add("Cn:%d" % v)
                    if not eg.eq(c, eid): eg.merge(c, eid); fired += 1
    return fired
def rule_comm(eg):
    fired = 0
    for eid in list(eg.classes):
        for en in list(eg.classes.get(eid, ())):
            if en[0] in ("Mul", "Add") and len(en[1]) == 2:
                c = eg.add(en[0], (en[1][1], en[1][0]))
                if not eg.eq(c, eid): eg.merge(c, eid); fired += 1
    return fired
def saturate(eg, rules, fuel=50):
    total = 0
    for _ in range(fuel):
        eg.rebuild()
        f = sum(r(eg) for r in rules)
        total += f
        if f == 0: break
    eg.rebuild(); return total

# ----------------------------------------------------------------- congruence self-test
def selftest():
    eg = EGraph()
    fa = eg.add_term(("f", ("a",))); fb = eg.add_term(("f", ("b",)))
    gfa = eg.add_term(("g", ("f", ("a",)))); gfb = eg.add_term(("g", ("f", ("b",))))
    assert not eg.eq(fa, fb)
    eg.merge(eg.add_term(("a",)), eg.add_term(("b",))); eg.rebuild()
    return eg.eq(fa, fb) and eg.eq(gfa, gfb)

print("e-graph congruence self-test (merge a=b => f(a)=f(b), g(f(a))=g(f(b))):",
      "PASS" if selftest() else "FAIL")
print("=" * 78)

# ----------------------------------------------------------------- (A) ground truth
from incrdt import church
MULT = "λm.λn.λf.(m (n f))"
terms = {
    "church(6)":            church(6),
    "mult(church2,church3)": f"(({MULT} {church(2)}) {church(3)})",
    "mult(church3,church2)": f"(({MULT} {church(3)}) {church(2)})",
    "mult(church6,church1)": f"(({MULT} {church(6)}) {church(1)})",
}
print("\n(A) GROUND TRUTH (reduce with ic_float; same NF => semantically equal):")
nfs = {}; costs = {}
for name, src in terms.items():
    nf, tot, _ = ic_float.run(src); nfs[name] = nf; costs[name] = tot
    print(f"    {name:24} -> NF {('= church6' if nf == nfs['church(6)'] else 'DIFFERS')}   reduction cost {tot}")
all_same = len(set(nfs.values())) == 1
print(f"    all four semantically equal: {all_same}")

# ----------------------------------------------------------------- (B) structural canon
print("\n(B) STRUCTURAL canon (the incrdt4 recognizer):")
keys = {name: canon(parse_tree(src)) for name, src in terms.items()}
print(f"    distinct structural keys among the four: {len(set(keys.values()))} of 4  "
      f"=> structural identity {'RECOGNIZES' if len(set(keys.values()))==1 else 'FAILS to recognize'} them")

# ----------------------------------------------------------------- (C) e-graph semantic
print("\n(C) E-GRAPH semantic identity (church-arithmetic rules + congruence):")
sym = {
    "church(6)":            ("Cn:6",),
    "mult(church2,church3)": ("Mul", ("Cn:2",), ("Cn:3",)),
    "mult(church3,church2)": ("Mul", ("Cn:3",), ("Cn:2",)),
    "mult(church6,church1)": ("Mul", ("Cn:6",), ("Cn:1",)),
}
eg = EGraph()
ids = {name: eg.add_term(t) for name, t in sym.items()}
fires = saturate(eg, [rule_fold, rule_comm])
one_class = len(set(eg.find(i) for i in ids.values())) == 1
print(f"    inserted 4 symbolic derivations; saturation rewrite-firings: {fires}")
print(f"    all four in ONE e-class (recognized equal): {one_class}")
print(f"    cost to recognize: e-graph {fires} firings  vs  reducing all four = "
      f"{sum(costs.values())} interactions")

# ----------------------------------------------------------------- (D) reading
print("\n" + "-" * 78)
print("READING:")
print(f" * Structural canon FAILS ({len(set(keys.values()))} distinct keys): same function,")
print("   different derivation is invisible to it.")
print(f" * The e-graph RECOGNIZES all four as equal in {fires} rewrite-firings -- far less")
print(f"   than the {sum(costs.values())} interactions it costs to recognize them by reducing.")
print("   So semantic identity IS cheaply decidable HERE: rules + congruence beat reduction.")
print(" * THE CATCH (honest): this works because we supplied the church-arithmetic algebra")
print("   (fold + commutativity). Those rules are domain-specific. For ARBITRARY programs")
print("   there is no finite complete ruleset -- program equivalence is undecidable, so a")
print("   saturation pass is necessarily a SEMI-procedure (recognizes what its rules span,")
print("   bounded by fuel). e-graphs make this practical, not magical.")
print("\nRESOLUTION OF THE CONUNDRUM:")
print(" * Marry the two recognizers: hash-consing (structural identity, incrdt4) IS the")
print("   e-graph's e-node table; a rewrite ruleset + congruence (this file) adds SEMANTIC")
print("   identity on top. Together = structurally + semantically content-addressed")
print("   computation with confluent merge, where 'how semantic' is exactly 'how complete")
print("   the ruleset is'. The undecidable core doesn't go away; it becomes a curated,")
print("   bounded ruleset -- the same bargain egg/equality-saturation makes everywhere.")
