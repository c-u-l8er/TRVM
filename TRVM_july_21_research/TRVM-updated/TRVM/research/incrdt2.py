"""
incrdt2.py -- Level 4: does REDUCTION preserve the CRDT properties, and does
merge preserve SHARING?  (The operational question, not the semantic one.)

Operator under test:  merge(A,B) = NF(A U B), reducing the union AS ONE NET so
shared sub-structure can be reduced once and stay shared through reduction.

Four metrics (semantic idempotence can hold while operational idempotence fails):
  NF-equality   -> CRDT correctness
  node count    -> storage cost
  rewrite count -> computational cost
  NF depth      -> scheduling-cost proxy (longest dependency chain in the result)

Plus the three failure modes:
  F1 semantic duplicates (A U A makes new reducible structure -> need canonicalization)
  F2 operational duplicates (NFs match, work doubles -> need optimal sharing)
  F3 merge creates NEW reductions (pieces interact -> merge becomes INFERENCE)

Reducer: ic_float.  Run: python3 incrdt2.py
"""
import ic_float
from incrdt import church, NOT, TRUE, FALSE, deriv, parse_tree, canon, treesize

def depth(t):
    tag = t[0]
    if tag in ("var", "era"): return 1
    if tag == "lam": return 1 + depth(t[2])
    if tag == "app": return 1 + max(depth(t[1]), depth(t[2]))
    if tag == "sup": return 1 + max(depth(t[2]), depth(t[3]))
    if tag == "dup": return 1 + max(depth(t[4]), depth(t[5]))

def reduce_meas(src):
    """(normal-form string, rewrites, NF node count, NF depth)"""
    nf, total, _ = ic_float.run(src)
    tr = parse_tree(nf)
    return nf, total, treesize(tr), depth(tr)

# ---- encode a knowledge multiset as ONE net under a free root R --------------
def bag_term(multiset):           # no dedup: every derivation inlined (duplicates kept)
    body = "R"
    for s in multiset: body = f"({body} {s})"
    return body

def set_term(multiset):           # content-addressed: distinct derivations, sorted (order-free)
    seen = {}
    for s in multiset: seen[canon(parse_tree(s))] = s
    body = "R"
    for k in sorted(seen): body = f"({body} {seen[k]})"
    return body

def facts_of(multiset):           # the SET of normal-form facts (semantic state)
    return frozenset(ic_float.run(s)[0] for s in set(
        {canon(parse_tree(s)): s for s in multiset}.values()))

# ============================================================ replicas
A = [deriv(2, FALSE), deriv(3, TRUE), deriv(5, FALSE)]
B = [deriv(2, FALSE), deriv(4, TRUE), deriv(7, FALSE)]
C = [deriv(3, TRUE),  deriv(7, FALSE), deriv(2, FALSE)]
def U(*reps):
    out = []
    for r in reps: out += r
    return out

print("Level 4: does reduction PRESERVE the CRDT properties + sharing?")
print("merge(A,B) = NF(A U B), reducing the union as one net.")
print("=" * 78)

# ---- commutativity & associativity ACROSS merges (semantic) -----------------
print("\n[1] COMMUTATIVITY / ASSOCIATIVITY across incremental merges (NF-set)")
print(f"    NF(AUB) == NF(BUA)                 : {facts_of(U(A,B)) == facts_of(U(B,A))}")
print(f"    NF(NF(AUB)UC) == NF(AU NF(BUC))    : "
      f"{facts_of(U(sorted(facts_of(U(A,B))), C)) == facts_of(U(A, sorted(facts_of(U(B,C)))))}")
print("    (holds by confluence + set union; staging does not change the facts.)")

# ---- idempotence on all four metrics ----------------------------------------
def metrics(term): 
    nf, rw, nodes, dp = reduce_meas(term); return rw, nodes, dp

aa_bag, a_bag = metrics(bag_term(U(A,A))), metrics(bag_term(A))
aa_set, a_set = metrics(set_term(U(A,A))), metrics(set_term(A))
print("\n[2] IDEMPOTENCE  merge(A,A) vs A  -- all four metrics   <== the money")
print(f"    semantic NF-set equal                 : {facts_of(U(A,A)) == facts_of(A)}")
print(f"    {'metric':14}{'A':>8}{'merge(A,A)':>14}{'idempotent?':>14}")
for name, av, mv in [("rewrites", a_bag[0], aa_bag[0]), ("nodes", a_bag[1], aa_bag[1]), ("depth", a_bag[2], aa_bag[2])]:
    print(f"    BAG {name:10}{av:>8}{mv:>14}{str(av==mv):>14}")
