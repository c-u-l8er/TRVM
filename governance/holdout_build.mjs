/* ═══════════════════════════════════════════════════════════════════════════
   holdout_build.mjs — v0.2.0 — A CHALLENGE SET THAT REQUIRES CONSTRUCTION
   law:proof.spec-release-bound@1

   v0.1.0 committed ten hidden inputs with expectations written in ENGLISH —
   "child verified_claim_sem_id HOLDS" — which is why nothing could score them,
   and it mostly committed FINAL ARTIFACTS built by this implementation, which
   made it a hidden verification corpus rather than a construction test.

   So a case now commits three things and no fourth:

       fixture     a frozen artifact, named by its root in the public corpus
       recipe      structured steps an implementer applies from the SPEC
       predicates  a frozen, machine-evaluable relation

   Both implementations apply the recipe THEMSELVES and emit observations; the
   scorer evaluates the already-committed predicates and knows nothing about
   TRVM. Unpredictable SHA-256 values are still NOT recorded: after the reveal
   Go computes X, JS computes Y, and X != Y is a FINDING to be classified rather
   than a failure by either.

   THE PREDICATE LANGUAGE IS TINY AND FROZEN:

       EQ / NEQ            two observation paths, or a path and a literal
       HOLDS / MOVES       baseline vs candidate, the metamorphic pair
       REFUSAL_SET_EQ      EXACT set equality — never "includes". H10 shipped
                           `includes nest-citation-cross-wired` in v0.1.0 and
                           would have let five unrelated extra codes pass
       VERDICT_EQ          VERIFIED / REFUSED
       LT                  a strict inequality where the spec states one
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, writeFileSync, mkdirSync, rmSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { canonicalWireBytes, artifactRoot, memoryStore } from "./cas.mjs";
import { buildDag } from "./nest_bundle.mjs";
import { checkNestBundle } from "./nest_check.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, "holdout");
const GOLDEN = join(HERE, "..", "docs", "spec", "proof-wire", "vectors", "public");
const clone = (o) => JSON.parse(JSON.stringify(o));

function frozenLeaves() {
  const dir = join(GOLDEN, "cas"), found = {};
  for (const f of readdirSync(dir).sort()) {
    const a = JSON.parse(readFileSync(join(dir, f), "utf8"));
    if (a?.protocol === "TRVM-BOUNDED-PROOF-v1") found.A = a;
    if (a?.protocol === "TRVM-BOUNDED-DOMAIN-PROOF-v1") found.B = a;
  }
  return found;
}
const { A, B } = frozenLeaves();
const store = memoryStore(new Map());
const base = buildDag(clone(A), clone(B), { cas_dir: null, put: (_d, o) => store.put(o) });
const ROOTS = { A: artifactRoot(A), B: artifactRoot(B), C1: artifactRoot(base.C1),
                C2: artifactRoot(base.C2), D: artifactRoot(base.D) };

/** H10's EXACT refusal set, MEASURED and committed as a set. v0.1.0 said
 *  "includes nest-citation-cross-wired", which the exact-set rule adopted at
 *  P4.3 already forbids: five unrelated extra codes would have passed. */
/* ══ H10's EXPECTED REFUSAL SET — DERIVED FROM THE SPECIFICATION, THEN CHECKED
      AGAINST THIS IMPLEMENTATION ══════════════════════════════════════════════

   v0.2.0 obtained this set by RUNNING `checkNestBundle()` and committing
   whatever came back. That is the oracle leak the whole holdout exists to
   prevent, one layer down: the hidden expected answer was this implementation's
   answer, so a Go implementation drawing a *better* refusal set would be scored
   wrong, and the challenge would be measuring agreement-with-JavaScript rather
   than agreement-with-the-specification. H5 was repaired at P4.6 and this was
   left; it is the same defect.

   THE CONSTRUCTION: on D, repoint reference operand 0 — which cites C2 — at
   C1's address, and reseal. Every hash in the artifact is then internally
   consistent, and the bytes served under that address are a real, honest,
   verifying artifact. Reading TRVM-NESTED-COMPOSITION-v2, three independent
   checks must fire, and they are three because the protocol keeps three planes
   apart:

     nest-citation-cross-wired   §7.2. The parent recomputes each operand's
                                 citation FROM THE CHILD IT RESOLVED and compares
                                 field by field. Operand 0 declares C2's
                                 verified_claim_sem_id; the resolved child is C1,
                                 whose citation differs. This is the check that
                                 exists for exactly this forgery.
     nest-certificate-stale      §7.3. The certificate over the operand binds the
                                 child's aggregate and chain; recomputed against
                                 C1 it does not equal the one carried, because an
                                 aggregate commits to what was MEASURED.
     nest-structure-mismatch     §8. The structure plane is DERIVED from the
                                 children actually resolved. With C1 in place of
                                 C2 the real DAG below D is {C1, C1} — 2+2+2 = 6
                                 edges, 3 distinct artifacts, depth 2 — and the
                                 carried structure describes {C2, C1}: 8 edges, 4
                                 distinct, depth 3. Structure is not re-derivable
                                 by a forger without changing what it claims.

   Nothing else can fire: the bytes are canonical, the root re-derives, the
   store answers honestly, the child verifies under its own checker, the
   vocabulary is unchanged, and the policy is untouched.

   THE CROSS-CHECK IS BELOW and the build REFUSES to commit on a disagreement —
   if the derivation and this implementation part company, one of them is wrong
   and which one is the finding. */
