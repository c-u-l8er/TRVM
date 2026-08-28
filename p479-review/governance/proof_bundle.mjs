/* ═══════════════════════════════════════════════════════════════════════════
   proof_bundle.mjs — v0.1.0 — THE FIRST BOUNDED PROOF-PRODUCING WORKLOAD
   law:proof.bounded-claim@1

   Everything from B1 to B8.3 built a chain that can carry ONE program from a
   source AST to a native execution and back to a decoded number, with an
   identity at each joint. This is the first artifact that uses the chain to
   say something that is not about the chain:

       x * (y + z)  =  (x * y) + (x * z)      for x, y, z ∈ {0,1,2,3}

   READ THE SCOPE BEFORE THE VERDICT. This is a BOUNDED EXHAUSTIVE
   VERIFICATION over sixty-four assignments. It is NOT a proof of
   distributivity over the naturals, it is not an induction, and nothing in it
   generalises past 3. The interesting object is the EVIDENCE BUNDLE — an
   artifact a checker that trusts none of this file can accept or refuse — and
   distributivity is the smallest proposition that exercises the whole chain
   while producing one.

   WHY THIS PROPOSITION. It reaches every part of the machine at once:
   input PORTS (three of them, closed per case) · `add` · `mul` · a NESTED
   structure on each side · numerals large enough to need B8.1's widened
   decoder (3*(3+3) = 18, whose canonical signature is §5-compacted) · emission
   · native DUP-plane execution · readback across allocator classes · decode ·
   equality. And it does that WITHOUT `sub`, so the partial codomain and its
   refusals stay out of the first artifact.

   THE TWO SIDES ARE DIFFERENT PROGRAMS. That is the content: LHS is one `mul`
   over an `add`, RHS is two `mul`s under an `add`, so they lower to different
   templates, emit to different bytes and reach different target terms. What
   they must share is the DECODED OUTCOME. A bundle in which the two sides had
   the same target_term_sem_id would be asserting nothing.

   WHAT IS CASE-INDEPENDENT, AND IT IS WORTH SAYING: the program, its lowering
   and its target template are the SAME on all sixty-four cases, because the
   variables are input PORTS and the ports are closed at instantiation. Only
   instantiation onward varies. Each CaseEvidence carries the full chain anyway
   — a checker should not have to know which fields happen to be constant to
   verify one case — and the aggregate reports the constancy as a measurement.

   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { ObservedExecutionHost } from "./observed_execution_host.mjs";
import { canonicalBytes, evaluate } from "./derive_protocol.mjs";
import { parse, extrude, FloatRt, semStateId, semStateSignature, runFloat, readback }
  from "./trvm_law_kernel.mjs";
import {
  lower, loweringReceipt, instantiate, instantiationReceipt, emit, emissionReceipt,
  closedTemplateSemId, outcomeSemId, programSemId, makeTargetDecoder,
  templatePorts,
  LOWERING_SEM_ID, INSTANTIATION_SEM_ID, EMISSION_SEM_ID, EMISSION_RULES_SEM_ID,
  TARGET_TEMPLATE_ENCODING_SEM_ID, TARGET_EXECUTABLE_ENCODING_SEM_ID, DECODE_SEM_ID,
  CANONICAL_EMITTER_PROFILE_ID, CANONICAL_EMITTER_ARTIFACT_ID, LOWERING_VERSION,
} from "./lowering.mjs";

export const PROOF_BUNDLE_VERSION = "0.1.0";
export const PROOF_PROTOCOL = "TRVM-BOUNDED-PROOF-v1";
const H = (s) => createHash("sha256").update(s).digest("hex");

const HERE = dirname(fileURLToPath(import.meta.url));
const FILM = join(HERE, "bridge", "ic32_film");
const C_FILM = "impl-c-ic32-film";

/* ── THE PROPOSITION, AS DATA ──────────────────────────────────────────────
   Both sides are source ASTs over input ports, so the checker rebuilds them
   from THIS record rather than from a copy of the generator. */
