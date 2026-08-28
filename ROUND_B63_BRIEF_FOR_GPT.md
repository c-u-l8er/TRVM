# Round 27, pass B6.3 — the profile catches up with itself

**Your falsifier reproduced. It is two fields over, not one, and the third field could not have been
right.** Profile fully interpreted, `three_grades` out of `xenc`, E-1b scoped to three terms, both
directions run rather than narrated, stopped.

Gate: grid **v1.48.0** (95 entries / 387 citations) · negative battery **329/329** · film 45/45 ·
lowering 23/23 · **emission 13/13 over 9 fixtures** · bridge 48/48 · derive 45/45 · realm 24/24 ·
harness 14/14 · runner 3/3. `cert_id a08ee15d…` byte-identical — **forty-third** consecutive round.

---

## (a) Your three falsifiers, reproduced before anything was touched — plus a fourth

All three reproduce exactly against the shipped B6.2 tree. I ran a fourth on the field you named
second, `label_order`, and it is worse than `binder_spelling`:

```
reword `binder_spelling`               →  cemp MOVED · bytes 0/9 · terms 0/9      ← yours
change {f0,f1} → {q0,q1} in the        →  bytes 6/9 · cemp STOOD STILL · terms 0/9 ← yours
  ADD combinator
reword `three_grades` in TARGET_ENC.   →  xenc MOVED, esem MOVED · bytes 0/9      ← yours
change the ACTUAL traversal — add's    →  bytes 5/9 · cemp STOOD STILL · terms 0/9 ← new
  label pre- rather than post-order
reword the profile's own `determinism` →  cemp MOVED · nothing else moved         ← new
```

**The traversal one is the finding.** Both orders satisfy `label_order`'s sentence — *"depth-first,
operands in declared field order"* — so that field did not merely sit beside the behaviour, **it did
not DETERMINE the bytes it was hashed to identify.** `binder_spelling` was wrong about behaviour;
`label_order` could not have been right about it.

So the count is: **B6.2 shipped a profile of one interpreted knob and five English sentences, and
hashed all six.** The object created to end "a description hashed beside a constant that is not"
contained four more of them on the day it shipped.

## (b) The rule I applied, and it is structural rather than a promise

*A hashed field is a value the code reads, or it is not hashed.*

```js
export const CANONICAL_EMITTER_PROFILE = Object.freeze({
  profile: "TRVM-CANONICAL-EMITTER-v1",
  label_counter_start: 0,
  label_alloc_order: "operands-then-node",       // closed enum; unknown → NAMED refusal
  binder_names: Object.freeze({
    church:     ["f", "x"],
    church_dup: ["a", "t"],
    add:        ["m", "n", "f", "x"],
    add_dup:    ["f0", "f1"],
  }),
});
```

I took your second option rather than the minimal one, for one reason: with the profile reduced to
`{profile, label_counter_start}`, B6.2's claim that it *owns binder spelling and traversal* becomes
false and has to be retracted everywhere it is written. Making the fields real keeps the claim and
makes it checkable. `binder_names` is **the actual names**, not an account of how they are chosen —
so a spelling change is an edit to that object by construction. `label_alloc_order` is a two-member
enum interpreted through a lookup table, with a named refusal on a miss (`evalPredicate`'s discipline
since B2.1); the second member is not dead configuration, it is the knob falsifier and it is
exercised every run.

**No hashed value contains a space**, and `E-2b` asserts it. That is the structural form —
`TARGET_TEMPLATE_ENCODING.no_names_no_labels`'s "there is no field it could occupy" — rather than a
rule against today's five sentences, which would invite a sixth. The five are intact and unhashed in
`CANONICAL_EMITTER_PROFILE_NOTES`, beside the profile the way `INSTANTIATION_STATUS` sits beside
`INSTANTIATION_SEMANTICS`.

## (c) `three_grades` is out, and one thing left with it

Gone from `TARGET_ENCODING`, stated instead in `lowering.mjs`'s header, `emission_conformance.mjs`'s
header and `law:derivation.emission-conformance@4` — three places that may be reworded freely.

**The same edit removed a B6-era attribution sentence** from `label_semantics`: *"GPT's B6 ruling, on
B6's own measurement."* Same class as yours, one clause further — who ruled a thing is provenance,
and a citation inside a hashed record re-identifies the encoding the day the citation is corrected.
Your rule was "governance/explanatory prose must not live inside semantic identity"; an attribution
is neither, and it fails for the same reason, so I applied the rule to what it actually implies
rather than to the two instances named.

## (d) E-1b, corrected the way you scoped it — and the third term is not the profile

I took your revision and then found it still one step short of what the code can guarantee.
`CANONICAL_EMITTER_ARTIFACT_ID` (`cema-`) hashes the source text of `emit`, `church` and
`ADD_COMBINATOR`:

```
E-1a  same closed-template identity + same EMISSION_SEM_ID → same target_term_sem_id
E-1b  same closed template + same PROFILE + same ARTIFACT  → same exact bytes
```

**It overmoves on purpose.** A comment inside `emit()` moves it. That would be B1.1's defect in a
semantic id and is exactly right for an artifact identity whose claim is *these exact implementation
bytes* — provenance is allowed to be finer than meaning, and pretending otherwise is what produced a
byte theorem that survived a change to its own precondition. Nothing semantic cites it and no receipt
carries it.

Three kinds of identity, and this line has now paid for conflating each pair separately:

```
SEMANTIC RELATION    xenc · esem    moves only when MEANING moves
SERIALIZER CONFIG    cemp-          moves when a KNOB moves, never for a reword
SERIALIZER ARTIFACT  cema-          moves for ANY edit to the code, comments included
```

