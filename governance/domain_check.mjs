/* ═══════════════════════════════════════════════════════════════════════════
   domain_check.mjs — v0.1.0 — THE BOUNDED DOMAIN CERTIFICATE CHECKER
   law:proof.bounded-claim@1

   P1's checker had one job per case: re-derive a chain that ran to the end.
   This one has to decide something harder first — WHETHER THE CHAIN SHOULD HAVE
   RUN AT ALL — and it must decide that WITHOUT ASKING THE COMPILER.

   THE RULE THAT SHAPES THIS FILE: it does not import `representableValue`. A
   checker that asked the compiler's own domain predicate whether the compiler
   was right to refuse would prove that the compiler agrees with itself, which
   is `productByIndex`'s tautology in the one place where it would be hardest to
   notice. So `evalForTargetDomain` below is an INDEPENDENT evaluator over the
   source AST that tracks every `sub` intermediate:

       const / input   →  the value
       add(a,b)        →  va + vb
       mul(a,b)        →  va * vb
       sub(a,b)        →  record (va - vb); representable only if va >= vb

   From that it derives BOTH the source value and the EXPECTED DISPOSITION, and
   compares the certificate's evidence against an expectation it computed.

   AND IT IS NOT A CHECK ON THE FINAL VALUE. Measured on this workload: five of
   the six refused assignments have a final source value that is a perfectly
   representable natural — `(0-1)+2 = 1`, `(1-3)+2 = 0` — so a checker that
   decided from the result would agree with the compiler on ten cases, disagree
   on one, and silently accept five miscompilations. The recursion is the point.

   THE REFUSED BRANCH IS EVIDENCE, INCLUDING WHAT IS NOT IN IT. A refusal case
   asserts that lowering and instantiation succeeded, that emission declined by
   name, and that NOTHING DOWNSTREAM EXISTS.

   AND P2 LET THE CLAIMANT SAY WHAT "NOTHING DOWNSTREAM" MEANT. This file read
   the absent-set out of `bundle.claim.downstream_of_emission`, so the artifact
   defined its own negative evidence. Reproduced in four lines — drop "film"
   from the claim's list, drop it from every refusal's `absent`, hang a REAL
   eight-frame native film on one REFUSED case, reseal — and the answer was
   `ok:true` with zero refusals, for a certificate that read `REFUSED at
   EMISSION` beside a recorded execution. `domain_claim_sem_id` did not move
   either, because it bound proposition, domain and quantifier semantics and not
   the absence contract.

   P2.1: THE CONTRACT IS THIS CHECKER'S, declared below and NOT imported, and a
   bundle whose contract differs is refused rather than obeyed. It is exactly
   P1.1's move — the checker independently owns the semantics it implements —
   applied one layer down: P1.1 stopped the claimant defining SCOPE, this stops
   the claimant defining ABSENCE.

   REFUSAL CODES. The four refusal-branch codes name WHICH LOGICAL PROPERTY
   failed, because P2's single `domain-refusal-malformed` was carrying five
   forgeries with nothing in common:

     domain-scope-mismatch             scope is not the one this checker implements
     domain-case-missing               an assignment in the domain uncovered
     domain-case-duplicated            two cases with the same assignment
     domain-assignment-outside-domain  a case outside the declared product
     domain-assignment-mislabelled     assignment_sem_id ≠ its own assignment
     domain-source-value-wrong         the recorded source value is not the one
                                       this checker's own evaluator computes
     domain-disposition-mismatch       EMITTED where refusal was due, or REFUSED
                                       where the chain should have completed
     domain-refusal-contract-mismatch  the ABSENCE PROTOCOL is not this checker's:
                                       the claim's contract differs, or a case's
                                       absent-set is not the contract's
     domain-refusal-attribution-wrong  the certificate is wrong about WHERE or WHY
                                       the chain stopped: phase, code, or witness
     domain-refusal-malformed          the RECORD'S OWN SHAPE: no refusal record,
                                       a disposition in neither branch, an EMITTED
                                       case carrying a refusal branch, prose that
                                       is not prose
     domain-refusal-carries-evidence   a REFUSED case carrying an artifact the
                                       contract requires to be absent
     domain-receipt-replaced           a re-derived receipt does not match
     domain-outcome-changed            a decoded outcome or its identity altered
     domain-film-replay-refused        a film that does not replay
     domain-chain-id-mismatch          evidence about a different compiler
     domain-count-inconsistent         the aggregate's arithmetic does not hold
     domain-checker-threw              the checker raised instead of refusing
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { parse, extrude, FloatRt, semStateId, runFloat, readback, replaySemFilm }
  from "./trvm_law_kernel.mjs";
import { ScrambledFloatRt } from "./scrambled_rt.mjs";
import { evaluate, canonicalBytes } from "./derive_protocol.mjs";
import {
  lower, loweringReceipt, instantiate, instantiationReceipt, emit, emissionReceipt,
  closedTemplateSemId, outcomeSemId, programSemId, makeTargetDecoder,
  makeEmissionVerifier, verifyInstantiationReceipt,
} from "./lowering.mjs";
import { caseSetCommitment, aggregateId, chainIds } from "./proof_bundle.mjs";
import { productByIndex, renderAst } from "./proof_check.mjs";
import { grammar, publicResult, ownSnapshot } from "./schema.mjs";
import { DOMAIN_PROTOCOL, domainClaimSemId, domainSemId2, assignmentSemId2, domainCaseId }
  from "./domain_bundle.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const BUNDLE = process.argv[2] ?? join(HERE, "domain_bundle.json");

/** The scope semantics THIS checker implements, declared here and not imported
 *  — P1.1's ruling. `disposition_is_total` is the one this file adds: every
 *  assignment gets exactly one of two branches, and "neither" is not a case. */
