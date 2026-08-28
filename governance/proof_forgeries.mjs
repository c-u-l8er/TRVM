/* ═══════════════════════════════════════════════════════════════════════════
   proof_forgeries.mjs — v0.1.0 — THE CHECKER'S NON-VACUITY
   law:proof.bounded-claim@1 · law:evidence.instrument-nonvacuity@1

   `proof_check.mjs` reports PASS in about a third of a second over 64 cases,
   128 re-derived chains and 128 film replays. That number means nothing until
   the checker has been shown to be able to REFUSE, and to refuse for the
   reason it names rather than for a neighbouring one.

   So every shape GPT enumerated gets a forgery here, mutating the BUNDLE — the
   evidence, not the source — and each is required to produce ITS OWN refusal
   code. `wants` is checked by membership in the returned codes, and a forgery
   whose code is absent FAILS even if the checker refused for something else:
   this line has recorded five times that a forgery caught by a neighbour is a
   green report about a check nobody exercised.

   TWO THINGS THIS FILE IS CAREFUL ABOUT:

     · A FORGERY THAT CHANGES NOTHING IS WORSE THAN AN ABSENT ONE, because the
       roster still counts it. Every case digests the bundle before and after
       and fails if the mutation was a no-op — the negative battery's
       instrument-nonvacuity law, applied to a JSON object instead of a tree.
     · THE HONEST BUNDLE MUST STILL PASS after every case, or the forgeries are
       leaking into each other. Each starts from a fresh deep copy.
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { checkBundle } from "./proof_check.mjs";
import { lower } from "./lowering.mjs";
import { assignmentSemId, caseEvidenceId, aggregateId, caseSetCommitment, domainSemId,
  boundedClaimSemId, propositionSemId, buildSide, newProducerHost, PROPOSITION } from "./proof_bundle.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const BUNDLE = process.argv[2] ?? join(HERE, "proof_bundle.json");
const digest = (o) => createHash("sha256").update(JSON.stringify(o)).digest("hex");
const clone = (o) => JSON.parse(JSON.stringify(o));

let ran = 0, fail = false;
const CASES = [];
const F = (name, wants, mutate, why) => CASES.push({ name, wants, mutate, why });

/* ── 1. ONE CASE MISSING ────────────────────────────────────────────────── */
F("one-case-missing", "proof-case-missing", (b) => { b.cases.splice(37, 1); },
  "63 cases for a 64-assignment domain. The checker derives the product itself, so " +
  "this is arithmetic rather than a comparison against a number the bundle supplied");

/* ── 2. ONE CASE DUPLICATED ─────────────────────────────────────────────── */
F("one-case-duplicated", "proof-case-duplicated", (b) => {
  // the honest shape of the dishonest bundle: drop one and repeat another, so
  // the COUNT is still 64 and only the coverage is short. A bundle that simply
  // appended a copy would be caught by the count alone.
  b.cases[37] = clone(b.cases[12]);
}, "64 cases over 63 unique assignments, which is the shape a total that is not a coverage takes");

/* ── 3. ONE ASSIGNMENT OUTSIDE THE DOMAIN ───────────────────────────────── */
F("assignment-outside-domain", "proof-assignment-outside-domain", (b) => {
  b.cases[5].assignment = { x: 9, y: 0, z: 1 };
  b.cases[5].assignment_sem_id = assignmentSemId(b.cases[5].assignment);
  b.cases[5].case_evidence_id = caseEvidenceId(b.cases[5]);
}, "an assignment the declared domain does not contain, re-labelled and re-identified so only " +
   "the DOMAIN check can catch it");

/* ── 4. ONE ASSIGNMENT MISLABELLED ──────────────────────────────────────── */
F("assignment-mislabelled", "proof-assignment-mislabelled", (b) => {
  b.cases[9].assignment_sem_id = assignmentSemId({ x: 0, y: 0, z: 0 });
  b.cases[9].case_evidence_id = caseEvidenceId(b.cases[9]);
}, "an id that identifies a DIFFERENT assignment than the one it sits beside — the shape that " +
   "lets one case's evidence be filed under another case's name");

