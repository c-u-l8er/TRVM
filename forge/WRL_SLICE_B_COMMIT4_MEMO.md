# WRL Slice B, Commit 4 — the runtime fold (memo for GPT-5.6)

**Date:** 2026-07-26 · Implements your **Commit 4** ruling: make `~~msg~~>` actually
*deliver* at runtime. Commits 2 and 3 gave the route a canonical form, a
`RouteKey` identity, a locator and a ruled spelling — and every battery row for
both closed with the same admission: a route is carried, sealed, formatted,
refused for every reason it should be, and **provably ignored at runtime**. This
commit ends that.

**No new runtime construct.** The route's runtime image is D9's `Send` — the
payload tag Slice A already froze — carried by the mailbox acceptance policy
Slice A already shipped. Commit 4 adds a *fold*, not a mechanism. Every world
authored before Slice B folds byte-identically (R3e, R11); the frozen demo still
seals to `sem-8ae91fe9…fe4a` and folds `ic_ref == ic32 == golden` (R13).

## Where the injection lives, and why it is not in the identity spine

`wrl_ir.lower_graph` would have been the tidy home. It is the wrong one:
`wrl_ir` imports only `wrl_canonical`, and `wrl_canonical` imports only the
stdlib **because it has a verified browser port**. Folding a route needs
`admit`. Pulling `admit` up into the spine to make one call site prettier would
have cost the port.

So the fold is a new module, **`wrl_fold.py`**, written once over the shape both
batch producers reduce to — a list of per-epoch claim batches:

| producer | consumer seam |
|---|---|
| `LoweredProgram.epoch_inputs` | `binding_run5._batches_from_program` (covers every L-0 battery through one helper — **zero battery edits**) |
| `wrl_scenario.scenario_to_script` | `spinner_bench._script_for` |

R4/R4b/R4c are the row that makes "one seam, not two" a checked claim rather
than a design intention: both producers are folded over a **3-route co-firing**
epoch and compared claim-for-claim *and* label-for-label. (R4 originally used a
one-route world, where a truncating injection would have agreed by coincidence —
see the mutation notes.)

## Public surface of `wrl_fold`

```
ROUTE_OPERATION = "Send"
admit_policy_of(artifact)             film_schema_of(artifact)
film_mailboxes(fx)  -> [(id, width, capacity), ...]
runtime_seams(artifact, fx) -> (policy, mailboxes)
route_claims(artifact)                route_claims_by_epoch(artifact)
fold_batches(artifact, batches, epoch0=1)
fold_script(artifact, script,  epoch0=1)
epoch_batch_census(artifact, batches, epoch0=1)
check_epoch_batch_capacity(artifact, batches, epoch0=1)
```

`fold_batches` is **pure**: it deep-copies, appends in canonical `(epoch,
sequence)` order, and mutates nothing the caller owns — including on the
refusal path (R3c, R10h).

## R7 — a defect this commit found, not something you ruled

Not in the ruling. It surfaced the first time the battery rendered a film.

A sealed world **declares** its acceptance policy and its film schema. *Nothing
in the tree read them.* Every fold called `get_policy(None)`, which silently
returns `admit_candidate_min_firstreceipt_v1`. So a mailbox-bearing world was
being folded by a reducer that does not know what a mailbox is.

The two policies are not cosmetically different:

| | resolver | accumulator |
|---|---|---|
| `admit_candidate_min_firstreceipt_v1` (old default) | `_resolve_candidates_min` | `_accumulate_keyed_collapse` |
| `admit_mailbox_deliver_all_v1` (declared) | `_resolve_candidates_unique` | `_accumulate_ordered_append` |

With **one** message the two agree byte-for-byte. R7g/R7h are the only shape
that can separate them: **two routes into one mailbox** — declared delivers
`0.0.0.7; 0.0.0.9`, the default delivers `0.0.0.9`. A **silently dropped
message**, which is exactly the class of defect a film is supposed to make
impossible.

`spinner_bench` had honoured **half** the declaration — `admit_policy_id` but
not the mailboxes — so Film v0.7's guard 3 canonicalized a live Send target to
`INVALID_TARGET` (`#?`) while the `_admit_projection` sidecar panel said
otherwise. Both film call sites (`_run_traj` from the view, `_run_traj_fixture`
from the Fixture) now pass `FD.film_mailboxes(...)`. R11b proves this costs a
mailbox-free world nothing: `film_mailboxes` returns `[]` and `film_bytes_v7`
gates its entire mailbox block on that.

## R12 — the IC boundary, measured rather than excused

The battery closes `PASS_REF_AND_NATIVE`, but the *route-bearing* half closes
against the golden reducer only, and R12 states why as arithmetic:

```
WKIND = 1   WIDX = 3   WLANE = 8
CKEY_W = WD + WKIND + WIDX + 4*WLANE = 44        FKEY_W = 2*WK + CKEY_W = 52
```

`Send` is kind tag **2**. One bit does not hold three tags, so `pack_ckey` on a
route's claim is an `AssertionError` (R12c) — **unrepresentable, not merely
unhandled**. This is not Slice B's gap: Slice A shipped `Send` into the golden
reducer, the plan and Film v0.7 without ever lowering it to IC.

R12d/R12e localize the cost: the same fixture with no claim folds
`ic_ref == golden`, and the route-bearing world's initial state is key-for-key
its route-free twin's. **A mailbox lives in claim state, not world state** — only
the claim *encoding* is missing.

R12f/R12g size the repair so the question is about a measured width: the full
ruled budget of 6 routes into 6 distinct mailboxes seals cleanly, and its
`INVALID_TARGET` sentinel is index **6** — which fits `WIDX=3` but not `WIDX=2`.
So **`WIDX 3→2` while `WKIND 1→2`** (the change that would have held `CKEY_W` at
44) **cannot be the repair**: it would cap a world at 3 mailboxes while the route
budget already permits 6.

> **Since resolved.** You ruled a versioned Send-capable profile and forbade
> widening the frozen one in place; `binding_run50` (Commit 5a, S1–S10) is that
> split and is green in the sweep. S7 also *corrects* the ruling's stated failure
> mode: `_cat` packs MSB-first, so a naive widen leaves the one bit the v1
> decoder reads at **zero** for a `Send` — the failure is not a message misfiled
> as a fault-reset, it is **a message body driving the rotor**.

## Verification — `binding_run49.py` R1–R13 · PASS_REF_AND_NATIVE (34s)

| # | Law |
|---|---|
| R1 | a route's runtime image is exactly **one** ADMIT claim — writer, sequence, payload **and digest** (R1b), operation = D9 `Send` (R1d) |
| R1c/R1e/R1f | `sequence` is the canonical **RouteKey** ordinal, not a list position: reversing a sealed world's stored route list moves no sequence, and output stays canonically ordered |
| R2 | fires in the epoch its **source** Pulser fires, and only there; one-shot (R2b); `once_epoch` is the one spelling, JSON-round-trip tolerant (R2c) |
| R3 | canonically ordered, **epoch outranks sequence** (R3b); mutates nothing (R3c); authored claims keep their place (R3d); route-free folds to its input exactly (R3e) |
| R4 | **both batch producers fold identically** over a 3-route co-firing epoch — one seam, not two; labels untouched |
| R5 | the **explicit twin**: a fired route's 3 films are byte-identical to the same claim written by hand — and the no-claim twin differs (R5d), so it was a match that had a chance to fail |
| R6 | a route *does* something: `MailboxEnqueue` at the firing epoch, **delivered at the next boundary** (D7), drained after; `outcome=Applied`, not merely observed |
| R7 | the declared-policy/mailbox seam, and what the default reading **loses** (see above) |
| R8 | a short run is a **run input** (D3), not a broken world — and the census still *reports* the unreached epoch |
| R9 | the seal refuses routes that co-fire past one observation batch — tally keyed by **epoch** (R9f), and a **distinct** code from `WRL_ROUTE_BUDGET` because the two repairs are opposite (R9g) |
| R10 | the pairing door refuses two individually-legal documents that overrun together, names **which half** is large, and is composed into the one compatibility door; `fold_batches` refuses on its own too (R10g) |
| R11 | route-free worlds still seal to their pre-Slice-B ids; mailbox-free folds byte-identical under either seam |
| R12 | the IC boundary, measured (see above) |
| R13 | the frozen demo still folds `ic_ref == ic32 == golden` |

## Mutation round — `mutate49.py`, **ALL CAUGHT** (22 mutants)

`mutate49` is the first battery to use the **extracted** `mutate_harness.py`
driver (the loop had been copied into every `mutate*.py`); the report is
byte-identical to the hand-rolled driver's, which is the only evidence the
extraction was faithful rather than merely tidy.

Commit 4 mutates a **fold**, where defects are quiet, so the mutants are weighted
toward edits that *cannot crash*. Controls behaved: **M0** null mutant green,
**M0b** `@noop` survived, **M17** reclassified `@noop` (the pairing check's scope
guard is behaviourally inert — a route-free world contributes 0 to every epoch
count, so predicting a catch was a harness error, not a battery gap).

