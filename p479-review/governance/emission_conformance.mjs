/* ═══════════════════════════════════════════════════════════════════════════
   emission_conformance.mjs — EMISSION_CONFORMANCE-v1

   ONE RELATION, OVER A FAMILY OF FIXTURES:

       closed_template_sem_id --(emission_sem_id)--> target_term_sem_id

   THIS IS NOT ANOTHER RUNTIME TEST, and keeping that straight is the whole
   design. The transition relation has its own evidence — 45/45 native semantic
   films, 48/48 canonical bytes, two terminal classes, nine rules. What has
   never been established is that the CANONICAL EMITTER deterministically
   realises its own declared relation over more than a single fixture.

   Until now emission had exactly one witness: add(const 2, const 3) at the
   empty environment, inside lowering_check, where it is one identity in an
   eleven-node refinement chain. One fixture cannot distinguish "the emitter
   implements its relation" from "the emitter happens to be right about this
   term", and the relation is the thing every future compiler round builds on.

   ── WHAT A CONFORMANCE RECORD IS ──────────────────────────────────────────
   Three fields, and no more:

       closed_template_sem_id     the invocation-closed template, ctmpl-
       emission_sem_id            the RELATION's identity, constant across
                                  every fixture — a per-fixture emission id
                                  would identify invocations, not the relation
       target_term_sem_id         the executable term's identity, MINTED BY
                                  THE KERNEL and never by the emitter

   ── AND WHAT VERIFICATION IS ──────────────────────────────────────────────
   Not "does the emitter agree with itself". The verifier rebuilds the closed
   template from the program and inputs, re-emits through the canonical
   emitter, hands the bytes to a canonicaliser IT was given rather than one the
   emitter chose, and compares. That is B2.1's ruling made routine: an emitter
   that produced the artifact AND certified its identity would verify a wrong
   emission against itself.

   ── THREE IDENTITIES, A LADDER RATHER THAN A PAIR ─────────────────────────
   B6's header framed this as two properties in tension. It is three, and the
   middle one is where emission lives:

       exact emitted BYTES
              │ quotient alpha-renaming and label SPELLING
              ▼
       target_term_sem_id
              │ execute, normalise, decode
              ▼
       outcome_sem_id

   Different bytes may share a target_term_sem_id; different target_term_sem_ids
   may share an outcome_sem_id. This battery demonstrates BOTH, and the
   consequence for what an EmissionReceipt proves is exact: it carries no byte
   digest, so it does not and must not claim "these exact bytes were produced".
   It proves the closed template maps, under this emission semantics, to this
   canonical target-term identity. If byte reproducibility ever needs proving it
   belongs beside executable_artifact_id as PROVENANCE — not inside a semantic
   relation whose own codomain deliberately erases the spelling.

   THE TWO ADVERSARIES ARE THEREFORE DIFFERENT ANIMALS, and B6 fused them:

       E-F1  canonical drift. "Same closed template, same relation id, a changed
             claim about the target term, therefore REFUSE." Needs NO semantic
             equivalence, so it applies to every fixture.
       E-8   semantic equivalence. "Different target_term_sem_id, SAME meaning."
             Requires a real equivalence and is applicable only where the
             fragment supplies one — operand reordering, valid here because
             addition commutes, and not valid once `sub` exists.

   Fused, the canonical-drift falsifier would lose its adversary the moment a
   non-commutative operator arrived, for a reason having nothing to do with what
   it proves. B6.3.1 generalised E-8 onto a beta wrapper before that happened,
   and B7 is the round that would otherwise have collapsed it: the swap is not
   an equivalence for `sub`, and E-8c now runs it as a falsifier for the
   OPPOSITE property — that operand order IS semantic.

   ── B7: THE FAMILY GAINS FIXTURES THAT DO NOT EMIT ────────────────────────
   Every fixture from B6 to B6.3.1 produced a term. `sub` brings the first ones
   that must NOT, and they are not failures — they are the compiler saying its
   codomain is smaller than its source language:

       EMITTING    lower -> instantiate -> emit -> receipt -> verify, as before
       REFUSING    lower -> instantiate -> emit REFUSES BY NAME, and the record
                   stops there. NO target term, NO receipt, and no claim that
                   one exists. The evidence has to say WHY there is nothing
                   downstream, or a reader cannot tell a refusal from a gap.

   So the cases below split their populations explicitly rather than filtering
   silently: a case that says 9/9 when the family holds 14 has stopped counting
   what it names.

   NO NATIVE FILM IS REQUIRED HERE. GPT's ruling, and it is right: the runtime
   relation already carries its own evidence and re-proving it inside an
   emission battery would make emission correctness DEFINED BY execution,
   which is the collapse the layer separation exists to prevent. A downstream
   composition runs at the end as an INTEGRATION theorem, clearly labelled,
   over the JS oracle rather than the native emitter.

   Run: node emission_conformance.mjs   (exit 0 iff every case holds)
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { evaluate, canonicalBytes } from "./derive_protocol.mjs";
import { parse, extrude, FloatRt, semStateId, semStateSignature, runFloat, readback }
  from "./trvm_law_kernel.mjs";
import {
  lower, instantiate, emit, decodeOwnedAgainst, makeTargetDecoder, outcomeSemId, closedTemplateSemId,
  emissionReceipt, verifyEmissionReceiptAgainst, makeEmissionVerifier,
  EMISSION_SEM_ID, EMISSION_RECEIPT_FIELDS, IMPLEMENTED_LOWERED_OPS,
  CANONICAL_EMITTER_PROFILE, CANONICAL_EMITTER_PROFILE_ID, emitterProfileId,
  CANONICAL_EMITTER_ARTIFACT_ID, emitterArtifactId, emitterArtifactBundle,
  EMITTER_ARTIFACT_MEMBERS, EMITTER_ARTIFACT_INERT,
  TARGET_EXECUTABLE_ENCODING_SEM_ID, TARGET_TEMPLATE_ENCODING_SEM_ID,
  LOWERING_SEM_ID, INSTANTIATION_SEM_ID,
  TARGET_ENCODING, TARGET_TEMPLATE_ENCODING, SUPERSEDED_PRE_SUB_SEM_IDS,
  SUPERSEDED_MAP_IN_CODOMAIN_SEM_IDS,
  EMISSION_RULES, EMISSION_RULES_SEM_ID, EMITTER_ARTIFACT_SEMANTIC, EMISSION_SEMANTICS,
} from "./lowering.mjs";
import * as LOWERING_EXPORTS from "./lowering.mjs";

let ran = 0, fail = false;
/* THE HEADLINE IS DERIVED FROM THESE, NOT WRITTEN ALONGSIDE THEM. B6's summary
   line claimed a semantics-preserving allocation change moved target_term_sem_id
   and was refused across the whole family, and that an alpha-equivalent emitter
   differed in id on every fixture — both FALSE, and both contradicted by the cases printed
   immediately above them in the same run. The cases had been corrected when the
   measurement came in; the summary kept the pre-measurement theory, and it is
   the summary that lands in RESULTS.txt where a reader who runs nothing else
   still sees it. GPT caught it. Every quantity the final line states is now a
   field written by the case that measured it. */
const MEASURED = {};
const R = (id, cond, note) => {
  ran++;
  if (!cond) fail = true;
  console.log(`${cond ? "PASS" : "FAIL"}  ${id.padEnd(30)} ${note}`);
};

/* THE CANONICALISER IS THE KERNEL'S, AND IT IS PASSED IN. The emitter never
   sees it. `makeEmissionVerifier` takes it as a parameter for the same reason:
   the module that defines a relation must not also choose the oracle that
   judges it. */
const kernelSemId = (term) => { const frt = new FloatRt(); return semStateId(frt, extrude(frt, parse(frt, term))); };
const kernelSig = (term) => { const frt = new FloatRt(); return semStateSignature(frt, extrude(frt, parse(frt, term))); };
/* B8.1: THE OWNED NORMAL FORM, AND ITS IDENTITY ORACLE.
   Every decode below used to go bytes -> runFloat -> readback -> STRING ->
   reparse -> SIGNATURE -> decode, which laundered the normal form through two
   serializations to reach a decoder that then could not read it above Church
   11. The object is carried instead: runFloat, readback, and hand the SAME
   frozen snapshot to the identity oracle and to the recogniser. */
const ownedNf = (bytes) => { const o = runFloat(bytes); return readback(o.frt, o.root).nf; };
const identifyNf = (own) => semStateId(new FloatRt(), own);
const decodeTarget = makeTargetDecoder({ identifyNormalForm: identifyNf });
const decodeBytes = (bytes) => decodeTarget(ownedNf(bytes));
const verify = makeEmissionVerifier({ canonicaliseTarget: kernelSemId });

const C = (v) => ({ op: "const", value: v });
const ADD = (a, b) => ({ op: "add", a, b });
const SUB = (a, b) => ({ op: "sub", a, b });
const MUL = (a, b) => ({ op: "mul", a, b });
const IN = (name) => ({ op: "input", name });

/* ── THE FIXTURE FAMILY ───────────────────────────────────────────────────
   Eight, chosen to vary the things the RELATION can be wrong about rather
   than to vary the arithmetic: arity zero through nesting, the empty
   environment against a bound one, one port against two, and the asymmetric
   binding that is the only shape able to reveal a swapped port. Anything the
   fragment cannot express is out of scope by construction —
   IMPLEMENTED_LOWERED_OPS is const/add/input and this file derives that list
   rather than restating it. */
