/* derive_battery.mjs — falsifiers for the serialized derivation boundary, v0.2.0.
   Written before the protocol is believed, per the house rule. Every case that
   must be refused asserts the EXACT refusal string, so a repair that changes
   what is refused cannot pass by refusing for a different reason.
   Run: node derive_battery.mjs   (exit 0 iff green) */
import {
  ProgramRegistry, programSemId, canonicalBytes, checkRequest, checkResult,
  deriveLocally, validateForeignResult, evaluate, resolveGrants, grantId,
  footprintWithinGrant, semanticProjection, JS_IMPLEMENTATION_ID,
} from "./derive_protocol.mjs";

const rows = [];
let fail = false;
const R = (id, ok, note) => { if (!ok) fail = true; rows.push({ id, ok, note });
  console.log(`${ok ? "PASS" : "FAIL"}  ${id.padEnd(34)} ${note}`); };

// a tiny deterministic program: (read fb) + input(bias)
const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const reg = new ProgramRegistry();
const PID = reg.bind(P);

// the World-side reader the AUTHORITY uses to resolve a snapshot. It never
// crosses the boundary; it is used once, here, on the authoritative side.
const worldReader = (vals) => ({
  read: (r) => ({ value: vals[r], version: 1 }),
  scope: (q) => "scope:" + q,
});
const snapshot = (vals, want = { exact: Object.keys(vals) }) =>
  resolveGrants(worldReader(vals), want);

const mkReq = (over = {}) => {
  const { read_grants, grant_id } = snapshot({ fb: 5 });
  return { request_id: "req-1", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, read_grants, grant_id, ...over };
};

// ── 1. the id is the program, so a caller cannot choose it ────────────────
{
  const other = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "const", value: 1000 } };
  const otherId = programSemId(other);
  R("program-id-is-content", PID !== otherId && PID === programSemId(P),
    `two programs, two ids (${PID.slice(0, 14)}… vs ${otherId.slice(0, 14)}…); recomputing P's id reproduces it`);
  // the 9D.4 shape: claim an honest program id while meaning a different program
  const reg2 = new ProgramRegistry();
  reg2.bind(other);
  const r = deriveLocally(reg2, mkReq());
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
    results.map(([n, ok]) => `${n}:${ok ? "refused" : "ADMITTED"}`).join(" ") +
    ` — structuredClone would have accepted Map, Set and Date; the canonical domain does not`);
  // and the schema itself is closed in both directions
  const extra = checkRequest({ ...mkReq(), extra_capability: 1 });
  const missing = checkRequest({ request_id: "r", program_sem_id: PID });
  R("request-schema-closed", !extra.ok && /unknown \[extra_capability\]/.test(extra.reason)
      && !missing.ok && /missing \[/.test(missing.reason),
    `an unknown field is refused (${extra.reason}) and a short request names what it lacks ` +
    `(${missing.reason.slice(0, 62)}…)`);
}

// ── 3. an honest derivation, and its footprint ───────────────────────────
{
  const r = deriveLocally(reg, mkReq());
  const r2 = deriveLocally(reg, mkReq({ canonical_inputs: { bias: 1000 } }));
  R("derivation-honest", r.ok && r.result.value === 5 && r2.ok && r2.result.value === 1005,
    `bias 0 -> ${r.ok && r.result.value}, bias 1000 -> ${r2.ok && r2.result.value}; the bias is an ` +
    `INPUT of the request, so it is visible in canonical_inputs instead of hiding in a lexical cell`);
  R("footprint-recorded", r.ok && canonicalBytes(r.result.read_footprint.exact) === canonicalBytes([["fb", 1]])
      && r.result.witness.reads === 1,
    `read_footprint.exact = ${JSON.stringify(r.ok && r.result.read_footprint.exact)} — reads are tracked ` +
    `by the evaluator on access, not declared by the caller`);
}

