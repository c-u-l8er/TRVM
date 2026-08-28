/* ═══════════════════════════════════════════════════════════════════════════
   nest_forgeries.mjs — v0.2.0 — P4.1's NON-VACUITY
   law:proof.reference-is-not-claim@1 · law:proof.verifier-policy-owned@1
   law:proof.canonical-wire@1 · law:proof.content-address-is-not-a-warrant@1
   law:evidence.instrument-nonvacuity@1

   P4's suite attacked the store and the address. P4.1's attacks the four things
   that round got wrong, each of which was reproduced against the shipped P4
   pack before a line was repaired:

     · THE ROOT WAS NOT A BYTE ADDRESS. It hashed the PARSED object, so pretty
       bytes and compact bytes resolved under one root — and a DUPLICATE
       `protocol` member, which `JSON.parse` silently resolves in favour of the
       last one, let hostile bytes be AUTHENTICATED as the honest artifact.
     · A PROSE EDIT RENAMED THE THEOREM. `artifact_root` sat inside
       `claim.operands` and therefore inside `nested_claim_sem_id`, so rewording
       one annotation on a leaf moved every ancestor's claim id.
     · THE DEPTH CEILING WAS THE CALLER'S. `{max_depth: 1000}` verified the
       40-deep chain the round shipped as its own positive witness.
     · AN UNTRUSTED CITATION STEERED A FILESYSTEM READ. `get("../proof_bundle")`
       returned 1.31 MB from outside the store.

   AND FOUR MEASUREMENTS THAT ARE NOT FORGERIES, because a property is not
   established by refusing its negation:

     · REFERENCE IS NOT CLAIM, as a positive: reword a leaf and watch the names
       hold while the addresses move.
     · DERIVATION REUSE IS OBSERVATIONALLY EQUIVALENT to recomputation — the
       verdict and the refusal set must be identical with the memo off.
     · a composed certificate was NOT CITABLE before P4.
     · a cycle was not sealable in a bounded experiment.
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { checkNestBundle, checkNestBytes, NEST_MAX_DEPTH, SHIPPED_POLICY } from "./nest_check.mjs";
import {
  NEST_PROTOCOL, CHILD_PROTOCOLS, buildNestBundle, buildDag,
  nestedClaimSemId, nestAggregateId, nestStructureSemId,
} from "./nest_bundle.mjs";
import {
  artifactRoot, memoryStore, canonicalWire, canonicalWireBytes, directoryStore,
} from "./cas.mjs";
import { verifiedClaimSemId, certificateOf } from "./certificate.mjs";
import { checkBundle } from "./proof_check.mjs";
import { caseEvidenceId, aggregateId } from "./proof_bundle.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const digest = (o) => createHash("sha256").update(JSON.stringify(o)).digest("hex");
const clone = (o) => JSON.parse(JSON.stringify(o));
const P1 = "TRVM-BOUNDED-PROOF-v1";

for (const f of ["proof_bundle.json", "domain_bundle.json"]) if (!existsSync(join(HERE, f))) {
  console.log(`NEST-FORGERIES: FAIL — no child bundle at ${f}`);
  process.exit(1);
}
const RAW_A = JSON.parse(readFileSync(join(HERE, "proof_bundle.json"), "utf8"));
const RAW_B = JSON.parse(readFileSync(join(HERE, "domain_bundle.json"), "utf8"));

/** A FORGER'S BUILD — leaf checkers that DERIVE the real measurements and then
 *  assert VERIFIED. Every count honest, the verdict a lie. Kept here rather
 *  than as a producer flag so the producer has no mode that mints unchecked
 *  certificates. */
const LYING = Object.freeze({
  ...CHILD_PROTOCOLS,
  [P1]: Object.freeze({ claim_field: "bounded_claim_sem_id", composed: false,
    check: (c) => ({ ...checkBundle(c), ok: true, verdict: "VERIFIED" }) }),
});

function resealDag(A, B, { protocols = LYING } = {}) {
  const store = memoryStore(new Map());
  store.put(A); store.put(B);
  const C1 = buildNestBundle([A, B], { protocols }); store.put(C1);
  const C2 = buildNestBundle([C1, A], { protocols }); store.put(C2);
  const D = buildNestBundle([C2, C1], { protocols }); store.put(D);
  return { A, B, C1, C2, D, store };
}

const H = (() => {
  const store = memoryStore(new Map());
  const dag = buildDag(clone(RAW_A), clone(RAW_B), { cas_dir: null, put: (_d, o) => store.put(o) });
  return { ...dag, store };
})();
const rootOf = (n) => H.roots[n];

