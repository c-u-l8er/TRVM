/* ═══════════════════════════════════════════════════════════════════════════
   js_holdout_adapter.mjs — v0.1.0 — ONE ADAPTER PER IMPLEMENTATION
   law:proof.scorer-implementation-free@1

   The JavaScript side of the boundary `holdout_score_core.mjs` sits on. It reads
   challenges in the frozen recipe grammar, applies them to the frozen public
   fixtures, and writes ONE `TRVM-HOLDOUT-OBSERVATION-v1` document. It evaluates
   no predicate and scores nothing — it does not know whether it passed.

       js_holdout_adapter   TRVM        → observation document
       go-holdout-adapter   Go          → the SAME document shape
       holdout_score_core   documents   → results, importing no TRVM at all

   Until P4.6 this code was a function inside the scorer and the executable path
   was always `score(entry, observeJS(entry))`, so the scorer had never been
   handed an observation by anything that could disagree with it.

   THE SEVEN RECIPE OPERATORS ARE `HOLDOUT-RECIPE-v1.md` §3, and an UNKNOWN one
   is a refusal to emit rather than a skipped step: an adapter that silently
   ignores what it does not understand reports an observation of something other
   than the challenge it was given.
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, writeFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { canonicalWire, artifactRoot, memoryStore, resolveArtifact } from "./cas.mjs";
import { buildDag, nestedClaimSemId, nestAggregateId, nestStructureSemId } from "./nest_bundle.mjs";
import { checkNestBundle } from "./nest_check.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const SPEC = join(HERE, "..", "docs", "spec", "proof-wire");
const GOLDEN = join(SPEC, "vectors", "public");
const clone = (o) => JSON.parse(JSON.stringify(o));
export const RECIPE_OPS = Object.freeze(["IDENTITY", "SET", "REVERSE", "RESEAL",
  "CHECK_WITH_OPTIONS", "WIRE_PREPEND_DUPLICATE_MEMBER", "RECOMPOSE_DAG"]);

function frozenLeaves() {
  const dir = join(GOLDEN, "cas"), found = {};
  for (const f of readdirSync(dir).sort()) {
    const a = JSON.parse(readFileSync(join(dir, f), "utf8"));
    if (a?.protocol === "TRVM-BOUNDED-PROOF-v1") found.A = a;
    if (a?.protocol === "TRVM-BOUNDED-DOMAIN-PROOF-v1") found.B = a;
  }
  return found;
}
/** The wrapper object carries the first segment, so descend through ALL but the
 *  last — the first draft dropped the head segment and then tried to descend
 *  into it anyway. */
const setPath = (o, path, v) => {
  const ks = path.split(".");
  let cur = o;
  for (const k of ks.slice(0, -1)) cur = cur[k];
  cur[ks[ks.length - 1]] = v;
};
/** RESEAL recomputes exactly three derived identities and no fourth, and leaves
 *  one it cannot compute as it stands — a forger cannot always reseal, and that
 *  is a fact about the artifact rather than an error here. */
const reseal = (b) => {
  const t = (f) => { try { f(); } catch { /* see above */ } };
  t(() => { b.claim.nested_claim_sem_id =
    nestedClaimSemId(b.claim.connective, b.claim.scope, b.claim.operands); });
  t(() => { b.aggregate.aggregate_id = nestAggregateId(b.aggregate); });
  t(() => { b.structure.structure_sem_id = nestStructureSemId(b.structure); });
};

/** RESOLVE BY CONTENT ADDRESS, out of the public corpus, by the address alone.
 *  The corpus stores every fixture as `cas/<root>.json`, so the address IS the
 *  lookup key and no label participates. Re-derives the root from the bytes it
 *  got back, because a store is not trusted — that rule is already in the wire
 *  protocol and it applies to a challenge fixture as much as to a citation. */
function resolveFromCorpus(root) {
  if (!/^root-[0-9a-f]{64}$/.test(String(root)))
    throw new Error(`fixture root ${JSON.stringify(root)} is not a well-formed content address`);
  const p = join(GOLDEN, "cas", `${root}.json`);
  if (!existsSync(p))
    throw new Error(`the public corpus holds no bytes under ${root}`);
  return JSON.parse(readFileSync(p, "utf8"));
}

/** A node record of the observation grammar, §3.1. Members the artifact does not
 *  carry are ABSENT rather than null. */
const snap = (into, art, name) => {
  if (!art) return;
  into[name] = { artifact_root: artifactRoot(art) };
  if (art.claim?.nested_claim_sem_id) into[name].nested_claim_sem_id = art.claim.nested_claim_sem_id;
  if (art.structure) into[name].structure = art.structure;
};