// ── 4. the 9D.4 witness has nowhere to live ──────────────────────────────
// The whole attack was a shared lexical cell mutated between derivations. A
// program is data and the evaluator is handed canonical grants and inputs;
// there is no captured environment to mutate, and two derivations of the same
// request must agree.
{
  const req = mkReq();
  const a = deriveLocally(reg, req);
  const b = deriveLocally(reg, req);
  R("no-ambient-cell", a.ok && b.ok && canonicalBytes(a.result) === canonicalBytes(b.result),
    `the same request derives identically twice; there is no environment between them to mutate ` +
    `(law:derivation.environment-confinement@1 is FALSIFIED for the closure API and this is the replacement path)`);
  // v0.2.0: the reader is no longer a caller-supplied callable either
  let readerRefusal = "IT WAS ACCEPTED";
  try { evaluate(P, { read: () => ({ value: 9, version: 1 }), scope: () => "s" }, { bias: 0 }); }
  catch (e) { readerRefusal = e.message; }
  R("reader-is-not-a-callable", readerRefusal === "grants-schema: [read,scope]",
    `evaluate(ast, read_grants, inputs) builds its own reader from canonical grant data. A pair of ` +
    `reader CALLABLES in the grant position is refused as data (${readerRefusal}) — v0.1.0 took the ` +
    `reader as a parameter, which was the closure-authority shape in miniature`);
}

// ── 5. THE GRANT AND THE FOOTPRINT ARE TWO RECORDS (the v0.1.0 defect) ───
{
  // W-1: a program that addresses the grant table as an input gets inputs only
  const exfil = { op: "input", name: "__reads" };
  const reg3 = new ProgramRegistry(); const XID = reg3.bind(exfil);
  const { read_grants, grant_id } = snapshot({ "secret:key": 42 });
  const r = deriveLocally(reg3, { request_id: "x", program_sem_id: XID,
    canonical_inputs: { __reads: "an ordinary input" }, read_grants, grant_id });
  R("grant-not-reachable-as-input", r.ok && r.result.value === "an ordinary input"
      && r.result.read_footprint.exact.length === 0,
    `{op:"input",name:"__reads"} returns ${JSON.stringify(r.ok && r.result.value)} — at v0.1.0 it ` +
    `returned the entire authority grant table with witness.reads = 0. read_grants is a separate ` +
    `request field and the input op cannot address it (W-1, frozen in probe_derivegrant_v02_repro.mjs)`);

  // the grant may be WIDER than the footprint, and that is the point: freshness
  // keys on what was read, not on what was made available
  const wide = snapshot({ fb: 5, unused_a: 1, unused_b: 2 });
  const r2 = deriveLocally(reg, { request_id: "w", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, read_grants: wide.read_grants, grant_id: wide.grant_id });
  R("footprint-is-the-access-subset",
    r2.ok && Object.keys(wide.read_grants.exact).length === 3 && r2.result.read_footprint.exact.length === 1,
    `grant covers ${Object.keys(wide.read_grants.exact).sort().join(",")} (3 resources); the footprint ` +
    `records ${JSON.stringify(r2.result.read_footprint.exact)} (1). Defining the footprint AS the grant ` +
    `would invalidate this derivation whenever unused_a moved, which it does not depend on`);

  // grant_id binds the snapshot: naming one grant while carrying another fails
  const tampered = { exact: { fb: { value: 1005, version: 1 } }, predicates: {} };
  const c = checkRequest({ ...mkReq(), read_grants: tampered });
  R("grant-id-binds-the-snapshot", !c.ok && c.reason === "request-grant-id-mismatch",
    `a request carrying a swapped snapshot under the original grant_id is refused: ${c.reason} ` +
    `— the id is H(canonical read_grants), so the snapshot cannot be edited in flight`);
}

// ── 6. the authority validates the footprint on its OWN evidence ─────────
{
  const req = mkReq();
  const honest = deriveLocally(reg, req).result;
  // over-claiming: a footprint naming a resource the authority never granted
  const overclaim = validateForeignResult(reg, req, { ...honest,
    witness: { ...honest.witness, reads: 2 },
    read_footprint: { exact: [["fb", 1], ["secret:key", 1]], predicates: [] } });
  // version forgery: the right resource at a version the grant does not carry
  const wrongVer = validateForeignResult(reg, req, { ...honest,
    read_footprint: { exact: [["fb", 99]], predicates: [] } });
  // and the subset check is INDEPENDENT of re-derivation: it fires here even
  // though the value is honest and would have re-derived equal
  const direct = footprintWithinGrant({ exact: [["nope", 1]], predicates: [] }, req.read_grants);
  R("footprint-validated-independently",
    !overclaim.ok && overclaim.reason === "footprint-ungranted-read: secret:key"
      && !wrongVer.ok && wrongVer.reason === "footprint-version-mismatch: fb"
      && !direct.ok && direct.reason === "footprint-ungranted-read: nope",
    `over-claimed read -> ${overclaim.reason}; forged version -> ${wrongVer.reason}. Both refused ` +
    `against the SNAPSHOT rather than against the executor's word, before any re-derivation`);
  // the witness may not disagree with the footprint it accompanies
  const inconsistent = checkResult({ ...honest, witness: { op: "add", reads: 7, scopes: 0 } }, req);
  R("witness-matches-footprint", !inconsistent.ok && inconsistent.reason === "result-witness-inconsistent",
    `a result claiming 7 reads with a 1-entry footprint is refused: ${inconsistent.reason}`);
}