const FIXTURES = [
  { id: "E-1 const 0", program: C(0), inputs: {},
    why: "the smallest term the encoding admits. Zero is the church numeral with NO applications, so " +
         "it is the one case where the emitter's loop body never runs" },
  { id: "E-2 const 1", program: C(1), inputs: {},
    why: "one application. The boundary between 'no body' and 'a body', which is where an off-by-one " +
         "in the encoding lives if there is one" },
  { id: "E-3 const 3", program: C(3), inputs: {},
    why: "several applications and therefore several dup cells, each needing a distinct label" },
  { id: "E-4 add(0,1)", program: ADD(C(0), C(1)), inputs: {},
    why: "the operator over the two smallest operands — the first term in which two sub-emissions have " +
         "to coexist without their allocations colliding" },
  { id: "E-5 add(2,3)", program: ADD(C(2), C(3)), inputs: {},
    why: "the historical witness. It is the ONE fixture emission had before this battery, and it is " +
         "kept so that the family contains the term whose 129 bytes are already on the record" },
  { id: "E-6 nested add", program: ADD(ADD(C(1), C(2)), C(3)), inputs: {},
    why: "an operand that is itself an operator application. Nesting is where an emitter that allocates " +
         "from a shared counter rather than a scoped one produces a collision" },
  { id: "E-7 one port", program: ADD(IN("x"), C(1)), inputs: { x: 2 },
    why: "a port closed by an invocation — the first fixture whose closed template is not equal to its " +
         "open template, so instantiation and emission are visibly different relations" },
  { id: "E-8 two-port collapse", program: ADD(IN("x"), IN("y")), inputs: { x: 2, y: 3 },
    why: "MISLABELLED 'I-4c asymmetric' at B6 AND IT IS NOT I-4C — add(x,y) with x=2,y=3 gives 5 under " +
         "the correct binding and 5 under the swap, which is the SYMMETRIC fixture B2 explicitly " +
         "rejected for that falsifier (INSTANTIATION_FALSIFIERS I-4c: 'a test whose output cannot " +
         "reveal the defect it is named for'). Kept under an honest name, because what it actually " +
         "proves is worth having: it closes to the SAME closed template as E-5 add(const 2, const 3), " +
         "so two different source and instantiation histories become indistinguishable to emission" },
  { id: "E-9 I-4c asymmetric", program: ADD(IN("x"), ADD(IN("x"), IN("y"))), inputs: { x: 2, y: 3 },
    why: "THE ACTUAL I-4c fixture, as lowering.mjs mandates it: x + (x + y) gives 7 under the correct " +
         "binding and 8 under the swap, so its output CAN reveal a swapped port. It is also a distinct " +
         "closed template (ctmpl-efba3154…) rather than a relabelling of an existing one, which is why " +
         "the family did not need a fixture invented to force distinctness" },
  /* ── B7. THE SUBTRACTION FIXTURES ────────────────────────────────────────
     Five that emit and four that refuse, and the four are as load-bearing as
     the five. `emits: false` is DECLARED per fixture rather than discovered,
     so a fixture that starts emitting when it should not — a saturating
     emitter, a representability check relaxed — fails E-0 instead of quietly
     joining the positive population and inflating every count below it. */
  { id: "E-10 sub(5,2)", program: SUB(C(5), C(2)), inputs: {},
    why: "the canonical subtraction. It emits PRED applied to two Church numerals and the interaction " +
         "net computes 3 over 96 frames — it does NOT emit church(3), which is the difference between " +
         "a compiler and a calculator and the thing E-10c measures directly" },
  { id: "E-11 sub(2,0)", program: SUB(C(2), C(0)), inputs: {},
    why: "subtracting zero. The subtrahend is the numeral APPLIED, so this is the case where the " +
         "applied numeral is church(0) — PRED is handed to a numeral that never uses it, which is the " +
         "one shape in the family where the affine DROP inside the Church numeral does the work" },
  { id: "E-12 sub(2,2)", program: SUB(C(2), C(2)), inputs: {},
    why: "the boundary. a >= b holds with no slack, so it emits, and the answer is the numeral zero — " +
         "the one output shape that is NOT distinguishable from a saturated underflow by its value " +
         "alone, which is exactly why the refusal cannot be a check on the RESULT" },
  { id: "E-13 sub(input x, input y)", program: SUB(IN("x"), IN("y")), inputs: { x: 5, y: 2 },
    why: "ports under a non-commutative operator. Its template holds sub(port x, port y) with NO " +
         "underflow fact in it at all; the fact arrives with the invocation. This is the fixture that " +
         "makes `lower-negative` impossible to write and the refusal necessarily post-instantiation" },
  { id: "E-14 (7-2)-1", program: SUB(SUB(C(7), C(2)), C(1)), inputs: {},
    why: "left-associated nesting, paired with E-15. Together they show the template shape is " +
         "SEMANTIC: same three operands, same operator, different tree, different answer — 4 against " +
         "6 — so an emitter that flattened or reassociated would be caught by the outcome" },
  { id: "E-15 7-(2-1)", program: SUB(C(7), SUB(C(2), C(1))), inputs: {},
    why: "right-associated, the other half of the association pair. Its inner sub is the SUBTRAHEND, " +
         "so the inner term is the one applied — a structurally different emission from E-14 rather " +
         "than the same bytes in another order" },
  { id: "E-16 sub(2,3) REFUSES", program: SUB(C(2), C(3)), inputs: {}, emits: false,
    refusal: "emit-sub-underflow",
    why: "THE HEADLINE REFUSAL. The source evaluates this to -1 and is right to; the compiler has no " +
         "image for -1 and says so. Not a source refusal, not a saturation to 0, and not " +
         "source-refusal to target-refusal preservation: nothing refused upstream" },
  { id: "E-17 sub(2,5) REFUSES", program: SUB(C(2), C(5)), inputs: {}, emits: false,
    refusal: "emit-sub-underflow",
    why: "the operand-swapped partner of E-10 sub(5,2). One emits and the other refuses over the SAME " +
         "two operands, which is the negative operand-order witness E-8b's algebraic swap became once " +
         "the fragment stopped being commutative" },
  { id: "E-18 (2-3)+2 REFUSES", program: ADD(SUB(C(2), C(3)), C(2)), inputs: {}, emits: false,
    refusal: "emit-sub-underflow",
    why: "THE NESTED FALSIFIER, and the one that makes the check recursive rather than a root test. " +
         "Its source value is 1 and 1 is perfectly emittable, so a root-only check accepts it — and " +
         "raw Church monus then answers 2. Measured before the check was written: an inner underflow " +
         "leaves NO trace in the outcome" },
  { id: "E-19 sub(input x, input y) UNDERFLOWS", program: SUB(IN("x"), IN("y")), inputs: { x: 2, y: 5 },
    emits: false, refusal: "emit-sub-underflow",
    why: "the same TEMPLATE as E-13 and the other INVOCATION. One closed template emits and the other " +
         "refuses from one lowering — which is what it means for the refusal to belong to emission " +
         "rather than to the program, and it is not derivable from the program alone" },
  /* ── B8.2. THE MULTIPLICATION FIXTURES ───────────────────────────────
     One of them is the round: mul(4,3) is 12, which is the first value the
     SIGNATURE decoder could not read. Its presence is what makes B8.1 a
     necessity rather than a widening done in advance. */
  { id: "E-20 mul(4,3)", program: MUL(C(4), C(3)), inputs: {},
    why: "THE FIXTURE THAT PROVES B8.1 WAS NECESSARY. 4*3 is 12; Church 12's canonical signature is " +
         "82 characters, over §5's 80-character bound, so it is replaced by its own hash and the " +
         "signature decoder refused it while the runtime had the normal form all along. It decodes " +
         "here because the decoder reads the OBJECT" },
  { id: "E-21 mul(0,3)", program: MUL(C(0), C(3)), inputs: {},
    why: "the annihilating operand. MUL is λm.λn.λf.(m (n f)) and m is church(0), so the whole (n f) " +
         "is dropped — the one shape in the multiplication family that exercises the affine drop " +
         "rather than a duplication" },
  { id: "E-22 mul(3,7)", program: MUL(C(3), C(7)), inputs: {},
    why: "21, well past both the old ceiling and E-20. A single fixture just over a boundary can be " +
         "a coincidence about that boundary; a second one far past it cannot" },
  { id: "E-23 (2+3)*4", program: MUL(ADD(C(2), C(3)), C(4)), inputs: {},
    why: "a multiplication whose operand is an addition — 20, and the first fixture in the family " +
         "where two different combinators nest and their label allocations must not collide" },
  { id: "E-24 mul(2, 2-3) REFUSES", program: MUL(C(2), SUB(C(2), C(3))), inputs: {}, emits: false,
    refusal: "emit-sub-underflow",
    why: "the representability walk is recursive THROUGH a mul. Its source value is -2 and its inner " +
         "sub underflows; a domain rule added per-operator without recursion would have accepted a " +
         "mul whose operand it never looked inside" },
];
/* DECLARED, then DERIVED. Every case below counts against one of these two
   populations by name; none filters `r.ok` and then reports the size of what
   survived, which is how a battery comes to say 9/9 about a family of 14. */
const EMITTING = FIXTURES.filter((f) => f.emits !== false);
const REFUSING = FIXTURES.filter((f) => f.emits === false);

/* ── build the records ───────────────────────────────────────────────────── */
/* THE STAGE IS RECORDED, NOT JUST THE OUTCOME. B7's refusing fixtures stop at
   emission, and a record that only said `ok:false` could not distinguish "the
   compiler declined to represent this" from "lowering fell over". Each record
   carries WHERE it stopped and under WHAT NAME, and E-0 checks that against the
   fixture's own declaration. */
const RECORDS = FIXTURES.map((f) => {
  const low = lower(f.program);
  if (!low.ok) return { ...f, ok: false, stage: "lower", reason: low.reason };
  const inst = instantiate(low.template, f.inputs);
  if (!inst.ok) return { ...f, ok: false, stage: "instantiate", reason: inst.reason, low };
  let bytes;
  try { bytes = emit(inst.closed_template); }
  catch (e) {
    return { ...f, ok: false, stage: "emit", reason: String(e.message).split(":")[0],
      detail: e.message, low, inst, closed: inst.closed_template };
  }
  const receipt = emissionReceipt(inst.closed_template_sem_id, kernelSemId(bytes));
  return { ...f, ok: true, stage: "emit", low, inst, bytes, receipt, closed: inst.closed_template };
});

{
  // DECLARED vs OBSERVED, both directions. A fixture declared `emits: false`
  // that emits is as much a failure as one declared to emit that does not —
  // and the first direction is the one a saturating emitter would trip.
  const wrong = RECORDS.filter((r) => (r.emits !== false) !== r.ok);
  const wrongName = REFUSING.map((f) => RECORDS.find((r) => r.id === f.id))
    .filter((r) => r.reason !== r.refusal);
  const lateStage = RECORDS.filter((r) => r.emits === false && r.stage !== "emit");
  R("E-0 every fixture reaches its DECLARED record",
    wrong.length === 0 && wrongName.length === 0 && lateStage.length === 0
      && EMITTING.length >= 9 && REFUSING.length >= 4,
    wrong.length === 0 && wrongName.length === 0 && lateStage.length === 0
      ? `${EMITTING.length} fixtures lowered, instantiated and emitted over the ` +
        `[${IMPLEMENTED_LOWERED_OPS.join(", ")}] fragment — the op list DERIVED from lowering.mjs, ` +
        `not restated here — and ${REFUSING.length} lowered and instantiated and were REFUSED AT ` +
        `EMISSION by name (${[...new Set(REFUSING.map((f) => f.refusal))].join(", ")}). ` +
        `${RECORDS.filter((r) => Object.keys(r.inputs).length).length} of the ${FIXTURES.length} ` +
        `close at least one port. EVERY REFUSAL IS AT THE EMISSION STAGE and none earlier: the ` +
        `program lowers, the template instantiates, and what has no image is the TERM — which is what ` +
        `makes this a codomain refusal rather than a source one, checked here rather than asserted`
      : `declared/observed mismatch: ${wrong.map((b) => `${b.id} declared ${b.emits === false ? "refuse" : "emit"} got ` +
          `${b.ok ? "emit" : b.reason}`).join("; ")}${wrongName.length ? `; wrong refusal name: ` +
          `${wrongName.map((b) => `${b.id} wanted ${b.refusal} got ${b.reason}`).join("; ")}` : ""}` +
          `${lateStage.length ? `; refused at the wrong stage: ${lateStage.map((b) => `${b.id}@${b.stage}`).join("; ")}` : ""}`);
}

