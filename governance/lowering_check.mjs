/* ═══════════════════════════════════════════════════════════════════════════
   lowering_check.mjs — the first end-to-end refinement witness.

   Source semantics, compilation identity, native execution, target normal-form
   identity, semantic decode, and refinement equality — connected without
   collapsing any of them into the same id.

       add(const 2, const 3)      inputs = {}
              │
              │  lowering_sem_id            re-lowered independently and compared
              ▼
       one canonical target term  ──▶ target_term_sem_id  (kernel; C agrees)
              │
              │  NATIVE ic32, launched by ObservedExecutionHost from an
              │  immutable catalog entry: hash first, execute second
              ▼
       canonical target normal form ──▶ target_nf_sem_id
              │
              │  decode_sem_id
              ▼
       {status:"value", value:5} ──▶ target_outcome_sem_id
                                          ║
       source evaluator ──▶ {status:"value", value:5} ──▶ source_outcome_sem_id

                    REFINEMENT: the two outcome ids are equal

   WHAT IS NOT COVERED, AND IT IS THE ONE THING THIS ROUND CANNOT CLAIM. The
   native execution leg is EVIDENCED BY OBSERVATION but NOT BY A FILM.
   ic32_film handles the dup-free one-step fragment, and a lowered addition is
   neither: it carries dup cells by construction, because Church addition uses
   its function argument twice and ic32's net is linear. The emitter says so by
   name — `film-dup-cell-present` — and this file asserts that refusal rather
   than working around it, so the gap is measured at exactly the fixture the
   refinement runs on. Closing it means DUP-LAM, DUP-SUP=, DUP-SUP!, DUP-ERA,
   DUP-VAR and DUP-APP in the emitter, plus the `d:` and `v:` loci, plus
   multi-frame films. That is the next piece of work and it is now concretely
   scoped rather than named in the abstract.

   So the honest classification of this file is two verdicts, not one:
       LOWERING REFINEMENT   witnessed
       NATIVE FILM EVIDENCE  absent for this fixture, by a checked refusal

   Run: node lowering_check.mjs   (exit 0 iff every case holds) */
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import {
  ProgramRegistry, deriveLocally, DerivationAuthority, canonicalBytes,
} from "./derive_protocol.mjs";
import { ObservedExecutionHost } from "./observed_execution_host.mjs";
import { parse, extrude, FloatRt, semStateId, semStateSignature } from "./trvm_law_kernel.mjs";
import {
  lower, loweringReceipt, decode, outcomeSemId, sourceOutcome, programSemId,
  LOWERING_SEM_ID, DECODE_SEM_ID, LOWERING_SPEC, INPUTS_MODEL,
} from "./lowering.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const CANON = join(HERE, "bridge", "ic32_canon");
const FILM = join(HERE, "bridge", "ic32_film");
const C_CANON = "impl-c-ic32-canon-v0.1.0";
const C_FILM = "impl-c-ic32-film-v0.1.0";

let fail = false, ran = 0;
const R = (id, ok, note) => { ran++; if (!ok) fail = true;
  console.log(`${ok ? "PASS" : "FAIL"}  ${id.padEnd(30)} ${note}`); };

for (const [n, p] of [["ic32_canon", CANON], ["ic32_film", FILM]]) {
  if (!existsSync(p)) {
    console.log(`LOWERING-CHECK: SKIP — ${n} not built (make gov-film builds both).`);
    console.log("  Unbuilt is never green: this exits nonzero so a CI that lost its compiler");
    console.log("  cannot read as a passing refinement claim.");
    process.exit(1);
  }
}

/* ── the host. Two catalogued native families, and no caller supplies an
      action or a path: hash first, execute second, both from one entry. ────── */
