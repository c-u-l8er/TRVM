# Slice B, commit 5d — freeze integrity

**Status: every gate of the commit-5d ruling is green.**

| gate | result |
|---|---|
| `binding_run53` — F1–F12, **49 rows** | **ALL PASS** (22s) |
| `mutate53` — the API mutation gate | **ALL CAUGHT, 8/8** |
| `run_l0_sweep` (frozen L-0 + live) | **21/21 green** (362s) |
| `mutate51` | **ALL CAUGHT, 16/16** |
| `binding_run3o` (persistent fold, native) | `PASS_REF_AND_NATIVE` (37s) |
| `binding_run43` (Slice A, native) | `PASS_REF_AND_NATIVE` (1s) |
| `binding_run35` (release closure, oracle path) | `PASS_REF_AND_NATIVE` (68s) |

The document is cut to **WRL Core 0.2.1**. The API seam of §8c is built.
**No sealed trajectory, no artifact id, no backend term and no valid Film
moved** — F11 asserts it and the four native batteries above re-prove it.

---

## 1. The thing to read first

The defect 5d fixed was **a permission, not a behaviour**.

`admit_step` took a `policy_id` that no caller in the tree ever passed
wrongly. Every trajectory was correct, every film was right, every battery was
green, and §8 consequence 1 — *"never from a caller-supplied option"* — was
false of the signature while being true of every call site.

That is why it survived 0.2.0's review, and it generalizes the lesson 5a–5c
were about:

> Agreement among **implementations** cannot see a shared misreading of the
> spec. Agreement among **call sites** cannot see an API that permits one.

It also dictates the shape of the battery. F7's rows assert about
**signatures** — `inspect.signature(AD.admit_step).parameters` — which looks
like testing the spelling of the code rather than what the code does, and is
the only kind of row that works here, because the property being frozen is
*what a caller is able to ask for*, and a caller who never asks leaves no
trace.

The measurement that follows: under `mutate53`, **N1 and N4 are each caught by
exactly one row.** That is not a coverage gap, it is the finding. Delete F7a
and N1 survives silently, forever, with every behavioural row in the entire
tree still green.

---

## 2. Documentary closure (Core 0.2.1)

All six ruled items, plus two the cut turned up on its own.

| # | ruled item | landed |
|---|---|---|
| 1 | restore the complete §16.1 verified-route gate | §16.1, four obligations |
| 2 | restore the §16.2 permission/instance split | §16.2, three layers + the no-principal prohibition |
| 3 | restore §17 sugar closure obligations | §17 + §17.1, five rows |
| 4 | correct six commits to eight | §16.3 table |
| 5 | scope the byte-movement statement to sealed trajectories | two-row *Where declared bytes moved* table |
| 6 | replace the ACCEPT/MAP paragraph with the ruled wording | §8 |
| + | §8c, the new frozen section | §8c |
| + | §16.4, verified-route staging (ruled) | §16.4 |

### Two corrections not in the ruling

**(a) §16's subsections were in the order 16.3, 16.1, 16.2, 16.4.** Row 3 of
§16's own table points a reader at §16.1; they were meeting §16.3. Reordered.

**(b) Eight, and why 5d is not a ninth row.** Adding a `5d` row to §16.3 would
have made the count **nine** while the ruling and F5 both say **eight**. That
needed resolving honestly rather than arithmetically. The resolution: the
eight rows are the commits that **grounded a construct**. 5d grounds nothing —
it changed no sealed trajectory, no artifact, no backend term and no valid
Film; it corrected the *record* of those eight and made one of their frozen
statements enforceable in code. Mixing the two into one list would make *"how
many commits did `~~` take?"* unanswerable, which is the question the section
exists to answer. So 5d is recorded in prose, with the distinction stated as
the reason, and the grounding count stays eight.

---

## 3. API closure

Five ruled items, four files.

| # | ruled item | where |
|---|---|---|
| 1 | production folds accept only sealed runtime seams | `wrl_fold.admit_step_sealed` gates on `RuntimeSeamsV1` |
| 2 | raw policy selection unavailable from the world path | `admit.admit_step(state, batch, epoch, fx)` — the parameter is **gone** |
| 3 | replay refuses policy/artifact mismatch | `wrl_fold.verify_replay_policy` → `WRL_REPLAY_POLICY_MISMATCH` |
| 4 | the explicit probe remains available to T7i | `admit.admit_policy_probe(..., policy_id)`, refuses `None` |
| 5 | no sealed trajectory/artifact/backend term/Film change | F11 + four native batteries |

