# DIST_IC — coordination-free distributed reduction over the IC32 runtime

**File:** `dist_ic.py` (self-validating: `python3 dist_ic.py`)
**Depends on / oracle:** `ic_float.py` (and the semantics shared with `ic32.c`).
**Status:** ✅ single-node matches the oracle on 20 terms; ✅ **480 distributed runs**
(20 terms × 24 partition/order configurations) every one equals the single-node
normal form — schedule- and partition-independent.

This is the strategic piece: reducing **one** interaction-calculus term across
multiple nodes with no locks and no consensus. It's the axis HVM isn't building
(cross-machine reduction), realized on the runtime from the previous steps.

## The claim, and why it holds

Interaction-calculus reduction is **confluent by construction**: the normal form
doesn't depend on the order redexes fire. Confluence is the operational license
for coordination-free distribution — if order doesn't matter, then *which node*
fires a given redex, and *when*, doesn't matter either. So:

- A term's heap is **sharded across nodes**; a reference is a global `(node, addr)`.
- Each interaction is performed by the node that **owns its principal node** (the
  `LAM`, the `SUP`, the floating `DUP`), dereferencing across boundaries on demand.
- No node ever needs a lock or a global agreement to fire a redex.

The test that this is real: vary the partition (which node owns which nodes) and
the evaluation order (which child is normalized first), and confirm the answer
never changes.

## Validation

`python3 dist_ic.py`:

- **Single-node vs `ic_float`: 20/20 match.** The reducer (ported to operate over
  a global `(node, addr)` store instead of a local heap) is itself correct —
  README examples, Church arithmetic, exponentiation, Church-N∘`NOT`, and the
  cases `ic_ref` diverges on.
- **Distributed invariance: 480/480.** Each term run under 24 configurations —
  worker counts W ∈ {2,3,4} × {round-robin, block, and randomized partitions} ×
  {left-first, right-first} evaluation order. **Every run produces the single-node
  normal form.** One distinct result across all of them.
- Cross-node interaction counts (the communication volume) range from 0 (a
  partition that happens to keep interacting nodes co-located) up to the full
  interaction count (maximally scattered, e.g. 51 cross-node delegations for
  `3³`) — real communication is happening, and the answer is invariant to it.

## Termination

In this **demand-driven** model (a node reduces a subterm to normal form, pulling
remote pieces on demand, like distributed lazy evaluation) termination is
**structural**: the computation is done when the root normalization returns. There
are no autonomously-firing redexes left in flight, so no separate distributed
termination detector is needed — the same reason `dsearch`'s termination was a
plain `join()`.

The harder regime is the **autonomous redex-bag** model: every node independently
drains a bag of redexes and pushes work across boundaries with no central
call/return structure. *There*, detecting global quiescence is nontrivial and
needs a Safra-style token — which is exactly what `p2.py` implements for the
interaction-combinator model. The two regimes are complementary; this file covers
the demand-driven one for IC32.

## Honest limitations

- **Faithful simulation, not real processes (yet).** Each node has its own
  isolated heap and all cross-node access is counted as communication, so the data
  placement and message structure are modeled exactly — but the nodes run in one
  Python process under a deterministic driver. That's deliberate: it lets the suite
  prove schedule-independence by exhausting many schedules, which a single threaded
  run can't. Running nodes as real OS processes is the engineering follow-on
  (`p2.py` already showed real threads work for combinators; `dsearch` uses real
  `multiprocessing`). The semantics don't change.
- **Demand-driven, so no parallel *speedup* is claimed here.** Like `dsearch`,
  the point is coordination-free *correctness* (any partition/order ⇒ same answer),
  not wall-clock. Parallel speedup needs the autonomous model with real concurrent
  workers and a non-toy workload.
- **Inherits the recursion-depth limit** of the recursive `normal`/`whnf` (Python
  recursion cap; the iterative rewrite noted for the WASM build applies here too).
- **One distributed knob shown (data placement + eval order).** A full treatment
  would also vary *when* messages are delivered under true concurrency; confluence
  predicts invariance there too, and `p2.py`'s threaded combinator runs are
  evidence, but this file doesn't exercise concurrent delivery.

## How it composes with the rest

Three distribution results now sit together, covering the space:

| | workload | cross-node dependency | merge / coordination | termination |
|---|---|---|---|---|
| `dsearch.py` | superposed **search** | none (independent branches) | G-Set union (CRDT) | trivial (`join`) |
| `dist_ic.py` (this) | **one term**, sharded | owner-performs-interaction | none (confluent) | structural (return) |
| `p2.py` | one net (combinators) | boundary active pairs | owner = `min(node)` | **Safra** detector |

Same underlying thesis throughout: **reduction is the data plane and needs no
coordination; only termination is ever a control-plane question, and only in the
autonomous regime.**

## Where this goes

1. **Real processes / Web Workers.** Put each node in its own process (or, for the
   WASM build, its own Web Worker), with the `(node, addr)` references carried over
   a real message channel (`postMessage` / WebRTC). The protocol is unchanged.
2. **Autonomous + Safra for IC32.** Add the redex-bag regime over the sharded heap
   and reuse `p2.py`'s Safra detector, to get parallel speedup (not just
   coordination-free correctness).
3. **Unify with the WASM substrate.** Each Web Worker runs `ic32.wasm`; the heap
   shards live in each worker's linear memory; boundary references cross via
   `postMessage`. That is the browser-native, sovereign, coordination-free
   multi-node interaction-calculus runtime the whole arc has been building toward.

Arc: correct simple core (`ic_ref`) → monotone search distributed coordination-free
(`dsearch`) → correct general core (`ic_float`) → packed-word native runtime
(`ic32.c`) → WebAssembly build (`ic32.wasm`) → **coordination-free distributed
reduction** (`dist_ic.py`, this file) → real-process/Worker deployment + autonomous
regime → [&]/OpenSentience unification.
