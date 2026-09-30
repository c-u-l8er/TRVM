import { parentPort, workerData } from 'node:worker_threads';
import { readResult } from './result.mjs';

try {
  const { module, input, outputBytes } = workerData;
  const ex = new WebAssembly.Instance(module, {}).exports;
  if (ex.abi_version() !== 2) throw Error("guest-abi-version");
  const bytes = Buffer.from(input, 'utf8');
  const ip = ex.input_ptr();
  const memory = ex.memory.buffer;
  if (bytes.length >= ex.input_capacity() || ip < 0 || ip + bytes.length >= memory.byteLength)
    throw Error('input-range');
  new Uint8Array(memory).set(bytes, ip);
  const status = ex.run_checked(bytes.length, 50000000, outputBytes);
  if (status !== ex.last_status()) throw Error("guest-status-mismatch");
  const length = ex.output_length();
  parentPort.postMessage(readResult(ex, length, outputBytes, status));
} catch {
  parentPort.postMessage({ status: 'failed', reason: 'guest-trap-or-invalid-output' });
}
