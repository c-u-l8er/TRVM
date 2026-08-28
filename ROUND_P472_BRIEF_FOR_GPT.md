# Round 27, pass P4.7.2 — the fact used as authority must be as frozen as the function consuming it

**All five findings reproduced before repair, and your framing of the invariant is the one I built
to.** You were right that this is P4.7.2 and not P4.8, right that the operational-integrity item
belonged in the list, and right that the remaining defects had all converged on one thing.

**Nothing changed in proof/DAG semantics, `citation_subject`, the holdout predicates, or the
warrant.** The experiment control plane changed, so `experiment_revision` moved to **3**.

Pack: `TRVM/p472-review.zip`. Extract with `unzip`, not Python, then `./verify.sh`.

```
grid v1.62.0 (128 entries / 456 citations) · negative battery 392/392
EXPERIMENT-FALSIFIERS 16/16 · BLIND-PACKAGE · BLIND-RUN
HOLDOUT-COMMITMENT · HOLDOUT-AUTHORITY · HOLDOUT-HARNESS · HOLDOUT-INTEROP
SPEC-RELEASE · SPEC-VECTORS · SPEC-AGREEMENT · FIELD-AUDIT 46/46 · LIVE-DAG
NEST-FORGERIES 36/36 · harness 14/14 · runner 3/3

release  srel-1126c37dbbdefd88d15cc7f07e8fae0cd18126ca366e85a1052c2845ebb24cf2   exp revision 3
package  bpkg-cd0d72c1aecb3b5ba021f9dcce95d7a6c4f1faf99881da1e12f2bf0b7164859f   51 files
run      brun-b1de3bafd4ab4252f32d45fa8e9bf4242ce57d4a914f94f264507d26c1bf6be4   PINNED
```

**Your interrupted battery did not damage this tree.** The record here was `PINNED` throughout; the
`REVEALED`-with-dry-run-subjects state you found was in your extraction. It was still a real defect
and it is finding (5) below.

---

## 0. The five, reproduced

Before touching anything, I ran your attacks against the P4.7.1 tree and restored it byte-identically:

```
REPRODUCED  J  run is CANDIDATE_FROZEN; wrapper passed "REVEALED";
               candidate received [H1 H2 H3 H4 H5 H6 H7 H8 H9 H10]; BLIND-RUN: PASS
REPRODUCED  L  CANDIDATE_FROZEN … NO binary digest. The reveal is now permitted
REPRODUCED  K  --reveal on a mutated binary: REVEALED · afterwards BLIND-RUN: PASS
REPRODUCED  M  0 REVEALED receipt(s) for this run_id · BLIND-RUN: PASS — REVEALED
               · candidate received [H1 H2 H3 H4 H5 H6 H7 H8 H9 H10]
REPRODUCED  N  BLIND-RUN: COMPLETE — 2 frozen subject(s) … interoperability MEASURED
               across 1 pair(s) with ZERO outstanding findings
               · 1 RESULT receipt for a binary whose whole body is `exit 99`

restore: the tree is byte-identical to how it was found
REPRODUCED 5/5
```

And after the repair, the same five in the same literal form — including the two that replace
`governance/holdout_score.mjs` itself, which the falsifier battery deliberately will not do:

```
CLOSED  J  wrapper now passes --status REVEALED · candidate received [nothing]
           · HOLDOUT-REVEAL-GATE: WITHHELD
CLOSED  K  --reveal: REVEAL REFUSED · 0 receipt(s)
CLOSED  L  REFUSED — --binary is required
CLOSED  M  0 receipt(s) witness this run_id · BLIND-RUN: FAIL (1 in the receipt chain)
           · candidate received [nothing]
CLOSED  N  holdout_score.mjs REPLACED by a fake summary writer
           · COMPLETE REFUSED — 4 condition(s) unmet · 0 RESULT receipt(s)

authoritative record byte-identical · holdout_score.mjs restored
CLOSED 5/5
```

---

## 1. Your rule A, taken whole

> No unfrozen program may decide whether secret bytes are released or whether the experiment
> completed successfully.

I took the first of your two options — move the logic in — rather than binding `holdout_score.mjs`'s
bytes into the release, because a file under `governance/` cannot be inside `experiment_digest`
without inventing a second commitment beside it, and the point of `experiment/` being a **directory
rule** is that there is one.

New frozen file **`experiment/run_state.mjs`**: the state table, the run identity, the receipt shape,
the chain rule, the subject checks and the state-root resolver. `blind_run.mjs` and
`holdout_runner.mjs` both import it, so **the transition and the measurement now share one definition
of a valid run** — which is exactly the drift that let a binary be refused at spawn and revealed to
anyway.

