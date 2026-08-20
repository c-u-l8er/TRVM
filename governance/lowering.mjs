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
export const LOWERING_VERSION = "0.3.0";

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

/* ── WHAT IS HASHED, AND WHAT IS MERELY TRUE ──────────────────────────────
   B1's first cut hashed the WHOLE spec, lifecycle fields included, so
   `implemented: false -> true` moved LOWERING_SEM_ID from lsem-5673108765b4…
   to lsem-63f98923ed13… without one line of the relation's meaning changing.
   B2 becoming built would have re-identified a relation B1 froze. `decided_at`
   did the same, and INSTANTIATION_SEM_ID moved when the conformance-test STATUS
   sentence was reworded.

   That is round 16 arriving inside the compiler specification: an identity
   depending on something that should not matter. The split:

       SEMANTICS   what the relation DOES — changing it changes emitted terms
                   or accepted inputs.  HASHED.
       STATUS      what the project has done about it — rounds, evidence
                   grades, whether code exists yet.  NOT HASHED.

   DECLARED OPEN, because the split is real and not total: the semantic records
   below are still English. `dup_label_policy` and `substitution` are NORMATIVE
   prose — there is no formal encoding of them in this tree today — so rewording
   them still moves the id, and that is correct-but-brittle rather than solved.
   What has been removed is the class GPT measured: lifecycle and evidence
   status can no longer re-identify a relation. A formal target-AST grammar
   would close the rest, and it is not written.

   The B1 ids are kept below as OVERBOUND_TRANSITIONAL_SEM_IDS rather than
   erased: they were the honest identities of the overbound projection, and a
   record that quietly replaces them would be doing what this round is fixing. */
export const INSTANTIATION_SEMANTICS = Object.freeze({
  relation: "target_template + inputs -> closed target term",
  port_namespace: INPUT_PORT_SPEC.namespace,
  port_identity: Object.freeze({
    source_name_semantic: true,
    target_allocation_semantic: false,
    unicode_normalization: false,
    rule: INPUT_PORT_SPEC.identity_rule,
    canonical_form: INPUT_PORT_SPEC.canonical_form,
  }),
  substitution: "each {op:\"input-port\", source_name:N} node is replaced by the canonical target " +
    "encoding of the value bound to N. Substitution is simultaneous and capture-free: an embedded " +
    "value's own binders are alpha-renamed away from the template's, because a value that captured a " +
    "template binder would make the term depend on the emitter's naming, which is exactly the " +
    "allocation dependence the port rule exists to remove.",
  missing_input: "REFUSED by name — instantiate-missing-input:<source_name>. Not defaulted: a default " +
    "is a value nobody supplied appearing inside an identity. NOTE that the SOURCE evaluator refuses " +
    "the same situation as program-input-missing:<name>, at a different layer and under a different " +
    "code; refusal-preservation between the two is DECLARED OPEN and is named in " +
    "REFINEMENT_SCOPE below rather than assumed.",
  // REVISED AT B1.1, and the first version was wrong twice over.
  extra_input: "IGNORED. An input the template has no port for does not participate in the term. " +
    "B1 froze this as a refusal on the argument that accepting it would let inputs_sem_id vary while " +
    "target_term_sem_id did not, 'so the receipt would stop being a function'. That argument is " +
    "FALSE — a function may be many-to-one, and (template, {x:2}) and (template, {x:2, unused:999}) " +
    "mapping to the same term is exactly such a function. And the rule contradicted the SOURCE: " +
    "evaluate({op:\"input\",name:\"x\"}, {}, {x:2, y:999}) returns 2, so refusing extras at the " +
    "target would have broken refinement BY CONSTRUCTION on the first program that had one. " +
    "different inputs_sem_id -> same target_term_sem_id is not an identity defect; it is the correct " +
    "statement that executable semantics do not depend on unused data. Making extras invalid would " +
    "be a SOURCE-LANGUAGE change requiring a new CORE_SEM_ID, and the instantiator may not impose it " +
    "unilaterally.",
  input_value_embedding: "a supplied value is embedded by the SAME target encoding lowering uses for " +
    "a constant of that type. A value the encoding cannot express is REFUSED by name rather than " +
    "approximated, on the same rule that makes lowering total-or-refusing on its fragment.",
  semantic_refusals: ["instantiate-missing-input", "instantiate-unencodable-input"],
});

