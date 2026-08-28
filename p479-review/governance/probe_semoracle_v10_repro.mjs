/* ═══════════════════════════════════════════════════════════════════════════
   probe_semoracle_v10_repro.mjs — acceptance took its semantic oracle from the
   claimant.

   By v0.9.0 the authority owned issuance, the World reader, execution
   observations and freshness. It did not own the thing that says what a
   `program_sem_id` MEANS.

       accept(registry, req, res)
                ^^^^^^^^
                supplied by the caller, every time

   P-4  AN AUTHORITY CANNOT VALIDATE A SEMANTIC CLAIM USING A PROGRAM RESOLVER
        SUPPLIED BY THE CLAIMANT.

            issue an ordinary request for  { op: "const", value: 5 }

            const fakeRegistry = {
              verify(id) { return { ok: true }; },        ← blesses the issued id
              get(id)    { return { op: "const", value: 999 }; }
            };

            deriveLocally(fakeRegistry, issuedRequest)
              → value 999, under the issued program_sem_id for const(5)

            authority.accept(fakeRegistry, issuedRequest, thatResult)
              → { ok: true, validated: true, fresh_at_check: true,
                  implementation_provenance: "unavailable" }

            authority.accept(realRegistry, issuedRequest, thatResult)
              → { ok: false, reason: "foreign-result-divergence" }

        Re-derivation was doing its job perfectly. It re-derived against the
        program the CLAIMANT nominated, agreed with itself, and reported
        agreement. Provenance being "unavailable" does not save it: a request
        that states no `expected_implementation_id` is allowed to accept a
        semantically validated result with no observed execution, which is the
        in-process path and is correct on its own terms.

   THE SUPPLIER LADDER, four rungs and one shape:

       @1  the caller supplied the implementation LABEL
       @2  the caller supplied the registration NAME
       @3  the caller supplied the ACTION beside the artifact evidence
       @4  the caller supplied the SEMANTIC ORACLE used at acceptance

   Round 24's own generalisation — any field a caller controls on the launch
   path becomes the provenance — has an exact twin on the semantic side.
   Acceptance takes no proof from its caller, INCLUDING the mapping from
   semantic identity to semantic program.

   An `instanceof ProgramRegistry` check would not have closed it. A Proxy, or a
   real registry the caller populated differently, leaves the ownership wrong
   while satisfying the type. The repair is ownership: the registry is built at
   the authority's construction from canonical program data, and no registry
   parameter crosses `execute` or `accept` again.

   PAIRED, and it gates.
   ═══════════════════════════════════════════════════════════════════════════ */
import {
  ProgramRegistry, DerivationAuthority, deriveLocally, validateForeignResult,
  validateFootprintFresh, programSemId,
} from "./derive_protocol.mjs";