const host = new ObservedExecutionHost({
  [C_CANON]: { kind: "native-exec", entrypoint: CANON, artifact_closure: [CANON] },
  [C_FILM]:  { kind: "native-exec", entrypoint: FILM,  artifact_closure: [FILM] },
});
const NF_DOMAIN = "TRVM-TARGET-NF-v1";
const runCanon = async (term, argv) => {
  const r = await host.run(C_CANON, NF_DOMAIN, { argv, stdin: term + "\n", raw_output: true });
  if (!r.ok) return { ok: false, reason: r.reason };
  const line = r.output.stdout.trimEnd().split("\n")[0] ?? "";
  const i = line.indexOf("\t");
  return i < 0 ? { ok: false, reason: "canon-output-malformed" }
    : { ok: true, id: line.slice(0, i), signature: line.slice(i + 1),
        observed: host.observationOf(NF_DOMAIN, { argv, stdin: term + "\n", raw_output: true }, r.output) };
};

/* ── the fixture ─────────────────────────────────────────────────────────── */
const PROGRAM = { op: "add", a: { op: "const", value: 2 }, b: { op: "const", value: 3 } };
const PROGRAM_SEM_ID = programSemId(PROGRAM);

/* ── 1. LOWERING, and its identity is the relation's rather than the run's ── */
const low = lower(PROGRAM);
const kernelSemId = (term) => { const frt = new FloatRt(); return semStateId(frt, extrude(frt, parse(frt, term))); };
const TARGET_TERM_SEM_ID = low.ok ? kernelSemId(low.target_term) : null;
const receipt = low.ok ? loweringReceipt(PROGRAM_SEM_ID, TARGET_TERM_SEM_ID) : null;
{
  R("lowering-is-deterministic",
    low.ok && lower(PROGRAM).target_term === low.target_term
      && receipt.lowering_sem_id === LOWERING_SEM_ID
      && receipt.program_sem_id === PROGRAM_SEM_ID
      && receipt.lowering_receipt_id.startsWith("lrec-"),
    `add(const 2, const 3) lowers to ${low.ok && low.target_term.length} characters of ic32, the same ` +
    `string twice. The RELATION is ${LOWERING_SEM_ID.slice(0, 16)}… and the APPLICATION is a receipt ` +
    `${receipt?.lowering_receipt_id.slice(0, 16)}… binding {program_sem_id, lowering_sem_id, ` +
    `target_term_sem_id} — one id must not answer both "which lowering is this" and "what did it do here"`);
}

/* ── 2. and the instrument is RE-LOWERING, not a film ────────────────────── */
{
  const again = lower(PROGRAM);
  const againId = again.ok ? kernelSemId(again.target_term) : null;
  const other = lower({ op: "add", a: { op: "const", value: 3 }, b: { op: "const", value: 2 } });
  R("re-lowering-verifies",
    againId === receipt.target_term_sem_id && again.target_term === low.target_term
      && other.ok && kernelSemId(other.target_term) !== receipt.target_term_sem_id,
    `lowering the program again independently reaches the same target_term_sem_id ` +
    `(${String(receipt.target_term_sem_id).slice(0, 12)}…), which is the whole verification — no film. ` +
    `A film is evidence for a TRANSITION SYSTEM and lowering is a relation; filming it would invent ` +
    `internal compiler steps and make implementation strategy semantic, which is the mistake the ` +
    `read-order ruling refused. add(3,2) lowers to a DIFFERENT target term, so the id is not vacuous`);
}

/* ── 3. NATIVE EXECUTION, observed, and the C side agrees on the pre-state ── */
const initial = await runCanon(low.target_term, []);
const nf = await runCanon(low.target_term, ["--nf"]);
{
  R("native-execution-observed",
    initial.ok && nf.ok && initial.id === receipt.target_term_sem_id
      && nf.observed?.implementation_family_id === C_CANON,
    `the host hashed the catalogued binary and then ran it: the C side's canonical id for the LOWERED ` +
    `term is ${initial.id?.slice(0, 12)}… and equals the kernel's target_term_sem_id, so the two planes ` +
    `agree on what was fed in before either says what came out. The normal form is observed against ` +
    `family ${nf.observed?.implementation_family_id}`);
}
const TARGET_NF_SEM_ID = nf.id;

