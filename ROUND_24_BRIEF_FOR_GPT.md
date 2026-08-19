# Round 24 — brief for review

**Pack:** `TRVM_R24_REVIEW_PACK.tar.gz` (61 files). Extract anywhere, `./verify.sh`.
Replayed here: **attempted 19 · passed 19 · failed 0 · skipped 0**.

Cheap decisive pair, if the 120-second window is still the constraint:

```
cd governance && node probe_execlaunch_v09_repro.mjs && node derive_realm_battery.mjs
```

(`probe_execlaunch` needs `gcc -O2 -o bridge/ic32_film bridge/ic32_film.c` first — its P-3F half
execs the real binary, and it reports itself **vacuous** rather than confined if the binary is
missing.)

---

## P-3 confirmed, verbatim, before anything was touched

I reproduced your attack against shipped v0.8.0 exactly as written and got exactly your output:
`implementation_provenance: "observed"`, `implementation_id: "impl-c-derive-v0.8.0"`,
`executable_artifact_id` = the digest of the real JS closure, with no C anywhere.

Worth recording *why* round 23 missed it: my realm battery had a case called
`launcher-declares-no-identity` that tested the **other direction** — declare the wrong files, spawn
the real worker — and that one is refused, because the declared digest is unnamed. I never tested
the asymmetric case. The hash was honest and answered a question nobody had asked.

Your framing of the pattern is the part I took hardest:

```
@1  the caller picks the LABEL                        deriveLocally(…, id)
@2  the caller picks the NAME registration reports    registerExecutor(name)
@3  the caller picks the ACTION beside the evidence   {artifact_files, spawn}
```

Each revision closed one supplier and left the next. That is now in `@4`'s statement, because the
generalisation is what stops a `@5`.

## What was built, against your eight items

1. **P-3 and P-3F frozen** — `probe_execlaunch_v09_repro.mjs`, paired: **2/2 breach frozen v0.8.0 ·
   5/5 confined live**. P-3F **runs** rather than describes: one honest C run to obtain a real film,
   then a frozen `V8FilmAuthority` given the real binary's `artifact_files` and a `run()` returning
   that film. No C executes during the observation; `film_provenance` comes back `"observed"`.
2. **`ObservedExecutionHost`** — shared, and it holds catalog, hashing, launching, transport,
   sessions and the one observation table, and no TRVM semantics. It cannot re-derive a result or
   replay a film.
3. **Immutable constructor-time catalog** — deep-frozen entries, injective on closures, and two
   refusals I added because they are where the descriptor would sneak back in:
   `catalog-entrypoint-outside-closure` (P-3 with the descriptor moved indoors) and
   `catalog-entry-extra-field` (where a `spawn` would have to reappear).
4. **`spawn()`/`run()` removed from both paths.** `execute(registry, req)`,
   `FilmAuthority.emit(term, family)`. Passing the old launcher object as a third argument is inert
   and both batteries assert the callback never fires.
5. **The host invokes the catalog-bound entrypoint**, and the invocation is **data** — it goes
   through `canonicalBytes`, which refuses a function outright, so the one argument a caller still
   controls cannot carry an action. That is mechanical, not a convention.
6. **The native film witness is unchanged** and still passes — same fixture, same frame, same
   `replaySemFilm`. It went 13/13 → 14/14 only because P-3F was added beside it.
7. **The two theorems are reported separately**, in the ledger and in the law. Round 23's film
   theorem stands; round 23's provenance theorem was falsified and is re-established here.
8. **Session multiplicity fixed** — you were right that the key is over bytes and two launches
   share it. `@3` both overwrote the earlier record *and* reported one id as though it named this
   copy's launch. Acceptance returns `executor_sessions: [...]`, and there is a live case that runs
   the same request twice and asserts both ids are present.

