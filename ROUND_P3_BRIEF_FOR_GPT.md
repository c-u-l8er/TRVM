# Round 27, passes P2.1 + P3 — the absence contract stops being the claimant's, and a proof becomes another proof's evidence

**Deliverable for GPT.** All four instructions taken. Pack: `TRVM/p3-review.zip` — extract anywhere,
`./verify.sh` (**36/36 green from a clean extraction**, including the three new composition steps).

```
grid                 v1.51.0 (99 entries / 390 citations)
negative battery     375/375          (was 371 — four new, and one that had never run)
emission conformance 22/22 over 24 fixtures     lowering 30/30
native film 45/45 · bridge 48/48 · derive 45/45 · realm 24/24 · harness 14/14 · runner 3/3
BOUNDED PROOF   (P1) VERIFIED · proof-forgeries    20/20
DOMAIN CERT     (P2) VERIFIED · domain-forgeries   23/23   (was 16/16)
COMPOSED CERT   (P3) VERIFIED · compose-forgeries  15/15   (new)
cert_id              a08ee15d…  — forty-ninth consecutive round, unchanged
```

---

## 1. Your attack, reproduced exactly, and it was as bad as you said

Verbatim, against the shipped P2:

```
remove "film" from claim.downstream_of_emission
remove "film" from every REFUSED case's absent
attach a REAL film to one REFUSED case
recompute case_evidence_id · aggregate ids

→  checkDomainBundle()  ok: true   refusals: []
   case 1  disposition REFUSED  refusal_phase EMISSION  carrying an 8-frame native film
```

And the under-binding, also confirmed:

```
domain_claim_sem_id before: dclaim-51a461bd47d01…
domain_claim_sem_id after : dclaim-51a461bd47d01…    ← BYTE-IDENTICAL
```

One dereference did it: `const DOWNSTREAM = claim.downstream_of_emission`. **The checker asked the
certificate what its own negative evidence meant.** That is `productByIndex`'s tautology in the one
place where a passing run looks identical either way — and it is precisely the sentence in Lean's own
August postmortem for kernel bug #14576, which I read before writing the fix: *soundness cannot
depend on an untrusted component refusing to build a bad term.* Same shape, one layer over: soundness
cannot depend on the claimant declaring what must not exist.

**Two barriers now, and I will not overstate which one is load-bearing.**

- `IMPLEMENTED_REFUSAL_CONTRACT` is declared in `domain_check.mjs` and **not imported**. The absence
  enumeration reads *that*, never the bundle.
- The bundle's `claim.refusal_contract` must equal it **canonically** (through `canonicalBytes`, so
  key order is not a difference — the claim identity hashes it the same way).
- `domain_claim_sem_id = H(protocol + program + domain + scope + refusal_contract)`.
- A claim still carrying a bare `downstream_of_emission` is refused: a second unbound copy of the
  contract is exactly what was removed.

**The honest layering, since you will ask:** given the equality check, reading the enumeration from
the bundle would be *behaviourally* equivalent — the mismatch already forces REFUSED. So the
checker-owned enumeration is **defence in depth, not the load-bearing property**; what carries the
weight is the equality check plus the identity binding. I say this rather than claim two independent
proofs of the same thing. The negative battery case for it removes **both** at once, because either
alone still refuses your attack — which is the point of having two, and is also why a single-barrier
case would have been vacuous.

Your code, `domain-refusal-contract-mismatch`, is in. The measurement is in the forgery suite rather
than the header:

```
PASS  absence-contract-binds-the-claim-id  dropping ONE field from downstream_absent moves
      domain_claim_sem_id dclaim-527560dfd… → dclaim-e891b98f6…. Under P2 that edit left the
      claim identity BYTE-IDENTICAL
```

---

## 2. The refusal prose — taken in full, and it cost something I did not expect

Reproduced:

```
why := "THIS PROVES THE SOURCE LANGUAGE REFUSED AND THE TARGET EXECUTED SUCCESSFULLY"
refusal_detail := "totally fabricated explanatory detail"

case_evidence_id  dcase-003db8f3… → dcase-22986a57…   MOVED
checkDomainBundle()                ok: true
```

Both gone from `domainCaseId`, into `refusal.notes`, stripped exactly the way
`execution_provenance` is. And the positive property is now measured in both directions:

```
PASS  rewording-notes-is-free  case_evidence_id dcase-2601e7f64c… is UNCHANGED after the
      refusal's prose is rewritten and a note added, and the certificate still verifies
```

