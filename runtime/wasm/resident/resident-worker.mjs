// A warm worker: holds the compiled module and, per job, instantiates it AFRESH, reduces, and posts exactly one
// reply carrying the job id. The instance is dropped when the handler returns; no guest state survives a job.
// The `fresh` witness is what a genuinely new instance reports before any input is written: zero output and zero
// interactions. Under an instance-reusing mutant it carries the previous job's values — that is how the harness
// sees the difference. The timing fields are the host's own reduction costs, which the one-shot host never exposed.
import { parentPort, workerData } from 'node:worker_threads';
import { performance } from 'node:perf_hooks';
import { readResult } from '../experimental/result.mjs';

const { module } = workerData;

parentPort.on('message', job => {
  const { id, input, outputBytes, maxInteractions } = job;
  const t0 = performance.now();
  try {
    const ex = new WebAssembly.Instance(module, {}).exports;
    if (ex.abi_version() !== 2) throw Error('guest-abi-version');
    const fresh = { outputLength: ex.output_length(), interactions: ex.last_interactions() };
    const t1 = performance.now();
    const bytes = Buffer.from(input, 'utf8');
    const ip = ex.input_ptr();
    const memory = ex.memory.buffer;
    if (bytes.length >= ex.input_capacity() || ip < 0 || ip + bytes.length >= memory.byteLength) throw Error('input-range');
    new Uint8Array(memory).set(bytes, ip);
    const status = ex.run_checked(bytes.length, maxInteractions, outputBytes);
    if (status !== ex.last_status()) throw Error('guest-status-mismatch');
    const t2 = performance.now();
    const result = readResult(ex, ex.output_length(), outputBytes, status);
    const t3 = performance.now();
    parentPort.postMessage({ id, ...result, fresh, timing: { instantiate_ms: t1 - t0, run_ms: t2 - t1, read_ms: t3 - t2 } });
  } catch {
    parentPort.postMessage({ id, status: 'failed', reason: 'guest-trap-or-invalid-output' });
  }
});

parentPort.postMessage({ ready: true });
