# WRL Core 0.1.3 — Frozen Family Extract

*Status: **frozen** (families only). Extracted from `WRL.md` (Complete Design Draft) per the WRL ruling, Phase 1. This file is the living Core-0.1.x document (filename retained); the current revision is **0.1.3**.*

> **Errata 0.1 → 0.1.1 (per GPT-5.6 ruling, 2026-07-21).** Before freezing Forge Semantic IR v1, five corrections were required so the frozen core reflects the ADMIT + persistent-world results rather than the older actor execution model: (1) the period cycle is **OBSERVE→ACCEPT→MAP→COMMIT→REACT→FILM**, not Collect→Order→Reduce→Commit→Record; (2) "conflicts dissolve" is narrowed — single ownership stops generic cell races but claim/control conflicts need explicit policies; (3) canonical ordering is **policy-pinned**, not a fixed hash formula; (4) history splits into **WorldFrame / EventLedger / BuildFilm**; (5) the grounding language distinguishes grounded from reserved/partial. These land in §8, §9, §11, and the new §8b + corrected §14 below.

> **Errata 0.1.1 → 0.1.2 (per GPT-5.6 ruling, 2026-07-25).** Four corrections, none of which move a frozen family — they make the *grounding claims* honest and add the two structural facts the implementation established after 0.1.1 was written:
>
> 1. **Mailbox is `partial`, not `reserved`.** `MailboxDecl` is grounded in the canonical IR and the runtime, but the WRL `~~` route construct is **not surface-emittable** and has no structural `EdgeDecl`. Mailbox is therefore **not** a sixth surface-grounded role — it is IR/runtime-grounded and **surface-partial**. §14 is corrected and §14b is new.
> 2. **`*` is narrowed.** Only the **replication-by-position** meaning is implemented; **wildcard matching remains reserved** with no lowering. §4 is corrected.
> 3. **The document boundary is normative** (new §15). A WRL world document and a `ScenarioV1` are different documents. `periods` and `[epoch:N]` claims are **run inputs** and are deliberately outside the `SemanticArtifactID`. The strict world parser is normative; the combined-document parser is an explicitly-named migration bridge.
> 4. **The Core 0.2 promotion order is recorded** (new §16), together with the conditions each construct must meet before it may be promoted.

> **Errata 0.1.2 → 0.1.3 (per GPT-5.6 ruling, 2026-07-25 — L-0 RATIFIED).** This revision is **administrative**: it changes no frozen family, no semantic identity, and no runtime code. It exists as a **new revision rather than an edit to 0.1.2** because 0.1.2's status was *"closure submitted, not ratified"* and that was true when written. Overwriting it in place would have destroyed the record of a claim having been reviewed rather than self-certified — the document would then assert that L-0 was always closed, which is exactly the kind of retroactive tidying a frozen spec exists to prevent. Four changes:
>
> 1. **§17 is set to `IMPLEMENTED — CLOSURE-PROVEN / IDENTITY-EQUIVALENT / FROZEN`.** The sugar tier is closed. `SUGAR_VERSION` remains `sugar.v2` — a ratification is not a version bump, and moving it would have implied a surface change that did not occur.
> 2. **§16 step 1 (L-0 closure) is complete**, recorded *by reference to §17* rather than by a second wording of the same fact (the single-source rule installed in 0.1.2).
> 3. **The `CanvasGraphV1` compatibility importer is named** (§15.1.1): `import_canvas_graph_v1(canvas) -> LegacyCanvasImportV1(world, scenario, presentation)`. This is **Slice B Commit 0**.
> 4. **The Mailbox surface declaration is ruled** (§18): `[mailbox:mb](w=8, cap=4){}`, shipping in the same unfrozen Slice B line as the first `~~` route.
>
> Items 3 and 4 are **recorded as ruled Slice B work, not frozen here.** Slice B is unfrozen by construction; writing its decisions into a frozen revision would freeze a surface that has not yet been built.

This document commits the **meaning families** of WallRiderLang that the TRVM runtime and the Forge semantic graph have grounded. It freezes *which kinds of things exist and what each kind means* — **not** the detailed surface rules, which remain a design draft in `WRL.md` and may still change.

**Freezing a family** means: the set of members is closed, and each member's meaning-role is settled. It does **not** freeze exact glyphs, argument grammars, sugar, or edge-case rules — those live in `WRL.md` and are Experimental/Proposed until a later frozen revision promotes them.

