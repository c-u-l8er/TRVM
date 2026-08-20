/* ═══════════════════════════════════════════════════════════════════════════
   lowering.mjs — v0.1.0 — the source language reaches the governed runtime

   Three logically independent relations, which is the whole design and not a
   decomposition for tidiness. Each can fail while the others hold: a lowering
   can be perfect while the decoder misreads the normal form; a decoder can be
   perfect while lowering emitted the wrong target term; and the runtime can
   execute a correctly lowered term incorrectly. Twenty-five rounds have gone
   into separating claims that felt like one claim, so they get three
   obligations, three laws, and six identities that may not collapse.

       program_sem_id  ──lowering_sem_id──▶  target_term_sem_id
                                                    │
                                             native ic32 execution
                                                    ▼
                                              target_nf_sem_id
                                                    │
                                              decode_sem_id
                                                    ▼
                                           target_outcome_sem_id
       source evaluator ─────────────────▶ source_outcome_sem_id

       REFINEMENT:  source_outcome_sem_id == target_outcome_sem_id

   THE LOWERING GETS NO FILM, and that is a ruling rather than an omission. A
   semantic film is evidence for a TRANSITION SYSTEM; lowering is a relation
   DeriveProgram → TargetTerm. Filming it would invent a sequence of internal
   compiler steps and make implementation strategy semantic — the mistake the
   read-order ruling refused when it kept access order out of the footprint and
   out of the semantic projection. The instrument here is RE-LOWERING: lower
   again, independently, and compare canonical target-term identity. A film
   becomes appropriate only if the lowering engine itself ever becomes a
   governed transition system whose intermediate steps matter.

   TWO IDS, NOT ONE, and they are split before either is written. One id must
   not silently answer both "which lowering semantics is this?" and "what
   happened when we lowered this particular program?":

       lowering_sem_id      the RELATION — H over the source core identity, the
                            target encoding, the canonical specification
       LoweringReceipt      the APPLICATION — {program_sem_id, lowering_sem_id,
                            target_term_sem_id}, itself content-addressed

   DEFERRED, AND NAMED SO IT IS NOT DISCOVERED. `add(const 2, const 3)` has
   inputs = {}, so this does not decide PARAMETERIZED lowering (program → target
   term with input ports, inputs arriving at execution, target_term_sem_id a
   function of the program alone) versus INSTANTIATED lowering (program +
   canonical_inputs → closed target term, where the identity must say so). Both
   are coherent and they are different systems. That decision comes BEFORE the
   `input` op, because an unstated variable inside target_term_sem_id is exactly
   the hidden-identity bug class round 16 exists to prevent. `INPUTS_MODEL`
   below records that it is undecided, and lowering REFUSES any program whose
   evaluation would consult an input.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { canonicalBytes, CORE_SEM_ID, programSemId } from "./derive_protocol.mjs";

const H = (s) => createHash("sha256").update(s).digest("hex");
export const LOWERING_VERSION = "0.2.0";

/* ── the target encoding ──────────────────────────────────────────────────
   ic32's interaction net is linear: a variable used twice needs an explicit
   dup. So Church numerals are emitted in LINEAR form with explicit dup labels,
   which is the shape the conformance corpus already uses for church_apply_N.
   The label policy is part of the encoding and therefore part of its identity:
   two lowerings that agree on everything except which integers they hand the
   dups are two different lowerings, and pretending otherwise would let an
   allocation detail hide inside a semantic id. */
export const TARGET_ENCODING = Object.freeze({
  target: "ic32 interaction net, SEMSTATE-CANONICAL-v1",
  numbers: "linear Church numerals. n is λf.λx. followed by n-1 dup bindings of " +
    "f and then n nested applications; 0 is λf.λx.x and 1 is λf.λx.(f x), which need no dup.",
  add: "λm.λn.λf.λx.!&L{f0,f1}=f;((m f0) ((n f1) x)) — the only non-linear use is f, " +
    "duplicated once per addition.",
  dup_label_policy: "labels are assigned by a counter that starts at 0 and advances in the " +
    "order the lowering emits them, depth-first, operands in declared field order. DETERMINISTIC " +
    "and part of this encoding's identity: a different assignment is a different encoding, because " +
    "the label reaches the canonical signature through Sn(…) and would otherwise be an allocation " +
    "detail hiding inside a semantic id.",
  refusals: ["lower-unsupported-op", "lower-non-integer-constant", "lower-negative",
    "lower-input-not-implemented", "lower-reads-undecided"],
});

