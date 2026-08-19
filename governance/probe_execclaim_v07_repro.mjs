/* ═══════════════════════════════════════════════════════════════════════════
   probe_execclaim_v07_repro.mjs — the law said impersonation was closed, and
   JavaScript could impersonate C all the way through acceptance.

   `law:derivation.implementation-provenance@1` said: "A caller therefore cannot
   cause a result to claim an implementation that did not produce it … this
   closes IMPERSONATION and does not yet establish PROVENANCE." The first half
   was false, and rounds 15 through 21 all shipped with it on the record.

   P-1  THE CALLER CHOSE THE LABEL AND THE AUTHORITY AGREED WITH ITSELF.
        `deriveLocally(registry, req, implementationId)` took the implementation
        identity as a PARAMETER, defaulted to JS. So:

            authorize(intent, {expected_implementation_id: "impl-c-derive-…"})
            deriveLocally(reg, req, "impl-c-derive-…")   ← the JS evaluator runs
            authority.accept(reg, req, res)

              → { ok: true, validated: true, fresh_at_check: true,
                  trace_conforms: true,
                  implementation_id: "impl-c-derive-v0.6.0" }

        Every byte of the result was honest JS output. Only the label was C.
        Acceptance compared the caller's EXPECTATION against the caller's own
        LABEL — a claim against a claim — and `trace_conforms: true` made the
        forged provenance read as better-attested than an unforged one.

   WHY A BINARY HASH WOULD NOT HAVE FIXED IT. The record's declared-open item
   was "implementation_id is a constant, not a digest of executable bytes". But
   a digest carried INSIDE the same untrusted result is still self-asserted: the
   forger simply writes the digest too. The missing object was never the hash.
   It is INDEPENDENT OBSERVATION OF WHICH EXECUTOR ACTUALLY RAN.

   So round 19's envelope idea was one distinction short:

       semantic_result        portable meaning
       execution_claim        what the result SAYS happened   ← this is what
                              `execution_evidence` actually is
       execution_observation  what the host INDEPENDENTLY observed

   A conforming trace does not prove C executed anything, and neither does a
   string. The host knows which worker it spawned; that is the only thing here
   that is not a claim. `registerExecutor` records it, `accept` compares against
   it, and where no observation exists the honest answer is
   `implementation-provenance-unavailable` rather than "C verified".

   PAIRED, and it gates.
   ═══════════════════════════════════════════════════════════════════════════ */
import {
  ProgramRegistry, DerivationAuthority, deriveLocally, validateForeignResult,
  JS_IMPLEMENTATION_ID,
} from "./derive_protocol.mjs";

const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "CONFINED" : "BREACH  "}  ${id.padEnd(26)} ${note}`); };

const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const mkWorld = () => ({ res: { fb: { value: 5, version: 1 } },
  read(r) { return { ...this.res[r] }; }, scope(q) { return "scope:" + q; } });
const reg = new ProgramRegistry(); const PID = reg.bind(P);
const C_ID = "impl-c-derive-v0.7.0";

/* ── v0.6.0's derivation and acceptance, VERBATIM in their essentials ─────
   deriveLocally took the identity as a parameter; accept compared the request's
   expectation against the result's own claim. Do not repair anything here. */
function v6Derive(registry, req, implementationId) {
  const honest = deriveLocally(registry, { ...req, expected_implementation_id: undefined,
    ...(("expected_implementation_id" in req) ? {} : {}) });
  // v0.6.0 simply stamped whatever the caller asked for
  const base = honest.ok ? honest.result : deriveLocally(registry,
    (({ expected_implementation_id, ...r }) => r)(req)).result;
  return { ...base, request_id: req.request_id,
    execution_evidence: { ...base.execution_evidence, implementation_id: implementationId } };
}
function v6Accept(registry, req, res) {
  const v = validateForeignResult(registry, req, res);
  if (!v.ok) return v;
  const claimed = res.execution_evidence.implementation_id;
  if ("expected_implementation_id" in req && claimed !== req.expected_implementation_id)
    return { ok: false, reason: "implementation-mismatch" };
  return { ok: true, validated: true, fresh_at_check: true, trace_conforms: true,
    implementation_id: claimed };
}

/* ── P-1 against the frozen v0.6.0 acceptance ─────────────────────────────── */
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request: req } = auth.authorize({ intent_id: "p1", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } },
    { expected_implementation_id: C_ID });
  const res = v6Derive(reg, req, C_ID);
  const acc = v6Accept(reg, req, res);
  R("P-1 frozen-v0.6.0", !(acc.ok && acc.implementation_id === C_ID),
    `the JS evaluator produced every byte and the caller chose the label ${C_ID}: accept -> ok=${acc.ok}, ` +
    `implementation_id ${acc.implementation_id}, trace_conforms ${acc.trace_conforms}. The expectation was ` +
    `compared against the result's own claim — a claim against a claim — and the conforming trace made ` +
    `the forgery read as better attested than an unforged result`);
}

