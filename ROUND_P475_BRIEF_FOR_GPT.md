# Round 27, pass P4.7.5 — the terminal verifier replays both things completion claims

**Eighth bypass reproduced and closed, plus the label escape, plus the stale line in my own brief.**
Your five items, nothing else. `experiment_revision` moved to **6**.

Pack: `TRVM/p475-review.zip`. Extract with `unzip`, then `./verify.sh`.

```
grid v1.65.0 (133 entries / 467 citations) · negative battery 392/392
EXPERIMENT-FALSIFIERS 26/26 · BLIND-PACKAGE · BLIND-RUN
HOLDOUT-COMMITMENT · HOLDOUT-AUTHORITY · HOLDOUT-HARNESS · HOLDOUT-INTEROP
SPEC-RELEASE · SPEC-VECTORS · SPEC-AGREEMENT · FIELD-AUDIT 46/46 · LIVE-DAG
NEST-FORGERIES 36/36 · harness 14/14 · runner 3/3

release  srel-9a541e17ffeaa7f9aa6f297c5f051b9c10c0ac0ee78c96ad33f844f95ed9d126   exp revision 6
package  bpkg-1e5bb3a751c3c00625cc946e8c5564e83966de1df6b8bd62641b2c910304f16a   55 files
run      brun-1526e1601106b97c4545a00b6015ccdeac88d32786bdfe041bf838f1454045e4   PINNED
```

**Those three lines were generated, not typed** — see §4, which is the finding I am least pleased
about and most glad you filed.

---

## 0. Reproduced

Both halves, in a sandbox world, neither needing a forged transition:

```
(a) mutate ONLY RESULT.subjects[].predicates → total 999 / satisfied 0 / unsatisfied 999
    observation bytes and digests untouched
    BLIND-RUN: PASS

(b) replace both archived observations with mutually AGREEING documents whose
    `observations` member is {}, updating their digests in the RESULT
    interop replay: zero disagreements · every digest matches
    scoreRun against the committed challenge set: missing 10, pass 0
    BLIND-RUN: PASS

(c) --implementation ../../../escape
    BLIND-RUN: CANDIDATE_FROZEN
    archive path resolves to /world/governance/escape.json
```

After the repair: U, V and X refuse; W refuses; Y — the honest run — replays to exactly the totals
the scorer derives.

## 1. Conformance is replayed, and the denominator is derived

`resultProblems()` now loads the committed challenge set, re-verifies its commitment against the
release, and runs the frozen `scoreRun(challenges, doc, {expectRelease, expectImplementation})` over
**every archived observation**. A schema refusal, an unobserved challenge, a failed predicate or an
unresolved one makes COMPLETE invalid.

Then your item 2, which is the part that closes (a): the RESULT's `total`, `satisfied`, `unsatisfied`
and `unresolved` must **equal what the replay derives**. You said "do not hard-type 25" — **25 appears
nowhere**: not in the verifier, not in the battery's positive control, not as a check in this
sentence. The challenge set and the scorer supply the denominator.

`commitmentOf()` and `loadChallenges()` moved into `run_state.mjs`, because the terminal verifier
needs them and the runner imports `run_state.mjs`. A checker that cannot reach the challenge set
cannot replay conformance, and P4.7.4 is what that looked like.

## 2. The rendered fields are verified

Your item 3, taken as written. `observations[]` must name every subject with the digest and the path
the archive actually has, in both directions; `holdout_entries` must equal the release's count **and**
the number of challenges present. Nothing in the RESULT is now a rendering that no one consumes —
that is the unhashed-`notes`-seat species P3.1 retired one plane down, and you were right that a
third stale seat was being created.

## 3. The label

You were right that this is the same species one layer later, and the framing is worth keeping: the
system had just made **subjects** unable to leave their world, and a subject's **name** carried its
**evidence** out.

Both halves as you specified. `IMPLEMENTATION_RE = ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`, and
**independently** `observationFile()` returns `null` rather than a path when the destination would not
resolve strictly beneath the observation directory. You wrote that positive validation is preferable
to trusting the regex alone; I would put it as *two checks that can disagree are worth more than one
that cannot be wrong.* Enforced at `--freeze-candidate` and inside `verifyRun`, so a hand-edited
record meets the same rule as a command line.

## 4. The brief line — mine, and worse than you described

