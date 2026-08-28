/* ═══════════════════════════════════════════════════════════════════════════
   certificate.mjs — v0.1.0 — THE CLAIM-QUALIFIED CERTIFICATE IDENTITY
   law:proof.bounded-claim@1

   P1 and P2 each end in an `aggregate_id`. The obvious way to compose them is
   for a third artifact to cite those ids. THAT IS WRONG, AND IT IS MEASURABLE.

   Replace P1's proposition with a completely different one — swap
   `x*(y+z) = (x*y)+(x*z)` for `x+(y*z) = (x+y)*z` — recompute
   `proposition_sem_id` and `bounded_claim_sem_id`, and then recompute the
   aggregate:

       bounded_claim_sem_id   bclaim-e21248e0…  →  bclaim-1d362445…   MOVED
       aggregate_id           agg-656940f8…     →  agg-656940f8…      IDENTICAL

   Because `aggregateId` commits to case ids, counts, measurements and the
   verdict — WHAT WAS MEASURED — and to nothing about WHAT WAS CLAIMED. Inside
   P1 that is harmless: `proof_check.mjs` reads the whole bundle and refuses the
   swap on four separate codes. But it means an aggregate id ALONE IS NOT A
   CITATION. "agg-656940f8…" does not say `bounded distributivity over {0,1,2,3}³
   under this compiler`; it says `sixty-four cases went like this`.

   So a citable certificate identity has to bind four things at once:

       protocol       WHICH proof protocol's checker accepted it
       claim_sem_id   WHAT was claimed          (the thing aggregate_id omits)
       aggregate_id   WHAT EVIDENCE established it
       chain_ids      UNDER WHICH COMPILER

   and the properties that makes it worth citing are:

       change the claim              → the certificate id MOVES
       change the evidence aggregate → the certificate id MOVES
       change the semantic chain     → the certificate id MOVES
       reword notes or provenance    → the certificate id HOLDS

   WHAT THIS IS NOT. It is not a trust token. Nothing in this file records that
   a checker ever accepted anything — there is no registry, no signature, and no
   verdict in the hash. `verified_claim_sem_id` NAMES a claim-plus-evidence
   pair; it does not assert that the pair checks out. A composer that received
   one and trusted it would have invented a certificate authority out of a hash.
   Whoever cites it must still run the child's own checker — see
   `compose_check.mjs`, which does exactly that and measures that it re-derived
   no leaf receipts of its own.

   AND THE CLAIM FIELD IS THE CITER'S TO KNOW. `claim_sem_id` is the P1 or P2
   claim identity, and which field of a child bundle holds it is PROTOCOL
   SEMANTICS. This file takes it as an argument and never looks it up, so a
   bundle cannot tell a composer where to find its own claim id.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { canonicalBytes } from "./derive_protocol.mjs";

export const CERTIFICATE_PROTOCOL = "TRVM-VERIFIED-CLAIM-v1";
const H = (s) => createHash("sha256").update(s).digest("hex");

/** The claim-qualified identity of a verified bounded claim. Every argument is
 *  required; an absent one is a refusal rather than a hole in the hash, because
 *  `H(undefined)` is a perfectly good hex string and would compose fine. */
export function verifiedClaimSemId({ protocol, claim_sem_id, aggregate_id, chain_ids }) {
  for (const [k, v] of Object.entries({ protocol, claim_sem_id, aggregate_id }))
    if (typeof v !== "string" || v.length === 0)
      throw new Error("certificate-incomplete: " + k);
  if (!chain_ids || typeof chain_ids !== "object")
    throw new Error("certificate-incomplete: chain_ids");
  return "vclaim-" + H(CERTIFICATE_PROTOCOL + "|" + canonicalBytes({
    certificate_protocol: CERTIFICATE_PROTOCOL, protocol, claim_sem_id, aggregate_id, chain_ids }));
}

/** Read a child bundle's certificate triple, given the field the CALLER says
 *  holds that protocol's claim identity. Returns the four bound values so a
 *  caller can compare them to a citation field by field — a citation that
 *  agrees on the id but disagrees on the claim it names is a cross-wire, and
 *  only a field-by-field comparison sees it. */
export function certificateOf(bundle, claim_field) {
  return {
    protocol: bundle?.protocol,
    claim_sem_id: bundle?.claim?.[claim_field],
    aggregate_id: bundle?.aggregate?.aggregate_id,
    chain_ids: bundle?.chain_ids,
  };
}
