/* bridge_check.mjs — the cross-plane gate (round 12).
   Feeds the canonical corpus to the C runtime's canonical-bytes emitter and
   requires BYTE equality with the golden pre-hash vectors — the signature
   strings, not merely their digests. Digest equality would let a C canonical
   form that is wrong in a way SHA-256 happens to absorb pass unnoticed; string
   equality localizes the divergence to the character.

   Two implementations, two representations (JS node objects with a heap of
   dups; C packed words with no Dup node at all), one canonical form. If this
   is green, the canonical form is a property of the calculus. If it is red,
   exactly one of the two is wrong and the diff says where.

   Run: node bridge/bridge_check.mjs   (exit 0 iff every state agrees) */
import { readFileSync, existsSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";

const BIN = "bridge/ic32_canon";
const CORPUS = process.env.TRVM_VECTORS ?? "../docs/spec/conformance/vectors/normalize.json";
const fails = [];
const ok = (c, m) => { if (!c) fails.push(m); };

if (!existsSync(BIN)) {
  console.log(`BRIDGE-CHECK: SKIP — ${BIN} not built (make gov-bridge builds it).`);
  console.log("  A missing binary is UNBUILT, never green: this exits nonzero so a");
  console.log("  CI that lost its compiler cannot read as a passing cross-plane claim.");
  process.exit(1);
}

const golden = JSON.parse(readFileSync("golden_prehash_vectors.json", "utf8"));
const corpus = (() => { const j = JSON.parse(readFileSync(CORPUS, "utf8")); return j.vectors ?? j; })();
ok(corpus.length === golden.per_term.length,
  `corpus has ${corpus.length} terms, golden vectors have ${golden.per_term.length}`);

const run = (args) => execFileSync(BIN, args, { input: corpus.map((v) => v.term).join("\n") + "\n", maxBuffer: 1 << 28 })
  .toString().trimEnd().split("\n").map((l) => { const i = l.indexOf("\t"); return { id: l.slice(0, i), sig: l.slice(i + 1) }; });

const stages = [["initial", run([])], ["normal_form", run(["--nf"])]];
let agreed = 0, total = 0;
for (const [stage, rows] of stages) {
  ok(rows.length === corpus.length, `${stage}: C emitted ${rows.length} rows for ${corpus.length} terms`);
  for (let i = 0; i < Math.min(rows.length, golden.per_term.length); i++) {
    const t = golden.per_term[i], want = t[stage], got = rows[i];
    total++;
    // the term the C side was fed must be the term the vector describes
    ok(corpus[i].term === t.term, `${t.name}: corpus term != golden term (row ${i})`);
    // BYTE equality first — this is the rung digest equality cannot reach
    if (got.sig !== want.sem_signature) {
      fails.push(`${t.name}/${stage}: canonical signature differs\n      C  ${got.sig}\n      JS ${want.sem_signature}`);
      continue;
    }
    if (got.id !== want.sem_state_id) {
      fails.push(`${t.name}/${stage}: signatures agree but ids differ — one side's SHA-256 is wrong`);
      continue;
    }
    // and the C side's own hash must be the hash of its own bytes
    ok(createHash("sha256").update(got.sig).digest("hex") === got.id,
      `${t.name}/${stage}: C signature does not hash to the id C reported`);
    agreed++;
  }
}

if (fails.length) {
  console.log("BRIDGE-CHECK: FAIL\n - " + fails.join("\n - "));
  process.exit(1);
}
console.log(`BRIDGE-CHECK: PASS — ${agreed}/${total} states byte-identical across implementations `
  + `(${corpus.length} vectors x {initial, normal form}); C packed-word heap and JS node graph `
  + `reach the same canonical signature STRING, not merely the same digest.`);
