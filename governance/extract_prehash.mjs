/* ═══════════════════════════════════════════════════════════════════════════
   extract_prehash.mjs — v1 — emits golden_prehash_vectors.json

   Closes the gap the ic32 handoff pack declared as Lane A's: milestone #5
   (`semStateId`-compatible canonical serialization) could previously be
   checked only at DIGEST level, so a second implementation learned nothing
   from a mismatch beyond "wrong". These are the PRE-HASH BYTES — the
   canonical signature strings of SEMSTATE-CANONICAL-v1 §5 — so ic32 can diff
   the string and see WHERE its canonical form diverges.

   The bytes come from the kernel's own `stateSignature`, which `stateDigest`
   is now defined in terms of (v1.1.0, additive). There is one code path: a
   vector cannot drift from the digest it explains, because the digest is the
   hash OF the vector.

   Every row carries two independently checkable bindings:
     · sha256(sem_signature) === sem_state_id            (engine-free)
     · normal_form.nf_id === refinement_receipt's nf_id  (binds to shipped
       golden evidence — these vectors cannot silently describe a different
       corpus than the one the receipts already committed)

   Run: node extract_prehash.mjs   (writes golden_prehash_vectors.json)
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import {
  KERNEL_VERSION, FloatRt, parse, extrude, readback, semId,
  stateSignature, semStateSignature, semStateId, foldCanonicalLive,
  normalizeFloat, EMBEDDED_VECTORS, projectVector,
} from "./trvm_law_kernel.mjs";

// Same corpus projection the kernel commits to, so vectors extracted from the
// canonical file and from the embedded set are the same corpus by construction.
// TRVM_VECTORS repoints this at docs/spec/conformance/vectors/normalize.json.
const CORPUS = (process.env.TRVM_VECTORS
  ? (() => { const j = JSON.parse(readFileSync(process.env.TRVM_VECTORS, "utf8")); return j.vectors ?? j; })()
  : EMBEDDED_VECTORS).map(projectVector);

const sha = (s) => createHash("sha256").update(s).digest("hex");
const js = (o) => JSON.stringify(o);

const cert = JSON.parse(readFileSync("scheduler_certificate.json", "utf8"));
const refine = JSON.parse(readFileSync("refinement_receipt.json", "utf8"));
const refById = new Map(refine.per_term.map((r) => [r.name, r]));

// mulberry32 seed + pick match runFloat's defaults; the semantic state is
// schedule-independent by law:state.semantic-quotient@1, and the nf_id
// anchor below is what proves we landed where the receipts say.
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const per_term = [];
const mismatches = [];
for (const v of CORPUS) {
  const frt = new FloatRt();
  let root = extrude(frt, parse(frt, v.term));

  // initial state — before any interaction
  const initSig = semStateSignature(frt, root);
  const initId = semStateId(frt, root);

  // normal form — reached under the default free-pool schedule
  const out = normalizeFloat(frt, root, (rs, r) => rs[Math.floor(r() * rs.length)],
    mulberry32(0xF10A7), {});
  root = out.root;
  const nfSig = semStateSignature(frt, root);
  const nfId = semStateId(frt, root);
  const nfStr = readback(frt, root).str;
  const nf_id = semId(nfStr);

  // ── the anchors: this row must agree with evidence already shipped ──
  const ref = refById.get(v.name);
  if (!ref) mismatches.push(`${v.name}: absent from refinement_receipt`);
  else if (ref.nf_id !== nf_id) mismatches.push(`${v.name}: nf_id ${nf_id} != receipt ${ref.nf_id}`);
  if (nfStr !== v.nf) mismatches.push(`${v.name}: printed nf "${nfStr}" != corpus "${v.nf}"`);
  if (sha(initSig) !== initId) mismatches.push(`${v.name}: initial signature does not hash to its id`);
  if (sha(nfSig) !== nfId) mismatches.push(`${v.name}: nf signature does not hash to its id`);

  per_term.push({
    name: v.name,
    term: v.term,
    termination: out.termination,
    steps: out.steps,
    initial: { sem_signature: initSig, sem_state_id: initId },
    normal_form: { nf: nfStr, sem_signature: nfSig, sem_state_id: nfId, nf_id },
  });
}

// ── §5 internal compaction: the 80/81 boundary, which had no golden fixture ──
// Built from real states rather than synthetic strings: nest applications of a
// free variable until the root signature crosses 80 characters. The row records
// the last uncompacted width and the first compacted one, with both signatures,
// so an implementation can bracket its own boundary against ours.
function nestApp(n) {                       // (F (F ... (F F)))
  let s = "F";
  for (let i = 0; i < n; i++) s = "(F " + s + ")";
  return s;
}
let below = null, above = null;
for (let n = 0; n <= 40 && !above; n++) {
  const frt = new FloatRt();
  const root = extrude(frt, parse(frt, nestApp(n)));
  const sig = semStateSignature(frt, root);
  const compacted = sig.startsWith("#") && sig.length === 65;
  const row = { nesting: n, term: nestApp(n), sem_signature: sig, length: sig.length,
                compacted, sem_state_id: semStateId(frt, root) };
  if (!compacted) below = row; else above = row;
}
// State WHAT was compacted, not merely that something was. The compacted row's
// pre-compaction string is the §5 App rule applied to the previous nesting's
// signature — and the reconstruction PROVES ITSELF: '#' + sha256(it) must equal
// the compacted signature the oracle actually emitted, or extraction refuses.
// An implementation that gets the boundary wrong sees the exact string it
// should have hashed, which is the whole point of shipping bytes.
let precompaction = null;
if (below && above && above.nesting === below.nesting + 1) {
  const candidate = "A(Ffree:F," + below.sem_signature + ")";
  if ("#" + sha(candidate) !== above.sem_signature) {
    mismatches.push(`compaction: reconstructed pre-compaction string does not hash to the emitted signature`);
  } else {
    precompaction = { signature: candidate, length: candidate.length };
  }
}

const compaction = {
  rule: "SEMSTATE-CANONICAL-v1 §5: a signature longer than 80 characters is replaced by '#' + sha256(signature), full width (65 chars). Ids print in decimal, no padding.",
  last_uncompacted: below,
  first_compacted: above,
  first_compacted_precompaction: precompaction,
};

const doc = {
  type: "TRVM-PREHASH-VECTORS-v1",
  version: 1,
  spec: "SEMSTATE-CANONICAL-v1.md §5 (canonical signature) over §3–§4 (live discovery order, canonical fold)",
  kernel_version: KERNEL_VERSION,
  law_refs: ["law:digest.canonical-bytes@1", "law:state.semantic-quotient@1", "law:digest.adequacy@2"],
  corpus: cert.corpus,
  binds: {
    refinement_receipt_id: refine.receipt_id,
    scheduler_certificate_id: cert.cert_id,
    note: "per_term[].normal_form.nf_id must equal refinement_receipt.per_term[].nf_id for the same name; every sem_signature must sha256 to its sem_state_id. Both are checkable without running the engine.",
  },
  per_term,
  compaction,
  informational: { generator: `extract_prehash.mjs via trvm_law_kernel.mjs v${KERNEL_VERSION}`, node: process.version },
};
doc.vectors_id = sha("TRVM-PREHASH-VECTORS-v1|" + js(doc.per_term) + "|" + js(doc.compaction) + "|" + js(doc.corpus));

if (mismatches.length) {
  console.error("EXTRACTION REFUSED — the oracle disagrees with shipped evidence:");
  for (const m of mismatches) console.error("  · " + m);
  process.exit(1);
}
writeFileSync("golden_prehash_vectors.json", JSON.stringify(doc, null, 1));
console.log(`golden_prehash_vectors.json — ${per_term.length} vectors, kernel v${KERNEL_VERSION}`);
console.log(`  every sem_signature hashes to its sem_state_id, every nf_id matches refinement_receipt`);
console.log(`  compaction boundary: ${below?.length} chars uncompacted → ${above?.length} chars compacted (nesting ${below?.nesting}→${above?.nesting})`);
console.log(`  vectors_id ${doc.vectors_id}`);
