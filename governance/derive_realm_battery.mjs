/* derive_realm_battery.mjs — the crossing itself, v0.9.0.
   The claim under test is narrow and stated as such: OBJECT authority does not
   cross, the derivation realm reads only what it was granted, and — from v0.8.0
   — an implementation identity is an EXECUTION EVENT THE AUTHORITY DROVE rather
   than a handle anyone can be given. Determinism and host confinement are
   separate scopes and this battery does not touch them.
   Run: node derive_realm_battery.mjs */
import { Worker } from "node:worker_threads";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  ProgramRegistry, programSemId, canonicalBytes, validateForeignResult,
  resolveGrants, grantId, semanticProjection, JS_IMPLEMENTATION_ID,
  DerivationAuthority, requestSemId, deriveLocally,
} from "./derive_protocol.mjs";
import { ObservedExecutionHost, digestArtifactFiles } from "./observed_execution_host.mjs";
import { JS_WORKER_ENTRY, defaultDeriveCatalog } from "./derive_launcher.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const reg = new ProgramRegistry(); const PID = reg.bind(P);
let fail = false, ran = 0;
const R = (id, ok, note) => { ran++; if (!ok) fail = true; console.log(`${ok ? "PASS" : "FAIL"}  ${id.padEnd(32)} ${note}`); };

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
R("crossing-derives", honest.ok && honest.result.semantic_result.value === 5
    && honest.result.execution_evidence.implementation_id === JS_IMPLEMENTATION_ID && honest.result.grant_id === grant_id,
  `worker returned value ${honest.ok && honest.result.semantic_result.value} for fb=5 bias=0, resolving the program from ` +
  `its OWN registry by id and stamping the result ${honest.ok && honest.result.execution_evidence.implementation_id} against ` +
  `grant ${grant_id.slice(0, 18)}…`);

// 3. and the claim is only evidence once the authority re-derives it
{
  const req = mkReq();
  const local = validateForeignResult(reg, req, honest.result);
  const lied = validateForeignResult(reg, req, { ...honest.result,
    semantic_result: { ...honest.result.semantic_result, value: 1005 } });
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
  R("grant-not-reachable-as-input", r.ok && r.result.semantic_result.value === "an ordinary input"
      && r.result.semantic_result.read_footprint.exact.length === 0 && r.result.semantic_result.witness.reads === 0,
    `the worker granted fb and secret:key returns ${JSON.stringify(r.ok && r.result.semantic_result.value)} for ` +
    `{op:"input",name:"__reads"} — at v0.1.0 this returned the whole grant table across the same ` +
    `boundary, with an empty footprint and zero tracked reads`);
  await w2.terminate();
}

// 7. the far side asserts its identity, and refuses a requirement it cannot meet
{
  const r = await ask(mkReq({ expected_implementation_id: "impl-c-pretend-v9" }));
  const ok2 = await ask(mkReq({ expected_implementation_id: JS_IMPLEMENTATION_ID }));
  R("executor-asserts-implementation", !r.ok && /implementation-mismatch: want impl-c-pretend-v9/.test(r.reason)
      && ok2.ok && ok2.result.execution_evidence.implementation_id === JS_IMPLEMENTATION_ID,
    `a request demanding a C executor is refused by the JS worker (${r.reason}); one demanding JS runs ` +
    `and returns its own id. The caller states a requirement; the executor answers it`);
}

// 8. a forged footprint from the far side dies against the snapshot
{
  const req = mkReq();
  const forged = { ...honest.result,
    semantic_result: { ...honest.result.semantic_result,
      witness: { ...honest.result.semantic_result.witness, reads: 2 },
      read_footprint: { exact: [["fb", 1], ["secret:key", 1]], predicates: [] } },
    execution_evidence: { ...honest.result.execution_evidence,
      read_trace: { exact: [["fb", 1], ["secret:key", 1]], predicates: [] } } };
  const v = validateForeignResult(reg, req, forged);
  R("foreign-footprint-refused", !v.ok && v.reason === "footprint-ungranted-read: secret:key",
    `${v.reason} — the authority checks the returned footprint against the grant it issued, on its own ` +
    `evidence. The footprint is the dependency record and the grant is the capability record; the ` +
    `round-14 prose collapsed them and the mechanism supported neither`);
}