/* WHICH ops lower. Deliberately the smallest set that makes the refinement
   theorem non-trivial, and everything else is a NAMED refusal rather than a
   silent omission. `input`, `read`, `scope` and `cite` are absent because the
   inputs model is undecided; `sub`, `mul` and `len` are absent because they are
   simply not encoded yet, and saying so is cheaper than discovering it. */
export const LOWERED_OPS = Object.freeze(["const", "add"]);

/* ── B1: THE INPUTS MODEL, DECIDED ────────────────────────────────────────
   The question was posed as parameterized VERSUS instantiated. It is a FALSE
   CHOICE: the template is parameterized AND the executed term is necessarily
   closed. They are two relations, they compose, and they answer different
   questions, so they get two identities.

       program_sem_id
             │  lowering_sem_id
             ▼
       target_template_sem_id           reusable, independent of invocation data
             │  instantiation_sem_id + inputs_sem_id
             ▼
       target_term_sem_id               the closed executable term
             │  native semantic film
             ▼
       target_nf_sem_id
             │  decode_sem_id
             ▼
       target_outcome_sem_id  ==  source_outcome_sem_id

   WHY THEY MAY NOT BE MERGED, and this is the whole of the ruling: a template
   can be perfectly lowered while instantiation binds "x" to the port for "y".
   Merge the relations and a target failure becomes ambiguous between *the
   program was translated incorrectly* and *the runtime inputs were wired into a
   correct template incorrectly*. Twenty-seven rounds have gone into removing
   exactly that kind of ambiguity, and this one is cheap to keep out.

   DECIDED, NOT BUILT. `input` still does not lower. The refusal changes name
   from lower-inputs-undecided to lower-input-not-implemented, because "we have
   not ruled" and "we have ruled and not written it" are different states and a
   refusal that cannot tell them apart is a stale instrument waiting to happen. */
export const INPUT_PORT_SPEC = Object.freeze({
  namespace: "TRVM-INPUT-PORT-v1",
  identity_rule: "port_sem_id = H(\"TRVM-INPUT-PORT-v1|\" + canonicalBytes(source_input_name)). The " +
    "port's target-side identity is a function of the SOURCE NAME and the encoding, and never of " +
    "whichever variable the emitter happened to allocate.",
  canonical_form: "at the canonical target-AST layer a port is {op:\"input-port\", source_name:\"x\"}, " +
    "BEFORE any textual or ic32 variable allocation. Two implementations that internally allocate " +
    "_impl17 and q93 canonicalize to the same node and therefore to the same target_template_sem_id.",
  quotient: "internal target variable names are NON-SEMANTIC (alpha-equivalent); source input keys " +
    "are SEMANTIC. This is the INVERSE of the round-16 bug: there, identity depended on a spelling " +
    "that should not matter; here the danger is identity depending on an ALLOCATION that should not " +
    "matter while losing the SOURCE NAME that must.",
  no_normalization: "source input names are NOT Unicode-normalized. If the frozen core distinguishes " +
    "two code-point sequences as different names, the port identity preserves that exact distinction. " +
    "Normalizing would itself be a language-semantic change and belongs to the language, not to this " +
    "encoding — and a quotient introduced at the encoding layer is invisible to the source.",
});

export const INSTANTIATION_SPEC = Object.freeze({
  relation: "target_template + inputs -> closed target term",
  port_spec: INPUT_PORT_SPEC,
  identifies: "THE RELATION, NOT THE INVOCATION. This id commits to the port namespace and version, " +
    "the source-name-to-port rule, missing- and extra-input semantics, the canonical embedding of an " +
    "input value, template substitution semantics, the refusal vocabulary and the conformance " +
    "vectors. It does NOT contain x=5; that is inputs_sem_id.",
  substitution: "each {op:\"input-port\", source_name:N} node is replaced by the canonical target " +
    "encoding of the value bound to N. Substitution is simultaneous and capture-free: an embedded " +
    "value's own binders are alpha-renamed away from the template's, because a value that captured a " +
    "template binder would make the term depend on the emitter's naming, which is exactly the " +
    "allocation dependence the port rule exists to remove.",
  missing_input: "REFUSED by name — instantiate-missing-input:<source_name>. Not defaulted: a default " +
    "is a value nobody supplied appearing inside an identity.",
  extra_input: "REFUSED by name — instantiate-extra-input:<source_name>. An input the template has no " +
    "port for cannot affect the term, so accepting it would let inputs_sem_id vary while " +
    "target_term_sem_id does not, and the receipt would stop being a function.",
  input_value_embedding: "a supplied value is embedded by the SAME target encoding lowering uses for " +
    "a constant of that type. A value the encoding cannot express is REFUSED by name rather than " +
    "approximated, on the same rule that makes lowering total-or-refusing on its fragment.",
  refusals: ["instantiate-missing-input", "instantiate-extra-input", "instantiate-unencodable-input",
    "instantiate-not-implemented"],
  conformance_vectors: "DECLARED OPEN until B2. The three falsifiers are named in INSTANTIATION_" +
    "FALSIFIERS below and none of them is written yet; this spec is frozen so that they can be " +
    "written against something rather than alongside it.",
  no_film: "instantiation gets NO FILM. It is a deterministic RELATION, not a transition system, so " +
    "its instrument is independent RE-INSTANTIATION — the same argument that gives lowering " +
    "re-lowering rather than a film. A film here would be evidence about the target runtime's steps, " +
    "which is a different claim about a different object.",
});

