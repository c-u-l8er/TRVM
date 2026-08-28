# Round 27, pass B7 — `sub`, and the first time the compiler is smaller than the language

**Deliverable for GPT.** B6.3.1 treated as closed; no identity or governance work reopened. This is a
computation round. Pack: `TRVM/b7-review.zip` — extract anywhere, `./verify.sh`.

---

## 0. Gate

```
grid                 v1.50.0 (98 entries / 388 citations)
negative battery     341/341 forgeries caught
emission conformance 20/20 over 19 fixtures — 15 EMITTING, 4 REFUSING
lowering refinement  26/26
native semantic film 45/45          cross-plane bridge  48/48
derive 45/45 · realm 24/24 · harness 14/14 · runner contract 3/3
NON-GATING           measure-compare 35/35 · measure_pred_sub 13/13
lowering.mjs         0.10.0
cert_id              a08ee15d…  — forty-fifth consecutive round, unchanged
```

---

## 1. B7.1 — the measurement, and it answered B6.3.1's open question

`governance/measure_pred_sub.mjs`, non-gating, asserts nothing, runs from `make gov-measure` and from
the pack's `verify.sh`.

**B6.3.1 recorded the worry as** *"ic32's fragment is LINEAR and Church predecessor is the classic
NON-LINEAR construction — it needs dups AND erasures inside the numeral"*. **That premise is wrong,
and counting settles it before any measurement:**

```
PRED = λn.λf.λx.(((n λg.λh.(h (g f))) λu.x) λw.w)
       n · f · x · g · h   used EXACTLY ONCE       the first u   used ZERO times
```

PRED is **AFFINE, not non-linear**. It needs a DROP, not a DUP, and ic32 drops an unused binder
through the substitution store with no Era node. It contains **no dup and therefore no label**, which
is also why duplicating it inside a Church numeral cannot collide. `sub` really is a one-operator
widening.

**Measured on both implementations. 13/13 agree, every one NORMAL_FORM.** Frame counts and rule
tallies are printed and appear nowhere as expected values — GPT's instruction, and this tree's rule
since B3. The tool builds its Church expansion **locally** rather than importing the emitter's,
because at B7.1 the emitter did not know what `sub` was; and it **delegates the C↔JS verdict to
`bridge/measure_compare.mjs`** rather than growing a second comparator.

```
          C↔JS  frames  fire                                        decode   true  monus
pred(0)   AGREE      6  APP-LAM=6                                        0     -1      0   MONUS
pred(1)   AGREE      9  APP-LAM=9                                        0      0      0
pred(2)   AGREE     17  APP-LAM=11 APP-SUP=2 DUP-LAM=2 DUP-SUP==2        1      1      1
pred(3)   AGREE     25  APP-LAM=13 APP-SUP=4 DUP-LAM=4 DUP-SUP==4        2      2      2
pred(4)   AGREE     33  APP-LAM=15 APP-SUP=6 DUP-LAM=6 DUP-SUP==6        3      3      3
2 - 0     AGREE      2  APP-LAM=2                                        2      2      2
5 - 2     AGREE     96  APP-LAM=30 APP-SUP=21 DUP-LAM=23 DUP-SUP==22     3      3      3
2 - 2     AGREE     48  APP-LAM=18 APP-SUP=9  DUP-LAM=11 DUP-SUP==10     0      0      0
7 - 2     AGREE    128  APP-LAM=38 APP-SUP=29 DUP-LAM=31 DUP-SUP==30     5      5      5
2 - 3     AGREE     70  APP-LAM=22 APP-SUP=14 DUP-LAM=18 DUP-SUP==16     0     -1      0   MONUS
(7-2)-1   AGREE    175  APP-LAM=55 APP-SUP=39 DUP-LAM=41 DUP-SUP==40     4      4      4
7-(2-1)   AGREE     92  APP-LAM=32 APP-SUP=19 DUP-LAM=21 DUP-SUP==20     6      6      6
(2-3)+2   AGREE     76  APP-LAM=28 APP-SUP=14 DUP-LAM=18 DUP-SUP==16     2      1      2   MONUS
```
(`pred(k)` is `SUB(k,1)`, so `pred(0)` is `0 - 1`: the two arithmetics disagree there and the
target's monus answer is the first of the three that distinguish them. The frame counts are LEFTMOST;
`emission_conformance` prints different ones for the same terms because `runFloat` defaults to a
seeded random scheduler, and the frame count is not a semantic quantity.)

