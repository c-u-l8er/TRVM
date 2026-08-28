/* ═══════════════════════════════════════════════════════════════════════════
   spec_agreement.mjs — v0.1.0 — THE SPEC IS ALLOWED TO DISAGREE
   law:proof.conformance-oracle-frozen@1 · law:evidence.instrument-nonvacuity@1

   `field_audit.mjs` takes its denominator from the CHECKER'S OWN GRAMMAR, and
   before a normative specification existed that was the correct source of
   truth. After freeze it is not sufficient, and the hole is exact: delete a
   field from the checker's grammar AND from the check that enforced it, and the
   audit's denominator shrinks from 46 to 45 and reports 45/45 PASS — while the
   protocol still has 46 fields.

   So this gate compares two INDEPENDENT declarations:

       docs/spec/proof-wire/schema/*.json        NORMATIVE, hand-owned
                    vs
       the checker's own exported constants      declared inside the checker

   AND THE RUNTIME MUST NOT IMPORT THE NORMATIVE SCHEMA. If both sides read one
   object they agree by construction and this file measures nothing — the same
   tautology `law:proof.semantic-vocabulary-closed@1` refuses one level down,
   where a checker reading its vocabulary out of the artifact proves only that
   the artifact agrees with itself.

   The two gates are complementary and neither replaces the other:

       spec_agreement  does the implementation have the vocabulary the
                       protocol says it has?
       field_audit     does every field it implements actually establish
                       something?
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, existsSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  GRAMMAR, IMPLEMENTED_CHILD_PROTOCOLS, IMPLEMENTED_CONNECTIVES, IMPLEMENTED_NEST_SCOPE,
  IMPLEMENTED_REFERENCE_CONTRACT, SHIPPED_POLICY,
} from "./nest_check.mjs";
import { NEST_PROTOCOL } from "./nest_bundle.mjs";
import { ARTIFACT_ROOT_PROTOCOL } from "./cas.mjs";
import { CERTIFICATE_PROTOCOL } from "./certificate.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const SCHEMA = join(HERE, "..", "docs", "spec", "proof-wire", "schema",
  "nested-composition-v2.json");

/** THE RUNTIME MUST NOT IMPORT THE NORMATIVE SCHEMA — asserted on the source of
 *  every file that is part of the checker, because "we did not import it" is
 *  the entire reason this comparison means anything. */
const RUNTIME = ["nest_check.mjs", "nest_bundle.mjs", "cas.mjs", "certificate.mjs", "schema.mjs"];

if (!existsSync(SCHEMA)) {
  console.log("SPEC-AGREEMENT: FAIL — no normative schema at docs/spec/proof-wire/schema/");
  process.exit(1);
}
const N = JSON.parse(readFileSync(SCHEMA, "utf8"));
const problems = [];
const same = (label, a, b) => {
  const A = JSON.stringify(a), B = JSON.stringify(b);
  if (A !== B) problems.push(`${label}: normative ${A} · implementation ${B}`);
};
const sortedKeys = (o) => Object.keys(o ?? {}).sort();

/* ── 1. THE RUNTIME DOES NOT READ THIS FILE ─────────────────────────────── */
for (const f of RUNTIME) {
  const p = join(HERE, f);
  if (!existsSync(p)) { problems.push(`runtime file ${f} is missing`); continue; }
  const src = readFileSync(p, "utf8");
  if (/proof-wire[\\/]schema/.test(src) || /nested-composition-v2\.json/.test(src))
    problems.push(`${f} REFERENCES the normative schema — the runtime must declare its own ` +
      `vocabulary, or this gate compares one object with itself`);
}

/* ── 2. GRAMMAR: exact key sets, record by record, both directions ───────── */
same("grammar record set", sortedKeys(N.grammar), sortedKeys(GRAMMAR));
for (const rec of sortedKeys(N.grammar)) {
  same(`grammar.${rec}.required`,
    [...(N.grammar[rec].required ?? [])].sort(), [...(GRAMMAR[rec]?.required ?? [])].sort());
  same(`grammar.${rec}.optional`,
    [...(N.grammar[rec].optional ?? [])].sort(), [...(GRAMMAR[rec]?.optional ?? [])].sort());
}