/* ── 1. TWO DETERMINISMS, AND THEY BELONG TO DIFFERENT THINGS ───────────
   B6 checked "same closed template -> same bytes -> same target_term_sem_id"
   as one theorem. After B6.1's ontology they are two, owned by two different
   identities, and GPT ruled them apart:

       SEMANTIC RELATION DETERMINISM      same closed_template_sem_id
                                          -> same target_term_sem_id
                                          belongs to EMISSION_SEM_ID

       CANONICAL BYTE REPRODUCIBILITY     same closed template + same emitter
                                          PROFILE + same emitter ARTIFACT
                                          -> same exact bytes
                                          belongs to CANONICAL_EMITTER_PROFILE_ID
                                          and CANONICAL_EMITTER_ARTIFACT_ID

   Both are worth testing. What must not happen is byte reproducibility
   re-cutting the semantic relation, which is exactly what B6.2 found and
   fixed.

   THE ARTIFACT TERM IS B6.3's CORRECTION, and it was falsified rather than
   reasoned into place. B6.2 wrote this theorem with two terms, and GPT changed
   the binder spelling inside the add combinator from {f0,f1} to {q0,q1}: the
   bytes differed on 6 of 9 fixtures while CANONICAL_EMITTER_PROFILE_ID — the
   theorem's entire stated precondition — stood still. A profile is
   CONFIGURATION, and configuration does not bind an implementation that
   declines to read it. Those two names are knobs now; the implementation as a
   whole never can be, so it gets an identity instead. */
{
  const rows = RECORDS.filter((r) => r.ok).map((r) => {
    const again = instantiate(lower(r.program).template, r.inputs);
    return {
      id: r.id,
      sameClosed: again.ok && again.closed_template_sem_id === r.receipt.closed_template_sem_id,
      sameId: again.ok && kernelSemId(emit(again.closed_template)) === r.receipt.target_term_sem_id,
      sameBytes: again.ok && emit(again.closed_template) === r.bytes,
    };
  });
  R("E-1a SEMANTIC relation determinism",
    rows.length === EMITTING.length && rows.every((x) => x.sameClosed && x.sameId),
    `all ${rows.length} fixtures rebuilt from (program, inputs) reach the same closed template and ` +
    `the same kernel-minted target_term_sem_id. THIS is the claim EMISSION_SEM_ID ` +
    `(${EMISSION_SEM_ID.slice(0, 14)}…) makes, and it says nothing about bytes`);
  R("E-1b CANONICAL byte reproducibility",
    rows.every((x) => x.sameBytes),
    `and under the same emitter PROFILE (${CANONICAL_EMITTER_PROFILE_ID.slice(0, 14)}…, ` +
    `label_counter_start ${CANONICAL_EMITTER_PROFILE.label_counter_start}, label_alloc_order ` +
    `${CANONICAL_EMITTER_PROFILE.label_alloc_order}) AND the same emitter ARTIFACT ` +
    `(${CANONICAL_EMITTER_ARTIFACT_ID.slice(0, 14)}…) the emitted BYTES are identical too on ` +
    `${rows.filter((x) => x.sameBytes).length}/${rows.length}. THREE TERMS, NOT TWO — B6.3, and the ` +
    `third was falsified into existence: with the theorem scoped to template+profile alone, changing ` +
    `{f0,f1} to {q0,q1} inside the add combinator moved the bytes on 6/9 while the profile id stood ` +
    `still, so the stated precondition could hold across a change to the very thing it bounded. A ` +
    `profile is CONFIGURATION and configuration does not bind an implementation that declines to read ` +
    `it. Separate case, separate owners: neither id is cited by anything semantic and E-2c/E-2d prove ` +
    `both directions`);
}

/* ── 2. THE RECEIPT VERIFIES BY RECONSTRUCTION ────────────────────────────
   The claim of this battery. Not "the emitter agrees with itself": the
   verifier rebuilds the closed template, re-emits, and canonicalises with an
   oracle it was HANDED. */
{
  const rows = RECORDS.filter((r) => r.ok).map((r) => ({
    id: r.id,
    v: verify(r.closed, r.receipt),
    direct: verifyEmissionReceiptAgainst(r.closed, r.receipt, kernelSemId),
    relationId: r.receipt.emission_sem_id === EMISSION_SEM_ID,
    complete: EMISSION_RECEIPT_FIELDS.every((f) => r.receipt[f] !== undefined),
  }));
  const okAll = rows.every((x) => x.v.ok === true && x.direct.ok === true && x.relationId && x.complete);
  R("E-2 every receipt verifies by independent reconstruction",
    rows.length === EMITTING.length && okAll,
    `${rows.length}/${rows.length} verified through makeEmissionVerifier({canonicaliseTarget}) AND through ` +
    `the ` +
    `direct entry point, with all ${EMISSION_RECEIPT_FIELDS.length} declared fields present. ` +
    `emission_sem_id is ${EMISSION_SEM_ID.slice(0, 14)}… on EVERY fixture — the relation's identity ` +
    `and not the invocation's. A per-fixture emission id would make each call a different relation, ` +
    `which is round 27's instantiation-identity finding one relation over`);
}

/* ── 2b. THE DUAL PROPERTY: THE ID MUST STAND STILL, TOO ─────────────────
   B1.1 taught this tree that a semantic id must move when its semantics move.
   The other half is the one B6.1 stated in prose and did not project: it must
   STAY PUT when only a representative choice changes. GPT reproduced the
   violation and it was inverted in both directions at once —

       edit the PROSE describing the label counter -> EMISSION_SEM_ID MOVED,
       while bytes and target terms were untouched;
       edit the ACTUAL counter inside emit()       -> bytes changed on 7 of 9
       fixtures and EMISSION_SEM_ID stood still.

   The id was bound to a DESCRIPTION of the policy rather than to the policy.
   B6.2 splits them: CANONICAL_EMITTER_PROFILE is INTERPRETED — emit() reads
   label_counter_start from it — so behaviour and identity cannot drift, and no
   semantic id hashes it. Asserted here in the direction that can regress. */
const SEMANTIC_IDS = {
  EMISSION_SEM_ID,
  TARGET_EXECUTABLE_ENCODING_SEM_ID,
  TARGET_TEMPLATE_ENCODING_SEM_ID,
  LOWERING_SEM_ID,
  INSTANTIATION_SEM_ID,
};
{
  // The semantic ids may not BE the serialization identities — the structural
  // form of "must stay put", checkable without mutating the module.
  const separate = !Object.values(SEMANTIC_IDS).includes(CANONICAL_EMITTER_PROFILE_ID)
    && !Object.values(SEMANTIC_IDS).includes(CANONICAL_EMITTER_ARTIFACT_ID)
    && CANONICAL_EMITTER_PROFILE_ID.startsWith("cemp-")
    && CANONICAL_EMITTER_ARTIFACT_ID.startsWith("cema-");
  // and the profile is INTERPRETED rather than described: emit() must actually
  // start where the profile says. Measured by reading the first label the
  // emitter produces on a dup-bearing fixture.
  const dupBearing = RECORDS.find((r) => r.ok && /&(\d+)/.test(r.bytes));
  const firstLabel = dupBearing ? Number(/&(\d+)/.exec(dupBearing.bytes)[1]) : null;
  const interpreted = firstLabel === CANONICAL_EMITTER_PROFILE.label_counter_start;
  // B6.3: EVERY field, not one. The structural form of "no prose is hashed
  // here" — a hashed value is a number, a short identifier, or a list of them,
  // and prose needs a space. Same shape as TARGET_TEMPLATE_ENCODING's
  // no_names_no_labels: not a promise to keep sentences out, but no field they
  // could occupy. B6.2's profile had one knob and five sentences and hashed
  // all six, so rewording `determinism` moved the id while nothing else moved.
  const ID = /^[A-Za-z0-9_.-]{1,48}$/;
  const flat = (v) => Array.isArray(v) ? v.flatMap(flat)
    : (v && typeof v === "object") ? Object.values(v).flatMap(flat) : [v];
  const values = flat(CANONICAL_EMITTER_PROFILE);
  const prose = values.filter((v) => typeof v === "string" && !ID.test(v));
  const nonValue = values.filter((v) => typeof v !== "string" && !Number.isInteger(v));
  R("E-2b the profile is SEPARATE, INTERPRETED, and PROSE-FREE",
    separate && interpreted && prose.length === 0 && nonValue.length === 0 && values.length >= 12,
    `CANONICAL_EMITTER_PROFILE_ID ${CANONICAL_EMITTER_PROFILE_ID.slice(0, 14)}… and ` +
    `CANONICAL_EMITTER_ARTIFACT_ID ${CANONICAL_EMITTER_ARTIFACT_ID.slice(0, 14)}… are distinct from ` +
    `all ${Object.keys(SEMANTIC_IDS).length} semantic ids; the profile is INTERPRETED rather than ` +
    `described — the first dup label the emitter produces is &${firstLabel} and the profile declares ` +
    `${CANONICAL_EMITTER_PROFILE.label_counter_start}; and all ${values.length} hashed values are ` +
    `integers or bare identifiers with ${prose.length} containing prose. THE LAST CLAUSE IS B6.3 AND ` +
    `IT IS THE ONE THAT REGRESSES: B6.2 shipped ONE interpreted knob beside FIVE English sentences ` +
    `and hashed all six, so rewording binder_spelling moved this id while changing the actual binder ` +
    `spelling did not — the same defect B6.2 was created to fix, one object in. Prose now has no ` +
    `field it could occupy; it is intact and unhashed in CANONICAL_EMITTER_PROFILE_NOTES`);
}

/* ── 2c. A KNOB MOVES THE BYTES AND THE PROFILE ID AND NOTHING SEMANTIC ───
   B6.2 asserted this in a LEDGER PARAGRAPH. It could not run it: the profile
   was a module-level frozen constant, so the only way to vary it was to edit
   the file and re-import — which is a measurement a reader has to take on
   trust, and this tree has already paid for three instruments that reported
   without measuring. emit() takes the profile as a parameter now, so both
   knobs are exercised here, live, against the canonical fixtures. */
{
  const ALT = [
    { name: "label_counter_start 0 -> 7000",
      profile: { ...CANONICAL_EMITTER_PROFILE, label_counter_start: 7000 } },
    { name: "label_alloc_order operands-then-node -> node-then-operands",
      profile: { ...CANONICAL_EMITTER_PROFILE, label_alloc_order: "node-then-operands" } },
    { name: "binder_names.add_dup {f0,f1} -> {q0,q1}",
      profile: { ...CANONICAL_EMITTER_PROFILE,
        binder_names: { ...CANONICAL_EMITTER_PROFILE.binder_names, add_dup: ["q0", "q1"] } } },
  ];
  const rows = ALT.map((alt) => {
    const rs = RECORDS.filter((r) => r.ok);
    const out = rs.map((r) => ({ bytes: emit(r.closed, alt.profile), was: r.bytes,
      id: kernelSemId(emit(r.closed, alt.profile)), wasId: r.receipt.target_term_sem_id }));
    return {
      name: alt.name,
      idMoved: emitterProfileId(alt.profile) !== CANONICAL_EMITTER_PROFILE_ID,
      bytesMoved: out.filter((x) => x.bytes !== x.was).length,
      termsMoved: out.filter((x) => x.id !== x.wasId).length,
      total: out.length,
    };
  });
  // and the semantic ids are untouched by construction: none of them is a
  // function of the profile, which E-2b checks structurally and this confirms
  // by running the emitter under three profiles without recomputing one.
  const ok2c = rows.every((x) => x.idMoved && x.bytesMoved > 0 && x.termsMoved === 0);
  MEASURED.knobs = rows.length;
  R("E-2c a KNOB moves bytes and the profile id, and NO semantic id",
    ok2c && rows.length === 3,
    `${rows.length} knobs varied live against all ${EMITTING.length} emitting fixtures: ` +
    `${rows.map((x) => `${x.name} — bytes differ ${x.bytesMoved}/${x.total}, profile id ` +
      `${x.idMoved ? "MOVED" : "STOOD STILL"}, target_term_sem_id moved ${x.termsMoved}/${x.total}`)
      .join("; ")}. Every one of the three is a field B6.2 either hashed as PROSE or did not hash at ` +
    `all; each now changes bytes without touching meaning, which is the entire claim the profile ` +
    `makes. RUN rather than narrated: B6.2 stated the counter result in the ledger because a frozen ` +
    `module constant cannot be varied by the battery meant to falsify it`);
}

