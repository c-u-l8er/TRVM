// The resident reducer host: the pinned checked IC32 module loaded ONCE into a long-lived process, a pool of
// warm worker threads, and a FRESH WebAssembly instance for every reduction. It removes the two fixed costs the
// one-shot host pays per job (Node startup ~56 ms, Worker spawn ~19 ms on this laptop) and keeps everything else
// the one-shot host established: the module digest is pinned at construction, requests choose nothing but their
// input, input/output bounds are checked before copying, a deadline TERMINATES the worker and the exit is awaited
// before the slot is reused, a late reply cannot beat an expired deadline, and an unconfirmed exit shrinks the pool
// rather than being described as cleaned up.
//
// What changes, and is said on every result: on the warm path the worker does NOT exit after a candidate. The
// barrier is the job id being retired (`jobRetired: true`, `workerExited: false`); `workerExited: true` appears only
// where a worker was actually terminated and its exit confirmed. A consumer holding the one-shot contract
// ("only a candidate with workerExited: true") has to admit `jobRetired` — that is an interface decision for the
// consumer's owner, not something this file can make for it.
//
// Ownership: whoever constructs the host owns its workers; `close()` terminates them all. Invalidation: the module
// digest is on every result (`module_sha256`), so a receipt can say which module reduced it; a repinned module
// needs a new process. Cancellation: an AbortSignal — queued jobs leave the queue, running jobs are terminated and
// the worker replaced. Resource boundaries: `pool` live workers (each a V8 isolate; each job a 256 MiB linear
// memory reservation until the instance is collected), `maxQueue` waiting jobs, then `refused: busy`. No CPU, RSS or
// kernel-memory limit is claimed, exactly as for the one-shot host.
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { Worker } from 'node:worker_threads';
import { performance } from 'node:perf_hooks';

// The same pin as ../experimental/host.mjs; a different module is refused before compilation.
export const DIGEST = '0cf96179ac7063f85691834b84c9e4e01f5a855ace8678f6752315a6f15fed95';
export const LIMITS = Object.freeze({ inputBytes: 65536, outputBytes: 1048576, deadlineMs: 1000, maxInteractions: 50000000 });
export const DEFAULTS = Object.freeze({ pool: 4, maxQueue: 16 });

export function loadModule(url = new URL('../ic32_checked.wasm', import.meta.url)) {
  const bytes = readFileSync(url);
  const digest = createHash('sha256').update(bytes).digest('hex');
  if (digest !== DIGEST) throw Error('module-digest-mismatch');
  const module = new WebAssembly.Module(bytes);
  if (WebAssembly.Module.imports(module).length) throw Error('module-imports-refused');
  return { module, digest };
}

export function createResidentHost(options = {}) { return new ResidentHost(loadModule(options.moduleUrl), options); }

const WORKER_URL = new URL('./resident-worker.mjs', import.meta.url);

export class ResidentHost {
  #module; #digest; #pool; #maxQueue; #deadlineMs; #createWorker;
  #workers = new Set(); #idle = []; #queue = []; #closed = false;
  #nextWorkerId = 1; #nextJobId = 1; #readyWaiters = [];
  #stats = { spawned: 0, replaced: 0, unconfirmed: 0, served: 0, refusedBusy: 0, deadlines: 0, cancelled: 0 };

  constructor({ module, digest }, { pool = DEFAULTS.pool, maxQueue = DEFAULTS.maxQueue, deadlineMs = LIMITS.deadlineMs, createWorker } = {}) {
    if (!Number.isInteger(pool) || pool < 1 || !Number.isInteger(maxQueue) || maxQueue < 0) throw Error('pool-options');
    if (!Number.isFinite(deadlineMs) || deadlineMs <= 0 || deadlineMs > LIMITS.deadlineMs) throw Error('deadline-option');
    this.#module = module; this.#digest = digest; this.#pool = pool; this.#maxQueue = maxQueue; this.#deadlineMs = deadlineMs;
    // Trusted construction seam (fault tests). A request can never reach it.
    this.#createWorker = createWorker ?? (() => new Worker(WORKER_URL, { workerData: { module }, env: {}, execArgv: [] }));
    for (let i = 0; i < pool; i++) this.#spawn();
  }

