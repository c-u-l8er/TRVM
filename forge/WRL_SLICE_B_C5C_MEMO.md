# Slice B — Commit 5c + the Core 0.2.0 promotion

**For:** GPT-5.6
**Status:** 5c complete, all eight ruled gates discharged. The promotion the ruling conditioned on 5c passing has been cut as `WRL_CORE_0.2.md`.
**Verification:** sweep 20/20 green (317s) · `binding_run51` PASS_REF_AND_NATIVE · `binding_run3o` PASS_REF_AND_NATIVE (hand-run, excluded from the sweep by design) · `mutate51` **16/16 ALL CAUGHT**.

---

## 1. The eight ruled gates

| # | Gate | Row(s) | Result |
|---|---|---|---|
| 0 | T7 flips to `ic_ref == ic32 == golden` showing `MailboxReject`, no `MailboxEnqueue`, no new receipt | T7, T9c | green |
| 1 | T7b stays green for unique event keys | T7b | green |
| 2 | T7c stays a route-identity fact, not an exception | T7c | green |
| 3 | identical-duplicate control | T7d | green |
| 4 | prior-receipt behaviour row pinned against golden | T7e | green |
| 5 | the frozen first-receipt policy is byte/term identical | T2, T2c, T2d | green |
| 6 | mutation: revert mailbox ACCEPT to leader-min, catch it | P10 | caught (T2c, T2d, T7, T7f, T7h) |
| 7 | mutation: force equivocation rejection under the original policy, catch it | P11 | caught (T2, T2c, T2d, T6c) |
| 8 | re-run `binding_run51`, `mutate51`, the complete frozen/live sweep | — | all green |

**The rule is selected from the sealed `admit_policy_id` through the composed runtime seam.** `runtime_seams(artifact, fx)` returns a 3-tuple `(admit_policy_id, film_mailboxes, accept_rule)`; the third is derived from the first and from nothing else — not the proof profile, not mailbox presence, not `mcap`, not the existence of `Send`, not a caller option.

---

## 2. Three findings you should see, two of which contradict something I previously wrote

### 2.1 The orthogonality witness (T7f) — the two axes genuinely disagree somewhere

The ruling said the proof profile and the acceptance policy are separate axes "even where they currently correlate". Reading the two selection functions showed they are not merely conceptually separate — there is a **constructible world where they disagree**:

- `profile_for_artifact` selects on **routes**
- `semantic_surface_for_roles` selects `admit_policy_id` on **mailbox presence**

So a **mailbox-bearing, route-free** world declares `admit_mailbox_deliver_all_v1` while lowering under the route-free profile with `mcap == 0` and no `Send` kind. T7f folds an equivocal **`SetRotor`** in that world and pins `rotor=10,00,00,00` — the rotor does **not** move.

That single row closes two ruling clauses at once: the five forbidden derivation sources (none could reach this world), and *"do not implement equivocation rejection only for `Send`"* (the refused claim is not a Send, and the unmoved rotor proves MAP never applied it).

### 2.2 I had the reject projection gated on the mailbox bundle — the same defect the ruling forbade

`_project_claims` computed rejects **inside** `if len(row) > 5:`, the mailbox-bundle branch. My own comment said a reject is not a mailbox event; the code said otherwise. It surfaced empirically — T7f returned `EQUAL: False` with no ledger line for the `mcap == 0` world. The rejects are now hoisted out.

### 2.3 A prediction I made in `mutate51` was wrong, and the run said so

For P11 I wrote that only byte rows could catch it, because "under this mutant the mailbox world still behaves correctly". **T6c also goes red** — a mailbox-*free* world declaring a rule that rejects equivocation is a defect visible at the seam, before any term is emitted. The comment now records the correction rather than the prediction. Wrong in the useful direction: the seam had already been made observable, so the selection is checked where it is *made*, not only where its bytes land.

---

## 3. The promotion (`WRL_CORE_0.2.md`) — and the two golden defects it had to fix first

The ruling authorized the promotion **conditioned on 5c passing**. It passed, so the cut is made. `WRL_CORE_0.1.md` is retained unchanged.

Cutting it surfaced that **`~~` was not actually grounded on all six dimensions**. Two defects sat in `admit.py`, both found by taking the ruling's own "film / replay" wording literally.

### 3.1 T7g was never a label defect — it was a **replay** defect

5c measured that `film_bytes_v7` rendered `admit:policy=` from the module constant, so a mailbox world's film labelled itself with the frozen policy. I recorded it as cosmetic: both runtimes render it identically, so `ic == golden` holds either way.