function fresh() {
  const store = memoryStore(new Map());
  const A = clone(H.A), B = clone(H.B), C1 = clone(H.C1), C2 = clone(H.C2), D = clone(H.D);
  for (const a of [A, B, C1, C2, D]) store.put(a);
  return { A, B, C1, C2, D, store };
}
const stateDigest = (w) => digest({ D: w.D, store: [...w.store.entries.entries()].sort() });
/** Reseal a parent's own three ids after a claim/structure/aggregate edit. */
const reseal = (b) => {
  b.claim.nested_claim_sem_id = nestedClaimSemId(b.claim.connective, b.claim.scope, b.claim.operands);
  b.aggregate.aggregate_id = nestAggregateId(b.aggregate);
  b.structure.structure_sem_id = nestStructureSemId(b.structure);
  return b;
};

let ran = 0, fail = false;
const CASES = [];
const F = (name, wants, mutate, why) => CASES.push({ name, wants, mutate, why });

/* ── THE WIRE IS CANONICAL OR IT IS REFUSED ──────────────────────────────── */

F("stored-bytes-are-pretty-printed-not-canonical", "nest-artifact-non-canonical", (w) => {
  w.store.entries.set(rootOf("C1"), JSON.stringify(w.C1, null, 1) + "\n");
}, "the same object, indented. P4 accepted it — the root hashed the PARSED object, so any byte " +
   "string that parsed to it resolved under it, and 'one root, one artifact' was false in the " +
   "shipped implementation. A root is an address or it is a description of a parse result");

F("duplicate-member-name-smuggles-a-second-protocol", "nest-artifact-non-canonical", (w) => {
  // JSON.parse keeps the LAST duplicate, so the parsed object — and the root —
  // are the honest ones while the bytes say something else entirely.
  w.store.entries.set(rootOf("C1"), '{"protocol":"TRVM-EVIL-v1",' + canonicalWire(w.C1).slice(1));
}, "REPRODUCED AGAINST P4 AT ok:true, VERIFIED, zero refusals, with TRVM-EVIL-v1 in the bytes the " +
   "store served. RFC 8259 calls parser behaviour on duplicate names unpredictable, I-JSON " +
   "forbids them and RFC 8785 requires I-JSON — so this is a CROSS-IMPLEMENTATION hazard, not a " +
   "formatting one: a second implementation keeping the FIRST duplicate would verify a different " +
   "object under the same root and believe it had checked the same artifact. Refused by the " +
   "canonical-wire equality rather than by a rule that names duplicates");

F("number-respelled-on-the-wire", "nest-artifact-non-canonical", (w) => {
  const bytes = canonicalWire(w.C1).replace('"edges":2', '"edges":2.0');
  w.store.entries.set(rootOf("C1"), bytes);
}, "`2.0` parses to the same double as `2` and canonicalises back to `2`, so the parsed object is " +
   "unchanged and the bytes are not. One equality catches respelled numbers, reordered keys, " +
   "whitespace and duplicate names together");

F("store-answers-a-root-with-a-different-real-artifact", "nest-artifact-root-mismatch", (w) => {
  w.store.entries.set(rootOf("C1"), canonicalWire(w.C2));
}, "C1's address, C2's bytes — both honest artifacts, canonical on the wire, and the MAPPING is " +
   "the lie. Only re-deriving the root from what came back can see it");

F("store-has-no-bytes-under-a-cited-root", "nest-artifact-unresolvable", (w) => {
  w.store.entries.delete(rootOf("C1"));
}, "availability is a separate axis from identity, and losing it is a refusal rather than a pass");

F("store-answers-with-bytes-that-do-not-parse", "nest-artifact-malformed", (w) => {
  w.store.entries.set(rootOf("C2"), '{"protocol": "TRVM-NESTED-COMP');
}, "truncated bytes, named rather than thrown — B2.1.2, in the module whose whole input is hostile");

/* ── AN UNTRUSTED CITATION MAY NOT STEER A FILESYSTEM READ ───────────────── */

F("citation-is-a-relative-path", "nest-artifact-root-malformed", (w) => {
  w.D.references.operands[0].artifact_root = "../proof_bundle";
}, "REPRODUCED AGAINST P4: directoryStore built join(dir, root + '.json') from whatever string " +
   "arrived and READ 1.31 MB from outside the store before the root comparison rejected it. " +
   "Integrity caught the wrong artifact; nothing caught the traversal. The grammar is checked " +
   "before a root reaches a path, a store or a hash");

/* ── A CONTENT ADDRESS IS NOT A WARRANT ──────────────────────────────────── */

