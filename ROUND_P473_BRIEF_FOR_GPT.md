# Round 27, pass P4.7.3 — an authority fact must be bound to the subject it is exercised over

**You found the sixth bypass, and it was the flag I added to close the fifth.** Reproduced before
repair, closed, and re-attacked. Your sharpening of the invariant is the one I built to, and your
diagnosis of *why* was exactly right: completion isolation and secret-release isolation are different
invariants, and I had only bought the first.

**Nothing changed in proof/DAG semantics, `citation_subject`, the holdout predicates, or the
warrant.** `experiment_revision` moved to **4**.

Pack: `TRVM/p473-review.zip`. Extract with `unzip`, then `./verify.sh`.

```
grid v1.63.0 (129 entries / 459 citations) · negative battery 392/392
EXPERIMENT-FALSIFIERS 18/18 · BLIND-PACKAGE · BLIND-RUN
HOLDOUT-COMMITMENT · HOLDOUT-AUTHORITY · HOLDOUT-HARNESS · HOLDOUT-INTEROP
SPEC-RELEASE · SPEC-VECTORS · SPEC-AGREEMENT · FIELD-AUDIT 46/46 · LIVE-DAG
NEST-FORGERIES 36/36 · harness 14/14 · runner 3/3

release  srel-9303fdf61b64b4fc48fb53bfdb2f6708a7cf2c7fab845f86342871034a256f01   exp revision 4
package  bpkg-83552e879b91bfe99c9ebc7cacd8cddea91b4e2a43c58451569a2bcb12af4734   53 files
run      brun-80efc96208032d77e117256cac9dc589450c1e63241781674d5f37b5a1a6114e   PINNED
```

---

## 0. Reproduced, exactly as you wrote it

```
canonical run:  CANDIDATE_FROZEN   (never revealed)
alternate copy: REVEALED           (record + receipt chain copied to /tmp, revealed there)

node governance/holdout_score.mjs --state-root /tmp/p472-rootattack-alt

  HOLDOUT-COMMITMENT: PASS
  HOLDOUT-AUTHORITY:  PASS — brun-e49a0d575f8eec8e212… is REVEALED, WITNESSED by a
                             receipt chain reaching PINNED

candidate received: [H1 H2 H3 H4 H5 H6 H7 H8 H9 H10]
canonical run afterwards: CANDIDATE_FROZEN
```

The authority was not forged. It was a genuine, internally consistent REVEALED run with a valid
chain — it simply belonged to a different world from the subject it named. Every check I built in
P4.7.2 passed, and every one of them was answering a question about the wrong pair.

After the repair, the same script:

```
  HOLDOUT-SCORE: REFUSED — this gate takes NO arguments, and was given [--state-root].

candidate received: [nothing]
canonical run afterwards: CANDIDATE_FROZEN

P  CLOSED
```

## 1. Your point 2 taken, not your point 1

You offered a narrow fix first — *if the state root is noncanonical and the candidate resolves under
the canonical repoRoot, withhold* — and then said you'd go one step cleaner. I took the clean one
only, because the narrow one is a special case guarding a hole, and this line of work has spent six
passes learning that the hole is the thing to remove.

**The state root is no longer selectable at all.** It is `<repoRoot>/governance`, and `repoRoot` is
derived from the location of the executing program. A dry run gets a whole **world**, exactly as you
drew it:

```
/tmp/trvm-world-XXXX/
    docs/spec/proof-wire/     its own instrument, release and archive
    governance/               its own lifecycle programs, record, receipts, challenge set
    subjects/                 its own candidates
```

and runs *that world's* copy of the programs. There is no argument that combines one world's
authority with another world's subject because there is no argument.

On top of that, `containedPath()`: every path a run names must be relative and must resolve —
symlinks resolved — strictly inside its own world. It is enforced from `executionProblems()`, so the
transition and the measurement apply it identically. That placement is the P4.7.2 lesson kept: the
reason a mutated binary could be refused at spawn and revealed to anyway was two definitions of a
valid subject.

## 2. Your point 3, and one thing you did not ask for

`holdout_score.mjs` takes **no arguments at all** now. You were right that it was contributing two
facts while claiming one; the honest version has nothing left to contribute but the path it hard-codes.

**And a retired flag that is silently ignored is a silent no-op.** Without this, your reproduction
would have "passed" by being ignored, and a caller that believed it had selected a state root would
have been wrong without being told. So the frozen runner accepts `--holdout` and `--summary` and
refuses everything else **by name**, saying which bypass each retired flag was:

```
HOLDOUT-RUNNER: REFUSED — --status is not an argument of this instrument; it was retired
because a status is WITNESSED by the receipt chain, never asserted by a caller.
The only inputs are [--holdout, --summary].
```

`--repo-root`, `--state-root`, `--adapters`, `--challenges` and `--revealed` each get the same
treatment. `blind_run.mjs` refuses the two retired roots by name.

## 3. The chain hardening — your three, plus a fourth

