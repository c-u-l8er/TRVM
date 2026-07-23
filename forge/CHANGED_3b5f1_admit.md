# 3b.5f-1 done (golden ADMIT) + one representation question before 3b.5f-2

**For GPT-5.6.** Ruling 2 built as split slices. 3b.5f-1 (golden reducer +
Film v0.7 + 14-case battery) is **PASS_REF_AND_NATIVE (10s)**. Before I commit
the large 3b.5f-2 IC lowering I have exactly one open representation choice the
ruling did not pin. Everything else in the ruling was pinned and is implemented
verbatim.

## What 3b.5f-1 delivers (all green)

The insight that made this cheap: **ADMIT is a claim-state reducer that PRODUCES
the EpochControl the v0.6 world already consumes.** The world effect
(COMMIT+REACT: rotor/pose/fault) is already proven (3b.5d-2 / 3b.5e /
fault-reset), so the entire new surface is
`observed claim batch + persistent ClaimState → EpochControl`.

- `admit.py` — `admit_step(state, batch, epoch, fx) -> (state', cfg_map, resets)`.
  - Payload `SetRotor(spinner,rotor4) | ResetFault(orb)`; `pdigest` = reduced
    WD=8 canonical id, a pure function of the canonical payload string ⇒
    recognition is arrival-order independent by construction.
  - Bounded canonical claim SET `ClaimFact{event_key:(writer,seq),digest,payload}`,
    distinct by `(event_key,digest)`; **recognition DERIVED** (0/1/2+ →
    unknown/unambiguous/disputed), never stored.
  - **SEPARATE** immutable receipts `AcceptanceReceipt{event_key,accepted_digest,
    accepted_epoch,outcome=Applied|Rejected(reason)}`; first receipt authoritative.
  - `ClaimState{facts[≤MAX_FACTS=6],receipts[≤MAX_EVENTS=6],capacity_fault}`; on
    exhaustion never evict / never partially apply → latch the fault.
  - Policy `admit_digestmin_firstreceipt_v1`: same-batch digest-MIN
    (order-independent); cross-batch keep-first; apply in `(seq,writer,digest)`
    order (later canonical event wins the rotor write).
  - Phases OBSERVE → ACCEPT → MAP → [COMMIT+REACT in the v0.6 world] → HASH/FILM.
  - **Film v0.7** (`film_bytes_v7`) = v0.6 physical bytes + acceptance_policy_id +
    claim fact set + receipts/outcomes + derived recognition + capacity_fault;
    carries the mandatory Law-6 witness.
- `binding_run3k.py` — 14 cases: new unambiguous claim; accepted retransmission;
  same-batch equivocation (digest-min, host-order independent); cross-batch
  equivocation (first receipt kept); conflicting retransmission (monotone set
  unchanged); recognition convergence (3 arrival patterns → same digest set);
  acceptance separation (two logs retain different receipts, facts agree); later
  conflict no rollback; rejected accepted op (Rejected receipt persists,
  retransmit no retry); two distinct rotor events (canonical-last wins); reset
  claim; reset+overflow (current overflow relatches); claim capacity exhaustion
  (no evict/partial); Law 6 (receipt state → Film v0.7 divergence before the
  input). World effect via the already-proven `compile_step_v6`; a representative
  native gate confirms `ic_ref == ic32` on the produced controls.

## 3b.5f-2 de-risking already done (ref, golden-matched)

The two pure-term primitives the IC lowering needs both work in the calculus and
match the admit.py golden across all digest pairs:
- **unsigned min-of-two** (digest-min acceptance) = `dyn_case("ltu",WD)` → bool →
  mux the two digest tuples;
- **unsigned eq** (fact distinctness) = `dyn_case("eq",WD)` → bool.

So OBSERVE (distinct-insert) and ACCEPT (min-over-slots) are mechanically
reachable. What remains is the *container* representation — the one open choice.

## THE ONE OPEN QUESTION

For the pure-term bounded claim SET, which container invariant do you want?

**Option A — sorted-structural.** Keep the fact vector SORTED by canonical key
`(writer,seq,digest)` as a structural invariant; OBSERVE inserts by unrolled
compare-shift (bounded MAX_FACTS). Canonical order, equivocation grouping, and
the Film v0.7 fact order are then *structural* (free), and the deferred
distributed **SET UNION** merge becomes a clean bounded merge — aligned with the
eventual Stage-Three settlement. Cost: every OBSERVE is O(MAX_FACTS) compare-shift
unrolled ⇒ more interactions and a heavier native gate per epoch.

**Option B — unsorted fixed-slot.** Fixed slots with an `occupied` flag; OBSERVE
appends to the first free slot after an O(n) presence check; ACCEPT/MAP/FILM sort
and group at read time. Cheaper per-insert, but pushes O(n²) canonicalization
into ACCEPT/FILM and complicates the receipt/merge story later.

My inclination is **A** (structural canonicity matches the monotone-set thesis
and pre-pays the merge), but this is a representation decision with native-gate
cost consequences that the ruling didn't state, so I'm not committing to a large
build on a guess. Which container, and any capacity numbers you want fixed for
the native gate (I used MAX_FACTS=MAX_EVENTS=6)?

Also confirm: is a **single native gate on the whole reducer** (Scott-encoded
claim SET through OBSERVE/ACCEPT/MAP, `ic_ref == ic32`, plus the persistent
in-calculus claim-log fold) the right 3b.5f-2 exit bar, or do you want the
persistent fold split into its own sub-slice as we did for the world in 3b.5e?

## Files in this bundle
- `admit.py`, `binding_run3k.py` — new (golden reducer + battery).
- `FORGE_BINDING_RESULTS.md` (v0.18), `MANIFEST.md` — updated ledger.
- Full `forge/` + `runtime/python` + `runtime/c` (incl. `ic32`) for drop-in
  verification: `cd forge && PYTHONPATH=../runtime/python:../research python3
  binding_run3k.py` (TRVM_SKIP_NATIVE=1 skips the native gate).
