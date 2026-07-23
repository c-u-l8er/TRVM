# TRVM Laws

The single index of TRVM's governance laws. Each law is a **retracted claim
converted into a permanent rule** — an invariant earned from a specific failure
and enforced by a specific battery.

This file has **two tiers plus a reserved state**, and the distinction is
load-bearing:

- **Tier A — CANONICAL.** Either real cited text exists in source, OR the
  architect has ratified a canonical statement by explicit ruling. The
  provenance line names which. Tier A laws are binding and may be cited.
- **Tier B — RECONSTRUCTED (NEEDS RATIFICATION).** No canonical statement of
  the law survives anywhere in the repo. The text below is a *reconstruction*
  from scattered commentary, OR the number itself is unattested. It is **not
  authoritative** until the architect ratifies it. Do NOT cite Tier B laws as
  binding authority in code.
- **RESERVED — canonical statement lost.** The ID is held but has no statement
  and no binding authority. A reserved law may **not** be cited and may **not**
  be reused for a new law. It can be restored only if real historical text is
  found, or a later architect explicitly assigns a new statement.

> Provenance rule (per repo policy — do not fabricate causal provenance):
> nothing may be promoted B→A by an agent. Only a human/architect ruling moves
> a law from RECONSTRUCTED to CANONICAL — either by locating real historical
> text, or by ratifying a canonical statement outright (recorded in an additive
> ratification file, e.g. `LAW_RATIFICATION_2026-07-22.md`).

---

## Series I — Binding Laws (semantics)

The binding line governs *meaning*: what a lowering may and may not change. It
is the authority `fixture.py` and `compiler.py` cite by number. As of the
round-11 review the `## Laws` section of `forge/FORGE_BINDING_RESULTS.md` states
only **"1–7 unchanged"** and gives text for **Law 5 alone**. Laws 1, 2, 3, and 7
have no recoverable canonical statement and are now **RESERVED**; Laws 4 and 6
were **ratified to Tier A by architect ruling** (see
`LAW_RATIFICATION_2026-07-22.md`).

### Law 1 — RESERVED — canonical statement lost
- **Status:** ID held, no statement, no binding authority. Attested only via
  "1–7 unchanged" (`forge/FORGE_BINDING_RESULTS.md:1562`). May not be cited or
  reused. Restorable only by real historical text or an explicit new ruling.

### Law 2 — RESERVED — canonical statement lost
- **Status:** ID held, no statement, no binding authority. May not be cited or
  reused.

### Law 3 — RESERVED — canonical statement lost
- **Status:** ID held, no statement, no binding authority. May not be cited or
  reused.

### Law 4 — CANONICAL (ratified 2026-07-22)
- **Statement:** *Every reported reduction cost must name the reduction strategy
  under which it was measured.* Eager/`first`, lazy-reference, or any later
  scheduler are different measurement regimes; an unlabeled step count is not an
  honest result.
- **Provenance:** architect ruling, `LAW_RATIFICATION_2026-07-22.md` (not a
  fabricated historical quote).
- **Cited by:** `forge/binding_run3.py:177`, `forge/binding_run3b.py:265`,
  `forge/binding_run3c.py:307` ("strategies named, per Law 4").
- **Enforced by:** the strategy-sample / `cost_report` blocks in those three
  binding runs (min/max step counts reported under a named strategy).

### Law 5 — CANONICAL
- **Statement:** *A numeric threshold may change representation, never meaning.*
  Round-11 sharpening: *two numeric policies are two meanings — an encoding may
  not switch between them silently; a policy change is an explicit act with a
  measured separator.*
- **Failure that earned it:** the period-33 horizon bug — a period-33 clock
  compiled as a saturating one-shot, diverging from the model at t = 33.
- **Cited by:** `forge/fixture.py:5-6`, `forge/compiler.py:6`,
  `FORGE_SEMANTIC_IR_v1_MEASURE.md:29,84,85`, `forge/MANIFEST.md:76`,
  `WRL.md:1108`.
- **Canonical text:** `forge/FORGE_BINDING_RESULTS.md:1562-1564`.
- **Enforced by:** `forge/binding_run3.py` (period-33 regression); one-hot vs
  binary counter equivalence across the compiler batteries.

### Law 6 — CANONICAL (ratified 2026-07-22, now GLOBAL)
- **Statement:** *A canonical shared observable must carry every state variable
  that can determine future behavior; if two states can lead to different
  futures, their Film bytes must differ.* This unifies all surviving witnesses:
  different rotor state; different receipt state; different one-shot/done-latch
  state; and any other hidden state that changes a future transition. The law is
  now **global**, not horizon-scoped — the later native Once work closed that
  temporary limitation.
- **Provenance:** architect ruling, `LAW_RATIFICATION_2026-07-22.md` (not a
  fabricated historical quote).
- **Witnesses:** `forge/FORGE_BINDING_RESULTS.md:989` ("Law 6 witness"),
  `:1548`, `forge/MANIFEST.md:69,70`, `forge/E2_RESULTS.md:50`,
  `forge/CHANGED_3b5f1_admit.md:43`.
