/* ═══════════════════════════════════════════════════════════════════════════
   proof_check.mjs — v0.1.0 — THE AGGREGATE CHECKER
   law:proof.bounded-claim@1

   Reads `proof_bundle.json` and decides whether its BoundedClaim holds. It
   trusts the bundle for NOTHING except the two things a bundle is entitled to
   state — WHAT is claimed (the proposition) and OVER WHAT (the domains) — and
   re-derives everything else.

   WHAT "INDEPENDENT" MEANS HERE, concretely:

     · THE DOMAIN IS THE CHECKER'S OWN. It computes the Cartesian product from
       the declared domains by MIXED-RADIX INDEX ARITHMETIC, which is a
       different algorithm from the generator's iterative expansion. Two
       implementations of the same set is the point; importing the generator's
       `cartesian` would make "the cases cover the domain" a tautology about
       one function.
     · EVERY RECEIPT IS RE-DERIVED, never read. The checker rebuilds each
       program from the PROPOSITION IN THE BUNDLE, lowers it, instantiates it
       with the case's own assignment, emits, canonicalises with the kernel's
       oracle, and compares field by field.
     · EVERY FILM IS REPLAYED, on TWO RUNTIME CLASSES — FloatRt and
       ScrambledFloatRt, whose heap ids are non-monotone. That is B8.3 being
       load-bearing rather than decorative: the proof rests on readback
       agreeing across allocator representations, and this is where it is
       cashed.
     · THE AGGREGATE'S OWN NUMBERS ARE RECOMPUTED. `completed`, `missing`,
       `failed`, the case-set commitment and the aggregate id are all
       re-derived; a bundle claiming 64/64 over sixty-three unique assignments
       is refused by arithmetic, not by reading its verdict field.

   AND THE CHAIN IDS MUST MATCH THE LIVE MODULE. A proof bundle produced by
   one compiler and checked against another is evidence about neither, and the
   failure is silent unless something looks.

   THE SEVEN SHAPES GPT NAMED, each with its own refusal code, plus three this
   file adds because the same reasoning reaches them:

     proof-case-missing                one assignment in the domain uncovered
     proof-case-duplicated             two cases with the same assignment
     proof-assignment-outside-domain   a case outside the declared product
     proof-assignment-mislabelled      assignment_sem_id ≠ its own assignment
     proof-receipt-replaced            a side's receipt fails reconstruction
     proof-outcome-changed             a decoded outcome or witness altered
     proof-domain-widened              domains or expected_cases moved
     proof-count-inconsistent          "64/64" over fewer unique assignments
     proof-film-replay-refused         a film that does not replay
     proof-chain-id-mismatch           evidence about a different compiler
     proof-scope-mismatch              the artifact's machine-readable scope is
                                       not the scope this checker implements
     proof-scope-property-mismatch     an OPTIONAL claim-specific property the
                                       bundle asserts about itself does not hold
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { parse, extrude, FloatRt, semStateId, semStateSignature, runFloat, readback, replaySemFilm }
  from "./trvm_law_kernel.mjs";
import { ScrambledFloatRt } from "./scrambled_rt.mjs";
import { evaluate, canonicalBytes } from "./derive_protocol.mjs";

/** RECORD EQUALITY IS CANONICAL, NOT SERIAL — and this was a latent defect
 *  until P4.1's canonical-wire ruling walked into it. Every comparison below
 *  used `JSON.stringify(a) !== JSON.stringify(b)`, which is sensitive to
 *  OBJECT KEY ORDER: two records with identical fields in a different order
 *  compared UNEQUAL. Storing this bundle in a content-addressed store sorts its
 *  keys, so the checker refused its own artifact with `receipt-replaced` on
 *  every case — semantically identical, serially different. Any independently
 *  implemented producer emitting a different key order would have hit exactly
 *  this. The identities are untouched: they already run through
 *  `canonicalBytes`, and this only makes the COMPARISON agree with them. It
 *  fails closed — a value with no canonical form is not equal to anything. */
const same = (a, b) => {
  let x, y;
  try { x = canonicalBytes(a); } catch { return false; }
  try { y = canonicalBytes(b); } catch { return false; }
  return x === y;
};

import { grammar, publicResult, ownSnapshot } from "./schema.mjs";
import {
  lower, loweringReceipt, instantiate, instantiationReceipt, emit, emissionReceipt,
  closedTemplateSemId, outcomeSemId, programSemId, makeTargetDecoder,
  makeEmissionVerifier, verifyInstantiationReceipt, templatePorts,
} from "./lowering.mjs";
import {
  PROOF_PROTOCOL, propositionSemId, domainSemId, assignmentSemId, caseEvidenceId,
  caseSetCommitment, aggregateId, boundedClaimSemId, chainIds,
} from "./proof_bundle.mjs";

