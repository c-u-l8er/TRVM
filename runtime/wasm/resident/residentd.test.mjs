// The socket service over the resident host: identity through the wire, pipelining on one connection, a cancel
// frame, the stats frame, a malformed request, and the abort of a connection's jobs when it closes.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';

const here = new URL('./', import.meta.url);
const sha = s => createHash('sha256').update(s, 'utf8').digest('hex');
const identities = JSON.parse(fs.readFileSync(new URL('./fixtures/identities.json', here)));
const fixture = name => fs.readFileSync(new URL(`./fixtures/${name}`, here), 'utf8');

class Conn {
  #sock; #buf = Buffer.alloc(0); #waiters = []; #frames = [];
  static async open(sockPath) {
    const c = new Conn(); c.#sock = net.createConnection(sockPath);
    await new Promise((res, rej) => { c.#sock.once('connect', res); c.#sock.once('error', rej); });
    c.#sock.on('data', d => { c.#buf = Buffer.concat([c.#buf, d]); c.#drain(); });
    return c;
  }
  #drain() {
    while (this.#buf.length >= 4) {
      const n = this.#buf.readUInt32BE(0); if (this.#buf.length < 4 + n) break;
      const f = JSON.parse(this.#buf.subarray(4, 4 + n).toString('utf8')); this.#buf = this.#buf.subarray(4 + n);
      const w = this.#waiters.shift(); if (w) w(f); else this.#frames.push(f);
    }
  }
  send(obj) { const b = Buffer.from(JSON.stringify(obj)); const l = Buffer.alloc(4); l.writeUInt32BE(b.length); this.#sock.write(Buffer.concat([l, b])); }
  next() { return this.#frames.length ? Promise.resolve(this.#frames.shift()) : new Promise(r => this.#waiters.push(r)); }
  close() { this.#sock.destroy(); }
}

let daemon, sockPath, dir;
test.before(async () => {
  dir = fs.mkdtempSync(path.join(os.tmpdir(), 'residentd-test-'));
  sockPath = path.join(dir, 'r.sock');
  daemon = spawn(process.execPath, [new URL('./residentd.mjs', here).pathname, '--socket', sockPath, '--pool', '2', '--max-queue', '4'], { stdio: ['ignore', 'pipe', 'inherit'] });
  const banner = await new Promise(r => daemon.stdout.once('data', d => r(JSON.parse(d.toString()))));
  assert.equal(banner.pool, 2); assert.equal(banner.ready, 2, 'listened only after every worker was ready');
});
test.after(async () => { daemon.kill('SIGTERM'); await new Promise(r => daemon.once('exit', r)); fs.rmSync(dir, { recursive: true, force: true }); });

test('S1 · the sealed world reduces through the wire to its recorded digest, with the host timing exposed', async () => {
  const c = await Conn.open(sockPath);
  try {
    const id = identities['chain30-epoch-1'];
    c.send({ id: 7, term: fixture(id.term_file) });
    const r = await c.next();
    assert.equal(r.id, 7); assert.equal(r.status, 'candidate');
    assert.equal(sha(r.output), id.payload_sha256); assert.equal(r.interactions, id.interactions);
    assert.equal(r.jobRetired, true); assert.equal(r.workerExited, false);
    assert.ok(r.serverMs > 0 && r.timing.run_ms > 0);
  } finally { c.close(); }
});

test('S2 · twenty pipelined requests on one connection: each answered under its own id, the pool+queue bound (2+4) refusing the overflow busy', async () => {
  const c = await Conn.open(sockPath);
  try {
    const terms = ['*', '(λx.x λy.y)', fixture('pulser-door-epoch-1.ic')];
    for (let i = 1; i <= 20; i++) c.send({ id: i, term: terms[i % 3] });
    const got = new Map();
    for (let i = 0; i < 20; i++) { const r = await c.next(); got.set(r.id, r); }
    assert.equal(got.size, 20);
    let candidates = 0, busy = 0;
    for (let i = 1; i <= 20; i++) {
      const r = got.get(i);
      if (r.status === 'refused') { assert.equal(r.reason, 'busy'); busy++; continue; }
      assert.equal(r.status, 'candidate'); candidates++;
      if (i % 3 === 0) assert.equal(r.output, '*'); if (i % 3 === 1) assert.equal(r.output, 'λa.a'); if (i % 3 === 2) assert.equal(r.interactions, 61);
    }
    assert.equal(candidates + busy, 20); assert.ok(candidates >= 2 && candidates <= 6, `candidates ${candidates}`); assert.ok(busy >= 14);
  } finally { c.close(); }
});

test('S3 · a cancel frame aborts a queued job of this connection; a duplicate id and a malformed request are refused', async () => {
  const c = await Conn.open(sockPath);
  try {
    const big = fixture('corpus-exp_2p16.ic');
    for (let i = 1; i <= 6; i++) c.send({ id: i, term: big }); // pool 2 + queue 4: the last ones wait
    c.send({ id: 6, cancel: true });
    c.send({ id: 3, term: '*' });
    c.send({ nonsense: true });
    const got = [];
    for (let i = 0; i < 8; i++) got.push(await c.next());
    const six = got.find(r => r.id === 6);
    assert.equal(six.status, 'cancelled', JSON.stringify(six));
    assert.equal(got.filter(r => r.status === 'candidate').length, 5);
    assert.ok(got.some(r => r.id === 3 && r.status === 'refused' && r.reason === 'duplicate-id'));
    assert.ok(got.some(r => r.id === null && r.reason === 'request-shape'));
  } finally { c.close(); }
});

test('S4 · the stats frame reports the pool and the module digest; closing a connection aborts its in-flight jobs', async () => {
  const a = await Conn.open(sockPath);
  a.send({ id: 1, term: fixture('corpus-exp_2p16.ic') }); a.send({ id: 2, term: fixture('corpus-exp_2p16.ic') }); a.send({ id: 3, term: fixture('corpus-exp_2p16.ic') });
  a.close(); // before the replies: the queued job is cancelled; running ones are terminated and their workers replaced
  const c = await Conn.open(sockPath);
  try {
    await new Promise(r => setTimeout(r, 200));
    c.send({ op: 'stats' });
    const s = await c.next();
    assert.equal(s.op, 'stats'); assert.equal(s.pool, 2); assert.equal(s.module_sha256, '0cf96179ac7063f85691834b84c9e4e01f5a855ace8678f6752315a6f15fed95');
    assert.ok(s.cancelled >= 1, `cancelled: ${s.cancelled}`);
    assert.equal(s.live, 2, 'the pool is whole again');
    c.send({ id: 1, term: '*' }); assert.equal((await c.next()).output, '*');
  } finally { c.close(); }
});
