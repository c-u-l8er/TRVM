# WRL Core 0.2.1 — Frozen Family Extract

*Status: **frozen** (families only). This document supersedes `WRL_CORE_0.1.md` at revision 0.1.3. That file is **retained unchanged** as the historical record of the 0.1.x line and is no longer edited.*

> **This document is self-contained (0.2.1).** No clause here derives its normative meaning from `WRL_CORE_0.1.md`. The 0.1 file may be read to see *how* a clause came to be worded, and this file cites it for that purpose; it is never required to discover *what* is frozen. 0.2.0 failed this test in three places — §16.1 dropped the `==` grounding gate outright, and §16.2 and §17 were reduced to "unchanged from 0.1.x" pointers — which made a superseded historical record load-bearing for the current constitution. Restoring them is the substance of 0.2.1.

> **Why a new file rather than a 0.1.4 erratum.** 0.1.x's revisions were all *administrative or corrective* — they made grounding claims honest without moving a family. The 0.2.0 revision **promoted a construct**: the `~~` async route moved from `partial` to `surface-grounded`, and Mailbox became a sixth surface-grounded role. A promotion changes what the frozen core *asserts is settled*, so it took a minor version and a separate document. Editing 0.1.3 in place would have destroyed the record of `~~` having been partial at the moment Slice B was authorized — which is precisely the claim the Slice B batteries were built to discharge.

> **Why 0.2.1 is a revision of this file rather than a further new one.** The 0.2.0 → 0.2.1 change is *corrective*: it restores dropped clauses, fixes a miscount, scopes a byte claim, and narrows one wording. It promotes nothing and moves no family. By the rule stated directly above, that is exactly the class of change the 0.1.x line handled as in-file revisions (0.1.0 → 0.1.3), so the 0.2.x line is carried in this file and currently stands at **0.2.1**. Cutting a third file for a correction would invert the convention: it would spend a document boundary on the change that does *not* move what is settled, while the change that does move it shares a file with its predecessor.
>
> Nothing frozen by 0.2.0 is weakened here. 0.2.1 adds text and narrows one over-broad sentence (§8); it removes no freeze.

---

## Promotion record: 0.1.3 → 0.2.0

Slice B (`~~` async route) is **complete**. §16 step 2 is discharged.

### What moved

| Item | 0.1.3 | 0.2.0 | Where |
|---|---|---|---|
| `~~` async route texture | `partial` — IR/runtime-grounded, not surface-emittable, no structural `EdgeDecl` | **surface-grounded** | §5, §14 |
| Mailbox role | IR/runtime-grounded, surface-**partial**; explicitly "not a sixth surface role" | **sixth surface-grounded role** | §14b |
| `AsyncRouteDecl` | required but unbuilt (the D8 gate) | **frozen** as the logical route representation, distinct from `EdgeDecl` | §19 (new) |
| Acceptance policy | one pinned policy, named inline in §8 | **policy-selected**, two frozen members | §8 |
| Mailboxes in the Configuration shape | "Experimental, not part of the frozen floor" | **part of the frozen floor** | §8 |
| `ReplayBundle.policy_ids` | frozen field, **incorrectly serialized** for mailbox worlds | correctly serialized; replay exactness proven | §8b, §12 |
| §18 surface/registry gap | recorded as open | **closed** — `unwritable_role_ids()` empties itself | §18 |

### What did NOT move

- **No frozen family gained or lost a member**, except where the table above says so. The ten construct kinds (§1), the four reading laws (§2), the container, identity, time, memory, boundary and canonicalization families are **byte-identical in meaning** to 0.1.3.
- **`==`, `!!`, `/gate` remain partial or reserved.** Slice B grounded exactly one texture. §16.1's warning that `==` is *not* "almost free" stands unmodified, and is if anything reinforced: grounding `~~` took **eight** commits and a ruling, and `==` introduces authorization structure that `~~` did not.
- **`*` wildcard matching remains reserved.**
- **No `SemanticArtifactID` moved.** The promotion added a construct; it did not re-canonicalize an existing one.

### Where declared bytes moved

**Among sealed artifact trajectories, declared bytes moved only in the Film v0.7 policy-label field for mailbox-bearing worlds. The low-level policy-conformance seam also corrects previously omitted EventLedger output for an unsealed policy/world pairing.**

Both halves are stated because the first alone is not true of the whole implementation:

| Scope | What moved |
|---|---|
| **Sealed trajectories** (a world executed under the policy its own artifact seals) | Film v0.7's `admit:policy=` line reports the **sealed** acceptance policy instead of a module constant. Mailbox-bearing worlds' films move; every mailbox-free world's film is byte-identical to 0.1.3. |
| **The low-level policy-conformance seam** (§8c) — a mailbox-free world driven under the mailbox policy, which is *not* a sealed configuration | The EventLedger is no longer suppressed. A film that previously asserted `state=disputed` while printing no ledger line now prints the `MailboxReject` that caused the dispute. |

0.2.0 claimed the first row and omitted the second, which made a true statement about sealed execution read as a false statement about the codebase. The second row is reachable only through the probe seam frozen in §8c; no sealed world can produce it, which is why it is a *conformance* correction rather than a trajectory change.

The first row is recorded as a promotion-scoped change rather than a bug fix because it is both. It was measured as an open edge during Slice B commit 5c and deliberately deferred — the fix moves declared bytes, and a frozen revision is the only place that may happen. See §8b for why it was never cosmetic.

---

## Corrective record: 0.2.0 → 0.2.1

0.2.0 was submitted as the final frozen document and was **not accepted as such**. The implementation it described was accepted in full; the document was returned for freeze-integrity defects. 0.2.1 discharges them.

| # | Defect in 0.2.0 | Correction |
|---|---|---|
| 1 | §16.1 **dropped** the frozen `==` grounding gate (the four-part ADMIT condition) | restored verbatim in meaning, alongside the Slice B empirical argument that replaced it |
| 2 | §16.2 reduced to "Unchanged from 0.1.2" | the permission/instance table and the no-principal constraint inlined in full |
| 3 | §17 reduced to "Unchanged from 0.1.3" | the five closure obligations, the seam that discharged them, the column-exactness note, the *no sugar-specific identity* law and the two gated properties inlined in full |
| 4 | the promotion record said Slice B took **six** commits; §16.3 lists **eight** | eight, consistently |
| 5 | "declared bytes moved in exactly one place" was true of sealed trajectories only | scoped explicitly, with the second location named |
| 6 | §8's ACCEPT/MAP freeze said event eligibility is decided *before anything examines the operation* — too absolute to admit verified authorization | replaced with the ruled wording: event-key resolution is **operation-agnostic**, which forbids the defect without forbidding `==` |

Defects 1–3 share one cause and it is worth naming, because it is the same class this line has hit twice before in code. A document that says *"unchanged from the superseded document"* has **forked its own normative content**: the current constitution and the historical record are now two spellings of one fact, and the reader must consult both to know what is frozen. §17's own note about the L-0 status — *"a second spelling of one fact is not a copy, it is a fork, and it will disagree"* — was written about exactly this, one section below where 0.2.0 committed it.