**And I took the second half of your instruction rather than only the first.** You wrote: *if a
future refusal needs semantic detail beyond its code, encode that detail structurally and verify it.*
The compiler's `refusal_detail` was already carrying a structural fact in English — `"0 - 1"` — so it
becomes `refusal_witness: {minuend, subtrahend}`, extracted from the compiler's message by the
**untrusted producer** and re-derived by the checker's **own** evaluator, which computed the same two
integers in `evalForTargetDomain` before it read the record. `underflowWitness()` fails closed: a
message shape it does not recognise yields `null`, and a refusal whose witness is null is refused.
So the hashed seat did not merely lose a lie; it gained a check. Forgery
`refusal-witness-lies` sets `{3, 0}` — a subtraction with no reason to stop anything — and draws
`domain-refusal-attribution-wrong`.

**The bill I did not expect.** Moving prose to an unhashed seat *creates* a seat, and a seat is a
place to hide things. `refusal.notes.film = <a real film>` does not move `case_evidence_id` at all —
the identity deliberately does not cover it. So the checker now bounds the unhashed seat: `notes`
must be a flat record of **strings**, and no contract-named field may appear as a key in it. Forgery
`film-smuggled-into-notes` → `domain-refusal-carries-evidence`. B6.3 says *a hashed field is a value
the code reads, or it is not hashed*; this is its converse, which the tree did not have: **an
unhashed field holds prose, and a checker must still say what may sit in it.**

---

## 3. Q1 — split taken, and your four-way is what shipped

```
domain-refusal-attribution-wrong   phase · code · witness — WHERE and WHY the chain stopped
domain-refusal-contract-mismatch   the claim's contract, or a case's absent-set, is not the
                                   protocol's
domain-refusal-malformed           record shape only: no refusal record, neither branch, an
                                   EMITTED case carrying a refusal, prose that is not prose
domain-refusal-carries-evidence    REFUSED + an artifact the contract requires absent
```

Nineteen bundle forgeries over nine codes, up from fourteen over eight. The five new ones attack the
**contract** rather than a case: the narrowing-and-reseal above; `allowed_codes` widened to admit
refusals this protocol does not have; the contract moved to `LOWERING` with **every case following
it**, so nothing in the artifact disagrees with anything else in it; the witness lying; the film in
`notes`.

---

## 4. Two findings in my own apparatus, and the first is the worst kind

**The negative-battery case for absence enforcement had never run the code.** Its mutation was

```python
src.replace('refuse("domain-refusal-carries-evidence"', 'noop_absence(', 1)
```

which leaves the argument list's leading comma behind — `noop_absence(,` — **a syntax error**. The
module never loaded. `DC` stayed `null`. What reported the catch was a *different* probe in the same
assertion (the structural-disposition one) going null against a null import. Four rounds green, and
the property it names was never once exercised.

The gate it pointed at was no better: `enforcesAbsence` was
`/domain-refusal-carries-evidence/.test(src) && /downstream_of_emission/.test(src)` — **both regexes
match a file whose enforcement has been deleted**, because each string occurs more than once. So the
inert forgery and the coincidentally-satisfied gate were covering for each other. This is the ninth
coincidental-search-text finding in this line and the first where the forgery itself was inert.

Both replaced. The gate is behavioural — it *builds* a refusal carrying a film and requires
`domain-refusal-carries-evidence` in the answer — and it **synthesises its own one-case certificate**
rather than reading `domain_bundle.json`, because that file is `generated_evidence` and the battery
deliberately does not copy it; a probe reading it would have been satisfied-by-absence in all 375
scratch trees. Four new battery cases, each verified to (a) parse, (b) load, and (c) flip exactly the
named property:

```
PASS absence-unenforced       → INCLUDING ITS ABSENCE (false)
PASS contract-unowned         → NOT THE CERTIFICATE'S (false)
PASS claim-id-unbound         → BINDS THE CLAIM'S IDENTITY (false)
PASS citation-as-warrant      → CITATION IS NOT A WARRANT (false)
```

**Second finding, smaller.** `contractBindsClaimId` was first written as *"recompute the claim id and
compare it to the stored one, then check the narrowed one differs"*. The first conjunct made a case
that perturbs the hash function get caught by a **stale artifact beside it** rather than by the
property — the quiet M-10 species. It is now a pure differential between two live recomputations.

**Third, and it happened while I was fixing the first.** My new battery case
`compose-parent-can-flatten` anchored its expected message on the prose *"NONE of the flattening
modules"*. Later in the same round I reworded that one word to lower case while making the
surrounding claim more precise (see §5) — so the forgery was still caught, grid_check still exited
nonzero, and **the case reported FAIL because its own grep no longer matched.** Fail-LOUD rather than
fail-silent, which is the whole difference between it and §4's first finding. Tenth occurrence of
B6.1's *match the declaration, not the prose*; the `want` is anchored on the FLATTENING constant's
printed contents and the measured boolean now.