export function observe(entry) {
  const { A, B } = frozenLeaves();
  const store = memoryStore(new Map());
  const dag = buildDag(clone(A), clone(B), { cas_dir: null, put: (_d, o) => store.put(o) });
  const baseline = { leaf: A, C1: dag.C1, C2: dag.C2, D: dag.D };
  const obs = { baseline: {}, candidate: {} };
  for (const n of ["C1", "C2", "D"]) snap(obs.baseline, baseline[n], n);
  obs.baseline.leaf = { artifact_root: artifactRoot(A),
    verified_claim_sem_id: dag.C1.claim.operands[0].verified_claim_sem_id };

  let leaf = clone(A), artifact = null, options = {}, wire = null;
  /* THE ROOT IS THE LOOKUP AUTHORITY — HOLDOUT-RECIPE-v1 §2, BOTH HALVES.
     P4.6's adapter read the NAME and never looked at the address at all. P4.6's
     repair looked the object up BY NAME and checked the address afterwards,
     which is a different rule: a corpus whose label and root disagree would
     still have been fetched by label, and "I checked" is the adapter marking its
     own homework. So resolve the CONTENT ADDRESS out of the public corpus
     first, and treat the label as a claim about the manifest to be checked
     second. The observation then REPORTS the address that was resolved, because
     nothing outside the adapter can otherwise tell the two orders apart. */
  const declared = entry.fixture.root;
  const byRoot = resolveFromCorpus(declared);
  const target = entry.fixture.artifact;
  if (target) {
    const labelled = dag[target];
    if (!labelled)
      throw new Error(`fixture ${entry.id}: label ${JSON.stringify(target)} is not a node of the ` +
        `frozen public DAG`);
    if (artifactRoot(labelled) !== declared)
      throw new Error(`fixture ${entry.id}: the challenge's convenience label ${target} names an ` +
        `object with root ${artifactRoot(labelled)}, and the challenge's AUTHORITATIVE root is ` +
        `${declared}. The label is checked against the corpus, never used in its place — this is a ` +
        `disagreement to report, not a typo to work around, and no observation is emitted for it`);
    if (artifactRoot(byRoot) !== declared)
      throw new Error(`fixture ${entry.id}: the corpus object stored under ${declared} re-derives ` +
        `to ${artifactRoot(byRoot)}`);
    artifact = clone(byRoot);
  } else if (artifactRoot(leaf) !== declared)
    throw new Error(`fixture ${entry.id}: leaf fixture declares ${declared} and the frozen leaf ` +
      `has root ${artifactRoot(leaf)}`);
  obs.fixture_root = declared;
  for (const step of entry.recipe) {
    if (!RECIPE_OPS.includes(step.op))
      throw new Error(`unknown recipe operator ${step.op} — the grammar is ` +
        `[${RECIPE_OPS.join(", ")}] and there is no eighth. Refusing to emit an observation of ` +
        `something other than this challenge`);
    if (step.op === "SET" && step.path.startsWith("leaf.")) setPath({ leaf }, step.path, step.value);
    else if (step.op === "SET") setPath({ artifact }, step.path, step.value);
    else if (step.op === "REVERSE") {
      const ks = step.path.split(".").slice(1);
      let cur = artifact; for (const k of ks) cur = cur[k];
      cur.reverse();
    } else if (step.op === "RESEAL") reseal(artifact);
    else if (step.op === "CHECK_WITH_OPTIONS") options = step.options;
    else if (step.op === "WIRE_PREPEND_DUPLICATE_MEMBER")
      wire = { root: artifactRoot(dag[target]),
        bytes: Buffer.from(`{"${step.name}":"${step.value}",` +
          canonicalWire(dag[target]).slice(1), "utf8") };
    else if (step.op === "RECOMPOSE_DAG") {
      const s2 = memoryStore(new Map());
      const d2 = buildDag(leaf, clone(B), { cas_dir: null, put: (_d, o) => s2.put(o) });
      for (const n of ["C1", "C2", "D"]) snap(obs.candidate, d2[n], n);
      obs.candidate.leaf = { artifact_root: artifactRoot(leaf),
        verified_claim_sem_id: d2.C1.claim.operands[0].verified_claim_sem_id };
      const r = checkNestBundle(d2.D, { store: s2 });
      obs.candidate.D.verdict = r.verdict;
      obs.refusal_set = [...new Set(r.refusals.map((x) => x.code))].sort();
      artifact = null;
    }
  }
  if (wire) {
    const s3 = memoryStore(new Map());
    s3.entries.set(wire.root, wire.bytes);
    obs.resolve = { outcome: resolveArtifact(s3, wire.root).outcome };
  }
  if (artifact) {
    const s4 = memoryStore(new Map());
    for (const n of ["A", "B", "C1", "C2", "D"]) s4.put(n === "A" ? A : n === "B" ? B : dag[n]);
    s4.put(artifact);
    const r = checkNestBundle(artifact, { store: s4, ...options });
    snap(obs.candidate, artifact, target);
    obs.candidate[target].verdict = r.verdict;
    obs.refusal_set = [...new Set(r.refusals.map((x) => x.code))].sort();
  }
  return obs;
}

export function observeAll(challenges, specReleaseId) {
  const observations = {};
  for (const entry of challenges) observations[entry.id] = observe(entry);
  return { type: "TRVM-HOLDOUT-OBSERVATION-v1", implementation: "javascript",
    spec_release_id: specReleaseId, observations };
}

/* ── CLI: challenges in, ONE observation document out ────────────────────── */
const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN) {
  const [challengesPath, outPath] = process.argv.slice(2);
  if (!challengesPath || !outPath) {
    console.log("JS-HOLDOUT-ADAPTER: usage — node js_holdout_adapter.mjs <challenges.json> " +
      "<observations.json>");
    process.exit(2);
  }
  const rel = JSON.parse(readFileSync(join(SPEC, "SPEC-RELEASE.json"), "utf8"));
  const challenges = JSON.parse(readFileSync(challengesPath, "utf8"));
  const doc = observeAll(challenges, rel.spec_release_id);
  writeFileSync(outPath, JSON.stringify(doc, null, 1) + "\n");
  console.log(`JS-HOLDOUT-ADAPTER: ${Object.keys(doc.observations).length} observations written to ` +
    `${outPath} against release ${String(rel.spec_release_id).slice(0, 20)}…. This adapter ` +
    `evaluates NO predicate and does not know whether it passed`);
  process.exit(0);
}