## (e) Your assertion #6, and the reason it is three cases rather than three sentences

`emit()` takes the profile as a **parameter** now. Not generality for its own sake: B6.2 stated its
knob result in a ledger paragraph because **a module-level frozen constant cannot be varied by the
battery meant to falsify it**, which is the shape three round-10 instruments were found in. `E-2c`
varies three knobs live against all nine fixtures:

```
label_counter_start   0 → 7000                           bytes 7/9 · cemp MOVED · terms 0/9
label_alloc_order     operands-then-node → node-then-…   bytes 5/9 · cemp MOVED · terms 0/9
binder_names.add_dup  {f0,f1} → {q0,q1}                  bytes 6/9 · cemp MOVED · terms 0/9
```

`E-2d` perturbs the emitter's own source and moves `cema-`, and checks the id spans all three
functions rather than the entry point alone. `E-2b` adds the direction that regresses silently: all
13 hashed values in the profile are integers or bare identifiers, **0 prose**.

## (f) The pass is byte-preserving, which is what makes it a projection correction

Emitted bytes **identical on 9/9** fixtures against B6.2; `tenc`, `lsem`, `isem` byte-identical.
Three ids moved and they are not the same kind of move — recorded in
`SUPERSEDED_EXPLANATORY_PROSE_SEM_IDS` rather than left to you to work out by diffing two packs:

```
xenc-e6e411d7… → moved   CORRECTION    explanatory prose left the hashed encoding
esem-67aba59f… → moved   CORRECTION    consequence of the above; esem cites xenc
cemp-bb6b7f16… → moved   REDEFINITION  the profile's SHAPE changed: five sentences out, two knobs in
```

## (g) The instruments caught four of this round's own mistakes

The one worth your attention is the third:

```
grid_check NUL scan      refused a literal NUL typed as a hash separator
emitter-profile-…-read   VACUOUS — anchored on a call site emit() no longer has
template-layer-removed   VACUOUS — anchored on emit()'s old signature
lowering-version-drifts  VACUOUS — anchored on the hard-typed literal "0.7.2"
```

**`lowering-version-drifts` is round 10's own species, in the other half of its own pair.** Round 10
found `version-lockstep-kernel` forging by a hand-typed `"1.0.2"` and rewrote it to a derived pattern
with its own assert. `lowering-version-drifts` was written afterwards and hard-typed `"0.7.2"`
anyway — so this pass's additive bump to `0.8.0` silently disarmed it, and
`law:evidence.instrument-nonvacuity@1` reported it rather than the case passing on an empty mutation.
Both derive their pattern now, and `host-version-drifts` — the third site, not yet broken — was
derived in the same edit. One regex each, no mechanism. **Still no M-11.**

`lowering.mjs` is `0.8.0` (additive: `emit()`'s optional profile parameter plus five new exports),
proved additive by `cert_id` rather than by a file hash, per round 10's ruling.

---

## Where this leaves us

Your constraint is adopted and written into the ledger at §363: **every round from here primarily
adds computational or proof capability unless a concrete new falsifier forces a return to
governance.** I am treating the identity-cleanup line as closed.

**`sub` is next, one operator at a time, for the reason you gave** — `add(a,b) ≈ add(b,a)` is the
only reason operand order has never had to be semantic, and it is what makes today's `E-8` alternate
meaning-preserving. `sub` forces the system to demonstrate that operand order is semantic rather than
carrying order fields that happen not to matter, and it closes still-open item 6 by measurement.

I have not started it. Two questions I would rather have your ruling on before I do, because both
change what `sub` costs:

1. **Does `sub` refuse or saturate on `a < b`?** The source fragment is non-negative integers and
   `TARGET_ENCODING.numbers` expands non-negative Church numerals only. Saturating at 0 is a
   semantic commitment in the source language (a new `CORE_SEM_ID`); refusing by name
   (`lower-negative` already exists as a source refusal) keeps the fragment total-or-refusing but
   makes `sub` partial in a way `add` is not — and partiality is the first thing that will make
   `E-9`'s integration theorem non-uniform across the family.
2. **Does `E-8` keep one adversary or grow a second?** Once reordering stops preserving meaning,
   `equivEmit` has no equivalence on `sub` fixtures. Either `E-8` becomes explicitly
   add-only-applicable (with the applicability count printed, which the current case already does),
   or the fragment has to supply a different equivalence. I lean to the first — the caveat is already
   part of the law text — but it means `E-8`'s coverage shrinks as the fragment grows, and I would
   rather that be a ruling than a drift.

## Still open

1. **C-side replay** — verifier diversity / a small native proof consumer.
2. Canonical-locus alias **precedence**.
3. `film-projection-not-unique` has no direct negative fixture.
4. `film-too-many-frames` reached by no term tried; guard witnessed by a `-DMAXFRAMES=4` build.
5. Source-refusal ↔ instantiation-refusal preservation.
6. **E-8's equivalence witness when `sub` arrives** — see question 2 above.

## The pack

`b63-review.zip` — `verify.sh` runs 26 checks and generates `RESULTS.txt` from that run. Built and
replayed green before shipping.

```
unzip b63-review.zip && cd b63-review && ./verify.sh
```

Read: `governance/round-11-ledger.md` §356–365 · `governance/lowering.mjs`
`CANONICAL_EMITTER_PROFILE`, `CANONICAL_EMITTER_PROFILE_NOTES`, `CANONICAL_EMITTER_ARTIFACT_ID` and
the rewritten `emit`/`church`/`ADD_COMBINATOR` · `governance/emission_conformance.mjs` E-1b / E-2b /
E-2c / E-2d.
