# Forge Semantic IR v1.1 — Mailbox Grounding — Slice A SPECIFICATION (Revision E)

*Status:*

```
IMPLEMENTED — MAILBOX REDUCER BATTERY GREEN
POST-RULING Q3/Q4 COMPLETE
CANONICAL ROLE DECLARATION PRESENT
SEMANTIC POLICY/VERSION WIRING COMPLETE  (Commit 8)
PRODUCTION COMPILE/RUN SEAM PROVEN       (Commit 8, §10.16)
NOT YET CLOSURE-PROVEN
NOT FROZEN
~~ remains Reserved/partial
```

*Commits 0–8 are complete; `binding_run43` executes §10.1–§10.18 `ALL PASS — PASS_REF_AND_NATIVE` (81 assertions). D6–D11 accepted as ruled; both Revision B open items (D9 capacity counter-correction, D10 two-seam parameterization) accepted; all four Revision C open questions **ruled** — see "Rulings received" below. Written against `FORGE_SEMANTIC_IR_v1.md` (FROZEN 2026-07-21) and `WRL_CORE_0.1.md` (rev 0.1.1). v1 resolved D1–D5; this document specifies **D6–D11**. This document is **not frozen**, and `~~` is **not** promoted to Grounded.*

**Purpose.** Ground the WRL `~~` async route — currently *"reserved in WRL, **absent** from IR v1 (no placeholder node)"* (v1 §2) — as the smallest additive IR revision that preserves every frozen v1 law.

**Non-goals.** Fragments, capabilities, supervision, dynamic topology, arbitrary actor behavior, distributed settlement, transport. All remain out of scope per v1 §0/§8.

**Revision C changes.** Two-stage capacity model frozen (§5); D10 parameterization shape and equivocation details frozen (§6); conformance test #7 qualified per ruling, four silent-failure obligations promoted to required tests, identity split into three separate fixtures (§10).

**Revision D changes.** All four Revision C open questions ruled and implemented as Commit 7: §10.12 restated as the **compositional** conformance clause (Q1); `MailboxDecl` added to the sanctioned canonical Semantic IR and §10.11d re-run over a **real mailbox-bearing artifact** (Q2); `empty_accumulator` removed from the policy registry, the common reducer now owning a fixed accumulator seed (Q3); receipt-capacity checking moved **after** pure candidate resolution (Q4). §6 gains the "per resolution epoch" wording for `MailboxReject`; §10 gains rows 10.13–10.15.

**Revision E changes (Commit 8 — the identity spine).** Revision D grounded the mailbox *reducer*; it did not finish grounding the *identity*. A sealed mailbox artifact still named the mailbox-free acceptance policy, still claimed `ir_version` `1.0` and `film.v0.7`, and could not be sealed as a compile plan at all. Commit 8 closes that gap: §9 gains the **unified role-derived semantic surface**, §3 gains the mailbox's place in `CompilePlanV1`, §2 makes the runtime state schema **exact rather than widened**, §7 pins the mailbox width bound, and §10 gains rows **10.16–10.18**. The mailbox world's `SemanticArtifactID` moved as a result; that movement is the *point* of the commit, and the Revision D value was provisional. Every mailbox-free identity is unmoved.

---

## Implementation ledger

Lifecycle: **ARCHITECTURAL GATE CROSSED → IMPLEMENTED → BATTERY PROVEN → FROZEN.** This document is **not frozen**. `~~` is **not** promoted to Grounded; it stays *Reserved/partial* in `WRL_CORE_0.1.md` §14 until the full §10 battery passes and GPT-5.6 rules on promotion.

The current battery is green, but "current battery green" is **not** the same as closure-proven. The status line is deliberately `IMPLEMENTED — CURRENT BATTERY GREEN / NOT YET CLOSURE-PROVEN / NOT FROZEN`.

| Commit | Scope | Status | Evidence |
|---|---|---|---|
| **0** | Freeze baseline evidence | **DONE** | `forge/admit_oracle.py`; `oracle_digest=2d6d50a0920f068a4de44860e16cc64feb3d28bbf8288ceeb51a4b3793d66f35`; run3k/3n/3o `PASS_REF_AND_NATIVE` |
| **1** | Parameterize the two D10 seams **only** | **DONE** | oracle transcript **byte-identical**; run3k/3n/3o/30/34 `PASS_REF_AND_NATIVE`; demo world still `sem-8ae91fe9…fe4a`, `identity_ok=True` |
| **2** | Tag-2 `Send` payload + three silent-failure guards | **DONE** | `--baseline` digest still `2d6d50a0…3f35`; guards witnessed; run3k/3n/3o/26/30/34 `PASS_REF_AND_NATIVE`; `sem-8ae91fe9…fe4a` unmoved |
| **3** | Additive IR surface (`MailboxDecl`, `RuntimeStateV1_1`) | **DONE** | `fixture.py` `mailboxes={id:(width,capacity)}`; `init_claimstate(fx)` sibling fields; D8 enforced (no edge may name a mailbox) |
| **4** | Configure the seams as `admit_mailbox_deliver_all_v1` | **DONE** | second `POLICIES` entry; reject-if-not-unique + ordered append; **no reducer fork** |
| **5** | Mailbox commit + ledger (`MailboxEnqueue`/`Deliver`/`Reject`) | **DONE** | `_roll_mailboxes` / `_commit_deliveries`; gated Film v0.7 mailbox block; `ledger_entries` |
| **6** | Full §10 battery + full pre-mailbox regression | **DONE** | `forge/binding_run43.py` 10.1–10.12 **`ALL PASS — PASS_REF_AND_NATIVE`**; oracle `--baseline` still `2d6d50a0…3f35`; run3k/3n/3o/7/26/30/34 green |
| **7** | The four GPT-5.6 rulings (Q1–Q4) | **DONE** | `admit.py` (Q3 registry arity enforced, Q4 capacity after resolution); `wrl_canonical.py`/`wrl_ir.py` (Q2 `Mailbox` role); `binding_run43.py` §10.11d + §10.13–§10.15; `binding_run4.py` probe corrected. **Both** oracle digests unmoved |
| **8** | The identity spine: policy/version wiring + production seam | **DONE** | `wrl_canonical.py` `semantic_surface_for_roles`; `wrl_plan.py` mailboxes through `CompilePlanV1`; `admit.py` schema-exact `init_claimstate`; `spinner_bench.py` runner reads the sealed policy; `binding_run43.py` §10.16–§10.18. **Both** oracle digests unmoved; mailbox world id moved (intended) |

**Aggregate evidence at Commit 8.**