`_admit_step_with_policy` is the shared private reduction. **Provenance, not
value, distinguishes the two seams**: production takes a `RuntimeSeamsV1` that
only a sealed artifact can build; conformance takes a bare string through a
function whose *name* says so. F11b asserts the two compute the **identical**
reduction for the same policy — provenance must not be observable in the
result, or the split would have been a behaviour change wearing an API change's
clothes.

`WRL_REPLAY_POLICY_MISMATCH` carries `field_path="policy_ids.admit_policy_id"`
**structurally**, not spliced into the message. F8d asserts on `e.field_path`.
The first cut asserted on `str(e)` and would have **survived** N5.

### THREE cases, not two

The one real regression this commit shipped and had to fix mid-flight.
`binding_run49.gfilms`'s dispatch first read *"declared or probe"* and routed
every `policy=None` caller into `admit_policy_probe`, which refuses `None` by
contract. It broke **T4, R7 and R11**.

`None` does not mean *no policy*. It **names the frozen default**, and
`admit_step` is the entry that means exactly that:

```python
if sealed:                    # RuntimeSeamsV1 from the artifact
    ... FD.admit_step_sealed(...)
elif policy is None:          # the FROZEN policy, named by omission
    ... AD.admit_step(...)
else:                         # a policy chosen BY HAND
    ... AD.admit_policy_probe(..., policy)
```

The same defect was live in `spinner_bench._run_traj_fixture` and was caught
before it ran: `admit_policy_of` returns `None` for a mailbox-free world, and
the demo world **is** mailbox-free, so an unconditional probe call would have
broken the pinned demo. Same three-case fix, plus hoisting the policy lookup
out of the epoch loop (it is a property of the world, not of the epoch).

N6 preserves the regression as a mutant so it cannot come back unnoticed.

---

## 4. The battery: `binding_run53`, F1–F12

**49 rows.** Documentary rows read a **parsed** document, never a substring
scan: `_sections()` walks the file once into `(level, title, body)`, a body
ends at the next heading of **any** level, and `_sec("17")` raises on absence
*and on ambiguity*. That guard earned itself on its first run — `17` matched
both `17.` and `17.1`.

*A law about a seam must PARSE, not grep*, extended from Python to Markdown.

| section | asserts |
|---|---|
| F1 | the document is self-contained (no normative pointer at the superseded file) |
| F2 | §16.1's four-obligation gate is present, and the empirical argument was **added beside** it, not swapped for it |
| F3 | §16.2's three layers **with what each carries**, and the no-principal prohibition |
| F4 | §17/§17.1's five closure obligations, one row each, plus the identity law |
| F5 | eight, counted from the **table**, not trusted from the prose beside it |
| F6 | the byte-movement claim is **scoped**, document-wide |
| F7 | **signatures**: `admit_step` has no policy parameter; `fold_world` has none; the sealed seam refuses a bare id |
| F8 | replay refuses a mismatch, and refuses a **missing** one, with the structured `field_path` |
| F9 | the probe survives, reaches T7i's unsealable configuration, refuses `None`, and the three-case dispatch folds |
| F10 | delegates to `binding_run51.t7_boundary` rather than forking T7's setup |
| F11 | the pinned demo world still seals `sem-8ae91fe9…fe4a`; both seams compute the identical reduction |
| FN | **negative controls** for the documentary rows |
| F12 | scope, checked |

### Why the documentary rows have in-memory negative controls

`mutate_harness` copies `forge/` and **symlinks its siblings**, so a mutation
naming `../WRL_CORE_0.2.md` would write straight through the symlink into the
real document — in a tree several sessions are editing at once. So F1–F6's
negative controls live in `fn_negative_controls`, which corrupts a **parsed
copy in memory** and touches no file. FN1–FN4 prove F1a, F5d, F6b and F2a are
live checks rather than patterns that match nothing.

*An assertion never observed to fail is not yet evidence* — §17.1's own rule,
applied to the battery asserting §17.1.

---

## 5. `mutate53` — and why most of these mutants change no output

| mutant | reverts | caught by |
|---|---|---|
| N0 | null control | battery green |
| N0b | `@noop` — a trailing comment | survived, as a no-op must |
| N1 | `admit_step` regains `policy_id=None` | **F7a** |
| N2 | the sealed seam accepts a bare id | **F7c** |
| N3 | replay reconciles instead of refusing | F8b, F8c, F8d |
| N4 | the probe accepts `None` | **F9c** |
| N5 | the refusal drops its `field_path` | **F8d** |
| N6 | the dispatch collapses to two cases | **F9d** |