F("impeccable-dag-over-a-child-its-own-checker-refuses", "nest-child-refused", (w) => {
  const A = clone(w.A);
  A.cases[0].lhs.outcome.value = A.cases[0].lhs.outcome.value + 1;
  A.cases[0].case_evidence_id = caseEvidenceId(A.cases[0]);
  A.aggregate.aggregate_id = aggregateId(A.aggregate);
  const forged = resealDag(A, clone(w.B));
  w.store = forged.store; w.D = forged.D;
}, "every address correct and canonical, every certificate recomputed, every aggregate and " +
   "structure resealed — over a child whose own checker refuses it. No property of an address " +
   "could catch this, which is why every DISTINCT artifact is judged by its own protocol's " +
   "checker. Reuse does not weaken it: the memo holds a judgment this verifier DERIVED");

F("reference-contract-declares-the-address-a-warrant", "nest-reference-contract-mismatch", (w) => {
  w.D.references.contract = { ...w.D.references.contract, address_is_a_warrant: true };
  reseal(w.D);
}, "the round's argument as a machine-readable value, flipped — and it now lives in the TRANSPORT " +
   "plane rather than the claim scope, because how bytes are fetched is not what is proved");

F("operand-claims-it-was-already-verified", "nest-vocabulary-unknown", (w) => {
  w.D.claim.operands[0].already_verified = true;
  w.D.claim.operands[0].warrant = "resolved from the store, therefore accepted";
  reseal(w.D);
  w.store.entries.set(artifactRoot(w.D), canonicalWire(w.D));
}, "the warrant smuggled in as a field and resealed, so it is AUTHENTICATED rather than merely " +
   "present. Refused by law:proof.semantic-vocabulary-closed@1 at a layer written after it");

/* ── REFERENCE IS NOT CLAIM, AND THE TWO PLANES MUST STILL AGREE ─────────── */

F("reference-points-at-another-real-artifact", "nest-citation-cross-wired", (w) => {
  w.D.references.operands[0].artifact_root = rootOf("C1");
}, "the citation names C2 and the reference fetches C1. Separating the planes creates the one " +
   "thing separation always creates — a way for the halves to disagree — so the certificate is " +
   "recomputed from what was RESOLVED and compared field by field");

F("a-reference-goes-missing", "nest-reference-mismatch", (w) => {
  w.D.references.operands = [w.D.references.operands[0]];
}, "an operand with no reference saying where its bytes are. The claim is untouched and still " +
   "coherent, which is exactly why the two planes are matched as SETS rather than by position");

F("certificate-id-replaced-by-another-valid-one", "nest-certificate-stale", (w) => {
  /* A REAL certificate from elsewhere in the DAG — the P1 leaf's, which is a
     genuine `vclaim-` this checker can verify exists but is NOT what the bytes
     at this reference compute. Using the SIBLING's would collide with the
     duplicate-operand check and test that instead. */
  const elsewhere = verifiedClaimSemId(certificateOf(w.A, "bounded_claim_sem_id"));
  const old = w.D.claim.operands[0].verified_claim_sem_id;
  w.D.claim.operands[0].verified_claim_sem_id = elsewhere;
  const ref = w.D.references.operands.find((r) => r.verified_claim_sem_id === old);
  ref.verified_claim_sem_id = elsewhere;
  w.D.aggregate.child_verdicts = {
    [elsewhere]: "VERIFIED",
    [w.D.claim.operands[1].verified_claim_sem_id]: "VERIFIED" };
  reseal(w.D);
}, "a forged name over honest bytes, with both planes agreeing about the forged name so nothing " +
   "internal disagrees. Under content addressing the DRIFT form of staleness is gone — bytes do " +
   "not move — and this is what is left: the resolved artifact simply does not compute the " +
   "certificate it is cited as");

F("chain-ids-declared-rather-than-derived", "nest-chain-ids-mismatch", (w) => {
  w.D.chain_ids = { leaf_chains: [...w.D.chain_ids.leaf_chains,
    { ...w.D.chain_ids.leaf_chains[0], lowering_version: "9.9.9" }] };
  reseal(w.D);
}, "a composition claiming a compiler none of its children were checked under. A producer that " +
   "could write its own chain would be naming the compiler its own proof was verified against");

F("duplicate-operand-at-one-node", "nest-operand-duplicated", (w) => {
  w.D.claim.operands = [clone(w.D.claim.operands[0]), clone(w.D.claim.operands[0])];
  reseal(w.D);
}, "`C2 ∧ C2` as a two-operand conjunction — DISTINCT from the diamond, which is one artifact " +
   "reached by two paths and is what the protocol is for. Hence per-node rather than global");

