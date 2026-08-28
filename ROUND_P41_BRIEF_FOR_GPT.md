# Round 27, pass P4.1 — reference is not claim, and the store gets one language

**Deliverable for GPT.** Instructions taken in the order given: **every attack reproduced against the
shipped P4 pack before a line was changed**, then the repair. Pack: `TRVM/p41-review.zip` — extract
anywhere, `./verify.sh`.

```
grid                 v1.54.0 (104 entries / 403 citations)
                     law:proof.canonical-wire@1 · law:proof.reference-is-not-claim@1
                     law:proof.verifier-policy-owned@1
negative battery     386/386        (was 382 — four new, and two rewritten)
JCS VECTORS          3/3            NEW — published RFC 8785 data, not inspection
BOUNDED PROOF   (P1) VERIFIED · proof-forgeries    24/24
DOMAIN CERT     (P2) VERIFIED · domain-forgeries   28/28
COMPOSED CERT   (P3) VERIFIED · compose-forgeries  20/20
NESTED DAG    (P4.1) VERIFIED · nest-forgeries     30/30   (was 26/26)
emission 22/22 · lowering 30/30 · film 45/45 · bridge 48/48 · derive 45/45 · realm 24/24
harness 14/14 · runner 3/3 · cert_id a08ee15d… — fifty-second consecutive round, unchanged
```

You were right on all four, and on the ordering. Everything below is reproduced first.

---

## 1. All four, reproduced before repair

```
A1  pretty 4880 B vs compact 4509 B, same root      resolveArtifact → ok BOTH
A2  {"protocol":"TRVM-EVIL-v1", … ,"protocol":"TRVM-NESTED-COMPOSITION-v1", …}
                                                    resolveArtifact → ok
                                                    checkNestBundle → VERIFIED, 0 refusals
B   reword ONE annotation on the P1 leaf:
      A.verified_claim_sem_id HOLDS · A.artifact_root MOVED
      C1 / C2 / D  nested_claim_sem_id  ALL MOVED
D   checkNestBundle(chain40, {store})                 → REFUSED
    checkNestBundle(chain40, {store, max_depth:1000}) → VERIFIED, max_depth_below 40
E   directoryStore(CAS_DIR).get("../proof_bundle")    → 1,311,408 bytes, from outside the store
```

All five now: `non-canonical-wire`, `non-canonical-wire`, every semantic name HOLDS,
`nest-policy-weakened`, `bad-root-syntax` with no read attempted.

---

## 2. The wire, and one equality instead of a family of special cases

Resolution requires `received === canonicalWire(parsed)` before it hashes anything. Duplicate names,
key reordering, respelled numbers and whitespace die there together — and **duplicate-key rejection
is a consequence rather than a check**: canonical output emits every key once, so bytes containing a
repeat can never equal the canonical form of what they parse to. I preferred that to a rule naming
duplicates, because the rule that names duplicates is the rule that misses the next thing.

**The tree has ONE canonical encoder and it is now measured against the standard.** `canonicalWire`
IS `canonicalBytes` — a second implementation would be two things called canonical that nothing
compared. `jcs_vectors.mjs` runs it against published RFC 8785 data, **3/3**: the RFC's own
§3.2.2/§3.2.3 worked example, the reference suite's `french.json`, and a **UTF-16 code-unit ordering**
vector where U+1F602 — surrogate pair, first unit D83D — must precede U+FB33, which is the vector a
code-point implementation fails and every surrogate-free vector misses.

**Three vectors are not the reference suite and I do not claim full conformance.** `weird.json`'s
U+0080 and U+007F members are deliberately absent: I could not transport them here verbatim with
confidence, and a conformance vector that might be wrong is worse than one that is narrow. If you
want the real gate, the reference suite as a file drop is the cheapest way to get it.

---

## 3. Reference is not claim — and the positive property is the deliverable

Five planes, each answering one question, and a sixth that is not in the artifact:

```
claim        WHAT is asserted        connective · scope · operands (NO address)
chain_ids    UNDER WHICH COMPILERS   derived from the children
references   WHERE THE BYTES ARE     verified_claim_sem_id → artifact_root
aggregate    WHAT EVIDENCE HOLDS     verdicts, and the parent's own zeroes
structure    WHAT SHAPE THE DAG IS   edges, unique artifacts, bytes, height
—            VERIFIER EXECUTION      reported by the checker, in no artifact
```

Measured after the repair, and this is the form that establishes the law rather than refusing its
negation: reword one annotation on the P1 leaf and **10 semantic names hold** — every claim id,
aggregate id and certificate id at all three composition levels — **while 4 addresses move**, and the
rebuilt DAG verifies.

**Operational counts left the artifact**, and the test I used is strategy-independence:
`films_below_by_edge_multiplicity` (404, what a walk of every edge would replay) and
`films_below_distinct` (138, what the distinct artifacts hold) are properties of the DAG;
`checker_evaluations` is a property of a run and no artifact can be right about it. Separating the
planes creates the one thing separation always creates, so operands and references are matched as
SETS and `nest-reference-mismatch` is a code.

Record-shape change, therefore a protocol revision: `TRVM-NESTED-COMPOSITION-v2`. That is
`semantic-vocabulary-closed@1`'s own rule applied to the protocol written under it.

---

## 4. Q1 taken, and P4 was wrong in the cautious direction

Three phases: RESOLVE into a verifier-owned snapshot, JUDGE each distinct artifact once, WALK every
edge. Your framing is the one I should have used — the distinction is not how long a cached verdict
lives, it is **whether anything was believed**, and running the same pure check four extra times was
never soundness.

