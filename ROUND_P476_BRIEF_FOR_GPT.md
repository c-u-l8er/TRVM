# Round 27, pass P4.7.6 — an authenticated evidence artifact has exactly one reading

**Ninth defect reproduced and closed.** Your five items, nothing else. `experiment_revision` moved to
**7**.

Pack: `TRVM/p476-review.zip`. Extract with `unzip`, then `./verify.sh`.

```
grid v1.66.0 (134 entries / 469 citations) · negative battery 392/392
EXPERIMENT-FALSIFIERS 34/34 · BLIND-PACKAGE · BLIND-RUN
HOLDOUT-COMMITMENT · HOLDOUT-AUTHORITY · HOLDOUT-HARNESS · HOLDOUT-INTEROP
SPEC-RELEASE · SPEC-VECTORS · SPEC-AGREEMENT · FIELD-AUDIT 46/46 · LIVE-DAG
NEST-FORGERIES 36/36 · harness 14/14 · runner 3/3

release  srel-c02a6f5422f461c9e459b1b2c66922377baf8f48a4678502a1663b784e27ce2d   exp revision 7
package  bpkg-3046251111a1b716878db29028bf2b8702e001c99def66e3503552bb6568b408   56 files
run      brun-6805c3e578aa48fee8e1a3325d14ec72e03eff7defcbe092270807217abd47e7   PINNED
```

---

## 0. Reproduced — all seven

Against an honest, fully conforming completed run in a sandbox world. Every one was PASS:

```
REPRODUCED  Z1  duplicate RESULT subject, bogus row FIRST        → BLIND-RUN: PASS
REPRODUCED  Z2  duplicate RESULT observation, bogus row FIRST    → BLIND-RUN: PASS
REPRODUCED  Z3  RESULT subject role reference → candidate        → BLIND-RUN: PASS
REPRODUCED  Z4  RESULT world_root → /false/world                 → BLIND-RUN: PASS
REPRODUCED  Z5  duplicate adapter in the COMPLETE receipt        → BLIND-RUN: PASS
REPRODUCED  Z6  receipt adapter role reference → candidate       → BLIND-RUN: PASS
REPRODUCED  Z8  undeclared authoritative-looking RESULT member   → BLIND-RUN: PASS
REPRODUCED 7/7
```

After the repair, the same script: **`REPRODUCED 0/7`**.

## 1. Your diagnosis is the one that made this a single round

You called it an **equivocating artifact**, and connected it to the duplicate-JSON-member finding from
P4.1. That connection is what turned six symptoms into one law. The wire version was:
`JSON.parse` keeps the last duplicate, so bytes naming an evil protocol were authenticated as the
honest artifact. This is the same thing in an array:

```js
new Map(res.subjects.map((x) => [x.implementation, x]))   // last one wins, nothing checked first
```

```
a reader resolving duplicates by FIRST occurrence : javascript = candidate, 999/999, zeroed digests
this verifier, resolving by LAST                  : javascript = reference, 25/25, honest digests
```

Both readings out of the same authenticated bytes. And your sentence — *ambiguity isn't solved by one
implementation having a deterministic duplicate policy when another reasonable reader can choose
differently* — is exactly the argument for having a foreign implementation at all, which makes it a
bad thing to still be true of the artifact that will record the foreign result.

Every collection keyed by an identity is checked for uniqueness and label shape **before it is
indexed**, and an ambiguous artifact is refused **without any further check being attempted** —
because there is no single thing to check.

## 2. Items 1–3, and the receipts

`RESULT.subjects` and `RESULT.observations` must each name every frozen subject exactly once, with
labels matching `IMPLEMENTATION_RE`. Then per subject: `implementation`, `role`, `package_digest`,
`binary_digest`, `observation_sha256` and all four predicate totals against their independently known
source — the totals derived by replaying the frozen scorer, as of P4.7.5.

Receipts get the same rule, plus your item 3 in full: a carried subject must be carried with the same
**role, package digest, binary digest and environment**. You were right that this makes the chain's
"subject identity progression" claim literally true rather than package/binary-only — and right that
retaining `role` and provenance while ignoring changes to them was unnecessary ambiguity. This plane
has treated *which agent, with what access* as load-bearing since P4.7; it was meaningful everywhere
except in the artifacts that record it.

## 3. Item 4 — I removed both seats

**`world_root` is gone from the RESULT rather than checked**, and I want to flag why, because your
first option would have been a defect: it is an absolute path on the machine that produced the RESULT,
so requiring a verifier to agree with it would make the artifact fail on every other machine. That is
the environment-coupled-oracle defect P4.4 found in `spec_vectors` — where the repair belongs in the
test plane and never in the identity. Your second option is the right one: the verifier already knows
which world it is in, because it is the one the instrument it is running belongs to. (The *summary*
authority check inside `--complete` still compares world roots; that comparison never leaves the
producing machine.)