export const IMPLEMENTED_SCOPE = Object.freeze({
  kind: "BOUNDED_EXHAUSTIVE_DOMAIN_CERTIFICATE",
  quantifier: "FOR_ALL_ASSIGNMENTS_IN_DECLARED_DOMAINS",
  generalizes_beyond_domain: false,
  disposition_is_total: true,
});

/** THE REFUSAL PROTOCOL THIS CHECKER IMPLEMENTS — the same ruling as
 *  IMPLEMENTED_SCOPE, one layer down, and the reason P2.1 exists. WRITTEN HERE
 *  AND NOT IMPORTED FROM `domain_bundle.mjs`: a checker that enumerated absence
 *  from the certificate would prove that the certificate agrees with itself,
 *  which is `productByIndex`'s tautology in the one place where a passing run
 *  looks identical either way.
 *
 *  Three things, and each is a different question a refusal must answer:
 *    phase              WHERE the chain is permitted to stop
 *    allowed_codes      WHICH refusals this protocol admits at all
 *    downstream_absent  WHAT a stop at that phase asserts does not exist
 *
 *  A bundle whose contract is not this one is REFUSED — not read, not merged,
 *  not preferred. The bundle may state its contract; it may not choose it. */
export const IMPLEMENTED_REFUSAL_CONTRACT = Object.freeze({
  phase: "EMISSION",
  allowed_codes: Object.freeze(["emit-sub-underflow"]),
  downstream_absent: Object.freeze([
    "emission_receipt", "target_term_sem_id", "target_term_bytes", "film",
    "target_nf_sem_id", "outcome", "outcome_sem_id",
  ]),
});

/** THE INDEPENDENT DOMAIN EVALUATOR. Deliberately NOT `representableValue`.
 *  Returns the source value, every subtraction intermediate it passed through,
 *  and whether the whole COMPUTATION stayed inside the non-negative naturals —
 *  which is a different question from whether its ANSWER did. */
export function evalForTargetDomain(node, env) {
  const subs = [];
  const walk = (n) => {
    if (!n || typeof n !== "object") throw new Error("domain-eval-malformed");
    switch (n.op) {
      case "const": return n.value;
      case "input": {
        if (!Object.prototype.hasOwnProperty.call(env, n.name))
          throw new Error("domain-eval-unbound: " + n.name);
        return env[n.name];
      }
      case "add": return walk(n.a) + walk(n.b);
      case "mul": return walk(n.a) * walk(n.b);
      case "sub": {
        const a = walk(n.a), b = walk(n.b);
        subs.push({ a, b, difference: a - b, representable: a >= b });
        return a - b;
      }
      default: throw new Error("domain-eval-unknown-op: " + String(n.op));
    }
  };
  const value = walk(node);
  const firstUnderflow = subs.find((s) => !s.representable) ?? null;
  return {
    value, subs,
    // THE DISPOSITION, AND IT IS DERIVED FROM THE STRUCTURE. `value >= 0` is
    // deliberately NOT consulted: on this workload it would accept five of the
    // six refusals.
    disposition: firstUnderflow ? "REFUSED" : "EMITTED",
    first_underflow: firstUnderflow,
    final_value_is_representable: Number.isInteger(value) && value >= 0,
  };
}

const identifyNf = (own) => semStateId(new FloatRt(), own);
const decodeTarget = makeTargetDecoder({ identifyNormalForm: identifyNf });
const kernelSemId = (t) => { const frt = new FloatRt(); return semStateId(frt, extrude(frt, parse(frt, t))); };
const verifyEmission = makeEmissionVerifier({ canonicaliseTarget: kernelSemId });
const ownedNf = (bytes) => { const o = runFloat(bytes); return readback(o.frt, o.root).nf; };
const keyOf = (a, vars) => vars.map((v) => `${v}=${a?.[v]}`).join(",");
/* THE SENTINEL IS A SYMBOL, AND THE FIRST ONE WAS A STRING WITH A LITERAL NUL
   IN IT — two defects for the price of one, and the tree already has a law for
   each.

   The sentinel: `safe()` returned a string on failure, and the emitted branch
   guards with `typeof bytes !== "string"`, so a refusing assignment relabelled
   EMITTED produced a FAILURE VALUE that passed the SUCCESS test and went into
   parse(), which died with "expected name at 0". Two of this file's own
   forgeries came back as `domain-checker-threw` instead of the codes they were
   written for. A sentinel a caller cannot distinguish from a result is not a
   sentinel. A Symbol cannot be mistaken for an id, a term or a receipt.

   The NUL: grid_check has a scan for exactly this, and its reason is that
   file(1) reports such a module as `data` and GREP SKIPS IT SILENTLY. Which is
   what happened — searching this file for `safe = ` returned nothing while the
   line was plainly there, and the fault looked like a failed edit. Write
   "\u0000" if a NUL is ever wanted, which is the same string. */
