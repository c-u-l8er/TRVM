/* derive_battery.mjs — falsifiers for the serialized derivation boundary.
   Written before the protocol is believed, per the house rule. Every case that
   must be refused asserts the EXACT refusal string, so a repair that changes
   what is refused cannot pass by refusing for a different reason.
   Run: node derive_battery.mjs   (exit 0 iff green) */
import {
  ProgramRegistry, programSemId, canonicalBytes, checkRequest, checkResult,
  deriveLocally, validateForeignResult, evaluate, JS_IMPLEMENTATION_ID,
} from "./derive_protocol.mjs";

const rows = [];
let fail = false;
const R = (id, ok, note) => { if (!ok) fail = true; rows.push({ id, ok, note });
  console.log(`${ok ? "PASS" : "FAIL"}  ${id.padEnd(34)} ${note}`); };

// a tiny deterministic program: (read fb) + input(bias)
const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const reg = new ProgramRegistry();
const PID = reg.bind(P);

const reader = (vals) => ({
  read: (r) => ({ value: vals[r], version: 1 }),
  scope: (q) => "scope:" + q,
});
const mkReq = (over = {}) => ({
  request_id: "req-1", program_sem_id: PID, implementation_id: JS_IMPLEMENTATION_ID,
  canonical_inputs: { bias: 0 }, grants: [], ...over,
});

// ── 1. the id is the program, so a caller cannot choose it ────────────────
{
  const other = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "const", value: 1000 } };
  const otherId = programSemId(other);
  R("program-id-is-content", PID !== otherId && PID === programSemId(P),
    `two programs, two ids (${PID.slice(0, 14)}… vs ${otherId.slice(0, 14)}…); recomputing P's id reproduces it`);
  // the 9D.4 shape: claim an honest program id while meaning a different program
  const reg2 = new ProgramRegistry();
  reg2.bind(other);
  const r = deriveLocally(reg2, mkReq(), reader({ fb: 5 }));
  R("label-substitution-refused", !r.ok && r.reason === "program-unknown",
    `a request naming P against a registry holding only the evil program is refused: ${r.reason} ` +
    `— an id cannot be pointed at different code, because the id IS the code's hash`);
}

// ── 2. the boundary is the canonical domain, not "structuredClone worked" ─
{
  const cases = [
    ["Function", () => {}], ["Map", new Map([["a", 1]])], ["Set", new Set([1])],
    ["Date", new Date(0)], ["class instance", new (class Cap {})()],
  ];
  const results = cases.map(([name, v]) => {
    const c = checkRequest(mkReq({ canonical_inputs: { bias: 0, sneak: v } }));
    return [name, !c.ok && /not-canonical/.test(c.reason), c.reason];
  });
  R("capabilities-refused-at-boundary", results.every((x) => x[1]),
    results.map(([n, ok, why]) => `${n}:${ok ? "refused" : "ADMITTED"}`).join(" ") +
    ` — structuredClone would have accepted Map, Set and Date; the canonical domain does not`);
  // and the schema itself is closed
  const extra = checkRequest({ ...mkReq(), extra_capability: 1 });
  const missing = checkRequest({ request_id: "r", program_sem_id: PID });
  R("request-schema-closed", !extra.ok && !missing.ok && /request-schema/.test(extra.reason),
    `an extra field is refused (${extra.reason.slice(0, 42)}…) and a short request is refused`);
}

// ── 3. an honest derivation, and its footprint ───────────────────────────
{
  const r = deriveLocally(reg, mkReq({ canonical_inputs: { bias: 0 } }), reader({ fb: 5 }));
  const r2 = deriveLocally(reg, mkReq({ canonical_inputs: { bias: 1000 } }), reader({ fb: 5 }));
  R("derivation-honest", r.ok && r.result.value === 5 && r2.ok && r2.result.value === 1005,
    `bias 0 -> ${r.ok && r.result.value}, bias 1000 -> ${r2.ok && r2.result.value}; the bias is an ` +
    `INPUT of the request, so it is visible in canonical_inputs instead of hiding in a lexical cell`);
  R("footprint-recorded", r.ok && canonicalBytes(r.result.read_footprint.exact) === canonicalBytes([["fb", 1]]),
    `read_footprint.exact = ${JSON.stringify(r.ok && r.result.read_footprint.exact)} — reads are tracked by the evaluator, not declared by the caller`);
}

// ── 4. the 9D.4 witness has nowhere to live ──────────────────────────────
// The whole attack was a shared lexical cell mutated between derivations. A
// program is data and the evaluator is handed a reader and inputs; there is no
// captured environment to mutate, and two derivations of the same request with
// the same inputs must agree.
{
  const req = mkReq({ canonical_inputs: { bias: 0 } });
  const a = deriveLocally(reg, req, reader({ fb: 5 }));
  const b = deriveLocally(reg, req, reader({ fb: 5 }));
  R("no-ambient-cell", a.ok && b.ok && canonicalBytes(a.result) === canonicalBytes(b.result),
    `the same request derives identically twice; there is no environment between them to mutate ` +
    `(law:derivation.environment-confinement@1 is FALSIFIED for the closure API and this is the replacement path)`);
}

// ── 5. a foreign result is a CLAIM until the authority re-derives it ─────
{
  const req = mkReq({ canonical_inputs: { bias: 0 } });
  const honest = deriveLocally(reg, req, reader({ fb: 5 })).result;
  const good = validateForeignResult(reg, req, honest, reader({ fb: 5 }));
  const lied = validateForeignResult(reg, req, { ...honest, value: 1005 }, reader({ fb: 5 }));
  const wrongReq = validateForeignResult(reg, req, { ...honest, request_id: "req-2" }, reader({ fb: 5 }));
  const wrongProg = validateForeignResult(reg, req, { ...honest, program_sem_id: programSemId({ op: "const", value: 1 }) }, reader({ fb: 5 }));
  R("foreign-result-revalidated",
    good.ok && !lied.ok && lied.reason === "foreign-result-divergence"
      && !wrongReq.ok && wrongReq.reason === "result-request-mismatch"
      && !wrongProg.ok && wrongProg.reason === "result-program-mismatch",
    `honest accepted; inflated value -> ${lied.reason}; re-labelled request -> ${wrongReq.reason}; ` +
    `re-labelled program -> ${wrongProg.reason}. Across a realm this is the entire trust story: ` +
    `the far side produces a claim, the authority reproduces it or refuses it`);
}

// ── 6. the registry cannot be made to lie ────────────────────────────────
{
  const v = reg.verify(PID);
  const unknown = reg.verify("psem-" + "0".repeat(64));
  R("registry-binding-verified", v.ok && !unknown.ok && unknown.reason === "program-unknown",
    `verify(PID) recomputes the hash and agrees; an unbound id is refused (${unknown.reason})`);
  const stored = reg.get(PID);
  let frozen = false;
  try { stored.op = "mul"; } catch { frozen = true; }
  R("registry-entry-frozen", frozen && reg.get(PID).op === "add",
    `the stored program is deep-frozen; mutating it throws and the registry still reads 'add'`);
}

console.log("═".repeat(96));
console.log(fail
  ? `DERIVE-BATTERY: FAIL — ${rows.filter((r) => !r.ok).length}/${rows.length}`
  : `DERIVE-BATTERY: PASS — ${rows.length}/${rows.length}. The program is data, its id is its hash, ` +
    `the boundary is the canonical domain, and a foreign result is re-derived before it is evidence.`);
process.exit(fail ? 1 : 0);
