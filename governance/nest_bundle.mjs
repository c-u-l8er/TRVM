/* ═══════════════════════════════════════════════════════════════════════════
   nest_bundle.mjs — v0.2.0 — P4.1, REFERENCE IS NOT CLAIM
   law:proof.reference-is-not-claim@1 · law:proof.content-address-is-not-a-warrant@1

   P4 shipped `artifact_root` INSIDE `claim.operands`, and therefore inside
   `nested_claim_sem_id`. Reproduced against the shipped P4 pack before this
   file changed — reword ONE English annotation on the P1 leaf, nothing
   semantic, and rebuild:

       A   verified_claim_sem_id   HOLDS      ← the leaf's NAME is untouched
       A   artifact_root           MOVED      ← its BYTES are different
       C1  nested_claim_sem_id     MOVED
       C2  nested_claim_sem_id     MOVED
       D   nested_claim_sem_id     MOVED      ← and so is every certificate id

   **An English prose edit at a leaf recursively renamed the theorem at the
   root.** That contradicts the taxonomy P4 stated two paragraphs away from the
   defect: `verified_claim_sem_id` says WHAT is cited, `artifact_root` says
   which bytes supply it. A locator may rename the ARTIFACT that carries a
   proof. It may not rename the PROOF.

   So the planes are separated, and each answers exactly one question:

       claim        WHAT is asserted           connective · scope · operands
                                               (protocol, claim_sem_id,
                                                aggregate_id, verified_claim_sem_id)
       chain_ids    UNDER WHICH COMPILERS      derived from the children
       references   WHERE THE BYTES ARE        verified_claim_sem_id → artifact_root
       aggregate    WHAT EVIDENCE HOLDS        verdicts, and the parent's own zeroes
       structure    WHAT SHAPE THE DAG IS      edges, unique artifacts, bytes, height
       annotations  NOTHING                    prose, non-authoritative

   `nested_claim_sem_id` binds the claim. `aggregate_id` binds the evidence.
   `verifiedClaimSemId` binds those two plus the chain — so a prose edit now
   moves the artifact root, moves the reference that points at it, moves the
   structure byte counts, and leaves the CLAIM and the CERTIFICATE alone.

   AND THE EXECUTION PLANE IS NOT IN THE ARTIFACT AT ALL. P4 put
   `child_checker_invocations` in the aggregate and
   `child_verdicts_cached_across_citations` in the claim scope, so switching a
   sound verifier from repeated evaluation to run-local reuse would have
   RENAMED THE THEOREM. Those are facts about a verification run, no artifact
   can be right about them, and `nest_check.mjs` reports them in `measured`
   where they gate nothing. What stays here is STRUCTURAL and
   strategy-independent: `edges` counts citations in the DAG,
   `films_below_by_edge_multiplicity` counts what a walk of every edge would
   replay, `films_below_distinct` counts what the distinct artifacts hold. Both
   are the same number whether or not the verifier reuses a derivation.

   THE SHAPE, unchanged from P4 and for the same reason:

       D  = C2 ∧ C1        C2 = C1 ∧ A        C1 = A ∧ B

   A diamond twice over. The conjunction is redundant on purpose — a shared
   lemma is what a real proof DAG deduplicates, and a diamond over a cheap node
   would measure nothing, so the shared node is the 1.3 MB P1 bundle.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, existsSync, rmSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { canonicalBytes } from "./derive_protocol.mjs";
import { verifiedClaimSemId, certificateOf } from "./certificate.mjs";
import { artifactRoot, artifactBytes, canonicalWireBytes, putArtifact } from "./cas.mjs";
import { checkBundle } from "./proof_check.mjs";
import { checkDomainBundle } from "./domain_check.mjs";

export const NEST_BUNDLE_VERSION = "0.2.0";
export const NEST_PROTOCOL = "TRVM-NESTED-COMPOSITION-v2";
/** v1 shipped `artifact_root` inside the claim and the execution counters
 *  inside the aggregate. Both are record-shape changes, so this is a protocol
 *  REVISION rather than a fix — law:proof.semantic-vocabulary-closed@1's own
 *  rule, applied to the protocol that was written under it. */
export const SUPERSEDED_PROTOCOLS = Object.freeze(["TRVM-NESTED-COMPOSITION-v1"]);
const H = (s) => createHash("sha256").update(s).digest("hex");
const HERE = dirname(fileURLToPath(import.meta.url));
export const CAS_DIR = join(HERE, "cas");

/** The PRODUCER's table. `nest_check.mjs` declares its own and does not import
 *  this one — P1.1's ruling, arriving for the sixth round running. */
