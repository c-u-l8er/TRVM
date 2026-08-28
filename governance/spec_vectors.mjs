/* ═══════════════════════════════════════════════════════════════════════════
   spec_vectors.mjs — v0.3.0 — THE SPEC OWNS THE ORACLE, AND IT IS PORTABLE
   law:proof.conformance-oracle-frozen@1
   law:proof.protocol-oracle-is-environment-independent@1

   v0.1.0 GENERATED the conformance vectors by importing the live implementation
   and WROTE them into the normative spec tree — and `verify.sh` ran it. So the
   implementation computed both the answer and the answer key. Reproduced by
   changing one implementation-only constant and touching no specification:

       ARTIFACT_ROOT_PROTOCOL   "TRVM-ARTIFACT-ROOT-v2" → "…-v999"

       expected root before   root-29c6a08e1c3e5c37…
       expected root after    root-a438f8a5fcafc0df…      ← the key moved
       normative spec still says TRVM-ARTIFACT-ROOT-v2
       SPEC-VECTORS: PASS

   A catastrophic protocol incompatibility, every artifact root changed, and the
   conformance gate green — because the gate asked the implementation what the
   answer should be. That is worth naming:

       An implementation under conformance test may not generate, rewrite or
       redefine the expected values against which that same implementation is
       judged.

   SO THIS FILE HAS TWO MODES AND ONLY ONE OF THEM WRITES.

     VERIFY   (default, and the only mode any gate runs)
              build a CANDIDATE corpus in a scratch directory, compare it
              byte for byte with the FROZEN corpus committed under
              docs/spec/proof-wire/vectors/, and never write there. The spec
              tree is digested before and after and must be unchanged.

     UPDATE   `--update --spec-revision <N>`, run by a human who has decided the
              protocol changed. Writes the frozen corpus and stamps the
              revision. Never invoked by verify.sh, make, or any battery.

   AND v0.2.0's CANDIDATE CAME FROM THE LOCAL PRODUCER, WHICH MADE THE ORACLE
   ENVIRONMENT-COUPLED. It regenerated the positive DAG over the locally
   generated leaf bundles, which carry
   `execution_provenance.executable_artifact_id` -- the identity of the binary
   that produced them. Reproduced by perturbing that one field on 128 sides:

       frozen P1 root   root-b5b33778522764c7...
       local  P1 root   root-d0898fd511b96d7a...
       proof_check      still VERIFIED
       SPEC-VECTORS     FAIL, 17 disagreements

   THAT IS ARTIFACT-VERSION IDENTITY BEHAVING EXACTLY AS P4.1 DESIGNED IT: a
   complete artifact's root MUST move when its provenance bytes move. The defect
   is in the TEST PLANE, which was asking *does this machine recreate the
   producer bytes of the machine that froze revision 1* while claiming to ask
   *does this implementation implement the proof-wire protocol*. Reproducible-
   build practice says the same: reproducibility is meaningful only relative to a
   defined build environment, and no such environment is part of this protocol.

   SO THE CANDIDATE NOW STARTS FROM THE FROZEN LEAF FIXTURES committed under
   `vectors/public/cas/`. They are consumed AS FIXTURES: read, parsed, composed.
   No native producer is launched and no local bundle is read, so this gate is
   portable to any machine with a JavaScript runtime. Whether THIS machine's
   compiler reproduces THAT machine's binary is a different question, it is not
   this protocol's, and `live_dag.mjs` is the gate that exercises local
   end-to-end execution without ever comparing a local complete root to somebody
   else's frozen one.

   AND THE REFUSAL COMPARISON IS EXACT. v0.1.0 recorded a `declared` set beside a
   `measured` set and checked that declared ⊆ measured, so adding a second fault
   to a single-fault vector — `nested_verdict` forged AND an unknown semantic
   key — still passed while the measured set had grown. The frozen corpus holds
   ONE sorted `expect_refusal_set` per vector and the candidate must reproduce
   it exactly. ORDER IS STILL NOT SEMANTIC: the sets are sorted before they are
   frozen, so byte equality of a sorted array IS set equality, and refusal
   precedence remains undecided and unrelied upon.
   ═══════════════════════════════════════════════════════════════════════════ */
import {
  readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync, rmSync, statSync,
} from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join, relative } from "node:path";
import { canonicalWire, canonicalWireBytes, artifactRoot, memoryStore } from "./cas.mjs";
import { JCS_VECTORS } from "./jcs_vectors.mjs";
import {
  buildDag, NEST_PROTOCOL, nestedClaimSemId, nestAggregateId, nestStructureSemId,
} from "./nest_bundle.mjs";
import { checkNestBundle, SHIPPED_POLICY, policyId } from "./nest_check.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const SPEC = join(HERE, "..", "docs", "spec", "proof-wire");
const GOLDEN = join(SPEC, "vectors", "public");
const clone = (o) => JSON.parse(JSON.stringify(o));
const sha = (b) => createHash("sha256").update(b).digest("hex");