/* THE PROPOSITION IS TWO ASTs AND THE VARIABLES THEY RANGE OVER. IT IS NOT A
   SENTENCE — P3.1's finding, and the sentence used to be in here, hashed.

       claim.proposition.statement := "P = NP, ESTABLISHED BY EXHAUSTIVE
                                       VERIFICATION"
       recompute proposition_sem_id, recompute bounded_claim_sem_id
       →  PROOF-CHECK: PASS — BOUNDED CLAIM VERIFIED. P = NP, ESTABLISHED BY
          EXHAUSTIVE VERIFICATION over x∈{0,1,2,3} × …

   The mathematics stayed exactly what it was: the ASTs did not move, all 128
   chains re-derived, all 128 films replayed. What moved was the NAME OF THE
   THEOREM, and the checker printed the producer's sentence as the thing it had
   established. Hashing the sentence made that worse rather than better — the
   identity moved, the artifact was self-consistent, and no check existed to
   disagree with it.

   So the statement is not semantic. It is rendered by whoever is reading, FROM
   THE AST THAT WAS CHECKED — `renderAst` in proof_check.mjs — and the
   generator's own wording lives in `annotations`, where it establishes
   nothing. */
const IN = (name) => ({ op: "input", name });
export const PROPOSITION = Object.freeze({
  variables: Object.freeze(["x", "y", "z"]),
  lhs: Object.freeze({ op: "mul", a: IN("x"), b: { op: "add", a: IN("y"), b: IN("z") } }),
  rhs: Object.freeze({ op: "add", a: { op: "mul", a: IN("x"), b: IN("y") },
                                  b: { op: "mul", a: IN("x"), b: IN("z") } }),
});
export const propositionSemId = (p) => "prop-" + H(PROOF_PROTOCOL + "|" + canonicalBytes(p));

/* ── THE DOMAIN, AS DATA, AND THE PRODUCT IS DERIVED FROM IT ───────────────
   The checker computes the Cartesian product itself and requires exact set
   equality against the cases. `expected_cases` is written here so that a
   bundle claiming a different count is REFUSED rather than believed — a
   claimed total is exactly the thing an aggregate must not be trusted about. */
export const VARIABLE_DOMAINS = Object.freeze({
  x: Object.freeze([0, 1, 2, 3]),
  y: Object.freeze([0, 1, 2, 3]),
  z: Object.freeze([0, 1, 2, 3]),
});
export const domainSemId = (d) => "dom-" + H(PROOF_PROTOCOL + "|" + canonicalBytes(d));

/* ── THE SCOPE, STRUCTURAL ─────────────────────────────────────────────────
   P1 shipped this as prose — a `kind` sentence, an `established` paragraph and
   a `not_claimed` list — and `proof_check.mjs` did not read any of it.
   Reproduced: `delete bundle.claim.scope` and rewriting it to
   `{kind:"UNBOUNDED PROOF", established:"proof over all naturals"}` BOTH left
   checkBundle at ok:true with zero refusals. The checker derived a bounded
   finite product correctly and the artifact could carry a contradictory claim
   beside the evidence.

   THE RULE, and it is B6.3's applied to a proof artifact: A HASHED FIELD IS A
   VALUE THE CODE READS, OR IT IS NOT HASHED — and here the same rule in its
   other direction, THE MACHINE-READABLE SCOPE MUST BE THE SCOPE THE CHECKER
   ACTUALLY CHECKS. So boundedness is three machine-readable values, none of
   them prose, none of them containing a space:

       kind                       what sort of claim this is
       quantifier                 over WHAT the claim ranges
       generalizes_beyond_domain  and explicitly that it does not

   The English warning stays, unhashed and rewordable, in
   BOUNDED_CLAIM_SCOPE_NOTES — hashing a warning would make the artifact's
   identity move when somebody improves the wording, which is B1.1's defect
   with explanatory prose in a hashed seat. */
export const BOUNDED_CLAIM_SCOPE = Object.freeze({
  kind: "BOUNDED_EXHAUSTIVE_VERIFICATION",
  quantifier: "FOR_ALL_ASSIGNMENTS_IN_DECLARED_DOMAINS",
  generalizes_beyond_domain: false,
});

/** NON-AUTHORITATIVE. Lives in `annotations`, outside every identity and every
 *  semantic record — P3.1's envelope. Rewording it costs nothing and
 *  establishes nothing. */
export const BOUNDED_CLAIM_SCOPE_NOTES = Object.freeze({
  established: "on each assignment in the declared domains the two source programs compile to ic32 " +
    "terms which the native runtime reduces to normal forms decoding to the SAME value, with every " +
    "step of both chains identified and every receipt independently reproducible.",
  not_claimed: Object.freeze([
    "NOT a proof of distributivity over the naturals",
    "NOT an induction, and nothing here generalises past 3",
    "not distributivity for any assignment outside the declared domains",
    "not that the compiler is correct for programs unlike these two",
    "nothing about `sub` or the partial codomain — deliberately excluded so the first artifact " +
      "carries no refusals",
    "not that the source evaluator and the target agree in general; 64 agreements are 64 agreements",
  ]),
});

