// In-process spans: the one-shot host's shape (module loaded once, a Worker per job — lab/BENCH.md §11 without the
// TCP) against the resident host (warm workers, a fresh instance per job), at concurrency 1 and 8, per term.
// Prints one JSON object. Latency is per job from `reduce` call to result; the host's own timing fields are
// reported where the host exposes them (only the resident host does).
//   node measure.mjs TERMFILE [JOBS] [POOL]
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { createResidentHost } from './resident.mjs';
import { createReducerHost } from '../experimental/host.mjs';

const [termFile, jobsArg = '60', poolArg = '8'] = process.argv.slice(2);
const term = readFileSync(termFile, 'utf8');
const JOBS = Number(jobsArg), POOL = Number(poolArg);
const sha = s => createHash('sha256').update(s, 'utf8').digest('hex');
const pct = (xs, p) => { const s = [...xs].sort((a, b) => a - b); return s[Math.min(s.length - 1, Math.floor(p * s.length))]; };
const summarize = (lat, extra = {}) => ({ n: lat.length, p50_ms: +pct(lat, 0.5).toFixed(3), p99_ms: +pct(lat, 0.99).toFixed(3), min_ms: +Math.min(...lat).toFixed(3), ...extra });

async function drive(reduceFn, concurrency, jobs) {
  const lat = [], timing = [], digests = new Set(), interactions = new Set(), statuses = {};
  let next = 0;
  const lane = async () => {
    while (next < jobs) {
      next++;
      const t0 = performance.now(); const r = await reduceFn(); lat.push(performance.now() - t0);
      statuses[r.status] = (statuses[r.status] ?? 0) + 1;
      if (r.status === 'candidate') { digests.add(sha(r.output)); interactions.add(r.interactions); }
      if (r.timing) timing.push(r.timing);
    }
  };
  const t0 = performance.now();
  await Promise.all(Array.from({ length: concurrency }, lane));
  const wall = performance.now() - t0;
  const extra = { jobs_per_s: +(jobs / (wall / 1000)).toFixed(1), statuses, output_sha256: [...digests], interactions: [...interactions] };
  if (timing.length) extra.host_timing_p50_ms = Object.fromEntries(['instantiate_ms', 'run_ms', 'read_ms'].map(k => [k, +pct(timing.map(t => t[k]), 0.5).toFixed(3)]));
  return summarize(lat, extra);
}

const out = { term: termFile.split('/').pop(), term_bytes: Buffer.byteLength(term), jobs: JOBS, pool: POOL, rows: {} };

// One-shot shape: POOL host objects (each serialises its own reductions and spawns a Worker per job).
{
  const hosts = Array.from({ length: POOL }, () => createReducerHost());
  const free = [...hosts]; const waiters = [];
  const acquire = () => free.length ? Promise.resolve(free.pop()) : new Promise(r => waiters.push(r));
  const release = h => { const w = waiters.shift(); if (w) w(h); else free.push(h); };
  const reduce = async () => { const h = await acquire(); try { return await h.reduce(term); } finally { release(h); } };
  await reduce(); // warm-up
  out.rows['oneshot-worker-per-job C=1'] = await drive(reduce, 1, JOBS);
  out.rows[`oneshot-worker-per-job C=${POOL}`] = await drive(reduce, POOL, JOBS);
}

// Resident: warm workers, fresh instance per job.
{
  const host = createResidentHost({ pool: POOL, maxQueue: POOL * 4 });
  await host.ready();
  const reduce = () => host.reduce(term);
  await reduce();
  out.rows['resident C=1'] = await drive(reduce, 1, JOBS);
  out.rows[`resident C=${POOL}`] = await drive(reduce, POOL, JOBS);
  out.resident_stats = await host.close();
}

console.log(JSON.stringify(out));
