"""
compmem_ic.py -- the computational memory ON THE REAL interaction-calculus runtime.

compmem.py used pure lambda + a toy beta reducer (no sharing). This runs the SAME
content-addressed-store-with-confluent-merge design on the actual dup-based IC terms,
evaluated by ic_float (the real floating-duplication reducer). Two things become real:

  - IDENTITY over dup-bearing terms: the canonical key handles BOTH lambda and dup
    binders (de Bruijn) AND duplication labels (alpha-rename labels), so the SAME
    computation derived on two machines with DIFFERENT labels collapses. (This is the
    incrdt4 result, now used as the store's key.)
  - EVALUATION with the runtime's own sharing: ic_float reduces via duplication nodes,
    so work shared WITHIN a computation is done once, on top of the store's
    cross-computation dedup.

Run: python3 compmem_ic.py
"""
import sys, ic_float
sys.setrecursionlimit(100000)
from incrdt import parse_tree, canon, NOT, FALSE, TRUE

# ----------------------------------------------------------------- IC terms (with dups)
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
def notn(n, base=1000): return f"(({church(n, base)} {NOT}) {FALSE})"

# ----------------------------------------------------------------- canonical key (binders + labels)
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
def ic_canon(src):
    """structural identity for IC terms: de Bruijn over lambda AND dup binders,
       plus alpha-renaming of duplication labels."""
    return canon(label_renumber(parse_tree(src)))

# ----------------------------------------------------------------- the store (on ic_float)
class Store:
    def __init__(self, memo=None):
        self.E = {}; self.memo = memo if memo is not None else {}   # key=ic_canon -> {src, nf, cost}
    def insert(self, src):
        self.E.setdefault(ic_canon(src), {"src": src, "nf": None, "cost": 0})
    def merge(self, other):
        for k, v in other.E.items(): self.E.setdefault(k, dict(v))
        return self
    def copy(self):
        n = Store(self.memo); n.E = {k: dict(v) for k, v in self.E.items()}; return n
    def evaluate(self):
        work = 0
        for k, v in self.E.items():
            if k in self.memo:
                v["nf"], v["cost"] = self.memo[k]; continue
            nf, tot, _ = ic_float.run(v["src"]); v["nf"], v["cost"] = nf, tot
            self.memo[k] = (nf, tot); work += tot
        return work
    def facts(self):
        c = {}
        for v in self.E.values(): c.setdefault(v["nf"], []).append(v["src"])
        return c

def agent(*srcs):
    s = Store()
    for x in srcs: s.insert(x)
    return s

# ============================================================ self-test
nf6, _, _ = ic_float.run(church(6))
nf_m23, _, _ = ic_float.run(mult(2, 3))
print("ic_float reduces dup-based mult(2,3) -> church(6):", "PASS" if nf_m23 == nf6 else "FAIL")
# identity across DIFFERENT labels: same computation, two machines
print("ic_canon collapses church(6) built with different labels:",
      ic_canon(church(6, 1000)) == ic_canon(church(6, 7000)))
print("ic_canon collapses mult(2,3) built with different labels:",
      ic_canon(mult(2, 3, 1000)) == ic_canon(mult(2, 3, 7000)))
print("=" * 78)

# ============================================================ demonstration
# Two agents, DIFFERENT label bases (independent machines). Overlap: both derived
# mult(2,3) and NOT^8(FALSE). B also has mult(3,2) -- same value, different derivation.
A = agent(mult(2, 3, 1000), mult(2, 4, 1000), notn(8, 1000))
B = agent(mult(2, 3, 5000), mult(3, 2, 5000), notn(8, 5000))

print("Two agents (independent label namespaces) merge their IC computations.")
AB = A.copy().merge(B); BA = B.copy().merge(A)
C = agent(mult(4, 2, 9000), notn(8, 9000))
asl = A.copy().merge(B).merge(C); asr = A.copy().merge(B.copy().merge(C))
print("\nMERGE IS A CRDT (over dup-bearing IC terms, keyed by ic_canon):")
print(f"   commutative : {set(AB.E) == set(BA.E)}")
print(f"   associative : {set(asl.E) == set(asr.E)}")
print(f"   idempotent  : {set(A.copy().merge(A).E) == set(A.E)}")

raw = len(A.E) + len(B.E)
print(f"\nSTRUCTURAL IDENTITY across machines (different labels collapse):")
print(f"   {raw} raw entries -> {len(AB.E)} after merge  "
      f"(mult(2,3) and NOT^8 collapse despite different labels)")

# shared computation reduced once across agents
A1, B1 = agent(*[v['src'] for v in A.E.values()]), agent(*[v['src'] for v in B.E.values()])
naive = A1.evaluate() + B1.evaluate()
merged = AB.copy(); merged.memo = {}; shared = merged.evaluate()
print(f"\nNO PAYING TWICE (real ic_float interactions):")
print(f"   agents evaluating independently : {naive} interactions")
print(f"   merged store evaluating once    : {shared} interactions  -> saved {naive - shared}")