Measured on a forged DAG as well as an honest one, because agreeing about a PASS is the easy half:

```
honest   VERIFIED both ways   reuse ON 4 evaluations + 2 reuses = 6 edges walked   OFF 8 + 0 = 8
forged   REFUSED  both ways   reuse ON 4 + 2 = 6                                   OFF 8 + 0 = 8
```

Identical verdicts and identical refusal SETS. `edge_traversals` always equals
`checker_evaluations + derivation_reuses`, so the accounting checks against itself — the first draft
counted only leaf calls and did not, which is how I noticed.

`persistent_warrant_hits` is reported and is 0, because there is no object in this tree that could
make it anything else.

---

## 5. The policy, and the half of it I would not have written

`law:proof.verifier-policy-owned@1`: a caller may tighten, a weakening request is the named refusal
`nest-policy-weakened`, and the effective policy carries an identity reported beside the verdict.
Six bounds, since an untrusted store supplies arbitrarily deep, wide and large artifacts.

**And the tightening test found a second defect immediately.** `max_depth: 2` accepted the honest
height-3 DAG, because the resolver only descends into COMPOSED artifacts and so reached recursion
depth 2 while the DAG's height is 3. **A ceiling on citation chains is about HEIGHT, not recursion
depth.** Every edge is checked as `depth + 1 + height(child)`, which is a property of a node rather
than a path and therefore composes with reuse. I would not have written the tightening case if you
had only asked me to refuse the weakening one.

---

## 6. The finding I did not expect, and it is an argument for your ordering

**The canonical wire walked straight into a latent defect in P1 and P2.** Both compared receipts with
`JSON.stringify(a) !== JSON.stringify(b)`, which is **key-order sensitive**. Storing the P1 bundle
canonically sorts its keys — and P1's own checker then refused its own artifact with
`proof-receipt-replaced` on every case. Semantically identical, serially different.

**Any independently implemented producer emitting another key order would have hit exactly this**, and
it sat in two shipped checkers for four rounds. Seven comparisons are canonical now; no identity
moved, because the identities already ran through `canonicalBytes` and only the comparison disagreed
with them. I am flagging it rather than burying it because you told me not to alter P1/P2/P3 silently
— this alters a comparison and no identity, and it was forced: without it the leaves cannot be stored
canonically at all.

---

## 7. Q2 investigated, and the answer is measurable

You asked whether the flattened `leaf_chains` is logically required or derived metadata. Change a
leaf's compiler:

```
A.verified_claim_sem_id                            MOVES
parent nested_claim_sem_id (contains NO chain)     MOVES     ← the operand alone propagates it
parent derived chain_ids                           MOVES
a chain-less parent is CITABLE                     NO — certificate-incomplete: chain_ids
```

**Redundant for BINDING, load-bearing only for CITABILITY.** The parent needs *a* `chain_ids` field to
be nameable at all, not because anything downstream reads it — which is an argument for your
checker-derived citation-subject interface rather than for keeping the flattened set. I have not built
it: it changes `certificate.mjs`, which P1, P2 and P3 share, in a round that already revises a
protocol. Filed as the shape of the P3 v2 / migration round.

Q3 taken as you ruled: annotations stay in complete-artifact identity and are out of claim identity.
F taken: the cycle claim now states the bounded experiment — 512 attempted fixpoints, 512 distinct
roots — and explicitly does not claim SHA-256 has no fixed point for this encoding.

---

## 8. One instrument finding, and three questions

**The grid probe threw on a shorthand slip and failed closed.** `{ aggregate, structure }` where the
local was named `agg`, so `synthDag` raised and **all six behavioural booleans read false at once**.
Right direction, still a gate you must read twice — six simultaneous falses are a bug in the
instrument, one false is a defect. Worth a rule: a behavioural block should probably report *why* it
returned false, not only that it did.

**Q1 — the independent producer, and what it should be allowed to import.** Your constraint is that it
must not import the JS canonicalizer, bundle builders or schemas, and must implement from frozen
protocol text. **The protocol text does not exist yet.** The grammar, scope, child table, reference
contract, chain derivation and policy are all declared inside checkers as executable data, and the
spec states none of them. So the first half of that round is writing the wire specification — which is
also the only real test of whether P4.1's five planes are describable rather than merely implemented.
Do you want that as a document in this tree, or as the producer's own README derived by reading the
checkers, so that a disagreement between spec and code shows up as a disagreement between two humans
rather than one?

**Q2 — which language, and does it get its own JCS?** A second JS implementation shares Node's
`JSON.parse` and its duplicate-key resolution, which is exactly the hazard I closed by construction
rather than by test. A producer in a language whose parser keeps the FIRST duplicate would make that
hazard *observable* instead of theoretical. That argues for Python or Go over TypeScript, and against
reusing any JCS library that was validated against the same vectors I used.

**Q3 — should the independent producer be given a REFUSING artifact to reproduce, not only a passing
one?** Every cross-implementation test I can think of checks that two implementations agree about a
VERIFIED artifact. The sharper test is whether they agree about *which refusal code* a forged artifact
draws — that is where a protocol's semantics actually live, and where two implementations that agree
on the happy path routinely diverge.

Backlog unchanged: source-refusal ↔ instantiation-refusal preservation · canonical-locus alias
PRECEDENCE · C-side replay · `film-too-many-frames` has no positive witness · `len` unencoded · the
`gov-*` recipe pipe/exit-status sweep.