/** Digest of every file under a directory, so "the gate did not write to the
 *  spec" is a measurement rather than a promise. */
function treeDigest(dir) {
  if (!existsSync(dir)) return "absent";
  const walk = (d) => readdirSync(d).sort().flatMap((f) => {
    const p = join(d, f);
    return statSync(p).isDirectory() ? walk(p) : [relative(dir, p) + ":" + sha(readFileSync(p))];
  });
  return sha(walk(dir).join("\n"));
}

/* ── THE CANDIDATE CORPUS ───────────────────────────────────────────────── */

/** THE LEAF FIXTURES, READ FROM THE FROZEN CORPUS -- never generated here.
 *  Identified by protocol rather than by filename, so the corpus can be
 *  re-frozen without this function learning a new name. */
function frozenLeaves() {
  const dir = join(GOLDEN, "cas");
  if (!existsSync(dir)) return null;
  const found = {};
  for (const f of readdirSync(dir).sort()) {
    const a = JSON.parse(readFileSync(join(dir, f), "utf8"));
    if (a?.protocol === "TRVM-BOUNDED-PROOF-v1") found.A = a;
    if (a?.protocol === "TRVM-BOUNDED-DOMAIN-PROOF-v1") found.B = a;
  }
  return found.A && found.B ? found : null;
}

function buildCandidate(seed) {
  const leaves = seed ?? frozenLeaves();
  if (!leaves) throw new Error(
    "no frozen leaf fixtures under vectors/public/cas/ -- this gate composes the FROZEN leaves and " +
    "never the local producer, so it cannot run without them");
  const A = leaves.A, B = leaves.B;
  const store = memoryStore(new Map());
  const D = buildDag(clone(A), clone(B), { cas_dir: null, put: (_d, o) => store.put(o) });
  const files = new Map();

  const wire_positive = JCS_VECTORS.map((v) => ({
    name: v.name, source: v.source, input: v.input,
    canonical_text: v.want,
    canonical_utf8_bytes: canonicalWireBytes(v.input).length,
    artifact_root: artifactRoot(v.input),
  }));

  const hex = (b) => Buffer.from(b).toString("hex");
  const honest = { x: "�" };
  const honestBytes = canonicalWireBytes(honest);
  const badUtf8 = Buffer.from(honestBytes); badUtf8[badUtf8.indexOf(0xef)] = 0xff;
  const wire_negative = [
    { name: "invalid-utf8", root: artifactRoot(honest), bytes_hex: hex(badUtf8),
      expect_outcome: "invalid-utf8",
      why: "a raw 0xFF where canonical UTF-8 has EF BF BD. A forgiving decoder substitutes " +
        "U+FFFD and makes two byte strings one artifact" },
    { name: "duplicate-member-name", root: artifactRoot(honest),
      bytes_hex: hex(Buffer.from('{"x":"EVIL",' + canonicalWire(honest).slice(1), "utf8")),
      expect_outcome: "non-canonical-wire",
      why: "an implementation whose parser rejects duplicates earlier MUST still report " +
        "non-canonical-wire; the internal detection stage is not protocol semantics" },
    { name: "pretty-printed", root: artifactRoot(honest),
      bytes_hex: hex(Buffer.from(JSON.stringify(honest, null, 1), "utf8")),
      expect_outcome: "non-canonical-wire", why: "the same object, indented" },
    { name: "honest", root: artifactRoot(honest), bytes_hex: hex(honestBytes),
      expect_outcome: "ok", why: "a wire gate that refused everything would pass every negative" },
  ];

  /* THE COMPLETE CAS FIXTURE. Every child artifact's canonical octets are
     written as a file, so a producer given only this directory can RECONSTRUCT
     the positive example rather than copy its expected hashes. */
  for (const [root, bytes] of store.entries) files.set(join("cas", root + ".json"), bytes);

  const nested_positive = {
    protocol: NEST_PROTOCOL,
    roots: D.roots,
    expect: {
      artifact_root: D.roots.D,
      nested_claim_sem_id: D.D.claim.nested_claim_sem_id,
      aggregate_id: D.D.aggregate.aggregate_id,
      structure_sem_id: D.D.structure.structure_sem_id,
      canonical_utf8_bytes: canonicalWireBytes(D.D).length,
      verdict: "VERIFIED",
      structure: D.D.structure,
      chain_ids: D.D.chain_ids,
      operands: D.D.claim.operands,
      references: D.D.references,
    },
    cas: Object.fromEntries([...store.entries.entries()].map(([r, b]) =>
      [r, { file: `cas/${r}.json`, canonical_utf8_bytes: b.length, sha256: sha(b) }])),
  };
  files.set("nested-positive.json", canonicalWireBytes(D.D));

  const NEGATIVES = [
    { name: "reference-contract-says-address-is-a-warrant",
      mutate: (b) => { b.references.contract.address_is_a_warrant = true; } },
    { name: "operand-carries-a-warrant-field",
      mutate: (b) => { b.claim.operands[0].warrant = "resolved"; } },
    { name: "operand-carries-an-address",
      mutate: (b) => { b.claim.operands[0].artifact_root = b.references.operands[0].artifact_root; } },
    { name: "nested-verdict-forged",
      mutate: (b) => { b.aggregate.nested_verdict = "REFUSED"; } },
    { name: "scope-generalizes-beyond-children",
      mutate: (b) => { b.claim.scope.generalizes_beyond_children = true; } },
  ];
  const tryTo = (f) => { try { f(); } catch { /* a forger cannot always reseal either */ } };
  const nested_negative = NEGATIVES.map((v) => {
    const b = clone(D.D);
    v.mutate(b);
    tryTo(() => { b.claim.nested_claim_sem_id =
      nestedClaimSemId(b.claim.connective, b.claim.scope, b.claim.operands); });
    tryTo(() => { b.aggregate.aggregate_id = nestAggregateId(b.aggregate); });
    tryTo(() => { b.structure.structure_sem_id = nestStructureSemId(b.structure); });
    const r = checkNestBundle(b, { store });
    tryTo(() => files.set(`nested-negative-${v.name}.json`, canonicalWireBytes(b)));
    return { name: v.name, file: `nested-negative-${v.name}.json`, expect_verdict: r.verdict,
      // SORTED, so byte equality of this array is SET equality and nothing here
      // depends on the order refusals happened to be raised in.
      expect_refusal_set: [...new Set(r.refusals.map((x) => x.code))].sort() };
  });

  const manifest = {
    type: "TRVM-PROOF-WIRE-CONFORMANCE-VECTORS-v1",
    spec_revision: null,          // stamped by --update
    note: "FROZEN. The independent producer receives this directory and the normative " +
      "specification beside it, and NOT the JavaScript source. Refusal expectations are SETS, " +
      "sorted: order is not part of the protocol and refusal precedence has not been decided. " +
      "This corpus is the ORACLE and is never regenerated by a verification run — see " +
      "law:proof.conformance-oracle-frozen@1.",
    verifier_policy: { ...SHIPPED_POLICY, policy_id: policyId(SHIPPED_POLICY) },
    wire_positive, wire_negative, nested_positive, nested_negative,
  };
  return { manifest, files };
}

