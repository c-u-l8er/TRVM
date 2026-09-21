# The resident compiled host — the built `.so`, the sealed plan and the printer held across jobs

**2026-09-20.** B5 measured the compiled `trvm.reduce` executor kind at **82 ms p50, flat on both chain30 and the
9.5 MB Golden demo**, because the step is 10–60 µs and everything else is Python starting and Forge importing.
`wek/b2/trvm/COMPILED_EXECUTOR_PROPOSAL.md` §6 had predicted exactly that — *"As a process per job, the compiled
kind buys nothing"* — and said the kind pays off only inside an executor that stays resident. This is that executor,
built in TRVM's lane with its **ownership, invalidation, cancellation and resource boundaries** stated rather than
assumed, and measured.

Status: **BUILT, MEASURED on the shared laptop (a development reading), harness 24/24, seven mutant controls each
turning exactly the cases it was written to flip.** Not claimed: any Super integration, confinement, external
reproduction, or a production throughput figure.

**It is not wired into Super, and §6's ruling is still Travis's.** That ruling — whether a retired job id is an
acceptable barrier for `local_mutate` on a resident host — gates *HyperSurface admitting* a resident host, not TRVM
building one. The resident **Wasm** host (`../runtime/wasm/resident/`) was built, measured and tested in this lane
under exactly that open question and says so in its own README §6. This is the same position, and §6 says the two
questions are the same question: *"if a retired job id is an acceptable barrier … it is the same question for a
resident compiled host."*

## 1. What it is

`resident.py` exports `ResidentCompiledHost(pool, max_queue, emitter)` → `submit(bundle, deadline_s=, cancel=)`,
taking the **same bundle** the one-shot executor's fixed-argv form takes and returning the **same candidate**. It is
a pool of worker **processes**; each holds `executor.prepare`'s result — the D22-sealed plan, the plan view, the
built `.so` and the `CanonicalPrinter` — keyed by the sha256 of the exact plan bytes, and runs **`executor.run`
itself**, not a copy of it. The checks are the same lines on the warm path as on the cold one; that is the whole
design, and §2k's lesson (two spellings of one rule, and the one that disagreed was wrong) is why.

`residentd.py` puts a host behind a Unix socket or TCP port: 4-byte big-endian length + UTF-8 JSON frames, the
framing `residentd.mjs` uses, with per-connection pipelining, a cancel frame per job id, a stats frame, and a
connection close that aborts its in-flight jobs. It listens only after every worker has announced itself, and it
prints the port the kernel **bound**, so `--port 0` is usable.

Workers are **spawned**, not forked: the parent is threaded by construction, and a fork from a threaded parent
inherits whatever locks were held at the instant of the fork. A spawn costs ~50 ms of Python and Forge import, paid
once per worker and once more when a killed worker is replaced.

## 2. The contract word, said as plainly as the Wasm host says it

On the warm path the worker does not exit, so a result says **`workerExited: false, jobRetired: true`** — the reply
was written after `run` returned, the job id is retired, and a later frame under that id changes nothing. Where a
worker really was killed (deadline, cancel, or a worker that died on its own) **`workerExited: true` appears only
after `waitpid` returned**; if the reap cannot be confirmed the result is `indeterminate` and the pool is one worker
smaller, not "cleaned up". A consumer holding the one-shot contract has to decide whether a retired job id is an
acceptable barrier for it. This host cannot make that decision either.

## 3. The four boundaries

- **Ownership.** The constructing process owns its workers and is the only thing that writes to them. `close()`
  kills every worker and refuses afterwards. A worker is a separate address space, which is what lets its `.so`
  cache be owned by its own Carrier rather than shared — §6's first "harder here".

- **Invalidation, and it is STRONGER here than on the Wasm host.** The Wasm host must build a fresh instance per
  job because its guest owns 256 MiB of linear memory, and it *witnesses* freshness by reading the guest's counters.
  **The compiled step has no guest state to carry**: `step_v6(const i64 *st, const i64 *ctl, i64 *out)` is a pure
  function over three caller-owned buffers. There is no instance, nothing to reset, and nothing to witness as reset.
  That is **checked, not asserted** — `no_writable_state()` reads the object's symbol table and refuses any mutable
  object that is not named C-runtime scaffolding, over **19 worlds × both C emitters** (N1). It is checked by
  *symbol* because the object does carry 16 writable bytes — `__dso_handle` and the run-once destructor guard
  `completed.0`, which gcc emits for every shared object — and the first version of the check, which looked at
  *sections*, reported them and was right to. Widening a section skip-list to tolerate those would also tolerate a
  `static long` the emitter might one day grow; N1b hands the same compiler exactly that and watches the check
  refuse it. The `.so` is content-addressed by its source sha256, so a repinned emitter is a different object and a
  different `backend_id` — there is no reload path, on purpose — and `executor.check_object` re-checks the file
  against the identity recorded beside it **per job, on the warm path too** (B1, B2).