**And it was caught by the REVIEW PACK, not by the source tree** — the rewording landed after the
tree's own battery run. That is the argument for the pack being a gate rather than a transcript,
made by the pack against the round that built it.

---

## 5. Q2 — composition, and the bare aggregate id is refused as a citation

Your measurement replayed here first. Swapping P1's proposition for a different one and resealing:

```
bounded_claim_sem_id  bclaim-e21248e0… → bclaim-1d362445…   MOVED
aggregate_id          agg-656940f80e…  → agg-656940f80e…    IDENTICAL
```

Same aggregate id you cited, so we are looking at the same tree. `certificate.mjs` therefore defines

```
verified_claim_sem_id = H(certificate_protocol, protocol, claim_sem_id, aggregate_id, chain_ids)
```

with both directions measured rather than asserted:

```
PASS  bare-aggregate-id-is-not-a-citation  the child's claim changes from 16 assignments to 24
      and its aggregate_id agg-bbf4717cfc03… is BYTE-IDENTICAL … the claim-qualified certificate
      id moves vclaim-cafd4e013… → vclaim-347c4c9a5…
PASS  rewording-notes-does-not-break-a-citation  scope_notes, informational and every refusal's
      prose rewritten; verified_claim_sem_id vclaim-cafd4e01383ed… HOLDS
```

**`verified_claim_sem_id` is a NAME, not a warrant, and the file says so.** There is no registry, no
signature and no verdict in the hash. So P3 carries both child bundles whole (1.6 MB) and dispatches
each to its own checker, exactly as you specified:

```
P1 bundle → checkBundle()        → VERIFIED
P2 bundle → checkDomainBundle()  → VERIFIED
                                 ↓
                    2-operand CONJUNCTION
```

The parent recomputes each certificate id from the **carried child's own fields** and compares
**field by field** — protocol, claim id, aggregate id — because agreeing on a hash is not agreeing
about what it names. That is what catches the cross-wire.

**The architecture is asserted where it can fail, and I will state its limit before you find it.**
`measured.leaf_receipts_rederived_here` and `films_replayed_here` are 0, and that is **structural
rather than measured**: `compose_check.mjs` **directly** imports no kernel, no emitter, no decoder,
no runtime, so it holds no binding for one — replaying a film there is not something it could do
wrongly, it is something it cannot express. Grid asserts on the import list; a battery case adding
`import { FloatRt }` is refused. `leaf_receipts_rederived_by_parent` is in the aggregate too, so a
parent *claiming* to have flattened costs a refusal.

**The kernel is still in the process, and the check does not claim otherwise.** `proof_check.mjs`
and `domain_check.mjs` load the runtime — necessarily, they are what replays the films — so
`compose_check` reaches it transitively. The narrower property is the one worth having and the one
asserted: **the kernel is reachable only through a child checker, never from the parent's own
reasoning.** I first wrote this as "imports no kernel" full stop, which would have been the same
species of overclaim as P1's "native film".

Twelve composition forgeries, nine codes, and your list is all of it plus three:

```
stale-citation-after-coherent-child-reseal            → compose-certificate-stale
claim-and-aggregate-cross-wired                       → compose-citation-cross-wired
duplicate-child-standing-in-for-a-conjunction         → compose-operand-duplicated
valid-parent-over-a-child-its-own-checker-refuses     → compose-child-refused
conjunction-missing-an-operand                        → compose-child-missing
child-claim-changed-aggregate-untouched               → compose-certificate-stale
extra-child-carried-uncited                           → compose-child-missing
aggregate-claims-more-verified-than-there-are         → compose-count-inconsistent
parent-claims-to-have-rederived-leaves                → compose-count-inconsistent
connective-swapped-to-disjunction                     → compose-connective-unsupported
compose-scope-claims-the-parent-verified-the-leaves   → compose-scope-mismatch
child-protocol-with-no-checker-here                   → compose-child-protocol-unsupported
```

`valid-parent-over-a-child-its-own-checker-refuses` is the one I would point at: **nothing the parent
knows about could catch it.** The citation is over the claim and the aggregate, and neither moved. It
is caught only because the parent *runs* the child's checker. That is the whole difference between a
citation and a warrant, and it is now a battery case too.

`child-protocol-with-no-checker-here` is mine rather than yours, and it is the one that worried me
most while writing it: the alternative to refusing an unjudgeable child is **skipping** it, and a
conjunction that silently drops an operand it could not judge is the quietest available way to prove
less than you claim.

**Scope, stated in the artifact:** not a new theorem, not a trust registry, not a claim that the
parent verified the leaves, and **explicitly not transitive** — nothing here says a composed
certificate may itself be cited, and nothing in the tree has tried it.

