# Async synthesis: four correction passes, and the result that survives all of them

*Scope: `research/synth_async.py` (fixes) and `FINDINGS.md` (corrected record),
plus `research/probe_quiescence.py` and `research/probe_autonomous.py` (probes).
Four rounds of an adversarial peer-review loop. Each round a satisfying claim
turned out to be an artifact; each was retracted; a narrower, better-measured
result survived — and by round 4 the surviving result is stronger than any of
the retracted ones. Every number is reproducible with the commands at the end.*

---

## Round 1 — the depth-blind memo key

`Node.refill()` advances enumeration depth by a recursion that leaves the
**frontier** unchanged, but its regeneration memo key stamped on the frontier
alone — so the guard fired the instant depth first reached `max_size`, skipping
the entire size-8 candidate band forever. Canonical `N=1` reported **14/16**
(XOR, XNOR "missing"), and fault-driven churn that defeated the guard looked
like an emergent benefit: "**schedule divergence purchases coverage**." That
headline was the bug's mirror image.

**Fix:** `stamp = (self.depth, frozenset(...))`. Canonical `N=1`: 16/16
deterministically, **16,134 interactions / 280 programs**, pid-for-pid equal to
the independent synchronous closure.

## Round 2 — the harness measured before closing (and restart accounting)

The round-1 replacement claim — under faults the collective "settles *below*
the ceiling" (one 15/16 run) — was the same premature-termination error one
level up: `run_async` reported coverage after a final fact merge **without
closing the merged frontier** (a node sat with `gen_stamp=None`, knowing it was
stale, never stepped again). `probe_quiescence.py` closes that run to **16/16
in ≤3 rounds**. Also fixed: restart rollback zeroed `paid`/`vpaid`, making
`dup = worker − unique` **negative** (−6,238); run-level carried counters make
`dup ≥ 0` by construction. Added an `N=1` seed sweep.

## Round 3 — the "fixed point" was a saturation oracle hiding eventual agreement

Round 2's closure phase is an **oracle**: all-to-all full-state exchange plus
central work exhaustion. It computes the point the dynamics converge toward —
it does not show the pairwise gossip scheduler getting there. Removing it
(`probe_autonomous.py`): coverage closure **is** autonomous and robust, but at
the default anti-entropy the stability heuristic stops the loop **disagreeing**
(a replica can still be below 16). Deterministic agreement at a stopping time
is what the oracle buys. Fixes: precise relabeling; saturation **bytes counted**
(KB was asymmetric with worker cost); round cap + guard assertion; "every
schedule" → "all tested configurations"; corrected lattice numbers (346–399
healthy, 427–508 faults); multiplicity demoted to a structural effect (no
strictly better preferred rep found).

## Round 4 — the partition that never happened, and layered agreement

The reviewer caught four more, all verified and fixed:

