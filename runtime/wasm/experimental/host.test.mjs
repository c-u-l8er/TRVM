import test from 'node:test';
import assert from 'node:assert/strict';
import { Worker } from 'node:worker_threads';
import { EventEmitter } from 'node:events';
import { createReducerHost, LIMITS, supervise } from './host.mjs';

const corpus = [
  ['*', '*'], ['(λx.x λy.y)', 'λa.a'],
  ['(λx.λt.(t x) λy.y)', 'λa.(a λb.b)'],
  ['(λb.λt.λf.((b f) t) λT.λF.T)', 'λa.λb.b'],
  ['!{a,b} = {λx.x,λy.y}; (a b)', 'λa.a'],
  ['({λx.x,λy.y} λz.z)', '&0{λa.a,λb.b}'],
];

test('fresh workers match the independently generated Python corpus', async () => {
  const host = createReducerHost();
  for (const [input, expected] of corpus) {
    const r = await host.reduce(input);
    assert.equal(r.status, 'candidate'); assert.equal(r.output, expected);
    assert.equal(r.workerExited, true);
  }
});

test('refuses bytes before copying, including multibyte input', async () => {
  const host = createReducerHost();
  for (const input of ['x'.repeat(LIMITS.inputBytes + 1), 'λ'.repeat(LIMITS.inputBytes)])
    assert.equal((await host.reduce(input)).reason, 'input-limit');
  for (const input of ['', '\0', '\ud800']) assert.equal((await host.reduce(input)).reason, 'input-encoding');
  assert.equal((await host.reduce({})).reason, 'input-type');
});

test('one slot and no queue; slot becomes reusable only after exit', async () => {
  const host = createReducerHost();
  const first = host.reduce('*');
  assert.equal((await host.reduce('*')).reason, 'busy');
  assert.equal((await first).workerExited, true);
  assert.equal((await host.reduce('*')).status, 'candidate');
});

test('typed ABI accepts the literal ABORTED as a normal form', async () => {
  const host = createReducerHost();
  assert.equal((await host.reduce('ABORTED')).output, 'ABORTED');
  assert.equal((await host.reduce('*')).output, '*');
});

test('pre-cancelled input does not occupy the host and cancellation exits the worker', async () => {
  const host = createReducerHost();
  assert.equal((await host.reduce('*', { signal: AbortSignal.abort() })).status, 'cancelled');
  const ac = new AbortController();
  const running = host.reduce('*', { signal: ac.signal }); ac.abort();
  assert.deepEqual(await running, { status: 'cancelled', workerExited: true });
  assert.equal((await host.reduce('*')).output, '*');
});

test('deadline terminates a real noncooperating worker without blocking the parent', async () => {
  let ticks = 0;
  const entered = new Int32Array(new SharedArrayBuffer(4));
  const ticker = setInterval(() => ticks++, 1);
  try {
    const r = await supervise(() => new Worker(`const { workerData } = require('node:worker_threads'); const m = new WebAssembly.Module(Buffer.from('0061736d01000000010401600000030201000707010372756e00000a0901070003400c000b0b', 'hex')); const instance = new WebAssembly.Instance(m); Atomics.store(new Int32Array(workerData), 0, 1); instance.exports.run();`, { eval: true, workerData: entered.buffer }), 250);
    assert.deepEqual(r, { status: 'deadline', workerExited: true });
    assert.ok(ticks > 0);
    assert.equal(Atomics.load(entered, 0), 1, 'worker reached the infinite Wasm call');
  } finally { clearInterval(ticker); }
});

test('worker exception and exit without result are typed and confirmed exited', async () => {
  for (const code of ['throw Error("fixture")', 'process.exit(0)']) {
    const r = await supervise(() => new Worker(code, { eval: true }), 1000);
    assert.equal(r.status, 'failed'); assert.equal(r.workerExited, true);
  }
});

test('a received result does not complete supervision before termination settles', async () => {
  const worker = new EventEmitter(); let release;
  worker.terminate = () => new Promise(resolve => { release = resolve; });
  let completed = false;
  const p = supervise(() => worker, 1000).then(r => { completed = true; return r; });
  worker.emit('message', { status: 'candidate', output: '*' });
  await new Promise(setImmediate); assert.equal(completed, false);
  release(0); assert.equal((await p).workerExited, true);
});

test('unconfirmed exit cannot be described as cleaned up', async () => {
  const worker = new EventEmitter(); worker.terminate = async () => { throw Error('fixture'); };
  const p = supervise(() => worker, 1000);
  worker.emit('message', { status: 'candidate', output: '*' });
  assert.deepEqual(await p, { status: 'indeterminate', reason: 'worker-exit-unconfirmed', workerExited: false });
});

test('output bounds refuse before decoding or copying', async () => {
  const { readResult } = await import('./result.mjs');
  const memory = new WebAssembly.Memory({ initial: 257 });
  const ex = { memory, output_ptr: () => 0, last_interactions: () => 0 };
  for (const length of [-1, memory.buffer.byteLength + 1, 0.5])
    assert.equal(readResult(ex, length, LIMITS.outputBytes, 0).reason, 'guest-output-range');
  for (const length of [LIMITS.outputBytes + 1, 16777215])
    assert.equal(readResult(ex, length, LIMITS.outputBytes, 0).reason, 'output-limit');
  new Uint8Array(memory.buffer)[0] = 255;
  assert.equal(readResult(ex, 1, LIMITS.outputBytes, 0).reason, 'guest-output-encoding');
  new Uint8Array(memory.buffer)[0] = 42;
  assert.equal(readResult(ex, 1, 1, 0).output, '*');
});

test('a late result cannot beat an expired deadline when the parent timer was delayed', async () => {
  const worker = new EventEmitter(); worker.terminate = async () => 0;
  const p = supervise(() => worker, 1);
  const until = performance.now() + 5;
  while (performance.now() < until) { /* deliberately delay the timer callback */ }
  worker.emit('message', { status: 'candidate', output: '*' });
  assert.deepEqual(await p, { status: 'deadline', workerExited: true });
});

test('a substituted module is refused before instantiation', async () => {
  const fs = await import('node:fs/promises');
  const { tmpdir } = await import('node:os');
  const { join } = await import('node:path');
  const { pathToFileURL } = await import('node:url');
  const dir = await fs.mkdtemp(join(tmpdir(), 'hs-module-pin-'));
  try {
    await fs.mkdir(join(dir, 'experimental'));
    await fs.copyFile(new URL('./host.mjs', import.meta.url), join(dir, 'experimental/host.mjs'));
    await fs.writeFile(join(dir, 'ic32_checked.wasm'), Buffer.from('0061736d01000000', 'hex'));
    const host = await import(pathToFileURL(join(dir, 'experimental/host.mjs')));
    assert.throws(() => host.createReducerHost(), /module-digest-mismatch/);
  } finally { await fs.rm(dir, { recursive: true, force: true }); }
});
