"""
incrdt3.py -- the frontier: AUTOMATIC content-addressing.

Level-4 (incrdt2) hand-encoded the DUP sharing. The thesis-grade question:
can a content-addressing pass AUTOMATICALLY find the shared sub-computation,
and does the sharing SURVIVE reduction?  This is where it gets subtle, because
the shared sub-term itself contains DUPs (Church numerals do), so sharing it
means duplicating a dup-containing term -- the exact maximal-sharing-under-
rewriting / e-graph frontier.

auto_share(sources):
  1. find CLOSED subterms repeated >=2x across the knowledge forest
  2. pick the most impactful (size x reuse), hoist ONE copy, share via a DUP fan
  3. emit one net; reduce; CHECK NF == unshared NF (correctness guard), compare work

Run: python3 incrdt3.py
"""
import ic_float
from incrdt import church, NOT, TRUE, FALSE, parse_tree, canon

# ---- term utilities ----------------------------------------------------------
def free_vars(t, bound=frozenset()):
    tag = t[0]
    if tag == "var": return set() if t[1] in bound else {t[1]}
    if tag == "era": return set()
    if tag == "lam": return free_vars(t[2], bound | {t[1]})
    if tag == "app": return free_vars(t[1], bound) | free_vars(t[2], bound)
    if tag == "sup": return free_vars(t[2], bound) | free_vars(t[3], bound)
    if tag == "dup": return free_vars(t[4], bound) | free_vars(t[5], bound | {t[2], t[3]})
    return set()

def is_closed(t): return not free_vars(t)

def size(t):
    tag = t[0]
    if tag in ("var", "era"): return 1
    if tag == "lam": return 1 + size(t[2])
    if tag == "app": return 1 + size(t[1]) + size(t[2])
    if tag == "sup": return 1 + size(t[2]) + size(t[3])
    if tag == "dup": return 1 + size(t[4]) + size(t[5])

def render(t):
    tag = t[0]
    if tag == "var": return t[1]
    if tag == "era": return "*"
    if tag == "lam": return f"λ{t[1]}.{render(t[2])}"
    if tag == "app": return f"({render(t[1])} {render(t[2])})"
    if tag == "sup": return f"&{t[1]}{{{render(t[2])},{render(t[3])}}}"
    if tag == "dup": return f"!&{t[1]}{{{t[2]},{t[3]}}}={render(t[4])};{render(t[5])}"

def collect(t, counts, reps):
    if is_closed(t) and size(t) >= 3:
        k = canon(t); counts[k] = counts.get(k, 0) + 1; reps[k] = t
    tag = t[0]
    if tag == "lam": collect(t[2], counts, reps)
    elif tag == "app": collect(t[1], counts, reps); collect(t[2], counts, reps)
    elif tag == "sup": collect(t[2], counts, reps); collect(t[3], counts, reps)
    elif tag == "dup": collect(t[4], counts, reps); collect(t[5], counts, reps)

def replace(t, key, ctr):
    if canon(t) == key:
        v = ("var", f"__p{ctr[0]}"); ctr[0] += 1; return v
    tag = t[0]
    if tag == "lam": return ("lam", t[1], replace(t[2], key, ctr))
    if tag == "app": return ("app", replace(t[1], key, ctr), replace(t[2], key, ctr))
    if tag == "sup": return ("sup", t[1], replace(t[2], key, ctr), replace(t[3], key, ctr))
    if tag == "dup": return ("dup", t[1], t[2], t[3], replace(t[4], key, ctr), replace(t[5], key, ctr))
    return t

def unshared_term(sources):
    body = "R"
    for s in sources: body = f"({body} {s})"
    return body

def auto_share(sources):
    trees = [parse_tree(s) for s in sources]
    counts, reps = {}, {}
    for t in trees: collect(t, counts, reps)
    cands = [(k, c) for k, c in counts.items() if c >= 2]
    if not cands:
        return unshared_term(sources), None, 0
    # most impactful: size of saved work x (reuse - 1)
    key = max(cands, key=lambda kc: size(reps[kc[0]]) * (kc[1] - 1))[0]
    val = render(reps[key]); K = counts[key]
    ctr = [0]
    new_trees = [replace(t, key, ctr) for t in trees]
    # build a K-way DUP fan from one copy of the shared value
    parts = []; cur = val
    for i in range(K - 1):
        a = f"__p{i}"; b = f"__p{K-1}" if i == K - 2 else f"__t{i}"
        parts.append(f"!&{700+i}{{{a},{b}}}={cur};"); cur = b
    body = "R"
    for t in new_trees: body = f"({body} {render(t)})"
    return "".join(parts) + body, (val, K), size(reps[key])