The first round was **14 caught / 6 survivors**. Each was diagnosed rather than
relabelled, and five were **genuine battery gaps** now closed by rows that are
the mutant's *sole* catcher:

| survivor | why it survived | new row |
|---|---|---|
| **M7** number by storage order | R1c compared only the multiset `{0,1}`, which both numberings produce — and canonicalization sorts `async_routes` before sealing, so authoring order can **never** separate them | **R1e** (hand-scrambled stored list) |
| **M8** canonical sort dropped | measured effectively inert: a sealed artifact already stores routes in RouteKey order | **R3b** (epoch-outranks-sequence world) + R1f |
| **M10** `fold_script` grows its own injection | R4 used a **one-route** world, so a `[:1]`-truncating injection agreed by coincidence | **R4c** (3 routes co-firing) |
| **M12** policy half forgotten | one message cannot distinguish the two policies | **R7g/R7h** (two routes, one mailbox) |
| **M20** `_assert_capacity` deleted | every R10 row went through the scenario door, which calls `check_epoch_batch_capacity` and never reaches `_assert_capacity` | **R10g/R10h** (hand-built batches, no scenario) |

**M3** was a *prediction* error, not a gap — it was caught, by R1b/R1d, not the
R1 I had listed. Recorded as such: a mutation caught by the wrong row is a
survivor of the row you thought was doing the work.

## Regressions — `run_l0_sweep.py` **18/18 PASS_REF_AND_NATIVE (214s)**

L-0 frozen (`binding_run5`–`14`, `44`, roundtrip probe) all green, and the live
Slice B chain `45` c0 → `46` c1 → `47` c2 → `48` c3 → **`49` c4** → `50` c5a.

## Promotion status — `~~` is **not** yet promotable, and this is why

It is tempting to read commit 4 as the promotion trigger. It is not, and the
spec is the reason. §16.3's gate for commit 4 reads:

> **Reference / native / runtime fold against the Slice A reducer** — *the
> construct is grounded only when **both reducers agree***.

The reference reducer agrees. The native one **cannot yet be asked**: R12c shows
a route's claim is unrepresentable in the frozen IC proof profile. `binding_run50`
(c5a) splits the profile so that it *can* be asked, but explicitly does **not**
give the native reducer mailbox state — and pretending otherwise would repeat
exactly the "provably ignored at runtime" admission commit 4 existed to end.

So the honest ledger against §14b's two-tier test:

| Tier | `~~` status after commit 4 |
|---|---|
| **surface-grounded** (declarable, emittable, round-trips canonical bytes) | **met** — commit 2 (canonical `AsyncRouteDecl`, distinct from `EdgeDecl`, discharging D8) + commit 3 (`~~` parse/format) |
| **IR/runtime-grounded** (runtime executes it, battery covers it) | **met for the reference reducer only** |
| §16.3 c4 gate (*both* reducers agree) | **not met** — pending native mailbox state (c5b) |

**I have therefore left `WRL_CORE_0.1.md` §14 unedited.** Promoting `~~` from
*partial* to *grounded* now would be a self-certification of exactly the kind
errata 0.1.3 was written as a new revision to prevent, and the §14 entry's
current wording — "*not surface-emittable, no structural `EdgeDecl`*" — is now
**stale in the other direction** and needs your ruling to restate rather than my
edit to overwrite.

**Requested ruling:**

1. Confirm the §14 async-route row should be restated to *"surface-grounded;
   reference-runtime-grounded; native pending c5b"* — an errata 0.1.4, not an
   in-place edit of 0.1.3.
2. Confirm **c5b** (native mailbox state under the v2 profile) is the commit
   that closes the §16.3 c4 gate, and that freezing the Slice B line waits for
   it.
3. Confirm the **pre-freeze obligation** still standing from §16.3 —
   `WRL_PORT_SIGNATURE` carrying a validator-owned canonical locator — is
   scheduled inside Slice B rather than deferred past the freeze.

## Autonomous decisions flagged

- **`wrl_fold` is a new module, not a `wrl_ir`/`wrl_canonical` addition** — to
  keep the identity spine stdlib-only for its verified browser port.
- **The injection sits at the two batch-list seams**, not at lowering — so every
  existing L-0 battery is covered through one helper with zero battery edits.
- **`spinner_bench` now reads both halves of the declaration** (policy *and*
  mailboxes) at both film call sites. This is a bug fix, not a feature; R11b
  bounds its blast radius to zero for mailbox-free worlds.
- **M17 reclassified `@noop`** rather than given a new row — the pairing check's
  scope guard is behaviourally inert, and manufacturing a row to "catch" an
  inert edit would be the comfortable lie the mutation discipline exists to
  prevent.
