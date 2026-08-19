/* ═══════════════════════════════════════════════════════════════════════════
   probe_reread_v13_repro.mjs — the request was authenticated as one value and
   used as another.

   v0.12.0 wrote the round-27 law correctly:

       Every untrusted structure that becomes authority state is canonicalised
       into an OWNED SNAPSHOT exactly once; validation, identity computation and
       storage operate only on that snapshot.

   and then applied it exactly where authority state was being CONSTRUCTED —
   ProgramRegistry.bind, the executor catalog, the issued request. Method
   arguments kept the older shape.

   P-7   AUTHENTICATE EXTERNAL X, THEN EXERCISE AUTHORITY USING LATER X'.

            execute(req)
              wasIssued(req)   → hashes ONE read of every field → PASSES
              req.expected_implementation_id      → read again
              { message: req } → read again by the host's canonicalBytes,
                                 and again by the worker's structured clone

         With a request whose `program_sem_id` answers const(5) to the first
         read and const(999) to every read after it:

            authority issued   request R → const(5)
            authority executed           → const(999)
            native worker returned        999

         Both programs are genuinely in the authority's own registry, so
         nothing is malformed, no identity is forged and nothing fails closed.
         Then acceptance, handed a FRESH time-varying copy of the same request:

            wasIssued      sees the issued const(5) bytes      → PASS
            re-derivation  now sees const(999), re-derives 999 → AGREES
            provenance     the execution really was authority-driven → observed
            freshness      → PASS

            { ok: true, validated: true, fresh_at_check: true,
              implementation_provenance: "observed" }

         for a result the authority never authorized. The same 999 result paired
         with the FROZEN issued request is correctly refused as
         result-program-mismatch — so this is not fail-closed hygiene that
         happens to hold. The forgery is precisely the caller's retained
         ownership, and nothing else.

   P-7b  THE SAME DEFECT ONE ARGUMENT TO THE RIGHT — the result side.

         `res` was live caller-owned input consulted by six checks in sequence:
         schema, footprint containment, re-derivation, trace conformance, the
         provenance lookup and freshness. Closed in the same round rather than
         waiting to be found, because "one argument to the right" is how this
         ladder has gone seven times.

   P-7c  AND THE SAME DEFECT IN THE HOST, WHICH GPT'S LIST DID NOT REACH.

         ObservedExecutionHost.run() canonicalised `invocation` for the
         observation key and then handed the SAME live object to the transport:

            inputCanonical = canonicalBytes(invocation)   ← read 1: the KEY
            runNodeWorker(entry, invocation)              ← read 2: what RUNS

         So a caller-owned invocation whose `message` answers honestly on read 1
         and hostilely on read 2 is KEYED under one request and EXECUTED as
         another, and the table ends up holding

            observation under the HONEST request bytes   PRESENT
            observation under the bytes that actually ran ABSENT

         which is worse than being unable to find a forged observation: it is a
         TRUE-LOOKING one for an execution that did not happen, in the very
         table round 23 built so that relabelling would move the key.
         Unreachable through DerivationAuthority.execute, whose invocation is
         built from owned parts — but the host is exported, FilmAuthority and
         lowering_check drive it directly, and it is an authority operation in
         its own right. The obligation is a property of the ENTRYPOINT, not of
         whoever happens to call it politely.

   THE RULE, stated so that it covers arguments and not only constructor data:

       Every authority operation consumes either an authority-owned object or
       one canonical snapshot made at entry. No trust decision authenticates one
       read of external state and exercises authority using another.

   Mechanically: ownCanonical() at the top of every method taking a non-root
   data argument; `#issued` keeps the REQUEST and not merely its hash — "were
   these bytes issued?" was answerable before, "what did I issue?" was not, and
   a method that needs the second question has no choice but to re-read the
   caller — and wasIssued() returns that owned request.

   Seven rungs: label · name · action · semantic oracle · authority-bearing
   object · mutable data read twice · mutable data authenticated once. @6 and @7
   are one rule seen at two moments: @6 validates X and stores X'; @7
   authenticates X and exercises authority with X'.

   THE FROZEN FUNCTIONS BELOW are v0.12.0's execute() and accept() bodies,
   reaching the registry image and the host through public accessors instead of
   the private fields the real methods used. Same calls, same order. That is the
   same construction probe_snapshot_v12_repro.mjs uses for v11Admit, and it is
   stated here rather than left for a reader to notice.

   PAIRED, and it gates.
   ═══════════════════════════════════════════════════════════════════════════ */
