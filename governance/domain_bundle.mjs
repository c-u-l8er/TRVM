/* ═══════════════════════════════════════════════════════════════════════════
   domain_bundle.mjs — v0.1.0 — P2, THE BOUNDED COMPILER-DOMAIN CERTIFICATE
   law:proof.bounded-claim@1

   P1 proved a positive equality: sixty-four assignments, both sides emitting,
   both sides decoding, outcomes equal. Every case had the same shape and the
   chain ran to the end on every one of them.

   P2's claim is about WHERE THE CHAIN MUST STOP.

       F(x, y) = (x - y) + 2        x, y ∈ {0,1,2,3}

   For every one of the sixteen assignments the SOURCE program is meaningful and
   the source evaluator returns a value. For ten of them the compiler emits, the
   native runtime reaches a normal form, and the decoded outcome equals the
   source. For the other six the compiler REFUSES, by name, and the certificate
   must carry that refusal as evidence — together with the ABSENCE of everything
   downstream of it.

   WHY THIS PROGRAM AND NOT `x - y`. The `+ 2` is the whole point. Consider:

       (0 - 1) + 2   source value 1     REFUSED
       (1 - 3) + 2   source value 0     REFUSED

   Both final values are perfectly representable Church naturals. **Five of the
   six refusals have a representable final source value**, and only `(0-3)+2 =
   -1` does not. So a compiler that decided representability by looking at the
   RESULT would accept five of the six, and B7 measured why that is a
   miscompilation rather than a lenience: raw Church subtraction is monus, so
   the inner underflow silently becomes 0 and `(0-1)+2` would answer 2 against
   the source's 1 — an answer that is itself representable and therefore
   invisible to any check on the output.

   THE CERTIFICATE THEREFORE PROVES A PROPERTY OF THE COMPILER'S DOMAIN, not of
   its answers: representability is a property of the COMPUTATION'S STRUCTURE,
   and the walk that decides it is recursive.

   THE CASE SHAPE IS A SUM TYPE, and that is the proof-system advance:

       CaseEvidence :=
         Emitted { source · lowering · instantiation · emission receipt ·
                   target term · native film · target NF · decoded outcome }
       | Refused { source · lowering · instantiation ·
                   refusal_phase = EMISSION · refusal_code = emit-sub-underflow ·
                   refusal_witness = { minuend, subtrahend } ·
                   and the DECLARED ABSENCE of emission receipt, target term,
                   film, target NF and target outcome }

   A Refused case is not a hole in the evidence. It is evidence, and what it
   asserts includes what is not there — so a checker must refuse a refusal case
   that carries downstream artifacts just as firmly as it refuses an emitting
   case that lacks them.

   AND EVERY FIELD OF THAT RECORD IS MACHINE EVIDENCE — P2.1's repair. The
   phase, the code, the witness and the absent-set are all values the checker
   re-derives. The English moved to `refusal.notes`, which `domainCaseId`
   strips, because P2 hashed two explanatory strings that no check ever read.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { canonicalBytes, evaluate } from "./derive_protocol.mjs";
import { parse, extrude, FloatRt, semStateId, semStateSignature, runFloat, readback }
  from "./trvm_law_kernel.mjs";
import {
  lower, loweringReceipt, instantiate, instantiationReceipt, emit, emissionReceipt,
  closedTemplateSemId, outcomeSemId, programSemId, makeTargetDecoder, templatePorts,
} from "./lowering.mjs";
import { newProducerHost, chainIds, cartesian, caseSetCommitment, aggregateId }
  from "./proof_bundle.mjs";

export const DOMAIN_BUNDLE_VERSION = "0.1.0";
export const DOMAIN_PROTOCOL = "TRVM-BOUNDED-DOMAIN-PROOF-v1";
const H = (s) => createHash("sha256").update(s).digest("hex");
const HERE = dirname(fileURLToPath(import.meta.url));
const C_FILM = "impl-c-ic32-film";

/* THE PROGRAM IS AN AST AND ITS VARIABLES. THE SENTENCE IS NOT PART OF IT —
   P3.1, and this is the attack that made the law obvious:

       claim.program.statement := "THE RIEMANN HYPOTHESIS IS PROVED FOR ALL
                                   NON-TRIVIAL ZEROES"
       (AST untouched, program_sem_id untouched)
       →  DOMAIN-CHECK: PASS — BOUNDED DOMAIN CERTIFICATE VERIFIED. THE RIEMANN
          HYPOTHESIS IS PROVED FOR ALL NON-TRIVIAL ZEROES over x∈{0,1,2,3} × …

   `program_sem_id` identifies the AST, so all sixteen cases still re-derived and
   the mathematics was untouched. What the producer controlled was THE NAME OF
   THE THEOREM, and the checker printed it as its own conclusion. The statement
   is rendered by the checker now, from the AST it checked. */
