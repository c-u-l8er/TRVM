/* ═══════════════════════════════════════════════════════════════════════════
   compose_forgeries.mjs — v0.1.0 — P3's NON-VACUITY
   law:proof.bounded-claim@1 · law:evidence.instrument-nonvacuity@1

   P1's forgeries attacked coverage and reseal. P2's attacked the branch
   structure and, after P2.1, the absence contract itself. P3's attack the JOINT
   — the place where one proof object becomes another proof object's evidence —
   and the shapes are new because the joint is new:

     · a CITATION THAT WENT STALE: the child was resealed coherently after the
       parent cited it, so both artifacts are internally perfect and the parent
       is about a claim that no longer exists;
     · a CROSS-WIRE: this claim, that evidence — the two halves of a citation
       belonging to different children;
     · ONE CHILD DOING TWO JOBS: `A ∧ A` presented as a two-operand conjunction;
     · A VALID PARENT OVER AN INVALID CHILD: every hash in the parent correct,
       and the child's own checker refuses it;
     · A CONJUNCTION MISSING AN OPERAND;
     · and THE ONE THAT JUSTIFIES THE WHOLE DESIGN: a child whose CLAIM changes
       while its AGGREGATE does not. A composition over bare aggregate ids would
       accept it. The certificate id moves and P3 refuses it.

   Each forgery must draw ITS OWN refusal code, and every mutation is digested
   before and after so a forgery that forged nothing FAILS rather than counting.
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { checkComposeBundle } from "./compose_check.mjs";
import { composedClaimSemId, composeAggregateId, operandFor } from "./compose_bundle.mjs";
import { verifiedClaimSemId } from "./certificate.mjs";
import { domainClaimSemId, domainSemId2 } from "./domain_bundle.mjs";
import { aggregateId } from "./proof_bundle.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const BUNDLE = process.argv[2] ?? join(HERE, "compose_bundle.json");
const digest = (o) => createHash("sha256").update(JSON.stringify(o)).digest("hex");
const clone = (o) => JSON.parse(JSON.stringify(o));
const P1 = "TRVM-BOUNDED-PROOF-v1";
const P2 = "TRVM-BOUNDED-DOMAIN-PROOF-v1";
const childOf = (b, proto) => b.children.find((c) => c.bundle.protocol === proto);
const operandOf = (b, proto) => b.claim.operands.find((o) => o.protocol === proto);
/** Reseal the PARENT as coherently as a forger could: claim id and aggregate.
 *  A forgery that only survives because the parent forgot to reseal is testing
 *  nothing about composition. */
const resealParent = (b) => {
  b.claim.composed_claim_sem_id =
    composedClaimSemId(b.claim.connective, b.claim.scope, b.claim.operands);
  b.aggregate.operands = b.claim.operands.length;
  b.aggregate.children_carried = b.children.length;
  b.aggregate.aggregate_id = composeAggregateId(b.aggregate);
  return b;
};

let ran = 0, fail = false;
const CASES = [];
const F = (name, wants, mutate, why) => CASES.push({ name, wants, mutate, why });

/* ── 1. THE STALE CITATION ───────────────────────────────────────────────── */
F("stale-citation-after-coherent-child-reseal", "compose-certificate-stale", (b) => {
  const child = childOf(b, P2).bundle;
  // the child's scope is rewritten and the child reseals its OWN claim id, so
  // nothing inside the child is inconsistent. The parent's citation is not
  // touched — it does not need to be; it was true when it was written.
  child.claim.scope = { ...child.claim.scope, generalizes_beyond_domain: true };
  child.claim.domain_claim_sem_id = domainClaimSemId(
    child.claim.program_sem_id, child.claim.domain_sem_id,
    child.claim.scope, child.claim.refusal_contract);
  resealParent(b);
}, "the child moved under the citation. Both artifacts are internally coherent and the parent is " +
   "about a claim that no longer exists — which is the failure mode a citation format exists to " +
   "have. The recomputed certificate id no longer matches, and the child's own checker also " +
   "refuses the rewritten scope");