/* ── 5. ONE SIDE'S RECEIPT REPLACED ─────────────────────────────────────── */
F("receipt-replaced", "proof-receipt-replaced", (b) => {
  b.cases[20].lhs.emission_receipt = clone(b.cases[21].lhs.emission_receipt);
  b.cases[20].case_evidence_id = caseEvidenceId(b.cases[20]);
}, "a well-formed receipt from a DIFFERENT case, which verifies against its own closed template " +
   "and is wrong only about which case it belongs to");

/* ── 6. ONE OUTCOME CHANGED ─────────────────────────────────────────────── */
F("outcome-changed", "proof-outcome-changed", (b) => {
  b.cases[44].rhs.outcome = { status: "value", value: 999 };
  b.cases[44].case_evidence_id = caseEvidenceId(b.cases[44]);
}, "the decoded answer altered. The checker re-decodes from a normal form it reached itself, so " +
   "this cannot be repaired by also editing the outcome id");

/* ── 7. THE DOMAIN WIDENED AFTER THE FACT ───────────────────────────────── */
F("domain-widened-after-the-fact", "proof-domain-widened", (b) => {
  b.claim.variable_domains.x = [0, 1, 2, 3, 4];
}, "the strongest of these: 64 cases of real evidence, and a claim that has quietly become a " +
   "claim about 80 assignments. Nothing in the CASES is wrong — the claim moved out from under them");

/* ── 7b. THE DOMAIN WIDENED AND THE CLAIM RE-SEALED AROUND IT ───────────
   The stronger form of 7, and the one that says which check is load-bearing.
   Here the widener is not lazy: domain_sem_id and expected_cases are both
   recomputed, so every hash in the claim is internally consistent and the
   bundle is a coherent statement about 80 assignments carrying evidence for
   64. Only the COVERAGE arithmetic refuses it — which is why the checker
   derives the product rather than comparing counts. */
F("domain-widened-and-resealed", "proof-case-missing", (b) => {
  b.claim.variable_domains.x = [0, 1, 2, 3, 4];
  b.claim.domain_sem_id = domainSemId(b.claim.variable_domains);
  b.claim.expected_cases = 80;
}, "domain, id and expected count all moved together, so the claim is coherent and 16 of its " +
   "assignments have no evidence at all. The hash check goes quiet and the coverage check does " +
   "the work");

/* ── 8. "64/64" OVER 63 UNIQUE ASSIGNMENTS ──────────────────────────────── */
F("count-claimed-over-nonunique", "proof-count-inconsistent", (b) => {
  b.cases[50] = clone(b.cases[3]);
  b.aggregate.case_set_commitment = caseSetCommitment(b.cases.map((c) => c.assignment_sem_id));
  b.aggregate.case_evidence_ids = b.cases.map((c) => c.case_evidence_id);
  b.aggregate.distinct_assignments = 64;          // the lie
  b.aggregate.aggregate_id = aggregateId(b.aggregate);
}, "the aggregate RESEALED around the duplicate so every hash is internally consistent, and only " +
   "the arithmetic — 64 completed against 63 distinct — refuses it");

/* ── 9. A FILM THAT DOES NOT REPLAY ─────────────────────────────────────── */
F("film-frame-forged", "proof-film-replay-refused", (b) => {
  const fr = b.cases[7].lhs.film.frames;
  fr[Math.floor(fr.length / 2)].locus = "t:0";
  b.cases[7].case_evidence_id = caseEvidenceId(b.cases[7]);
}, "one frame's locus moved. The film is the only part of the bundle the checker cannot re-derive " +
   "— it is a native execution — so it is REPLAYED instead, on two runtime classes");