The abbreviation was not a summary error. It was a **compression that changed the document's type**: 0.2.0 read as a diff against 0.1.3 while claiming to supersede it.

---

This document commits the **meaning families** of WallRiderLang that the TRVM runtime and the Forge semantic graph have grounded. It freezes *which kinds of things exist and what each kind means* — **not** the detailed surface rules, which remain a design draft in `WRL.md` and may still change.

**Freezing a family** means: the set of members is closed, and each member's meaning-role is settled. It does **not** freeze exact glyphs, argument grammars, sugar, or edge-case rules — those live in `WRL.md` and are Experimental/Proposed until a later frozen revision promotes them.

When `WRL.md` and this file conflict about *what is settled*, **this file wins**. `WRL.md` remains authoritative for full rationale and forward design.

---

## 0. Architectural rule (frozen)

WRL denotes the **canonical Forge semantic graph**. It is **not** lowered by compiling surface syntax directly to hand-written interaction-calculus text. The only sanctioned path is:

> WRL source / canvas → canonical **semantic graph** → **Forge Semantic IR** → TRVM facts / films / reductions.

Forge Semantic IR v1 is frozen (`FORGE_SEMANTIC_IR_v1.md`, profile `forge.world.core.v1`).

---

## 1. The ten construct kinds (frozen: closed set)

Every WRL construct is exactly one of these ten kinds. The set is closed.

| Kind | Role (frozen) |
|---|---|
| Function | calculates — pure local computation |
| Actor | persists — durable identity + owned state |
| Route | communicates — a directed, textured transition edge |
| Wall (boundary) | authorizes — gate / commit / seal on propagation |
| Period | orders — logical-time step under which events settle |
| Fragment | carries code — quoted graph as movable data |
| Stencil | constructs graphs — parameterized fragment producer |
| Derive | transforms typed graphs |
| Film | proves what occurred — append-only replayable log |
| Hash | identifies what was built — content address |

Of these, **Actor, Route, Wall, Period, Film, Hash** are additionally grounded by TRVM today (§14). **Function, Fragment, Stencil, Derive** are frozen *as kinds* but their detailed semantics remain draft.

---

## 2. The four reading laws (frozen)

1. **Shape says what a thing is.** Bracket shape identifies the kind of object.
2. **Line texture says how it moves.** Route style identifies the operational guarantee.
3. **The colon introduces; the slash bounds.** Both families cap at three strokes, ordered by permanence: transient · committed · sealed.
4. **Marks for architecture, words for computation.** Process notation owns punctuation; expression notation defaults to words.

---

## 3. Container / shape-as-kind family (frozen: 3 members)

| Shape | Kind (frozen) |
|---|---|
| `[x]` | durable **identity** (actor, region, mailbox, named artifact) |
| `(x)` | **state** — current, mutable-by-replacement cell |
| `{x}` | **wiring** — permitted topology / capabilities / ports |

Frozen invariant: `(state)` is single-owner and mutable-by-replacement; `{…}` is permitted/static structure, distinct from current state. Exact field grammars are draft.

---

## 4. Identity / addressing family (frozen: 4 members)

| Symbol | Meaning-role (frozen) |
|---|---|
| `#` | canonical identity / content hash |
| `@` | address / placement / stamp |
| `?` | pattern variable introduced by matching |
| `*` | wildcard match, or replication-by-position |

Frozen invariant: executable identity is a hash; human aliases are words and never semantic.

**Implementation status of `*`.** The symbol's *family role* stays frozen as written, but the two meanings are at different maturities and the spec must not imply otherwise:

| Meaning | Status |
|---|---|
| **replication-by-position** (`[relay:r*3]`) | **implemented** — surface sugar, bounded, identity-equivalent (§17) |
| **wildcard match** | **reserved** — no lowering exists |

---

## 5. Route / texture family (frozen: 4 core textures)

The reduction relation is defined over exactly these four irreducible textures. All surface sugar canonicalizes down to one of them plus attributes.

| Texture | Guarantee (frozen) |
|---|---|
| `--x-->` solid | deterministic local transition; settles within the period |
| `~~x~~>` async | asynchronous message; appended to a mailbox; observable next period |
| `==x==>` verified | evidence-backed / committed transition under a named policy |
| `!!x!!>` fault | crash / cancel / reject / interrupt; engages supervision |

Frozen: the *set* of core textures and their guarantee-roles. Not frozen: label/payload/guard grammar, the sugar table, branch/lane rules.

**Surface status (0.2.0).** Freezing a texture's *meaning-role* is not the same as grounding its *construct*. Two of the four are now surface-grounded:

| Texture | Surface status | See |
|---|---|---|
| `--` solid | **surface-grounded** — declarable, emittable, round-trips | §14 |
| `~~` async | **surface-grounded** *(promoted in 0.2.0)* — declarable, emittable, round-trips, and grounded across reference reduction, native reduction, film and replay | §14, §19 |
| `==` verified | **partial** — acceptance machinery exists; the construct does not | §16.1 |
| `!!` fault | **partial** — fault *state* exists; route + supervision do not | §16 |

> **`~~` is grounded as a *logical route*, not as an edge.** The promotion did **not** add an `EdgeDecl` kind. An async route does not settle within the period, so it cannot participate in the within-period REACT fixpoint the way `--` does; it is represented by a separate canonical declaration. This distinction is frozen in §19 and is the substance of the promotion, not a detail of it.

---

## 6. Time family (frozen)

- Logical time is **superdense**: every event carries `(period t, microstep m)`.
- A **period** is the settle-and-commit unit; same-period events are ordered by microstep.
- Wall-clock enters only through an explicit boundary and is recorded as a signed fact; wall-clock is never replayable state, logical time is.

Frozen: the period/microstep model and the wall-clock-as-fact discipline. Not frozen: the tick/`.n`/`...` surface syntax details.

---

## 7. Memory-kind family (frozen: 5 members)

| Shape | Memory kind (frozen) | Lifetime rule |
|---|---|---|
| `(state)` | volatile cell | mutable by replacement; single-owner |
| `{facts}` | monotonic knowledge | grow-only; merges by lattice union; never retracts |
| `[archive]` | durable store | persistent addressable actor; survives restart |
| `:: fragment //` | code memory | quoted graph as portable data |
| `#hash` | sealed identity | immutable, content-addressed |

Frozen invariant: **no shared mutable cell**. Shared knowledge is `{facts}` (monotone union); shared identity is `[archive]`. This single-owner discipline is what makes execution deterministic without a runtime conflict resolver.

> **Where a mailbox sits (0.2.0).** A mailbox is **not** a sixth memory kind. Its contents are messages in transit, not a memory cell: they are appended by a logical route, observable exactly one period later, and consumed at a period boundary. The mailbox's *identity* is `[x]` (§3) and its *inbox* is state owned solely by the mailbox. No shared mutable cell is introduced, so the frozen invariant holds unmodified.