/* ── 2. THE CROSS-WIRE ───────────────────────────────────────────────────── */
F("claim-and-aggregate-cross-wired", "compose-citation-cross-wired", (b) => {
  const o1 = operandOf(b, P1), o2 = operandOf(b, P2);
  // this claim, that evidence — and the certificate id recomputed over the
  // mixture, so the id itself is perfectly self-consistent.
  o1.aggregate_id = o2.aggregate_id;
  o1.verified_claim_sem_id = verifiedClaimSemId({
    protocol: o1.protocol, claim_sem_id: o1.claim_sem_id,
    aggregate_id: o1.aggregate_id, chain_ids: childOf(b, P1).bundle.chain_ids });
  childOf(b, P1).verified_claim_sem_id = o1.verified_claim_sem_id;
  resealParent(b);
}, "P1's claim cited against P2's evidence. The certificate id is recomputed over the mixture so " +
   "it is internally right; what refuses it is the FIELD-BY-FIELD comparison against the carried " +
   "child, because agreeing on a hash is not agreeing about what the hash names");

/* ── 3. ONE CHILD DOING TWO JOBS ─────────────────────────────────────────── */
F("duplicate-child-standing-in-for-a-conjunction", "compose-operand-duplicated", (b) => {
  const keep = childOf(b, P1);
  b.claim.operands = [clone(operandOf(b, P1)), clone(operandOf(b, P1))];
  b.children = [clone(keep)];
  resealParent(b);
}, "`A ∧ A` presented as a two-operand conjunction carrying one child. Distinctness is by " +
   "CERTIFICATE id rather than by protocol, because two different P1 claims are a perfectly good " +
   "conjunction and this is not");

/* ── 4. A VALID PARENT OVER AN INVALID CHILD ─────────────────────────────── */
F("valid-parent-over-a-child-its-own-checker-refuses", "compose-child-refused", (b) => {
  // one case of the P2 child loses its refusal witness. Every hash in the
  // PARENT is correct and untouched; the citation is not stale, because the
  // child's claim id and aggregate id have not moved.
  const child = childOf(b, P2).bundle;
  const c = child.cases.find((x) => x.disposition === "REFUSED");
  c.refusal.refusal_witness = { minuend: 7, subtrahend: 1 };
}, "the parent is impeccable and the child is not. Nothing the parent knows about could catch this " +
   "— the citation is over the claim and the aggregate, and neither moved. It is caught because the " +
   "parent RUNS the child's own checker rather than trusting a name");

/* ── 5. THE CONJUNCTION LOSES AN OPERAND ─────────────────────────────────── */
F("conjunction-missing-an-operand", "compose-child-missing", (b) => {
  b.claim.operands = [clone(operandOf(b, P1))];
  resealParent(b);
}, "a parent that says `A` while carrying the evidence for A and B. The claim id is resealed over " +
   "the shortened operand list, so the artifact is coherent — and a carried child that nothing " +
   "cites is refused, because a conjunction is over exactly its operands");

/* ── 6. THE ONE THAT JUSTIFIES THE DESIGN ────────────────────────────────── */
F("child-claim-changed-aggregate-untouched", "compose-certificate-stale", (b) => {
  const child = childOf(b, P2).bundle;
  // the child now claims a WIDER domain. Its aggregate — case ids, counts,
  // measurements, verdict — is not touched at all, and neither is its
  // aggregate_id. A composition citing bare aggregate ids would see nothing.
  child.claim.variable_domains = { x: [0, 1, 2, 3, 4], y: [0, 1, 2, 3] };
  child.claim.domain_sem_id = domainSemId2(child.claim.variable_domains);
  child.claim.expected_cases = 20;
  child.claim.domain_claim_sem_id = domainClaimSemId(
    child.claim.program_sem_id, child.claim.domain_sem_id,
    child.claim.scope, child.claim.refusal_contract);
  resealParent(b);
}, "THE MEASUREMENT BEHIND `NO BARE AGGREGATE IDS`. The child's claim is now about twenty " +
   "assignments and its aggregate_id is byte-identical, because an aggregate commits to what was " +
   "MEASURED and not to what was CLAIMED. A citation over aggregate ids alone would accept this " +
   "silently; the claim-qualified certificate id moves and the citation goes stale");