/* ── 10. EVIDENCE ABOUT A DIFFERENT COMPILER ────────────────────────────── */
F("chain-id-from-another-compiler", "proof-chain-id-mismatch", (b) => {
  b.chain_ids.emission_sem_id = "esem-" + "0".repeat(64);
}, "a bundle whose every case is internally perfect and which is evidence about an emission " +
   "relation this tree does not have. The failure is silent unless something looks");

/* ── 11. ONE SIDE'S EVIDENCE IS THE OTHER SIDE'S ────────────────────────
   P1 caught this with a rule refusing any case whose two sides reached the same
   target term, and GPT overruled that rule: a canonicalisation collapsing two
   source programs at one assignment would make the case EASY, not empty, and a
   trivial theorem is a valid theorem. The rule is gone and the forgery is
   UNCHANGED and still caught, harder — the `wants` names what was actually
   doing the work all along. Each side's evidence must be evidence for the
   source program THE PROPOSITION NAMES, and independent reconstruction says so
   nine times over before any question of distinctness arises. */
F("both-sides-same-program", "proof-receipt-replaced", (b) => {
  b.cases[31].rhs = clone(b.cases[31].lhs);
  b.cases[31].equality.target_terms_differ = false;
  b.cases[31].case_evidence_id = caseEvidenceId(b.cases[31]);
}, "the RHS evidence replaced by the LHS's. Caught by RE-DERIVATION -- wrong program_sem_id, wrong " +
   "lowering, instantiation and emission receipts, a film that does not replay -- and not by any " +
   "rule about whether the case is interesting");

/* ── 11b. THE OPTIONAL CLAIM, BROKEN WITHOUT BREAKING VALIDITY ──────────
   THIS artifact additionally claims all its sides compile to distinct target
   terms. That is a property of the workload and not of proof validity, so it
   gets its own code — and a bundle that made no such claim would still verify.
   Forged the only way that isolates it: assert the property while supplying a
   case that violates it, with the evidence otherwise untouched. */
F("declared-property-violated", "proof-scope-property-mismatch", (b) => {
  // make ONE case's sides agree on the target term without disturbing anything
  // the validity checks re-derive: the rhs target_term_sem_id is a recorded
  // field, and the reconstruction refuses it too -- so the point of the case is
  // that the PROPERTY code appears, which `wants` requires by name.
  b.cases[18].rhs.target_term_sem_id = b.cases[18].lhs.target_term_sem_id;
  b.cases[18].case_evidence_id = caseEvidenceId(b.cases[18]);
}, "the bundle asserts every case has distinct sides and one does not. A CLAIM-SPECIFIC property, " +
   "under its own code, never a validity condition");

/* ── 11c. THE SCOPE IS GONE ─────────────────────────────────────────────
   GPT's first reproduction. Deleting claim.scope left checkBundle at ok:true
   with zero refusals: the checker derived a bounded product correctly and never
   looked at what the artifact said it had proved. */
F("scope-deleted", "proof-scope-mismatch", (b) => { delete b.claim.scope; },
  "the artifact stops saying what kind of claim it is, and the evidence is untouched. The checker " +
  "must require the scope semantics IT IMPLEMENTS, not merely implement them");

/* ── 11d. BOUNDED BECOMES UNBOUNDED, EVIDENCE UNTOUCHED ─────────────────
   The second reproduction and the one that matters: 64 assignments of real
   evidence under a claim that says it proves distributivity over the naturals.
   Nothing in the CASES is wrong. */
F("scope-bounded-to-unbounded", "proof-scope-mismatch", (b) => {
  b.claim.scope = { kind: "UNBOUNDED_PROOF", quantifier: "FOR_ALL_NATURALS",
                    generalizes_beyond_domain: true };
  b.claim.bounded_claim_sem_id = boundedClaimSemId(
    b.claim.proposition_sem_id, b.claim.domain_sem_id, b.claim.scope);
}, "and RESEALED: the claim identity is recomputed over the new scope, so every hash in the artifact " +
   "agrees and it is a coherent statement that 64 assignments prove a theorem about all naturals. " +
   "Only a checker that requires its OWN scope semantics refuses it");