/** THE GRAMMAR THIS CHECKER IMPLEMENTS — law:proof.semantic-vocabulary-closed@1.
 *  P2 shipped accepting `claim.scope.proves_all_integers = true`, resealed and
 *  VERIFIED, and `refusal_witness.also_proves = "EVERY SUBTRACTION IS
 *  REPRESENTABLE"` likewise. Neither changed a value the checker read; both
 *  added vocabulary it had never agreed to. Declared here, not imported. */
const GRAMMAR = Object.freeze({
  bundle: { required: ["protocol", "claim", "chain_ids", "port_names", "cases", "aggregate"],
            optional: ["type", "version", "annotations"] },
  claim: { required: ["program", "program_sem_id", "variable_domains", "domain_sem_id",
                      "expected_cases", "scope", "refusal_contract", "domain_claim_sem_id"],
           optional: [] },
  program: { required: ["variables", "ast"], optional: [] },
  contract: { required: ["phase", "allowed_codes", "downstream_absent"], optional: [] },
  case: { required: ["case_index", "assignment", "assignment_sem_id", "source_value",
                     "case_evidence_id", "disposition"],
          optional: ["evidence", "refusal"] },
  refusal: { required: ["program_sem_id", "lowering_receipt", "instantiation_receipt",
                        "closed_template_sem_id", "refusal_phase", "refusal_code",
                        "refusal_witness", "absent"],
             optional: [] },
  witness: { required: ["minuend", "subtrahend"], optional: [] },
  evidence: { required: ["program_sem_id", "lowering_receipt", "instantiation_receipt",
                         "closed_template_sem_id", "emission_receipt", "target_term_sem_id",
                         "target_term_bytes", "film", "target_nf_sem_id",
                         "target_nf_signature_compacted", "outcome", "outcome_sem_id",
                         "execution_provenance"],
              optional: [] },
  aggregate: { required: ["case_set_commitment", "case_evidence_ids", "completed",
                          "distinct_assignments", "missing", "emitted", "refused",
                          "refused_with_representable_source_value",
                          "emitted_outcomes_equal_source", "refusal_codes",
                          "bounded_claim_verdict", "aggregate_id"],
               optional: [] },
});

const THREW = Symbol("threw");
// and the same rule for "the compiler did NOT refuse": a marker, never a string
// that could collide with a refusal code.
const EMITTED_MARKER = Symbol("emitted");
const safe = (f) => { try { return f(); } catch { return THREW; } };
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


export function checkDomainBundle(bundle) {
  /* INGRESS — law:proof.verifier-input-owned@1. One read, canonicalised,
     re-parsed into data this verifier owns; nothing below reads the
     caller's object again, so a getter cannot mean one thing to the
     check and another to everyone afterwards. */
  let owned;
  try { owned = ownSnapshot(bundle); }
  catch (e) {
    return publicResult({ measured: {}, refusals: [{ code: "domain-ingress-refused",
      detail: `the artifact has no canonical form and cannot be taken into this ` +
        `verifier's ownership: ${String(e?.message ?? e)}` }] });
  }
  try { return checkInner(owned); }
  catch (e) {
    return publicResult({ measured: {},
      refusals: [{ code: "domain-checker-threw",
        detail: `the checker raised instead of refusing: ${String(e?.message ?? e)}` }] });
  }
}

