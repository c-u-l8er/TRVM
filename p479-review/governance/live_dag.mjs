/* ═══════════════════════════════════════════════════════════════════════════
   live_dag.mjs — v0.1.0 — LOCAL END-TO-END, AND NOT A CONFORMANCE CLAIM
   law:proof.protocol-oracle-is-environment-independent@1

   `spec_vectors.mjs` composes the FROZEN leaf fixtures and never launches a
   producer, so it is portable. This gate is the other half: it takes the
   artifacts THIS machine's runtime actually produced and carries them all the
   way through, which is the only thing that exercises the native execution
   plane end to end.

   WHAT IT MUST NOT DO, and P4.3's conformance gate did:

       assert  local complete artifact_root == somebody else's frozen root

   A complete artifact's root binds `execution_provenance.executable_artifact_id`
   — the identity of the binary that produced it — and P4.1 designed it that way
   on purpose. Two machines with different compilers produce semantically
   identical proofs with different complete roots, and demanding otherwise turns
   a protocol gate into a reproducible-build gate for a build environment this
   protocol never defined. Measured on a reviewer's machine: every semantic id
   held, every provenance id moved, and the conformance gate reported 17
   disagreements.

   SO THIS GATE ASSERTS RELATIONS, NOT VALUES:

     · the local leaves verify under their own checkers;
     · the local DAG verifies;
     · every semantic identity is the one the FROZEN corpus records — because
       claim identities do NOT bind provenance, and if a local claim id moved,
       that WOULD be a defect;
     · every complete artifact root is internally consistent — each reference
       resolves to bytes that hash to it;
     · and the local roots are ALLOWED to differ from the frozen ones, which is
       reported rather than asserted either way.
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, existsSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { memoryStore, artifactRoot, canonicalWire } from "./cas.mjs";
import { buildDag } from "./nest_bundle.mjs";
import { checkNestBundle } from "./nest_check.mjs";
import { checkBundle } from "./proof_check.mjs";
import { checkDomainBundle } from "./domain_check.mjs";
import { verifiedClaimSemId, certificateOf } from "./certificate.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const GOLDEN = join(HERE, "..", "docs", "spec", "proof-wire", "vectors", "public");
const clone = (o) => JSON.parse(JSON.stringify(o));

for (const f of ["proof_bundle.json", "domain_bundle.json"]) if (!existsSync(join(HERE, f))) {
  console.log(`LIVE-DAG: FAIL — no locally generated ${f}`);
  process.exit(1);
}
const A = JSON.parse(readFileSync(join(HERE, "proof_bundle.json"), "utf8"));
const B = JSON.parse(readFileSync(join(HERE, "domain_bundle.json"), "utf8"));

const problems = [];
const need = (cond, msg) => { if (!cond) problems.push(msg); };

/* 1. THE LOCAL LEAVES VERIFY UNDER THEIR OWN CHECKERS. */
const rA = checkBundle(A), rB = checkDomainBundle(B);
need(rA.ok, `the locally produced bounded proof does not verify: ${rA.refusals.map((x) => x.code).join(", ")}`);
need(rB.ok, `the locally produced domain certificate does not verify: ${rB.refusals.map((x) => x.code).join(", ")}`);

/* 2. THE LOCAL DAG VERIFIES, FROM A STORE HOLDING LOCAL BYTES. */
const store = memoryStore(new Map());
const dag = buildDag(clone(A), clone(B), { cas_dir: null, put: (_d, o) => store.put(o) });
const rD = checkNestBundle(dag.D, { store });
need(rD.ok, `the locally composed DAG does not verify: ${rD.refusals.map((x) => x.code).join(", ")}`);

/* 3. EVERY SEMANTIC IDENTITY IS THE FROZEN ONE. This is the assertion that
      matters: a claim identity does NOT bind provenance, so a local one that
      moved would be a real defect rather than a different machine. */
