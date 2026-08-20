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

   THE EXECUTION LEG IS NOW FILM-EVIDENCED, and how that happened is worth
   keeping. Round 25 could only claim OBSERVED: ic32_film v0.1.0 refused this
   fixture with `film-dup-cell-present`, and this file asserted the refusal
   rather than working around it. Measuring the KERNEL's film for the same term
   then showed the refusal was right about the fixture and wrong about the
   reason — the lowered term carries dup cells and, under the leftmost-tree-app
   strategy, NOT ONE DUP RULE EVER FIRES. Six APP-LAM frames, tree loci, and the
   residual dups dead by the end. The blocker was never their presence; it was
   firing them. So the precondition moved from PRESENCE to ENABLEDNESS and the
   emitter now emits multi-frame films over dup-carrying terms, refusing by name
   (`film-dup-rule-enabled`) where a dup rule actually becomes enabled.

   WHAT IS STILL NOT COVERED: the six DUP-* rules themselves, the `d:` and `v:`
   loci, and BUDGET_EXHAUSTED terminals. A term needing any of them is refused,
   not approximated.

   Run: node lowering_check.mjs   (exit 0 iff every case holds) */
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import { createHash } from "node:crypto";
import {
  ProgramRegistry, deriveLocally, DerivationAuthority, canonicalBytes, evaluate,
} from "./derive_protocol.mjs";
import { ObservedExecutionHost } from "./observed_execution_host.mjs";
import { parse, extrude, FloatRt, DescFloatRt, semStateId, semStateSignature, replaySemFilm }
  from "./trvm_law_kernel.mjs";
import {
  lower, loweringReceipt, decode, outcomeSemId, sourceOutcome, programSemId,
  LOWERING_SEM_ID, DECODE_SEM_ID, LOWERING_SPEC, INPUTS_MODEL,
  INSTANTIATION_SEM_ID, INSTANTIATION_FALSIFIERS, LOWERING_SEMANTICS,
  INSTANTIATION_SEMANTICS, LOWERING_STATUS, INSTANTIATION_STATUS,
  OVERBOUND_TRANSITIONAL_SEM_IDS,
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
    console.log(`LOWERING-CHECK: SKIP — ${n} not built (make gov-lower builds both).`);
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
    [{ op: "input", name: "x" }, "lower-input-not-implemented"],
    [{ op: "read", resource: "fb" }, "lower-reads-undecided"],
    [{ op: "sub", a: { op: "const", value: 1 }, b: { op: "const", value: 1 } }, "lower-unsupported-op"],
    [{ op: "const", value: 1.5 }, "lower-non-integer-constant"],
    [{ op: "const", value: -1 }, "lower-negative"],
  ];
  const got = cases.map(([ast, want]) => {
    const r = lower(ast);
    return !r.ok && String(r.reason).startsWith(want);
  });
  R("out-of-fragment-refused",
    got.every(Boolean) && INPUTS_MODEL.decided === true && INPUTS_MODEL.implemented === false
      && INSTANTIATION_FALSIFIERS.length === 3
      && INSTANTIATION_FALSIFIERS.every((f) => f.status === "DECLARED")
      && INSTANTIATION_SEM_ID !== LOWERING_SEM_ID,
    `${cases.map(([, w]) => w).join(" · ")} — each a NAMED refusal. The inputs model is now DECIDED ` +
    `(${INPUTS_MODEL.decided}) and NOT IMPLEMENTED (${INPUTS_MODEL.implemented}), and \`input\` is ` +
    `refused as lower-input-not-implemented rather than lower-inputs-undecided, because "not ruled" ` +
    `and "ruled, not written" are different states. The ruling is TWO LEVELS: lowering makes a ` +
    `parameterized TEMPLATE and instantiation closes it, so instantiation carries its own relation id ` +
    `(${INSTANTIATION_SEM_ID.slice(0, 16)}…, distinct from lowering's ${LOWERING_SEM_ID.slice(0, 16)}…) ` +
    `— a template can be perfectly lowered while "x" is bound to the port for "y". The three port ` +
    `falsifiers are DECLARED and none is written; B2 writes them`);
}