/* ── THE SCOPE THIS CHECKER IMPLEMENTS, DECLARED HERE ──────────────────────
   P1's bundle carried a `scope` and this file did not read it. Reproduced
   before repair: deleting `claim.scope`, and rewriting it to
   {kind:"UNBOUNDED PROOF", established:"proof over all naturals"}, BOTH left
   checkBundle at ok:true with zero refusals. The evidence really did establish
   a bounded fact; nothing connected that fact to the sentence sitting beside it.

   THIS IS WRITTEN HERE AND NOT IMPORTED, deliberately. Importing the
   generator's scope would compare the bundle's claim to the bundle's own idea
   of what the claim means, which is the tautology `productByIndex` exists to
   avoid one field over. What follows is a description of what the code below
   ACTUALLY DOES: it derives the full Cartesian product of the declared finite
   domains and requires a case for every member and no member outside it. That
   is universal quantification over exactly the declared domains, and nothing
   in it reaches past them. A bundle whose scope says anything else is making a
   claim this checker cannot support, and it is refused rather than trimmed. */
export const IMPLEMENTED_SCOPE = Object.freeze({
  kind: "BOUNDED_EXHAUSTIVE_VERIFICATION",
  quantifier: "FOR_ALL_ASSIGNMENTS_IN_DECLARED_DOMAINS",
  generalizes_beyond_domain: false,
});

const HERE = dirname(fileURLToPath(import.meta.url));
const BUNDLE = process.argv[2] ?? join(HERE, "proof_bundle.json");

const identifyNf = (own) => semStateId(new FloatRt(), own);
const decodeTarget = makeTargetDecoder({ identifyNormalForm: identifyNf });
const kernelSemId = (term) => { const frt = new FloatRt(); return semStateId(frt, extrude(frt, parse(frt, term))); };
const verifyEmission = makeEmissionVerifier({ canonicaliseTarget: kernelSemId });
const ownedNf = (bytes) => { const o = runFloat(bytes); return readback(o.frt, o.root).nf; };

/** THE CHECKER'S OWN PRODUCT — mixed-radix index arithmetic, deliberately not
 *  the generator's iterative expansion. Returns the assignments; the caller
 *  compares as a SET, so the two need not agree about order to agree about
 *  membership. */
export function productByIndex(variables, domains) {
  const radix = variables.map((v) => domains[v].length);
  const total = radix.reduce((a, b) => a * b, 1);
  const out = [];
  for (let n = 0; n < total; n++) {
    const a = {}; let rest = n;
    for (let i = variables.length - 1; i >= 0; i--) {
      a[variables[i]] = domains[variables[i]][rest % radix[i]];
      rest = Math.floor(rest / radix[i]);
    }
    out.push(a);
  }
  return out;
}

const keyOf = (a, variables) => variables.map((v) => `${v}=${a?.[v]}`).join(",");

/* B8.3+ P1.1: EVERY BYTE THIS FUNCTION READS COMES FROM AN UNTRUSTED PRODUCER,
   so it must REFUSE and must never THROW. The scope-deleted forgery made it die
   with a stack trace out of canonicalBytes — B2.1.2's finding, which cost a
   round when a grid forgery crashed the behavioural rung, recurring in the one
   place in this tree whose whole input is adversarial by design.
   TWO LAYERS, because one is not enough. `safe()` wraps each identity
   recomputation so a malformed field becomes a NAMED refusal at the site that
   noticed it; the outer catch is a BACKSTOP that turns anything still escaping
   into `proof-checker-threw` — refusing, not crashing, and saying which. A
   backstop that silently passed would be worse than the crash. */
const THREW = "\u0000THREW";
const safe = (f) => { try { return f(); } catch { return THREW; } };

/** THE CHECKER RENDERS THE THEOREM. It does not read one.
 *
 *  P1 shipped with `proposition.statement` inside the hashed proposition, and
 *  the PASS line printed it. Setting it to "P = NP, ESTABLISHED BY EXHAUSTIVE
 *  VERIFICATION" and resealing `proposition_sem_id` + `bounded_claim_sem_id`
 *  produced, from an artifact whose 128 chains all re-derive and whose 128 films
 *  all replay:
 *
 *      PROOF-CHECK: PASS — BOUNDED CLAIM VERIFIED. P = NP, ESTABLISHED BY
 *      EXHAUSTIVE VERIFICATION over x∈{0,1,2,3} × …
 *
 *  Hashing the sentence made it WORSE rather than better: the identity moved,
 *  the artifact stayed self-consistent, and nothing existed to disagree with it.
 *  A producer must not be able to name what a PASS proved.
 *
 *  Exported because `domain_check.mjs` needs the same rendering, and importing
 *  it is the `productByIndex` precedent — a DERIVATION both checkers own, as
 *  against a SEMANTICS either could be handed. */
export function renderAst(node) {
  const go = (n, parentPrec) => {
    if (!n || typeof n !== "object") return "?";
    switch (n.op) {
      case "const": return String(n.value);
      case "input": return String(n.name);
      case "add": case "sub": case "mul": {
        const prec = n.op === "mul" ? 2 : 1;
        const sym = n.op === "add" ? " + " : n.op === "sub" ? " - " : " * ";
        const s = go(n.a, prec) + sym + go(n.b, prec + 1);
        return prec < parentPrec ? `(${s})` : s;
      }
      default: return "?";
    }
  };
  return go(node, 0);
}

/** THE GRAMMAR THIS CHECKER IMPLEMENTS — law:proof.semantic-vocabulary-closed@1.
 *  Key SETS, not values. Declared here and not imported. */