/* ── 2d. THE IMPLEMENTATION MOVES THE ARTIFACT ID AND NOTHING ELSE ────────
   GPT's B6.3 falsifier, kept as a standing case. The profile cannot cover the
   emitter, only configure it, and the honest response to that is a third
   identity rather than a wider profile. */
{
  const bundle = emitterArtifactBundle(EMITTER_ARTIFACT_MEMBERS);
  // MUTATE EACH MEMBER IN TURN. B6.3 perturbed emit() alone and concluded the
  // bundle was covered; the member it had never perturbed was the one that was
  // missing. Each member's source is now separately shown to move the id.
  const perMember = EMITTER_ARTIFACT_MEMBERS.map(([name, f]) => {
    const mutated = EMITTER_ARTIFACT_MEMBERS.map(([n2, g]) =>
      n2 === name ? [n2, { toString: () => g.toString() + " /* perturbed */" }] : [n2, g]);
    return { name, moves: emitterArtifactId(emitterArtifactBundle(mutated)) !== CANONICAL_EMITTER_ARTIFACT_ID };
  });
  // AND A RENAME MOVES IT TOO: the name is hashed beside the body, so two
  // different arrangements of the same code are two artifacts.
  const renamed = emitterArtifactId(emitterArtifactBundle(
    EMITTER_ARTIFACT_MEMBERS.map(([n2, g], i) => i === 0 ? ["emitCanonical", g] : [n2, g])))
    !== CANONICAL_EMITTER_ARTIFACT_ID;
  const boundToBundle = CANONICAL_EMITTER_ARTIFACT_ID === emitterArtifactId(bundle)
    && emitterArtifactId(emit.toString()) !== CANONICAL_EMITTER_ARTIFACT_ID;
  const citedByNothing = !Object.values(SEMANTIC_IDS)
    .some((id) => id.includes(CANONICAL_EMITTER_ARTIFACT_ID.slice(5, 21)));
  MEASURED.artifact_members = EMITTER_ARTIFACT_MEMBERS.length;
  R("E-2d the IMPLEMENTATION moves the artifact id, and NO semantic id",
    perMember.every((x) => x.moves) && renamed && boundToBundle && citedByNothing
      && EMITTER_ARTIFACT_MEMBERS.length >= 4,
    `perturbing the source of EACH of the ${EMITTER_ARTIFACT_MEMBERS.length} bundled members ` +
    `separately — ${perMember.map((x) => x.name).join(", ")} — moves CANONICAL_EMITTER_ARTIFACT_ID ` +
    `(${CANONICAL_EMITTER_ARTIFACT_ID.slice(0, 14)}…) on ${perMember.filter((x) => x.moves).length}` +
    `/${perMember.length}, and so does renaming one, while all ` +
    `${Object.keys(SEMANTIC_IDS).length} semantic ids are functions of records the emitter's source ` +
    `does not appear in. PER-MEMBER IS B6.3.1 AND IT IS THE POINT: B6.3 perturbed emit() alone, ` +
    `concluded the bundle was covered, and the member it never perturbed was the one that was ` +
    `MISSING. IT IS PROVENANCE AND IT OVERMOVES ON PURPOSE: a comment moves it, which would be ` +
    `B1.1's defect in a SEMANTIC id and is exactly right for an artifact whose claim is "these exact ` +
    `implementation bytes". Nothing semantic cites it and no receipt carries it — it names what ` +
    `E-1b's byte claim is RELATIVE TO, rather than letting the claim read as absolute`);
}

/* ── 2e. THE BUNDLE IS COMPLETE, BY DERIVATION RATHER THAN BY CARE ────────
   GPT's B6.3 falsifier, and the instrument that makes it non-recurring.

   B6.3 hashed emit, church and ADD_COMBINATOR and missed the module-level enum
   table emit() reads. One boolean flipped in that table, profile untouched:
   bytes moved on 5 of 9 fixtures while the closed template, the profile id AND
   the artifact id all stood still. E-1b's three stated preconditions all held
   and its conclusion was false — a theorem refuted by a change to something it
   claimed to bound.

   THE RULE: IF CHANGING A PIECE OF IMPLEMENTATION CAN CHANGE EMITTED BYTES
   WHILE THE TEMPLATE AND PROFILE STAY FIXED, THAT PIECE BELONGS TO THE ARTIFACT
   IDENTITY. Fixing the one table would satisfy the falsifier and leave the NEXT
   helper exactly as exposed, which is why this reads the module's source and
   derives the answer: every module-level binding a bundled member REFERENCES
   must be bundled, be the profile, or be declared byte-inert. A hand-kept list
   is what artifact_versions was when three of its six entries had no reader. */
{
  const modSrc = readFileSync(new URL("./lowering.mjs", import.meta.url), "utf8");
  // module-level bindings, DERIVED from the file rather than enumerated here
  const moduleNames = new Set([...modSrc.matchAll(
    /^(?:export\s+)?(?:const|let|function)\s+([A-Za-z_$][\w$]*)/gm)].map((m) => m[1]));
  // comments and quoted strings are not references; TEMPLATE literals are kept,
  // because `${ADD_COMBINATOR(L, B)}` is exactly the reference being looked for
  const strip = (s) => s
    .replace(/\/\*[\s\S]*?\*\//g, " ").replace(/\/\/[^\n]*/g, " ")
    .replace(/"(?:[^"\\]|\\.)*"/g, '""').replace(/'(?:[^'\\]|\\.)*'/g, "''")
    .replace(/\.\s*[A-Za-z_$][\w$]*/g, ".");           // property access is not a free name
  const bundled = new Set(EMITTER_ARTIFACT_MEMBERS.map(([n]) => n));
  const inert = new Set(Object.keys(EMITTER_ARTIFACT_INERT));
  // B7.1r: a FOURTH category, because EMISSION_RULES is referenced by emit()
  // and representableValue(), is NOT byte-inert, and must not be bundled — its
  // content is covered by a SEMANTIC id, which is strictly stronger than this
  // provenance one. Each entry must NAME the covering id and that id must
  // actually exist on the module; an allowlist of unverified strings is how the
  // enum table got in at B6.3.
  const semantic = new Set(Object.keys(EMITTER_ARTIFACT_SEMANTIC));
  const coveredNamed = [...semantic].every((k) => {
    const m2 = /covered_by ([A-Z_]+)/.exec(EMITTER_ARTIFACT_SEMANTIC[k] ?? "");
    return m2 !== null && LOWERING_EXPORTS[m2[1]] !== undefined;
  });
  const refs = new Map();
  for (const [name, f] of EMITTER_ARTIFACT_MEMBERS) {
    const body = strip(f.toString());
    for (const m of moduleNames) {
      if (m === name) continue;
      if (new RegExp(`(?<![\\w$])${m}(?![\\w$])`).test(body))
        refs.set(m, (refs.get(m) ?? []).concat(name));
    }
  }
  const escapes = [...refs.keys()].filter((m) => !bundled.has(m) && !inert.has(m) && !semantic.has(m));
  // and the check must not be vacuous: at least one bundled member must
  // reference another, or an empty reference set would pass trivially.
  const nonVacuous = [...refs.keys()].some((m) => bundled.has(m));
  const inertDeclared = [...inert].every((k) => (EMITTER_ARTIFACT_INERT[k] ?? "").length > 40);
  MEASURED.closure_refs = refs.size;
  R("E-2e the artifact bundle is the WHOLE byte-producing closure",
    escapes.length === 0 && nonVacuous && inertDeclared && coveredNamed && semantic.size >= 1
      && moduleNames.size > 20,
    `${moduleNames.size} module-level bindings derived from lowering.mjs's own source; the ` +
    `${EMITTER_ARTIFACT_MEMBERS.length} bundled members reference ${refs.size} of them ` +
    `(${[...refs.entries()].map(([m, by]) => `${m}←${by.join("+")}`).join(", ")}) and ` +
    `${escapes.length} escape the bundle. B6.3 SHIPPED ONE THAT DID: a module-level enum table ` +
    `emit() read, outside the id, so flipping one boolean in it moved the bytes on 5/9 fixtures ` +
    `while template, profile id and artifact id all stood still — E-1b's three preconditions holding ` +
    `across a change to its own conclusion. Repairing that one table would have left the NEXT helper ` +
    `exactly as exposed, so membership is DERIVED here rather than maintained: bundled, the profile, ` +
    `or declared byte-inert with a reason. A hand-kept list is what artifact_versions was when three ` +
    `of its six entries had no reader. B7.1r ADDS A FOURTH ANSWER: ${semantic.size} binding(s) — ` +
    `${[...semantic].join(", ")} — are covered by a SEMANTIC identity instead, which is strictly ` +
    `stronger than this provenance one, and each names the id that covers it (verified present on ` +
    `the module: ${coveredNamed}). Calling EMISSION_RULES byte-inert would have been false and ` +
    `bundling it would have made a reworded rule a new emitter`);
}

/* ── 3. TWO PROGRAMS, ONE CLOSED TEMPLATE — MEASURED, NOT ASSUMED ────────
   The first draft of this case required all eight closed templates to be
   distinct and FAILED, which is how the family's most useful property was
   found rather than designed: `add(const 2, const 3)` and
   `add(input x, input y)` closed with {x:2, y:3} are THE SAME CLOSED TEMPLATE,
   ctmpl-d0105d4f…, and therefore the same emission.

   That is exactly right and it is worth an assertion of its own. Instantiation
   has already erased the difference between a literal and a port bound to that
   literal, so by the time emission runs there is nothing left to distinguish
   them — which is what it means for emission's domain to be the CLOSED
   template rather than the program. An emitter that produced different bytes
   for those two would be reading something it is not entitled to see.

   So what is checked is the implication, in the direction that can be wrong:
   equal closed templates must reach equal target terms, and DIFFERENT closed
   templates must not collide. */
{
  const rs = RECORDS.filter((r) => r.ok);
  const byClosed = new Map();
  for (const r of rs) {
    const k = r.receipt.closed_template_sem_id;
    byClosed.set(k, (byClosed.get(k) ?? []).concat(r));
  }
  // equal domain -> equal codomain
  const funcOk = [...byClosed.values()].every((group) =>
    new Set(group.map((r) => r.receipt.target_term_sem_id)).size === 1);
  // different domain -> different codomain
  const targets = new Map();
  for (const [k, group] of byClosed) targets.set(group[0].receipt.target_term_sem_id,
    (targets.get(group[0].receipt.target_term_sem_id) ?? []).concat(k));
  const collisions = [...targets.values()].filter((ks) => new Set(ks).size > 1);
  const shared = [...byClosed.values()].filter((g) => g.length > 1);
  MEASURED.distinct_closed = byClosed.size;
  MEASURED.shared_groups = shared.length;
  MEASURED.shared_named = shared.map((g) => g.map((r) => r.id.split(" ")[0]).join("==")).join(", ");
  R("E-3 emission is a function OF THE CLOSED TEMPLATE",
    funcOk && collisions.length === 0 && shared.length >= 1,
    `${byClosed.size} distinct closed templates over ${rs.length} fixtures, ` +
    `${targets.size} distinct target terms, ${collisions.length} collisions between different domain ` +
    `values. ${shared.length} closed template(s) are reached by more than one fixture — ` +
    `${shared.map((g) => g.map((r) => r.id).join(" == ")).join("; ")} — and they emit IDENTICALLY. ` +
    `That is the property, not a coincidence: instantiation has already erased the difference between ` +
    `a literal and a port bound to that literal, so an emitter producing different bytes for those two ` +
    `would be reading something it is not entitled to see. This case required all eight to be ` +
    `DISTINCT in its first draft and failed, which is how the family's most useful property was ` +
    `measured rather than designed`);
}

/* ── 4. TWO ADVERSARIES, AND THEY HAVE DIFFERENT JOBS ───────────────────
   B6 used ONE helper for both cases and GPT ruled them apart, correctly: they
   are proving different things and only one of them is constrained.

       driftEmit   E-F1's adversary. Its theorem is "same closed template, same
                   relation id, a changed claim about the target term, therefore
                   REFUSE". It does NOT need to preserve meaning, so it may be
                   any quotient-visible structural change — and because it is
                   unconstrained it applies to EVERY fixture.

       equivEmit   E-8's adversary. Its theorem is "different target_term_sem_id,
                   SAME meaning", so it must be a real semantic equivalence.
                   That is a much stronger requirement and it is why this one
                   is only applicable where the fragment supplies an
                   equivalence.

   Fusing them made the canonical-drift falsifier depend on whatever semantic
   equivalence happened to be available — so when `sub` arrives and operand
   reordering stops being meaning-preserving, E-F1 would have lost its adversary
   for a reason that has nothing to do with what E-F1 proves.

   THE OBVIOUS DRIFT MUTATION DOES NOT WORK, AND FINDING THAT OUT IS A RESULT.
   The first draft shifted the emitter's dup labels (&1001 -> &1501) — the
   textbook "allocation changed" edit — and target_term_sem_id did not move on
   any fixture. It cannot: the canonical signature is BYTE-EQUIVARIANT under
   alpha-renaming and label permutation, by asserted law (L-BYTES-1). An emitter
   that only renames has not produced a different term, which is now recorded in
   TARGET_ENCODING.label_semantics rather than contradicted by it. */
