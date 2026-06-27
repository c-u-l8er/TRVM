# DIST_REAL — the boundary-port protocol on real OS processes

**File:** `dist_real.py` (self-validating: `python3 dist_real.py`)
**Builds on:** `dist_ic.py` (the protocol, proven in simulation) + `ic_float.py` (oracle).
**Status:** ✅ every term, every worker count, every partition — running on real
forked OS processes with real inter-process messaging — equals the single-node
normal form, including the cases `ic_ref` diverges on.

`dist_ic.py` proved the boundary-port protocol is coordination-free in a faithful
single-process simulation (480 schedule/partition-independent runs). This file
takes that **off the simulation**: each node is a genuinely isolated OS process
(its own heap shard in its own memory), and **every cross-shard reference is a real
message** over a `multiprocessing` channel. The reducer is `dist_ic`'s, unchanged —
it's parameterized over a `net`, and here the `net`'s `read`/`write`/`alloc` are IPC
calls instead of dict access.

## What it shows

`python3 dist_real.py` runs the battery (Church arithmetic, Ex5, Church-N∘`NOT`,
and the divergent-pattern cases) on 2 and 3 real worker processes, under multiple
partitions:

```
term                       oracle | W | IPC msgs  x-shard int | verdict
Ex5                       λa.λb.a | 2 |     139        9       | OK
exp(3,2)=8           λa.(S (S (S  | 2 |     514       15       | OK
div: dup C2->NOT                B | 2 |     233       17       | OK
... (all OK, W=2 and W=3, multiple partitions)
RESULT: all real-process runs == single-node oracle (partition-independent)
```

- **Genuinely isolated heaps.** Each worker is a separate process; shards live in
  separate process memory; there is no shared address space. All access is by
  message.
- **Real IPC volume reported.** 66–514 inter-process messages per reduction. The
  cross-shard *interaction* count (9–23) matches `dist_ic`'s simulation exactly —
  the protocol behaves identically over real channels.
- **Still partition-independent on real processes**, as confluence predicts.

## How it stays deadlock-free (and the honest tradeoff)

Cross-shard interactions create *mutual* data dependencies: an `App` on shard A
applies a `Lam` on shard B, whose body then references the argument back on A. If
every worker both reduced **and** served requests while blocked on another worker,
that mutual dependency would deadlock without re-entrant workers.

This file takes the simplest sound split: **workers are passive shard servers**
(`READ`/`WRITE`/`ALLOC`, never blocking on each other), and a **single coordinator
runs the reduction**, touching remote shards only through messages. No worker ever
waits on another worker, so there is no deadlock. The **state** is genuinely
distributed; the **control flow** is centralized.

That centralization is the honest cost, and it shows up in the message counts: Ex5
does 16 interactions but 139 IPC messages, because *every slot access* is a round
trip. A system with distributed control flow would perform each interaction on the
worker that owns its principal, so messages would drop to just the boundary
crossings (9 for Ex5, not 139). Getting there needs **re-entrant workers** (threads
+ fine-grained per-shard locks) or a **CPS / actor scheduler** so a worker can serve
incoming requests while its own reduction is suspended. That is the next frontier,
and it's also where **parallel speedup** comes from (multiple workers reducing at
once) — neither of which this rung claims.

## The distribution results, now spanning sim and reality

| | model | nodes | cross-node | termination | status |
|---|---|---|---|---|---|
| `dsearch.py` | independent search | real processes | none | trivial `join` | real, parallel |
| `dist_ic.py` | boundary-port reduction | simulated | owner interaction | structural | sim, coordination-free |
| `dist_real.py` (this) | boundary-port reduction | **real processes** | real IPC | structural | **real, coordination-free** |
| `p2.py` | combinator net | real threads | owner=`min` | Safra | real, autonomous |

`dsearch` had real parallelism but no boundary crossings; `dist_ic` had boundary
crossings but in simulation. **This file closes that gap: boundary crossings over
real IPC between real isolated processes.**

## Honest limitations

- **Centralized control flow** (workers are passive) — so no parallel speedup, and
  message counts are higher than a distributed-control system would need. Addressed
  by the re-entrant/CPS step.
- **Chatty by design** (every access is a message) for the same reason.
- **Inherits** the recursive-`normal` depth limit and the no-GC heap bound from the
  underlying reducer.

## Where this goes

1. **Distributed control flow** — re-entrant workers (threads + per-shard locks) or
   a CPS scheduler, so interactions run on the owning worker. This collapses
   messages to boundary-crossings-only and unlocks **parallel speedup** — the piece
   that makes distribution win on wall-clock, reusing `p2.py`'s Safra detector for
   the now-autonomous termination.
2. **Web Workers + `ic32.wasm`** — swap the OS processes for browser Web Workers,
   each running `ic32.wasm`, shards in each worker's linear memory, boundary
   references over `postMessage`/WebRTC. Same protocol, browser-native and
   sovereign — the concrete "browser is the new BEAM" realization.

Arc: correct simple core (`ic_ref`) → monotone search distributed coordination-free
(`dsearch`) → correct general core (`ic_float`) → packed-word native runtime
(`ic32.c`) → WebAssembly build (`ic32.wasm`) → coordination-free distributed
reduction in simulation (`dist_ic.py`) → **the same protocol on real OS processes**
(`dist_real.py`, this file) → distributed control flow + Web Workers →
[&]/OpenSentience unification.
