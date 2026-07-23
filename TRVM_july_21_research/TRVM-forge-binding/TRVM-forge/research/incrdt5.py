"""
incrdt5.py -- does canonicalization SCALE? (the pushed experiment)

Measure, as the computation size M grows: the cost to CANONICALIZE replicas vs the
cost to REDUCE them, and the work recovered. Find where the curves cross.

IMPORTANT framing: this measures STRUCTURAL identity (same derivation, different
labels) -- a linear pass in principle. It does NOT measure SEMANTIC identity (same
function, different derivation), which is undecidable and is what e-graphs approximate.
So a "canon stays cheap" result confirms the easy tier only.

Run: python3 incrdt5.py
"""
import ic_float, time
from incrdt import parse_tree, canon, NOT, FALSE

def church(n, base):
    if n == 0: return "λf.λx.x"
    if n == 1: return "λf.λx.(f x)"
    cs = [f"c{i}" for i in range(n)]; src = []; cur = "f"
    for i in range(n-1):
        L = base + n*1000 + i; nxt = f"t{i}" if i < n-2 else cs[-1]
        src.append(f"!&{L}{{{cs[i]},{nxt}}}={cur};"); cur = nxt
    body = "x"
    for c in reversed(cs): body = f"({c} {body})"
    return "λf.λx." + "".join(src) + body

def label_renumber(t, m=None, nxt=None):
    if m is None: m = {}; nxt = [0]
    tag = t[0]
    if tag in ("var", "era"): return t
    if tag == "lam": return ("lam", t[1], label_renumber(t[2], m, nxt))
    if tag == "app": return ("app", label_renumber(t[1], m, nxt), label_renumber(t[2], m, nxt))
    if tag == "sup":
        if t[1] not in m: m[t[1]] = nxt[0]; nxt[0] += 1
        return ("sup", m[t[1]], label_renumber(t[2], m, nxt), label_renumber(t[3], m, nxt))
    if tag == "dup":
        if t[1] not in m: m[t[1]] = nxt[0]; nxt[0] += 1
        return ("dup", m[t[1]], t[2], t[3], label_renumber(t[4], m, nxt), label_renumber(t[5], m, nxt))
def canon_canonical(t): return canon(label_renumber(t))

# --- minimal closed-subterm sharing (canonical), to build the shared net ------
def free_vars(t, b=frozenset()):
    g = t[0]
    if g == "var": return set() if t[1] in b else {t[1]}
    if g == "era": return set()
    if g == "lam": return free_vars(t[2], b | {t[1]})
    if g == "app": return free_vars(t[1], b) | free_vars(t[2], b)
    if g == "sup": return free_vars(t[2], b) | free_vars(t[3], b)
    if g == "dup": return free_vars(t[4], b) | free_vars(t[5], b | {t[2], t[3]})
    return set()
def size(t):
    g = t[0]
    if g in ("var", "era"): return 1
    if g == "lam": return 1 + size(t[2])
    if g == "app": return 1 + size(t[1]) + size(t[2])
    if g == "sup": return 1 + size(t[2]) + size(t[3])
    if g == "dup": return 1 + size(t[4]) + size(t[5])
def render(t):
    g = t[0]
    if g == "var": return t[1]
    if g == "era": return "*"
    if g == "lam": return f"λ{t[1]}.{render(t[2])}"
    if g == "app": return f"({render(t[1])} {render(t[2])})"
    if g == "sup": return f"&{t[1]}{{{render(t[2])},{render(t[3])}}}"
    if g == "dup": return f"!&{t[1]}{{{t[2]},{t[3]}}}={render(t[4])};{render(t[5])}"
