# Round 27 A.4 + B1 — your two cleanups, then the inputs model is frozen

**Pack:** `TRVM_B1_REVIEW_PACK.tar.gz`. Extract anywhere, run `./verify.sh`.
This run: **24 attempted / 24 passed / 0 failed / 0 skipped.**

---

## A.4 — your two cleanups

**1. Severity is a field now, not a sentence.** You were right that checking the exact English was the
over-engineering. Entries carry structured metadata against a declared `defect_class_vocabulary`:

```json
{ "defect_class": "provenance-shape",
  "accepted_false_verdict": false,
  "underlying_observations_genuine": true }
```

and the contrast is in **data**: `derivation.entry-snapshot@1` and `derivation.owned-snapshot@1` are
`authority-forgery` with `accepted_false_verdict: true`. Any entry declaring a `defect_class` must
declare a known one *and answer both questions* — a class name alone re-creates the prose problem with
fewer characters. The prose sentence stays in the statement; nothing checks it.

**2. The NUL came back, and it was mine.** A.3's new grouping key reintroduced the raw byte into the
same file A.1 fixed, four commits later, under a comment explaining the hazard. `grid_check` now scans
every governance `.mjs/.js/.sh/.json/.md/.c/.h/.py` file in the root and `bridge/` and fails on any
literal NUL, naming file, offset and line.

**It caught its author on the first run.** `grid_check.mjs` itself contained one — in the comment
explaining the hazard, where the escape had been pasted as the byte it describes. Three occurrences
in one round, across three files, none visible to `grep`. The check is the argument for the check.

A negative-battery forgery rewrites the escape back into a raw byte and must be caught.

---

## B1 — the inputs model, decided and not built

**"Parameterized versus instantiated" was a false choice.** The template is parameterized **and** the
executed term is necessarily closed. Two relations, two identities, exactly the chain you endorsed:

```
program_sem_id ──lowering_sem_id──▶ target_template_sem_id
               ──instantiation_sem_id + inputs_sem_id──▶ target_term_sem_id
               ──native film──▶ target_nf_sem_id ──decode_sem_id──▶ target_outcome_sem_id
                                          source_outcome_sem_id == target_outcome_sem_id
```

Frozen in `lowering.mjs` **0.2.0**: `INPUT_PORT_SPEC`, `INSTANTIATION_SPEC`, `INSTANTIATION_SEM_ID`,
`inputsSemId`, `portSemId`, `INSTANTIATION_RECEIPT_FIELDS`, and `law:derivation.instantiation-identity@1`.

- **The relation, not the invocation.** `instantiation_sem_id` commits to port namespace/version, the
  source-name→port rule, missing/extra-input semantics, canonical input embedding, substitution
  semantics, refusal vocabulary and conformance vectors. It does not contain `x=5`.
- **Port bound to the source name**, at the canonical target-AST layer as
  `{op:"input-port", source_name:"x"}`, before any variable allocation. Quotient stated exactly:
  internal target variable names non-semantic/alpha-equivalent, source input keys semantic. Recorded
  as **round 16's inverse** — there identity depended on a spelling that should not matter; here the
  danger is depending on an allocation that should not matter while losing the source name that must.
- **No Unicode normalization**, because a quotient introduced at the encoding layer is a
  language-semantic change made where the source cannot see it.
- **No film.** Instantiation is a relation; the instrument is independent re-instantiation against an
  `InstantiationReceipt`.

### Three things I want you to check

**`LOWERING_SEM_ID` moved.** `LOWERING_SPEC` carries `inputs_model`, so deciding the model changes the
lowering relation and its identity. I treated that as correct and re-cut rather than re-pointed — an
id that survived this ruling unchanged would be claiming the decision was not part of the relation.
The 9/9 refinement witness is unchanged and still FILM-EVIDENCED. Tell me if you would have kept it
stable instead.

**The refusal was renamed** `lower-inputs-undecided` → `lower-input-not-implemented`, and
`instantiate()` throws `instantiate-not-implemented`. *"We have not ruled"* and *"we have ruled and
not written it"* are different states, and one refusal string covering both is a stale instrument with
a delay fuse.

**A negative case was deleted, not repointed.** `inputs-silently-lowered` flipped `decided: false →
true` and asserted *"must record the inputs model as UNDECIDED"*. B1 made its perturbation the live
state, so it went VACUOUS. Its premise is what the round reversed, so it is gone with a comment saying
why, and `inputs-model-reverted` guards the new state in the new direction. Deleting a falsifier is
the kind of move that deserves a second reader — a falsifier that outlives its premise has stopped
measuring, but so has one that was removed too eagerly.

### And the law claims nothing about behaviour

The three port falsifiers are **declared as data** — `INSTANTIATION_FALSIFIERS`, I-4a/I-4b/I-4c,
`status: "DECLARED"` — and **none is written**. The law's evidence says it is PROPERTY-TESTED *for the
decision and its refusal surface* and carries no claim about instantiation behaviour, and a
`grid_check` assertion requires it to keep saying that. This is the one place a frozen architecture
can quietly start reading as a working feature.

`lowering_spike.status` was already contradicting the code the moment B1 landed — it still said
*"inputs model UNDECIDED"*, which is the same drift its own `record_correction` field is about, in the
same file. `grid_check` now binds that record to `INPUTS_MODEL.decided` in the source in **both**
directions.

---

## Gate

grid **v1.34.0** — 76 entries / 372 citations · `lowering.mjs` **0.2.0** ·
`observed_execution_host.mjs` **0.5.1** · negative battery **207/207** (ten new B1 forgeries, five
structured-severity/NUL forgeries, one deleted) · lowering refinement **9/9, still FILM-EVIDENCED** ·
derive 45/45 · realm 24/24 · bridge 48/48 · film 16/16 · twelve paired probes · harness 9/9 · runner
3/3 · pack **24/24, 0 skipped**. `cert_id a08ee15d…` unchanged — **twenty-eighth** consecutive round.

---

## Next: B2

The three witnesses, against the now-frozen spec:

```
same source name  + different internal allocation   →  SAME target_template_sem_id
different source name + same allocation strategy    →  DIFFERENT target_template_sem_id
x/y binding swapped at instantiation                →  changes or refuses, and must NEVER
                                                       validate under the correct receipt
```

That needs `input` to actually lower and `instantiate()` to exist, so B2 is where the implementation
lands — behind the falsifiers rather than before them. Then `church_exp_2_2` and the dedicated DUP-ERA
fixture for the native film.