/** The three falsifiers that must hold before `input` becomes executable
 *  semantics. Declared as DATA so B2 writes them against a frozen statement and
 *  so a future reader can see which of them exist — the alternative is a prose
 *  list that drifts from the suite, which this tree has now watched happen to a
 *  law count, a case count and a rung count. */
export const INSTANTIATION_FALSIFIERS = Object.freeze([
  Object.freeze({ id: "I-4a", name: "allocation-invariance", status: "DECLARED",
    claim: "same source input name, different internal target variable allocation " +
      "(_impl17 vs q93) -> the SAME target_template_sem_id",
    proves: "the emitter's allocation is not semantic" }),
  Object.freeze({ id: "I-4b", name: "source-name-sensitivity", status: "DECLARED",
    claim: "different source input names, same allocation strategy -> DIFFERENT " +
      "target_template_sem_id",
    proves: "the source input key IS semantic, so the quotient did not throw it away" }),
  Object.freeze({ id: "I-4c", name: "binding-has-force", status: "DECLARED",
    claim: "x/y port binding swapped during instantiation -> the target term or outcome changes, or " +
      "is refused; and it must NEVER validate under the correct instantiation receipt",
    proves: "instantiation HONOURS the port identity rather than carrying it decoratively — " +
      "without this one, a and b prove only that a label is being copied around" }),
]);

export const INPUTS_MODEL = Object.freeze({
  decided: true,
  decided_at: "round 27, pass B1",
  ruling: "TWO LEVELS, TWO IDENTITIES. Lowering produces a PARAMETERIZED target TEMPLATE whose " +
    "identity is a function of the program alone; instantiation closes that template against " +
    "canonical inputs and produces the executable TERM. 'Parameterized versus instantiated' was a " +
    "false choice — the template is parameterized AND the executed term is necessarily closed.",
  why_two_relations: "a template can be perfectly lowered while instantiation binds \"x\" to the port " +
    "for \"y\". Merged, a target failure is ambiguous between a mistranslated program and correctly " +
    "translated code with miswired inputs. Separated, each is independently falsifiable.",
  template_identity: "target_template_sem_id — a function of program_sem_id and lowering_sem_id, " +
    "reusable across invocations and independent of invocation data",
  term_identity: "target_term_sem_id — a function of target_template_sem_id, instantiation_sem_id " +
    "and inputs_sem_id",
  receipt: "InstantiationReceipt {target_template_sem_id, instantiation_sem_id, inputs_sem_id, " +
    "target_term_sem_id}, verified by INDEPENDENTLY RE-INSTANTIATING, the way LoweringReceipt is " +
    "verified by re-lowering",
  implemented: false,
  why_decided_before_implemented: "an unstated variable inside target_term_sem_id is the round-16 " +
    "hidden-identity bug class. Deciding this while writing `input` is how it gets in. The first " +
    "lowering witness used inputs={} and therefore decided nothing, which is why the decision is a " +
    "separate act rather than a consequence of the next commit.",
});

export const LOWERING_SPEC = Object.freeze({
  language: "TRVM-DERIVE-CORE",
  source_core_sem_id: CORE_SEM_ID,
  target_encoding: TARGET_ENCODING,
  lowered_ops: LOWERED_OPS,
  inputs_model: INPUTS_MODEL,
  totality: "lowering is TOTAL on the lowered fragment and REFUSES by name outside it. A lowering " +
    "that silently emitted something for an op it does not encode would make the refinement theorem " +
    "a statement about whatever it happened to emit.",
});

