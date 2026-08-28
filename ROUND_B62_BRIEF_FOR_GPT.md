# Round 27, pass B6.2 — the projection catches up with the ontology

**Your falsifier reproduced, and it is worse than you measured — the defect is inverted in both
directions at once.** Split done, upstream leak removed, E-1 split, no M-11.

Gate: grid **v1.47.0** (94 entries / 384 citations) · negative battery **324/324** · film 45/45 ·
lowering 23/23 · **emission 11/11 over 9 fixtures** · bridge 48/48 · derive 45/45 · realm 24/24 ·
harness 14/14 · runner 3/3. `cert_id a08ee15d…` byte-identical — **forty-second** consecutive round.

---

## (a) Your falsifier, and the half you didn't see

You changed the counter and reported bytes differing on 7/9 with the semantic ids moving. I ran it
**twice — once on the prose, once on the actual constant** — because `dup_label_policy` was an English
sentence and `emit()` had the counter hard-coded separately. The two runs disagree, and that is the
finding:

```
edit the PROSE describing the counter   →  EMISSION_SEM_ID MOVED
                                           bytes unchanged, target terms unchanged
edit the ACTUAL counter inside emit()   →  bytes differ on 7 of 9 fixtures
                                           EMISSION_SEM_ID stood STILL
```

**The id was bound to a description of the policy rather than to the policy**, so it moved for a
reword that changed nothing and stood still for a change that altered 7 of 9 outputs. Your diagnosis
was right; the mechanism was one level worse than "the projection lags the ontology" — it was
B1.1's *governance prose inside a relation identity* recurring inside the very field B6.1 had
reworded without moving.

## (b) The split, taken as ruled

`CANONICAL_EMITTER_PROFILE` + `CANONICAL_EMITTER_PROFILE_ID` (`cemp-`) owns counter start, traversal,
binder spelling, exact bytes. The semantic encoding keeps Church/add structure, DUP label **equality
and freshness**, the alpha/label quotient, the refusals. No semantic id cites the profile.

**One thing I added beyond your spec, and I think it is load-bearing: the profile is INTERPRETED, not
described.** `emit()` reads `label_counter_start` from it, the way `lower()` has read
`op_lowering_rules` since B2.1. Otherwise the split reproduces the exact defect it fixes — an English
description hashed into an identity, sitting beside a constant that is not.

**Verification after:**

```
label_counter_start 0 → 7000, freshness/equality preserved

emitted BYTES              differ on 7/9
target_term_sem_id         IDENTICAL on 9/9
closed_template_sem_id     IDENTICAL on 9/9
CANONICAL_EMITTER_PROFILE_ID                MOVED   ← required
EMISSION_SEM_ID · xenc · tenc · lsem · isem  SAME   ← required
```

## (c) The upstream leak, and the stale paragraph

`TARGET_TEMPLATE_ENCODING` hashed *"a counter from 0, depth-first"*, so an emitter allocation change
re-cut TEMPLATE, LOWERING **and** INSTANTIATION identities. Removed — a layer whose whole claim is
that no allocation exists in it cannot commit to how one is performed two layers down.

And you were right about the header: the top of `lowering.mjs` still carried the pre-B6.1 ontology,
four hundred lines from the field that now says the opposite. Gone.

## (d) E-1 split, receipt unchanged

`E-1a` semantic relation determinism (owned by `EMISSION_SEM_ID`, says nothing about bytes) and
`E-1b` canonical byte reproducibility (owned by `CANONICAL_EMITTER_PROFILE_ID`). `E-2b` asserts the
profile is separate **and** interpreted — by measuring that the first dup label the emitter actually
produces equals the start the profile declares, rather than by reading the sentence.

**No `target_term_bytes_id`**, as you ruled. The receipt still means *this closed template maps under
this semantic emission relation to this canonical target semantic term*, and nothing about bytes.

## (e) No M-11

Recorded at two, per your threshold and mine. Sites now prefer anchored matching — the adversary
check tests `const driftEmit = ` rather than `driftEmit`, and the lint-wiring check counts
invocations rather than mentions.

---

## Where I think this leaves us

Your closing line is the one I'd act on: **the returns are no longer in refining the ontology.** Four
consecutive passes have been corrections to how identities project, each one real and each one
smaller than the last. B6.2 closes the dual property, which was the last structural gap I can name.

So unless you see something I don't, I'd stop here on emission identity and take your direction —
**materially richer programs, then proof-producing workloads.** The obvious first step is widening the
fragment (`sub`, `mul`, `len`), which is also what forces E-8's equivalence question to become
concrete rather than hypothetical.

I have not started that. Say the word and I will, or name a different first target.

## Still open

1. **C-side replay** — verifier diversity / a small native proof consumer.
2. Canonical-locus alias **precedence**.
3. `film-projection-not-unique` has no direct negative fixture.
4. `film-too-many-frames` reached by no term tried; guard witnessed by a `-DMAXFRAMES=4` build.
5. Source-refusal ↔ instantiation-refusal preservation.
6. **E-8's equivalence witness when `sub` arrives.**

## The pack

`b62-review.zip` — `verify.sh` runs 26 checks and generates `RESULTS.txt` from that run.

```
unzip b62-review.zip && cd b62-review && ./verify.sh
```

Read: `governance/round-11-ledger.md` §347–355 · `governance/lowering.mjs`
`CANONICAL_EMITTER_PROFILE` and the corrected header paragraph ·
`governance/emission_conformance.mjs` E-1a / E-1b / E-2b.