| Gate | Result |
|---|---|
| §10 conformance battery (`binding_run43`, 10.1–10.18) | `ALL PASS — PASS_REF_AND_NATIVE`, 81 assertions |
| Frozen pre-`Send` oracle (`--baseline`) | `2d6d50a0920f068a4de44860e16cc64feb3d28bbf8288ceeb51a4b3793d66f35` — **unmoved** |
| Slice A oracle golden (full) | `5dbaeddcbed28c79f65d008b3a5f93dc0caffdfa37efffde51c2fb117d84ef77` — **unmoved by Commit 8** |
| Demo world identity | `sem-8ae91fe9…fe4a`, `identity_ok=True` — **unmoved** |
| Mailbox-bearing world identity | `sem-3de1dc5f8cd9eea4640a40437a031bc247c0a1c4d305f7845ad756175ae873c2` — **moved from the provisional Revision D value, intentionally** |
| Mailbox-free twin world identity | `sem-972188ab394d8911fdd6187b7291c34e7a4c744bbe7adf09c4d9dcbab22999a5` |
| Mailbox `CompilePlanDigest` | `plan-565fcaf7f69fbd289fd139e73e8ae148db100c72c317274226772f12c9541f63` |
| Regression sweep | run4/5/7/3k/3n/3o/8/26/30/34/37/41/42 all green |

**Why the mailbox world id moved, and why nothing else did.** Its artifact now names `admit_mailbox_deliver_all_v1`, `film.v0.7.mailbox.v1`, `ir_version 1.1` and `RuntimeStateV1_1` — four fields that are *inside* the `SemanticArtifactID` and were previously wrong. The Revision D value `sem-d7708903…1468` identified an artifact that claimed the mailbox-free semantics while executing mailbox semantics; it should not be preserved. All four fields are now derived from **one** function over the roles present, so they cannot drift apart again.

**Three pre-existing failures, unchanged by this work and NOT caused by it.** All were confirmed to fail identically at `HEAD` with the Slice A changes stashed:

| Battery | Symptom | Status |
|---|---|---|
| `binding_run6` | `AssertionError: claim batches differ` at `binding_run6.py:83` (`v2_canvas_to_text`) | pre-existing |
| `binding_run9` | `L1` (`parse_wrl_core(format(graph)) == graph`) and `L8` (run inputs survive format→parse) | pre-existing; **newly surveyed** — earlier sweeps did not include this battery, so Revision D's "two pre-existing failures" undercounted |
| `binding_run15` | 2 `FAIL` lines (S9) | pre-existing; count identical before and after |

`run6` and `run9` are both **text round-trip** failures involving run inputs surviving a format/parse cycle. They are plausibly one root cause — the v0.5-0 source-surface closure removed run inputs from the world source — but that has not been proven and is not part of Slice A.

### Commit 3 — the additive IR surface

`MailboxDecl` lands on `Fixture` as `mailboxes={mailbox_id: (width, capacity)}` — additive and defaulted, so every pre-v1.1 fixture is byte-for-byte unchanged. Validation enforces `0 < width ≤ 32`, `capacity ≥ 1`, role-id uniqueness against the five existing roles, and **D8**: no structural edge or socket may reference a mailbox. `kinds()` reports `"mailbox"`.

`init_claimstate(fx)` adds the two D6 sibling fields — `mailbox_states` and `mailbox_capacity_fault` — and pre-declares one state record per declared mailbox. Called with no fixture (every pre-Slice-A call site) the mailbox plane is empty and inert.

### Commit 4 — the second policy, no reducer fork

`admit_mailbox_deliver_all_v1` is a second `POLICIES` entry configuring the **same two seams**:

- **Seam 1** `_resolve_candidates_unique` — reject if the event key has more than one candidate (`equivocal_send`), rather than taking the canonical minimum.
- **Seam 2** `_accumulate_ordered_append` — append every accepted `Send` to the delivery list rather than collapsing keyed on mailbox.

The accumulator is a uniform 3-tuple `(cfg_map, resets, deliveries)` under **both** policies, so the reducer never learns an accumulator's shape. Control kinds keep their frozen v0.6 collapse semantics under both. The genuine difference is exactly the one §6 names: keyed collapse keeps one message per mailbox per epoch, ordered append keeps all — and under the frozen default that collapse is deliberately **not** a silent drop.

### Commit 5 — commit, capacity, ledger

`_roll_mailboxes` runs at the **top** of `admit_step`, before OBSERVE, and implements D7's lifetime law literally:

```
inbox' = admitted(next_inbox)        next_inbox' = []
```

REPLACED, not appended — the same `cur/next` idiom the v0.6 film already uses for relays and doors. Because it is the epoch boundary it runs regardless of what the batch does, *including* when a capacity latch aborts the batch.

`_commit_deliveries` is MAP's mailbox stage and implements D9's second stage: canonically order, test mailbox capacity, append **all or none**. The atomicity is across the *whole epoch* — if any one mailbox would overflow, the latch is set and nothing is delivered anywhere, including to mailboxes that had room. Correction 2's law governs unchanged: never evict, never partially apply.

Film v0.7 gained a **gated** mailbox block (`admit_mailbox:`, `mailbox:<id>:`, `ledger:`), emitted only when the world declares a mailbox, so every pre-v1.1 film is byte-identical. Ledger entries live in `ledger_entries` (D11), never in `world_frame`.

### Commit 6 — the battery, and three findings

`forge/binding_run43.py` executes §10.1–§10.12; the row numbering *is* the spec numbering. Three findings were recorded while making the clauses executable:

1. **§10.6's qualifier is load-bearing and is satisfied exactly, not loosely.** The frozen `canon_payload` hashes the raw target name, so the reduced digest **does** retain it — identically for `SetRotor "zz1"` vs `"zz2"`, which is pre-Slice-A behaviour this work did not touch. Two sends to two *different* unknown mailboxes are therefore genuinely different claims. What the sentinel discipline normalizes is the **rendered target** and the **payload key**; the films agree on every line except the policy-retained digest. The battery asserts precisely that, and asserts that the *only* diverging lines are `claim:` and `receipt:`.
2. **Declaring a mailbox advances the compiler's gensym counter**, so the emitted backend term is alpha-*equivalent* but not byte-equal to the mailbox-free world's. This is exactly what `wrl_plan._canonicalize_term` (D26) exists for: the battery states the "adds nothing physical" claim over the alpha-canonical form, and separately asserts that `_backend_content_hash` is **identical** across the two worlds. No identity moves.
3. **`_op_outcome`'s `unknown_kind` fallback is still live and still correct** — it returns `("Rejected","unknown_kind")` rather than raising. Guard 1 is not "unknown kinds raise"; it is "a `Send` must not *reach* that fallback". The battery asserts both halves.

**§10.12 is gated compositionally.** This was Revision C's one interpretive clause; it has since been **ruled** — see below.

### Rulings received — GPT-5.6, 2026-07-24

All four Revision C open questions were ruled. Commit 7 implements them. Nothing below is an interpretation.

