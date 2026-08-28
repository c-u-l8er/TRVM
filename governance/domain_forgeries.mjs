/* ═══════════════════════════════════════════════════════════════════════════
   domain_forgeries.mjs — v0.1.0 — P2's NON-VACUITY
   law:proof.bounded-claim@1 · law:evidence.instrument-nonvacuity@1

   P1's forgeries attacked coverage, identity and reseal. P2 has a second kind
   of evidence to defend — a REFUSAL, and the ABSENCE of everything downstream
   of it — so the forgeries attack the branch structure itself. GPT's eleven,
   plus the ones the same reasoning reaches.

   The shapes worth naming, because they are what "negative evidence doing real
   work" means:

     · an assignment the compiler must refuse, relabelled EMITTED, or the
       reverse — the certificate lying about the partition;
     · a refusal case that carries an emission receipt, or a film, or an
       outcome, ANYWAY — the absence stops being an assertion;
     · a refusal renamed to a different code, or moved to a different phase —
       the certificate saying WHERE the chain stopped, wrongly;
     · and the one this workload exists for: (0-1)+2, whose final source value
       is 1 and therefore representable, accepted because somebody checked the
       ANSWER rather than the COMPUTATION.

   AND FIVE MORE AT P2.1, WHICH ATTACK THE CONTRACT RATHER THAN A CASE. P2 read
   the absent-set out of the certificate, so every forgery above could be
   defeated by a claimant who simply redefined what absence meant — shorten the
   list, shorten each case's `absent` to match, attach a real film, reseal. P2
   accepted that at ok:true with ZERO refusals. So the certificate's contract is
   now compared against the CHECKER's, and the new shapes are: the contract
   narrowed, the contract widened to admit refusals this protocol does not have,
   the contract MOVED with every case obediently following it, the structural
   witness lying about which subtraction underflowed, and a film hidden in the
   unhashed `notes` seat that moving prose out of the identity created.

   Each forgery must draw ITS OWN refusal code, and every mutation is digested
   before and after so a forgery that forged nothing FAILS rather than counting.
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { checkDomainBundle, evalForTargetDomain } from "./domain_check.mjs";
import { domainCaseId, domainClaimSemId, domainSemId2, REFUSAL_CONTRACT }
  from "./domain_bundle.mjs";
import { caseSetCommitment, aggregateId } from "./proof_bundle.mjs";

/** Reseal a certificate as coherently as a forger could: every case id, the
 *  aggregate's list, the aggregate id and the claim id. A forgery that only
 *  survives because it forgot to reseal has not tested anything. */
const reseal = (b) => {
  for (const c of b.cases) c.case_evidence_id = domainCaseId(c);
  b.aggregate.case_evidence_ids = b.cases.map((c) => c.case_evidence_id);
  b.aggregate.aggregate_id = aggregateId(b.aggregate);
  b.claim.domain_claim_sem_id = domainClaimSemId(
    b.claim.program_sem_id, b.claim.domain_sem_id, b.claim.scope, b.claim.refusal_contract);
  return b;
};

const HERE = dirname(fileURLToPath(import.meta.url));
const BUNDLE = process.argv[2] ?? join(HERE, "domain_bundle.json");
const digest = (o) => createHash("sha256").update(JSON.stringify(o)).digest("hex");
const clone = (o) => JSON.parse(JSON.stringify(o));
const at = (b, pred) => b.cases.find(pred);

let ran = 0, fail = false;
const CASES = [];
const F = (name, wants, mutate, why) => CASES.push({ name, wants, mutate, why });