---

## 8. Execution-model family — the deterministic reactive floor (frozen)

Grounded directly by TRVM's deterministic reduction, ADMIT reducer, persistent fold, and replayable films.

**Configuration** (frozen shape): the persistent runtime state — world state (owned state cells), monotone claim facts, immutable acceptance receipts, capacity-fault latches, clock state, poses, rotors, numeric faults, **mailbox inboxes and the mailbox capacity latch**; plus static topology + policies.

*(0.2.0: mailboxes move into the frozen floor. In 0.1.x the Configuration shape excluded them as "Experimental". Supervisor and behavior tables remain Experimental and remain excluded.)*

**Two frozen invariants** (enforced statically):
1. **Single-owner cells** — no shared mutable cell.
2. **Disjoint deterministic guards** — at most one deterministic rule enabled per actor-state; genuine choice must be an explicit `scored` branch.

**Period cycle** (frozen 6 phases): the proven Forge/TRVM epoch boundary is
**OBSERVE** (canonicalize + insert distinct claims) →
**ACCEPT** (create missing receipts per the selected acceptance policy) →
**MAP** (newly-accepted successful ops → controls) →
**COMMIT** (apply control writes + fault resets to owned cells) →
**REACT** (deterministic within-period token cascade to fixpoint; latch current overflow) →
**FILM** (record the entries needed to replay the epoch).

For claim-free profiles the first three phases (OBSERVE/ACCEPT/MAP) **degenerate to identity but must not disappear** from the semantic model: the OBSERVE/ACCEPT/MAP distinction is what determines which claims were seen, which candidate was accepted, whether a retransmission retries an effect, which controls were committed, and whether a same-epoch configuration affects that epoch's reaction.

> **ACCEPT owns receipt eligibility; MAP owns operation effects (frozen, 0.2.0; narrowed 0.2.1).** **Event-key resolution is operation-agnostic: the same event key may not be resolved differently merely because its candidates carry different operation kinds. Any authorization predicate over claimant, target, operation family or named policy must complete before receipt creation. MAP consumes only accepted operations and may never create, suppress, reverse or repair an acceptance decision.**
>
> This is stated because it is the exact defect Slice B produced and had to correct: the two ACCEPT implementations compute per-slot eligibility independently, so a rule threaded into one and not the other yields a machine that refuses a receipt and applies the operation anyway. A policy that refused an equivocal `Send` but admitted an equivocal `SetRotor` would be resolving the key by operation kind, which this clause forbids.
>
> **Why the 0.2.0 wording was withdrawn.** It said eligibility is decided *"before anything examines what operation the claim carries"*. That is stronger than the law needed and would have frozen `==` out of the core: a verified route's whole purpose is to authorize a **claimant / target / operation family / named policy** tuple (§16.1), so authorization must be permitted to *read* the operation family while still completing before any receipt exists. The distinction the core actually needs is not *whether* the operation may be examined but *what may be concluded from it*: an operation family may gate authorization, and may never gate how a contested key is resolved among its candidates. Prohibiting the reading rather than the conclusion would have made the next promoted construct unspellable — a freeze that forbids its own successor.

**Canonical ordering is policy-pinned (frozen as a family, not a formula).** Events and accepted operations are ordered by a *total canonical key whose schema and policy identity are part of the semantic artifact*. Worker arrival order is never semantic. The *existence and policy-pinning* of the key is frozen; the specific formula is not.

**Acceptance is policy-SELECTED (frozen, 0.2.0: two members).** 0.1.x named a single pinned policy inline, and §8 anticipated this revision in as many words: *"a future mailbox profile may pin a different key."* That profile now exists, so acceptance is frozen as a **selection over a closed set** rather than as one formula:

| Policy | Seam-1 resolution | Selected when |
|---|---|---|
| `admit_candidate_min_firstreceipt_v1` | MIN CandidateKey / first-receipt — competing candidates for one event key collapse to the minimum | a world declares **no** mailbox |
| `admit_mailbox_deliver_all_v1` | equivocation is **refused** — an event key with more than one distinct candidate yields no receipt, no effect, and a `MailboxReject` | a world declares a mailbox |

**Frozen consequences of the selection:**

1. **The policy is part of the sealed semantic artifact** (`semantic_policies.admit_policy_id`) and is read from it. It is never re-derived at run time from the world's shape.
2. **The acceptance policy and the proof profile are separate semantic axes**, even where they correlate. The proof profile is selected by which *route kinds* a world contains; the acceptance policy by whether a *mailbox* is declared. A mailbox-bearing, route-free world is the witness that they are independent: it declares the mailbox policy while lowering under the route-free profile.
3. **Every runtime honours the same declaration.** The reference reducer, the native reducer, and the film projection each take the policy from the seal. A runtime that derived it from the profile, from mailbox presence, from a capacity value, from the presence of a `Send`, or from a caller-supplied option would be correct only by coincidence.

