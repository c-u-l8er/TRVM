# TRVM-NESTED-COMPOSITION-v2 — a proof DAG over a content-addressed store

**Status: NORMATIVE.** Depends on `TRVM-PROOF-WIRE-v1.md`, which defines the wire, the content
address, resolution, input ownership and resource policy. This document defines one proof protocol
carried on it.

Conformance vectors: `vectors/manifest.json`.

---

## 1. What the protocol is for

A nested composition asserts the **conjunction** of the claims named by its operands, and nothing
else. It carries none of them: each is named by a content address and resolved from an untrusted
store.

The theorem is deliberately trivial. What the protocol is for is the **shape** — a proof DAG whose
shared nodes are stored once and whose every node is judged by the checker of its own protocol.

---

## 2. Six planes, and none of them stands in for another

An artifact of this protocol has exactly these members. Every one is required except the three marked
non-semantic.

| member | plane | answers |
|---|---|---|
| `protocol` | CHECKED | which protocol this is |
| `claim` | semantic | WHAT is asserted |
| `chain_ids` | derived | UNDER WHICH COMPILERS |
| `references` | transport | WHERE THE OCTETS ARE |
| `aggregate` | evidence | WHAT EVIDENCE HOLDS |
| `structure` | shape | WHAT SHAPE THE DAG IS |
| `type`, `version`, `annotations` | NON-SEMANTIC | nothing |

A sixth plane — **verifier execution**, how many times a checker ran and whether it reused a
derivation — is **not in the artifact at all**. It is a property of a verification run, no artifact
can be right about it, and placing it in the claim or the aggregate means a sound verifier changing
*strategy* renames the theorem.

**2.1. `claim.operands` MUST NOT contain an address.** A locator may rename the artifact carrying a
proof; it MUST NOT rename the proof. An implementation that binds `artifact_root` into the claim
identity will find that rewording a non-semantic annotation on a leaf renames the theorem at every
level above it.

**2.2. What an artifact may state about its own shape MUST be strategy-independent.** `edges` and
`films_below_by_edge_multiplicity` are properties of the DAG. `checker_evaluations` is not.

**2.3. `annotations` establishes nothing.** It is bounded to strings, arrays of strings, and flat
records of those. It is inside the artifact root — so editing it changes the artifact's *address* —
and it is outside every semantic identity, so editing it changes no claim, aggregate or certificate.

---

## 3. Records

`protocol` is the string `TRVM-NESTED-COMPOSITION-v2`.

```
bundle      = { protocol, claim, chain_ids, references, aggregate, structure,
                type?, version?, annotations? }
claim       = { connective, scope, operands, nested_claim_sem_id }
scope       = { kind, quantifier, generalizes_beyond_children,
                children_rechecked_by_their_own_checkers, parent_rederives_leaf_evidence }
operand     = { protocol, claim_sem_id, aggregate_id, verified_claim_sem_id }
references  = { contract, operands }
contract    = { resolution, wire, address_is_a_warrant }
reference   = { verified_claim_sem_id, artifact_root }
chain_ids   = { leaf_chains }
aggregate   = { operands, child_verdicts, leaf_receipts_rederived_by_parent,
                films_replayed_by_parent, nested_verdict, aggregate_id }
structure   = { edges, unique_artifacts, max_depth_below, bytes_if_inlined, unique_bytes,
                films_below_by_edge_multiplicity, films_below_distinct,
                cases_below_by_edge_multiplicity, cases_below_distinct, structure_sem_id }
```

**3.1. The key sets are EXACT.** A member not listed for a record is a refusal. This is not a
convenience: a producer that can add a member can state things the checker never agreed to without
altering any value the checker reads. Extending the vocabulary is a protocol revision.

**3.2. The checker owns the vocabulary.** An implementation MUST declare these key sets itself and
MUST NOT read them from the artifact.

**3.3. Values the checker declares** (`CHECKED` — compared against the implementation's own copy,
never read from the artifact):