/* ── 11e. PROSE RETURNS TO THE HASHED SEAT ──────────────────────────────
   The other direction of B6.3's rule. A scope field holding a sentence is a
   field whose identity moves when somebody rewords the warning, and a warning
   that can be reworded into agreement is not a constraint. */
F("scope-becomes-prose", "proof-scope-mismatch", (b) => {
  b.claim.scope.kind = "BOUNDED EXHAUSTIVE VERIFICATION (see notes)";
  b.claim.bounded_claim_sem_id = boundedClaimSemId(
    b.claim.proposition_sem_id, b.claim.domain_sem_id, b.claim.scope);
}, "a hashed scope value containing whitespace, resealed. Explanatory text belongs in scope_notes, " +
   "where rewording it costs nothing");

/* ── 11f. THE CLAIM IDENTITY NAMES A DIFFERENT CLAIM ────────────────────
   proposition, domain and quantifier semantics were three adjacent pieces with
   nothing binding them. */
F("bounded-claim-id-mislabelled", "proof-scope-mismatch", (b) => {
  b.claim.bounded_claim_sem_id = boundedClaimSemId(
    b.claim.proposition_sem_id, "dom-" + "0".repeat(64), b.claim.scope);
}, "an identity computed over a DIFFERENT domain than the one beside it — the shape that lets one " +
   "claim's evidence be filed under another claim's name");

/* ── 12. THE VERDICT ASSERTED OVER REFUSED EVIDENCE ─────────────────────── */
F("verdict-asserted-not-computed", "proof-count-inconsistent", (b) => {
  b.cases.splice(1, 1);                            // now genuinely short
  b.aggregate.completed = 63;
  b.aggregate.distinct_assignments = 63;
  b.aggregate.missing = 0;                         // the lie
  b.aggregate.case_set_commitment = caseSetCommitment(b.cases.map((c) => c.assignment_sem_id));
  b.aggregate.case_evidence_ids = b.cases.map((c) => c.case_evidence_id);
  b.aggregate.bounded_claim_verdict = "VERIFIED";
  b.aggregate.aggregate_id = aggregateId(b.aggregate);
}, "an aggregate that admits 63 cases, claims 0 missing and still says VERIFIED. The verdict field " +
   "is read last and believed never");

/* ── P3.1: THE CHECKER OWNS THE GRAMMAR, NOT ONLY THE VALUES ──────────────
   Every forgery above changes something the checker READS. These change
   something it did not know existed — which is cheaper, needs no understanding
   of the evidence, and against the shipped P1 came back VERIFIED. */
F("scope-gains-proves_all_naturals", "proof-vocabulary-unknown", (b) => {
  b.claim.scope = { ...b.claim.scope, proves_all_naturals: true };
  b.claim.bounded_claim_sem_id = boundedClaimSemId(
    b.claim.proposition_sem_id, b.claim.domain_sem_id, b.claim.scope);
}, "GPT's attack 1, verbatim. `generalizes_beyond_domain:false` sits two fields away and every " +
   "value the checker read was correct — the claimant simply added a field the protocol does not " +
   "have, resealed the claim identity, and the artifact asserted boundedness and all the naturals " +
   "in one record. Owning the VALUES of known fields is not owning the vocabulary");