/** THE BOUNDED CLAIM'S OWN IDENTITY — proposition, domain and the QUANTIFIER
 *  SEMANTICS in one place, so the three stop being adjacent unauthenticated
 *  pieces. What it identifies is WHAT THIS EVIDENCE PURPORTS TO ESTABLISH; the
 *  checker still derives the domain and the cases rather than trusting it. The
 *  hash says what the claim is, the checker says whether it holds. */
export const boundedClaimSemId = (proposition_sem_id, domain_sem_id, scope) =>
  "bclaim-" + H(PROOF_PROTOCOL + "|" + canonicalBytes({
    protocol: PROOF_PROTOCOL, proposition_sem_id, domain_sem_id, scope }));

/** The product, in a DECLARED canonical order: variables in the order the
 *  proposition lists them, each cycling its own domain, last variable fastest.
 *  Written once and exported so the generator and the checker cannot drift
 *  into two different enumerations of "the same" domain — but the checker
 *  still derives its own and compares as a SET, so agreeing about the order is
 *  not what makes them agree. */
export function cartesian(variables, domains) {
  let out = [{}];
  for (const v of variables) {
    const next = [];
    for (const partial of out) for (const val of domains[v]) next.push({ ...partial, [v]: val });
    out = next;
  }
  return out;
}
export const assignmentSemId = (a) => "asgn-" + H(PROOF_PROTOCOL + "|" + canonicalBytes(a));

/** A CaseEvidence's own id, over its content MINUS the id field AND MINUS each
 *  side's execution provenance.
 *
 *  THE EXCLUSION IS THE POINT, and it is B6.1's ruling one artifact over: exact
 *  emitted bytes are PROVENANCE and sit beside executable_artifact_id rather
 *  than inside a semantic identity. `executor_session_id` names a LAUNCH, so
 *  folding it in would make the same evidence, produced twice, carry two ids —
 *  an identity that moves because somebody ran the producer again, which is
 *  over-binding of exactly the species B1.2.1 recorded.
 *
 *  WHAT THAT IS NOT: the reason first written here was that a session id
 *  "differs every run", and the check written to confirm it MEASURED IT FALSE.
 *  The host's session counter is per-instance and resets with the process, so
 *  two generations produce identical session ids. What a session id actually
 *  distinguishes is two LAUNCHES — proof_forgeries.mjs runs the same binary
 *  twice on the same input and gets byte-identical evidence, the same
 *  executable_artifact_id, the same input_canonical and a different session id,
 *  with caseEvidenceId blind to the difference. The exclusion is right; the
 *  first reason for it was not. */
export function caseEvidenceId(ev) {
  const { case_evidence_id, ...rest } = ev;
  const strip = (side) => {
    if (!side || typeof side !== "object") return side;
    const { execution_provenance, ...s } = side;
    return s;
  };
  return "case-" + H(PROOF_PROTOCOL + "|" + canonicalBytes(
    { ...rest, lhs: strip(rest.lhs), rhs: strip(rest.rhs) }));
}

/** THE CASE-SET COMMITMENT. Sorted so it is order-independent, and NOT
 *  deduplicated, so sixty-three unique assignments plus one repeat does not
 *  hash the same as sixty-four unique ones. `distinct` is reported beside it
 *  because a commitment cannot say by itself that its members are distinct. */
export function caseSetCommitment(assignmentIds) {
  return "cset-" + H(PROOF_PROTOCOL + "|" + [...assignmentIds].sort().join("|"));
}

export function aggregateId(agg) {
  const { aggregate_id, ...rest } = agg;
  return "agg-" + H(PROOF_PROTOCOL + "|" + canonicalBytes(rest));
}

/* ── THE CHAIN IDS THE BUNDLE IS EVIDENCE UNDER ────────────────────────────
   A proof bundle produced by one compiler and checked against another is
   evidence about neither. Every relation identity the chain passes through is
   recorded, and the checker requires each to equal the live module's. */