```
scope.kind                                      "NESTED_COMPOSED_VERIFIED_CLAIM_CONJUNCTION"
scope.quantifier                                "OVER_CITED_CHILD_CERTIFICATES"
scope.generalizes_beyond_children               false
scope.children_rechecked_by_their_own_checkers  true
scope.parent_rederives_leaf_evidence            false
references.contract.resolution                  "CONTENT_ADDRESSED"
references.contract.wire                        "CANONICAL"
references.contract.address_is_a_warrant        false
claim.connective                                one of ["CONJUNCTION"]
```

A scope value that is a string containing whitespace is a refusal: explanatory prose does not belong
in a machine-readable value.

---

## 4. Identities

All three use the canonical encoding of `TRVM-PROOF-WIRE-v1.md` §1 and a domain-separation prefix
that is part of the preimage.

```
nested_claim_sem_id = "nclaim-" ++ hex(SHA-256(
    "TRVM-NESTED-COMPOSITION-v2|" ++ canonical_bytes({
        protocol: "TRVM-NESTED-COMPOSITION-v2", connective, scope, operands })))

aggregate_id        = "nagg-"   ++ hex(SHA-256(
    "TRVM-NESTED-COMPOSITION-v2|" ++ canonical_bytes(aggregate WITHOUT aggregate_id)))

structure_sem_id    = "nstruct-" ++ hex(SHA-256(
    "TRVM-NESTED-COMPOSITION-v2|" ++ canonical_bytes(structure WITHOUT structure_sem_id)))
```

**4.1.** `nested_claim_sem_id` binds the operand **sequence**. Two artifacts differing only in operand
order are different claims.

**4.2.** The certificate identity of a child, `verified_claim_sem_id`, is defined by the certificate
protocol and binds `(protocol, claim_sem_id, aggregate_id, chain_ids)` together. An artifact that does
not carry all four **cannot be cited at all** — this is *citability*, and it comes before identity,
availability and warrant.

---

## 5. The chain is derived, never declared

```
chain_ids(leaf)     = the leaf's own chain record
chain_ids(composed) = { leaf_chains: the flat, deduplicated set of its DIRECT
                        children's chain records, canonically ordered }
```

**5.1.** A composed child's set is already flat, so it never grows with depth and a parent reads only
its direct children. It is O(distinct compilers), not O(evidence); this is not flattening.

**5.2.** `leaf_chains` is compared as a **SET**. Order is not part of the protocol.

**5.3.** A producer MUST NOT write its own chain. A producer that could would be naming the compiler
its own proof was checked under.

---

## 6. Verification

Three phases, in this order.

**6.1. RESOLVE.** Walk `references.operands` from the root, resolving each cited root per
`TRVM-PROOF-WIRE-v1.md` §3 into a snapshot the verifier owns. Every resource bound is decided here.
When resolution completes, the store MUST NOT be consulted again.

- each unique root is resolved once;
- a root already on the current path is a cycle refusal;
- for each edge, `depth + 1 + height(child)` MUST NOT exceed the depth bound (§6 of the wire spec);
- resolution count, total resolved octets and per-node operand counts are all bounded, and **both**
  `claim.operands` and `references.operands` are bounded before either is iterated.

**6.2. JUDGE.** Each **distinct** artifact in the snapshot is handed to the checker of its own
protocol. A verifier MAY reuse a judgment it derived itself in this run; the verdict and the refusal
set MUST be identical to recomputation.

**6.3. WALK.** For every operand:

- exactly one reference names the same `verified_claim_sem_id` — the two planes are matched as **SETS**,
  not by position;
- the resolved artifact's certificate is **recomputed** and compared to the citation field by field,
  because agreeing on a hash is not agreeing about what the hash names;
- the child's verdict is VERIFIED.

Then: operands are pairwise distinct by certificate at this node (the same artifact reached by two
different **paths** is the diamond and is what the protocol is for); `nested_claim_sem_id`,
`aggregate_id` and `structure_sem_id` are recomputed; and **every** member of `aggregate` and
`structure` is derived and compared.