**THE SEMANTIC OBSERVATION, and it is the round.** Raw Church SUB is **monus**. The frozen core's
`sub` is `(x,y) => x - y`, so compiling straight onto it is a **miscompilation**. The line that
matters is the last one: **`(2-3)+2` decodes to 2 against the source's 1** — an inner underflow
leaves **no trace in the outcome**, and 1 and 2 are both perfectly representable, so no check on the
RESULT can ever catch it. That is why the representability walk is recursive rather than a root test.

Rules exercised across the fixtures: `APP-LAM APP-SUP DUP-LAM DUP-SUP=`. **No new rule** — the pool
closed at B4 — but `sub` drives APP-SUP and the `d:`/`v:` loci far harder than any add fixture.

---

## 2. B7.2 — structural `sub`

```
Template := church(n) | add(a,b) | sub(a,b) | port(name)
lower(sub(a,b)) = sub(lower(a), lower(b))              source order, preserved exactly
emit(sub(a,b))  = ((emit(b) PRED) emit(a))             the SUBTRAHEND is the numeral applied
```

The target application order is the **inverse** of the source's `a − b`, and that inversion happens
in **one expression inside `emit()` and nowhere else** — which is why the template keeps the source's
order rather than carrying a pre-inverted pair whose orientation a reader has to remember.

`op_lowering_rules.sub` is `add`'s rule with the tag renamed and **zero preconditions**. Instantiation
does not check representability either: `sub(port x, port y)` closed with `{x:2,y:5}` is a perfectly
well-formed closed template of a perfectly well-formed program; what has no image is its **emission**.

---

## 3. The refusal: `emit-sub-underflow`

**Three tempting homes, all wrong**, and each was written out before being rejected:

| candidate | why not |
|---|---|
| saturate to 0 | answers a different program's question; `(2-3)+2 → 2` and nothing downstream sees it |
| `lower-negative` on the sub rule | **cannot be written** — `sub(input x, input y)` has no underflow fact until ports bind. One template: `{x:5,y:2}` emits, `{x:2,y:5}` refuses |
| refuse in the source | changes the language to suit the compiler; **moves `CORE_SEM_ID`** |

So it is a refusal at **EMISSION**, against the **CODOMAIN**. The shape is
`source language ⊃ representable target fragment` — an ordinary partial compiler.

**It is NOT source-refusal ↔ target-refusal preservation**, and the record says so in three places
(`REFINEMENT_SCOPE.representable_only`, the law statement, a grid assertion) plus a battery forgery
that refuses any edit booking it as progress on the open item. For `sub(2,3)` **the source does not
refuse** — it evaluates to −1, correctly — and the compiler declines. No target term is produced, no
`EmissionReceipt` is built, and **no target outcome is claimed**.

**It is decided before a single knob is read.** `representableValue()` runs before `emit()` even
validates the profile, so no serialization configuration can turn a domain refusal into an acceptance
*or into a different refusal*. Measured: 16 (refusing fixture × profile) pairs across four profiles —
two valid knob settings and **two deliberately broken ones** — all answer `emit-sub-underflow`.
**Non-vacuous**: the same two broken profiles handed a *representable* template answer
`emitter-profile-unknown-label-alloc-order` and `emitter-profile-malformed`, so the invariance is the
ORDER of the checks and not the profiles being harmless.

---

## 4. Witnesses

Every one you asked for, plus the association pair.

```
5 - 2                        → 3     E-10 · lowering_check B7-sub-refinement-is-film-evidenced
2 - 0                        → 2     E-11
2 - 2                        → 0     E-12
input x - input y {x:5,y:2}  → 3     E-13 · lowering_check B7-emit-sub-underflow (positive half)
(7 - 2) - 1                  → 4     E-14 · lowering_check B7-association-is-semantic
7 - (2 - 1)                  → 6     E-15 · lowering_check B7-association-is-semantic
2 - 3                        REFUSES emit-sub-underflow      E-16
2 - 5   (5-2 succeeds)       REFUSES emit-sub-underflow      E-17 · E-8c pair
(2 - 3) + 2                  REFUSES emit-sub-underflow      E-18   ← the nested falsifier
input x - input y {x:2,y:5}  REFUSES emit-sub-underflow      E-19   ← same template as E-13
```

**`E-0` checks DECLARED against OBSERVED in both directions**, so a fixture declared to refuse that
emits fails as loudly as one declared to emit that does not — which is the direction a saturating
emitter would trip. Every count in the battery is over the population it names; a case reporting 9/9
about a family of 19 has stopped counting what it names.

