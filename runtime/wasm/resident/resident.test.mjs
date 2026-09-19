// The resident host's harness. Identity against the one-shot host and the sealed worlds; then every property the
// one-shot host established, re-established on a host whose workers survive a job. Each case names what it asserts;
// controls/run-controls.sh says which case each mutant must turn red.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { EventEmitter } from 'node:events';
import { Worker } from 'node:worker_threads';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { createResidentHost, LIMITS } from './resident.mjs';
import { createReducerHost } from '../experimental/host.mjs';

const here = new URL('./', import.meta.url);
const sha = s => createHash('sha256').update(s, 'utf8').digest('hex');
const corpus = JSON.parse(fs.readFileSync(new URL('../experimental/oracle-corpus.json', import.meta.url)));
const identities = JSON.parse(fs.readFileSync(new URL('./fixtures/identities.json', here)));
const fixture = name => fs.readFileSync(new URL(`./fixtures/${name}`, here), 'utf8');

// A Wasm module whose only export loops forever: the noncooperating guest (from ../experimental/host.test.mjs).
const LOOP_WASM = '0061736d01000000010401600000030201000707010372756e00000a0901070003400c000b0b';
// Fixture workers for the trusted construction seam. Each announces `ready` like the real one, then misbehaves ONCE.
const fixtureWorker = body => new Worker(`const { parentPort } = require('node:worker_threads'); parentPort.on('message', m => { ${body} }); parentPort.postMessage({ ready: true });`, { eval: true });
const LOOP_BODY = `const inst = new WebAssembly.Instance(new WebAssembly.Module(Buffer.from('${LOOP_WASM}', 'hex'))); inst.exports.run();`;
const realWorker = () => new Worker(new URL('./resident-worker.mjs', here), { workerData: { module: loadedModule() }, env: {}, execArgv: [] });
let _mod;
function loadedModule() { return _mod ??= new WebAssembly.Module(fs.readFileSync(new URL('../ic32_checked.wasm', here))); }
// First N constructions misbehave, the rest are real: the pool must heal with a real replacement.
const firstThen = (n, bad) => { let k = 0; return () => (k++ < n ? bad() : realWorker()); };

class FakeWorker extends EventEmitter {
  sent = []; terminated = 0; terminateThrows = false;
  postMessage(m) { this.sent.push(m); }
  async terminate() { this.terminated++; if (this.terminateThrows) throw Error('fixture'); return 0; }
  ready() { setImmediate(() => this.emit('message', { ready: true })); return this; }
}

test('I1 · every oracle case reduces on the resident host exactly as on the one-shot host', async () => {
  const resident = createResidentHost({ pool: 2 });
  const oneShot = createReducerHost();
  try {
    for (const c of corpus) {
      const [a, b] = await Promise.all([resident.reduce(c.input), oneShot.reduce(c.input)]);
      assert.equal(a.status, 'candidate', c.input);
      assert.equal(a.output, b.output, c.input); assert.equal(a.interactions, b.interactions, c.input);
      assert.equal(a.output, c.output); assert.equal(a.interactions, c.interactions);
      assert.deepEqual(a.fresh, { outputLength: 0, interactions: 0 });
      assert.equal(a.jobRetired, true); assert.equal(a.workerExited, false);
      assert.equal(a.module_sha256, resident.digest);
    }
  } finally { await resident.close(); }
});

test('I2 · the three sealed worlds reduce to their recorded payload digests and interaction counts', async () => {
  const host = createResidentHost({ pool: 1 });
  try {
    for (const [name, id] of Object.entries(identities)) {
      if (name.startsWith('_')) continue;
      const term = fixture(id.term_file);
      assert.equal(sha(term), id.term_sha256, name); assert.equal(Buffer.byteLength(term), id.term_bytes);
      const r = await host.reduce(term);
      assert.equal(r.status, 'candidate', name);
      assert.equal(Buffer.byteLength(r.output), id.payload_bytes, name);
      assert.equal(sha(r.output), id.payload_sha256, name);
      assert.equal(r.interactions, id.interactions, name);
    }
  } finally { await host.close(); }
});