const IN = (name) => ({ op: "input", name });
export const PROGRAM = Object.freeze({
  variables: Object.freeze(["x", "y"]),
  ast: Object.freeze({ op: "add", a: { op: "sub", a: IN("x"), b: IN("y") },
                                  b: { op: "const", value: 2 } }),
});
export const VARIABLE_DOMAINS = Object.freeze({ x: Object.freeze([0, 1, 2, 3]),
                                                y: Object.freeze([0, 1, 2, 3]) });

/* THE SCOPE, STRUCTURAL — P1.1's shape, with a second machine-readable value
   because this claim is about a PARTITION rather than a single property. The
   English stays unhashed. */
export const DOMAIN_CLAIM_SCOPE = Object.freeze({
  kind: "BOUNDED_EXHAUSTIVE_DOMAIN_CERTIFICATE",
  quantifier: "FOR_ALL_ASSIGNMENTS_IN_DECLARED_DOMAINS",
  generalizes_beyond_domain: false,
  disposition_is_total: true,   // every assignment is EMITTED or REFUSED, never neither
});
export const DOMAIN_CLAIM_SCOPE_NOTES = Object.freeze({
  established: "for every assignment in the declared domains the source program evaluates, and the " +
    "compiler either carries it to a decoded target outcome equal to the source value, or refuses " +
    "it by name at emission with no downstream evidence in existence.",
  not_claimed: Object.freeze([
    "NOT a proof about `sub` outside the declared domains",
    "NOT source-refusal to target-refusal preservation — the SOURCE never refuses here; it " +
      "evaluates every one of the sixteen, and the COMPILER declines six",
    "NOT that emit-sub-underflow is the only refusal the compiler can make",
    "NOT an induction, and nothing here generalises past 3",
  ]),
});
/** THE FIELDS A REFUSED CASE MUST NOT CARRY. Declared as data so the checker
 *  enumerates them rather than remembering them, and so a future branch of the
 *  chain cannot be added without a decision about its absence. */
export const DOWNSTREAM_OF_EMISSION = Object.freeze([
  "emission_receipt", "target_term_sem_id", "target_term_bytes", "film",
  "target_nf_sem_id", "outcome", "outcome_sem_id",
]);

/* ── THE REFUSAL CONTRACT, AND P2.1 EXISTS BECAUSE P2 LET THE CLAIMANT WRITE IT
   ─────────────────────────────────────────────────────────────────────────────
   P2 shipped the absent-list as `claim.downstream_of_emission` and
   `domain_check.mjs` read the enumeration OUT OF THE BUNDLE. So the artifact
   defined what its own negative evidence meant, and the attack is four lines:

       remove "film" from claim.downstream_of_emission
       remove "film" from every REFUSED case's `absent`
       attach a REAL film to one refusal
       reseal case ids and the aggregate     →  checkDomainBundle() ok:true

   REPRODUCED: a case reading `disposition: REFUSED`, `refusal_phase: EMISSION`
   and an eight-frame native film, accepted with ZERO refusals. That directly
   contradicts the theorem the branch exists to state.

   AND `domain_claim_sem_id` DID NOT MOVE. The claim identity bound proposition,
   domain and quantifier semantics — not the absence contract — so the meaning
   of the negative evidence could change while the identity of the bounded claim
   stood still. Under-binding, and it is P1.1's scope defect one layer down: in
   P1.1 the claimant said what SCOPE meant, here the claimant said what ABSENCE
   meant.

   So the contract is DATA, it is bound into the claim's identity, and the
   checker declares its OWN copy and requires exact agreement rather than
   importing this one. A checker that enumerates absence from the bundle proves
   that the bundle agrees with itself. */
