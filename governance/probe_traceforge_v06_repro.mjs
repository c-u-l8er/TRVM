/* ═══════════════════════════════════════════════════════════════════════════
   probe_traceforge_v06_repro.mjs — "outside the semantic projection" had
   quietly become "unchecked".

   Round 16 ruled that access ORDER is execution strategy and must not be
   semantic identity: depending on {a,b} is one dependency set however it was
   visited. That ruling was right and remains. What it did not say — and what
   v0.5.0 therefore did not do — is that a field excluded from the comparison
   still needs a rule of its own.

   T-1  A FORGED TRACE VALIDATED AND WAS ACCEPTED. A program reading `a` then
        `b` honestly traces [["a",1],["b",1]]. Reverse ONLY the trace, leave the
        canonical footprint and the value untouched, and against v0.5.0:

            validateForeignResult  -> { ok: true }
            authority.accept       -> { ok: true, validated: true,
                                        fresh_at_check: true }

        checkResult compared the footprint to the SET of the trace — which a
        reversal does not change — and validateForeignResult compared only the
        semantic projection, from which the trace was excluded. So the one field
        carrying execution evidence was the one field nothing looked at.

   WHY THE FLAT SHAPE WAS PART OF THE DEFECT. read_trace sat as a sibling of
   value, support and read_footprint. A field inside DeriveResult reads as
   authenticated by the same machinery as its neighbours, and this one was not.
   v0.6.0 makes the envelopes explicit — `semantic_result` and
   `execution_evidence` — so that the trust status of each is visible in the
   shape rather than only in a comment.

   AND THE RULE ITSELF: the core PROMISES deterministic left-to-right
   evaluation, so a trace disagreeing with an honest re-derivation is a
   CONFORMANCE failure of the implementation, not a disagreement about the
   program. It is refused, and the two verdicts are reported separately —
   `semantic_agreement: true, trace_conforms: false` — because "same meaning,
   different strategy" and "wrong answer" are different diagnoses and v0.5.0
   could make neither.

   NON-SEMANTIC DOES NOT MEAN UNVERIFIED.

   PAIRED, and it gates.
   ═══════════════════════════════════════════════════════════════════════════ */
import {
  ProgramRegistry, DerivationAuthority, deriveLocally, validateForeignResult,
  canonicalBytes, SEMANTIC_RESULT_FIELDS, EXECUTION_ENVELOPE_FIELDS, validateTraceConformance,
} from "./derive_protocol.mjs";