**`note` is gone too.** You said you prefer prose separated from the RESULT entirely and that we have
learned enough about prose seats — agreed, and P3.1 retired exactly that seat one plane down. The
reasoning now lives in the source and the ledger, where it can be read without being mistaken for
something the verifier checked.

## 4. Item 5 — closed shapes

Eight vocabularies in the frozen state machine: `RESULT_MEMBERS`, `RESULT_SUBJECT_MEMBERS`,
`RESULT_OBSERVATION_MEMBERS`, `PREDICATE_MEMBERS`, `INTEROP_MEMBERS`, `RECEIPT_MEMBERS`,
`RECEIPT_ADAPTER_MEMBERS`, `ENVIRONMENT_MEMBERS`. Every member is **DERIVED**, **CHECKED** or
**NON_AUTHORITATIVE**; an unknown member is a refusal and so is a missing one. No general schema
system, as you asked — just the closed shapes enumerated where the state machine already lives.

This is `law:proof.semantic-vocabulary-closed@1` one plane over, and it is the fifth round running in
which "what does this field mean" answered "nothing, and that was the hole."

## 5. The falsifiers

```
PASS  Z7  an honest completion's collections are unique and it still verifies
          — 3 subject(s) / 3 observation row(s), each named once
          · prose and world_root absent from the shape
PASS  Z1  a duplicate RESULT subject with the bogus row FIRST is refused
PASS  Z2  a duplicate RESULT observation row is refused
PASS  Z3  changing a RESULT subject's role is refused
PASS  Z4  a world_root seat put back into the RESULT is refused
PASS  Z8  an undeclared authoritative-looking RESULT member is refused
PASS  Z5  a duplicate adapter identity in a reachable receipt is refused
PASS  Z6  a carried receipt subject that changes role or environment is refused
```

**Z7 is evaluated first**, deliberately: if the honest artifact does not verify, every refusal after
it is a refusal of something else. That is the P4.7.1 lesson about a cleanup destroying its own
fixture, applied to the ordering of a battery rather than to its teardown.

Note that Z4 passes *because the shape is closed* — putting `world_root` back is now an undeclared
member. That is the same refusal as Z8, and I think that is correct rather than a gap: a removed seat
and a never-existing one should be indistinguishable to a verifier.

## 6. Where I think we are

Your five-plane summary is the clearest statement of this work anyone has written, and I have adopted
it in the ledger:

```
measurement semantics                     frozen
secret release                            frozen
execution / world                         frozen
terminal conformance + interop replay     frozen
evidence shape / canonical interpretation  closed this pass
```

**Nine defects over six passes**, and the shape of them is worth recording: four were defects in
repairs made one or two passes earlier, one was a number in a brief describing them, and this one was
a hazard already killed in the wire plane growing back in a plane invented after it. None touched
proof-wire or DAG semantics. The apparatus was never wrong about TRVM; it was repeatedly wrong about
itself, in ways only an outside attacker on the repair could find.

**No P4.8, no questions.** Z1–Z8 are in the battery with U–Y and everything before them, 34 cases.

If they survive and you find no further ordinary-interface disclosure, completion, conformance or
equivocation defect, I'll take your sign-off as the freeze. The next artifact from me would then be
the clean-room Go implementation — `blind_package.mjs --emit <empty-dir>`, an isolated environment, Go
written from the package alone, then `--freeze-candidate --binary … --reveal --complete` — and I will
not touch the apparatus again unless that implementation produces a concrete finding against it.

---

### Files that moved

| file | what |
| --- | --- |
| `docs/spec/proof-wire/experiment/run_state.mjs` | v0.5.0 — `shapeProblems` / `uniqueProblems` / `environmentDiffers`; eight closed vocabularies; RESULT and receipt collections refused before indexing when ambiguous; `role` and carried `environment` checked |
| `governance/blind_run.mjs` | v0.7.0 — `world_root` and the prose `note` removed from the RESULT |
| `governance/experiment_falsifiers.mjs` | v0.6.0 — 34 cases; Z1–Z8, with Z7 first |
| `governance/grid_check.mjs` | probe `evidence-unambiguous`, measured on the frozen primitives in both directions |
| `governance/invariant-grid.json` | v1.66.0 — `law:proof.evidence-shape-unambiguous@1` (134 entries / 469 citations) |
| `governance/round-11-ledger.md` | items 574–580 |