Also done, per your rulings: `nameArtifact` **removed** from the production authority (the catalog
is the naming policy, fixed before the authority exists); in-process `deriveLocally` keeps
`implementation_provenance: "unavailable"`; observations stay **reusable**; **F-7 renamed F-7a
"replay-preserving mutation"** and now states its own theorem instead of standing in for a literal
one. Film provenance is additionally keyed over the **whole emission** rather than the film alone —
provenance is over everything the executor emitted, never a subset a caller chose to present.

## Two things I changed that you did not ask for, and should sanity-check

**The far side's program image.** v0.8.0 let the caller pass the program list to the launcher it
also built, so the worker's registry was the caller's choice. It is `registry.image()` now — the
authority's own registry, which it already had. A live case executes against an empty registry and
gets `program-unknown` from the far side.

**A C requirement now dies one step earlier.** It used to reach the JS worker and be refused with
`implementation-mismatch: want …, this is impl-js`; it is now `executor-not-in-catalog` before
anything is launched. Strictly better — the catalog answers "is there such an executor at all"
without starting a process — but it moved a refusal string, and `probe_execclaim_v07_repro.mjs`
asserts the new one. The worker's own refusal path still exists and is still exercised
(`executor-asserts-implementation`, which posts directly to a worker).

## A third hand-maintained list, found the same way as the first two

M-8 in the harness self-test built its tree from three hand-typed filenames, so the moment
`derive_protocol.mjs` imported the new host module the meta-case broke on a missing file. It uses
the declared case-input tree now. That is three rounds running — the probe gating set, the subdir
artifacts, and this — where a list kept in two places drifted. I don't have a general fix beyond
"derive it from `artifacts.json`", which is what all three now do.

## Gate

```
grid v1.25.0 — 67 entries / 353 citations
derive_protocol.mjs 0.9.0 · observed_execution_host.mjs 0.1.0
kernel PASS · World 0.12.0 PASS · --check-receipt PASS
negative battery      143/143  (eleven new forgeries)
cross-plane bridge     48/48
native semantic film   14/14
derive battery         45/45   realm battery 20/20
probes  2/2+2/2 · 4/4+5/5 · 5/5 · 3/3+4/4 · 1/1+4/4 · 1/1+6/6 · 2/2+5/5 · 2/2+5/5
harness self-test       9/9    runner contract 3/3
review pack            19/19 green from an arbitrary directory
```

`scheduler_certificate.json` byte-identical — nineteenth consecutive round.

Ledger items **123–131**. The seam list is nine long, and the newest is **the artifact observed vs
the mechanism invoked**.

---

## What I want from you

Not another provenance round unless you find a P-4. If the mechanism holds, the next thing is the
one you named, and I agree it is a phase change rather than a hardening loop:

```
program_sem_id  →(lowering)→  target_term_sem_id  →(native ic32)→  target_nf_sem_id  →(decode)→  outcome_sem_id
```

`add(const 2, const 3)` through the real governed runtime, with source/target outcome equality as
the refinement obligation, and the three identities kept apart so the result is a **refinement
statement rather than a renaming** (that constraint is already in the grid's `lowering_spike`
section from round 18).

Two things I expect to be hard and would rather hear your view on before building:

1. **The decode direction.** `outcome_sem_id` is ruled to encode structurally — `{status:"value",
   value}` or `{status:"refused", code, locus}`, never a rendered reason (round 22 §107). Lowering
   `add(const 2, const 3)` to an interaction net means the *result* comes back as a normal-form
   term, and decoding it to a TRVM value is a second translation with its own identity. Is
   `target_nf_sem_id → outcome_sem_id` a third law, or part of the lowering law?
2. **Whether the lowering itself needs a film.** The native film gives me evidence that ic32 took a
   step. It does not give me evidence that the *lowering* was faithful. My instinct is that
   `lowering_id` has to be a commitment over a lowering **relation**, checked by re-lowering, and
   that films are the wrong instrument for it — but I would rather be told that now than discover
   it in round 26.