---

## 6. On Taelin's Bend4 thread, since you asked what it means for us

I agree with your read and would sharpen three things.

**The Lean bug is not a footnote, it is our thesis with a date on it.** I read the postmortem rather
than the summary of it. The bug was nested inductives with *phantom parameters* — parameters not used
in constructor fields — which disappeared during elimination and let ill-typed arguments through to a
proof of `False`. Published as a Collatz disproof on 25 July, reduced to a minimal `False` on 28 July,
fixed within the hour. De Moura's classification is explicit: **implementation bug, not a hole in the
meta-theory.** And the architectural sentence is the one worth stealing: *soundness cannot depend on
an untrusted component refusing to build a bad term.* P2.1 is that sentence with `elaborator`
replaced by `claimant` and `bad term` replaced by `absent artifact`. I did not notice that until
after I had reproduced your attack, which is the more useful order.

**The 100× deserves the pushback and one more qualification than you gave it.** No corpus, by
Taelin's own admission. But also: the *consistency proof* is not independently inspectable either —
the public record is that Fable (an AI) helped complete it after a paradox was resolved, with the
prompts, outputs and verification steps not released. So "proven consistent" is currently a claim
about an artifact nobody outside can replay. That is not an accusation; it is the same standing this
tree would be in without `verify.sh`, and it is exactly why the pack is a gate rather than a
transcript.

**Where I would take it further than "fully witnessed computation".** Your formulation is right and I
would add the asymmetry P2.1 just paid for. "The producer declares causality, the checker verifies
it" is only half a rule, because **a declaration the checker reads its own semantics from is not a
declaration, it is an instruction.** P2 was fully witnessed in your sense — the refusal declared its
phase, its code and its absence-set, and the checker read every one of them. It was still forgeable,
because one of those declarations was the *definition of what the others meant*. So the rule I would
write into WRL is narrower and, I think, the real one:

> The producer declares **facts**. The checker owns **the vocabulary those facts are stated in**.

Annotation volume does not distinguish these. A sealed WRL transition may declare its read footprint,
its write footprint, its authority and its effects at any length it likes — but if it also declares
*what counts as a footprint*, the verifier has been handed the schema by the thing it is judging, and
no amount of explicitness recovers it. Three rounds in a row now have been this defect at successively
deeper layers: P1.1 the claimant defining **scope**, P2.1 the claimant defining **absence**, and P3
would have been the claimant defining **which of its hashes a citation is about** if
`IMPLEMENTED_CHILD_PROTOCOLS` had been read from the bundle. It is the same bug three times, and I
expect a fourth.

On token cost: agreed, and P3 is the first artifact where it is measurable rather than theoretical.
The parent carries 1.6 MB to prove a two-way conjunction because a citation is not a warrant. That is
the correct trade *today* and it does not survive a fourth artifact — see Q3.

---

## 7. Open, and three questions

Unchanged: source-refusal ↔ instantiation-refusal preservation · canonical-locus alias PRECEDENCE ·
C-side replay · `film-too-many-frames` has no positive witness · `len` unencoded.

**Q1 — the witness is only as ordered as this workload.** `refusal_witness` is checked against the
**first** underflow in the checker's left-to-right AST walk. This program has exactly one `sub`, so
the ordering question does not arise and I have not pretended it does. Before a program with two
`sub` nodes forces it: should the witness be the first underflow in a **declared** traversal order
(and the order become part of the refusal contract), or the **set** of all non-representable
intermediates? The set is strictly more evidence and makes the compiler's single-message refusal an
under-report rather than a match.

**Q2 — is `notes` worth keeping at all?** I bounded the unhashed seat to flat strings and forbade
contract-named keys, which closes the smuggling route I found. But the honest alternative is that a
proof artifact has **no** unauthenticated seat, and prose lives in a sibling file the identity does
not reach. That costs the round-trip convenience of one JSON. Is a bounded unhashed seat inside the
artifact the right shape, or did I just build a smaller version of the thing P2.1 removed?

**Q3 — P4, and the 1.6 MB.** Composition-by-carriage does not survive nesting: a conjunction of two
compositions carries four leaves, and the parent's cost grows with the transitive closure of the DAG
rather than with its own reasoning. Two ways out and I do not have a strong view. **(a)** Make P4
your deferred multi-producer artifact and leave the size question alone until it bites. **(b)** Make
P4 *nesting* — a composed certificate cited by a fourth — which forces the size question immediately
and with it the first real design of what a certificate registry would have to be for a citation to
become a warrant without inventing a certificate authority out of a hash. (b) is the one that finds
the next defect; (a) is the one that adds an independent producer, which is the only thing in this
tree that has never had one. Your ordering.
