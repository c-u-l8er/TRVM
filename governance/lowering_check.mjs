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
// THE RECEIPT ENDS AT THE TEMPLATE. Lowering's codomain is the template after
// B1/B1.2; a receipt ending in target_term_sem_id would keep asserting that
// lowering produced the executable term, which the two-level ruling denies.
const receipt = low.ok ? loweringReceipt(PROGRAM_SEM_ID, low.target_template_sem_id) : null;
{
  R("lowering-is-deterministic",
    low.ok && lower(PROGRAM).target_term === low.target_term
      && receipt.lowering_sem_id === LOWERING_SEM_ID
      && receipt.program_sem_id === PROGRAM_SEM_ID
      && receipt.lowering_receipt_id.startsWith("lrec-")
      && receipt.target_template_sem_id === low.target_template_sem_id
      && receipt.target_term_sem_id === undefined,
    `add(const 2, const 3) lowers to ${low.ok && low.target_term.length} characters of ic32, the same ` +
    `string twice. The RELATION is ${LOWERING_SEM_ID.slice(0, 16)}… and the APPLICATION is a receipt ` +
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
  const againId = again.ok ? kernelSemId(again.target_term) : null;
  const other = lower({ op: "add", a: { op: "const", value: 3 }, b: { op: "const", value: 2 } });
  R("re-lowering-verifies",
    againId === TARGET_TERM_SEM_ID && again.target_term === low.target_term
      && again.target_template_sem_id === low.target_template_sem_id
      && other.ok && kernelSemId(other.target_term) !== TARGET_TERM_SEM_ID
      && other.target_template_sem_id !== low.target_template_sem_id,
    `lowering the program again independently reaches the same target_term_sem_id ` +
    `(${String(TARGET_TERM_SEM_ID).slice(0, 12)}…) and the same target_template_sem_id ` +
    `(${String(low.target_template_sem_id).slice(0, 12)}…), which is the whole verification — no film. ` +
    `A film is evidence for a TRANSITION SYSTEM and lowering is a relation; filming it would invent ` +
    `internal compiler steps and make implementation strategy semantic, which is the mistake the ` +
    `read-order ruling refused. add(3,2) lowers to a DIFFERENT target term, so the id is not vacuous`);
}

/* ── 3. NATIVE EXECUTION, observed, and the C side agrees on the pre-state ── */
const initial = await runCanon(low.target_term, []);
const nf = await runCanon(low.target_term, ["--nf"]);
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
    instantiation_sem_id: null,   // exercised:false — no instantiate() yet
    inputs_sem_id: null,          // exercised:false — the environment is {}
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
      && open.every((n) => value[n.id] === null && typeof n.why_not === "string"),
    exercised.map((n) => `${n.id.replace("_sem_id", "")}=${String(value[n.id]).slice(0, 10)}…`)
      .join(" · ") +
    ` — ${vals.length} distinct values over a ${declared.length}-node chain, and the count is DERIVED ` +
    `from REFINEMENT_CHAIN rather than asserted. Collapsing any pair turns a refinement statement into ` +
    `a RENAMING, which is the failure this chain exists to avoid. DECLARED AND NOT EXERCISED: ` +
    `${open.map((n) => n.id).join(", ")} — the ids exist and are distinct, but this fixture reaches ` +
    `its term through lower()'s convenience emission rather than through instantiate(), so naming them ` +
    `here is scope rather than coverage`);
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
    ports.length === 0 && emitted === low.target_term
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
    // DERIVED. This sentence said "Six identities stay distinct" for the round
    // in which the chain grew a seventh node, in the headline of the check whose
    // job is to report exactly that. Same species as the four-rung print and the
    // UNDECIDED spike status — and the count below cannot disagree with the case
    // above it, because both read REFINEMENT_CHAIN.
    `${REFINEMENT_CHAIN.filter((n) => n.exercised).length} of the chain's ${REFINEMENT_CHAIN.length} ` +
    `identities are exercised here and stay distinct; ` +
    `${REFINEMENT_CHAIN.filter((n) => !n.exercised).map((n) => n.id).join(" and ")} are DECLARED and ` +
    `not exercised until instantiation is built. STILL NOT CLAIMED: the six DUP-* rules, the d:/v: loci and ` +
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