export const CHILD_PROTOCOLS = Object.freeze({
  "TRVM-BOUNDED-PROOF-v1": Object.freeze({
    claim_field: "bounded_claim_sem_id", check: checkBundle, composed: false }),
  "TRVM-BOUNDED-DOMAIN-PROOF-v1": Object.freeze({
    claim_field: "domain_claim_sem_id", check: checkDomainBundle, composed: false }),
  [NEST_PROTOCOL]: Object.freeze({
    claim_field: "nested_claim_sem_id", check: null, composed: true }),
});

/* THE SCOPE IS PURELY SEMANTIC NOW. `children_resolved_by_content_address` was
   transport and `child_verdicts_cached_across_citations` was execution
   strategy; both have left, and what remains says only what the conjunction
   rests on. */
export const NEST_CLAIM_SCOPE = Object.freeze({
  kind: "NESTED_COMPOSED_VERIFIED_CLAIM_CONJUNCTION",
  quantifier: "OVER_CITED_CHILD_CERTIFICATES",
  generalizes_beyond_children: false,
  children_rechecked_by_their_own_checkers: true,
  parent_rederives_leaf_evidence: false,
});

/** THE REFERENCE CONTRACT — the transport plane's own declared semantics, kept
 *  out of the claim because how bytes are fetched is not what is proved. The
 *  checker declares its own copy and compares; an artifact saying its addresses
 *  are warrants is refused by the same mechanism that refuses an unbounded
 *  proof claim. */
export const REFERENCE_CONTRACT = Object.freeze({
  resolution: "CONTENT_ADDRESSED",
  wire: "CANONICAL",
  address_is_a_warrant: false,
});

export const NEST_CLAIM_SCOPE_NOTES = Object.freeze({
  established: "each cited child certificate names a claim, an evidence aggregate and a compiler " +
    "chain together; each child is RESOLVED BY CONTENT ADDRESS from a store this checker does not " +
    "trust, required to be canonical on the wire, re-hashed, and re-checked by the checker of its " +
    "own protocol — recursively; and this artifact asserts the CONJUNCTION of exactly those " +
    "child claims.",
  not_claimed: Object.freeze([
    "NOT a new mathematical result — the conjunction is redundant on purpose; the DAG shape is " +
      "the content and a diamond over a cheap shared node would measure nothing",
    "NOT that resolving an artifact_root establishes anything about the artifact: a content " +
      "address gives IDENTITY and a store gives AVAILABILITY, and acceptance is neither",
    "NOT a warrant cache. A verifier may reuse a judgment it derived ITSELF, in THIS run, over an " +
      "immutable snapshot it owns — that is common-subexpression elimination. Believing a verdict " +
      "issued elsewhere, or one that outlived a run, is a different object and does not exist here",
    "NOT unbounded: depth, artifact bytes, total resolved bytes, operand count and resolution " +
      "count are all bounded by a policy the CHECKER owns and a caller may only tighten",
    "NOT a claim about how many times anything was checked — that is a fact about a verifier run " +
      "and appears in the checker's measurements, never in this artifact",
  ]),
});
export const CONNECTIVE = "CONJUNCTION";

/** THE CLAIM'S IDENTITY, AND `artifact_root` IS NOT IN IT. That is the whole of
 *  law:proof.reference-is-not-claim@1: an operand names a certificate, and
 *  where the bytes for that certificate live is a different question with a
 *  different answer that may change without the claim changing. */
export const nestedClaimSemId = (connective, scope, operands) =>
  "nclaim-" + H(NEST_PROTOCOL + "|" + canonicalBytes({
    protocol: NEST_PROTOCOL, connective, scope, operands }));

export const nestAggregateId = (agg) => {
  const { aggregate_id, ...rest } = agg;
  return "nagg-" + H(NEST_PROTOCOL + "|" + canonicalBytes(rest));
};

/** The structure plane has its own identity so it is authenticated inside the
 *  artifact root without being inside the certificate. A hashed field is a
 *  checked field — `nest_check.mjs` derives every one of these — but a DAG that
 *  grew a node is a different ARTIFACT, not a different THEOREM. */
export const nestStructureSemId = (s) => {
  const { structure_sem_id, ...rest } = s;
  return "nstruct-" + H(NEST_PROTOCOL + "|" + canonicalBytes(rest));
};

/** THE CHAIN RECORDS BENEATH AN ARTIFACT, flat and deduplicated. Reading a
 *  child's `chain_ids` is reading a field that child's OWN checker validated. */
export function leafChainsOf(artifact) {
  const c = artifact?.chain_ids;
  if (c && typeof c === "object" && Array.isArray(c.leaf_chains)) return c.leaf_chains;
  return c === undefined || c === null ? [] : [c];
}
export function derivedChainIds(children) {
  const byBytes = new Map();
  for (const child of children)
    for (const rec of leafChainsOf(child)) byBytes.set(canonicalBytes(rec), rec);
  return { leaf_chains: [...byBytes.keys()].sort().map((k) => byBytes.get(k)) };
}