/* ── 4. DECODE, structurally, from the canonical signature ───────────────── */
const dec = decode(nf.signature);
const TARGET_OUTCOME = dec.ok ? dec.outcome : null;
{
  R("decode-is-structural",
    dec.ok && dec.outcome.status === "value" && dec.outcome.value === 5
      && DECODE_SEM_ID.startsWith("dsem-") && DECODE_SEM_ID !== LOWERING_SEM_ID,
    `the normal form's canonical signature ${nf.signature} decodes to ` +
    `${JSON.stringify(dec.outcome)}. It reads the SIGNATURE rather than a readback string — the same ` +
    `bytes the 48/48 bridge agreed on — and the outcome is structural, never a rendered reason. ` +
    `decode_sem_id ${DECODE_SEM_ID.slice(0, 16)}… is its OWN identity: a decoder can be perfect while ` +
    `lowering emitted the wrong term, and the reverse, so they are proved apart`);
}

/* ── 5. THE REFINEMENT ───────────────────────────────────────────────────── */
const reg = new ProgramRegistry(); reg.bind(PROGRAM);
const world = { read: () => ({ value: null, version: 1 }), scope: (q) => "scope:" + q };
const auth = new DerivationAuthority(world, [PROGRAM]);
const a = auth.authorize({ intent_id: "refine-1", program_sem_id: PROGRAM_SEM_ID,
  canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } });
const srcRes = deriveLocally(reg, a.request);
const SOURCE_OUTCOME = sourceOutcome(srcRes);
const SOURCE_OUTCOME_SEM_ID = outcomeSemId(SOURCE_OUTCOME);
const TARGET_OUTCOME_SEM_ID = TARGET_OUTCOME ? outcomeSemId(TARGET_OUTCOME) : null;
{
  const accepted = auth.accept(a.request, srcRes.result);
  R("REFINEMENT source==target",
    SOURCE_OUTCOME_SEM_ID === TARGET_OUTCOME_SEM_ID && SOURCE_OUTCOME.value === 5
      && accepted.ok && accepted.validated === true,
    `source ${JSON.stringify(SOURCE_OUTCOME)} → ${SOURCE_OUTCOME_SEM_ID.slice(0, 20)}… and target ` +
    `${JSON.stringify(TARGET_OUTCOME)} → ${String(TARGET_OUTCOME_SEM_ID).slice(0, 20)}…. EQUAL. The ` +
    `source evaluator and the native interaction-net runtime agree on the outcome of the same program, ` +
    `reached through a canonical lowering and a structural decode, and the source side was itself ` +
    `accepted by an authority that owns every oracle it consulted`);
}

/* ── 6. six identities, and none of them is another one ──────────────────── */
{
  const ids = { PROGRAM_SEM_ID, LOWERING_SEM_ID, TARGET_TERM_SEM_ID: receipt.target_term_sem_id,
    TARGET_NF_SEM_ID, DECODE_SEM_ID, OUTCOME_SEM_ID: SOURCE_OUTCOME_SEM_ID };
  const vals = Object.values(ids);
  R("six-identities-stay-distinct",
    new Set(vals).size === 6 && vals.every((v) => typeof v === "string" && v.length > 0),
    Object.entries(ids).map(([k, v]) => `${k.replace("_SEM_ID", "")}=${v.slice(0, 10)}…`).join(" · ") +
    ` — six distinct values. Collapsing any pair turns a refinement statement into a RENAMING, which ` +
    `is the failure this chain exists to avoid`);
}

