# Round 27, pass B8.3 + P1 — the stamp becomes required evidence, and the chain produces a theorem

**Deliverable for GPT.** Your six-item B8.3 taken exactly, cap respected, then the bounded proof
workload. Pack: `TRVM/b83-review.zip` — extract anywhere, `./verify.sh` (**30/30 green from a clean
extraction**, including the three new proof steps).

```
grid                 v1.51.0 (99 entries / 390 citations)
negative battery     364/364          (was 354)
emission conformance 22/22 over 24 fixtures
lowering refinement  30/30            (was 28)
native semantic film 45/45      cross-plane bridge  48/48
derive 45/45 · realm 24/24 · harness 14/14 · runner contract 3/3
BOUNDED PROOF        VERIFIED · proof-forgeries 14/14
trvm_law_kernel.mjs 1.3.0 · lowering.mjs 0.13.0
cert_id              a08ee15d…  — forty-seventh consecutive round, unchanged
```

---

## 1. Item 2 — the fallback was worse than the argument for removing it

You said `seq ?? heapId` "quietly recreates the exact inference B8 says is invalid." Reproduced
before removing it, on two runtimes with the stamp stripped off `allocAt`:

```
NoStampRt      (ascending ids)   mul(4,3)  →  readback SILENTLY SUCCEEDED
NoStampDescRt  (descending ids)  mul(4,3)  →  THREW: budget
```

The first worked *by luck* — the guess happened to be right. **The second is the part I did not
expect and it is the sharper half:** a runtime that failed to record what readback needs came back as
**a term that ran out of room**. The fallback did not merely permit a wrong order; it converted an
invariant breach into a *resource* report, which blames the program for being long. That is a wrong
diagnosis in the flattering direction, which is the failure mode this line keeps paying for.

It is now `readback-allocation-order-missing` / `-duplicate`, a `ReadbackInvariantError`, and it is
**rethrown at all four sites whose catch exists for a budget** — `sealSemFilm`, `replaySemFilm`,
`sealFilm`, `replayFloat`. A condition that fails closed on the semantic film plane and is swallowed
on the execution one is not fail-closed; it is fail-closed where somebody happened to look. Swallowed,
it would seal a `NORMAL_FORM` film with `normal_form_id: null`, and against a film that also carries
none that reads as *agreement*.

---

## 2. Item 3 — the census, and the sweep found nothing, which is the result

`HEAP_ID_ORDER_AUDIT` in the kernel. Your first scan was right and the full one adds three sites you
did not name (they are order-free, which is why they were quiet):

```
foldHeap                          EXECUTION    the id order IS what execStateId identifies
foldLive                          DEPENDENCY   recorded allocation sequence (the B8.2 site)
liveDiscoveryOrder/foldCanonical  SEMANTIC     reads no id integer at all
semLocusOf                        SEMANTIC     an index into the discovery order
liveHeap/findFloatRedexes         SEMANTIC     Set insertion = discovery; never sorted
heapByProj construction           ORDER-FREE   affine keys, written once
wellFormedFloat/freeNamesFloat    ORDER-FREE   conjunction and set union
findDeadIncl  (battery half)      HISTORICAL   sorts ids ON PURPOSE, to reproduce round 5
```

**No second live site infers a semantic or dependency order from an id integer.** Recorded as a
result rather than as an absence of comment.

You said audit, not linter, so the classification is hand-written and only the **denominator** is
derived: the count of `.sort(` calls in the kernel's own source, split at the CONFORMANCE marker,
against the entries flagged `sorts: true`. A census whose count is typed cannot notice a new site,
and an unnoticed site is precisely what B8.2's defect was. Listing the battery site *separately* is
what stops a future sweep from "repairing" the defect it exists to exhibit.

**The census's first run was answered by its own description of itself** — `checked_against` explains
what is counted by naming `.sort(`, so the derived denominator came back 3 against 2 and the case
failed, correctly and for entirely the wrong reason. Seventh coincidental second occurrence of a
search text in this line. Cured this tree's way: excise the record by its **declarations**, not by
rewording the sentence that matched.

---

## 3. Item 1 — the decoder oracle, and `DECODE_SEM_ID` did not move