**Q1 — §10.12 native fold scope. → ACCEPT the compositional argument. Do NOT add an IC mailbox construct for Slice A.**

The compositional reference/native conformance argument satisfies §10.12. Per **D8** a mailbox has no structural port and no structural edge, so it contributes nothing physical; gating the physical half natively and the mailbox plane by golden reducer plus film parity **is** the sanctioned conformance argument for Slice A. The standing order stands: no new IC runtime construct. §10.12 is restated compositionally below.

**Q2 — `MailboxDecl` in the canonical Semantic IR. → ADD it before freezing. Full WRL `~~` emission remains Slice B.**

`MailboxDecl` is now a sanctioned member of the canonical Semantic IR: `Mailbox` is the sixth entry of `ROLE_IDS`, carries `{w, cap}`, validates `w > 0` and `cap >= 1`, and — per D8 — declares **empty ports**, so any attempt to wire a mailbox fails structurally with `WRL_ILLEGAL_PORT_PAIR`. A mailbox-bearing world therefore earns a genuine `SemanticArtifactID` and declares `RuntimeStateV1_1`. **This is strictly additive:** the frozen demo world still seals `sem-8ae91fe9…fe4a` with `identity_ok=True`. Emitting `~~` from WRL *text* remains Slice B.

**Q3 — `empty_accumulator` as a third registry key. → REMOVE it. The common reducer owns the fixed accumulator seed.**

`POLICY_OPERATIONS` is now exactly `("resolve_candidates", "accumulate_map")`, and `get_policy` **enforces that arity**, so "exactly two policy operations" is true by inspection rather than by convention. The reducer seeds every fold with its own `_empty_control_accumulator()`.

**Q4 — receipt-capacity pre-check placement. → MOVE capacity checking after pure candidate resolution.**

Rejected event keys must not reserve receipts that can never exist. Every event key is now resolved **first** — `resolve_candidates` is pure, so this is safe on state that may yet be rolled back — and capacity is then tested against the keys that actually mint a receipt. Atomicity is unchanged: if the bound is exceeded the entire ACCEPT stage is abandoned, emitting neither receipts **nor** `MailboxReject` entries (§10.13).

The baseline oracle digest is unmoved by Q4, because `admit_candidate_min_firstreceipt_v1` never rejects; the change is observable only under the mailbox policy, which is exactly its intent.

### Commit 7 — the rulings

Q3 and Q4 in `forge/admit.py`; Q2 in `forge/wrl_canonical.py` and `forge/wrl_ir.py`; Q1 as documentation only (the implementation was already what was ruled). `binding_run43` gains §10.11d and rows §10.13–§10.15, covering the six pre-freeze additions the ruling required.

One collateral fix: `binding_run4`'s registry-closure probe used `Mailbox` as its "role not in the registry" example, so after Q2 it would have passed for the wrong reason. It now probes `Portal` and additionally asserts positively that a well-formed `Mailbox` **is** admitted with `RuntimeStateV1_1`.

**Promotion status.** `~~` remains *Reserved/partial* in `WRL_CORE_0.1.md` §14. It is **not** promoted to Grounded, and must not be until Q1 (and, if ruled in scope, Q2) are resolved.

### Commit 0 — the oracle

The battery scripts are a strong *semantic* gate but a weak *textual* oracle: their stdout embeds wall-clock timings, so byte-comparing them across a refactor is unsound. `forge/admit_oracle.py` is the strict oracle instead — a pure, timing-free fold over `admit_step` plus the Film v0.7 claim projection across 24 scenarios, with an executable permutation-invariance law (Correction 2) and a quarantined `MAX_EVENTS` override.

Two findings recorded during Commit 0:

1. **`receipt_capacity_fault` is structurally unreachable** at `MAX_FACTS == MAX_EVENTS == 6`, because every event key requires at least one fact, so `needed ≤ len(facts) ≤ MAX_FACTS == MAX_EVENTS`. The branch is live code, so the oracle exercises it under an explicit, always-restored override. **This matters for D9:** the two-stage capacity model must not assume the receipt stage is ever the binding constraint.
2. **Correction 1 is load-bearing and now directly witnessed.** `SetRotor spa (0,0,14,0)` and `SetRotor spa (0,1,3,0)` genuinely collide at `WD=8` (both `0x94`). The oracle pins that they remain **two** facts reading `disputed`, and that the `payload_key` tie-break is arrival-order independent.

### Commit 1 — what actually changed

19 lines removed, ~121 added (mostly the normative comment block). The reducer now calls:

```
SEAM 1   policy["resolve_candidates"](event_key, candidates)
             → ("Accepted", candidate) | ("Rejected", reason, evidence)
SEAM 2   policy["accumulate_map"](accumulator, accepted_operation)
```

with `POLICIES[admit_candidate_min_firstreceipt_v1]` bound to *canonical minimum* + *keyed collapse*, reproducing pre-Slice-A behaviour exactly. `admit_step` gained a trailing `policy_id=None`; all 30+ existing call sites pass four positional arguments and are untouched.

Three implementation notes were flagged for GPT-5.6 here. **Two were subsequently ruled against and have been superseded by Commit 7** — they are kept below only so the ledger records what was actually built at Commit 1 and why it changed.

- ~~**`empty_accumulator` is registered beside the two ruled operations.**~~ The argument was that a fold needs a seed and a step, and the seed is the identity element determined by the step's own type. **Ruled Q3: removed.** The registry is exactly the two ruled operations and `get_policy` enforces that; the reducer owns a fixed seed.
- ~~**The receipt-capacity pre-check is deliberately conservative.**~~ It reserved one slot per event key *needing resolution*, before Seam 1 ran. **Ruled Q4: moved.** Rejected keys must not reserve receipts that can never exist, so capacity is now tested after pure resolution, against the keys that actually mint one.
- **The Rejected branch `continue`s with no ledger entry at this commit.** *(Stands.)* Per §6 the equivocal event key correctly mints no receipt, no delivery, and retains all facts; the single canonical `MailboxReject` entry is Commit 5's work, and the frozen default policy never takes this branch.

### Commit 2 — tag 2 and the three guards

`Send` is now a real payload kind at tag 2, threaded through `canon_payload`, `payload_key`, `_op_outcome`, `_payload_str` and the Film v0.7 projection. New helper `admit.mailboxes_of(fx)` reads `{mailbox_id: (width, capacity)}` off the fixture and **returns empty when the attribute is absent** — so before `MailboxDecl` exists (Commit 3) every `Send` target is unknown and is Rejected `unknown_mailbox`, never silently Applied.

The oracle grew a `--baseline` mode that emits only the original 24 pre-`Send` scenarios, so the frozen Commit 0/1 digest stays verifiable forever. It is asserted on **every** run against `BASELINE_DIGEST`; the oracle fails loudly if pre-`Send` behaviour ever moves.

