/* derive_realm_battery.mjs — the crossing itself, v0.8.0.
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
  DerivationAuthority, digestArtifactFiles, executionKey, requestSemId,
} from "./derive_protocol.mjs";
import { jsWorkerLauncher, fileClosureLauncher } from "./derive_launcher.mjs";

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

// ── v0.8.0: THE AUTHORITY LAUNCHES ────────────────────────────────────────
const mkWorld = () => ({ res: { fb: { value: 5, version: 1 } },
  read(r) { return { ...this.res[r] }; }, scope(q) { return "scope:" + q; } });
const JS_DIGEST = digestArtifactFiles([join(HERE, "derive_worker.mjs"), join(HERE, "derive_protocol.mjs")]);

// 11. an execution the authority drove, and the three identities it separates
let observedRun = null;
{
  const auth = new DerivationAuthority(mkWorld());
  auth.nameArtifact(JS_DIGEST, JS_IMPLEMENTATION_ID);
  const a = auth.authorize({ intent_id: "i-obs", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } },
    { expected_implementation_id: JS_IMPLEMENTATION_ID });
  const x = await auth.execute(a.request, jsWorkerLauncher([P]));
  const acc = x.ok ? auth.accept(reg, a.request, x.result) : { ok: false };
  observedRun = { auth, req: a.request, res: x.result };
  R("authority-launched-execution",
    x.ok && acc.ok && acc.implementation_provenance === "observed"
      && acc.implementation_id === JS_IMPLEMENTATION_ID
      && acc.executable_artifact_id === JS_DIGEST
      && acc.executor_session_id === x.executor_session_id,
    `the authority hashed the artifact closure (${JS_DIGEST.slice(0, 12)}…), resolved its name from its ` +
    `OWN policy, spawned it, sent the request and took the result — and acceptance reports three ` +
    `identities: family ${acc.implementation_id}, artifact ${String(acc.executable_artifact_id).slice(0, 12)}…, ` +
    `session ${String(acc.executor_session_id).slice(0, 12)}…`);
}

// 12. P-2 ITSELF: naming C and never launching C buys nothing (F-7 shape)
{
  const auth = new DerivationAuthority(mkWorld());
  auth.nameArtifact(JS_DIGEST, JS_IMPLEMENTATION_ID);
  // the caller names a C family against a digest of its own choosing — the
  // policy accepts the NAMING, because a naming is not an observation
  const FAKE_C_DIGEST = "c".repeat(64);
  let named = null;
  try { named = auth.nameArtifact(FAKE_C_DIGEST, "impl-c-derive-v0.8.0"); } catch (e) { named = e.message; }
  const a = auth.authorize({ intent_id: "i-p2", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } },
    { expected_implementation_id: "impl-c-derive-v0.8.0" });
  // JS runs. Nothing C-shaped is anywhere near this.
  const x = await auth.execute(a.request, jsWorkerLauncher([P]));
  R("naming-c-without-launching-c",
    named?.ok === true && !x.ok && /implementation-mismatch: want impl-c-derive-v0.8.0/.test(x.reason ?? ""),
    `naming a digest "impl-c-derive-v0.8.0" SUCCEEDS — a naming policy is not an observation and does ` +
    `not pretend to be — and the run still dies: ${x.reason}. Under v0.7.0 the equivalent three lines ` +
    `(registerExecutor("impl-c-derive-v0.8.0"), run JS, accept with the handle) returned ok:true with ` +
    `implementation_provenance "observed"`);
}

// 13. relabelling an OBSERVED result after the fact (F-7, at acceptance)
{
  const { auth, req, res } = observedRun;
  const asIfC = { ...res,
    execution_evidence: { ...res.execution_evidence, implementation_id: "impl-c-derive-v0.8.0" } };
  const acc = auth.accept(reg, req, asIfC);
  const v = validateForeignResult(reg, req, asIfC);
  R("relabel-after-observation",
    !acc.ok && acc.reason === "implementation-provenance-unavailable"
      && v.ok && v.implementation_claimed === "impl-c-derive-v0.8.0"
      && auth.observationOf(req, asIfC) === null && auth.observationOf(req, res) !== null,
    `an OBSERVED result with one byte of its label changed is ${acc.reason}: the observation is keyed ` +
    `over the whole execution event, so the relabelled bytes are not in the table at all. Note the ` +
    `split — the validator still says the semantics agree (implementation_claimed ` +
    `${v.implementation_claimed}); it is provenance that is absent, and they are different verdicts`);
}

// 14. a genuine observation cannot be re-pointed at other bytes (F-6)
{
  const { auth, req, res } = observedRun;
  const inflated = { ...res,
    semantic_result: { ...res.semantic_result, value: 1005 } };
  const accInflated = auth.accept(reg, req, inflated);
  // and the SAME honest result under a DIFFERENT request finds nothing either
  const auth2 = new DerivationAuthority(mkWorld());
  auth2.nameArtifact(JS_DIGEST, JS_IMPLEMENTATION_ID);
  const b = auth2.authorize({ intent_id: "i-other", program_sem_id: PID,
    canonical_inputs: { bias: 1 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const crossAuth = auth2.observationOf(b.request, res);
  R("observation-binds-request-and-bytes",
    !accInflated.ok && accInflated.reason === "foreign-result-divergence" && crossAuth === null
      && executionKey(requestSemId(req), res) !== executionKey(requestSemId(b.request), res),
    `changing the value breaks re-derivation first (${accInflated.reason}) and would have missed the ` +
    `observation anyway; and a second authority holds no observation for the same bytes, because the ` +
    `key is over request AND result and the table is private to the authority that drove the run`);
}

// 15. an artifact the authority has no name for does not run
{
  const auth = new DerivationAuthority(mkWorld());          // no nameArtifact call at all
  const a = auth.authorize({ intent_id: "i-unnamed", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const x = await auth.execute(a.request, jsWorkerLauncher([P]));
  // and a launcher declaring a DIFFERENT closure reaches a different identity
  const other = digestArtifactFiles([join(HERE, "derive_worker.mjs")]);
  R("unnamed-artifact-refused",
    !x.ok && /^artifact-unnamed: /.test(x.reason) && other !== JS_DIGEST,
    `${x.reason} — the authority resolves the name from the bytes it hashed, so an unnamed artifact is ` +
    `refused before it is spawned. Declaring a narrower closure (worker only, ${other.slice(0, 12)}…) is ` +
    `a DIFFERENT identity from the worker-plus-protocol closure (${JS_DIGEST.slice(0, 12)}…): what the ` +
    `executor depends on is part of what it is`);
}

// 16. the launcher supplies mechanism and no identity
{
  const auth = new DerivationAuthority(mkWorld());
  auth.nameArtifact(JS_DIGEST, JS_IMPLEMENTATION_ID);
  const a = auth.authorize({ intent_id: "i-mech", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  // a launcher that spawns the JS worker while POINTING its declaration at C's
  // source. The authority hashes what the declaration names, so the two cannot
  // be separated: naming other files means being identified as other files.
  const realLauncher = jsWorkerLauncher([P]);
  const liar = fileClosureLauncher([join(HERE, "derive_realm_battery.mjs")], () => realLauncher.spawn());
  const x = await auth.execute(a.request, liar);
  const malformed = await auth.execute(a.request, { artifact_files: ["x"], spawn: null });
  const missing = await auth.execute(a.request, fileClosureLauncher([join(HERE, "no-such-file.mjs")],
    () => realLauncher.spawn()));
  R("launcher-declares-no-identity",
    !x.ok && /^artifact-unnamed: /.test(x.reason) && !malformed.ok && malformed.reason === "launcher-malformed"
      && !missing.ok && /^artifact-unreadable: /.test(missing.reason),
    `a launcher that spawns the real worker while declaring someone else's files is identified by what ` +
    `it declared (${x.reason}) — there is no field in which it may simply state a name. A malformed ` +
    `launcher is ${malformed.reason}; an unreadable one is refused before any spawn`);
}

// 17. the naming policy is injective and cannot be rewritten mid-run
{
  const auth = new DerivationAuthority(mkWorld());
  auth.nameArtifact(JS_DIGEST, JS_IMPLEMENTATION_ID);
  const rebind = (() => { try { auth.nameArtifact(JS_DIGEST, "impl-c-derive-v0.8.0"); return null; }
    catch (e) { return e.message; } })();
  const realias = (() => { try { auth.nameArtifact("a".repeat(64), JS_IMPLEMENTATION_ID); return null; }
    catch (e) { return e.message; } })();
  const idem = (() => { try { return auth.nameArtifact(JS_DIGEST, JS_IMPLEMENTATION_ID).ok; }
    catch { return false; } })();
  R("naming-policy-injective",
    /^artifact-already-named: /.test(rebind ?? "") && /^family-already-bound: /.test(realias ?? "") && idem === true,
    `renaming an already-named digest is refused (${rebind}) and pointing an already-bound family at ` +
    `other bytes is refused (${realias}); restating the same pair is idempotent. A policy a caller can ` +
    `rewrite mid-run is a policy a caller chooses`);
}

// 18. registerExecutor is GONE, not deprecated
{
  const auth = new DerivationAuthority(mkWorld());
  const gone = typeof auth.registerExecutor === "undefined"
    && !("registerExecutor" in DerivationAuthority.prototype);
  const arity = DerivationAuthority.prototype.accept.length;
  R("registration-api-deleted", gone && arity === 3,
    `registerExecutor is absent from the instance and the prototype, and accept takes ${arity} ` +
    `parameters (registry, req, res) — no provenance argument survives for a caller to fill. Round 17 ` +
    `removed caller-supplied proof from issuance; v0.7.0 reintroduced it one level up at acceptance`);
}

await w.terminate();
console.log("═".repeat(96));
console.log(fail
  ? `DERIVE-REALM: FAIL — ${ran} cases ran, at least one failed`
  : `DERIVE-REALM: PASS — ${ran}/${ran}. Object authority does not cross the boundary, the realm reads ` +
    `only its grant, and an implementation identity is now an EXECUTION EVENT THE AUTHORITY DROVE: it ` +
    `hashes the artifact closure, resolves the name from its own policy, launches, and keys the ` +
    `observation over the whole request-and-result. Determinism, host confinement and TOCTOU-free ` +
    `artifact identity are SEPARATE scopes and are not claimed here.`);
process.exit(fail ? 1 : 0);
