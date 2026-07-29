# Slice B, commit 5c — ACCEPT selected from the sealed policy

**Status:** **all eight** gates of the commit-5c ruling are green.
Gates (0)–(7) are `binding_run51`, **34 rows, `PASS_REF_AND_NATIVE`, 101s**.
Gate (8) is the full re-run: `mutate51` **ALL CAUGHT, 14/14**, sweep
**20/20 green (303s)**, `binding_run3o` **`PASS_REF_AND_NATIVE` (33s)**.

**T7 has flipped.** The divergence commit 5b recorded as a measured boundary
— golden emits `MailboxReject`, the fold emits `MailboxEnqueue` — is closed:
`ic_ref == ic32 == golden`.

Slice B is still **not frozen** and `~~` is still **partial** in
`WRL_CORE_0.1.md` §5/§14. That is now a promotion decision (§8), not a defect.

---

## 1. Gate by gate

| gate | row(s) |
|---|---|
| (0) T7 flips: `MailboxReject`, no `MailboxEnqueue`, no receipt | **T7** |
| (1) T7b stays green for unique event keys | T7b |
| (2) T7c stays a route-identity **fact**, not an exception | T7c |
| (3) identical-duplicate control | **T7d** |
| (4) prior-receipt behaviour pinned against golden | **T7e** |
| (5) the frozen first-receipt policy is byte/term identical | T2, **T2c**, **T2d** |
| (6) mutation: revert mailbox ACCEPT to leader-min → caught | **P10** |
| (7) mutation: force equivocation rejection on the frozen policy → caught | **P11** |
| (8) re-run 51 + mutate51 + the complete frozen/live sweep | §7 |

Two rows were added beyond the ruling: **T7f** (§3), and **P12** (§5).

---

## 2. What landed, and where

Four places:

- **`admit_ic.py`** — `AcceptRule(policy_id, reject_equivocal)`, two instances
  (`ACCEPT_MIN`, `ACCEPT_UNIQUE`), and `accept_rule_for_policy`. The rule is
  threaded as an optional argument into `ic_accept`, `ic_map` and `ic_reduce`,
  **defaulting to `ACCEPT_MIN`** so every pre-existing caller is unaffected.
- **`wrl_fold.runtime_seams`** — widened from a pair to a **triple**,
  `(admit_policy_id, film_mailboxes, accept_rule)`. This is the ruling's
  "composed runtime seam": one call that a caller cannot half-honour.
- **`binding_run3o._reject_entries`** — the `MailboxReject` projection.
- **`binding_run3o._project_claims`** — where the rejects are attached (§4.1).

The equivocation test itself is **not** an `O(cap²)` scan. The fact vector is
sorted ascending and all-ones padded, so **adjacency is equivocation**: an
event key's candidates are contiguous. `ACCEPT` already computes `leader` (no
predecessor shares my ekey); adding a **successor** test yields
`len(candidates) == 1` in one extra comparison per slot.

### The rule is derived from ONE field and nothing else

The ruling named five forbidden sources. `runtime_seams` reads the sealed
`admit_policy_id` and **not**: the v2 proof profile, mailbox presence, `mcap`,
the existence of a `Send`, or a caller-supplied option. T6a proves the
artifact route and the policy-id route reach the *same object*, because the
artifact route only reads that field.

---

## 3. The finding: the two axes actually disagree somewhere — T7f

The ruling said the proof profile and the acceptance policy are separate
semantic axes "even where they currently correlate". I went looking for
where they **stop** correlating, because a claim of orthogonality that no test
can distinguish from correlation is not measured.

They are selected by different predicates:

- `profile_for_artifact` selects on **routes** →
  `admit.ic.v1.core52` / `admit.ic.v2.mailbox53`
- `semantic_surface_for_roles` selects `admit_policy_id` on **mailbox presence**

So there is exactly one world where they visibly disagree: a **mailbox-bearing,
route-free** world. It declares `admit_mailbox_deliver_all_v1` while lowering
under `admit.ic.v1.core52`, with `mcap == 0` and no `Send` kind in the profile.

**T7f folds an equivocal `SetRotor` in that world.** It is refused —
`ic_ref == golden`, one `MailboxReject`, no receipt — and the rotor stays at
`10,00,00,00`.

That single row closes **two** ruling clauses at once:

1. **The five forbidden sources.** A rule read from the profile, the mailbox
   bundle, `mcap`, or the presence of `Send` could not possibly reach this
   world. It is reached anyway.
2. **"Do not implement equivocation rejection only for `Send`."** The refused
   claim is a `SetRotor`, in a world with no mailbox traffic at all, and the
   unmoved rotor is the proof that **MAP never applied it**. ACCEPT resolved
   the event key before MAP looked at the operation.

The negative half is in `mutate51`: **T7f goes red under both P10 and P12**.
It is not merely insensitive to the forbidden sources, it is genuinely
sensitive to the permitted one.

---

## 4. Three corrections to my own work

### 4.1 The rejects were gated on the mailbox bundle — the defect the ruling named, in my own code

`_project_claims` attached `MailboxReject` entries **inside** the
`if len(row) > 5:` branch that builds the mailbox bundle. I had written a
comment one screen above saying a reject is not a mailbox event; the code did
not agree with it.

This was **not** caught by reasoning. It was caught by T7f returning
`EQUAL: False` with no `ledger:MailboxReject` line at all, in the `mcap == 0`
world. Gating on the bundle had silently made rejection **Send-specific** —
precisely what the ruling forbade — and only the orthogonality world could
show it. The rejects are now computed unconditionally and attached via an
`elif`.

