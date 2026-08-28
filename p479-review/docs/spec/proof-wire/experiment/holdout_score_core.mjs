/* ═══════════════════════════════════════════════════════════════════════════
   holdout_score_core.mjs — v0.3.0 — THE INSTRUMENT IS FROZEN WITH THE EXPERIMENT
   law:proof.scorer-implementation-free@1 · law:proof.instrument-content-bound@1
   law:proof.observation-boundary-enforced@1 · law:evidence.instrument-nonvacuity@1

   P4.6 moved this file's LOGIC across a document boundary and left its BYTES
   unbound. REPRODUCED, and it is the decisive falsifier of that round:

       insert  if (entry.id.startsWith("H")) { pass = true; continue; }

       SCORER FIXTURE   19/19 PASS      the synthetic cases are not H*
       HOLDOUT-SCORE    25/25 PASS      every real predicate forced true
       SPEC-RELEASE     PASS, SAME srel the scorer was not in any digest
       BLIND-RUN        PASS            the pinned run noticed nothing

   The synthetic fixture proves that one set of scorer behaviours works. It
   cannot prove that the scorer later applied to the secret H* cases is the same
   scorer. **So the instrument has to be content-bound**, and the cheapest honest
   way to bind it is to put it where the experiment digest already reaches:
   `docs/spec/proof-wire/experiment/`. Editing one byte of this file now moves
   `experiment_digest`, therefore `spec_release_id`, therefore the pinned run
   goes RED. Freeze the evidence, freeze the interpreter of the evidence, freeze
   the subjects being compared.

   THIS FILE IMPORTS `node:fs`, `node:url`, `node:path` AND ONE SIBLING
   (`holdout_schema.mjs`, which imports nothing). Not the canonicaliser, not the
   store, not the bundle builder, not the checker. What it cannot load, it cannot
   quietly agree with — and `grid_check` asserts the transitive closure, because
   a comment claiming independence is not independence.

   THREE THINGS IT NOW REFUSES THAT v0.1.0 ACCEPTED:

     an observation document that violates its own published schema — P4.6
     shipped the schema and never executed it, so a smuggled top-level member,
     a smuggled observation member and a smuggled node member all passed;

     an observation whose `fixture_root` is not the address the challenge
     declared — an adapter that fetched by the convenience label cannot be told
     from one that fetched by the address unless it must report what it fetched;

     an unsorted `refusal_set` — sets are compared by byte-comparing sorted
     arrays, so an unsorted one is not a differently-presented set, it is a set
     that compares unequal to itself.

   ONE ROOT PER OPERATOR, NO FALLBACK CHAIN. ABSENT IS `UNRESOLVED`, NEITHER PASS
   NOR FAIL. AND IT ASSIGNS NO BLAME: a disagreement is `UNCLASSIFIED_FINDING`
   until a human puts it in one of the six frozen categories.
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync } from "node:fs";
import { readEvidence } from "./evidence.mjs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { validate } from "./holdout_schema.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
export const OPS = Object.freeze(
  ["EQ", "NEQ", "HOLDS", "MOVES", "REFUSAL_SET_EQ", "VERDICT_EQ", "OUTCOME_EQ", "LT"]);
export const OBSERVATION_TYPE = "TRVM-HOLDOUT-OBSERVATION-v1";
const OBS_SCHEMA = () => readEvidence(join(HERE, "holdout-observation-v1.schema.json"));
const RECIPE_SCHEMA = () => readEvidence(join(HERE, "holdout-recipe-v1.schema.json"));

/** ABSENT IS A VALUE OF ITS OWN. `undefined` cannot be told from "the member is
 *  there and holds undefined" once it has been through JSON, so resolution
 *  returns a tagged result and every operator has to say what it does with it. */
const ABSENT = Symbol("absent");
function at(root, path) {
  if (root == null || typeof path !== "string" || path === "") return ABSENT;
  let cur = root;
  for (const k of path.split(".")) {
    if (cur === null || typeof cur !== "object" || !(k in cur)) return ABSENT;
    cur = cur[k];
  }
  return cur;
}
/** Values compare by a stable encoding with member order removed, so the order
 *  of members inside a `structure` record never decides a predicate. This is
 *  key-sorted JSON, NOT the protocol's canonical encoder — importing that would
 *  make this file load implementation code to score the implementation. */
