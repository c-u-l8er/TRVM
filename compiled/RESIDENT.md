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

| world | one-shot (a process per job) | resident, in-process C=1 | over a Unix socket C=1 | vs the floor |
|---|---:|---:|---:|---:|
| **chain30** (the witness's world) | **74.66 ms** | **0.17 ms** | 0.36 ms | **439×** |
| golden-demo (9.5 MB term) | 68.17 | **0.20** | 0.43 | 341× |
| spinner-w33-n16 (46 MB term) | 68.58 | **0.23** | 0.53 | 298× |
| chain120 | 75.08 | **0.36** | 1.09 | 209× |

**The span is flat and small across every world** — 0.17–0.36 ms, where the one-shot kind was ~82 ms flat. That is
the same shape of finding twice over: a flat number is a number dominated by something other than the work. It was
82 ms flat because Python was starting; when this host was first built it was 0.95–3.61 ms and the spread was the
Python *reader*; with `README.md` §2l's C reader in place both are gone.

**A development reading on a shared laptop, not a benchmark.** `BENCHMARK_LANE.md` §1's B2/B3 split applies here
exactly as it applies to the battery's timing columns.

### 4b. What now dominates, and it is no longer anything this host can remove

When this host was first built the answer was the reader: **86–93 % of a warm job was `ic_ref.parse`** reading the
previous payload back in. That is what `README.md` §2l went and fixed, in both directions — the state text and the
epoch control — and the table above is the result. The phases now (p50, µs):

| world | prepare | **object check** | decode (both inputs) | step | render | host total |
|---|---:|---:|---:|---:|---:|---:|
| chain30 | 0.5 | **25.7** | 13.1 | 1.5 | 5.5 | 91.0 |
| golden-demo | 0.6 | **27.5** | 18.3 | 1.4 | 6.0 | 103.9 |
| spinner-w33-n16 | 0.5 | **27.2** | 22.7 | 1.3 | 7.9 | 126.1 |
| chain120 | 0.8 | **35.1** | 27.1 | 1.8 | 12.4 | 173.6 |

**The per-job `.so` re-hash is now the single largest phase**, and it stays. It is F-B, and residency must not mean
checking an object once and trusting it forever (§3, B2). The gap between the phases and the host total is the
worker's own frame handling — base64 and JSON — which is the transport's cost, not the executor's. `step_us` fell
from 14.9 µs to 1.5 for a reason worth stating: it used to include `CompiledStep.encode` turning a state dict into
slots, and there is no dict on this path any more — the reader hands the step its vector directly.

## 5. Harness and controls

`python3 -B resident_test.py` — **28 cases, ~13 s** (the table below is the original 24; §7 lists the four added 2026-09-23 and the one rewritten):

| case | establishes |
|---|---|
| I1 | chain30 epoch 1 warm still renders to `2318bd82…`/3,260 B, the vertical witness's golden receipt |
| I2 | four worlds: every **field** of the warm candidate equals the one-shot candidate's, not merely the digest |
| (both) | every case above also passes under `TRVM_READER_CHECK=1`, which runs the C reader and the Python decoder on **every** job and refuses on disagreement |
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

## 7. Lifecycle, settled against a consumer (2026-09-23)

The checkpoint after Super's client first ran this daemon (`wek/b2/trvm/RESIDENT_LIFECYCLE.md`, the consumer's
record) asked for cancellation, deadlines, worker death, queued cancellation, races, connection loss and safe
replacement — through Super's actual client, with the daemon's word on each. Building those cases found **three
defects in this host** and one naming choice, each fixed where it lives and each with a harness case that goes red
on the defect:

