# HyperSurface reducer-host experiment

A bounded invocation adapter for the pinned ABI-v2 IC32 Wasm binary. This
is an experimental host, not a Super backend, TRVM distribution implementation,
semantic admission service, or hardware-isolated execution profile.

Tested with Node 25.2.1. No packages or network access are needed.

```sh
printf '%s' '(λx.x λy.y)' | node runtime/wasm/experimental/cli.mjs
node --test --test-isolation=none runtime/wasm/experimental/host.test.mjs
```

The library entry is `createReducerHost().reduce(input, {signal})`. Construction
verifies the exact module digest and zero imports. Requests cannot choose a
module, worker program, deadline or import set. One host object permits one
in-flight invocation and refuses concurrent work without queueing. Multiple
host objects are possible; this is not a process-wide concurrency limit.

Each invocation gets a fresh worker thread and a fresh Wasm instance. Only the
compiled module is reused. Inputs are limited to 64 KiB of UTF-8, checked before
encoding/copying, with a preliminary string-length cap. NUL, empty input and
ill-formed Unicode refuse. The CLI caps streaming input before concatenation.
Candidate output is capped at 1 MiB before decoding, copying or posting it.

The one-second deadline starts before worker construction. Timer expiration
requests termination; an independently checked clock rejects late replies even
if the parent's timer was delayed. Cancellation uses the same exit barrier.
The host returns an admitted invocation's result and releases its slot only
after worker exit. A termination error returns `indeterminate` and keeps the
host object occupied. There is no automatic replacement after unconfirmed exit.
The deadline is not a hard real-time response bound: scheduling and termination
can take longer. Node/V8 and the trusted JS adapter remain in the host TCB.

No hard CPU, process-memory, kernel-memory or RSS limit is claimed. The guest
has 256 MiB initial linear memory; that is not measured resident memory. Worker
`resourceLimits` are intentionally not advertised as Wasm memory enforcement.
See [Node worker documentation](https://nodejs.org/api/worker_threads.html).

## Checked ABI and semantic boundary

The adapter now uses `ic32_checked.wasm` and ABI v2. Guest parse errors, step
exhaustion, output overflow and guarded resource exhaustion are typed separately.
Literal `ABORTED` is valid candidate text. Partial failed output is never returned.
See [ABI_V2.md](ABI_V2.md) for status codes, grammar/resource limits and build steps.

A successful guest result remains a candidate, not an accepted semantic successor.
This bounded corpus is not full TRVM conformance. Host status and guest status
also remain separate: a trap or interrupted worker is not a successful guest call.

Structured host statuses are `candidate`, `refused`, `cancelled`, `deadline`,
`failed`, and `indeterminate`. `workerExited: true` is only added after exit is
confirmed. Pre-dispatch refusals create no worker.

## Relationship to existing hosts

`wrun.js` remains the minimal standalone wrapper. `runtime/js/swarm.js` remains
its existing partitioned-search/union experiment; it reuses a worker's instance
across a slice and resolves results before awaiting termination. This adapter
adds per-invocation bounds and an exit barrier without changing that experiment
or adding another scheduler. It is deliberately not wired into Super's current
terminal-bearing Carrier profile: a headless reducer requires its own admitted
profile and owner integration.

Tests cover the prior independent Python corpus, input/output refusal,
substituted-module rejection, cancellation, single-slot admission, late replies,
worker failure, cleanup ordering, unconfirmed exit and termination of a real
worker reaching an infinite Wasm function while the parent stays responsive.
The output-boundary cases use synthetic export observations; they do not claim
the production reducer was driven to every allocation failure. No live-instance
pool or external host port is introduced.