/* ── 1. AN EXPECTED-EMITTING ASSIGNMENT RELABELLED REFUSED ──────────────── */
F("emitting-relabelled-refused", "domain-disposition-mismatch", (b) => {
  const c = at(b, (x) => x.disposition === "EMITTED");
  const { evidence, ...rest } = c;
  Object.keys(c).forEach((k) => delete c[k]);
  Object.assign(c, rest, { disposition: "REFUSED",
    refusal: { program_sem_id: evidence.program_sem_id,
      lowering_receipt: evidence.lowering_receipt,
      instantiation_receipt: evidence.instantiation_receipt,
      closed_template_sem_id: evidence.closed_template_sem_id,
      refusal_phase: REFUSAL_CONTRACT.phase, refusal_code: "emit-sub-underflow",
      refusal_witness: { minuend: 9, subtrahend: 99 },
      absent: REFUSAL_CONTRACT.downstream_absent } });
  c.case_evidence_id = domainCaseId(c);
}, "a certificate claiming the compiler refuses something it emits. The checker derives the " +
   "disposition itself AND re-emits, so the claim fails twice over");

/* ── 2. AN EXPECTED-REFUSING ASSIGNMENT GIVEN A FAKE TARGET RESULT ──────── */
F("refusing-given-a-target-result", "domain-disposition-mismatch", (b) => {
  const donor = at(b, (x) => x.disposition === "EMITTED");
  const c = at(b, (x) => x.disposition === "REFUSED");
  delete c.refusal;
  c.disposition = "EMITTED";
  c.evidence = clone(donor.evidence);
  c.case_evidence_id = domainCaseId(c);
}, "the miscompilation this whole workload exists to refuse, stated as evidence: an underflowing " +
   "computation carrying a complete successful chain");

/* ── 3. THE UNDERFLOW REFUSAL RENAMED ───────────────────────────────────── */
F("refusal-code-renamed", "domain-refusal-attribution-wrong", (b) => {
  const c = at(b, (x) => x.disposition === "REFUSED");
  c.refusal.refusal_code = "emit-unbound-port";
  c.case_evidence_id = domainCaseId(c);
}, "the certificate says WHY the chain stopped and it must say so truthfully. The checker derives " +
   "WHETHER a refusal is due on its own and then asks the compiler WHICH — only the compiler can " +
   "answer the second, and a certificate may not answer it for the compiler");

/* ── 4. THE REFUSAL MOVED TO AN EARLIER PHASE ───────────────────────────── */
F("refusal-moved-to-lowering", "domain-refusal-attribution-wrong", (b) => {
  const c = at(b, (x) => x.disposition === "REFUSED");
  c.refusal.refusal_phase = "LOWERING";
  c.case_evidence_id = domainCaseId(c);
}, "B7's ruling as a forgery: `sub(input x, input y)` has NO underflow fact until ports bind, so a " +
   "refusal at lowering is a claim about an object that cannot have made it. WHERE the chain stops " +
   "is part of what the certificate asserts");

/* ── 5. A REFUSAL CARRYING AN EMISSION RECEIPT ANYWAY ───────────────────── */
F("refusal-carries-emission-receipt", "domain-refusal-carries-evidence", (b) => {
  const donor = at(b, (x) => x.disposition === "EMITTED");
  const c = at(b, (x) => x.disposition === "REFUSED");
  c.refusal.emission_receipt = clone(donor.evidence.emission_receipt);
  c.case_evidence_id = domainCaseId(c);
}, "the absence stops being an assertion. A refusal that carries the receipt of the step it says " +
   "did not happen is not a refusal");

/* ── 6. A REFUSAL CARRYING A FILM AND AN OUTCOME ANYWAY ─────────────────── */
F("refusal-carries-film-and-outcome", "domain-refusal-carries-evidence", (b) => {
  const donor = at(b, (x) => x.disposition === "EMITTED");
  const c = at(b, (x) => x.disposition === "REFUSED");
  c.refusal.film = clone(donor.evidence.film);
  c.refusal.outcome = clone(donor.evidence.outcome);
  c.refusal.target_nf_sem_id = donor.evidence.target_nf_sem_id;
  c.case_evidence_id = domainCaseId(c);
}, "the same shape one layer further down: an execution and an answer for a program that was never " +
   "emitted. Enumerated from the CHECKER's refusal contract rather than remembered — and after " +
   "P2.1, rather than read out of the certificate under attack");