/* ── 3. CONSTANTS ───────────────────────────────────────────────────────── */
const C = N.constants;
same("constants.protocol", C.protocol, NEST_PROTOCOL);
same("constants.connectives", [...C.connectives].sort(), [...IMPLEMENTED_CONNECTIVES].sort());
same("constants.scope", C.scope, { ...IMPLEMENTED_NEST_SCOPE });
same("constants.reference_contract", C.reference_contract, { ...IMPLEMENTED_REFERENCE_CONTRACT });
same("constants.artifact_root_protocol", C.artifact_root_protocol, ARTIFACT_ROOT_PROTOCOL);
same("constants.certificate_protocol", C.certificate_protocol, CERTIFICATE_PROTOCOL);
same("constants.verifier_policy", C.verifier_policy, { ...SHIPPED_POLICY });
same("constants.child_protocols", sortedKeys(C.child_protocols),
  sortedKeys(IMPLEMENTED_CHILD_PROTOCOLS));
for (const p of sortedKeys(C.child_protocols)) {
  same(`child_protocols[${p}].claim_field`,
    C.child_protocols[p].claim_field, IMPLEMENTED_CHILD_PROTOCOLS[p]?.claim_field);
  same(`child_protocols[${p}].composed`,
    C.child_protocols[p].composed, IMPLEMENTED_CHILD_PROTOCOLS[p]?.composed);
}

/* ── 4. FIELD PLANES cover exactly the normative grammar ─────────────────── */
for (const rec of sortedKeys(N.grammar)) {
  const keys = [...(N.grammar[rec].required ?? []), ...(N.grammar[rec].optional ?? [])].sort();
  same(`field_planes.${rec} covers the grammar`, keys, sortedKeys(N.field_planes?.[rec]));
  for (const k of keys) {
    const plane = N.field_planes?.[rec]?.[k];
    if (!["DERIVED", "CHECKED", "NON_AUTHORITATIVE"].includes(plane))
      problems.push(`field_planes.${rec}.${k} is ${JSON.stringify(plane)}; the normative ` +
        `classification is DERIVED, CHECKED or NON_AUTHORITATIVE and there is no fourth category`);
  }
}

/* ── 5. REFUSAL CODES: the checker's header comment is prose, so the source of
       truth on the implementation side is the set of codes the checker can
       actually emit. Derived from its source by literal, which is the one place
       a string is the protocol rather than a description of one. ──────────── */
const src = readFileSync(join(HERE, "nest_check.mjs"), "utf8");
const emitted = [...new Set([...src.matchAll(/"(nest-[a-z0-9-]+)"/g)].map((m) => m[1]))].sort();
const declared = [...N.refusal_codes].sort();
const missing = declared.filter((c) => !emitted.includes(c));
const extra = emitted.filter((c) => !declared.includes(c));
if (missing.length) problems.push(`refusal codes in the spec that this checker never emits: ` +
  `${missing.join(", ")}`);
if (extra.length) problems.push(`refusal codes this checker emits that the spec does not declare: ` +
  `${extra.join(", ")}`);

for (const p of problems.slice(0, 15)) console.log(`  ${p}`);
console.log(problems.length === 0
  ? `SPEC-AGREEMENT: PASS — the normative schema and the checker's OWN declarations agree on ` +
    `${sortedKeys(N.grammar).length} record grammars, ` +
    `${Object.values(N.grammar).reduce((n, r) => n + r.required.length + r.optional.length, 0)} ` +
    `fields and their planes, ${declared.length} refusal codes, the scope, the reference contract, ` +
    `the child-protocol table, both domain-separation strings and all ` +
    `${Object.keys(N.constants.verifier_policy).length} verifier-policy values — AND THE RUNTIME ` +
    `DOES NOT IMPORT THE SCHEMA, asserted on the source of all ${RUNTIME.length} files, because ` +
    `two declarations that read one object agree by construction. This is what field_audit.mjs ` +
    `cannot do: deleting a field from the checker AND from the check that enforced it merely ` +
    `shrinks that audit's denominator to 45/45, while the protocol still has 46 fields`
  : `SPEC-AGREEMENT: FAIL — ${problems.length} disagreement(s) between the normative ` +
    `specification and the implementation. One of the two is wrong and the gate does not know ` +
    `which; that is the point of having two`);
process.exit(problems.length === 0 ? 0 : 1);
