/* ═══════════════════════════════════════════════════════════════════════════
   probe_derivegrant_v02_repro.mjs — the two defects in DERIVE-v0.1.0, frozen.

   Round 14 shipped the serialized derivation boundary and wrote two sentences
   about it that the mechanism did not support. External review supplied a
   witness for each; both reproduced here verbatim before anything was changed.

   W-1  THE READ FOOTPRINT WAS BYPASSABLE.
        The worker sourced its read table from `req.canonical_inputs.__reads`,
        and the language has `{op:"input", name:…}`, which retrieves ANY
        canonical input. So the one-node program {op:"input", name:"__reads"}
        returns the entire authority-supplied read table with witness.reads = 0,
        support = [] and read_footprint = {exact:[],predicates:[]}. The round-14
        ledger's claim — "the footprint is now the authority's record of what it
        read on the derivation's behalf" — describes a mechanism that did not
        exist: nothing forced a consumed read to be a TRACKED read.

   W-2  implementation_id WAS DECORATION.
        DeriveRequest carried it, no executor checked it, and DeriveResult did
        not carry it at all. A request asserting `impl-c-pretend-v9` was executed
        by the JavaScript evaluator and returned success. The grid's own
        film_identity_forward_declaration makes implementation_id the executable
        provenance half of the film identity split; a field the caller asserts
        and no one verifies cannot carry provenance.

   WHY THIS PROBE GATES, WHERE ITS SIBLINGS DOCUMENT
   ─────────────────────────────────────────────────
   probe_closureenv / probe_realm_9d2 / probe_ownfailopen freeze a boundary that
   is declared open, so they report a breach and that is the record. These two
   defects ARE repaired, so this probe runs each witness TWICE — against the
   frozen v0.1.0 copy below, where it must still breach, and against the live
   modules, where it must be confined. Exit 0 requires both directions.

   That is law:evidence.instrument-nonvacuity@1 applied to a repro: a witness
   that stops reproducing against the version it was written for has stopped
   measuring, and six apparatus failures across four rounds were exactly that.
   A one-directional probe here would pass just as happily if the frozen copy
   were replaced with the repaired one.

   The frozen copy is embedded as a data: URL and run in a REAL worker_threads
   realm, because W-1 is a defect in the worker's reader wiring rather than in
   the shared evaluator — the in-process path took a reader argument and never
   had it. Nothing is written to the artifact tree.
   ═══════════════════════════════════════════════════════════════════════════ */
import { Worker } from "node:worker_threads";
import {
  ProgramRegistry as LiveRegistry, JS_IMPLEMENTATION_ID as LIVE_IMPL, grantId as liveGrantId,
} from "./derive_protocol.mjs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "CONFINED" : "BREACH  "}  ${id.padEnd(34)} ${note}`); };

/* ── DERIVE-v0.1.0, VERBATIM ──────────────────────────────────────────────
   derive_protocol.mjs and derive_worker.mjs as shipped in commit 5b25a08,
   concatenated so the worker resolves nothing from the repository. Do not
   "fix" anything in this string: its job is to keep failing. */