const driftEmit = (r) => {
  // ANY quotient-visible structural change. Bumping the first church numeral is
  // one, it is meaning-CHANGING (which is allowed here), and every fixture in
  // the fragment contains at least one — so this adversary needs no
  // applicability caveat and E-F1 covers the whole family.
  let done = false;
  const bump = (n) => {
    if (done || n === null || typeof n !== "object") return n;
    if (n.t === "church") { done = true; return { ...n, n: n.n + 1 }; }
    const out = { ...n };
    for (const k of ["a", "b"]) if (k in out) out[k] = bump(out[k]);
    return out;
  };
  const mutated = bump(r.closed);
  return done ? emit(mutated) : null;
};
/* ── E-8's ADVERSARY, GENERALISED AT B6.3.1 ──────────────────────────────
   GPT's answer to a question B6.1 deferred and B6.3's brief posed as a choice
   between two bad options — make E-8 add-only, or invent an equivalence for
   `sub` before `sub` exists. It is neither.

   E-8's theorem is that target_term_sem_id identifies THIS EMITTER'S OUTPUT
   rather than the term's MEANING. That needs a meaning-preserving structural
   alternate; it does NOT need an algebraic law of any source operator. A beta
   redex around the whole term supplies one generically:

       T   ->   (λz.z T)

   Measured over the current family before adopting it: DIFFERENT
   target_term_sem_id on 9/9, SAME decoded outcome on 9/9 — where the operand
   swap is applicable to the 6 add-bearing fixtures only, and is meaning-
   preserving solely because addition commutes. The generic witness is
   independent of that, survives `sub` and `mul` by construction, and covers
   const and input fixtures the swap could never reach.

   THE BINDER IS CHOSEN AGAINST THE PROFILE, not hard-coded: binder_names is a
   knob now, so a wrapper spelled `z` would capture if a profile ever named a
   binder `z`. Picking the first candidate the profile does not use keeps the
   adversary correct under E-2c's own mutations — the alternative is an
   adversary that silently stops being alpha-safe when a knob moves. */
const betaEmit = (r) => {
  const used = new Set(Object.values(CANONICAL_EMITTER_PROFILE.binder_names).flat());
  const z = ["z", "w", "u", "zz"].find((c) => !used.has(c));
  return z ? `(λ${z}.${z} ${r.bytes})` : null;
};

/* E-8b's adversary: a real ALGEBRAIC equivalence, applicable only where the
   fragment supplies one. Kept as an add-specific measurement after B6.3.1 moved
   the architecture-level theorem onto betaEmit — a fact worth having, no longer
   a fact the proof depends on. */
const equivEmit = (r) => {
  const c = r.closed;
  // the CLOSED TEMPLATE's own vocabulary — {t:"add", a, b} over {t:"church", n} —
  // read from the structure rather than assumed from the source AST's, which is
  // what the first draft did (it looked for `op` and found none, so every
  // fixture reported "nothing to swap" and the case passed vacuously on an
  // empty set until the >= 4 floor caught it).
  if (c?.t !== "add") return null;
  if (JSON.stringify(c.a) === JSON.stringify(c.b)) return null;   // a swap that changes nothing
  return emit({ ...c, a: c.b, b: c.a });
};
{
  const rows = RECORDS.filter((r) => r.ok).map((r) => {
    const bytes = driftEmit(r);
    if (bytes === null) return { id: r.id, applicable: false };
    const forgedId = kernelSemId(bytes);
    const moved = forgedId !== r.receipt.target_term_sem_id;
    const v = verify(r.closed, { ...r.receipt, target_term_sem_id: forgedId });
    return { id: r.id, applicable: true, moved, refused: v.ok === false, reason: v.reason, bytes };
  });
  const app = rows.filter((x) => x.applicable);
  MEASURED.drift_applicable = app.length;
  MEASURED.drift_refused = app.filter((x) => x.moved && x.refused).length;
  R("E-F1 an emitter whose STRUCTURE moved is refused",
    app.length === EMITTING.length && app.every((x) => x.moved && x.refused),
    `${app.length}/${rows.length} fixtures — the WHOLE family, because this adversary is not required ` +
    `to preserve meaning and therefore needs no applicability caveat. On every one the drifted ` +
    `emission produces a DIFFERENT target_term_sem_id and the receipt carrying it is refused ` +
    `(${[...new Set(app.map((x) => x.reason))].join(", ")}), while closed_template_sem_id and ` +
    `emission_sem_id are untouched — both declared ids agreeing is precisely the state in which a ` +
    `verifier that trusted them would accept. SEPARATED FROM E-8's ADVERSARY at B6.1 on GPT's ruling: ` +
    `fusing them made this falsifier depend on whatever semantic equivalence happened to exist, so ` +
    `when sub arrives and reordering stops preserving meaning, E-F1 would lose its adversary for a ` +
    `reason having nothing to do with what E-F1 proves. A LABEL-SHIFT MUTATION WAS TRIED ` +
    `FIRST AND MOVED NOTHING on any fixture: the canonicaliser is byte-equivariant under alpha and ` +
    `label ` +
    `permutation by asserted law, so "the emitter's allocation changed" is invisible at this identity ` +
    `and the adversary has to be structural`);
}

/* ── 5. E-F2: THE RECEIPT MAY NOT BE VERIFIED AGAINST ANOTHER TEMPLATE ────
   The complement of E-F1: an honest receipt, checked against the wrong domain
   value. It must fail on the domain rather than on the codomain, or the
   verifier is only comparing hashes it was handed. */
{
  const rs = RECORDS.filter((r) => r.ok);
  const rows = rs.map((r, i) => {
    const other = rs[(i + 1) % rs.length];
    const v = verify(other.closed, r.receipt);
    return { id: r.id, against: other.id, refused: v.ok === false, reason: v.reason };
  });
  R("E-F2 a receipt does not verify against another closed template",
    rows.every((x) => x.refused),
    `${rows.filter((x) => x.refused).length}/${rows.length} refused when each fixture's honest receipt ` +
    `is checked against its neighbour's closed template ` +
    `(${[...new Set(rows.map((x) => x.reason))].join(", ")}). Without this, a verifier that merely ` +
    `re-emitted and compared to the number in the receipt would pass every honest receipt and every ` +
    `mismatched pairing alike`);
}

/* ── 6. E-F3: THE RELATION ID IS COMMITTED ───────────────────────────────
   A receipt naming a different emission relation must not verify, even when
   its bytes are honest. The relation is part of the claim. */
{
  const r = RECORDS.find((x) => x.ok);
  const wrongRel = { ...r.receipt, emission_sem_id: "esem-" + "0".repeat(64) };
  const v = verify(r.closed, wrongRel);
  const missing = (() => {
    try { emissionReceipt(r.receipt.closed_template_sem_id, undefined); return "BUILT"; }
    catch (e) { return e.message; }
  })();
  R("E-F3 the relation id is part of the claim",
    v.ok === false && /emission-receipt-incomplete/.test(missing),
    `a receipt whose target_term_sem_id and closed_template_sem_id are both honest but which names a ` +
    `different emission relation is ${v.reason}; and a receipt built with a missing field is refused ` +
    `at construction (${missing}) rather than verifying with an undefined in it`);
}

/* ── 7. E-8: THE ALTERNATE EMITTER — DIFFERENT ID, SAME MEANING ─────────
   The property that must NOT be confused with E-F1, proved separately for
   exactly that reason. E-F1 says the canonical relation is pinned; this says
   the pin identifies a CHOICE rather than the meaning.

   GPT'S FORM OF THIS PROPERTY WAS "an alternate ALPHA-EQUIVALENT emitter
   produces a different target_term_sem_id", AND THAT IS FALSE HERE. Measured:
   an alpha-equivalent emitter produces the SAME id, on every fixture, because
   the canonical signature is byte-equivariant under alpha-renaming and label
   permutation by asserted law (L-BYTES-1). The id already quotients renaming,
   so renaming cannot be the witness.

   The honest witness is the same STRUCTURAL alternate E-F1 uses — operands
   emitted in the other order. It differs in id and agrees in meaning, which is
   the property GPT was after; only the mutation that exhibits it had to move
   one level up, from the names to the shape. */
{
  const outcomeOf = (bytes) => {
    const d = decodeBytes(bytes);
    return d.ok ? outcomeSemId(d.outcome) : `refused:${d.reason}`;
  };
  const measure = (alt) => RECORDS.filter((r) => r.ok).map((r) => {
    const bytes = alt(r);
    if (bytes === null) return { id: r.id, applicable: false };
    return { id: r.id, applicable: true,
      differs: kernelSemId(bytes) !== r.receipt.target_term_sem_id,
      same: outcomeOf(bytes) === outcomeOf(r.bytes) };
  });
  const beta = measure(betaEmit).filter((x) => x.applicable);
  // AND the alpha claim, measured rather than assumed in either direction
  const alphaSame = RECORDS.filter((r) => r.ok).every((r) =>
    kernelSemId(r.bytes.replace(/&(\d+)/g, (_, n) => "&" + (Number(n) + 7000))) === r.receipt.target_term_sem_id);
  MEASURED.beta_applicable = beta.length;
  MEASURED.beta_differs = beta.filter((x) => x.differs).length;
  MEASURED.beta_same_meaning = beta.filter((x) => x.same).length;
  MEASURED.alpha_identical = alphaSame ? EMITTING.length : -1;
  R("E-8 a GENERIC structural alternate differs in ID and agrees in MEANING",
    beta.length === EMITTING.length && beta.every((x) => x.differs && x.same) && alphaSame,
    `the beta wrapper T -> (λz.z T) applies to ALL ${beta.length} fixtures and produces a different ` +
    `target_term_sem_id on ${beta.filter((x) => x.differs).length}/${beta.length} AND the same ` +
    `decoded outcome identity on ${beta.filter((x) => x.same).length}/${beta.length}. These two facts ` +
    `look like a contradiction and are the point — E-F1 proves the CANONICAL relation is a ` +
    `commitment, this proves target_term_sem_id identifies THAT emitter's output rather than the ` +
    `term's meaning. Collapsing them yields either "a restructuring is a semantic change" or ` +
    `"emission may drift as long as the answer matches", and the second is how a compiler stops being ` +
    `reproducible quietly. GENERIC AT B6.3.1, AND THAT RESOLVES AN ITEM RATHER THAN DEFERRING IT: ` +
    `this theorem needs a MEANING-PRESERVING STRUCTURAL ALTERNATE and does not need an algebraic law ` +
    `of any source operator. Until B6.3.1 it rode on add's commutativity, so it covered 6 of 9 ` +
    `fixtures and was going to lose its adversary the day sub arrived — for a reason having nothing ` +
    `to do with what it proves. A beta redex is independent of the fragment's algebra, reaches the ` +
    `const and input fixtures the swap never could, and survives sub and mul by construction. ` +
    `SEPARATELY MEASURED, because the property was originally stated over ALPHA-equivalence: a ` +
    `relabelled emitter produces the IDENTICAL id on all ${EMITTING.length} emitting fixtures (${alphaSame}), ` +
    `so the id already quotients renaming and renaming cannot witness this at all`);

  const swap = measure(equivEmit).filter((x) => x.applicable);
  MEASURED.equiv_applicable = swap.length;
  MEASURED.equiv_differs = swap.filter((x) => x.differs).length;
  MEASURED.equiv_same_meaning = swap.filter((x) => x.same).length;
  R("E-8b the add-specific ALGEBRAIC alternate, kept as a measurement",
    swap.length >= 4 && swap.every((x) => x.differs && x.same),
    `operand reordering is applicable to ${swap.length}/${EMITTING.length} emitting fixtures — the add-bearing ` +
    `ones — and on each it differs in id and agrees in outcome. IT CARRIED E-8's ARCHITECTURE-LEVEL ` +
    `THEOREM UNTIL B6.3.1 AND NO LONGER DOES. It is meaning-preserving ONLY because addition ` +
    `commutes; sub(a,b) != sub(b,a), so the day the fragment widens this stops being an equivalence ` +
    `and becomes a falsifier for the OPPOSITE property — that operand order IS semantic. Kept ` +
    `because the fact is worth having and the applicability count is worth watching, demoted because ` +
    `a proof that depends on the algebra of whichever operators happen to exist is a proof with an ` +
    `expiry date`);
}

