# Round 27, passes B7.1r + B8.1 + B8.2 — the map leaves the codomain, the decoder leaves the hash, and `mul`

**Deliverable for GPT.** All four instructions taken. Pack: `TRVM/b8-review.zip` — extract anywhere,
`./verify.sh`.

```
grid                 v1.50.0 (98 entries / 388 citations)
negative battery     354/354
emission conformance 22/22 over 24 fixtures — 19 EMITTING, 5 REFUSING
lowering refinement  28/28
native semantic film 45/45          cross-plane bridge  48/48
derive 45/45 · realm 24/24 · harness 14/14 · runner contract 3/3
lowering.mjs 0.12.0 · trvm_law_kernel.mjs 1.2.0
cert_id              a08ee15d…  — forty-sixth consecutive round, unchanged
```

---

## 1. Q1 — you were right, and B7's defence was the wrong decomposition

Taken in full. `sub` added **no executable constructor and no runtime rule** — B7.1's own measurement
prints `DECLARED POOL NOT EXERCISED` and lists no new rule. It added a macro expanded into
`Var/Lam/App/Dup/Sup/Era`, and there is no SUB node in the runtime at all. What moved `xenc` was that
the Church expansion, the combinators, the operand order, the codomain restriction and the emission
refusals were all inside the codomain's identity: **B1.2.1's over-binding defect, in the field
B1.2.1 created to fix under-binding.**

`EMISSION_RULES` (`erul-`) now owns the map, and `EMISSION_SEMANTICS` names it as the third term:

```
EMISSION_SEM_ID = H( target-template encoding
                   + executable target encoding
                   + EMISSION_RULES )
```

**INTERPRETED, and honest about where it is not.** `emit()` reads the combinator `shape` strings and
the `application` shape; `representableValue()` reads the domain rules. So `ADD_COMBINATOR` and
`PRED_COMBINATOR` are gone as code — they were arrow functions, which meant replacing PRED with an
extensionally equal predecessor moved only the provenance id while the RELATION claimed not to have
changed. What is **not** interpreted is stated rather than implied: the linear Church expansion is a
loop over `n`, so `church` carries a rule KIND dispatched on with a named refusal and the loop body
stays code inside `cema-`.

`TARGET_ENCODING` is now constructors, binding, label equality/freshness, the alpha/label quotient,
the identity — and **no refusal list at all**, because a LANGUAGE does not refuse; a MAP into it does.

**`E-2f` makes `xenc` answer a question**, both directions, against an operator the fragment does not
have (`div` — the case checks it is genuinely absent, so it cannot decay the way a synthetic `mul`
did the moment B8.2 added the real one):

```
a new compiler-library OPERATOR   →  erul MOVES, esem MOVES, xenc STANDS STILL
a new executable CONSTRUCTOR      →  xenc MOVES
a change to the alpha/label QUOTIENT →  xenc MOVES
```

and the recomputation reproduces all three live ids before mutating anything, so the equalities are
evidence rather than a tautology about an object nobody touched.

**Then B8.2 met the prediction with a real operator.** `mul` moved `tenc`, `lsem`, `isem`, `esem`,
`erul`, `cemp` and `cema`, and `xenc` stood exactly still.

### The template encoding carried the same leak, and the scrub found four more places than you named

You named `nodes.sub`. Scrubbing it and then writing the structural check to enforce the scrub
immediately found the same leak in `nodes.add`, in `nodes.church`, in `determinism` and in a refusal
list — and **two of them cited `TARGET_ENCODING.numbers`, a field that no longer exists**. Repairing
only what the ruling named would have left the neighbours exactly as exposed. The check is a standing
case now: no field of either encoding may mention `PRED`, `combinator`, `emit-`, `underflow`,
`Church` or `emit()`.

The stale top-of-file chain diagram is fixed, and it says what it was and for how long.

---

## 2. Q3 — no `representability_sem_id`, and the rules are structural instead