/* ── MODES ──────────────────────────────────────────────────────────────── */

const argv = process.argv.slice(2);
const UPDATE = argv.includes("--update");
const revArg = argv.indexOf("--spec-revision");
const before = treeDigest(SPEC);
const { manifest, files } = buildCandidate();

if (UPDATE) {
  if (revArg < 0 || !argv[revArg + 1]) {
    console.log("SPEC-VECTORS: FAIL — --update requires --spec-revision <N>. Rewriting the oracle " +
      "is a normative act and must name the revision it produces.");
    process.exit(1);
  }
  manifest.spec_revision = argv[revArg + 1];
  rmSync(GOLDEN, { recursive: true, force: true });
  mkdirSync(join(GOLDEN, "cas"), { recursive: true });
  for (const [name, bytes] of files) writeFileSync(join(GOLDEN, name), bytes);
  writeFileSync(join(GOLDEN, "manifest.json"), canonicalWireBytes(manifest));
  console.log(`SPEC-VECTORS: UPDATED to spec revision ${manifest.spec_revision} — ` +
    `${files.size + 1} files written to docs/spec/proof-wire/vectors/. THIS IS A NORMATIVE ACT ` +
    `and no gate performs it: a conformance corpus a verification run can rewrite is a corpus ` +
    `that agrees with whatever the implementation currently does.`);
  process.exit(0);
}

/* VERIFY. Nothing below writes to the spec tree. */
if (!existsSync(join(GOLDEN, "manifest.json"))) {
  console.log("SPEC-VECTORS: FAIL — no frozen corpus at docs/spec/proof-wire/vectors/manifest.json. " +
    "Run `node spec_vectors.mjs --update --spec-revision <N>` deliberately; a verification run " +
    "will not create its own oracle.");
  process.exit(1);
}
const frozenManifest = JSON.parse(readFileSync(join(GOLDEN, "manifest.json"), "utf8"));
manifest.spec_revision = frozenManifest.spec_revision;   // the revision is the SPEC's, not ours

