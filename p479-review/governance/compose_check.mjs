/* ═══════════════════════════════════════════════════════════════════════════
   compose_check.mjs — v0.1.0 — THE COMPOSITION CHECKER
   law:proof.bounded-claim@1

   P1's and P2's checkers each do the same kind of work: walk every case,
   re-derive every receipt, replay every film. THIS ONE DOES NONE OF THAT, ON
   PURPOSE, AND SAYS SO IN A NUMBER.

   What it does instead:

       for each cited operand
         · is its protocol one this checker implements?
         · is the child bundle actually here?
         · hand it to THAT PROTOCOL'S OWN CHECKER and require VERIFIED
         · recompute the certificate id from the CHILD'S OWN fields
         · require the citation to agree field by field, not just on the id
       then
         · the operands are pairwise distinct
         · the parent's claim identity is over exactly these operands
         · the conjunction holds

   `measured.leaf_receipts_rederived_here` is 0 and `measured.films_replayed_here`
   is 0 BY CONSTRUCTION, and the construction is worth stating exactly: THIS FILE
   HOLDS NO BINDING for the runtime, the emitter or the decoder. Replaying a film
   here is not something that could be done wrongly; it is something that cannot
   be expressed. If that ever stops being true, composition has collapsed back
   into flattening and the artifact is worth nothing over a bigger P1.

   AND THE KERNEL IS STILL IN THE PROCESS. Pretending otherwise would be the
   species of overclaim this whole line exists to refuse — `proof_check.mjs` and
   `domain_check.mjs` load the runtime, necessarily, because they are the things
   that replay the films. What the import list establishes is narrower than "no
   kernel here" and is the property that actually matters: **the kernel is
   reachable only THROUGH A CHILD CHECKER, never from the parent's own
   reasoning.** The parent's reasoning is over two verdicts.

   THE TABLE IS THIS CHECKER'S. `IMPLEMENTED_CHILD_PROTOCOLS` says which
   protocols may appear, which checker judges each, and WHICH FIELD OF A CHILD
   HOLDS THE CLAIM A CITATION IS ABOUT. All three are semantics, all three are
   declared here, and none is read from the bundle — P1.1's ruling on scope and
   P2.1's on the absence contract, arriving for the third time. A composer that
   let the artifact name its own claim field would let it choose which of its
   hashes to be judged on.

   AND A CITATION IS NOT A WARRANT. There is no registry of accepted
   certificates anywhere in this tree, so `verified_claim_sem_id` is a NAME for
   a (protocol, claim, aggregate, chain) tuple and nothing more. This checker
   never treats one as evidence that the child was accepted; it re-runs the
   child's checker every time. The saving is not in trusting the citation — it
   is that the PARENT's own reasoning is over two verdicts rather than over 138
   films.

   REFUSAL CODES

     compose-protocol-mismatch        not a composed certificate
     compose-scope-mismatch           scope is not the one this checker implements
     compose-connective-unsupported   a connective this checker cannot evaluate
     compose-operand-malformed        an operand missing a field a citation needs
     compose-operand-duplicated       the same certificate cited twice, which
                                      would let one child stand in for two
     compose-child-missing            an operand with no child bundle carried,
                                      or a child carried that nothing cites
     compose-child-protocol-unsupported  a child protocol with no checker here
     compose-child-refused            a child's OWN checker did not return VERIFIED
     compose-certificate-stale        the recomputed certificate id is not the
                                      one cited — the child moved under the citation
     compose-citation-cross-wired     the citation's id is right and the claim or
                                      aggregate it names is not the child's own
     compose-claim-id-mismatch        composed_claim_sem_id is not over these operands
     compose-count-inconsistent       the aggregate's arithmetic does not hold
     compose-checker-threw            the checker raised instead of refusing
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { grammar, publicResult, ownSnapshot } from "./schema.mjs";
import { verifiedClaimSemId, certificateOf } from "./certificate.mjs";
import { checkBundle } from "./proof_check.mjs";
import { checkDomainBundle } from "./domain_check.mjs";
import { COMPOSE_PROTOCOL, composedClaimSemId, composeAggregateId } from "./compose_bundle.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const BUNDLE = process.argv[2] ?? join(HERE, "compose_bundle.json");

/** DECLARED HERE, NOT IMPORTED. See the header. */
export const IMPLEMENTED_CHILD_PROTOCOLS = Object.freeze({
  "TRVM-BOUNDED-PROOF-v1": Object.freeze({
    claim_field: "bounded_claim_sem_id", check: checkBundle }),
  "TRVM-BOUNDED-DOMAIN-PROOF-v1": Object.freeze({
    claim_field: "domain_claim_sem_id", check: checkDomainBundle }),
});
export const IMPLEMENTED_CONNECTIVES = Object.freeze(["CONJUNCTION"]);
export const IMPLEMENTED_COMPOSE_SCOPE = Object.freeze({
  kind: "COMPOSED_VERIFIED_CLAIM_CONJUNCTION",
  quantifier: "OVER_CITED_CHILD_CERTIFICATES",
  generalizes_beyond_children: false,
  children_rechecked_by_their_own_checkers: true,
  parent_rederives_leaf_evidence: false,
});
const CITATION_FIELDS = Object.freeze(
  ["protocol", "claim_sem_id", "aggregate_id", "verified_claim_sem_id"]);

