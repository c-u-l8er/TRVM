# Round 27, pass B5 — the partial execution becomes evidence

**Your B4 review taken in full: the stale `lowering_spike` record and its ratchet repaired first,
then `BUDGET_EXHAUSTED` as a native terminal.** `EMISSION_CONFORMANCE-v1` is untouched and is next,
with nothing between.

Gate: grid **v1.43.0** (90 entries / 380 citations) · `bridge/ic32_film.c` **0.5.0** · negative battery
**304/304** · film **43/43** · lowering 23/23 · bridge 48/48 · derive 45/45 · realm 24/24 · harness
9/9 · runner 3/3 · **measure-compare 35/35 (non-gating)**. `cert_id a08ee15d…` byte-identical —
**thirty-eighth** consecutive round.

---

## (a) The record defect — you were right, and it was worse than one word

Your finding reproduced exactly. `INPUTS_MODEL.implemented = true` since B2; the grid said `false`;
`falsifier_status` reported I-4a/b/c unwritten; `grid_check` **required** the false value. Four
passes. Three things to add.

**The negative battery was enforcing it too.** `spike-record-claims-implemented` forged
`implemented = True` and expected *"must stay false"*. After B2 that case was **testing a lie** —
which is how 298/298 stayed green over a record contradicting the code for four passes. The
assertion and its falsifier were pinned to the same phase value, so the falsifier could not report
the assertion had gone wrong. Both directions are forged now and neither expectation names a
polarity.

**Both chain strings were stale, each frozen at a different round.** `identities.chain` ran lowering
straight to `target_term_sem_id` — the B1 shape, from before a template layer existed.
`inputs_model.chain` was the B1.2 shape, missing `closed_template_sem_id` and `emission_sem_id`.
You spotted the second; the first had been wrong two passes longer.

**The repair is derivation, in both directions, and not a corrected constant.** Per your ruling,
nothing is pinned to `true` either:

```
grid lowering_spike.inputs_model.implemented  ==  INPUTS_MODEL.implemented
grid falsifier_status reports WITNESSED       <=> INSTANTIATION_FALSIFIERS all WITNESSED
grid scope names the BUILT ops                ==  IMPLEMENTED_LOWERED_OPS
grid chain prose, *_sem_id tokens IN ORDER    ==  REFINEMENT_CHAIN ids
```

That last one is the general instrument the section needed: prose stays readable, a node added in
code forces the prose, a node dropped from the prose fails the gate. It would have caught this
defect at B1.2, four passes before you did.

Six new negative cases, each verified to die on **its own** assertion rather than a neighbour's.

---

## (b) `BUDGET_EXHAUSTED` — the terminal, exactly the contract you specified

`ic32_film` **v0.5.0**, `film.native-emission@4` supersedes @3. No new budget concept: C now
originates the terminal object `TRVM-SEMFILM-v1.1` already knew how to judge, and replay re-derives
every field on `FloatRt` and `DescFloatRt`.

The C-side change is the one you described. Enumerate, then decide:

```
enumerate full declared pool
   n == 0        →  NORMAL_FORM          (wins, even at steps == budget)
   nf >= budget  →  seal BUDGET_EXHAUSTED, break, fire nothing further
   nf >= MAXFRAMES → film-too-many-frames (storage, refusal only)
```

**Measured, on `church_exp_2_2`:**

| `--budget` | terminal | steps | `remaining_work` |
|---|---|---|---|
| 0 | BUDGET_EXHAUSTED | 0 | 1 |
| 1 | BUDGET_EXHAUSTED | 1 | 2 |
| 3 | BUDGET_EXHAUSTED | 3 | 4 |
| 10 | BUDGET_EXHAUSTED | 10 | 2 |
| 20 | BUDGET_EXHAUSTED | 20 | 1 |
| 21 | NORMAL_FORM | 21 | — |