export function chainIds() {
  return {
    lowering_sem_id: LOWERING_SEM_ID,
    instantiation_sem_id: INSTANTIATION_SEM_ID,
    emission_sem_id: EMISSION_SEM_ID,
    emission_rules_sem_id: EMISSION_RULES_SEM_ID,
    target_template_encoding_sem_id: TARGET_TEMPLATE_ENCODING_SEM_ID,
    target_executable_encoding_sem_id: TARGET_EXECUTABLE_ENCODING_SEM_ID,
    decode_sem_id: DECODE_SEM_ID,
    canonical_emitter_profile_id: CANONICAL_EMITTER_PROFILE_ID,
    canonical_emitter_artifact_id: CANONICAL_EMITTER_ARTIFACT_ID,
    lowering_version: LOWERING_VERSION,
  };
}

/* ── BUILDING ONE SIDE OF ONE CASE ─────────────────────────────────────────
   The whole chain, with the receipt each relation mints for itself. The
   identity oracle is BOUND (B8.3): this generator does not get to nominate
   the judge of its own output any more than a caller does. */
const identifyNf = (own) => semStateId(new FloatRt(), own);
const decodeTarget = makeTargetDecoder({ identifyNormalForm: identifyNf });
const kernelSemId = (term) => { const frt = new FloatRt(); return semStateId(frt, extrude(frt, parse(frt, term))); };
const ownedNf = (bytes) => { const o = runFloat(bytes); return readback(o.frt, o.root).nf; };

export async function buildSide(host, ast, low, inputs) {
  const program_sem_id = programSemId(ast);
  if (!low.ok) return { ok: false, reason: "lower-refused:" + low.reason };
  const inst = instantiate(low.template, inputs);
  if (!inst.ok) return { ok: false, reason: "instantiate-refused:" + inst.reason };
  let bytes;
  try { bytes = emit(inst.closed_template); }
  catch (e) { return { ok: false, reason: "emit-refused:" + String(e.message ?? e) }; }
  const closed_template_sem_id = closedTemplateSemId(inst.closed_template);
  const target_term_sem_id = kernelSemId(bytes);
  const f = await host.run(C_FILM, "TRVM-FILM-EXEC-v1", { argv: [bytes] });
  const film = f.ok && f.output?.ok ? f.output.film : null;
  if (!film) return { ok: false, reason: "film-refused" };
  /* THREE DIFFERENT CLAIMS, AND P1 CONFLATED TWO OF THEM IN ONE ADJECTIVE.
     "native film" was doing double duty: the host really does launch the C
     binary, and the host really does return executable_artifact_id,
     executor_session_id and input_canonical — and buildSide DISCARDED all
     three. So what the bundle established was

         PROOF VALIDITY        this film replays and the theorem checks
                               (established, and it is what gov-proof gates)

     and what it did NOT establish, while the word "native-originated" implied
     it, was

         PRODUCER PROVENANCE   this film was observed from artifact X in
                               session Y   (recorded here, from B8.3+ on)
         NATIVE REPRODUCIBILITY  today's artifact X can rerun and reproduce it
                               (NOT established, and a rerun today could not
                               establish the historical origin anyway — it
                               would establish reproducibility by the current
                               artifact, which is a third thing)

     Recorded BESIDE the evidence and outside its identity. The proof verdict
     does not depend on any of it. */
  const execution_provenance = {
    implementation_family_id: C_FILM,
    executable_artifact_id: f.executable_artifact_id ?? null,
    executor_session_id: f.executor_session_id ?? null,
    input_canonical: f.input_canonical ?? null,
  };
  const own = ownedNf(bytes);
  const dec = decodeTarget(own);
  if (!dec.ok) return { ok: false, reason: "decode-refused:" + dec.reason };
  return {
    ok: true,
    program_sem_id,
    lowering_receipt: loweringReceipt(program_sem_id, low.target_template_sem_id),
    // instantiate() mints inputs_sem_id over its OWN snapshot of the inputs
    // (B2.1's entry-snapshot repair), so the receipt takes that id rather than
    // recomputing one from the caller's object — recomputing here would be the
    // read-it-twice defect the snapshot exists to close.
    instantiation_receipt: instantiationReceipt(
      low.target_template_sem_id, inst.inputs_sem_id, closed_template_sem_id),
    closed_template_sem_id,
    // MEASURED AND IT CAUGHT ME: this field did not exist in the first draft,
    // only inside the emission receipt, so the aggregate's
    // `cases_with_distinct_target_terms` compared undefined to undefined and
    // reported 0/64. It failed in the UNFLATTERING direction, which is the only
    // reason it was visible — the same comparison written `===` would have
    // reported 64/64 agreement over a field neither side had.
    target_term_sem_id,
    emission_receipt: emissionReceipt(closed_template_sem_id, target_term_sem_id),
    // PROVENANCE, beside the identity and not inside it — B6.1's ruling that a
    // receipt carrying no byte digest must not claim these exact bytes.
    target_term_bytes: bytes,
    film,
    target_nf_sem_id: dec.target_nf_sem_id,
    target_nf_signature_compacted: semStateSignature(new FloatRt(), dec.owned).includes("#"),
    execution_provenance,
    outcome: dec.outcome,
    outcome_sem_id: outcomeSemId(dec.outcome),
  };
}