test('F1 · a job after a 476-interaction job sees a fresh instance: zero output, zero interactions before input', async () => {
  const host = createResidentHost({ pool: 1 });
  try {
    const a = await host.reduce(fixture('chain30-epoch-1.ic'));
    assert.equal(a.interactions, 476); assert.equal(a.worker.id, 1);
    const b = await host.reduce('*');
    assert.equal(b.worker.id, 1, 'same warm worker'); assert.equal(b.worker.jobs, 2);
    assert.deepEqual(b.fresh, { outputLength: 0, interactions: 0 });
    assert.equal(b.interactions, 0); assert.equal(b.output, '*');
  } finally { await host.close(); }
});

test('X1 · 26 distinct terms on a pool of 4 each come back to their own requester', async () => {
  const host = createResidentHost({ pool: 4, maxQueue: 64 });
  try {
    const results = await Promise.all(corpus.map(c => host.reduce(c.input)));
    results.forEach((r, i) => { assert.equal(r.status, 'candidate'); assert.equal(r.output, corpus[i].output); assert.equal(r.interactions, corpus[i].interactions); });
    const s = host.stats();
    assert.equal(s.served, 26); assert.equal(s.live, 4); assert.equal(s.idle, 4); assert.equal(s.replaced, 0);
    assert.ok(new Set(results.map(r => r.worker.id)).size > 1, 'more than one worker served');
  } finally { await host.close(); }
});

test('E1 · pre-dispatch refusals create no job and touch no worker', async () => {
  const host = createResidentHost({ pool: 1 });
  try {
    for (const input of ['x'.repeat(LIMITS.inputBytes + 1), 'λ'.repeat(LIMITS.inputBytes)]) assert.equal((await host.reduce(input)).reason, 'input-limit');
    for (const input of ['', '\0', '\ud800']) assert.equal((await host.reduce(input)).reason, 'input-encoding');
    assert.equal((await host.reduce({})).reason, 'input-type');
    assert.equal((await host.reduce('*', { signal: 1 })).reason, 'signal-type');
    assert.equal((await host.reduce('*', { signal: AbortSignal.abort() })).status, 'cancelled');
    assert.equal(host.stats().served, 0);
  } finally { await host.close(); }
});

test('D1 · the deadline terminates a real noncooperating guest, the exit is confirmed, and the pool heals with a real worker', async () => {
  let loopWorker;
  const host = createResidentHost({ pool: 1, deadlineMs: 250, createWorker: firstThen(1, () => (loopWorker = fixtureWorker(LOOP_BODY))) });
  let ticks = 0; const ticker = setInterval(() => ticks++, 1);
  try {
    const exited = new Promise(r => loopWorker.once('exit', r));
    const r = await host.reduce('*');
    assert.equal(r.status, 'deadline'); assert.equal(r.workerExited, true); assert.equal(r.worker.id, 1);
    assert.ok(ticks > 0, 'the parent stayed responsive');
    await Promise.race([exited, new Promise((_, rej) => setTimeout(() => rej(Error('the looping worker did not exit')), 2000))]);
    const s = host.stats(); assert.equal(s.deadlines, 1); assert.equal(s.replaced, 1); assert.equal(s.live, 1);
    const next = await host.reduce('*');
    assert.equal(next.status, 'candidate'); assert.equal(next.output, '*'); assert.equal(next.worker.id, 2);
  } finally { clearInterval(ticker); await host.close(); await loopWorker?.terminate().catch(() => {}); }
});

