# Round 27, pass B3 — the native float plane: measured first, then asserted

**Your sequence, taken exactly: C-side measurement as the first sub-pass of the substantive round, an
independent C↔JS diff inspected before any conformance assertion, and continuation only because the
relation actually agreed.**

One correction on the packaging: this landed as **one commit, not two**. The two sub-passes were
genuinely done and gated in order — B3.1's reducer, `--measure` mode and comparator were built, the
whole gate was run green, and the 27-fixture diff was inspected, all before a line of B3.2's
conformance assertions existed — but the B3.1 and B3.2 edits interleave inside four files
(`film_check.mjs`, `grid_check.mjs`, `negative_battery.sh`, `invariant-grid.json`), and a hunk-split
would have produced a first commit I never actually ran. The ledger carries the two sub-passes
separately (items 275–286 and 287–297) and that is the authoritative record of the order.

Gate: grid **v1.41.0** (88 entries / 379 citations) · `bridge/ic32_film.c` **0.3.0** · negative battery
**295/295** · film **25/25** · lowering **23/23** · derive 45/45 · realm 24/24 · bridge **48/48** ·
harness 9/9 · runner 3/3 · **measure-compare 27/27 (non-gating)**. `cert_id a08ee15d…` byte-identical
— **thirty-sixth** consecutive round.

---

## 1. The measurement came first, and it agreed on 27 fixtures rather than 1

You asked for `church_exp_2_2`. I ran the whole conformance corpus plus the three film fixtures,
because one fixture cannot tell you whether an instrument works — see §2, which is exactly that.

`bridge/measure_compare.mjs` runs the JS reference relation and `ic32_film --measure` and diffs:

| | fields |
|---|---|
| **SEMANTIC** | frame ordering · rule · plane · canonical locus · `pre_sem_id` · `post_sem_id` · terminal class · steps · `final_sem_id` · normal form · `normal_form_id` |
| **DIAGNOSTIC** | the whole **enabled SET** per frame · rule tally · locus-family tally · signature length |
| **NOT COMPARED, said out loud** | ic32's `interactions` — not plane-classified, so it is a different quantity from the kernel's INTERACT-plane readback claim. Both printed. |

**27/27 agree.** `church_exp_2_2` is 21 frames — `APP-LAM 6 · DUP-SUP= 4 · DUP-LAM 3 · DUP-VAR 3 ·
APP-SUP 2 · DUP-APP 2 · DUP-SUP! 1`, `t: 4 · d: 13 · v: 4`, NORMAL_FORM at `λa.(S (S (S (S a))))`.
`church_exp_3_3` is **91 frames with 87 dup-plane loci**.

**Your `enabled_count` ruling, and one step past it.** It stays out of the film. But the comparator
now diffs the whole enabled **SET** rather than its cardinality — two enumerations can agree on every
chosen redex and every state across a whole corpus and still disagree about what else was available,
and that divergence stays invisible until the day the strategy changes. Diagnostic, in a tool that
commits nothing.

**No expected table exists in the emitter or the comparator.** `grid_check` now refuses the fixture
term in either file. The fixture belongs in the check; an expected answer for it inside the emitter is
how a conformance theorem becomes a transcription theorem, and nothing downstream could tell.

## 2. The comparator's first find was a defect in the comparator

It reported `lowered_add_2_3` **DIFFER** on `terminal final` and `signature length` (JS 40 vs C 65 —
the `#`-prefixed §5 compaction marker) while **all six frames matched exactly**.

The C computes its final signature before calling `normal()`. My JS side read `semStateId` /
`semStateSignature` inside an object literal evaluated **after** `readback`, which folds the live heap
and **fires rules into the same runtime**. It was measuring a state the film never reached.

**`church_exp_2_2` hid it**, because there the readback fires nothing at all (`interactFired 0 ·
collapseFired 0 · liveCount 0`) and the two reads coincide. A fixture on which an instrument's bug is
invisible is not a fixture that validates the instrument.

## 3. Agreement is worth nothing until the comparator has been shown to differ

Three perturbed C builds, none committed:

| perturbation | fixtures that DIFFER |
|---|---|
| enumeration order R2L → L2R | 8 |
| locus index order L2R → R2L | 12 |
| child push order in the app walk not reversed | 2 |
| *(added later, for the enabled-SET field)* dup-value redexes reordered | 10 |

The locus-order one reports `frame 3 locus: JS d:0 vs C d:1` on `church_apply_3` — a real dup,
correctly enumerated, **named by the wrong index**. Precisely the failure you told the round to be
strict about, and precisely the one a count-only diagnostic cannot see.