All three §6 silent-failure extension points are now closed and directly witnessed:

| Guard | Failure it prevents | Witness |
|---|---|---|
| 1. `_op_outcome` Send branch | Fallthrough to `("Rejected","unknown_kind")` would reject **every** send and no delivery would ever occur — a total behavioural failure that never raises | `guard1 _op_outcome(Send) -> Rejected(unknown_mailbox)`, `is_unknown_kind_fallback=False` |
| 2. `_payload_str` explicit dispatch | The unguarded `else` did `ob = p[1]`, so a `Send` would render as a **ResetFault** in Film v0.7 — a film-correctness defect that never crashes | `guard2 ... -> Send:mb0:1.0.0.0`, `unknown_kind_raises=True` |
| 3. `INVALID_TARGET` extends to mailbox ids | `payload_key` already packs an unknown target to sentinel index `len(targets)`; if the rendering did not match, two films identical up to a non-authoritative name would falsely diverge | `guard3 ... -> Send:#?:1.0.0.0`, `sentinel_index=0 == n_mailboxes=0` |

Tag additivity confirmed: `SetRotor=0 ResetFault=1 Send=2`. `film_bytes_v7` gained a trailing `mailboxes=None`; every caller passes seven positional args plus `state=`, so all are unaffected. `spinner_bench._admit_projection` now passes the declared mailbox set rather than `None`, so the sentinel discipline holds identically in the Film panel and in the film.

---

## 0. Why v1 cannot express a mailbox today

**Gap 1 — no sequence-valued state.** Relay state is `cur_out`/`next_out`; Door is `open`/`next_open` — boolean signal state, no payload. Spinner `rotor` and Orb `pose4` are fixed-width numerics. Nothing in `RuntimeStateV1` is a sequence with per-element identity **except `claim_facts` / `acceptance_receipts`**. There is no queue to compose a queue from.

**Gap 2 — direction.** Claims enter from outside as `EpochInputV1`. A mailbox requires sends generated during `REACT`, from inside the world. No v1 construct lets a node emit a claim. This is a change to dataflow **shape**, not vocabulary.

Gap 1 is solved by borrowing ADMIT's machinery (§1). Gap 2 splits: its **structural** half is closed by D8; its **behavioral** half is deferred to Slice B (§8).

---

## 1. What is already sufficient (no delta required)

| Requirement | Already frozen in v1 | Verdict |
|---|---|---|
| "Observable next period" | Relay `cur_out' = next_out`; Door `open' = next_open` | **Native idiom.** No temporal delta. |
| Deterministic message identity | `ClaimFactKey = (writer_id, sequence, digest, payload_key)` | **Reusable as-is.** |
| Canonical order independent of arrival | `CandidateKey`; *"worker arrival order is never semantic"* | **Reusable as-is.** Buys §12 scheduler invariance. |
| Bounded capacity, order-independent | Correction 2 atomicity: canonicalize+dedup, all-or-nothing, latch, *never evict, never partially apply* | **Reusable pattern.** |
| Pluggable acceptance policy | `admit_policy_id ; e.g. admit_candidate_min_firstreceipt_v1` | **Extension point exists.** |
| Evidence surface | `EpochResultV1.ledger_entries` (EventLedger / Film v0.7) | **Correct home exists.** |

**Consequence.** No new temporal, ordering, identity, or capacity machinery is required. What is required is a place to put messages and a MAP accumulator that does not collapse them.

---

## 2. D6 — Mailbox state is a SIBLING field *(ACCEPTED)*

Add `mailbox_states` and `mailbox_capacity_fault` as new sibling fields. Do **not** store messages in `claim_facts`.

v1 §6 reserves **v2** for *"any change to the meaning of an existing field"* and warns *"a second implementation must NOT silently reinterpret v1 fields."*

> **Borrow: identity, canonicalization, deduplication, capacity discipline, policy structure.
> Do not borrow: `claim_facts` storage, `acceptance_receipts` storage, existing field meanings.**

**Schema naming — ruled.** `ForgeSemanticArtifactV1.schemas` carries `runtime_state_schema` as a **referenced schema id inside the artifact**. Adding fields therefore requires a new schema id, which changes the artifact, which moves the `SemanticArtifactID`. The schema is exact, not a family. Introduce **`RuntimeStateV1_1`**; do not silently widen `RuntimeStateV1`.

```
RuntimeStateV1_1 {
    ... all RuntimeStateV1 fields unchanged ...
    mailbox_states            ; NEW — per-mailbox { inbox, next_inbox }
    mailbox_capacity_fault    ; NEW — sibling of fact_/receipt_capacity_fault
}
```

### The in-memory shape must be exact too *(Commit 8)*

"Do not silently widen `RuntimeStateV1`" is a claim about the **running state**, not only about the schema id. Revision D honored it in the artifact and broke it in memory twice over:

1. `init_claimstate()` unconditionally returned `mailbox_states` and `mailbox_capacity_fault`, so *every* world's state carried the v1.1 siblings regardless of what its artifact declared;
2. `_mailbox_states` used `setdefault` unconditionally, so merely **stepping** a mailbox-free world installed an empty `mailbox_states` — a world could be promoted to v1.1 shape by having been run.

Both are corrected. The rule:

> **The schema a state satisfies is decided by the artifact, not by the state having been constructed or run.**

- A world declaring no mailbox inits **exactly** `RuntimeStateV1` — the siblings are *absent*, not empty.
- Declaring a `Mailbox` is what adds them, pre-populated per declared mailbox; no mailbox materializes on demand.
- Stepping never changes which schema a state satisfies.

`ledger_entries` stays in the base shape deliberately: D6 named exactly two new sibling fields, and the ledger predates the mailbox roles that write to it, so gating it would *change* `RuntimeStateV1` rather than preserve it.

§10.17 asserts both directions — the artifact's declared `runtime_state_schema`, the shape the runner builds from the plan view, and the shape `lower_graph` puts in `initial_claim_state` must all agree.

---

## 3. D7 — `MailboxDecl`, a sixth built-in role *(ACCEPTED + lifetime law)*

v1 §1: *"New built-in roles are **additive v1.x**."*

```
MailboxDecl
    static_config : capacity (bounded, ≥ 1)
    ports         : none structural (see D8)
    state         : inbox, next_inbox
    invariant     : inbox' = admitted(next_inbox) ; next_inbox' = []
```

**Lifetime law (frozen):**

> **Mailbox `inbox` is the canonically ordered delivery batch observable during exactly one logical period. It is REPLACED, not appended, at the next commit. A message delivered in period *k+1* is gone at the following commit whether or not anything observed it. Persistence requires explicit promotion into another state form.**