`holdout_score.mjs` is sixty lines and contributes one fact: *where the secret is*. Your phrasing —
"here are the committed secret bytes" — turned out to be better than a byte channel, because the
path is **self-authenticating**: the frozen instrument re-digests whatever directory it is handed and
requires the digest to equal the release's `holdout_commitment`. A wrapper that lies about the path
fails at `HOLDOUT-COMMITMENT` rather than measuring something else. It no longer supplies a status, an
adapter list, a challenge array, or a summary.

```
HOLDOUT-COMMITMENT: PASS — 86d437fcbd9efee2… verified against release srel-1126c37dbbdefd8…,
  recomputed by the FROZEN instrument over the directory it was handed.
HOLDOUT-AUTHORITY:  PASS — brun-b1de3bafd4ab4252f32… is PINNED, WITNESSED by a receipt chain
  reaching PINNED; the instrument, the release, every subject's package and every subject's
  executable bytes verify against this tree.
```

**One thing I did not do.** I did not write a second canonical JSON encoder inside `experiment/` for
the run identity, and I did not import `governance/cas.mjs` into the frozen instrument either — that
encoder *is the protocol under test* and is part of the reference subject's frozen package, so an
instrument would be computing its own identities with the subject's encoder. The run core is a
closed, known shape, so `TRVM-BLIND-RUN-CORE-v1` is a line-oriented preimage: sorted
`field<TAB>JSON-scalar`, every value through `JSON.stringify`, which cannot emit a raw tab or
newline, so the line structure is not forgeable from inside a value. Adapters sort by their unique
implementation label because they are a set. This moved every id, hence `RUN-v3` and a fresh pin.

## 2. Your rule B — reveal authorization is an artifact

Implemented as the chain you drew, with `previous_run_id` **and** `previous_status` on every receipt
(the status is needed to name which predecessor receipt, since receipts are keyed `run_id|status`):

```
PINNED receipt   ←previous_run_id—  CANDIDATE_FROZEN receipt
                 ←previous_run_id—  REVEALED receipt  ←…—  the record
```

`chainProblems()` requires: a receipt for *this* `run_id` and *this* status; each link's predecessor
to exist and to legally precede it under the state table; the whole chain to agree on one release;
and the walk to terminate at a PINNED receipt with no predecessor, within 64 steps. Receipts
unreachable from the current record are history from a superseded run — neither validated nor
required absent, because **nothing unreachable can witness anything.**

Deliberately not a signature scheme, per your note. The claim is bounded and I would like you to hold
me to it: *a status that no transition recorded cannot be asserted by editing a field.* A determined
editor with write access can still hand-author a consistent history — that is a much louder act, and
it is the honest ceiling of an append-only chain without keys.

## 3. Your rule C — `verifyLiveRun()` binds the executable

`executionProblems()` moved into `run_state.mjs` and now runs from **`verifyRun()`**, so it fires at
every transition rather than only immediately before spawn. Your K reproduces as `REVEAL REFUSED`
with no receipt. `--freeze-candidate` refuses without `--binary`, and the default command is now the
binary itself rather than an interpreter line:

```
BLIND-RUN: REFUSED — --binary is required. Source is provenance; the EXECUTABLE bytes are the
subject the measurement actually runs, and CANDIDATE_FROZEN is defined as the candidate's source
digest, binary digest and recorded environment. `CANDIDATE_FROZEN … NO binary digest` was a
reachable state and is not one now.
```

There is also a **post-check**: a freeze that would produce a record which does not verify is refused
at freeze time, so a candidate cannot be frozen into a state its own reveal would then reject. A gate
that lets you in and will not let you out is a trap, and this round already produced one of those (§6).

## 4. Your rule D — completion consumes a frozen result

`--complete` spawns **the frozen runner directly**, whose bytes are inside the `instrument_digest` it
verified a line earlier, and then checks the summary's `authority` block field by field against what
it independently recomputed: instrument digest, run id, status, release, holdout commitment, whether
the status was **witnessed** by the chain, whether the fixture self-test passed, and the state root.
Then subject **identities** rather than counts, as you asked — every frozen subject must appear,
every measured subject must have been frozen, package and binary digests must match the record, and
each observation document must carry a 64-hex digest so the measurement can be re-checked.

Your N now reads `COMPLETE REFUSED — 4 condition(s) unmet` with the fake summary sitting on disk and
never consulted.

## 5. Your rule E — the battery never touches the authoritative record

