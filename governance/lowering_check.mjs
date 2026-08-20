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
  OVERBOUND_TRANSITIONAL_SEM_IDS, T, emit, templatePorts, targetTemplateSemId,
  TARGET_TEMPLATE_ENCODING_SEM_ID, TARGET_EXECUTABLE_ENCODING_SEM_ID,
  TARGET_ENCODING, TARGET_TEMPLATE_ENCODING, REFINEMENT_CHAIN,
  SUPERSEDED_CODOMAIN_SEM_IDS, IMPLEMENTED_LOWERED_OPS,
  instantiate, instantiationReceipt, inputsSemId, portSemId,
  INSTANTIATION_RECEIPT_FIELDS, SUPERSEDED_PROSE_RULE_SEM_IDS, INPUT_PORT_SPEC,
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
// THE TERM COMES FROM instantiate(), NOT FROM lower(). B2 removed lower()'s
// target_term convenience, so this witness now traverses the instantiation
// relation to reach native code — which is what makes instantiation_sem_id and
// inputs_sem_id EXERCISED rather than merely declared.
const INST0 = instantiate(low.template, {});
const TARGET_TERM = INST0.ok ? INST0.target_term : null;
// AND THE ID IS MINTED BY THE KERNEL, never by instantiate(). GPT's B2
// constraint: an instantiator that certified the semantic id of its own output
// would emit the artifact and the certificate from one source, so a wrong
// emission would carry a matching id and verify.
const TARGET_TERM_SEM_ID = TARGET_TERM ? kernelSemId(TARGET_TERM) : null;
// THE RECEIPT ENDS AT THE TEMPLATE. Lowering's codomain is the template after
// B1/B1.2; a receipt ending in target_term_sem_id would keep asserting that
// lowering produced the executable term, which the two-level ruling denies.
const receipt = low.ok ? loweringReceipt(PROGRAM_SEM_ID, low.target_template_sem_id) : null;
{
  R("lowering-is-deterministic",
    low.ok && low.target_term === undefined
      && lower(PROGRAM).target_template_sem_id === low.target_template_sem_id
      && receipt.lowering_sem_id === LOWERING_SEM_ID
      && receipt.program_sem_id === PROGRAM_SEM_ID
      && receipt.lowering_receipt_id.startsWith("lrec-")
      && receipt.target_template_sem_id === low.target_template_sem_id
      && receipt.target_term_sem_id === undefined,
    `add(const 2, const 3) lowers to a TEMPLATE, twice, and to no executable term at all — ` +
    `lower().target_term is ${low.target_term === undefined ? "gone" : "STILL HERE"}, so there is no ` +
    `second path to a term beside instantiate(). The RELATION is ${LOWERING_SEM_ID.slice(0, 16)}… and the APPLICATION is a receipt ` +
    `${receipt?.lowering_receipt_id.slice(0, 16)}… binding ` +
    // DERIVED FROM THE RECEIPT. This sentence hand-typed `target_term_sem_id`
    // and went on printing it for a round after B1.2 moved the receipt's domain
    // onto the template — the code was right and its own report was describing
    // the previous architecture. Reading the field list off the object is the
    // only version of this line that cannot say something the receipt does not.
    `{${Object.keys(receipt ?? {}).filter((k) => k !== "lowering_receipt_id").join(", ")}} — one id ` +
    `must not answer both "which lowering is this" and "what did it do here"`);
}

/* ── 2. and the instrument is RE-LOWERING, not a film ────────────────────── */
{
  const again = lower(PROGRAM);
  const againInst = again.ok ? instantiate(again.template, {}) : { ok: false };
  const againId = againInst.ok ? kernelSemId(againInst.target_term) : null;
  const other = lower({ op: "add", a: { op: "const", value: 3 }, b: { op: "const", value: 2 } });
  const otherInst = other.ok ? instantiate(other.template, {}) : { ok: false };
  R("re-lowering-verifies",
    againId === TARGET_TERM_SEM_ID && againInst.target_term === TARGET_TERM
      && again.target_template_sem_id === low.target_template_sem_id
      && otherInst.ok && kernelSemId(otherInst.target_term) !== TARGET_TERM_SEM_ID
      && other.target_template_sem_id !== low.target_template_sem_id,
    `lowering the program again independently reaches the same target_term_sem_id ` +
    `(${String(TARGET_TERM_SEM_ID).slice(0, 12)}…) and the same target_template_sem_id ` +
    `(${String(low.target_template_sem_id).slice(0, 12)}…), which is the whole verification — no film. ` +
    `A film is evidence for a TRANSITION SYSTEM and lowering is a relation; filming it would invent ` +
    `internal compiler steps and make implementation strategy semantic, which is the mistake the ` +
    `read-order ruling refused. add(3,2) lowers to a DIFFERENT target term, so the id is not vacuous`);
}