import {
  DerivationAuthority, ProgramRegistry, programSemId, canonicalBytes,
  validateForeignResult, validateFootprintFresh, requestSemId,
  JS_IMPLEMENTATION_ID, DERIVE_EXEC_DOMAIN, SUPPLIER_LADDER, LADDER_RUNGS,
} from "./derive_protocol.mjs";
import { ObservedExecutionHost, canonicalBytes as hostCanonicalBytes }
  from "./observed_execution_host.mjs";
import { defaultDeriveCatalog } from "./derive_launcher.mjs";

const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "CONFINED" : "BREACH  "}  ${id.padEnd(32)} ${note}`); };

const P5 = { op: "const", value: 5 };
const P999 = { op: "const", value: 999 };
const ID5 = programSemId(P5);
const ID999 = programSemId(P999);
const mkWorld = () => ({ res: { fb: { value: 5, version: 1 } },
  read(r) { return { ...this.res[r] }; }, scope: (q) => "scope:" + q });

const mkAuth = () => new DerivationAuthority(mkWorld(), [P5, P999],
  defaultDeriveCatalog(JS_IMPLEMENTATION_ID));

/** the issued request, and a time-varying object mirroring it: const(5) for the
 *  first `honest` reads of program_sem_id, const(999) for every read after. */
function timeVarying(frozen, honest) {
  let reads = 0;
  const o = {};
  for (const k of Object.keys(frozen)) {
    if (k === "program_sem_id")
      Object.defineProperty(o, k, { enumerable: true,
        get() { return ++reads <= honest ? ID5 : ID999; } });
    else Object.defineProperty(o, k, { enumerable: true, value: frozen[k] });
  }
  return { obj: o, reads: () => reads };
}

/* ── v0.12.0's execute(), VERBATIM in its essentials. A FROZEN COPY.
      Authenticate the caller's object, then keep reading the caller's object.
      Do not repair it. ─────────────────────────────────────────────────────── */
async function v12Execute(auth, host, req) {
  const iss = auth.wasIssued(req);                              // read 1: PASSES
  if (!iss.ok) return { ok: false, reason: iss.reason };
  const family = req.expected_implementation_id;                // read 2
  const programs = auth.programIds().map((id) => auth.programOf(id));
  const invocation = { init: { programs }, message: req };      // read 3, and 4
  const r = await host.run(family, DERIVE_EXEC_DOMAIN, invocation);
  if (!r.ok) return { ok: false, reason: r.reason };
  if (!r.output?.ok) return { ok: false, reason: r.output?.reason ?? "nothing" };
  return { ok: true, result: r.output.result };
}

/* ── v0.12.0's accept(), VERBATIM in its essentials. A FROZEN COPY. ───────── */
function v12Accept(auth, host, req, res) {
  const iss = auth.wasIssued(req);                              // read 1: PASSES
  if (!iss.ok) return { ok: false, reason: iss.reason };
  const reg = new ProgramRegistry();
  for (const id of auth.programIds()) reg.bind(auth.programOf(id));
  const v = validateForeignResult(reg, req, res);                // reads again
  if (!v.ok) return v;
  const programs = auth.programIds().map((id) => auth.programOf(id));
  const observed = host.observationOf(DERIVE_EXEC_DOMAIN,
    { init: { programs }, message: req }, { ok: true, result: res }) ?? undefined;
  if ("expected_implementation_id" in req) {
    if (observed === undefined)
      return { ok: false, reason: "implementation-provenance-unavailable" };
    if (observed.implementation_family_id !== req.expected_implementation_id)
      return { ok: false, reason: "implementation-mismatch" };
  }
  // an equivalent reader: the authority's own is private, and this probe's
  // World never moves, so freshness answers the same either way
  const f = validateFootprintFresh(mkWorld(), res.semantic_result.read_footprint);
  if (!f.ok) return { ok: false, reason: f.reason };
  return { ok: true, validated: true, fresh_at_check: true,
    implementation_provenance: observed === undefined ? "unavailable" : "observed",
    implementation_id: observed?.implementation_family_id };
}

/* ── P-7 against the frozen v0.12.0 ──────────────────────────────────────── */
let forged = null;
{
  const auth = mkAuth();
  const host = new ObservedExecutionHost(defaultDeriveCatalog(JS_IMPLEMENTATION_ID));
  const a = auth.authorize({ intent_id: "p7", program_sem_id: ID5,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } },
    { expected_implementation_id: JS_IMPLEMENTATION_ID });
  const { obj, reads } = timeVarying(a.request, 1);
  const run = await v12Execute(auth, host, obj);
  forged = run.ok ? run.result : null;
  const drove999 = run.ok && run.result.program_sem_id === ID999
    && run.result.semantic_result.value === 999;
  R("P-7 frozen-v0.12.0-execute", !drove999,
    `${reads()} reads of one getter. wasIssued saw const(5)'s bytes and PASSED; every read after it ` +
    `returned const(999)'s id. The authority issued ${ID5.slice(0, 14)}… and executed ` +
    `${run.result?.program_sem_id?.slice(0, 14)}…, and the worker returned ` +
    `${JSON.stringify(run.result?.semantic_result?.value)}. Both programs are genuinely in the ` +
    `authority's own registry, so nothing is malformed and nothing fails closed`);
}