const FROZEN_V010 = `
import { parentPort, workerData } from "node:worker_threads";
import { createHash } from "node:crypto";
const H = (s) => createHash("sha256").update(s).digest("hex");

function canonicalBytes(v, path = "$", onPath = new Set()) {
  if (v === null) return "null";
  const t = typeof v;
  if (t === "boolean") return v ? "true" : "false";
  if (t === "number") {
    if (!Number.isFinite(v)) throw new Error("not-canonical: non-finite number at " + path);
    return JSON.stringify(v);
  }
  if (t === "string") return JSON.stringify(v);
  if (t === "object") {
    if (onPath.has(v)) throw new Error("not-canonical: cycle at " + path);
    onPath.add(v);
    let out;
    if (Array.isArray(v)) {
      out = "[" + v.map((x, i) => canonicalBytes(x, path + "[" + i + "]", onPath)).join(",") + "]";
    } else if (Object.getPrototypeOf(v) === Object.prototype || Object.getPrototypeOf(v) === null) {
      const keys = Object.keys(v).sort();
      out = "{" + keys.map((k) => JSON.stringify(k) + ":" +
        canonicalBytes(v[k], path + "." + k, onPath)).join(",") + "}";
    } else {
      throw new Error("not-canonical: non-plain object at " + path);
    }
    onPath.delete(v);
    return out;
  }
  throw new Error("not-canonical: " + t + " at " + path);
}
const OPS = {
  const: (n) => n.value,
  add: (n, ev) => ev(n.a) + ev(n.b),
  sub: (n, ev) => ev(n.a) - ev(n.b),
  mul: (n, ev) => ev(n.a) * ev(n.b),
  len: (n, ev) => { const v = ev(n.a); if (!Array.isArray(v)) throw new Error("program-type: len of non-array"); return v.length; },
};
function programSemId(ast) { return "psem-" + H("TRVM-PROGRAM-v1|" + canonicalBytes(ast)); }
function deepFreeze(v) {
  if (v === null || typeof v !== "object" || Object.isFrozen(v)) return v;
  Object.freeze(v);
  for (const k of Object.keys(v)) deepFreeze(v[k]);
  return v;
}
class ProgramRegistry {
  #byId = new Map();
  constructor() { Object.freeze(this); }
  bind(ast) {
    const id = programSemId(ast);
    const frozen = JSON.parse(canonicalBytes(ast));
    deepFreeze(frozen);
    this.#byId.set(id, frozen);
    return id;
  }
  get(id) { return this.#byId.get(id); }
  verify(id) {
    const ast = this.#byId.get(id);
    if (!ast) return { ok: false, reason: "program-unknown" };
    return programSemId(ast) === id ? { ok: true } : { ok: false, reason: "program-id-mismatch" };
  }
}
const REQUEST_FIELDS = ["request_id", "program_sem_id", "implementation_id", "canonical_inputs", "grants"];
function checkRequest(req) {
  if (req === null || typeof req !== "object" || Array.isArray(req))
    return { ok: false, reason: "request-not-an-object" };
  const keys = Object.keys(req).sort();
  const want = [...REQUEST_FIELDS].sort();
  if (canonicalBytes(keys) !== canonicalBytes(want))
    return { ok: false, reason: "request-schema: [" + keys.join(",") + "]" };
  try { canonicalBytes(req); }
  catch (e) { return { ok: false, reason: "request-" + e.message }; }
  if (typeof req.program_sem_id !== "string" || !req.program_sem_id.startsWith("psem-"))
    return { ok: false, reason: "request-program-id-malformed" };
  if (!Array.isArray(req.grants)) return { ok: false, reason: "request-grants-not-a-list" };
  return { ok: true };
}
function evaluate(ast, reader, inputs = {}) {
  const exact = [], predicates = [], support = [];
  const ev = (n) => {
    if (n === null || typeof n !== "object" || typeof n.op !== "string")
      throw new Error("program-malformed-node");
    switch (n.op) {
      case "const": return OPS.const(n);
      case "input": {
        if (!Object.prototype.hasOwnProperty.call(inputs, n.name))
          throw new Error("program-input-missing: " + n.name);
        return inputs[n.name];                       // <<< W-1 LIVES HERE: any canonical input
      }
      case "read": {
        const r = reader.read(n.resource);
        exact.push([n.resource, r.version]);
        support.push(n.resource);
        return r.value;
      }
      case "scope": {
        const d = reader.scope(n.query);
        predicates.push([n.query, d]);
        return d;
      }
      case "cite": {
        const r = reader.read("warrant:" + n.name);
        exact.push(["warrant:" + n.name, r.version]);
        support.push("warrant:" + n.name);
        return r.value?.value;
      }
      case "add": case "sub": case "mul": case "len":
        return OPS[n.op](n, ev);
      default: throw new Error("program-unknown-op: " + n.op);
    }
  };
  const value = ev(ast);
  return { value, witness: { op: ast.op, reads: exact.length },
    support: [...new Set(support)].sort(), read_footprint: { exact, predicates } };
}

/* derive_worker.mjs v0.1.0, verbatim */
const reg = new ProgramRegistry();
for (const ast of workerData.programs) reg.bind(ast);
parentPort.on("message", (req) => {
  const c = checkRequest(req);
  if (!c.ok) { parentPort.postMessage({ ok: false, reason: c.reason }); return; }
  const v = reg.verify(req.program_sem_id);
  if (!v.ok) { parentPort.postMessage({ ok: false, reason: v.reason }); return; }
  const ast = reg.get(req.program_sem_id);
  const reads = req.canonical_inputs.__reads ?? {};   // <<< W-1: the grant table IS an input
  const reader = {
    read: (r) => { if (!(r in reads)) throw new Error("read-not-granted: " + r); return reads[r]; },
    scope: (q) => { if (!(q in reads)) throw new Error("scope-not-granted: " + q); return reads[q].value; },
  };
  try {
    const out = evaluate(ast, reader, req.canonical_inputs);
    parentPort.postMessage({ ok: true, result: {                 // <<< W-2: no implementation_id
      request_id: req.request_id, program_sem_id: req.program_sem_id,
      value: out.value, witness: out.witness, support: out.support,
      read_footprint: out.read_footprint } });
  } catch (e) { parentPort.postMessage({ ok: false, reason: "derivation-threw: " + e.message }); }
});
`;

const frozenURL = new URL("data:text/javascript," + encodeURIComponent(FROZEN_V010));
const spawn = (src, programs) => {
  const w = src === "frozen"
    ? new Worker(frozenURL, { workerData: { programs } })
    : new Worker(join(HERE, "derive_worker.mjs"), { workerData: { programs } });
  return { w, ask: (req) => new Promise((res) => { w.once("message", res); w.postMessage(req); }) };
};

