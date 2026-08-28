# `TRVM-HOLDOUT-OBSERVATION-v1` — the neutral observation grammar

**Status: PROCEDURAL, not normative.** This is the document format an implementation emits after
applying a challenge recipe. It is the boundary between an implementation and the scorer.

Published **before** any challenge is revealed. See `HOLDOUT-RECIPE-v1.md` §1.

---

## 1. Why the boundary is a document

Until P4.6 the scorer and the JavaScript implementation shared a process. The pure scoring function
knew only the predicate operators, but the executable path was always

```
score(challenge, observeJS(challenge))
```

so there was no way for anything other than JavaScript to be scored, and the claim *the scorer knows
eight operators and no TRVM* was true of a function and false of the program. A second
implementation's observations had nowhere to enter.

A **document** fixes that: each implementation writes one, the scorer reads them, and the scorer
imports no protocol code. What the scorer cannot load, it cannot silently agree with.

---

## 2. The envelope

```json
{
  "type": "TRVM-HOLDOUT-OBSERVATION-v1",
  "implementation": "javascript",
  "spec_release_id": "srel-<64 hex>",
  "observations": { "H0": { … }, "H1": { … } }
}
```

| field | meaning |
| --- | --- |
| `type` | exactly this string; anything else is refused |
| `implementation` | free-form label naming the producer, e.g. `javascript`, `go` |
| `spec_release_id` | the release this run was written against — see the contract §2 |
| `observations` | one entry per challenge, keyed by the challenge `id` |

Two observation documents are only comparable when their `spec_release_id` agree. A scorer that finds
them different **reports it and refuses**, because comparing two implementations of two different
specifications measures nothing.

---

## 3. One observation

Every member is optional. **A member that the recipe did not produce is ABSENT, never `null` and
never a zero value** — an observation asserting `"verdict": null` claims the checker returned nothing,
which is a different fact from not having been asked.

```json
{
  "baseline":    { "<node>": { … }, "leaf": { … } },
  "candidate":   { "<node>": { … }, "leaf": { … } },
  "refusal_set": ["nest-policy-weakened"],
  "resolve":     { "outcome": "non-canonical-wire" }
}
```

`baseline` is the fixture as the corpus holds it. `candidate` is what the recipe produced. A recipe
of `IDENTITY` still yields a `candidate` — the same object, verified.

### 3.1 A node record

```json
{
  "artifact_root":         "root-<64 hex>",
  "nested_claim_sem_id":   "nclaim-<64 hex>",
  "verified_claim_sem_id": "vclaim-<64 hex>",
  "verdict":               "VERIFIED",
  "structure": {
    "edges": 4,
    "unique_artifacts": 3,
    "max_depth_below": 2,
    "bytes_if_inlined": 0,
    "unique_bytes": 0,
    "films_below_by_edge_multiplicity": 266,
    "films_below_distinct": 138,
    "cases_below_by_edge_multiplicity": 144,
    "cases_below_distinct": 80,
    "structure_sem_id": "nstruct-<64 hex>"
  }
}
```

Node names are the frozen DAG's: `A`, `B`, `C1`, `C2`, `D`, plus `leaf` for a leaf fixture. `verdict`
is one of `VERIFIED` or `REFUSED` and appears only on the node that was actually verified.

`structure` is reported **verbatim as the artifact carries it**. An implementation does not
recompute, round, reorder or omit members here; the point of the plane is that two implementations
either derived the same structural facts or did not.

### 3.2 `refusal_set`

```json
"refusal_set": ["nest-citation-cross-wired", "nest-structure-mismatch"]
```

A **sorted array of distinct refusal codes**, and the sortedness is what makes byte equality the same
thing as set equality. A verification that refused nothing emits `[]`. A verification that did not
happen omits the member entirely — those are different observations and a predicate can tell them
apart.

### 3.3 `resolve`

```json
"resolve": { "outcome": "non-canonical-wire" }
```

Present only for a challenge that served octets under an address. `outcome` is the observable
resolution outcome from `TRVM-PROOF-WIRE-v1.md` §3.3 — the *outcome*, not the internal stage at which
a strict parser happened to notice, per §3.6.

