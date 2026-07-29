# Slice B, commit 5b — the mailbox-capable native profile

**Status:** **all nine** conditions of the commit-5a ruling are green.
(1)–(8) are `binding_run51`, `PASS_REF_AND_NATIVE`. (9) is `mutate51`:
**ALL CAUGHT**, eleven mutants, with the null control green and the `@noop`
surviving. Slice B is **not frozen**, and this memo argues it should not freeze
yet — for **one** reason, stated in §4.

Batteries: `binding_run51.py` (T0–T9, 221s), `binding_run52.py` (L0–L10b, 12s).

---

## 1. What landed, and where

Three places, and no fourth:

- `ic_map` grew a **mailbox stage** and returns `PAIR(EpochControl, bundle)`.
- `ic_reduce` splits that pair and emits `TUP6` instead of `TUP5`.
- `_build_fold` threads the `mailbox_capacity_fault` **latch** across epochs and
  carries each epoch's bundle out.

The **inbox is deliberately not threaded**. `_roll_mailboxes` empties
`next_inbox` at the top of every `admit_step`, so `_commit_deliveries` always
appends into an empty box. Epoch *e*'s inbox is exactly epoch *e−1*'s emitted
bundle, and **D7's lifetime law — REPLACED, not appended — falls out of a shift
in the projection** rather than being implemented a second time.

Condition-by-condition: (1)(2) T0/T0b · (3) T2/T2b/T2c · (4) T3 · (5) T4 ·
(6) T5 · (7) T6 · (8) T8/T9.

---

## 2. The finding that matters most: a mailbox is CLAIM state

The frozen two-field `EpochControl` **did not grow**. What grew is the
**reducer's output**, not the world's input:

- **T1** — with no mailbox, MAP emits the frozen 2-field EpochControl.
- **T1b** — with one, it emits `PAIR(EpochControl, bundle)`; the EpochControl
  still has exactly two fields.
- **T8b** — the reduced world state carries **no mailbox at all**. Every mailbox
  line in a film matched against golden was **rebuilt from the emitted bundle**.

So `binding_run49`'s R12 measurement — a mailbox costs the world state nothing —
survives commit 5b intact rather than being spent by it.

### Two claims from my own pre-commit notes, both RETRACTED

I wrote a baseline (`v6_backend_fingerprints.txt`) *before* this work and it
predicted the opposite. Both of its load-bearing arguments were wrong, and I
would rather flag that than quietly re-file it:

1. **"`binding_run43` 10.16 must be SPLIT three ways."** It says "D8: the
   mailbox moves NO backend fingerprint". It is **green after 5b and correct**.
   Nothing inverts. The proposed split (object_order survives / epin-,obsv-
   survive / slay-,blay- invert) is withdrawn entirely.

2. **"Ruling condition (3), 'route-free v1 terms byte-identical', cannot mean
   what it says; the frozen class is the MAILBOX-free class."** It means exactly
   what it says and is satisfied **literally**. `profile_for_artifact` selects on
   **routes**: a mailbox-declaring but route-free world stays on
   `admit.ic.v1.core52` (T2c, and run50 S9d). The observation underneath the
   claim is still true — `init_claimstate` and the Film v0.7 projection both fork
   on **declaration**, so a route-free mailbox world does carry claim state and
   does emit mailbox film lines — it is simply not a statement about v1 terms.

**Root cause of both.** I reasoned correctly that a mailbox must have runtime
state somewhere, then **assumed "somewhere" was `_v6_fields`** because that is
the state my fingerprint tool happened to hash. The assumption was never
measured. A world-state fingerprint cannot see a claim-state feature.

The file's role has **inverted from prediction to guard**: all five worlds must
now stay byte-identical, and one that moves has smuggled the mailbox into world
state. `mailbox_routed` — which routes into its mailbox, selects
`admit.ic.v2.mailbox53`, and folds real sends natively while moving **none** of
the three columns — is now the strongest row in the file, for the opposite
reason it was added.

---

## 3. The de-fork that had to happen first (`binding_run52`)

The v0.6 encoded-state layout order was written down **five times**, and **two
of the five were dead code that looked authoritative**: `enc_state_v6` and
`dec_state_v6` both called `_v6_fields`, used **none** of what it returned, and
re-walked the layout by hand. A reader correcting `_v6_fields` would have
believed the codecs followed it.

Now `compiler.state_layout` is **the** walk and every consumer projects it —
`_v6_fields`, both codecs, and `wrl_plan._layout_records` (feeding both `slay-`
and `blay-`). `compiler.pose_width` is the one width rule.

Rows worth naming:

- **L4/L5** make it load-bearing rather than cosmetic: a consistent reorder moves
  `enc_state_v6`, `slay-` and `blay-` **together**, and does **not** move the
  film. Before the de-fork the two signatures would have moved and the encoding
  would not — three fingerprints disagreeing with the thing they fingerprint.
- **L0b is a tripwire on a coincidence.** `_v6_fields` **regroups** into
  (base, pose/fault, rotor) and concatenates. That equals the walk *only*
  because the walk already emits kinds in group order `[0,0,0,1,1,2]`. An
  interleaved walk would silently desync the compiler (which reads the regrouped
  list) from the codecs (which read the raw one). This was a **sixth spelling
  hiding inside the fix**, and it is now pinned.
- **L6** — `dec_state_v6` names the field it failed on. This is not readability:
  `mutate_harness` scores a bare traceback as a **crash, not a catch**, so an
  unnamed failure turns a mutation that should be caught into one that proves
  nothing.
