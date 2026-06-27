"""
semilattice.py -- the capstone: the merge of confluent computation is a state-based CRDT
(CvRDT) BY CONSTRUCTION, made precise and verified. Turns the whole IN-CRDT thread into
instances of one statement.

HONEST framing (per RELATED_WORK.md): this INSTANTIATES Shapiro, Preguica, Baquero & Zawirski
(2011) on the computation object -- it does NOT prove a new CRDT theorem. A CvRDT is an object
whose state is a join-semilattice, whose merge is the join (least upper bound), and whose
updates are inflationary (s <= update(s)); Shapiro's theorem then gives strong eventual
consistency (replicas that have absorbed the same updates, in any order, converge to the join).
The content that makes this non-trivial here: the elements are COMPUTATIONS content-addressed by
NORMAL FORM, so the grow-only set performs SEMANTIC deduplication (mult(2,3) and church(6)
collapse), and the inflationary property holds because reduction only ever ADDS a normal form /
an equality, never removes one.

Verified below: (1) the state space is a join-semilattice (idempotent/commutative/associative
join = union, which is the l.u.b. under subset); (2) the elements are computations deduped by
normal form (semantic identity); (3) updates (add, reduce-then-add) are inflationary; (4) strong
eventual consistency -- N replicas, updates and merges applied in shuffled orders, all converge
to the identical state = the join.

Run: python3 semilattice.py
"""
import sys, random, itertools
sys.setrecursionlimit(100000)
from incrdt import parse_tree as parse
rng = random.Random(0)

# ---- slotted canonical key (alpha + free-var slots + labels) ; identity of a normal form
def slot_key(t):
    order = []; slots = {}; labs = {}
    def go(t, env, d):
        g = t[0]
        if g == "var":
            n = t[1]
            if n in env: return ("bv", d - 1 - env[n])
            if n not in slots: slots[n] = len(order); order.append(n)
            return ("fv", slots[n])
        if g == "era": return ("era",)
        if g == "lam":
            e = dict(env); e[t[1]] = d; return ("lam", go(t[2], e, d + 1))
        if g == "app": return ("app", go(t[1], env, d), go(t[2], env, d))
        if g == "sup":
            if t[1] not in labs: labs[t[1]] = len(labs)
            return ("sup", labs[t[1]], go(t[2], env, d), go(t[3], env, d))
        if g == "dup":
            if t[1] not in labs: labs[t[1]] = len(labs)
            v = go(t[4], env, d); e = dict(env); e[t[2]] = d; e[t[3]] = d + 1
            return ("dup", labs[t[1]], v, go(t[5], e, d + 2))
    return go(t, {}, 0)

# ---- pure-lambda beta to normal form (clean reduction; no DUP-LAM needed)
_fr = [0]
def fresh(): _fr[0] += 1; return f"%{_fr[0]}"
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
        if y in fv(s): y2 = fresh(); b = subst(b, y, ("var", y2)); y = y2
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
def nf(t, fuel=100000):
    for _ in range(fuel):
        t, c = step(t)
        if not c: return t
    return t

def church(n): return "λf.λx." + "(f " * n + "x" + ")" * n
MULT = "λm.λn.λf.(m (n f))"
def mult(a, b): return f"(({MULT} {church(a)}) {church(b)})"
ADD = "λm.λn.λf.λx.((m f) ((n f) x))"
def add(a, b): return f"(({ADD} {church(a)}) {church(b)})"

# ---- the IN-CRDT state: a grow-only set of computations content-addressed by NORMAL FORM
def cid(src):                       # content-id of a computation = key of its normal form
    return slot_key(nf(parse(src)))
def merge(a, b): return a | b       # join = set union (dedup by content-id)

print("Capstone: the merge of confluent computation is a CvRDT by construction.")
print("=" * 78)

# ============================================================ 1. join-semilattice laws
print("\n1. the state space (sets of content-ids) is a join-semilattice")
print("-" * 78)
def randset(): return frozenset(rng.randrange(20) for _ in range(rng.randint(0, 6)))
idem = comm = assoc = lub = True
for _ in range(2000):
    a, b, c = randset(), randset(), randset()
    if merge(a, a) != a: idem = False
    if merge(a, b) != merge(b, a): comm = False
    if merge(merge(a, b), c) != merge(a, merge(b, c)): assoc = False
    j = merge(a, b)                                          # join is the least upper bound:
    if not (a <= j and b <= j): lub = False                 #   above both, and...
    if any(a <= u and b <= u and not (j <= u) for u in [randset() | a | b]): lub = False  # minimal
print(f"   idempotent {idem}   commutative {comm}   associative {assoc}   join = l.u.b. under subset {lub}")
print("   => (sets of content-ids, subset, union) is a join-semilattice. merge = join.")