/* ── P-7 acceptance against the frozen v0.12.0 ───────────────────────────── */
{
  const auth = mkAuth();
  const host = new ObservedExecutionHost(defaultDeriveCatalog(JS_IMPLEMENTATION_ID));
  const a = auth.authorize({ intent_id: "p7", program_sem_id: ID5,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } },
    { expected_implementation_id: JS_IMPLEMENTATION_ID });
  // drive the execution through the frozen path so the host really observes it
  const drive = await v12Execute(auth, host, timeVarying(a.request, 1).obj);
  const res = drive.ok ? drive.result : forged;
  const acc = res ? v12Accept(auth, host, timeVarying(a.request, 1).obj, res) : { ok: false };
  const honest = res ? v12Accept(auth, host, a.request, res) : { ok: false };
  const accepted999 = acc.ok && acc.implementation_provenance === "observed"
    && res.semantic_result.value === 999;
  R("P-7 frozen-v0.12.0-accept", !accepted999,
    `acceptance of the 999 result under a fresh time-varying copy returns ` +
    `${JSON.stringify({ ok: acc.ok, validated: acc.validated, provenance: acc.implementation_provenance })} ` +
    `— re-derivation AGREES because it re-derived 999 against 999, and the provenance is an execution ` +
    `the authority genuinely drove. The SAME result under the FROZEN issued request is refused ` +
    `(${honest.reason}), which is what makes this a forgery rather than fail-closed hygiene: the ` +
    `difference is entirely the caller's retained ownership`);
}

/* ── live: execute uses what was ISSUED, not what is presented ───────────── */
{
  const auth = mkAuth();
  const a = auth.authorize({ intent_id: "p7", program_sem_id: ID5,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } },
    { expected_implementation_id: JS_IMPLEMENTATION_ID });
  const { obj, reads } = timeVarying(a.request, 1);
  const run = await auth.execute(obj);
  R("live: execute-uses-the-issued-request",
    run.ok && reads() === 1 && run.result.program_sem_id === ID5
      && run.result.semantic_result.value === 5,
    `the getter is read EXACTLY ${reads()} time — ownCanonical takes the snapshot inside wasIssued, ` +
    `which returns the AUTHORITY'S OWN copy of the request, and execute reads that. The program that ` +
    `ran is ${run.result?.program_sem_id?.slice(0, 14)}… and the value is ` +
    `${JSON.stringify(run.result?.semantic_result?.value)} — the one that was authorized`);
}