F("proposition-regains-its-statement", "proof-vocabulary-unknown", (b) => {
  b.claim.proposition = { ...b.claim.proposition,
    statement: "P = NP, ESTABLISHED BY EXHAUSTIVE VERIFICATION" };
  b.claim.proposition_sem_id = propositionSemId(b.claim.proposition);
  b.claim.bounded_claim_sem_id = boundedClaimSemId(
    b.claim.proposition_sem_id, b.claim.domain_sem_id, b.claim.scope);
}, "the display lie. P1 shipped with `statement` INSIDE the hashed proposition and the PASS line " +
   "printed it, so a resealed sentence put P = NP immediately after the word VERIFIED while all 128 " +
   "chains re-derived and all 128 films replayed. Hashing it made it worse: the identity moved, the " +
   "artifact stayed self-consistent, and nothing existed to disagree. The theorem is RENDERED from " +
   "the ASTs now, and the sentence is not part of the proposition at all");

F("aggregate-failed-count-invented", "proof-count-inconsistent", (b) => {
  b.aggregate.failed = 41;
  b.aggregate.aggregate_id = aggregateId(b.aggregate);
}, "hashed into aggregate_id and compared to nothing. The headline count of FAILED CASES, set to " +
   "forty-one, resealed, and accepted — while the checker's own reconstruction of all 64 cases " +
   "found none. Hashing a value is not evidence for that value");

F("annotations-carry-evidence", "proof-vocabulary-unknown", (b) => {
  b.annotations = { ...b.annotations, smuggled: clone(b.cases[0].lhs.film) };
}, "the price of having a second trust domain, and the one duty a checker keeps over it: " +
   "annotations are reachable by no identity and read by nothing, so what may sit there has to be " +
   "said out loud. Prose, and only prose");

if (!existsSync(BUNDLE)) {
  console.log(`PROOF-FORGERIES: FAIL — no bundle at ${BUNDLE}`);
  process.exit(1);
}
const HONEST = JSON.parse(readFileSync(BUNDLE, "utf8"));

// THE HONEST BUNDLE MUST PASS FIRST. A forgery suite that runs against a bundle
// the checker already refuses proves nothing about the forgeries.
{
  ran++;
  const r = checkBundle(clone(HONEST));
  if (r.ok !== true) {
    fail = true;
    console.log(`FAIL  honest-bundle-verifies  the unmutated bundle is refused: ` +
      `${r.refusals.slice(0, 3).map((x) => x.code).join(", ")}`);
  } else console.log(`PASS  honest-bundle-verifies  ${r.measured.derived_cases} derived cases, ` +
    `${r.measured.reconstructed_sides} sides re-derived, ` +
    `${r.measured.films_replayed_on_two_classes} films replayed on two classes`);
}

for (const c of CASES) {
  ran++;
  const b = clone(HONEST);
  const before = digest(b);
  c.mutate(b);
  if (digest(b) === before) {
    fail = true;
    console.log(`FAIL  ${c.name}  (VACUOUS — the forgery changed nothing)`);
    continue;
  }
  const r = checkBundle(b);
  const codes = [...new Set(r.refusals.map((x) => x.code))];
  if (r.ok) {
    fail = true;
    console.log(`FAIL  ${c.name}  (ACCEPTED — the checker verified a forged bundle)`);
  } else if (!codes.includes(c.wants)) {
    fail = true;
    console.log(`FAIL  ${c.name}  (WRONG REFUSAL — wanted ${c.wants}, got [${codes.join(", ")}])`);
  } else {
    console.log(`PASS  ${c.name.padEnd(32)} → ${c.wants}` +
      (codes.length > 1 ? `  (+${codes.length - 1} other code(s))` : ""));
  }
}

