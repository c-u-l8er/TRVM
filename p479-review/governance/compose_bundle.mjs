/* ═══════════════════════════════════════════════════════════════════════════
   compose_bundle.mjs — v0.1.0 — P3, THE FIRST COMPOSED PROOF OBJECT
   law:proof.bounded-claim@1

   P1 is a positive bounded equality. P2 is a bounded compiler-domain
   certificate whose refusals are typed evidence. Both are LEAVES: each ends in
   an aggregate over hundreds of low-level receipts, and each is checked by
   walking every one of them.

   THE QUESTION P3 ASKS IS WHETHER A VERIFIED TRVM PROOF CAN BE AN INPUT TO
   ANOTHER TRVM PROOF WITHOUT BEING FLATTENED BACK INTO ITS RECEIPTS.

       128 films + 64 cases  →  P1 checker  →  certificate A
        10 films +  6 typed refusals  →  P2 checker  →  certificate B
                      certificate A ∧ certificate B
                            ↓
                     P3 composition checker
                            ↓
                      composed certificate C

   That is a proof DAG rather than one enormous proof tree, and it is the whole
   content. THE THEOREM IS DELIBERATELY TRIVIAL: a conjunction. P3 claims that
   both cited child claims hold, and nothing more. Inventing a hard inference
   rule here would confuse two questions — whether composition WORKS and whether
   this particular inference is SOUND — and only the first is being tested.

   WHAT P3 DOES NOT CITE: bare `aggregate_id`s. See `certificate.mjs` for the
   measurement — P1's aggregate id is BYTE-IDENTICAL under a completely
   different proposition, because an aggregate commits to what was measured and
   not to what was claimed. A composition over bare aggregate ids would be
   citing "sixty-four cases went like this" and calling it "distributivity over
   {0,1,2,3}³". So an operand cites a `verified_claim_sem_id` binding protocol,
   CLAIM identity, aggregate identity and chain ids together.

   AND P3 CARRIES ITS CHILDREN. There is no registry saying "checker Y already
   accepted certificate X", so a citation is not yet a warrant and this artifact
   does not pretend otherwise: the full P1 and P2 bundles travel inside it, and
   `compose_check.mjs` dispatches each to ITS OWN checker. The parent verifies
   the conjunction of two verdicts it did not itself compute from receipts —
   and measures that it re-derived none.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { canonicalBytes } from "./derive_protocol.mjs";
import { verifiedClaimSemId, certificateOf } from "./certificate.mjs";
import { checkBundle } from "./proof_check.mjs";
import { checkDomainBundle } from "./domain_check.mjs";

export const COMPOSE_BUNDLE_VERSION = "0.1.0";
export const COMPOSE_PROTOCOL = "TRVM-COMPOSED-PROOF-v1";
const H = (s) => createHash("sha256").update(s).digest("hex");
const HERE = dirname(fileURLToPath(import.meta.url));

/** THE PRODUCER'S table of child protocols. `compose_check.mjs` declares its
 *  OWN and does not import this one — P1.1's ruling, and the reason it matters
 *  here is that `claim_field` is the answer to "where does this protocol keep
 *  the thing a citation is ABOUT". A checker that let the artifact answer that
 *  would let the artifact choose which of its own hashes to be judged on. */
export const CHILD_PROTOCOLS = Object.freeze({
  "TRVM-BOUNDED-PROOF-v1": Object.freeze({
    claim_field: "bounded_claim_sem_id", check: checkBundle, source: "proof_bundle.json" }),
  "TRVM-BOUNDED-DOMAIN-PROOF-v1": Object.freeze({
    claim_field: "domain_claim_sem_id", check: checkDomainBundle, source: "domain_bundle.json" }),
});

export const COMPOSE_CLAIM_SCOPE = Object.freeze({
  kind: "COMPOSED_VERIFIED_CLAIM_CONJUNCTION",
  quantifier: "OVER_CITED_CHILD_CERTIFICATES",
  generalizes_beyond_children: false,
  children_rechecked_by_their_own_checkers: true,
  parent_rederives_leaf_evidence: false,
});
export const COMPOSE_CLAIM_SCOPE_NOTES = Object.freeze({
  established: "each cited child certificate names a claim, an evidence aggregate and a compiler " +
    "chain together; each child bundle is carried whole and re-checked by the checker of its own " +
    "protocol; and this artifact asserts the CONJUNCTION of exactly those child claims.",
  not_claimed: Object.freeze([
    "NOT a new mathematical result — the conjunction of two verified claims is the weakest " +
      "interesting composition and is chosen for exactly that reason",
    "NOT a trust registry: a verified_claim_sem_id is a NAME, not a warrant, and this checker " +
      "re-runs both child checkers rather than believing a citation",
    "NOT a claim that the parent verified the children's receipts — it deliberately did not, and " +
      "the measurement `leaf_receipts_rederived_by_parent = 0` is the point of the artifact",
    "NOT transitive: nothing here says a composed certificate may itself be cited by a fourth " +
      "artifact, and no test in this tree has tried it",
  ]),
});
export const CONNECTIVE = "CONJUNCTION";

/** The composed claim's identity: the connective, the quantifier semantics, and
 *  the OPERAND LIST — so a parent that swapped one operand for another is a
 *  different claim even when both operands are real certificates. */