/** The producer host, exported so the forgery suite can launch the binary twice
 *  itself and measure what an executor_session_id actually distinguishes. */
export function newProducerHost() {
  if (!existsSync(FILM)) throw new Error("proof-bundle-requires-ic32_film");
  return new ObservedExecutionHost({
    [C_FILM]: { kind: "native-exec", entrypoint: FILM, artifact_closure: [FILM] },
  });
}

export async function buildBundle() {
  const host = newProducerHost();
  const lowL = lower(PROPOSITION.lhs), lowR = lower(PROPOSITION.rhs);
  const assignments = cartesian(PROPOSITION.variables, VARIABLE_DOMAINS);
  const cases = [];
  for (let i = 0; i < assignments.length; i++) {
    const a = assignments[i];
    const lhs = await buildSide(host, PROPOSITION.lhs, lowL, a);
    const rhs = await buildSide(host, PROPOSITION.rhs, lowR, a);
    // THE SOURCE EVALUATOR IS A THIRD OPINION, not the referee. It answers in
    // IEEE-754 doubles over the source language; the two target chains answer
    // by executing ic32. The bundle records all three and the checker requires
    // them to agree, which is one more independent way for a wrong case to be
    // caught than the equality alone would give.
    const srcL = evaluate(PROPOSITION.lhs, { exact: {}, predicates: {} }, a).value;
    const srcR = evaluate(PROPOSITION.rhs, { exact: {}, predicates: {} }, a).value;
    const ev = {
      case_index: i,
      assignment: a,
      assignment_sem_id: assignmentSemId(a),
      source_value: srcL,
      source_sides_agree: srcL === srcR,
      lhs, rhs,
      equality: {
        outcome_sem_id_equal: lhs.ok && rhs.ok && lhs.outcome_sem_id === rhs.outcome_sem_id,
        // FAIL-CLOSED: both must be present AND different. `!==` over two
        // absent fields is true, and a measurement that reads an absent field
        // as a difference is worse than one that reads it as a match.
        target_terms_differ: lhs.ok && rhs.ok
          && typeof lhs.target_term_sem_id === "string" && typeof rhs.target_term_sem_id === "string"
          && lhs.target_term_sem_id !== rhs.target_term_sem_id,
        closed_templates_differ: lhs.ok && rhs.ok
          && typeof lhs.closed_template_sem_id === "string"
          && typeof rhs.closed_template_sem_id === "string"
          && lhs.closed_template_sem_id !== rhs.closed_template_sem_id,
        witness: lhs.ok && rhs.ok && lhs.outcome_sem_id === rhs.outcome_sem_id
          ? lhs.outcome_sem_id : null,
        source_agrees: lhs.ok && srcL === lhs.outcome?.value,
      },
      case_evidence_id: null,
    };
    ev.case_evidence_id = caseEvidenceId(ev);
    cases.push(ev);
  }
  const failed = cases.filter((c) => !(c.lhs.ok && c.rhs.ok && c.equality.outcome_sem_id_equal
    && c.equality.source_agrees && c.source_sides_agree)).length;
  const assignmentIds = cases.map((c) => c.assignment_sem_id);
  const aggregate = {
    case_set_commitment: caseSetCommitment(assignmentIds),
    case_evidence_ids: cases.map((c) => c.case_evidence_id),
    completed: cases.length,
    distinct_assignments: new Set(assignmentIds).size,
    missing: assignments.length - new Set(assignmentIds).size,
    failed,
    // MEASURED, not assumed: how many cases have genuinely different target
    // terms on the two sides. A bundle where they coincided would be asserting
    // that a program equals itself.
    cases_with_distinct_target_terms: cases.filter((c) => c.equality.target_terms_differ).length,
    cases_with_distinct_closed_templates: cases.filter((c) => c.equality.closed_templates_differ).length,
    cases_past_the_signature_ceiling:
      cases.filter((c) => c.lhs.ok && c.lhs.target_nf_signature_compacted).length,
    // and the case-INDEPENDENCE of the front of the chain, as a fact rather
    // than a comment: ports are closed at instantiation, so program, lowering
    // and template are one value across all sixty-four.
    distinct_lhs_program_sem_ids: new Set(cases.map((c) => c.lhs.program_sem_id)).size,
    distinct_lhs_target_template_sem_ids:
      new Set(cases.map((c) => c.lhs.lowering_receipt?.target_template_sem_id)).size,
    distinct_lhs_target_term_sem_ids:
      new Set(cases.map((c) => c.lhs.emission_receipt?.target_term_sem_id)).size,
    bounded_claim_verdict: failed === 0 && cases.length === assignments.length
      && new Set(assignmentIds).size === assignments.length ? "VERIFIED" : "REFUSED",
    aggregate_id: null,
  };
  aggregate.aggregate_id = aggregateId(aggregate);
  return {
    type: "BoundedProofBundle",
    protocol: PROOF_PROTOCOL,
    version: PROOF_BUNDLE_VERSION,
    claim: {
      proposition: PROPOSITION,
      proposition_sem_id: propositionSemId(PROPOSITION),
      variable_domains: VARIABLE_DOMAINS,
      domain_sem_id: domainSemId(VARIABLE_DOMAINS),
      expected_cases: assignments.length,
      scope: BOUNDED_CLAIM_SCOPE,
      bounded_claim_sem_id: boundedClaimSemId(
        propositionSemId(PROPOSITION), domainSemId(VARIABLE_DOMAINS), BOUNDED_CLAIM_SCOPE),
      /* OPTIONAL, CLAIM-SPECIFIC, AND NOT A VALIDITY CONDITION. P1 refused any
         case whose two sides reached the same target term, on the theory that
         such a case "asserts nothing". GPT overruled it and is right: if a
         future canonicalisation collapses two distinct source programs at one
         assignment, that assignment still legitimately proves the equality —
         it just makes that case easy. A TRIVIAL THEOREM IS STILL A VALID
         THEOREM, and "is this workload interesting?" is generator policy, not
         logical validity.
         So it moves here: THIS artifact additionally claims that all its sides
         compile to distinct target terms, the checker verifies that claim
         because the artifact makes it, and a bundle that did not make it would
         still be valid. */
      declared_properties: { all_sides_distinct_target_terms: true },
    },
    chain_ids: chainIds(),
    port_names: { lhs: templatePorts(lowL.template), rhs: templatePorts(lowR.template) },
    cases,
    aggregate,
    /* THE SECOND TRUST DOMAIN. Everything above is machine semantics under an
       exact grammar the checker owns; everything here is prose, is reachable by
       no identity, is checked only for SHAPE, and establishes nothing. The
       checker must never interpolate any of it into a sentence describing what
       it verified — which is exactly what P3.1 found it doing with
       `proposition.statement`. */
    annotations: {
      note: "NON-AUTHORITATIVE — nothing in this record is hashed, checked, or established",
      generator: "proof_bundle.mjs v" + PROOF_BUNDLE_VERSION,
      statement: "x * (y + z) = (x * y) + (x * z)",
      scope_notes: BOUNDED_CLAIM_SCOPE_NOTES,
    },
  };
}

const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN) {
  const bundle = await buildBundle();
  const out = join(HERE, "proof_bundle.json");
  writeFileSync(out, JSON.stringify(bundle, null, 1) + "\n");
  const a = bundle.aggregate;
  console.log(`proof_bundle v${PROOF_BUNDLE_VERSION} — ${bundle.annotations.statement} ` +
    `(the GENERATOR's wording, non-authoritative; proof_check renders its own from the AST)`);
  console.log(`  ${a.completed} cases, ${a.distinct_assignments} distinct, ${a.missing} missing, ` +
    `${a.failed} failed → ${a.bounded_claim_verdict}`);
  console.log(`  ${a.cases_with_distinct_target_terms}/${a.completed} cases where the two sides ` +
    `reach DIFFERENT target terms; ${a.cases_past_the_signature_ceiling} past §5's signature ceiling`);
  console.log(`  aggregate ${a.aggregate_id}`);
  console.log(`  written to ${out}`);
}