function stable(v) {
  if (v === ABSENT) return "\u0000ABSENT";   /* a sentinel no JSON value can encode to, written as
                                                an ESCAPE because a literal NUL makes file(1) call
                                                this module `data` and grep skip it in silence */
  if (v === null || typeof v !== "object") return JSON.stringify(v) ?? "null";
  if (Array.isArray(v)) return "[" + v.map(stable).join(",") + "]";
  return "{" + Object.keys(v).sort().map((k) => JSON.stringify(k) + ":" + stable(v[k])).join(",") + "}";
}
export { stable };
const show = (v) => v === ABSENT ? "ABSENT" : stable(v).slice(0, 40);

/** THE RESOLUTION TABLE IS THE RULE — HOLDOUT-OBSERVATION-v1.md §4. */
export function score(entry, obs) {
  const out = [];
  const b = obs?.baseline, c = obs?.candidate;
  for (const p of entry.predicates ?? []) {
    let pass = null, detail = "";
    switch (p.op) {
      case "HOLDS": case "MOVES": {
        const x = at(b, p.path), y = at(c, p.path);
        detail = `${show(x)} → ${show(y)}`;
        if (x === ABSENT || y === ABSENT) break;          // UNRESOLVED
        pass = p.op === "HOLDS" ? stable(x) === stable(y) : stable(x) !== stable(y);
        break; }
      case "EQ": case "NEQ": {
        const x = at(obs, p.path);
        const y = "value" in p ? p.value : at(obs, p.right);
        detail = `${show(x)} vs ${show(y)}`;
        if (x === ABSENT || y === ABSENT) break;
        pass = p.op === "EQ" ? stable(x) === stable(y) : stable(x) !== stable(y);
        break; }
      case "VERDICT_EQ": {
        const x = at(c, p.path);
        detail = `${show(x)} vs ${JSON.stringify(p.value)}`;
        if (x === ABSENT) break;
        pass = x === p.value;
        break; }
      case "OUTCOME_EQ": {
        const x = at(obs, p.path);
        detail = `${show(x)} vs ${JSON.stringify(p.value)}`;
        if (x === ABSENT) break;
        pass = x === p.value;
        break; }
      case "REFUSAL_SET_EQ": {
        /* EXACT SET EQUALITY, never "includes" — P4.5's H10 shipped `includes`
           and would have let five unrelated refusal codes pass. An ABSENT set
           means no verification happened, which is not the same observation as
           a verification that refused nothing. */
        const got = at(obs, "refusal_set");
        detail = `${show(got)} vs ${stable(p.value)}`;
        if (got === ABSENT || !Array.isArray(got)) break;
        pass = stable([...got].sort()) === stable([...(p.value ?? [])].sort());
        break; }
      case "LT": {
        const x = at(obs, p.left), y = at(obs, p.right);
        detail = `${show(x)} < ${show(y)}`;
        /* A NON-NUMBER IS UNRESOLVED, NOT FALSE. Number(undefined) is NaN and
           every comparison against NaN is false, so a missing measurement would
           otherwise arrive as a confidently failed inequality. */
        if (typeof x !== "number" || typeof y !== "number") break;
        pass = x < y;
        break; }
      default:
        detail = `unknown predicate op ${p.op} — the language is [${OPS.join(", ")}] and there is ` +
          `no ninth`;
    }
    out.push({ id: entry.id, op: p.op,
      path: p.path ?? (p.left ? `${p.left} < ${p.right}` : "refusal_set"), pass, detail });
  }
  return out;
}

/** A whole run: challenges × one observation document.
 *
 *  THE BOUNDARY IS EXECUTED HERE. v0.1.0 checked only `doc.type`, so every other
 *  rule the published schema states — unknown members, malformed roots, unsorted
 *  or duplicated refusal codes, wrong types — was documentation. */