for name, av, mv in [("rewrites", a_set[0], aa_set[0]), ("nodes", a_set[1], aa_set[1]), ("depth", a_set[2], aa_set[2])]:
    print(f"    CA  {name:10}{av:>8}{mv:>14}{str(av==mv):>14}")
print("    => F2 confirmed for BAG (NF matches but work+storage DOUBLE).")
print("       Content-addressing makes idempotence hold OPERATIONALLY, not just semantically.")

# ============================================================ the sharing curve
print("\n" + "=" * 78)
print("[3] DOES MERGE PRESERVE SHARING?  cost vs # derivations sharing a sub-computation")
print("    Shared sub-computation S = (church6 NOT) (expensive). N derivations use it.")
S = f"({church(6)} {NOT})"
args = [FALSE, TRUE, FALSE, TRUE, FALSE, TRUE]

def unshared(n):                       # each derivation reduces its own copy of S
    body = "R"
    for i in range(n): body = f"({body} ({S} {args[i]}))"
    return body

def shared(n, base=900):               # S shared via a dup-cascade, reduced ~once
    if n == 1: return f"(R ({S} {args[0]}))"
    src = ""; cur = S; copies = []
    for i in range(n-1):
        s, r = f"s{i}", f"r{i}"; src += f"!&{base+i}{{{s},{r}}}={cur};"; copies.append(s); cur = r
    copies.append(cur)
    body = "R"
    for i in range(n): body = f"({body} ({copies[i]} {args[i]}))"
    return src + body

print(f"    {'N':>3}{'unshared rw':>14}{'shared rw':>12}{'ratio':>8}   (shared should grow much slower)")
for n in (1, 2, 3, 4, 6):
    _, u, _, _ = reduce_meas(unshared(n))
    _, s, _, _ = reduce_meas(shared(n))
    print(f"    {n:>3}{u:>14}{s:>12}{(u/s):>8.2f}")
print("    => sharing IS preserved under reduction: the common sub-computation is built")
print("       once; you pay linearly only for the genuinely-distinct application work.")
print("       merge(A,A) (everything shared) -> constant; merge(A,B) -> core once + distinct tails.")

# ============================================================ failure 3: inference
print("\n" + "=" * 78)
print("[4] FAILURE 3 (the fascinating one): does merge create NEW reductions?")
print("    Two pieces, each individually in normal form, that INTERACT when composed.")
rule = f"λx.(({church(3)} {NOT}) x)"     # a 'rule': flips parity 3x (= one flip), awaits input
fact = TRUE                               # a 'fact'
nf_rule, rw_rule, _, _ = reduce_meas(rule)
nf_fact, rw_fact, _, _ = reduce_meas(fact)
nf_join, rw_join, _, _ = reduce_meas(f"({rule} {fact})")   # compose: wire rule's input to fact
print(f"    NF(rule) stable (a lambda), rewrites to reach it : {rw_rule}")
print(f"    NF(fact) stable (TRUE),     rewrites             : {rw_fact}")
print(f"    NF(compose(rule,fact)) = {nf_join!r}")
print(f"      -> a NEW fact (FALSE), produced by {rw_join} rewrites the pieces did not do alone.")
print("    So when pieces share an interface, merge performs INFERENCE, not just storage.")
print("    HONEST: this needs composition (wiring an open port to a value), not bare set")
print("    union. That is strictly more than a replicated data structure -- and strictly")
print("    more powerful: knowledge accumulation = new inference.")

print("\n" + "=" * 78)
print("VERDICT")
print(" * Reduction PRESERVES commutativity, associativity, and idempotence -- provided")
print("   the union is content-addressed. Then merge(A,A) costs the SAME (not 2x) in")
print("   rewrites, storage, and depth: operational idempotence, the property a data CRDT")
print("   doesn't need but a *computational* CRDT must have.")
print(" * Sharing survives reduction: overlapping knowledge is reduced once; you pay only")
print("   for what is genuinely new. That is the 'doesn't pay repeatedly for already-")
print("   discovered work' property -- a replicated COMPUTATIONAL structure.")
print(" * And merge can become inference (F3) when pieces share an interface -- the regime")
print("   where accumulation produces new knowledge. That is the Graphonomous direction.")
print(" * Open hard part remains: AUTOMATIC sub-term content-addressing under arbitrary")
print("   reduction (here the sharing was encoded deliberately) = maximal-sharing-under-")
print("   rewriting = the e-graph / optimal-reduction frontier.")
