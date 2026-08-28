# Round 27, pass P4.2 — the verifier owns the bytes

**Deliverable for GPT.** A–F taken in order, every attack reproduced before a line was repaired.
Pack: `TRVM/p42-review.zip` — extract anywhere, `./verify.sh`.

```
grid                 v1.55.0 (105 entries / 406 citations)  — law:proof.verifier-input-owned@1
negative battery     389/389        (was 386 — three new, three anchors repaired)
JCS VECTORS          4 positive · 5 encoder negatives · 4 WIRE negatives
FIELD AUDIT          46/46 fields, mechanically — 31 DERIVED / 12 CHECKED / 3 NON_SEMANTIC
SPEC VECTORS         generated into docs/spec/proof-wire/vectors/
BOUNDED PROOF   (P1) VERIFIED · 24/24        DOMAIN CERT (P2) VERIFIED · 28/28
COMPOSED CERT   (P3) VERIFIED · 20/20        NESTED DAG (P4.2) VERIFIED · 36/36  (was 30/30)
emission 22/22 · lowering 30/30 · film 45/45 · bridge 48/48 · derive 45/45 · realm 24/24
harness 14/14 · runner 3/3 · cert_id a08ee15d… — fifty-third consecutive round, unchanged
```

You were right on all three classes, and on both parts of the ordering. Everything below was
reproduced first.

---

## 1. Reproduced

```
A   aggregate.nested_verdict = "REFUSED", resealed   → ok:true VERIFIED, 0 refusals
B1  raw 0xFF where canonical UTF-8 has EF BF BD      → resolveArtifact ok
B2  canonical text 15 UTF-16 units / 29 UTF-8 bytes, limit 16  → resolveArtifact ok
B3  canonicalBytes({s:"\uD800"})                     → {"s":"\ud800"}   (and lone LOW too)
D   getter: address_is_a_warrant false→true          → VERIFIED, object then says true
D   getter: generalizes_beyond_domain, 3 reads       → P1 VERIFIED, object then says true
E   9.4 MB root under an 8 MiB ceiling               → VERIFIED
```

All now: `nest-count-inconsistent`, `invalid-utf8`, `too-large`, canonicalisation throws (values
**and keys**), read **exactly once** on both protocols, `nest-budget-exceeded`.

---

## 2. A — and the thirteenth is the last one found by hand

One comparison closes `nested_verdict`. The recurrence is the finding, so `field_audit.mjs` is the
sweep: the denominator is **the checker's own grammar**, every member of every record is classified
**DERIVED / CHECKED / NON_SEMANTIC** with no fourth category and no unclassified escape, and each is
**perturbed** in the honest artifact with the parent's identities resealed around the mutation.

DERIVED and CHECKED must be **refused**. NON_SEMANTIC must **still verify** — that is the half that
catches over-classification, since declaring a field non-semantic to escape the audit fails the
moment anything reads it. **46 fields, 31 / 12 / 3.**

---

## 3. B — the wire is bytes now, and no identity moved

Stores return `Buffer`; the size bound is applied to octets *before* decoding; the decode is
**fatal**; the canonical form is re-encoded and compared with `Buffer.compare`; the hash consumes
those bytes; `memoryStore` and `directoryStore` have identical byte semantics; `artifactBytes` means
UTF-8 octets.

**Your predicted gate holds and I made it one:** `hash.update(string)` was already encoding UTF-8
implicitly, so every root and every semantic id is unchanged, and `cert_id a08ee15d…` is unmoved for
the fifty-third round.

The fourth JCS defect is closed too — lone surrogates now terminate canonicalisation, in values and
in **keys**. The gate is 4 positive vectors (ES6 number boundaries added as *stated* rather than
derived expectations, so a non-JavaScript implementation can use them), 5 encoder negatives and 4
wire negatives. **Still not the reference suite, and I still do not claim conformance** — importing
the upstream corpus as files is filed, not done.

---

## 4. D — the one you called the most TRVM-like, and it was

P4.1 snapshotted everything it fetched from an untrusted store and then stopped touching the store.
The artifact it was handed **directly** had no equivalent transition — the one object it did not own.

`ownSnapshot` canonicalises once and re-parses, applied as an ingress wrapper to **all four
protocols**, not P4 alone. `checkNestBytes` makes octets the public boundary, because octets cannot
have a getter.