facts = merged.facts()
print(f"\nSEMANTIC IDENTITY (same value, different derivation):")
print(f"   {len(merged.E)} structural entries -> {len(facts)} semantic facts")
for nf, ss in sorted(facts.items(), key=lambda kv: len(kv[1]), reverse=True):
    print(f"     {nf[:24]:24} <= {len(ss)} derivation(s)")

m1 = A.copy().merge(B); m1.memo = {}; m1.evaluate()
m2 = B.copy().merge(A); m2.memo = {}; m2.evaluate()
print(f"\nCOORDINATION-FREE: same facts regardless of merge order: "
      f"{set(m1.facts()) == set(m2.facts())}")

# ---- within-computation sharing: the runtime's own dup-sharing -------------------
print("\n" + "-" * 78)
print("WITHIN-COMPUTATION SHARING (the runtime's dups, which pure-lambda compmem lacks):")
# reuse a sub-result twice: shared via dup vs spelled out twice
SUB = f"({church(5)} {NOT})"           # NOT^5, used twice
unshared = f"R ({SUB} {FALSE}) ({SUB} {TRUE})"
unshared = f"((R ({SUB} {FALSE})) ({SUB} {TRUE}))"
shared = f"!&9{{s0,s1}}={SUB}; ((R (s0 {FALSE})) (s1 {TRUE}))"
_, u, _ = ic_float.run(unshared); _, s, _ = ic_float.run(shared)
print(f"   reusing NOT^5 twice: spelled out {u} interactions  vs  shared-via-dup {s}"
      + (f"  ({u/s:.2f}x)" if s else ""))

# ---- evaluator swapped to the native runtime ic32: dramatic optimal sharing ------
import os, subprocess, tempfile
_IC32 = [None]
def _build_ic32():
    if _IC32[0]: return _IC32[0]
    if not os.path.exists("ic32.c"): return None
    out = os.path.join(tempfile.gettempdir(), "ic32_compmem")
    try:
        r = subprocess.run(["gcc", "-O2", "-o", out, "ic32.c"], capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(out):
            os.chmod(out, 0o755); _IC32[0] = out; return out
    except Exception:
        pass
    return None
def ic32(term):
    b = _build_ic32()
    if not b: return None
    r = subprocess.run([b, "-v"], input=term, capture_output=True, text=True)
    it = next((int(x.split("=")[1]) for x in r.stderr.split() if x.startswith("interactions=")), -1)
    return r.stdout.strip(), it
def parity2(N, base): return f"((({church(N, base)} {church(2, base)}) {NOT}) {FALSE})"

print("\n" + "=" * 78)
print("EVALUATOR = ic32 (native runtime): the memory inherits DRAMATIC optimal sharing")
pa, pb = parity2(24, 1000), parity2(24, 5000)   # two machines derive parity of 2^24
res = None
try: res = ic32(pa)
except Exception: res = None
if res:
    nf, cost = res
    print(f"   an entry: parity of 2^24  (value = {2**24:,} applications)")
    print(f"   same computation on two machines, different labels -> ic_canon collapses: {ic_canon(pa) == ic_canon(pb)}")
    print(f"   stored once, reduced once via ic32: NF={nf}  cost={cost} interactions")
    print(f"   both agents reducing independently: {2*cost}   merged store: {cost}  (saved {cost})")
    print(f"   => astronomical VALUE ({2**24:,}) at {cost} interactions, and overlapping")
    print(f"      knowledge across machines reduced ONCE: two-level sharing on the real runtime.")
else:
    print("   (native ic32 unavailable here -- build with: gcc -O2 -o ic32 ic32.c)")
    print(f"   ic_canon collapses the two machines' derivations: {ic_canon(pa) == ic_canon(pb)}")
    print("   Reference (ic32): parity of 2^24 = 16,777,216 applications -> 478 interactions;")
    print("   merged store reduces it once (478) not twice (956). Astronomical value, linear cost.")

print("\n" + "-" * 78)
print("WHAT'S NEW vs compmem.py:")
print(" * The store now runs on the REAL dup-based IC terms, evaluated by ic_float --")
print("   not pure lambda. Identity handles dup binders AND labels, so the same")
print("   computation derived on machines with different labels collapses (incrdt4 key).")
print(" * Two levels of sharing now compose: CROSS-computation (the store's CRDT dedup,")
print("   shared work reduced once) and WITHIN-computation (the runtime's dups).")
print(" * HONEST: ic_float (Python) hits recursion limits on some higher-order cases, so")
print("   the DRAMATIC optimal sharing (parity of 2^24 in ~478 interactions) needs the C")
print("   runtime ic32 -- now wired in above as the evaluator. SEMANTIC identity here is")
print("   still reduce-then-dedup; an interaction-rule e-graph over IC terms (dup/sup")
print("   binders in e-graphs) remains the open frontier.")
