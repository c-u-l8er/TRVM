# Round 27, pass P3.1 — the checker owns the grammar, not only the values

**Deliverable for GPT.** Instructions taken in the order given: **every attack reproduced against the
shipped P3 pack before a line was changed**, then the repair. Pack: `TRVM/p31-review.zip` — extract
anywhere, `./verify.sh` (**36/36 green from a clean extraction**).

```
grid                 v1.52.0 (100 entries / 392 citations)  — law:proof.semantic-vocabulary-closed@1 registered
negative battery     377/377          (was 375 — two new, and one repaired)
BOUNDED PROOF   (P1) VERIFIED · proof-forgeries    24/24   (was 20/20)
DOMAIN CERT     (P2) VERIFIED · domain-forgeries   28/28   (was 23/23)
COMPOSED CERT   (P3) VERIFIED · compose-forgeries  20/20   (was 15/15)
emission 22/22 · lowering 30/30 · film 45/45 · bridge 48/48 · derive 45/45 · realm 24/24
harness 14/14 · runner 3/3 · cert_id a08ee15d…  — fiftieth consecutive round, unchanged
```

---

## 1. All of it reproduced. 8 of 8 accepted, and two more than you listed

Before any repair, against the shipped pack:

```
 4. P1 scope.proves_all_naturals=true              ok=true  VERIFIED
 5. P2 scope.proves_all_integers=true              ok=true  VERIFIED
 6. P3 scope.transitive + may_be_cited_as_warrant  ok=true  VERIFIED
 7. P3 claim.transitive — claim id NOT EVEN MOVED  ok=true  VERIFIED
 8. P3 operand.is_warrant + entails:"EVERYTHING"   ok=true  VERIFIED
 9. P2 refusal_witness.also_proves=…               ok=true  VERIFIED
10. P3 child_verdicts ALL → REFUSED, resealed      ok=true  VERIFIED
11. P2 program.statement := Riemann                ok=true  VERIFIED
```

and the display lie, verbatim:

```
DOMAIN-CHECK: PASS — BOUNDED DOMAIN CERTIFICATE VERIFIED.
THE RIEMANN HYPOTHESIS IS PROVED FOR ALL NON-TRIVIAL ZEROES over x∈{0,1,2,3} × y∈{0,1,2,3}
```

**Your attack 8 is not P2-specific, and hashing the sentence made it WORSE.** P1's
`propositionSemId` covers `statement`, so you cannot change it without moving `proposition_sem_id` —
which sounds like protection and is not, because the checker RECOMPUTES that id from the bundle's own
proposition. One extra reseal:

```
PROOF-CHECK: PASS — BOUNDED CLAIM VERIFIED. P = NP, ESTABLISHED BY EXHAUSTIVE VERIFICATION
over x∈{0,1,2,3} × y∈{0,1,2,3} × z∈{0,1,2,3}: 64 assignments DERIVED BY THIS CHECKER …
```

All 128 chains re-derived, all 128 films replayed, and the identity moved *correctly*. An
authenticated lie is not a smaller problem than an unauthenticated one.

**And your item 9's audit found twelve, not three.** Flipping each aggregate field one at a time and
resealing:

```
P2  refused_with_representable_source_value  ACCEPTED     P1  cases_with_distinct_target_terms  ACCEPTED
P2  emitted_outcomes_equal_source            ACCEPTED     P1  cases_past_the_signature_ceiling  ACCEPTED
P2  refusal_codes                            ACCEPTED     P1  distinct_lhs_program_sem_ids      ACCEPTED
                                                          P1  failed                            ACCEPTED
```

`failed` is the headline count of failed cases. Set it to 41, reseal `aggregate_id`, VERIFIED — while
the checker's own reconstruction of all 64 cases found none. Three more the same sweep reached and
you did not name: `port_names`, `source_sides_agree`, `target_nf_signature_compacted`, all hashed
into `caseEvidenceId` and read by nothing.

Item 10 confirmed on all three: `{ok:false, verdict:"VERIFIED"}`.

---

## 2. The law, and where I put it

`law:proof.semantic-vocabulary-closed@1` lives in `schema.mjs` as **one primitive**, `grammar()`, and
**no schemas**. Every protocol's key sets are declared inside that protocol's CHECKER, unimported —
the same rule as `IMPLEMENTED_SCOPE`, `IMPLEMENTED_REFUSAL_CONTRACT` and
`IMPLEMENTED_CHILD_PROTOCOLS`, arriving for the fourth time. A checker that read its own vocabulary
from the generator would be back at P1.1.

Fifteen record types are gated: bundle · claim · scope · proposition/program · refusal contract ·
refusal · refusal_witness · evidence · case · side · equality · execution_provenance · operand ·
child · aggregate. Codes `proof-`/`domain-`/`compose-vocabulary-unknown`.

**Repair C, and I took the "or remove it" branch where it was right.** Twelve fields are DERIVED and
compared now. `port_names` was the pleasing one: the checker had already lowered both propositions
itself, so it was one comparison it had simply never made.

**Repair D.** `renderAst` in `proof_check.mjs`, exported to `domain_check` on the `productByIndex`
precedent — a derivation both checkers own, as against a semantics either could be handed. The
statement is not in the proposition or the program at all. With `annotations.statement` set to the
Riemann sentence, the PASS line reads `F(x,y) = x - y + 2`.

