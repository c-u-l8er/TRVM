/* derive_worker.mjs — the far side of the realm boundary.
   Holds NO parent reference of any kind: it receives canonical data on a
   message port, resolves the program from its OWN registry by id, evaluates,
   and posts back canonical data. It cannot read the World — and does not need
   to, because reads are an AUTHORITY operation performed by the parent before
   the request is sent, while computation is not. That split is what makes the
   worker's grant set empty: it holds no capability because it needs none. */
import { parentPort, workerData } from "node:worker_threads";
import { ProgramRegistry, evaluate, canonicalBytes, checkRequest } from "./derive_protocol.mjs";

const reg = new ProgramRegistry();
for (const ast of workerData.programs) reg.bind(ast);   // resolved HERE, from data

parentPort.on("message", (req) => {
  const c = checkRequest(req);
  if (!c.ok) { parentPort.postMessage({ ok: false, reason: c.reason }); return; }
  const v = reg.verify(req.program_sem_id);
  if (!v.ok) { parentPort.postMessage({ ok: false, reason: v.reason }); return; }
  const ast = reg.get(req.program_sem_id);
  // the only reader available is the pre-resolved read set: no world, no I/O
  const reads = req.canonical_inputs.__reads ?? {};
  const reader = {
    // granted reads arrive as {value, version} — the version is what makes the
    // returned footprint checkable by the authority, so the grant carries it
    read: (r) => { if (!(r in reads)) throw new Error("read-not-granted: " + r); return reads[r]; },
    scope: (q) => { if (!(q in reads)) throw new Error("scope-not-granted: " + q); return reads[q].value; },
  };
  try {
    const out = evaluate(ast, reader, req.canonical_inputs);
    parentPort.postMessage({ ok: true, result: {
      request_id: req.request_id, program_sem_id: req.program_sem_id,
      value: out.value, witness: out.witness, support: out.support,
      read_footprint: out.read_footprint } });
  } catch (e) { parentPort.postMessage({ ok: false, reason: "derivation-threw: " + e.message }); }
});