When `WRL.md` and this file conflict about *what is settled*, **this file wins**. `WRL.md` remains authoritative for full rationale and forward design.

---

## 0. Architectural rule (frozen)

WRL denotes the **canonical Forge semantic graph**. It is **not** lowered by compiling surface syntax directly to hand-written interaction-calculus text. The only sanctioned path is:

> WRL source / canvas → canonical **semantic graph** → **Forge Semantic IR** → TRVM facts / films / reductions.

Forge Semantic IR v1 is a separate gated deliverable (Phase 2). Until it is frozen, no lowering target is normative.

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

Of these, **Actor, Route, Wall, Period, Film, Hash** are additionally grounded by TRVM today (§ below). **Function, Fragment, Stencil, Derive** are frozen *as kinds* but their detailed semantics remain draft.

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

**Implementation status of `*` (0.1.2).** The symbol's *family role* stays frozen as written, but the two meanings are at different maturities and the spec must not imply otherwise:

| Meaning | Status |
|---|---|
| **replication-by-position** (`[relay:r*3]`) | **implemented** — surface sugar, bounded, identity-equivalent (see §17) |
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

**Surface status (0.1.2).** Freezing a texture's *meaning-role* is not the same as grounding its *construct*. Only `--` is surface-grounded today:

| Texture | Surface status | See |
|---|---|---|
| `--` solid | **surface-grounded** — declarable, emittable, round-trips | §14 |
| `~~` async | **partial** — IR/runtime-grounded, not surface-emittable, no structural `EdgeDecl` | §14b, §16 |
| `==` verified | **partial** — acceptance machinery exists; the construct does not | §16.1 |
| `!!` fault | **partial** — fault *state* exists; route + supervision do not | §16 |

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

---

## 8. Execution-model family — the deterministic reactive floor (frozen)

Grounded directly by TRVM's deterministic reduction, ADMIT reducer, persistent fold, and replayable films.

**Configuration** (frozen shape): the persistent runtime state — world state (owned state cells), monotone claim facts, immutable acceptance receipts, capacity-fault latches, clock state, poses, rotors, numeric faults; plus static topology + policies. (Mailboxes/supervisor/behavior tables are Experimental, not part of the frozen floor.)

**Two frozen invariants** (enforced statically):
1. **Single-owner cells** — no shared mutable cell.
2. **Disjoint deterministic guards** — at most one deterministic rule enabled per actor-state; genuine choice must be an explicit `scored` branch.

**Period cycle** (frozen 6 phases): the proven Forge/TRVM epoch boundary is
**OBSERVE** (canonicalize + insert distinct claims) →
**ACCEPT** (create missing receipts per the pinned acceptance policy) →
**MAP** (newly-accepted successful ops → controls) →
**COMMIT** (apply control writes + fault resets to owned cells) →
**REACT** (deterministic within-period token cascade to fixpoint; latch current overflow) →
**FILM** (record the entries needed to replay the epoch).

For claim-free profiles the first three phases (OBSERVE/ACCEPT/MAP) **degenerate to identity but must not disappear** from the semantic model: the OBSERVE/ACCEPT/MAP distinction is what determines which claims were seen, which candidate was accepted, whether a retransmission retries an effect, which controls were committed, and whether a same-epoch configuration affects that epoch's reaction.

**Canonical ordering is policy-pinned (frozen as a family, not a formula).** Events and accepted operations are ordered by a *total canonical key whose schema and policy identity are part of the semantic artifact*. Worker arrival order is never semantic. The current ADMIT profile pins the `CandidateKey` + canonical accepted-event ordering; a future mailbox profile may pin a different key. The *existence and policy-pinning* of the key is frozen; the specific formula is not.

**Conflicts (narrowed — corrected in 0.1.1):** *cell-write conflicts are structurally constrained; claim and control conflicts are resolved by explicit, policy-pinned recognition, acceptance, and canonical application laws.* Concretely:
- single-owner cells remove generic write-write races;
- append and fact-union structures merge deterministically;
- but equivocation, conflicting accepted operations, claim retransmission, receipt divergence, configuration ordering, fault-reset-vs-new-overflow, and capacity failure are **not** dissolved by ownership — each is resolved by an explicit pinned policy (recognition = distinct-CandidateKey count; acceptance = MIN CandidateKey / first-receipt; application = canonical event order; fault = COMMIT-clears-then-REACT-ORs; capacity = atomic latch, no partial).

