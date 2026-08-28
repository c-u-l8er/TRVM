# Round 27, pass B6.1 — your three corrections

**All three taken, plus the ontology ruling.** Every defect you found was in B6's own emission layer,
which is the right place for a new layer's defects to be.

Gate: grid **v1.46.0** (93 entries / 383 citations) · negative battery **320/320** · film 45/45 ·
lowering 23/23 · **emission 9/9 over 9 fixtures** · bridge 48/48 · derive 45/45 · realm 24/24 ·
harness 14/14 · runner 3/3. `cert_id a08ee15d…` byte-identical — **forty-first** consecutive round.

---

## (a) The fixture was not I-4c, and my headline finding was false because of it

Confirmed, including your ids:

```
add(const 2, const 3)              ctmpl-d0105d4f…
add(input x, input y) {x:2,y:3}    ctmpl-d0105d4f…   SAME
x + (x + y)          {x:2,y:3}     ctmpl-efba3154…   DIFFERENT
```

`2 + 3 == 3 + 2`, so it is exactly the symmetric fixture `INSTANTIATION_FALSIFIERS` I-4c rejects **in
its own words** — *a test whose output cannot reveal the defect it is named for*. I reported the
collapse as the interesting finding and the collapse was an artifact of the mislabelling.

**Your fix taken exactly**: kept under the honest name `two-port collapse`, because what it actually
proves is worth having, and the **real I-4c added beside it** — already a distinct closed template,
so nothing was invented to force distinctness. Nine fixtures, eight distinct domain values, and E-9
now reports `…, 3, 5, 7` — the 7 is the real I-4c computing correctly.

The surviving theorem is the one you named: **emission cannot depend on provenance instantiation
erased.**

## (b) The headline contradicted its own cases

Confirmed, and it is the worse of the two reporting defects because it lands in `RESULTS.txt` where a
reviewer who runs nothing else sees only that. Every quantity in the final line is now a field
written by the case that measured it:

```
QUOTIENT-VISIBLE STRUCTURAL DRIFT … REFUSED on 9/9
ALPHA-RENAMING AND LABEL PERMUTATION LEAVE IT UNCHANGED on 9/9, as L-BYTES-1 requires
The structural alternate differs in id on 6/6 applicable and agrees in decoded outcome on 6/6
```

No new harness species, as you said. The stale header prose is corrected too.

## (c) The ontology — ruled your way, and the move is scoped by measurement

`TARGET_ENCODING.dup_label_policy` justified the allocation as semantic *"because the label reaches
the canonical signature"*. It does not, and B6's own battery measured that. **An encoding identity
cannot be justified by a difference its own codomain erases.**

The encoding now commits to **label equality and freshness structure** — collapsing two distinct dups
onto one label changes whether `DUP-SUP=` or `DUP-SUP!` fires, and that is semantic — and says
nothing about the integers representing it.

**What moved, and what did not:**

```
MOVED   TARGET_EXECUTABLE_ENCODING_SEM_ID   xenc-7ce8f33f… → xenc-25464e50…
MOVED   EMISSION_SEM_ID                     esem-aab30fb5… → esem-a88100f1…
SAME    LOWERING_SEM_ID · INSTANTIATION_SEM_ID · TARGET_TEMPLATE_ENCODING_SEM_ID · DECODE_SEM_ID
```

The executable encoding's semantics changed and nothing else did — which is what makes this a
correction rather than a re-cutting of the chain. B6's pair is kept in
`SUPERSEDED_LABEL_SEMANTICS_SEM_IDS`.

**I took your first design, not the second.** No `target_term_bytes_id` in the receipt. Emission
proves the semantic target term; exact bytes belong beside `executable_artifact_id` as provenance. The
law now says so explicitly, including what the receipt does **not** prove.

**And your ladder is in the law**, replacing my pair:

```
exact emitted BYTES ──quotient alpha and label spelling──▶ target_term_sem_id
                    ──execute, normalise, decode─────────▶ outcome_sem_id
```

`derivation.emission-conformance@2` supersedes @1, kept as history.

## (d) The adversaries are split

`E-F1` uses an unconstrained quotient-visible drift — bump a church numeral — and therefore covers
**9/9** with no applicability caveat. `E-8` keeps the commutativity-dependent equivalence and covers
the **6** add-bearing fixtures. **No replacement equivalence invented before `sub` exists**, as you
ruled.

---

## One thing worth flagging: it happened twice in one session

Two of my own new assertions matched **substrings rather than the thing**:

- the M-10 wiring check counted *mentions* of `phase_pin_lint.py`, so `true "$BASE/phase_pin_lint.py"`
  disarmed the guard and left it green;
- the adversary-split check tested `/driftEmit/`, which `notTheDriftEmitter` satisfies.

Both were caught by the negative case written beside the assertion, on its first run. That is the
argument for writing the forgery next to the claim rather than after it — but two instances in one
session of *the guard matches a substring of its own disarming* is a shape, not an accident.

**I am not proposing an M-11.** You said stop at ten and I agree; I am recording it in the ledger so
that if it recurs a third time there is a countable record rather than a memory. If you think that is
already enough to act on, say so and I will bring it back.

## Still open

1. **C-side replay** — verifier diversity / a small native proof consumer.
2. Canonical-locus alias **precedence**.
3. `film-projection-not-unique` has no direct negative fixture.
4. `film-too-many-frames` reached by no term tried; guard witnessed by a `-DMAXFRAMES=4` build.
5. Source-refusal ↔ instantiation-refusal preservation.
6. **E-8's equivalence witness when `sub` arrives** — deferred by ruling, not forgotten.

## The pack

`b61-review.zip` — `verify.sh` runs 26 checks and generates `RESULTS.txt` from that run.

```
unzip b61-review.zip && cd b61-review && ./verify.sh
```

Read: `governance/round-11-ledger.md` §339–346 · `governance/emission_conformance.mjs` (the ladder is
in the header, the adversaries are `driftEmit` / `equivEmit`) · `governance/lowering.mjs`
`TARGET_ENCODING.label_semantics` and `SUPERSEDED_LABEL_SEMANTICS_SEM_IDS`.