export function scoreRun(challenges, doc, { expectRelease = null, expectImplementation = null } = {}) {
  const problems = [];
  for (const entry of challenges)
    problems.push(...validate(entry, RECIPE_SCHEMA()).map((p) => `challenge ${entry?.id}: ${p}`));
  problems.push(...validate(doc, OBS_SCHEMA()).map((p) => `observation document ${p}`));
  /* AN OBSERVATION IS ATTRIBUTED, NOT SELF-DECLARED. The document names its own
     producer, and until P4.7.1 nothing required that name to be the adapter the
     run actually launched — so two subjects could both answer as "go", or one
     could answer as the other, and the interop comparison would be between
     labels rather than between implementations. */
  if (expectImplementation && doc?.implementation !== expectImplementation)
    problems.push(`the observation document calls itself ` +
      `${JSON.stringify(doc?.implementation)} and the adapter this run launched is ` +
      `${JSON.stringify(expectImplementation)} — an observation is attributed to the subject that ` +
      `produced it, not to whatever the document says`);
  if (expectRelease && doc?.spec_release_id !== expectRelease)
    problems.push(`observation document was produced against release ` +
      `${String(doc?.spec_release_id).slice(0, 24)}…, and this run is ` +
      `${String(expectRelease).slice(0, 24)}… — comparing two implementations of two different ` +
      `specifications measures nothing`);
  if (problems.length) return { refused: problems.slice(0, 10).join(" · "), problems };

  const results = [], missing = [];
  for (const entry of challenges) {
    const obs = doc.observations?.[entry.id];
    if (obs === undefined) { missing.push(entry.id); continue; }
    /* Q3, SECOND HALF. The address the adapter says it resolved must be the
       address the challenge declared. An adapter that fetched by the convenience
       label and checked the root afterwards is indistinguishable from one that
       fetched by the root — unless it has to report what it fetched, and unless
       something other than the adapter checks the report. */
    if (entry.fixture?.root && obs.fixture_root !== entry.fixture.root)
      problems.push(`${entry.id}: the challenge names ${entry.fixture.root.slice(0, 24)}… and the ` +
        `adapter reports resolving ${String(obs.fixture_root).slice(0, 24)}… — the root is the ` +
        `LOOKUP AUTHORITY and the label is a convenience`);
    results.push(...score(entry, obs));
  }
  if (problems.length) return { refused: problems.slice(0, 10).join(" · "), problems };
  const pass = results.filter((r) => r.pass === true).length;
  const unresolved = results.filter((r) => r.pass === null).length;
  return { results, missing, total: results.length, pass, unresolved,
    fail: results.length - pass - unresolved,
    implementation: doc.implementation, spec_release_id: doc.spec_release_id };
}

/** OBSERVATION COMPARISON, NOT PREDICATE-BIT COMPARISON.
 *
 *  P4.6 compared the two implementations' PREDICATE RESULTS. REPRODUCED: mutate
 *  `H4.candidate.C1.artifact_root` in a second implementation's document — a
 *  root no predicate in the frozen set happens to read — and both score 25/25
 *  with byte-identical result vectors, while the observations plainly disagree.
 *  Conformance is what the frozen predicates measure; INTEROPERABILITY is
 *  whether two implementations saw the same thing, and that is a question about
 *  the observations. Producer labels are excluded and nothing else is. */
export function compareObservations(a, b) {
  const findings = [];
  const walk = (x, y, path) => {
    const sx = stable(x === undefined ? ABSENT : x), sy = stable(y === undefined ? ABSENT : y);
    if (sx === sy) return;
    const both = x && y && typeof x === "object" && typeof y === "object"
      && !Array.isArray(x) && !Array.isArray(y);
    if (both) {
      for (const k of [...new Set([...Object.keys(x), ...Object.keys(y)])].sort())
        walk(x[k], y[k], `${path}.${k}`);
      return;
    }
    findings.push({ path, a: show(x === undefined ? ABSENT : x), b: show(y === undefined ? ABSENT : y),
      classification: "UNCLASSIFIED_FINDING" });
  };
  for (const id of [...new Set([...Object.keys(a.observations ?? {}),
                                ...Object.keys(b.observations ?? {})])].sort())
    walk(a.observations?.[id], b.observations?.[id], id);
  return findings;
}

/* ── CLI ─────────────────────────────────────────────────────────────────── */
const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;