test('C1 · a queued job is cancelled without ever reaching a worker; the running job completes', async () => {
  const host = createResidentHost({ pool: 1 });
  await host.ready();
  try {
    const ac = new AbortController();
    const first = host.reduce(fixture('chain30-epoch-1.ic'));
    const second = host.reduce('*', { signal: ac.signal });
    assert.equal(host.stats().queued, 1);
    ac.abort();
    assert.deepEqual(await second, { status: 'cancelled' });
    assert.equal((await first).interactions, 476);
    const s = host.stats(); assert.equal(s.cancelled, 1); assert.equal(s.served, 1); assert.equal(s.replaced, 0);
  } finally { await host.close(); }
});

test('C2 · cancelling a running job terminates its worker (observed exiting), confirms the exit and replaces it', async () => {
  let stuck;
  const host = createResidentHost({ pool: 1, createWorker: firstThen(1, () => (stuck = fixtureWorker('/* ignores the job */'))) });
  try {
    const ac = new AbortController();
    await host.ready();
    const exited = new Promise(r => stuck.once('exit', r));
    const running = host.reduce('*', { signal: ac.signal });
    await new Promise(r => setTimeout(r, 30)); ac.abort();
    const r = await running;
    assert.equal(r.status, 'cancelled'); assert.equal(r.workerExited, true);
    await Promise.race([exited, new Promise((_, rej) => setTimeout(() => rej(Error('the stuck worker did not exit')), 2000))]);
    assert.equal((await host.reduce('*')).output, '*');
    const s = host.stats(); assert.equal(s.cancelled, 1); assert.equal(s.replaced, 1);
  } finally { await host.close(); await stuck?.terminate().catch(() => {}); }
});

test('Q1 · the queue is bounded: beyond maxQueue a request is refused busy, and close cancels what waited', async () => {
  const host = createResidentHost({ pool: 1, maxQueue: 2, createWorker: () => fixtureWorker('/* never replies */') });
  try {
    await host.ready();
    const j1 = host.reduce('*'), j2 = host.reduce('*'), j3 = host.reduce('*');
    assert.deepEqual(await host.reduce('*'), { status: 'refused', reason: 'busy' });
    assert.equal(host.stats().queued, 2); assert.equal(host.stats().refusedBusy, 1);
    const s = await host.close();
    assert.equal(s.closed, true);
    for (const j of [j2, j3]) assert.deepEqual(await j, { status: 'cancelled' });
    assert.equal((await j1).status, 'cancelled');
    assert.deepEqual(await host.reduce('*'), { status: 'refused', reason: 'closed' });
  } finally { await host.close(); }
});

test('W1 · a worker that exits without replying is a typed failure with a confirmed exit, and is replaced', async () => {
  const host = createResidentHost({ pool: 1, createWorker: firstThen(1, () => fixtureWorker('process.exit(0)')) });
  try {
    const r = await host.reduce('*');
    assert.equal(r.status, 'failed'); assert.equal(r.reason, 'worker-exit-without-result'); assert.equal(r.workerExited, true);
    assert.equal((await host.reduce('*')).output, '*');
    assert.equal(host.stats().replaced, 1);
  } finally { await host.close(); }
});

test('L1 · a reply that arrives after the deadline expired is a deadline, even when the timer was delayed', async () => {
  const fake = new FakeWorker().ready();
  const host = createResidentHost({ pool: 1, deadlineMs: 1, createWorker: () => fake });
  await host.ready();
  const p = host.reduce('*');
  const until = performance.now() + 5; while (performance.now() < until) { /* delay the timer callback */ }
  fake.emit('message', { id: fake.sent[0].id, status: 'candidate', output: '*', interactions: 0 });
  const r = await p;
  assert.equal(r.status, 'deadline'); assert.equal(r.workerExited, true); assert.equal(fake.terminated, 1);
  await host.close();
});

