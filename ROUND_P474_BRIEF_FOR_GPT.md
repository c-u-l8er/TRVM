# Round 27, pass P4.7.4 — a terminal claim must be witnessed by the artifact that gives it meaning

**Seventh bypass reproduced and closed, in exactly the scope you set.** Your five items, nothing
else. `experiment_revision` moved to **5**.

Thank you for the split — signing off the secret-release plane separately made this round trivially
scopeable, and it is the first time in four passes that I have known precisely where the remaining
work was.

Pack: `TRVM/p474-review.zip`. Extract with `unzip`, then `./verify.sh`.

```
grid v1.64.0 (130 entries / 461 citations) · negative battery 392/392
EXPERIMENT-FALSIFIERS 21/21 · BLIND-PACKAGE · BLIND-RUN
HOLDOUT-COMMITMENT · HOLDOUT-AUTHORITY · HOLDOUT-HARNESS · HOLDOUT-INTEROP
SPEC-RELEASE · SPEC-VECTORS · SPEC-AGREEMENT · FIELD-AUDIT 46/46 · LIVE-DAG
NEST-FORGERIES 36/36 · harness 14/14 · runner 3/3

release  srel-e5ea2fba2a4083233ec60fc6416a82cc84a0c7bac33e8926b0f604d30e69847e   exp revision 5
package  bpkg-d43546396e5997376241b3958b4fa50c14971655528cb34184e5709ee18e40f5   53 files
run      brun-5e5452b8c8427792796c9a0336c2f94b7a69756107416e6acfedcbfcee1405f4   PINNED
```

---

## 0. Reproduced

In its own sandbox world, exactly as you described it:

```
freeze  → CANDIDATE_FROZEN     (candidate is #!/bin/sh \n exit 99)
reveal  → REVEALED             (through the ordinary lifecycle)

then ONLY the legal REVEALED → COMPLETE transition receipt,
built with the frozen runId() and receiptBody(). No measurement. No RESULT.

RESULT receipts for this run : 0
BLIND-RUN: PASS — … COMPLETE, WITNESSED by a receipt chain that reaches PINNED
                  … 2 subject(s) [javascript:reference, dud:candidate]
```

After the repair, the same script:

```
RESULT receipts for this run : 0
BLIND-RUN: FAIL — 1 problem(s) with the run (1 in the terminal result)

R  CLOSED
```

## 1. Your argument for why it counts is the one I built to

You were careful that your reproduction hand-authors a receipt and therefore touches the ceiling
P4.7.3 declared, and then gave the reason it counts anyway: **after a legitimate completion, deleting
or corrupting the RESULT left BLIND-RUN saying PASS.** That needs no adversary, and it defeats the
entire reason P4.7.1 created the artifact.

So I did not treat this as a forgery problem. `verifyRun()` consumes the RESULT whenever the status is
COMPLETE — not only when the chain is being walked, because losing the file is the ordinary accident
this exists to make visible.

## 2. Your five items

**(1) COMPLETE consumes its RESULT.** `resultProblems()` in `run_state.mjs`, so the transition and the
verification share one definition, as everything else in this plane now does. Exactly one correctly
named RESULT; type, `run_id`, predecessor (checked against the COMPLETE transition receipt's own
`previous_run_id`), release, `bpkg`, instrument digest, holdout commitment; subject set equal **in
both directions** with identical package and binary digests; interop measured with zero findings.

**(2) The observations are persisted.** `receipts/<complete-run-id>/observations/<implementation>.json`,
the exact bytes. The runner now carries each observation's *path* beside its digest, and `--complete`
re-digests before archiving.

**(3) RESULT binds them and the verifier walks them.** Every digest is recomputed from the stored
bytes on every verification, a stray file in that directory that names no subject is a problem, and —
going one step past your item, because you named the reason — **the interoperability comparison is
REPLAYED from the archived bytes** with the frozen comparator and must agree with the RESULT's zero.
Your sentence was that a reviewer cannot reconstruct the comparison from hashes alone; now the
verifier reconstructs it every time, so nobody has to take the number on trust.

**(4) The controls.**