/** The identity of the RELATION. Content-bound, like every other id here: a
 *  bare "TRVM-LOWERING-v1" label would be a name anyone could claim, which the
 *  primitive ruling already refuses for `componentReachability`.
 *
 *  IT MOVED AT B1, AND THAT IS THE POINT. LOWERING_SPEC carries inputs_model,
 *  so deciding the inputs model changes the lowering relation and therefore its
 *  identity. A lowering_sem_id that survived this ruling unchanged would be
 *  claiming the decision was not part of the relation, and the refinement
 *  receipt is re-cut rather than re-pointed. */
export const LOWERING_SEM_ID = "lsem-" + H("TRVM-LOWERING-v1|" + canonicalBytes(LOWERING_SPEC));

/** The identity of the INSTANTIATION relation — separate from lowering's,
 *  because they are separate relations. See INPUTS_MODEL.why_two_relations. */
export const INSTANTIATION_SEM_ID =
  "isem-" + H("TRVM-INSTANTIATION-v1|" + canonicalBytes(INSTANTIATION_SPEC));

/** The identity of a particular INVOCATION's inputs. This is where `x=5` lives,
 *  and it is deliberately not inside INSTANTIATION_SEM_ID: one names the rule,
 *  the other names the data the rule was applied to. Same shape as programSemId
 *  and grantId — one canonical traversal, no second read — and like them it is
 *  called on data the authority already owns. */
export const inputsSemId = (inputs) => "insem-" + H("TRVM-INPUTS-v1|" + canonicalBytes(inputs));

/** The port's target-side identity: a function of the SOURCE NAME, never of the
 *  emitter's allocation. Defined here so B2's falsifiers have something to be
 *  falsified against; nothing calls it yet. */
export const portSemId = (source_name) =>
  "psem-port-" + H(INPUT_PORT_SPEC.namespace + "|" + canonicalBytes(source_name));

/** The receipt SHAPE, frozen; the verifier is B2's work. Named fields rather
 *  than a tuple because a receipt whose positions carry meaning is a receipt
 *  that can be read wrong. */
export const INSTANTIATION_RECEIPT_FIELDS = Object.freeze([
  "target_template_sem_id", "instantiation_sem_id", "inputs_sem_id", "target_term_sem_id"]);

/** DECLARED, NOT BUILT. Named so that "the model is undecided" and "the model is
 *  decided and the code is not written" cannot be confused — they were the same
 *  refusal string until B1, and a refusal that cannot distinguish two states is
 *  a stale instrument with a delay fuse. */
export function instantiate() {
  throw new Error("instantiate-not-implemented: the model is frozen at INPUTS_MODEL and the three " +
    "falsifiers in INSTANTIATION_FALSIFIERS are DECLARED; B2 writes them and this");
}

/* ── the lowering ─────────────────────────────────────────────────────────── */

/** Linear Church numeral. n uses f exactly n times, so n-1 dups. */
function church(n, labels) {
  if (n === 0) return "λf.λx.x";
  if (n === 1) return "λf.λx.(f x)";
  const binds = [];
  let cur = "f";
  for (let i = 0; i < n - 1; i++) {
    const L = labels.next();
    if (i < n - 2) { binds.push(`!&${L}{a${i},t${i}}=${cur};`); cur = `t${i}`; }
    else binds.push(`!&${L}{a${i},a${i + 1}}=${cur};`);
  }
  let body = "x";
  for (let i = n - 1; i >= 0; i--) body = `(a${i} ${body})`;
  return `λf.λx.${binds.join("")}${body}`;
}

const ADD_COMBINATOR = (L) => `λm.λn.λf.λx.!&${L}{f0,f1}=f;((m f0) ((n f1) x))`;

/** program AST → canonical target term, or a NAMED refusal. Deterministic: the
 *  same AST always produces the same string, including its dup labels. */
export function lower(ast) {
  const labels = { n: 0, next() { return this.n++; } };
  const go = (node) => {
    if (!node || typeof node !== "object") throw new Error("lower-unsupported-op");
    if (!LOWERED_OPS.includes(node.op)) {
      if (["input"].includes(node.op)) throw new Error("lower-input-not-implemented");
      if (["read", "scope", "cite"].includes(node.op)) throw new Error("lower-reads-undecided");
      throw new Error("lower-unsupported-op: " + String(node.op));
    }
    if (node.op === "const") {
      if (!Number.isInteger(node.value)) throw new Error("lower-non-integer-constant");
      if (node.value < 0) throw new Error("lower-negative");
      return church(node.value, labels);
    }
    // `add`: operands in DECLARED FIELD ORDER, a before b, which is the core's
    // own evaluation order — so the label counter advances the same way the
    // source evaluator would have walked the tree.
    const a = go(node.a), b = go(node.b);
    return `((${ADD_COMBINATOR(labels.next())} ${a}) ${b})`;
  };
  try { return { ok: true, target_term: go(ast) }; }
  catch (e) { return { ok: false, reason: e.message }; }
}