F("child-protocol-with-no-checker-here", "nest-child-protocol-unsupported", (w) => {
  const alien = { protocol: "TRVM-SOMETHING-ELSE-v1", claim: { x: 1 }, chain_ids: {}, aggregate: {} };
  const root = w.store.put(alien);
  w.D.references.operands[1].artifact_root = root;
}, "a correctly addressed, canonically stored artifact of a protocol this checker cannot judge. " +
   "Resolution succeeded perfectly, which is the point");

F("connective-swapped-to-disjunction", "nest-connective-unsupported", (w) => {
  w.D.claim.connective = "DISJUNCTION";
  reseal(w.D);
}, "a connective this checker cannot evaluate. Guessing would be the interesting kind of wrong");

F("scope-generalizes-beyond-its-children", "nest-scope-mismatch", (w) => {
  w.D.claim.scope = { ...w.D.claim.scope, generalizes_beyond_children: true };
  reseal(w.D);
}, "the claim scope is purely semantic now — transport and execution have left it — and what " +
   "remains is exactly what a claimant must not be allowed to write");

/* ── THE TWO AUTHENTICATED-BUT-NOT-SEMANTIC PLANES ───────────────────────── */

F("parent-claims-to-have-rederived-leaf-receipts", "nest-count-inconsistent", (w) => {
  w.D.aggregate.leaf_receipts_rederived_by_parent = 128;
  reseal(w.D);
}, "a composition that flattened its children is a bigger leaf. The zero is structural — this " +
   "checker imports no kernel — so the artifact cannot be right about it");

F("structure-understates-the-dag", "nest-structure-mismatch", (w) => {
  w.D.structure.edges = 2;
  w.D.structure.max_depth_below = 1;
  reseal(w.D);
}, "the structure plane is OUTSIDE the certificate identity and still fully derived and compared. " +
   "Outside the theorem's name is not outside the checker's reach");

F("dedup-ratio-inflated-by-halving-the-stored-bytes", "nest-structure-mismatch", (w) => {
  w.D.structure.unique_bytes = Math.floor(w.D.structure.unique_bytes / 2);
  reseal(w.D);
}, "the headline saving, doubled by a producer");

F("transitive-film-count-erased", "nest-structure-mismatch", (w) => {
  w.D.structure.films_below_by_edge_multiplicity = 0;
  w.D.structure.films_below_distinct = 0;
  reseal(w.D);
}, "the two numbers that say how much work the CHILD checkers hold, set to the number that says " +
   "how much the parent did. Both are STRUCTURAL — neither depends on the verifier's strategy — " +
   "which is why they may live in the artifact at all when the evaluation counts may not");

F("annotations-carry-a-child-bundle", "nest-vocabulary-unknown", (w) => {
  w.D.annotations = { ...w.D.annotations, helpful_copy: w.C1 };
  w.store.entries.set(artifactRoot(w.D), canonicalWire(w.D));
}, "the non-authoritative seat used to carry evidence — and here it would be the reference model " +
   "quietly becoming the carriage model again");

F("bundle-gains-a-semantic-field", "nest-vocabulary-unknown", (w) => {
  w.D.trusted_by = "the store";
  w.D.transitive = true;
}, "a key the bundle grammar does not have. Every record in this protocol has one from its first " +
   "commit, so it does not need resealing to be dangerous and does not survive being resealed");


/* ── P4.2: THE WIRE IS BYTES, AND THE VERIFIER OWNS ITS INPUT ────────────── */

F("stored-bytes-are-not-valid-utf8", "nest-artifact-invalid-utf8", (w) => {
  const canonical = canonicalWireBytes(w.C1);
  // a raw 0xFF where canonical UTF-8 for the first non-ASCII codepoint would be
  const idx = canonical.findIndex((b) => b >= 0x80);
  const bad = Buffer.from(canonical);
  bad[idx >= 0 ? idx : 1] = 0xff;
  w.store.entries.set(rootOf("C1"), bad);
}, "REPRODUCED AGAINST P4.1: the store read files with the forgiving `utf8` decoder, so Node " +
   "substituted U+FFFD for the invalid byte BEFORE the canonical equality ran — two different " +
   "byte strings accepted as one wire artifact, which is the defect P4.1 existed to close, one " +
   "layer lower. The decode is fatal now and the bound is applied to bytes");

F("nested-verdict-says-refused-and-is-resealed", "nest-count-inconsistent", (w) => {
  w.D.aggregate.nested_verdict = "REFUSED";
  reseal(w.D);
}, "THE THIRTEENTH B6.3: nested_verdict was in the required grammar and inside aggregate_id, and " +
   "no checker read it. P4.1 answered ok:true, VERIFIED, zero refusals over an artifact that said " +
   "of itself that it was REFUSED. field_audit.mjs now perturbs every field of every record " +
   "mechanically, so the fourteenth cannot be found by hand either");

