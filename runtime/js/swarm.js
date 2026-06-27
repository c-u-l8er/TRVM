// swarm.js -- the capstone: the IC32 WebAssembly runtime running COORDINATION-FREE
// across many real workers.
//
// Each worker is its own thread (the Web Worker analog; in a browser these are
// literally Web Workers) with its OWN instance of ic32.wasm and its OWN linear
// memory -- a genuinely isolated node. The workers partition a search and each
// reduces its slice through the WASM runtime. Their solution sets merge by UNION,
// a grow-only set (the canonical CRDT join: commutative, idempotent, monotone).
//
// Because the merge is monotone, CALM guarantees the result is independent of how
// many workers there are and of the order their results are combined -- no locks,
// no consensus, no coordination. This file proves that empirically: every worker
// count x merge order produces the same answer as a brute-force oracle.
//
// This is the whole thesis, end to end, on the sovereign substrate:
//   a coordination-free, multi-node interaction-calculus runtime, in WebAssembly.
//
//   run: node swarm.js
//
// Toy problem (same as dsearch.py): find the odd numbers in {0..N-1}, with the
// predicate computed INSIDE the calculus as NOT^n(FALSE) (= TRUE iff n is odd),
// i.e. each candidate's test is a real interaction-calculus reduction.

const path = require("path");
const fs = require("fs");
const {
  Worker, isMainThread, parentPort, workerData
} = require("worker_threads");

const WASM = path.join(__dirname, "..", "wasm", "ic32.wasm");

// ---- shared: build the predicate term for candidate n -----------------------
function church(n, lab) {
  if (n === 0) return "λf.λx.x";
  if (n === 1) return "λf.λx.(f x)";
  const cs = [...Array(n).keys()].map(i => "c" + i);
  const src = []; let cur = "f";
  for (let i = 0; i < n - 1; i++) {
    lab.v++; const L = lab.v;
    const nx = i < n - 2 ? ("t" + i) : cs[n - 1];
    src.push("!&" + L + "{" + cs[i] + "," + nx + "}=" + cur + ";");
    cur = nx;
  }
  let body = "x";
  for (let i = cs.length - 1; i >= 0; i--) body = "(" + cs[i] + " " + body + ")";
  return "λf.λx." + src.join("") + body;
}
const NOT = "λp.λt.λf.((p f) t)";
const FALSE = "λa.λb.b";
function predicateTerm(n) {
  const lab = { v: 1000 };
  // ((((church(n) NOT) FALSE) A) B)  ->  A if NOT^n(FALSE)=TRUE (n odd), else B
  return "((((" + church(n, lab) + " " + NOT + ") " + FALSE + ") A) B)";
}

// ---- worker side: own ic32.wasm instance, reduce assigned candidates --------
if (!isMainThread) {
  const { slice } = workerData;
  const bytes = fs.readFileSync(WASM);
  WebAssembly.instantiate(bytes, {}).then(({ instance }) => {
    const ex = instance.exports, mem = ex.memory, enc = new TextEncoder();
    function reduce(term) {
      const b = enc.encode(term);
      new Uint8Array(mem.buffer).set(b, ex.input_ptr());
      const n = ex.run(b.length);
      return Buffer.from(mem.buffer, ex.output_ptr(), n).toString("utf8");
    }
    const found = [];
    let interactions = 0;
    for (const n of slice) {
      const out = reduce(predicateTerm(n));   // 'A' => odd, 'B' => even
      interactions += Number(ex.last_interactions());
      if (out === "A") found.push(n);
    }
    parentPort.postMessage({ found, interactions });
  });
}

// ---- main side: partition, spawn workers, merge by CRDT union ---------------
function runSlice(slice) {
  return new Promise((resolve, reject) => {
    const w = new Worker(__filename, { workerData: { slice } });
    w.on("message", m => { resolve(m); w.terminate(); });
    w.on("error", reject);
  });
}

async function distributedSearch(domain, W) {
  const slices = Array.from({ length: W }, (_, k) => domain.filter(n => n % W === k));
  const t0 = process.hrtime.bigint();
  const parts = await Promise.all(slices.map(runSlice));   // workers run concurrently
  const ms = Number(process.hrtime.bigint() - t0) / 1e6;
  return { parts, ms };
}

function gsetUnion(sets, order) {
  const acc = new Set();
  for (const idx of order) for (const x of sets[idx]) acc.add(x);   // monotone CRDT join
  return [...acc].sort((a, b) => a - b);
}

async function main() {
  const N = 16;
  const domain = [...Array(N).keys()];
  const oracle = domain.filter(n => n % 2 === 1);

  console.log("ic32.wasm running coordination-free across real workers (worker_threads).");
  console.log("Problem: odd numbers in 0.." + (N - 1) + ", predicate = NOT^n(FALSE) reduced in WASM.");
  console.log("=".repeat(72));
  console.log("oracle (odds):", oracle.join(" "));
  console.log("");

  const allResults = new Set();
  for (const W of [1, 2, 3, 4, 6, 8]) {
    const { parts, ms } = await distributedSearch(domain, W);
    const sets = parts.map(p => p.found);
    const totalInter = parts.reduce((s, p) => s + p.interactions, 0);
    const orders = {
      "in-order": [...Array(W).keys()],
      "reversed": [...Array(W).keys()].reverse(),
    };
    if (W > 2) { const sh = [...Array(W).keys()]; sh.sort(() => 0.5 - Math.random()); orders["shuffled"] = sh; }
    let merged;
    for (const o of Object.values(orders)) {
      merged = gsetUnion(sets, o);
      allResults.add(JSON.stringify(merged));
    }
    const ok = JSON.stringify(merged) === JSON.stringify(oracle);
    console.log(
      "W=" + W + ": per-worker found sizes=[" + sets.map(s => s.length).join(",") + "]  " +
      "wall=" + ms.toFixed(1) + "ms  total-interactions=" + totalInter +
      "  merge-orders=" + Object.keys(orders).length + "  " + (ok ? "OK" : "MISMATCH")
    );
  }

  console.log("");
  console.log("distinct merged results across ALL (worker-count x merge-order) configs: " +
              allResults.size + " " +
              (allResults.size === 1 ? "(schedule-independent: coordination-free, as CALM predicts)" : "(!! DEPENDENT)"));
  const correct = allResults.size === 1 && [...allResults][0] === JSON.stringify(oracle);
  console.log("all configs == oracle: " + correct);
  console.log("");
  console.log("HONEST NOTE: workers run concurrently and the merge needs no coordination,");
  console.log("but at this toy scale worker-thread startup dominates wall-clock, so more");
  console.log("workers is not faster here. The point proven is COORDINATION-FREE CORRECTNESS");
  console.log("on the real WASM runtime: any worker count, any merge order -> same answer.");
  process.exit(correct ? 0 : 1);
}

if (isMainThread) main();