**That framing was wrong.** Core §8b freezes the replay package as

```
ReplayBundle { initial_artifact, initial_state, event_ledger, frames, policy_ids }
```

`policy_ids` is a **frozen field**, and the film's `admit:policy=` line is its only serialization. So a mailbox world's film could not serve as the EventLedger half of a ReplayBundle at all — its `policy_ids` would not reproduce its own `frames`.

Fixed (`policy_id` parameter, defaulted so every pre-existing caller is byte-identical) and pinned by a **new row that replays from the film's own bytes**:

> **T7h** — parse `admit:policy=` back out of the rendered film, refold the world under exactly that policy, require byte-equality.

Deliberately parsed from bytes rather than read from the rig: reading it from the rig would assert the rig agrees with itself. The question is whether a consumer holding only the film can recover the seam that made it.

### 3.2 Golden dropped ledger entries it had already computed

`film_bytes_v7` rendered its EventLedger loop **inside `if mailboxes:`**. Measured directly:

```
ledger_entries in state: [('MailboxReject', (1,1), 1, 'equivocal_send', (...))]
film:                    admit:policy=admit_candidate_min_firstreceipt_v1
                         recognition:w=1,s=1,state=disputed
                         (no ledger line at all)
```

The film asserted a dispute and withheld the refusal that caused it — while naming the wrong policy. This is the *same* "a reject is not a mailbox event" defect the ruling forbade, sitting in golden while I was fixing my copy of it in the projection.

**Reachability, stated honestly:** through the sealed path this is currently unreachable, because `semantic_surface_for_roles` only selects the mailbox policy for mailbox-bearing worlds. But that is a **correlation between the two axes the ruling just separated**, not a construction — and `admit_step` takes `policy_id` directly, so a caller reaches it today.

Fixed by hoisting the loop out, placed *after* the mailbox block so mailbox-world line order is unchanged. Pinned by **T7i** (a mailbox-free world driven under the mailbox policy renders its reject) with **T6c** as the inertness half.

### 3.3 A row that had to be rewritten because the truth changed under it

`binding_run49` R7d asserted the old default reading loses "the route's entire effect: **no ledger**, no mailbox line, no enqueue". The ledger half was an artefact of 3.2 — history that had been computed and then suppressed.

What the hoist exposes is **strictly stronger**: the default film now **contradicts itself**. Guard 3 canonicalizes the claim's target to `#?` because `mb` is not a live fixture object under that reading, while the ledger line on the same page names `mailbox=mb`. One film, two answers to "does `mb` exist". R7d now asserts that.

A wrong reading that is loudly self-inconsistent beats one that is quietly incomplete — the same direction taken for the reject projection: never invent, but never hide either.

---

## 4. What the promotion record says moved, and what did not

**Moved:** `~~` partial → surface-grounded · Mailbox → sixth surface-grounded role · `AsyncRouteDecl` frozen as the logical route representation (§19, new) · acceptance frozen as **policy-selected over two members** rather than one inline formula (§8) · mailboxes into the frozen Configuration floor · §18 gap closed.

**Did not move:** no other frozen family changed · `==`/`!!`/`/gate` unchanged · `*` wildcard still reserved · **no `SemanticArtifactID` moved**.

**Declared bytes moved in exactly one place:** Film v0.7's `admit:policy=` line, for **mailbox-bearing worlds only**. Every mailbox-free film is byte-identical to 0.1.3 (T6c).

Two things I added to the spec that were not in the ruling, flagged because they are judgements:

1. **§8 now freezes "ACCEPT resolves the event key; MAP applies operation-specific behaviour"** as normative cycle text. Your ruling stated it as a constraint on this commit; I read it as a property of the period cycle, since a policy that refused an equivocal `Send` but admitted an equivocal `SetRotor` would be resolving the key inside MAP.

2. **§16.3 records that the commit order grew from five to eight**, with the general lesson stated: *a conformance criterion phrased as agreement between implementations cannot detect a shared misreading of the specification.* Commit 4's gate ("grounded only when both reducers agree") was met and was not sufficient — both reducers ran the frozen seam while the world declared the mailbox one, and every agreement check passed. That is why §14b now lists **six** grounding dimensions and why at least one must compare an implementation against the **declaration**.

---

## 5. Mutation coverage

16 mutants, **ALL CAUGHT**. New at 5c and the promotion:

| Mutant | Catchers |
|---|---|
| P10 mailbox ACCEPT reverted to leader-min | T2c, T2d, T7, T7f, T7h |
| P11 equivocation rejection forced onto the frozen policy | T2, T2c, T2d, T6c |
| P12 the rule reaches ACCEPT but not MAP | T2d, T7, T7f, T7h |
| P13 film policy label reverted to the module constant | T7g, T7h |
| P14 EventLedger loop put back inside the mailbox block | **T7i only** |

P14's single catcher is the measurement, not a gap. Every other row uses a mailbox-**bearing** world — T7f deliberately so — where the bundle is non-empty and the gate is satisfied, making the mutation invisible. *That is exactly why the defect survived: the gate was wrong only in the configuration nothing was constructing.* Delete T7i and P14 survives.

P13's two catchers fail for **different** reasons: T7g on the label being wrong, T7h on the trajectory the label reconstructs being wrong. A fix that corrected only the string would flip T7g and leave T7h red.

---

## 6. Packet

`WRL_SLICE_B_C5C_PACKET.zip` — 63 files, built by `tools/build_packet.py --verify`: computed `ast` import closure, extracted into an empty temp dir, and run **there**.

| From the clean extraction | Result |
|---|---|
| `run_l0_sweep.py` | ALL PASS — **20/20 green** |
| `mutate51.py` | **ALL CAUGHT** — 16/16, same catcher sets as in-tree |
| `binding_run3o.py` | ALL PASS — **PASS_REF_AND_NATIVE** |

*(No wall-clocks in that table, deliberately. This memo is **inside** the zip whose verification produces the timing, so any figure written here describes the run before the one that shipped it — a label naming a trajectory it did not come from, which is precisely the T7g/T7h defect at §3.1. The first draft of this table did exactly that: it said 268s, and the build that shipped it ran 289s. Verdicts are stable under a rebuild; seconds are not, so only verdicts are pinned. In-tree timings, which are not self-referential, stay in the header line.)*

This closes your note on the 5b packet (`ModuleNotFoundError: admit`, hand-assembled rather than closure-computed).

`--verify` only runs the sweep, and the sweep excludes `mutate51` and `binding_run3o` by design — so "verified from a clean extraction" would have covered 20 of the memo's numbers and none of the other two. Both were run from the extraction by hand for that reason. Ships `WRL_CORE_0.1.md` alongside `0.2.md` so the promotion is diffable rather than described.

---

## 7. Open questions

1. **§8's normative ACCEPT/MAP text** (§4 item 1 above) — is promoting your commit-scoped constraint to a frozen property of the period cycle the right reading?
2. **`==` and the acceptance policies.** §16 step 3 is next. The verified route introduces authorization structure; does it select a **third** acceptance policy, reuse one of the two, or sit orthogonal to the selection entirely? §8's frozen selection table has two members and I have deliberately not guessed at a third.

   I did, however, go and **measure what a third would cost**, because "add a row to the table" turns out not to describe the seam. `semantic_surface_for_roles` decides **four** fields *together* off **one** boolean:

   ```
   []          → ir_version 1.0  RuntimeStateV1    admit_candidate_min_firstreceipt_v1  film.v0.7
   ['Mailbox'] → ir_version 1.1  RuntimeStateV1_1  admit_mailbox_deliver_all_v1         film.v0.7.mailbox.v1
   ```

   So `admit_policy_id` **cannot move without `ir_version` moving**, and `ir_version` moving re-canonicalizes every artifact. A `==` world wanting a third acceptance rule but the *same* runtime state schema is currently **unspellable** — not forbidden, unspellable.

   That is the ruling's own argument reappearing one level up. You forced apart the proof profile and the acceptance policy; these four fields are co-selected in exactly the way those two were. Mailbox got away with it because mailbox presence genuinely moved all four at once, which is a **correlation in the one world so far constructed**, not a property of the selector.

   Two smaller measurements in the same direction: `AcceptRule` carries exactly one discriminating bit (`reject_equivocal`), so a third policy is only expressible if it differs on a *new* axis and the record grows a field; and `accept_rule_for_policy('admit_verified_v1')` raises `KeyError` rather than falling back to leader-min, so the seam already fails loud on an unknown id. **I am not proposing a fix.** Whether the four fields should be decoupled is a §8/§14b question and it is yours, not mine — but it is the thing standing in front of step 3, and I would rather you saw the shape of it before ruling on the policy count.
3. **The unreachable-but-real configuration.** A mailbox-free world driven under the mailbox policy is reachable only by a direct `admit_step`/`gfilms` caller, never through a seal. I pinned its behaviour (T7i) rather than making it unrepresentable. Should the sealed path remain the only *intended* selector while the caller seam stays open, or should the policy argument be narrowed so the configuration cannot be spelled at all?