Taken as ruled. It is the domain predicate of emission: no receipt carries it, nothing downstream
observes it, no second implementation is compared against it, the split trigger has not fired. Its
rules live in `EMISSION_RULES.domain` as values `representableValue()` interprets, so acceptance
semantics are content-bound to `EMISSION_SEM_ID` without inventing a fifth relation.

The arithmetic became a **closed operator vocabulary** in the same edit — `{operator:"+"}`,
`{"-"}`, `{"*"}` with an unknown one a named refusal — which is what made `mul` a pure data change
rather than an edit to the emitter's source.

---

## 3. Q2 — decode widened, SEMSTATE untouched

Boundary reproduced first:

```
Church 11  →  signature 76 chars  →  decodes
Church 12  →  signature 82 chars  →  §5-COMPACTED  →  refused
```

with the runtime reaching the normal form for both. §5's 80-character bound is **not touched** and a
battery forgery refuses raising it. The shape is yours:

```
owned target normal form
      ├── identify ──▶ target_nf_sem_id     (oracle, HANDED IN)
      └── decode  ───▶ outcome
```

`decodeOwned(nf, identify)` freezes the normal form once and hands the same object to both. The
oracle is a **parameter**, for the reason `makeEmissionVerifier` takes one, and `decodeOwned`
**refuses to run without it** — so a caller cannot decode an object whose identity nobody computed.
Recognition is by **binding identity**, never by a binder name, so alpha-invariance is a property of
the recognition rather than of a prior canonicalisation.

**Demonstrated 0..20 including 11, 12 and 20**, and on every one the native `ic32_canon --nf` id
equals the id computed from the owned object — so the object decoded is the one the native runtime
reached, and nothing about SEMSTATE-CANONICAL-v1 moved to make it readable.

`decode-signature-compacted` is **gone from the spec entirely**, not repointed: it named a fact about
a representation the decoder no longer reads. It is **not** recast as a partial result — a term
normalising to Church 12 is a complete computation with an existing normal form, and conflating that
with `BUDGET_EXHAUSTED` would undo B5's distinction. `DECODE_SEM_ID` moved; every film and state id
did not.

---

## 4. `mul`, and the kernel defect it found

`MUL = λm.λn.λf.(m (n f))` — fully **linear**, every binder used exactly once, so unlike PRED it
needs neither a dup nor even a drop and contributes no label. Measured on both implementations first.
`mul(4,3)=12`, `mul(0,3)=0`, `mul(3,7)=21`, `(2+3)*4=20`, `mul(2, 2-3)` refuses through the
recursive domain walk. Every emitting mul fixture carries the MUL combinator in its bytes and is
longer than the folded literal would be; three of the four normalise to numerals whose signatures are
§5-compacted, **so the retired decoder could not have read their answers**.

### The defect

`mul(4,3)` and `mul(3,1)` replayed on `FloatRt` and **failed on `DescFloatRt`**. `foldLive` nested
live dups by **ascending heap id** and called that allocation order — true only because `FloatRt`'s
ids ascend. `DescFloatRt` allocates descending ids *precisely so nothing may depend on that*, and
under it the last-allocated dup was nested outside the binder its own value mentions; `normalRef`
then chased substitutions it could not resolve and ran out of budget.

No fixture before `mul` reached it: **every earlier term's live dups were independent**, so any
nesting worked. A left operand of `church(3)` or more is the first shape whose chained dups depend on
each other.

**The first repair was wrong and the measurement said so.** Switching to `liveDiscoveryOrder` — the
allocation-independent order the *semantic* fold has always used — fixed the chained case and **broke
`(2+3)*4` under `FloatRt`**. A traversal order is not a topological order on dup dependency.
**Allocation order is**, because a dup's value can only mention names that already existed when it
was allocated. It is a recorded stamp now, and `DescFloatRt` routes through the same `allocAt` so an
adversarial subclass cannot miss it.

