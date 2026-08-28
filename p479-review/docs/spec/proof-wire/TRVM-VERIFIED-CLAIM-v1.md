# TRVM-VERIFIED-CLAIM-v1 — the citable identity of a verified claim

**Status: NORMATIVE.** Depends on `TRVM-PROOF-WIRE-v1.md` §1 for the canonical encoding.

This document exists because a blind implementation could not be written without it. `TRVM-NESTED-COMPOSITION-v2.md` §4.2 says an operand names a child by its `verified_claim_sem_id` and that an artifact which cannot produce all four bound values *cannot be cited at all* — and then did not say how the value is computed. That is a specification gap, recorded as one, and this is its repair.

---

## 1. What a citation names

An operand of a composing protocol does **not** name an artifact. It names a **verified claim**: a claim, the evidence aggregate that established it, and the compiler chain both were produced under, bound together.

This is not a stylistic choice and it was measured. A bare `aggregate_id` is **not** a certificate: replacing a bounded proof's proposition with a completely different one moves its claim identity and leaves its `aggregate_id` **byte-identical**, because an aggregate commits to what was *measured* and not to what was *claimed*. A composition over bare aggregate ids would be citing "sixty-four cases went like this" and calling it a theorem.

---

## 2. The formula

```
verified_claim_sem_id =
  "vclaim-" ++ lowercase-hex( SHA-256(
      "TRVM-VERIFIED-CLAIM-v1|" ++ canonical_bytes({
          certificate_protocol: "TRVM-VERIFIED-CLAIM-v1",
          protocol:      <the child artifact's own protocol string>,
          claim_sem_id:  <the child's claim identity>,
          aggregate_id:  <the child's evidence aggregate identity>,
          chain_ids:     <the child's compiler chain record>
      }) ) )
```

`canonical_bytes` is `TRVM-PROOF-WIRE-v1.md` §1 — RFC 8785 over the object, UTF-8. The domain-separation prefix `"TRVM-VERIFIED-CLAIM-v1|"` is part of the preimage. Note that `certificate_protocol` appears **both** as the prefix and as a member of the hashed object; that is the shipped preimage and an implementation MUST reproduce it exactly.

**2.1. All four inputs are required.** An absent one MUST be a refusal and MUST NOT be hashed as a missing member. `SHA-256` of an object with a member omitted is a perfectly good hex string that composes fine and names nothing — that is what made a composed certificate silently uncitable before it made it loudly uncitable.

**2.2. `claim_sem_id` is protocol-specific and the CITER decides where to find it.** Which member of a child artifact holds its claim identity is **protocol semantics belonging to the composing checker**, not to the child. A composer that let an artifact tell it which member to read would let the artifact choose which of its own hashes to be judged on.

The mapping for the protocols currently defined:

| child protocol | claim member | composed |
|---|---|---|
| `TRVM-BOUNDED-PROOF-v1` | `claim.bounded_claim_sem_id` | no |
| `TRVM-BOUNDED-DOMAIN-PROOF-v1` | `claim.domain_claim_sem_id` | no |
| `TRVM-NESTED-COMPOSITION-v2` | `claim.nested_claim_sem_id` | yes |

`aggregate_id` is read from `aggregate.aggregate_id` and `chain_ids` from the artifact's top-level `chain_ids` for every protocol above.

---

## 3. The properties this identity has, and the ones it does not

**3.1. It MOVES when the claim moves, when the evidence aggregate moves, and when the compiler chain moves.**

**3.2. It HOLDS when anything non-authoritative is reworded.** Annotations, scope prose and generator notes are outside all four bound values. Editing them changes the artifact's **address** (`TRVM-PROOF-WIRE-v1.md` §2) and not its **name**. An operand therefore carries one stable name and one brittle one, and they answer different questions.

**3.3. IT IS NOT A WARRANT.** Nothing in this identity records that any checker ever accepted anything: there is no registry, no signature and no verdict in the preimage. It NAMES a claim-plus-evidence pair; it does not assert that the pair checks out. A composer receiving one and trusting it would have invented a certificate authority out of a hash. Whoever cites it MUST still run the child's own checker.

---

## 4. Known-awkward, and deliberately not repaired

`chain_ids` is required by §2.1, so a composed artifact must carry one to be citable. Its content is defined by `TRVM-NESTED-COMPOSITION-v2.md` §5 as the flat set of its direct children's chain records.

**That set is measured to be redundant for binding.** A child's own `verified_claim_sem_id` already binds its chain, and an operand binds that certificate, so a leaf compiler change propagates into every ancestor's claim identity **without** the parent carrying a chain set at all. Its only surviving role is satisfying §2.1.

This is almost certainly telling us the abstraction is wrong — a successful checker should derive a *citation subject* rather than every composer knowing where four values live in every child protocol. **It is documented rather than redesigned on purpose**: an independent implementation reading this document is the cheapest available evidence that the current interface is describable, and that evidence is worth more before the redesign than after it. The awkwardness is data.
