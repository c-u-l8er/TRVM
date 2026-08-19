/* derive_battery.mjs — falsifiers for the serialized derivation boundary, v0.4.0.
   Written before the protocol is believed, per the house rule. Every case that
   must be refused asserts the EXACT refusal string, so a repair that changes
   what is refused cannot pass by refusing for a different reason.
   Run: node derive_battery.mjs   (exit 0 iff green) */
import {
  ProgramRegistry, programSemId, canonicalBytes, checkRequest, checkResult,
  deriveLocally, validateForeignResult, evaluate, resolveGrants, grantId,
  footprintWithinGrant, semanticProjection, JS_IMPLEMENTATION_ID,
  CORE_SPEC, CORE_SEM_ID, validateProgram, SEMANTIC_RESULT_FIELDS, EXECUTION_ENVELOPE_FIELDS,
  validateTraceConformance,
  validateFootprintFresh, DerivationAuthority, checkIntent, requestSemId,
} from "./derive_protocol.mjs";
import { createHash } from "node:crypto";

// forgeries must now reach INSIDE the envelope they are forging, which is
// itself the round's point: the shape says which trust status a field carries
const withSem = (r, o) => ({ ...r, semantic_result: { ...r.semantic_result, ...o } });
const withExec = (r, o) => ({ ...r, execution_evidence: { ...r.execution_evidence, ...o } });

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
  R("derivation-honest", r.ok && r.result.semantic_result.value === 5 && r2.ok && r2.result.semantic_result.value === 1005,
    `bias 0 -> ${r.ok && r.result.semantic_result.value}, bias 1000 -> ${r2.ok && r2.result.semantic_result.value}; the bias is an ` +
    `INPUT of the request, so it is visible in canonical_inputs instead of hiding in a lexical cell`);
  R("footprint-recorded", r.ok && canonicalBytes(r.result.semantic_result.read_footprint.exact) === canonicalBytes([["fb", 1]])
      && r.result.semantic_result.witness.reads === 1,
    `read_footprint.exact = ${JSON.stringify(r.ok && r.result.semantic_result.read_footprint.exact)} — reads are tracked ` +
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
  R("grant-not-reachable-as-input", r.ok && r.result.semantic_result.value === "an ordinary input"
      && r.result.semantic_result.read_footprint.exact.length === 0,
    `{op:"input",name:"__reads"} returns ${JSON.stringify(r.ok && r.result.semantic_result.value)} — at v0.1.0 it ` +
    `returned the entire authority grant table with witness.reads = 0. read_grants is a separate ` +
    `request field and the input op cannot address it (W-1, frozen in probe_derivegrant_v02_repro.mjs)`);

  // the grant may be WIDER than the footprint, and that is the point: freshness
  // keys on what was read, not on what was made available
  const wide = snapshot({ fb: 5, unused_a: 1, unused_b: 2 });
  const r2 = deriveLocally(reg, { request_id: "w", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, read_grants: wide.read_grants, grant_id: wide.grant_id });
  R("footprint-is-the-access-subset",
    r2.ok && Object.keys(wide.read_grants.exact).length === 3 && r2.result.semantic_result.read_footprint.exact.length === 1,
    `grant covers ${Object.keys(wide.read_grants.exact).sort().join(",")} (3 resources); the footprint ` +
    `records ${JSON.stringify(r2.result.semantic_result.read_footprint.exact)} (1). Defining the footprint AS the grant ` +
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
  const overclaim = validateForeignResult(reg, req, {
    ...honest,
    semantic_result: { ...honest.semantic_result,
      witness: { ...honest.semantic_result.witness, reads: 2 },
      read_footprint: { exact: [["fb", 1], ["secret:key", 1]], predicates: [] } },
    execution_evidence: { ...honest.execution_evidence,
      read_trace: { exact: [["fb", 1], ["secret:key", 1]], predicates: [] } } });
  // version forgery: the right resource at a version the grant does not carry
  const wrongVer = validateForeignResult(reg, req, {
    ...honest,
    semantic_result: { ...honest.semantic_result, read_footprint: { exact: [["fb", 99]], predicates: [] } },
    execution_evidence: { ...honest.execution_evidence, read_trace: { exact: [["fb", 99]], predicates: [] } } });
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
  const inconsistent = checkResult(withSem(honest, { witness: { op: "add", reads: 7, scopes: 0 } }), req);
  R("witness-matches-footprint", !inconsistent.ok && inconsistent.reason === "result-witness-inconsistent",
    `a result claiming 7 reads with a 1-entry footprint is refused: ${inconsistent.reason}`);
}

// ── 7. a foreign result is a CLAIM until the authority re-derives it ─────
{
  const req = mkReq();
  const honest = deriveLocally(reg, req).result;
  const good = validateForeignResult(reg, req, honest);
  const lied = validateForeignResult(reg, req, withSem(honest, { value: 1005 }));
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
  R("implementation-id-asserted", honest.execution_evidence.implementation_id === JS_IMPLEMENTATION_ID,
    `the result carries ${honest.execution_evidence.implementation_id}, emitted by the evaluator that ran. At v0.1.0 the ` +
    `REQUEST carried implementation_id, nothing checked it and the result carried none (W-2)`);
  const demand = deriveLocally(reg, { ...req, expected_implementation_id: "impl-c-pretend-v9" });
  R("implementation-requirement-refused", !demand.ok
      && demand.reason === "implementation-mismatch: want impl-c-pretend-v9, this is " + JS_IMPLEMENTATION_ID,
    `a request demanding a C executor is refused BY the JS executor (${demand.reason}) — the caller's ` +
    `field states a requirement and the executor answers it, so impersonation has no path`);
  const malformed = checkResult(withExec(honest, { implementation_id: "js" }), req);
  R("implementation-id-well-formed", !malformed.ok && malformed.reason === "result-implementation-id-malformed",
    `a result whose implementation_id is not an impl- identity is refused: ${malformed.reason}`);

  // THE POINT OF THE SPLIT: a conforming foreign implementation validates, and
  // its provenance is reported rather than compared away. Comparing whole
  // results would make cross-implementation validation fail by construction.
  const asIfC = withExec(honest, { implementation_id: "impl-c-derive-v0.6.0" });
  const v = validateForeignResult(reg, req, asIfC);
  const sameSemantics = canonicalBytes(semanticProjection(asIfC)) === canonicalBytes(semanticProjection(honest));
  R("semantic-projection-is-portable", v.ok && v.implementation_id === "impl-c-derive-v0.6.0" && sameSemantics,
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

// ── 10. TRVM-DERIVE-CORE-v1: the id commits SEMANTICS, not just syntax ──
{
  R("core-id-is-content-bound", CORE_SEM_ID === "core-" + createHash("sha256")
      .update("TRVM-DERIVE-CORE-SPEC-v1|" + canonicalBytes(CORE_SPEC)).digest("hex")
      && Object.isFrozen(CORE_SPEC),
    `CORE_SEM_ID recomputes from the frozen CORE_SPEC (${CORE_SEM_ID.slice(0, 20)}…). A bare label ` +
    `"TRVM-DERIVE-CORE-v1" would be the caller-selected-name defect the primitive ruling already refuses`);
  R("program-id-commits-the-core", programSemId(P) === "psem-" + createHash("sha256")
      .update("TRVM-PROGRAM-v2|" + CORE_SEM_ID + "|" + canonicalBytes(P)).digest("hex"),
    `program_sem_id = H("TRVM-PROGRAM-v2|" + core_sem_id + "|" + canonicalBytes(ast)) — change what ` +
    `add means and the core moves and every program id moves with it, which is what makes the id semantic`);
  // the grammar refuses out-of-language programs BEFORE issuing an identity
  const malformed = [
    ["unknown op", { op: "exec", cmd: "rm -rf /" }, /program-unknown-op/],
    ["missing field", { op: "const" }, /program-node-fields/],
    ["extra field", { op: "add", a: { op: "const", value: 1 }, b: { op: "const", value: 2 }, x: 1 }, /program-node-fields/],
    ["non-string name", { op: "input", name: 7 }, /program-node-fields|program-name-not-a-string/],
    ["bad child", { op: "add", a: { op: "const", value: 1 }, b: { op: "nope" } }, /program-unknown-op/],
    ["non-canonical const", { op: "const", value: new Map() }, /program-const-not-canonical/],
  ];
  const got = malformed.map(([l, ast, rx]) => {
    const v = validateProgram(ast);
    let threw = "ISSUED AN ID";
    try { programSemId(ast); } catch (e) { threw = e.message; }
    return [l, !v.ok && rx.test(v.reason) && rx.test(threw)];
  });
  R("grammar-refuses-before-id", got.every((x) => x[1]),
    got.map(([l, ok]) => `${l}:${ok ? "refused" : "ADMITTED"}`).join(" ") +
    ` — v0.2.0 issued a program_sem_id to {op:"exec", cmd:"rm -rf /"}, which failed only later at ` +
    `evaluation, having already been given a semantic identity`);
  // arithmetic is typed and total: no coercion, no non-finite result
  const A = { op: "add", a: { op: "input", name: "x" }, b: { op: "input", name: "y" } };
  const ev = (i) => { try { return "=" + JSON.stringify(evaluate(A, { exact: {}, predicates: {} }, i).value); }
    catch (e) { return e.message; } };
  R("arithmetic-typed-and-total",
    ev({ x: 2, y: 3 }) === "=5" && /program-type: add of non-number/.test(ev({ x: "2", y: "3" }))
      && /program-type: add of non-number/.test(ev({ x: [], y: {} }))
      && /program-arith-non-finite: add/.test(ev({ x: 1e308, y: 1e308 })),
    `2+3 ${ev({ x: 2, y: 3 })} · "2"+"3" ${ev({ x: "2", y: "3" })} · []+{} ${ev({ x: [], y: {} })} · ` +
    `1e308+1e308 ${ev({ x: 1e308, y: 1e308 })}. v0.2.0's add was JavaScript's + and produced "23" and ` +
    `"[object Object]" under the same program_sem_id`);
}


// ── 11. the footprint is a SET; the trace keeps order ────────────────────
{
  // b is visited first and twice; a once. Three accesses, two dependencies.
  const RD = { op: "add", a: { op: "read", resource: "b" },
    b: { op: "add", a: { op: "read", resource: "a" }, b: { op: "read", resource: "b" } } };
  const g = { exact: { a: { value: 1, version: 1 }, b: { value: 2, version: 1 } }, predicates: {} };
  const out = evaluate(RD, g, {});
  R("footprint-is-a-canonical-set",
    canonicalBytes(out.read_footprint.exact) === canonicalBytes([["a", 1], ["b", 1]])
      && canonicalBytes(out.read_trace.exact) === canonicalBytes([["b", 1], ["a", 1], ["b", 1]])
      && out.witness.reads === 2,
    `three accesses in order ${JSON.stringify(out.read_trace.exact)} produce the dependency set ` +
    `${JSON.stringify(out.read_footprint.exact)}. Depending on {a,b} is ONE dependency set however it ` +
    `was visited — declaring the order semantic would make two correct implementations diverge over a ` +
    `field neither of them considers semantic`);
  R("trace-is-outside-the-semantic-projection",
    !SEMANTIC_RESULT_FIELDS.includes("execution_evidence")
      && SEMANTIC_RESULT_FIELDS.includes("semantic_result")
      && canonicalBytes(EXECUTION_ENVELOPE_FIELDS) === canonicalBytes(["implementation_id", "read_trace"]),
    `semantic projection = [${SEMANTIC_RESULT_FIELDS.join(", ")}]; execution evidence = ` +
    `[${EXECUTION_ENVELOPE_FIELDS.join(", ")}]. Excluded from the comparison and NOT excluded from ` +
    `checking — non-semantic does not mean unverified, which is what v0.5.0 got wrong`);
  // a result carrying a sequence where the set is required is REFUSED, not normalized
  const req = mkReq();
  const honest = deriveLocally(reg, req).result;
  const resequenced = withSem(honest, { read_footprint: { exact: [["fb", 1], ["fb", 1]], predicates: [] } });
  const c = checkResult(resequenced, req);
  R("footprint-set-is-checked-not-normalized",
    !c.ok && c.reason === "result-footprint-not-canonical-set: exact",
    `${c.reason} — normalizing on receipt would let two implementations commit to different bytes and ` +
    `still be told they agreed`);
}

// ── 12. the arithmetic edge matrix, all three operators ──────────────────
{
  const g = { exact: {}, predicates: {} };
  const bin = (op) => ({ op, a: { op: "input", name: "x" }, b: { op: "input", name: "y" } });
  const run = (op, i) => { try { return "=" + JSON.stringify(evaluate(bin(op), g, i).value); }
    catch (e) { return e.message; } };
  const overflow = [["add", { x: 1e308, y: 1e308 }], ["sub", { x: -1e308, y: 1e308 }], ["mul", { x: 1e308, y: 2 }]];
  const typed = [["add", { x: "2", y: "3" }], ["sub", { x: [], y: 1 }], ["mul", { x: 1, y: {} }]];
  R("overflow-refused-on-every-operator",
    overflow.every(([op, i]) => run(op, i) === "program-arith-non-finite: " + op),
    overflow.map(([op, i]) => `${op}:${run(op, i)}`).join(" · ") +
    ` — one refusal string, three separately frozen semantic surfaces, each witnessed`);
  R("coercion-refused-on-every-operator",
    typed.every(([op, i]) => run(op, i) === "program-type: " + op + " of non-number"),
    typed.map(([op, i]) => `${op}:${run(op, i)}`).join(" · "));
  // signed zero: the canonical quotient identifies -0 with +0, and says so
  const negZero = evaluate(bin("mul"), g, { x: -1, y: 0 }).value;
  R("signed-zero-identified", Object.is(negZero, -0) && canonicalBytes(negZero) === "0"
      && canonicalBytes(-0) === canonicalBytes(0) && /IDENTIFIES -0 with \+0/.test(CORE_SPEC.signed_zero),
    `mul(-1, 0) evaluates to ${Object.is(negZero, -0) ? "-0" : "+0"} and canonicalizes to ` +
    `${canonicalBytes(negZero)} — the canonical numeric quotient identifies them, which was already ` +
    `true of the domain and unstated. A C implementation would otherwise have decided it by accident`);
}


// ── 13. freshness is a DIFFERENT question from containment ──────────────
{
  const live = { res: { fb: { value: 5, version: 1 }, other: { value: 0, version: 1 } },
    read(r) { return { ...this.res[r] }; }, scope(q) { return "scope:" + q; } };
  const auth = new DerivationAuthority(live);
  const { request: req } = auth.authorize({ intent_id: "f1", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const res = deriveLocally(reg, req).result;
  const before = auth.accept(reg, req, res);
  live.res.fb = { value: 9, version: 2 };                 // the World moves
  const containment = footprintWithinGrant(res.semantic_result.read_footprint, req.read_grants);
  const rederive = validateForeignResult(reg, req, res);
  const after = auth.accept(reg, req, res);
  R("freshness-is-not-containment",
    before.ok && containment.ok && rederive.ok
      && !after.ok && after.reason === "stale-read: fb granted@1 live@2",
    `after fb moves 1→2: footprintWithinGrant ${containment.ok ? "PASS" : containment.reason}, ` +
    `re-derivation ${rederive.ok ? "PASS" : rederive.reason} — both CORRECT about the snapshot — and ` +
    `acceptance ${after.reason}. Containment is historical, freshness is temporal, and a protocol that ` +
    `stops at re-derivation commits a value the World has already contradicted`);
  live.res.fb = { value: 5, version: 1 };
  live.res.other = { value: 999, version: 2 };            // a write nothing read
  const unrelated = auth.accept(reg, req, res);
  R("unrelated-write-does-not-invalidate", unrelated.ok && unrelated.fresh_at_check === true,
    `other@1→2 moved and acceptance still passes — freshness keys on the FOOTPRINT, never on a global ` +
    `vclock. A vclock rule would invalidate every derivation on every unrelated write, undoing the ` +
    `grant/footprint separation from the other side`);
  R("acceptance-does-not-claim-committable",
    unrelated.committable === undefined && unrelated.validated === true && unrelated.fresh_at_check === true,
    `accept() returns {validated, fresh_at_check} and NOT committable. One call cannot make a result ` +
    `committable: the World can move between this returning and the caller applying. The composition ` +
    `that commits belongs to the World — lock, accept, prepared apply, receipt, unlock — and no lock ` +
    `capability is exported to reach it`);
}

// ── 14. issuance binds the WHOLE request, and cannot be handed to a caller ─
{
  const live = { res: { fb: { value: 5, version: 1 } }, read(r) { return { ...this.res[r] }; },
    scope(q) { return "scope:" + q; } };
  const auth = new DerivationAuthority(live);
  const intent = { intent_id: "i1", program_sem_id: PID, canonical_inputs: { bias: 0 },
    requested_resources: { exact: ["fb"], predicates: [] } };
  const a = auth.authorize(intent);
  const res = deriveLocally(reg, a.request).result;
  const mine = auth.accept(reg, a.request, res);
  const theirs = new DerivationAuthority(live).accept(reg, a.request, res);
  // the defect: same request_id, same grant_id, different inputs
  const swapped = { ...a.request, canonical_inputs: { bias: 1000 } };
  const swappedRes = deriveLocally(reg, swapped).result;
  const swapAcc = auth.accept(reg, swapped, swappedRes);
  R("issuance-binds-the-whole-request",
    a.ok && mine.ok && !theirs.ok && theirs.reason === "grant-not-issued-by-this-authority"
      && swappedRes.semantic_result.value === 1005 && !swapAcc.ok && swapAcc.reason === "request-not-as-issued",
    `the issuing authority accepts; a different instance refuses (${theirs.reason}); and an input swap ` +
    `under an UNTOUCHED request_id and grant_id — which derives to ${swappedRes.semantic_result.value} — is refused ` +
    `(${swapAcc.reason}). The draft bound request_id → grant_id and answered "was this issued?" about a ` +
    `GRANT while the thing being accepted was a REQUEST`);
  R("request-sem-id-recomputes",
    requestSemId(a.request) === requestSemId(JSON.parse(canonicalBytes(a.request)))
      && requestSemId(a.request) !== requestSemId(swapped),
    `request_sem_id = H(canonical request) recomputes over an owned copy and differs for the swapped ` +
    `request — which is the whole mechanism`);
  const bagged = auth.authorize(intent, { canonical_inputs: { bias: 1000 } });
  const impl = auth.authorize({ ...intent, intent_id: "i2" }, { expected_implementation_id: "impl-c-derive-v0.5.0" });
  R("authorize-options-whitelisted",
    !bagged.ok && bagged.reason === "authorize-options-unknown: [canonical_inputs]"
      && impl.ok && impl.request.expected_implementation_id === "impl-c-derive-v0.5.0",
    `${bagged.reason} — the draft spread \`...over\` after every authority-decided field, so a caller ` +
    `could overwrite canonical_inputs on an authority-ISSUED request. Exactly one field may be requested`);
  let froze = false;
  try { a.request.canonical_inputs.bias = 1000; } catch { froze = true; }
  R("issued-request-is-owned-and-frozen", froze && a.request.canonical_inputs.bias === 0,
    `the issued request is owned through canonicalBytes and deep-frozen; mutating it throws. Defence in ` +
    `depth — the BINDING is what refuses a modified request; this stops accidental modification inside ` +
    `the authority's own process`);
  const badIntents = [
    ["extra field", { ...intent, sneak: 1 }, /intent-schema/],
    ["missing field", { intent_id: "x", program_sem_id: PID }, /intent-schema/],
    ["resources not lists", { ...intent, requested_resources: { exact: "fb", predicates: [] } }, /intent-requested-exact-not-a-string-list/],
    ["capability in inputs", { ...intent, canonical_inputs: { f: () => 1 } }, /not-canonical/],
  ];
  R("intent-schema-closed", badIntents.every(([, i, rx]) => { const c = checkIntent(i); return !c.ok && rx.test(c.reason); }),
    badIntents.map(([l, i]) => `${l}:${checkIntent(i).ok ? "ADMITTED" : "refused"}`).join(" ") +
    ` — the untrusted half of the two-phase protocol is validated as strictly as the authority's half`);
  let noReader = "ACCEPTED";
  try { new DerivationAuthority({}); } catch (e) { noReader = e.message; }
  R("authority-requires-a-world", noReader === "authority-requires-a-world-reader",
    `${noReader} — an authority without a World cannot answer the temporal question, and one that ` +
    `silently could not would report fresh by never looking`);
}

console.log("═".repeat(96));
console.log(fail
  ? `DERIVE-BATTERY: FAIL — ${rows.filter((r) => !r.ok).length}/${rows.length}`
  : `DERIVE-BATTERY: PASS — ${rows.length}/${rows.length}. The program is data and its id commits the ` +
    `frozen core's semantics, not just its syntax; the grant is what the authority made available and ` +
    `the footprint is what the program consumed — a canonical dependency SET whose access order is a ` +
    `separate trace, outside semantics; the executor asserts its own identity; containment is ` +
    `historical and freshness is temporal; and issuance binds the whole request to the authority that ` +
    `cut it, which no caller can supply on its behalf.`);
process.exit(fail ? 1 : 0);
