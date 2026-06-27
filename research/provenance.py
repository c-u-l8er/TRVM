"""
provenance.py -- two results: the provenance G-Set as a structural tier-1 invariant, and the
inter-agent sigma case that fixes the replica-scoping frontier.py flagged.

1. PROVENANCE G-SET: derivation facts (what was derived, by which rule, from which premises)
   form a grow-only set merged by union -- the canonical CRDT. "No duplicate or conflicting
   provenance" is structural (set membership), not checked. This is the second representation-
   structural tier-1 result, alongside beta (a counter) and sigma-by-construction (frontier.py).

2. INTER-AGENT SIGMA: frontier.py showed sigma is tier-1 for REPLICAS (the confluent merge
   forces agreement, so H^1 = 0 by construction). But two independent AGENTS can hold views
   that genuinely disagree -- a real gluing obstruction, H^1 != 0, that the substrate MEASURES
   (tier-2) rather than makes vanish. This is the honest scope: sigma is tier-1 for replicas,
   tier-2 for arbitrary inter-agent views.

Run: python3 provenance.py
"""
import random
rng = random.Random(0)

# ============================================================ 1. provenance G-Set
print("1. provenance G-Set -- a structural tier-1 invariant")
print("=" * 78)
# a provenance fact: (derived_term, rule, frozenset(premises)) -- immutable, content-addressed
def prov(term, rule, premises): return (term, rule, frozenset(premises))
agentA = {prov("c6", "mult", ["c2", "c3"]), prov("c8", "mult", ["c2", "c4"])}
agentB = {prov("c6", "mult", ["c3", "c2"]), prov("c6", "add", ["c3", "c3"])}  # 2 ways to get c6
def merge(x, y): return x | y                                   # union
A, B = agentA, agentB
print(f"   agent A derived {len(A)} facts, agent B derived {len(B)} facts")
comm = merge(A, B) == merge(B, A)
assoc = merge(merge(A, B), agentB) == merge(A, merge(B, agentB))
idem = merge(A, A) == A
print(f"   CRDT laws on union:  commutative {comm}   associative {assoc}   idempotent {idem}")
print(f"   merged provenance has {len(merge(A, B))} facts (c6-via-mult-c2-c3 counted once across agents)")
print( "   structural: a duplicate provenance fact is unstorable (set membership); two DIFFERENT")
print( "   derivations of the same term (mult vs add for c6) are kept as distinct facts -- the")
print( "   merge records HOW each result was reached, coordination-free, no double-counting.")
print( "   => tier-1 by representation (like beta and sigma-by-construction): nothing to check.")

# ============================================================ 2. inter-agent sigma
print("\n\n2. inter-agent sigma -- the obstruction is REAL when agents (not replicas) disagree")
print("=" * 78)
def loop_sum(g01, g12, g20): return g01 + g12 + g20             # H^1 obstruction on a triangle

# REPLICA case (frontier.py): confluent merge reconciles to a shared potential -> coboundary -> 0
phi = {0: 5, 1: 8, 2: 3}                                        # the agreed global value
g01, g12, g20 = phi[1] - phi[0], phi[2] - phi[1], phi[0] - phi[2]
print(f"   replicas (confluent merge to shared potential): H^1 obstruction = {loop_sum(g01, g12, g20)}")
print( "     -> 0 by construction; a gluing failure is unrepresentable. tier-1 (frontier.py).")

# INTER-AGENT case: three agents hold pairwise-overlap claims that do NOT come from one potential
# e.g. on overlap A-B agent says +2, B-C says +2, C-A says +2 -- a cycle that cannot close.
gAB, gBC, gCA = 2, 2, 2
obstruction = loop_sum(gAB, gBC, gCA)
print(f"\n   agents (independent views): overlap claims +2, +2, +2 around a 3-cycle")
print(f"     H^1 obstruction = {obstruction}  != 0  -> the views CANNOT glue: a real conflict")
print( "     -> detecting it is computing the cycle sum (linear algebra) = TIER 2, not free.")
print( "        the substrate MEASURES the disagreement; it does not make it vanish. One agent")
print( "        must yield (a genuine resolution decision), which is exactly why inter-agent")
print( "        sigma is tier-2 while the replica case is tier-1.")

# show it's a real obstruction: no global assignment satisfies all three overlap constraints
def has_global_section(gAB, gBC, gCA):
    # try to find values vA,vB,vC with vB-vA=gAB, vC-vB=gBC, vA-vC=gCA
    vA = 0; vB = vA + gAB; vC = vB + gBC
    return (vA - vC) == gCA                                     # closes iff cycle sum = 0
print(f"\n   global section exists? {has_global_section(gAB, gBC, gCA)} for the agents"
      f"  vs {has_global_section(g01, g12, g20)} for the replicas")

print("\n" + "=" * 78)
print("SUMMARY:")
print(" * provenance G-Set: a third representation-structural tier-1 invariant (after beta the")
print("   counter and sigma-by-construction) -- derivation history merges by union, duplicates")
print("   unrepresentable, distinct derivations preserved, coordination-free.")
print(" * inter-agent sigma: the honest scope of frontier.py. sigma is tier-1 for REPLICAS (the")
print("   confluent merge forces H^1 = 0); for arbitrary AGENT views the obstruction is real and")
print("   nonzero, and the substrate measures it (tier-2) rather than dissolving it. Conflict-")
print("   freedom is a property the merge GIVES replicas, not one it can impose on disagreeing")
print("   agents -- which is the correct, non-overclaimed statement.")