// ── 7. a foreign result is a CLAIM until the authority re-derives it ─────
{
  const req = mkReq();
  const honest = deriveLocally(reg, req).result;
  const good = validateForeignResult(reg, req, honest);
  const lied = validateForeignResult(reg, req, { ...honest, value: 1005 });
  const wrongReq = validateForeignResult(reg, req, { ...honest, request_id: "req-2" });
  const wrongProg = validateForeignResult(reg, req, { ...honest, program_sem_id: programSemId({ op: "const", value: 1 }) });
  const wrongGrant = validateForeignResult(reg, req, { ...honest, grant_id: grantId({ exact: {}, predicates: {} }) });
  R("foreign-result-revalidated",
    good.ok && !lied.ok && lied.reason === "foreign-result-divergence"
      && !wrongReq.ok && wrongReq.reason === "result-request-mismatch"
      && !wrongProg.ok && wrongProg.reason === "result-program-mismatch"
      && !wrongGrant.ok && wrongGrant.reason === "result-grant-mismatch",
    `honest accepted; inflated value -> ${lied.reason}; re-labelled request -> ${wrongReq.reason}; ` +
    `re-labelled program -> ${wrongProg.reason}; re-labelled grant -> ${wrongGrant.reason}. Across a ` +
    `realm this is the entire trust story: the far side produces a claim, the authority reproduces it`);
}

// ── 8. implementation_id is the EXECUTOR's assertion, not the caller's ───
{
  const req = mkReq();
  const honest = deriveLocally(reg, req).result;
  R("implementation-id-asserted", honest.implementation_id === JS_IMPLEMENTATION_ID,
    `the result carries ${honest.implementation_id}, emitted by the evaluator that ran. At v0.1.0 the ` +
    `REQUEST carried implementation_id, nothing checked it and the result carried none (W-2)`);
  const demand = deriveLocally(reg, { ...req, expected_implementation_id: "impl-c-pretend-v9" });
  R("implementation-requirement-refused", !demand.ok
      && demand.reason === "implementation-mismatch: want impl-c-pretend-v9, this is " + JS_IMPLEMENTATION_ID,
    `a request demanding a C executor is refused BY the JS executor (${demand.reason}) — the caller's ` +
    `field states a requirement and the executor answers it, so impersonation has no path`);
  const malformed = checkResult({ ...honest, implementation_id: "js" }, req);
  R("implementation-id-well-formed", !malformed.ok && malformed.reason === "result-implementation-id-malformed",
    `a result whose implementation_id is not an impl- identity is refused: ${malformed.reason}`);

  // THE POINT OF THE SPLIT: a conforming foreign implementation validates, and
  // its provenance is reported rather than compared away. Comparing whole
  // results would make cross-implementation validation fail by construction.
  const asIfC = { ...honest, implementation_id: "impl-c-derive-v0.2.0" };
  const v = validateForeignResult(reg, req, asIfC);
  const sameSemantics = canonicalBytes(semanticProjection(asIfC)) === canonicalBytes(semanticProjection(honest));
  R("semantic-projection-is-portable", v.ok && v.implementation_id === "impl-c-derive-v0.2.0" && sameSemantics,
    `a result identical in semantics but produced by impl-c-derive-v0.2.0 validates, and the authority ` +
    `records WHO ran it (${v.implementation_id}). program_sem_id is equal across implementations; ` +
    `implementation_id is outside the semantic projection, which is what makes a portable film possible`);
  // and the requirement is enforced against the foreign claim too
  const mismatched = validateForeignResult(reg, { ...req, expected_implementation_id: JS_IMPLEMENTATION_ID }, asIfC);
  R("implementation-requirement-checked-on-result", !mismatched.ok && /implementation-mismatch: want/.test(mismatched.reason),
    `a result from a different executor than the one required is refused: ${mismatched.reason}`);
}

// ── 9. the registry cannot be made to lie ────────────────────────────────
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
  : `DERIVE-BATTERY: PASS — ${rows.length}/${rows.length}. The program is data and its id is its hash; the ` +
    `grant is what the authority made available and the footprint is what the program consumed; the ` +
    `executor asserts its own identity; and a foreign result is re-derived before it is evidence.`);
process.exit(fail ? 1 : 0);