**`E-10c` — emission emits subtraction, it does not compute it.** The representability walk computes
exactly the number a folder would return and throws it away, so "we did not fold" is not visible in
the code that decides not to. Measured instead: all 6 emitting sub fixtures contain the PRED body,
differ from `emit(church(theirOwnValue))`, and are **longer** than that fold would be; the runtime
does the work — `sub(5,2)` in 96 frames where a folded numeral reduces in zero.

**Native films, replayed through both JS runtime classes** exactly as prior native-film work:
`sub(const 5, const 2)` → 96 chained frames over `APP-LAM=30 APP-SUP=21 DUP-LAM=23 DUP-SUP==22`,
**66 dup-plane loci**, accepted by `replaySemFilm` on `FloatRt` and `DescFloatRt`, normal form
decoded to 3, source evaluator agreeing. **This is the first refinement witness that is also a
dup-plane term** — `add(2,3)` films six APP-LAM frames at tree loci and fires no dup rule at all, so
until B7 the refinement chain and the runtime frontier were exercised by different fixtures.

**E-8 is untouched** at 15/15 differs and 15/15 same-outcome: the generic β-wrapper `T → (λz.z T)`
survived the arrival of `sub` by construction, which is exactly what B6.3.1 generalised it for.
**`E-8b` is kept** as the add-specific algebraic measurement (6 applicable). **`E-8c` is new** and is
the swap as a *negative* operand-order witness: 8 applicable fixtures, every one either refusing or
changing the answer, and the sharpest form is a **pair over the same two operands** — `sub(5,2)`
emits, `sub(2,5)` refuses.

---

## 5. Semantic-ID movement — predicted, then measured, and one prediction was wrong

```
                                                          predicted   measured
CORE_SEM_ID                     core-0930d6f1…            unchanged   SAME
DECODE_SEM_ID                   dsem-71f531c6…            unchanged   SAME
TARGET_EXECUTABLE_ENCODING_SEM  xenc-69a5ffbf… → f422ea28… unchanged   MOVED   ← WRONG
TARGET_TEMPLATE_ENCODING_SEM    tenc-b4b5c4a4… → 48c96669… move        MOVED
LOWERING_SEM_ID                 lsem-51fda904… → a9573a90… move        MOVED
INSTANTIATION_SEM_ID            isem-7418dc41… → 8236aad4… move        MOVED
EMISSION_SEM_ID                 esem-b6958270… → c45b734d… move        MOVED
CANONICAL_EMITTER_PROFILE_ID    cemp-c546742f… → d7a2fe4f… iff config  MOVED
CANONICAL_EMITTER_ARTIFACT_ID   cema-5d748198… → 0770b921… move        MOVED
```

**`TARGET_EXECUTABLE_ENCODING_SEM_ID` could not stand still, and I think the brief's expectation was
the error rather than the implementation.** The executable encoding is the record that says how a
target construct becomes an interaction-net term; B7 hands it PRED/SUB and a statement of its own
domain. An `xenc-` that did not move across a new construct is **B1.2.1's UNDER-BOUND defect
exactly** — the identity of the encoding standing still across a change to the bytes that encoding
produces.

The claim worth making is narrower than "it moved", and `E-10d` runs it: **delete precisely the four
B7 edits from the LIVE object** — `.sub`, `.domain`, `.saturation`, and `emit-sub-underflow` from the
refusal list — and `xenc-69a5ffbf…` comes back **byte for byte**. So the move is attributable to
those four and nothing else drifted this round.

`cemp-` moved because `binder_names` gained `pred: ["n","f","x","g","h","u","w"]` — an actual value
`emit()` reads, so it is new serializer configuration and would have moved for that alone. `cema-`
moved because the bundle gained `PRED_COMBINATOR` and `representableValue`. B6.3.1's derived
dependency-closure check (`E-2e`) was **not weakened**: it now derives 69 module-level bindings, 6
bundled members referencing 6 of them, **0 escaping**. `representableValue` produces no bytes and is
bundled anyway — relax one comparison in it and a template that emitted nothing starts emitting a
full term with template and profile fixed, and "no bytes" is a byte-level outcome.

`SUPERSEDED_PRE_SUB_SEM_IDS` records the generation and **claims no defect in either direction** —
the first supersession in this line that is neither a correction nor a re-expression. Four ids moved
because *the thing they identify got bigger*, which is what a semantic identity is for.

---

## 6. Instrument defects this round found in itself

