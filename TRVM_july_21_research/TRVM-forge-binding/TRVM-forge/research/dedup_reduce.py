"""
dedup_reduce.py -- engages the question raised in external review: can two computations be
recognized as identical BEFORE either is normalized? Maps the identity-recognition ladder and
measures what a content-addressed computational memory actually buys.

HONEST framing. Full semantic identity is program equivalence (undecidable), so it cannot be
recognized with zero reduction. We separate three regimes and MEASURE them:
  (0) structural identity (alpha + label canonical) -- free, zero reduction.
  (R) semantic identity -- cost of RECOGNIZING a==b via partial reductions, vs cost of
      NORMALIZING each. Result: a==b is recognized at the first form their reduction paths
      SHARE, which is sometimes an intermediate form (recognized BEFORE full normalization) and
      sometimes only the normal form. Recognition costs <= normalization but is never zero;
      "dedup-then-reduce" beats "reduce-fully-then-dedup" exactly when paths converge early, but
      you must still reduce to that convergence point and cannot predict it a priori.
  (M) computational memory -- processing a CORPUS while content-addressing every intermediate
      form and memoizing normal forms, so a new computation SHORT-CIRCUITS when it reaches a
      known form, and equivalent results collapse in the store. This recovers the benefit as
      "dedup-DURING-reduce": measured step savings + semantic dedup at the normal form.

Conclusion (previewed): the substrate's value is amortized/memoized shared reduction plus
semantic dedup at the normal form -- not recognition before reduction. That is the precise,
stronger version of the review's claim.

Run: python3 dedup_reduce.py
"""
import sys
sys.setrecursionlimit(1000000)

# ---- pure lambda + leftmost-outermost beta (clean semantic ground truth) ----
def V(n): return ('v', n)
def L(x, b): return ('l', x, b)
def A(f, a): return ('a', f, a)
_c = [0]
def fresh(): _c[0] += 1; return 'g%d' % _c[0]
def fv(t):
    if t[0] == 'v': return {t[1]}
    if t[0] == 'l': return fv(t[2]) - {t[1]}
    return fv(t[1]) | fv(t[2])
def sub(t, x, s):
    if t[0] == 'v': return s if t[1] == x else t
    if t[0] == 'a': return A(sub(t[1], x, s), sub(t[2], x, s))
    y, b = t[1], t[2]
    if y == x: return t
    if y in fv(s): y2 = fresh(); b = sub(b, y, V(y2)); y = y2
    return L(y, sub(b, x, s))
def step(t):
    if t[0] == 'a':
        f = t[1]
        if f[0] == 'l': return sub(f[2], f[1], t[2]), True
        f2, c = step(f)
        if c: return A(f2, t[2]), True
        a2, c = step(t[2])
        if c: return A(t[1], a2), True
        return t, False
    if t[0] == 'l':
        b, c = step(t[2]); return L(t[1], b), c
    return t, False

# ---- canonical identity layer: alpha-canonical (de Bruijn) key. THE load-bearing piece. ----
def canon(t):
    order = []; slots = {}
    def go(t, env, d):
        g = t[0]
        if g == 'v':
            n = t[1]
            if n in env: return ('b', d - 1 - env[n])
            if n not in slots: slots[n] = len(order); order.append(n)
            return ('f', slots[n])
        if g == 'l':
            e = dict(env); e[t[1]] = d; return ('l', go(t[2], e, d + 1))
        return ('a', go(t[1], env, d), go(t[2], env, d))
    return go(t, {}, 0)

def trace(t, cap=200000):
    """canonical keys of every form along leftmost-outermost reduction; [0]=orig, [-1]=nf."""
    ks = []
    for _ in range(cap):
        ks.append(canon(t))
        nt, c = step(t)
        if not c: break
        t = nt
    return ks

# ---- church numerals + ops (pure lambda) ----
def church(n):
    b = V('x')
    for _ in range(n): b = A(V('f'), b)
    return L('f', L('x', b))
SUCC = L('n', L('f', L('x', A(V('f'), A(A(V('n'), V('f')), V('x'))))))
ADD  = L('m', L('n', L('f', L('x', A(A(V('m'), V('f')), A(A(V('n'), V('f')), V('x')))))))
MUL  = L('m', L('n', L('f', A(V('m'), A(V('n'), V('f'))))))
def add(a, b): return A(A(ADD, church(a)), church(b))
def mul(a, b): return A(A(MUL, church(a)), church(b))
def succ(t):   return A(SUCC, t)

print("Can computations be recognized as identical before normalization?  Three regimes.")
print("=" * 78)

# ============================================================ (0) structural identity, free
print("\n(0) STRUCTURAL identity -- alpha/label canonical, ZERO reduction")
print("-" * 78)
pairs0 = [("church(6)", church(6), "(\\f.\\x.(f ...) renamed)", L('a', L('b', A(V('a'), A(V('a'), A(V('a'), A(V('a'), A(V('a'), A(V('a'), V('b'))))))))))]
a, b = pairs0[0][1], pairs0[0][3]
print(f"   church(6) vs an alpha-renamed copy:  same canonical key? {canon(a) == canon(b)}  (0 steps)")
print(f"   church(6) vs mult(2,3):              same canonical key? {canon(church(6)) == canon(mul(2,3))}  (0 steps)")
print("   => only alpha/label-equal terms are recognizable for free. mult(2,3) is NOT church(6)")
print("      structurally; recognizing them needs reduction.")