All three now hold across every reachable receipt rather than only at the top: `spec_release_id`,
`blind_package_id`, `instrument_digest`. You were right that it costs nothing.

You mentioned "ideally the frozen subject identity progression expected at that transition" and I
built it: **the subject set only ever grows, and only where the state table says.** A subject carried
across a transition must be carried with the same package digest *and* the same binary digest, and a
new subject may appear only at `PINNED → CANDIDATE_FROZEN`. Otherwise a history could quietly swap
which implementation its later receipts are about while every link still named a legal predecessor.

No signatures, per your note and mine.

## 4. P and Q

```
PASS  P  a REVEALED world may not authorize a subject outside it
         — freeze REFUSED · reveal refused · subject received [nothing]
         · HOLDOUT-AUTHORITY: FAIL — 2 problem(s)
PASS  Q  a REVEALED world DOES authorize its own subject
         — frozen · revealed · HOLDOUT-HARNESS: PASS
```

P is mounted two ways, because refusing the freeze would otherwise make the case untestable: first
through `--freeze-candidate` (refused), then by writing the escaping adapter straight into the record
and re-identifying it, which is what a hostile operator would actually do (refused, zero H* bytes).

Thank you for insisting on Q. You called the over-correction risk before it happened and it had
*already* happened once — P4.7.2's first sandbox rule made `--complete` refuse any non-canonical
state root and took falsifier H, my own positive control, down with it.

## 5. One of my own, and it is the same species as ever

The battery went **18/18 when I ran it directly and then FAILED case J under `make governance`** —
because between those two runs I added the strict-argument refusal, and J was asserting on the string
`HOLDOUT-REVEAL-GATE: WITHHELD`. The runner now refuses the retired flag *before* it gets as far as
measuring and reporting the withholding, so the case went red while the property it tests got
strictly stronger.

Fifteenth text-anchored gate in this tree, and the third caused by an improvement rather than a
regression. J asserts the measurement now: the subject received nothing, and the invocation did not
succeed.

## 6. What this does not claim

Worth stating plainly, because I overclaimed once already in the P4.7.2 brief when I wrote that a
sandbox "can reach nothing else."

The apparatus stops one world's authority reaching another world's subject **through the ordinary
interface, with the record intact**. It does not and cannot stop an operator with write access from
reading `governance/holdout/` directly, and a sandbox world contains a *copy* of the challenge set by
construction — that is what lets cases A, J, M and P measure withholding of real material at all.
The protected claim is: *the record cannot say a subject was blind when it was not, and no ordinary
invocation discloses to a subject the record has not opened.*

## 7. Also closed

`gov-nest`'s `tail -3` was swallowing `HOLDOUT-COMMITMENT` and `HOLDOUT-AUTHORITY` — the two claim
lines P4.7.2 had just added. A hand-typed `N` in a `tail` is the same species as a hand-typed count;
the filter is derived from the claim prefix now. That retires the last item of the `gov-*` recipe
sweep that has been on the open list since round 27 P4.

## 8. Where I think we are

Your list of what has been successively eliminated is the right frame, and I would add that the last
two entries were both **mine**: the mutable measurement result was closed by a repair that introduced
mutable authority selection. That is worth recording as a property of this kind of work rather than as
an embarrassment — each repair creates a new interface, and a new interface is a new place for the
authority-binding rule to be violated.

**Six attacks, three passes. Zero were proof-wire or DAG semantics.** I agree with your reading: these
are experimental metrology defects at the boundaries between components that are individually correct.

**No P4.8, no questions.** The next step is `blind_package.mjs --emit <empty-dir>`, an isolated
environment, a Go implementation written from the package alone, then
`--freeze-candidate --binary … --reveal --complete`.

Over to you for the last attack. If P and Q survive and you find no further disclosure or completion
bypass, I'll take your sign-off as the freeze and start Go. If you find a seventh, it is P4.7.4 and
I'd rather have it now than after a foreign implementation has seen the challenge set.

---

### Files that moved

| file | what |
| --- | --- |
| `docs/spec/proof-wire/experiment/run_state.mjs` | `resolveState()` takes no override; `containedPath()`; chain-wide commitments; subject-set progression |
| `docs/spec/proof-wire/experiment/holdout_runner.mjs` | v0.4.0 — no `--repo-root`, no `--state-root`; two arguments, everything else refused by name |
| `governance/holdout_score.mjs` | v0.6.0 — no arguments at all |
| `governance/blind_run.mjs` | v0.4.0 — retired roots refused by name; `--complete` checks `world_root` |
| `governance/experiment_falsifiers.mjs` | v0.3.0 — 18 cases, each in its own world; P and Q; J re-anchored on the measurement |
| `governance/grid_check.mjs` | probe `authority-bound-to-world`, measured on derivation, ignored override, and both directions of containment |
| `governance/invariant-grid.json` | v1.63.0 — `law:proof.authority-bound-to-its-world@1` (129 entries / 459 citations) |
| `Makefile` | the holdout gate's output filter is derived from the claim prefix, not `tail -3` |
| `governance/round-11-ledger.md` | items 553–559 |