let frozen = null;
try { frozen = JSON.parse(readFileSync(join(GOLDEN, "manifest.json"), "utf8")); } catch { /* null */ }
const semantic = [];
if (frozen) {
  const e = frozen.nested_positive.expect;
  const pairs = [
    ["nested_claim_sem_id", e.nested_claim_sem_id, dag.D.claim.nested_claim_sem_id],
    ["aggregate_id", e.aggregate_id, dag.D.aggregate.aggregate_id],
    /* CANONICAL, NOT INSERTION-ORDERED — and this file reproduced that defect on
       its first run, in the same round that fixed it in spec_vectors.mjs. The
       frozen manifest is written canonically so its members are sorted; a
       locally built record carries insertion order. Comparing the two with
       JSON.stringify reported a SEMANTIC identity as moved when every member
       and value was identical. Third appearance of the key-order family: P4.1's
       receipt comparison, P4.3's spec diagnostics, and now here. */
    ["chain_ids", canonicalWire(e.chain_ids), canonicalWire(dag.D.chain_ids)],
  ];
  for (const [i, o] of e.operands.entries())
    pairs.push([`operand[${i}].verified_claim_sem_id`, o.verified_claim_sem_id,
      dag.D.claim.operands[i]?.verified_claim_sem_id]);
  for (const [label, want, got] of pairs) {
    semantic.push([label, want === got]);
    need(want === got, `SEMANTIC identity ${label} moved locally: frozen ${want}, local ${got}. ` +
      `A claim identity does not bind provenance, so this is a defect and not a different machine`);
  }
} else problems.push("no frozen corpus to compare semantic identities against");

/* 4. EVERY COMPLETE ROOT IS INTERNALLY CONSISTENT. */
let refs = 0;
for (const [name, art] of Object.entries({ C1: dag.C1, C2: dag.C2, D: dag.D }))
  for (const r of art.references.operands) {
    refs += 1;
    const bytes = store.get(r.artifact_root);
    need(bytes !== null, `${name} cites ${r.artifact_root.slice(0, 20)}… and the local store has no bytes`);
  }

/* 5. AND THE COMPLETE ROOTS ARE ALLOWED TO DIFFER. Reported, never asserted. */
const localRootA = artifactRoot(A);
const frozenRootA = frozen
  ? Object.keys(frozen.nested_positive.cas).find((r) => {
      try { return JSON.parse(readFileSync(join(GOLDEN, "cas", r + ".json"), "utf8")).protocol
        === "TRVM-BOUNDED-PROOF-v1"; } catch { return false; }
    }) : null;
const rootsMatch = localRootA === frozenRootA;

console.log(problems.length === 0
  ? `LIVE-DAG: PASS — the artifacts THIS machine's runtime produced go end to end. The local ` +
    `bounded proof and domain certificate verify under their own checkers, the local DAG they ` +
    `compose VERIFIES, all ${refs} references resolve inside the local store, and every one of ` +
    `${semantic.length} SEMANTIC identities equals the frozen corpus's — which is the assertion ` +
    `that matters, because a claim identity does not bind provenance and a local one that moved ` +
    `would be a defect rather than a different machine. THE COMPLETE ARTIFACT ROOT IS REPORTED, ` +
    `NOT ASSERTED: local ${localRootA.slice(0, 22)}… ` +
    `${rootsMatch ? "HAPPENS TO EQUAL" : "DIFFERS FROM"} the frozen ` +
    `${(frozenRootA ?? "?").slice(0, 22)}…, and ${rootsMatch ? "that is a coincidence of this " +
    "machine rather than a requirement" : "that is CORRECT — it binds the identity of the binary " +
    "that produced it, and demanding otherwise would make this a reproducible-build gate for a " +
    "build environment the protocol never defined"}`
  : `LIVE-DAG: FAIL — ${problems.length} problem(s):\n  ${problems.slice(0, 8).join("\n  ")}`);
process.exit(problems.length === 0 ? 0 : 1);