/* ── 7. THE DECLARED ABSENCE QUIETLY SHRINKS ────────────────────────────── */
F("declared-absence-shrinks", "domain-refusal-contract-mismatch", (b) => {
  const c = at(b, (x) => x.disposition === "REFUSED");
  c.refusal.absent = c.refusal.absent.filter((f) => f !== "film");
  c.case_evidence_id = domainCaseId(c);
}, "a refusal that stops asserting the absence of one artifact. The list must be the CHECKER's " +
   "contract, not the certificate's — under P2 this drew `malformed`, and it is not a malformation, " +
   "it is a case declining the absence protocol it is filed under");

/* ── 8. THE SOURCE VALUE CHANGED, CLASSIFICATION LEFT RIGHT ─────────────── */
F("source-value-changed-classification-kept", "domain-source-value-wrong", (b) => {
  const c = at(b, (x) => x.disposition === "REFUSED");
  c.source_value = 42;
  c.case_evidence_id = domainCaseId(c);
}, "the disposition stays correct and the recorded source value does not. The checker computes the " +
   "value itself, so a certificate cannot be right about the branch and wrong about the fact");

/* ── 9. ONE EMITTING CASE'S CHAIN COPIED ONTO A REFUSAL ASSIGNMENT ──────── */
F("emitting-chain-copied-onto-refusal", "domain-disposition-mismatch", (b) => {
  const donor = at(b, (x) => x.disposition === "EMITTED");
  const c = at(b, (x) => x.disposition === "REFUSED");
  const keep = { case_index: c.case_index, assignment: c.assignment,
    assignment_sem_id: c.assignment_sem_id, source_value: c.source_value };
  Object.keys(c).forEach((k) => delete c[k]);
  Object.assign(c, keep, { disposition: "EMITTED", evidence: clone(donor.evidence) });
  c.case_evidence_id = domainCaseId(c);
}, "a whole real successful chain, filed under an assignment that must be refused. Every receipt in " +
   "it verifies against ITS OWN closed template — it is simply not this case's");

/* ── 10. THE DOMAIN WIDENED COHERENTLY, EVIDENCE LEFT SHORT ─────────────── */
F("domain-widened-and-resealed", "domain-case-missing", (b) => {
  b.claim.variable_domains.x = [0, 1, 2, 3, 4];
  b.claim.domain_sem_id = domainSemId2(b.claim.variable_domains);
  b.claim.expected_cases = 20;
  reseal(b);
}, "every hash internally consistent and a coherent claim about 20 assignments carrying evidence " +
   "for 16. No hash check can see it; the derived coverage refuses it");

/* ── 11. "ALL 16" OVER 15 UNIQUE ASSIGNMENTS ────────────────────────────── */
F("count-claimed-over-nonunique", "domain-count-inconsistent", (b) => {
  b.cases[11] = clone(b.cases[3]);
  b.aggregate.case_set_commitment = caseSetCommitment(b.cases.map((c) => c.assignment_sem_id));
  b.aggregate.case_evidence_ids = b.cases.map((c) => c.case_evidence_id);
  b.aggregate.distinct_assignments = 16;
  b.aggregate.aggregate_id = aggregateId(b.aggregate);
}, "resealed around its own duplicate: 16 completed over 15 distinct, refused by arithmetic");

/* ── 12. THE PARTITION STOPS BEING TOTAL ────────────────────────────────── */
F("disposition-neither-branch", "domain-refusal-malformed", (b) => {
  const c = at(b, (x) => x.disposition === "REFUSED");
  c.disposition = "SKIPPED";
  c.case_evidence_id = domainCaseId(c);
}, "an assignment in NEITHER branch. `disposition_is_total` is a scope value, and this is it being " +
   "cashed: a certificate may not quietly decline to classify an assignment it declares it covers");

/* ── 13. THE SCOPE REWRITTEN, RESEALED ──────────────────────────────────── */
F("scope-bounded-to-unbounded", "domain-scope-mismatch", (b) => {
  b.claim.scope = { kind: "UNBOUNDED_DOMAIN_PROOF", quantifier: "FOR_ALL_NATURALS",
                    generalizes_beyond_domain: true, disposition_is_total: true };
  reseal(b);
}, "P1.1's finding carried into P2's protocol: 16 assignments of real evidence under a coherent, " +
   "correctly-hashed claim about all naturals");