/* ── live: and the same for acceptance, on both arguments ───────────────── */
{
  const auth = mkAuth();
  const a = auth.authorize({ intent_id: "p7", program_sem_id: ID5,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } },
    { expected_implementation_id: JS_IMPLEMENTATION_ID });
  const run = await auth.execute(a.request);
  const { obj, reads } = timeVarying(a.request, 1);
  const acc = auth.accept(obj, run.result);
  // and a time-varying RESULT: honest for the first read, 999 after
  let rr = 0;
  const liveRes = {};
  for (const k of Object.keys(run.result))
    Object.defineProperty(liveRes, k, k === "program_sem_id"
      ? { enumerable: true, get() { return ++rr <= 1 ? ID5 : ID999; } }
      : { enumerable: true, value: run.result[k] });
  const accRes = auth.accept(a.request, liveRes);
  R("live: accept-owns-both-arguments",
    acc.ok && reads() === 1 && accRes.ok && rr === 1
      && acc.implementation_provenance === "observed",
    `a time-varying REQUEST is read ${reads()} time and acceptance is ${acc.ok ? "correct" : acc.reason} ` +
    `with provenance ${acc.implementation_provenance}; a time-varying RESULT is read ${rr} time and ` +
    `acceptance is ${accRes.ok ? "correct" : accRes.reason}. Neither object is consulted twice, so ` +
    `there is no window between the read that authenticates and the read that acts`);
}

/* ── live: the issued request is kept, not only its hash ────────────────── */
{
  const auth = mkAuth();
  const a = auth.authorize({ intent_id: "p7", program_sem_id: ID5,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } });
  const iss = auth.wasIssued(timeVarying(a.request, 1).obj);
  const stranger = mkAuth().wasIssued(a.request);
  R("live: issuance-returns-the-owned-request",
    iss.ok && iss.request !== undefined && Object.isFrozen(iss.request)
      && requestSemId(iss.request) === requestSemId(a.request)
      && iss.request.program_sem_id === ID5
      && !stranger.ok && stranger.request === undefined,
    `wasIssued answers "yes, and here is the one I issued": a deep-frozen object whose ` +
    `request_sem_id matches. v0.12.0 stored only the hash, which can answer "were these bytes ` +
    `issued?" and cannot answer "what did I issue?", so every method that needed the second ` +
    `question had no choice but to re-read the caller. A stranger still gets ${stranger.reason} ` +
    `and no request`);
}

/* ── live: a non-canonical argument dies at the entry, not halfway through ─ */
{
  const auth = mkAuth();
  const a = auth.authorize({ intent_id: "p7", program_sem_id: ID5,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } });
  const run = await auth.execute(a.request);
  const withFn = auth.accept(a.request, { ...run.result, evil() {} });
  const asRegistry = auth.accept(new ProgramRegistry(), run.result);
  const badIntent = auth.authorize({ intent_id: "x", program_sem_id: ID5,
    canonical_inputs: { f: () => 1 }, requested_resources: { exact: [], predicates: [] } });
  R("live: non-canonical-dies-at-entry",
    /^result-not-canonical: /.test(withFn.reason)
      && /^request-not-canonical: /.test(asRegistry.reason)
      && /^intent-not-canonical: /.test(badIntent.reason),
    `a result carrying a function is ${withFn.reason.split(":")[0]}, a ProgramRegistry in the request ` +
    `slot is ${asRegistry.reason.split(":")[0]}, and an intent carrying a closure is ` +
    `${badIntent.reason.split(":")[0]} — each refused by canonicalBytes at the entry, before any ` +
    `field has been examined. SEVER BEFORE VALIDATING is round 27's other half, and it is what makes ` +
    `the snapshot a refusal surface as well as a copy`);
}