Every one replays on both runtime classes. Every one's frames are **byte-identical to the unbudgeted
film's prefix, `frame_id` included** — so the budget truncated the execution rather than altering it,
which is asserted rather than assumed. `--budget 21` is byte-identical to the unbudgeted film
entirely.

Your boundary rule holds and is stated as an **ordering, not a comparison**: the pool is enumerated
before the budget is tested, so a computation finishing exactly on its last permitted step *finished*.

**`remaining_work` is not monotone in the budget** (1, 2, 4, 2, 1) and is not expected to be — an
interaction net's enabled pool grows and shrinks as dups distribute. So it is re-derived per film
rather than predicted from one, which is also why the forgeries below cannot be caught by arithmetic
on a neighbouring film.

### The thing that is new in kind, not just in coverage

**`remaining_work` is the first *count* that has ever had to cross implementations.** Every native
film to date asked the JS oracle to agree about **states** — canonical signatures, chains, normal
forms. This is the **cardinality** of C's fresh full-pool enumeration, committed inside `film_id` and
re-derived by `findFloatRedexes`. Two enumerators that agree about every state they visit can still
disagree about how many redexes a state contains, and nothing before this round would have noticed.

### The zero-frame witness, generated rather than forged

`--budget 0` produces the round-6B audit's exact attack shape **honestly**: 0 frames, `last_frame
genesis`, `remaining_work 1`, final state equal to the full film's frame-0 pre-state, no
`normal_form` field. The repaired schema judges it on both runtimes. As you said — a satisfying
closure witness, and the reason it is worth having is that the v1 terminal accepted this shape while
mutating `budget` or `remaining_work` did not even move `film_id`.

A zero-frame film is **two different facts** and they do not share a name: nothing *enabled* is still
`film-no-redex-at-source`.

### A partial film carries no normal form

Absent, not present-and-unused. Reading one back performs exactly the work the budget denied and
reports it beside a terminal saying it was not done — two contradictory answers to *what did this
execution produce?*

### The forgeries

All six you listed, plus one, each re-sealed so it dies on re-derivation rather than a hash it forgot
to fix:

| | attack | refusal |
|---|---|---|
| B-6 | `remaining_work` inflated | `sem-terminal-work-mismatch` |
| B-7 | budget ≠ steps | `sem-budget-mismatch` |
| B-8 | partial claiming `NORMAL_FORM` | `sem-false-normal-form` |
| B-9 | terminal names another state | `sem-terminal-state-mismatch` |
| B-10 | complete film relabelled `BUDGET_EXHAUSTED` | `sem-terminal-work-mismatch` |
| B-11 | pool narrowing | `sem-terminal-work-mismatch` |

**B-10 dies on the work count and not on the label, which is the right refusal**: the state is
quiescent, so no honest `remaining_work` exists for it at all.

**B-11 is the one worth your attention.** The obvious narrowing — drop the DUP rules — *is* caught,
but by `sem-plane-not-permitted` at frame 2, because the honest chain fires a DUP rule. The work
arithmetic never runs. **That is the coincidental-second-occurrence species for the fifth time in
this line**, and it reads as a green case either way. So the case now **searches** for a rule that
(a) no frame fires and (b) changes the enabled count — `DUP-SUP!`, 4 → 3 — leaving the arithmetic as
the only thing that can catch it. If no such rule existed on the fixture, the case reports itself
vacuous rather than passing.

---

## (c) Two ratchets your finding predicted, found by looking for the class

You classified the `lowering_spike` defect as *"an assertion that was correct while a feature was
open becomes a mechanism preventing the record from acknowledging that the feature closed."* Looking
for that shape rather than that instance found three more in one round.

**`scope-is-stated-by-refusal` required `film-budget-exhausted`** — its third move (dup PRESENCE at
v0.1.0, dup ENABLEDNESS at v0.2.0, the budget now). Rewritten as the durable property: *the emitter
states its limits by refusing BY NAME.*

**The canonical-law assertions named `film.native-emission@3` by number** and had been hand-edited on
every supersession. They now find the revision **by canonicity**, so a new revision must carry the
durable sentences forward rather than inherit them by being newer.

**Three battery cases were pinned to `revision == 3`.** When @4 became canonical they went on
mutating a superseded revision nothing asserts over — and **correctly reported their own forgeries as
uncaught**, which is the only reason they were found. The retarget is the same one-line change.

---

## (d) One guard traded, and I want you to check the trade

P-3F asserted `FilmAuthority.prototype.emit.length === 2`: with no third argument slot, there was
nothing to smuggle a `run()` through. **B5 needs `--budget` flags, so the slot had to open.**

I did **not** restate the arity guard. The third parameter is typed — argv **strings** only, refusing
`emitter-flags-not-argv-strings` — and P-3F now forges **through** the parameter instead of asserting
it away, including a `run()` hidden inside a flags array. The claim is that this is at least as
strong: arity could only prove the door was absent; this proves it is shut, and a function is not a
string.

**If you disagree, the alternative is a separate `emitFlagged` method** leaving `emit` at arity 2 —
which I think is two mechanisms where one will do, and this tree has paid for that twice, but the
call is yours.

---

## (e) Measured, negative, and reported anyway

**`film-too-many-frames` has no positive witness.** The plan for that case was a term exceeding
`MAXFRAMES` (4096). No such term exists among those this emitter can film: **`MAXPATH` (480) binds
first**, because a computation long enough to fill the frame array has a spine too deep to address.
The frames ceiling is therefore **unreachable in practice** at the current `MAXPATH`, and B-5 says so
rather than looking witnessed by the case it appears in.

What B-5 *does* witness is closer to your actual point: **one term, two limits.** church 4^4 refuses
`film-locus-path-too-deep` unbudgeted and yields an honest 5-frame partial film under `--budget 5` —
a storage refusal and an execution terminal out of the same run. A term the emitter cannot film to
completion still has a filmable prefix, and conflating the two would have thrown that away.

`--budget -1` refuses `film-budget-negative` rather than sealing a film claiming `budget = -1`
against `steps = 0`: being caught downstream is not the same as being honest upstream.

---

## Questions for you

1. **The arity-for-type trade in (d)** — sound, or do you want `emit` held at two parameters?
2. **`MAXPATH` at 480.** It is now the binding constraint on how large a fixture can be filmed at
   all, and it was chosen when films were six frames long. Raising it is cheap; the question is
   whether the frames ceiling should stay unreachable, or whether an emitter should be able to
   demonstrate every refusal it declares. I lean towards the latter but it is not free evidence — it
   is a bigger fixture that proves a limit rather than a semantics.
3. **C-side replay.** Films still flow C→JS only. You have twice said symmetry is optional. With
   `remaining_work` now crossing as a count rather than a state, does that change?

## Still open, in your order

1. **`EMISSION_CONFORMANCE-v1`** over `{closed_template → target_term_sem_id}` — next, nothing before it.
2. **C-side replay** (films flow C→JS only).
3. Canonical-locus alias **precedence**, if a well-formed fixture ever produces one.
4. `film-projection-not-unique` has no direct negative fixture.
5. `film-too-many-frames` unreachable at the current `MAXPATH`.

## The pack

`b5-review.zip` carries the governance tree in repository shape plus `verify.sh`, which checks the
manifest and then **runs** everything — grid baseline, negative battery, harness self-test, runner
contract, film/lowering/derive/realm batteries and every probe. **The headline numbers in
`RESULTS.txt` are generated by that replay; nothing in the pack transcribes a count.**

```
unzip b5-review.zip && cd b5-review && ./verify.sh
```

Read in this order: `governance/round-11-ledger.md` §309–322 (this round, newest section wins) ·
`governance/bridge/ic32_film.c` header and the terminal block · `governance/bridge/film_check.mjs`
B-1…B-11 · `governance/grid_check.mjs` around the `lowering_spike` derived checks.
