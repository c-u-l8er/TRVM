"""
frontier.py -- the tier-1 frontier and its edge, from the periodic-table sort.

Three things the sort claims, made concrete:
  1. sigma -> tier 1 BY CONSTRUCTION (representation-structural) == conflict-freedom.
     The genuine third structural result after beta and the provenance G-Set.
  2. kappa (incremental SCC) is NOT the same flavor: a maintained index whose guarantee
     lives in the maintenance, not the representation -- a cache that CAN go stale.
  3. delta (demurrage) marks the edge -- and the culprit is PROPORTIONALITY x transactions,
     not time. Fixed/per-capita demurrage commutes with deposits (CRDT-able); proportional
     does not (coordination-hard).

Run: python3 frontier.py
"""
print("The tier-1 frontier and its edge.")
print("=" * 78)

# ============================================================ 1. sigma to tier 1
# H1 of a cellular sheaf = obstruction to gluing local sections. Model: regions in a
# loop, each overlap demanding a difference g_ij (the restriction-map mismatch). A
# 1-cochain is a coboundary (glues; H1 class = 0) iff its sum around every cycle is 0.
print("\n1. sigma (resolution) -> TIER 1 by construction  ==  conflict-freedom")
print("-" * 78)
def loop_sum(g01, g12, g20): return g01 + g12 + g20   # cocycle sum on a triangle

# measured sigma: an ARBITRARY sheaf -- differences need not sum to zero.
import random
random.seed(0)
arb_nonzero = sum(1 for _ in range(1000)
                  if loop_sum(random.randint(-9, 9), random.randint(-9, 9), random.randint(-9, 9)) != 0)
print(f"   measured (arbitrary sheaf): {arb_nonzero}/1000 random cochains have H1 obstruction != 0")
print( "     -> detecting the obstruction = computing the cycle sum = linear algebra = TIER 2")

# built sigma: the confluent merge reconciles regions to a shared potential phi (a join);
# every overlap difference is then g_ij = phi[j]-phi[i], a COBOUNDARY -> loop sum telescopes
# to 0 ALWAYS. A nonzero obstruction is unrepresentable.
built_nonzero = 0
for _ in range(1000):
    phi = [random.randint(-50, 50) for _ in range(3)]
    g01, g12, g20 = phi[1] - phi[0], phi[2] - phi[1], phi[0] - phi[2]
    if loop_sum(g01, g12, g20) != 0: built_nonzero += 1
print(f"   built (differences from a shared potential): {built_nonzero}/1000 have obstruction != 0")
print( "     -> a gluing failure is UNREPRESENTABLE: differences from a potential telescope to 0.")
print( "        sigma is free, H1 = 0 by construction. That IS conflict-freedom -- exactly what")
print( "        the confluent merge hands you for the replica case. REPRESENTATION-structural,")
print( "        like beta and content-addressing: nothing to check, no code to trust.")

# ============================================================ 2. kappa is a different flavor
print("\n\n2. kappa (routing) -> the incremental route is a MAINTAINED INDEX, not structural")
print("-" * 78)
# truth: "is node 0 on a cycle?" by recomputation (can it reach itself?).
def reaches_self(edges, n=0):
    seen = set(); stack = [b for (a, b) in edges if a == n]
    while stack:
        x = stack.pop()
        if x == n: return True
        if x in seen: continue
        seen.add(x); stack += [b for (a, b) in edges if a == x]
    return False
edges = [(0, 1), (1, 2)]
cache_on_cycle = False                       # maintained as edges arrive
def add_edge(e, maintain=True):
    edges.append(e)
    global cache_on_cycle
    if maintain and reaches_self(edges):      # the maintenance step
        cache_on_cycle = True
add_edge((2, 0))                              # closes the loop, maintained
print(f"   after closing the loop (maintained): cache={cache_on_cycle}, truth={reaches_self(edges)}  agree")
edges2 = list(edges)
edges.clear(); edges.extend([(0, 1), (1, 2)]); cache_on_cycle = False
add_edge((2, 0), maintain=False)             # a SKIPPED update (missed event / bug)
print(f"   after closing the loop (maintenance skipped): cache={cache_on_cycle}, truth={reaches_self(edges)}  DIVERGE")
print( "     -> the representation does not forbid the stale cache; the guarantee lives in the")
print( "        maintenance being correct. Fast (O(1) query) but tier-1.5, not structural --")
print( "        unlike sigma, where the bad state simply cannot be built. So the honest count is")
print( "        beta + sigma + provenance G-Set structural; kappa a fast path with an obligation.")

# ============================================================ 3. delta -- the edge
print("\n\n3. delta (demurrage) -> the edge, and the culprit is PROPORTIONALITY x transactions")
print("-" * 78)
b, d, r, c = 100.0, 50.0, 0.1, 3.0
prop = lambda x: x * (1 - r)        # proportional demurrage (Gesell's holding %)
fixed = lambda x: x - c             # fixed / per-capita demurrage
dep = lambda x: x + d               # a deposit (a transaction)
pde, ped = prop(dep(b)), dep(prop(b))
fde, fed = fixed(dep(b)), dep(fixed(b))
print(f"   proportional: decay(deposit(b))={pde:.1f}  vs  deposit(decay(b))={ped:.1f}   commute? {abs(pde-ped) < 1e-9}")
print(f"   fixed:        decay(deposit(b))={fde:.1f}  vs  deposit(decay(b))={fed:.1f}   commute? {abs(fde-fed) < 1e-9}")
print( "     -> proportional decay does NOT commute with a deposit (order matters -> not a CRDT,")
print( "        coordination needed). Fixed decay DOES commute (a constant drain that merges as a")
print( "        PN-counter once you key the drain idempotently per epoch). The break is not time --")
print( "        it is proportionality. Gesell's demurrage is a percentage, so as written it cannot")
print( "        be a coordination-free currency beside deposits; only a fixed/per-capita holding")
print( "        cost stays mergeable. A concrete warning for the v0.5 economic layer.")

print("\n" + "=" * 78)
print("FRONTIER:")
print("  sigma  -> TIER 1 by construction (representation-structural)  == conflict-freedom  [NEW]")
print("  kappa  -> TIER 2 with an O(1) fast path (maintained index, carries an obligation)")
print("  delta  -> TIER 2; proportional-decay x transactions is non-commutative (the real edge)")
print("\n  'tier-1 is a technique' holds for the REPRESENTATION-structural kind: beta, the G-Set,")
print("  and now sigma-by-construction. kappa is a fast path, not a fourth structural result.")
print("  delta pinpoints where the substrate stops -- not at time, but at proportional value.")