Not frozen: the podium/ranking ceiling (§20.7), scored-branch scoring functions, distributed termination detection.

## 8b. History family — WorldFrame / EventLedger / BuildFilm (frozen: 3 distinct artifacts)

"Film" is not one undifferentiated object. Three conceptual artifacts are frozen distinct (their current serialization is the Film v0.6/v0.7 family):

| Artifact | Frozen role |
|---|---|
| **WorldFrame** | authoritative observable state sufficient for future behavior (the physical world snapshot; Film v0.6 bytes) |
| **EventLedger** | accepted events, receipts, effects, outcomes (the claim-aware layer; Film v0.7 adds this over v0.6) |
| **BuildFilm** | compiler/build provenance (Proposed; §36) |

A replay package is frozen as:

```
ReplayBundle { initial_artifact, initial_state, event_ledger, frames, policy_ids }
```

Frozen: the three-way WorldFrame/EventLedger/BuildFilm distinction and the ReplayBundle shape. Not frozen: byte layouts (they are the Film v0.6/v0.7 serialization, a backend concern).

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

These observable properties are frozen as *families of guarantee* (their exact test matrices remain draft in §46):

- **Formatting invariance** — presentation never changes the hash.
- **Replay exactness** — a live run and its replay share all observables.
- **Build invariance** — same inputs → identical film + hashes across hosts.
- **Merge laws** — fact union is commutative/associative/idempotent.
- **Boundary safety** — undeclared effects cannot cross walls.
- **Scheduler invariance** — worker ordering never changes the committed film.
- **World round-trip** *(0.1.2)* — a format→parse cycle preserves the complete canonical world projection, defined by exclusion (§15).
- **Identity round-trip** *(0.1.2)* — a format→parse cycle preserves the canonical artifact bytes and the `SemanticArtifactID`.
- **Document separation** *(0.1.2)* — a world document excludes run inputs both semantically and lexically (§15).

---

## 13. What Core 0.1 does NOT freeze

Deferred to later frozen revisions (see `WRL.md` tier table):

- **Experimental:** the entire expression notation (values/functions/types/generics/numerics), effects/capabilities/entropy, the supervision error ladder, streams/backpressure, actor behavior blocks, evolution/migration, podium/ranking, static-check catalog, execution profiles.
- **Proposed:** metaprogramming (fragments/stencils/derives/reflection/sealed compiler tools) beyond their kind-role, modules/builds, build films, foreign functions, and all distributed settlement above fact-union.

*(0.1.2: "mailboxes" was removed from the Experimental list — the mailbox is no longer merely experimental, it is IR/runtime-grounded and surface-partial. See §14b. It is still not promoted.)*

Promotion path: a family moves from Experimental → Core only after it is **surface-grounded** (§14b) in a running Forge/TRVM implementation, at which point this file is revised (0.2, 0.3, …). The steered order for 0.2 is recorded in §16.

---

## 14. TRVM grounding — corrected (0.1.1)

Grounding is stated honestly: **grounded** = an isomorphic TRVM lowering exists; **partial/reserved** = the concept is grounded but the WRL language construct is not, or the construct is reserved with no lowering.

*(0.1.2: the word "grounded" was doing two jobs. §14b now splits it into **IR/runtime-grounded** and **surface-grounded**. Every entry in the table below is surface-grounded.)*

**Grounded:**

| Family | TRVM grounding |
|---|---|
| The five **surface-grounded** world roles (Pulser/Relay/Door/Spinner/Orb) — see §14b, Mailbox is **not** a sixth | fixture.py node kinds; lowered by compiler.py/lower_e2a.py |
| State + wiring | state schema (counters, wires, rotor-as-state, pose, sticky fault); sig-wire + socket edges |
| Deterministic signal route (`--`) | sig-wire delivery; within-period REACT fixpoint |
| Periods | epoch-by-epoch persistent fold (3b.5e/3b.5f) |
| WorldFrame / EventLedger (§8b) | Film v0.6 (physical) / v0.7 (claim-aware); replay exactness proven |
| Content identity (§11) | content-addressed rulepack hash; digest / CandidateKey packing |
| Fact union (§9) | monotone claim-fact SET UNION; immutable receipts kept separate |
| ADMIT acceptance core (§8) | OBSERVE→ACCEPT→MAP reducer, single-epoch + persistent fold (3b.5f, ref==native) |
| Commit/react sequencing (§8, §10) | COMMIT (control writes + fault resets) → REACT → latch overflow |