/* ── 7b. THE SEMANTIC IDS DO NOT MOVE WHEN THE PROJECT DOES ──────────────
      B1 hashed the whole spec, lifecycle included, so `implemented: false ->
      true` re-identified a relation whose meaning had not changed — B2 becoming
      BUILT would have moved an id B1 froze. That is round 16 inside the
      compiler specification. Measured in both directions here, because an id
      that stopped tracking semantics would be the same defect facing the other
      way, and this tree has shipped that version too. */
{
  const semId = (tag, o) => "x-" + createHash("sha256")
    .update(tag + "|" + canonicalBytes(o)).digest("hex");
  const L = (over = {}) => semId("TRVM-LOWERING-SEM-v2", { ...LOWERING_SEMANTICS, ...over });
  const I = (over = {}) => semId("TRVM-INSTANTIATION-SEM-v2", { ...INSTANTIATION_SEMANTICS, ...over });
  const baseL = L(), baseI = I();

  // lifecycle facts are NOT in either projection at all
  const statusFields = Object.keys(LOWERING_STATUS).concat(Object.keys(INSTANTIATION_STATUS));
  const leaked = statusFields.filter((k) => k in LOWERING_SEMANTICS || k in INSTANTIATION_SEMANTICS);

  // …and genuine semantic change still moves the RIGHT id and only that one
  const opsChanged = L({ lowered_ops: ["const"] });
  const extraChanged = I({ extra_input: "REFUSED." });
  const portChanged = I({ port_identity: { ...INSTANTIATION_SEMANTICS.port_identity,
    source_name_semantic: false } });

  R("semantic-ids-track-semantics-only",
    leaked.length === 0
      && LOWERING_SEM_ID.startsWith("lsem-") && INSTANTIATION_SEM_ID.startsWith("isem-")
      && opsChanged !== baseL && extraChanged !== baseI && portChanged !== baseI
      && LOWERING_SPEC.status.implemented === false
      && OVERBOUND_TRANSITIONAL_SEM_IDS.lowering_sem_id_v1 !== LOWERING_SEM_ID,
    `no lifecycle field (${statusFields.length} of them: implemented, decided_at, evidence grades, ` +
    `conformance status) appears in either semantic projection, so B2 becoming BUILT cannot re-` +
    `identify a relation B1 froze. And the projections are not inert: dropping \`add\` from ` +
    `lowered_ops moves the LOWERING id, while changing extra-input semantics or making the source ` +
    `name non-semantic moves the INSTANTIATION id and NOT lowering's — which is the two-relation ` +
    `ruling measured rather than asserted. The overbound B1 ids are kept in ` +
    `OVERBOUND_TRANSITIONAL_SEM_IDS rather than erased`);
}