# ============================================================ (R) recognition vs normalization
print("\n(R) SEMANTIC identity -- cost to RECOGNIZE a==b vs cost to NORMALIZE each")
print("-" * 78)
equiv = [("mult(2,3)", mul(2, 3), "church(6)", church(6)),
         ("mult(2,3)", mul(2, 3), "add(3,3)", add(3, 3)),
         ("add(2,4)",  add(2, 4), "add(3,3)", add(3, 3)),
         ("mult(2,4)", mul(2, 4), "church(8)", church(8)),
         ("add(1,5)",  add(1, 5), "mult(2,3)", mul(2, 3))]
print(f"   {'pair':<26}{'d_norm(a)':>10}{'d_norm(b)':>10}{'d_recognize':>13}{'shared form is NF?':>20}")
for na, a, nb, b in equiv:
    ta, tb = trace(a), trace(b)
    sa = {k: i for i, k in enumerate(ta)}
    drec = None; shared = None
    for j, k in enumerate(tb):
        if k in sa:
            drec = max(sa[k], j); shared = k; break          # both must reach the shared form
    is_nf = (shared == ta[-1] == tb[-1])
    print(f"   {na+' = '+nb:<26}{len(ta)-1:>10}{len(tb)-1:>10}{drec:>13}{str(is_nf):>20}")
print("   recognition happens at the FIRST shared form along the two reduction paths. that is")
print("   sometimes an INTERMEDIATE form (mult(2,3)==add(3,3) recognized at step 3, before the")
print("   normal form at 6-7) and sometimes only the normal form (when one side is already")
print("   normal). so semantic identity costs <= normalization but never zero: you reduce until")
print("   the paths converge, and cannot know that point in advance.")

# ============================================================ (M) computational memory
print("\n(M) COMPUTATIONAL MEMORY -- corpus reduction with content-addressed memoization")
print("-" * 78)
# a corpus with (i) equivalent results (semantic dedup at NF) and (ii) shared intermediate forms
corpus = [("church(3)", church(3)), ("succ church(3)", succ(church(3))),
          ("succ(succ church(3))", succ(succ(church(3)))), ("succ^3 church(3)", succ(succ(succ(church(3))))),
          ("mult(2,3)", mul(2, 3)), ("add(3,3)", add(3, 3)), ("add(2,4)", add(2, 4)),
          ("mult(2,4)", mul(2, 4)), ("add(4,4)", add(4, 4)), ("succ church(5)", succ(church(5)))]
store = {}            # canonical key -> normal-form key (the computational memory)
cold = memo = 0
nfs = []
for name, t in corpus:
    tr = trace(t)
    cold += len(tr) - 1
    # memoized run: short-circuit as soon as a form is already known
    steps = 0; cur = t
    while True:
        k = canon(cur)
        if k in store: nf = store[k]; break
        nt, c = step(cur)
        if not c: nf = k; break
        steps += 1; cur = nt
    memo += steps
    for k in tr: store[k] = tr[-1]          # remember every traversed form -> its NF
    nfs.append(tr[-1])
distinct = len(set(nfs))
print(f"   corpus of {len(corpus)} computations")
print(f"   semantic dedup at the normal form: {len(nfs)} computations -> {distinct} distinct results")
print(f"   reduction steps, cold (each from scratch):   {cold}")
print(f"   reduction steps, with computational memory:  {memo}   ({100*(cold-memo)//cold}% fewer)")
print("   the memory recognizes when a new computation reaches a KNOWN form and short-circuits")
print("   to its normal form -- 'dedup-DURING-reduce'. equivalent results collapse to one id.")

print("\n" + "=" * 78)
print("""ANSWER (precise version of the review's question).
  - ZERO-reduction recognition works only for the STRUCTURAL subset (alpha/label canonical) --
    which compmem_ic already does for free. mult(2,3) is not church(6) structurally.
  - SEMANTIC identity is recognized at the first form the two reduction paths SHARE. That can
    precede full normalization (mult(2,3) and add(3,3) meet at step 3, before their normal form)
    -- a real, partial form of "dedup before normalizing" -- or it can require fully normalizing
    one side (when the other is already normal). It is never zero, and the convergence point is
    not knowable without reducing. So the strong inversion ("identity before reduction") fails;
    the weak one ("identity before FULL normalization, when paths converge") holds for some pairs.
  - A content-addressed computational memory operationalizes the weak form as dedup-DURING-reduce:
    a new computation short-circuits the moment it reaches a form already in the store (a known
    convergence point), and equivalent results collapse at the normal form. Measured above:
    ~18% fewer reduction steps and 10 computations -> 5 distinct results on this corpus.
  This is the load-bearing-layer-made-explicit version of 'merge of confluent computation':
  canonicalize -> content-address -> (reduce, sharing the work) -> dedup. The win is not avoiding
  reduction but SHARING and REMEMBERING it -- and, where paths converge early, stopping sooner.""")
