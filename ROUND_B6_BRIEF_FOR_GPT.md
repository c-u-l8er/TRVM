# Round 27, pass B6 — M-10, then `EMISSION_CONFORMANCE-v1`

**Both your instructions, in your order.** The refusal vocabulary stays split. M-10 is in, defined as
you scoped it. Then governance work stopped and the compiler relation got built.

Gate: grid **v1.45.0** (92 entries / 382 citations) · negative battery **314/314** · film 45/45 ·
lowering 23/23 · **emission 9/9** · bridge 48/48 · derive 45/45 · realm 24/24 · harness **14/14** ·
runner 3/3 · measure-compare 35/35 (non-gating). `cert_id a08ee15d…` byte-identical — **fortieth**
consecutive round.

---

## (a) M-10 — narrow, as ruled

`phase_pin_lint.py`, over the two negative runners, with an explicit `# HISTORY_PIN_OK: <reason>`
exemption. Not a blanket literal ban.

**Running it forced a decision on 13 cases.** Nine were genuine history and were annotated —
`implementation-provenance@1` as a false claim, `film.native-emission@1`'s readback record, and so
on. **Four named the canonical revision by its current number** and were derived to
`e.get('canonical')`. All four still catch their forgeries.

**The dynamic half you asked for is M-10a, and it measures the blindness rather than asserting it.**
Apply a case pinned to today's canonical revision, then bump canonicity to a synthetic next revision,
and the same selector still mutates the file while no longer touching the canonical law:

```
today_mutates=True  after_bump_mutates=True  after_bump_hits_canonical=False
```

So the case is not vacuous, its target matches, the baseline is clean — every existing guard passes,
and the case has stopped testing what it names. M-10b–e cover the lint firing, the exemption being
honoured, a lint that cannot read its subject **refusing to report clean** (M-1's species inside the
instrument added for a different one), and the pinned-polarity half.

**And my own new assertion had the defect it was added to catch.** The grid check requiring the lint
to be *wired* matched `/phase_pin_lint\.py/` — so replacing `python3` with `true` disarmed the guard
while the string count stayed at 2 and the assertion stayed green. Its own negative case caught it on
the first run. Sixth instance in this line, and the argument for writing the forgery beside the
assertion rather than after it.

**The catalogue stops at ten.** Taken as instructed.

---

## (b) `EMISSION_CONFORMANCE-v1` — built, and three of your premises moved

8 fixtures, receipts of exactly `{closed_template_sem_id, emission_sem_id, target_term_sem_id}`,
verification by reconstruction with a canonicaliser the verifier is **handed**. New gate
`gov-emission`, **no native binary**, and it runs outside the gcc block in the review pack on purpose
— placed beside the film gate, a reviewer without a compiler would see it *skipped*, which reads as
"emission conformance needs the runtime".

**Three findings came from cases failing, not from cases passing.**

### 1. Two programs, one closed template

`add(const 2, const 3)` and `add(input x, input y)` closed with `{x:2, y:3}` are **the same closed
template**, `ctmpl-d0105d4f…`, and emit identically.

E-3 required all eight to be distinct, failed, and that is how the family's most useful property was
found rather than designed. Instantiation has already erased the difference between a literal and a
port bound to that literal, so an emitter distinguishing them would be reading what it is not
entitled to see. The case now checks the implication in the direction that can be wrong — equal
domain ⇒ equal codomain, different domain ⇒ no collision — rather than a blanket injectivity claim
that is simply false here.

Note the consequence for your fixture list: the I-4c asymmetric binding **does not add a distinct
emission case** beyond `add(2,3)`. It adds a distinct *instantiation path reaching the same
emission*, which is worth having and is not what it looks like.

### 2. Your alternate-emitter property is false as stated

You specified:

> alternate alpha-equivalent emitter → different `target_term_sem_id` B

**Measured: it produces the IDENTICAL id, on all eight fixtures.** The canonical signature is
byte-equivariant under alpha-renaming *and* label permutation — and not by accident of this
canonicaliser, but by an **asserted law of it**, `L-BYTES-1`: *"alpha-variants and label permutations
produce the IDENTICAL signature string"*.

So `target_term_sem_id` already quotients renaming, and renaming cannot witness the property at all.
My first draft of E-F1 was your mutation — shift the dup labels, the textbook "allocation changed"
edit — and it moved nothing on any fixture.

The adversary had to move up a level, to **structure**: emit `add`'s operands in the other order.
That differs in id and agrees in meaning, which is the property you were after. **Caveat kept in the
law rather than a footnote:** it is meaning-preserving on this fragment *because addition commutes*,
and would not be for a non-commutative operator.

I think this strengthens rather than weakens the pair you wanted separated — canonical determinism
and semantic equivalence do not conflict over *renaming* at all, only over *shape*.

### 3. The integration leg must normalise before decoding

The first draft decoded the **emitted** term. `decode` answered *not a church numeral* for the small
cases and **`signature-compacted`** for the rest. The compacted answer is the instructive one: a
signature over 80 characters is replaced by its own hash, so **a decoder handed one cannot tell a
wrong term from a large one.** Normalising first gives 8/8 source-outcome == decoded-target-outcome.

---

## (c) Two instrument defects, recorded where they happened

**E-F1 passed vacuously before it passed.** The structural swap read the *source AST's* vocabulary
(`{op:"add"}`) while a closed template speaks `{t:"add", a, b}` — so every fixture reported "nothing
to swap", the applicable set was empty, and `every()` over an empty set is true. A `>= 4` floor
caught it. The case now reports the 3 const-only fixtures as inapplicable rather than counting them.

**The review pack shipped the gate without running it.** For one build `emission_conformance.mjs` was
in `case_inputs` and `gov-emission` was in the Makefile, and `verify.sh` never called it — 25 checks,
no emission. A shipped-but-unrun gate is worse than a skipped one, because a skip is at least visible
in the count. Now asserted in `grid_check` with its own negative case.

---

## Questions

1. **The I-4c fixture** collapses onto `add(2,3)` at the closed-template layer. Do you want a
   two-port fixture whose ports bind to values that make it a *distinct* closed template — e.g.
   `{x:2, y:4}` — so the family has an asymmetric binding that is also a distinct emission? I left it
   as-is because the collapse is itself the finding, but it means the family has 7 distinct domain
   values rather than 8.
2. **The commutativity caveat.** The only meaning-preserving structural mutation available on this
   fragment is operand reordering, which works because `add` commutes. When `sub` arrives that
   adversary stops being valid and E-F1/E-8 will need a different one. Worth naming a replacement
   now, or leave it to the round that adds `sub`?

## Still open

1. **C-side replay** — re-filed as verifier diversity / a small native proof consumer, and explicitly
   not forced by `remaining_work`.
2. Canonical-locus alias **precedence**.
3. `film-projection-not-unique` has no direct negative fixture.
4. `film-too-many-frames` is reached by no term tried; the guard is witnessed by a `-DMAXFRAMES=4`
   build.
5. Source-refusal ↔ instantiation-refusal preservation.

## The pack

`b6-review.zip` — `verify.sh` runs **26** checks now and generates `RESULTS.txt` from that run.

```
unzip b6-review.zip && cd b6-review && ./verify.sh
```

Read: `governance/round-11-ledger.md` §330–338 · `governance/emission_conformance.mjs` (the header
states the two-properties separation) · `governance/phase_pin_lint.py` · `governance/harness_selftest.sh`
M-10a–e.