const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "CONFINED" : "BREACH  "}  ${id.padEnd(30)} ${note}`); };

const mkWorld = () => ({ res: { fb: { value: 5, version: 1 } },
  read(r) { return { ...this.res[r] }; }, scope(q) { return "scope:" + q; } });
const HONEST = { op: "const", value: 5 };
const EVIL = { op: "const", value: 999 };

/* ── v0.9.0's acceptance, VERBATIM in its essentials ──────────────────────
   A FROZEN COPY. The registry arrives as a parameter and every semantic check
   below it resolves through that parameter. It is wrong on purpose and must
   stay wrong. */
function v9Accept(authority, registry, req, res) {
  const iss = authority.wasIssued(req);
  if (!iss.ok) return { ok: false, reason: iss.reason };
  const v = validateForeignResult(registry, req, res);   // ← the claimant's oracle
  if (!v.ok) return v;
  return { ok: true, validated: true, fresh_at_check: true,
    implementation_provenance: "unavailable" };
}

/* ── P-4 against the frozen v0.9.0 ───────────────────────────────────────── */
{
  const real = new ProgramRegistry();
  const PID = real.bind(HONEST);
  const auth = new DerivationAuthority(mkWorld(), [HONEST]);
  const { request: req } = auth.authorize({ intent_id: "p4", program_sem_id: PID,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } });

  // an object shaped like a registry, whose verify() blesses the ISSUED id and
  // whose get() resolves it to a different program
  const fake = { verify: () => ({ ok: true }), get: () => EVIL };
  const forged = deriveLocally(fake, req).result;
  const withFake = v9Accept(auth, fake, req, forged);
  const withReal = v9Accept(auth, real, req, forged);

  R("P-4 frozen-v0.9.0",
    !(withFake.ok && forged.semantic_result.value === 999 && !withReal.ok),
    `an issued request for const(5) accepted as ${forged.semantic_result.value} — accept(fake) -> ` +
    `ok=${withFake.ok}, and accept(real) on the IDENTICAL result -> ${withReal.reason}. Re-derivation ` +
    `was working perfectly: it re-derived against the program the CLAIMANT nominated, agreed with ` +
    `itself, and reported agreement. The difference between the two lines is entirely who supplied ` +
    `the oracle`);
}

/* ── P-4b: a REAL ProgramRegistry, populated differently ─────────────────── */
{
  const real = new ProgramRegistry();
  const PID = real.bind(HONEST);
  const auth = new DerivationAuthority(mkWorld(), [HONEST]);
  const { request: req } = auth.authorize({ intent_id: "p4b", program_sem_id: PID,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } });
  // no duck typing here: this IS a ProgramRegistry. It simply does not hold the
  // program the request names, and the caller chose which one it holds.
  const other = new ProgramRegistry();
  other.bind(EVIL);
  const acc = v9Accept(auth, other, req, deriveLocally(real, req).result);
  R("P-4b frozen-v0.9.0 real-class",
    !(!acc.ok && acc.reason === "program-unknown"),
    `a genuine ProgramRegistry instance that holds the wrong program yields ${acc.reason} rather than ` +
    `an authority-level refusal. The type was never the question — an instanceof check passes here — ` +
    `and neither is this a hostile object. OWNERSHIP is the question: the caller decided which ` +
    `programs the acceptance-time oracle knew`);
}

/* ── live: no registry crosses execute or accept ─────────────────────────── */
{
  const auth = new DerivationAuthority(mkWorld(), [HONEST]);
  const PID = programSemId(HONEST);
  const { request: req } = auth.authorize({ intent_id: "l1", program_sem_id: PID,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } });
  const fake = { verify: () => ({ ok: true }), get: () => EVIL };
  const forged = deriveLocally(fake, req).result;
  const acc = auth.accept(req, forged, fake);          // a third argument, offered
  const honest = auth.accept(req, deriveLocally(new (class { verify(){return{ok:true};} get(){return HONEST;} })(), req).result);
  R("live: no-registry-parameter",
    !acc.ok && acc.reason === "foreign-result-divergence"
      && DerivationAuthority.prototype.accept.length === 2
      && DerivationAuthority.prototype.execute.length === 1
      && honest.ok && honest.validated === true,
    `accept takes ${DerivationAuthority.prototype.accept.length} parameters (req, res) and execute ` +
    `takes ${DerivationAuthority.prototype.execute.length}; a third argument carrying a fake oracle is ` +
    `inert, and the forged 999 dies as ${acc.reason} against the authority's OWN registry. An honest ` +
    `result produced through any oracle still accepts, because what is being checked is the RESULT`);
}

/* ── live: the authority's registry is built from canonical data it owns ─── */
{
  const auth = new DerivationAuthority(mkWorld(), [HONEST]);
  const ids = auth.programIds();
  const held = auth.programOf(programSemId(HONEST));
  // mutate the array and the AST the caller still holds
  const mine = { op: "const", value: 5 };
  const auth2 = new DerivationAuthority(mkWorld(), [mine]);
  mine.value = 999;
  const after = auth2.programOf(programSemId({ op: "const", value: 5 }));
  R("live: registry-is-severed-at-construction",
    ids.length === 1 && held.value === 5 && after?.value === 5 && Object.isFrozen(held),
    `the authority holds ${ids.length} program and returns it frozen; editing the AST the caller still ` +
    `holds after construction changes nothing (${after?.value}). ProgramRegistry.bind severs through ` +
    `canonicalBytes, so the authority's semantic oracle is data it owns rather than an object it shares`);
}