F("root-artifact-over-the-byte-ceiling", "nest-budget-exceeded", (w) => {
  w.D.annotations = { ...w.D.annotations, padding: "x".repeat(9 * 1024 * 1024) };
}, "P4.1 applied max_artifact_bytes only to artifacts fetched through the CAS, so the one " +
   "artifact handed in directly could be any size: a 9.4 MB root verified under an 8 MiB " +
   "ceiling. The ROOT is not exempt from a policy its children are held to");

F("more-operands-than-the-policy-allows", "nest-budget-exceeded", (w) => {
  const op = clone(w.D.claim.operands[0]);
  w.D.claim.operands = Array.from({ length: 200 }, (_, i) =>
    ({ ...op, verified_claim_sem_id: op.verified_claim_sem_id.slice(0, -3) + String(i).padStart(3, "0") }));
  reseal(w.D);
}, "phase 1 bounded references.operands because that is what it walks; nothing bounded " +
   "claim.operands, which the verify phase walks four times. Both planes are bounded before " +
   "either is iterated");

/* ══ MEASURED, NOT FORGED ════════════════════════════════════════════════ */

{
  ran++;
  const r = checkNestBundle(H.D, { store: H.store });
  const m = r.measured;
  if (!r.ok) { fail = true;
    console.log(`FAIL  honest-nested-composition-verifies  [${r.refusals.map((x) => x.code).join(", ")}]`);
  } else console.log(`PASS  honest-nested-composition-verifies           → ` +
    `${m.reference_bundle_bytes.toLocaleString()} canonical B names ` +
    `${m.bytes_if_inlined.toLocaleString()} B of proof; ${m.unique_artifact_resolutions} artifacts, ` +
    `DAG unfolds to ${m.edges_if_fully_unfolded} edges, ${m.edge_traversals} walked = ` +
    `${m.checker_evaluations} evaluations + ${m.derivation_reuses} reuses, ` +
    `${m.persistent_warrant_hits} warrants believed, ${m.dedup_ratio}× dedup`);
}


/* THE VERIFIER OWNS ITS INPUT — law:proof.verifier-input-owned@1, measured on
   TWO protocols, because P4.1's ingress hole was not a P4 hole. */
{
  ran++;
  const probeField = (obj, path, hostile) => {
    let reads = 0;
    const rec = path.slice(0, -1).reduce((x, k) => x[k], obj);
    const key = path[path.length - 1];
    const real = rec[key];
    delete rec[key];
    Object.defineProperty(rec, key, { enumerable: true, configurable: true,
      get() { reads += 1; return reads <= 1 ? real : hostile; } });
    return () => reads;
  };
  // 1. exactly ONE read, so there is no later read to disagree with
  const d1 = clone(H.D);
  const reads1 = probeField(d1, ["references", "contract", "address_is_a_warrant"], true);
  const r1 = checkNestBundle(d1, { store: H.store });
  const a1 = clone(RAW_A);
  const reads2 = probeField(a1, ["claim", "scope", "generalizes_beyond_domain"], true);
  const r2 = checkBundle(a1);
  // 2. and a getter that is hostile AT INGRESS is refused, so the single read is
  //    not merely single but load-bearing
  const d3 = clone(H.D);
  let n = 0;
  const c3 = d3.references.contract;
  delete c3.address_is_a_warrant;
  Object.defineProperty(c3, "address_is_a_warrant", { enumerable: true, configurable: true,
    get() { n += 1; return true; } });
  const r3 = checkNestBundle(d3, { store: H.store });
  const ok = reads1() === 1 && r1.ok === true && reads2() === 1 && r2.ok === true
    && r3.ok === false && r3.refusals.some((x) => x.code === "nest-reference-contract-mismatch");
  if (!ok) { fail = true;
    console.log(`FAIL  verifier-owns-its-input  P4 reads=${reads1()} ok=${r1.ok} · ` +
      `P1 reads=${reads2()} ok=${r2.ok} · hostile-at-ingress ok=${r3.ok}`);
  } else console.log(`PASS  verifier-owns-its-input                      → ` +
    `a live getter is read EXACTLY ONCE by each checker (P4: ${reads1()}, P1: ${reads2()}), so ` +
    `there is no later read for it to disagree with — and a getter returning the hostile value AT ` +
    `INGRESS is refused, so the single read is load-bearing rather than lucky. AGAINST P4.1 THIS ` +
    `MEASURED THE OPPOSITE ON BOTH PROTOCOLS: address_is_a_warrant read false then true with ` +
    `checkNestBundle returning VERIFIED and the same object serialising as true immediately ` +
    `afterwards, and generalizes_beyond_domain read false 3 times and true afterwards with ` +
    `checkBundle returning VERIFIED over what then read as an UNBOUNDED scope`);
}