/* ── live: the caller cannot select an identity at all ────────────────────── */
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request: req } = auth.authorize({ intent_id: "p2", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } },
    { expected_implementation_id: C_ID });
  const d = deriveLocally(reg, req, C_ID);          // third argument no longer exists
  R("P-1 live: no caller label", !d.ok && /implementation-mismatch: want .*, this is impl-js/.test(d.reason),
    `${d.reason} — deriveLocally takes no implementation parameter; the JS evaluator answers a C ` +
    `requirement by refusing it, because an implementation's identity comes from the implementation`);
}

/* ── live: provenance is compared against OBSERVATION ─────────────────────── */
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const mk = (opts, id) => auth.authorize({ intent_id: id, program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } }, opts).request;
  const jsHandle = auth.registerExecutor(JS_IMPLEMENTATION_ID);

  const honestReq = mk({}, "h1");
  const honest = deriveLocally(reg, honestReq).result;
  const observed = auth.accept(reg, honestReq, honest, jsHandle);
  const unobserved = auth.accept(reg, honestReq, honest);
  R("provenance-needs-observation",
    observed.ok && observed.implementation_provenance === "observed"
      && observed.implementation_id === JS_IMPLEMENTATION_ID
      && unobserved.ok && unobserved.implementation_provenance === "unavailable"
      && unobserved.implementation_id === undefined,
    `with the host's observation: provenance ${observed.implementation_provenance}, id ` +
    `${observed.implementation_id}. Without it: provenance ${unobserved.implementation_provenance} and ` +
    `NO implementation_id at all — the honest answer, rather than repeating the result's claim back`);

  const forged = { ...honest, execution_evidence: { ...honest.execution_evidence, implementation_id: C_ID } };
  const contradicted = auth.accept(reg, honestReq, forged, jsHandle);
  R("claim-vs-observation", !contradicted.ok
      && contradicted.reason === "implementation-claim-contradicts-observation: claims " + C_ID +
         ", observed " + JS_IMPLEMENTATION_ID,
    `${contradicted.reason} — the result's claim is checked AGAINST the observation instead of standing ` +
    `in for it`);

  const cReq = mk({ expected_implementation_id: C_ID }, "h2");
  const noObs = auth.accept(reg, cReq, { ...honest, request_id: cReq.request_id }, null);
  const wrongObs = auth.accept(reg, cReq, { ...honest, request_id: cReq.request_id }, jsHandle);
  R("unavailable-is-not-verified",
    !noObs.ok && noObs.reason === "implementation-provenance-unavailable"
      && !wrongObs.ok && /implementation-mismatch: want .*, observed impl-js/.test(wrongObs.reason),
    `a C requirement with no observation -> ${noObs.reason}; with a JS executor observed -> ` +
    `${wrongObs.reason}. "Unavailable" is the honest answer where v0.6.0 said "C verified"`);

  let forgedHandle = "ACCEPTED";
  const acc = auth.accept(reg, honestReq, honest, { token: Symbol("impl-c-derive-v0.7.0") });
  if (!acc.ok) forgedHandle = acc.reason;
  R("handles-are-authority-issued", forgedHandle === "executor-not-registered-with-this-authority",
    `${forgedHandle} — the handle holds a private Symbol this authority created, so a caller cannot ` +
    `fabricate one or name an executor the host never launched`);
}

/* ── and the success shape no longer invites weighing booleans ────────────── */
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request: req } = auth.authorize({ intent_id: "s1", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const res = deriveLocally(reg, req).result;
  const h = auth.registerExecutor(JS_IMPLEMENTATION_ID);
  const acc = auth.accept(reg, req, res, h);
  const v = validateForeignResult(reg, req, res);
  R("success-shape-is-narrow",
    acc.trace_conforms === undefined && acc.committable === undefined
      && acc.fresh_at_check === true && v.trace_conforms === true && v.semantic_agreement === true,
    `accept success = {${Object.keys(acc).join(", ")}} — trace_conforms is gone from it, because on ` +
    `success it is redundant and a boolean per check invites a reader to weigh them. It stays in the ` +
    `validator (${v.semantic_agreement}/${v.trace_conforms}) and in the failure diagnostics, where ` +
    `semantic_agreement:true + trace_conforms:false is the distinction worth having. fresh_at_check ` +
    `stays because its temporal limit is meaningful`);
}

console.log("=".repeat(100));
const frozenHeld = results.filter((r) => r.id.includes("frozen") && r.held);
const liveBreached = results.filter((r) => !r.id.includes("frozen") && !r.held);
console.log(
  `EXEC-CLAIM v0.7 REPRO: ${results.filter((r) => r.id.includes("frozen") && !r.held).length}/1 reproduce ` +
  `against the frozen v0.6.0 · ${results.filter((r) => !r.id.includes("frozen") && r.held).length}/6 confined against live` +
  (frozenHeld.length ? ` — VACUOUS: ${frozenHeld.map((r) => r.id).join(", ")}` : "") +
  (liveBreached.length ? ` — REGRESSION: ${liveBreached.map((r) => r.id).join(", ")}` : ""));
process.exit(frozenHeld.length + liveBreached.length ? 1 : 0);
