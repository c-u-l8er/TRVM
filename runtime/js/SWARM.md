# SWARM — the runtime, coordination-free, on the WebAssembly substrate

**File:** `swarm.js` (`node swarm.js`) · uses `ic32.wasm`
**Status:** ✅ `ic32.wasm` running across real isolated workers; every worker count
× merge order equals the oracle; one distinct result (schedule-independent).

This is the capstone: the whole thesis, end to end, on the sovereign substrate —
**a coordination-free, multi-node interaction-calculus runtime, in WebAssembly.**

## What runs

`swarm.js` spawns Node `worker_threads` — the Web Worker analog; in a browser
these are literally Web Workers (separate JS realm, separate WASM linear memory).
**Each worker is a genuinely isolated node** with its own instance of `ic32.wasm`
and its own heap. The workers partition a search and each reduces its slice
*through the WASM runtime* (each candidate's test is a real interaction-calculus
reduction: `NOT^n(FALSE)`, which is `TRUE` iff `n` is odd). Their solution sets
merge by **union** — a grow-only set, the canonical CRDT join (commutative,
idempotent, monotone).

## What it proves

```
ic32.wasm coordination-free across real workers (worker_threads)
oracle (odds 0..15): 1 3 5 7 9 11 13 15
W=1: sizes=[8]            total-interactions=1264  OK
W=2: sizes=[0,8]          total-interactions=1264  OK
W=3: sizes=[3,3,2]        total-interactions=1264  OK
W=4: sizes=[0,4,0,4]      total-interactions=1264  OK
W=6: sizes=[0,3,0,3,0,2]  total-interactions=1264  OK
W=8: sizes=[0,2,...]      total-interactions=1264  OK
distinct merged results across ALL (worker-count x merge-order) configs: 1
all configs == oracle: true
```

- **Real isolated nodes.** Each worker has its own WASM instance and linear
  memory; nothing is shared but the final result sets.
- **Coordination-free.** The merge is a monotone CRDT join, so by CALM the result
  is independent of worker count and merge order — **one distinct result across
  every configuration**, equal to the brute-force oracle. No locks, no consensus.
- **On the real runtime.** The per-candidate predicate is reduced by `ic32.wasm`,
  not a mock — total interaction count (1264) is identical across all partitions.

## Honest note

Workers run concurrently and the merge needs no coordination, but at this toy
scale **worker-thread startup dominates wall-clock**, so more workers is not
faster here (W=1: 126 ms → W=8: 495 ms). The claim is coordination-free
*correctness* on the real WASM runtime — any worker count, any merge order, same
answer — not speed. Wall-clock speedup needs a heavier per-worker workload (so
compute dominates startup) and/or the distributed-control-flow regime; see the
limitations in `DIST_REAL.md`.

## Why this is the capstone

It composes every prior piece into one runnable artifact on the target substrate:

- the **runtime** (`ic32.wasm`, the packed-word IC32 reducer compiled to WASM),
- the **distribution thesis** (coordination-free, monotone-merge, schedule-
  independent — the same property proved for reduction in `dist_ic`/`dist_real`
  and for search in `dsearch`),
- the **sovereignty substrate** (WebAssembly, browser-native, no server).

In a browser this is the same code with `Worker` instead of `worker_threads`:
client-side, sovereign, multi-node interaction-calculus compute with no
coordination — the concrete "browser is the new BEAM" realization, and the
substrate the [&]/OpenSentience layer sits on.

## Where it goes from here

- **Browser harness** — load `swarm.js`'s logic from a page with Web Workers (the
  isolation model is identical); add WebRTC so the workers can span *machines*, not
  just cores.
- **Distributed control flow** (re-entrant workers / CPS) — for the boundary-port
  *reduction* regime (`dist_real`) on these workers, collapsing messages to
  boundary-crossings-only and unlocking parallel speedup.
- **OpenSentience** — agents as IC sub-nets on this engine, `&reason` governance
  verified on it, coordination-free across browsers/edge.