## 4. The thing you warned about is real: they are two different traversals

You wrote *"don't let C implement something equivalent enough and then translate the locus
afterward."* The kernel does not have one live-cell order, it has **two**, and they disagree:

- **`liveHeap`** pushes children FORWARD → pops **right-to-left**. This orders the ENUMERATION, so it
  decides which redex is leftmost.
- **`liveDiscoveryOrder`** pushes children REVERSED → pops **left-to-right**. This indexes the
  `d:`/`v:` loci, so it decides what NUMBER the chosen redex's locus carries.

Collapsing either onto the other still produces a locus that names a real, live, correctly-enumerated
redex — just not the one that fired. `live_cells(root, direction)` implements both and every caller
says which it wants. The law records it and a forgery holds it there.

## 5. ic32 cannot substitute a dup by name — and that cost is representational, not semantic

`FloatRt` keeps dups in a side table with the projections as NAMES, so firing one is two substitutions
and the occurrence never has to be found. ic32 has no such table: `heap[D]` is the cell's **value**
before the rule fires and the **other side's substitution** afterwards. So a dup can only be fired
**from a demanded side**, and the demanded projection must be replaced where it stands.

`find_projections` walks every reachable slot — structural children, substitution slots (an APP-LAM
whose argument was a projection writes it into the binder's slot), and live cell values — and
**refuses (`film-projection-not-unique`) rather than choosing** if a projection is not unique. A
linear net has exactly one; "exactly one" is a property to check, not a fact to rely on.

The rules fired are **ic32's own `fire()` and `app_sup()`, unedited**. The rules are the runtime's;
the scheduling and the addressing are the film's.

**One thing I want your read on** — §9(b).

## 6. The conformance claim — `film.native-emission@2`

`church_exp_2_2` emits **21 chained native frames** covering `APP-LAM · APP-SUP · DUP-LAM · DUP-SUP= ·
DUP-SUP! · DUP-VAR · DUP-APP` across **`t:`, `d:`, `v:`** and **both semantic planes**, and the
kernel's own `replaySemFilm` accepts the whole chain on `FloatRt` and on `DescFloatRt`. Endpoints are
the corpus vector's own initial state and normal form, already agreed byte-for-byte by the 48/48
bridge — so the new claim is exactly the **21 transitions between them**.

The coverage assertion is **derived from the film** (which rules occur, which locus families, which
planes); every forgery index is **found** (`firstFrame(f => …)`, never `frames[6]`).

`@1` is kept as **history, not withdrawn** — it is not wrong about anything it claims, it is narrower,
and it carries the two scope corrections `@2` does not repeat.

**ERA is enumerated and refuses.** Both, by name (`film-era-rule-not-implemented`). Enumeration must
include them or "no enabled work" silently means "no work of the kinds I implement". Firing them
without a witness would be coverage by hope. **`BUDGET_EXHAUSTED` is a typed refusal
(`film-budget-exhausted`), never a terminal**, and the terminal is concluded only after a **fresh
full-pool enumeration** returns empty.

## 7. Seven forgeries on the new surfaces

A mid-chain edit needs every later frame's `prev` and `frame_id` rebuilt, so the round added a
multi-frame `rechain`; the single-frame `recommit` could not express any of these.

| | forgery | refusal |
|---|---|---|
| D-1 | a `d:` index no live cell carries | `sem-locus-not-enabled` |
| D-2 | a `v:` path extended past any application | `sem-locus-not-enabled` |
| D-3 | `DUP-SUP=` relabelled as its sibling `DUP-SUP!` | `sem-rule-mismatch` |
| D-4 | `APP-SUP` relabelled `APP-LAM` | `sem-rule-mismatch` |
| D-5 | a COLLAPSE frame claiming INTERACT | `sem-plane-mismatch` |
| D-6 | the honest film stopped one frame early, terminal HONESTLY recomputed | `sem-false-normal-form` |
| D-7 | a locus naming a **different redex that really is live and enabled** | `sem-post-mismatch` |

**D-5 is only possible now.** Every native frame before this round was INTERACT, so the `plane` field
had nothing else it could say. A hybrid-plane film is the first one in which
`law:plane.rule-partition@1` is forgeable at all.

**D-6 is your terminal point, manufactured against the fixture that carried the disease.**
`l_prog_history.round_4_diagnosis` names `church_exp_2_2` at step 15 as the false-quiescence witness
that falsified `law:sched.free.ast-term@1`. D-6 stops one frame early and recomputes `steps`,
`last_frame` and `final_sem_id` for the state it really stops in, so **every bookkeeping check
passes**; replay refuses it because it re-enumerates the pool at the terminal and finds work.

**D-7 is the only one that distinguishes "the locus names A redex" from "the locus names THE redex."**
It replays the film's first *k* frames with the kernel's own machinery, enumerates the live redexes,
and picks one with the SAME rule at a DIFFERENT locus — frame 4 fired `APP-LAM` at `t:` while `t:arg`
was equally live and equally `APP-LAM`. It gets past enabledness entirely and dies on the post-state.
If a fixture ever has no such alternative the case **reports it could not be built** rather than
skipping.

## 8. Three stale records, and one forgery that had retired itself

- **Two ratchets.** `grid_check` required the literal `film-dup-rule-enabled` in the emitter, and
  `film_check` asserted a DUP-SUP term is refused. Both were true at v0.2.0 and **both would have
  blocked the round that closed the gap** — the species B1.2.1 named. `lowering_check`'s
  "STILL NOT CLAIMED" list is now **PROBED** from the emitter rather than typed.
- **A refinement grade that would have improved for free.** `derivation.lowering-refinement@4` said
  the open item was "a fixture where a DUP-* rule actually becomes enabled". Closed — **by
  `church_exp_2_2` under `film.native-emission@2`, and NOT by the refinement fixture**, which still
  fires no dup rule and still emits the same six APP-LAM frames. Both records now say so. At v0.2.0
  those six frames were the emitter's LIMIT; at v0.3.0 they are a fact about the TERM.
- **A forgery keyed on a version literal.** `film-emitter-version-drifts` forged
  `emitter_version":"0.2.0`; the bump made it a no-op and the non-vacuity detector said so on the
  first run. Regex now. **Third time** a version literal inside a forgery has retired itself silently.
- **A property re-homed rather than dropped.** The grid assertion for the removed
  readback-interaction-count record now reads `@1`, where that v0.1.0 fact lives, and independently
  the C source still carries it and is still checked. Deleting an assertion because a revision bump
  moved its subject is how a property is lost in a rename.

## 9. Three things for you

**(a) The catalog family id is `impl-c-ic32-film-v0.1.0` and the binary is v0.3.0.** Nothing is wrong
today — artifact identity is the DIGEST, which does move, and the family is a catalog key. But a
version inside a name that nothing checks is the shape that drifts, and this round already caught one
forgery that retired itself on a version literal. Options: drop the version from the family name; bump
it and accept that every emitter bump is a catalog change; or leave it and record why. **Flagged, not
changed** — it touches a frozen probe's era wording and the observation keys, so it is a ruling.

**(b) The one-interaction check is post-hoc.** `fire(D,L,k)` opens with `whnf(heap[D])`, which could in
principle do work. I argue it cannot here: `dup_rule_name` has already established by **chasing** that
the value is a Lam/Sup/Era/free-Var/stuck-App, and `whnf` returns each of those without an
interaction. The emitter then checks `interactions - before == 1` — but that check runs **after** the
mutation, so a violated precondition is caught rather than prevented. Is a post-hoc counter check the
right instrument here, or should the emitter assert the precondition structurally before calling in?

**(c) The `v:` locus and shared subterms.** Each `findAppRedexes` call carries its own visited set, so
a node reachable both from the root and from inside a dup value is enumerated **twice**, under a `t:`
locus and a `v:` locus. C reproduces that faithfully and the corpus agrees. I have not found a fixture
where the two loci name the same redex and a film could legitimately cite either — is that worth a
purpose-built witness, or is it a non-question because both loci fire the same rule to the same
post-state?

## 10. Next, in your order

1. **The ERA witnesses** — two fixtures, not one contrived term containing both: coverage by
   construction. Both `APP-ERA` and `DUP-ERA`, since the measurement showed neither fires here.
2. **BUDGET_EXHAUSTED** native film evidence, currently a typed refusal.
3. **`EMISSION_CONFORMANCE-v1`** over `{closed_template → target_term_sem_id}`.

C-side replay — films flowing the other direction — remains unclaimed and unchanged.

## Files

- `TRVM_B3_REVIEW_PACK.tar.gz` — runs from any extraction dir; `./verify.sh` replays every gate **and**
  the non-gating measurement, and writes `RESULTS.txt` from the run.
- `governance/round-11-ledger.md` §§ B3.1 (items 275–286) and B3.2 (items 287–297).
- `governance/bridge/ic32_film.c` v0.3.0 · `governance/bridge/measure_compare.mjs` ·
  `governance/bridge/film_check.mjs`.
- Reproduce the measurement: `make gov-measure` (not in `make governance`).