export const REFUSAL_CONTRACT = Object.freeze({
  phase: "EMISSION",
  allowed_codes: Object.freeze(["emit-sub-underflow"]),
  downstream_absent: DOWNSTREAM_OF_EMISSION,
});

export const domainClaimSemId = (program_sem_id, domain_sem_id, scope, refusal_contract) =>
  "dclaim-" + H(DOMAIN_PROTOCOL + "|" + canonicalBytes({
    protocol: DOMAIN_PROTOCOL, program_sem_id, domain_sem_id, scope, refusal_contract }));
export const domainSemId2 = (d) => "dom-" + H(DOMAIN_PROTOCOL + "|" + canonicalBytes(d));
export const assignmentSemId2 = (a) => "asgn-" + H(DOMAIN_PROTOCOL + "|" + canonicalBytes(a));

/** THE COMPILER'S REFUSAL DETAIL IS AN ENGLISH STRING — `emit-sub-underflow: 0
 *  - 1` — and P2 hashed it. What is STRUCTURAL inside it is two integers, so
 *  the producer extracts them here and the CHECKER DERIVES THEM ITSELF from its
 *  own evaluator and compares. The English goes to `notes`, unhashed.
 *
 *  Fail-closed on a shape it does not recognise: `null` is not a witness, and a
 *  refusal whose witness is null is refused rather than believed. */
export function underflowWitness(detail) {
  const m = /^(-?\d+)\s*-\s*(-?\d+)$/.exec(String(detail ?? "").trim());
  return m ? { minuend: Number(m[1]), subtrahend: Number(m[2]) } : null;
}

/** Same exclusion as P1.1: execution provenance names a LAUNCH and sits beside
 *  the evidence rather than inside its identity.
 *
 *  AND THE SECOND EXCLUSION IS P2.1's, in the other branch. P2's refused cases
 *  carried `why` and `refusal_detail` — explanatory English — INSIDE this hash
 *  and NOTHING in the checker ever read either one. So the artifact had the
 *  worst pairing available:
 *
 *      reword the prose   →  the proof's identity MOVES
 *      make the prose LIE →  the proof still verifies
 *
 *  Measured: replacing `why` with "THIS PROVES THE SOURCE LANGUAGE REFUSED AND
 *  THE TARGET EXECUTED SUCCESSFULLY" moved case_evidence_id and left
 *  checkDomainBundle at ok:true. That is B1.1's disease inside the first
 *  negative proof object. What replaces it in the hashed seat is
 *  `refusal_witness`, which is two integers the checker re-derives.
 *
 *  P2.1 put the prose in `refusal.notes` — an unhashed seat INSIDE the semantic
 *  record — and P3.1 retired that. An unauthenticated field nested in an
 *  authenticated object is a place for evidence to hide (a real film in
 *  `notes.film` moved no identity at all), and bounding it to strings was a
 *  smaller version of the thing being removed. Prose lives in the bundle's
 *  `annotations`, keyed by `assignment_sem_id`, in the other trust domain
 *  entirely — so `refusal` has no unhashed member left to strip. */
export function domainCaseId(ev) {
  const { case_evidence_id, ...rest } = ev;
  const drop = (o, k) => { if (!o || typeof o !== "object") return o;
    const { [k]: _unhashed, ...r } = o; return r; };
  // A REFUSED case has no `evidence` key at all and an EMITTED one has no
  // `refusal` key. `canonicalBytes` refuses an explicit undefined, which is the
  // right behaviour — a sum type must not be spelled as one record with half
  // its fields absent-but-present. So the branch is REBUILT rather than
  // spread-and-patched.
  const out = { ...rest };
  if ("evidence" in out) out.evidence = drop(out.evidence, "execution_provenance");
  // and NOTHING is stripped from `refusal` any more — it has no unhashed member
  // left to strip, which is P3.1's whole point about mixed seats.
  return "dcase-" + H(DOMAIN_PROTOCOL + "|" + canonicalBytes(out));
}

const identifyNf = (own) => semStateId(new FloatRt(), own);
const decodeTarget = makeTargetDecoder({ identifyNormalForm: identifyNf });
const kernelSemId = (t) => { const frt = new FloatRt(); return semStateId(frt, extrude(frt, parse(frt, t))); };
const ownedNf = (bytes) => { const o = runFloat(bytes); return readback(o.frt, o.root).nf; };