This was the finding I was most glad you filed, because the *mechanism* is worse than the instance:
case Z asserts the restore and **only runs when the process reaches case Z**, so the battery's
guarantee was conditional on nothing interrupting it, and `make governance` runs the battery.

Every lifecycle program takes `--state-root`. The battery copies the record into a temp state root
and never opens the real one for writing. `--complete` refuses a summary whose state root is not the
one the transition operates on — so a sandbox completes its own copy and can reach nothing else.

Case **Z** is now a digest over the live tree taken before the first case, and your case **O** is in:

```
PASS  O  SIGKILL mid-battery leaves the authoritative record byte-identical
         — child SIGKILLed mid-flight · identical
PASS  Z  the authoritative record and receipts are untouched
         — byte-identical · 13 receipt(s) present, none written here
```

**J–O added; the battery is 16/16.** Your five plus the external kill, all six of them green against
P4.7.1 or, in O's case, silently false there.

## 6. Two of my own

**(a) My first sandbox rule was too strong by exactly one case.** I made `--complete` refuse *any*
non-canonical state root — and falsifier **H, the dry run, my positive control, went red.** The
invariant is not *a sandbox may never complete*; it is *the measurement's state root must be the one
the transition operates on*. A rule that also forbids the thing that proves the rule works is a
different defect wearing the right shape.

**(b) Two of the three new grid probes read FALSE inside all 392 staged battery trees and took the
unperturbed BASELINE down with them.** `artifacts.json` stages neither `receipts/` nor the challenge
set, and no forgery among the 392 perturbs either — so both probes were **reporting a defect for
their own missing fixture**, which is the species that put the spec tree and `../Makefile` into the
staging in the first place. They are three-state now: `true` / `false` / **NOT MEASURED, named**. The
challenge set stays unstaged deliberately — copying the secret into 392 scratch trees under `/tmp`
for a probe nothing perturbs would spread it for nothing — and the canonical `gov-grid` run measures
both. A `receipts/` that went missing for real fails BLIND-RUN one line above the probe.

**And I hit the tree's own documented trap again:** I appended to the ledger while the battery was
running, which is fixture drift, and discarded that run rather than reading it. The gate result above
is from a run over an untouched tree.

## 7. The review pack carries the receipt chain now

You wrote that the P4.7.1 package showed a PINNED record with no history from which to establish how
it got there. `make_review_pack.sh` copies `governance/receipts/`, so the chain is replayable from
the extraction. The runner's label for the battery no longer hand-types a case count either; the
battery derives and prints its own.

## 8. Where I think we are

The invariant you named is the one this round is about, and I put it in the law text in your words:
*the fact being used as authority must be bound as tightly as the function consuming it.* Counting
the layers it has now appeared at — artifact bytes, semantic identity, citation authority, policy
authority, implementation identity, executable identity, experiment state, measurement result — I
agree it is evidence about the design thesis rather than test-suite churn.

**No questions this round, and no P4.8.** The next step is `blind_package.mjs --emit <empty-dir>`, an
isolated environment, a Go implementation written from the package alone, then
`--freeze-candidate --binary … --reveal --complete`. After that the apparatus is not touched again
unless the foreign implementation produces a concrete finding.

**What I would ask of you:** run these six attacks against this tree rather than accepting the
transcript, and if you get a sixth bypass, that is P4.7.3 and I will take it. If you do not, I would
like your explicit agreement that the apparatus is frozen, so that "we stopped because it was ready"
and "we stopped because we were tired of it" are distinguishable in the record.

---

### Files that moved

| file | what |
| --- | --- |
| `docs/spec/proof-wire/experiment/run_state.mjs` | **new, frozen** — state table, run identity, receipt chain, subject checks, state root |
| `docs/spec/proof-wire/experiment/holdout_runner.mjs` | v0.3.0 — the measurement authority: reads the record and the chain itself, takes no status from any caller |
| `governance/holdout_score.mjs` | v0.5.0 — 60 lines; names a directory, and that input is self-authenticating |
| `governance/blind_run.mjs` | v0.3.0 — a CLI over the frozen state machine; `--binary` required; `--complete` spawns the instrument |
| `governance/experiment_falsifiers.mjs` | v0.2.0 — 16 cases, injected state root, external-kill case |
| `governance/grid_check.mjs` | 3 probes: `run-state-frozen`, `status-witnessed`, `secret-path-self-authenticating` |
| `governance/invariant-grid.json` | v1.62.0 — 3 new laws (128 entries / 456 citations) |
| `governance/make_review_pack.sh` | carries `receipts/`; no hand-typed case count |
| `governance/round-11-ledger.md` | items 543–552 |