- **Enforced by:** `forge/binding_run3k.py:32,313,325` and
  `forge/binding_run3h.py:21,285` (hidden-state → Film v0.7 divergence witness).

### Law 7 — RESERVED — canonical statement lost
- **Status:** ID held, no statement, no binding authority. Attested only via
  "1–7 unchanged." May not be cited or reused.

---

## Series II — Distribution / Autonomous Laws (epistemics)

The distribution line governs *how measurement and autonomy are conducted* — not
what things mean, but how not to fool yourself about them. WARNING: unlike the
binding line, these are **largely unnumbered in the source.** Only Laws 10, 13,
23 (referenced), and 26 carry actual numbers in-repo. The "laws 20–25"
enumeration that appears in review commentary is a *paraphrase*, not attested
numbering. Every unnumbered entry below is Tier B until ratified.

### Law 10 — CANONICAL
- **Statement:** there is NO central level controller; each node owns its own
  level (reviewer-specified decentralization).
- **Cited by / text:** `research/synth_async.py:8`.
- **Enforced by:** the swarm / async batteries in `synth_async.py`.

### Law 13 — CANONICAL
- **Statement:** set-equality replication is **orchestrator→worker directional**;
  worker→orchestrator updates of existing records are limited to the promotion
  path. Candidate completeness and fact updates are DISTINCT protocol channels
  and must not share one set-equality rule.
- **Failure that earned it:** Law 13 "preceded its implementation by one
  release" — only behavior deltas were value-compared, leaving workers negative
  authority (suppress a true behavior, withhold a program, forge the solution
  signal).
- **Cited by / text:** `FINDINGS.md:341,371-373`.
- **Enforced by:** the v4.4/v4.5 forgery-omission LAWS batteries (twenty
  forgery/omission classes rejected).

### Law 23 — CANONICAL (ratified 2026-07-22)
- **Statement:** *A memoization key must include every dimension over which the
  memoized generator ranges.* A key that omits depth, size, profile, policy or
  another ranged dimension silently aliases different computations and can
  manufacture false coverage or emergence results.
- **Provenance:** architect ruling, `LAW_RATIFICATION_2026-07-22.md` (not a
  fabricated historical quote).
- **Witness (candidate):** `TRVM_july_21_research/async-memokey-fix.patch`.

### Law 26 — CANONICAL
- **Statement:** a fault-injection test must assert the fault actually fired.
- **Failure that earned it:** the "partition" row — partition window (2,300,900)
  vs stops at ticks 238–318; 7/8 runs ended before the partition began. It
  measured no-partition dynamics under a partition label.
- **Cited by / text:** `FINDINGS.md:406`,
  `TRVM_july_21_research/CHANGELOG-async-memokey-fix.md:112`.
- **Enforced by:** the staged-partition-healing probe (asserts the partition
  bites 8/8 before measuring recovery).

> **Laws 20, 21, 22, 24, 25 — removed from the numbered index (2026-07-22).**
> There was no coherent numbered 20–25 series. Only Laws 10, 13, 23, and 26 are
> attested. The useful paraphrases that once carried those numbers are preserved
> without numbers in the appendix **"Unnumbered candidate principles"** below.
> They become laws only through a future explicit ratification.

---

## Unnumbered candidate principles

These are attested *paraphrases* from review commentary, preserved for their
content only. **They are not laws.** They carry no number and no binding
authority, and may not be cited. A future architect ruling may promote one by
assigning it a fresh reserved ID and a canonical statement.

- **Fixed-point coverage** — measure coverage only at a genuine fixed point of
  merge, never when local queues first empty. (Formerly floated as "law 24.")
- **Oracle separation** — distinguish autonomous dynamics from a measurement
  oracle; the thing being measured must not double as the measurer. (Formerly
  floated as "law 25.")
- **(20, 21, 22)** — no recoverable content; numbers only, discarded.

---

## How to use this file

1. **Citations in code point at law IDs.** A docstring may write "(Binding Law
   5)"; that citation resolves here.
2. **Battery runners should print which laws they assert.** A green run should
   name the law IDs it just enforced.
3. **B→A promotion is a human act.** When the architect supplies canonical text
   for a Tier B law — or ratifies a canonical statement outright — move it to
   Tier A with the provenance (source location or ratification file). Never
   backfill canonical text from an agent's paraphrase.
4. **Future batteries declare the laws they assert.** New battery runners set
   `ASSERTS_LAWS = ("L4", "L6")` and print it in the final verdict. Do **not**
   retrofit this onto frozen historical `binding_run*.py`, `fixture.py`, or
   `compiler.py`.

## Ratification history

- **2026-07-22** — `LAW_RATIFICATION_2026-07-22.md`: ratified Laws 4, 6, 23 to
  Tier A; reserved Laws 1, 2, 3, 7; removed the unattested 20–25 numbering
  (kept attested Law 23); fixed the B→A provenance typo. Law 6 is now global,
  no longer horizon-scoped.

## Open items for the architect

- Restore any of the RESERVED IDs (1, 2, 3, 7) only if real historical text is
  found or a new statement is explicitly assigned.
- Consider whether the "Unnumbered candidate principles" warrant fresh ratified
  IDs.