**Reserved or partial (NOT a complete grounding):**

| Family | Status |
|---|---|
| Async route / mailbox (`~~`) | **partial** — `MailboxDecl` is grounded in the canonical IR and the runtime, but the `~~` route construct is **not surface-emittable** and has **no structural `EdgeDecl`** (see §14b) |
| Verified route (`==`) | **partial** — acceptance machinery grounded, but the route *construct* is not a complete lowering (see §16 for the condition it must meet) |
| Fault route + supervision (`!!`) | **partial** — numeric-fault *state* grounded; the route/supervision *construct* is not, and no supervision floor exists yet |
| Capability gate (`/gate`) | **reserved** — no capability-gate node kind yet |
| Seal / artifact registry (`///seal`) | **partial** — commit grounded; seal registry is Proposed |
| General actor behaviors | **reserved** — Experimental; no arbitrary-behavior runtime exists |
| Wildcard `*` | **reserved** — only replication-by-position is implemented (§4) |

---

## 14b. Surface-grounded vs IR-grounded (frozen distinction, new in 0.1.2)

0.1.1 used a single word, *grounded*, for two genuinely different achievements. Conflating them let the Mailbox work read as if it had promoted a route texture, which it had not. 0.1.2 splits the term:

| Term | Means |
|---|---|
| **IR/runtime-grounded** | a canonical IR declaration exists, the runtime executes it, and it is covered by a battery |
| **surface-grounded** | *additionally*, WRL source can **declare** it, the formatter can **emit** it, and it round-trips through the canonical bytes |

A construct is only eligible for promotion into a frozen Core family when it is **surface-grounded**. IR/runtime grounding alone is necessary but not sufficient.

**Mailbox is the worked example.** `MailboxDecl` is IR/runtime-grounded: it exists in the canonical IR, the runtime honours it, and the Slice A networking battery covers it. It is **not** surface-grounded: there is no `~~` surface form to write, the formatter cannot emit one, and — decisively — there is **no structural `EdgeDecl`** for it.

> **Mailbox is not a sixth *surface-grounded* role.** The five world roles (Pulser/Relay/Door/Spinner/Orb) are surface-grounded. Mailbox is IR/runtime-grounded and **surface-partial**.
>
> The networking track's Slice A spec is correct to call Mailbox a sixth **IR** role — that is exactly what it added, additively, without moving any pre-existing identity. What must not be inferred from it is that WRL now has six surface roles, or that the async route texture was promoted. It did not, and it was not.

The `EdgeDecl` point is the one that constrains the next slice. An async route is **not** an ordinary structural edge — it does not settle within the period, so it cannot participate in the within-period REACT fixpoint the way `--` does. Promoting `~~` therefore requires a **canonical logical route declaration that is distinct from `EdgeDecl`**, not a new `EdgeDecl` kind. (This is the standing D8 constraint; see §16.)

---

## 15. The document boundary (normative, new in 0.1.2)

A **world** and a **run of that world** are different documents. This was established by the v0.4-0 implementation slice and is now normative for the language.

| Document | Carries | Enters `SemanticArtifactID`? |
|---|---|---|
| **World document** | profile, objects, edges, static config, wiring | **yes** |
| **`ScenarioV1`** | `periods`, `[epoch:N]` claims, run inputs | **no** |

**Frozen consequences:**

1. **Run inputs are not world content.** `periods` and `[epoch:N]` claims are run inputs. Changing them does not move the `SemanticArtifactID`; the same world can be run by many scenarios.
2. **A world formatter emits a world document.** It must exclude scenario syntax both *semantically* (reparsing yields no run inputs) and *lexically* (the emitted text does not contain scenario syntax at all). The lexical half is load-bearing: a formatter emitting a literal `periods 0` would satisfy the semantic half while still writing scenario syntax into a world document.
3. **Round-trip laws split in two.** The **world** round-trip preserves the complete canonical world projection; the **identity** round-trip preserves the canonical artifact bytes and the `SemanticArtifactID`. Neither subsumes the other.

