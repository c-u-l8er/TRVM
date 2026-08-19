/* derive_worker.mjs — v0.4.0 — the far side of the realm boundary.
   Holds NO parent reference of any kind: it receives canonical data on a
   message port, resolves the program from its OWN registry by id, evaluates
   against the grant snapshot the request carries, and posts back canonical
   data. It cannot read the World — and does not need to, because resolving
   reads is an AUTHORITY operation performed by the parent before the request
   is sent, while computation is not. That split is what makes the worker's
   capability set empty: it holds none because it needs none.

   Two things this file must NOT do, each of which it did at v0.1.0:

   1. It must not source its read table from `canonical_inputs`. The language
      has `{op:"input", name:…}`, so anything reachable as an input is
      reachable WITHOUT a tracked read — which made the read footprint
      bypassable and the round-14 claim about it false. Reads now come from
      `read_grants`, a separate request field the `input` op cannot address,
      and the evaluator builds its own reader from it.
   2. It must not echo the caller's implementation_id. The executor ASSERTS
      its identity; the caller may only state a REQUIREMENT, which this worker
      refuses when it cannot satisfy it. A field the caller sets and nobody
      checks is decoration, and the film identity split needs provenance.

   Scope, unchanged and still not claimed: this is object confinement. A worker
   holding `let counter = 0` leaks no parent authority and still fails to make
   program_sem_id denote a stable function, and Date.now, Math.random, the
   filesystem and the network remain reachable from here. */
import { parentPort, workerData } from "node:worker_threads";
import { ProgramRegistry, evaluate, checkRequest, JS_IMPLEMENTATION_ID } from "./derive_protocol.mjs";

const reg = new ProgramRegistry();
for (const ast of workerData.programs) reg.bind(ast);   // resolved HERE, from data

parentPort.on("message", (req) => {
  const c = checkRequest(req);
  if (!c.ok) { parentPort.postMessage({ ok: false, reason: c.reason }); return; }
  // the caller's expectation is a requirement on the EXECUTOR, and this
  // executor is the only thing that knows what it is
  if ("expected_implementation_id" in req && req.expected_implementation_id !== JS_IMPLEMENTATION_ID) {
    parentPort.postMessage({ ok: false, reason: "implementation-mismatch: want " +
      req.expected_implementation_id + ", this is " + JS_IMPLEMENTATION_ID });
    return;
  }
  const v = reg.verify(req.program_sem_id);
  if (!v.ok) { parentPort.postMessage({ ok: false, reason: v.reason }); return; }
  const ast = reg.get(req.program_sem_id);
  try {
    // reads come from the grant snapshot and nowhere else; the evaluator is
    // handed canonical data rather than a reader callable
    const out = evaluate(ast, req.read_grants, req.canonical_inputs);
    parentPort.postMessage({ ok: true, result: {
      request_id: req.request_id, program_sem_id: req.program_sem_id,
      implementation_id: JS_IMPLEMENTATION_ID, grant_id: req.grant_id,
      value: out.value, witness: out.witness, support: out.support,
      read_footprint: out.read_footprint, read_trace: out.read_trace } });
  } catch (e) { parentPort.postMessage({ ok: false, reason: "derivation-threw: " + e.message }); }
});