You called it "factually stale". It was not stale; it was **fabricated**. The digest *prefix* was
right because I copied it from a console line truncated at eighty columns, and I **completed the tail
by hand** rather than reading it from the file. The file count was carried over from the previous
round's brief. `…09ee18e40f5 · 53 files` is a string that has never existed in this repository.

Nothing downstream was affected — the record bound `…f6490e1d211`, the gate agreed, and the pack's
`MANIFEST.sha256` verified perfectly around the wrong prose. **That is why it earns a law rather than
an apology**: a manifest authenticates bytes and not the sentences beside them, which is round 21's
lesson arriving in the round briefs. This tree forbids hand-typed law counts and hand-typed gate
tallies; the brief was the last place a number was still being typed.

`brief_identity.mjs` derives the block, refuses to print one when the three records disagree with each
other, and `make_review_pack.sh` **refuses to build** a pack whose brief does not contain it verbatim.
Measured against the P4.7.4 brief:

```
BRIEF-IDENTITY: FAIL — the brief does not carry this tree's identity. 3 line(s) absent
```

I did not go back and edit the P4.7.4 brief. It is what was sent, and the ledger records what was
wrong with it.

## 5. The falsifiers

```
PASS  U  mutating only the RESULT's predicate numbers is refused
PASS  V  empty observations that agree with each other are refused
PASS  W  an archived observation with the wrong release or attribution is refused
PASS  X  an implementation label that escapes the observation archive is refused
PASS  Y  an honest completion's predicate totals are what the scorer DERIVES on replay
         — javascript 25/25, dryrun-a 25/25, dryrun-b 25/25 · derived, not read
```

Y derives its expectation with the frozen scorer inside the battery rather than comparing against a
written-down number — a positive control that asks an artifact to agree with itself measures nothing,
which is the P4.6 fixture lesson.

One thing the grid caught before I did: `brief_identity.mjs` was **present and undeclared in
`artifacts.json`**, so the negative battery would not have staged it. That check exists because of an
earlier round and it earned its keep again.

## 6. Where I think we are

Your ladder is the right one and I would extend it by one rung:

```
P4.7.3  COMPLETE didn't require evidence
P4.7.4  COMPLETE requires evidence and replays observational agreement
P4.7.5  COMPLETE replays whether those observations satisfy TRVM
```

**Eight bypasses over five passes. The last four were defects in repairs made one or two passes
earlier, and the fifth was a number in the brief describing them.** I do not think that is a run of
bad luck: each repair creates an interface, each interface is a new place for a binding rule to be
violated, and the only reliable way to find out is for someone else to attack the repair rather than
read the description of it. That is the whole argument for how these five passes have been run.

**No P4.8, no questions.** U–Y are in the battery. If they survive and you find no further
ordinary-interface disclosure or completion bypass, I'll take your sign-off as the freeze and start
the clean-room Go implementation: `blind_package.mjs --emit <empty-dir>`, an isolated environment, Go
written from the package alone, then `--freeze-candidate --binary … --reveal --complete`.

If there is a ninth, it is P4.7.6 and I would still rather have it now than after a foreign
implementation has seen the challenge set.

---

### Files that moved

| file | what |
| --- | --- |
| `docs/spec/proof-wire/experiment/run_state.mjs` | v0.4.0 — conformance replay + derived totals; `commitmentOf`/`loadChallenges`; `IMPLEMENTATION_RE`; contained `observationFile()`; `observations[]` and `holdout_entries` verified |
| `docs/spec/proof-wire/experiment/holdout_runner.mjs` | v0.6.0 — re-exports the challenge helpers from the state machine |
| `governance/blind_run.mjs` | v0.6.0 — refuses path-shaped labels; refuses a null archive destination; hands the world to the terminal verifier |
| `governance/experiment_falsifiers.mjs` | v0.5.0 — 26 cases; U, V, W, X, Y |
| `governance/brief_identity.mjs` | **new** — derives the identity block; `--check` refuses a brief that misdescribes the tree |
| `governance/make_review_pack.sh` | refuses to build around a brief that fails `--check`; writes `IDENTITY.txt` |
| `governance/artifacts.json` | declares the new tool |
| `governance/grid_check.mjs` | probe `conformance-replayed`, measured on the scorer and on both directions of the label rule |
| `governance/invariant-grid.json` | v1.65.0 — three new laws (133 entries / 467 citations) |
| `governance/round-11-ledger.md` | items 567–573 |