/** THE GRAMMAR THIS CHECKER IMPLEMENTS — law:proof.semantic-vocabulary-closed@1.
 *
 *  Not the values; the KEY SETS. P3 shipped accepting `claim.scope.transitive =
 *  true` and `claim.parent_may_be_cited_as_warrant = true`, both resealed, both
 *  VERIFIED, both flatly contradicting the scope_notes beside them — and the
 *  second did not even have to move the claim id, because `claim` itself had no
 *  vocabulary at all. An operand accepted `entails: "EVERYTHING"`.
 *
 *  Declared here and not imported, for the third time in three rounds. */
const GRAMMAR = Object.freeze({
  bundle: { required: ["protocol", "claim", "children", "aggregate"],
            optional: ["type", "version", "annotations"] },
  claim: { required: ["connective", "scope", "operands", "composed_claim_sem_id"],
           optional: [] },
  scope: { required: Object.keys(IMPLEMENTED_COMPOSE_SCOPE), optional: [] },
  operand: { required: [...CITATION_FIELDS], optional: [] },
  child: { required: ["verified_claim_sem_id", "bundle"], optional: [] },
  aggregate: { required: ["operands", "children_carried", "children_verified", "child_verdicts",
                          "leaf_receipts_rederived_by_parent", "composed_verdict", "aggregate_id"],
               optional: [] },
});

const THREW = Symbol("threw");
const safe = (f) => { try { return f(); } catch { return THREW; } };

export function checkComposeBundle(bundle) {
  /* INGRESS — law:proof.verifier-input-owned@1. One read, canonicalised,
     re-parsed into data this verifier owns; nothing below reads the
     caller's object again, so a getter cannot mean one thing to the
     check and another to everyone afterwards. */
  let owned;
  try { owned = ownSnapshot(bundle); }
  catch (e) {
    return publicResult({ measured: {}, refusals: [{ code: "compose-ingress-refused",
      detail: `the artifact has no canonical form and cannot be taken into this ` +
        `verifier's ownership: ${String(e?.message ?? e)}` }] });
  }
  try { return checkInner(owned); }
  catch (e) {
    return publicResult({ measured: {},
      refusals: [{ code: "compose-checker-threw",
        detail: `the checker raised instead of refusing: ${String(e?.message ?? e)}` }] });
  }
}