const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "CONFINED" : "BREACH  "}  ${id.padEnd(22)} ${note}`); };

const P = { op: "add", a: { op: "read", resource: "a" }, b: { op: "read", resource: "b" } };
const mkWorld = () => ({ res: { a: { value: 1, version: 1 }, b: { value: 2, version: 1 } },
  read(r) { return { ...this.res[r] }; }, scope(q) { return "scope:" + q; } });
const reg = new ProgramRegistry(); const PID = reg.bind(P);
const intent = { intent_id: "t-1", program_sem_id: PID, canonical_inputs: {},
  requested_resources: { exact: ["a", "b"], predicates: [] } };

/* ── v0.5.0's validation of a result, VERBATIM in its essentials ──────────
   The flat result shape, the footprint-is-the-set-of-the-trace check, and a
   semantic projection that excluded implementation_id and read_trace — after
   which nothing else looked at the trace. Do not repair anything here. */
const V5_SEMANTIC = ["request_id", "program_sem_id", "grant_id", "value", "witness", "support", "read_footprint"];
const v5Flatten = (res) => ({
  request_id: res.request_id, program_sem_id: res.program_sem_id, grant_id: res.grant_id,
  implementation_id: res.execution_evidence.implementation_id,
  value: res.semantic_result.value, witness: res.semantic_result.witness,
  support: res.semantic_result.support, read_footprint: res.semantic_result.read_footprint,
  read_trace: res.execution_evidence.read_trace,
});
function v5Validate(registry, req, res) {
  // schema-ish: the footprint must be the canonical SET of the trace
  for (const kind of ["exact", "predicates"]) {
    const seen = new Map();
    for (const pr of res.read_trace[kind]) seen.set(canonicalBytes(pr), pr);
    const want = [...seen.values()].sort((x, y) => canonicalBytes(x) < canonicalBytes(y) ? -1 : 1);
    if (canonicalBytes(res.read_footprint[kind]) !== canonicalBytes(want))
      return { ok: false, reason: "result-footprint-not-canonical-set: " + kind };
  }
  const mine = v5Flatten(deriveLocally(registry, req).result);
  const proj = (r) => { const o = {}; for (const f of V5_SEMANTIC) o[f] = r[f]; return o; };
  return canonicalBytes(proj(mine)) === canonicalBytes(proj(res))
    ? { ok: true } : { ok: false, reason: "foreign-result-divergence" };
}

/* ── T-1 against the frozen v0.5.0 validation ─────────────────────────────── */
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request: req } = auth.authorize(intent);
  const honest = v5Flatten(deriveLocally(reg, req).result);
  const forged = { ...honest, read_trace: { exact: [...honest.read_trace.exact].reverse(), predicates: [] } };
  const v = v5Validate(reg, req, forged);
  R("T-1 frozen-v0.5.0", !v.ok,
    `honest trace ${JSON.stringify(honest.read_trace.exact)} reversed to ` +
    `${JSON.stringify(forged.read_trace.exact)} with the footprint ` +
    `${JSON.stringify(forged.read_footprint.exact)} and the value ${forged.value} untouched: ` +
    `validateForeignResult -> ok=${v.ok}. The footprint check compares the SET, which a reversal does ` +
    `not change, and the semantic projection excluded the trace — so nothing looked at it`);
}

/* ── the same forgery against live ────────────────────────────────────────── */
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request: req } = auth.authorize(intent);
  const honest = deriveLocally(reg, req).result;
  const forged = { ...honest, execution_evidence: { ...honest.execution_evidence,
    read_trace: { exact: [...honest.execution_evidence.read_trace.exact].reverse(), predicates: [] } } };
  const v = validateForeignResult(reg, req, forged);
  const acc = auth.accept(reg, req, forged);
  R("T-1 live", !v.ok && v.reason === "trace-nonconforming: exact"
      && v.semantic_agreement === true && v.trace_conforms === false
      && !acc.ok && acc.reason === "trace-nonconforming: exact",
    `${v.reason} — and the two verdicts are reported SEPARATELY: semantic_agreement ` +
    `${v.semantic_agreement}, trace_conforms ${v.trace_conforms}. "Same meaning, different strategy" ` +
    `and "wrong answer" are different diagnoses, and v0.5.0 could make neither`);
}

/* ── the honest result still passes, and reports both verdicts ────────────── */
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request: req } = auth.authorize(intent);
  const honest = deriveLocally(reg, req).result;
  const acc = auth.accept(reg, req, honest);
  R("honest-still-accepted", acc.ok && acc.trace_conforms === true && acc.validated === true
      && acc.committable === undefined,
    `an honest result is accepted with validated ${acc.validated}, trace_conforms ${acc.trace_conforms} ` +
    `and still NO committable — the new check refuses a forgery without inventing a stronger claim ` +
    `about the honest case`);
}

/* ── and the shape now says which fields carry which trust status ─────────── */
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request: req } = auth.authorize(intent);
  const honest = deriveLocally(reg, req).result;
  R("envelopes-are-explicit",
    canonicalBytes(Object.keys(honest).sort()) ===
      canonicalBytes(["execution_evidence", "grant_id", "program_sem_id", "request_id", "semantic_result"])
      && canonicalBytes(EXECUTION_ENVELOPE_FIELDS) === canonicalBytes(["implementation_id", "read_trace"])
      && !SEMANTIC_RESULT_FIELDS.includes("execution_evidence"),
    `the result is {${Object.keys(honest).sort().join(", ")}} and the semantic projection is ` +
    `[${SEMANTIC_RESULT_FIELDS.join(", ")}]. At v0.5.0 read_trace was a SIBLING of value and ` +
    `read_footprint, which reads as authenticated by the same machinery as its neighbours — and was not`);
  // the conformance rule is a real function with its own verdict, not a comment
  const t = validateTraceConformance({ exact: [["a", 1]], predicates: [] }, { exact: [["b", 1]], predicates: [] });
  R("trace-rule-is-executable", !t.ok && t.reason === "trace-nonconforming: exact",
    `validateTraceConformance is exported and refuses by name (${t.reason}) — the core FIXES evaluation ` +
    `order so refusals and traces reproduce, so a disagreeing trace is a conformance failure of the ` +
    `implementation rather than a disagreement about the program`);
}

console.log("=".repeat(100));
const frozenHeld = results.filter((r) => r.id.includes("frozen") && r.held);
const liveBreached = results.filter((r) => !r.id.includes("frozen") && !r.held);
console.log(
  `TRACE-FORGE v0.6 REPRO: ${results.filter((r) => r.id.includes("frozen") && !r.held).length}/1 reproduce ` +
  `against the frozen v0.5.0 · ${results.filter((r) => !r.id.includes("frozen") && r.held).length}/4 confined against live` +
  (frozenHeld.length ? ` — VACUOUS: ${frozenHeld.map((r) => r.id).join(", ")}` : "") +
  (liveBreached.length ? ` — REGRESSION: ${liveBreached.map((r) => r.id).join(", ")}` : ""));
process.exit(frozenHeld.length + liveBreached.length ? 1 : 0);
