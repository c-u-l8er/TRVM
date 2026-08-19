/* derive_realm_battery.mjs — the crossing itself, v0.4.0.
   The claim under test is narrow and stated as such: OBJECT authority does not
   cross, the derivation realm reads only what it was granted, and the executor
   — not the caller — says which implementation ran. Determinism and host
   confinement are separate scopes and this battery does not touch them.
   Run: node derive_realm_battery.mjs */
import { Worker } from "node:worker_threads";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  ProgramRegistry, programSemId, canonicalBytes, validateForeignResult,
  resolveGrants, grantId, semanticProjection, JS_IMPLEMENTATION_ID,
} from "./derive_protocol.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const reg = new ProgramRegistry(); const PID = reg.bind(P);
let fail = false;
const R = (id, ok, note) => { if (!ok) fail = true; console.log(`${ok ? "PASS" : "FAIL"}  ${id.padEnd(32)} ${note}`); };

const w = new Worker(join(HERE, "derive_worker.mjs"), { workerData: { programs: [P] } });
const ask = (req) => new Promise((res) => { w.once("message", res); w.postMessage(req); });

// the authority resolves the snapshot on the authoritative side, once
const worldReader = { read: (r) => ({ value: { fb: 5, "secret:key": 42 }[r], version: 1 }),
  scope: (q) => "scope:" + q };
const { read_grants, grant_id } = resolveGrants(worldReader, { exact: ["fb"] });
const mkReq = (over = {}) => ({ request_id: "r1", program_sem_id: PID,
  canonical_inputs: { bias: 0 }, read_grants, grant_id, ...over });

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

// 2. an honest derivation crosses and comes back as a CLAIM, stamped by its executor
const honest = await ask(mkReq());
R("crossing-derives", honest.ok && honest.result.value === 5
    && honest.result.implementation_id === JS_IMPLEMENTATION_ID && honest.result.grant_id === grant_id,
  `worker returned value ${honest.ok && honest.result.value} for fb=5 bias=0, resolving the program from ` +
  `its OWN registry by id and stamping the result ${honest.ok && honest.result.implementation_id} against ` +
  `grant ${grant_id.slice(0, 18)}…`);

// 3. and the claim is only evidence once the authority re-derives it
{
  const req = mkReq();
  const local = validateForeignResult(reg, req, honest.result);
  const lied = validateForeignResult(reg, req, { ...honest.result, value: 1005 });
  R("claim-revalidated-at-home", local.ok && !lied.ok && lied.reason === "foreign-result-divergence",
    `the worker's honest result reproduces locally against the same snapshot; an inflated one is ` +
    `refused (${lied.reason})`);
}

// 4. the worker cannot read anything it was not granted
{
  const empty = { exact: {}, predicates: {} };
  const r = await ask(mkReq({ read_grants: empty, grant_id: grantId(empty) }));
  R("ungranted-read-refused", !r.ok && /read-not-granted: fb/.test(r.reason),
    `${r.reason} — resolving reads is an AUTHORITY operation the parent performs; the worker holds no ` +
    `world and needs none`);
}

// 5. an unknown program is refused on the far side too
{
  const r = await ask(mkReq({ program_sem_id: programSemId({ op: "const", value: 1 }) }));
  R("unknown-program-refused", !r.ok && r.reason === "program-unknown",
    `${r.reason} — the worker resolves ids against its own registry, so a caller cannot name code the ` +
    `worker does not hold`);
}

// 6. THE GRANT TABLE IS NOT AN INPUT (W-1, across the boundary this time)
{
  const exfil = { op: "input", name: "__reads" };
  const reg2 = new ProgramRegistry(); const XID = reg2.bind(exfil);
  const w2 = new Worker(join(HERE, "derive_worker.mjs"), { workerData: { programs: [exfil] } });
  const ask2 = (req) => new Promise((res) => { w2.once("message", res); w2.postMessage(req); });
  const wide = resolveGrants(worldReader, { exact: ["fb", "secret:key"] });
  const r = await ask2({ request_id: "x", program_sem_id: XID,
    canonical_inputs: { __reads: "an ordinary input" },
    read_grants: wide.read_grants, grant_id: wide.grant_id });
  R("grant-not-reachable-as-input", r.ok && r.result.value === "an ordinary input"
      && r.result.read_footprint.exact.length === 0 && r.result.witness.reads === 0,
    `the worker granted fb and secret:key returns ${JSON.stringify(r.ok && r.result.value)} for ` +
    `{op:"input",name:"__reads"} — at v0.1.0 this returned the whole grant table across the same ` +
    `boundary, with an empty footprint and zero tracked reads`);
  await w2.terminate();
}

// 7. the far side asserts its identity, and refuses a requirement it cannot meet
{
  const r = await ask(mkReq({ expected_implementation_id: "impl-c-pretend-v9" }));
  const ok2 = await ask(mkReq({ expected_implementation_id: JS_IMPLEMENTATION_ID }));
  R("executor-asserts-implementation", !r.ok && /implementation-mismatch: want impl-c-pretend-v9/.test(r.reason)
      && ok2.ok && ok2.result.implementation_id === JS_IMPLEMENTATION_ID,
    `a request demanding a C executor is refused by the JS worker (${r.reason}); one demanding JS runs ` +
    `and returns its own id. The caller states a requirement; the executor answers it`);
}

// 8. a forged footprint from the far side dies against the snapshot
{
  const req = mkReq();
  const forged = { ...honest.result, witness: { ...honest.result.witness, reads: 2 },
    read_footprint: { exact: [["fb", 1], ["secret:key", 1]], predicates: [] },
    read_trace: { exact: [["fb", 1], ["secret:key", 1]], predicates: [] } };
  const v = validateForeignResult(reg, req, forged);
  R("foreign-footprint-refused", !v.ok && v.reason === "footprint-ungranted-read: secret:key",
    `${v.reason} — the authority checks the returned footprint against the grant it issued, on its own ` +
    `evidence. The footprint is the dependency record and the grant is the capability record; the ` +
    `round-14 prose collapsed them and the mechanism supported neither`);
}

// 9. a conforming foreign implementation validates on the semantic projection
{
  const req = mkReq();
  const asIfC = { ...honest.result, implementation_id: "impl-c-derive-v0.4.0" };
  const v = validateForeignResult(reg, req, asIfC);
  R("cross-implementation-shape", v.ok && v.implementation_id === "impl-c-derive-v0.4.0"
      && canonicalBytes(semanticProjection(asIfC)) === canonicalBytes(semanticProjection(honest.result)),
    `the same result stamped by a C executor validates and its provenance is RECORDED rather than ` +
    `compared away. This is the shape a real C implementation plugs into — it is not a claim that one ` +
    `exists, and this battery does not have one`);
}

await w.terminate();
console.log("═".repeat(96));
console.log(fail ? "DERIVE-REALM: FAIL"
  : "DERIVE-REALM: PASS — object authority does not cross the boundary, the realm reads only its grant, " +
    "and the executor names itself. Determinism and host confinement are SEPARATE scopes and are not claimed here.");
process.exit(fail ? 1 : 0);
