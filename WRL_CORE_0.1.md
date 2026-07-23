# WRL Core 0.1.1 — Frozen Family Extract

*Status: **frozen** (families only). Extracted from `WRL.md` (Complete Design Draft) per the WRL ruling, Phase 1. This file is the living Core-0.1.x document (filename retained); the current revision is **0.1.1**.*

> **Errata 0.1 → 0.1.1 (per GPT-5.6 ruling, 2026-07-21).** Before freezing Forge Semantic IR v1, five corrections were required so the frozen core reflects the ADMIT + persistent-world results rather than the older actor execution model: (1) the period cycle is **OBSERVE→ACCEPT→MAP→COMMIT→REACT→FILM**, not Collect→Order→Reduce→Commit→Record; (2) "conflicts dissolve" is narrowed — single ownership stops generic cell races but claim/control conflicts need explicit policies; (3) canonical ordering is **policy-pinned**, not a fixed hash formula; (4) history splits into **WorldFrame / EventLedger / BuildFilm**; (5) the grounding language distinguishes grounded from reserved/partial. These land in §8, §9, §11, and the new §8b + corrected §14 below.

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

---

## 13. What Core 0.1 does NOT freeze

Deferred to later frozen revisions (see `WRL.md` tier table):

- **Experimental:** the entire expression notation (values/functions/types/generics/numerics), effects/capabilities/entropy, the supervision error ladder, mailboxes/streams/backpressure, actor behavior blocks, evolution/migration, podium/ranking, static-check catalog, execution profiles.
- **Proposed:** metaprogramming (fragments/stencils/derives/reflection/sealed compiler tools) beyond their kind-role, modules/builds, build films, foreign functions, and all distributed settlement above fact-union.

Promotion path: a family moves from Experimental → Core only after it is grounded in a running Forge/TRVM implementation, at which point this file is revised (0.2, 0.3, …).

---

## 14. TRVM grounding — corrected (0.1.1)

Grounding is stated honestly: **grounded** = an isomorphic TRVM lowering exists; **partial/reserved** = the concept is grounded but the WRL language construct is not, or the construct is reserved with no lowering.

**Grounded:**

| Family | TRVM grounding |
|---|---|
| Five concrete world roles (Pulser/Relay/Door/Spinner/Orb) | fixture.py node kinds; lowered by compiler.py/lower_e2a.py |
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
| Async route / mailbox (`~~`) | reserved in WRL, absent from the floor — no mailbox node exists |
| Verified route (`==`) | acceptance machinery grounded, but the route *construct* is not a complete lowering |
| Fault route + supervision (`!!`) | numeric-fault *state* grounded; the route/supervision *construct* is not |
| Capability gate (`/gate`) | no capability-gate node kind yet |
| Seal / artifact registry (`///seal`) | commit grounded; seal registry is Proposed |
| General actor behaviors | Experimental; no arbitrary-behavior runtime exists |

---

*End of WRL Core 0.1.1. Next gated deliverable: Forge Semantic IR v1 (Phase 2) — a restricted `deterministic-circuit-world` profile — the sanctioned lowering target for this frozen core.*