/* ── P-7c against the frozen v0.2.1 host ─────────────────────────────────
      The transport is elided on purpose: the defect is entirely the ordering
      of the two reads, and the live case below drives the REAL host end to
      end. Re-implementing Worker launch here would prove the occasion. ───── */
{
  const auth = mkAuth();
  const a = auth.authorize({ intent_id: "p7c", program_sem_id: ID5,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } });
  const evil = { ...a.request, program_sem_id: ID999 };
  let reads = 0;
  const invocation = { init: { programs: [P5, P999] },
    get message() { return ++reads <= 1 ? a.request : evil; } };
  // v0.2.1: key over read 1, execute read 2
  const inputCanonical = hostCanonicalBytes(invocation);
  const executed = invocation.message;
  const keyedOver = JSON.parse(inputCanonical).message;
  const split = keyedOver.program_sem_id === ID5 && executed.program_sem_id === ID999;
  R("P-7c frozen-v0.2.1-host", !split,
    `${reads} reads of one getter inside run(). The observation is keyed over ` +
    `${keyedOver.program_sem_id?.slice(0, 14)}… and what the transport receives is ` +
    `${executed.program_sem_id?.slice(0, 14)}…. The table then holds a true-looking observation for ` +
    `an execution that did not happen — in the table built so that relabelling would MOVE the key`);
}

/* ── live: the host severs its invocation and runs what it keyed ─────────── */
{
  const auth = mkAuth();
  const host = new ObservedExecutionHost(defaultDeriveCatalog(JS_IMPLEMENTATION_ID));
  const a = auth.authorize({ intent_id: "p7c", program_sem_id: ID5,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } });
  const evil = { ...a.request, program_sem_id: ID999 };
  const programs = [P5, P999];
  let reads = 0;
  const r = await host.run(JS_IMPLEMENTATION_ID, DERIVE_EXEC_DOMAIN,
    { init: { programs }, get message() { return ++reads <= 1 ? a.request : evil; } });
  const underRan = host.observationOf(DERIVE_EXEC_DOMAIN,
    { init: { programs }, message: a.request }, r.output);
  const underEvil = host.observationOf(DERIVE_EXEC_DOMAIN,
    { init: { programs }, message: evil }, r.output);
  R("live: host-runs-what-it-keyed",
    reads === 1 && r.ok && r.output?.result?.semantic_result?.value === 5
      && underRan !== null && underEvil === null,
    `the getter is read EXACTLY ${reads} time; the worker answered ` +
    `${JSON.stringify(r.output?.result?.semantic_result?.value)} for the request that was keyed; and ` +
    `the observation is present under the bytes that ran and absent under the ones that did not. The ` +
    `host is an authority operation in its own right — DerivationAuthority.execute passes it owned ` +
    `parts, but FilmAuthority and lowering_check drive it directly and politeness is not a boundary`);
}

/* ── live: the ladder is one record and it has seven rungs ──────────────── */
{
  R("live: seven-rung-ladder-derived",
    LADDER_RUNGS === 7 && SUPPLIER_LADDER.length === 7
      && SUPPLIER_LADDER[5].supplied === "MUTABLE DATA READ TWICE"
      && SUPPLIER_LADDER[6].supplied === "MUTABLE DATA AUTHENTICATED ONCE"
      && DerivationAuthority.prototype.accept.length === 2
      && DerivationAuthority.prototype.execute.length === 1,
    `${LADDER_RUNGS} rungs, one shape, and the count comes from SUPPLIER_LADDER rather than from ` +
    `prose — at round 27A the live realm battery was still printing "Four rungs" against a six-rung ` +
    `mechanism. @6 and @7 are one rule at two moments: validate X then store X', authenticate X then ` +
    `act with X'. What a caller supplies is an INTENT and a RESULT TO VALIDATE, each snapshotted at ` +
    `entry rather than trusted to hold still`);
}

console.log("=".repeat(100));
const frozen = results.filter((r) => r.id.includes("frozen"));
const live = results.filter((r) => r.id.startsWith("live:"));
const frozenHeld = frozen.filter((r) => r.held);
const liveBreached = live.filter((r) => !r.held);
console.log(
  `REREAD v0.13 REPRO: ${frozen.length - frozenHeld.length}/${frozen.length} reproduce against the ` +
  `frozen v0.12.0 · ${live.length - liveBreached.length}/${live.length} confined against live` +
  (frozenHeld.length ? ` — VACUOUS: ${frozenHeld.map((r) => r.id).join(", ")}` : "") +
  (liveBreached.length ? ` — REGRESSION: ${liveBreached.map((r) => r.id).join(", ")}` : ""));
process.exit(frozenHeld.length + liveBreached.length ? 1 : 0);