test('R1 · a reply carrying a retired or foreign job id changes nothing; only the live id settles the job', async () => {
  const fake = new FakeWorker().ready();
  const host = createResidentHost({ pool: 1, createWorker: () => fake });
  await host.ready();
  const p = host.reduce('*');
  let settled = false; p.then(() => { settled = true; });
  fake.emit('message', { id: 999999, status: 'candidate', output: 'WRONG', interactions: 7 });
  await new Promise(setImmediate); assert.equal(settled, false);
  fake.emit('message', { id: fake.sent[0].id, status: 'candidate', output: '*', interactions: 0 });
  const r = await p; assert.equal(r.output, '*'); assert.equal(r.jobRetired, true);
  fake.emit('message', { id: fake.sent[0].id, status: 'candidate', output: 'AGAIN', interactions: 0 }); // retired id
  assert.equal(host.stats().served, 1);
  await host.close();
});

test('U1 · an unconfirmed exit is indeterminate, shrinks the pool and is not described as replaced', async () => {
  const fake = new FakeWorker().ready(); fake.terminateThrows = true;
  const host = createResidentHost({ pool: 1, deadlineMs: 5, createWorker: () => fake });
  await host.ready();
  const r = await host.reduce('*');
  assert.equal(r.status, 'indeterminate'); assert.equal(r.reason, 'worker-exit-unconfirmed'); assert.equal(r.workerExited, false);
  const s = host.stats(); assert.equal(s.unconfirmed, 1); assert.equal(s.replaced, 0); assert.equal(s.live, 0);
  assert.deepEqual(await host.reduce('*'), { status: 'refused', reason: 'exhausted' });
  await host.close();
});

test('M1 · a substituted module is refused before compilation', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'resident-pin-'));
  try {
    const bad = path.join(dir, 'ic32_checked.wasm');
    fs.writeFileSync(bad, Buffer.from('0061736d01000000', 'hex'));
    let leaked;
    try { assert.throws(() => (leaked = createResidentHost({ moduleUrl: pathToFileURL(bad) })), /module-digest-mismatch/); }
    finally { await leaked?.close(); }
  } finally { fs.rmSync(dir, { recursive: true, force: true }); }
});

test('P1 · 200 jobs over a pool of 4: every result a candidate on a fresh instance, the workers accounting for all of them', async () => {
  const host = createResidentHost({ pool: 4, maxQueue: 256 });
  try {
    const term = fixture('pulser-door-epoch-1.ic');
    const results = await Promise.all(Array.from({ length: 200 }, () => host.reduce(term)));
    for (const r of results) { assert.equal(r.status, 'candidate'); assert.equal(r.interactions, 61); assert.deepEqual(r.fresh, { outputLength: 0, interactions: 0 }); }
    const perWorker = new Map(); for (const r of results) perWorker.set(r.worker.id, Math.max(perWorker.get(r.worker.id) ?? 0, r.worker.jobs));
    assert.equal([...perWorker.values()].reduce((a, b) => a + b, 0), 200);
    assert.equal(host.stats().served, 200);
  } finally { await host.close(); }
});

// A deployment fault (2026-09-19, locuchest: the worker's `../experimental/result.mjs` was not copied) used to spin the
// pool silently -- 155 spawns in 3 s, `ready()` never resolving, the daemon never announcing. Now the third consecutive
// startup death stops the respawn, `ready()` rejects with the worker's own error, and `reduce` refuses `exhausted`.
test('D2 · a worker that dies before announcing itself is replaced at most twice; then ready() rejects with its error and reduce refuses exhausted', async () => {
  const dying = () => new Worker('throw new Error("no such module at startup")', { eval: true });
  const host = createResidentHost({ pool: 2, maxQueue: 1, createWorker: dying });
  await assert.rejects(host.ready(), e => e.reason === 'startup-deaths' && /no such module at startup/.test(e.message));
  const st = host.stats();
  assert.equal(st.startupDeaths, 3); assert.ok(st.spawned <= 4, 'spawned ' + st.spawned);
  assert.deepEqual(await host.reduce('*').then(r => [r.status, r.reason]), ['refused', 'exhausted']);
  await host.close();
});