export async function buildCase(host, ast, low, inputs, index) {
  const program_sem_id = programSemId(ast);
  const src = evaluate(ast, { exact: {}, predicates: {} }, inputs);
  const inst = instantiate(low.template, inputs);
  if (!inst.ok) throw new Error("domain-bundle-instantiate-refused: " + inst.reason);
  const closed_template_sem_id = closedTemplateSemId(inst.closed_template);
  const front = {
    program_sem_id,
    lowering_receipt: loweringReceipt(program_sem_id, low.target_template_sem_id),
    instantiation_receipt: instantiationReceipt(
      low.target_template_sem_id, inst.inputs_sem_id, closed_template_sem_id),
    closed_template_sem_id,
  };
  const base = {
    case_index: index,
    assignment: inputs,
    assignment_sem_id: assignmentSemId2(inputs),
    source_value: src.value,
    case_evidence_id: null,
  };

  let bytes = null, refusal = null;
  try { bytes = emit(inst.closed_template); }
  catch (e) {
    const msg = String(e.message ?? e);
    const i = msg.indexOf(":");
    refusal = { code: i < 0 ? msg : msg.slice(0, i).trim(),
                detail: i < 0 ? null : msg.slice(i + 1).trim() };
  }

  if (refusal) {
    /* THE REFUSED BRANCH. The chain that DID complete is carried in full —
       lowering and instantiation both succeeded and their receipts are real
       evidence — and then it STOPS, on purpose, with the stop declared rather
       than left as an absence a reader has to notice.

       EVERYTHING HASHED HERE IS MACHINE EVIDENCE. phase, code, witness and the
       absent-set are all values a checker reads and re-derives; the English sits
       in `notes`, which `domainCaseId` strips. P2 had it the other way round. */
    return { ...base, disposition: "REFUSED",
      refusal: { ...front,
        refusal_phase: REFUSAL_CONTRACT.phase,
        refusal_code: refusal.code,
        // THE STRUCTURAL DETAIL, extracted from the compiler's English by an
        // UNTRUSTED producer and re-derived by the checker's own evaluator. If
        // the message shape changes this is null and the checker refuses.
        refusal_witness: underflowWitness(refusal.detail),
        absent: REFUSAL_CONTRACT.downstream_absent } };
  }

  const target_term_sem_id = kernelSemId(bytes);
  const f = await host.run(C_FILM, "TRVM-FILM-EXEC-v1", { argv: [bytes] });
  const film = f.ok && f.output?.ok ? f.output.film : null;
  if (!film) throw new Error("domain-bundle-film-refused at case " + index);
  const own = ownedNf(bytes);
  const dec = decodeTarget(own);
  if (!dec.ok) throw new Error("domain-bundle-decode-refused: " + dec.reason);
  return { ...base, disposition: "EMITTED",
    evidence: { ...front,
      emission_receipt: emissionReceipt(closed_template_sem_id, target_term_sem_id),
      target_term_sem_id, target_term_bytes: bytes, film,
      target_nf_sem_id: dec.target_nf_sem_id,
      target_nf_signature_compacted: semStateSignature(new FloatRt(), dec.owned).includes("#"),
      outcome: dec.outcome, outcome_sem_id: outcomeSemId(dec.outcome),
      execution_provenance: {
        implementation_family_id: C_FILM,
        executable_artifact_id: f.executable_artifact_id ?? null,
        executor_session_id: f.executor_session_id ?? null,
        input_canonical: f.input_canonical ?? null,
      } } };
}