const GRAMMAR = Object.freeze({
  bundle: { required: ["protocol", "claim", "chain_ids", "port_names", "cases", "aggregate"],
            optional: ["type", "version", "annotations"] },
  claim: { required: ["proposition", "proposition_sem_id", "variable_domains", "domain_sem_id",
                      "expected_cases", "scope", "bounded_claim_sem_id", "declared_properties"],
           optional: [] },
  proposition: { required: ["variables", "lhs", "rhs"], optional: [] },
  scope: { required: Object.keys(IMPLEMENTED_SCOPE), optional: [] },
  declared_properties: { required: [], optional: ["all_sides_distinct_target_terms"] },
  case: { required: ["case_index", "assignment", "assignment_sem_id", "source_value",
                     "source_sides_agree", "lhs", "rhs", "equality", "case_evidence_id"],
          optional: [] },
  side: { required: ["ok", "program_sem_id", "lowering_receipt", "instantiation_receipt",
                     "closed_template_sem_id", "target_term_sem_id", "emission_receipt",
                     "target_term_bytes", "film", "target_nf_sem_id",
                     "target_nf_signature_compacted", "execution_provenance", "outcome",
                     "outcome_sem_id"],
          optional: [] },
  equality: { required: ["outcome_sem_id_equal", "target_terms_differ", "closed_templates_differ",
                         "witness", "source_agrees"], optional: [] },
  provenance: { required: ["implementation_family_id", "executable_artifact_id",
                           "executor_session_id", "input_canonical"], optional: [] },
  aggregate: { required: ["case_set_commitment", "case_evidence_ids", "completed",
                          "distinct_assignments", "missing", "failed",
                          "cases_with_distinct_target_terms", "cases_with_distinct_closed_templates",
                          "cases_past_the_signature_ceiling", "distinct_lhs_program_sem_ids",
                          "distinct_lhs_target_template_sem_ids", "distinct_lhs_target_term_sem_ids",
                          "bounded_claim_verdict", "aggregate_id"],
               optional: [] },
});

export function checkBundle(bundle) {
  /* INGRESS — law:proof.verifier-input-owned@1. One read, canonicalised,
     re-parsed into data this verifier owns; nothing below reads the
     caller's object again, so a getter cannot mean one thing to the
     check and another to everyone afterwards. */
  let owned;
  try { owned = ownSnapshot(bundle); }
  catch (e) {
    return { ok: false, verdict: "REFUSED", measured: {}, refusals: [{ code: "proof-ingress-refused",
      detail: `the artifact has no canonical form and cannot be taken into this ` +
        `verifier's ownership: ${String(e?.message ?? e)}` }] };
  }
  try { return checkBundleInner(owned); }
  catch (e) {
    return { ok: false, verdict: "REFUSED", measured: {},
      refusals: [{ code: "proof-checker-threw",
        detail: `the checker raised instead of refusing: ${String(e?.message ?? e)}. A proof ` +
          `checker reads adversary-supplied bytes; a stack trace is not a verdict` }] };
  }
}