/* ── WHAT AN executor_session_id ACTUALLY DISTINGUISHES, MEASURED ─────────
   `caseEvidenceId` excludes each side's execution_provenance. The reason
   written down first was that a session id "differs every run" — AND THAT IS
   FALSE, and this case measured it false. The host's session counter is
   per-instance and resets with the process, so two generations produce
   IDENTICAL session ids and the first draft of this check failed on its own
   claim rather than on the code.

   WHAT IS TRUE IS SHARPER: a session id names a LAUNCH. Launch the same binary
   twice on the same input, in one host, and the two launches produce
   byte-identical evidence and DIFFERENT session ids. That is exactly why it may
   not sit inside the evidence identity — the identity would then say two
   things were different when the only difference is that somebody ran the
   producer twice.

   Both directions are required here: the ids that must be equal, and the id
   that must not be. */
{
  ran++;
  const host = newProducerHost();
  const lowL = lower(PROPOSITION.lhs);
  const inputs = { x: 2, y: 1, z: 3 };
  const a = await buildSide(host, PROPOSITION.lhs, lowL, inputs);
  const b = await buildSide(host, PROPOSITION.lhs, lowL, inputs);
  const strip = (o) => { const { execution_provenance, ...r } = o; return r; };
  const evidenceIdentical = JSON.stringify(strip(a)) === JSON.stringify(strip(b));
  const sessionsDiffer = a.execution_provenance.executor_session_id
                      !== b.execution_provenance.executor_session_id;
  const artifactSame = a.execution_provenance.executable_artifact_id
                    === b.execution_provenance.executable_artifact_id;
  const inputSame = a.execution_provenance.input_canonical
                 === b.execution_provenance.input_canonical;
  // and the identity function must be blind to the difference
  const mk = (side) => caseEvidenceId({ case_index: 0, assignment: inputs,
    assignment_sem_id: "asgn-x", source_value: 5, source_sides_agree: true,
    lhs: side, rhs: side, equality: {}, case_evidence_id: null });
  const idsEqual = mk(a) === mk(b);
  if (!(evidenceIdentical && sessionsDiffer && artifactSame && inputSame && idsEqual)) {
    fail = true;
    console.log(`FAIL  identity-excludes-provenance  evidence identical ${evidenceIdentical}, ` +
      `sessions differ ${sessionsDiffer}, artifact same ${artifactSame}, input same ${inputSame}, ` +
      `ids equal ${idsEqual}`);
  } else console.log(`PASS  identity-excludes-provenance  two LAUNCHES of the same binary on the ` +
    `same input: every evidence field byte-identical, same executable_artifact_id, same ` +
    `input_canonical, DIFFERENT executor_session_id, and caseEvidenceId blind to the difference — ` +
    `so a proof identity does not move because somebody ran the producer twice`);
}

console.log("═".repeat(96));
/* DERIVED. This line hand-listed thirteen forgeries by name, and P1.1 added six
   more — so it would have described a run of nineteen cases as a run of
   thirteen, which is B6.1's finding: the summary lands where a reader who runs
   nothing else sees only it. Every forgery names itself now. */
const byCode = new Map();
for (const c of CASES) byCode.set(c.wants, (byCode.get(c.wants) ?? 0) + 1);
console.log(fail
  ? `PROOF-FORGERIES: FAIL — ${ran} cases ran, at least one forgery was not caught by its own check`
  : `PROOF-FORGERIES: PASS — ${ran}/${ran}. The honest bundle verifies; its evidence identity is blind ` +
    `to which LAUNCH produced it while its provenance is not, which is the whole content of keeping ` +
    `them apart; and ${CASES.length} forged bundles are each refused BY THE CHECK WHOSE ` +
    `SUBJECT THEY ARE rather than by a neighbour, across ${byCode.size} distinct refusal codes ` +
    `[${[...byCode].map(([k, n]) => `${k}×${n}`).join(", ")}]: ` +
    `${CASES.map((c) => c.name).join(", ")}. THE THREE THAT NO HASH CAN CATCH: the aggregate ` +
    `RESEALED around its own duplicate, the domain widened WITH its id and expected count updated, ` +
    `and the bounded scope rewritten to an unbounded one WITH the claim identity recomputed — all ` +
    `three internally consistent at every digest, all three refused by derivation. Every mutation is ` +
    `digested before and after, so a forgery that forged nothing FAILS rather than counting`);
process.exit(fail ? 1 : 0);