**6.4. There is no fourth category.** Every member of every record is DERIVED (the checker computes
the value itself), CHECKED (compared against a value the checker declares), or NON-SEMANTIC (nothing
depends on it). A member that is hashed and read by nothing is not evidence — `nested_verdict` was
exactly that, and an artifact stating of itself that it was REFUSED verified.

---

## 7. Refusal vocabulary

An implementation MUST use these codes. Conformance on negative vectors is compared as a **SET**;
refusal precedence is **not** part of this protocol and MUST NOT be relied on.

```
nest-ingress-refused              the artifact handed in has no canonical form
nest-protocol-mismatch            not a nested composition
nest-vocabulary-unknown           a member this checker's grammar does not have
nest-scope-mismatch               scope is not the one this checker implements
nest-reference-contract-mismatch  the transport contract is not this one
nest-connective-unsupported       a connective this checker cannot evaluate
nest-operand-malformed            an operand missing a field a citation needs
nest-operand-duplicated           the same certificate cited twice at one node
nest-reference-mismatch           references and operands do not name the same set
nest-artifact-root-malformed      a citation that is not a well-formed root
nest-artifact-unresolvable        the store has no octets under a cited root
nest-artifact-invalid-utf8        the octets are not valid UTF-8
nest-artifact-malformed           the octets do not parse, or have no canonical form
nest-artifact-non-canonical       the octets are not the canonical encoding of what they parse to
nest-artifact-root-mismatch       the octets are not the artifact that was cited
nest-child-protocol-unsupported   a child protocol with no checker here
nest-child-refused                a child's OWN checker did not return VERIFIED
nest-certificate-stale            the recomputed certificate id is not the one cited
nest-citation-cross-wired         the id is right and the claim or aggregate it names is not
nest-chain-ids-mismatch           the stored chain set is not the one the children give
nest-claim-id-mismatch            nested_claim_sem_id is not over these operands
nest-count-inconsistent           an aggregate member this checker derives otherwise
nest-structure-mismatch           a structural member this checker derives otherwise
nest-depth-exceeded               a citation chain past the policy ceiling
nest-budget-exceeded              octets, resolutions or operands past the policy ceiling
nest-cycle                        a root cited by one of its own ancestors
nest-policy-weakened              a caller asked for a policy looser than the shipped one
nest-checker-threw                the checker raised instead of refusing
```

`nest-cycle` is **defence in depth and not load-bearing**: sealing a cycle requires octets that hash
to a root those octets already contain. That was not achieved in a bounded experiment of 512
attempted fixpoints; it is *assumed computationally infeasible* under the hash model and is **not**
proved.

---

## 8. What this protocol does not claim

- **Not a new mathematical result.** The conjunction is redundant by design.
- **Not that resolving an address establishes anything about the artifact.**
- **Not a warrant cache.** A verifier may reuse a judgment it derived itself, in this run, over a
  snapshot it owns. Believing a verdict issued elsewhere, or one that outlived a run, is a different
  object and does not exist in this protocol.
- **Not unbounded.** Every dimension an untrusted store controls is bounded by a policy the checker
  owns and a caller may only tighten.
- **Not a claim about how many times anything was checked.**
- **Not transitive in the sense of trust.** A nested composition may cite another, and every artifact
  in the graph is judged by its own protocol's checker regardless of depth.

---

## 9. Open, and deliberately unspecified

These are named so an implementer does not assume they were forgotten:

- **Refusal precedence.** Not decided. Compare sets.
- **Connectives other than CONJUNCTION.** Not specified.
- **A persistent, verifier-issued warrant.** Not specified, and §8 says why.
- **A generic checker-derived citation subject.** `verified_claim_sem_id` is currently defined by the
  certificate protocol and requires `chain_ids`; a composition's flattened `leaf_chains` is
  *redundant for binding* — a child certificate already propagates a compiler change into every
  ancestor's claim id — and load-bearing only for citability. The interface that would replace it is
  not specified here.
- **Full RFC 8785 conformance.** The bundled corpus is not the reference suite.
