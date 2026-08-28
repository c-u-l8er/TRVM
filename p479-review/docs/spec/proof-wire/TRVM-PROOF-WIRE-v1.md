# TRVM-PROOF-WIRE-v1 — the canonical wire and the content address

**Status: NORMATIVE.** This document defines the byte-level substrate every TRVM proof protocol
travels on. It is written to be implemented from, by someone who has not read the JavaScript. Where
it says MUST, an implementation that does otherwise is not conformant.

Conformance vectors: `vectors/manifest.json` beside this file. An implementation that has not
reproduced them has not implemented this document.

**What this document does not do.** It does not define any proof protocol. It defines the wire those
protocols are carried on, the identity of an artifact, and what a store is allowed to be asked.
`TRVM-NESTED-COMPOSITION-v2.md` is one protocol built on it.

---

## 1. The wire is bytes

An **artifact** is a JSON value. A **wire artifact** is a sequence of octets.

1.1. The canonical encoding of an artifact MUST be **RFC 8785 (JCS)** applied to that value, encoded
as **UTF-8**. Call the result its *canonical bytes*.

1.2. Everything that measures, compares, addresses or transmits an artifact MUST operate on canonical
bytes. In particular a byte budget MUST count octets. Counting UTF-16 code units, host-language
string length, or characters is non-conformant: a 29-octet artifact measured 15 that way, and passed
a ceiling of 16.

1.3. RFC 8785 constrains its input to I-JSON. This document adds no exceptions and removes none. In
particular:

- An object MUST NOT contain duplicate member names. Behaviour on duplicates is unspecified across
  JSON parsers (RFC 8259), which makes a duplicate a *cross-implementation* hazard rather than a
  formatting one: an implementation that keeps the first and an implementation that keeps the last
  verify different objects while believing they verified the same artifact.
- A string containing a lone surrogate — an unpaired UTF-16 high or low surrogate — has **no**
  canonical form. Canonicalisation MUST terminate with an error. This applies to member **names** as
  well as to values; a name is a string.
- A number that is not finite has no canonical form. Canonicalisation MUST terminate with an error.

1.4. Number serialisation MUST follow ECMA-262 `Number::toString` as RFC 8785 requires. See the
`es6-number-boundaries` vector, whose expected strings are stated rather than derived from any
implementation, for the cases where a naive formatter diverges.

1.5. Member ordering MUST be by **UTF-16 code unit**, not by code point. These differ. U+1F602 is the
surrogate pair `D83D DE02`; by code unit it sorts *before* U+FB33, and by code point it sorts after.
The `jcs-utf16-code-unit-order` vector is the only one in the corpus that separates the two, and an
implementation that sorts code points passes every other vector.

---

## 2. The content address

2.1. The **artifact root** of an artifact is

```
root-  ||  lowercase-hex( SHA-256( "TRVM-ARTIFACT-ROOT-v2|" ++ canonical_bytes ) )
```

where `"TRVM-ARTIFACT-ROOT-v2|"` is those 22 characters encoded as UTF-8 and `++` is octet
concatenation. The domain-separation prefix is part of the preimage and MUST NOT be omitted; a bare
`SHA-256(bytes)` is a different value and is not an artifact root.

2.2. A root MUST match exactly:

```
^root-[0-9a-f]{64}$
```

An implementation MUST validate this **before** a root reaches a filesystem path, a store, a hash, or
any other operation. A citation is untrusted input, and `../proof_bundle` is a perfectly good string:
a store that built a path from one read 1.31 MB from outside itself before anything refused it.

2.3. The root addresses the **bytes**, not a parse result. Hashing a re-encoding of the parsed value
without requiring the received bytes to equal that encoding makes any byte string that parses to the
same value resolve under the same root — pretty-printed and compact forms, respelled numbers,
reordered members, and duplicate names all included.

---

## 3. Resolution

A **store** is anything that answers a root with octets or with nothing. It is **untrusted**. It may
be a directory, a network, or an adversary.

3.1. A store MUST be asked exactly one question — *do you have bytes under this name* — and MUST be
able to give exactly one kind of answer. A store interface that offers a verdict, a trust level, or
an "is this valid" is a registry, not a store, and is out of scope for this document.