function checkInner(bundle) {
  const refusals = [];
  const refuse = (code, detail) => { refusals.push({ code, detail }); };
  const measured = {
    // BY CONSTRUCTION, and it is the claim of the artifact rather than a note
    // about it: this module imports no kernel, no emitter and no decoder.
    leaf_receipts_rederived_here: 0,
    films_replayed_here: 0,
  };

  if (bundle?.protocol !== COMPOSE_PROTOCOL)
    return publicResult({ measured,
      refusals: [{ code: "compose-protocol-mismatch", detail: String(bundle?.protocol) }] });

  /* THE VOCABULARY IS THIS CHECKER'S. P3 accepted `claim.scope.transitive =
     true` and `claim.parent_may_be_cited_as_warrant = true` — both resealed,
     both VERIFIED, both flatly contradicting the scope this file declares two
     fields away — and the second did not even have to move the claim id,
     because `claim` had no vocabulary at all. */
  const vocab = (record, spec, where) => {
    for (const v of grammar(record, spec, where)) refuse("compose-vocabulary-unknown", v.detail);
  };
  vocab(bundle, GRAMMAR.bundle, "bundle");
  if (bundle.annotations !== undefined) {
    const flat = (v) => typeof v === "string"
      || (Array.isArray(v) && v.every((x) => typeof x === "string"))
      || (v && typeof v === "object" && !Array.isArray(v)
          && Object.values(v).every((x) => typeof x === "string"
            || (Array.isArray(x) && x.every((y) => typeof y === "string"))));
    if (bundle.annotations === null || typeof bundle.annotations !== "object"
        || Array.isArray(bundle.annotations) || !Object.values(bundle.annotations).every(flat))
      refuse("compose-vocabulary-unknown",
        "annotations is the NON-AUTHORITATIVE seat and holds prose only");
  }

  const claim = bundle.claim ?? {};
  vocab(claim, GRAMMAR.claim, "claim");
  const scope = claim.scope;
  vocab(scope, GRAMMAR.scope, "claim.scope");
  for (const k of Object.keys(IMPLEMENTED_COMPOSE_SCOPE))
    if (scope?.[k] !== IMPLEMENTED_COMPOSE_SCOPE[k])
      refuse("compose-scope-mismatch",
        `scope.${k} is ${JSON.stringify(scope?.[k])}, this checker implements ` +
        `${JSON.stringify(IMPLEMENTED_COMPOSE_SCOPE[k])}`);
  for (const [k, v] of Object.entries(scope ?? {}))
    if (typeof v === "string" && /\s/.test(v))
      refuse("compose-scope-mismatch", `scope.${k} holds prose; explanatory text belongs in scope_notes`);
  if (!IMPLEMENTED_CONNECTIVES.includes(claim.connective))
    refuse("compose-connective-unsupported",
      `connective ${JSON.stringify(claim.connective)}; this checker evaluates ` +
      `[${IMPLEMENTED_CONNECTIVES.join(", ")}]`);

  const operands = Array.isArray(claim.operands) ? claim.operands : [];
  const children = Array.isArray(bundle.children) ? bundle.children : [];
  measured.operands = operands.length;
  measured.children_carried = children.length;
  if (operands.length === 0)
    return publicResult({ measured,
      refusals: [...refusals, { code: "compose-operand-malformed", detail: "no operands" }] });

  for (const [i, o] of operands.entries()) {
    vocab(o, GRAMMAR.operand, `operand ${i}`);
    for (const f of CITATION_FIELDS) if (typeof o?.[f] !== "string" || o[f].length === 0)
      refuse("compose-operand-malformed", `operand ${i}: ${f} is ${JSON.stringify(o?.[f])}`);
  }
  for (const [i, c] of children.entries()) vocab(c, GRAMMAR.child, `children[${i}]`);

  /* A DUPLICATE OPERAND IS ONE CHILD DOING TWO JOBS. `A ∧ A` carrying one
     bundle would otherwise satisfy a two-operand conjunction with a single
     verified child, which is the composition-shaped version of counting the
     same case twice. Distinctness is by CERTIFICATE id, not by protocol — two
     different P1 claims are a perfectly good conjunction. */
  const seen = new Map();
  for (const [i, o] of operands.entries()) {
    if (seen.has(o?.verified_claim_sem_id))
      refuse("compose-operand-duplicated",
        `${o.verified_claim_sem_id} cited at operands ${seen.get(o.verified_claim_sem_id)} and ${i}`);
    else seen.set(o?.verified_claim_sem_id, i);
  }

  const byId = new Map();
  for (const c of children) {
    if (byId.has(c?.verified_claim_sem_id))
      refuse("compose-child-missing", `two children carried under ${c?.verified_claim_sem_id}`);
    byId.set(c?.verified_claim_sem_id, c);
  }
  for (const id of byId.keys()) if (!seen.has(id))
    refuse("compose-child-missing", `a child is carried under ${id} that no operand cites`);

  let verified = 0;
  const verdicts = {};
  for (const [i, o] of operands.entries()) {
    const carried = byId.get(o?.verified_claim_sem_id);
    if (!carried) {
      refuse("compose-child-missing",
        `operand ${i} cites ${o?.verified_claim_sem_id} and no child bundle is carried under it`);
      continue;
    }
    const child = carried.bundle;
    const spec = IMPLEMENTED_CHILD_PROTOCOLS[child?.protocol];
    if (!spec) {
      refuse("compose-child-protocol-unsupported",
        `operand ${i}: child protocol ${JSON.stringify(child?.protocol)}; this checker implements ` +
        `[${Object.keys(IMPLEMENTED_CHILD_PROTOCOLS).join(", ")}]`);
      continue;
    }

    /* THE CHILD'S OWN CHECKER DECIDES THE CHILD. This is the whole architecture
       in one call: the parent does not know what a film is, and P1's checker is
       the only thing in this tree entitled to say whether P1's evidence holds. */
    const r = safe(() => spec.check(child));
    const verdict = r === THREW ? "THREW" : r?.verdict;
    verdicts[o.verified_claim_sem_id] = verdict;
    if (r === THREW || r.ok !== true || r.verdict !== "VERIFIED")
      refuse("compose-child-refused",
        `operand ${i} (${child.protocol}): its own checker returns ${verdict}` +
        (r !== THREW && r?.refusals?.length
          ? ` [${[...new Set(r.refusals.map((x) => x.code))].join(", ")}]` : ""));
    else verified++;

    /* THE CITATION IS RECOMPUTED FROM THE CHILD, NOT READ. A child that moved
       under a citation — its claim resealed, its scope rewritten, its domain
       widened — produces a different certificate id here, and the mismatch is
       the whole reason bare aggregate ids were refused as citations. */
    const own = certificateOf(child, spec.claim_field);
    const recomputed = safe(() => verifiedClaimSemId(own));
    if (recomputed === THREW)
      refuse("compose-operand-malformed",
        `operand ${i}: the child is missing a field the certificate identity binds`);
    else if (recomputed !== o.verified_claim_sem_id)
      refuse("compose-certificate-stale",
        `operand ${i}: cites ${o.verified_claim_sem_id.slice(0, 24)}…, the carried child computes ` +
        `${recomputed.slice(0, 24)}…`);

    /* AND FIELD BY FIELD, because agreeing on the hash is not agreeing on what
       it names. A citation whose id happens to match while its stated claim or
       aggregate belongs to the OTHER child is a cross-wire, and only this
       comparison sees it. */
    for (const f of ["protocol", "claim_sem_id", "aggregate_id"])
      if (o[f] !== own[f])
        refuse("compose-citation-cross-wired",
          `operand ${i}: cites ${f} ${JSON.stringify(o[f])}, the carried child's own is ` +
          `${JSON.stringify(own[f])}`);
  }
  measured.children_verified = verified;
  measured.child_verdicts = verdicts;
  measured.distinct_child_protocols = new Set(
    children.map((c) => c?.bundle?.protocol).filter(Boolean)).size;

  if (safe(() => composedClaimSemId(claim.connective, scope, operands)) !== claim.composed_claim_sem_id)
    refuse("compose-claim-id-mismatch",
      "composed_claim_sem_id does not identify (connective, quantifier semantics, operands)");

  const agg = bundle.aggregate ?? {};
  vocab(agg, GRAMMAR.aggregate, "aggregate");
  /* HASHED, SO CHECKED. `child_verdicts` went into composeAggregateId and was
     compared to nothing: flipping every value from VERIFIED to REFUSED and
     resealing left the composition VERIFIED. It is the cleanest witness in the
     tree for `authentication is not verification`. */
  if (JSON.stringify(agg.child_verdicts) !== JSON.stringify(verdicts))
    refuse("compose-count-inconsistent",
      `aggregate.child_verdicts says ${JSON.stringify(agg.child_verdicts)}, this checker ` +
      `derives ${JSON.stringify(verdicts)}`);
  if (agg.operands !== operands.length)
    refuse("compose-count-inconsistent", `aggregate says ${agg.operands} operands over ${operands.length}`);
  if (agg.children_carried !== children.length)
    refuse("compose-count-inconsistent",
      `aggregate says ${agg.children_carried} children carried over ${children.length}`);
  if (agg.children_verified !== verified)
    refuse("compose-count-inconsistent",
      `aggregate says ${agg.children_verified} verified, this checker counts ${verified}`);
  if (agg.leaf_receipts_rederived_by_parent !== 0)
    refuse("compose-count-inconsistent",
      `the parent claims to have re-derived ${agg.leaf_receipts_rederived_by_parent} leaf receipts; ` +
      `a composition that flattens its children is a bigger leaf, not a composition`);
  if (safe(() => composeAggregateId(agg)) !== agg.aggregate_id)
    refuse("compose-count-inconsistent", "aggregate_id does not identify the aggregate beside it");

  /* THE CONJUNCTION. Stated as arithmetic so a partial conjunction cannot pass:
     every operand must have been verified, by its own checker, this run. */
  if (claim.connective === "CONJUNCTION" && verified !== operands.length)
    refuse("compose-child-refused",
      `the claim is a CONJUNCTION of ${operands.length} child claims and ${verified} are verified`);

  const evidence_verdict = refusals.length === 0 ? "VERIFIED" : "REFUSED";
  if (agg.composed_verdict !== evidence_verdict)
    refusals.push({ code: "compose-count-inconsistent",
      detail: `bundle says ${agg.composed_verdict}, this checker computes ${evidence_verdict}` });
  // ok === (verdict === "VERIFIED"), always — and this checker is the one that
  // ASKS a child for both, so the ambiguity it used to publish was its own.
  return publicResult({ refusals, measured, evidence_verdict });
}