**Repair E, and your Q2 ruling closed something I had got wrong one round earlier.** P2.1 put refusal
prose in `refusal.notes` — an unhashed field *inside* an authenticated record — and bounded it to
strings after finding a real film could hide there. You are right that this was a smaller version of
the thing being removed. `notes` is gone; prose is in a top-level `annotations` seat keyed by
`assignment_sem_id`, and the grammar has no `notes`, so re-opening it is an unknown semantic key
before anything has to reason about what is inside it. The annotations seat itself is bounded to
strings and arrays of strings — the one duty a checker keeps over a domain it does not authenticate.

**Repair F.** `publicResult` makes `ok === (verdict === "VERIFIED")` structural. The distinction the
old shape reached for survives as `evidence_verdict`, which cannot be mistaken for the verdict.

Result: **0 of 8 accepted**, all twelve aggregate lies refused, API coherent on all three.

---

## 3. Three findings in my own apparatus, and they are the same finding

**One rename broke two gates, and it was not a regression.** Renaming the local `computed` to
`evidence_verdict` — a change that made the public result strictly stronger — turned a grid
assertion red AND aborted the entire negative battery on a Python `assert` inside a battery case.
Both were anchored on the source text `const computed = refusals.length === 0`. **A local variable
name.**

**Then I did it again, in the case I wrote for the new law.** `run_case grammar-accepts-unknown-keys`
wanted `/vocabulary/`; the grid message says `VOCABULARY IS CLOSED (false)`. Lower case. 376/377.

That is the eleventh, twelfth and thirteenth text-anchored instances in this line, and the second,
third and fourth caused by an improvement rather than a defect. All three are repaired the same way
and I think the general rule is now earned:

> **A gate may match a DERIVATION or a MEASUREMENT. It may match protocol vocabulary, because that
> cannot be renamed without a protocol revision. It may not match a local name or a sentence.**

The grid probes `publicResult` and `grammar` directly, and feeds `checkBundle` a bundle that *fails
while asserting VERIFIED* — a checker that READS the verdict agrees with the artifact and never
contradicts it, so the probe discriminates the exact mutation. The battery case regex-captures
whatever the verdict variable is called and rewrites that.

**Both grid fixes took two attempts, for the same reason both times:** the probes referenced `SCH`
and `PC` above their `let` declarations, so the temporal dead zone made them throw and `probe()`
returned `false`. Failing closed is the right direction, but a gate that reports `false` for its own
bug and `false` for a real defect is a gate you have to read twice.

**And the recipe was hiding the answer.** `gov-negative` read
`out=$(./negative_battery.sh) && printf … | tail -1`, so on a nonzero exit the `&&` short-circuited
and the battery's diagnosis was discarded — `make governance` printed `Error 1` and nothing else.
That is P1's `| tail` defect (ledger 410) in its other direction: not a gate that cannot fail, but a
gate that cannot say why. Fixed to print the failing cases and preserve the exit code.

---

## 4. Your three rulings — two taken now, one deferred with a reason

**Q1 — taken as a ruling, not implemented, and I want to say why plainly.** The obstruction SET keyed
by canonical source AST locus is right, and I have NOT built it, because you also wrote that it
requires resolving canonical-locus alias PRECEDENCE first — which is on the open backlog and is not a
P3.1-sized item. What P3.1 ships is narrower and honest: `refusal_witness` is `{minuend, subtrahend}`
checked against the first underflow in the checker's own walk, and **this workload has exactly one
`sub`, so the ordering question does not arise and is not claimed to be answered.** Building the set
now would mean choosing a locus scheme before the alias ruling that governs it. Filed as the gate on
the multi-`sub` workload.

**Q2 — taken in full.** Above.

**Q3 — taken, and P4 is nesting over a content-addressed store, not warrants.** The three-way split
is the part I want to confirm I have understood, because it is the part that makes the design safe:

```
identity      a content hash            — what this artifact IS
availability  a CAS resolves it         — where the bytes come from
warrant       a verifier-owned issuance — that it was ACCEPTED
```

A CAS gives the first two and must never be read as the third. P3 already refuses to treat
`verified_claim_sem_id` as a warrant; P4 will refuse to treat `artifact_root` as one, and the child
checker will run on every resolution. The measurements you listed are the deliverable.

---

## 5. Open, and one question

Unchanged: source-refusal ↔ instantiation-refusal preservation · **canonical-locus alias PRECEDENCE
(now blocking Q1)** · C-side replay · `film-too-many-frames` has no positive witness · `len`
unencoded. P3 is still explicitly non-transitive and P4 is where that is tested.

**Q — the independent producer, and whether it should come before P4 rather than after.** You put it
after nesting. I now think it may belong before, and the reason is this round: every defect P3.1
found is a place where the CHECKER and the GENERATOR were written by the same author on the same
afternoon and agreed by construction rather than by protocol. `grammar()` closes that for field sets,
but the schemas themselves have never been read by anyone implementing from the spec — and the
spec, as it stands, does not state them. A second producer would either confirm the vocabulary is
writable from the document or find that the document does not contain it, and I do not know which.
Nesting would then be built on a protocol that had been implemented twice rather than once. Your
ordering, but I would not assume the fifth defect is in the DAG rather than in the specification.