/* AND THE BYTES API, which is what an independent implementation will use. */
{
  ran++;
  const bytes = canonicalWireBytes(H.D);
  const good = checkNestBytes(bytes, { store: H.store });
  const pretty = checkNestBytes(Buffer.from(JSON.stringify(H.D, null, 1), "utf8"), { store: H.store });
  const ok = good.ok === true && pretty.ok === false
    && pretty.refusals.some((x) => x.code === "nest-ingress-refused");
  if (!ok) { fail = true;
    console.log(`FAIL  the-public-boundary-is-bytes  canonical=${good.verdict} pretty=${pretty.verdict}`);
  } else console.log(`PASS  the-public-boundary-is-bytes                 → ` +
    `checkNestBytes accepts the ${bytes.length}-byte canonical encoding and refuses the same ` +
    `artifact pretty-printed, nest-ingress-refused. Bytes cannot have a getter, which is why this ` +
    `is the boundary an independent implementation should be handed rather than an object`);
}

/* THE ROUND'S HEADLINE POSITIVE PROPERTY. law:proof.reference-is-not-claim@1
   in the only form that establishes it: not a forgery refused, but a legitimate
   non-semantic edit leaving every semantic name where it was. */
{
  ran++;
  const A2 = clone(RAW_A);
  A2.annotations = { ...A2.annotations, note: "REWORDED ENTIRELY, AND NOTHING SEMANTIC CHANGED" };
  const s2 = memoryStore(new Map());
  const d2 = buildDag(A2, clone(RAW_B), { cas_dir: null, put: (_d, o) => s2.put(o) });
  const cert = (b, f) => verifiedClaimSemId(certificateOf(b, f));
  const held = [], moved = [];
  const note = (label, before, after, want) => {
    const same = before === after;
    (same ? held : moved).push(label);
    return same === (want === "HOLD");
  };
  let good = true;
  good &&= note("A.verified_claim_sem_id",
    cert(H.A, "bounded_claim_sem_id"), cert(A2, "bounded_claim_sem_id"), "HOLD");
  good &&= note("A.artifact_root", rootOf("A"), artifactRoot(A2), "MOVE");
  for (const n of ["C1", "C2", "D"]) {
    good &&= note(`${n}.nested_claim_sem_id`,
      H[n].claim.nested_claim_sem_id, d2[n].claim.nested_claim_sem_id, "HOLD");
    good &&= note(`${n}.aggregate_id`, H[n].aggregate.aggregate_id, d2[n].aggregate.aggregate_id, "HOLD");
    good &&= note(`${n}.verified_claim_sem_id`,
      cert(H[n], "nested_claim_sem_id"), cert(d2[n], "nested_claim_sem_id"), "HOLD");
    good &&= note(`${n}.artifact_root`, rootOf(n), artifactRoot(d2[n]), "MOVE");
  }
  const stillOk = checkNestBundle(d2.D, { store: s2 }).ok;
  if (!good || !stillOk) { fail = true;
    console.log(`FAIL  reference-is-not-claim  HELD=[${held.join(", ")}] MOVED=[${moved.join(", ")}] ok=${stillOk}`);
  } else console.log(`PASS  reference-is-not-claim                       → ` +
    `reword ONE annotation on the P1 leaf and NOTHING SEMANTIC MOVES: ${held.length} names hold ` +
    `(every claim id, every aggregate id and every certificate id at all three composition ` +
    `levels), ${moved.length} addresses move (the leaf's root and every ancestor's), and the ` +
    `rebuilt DAG verifies. AGAINST P4 THIS MEASURED THE OPPOSITE: an English prose edit at a leaf ` +
    `recursively renamed the theorem at the root, because artifact_root sat inside the claim`);
}