Without this, a second implementation could build a conventional persistent queue and still believe it conforms. Replace-not-append keeps the mailbox analogous to Relay (`cur_out' = next_out`) and keeps state bounded.

### Canonical IR surface *(ruling Q2)*

`Mailbox` is the sixth entry of the closed `ROLE_IDS` tuple in `wrl_canonical.py`:

```
ROLE_IDS = ("Pulser", "Relay", "Door", "Spinner", "Orb", "Mailbox")

Mailbox
    surface / static_config keys : w, cap
    validation                   : 1 <= w <= MAILBOX_WIDTH_MAX (32)
                                              → WRL_NUMERIC_RANGE
                                   cap >= 1   → WRL_NUMERIC_RANGE
    ports                        : {"out": (), "in": ()}
```

**The width bound is one number in one place** *(Commit 8)*. Revision D let the canonical validator accept any `w > 0` while the Fixture oracle enforced `0 < w <= 32`. An artifact with `w = 33` could therefore seal, earn a `SemanticArtifactID`, and only then fail to lower to the oracle — an identity minted for a world that cannot run. Both surfaces now read `WC.MAILBOX_WIDTH_MAX`, and the bound is inclusive at both ends (§10.18).

The empty port sets are how **D8 is enforced structurally rather than by a special case**: edge validation is entirely port-driven, so any attempt to wire a mailbox already fails with `WRL_ILLEGAL_PORT_PAIR` without a single mailbox-aware branch in the edge checker.

A world declaring a mailbox must declare the D6 runtime schema, and this is derived from the roles present rather than asserted:

```
schemas_for_roles(roles) = SCHEMA_IDS_V1_1  if "Mailbox" in roles
                           SCHEMA_IDS       otherwise
```

**This is strictly additive.** Adding the sixth role moves no pre-existing identity: the frozen demo world still seals `sem-8ae91fe9…fe4a` with `identity_ok=True` (§10.11d).

### The mailbox in `CompilePlanV1` *(Commit 8)*

Revision D left the mailbox out of `CompilePlanV1` on the reasoning that a mailbox is not physical (D8) and the plan is the backend-neutral lowering contract. That reasoning was **wrong**, and the failure is structural rather than aesthetic.

`seal_compile_plan` binds a plan to its artifact by *reconstructing* the IR from the plan (`_plan_to_artifact`) and re-hashing it. A plan that drops the `MailboxDecl`s reconstructs a **different world**, so it can never reproduce the `SemanticArtifactID` it claims. Under Revision D a mailbox artifact therefore **could not be sealed as a compile plan at all**, and consequently could not reach the production compile/run path. The battery never noticed because it drove the reducer directly.

The plan now carries the declarations, in a shape that states D8 rather than assuming it:

```
plan["mailboxes"] = [{"id": …, "w": …, "cap": …}, …]      canonically sorted
```

- **Declared, but not physical.** Mailboxes are absent from `object_order` / `object_index` and from all three neutral plan signatures. A mailbox id may not collide with a physical object id.
- **Provably ignored by the backend.** `compile_step_v6` never reads the field. Against the mailbox-free twin, §10.16 asserts the object index, all three neutral signatures, the `backend_layout_signature` and the `_backend_content_hash` are **identical**, while the `SemanticArtifactID` and the `CompilePlanDigest` differ.
- **Inside the identity.** Deleting one `MailboxDecl` from a plan that keeps its claimed id is caught as `WRL_BAD_COMPILE_PLAN` — *"plan is not bound to its semantic artifact"*.

This is a **stronger** statement of D8 than omission. An omitted declaration makes "the mailbox contributes nothing physical" unfalsifiable at the plan layer; a declaration the compiler demonstrably ignores makes it a measurement.

`CompilePlanDigest` values move for **every** world as a result, since the plan gained a field. That digest is documented as test-only and is never pinned as a literal; no runtime id and no film depends on it.

### The runner selects the semantics the artifact names *(Commit 8)*

