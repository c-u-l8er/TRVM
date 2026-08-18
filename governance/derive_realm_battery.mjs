/* derive_realm_battery.mjs — the crossing itself.
   The claim under test is narrow and stated as such: OBJECT authority does not
   cross. Determinism and host confinement are separate scopes and this battery
   does not touch them. Run: node derive_realm_battery.mjs */
import { Worker } from "node:worker_threads";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { ProgramRegistry, programSemId, canonicalBytes, validateForeignResult, JS_IMPLEMENTATION_ID } from "./derive_protocol.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const reg = new ProgramRegistry(); const PID = reg.bind(P);
let fail = false;
const R = (id, ok, note) => { if (!ok) fail = true; console.log(`${ok ? "PASS" : "FAIL"}  ${id.padEnd(30)} ${note}`); };

const w = new Worker(join(HERE, "derive_worker.mjs"), { workerData: { programs: [P] } });
const ask = (req) => new Promise((res) => { w.once("message", res); w.postMessage(req); });
const mkReq = (over = {}) => ({ request_id: "r1", program_sem_id: PID,
  implementation_id: JS_IMPLEMENTATION_ID, canonical_inputs: { bias: 0, __reads: { fb: { value: 5, version: 1 } } },
  grants: [], ...over });

// 1. a callable cannot cross at all — the transport refuses it
{
  let threw = null;
  try { w.postMessage({ ...mkReq(), canonical_inputs: { bias: 0, evil: () => 1 } }); }
  catch (e) { threw = e.name + ": " + String(e.message).slice(0, 60); }
  R("closure-cannot-cross", threw !== null,
    `postMessage of a request carrying a function throws — ${threw ?? "IT CROSSED"}. ` +
    `The 9D.4 lexical-cell attack has no transport: structured cloning refuses callables, ` +
    `so the confinement is done by the boundary rather than by object discipline`);
}

// 2. an honest derivation crosses and comes back as a CLAIM
const honest = await ask(mkReq());
R("crossing-derives", honest.ok && honest.result.value === 5,
  `worker returned value ${honest.ok && honest.result.value} for fb=5 bias=0, resolving the program from its OWN registry by id`);

// 3. and the claim is only evidence once the authority re-derives it
{
  const reader = { read: (r) => ({ value: { fb: 5 }[r], version: 1 }), scope: (q) => "s" };
  const req = { ...mkReq(), canonical_inputs: { bias: 0 } };
  const local = validateForeignResult(reg, req, { ...honest.result,
    read_footprint: { exact: [["fb", 1]], predicates: [] } }, reader);
  const lied = validateForeignResult(reg, req, { ...honest.result, value: 1005,
    read_footprint: { exact: [["fb", 1]], predicates: [] } }, reader);
  R("claim-revalidated-at-home", local.ok && !lied.ok && lied.reason === "foreign-result-divergence",
    `the worker's honest result reproduces locally; an inflated one is refused (${lied.reason})`);
}

// 4. the worker cannot read anything it was not granted
{
  const r = await ask(mkReq({ canonical_inputs: { bias: 0, __reads: {} } }));
  R("ungranted-read-refused", !r.ok && /read-not-granted/.test(r.reason),
    `${r.reason} — reads are an AUTHORITY operation the parent performs; the worker holds no world and needs none`);
}

// 5. an unknown program is refused on the far side too
{
  const r = await ask(mkReq({ program_sem_id: programSemId({ op: "const", value: 1 }) }));
  R("unknown-program-refused", !r.ok && r.reason === "program-unknown",
    `${r.reason} — the worker resolves ids against its own registry, so a caller cannot name code the worker does not hold`);
}

await w.terminate();
console.log("═".repeat(96));
console.log(fail ? "DERIVE-REALM: FAIL"
  : "DERIVE-REALM: PASS — object authority does not cross the boundary. " +
    "Determinism and host confinement are SEPARATE scopes and are not claimed here.");
process.exit(fail ? 1 : 0);
