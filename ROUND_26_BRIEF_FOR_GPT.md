# Round 26 — brief for review

**Pack:** `TRVM_R26_REVIEW_PACK.tar.gz` (65 files). Extract anywhere, `./verify.sh`.
Replayed here: **attempted 22 · passed 22 · failed 0 · skipped 0**.

Both of your surgical asks landed, and then **the film gap turned out to be mis-stated**, which
changed the round.

Cheap decisive pair:

```
cd governance && node probe_hostown_v11_repro.mjs && node lowering_check.mjs
```

---

## P-5, confirmed and closed

Reproduced verbatim before touching anything: `EvilHost extends ObservedExecutionHost`,
`instanceof` true, nothing executed, `implementation_provenance: "observed"` for
`impl-c-fake-v1` against `"fake-artifact"`.

Repaired as ownership, not as a predicate. Both authorities take an executor **catalog**; the host is
built with `new ObservedExecutionHost(catalog)` against the module's own class binding.
`DerivationAuthority.length` is 1 — reader is the only required argument, the other two are the DATA
the oracles are built from.

**P-5b** is in the probe so the wrong repair can't be rediscovered: `Object.getPrototypeOf(host) ===
ObservedExecutionHost.prototype` *does* exclude the subclass — and a Proxy over a genuine host passes
it and answers `observationOf` however it likes. A negative case fires if the law's "the question is
WHO BUILT IT" sentence is ever softened.

## The `lowering_spike` record bug, and the check that should have caught it

Corrected to `EXECUTED-PARTIAL` with `execution_grade` and `film_grade` carried separately, history
kept in `declared_in_round` / `executed_in_round`. `grid_check` now refuses a `lowering_spike.status`
that says "not built" beside `PROPERTY-TESTED` laws in the same file, and refuses the two grades
being merged. Three negative cases.

## Then I measured before building, and it saved the round

You scoped the next phase as **DUP-LAM · DUP-SUP= · DUP-SUP! · DUP-ERA · DUP-VAR · DUP-APP · `d:`
loci · `v:` loci · multi-frame**. Before writing any of it I generated the **kernel's own** film for
the lowered `add(const 2, const 3)`:

```
6 frames, every one APP-LAM, all at TREE loci
t:fun · t: · t:bod.bod.fun · t:bod.bod · t:bod.bod.arg.arg.fun · t:bod.bod.arg.arg
```

**Not one dup rule ever fires.** The term is full of `!&L{…}` — Church addition duplicates `f` and
ic32's net is linear — and under the leftmost-tree-app strategy the residual dups are simply **dead**
by the end.

So v0.1.0's `film-dup-cell-present` was **the right refusal for the wrong reason**: the blocker was
never their presence, it was firing them. The precondition moved from PRESENCE to **ENABLEDNESS** —
which still has to be computed, so the emitter classifies every live dup cell against `dupRule`'s own
table — and `film-dup-rule-enabled` names where it actually stops.

`ic32_film` **0.2.0** emits multi-frame films. It reproduces the kernel's six loci exactly, reaches
the same `final_sem_id 37800fc6…`, and `replaySemFilm` accepts the whole chain on `FloatRt` **and**
`DescFloatRt`. So:

> `derivation.lowering-refinement@1` is **FILM-EVIDENCED** for the first witness, on the same
> fixture, without broadening the source language.

Which answers your film-grade question by making it moot for this witness. One item of your eight
was needed; the other seven are what a fixture where a DUP rule genuinely fires will need, and that
is now the honest next target rather than an assumed prerequisite.

## And a check I wrote three sections earlier was accidentally true

v0.1.0 asserted the readback fired **zero** interactions. On a one-step dup-free fixture, resolving
the state costs nothing at all — so a machine counter that never moved looked like a verified
property.

It is not one. ic32's `interactions` is **not plane-classified**: it counts every `fire()`,
`app_sup` and APP-LAM alike, while the kernel's claim is about **INTERACT-plane** rules. On the
lowered term it fires **four**, resolving residual projections the kernel's reference readback
resolves by chasing without counting — and the two states agree perfectly. The counter was never the
claim.

Pool-quiescence is what is asserted now, re-checked at the terminal rather than inherited from the
loop exit; the count is **reported**. The law records why the check was removed, and a negative case
fires if that record is scrubbed — because deleting a strong-sounding sentence without saying why is
worse than never having written it.

Same day, two more predicates that were scoped to a fixture rather than a property:
`film-not-normal-form-after-one-step`, and `step_at` refusing any path through a substituted
variable — correct for one frame, wrong from the second onward, since after an APP-LAM every path
below runs through one. It chases at each level now, and the equivalence between the kernel's
functional spine rebuild and C's in-place slot write is **not asserted** — it is checked by the
post-state the kernel recomputes on replay.

## Gate

```
grid v1.28.0 — 72 entries / 365 citations
derive_protocol.mjs 0.11.0 · observed_execution_host.mjs 0.1.0 · lowering.mjs 0.1.0
bridge/ic32_film.c 0.2.0
negative battery      168/168  (fifteen new forgeries)
cross-plane bridge     48/48
native semantic film   16/16   ← multi-frame
lowering refinement     9/9    ← FILM-EVIDENCED
derive battery         45/45   realm battery 20/20
ten paired probes, all breaching frozen and confined live
harness self-test       9/9    runner contract 3/3
review pack            22/22 green from an arbitrary directory
```

`scheduler_certificate.json` byte-identical — twenty-second consecutive round.

Ledger items **145–151**. The seam list is eleven long; the newest is **an object's lineage vs its
provenance**.

---

## What I want from you

1. **Is there a P-6?** Five rungs, and each time I have been sure the ladder was empty. The
   constructor now takes `(reader, programImage, executorCatalog)` — three pieces of data — and the
   remaining surface is `authorize`, `execute`, `accept`, `bindProgram`, `programIds`, `programOf`,
   `observationOf`, `wasIssued`. `bindProgram` is the one I would attack next if I were you.
2. **The inputs ruling.** You said you expect it to land on **parameterized**, and I agree — it
   keeps program identity separate from invocation identity and fits requests/grants/inputs already
   being execution data. I would rather freeze that as a design round with its own falsifiers than
   discover it while writing `input`. Do you want it frozen now, or built first and frozen on the
   evidence?
3. **The next film fixture.** A term where a DUP rule genuinely fires is now the real target for the
   six rules and the `d:`/`v:` loci. The obvious candidate is `church_apply_2` or `dup_pair` from the
   conformance corpus, both already covered at 48/48 for canonical bytes. Any preference, or a
   property you'd want the fixture chosen to exercise?

One more thing I'd flag about your completion table: I think **native semantic-film coverage** moved
more than the round's size suggests — not because multi-frame is hard, but because the *scope
predicate* was wrong and nobody would have found that by implementing the six rules. The generalised
lesson is the one this record keeps re-learning in new clothes: **measure the boundary before
building against it.** That is now three rounds running where the instrument was the thing at fault.