### 4.2 The capacity guard checked one fault, and there are two

`_reject_entries` skipped rendering when `receipt_capacity_fault` was set.
Reading `admit_step` showed golden abandons the **whole ACCEPT stage** on
**either** overflow, and **both bits are sticky latches** — so post-epoch state
cannot distinguish "this epoch aborted" from "an earlier epoch did".

The guard now covers both, and the boundary is **stated rather than hidden**:
this projection renders no rejects for any epoch in a faulted trajectory. That
direction is deliberate. It can omit an entry golden emitted (a **loud** film
mismatch) but can never invent one golden did not (a **quiet** false pass).

### 4.3 A prediction I wrote into `mutate51` was wrong

For **P11** (equivocation forced onto the frozen policy) I wrote: *"There is no
behavioural row that could catch it honestly, because under this mutant the
mailbox world still behaves correctly."*

The run said **T6c**. A **mailbox-free** world declaring a rule that rejects
equivocation is a defect visible **at the seam**, before any term is emitted.
The prediction was wrong in the useful direction — the seam had already been
made observable, so the selection is checked where it is *made* and not only
where its bytes land. The comment in `mutate51.py` now records the retraction
rather than the prediction.

The same happened, twice more, for T7f under P10 and P12. Both catch-sets are
now **observed** values folded back into the declarations.

---

## 5. P12 — the mutation the ruling did not ask for

`ic_accept` and `ic_map` compute per-slot eligibility **independently**. There
is no shared `accept_i` between them, only two copies of the same arithmetic.
So the single most likely way to get this commit wrong is to thread the rule
into one stage and forget the other, producing exactly the incoherent machine
the ruling named: **ACCEPT refuses the equivocal key a receipt while MAP
enqueues its message anyway.**

P12 does that. It is caught by **T2d** at the emitter (before any fold),
by **T7** on the "no `MailboxEnqueue`" clause — which is why that clause is
asserted separately rather than left implied by film equality — and by
**T7f**, whose witness is the sharpest of the three: the rotor **moves**. The
leak shows up as a change to *world* state in a world containing no mailbox
traffic whatsoever.

---

## 6. What is NOT fixed, and why — T7g

`film_bytes_v7` has **no policy parameter**. It renders `admit:policy=` from
the module constant `ACCEPTANCE_POLICY_ID`, so a world declaring
`admit_mailbox_deliver_all_v1` renders a film **labelled**
`admit_candidate_min_firstreceipt_v1`.

Both runtimes render it identically, so this is a **label** defect, not a
divergence — every `ic_ref == ic32 == golden` claim in this memo holds. It is
recorded as **T7g**, a measured row, rather than fixed, because the fix moves
**declared film bytes** and the ruling places the film in the promotion. It is
flagged here so it is not discovered later as a surprise.

---

## 7. The packet now builds from a computed import closure

The ruling noted the 19-entry 5b packet was reviewable but **not independently
runnable**: `binding_run51.py` stopped at `ModuleNotFoundError: admit`. That
packet was assembled **by hand**.

This one is built by `tools/build_packet.py`, which walks the import graph with
`ast`, additionally resolves **subprocess entry points** (the sweep names its
batteries as bare strings) and **data assets** opened by name
(`ic_v1_term_fingerprints.txt`), and **fails** rather than shipping if any
non-stdlib import is unresolved. `--verify` extracts the finished zip into an
empty temp dir and runs the sweep **there**.

`--verify` only runs the sweep, so I replayed the other two entry points from
that same extraction by hand rather than assuming they came along:

| from `<extract>/forge/` | result |
|---|---|
| `python3 run_l0_sweep.py` | ALL PASS — 20/20 green, **262s** |
| `python3 binding_run3o.py` | ALL PASS — `PASS_REF_AND_NATIVE`, **30s** |
| `python3 mutate51.py` | **ALL CAUGHT — 14/14** |

All three are bare commands: **no `PYTHONPATH` is required.** I had been
setting one out of habit; measuring showed the batteries self-locate the
reference runtime, so the habit was hiding whether the packet was actually
self-sufficient. It is.

---

## 8. State of the tree

| battery | verdict |
|---|---|
| `binding_run51` (c5c, T0–T9b, 34 rows) | ALL PASS — `PASS_REF_AND_NATIVE`, 101s |
| `binding_run3o` (ADMIT fold, hand-run) | ALL PASS — `PASS_REF_AND_NATIVE`, 33s |
| L-0 + LIVE sweep | **ALL PASS — 20/20 green, 303s** |
| `mutate51` (gates 6, 7 + P0–P9, P12) | **ALL CAUGHT — 14/14** |

`binding_run3o` is deliberately **not** in the sweep and is re-run by hand
alongside every sweep in this slice, because this commit changed its
projection: `_project_claims` now renders a ledger entry it never rendered
before. A defaulted parameter that changes **output** has a wider blast radius
than one that changes shape.

### The promotion is next, and is not mine to start

With T7 closed, "declared policy honoured" is true without an asterisk. Per the
ruling the promotion is **WRL Core 0.2.0** — a new cut, not an in-place edit of
frozen 0.1.3 — promoting Mailbox to surface-grounded, `~~` to grounded across
source / canonical IR / sealed-policy reference behaviour / native reduction /
film / replay, and `AsyncRouteDecl` as the **logical** route representation
distinct from structural `EdgeDecl`.

The §5 row (line 121) and the §14 sentence (line 283) are both stale today, as
5b §4b measured. I have still not edited them: rewriting a frozen status row
**is** the promotion.