- **Cancellation, the one that is genuinely harder here — §6's second.** A native step cannot be interrupted: there
  is no `Worker.terminate()` and no abort check inside someone else's compiled loop. **SIGKILL then `waitpid` is the
  only witness**, and it costs the worker. A deadline or a cancel on a *running* job kills that worker, reaps it
  (`killed_confirmed`, and the **return of the wait** is the witness — not the signal, which only asks), and
  replaces it; a *queued* job leaves the queue without touching a worker. A runaway step loses the pool one worker,
  exactly as §6 said it would.

- **Resource boundaries.** `pool` worker processes; `max_queue` may wait; beyond that `refused: busy`; with no
  worker left, `refused: exhausted`. No CPU, RSS or kernel-memory limit is claimed — the one-shot executor's and the
  Wasm host's position.

## 4. Measured (`resident_spans.py` → `results-resident-compiled.json`; laptop, shared host)

40 jobs per row (8 for the process-per-job floor), pool 8 on the concurrent rows. **Every row asserts the payload
digest**, so what is compared is the same computation. Latency is per job from the caller's side, queue wait
included; throughput is jobs divided by the wall time the batch took.

| world | one-shot (a process per job) | resident, in-process C=1 | over a Unix socket C=1 | in-process C=8 | socket C=8 |
|---|---:|---:|---:|---:|---:|
| **chain30** (the witness's world) | **66.03 ms** | **0.95 ms** | 1.49 ms | 13.71 ms · 1,936 j/s | 2.37 ms · 1,628 j/s |
| golden-demo (9.5 MB term) | 65.73 | **1.04** | 1.74 | 13.91 · 1,945 j/s | 2.54 · 1,678 j/s |
| spinner-w33-n16 (46 MB term) | 64.73 | **1.91** | 2.79 | 16.07 · 1,611 j/s | 3.64 · 1,274 j/s |
| chain120 | 73.72 | **3.61** | 5.14 | 33.54 · 824 j/s | 5.74 · 738 j/s |

**69× on chain30** in-process, 44× over the socket; and the span is no longer flat across worlds, which is itself
the point — once Python's startup is gone, what is left is proportional to the world. The C=8 rows trade latency for
throughput: eight jobs deep on eight workers, per-job latency is queue wait plus service, and throughput roughly
doubles. (`jobs_per_s` was briefly `len(lat)/sum(lat)` — the inverse of the mean latency, which is right only when
jobs do not overlap; it reported the C=8 rows as *slower* than C=1 while they were twice as fast. It is wall-clock.)

**A development reading on a shared laptop, not a benchmark.** `BENCHMARK_LANE.md` §1's B2/B3 split applies here
exactly as it applies to the battery's timing columns.

### 4b. What now dominates, and it is the mirror image of what the C printer fixed

Per-job phases on the warm path (p50, µs):

| world | prepare | object check | **decode (input)** | step | render (output) | total |
|---|---:|---:|---:|---:|---:|---:|
| chain30 | 0.9 | 36.0 | **699.5 (86 %)** | 14.9 | 6.0 | 817.4 |
| golden-demo | 0.9 | 34.7 | **826.2 (89 %)** | 9.4 | 6.2 | 928.8 |
| spinner-w33-n16 | 1.1 | 40.5 | **1,615.5 (92 %)** | 10.5 | 8.5 | 1,759.6 |
| chain120 | 1.2 | 50.0 | **3,130.4 (93 %)** | 39.1 | 12.8 | 3,379.7 |

**86–93 % of a warm job is `ic_ref.parse` reading the previous payload back in.** §2j took the *output* side from
33–4,602 µs to 3–22 µs with a C printer; the *input* side is still three Python conversions in the other direction
(canonical text → AST → state dict → slot vector). The step is 9–39 µs and the render 6–13 µs; everything else is
the reader. **A C reader — the printer's inverse, over the same four shapes and the same layout descriptor — would
take a warm job from ~1 ms to well under 100 µs**, and it is the same size of job the printer was. That is the next
build this hands on, and it was measured here rather than guessed.

## 5. Harness and controls

`python3 -B resident_test.py` — **24 cases, ~2 s**:

| case | establishes |
|---|---|
| I1 | chain30 epoch 1 warm still renders to `2318bd82…`/3,260 B, the vertical witness's golden receipt |
| I2 | four worlds: every **field** of the warm candidate equals the one-shot candidate's, not merely the digest |
| I3 | both C emitters, each reporting its own kind |
| N1 | no emitted object over 19 worlds × 2 emitters carries a mutable object of its own |
| N1b | the same compiler given a `static int64_t` is refused — a check that cannot fail is not a check |
| N2 | one warm worker holding four worlds at once; each answers its own bytes, interleaved, three rounds |
| X1/P1 | 48 concurrent jobs over 4 workers, each reply to its own requester, counters summing |
| E1–E4 | request-mismatch, plan-not-bound and a malformed bundle refuse warm exactly as cold, the worker survives, and a refusal says `jobRetired` rather than a pretend exit |
| B1, B2 | a stale object is refused, and the object check runs on **every** job, not once |
| C1 | a queued job is cancelled without touching a worker |
| D1 | a deadline kills the worker, `waitpid` **returns** (`killed_confirmed`), the pool heals with a real worker |
| W1 | a worker that died without replying is a typed failure with a confirmed exit, and is replaced |
| Q1, U1 | the queue bound refuses `busy`, `close()` refuses after, and with no worker left requests are `exhausted` |
| S0–S5 | over the socket: announce-after-ready, identity, pipelining, stats, a duplicate id, and a closed connection leaving the pool whole |

`python3 -B controls/run_resident_controls.py` → `controls/RESIDENT_SUMMARY.txt`. Seven textual mutants over a copy
of `compiled/`; **a patch that does not apply exactly once is a refusal**, because a mutant that silently failed to
apply is a control that proves nothing and reports GREEN.

```
control=unmutated                        GREEN
control=no-kill-on-deadline              failing: D1                    expected= D1              RED-AS-EXPECTED
control=no-replace-after-confirmed-exit  failing: D1,W1                 expected= D1,W1           RED-AS-EXPECTED
control=unbounded-queue                  failing: Q1                    expected= Q1              RED-AS-EXPECTED
control=worker-replies-wrong-id          failing: B2,D1,E1,E2,E3,E4,I1,I2,I3,N2,S1,S2,W1,X1  expected>= I1  RED-AS-EXPECTED
control=skip-object-check                failing: B1                    expected= B1              RED-AS-EXPECTED
control=writable-state-allowed           failing: N1b                   expected= N1b             RED-AS-EXPECTED
```

**Two things the controls taught, recorded rather than smoothed.** The first version of the runner copied `compiled/`
to a temp directory; the harness resolves `../forge` relative to itself, so **every run died on the import and every
control reported "failing: none"** — which is what a control that cannot fail looks like from the outside, and it
reported the unmutated copy as red, which is the only reason it was caught. The copy is now a sibling of `compiled/`
inside the TRVM tree. And `worker-replies-wrong-id` is the one control whose expectation is `>=` rather than `=`:
it breaks every case that submits a job at all, and pinning that exact list would pin an accident of which cases
happen to submit.

## 6. What HyperSurface would have to admit (a proposal, nothing in `super/` changed)

Today the guardian runs `python3 executor.py c BUNDLE` per job and forwards a reaped child's candidate. With a
resident host the smallest coherent change is the same shape the Wasm host's README §6 proposes: the guardian starts
**`residentd.py` once** (same ownership, PDEATHSIG, output bound), speaks the frame protocol over a Unix socket it
creates, and one job is one `{id, bundle_b64}` frame. What it must then decide is unchanged and is §6's open
question: **whether `jobRetired: true` is an acceptable barrier where `workerExited: true` is required today.** The
compiled kind's answer is not better than the Wasm kind's — it is the same answer, for the same reason.

Two things this host can say that the Wasm one cannot. **Invalidation is checked rather than witnessed** (§3): there
is no guest state, and `no_writable_state` proves it per object rather than inferring it from a counter. And the
`.so` cache is per-worker-process by construction, so §6's "owned by the executor's Carrier, not shared" is a
deployment choice (`TRVM_COMPILED_CACHE`) rather than a redesign.

## 7. Reproduce

```bash
cd TRVM/compiled
PYTHONDONTWRITEBYTECODE=1 python3 -B resident_test.py                        # 24 cases, ~2 s
PYTHONDONTWRITEBYTECODE=1 python3 -B controls/run_resident_controls.py       # seven mutants, ~3 min
PYTHONDONTWRITEBYTECODE=1 python3 -B resident_spans.py --jobs 40             # the table above, ~2 min
PYTHONDONTWRITEBYTECODE=1 python3 -B residentd.py --socket /tmp/rc.sock --pool 4   # the daemon
```