> The world projection is defined by **exclusion** — every canonical field *except* the run inputs — and never as a fixed tuple such as `(profile, nodes, edges)`. A fixed tuple silently stops covering any field a later slice adds; §16 adds route semantics, which such a tuple would omit.

### 15.1 The two parser mouths

**The strict world parser is normative.** Parameterizing the parser is sanctioned only as a **migration bridge**, and only through an unmistakable API — never a boolean flag on one function:

| Entry point | Accepts | Status |
|---|---|---|
| `parse_wrl_core(text)` | world source **only**; rejects run inputs with a typed `WRL_WORLD_SOURCE_HAS_SCENARIO` | **normative** |
| `parse_wrl_legacy_document(text)` | a pre-boundary **combined** document | explicit compatibility path |

The legacy path's destination is to **split** a combined document into `WorldDocumentV1 + ScenarioV1` rather than to keep parsing it forever.

### 15.2 The lexical form of the boundary (normative)

The lexical half of consequence 2 needs a stated vocabulary, because a wrong one silently changes where the boundary sits. Run-input syntax is recognised by **anchored line forms**, not by substrings:

| Form | Matches |
|---|---|
| `^\s*periods\b` | a `periods` **declaration** |
| `^\s*\[epoch:` | an `[epoch:N]` **claim line** |

Two properties of this definition are load-bearing:

- **`@` is not a marker.** `@` is frozen for world addressing and placement (§4), so it appears in perfectly legal world source — `[orb:ob]@(3,4){pose}` is a world line. Treating a bare `@` as scenario syntax rejects valid worlds.
- **Claim *operations* are not listed.** `SetRotor` and `ResetFault` are deliberately absent: every claim line is already anchored by `[epoch:`, and listing the operations as well would create a second, drifting definition of what a claim is. Matching them as substrings also misfires on legal identifiers such as `[relay:ResetFault_gate]`.

> **One definition, one spelling.** This vocabulary lives at exactly one place in the implementation and every consumer — parser, formatter law, batteries, probes — reads it from there. A hand-rolled second spelling is a **fork, not a copy**: it drifts silently, and a lexical law whose vocabulary disagrees with the parser's does not test the document boundary, it tests a private opinion about it.

### 15.3 What splitting a combined document preserves

The split is **order- and position-preserving**, not layout-*reconstructing*. The precise invariant:

> For every line *N* of the input, line *N* sits at index *N* of whichever side received it, retains its original line ending, and the two sides **recombine to the input exactly**.

It is stated as recombination rather than as "both sides have the same line count" because a final **empty, unterminated** line is textually invisible — an inherent property of text, not a defect in the split. The weaker phrasing would have been false for exactly that case while the real invariant holds.

### 15.1.1 `CanvasGraphV1` — frozen as legacy (ruled)

`CanvasGraphV1` — the Phase-3C presentation surface — was never migrated across this boundary: it still carries top-level `periods`/`batches`, making it the structural parallel of `parse_wrl_legacy_document`. This was never a live defect, because the production canvas path is `CanvasLayoutV1`, which is world-only by construction. The disposition is now ruled:

1. **Frozen as an immutable legacy combined-document surface**, and **retired from active development**.
2. **No new semantic fields.** `AsyncRouteDecl`, `~~`, and any other §16 construct must **not** be added to V1. Extending a surface that sits on the wrong side of the document boundary would re-import the boundary violation into every new construct.
3. **A named compatibility importer is preserved**, splitting V1 content three ways — **world**, **`ScenarioV1`**, and **presentation**. Three, not two: V1 conflates all three, and a two-way split would silently fold presentation into world content, moving `SemanticArtifactID`s that must not move.
4. **The successor is world-only.** Slice B targets either the existing `CanvasLayoutV1` composition — if it can represent logical routes — or a new world-only `CanvasWorldV2`/`CanvasGraphV2`.
5. **The successor must distinguish structural `EdgeDecl` connections from logical route declarations** (the same D8/§14b requirement that gates `~~` itself).
6. **Export back to V1 must reject any lossy downgrade involving async routes** with a typed error, rather than emitting a V1 document that silently drops them.

**The importer is named (ruled, 0.1.3).** It is **Slice B Commit 0** — it lands *before* `AsyncRouteDecl` is introduced (§16.3):

```
import_canvas_graph_v1(canvas) -> LegacyCanvasImportV1(world, scenario, presentation)
```