/* ── 7. the refusals are named, and the fragment's edges are checked ─────── */
{
  const cases = [
    [{ op: "input", name: "x" }, "lower-inputs-undecided"],
    [{ op: "read", resource: "fb" }, "lower-reads-undecided"],
    [{ op: "sub", a: { op: "const", value: 1 }, b: { op: "const", value: 1 } }, "lower-unsupported-op"],
    [{ op: "const", value: 1.5 }, "lower-non-integer-constant"],
    [{ op: "const", value: -1 }, "lower-negative"],
  ];
  const got = cases.map(([ast, want]) => {
    const r = lower(ast);
    return !r.ok && String(r.reason).startsWith(want);
  });
  R("out-of-fragment-refused", got.every(Boolean) && INPUTS_MODEL.decided === false,
    `${cases.map(([, w]) => w).join(" · ")} — each a NAMED refusal. \`input\` is refused because the ` +
    `inputs model is UNDECIDED (parameterized vs instantiated), and that decision belongs before the ` +
    `op rather than during it: target_term_sem_id is a function of the program alone under one model ` +
    `and of the program AND the inputs under the other, and an unstated variable inside an identity is ` +
    `the round-16 bug class`);
}

/* ── 8. the decoder's own boundary is a refusal too ──────────────────────── */
{
  const notChurch = decode("A(N0,N1)");
  const compacted = decode("#" + "a".repeat(64));
  const zero = decode("L0(L1(N1))");
  const one = decode("L0(L1(A(N0,N1)))");
  R("decoder-boundary-named",
    !notChurch.ok && notChurch.reason === "decode-not-a-church-numeral"
      && !compacted.ok && compacted.reason === "decode-signature-compacted"
      && zero.ok && zero.outcome.value === 0 && one.ok && one.outcome.value === 1,
    `a non-numeral is ${notChurch.reason}; a §5-COMPACTED signature is ${compacted.reason} rather than ` +
    `guessed at, because compaction is irreversible and a mis-decode would be worse than a refusal — ` +
    `which bounds the decodable numerals, and the bound is stated. 0 and 1 decode, and they are the ` +
    `two shapes that carry no dup`);
}

/* ── 9. THE GAP, measured at the fixture the refinement runs on ──────────── */
{
  const f = await host.run(C_FILM, "TRVM-FILM-EXEC-v1", { argv: [low.target_term] });
  const reason = f.ok ? (f.output?.ok ? "EMITTED" : f.output.reason) : f.reason;
  R("native-film-absent-by-refusal", reason === "film-dup-cell-present",
    `the film emitter REFUSES this fixture: ${reason}. Church addition uses its function argument ` +
    `twice and ic32's net is linear, so a lowered addition carries dup cells by construction — and ` +
    `ic32_film v0.1.0 handles the dup-free one-step fragment. So the native execution leg of this ` +
    `chain is evidenced by OBSERVATION and not by a FILM, and this case asserts the refusal rather ` +
    `than working around it. Closing it is DUP-LAM / DUP-SUP= / DUP-SUP! / DUP-ERA / DUP-VAR / ` +
    `DUP-APP plus the d: and v: loci plus multi-frame films — concretely scoped now, not "later"`);
}

console.log("═".repeat(96));
console.log(fail
  ? `LOWERING-CHECK: FAIL — ${ran} cases ran, at least one failed`
  : `LOWERING-CHECK: PASS — ${ran}/${ran}. REFINEMENT WITNESSED: add(const 2, const 3) with inputs={} ` +
    `lowers to one canonical ic32 term, the native runtime the host launched reduces it to a canonical ` +
    `normal form, that form decodes structurally to {status:"value",value:5}, and its outcome identity ` +
    `EQUALS the source evaluator's. Six identities stay distinct. NOT CLAIMED, by a checked refusal: ` +
    `the native execution leg has no FILM for this fixture — a lowered addition carries dup cells and ` +
    `ic32_film v0.1.0 is the dup-free one-step fragment. The inputs model stays UNDECIDED and \`input\` ` +
    `is refused until it is ruled.`);
process.exit(fail ? 1 : 0);
