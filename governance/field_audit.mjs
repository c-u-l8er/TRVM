/* ═══════════════════════════════════════════════════════════════════════════
   field_audit.mjs — v0.2.0 — EVERY FIELD IS DERIVED, CHECKED, OR NON-AUTHORITATIVE
   law:proof.semantic-vocabulary-closed@1 · law:evidence.instrument-nonvacuity@1

   `aggregate.nested_verdict` was in P4.1's required grammar and inside
   `aggregate_id`, and no checker ever read it. Set it to `"REFUSED"`, reseal,
   and the nested checker answered ok:true / VERIFIED / zero refusals over an
   artifact that said of itself that it was refused.

   That is B6.3 for the thirteenth time — *a hashed field is not evidence merely
   because it is hashed* — and it happened in a protocol written two rounds
   after the law that forbids it. The repair is one comparison. The interesting
   part is that it was found by hand, again, and the twelve before it were found
   by hand too.

   SO THIS FILE IS THE SWEEP. The denominator is the checker's OWN grammar, so a
   field added to any record is a field this audit immediately demands an answer
   about. Every field is classified exactly once:

       DERIVED       the checker computes this value itself and compares
       CHECKED       the checker compares it against a value it declares
       NON_AUTHORITATIVE  its CONTENT establishes nothing — though the envelope
                          is still protocol-shaped and structurally validated,
                          which is why it is not called NON_SEMANTIC

   AND THIS GATE'S DENOMINATOR IS THE CHECKER'S OWN GRAMMAR, WHICH IS NO LONGER
   SUFFICIENT ON ITS OWN. Delete a field from the checker, from the check that
   enforced it and from the producer, and this audit reports 45/45 PASS while
   the protocol still has 46 fields — measured, not hypothesised.
   `spec_agreement.mjs` is the gate that catches that, by comparing the
   checker's declarations against a NORMATIVE schema the runtime does not
   import. The two are complementary: this one asks whether every implemented
   field establishes something; that one asks whether the implemented
   vocabulary is the protocol's.

   and the classification is not believed. Each field is MUTATED in the honest
   artifact, the parent's own identities are resealed around the mutation, and:

       DERIVED / CHECKED  →  the check MUST refuse
       NON_AUTHORITATIVE       →  the check MUST still verify

   The second half is the one that catches over-classification: declaring a
   field non-semantic to escape the audit fails immediately if anything reads
   it. There is no fourth category, and an unclassified field FAILS.
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { GRAMMAR, checkNestBundle } from "./nest_check.mjs";
import { buildDag, nestedClaimSemId, nestAggregateId, nestStructureSemId } from "./nest_bundle.mjs";
import { memoryStore } from "./cas.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const clone = (o) => JSON.parse(JSON.stringify(o));

/** THE CLASSIFICATION, DECLARED HERE AND COMPARED TO THE GRAMMAR. */
const PLANES = Object.freeze({
  bundle: { protocol: "CHECKED", claim: "DERIVED", chain_ids: "DERIVED",
            references: "DERIVED", aggregate: "DERIVED", structure: "DERIVED",
            type: "NON_AUTHORITATIVE", version: "NON_AUTHORITATIVE", annotations: "NON_AUTHORITATIVE" },
  claim: { connective: "CHECKED", scope: "CHECKED", operands: "DERIVED",
           nested_claim_sem_id: "DERIVED" },
  scope: { kind: "CHECKED", quantifier: "CHECKED", generalizes_beyond_children: "CHECKED",
           children_rechecked_by_their_own_checkers: "CHECKED",
           parent_rederives_leaf_evidence: "CHECKED" },
  operand: { protocol: "DERIVED", claim_sem_id: "DERIVED", aggregate_id: "DERIVED",
             verified_claim_sem_id: "DERIVED" },
  references: { contract: "CHECKED", operands: "DERIVED" },
  reference_contract: { resolution: "CHECKED", wire: "CHECKED", address_is_a_warrant: "CHECKED" },
  reference: { verified_claim_sem_id: "DERIVED", artifact_root: "DERIVED" },
  chain_ids: { leaf_chains: "DERIVED" },
  aggregate: { operands: "DERIVED", child_verdicts: "DERIVED",
               leaf_receipts_rederived_by_parent: "DERIVED", films_replayed_by_parent: "DERIVED",
               nested_verdict: "DERIVED", aggregate_id: "DERIVED" },
  structure: { edges: "DERIVED", unique_artifacts: "DERIVED", max_depth_below: "DERIVED",
               bytes_if_inlined: "DERIVED", unique_bytes: "DERIVED",
               films_below_by_edge_multiplicity: "DERIVED", films_below_distinct: "DERIVED",
               cases_below_by_edge_multiplicity: "DERIVED", cases_below_distinct: "DERIVED",
               structure_sem_id: "DERIVED" },
});

/** Where each grammar record lives in the shipped artifact. */
const WHERE = Object.freeze({
  bundle: [], claim: ["claim"], scope: ["claim", "scope"], operand: ["claim", "operands", 0],
  references: ["references"], reference_contract: ["references", "contract"],
  reference: ["references", "operands", 0], chain_ids: ["chain_ids"],
  aggregate: ["aggregate"], structure: ["structure"],
});

