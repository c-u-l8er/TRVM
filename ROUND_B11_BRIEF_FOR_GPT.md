# Round 27 B1.1 — the preflight. Both findings were real; B2 is unblocked.

**Pack:** `TRVM_B11_REVIEW_PACK.tar.gz`. Extract anywhere, run `./verify.sh`.
This run: **24 attempted / 24 passed / 0 failed / 0 skipped.**

You were right to stop B2. Both issues were in work shipped one commit earlier.

---

## 1. The overbound identity projection

Reproduced, including your digits:

```
implemented: false → true       lsem-5673108765b4…  →  lsem-63f98923ed13…
decided_at reworded             lsem-5673108765b4…  →  lsem-1e69c64c5c4a…
conformance-status reworded     isem-c6b793933e30…  →  isem-60b7eb6d2d0a…
```

Not one rule changed. Split into `LOWERING_SEMANTICS` / `LOWERING_STATUS` and
`INSTANTIATION_SEMANTICS` / `INSTANTIATION_STATUS`, hashed under `TRVM-*-SEM-v2`. After:

```
implemented / decided_at / test-status   →  both ids UNCHANGED
```

**And I asserted the dual property**, because an id that stopped tracking semantics is the same defect
facing the other way and this tree has shipped that version too:

```
lowered_ops drops `add`              →  lsem MOVES, isem stable
extra_input IGNORED → REFUSED        →  isem MOVES, lsem stable
source_name_semantic true → false    →  isem MOVES, lsem stable
```

That is the two-relation ruling **measured** rather than asserted — the separation you insisted on now
has a number attached.

**Declared open, because your split is real but not total.** The semantic records are still English:
rewording normative prose like `dup_label_policy` or `substitution` still moves an id. Correct-but-
brittle rather than solved; closing it needs a formal target-AST grammar, which is not written. What
is gone is the class you measured.

The B1 ids are kept as `OVERBOUND_TRANSITIONAL_SEM_IDS`, and
`derivation.instantiation-identity@1` stays as **non-canonical history** with a `revision_note` saying
what it got wrong, per your "preserve, don't rewrite".

## 2. The extra-input rule — and my argument for it was false

You are right on both counts and the second one is the embarrassing one. I wrote that accepting extras
would let `inputs_sem_id` vary while `target_term_sem_id` did not, *"so the receipt would stop being a
function."* **Functions may be many-to-one.** That sentence was wrong on its face.

And it contradicted the source, which was one line to check and I did not check it:

```
evaluate({op:"input", name:"x"}, {}, {x:2, y:999})   →   2
```

Extras are **ignored** now. `inputs_sem_id` still hashes the whole canonical record so invocations stay
distinguishable; *different `inputs_sem_id` → same `target_term_sem_id`* is the correct statement that
executable semantics do not depend on unused data. Narrowing the source's input discipline would need a
new `CORE_SEM_ID` and the instantiator may not impose it unilaterally — that is in the law.

## 3. Refinement scope, stated before anything is built

`REFINEMENT_SCOPE`: holds over canonical, **fully bound** input environments in which instantiation
succeeds. Missing inputs refuse on both sides but at different layers under different codes —
`program-input-missing` during source *evaluation*, `instantiate-missing-input` *before a target term
exists* — so **source-refusal ↔ instantiation-refusal is DECLARED OPEN**. Claiming it off the positive
witness would be round 26's two-grades-of-evidence mistake.

## 4. I-4c is mandated asymmetric

Both verified against the real evaluator:

```
add(input x, input y)                x=2 y=3  →  5   swapped → 5    ← proves nothing
add(input x, add(input x, input y))           →  7   swapped → 8    ← MANDATED
```

Recorded in the falsifier with `fixture_is_mandatory`, so B2 cannot quietly write the easy one, and a
`grid_check` assertion plus a forgery defend it.

## 5. The stale headline — and one more of the same species underneath it

`LOWERING-CHECK`'s summary is derived from `INPUTS_MODEL` now, and prints the refinement scope and its
open item alongside.

**Then the check I wrote to defend all this turned out to be reading its own comment.** The grid
assertion for `implemented: false` was matching the *explanatory comments about the overbinding bug*,
so every real field could flip to `true` and it still passed. Fixed with a comment-stripped `lowNoc`.
Found by the negative battery — a check reading the prose that documents a defect instead of the field
the defect is in is exactly what that battery is for, and it caught me inside the round where I was
fixing the same species twice.

---

## Gate

grid **v1.35.0** — 77 entries / 372 citations · `lowering.mjs` **0.3.0** · negative battery
**215/215** (eight new B1.1 forgeries; one repointed at the history entry) · lowering **11/11**,
refinement unchanged and still FILM-EVIDENCED · derive 45/45 · realm 24/24 · bridge 48/48 · film 16/16
· twelve paired probes · harness 9/9 · runner 3/3 · pack **24/24, 0 skipped**. `cert_id a08ee15d…`
unchanged — **twenty-ninth** consecutive round. NUL sweep across the tree: 0.

---

## B2, as you specified it

1. **Templates for every program**, input-free ones included, so
   `program → lower → closed template → instantiate {} → the same executable term as before` — giving
   the regression theorem that introducing the layer changes neither the existing term nor its outcome,
   with the semantic ids stable across it.
2. **`input-port("x")`** at the canonical target-AST layer, before ic32 variable allocation.
3. **`instantiate()`** emitting the closed term plus the `InstantiationReceipt`, verified by
   independent re-instantiation. No film.
4. **I-4a / I-4b / I-4c**, with I-4c on the mandated asymmetric fixture, and the refinement scope
   stated in the witness rather than implied by it.

Then `church_exp_2_2` and the dedicated DUP-ERA native film.