/* ── 2f. B7.1r: THE CODOMAIN ID MUST NOT MOVE WHEN THE MAP GROWS ─────────
   GPT's ruling on B7's one disagreement, and the case that makes it a
   measurement rather than a decomposition argument.

   B7 added `sub` and TARGET_EXECUTABLE_ENCODING_SEM_ID moved. B7's brief
   defended that: the executable encoding is what says how a construct becomes
   an interaction-net term, so a new construct must move it. THAT WAS THE WRONG
   DECOMPOSITION. B1.2.1's rule is

       relation identity = domain encoding + codomain encoding + THE MAP

   and `sub` added no executable constructor and no runtime rule — the B7.1
   measurement says so in as many words. It added a MACRO expanded into
   Var/Lam/App/Dup/Sup/Era. What moved xenc was that the MAP was still stored
   inside the codomain's identity: B1.2.1's OVER-BINDING defect, in the field
   B1.2.1 created to fix UNDER-binding.

   SO xenc HAS A QUESTION TO ANSWER, and this case is what makes it able to:

       a new compiler-library OPERATOR      ->  esem MOVES, xenc STANDS STILL
       a new executable CONSTRUCTOR or a
       change to the target language        ->  xenc MOVES

   An id that moves for both cannot distinguish them, which is exactly the
   state B7 shipped in. Both directions are run below against a SYNTHETIC `mul`
   rule, so the property is established BEFORE `mul` exists rather than
   discovered by it. */
{
  // PREFIX AND TAG ARE SEPARATE. The first draft folded them into one string
  // and hashed the prefix too, so every recomputation missed the live id and
  // the case reported "xenc MOVED" for a mutation that had not been applied —
  // a falsifier failing in the direction that flatters the round it is testing.
  const semId = (prefix, tag, o) => prefix + createHash("sha256")
    .update(tag + "|" + canonicalBytes(o)).digest("hex");
  const rulesId = (r) => semId("erul-", "TRVM-EMISSION-RULES-v1", r);
  const esemOf = (over) => semId("esem-", "TRVM-EMISSION-SEM-v1", { ...EMISSION_SEMANTICS, ...over });
  const xencOf = (e) => semId("xenc-", "TRVM-TARGET-EXECUTABLE-ENC-v1", e);
  // THE RECOMPUTATION MUST REPRODUCE THE LIVE IDS FIRST, or every comparison
  // below is against a number this case invented.
  const anchored = xencOf(TARGET_ENCODING) === TARGET_EXECUTABLE_ENCODING_SEM_ID
    && rulesId(EMISSION_RULES) === EMISSION_RULES_SEM_ID
    && esemOf({}) === EMISSION_SEM_ID;

  // 1. GROW THE MAP with an operator that DOES NOT EXIST YET. B7.1r used a
  //    synthetic `mul` here and B8.2 then added the real one — at which point
  //    the spread below would have been REPLACING an existing rule rather than
  //    adding one, and the case would have gone on passing while testing a
  //    weaker thing. The synthetic operator is always the NEXT one, and the
  //    assertion checks it is genuinely absent, so this cannot decay quietly.
  const FUTURE = "div";
  const grown = { ...EMISSION_RULES,
    node_rules: { ...EMISSION_RULES.node_rules,
      [FUTURE]: { kind: "combinator", binders: "mul", dup_binders: null, labels: 0,
                  shape: "λ{B0}.λ{B1}.λ{B2}.({B0} ({B1} {B2}))",
                  application: "(({COMB} {a}) {b})" } },
    domain: { ...EMISSION_RULES.domain,
      value_rules: { ...EMISSION_RULES.domain.value_rules, [FUTURE]: { operator: "/" } } } };
  const futureAbsent = EMISSION_RULES.node_rules[FUTURE] === undefined;
  const grownRules = rulesId(grown) !== EMISSION_RULES_SEM_ID;
  const grownEsem = esemOf({ rules_sem_id: rulesId(grown) }) !== EMISSION_SEM_ID;
  // xenc is a function of TARGET_ENCODING alone, so "the map grew" cannot reach
  // it — which is the claim, and `anchored` above is what makes the equality
  // below evidence rather than a tautology about an unchanged object.
  const grownXenc = xencOf(TARGET_ENCODING) === TARGET_EXECUTABLE_ENCODING_SEM_ID;

  // 2. CHANGE THE TARGET LANGUAGE: a new executable constructor. THIS must move
  //    xenc, or the id has simply stopped answering anything.
  const widened = { ...TARGET_ENCODING,
    constructors: [...TARGET_ENCODING.constructors, "Num"] };
  const widenedXenc = xencOf(widened) !== TARGET_EXECUTABLE_ENCODING_SEM_ID;
  // …and so must a change to the quotient, which is the other thing genuinely
  // true of an executable term rather than of the map.
  const requotiented = { ...TARGET_ENCODING, quotient: "alpha-renaming only" };
  const requotientedXenc = xencOf(requotiented) !== TARGET_EXECUTABLE_ENCODING_SEM_ID;

  // 3. AND THE CODOMAIN RECORD MUST NOT HAVE CRAWLED BACK. Structural, so the
  //    split cannot decay into prose: no field of TARGET_ENCODING may name a
  //    source-fragment operator or an emission refusal.
  //    BOTH RECORDS, because the template encoding carried the same leak in
  //    miniature: TARGET_TEMPLATE_ENCODING.nodes.sub used to state that the
  //    target application order is inverted and that the inversion happens
  //    inside emit(), so replacing PRED with a different extensionally equal
  //    construction would have re-cut tenc, lsem and isem for a change the
  //    TEMPLATE LANGUAGE did not undergo.
  const leakWords = ["PRED", "combinator", "emit-", "underflow", "Church", "emit()"];
  const codomainLeaks = leakWords.filter((w) => canonicalBytes(TARGET_ENCODING).includes(w));
  const templateLeaks = leakWords.filter((w) => canonicalBytes(TARGET_TEMPLATE_ENCODING).includes(w));
  const mapWords = [...codomainLeaks, ...templateLeaks];
  MEASURED.map_grew_esem_moved = grownEsem;
  R("E-2f a new OPERATOR moves the map's id and NOT the codomain's",
    anchored && futureAbsent && grownRules && grownEsem && grownXenc
      && widenedXenc && requotientedXenc && mapWords.length === 0,
    `adding a synthetic \`${FUTURE}\` rule — an operator the fragment does NOT have ` +
    `(${futureAbsent}) — to EMISSION_RULES moves EMISSION_RULES_SEM_ID (${grownRules}) ` +
    `and EMISSION_SEM_ID (${grownEsem}) while TARGET_EXECUTABLE_ENCODING_SEM_ID ` +
    `(${TARGET_EXECUTABLE_ENCODING_SEM_ID.slice(0, 14)}…) STANDS STILL (${grownXenc}) — which is the ` +
    `property B7 did not have and could not have had, because the Church expansion, the combinators, ` +
    `the operand order, the codomain restriction and the emission refusals were all inside the ` +
    `codomain's own record. NON-VACUOUS IN THE OTHER DIRECTION: adding an executable CONSTRUCTOR ` +
    `moves xenc (${widenedXenc}) and so does changing the alpha/label QUOTIENT (${requotientedXenc}), ` +
    `so the id has not merely gone quiet. AND THE PREDICTION WAS THEN MET BY A REAL OPERATOR: B8.2 ` +
    `added \`mul\` — a template node, a lowering rule, an emission rule, a domain rule and a binder ` +
    `slot — and tenc, lsem, isem, esem, erul, cemp and cema all moved while ` +
    `TARGET_EXECUTABLE_ENCODING_SEM_ID stood exactly still. AND THE SPLIT IS STRUCTURAL rather than a convention: no ` +
    `field of TARGET_ENCODING mentions a source operator, a combinator or an emission refusal ` +
    `(${mapWords.length} such words across TARGET_ENCODING and TARGET_TEMPLATE_ENCODING), so map ` +
    `facts have no field to crawl back into. The recomputation reproduces all three live ids before ` +
    `mutating anything (${anchored}), so the equalities above are evidence rather than a tautology ` +
    `about an object nobody touched`);
}

/* ── 7b. B7: THE CODOMAIN REFUSAL, AND WHAT IT IS NOT ────────────────────
   Four fixtures whose programs are impeccable and whose terms do not exist.
   The case has to establish four separate things, and collapsing any two of
   them would let the refusal be mistaken for something it is not:

       IT IS NOT A SOURCE REFUSAL     the source evaluator computes a value for
                                      every one of them. sub(2,3) is -1.
       IT IS NOT A LOWERING REFUSAL   all four lower, and all four instantiate.
       IT IS NOT SATURATION           no target term is produced at all, so
                                      there is no 0 to mistake for an answer.
       THERE IS NO TARGET OUTCOME     and the evidence SAYS SO. A refusal that
                                      left the reader to infer the absence of a
                                      downstream claim is how "we did not check"
                                      comes to look like "we checked and it held". */
{
  const rows = REFUSING.map((f) => {
    const r = RECORDS.find((x) => x.id === f.id);
    let source = null;
    try { source = evaluate(r.program, { exact: {}, predicates: {} }, r.inputs).value; }
    catch (e) { source = `threw:${e.message}`; }
    return {
      id: r.id,
      lowered: r.low?.ok === true,
      instantiated: r.inst?.ok === true,
      refusedAtEmit: r.ok === false && r.stage === "emit" && r.reason === f.refusal,
      // the SOURCE produced a value — that is what makes this a codomain refusal
      sourceValued: typeof source === "number",
      source,
      detail: r.detail,
    };
  });
  // AND THE SOURCE VALUE IS NOT ALWAYS NEGATIVE, which is the whole point of
  // the nested fixture: (2-3)+2 evaluates to 1 in the source, and 1 is
  // perfectly emittable. A check that refused on the ROOT value would accept it.
  const nestedOk = rows.some((x) => x.id.startsWith("E-18") && x.source >= 0 && x.refusedAtEmit);
  // no receipt exists for any of them — not an empty one, not a refused one
  const noReceipt = REFUSING.every((f) => RECORDS.find((x) => x.id === f.id).receipt === undefined);
  MEASURED.refusing = rows.length;
  MEASURED.refusing_named = rows.filter((x) => x.refusedAtEmit).length;
  R("E-10 the CODOMAIN refusal is named, and it is not a source refusal",
    rows.length >= 4 && rows.every((x) => x.lowered && x.instantiated && x.refusedAtEmit && x.sourceValued)
      && nestedOk && noReceipt,
    `${rows.length}/${rows.length} refusing fixtures LOWERED and INSTANTIATED and were refused only at ` +
    `EMISSION (${rows.map((x) => `${x.id.split(" ")[0]} ${x.detail}`).join(", ")}), while the SOURCE ` +
    `evaluator returned a value for every one of them (${rows.map((x) => x.source).join(", ")}). That ` +
    `combination is the claim: source language PROPERLY CONTAINS the representable target fragment. ` +
    `It is NOT source-refusal to target-refusal preservation — nothing refused upstream, sub(2,3) is ` +
    `-1 and the frozen core is right about that — and it is not saturation, because no target term ` +
    `exists to carry a wrong answer. NO EmissionReceipt is built for any of them (${noReceipt}), so ` +
    `there is no target outcome and nothing downstream claims one. AND THE ROOT VALUE IS NOT THE ` +
    `TEST: (2-3)+2 has source value ${rows.find((x) => x.id.startsWith("E-18"))?.source}, which is ` +
    `emittable, and it refuses anyway — a root-only check would accept it and raw Church monus would ` +
    `then answer 2`);
}