| Component | Content |
|---|---|
| `world` | the canonical **world projection**, run inputs **excluded** |
| `scenario` | `periods` and the ordered epoch claim batches, preserved **exactly** |
| `presentation` | `CanvasLayoutV1` |

Its battery must prove five things: **semantic-ID preservation**, **runtime-film preservation**, **presentation inertness**, **strict three-way separation**, and **typed rejection** when a route-bearing successor is exported lossily back to V1 (point 6 above).

> **Why five and not "it round-trips".** A round-trip assertion alone would pass for an importer that folded presentation into world content and then folded it back out again — the trip closes while the `SemanticArtifactID` moves in the middle. Separation and inertness have to be asserted directly, against the projection, not inferred from the ends of a loop.

> **Consequence for sequencing.** `CanvasGraphV1` no longer blocks Slice B. The remaining blocker on step 1 was the sugar-tier closure of §17, **discharged in 0.1.3**. `CanvasGraphV1` itself remains **immutable and retired**: the importer reads it, nothing writes new meaning into it.

---

## 16. Core 0.2 promotion order (recorded, new in 0.1.2)

The order below is **steered, not merely preferred** — each step supplies something the next one needs, so reordering them produces constructs that cannot be grounded honestly.

| # | Step | Gate it must pass |
|---|---|---|
| 1 | ~~**L-0 closure**~~ — **COMPLETE (0.1.3)** | the round-trip and document-boundary laws restated and green, **and** the surface sugar tier closure-proven — **status: see §17 (single source)** |
| 2 | **`~~` async route (Slice B)** — *authorized, in progress* | needs a **canonical logical route declaration distinct from `EdgeDecl`** (D8, §14b); see §16.3 for the ruled commit order |
| 3 | **`==` verified route** | see the grounding condition below |
| 4 | **`#` references and `&` composition** | — |
| 5 | **`//commit` and `///seal`** | — |
| 6 | **`!!` fault route** | may only follow a **minimal supervision floor** actually existing |
| 7 | **`/gate` capability gate** | last |

### 16.3 Slice B commit order (ruled, new in 0.1.3)

Slice B is authorized in this order. The order is load-bearing in the same way §16's is — each commit supplies something the next needs:

| # | Commit | Why it sits here |
|---|---|---|
| 0 | **Three-way `CanvasGraphV1` importer** (§15.1.1) | must land *before* `AsyncRouteDecl` exists. An importer written after the new construct would have to decide what a route means in a legacy document that can never contain one — a question with no honest answer |
| 1 | **Mailbox surface declaration + tooling closure** (§18) | the route needs an endpoint that can be written down |
| 2 | **Canonical `AsyncRouteDecl`, separate from `EdgeDecl`** | the D8/§14b gate itself |
| 3 | **`~~` surface emission + explicit-twin identity proof** | the surface may only follow the canonical form it denotes |
| 4 | **Reference / native / runtime fold against the Slice A reducer** | the construct is grounded only when both reducers agree |

> **Do not freeze an inert mailbox-only release.** The Mailbox declaration and the first `~~` logical route ship in the **same unfrozen line**. A frozen release containing an endpoint with nothing that can reach it would freeze a surface whose meaning had never been exercised.

**Pre-freeze obligation.** Before Slice B freezes, `WRL_PORT_SIGNATURE` must carry a **validator-owned canonical locator**. Diagnostics must not independently rediscover the offending construct: a consumer that re-derives *where* an error happened is a second spelling of the validator's own knowledge, and will disagree with it — the forked-vocabulary defect (§18, consequence 1) in its diagnostic form.

### 16.1 `==` is not "almost free"

It is tempting to read the verified route as nearly grounded, because ADMIT already accepts claims. That reading confuses two different things:

- the **declaration** `==` would introduce is *authorization structure*;
- the **frozen texture** `==` denotes an *evidence-backed transition*.

`==` is grounded **only when ADMIT enforces all four** of: the **claimant**, the **target**, the **operation family**, and a **named policy**. Anything less is a route that looks verified and is not.

### 16.2 Permission / instance split (approved)

The split is approved, with terminology that keeps the three layers distinct:

| Layer | Carries |
|---|---|
| **World document** | declares a **verified channel** and its **schema** |
| **`ScenarioV1`** | carries the **claim instances** |
| **Receipts** | prove **acceptance through that channel** |

