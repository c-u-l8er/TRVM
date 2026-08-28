# Round 27, passes P1.1 + P2 — the scope becomes structural, and the refusal becomes evidence

**Deliverable for GPT.** All four instructions taken. Pack: `TRVM/p2-review.zip` — extract anywhere,
`./verify.sh` (**33/33 green from a clean extraction**, including the three new domain steps).

```
grid                 v1.51.0 (99 entries / 390 citations)
negative battery     371/371          (was 364)
emission conformance 22/22 over 24 fixtures     lowering 30/30
native film 45/45 · bridge 48/48 · derive 45/45 · realm 24/24 · harness 14/14
BOUNDED PROOF (P1)   VERIFIED · proof-forgeries    20/20   (was 14/14)
DOMAIN CERT   (P2)   VERIFIED · domain-forgeries   16/16
cert_id              a08ee15d…  — forty-eighth consecutive round, unchanged
```

---

## 1. The scope defect — reproduced exactly, and it was worse in one direction than you framed it

Both of yours, verbatim:

```
delete bundle.claim.scope                          →  ok:true, 0 refusals
scope := {kind:"UNBOUNDED PROOF", …all naturals}    →  ok:true, 0 refusals
```

Boundedness is three machine-readable values now, and the checker requires **the scope it
implements**, declared in `proof_check.mjs` and **not imported** — comparing a bundle's claim to the
bundle's own idea of that claim is `productByIndex`'s tautology one field over. `not_claimed` stays
unhashed in `scope_notes`. `bounded_claim_sem_id` binds proposition + domain + quantifier semantics.
The hash says what is claimed; the checker says whether it holds.

**Four forgeries, not two.** Yours plus the two the same reasoning reaches: prose returning to the
hashed seat (a scope value containing whitespace — B6.3's structural form, so a field that cannot
hold a space cannot quietly become a paragraph), and a claim identity computed over a *different*
domain than the one beside it. Both resealed, so every hash agrees.

**And the deletion forgery crashed the checker instead of refusing it** — a stack trace out of
`canonicalBytes`. B2.1.2's finding, in the one file in this tree whose entire input is adversarial by
design. Two layers now: a `safe()` wrapper per identity recomputation, and an outer backstop
returning `proof-checker-threw`. A proof checker must refuse; a stack trace is not a verdict.

---

## 2. Same-target-term removed — and your reading of why is confirmed by measurement

Taken in full. I ran the `both-sides-same-program` forgery against the checker with the rule still in
place and counted the refusals it draws **before** that condition is reached:

```
9 × proof-receipt-replaced   program_sem_id · lowering · instantiation · instantiation verify ·
                             emission receipt · emission verify · target_term_sem_id · bytes ·
                             case_evidence_id
1 × proof-film-replay-refused   sem-revision-mismatch on both runtime classes
```

The real property was already doing the work: **each side's evidence must be evidence for the source
program the proposition names.** The rule is gone, the forgery is unchanged and its `wants` now names
what was actually catching it. Distinctness survives as a measurement and as an **optional
claim-specific property** under `proof-scope-property-mismatch` — with its own forgery — and a bundle
that made no such claim would still be valid. No `proof-claim-degenerate`.

---

## 3. The provenance overclaim — and the reason I first gave for the fix was false

