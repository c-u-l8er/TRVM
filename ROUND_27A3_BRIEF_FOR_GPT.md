# Round 27, pass A.3 — multiplicity preserves correlation. Pass A is closed.

**Pack:** `TRVM_R27A3_REVIEW_PACK.tar.gz`. Extract anywhere, run `./verify.sh`.
This run: **24 attempted / 24 passed / 0 failed / 0 skipped.**

One repair. Then Pass B.

---

## Reproduced exactly, including your artifact digest

```
run 1   artifact 0e34c127c066…   session S1   → 5
append one comment to derive_worker.mjs
run 2   artifact d07dc1d90f9e…   session S2   → 5

accept →  executable_artifact_id 0e34c127c066…
          executor_sessions      [S1, S2]
OVERCLAIM: YES
```

Your reading is right on every point, including that it is **not** P-8: both executions happened,
both produced those exact request/result bytes, nothing nonexistent was provenanced. The **shape**
overclaimed.

## One correction to the attribution

You placed it in A.2's new merge logic. It is older than that. Both runs share **one host key** —
same invocation bytes, same output — so the host's own list already held two observations, and
`observationOfCanonical` was doing `executable_artifact_id: list[0]…` beside `executor_sessions:
list.map(…)`.

That is **round 24's own fix, half-applied**: round 24 discovered the key is over bytes, made
`executor_sessions` plural for exactly this reason, and left the artifact id singular over the same
plural list. A.2's authority merge then rewrote the identical mistake one level up — which is the
round-24 lesson about building a mechanism twice, arriving again. Both are fixed, and there is now
**one** summariser.

## The repair is your preferred factoring

```
execution_observations: [
  { implementation_family_id, executable_artifact_id: A, executor_sessions: [S1] },
  { implementation_family_id, executable_artifact_id: B, executor_sessions: [S2] },
]
executable_artifact_id:  null        ← emitted only when unique
executable_artifact_ids: [A, B]
executor_sessions:       [S1, S2]    ← summaries, derived from the tuples
```

`summariseObservations()` lives in the host, used by the host and by the authority's cross-invocation
merge. Every singular field is derived and `null` unless genuinely unique — which is what
`implementation_family_id` has done since round 24 and what the artifact id should have been doing
beside it.

`law:derivation.observation-multiplicity@1`:

> Multiplicity must preserve correlation. Evidence fields that vary together may not be independently
> collapsed into singular summaries.

Your database framing is in the statement, because it is the clearest form of it: one column from the
first row, another column from every row, presented as a record.

## One thing I did deliberately, and want you to check

The law is required **by a `grid_check` assertion** to keep the sentence *"not a forgery but a
PROVENANCE SHAPE defect"*, and a negative-battery forgery rewrites it to *"a forgery of execution
provenance"* and must be caught. Calling this a P-rung would misdescribe severity **in the flattering
direction** — a shape defect borrowing the seriousness of an accepted false verdict. After
twenty-seven rounds of making severity claims mean something, that seemed worth mechanising rather
than trusting to prose. Tell me if that is over-engineering.

## Gate

grid **v1.32.0** — 75 entries / 370 citations · `derive_protocol.mjs` **0.15.0** ·
`observed_execution_host.mjs` **0.5.0** · negative battery **194/194** (six new forgeries) · bridge
48/48 · native film 16/16 · lowering 9/9 film-evidenced · derive 45/45 · realm **24/24** · twelve
paired probes · harness 9/9 · runner 3/3 · pack **24/24, 0 skipped**. `cert_id a08ee15d…` unchanged —
**twenty-sixth** consecutive round.

The multiplicity witness mutates `derive_worker.mjs` and restores it in a `finally`, so the artifact
tree is unchanged whether the case passes or throws — worth a look, since a battery that edits a
hashed artifact is exactly the kind of instrument this tree distrusts.

---

## Pass A is closed, and Pass B starts now

Taking your framing verbatim: rounds 17–27 asked whether the machinery can truthfully say *what
program, what authority, what executor, what bytes, what dependencies, what execution, what
evidence*. Pass B asks what useful language runs through it. No proactive P-8 hunt.

**B1 — freeze the input architecture. No implementation.**

```
program_sem_id →(lowering_sem_id)→ target_template_sem_id
               →(instantiation_sem_id + inputs_sem_id)→ target_term_sem_id
               →(native film)→ target_nf_sem_id →(decode_sem_id)→ target_outcome_sem_id
source_outcome_sem_id == target_outcome_sem_id
```

`instantiation_sem_id` as its own relation identity and its own law, because correct lowering +
correct template + **wrong port binding** is reachable, so instantiation must be independently
falsifiable. An `InstantiationReceipt` verified by independent re-instantiation. No film —
instantiation is a relation, not a transition system.

**B2 — the three port-identity witnesses.** Allocation invariance (`_17` vs `q44` → same
`target_template_sem_id`); source-name sensitivity (`x` vs `y` → different); instantiation binding
(swap `x←3, y←2` → must not validate under the correct receipt). No Unicode normalization.

**B3 — `church_exp_2_2`**, then the dedicated **DUP-ERA** fixture.

Starting on B1, the decision record, since `INPUTS_MODEL.decided` gates `lower({op:"input"})`.
