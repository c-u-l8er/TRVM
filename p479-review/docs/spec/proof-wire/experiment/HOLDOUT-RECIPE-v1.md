# `TRVM-PROOF-WIRE-HOLDOUT-v2` — the recipe grammar

**Status: PROCEDURAL, not normative.** This document does not define the wire protocol. It defines
the language a hidden challenge is written in, so that an implementation can be written against the
language **before the challenges are revealed**.

Everything here is public. The challenges written in it are not.

---

## 1. Why this is published before the reveal

A hidden challenge set that could only be applied by an implementation which had already seen it
would not be a measurement. Worse, if the shape of the input and the shape of the answer were settled
*after* the challenge set was opened, the instrument would have been adjusted in the light of the
thing it was about to measure, and every predicate frozen in the holdout would be worth nothing.

So the split is:

```
PUBLIC   BEFORE the reveal     the recipe operators and their exact semantics
                               the observation grammar (HOLDOUT-OBSERVATION-v1.md)
                               the observation schema
                               a synthetic fixture exercising the whole path

HIDDEN   UNTIL the reveal      which fixtures, which recipes, which predicates,
                               and which values those predicates assert
```

A challenge set is committed by digest in `SPEC-RELEASE.json` (`holdout_commitment`). Scoring is
**refused** if the revealed tree does not match that commitment: a challenge set altered after it was
committed is not a challenge set.

---

## 2. A challenge

```json
{
  "id":         "H0",
  "name":       "short-kebab-case-name",
  "fixture":    { "artifact": "C2", "root": "root-<64 hex>" },
  "recipe":     [ { "op": "…" } ],
  "predicates": [ { "op": "…" } ],
  "note":       "free text, not evaluated"
}
```

`fixture` names ONE starting point, by its content address in the public corpus, and takes exactly
one of two forms:

| form | meaning |
| --- | --- |
| `{"artifact": "<node>", "root": "<address>"}` | start from that node of the frozen DAG |
| `{"leaf": "<protocol>", "root": "<address>"}` | start from that frozen leaf artifact |

The node names `A`, `B`, `C1`, `C2`, `D` are the frozen public DAG of
`TRVM-NESTED-COMPOSITION-v2.md` §9: `C1 = A ∧ B`, `C2 = C1 ∧ A`, `D = C2 ∧ C1`. The `root` is
authoritative; the name is a convenience, and an implementation that resolves the address and gets a
different object has found a disagreement worth reporting, not a typo to work around.

---

## 3. The recipe operators

There are **seven**, and there is no eighth. An unknown operator is a **refusal to score**, never a
skipped step — an adapter that silently ignores what it does not understand reports an observation of
something other than the challenge.

Steps apply **in order**. Unless stated, a step mutates the working artifact in place.

### `IDENTITY`
```json
{ "op": "IDENTITY" }
```
Do nothing. The challenge is about the fixture as it stands.

### `SET`
```json
{ "op": "SET", "path": "artifact.claim.smuggled", "value": true }
```
Set one member to a literal JSON value, creating it if it is absent. The path is dot-separated;
`artifact.` addresses the working artifact and `leaf.` addresses the working leaf. A numeric segment
indexes an array (`references.operands.0.artifact_root`).

**`SET` does not reseal.** Any identity that the specification derives from a member this step
touched is now stale, and whether the checker notices is precisely what some challenges ask.

### `REVERSE`
```json
{ "op": "REVERSE", "path": "artifact.references.operands" }
```
Reverse the array at that path, in place. Used to separate members the specification declares to be a
**set** (§6.3, order not observable) from members it declares to be **ordered** (§4.1, order is part
of the claim).

### `RESEAL`
```json
{ "op": "RESEAL" }
```
Recompute, over the working artifact as it now stands, exactly these three derived identities:

```
claim.nested_claim_sem_id
aggregate.aggregate_id
structure.structure_sem_id
```

and nothing else. In particular `RESEAL` does **not** recompute `artifact_root`, because a root is an
address of bytes rather than a field of a record.

An identity that cannot be recomputed — because the step before it removed a member the formula needs
— is left as it stands and the step continues. A forger cannot always reseal, and that is a fact
about the artifact rather than an error in the adapter.

### `CHECK_WITH_OPTIONS`
```json
{ "op": "CHECK_WITH_OPTIONS", "options": { "max_depth": 1000 } }
```
Present these options to the checker for this challenge's verification. This carries no promise that
they are honoured: a caller asking for a **looser** bound than the checker's own is the subject of
`nest-policy-weakened`, so the expected observation may well be a refusal.

### `WIRE_PREPEND_DUPLICATE_MEMBER`
```json
{ "op": "WIRE_PREPEND_DUPLICATE_MEMBER", "name": "protocol", "value": "EVIL" }
```
Operate on **octets**, not on a parsed object. Take the canonical wire bytes of the fixture, prepend
`{"<name>":"<value>",` in place of the opening brace, and serve the result **under the fixture's own
unmodified root**. The observation is the resolution outcome (§4 of the observation grammar).

This is the one operator that cannot be expressed as a mutation of a parsed value, which is the
reason it exists.

### `RECOMPOSE_DAG`
```json
{ "op": "RECOMPOSE_DAG" }
```
Rebuild the whole public DAG bottom-up from the working leaf — `C1 = A ∧ B`, then `C2 = C1 ∧ A`, then
`D = C2 ∧ C1` — and record the result as the **candidate**, then verify `D`. Used for challenges
about what a change to a leaf does to every name above it.

---

## 4. What an implementation must do with a challenge

```
read the challenge
resolve the fixture by its root in the public corpus
apply every recipe step, in order
emit ONE TRVM-HOLDOUT-OBSERVATION-v1 document
```

and **stop**. The implementation does not evaluate the predicates and does not score itself. The
predicates are evaluated by a scorer that loads no protocol code at all — see
`HOLDOUT-OBSERVATION-v1.md` §6.

---

## 5. The predicate language, for reference

An implementation does **not** need to evaluate these. They are published so that the shape of the
observation is legible: an observation exists to be the left-hand side of one of these.

| op | reads |
| --- | --- |
| `HOLDS` | `path` under `baseline` and under `candidate`; asserts equal |
| `MOVES` | the same two; asserts different |
| `EQ` / `NEQ` | `path` under the observation root, against `value` or `right` |
| `VERDICT_EQ` | `path` under `candidate` |
| `OUTCOME_EQ` | `path` under the observation root |
| `REFUSAL_SET_EQ` | `refusal_set`, as **exact set equality** — never "includes" |
| `LT` | `left` and `right` under the observation root |

`REFUSAL_SET_EQ` is exact by rule. A challenge that expected `includes` would let five unrelated
refusal codes pass unnoticed, and one did until P4.5.

---

## 6. What this document deliberately does not fix

- **The order of a refusal set.** Sets are compared sorted; ordering is not part of the protocol.
- **How an adapter is invoked.** A process writing JSON to a file, or to stdout, is equally fine.
- **What a disagreement means.** A predicate that fails for Go and passes for JavaScript is an
  `UNCLASSIFIED_FINDING` until a human puts it in one of the six categories in
  `BLIND-IMPLEMENTATION-CONTRACT.md` §7. Nothing here assigns blame, and no automatic verdict does.