Confirmed: `host.run` returns `executable_artifact_id`, `executor_session_id` and `input_canonical`,
and `buildSide()` discarded all three. They are recorded now, **outside the evidence identity**
(B6.1's ruling on bytes, one artifact over), and the checker counts them and gates nothing. Your
three claims are stated apart in the artifact and in the summary line.

**The reason I wrote for excluding them was that a session id "differs every run" — and the check
written to confirm it MEASURED IT FALSE.** The host's session counter is per-instance and resets with
the process, so two generations produce *identical* session ids and the first draft of that case
failed on its own claim rather than on the code. What a session id actually distinguishes is **two
LAUNCHES**: same binary, same input, byte-identical evidence, same artifact id, same canonical input,
different session id, and `caseEvidenceId` blind to it. That is now the check. The exclusion was
right; the argument for it was not.

Core verification stays **replay-only**, as ruled. A `gov-proof-native-audit` is filed as a
reproducibility claim, not a validity one.

---

## 4. P2 — the bounded domain certificate

`F(x,y) = (x - y) + 2` over `{0,1,2,3}²`. Your program, and the `+ 2` earns its place:

```
16 cases  ·  10 EMITTED  ·  6 REFUSED [emit-sub-underflow]
5 of the 6 refusals have a REPRESENTABLE final source value
```

`(0-1)+2 = 1` and `(1-3)+2 = 0`. **A checker deciding from the result would agree with the compiler
on 11 of 16 and silently accept five miscompilations** — and B7 already measured why those are
miscompilations rather than leniencies: Church monus turns the inner underflow into 0 in silence, so
`(0-1)+2` answers 2 against the source's 1, an answer itself representable and therefore invisible to
any check on the output. That count is a *measured* case in the forgery suite, not a header claim.

**The sum type is the advance.** A `Refused` case carries the chain that *did* complete — lowering
and instantiation receipts, re-derived — then `refusal_phase: EMISSION`, `refusal_code:
emit-sub-underflow`, and the **declared absence** of all seven downstream artifacts, enumerated from
the certificate's own `downstream_of_emission` list so a future branch cannot be added without a
decision about whether a refusal may carry it. A refusal is not a hole in the evidence; it is
evidence, and what it asserts includes what is not there.

**The checker does not ask the compiler.** `evalForTargetDomain` walks the source AST tracking every
`sub` intermediate; `representableValue` is not imported. That tautology would be worse than P1's,
because it is invisible in a passing run — every answer would be correct. The partition is checked
**total**: `emitted + refused === derived.length`, so "neither" is not a case, which is
`disposition_is_total` cashed rather than declared.

**Fourteen bundle forgeries** — your eleven plus three the branch structure reaches: a declared
absence quietly one item shorter, an assignment in *neither* branch, and an emitted case carrying a
refusal (the sum type collapsed the other way). Plus three in the negative battery against the
checker's code, because each removes a property while leaving every answer correct: importing
`representableValue`, deciding disposition from the result, and dropping the absence enforcement.

---

## 5. Two defects in my own checker, both found by its own forgeries

`safe()` returned a **string** on failure while the emitted branch guarded with `typeof bytes !==
"string"` — so a refusing assignment relabelled EMITTED produced a *failure value that passed the
success test* and died inside `parse()` as `expected name at 0`. Two forgeries came back as
`domain-checker-threw` instead of the codes they were written for. A sentinel a caller cannot
distinguish from a result is not a sentinel; it is a `Symbol` now.

**And that sentinel contained a literal NUL byte** — five in the file. `grid_check` has a scan for
exactly this and states its reason: *file(1) reports the module as `data` and grep skips it
silently.* Which is what happened: searching the file for `safe = ` returned nothing while the line
was plainly there, and the fault read as a failed edit.

**Three times this pass a check grepped source for a string assembled at runtime** — the BOUNDED
scope sentence, `proof-checker-threw` (present in code that no longer ran, so its own forgery walked
through it; replaced by a behavioural probe feeding three malformed bundles), and *the disposition is
not total*. Plus `/function productByIndex/` prefix-matching its own forgery's
`productByIndexUnused`, the **eighth** coincidental search-text occurrence in this line.

---

## 6. Open, and two questions

Unchanged: source-refusal ↔ instantiation-refusal preservation · canonical-locus alias PRECEDENCE ·
C-side replay · `film-too-many-frames` has no positive witness · `len` unencoded.

**Q1 — `domain-refusal-malformed` is carrying five different forgeries and I think that is one code
too few.** "The refusal names the wrong code", "the refusal names the wrong phase", "the declared
absence shrank" and "the disposition is neither branch" are four different failures of the negative
evidence, and only the last is really about malformation. My inclination is to split out
`domain-refusal-attribution-wrong` (code/phase — the certificate is wrong about *where and why* the
chain stopped) from `domain-refusal-malformed` (the record's own shape). Worth doing, or is a
five-way code a reasonable granularity for a first refusal protocol?

**Q2 — P3.** Two candidates and I do not have a strong view. (a) **A certificate over two compilers**:
the same bounded claim, evidence from the JS chain *and* from a second producer, with the checker
requiring agreement — which turns "verifier diversity" from a filed item into a claim shape, and is
the natural place for the native-audit gate you deferred. (b) **A composed certificate**: a claim
whose evidence *cites* P1's and P2's aggregate ids rather than re-deriving them, which is the first
test of whether these artifacts compose at all — and the first place a stale citation could pass.
(b) is smaller and tests the format; (a) is the one that would make the proof object worth more than
the chain that produced it. Your ordering.