/* ── 15. GPT'S ATTACK: THE CLAIMANT REDEFINES WHAT ABSENCE MEANS ─────────
   The one that made P2.1 exist, reproduced verbatim. Against P2 this returned
   `ok:true` with ZERO refusals, for a case reading REFUSED / EMISSION beside an
   eight-frame native film. */
F("absence-contract-narrowed-and-resealed", "domain-refusal-contract-mismatch", (b) => {
  const donor = at(b, (x) => x.disposition === "EMITTED");
  b.claim.refusal_contract = { ...b.claim.refusal_contract,
    downstream_absent: b.claim.refusal_contract.downstream_absent.filter((f) => f !== "film") };
  for (const c of b.cases) if (c.disposition === "REFUSED")
    c.refusal.absent = c.refusal.absent.filter((f) => f !== "film");
  at(b, (x) => x.disposition === "REFUSED").refusal.film = clone(donor.evidence.film);
  reseal(b);
}, "the claimant shortens the absence contract, shortens every case's declared absence to match, " +
   "hangs a REAL film on a refusal, and reseals every identity in the artifact including the claim " +
   "id. Nothing is internally inconsistent. It is refused because the checker OWNS the contract and " +
   "compares rather than reads — P1.1's ruling on scope, one layer down");

/* ── 16. THE CONTRACT ADMITS A CODE THE PROTOCOL DOES NOT ────────────────── */
F("contract-widened-to-admit-any-refusal", "domain-refusal-contract-mismatch", (b) => {
  b.claim.refusal_contract = { ...b.claim.refusal_contract,
    allowed_codes: [...b.claim.refusal_contract.allowed_codes, "emit-unbound-port",
                    "template-malformed"] };
  reseal(b);
}, "a certificate that declares itself entitled to refuse for reasons this protocol does not admit. " +
   "`allowed_codes` is the second half of the contract: WHERE a chain may stop, and WHICH stops " +
   "count. A widened list is a different protocol wearing this one's name");

/* ── 17. THE WHOLE PROTOCOL MOVED TO AN EARLIER PHASE, COHERENTLY ────────── */
F("contract-phase-moved-and-every-case-follows", "domain-refusal-contract-mismatch", (b) => {
  b.claim.refusal_contract = { ...b.claim.refusal_contract, phase: "LOWERING" };
  for (const c of b.cases) if (c.disposition === "REFUSED") c.refusal.refusal_phase = "LOWERING";
  reseal(b);
}, "forgery 4 done properly: not one case disagreeing with the contract, but the CONTRACT MOVED and " +
   "every case following it, so the artifact is entirely self-consistent. B7's ruling says " +
   "`sub(input x, input y)` has no underflow fact until ports bind, and the checker holds that " +
   "ruling rather than the certificate");

/* ── 18. THE STRUCTURAL WITNESS LIES ─────────────────────────────────────── */
F("refusal-witness-lies", "domain-refusal-attribution-wrong", (b) => {
  const c = at(b, (x) => x.disposition === "REFUSED");
  c.refusal.refusal_witness = { minuend: 3, subtrahend: 0 };
  c.case_evidence_id = domainCaseId(c);
}, "what replaced the hashed English. `3 - 0` does not underflow, so this refusal now says the " +
   "chain stopped at a subtraction that had no reason to stop it. Under P2 the equivalent lie lived " +
   "in `refusal_detail`, was hashed, and was never read by anything");