/** A CLAIM OPERAND: the citation, and nothing else. No address. */
export function operandFor(artifact, claim_field) {
  const c = certificateOf(artifact, claim_field);
  return {
    protocol: c.protocol,
    claim_sem_id: c.claim_sem_id,
    aggregate_id: c.aggregate_id,
    verified_claim_sem_id: verifiedClaimSemId(c),
  };
}
/** A REFERENCE: the same certificate name, and where to get it. */
export const referenceFor = (artifact, verified_claim_sem_id) =>
  ({ verified_claim_sem_id, artifact_root: artifactRoot(artifact) });

/* ── THE STRUCTURE OF THE SUBTREE BELOW A NODE ──────────────────────────────
   Everything here is a property of the DAG rather than of a verifier run, and
   the two film counts are the pair that makes that visible: what a walk of
   every edge WOULD replay, and what the distinct artifacts actually hold. A
   verifier that reuses a derivation reports the second; one that does not
   reports the first; the ARTIFACT states both and neither depends on which. */
function shapeBelow(children, protocols, leafStats) {
  const unique = new Map();
  let edges = 0, inlined = 0, height = 0, filmsByEdge = 0, casesByEdge = 0;
  for (const child of children) {
    const spec = protocols[child?.protocol];
    const root = artifactRoot(child), bytes = artifactBytes(child);
    edges += 1; inlined += bytes;
    if (spec?.composed) {
      unique.set(root, { bytes, films: 0, cases: 0 });
      const s = shapeBelow(child.__children, protocols, leafStats);
      for (const [r, v] of s.unique) unique.set(r, v);
      edges += s.edges; inlined += s.inlined;
      filmsByEdge += s.filmsByEdge; casesByEdge += s.casesByEdge;
      height = Math.max(height, 1 + s.height);
    } else {
      const st = leafStats.get(root) ?? { films: 0, cases: 0 };
      unique.set(root, { bytes, films: st.films, cases: st.cases });
      filmsByEdge += st.films; casesByEdge += st.cases;
      height = Math.max(height, 1);
    }
  }
  return { unique, edges, inlined, height, filmsByEdge, casesByEdge };
}

export function buildNestBundle(children, { protocols = CHILD_PROTOCOLS } = {}) {
  const operands = [], references = [], verdicts = {};
  const leafStats = new Map();
  for (const child of children) {
    const spec = protocols[child?.protocol];
    if (!spec) throw new Error("nest-bundle-unknown-child-protocol: " + child?.protocol);
    const op = operandFor(child, spec.claim_field);
    if (spec.composed) {
      if (child.aggregate?.nested_verdict !== "VERIFIED")
        throw new Error("nest-bundle-child-refused: " + child.protocol);
      verdicts[op.verified_claim_sem_id] = "VERIFIED";
      for (const [r, v] of (child.__leafStats ?? new Map())) leafStats.set(r, v);
    } else {
      const r = spec.check(child);
      if (!(r.ok === true && r.verdict === "VERIFIED"))
        throw new Error(`nest-bundle-child-refused: ${child.protocol} → ` +
          (r.refusals ?? []).map((x) => x.code).join(", "));
      verdicts[op.verified_claim_sem_id] = r.verdict;
      leafStats.set(artifactRoot(child), {
        films: r.measured.films_replayed_on_two_classes ?? 0,
        cases: r.measured.derived_cases ?? 0 });
    }
    operands.push(op);
    references.push(referenceFor(child, op.verified_claim_sem_id));
  }

  const aggregate = {
    operands: operands.length,
    child_verdicts: verdicts,
    // STRUCTURAL. This protocol's checker imports no kernel, emitter or decoder.
    leaf_receipts_rederived_by_parent: 0,
    films_replayed_by_parent: 0,
    nested_verdict: "PENDING",
    aggregate_id: null,
  };
  aggregate.nested_verdict =
    Object.values(verdicts).filter((v) => v === "VERIFIED").length === operands.length
    && operands.length > 0 ? "VERIFIED" : "REFUSED";
  aggregate.aggregate_id = nestAggregateId(aggregate);

  const sub = shapeBelow(children, protocols, leafStats);
  const structure = {
    edges: sub.edges,
    unique_artifacts: sub.unique.size,
    max_depth_below: sub.height,
    bytes_if_inlined: sub.inlined,
    unique_bytes: [...sub.unique.values()].reduce((a, b) => a + b.bytes, 0),
    films_below_by_edge_multiplicity: sub.filmsByEdge,
    films_below_distinct: [...sub.unique.values()].reduce((a, b) => a + b.films, 0),
    cases_below_by_edge_multiplicity: sub.casesByEdge,
    cases_below_distinct: [...sub.unique.values()].reduce((a, b) => a + b.cases, 0),
    structure_sem_id: null,
  };
  structure.structure_sem_id = nestStructureSemId(structure);

  const bundle = {
    type: "NestedComposition",
    protocol: NEST_PROTOCOL,
    version: NEST_BUNDLE_VERSION,
    claim: {
      connective: CONNECTIVE,
      scope: NEST_CLAIM_SCOPE,
      operands,
      nested_claim_sem_id: nestedClaimSemId(CONNECTIVE, NEST_CLAIM_SCOPE, operands),
    },
    chain_ids: derivedChainIds(children),
    references: { contract: REFERENCE_CONTRACT, operands: references },
    aggregate,
    structure,
    annotations: {
      note: "NON-AUTHORITATIVE — nothing in this record is hashed, checked, or established",
      generator: "nest_bundle.mjs v" + NEST_BUNDLE_VERSION,
      statement: operands.map((o) => `VERIFIED(${o.protocol})`).join(" AND "),
      scope_notes: NEST_CLAIM_SCOPE_NOTES,
    },
  };
  /* Non-enumerable, so they reach neither `canonicalWire` nor `JSON.stringify`:
     they never become a hash, a file, or anything a checker sees. */
  Object.defineProperty(bundle, "__children", { value: children, enumerable: false });
  Object.defineProperty(bundle, "__leafStats", { value: leafStats, enumerable: false });
  return bundle;
}