export const composedClaimSemId = (connective, scope, operands) =>
  "cclaim-" + H(COMPOSE_PROTOCOL + "|" + canonicalBytes({
    protocol: COMPOSE_PROTOCOL, connective, scope, operands }));

export const composeAggregateId = (agg) => {
  const { aggregate_id, ...rest } = agg;
  return "cagg-" + H(COMPOSE_PROTOCOL + "|" + canonicalBytes(rest));
};

/** One operand: the citation, and nothing else. It is deliberately NOT a copy
 *  of the child's claim record — a citation that restated the proposition would
 *  give a forger a second place to say what was proved. */
export function operandFor(bundle, claim_field) {
  const c = certificateOf(bundle, claim_field);
  return {
    protocol: c.protocol,
    claim_sem_id: c.claim_sem_id,
    aggregate_id: c.aggregate_id,
    verified_claim_sem_id: verifiedClaimSemId(c),
  };
}

export function buildComposeBundle(children) {
  /* THE PRODUCER CHECKS ITS OWN CHILDREN. It has to: a conjunction of two
     claims is only worth stating if both hold, and a producer that asserted it
     without looking would be minting the exact citation the checker exists to
     distrust. The checker repeats all of it independently. */
  const operands = [], carried = [], verdicts = {};
  for (const child of children) {
    const spec = CHILD_PROTOCOLS[child.protocol];
    if (!spec) throw new Error("compose-bundle-unknown-child-protocol: " + child.protocol);
    const r = spec.check(child);
    if (!(r.ok === true && r.verdict === "VERIFIED"))
      throw new Error(`compose-bundle-child-refused: ${child.protocol} → ` +
        (r.refusals ?? []).map((x) => x.code).join(", "));
    const op = operandFor(child, spec.claim_field);
    operands.push(op);
    carried.push({ verified_claim_sem_id: op.verified_claim_sem_id, bundle: child });
    verdicts[op.verified_claim_sem_id] = r.verdict;
  }
  const aggregate = {
    operands: operands.length,
    children_carried: carried.length,
    children_verified: Object.values(verdicts).filter((v) => v === "VERIFIED").length,
    child_verdicts: verdicts,
    // MEASURED IN THE CHECKER, declared here: this producer read no film and
    // re-derived no receipt of its own either. Both sides of the composition
    // treat a child as an object with a checker, not as a pile of receipts.
    leaf_receipts_rederived_by_parent: 0,
    composed_verdict: "PENDING",
    aggregate_id: null,
  };
  aggregate.composed_verdict =
    aggregate.children_verified === aggregate.operands && aggregate.operands > 0
      ? "VERIFIED" : "REFUSED";
  aggregate.aggregate_id = composeAggregateId(aggregate);
  return {
    type: "ComposedProofCertificate",
    protocol: COMPOSE_PROTOCOL,
    version: COMPOSE_BUNDLE_VERSION,
    claim: {
      // NO `statement`. P3.1: a composed certificate that named its own theorem
      // would be the display lie one artifact up, and the checker renders the
      // conjunction from the operands it actually verified.
      connective: CONNECTIVE,
      scope: COMPOSE_CLAIM_SCOPE,
      operands,
      composed_claim_sem_id: composedClaimSemId(CONNECTIVE, COMPOSE_CLAIM_SCOPE, operands),
    },
    children: carried,
    aggregate,
    /* THE SECOND TRUST DOMAIN — P3.1. No identity reaches it, nothing reads
       it, and the checker's only duty is to say what may sit in it. */
    annotations: {
      note: "NON-AUTHORITATIVE — nothing in this record is hashed, checked, or established",
      generator: "compose_bundle.mjs v" + COMPOSE_BUNDLE_VERSION,
      statement: operands.map((o) => `VERIFIED(${o.protocol})`).join(" AND "),
      scope_notes: COMPOSE_CLAIM_SCOPE_NOTES,
    },
  };
}

const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN) {
  const paths = Object.values(CHILD_PROTOCOLS).map((s) => join(HERE, s.source));
  for (const p of paths) if (!existsSync(p)) {
    console.log(`compose_bundle: FAIL — no child bundle at ${p} (build P1 and P2 first).`);
    process.exit(1);
  }
  const children = paths.map((p) => JSON.parse(readFileSync(p, "utf8")));
  const b = buildComposeBundle(children);
  const out = join(HERE, "compose_bundle.json");
  writeFileSync(out, JSON.stringify(b, null, 1) + "\n");
  const a = b.aggregate;
  console.log(`compose_bundle v${COMPOSE_BUNDLE_VERSION} — ${a.operands}-operand ${CONNECTIVE}`);
  for (const o of b.claim.operands)
    console.log(`  ${o.protocol.padEnd(30)} claim ${o.claim_sem_id.slice(0, 20)}… ` +
      `agg ${o.aggregate_id.slice(0, 16)}… → ${o.verified_claim_sem_id.slice(0, 22)}…`);
  console.log(`  ${a.children_verified}/${a.operands} children VERIFIED by their own checkers ` +
    `→ ${a.composed_verdict}`);
  console.log(`  composed claim ${b.claim.composed_claim_sem_id}`);
  console.log(`  written to ${out}`);
}