/* ── 7. AN UNCITED CHILD SMUGGLED IN ─────────────────────────────────────── */
F("extra-child-carried-uncited", "compose-child-missing", (b) => {
  const extra = clone(childOf(b, P1));
  extra.verified_claim_sem_id = "vclaim-" + "0".repeat(64);
  b.children.push(extra);
  resealParent(b);
}, "a child bundle riding along that no operand cites. Harmless today and exactly how a later " +
   "reader ends up believing the parent proved three things — the children carried and the " +
   "operands cited must be the same set in both directions");

/* ── 8. THE PARENT PROMOTES A REFUSED CHILD BY ARITHMETIC ────────────────── */
F("aggregate-claims-more-verified-than-there-are", "compose-count-inconsistent", (b) => {
  b.aggregate.children_verified = 99;
  b.aggregate.aggregate_id = composeAggregateId(b.aggregate);
}, "the aggregate's own count, resealed. P1 refused `64/64 over 63 unique assignments` by " +
   "recomputing rather than reading, and the composed aggregate gets the same treatment");

/* ── 9. THE PARENT SAYS IT FLATTENED ITS CHILDREN ────────────────────────── */
F("parent-claims-to-have-rederived-leaves", "compose-count-inconsistent", (b) => {
  b.aggregate.leaf_receipts_rederived_by_parent = 138;
  b.aggregate.aggregate_id = composeAggregateId(b.aggregate);
}, "the architecture as an assertion the artifact can fail. A composition that re-derives its " +
   "children's receipts is a bigger leaf wearing a composition's name, and the number is in the " +
   "aggregate so that claiming it costs a refusal");

/* ── 10. A CONNECTIVE THE CHECKER CANNOT EVALUATE ────────────────────────── */
F("connective-swapped-to-disjunction", "compose-connective-unsupported", (b) => {
  b.claim.connective = "DISJUNCTION";
  resealParent(b);
}, "a parent asserting a weaker theorem than its evidence supports would be sound; asserting one " +
   "this checker has no rule for is not. The connective set is the checker's, and an unimplemented " +
   "connective is a REFUSAL rather than a default to conjunction");

/* ── 11. THE COMPOSED SCOPE REWRITTEN ────────────────────────────────────── */
F("compose-scope-claims-the-parent-verified-the-leaves", "compose-scope-mismatch", (b) => {
  b.claim.scope = { ...b.claim.scope, parent_rederives_leaf_evidence: true,
                    children_rechecked_by_their_own_checkers: false };
  resealParent(b);
}, "P1.1's ruling arriving at the third artifact: the machine-readable scope must be the scope the " +
   "CHECKER implements, and a composed certificate claiming it verified the leaves itself is " +
   "claiming a different architecture");

/* ── 12. A CHILD PROTOCOL WITH NO CHECKER ────────────────────────────────── */
F("child-protocol-with-no-checker-here", "compose-child-protocol-unsupported", (b) => {
  const child = childOf(b, P2);
  child.bundle.protocol = "TRVM-BOUNDED-DOMAIN-PROOF-v2";
  resealParent(b);
}, "a child from a protocol this checker does not implement. The alternative to refusing is " +
   "skipping it, and a conjunction that silently drops an operand it could not judge is the " +
   "quietest possible way to prove less than you claim");

/* ── P3.1: THE GRAMMAR ATTACKS, WHICH NEED NO UNDERSTANDING OF THE EVIDENCE ─
   Everything above changes something the checker reads. These add vocabulary it
   never agreed to, and against the shipped P3 all four returned VERIFIED. */
F("scope-declares-itself-transitive", "compose-vocabulary-unknown", (b) => {
  b.claim.scope = { ...b.claim.scope, transitive: true, parent_may_be_cited_as_warrant: true };
  resealParent(b);
}, "GPT's attack 3. The scope this checker implements says the opposite in the field beside it, and " +
   "scope_notes said `NOT transitive` in plain English — and none of that mattered, because the " +
   "comparison iterated the CHECKER's keys and never asked what else was there");

F("claim-gains-warrant-vocabulary-unsealed", "compose-vocabulary-unknown", (b) => {
  b.claim.transitive = true;
  b.claim.parent_may_be_cited_as_warrant = true;
  // NOT resealed: composed_claim_sem_id does not bind these, because they are
  // not in the record it hashes. That is the attack — the claim object itself
  // had no vocabulary, so a semantic assertion could be added beside the ones
  // that are checked without moving a single identity.
}, "GPT's attack 4, and the sharpest of the set: the artifact asserts it may be cited as a warrant, " +
   "the claim identity does not move, and the composition verifies. An unbound field next to bound " +
   "ones is not a smaller problem than a forged bound one — it is a larger one, because nothing " +
   "even has to be resealed");