/* ── 19. THE MIXED SEAT ITSELF ───────────────────────────────────────────── */
F("prose-seat-reopened-inside-the-refusal", "domain-vocabulary-unknown", (b) => {
  const donor = at(b, (x) => x.disposition === "EMITTED");
  const c = at(b, (x) => x.disposition === "REFUSED");
  c.refusal.notes = { why: "harmless", film: clone(donor.evidence.film) };
  c.case_evidence_id = domainCaseId(c);
}, "P2.1 put an unhashed `notes` seat INSIDE the refusal record and bounded it to strings. A real " +
   "film hidden there moved no identity at all, because the identity deliberately did not cover it " +
   "— so the bound was the only thing standing between the absence contract and a back door. P3.1 " +
   "removed the seat instead of guarding it: `notes` is not in the grammar, so re-opening it is an " +
   "unknown semantic key before anything has to reason about what is inside it");

/* ── 20-24. THE VOCABULARY ATTACKS, GPT'S LIST ───────────────────────────── */
F("scope-gains-proves_all_integers", "domain-vocabulary-unknown", (b) => {
  b.claim.scope = { ...b.claim.scope, proves_all_integers: true };
  reseal(b);
}, "GPT's attack 2, verbatim. Nothing the checker READ was wrong — every value it knew about was " +
   "correct. The claimant added a field the checker had never agreed to, resealed, and the " +
   "certificate came back VERIFIED asserting boundedness in one field and all the integers in the " +
   "next. Owning the VALUES of known fields is not owning the vocabulary");

F("claim-gains-an-unbound-semantic-field", "domain-vocabulary-unknown", (b) => {
  b.claim.entails = "EVERY PROGRAM IN THE SOURCE LANGUAGE";
  reseal(b);
}, "and the claim record itself had no vocabulary, so a semantic-looking assertion could simply be " +
   "added beside the ones that are checked");

F("refusal-witness-gains-a-field", "domain-vocabulary-unknown", (b) => {
  const c = at(b, (x) => x.disposition === "REFUSED");
  c.refusal.refusal_witness = { ...c.refusal.refusal_witness,
    also_proves: "EVERY SUBTRACTION IS REPRESENTABLE" };
  c.case_evidence_id = domainCaseId(c);
}, "GPT's attack 6. The witness P2.1 added to replace hashed English was itself an open record — so " +
   "the repair for prose-in-a-hash shipped with the vocabulary defect inside it");

F("aggregate-measurement-invented", "domain-count-inconsistent", (b) => {
  b.aggregate.emitted_outcomes_equal_source = 10;
  b.aggregate.refused_with_representable_source_value = 0;
  b.aggregate.aggregate_id = aggregateId(b.aggregate);
  b.cases[1].source_value = b.cases[1].source_value;   // keep the digest honest
  b.aggregate.refusal_codes = ["emit-nothing-ever"];
  b.aggregate.aggregate_id = aggregateId(b.aggregate);
}, "three aggregate fields that were hashed into aggregate_id and compared to nothing. The middle " +
   "one is the headline of the emitted branch and the last is the NAME OF THE REFUSAL — a " +
   "certificate could rename its own refusal code in the summary while every case still said " +
   "emit-sub-underflow. Hashing a value is not evidence for that value");

F("annotations-carry-a-film", "domain-vocabulary-unknown", (b) => {
  const donor = at(b, (x) => x.disposition === "EMITTED");
  b.annotations = { ...b.annotations, smuggled: clone(donor.evidence.film) };
}, "the bill for having a second trust domain at all, paid where it is cheap: annotations are " +
   "reachable by no identity and read by nothing, so the ONE thing a checker must still do is say " +
   "what may sit there. Prose, and only prose");

/* ── 14. AN EMITTED CASE THAT ALSO CARRIES A REFUSAL ────────────────────── */
F("emitted-case-carries-a-refusal", "domain-refusal-malformed", (b) => {
  const donor = at(b, (x) => x.disposition === "REFUSED");
  const c = at(b, (x) => x.disposition === "EMITTED");
  c.refusal = clone(donor.refusal);
  c.case_evidence_id = domainCaseId(c);
}, "the sum type collapsed the other way. A case is one branch or the other, and a record carrying " +
   "both is not a disjunction");

if (!existsSync(BUNDLE)) { console.log(`DOMAIN-FORGERIES: FAIL — no certificate at ${BUNDLE}`); process.exit(1); }
const HONEST = JSON.parse(readFileSync(BUNDLE, "utf8"));