**Conflicts (narrowed):** *cell-write conflicts are structurally constrained; claim and control conflicts are resolved by explicit, policy-pinned recognition, acceptance, and canonical application laws.* Concretely:
- single-owner cells remove generic write-write races;
- append and fact-union structures merge deterministically;
- but equivocation, conflicting accepted operations, claim retransmission, receipt divergence, configuration ordering, fault-reset-vs-new-overflow, and capacity failure are **not** dissolved by ownership — each is resolved by an explicit pinned policy (recognition = distinct-CandidateKey count; **acceptance = the selected policy's seam-1 rule**; application = canonical event order; fault = COMMIT-clears-then-REACT-ORs; capacity = atomic latch, no partial).

Not frozen: the podium/ranking ceiling, scored-branch scoring functions, distributed termination detection.

---

## 8b. History family — WorldFrame / EventLedger / BuildFilm (frozen: 3 distinct artifacts)

"Film" is not one undifferentiated object. Three conceptual artifacts are frozen distinct (their current serialization is the Film v0.6/v0.7 family):

| Artifact | Frozen role |
|---|---|
| **WorldFrame** | authoritative observable state sufficient for future behavior (the physical world snapshot; Film v0.6 bytes) |
| **EventLedger** | accepted events, receipts, effects, outcomes (the claim-aware layer; Film v0.7 adds this over v0.6) |
| **BuildFilm** | compiler/build provenance (Proposed) |

A replay package is frozen as:

```
ReplayBundle { initial_artifact, initial_state, event_ledger, frames, policy_ids }
```

Frozen: the three-way WorldFrame/EventLedger/BuildFilm distinction and the ReplayBundle shape. Not frozen: byte layouts (they are the Film v0.6/v0.7 serialization, a backend concern).

**`policy_ids` is load-bearing (frozen consequence, 0.2.0).** Because acceptance is now policy-selected (§8), the recorded policy is the only thing that makes a ledger replayable. Two frozen consequences follow:

1. **A film must name the seam that produced it.** The serialization records the acceptance policy the trajectory *actually ran under*, not a compiled-in default. Through 0.1.x it recorded a constant, so a mailbox world's film named a policy that would not reproduce its own frames — a `ReplayBundle` whose `policy_ids` contradicted its `frames`. This is why the byte move in the promotion record is a correctness fix and not a relabelling.
2. **The EventLedger is not part of any role's block.** Ledger entries are recorded whenever they exist, independently of which roles the world declares. A rejection is ACCEPT refusing an event key (§8), so conditioning its *record* on the presence of a mailbox would make the ledger's contents depend on the world's shape rather than on what occurred — and would silently reintroduce operation-specific rejection at the serialization layer, having excluded it from the reducer.

---

## 8c. Sealed execution and the policy probe seam (frozen, new in 0.2.1)

§8 consequence 1 says the acceptance policy is read from the seal and *"never from a caller-supplied option"*. 0.2.0 asserted that as a property of the runtime while the runtime still exposed a raw policy argument on its ordinary entry points. A statement a public API contradicts is not a freeze; it is a convention. 0.2.1 freezes the two-level structure that makes it enforceable.

**Level 1 — production world execution (frozen).**

```
fold_world(artifact, ...)
  → RuntimeSeamsV1 derived from the artifact
  → admit reduction
  → film
```

There is **no** policy override on this path. A world runs under the policy its own artifact seals, or it does not run.

**Level 2 — the policy probe (frozen as explicitly non-world).**

A named, clearly non-world seam remains available for exercising policy tables, reducer seams and serializers across combinations that no sealed artifact can produce:

```
admit_policy_probe(...)
```

**Frozen consequences:**

1. **Ordinary world execution cannot select an acceptance policy.** The only way to change the policy a world runs under is to change the world, which moves its `SemanticArtifactID`. Acceptance semantics are therefore reachable only through identity.
2. **Replay verifies the policy against the seal.** A `ReplayBundle` whose recorded `policy_ids` disagrees with `initial_artifact.semantic_policies.admit_policy_id` is **refused**, not reconciled, with `WRL_REPLAY_POLICY_MISMATCH`. §8b makes the recorded policy load-bearing; this is what makes it *checked*. A replay that silently preferred either source would reintroduce the 0.1.x defect from the opposite end — there the film disagreed with the world and nothing looked, here the film may disagree with the world and something must.
3. **The probe is not a second execution path.** It selects the policy explicitly *and marks the result as unsealed*. A probe result is a statement about a policy table, never about a world.
4. **Cross-product conformance stays reachable.** The probe exists because the useful negative evidence lives at combinations no world can seal — a mailbox-free world under the mailbox policy is how the core demonstrates that the EventLedger is independent of the mailbox block (§8b consequence 2). Removing the seam would have deleted the test rather than the risk.

> **Why not simply delete the raw argument.** Because the argument had a legitimate user and an illegitimate one, and they are distinguishable. The illegitimate user is application code executing a world under semantics it did not seal. The legitimate user is a conformance battery asserting a law *about the policy table itself*, which by construction must reach configurations the seal cannot express. Deleting the parameter would have satisfied the letter of §8 by discarding the evidence that §8b is honoured. Naming the two levels keeps both properties.

---

## 9. Fact-merge family (frozen: union law only)

Replicated `{facts}` merge by a **join-semilattice union** that is commutative, associative, and idempotent. This is the frozen distributed floor and matches TRVM's proven claim-fact SET UNION.

**Explicitly NOT frozen (Proposed in draft):** acceptance-receipt settlement across logs, Byzantine/trust modes, sequencer/authority settlement, signatures/reputation. Conflicting receipts are *recognized evidence for later settlement*, never blindly merged.

---

## 10. Boundary (wall) family (frozen: gate / commit / seal)

| Boundary | Reduction effect (frozen role) |
|---|---|
| `/gate` | require capability; emit an effect-request node (no ambient I/O) |
| `//commit` | canonicalize the fragment-so-far; assign a content id; freeze it |
| `///seal` | commit, then register the artifact under a content hash |

Frozen: the three-tier gate/commit/seal ordering by permanence, and the no-ambient-authority rule (effects cross named walls only). Not frozen: exact policy grammars.

---

## 11. Canonicalization & content-identity family (frozen)

- Meaning is **normalized before content addressing**. Comments, spacing, alignment, decorative line/route length, and presentation color never affect the semantic hash.
- Identity is **content-addressed** (`#hash`); the same normalized graph yields the same hash on every host.
- Builds/expansion are **hermetic and host-blind**: same source → same canonical bytes.

This matches TRVM's content-addressed objects and the digest/candidate-key discipline used in the ADMIT core.

---

## 12. Conformance families frozen

These observable properties are frozen as *families of guarantee* (their exact test matrices remain draft):

- **Formatting invariance** — presentation never changes the hash.
- **Replay exactness** — a live run and its replay share all observables. *(0.2.0: this now includes the acceptance policy — a replay driven from a film's own recorded `policy_ids` must reproduce that film exactly. See §8b.)* *(0.2.1: and a replay whose recorded policy disagrees with the sealed artifact is **refused**, not reconciled — see §8c consequence 2. Exactness without refusal is only a hope that the two agree.)*
- **Build invariance** — same inputs → identical film + hashes across hosts.
- **Merge laws** — fact union is commutative/associative/idempotent.
- **Boundary safety** — undeclared effects cannot cross walls.
- **Scheduler invariance** — worker ordering never changes the committed film.
- **World round-trip** — a format→parse cycle preserves the complete canonical world projection, defined by exclusion (§15).
- **Identity round-trip** — a format→parse cycle preserves the canonical artifact bytes and the `SemanticArtifactID`.
- **Document separation** — a world document excludes run inputs both semantically and lexically (§15).
- **Runtime agreement** *(0.2.0)* — the reference reducer and the native reducer produce identical films for every grounded construct, under the policy the world declares.

---

## 13. What Core 0.2 does NOT freeze

Deferred to later frozen revisions (see `WRL.md` tier table):

- **Experimental:** the entire expression notation (values/functions/types/generics/numerics), effects/capabilities/entropy, the supervision error ladder, streams/backpressure, actor behavior blocks, evolution/migration, podium/ranking, static-check catalog, execution profiles.
- **Proposed:** metaprogramming (fragments/stencils/derives/reflection/sealed compiler tools) beyond their kind-role, modules/builds, build films, foreign functions, and all distributed settlement above fact-union.

*(0.1.2 removed "mailboxes" from the Experimental list on the grounds that they were IR/runtime-grounded and surface-partial. 0.2.0 completes that: mailboxes are **promoted**, not merely un-Experimental. See §14b and §19.)*

Promotion path: a family moves from Experimental → Core only after it is **surface-grounded** (§14b) in a running Forge/TRVM implementation, at which point this file is revised (0.3, 0.4, …). The steered order for the remainder is recorded in §16.

---

## 14. TRVM grounding

Grounding is stated honestly: **grounded** = an isomorphic TRVM lowering exists; **partial/reserved** = the concept is grounded but the WRL language construct is not, or the construct is reserved with no lowering.

*(§14b splits "grounded" into **IR/runtime-grounded** and **surface-grounded**. Every entry in the table below is surface-grounded.)*

**Grounded:**

| Family | TRVM grounding |
|---|---|
| The six **surface-grounded** world roles (Pulser/Relay/Door/Spinner/Orb/**Mailbox**) — see §14b | fixture node kinds; lowered by the compiler + IC emitter |
| State + wiring | state schema (counters, wires, rotor-as-state, pose, sticky fault); sig-wire + socket edges |
| Deterministic signal route (`--`) | sig-wire delivery; within-period REACT fixpoint |
| **Async route (`~~`)** *(0.2.0)* | canonical `AsyncRouteDecl` (§19) → mailbox enqueue/deliver across the period boundary; reference + native reduction agree |
| Periods | epoch-by-epoch persistent fold |
| WorldFrame / EventLedger (§8b) | Film v0.6 (physical) / v0.7 (claim-aware); replay exactness proven, including `policy_ids` |
| Content identity (§11) | content-addressed rulepack hash; digest / CandidateKey packing |
| Fact union (§9) | monotone claim-fact SET UNION; immutable receipts kept separate |
| ADMIT acceptance core (§8) | OBSERVE→ACCEPT→MAP reducer, single-epoch + persistent fold, both acceptance policies, ref == native |
| Commit/react sequencing (§8, §10) | COMMIT (control writes + fault resets) → REACT → latch overflow |

**Reserved or partial (NOT a complete grounding):**

| Family | Status |
|---|---|
| Verified route (`==`) | **partial** — acceptance machinery grounded, but the route *construct* is not a complete lowering (see §16.1 for the condition it must meet) |
| Fault route + supervision (`!!`) | **partial** — numeric-fault *state* grounded; the route/supervision *construct* is not, and no supervision floor exists yet |
| Capability gate (`/gate`) | **reserved** — no capability-gate node kind yet |
| Seal / artifact registry (`///seal`) | **partial** — commit grounded; seal registry is Proposed |
| General actor behaviors | **reserved** — Experimental; no arbitrary-behavior runtime exists |
| Wildcard `*` | **reserved** — only replication-by-position is implemented (§4) |

---

## 14b. Surface-grounded vs IR-grounded (frozen distinction)

0.1.1 used a single word, *grounded*, for two genuinely different achievements. Conflating them let IR work read as if it had promoted a route texture, which it had not. The distinction is frozen:

| Term | Means |
|---|---|
| **IR/runtime-grounded** | a canonical IR declaration exists, the runtime executes it, and it is covered by a battery |
| **surface-grounded** | *additionally*, WRL source can **declare** it, the formatter can **emit** it, and it round-trips through the canonical bytes |

A construct is only eligible for promotion into a frozen Core family when it is **surface-grounded**. IR/runtime grounding alone is necessary but not sufficient.

**Mailbox was the worked example, and is now the worked promotion.** The 0.1.2/0.1.3 text read:

> *Mailbox is not a sixth surface-grounded role. `MailboxDecl` is IR/runtime-grounded: it exists in the canonical IR, the runtime honours it, and the Slice A networking battery covers it. It is not surface-grounded: there is no `~~` surface form to write, the formatter cannot emit one, and — decisively — there is no structural `EdgeDecl` for it.*

Every clause of that has been discharged. **Mailbox is now the sixth surface-grounded role**, and `~~` is a surface-grounded texture (§5).

The `EdgeDecl` clause was discharged **by satisfying it, not by waiving it**: no `EdgeDecl` kind was added. The route is carried by a separate canonical declaration (§19), which is what the constraint demanded.

> **The bar this sets for the next promotion.** Six dimensions had to hold simultaneously, and each was proven by a named battery rather than argued:
>
> | Dimension | What had to be true |
> |---|---|
> | **source** | `~~` parses, and the formatter emits it |
> | **canonical IR** | a declaration distinct from `EdgeDecl`, entering world identity |
> | **sealed-policy reference behaviour** | the reference reducer honours the policy the world declares |
> | **native reduction** | the native reducer agrees with the reference reducer, byte for byte |
> | **film** | Film v0.7 renders the construct's full effect, labelled with the seam that produced it |
> | **replay** | replaying from the film's own recorded `policy_ids` reproduces that film exactly |
>
> A construct passing five of six is **not** surface-grounded. The film and replay dimensions in particular were the last to close and were closed by this revision — they are easy to believe are already satisfied, because a wrong film that both runtimes render identically survives every runtime-agreement check there is.

---

## 15. The document boundary (normative)

A **world** and a **run of that world** are different documents.

| Document | Carries | Enters `SemanticArtifactID`? |
|---|---|---|
| **World document** | profile, objects, edges, **async routes**, static config, wiring | **yes** |
| **`ScenarioV1`** | `periods`, `[epoch:N]` claims, run inputs | **no** |

*(0.2.0: `AsyncRouteDecl` is world content and enters world identity. It is listed explicitly because §15's own warning — that the world projection must be defined by exclusion and never as a fixed tuple such as `(profile, nodes, edges)` — anticipated exactly this addition.)*

**Frozen consequences:**

1. **Run inputs are not world content.** `periods` and `[epoch:N]` claims are run inputs. Changing them does not move the `SemanticArtifactID`; the same world can be run by many scenarios.
2. **A world formatter emits a world document.** It must exclude scenario syntax both *semantically* (reparsing yields no run inputs) and *lexically* (the emitted text does not contain scenario syntax at all). The lexical half is load-bearing: a formatter emitting a literal `periods 0` would satisfy the semantic half while still writing scenario syntax into a world document.
3. **Round-trip laws split in two.** The **world** round-trip preserves the complete canonical world projection; the **identity** round-trip preserves the canonical artifact bytes and the `SemanticArtifactID`. Neither subsumes the other.

> The world projection is defined by **exclusion** — every canonical field *except* the run inputs — and never as a fixed tuple. A fixed tuple silently stops covering any field a later slice adds.

### 15.1 The two parser mouths

**The strict world parser is normative.** Parameterizing the parser is sanctioned only as a **migration bridge**, and only through an unmistakable API — never a boolean flag on one function:

| Entry point | Accepts | Status |
|---|---|---|
| `parse_wrl_core(text)` | world source **only**; rejects run inputs with a typed `WRL_WORLD_SOURCE_HAS_SCENARIO` | **normative** |
| `parse_wrl_legacy_document(text)` | a pre-boundary **combined** document | explicit compatibility path |

The legacy path's destination is to **split** a combined document into `WorldDocumentV1 + ScenarioV1` rather than to keep parsing it forever.

### 15.2 The lexical form of the boundary (normative)

Run-input syntax is recognised by **anchored line forms**, not by substrings:

| Form | Matches |
|---|---|
| `^\s*periods\b` | a `periods` **declaration** |
| `^\s*\[epoch:` | an `[epoch:N]` **claim line** |

Two properties of this definition are load-bearing:

- **`@` is not a marker.** `@` is frozen for world addressing and placement (§4), so it appears in perfectly legal world source — `[orb:ob]@(3,4){pose}` is a world line. Treating a bare `@` as scenario syntax rejects valid worlds.
- **Claim *operations* are not listed.** `SetRotor` and `ResetFault` are deliberately absent: every claim line is already anchored by `[epoch:`, and listing the operations as well would create a second, drifting definition of what a claim is. Matching them as substrings also misfires on legal identifiers such as `[relay:ResetFault_gate]`.

> **One definition, one spelling.** This vocabulary lives at exactly one place in the implementation and every consumer — parser, formatter law, batteries, probes — reads it from there. A hand-rolled second spelling is a **fork, not a copy**.

### 15.3 What splitting a combined document preserves

The split is **order- and position-preserving**, not layout-*reconstructing*:

> For every line *N* of the input, line *N* sits at index *N* of whichever side received it, retains its original line ending, and the two sides **recombine to the input exactly**.

It is stated as recombination rather than as "both sides have the same line count" because a final **empty, unterminated** line is textually invisible — an inherent property of text, not a defect in the split.

### 15.1.1 `CanvasGraphV1` — frozen as legacy

`CanvasGraphV1` — the Phase-3C presentation surface — was never migrated across this boundary: it still carries top-level `periods`/`batches`, making it the structural parallel of `parse_wrl_legacy_document`. The disposition:

1. **Frozen as an immutable legacy combined-document surface**, and **retired from active development**.
2. **No new semantic fields.** `AsyncRouteDecl`, `~~`, and any other §16 construct must **not** be added to V1.
3. **A named compatibility importer is preserved**, splitting V1 content three ways — **world**, **`ScenarioV1`**, and **presentation**. Three, not two: V1 conflates all three, and a two-way split would silently fold presentation into world content, moving `SemanticArtifactID`s that must not move.
4. **The successor is world-only.**
5. **The successor must distinguish structural `EdgeDecl` connections from logical route declarations** (§19).
6. **Export back to V1 must reject any lossy downgrade involving async routes** with a typed error, rather than emitting a V1 document that silently drops them.

The importer is **Slice B Commit 0** — it landed *before* `AsyncRouteDecl` existed:

```
import_canvas_graph_v1(canvas) -> LegacyCanvasImportV1(world, scenario, presentation)
```

| Component | Content |
|---|---|
| `world` | the canonical **world projection**, run inputs **excluded** |
| `scenario` | `periods` and the ordered epoch claim batches, preserved **exactly** |
| `presentation` | `CanvasLayoutV1` |

> **Why point 6 is now live rather than hypothetical.** Through 0.1.x no world could contain an async route, so the lossy-downgrade rejection had nothing to reject. As of 0.2.0 route-bearing worlds exist and the rejection is load-bearing.

---

## 16. Core 0.3 promotion order

The order below is **steered, not merely preferred** — each step supplies something the next one needs, so reordering them produces constructs that cannot be grounded honestly.

| # | Step | Gate it must pass |
|---|---|---|
| 1 | ~~**L-0 closure**~~ — **COMPLETE (0.1.3)** | see §17 |
| 2 | ~~**`~~` async route (Slice B)**~~ — **COMPLETE (0.2.0)** | needed a canonical logical route declaration distinct from `EdgeDecl` — discharged in §19 |
| 3 | **`==` verified route** — *next; ruling packet required before implementation* | see §16.1 for the grounding gate and §16.4 for the frozen staging |
| 4 | **`#` references and `&` composition** | — |
| 5 | **`//commit` and `///seal`** | — |
| 6 | **`!!` fault route** | may only follow a **minimal supervision floor** actually existing |
| 7 | **`/gate` capability gate** | last |

### 16.1 `==` is not "almost free"

It is tempting to read the verified route as nearly grounded, because ADMIT already accepts claims. That reading confuses two different things:

- the **declaration** `==` would introduce is *authorization structure*;
- the **frozen texture** `==` denotes an *evidence-backed transition*, and what ADMIT provides is *acceptance mechanics*.

**`==` is grounded only when ADMIT enforces all four** of: the **claimant**, the **target**, the **operation family**, and a **named policy**. Anything less is a route that looks verified and is not.

*(Restored in 0.2.1. 0.2.0 dropped this paragraph while adding the empirical argument below. It is the gate for the next promoted construct, and §8's ACCEPT/MAP clause is now worded against it — the four enforced facts are exactly what an authorization predicate is permitted to read before a receipt exists.)*

Slice B is the empirical argument. `~~` looked closer to free than `==` does — the mailbox was already IR/runtime-grounded and the reducer already delivered messages — and grounding it still took eight commits, a ruling, and the discovery that the acceptance policy and the proof profile were separate axes. `==` starts further back.

### 16.2 Permission / instance split (approved)

The split is approved, with terminology that keeps the three layers distinct:

| Layer | Carries |
|---|---|
| **World document** | declares a **verified channel** and its **schema** |
| **`ScenarioV1`** | carries the **claim instances** |
| **Receipts** | prove **acceptance through that channel** |

> **Constraint.** Do **not** introduce a principal-shaped role such as `[worker:w1]` as part of this work. How principals and writers exist in the role system is a **separate question requiring its own sanction**; smuggling one in as a side effect of the verified route would freeze a role-system decision that was never ruled on.

*(Restored in full in 0.2.1; 0.2.0 carried only a pointer. The constraint is the load-bearing half — it is a prohibition, and a prohibition stated only in a superseded document is not in force.)*

### 16.3 Slice B commit order (as executed)

Slice B was authorized in a five-commit order. It executed in eight, and the record states what happened rather than what was planned:

| # | Commit | Status |
|---|---|---|
| 0 | Three-way `CanvasGraphV1` importer (§15.1.1) | as ruled |
| 1 | Mailbox surface declaration + tooling closure (§18) | as ruled |
| 2 | Canonical `AsyncRouteDecl`, separate from `EdgeDecl` | as ruled — the D8/§14b gate |
| 3 | `~~` surface emission + explicit-twin identity proof | as ruled |
| 4 | Reference / native / runtime fold against the Slice A reducer | as ruled |
| 5a | The IC proof-profile split (route-free / route-bearing) | **not in the original order** |
| 5b | The mailbox stage in the reduced profile | **not in the original order** |
| 5c | Seam-1 acceptance selected from the sealed policy | **not in the original order** |

**Eight, and why 5d is not a ninth row.** This revision was itself produced by a further commit, 5d ("freeze integrity"): the corrective cut to this document plus the API seam of §8c. It is deliberately **not** in the table above, and the reason is a distinction worth keeping rather than a preference about counting. The eight rows are the commits that **grounded a construct** — each one moved `~~` from declared to executable, and the sequence is complete because the last of them closed the final gap between declaration and runtime. 5d grounds nothing; it changed no sealed trajectory, no artifact, no backend term and no valid Film. It corrected the *record* of those eight and made one of their frozen statements enforceable in code.

Mixing the two into one list would make "how many commits did `~~` take?" unanswerable, which is the question the section exists to answer. So the grounding count is **eight** and stays eight, and freeze-integrity work is recorded in §"Corrective record: 0.2.0 → 0.2.1" above, where a reader looking for *what changed about the document* will actually look.

> **Why the order grew, recorded because it is the reusable lesson.** Commit 4's gate — "the construct is grounded only when both reducers agree" — was met, and it was not sufficient. Agreement between two runtimes says nothing about whether *either* honours the world's declaration; both can be wrong in the same direction. Commits 5a–5c exist because the reduced profile initially implemented the *frozen* acceptance seam while the world declared the *mailbox* one, and every runtime-agreement check passed throughout.
>
> The general form, and the reason §14b now lists six dimensions rather than four: **a conformance criterion phrased as agreement between implementations cannot detect a shared misreading of the specification.** At least one dimension must compare an implementation against the *declaration*, not against another implementation.
>
> **5d applied the same lesson to this document and to the API.** 5a–5c closed a gap between two runtimes and a declaration; 5d closed the gap between a declaration and the interface that was supposed to implement it. §8 consequence 1 said the acceptance policy is never taken from a caller-supplied option — true of every call site in the tree, and false of `admit_step`'s signature. Nothing was misbehaving, and nothing detected it, because **a public parameter that no caller happens to misuse is invisible to every test that runs callers.** The runtime-agreement lesson generalizes one step further than 5a–5c stated it: agreement among implementations cannot see a shared misreading, and agreement among *call sites* cannot see an API that permits one.

### 16.4 Verified-route staging (ruled, new in 0.2.1)

The `==` implementation is **not** authorized by this revision. What is frozen here is the shape the next ruling packet must respect, because two of its decisions were settled while closing Slice B.

**Authorization and event-key resolution are orthogonal axes.** They answer different questions:

| Axis | Field | Question it answers |
|---|---|---|
| Event-key resolution | `admit_policy_id` | how is **one event key** resolved when multiple candidate facts exist? |
| Verified-channel authorization | `authorization_policy_id` | is **this claimant** authorized to submit **this operation** to **this target** through **this declared channel**? |

**Frozen consequences:**

1. **`==` does not introduce a third `admit_policy_id`.** The closed set of §8 stays at two members. A verified world selects an event-resolution policy by the same rule every other world does.
2. **Receipt eligibility is the conjunction.** `verified-channel authorization AND event-key resolution`. Both must pass before a receipt exists; MAP then applies the accepted operation (§8).
3. **The two fields combine freely.** A mailbox-bearing verified world carries `authorization_policy_id = <channel policy>` with `admit_policy_id = admit_mailbox_deliver_all_v1`; a mailbox-free verified world carries a channel policy with `admit_candidate_min_firstreceipt_v1`. Neither field constrains the other.
4. **`authorization_policy_id` is canonically omitted when no verified channel exists.** It is not added as an empty or defaulted field to every artifact. Existing v1.0 and v1.1 artifacts must retain **byte-identical** canonical encodings; verified worlds take a new IR revision (expected `ir_version = 1.2`).
5. **The role-derived and policy-derived facts must be separated before `==` is implemented.** Slice B measured that `semantic_surface_for_roles()` co-selects four independent facts from one mailbox Boolean. That is currently correct by coincidence and would become wrong the moment a fifth fact stopped correlating:

   | Genuinely role-derived | Genuinely route/policy-derived |
   |---|---|
   | `runtime_state_schema` | `admit_policy_id` |
   | mailbox film projection requirements | `authorization_policy_id` |
   | | proof profile |

6. **Authorization is not hidden inside MAP.** Whether it becomes a named substage of ACCEPT or Core 0.3 names an explicit `AUTHORIZE` phase is open. That it happens *before receipt creation* is not (§8).

The non-negotiable semantic composition is:

```
AUTHORIZE claimant / target / operation family / named policy
  → resolve event key under the existing admit_policy_id
  → mint receipt only if both pass
  → MAP accepted operation
```

---

## 17. Surface sugar tier

Sugar is a **source-to-source pre-pass** that runs in front of the untouched canonical parser.

**Status: `IMPLEMENTED — CLOSURE-PROVEN / IDENTITY-EQUIVALENT / FROZEN`.** `SUGAR_VERSION` remains **`sugar.v2`**. Freezing a tier records that its obligations were discharged; it does not alter the surface, so the version it emits does not move.

> **This section is the single source of the L-0 status.** §16 step 1 cites it rather than restating it. The two previously carried independent wordings and drifted into direct contradiction — §16 said *complete* while §17 said *not closure-proven*. That is the same defect class as a forked vocabulary in code: a second spelling of one fact is not a copy, it is a fork, and it will disagree. Any future status change is made **here** and nowhere else.

**Why L-0 closure includes the sugar tier at all.** L-0 is the claim that the *authored document* survives the toolchain. Sugar is the only construct that makes authored text and parsed text differ, so an unproven sugar tier leaves L-0 asserting something it has not tested.

### 17.1 What "closure-proven" requires (and what it does not accept)

The distinction that governs this section: proving a **mapping exists** is not proving the **toolchain uses it**. A hand-composed demonstration in a battery shows a human *can* trace a generated line back to its origin; it says nothing about whether any shipped diagnostic, completion, or `SemanticDiff` path actually does. Closure requires the latter.

Accordingly the tier is closure-proven only when all of the following hold, each with a **negative control** — an assertion never observed to fail is not yet evidence:

| # | Obligation |
|---|---|
| 1 | a generated-span → authored-span **remapping seam** exists as an API, not as battery-local composition |
| 2 | a **real sugar-aware diagnostics path** performs that remapping, so an error in the *n*-th generated member reports the authored span |
| 3 | a **later** error retains its authored **line *and column*** after an earlier expansion has shifted the generated text |
| 4 | **completion** and **`SemanticDiff`** operate in authored coordinates |
| 5 | bounded-expansion and generated-name-collision rows remain as **additional** coverage, never as substitutes for 1–4 |

**All five were discharged and ratified (0.1.3).** The seam that carried them is worth recording, because it is the reason obligation 4 cost almost nothing: the remap was applied to the **`WrlSourceMap` itself** rather than to each consumer of it. Every span consumer downstream — diagnostics, completion, `SemanticDiff` — then reports authored coordinates without knowing sugar exists. `wrl_diff.locate_changes` required *zero* sugar awareness. Had the remap instead been threaded through each consumer, obligation 4 would have been a per-consumer duty that new consumers could silently omit, and the closure would have decayed the first time one was added.

> **On column exactness.** Columns survive the prepass precisely when the emitted line is **byte-identical** to the authored line. "The line was not expanded" is the wrong test and quietly fails: *value* sugar such as `rotor=identity` → `rotor=16.0.0.0` expands nothing yet shifts every column after it. The remap therefore reports whether a column is exact rather than assuming it.

**The law is: *no sugar-specific identity.*** Stated precisely, because the looser phrasing is false:

- A sugared spelling and its explicit twin desugar to the **same canonical bytes** and therefore seal to the **same** `SemanticArtifactID`. Sugar introduces no identity of its own and no privileged path to the seal.
- It is **not** the claim that editing sugar cannot move an identity. `sp*3` → `sp*4` is a *different program* and moves the identity, exactly as the explicit spelling would.

Two properties are required of any sugar, and are gated by battery:

1. **Bounded expansion.** A one-to-many form must reject an absurd count with a **typed diagnostic** *before* allocating the expansion. `sp*1000000000` is a diagnostic, not an out-of-memory event.
2. **Original-source mapping.** A one-to-many expansion must preserve the **authored spans**, so that diagnostics, completion, `SemanticDiff`, and editor operations all refer to what the author wrote rather than to generated text.

Generated names are judged by the **ordinary seal** — a collision between a generated name and an explicit one is a normal `WRL_DUPLICATE_ID`, not a special sugar rule.

*(Restored in full in 0.2.1. 0.2.0 replaced all of §17 with a status line and "unchanged from 0.1.3", which left the current constitution unable to state what its own `CLOSURE-PROVEN` status means — the five obligations, their negative-control requirement, and the two gated properties all lived only in the superseded file.)*

---

## 18. Surface/registry gap — CLOSED (0.2.0)

0.1.2 recorded a gap: `Mailbox` was a registry role with ports and a config schema that **no author could write down**. 0.1.3 ruled its surface form. 0.2.0 records the closure.

The five **frozen consequences** established while the gap was open are **retained in full** — they are general laws about the registry/surface relationship, not workarounds for one missing lexeme:

1. The surface table is a **projection** of the registry, never a copy of it, and the relationship is stated where the table is defined.
2. Reads of the vocabulary are **total** over the registry: no registry role may make a completion or metadata read crash, whether or not it can be spelled.
3. Completions offer **only writable roles** — a completion is a promise that the text is acceptable if accepted.
4. The gap is **reported**, not hidden behind an absence, and is **computed** rather than hand-listed.
5. Rejections **distinguish** "unknown role" from "registry role with no surface form yet".

> **Consequence 4 is what closed this section.** Because the gap was computed rather than hand-listed, adding the lexeme emptied `unwritable_role_ids()` automatically. No edit to a list was required, and no list could be left stale. A hand-maintained allowlist would have needed a sixth spelling of the vocabulary and would have drifted exactly as the other three did.

### 18.1 The Mailbox surface form (frozen)

```
[mailbox:mb](w=8, cap=4){}
```

| Element | Frozen |
|---|---|
| `w`, `cap` | **required**, not defaulted |
| `{}` | **explicitly** denotes empty structural ports |
| identity | enters world identity through the canonical `MailboxDecl` — no new identity construct |
| topology | Mailbox **cannot participate in `--`** |
| kind | **not** an ordinary actor with a behavior table |

> **Why `{}` is written rather than omitted.** An absent port block and an empty one are different claims: the first says nothing, the second says *nothing connects here structurally*. Since Mailbox is precisely the role reached by a **logical route** and not by a structural edge, the empty block is the part of the declaration that carries the meaning.

> **Why `w` and `cap` are required.** Defaulting either would put a runtime-observable value into world identity that the author never wrote. Two documents that look different would seal the same, or — worse — a default change would move every existing `SemanticArtifactID` silently.

---

## 19. Logical routes — `AsyncRouteDecl` (frozen, new in 0.2.0)

This section discharges the D8/§14b constraint that gated the `~~` promotion: *promoting `~~` requires a canonical logical route declaration that is **distinct from `EdgeDecl`**, not a new `EdgeDecl` kind.*

**Frozen distinction — two kinds of connection:**

| | **Structural edge** (`EdgeDecl`) | **Logical route** (`AsyncRouteDecl`) |
|---|---|---|
| Texture | `--` | `~~` |
| Settles | within the period, in the REACT fixpoint | at the **next** period boundary |
| Endpoint | a wired port on a world role | a **mailbox** |
| Participates in REACT | yes | **no** |
| Appears in the world's edge list | yes | **no** |

**Canonical shape (frozen):**

```
AsyncRouteDecl { source_id, route_tag, mailbox_id, body }
```

**Surface form (frozen):**

```
[p0] ~~msg~~> [mb] (body=0.0.0.7)
```

**Frozen consequences:**

1. **A logical route is not an edge in disguise.** It is a separate declaration in a separate collection. A world's edge list is unchanged by adding an async route — which is the observable form of the D8 constraint, and the property that makes the distinction checkable rather than merely asserted.
2. **The route enters world identity.** `AsyncRouteDecl` is world content (§15); adding, removing, or retagging a route moves the `SemanticArtifactID`. Presentation of the route does not.
3. **`body` is required and fully written.** As with `w`/`cap` on the mailbox (§18.1), no lane of the body is defaulted: a defaulted lane would place a runtime-observable value into world identity that the author never wrote.
4. **A `~~` line is judged as a route, however malformed.** A syntactically broken async route produces a typed route diagnostic, never a fallback reading as some other construct. A surface that silently reinterprets a malformed route as an edge would reintroduce the conflation this section exists to prevent.
5. **The route is directed into a mailbox, never into a role that could take a `--` edge.** Mailbox cannot participate in `--` (§18.1) and no other role may terminate a `~~`. The two connection kinds therefore have disjoint endpoint sets, which is what keeps the REACT fixpoint's input set unambiguous.
6. **Delivery is period-boundary semantics, not a fast edge.** A message enqueued during period *t* is observable in period *t+1*. This is the frozen meaning of the `~~` texture (§5) and is what makes the construct unrepresentable as an `EdgeDecl` regardless of how one might be annotated.

> **Why this is a Route (§1) and not a new construct kind.** The ten construct kinds are closed, and `Route` is already defined as *"communicates — a directed, textured transition edge"*. `~~` is a Route with the async texture. What §19 adds is not a kind but the recognition that a Route's **canonical representation depends on its texture** — a synchronous Route is an `EdgeDecl`, an asynchronous one is an `AsyncRouteDecl`. 0.1.x's `EdgeDecl` was never "the representation of Route"; it was the representation of the one texture that had been grounded.

---

*End of WRL Core 0.2.1. **§16 steps 1 and 2 are complete.** The live deliverable is §16 step 3, the `==` verified route — and §16.1 is the standing warning that it is further from free than it looks.*

*What 0.2.0 left open about `==` is now partly settled and recorded in §16.4: authorization and event-key resolution are **orthogonal** policy axes, and `==` introduces **no third** `admit_policy_id`. What remains open is the `VerifiedRouteDecl` shape, its surface spelling, the claimant representation (without a new principal role — §16.2), the `authorization_policy_id` schema, the authorized receipt projection, and the Film/replay authorization evidence. Those belong to the verified-route ruling packet, and the parser and runtime for `==` are **not** authorized before it.*