def rw(term):
    nf, total, _ = ic_float.run(term)
    return nf, total

# ============================================================ experiment
# knowledge where derivations SHARE an expensive closed sub-computation (church6 NOT)
SUB = f"({church(6)} {NOT})"
K = [f"({SUB} {FALSE})", f"({SUB} {TRUE})", f"({SUB} {FALSE})"]   # 3 uses (one a whole dup)

print("AUTOMATIC content-addressing: can a pass find shared sub-computation and")
print("does the sharing survive reduction (it contains DUPs -> the hard case)?")
print("=" * 78)
print(f"knowledge: 3 derivations all using SUB = (church6 NOT), applied to F/T/F")

u_term = unshared_term(K)
a_term, info, subsize = auto_share(K)
nf_u, rw_u = rw(u_term)
nf_a, rw_a = rw(a_term)

print(f"\nauto-share found a repeated closed subterm: {'YES' if info else 'no'}", end="")
if info: print(f"  (size {subsize}, reused {info[1]}x)")
print(f"\n  {'':22}{'rewrites':>10}")
print(f"  unshared (each rebuilds SUB) {rw_u:>10}")
print(f"  auto-shared (SUB hoisted)    {rw_a:>10}")
print(f"\n  CORRECTNESS  NF(auto) == NF(unshared) : {nf_a == nf_u}   <== the guard")
print(f"  SHARING      auto-shared < unshared   : {rw_a < rw_u}"
      + (f"   ({rw_u/rw_a:.2f}x less work)" if rw_a and rw_a < rw_u else "   (NO saving)"))

print("\n" + "-" * 78)
print("INTERPRETATION:")
if nf_a != nf_u:
    print(" * NF MISMATCH: sharing a DUP-containing term under another DUP changed the")
    print("   result. That is the maximal-sharing-under-rewriting boundary, found concretely:")
    print("   naive content-addressing is UNSOUND when shared sub-terms contain dups.")
    print("   (This is exactly why optimal sharing / e-graph canonicalization is hard.)")
elif rw_a < rw_u:
    print(" * CORRECT *and* CHEAPER: the automatic pass found the shared sub-computation,")
    print("   shared it via a DUP fan, and reduction PRESERVED the sharing -- the dup-of-a-")
    print("   dup case resolved soundly. Automatic content-addressed merge works here.")
    print(" * This is the operational property a *computational* CRDT needs, achieved")
    print("   automatically (not hand-encoded): overlapping knowledge reduced once, soundly.")
else:
    print(" * CORRECT but NOT cheaper: NF matches, yet the shared sub-term was re-reduced")
    print("   per use (F2 persists). Sharing is sound but not exploited -- you'd need the")
    print("   reducer to memoize the shared whnf. The frontier is the *exploitation*, not")
    print("   the correctness.")

# ---- second case: scale it, confirm the law holds automatically --------------
print("\n" + "=" * 78)
print("SCALING the automatic pass (N derivations sharing SUB):")
print(f"  {'N':>3}{'unshared':>11}{'auto':>9}{'NF ok':>8}{'ratio':>8}")
for n in (2, 3, 4, 6):
    Ks = [f"({SUB} {FALSE})" if i % 2 == 0 else f"({SUB} {TRUE})" for i in range(n)]
    nfu, ut = rw(unshared_term(Ks))
    at_term, _, _ = auto_share(Ks)
    nfa, at = rw(at_term)
    print(f"  {n:>3}{ut:>11}{at:>9}{str(nfa==nfu):>8}{(ut/at if at else 0):>8.2f}")

print("\n" + "=" * 78)
print("VERDICT (frontier): see correctness guard above. If NF matches and work drops,")
print("automatic content-addressed merge preserves sharing under reduction -- the IN-CRDT")
print("is real, not just axiomatically but operationally and automatically. If NF matches")
print("but work doesn't drop, the open problem is sharing EXPLOITATION (memoize shared")
print("whnf). If NF mismatches, the open problem is sharing SOUNDNESS (dup-of-dup) -- and")
print("either way the boundary is now concrete and measured, not hand-waved.")