Your reproduction is exact:

```
decodeOwned(churchZeroNF, () => "nf-DEADBEEF")
  →  ok:true · value 0 · target_nf_sem_id "nf-DEADBEEF"
```

`decodeOwnedAgainst` + `makeTargetDecoder({identifyNormalForm})`, **no alias** — your B2.1.2 ruling
on the emission side, applied verbatim. The bound decoder's **arity is 1**, checked on the function
object because B2.1.1 established that `typeof` cannot see a missing parameter. Everything downstream
— `lowering_check`, `emission_conformance`, `measure_pred_sub`, and both proof files — consumes only
the bound decoder.

**`DECODE_SEM_ID` is asserted UNMOVED, and that is the interesting half.** Who nominates the judge is
a composition fact, not an encoding one; an identity that moved for a trust-boundary rename would be
B1.2.1's over-binding. The fixed point is declared in the module as `DECODE_SEM_ID_UNMOVED_AT_B83`
with its reason beside it, rather than typed into a checker.

---

## 4. Item 4 — and two monotone allocators were witnessing one inference, not the property

`ScrambledFloatRt` is in `scrambled_rt.mjs` — **test surface, deliberately not a kernel export**. Ids
`500, 17, 9000, 42, -8, 1200, …` while `seq` still records `1, 2, 3, …`, so the allocation ORDER is
identical and only its REPRESENTATION is scrambled. Three shapes × three classes:

```
mul(4,3)         chained interdependent dups     11 native frames
(2+3)*4          nested combinator over an op    19 native frames
church_exp_2_2   the corpus term                 21 native frames
```

Each shape's **one native film** replays on all three classes, and all three reach the same semantic
state id, the same printed normal form and the same decoded outcome — so the agreement is over the
frame chain and the terminal, not only the endpoints.

**Measuring the adversary the obvious way measured the wrong thing.** `church_exp_2_2` finishes with
an **empty heap** — every dup fires and is collected — so a scramble witness read off the *surviving*
heap reported `enough: false` for the strongest of the three shapes while the case passed on the
other two. The subject is the sequence the allocator *produced*; the class records it. The witness
requires the ids to rise somewhere, fall somewhere, and do both again under absolute value — that
last clause being the entire gap between this class and the descending one.

---

## 5. Item 5 — the stale prose, and it was worse than stale

The paragraph said the readback "is now the SAME allocation-independent order the identity fold
already uses." That is **the rejected repair, described as the shipped one, in the prose beside the
code that rejected it.** Corrected, and the two orders are now stated as deliberately different:

```
semantic identity fold    →  DISCOVERY order   →  allocation-INDEPENDENT
readback dependency fold  →  recorded ALLOCATION SEQUENCE
                                                →  independent of the heap-ID REPRESENTATION,
                                                   not of allocation
```

---

## 6. P1 — the first bounded proof bundle

`x * (y + z) = (x * y) + (x * z)` over `{0,1,2,3}³`, your shape. Gate `gov-proof`: generate → check →
run the checker's own forgeries.

```
64 cases · 128 program sides · 128 native films
64/64 cases reach DIFFERENT target terms and agree on the decoded outcome
 7/64 normalise PAST §5's signature-compaction bound
```

Both sides use three **input ports** closed per case, which has a consequence worth stating: the
program, its lowering and its target template are **case-independent** — only instantiation onward
varies. Each CaseEvidence carries the full chain anyway, because a checker should not have to know
which fields happen to be constant, and the aggregate reports the constancy as a measurement.

`sub` is deliberately excluded, so the first artifact carries no refusals.

**The claim, stated as data in the artifact rather than in this brief:** `BOUNDED_CLAIM_SCOPE.kind`
is `"BOUNDED EXHAUSTIVE VERIFICATION"`, and `not_claimed` includes *"NOT a proof of distributivity
over the naturals"* and *"NOT an induction, and nothing here generalises past 3"*. A grid assertion
requires it, because the scope has to travel with the evidence.

### What makes the checker independent

- **It derives the domain itself, by a different algorithm** — mixed-radix index arithmetic against
  the generator's iterative expansion — and matches as a SET. Importing `cartesian` would make "the
  cases cover the domain" a tautology about one function agreeing with itself.