F("operand-claims-to-entail-everything", "compose-vocabulary-unknown", (b) => {
  b.claim.operands[0].is_warrant = true;
  b.claim.operands[0].entails = "EVERYTHING";
  resealParent(b);
}, "GPT's attack 5. A citation is four strings and nothing else; an operand that carries a fifth is " +
   "a citation making a claim of its own");

F("child-verdicts-all-flipped-and-resealed", "compose-count-inconsistent", (b) => {
  for (const k of Object.keys(b.aggregate.child_verdicts)) b.aggregate.child_verdicts[k] = "REFUSED";
  b.aggregate.aggregate_id = composeAggregateId(b.aggregate);
}, "GPT's attack 7, and the cleanest witness in the tree for `authentication is not verification`: " +
   "a field inside the aggregate hash, recording the verdict of every child, which the checker " +
   "computed for itself and then never compared. Every value flipped, resealed, VERIFIED");

F("annotations-carry-a-child-bundle", "compose-vocabulary-unknown", (b) => {
  b.annotations = { ...b.annotations, smuggled: clone(b.children[0].bundle.aggregate) };
}, "the second trust domain, bounded where it is cheap to bound it");

if (!existsSync(BUNDLE)) { console.log(`COMPOSE-FORGERIES: FAIL — no composed certificate at ${BUNDLE}`); process.exit(1); }
const HONEST = JSON.parse(readFileSync(BUNDLE, "utf8"));

{
  ran++;
  const r = checkComposeBundle(clone(HONEST));
  if (r.ok !== true) { fail = true;
    console.log(`FAIL  honest-composition-verifies  ${r.refusals.slice(0, 3).map((x) => x.code + ": " + x.detail).join(" | ")}`);
  } else console.log(`PASS  honest-composition-verifies  ${r.measured.operands}-operand ` +
    `${HONEST.claim.connective}, ${r.measured.children_verified} children VERIFIED by their own ` +
    `checkers, ${r.measured.leaf_receipts_rederived_here} leaf receipts re-derived by the parent`);
}

/* ── THE POSITIVE PROPERTY P3 EXISTS FOR ──────────────────────────────────
   Not a forgery: the direct measurement that a bare aggregate id is not a
   citation. This is why the composition format is claim-qualified, and it is
   stated in numbers rather than in a header. */
{
  ran++;
  const child = clone(childOf(HONEST, P2).bundle);
  const aggBefore = child.aggregate.aggregate_id;
  const certBefore = verifiedClaimSemId({ protocol: child.protocol,
    claim_sem_id: child.claim.domain_claim_sem_id,
    aggregate_id: child.aggregate.aggregate_id, chain_ids: child.chain_ids });
  child.claim.variable_domains = { x: [0, 1, 2, 3, 4, 5], y: [0, 1, 2, 3] };
  child.claim.domain_sem_id = domainSemId2(child.claim.variable_domains);
  child.claim.domain_claim_sem_id = domainClaimSemId(
    child.claim.program_sem_id, child.claim.domain_sem_id,
    child.claim.scope, child.claim.refusal_contract);
  const aggAfter = aggregateId(child.aggregate);
  const certAfter = verifiedClaimSemId({ protocol: child.protocol,
    claim_sem_id: child.claim.domain_claim_sem_id,
    aggregate_id: child.aggregate.aggregate_id, chain_ids: child.chain_ids });
  if (!(aggBefore === aggAfter && certBefore !== certAfter)) {
    fail = true;
    console.log(`FAIL  bare-aggregate-id-is-not-a-citation  agg ${aggBefore === aggAfter ? "held" : "MOVED"}, ` +
      `cert ${certBefore === certAfter ? "HELD" : "moved"}`);
  } else console.log(`PASS  bare-aggregate-id-is-not-a-citation  the child's claim changes from 16 ` +
    `assignments to 24 and its aggregate_id ${aggBefore.slice(0, 16)}… is BYTE-IDENTICAL, because ` +
    `an aggregate commits to what was MEASURED and not to what was CLAIMED. The claim-qualified ` +
    `certificate id moves ${certBefore.slice(0, 18)}… → ${certAfter.slice(0, 18)}…. That is the ` +
    `whole reason P3 does not compose over aggregate ids`);
}