const at = (o, path) => path.reduce((x, k) => x?.[k], o);
/** A perturbation that is detectable for any type, and never a no-op. */
const perturb = (v) => {
  if (typeof v === "number") return v + 1;
  if (typeof v === "boolean") return !v;
  if (typeof v === "string") return v + "-PERTURBED";
  if (v === null || v === undefined) return 0;
  if (Array.isArray(v)) return v.length > 1 ? v.slice(0, -1) : (v.length === 1 ? [] : [1]);
  return {};
};
const ID_FIELDS = new Set(["nested_claim_sem_id", "aggregate_id", "structure_sem_id"]);
/** Reseal as coherently as a forger could, and TOLERATE FAILURE: perturbing a
 *  whole sub-record can leave the artifact with no computable identity at all,
 *  which is a state a forger can also be in. The check must still refuse — and
 *  by a NAMED code, not by an exception. */
const tryTo = (f) => { try { f(); } catch { /* the forger could not reseal either */ } };
const reseal = (b, skip) => {
  if (skip !== "nested_claim_sem_id") tryTo(() => {
    b.claim.nested_claim_sem_id = nestedClaimSemId(b.claim.connective, b.claim.scope, b.claim.operands);
  });
  if (skip !== "aggregate_id") tryTo(() => { b.aggregate.aggregate_id = nestAggregateId(b.aggregate); });
  if (skip !== "structure_sem_id") tryTo(() => {
    b.structure.structure_sem_id = nestStructureSemId(b.structure);
  });
};

for (const f of ["proof_bundle.json", "domain_bundle.json"]) if (!existsSync(join(HERE, f))) {
  console.log(`FIELD-AUDIT: FAIL — no child bundle at ${f}`);
  process.exit(1);
}
const store = memoryStore(new Map());
const H = buildDag(JSON.parse(readFileSync(join(HERE, "proof_bundle.json"), "utf8")),
                   JSON.parse(readFileSync(join(HERE, "domain_bundle.json"), "utf8")),
                   { cas_dir: null, put: (_d, o) => store.put(o) });

let fail = false, checked = 0;
const tally = { DERIVED: 0, CHECKED: 0, NON_AUTHORITATIVE: 0 };

/* THE DENOMINATOR IS THE CHECKER'S OWN GRAMMAR. */
const rows = [];
for (const [record, spec] of Object.entries(GRAMMAR)) {
  const keys = [...(spec.required ?? []), ...(spec.optional ?? [])];
  for (const key of keys) {
    const plane = PLANES[record]?.[key];
    if (!plane) {
      fail = true;
      rows.push(`FAIL  ${record}.${key} is UNCLASSIFIED — every field of every semantic record ` +
        `must be DERIVED, CHECKED or NON_AUTHORITATIVE, and there is no fourth category`);
      continue;
    }
    const where = WHERE[record];
    if (!where) { fail = true; rows.push(`FAIL  ${record} has no location in the shipped artifact`); continue; }

    const b = clone(H.D);
    const target = at(b, where);
    if (target === undefined) { fail = true; rows.push(`FAIL  ${record}.${key}: no such record at [${where}]`); continue; }
    const before = JSON.stringify(target[key]);
    target[key] = perturb(target[key]);
    if (JSON.stringify(target[key]) === before) {
      fail = true; rows.push(`FAIL  ${record}.${key}: VACUOUS — the perturbation changed nothing`);
      continue;
    }
    reseal(b, ID_FIELDS.has(key) ? key : null);
    const r = checkNestBundle(b, { store });
    checked += 1; tally[plane] += 1;
    const want = plane === "NON_AUTHORITATIVE";
    if (r.ok !== want) {
      fail = true;
      rows.push(`FAIL  ${record}.${key} [${plane}] — perturbed and the checker answered ` +
        `${r.verdict}; ${want ? "a NON_AUTHORITATIVE field must change nothing" :
        "a DERIVED or CHECKED field must be refused"}` +
        (r.refusals.length ? ` [${[...new Set(r.refusals.map((x) => x.code))].join(", ")}]` : ""));
    } else {
      rows.push(`  ${plane.padEnd(12)} ${(record + "." + key).padEnd(46)} ` +
        (want ? "perturbed, still VERIFIED" :
          `refused [${[...new Set(r.refusals.map((x) => x.code))].join(", ")}]`));
    }
  }
}
for (const row of rows) console.log(row);
console.log("═".repeat(96));
console.log(fail
  ? `FIELD-AUDIT: FAIL — a field of this protocol is unclassified, or its classification is wrong`
  : `FIELD-AUDIT: PASS — ${checked}/${checked} fields, mechanically. The denominator is the ` +
    `CHECKER'S OWN GRAMMAR, so a field added to any record is a field this audit immediately ` +
    `demands an answer about: ${tally.DERIVED} DERIVED (the checker computes the value itself ` +
    `and compares), ${tally.CHECKED} CHECKED (compared against a value the checker declares and ` +
    `does not import), ${tally.NON_AUTHORITATIVE} NON_AUTHORITATIVE. NO FOURTH CATEGORY, and an ` +
    `unclassified field FAILS. Every one is PERTURBED in the honest artifact with the parent's ` +
    `identities resealed around the mutation: DERIVED and CHECKED must be REFUSED, and ` +
    `NON_AUTHORITATIVE must still VERIFY — which is the half that catches over-classification, ` +
    `because a field declared non-semantic to escape the audit fails the moment anything reads ` +
    `it. THIS EXISTS BECAUSE aggregate.nested_verdict WAS HASHED AND UNREAD: set to REFUSED and ` +
    `resealed, P4.1 answered VERIFIED over an artifact that said of itself that it was refused. ` +
    `That is the thirteenth instance of B6.3 in this line and the twelve before it were all ` +
    `found by hand`);
process.exit(fail ? 1 : 0);