---

## 4. How a predicate path resolves

Exactly one root per operator, stated here, with **no fallback chain**. An implementation of the
scorer that tries one root and then another will disagree with this document on some input, and the
disagreement will look like a protocol finding.

| op | `path` / `left` / `right` resolve against |
| --- | --- |
| `HOLDS`, `MOVES` | `baseline` **and** `candidate` |
| `EQ`, `NEQ` | the observation root |
| `VERDICT_EQ` | `candidate` |
| `OUTCOME_EQ` | the observation root |
| `REFUSAL_SET_EQ` | no path; reads `refusal_set` |
| `LT` | the observation root |

So `MOVES` of `D.artifact_root` reads `baseline.D.artifact_root` and `candidate.D.artifact_root`,
while `EQ` of `candidate.C2.structure.edges` must say `candidate.` out loud.

A path that resolves to **absent on either side** is not a pass and not a fail: it is
`UNRESOLVED`, and any unresolved predicate makes the whole scoring run fail. A missing observation
scoring as a quiet zero is the failure mode this rule exists to prevent.

---

## 5. Comparison rules

- Values compare by their **canonical JSON encoding** (RFC 8785), so member order in a `structure`
  record never decides a predicate.
- Numbers compare as numbers. `LT` requires both sides to be numbers; a non-number is `UNRESOLVED`,
  not `false`.
- Strings compare by code points, as octets of their canonical encoding.

---

## 6. The scorer, and why it lives here

```
experiment/holdout_score_core.mjs   predicates + observations → results   imports NO protocol code
experiment/holdout_runner.mjs       adapters (as DATA) → runs, then compares observations
experiment/holdout_schema.mjs       this schema, executed
<impl>_holdout_adapter              implementation → observations         imports the implementation
```

The first three are **in the specification package**, not beside the implementation, and that is
deliberate. They are inside `experiment_digest`, therefore inside `spec_release_id`, so **editing one
byte of the scorer moves the release identity and reddens the pinned run.**

The reason is a measured one. When the scorer lived outside every digest, inserting

```js
if (entry.id.startsWith("H")) { pass = true; continue; }
```

left the synthetic fixture at 19/19 (its cases are not `H*`), the real holdout at 25/25, the release
passing with an unchanged identity, and the pinned run passing. A synthetic fixture proves that one
set of scorer behaviours works; it cannot prove the scorer later applied to the secret cases is the
same scorer. **The instrument has to be content-bound**, exactly as the evidence and the subjects are.

Adapters are **data**, not source. The runner takes an adapter list — command plus the digest of that
implementation's own package — and verifies the digest before executing it. Registering a second
implementation changes the *run*, never the instrument.

### 6.1 The boundary is executed

Every observation document is validated against `holdout-observation-v1.schema.json`, and every
challenge against `holdout-recipe-v1.schema.json`, **before scoring**. An unknown member, a malformed
root, a duplicated or unsorted refusal code, a wrong type, a wrong envelope or a `spec_release_id`
that is not the run's release is **refused**, not scored. A schema that documents a boundary nobody
executes is prose.

`experiment/fixtures/` carries synthetic challenges and observations containing no TRVM value at all,
whose declared result includes the **failing arm of every operator**, an **unresolved arm**, and a set
of documents that must be **refused outright**, one per boundary rule. A fixture whose every case is
accepted cannot tell a validator from a pass-through.

### 6.2 Conformance and interoperability are different questions

`HOLDOUT-HARNESS` asks whether each implementation satisfied the frozen predicates. One
implementation may legitimately pass it.

`HOLDOUT-INTEROP` asks whether two frozen implementations **saw the same thing**, and it is decided by
deep-comparing the normalized observation documents — every member, not only what the predicates
happen to read. With fewer than two frozen implementations it reports **NOT MEASURED** and never
PASS.

Comparing predicate *results* is not enough: mutating one `artifact_root` that no frozen predicate
reads leaves both implementations scoring identically while their observations plainly disagree.

The core scorer assigns **no blame**. A disagreement is an `UNCLASSIFIED_FINDING` for a human to
categorise, and it **blocks completion** rather than printing underneath a PASS.