/** The APPLICATION record. target_term_sem_id is supplied by the caller because
 *  it is a SEMANTIC identity of the target term — the ic32 canonical state id —
 *  and computing it is the kernel's job, not the lowering's. A lowering that
 *  minted the identity of its own output would be grading its own homework. */
export function loweringReceipt(program_sem_id, target_term_sem_id) {
  const receipt = { program_sem_id, lowering_sem_id: LOWERING_SEM_ID, target_term_sem_id };
  return Object.freeze({ ...receipt,
    lowering_receipt_id: "lrec-" + H("TRVM-LOWERING-RECEIPT-v1|" + canonicalBytes(receipt)) });
}

/* ── the decoder ──────────────────────────────────────────────────────────
   It reads the CANONICAL SEMANTIC SIGNATURE rather than a printed term, so it
   is reading the same bytes the bridge gate has agreed on since round 12 rather
   than a readback that could differ by a binder name. A Church numeral n is

       L0(L1( A(N0, A(N0, … A(N0, N1) … )) ))     with n applications
       L0(L1(N1))                                  for n = 0

   and anything else is a NAMED refusal. §5 compaction replaces a signature
   longer than 80 characters with '#'+sha256, which is irreversible, so a
   compacted signature is refused rather than guessed at — the boundary is real
   and it is better named than silently mis-decoded. */
export const DECODER_SPEC = Object.freeze({
  reads: "the SEMSTATE-CANONICAL-v1 signature of the target normal form, not a readback string",
  numbers: "linear Church numerals: L0(L1(A(N0,…A(N0,N1)…))) with n applications; L0(L1(N1)) is 0",
  outcome_shape: "STRUCTURAL — {status:'value', value} or {status:'refused', code, locus}. Never a " +
    "rendered reason: hashing rendered English would recreate round 16's 'the identity bound a " +
    "spelling' one layer up, where two conforming decoders differ by a comma.",
  refusals: ["decode-signature-compacted", "decode-not-a-church-numeral"],
  compaction_note: "§5 compaction is irreversible, so a compacted signature is REFUSED. This bounds " +
    "the decodable numerals and the bound is stated rather than discovered: at 80 characters the " +
    "signature holds roughly a dozen applications.",
});
export const DECODE_SEM_ID = "dsem-" + H("TRVM-DECODE-v1|" + canonicalBytes(DECODER_SPEC));

export function decode(signature) {
  if (typeof signature !== "string") return { ok: false, reason: "decode-not-a-church-numeral" };
  if (signature.includes("#")) return { ok: false, reason: "decode-signature-compacted" };
  const m = /^L(\d+)\(L(\d+)\((.*)\)\)$/.exec(signature);
  if (!m) return { ok: false, reason: "decode-not-a-church-numeral" };
  const fName = "N" + m[1], xName = "N" + m[2];
  let body = m[3], n = 0;
  const app = new RegExp("^A\\(" + fName + ",(.*)\\)$");
  for (;;) {
    if (body === xName) return { ok: true, outcome: { status: "value", value: n } };
    const a = app.exec(body);
    if (!a) return { ok: false, reason: "decode-not-a-church-numeral" };
    body = a[1]; n++;
    if (n > 1000) return { ok: false, reason: "decode-not-a-church-numeral" };
  }
}

/** TRVM-DERIVE-OUTCOME-v1, ruled in round 22 before it was built: the identity
 *  encodes STRUCTURALLY and never hashes a human-readable reason. */
export function outcomeSemId(outcome) {
  return "osem-" + H("TRVM-DERIVE-OUTCOME-v1|" + canonicalBytes(outcome));
}

/** The source side of the refinement, in the same structural shape. */
export function sourceOutcome(deriveResult) {
  return deriveResult.ok
    ? { status: "value", value: deriveResult.result.semantic_result.value }
    : { status: "refused", code: String(deriveResult.reason).split(":")[0], locus: "$" };
}

export { programSemId };
