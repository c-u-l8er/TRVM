# The resident reducer host — the checked IC32 module loaded once, warm workers, a fresh instance per reduction

**2026-09-18.** The vertical witness (`ProjectAmp2/wek/b2/trvm/`, `FOUNDATION_LANE.md` §3ap) measured the executor span of one
`trvm.reduce` effect at **~64 ms of a 67 ms round trip, of which ~56 ms is Node starting** and the reduction itself ~1 ms. Gate 5
of the development plan asked for the bottleneck to be identified before anything was pooled; this is the identified bottleneck's
fix, built in TRVM's lane as the plan's line on "persistent checked-host reuse" requires — with its **ownership, invalidation,
cancellation and resource boundaries** stated (§3) rather than assumed. It is a TRVM component. It is not wired into Super; what
HyperSurface would have to admit to use it is §6, and that is Codex's decision.

Status: **BUILT, MEASURED on the shared laptop (development reading), harness 15/15 + 4/4 over the socket, seven mutant controls
each turning exactly its expected cases red.** Not claimed: any Super integration, confinement, external reproduction, or a
production throughput figure.

## 1. What it is

`resident.mjs` exports `createResidentHost({ pool, maxQueue })` → `reduce(input, { signal })`, the same request shape as the
one-shot host `../experimental/host.mjs` and the same pre-dispatch policy (64 KiB UTF-8 input, NUL/empty/ill-formed refused,
1 MiB output, 50 M interactions, a 1 s deadline; the module digest `0cf96179…` pinned before compilation; zero imports). What
differs is the worker lifecycle: `pool` worker threads are spawned once and kept; each job is posted to an idle worker, which
**instantiates the module afresh** (`new WebAssembly.Instance`, 0.2–0.4 ms: the 256 MiB linear memory is lazily mapped), runs
`run_checked`, reads the result through the same `../experimental/result.mjs` adapter, and posts exactly one reply carrying the
job id. The instance is unreachable when the handler returns. The worker survives to take the next job.

`residentd.mjs` puts a host behind a Unix socket or TCP port (length-prefixed JSON frames, per-connection pipelining, a cancel
frame per job id, a stats frame; a connection's close aborts its in-flight jobs; it listens only after every worker has announced
itself). `client.py` is a client that is not Node, so the per-job span it measures contains no Node startup on the client side.