const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN) {
  if (!existsSync(BUNDLE)) {
    console.log(`COMPOSE-CHECK: FAIL — no composed certificate at ${BUNDLE} (make gov-proof builds it).`);
    process.exit(1);
  }
  const b = JSON.parse(readFileSync(BUNDLE, "utf8"));
  const r = checkComposeBundle(b);
  console.log("═".repeat(96));
  if (!r.ok) {
    for (const x of r.refusals.slice(0, 12)) console.log(`  ${x.code}: ${x.detail}`);
    if (r.refusals.length > 12) console.log(`  … and ${r.refusals.length - 12} more`);
    console.log(`COMPOSE-CHECK: FAIL — ${r.refusals.length} refusal(s); ` +
      `[${[...new Set(r.refusals.map((x) => x.code))].join(", ")}]`);
    process.exit(1);
  }
  const m = r.measured, c = b.claim;
  console.log(`COMPOSE-CHECK: PASS — COMPOSED CERTIFICATE VERIFIED. ${m.operands}-operand ` +
    `${c.connective} over ${m.distinct_child_protocols} distinct child protocols: ` +
    `${c.operands.map((o) => o.protocol).join(" ∧ ")}. EACH CHILD WAS JUDGED BY ITS OWN CHECKER — ` +
    `${m.children_verified}/${m.operands} returned VERIFIED — and THIS checker re-derived ` +
    `${m.leaf_receipts_rederived_here} leaf receipts and replayed ${m.films_replayed_here} films of ` +
    `its own, which is the artifact's whole content: it imports no kernel, no emitter and no ` +
    `decoder, so a composition that quietly flattened its children back into 138 films could not be ` +
    `written in this file. EVERY CITATION IS RECOMPUTED FROM THE CARRIED CHILD, never read, and ` +
    `compared FIELD BY FIELD — protocol, claim id and aggregate id — because agreeing on a hash is ` +
    `not agreeing about what it names. AND THE CITATION IS CLAIM-QUALIFIED, WHICH IS THE POINT: a ` +
    `bare aggregate_id is NOT a certificate, measured — replacing P1's proposition with a different ` +
    `one moves bounded_claim_sem_id and leaves aggregate_id BYTE-IDENTICAL, because an aggregate ` +
    `commits to what was measured and not to what was claimed. verified_claim_sem_id binds ` +
    `protocol, claim, aggregate and chain ids together. A CITATION IS STILL NOT A WARRANT: there is ` +
    `no registry of accepted certificates in this tree, so both child bundles travel inside this ` +
    `one and both child checkers run every time. SCOPE: this is the CONJUNCTION of ${m.operands} ` +
    `cited bounded claims and nothing else — not a new theorem, not transitive, and not a claim ` +
    `that a composed certificate may itself be cited by a fourth artifact.`);
  console.log(`  composed claim ${c.composed_claim_sem_id}`);
  for (const o of c.operands)
    console.log(`    ∧ ${o.protocol.padEnd(30)} ${o.verified_claim_sem_id.slice(0, 28)}… ` +
      `→ ${m.child_verdicts[o.verified_claim_sem_id]}`);
}