1. **The autonomous "partition" row was an invalid test.** Partition window
   (2, 300, 900) vs run stops at ticks **238–318**: 7/8 runs ended *before the
   partition began*; none saw healing. It measured no-partition dynamics under
   a partition label. (In the main harness the window IS active at quiescence —
   so that row measures "partition active at stop; the oracle reunites the
   node"; now annotated.) **Rebuilt as a staged-healing experiment** that
   asserts the fault overlaps execution and records per-node coverage at heal:
   the fault bites in **8/8** runs per window (isolated node at **14–15/16** at
   heal), and the **unchanged protocol recovers autonomously** — median
   **31–38 ticks** from heal to full per-replica coverage, median **~91**
   (max 212) to fact agreement, across windows (50,150), (50,250), (100,250) ×
   8 seeds. Autonomous partition recovery is now demonstrated, not assumed.
2. **"A fact still in flight" was the wrong mechanism.** At both non-agreeing
   stops, all inboxes were **empty** (`[0,0,0,0]`); the differing facts sat in
   one replica's store (`[325,321,321,323]` / `[351,351,351,348]` programs)
   **awaiting a future random anti-entropy pairing**. Continued ordinary gossip
   agreed in **6** and **43** ticks — the eventual-consistency reading,
   strengthened.
3. **The probe's coverage read node 0 only.** "40/40" formally asserted node
   0's coverage; the per-replica claim happened to be true but unenforced. Now
   `covs()` is per-node and the battery **asserts every replica** at 16/16
   (**32/32** in the relabeled no-partition battery).
4. **Agreement is layered, and the layering is the finding.** At the heuristic
   stop: **signature-set agreement 32/32**, **preferred-map agreement 32/32**,
   **fact-store agreement 31/32**. Semantic recognition stabilizes **before**
   the supporting evidence history synchronizes. Also tightened: "global
   convergence is not locally decidable" → **this stability heuristic** cannot
   establish fact agreement; certified termination (acks, version vectors,
   termination-detection protocols) is a distinct, unbuilt layer. The record
   now carries the stopping-mode ladder: local stability < local closure <
   signature-set agreement < preferred-map agreement < fact agreement <
   saturated closure < certified termination.

## The result that survives all four passes

| layer | status |
|---|---|
| **Per-replica behavior coverage** | autonomous and robust: **32/32** runs (latency/dup/loss battery, per-node asserted); after a partition that provably bites, recovered in median **31–38** ticks post-heal. |
| **Semantic agreement** (signature set, preferred map) | **32/32** at the stability stop — stabilizes before fact histories synchronize. |
| **Fact-store agreement** | eventual: **31/32** at the stop; the miss agrees after **43** ticks of continued gossip; deterministic agreement at a chosen time is what the saturation oracle buys. |
| **Partition healing** | demonstrated: fault bites 8/8 (node at 14–15/16 at heal); unchanged protocol recovers coverage and agreement autonomously. |
| **Program lattice** | trajectory-dependent: 280 / 346–399 / 427–508 (canonical / healthy / faults), not nested; **no strictly better preferred rep** — multiplicity is structural, benefit unproven. |
| **Cost** | 58–90% extra worker interactions under faults; saturation bytes counted; adequate autonomous anti-entropy ≈ 2× bandwidth. |

One-liner: **same facts compel the same recognized behaviors — and recognition
can be shared before, and independently of, the full evidence history being
shared.**

## Verification (all fresh, all green)

| check | result |
|---|---|
| canonical `N=1` | 16/16, 16,134, 280; deterministic over seed sweep; == sync closure pid-for-pid |
| six fault configs (saturated) | all 16/16; agreement saturation-confirmed; `dup ≥ 0` |
| L=20 resume probe | 15/16 at old stop → 16/16 in ≤3 rounds |
| autonomous battery (no partition) | per-replica coverage **32/32**; sig/pref agreement **32/32**; fact **31/32**; miss agrees +43 ticks |
| staged partition healing | bites 8/8; recovery median 31–38 (cov) / ~91 (agree, max 212) ticks post-heal |
| partition-row audit | old row: 7/8 runs ended before the partition began (Law 26) |
| `make test` | 13/13 + wasm + swarm + CvRDT laws |
| FLAG XOR3 `5779c31e` → `cd8b128e` | holds |

## Laws (async series)

23 — a memo key must include every dimension the generator ranges over.
24 — measure coverage only at a genuine fixed point.
25 — distinguish autonomous dynamics from a measurement oracle; a stability
heuristic observes silence, not agreement; certified termination is a separate
unbuilt layer; account for oracle bytes symmetrically.
**26 — a fault-injection test must assert the fault actually overlapped
execution** — a test whose fault never fires measures the wrong hypothesis
while reporting success.

## Open questions (deliberately not built yet)

Whether trajectory-created multiplicity ever **helps** — component-removal
resilience, larger-horizon closure, cross-runtime corroboration, richer quality
metrics. Whether single-preferred-rep closure is complete at all horizons.
Certified distributed termination. Measure before building.

## Reproduce

```
PYTHONPATH=runtime/python:research python3 research/synth_async.py          # CONV (saturated)
PYTHONPATH=runtime/python:research python3 research/synth_async.py FLAG      # XOR3 via cd8b128e
PYTHONPATH=runtime/python:research python3 research/probe_quiescence.py      # closure: L=20 15->16
PYTHONPATH=runtime/python:research python3 research/probe_autonomous.py      # autonomous: 32/32; layered agreement; staged healing
PYTHONPATH=runtime/python:research python3 research/synth_bool4.py LAWS DET MP
make test
```

## Files

- `async-memokey-fix.patch` — cumulative unified diff of all four rounds
  (`git apply` from the TRVM root; verified against the pristine tree).
- `synth_async.py`, `FINDINGS.md`, `probe_autonomous.py`, `probe_quiescence.py`
  — changed/new files for direct review.
- `TRVM-updated.zip` — full tree, drop-in verified.