function checkBundleInner(bundle) {
  const refusals = [];
  const refuse = (code, detail) => { refusals.push({ code, detail }); return false; };
  const measured = {};

  // ── 0. SHAPE AND PROTOCOL ───────────────────────────────────────────────
  if (bundle?.protocol !== PROOF_PROTOCOL)
    return publicResult({ refusals: [{ code: "proof-protocol-mismatch", detail: String(bundle?.protocol) }], measured });

  /* ── 0b. THE VOCABULARY IS THIS CHECKER'S ────────────────────────────────
     Before any value is compared, the KEY SET of every semantic record must be
     one this checker implements. P1 shipped accepting
     `claim.scope.proves_all_naturals = true` — resealed, VERIFIED, and flatly
     contradicting the boundedness the same scope declares two fields away.
     Nothing about the values was wrong; the vocabulary was open. */
  const vocab = (record, spec, where) => {
    for (const v of grammar(record, spec, where))
      refuse("proof-vocabulary-unknown", v.detail);
  };
  vocab(bundle, GRAMMAR.bundle, "bundle");

  // ── 1. THE CLAIM IS WHAT IT SAYS IT IS ──────────────────────────────────
  const claim = bundle.claim ?? {};
  vocab(claim, GRAMMAR.claim, "claim");
  vocab(claim.proposition, GRAMMAR.proposition, "claim.proposition");
  vocab(claim.declared_properties, GRAMMAR.declared_properties, "claim.declared_properties");
  /* AND THE UNAUTHENTICATED SEAT IS BOUNDED. `annotations` is reachable by no
     identity and read by nothing, which is exactly why a checker must still say
     what may sit in it: an unbounded seat is where a semantic record's contents
     go to hide. Strings and arrays of strings, nothing else. */
  if (bundle.annotations !== undefined) {
    const flat = (v) => typeof v === "string"
      || (Array.isArray(v) && v.every((x) => typeof x === "string"))
      || (v && typeof v === "object" && !Array.isArray(v)
          && Object.values(v).every((x) => typeof x === "string"
            || (Array.isArray(x) && x.every((y) => typeof y === "string"))));
    if (bundle.annotations === null || typeof bundle.annotations !== "object"
        || Array.isArray(bundle.annotations) || !Object.values(bundle.annotations).every(flat))
      refuse("proof-vocabulary-unknown",
        "annotations is the NON-AUTHORITATIVE seat and holds prose only — strings, arrays of " +
        "strings, or one level of record over them. Evidence does not live outside the grammar");
  }
  if (safe(() => propositionSemId(claim.proposition)) !== claim.proposition_sem_id)
    refuse("proof-proposition-mislabelled", "proposition_sem_id does not identify the proposition beside it");
  if (safe(() => domainSemId(claim.variable_domains)) !== claim.domain_sem_id)
    refuse("proof-domain-widened", "domain_sem_id does not identify the domains beside it — a domain " +
      "widened after the evidence was cut would otherwise keep its old id");

  const variables = claim.proposition?.variables ?? [];
  const domains = claim.variable_domains ?? {};
  if (!Array.isArray(variables) || variables.length === 0
      || !variables.every((v) => Array.isArray(domains[v]) && domains[v].length > 0))
    return publicResult({ refusals: [...refusals, { code: "proof-domain-widened", detail: "domains do not cover the proposition's variables" }], measured });

  // ── 1b. THE SCOPE MUST BE THE ONE THIS CHECKER IMPLEMENTS ─────────────
  const scope = claim.scope;
  vocab(scope, GRAMMAR.scope, "claim.scope");
  for (const k of Object.keys(IMPLEMENTED_SCOPE)) {
    if (scope?.[k] !== IMPLEMENTED_SCOPE[k])
      refuse("proof-scope-mismatch",
        `scope.${k} is ${JSON.stringify(scope?.[k])}, this checker implements ` +
        `${JSON.stringify(IMPLEMENTED_SCOPE[k])}`);
  }
  // NO PROSE IN THE HASHED SCOPE — B6.3's structural form of the rule rather
  // than a promise to keep sentences out: a field that cannot hold a space
  // cannot quietly become a paragraph, and a paragraph in a hashed seat moves
  // the claim identity when somebody rewords it.
  for (const [k, v] of Object.entries(scope ?? {}))
    if (typeof v === "string" && /\s/.test(v))
      refuse("proof-scope-mismatch", `scope.${k} contains whitespace — the hashed scope is values, ` +
        `not prose; explanatory text belongs in scope_notes`);
  // AND THE CLAIM IDENTITY MUST IDENTIFY THE CLAIM BESIDE IT. proposition,
  // domain and quantifier semantics were three adjacent unauthenticated pieces.
  if (safe(() => boundedClaimSemId(claim.proposition_sem_id, claim.domain_sem_id, scope))
      !== claim.bounded_claim_sem_id)
    refuse("proof-scope-mismatch",
      "bounded_claim_sem_id does not identify (proposition, domain, quantifier semantics)");

  const derived = productByIndex(variables, domains);
  measured.derived_cases = derived.length;
  if (claim.expected_cases !== derived.length)
    refuse("proof-domain-widened",
      `expected_cases ${claim.expected_cases} against a derived product of ${derived.length}`);

  // ── 2. THE CASES COVER THE DERIVED DOMAIN, EXACTLY ONCE EACH ────────────
  const cases = Array.isArray(bundle.cases) ? bundle.cases : [];
  measured.cases_present = cases.length;
  const derivedKeys = new Set(derived.map((a) => keyOf(a, variables)));
  const seen = new Map();
  for (const c of cases) {
    vocab(c, GRAMMAR.case, `case ${c?.case_index}`);
    vocab(c?.equality, GRAMMAR.equality, `case ${c?.case_index}.equality`);
    for (const side of ["lhs", "rhs"]) {
      vocab(c?.[side], GRAMMAR.side, `case ${c?.case_index}.${side}`);
      vocab(c?.[side]?.execution_provenance, GRAMMAR.provenance,
        `case ${c?.case_index}.${side}.execution_provenance`);
    }
    const k = keyOf(c.assignment, variables);
    if (!derivedKeys.has(k))
      refuse("proof-assignment-outside-domain", `case ${c.case_index} assigns ${k}`);
    if (seen.has(k))
      refuse("proof-case-duplicated", `${k} appears at case ${seen.get(k)} and case ${c.case_index}`);
    else seen.set(k, c.case_index);
    // AN ASSIGNMENT MUST ALSO HAVE THE RIGHT ARITY. A case carrying an extra
    // variable, or missing one, has a key that still matches by projection.
    const keys = Object.keys(c.assignment ?? {}).sort().join(",");
    if (keys !== [...variables].sort().join(","))
      refuse("proof-assignment-outside-domain", `case ${c.case_index} binds [${keys}]`);
    if (safe(() => assignmentSemId(c.assignment)) !== c.assignment_sem_id)
      refuse("proof-assignment-mislabelled", `case ${c.case_index}: ${c.assignment_sem_id}`);
  }
  for (const k of derivedKeys) if (!seen.has(k)) refuse("proof-case-missing", k);
  measured.distinct_assignments = seen.size;

  // ── 3. THE CHAIN IDS ARE THIS COMPILER'S ────────────────────────────────
  const live = chainIds();
  for (const [k, v] of Object.entries(live))
    if (bundle.chain_ids?.[k] !== v)
      refuse("proof-chain-id-mismatch", `${k}: bundle ${bundle.chain_ids?.[k]} vs live ${v}`);

  // ── 4. EVERY CASE, BOTH SIDES, RE-DERIVED FROM THE PROPOSITION ──────────
  const lowOf = { lhs: lower(claim.proposition.lhs), rhs: lower(claim.proposition.rhs) };
  let replayed = 0, redecoded = 0, reconstructed = 0;
  const pastCeiling = new Set();
  for (const c of cases) {
    for (const side of ["lhs", "rhs"]) {
      const ev = c[side], ast = claim.proposition[side], low = lowOf[side];
      if (!ev?.ok) { refuse("proof-receipt-replaced", `case ${c.case_index} ${side}: not ok`); continue; }
      if (!low.ok) { refuse("proof-receipt-replaced", `case ${c.case_index} ${side}: proposition does not lower`); continue; }

      // 4a. the front of the chain, rebuilt
      const psid = programSemId(ast);
      if (psid !== ev.program_sem_id)
        refuse("proof-receipt-replaced", `case ${c.case_index} ${side}: program_sem_id`);
      const lrec = loweringReceipt(psid, low.target_template_sem_id);
      if (!same(lrec, ev.lowering_receipt))
        refuse("proof-receipt-replaced", `case ${c.case_index} ${side}: lowering receipt`);

      // 4b. instantiation, closed with THIS case's assignment
      const inst = instantiate(low.template, c.assignment);
      if (!inst.ok) { refuse("proof-receipt-replaced", `case ${c.case_index} ${side}: instantiate ${inst.reason}`); continue; }
      const ctsid = closedTemplateSemId(inst.closed_template);
      const irec = instantiationReceipt(low.target_template_sem_id, inst.inputs_sem_id, ctsid);
      if (!same(irec, ev.instantiation_receipt))
        refuse("proof-receipt-replaced", `case ${c.case_index} ${side}: instantiation receipt`);
      const vi = verifyInstantiationReceipt(low.template, c.assignment, ev.instantiation_receipt);
      if (vi.ok !== true)
        refuse("proof-receipt-replaced", `case ${c.case_index} ${side}: instantiation verify ${vi.reason}`);

      // 4c. emission, re-emitted independently and canonicalised by the kernel
      let bytes;
      try { bytes = emit(inst.closed_template); }
      catch (e) { refuse("proof-receipt-replaced", `case ${c.case_index} ${side}: emit ${e.message}`); continue; }
      const ttsid = kernelSemId(bytes);
      const erec = emissionReceipt(ctsid, ttsid);
      if (!same(erec, ev.emission_receipt))
        refuse("proof-receipt-replaced", `case ${c.case_index} ${side}: emission receipt`);
      const ve = verifyEmission(inst.closed_template, ev.emission_receipt);
      if (ve.ok !== true)
        refuse("proof-receipt-replaced", `case ${c.case_index} ${side}: emission verify ${ve.reason}`);
      if (ttsid !== ev.target_term_sem_id)
        refuse("proof-receipt-replaced", `case ${c.case_index} ${side}: target_term_sem_id`);
      // THE BYTES ARE PROVENANCE, not identity (B6.1) — so they are checked as
      // provenance: the recorded bytes must be the ones this emitter produces,
      // and a mismatch is reported as such rather than as a broken theorem.
      if (bytes !== ev.target_term_bytes)
        refuse("proof-receipt-replaced", `case ${c.case_index} ${side}: recorded bytes are not what emit() produces`);
      reconstructed++;

      // 4d. THE NATIVE FILM, REPLAYED ON TWO RUNTIME CLASSES. The second is
      // ScrambledFloatRt: this is where the proof cashes B8.3.
      const rA = replaySemFilm(bytes, ev.film, FloatRt);
      const rS = replaySemFilm(bytes, ev.film, ScrambledFloatRt);
      if (rA.ok !== true || rS.ok !== true)
        refuse("proof-film-replay-refused",
          `case ${c.case_index} ${side}: FloatRt ${rA.ok ? "ok" : rA.reason}, ScrambledFloatRt ${rS.ok ? "ok" : rS.reason}`);
      else replayed++;
      if (ev.film?.terminal?.termination !== "NORMAL_FORM")
        refuse("proof-film-replay-refused", `case ${c.case_index} ${side}: terminal ${ev.film?.terminal?.termination}`);

      // 4e. the outcome, re-decoded from a normal form this checker reached
      const dec = decodeTarget(ownedNf(bytes));
      if (!dec.ok) { refuse("proof-outcome-changed", `case ${c.case_index} ${side}: decode ${dec.reason}`); continue; }
      if (dec.target_nf_sem_id !== ev.target_nf_sem_id)
        refuse("proof-outcome-changed", `case ${c.case_index} ${side}: target_nf_sem_id`);
      if (!same(dec.outcome, ev.outcome))
        refuse("proof-outcome-changed", `case ${c.case_index} ${side}: outcome`);
      if (outcomeSemId(dec.outcome) !== ev.outcome_sem_id)
        refuse("proof-outcome-changed", `case ${c.case_index} ${side}: outcome_sem_id`);
      /* HASHED, SO CHECKED — P3.1's audit. This flag was inside caseEvidenceId
         and no code read it, which made it a value a producer could assert
         freely; it also feeds `cases_past_the_signature_ceiling`, so an
         unchecked flag was propagating into an unchecked total. Both are
         derived now, from a signature this checker computes over a normal form
         it reached itself. */
      const compacted = safe(() => semStateSignature(new FloatRt(), dec.owned).includes("#"));
      if (compacted !== ev.target_nf_signature_compacted)
        refuse("proof-outcome-changed",
          `case ${c.case_index} ${side}: target_nf_signature_compacted says ` +
          `${ev.target_nf_signature_compacted}, this checker computes ${compacted}`);
      if (compacted === true) pastCeiling.add(`${c.case_index}:${side}`);
      redecoded++;
    }

    // 4f. THE EQUALITY ITSELF, and the third opinion beside it
    if (c.lhs?.ok && c.rhs?.ok) {
      if (c.lhs.outcome_sem_id !== c.rhs.outcome_sem_id)
        refuse("proof-outcome-changed", `case ${c.case_index}: the two sides disagree`);
      if (c.equality?.witness !== c.lhs.outcome_sem_id)
        refuse("proof-outcome-changed", `case ${c.case_index}: equality witness is not the shared outcome id`);
      /* P1 REFUSED HERE IF THE TWO SIDES REACHED THE SAME TARGET TERM, and
         that was wrong as a validity condition. GPT overruled it: a future
         canonicalisation could legitimately collapse two distinct source
         programs at one assignment, and that assignment still proves the
         equality — it makes the case EASY, not empty. A trivial theorem is a
         valid theorem.
         AND THE FORGERY IT WAS SUPPOSED TO CATCH DOES NOT NEED IT. Replacing
         the RHS evidence with the LHS's draws NINE proof-receipt-replaced
         refusals and a film-replay refusal from independent reconstruction
         before this condition is ever reached, because each side's evidence
         must be evidence for the source program the PROPOSITION names. That is
         the stronger property, and it was already doing the work.
         Distinctness survives as a MEASUREMENT, and as an optional
         claim-specific property this artifact happens to assert — checked
         below, under its own code, because a bundle that did not assert it
         would still be valid. */
      const srcL = evaluate(claim.proposition.lhs, { exact: {}, predicates: {} }, c.assignment).value;
      const srcR = evaluate(claim.proposition.rhs, { exact: {}, predicates: {} }, c.assignment).value;
      if (!(srcL === srcR && srcL === c.lhs.outcome?.value))
        refuse("proof-outcome-changed",
          `case ${c.case_index}: source evaluator gives ${srcL}/${srcR}, target decoded ${c.lhs.outcome?.value}`);
      // hashed, so checked: the case's own record of whether the two source
      // sides agreed, against the two values this checker just computed.
      if (c.source_sides_agree !== (srcL === srcR))
        refuse("proof-outcome-changed",
          `case ${c.case_index}: source_sides_agree says ${c.source_sides_agree}, this checker ` +
          `computes ${srcL === srcR}`);
      if (c.source_value !== srcL)
        refuse("proof-outcome-changed",
          `case ${c.case_index}: source_value ${c.source_value} against a source evaluator giving ${srcL}`);
    }

    if (safe(() => caseEvidenceId(c)) !== c.case_evidence_id)
      refuse("proof-receipt-replaced", `case ${c.case_index}: case_evidence_id does not identify its own content`);
  }
  // ── 4g. OPTIONAL, CLAIM-SPECIFIC PROPERTIES ────────────────────────────
  // Not validity. A bundle may additionally CLAIM something about its own
  // shape, and if it does, the claim is checked; if it does not, nothing here
  // fires. Keeping this separate is what stops "is this workload interesting?"
  // from becoming a rule about what a proof is.
  const props = claim.declared_properties ?? {};
  if (props.all_sides_distinct_target_terms === true) {
    const same = cases.filter((c) => c.lhs?.ok && c.rhs?.ok
      && c.lhs.target_term_sem_id === c.rhs.target_term_sem_id);
    if (same.length > 0)
      refuse("proof-scope-property-mismatch",
        `the bundle CLAIMS all sides compile to distinct target terms, and ${same.length} case(s) ` +
        `do not (first: case ${same[0].case_index})`);
  }
  measured.declared_properties_checked = Object.keys(props).length;
  measured.reconstructed_sides = reconstructed;
  // PROVENANCE, COUNTED AND NEVER GATED. `executor_session_id` names a launch
  // and differs every run; `executable_artifact_id` digests the binary. Neither
  // is proof validity, and neither is checked as such — recorded here so the
  // summary can say which of the three claims this bundle actually carries.
  measured.sides_with_execution_provenance = cases.reduce((n, c) =>
    n + ["lhs", "rhs"].filter((k) => c[k]?.execution_provenance?.executable_artifact_id).length, 0);
  measured.distinct_producer_artifacts = new Set(cases.flatMap((c) =>
    ["lhs", "rhs"].map((k) => c[k]?.execution_provenance?.executable_artifact_id).filter(Boolean))).size;
  measured.films_replayed_on_two_classes = replayed;
  measured.outcomes_redecoded = redecoded;

  // ── 5. THE AGGREGATE, RECOMPUTED ────────────────────────────────────────
  const agg = bundle.aggregate ?? {};
  vocab(agg, GRAMMAR.aggregate, "aggregate");
  vocab(bundle.port_names, { required: ["lhs", "rhs"], optional: [] }, "port_names");
  /* PORT NAMES, DERIVED. Hashed into nothing and read by nobody until P3.1's
     audit: the bundle declared which ports each template opens and the checker
     had already lowered both propositions itself, so this is one comparison it
     simply never made. */
  for (const side of ["lhs", "rhs"]) {
    const mine = safe(() => templatePorts(lowOf[side].template));
    if (!same(mine, bundle.port_names?.[side]))
      refuse("proof-receipt-replaced",
        `port_names.${side} is ${JSON.stringify(bundle.port_names?.[side])}, this checker's own ` +
        `lowering opens ${JSON.stringify(mine)}`);
  }
  /* EVERY MEASUREMENT IS DERIVED, NOT READ — P3.1 repair C. Seven aggregate
     fields across P1 and P2 were hashed and never compared to anything, so a
     producer could assert them freely and the checker printed them. `failed` is
     the plainest: set it to 41, reseal the aggregate id, and the shipped
     checker returned VERIFIED over a bundle claiming forty-one failures.
     Hashing a value is not evidence for that value. */
  const derivedFailed = cases.filter((c) => !(c.lhs?.ok && c.rhs?.ok
    && c.equality?.outcome_sem_id_equal === true && c.equality?.source_agrees === true
    && c.source_sides_agree === true)).length;
  const derivedDistinctTerms = cases.filter((c) => c.equality?.target_terms_differ === true).length;
  const derivedDistinctTemplates =
    cases.filter((c) => c.equality?.closed_templates_differ === true).length;
  const derivedAgg = {
    failed: derivedFailed,
    cases_with_distinct_target_terms: derivedDistinctTerms,
    cases_with_distinct_closed_templates: derivedDistinctTemplates,
    cases_past_the_signature_ceiling: [...pastCeiling].filter((k) => k.endsWith(":lhs")).length,
    distinct_lhs_program_sem_ids: new Set(cases.map((c) => c.lhs?.program_sem_id)).size,
    distinct_lhs_target_template_sem_ids:
      new Set(cases.map((c) => c.lhs?.lowering_receipt?.target_template_sem_id)).size,
    distinct_lhs_target_term_sem_ids:
      new Set(cases.map((c) => c.lhs?.emission_receipt?.target_term_sem_id)).size,
  };
  for (const [k, v] of Object.entries(derivedAgg))
    if (agg[k] !== v)
      refuse("proof-count-inconsistent",
        `aggregate.${k} says ${JSON.stringify(agg[k])}, this checker derives ${JSON.stringify(v)}`);
  measured.aggregate_fields_derived = Object.keys(derivedAgg).length;
  const ids = cases.map((c) => c.assignment_sem_id);
  if (safe(() => caseSetCommitment(ids)) !== agg.case_set_commitment)
    refuse("proof-count-inconsistent", "case_set_commitment does not commit to the assignments present");
  if (agg.completed !== cases.length)
    refuse("proof-count-inconsistent", `completed ${agg.completed} against ${cases.length} cases`);
  if (agg.distinct_assignments !== seen.size)
    refuse("proof-count-inconsistent", `distinct ${agg.distinct_assignments} against ${seen.size} measured`);
  if (agg.completed !== agg.distinct_assignments)
    refuse("proof-count-inconsistent",
      `${agg.completed} cases over ${agg.distinct_assignments} unique assignments — a total is not a coverage`);
  if (agg.missing !== derived.length - seen.size)
    refuse("proof-count-inconsistent", `missing ${agg.missing} against ${derived.length - seen.size} derived`);
  if (!same(agg.case_evidence_ids, cases.map((c) => c.case_evidence_id)))
    refuse("proof-receipt-replaced", "case_evidence_ids does not list the cases present");
  if (safe(() => aggregateId(agg)) !== agg.aggregate_id)
    refuse("proof-receipt-replaced", "aggregate_id does not identify the aggregate beside it");
  // THE VERDICT FIELD IS READ LAST AND BELIEVED NEVER. It is compared against
  // one this checker computes; a bundle asserting VERIFIED over refused
  // evidence is refused for asserting it.
  const evidence_verdict = refusals.length === 0 ? "VERIFIED" : "REFUSED";
  if (agg.bounded_claim_verdict !== evidence_verdict)
    refusals.push({ code: "proof-count-inconsistent",
      detail: `bundle says ${agg.bounded_claim_verdict}, this checker computes ${evidence_verdict}` });

  /* THE PUBLIC RESULT HAS ONE INVARIANT: ok === (verdict === "VERIFIED").
     This used to return `computed`, captured BEFORE the line above ran — so a
     bundle whose evidence checked out and whose stored verdict was forged to
     REFUSED came back {ok:false, verdict:"VERIFIED"}. Reproduced on all three
     checkers. Inside one checker that is untidy; under nesting it is a defect
     waiting, because a parent asking `verdict === "VERIFIED"` and a parent
     asking `ok === true` would disagree about the same child. What the old
     shape was reaching for is kept as `evidence_verdict`, which cannot be
     mistaken for the verdict. */
  return publicResult({ refusals, measured, evidence_verdict });
}

