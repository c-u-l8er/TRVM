/* ═══════════════════════════════════════════════════════════════════════════
   probe_hostown_v11_repro.mjs — the authority accepted somebody else's
   execution-authority object and then trusted its methods.

   P-4 said: don't accept somebody else's semantic REGISTRY object; build yours
   from data. v0.10.0 did exactly that — and one constructor argument later it
   was still accepting a ready-made `ObservedExecutionHost`, guarded by

       if (host !== null && !(host instanceof ObservedExecutionHost))
         throw new Error("authority-host-must-be-an-ObservedExecutionHost");

   P-5  AN instanceof GUARD IS SATISFIED BY A SUBCLASS.

            class EvilHost extends ObservedExecutionHost {
              async run() { throw new Error("must not execute"); }
              observationOf() {
                return { implementation_family_id: "impl-c-fake-v1",
                         implementation_families: ["impl-c-fake-v1"],
                         executable_artifact_id: "fake-artifact",
                         executor_sessions: ["fake-session"] };
              }
            }

            evil instanceof ObservedExecutionHost   →  true

        Issue a request requiring impl-c-fake-v1, derive an ordinary honest
        result, relabel its execution claim, and accept:

            → { ok: true, validated: true, fresh_at_check: true,
                implementation_provenance: "observed",
                implementation_id: "impl-c-fake-v1",
                executable_artifact_id: "fake-artifact",
                executor_sessions: ["fake-session"] }

        NOTHING EXECUTED. `run` was never called; it throws if it is. The
        observation table, the artifact digest, the catalog and hash-then-launch
        are all still correct and all still bypassed, because the object that
        was asked was not the object that holds them.

   THE SUPPLIER LADDER, five rungs and one shape:

       @1  the caller supplied the implementation LABEL
       @2  the caller supplied the registration NAME
       @3  the caller supplied the ACTION beside the artifact evidence
       @4  the caller supplied the SEMANTIC ORACLE at acceptance
       @5  the caller supplied the EXECUTION-AUTHORITY OBJECT itself

   Each rung was in the parameter that had stopped being looked at because it
   was "obviously infrastructure". @5's guard was the strongest yet and still
   answered the wrong question: `instanceof` asks what a thing IS DESCENDED
   FROM, and the question is WHO BUILT IT.

   AND THE REPAIR IS NOT A BETTER TYPE CHECK. `Object.getPrototypeOf(host) ===
   ObservedExecutionHost.prototype` would exclude the subclass and would be P-4
   repeated as a tighter predicate. The authority takes CATALOG DATA and
   constructs the host itself, against the module's own class binding, which no
   caller can substitute.

   PAIRED, and it gates.
   ═══════════════════════════════════════════════════════════════════════════ */
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  ProgramRegistry, DerivationAuthority, deriveLocally, validateForeignResult,
  JS_IMPLEMENTATION_ID,
} from "./derive_protocol.mjs";
import { ObservedExecutionHost } from "./observed_execution_host.mjs";
import { JS_WORKER_ENTRY, defaultDeriveCatalog } from "./derive_launcher.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "CONFINED" : "BREACH  "}  ${id.padEnd(30)} ${note}`); };

const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const mkWorld = () => ({ res: { fb: { value: 5, version: 1 } },
  read(r) { return { ...this.res[r] }; }, scope(q) { return "scope:" + q; } });
const reg = new ProgramRegistry(); const PID = reg.bind(P);
const FAKE = "impl-c-fake-v1";
const CATALOG = defaultDeriveCatalog(JS_IMPLEMENTATION_ID);

/** The subclass. It is not exotic: it overrides two methods and inherits the
 *  rest, and every guard v0.10.0 had is satisfied. */
class EvilHost extends ObservedExecutionHost {
  async run() { throw new Error("must not execute"); }
  observationOf() {
    return { implementation_family_id: FAKE, implementation_families: [FAKE],
      executable_artifact_id: "fake-artifact", executor_sessions: ["fake-session"] };
  }
}

/* ── v0.10.0's constructor guard, VERBATIM ────────────────────────────────
   A FROZEN COPY. It is wrong on purpose and must stay wrong. */