def auto_share_canonical(sources):
    trees = [parse_tree(s) for s in sources]
    counts, reps = {}, {}
    def collect(t):
        if not free_vars(t) and size(t) >= 3:
            k = canon_canonical(t); counts[k] = counts.get(k, 0) + 1; reps[k] = t
        g = t[0]
        if g == "lam": collect(t[2])
        elif g == "app": collect(t[1]); collect(t[2])
        elif g == "sup": collect(t[2]); collect(t[3])
        elif g == "dup": collect(t[4]); collect(t[5])
    for t in trees: collect(t)
    cands = [(k, c) for k, c in counts.items() if c >= 2]
    if not cands:
        b = "R"
        for s in sources: b = f"({b} {s})"
        return b
    key = max(cands, key=lambda kc: size(reps[kc[0]]) * (kc[1] - 1))[0]
    ctr = [0]
    def repl(t):
        if canon_canonical(t) == key:
            v = ("var", f"__p{ctr[0]}"); ctr[0] += 1; return v
        g = t[0]
        if g == "lam": return ("lam", t[1], repl(t[2]))
        if g == "app": return ("app", repl(t[1]), repl(t[2]))
        if g == "sup": return ("sup", t[1], repl(t[2]), repl(t[3]))
        if g == "dup": return ("dup", t[1], t[2], t[3], repl(t[4]), repl(t[5]))
        return t
    nt = [repl(t) for t in trees]; K = counts[key]; val = render(reps[key])
    parts = []; cur = val
    for i in range(K-1):
        a = f"__p{i}"; bb = f"__p{K-1}" if i == K-2 else f"__t{i}"
        parts.append(f"!&{500+i}{{{a},{bb}}}={cur};"); cur = bb
    b = "R"
    for t in nt: b = f"({b} {render(t)})"
    return "".join(parts) + b

def time_it(f, reps=3):
    best = 1e9
    for _ in range(reps):
        t0 = time.perf_counter(); f(); best = min(best, time.perf_counter() - t0)
    return best

# ============================================================ scaling in M
N = 4
print("Does canonicalization scale?  N=4 replicas of NOT^M(FALSE), different labels.")
print("Measured: canon (recognition) vs reduction (the shared work).  [ms]")
print("=" * 78)
print(f"{'M':>5}{'termsize':>10}{'canon_ms':>11}{'shared_red_ms':>15}{'unshared_red_ms':>17}{'canon/red':>11}")
for M in (8, 16, 32, 64, 128):
    src = [f"(({church(M, 1000*(k+1))} {NOT}) {FALSE})" for k in range(N)]
    trees = [parse_tree(s) for s in src]
    ts = size(trees[0])
    canon_ms = time_it(lambda: [canon_canonical(t) for t in trees]) * 1e3
    shared = auto_share_canonical(src)
    red_ms = time_it(lambda: ic_float.run(shared)) * 1e3
    b = "R"
    for s in src: b = f"({b} {s})"
    un_ms = time_it(lambda: ic_float.run(b)) * 1e3
    print(f"{M:>5}{ts:>10}{canon_ms:>11.2f}{red_ms:>15.2f}{un_ms:>17.2f}{canon_ms/red_ms:>11.2f}")

print("\n" + "-" * 78)
print("READING:")
print(" * The honest result: with this NAIVE canon (recomputed per subterm, O(n^2)")
print("   string building), canon cost grows fast and can overtake reduction for large M.")
print("   That is an IMPLEMENTATION artifact, not a fundamental one: structural")
print("   canonicalization is O(n) with proper hash-consing, paid ONCE per distinct")
print("   computation on insert (amortized over all future merges), with lookups O(1).")
print(" * So the principled cost model is: canon O(size) amortized, merge O(lookups) --")
print("   subdominant when amortized, exactly as e-graph hash-consing is on insert.")
print(" * CRUCIAL CAVEAT: this measures STRUCTURAL identity (same derivation, different")
print("   labels) -- cheap, decidable. It does NOT measure SEMANTIC identity (same")
print("   function, different derivation), which is undecidable and is the tier e-graphs")
print("   approximate. Converting structural equivalence to computational idempotence is")
print("   shown; converting SEMANTIC equivalence is the open, harder problem.")