/* ── 7c. B7: THE REFUSAL IS PROFILE-INDEPENDENT ──────────────────────────
   Emission takes a profile now (B6.3), so "which templates are emittable" is a
   question that COULD have been made configurable by accident. It is not, and
   the check is cheap: run the domain refusal under every alternate profile
   E-2c varies, and under a profile so broken that emission could not proceed
   even for a good template. */
{
  const ALT_PROFILES = [
    ["counter 7000", { ...CANONICAL_EMITTER_PROFILE, label_counter_start: 7000 }],
    ["node-then-operands", { ...CANONICAL_EMITTER_PROFILE, label_alloc_order: "node-then-operands" }],
    ["unknown alloc order", { ...CANONICAL_EMITTER_PROFILE, label_alloc_order: "nonsense" }],
    ["malformed binder_names", { ...CANONICAL_EMITTER_PROFILE, binder_names: null }],
  ];
  const under = REFUSING.map((f) => {
    const r = RECORDS.find((x) => x.id === f.id);
    return ALT_PROFILES.map(([name, p]) => {
      try { emit(r.closed, p); return { name, reason: "EMITTED" }; }
      catch (e) { return { name, reason: String(e.message).split(":")[0] }; }
    });
  }).flat();
  const allSame = under.every((x) => x.reason === "emit-sub-underflow");
  // and the SAME broken profiles do stop a GOOD template, so the check above is
  // not passing because those profiles are harmless
  const good = RECORDS.find((r) => r.ok && r.id.startsWith("E-10"));
  const brokenBite = ALT_PROFILES.slice(2).map(([name, p]) => {
    try { emit(good.closed, p); return { name, reason: "EMITTED" }; }
    catch (e) { return { name, reason: String(e.message).split(":")[0] }; }
  });
  R("E-10b the domain refusal does not depend on the PROFILE",
    allSame && brokenBite.every((x) => x.reason !== "EMITTED" && x.reason !== "emit-sub-underflow"),
    `${under.length} (refusing fixture × profile) pairs across ${ALT_PROFILES.length} profiles — two ` +
    `valid knob settings and two BROKEN profiles — all answer emit-sub-underflow (${allSame}). The ` +
    `refusal is decided before a knob is read, so no serialization configuration can turn it into an ` +
    `acceptance OR into a different refusal. NON-VACUOUS: the same two broken profiles handed a ` +
    `representable template answer ${brokenBite.map((x) => `${x.name} -> ${x.reason}`).join(", ")}, so ` +
    `they really are fatal and the invariance above is the ORDER of the checks rather than the ` +
    `profiles being harmless`);
}

/* ── 7d. B7: EMISSION IS NOT A CONSTANT FOLDER ───────────────────────────
   The representability walk computes the value of the closed template. It
   would be one line from there to returning church(value), every integration
   theorem would pass, and the compiler would have stopped compiling. So the
   distinction is MEASURED rather than promised: for each emitting sub fixture,
   the bytes must contain the predecessor structure and must NOT equal the
   bytes of the folded literal — and the RUNTIME must actually do the work. */
/* THE SUB-BEARING SET IS DERIVED FROM THE CLOSED TEMPLATES, not from fixture
   names. A regex over ids would have been a hand-kept list wearing a
   derivation's clothes — and it is the kind of selector that silently shrinks
   the day a fixture is renamed. */
const hasSub = (t) => !!t && typeof t === "object"
  && (t.t === "sub" || hasSub(t.a) || hasSub(t.b));
const hasMul = (t) => !!t && typeof t === "object"
  && (t.t === "mul" || hasMul(t.a) || hasMul(t.b));
{
  const subFixtures = RECORDS.filter((r) => r.ok && hasSub(r.closed));
  const rows = subFixtures.map((r) => {
    const out = runFloat(r.bytes);
    const value = decodeBytes(r.bytes);
    const folded = value.ok ? emit({ t: "church", n: value.outcome.value }) : null;
    return {
      id: r.id,
      hasPred: /λg\.λh\.\(h \(g f\)\)/.test(r.bytes),
      notFolded: folded !== null && r.bytes !== folded,
      longer: folded !== null && r.bytes.length > folded.length,
      steps: out.steps,
      value: value.ok ? value.outcome.value : value.reason,
    };
  });
  MEASURED.sub_emitting = rows.length;
  R("E-10c emission EMITS SUBTRACTION, it does not compute it",
    rows.length >= 5 && rows.every((x) => x.hasPred && x.notFolded && x.longer && x.steps > 0),
    `${rows.length} emitting sub fixtures: every one contains the PRED body λg.λh.(h (g f)) in its ` +
    `bytes, every one differs from emit(church(itsOwnValue)), and every one is LONGER than that fold ` +
    `would be. The runtime then does the arithmetic under its own dynamics — ` +
    `${rows.map((x) => `${x.id.split(" ")[0]} ${x.steps} frames -> ${x.value}`).join(", ")} — where a ` +
    `folded church numeral would reduce in ZERO. (These counts come from runFloat's default RANDOM ` +
    `scheduler and are not the leftmost counts measure_pred_sub.mjs prints; the frame count is not a ` +
    `semantic quantity and two schedulers are entitled to disagree about it.) This case exists ` +
    `because the representability walk computes exactly the value a folder would return and then ` +
    `throws it away, and "we did not fold" is not a property a reader can see by looking at the code ` +
    `that decides not to`);
}

/* ── 7e. B7: OPERAND ORDER IS SEMANTIC, AND THE SWAP IS NOW A FALSIFIER ──
   E-8b's algebraic swap is meaning-preserving only because addition commutes.
   B6.3.1 said in as many words that the day `sub` landed it would become a
   falsifier for the OPPOSITE property. This is that case, and it is stated as
   a prediction met rather than a new idea: swapping a sub's operands must
   either change the answer or leave the codomain entirely. */
/* THE FIRST DRAFT OF THIS CASE FAILED, AND IT FAILED CORRECTLY. It called the
   swap applicable to every sub-rooted fixture, and sub(2,2) is its own swap —
   so the applicable set contained a fixture whose output CANNOT reveal the
   property being claimed. That is INSTANTIATION_FALSIFIERS I-4c's own species
   ("a test whose output cannot reveal the defect it is named for") and B6.1's
   mislabelled fixture again: a symmetric operand pair is not a witness for
   order-sensitivity, in exactly the way add(x,y) with x=2,y=3 is not a witness
   for a swapped port. equivEmit has excluded byte-equal operands since B6.1 and
   this case did not, which is the second time a property was stated more
   widely than the population it can hold over. Excluded BY NAME below, with a
   count, so the exclusion is visible rather than a filter nobody sees. */
{
  const eq = (x, y) => JSON.stringify(x) === JSON.stringify(y);
  const subRooted = RECORDS.filter((r) => r.closed?.t === "sub");
  const symmetric = subRooted.filter((r) => eq(r.closed.a, r.closed.b));
  const rows = subRooted.filter((r) => !eq(r.closed.a, r.closed.b)).map((r) => {
    const c = r.closed;
    let swapped;
    try {
      const bytes = emit({ t: "sub", a: c.b, b: c.a });
      const o = runFloat(bytes);
      const d = decodeBytes(bytes);
      swapped = { kind: "emitted", value: d.ok ? d.outcome.value : d.reason };
    } catch (e) { swapped = { kind: "refused", reason: String(e.message).split(":")[0] }; }
    let mine;
    if (r.ok) { const d = decodeBytes(r.bytes);
      mine = { kind: "emitted", value: d.ok ? d.outcome.value : d.reason }; }
    else mine = { kind: "refused", reason: r.reason };
    // THREE WITNESS SHAPES, and every applicable fixture must be one of them.
    // Written as a classification rather than a boolean so that "differs" can
    // never be satisfied by comparing a value against an undefined — which is
    // what the first draft did for the refusing fixtures, and it would have
    // passed them vacuously.
    const shape = mine.kind === "emitted" && swapped.kind === "refused" ? "emit->refuse"
      : mine.kind === "refused" && swapped.kind === "emitted" ? "refuse->emit"
      : mine.kind === "emitted" && swapped.kind === "emitted" && mine.value !== swapped.value ? "value-changed"
      : "NO WITNESS";
    return { id: r.id.split(" ")[0], mine, swapped, shape };
  });
  const shapes = new Set(rows.map((x) => x.shape));
  // the sharpest form: ONE PAIR OF FIXTURES over the same two operands, one of
  // which emits and one of which does not
  const emits52 = RECORDS.find((r) => r.id.startsWith("E-10 "));
  const refuses25 = RECORDS.find((r) => r.id.startsWith("E-17 "));
  const pairOk = emits52?.ok === true && refuses25?.ok === false
    && eq(emits52.closed.a, refuses25.closed.b) && eq(emits52.closed.b, refuses25.closed.a);
  MEASURED.swap_sub_applicable = rows.length;
  MEASURED.swap_sub_symmetric = symmetric.length;
  R("E-8c the operand SWAP is a FALSIFIER for sub, not an equivalence",
    rows.length >= 4 && !shapes.has("NO WITNESS") && shapes.has("emit->refuse")
      && shapes.has("refuse->emit") && pairOk && symmetric.length >= 1,
    `swapping a sub's operands is applicable to ${rows.length} of ${subRooted.length} sub-rooted ` +
    `fixtures and on every one it produces a witness ` +
    `(${rows.map((x) => `${x.id}: ${x.shape}`).join(", ")}) across ${shapes.size} distinct shapes. ` +
    `${symmetric.length} fixture(s) are EXCLUDED BY NAME — ` +
    `${symmetric.map((r) => r.id.split(" ")[0]).join(", ")}, whose two operands are byte-equal, so the ` +
    `swap is the identity and the output cannot reveal the property. THE FIRST DRAFT INCLUDED THEM ` +
    `AND FAILED: that is INSTANTIATION_FALSIFIERS I-4c's own species — a test whose output cannot ` +
    `reveal the defect it is named for — and equivEmit has excluded byte-equal operands since B6.1 ` +
    `while this case did not. THE SHARPEST FORM IS A PAIR: E-10 sub(5,2) emits and E-17 sub(2,5) is ` +
    `refused, over the SAME two operands with the fields exchanged (${pairOk}). B6.3.1 predicted this ` +
    `round when it demoted E-8b — a proof that depends on the algebra of whichever operators happen ` +
    `to exist is a proof with an expiry date, and this is the round it expired in`);
}