Every result says what produced it: `module_sha256`, `worker: {id, jobs}` (which warm worker, how many jobs it has served),
`fresh: {outputLength, interactions}` (what the instance reported before any input was written — zero on a genuinely fresh
instance), and `timing: {instantiate_ms, run_ms, read_ms}` (the host's own reduction costs, which the one-shot host never exposed
and the witness's `spans.json` listed as not measured).

## 2. The one honest change of contract: `jobRetired`, not `workerExited`

The one-shot host returns every admitted result with `workerExited: true`, because its worker exits after each job and the exit is
the barrier proving the guest can neither run on nor reply again. HyperSurface forwards "only a candidate with `workerExited:
true`". On the resident host's warm path the worker does not exit. Saying `workerExited: true` there would be a lie, so the result
says **`workerExited: false, jobRetired: true`**: the reply was posted by the worker after `run_checked` returned, the job id is
retired, and a later message under that id changes nothing (R1 in the harness, and the `accept-foreign-job-id` control). Where a
worker actually is terminated — deadline, cancellation, worker error or exit — `workerExited: true` appears only after
`terminate()` resolved; if it throws, the result is `indeterminate` and the pool is one worker smaller (`stats.unconfirmed`), not
"cleaned up". A consumer that holds the one-shot contract must decide whether a retired job id is an acceptable barrier for it;
this file cannot make that decision (§6).

## 3. Ownership, invalidation, cancellation, resource boundaries (the plan's four requirements for reuse)

- **Ownership.** The process that constructs the host owns its workers and is the only thing that can post to them; `close()`
  terminates every worker and cancels every queued job. In the service, the daemon process owns the host; a guardian that owns the
  daemon (as `node-guardian` owns the one-shot Node child today) owns everything under it by the same PDEATHSIG mechanism,
  unchanged. Requests own nothing: they choose only their input.
- **Invalidation.** The module is read and its digest checked once, at construction; every result carries `module_sha256`, so a
  receipt can name the module that reduced it. A repinned module is a new process — there is no reload path, on purpose.
  Guest state is invalidated per job by construction (a fresh instance); the `fresh` witness is the observable, and the
  `reuse-instance` control shows the harness sees the difference (§5).
- **Cancellation.** An `AbortSignal` (in the service: a cancel frame, or the connection closing). A queued job leaves the queue
  and answers `cancelled` without touching a worker (C1). A running job's worker is terminated, its exit awaited, and it is
  replaced (C2, observed on the worker's own `exit` event). A deadline is the same path (D1, on a real noncooperating Wasm loop,
  the parent staying responsive throughout). A late reply after the deadline is a deadline (L1), by an independently checked clock.
- **Resource boundaries.** `pool` live workers (each a V8 isolate, ~10–20 MB resident), `maxQueue` waiting jobs, then
  `refused: busy` (Q1; over the wire, S2). Each job reserves a 256 MiB linear memory that V8 releases when the instance is
  collected; over 2,000 sequential jobs on one worker `VmSize` oscillated between 26 and 43 GB of reservation and `VmRSS` stayed
  at 108–144 MB (the smoke run of 2026-09-18 08:0x; not asserted by the harness). No CPU, RSS or kernel-memory limit is claimed,
  and Worker `resourceLimits` are not advertised as Wasm enforcement — exactly the one-shot host's position.

## 4. Measured: the executor span, four ways (`spans.py` → `results-resident.json`; laptop, shared host, load 1.2–1.4)

60 jobs per row (30 for the process-per-job floor), Node 25.2.1, pool 8. Every candidate on every row hashes to the recorded
payload digest with the recorded interaction count (`2318bd82…`/476 for the sealed 30-relay world; `aa092c17…`/131,268 for
`exp 2^16`). Latency is per job, request to result, from the caller's side.

| term | row | p50 ms | p99 ms | jobs/s | host `run_ms` p50 |
|---|---|---:|---:|---:|---:|
| chain30-epoch-1 (8,850 B, 476 itr) | floor: a Node process per job (`cli.mjs`, the shape of `reduce-file.mjs`) | **58.3** | 66.4 | — | — |
| | one-shot host in-process, a Worker per job (lab §11's shape), C=1 | 25.5 | 26.5 | 40 | — |
| | same, C=8 | 33.7 | 46.4 | 226 | — |
| | **resident, in-process, C=1** | **1.06** | 2.45 | 1,003 | 0.38 |
| | resident, in-process, C=8 | 2.98 | 9.49 | 2,034 | 1.67 |
| | **resident over a Unix socket from Python, C=1** | **1.41** | 2.46 | 736 | 0.46 |
| | same, C=8 | 3.30 | 15.2 | 1,485 | 1.04 |
| exp 2^16 (393 B, 131,268 itr, 262 KB output) | floor: a Node process per job | 63.1 | 71.9 | — | — |
| | one-shot host in-process, C=1 / C=8 | 28.1 / 36.3 | 29.6 / 47.9 | 35 / 213 | — |
| | resident, in-process, C=1 / C=8 | **2.80** / 6.55 | 4.52 / 14.7 | 313 / 984 | 2.03 / 4.08 |
| | resident over the socket from Python, C=1 / C=8 | 4.73 / 13.5 | 6.46 / 30.3 | 204 / 521 | 2.82 / 5.43 |

Reading, in the witness's terms: of the 64 ms executor span, the resident host leaves **~1.1 ms in-process or ~1.4 ms over a
socket** for the sealed world — the reduction (0.4 ms), a fresh instance (0.35 ms), and transfer. The 56 ms of Node startup and
the ~19 ms of Worker spawn are gone; nothing was done to the reduction itself. On the 262 KB-output control the socket path pays
~2 ms more than in-process for JSON-encoding the output twice, which is the wire format's cost, not the host's. At C=8 on 8 warm
workers the sealed world runs at ~2,000 jobs/s in-process; `run_ms` rises from 0.38 to 1.67 ms because eight isolates share the
cores with the Claude app and everything else on this laptop — a development reading, as the load average says. The same
computation on the same engine at ~1 ms means the executor span would no longer dominate the witness's 67 ms round trip: the
~2.6 ms boundary and the ~8 ms of guardian and bridge would.

## 5. Harness and controls

`node --test --test-isolation=none --test-force-exit resident.test.mjs residentd.test.mjs` — 15 + 4 cases, ~8 s:

| case | establishes |
|---|---|
| I1 | every one of the 26 oracle-corpus terms reduces on the resident host exactly as on the one-shot host, on a fresh instance |
| I2 | the three sealed worlds (`fixtures/`, identities copied from `wek/b2/compute/nf_identities.json`) reduce to their recorded payload digests and interaction counts |
| F1 | a job after a 476-interaction job on the same warm worker sees zero output and zero interactions before its input is written |
| X1, P1 | 26 distinct terms on 4 workers each return to their own requester; 200 jobs on 4 workers, every one on a fresh instance, the workers' counters summing to 200 |
| E1 | pre-dispatch refusals (limit, encoding, type, signal, pre-aborted) create no job |
| D1 | the deadline terminates a real noncooperating Wasm loop; the worker's exit is observed; the parent stayed responsive; the pool heals with a real worker |
| C1, C2 | cancellation of a queued job (no worker touched) and of a running one (worker observed exiting, replaced) |
| Q1 | the queue bound: `busy` beyond it; `close()` cancels what waited and refuses afterwards |
| W1 | a worker that exits without replying is a typed failure with a confirmed exit, and is replaced |
| L1 | a reply after the deadline is a deadline even when the timer callback was delayed |
| R1 | a reply with a foreign or retired job id changes nothing |
| U1 | an unconfirmed exit is `indeterminate`, shrinks the pool, and is not counted as replaced; with no worker left, requests are refused `exhausted` |
| M1 | a substituted module is refused before compilation |
| S1–S4 | through the socket: identity with host timing exposed; pipelining with the pool+queue bound refusing the overflow; a cancel frame, a duplicate id and a malformed request; the stats frame, and a closed connection aborting its jobs with the pool whole again |

`bash controls/run-controls.sh` → `controls/SUMMARY.txt`. Seven textual mutants over a copy of this directory; a patch that does
not apply exactly once is a refusal. Every one turned exactly the cases it was written to flip:

```
control=unmutated                       15 pass, 0 fail                                → GREEN
control=no-terminate-on-deadline        failing: C2,D1,L1,U1   expected: C2,D1,L1,U1   → RED-AS-EXPECTED
control=no-replace-after-confirmed-exit failing: C2,D1,W1      expected: C2,D1,W1      → RED-AS-EXPECTED
control=late-reply-accepted             failing: L1            expected: L1            → RED-AS-EXPECTED
control=unbounded-queue                 failing: Q1            expected: Q1            → RED-AS-EXPECTED
control=reuse-instance                  failing: F1,I1,P1,X1   expected: F1,I1,P1,X1   → RED-AS-EXPECTED
control=skip-digest-check               failing: M1            expected: M1            → RED-AS-EXPECTED
control=accept-foreign-job-id           failing: R1            expected: R1            → RED-AS-EXPECTED
```

Two things the controls taught, recorded rather than smoothed: the deadline mutant is caught by four cases, not the one it was
aimed at, because L1 and U1 assert the terminate call itself — that is the right shape (a check that terminate happened, made
three ways), not a control "flipping cases it is not about"; and `reuse-instance` flips every case that asserts the `fresh`
witness (four), which says the freshness discipline is asserted wherever a result is inspected, not in one place. Before the
first control run, C2 did not observe the worker's exit and Q1/M1 leaked a worker on their failure path so a mutant hung the
runner for three minutes; both were harness defects, fixed (`--test-force-exit` is now belt and braces).

**What the `fresh` witness is and is not.** It is the guest's own `output_length()` and `last_interactions()` read by the trusted
worker after instantiation and before input. Under instance reuse it carries the previous job's 476; on a fresh instance it is 0.
It is computed from guest state, not asserted by a boolean, but the worker that reads it is in the host TCB like all of
`host.mjs`. A stronger witness (a semantic difference in output caused by leaked state) does not exist for this guest, because the
checked ABI resets per run by design; the discipline is therefore a discipline, witnessed as well as it can be.

## 6. What HyperSurface would have to admit to use it (a proposal for Codex, nothing changed in `super/`)

Today: guardian → `node reduce-file.mjs host.mjs term` per job; the guardian owns the Node child; cancel/deadline = a stop byte →
SIGKILL → `Child.wait` = confirmed absence; the bridge forwards only a reaped child's `candidate` with `workerExited: true`.

With a resident host, the smallest coherent change:

1. The guardian starts **`residentd.mjs` once** (same ownership, PDEATHSIG, output bound) and speaks the frame protocol over the
   child's stdio or a Unix socket the guardian creates. One job = one `{id, term}` frame; the reply is the host's result object.
2. **Per-job cancel = a cancel frame**, answered `cancelled` with `workerExited: true` after the worker's terminate resolved.
   That witness is the host's word, not the kernel's. Where the bridge needs the kernel's witness (a lost reply, an
   `indeterminate`, a deadline the host did not answer), the existing path stands: stop byte → SIGKILL → `Child.wait` — which
   loses the warm pool and keeps the proof. The bridge would decide between the two by what it observed, as it does today.
3. **The forward rule** admits `candidate` with `jobRetired: true` from a live resident child, or with `workerExited: true` after
   a terminate. Both carry `module_sha256`; the receipt allowlist for `trvm.reduce` could carry `worker` and `timing` too, since
   they are the host's own account of the job (the reference gate remains the only honesty check, as F-D established).
4. **Replacement** (F-X in HyperSurface's `replacement_test.exs`) is unchanged in kind: the resident child is the executor; a
   replaced executor is a new child with an empty pool.

Not proposed: pooling across Carriers, sharing a resident host between bridges, any change to Landlock/seccomp (Node still needs
threads), or pinning the daemon inside the current Carrier profile. Whether the loss of the per-job kernel witness on the
warm path is acceptable for `local_mutate` effects is the question §2 leaves for the owner.

## 7. Dependencies this directory has on files another lane owns

`../ic32_checked.wasm` (sha256 `0cf96179…`, the pinned module), `../experimental/result.mjs` (`4bf62f84…`, the ABI v2 result
adapter) and, for the identity harness, `../experimental/host.mjs` (`64d07630…`) and `oracle-corpus.json`. As of 2026-09-18 those
files are **uncommitted in TRVM** — they belong to the checked-host lane, which also holds `ic32_wasm.c` and `build-checked.sh`
uncommitted — so this directory is committed against files whose bytes are recorded here but whose history is not yet in git.
`fixtures/identities.json` records where its three sealed-world identities came from.

## 8. Reproduce

```bash
cd TRVM/runtime/wasm/resident
node --test --test-isolation=none --test-force-exit resident.test.mjs residentd.test.mjs   # 19/19
TMPDIR=~/.cache/resident-tmp bash controls/run-controls.sh                                 # ALL CONTROLS AS EXPECTED
python3 spans.py --jobs 60 --pool 8                                                        # results-resident.json
node residentd.mjs --socket /tmp/r.sock --pool 4 &  python3 client.py /tmp/r.sock fixtures/chain30-epoch-1.ic 200 4
```