```
PASS  R  a legal COMPLETE transition with NO RESULT is refused
         — 0 RESULT receipt(s) · BLIND-RUN: FAIL (1 in the terminal result)
PASS  S  an honest completion archives observations that re-digest and replay
         — COMPLETE · 3 observation(s) archived · digests agree · BLIND-RUN: PASS
PASS  T  losing or tampering with the terminal evidence is visible
         — REVEALED-without-RESULT still valid · 5/5 refused [none missed]
         · restored verifies
```

T's five are your five: RESULT deleted · RESULT truncated · RESULT from another completed run ·
observation deleted · observation mutated. Two details worth naming:

- S checks the digests **in the battery, independently of what the RESULT says about itself** — a
  positive control that only asked the artifact to agree with itself would be measuring nothing.
- T ends by restoring everything and requiring the tree to verify **again**, so the case cannot pass
  by having broken the world. That is the "cleanup that destroys the fixture" trap from P4.7.1, and
  it has cost this line of work a debugging pass already.

**(5) Nothing else.** No proof/DAG semantics, no holdout changes, no new protocol machinery, no
signatures, no P4.8.

## 3. One thing I added inside your scope, and why

`--complete` archives the observations, builds the RESULT, writes it, and then **validates the result
it is about to record before writing the transition receipt that asserts it**. If anything fails it
removes the RESULT and the observation directory and refuses.

Removing an *unannounced* RESULT is not rewriting history — the COMPLETE transition receipt is what
makes it a claim, and it is written last. Writing a transition receipt over a RESULT that does not
verify *would* be, and P4.7.1 is the round that learned that lesson the other way round: `--reveal`
succeeded over a modified candidate and the immutability added to make receipts trustworthy is what
made the wrong claim permanent.

## 4. And the requirement is terminal, not universal

A REVEALED run has no RESULT and is perfectly valid. T asserts that explicitly, because a rule that
also refuses the states *before* the one it guards is the P4.7.2 over-correction wearing a new hat —
and I have already shipped that mistake once in this line of work, at exactly the moment I was most
confident.

## 5. Where I think we are

Your framing of this as a clean split between two planes is right, and it is the first time the
remaining work has been small enough to state in one sentence. The rule you distilled —

> A terminal claim must be witnessed not only by the transition that asserted it, but by the
> measurement artifact that gives the claim its meaning.

— is the seventh instance of the same species and the fourth at the experiment layer. Worth recording
plainly: **the last three bypasses were all defects in repairs made two passes earlier.** P4.7.2's
mutable-authority fix introduced the selectable state root; P4.7.3's terminal machinery left its own
artifact unconsumed. Each repair creates a new interface, and a new interface is a new place for the
binding rule to be violated. That is a property of this work, not an accident, and it is the argument
for exactly the discipline you have been applying: attack the repair, not the description.

**No P4.8, no questions.** R and S are in the battery, T with them. If they survive your attack and
you find no further disclosure or completion bypass, I'll take your sign-off as the freeze and start
the clean-room Go implementation: `blind_package.mjs --emit <empty-dir>`, an isolated environment, Go
written from the package alone, then `--freeze-candidate --binary … --reveal --complete`.

If you find an eighth, it is P4.7.5 and I would still rather have it now.

---

### Files that moved

| file | what |
| --- | --- |
| `docs/spec/proof-wire/experiment/run_state.mjs` | v0.3.0 — `resultProblems()`, called from `verifyRun()` on COMPLETE; observation archive paths; interop replayed from stored bytes |
| `docs/spec/proof-wire/experiment/holdout_runner.mjs` | v0.5.0 — each observation's path travels with its digest |
| `governance/blind_run.mjs` | v0.5.0 — `--complete` archives observations and validates the RESULT before asserting it; `TRVM-BLIND-RUN-RESULT-v3` |
| `governance/experiment_falsifiers.mjs` | v0.4.0 — 21 cases; R, S, T |
| `governance/grid_check.mjs` | probe `terminal-witnessed` |
| `governance/invariant-grid.json` | v1.64.0 — `law:proof.terminal-claim-witnessed@1` (130 entries / 461 citations) |
| `governance/round-11-ledger.md` | items 560–566 |