**The semantic identities were never affected** — `foldCanonicalLive` has used discovery order since
it was written. Proof the repair is inert where it must be: regenerating
`golden_prehash_vectors.json` moved **two lines, both version strings**, with every signature and
every id byte-identical. Bridge 48/48, film 45/45, `cert_id` unchanged. `KERNEL_VERSION` 1.1.0 →
1.2.0, proved additive by `cert_id` as round 10 ruled such a claim must be.

---

## 5. Four gaps in my own new assertions, all found by the forgeries written against them

```
the fold assertion tested ONE shape       →  the discovery-order forgery PASSED it
nothing checked the adversary ADVERSES    →  a DescFloatRt with ascending ids PASSED
nothing exercised an unknown OPERATOR     →  a silent `+` fallback PASSED
no rule required an emission rule per     →  dropping node_rules.mul was caught by a
  lowered op                                 NEIGHBOUR, coincidentally
```

The first is the sharpest: **the two wrong fold orders fail on different shapes**, so an assertion
carrying only one passes the other's forgery. Both are in it now. The operator vocabulary needed
`representableValue` to take its rules as a parameter — B6.2's lesson one object over: *a
module-level frozen constant cannot be varied by the battery meant to falsify it.* And the
coincidental catch is the fifth in this line, so the case was retargeted at the assertion whose
subject it actually is.

Two pre-existing battery cases also tripped: `fragment-lists-disagree` hard-typed the four-op list
(**the same ratchet species B7 derived out of two grid assertions and two lowering_check cases,
surviving in the battery because nobody looked there**), and `sub-underflow-root-only` went vacuous
when `representableValue` gained a parameter. Both derived now.

---

## 6. Movement table across both passes

```
                                B6.3.1      B7          B7.1r       B8.1/B8.2
CORE_SEM_ID                     0930d6f1    SAME        SAME        SAME
DECODE_SEM_ID                   71f531c6    SAME        SAME        1f4b58c6   ← domain widened
TARGET_EXECUTABLE_ENCODING      69a5ffbf    f422ea28    7e89eee7    SAME       ← the point
TARGET_TEMPLATE_ENCODING        b4b5c4a4    48c96669    9449ba67    6643d8fc
LOWERING_SEM_ID                 51fda904    a9573a90    8fe7d024    a2410c95
INSTANTIATION_SEM_ID            7418dc41    8236aad4    d84c1050    108b38ec
EMISSION_SEM_ID                 b6958270    c45b734d    f7b8fa18    5e2b4ba7
EMISSION_RULES_SEM_ID           —           —           0ef7fd99    d0f9f474
CANONICAL_EMITTER_PROFILE_ID    c546742f    d7a2fe4f    SAME        e0a333a9
CANONICAL_EMITTER_ARTIFACT_ID   5d748198    0770b921    5234206c    a4e16db4
```

Both supersessions are recorded with their reasons — `SUPERSEDED_MAP_IN_CODOMAIN_SEM_IDS` says B7
defended a conclusion that was wrong, and `SUPERSEDED_SIGNATURE_DECODER_SEM_ID` records the 11/12
boundary the widening was forced by.

---

## 7. Open, and one question

Unchanged: source-refusal ↔ instantiation-refusal preservation · canonical-locus alias PRECEDENCE ·
C-side replay · `film-too-many-frames` has no positive witness · `len` unencoded.

**Next on your ordering: the first small bounded proof-producing workload**, not `len` automatically.

**Q — the `DescFloatRt` finding is bigger than one fold, and I did not widen the search.** The class
exists to prove that nothing depends on heap-id ordering, and it had never reached `foldLive` because
no fixture's dups were interdependent. I repaired the one site `mul` exposed and added an assertion
covering both failure shapes, but I have not swept the kernel for other places that infer an order
from an id integer. Do you want that sweep as its own small pass before the proof workload, or
folded into it as a precondition? My inclination is a short pass — the sweep is mechanical, and the
proof bundle will be the first artifact whose *correctness* depends on readback agreeing across
runtime classes.
