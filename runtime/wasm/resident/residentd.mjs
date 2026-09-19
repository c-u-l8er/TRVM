// The resident host behind a socket, so a client that is not Node pays no Node startup per job.
// Wire (both directions): 4-byte big-endian length + UTF-8 JSON.
//   {"id": n, "term": "..."}     → {"id": n, ...result, "serverMs": x}
//   {"id": n, "cancel": true}    → aborts job n of THIS connection (its reply is `cancelled`)
//   {"op": "stats"}              → {"op": "stats", ...host.stats(), "module_sha256": ...}
// Closing a connection aborts every in-flight job it submitted. Frames larger than 1 MiB close the connection.
//   node residentd.mjs (--socket PATH | --port N [--bind ADDR]) [--pool P] [--max-queue Q]
import { createServer } from 'node:net';
import { unlinkSync } from 'node:fs';
import { performance } from 'node:perf_hooks';
import { createResidentHost } from './resident.mjs';

const args = Object.fromEntries(process.argv.slice(2).map((a, i, v) => a.startsWith('--') ? [a.slice(2), v[i + 1]] : []).filter(x => x.length));
const pool = Number(args.pool ?? 4), maxQueue = Number(args['max-queue'] ?? 16);
const host = createResidentHost({ pool, maxQueue });
const MAX_FRAME = 1048576 + 4096;

const server = createServer(sock => {
  let buf = Buffer.alloc(0), draining = false;
  const inflight = new Map(); // id → AbortController
  const send = obj => { const out = Buffer.from(JSON.stringify(obj)); const len = Buffer.alloc(4); len.writeUInt32BE(out.length); sock.write(Buffer.concat([len, out])); };
  const handle = async req => {
    if (req?.op === 'stats') return send({ op: 'stats', ...host.stats(), module_sha256: host.digest });
    if (req?.cancel === true) { inflight.get(req.id)?.abort(); return; }
    if (typeof req?.term !== 'string' || req.id === undefined) return send({ id: req?.id ?? null, status: 'refused', reason: 'request-shape' });
    if (inflight.has(req.id)) return send({ id: req.id, status: 'refused', reason: 'duplicate-id' });
    const ac = new AbortController(); inflight.set(req.id, ac);
    const t0 = performance.now();
    let result;
    try { result = await host.reduce(req.term, { signal: ac.signal }); }
    finally { inflight.delete(req.id); }
    if (!sock.destroyed) send({ id: req.id, ...result, serverMs: +(performance.now() - t0).toFixed(3) });
  };
  // One serial drain per socket: 'data' only appends; frames are parsed in order. Jobs run concurrently on the pool
  // (each `handle` is awaited by nobody but its own reply), which is what lets one connection pipeline.
  const drain = () => {
    if (draining) return; draining = true;
    try {
      while (buf.length >= 4) {
        const n = buf.readUInt32BE(0);
        if (n > MAX_FRAME) { sock.destroy(); return; }
        if (buf.length < 4 + n) break;
        let req; try { req = JSON.parse(buf.subarray(4, 4 + n).toString('utf8')); } catch { req = null; }
        buf = buf.subarray(4 + n);
        handle(req).catch(() => {});
      }
    } finally { draining = false; }
  };
  sock.on('data', chunk => { buf = Buffer.concat([buf, chunk]); drain(); });
  sock.on('close', () => { for (const ac of inflight.values()) ac.abort(); inflight.clear(); });
  sock.on('error', () => {});
});

const announce = where => console.log(JSON.stringify({ residentd: where, pool, maxQueue, pid: process.pid, module_sha256: host.digest, ready: host.stats().idle }));
try { await host.ready(); } catch (e) { console.error(JSON.stringify({ residentd: 'refused', reason: e.reason ?? 'startup', error: e.message })); process.exit(3); } // no connection is accepted before every worker has announced itself; a pool that cannot start says so and exits
if (args.socket) { try { unlinkSync(args.socket); } catch {} server.listen(args.socket, () => announce(args.socket)); }
else server.listen(Number(args.port ?? 7421), args.bind ?? '127.0.0.1', () => announce(`${server.address().address}:${server.address().port}`));   // the port the kernel BOUND, so `--port 0` is usable

const stop = async () => { server.close(); await host.close(); process.exit(0); };
process.on('SIGTERM', stop); process.on('SIGINT', stop);