function checkInner(bundle) {
  const refusals = [];
  const refuse = (code, detail) => { refusals.push({ code, detail }); };
  const measured = {};

  if (bundle?.protocol !== DOMAIN_PROTOCOL)
    return publicResult({ measured,
      refusals: [{ code: "domain-protocol-mismatch", detail: String(bundle?.protocol) }] });

  /* THE VOCABULARY IS THIS CHECKER'S, before any value is compared. */
  const vocab = (record, spec, where) => {
    for (const v of grammar(record, spec, where)) refuse("domain-vocabulary-unknown", v.detail);
  };
  vocab(bundle, GRAMMAR.bundle, "bundle");
  /* AND THE NON-AUTHORITATIVE SEAT IS BOUNDED. P2.1 put prose in
     `refusal.notes` — an unhashed field INSIDE an authenticated record — and a
     real film hidden there moved no identity at all. P3.1 retires that shape
     entirely: prose lives out here, in the other trust domain, and this is the
     only place a checker has to say what may sit in it. */
  if (bundle.annotations !== undefined) {
    const flat = (v) => typeof v === "string"
      || (Array.isArray(v) && v.every((x) => typeof x === "string"))
      || (v && typeof v === "object" && !Array.isArray(v)
          && Object.values(v).every((x) => typeof x === "string"
            || (Array.isArray(x) && x.every((y) => typeof y === "string"))));
    if (bundle.annotations === null || typeof bundle.annotations !== "object"
        || Array.isArray(bundle.annotations) || !Object.values(bundle.annotations).every(flat))
      refuse("domain-vocabulary-unknown",
        "annotations is the NON-AUTHORITATIVE seat and holds prose only — strings, arrays of " +
        "strings, or one level of record over them. Evidence does not live outside the grammar");
  }

  const claim = bundle.claim ?? {};
  vocab(claim, GRAMMAR.claim, "claim");
  vocab(claim.program, GRAMMAR.program, "claim.program");
  const scope = claim.scope;
  vocab(scope, { required: Object.keys(IMPLEMENTED_SCOPE), optional: [] }, "claim.scope");
  vocab(claim.refusal_contract, GRAMMAR.contract, "claim.refusal_contract");
  for (const k of Object.keys(IMPLEMENTED_SCOPE))
    if (scope?.[k] !== IMPLEMENTED_SCOPE[k])
      refuse("domain-scope-mismatch",
        `scope.${k} is ${JSON.stringify(scope?.[k])}, this checker implements ${JSON.stringify(IMPLEMENTED_SCOPE[k])}`);
  for (const [k, v] of Object.entries(scope ?? {}))
    if (typeof v === "string" && /\s/.test(v))
      refuse("domain-scope-mismatch", `scope.${k} holds prose; explanatory text belongs in scope_notes`);
  if (safe(() => domainSemId2(claim.variable_domains)) !== claim.domain_sem_id)
    refuse("domain-scope-mismatch", "domain_sem_id does not identify the domains beside it");
  if (safe(() => programSemId(claim.program?.ast)) !== claim.program_sem_id)
    refuse("domain-scope-mismatch", "program_sem_id does not identify the program beside it");
  /* ── THE ABSENCE CONTRACT, BEFORE ANY CASE IS READ ──────────────────────
     Compared canonically, so key order is not a difference — the claim
     identity hashes it through canonicalBytes and the two must agree about
     what "the same contract" means. */
  const contract = claim.refusal_contract;
  const canon = (x) => safe(() => canonicalBytes(x));
  const MINE = canon(IMPLEMENTED_REFUSAL_CONTRACT);
  if (canon(contract) !== MINE)
    refuse("domain-refusal-contract-mismatch",
      `the certificate's refusal contract is not the one this checker implements: ` +
      `bundle ${JSON.stringify(contract)} vs checker ${JSON.stringify(IMPLEMENTED_REFUSAL_CONTRACT)}`);
  if (claim.downstream_of_emission !== undefined)
    refuse("domain-refusal-contract-mismatch",
      "the claim carries a bare `downstream_of_emission` list; the absence protocol is " +
      "`refusal_contract`, and a second unbound copy of it is exactly what P2.1 removed");
  if (safe(() => domainClaimSemId(claim.program_sem_id, claim.domain_sem_id, scope, contract))
      !== claim.domain_claim_sem_id)
    refuse("domain-scope-mismatch",
      "domain_claim_sem_id does not identify (program, domain, quantifier semantics, refusal contract)");

  const variables = claim.program?.variables ?? [];
  const domains = claim.variable_domains ?? {};
  if (!Array.isArray(variables) || variables.length === 0
      || !variables.every((v) => Array.isArray(domains[v]) && domains[v].length > 0))
    return publicResult({ measured,
      refusals: [...refusals, { code: "domain-scope-mismatch", detail: "domains do not cover the program's variables" }] });

  const derived = productByIndex(variables, domains);
  measured.derived_cases = derived.length;
  if (claim.expected_cases !== derived.length)
    refuse("domain-scope-mismatch", `expected_cases ${claim.expected_cases} against a derived product of ${derived.length}`);

  const cases = Array.isArray(bundle.cases) ? bundle.cases : [];
  const derivedKeys = new Set(derived.map((a) => keyOf(a, variables)));
  const seen = new Map();
  for (const c of cases) {
    vocab(c, GRAMMAR.case, `case ${c?.case_index}`);
    if (c?.refusal !== undefined) {
      vocab(c.refusal, GRAMMAR.refusal, `case ${c.case_index}.refusal`);
      vocab(c.refusal?.refusal_witness, GRAMMAR.witness, `case ${c.case_index}.refusal_witness`);
    }
    if (c?.evidence !== undefined) vocab(c.evidence, GRAMMAR.evidence, `case ${c.case_index}.evidence`);
    const k = keyOf(c.assignment, variables);
    if (!derivedKeys.has(k)) refuse("domain-assignment-outside-domain", `case ${c.case_index}: ${k}`);
    if (seen.has(k)) refuse("domain-case-duplicated", `${k} at cases ${seen.get(k)} and ${c.case_index}`);
    else seen.set(k, c.case_index);
    const keys = Object.keys(c.assignment ?? {}).sort().join(",");
    if (keys !== [...variables].sort().join(","))
      refuse("domain-assignment-outside-domain", `case ${c.case_index} binds [${keys}]`);
    if (safe(() => assignmentSemId2(c.assignment)) !== c.assignment_sem_id)
      refuse("domain-assignment-mislabelled", `case ${c.case_index}`);
  }
  for (const k of derivedKeys) if (!seen.has(k)) refuse("domain-case-missing", k);
  measured.distinct_assignments = seen.size;

  const live = chainIds();
  for (const [k, v] of Object.entries(live))
    if (bundle.chain_ids?.[k] !== v)
      refuse("domain-chain-id-mismatch", `${k}: bundle ${bundle.chain_ids?.[k]} vs live ${v}`);

  // ── EVERY CASE: EXPECTED DISPOSITION FIRST, THEN THE BRANCH ─────────────
  const ast = claim.program?.ast;
  const low = safe(() => lower(ast));
  /* THE ENUMERATION IS THIS CHECKER'S, NOT THE CERTIFICATE'S. The line this
     replaces read `claim.downstream_of_emission`, and that one dereference is
     the whole of P2's negative-evidence defect. */
  const DOWNSTREAM = IMPLEMENTED_REFUSAL_CONTRACT.downstream_absent;
  let emitted = 0, refusedCount = 0, replayed = 0, wouldPassResultOnlyCheck = 0;
  let outcomesEqualSource = 0;
  for (const c of cases) {
    const exp = safe(() => evalForTargetDomain(ast, c.assignment));
    if (exp === THREW) { refuse("domain-source-value-wrong", `case ${c.case_index}: evaluator refused`); continue; }
    if (exp.value !== c.source_value)
      refuse("domain-source-value-wrong",
        `case ${c.case_index}: recorded ${c.source_value}, this checker computes ${exp.value}`);
    if (exp.disposition !== c.disposition)
      refuse("domain-disposition-mismatch",
        `case ${c.case_index} ${keyOf(c.assignment, variables)}: recorded ${c.disposition}, ` +
        `this checker derives ${exp.disposition}` +
        (exp.first_underflow ? ` (${exp.first_underflow.a} - ${exp.first_underflow.b} underflows)` : ""));
    if (exp.disposition === "REFUSED" && exp.final_value_is_representable) wouldPassResultOnlyCheck++;

    if (c.disposition === "REFUSED") {
      refusedCount++;
      const r = c.refusal;
      if (!r) { refuse("domain-refusal-malformed", `case ${c.case_index}: no refusal record`); continue; }
      // THE ABSENCE IS THE EVIDENCE. Enumerated from the certificate's own
      // declaration, so a new downstream artifact cannot be added without a
      // decision about whether a refusal may carry it.
      if (c.evidence !== undefined)
        refuse("domain-refusal-carries-evidence",
          `case ${c.case_index}: a REFUSED case carries an \`evidence\` branch`);
      for (const f of DOWNSTREAM) if (r[f] !== undefined)
        refuse("domain-refusal-carries-evidence", `case ${c.case_index}: refusal carries ${f}`);
      /* P2.1 BOUNDED AN UNHASHED `notes` SEAT INSIDE THIS RECORD, and P3.1
         retired it: the grammar above has no `notes`, so prose here is an
         unknown semantic key and a film here is refused twice over. Bounding a
         mixed seat was a smaller version of the defect; removing the seat is
         the repair. */
      if (!same(r.absent, DOWNSTREAM))
        refuse("domain-refusal-contract-mismatch",
          `case ${c.case_index}: the refusal's declared absence is not the contract's ` +
          `downstream_absent list`);
      if (r.refusal_phase !== IMPLEMENTED_REFUSAL_CONTRACT.phase)
        refuse("domain-refusal-attribution-wrong",
          `case ${c.case_index}: refusal_phase ${r.refusal_phase}, the contract permits ` +
          `${IMPLEMENTED_REFUSAL_CONTRACT.phase}`);
      if (!IMPLEMENTED_REFUSAL_CONTRACT.allowed_codes.includes(r.refusal_code))
        refuse("domain-refusal-attribution-wrong",
          `case ${c.case_index}: refusal_code ${r.refusal_code} is not in the contract's ` +
          `allowed_codes [${IMPLEMENTED_REFUSAL_CONTRACT.allowed_codes.join(", ")}]`);
      /* THE WITNESS, RE-DERIVED. What the compiler said in English — "0 - 1" —
         is two integers, and this checker computed them itself in
         `evalForTargetDomain` before it read the record. So the certificate's
         account of WHY the chain stopped is checked rather than narrated. */
      const fu = exp.first_underflow;
      const w = r.refusal_witness;
      if (!w || typeof w !== "object" || w.minuend !== fu?.a || w.subtrahend !== fu?.b)
        refuse("domain-refusal-attribution-wrong",
          `case ${c.case_index}: refusal_witness ${JSON.stringify(w)}, this checker's own ` +
          `evaluator derives {"minuend":${fu?.a},"subtrahend":${fu?.b}}`);
      // AND THE CODE IS RE-DERIVED FROM THE COMPILER, not read. The checker
      // decides WHETHER a refusal is due on its own; it must still confirm the
      // compiler refused for the reason recorded, which only the compiler can say.
      const inst = safe(() => instantiate(low.template, c.assignment));
      if (inst === THREW || !inst?.ok) {
        refuse("domain-receipt-replaced", `case ${c.case_index}: instantiate refused`); continue; }
      let actual = null;
      try { emit(inst.closed_template); actual = EMITTED_MARKER; }
      catch (e) { const m = String(e.message ?? e); const i = m.indexOf(":");
        actual = i < 0 ? m : m.slice(0, i).trim(); }
      if (actual === EMITTED_MARKER)
        refuse("domain-disposition-mismatch",
          `case ${c.case_index}: recorded REFUSED, and re-emitting SUCCEEDS`);
      else if (actual !== r.refusal_code)
        refuse("domain-refusal-attribution-wrong",
          `case ${c.case_index}: recorded ${r.refusal_code}, the compiler says ${actual}`);
      // the front of the chain DID complete and its receipts are real evidence
      const psid = safe(() => programSemId(ast));
      if (psid !== r.program_sem_id) refuse("domain-receipt-replaced", `case ${c.case_index}: program_sem_id`);
      if (!same(safe(() => loweringReceipt(psid, low.target_template_sem_id)), r.lowering_receipt))
        refuse("domain-receipt-replaced", `case ${c.case_index}: lowering receipt`);
      const ctsid = safe(() => closedTemplateSemId(inst.closed_template));
      if (!same(safe(() => instantiationReceipt(low.target_template_sem_id, inst.inputs_sem_id, ctsid)),
                r.instantiation_receipt))
        refuse("domain-receipt-replaced", `case ${c.case_index}: instantiation receipt`);
      continue;
    }

    if (c.disposition !== "EMITTED") {
      refuse("domain-refusal-malformed", `case ${c.case_index}: disposition ${c.disposition} is neither branch`);
      continue;
    }
    emitted++;
    const ev = c.evidence;
    if (!ev) { refuse("domain-receipt-replaced", `case ${c.case_index}: no evidence branch`); continue; }
    if (c.refusal !== undefined)
      refuse("domain-refusal-malformed", `case ${c.case_index}: an EMITTED case carries a \`refusal\` branch`);
    const psid = safe(() => programSemId(ast));
    if (psid !== ev.program_sem_id) refuse("domain-receipt-replaced", `case ${c.case_index}: program_sem_id`);
    if (!same(safe(() => loweringReceipt(psid, low.target_template_sem_id)), ev.lowering_receipt))
      refuse("domain-receipt-replaced", `case ${c.case_index}: lowering receipt`);
    const inst = safe(() => instantiate(low.template, c.assignment));
    if (inst === THREW || !inst?.ok) { refuse("domain-receipt-replaced", `case ${c.case_index}: instantiate`); continue; }
    const ctsid = closedTemplateSemId(inst.closed_template);
    if (!same(instantiationReceipt(low.target_template_sem_id, inst.inputs_sem_id, ctsid), ev.instantiation_receipt))
      refuse("domain-receipt-replaced", `case ${c.case_index}: instantiation receipt`);
    if (verifyInstantiationReceipt(low.template, c.assignment, ev.instantiation_receipt).ok !== true)
      refuse("domain-receipt-replaced", `case ${c.case_index}: instantiation verify`);
    const bytes = safe(() => emit(inst.closed_template));
    if (bytes === THREW || typeof bytes !== "string") {
      refuse("domain-disposition-mismatch", `case ${c.case_index}: recorded EMITTED and re-emitting REFUSES`);
      continue;
    }
    const ttsid = kernelSemId(bytes);
    if (!same(emissionReceipt(ctsid, ttsid), ev.emission_receipt))
      refuse("domain-receipt-replaced", `case ${c.case_index}: emission receipt`);
    if (verifyEmission(inst.closed_template, ev.emission_receipt).ok !== true)
      refuse("domain-receipt-replaced", `case ${c.case_index}: emission verify`);
    if (ttsid !== ev.target_term_sem_id) refuse("domain-receipt-replaced", `case ${c.case_index}: target_term_sem_id`);
    if (bytes !== ev.target_term_bytes)
      refuse("domain-receipt-replaced", `case ${c.case_index}: recorded bytes are not what emit() produces`);
    const rA = replaySemFilm(bytes, ev.film, FloatRt);
    const rS = replaySemFilm(bytes, ev.film, ScrambledFloatRt);
    if (rA.ok !== true || rS.ok !== true)
      refuse("domain-film-replay-refused",
        `case ${c.case_index}: FloatRt ${rA.ok ? "ok" : rA.reason}, ScrambledFloatRt ${rS.ok ? "ok" : rS.reason}`);
    else replayed++;
    if (ev.film?.terminal?.termination !== "NORMAL_FORM")
      refuse("domain-film-replay-refused", `case ${c.case_index}: terminal ${ev.film?.terminal?.termination}`);
    const dec = safe(() => decodeTarget(ownedNf(bytes)));
    if (dec === THREW || !dec?.ok) { refuse("domain-outcome-changed", `case ${c.case_index}: decode`); continue; }
    if (dec.target_nf_sem_id !== ev.target_nf_sem_id)
      refuse("domain-outcome-changed", `case ${c.case_index}: target_nf_sem_id`);
    if (!same(dec.outcome, ev.outcome)) refuse("domain-outcome-changed", `case ${c.case_index}: outcome`);
    if (outcomeSemId(dec.outcome) !== ev.outcome_sem_id)
      refuse("domain-outcome-changed", `case ${c.case_index}: outcome_sem_id`);
    // AND THE TARGET MUST AGREE WITH THE SOURCE. This is the emitted branch's
    // half of the theorem; the refused branch's half is that nothing exists.
    if (dec.outcome?.value !== exp.value)
      refuse("domain-outcome-changed",
        `case ${c.case_index}: target decodes to ${dec.outcome?.value}, source is ${exp.value}`);
    else outcomesEqualSource++;
  }
  for (const c of cases)
    if (safe(() => domainCaseId(c)) !== c.case_evidence_id)
      refuse("domain-receipt-replaced", `case ${c.case_index}: case_evidence_id does not identify its own content`);

  measured.emitted = emitted;
  measured.refused = refusedCount;
  measured.films_replayed_on_two_classes = replayed;
  measured.refusals_a_result_only_check_would_accept = wouldPassResultOnlyCheck;

  // ── THE AGGREGATE, RECOMPUTED ───────────────────────────────────────────
  const agg = bundle.aggregate ?? {};
  vocab(agg, GRAMMAR.aggregate, "aggregate");
  /* EVERY MEASUREMENT DERIVED, NOT READ — P3.1 repair C. These three were
     hashed into `aggregate_id` and compared to nothing, so a producer could
     assert them freely and the PASS line printed them. The middle one is the
     headline of the emitted branch and the last is the name of the refusal. */
  const derivedAgg = {
    refused_with_representable_source_value: wouldPassResultOnlyCheck,
    emitted_outcomes_equal_source: outcomesEqualSource,
    refusal_codes: [...new Set(cases.filter((c) => c.disposition === "REFUSED")
      .map((c) => c.refusal?.refusal_code))],
  };
  for (const [k, v] of Object.entries(derivedAgg))
    if (!same(agg[k], v))
      refuse("domain-count-inconsistent",
        `aggregate.${k} says ${JSON.stringify(agg[k])}, this checker derives ${JSON.stringify(v)}`);
  measured.aggregate_fields_derived = Object.keys(derivedAgg).length;
  const ids = cases.map((c) => c.assignment_sem_id);
  if (safe(() => caseSetCommitment(ids)) !== agg.case_set_commitment)
    refuse("domain-count-inconsistent", "case_set_commitment does not commit to the assignments present");
  if (agg.completed !== cases.length)
    refuse("domain-count-inconsistent", `completed ${agg.completed} against ${cases.length} cases`);
  if (agg.distinct_assignments !== seen.size)
    refuse("domain-count-inconsistent", `distinct ${agg.distinct_assignments} against ${seen.size} measured`);
  if (agg.completed !== agg.distinct_assignments)
    refuse("domain-count-inconsistent",
      `${agg.completed} cases over ${agg.distinct_assignments} unique assignments — a total is not a coverage`);
  if (agg.emitted !== emitted || agg.refused !== refusedCount)
    refuse("domain-count-inconsistent",
      `aggregate says ${agg.emitted}/${agg.refused} emitted/refused, this checker counts ${emitted}/${refusedCount}`);
  // THE PARTITION IS TOTAL, which is `disposition_is_total` cashed rather than
  // declared: every derived assignment falls in exactly one branch.
  if (emitted + refusedCount !== derived.length)
    refuse("domain-count-inconsistent",
      `${emitted} + ${refusedCount} branches over a derived domain of ${derived.length} — the ` +
      `disposition is not total, so some assignment is in neither branch`);
  if (agg.missing !== derived.length - seen.size)
    refuse("domain-count-inconsistent", `missing ${agg.missing} against ${derived.length - seen.size} derived`);
  if (!same(agg.case_evidence_ids, cases.map((c) => c.case_evidence_id)))
    refuse("domain-receipt-replaced", "case_evidence_ids does not list the cases present");
  if (safe(() => aggregateId(agg)) !== agg.aggregate_id)
    refuse("domain-receipt-replaced", "aggregate_id does not identify the aggregate beside it");
  const evidence_verdict = refusals.length === 0 ? "VERIFIED" : "REFUSED";
  if (agg.bounded_claim_verdict !== evidence_verdict)
    refusals.push({ code: "domain-count-inconsistent",
      detail: `bundle says ${agg.bounded_claim_verdict}, this checker computes ${evidence_verdict}` });
  // ok === (verdict === "VERIFIED"), always — P3.1 repair F.
  return publicResult({ refusals, measured, evidence_verdict });
}