N1 restores the defect *exactly as it stood through 0.2.0* — a default of
`None`, so every existing caller behaves identically and every trajectory is
byte-for-byte what it was. Nothing miscomputes. The world is simply once again
executable under semantics it did not seal, by any caller who passes a fifth
argument. **Every behavioural row in the entire tree stays green under it.**

N3 is listed with two catchers deliberately: F8b and F8c fail for *different*
inputs — a wrong policy and a missing one — so a fix that special-cased only
the first would flip one and not the other.

---

## 6. Defects found in flight (all self-caught, all fixed)

1. **The three-case dispatch** (§3 above) — cost two reruns of `binding_run51`.
2. **`spinner_bench` would have broken the demo** — caught by reading, before
   it ran.
3. **`_sec("17")` matched `17.1`** — the ambiguity guard earned itself.
4. **F1a flagged four false offenders.** Debugged rather than guessed; all four
   were the document *quoting* the defect. The discriminator is not *which*
   section speaks but *whether it is quoting*, which let the by-name exemptions
   be deleted entirely. Hoisted into one `_unquoted()` helper when F6a needed
   the same rule — spelling it twice would have been a fork.
5. **F2c ended in `or True`** and asserted nothing. Rewritten to assert on
   §16.1's heading.
6. **F12 was `rep(True, ...)`** — the same defect in its politest form: it
   reported coverage and checked nothing. Now F12a checks the named sibling
   gates **exist**.
7. **N6 scored SURVIVED — *"crashed, rows never ran"*.** Crash is not a catch.
   `section()` let the exception escape, so the battery stopped and every later
   row went unreported. Two fixes, not redundant: `section()` now contains
   escapes into a named red row (`binding_run51`'s discipline, ported), and
   F9d is written as a **callable** so the raise lands on *its own row* — a
   section-level catch says the battery broke, a row says **which law**.
8. **Five rows all named `F4c`.** `mutate_harness.rows_failed` keys a catcher
   by id, so five distinct laws were one indistinguishable row and a mutant
   breaking one would be credited to all five. Invisible while they pass. Now
   F4c–F4g, and **F12b is the self-check** that no two rows share an id —
   verified by duplicating one and watching it go red. *Set membership is not
   identity*, third time this class has appeared.

---

## 7. Autonomous decisions, flagged

1. **Eight grounding commits + 5d in prose** (§2b). The alternative was a
   nine-row table contradicting F5 and the ruling.
2. **§16 subsections reordered** into numeric order. Not in the ruling; §16's
   own table was pointing at the wrong section.
3. **`admit_policy_of` is total over both sealed carriers** (artifact mapping
   and plan view) so the bench does not spell the lookup a second way.
4. **F10 delegates to `binding_run51.t7_boundary`** and runs its prerequisite
   `t0_profile_and_codec` rather than rebuilding the rigs. 5d is a commit about
   forks; a second copy of T7's setup would be one. T0's own rows are excluded
   from F10's verdict by snapshotting `_FAILED` after it.
5. **`binding_run53` is registered in `SWEEP_LIVE`**, not `SWEEP_L0`. L-0 is
   closed.
6. **Documentary rows are not mutated**, for the symlink reason in §4.

---

## 8. What this does NOT close

- `binding_run53` proves the **document** and the **API seam**. It proves no
  reduction, no backend term and no native fold. Those are `binding_run51`,
  `binding_run49`, `binding_run43`, `binding_run3o` and `mutate51`, run
  separately and reported in the header — and 5d's claim is precisely that it
  did not move them.
- `Core §5 L121` and `§14 L283` still describe `~~` as partial. That is now a
  **promotion decision**, not a defect; rewriting them *is* the promotion.
- The `==` verified route is **staged, not begun**. §16.4 records the ruling:
  authorization is an **orthogonal** `authorization_policy_id` axis, not a
  third acceptance policy. No parser, no runtime.

---

## 9. Ask

Confirm, or steer:

1. **Core 0.2.1 → FROZEN**, and **Slice B → CLOSED**.
2. The eight-plus-prose resolution of the commit count (§2b).
3. Whether F7's signature rows are the right shape for a freeze whose subject
   is a permission — they are the only rows that can see N1 and N4, and they
   are also the only rows in the tree that would go red on a *harmless*
   refactor of those signatures. That trade is deliberate; it is worth a
   ruling.
4. Next milestone. The expected answer is the `==` verified-route ruling
   packet, which is not started.