/* DERIVATION REUSE IS OBSERVATIONALLY EQUIVALENT — GPT's Q1 ruling, measured
   rather than assumed, on an honest DAG and on a forged one. */
{
  ran++;
  const forged = (() => { const w = fresh();
    CASES.find((c) => c.name === "impeccable-dag-over-a-child-its-own-checker-refuses").mutate(w);
    return w; })();
  const codes = (r) => [...new Set(r.refusals.map((x) => x.code))].sort().join(",");
  const pairs = [["honest", H.D, H.store], ["forged", forged.D, forged.store]];
  const rows = [];
  let agree = true;
  for (const [label, bundle, store] of pairs) {
    const on = checkNestBundle(bundle, { store });
    const off = checkNestBundle(bundle, { store, derivation_reuse: false });
    agree &&= on.ok === off.ok && on.verdict === off.verdict && codes(on) === codes(off);
    rows.push(`${label}: ${on.verdict} both ways · reuse ON ` +
      `${on.measured.checker_evaluations}+${on.measured.derivation_reuses}=` +
      `${on.measured.edge_traversals} · OFF ${off.measured.checker_evaluations}+` +
      `${off.measured.derivation_reuses}=${off.measured.edge_traversals}`);
  }
  if (!agree) { fail = true; console.log(`FAIL  derivation-reuse-is-observationally-equivalent  ${rows.join(" | ")}`);
  } else console.log(`PASS  derivation-reuse-is-observationally-equivalent → ${rows.join(" | ")}. ` +
    `A memo created inside ONE top-level verification, populated only by this verifier, keyed by ` +
    `an immutable snapshot it owns, never persisted and never transmitted, is common-subexpression ` +
    `elimination inside one derivation — not a verdict believed from elsewhere. Equal verdicts ` +
    `AND equal refusal sets on a forged DAG as well as an honest one, because agreeing about a ` +
    `PASS is the easy half`);
}

/* THE POLICY IS THE CHECKER'S — D, and P4 shipped the opposite. */
{
  ran++;
  const s3 = memoryStore(new Map());
  s3.put(clone(RAW_A));
  let node = buildNestBundle([clone(RAW_A)]); s3.put(node);
  for (let i = 1; i < NEST_MAX_DEPTH + 8; i++) { node = buildNestBundle([node]); s3.put(node); }
  const shipped = checkNestBundle(node, { store: s3 });
  const raised = checkNestBundle(node, { store: s3, max_depth: 1000 });
  const tightened = checkNestBundle(H.D, { store: H.store, max_depth: 2 });
  const depthCodes = shipped.measured.refusal_codes_transitive ?? [];
  const ok = shipped.ok === false
    && [...new Set(shipped.refusals.map((x) => x.code))].includes("nest-depth-exceeded")
    && raised.ok === false
    && raised.refusals.some((x) => x.code === "nest-policy-weakened")
    && tightened.ok === false
    && tightened.refusals.some((x) => x.code === "nest-depth-exceeded");
  if (!ok) { fail = true;
    console.log(`FAIL  verifier-policy-is-checker-owned  shipped=${shipped.verdict} ` +
      `raised=${raised.verdict}[${raised.refusals.map((x) => x.code).join(",")}] ` +
      `tightened=${tightened.verdict}`);
  } else console.log(`PASS  verifier-policy-is-checker-owned             → ` +
    `a genuine ${NEST_MAX_DEPTH + 8}-deep chain, every node sealed and stored, is refused at the ` +
    `shipped ceiling of ${NEST_MAX_DEPTH}; asking for max_depth:1000 is refused ` +
    `nest-policy-weakened rather than obeyed — AGAINST P4 IT RETURNED VERIFIED, with ` +
    `max_depth_below 40 and a ceiling of 1000; and TIGHTENING still works, since max_depth:2 ` +
    `refuses the honest 3-high DAG. A caller may make a verifier stricter and may not make it ` +
    `agree with something the shipped policy refuses`);
}

/* CITABILITY — unchanged from P4 and still the reason this protocol exists. */
{
  ran++;
  const composePath = join(HERE, "compose_bundle.json");
  let threw = null;
  if (existsSync(composePath)) {
    const p3 = JSON.parse(readFileSync(composePath, "utf8"));
    try { verifiedClaimSemId(certificateOf(p3, "composed_claim_sem_id")); }
    catch (e) { threw = e.message; }
  }
  const nested = verifiedClaimSemId(certificateOf(H.C1, "nested_claim_sem_id"));
  if (threw !== "certificate-incomplete: chain_ids" || !nested.startsWith("vclaim-")) {
    fail = true; console.log(`FAIL  p3-was-not-citable-and-p4-is  (P3 gave ${threw})`);
  } else console.log(`PASS  p3-was-not-citable-and-p4-is                 → ` +
    `verifiedClaimSemId(P3 composed certificate) THROWS "${threw}". P3's non-transitivity was a ` +
    `HOLE, not a policy: the identity a citation is made of binds a compiler chain and a ` +
    `composition had none`);
}

