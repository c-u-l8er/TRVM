/* ═══════════════════════════════════════════════════════════════════════════
   probe_execreg_v08_repro.mjs — the architecture said "the host observes what
   it launched", and registration launched nothing.

   Round 22 diagnosed P-1 correctly: an execution CLAIM is not provenance, and
   the only thing in the loop that is not a claim is what the host observed it
   launch. Then it shipped a mechanism that observed nothing.

   P-2  REGISTRATION IS AN ASSERTION WEARING AN OBSERVATION'S CLOTHES.
        `DerivationAuthority.registerExecutor(implementation_id)` took a string,
        put it in a private Map, and returned a handle carrying a private
        Symbol. No process was started. No request was sent. No bytes were read.

            actual executor: impl-js-derive-v0.7.0

            auth.registerExecutor("impl-c-derive-v0.7.0")
                ← no C executable launched, or present, anywhere

            the JS evaluator produces the result
            the result is relabelled as C
            authority.accept(req, res, thatHandle)

              → { ok: true, validated: true, fresh_at_check: true,
                  implementation_provenance: "observed",
                  implementation_id: "impl-c-derive-v0.7.0" }

        The Symbol proved exactly one thing: THIS AUTHORITY MINTED THIS HANDLE.
        It did not prove THIS AUTHORITY OBSERVED THIS IMPLEMENTATION EXECUTE
        THIS REQUEST AND PRODUCE THIS RESULT — and only the second sentence is
        provenance. So the P-1 attack did not close; it MOVED:

            v0.6   the caller chooses the identity at deriveLocally()
            v0.7   the caller chooses the identity at registerExecutor()

   P-2b THE ROUND-17 SHAPE CAME BACK ONE LEVEL UP. Round 17's lesson was that
        acceptance must take no proofs from its caller: issuance and the live
        reader became closed-over authority state rather than arguments. Then
        v0.7.0 wrote `accept(registry, req, res, executor = null)` and the
        executor handle was a proof supplied at acceptance time. Even if
        registration had really launched C, a valid C handle could still have
        been paired with a result produced elsewhere.

            EXECUTOR EXISTENCE IS NOT EXECUTION PROVENANCE.
            An observation must bind the executor, the request and the returned
            bytes as ONE EVENT.

        which is the same symmetry, one layer higher:

            request provenance    don't authenticate the grant;
                                  authenticate the WHOLE REQUEST.
            execution provenance  don't authenticate the executor handle;
                                  authenticate the WHOLE EXECUTION EVENT.

   PAIRED, and it gates. The frozen half must keep breaching and the live half
   must keep holding, so a future edit that repairs the frozen copy instead of
   the live one fails here rather than passing quietly.
   ═══════════════════════════════════════════════════════════════════════════ */
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  ProgramRegistry, DerivationAuthority, deriveLocally, validateForeignResult,
  JS_IMPLEMENTATION_ID, requestSemId,
} from "./derive_protocol.mjs";
import { ObservedExecutionHost, digestArtifactFiles } from "./observed_execution_host.mjs";
import { JS_WORKER_ENTRY, defaultDeriveCatalog } from "./derive_launcher.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const JS_DIGEST = digestArtifactFiles(JS_WORKER_ENTRY.artifact_closure);
const CATALOG = defaultDeriveCatalog(JS_IMPLEMENTATION_ID);