/** THE DAG. Built bottom-up, every node filed in the store by its own root. */
export function buildDag(A, B, { cas_dir = CAS_DIR, put = putArtifact } = {}) {
  const rootA = put(cas_dir, A), rootB = put(cas_dir, B);
  const C1 = buildNestBundle([A, B]);
  const rootC1 = put(cas_dir, C1);
  const C2 = buildNestBundle([C1, A]);
  const rootC2 = put(cas_dir, C2);
  const D = buildNestBundle([C2, C1]);
  const rootD = put(cas_dir, D);
  return { A, B, C1, C2, D, roots: { A: rootA, B: rootB, C1: rootC1, C2: rootC2, D: rootD } };
}

const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN) {
  for (const f of ["proof_bundle.json", "domain_bundle.json"]) if (!existsSync(join(HERE, f))) {
    console.log(`nest_bundle: FAIL — no child bundle at ${f} (build P1 and P2 first).`);
    process.exit(1);
  }
  rmSync(CAS_DIR, { recursive: true, force: true });
  const A = JSON.parse(readFileSync(join(HERE, "proof_bundle.json"), "utf8"));
  const B = JSON.parse(readFileSync(join(HERE, "domain_bundle.json"), "utf8"));
  const { D, roots } = buildDag(A, B);
  /* THE PROOF-WIRE FILE IS CANONICAL OCTETS. `nest_bundle.json` is the artifact
     an executable verifies and therefore IS the wire form; the indented copy is
     named for what it is and is never verified. P4.2 wrote the pretty form here
     and the CLI parsed it forgivingly, so the executable and the library
     disagreed about the same file. */
  const out = join(HERE, "nest_bundle.json");
  writeFileSync(out, canonicalWireBytes(D));
  writeFileSync(join(HERE, "nest_bundle.presentation.json"), JSON.stringify(D, null, 1) + "\n");
  const s = D.structure;
  console.log(`nest_bundle v${NEST_BUNDLE_VERSION} (${NEST_PROTOCOL}) — D = C2 ∧ C1, ` +
    `a diamond over A (P1) and C1, height ${s.max_depth_below}`);
  for (const [n, r] of Object.entries(roots)) console.log(`  ${n.padEnd(3)} ${r}`);
  console.log(`  ${s.unique_artifacts} unique artifacts below over ${s.edges} DAG edges`);
  console.log(`  bytes if inlined ${s.bytes_if_inlined.toLocaleString()} · unique ` +
    `${s.unique_bytes.toLocaleString()} · ${(s.bytes_if_inlined / s.unique_bytes).toFixed(2)}× dedup`);
  console.log(`  reference bundle itself ${artifactBytes(D).toLocaleString()} canonical bytes`);
  console.log(`  films below: ${s.films_below_by_edge_multiplicity} by edge multiplicity, ` +
    `${s.films_below_distinct} over DISTINCT artifacts — both STRUCTURAL, neither a verifier fact`);
  console.log(`  nested claim ${D.claim.nested_claim_sem_id}`);
  console.log(`  written to ${out}, store ${CAS_DIR}`);
}