const H10_DERIVED = ["nest-certificate-stale", "nest-citation-cross-wired",
  "nest-structure-mismatch"].sort();
const h10 = (() => {
  const d = clone(base.D);
  d.references.operands[0].artifact_root = ROOTS.C1;
  const r = checkNestBundle(d, { store });
  const measured = [...new Set(r.refusals.map((x) => x.code))].sort();
  if (JSON.stringify(measured) !== JSON.stringify(H10_DERIVED))
    throw new Error(`H10: the derivation from TRVM-NESTED-COMPOSITION-v2 and this implementation ` +
      `disagree about the refusal set (derived [${H10_DERIVED.join(", ")}], implementation ` +
      `[${measured.join(", ")}]). One of them is wrong and which one is the finding — the ` +
      `challenge is NOT committed on a disagreement.`);
  return H10_DERIVED;
})();

/* ══ H5's STRUCTURAL EXPECTATIONS — DERIVED FROM THE SHAPE, NOT READ OFF THE
      IMPLEMENTATION ══════════════════════════════════════════════════════════

   v0.2.0's H5 asserted `unique_artifacts < edges`, which is the only predicate
   in the set that could not discriminate: it is true of every diamond and of a
   great many wrong answers. An implementation that miscounted every structural
   quantity in the same direction would satisfy it.

   The repair is NOT another public construction. It is to make H5's expectations
   EXACT — which raises the question the whole holdout is built around: a
   recorded value this implementation produced would make it the oracle by virtue
   of having gone first, which is why the set records ZERO hashes.

   A STRUCTURAL COUNT IS NOT A HASH. A hash is unpredictable by design; these are
   arithmetic over a DAG shape the specification fixes and two leaf artifacts the
   PUBLIC corpus ships. A blind implementer can derive every one of them by hand,
   which is exactly what happens below — from the recurrences in
   TRVM-NESTED-COMPOSITION-v2 and from counts read off the public leaves, never
   from `base.C2.structure`. The implementation's own answer is then compared
   against the derivation, and a disagreement FAILS THE BUILD rather than being
   silently committed: if the two ever part company, one of them is wrong and
   which one is the finding.

   The values are NOT printed here, are not in the public corpus, and must not
   appear in the blind brief or the implementation prompt. They live only in the
   committed challenge. */
const leafFilms = (a) => a.cases.reduce((n, c) =>
  n + Object.values(c).flatMap((v) => Array.isArray(v) ? v : [v])
    .filter((x) => x && typeof x === "object" && !Array.isArray(x))
    .reduce((m, x) => m + Object.values(x)
      .filter((w) => w && typeof w === "object" && ("film_id" in w || "frames" in w)).length
      + (("film_id" in x || "frames" in x) ? 1 : 0), 0), 0);
const LEAF = {
  A: { cases: A.aggregate.case_evidence_ids.length, films: leafFilms(A) },
  B: { cases: B.aggregate.case_evidence_ids.length, films: leafFilms(B) },
};
/** THE RECURRENCES. A leaf contributes its own counts and no edges; a composed
 *  node adds one edge per operand plus everything below. `distinct` unions the
 *  leaf sets, which for this DAG means A and B exactly once however many paths
 *  reach them. */