/* ── W-1 against the frozen v0.1.0: the read table is reachable as an input ── */
const EXFIL = { op: "input", name: "__reads" };
{
  const { w, ask } = spawn("frozen", [EXFIL]);
  const pid = "psem-" + (await import("node:crypto")).createHash("sha256")
    .update('TRVM-PROGRAM-v1|{"name":"__reads","op":"input"}').digest("hex");
  const r = await ask({
    request_id: "w1", program_sem_id: pid, implementation_id: "impl-js-derive-v0.1.0",
    canonical_inputs: { __reads: { "secret:key": { value: 42, version: 7 } } }, grants: [],
  });
  const got = r.ok ? r.result.value?.["secret:key"]?.value : null;
  const tracked = r.ok ? r.result.read_footprint.exact.length : -1;
  R("W-1 frozen-v0.1.0", !(got === 42 && tracked === 0),
    `program {op:"input",name:"__reads"} returned the whole grant table (secret:key = ${got}) ` +
    `with witness.reads = ${r.ok && r.result.witness.reads}, support = ${JSON.stringify(r.ok && r.result.support)}, ` +
    `read_footprint.exact = ${JSON.stringify(r.ok && r.result.read_footprint.exact)} — ` +
    `a read that consumed authority data and produced no dependency record`);
  await w.terminate();
}

/* ── W-2 against the frozen v0.1.0: the caller names the executor ─────────── */
{
  const P = { op: "const", value: 1 };
  const { w, ask } = spawn("frozen", [P]);
  const pid = "psem-" + (await import("node:crypto")).createHash("sha256")
    .update('TRVM-PROGRAM-v1|{"op":"const","value":1}').digest("hex");
  const r = await ask({
    request_id: "w2", program_sem_id: pid, implementation_id: "impl-c-pretend-v9",
    canonical_inputs: {}, grants: [],
  });
  R("W-2 frozen-v0.1.0", !(r.ok && !("implementation_id" in r.result)),
    `a request asserting implementation_id "impl-c-pretend-v9" was executed by the JS evaluator ` +
    `and returned ok=${r.ok}; the result carries no implementation_id at all ` +
    `(fields: ${r.ok ? Object.keys(r.result).sort().join(",") : "—"}) — nothing to verify against`);
  await w.terminate();
}

/* ── the same two witnesses against the LIVE modules ──────────────────────── */
{
  const reg = new LiveRegistry(); const pid = reg.bind(EXFIL);
  const { w, ask } = spawn("live", [EXFIL]);
  const grants = { exact: { "secret:key": { value: 42, version: 7 } }, predicates: {} };
  const r = await ask({
    request_id: "w1b", program_sem_id: pid, canonical_inputs: { __reads: "not the grant table" },
    read_grants: grants, grant_id: liveGrantId(grants),
  });
  R("W-1 live", r.ok && r.result.semantic_result.value === "not the grant table",
    `the same program now returns only what the CALLER put in canonical_inputs ` +
    `(${JSON.stringify(r.ok ? r.result.semantic_result.value : r.reason)}); read_grants is a separate field the ` +
    `input op cannot address, so the grant table is not reachable without a tracked read`);
  await w.terminate();
}
{
  const P = { op: "const", value: 1 };
  const reg = new LiveRegistry(); const pid = reg.bind(P);
  const { w, ask } = spawn("live", [P]);
  const grants = { exact: {}, predicates: {} };
  const base = { request_id: "w2b", program_sem_id: pid, canonical_inputs: {},
    read_grants: grants, grant_id: liveGrantId(grants) };
  const honest = await ask(base);
  const impersonated = await ask({ ...base, expected_implementation_id: "impl-c-pretend-v9" });
  R("W-2 live", honest.ok && honest.result.execution_evidence.implementation_id === LIVE_IMPL
      && !impersonated.ok && /implementation-mismatch/.test(impersonated.reason),
    `the executor asserts its own id (${honest.ok && honest.result.execution_evidence.implementation_id}); a request ` +
    `demanding "impl-c-pretend-v9" is refused by the executor itself (${impersonated.reason}) ` +
    `— the caller's field is a REQUIREMENT, the result's field is an ASSERTION`);
  await w.terminate();
}

console.log("=".repeat(100));
const frozenHeld = results.filter((r) => r.id.includes("frozen") && r.held);
const liveBreached = results.filter((r) => r.id.includes("live") && !r.held);
const bad = frozenHeld.length + liveBreached.length;
console.log(
  `DERIVE-GRANT-v0.2 REPRO: ${results.filter((r) => r.id.includes("frozen") && !r.held).length}/2 reproduce against ` +
  `the frozen v0.1.0 · ${results.filter((r) => r.id.includes("live") && r.held).length}/2 confined against live` +
  (frozenHeld.length ? ` — VACUOUS: ${frozenHeld.map((r) => r.id).join(", ")} no longer reproduces, so it has stopped measuring` : "") +
  (liveBreached.length ? ` — REGRESSION: ${liveBreached.map((r) => r.id).join(", ")}` : ""));
process.exit(bad ? 1 : 0);