3.2. A store MUST NOT answer a name that is not a well-formed root (§2.2).

3.3. `resolve(store, root, limit)` MUST proceed in this order, and MUST NOT reorder these steps:

```
1.  root matches ^root-[0-9a-f]{64}$          else  bad-root-syntax
2.  bytes = store.get(root)                   else  unresolvable
3.  bytes.length <= limit (OCTETS)            else  too-large
4.  text = UTF-8 decode, FATAL                else  invalid-utf8
5.  value = JSON parse of text                else  malformed
6.  canonical = canonical_bytes(value)        else  malformed
7.  canonical == bytes, octet for octet       else  non-canonical-wire
8.  root_of(canonical) == root                else  root-mismatch
                                              then  ok
```

Step 3 precedes step 4 so that an untrusted store cannot choose how much memory a decode costs. Step
4 MUST be fatal: a decoder that substitutes U+FFFD for an invalid octet has made a substitution the
comparison in step 7 can no longer see, and two distinct byte strings become one artifact again.

3.4. Every outcome MUST be **named and returned**, never raised as an exception that escapes. A
verifier whose entire input is hostile does not refuse by stack trace.

3.5. **Duplicate member names are refused by step 7 and require no rule of their own.** Canonical
output emits each name once, so bytes containing a repeat cannot equal the canonical encoding of what
they parse to. An implementation MAY reject duplicates earlier; it MUST NOT rely on doing so instead
of step 7.

3.6. **THE INTERNAL DETECTION STAGE IS NOT PROTOCOL SEMANTICS, AND THE OBSERVABLE OUTCOME IS
PINNED.** Implementations legitimately differ about *where* they notice bad input — a strict JSON
reader may reject a duplicate member name or invalid UTF-8 in the parser, where a permissive one only
discovers it at step 7. Two conforming implementations MUST still report the same outcome for the
same octets:

| the input is | the outcome MUST be |
|---|---|
| not valid UTF-8 | `invalid-utf8` |
| valid UTF-8, and not well-formed JSON | `malformed` |
| well-formed JSON whose value has no canonical form (lone surrogate, non-finite number) | `malformed` |
| well-formed JSON, canonicalisable, and not byte-identical to its canonical encoding — **duplicate member names included** | `non-canonical-wire` |
| canonical, and hashing to a different root than was asked for | `root-mismatch` |

An implementation whose parser refuses a duplicate name at step 5 MUST report `non-canonical-wire`,
not `malformed`. An implementation whose parser refuses invalid UTF-8 as a parse error MUST report
`invalid-utf8`, not `malformed`. Mapping an internal failure to the outcome the protocol names is
part of conformance.

---

## 4. What resolution establishes, and what it does not

4.1. `ok` from §3.3 establishes exactly three things:

- the cited name is a well-formed root;
- the octets returned are the canonical encoding of the value they parse to;
- that value's root is the one that was asked for.

4.2. It establishes **nothing** about whether the artifact is valid, checked, or accepted. These are
four separate concepts and this document supplies only the first three:

```
citability     the artifact carries the fields its citation identity binds
identity       a content hash                — WHICH artifact is meant
availability   a store resolves it           — WHERE the octets came from
warrant        a verifier-owned issuance     — THAT it was ACCEPTED
```

4.3. An implementation MUST NOT treat a successful resolution as acceptance. Whether an artifact
checks out is decided by the checker of that artifact's own protocol, on every citation.

4.4. **A cached verdict is not a property of the bytes.** It is a property of the bytes *and* the
checker *and* its version, so issuing one is an authority decision and is out of scope here. A
verifier MAY reuse a judgment it derived **itself**, within a single top-level verification, over a
snapshot it owns, provided the result is observationally identical to recomputation. It MUST NOT
accept a verdict produced anywhere else.

---

## 5. Verifier input ownership

5.1. A verifier MUST compute its verdict from **one immutable snapshot it owns**, taken at ingress.
After ingress, no semantic check, identity computation, policy decision, measurement or diagnostic
may reread caller-supplied state.

5.2. The preferred public entry point therefore takes **octets**:

```
check<Protocol>Bytes(raw_bytes, ...) → verdict
```