const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN) {
  if (!existsSync(BUNDLE)) {
    console.log(`DOMAIN-CHECK: FAIL — no certificate at ${BUNDLE} (make gov-proof builds it first).`);
    process.exit(1);
  }
  const b = JSON.parse(readFileSync(BUNDLE, "utf8"));
  const r = checkDomainBundle(b);
  console.log("═".repeat(96));
  if (!r.ok) {
    for (const x of r.refusals.slice(0, 12)) console.log(`  ${x.code}: ${x.detail}`);
    if (r.refusals.length > 12) console.log(`  … and ${r.refusals.length - 12} more`);
    console.log(`DOMAIN-CHECK: FAIL — ${r.refusals.length} refusal(s); ` +
      `[${[...new Set(r.refusals.map((x) => x.code))].join(", ")}]`);
    process.exit(1);
  }
  const m = r.measured, c = b.claim, a = b.aggregate;
  /* RENDERED FROM THE AST THIS CHECKER CHECKED. P3.1: this used to print
     `c.program.statement`, and a resealed statement put THE RIEMANN HYPOTHESIS
     IS PROVED FOR ALL NON-TRIVIAL ZEROES immediately after the word VERIFIED. */
  const rendered = `F(${c.program.variables.join(",")}) = ${renderAst(c.program.ast)}`;
  console.log(`DOMAIN-CHECK: PASS — BOUNDED DOMAIN CERTIFICATE VERIFIED. ${rendered} over ` +
    `${c.program.variables.map((v) => `${v}∈{${c.variable_domains[v].join(",")}}`).join(" × ")}: ` +
    `${m.derived_cases} assignments DERIVED BY THIS CHECKER, ${m.distinct_assignments} distinct, 0 ` +
    `missing, 0 duplicated. THE PARTITION IS TOTAL AND THIS CHECKER DERIVED IT: ${m.emitted} EMITTED ` +
    `+ ${m.refused} REFUSED = ${m.derived_cases}, decided by an INDEPENDENT evaluator that walks the ` +
    `source AST tracking every subtraction intermediate — \`representableValue\` is NOT imported, ` +
    `because a checker asking the compiler's own domain predicate whether the compiler was right to ` +
    `refuse would prove only that it agrees with itself. AND IT IS NOT A CHECK ON THE ANSWER: ` +
    `${m.refusals_a_result_only_check_would_accept}/${m.refused} of the refused assignments have a ` +
    `final source value that is a perfectly representable natural — (0-1)+2 is 1, (1-3)+2 is 0 — so ` +
    `a checker deciding from the RESULT would accept them, and B7 measured why that is a ` +
    `miscompilation: Church monus turns the inner underflow into 0 silently. THE EMITTED BRANCH ` +
    `carries the whole chain: ${a.emitted_outcomes_equal_source}/${m.emitted} decoded outcomes equal ` +
    `the source value, with every receipt reproduced field for field and ` +
    `${m.films_replayed_on_two_classes} films replayed on FloatRt and ScrambledFloatRt. THE REFUSED ` +
    `BRANCH IS EVIDENCE, INCLUDING WHAT IS NOT IN IT: lowering and instantiation receipts are real ` +
    `and re-derived, the refusal is ${a.refusal_codes.join("/")} at ` +
    `${IMPLEMENTED_REFUSAL_CONTRACT.phase}, its WITNESS is two integers this checker's own ` +
    `evaluator derived before reading them, and the ABSENCE of all ` +
    `${IMPLEMENTED_REFUSAL_CONTRACT.downstream_absent.length} downstream artifacts — emission ` +
    `receipt, target term, bytes, film, target NF and outcome — is enumerated FROM THE CONTRACT ` +
    `THIS CHECKER DECLARES AND DOES NOT IMPORT. That is P2.1: P2 read the absent-set out of the ` +
    `certificate, so the claimant defined what its own negative evidence meant, and a REFUSED case ` +
    `carrying a real eight-frame film verified with zero refusals once the list was shortened and ` +
    `resealed. The contract is now bound into domain_claim_sem_id ${c.domain_claim_sem_id.slice(0, 18)}…, ` +
    `so the meaning of the absence cannot change while the identity of the claim stands still. ` +
    `SCOPE: this is a BOUNDED EXHAUSTIVE DOMAIN CERTIFICATE over 16 assignments. It says ` +
    `nothing about \`sub\` outside them, and it is NOT source-refusal to target-refusal preservation ` +
    `— the source refuses NOTHING here; it evaluates all sixteen and the COMPILER declines six.`);
}