export async function buildDomainBundle() {
  const host = newProducerHost();
  const low = lower(PROGRAM.ast);
  if (!low.ok) throw new Error("domain-bundle-lower-refused: " + low.reason);
  const assignments = cartesian(PROGRAM.variables, VARIABLE_DOMAINS);
  const cases = [];
  for (let i = 0; i < assignments.length; i++) {
    const ev = await buildCase(host, PROGRAM.ast, low, assignments[i], i);
    ev.case_evidence_id = domainCaseId(ev);
    cases.push(ev);
  }
  const emitted = cases.filter((c) => c.disposition === "EMITTED");
  const refused = cases.filter((c) => c.disposition === "REFUSED");
  const ids = cases.map((c) => c.assignment_sem_id);
  const program_sem_id = programSemId(PROGRAM.ast);
  const domain_sem_id = domainSemId2(VARIABLE_DOMAINS);
  const aggregate = {
    case_set_commitment: caseSetCommitment(ids),
    case_evidence_ids: cases.map((c) => c.case_evidence_id),
    completed: cases.length,
    distinct_assignments: new Set(ids).size,
    missing: assignments.length - new Set(ids).size,
    emitted: emitted.length,
    refused: refused.length,
    // MEASURED, and it is the finding this workload exists for: how many of the
    // refusals have a final source value that IS representable. A compiler
    // deciding representability from the result would accept these.
    refused_with_representable_source_value:
      refused.filter((c) => Number.isInteger(c.source_value) && c.source_value >= 0).length,
    emitted_outcomes_equal_source:
      emitted.filter((c) => c.evidence.outcome?.value === c.source_value).length,
    refusal_codes: [...new Set(refused.map((c) => c.refusal.refusal_code))],
    bounded_claim_verdict: "PENDING",
    aggregate_id: null,
  };
  aggregate.bounded_claim_verdict =
    aggregate.completed === assignments.length
    && aggregate.distinct_assignments === assignments.length
    && aggregate.emitted + aggregate.refused === assignments.length
    && aggregate.emitted_outcomes_equal_source === aggregate.emitted ? "VERIFIED" : "REFUSED";
  aggregate.aggregate_id = aggregateId(aggregate);
  return {
    type: "BoundedDomainCertificate",
    protocol: DOMAIN_PROTOCOL,
    version: DOMAIN_BUNDLE_VERSION,
    claim: {
      program: PROGRAM,
      program_sem_id,
      variable_domains: VARIABLE_DOMAINS,
      domain_sem_id,
      expected_cases: assignments.length,
      scope: DOMAIN_CLAIM_SCOPE,
      // THE ABSENCE CONTRACT IS PART OF THE CLAIM AND PART OF ITS IDENTITY.
      // `downstream_of_emission` used to sit here alone, unbound, and a claimant
      // could shorten it without moving a single hash.
      refusal_contract: REFUSAL_CONTRACT,
      domain_claim_sem_id: domainClaimSemId(
        program_sem_id, domain_sem_id, DOMAIN_CLAIM_SCOPE, REFUSAL_CONTRACT),
    },
    chain_ids: chainIds(),
    port_names: templatePorts(low.template),
    cases,
    aggregate,
    /* THE SECOND TRUST DOMAIN — P3.1. Reachable by no identity, read by
       nothing, checked only for shape, and never interpolated into a sentence
       about what was verified. The refusal prose that P2.1 put inside each
       refusal record lives here instead, keyed by the assignment it explains. */
    annotations: {
      note: "NON-AUTHORITATIVE — nothing in this record is hashed, checked, or established",
      generator: "domain_bundle.mjs v" + DOMAIN_BUNDLE_VERSION,
      statement: "F(x,y) = (x - y) + 2",
      scope_notes: DOMAIN_CLAIM_SCOPE_NOTES,
      refusals: Object.fromEntries(refused.map((c) => [c.assignment_sem_id,
        "the source program evaluates to " + c.source_value + " and the compiler declines: this " +
        "is a CODOMAIN refusal, not a source refusal, and no target outcome is claimed"])),
    },
  };
}

const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN) {
  const b = await buildDomainBundle();
  const out = join(HERE, "domain_bundle.json");
  writeFileSync(out, JSON.stringify(b, null, 1) + "\n");
  const a = b.aggregate;
  console.log(`domain_bundle v${DOMAIN_BUNDLE_VERSION} — ${b.annotations.statement} ` +
    `(the GENERATOR's wording, non-authoritative; domain_check renders its own from the AST)`);
  console.log(`  ${a.completed} cases: ${a.emitted} EMITTED, ${a.refused} REFUSED ` +
    `[${a.refusal_codes.join(", ")}] → ${a.bounded_claim_verdict}`);
  console.log(`  ${a.emitted_outcomes_equal_source}/${a.emitted} emitted outcomes equal the source`);
  console.log(`  ${a.refused_with_representable_source_value}/${a.refused} refusals have a ` +
    `REPRESENTABLE final source value — a compiler deciding from the RESULT would accept them`);
  console.log(`  aggregate ${a.aggregate_id}`);
  console.log(`  written to ${out}`);
}