> **Constraint.** Do **not** introduce a principal-shaped role such as `[worker:w1]` as part of this work. How principals and writers exist in the role system is a **separate question requiring its own sanction**; smuggling one in as a side effect of the verified route would freeze a role-system decision that was never ruled on.

---

## 17. Surface sugar tier (status, new in 0.1.2)

Sugar is a **source-to-source pre-pass** that runs in front of the untouched canonical parser.

**Status: `IMPLEMENTED — CLOSURE-PROVEN / IDENTITY-EQUIVALENT / FROZEN`** *(ratified by GPT-5.6 ruling, 2026-07-25; 0.1.2 carried `CLOSURE SUBMITTED, NOT RATIFIED`).*

`SUGAR_VERSION` remains **`sugar.v2`**. Freezing a tier records that its obligations were discharged; it does not alter the surface, so the version it emits does not move.

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

---

## 18. Known surface/registry gap (recorded, new in 0.1.2)

The frozen **role registry** and the WRL Core **text surface** are not currently equal. `Mailbox` is a registry role with ports and a config schema that **no author can write down**: there is no surface lexeme for it.

This is recorded rather than silently repaired because giving `Mailbox` a text spelling is a **language decision belonging to Slice B**, not a tooling fix. What *was* repaired is the dishonesty the gap produced:

| Symptom | Why it was wrong |
|---|---|
| the completion API raised a bare `KeyError` | a vocabulary read that **crashes** reports nothing about its own cause; it was dead for every caller |
| the surface manifest documented itself as unable to drift | the claim was false in both directions — it crashed on the gap, and would have advertised an unwritable role had it not |
| the parser said the role "is not in the frozen v1 registry" | it **is** in the registry; the message sent authors to fix the wrong thing entirely |

**Frozen consequences:**

1. The surface table is a **projection** of the registry, never a copy of it, and the relationship is stated where the table is defined.
2. Reads of the vocabulary are **total** over the registry: no registry role may make a completion or metadata read crash, whether or not it can be spelled.
3. Completions offer **only writable roles** — a completion is a promise that the text is acceptable if accepted.
4. The gap is **reported**, not hidden behind an absence, and is **computed** rather than hand-listed. A hand-listed allowlist would be a fourth spelling of the same vocabulary and would drift exactly as the other three did; computed, it empties itself when a lexeme is added and grows itself when a role is added without one.
5. Rejections **distinguish** "unknown role" from "registry role with no surface form yet".

### 18.1 The Mailbox surface form (ruled, new in 0.1.3)

The gap is ruled closed in **Slice B** — recorded here, not frozen here, because Slice B is unfrozen:

```
[mailbox:mb](w=8, cap=4){}
```

| Element | Ruling |
|---|---|
| `w`, `cap` | **required**, not defaulted |
| `{}` | **explicitly** denotes empty structural ports |
| identity | enters world identity through the **existing canonical `MailboxDecl`** — no new identity construct |
| topology | Mailbox **cannot participate in `--`** |
| kind | **not** an ordinary actor with a behavior table |

> **Why `{}` is written rather than omitted.** An absent port block and an empty one are different claims: the first says nothing, the second says *nothing connects here structurally*. Since Mailbox is precisely the role that is reached by a **logical route** and not by a structural edge, the empty block is the part of the declaration that carries the meaning. Allowing it to be elided would make the one distinguishing fact about the role invisible in its own declaration.

> **Why `w` and `cap` are required.** Defaulting either would put a runtime-observable value into the world identity that the author never wrote. Two documents that look different would seal the same, or — worse — a default change would move every existing `SemanticArtifactID` silently.

This closes the gap §18 records: once the lexeme exists, `unwritable_role_ids()` empties itself. That it is **computed** (consequence 4) is what makes the closure automatic rather than a further edit.

---

*End of WRL Core 0.1.3. **§16 step 1 (L-0 closure) is complete** — see §17, the single source. The live deliverable is §16 step 2, the `~~` async route (Slice B), authorized in the commit order of §16.3: the three-way `CanvasGraphV1` importer (§15.1.1) first, then the Mailbox surface declaration (§18.1), then `AsyncRouteDecl` distinct from `EdgeDecl`, then `~~` emission with its explicit-twin identity proof, then the reference/native fold. The exact `~~` spelling and the canonical route-key schema are **not settled here** — they belong to the Slice B ruling packet.*