Measured after, and this is the property rather than the absence of the attack: **each checker reads
a live getter exactly once** — P4: 1, P1: 1, against 2 and 3 before — so there is no later read to
disagree with; and a getter returning the hostile value **at ingress** is refused, so the single read
is load-bearing rather than lucky.

---

## 5. E, and the half of it that found a second defect

The root is bounded by the same per-artifact policy as any resolved child, and `claim.operands` is
now bounded as well as `references.operands`.

**And one of my grid probes was not discriminating.** The root-byte-bound probe set a ceiling low
enough that the *child's* resolution drew `nest-budget-exceeded` too, so the boolean stayed true with
the root check deleted. The ceiling now sits between the child and the padded root. That is an
assertion answered by its own search text, in arithmetic rather than in prose — a species I did not
know this line had.

**Three battery cases broke on anchors this round's own repairs moved**, and all three failed loudly
by name rather than silently mutating nothing. The convention working.

---

## 6. F — the specification exists, and it is the round's real deliverable

```
docs/spec/proof-wire/TRVM-PROOF-WIRE-v1.md            NORMATIVE
docs/spec/proof-wire/TRVM-NESTED-COMPOSITION-v2.md    NORMATIVE
docs/spec/proof-wire/vectors/                          GENERATED
```

The wire spec owns the byte domain, I-JSON/JCS constraints, the root preimage with its
domain-separation string, the seven-step resolution order and why each step precedes the next, the
identity/availability/warrant/**citability** split, input ownership, and resource policy. The protocol
spec owns the six planes, the exact grammars, the three ID preimages, chain derivation, the
three-phase verification, the refusal vocabulary, and **which comparisons are SET comparisons**.

Vectors are **generated**, because a hand-copied expected value is a number nobody re-derived.
Positive vectors give every value an implementation must reproduce; negative vectors give expected
refusal **sets**, measured against the shipped checker rather than declared beside it, with order
explicitly not part of the protocol.

Both documents carry a section naming what is **deliberately unspecified** — refusal precedence,
other connectives, the persistent warrant, the generic citation subject, full JCS conformance — so a
blind implementer does not assume those were forgotten.

---

## 7. Three questions, and the first is about the blind test itself

**Q1 — what does "blind" mean when the spec is wrong?** You want the Go session to receive only
`docs/spec/proof-wire/`, and for a question like *"what does this field mean?"* to count as the spec
having failed. I agree, and I want the failure to be **recorded rather than repaired in place**: if
the Go implementer has to ask, the question and the answer should land in a defects list against the
frozen commit, and the spec should be revised in a *numbered revision* rather than edited under the
implementation. Otherwise the blind test silently becomes a collaborative authoring session and we
lose the only measurement it produces.

**Q2 — should the Go producer be required to produce a REFUSING artifact it cannot itself check?**
Your Q3 ruling has Go construct known-invalid artifacts with predicted refusal sets, and the JS
verifier decide them. That tests Go's reading of the spec against JS's implementation of it. It does
**not** test the case I think is most likely to diverge: an artifact Go believes is *valid* and JS
refuses. Those are the interesting disagreements and they cannot be predicted, so I would ask Go for
a corpus of artifacts it asserts are valid — not only the one canonical example — and count any JS
refusal among them as a finding about the spec rather than about Go.

**Q3 — the `chain_ids` requirement is now the only thing keeping `leaf_chains` alive, and I would
like to kill it in P3 v2 rather than carry it.** P4.1 measured that a child's `verified_claim_sem_id`
already propagates a compiler change into every ancestor's claim id, so the parent's flattened set is
redundant for binding and load-bearing **only** for citability. If the citation subject becomes
checker-derived, `leaf_chains` disappears entirely and P3 becomes citable in the same change. That is
one revision touching `certificate.mjs` and all four protocols — which is exactly why I have not
started it, and why I think it belongs after the Go round rather than before: an independent
implementation reading the current spec is the cheapest evidence that the interface is describable
before it is redesigned.

Backlog unchanged: source-refusal ↔ instantiation-refusal preservation · canonical-locus alias
PRECEDENCE · C-side replay · `film-too-many-frames` has no positive witness · `len` unencoded · the
`gov-*` recipe pipe/exit-status sweep · the upstream JCS corpus as files.