{
  ran++;
  const r = checkDomainBundle(clone(HONEST));
  if (r.ok !== true) { fail = true;
    console.log(`FAIL  honest-certificate-verifies  ${r.refusals.slice(0, 3).map((x) => x.code + ": " + x.detail).join(" | ")}`);
  } else console.log(`PASS  honest-certificate-verifies  ${r.measured.emitted} EMITTED + ` +
    `${r.measured.refused} REFUSED = ${r.measured.derived_cases} derived`);
}

/* ── THE POSITIVE PROPERTY THIS WORKLOAD EXISTS FOR ───────────────────────
   Not a forgery: a direct measurement of the checker's OWN derivation. A
   result-only check would accept five of the six refusals, and this says so in
   numbers rather than in the file header. */
{
  ran++;
  const ast = HONEST.claim.program.ast;
  const rows = HONEST.cases.map((c) => ({ a: c.assignment, ...evalForTargetDomain(ast, c.assignment) }));
  const refused = rows.filter((r) => r.disposition === "REFUSED");
  const wouldPass = refused.filter((r) => r.final_value_is_representable);
  const zeroOne = rows.find((r) => r.a.x === 0 && r.a.y === 1);
  if (!(refused.length === 6 && wouldPass.length === 5
        && zeroOne.disposition === "REFUSED" && zeroOne.value === 1
        && zeroOne.final_value_is_representable === true)) {
    fail = true;
    console.log(`FAIL  result-only-check-would-accept-five  refused ${refused.length}, ` +
      `would-pass ${wouldPass.length}, (0,1) ${zeroOne.disposition}/${zeroOne.value}`);
  } else console.log(`PASS  result-only-check-would-accept-five  ${wouldPass.length}/${refused.length} ` +
    `refusals have a REPRESENTABLE final source value — (0-1)+2 is 1 and REFUSED. A checker deciding ` +
    `from the ANSWER agrees with the compiler on 11 of 16 and silently accepts 5 miscompilations`);
}

/* ── THE TWO PROPERTIES P2.1 ADDED, MEASURED RATHER THAN ASSERTED ─────────
   Both are POSITIVE: they say what must NOT change and what MUST. The first is
   the direct counterpart of P2's defect — prose was hashed and unread, so
   rewording moved the proof's identity while lying left it valid. */
{
  ran++;
  const b = clone(HONEST);
  const c = b.cases.find((x) => x.disposition === "REFUSED");
  const idBefore = c.case_evidence_id;
  b.annotations = { note: "rewritten entirely", statement: "reworded",
    scope_notes: { established: "reworded too" },
    refusals: Object.fromEntries(Object.keys(b.annotations.refusals ?? {})
      .map((k) => [k, "an explanation that did not exist a moment ago"])) };
  const idAfter = domainCaseId(c);
  const r = checkDomainBundle(b);
  if (!(idAfter === idBefore && r.ok === true)) {
    fail = true;
    console.log(`FAIL  rewording-annotations-is-free  id ${idAfter === idBefore ? "held" : "MOVED"}, ` +
      `checker ${r.ok ? "ok" : r.refusals.map((x) => x.code).join(",")}`);
  } else console.log(`PASS  rewording-annotations-is-free  case_evidence_id ${idBefore.slice(0, 16)}… ` +
    `is UNCHANGED after every sentence in the artifact is rewritten, and the certificate still ` +
    `verifies. P2 hashed \`why\` and \`refusal_detail\` and read neither, so rewording MOVED the ` +
    `proof's identity while lying left it VERIFIED; P2.1 put the prose in an unhashed seat INSIDE ` +
    `the refusal; P3.1 moved it to the other trust domain, where it is not nested in anything ` +
    `authenticated at all`);
}
{
  ran++;
  const c = HONEST.claim;
  const narrowed = { ...c.refusal_contract,
    downstream_absent: c.refusal_contract.downstream_absent.filter((f) => f !== "film") };
  const idWith = domainClaimSemId(c.program_sem_id, c.domain_sem_id, c.scope, c.refusal_contract);
  const idNarrowed = domainClaimSemId(c.program_sem_id, c.domain_sem_id, c.scope, narrowed);
  if (!(idWith === c.domain_claim_sem_id && idNarrowed !== idWith)) {
    fail = true;
    console.log(`FAIL  absence-contract-binds-the-claim-id  ${idWith.slice(0, 20)} vs ${idNarrowed.slice(0, 20)}`);
  } else console.log(`PASS  absence-contract-binds-the-claim-id  dropping ONE field from ` +
    `downstream_absent moves domain_claim_sem_id ${idWith.slice(0, 16)}… → ${idNarrowed.slice(0, 16)}…. ` +
    `Under P2 that edit left the claim identity BYTE-IDENTICAL, so the meaning of the negative ` +
    `evidence could change while the identity of the bounded claim stood still`);
}