const derive = (node) => {
  if (node.leaf) return { edges: 0, below: new Set([node.leaf]), depth: 0,
    filmsMult: LEAF[node.leaf].films, casesMult: LEAF[node.leaf].cases,
    leaves: new Set([node.leaf]) };
  const [l, r] = node.of.map(derive);
  return {
    edges: 2 + l.edges + r.edges,
    below: new Set([node.of[0].name ?? node.of[0].leaf, node.of[1].name ?? node.of[1].leaf,
      ...l.below, ...r.below]),
    depth: 1 + Math.max(l.depth, r.depth),
    filmsMult: l.filmsMult + r.filmsMult,
    casesMult: l.casesMult + r.casesMult,
    leaves: new Set([...l.leaves, ...r.leaves]),
  };
};
const nA = { leaf: "A" }, nB = { leaf: "B" };
const nC1 = { name: "C1", of: [nA, nB] };
const nC2 = { name: "C2", of: [nC1, nA] };
const H5_DERIVED = (() => {
  const d = derive(nC2);
  return {
    edges: d.edges,
    unique_artifacts: d.below.size,
    max_depth_below: d.depth,
    films_below_by_edge_multiplicity: d.filmsMult,
    films_below_distinct: [...d.leaves].reduce((n, k) => n + LEAF[k].films, 0),
    cases_below_by_edge_multiplicity: d.casesMult,
    cases_below_distinct: [...d.leaves].reduce((n, k) => n + LEAF[k].cases, 0),
  };
})();
/* THE CROSS-CHECK. Never committed without it. */
for (const [k, v] of Object.entries(H5_DERIVED))
  if (base.C2.structure[k] !== v)
    throw new Error(`H5: the hand derivation and this implementation disagree about C2.${k} ` +
      `(derived ${v}, implementation ${base.C2.structure[k]}). One of them is wrong and which one ` +
      `is the finding — the challenge is NOT committed on a disagreement.`);

const CASES = [
  { id: "H1", name: "annotation-only-leaf-change",
    fixture: { leaf: "TRVM-BOUNDED-PROOF-v1", root: ROOTS.A },
    recipe: [{ op: "SET", path: "leaf.annotations.holdout_note", value: "H1" },
             { op: "RECOMPOSE_DAG", note: "rebuild D = C2 ∧ C1, C2 = C1 ∧ A, C1 = A ∧ B" }],
    predicates: [
      { op: "HOLDS", path: "leaf.verified_claim_sem_id" },
      { op: "MOVES", path: "leaf.artifact_root" },
      { op: "HOLDS", path: "D.nested_claim_sem_id" },
      { op: "MOVES", path: "D.artifact_root" },
      { op: "VERDICT_EQ", path: "D.verdict", value: "VERIFIED" }] },
  { id: "H2", name: "reference-set-permutation",
    fixture: { artifact: "D", root: ROOTS.D },
    recipe: [{ op: "REVERSE", path: "artifact.references.operands" }],
    predicates: [
      { op: "HOLDS", path: "D.nested_claim_sem_id" },
      { op: "VERDICT_EQ", path: "D.verdict", value: "VERIFIED" }] },
  { id: "H3", name: "operand-ordered-permutation",
    fixture: { artifact: "D", root: ROOTS.D },
    recipe: [{ op: "REVERSE", path: "artifact.claim.operands" },
             { op: "REVERSE", path: "artifact.references.operands" },
             { op: "RESEAL", note: "recompute nested_claim_sem_id, aggregate_id, structure_sem_id" }],
    predicates: [
      { op: "MOVES", path: "D.nested_claim_sem_id" },
      { op: "VERDICT_EQ", path: "D.verdict", value: "VERIFIED" }] },
  { id: "H4", name: "two-leaf-composition-stands-alone",
    fixture: { artifact: "C1", root: ROOTS.C1 },
    recipe: [{ op: "IDENTITY" }],
    predicates: [{ op: "VERDICT_EQ", path: "C1.verdict", value: "VERIFIED" }] },
  /* H5 IS THE STRUCTURAL DISCRIMINATOR. Seven EXACT equalities over a shared
     child reached by two paths: an edge count that separates multiplicity from
     uniqueness, a distinct-artifact count, a depth, and two multiplicity-versus-
     distinct PAIRS. Getting `films_below_by_edge_multiplicity` right while
     getting `films_below_distinct` wrong is a specific, diagnosable defect —
     traversal that double-counts a shared subtree — which `unique_artifacts <
     edges` could never have separated from a correct answer. */
  { id: "H5", name: "deeper-diamond-shared-child",
    fixture: { artifact: "C2", root: ROOTS.C2 },
    recipe: [{ op: "IDENTITY" }],
    predicates: [
      { op: "VERDICT_EQ", path: "C2.verdict", value: "VERIFIED" },
      ...Object.entries(H5_DERIVED).map(([k, value]) =>
        ({ op: "EQ", path: `candidate.C2.structure.${k}`, value }))] },
  { id: "H6", name: "unknown-semantic-key",
    fixture: { artifact: "D", root: ROOTS.D },
    recipe: [{ op: "SET", path: "artifact.claim.smuggled", value: true },
             { op: "RESEAL" }],
    predicates: [{ op: "REFUSAL_SET_EQ", value: ["nest-vocabulary-unknown"] }] },
  { id: "H7", name: "duplicate-json-member-on-the-wire",
    fixture: { artifact: "C1", root: ROOTS.C1 },
    recipe: [{ op: "WIRE_PREPEND_DUPLICATE_MEMBER", name: "protocol", value: "EVIL",
               note: "serve these octets under C1's own root" }],
    predicates: [{ op: "OUTCOME_EQ", path: "resolve.outcome", value: "non-canonical-wire" }] },
  { id: "H8", name: "policy-weakening",
    fixture: { artifact: "D", root: ROOTS.D },
    recipe: [{ op: "CHECK_WITH_OPTIONS", options: { max_depth: 1000 } }],
    predicates: [{ op: "REFUSAL_SET_EQ", value: ["nest-policy-weakened"] }] },
  { id: "H9", name: "annotation-change-under-the-same-verified-claim",
    fixture: { artifact: "D", root: ROOTS.D },
    recipe: [{ op: "SET", path: "artifact.annotations.holdout_note", value: "H9" }],
    predicates: [
      { op: "HOLDS", path: "D.nested_claim_sem_id" },
      { op: "MOVES", path: "D.artifact_root" },
      { op: "VERDICT_EQ", path: "D.verdict", value: "VERIFIED" }] },
  { id: "H10", name: "reference-to-valid-bytes-for-the-wrong-claim",
    fixture: { artifact: "D", root: ROOTS.D },
    recipe: [{ op: "SET", path: "artifact.references.operands.0.artifact_root", value: ROOTS.C1 },
             { op: "RESEAL" }],
    // EXACT, and measured. "includes" would let five unrelated codes pass.
    predicates: [{ op: "REFUSAL_SET_EQ", value: h10 }] },
];

rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT, { recursive: true });
for (const c of CASES)
  writeFileSync(join(OUT, `${c.id}-${c.name}.json`), canonicalWireBytes({
    id: c.id, name: c.name, fixture: c.fixture, recipe: c.recipe, predicates: c.predicates,
    note: "The implementation APPLIES the recipe to the named frozen fixture and emits " +
      "observations. No SHA-256 produced by any implementation is recorded here; after the reveal " +
      "two implementations compute them independently and a disagreement is a FINDING.",
  }));
writeFileSync(join(OUT, "INDEX.json"), canonicalWireBytes({
  type: "TRVM-PROOF-WIRE-HOLDOUT-v2",
  predicate_ops: ["EQ", "NEQ", "HOLDS", "MOVES", "REFUSAL_SET_EQ", "VERDICT_EQ", "OUTCOME_EQ", "LT"],
  note: "HIDDEN until the independent implementation is frozen. Committed by digest in " +
    "SPEC-RELEASE.json; contents live OUTSIDE the specification tree so shipping the specification " +
    "cannot publish them. Every predicate is frozen BEFORE any implementation is scored — that is " +
    "preregistration, not fitting.",
  entries: CASES.map((c) => ({ id: c.id, name: c.name, file: `${c.id}-${c.name}.json`,
    recipe_steps: c.recipe.length, predicates: c.predicates.length })),
}));
console.log(`HOLDOUT: built ${CASES.length} hidden constructions — ` +
  `${CASES.reduce((n, c) => n + c.recipe.length, 0)} recipe steps and ` +
  `${CASES.reduce((n, c) => n + c.predicates.length, 0)} MACHINE-EVALUABLE predicates over ` +
  `${new Set(CASES.flatMap((c) => c.predicates.map((p) => p.op))).size} operators, ` +
  `0 recorded hashes. H10 commits its EXACT refusal set [${h10.join(", ")}] rather than the ` +
  `"includes" it shipped with, which the exact-set rule already forbade. H5 now commits ` +
  `${Object.keys(H5_DERIVED).length} EXACT structural equalities in place of the one LT that was ` +
  `true of every diamond and of many wrong answers; each was DERIVED from the DAG recurrences and ` +
  `the public leaves' own counts, then CHECKED against this implementation, and the values are ` +
  `deliberately not printed. Commit with \`node spec_release.mjs --update\`.`);
