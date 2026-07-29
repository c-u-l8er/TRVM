# TRVM conformance

How a new implementation of the TRVM runtime proves it is correct. This is the
contract `spec/SPEC.md §6` defines, made executable.

## 1. Purpose, scope, and exclusions

This document specifies the conformance pass that settles the claim: **TRVM's
distribution protocol produces identical results on real deployed machines as
single-node sequential reduction.** The pass exercises every §6 criterion against
the real substrate — separate OS processes, real network transport, real storage.

| | |
|---|---|
| **Prior evidence rung** | In-process simulation (`dist_ic.py`): protocol-correct under function-call message passing within a single OS process. |
| **Target evidence rung** | Cross-process, real transport: distribution-correct across separate OS processes communicating over serialized bytes on a real network. |
| **Settling artifact** | A machine-readable JSON certificate (§5) with verdict PASS, listing the participating `node_id`s, OS PIDs, hosts, transport type, and the predicate that was evaluated. |

### 1.1 Deployed-machine topology

The conformance pass requires **at least two TRVM instances** running as separate
OS processes on separate machines (or separate containers with isolated network
namespaces). The minimum topology:

| Role | Count | Description |
|------|-------|-------------|
| **Reducer node** | ≥ 2 | Each runs a `trvm_reduce_batch` loop on its own heap. Connected by a real transport (TCP or distributed Erlang). Each node has a distinct `node_id`. |
| **Test harness** | 1 | Orchestrates: loads the net, partitions it, distributes partitions, triggers reduction, collects readback, compares against the sequential oracle. Does NOT participate in reduction. |

The harness MUST record and report for each run: the `node_id` of every
participating reducer, the transport type (e.g. `tcp`, `dist_erlang`), and the
OS process IDs.

### 1.2 Explicit exclusions

The following do NOT satisfy deployed-substrate conformance, regardless of how
many §6 checks they pass:

- **In-process simulation.** Multiple heaps in one OS process with function-call
  "message passing" (e.g. `dist_ic.py`'s model) validates the protocol semantics
  but not the transport, serialization, or process-isolation boundaries.
- **Injected/mock transports.** A transport layer that bypasses serialization or
  delivers messages by reference transfer is not a real transport.
- **Stubs.** A backend that implements `trvm_reduce_batch` but stubs
  `trvm_inject`, `trvm_snapshot`, or `trvm_restore` is incomplete.
- **Single-process round-trips.** Loopback connections within one process do not
  exercise OS-level isolation or real network failure modes.

These approaches remain valuable for development (see §7: Rejected Approaches)
but produce a different, weaker evidence class.

---

## 2. What an implementation must do

1. **Reproduce every vector.** `vectors/normalize.json` is a list of
   `{ term, nf, ref_interactions }`. Each `term` is in the surface IC/lambda syntax
   (`λ`, application `(f x)`, superposition `&L{a,b}`, duplication `!&L{a,b}=v; body`,
   eraser `*`). Your runtime MUST normalize `term` to exactly `nf` (canonical naming:
   bound variables renamed `a, b, c, …` in first-encounter order; free names
   preserved). `ref_interactions` is the Python reference reducer's interaction count
   — a *native/optimal-sharing* runtime may take a different number of interactions,
   so only the **normal form** is normative across runtimes; the interaction count is
   pinned only for the reference reducer it was recorded from.

   The vectors are **cross-validated at authoring time**: a term is only included if
   `ic_float` (Python reference) and `ic32` (C) already agree on its normal form, so
   you can diff against `nf` directly.

2. **Pass the behavioral batteries** (SPEC §6.1–§6.3) — see §3 below for the
   fixed battery contract.

3. **Pass the deployed-substrate criteria** (SPEC §6.6–§6.9) against real
   machines as described in §1.1.

---

## 3. Behavioral battery contract

The batteries referenced by SPEC §6.1–§6.3 use these fixed parameters. "N
random" and "a battery of nets" are replaced with concrete, reproducible rules.

### 3.1 Test nets (the battery)

The battery consists of **all terms in `vectors/normalize.json`** that produce at
least one interaction (`ref_interactions > 0`). This is the complete corpus — no
sampling, no "representative subset." When vectors are added, the battery grows
automatically.

For the distribution batteries (§6.2–§6.3), the battery additionally includes
the `make_demo_net(D)` combinator net from `inet.py` with D=3 (15 interactions,
the canonical test net from the paper).

### 3.2 Confluence battery (§6.1)

For each net in the battery:

- **Run count:** N = 300 random reduction orders per net (as already implemented).
- **Seed recording:** the PRNG seed for each run MUST be recorded in the
  certificate. The runner MUST accept an optional `--seed` argument to reproduce
  a specific run.
- **Fixed policies:** additionally reduce under `first` and `last` redex-selection
  policies (2 extra runs per net). All 302 runs MUST produce identical normal form
  and identical interaction count.

**Interaction-count equality scope.** Within a single runtime (e.g. all 302 runs
of `ic32`), interaction count MUST be identical across all reduction orders — this
is the confluence invariant. Across runtimes (e.g. `ic_float` vs `ic32`), only the
normal form is normative (§2 item 1). A native or optimal-sharing runtime that
takes a different number of interactions than the reference reducer is conformant
provided (a) its normal form matches the oracle and (b) its own interaction count
is stable across all reduction orders of the same net.

### 3.3 Distribution battery (§6.2)

For each net in the battery:

- **Partition count:** test with 2, 3, and 4 partitions (nodes).
- **Partition rule:** for P partitions, agent `i` is assigned to node `i mod P`.
  This is deterministic and exercises all partition sizes without randomness.
  Additionally, one random partition per (net, P) pair MUST be tested, with its
  seed recorded.
- **Delivery-order coverage:** for each (net, partition), reduce under at least
  3 random message-delivery orders, seeds recorded. At least one run per net MUST
  use a delivery order that reverses the natural emission order (worst-case
  reordering within the per-pair FIFO constraint).
- **Total:** for each net: 3 partition sizes × (1 deterministic + 1 random
  partition) × 3 delivery orders = 18 runs minimum.

### 3.4 Exactly-once battery (§6.3)

For every run in §3.3, assert: `exports == boundary_rewrites`. No separate
battery — exactly-once is a per-run invariant checked on every distribution run.

Additionally, inject at least one duplicate Export (same `(sender, seq)`) per
(net, partition) pair and verify it is silently discarded per §4.5 idempotent
inject.

---

## 4. Conformance verdict

### 4.1 Required backends

A conformance run MUST exercise **all five IC32-family backends** declared in the
runner (`ic_float`, `ic32` C, `ic32.wasm`, `ic32z` Zig, `ic32m` Mojo). A backend
that is not built is **INCOMPLETE**, not skipped.

### 4.2 Verdict definitions

| Verdict | Condition |
|---------|-----------|
| **PASS** | All five IC32 backends produce matching normal forms for every vector. §6.1 confluence (302 runs/net), §6.2 distributed==sequential (18 runs/net), and §6.3 exactly-once all pass. §6.4 and §6.5 pass if their prerequisites exist (see §6). The deployed-substrate criteria §6.6–§6.9 all pass against real machines (§1.1). |
| **FAIL** | Any backend produces a normal form that disagrees with the oracle. Any §6.1–§6.3 or §6.6–§6.9 check fails. Any duplicate-Export injection is not discarded. |
| **INCOMPLETE** | Any declared IC32 backend is not built. §6.4 or §6.5 prerequisites are absent and those checks are therefore not run. Any deployed-substrate criterion is not exercised (e.g. no multi-machine setup available). |

The runner MUST exit 0 only on PASS. INCOMPLETE MUST exit nonzero (exit code 2)
with a report naming every skipped check and why. The current runner's
auto-detection policy (skip with a note) satisfies the visibility requirement but
MUST NOT produce exit 0 when backends are missing.

### 4.3 Prohibited claims

The following MUST NOT be reported as conformance (PASS or INCOMPLETE):

- **Disagreement.** Any backend producing a normal form that differs from the
  oracle is a FAIL, not a data point to investigate later.
- **Crash or signal death.** A backend that crashes, segfaults, or is killed by a
  signal during any conformance check is a FAIL for that backend.
- **Timeout.** A backend that does not terminate within the runner's timeout is a
  FAIL. The timeout MUST be recorded in the certificate.
- **Malformed output.** A backend whose readback is not a valid §2.4 serialization,
  or whose normal-form string does not parse, is a FAIL.
- **Missing mandatory capability.** A backend that does not implement
  `trvm_reduce_batch`, `trvm_inject`, `trvm_load`, or `trvm_readback` is
  INCOMPLETE (not PASS and not "skipped with a note").
- **Skipped required checks.** A run that omits any §6.1–§6.3 check or any
  deployed-substrate check (§6.6–§6.9) that the runner claims to cover is a FAIL,
  not a partial pass.
- **Silent canonicalization.** A runtime that rewrites, repairs, or
  re-canonicalizes a readback result before comparing it to the oracle is
  non-conforming. The comparison input MUST be the raw readback output; any
  mismatch is a FAIL, not a fixable discrepancy.

A certificate with verdict PASS MUST NOT contain any of the above conditions. A
runner that encounters any of these MUST set the verdict to FAIL (or INCOMPLETE
for missing capabilities) and MUST exit nonzero.

---

## 5. Certificate and evidence

Each conformance run MUST produce a machine-readable JSON certificate. One
certificate per run; the harness collects them into a single report.

### 5.1 Certificate schema

```json
{
  "claim": "§6.2 distributed == sequential",
  "prior_rung": "in-process simulation (dist_ic.py)",
  "resulting_rung": "cross-process, real transport",
  "verdict": "PASS",
  "machines": [
    { "node_id": 0, "pid": 12345, "host": "node-a.internal" },
    { "node_id": 1, "pid": 12346, "host": "node-b.internal" }
  ],
  "transport": "dist_erlang",
  "backend": "ic32",
  "backend_version": "git:abc1234",
  "net": "church_2_add",
  "seed": 42,
  "partition": [0, 1, 0, 1, 0],
  "delivery_order_seed": 99,
  "result": {
    "nf": "(s (s z))",
    "interactions": 15,
    "exports": 4,
    "boundary_rewrites": 4,
    "oracle_nf": "(s (s z))",
    "oracle_interactions": 15
  },
  "settled_by": "nf == oracle_nf AND interactions == oracle_interactions AND exports == boundary_rewrites",
  "timestamp": "2026-07-29T12:00:00Z"
}
```

### 5.2 Required fields

Every certificate MUST include: `claim`, `verdict`, `machines` (with `node_id`,
`pid`, `host` for deployed-substrate runs), `backend` and `backend_version`,
`net` (identifying the input), `seed` (PRNG seed, or `null` for deterministic
runs), `result` (observables), `settled_by` (the predicate that was evaluated),
and `timestamp`.

For distribution certificates (§6.2–§6.3, §6.6–§6.9), the certificate MUST
additionally include: `partition` (the agent-to-node assignment array, verbatim),
`delivery_order_seed` (the PRNG seed governing message-delivery order), and
`partition_seed` (the PRNG seed for random partition assignment, or `null` for
the deterministic `i mod P` assignment). These fields, together with `seed` and
`net`, MUST be sufficient to reproduce the exact run.

For claims being moved up the evidence ladder, `prior_rung` and `resulting_rung`
MUST name the evidence level before and after this run.

---

## 6. Required §6 coverage: §6.4 and §6.5

### §6.4 Snapshot round-trip

**Status: deferred.** No `snapshot()`/`restore()` implementation exists in the
reference reducers. The C/Zig/Mojo/WASM backends implement single-net reduction
only; the serialization API (§2.4) is implemented for `trvm_load` but not for
`trvm_snapshot`/`trvm_restore`.

**Consequence:** until §6.4 is exercised, the conformance claim is:

> *"TRVM reduction is correct and distribution-safe (§6.1–§6.3, §6.6–§6.9), but
> checkpoint/restore round-trip fidelity is unverified."*

This is a narrower claim but it is honest: snapshot/restore (§5) provides local
checkpoint/recovery only and is not on the critical path for the distribution
protocol's correctness. The distribution protocol does not depend on snapshots —
it depends on confluence, exactly-once ownership, and FIFO delivery (all of which
are covered). Snapshot round-trip must be verified before any claim about fault
tolerance (§8) or durable recovery.

### §6.5 REF unfolding

**Status: deferred.** The current battery operates on the interaction-combinator
fragment (ERA, CON, DUP). No vector or battery net contains a `REF` agent
because the reference reducers do not implement supercombinator definitions.

**Consequence:** until §6.5 is exercised, the conformance claim excludes
recursive definitions:

> *"TRVM correctly reduces the interaction-combinator fragment (ERA/CON/DUP) under
> distribution. REF unfolding and recursive supercombinator definitions are
> unverified."*

This is acceptable for v0.1 because the confluent core (§1, §3.1–§3.3) is fully
specified without REF — REF is machinery for recursion that sits above the
combinator substrate. REF unfolding must be verified before any claim about
Turing-complete program reduction.

### Lane-completion gate

This lane (trvm) CANNOT claim full §6 conformance with §6.4 and §6.5 deferred.
The verdict MUST be **INCOMPLETE** with the narrower claims above stated
explicitly. Moving to PASS requires implementing and exercising both.

---

## 7. Rejected approaches

These approaches were considered and rejected for deployed-substrate conformance.
They remain useful for development but produce evidence at a lower rung.

| Approach | Why it is rejected |
|----------|-------------------|
| **In-process multi-heap simulation** (`dist_ic.py`) | Validates the distribution *protocol* (ownership, FIFO, exactly-once) but messages are Python function calls, not serialized bytes over a real transport. Cannot catch serialization bugs, endianness issues, or process-isolation failures. Evidence rung: *protocol-correct*, not *deployment-correct*. |
| **Cross-runtime NF agreement alone** | Proves that multiple backends compute the same normal form for the same input, but says nothing about whether they can coordinate across a real network. NF agreement is necessary but not sufficient for distribution conformance. |
| **Skipped/absent backends** | "0 failures from 0 checks" is not evidence. A runner that exits 0 while backends are missing can mask a broken build or a regression in a backend nobody noticed was absent. The IC32 gate (`bench/test_ic32_gate.py`) exists precisely because this failure mode was observed. |
| **Stub implementations** | A backend that stubs `trvm_inject` or `trvm_snapshot` passes the single-node battery trivially but has not exercised the boundary or checkpoint code paths. Stubs are development scaffolding, not conformance evidence. |
| **Injected/mock transports** | A transport that delivers messages by shared-memory reference transfer or by direct function call bypasses the serialization and OS-level delivery path. Conformance requires that the §2.4 wire format is actually serialized, transmitted, and deserialized. |
| **Single-process distributed simulation** | Running two TRVM instances in the same OS process with loopback sockets tests the code paths but not the failure modes (process crash, independent memory corruption, OS-level resource exhaustion) that real deployment introduces. It is a useful intermediate step, not a final certificate. |
| **Interaction-count portability as conformance evidence** | Interaction count is a mathematical invariant of a *specific reduction strategy*, not a universal runtime property. Optimal-sharing runtimes, runtimes with different REF-unfolding strategies, or runtimes that fuse commutation steps will produce different counts for the same net. Requiring cross-runtime interaction-count agreement would exclude correct implementations. Only normal-form agreement is normative across runtimes (§2 item 1, §3.2). |
| **Single-runtime vectors** | A vector validated by only one runtime (e.g. `ic_float` alone) has no cross-check — a bug in that runtime becomes a bad oracle. The two-runtime admission rule (§10.1) exists because this failure mode is real: `ic_float` and `ic32` have historically disagreed on edge cases, and only cross-validation caught the bugs. |

---

## 8. Coverage status

| Check | Status | Where it runs |
|---|---|---|
| Cross-runtime normal-form vectors | **covered** | `runtime/python/conformance.py` — 6 runtimes: `ic_float`, `ic_ref`, `ic32` (C), `ic32.wasm`, `ic32z` (Zig), `ic32m` (Mojo) |
| §6.1 confluence (300 random orders) | **covered** | `runtime/python/inet.py` battery |
| §6.2 distributed == sequential | **covered (in-process)** | `distribution/dist_ic.py` (480 runs) |
| §6.3 exactly-once boundary | **covered (in-process)** | `inet.py` / `dist_ic.py` |
| §6.4 snapshot round-trip | **GAP** | no `snapshot()`/`restore()` in the reference yet |
| §6.5 REF unfolding | **GAP** | recursive supercombinator REFs not exercised |
| §6.6 cross-process reduction | **GAP** | requires multi-process harness (§1.1) |
| §6.7 exactly-once (cross-process) | **GAP** | requires §6.6 harness |
| §6.8 termination detection (cross-process) | **GAP** | requires Safra/D-S detector over real transport |
| §6.9 serialization interop | **GAP** | requires separately-compiled instances exchanging §2.4 bytes |

The in-process coverage (§6.1–§6.3) validates protocol semantics. The deployed-
substrate criteria (§6.6–§6.9) are the gaps this lane exists to close.

---

## 9. Running it

```bash
make test                              # everything below
python3 runtime/python/conformance.py  # just the conformance runner
```

The runner auto-detects which backends are present. It always checks the Python
reference; it additionally checks any of the following that exist:

| Backend | Built by | Binary |
|---|---|---|
| `ic32` (C) | `make native` | `runtime/c/ic32` |
| `ic32.wasm` | prebuilt; needs `node` | `runtime/wasm/ic32.wasm` |
| `ic32(zig)` | `make zig` | `runtime/zig/ic32z` |
| `ic32(mojo)` | `make mojo` | `runtime/mojo/ic32m` |

A backend that is **not** built is reported as *skipped*, with a note naming the
missing path — never silently treated as passing (see §4.2: this produces
INCOMPLETE, not PASS).

Because only the normal form is normative (§2 above), the runner asserts **NF
agreement** for every backend but pins `ref_interactions` to `ic_float` alone.

---

## 10. Adding vectors

### 10.1 Vector-admission rule (normative)

A candidate term is admitted to `vectors/normalize.json` if and only if:

1. **Cross-validation.** The term is reduced to normal form by **both** `ic_float`
   (Python reference) and `ic32` (C). These two are the **authoritative runtimes**
   for vector admission. Both MUST produce identical normal forms (after
   canonicalization per §10.2). If they disagree, the term MUST NOT be admitted —
   it indicates a bug in one of the runtimes, not a valid test case.

2. **Labeling discipline.** The term uses linear binders and distinct fan labels
   for independent duplicators. Terms with naively-shared labels reduce incorrectly
   *by design* and are not valid vectors.

3. **Canonicalization.** The `nf` field in the vector file MUST use canonical
   variable naming: bound variables renamed `a, b, c, …` in first-encounter
   (left-to-right, depth-first) order; free variable names preserved as-is. The
   canonicalization procedure is deterministic — two correct implementations MUST
   produce byte-identical `nf` strings for the same normal form.

4. **Reference interaction count.** The `ref_interactions` field records `ic_float`'s
   interaction count. This count is normative only for runtimes that claim to
   implement the same reduction strategy as `ic_float`. Other runtimes (native,
   optimal-sharing) are bound only by normal-form agreement (§3.2).

### 10.2 Disagreement

If `ic_float` and `ic32` disagree on a candidate term's normal form, the term
MUST be rejected and the disagreement MUST be reported as a bug. A vector file
containing a term on which the authoritative runtimes disagree is invalid — the
conformance runner MUST refuse to load it.