/* ── 3. NATIVE EXECUTION, observed, and the C side agrees on the pre-state ── */
const initial = await runCanon(TARGET_TERM, []);
const nf = await runCanon(TARGET_TERM, ["--nf"]);
{
  R("native-execution-observed",
    initial.ok && nf.ok && initial.id === TARGET_TERM_SEM_ID
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

/* ── 6. every identity the chain declares, and none of them is another one ──
      THE COUNT IS NOT WRITTEN DOWN. This case asserted that SIX identities stay
      distinct; B1.2 added target_template_sem_id to the chain and not to the
      set, so it went on proving a six-way claim about a seven-node chain — green
      the whole time, and one node short of what its own name promised. The set
      is now DERIVED from REFINEMENT_CHAIN, so a node added to the chain and not
      to the witness fails here instead of being quietly excluded, and the
      unexercised nodes are NAMED rather than absent. */
{
  const value = {
    program_sem_id: PROGRAM_SEM_ID,
    lowering_sem_id: LOWERING_SEM_ID,
    target_template_sem_id: low.ok ? low.target_template_sem_id : null,
    instantiation_sem_id: INSTANTIATION_SEM_ID,
    inputs_sem_id: INST0.ok ? INST0.inputs_sem_id : null,
    target_term_sem_id: TARGET_TERM_SEM_ID,
    target_nf_sem_id: TARGET_NF_SEM_ID,
    decode_sem_id: DECODE_SEM_ID,
    outcome_sem_id: SOURCE_OUTCOME_SEM_ID,
  };
  const declared = REFINEMENT_CHAIN.map((n) => n.id);
  const exercised = REFINEMENT_CHAIN.filter((n) => n.exercised);
  const open = REFINEMENT_CHAIN.filter((n) => !n.exercised);
  const vals = exercised.map((n) => value[n.id]);
  // the set must COVER the chain: a node declared and not wired up here is the
  // defect this rewrite exists to make impossible, so it is a failure and not a
  // silent skip
  const covered = declared.every((id) => id in value)
    && Object.keys(value).every((k) => declared.includes(k));
  R("chain-identities-stay-distinct",
    covered && vals.every((v) => typeof v === "string" && v.length > 0)
      && new Set(vals).size === vals.length
      && open.every((n) => value[n.id] === null && typeof n.why_not === "string")
      && exercised.length === REFINEMENT_CHAIN.length,
    exercised.map((n) => `${n.id.replace("_sem_id", "")}=${String(value[n.id]).slice(0, 10)}…`)
      .join(" · ") +
    ` — ${vals.length} distinct values over a ${declared.length}-node chain, and the count is DERIVED ` +
    `from REFINEMENT_CHAIN rather than asserted. Collapsing any pair turns a refinement statement into ` +
    `a RENAMING, which is the failure this chain exists to avoid. ` +
    (open.length
      ? `DECLARED AND NOT EXERCISED: ${open.map((n) => n.id).join(", ")} — scope, not coverage`
      : `EVERY NODE IS NOW EXERCISED: B2 removed lower()'s convenience emission, so the witness ` +
        `reaches native code THROUGH instantiate(), and instantiation_sem_id and inputs_sem_id ` +
        `stopped being declared architecture`));
}

/* ── 7. the refusals are named, and the fragment's edges are checked ─────── */
{
  const cases = [
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
    got.every(Boolean) && INPUTS_MODEL.decided === true && INPUTS_MODEL.implemented === true
      && lower({ op: "input", name: "x" }).ok === true
      && INSTANTIATION_FALSIFIERS.length === 3
      && INSTANTIATION_FALSIFIERS.every((f) => f.status === "WITNESSED")
      && INSTANTIATION_SEM_ID !== LOWERING_SEM_ID,
    `${cases.map(([, w]) => w).join(" · ")} — each a NAMED refusal. The inputs model is DECIDED ` +
    `(${INPUTS_MODEL.decided}) and IMPLEMENTED (${INPUTS_MODEL.implemented}): \`input\` LOWERS now, to ` +
    `a structural port, and the refusal that carried it through three passes of "ruled, not written" ` +
    `is gone rather than repointed. The ruling is TWO LEVELS: lowering makes a ` +
    `parameterized TEMPLATE and instantiation closes it, so instantiation carries its own relation id ` +
    `(${INSTANTIATION_SEM_ID.slice(0, 16)}…, distinct from lowering's ${LOWERING_SEM_ID.slice(0, 16)}…) ` +
    `— a template can be perfectly lowered while "x" is bound to the port for "y". All three port ` +
    `falsifiers are WITNESSED below, I-4c end to end through native execution`);
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
      && LOWERING_SPEC.status.implemented === true
      && OVERBOUND_TRANSITIONAL_SEM_IDS.lowering_sem_id_v1 !== LOWERING_SEM_ID,
    `no lifecycle field (${statusFields.length} of them: implemented, decided_at, evidence grades, ` +
    `conformance status) appears in either semantic projection, so B2 becoming BUILT cannot re-` +
    `identify a relation B1 froze. And the projections are not inert: dropping \`add\` from ` +
    `lowered_ops moves the LOWERING id, while changing extra-input semantics or making the source ` +
    `name non-semantic moves the INSTANTIATION id and NOT lowering's — which is the two-relation ` +
    `ruling measured rather than asserted. The overbound B1 ids are kept in ` +
    `OVERBOUND_TRANSITIONAL_SEM_IDS rather than erased`);
}

/* ── 7d. THE TARGET TEMPLATE EXISTS, and allocation cannot reach it ──────
      B1 ruled that a port lives "at the canonical target-AST layer, before any
      variable allocation" and there was no such layer — lower() built an ic32
      string, so a port would have had to be a placeholder like `$input_x` and
      spelling would be semantics again. The template is that layer, and the
      reason I-4a holds is STRUCTURAL: a template has nowhere to put a binder
      name or a dup label, because emit() invents both from its shape. */
{
  const t = low.template;
  const emitted = emit(t);
  const ports = templatePorts(t);
  // a template that still has a port is not a term, and emit says so by name
  const withPort = T.add(T.port("x"), T.church(3));
  const refused = (() => { try { emit(withPort); return "EMITTED"; }
    catch (e) { return e.message; } })();
  // two structurally equal templates have one identity; a different one differs
  const rebuilt = T.add(T.church(2), T.church(3));
  const different = T.add(T.church(3), T.church(2));
  const noNames = !JSON.stringify(t).includes("λ") && !/"[a-z]+\d"/.test(JSON.stringify(t));
  R("target-template-is-the-pre-allocation-layer",
    ports.length === 0 && emitted === TARGET_TERM
      && targetTemplateSemId(rebuilt) === low.target_template_sem_id
      && targetTemplateSemId(different) !== low.target_template_sem_id
      && targetTemplateSemId(withPort) !== low.target_template_sem_id
      && /^emit-unbound-port: x/.test(refused) && noNames
      && low.target_template_sem_id.startsWith("tmpl-")
      && TARGET_TEMPLATE_ENCODING_SEM_ID.startsWith("tenc-"),
    `lowering's codomain is ${JSON.stringify(t)} — no binder names, no dup labels, ports structural. ` +
    `emit() allocates both from the template's shape and reproduces the SAME ${emitted.length} ` +
    `characters of ic32 the pre-template lowering produced, so introducing the layer changed neither ` +
    `the executable term nor its outcome. A template still holding a port is ${refused.split(":")[0]} ` +
    `rather than emitted, because a template with a free port is not a term. Structural equality is ` +
    `identity (${low.target_template_sem_id.slice(0, 14)}…) and add(3,2) differs — and the template's ` +
    `id lives in its own domain from the term's even here, where there are zero ports`);
}

/* ── 7e. emit() IS NOT A HIDDEN RELATION — B1.2.1, GPT's find ────────────
      B1.2 named lowering's DOMAIN encoding by id and instantiation's CODOMAIN
      in prose ("… via emit()"), so the rule deciding how church(n) and add(a,b)
      become interaction-net terms reached the identity of the relation that
      produces those terms only as a symbol name inside an English sentence.
      Measured against B1.2: change the add combinator and the executable term's
      bytes change, while isem-bf9434fc…, the template id and the template-
      encoding id all stand still. LOWERING_SEM_ID moved — the wrong id, and for
      the wrong reason: a pre-template leftover binding lowering to an encoding
      two layers downstream, so an emitter change re-identified every
      LoweringReceipt ever issued.

      Both halves are the same mistake facing opposite ways, and the fix is one
      boundary drawn twice. THREE MUTATIONS, THREE ANSWERS — asserted here
      because the two-relation ruling is worth nothing if the ids do not sort
      changes between the relations. */
{
  const semId = (tag, o) => tag + "|" + createHash("sha256")
    .update(tag + "|" + canonicalBytes(o)).digest("hex");
  const XE = (o) => semId("TRVM-TARGET-EXECUTABLE-ENC-v1", o);
  const TE = (o) => semId("TRVM-TARGET-TEMPLATE-ENC-v1", o);
  const L = (over = {}) => semId("TRVM-LOWERING-SEM-v2", { ...LOWERING_SEMANTICS, ...over });
  const I = (over = {}) => semId("TRVM-INSTANTIATION-SEM-v2", { ...INSTANTIATION_SEMANTICS, ...over });
  const baseL = L(), baseI = I();

  // 1. THE EMITTER: three different rules, each changing the emitted term
  const emitterMoves = [
    { ...TARGET_ENCODING, add: "λm.λn.λf.λx.!&L{f0,f1}=f;((n f1) ((m f0) x))" },
    { ...TARGET_ENCODING, dup_label_policy: "labels count DOWN from 1000, breadth-first." },
    { ...TARGET_ENCODING, numbers: "binary naturals rather than Church numerals." },
  ].map((mut) => ({ l: L(), i: I({ codomain_encoding_sem_id: XE(mut) }) }));

  // 2. A LOWERING RULE: the source -> template map, which is lowering's alone
  const ruleMoves = [
    { ...LOWERING_SEMANTICS.op_lowering_rules, const: "{op:\"const\", value:n} lowers to church(n+1)." },
    { ...LOWERING_SEMANTICS.op_lowering_rules, add: "{op:\"add\", a, b} lowers to add(b', a') — SWAPPED." },
  ].map((mut) => ({ l: L({ op_lowering_rules: mut }), i: I() }));

  // 3. THE TEMPLATE GRAMMAR: the shared boundary, so BOTH must move
  const gMut = { ...TARGET_TEMPLATE_ENCODING,
    grammar: "Template := church(n) | add(Template, Template) | port(source_name) | lam(Template)" };
  const shared = { l: L({ target_template_encoding_sem_id: TE(gMut) }),
    i: I({ domain_encoding_sem_id: TE(gMut) }), t: TE(gMut) };

  // and lowering may not claim a refusal it cannot produce
  const drive = {
    "lower-unsupported-op": { op: "sub", a: { op: "const", value: 1 }, b: { op: "const", value: 1 } },
    "lower-non-integer-constant": { op: "const", value: 1.5 },
    "lower-negative": { op: "const", value: -1 },
    "lower-reads-undecided": { op: "read", resource: "fb" },
  };
  const reachable = LOWERING_SEMANTICS.refusal_semantics.every((name) => {
    const r = drive[name] ? lower(drive[name]) : { ok: true };
    return !r.ok && String(r.reason).startsWith(name);
  });

  R("emit-is-not-a-hidden-relation",
    emitterMoves.every((m) => m.i !== baseI && m.l === baseL)
      && ruleMoves.every((m) => m.l !== baseL && m.i === baseI)
      && shared.l !== baseL && shared.i !== baseI && shared.t !== TARGET_TEMPLATE_ENCODING_SEM_ID
      && INSTANTIATION_SEMANTICS.codomain_encoding_sem_id === TARGET_EXECUTABLE_ENCODING_SEM_ID
      && TARGET_EXECUTABLE_ENCODING_SEM_ID.startsWith("xenc-")
      && !("target_encoding" in LOWERING_SEMANTICS)
      && reachable
      && !LOWERING_SEMANTICS.refusal_semantics.includes("emit-unbound-port")
      && INSTANTIATION_SEMANTICS.semantic_refusals.includes("emit-unbound-port")
      && SUPERSEDED_CODOMAIN_SEM_IDS.lowering_sem_id_b12 !== LOWERING_SEM_ID
      && SUPERSEDED_CODOMAIN_SEM_IDS.instantiation_sem_id_b12 !== INSTANTIATION_SEM_ID,
    `changing the add combinator, the dup label policy or the Church expansion moves the ` +
    `INSTANTIATION id and NOT lowering's — the executable encoding is content-bound at ` +
    `${TARGET_EXECUTABLE_ENCODING_SEM_ID.slice(0, 16)}… instead of named as "via emit()" in prose. ` +
    `Changing a per-op lowering rule moves LOWERING's id and NOT instantiation's, and those rules had ` +
    `to be WRITTEN DOWN: removing the leftover target_encoding binding exposed that nothing in the ` +
    `hashed semantics said a const becomes a church node, so const(n) -> church(n+1) would have ` +
    `contradicted no sentence. Changing the TEMPLATE grammar moves BOTH, because it is the boundary ` +
    `they share. And lowering no longer claims emit-unbound-port or template-malformed: all ` +
    `${LOWERING_SEMANTICS.refusal_semantics.length} names it does claim are driven to a refusal above`);
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

/* ── B2-1. THE MIGRATION THEOREM ─────────────────────────────────────────
      lower() no longer returns an executable term. GPT's ruling, and the reason
      is the one this tree keeps re-learning: keeping the convenience field
      would have left an official path (lower -> instantiate -> term) beside a
      shortcut (lower -> term), with every future reader having to remember
      which carried the semantics. That is how a hidden second mechanism comes
      back. The equality survives as a THEOREM rather than an API. */
{
  const viaInstantiation = INST0.ok ? INST0.target_term : null;
  const viaEmitDirect = emit(low.template);           // what the shortcut used to do
  R("migration-preserves-the-old-bytes",
    INST0.ok && viaInstantiation === viaEmitDirect && viaInstantiation.length === 129
      && low.target_term === undefined
      && INST0.consumed_inputs.length === 0
      && INST0.inputs_sem_id === inputsSemId({})
      && TARGET_TERM_SEM_ID === kernelSemId(viaEmitDirect),
    `instantiate(template, {}) reproduces the EXACT ${viaInstantiation?.length} characters the removed ` +
    `lower().target_term used to return, and the six-frame film, normal form and value 5 below are ` +
    `reached through it. So the zero-input path did not change meaning when it changed owner — which ` +
    `is what makes removing the shortcut safe rather than merely tidy. consumed_inputs is [] because ` +
    `the template declares no ports, and inputs_sem_id ${INST0.inputs_sem_id?.slice(0, 14)}… is the ` +
    `identity of the EMPTY environment rather than an absent field`);
}

/* ── B2-2. THE RECEIPT IS NOT SELF-CERTIFIED ─────────────────────────────
      GPT's B2 constraint, and it is load-bearing: an instantiate() that emitted
      bytes AND certified their semantic id would produce the artifact and its
      certificate from one source, so a wrong emission would carry a matching id
      and verify against itself. The same discipline LoweringReceipt already
      followed — the runtime owns the identity of what it executes. */
{
  const returned = Object.keys(INST0).sort();
  const mintsItsOwnId = returned.includes("target_term_sem_id");
  const rec = instantiationReceipt(low.target_template_sem_id, INST0.inputs_sem_id, TARGET_TERM_SEM_ID);
  // VERIFICATION: re-instantiate independently, re-canonicalise independently,
  // and compare — never ask the instantiator whether it agrees with itself.
  const again = instantiate(lower(PROGRAM).template, {});
  const verified = again.ok && kernelSemId(again.target_term) === rec.target_term_sem_id
    && again.inputs_sem_id === rec.inputs_sem_id;
  // and a receipt built over a DIFFERENT term must not verify against this one
  const otherTerm = instantiate(lower({ op: "add", a: { op: "const", value: 3 },
    b: { op: "const", value: 2 } }).template, {});
  const forged = kernelSemId(otherTerm.target_term) === rec.target_term_sem_id;
  const incomplete = (() => { try { instantiationReceipt(low.target_template_sem_id,
    INST0.inputs_sem_id, undefined); return "BUILT"; } catch (e) { return e.message; } })();
  R("receipt-is-not-self-certified",
    !mintsItsOwnId && verified && !forged
      && rec.instantiation_sem_id === INSTANTIATION_SEM_ID
      && rec.instantiation_receipt_id.startsWith("irec-")
      && INSTANTIATION_RECEIPT_FIELDS.every((f) => rec[f] !== undefined)
      && /^instantiation-receipt-incomplete: target_term_sem_id/.test(incomplete),
    `instantiate() returns {${returned.join(", ")}} and NOT target_term_sem_id — it hands over bytes ` +
    `and the kernel canonicalises them, so the certificate and the artifact do not come from one ` +
    `source. The receipt ${rec.instantiation_receipt_id.slice(0, 16)}… is built AFTER that id exists, ` +
    `and verification RE-INSTANTIATES and RE-CANONICALISES independently rather than asking the ` +
    `instantiator to agree with itself. add(3,2)'s term does not verify against it, and a receipt ` +
    `missing a field is ${incomplete.split(":")[0]} rather than a receipt with a hole in it`);
}

/* ── B2-3. I-4a — ALLOCATION INVARIANCE, against a SECOND EMITTER ────────
      The claim is "same source input name, different internal target variable
      allocation (_impl17 vs q93) -> the SAME target_template_sem_id". Asserting
      it about one emitter proves nothing, so here is a second one: different
      binder names, different label origin, genuinely different ic32 text. The
      template it reads is byte-identical because a template HAS no field an
      allocation could occupy. */
{
  const altEmit = (tmpl) => {
    let L = 100;
    const church2 = (n) => {
      if (n === 0) return "λ_impl17.λq93.q93";
      if (n === 1) return "λ_impl17.λq93.(_impl17 q93)";
      const binds = []; let cur = "_impl17";
      for (let i = 0; i < n - 1; i++) {
        const l = L++;
        if (i < n - 2) { binds.push(`!&${l}{z${i},w${i}}=${cur};`); cur = `w${i}`; }
        else binds.push(`!&${l}{z${i},z${i + 1}}=${cur};`);
      }
      let body = "q93";
      for (let i = n - 1; i >= 0; i--) body = `(z${i} ${body})`;
      return `λ_impl17.λq93.${binds.join("")}${body}`;
    };
    const go = (n) => {
      if (n.t === "church") return church2(n.n);
      if (n.t === "add") { const a = go(n.a), b = go(n.b);
        return `((λ_m.λ_n.λ_impl17.λq93.!&${L++}{g0,g1}=_impl17;((_m g0) ((_n g1) q93)) ${a}) ${b})`; }
      throw new Error("emit-unbound-port");
    };
    return go(tmpl);
  };
  const lx = lower({ op: "add", a: { op: "input", name: "x" }, b: { op: "const", value: 3 } });
  const boundTmpl = T.add(T.church(2), T.church(3));
  const a1 = emit(boundTmpl), a2 = altEmit(boundTmpl);
  const nf1 = await runCanon(a1, ["--nf"]), nf2 = await runCanon(a2, ["--nf"]);
  R("I-4a-allocation-is-not-semantic",
    a1 !== a2 && /_impl17|q93/.test(a2) && !/_impl17|q93/.test(a1)
      && targetTemplateSemId(boundTmpl) === targetTemplateSemId(T.add(T.church(2), T.church(3)))
      && !JSON.stringify(lx.template).includes("_impl17")
      && !JSON.stringify(lx.template).includes("λ")
      && lx.ok && lx.ports.join() === "x"
      && nf1.ok && nf2.ok && nf1.signature === nf2.signature,
    `two emitters over ONE template: ${a1.length} characters against ${a2.length}, the second full of ` +
    `_impl17 and q93 with labels from 100 — genuinely different allocation. The template's id is the ` +
    `same because there is NO FIELD an allocation could occupy, which is why I-4a is a property of the ` +
    `data structure rather than a convention an emitter is asked to respect. And the allocation turns ` +
    `out to be non-semantic all the way DOWN: both terms reach the identical canonical normal-form ` +
    `signature ${nf1.signature}, so the native runtime does not see the difference either`);
}

/* ── B2-4. I-4b — THE SOURCE NAME IS SEMANTIC ────────────────────────────
      The inverse of round 16, and the half that is easy to lose: having
      quotiented away the allocation, the quotient must NOT have taken the
      source key with it. */
{
  const lx = lower({ op: "input", name: "x" });
  const ly = lower({ op: "input", name: "y" });
  // NO Unicode normalization: two code-point sequences the core distinguishes
  // must stay distinguished at the port
  const composed = lower({ op: "input", name: "é" });        // é, one code point
  const decomposed = lower({ op: "input", name: "é" });     // e + combining acute
  R("I-4b-the-source-name-is-semantic",
    lx.ok && ly.ok && lx.target_template_sem_id !== ly.target_template_sem_id
      && portSemId("x") !== portSemId("y")
      && composed.target_template_sem_id !== decomposed.target_template_sem_id
      && INPUT_PORT_SPEC.no_normalization.includes("NOT Unicode-normalized")
      && lower({ op: "input", name: "x" }).target_template_sem_id === lx.target_template_sem_id,
    `input("x") and input("y") reach DIFFERENT target_template_sem_ids ` +
    `(${lx.target_template_sem_id.slice(0, 14)}… vs ${ly.target_template_sem_id.slice(0, 14)}…), so the ` +
    `quotient that made allocation non-semantic did not take the source key with it. And composed é ` +
    `differs from decomposed e+combining-acute: normalizing would be a LANGUAGE-semantic change made ` +
    `at the encoding layer, where the source cannot see it`);
}

/* ── B2-5. I-4c — BINDING HAS FORCE, END TO END ──────────────────────────
      The mandated ASYMMETRIC fixture. add(x, y) with x=2,y=3 gives 5 under the
      correct binding and 5 under the swap, so the obvious witness is green
      whether or not the binding was honoured — a test whose output cannot
      reveal the defect it is named for. x + (x + y) gives 7 and 8.

      ALL THE WAY THROUGH, not merely to different bytes: native execution,
      canonical normal form, structural decode, and the source evaluator
      independently agreeing with the correct one. */
{
  const P = { op: "add", a: { op: "input", name: "x" },
    b: { op: "add", a: { op: "input", name: "x" }, b: { op: "input", name: "y" } } };
  const lp = lower(P);
  // GPT's item 9: the positive witness carries an UNUSED input, so "extras are
  // ignored" is exercised rather than merely written down.
  const RIGHT = { x: 2, y: 3, unused: 999 };
  const SWAPPED = { x: 3, y: 2, unused: 999 };
  const ok = instantiate(lp.template, RIGHT);
  const sw = instantiate(lp.template, SWAPPED);
  const nfOk = await runCanon(ok.target_term, ["--nf"]);
  const nfSw = await runCanon(sw.target_term, ["--nf"]);
  const decOk = decode(nfOk.signature), decSw = decode(nfSw.signature);

  const G = { exact: {}, predicates: {} };
  const srcOk = evaluate(P, G, RIGHT).value, srcSw = evaluate(P, G, SWAPPED).value;

  // THE RECEIPT MUST ACCEPT ONLY THE 7-PRODUCING TERM
  const recOk = instantiationReceipt(lp.target_template_sem_id, ok.inputs_sem_id,
    kernelSemId(ok.target_term));
  const swapVerifiesAgainstIt = kernelSemId(sw.target_term) === recOk.target_term_sem_id;

  // extras: a different inputs_sem_id reaching the SAME term
  const noExtra = instantiate(lp.template, { x: 2, y: 3 });
  const extrasIgnored = noExtra.ok && noExtra.target_term === ok.target_term
    && noExtra.inputs_sem_id !== ok.inputs_sem_id;

  R("I-4c-binding-has-force",
    ok.ok && sw.ok && ok.target_term !== sw.target_term
      && decOk.ok && decSw.ok && decOk.outcome.value === 7 && decSw.outcome.value === 8
      && srcOk === 7 && srcSw === 8
      && outcomeSemId(decOk.outcome) === outcomeSemId({ status: "value", value: srcOk })
      && !swapVerifiesAgainstIt && extrasIgnored
      && ok.consumed_inputs.join() === "x,y",
    `x + (x + y) with x=2,y=3 runs NATIVELY to ${decOk.outcome?.value} and the x/y swap to ` +
    `${decSw.outcome?.value} — different terms, different normal forms, different outcome identities, ` +
    `and the SOURCE evaluator independently gives ${srcOk} and ${srcSw}. The swapped term does NOT ` +
    `verify against the correct receipt ${recOk.instantiation_receipt_id.slice(0, 14)}…, which is the ` +
    `whole falsifier: instantiation HONOURS the port identity rather than carrying it decoratively. ` +
    `The symmetric fixture add(x,y) is REFUSED for this witness because 2+3 == 3+2 would be green ` +
    `either way. EXTRAS: {x,y,unused:999} and {x,y} have different inputs_sem_id and reach the SAME ` +
    `term, and consumed_inputs is [${ok.consumed_inputs}] — supplied and consumed stay distinct`);
}

/* ── B2-6. BUILDING IT MOVED NEITHER SEMANTIC ID ─────────────────────────
      The property B1.1 set out to make possible, and B2 is the first round able
      to exercise it: `implemented` went false -> true, `input` became
      executable, instantiate() was written, the falsifiers went DECLARED ->
      WITNESSED, and none of that may have moved a relation id. Both ids DID
      move this round, for two changes that are NOT the implementation, and the
      point of this case is that the two causes are separable. */
{
  const semId2 = (prefix, tag, o) => prefix + createHash("sha256")
    .update(tag + "|" + canonicalBytes(o)).digest("hex");

  // THE EXACT CHECK, not a simulation. Spreading STATUS onto SEMANTICS was the
  // first version of this case and it was meaningless: STATUS keys are not IN
  // the hashed object, so adding them produces a different object and a
  // different hash, measuring nothing about lifecycle. (Case 7b already proves
  // no status KEY leaks into either semantic record.)
  //
  // What B2 has to show is stronger and is stated as an equation: the ONLY
  // fields of the hashed records that B2 touched are op_lowering_rules and
  // emission. Put the B1.2.1 values of exactly those two back, and the B1.2.1
  // identities must return EXACTLY — which proves that implementing `input`,
  // writing instantiate(), removing lower()'s target_term and flipping every
  // lifecycle flag changed no hashed rule at all. This is the same device the
  // pack uses to prove a version bump additive by cert_id rather than by
  // assertion.
  const B121_OP_RULES = Object.freeze({
    const: "{op:\"const\", value:n} lowers to {t:\"church\", n} for a non-negative integer n, with n " +
      "carried through UNCHANGED. The expansion of that node into interaction-net text belongs to the " +
      "EXECUTABLE encoding and is deliberately not stated here — that is the boundary whose absence " +
      "made emit() a hidden relation.",
    add: "{op:\"add\", a, b} lowers to {t:\"add\", a', b'} where a' and b' are the lowerings of a and " +
      "b. Operand order is PRESERVED, a then b, the core's own evaluation order; the target `add` " +
      "node names the combinator, and which combinator that is belongs to the executable encoding.",
    input: "see inputs.input_lowering_rule — {op:\"input\", name:N} lowers to {t:\"port\", " +
      "source_name:N}. Stated there rather than duplicated here, because a rule written twice in one " +
      "hashed record is a rule that can disagree with itself.",
  });
  const B121_EMISSION =
    "substitution THEN emission, both inside this relation. Ports are replaced by canonically " +
    "encoded values and the closed template is serialized by codomain_encoding_sem_id. Emission is " +
    "DETERMINISTIC: equal closed templates emit equal terms, binder names and dup labels included. " +
    "It carries no identity of its own because it is neither independently reused nor independently " +
    "theorem-bearing; if it becomes either, it earns an emission_sem_id and this relation's codomain " +
    "becomes the closed TEMPLATE rather than the executable term.";

  const backL = semId2("lsem-", "TRVM-LOWERING-SEM-v2",
    { ...LOWERING_SEMANTICS, op_lowering_rules: B121_OP_RULES });
  const backI = semId2("isem-", "TRVM-INSTANTIATION-SEM-v2",
    { ...INSTANTIATION_SEMANTICS, emission: B121_EMISSION });

  R("implementing-moved-neither-id",
    backL === SUPERSEDED_PROSE_RULE_SEM_IDS.lowering_sem_id_b121
      && backI === SUPERSEDED_PROSE_RULE_SEM_IDS.instantiation_sem_id_b121
      && backL !== LOWERING_SEM_ID && backI !== INSTANTIATION_SEM_ID
      && LOWERING_STATUS.implemented === true && INSTANTIATION_STATUS.implemented === true
      && INPUTS_MODEL.implemented === true
      && INSTANTIATION_FALSIFIERS.every((f) => f.status === "WITNESSED")
      && IMPLEMENTED_LOWERED_OPS.join() === LOWERING_SEMANTICS.lowered_ops.join()
      && !("emission_split_trigger" in INSTANTIATION_SEMANTICS)
      && "emission_split_trigger" in INSTANTIATION_STATUS,
    `putting back ONLY op_lowering_rules and ONLY emission returns the B1.2.1 identities EXACTLY ` +
    `(${backL.slice(0, 16)}… and ${backI.slice(0, 16)}…), so those two fields are the ONLY hashed ` +
    `bytes B2 touched. Everything the round actually BUILT — \`input\` lowering, instantiate(), the ` +
    `removal of lower().target_term, three falsifiers going DECLARED -> WITNESSED and every lifecycle ` +
    `flag flipping — moved NO semantic id. That is the property B1.1 split the records to make ` +
    `possible and B2 is the first round able to exercise it. The two changes that DID move an id are ` +
    `record changes GPT ruled: the rules became STRUCTURAL, and the emission SPLIT TRIGGER left the ` +
    `relation for STATUS, where B1.2.1 should have put it — it was re-committing the very defect B1.1 ` +
    `found. Specified and implemented op lists now COINCIDE (${IMPLEMENTED_LOWERED_OPS.join(" · ")}), ` +
    `which is a fact about this moment and not a reason to merge the names`);
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
  const f = await host.run(C_FILM, "TRVM-FILM-EXEC-v1", { argv: [TARGET_TERM] });
  const film = f.ok && f.output?.ok ? f.output.film : null;
  const rep = film ? replaySemFilm(TARGET_TERM, film, FloatRt) : { ok: false };
  const repB = film ? replaySemFilm(TARGET_TERM, film, DescFloatRt) : { ok: false };
  const obs = host.observationOf("TRVM-FILM-EXEC-v1", { argv: [TARGET_TERM] }, f.output);
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
    // DERIVED. This sentence said "Six identities stay distinct" for the round
    // in which the chain grew a seventh node, in the headline of the check whose
    // job is to report exactly that. Same species as the four-rung print and the
    // UNDECIDED spike status — and the count below cannot disagree with the case
    // above it, because both read REFINEMENT_CHAIN.
    `${REFINEMENT_CHAIN.filter((n) => n.exercised).length} of the chain's ${REFINEMENT_CHAIN.length} ` +
    `identities are exercised here and stay distinct` +
    // the trailing clause is CONDITIONAL, because at B2 the open list emptied
    // and a hand-written "and X are declared" left a dangling sentence naming
    // nothing — a smaller version of the same staleness this file keeps finding
    (REFINEMENT_CHAIN.some((n) => !n.exercised)
      ? `; ${REFINEMENT_CHAIN.filter((n) => !n.exercised).map((n) => n.id).join(" and ")} are ` +
        `DECLARED and not exercised`
      : `, every one of them`) +
    `. STILL NOT CLAIMED: the six DUP-* rules, the d:/v: loci and ` +
    `BUDGET_EXHAUSTED terminals — a term needing any of them is refused by name, not approximated. ` +
    // DERIVED, because the hand-written version of this sentence said "stays
    // UNDECIDED" for a whole round after B1 decided it — green headline, green
    // cases, and the headline describing the world before the round that
    // produced it. The same class as the four-rung print and the UNDECIDED
    // spike status, in the check that exists to report this exact distinction.
    `The inputs model is ${INPUTS_MODEL.decided ? "DECIDED" : "UNDECIDED"} and ` +
    `${INPUTS_MODEL.implemented ? "IMPLEMENTED" : "NOT IMPLEMENTED"}: \`input\` ` +
    `${INPUTS_MODEL.implemented ? "lowers to a structural port and instantiate() closes it" : "is refused as lower-input-not-implemented"}, ` +
    `the three port falsifiers are ` +
    `${INSTANTIATION_FALSIFIERS.every((f) => f.status === "WITNESSED") ? "WITNESSED" : "DECLARED"} ` +
    `with I-4c carried end to end through native execution, and the refinement claim above holds over ` +
    `${LOWERING_SPEC.status.refinement_scope.holds_over}. DECLARED OPEN: ` +
    `${LOWERING_SPEC.status.refinement_scope.declared_open.split(".")[0]}.`);
process.exit(fail ? 1 : 0);
