/* ═══════════════════════════════════════════════════════════════════════════
   schema.mjs — v0.1.0 — THE CHECKER OWNS THE GRAMMAR
   law:proof.semantic-vocabulary-closed@1

   P1.1 stopped the claimant defining SCOPE. P2.1 stopped it defining ABSENCE.
   P3 stopped it defining WHAT A CITATION IS ABOUT. Each time the repair was the
   same: the checker declares the semantics it implements and compares.

   And each time the repair owned the VALUES OF KNOWN FIELDS, never the FIELD
   SET. So the fourth form of the defect was still open, and it is the cheapest
   of the four to exploit — you do not have to change anything the checker looks
   at. You add something it does not:

       claim.scope.proves_all_naturals        = true   →  VERIFIED
       claim.scope.proves_all_integers        = true   →  VERIFIED
       claim.scope.transitive                 = true   →  VERIFIED
       claim.parent_may_be_cited_as_warrant   = true   →  VERIFIED
       operand.entails = "EVERYTHING"                  →  VERIFIED
       refusal_witness.also_proves = "…"               →  VERIFIED

   All eight reproduced against the shipped P3 pack before a line of this file
   existed. Every one reseals cleanly, because the identity hashes whatever is
   there — so the forged field is not merely accepted, it is AUTHENTICATED.

   THE LAW, and it is a strengthening of B6.3 rather than a new idea:

       AUTHENTICATION IS NOT VERIFICATION. A field being inside a hash is
       meaningless unless the verifier derives it, checks it, or explicitly
       classifies it as non-semantic.

   B6.3 said *a hashed field is a value the code reads, or it is not hashed*,
   and read it as a rule about PROSE. It is a rule about VOCABULARY: the set of
   fields a semantic record may contain is part of the protocol, and a producer
   that can add to it can say things the checker never agreed to.

   So every machine-semantic record is checked against an EXACT key set:
   everything required is present, and nothing else is there at all. Extending
   the vocabulary is a protocol revision, not a field.

   WHAT THIS FILE IS NOT. It holds no schemas. The grammar of each protocol is
   declared inside that protocol's CHECKER, unimported, for the same reason
   IMPLEMENTED_SCOPE and IMPLEMENTED_REFUSAL_CONTRACT are — a checker that read
   its own vocabulary out of the generator would be back where P1.1 started.
   This module is the comparison, the way `canonicalBytes` is the encoding.
   ═══════════════════════════════════════════════════════════════════════════ */
import { canonicalBytes } from "./derive_protocol.mjs";


/** THE INGRESS BOUNDARY — law:proof.verifier-input-owned@1.
 *
 *  Every checker in this tree took a caller's JavaScript OBJECT and read it
 *  repeatedly. A getter is enough to make that unsound, and it was measured on
 *  two protocols at once against the shipped P4.1 pack:
 *
 *      references.contract.address_is_a_warrant  →  false, then true
 *      checkNestBundle → VERIFIED, and the same object then serialises
 *      with address_is_a_warrant = true
 *
 *      claim.scope.generalizes_beyond_domain     →  false for 3 reads, then true
 *      checkBundle → VERIFIED, and the object then says an UNBOUNDED scope
 *
 *  P4.1 already snapshotted everything it fetched from the store and then
 *  stopped touching it. The ROOT input had no equivalent transition, so the one
 *  object a verifier is handed directly was the one object it did not own.
 *
 *  So: canonicalise ONCE — which reads every field exactly once, and it is THAT
 *  read the verdict is about — and re-parse into plain data this verifier owns.
 *  Getters, proxies, prototypes and shared references are all severed by the
 *  round trip. Throws on anything with no canonical form, which callers turn
 *  into a named `*-ingress-refused` rather than a stack trace. */
export function ownSnapshot(value) {
  return JSON.parse(canonicalBytes(value));
}

/** Exact-key-set comparison for one record.
 *
 *  `required` must all be present. `optional` may be. ANYTHING ELSE IS A
 *  VIOLATION — that is the whole point, and it is why this returns unknown keys
 *  rather than only missing ones.
 *
 *  Returns [] for a conforming record. Never throws: every byte it reads comes
 *  from an untrusted producer, and a grammar checker that crashed on a
 *  malformed record would be refusing by stack trace. */
export function grammar(record, { required = [], optional = [] } = {}, where = "record") {
  if (record === null || typeof record !== "object" || Array.isArray(record))
    return [{ where, key: null, problem: "not-a-record",
      detail: `${where} is ${Array.isArray(record) ? "an array" : typeof record}, not a record` }];
  const known = new Set([...required, ...optional]);
  const out = [];
  for (const k of Object.keys(record))
    if (!known.has(k))
      out.push({ where, key: k, problem: "unknown",
        detail: `${where}.${k} is not in this checker's vocabulary — a semantic field the ` +
          `checker does not implement is a claim it never agreed to. Extending the vocabulary ` +
          `is a protocol revision; annotations belong outside the semantic record` });
  for (const k of required)
    if (!Object.prototype.hasOwnProperty.call(record, k))
      out.push({ where, key: k, problem: "missing",
        detail: `${where}.${k} is required by this checker's vocabulary and absent` });
  return out;
}

/** THE PUBLIC RESULT, AND ITS ONE INVARIANT: `ok === (verdict === "VERIFIED")`.
 *
 *  All three checkers used to compute `verdict` BEFORE appending the refusal
 *  raised by a forged aggregate verdict, so a bundle whose evidence checked out
 *  but whose stored verdict said REFUSED came back
 *
 *      { ok: false, verdict: "VERIFIED" }
 *
 *  Reproduced on P1, P2 and P3 alike. Inside one checker that is merely ugly;
 *  under nesting it is a defect waiting to happen, because a parent asking a
 *  child `verdict === "VERIFIED"` and a parent asking `ok === true` would
 *  disagree about the same child. `compose_check` happens to ask both, which is
 *  luck rather than design.
 *
 *  The distinction the old shape was reaching for is real and is kept, under a
 *  name that cannot be mistaken for the verdict: `evidence_verdict` is what the
 *  evidence computed to BEFORE the envelope checks — useful for saying WHY a
 *  bundle failed, never for deciding whether it passed. */
export function publicResult({ refusals, measured = {}, evidence_verdict = null }) {
  const list = Array.isArray(refusals) ? refusals : [];
  const verdict = list.length === 0 ? "VERIFIED" : "REFUSED";
  return {
    ok: list.length === 0,
    verdict,
    // null when nothing distinguished them, so a reader is not invited to
    // compare two fields that agree by construction.
    evidence_verdict: evidence_verdict === verdict ? null : evidence_verdict,
    refusals: list,
    measured,
  };
}