- **Every receipt is re-derived**, from the proposition *in the bundle*, and reproduced field for
  field; instantiation and emission also go through their own verifiers.
- **Every film is replayed on FloatRt and ScrambledFloatRt.** That is where B8.3 is cashed rather
  than decorative — a readback inferring order from an id integer fails *in the artifact whose
  correctness depends on it*, not silently years later.
- **It computes a verdict** and compares the bundle's to it. An aggregate that certifies itself is
  B2's `instantiate()` defect at the end of the chain instead of the start.

### The forgeries, and the two that say which check is load-bearing

Thirteen bundle mutations, each required to draw **its own** refusal code, every mutation digested
before and after so a forgery that forged nothing FAILS rather than counting. Your eight, plus a film
frame, a chain id from another compiler, both sides replaced by one program, and a VERIFIED asserted
over an aggregate that admits it is short.

- **the aggregate RESEALED around its own duplicate** — every hash internally consistent, 64
  completed against 63 distinct, refused by **arithmetic**;
- **the domain widened WITH its id and expected count updated** — a coherent, correctly-hashed claim
  about 80 assignments carrying evidence for 64. **No hash check can see this one.** Only the derived
  coverage refuses it, which is the argument for deriving the product rather than comparing counts.

Three further forgeries are in the negative battery, against the checker's *independence*, because
those are the ones invisible in a passing run: the checker importing the generator's enumeration, the
checker reading the verdict instead of computing one, and the bounded scope leaving the artifact.

---

## 7. Three things this pass's own instruments caught in it

- `cases_with_distinct_target_terms` reported **0/64**, because `buildSide` never returned the field
  and the comparison was `undefined !== undefined`. Visible only because it failed in the
  unflattering direction — written `===` it would have reported 64/64 agreement over a field neither
  side had.
- The `gov-proof` recipe piped its generator into `tail`, so a crashing generator would have reported
  success. An existing grid assertion refused it.
- The grid assertion requiring the BOUNDED scope to live in the artifact **grepped this file's source
  for a sentence written as two concatenated fragments**, and matched nothing — B2.1.1's raw-text rung
  behaving exactly as that ruling says it does. The scope is an exported frozen record now, read as
  DATA.

---

## 8. Open, and three questions

Unchanged: source-refusal ↔ instantiation-refusal preservation · canonical-locus alias PRECEDENCE ·
C-side replay · `film-too-many-frames` has no positive witness · `len` unencoded.

New, and declared rather than left implicit: the bundle's films are **replayed, not re-executed** —
the checker does not re-run the native binary; and `proof_bundle.json` is declared
`generated_evidence` rather than a case input (1.2 MB × 375 scratch trees), so **no negative-battery
case forges the bundle**. `proof_forgeries.mjs` covers that and covers it better, but they are
different instruments and the manifest says so rather than leaving the exemption silent.

**Q1 — is `proof-outcome-changed` the right code for "both sides reach the same target term"?** It is
not an outcome defect; it is a *degenerate claim* — the case asserts that a program equals itself, and
64 of those would still aggregate to VERIFIED. It may deserve its own code
(`proof-claim-degenerate`), which would also make the forgery's own report sharper.

**Q2 — should the checker re-EXECUTE rather than replay?** Replay is stronger evidence about the
transition relation and weaker evidence about the binary. Adding a native re-run would give the
verifier a second implementation to disagree with — the "verifier diversity" item filed at B5.1 —
but it also puts a compiler in the proof checker's dependency set, and a reviewer without gcc would
then see the proof gate SKIPPED, which is the layer collapse `EMISSION_CONFORMANCE-v1` is
deliberately placed to avoid.

**Q3 — what is the second proof object?** The obvious ladder is (a) a *refusal* theorem, using `sub`
to state a bounded claim about where the compiler declines — which would put the partial codomain
inside a proof artifact for the first time; or (b) a second *algebraic* bounded claim over the same
machinery (associativity of `add`, or `mul` commutativity) which costs almost nothing and mostly
tests whether the bundle format generalises. I think (a) is the interesting one and (b) is the honest
regression test, and I would not do both. Your ordering.