const problems = [];
const candidateBytes = canonicalWireBytes(manifest);
const frozenBytes = readFileSync(join(GOLDEN, "manifest.json"));
if (!candidateBytes.equals(frozenBytes)) {
  /* Say WHICH expectation moved, because "the manifest differs" is a verdict
     and not a diagnosis. */
  const f = frozenManifest, c = manifest;
  /* CANONICAL, NOT INSERTION-ORDERED. This read JSON.stringify on both sides,
     so once a real difference triggered the diagnosis, records with identical
     members in a different insertion order were reported as disagreements too.
     It could not create a false PASS -- the outer comparison is over canonical
     bytes -- but a diagnosis containing invented rows fails on the diagnosis
     side of the verdict/diagnosis distinction P4 established. */
  const enc = (v) => { try { return canonicalWire(v); } catch { return JSON.stringify(v) ?? "undefined"; } };
  const cmp = (label, a, b) => {
    if (enc(a) !== enc(b))
      problems.push(`${label}: frozen ${JSON.stringify(a)} · this implementation ${JSON.stringify(b)}`);
  };
  for (const [i, v] of c.wire_positive.entries()) {
    cmp(`wire_positive[${v.name}].artifact_root`, f.wire_positive?.[i]?.artifact_root, v.artifact_root);
    cmp(`wire_positive[${v.name}].canonical_text`, f.wire_positive?.[i]?.canonical_text, v.canonical_text);
  }
  for (const [i, v] of c.wire_negative.entries())
    cmp(`wire_negative[${v.name}].expect_outcome`, f.wire_negative?.[i]?.expect_outcome, v.expect_outcome);
  for (const k of Object.keys(c.nested_positive.expect))
    cmp(`nested_positive.expect.${k}`, f.nested_positive?.expect?.[k], c.nested_positive.expect[k]);
  for (const [i, v] of c.nested_negative.entries()) {
    cmp(`nested_negative[${v.name}].expect_refusal_set`,
      f.nested_negative?.[i]?.expect_refusal_set, v.expect_refusal_set);
    cmp(`nested_negative[${v.name}].expect_verdict`, f.nested_negative?.[i]?.expect_verdict, v.expect_verdict);
  }
  cmp("verifier_policy", f.verifier_policy, c.verifier_policy);
  if (problems.length === 0) problems.push("the manifest differs from the frozen corpus");
}
/* And every fixture FILE, because an artifact that changed while its recorded
   hashes did not is the same defect in the other direction. */
for (const [name, bytes] of files) {
  const p = join(GOLDEN, name);
  if (!existsSync(p)) { problems.push(`fixture ${name} is missing from the frozen corpus`); continue; }
  if (!Buffer.from(bytes).equals(readFileSync(p)))
    problems.push(`fixture ${name} does not match the frozen bytes`);
}

const after = treeDigest(SPEC);
if (after !== before)
  problems.push("THE SPECIFICATION TREE CHANGED DURING A VERIFICATION RUN — a conformance gate " +
    "that can write its own oracle has not tested anything");

for (const p of problems.slice(0, 12)) console.log(`  ${p}`);
console.log(problems.length === 0
  ? `SPEC-VECTORS: PASS — this implementation reproduces the FROZEN corpus at spec revision ` +
    `${manifest.spec_revision}: ${manifest.wire_positive.length} positive wire vectors, ` +
    `${manifest.wire_negative.length} negative wire vectors, a positive nested artifact with ` +
    `${Object.keys(manifest.nested_positive.cas).length} complete CAS fixtures, and ` +
    `${manifest.nested_negative.length} negative protocol vectors whose expected refusal SETS are ` +
    `compared for EXACT equality — a sorted array, so byte equality is set equality and refusal ` +
    `ORDER remains outside the protocol. THE CANDIDATE WAS COMPOSED FROM THE FROZEN LEAF ` +
    `FIXTURES and no local producer was launched, so this gate asks whether this ` +
    `implementation implements the PROTOCOL rather than whether this machine recreates ` +
    `another machine's compiler output. THE CORPUS WAS NOT REGENERATED: it was read, and the ` +
    `specification tree is byte-identical before and after this run. An implementation that ` +
    `computes its own answer key has not been tested against anything`
  : `SPEC-VECTORS: FAIL — ${problems.length} disagreement(s) with the FROZEN corpus at spec ` +
    `revision ${manifest.spec_revision}. This implementation does not conform to the normative ` +
    `specification. Repair the implementation, or — if the protocol genuinely changed — issue a ` +
    `numbered spec revision and run \`--update --spec-revision <N>\` deliberately`);
process.exit(problems.length === 0 ? 0 : 1);