Octets cannot change between reads. An entry point taking a host-language value is permitted provided
it canonicalises **once** and thereafter uses only the resulting owned value; the single ingress read
is the read the verdict is about.

5.3. This is not hypothetical. Against an implementation without §5, a property defined by a getter
returned one value to the verifier's read and another to every later read, and the verifier returned
VERIFIED over an object that afterwards said something it had never accepted.

---

## 6. Resource policy

6.1. A verifier MUST declare its own resource policy and MUST refuse a request to **weaken** it. A
caller MAY request a stricter policy. A weakening request MUST be a named refusal, not a silent
clamp, because a caller that believes it changed a bound and a verifier that ignored it disagree
about what was checked.

6.2. The effective policy MUST carry an identity reported beside the verdict, so a reader can tell
which policy accepted an artifact.

6.3. The **root** artifact — the one handed to the verifier directly — is subject to the same
per-artifact bounds as any artifact fetched from a store. An implementation that bounds only what it
resolved has left the one artifact it did not choose unbounded.

6.4. A bound on citation-chain length is a bound on the **height** of the artifact graph, not on the
depth of any particular traversal. An implementation whose traversal descends only into some node
kinds reaches a smaller number than the longest path and will accept a graph taller than its own
stated bound.

---

## 6A. Derived values an implementation must reproduce

Two values are computed by the verifier rather than read, and a blind implementation needs both.

**6A.1. The verifier policy identity.**

```
verifier_policy_id =
  "nestpol-" ++ lowercase-hex( SHA-256(
      "<protocol string>|" ++ join("|", sorted-by-name( name ++ "=" ++ JSON(value) )) ) )
```

over every member of the **effective** policy, sorted by member name, where `JSON(value)` is the
RFC 8785 encoding of that scalar. The protocol string is the composing protocol's own — for
`TRVM-NESTED-COMPOSITION-v2` it is that literal. The shipped policy values are in
`schema/nested-composition-v2.json` under `constants.verifier_policy` and in the frozen vector
manifest under `verifier_policy`.

**6A.2. Aggregate and structure derivations.** Every member of both records is computed by the
verifier and compared; `TRVM-NESTED-COMPOSITION-v2.md` §3 lists them and §6.3 says when. The
arithmetic is:

```
aggregate.operands                            number of claim.operands
aggregate.child_verdicts                      { verified_claim_sem_id → verdict } for each operand
aggregate.leaf_receipts_rederived_by_parent   0    (structural)
aggregate.films_replayed_by_parent            0    (structural)
aggregate.nested_verdict                      VERIFIED iff every operand's child verified

structure.edges                     citations below this node, counted with multiplicity
                                    through the unfolded tree
structure.unique_artifacts          distinct artifact roots below this node
structure.max_depth_below           height of the subtree below this node
structure.bytes_if_inlined          sum of canonical octet lengths, with multiplicity
structure.unique_bytes              sum of canonical octet lengths over distinct roots
structure.films_below_*             leaf film counts, by edge multiplicity and over distinct
                                    artifacts; both strategy-independent
structure.cases_below_*             the same for leaf case counts
```

An implementation MUST NOT place a count of its own evaluations in either record.
`TRVM-NESTED-COMPOSITION-v2.md` §2 says why.

## 7. Conformance

An implementation is conformant with respect to the corpus in `vectors/manifest.json` when:

- for every `wire_positive` entry it produces the recorded `canonical_text`, `canonical_utf8_bytes`
  and `artifact_root`;
- for every `wire_negative` entry it produces the recorded `expect_outcome` from §3.3, given the
  recorded octets under the recorded root.

This is **not** the RFC 8785 reference suite, and passing it does not establish full JCS conformance.
An implementation SHOULD additionally run the upstream JCS corpus.

**The corpus is FROZEN and is the oracle.** It is committed under `vectors/`, carries a
`spec_revision`, and is never regenerated by a verification run — see
`law:proof.conformance-oracle-frozen@1`. An implementation that computes the expected values it is
then judged against has not been tested: changing one implementation-only constant
(`TRVM-ARTIFACT-ROOT-v2` → `…-v999`) while touching no specification moved every expected root and
still reported PASS, before this was closed. Regenerating the corpus requires an explicit, human-run
update naming the new spec revision.
