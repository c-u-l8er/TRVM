# Round 27, pass B2 — inputs become executable

**All ten steps done, both API constraints enforced, and `x + (x + y)` runs natively to 7 against 8.**

Gate: grid **v1.38.0** (83 entries / 374 citations) · `lowering.mjs` **0.6.0** · negative battery
**260/260** · lowering **19/19** film-evidenced · derive 45/45 · realm 24/24 · bridge 48/48 · film
16/16 · twelve paired probes · harness 9/9 · runner 3/3 · pack 24/24, 0 skipped · NUL sweep 0.
`cert_id a08ee15d…` byte-identical — **thirty-second** consecutive round.

---

## Your ten steps

| # | | |
|---|---|---|
| 1 | rule table minimally structural | `op_lowering_rules` is data and **`lower()` interprets it** |
| 2 | `input → T.port(name)` | done; both dead refusal names deleted, not repointed |
| 3 | `instantiate()` not self-minting | returns bytes + `inputs_sem_id` + `consumed_inputs`, **no id** |
| 4 | receipt after independent canonicalization | kernel mints, then `instantiationReceipt(…)` |
| 5 | remove `lower().target_term` | gone; grid refuses its return |
| 6 | zero-input migration theorem | **exact 129 bytes**, same six-frame film, same NF, same 5 |
| 7 | I-4a / I-4b structurally | I-4a against a **second emitter**; I-4b incl. Unicode |
| 8 | I-4c end to end | **native 7 vs 8**; correct receipt accepts only the 7-term |
| 9 | extra unused input in the positive witness | `{x,y,unused:999}` ≠ `inputs_sem_id`, **same term** |
| 10 | missing-input refusal stays open | unchanged in `REFINEMENT_SCOPE` |

## The measurement that matters: building it moved neither id

My first version of this case spread the STATUS fields over the SEMANTICS record and hashed the
result — which measures **nothing**, since status keys are not *in* the hashed object and adding them
changes the hash by construction. The real check is an equation:

> Put back **only** `op_lowering_rules` and **only** `emission`, and the B1.2.1 identities return
> exactly — `lsem-84c9344790a…`, `isem-6ac0ea7b0d1…`.

So those two fields are the only hashed bytes B2 touched, and everything the round actually **built** —
`input` lowering, `instantiate()`, removing `target_term`, three falsifiers going DECLARED →
WITNESSED, every lifecycle flag flipping — **moved no identity at all.** That is what B1.1 split the
records to make possible and this is the first round able to exercise it.

The two ids did move, for the two changes you ruled: the rules became structural (`lsem`), and the
emission split trigger left the hashed semantics for STATUS (`isem`).

## On §3 — you were right that B1.2.1 had the trigger in the wrong record

Putting the split trigger inside `INSTANTIATION_SEMANTICS` was **re-committing B1.1's own finding**:
governance prose inside a relation identity, so rewording a note about what the project should do next
re-identifies the relation. It is in `INSTANTIATION_STATUS` now with all four conditions. Your
underlying rule is the one I recorded, because it generalises past emission:

> keep A∘B one relation while nobody needs to name, vary, verify, reuse or observe A independently of B.

## I-4a came out stronger than the falsifier asked for

The claim was "different allocation → same `target_template_sem_id`". A hostile second emitter
(`_impl17`/`q93` binders, labels from 100) emits **189 characters** where the real one emits 129, from
the same template. Same template id, as claimed — **and both terms reach the identical canonical
normal-form signature.** Allocation is non-semantic all the way down to the runtime. Measured, not
assumed.

## Four instrument defects found this round, three of them mine and new

1. **Two grid assertions had become ratchets.** The inputs model was pinned `implemented: false` with
   `lower-input-not-implemented` required present — correct for three passes and **guaranteed to fail
   on the round that fixed it**. Same species as `canonical-lowering@1`'s "keep it DEFERRED", one file
   over. The `REFINEMENT_CHAIN` assertion required `exercised: false` to exist; it now requires the
   *mechanism* (a flag on every node, a `why_not` on every node lacking one), which holds in both states.
2. **`consumed_inputs` was being answered by the implementation.** The assertion guards a *semantic*
   commitment; once `instantiate()` returned a field of the same name, renaming the semantics field
   left grid_check green. Caught by the battery going `exit=0`. Now scoped to the semantics block.
3. **A check I wrote this round would have refused the correct architecture.** "lower() must not
   return a target_term" tested the whole file for `target_term: emit(` and matched **`instantiate()`'s
   own emission**. Scoped to `lower()`'s body.
4. **Parentheses are an empty regex group.** Six new battery cases reported `exit=1 … wanted /lower()
   must INTERPRET it/` against a *correct* refusal, because the pattern silently matched `lower must
   INTERPRET it`, which is never printed. All paren-free now.

Plus: **three law forgeries had been retargeted at history by a revision bump** — they keyed on
`e['revision'] == 2`, so revising the law pointed them at a superseded entry and they perturbed
history while leaving the live statement alone. They key on `canonical` now, the same correction your
B1.2.1 review forced on grid_check's own lookup.

## Questions

1. **`closed_template` is returned by `instantiate()`** alongside the bytes. Today it is a
   convenience for the witness. By your own split trigger, condition (4) is *"the closed-template
   intermediate becomes an independently identified or externally observed artifact"* — does returning
   it already count as **observed**, or does the trigger want an *identity* on it before it fires? I
   have read it as identity, so it stays unidentified, but it is the closest of the four to firing.
2. **The DUP scope.** `x + (x + y)` reaches native NF and decodes, but I have not put it through the
   *film* path — the fixture may enable a DUP rule, which `ic32_film` refuses by name. Should the next
   round make I-4c film-evidenced too, or does `church_exp_2_2` cover that ground better?
3. **`op_lowering_rules` interpretation depth.** `PRECONDITION` and `TRANSFORM` are closed tables of
   two and one entries. Is a closed vocabulary the right shape, or should a rule be able to name a
   predicate the core already defines?

## Files

- `governance/lowering.mjs` **0.6.0** — structural interpreted rules, `instantiate()`,
  `instantiationReceipt()`, `target_term` removed, `SUPERSEDED_PROSE_RULE_SEM_IDS`, the four-condition
  split trigger in STATUS
- `governance/lowering_check.mjs` **19/19** — six new cases: migration theorem, receipt discipline,
  I-4a/I-4b/I-4c, and the revert-and-compare identity equation
- `governance/grid_check.mjs` — B2 assertions; three B1-era assertions de-ratcheted; two scoping fixes
- `governance/negative_battery.sh` **260/260** — 20 new, 2 deleted for dead premises, 10 repointed
- `governance/invariant-grid.json` **v1.38.0** — three law revisions, predecessors kept as history
- `governance/round-11-ledger.md` — items 233–247