/* ── 7c. extra inputs are IGNORED, because the SOURCE ignores them ───────── */
{
  const P2 = { op: "input", name: "x" };
  const G = { exact: {}, predicates: {} };
  const bound = (() => { try { return evaluate(P2, G, { x: 2 }).value; } catch (e) { return e.message; } })();
  const extra = (() => { try { return evaluate(P2, G, { x: 2, y: 999 }).value; } catch (e) { return e.message; } })();
  const missing = (() => { try { return evaluate(P2, G, {}).value; } catch (e) { return e.message; } })();
  R("extra-inputs-ignored-by-the-source",
    bound === 2 && extra === 2 && String(missing).startsWith("program-input-missing")
      && /^IGNORED\./.test(INSTANTIATION_SEMANTICS.extra_input)
      // the open item must NAME both codes it is open about, which is a
      // property of the record rather than of its wording
      && "declared_open" in LOWERING_SPEC.status.refinement_scope
      && LOWERING_SPEC.status.refinement_scope.declared_open.includes("program-input-missing")
      && LOWERING_SPEC.status.refinement_scope.declared_open.includes("instantiate-missing-input")
      && !INSTANTIATION_SEMANTICS.semantic_refusals.includes("instantiate-extra-input"),
    `the SOURCE evaluator returns ${JSON.stringify(extra)} for input("x") with {x:2, y:999} — the ` +
    `unused input is ignored — so instantiation IGNORES extras too. B1 froze this as a REFUSAL, ` +
    `which would have broken refinement by construction on the first program with a spare input, ` +
    `and justified it by claiming a many-to-one map would stop the receipt "being a function". That ` +
    `is simply false about functions. Missing inputs stay a refusal on both sides (${missing}) but ` +
    `under DIFFERENT codes at different layers, so refusal-preservation is DECLARED OPEN rather ` +
    `than assumed, and the refinement claim is scoped to fully bound environments`);
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

/* ── 9. THE EXECUTION LEG IS FILM-EVIDENCED ──────────────────────────────
   Round 25 could only say OBSERVED here: ic32_film v0.1.0 refused the fixture
   on film-dup-cell-present, and the check asserted that refusal rather than
   working around it. Measuring the JS film for this exact term then showed the
   blocker was mis-stated — the term CARRIES dup cells and, under the
   leftmost-tree-app strategy, not one dup rule ever fires. So the precondition
   moved from PRESENCE to ENABLEDNESS and the film is six APP-LAM frames. */
{
  const f = await host.run(C_FILM, "TRVM-FILM-EXEC-v1", { argv: [low.target_term] });
  const film = f.ok && f.output?.ok ? f.output.film : null;
  const rep = film ? replaySemFilm(low.target_term, film, FloatRt) : { ok: false };
  const repB = film ? replaySemFilm(low.target_term, film, DescFloatRt) : { ok: false };
  const obs = host.observationOf("TRVM-FILM-EXEC-v1", { argv: [low.target_term] }, f.output);
  R("execution-leg-is-film-evidenced",
    rep.ok === true && repB.ok === true && film.terminal.steps === 6
      && film.frames.every((fr) => fr.rule === "APP-LAM")
      && obs?.implementation_family_id === C_FILM,
    `the native runtime emits ${film?.terminal?.steps} chained frames for the LOWERED term and the ` +
    `kernel's own replaySemFilm accepts the whole chain on two runtime classes. So this leg is no ` +
    `longer OBSERVED-only: an execution the host drove AND a transition sequence an independent ` +
    `checker replayed are both present, and they were different claims all along. Every frame is ` +
    `APP-LAM — the dups are carried, never fired — and a term where a DUP rule IS enabled is still ` +
    `refused by name, which is where the six dup rules remain unbuilt`);
}

console.log("═".repeat(96));
console.log(fail
  ? `LOWERING-CHECK: FAIL — ${ran} cases ran, at least one failed`
  : `LOWERING-CHECK: PASS — ${ran}/${ran}. REFINEMENT WITNESSED, AND FILM-EVIDENCED: ` +
    `add(const 2, const 3) with inputs={} lowers to one canonical ic32 term; the native runtime the ` +
    `host launched emits SIX chained semantic-film frames that the law kernel's own replaySemFilm ` +
    `accepts on two runtime classes, and reduces it to a canonical normal form; that form decodes ` +
    `structurally to {status:"value",value:5}; and its outcome identity EQUALS the source evaluator's. ` +
    `Six identities stay distinct. STILL NOT CLAIMED: the six DUP-* rules, the d:/v: loci and ` +
    `BUDGET_EXHAUSTED terminals — a term needing any of them is refused by name, not approximated. ` +
    // DERIVED, because the hand-written version of this sentence said "stays
    // UNDECIDED" for a whole round after B1 decided it — green headline, green
    // cases, and the headline describing the world before the round that
    // produced it. The same class as the four-rung print and the UNDECIDED
    // spike status, in the check that exists to report this exact distinction.
    `The inputs model is ${INPUTS_MODEL.decided ? "DECIDED" : "UNDECIDED"} and ` +
    `${INPUTS_MODEL.implemented ? "IMPLEMENTED" : "NOT IMPLEMENTED"}: \`input\` is refused as ` +
    `lower-input-not-implemented, and the refinement claim above holds over ` +
    `${LOWERING_SPEC.status.refinement_scope.holds_over}. DECLARED OPEN: ` +
    `${LOWERING_SPEC.status.refinement_scope.declared_open.split(".")[0]}.`);
process.exit(fail ? 1 : 0);