class V10Authority {
  #host; #issued = new Map();
  constructor(host) {
    if (host !== null && !(host instanceof ObservedExecutionHost))
      throw new Error("authority-host-must-be-an-ObservedExecutionHost");
    this.#host = host;
  }
  remember(req) { this.#issued.set(req.request_id, true); }
  accept(registry, req, res) {
    if (!this.#issued.get(req.request_id)) return { ok: false, reason: "not-issued" };
    const v = validateForeignResult(registry, req, res);
    if (!v.ok) return v;
    const o = this.#host.observationOf(req, res);      // ← asks the object it was handed
    if ("expected_implementation_id" in req) {
      if (!o) return { ok: false, reason: "implementation-provenance-unavailable" };
      if (o.implementation_family_id !== req.expected_implementation_id)
        return { ok: false, reason: "implementation-mismatch" };
    }
    return o ? { ok: true, validated: true, fresh_at_check: true,
      implementation_provenance: "observed", implementation_id: o.implementation_family_id,
      executable_artifact_id: o.executable_artifact_id, executor_sessions: o.executor_sessions }
      : { ok: true, validated: true, fresh_at_check: true, implementation_provenance: "unavailable" };
  }
}

/* ── P-5 against the frozen v0.10.0 ──────────────────────────────────────── */
{
  const issuer = new DerivationAuthority(mkWorld(), [P]);
  const evil = new EvilHost(CATALOG);
  const v10 = new V10Authority(evil);
  const { request: req } = issuer.authorize({ intent_id: "p5", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } },
    { expected_implementation_id: FAKE });
  v10.remember(req);
  const { expected_implementation_id: _w, ...bare } = req;
  const honest = deriveLocally(reg, bare).result;
  const relabelled = { ...honest, request_id: req.request_id,
    execution_evidence: { ...honest.execution_evidence, implementation_id: FAKE } };
  const acc = v10.accept(reg, req, relabelled);
  R("P-5 frozen-v0.10.0",
    !(acc.ok && acc.implementation_provenance === "observed" && acc.implementation_id === FAKE),
    `evil instanceof ObservedExecutionHost is ${evil instanceof ObservedExecutionHost}, and NOTHING ` +
    `EXECUTED — run() throws if it is called. Acceptance returned ok=${acc.ok}, provenance ` +
    `${acc.implementation_provenance}, id ${acc.implementation_id}, artifact ` +
    `${acc.executable_artifact_id}. The catalog, the digest, the observation table and hash-then-launch ` +
    `are all still correct and all still bypassed, because the object that was ASKED was not the object ` +
    `that HOLDS them`);
}

/* ── P-5b: the tighter type check that would have been the wrong repair ──── */
{
  const evil = new EvilHost(CATALOG);
  const exactProto = Object.getPrototypeOf(evil) === ObservedExecutionHost.prototype;
  // a Proxy passes even THAT, because get() answers for whatever it likes
  const proxied = new Proxy(new ObservedExecutionHost(CATALOG), {
    get(t, k) { return k === "observationOf"
      ? () => ({ implementation_family_id: FAKE, implementation_families: [FAKE],
                 executable_artifact_id: "fake-artifact", executor_sessions: ["fake-session"] })
      : Reflect.get(t, k); },
  });
  R("P-5b frozen-v0.10.0 tighter-check",
    !(exactProto === false && proxied instanceof ObservedExecutionHost),
    `Object.getPrototypeOf(evil) === ObservedExecutionHost.prototype is ${exactProto}, so a prototype ` +
    `check WOULD exclude the subclass — and a Proxy over a genuine host is still ` +
    `${proxied instanceof ObservedExecutionHost} and still answers observationOf however it likes. ` +
    `Tightening the predicate is P-4's mistake with a longer expression: the question is not what the ` +
    `object IS, it is WHO BUILT IT`);
}

/* ── live: the authority takes CATALOG DATA and builds the host itself ───── */
{
  const auth = new DerivationAuthority(mkWorld(), [P], CATALOG);
  const { request: req } = auth.authorize({ intent_id: "l1", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const run = await auth.execute(req);
  const acc = auth.accept(req, run.result);
  R("live: host-is-built-from-data",
    run.ok && acc.ok && acc.implementation_provenance === "observed"
      && acc.implementation_id === JS_IMPLEMENTATION_ID
      && DerivationAuthority.length === 1,
    `the third constructor argument is a CATALOG, not a host: the authority calls ` +
    `new ObservedExecutionHost(catalog) against this module's own class binding, which no caller can ` +
    `substitute. A real execution still reports provenance ${acc.implementation_provenance} for ` +
    `${acc.implementation_id}`);
}

/* ── live: an object is not a catalog, however host-shaped it is ─────────── */
{
  const evil = new EvilHost(CATALOG);
  const asHost = (() => { try { new DerivationAuthority(mkWorld(), [P], evil); return "ACCEPTED"; }
    catch (e) { return e.message; } })();
  const asRealHost = (() => { try {
    new DerivationAuthority(mkWorld(), [P], new ObservedExecutionHost(CATALOG)); return "ACCEPTED"; }
    catch (e) { return e.message; } })();
  // A Proxy in the CATALOG position is accepted, and that is correct rather
  // than a hole: a catalog is DATA, read once, validated and copied into a
  // frozen map. Answering get() differently afterwards reaches nothing. The
  // check is therefore not "is it a Proxy" but "does changing it later matter".
  const live = { [JS_IMPLEMENTATION_ID]: { ...JS_WORKER_ENTRY } };
  const authFromMutable = new DerivationAuthority(mkWorld(), [P], live);
  live[JS_IMPLEMENTATION_ID].entrypoint = join(HERE, "grid_check.mjs");
  live["impl-c-smuggled-v1"] = JS_WORKER_ENTRY;
  const stillOne = (await authFromMutable.execute(authFromMutable.authorize({ intent_id: "l2b",
    program_sem_id: PID, canonical_inputs: { bias: 0 },
    requested_resources: { exact: ["fb"], predicates: [] } }).request));
  R("live: a-host-is-not-a-catalog",
    /^host-catalog-/.test(asHost) && /^host-catalog-/.test(asRealHost)
      && stillOne.ok && stillOne.result.semantic_result.value === 5,
    `passing the EvilHost is ${asHost} and passing a GENUINE ObservedExecutionHost is ${asRealHost} — ` +
    `neither is a catalog, and the authority no longer has a parameter that takes one. Editing the ` +
    `caller's catalog object AFTER construction reaches nothing: entries are read, validated and ` +
    `copied into a frozen map, so the authority still ran the real worker and got ` +
    `${stillOne.result?.semantic_result?.value}`);
}

/* ── live: overriding the class cannot reach the authority's host ────────── */
{
  const auth = new DerivationAuthority(mkWorld(), [P], CATALOG);
  const { request: req } = auth.authorize({ intent_id: "l3", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const honest = (await auth.execute(req)).result;
  // the observation lives behind a #private field on an object the caller has
  // never held a reference to, and the class itself is frozen
  const reachable = Object.getOwnPropertyNames(auth).length === 0 && Object.isFrozen(auth)
    && Object.isFrozen(ObservedExecutionHost) && Object.isFrozen(ObservedExecutionHost.prototype);
  const acc = auth.accept(req, honest);
  R("live: host-is-unreachable",
    reachable && acc.implementation_provenance === "observed",
    `the authority exposes ${Object.getOwnPropertyNames(auth).length} own properties and is frozen; ` +
    `the host is a #private field the caller never receives, and both the class and its prototype are ` +
    `frozen. There is no reference to swap and no method to shadow`);
}

/* ── live: the five rungs, checked as a set ──────────────────────────────── */
{
  const auth = new DerivationAuthority(mkWorld(), [P], CATALOG);
  R("live: five-rung-ladder-empty",
    typeof auth.registerExecutor === "undefined" && typeof auth.nameArtifact === "undefined"
      && DerivationAuthority.prototype.accept.length === 2
      && DerivationAuthority.prototype.execute.length === 1
      && DerivationAuthority.length === 1,
    `no label parameter, no naming setter, no launcher argument, no registry argument, and the third ` +
    `constructor slot is DATA rather than an authority-bearing object. DerivationAuthority.length is ` +
    `${DerivationAuthority.length} because reader is the only required one. What a caller supplies is ` +
    `an INTENT and a RESULT TO VALIDATE — and, at construction, the DATA every oracle is built from`);
}

console.log("=".repeat(100));
const frozen = results.filter((r) => r.id.includes("frozen"));
const live = results.filter((r) => r.id.startsWith("live:"));
const frozenHeld = frozen.filter((r) => r.held);
const liveBreached = live.filter((r) => !r.held);
console.log(
  `HOST-OWN v0.11 REPRO: ${frozen.length - frozenHeld.length}/${frozen.length} reproduce against the ` +
  `frozen v0.10.0 · ${live.length - liveBreached.length}/${live.length} confined against live` +
  (frozenHeld.length ? ` — VACUOUS: ${frozenHeld.map((r) => r.id).join(", ")}` : "") +
  (liveBreached.length ? ` — REGRESSION: ${liveBreached.map((r) => r.id).join(", ")}` : ""));
process.exit(frozenHeld.length + liveBreached.length ? 1 : 0);