/* ── live: binding a NEW program cannot repoint an old id ────────────────── */
{
  const auth = new DerivationAuthority(mkWorld(), [HONEST]);
  const PID = programSemId(HONEST);
  const newId = auth.bindProgram(EVIL);
  const { request: req } = auth.authorize({ intent_id: "l3", program_sem_id: PID,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } });
  const forged = deriveLocally({ verify: () => ({ ok: true }), get: () => EVIL }, req).result;
  const acc = auth.accept(req, forged);
  R("live: binding-cannot-repoint-an-id",
    newId !== PID && !acc.ok && acc.reason === "foreign-result-divergence"
      && auth.programOf(PID).value === 5 && auth.programOf(newId).value === 999,
    `bindProgram is an explicit AUTHORITY operation and it is safe for the reason the id exists: ` +
    `const(999) gets its own id (${newId.slice(0, 14)}…), not const(5)'s. Teaching the authority a new ` +
    `program cannot change what an issued id means, so growing the registry needs no second rule`);
}

/* ── live: the four suppliers are all gone from the same object ──────────── */
{
  const auth = new DerivationAuthority(mkWorld(), [HONEST]);
  const surface = Object.getOwnPropertyNames(DerivationAuthority.prototype)
    .filter((k) => k !== "constructor").sort();
  R("live: the-supplier-ladder-is-empty",
    DerivationAuthority.prototype.accept.length === 2
      && DerivationAuthority.prototype.execute.length === 1
      && typeof auth.registerExecutor === "undefined" && typeof auth.nameArtifact === "undefined"
      && !surface.includes("registerExecutor") && !surface.includes("nameArtifact"),
    `the authority's surface is {${surface.join(", ")}}. @1 the implementation label, @2 the ` +
    `registration name, @3 the action beside the evidence, @4 the semantic oracle — none of the four ` +
    `has a parameter left. What a caller supplies is an INTENT and a RESULT TO VALIDATE`);
}

/* ── live: and the World reader was never a parameter either ─────────────── */
{
  const auth = new DerivationAuthority(mkWorld(), [HONEST]);
  const PID = programSemId(HONEST);
  const { request: req } = auth.authorize({ intent_id: "l5", program_sem_id: PID,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } });
  const res = deriveLocally(new ProgramRegistry(), { ...req });
  const honestRes = (() => { const r = new ProgramRegistry(); r.bind(HONEST);
    return deriveLocally(r, req).result; })();
  const acc = auth.accept(req, honestRes, { read: () => ({ value: 0, version: 99 }), scope: () => "x" });
  R("live: freshness-oracle-is-owned-too",
    acc.ok && acc.fresh_at_check === true && !res.ok,
    `a third argument shaped like a live World reader is inert as well — freshness still runs against ` +
    `the authority's own reader (fresh_at_check ${acc.fresh_at_check}). Round 17 closed that one; this ` +
    `case exists so the four rungs are checked as a set rather than one at a time`);
}

console.log("=".repeat(100));
const frozen = results.filter((r) => r.id.includes("frozen"));
const live = results.filter((r) => r.id.startsWith("live:"));
const frozenHeld = frozen.filter((r) => r.held);
const liveBreached = live.filter((r) => !r.held);
console.log(
  `SEM-ORACLE v0.10 REPRO: ${frozen.length - frozenHeld.length}/${frozen.length} reproduce against the ` +
  `frozen v0.9.0 · ${live.length - liveBreached.length}/${live.length} confined against live` +
  (frozenHeld.length ? ` — VACUOUS: ${frozenHeld.map((r) => r.id).join(", ")}` : "") +
  (liveBreached.length ? ` — REGRESSION: ${liveBreached.map((r) => r.id).join(", ")}` : ""));
process.exit(frozenHeld.length + liveBreached.length ? 1 : 0);