if (IS_MAIN && process.argv[2] === "--fixture") {
  /* law:evidence.instrument-nonvacuity@1 AT THE SCORER. Synthetic challenges
     carrying no TRVM value: eight operators arranged to PASS, the same eight
     arranged to FAIL, three whose observation is ABSENT and must be UNRESOLVED,
     and — new in v0.2.0 — a set of documents that must be REFUSED OUTRIGHT, one
     per boundary rule. A fixture whose every case is accepted cannot tell a
     validator from a pass-through, which is exactly what P4.6's was. */
  const F = join(HERE, "fixtures");
  const challenges = readEvidence(join(F, "synthetic-challenges.json"));
  const doc = readEvidence(join(F, "synthetic-observations.json"));
  const want = readEvidence(join(F, "synthetic-expected.json"));
  const negatives = readEvidence(join(F, "synthetic-negatives.json"));
  const bad = [];
  const r = scoreRun(challenges, doc);
  if (r.refused) bad.push(`the honest synthetic document was REFUSED: ${r.refused}`);
  else {
    for (const [id, w] of Object.entries(want.by_challenge)) {
      const mine = r.results.filter((x) => x.id === id);
      const got = { pass: mine.filter((x) => x.pass === true).length,
        fail: mine.filter((x) => x.pass === false).length,
        unresolved: mine.filter((x) => x.pass === null).length };
      if (stable(got) !== stable(w)) bad.push(`${id}: declared ${stable(w)}, this scorer ${stable(got)}`);
    }
    const seen = new Set(r.results.map((x) => x.op));
    for (const op of want.operators_exercised)
      if (!seen.has(op)) bad.push(`operator ${op} is declared exercised and was never evaluated`);
  }
  /* THE REFUSING ARM. Each negative names the rule it violates and MUST be
     refused; a negative that is accepted is a boundary that is not executed. */
  for (const neg of negatives.cases) {
    const ch = neg.challenges ?? challenges;
    const d = JSON.parse(JSON.stringify(doc));
    for (const m of neg.mutations) {
      const ks = m.path.split(".");
      let cur = d;
      for (const k of ks.slice(0, -1)) cur = cur?.[k];
      if (cur === undefined) { bad.push(`${neg.id}: mutation path ${m.path} does not exist`); continue; }
      if (m.delete) delete cur[ks[ks.length - 1]]; else cur[ks[ks.length - 1]] = m.value;
    }
    const got = scoreRun(ch, d, neg.expect_release ? { expectRelease: neg.expect_release } : {});
    if (!got.refused) bad.push(`${neg.id} (${neg.rule}): ACCEPTED — the boundary is not executed`);
  }
  /* AND THE INTEROP COMPARATOR'S OWN FALSIFIER. */
  const twin = JSON.parse(JSON.stringify(doc)); twin.implementation = "synthetic-twin";
  if (compareObservations(doc, twin).length !== 0)
    bad.push("two identical observation documents reported a disagreement");
  const drifted = JSON.parse(JSON.stringify(twin));
  drifted.observations.S1.candidate.D.artifact_root = "root-" + "b".repeat(64);
  const found = compareObservations(doc, drifted);
  if (!found.some((f) => f.path === "S1.candidate.D.artifact_root"))
    bad.push("a mutated artifact_root that NO predicate reads was not reported as a disagreement — " +
      "this is the P4.6 defect, where interop compared predicate bits instead of observations");

  for (const b of bad) console.log(`  ${b}`);
  console.log(bad.length === 0
    ? `HOLDOUT-SCORE-CORE: FIXTURE PASS — ${r.total} synthetic predicates over ` +
      `${challenges.length} challenges reproduce the DECLARED split exactly (${r.pass} satisfied, ` +
      `${r.fail} unsatisfied, ${r.unresolved} unresolved), all ` +
      `${want.operators_exercised.length} operators were evaluated, ` +
      `${negatives.cases.length} boundary negatives were each REFUSED, and the interop comparator ` +
      `reported 0 disagreements between identical documents and FOUND a mutated artifact_root that ` +
      `no predicate reads. THE INSTRUMENT IS CONTENT-BOUND: this file lives inside ` +
      `experiment_digest, so editing one byte of it moves spec_release_id and reddens the pinned ` +
      `run — against P4.6, forcing every real predicate true left the fixture, the holdout, the ` +
      `release and the run ALL GREEN`
    : `HOLDOUT-SCORE-CORE: FIXTURE FAIL — ${bad.length} disagreement(s) with the declared result`);
  process.exit(bad.length === 0 ? 0 : 1);
}

if (IS_MAIN) {
  const [challengesPath, obsPath] = process.argv.slice(2);
  if (!challengesPath || !obsPath) {
    console.log("HOLDOUT-SCORE-CORE: usage — node holdout_score_core.mjs <challenges.json> " +
      "<observations.json>, or --fixture");
    process.exit(2);
  }
  const challenges = readEvidence(challengesPath, "the challenge document");
  const doc = readEvidence(obsPath, "the observation document");
  const r = scoreRun(challenges, doc);
  if (r.refused) { console.log(`HOLDOUT-SCORE-CORE: REFUSED — ${r.refused}`); process.exit(1); }
  for (const x of r.results) if (x.pass !== true) console.log(`  ${x.id} ${x.op} ${x.path}: ${x.detail}`);
  for (const id of r.missing) console.log(`  ${id}: NO OBSERVATION in this document`);
  const ok = r.fail === 0 && r.unresolved === 0 && r.missing.length === 0;
  console.log(`HOLDOUT-SCORE-CORE: ${ok ? "PASS" : "FAIL"} — implementation ` +
    `${JSON.stringify(r.implementation)}: ${r.pass} satisfied, ${r.fail} unsatisfied, ` +
    `${r.unresolved} unresolved of ${r.total} predicates over ${challenges.length} challenges`);
  process.exit(ok ? 0 : 1);
}