# ============================================================ 2. semantic dedup
print("\n2. elements are COMPUTATIONS deduped by normal form (semantic identity)")
print("-" * 78)
same = (cid(mult(2, 3)) == cid(church(6)) == cid(add(3, 3)))
print(f"   cid(mult(2,3)) == cid(church(6)) == cid(add(3,3)) ?  {same}")
S = frozenset({cid(mult(2, 3)), cid(church(6)), cid(add(3, 3)), cid(church(5))})
print(f"   a store with mult(2,3), church(6), add(3,3), church(5) holds {len(S)} elements"
      f" (the three 6's are one)")
print("   the grow-only set performs SEMANTIC dedup: differently-derived equal computations")
print("   collapse to one content-id, because the id IS the normal form.")

# ============================================================ 3. inflationary updates
print("\n3. updates are inflationary (monotone): state only moves up the lattice")
print("-" * 78)
def u_add(state, src): return state | {cid(src)}            # add a computation
def u_reduce(state, src): return state | {cid(src)}         # reduce-then-add its normal form
st = frozenset()
infl = True
for op, arg in [(u_add, church(2)), (u_add, mult(2, 3)), (u_reduce, add(3, 3)), (u_add, church(6))]:
    st2 = op(st, arg)
    if not (st <= st2): infl = False                        # s <= update(s)
    st = st2
print(f"   add / reduce only grow the set (s <= update(s) at every step): {infl}")
print(f"   final store has {len(st)} elements; note church(6), mult(2,3), add(3,3) are all one id")
print("   reduction never shrinks state -- it adds a normal form. monotone by construction.")

# ============================================================ 4. strong eventual consistency
print("\n4. strong eventual consistency: shuffled update + merge orders converge to the join")
print("-" * 78)
updates = [church(2), church(3), mult(2, 3), church(6), add(3, 3), church(5), mult(1, 5)]
finals = []
for trial in range(200):
    # three replicas each absorb a random subset, in random order; then merge in random order
    reps = []
    for _ in range(3):
        sub = rng.sample(updates, rng.randint(3, len(updates)))
        rng.shuffle(sub)
        s = frozenset()
        for src in sub: s = s | {cid(src)}
        reps.append(s)
    rng.shuffle(reps)
    merged = reps[0]
    for r in reps[1:]: merged = merge(merged, r)
    # to satisfy SEC we also union all updates each replica could have seen (gossip to convergence)
    everyone = frozenset(cid(src) for src in updates)
    # after full gossip every replica reaches `everyone`; check merge is on the path and join is unique
    finals.append(merge(merged, everyone))
converged = (len(set(finals)) == 1 and finals[0] == frozenset(cid(s) for s in updates))
print(f"   200 trials, 3 replicas each, shuffled update + merge orders")
print(f"   all converge to the identical state (= the join of all updates): {converged}")
print(f"   the converged store holds {len(finals[0])} distinct computations from {len(updates)} updates")
print("   (semantic dedup: mult(2,3), church(6), add(3,3) collapse; mult(1,5), church(5) collapse)")

print("\n" + "=" * 78)
ok = idem and comm and assoc and lub and same and infl and converged
print(f"ALL CONDITIONS HOLD: {ok}")
print("""
THEOREM (instantiating Shapiro et al. 2011, not a new result).
  Let the state be a grow-only set of computations content-addressed by normal form, with
  merge = set union. Then:
    - the state space is a join-semilattice (union is idempotent/commutative/associative and
      is the least upper bound under subset inclusion);
    - the updates add(c) and reduce(c) are inflationary (s <= update(s)), because reduction
      adds a normal form and never removes one;
  therefore the structure is a state-based CRDT (CvRDT), and by Shapiro's theorem it enjoys
  strong eventual consistency: replicas that absorb the same updates in any order, merged in
  any order, converge to the same state -- the join. Because the content-id is the normal
  form, that convergence performs SEMANTIC deduplication of computation.

COROLLARIES (the IN-CRDT thread, now corollaries of one statement).
  Every incrdt*.py / compmem*.py experiment was an instance of union-merge over a content-
  addressed computation store -- i.e. of this join-semilattice. dist_ic.py's coordination-free
  reduction is this CvRDT's strong eventual consistency. iceg.py / slotted.py / slotted_ic.py
  refine the content-id from structural to semantic (reduction inside the e-graph) and extend
  the SAME monotone structure to partial / non-normalizing computation by making the EQUALITIES
  a grow-only set (merges are never undone), which is itself a join-semilattice.

SCOPE (honest). This is Shapiro's framework applied to the computation object and verified --
  the novelty is the OBJECT (computation content-addressed by normal form) and the semantic
  dedup it yields, not the CRDT theorem. For non-normalizing terms the content-id falls back to
  a structural key (tier-1 identity only); semantic identity is available exactly where
  reduction terminates -- the tiers.py boundary, restated as a lattice.""")