Reported because the round's own falsifiers found them, not because they were expected.

1. **Two `lowering_check` cases and two `grid_check` assertions were RATCHETS**, pinned to
   `const,add,input` by equality; **all four failed on the first run of the widened fragment**. The
   out-of-fragment driver is now derived from `CORE_SPEC.ops` minus `IMPLEMENTED_LOWERED_OPS` minus
   the read family, with its AST built from the op's own field list, and **an empty derivation is a
   FAILURE, never a skip**. Repointing it at `mul` would have rebuilt the identical trap.

2. **`grid_check` exited with a stack trace instead of a diagnostic** under my own
   `sub-refusal-moved-to-lowering` forgery: `lower()` refuses, so `closed_template` is `undefined`,
   and an unwrapped `emit()` threw out of the checker. **This is B2.1.2's finding, two rounds later,
   in a block written by someone who had read it.** Every probe on the behavioural rung is wrapped
   now, in one `compile()` helper.

3. **My first grid assertion checked `sub(2,3)` alone, and the ROOT-ONLY forgery passed clean.** The
   nested falsifier lived in `emission_conformance` and `lowering_check` and **not** in `grid_check`
   — which is the only thing the negative battery runs. `(2-3)+2` is a grid case now.

4. **My first `E-8c` included `sub(2,2)`**, which is its own swap and contributes `0 → 0`. I-4c's own
   species — *a test whose output cannot reveal the defect it is named for*. Symmetric fixtures are
   excluded by name with a count, and a battery case re-admits them to prove the exclusion is
   load-bearing. The case failed on its first run, which is how it was found.

5. **Two pre-existing battery cases broke on the widening, differently.**
   `input-dropped-from-semantics` went **VACUOUS** (hard-typed list). `source-refusals-in-the-encoding`
   **silently retargeted**: it replaced the *first* `refusals: ["emit-unbound-port",
   "template-malformed"],`, which was `TARGET_ENCODING`'s until B7 added a third entry to it — after
   which the first match is `TARGET_TEMPLATE_ENCODING`'s, a **different record**. Neither vacuous nor
   target-mismatched; it mutated a file and stopped testing what it names. **M-10's species and the
   sixth coincidental-second-occurrence in this line.** Both anchored on their declarations now.

**Eight new forgeries** cover the eight ways `sub` could go wrong: saturation, refusal moved to
lowering, refusal dropped from the encoding vocabulary, representability moved after the profile,
root-only check, constant folding, the open item booked as closed, and the two fragment lists
drifting apart. `341/341`.

---

## 7. Scope discipline

Not done, as instructed: no signed integers · no `mul` or `len` · no new governance or harness
species · no C-side replay · alias precedence untouched · no old authority work reopened. Nothing in
`REFINEMENT_SCOPE.declared_open` was closed.

---

## 8. Open, and three questions

Unchanged: source-refusal ↔ instantiation-refusal preservation · canonical-locus alias PRECEDENCE ·
C-side replay · `film-too-many-frames` has no positive witness · `mul` and `len` unencoded.

**New and measured, not estimated:** the **decodable** target range is **0 through 11**. A Church
numeral's canonical signature is `10 + 6n` characters, so 11 is 76 and 12 is 82 — over §5's
80-character compaction bound, replaced by its own hash and refused as
`decode-signature-compacted`. That is a bound on the **DECODER**, not on the runtime, which computes
12 perfectly well. No B7 fixture reaches it. **`mul(4,3)` does.**

**Q1 — is my reading of the `xenc-` prediction right?** I believe the brief's expectation table was
wrong on that row and the implementation is correct, for the B1.2.1 reason in §5. If you disagree,
the alternative is that `TARGET_ENCODING` should not describe `sub` at all — but then the record that
owns the executable encoding would be silent about a construct it emits, which seems worse.

**Q2 — `mul` will cross the decoder's bound almost immediately.** Does `mul` come with a decoder
widening (raise or remove §5 compaction for signatures the decoder is asked to read), or with
fixtures kept under 11, or with a `decode-signature-compacted` outcome treated as an honest partial
result? I have not touched `DECODE_SEM_ID` and would rather be told than guess.

**Q3 — should `representableValue` become an exported, identified DECISION PROCEDURE with its own
`sem_id`?** Today it is bundled into `cema-` as an implementation detail. It is the only thing that
decides which programs the compiler will accept, which feels like it wants an identity of its own —
but the emission split trigger's four conditions do not obviously fire for it, and I did not want to
invent a fifth relation without a ruling.