/* ── 7f. B7.1r: THE ROUND BEFORE THIS ONE GOT THIS WRONG, ON THE RECORD ──
   B7 shipped a case here called "the executable encoding moved, and ONLY for
   the B7 additions". It measured correctly — deleting `.sub`, `.domain`,
   `.saturation` and the underflow refusal from the live TARGET_ENCODING
   reproduced the B6.3.1 id byte for byte — and it drew the wrong conclusion
   from the measurement: that a new source operator must move the executable
   encoding's identity.

   GPT ruled otherwise and E-2f now carries the correct property. What is left
   for this case is the SUPERSESSION, because a round that defended the wrong
   decomposition and a round that fixed it are different facts, and a reader
   comparing the two packs deserves to find the first one recorded rather than
   quietly gone. */
{
  const R7 = SUPERSEDED_MAP_IN_CODOMAIN_SEM_IDS;
  const recorded = typeof R7?.target_executable_encoding_sem_id_b7 === "string"
    && R7.target_executable_encoding_sem_id_b7.startsWith("xenc-")
    && R7.target_executable_encoding_sem_id_b7 !== TARGET_EXECUTABLE_ENCODING_SEM_ID
    && R7.target_template_encoding_sem_id_b7 !== TARGET_TEMPLATE_ENCODING_SEM_ID;
  // and the correction must SAY it was a correction, in the direction that can
  // be softened later
  const admits = /IT WAS NEITHER/.test(R7?.correction ?? "");
  // the B7 additions really are gone from the codomain record, which is what
  // the old case measured and is still worth measuring — just no longer worth
  // the conclusion it drew
  const gone = !("sub" in TARGET_ENCODING) && !("domain" in TARGET_ENCODING)
    && !("saturation" in TARGET_ENCODING) && !("numbers" in TARGET_ENCODING)
    && !("add" in TARGET_ENCODING) && TARGET_ENCODING.refusals === undefined;
  R("E-10d B7's xenc conclusion is SUPERSEDED and recorded as wrong",
    recorded && admits && gone && EMISSION_RULES.node_rules.sub !== undefined,
    `TARGET_EXECUTABLE_ENCODING_SEM_ID was ${R7.target_executable_encoding_sem_id_b7.slice(0, 14)}… at ` +
    `B7 and is ${TARGET_EXECUTABLE_ENCODING_SEM_ID.slice(0, 14)}… now, and the record says why: B7 ` +
    `defended the movement as necessary and it was neither necessary nor caused by \`sub\`. The ` +
    `Church expansion, the combinators, the operand order, the codomain restriction and the emission ` +
    `refusals have all left TARGET_ENCODING (${gone}) for EMISSION_RULES, where E-2f shows a new ` +
    `operator moves the map's id and leaves the codomain's alone. B7's OWN CASE HERE MEASURED ` +
    `CORRECTLY AND CONCLUDED WRONGLY, which is the more useful thing to leave on the record than a ` +
    `deleted case`);
}

/* ── 7g. B8.2: mul(4,3) IS WHY B8.1 HAD TO HAPPEN FIRST ─────────────────
   The decoder widening and the operator are one capability round, and this is
   the case that says so rather than leaving the ordering to a ledger sentence.
   4*3 is 12; Church 12's canonical signature crosses §5's 80-character bound
   and is replaced by its own hash. A decoder reading signatures could not have
   read this fixture's answer, while the runtime reached the normal form and
   the native binary agreed about it the whole time. */
{
  const rows = RECORDS.filter((r) => r.ok && hasMul(r.closed)).map((r) => {
    const own = ownedNf(r.bytes);
    const sig = semStateSignature(new FloatRt(), own);
    const d = decodeTarget(own);
    return { id: r.id.split(" ")[0], value: d.ok ? d.outcome.value : d.reason,
      siglen: sig.length, compacted: sig.includes("#"),
      hasComb: /λm\.λn\.λf\.\(m \(n f\)\)/.test(r.bytes) };
  });
  const past = rows.filter((x) => x.compacted);
  const twelve = rows.find((x) => x.value === 12);
  MEASURED.mul_fixtures = rows.length;
  MEASURED.mul_past_ceiling = past.length;
  R("E-11 mul NEEDS the widened decoder, and it is not folded",
    rows.length >= 4 && rows.every((x) => x.hasComb) && past.length >= 1 && twelve !== undefined
      && IMPLEMENTED_LOWERED_OPS.includes("mul"),
    `${rows.length} emitting mul fixtures, every one carrying the MUL combinator λm.λn.λf.(m (n f)) ` +
    `in its bytes rather than a folded literal: ` +
    `${rows.map((x) => `${x.id}=${x.value}(sig ${x.siglen}${x.compacted ? ", COMPACTED" : ""})`).join(", ")}. ` +
    `${past.length} of them normalise to a Church numeral whose canonical SIGNATURE is §5-compacted, ` +
    `so the signature decoder retired at B8.1 could not have read their answers — and one of them is ` +
    `mul(4,3) = 12, the first value past that ceiling. THAT IS THE ORDERING ARGUMENT AS A ` +
    `MEASUREMENT: the decoder widening was forced by this workload rather than done in advance, and ` +
    `a round that added mul without it would have had to either cap its fixtures below 12 or call a ` +
    `complete computation a partial result`);
}

/* ── 8. THE INTEGRATION THEOREM, LABELLED AS ONE ─────────────────────────
   GPT's ruling: compose downstream, but do NOT let this become the definition
   of emission correctness. So it runs last, over the JS oracle, and every case
   above stands without it. What it adds is that the emitted terms are not
   merely well-identified but actually compute the source program's answer. */
{
  const rows = RECORDS.filter((r) => r.ok).map((r) => {
    // NORMALISE FIRST. The first draft decoded the signature of the EMITTED
    // term, which is the program before it has computed anything — decode
    // answered "not a church numeral" for the small cases and
    // "signature-compacted" for the rest, and the compacted answer is the
    // instructive one: a >80-character signature is replaced by its own hash,
    // so a decoder handed one cannot tell a wrong term from a large one.
    const out = runFloat(r.bytes);
    const d = decodeBytes(r.bytes);
    const target = d.ok ? outcomeSemId(d.outcome) : null;
    // The source evaluator takes a GRANT — {exact, predicates} — as its second
    // argument. `null` threw on every fixture, and the case reported 0/8 with
    // the target column populated, which reads like a target defect and was an
    // instrument defect. The pure fragment reads nothing, so the grant is empty.
    let source = null;
    try { source = outcomeSemId({ status: "value",
      value: evaluate(r.program, { exact: {}, predicates: {} }, r.inputs).value }); }
    catch (e) { source = `threw:${e.message}`; }
    return { id: r.id, agree: target !== null && target === source, target, source,
             steps: out.steps, value: d.ok ? d.outcome.value : d.reason };
  });
  const agreed = rows.filter((x) => x.agree).length;
  MEASURED.integration_agreed = agreed;
  MEASURED.integration_total = rows.length;
  R("E-9 INTEGRATION source outcome == decoded target outcome",
    agreed === rows.length,
    `${agreed}/${rows.length} fixtures: the source evaluator's outcome identity equals the identity of ` +
    `the outcome decoded from the emitted term's canonical signature ` +
    `(values ${rows.map((x) => x.value).join(", ")}). LABELLED AN INTEGRATION THEOREM and run last on ` +
    `purpose: emission conformance is E-1..E-F3 above and does not depend on this. Defining the ` +
    `emitter's correctness by what its output computes would put the runtime inside the compiler's ` +
    `contract, which is the layer collapse lowering_spike.layer_separation exists to refuse`);
}

console.log("═".repeat(96));
console.log(fail
  ? `EMISSION-CONFORMANCE: FAIL — ${ran} cases ran, at least one failed`
  : `EMISSION-CONFORMANCE-v1: PASS — ${ran}/${ran} over ${FIXTURES.length} fixtures — ` +
    `${EMITTING.length} that EMIT and ${MEASURED.refusing} the compiler REFUSES BY NAME, which is ` +
    `B7's addition and is not a shortfall. Every count below is over the population it names. The ` +
    `emitting family closes to ${MEASURED.distinct_closed} distinct templates, ` +
    `${MEASURED.shared_groups} of them reached by more than one fixture ` +
    `(${MEASURED.shared_named}) — the finding rather than a defect. ` +
    `The canonical emitter DETERMINISTICALLY REALISES its declared ` +
    `relation ${EMISSION_SEM_ID.slice(0, 14)}…: every receipt {closed_template_sem_id, ` +
    `emission_sem_id, target_term_sem_id} verifies by INDEPENDENT RECONSTRUCTION — rebuild the closed ` +
    `template, re-emit, canonicalise with an oracle the emitter was not allowed to choose. ` +
    // EVERY NUMBER AND EVERY DIRECTION BELOW IS A FIELD WRITTEN BY THE CASE
    // THAT MEASURED IT. The B6 version of this sentence asserted the opposite
    // of two of them.
    `QUOTIENT-VISIBLE STRUCTURAL DRIFT moves target_term_sem_id and is REFUSED on ` +
    `${MEASURED.drift_refused}/${MEASURED.drift_applicable} emitting fixtures. ALPHA-RENAMING AND ` +
    `LABEL PERMUTATION LEAVE IT UNCHANGED on ${MEASURED.alpha_identical}/${EMITTING.length}, as L-BYTES-1 ` +
    `requires — so an emitter that only relabels has not produced a different term, and "the ` +
    `allocation changed" is invisible at this identity. THE GENERIC structural alternate — a beta ` +
    `wrapper, applicable to every fixture rather than to the add-bearing ones — differs in id on ` +
    `${MEASURED.beta_differs}/${MEASURED.beta_applicable} and agrees in decoded outcome on ` +
    `${MEASURED.beta_same_meaning}/${MEASURED.beta_applicable}; the add-specific operand swap is kept ` +
    `beside it as a measurement over its ${MEASURED.equiv_applicable} applicable fixtures. THAT IS A ` +
    `LADDER AND NOT ` +
    `A PAIR: exact emitted BYTES —quotient alpha and label spelling→ target_term_sem_id —execute, ` +
    `normalise, decode→ outcome_sem_id. Different bytes may share a target term; different target ` +
    `terms may share an outcome; EMISSION PROVES THE MIDDLE ONE, and a receipt carrying no byte ` +
    `digest does not claim these exact bytes were produced. AND THE BYTE END OF THAT LADDER HAS TWO ` +
    `OWNERS, NOT ONE: ${MEASURED.knobs} serialization knobs varied LIVE each move the emitted bytes ` +
    `and CANONICAL_EMITTER_PROFILE_ID and no target term, while the emitter's own source text is ` +
    `identified separately as ${CANONICAL_EMITTER_ARTIFACT_ID.slice(0, 14)}… over ` +
    `${MEASURED.artifact_members} members whose completeness is DERIVED from the module's own ` +
    `bindings (${MEASURED.closure_refs} referenced, 0 escaping) rather than maintained — because a ` +
    `profile is configuration, and B6.2's two-term byte theorem survived a change to the very ` +
    `spelling it named as its precondition, and B6.3's three-member bundle survived a boolean flipped ` +
    `in a table emit() reads. NO NATIVE FILM IS REQUIRED OR USED. E-9 ` +
    `composes downstream — ${MEASURED.integration_agreed}/${MEASURED.integration_total} source ` +
    `outcome == decoded target outcome — and is labelled an INTEGRATION theorem rather than the ` +
    `definition. AND B7's OTHER HALF IS THE OTHER DIRECTION: ` +
    `${MEASURED.refusing_named}/${MEASURED.refusing} fixtures LOWER, INSTANTIATE and are then refused ` +
    `at EMISSION as emit-sub-underflow while the SOURCE evaluator returns a value for every one — so ` +
    `the claim is source language PROPERLY CONTAINS the representable target fragment, NOT ` +
    `source-refusal to target-refusal preservation, and no target outcome is claimed for any of them. ` +
    `The ${MEASURED.sub_emitting} emitting sub fixtures each carry real PRED structure and are each ` +
    `LONGER than emit(church(theirOwnValue)) would be, so the representability walk DECIDED and did ` +
    `not FOLD; and the operand swap, an EQUIVALENCE for add, is now a falsifier over ` +
    `${MEASURED.swap_sub_applicable} fixtures with ${MEASURED.swap_sub_symmetric} symmetric one(s) ` +
    `excluded by name.`);
process.exit(fail ? 1 : 0);