// 9. a conforming foreign implementation agrees on MEANING; provenance is not
//    established by relabelling a result, and this case no longer pretends it is
{
  const req = mkReq();
  const asIfC = { ...honest.result,
    execution_evidence: { ...honest.result.execution_evidence, implementation_id: "impl-c-derive-v0.8.0" } };
  const v = validateForeignResult(reg, req, asIfC);
  R("cross-implementation-shape", v.ok && v.implementation_claimed === "impl-c-derive-v0.8.0"
      && v.semantic_agreement === true && v.trace_conforms === true
      && canonicalBytes(semanticProjection(asIfC)) === canonicalBytes(semanticProjection(honest.result)),
    `a result CLAIMING impl-c-derive-v0.8.0 agrees semantically and conforms on its trace, and the ` +
    `validator reports what it CLAIMED (implementation_claimed) rather than certifying it. Until round ` +
    `22 this same case relabelled a JS result and called the outcome provenance — which is exactly the ` +
    `P-1 forgery, sitting in the battery as a passing test`);
}

// 10. intent → authority → realm → acceptance, and the World moving underneath
{
  const live = { res: { fb: { value: 5, version: 1 } }, read(r) { return { ...this.res[r] }; },
    scope(q) { return "scope:" + q; } };
  const auth = new DerivationAuthority(live);
  const a = auth.authorize({ intent_id: "i-realm", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const crossed = await ask(a.request);
  const accepted = auth.accept(reg, a.request, crossed.result);
  live.res.fb = { value: 9, version: 2 };                 // the World moves after the crossing
  const stale = auth.accept(reg, a.request, crossed.result);
  R("intent-to-acceptance", a.ok && crossed.ok && crossed.result.semantic_result.value === 5
      && accepted.ok && accepted.fresh_at_check === true
      && !stale.ok && stale.reason === "stale-read: fb granted@1 live@2",
    `a caller's INTENT is authorized into a request by the authority, crosses to a realm holding no ` +
    `world, returns a claim, and is accepted (fresh_at_check ${accepted.fresh_at_check}) — then the ` +
    `same claim is refused once fb moves 1→2 (${stale.reason}). The worker never learns the World exists`);
  // …and crossing OUTSIDE the authority's own launch yields no provenance at
  // all. This result is honest in every byte and was still not observed.
  R("unlaunched-crossing-unprovenanced",
    accepted.ok && accepted.implementation_provenance === "unavailable"
      && !("implementation_id" in accepted) && auth.observationOf(a.request, crossed.result) === null,
    `the same accepted result reports implementation_provenance ${accepted.implementation_provenance} ` +
    `with NO implementation_id, because this battery — not the authority — spawned the worker. A ` +
    `crossing the authority did not drive is not an execution it observed`);
}

// ── v0.9.0: THE AUTHORITY LAUNCHES, AND CANNOT BE HANDED A LAUNCHER ───────
const mkWorld = () => ({ res: { fb: { value: 5, version: 1 } },
  read(r) { return { ...this.res[r] }; }, scope(q) { return "scope:" + q; } });
const JS_DIGEST = digestArtifactFiles(JS_WORKER_ENTRY.artifact_closure);
const mkAuth = (catalog = defaultDeriveCatalog(JS_IMPLEMENTATION_ID)) =>
  new DerivationAuthority(mkWorld(), new ObservedExecutionHost(catalog));

// 11. an execution the authority drove, and the three identities it separates
let observedRun = null;
{
  const auth = mkAuth();
  const a = auth.authorize({ intent_id: "i-obs", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } },
    { expected_implementation_id: JS_IMPLEMENTATION_ID });
  const x = await auth.execute(reg, a.request);
  const acc = x.ok ? auth.accept(reg, a.request, x.result) : { ok: false };
  observedRun = { auth, req: a.request, res: x.result };
  R("authority-launched-execution",
    x.ok && acc.ok && acc.implementation_provenance === "observed"
      && acc.implementation_id === JS_IMPLEMENTATION_ID
      && acc.executable_artifact_id === JS_DIGEST
      && Array.isArray(acc.executor_sessions) && acc.executor_sessions.length === 1,
    `the host hashed the catalogued artifact closure (${JS_DIGEST.slice(0, 12)}…), launched the ` +
    `entrypoint that closure contains, sent the request and took the result — and acceptance reports ` +
    `family ${acc.implementation_id}, artifact ${String(acc.executable_artifact_id).slice(0, 12)}…, and ` +
    `${acc.executor_sessions?.length} recorded session. Sessions are a LIST because the key is over ` +
    `bytes: two launches producing identical output share it, and v0.8.0 overwrote one with the other ` +
    `while reporting a single id as if it named this copy's launch`);
}

// 12. P-3 ITSELF: there is no field in which to supply an action
{
  const auth = mkAuth();
  const a = auth.authorize({ intent_id: "i-p3", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } },
    { expected_implementation_id: JS_IMPLEMENTATION_ID });
  // the v0.8.0 attack, offered verbatim: declare the real closure, supply an
  // unrelated spawn. Both extra arguments are simply not read.
  let ranMine = false;
  const liar = { artifact_files: JS_WORKER_ENTRY.artifact_closure,
    spawn: () => { ranMine = true; return { send: () => ({ ok: true, result: null }), close() {} }; } };
  const x = await auth.execute(reg, a.request, liar);
  const acc = x.ok ? auth.accept(reg, a.request, x.result) : { ok: false };
  R("no-launcher-parameter",
    x.ok && !ranMine && acc.ok && acc.implementation_id === JS_IMPLEMENTATION_ID
      && DerivationAuthority.prototype.execute.length === 2,
    `execute takes ${DerivationAuthority.prototype.execute.length} parameters (registry, req); a third ` +
    `argument carrying artifact_files beside a spawn() is inert — the callback never ran (${ranMine}) ` +
    `and the real worker did. Under v0.8.0 that object WAS the API, and its two fields were unrelated: ` +
    `the authority hashed X and invoked Y`);
}