/** NOT hashed into INSTANTIATION_SEM_ID. Everything here is a fact about the
 *  project rather than about the relation, and B2 will change all of it. */
export const INSTANTIATION_STATUS = Object.freeze({
  decided_at: "round 27, pass B1",
  semantics_corrected_at: "round 27, pass B1.1 — extra_input and the semantic/status split",
  implemented: false,
  operational_refusals: ["instantiate-not-implemented"],
  conformance_vectors: "DECLARED OPEN until B2. The three falsifiers are named in " +
    "INSTANTIATION_FALSIFIERS and none of them is written yet.",
  no_film: "instantiation gets NO FILM. It is a deterministic RELATION, not a transition system, so " +
    "its instrument is independent RE-INSTANTIATION — the same argument that gives lowering " +
    "re-lowering rather than a film. This is a statement about the INSTRUMENT, not about the " +
    "relation's meaning, which is why it lives here and is not hashed.",
});

/** A reader's view. Not hashed; the two halves above are the sources. */
export const INSTANTIATION_SPEC = Object.freeze({
  semantics: INSTANTIATION_SEMANTICS, status: INSTANTIATION_STATUS });

/** THE DOMAIN OF THE REFINEMENT CLAIM, stated before anything is built so that
 *  B2's first green witness cannot quietly be read as more than it is. */
export const REFINEMENT_SCOPE = Object.freeze({
  holds_over: "canonical, fully bound input environments — every port the template declares has a " +
    "value in canonical_inputs, and instantiation succeeds",
  extra_inputs: "IN SCOPE: unused canonical inputs are ignored by both source and target, and the " +
    "witness includes one",
  declared_open: "SOURCE-REFUSAL <-> INSTANTIATION-REFUSAL. The source refuses a missing input as " +
    "program-input-missing:<name> during EVALUATION; instantiation refuses it as " +
    "instantiate-missing-input:<name> before any target term exists. Those are different layers, " +
    "different codes and different moments, and refinement over refusals is a separate theorem that " +
    "is not attempted here. Claiming refusal preservation without it would be the two-grades-of-" +
    "evidence mistake round 26 made about films.",
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
      "without this one, a and b prove only that a label is being copied around",
    // THE FIXTURE IS MANDATED, because the obvious one cannot fail. add(x, y)
    // with x=2, y=3 gives 5 under the correct binding and 5 under the swap:
    // addition is commutative, so a symmetric witness is green whether or not
    // the binding was honoured. That is a test whose output cannot reveal the
    // defect it is named for — the species this tree has caught four times.
    fixture: "add(input(\"x\"), add(input(\"x\"), input(\"y\"))) with x=2, y=3. Correct binding " +
      "evaluates to 7 and the x/y swap to 8, verified against the SOURCE evaluator, so the witness " +
      "reaches a different target term, a different native result and a different " +
      "target_outcome_sem_id rather than merely different target bytes.",
    fixture_is_mandatory: "a symmetric fixture such as add(input(\"x\"), input(\"y\")) is REFUSED " +
      "for this falsifier: 2+3 == 3+2, so it would pass under a swapped binding and prove nothing" }),
]);

/* ── LOWERING: the same split ────────────────────────────────────────────── */
export const LOWERING_SEMANTICS = Object.freeze({
  language: "TRVM-DERIVE-CORE",
  source_core_sem_id: CORE_SEM_ID,
  target_encoding: TARGET_ENCODING,
  lowered_ops: LOWERED_OPS,
  inputs: Object.freeze({
    model: "template-then-instantiation",
    ruling: "TWO LEVELS, TWO IDENTITIES. Lowering produces a PARAMETERIZED target TEMPLATE whose " +
      "identity is a function of the program alone; instantiation closes that template against " +
      "canonical inputs and produces the executable TERM. 'Parameterized versus instantiated' was a " +
      "false choice — the template is parameterized AND the executed term is necessarily closed.",
    template_identity_rule: "target_template_sem_id — a function of program_sem_id and " +
      "lowering_sem_id, reusable across invocations and independent of invocation data",
    executable_term_identity_rule: "target_term_sem_id — a function of target_template_sem_id, " +
      "instantiation_sem_id and inputs_sem_id",
    instantiation_sem_id_is_separate: true,
  }),
  refusal_semantics: TARGET_ENCODING.refusals,
  totality: "lowering is TOTAL on the lowered fragment and REFUSES by name outside it. A lowering " +
    "that silently emitted something for an op it does not encode would make the refinement theorem " +
    "a statement about whatever it happened to emit.",
});