const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "CONFINED" : "BREACH  "}  ${id.padEnd(28)} ${note}`); };

const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const mkWorld = () => ({ res: { fb: { value: 5, version: 1 } },
  read(r) { return { ...this.res[r] }; }, scope(q) { return "scope:" + q; } });
const reg = new ProgramRegistry(); const PID = reg.bind(P);
const C_ID = "impl-c-derive-v0.7.0";

/* ── v0.7.0's registration and acceptance, VERBATIM in their essentials ────
   A FROZEN COPY. It is wrong on purpose and must stay wrong: the value of this
   file is that the breach keeps reproducing. Do not repair anything below. */
class V7Authority {
  #executors = new Map();
  registerExecutor(implementation_id) {
    if (typeof implementation_id !== "string" || !implementation_id.startsWith("impl-"))
      throw new Error("executor-implementation-id-malformed");
    const token = Symbol(implementation_id);           // …and that is the whole
    this.#executors.set(token, implementation_id);     // of "the host observes
    return Object.freeze({ token });                   //  what it launched"
  }
  accept(registry, req, res, executor = null) {
    const v = validateForeignResult(registry, req, res);
    if (!v.ok) return v;
    let observed;
    if (executor !== null) {
      observed = this.#executors.get(executor?.token);
      if (observed === undefined) return { ok: false, reason: "executor-not-registered-with-this-authority" };
    }
    if ("expected_implementation_id" in req) {
      if (observed === undefined) return { ok: false, reason: "implementation-provenance-unavailable" };
      if (observed !== req.expected_implementation_id)
        return { ok: false, reason: "implementation-mismatch" };
    }
    if (observed !== undefined && v.implementation_claimed !== observed)
      return { ok: false, reason: "implementation-claim-contradicts-observation" };
    return observed === undefined
      ? { ok: true, validated: true, fresh_at_check: true, implementation_provenance: "unavailable" }
      : { ok: true, validated: true, fresh_at_check: true,
          implementation_provenance: "observed", implementation_id: observed };
  }
}

/* ── P-2 against the frozen v0.7.0: name C, run JS, be told C ─────────────── */
{
  const auth = new DerivationAuthority(mkWorld(), [P]);
  const v7 = new V7Authority();
  const { request: req } = auth.authorize({ intent_id: "p2a", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } },
    { expected_implementation_id: C_ID });

  const cHandle = v7.registerExecutor(C_ID);      // nothing is launched by this line
  // the honest JS run, with the C requirement dropped so the JS evaluator will
  // answer at all — the forgery is applied afterwards, exactly as v0.7.0 allowed
  const { expected_implementation_id: _want, ...bare } = req;
  const jsRes = deriveLocally(reg, bare).result;
  const asIfC = { ...jsRes, request_id: req.request_id,
    execution_evidence: { ...jsRes.execution_evidence, implementation_id: C_ID } };
  const acc = v7.accept(reg, req, asIfC, cHandle);

  R("P-2 frozen-v0.7.0",
    !(acc.ok && acc.implementation_provenance === "observed" && acc.implementation_id === C_ID),
    `registerExecutor("${C_ID}") launched nothing; the JS evaluator produced every byte; the result was ` +
    `relabelled C — and acceptance returned ok=${acc.ok}, implementation_provenance ` +
    `${acc.implementation_provenance}, implementation_id ${acc.implementation_id}. The private Symbol ` +
    `proved only that this authority minted this handle`);
}

/* ── P-2b against the frozen v0.7.0: a real handle, unrelated bytes ───────── */
{
  const auth = new DerivationAuthority(mkWorld(), [P]);
  const v7 = new V7Authority();
  const { request: reqA } = auth.authorize({ intent_id: "p2b-1", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const { request: reqB } = auth.authorize({ intent_id: "p2b-2", program_sem_id: PID,
    canonical_inputs: { bias: 7 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const jsHandle = v7.registerExecutor(JS_IMPLEMENTATION_ID);
  // one handle, and it certifies EVERY result that ever passes through this
  // acceptance — nothing ties it to a request or to a set of bytes
  const resA = deriveLocally(reg, reqA).result;
  const resB = deriveLocally(reg, reqB).result;
  const accA = v7.accept(reg, reqA, resA, jsHandle);
  const accB = v7.accept(reg, reqB, resB, jsHandle);
  R("P-2b frozen-v0.7.0 handle-reuse",
    !(accA.ok && accB.ok && accA.implementation_provenance === "observed"
      && accB.implementation_provenance === "observed"),
    `ONE handle provenances TWO unrelated executions (${accA.implementation_provenance}, ` +
    `${accB.implementation_provenance}). A handle proves an executor EXISTS; it binds nothing to a ` +
    `request and nothing to the bytes that came back, so acceptance took a proof from its caller — ` +
    `the shape round 17 removed from issuance, reappearing one level up`);
}

/* ── live: there is no registration API at all ────────────────────────────── */
{
  const auth = new DerivationAuthority(mkWorld(), [P]);
  R("live: registration deleted",
    typeof auth.registerExecutor === "undefined"
      && !("registerExecutor" in DerivationAuthority.prototype)
      && DerivationAuthority.prototype.accept.length === 2
      && typeof auth.execute === "function",
    `registerExecutor is absent from the instance and the prototype, and accept takes ` +
    `${DerivationAuthority.prototype.accept.length} parameters — the executor argument is gone, so a ` +
    `caller has no slot in which to supply a proof. The replacement is execute(), where the AUTHORITY ` +
    `does the launching`);
}

/* ── live: a NAME is not an executor, and there is nowhere to put one ─────── */
{
  const auth = new DerivationAuthority(mkWorld(), [P], CATALOG);
  const { request: req } = auth.authorize({ intent_id: "l1", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } },
    { expected_implementation_id: "impl-c-derive-v0.9.0" });
  const run = await auth.execute(req);
  R("live: name-without-launch",
    typeof auth.nameArtifact === "undefined"
      && !run.ok && /^executor-not-in-catalog: impl-c-derive-v0\.9\.0/.test(run.reason),
    `there is no nameArtifact() to call: v0.8.0 kept a digest→name setter and v0.9.0 replaced it with a ` +
    `catalog fixed at the host's construction. A C requirement against a catalog holding only JS is ` +
    `${run.reason.split(":")[0]} — refused before anything is launched. The v0.7.0 attack has no ` +
    `surface left to touch`);
}