// 13. the catalog refuses an entrypoint outside the closure it hashes
{
  const outside = { [JS_IMPLEMENTATION_ID]: { kind: "node-worker",
    entrypoint: join(HERE, "derive_worker.mjs"),
    artifact_closure: [join(HERE, "derive_battery.mjs")] } };
  const bad = (() => { try { new ObservedExecutionHost(outside); return "ACCEPTED"; }
    catch (e) { return e.message; } })();
  const aliased = (() => { try { new ObservedExecutionHost({
      "impl-a-v1": JS_WORKER_ENTRY, "impl-b-v1": JS_WORKER_ENTRY }); return "ACCEPTED"; }
    catch (e) { return e.message; } })();
  const extra = (() => { try { new ObservedExecutionHost({ [JS_IMPLEMENTATION_ID]:
      { ...JS_WORKER_ENTRY, spawn: () => {} } }); return "ACCEPTED"; }
    catch (e) { return e.message; } })();
  R("catalog-entry-well-formed",
    /^catalog-entrypoint-outside-closure: /.test(bad) && /^catalog-closure-aliased: /.test(aliased)
      && /^catalog-entry-extra-field: /.test(extra),
    `an entrypoint outside its own hashed closure is refused (${bad.split(":")[0]}) — that is P-3 with ` +
    `the descriptor moved indoors, and moving it indoors is not a repair. Two families over one closure ` +
    `is refused (${aliased.split(":")[0]}), and a catalog entry carrying an extra field is refused ` +
    `(${extra}) — which is where a spawn() would have to reappear`);
}

// 14. relabelling an OBSERVED result after the fact
{
  const { auth, req, res } = observedRun;
  const asIfC = { ...res,
    execution_evidence: { ...res.execution_evidence, implementation_id: "impl-c-derive-v0.9.0" } };
  const acc = auth.accept(reg, req, asIfC);
  const v = validateForeignResult(reg, req, asIfC);
  R("relabel-after-observation",
    !acc.ok && acc.reason === "implementation-provenance-unavailable"
      && v.ok && v.implementation_claimed === "impl-c-derive-v0.9.0"
      && auth.observationOf(reg, req, asIfC) === null && auth.observationOf(reg, req, res) !== null,
    `an OBSERVED result with one byte of its label changed is ${acc.reason}: the observation is keyed ` +
    `over the whole execution event, so the relabelled bytes are not in the table at all. Note the ` +
    `split — the validator still says the semantics agree (implementation_claimed ` +
    `${v.implementation_claimed}); it is provenance that is absent, and they are different verdicts`);
}

// 15. a genuine observation cannot be re-pointed at other bytes
{
  const { auth, req, res } = observedRun;
  const inflated = { ...res, semantic_result: { ...res.semantic_result, value: 1005 } };
  const accInflated = auth.accept(reg, req, inflated);
  const auth2 = mkAuth();
  const b = auth2.authorize({ intent_id: "i-other", program_sem_id: PID,
    canonical_inputs: { bias: 1 }, requested_resources: { exact: ["fb"], predicates: [] } });
  R("observation-binds-request-and-bytes",
    !accInflated.ok && accInflated.reason === "foreign-result-divergence"
      && auth2.observationOf(reg, b.request, res) === null
      && auth.observationOf(reg, b.request, res) === null,
    `changing the value breaks re-derivation first (${accInflated.reason}) and would have missed the ` +
    `observation anyway; the same bytes under a DIFFERENT request find nothing even at the authority ` +
    `that ran them, because the key is over input AND output; and a second authority holds no ` +
    `observation at all, because each has its own host`);
}