/** NOT hashed. Rounds, evidence grades, and whether the code exists. */
export const LOWERING_STATUS = Object.freeze({
  decided_at: "round 27, pass B1",
  semantics_corrected_at: "round 27, pass B1.1",
  implemented: false,
  why_decided_before_implemented: "an unstated variable inside target_term_sem_id is the round-16 " +
    "hidden-identity bug class. Deciding this while writing `input` is how it gets in. The first " +
    "lowering witness used inputs={} and therefore decided nothing, which is why the decision is a " +
    "separate act rather than a consequence of the next commit.",
  falsifiers: "INSTANTIATION_FALSIFIERS — three, all DECLARED, none written",
  refinement_scope: REFINEMENT_SCOPE,
});

/** The inputs model, as the batteries and the grid read it. Semantics live in
 *  LOWERING_SEMANTICS.inputs; the two lifecycle flags live here and are the
 *  reason this object is NOT hashed into any identity. */
export const INPUTS_MODEL = Object.freeze({
  decided: true,
  implemented: false,
  semantics: LOWERING_SEMANTICS.inputs,
  status: LOWERING_STATUS,
  why_two_relations: "a template can be perfectly lowered while instantiation binds \"x\" to the port " +
    "for \"y\". Merged, a target failure is ambiguous between a mistranslated program and correctly " +
    "translated code with miswired inputs. Separated, each is independently falsifiable.",
  receipt: "InstantiationReceipt {target_template_sem_id, instantiation_sem_id, inputs_sem_id, " +
    "target_term_sem_id}, verified by INDEPENDENTLY RE-INSTANTIATING, the way LoweringReceipt is " +
    "verified by re-lowering",
});

/** A reader's view. NOT hashed — LOWERING_SEMANTICS is what the id commits to. */
export const LOWERING_SPEC = Object.freeze({
  semantics: LOWERING_SEMANTICS, status: LOWERING_STATUS });

/** The identity of the RELATION. Content-bound, like every other id here: a
 *  bare "TRVM-LOWERING-v1" label would be a name anyone could claim, which the
 *  primitive ruling already refuses for `componentReachability`.
 *
 *  IT MOVED AT B1, AND THAT WAS RIGHT: deciding the inputs model changed what
 *  the relation MEANS, and an id surviving that ruling unchanged would claim the
 *  decision was not part of the relation.
 *
 *  IT MOVED AGAIN AT B1.1, AND THAT IS A FIX. v1 hashed the whole spec including
 *  lifecycle, so `implemented: false -> true` re-identified the relation. v2
 *  hashes LOWERING_SEMANTICS only, so B2 becoming BUILT cannot move it. */
export const LOWERING_SEM_ID =
  "lsem-" + H("TRVM-LOWERING-SEM-v2|" + canonicalBytes(LOWERING_SEMANTICS));

/** The identity of the INSTANTIATION relation — separate from lowering's,
 *  because they are separate relations. See INPUTS_MODEL.why_two_relations.
 *  Semantics only, for the reason above. */
export const INSTANTIATION_SEM_ID =
  "isem-" + H("TRVM-INSTANTIATION-SEM-v2|" + canonicalBytes(INSTANTIATION_SEMANTICS));

/** THE OVERBOUND B1 IDENTITIES, kept rather than erased. They were the honest
 *  ids of the projection B1 shipped, and a record that silently replaced them
 *  would be doing the thing this correction is about. Anything citing them cites
 *  a relation whose id was a function of round numbers and evidence prose. */
export const OVERBOUND_TRANSITIONAL_SEM_IDS = Object.freeze({
  note: "B1 (round 27) hashed the full spec, lifecycle fields included. Superseded at B1.1 by the " +
    "TRVM-*-SEM-v2 projections above, which hash semantics only.",
  lowering_sem_id_v1: "lsem-5673108765b400bc9abff5a7b7b8fcb4375cf9894c5dbd50201efec3df79ccbc",
  instantiation_sem_id_v1: "isem-c6b793933e30c1e6ad29dfd1cd1cc04c42c06858bea816bbe7750806626435a5",
  measured: "flipping only `implemented` moved lowering to lsem-63f98923ed13…; rewording only the " +
    "conformance-test STATUS sentence moved instantiation. Neither changed a rule.",
});

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