`_PlanView` — the object the runner hands to `admit_step` — now carries both `mailboxes` (duck-typing the Fixture's own attribute, so `admit.mailboxes_of` reads either through one accessor) and `admit_policy_id`. `spinner_bench` passes `policy_id=view.admit_policy_id` and seeds state with `init_claimstate(view)`.

Both facts arrive from **one object with one provenance**, the sealed artifact. Revision D's runner called `init_claimstate()` with no argument and `admit_step` with no `policy_id`, so a sealed mailbox world would have executed the mailbox-free policy against un-declared mailbox state.

---

## 4. D8 — Logical targeting by `mailbox_id`; NO new edge kind *(ACCEPTED)*

A mailbox has **no structural port and no structural edge**. Sends are payloads addressed to a `mailbox_id`.

v1 §2 (D2) froze *exactly two* structural edges and ruled async/verified/fault are *"transition-class reserved, **not edges**."* A third edge kind is forbidden. `SignalWireDecl` could not carry a message regardless — it carries a bit (`or-merge of incoming .nxt`).

The precedent is already in v1: **ADMIT control targeting has no structural edge either.** `SetRotor` names a spinner by id; `ResetFault` names an orb by id. `Send` names a mailbox by id, by identical discipline. Mailbox topology is **logical**, not structural.

> **This closes the structural direction problem without adding an edge kind. The behavioral emission gap remains deferred until Slice B.**

---

## 5. D9 — `Send` at tag 2; two-stage capacity *(ACCEPTED)*

`admit.payload_key` is a **length-6 fixture-scoped tuple** with kind tags `0` (SetRotor) and `1` (ResetFault). Tag `2` is free:

```
canon_payload:   "Send|" + mailbox_id + "|" + body_encoding
payload_key:     (2, mailbox_index, b0, b1, b2, b3)
```

Both existing encodings untouched → additive. Body bounded to 4 lanes **in the proof profile only**, consistent with `MAX_FACTS=6` / `MAX_BATCH=4` and with the existing note that *"the production bridge uses full canonical payload bytes after the full digest; this proof profile is collision-free by construction."*

### Two-stage capacity model (frozen for Slice A)

The earlier draft conflated two capacities operating at **different phases over different semantic sets**. This is not an exception to atomicity — it is two separate atomic capacities.

| Capacity | Set being bounded | Counts equivocating candidates? |
|---|---|---|
| `fact_capacity_fault` | Monotone evidence retained for future derivation | **YES** |
| `mailbox_capacity_fault` | Valid deliveries observable next period | **NO** |

**Normative pipeline:**

```
OBSERVE
    canonicalize incoming facts
    → deduplicate exact ClaimFactKeys
    → test FACT capacity over all new distinct facts
    → store all or none

RECOGNIZE / ACCEPT
    group stored facts by (writer_id, sequence)
    → derive disputed groups
    → reject equivocations
    → retain one accepted candidate per surviving event key

MAP
    canonically order accepted deliveries
    → test MAILBOX capacity
    → append all or none
```

**Why fact capacity must count equivocations.** Fact capacity is tested at OBSERVE, *before* recognition. The claim fact set is monotone and stores every distinct candidate including losers. `recognition()` derives `"disputed"` from `len(_candidates(...)) > 1`, and recognition is *never stored*. Removing equivocations before fact-capacity accounting would erase the basis of the dispute.

---

## 6. D10 — `admit_mailbox_deliver_all_v1` *(ACCEPTED; two seams)*

**Policy definition (normative wording — prevents misreading "deliver all"):**

> **Deliver every accepted event key exactly once; never deliver more than one candidate for an event key.**

After equivocation rejection every surviving event key holds exactly one accepted candidate. The mailbox is "deliver all" *across the set of surviving event keys*, never across candidates within one key.

### The real distinction is accumulator shape, not acceptance discipline

| Policy | MAP accumulator | Property |
|---|---|---|
| `admit_candidate_min_firstreceipt_v1` | `cfg_map[target] = value` — later canonical assignment collapses earlier | **lossy by design** |
| `admit_mailbox_deliver_all_v1` | `deliveries.append(message)` — no accepted event key collapsed | **lossless** |

### Sanctioned parameterization — two policy operations, no fork

Do not scatter mailbox conditionals through the reducer. The common reducer exposes exactly two policy operations:

```
resolve_candidates(event_key, candidates)
    → Accepted(candidate)
    | Rejected(reason, evidence)

accumulate_map(accumulator, accepted_operation)
    → updated accumulator
```

```
admit_candidate_min_firstreceipt_v1:
    resolve_candidates = canonical minimum          ; admit.py ~line 218
    accumulate_map     = keyed collapse             ; admit.py ~lines 232–243

admit_mailbox_deliver_all_v1:
    resolve_candidates = reject if count != 1
    accumulate_map     = ordered append
```

**The common reducer retains ownership of:** grouping · exact-fact deduplication · canonical ordering · fact capacity · receipt capacity · receipt creation · ledger emission · **the accumulator seed** · atomic commit behavior.

**The policy chooses only:** (1) how one event key resolves; (2) how accepted operations accumulate.

Seam 1 is a genuine ACCEPT-policy variation — `cands[0]` cannot be reused unchanged, because it would silently choose a winner from an equivocal mailbox send.

**Registry arity is enforced, not conventional (ruling Q3).** `POLICY_OPERATIONS` is exactly the two names above and `get_policy` rejects any policy whose key set differs. There is no `empty_accumulator` key; the reducer owns a fixed seed.

**Seam 1 must be pure (ruling Q4).** Because capacity is now tested *after* resolution, `resolve_candidates` runs on state that may yet be rolled back. It must not mutate state, emit ledger entries, or depend on call order.

### Equivocal event key — frozen behavior

```
acceptance receipt : none
delivery           : none
MailboxReject      : exactly ONE canonical rejection entry,
                     per unresolved key, PER RESOLUTION EPOCH
stored claim facts : all distinct candidates retained
```

`MailboxReject` refers to the **event key and the canonically ordered candidate identities**. It must **not** emit one rejection per arrival — that would make the film sensitive to transport multiplicity.

**"Per resolution epoch" is exact and is not a redundant-re-emission defect.** An unresolved key mints no receipt, so it is still in `needed` on the following epoch and is resolved — and rejected — again. One entry per epoch is therefore the correct and intended reading: the ledger records that the dispute *was still unresolved at that epoch*, not merely that it once occurred. Two consequences follow, and both are asserted in §10.14–§10.15:

- **Multiplicity within an epoch collapses; recurrence across epochs does not.** Four arrivals of the same disputed key in one epoch yield exactly one entry; the same dispute standing for three epochs yields exactly one entry *each* epoch.
- **A settled key emits nothing.** Once a key holds a receipt it leaves `needed`, so a candidate arriving *later* flips recognition to `disputed` and is retained as evidence, but emits **no** `MailboxReject` — and never retracts the delivery the first receipt already authorised.

### Three extension points that fail silently

Promoted to required conformance tests (§10.4–10.7). Each can fail without crashing:

1. **`_op_outcome`** returns `("Rejected", "unknown_kind")` for unrecognised kinds → without a `Send` branch, every send is Rejected and no delivery ever occurs.
2. **`_payload_str` has an unguarded `else`** (`ob = p[1]` assumes ResetFault) → a `Send` renders as a ResetFault in the Film v0.7 projection. A silent film-correctness defect, not a crash.
3. **`payload_key` is fixture-scoped** and needs a mailbox index; the `INVALID_TARGET = "#?"` sentinel discipline must extend to unknown mailbox ids, or *"two films that are identical up to a non-authoritative name would falsely diverge."*

---

## 7. D11 — Ledger events; three distinct identity comparisons *(ACCEPTED)*

```
ledger_entries += MailboxEnqueue | MailboxDeliver | MailboxReject
```

Events belong in `ledger_entries` (EventLedger, claim-aware, Film v0.7), **not** `world_frame` (WorldFrame, physical, Film v0.6). Per WRL §8b the EventLedger is the home for *"accepted events, receipts, effects, outcomes."*

v1 §3 supplies the hash inputs:

```
BackendArtifactID = hash( SemanticArtifactID + lowering profile + compiler hash + backend representation )
```

Three separate comparisons — **three battery fixtures, never one overloaded identity test**:

| Operation | SemanticArtifactID | BackendArtifactID |
|---|---|---|
| Relocate unchanged artifact across thread / process / host | unchanged | unchanged |
| Revise compiler to support mailbox lowering | unchanged | **moves** (incorporates `compiler hash`) |
| Add mailbox schema + film semantics | **moves** | moves |

Relocation, backend revision, and semantic revision are distinct operations and must not be conflated.

---

## 8. Staging — Slice A before Slice B

**Slice A — mailbox as delivery buffer. Sends arrive only via `EpochInputV1`.**
Grounds `~~`'s temporal semantics with **zero** node behavior. Requires D6, D7, D9, D10, D11. Structural direction closed by D8; behavioral emission deferred. Still fully deterministic; still a circuit world with one buffered relation.

**Slice B — node-generated sends.** A minimal deterministic emitter (clock-driven, static target and payload, in the spirit of `PulserDecl`'s *"never data-dependent"* invariant) emits during REACT into `next_inbox`. Closes the behavioral half of Gap 2 without opening the general actor-behavior system.

### `~~` promotion status after Slice A

Slice A grounds mailbox storage, canonical admission, next-period visibility, capacity behaviour, rejection evidence, and scheduler invariance under external sends. Per ruling Q2 it now **also** grounds `MailboxDecl` in the canonical Semantic IR, so a mailbox world earns a real `SemanticArtifactID`. It still does **not** ground the full WRL route, because no WRL node emits a `Send` during execution.

> **After Slice A: `~~` receiving and commit semantics implemented, and `MailboxDecl` is declarable in the canonical IR; end-to-end `~~` route lowering and WRL `~~` *emission* remain Experimental (Slice B).**

Declaring a mailbox is not the same as routing to one. Q2 moved the **declaration** into scope; it did not move **emission**.

Promotion from Reserved to Grounded in `WRL_CORE_0.1.md` waits until Slice B proves the whole chain:

```
WRL source ~~ → sanctioned IR Send → mailbox next_inbox
    → epoch commit → inbox delivery → canonical ledger events → byte-identical film
```

This protects the implement-then-freeze discipline of WRL §13.

---

## 9. Versioning — ruled

| Change | Class |
|---|---|
| `MailboxDecl` role | additive — v1 §1 authorizes new roles as v1.x |
| `Send` payload kind at tag 2 | additive — existing tags 0/1 untouched |
| `mailbox_states`, `mailbox_capacity_fault` | additive — new sibling fields, new `RuntimeStateV1_1` schema id |
| `admit_mailbox_deliver_all_v1` | additive — policy slot already pluggable |
| New ledger entry kinds | additive — moves SemanticArtifactID (correct) |
| New structural edge | **NOT PROPOSED** — D2 preserved (D8) |
| Reuse of `claim_facts` | **REJECTED** — would force v2 |
| Mailbox-specific reducer fork | **REJECTED** — parameterize the two seams (§6) |

```
Slice A:  profile_id = forge.world.core.v1   ir revision = v1.1
Slice B:  profile_id = forge.world.core.v1   ir revision = v1.1
          (provided the emitter remains static, bounded, deterministic)
Later general actor/mailbox system: reconsider forge.world.async.v1
```

### 9a. The unified role-derived semantic surface *(Commit 8)*

Four fields of a sealed artifact change together when a `Mailbox` is declared, and every one of them is **inside** the `SemanticArtifactID`:

| Field | mailbox-free | mailbox-bearing |
|---|---|---|
| `ir_version` | `1.0` | `1.1` |
| `schemas.runtime_state_schema` | `RuntimeStateV1` | `RuntimeStateV1_1` |
| `semantic_policies.admit_policy_id` | `admit_candidate_min_firstreceipt_v1` | `admit_mailbox_deliver_all_v1` |
| `semantic_policies.film_schema_id` | `film.v0.7` | `film.v0.7.mailbox.v1` |

Revision D derived only the second of these and hardcoded the rest, so a mailbox artifact *named* the mailbox-free semantics while the battery *executed* the mailbox semantics — the identity and the behavior disagreed, and nothing detected it.

They are now decided in exactly one place:

```python
WC.semantic_surface_for_roles(roles) -> {
    "ir_version", "runtime_state_schema", "admit_policy_id", "film_schema_id"
}
```

`schemas_for_roles` is *derived from* that selector rather than chosen beside it, so the runtime state schema cannot disagree with the admit policy. The rule is enforced in both directions:

- **Emission** — `graph_to_ir` and `_plan_to_artifact` both build their version/policy block from the selector, never from a module constant.
- **Validation** — `validate_artifact_v1` recomputes the selector from the artifact's *own* roles and rejects any mismatch (`WRL_MALFORMED_ARTIFACT` for `ir_version`/`schemas`, `WRL_UNSEALED_POLICY` for the two policy ids). A hand-built artifact naming the wrong policy for its roles cannot seal.

> **An artifact must name the semantics it executes.** This is the law Commit 8 adds; §10.16 and §10.17 are its witnesses.

The film schema id is now versioned too. A mailbox world's film carries a gated `admit_mailbox:` block, which is a genuine film-schema revision, so continuing to call it `film.v0.7` was a false claim about the observable surface.

### 9b. Deliberate non-change: `profile_id`

`profile_id` stays `forge.world.core.v1`. Commit 8 changes which *semantics* an artifact names, not the execution model, conformance relation, or semantic interpretation — none of §9's six sibling-profile triggers is crossed.

### Version-policy closing rule (adopted)

> **The IR version identifies compatible additive or breaking revisions within a semantic world family. `profile_id` changes only when the execution model, conformance relation, or semantic interpretation changes — not whenever a new additive role is grounded.**

A sibling profile becomes justified only on crossing one of: dynamic mailbox creation or topology · arbitrary data-dependent actor sends · unbounded message retention · nondeterministic receive selection · transport state becoming semantically observable · actor-local scheduling not reducible to the epoch transition · a different termination or conformance law.

---

## 10. Slice A conformance battery

**10.1 Scheduler invariance (WRL §12).** N permutations of the same send set → one byte-identical committed film.

**10.2 Mailbox capacity atomicity.** An overflowing delivery set, reversed, produces identical state: latch set, zero delivered.

**10.3 Equivocation visibility.** Conflicting `(writer_id, sequence)` → exactly one canonical `MailboxReject`; no receipt; no delivery. Rejection count is invariant under arrival multiplicity.

**10.4 Send outcome coverage** *(guards the `_op_outcome` unknown-kind fallback)*
```
valid Send to known mailbox
    → Accepted
    → MailboxEnqueue
    → next-period MailboxDeliver
```

**10.5 Film payload discrimination** *(guards the unguarded `else` in `_payload_str`)*
```
_payload_str(Send(...)) != _payload_str(ResetFault(...))
```
Also assert the exact canonical `Send` projection.

**10.6 Invalid mailbox normalization** *(guards the sentinel discipline)*
```
Send("unknown-a", body)
Send("unknown-b", body)
    → target "#?"
```
Semantic films must remain identical where the non-authoritative name is not retained by policy.

**10.7 Payload-key injectivity**
```
Send payload_key != any SetRotor payload_key
                 != any ResetFault payload_key
```
Distinct fixture mailbox indices remain injective for the proof profile.

**10.8 Temporal law.** A message enqueued in epoch *k* is observable in *k+1* and never in *k*.

**10.9 Inbox lifetime (D7).** An unobserved message delivered in *k+1* is absent at *k+2*. Replace, not append.

**10.10 Dispute retention (D9 — qualified per ruling).**
> When an equivocating pair fits within remaining fact capacity, both distinct candidates consume fact capacity and remain stored, and recognition derives `disputed`. Reversing their arrival order does not change the stored facts, fault state, recognition, or film.

The qualifier is required: if the incoming OBSERVE batch itself overflows fact capacity, Correction 2 requires inserting none. The system cannot derive a dispute from facts it atomically refused to observe. That is existing bounded-state behavior, not evidence loss after recognition.

**10.11 Identity — three separate fixtures (D11).** Relocation moves neither ID; compiler revision moves BackendArtifactID only; schema/film revision moves both.

**10.11d Identity over a REAL mailbox-bearing artifact (ruling Q2).** The three fixtures above are necessary but not sufficient, because Revision C could only run them over a mailbox-*free* artifact. With `MailboxDecl` in the canonical IR the battery must additionally prove, over a genuine mailbox world:

```
a Mailbox-bearing world earns its OWN SemanticArtifactID
    → sem-d7708903a962…
its runtime schema is RuntimeStateV1_1 iff a Mailbox is declared
Q2 is ADDITIVE: the frozen demo world is UNMOVED
    → sem-8ae91fe9…fe4a
relocation invariance still holds for a mailbox world
changing a MailboxDecl capacity MOVES the SemanticArtifactID
D8: a Mailbox carries no edge in the sealed artifact
the sealed artifact lowers back to the declarations
```

The additivity assertion is the load-bearing one: adding the sixth role must not perturb any pre-existing identity.

**10.12 Reference/native fold — compositional (ruled, Q1).** Slice A conformance is established **compositionally**, and this is the sanctioned argument, not a concession:

1. **Physical plane, natively.** `ic_ref == ic32 == oracle` over a mailbox world across a K-epoch trajectory, films byte-equal.
2. **Mailbox contributes nothing physical.** Declaring a mailbox leaves the encoded circuit state alpha-canonically identical and does **not** move `_backend_content_hash`. This is what makes (1) a complete account of the physical half — it discharges D8 dynamically rather than assuming it.
3. **Mailbox plane, by golden reducer + film parity.** The claim-and-mailbox plane is proved against the frozen oracle, and the D7 lifetime law is asserted across the trajectory.

Together these cover the whole state. Extending the in-calculus fold to `mailbox_states` would require **a new IC runtime construct** and is explicitly **out of scope for Slice A**.

**10.13 Mixed valid-plus-equivocal receipt capacity (ruling Q4).** In a batch mixing valid and equivocal event keys, capacity must bind on the keys that actually **mint a receipt**, never on keys merely *needing resolution*. Required: a fixture where `needed > MAX_EVENTS >= accepted`, proving (a) no latch, (b) every valid key mints a receipt and still delivers, (c) the equivocal key mints none and reads `disputed`, (d) capacity still binds when the *accepted* count exceeds the bound, and (e) an abandoned ACCEPT stage emits **no partial evidence** — no receipts, no enqueues, and no `MailboxReject`.

**10.14 Repeated unresolved equivocation.** A key left unresolved across successive epochs yields exactly **one** `MailboxReject` per epoch, each naming the key and its own epoch; never a receipt, never a delivery; both candidates retained throughout. Retransmitting an identical candidate adds no facts. Multiplicity *within* an epoch still collapses to one entry.

**10.15 Late equivocation after a receipt.** A conflicting candidate arriving *after* a key has settled must: flip recognition to `disputed`; leave the first receipt authoritative and unrewritten; be retained as evidence; emit **no** `MailboxReject`; and **not retract** the already-authorised delivery. The late candidate itself is never delivered. Under this policy the settled winner is the **first-seen** candidate, not the canonical minimum — the assertion must state which.

### Rows added at Commit 8

Rows 10.1–10.15 prove the mailbox **reducer**. They do not prove that the shipped runner *selects* the semantics they prove. These three rows close that gap.

**10.16 The production compile/run seam.** Drive a mailbox artifact through the path the runner actually uses:

```
sealed artifact → artifact_to_compile_plan_v1 → seal_compile_plan
               → plan_view → admit_step
```

Required: (a) a mailbox plan **seals** and re-binds to its `SemanticArtifactID` — this was impossible before Commit 8; (b) the plan view carries the declarations to ADMIT and **names the policy its artifact names**, with the mailbox-free twin naming the other one; (c) against that twin, the object index, all three neutral signatures, the `backend_layout_signature` and the `_backend_content_hash` are **identical** while the semantic id and plan digest **differ** (D8, measured rather than assumed); (d) no mailbox appears in `object_order`; (e) deleting a `MailboxDecl` from a plan that keeps its claimed id fails `WRL_BAD_COMPILE_PLAN`; (f) an end-to-end fold through the seam with **two sends to one mailbox plus an equivocal send** delivers both valid messages and rejects the equivocal key.

**10.17 Runtime schema exactness.** A mailbox-free world inits **exactly** `RuntimeStateV1` — the two D6 siblings absent, not empty. Declaring a `Mailbox` is what adds them, pre-declared. **Stepping** a mailbox-free world must not widen it. In both directions, the artifact's declared `runtime_state_schema`, the shape the runner builds from the plan view, and `lower_graph`'s `initial_claim_state` must agree.

**10.18 Mailbox width bound.** `w == 32` seals (inclusive); `w == 33`, `w == 0` and `cap == 0` are each a typed `WRL_NUMERIC_RANGE`; and the Fixture oracle admits exactly what the IR seals, so a sealed artifact can always lower.

---

## 11. Erratum against frozen v1 §7 — non-mutating

Do not edit the frozen artifact in place; publish as a non-semantic erratum preserving the original digest.

> **Erratum to §7 — production lowering path.** The production path is `Semantic IR → CompilePlanV1 → TRVM compiler`. The Fixture adapter is retained only as an oracle/testing bridge through `as_fixture_for_test`; it is not the production lowering contract. This corrects implementation drift and changes no frozen semantics.

---

## 12. What remains before FROZEN

1. **Closure proof.** "Current battery green" is not closure. §10 now has 18 rows and 81 assertions, but the row set has still not been shown *complete* over the D6–D11 surface.
2. **Three pre-existing red batteries** — `binding_run6`, `binding_run9`, `binding_run15`. None is mailbox-related; none should be inherited by Slice B.
3. **Slice B** — WRL `~~` emission, the half ruling Q2 explicitly left out.
4. **`~~` promotion** in `WRL_CORE_0.1.md` §14 — still *Reserved/partial*, still GPT-5.6's to rule.

### Open for ruling — one architectural reversal to confirm

Commit 8 **reverses** a Revision D decision: `CompilePlanV1` now carries `MailboxDecl`s. The reversal was forced by `seal_compile_plan`'s reconstruct-and-re-hash binding, not chosen — a mailbox artifact was unsealable without it (§4, "The mailbox in `CompilePlanV1`"). The alternative would have been to change how a plan binds to its artifact, replacing reconstruction with carried canonical bytes; that is a larger change to a mechanism frozen at Phase 3D.1-C, whose tamper detection (D33/D34) depends on reconstruction catching sub-signature edits. The chosen option preserves that mechanism and makes D8 measurable. **This is flagged rather than assumed ruled.**

---

*End of Revision E. Commits 0–8 implemented; §10.1–§10.18 green. Not closure-proven, not frozen.*