// 16. an authority with no host cannot execute, and cannot pretend it did
{
  const bare = new DerivationAuthority(mkWorld());
  const a = bare.authorize({ intent_id: "i-nohost", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const x = await bare.execute(reg, a.request);
  const local = deriveLocally(reg, a.request);
  const acc = bare.accept(reg, a.request, local.result);
  const badHost = (() => { try { new DerivationAuthority(mkWorld(), { run: () => {} }); return "ACCEPTED"; }
    catch (e) { return e.message; } })();
  R("no-host-no-provenance",
    !x.ok && x.reason === "authority-has-no-execution-host"
      && acc.ok && acc.implementation_provenance === "unavailable"
      && badHost === "authority-host-must-be-an-ObservedExecutionHost",
    `${x.reason}; and in-process derivation at the same authority accepts with provenance ` +
    `${acc.implementation_provenance}. An object merely SHAPED like a host is refused at construction ` +
    `(${badHost}) — duck-typing the host is how a caller would supply the launcher again`);
}

// 17. a request naming an uncatalogued family does not run
{
  const auth = mkAuth();
  const a = auth.authorize({ intent_id: "i-uncat", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } },
    { expected_implementation_id: "impl-c-derive-v0.9.0" });
  const x = await auth.execute(reg, a.request);
  const two = new ObservedExecutionHost({ [JS_IMPLEMENTATION_ID]: JS_WORKER_ENTRY,
    "impl-js-derive-shadow": { ...JS_WORKER_ENTRY,
      artifact_closure: [join(HERE, "derive_worker.mjs"), join(HERE, "derive_protocol.mjs")] } });
  const amb = new DerivationAuthority(mkWorld(), two);
  const b = amb.authorize({ intent_id: "i-amb", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const y = await amb.execute(reg, b.request);
  R("uncatalogued-family-refused",
    !x.ok && /^executor-not-in-catalog: impl-c-derive-v0\.9\.0/.test(x.reason)
      && !y.ok && /^execute-implementation-ambiguous: /.test(y.reason),
    `${x.reason} — a C requirement against a catalog that holds only JS is refused before anything is ` +
    `launched. And with two catalogued families a request naming NONE is ${y.reason.split(":")[0]} ` +
    `rather than silently defaulting: picking one for the caller would be the authority choosing the ` +
    `provenance`);
}

// 18. the far side's program image is the AUTHORITY's, not a caller's
{
  const auth = mkAuth();
  const empty = new ProgramRegistry();          // holds nothing
  const a = auth.authorize({ intent_id: "i-img", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const x = await auth.execute(empty, a.request);
  const good = await auth.execute(reg, a.request);
  R("worker-image-is-the-registry's",
    !x.ok && x.reason === "program-unknown" && good.ok && good.result.semantic_result.value === 5
      && reg.image().length === 1,
    `executing against an EMPTY registry gives ${x.reason} on the far side, and against the real one ` +
    `gives ${good.ok && good.result.semantic_result.value}. At v0.8.0 the caller chose which programs ` +
    `the worker would hold, by passing them to the launcher it also built; the image is ` +
    `registry.image() now, and the authority already had a registry`);
}

// 19. registerExecutor and nameArtifact are both GONE
{
  const auth = mkAuth();
  R("registration-api-deleted",
    typeof auth.registerExecutor === "undefined" && typeof auth.nameArtifact === "undefined"
      && !("registerExecutor" in DerivationAuthority.prototype)
      && !("nameArtifact" in DerivationAuthority.prototype)
      && DerivationAuthority.prototype.accept.length === 3,
    `registerExecutor and nameArtifact are both absent from the instance and the prototype, and accept ` +
    `takes ${DerivationAuthority.prototype.accept.length} parameters. The catalog IS the naming policy ` +
    `and it is immutable at construction — an authority whose identity policy can move during its ` +
    `lifetime makes its own historical observations hard to read`);
}

await w.terminate();
console.log("═".repeat(96));
console.log(fail
  ? `DERIVE-REALM: FAIL — ${ran} cases ran, at least one failed`
  : `DERIVE-REALM: PASS — ${ran}/${ran}. Object authority does not cross the boundary, the realm reads ` +
    `only its grant, and an implementation identity is an EXECUTION EVENT THE AUTHORITY DROVE — where ` +
    `both the entrypoint and the transport are consequences of one immutable catalog entry, so there is ` +
    `no field left in which a caller may supply an action beside the evidence. Determinism, host ` +
    `confinement and TOCTOU-free artifact identity are SEPARATE scopes and are not claimed here.`);
process.exit(fail ? 1 : 0);