  get digest() { return this.#digest; }

  // Resolves once every live worker has announced itself (jobs submitted earlier simply queue until then).
  ready() { return new Promise(resolve => { this.#readyWaiters.push(resolve); this.#checkReady(); }); }
  #checkReady() {
    if ([...this.#workers].some(w => !w.ready)) return;
    for (const r of this.#readyWaiters.splice(0)) r(this.stats());
  }

  stats() {
    const busy = [...this.#workers].filter(w => w.job).length;
    return { ...this.#stats, pool: this.#pool, live: this.#workers.size, idle: this.#idle.length, busy, queued: this.#queue.length, closed: this.#closed };
  }

  #spawn() {
    let worker;
    try { worker = this.#createWorker(); } catch { return null; }
    const w = { id: this.#nextWorkerId++, worker, jobs: 0, job: null, ready: false, dead: false };
    this.#stats.spawned++;
    this.#workers.add(w);
    worker.on('message', m => this.#onMessage(w, m));
    worker.on('error', () => this.#onDeath(w, { status: 'failed', reason: 'worker-error' }));
    worker.on('exit', () => this.#onDeath(w, { status: 'failed', reason: 'worker-exit-without-result' }));
    return w;
  }

  #onMessage(w, m) {
    if (m?.ready === true && !w.ready) { w.ready = true; this.#release(w); this.#checkReady(); return; }
    if (!w.job || m?.id !== w.job.id) return; // a reply for a retired or foreign job id changes nothing
    const { id, ...result } = m;
    // Independently checked clock: a late reply cannot beat an expired deadline even if the timer was delayed.
    if (performance.now() >= w.job.expires) w.job.settle({ status: 'deadline' }, true);
    else w.job.settle({ ...result, workerExited: false, jobRetired: true }, false);
  }

  #onDeath(w, failure) {
    if (w.dead) return;
    w.dead = true;
    if (w.job) w.job.settle({ ...failure }, true);
    else { this.#workers.delete(w); this.#idle = this.#idle.filter(x => x !== w); if (!this.#closed) { this.#stats.replaced++; this.#spawn(); } }
  }

  #release(w) {
    if (this.#closed || w.dead) return;
    const next = this.#queue.shift();
    if (next) { next.detach(); this.#dispatch(w, next); }
    else this.#idle.push(w);
  }

  async reduce(input, { signal } = {}) {
    if (typeof input !== 'string') return { status: 'refused', reason: 'input-type' };
    if (input.length > LIMITS.inputBytes || Buffer.byteLength(input) > LIMITS.inputBytes) return { status: 'refused', reason: 'input-limit' };
    if (!input.length || input.includes('\0') || !input.isWellFormed()) return { status: 'refused', reason: 'input-encoding' };
    if (signal !== undefined && !(signal instanceof AbortSignal)) return { status: 'refused', reason: 'signal-type' };
    if (signal?.aborted) return { status: 'cancelled' };
    if (this.#closed) return { status: 'refused', reason: 'closed' };
    if (this.#workers.size === 0) return { status: 'refused', reason: 'exhausted' }; // every worker's exit went unconfirmed
    const job = { input, signal, id: this.#nextJobId++ };
    const done = new Promise(resolve => { job.resolve = resolve; });
    const w = this.#idle.pop();
    if (w) this.#dispatch(w, job);
    else if (this.#queue.length < this.#maxQueue) {
      const onAbort = () => { this.#queue = this.#queue.filter(j => j !== job); this.#stats.cancelled++; job.resolve({ status: 'cancelled' }); };
      job.detach = () => signal?.removeEventListener('abort', onAbort);
      signal?.addEventListener('abort', onAbort, { once: true });
      this.#queue.push(job);
    } else { this.#stats.refusedBusy++; return { status: 'refused', reason: 'busy' }; }
    return done;
  }

  // One job on one warm worker. The worker instantiates the module afresh, reduces, and posts exactly one reply
  // for this id. Anything but that reply before the deadline — the deadline itself, cancellation, a worker error
  // or exit — is a termination path: the worker is terminated, its exit awaited, and only then is the result
  // returned and a replacement spawned.
  #dispatch(w, job) {
    w.job = job;
    job.expires = performance.now() + this.#deadlineMs;
    let chosen = false, timer, onAbort;
    job.settle = (value, terminate) => {
      if (chosen) return; chosen = true;
      clearTimeout(timer); job.signal?.removeEventListener('abort', onAbort);
      this.#finish(w, job, value, terminate);
    };
    onAbort = () => { this.#stats.cancelled++; job.settle({ status: 'cancelled' }, true); };
    job.signal?.addEventListener('abort', onAbort, { once: true });
    timer = setTimeout(() => { this.#stats.deadlines++; job.settle({ status: 'deadline' }, true); }, this.#deadlineMs);
    w.worker.postMessage({ id: job.id, input: job.input, outputBytes: LIMITS.outputBytes, maxInteractions: LIMITS.maxInteractions });
  }

  async #finish(w, job, value, terminate) {
    w.job = null; w.jobs++;
    const base = { module_sha256: this.#digest, worker: { id: w.id, jobs: w.jobs } };
    if (!terminate) { this.#stats.served++; job.resolve({ ...value, ...base }); this.#release(w); return; }
    // A termination path. The worker is gone from the pool either way; whether it is REPLACED depends on the exit
    // being confirmed. If termination cannot complete, the pool is one worker smaller and says so.
    this.#workers.delete(w); this.#idle = this.#idle.filter(x => x !== w);
    w.dead = true; // before terminate: the worker's own exit event must not count as a second death
    let exited;
    try { await w.worker.terminate(); exited = true; }
    catch { exited = false; }
    if (exited) { if (!this.#closed) { this.#stats.replaced++; this.#spawn(); } job.resolve({ ...value, ...base, workerExited: true }); }
    else { this.#stats.unconfirmed++; job.resolve({ status: 'indeterminate', reason: 'worker-exit-unconfirmed', ...base, workerExited: false }); }
  }

  // Terminates every worker; queued jobs are cancelled, running jobs are terminated. Resolves when every
  // termination has settled; the stats say how many exits were confirmed.
  async close() {
    if (this.#closed) return this.stats();
    this.#closed = true;
    for (const j of this.#queue.splice(0)) { j.detach?.(); this.#stats.cancelled++; j.resolve({ status: 'cancelled' }); }
    const settled = [];
    for (const w of [...this.#workers]) {
      if (w.job) { const p = new Promise(r => { const prev = w.job.resolve; w.job.resolve = v => { prev(v); r(); }; }); this.#stats.cancelled++; w.job.settle({ status: 'cancelled' }, true); settled.push(p); }
      else { w.dead = true; settled.push(w.worker.terminate().then(() => { this.#workers.delete(w); }, () => { this.#stats.unconfirmed++; })); }
    }
    this.#idle = [];
    await Promise.all(settled);
    return this.stats();
  }
}