/* ── live: an observation binds executor, request and bytes as ONE event ──── */
{
  const auth = new DerivationAuthority(mkWorld(), [P], CATALOG);
  const mk = (id, bias) => auth.authorize({ intent_id: id, program_sem_id: PID,
    canonical_inputs: { bias }, requested_resources: { exact: ["fb"], predicates: [] } }).request;
  const reqA = mk("l2-a", 0), reqB = mk("l2-b", 7);
  const runA = await auth.execute(reqA);
  const resB = deriveLocally(reg, reqB).result;      // B is NEVER launched

  const accA = auth.accept(reqA, runA.result);
  const accB = auth.accept(reqB, resB);
  // and A's observation cannot be borrowed for B's bytes: there is nothing to
  // borrow, because the key IS the event
  const borrowed = auth.observationOf(reqB, resB);
  R("live: observation-is-per-event",
    accA.implementation_provenance === "observed" && accB.implementation_provenance === "unavailable"
      && borrowed === null
      && auth.observationOf(reqA, runA.result) !== null,
    `the launched execution is ${accA.implementation_provenance}; a second, unlaunched derivation at the ` +
    `SAME authority is ${accB.implementation_provenance}. Under v0.7.0 one handle covered both. There is ` +
    `no handle to reuse now: the key is H(request_sem_id | canonical(whole result)), so an observation ` +
    `is a fact about one event and cannot be spent on another`);
}

/* ── live: every field of the result is inside the key ────────────────────── */
{
  const auth = new DerivationAuthority(mkWorld(), [P], CATALOG);
  const { request: req } = auth.authorize({ intent_id: "l3", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const run = await auth.execute(req);
  const res = run.result;
  const mutate = (m) => auth.observationOf(req, m);
  const relabelled = { ...res,
    execution_evidence: { ...res.execution_evidence, implementation_id: "impl-c-derive-v0.8.0" } };
  const revalued = { ...res, semantic_result: { ...res.semantic_result, value: 6 } };
  const retraced = { ...res,
    execution_evidence: { ...res.execution_evidence, read_trace: { exact: [], predicates: [] } } };
  R("live: whole-result-is-the-key",
    mutate(res) !== null && mutate(relabelled) === null && mutate(revalued) === null
      && mutate(retraced) === null,
    `the observed result is found; the same result with its implementation_id changed, or its value ` +
    `changed, or its read_trace emptied, is not — three different fields, one mechanism. The key is over ` +
    `canonical(res) rather than over a projection of it, so there is no field a forger may edit and stay ` +
    `inside the observation`);
}

/* ── live: there is no launcher at all, so it cannot name anything ────────── */
{
  const auth = new DerivationAuthority(mkWorld(), [P], CATALOG);
  const { request: req } = auth.authorize({ intent_id: "l4", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  // the v0.8.0 API, offered as a third argument. Nothing reads it.
  let ranMine = false;
  const liar = { artifact_files: [join(HERE, "derive_protocol.mjs")],
    spawn: () => { ranMine = true; return { send: () => ({ ok: true, result: null }), close() {} }; } };
  const x = await auth.execute(req, liar);
  const entry = Object.keys(JS_WORKER_ENTRY).sort().join(",");
  R("live: launcher-has-no-identity-field",
    x.ok && !ranMine && DerivationAuthority.prototype.execute.length === 1 && entry === "artifact_closure,entrypoint,kind",
    `execute takes ${DerivationAuthority.prototype.execute.length} parameter and a launcher-shaped ` +
    `second one is inert (the callback ran: ${ranMine}). What replaced it is a catalog ENTRY — ` +
    `{${entry}} — inert data whose transport the host owns. v0.7.0's caller supplied the identity as a ` +
    `string; v0.8.0's supplied an action beside the evidence (P-3); v0.9.0 supplies neither`);
}

console.log("=".repeat(100));
// Counted, never typed.
const frozen = results.filter((r) => r.id.includes("frozen"));
const live = results.filter((r) => r.id.startsWith("live:"));
const frozenHeld = frozen.filter((r) => r.held);
const liveBreached = live.filter((r) => !r.held);
console.log(
  `EXEC-REG v0.8 REPRO: ${frozen.length - frozenHeld.length}/${frozen.length} reproduce against the ` +
  `frozen v0.7.0 · ${live.length - liveBreached.length}/${live.length} confined against live` +
  (frozenHeld.length ? ` — VACUOUS: ${frozenHeld.map((r) => r.id).join(", ")}` : "") +
  (liveBreached.length ? ` — REGRESSION: ${liveBreached.map((r) => r.id).join(", ")}` : ""));
process.exit(frozenHeld.length + liveBreached.length ? 1 : 0);
