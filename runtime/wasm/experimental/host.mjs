import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { Worker } from 'node:worker_threads';
import { performance } from 'node:perf_hooks';

const DIGEST = '0cf96179ac7063f85691834b84c9e4e01f5a855ace8678f6752315a6f15fed95';
export const LIMITS = Object.freeze({ inputBytes: 65536, outputBytes: 1048576, deadlineMs: 1000 });

// Trusted construction, never a request parameter. No fallback for another ABI.
export function createReducerHost() {
  const bytes = readFileSync(new URL('../ic32_checked.wasm', import.meta.url));
  if (createHash('sha256').update(bytes).digest('hex') !== DIGEST) throw Error('module-digest-mismatch');
  const module = new WebAssembly.Module(bytes);
  if (WebAssembly.Module.imports(module).length) throw Error('module-imports-refused');
  return new ReducerHost(module);
}

class ReducerHost {
  #module;
  #busy = false;
  constructor(module) { this.#module = module; }

  async reduce(input, { signal } = {}) {
    if (typeof input !== 'string') return { status: 'refused', reason: 'input-type' };
    // Bound the scan/allocation even for large strings before UTF-8 encoding.
    if (input.length > LIMITS.inputBytes || Buffer.byteLength(input) > LIMITS.inputBytes)
      return { status: 'refused', reason: 'input-limit' };
    if (!input.length || input.includes('\0') || !input.isWellFormed())
      return { status: 'refused', reason: 'input-encoding' };
    if (signal !== undefined && !(signal instanceof AbortSignal)) return { status: 'refused', reason: 'signal-type' };
    if (signal?.aborted) return { status: 'cancelled' };
    if (this.#busy) return { status: 'refused', reason: 'busy' };
    this.#busy = true;
    let result;
    try {
      result = await supervise(() => new Worker(new URL('./worker.mjs', import.meta.url), {
        workerData: { module: this.#module, input, outputBytes: LIMITS.outputBytes },
        env: {}, execArgv: [],
      }), LIMITS.deadlineMs, signal);
      return result;
    } finally { if (result?.workerExited !== false) this.#busy = false; }
  }
}

// Internal supervision seam for deterministic fault tests. A request cannot
// choose the worker, module or deadline. No result/slot is released until exit.
export async function supervise(makeWorker, deadlineMs, signal) {
  const expires = performance.now() + deadlineMs;
  let worker;
  try { worker = makeWorker(); } catch { return { status: 'failed', reason: 'worker-start' }; }
  let timer, abort;
  const result = await new Promise(resolve => {
    let chosen = false;
    const settle = value => { if (!chosen) { chosen = true; resolve(value); } };
    worker.once('error', () => settle({ status: 'failed', reason: 'worker-error' }));
    worker.once('exit', () => settle({ status: 'failed', reason: 'worker-exit-without-result' }));
    worker.once('message', message => {
      if (performance.now() >= expires) settle({ status: 'deadline' });
      else settle(message);
    });
    abort = () => settle({ status: 'cancelled' });
    signal?.addEventListener('abort', abort, { once: true });
    timer = setTimeout(() => settle({ status: 'deadline' }), Math.max(0, expires - performance.now()));
    if (signal?.aborted) abort();
  });
  clearTimeout(timer);
  signal?.removeEventListener('abort', abort);
  // A deadline requests termination; this await establishes worker exit.
  // If termination cannot complete, the host intentionally retains its slot.
  try { await worker.terminate(); }
  catch { return { status: 'indeterminate', reason: 'worker-exit-unconfirmed', workerExited: false }; }
  return { ...result, workerExited: true };
}