/* THE CYCLE GUARD — and the claim is now stated as what was MEASURED. */
{
  ran++;
  const ITER = 512;
  let obj = { protocol: NEST_PROTOCOL, cites: null };
  const seen = new Set();
  let converged = false, revisited = false;
  for (let i = 0; i < ITER; i++) {
    const r = artifactRoot(obj);
    if (obj.cites === r) { converged = true; break; }
    if (seen.has(r)) { revisited = true; break; }
    seen.add(r);
    obj = { protocol: NEST_PROTOCOL, cites: r };
  }
  if (converged || revisited) { fail = true;
    console.log(`FAIL  a-cycle-was-not-sealable-in-a-bounded-experiment (converged=${converged})`);
  } else console.log(`PASS  a-cycle-was-not-sealable-in-a-bounded-experiment → ` +
    `${ITER} iterations of "cite your own root" produced ${seen.size} distinct roots and NO ` +
    `FIXED POINT. THAT IS WHAT WAS MEASURED AND IT IS ALL THAT IS CLAIMED: sealing a cycle needs ` +
    `bytes that hash to a root those bytes already contain, which is assumed computationally ` +
    `infeasible under the hash model and is NOT proved here — no bounded experiment can show ` +
    `SHA-256 has no fixed point for this encoding. nest-cycle is kept, is defence in depth, and ` +
    `is not load-bearing`);
}

for (const c of CASES) {
  ran++;
  const w = fresh();
  const before = stateDigest(w);
  try { c.mutate(w); }
  catch (e) { fail = true; console.log(`FAIL  ${c.name}  (forgery threw: ${e.message})`); continue; }
  if (stateDigest(w) === before) { fail = true; console.log(`FAIL  ${c.name}  (VACUOUS — the forgery changed nothing)`); continue; }
  const r = checkNestBundle(w.D, { store: w.store });
  const codes = [...new Set(r.refusals.map((x) => x.code))];
  if (r.ok) { fail = true; console.log(`FAIL  ${c.name}  (ACCEPTED — the checker verified a forged DAG)`); }
  else if (!codes.includes(c.wants)) { fail = true;
    console.log(`FAIL  ${c.name}  (WRONG REFUSAL — wanted ${c.wants}, got [${codes.join(", ")}])`); }
  else console.log(`PASS  ${c.name.padEnd(50)} → ${c.wants}` +
    (codes.length > 1 ? `  (+${codes.length - 1} other code(s))` : ""));
}

console.log("═".repeat(96));
const byCode = new Map();
for (const c of CASES) byCode.set(c.wants, (byCode.get(c.wants) ?? 0) + 1);
const M = checkNestBundle(H.D, { store: H.store }).measured;
console.log(fail
  ? `NEST-FORGERIES: FAIL — ${ran} cases ran, at least one forgery was not caught by its own check`
  : `NEST-FORGERIES: PASS — ${ran}/${ran}. The honest DAG verifies from a store nothing trusts; ` +
    `REFERENCE IS NOT CLAIM is measured POSITIVELY — rewording one annotation on a leaf holds ` +
    `every claim, aggregate and certificate id at all three composition levels while moving every ` +
    `address, which against P4 renamed the theorem; DERIVATION REUSE is measured observationally ` +
    `equivalent to recomputation on an honest DAG AND a forged one ` +
    `(${M.checker_evaluations} evaluations + ${M.derivation_reuses} reuses = ` +
    `${M.edge_traversals} of ${M.edges_if_fully_unfolded} unfolded edges, ` +
    `${M.persistent_warrant_hits} verdicts believed from elsewhere); the VERIFIER POLICY is ` +
    `measured to be the checker's, refusing max_depth:1000 which P4 obeyed; a composed ` +
    `certificate is measured to have been un-citable before P4; and a cycle is measured not to ` +
    `have been sealable in 512 attempts, which is stated as the bounded experiment it is rather ` +
    `than as a theorem about SHA-256. ${CASES.length} forged DAGs are each refused BY THE CHECK ` +
    `WHOSE SUBJECT THEY ARE across ${byCode.size} distinct codes ` +
    `[${[...byCode].map(([k, n]) => `${k}×${n}`).join(", ")}]: ${CASES.map((c) => c.name).join(", ")}. ` +
    `THE THREE THAT ARE NEW AT THIS LAYER ARE ABOUT THE WIRE: the same object indented, a number ` +
    `respelled, and a DUPLICATE MEMBER NAME that JSON.parse silently resolves in favour of the ` +
    `last one — which P4 authenticated as the honest artifact, VERIFIED with zero refusals and ` +
    `TRVM-EVIL-v1 sitting in the bytes the store served. All three die on one equality: the bytes ` +
    `must BE the canonical encoding of what they parse to`);
process.exit(fail ? 1 : 0);