- **L9** — the fingerprint file was, until now, **read by nothing**. A guard
  nothing runs is not a guard.

---

## 4. THE OPEN QUESTION — please rule before Slice B freezes

`binding_run51` **T7**, recorded as a measured boundary rather than left silent.

`admit_mailbox_deliver_all_v1` replaces **seam 1** as well as seam 2. On an
**equivocal event key** (two facts, same writer and sequence, different
candidate) the declared policy yields no receipt, no delivery, and a
`MailboxReject`. The IC ACCEPT stage implements the **frozen seam 1** —
leader-wins, `_resolve_candidates_min` — so it mints a receipt and **delivers**.

Measured: golden emits `MailboxReject`, the fold emits `MailboxEnqueue`.

Three things bound it:

- The divergence is in **ACCEPT**, not in the mailbox stage this commit added,
  and it **predates** it — commits 4 and 5a both left ACCEPT alone.
- It is **unreachable from a world's own routes** (T7c): `route_claim_identity`
  numbers by canonical RouteKey, so two routes mint two distinct event keys. It
  is reachable only from an authored batch.
- It is **exactly that shape and no wider** (T7b): the same world, policy and
  mailbox with unique event keys folds identical films.

**The question.** Should Slice B freeze with a declared policy whose seam 1 the
reducer does not implement, documented as T7 — or should ACCEPT be brought onto
the declared seam 1 first, as a commit 5c, so that "declared policy honoured"
(condition 7) is true without an asterisk?

I have not guessed at this. It changes what `~~` *means* when it is promoted,
and that is a specification decision rather than an implementation one.

---

## 4b. What the promotion edit actually is — and a stale row

I checked my own claim about §14 rather than repeating it, and it was loose in
one place and wrong in another.

**Loose.** Core does not say `~~ NOT YET FULLY GROUNDED`. §5's surface-status
table (line 121) says:

> `~~` async | **partial** — IR/runtime-grounded, not surface-emittable, no
> structural `EdgeDecl` | §14b, §16

**Wrong.** Both clauses of that row are now out of date, and I measured it by
PARSING rather than grepping:

1. **`~~` IS surface-emittable.** `format_wrl_core` emits
   `[p0] ~~msg~~> [mb] (body=0.0.0.7)`, and re-parsing that emission is
   identity-stable (`sem-079769eceb95e31b` both ways).
2. **The explicit-twin identity proof holds.** The same route written as `~~`
   surface text and written as a route dict onto a parsed graph produce the
   **byte-identical SemanticArtifactID**. `binding_run48` (Slice B commit 3,
   green in the sweep) already proves this at RECORD level — Q0 "the ruled
   spelling parses to exactly the ruled record" and Q3 round-trip. I restated it
   at **identity** level because §16.3 asks for an identity proof and record
   equality implying identity equality is an inference, not a measurement.
3. **"no structural `EdgeDecl`" is mis-framed as a gap.** §14b/D8 *requires* a
   canonical logical route declaration **distinct from** `EdgeDecl`. Having no
   structural `EdgeDecl` is the requirement being **satisfied** by
   `AsyncRouteDecl` (commit 2), not a deficiency. Read literally today, the row
   cites the ruled design as the reason the construct is partial.

§14 (line 283) carries the same sentence and needs the same correction.

**So the §16.3 commit order is exhausted:** 0 importer · 1 mailbox surface
declaration · 2 `AsyncRouteDecl` distinct from `EdgeDecl` · 3 `~~` emission +
explicit twin (measured above) · 4 reference/native fold against the Slice A
reducer (`binding_run51`, `PASS_REF_AND_NATIVE`).

**And the §16.3 pre-freeze obligation is already discharged.**
`WRL_PORT_SIGNATURE` now carries a validator-owned canonical `ObjectKey`
locator (`wrl_canonical.validate_port_projection`), covered by `binding_run46`
rows 471/483. I flag it because it is an easy thing to arrive at freeze having
forgotten; it is done, not outstanding.

I have **not** edited §5 or §14. Rewriting a frozen status row is the promotion
itself, and §4 is the reason I am not doing it unasked.

---

## 5. State of the tree

| battery | verdict |
|---|---|
| `binding_run51` (c5b, T0–T9) | ALL PASS — `PASS_REF_AND_NATIVE`, 221s |
| `binding_run52` (de-fork + guard, L0–L10b) | ALL PASS — `PASS_REF_ONLY`, 12s |
| `binding_run43` (Slice A, incl. 10.16) | ALL PASS — `PASS_REF_AND_NATIVE` |
| L-0 sweep (with 52 registered) | **ALL PASS — 20/20 green, 236s** |
| `mutate51` (condition 9) | **ALL CAUGHT** — 11/11 |

Not frozen. `~~` remains **partial** in `WRL_CORE_0.1.md` §5/§14. **One thing
stands between the tree and promotion: the §4 ruling.** Every commit-5a
condition is green, the §16.3 commit order is exhausted, and its pre-freeze
obligation is discharged (§4b).

### A note on the mutation blast radius

Every mutant reddened a **superset** of the rows `mutate51` demanded of it —
P1 was required to redden `T1, T2c` and reddened eight rows; P4 was required to
redden three and reddened eleven. The required-row lists are therefore
conservative, which is the safe direction: a battery that catches more than it
promised is not a battery that promised too little, but the predictions in
`mutate51`'s comments should be read as **floors**, not as descriptions of a
defect's reach.