const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN) {
  if (!existsSync(BUNDLE)) {
    console.log(`PROOF-CHECK: FAIL — no bundle at ${BUNDLE} (make gov-proof builds it first).`);
    process.exit(1);
  }
  const bundle = JSON.parse(readFileSync(BUNDLE, "utf8"));
  const r = checkBundle(bundle);
  const m = r.measured;
  console.log("═".repeat(96));
  if (!r.ok) {
    for (const x of r.refusals.slice(0, 12)) console.log(`  ${x.code}: ${x.detail}`);
    if (r.refusals.length > 12) console.log(`  … and ${r.refusals.length - 12} more`);
    console.log(`PROOF-CHECK: FAIL — ${r.refusals.length} refusal(s); ` +
      `[${[...new Set(r.refusals.map((x) => x.code))].join(", ")}]`);
    process.exit(1);
  }
  const c = bundle.claim, a = bundle.aggregate;
  /* THE THEOREM IS RENDERED FROM THE ASTs THIS CHECKER CHECKED, never read from
     the artifact. P3.1: the statement used to come out of the bundle, and a
     resealed `proposition.statement` put "P = NP, ESTABLISHED BY EXHAUSTIVE
     VERIFICATION" directly after the word VERIFIED. */
  const rendered = `${renderAst(c.proposition.lhs)} = ${renderAst(c.proposition.rhs)}`;
  console.log(`PROOF-CHECK: PASS — BOUNDED CLAIM VERIFIED. ${rendered} over ` +
    `${c.proposition.variables.map((v) => `${v}∈{${c.variable_domains[v].join(",")}}`).join(" × ")}: ` +
    `${m.derived_cases} assignments DERIVED BY THIS CHECKER from the declared domains, by mixed-radix ` +
    `index arithmetic rather than by importing the generator's enumeration, and matched as a SET ` +
    `against ${m.cases_present} cases — ${m.distinct_assignments} distinct, 0 missing, 0 duplicated, ` +
    `0 outside the domain. ${m.reconstructed_sides} program sides RE-DERIVED from the proposition in ` +
    `the bundle: lowered, instantiated with the case's own assignment, re-emitted, canonicalised by ` +
    `the kernel's oracle, and every lowering, instantiation and emission receipt reproduced field for ` +
    `field. ${m.films_replayed_on_two_classes} native films replayed on TWO RUNTIME CLASSES including ` +
    `ScrambledFloatRt, whose heap ids are non-monotone — which is where the proof cashes B8.3, ` +
    `because a readback that inferred order from an id integer would fail here rather than in a ` +
    `year. ${m.outcomes_redecoded} outcomes RE-DECODED from normal forms this checker reached ` +
    `itself. THE TWO SIDES ARE DIFFERENT PROGRAMS: ` +
    `${a.cases_with_distinct_target_terms}/${a.completed} cases reach DIFFERENT target terms and ` +
    `agree on the decoded outcome, with the source evaluator agreeing independently on both. ` +
    `${a.cases_past_the_signature_ceiling} of them normalise past §5's signature-compaction bound, so ` +
    `the decoder retired at B8.1 could not have read their answers. ` +
    `SCOPE IS AUTHENTICATED AND NOT MERELY STATED: kind=${c.scope.kind}, ` +
    `quantifier=${c.scope.quantifier}, generalizes_beyond_domain=${c.scope.generalizes_beyond_domain} ` +
    `— three machine-readable values, checked against the scope THIS CHECKER implements and declares ` +
    `for itself, with the English warning left unhashed in scope_notes where rewording it is free. ` +
    `bounded_claim_sem_id ${String(c.bounded_claim_sem_id).slice(0, 15)}… identifies proposition, ` +
    `domain and quantifier semantics together, so they are no longer three adjacent unauthenticated ` +
    `pieces; the hash says WHAT is claimed and this checker says whether it HOLDS. ` +
    `${m.declared_properties_checked} optional claim-specific propert(ies) verified — distinct target ` +
    `terms is one of those and NOT a validity condition, because a canonicalisation that collapsed ` +
    `two source programs at one assignment would make that case easy rather than empty. ` +
    `AND THREE CLAIMS ARE KEPT APART: PROOF VALIDITY is what this gate decides; PRODUCER PROVENANCE ` +
    `is recorded beside it and gates nothing — ${m.sides_with_execution_provenance}/` +
    `${a.completed * 2} sides carry an observed executable_artifact_id and executor_session_id, over ` +
    `${m.distinct_producer_artifacts} distinct producer artifact(s); NATIVE REPRODUCIBILITY is NOT ` +
    `established here, and re-running the binary today could not establish historical origin anyway. ` +
    `SCOPE, AND IT IS THE POINT: BOUNDED EXHAUSTIVE VERIFICATION over 64 assignments. It is NOT a ` +
    `proof of distributivity over the naturals and nothing in it generalises past 3.`);
}