for (const c of CASES) {
  ran++;
  const b = clone(HONEST);
  const before = digest(b);
  try { c.mutate(b); } catch (e) { fail = true; console.log(`FAIL  ${c.name}  (forgery threw: ${e.message})`); continue; }
  if (digest(b) === before) { fail = true; console.log(`FAIL  ${c.name}  (VACUOUS — the forgery changed nothing)`); continue; }
  const r = checkDomainBundle(b);
  const codes = [...new Set(r.refusals.map((x) => x.code))];
  if (r.ok) { fail = true; console.log(`FAIL  ${c.name}  (ACCEPTED — the checker verified a forged certificate)`); }
  else if (!codes.includes(c.wants)) { fail = true;
    console.log(`FAIL  ${c.name}  (WRONG REFUSAL — wanted ${c.wants}, got [${codes.join(", ")}])`); }
  else console.log(`PASS  ${c.name.padEnd(38)} → ${c.wants}` +
    (codes.length > 1 ? `  (+${codes.length - 1} other code(s))` : ""));
}

console.log("═".repeat(96));
const byCode = new Map();
for (const c of CASES) byCode.set(c.wants, (byCode.get(c.wants) ?? 0) + 1);
console.log(fail
  ? `DOMAIN-FORGERIES: FAIL — ${ran} cases ran, at least one forgery was not caught by its own check`
  : `DOMAIN-FORGERIES: PASS — ${ran}/${ran}. The honest certificate verifies, the checker's own ` +
    `derivation is measured against the result-only shortcut it must not take, and ${CASES.length} ` +
    `forged certificates are each refused BY THE CHECK WHOSE SUBJECT THEY ARE across ` +
    `${byCode.size} distinct codes [${[...byCode].map(([k, n]) => `${k}×${n}`).join(", ")}]: ` +
    `${CASES.map((c) => c.name).join(", ")}. THE NEGATIVE-EVIDENCE SHAPES ARE THE POINT: a refusal ` +
    `carrying the receipt of the step it says did not happen, a refusal carrying a film and an ` +
    `outcome for a program that was never emitted, a refusal moved to a phase that cannot have made ` +
    `it, and an assignment in NEITHER branch. AND THE FIVE THAT ARE NEW IN P2.1 ARE THE ONES THAT ` +
    `ATTACK THE CONTRACT ITSELF RATHER THAN A CASE: the claimant narrowing the absence contract and ` +
    `resealing every identity including the claim id — which P2 ACCEPTED, ok:true and zero refusals, ` +
    `for a case reading REFUSED at EMISSION beside a real eight-frame film; the contract widened to ` +
    `admit refusals this protocol does not have; the whole contract moved to LOWERING with every ` +
    `case following it, so nothing in the artifact disagrees with anything else in it; the ` +
    `structural witness lying about which subtraction underflowed; and a film smuggled into the ` +
    `UNHASHED \`notes\` seat, which is the bill for moving prose out of the identity and is why the ` +
    `checker bounds that seat to a flat record of strings. Every mutation is digested before and ` +
    `after, so a forgery that forged nothing FAILS rather than counting`);
process.exit(fail ? 1 : 0);