/* And the other half of a citable identity: rewording what is NOT bound must
   leave it alone, or every improvement to the prose breaks every citation. */
{
  ran++;
  const child = clone(childOf(HONEST, P2).bundle);
  const before = verifiedClaimSemId({ protocol: child.protocol,
    claim_sem_id: child.claim.domain_claim_sem_id,
    aggregate_id: child.aggregate.aggregate_id, chain_ids: child.chain_ids });
  child.claim.scope_notes = { established: "reworded entirely", not_claimed: ["and shortened"] };
  child.informational = { note: "rewritten" };
  for (const c of child.cases) if (c.disposition === "REFUSED")
    c.refusal.notes = { why: "reworded too" };
  const after = verifiedClaimSemId({ protocol: child.protocol,
    claim_sem_id: child.claim.domain_claim_sem_id,
    aggregate_id: child.aggregate.aggregate_id, chain_ids: child.chain_ids });
  if (before !== after) { fail = true;
    console.log(`FAIL  rewording-notes-does-not-break-a-citation  ${before.slice(0, 20)} → ${after.slice(0, 20)}`);
  } else console.log(`PASS  rewording-notes-does-not-break-a-citation  scope_notes, informational ` +
    `and every refusal's prose rewritten; verified_claim_sem_id ${before.slice(0, 20)}… HOLDS. A ` +
    `certificate identity that moved when somebody improved a sentence would make every citation in ` +
    `the tree a maintenance hazard`);
}

for (const c of CASES) {
  ran++;
  const b = clone(HONEST);
  const before = digest(b);
  try { c.mutate(b); } catch (e) { fail = true; console.log(`FAIL  ${c.name}  (forgery threw: ${e.message})`); continue; }
  if (digest(b) === before) { fail = true; console.log(`FAIL  ${c.name}  (VACUOUS — the forgery changed nothing)`); continue; }
  const r = checkComposeBundle(b);
  const codes = [...new Set(r.refusals.map((x) => x.code))];
  if (r.ok) { fail = true; console.log(`FAIL  ${c.name}  (ACCEPTED — the checker verified a forged composition)`); }
  else if (!codes.includes(c.wants)) { fail = true;
    console.log(`FAIL  ${c.name}  (WRONG REFUSAL — wanted ${c.wants}, got [${codes.join(", ")}])`); }
  else console.log(`PASS  ${c.name.padEnd(48)} → ${c.wants}` +
    (codes.length > 1 ? `  (+${codes.length - 1} other code(s))` : ""));
}

console.log("═".repeat(96));
const byCode = new Map();
for (const c of CASES) byCode.set(c.wants, (byCode.get(c.wants) ?? 0) + 1);
console.log(fail
  ? `COMPOSE-FORGERIES: FAIL — ${ran} cases ran, at least one forgery was not caught by its own check`
  : `COMPOSE-FORGERIES: PASS — ${ran}/${ran}. The honest composition verifies, a bare aggregate id ` +
    `is MEASURED not to identify the claim it proved, rewording unbound prose is measured NOT to ` +
    `break a citation, and ${CASES.length} forged compositions are each refused BY THE CHECK WHOSE ` +
    `SUBJECT THEY ARE across ${byCode.size} distinct codes ` +
    `[${[...byCode].map(([k, n]) => `${k}×${n}`).join(", ")}]: ${CASES.map((c) => c.name).join(", ")}. ` +
    `THE SHAPES THAT ARE NEW AT THE JOINT: a citation that went stale because the child was ` +
    `resealed coherently underneath it; a cross-wire carrying this claim against that evidence with ` +
    `the certificate id recomputed over the mixture; one child standing in for both halves of a ` +
    `conjunction; an impeccable parent over a child its OWN checker refuses, which nothing in the ` +
    `parent could have caught and which is why the citation is not treated as a warrant; and a ` +
    `child whose CLAIM moved while its AGGREGATE did not, which a composition over bare aggregate ` +
    `ids would have accepted in silence`);
process.exit(fail ? 1 : 0);