| found | what was wrong | fix | case |
|---|---|---|---|
| a queued job's cancel was bounded by **someone else's work** | `_acquire` waited on the condition with no look at the cancel flag, so a queued job's cancel was honoured only when a worker freed — with the one worker held by a running job, not until *that* job's deadline (10 s by default). A client with a 3 s cancel bound gave up and reported the stop unconfirmed for a job that had never touched a worker. | `_acquire(…, cancel)` wakes in 50 ms slices while a cancel is possible and returns `cancelled`; the reply is `cancelled/queued/workerExited:false` and counts `cancelled_queued` | C2, S6 |
| a **replacement worker was listed idle twice** | `_spawn` appended the new worker to `_idle`, then `_retire` released it again after its announce. On a pool of one, two concurrent jobs after any replacement were both dispatched to the same worker; each parent thread read the other's reply, `foreign-job-id`, and the worker was killed for answering out of order. Visible from outside as `stats()` reporting `idle: 2, live: 1`. | `_spawn(idle=False)` for a replacement; it is idle only once it has announced itself | D1 (books), D2 (two concurrent jobs after a replacement, both candidates, nothing killed) |
| **SIGTERM ended the daemon without ending its workers** | `finally` never ran; an idle worker exited on EOF, a HELD one did not, and a worker that had already died stayed a zombie of a parent that no longer waited. Found by the consumer's teardown, which asserts confirmed absence and named exactly such a zombie. | TERM takes ^C's road: the loop ends and `HOST.close()` SIGKILLs and `waitpid`s every worker | every S case's teardown |
| `worker-read` named the **symptom**, not the cause | a worker killed with unread input on its socket answers the parent with a reset rather than EOF, so the same death was `worker-exited` or `worker-read` depending on which the kernel chose | when the exit is confirmed and the read failed with an `OSError`, the reason is `worker-exited`; `worker-read` is kept for a frame this parent could not read from a worker whose exit was not what ended the read | W1 (rewritten: the worker now dies **under** a dispatched job; W2 is the idle death) |

And one addition: an **idle worker that died on its own** is found at dispatch — `poll()`, which is also the reap —
and replaced before any job is written to the corpse (`died_idle`), rather than by the next job failing. `stats()`
now carries `worker_pids`, so a consumer can tell replacement from survival by pid rather than by count, and the
counters `cancelled_queued`, `cancelled_running`, `died_idle`.

**The reply shapes, as a consumer must match them** (this is the table Super's client now encodes, by name):

| reply | means | witness |
|---|---|---|
| `candidate` · `jobRetired:true` · `workerExited:false` | the warm path; the worker is alive and this id is retired | the worker's own reply after `run` returned |
| `cancelled` · `stage:running` · `workerExited:true` · `killed_confirmed:true` | the running job's worker was SIGKILLed and reaped | `waitpid` returned |
| `cancelled` · `stage:queued` · `workerExited:false` | the job left the queue; **no worker ever took it** — there is no exit to report and none may be demanded | the pool's own bookkeeping; `worker_pids` unchanged |
| `refused` · `reason:deadline` · `workerExited:true` · `killed_confirmed:true` | the host's own deadline killed and reaped the worker | `waitpid` returned |
| `failed` · `reason:worker-exited` · `workerExited:true` | the worker died under the job; its owner reaped it | `waitpid` returned |
| `refused` · `reason:request-mismatch` / `plan-not-bound` / … · `jobRetired:true` | the worker refused, and stays alive | its own reply |
| `indeterminate` (or `indeterminate:true` on any of the above) | the host asked and `waitpid` did not return in its bound; the pool is one worker smaller | **none** — and that is the point |

A closed connection is none of these: it is the absence of a reply, and it says nothing about the worker. Measured
on the consumer's side by killing the daemon under a held job — every socket closed, and the native worker was still
alive.

Harness: **28 cases** (`resident_test.py`), plus the seven mutant controls unchanged.

## 8. Reproduce

```bash
cd TRVM/compiled
PYTHONDONTWRITEBYTECODE=1 python3 -B resident_test.py                        # 28 cases, ~13 s
PYTHONDONTWRITEBYTECODE=1 python3 -B controls/run_resident_controls.py       # seven mutants, ~3 min
PYTHONDONTWRITEBYTECODE=1 python3 -B resident_spans.py --jobs 40             # the table above, ~2 min
PYTHONDONTWRITEBYTECODE=1 python3 -B residentd.py --socket /tmp/rc.sock --pool 4   # the daemon
```
