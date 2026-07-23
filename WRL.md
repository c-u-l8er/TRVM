# WallRiderLang (WRL) — Complete Design Draft

*A spatial actor language in which computation is represented as staged movement through bounded space. This document defines the language in full: its notation, its meaning, its execution model, its metaprogramming system, and its content-identity model. It is written to be read cold — no prior context is assumed.*

**Contents.** Part I — Foundations (§1–9). Part II — The Expression Notation (§10–17). Part III — Process Semantics (§18–27). Part IV — Metaprogramming (§28–34). Part V — Programs at Scale (§35–38). Part VI — Reference (§39–46).

---

## Status and stability (READ FIRST)

> **This is a complete *design draft*, not a frozen specification.** The document below describes WallRiderLang in full so it can be read and evaluated cold. It is deliberately ambitious and its detailed rules are **not yet frozen**. Do not implement it verbatim as if it were a ratified standard, and do not announce any part of it as "shipped" until it has been extracted into a frozen core (see below).

**Grounding.** WRL is the surface language for the **canonical Forge semantic graph**. The stable, implementation-grounded slice of this draft is exactly the part that the TRVM runtime has already proven: content-addressed objects, monotone facts, separate immutable receipts, deterministic reduction, and replayable *films*. Everything else is design ahead of implementation.

**Architectural rule (normative for implementers).** WRL denotes the **Forge semantic graph**. It MUST NOT be lowered by compiling its surface syntax directly to hand-written interaction-calculus text. The path is always: WRL source/canvas → canonical semantic graph → Forge semantic IR → TRVM facts/films/reductions. A future *Forge Semantic IR v1* (a separate, gated deliverable) is the only sanctioned lowering target.

### Three stability tiers

Every section is classified into one of three tiers. The tiers say **how settled the meaning is**, not how important it is.

- **Core** — meaning *families* that TRVM/Forge has grounded and that the frozen **WRL Core 0.1** extract commits to (families only, not every detailed rule). Stable enough to build against.
- **Experimental** — coherent, designed, and intended, but **not yet grounded** in a running implementation. Rules here may change as they meet the runtime.
- **Proposed** — speculative or explicitly deferred surface (distributed settlement, mobile-code metaprogramming, scale/build tooling). Present for completeness; expect substantial change or removal.

### Section classification

| Tier | Sections |
|---|---|
| **Core** | §1 Introduction · §2 Design principles · §3 Notation at a glance · §4 Lexical structure · §5 Delimiters and scope · §6 Containers (shape-as-kind) · §7 Identity and addressing · §8 Routes · §9 Time · §18 Memory model · §19 Runtime entities · §20 Execution model (deterministic reactive floor + films) · §22 Merging replicated facts (union law only) · §23 Verification and sealing · §39 Canonicalization and content identity · §42 Grammar · §46 Conformance |
| **Experimental** | Part II — Expression Notation (§10–17) · §21 Effects, capabilities, entropy · §24 Supervision, faults, error ladder · §25 Mailboxes, streams, backpressure · §26 Actor behavior blocks · §27 Evolution: migration & compatibility · §20.7 Podium / ranking · §37 Testing & conformance monitoring · §40 Static checks · §41 Execution profiles |
| **Proposed** | Part IV — Metaprogramming (§28–34: fragments, stencils, derives, sealed compiler tools, reflection) · §35 Modules & builds · §36 Build films · §38 Foreign functions · §22 distributed/trust settlement (Stage-Three, Byzantine modes) · §45 Reserved & implementation-defined |

Note: a few sections straddle tiers. §22 fact-union is **Core**; its distributed trust/settlement policy is **Proposed**. §20 deterministic reactive floor + film emission is **Core**; the podium/ranking ceiling (§20.7) is **Experimental**. §44 Exclusions applies across all tiers (permanent negative space).

### The frozen extract

The **families** committed by this draft are frozen separately in **`WRL_CORE_0.1.md`** (the Phase 1 extract). When in conflict, `WRL_CORE_0.1.md` — not this draft — is authoritative for what is *actually settled*. This draft remains the full design rationale and forward map.

---

# Part I — Foundations

## 1. Introduction

WallRiderLang — WRL for short — is a programming language for actor systems, graph rewriting, simulation, generative worlds, distributed execution, and machine-assisted fabrication. A program is a graph of durable identities connected by textured routes and separated by boundaries. The name is literal: programs are made of *riders* — identities in motion along routes — and *walls* — the boundaries that gate, commit, and seal what they do. The surface reads like a route map or a piece of graffiti, but the meaning is a precise, canonicalizable graph.

The governing idea is that the *appearance* of the code reveals *runtime facts* that are usually hidden: where identity lives, what state may change, which transitions are deterministic, which messages are asynchronous, where authority or effects cross a boundary, what can be copied and moved as code, and what has been verified and sealed.

### 1.1 Two notations, one language

WRL has exactly two notations and one language:

- The **process notation** — routes, boundaries, containers, textures — describes the *architecture of computation*: identity, state, topology, movement, time, authority, quotation, ranking.
- The **expression notation** — values, functions, types, pattern matching — describes *computation itself*: arithmetic, data manipulation, local logic.

Both notations share one grammar, one type system, one checker, and one canonical form. The expression notation can be evaluated at three moments — expansion time, verification time, and run time (§28) — but it is the same language at each; there is no separate macro or template dialect.

### 1.2 The architectural creed

> **Functions calculate. Actors persist. Routes communicate. Walls authorize. Periods order. Fragments carry code. Stencils construct graphs. Derives transform typed graphs. Films prove what occurred. Hashes identify what was built.**

Every construct in this document is one of these ten things.

### 1.3 The four reading laws

Everything in the notation follows four laws. If in doubt, apply them.

> **Shape says what a thing is.** Brackets identify the *kind* of computational object.
>
> **Line texture says how it moves.** The style of a route identifies the *operational guarantee* of a transition.
>
> **The colon introduces; the slash bounds.** Colons bring things into being; slashes mark places where propagation changes. Both families cap at three strokes, ordered by permanence: transient, committed, sealed.
>
> **Marks for architecture, words for computation.** The process notation owns punctuation; the expression notation defaults to words (§10.1).

### 1.4 Conceptual lineage (for orientation)

The execution model is synchronous-reactive and deterministic in the manner of the reactor/logical-time family; structure separates *placing* (containment) from *linking* (communication) in the manner of bigraphs; identity is content-addressed in the manner of Unison; compartments and membranes echo membrane computing; authority follows object-capability discipline (no ambient authority); replicated knowledge merges as CRDT join-semilattices; metaprogramming follows the hermetic compile-time-evaluation discipline and the typed-staging guarantee that generated code is well-typed by construction; and the runtime is a deterministic-simulation substrate in the tradition of simulation-tested distributed databases. An agent fluent in those models can map WRL onto them quickly. No familiarity with them is required to use this document.

### 1.5 Relationship to the surrounding ecosystem

WRL is a standalone language and can be implemented and reasoned about entirely on its own. It is also designed to sit above two systems it is commonly paired with:

- **Forge** — an authoring and world environment that can present one WRL program through several coordinated views (a spatial canvas, canonical text, a runtime timeline, or a playable world).
- **TRVM** — a deterministic graph runtime providing content-addressed objects, monotonic facts, deterministic reduction, and replayable event logs called *films*.

The mapping is: WRL source and canvas → canonical graph → Forge authoring → TRVM facts, films, reductions, and actors → native device runtimes.

---

## 2. Design principles

These are the invariants the language holds to. They are normative: a feature that violates one is not part of the language.

1. **Visual law before visual novelty.** Every symbol family expresses one durable computational distinction. A mark that is clever but does not improve reading, composition, checking, or execution is not admitted.
2. **Structured source, not pixel art.** The surface may be spatial, but the canonical artifact is a graph. Layout, line length, paint, and typography are presentation metadata; they never affect meaning.
3. **Deterministic floor, expressive ceiling.** The runtime core is deterministic and replayable. Ranking, generation, inference, and other heuristic behavior are explicit scored or effectful routes layered above that floor.
4. **Code can move.** A quoted fragment is a first-class value that can be copied, sent, stored, signed, stamped, and pasted. A stencil produces such fragments from parameters. Mobility is decided by the type system, not by ceremony (§12.4).
5. **Boundaries are first-class.** A slash is not punctuation after the fact. It is a membrane, a capability gate, a commit point, or a sealed-artifact boundary, each with a defined runtime effect.
6. **Texture conveys causality.** A reader can see, without a legend, whether a transition is local, asynchronous, delayed, verified, or a fault.
7. **Canonicalization precedes identity.** Comments, spacing, alignment, decorative line length, and presentation color cannot affect the semantic hash. Meaning is normalized before content addressing.
8. **Failure is visible.** Crashes, rejected proofs, unavailable capabilities, and quarantined effects appear as explicit graph events, never as silent exceptions.
9. **No ambient authority — at run time and at expansion time.** Effects cross named walls; a copied fragment inherits no capability it did not explicitly capture; a metaprogram gains nothing from the machine that runs it.
10. **Marks for architecture, words for computation.** The process alphabet owns punctuation globally. The expression notation may claim a punctuation token only if it collides with no process glyph, in both lexer and eye (§10.1).
11. **Expansion is hermetic and host-blind.** Compile-time evaluation performs no I/O and cannot observe the build machine. The same source produces the same canonical bytes on every host.
12. **Generated structure remains visible.** Every expanded or derived node carries provenance; tooling can always show the collapsed invocation, the expanded graph, and which invocation produced which node.

---

## 3. Notation at a glance

A single actor, fully formed, is legible on sight:

```
[rider:a](
  energy=74,
  speed=42,
  role=leader
){
  road,
  team,
  radio
}
```

- `[rider:a]` — a durable identity (this box *is* the actor).
- `(…)` — its current state cell.
- `{…}` — its permitted ports and capabilities.

A master table of every symbol family follows. Each is defined normatively in its own section.

| Family | Forms | Meaning | Section |
|---|---|---|---|
| Containers | `[x]` `(x)` `{x}` | identity / state / wiring | 6 |
| Staging | `: x` | introduce one form into the configuration | 5 |
| Fragment | `:: x //` | quote a movable graph fragment | 30 |
| Stencil | `::: x ///` | define a reusable parameterized producer | 31 |
| Boundaries | `/x` `//x` `///x` | gate / commit / seal | 23, §20.6 |
| Podium | `oN.` | ranked top-N result with provenance | §20.7 |
| Routes | `--` `~~` `==` `!!` (+ sugar) | transition textures | 8 |
| Identity | `#` `@` `?` `*` | hash / address / variable / wildcard | 7 |
| Composition | `+` `&` `\|` `\|\|` | union / composition / branch / parallel | 8 |
| Control glyphs | `_` `^` | rest / supervision | 24 |
| Time | `.` `.n` `...` | tick / repeat / continue | 9 |
| Expression notation | words, `+ - = < >` etc. | values, functions, types | Part II |

---

## 4. Lexical structure

A source file is UTF-8. Executable punctuation is ASCII. Whitespace and line length are presentation, except that indentation may disambiguate a multi-line continuation; a structured editor may write the graph directly and serialize canonical text.

**Comments.** Because `//` and `///` bound scopes, slash comments do not exist. Non-semantic notes use a semicolon:

```
; this line is commentary
[rider] --pedal--> [road]   ; inline note
```

**Annotations.** Structured, tagged metadata uses a bracketed hash form:

```
#[author="ana", intent="demo", color="spray-orange"]
```

Annotations are removed before semantic hashing unless explicitly declared executable (e.g. `#[det=bitexact]`, `#[meta_fuel=10_000]`).

**Literals.** Ordinary values are written plainly:

```
42        3.14        true        false
"rider a"        #8f21ac        [1, 2, 3]        (speed=42, energy=80)
```

Parentheses form a state/value cell when attached to an identity or used in a state position; in expression position they group. The grammar (§42), not visual guesswork, resolves which.

**Reserved symbols.** The following are reserved and carry no defined meaning; a conforming implementation rejects them in executable position:

```
%   $   ~ (as a unary operator)   ` (backtick)
< > (as standalone delimiters — attached generics are legal, §14)
```

A small coherent alphabet is preferred to a large one.

---

## 5. Delimiters and scope

Colons and slashes are two independent families. They coincide as open/close only at the two levels that require an explicit end.

### 5.1 The colon is a staging prefix

`:` introduces exactly one form into the initial configuration. It opens no region and requires no closer, because the form it stages is self-delimiting through its own brackets:

```
: [rider:a](energy=100, watts=330){road, radio, team}
```

Multiple staged forms are multiple `:` lines. `:` places a form; it does not imply the form has already run.

### 5.2 Fragments and stencils are the only paired scopes

Two constructs need an explicit end, and they borrow a doubled or tripled slash as the closer:

| Open | Close | Construct |
|---|---|---|
| `::` | `//` | quoted graph fragment (§30) |
| `:::` | `///` | stencil / reusable producer (§31) |

### 5.3 A lone slash is a boundary node, never a closer

`/name`, `//name`, and `///name` are *first-class boundary nodes* — places in the graph (§23, §20.6), not punctuation. `/net`, `//finish`, and `///world17` are things you route to and from.

The disambiguation rule is exactly one sentence:

> A `//` or `///` **closes** the nearest open `::` or `:::` at the current depth if one is open; otherwise it is a **boundary node reference**. A single `/` is *always* a boundary node.

This is why the slash is free to mean *membrane*: it is never asked to also mean *the end of a staged form*.

### 5.4 Depth is categorical and capped at three

The three levels form a closed set ordered by **permanence**. There is no four-stroke form; `::::` and `////` are reserved and undefined.

| Strokes | Colon (introduce) | Slash (bound) | Permanence |
|---|---|---|---|
| one | stage a form | local gate | transient / most local |
| two | quote a fragment | commit a fragment | committed, movable |
| three | seal a stencil | seal an artifact | sealed, content-addressed |

---

## 6. Containers and the shape-as-kind system

Container shape is a kind marker. The parser reads the shape to know what sort of object it is holding.

| Form | Kind |
|---|---|
| `[x]` | durable identity — actor, region, mailbox, named artifact |
| `(x)` | state — value, payload, cell, mutable contents |
| `{x}` | wiring — topology, capability set, ports, rules, relationships |

`{…}` describes *permitted or static* structure (what routes are legal, what capabilities are held), distinct from `(…)`, which is *current mutable* state. A topology block can constrain which routes are legal and provide default ports:

```
{
  [coach] ~~radio~~> [rider:*]
  [rider:*] ~~draft~~> [rider:next]
  [timing] ==result==> //finish
}
```

---

## 7. Identity and addressing

| Symbol | Question it answers | Meaning | Example |
|---|---|---|---|
| `#` | *what is it?* | canonical identity / content hash / tag | `[film:#8f21ac]` |
| `@` | *where / which one?* | address, placement, stamp (of a stencil or derive) | `@rider(a)` |
| `?` | *unknown* | pattern variable introduced by matching | `(energy=?e)` |
| `*` | *which set?* | wildcard match, or replication by position | `[rider:*]`, `*@seed` |

Position distinguishes the two senses of `*`:

```
[rider:*]        wildcard — every matching identity
*@rider(300)     replication — spawn requests
```

Human aliases are words; executable identity is a hash. `#name` names a thing; `@name` points at one or stamps one.

---

## 8. Routes

A route is a directed edge whose *texture* carries an operational guarantee. Decorative line length is not stored; `[a] --go--> [b]` and `[a] ----------go----------> [b]` are the same edge.

### 8.1 Core textures

Four textures are semantically irreducible. The reduction relation (§20) is defined over exactly these.

| Texture | Class | Guarantee |
|---|---|---|
| `--x-->` | solid | deterministic local transition; settles within the period |
| `~~x~~>` | async | asynchronous message; appended to a mailbox, observable next period |
| `==x==>` | verified | evidence-backed / committed transition under a named policy |
| `!!x!!>` | fault | crash, cancellation, rejection, or interrupt; engages supervision |

### 8.2 Derived textures (sugar)

The following read naturally and are retained in the surface, but they canonicalize to a core texture plus an attribute. A conforming parser rewrites them during canonicalization.

| Surface | Canonicalizes to |
|---|---|
| `..x..>` (delayed) | `--x-->` with a schedule attribute (§9) |
| `??x??>` (query) | `--x-->` labelled as an ask, returning a binding |
| `<~x~>` (merge) | `==x==>` with `policy=crdt` (§22) |
| `<--x-->` (rendezvous) | `~~x~~>` plus an explicit continuation and timeout |

### 8.3 Labels, payloads, guards

A route body is a label with optional arguments: `--pedal(cost=8)-->`. A guard filters eligibility:

```
[rider](energy=?e)
  --when(?e > 30)-->
[road]
```

Guard expressions use the expression notation (§10): comparisons `=` `<` `>` `<=` `>=`, connectives `and` `or` `not`.

### 8.4 Branches and parallel lanes

A guarded branch selects one lane. Guards are evaluated in canonical order; overlapping deterministic guards are a static error (§40) unless the branch is explicitly `scored`.

```
[rider](energy=?e) -->
  | when ?e > 30  --attack--> [road]
  | otherwise     --hold----> _
```

Parallel lanes run concurrently; the continuation runs after all required lanes commit, or per a named join policy.

```
|| {
  [camera] --record--> [archive]
  [timing] --measure--> [results]
}
```

### 8.5 Composition operators

| Operator | Meaning |
|---|---|
| `+` | monotonic union / accumulation (§22) |
| `&` | composition that retains named parts |
| `\|` | one alternative lane or guarded branch |
| `\|\|` | a parallel lane group |

```
[layout] & [report:roads] & [report:budget] ==verified(policy=world.v1)==> [film:#w]
```

`+` and `&` are process-notation operators over graph values. Arithmetic addition occurs only inside expression position (§15); boolean conjunction is the word `and`.

---

## 9. Time

Logical time is state and is replayable. Wall-clock time is an effect (§21).

| Form | Meaning |
|---|---|
| `.` | one logical period (tick) when used as an operator |
| `.n` | repeat / advance n logical periods |
| `.....` | presentation sugar for `.5` (repeat-suffix position only) |
| `...` | continue until an enclosing stop, budget, or boundary decides |
| `..after(k)..>` | schedule an event k periods ahead |

A closed fragment may be repeated a fixed number of periods; `.....` is the graffiti-friendly form and `.5` is the canonical form of the same count:

```
(
  [rider:*] --lap--> [course]
).5
```

An unbounded `...` is rejected in restricted profiles unless a fuel or boundary policy is attached.

**The dot family means logical time and nothing else.** Four things that other languages conflate are distinct here, and only the first uses periods:

| Need | Construct |
|---|---|
| advance logical time / keep a process alive across periods | `.n`, `...`, quiescence and wake (§24.2) |
| iterate over data | `for x in xs { … }`, `map`, `fold` (§16) |
| repeat a pure computation | an ordinary loop or recursion in expression notation |
| schedule a future event | `..after(k)..>` |

**Superdense tags.** Internally, every event carries a tag `(t, m)`: a logical period `t` and a microstep `m` within it. Same-period events are ordered by microstep. This is defined in §20.2.

---

# Part II — The Expression Notation

## 10. Overview and the punctuation rule

The expression notation is where ordinary computation lives: values, records, arithmetic, functions, pattern matching, collections. It appears inside state cells, route arguments, guards, behavior blocks, derives, and tests. It is deliberately conventional — the visual symbols describe the architecture of computation, not arithmetic.

### 10.1 The punctuation rule

> **The process alphabet owns punctuation globally. The expression notation defaults to words, and may claim a punctuation token only after passing a collision audit against every process glyph — in both lexer and eye.**

The sanctioned expression tokens, and the collisions they were audited against:

| Purpose | Token | Audit note |
|---|---|---|
| arithmetic | `+` `-` | `+` is graph-union only in process position; context-split by grammar |
| multiplication / division / remainder | `mul` `div` `rem` | words — `*` is wildcard/replication, `/` is a boundary |
| comparison | `=` `<` `>` `<=` `>=` | `=` is equality in guard/pattern position, field assignment in cells; never `==` (verified route) or `!=` (`!` is the fault family) |
| logic | `and` `or` `not` | never `&&` (`&` is composition), `\|\|` (parallel lanes), `!` (faults) |
| error propagation | `try expr` | a word — postfix `?` would collide with `?x` pattern variables |
| paths / field access | `.` | `Command.attack`, `race.timing`, `state.status` — never `::` (fragment opener) |
| match arms | `=>` | permitted; the formatter must never let an arm line resemble a `==>` route |
| function return type | `->` | permitted; one dash vs. two is the learnable distinction from `-->` |
| generics | `<T>` attached to an identifier | `Mailbox<T>`, `Fixed<16>`; standalone `<` `>` delimiters remain reserved |
| binding | `let` `var` `<-` | `<-` binds a pattern to a result (`[winner] <- o3.`) |
| record update | `with` | `rider with { energy=e }` |
| closures | `fn(x) expr` | never `\|x\|` (lanes) |

Nothing else. Operator overloading of punctuation does not exist (§44).

## 11. Values and data types

The language has algebraic data types: records, variants, tuples, and recursive data. There is no `null`.

```
type Rider = {
  name: Name,
  watts: Watts,
  energy: Energy,
  status: RiderStatus
}

enum RiderStatus {
  staged,
  riding(lap: Int32),
  dropped(reason: DropReason),
  finished(time: Period)
}

enum Option<T> { some(T), none }
enum Result<T, E> { ok(T), err(E) }
```

These are the foundation of messages, actor state, boundary responses, films, and evidence. Absence is `Option`; expected failure is `Result`; a genuine fault travels on `!!` (§24.3). Values are immutable; "updating" produces a new value:

```
let next = rider with { energy = rider.energy - cost }
```

## 12. Bindings, functions, and closures

### 12.1 Bindings

`let` introduces an immutable binding. `var` permits local mutation as sugar; it lowers to immutable form, and shared mutable variables are impossible by construction (§18).

```
let cost = grade_cost(course.grade)
var total = 0        ; local only; lowers to SSA
```

### 12.2 Pure functions

Actors do not replace functions. Actors are for identity, concurrency, persistence, and fault domains; pure functions are for local calculation. A function declares its effect row with `uses`; an empty row means pure.

```
fn drain(rider: Rider, cost: Energy) -> Result<Rider, Exhausted>
  uses {} {
  let remaining = rider.energy - cost
  match remaining {
    e when e >= 0 => ok(rider with { energy = e })
    _             => err(exhausted(required=cost, available=rider.energy))
  }
}
```

Pure functions have no hidden effects, are deterministic, are callable from guards and metaprograms, and never require spawning an actor.

### 12.3 Effect rows

A function that performs effects names the capabilities it uses; the checker proves the row:

```
fn download_world(id: WorldId) -> Result<Bytes, NetError>
  uses { net.send, storage.write }
```

Effect rows are the type-level face of the capability walls in §21: a call whose row is non-empty can only execute where an actor's ports grant those capabilities.

### 12.4 Closures and portability

Closures exist: `riders.filter(fn(r) r.watts > 350)`.

**Portability is decided by the type system, not by ceremony.** A closure whose effect row is empty and whose captures are all content-addressed values has a canonical graph — it *is* a fragment, and may travel as a message, be stored, or be stamped. A closure capturing a live capability or an affine resource handle is not portable, and using it where a portable value is required is a compile error naming the offending capture. The `:: … //` syntax (§30) is the *literal notation* for fragment values and the home of typed holes and explicit captures — the notation for the property, not its source. This is also how "a copied fragment inherits no ambient authority" is a theorem rather than a rule.

## 13. Pattern matching

`match` is the ordinary conditional over data, with guards:

```
match message {
  Command.attack(at=?p)            => …
  Command.recover(amount=?n) when ?n > 0 => …
  _                                => …
}
```

Graph patterns use the same binding system:

```
[rider:?id](energy=?e, status=riding(?lap))
  --when(?e < 20)-->
/feed-zone
```

**Matching is bounded and deterministic.** There is no implicit search in the ordinary language:

- **Rule patterns are anchored.** The left side of a solid rule may match its own subject actor's cell and mailbox head — tree matching, cheap by construction. Topology-wide relational patterns are legal only in derives (§32), which are offline, stratified, and budgeted, or in explicitly `scored`/search contexts on the expressive ceiling.
- Non-exhaustive matches over variants are static errors unless a `_` arm exists.

## 14. Generics and traits

### 14.1 Generics

Generics are parametric (never token-templates), with const parameters where needed:

```
type Mailbox<T>        type Port<T>        type Graph<T>
type Fragment<T>       type Result<T, E>   type Vector<T, N: Int32>
fn map<T, U>(items: List<T>, f: fn(T) -> U) -> List<U>
```

Stencil parameters and type parameters are related but distinct; a stencil may take both: `::: cache<K, V>(name, capacity: Int32) … ///`.

### 14.2 Traits

Traits are the abstraction mechanism; there is no class inheritance (§44).

```
trait Hashable {
  fn hash(self) -> Hash
}

trait Merge<T> {
  fn join(left: T, right: T) -> T
}

trait Verify<Candidate, Evidence> {
  fn verify(candidate: Candidate, evidence: Evidence)
    -> Result<Verified<Candidate>, Rejection>
}
```

Traits map directly onto runtime policies: `Merge` instances implement `<~merge~>`; `Verify` instances implement `==verified==>` checkers; boundary adapters are trait implementations.

### 14.3 Coherence is hash-pinned

Instance resolution is a **correctness** property here, not a style preference. `<~merge~>` converges *because* every replica applies the same commutative, associative, idempotent join; if two replicas resolved `Merge<FactSet<T>>` to different instances, they would diverge while each believed it had merged correctly.

Therefore: during canonicalization, every trait-method call site is resolved to a concrete instance, and **the instance's content hash is baked into the canonical bytes** (§39.1, step 7). Two replicas holding the same program hash hold the same join function, by construction. Instance selection can never vary by context, import order, or build.

## 15. Numerics and determinism classes

Numeric types are explicit and fixed-width:

```
Int8  Int16  Int32  Int64      UInt8 … UInt64
Float32  Float64                Decimal
Fixed<Q>                        Duration   Period
```

**Integer semantics are fully defined and identical on every target.** Overflow is checked by default; `wrapping_add`, `saturating_add`, and friends are explicit. Quotient truncates toward zero and remainder takes the dividend's sign, identically everywhere; `div_euclid` / `rem_euclid` variants exist. No numeric behavior may depend on build mode or platform.

**Floating point is a determinism hazard and is treated as one.** Identical executables on identical hardware reproduce float results; across hardware, compilers, or optimization settings they do not — fused multiply-add, SIMD variation, and transcendental library differences all break bit-equality. The language's answer is *determinism classes bound to execution profiles* (§41):

| Profile | Simulation-state numerics | Floats |
|---|---|---|
| `world` (lockstep console/desktop simulation) | `Fixed<Q>`, integers | forbidden in state cells; permitted on the presentation/effect side only (rendering, audio) |
| `pure` / `replay` | `Fixed<Q>`, integers; `Float64` with `#[det=bitexact]` | strict IEEE-754, no FMA, no fast-math, pinned softfloat transcendental artifact |
| effect side of any wall | anything | float results are observations; their hashes enter the film like any effect |

The corresponding static check: **a `Float` type may not appear in a state cell of a `world`-profile actor** (§40). `Duration` is a wall-clock quantity and therefore effect-side; `Period` is logical time and replayable.

## 16. Collections, strings, and symbols

The minimum standard vocabulary:

```
List<T>   Vector<T, N>   Map<K, V>   Set<T>   Bytes   String
Queue<T>  Mailbox<T>     FactSet<T>  Stream<T>
```

Every collection defines deterministic iteration order, canonical serialization, equality and hashing, and documented complexity. Nondeterministic map iteration does not exist (§44).

**`Set<T>` and `FactSet<T>` are different types on purpose.** A `Set` is a local collection. A `FactSet` is a monotonic join-semilattice (§22) — a *claim* that its merge obeys the lattice laws. Collections are never silently CRDT-mergeable; replication is opt-in by type.

Data iteration is textual and never uses periods (§9):

```
for rider in riders { … }
map(riders, score)
fold(results, initial, combine)
```

**Strings, symbols, identities, addresses** are four different things:

```
"rider a"      String — data
rider_a        identifier — a name in source
#rider-a       tag / content identity
@rider-a       address / stamp
```

Interned symbols exist as `Symbol`; the intern table is bounded per sealed scope and cannot grow without limit at runtime.

## 17. Resources and ownership

The ownership model is small and sufficient:

- values are immutable;
- actor state is singly owned (§18);
- messages are immutable;
- large binaries use shared *immutable* storage;
- external resources are **affine handles**;
- capabilities cannot be duplicated unless their type permits it.

```
resource FileHandle
resource GpuBuffer
resource Socket

fn upload(buffer: borrow GpuBuffer) -> Result<Receipt, GpuError>
fn close(socket: move Socket)
```

A resource is consumed, moved, or explicitly borrowed. There are no shared mutable pointers anywhere in the language.

---

# Part III — Process Semantics

## 18. Memory model

Different container shapes are different *kinds of memory*. An agent can read the kind of memory off the shape.

| Shape | Memory kind | Mutability / lifetime | Physical intuition |
|---|---|---|---|
| `(state)` | volatile cell | mutable by replacement; one logical step, then a new value at the same identity | working memory — what is held right now |
| `{facts}` | monotonic knowledge | grow-only; merges by lattice union; never retracts | a ledger — lines are added, never erased |
| `[archive]` | durable store | persistent addressable actor; survives restart | an archive room — walked to, looked up, outlives the session |
| `:: fragment //` | code memory | quoted graph as data; portable, signable, stampable | a stencil — a pattern carried and stamped elsewhere |
| `#hash` | sealed identity | immutable forever; content-addressed | a sealed vault whose address is its contents |

A `(state)` cell belongs to exactly one actor. Shared *knowledge* is `{facts}` (merged monotonically); shared *identity* is `[archive]` (a durable actor). There is no shared mutable cell. This single-owner discipline is what makes the execution model deterministic without a runtime conflict resolver (§20.4).

## 19. Runtime entities

An implementation needs six semantic entity types.

- **Actor** — a stable identity, a current state cell, a mailbox, a declared port/capability set, an optional supervisor, a deterministic behavior table (the solid rules whose source is this actor), and resource counters and status.
- **Value** — immutable. Updating state produces a new value at the same identity at the next logical step.
- **Edge** — source, destination, label, texture, payload expression, policy, and provenance. Decorative line length is not stored.
- **Boundary** — mediates propagation: stop, filter, authorize, commit, snapshot, rank, externalize, or seal.
- **Fragment** — quoted graph data with hygienic holes and explicitly captured identities; typed as `Fragment<T>`.
- **Stencil** — a deterministic, hygienic, resource-bounded, canonicalizable map from parameters to a fragment; typed as `Stencil<Args, Fragment<T>>`.

```
[actor:#id](state){ports}
```

## 20. Execution model

This section defines what a program *does* and why it does the same thing on every machine.

### 20.1 The configuration

A **configuration** is the runtime state at a moment in logical time:

- **Actors**, each with identity, current state cell, mailbox, port set, optional supervisor, behavior table, status (`runnable` / `quiescent`), and resource counters.
- **Scheduled events**, keyed by the logical time they are due.
- **Boundaries** and their policies.
- **Fact sets** `{facts}` — monotonic CRDT lattices.
- **The film** — an append-only event log; the replayable record.

Two invariants make the model tractable and are enforced by static checks (§40):

1. **Single-owner cells.** A `(state)` cell belongs to exactly one actor. No shared mutable cells.
2. **Disjoint deterministic guards.** Within one actor, at most one deterministic rule is enabled per state; overlapping deterministic guards are a compile error. Genuine choice must be an explicit `scored` branch.

### 20.2 Logical time is superdense

Every event carries a tag `(t, m)`: a logical period `t` and a microstep `m`. Same-period events are ordered by `m`. Wall-clock time enters only through a `/time` boundary that converts a duration into a period count, recorded as a signed fact in the film. Logical time is replayable state; wall-clock is not.

### 20.3 The period cycle (five phases)

Each period `t` runs a settle-and-commit cycle.

1. **Collect** the eligible set: solid rules whose pattern matches and guard holds; messages deliverable at `t`; scheduled events due at `t`; boundary arrivals.
2. **Order** by a total **canonical event key** = the content hash of `(source_id, rule_or_label, matched_binding, arg_hash)`. Never by worker arrival. A full binding makes key collisions impossible for genuinely distinct events.
3. **Reduce** to a fixpoint (§20.5).
4. **Commit** the settled result: new cells at the same identities; messages appended to mailboxes; facts lattice-joined; boundary outputs; spawned actors; supervision actions. This snapshot is what other actors and the next period observe.
5. **Record** the film entries needed to replay `t`: rules fired and their microstep order, bindings, messages, scheduled events, boundary crossings, effect observations (as signed hashes), and verification results.

### 20.4 Conflicts dissolve

Given the two invariants, ask what two same-period events can contend over:

| Contended thing | Destructive conflict possible? | Why |
|---|---|---|
| an actor's state cell | no | single-owner + at most one enabled deterministic rule |
| a mailbox (two senders) | no — ordering only | both are appends; ordered by canonical key |
| a fact set (two contributors) | no | lattice join is commutative, associative, idempotent |
| a spawn (colliding ids) | caught at expansion | stencil expansion allocates deterministic ids hygienically (§31.2) |

The only concurrently-written structures are **mailboxes** and **fact sets**, and both have deterministic merges. There is no destructive write-write conflict on state. The ownership discipline *buys* determinism rather than requiring a runtime resolver.

### 20.5 Within-period fixpoint

Within a period, deterministic local reduction settles to a fixpoint, like a synchronous circuit settling within a clock tick. Independent events (disjoint read/write footprints) commit at the same microstep. Dependent events (one reads another's output — a chain such as `--grind--> --brew-->`) fire at the next microstep, seeing the settled value. Enablement is re-derived after each microstep until no further local progress is possible. Committed cell writes and sent messages become observable at the *next* period.

### 20.6 Boundaries as reduction operators

A boundary mediates propagation. Each boundary is a reduction operator with a defined effect on memory.

| Boundary | Reduction effect |
|---|---|
| `/gate` | require the named capability in the crossing fragment's ports; emit an *effect-request node* rather than performing I/O |
| `//commit` | canonicalize the fragment so far, assign it a content id; it becomes immutable |
| `//finish` | a commit boundary that may also receive race or workflow arrivals |
| `///seal` | perform `//commit`, then register the artifact under a content hash (and optional name) |

A gate authorizes and externalizes; a commit freezes; a seal freezes and content-addresses. The finish line is literal: crossing `//finish` *is* the canonicalize-and-record reduction, which is why it can feed a podium directly.

### 20.7 Podium — ranked selection with provenance

`oN.` consumes an eligible result set that has crossed a boundary this run and reduces to a provenance-carrying object with N named places:

```
Podium {
  places: [r; N],        ; missing places are explicit _
  ranking_policy,
  evidence,
  source_boundary
}
```

Ranking must name a stable tie-breaker — arrival order and scheduling are never acceptable implicit tie-breakers. The podium can rank anything, not only race results. `o0.` is accepted as sugar for `o3.` where the three-place podium reading is intended.

```
//finish ==rank(by=time, tie=#id)==> o3.
[winner, second, third] <- o3.
```

### 20.8 Messages

A `~~msg~~>` in period `t` appends an immutable fact:

```
{ msg_id, sender, receiver, payload_hash,
  send_tag=(t,m), delivery_policy, provenance }
```

Delivery is a separate event. Under the default policy a message sent at `(t, m)` becomes deliverable no earlier than `(t+1, 0)`; an actor cannot observe its own send within the same period, which keeps periods well-founded and forbids same-period causal loops. Exactly-once processing is not assumed; deduplication keys and acknowledgements are explicit.

### 20.9 Scheduled events

`..after(periods=k)..>` at period `t` creates an event due at `t+k`. `..after(5s)..>` desugars through a `/time` wall that converts the duration into a period count; the observed conversion is a signed fact, so replay uses the recorded count, not a live clock.

### 20.10 Determinism

**Property.** Given the same initial configuration and the same sequence of external observations (the signed facts crossing effect walls), the committed film is byte-identical across any hardware scheduling.

Phases 1–2 depend only on configuration content; phase 3's independent set commits order-independently (disjoint footprints commute) and its dependent cascade is serialized by microstep as a pure function of content; §20.4 shows no destructive state conflict, only commutative appends and joins; phases 4–5 are deterministic functions of phase 3. The only entry point for nondeterminism is effect-wall observations, which are captured in the film — so replay is exact. Consequently, "the same sealed film runs identically on desktop and console" is a testable property, not a hope — provided the numeric rules of §15 are respected.

### 20.11 Termination and quiescence

A graph is locally **quiescent** when no solid transition is enabled, no message is deliverable this period, no scheduled event is due, no actor is runnable, and all required boundary commits are complete. A distributed run is **complete** only under an explicit termination detector or a sealed finite-horizon film. Importing state that marks actors runnable invalidates a prior quiescence conclusion; restored work must be rescheduled before termination is declared.

## 21. Effects, capabilities, and entropy

All non-deterministic or external action crosses a named wall. No effect happens invisibly.

```
[request] --> /net
[frame]   --> /gpu
[sound]   --> /audio
[file]    --> /storage
```

An adapter returns a signed observation, which is what enters the film so a replay reproduces the run without repeating the call:

```
/net ==observed(response=#hash)==> [requester]
```

Capabilities live at boundaries and ports and are typed as effect rows (§12.3). A copied fragment inherits no ambient authority; captured capabilities must be named:

```
[actor]{net.send}
[request] --> /net requires net.send
```

**Randomness is an effect.** All randomness — simulation noise, scored-branch exploration seeds, scheduler-fuzzing seeds — enters through `/entropy` as seeded streams whose seeds are recorded as facts. Any run, including a randomized test exploration, therefore replays exactly from its film.

Effect walls are the *only* source of nondeterminism in the language. Everything else is a pure function of configuration content.

## 22. Merging replicated facts

Monotonic knowledge merges as a CRDT join-semilattice. The merge is commutative, associative, and idempotent; convergence follows from these laws.

```
[node:a] <~merge(facts)~> [node:b]
[node:a]{facts} + [node:b]{facts} --> [facts:joined]
```

`<~merge~>` canonicalizes both fact sets, unions them, and deterministically reduces. `+` denotes monotonic union or accumulation, not arithmetic addition. The join function is a `Merge<T>` instance whose content hash is pinned into the program's canonical identity (§14.3) — so every replica of a given program hash provably applies the same join. Semantic convergence is a separate concern from work efficiency; an implementation reports duplicate work, verifier work, and divergence cost independently.

## 23. Verification and sealing

A verified route requires evidence satisfying a named policy. The runtime does not infer what "verified" means; verification is a protocol with an explicit checker identity (a `Verify` instance, §14.2), a policy version, inputs, a result, and an evidence hash.

```
[candidate]
  ==verified(by=proof, policy=forge.v1)==>
[film:#hash]
```

A failed verification travels on an explicit rejection route to a quarantine boundary:

```
[candidate] !!reject(reason=?r)!!> /quarantine
```

Sealing (`///`) content-addresses the result, making it a reusable, immutable artifact.

## 24. Supervision, faults, and the error ladder

### 24.1 Supervision

The caret denotes upward supervision or promotion:

```
[worker:a] ^ [supervisor:pool]
```

A supervisor deterministically chooses a policy in response to a fault:

```
[supervisor:pool](policy=restart_one)
  --on(crash(worker=?w))-->
@worker(id=?w, restored_from=last_checkpoint)
```

### 24.2 Rest and wake

The underscore is a parked or quiescent actor state — observable, and useful for defining termination, snapshot safety, and scheduler economics:

```
[worker:a] --> _
[queue] ~~job(?j)~~> [worker:a] _--> active(job=?j)
```

### 24.3 The error ladder

Three levels, kept distinct, with the distinction statically checked:

| Level | Meaning | Form |
|---|---|---|
| normal absence / alternative | not an error at all | `Option<T>` |
| expected failure | an anticipated bad outcome; a value | `Result<T, E>` — e.g. `err(file_not_found)` |
| fault | corrupted invariant, crashed adapter, genuine breakage | `!!crash(reason)!!>` — engages supervision |

A missing file is `err(file_not_found)`. A corrupted driver is `[storage] !!crash(reason=corrupt_driver)!!> [supervisor]`. A path that is a normal outcome must not silently become a fault; `!!` is reserved for faults, and the checker rejects the promotion (§40).

## 25. Mailboxes, streams, and backpressure

**Mailboxes are bounded by default.** An unbounded mailbox is rejected unless an explicit policy says otherwise:

```
Mailbox<Job, capacity=1024, overflow=reject>
```

Overflow policies: `reject` (sender receives a normal `Result`-level refusal), `shed_oldest`, `shed_newest`, `backpressure` (participate in demand signaling). Shedding and refusal are recorded as facts.

**Backpressure is explicit demand signaling.** Producers send only what consumers have demanded:

```
[consumer] ~~demand(32)~~> [producer]
[producer] ~~items(batch)~~> [consumer]
```

The stream vocabulary: `Stream<T>`, `Subscription<T>`, `CancelToken`, `Demand`. Cancellation is a normal message, observable in the film; a canceled producer winds down through ordinary routes, not through faults.

## 26. Actor behavior blocks

Routes are excellent for diagrams; complex actors also need an organized textual home. A behavior block declares an actor's state shape, ports, and handlers in one place:

```
actor rider(name: Name, watts: Watts) {
  state (name=name, watts=watts, energy=100, status=staged)

  ports {
    radio: Mailbox<Command, capacity=64, overflow=reject>,
    road: Port<RideEvent>
  }

  on ~~Command.attack(at=?t)~~> {
    [self] --set(status=attacking(?t))--> (state)
  }

  on --tick--> when state.status = riding(?lap) {
    (state) <- try drain(state, 8)
  }

  on !!crash(?reason)!!> {
    [self] !!report(?reason)!!> [supervisor]
  }
}
```

**A behavior block is a projection, not a second semantics.** It canonicalizes to exactly the same behavior table — and therefore the same content hash — as the equivalent drawn routes. This is a conformance requirement (§46): for every construct with both a drawn and a textual form, the two forms produce identical canonical bytes. The language has two surfaces and one meaning, permanently.

## 27. Evolution: state migration and message compatibility

### 27.1 Live-state migration

Content-addressed modules (§35) evolve *code*: a new implementation is a new hash, and names re-point. But a persistent actor in the `world` profile holds state typed by the old version, and re-pointing a name transforms nothing. Live state evolves through an explicit, verified migration:

```
(state: Rider@#a91) ==migrate(policy=rider.upgrade.v1v2, by=#m7)==> (state: Rider@#b12)
```

A migration is a verified route: evidence-carrying, recorded in the film, orchestrated by supervisors (drain to `_`, migrate, wake), and replayable. A world upgrade is a sequence of migrations, not an improvisation.

### 27.2 Message compatibility

Message types are content-addressed like everything else. A mailbox accepts the message hashes its port type declares; an unrecognized hash is a **normal outcome** (an `unknown` arm at Result level), never a fault — leaving room for explicit adapter routes between versions:

```
on ~~unknown(#msg)~~> {
  [self] --forward(#msg)--> /adapter.v1v2
}
```

---

# Part IV — Metaprogramming

Metaprogramming is a defining capability of the language, not an accessory — and it is *not* textual substitution. WRL is homoiconic over its **canonical graph**, not its surface text: a metaprogram inspects and produces typed graph nodes and can never distinguish `--go-->` from `----go---->`, because those are the same edge. Raw token arrays are not exposed.

## 28. Phases

The expression notation evaluates at three moments. It is the same language at each; the phase determines only what exists to be touched.

| Phase | What runs | Capabilities available |
|---|---|---|
| **expansion time** | stencil bodies; derives over `Graph<T>` | pure only; no walls exist yet; fuel-bounded; host-blind |
| **verification time** | `Verify` policy checkers behind `==verified==>` | the checker's declared capabilities only |
| **run time** | guards, cell updates, handlers, ordinary computation | whatever the actor's ports grant |

The build pipeline (§39.1) fixes when expansion happens: stencils expand, then derives evaluate to fixpoint, before canonicalization and hashing — and long before any reduction runs. Metaprograms cannot modify sealed artifacts; they produce new graphs, and therefore new hashes.

## 29. The six laws of metaprogramming

1. **Hygiene by default.** Identities minted by an expansion never collide with identities at the expansion site. `@worker_pool(a)` and `@worker_pool(b)` produce distinct internal queues, clocks, and supervisors unless a capture is explicitly shared (`capture [shared:clock]`).
2. **Phase separation.** Every metaprogram knows which phase it runs in; expansion-time code cannot reach forward into run time, and sealed artifacts cannot be reached backward.
3. **No ambient authority.** A metaprogram gains no network, filesystem, model, clock, or package access from the compiler that runs it. Pure by default; anything else is a sealed tool behind `/compiler` (§33).
4. **Resource-bounded expansion.** Stencil recursion must be structurally decreasing; general expansion carries explicit fuel (`#[meta_fuel=10_000, max_nodes=50_000]`). A build that exhausts fuel **fails**; it never silently emits a partially expanded program.
5. **Generated structure remains visible.** Tooling always offers: the collapsed invocation, the expanded graph, per-node provenance, the canonical bytes actually hashed, and diffs between expansions. Invisible macro magic does not exist.
6. **Expansion is hermetic and host-blind.** Expansion-time code has no I/O facilities at all and cannot observe the build machine — no host paths, clocks, endianness, or environment. Consequently expansion is reproducible and cacheable everywhere (§35.2).

## 30. Fragments

`::` opens a quoted graph fragment; `//` closes it. A fragment is a first-class value of type `Fragment<T>` — data until stamped or explicitly executed. It supports typed holes, explicit captures, hygienic local identities, copying, transport as a message, signing, storage, inspection, and canonical hashing.

```
:: breakaway(leader=?l, mate=?m)
  [rider:?l] ~~signal~~> [rider:?m]
  [rider:?l] --accelerate--> [road]
//
```

Free variables are illegal unless declared as holes; captured identities must be named:

```
:: with_clock(capture [shared:clock], hole ?target)
  [shared:clock] ~~tick~~> ?target
//
```

Copying a fragment mints fresh local identities unless an identity is explicitly marked shared. Because a fragment is a value, it travels as a message payload — code as a message:

```
[coach] --plan(::breakaway//)--> [team]
```

A fragment does not run merely because it exists. It must be stamped, executed, or crossed through an appropriate boundary.

## 31. Stencils

### 31.1 Stencils are the ordinary metaprogramming mechanism

`:::` opens a typed, hygienic graph constructor; `///` seals it. Most things that are classes, component definitions, declarative macros, annotations, or infrastructure templates elsewhere are stencils here.

```
::: rider(name: Name, watts: Watts)
  : [rider:#name](
      watts=watts,
      energy=100,
      status=staged
    ){
      road: Port<RideEvent>,
      radio: Mailbox<Command, capacity=64, overflow=reject>
    }
///
```

Stamping instantiates: `: @rider(a, 330)`. Idiomatic stencils scale from one actor to whole architectures: `@supervised_pool(workers=8)`, `@replicated_archive(nodes=3)`, `@forge_pipeline(policy=world.v1)`.

### 31.2 Identity derivation

Hygiene demands fresh identities per site; incremental builds and stable diffs demand the *same* identities on every rebuild. Both hold via one normative formula:

```
#child = H( stencil#, canonical(args), path-within-expansion )
```

Same stencil, same arguments, same position ⇒ the same identity on every rebuild. Different site or arguments ⇒ a different identity. Colliding identities are caught at expansion, never at run time.

### 31.3 Expansion pipeline

Stamping performs, deterministically: normalize arguments → allocate derived identities by §31.2 → substitute parameters → alpha-rename locals → validate capabilities and budget → canonicalize → attach provenance.

## 32. Derives

Some transformations are inconvenient as stencils — cross-cutting rules like "every faultable actor gets a supervisor." These are **derives**: expression-notation functions over typed graphs, evaluated at expansion time.

```
derive supervise_faulting(g: Graph<Actor>) -> Graph<Supervision> {
  for actor in g.actors
  where actor.can_fault and actor.supervisor = none
  emit actor ^ [supervisor:#actor.id]
}
```

Invocation stamps the derive over a fragment, like a stencil: `@supervise_faulting(::workers//)`.

Three normative restrictions give derives their guarantees:

1. **Derives are intrinsically typed.** A `derive f(g: Graph<A>) -> Graph<B>` is checked once at its definition; the type system guarantees every output is a well-formed `Graph<B>`, in the manner of typed staged programming, where a well-typed generator can only generate well-typed code. Derive output therefore needs no re-checking, and the build pipeline never loops.
2. **Derives are stratified and monotonic.** A derive may read, filter, and `emit`; it may not delete or mutate emitted structure; negation only across strata. This yields **termination** (stratified evaluation reaches a fixpoint), **confluence** (monotonic rules commute, so derive order cannot change the result — the same law that makes fact merges safe), and **incrementality** (monotonic rules recompute efficiently under the memo table of §35.2).
3. **Derives receive semantics, not spelling.** A derive sees typed canonical nodes; it cannot observe formatting, layout, comments, or anything else that canonicalization removes.

Anything genuinely non-monotonic — deletion, rewriting, arbitrary recursion — belongs to sealed tools (§33). That is the principled boundary between the two levels.

## 33. Sealed tools behind /compiler

Parsers, schema generators, GPU layout generators, binding generators, asset importers — procedural power that cannot live in the stratified system — run as **sealed tools** behind an explicit compiler capability wall:

```
[schema:#game] --> /compiler
/compiler ==generated(tool=#generator-hash)==> [bindings:#hash]
```

A sealed tool requires: a pinned tool hash; explicit input hashes; declared capabilities; CPU and memory budgets; deterministic output where possible; recorded provenance; and a sealed generated artifact. Because tools are content-addressed, capability-declared, and budgeted, they can be published, signed, and verified with the same `==verified==>` machinery as everything else — compiler extensibility without compiler trust. Every tool invocation appears in the build film (§36).

## 34. Reflection

Compile-time reflection over canonical structure is rich and free:

```
graph.actors      graph.routes       graph.boundaries
type.fields       fragment.holes     fragment.capabilities
```

Runtime reflection is capability-controlled: a mirror over an actor is a capability (`{reflect: Capability<Mirror<Pool>>}`) that must be granted like any other port. Unrestricted runtime reflection over private actor state does not exist.

---

# Part V — Programs at Scale

## 35. Modules, builds, and the no-build property

### 35.1 Content-addressed modules

```
module race.timing@#a184

export { Time, FinishResult, rank_finish }

import trvm.facts@#91bc as facts
import forge.world@#33ae as world
```

Human-readable names and versions are metadata that point to immutable hashes:

```
race.timing@1.4 -> #a184
```

A locked build stores the hashes, not only the human versions. Upgrading never mutates a sealed artifact; it produces a *new* artifact with a *new* hash, and names re-point. Because downstream references are to hashes, nothing silently changes underneath a consumer; a consumer opts into a new version by re-pointing a name. Live actor state evolves separately, by migration (§27.1).

### 35.2 The no-build property

**Property.** Given pure, host-blind, fuel-bounded expansion (Laws 3, 4, 6) over content-addressed inputs, build caching by

```
memo[ (transform#, input#) ] = output#
```

is sound with **no invalidation logic**: a hash either matches or it does not. Incremental compilation, distributed build caches, and perfect reuse across machines follow immediately. The hard problem of incremental build systems — knowing when a cached result is still valid — does not exist here, because validity *is* hash equality.

## 36. Build films

The build pipeline (§39.1) is itself a deterministic process with effects only at declared walls — so it is recorded as one. Every build emits a **build film**: which stencils expanded with which arguments, which derives fired, which trait instances were resolved and pinned, which sealed tools ran against which input hashes, and what was hashed.

Consequences: `wrl replay build.film` reproduces any build bit-for-bit; provenance views (§29, Law 5) are film queries; and "why does this node exist?" has the same kind of answer at compile time as at run time. One mechanism, both worlds.

## 37. Testing and conformance monitoring

### 37.1 Tests are first-class graph specifications

```
test "formatting does not affect identity" {
  hash(program_a) = hash(program_b)
}

property "fact join is commutative" {
  for all a, b: join(a, b) = join(b, a)
}

film_test "worker restart" {
  run scenario
  restore checkpoint
  expect same observables
}
```

### 37.2 The language is simulation-native

Every prerequisite of deterministic simulation testing — a deterministic scheduler, virtualized time, randomness funneled through recorded seeds, effects behind mockable walls — is a construction property of the language, not a retrofit. The test runner therefore explores adversity as ordinary execution:

```
check schedules=10_000
check partitions=100
check restores=100
check scores=all          ; systematically enumerate scored-branch choices
```

Exploration randomness enters through `/entropy` (§21), so **every failing exploration replays exactly** from its film. Scheduler randomization, fault injection, partition simulation, and restore testing are modes of the one deterministic machine.

### 37.3 Film conformance monitoring

A film is a total record, and a sealed specification is executable — so conformance is a diff. An implementation may continuously validate **production films against a sealed specification film's invariants**, closing the gap between the verified design and the running system: the model and the implementation are the same graph.

## 38. Foreign functions

The FFI is boundary-based. Impure native calls cross a named wall and return observations:

```
[physics_request] --> /native.physics
/native.physics ==observed(result=#hash)==> [world]
```

Pure native functions may be imported as verified deterministic modules:

```
extern pure fn vec_dot(a: Vec3, b: Vec3) -> Fixed<16>
  from artifact #native-math-v3
```

Every extern pins: target ABI; compiler/toolchain hash; native artifact hash; declared effects; and determinism class (§15). An `extern pure` claiming bit-exact determinism is testable against that claim (§46) and is rejected if the artifact's outputs vary across supported targets.

---

# Part VI — Reference

## 39. Canonicalization and content identity

The canonical form contains no decorative line lengths and no source coordinates in semantic nodes.

```
Program
  declarations[]  actors[]  edges[]  boundaries[]
  stencils[]  fragments[]  derives[]  annotations[]
```

A canonical edge:

```json
{
  "kind": "edge",
  "texture": "async",
  "source": "actor:#coach",
  "label": "attack",
  "args": {"at": {"period": 4}},
  "target": "actor:#rider-a",
  "policy": "mailbox.default"
}
```

### 39.1 The canonicalization pipeline

1. Parse source, or load the structured editor graph.
2. Remove comments and non-executable presentation annotations.
3. Normalize identifiers, numeric forms, strings, and route aliases (derived textures → core, §8.2).
4. Expand stencils under the hygiene rules and identity formula (§31).
5. Evaluate derives to a fixpoint (stratified, monotonic, intrinsically typed; §32).
6. Resolve addresses and explicit shared captures.
7. Resolve every trait-method call site to a concrete instance and pin the instance hashes (§14.3).
8. Sort unordered fields and topology sets by canonical key.
9. Normalize route line lengths to texture tokens; convert visual dot counts to numeric period counts.
10. Validate types, effect rows, capabilities, boundaries, guards, and profile restrictions.
11. Serialize canonical graph bytes.
12. Hash the canonical bytes to obtain the content identity.

The entire pipeline is recorded as a build film (§36).

### 39.2 Formatting invariance (worked)

Two visibly different surfaces normalize to the same canonical graph and therefore the same hash.

Surface 1:

```
: [rider:a](energy=100){road}
: [rider:b](energy=100){road}
[coach] ~~attack~~> [rider:a]
[rider:a] --sprint--> //finish
```

Surface 2 (reordered, respaced, longer routes, a comment):

```
;; opening move
:   [rider:b]( energy = 100 ){ road }
:   [rider:a]( energy = 100 ){ road }

[coach] ~~~~~~attack~~~~~~> [rider:a]
[rider:a] --------sprint--------> //finish
```

Both reduce to:

```json
{
  "actors": [
    {"id": "rider:a", "cell": {"energy": 100}, "ports": ["road"]},
    {"id": "rider:b", "cell": {"energy": 100}, "ports": ["road"]}
  ],
  "edges": [
    {"texture": "async", "source": "coach", "label": "attack", "target": "rider:a"},
    {"texture": "solid", "source": "rider:a", "label": "sprint", "target": "//finish"}
  ]
}
```

Nothing decorative — line length, port order, staging order among independent forms, spacing, comments — survives into the semantic node set. Equal canonical bytes yield equal hashes. The same invariance holds between a behavior block and its equivalent drawn routes (§26, §46).

## 40. Static checks

A conforming checker rejects:

- duplicate durable identities in one sealed scope;
- unbound pattern variables; free variables in quoted fragments;
- overlapping deterministic branch guards (§20.1);
- shared mutable cells (§18);
- routes crossing undeclared capability walls; direct effects outside named boundaries;
- a `Float` type in a state cell of a `world`-profile actor (§15);
- an unbounded mailbox without an explicit overflow policy (§25);
- a non-anchored multi-node pattern on a rule's left side (§13);
- a capability or affine-resource capture in a value used where portability is required (§12.4);
- expression-layer punctuation outside the sanctioned set (§10.1);
- a Level-3 derive that deletes or mutates emitted structure (§32);
- a normal-outcome path promoted to a fault, or a fault demoted to a value (§24.3);
- non-exhaustive matches over variants without a `_` arm;
- missing stable tie-breakers for `oN.`;
- recursive stencil expansion without a decreasing budget; expansion exceeding declared fuel;
- mutation of content-addressed sealed artifacts;
- scheduler arrival order used as semantic data;
- mismatched `:: //` or `::: ///` scopes.

## 41. Execution profiles

An implementation may offer restricted profiles that trade expressiveness for guarantees:

| Profile | Characteristics | Simulation-state numerics |
|---|---|---|
| `pure` | no effect walls; finite fuel | integers, `Fixed<Q>`; `Float64` only with `#[det=bitexact]` |
| `replay` | effects supplied only from a film | as `pure` |
| `sandbox` | named adapters with quotas | as `pure` |
| `world` | persistent actors; bounded per-period reductions; lockstep-capable | integers, `Fixed<Q>`; floats forbidden in state cells |
| `forge` | generation plus verification gates | as `pure` |
| `cluster` | replicated facts and reconciliation; termination distinct from quiescence | as `pure` |

A **minimal conforming implementation** supports staged actors, the four core route textures, single `/` walls, `:: … //` fragments, `.n` period repetition, `?` variables, `|` guarded branches, `_` quiescence, and the expression core (records, variants, `Option`/`Result`, pure functions, `match`) — enough to observe the deterministic reduction property. Podium, stencils, derives, verified routes, merge, behavior blocks, streams, and the spatial canvas may be added incrementally without changing the core semantics.

## 42. Grammar

Illustrative EBNF. A conforming tokenizer uses explicit token classes for each route texture rather than recognizing arbitrary runs of punctuation.

### 42.1 Process notation

```
program        = { declaration | statement } ;

declaration    = stencil_decl | fragment_decl | derive_decl | actor_decl
               | actor_block | topology_decl | type_decl | fn_decl
               | trait_decl | module_decl | test_decl | extern_decl ;

actor_decl     = ":" actor_form [ state_form ] [ wiring_form ] ;
actor_form     = "[" actor_name "]" ;
state_form     = "(" [ field_list ] ")" ;
wiring_form    = "{" [ wiring_items ] "}" ;

fragment_decl  = "::" identifier [ parameter_list ]
                 { declaration | statement } "//" ;

stencil_decl   = ":::" identifier [ parameter_list ]
                 { declaration | statement } "///" ;

topology_decl  = "{" { edge_stmt | capability_stmt } "}" ;

statement      = edge_stmt | repeat_stmt | branch_stmt
               | stamp_stmt | bind_stmt | boundary_stmt | annotation ;

edge_stmt      = endpoint route endpoint ;
endpoint       = actor_form [ state_form ] | state_form
               | boundary | podium | address | rest ;

route          = solid_route | async_route | verified_route | fault_route
               | delayed_route | query_route | merge_route | rendezvous_route ;

solid_route     = "--" route_body "-->" ;
async_route     = "~~" route_body "~~>" ;
verified_route  = "==" route_body "==>" ;
fault_route     = "!!" route_body "!!>" ;
delayed_route   = ".." route_body "..>" ;      ; sugar → solid + schedule
query_route     = "??" route_body "??>" ;      ; sugar → solid ask
merge_route     = "<~" route_body "~>" ;       ; sugar → verified + crdt
rendezvous_route= "<--" route_body "-->" ;     ; sugar → async + continuation

route_body     = identifier [ argument_list ] ;

boundary       = "/" identifier | "//" identifier | "///" identifier ;
podium         = "o" integer "." ;
address        = "@" qualified_name [ argument_list ] ;
rest           = "_" ;

repeat_stmt    = "(" { statement } ")" repeat_suffix ;
repeat_suffix  = "." integer | dots | "..." ;

stamp_stmt     = "@" qualified_name [ argument_list ] [ "-->" endpoint ] ;
bind_stmt      = pattern "<-" expression ;

annotation     = "#[" field_list "]" ;
comment        = ";" { any_character_except_newline } ;
```

### 42.2 Expression and declaration notation (sketch)

```
expression     = literal | variable | path | call | match_expr | closure
               | record_expr | record_update | "(" expression ")"
               | expression binop expression | "not" expression
               | "try" expression ;

binop          = "+" | "-" | "mul" | "div" | "rem"
               | "=" | "<" | ">" | "<=" | ">=" | "and" | "or" ;

path           = identifier { "." identifier } ;
variable       = "?" identifier ;
closure        = "fn" "(" [ params ] ")" ( expression | block ) ;
record_update  = expression "with" "{" field_list "}" ;

fn_decl        = "fn" identifier [ generics ] "(" [ params ] ")"
                 "->" type [ "uses" "{" [ capability_list ] "}" ] block ;

type_decl      = "type" identifier [ generics ] "=" type_body
               | "enum" identifier [ generics ] "{" variant_list "}"
               | "resource" identifier ;

trait_decl     = "trait" identifier [ generics ] "{" { fn_sig } "}" ;

derive_decl    = "derive" identifier "(" params ")" "->" type block ;

actor_block    = "actor" identifier "(" [ params ] ")" "{"
                 "state" state_form
                 [ "ports" wiring_form ]
                 { "on" route [ "when" expression ] block }
                 "}" ;

module_decl    = "module" path "@" hash
                 { "export" "{" name_list "}" | "import" path "@" hash "as" identifier } ;

test_decl      = ( "test" | "property" | "film_test" ) string block
               | "check" identifier "=" ( integer | "all" ) ;

extern_decl    = "extern" "pure" fn_sig "from" "artifact" hash ;
```

Disambiguation notes: `(x=1)` is a cell, `(expr)` is grouping, and a field-form parenthesis attached to `[actor]` is always state; `.5` is a period count, `.....` is its sugar in repeat position, `...` is continuation, the `.` in `oN.` belongs to the podium token, and a `.` between identifiers is a path; `*` inside an identity selector is a wildcard and before a stamp is replication, with `mul` for multiplication; angle brackets are legal only attached to an identifier.

## 43. Worked examples

These seven span sports, distributed systems, fabrication, biology, machine-assisted patching, and a versioned service. Together they exercise every construct in the language.

### 43.1 Criterium race — staging, stencils, periods, async, finish, podium

```
; a five-lap criterium with async team radio and a podium

::: rider(name, watts)
  [rider:#name](watts=watts, energy=100, lap=0, status=staged){road, radio, timing}
///

: @rider(a, 330)
: @rider(b, 295)
: @rider(c, 410)
: @rider(d, 305)
: [coach](plan=wait_then_attack)
: [clock](period=0)

{
  [coach] ~~radio~~> [rider:*]
  [rider:*] ~~draft~~> [rider:next]
  [clock] ..tick..> [rider:*]
}

(
  [clock](period=?t) --advance--> (clock period=?t+1)
  [rider:*](lap=?l, energy=?e) --ride(cost=8)--> (rider:* lap=?l+1, energy=?e-8)
  [coach](plan=wait_then_attack) --when(clock.period=4)--> (coach plan=sent)
  [coach] ~~attack~~> [rider:c]
).5

[rider:*] --sprint--> //finish
//finish ==rank(by=time, tie=#id)==> o3.
[winner, second, third] <- o3.
///race-result
```

### 43.2 Supervised worker pool — mailboxes, quiescence, faults, restart

```
::: worker(id)
  [worker:#id](status=idle, checkpoint=0){jobs: Mailbox<Job, capacity=256, overflow=reject>, supervisor}
///

: [supervisor:pool](policy=restart_one)
: @worker(a)
: @worker(b)
: @worker(c)
: [queue](jobs=[j1, j2, j3])

[worker:*] ^ [supervisor:pool]

[queue] ~~job(?j)~~> [worker:*]
[worker:*] _--> active(job=?j)
[worker:*] --perform(?j)--> (worker:* status=idle, checkpoint=?j)
[worker:*] --> _

[worker:b] !!crash(reason="bad input")!!> [supervisor:pool]

[supervisor:pool](policy=restart_one)
  --on(crash(worker=?w))-->
@worker(?w, restored_from=last_checkpoint)

[supervisor:pool] ==pool_quiescent==> //done
```

### 43.3 Replicated fact lattice — CRDT merge, partition, convergence

```
: [node:a]{facts, peers}
: [node:b]{facts, peers}
: [node:c]{facts, peers}

[worker:a] ~~candidate(program=#p1, result=true)~~> [node:a]
[node:a] --verify(program=#p1)--> [fact:#f1]
[fact:#f1] ==accepted(by=node:a)==> [node:a]{facts+#f1}

[node:a] <~merge(facts)~> [node:b]
[node:b] <~merge(facts)~> [node:c]

/partition
[node:a] <~blocked~> [node:c]
[node:c] --derive(from=#f1)--> [fact:#f2]

/partition --open--> _
[node:a] <~merge(facts)~> [node:c]
[node:b] <~merge(facts)~> [node:c]

[node:a]{facts} ==same_hash==> [node:b]{facts}
[node:b]{facts} ==same_hash==> [node:c]{facts}
///converged
```

### 43.4 Forge world fabrication — model wall, checks, verification, seal

```
: [brief](goal="coastal cycling city", players=64)
: [seed:#city17]

[brief] & [seed:#city17] --derive--> [world_spec]
[world_spec] --> /model
/model ==observed(candidate=#layout1)==> [layout:#layout1]

[layout:#layout1] --check_connectivity--> [report:roads]
[layout:#layout1] --check_spawn_safety--> [report:spawns]
[layout:#layout1] --check_budget--> [report:budget]

[layout:#layout1]
  & [report:roads] & [report:spawns] & [report:budget]
  ==verified(policy=forge.world.v1)==>
[film:#world17]

[film:#world17] --> /gpu
/gpu ==preview(frame=#preview17)==> [designer]
[designer] ~~approve~~> [film:#world17]
[film:#world17] ==seal==> ///world17
```

### 43.5 Cell signaling — membranes, diffusion, decay

```
::: cell(id, kind)
  [cell:#id](kind=kind, active=false, energy=50){membrane, neighbors}
///

: @cell(a, sensor)
: @cell(b, relay)
: @cell(c, motor)
: [field](signal=0)

[field](signal=?s) --increase(10)--> (field signal=?s+10)
[field] ~~diffuse(level=?s)~~> [cell:a]

[cell:a](kind=sensor, active=false) --when(signal>5)--> (cell:a active=true)

[cell:a] ~~ligand(type=go)~~> /membrane:b
/membrane:b --bind(type=go)--> [cell:b]
[cell:b] ~~relay(type=go)~~> /membrane:c
/membrane:c --bind(type=go)--> [cell:c]
[cell:c] --contract--> (cell:c energy=energy-5)

([field] --decay(1)--> [field]).10
```

### 43.6 Proof-carrying patch — parallel checks, verified acceptance, seal

```
: [issue:#217](failure="stale imported schedule")
: [repo:#trvm](revision=#a91)

[issue:#217] & [repo:#trvm] --> /model
/model ==observed(patch=#p44)==> [patch:#p44]

|| {
  [patch:#p44] --compile--> [report:compile]
  [patch:#p44] --property_tests--> [report:laws]
  [patch:#p44] --replay_battery--> [report:replay]
  [patch:#p44] --diff_scope--> [report:scope]
}

[patch:#p44]
  & [report:compile] & [report:laws] & [report:replay] & [report:scope]
  ==verified(policy=trvm.patch.v1)==>
[film:#accepted-p44]

[film:#accepted-p44] ==merge_candidate==> //review
[reviewer] ~~approve~~> //review
//review ==seal==> ///release-candidate
```

### 43.7 Versioned telemetry ingest — expression notation, behavior block, backpressure, migration, test

```
module ingest@#b12

type Reading = { sensor: SensorId, value: Fixed<16>, at: Period }

enum IngestNote { out_of_range(sensor: SensorId), duplicate(sensor: SensorId) }

fn validate(r: Reading) -> Result<Reading, IngestNote>
  uses {} {
  match r.value {
    v when v >= 0 and v <= 5000 => ok(r)
    _                           => err(out_of_range(r.sensor))
  }
}

actor ingest(shard: ShardId) {
  state (stored=0, noted=0)

  ports {
    readings: Mailbox<Reading, capacity=1024, overflow=backpressure>,
    archive: Port<FactWrite>
  }

  on ~~Reading(?r)~~> {
    match try validate(?r) {
      ok(?v)  => [self] --store(?v)--> {facts + ?v}
      err(?e) => [self] --note(?e)--> (state noted=state.noted+1)
    }
  }

  on ~~unknown(#msg)~~> {
    [self] --forward(#msg)--> /adapter.v1v2     ; unknown messages are outcomes, not faults
  }
}

; demand-driven collection
[ingest:shard] ~~demand(32)~~> [sensor:*]
[sensor:*] ~~Reading(batch)~~> [ingest:shard]

; upgrading a live shard
(state: Ingest@#a91) ==migrate(policy=ingest.v1v2, by=#m7)==> (state: Ingest@#b12)

test "validation rejects out of range" {
  validate({sensor=s1, value=9000, at=0}) = err(out_of_range(s1))
}

check schedules=10_000
```

## 44. Exclusions

The following are permanently excluded. They are not "future work"; each would break a stated principle.

- textual or unhygienic macros; raw token-array metaprogramming
- operator overloading of punctuation
- implicit conversions
- `null`
- class inheritance; deep hierarchies; implicit virtual dispatch; actors inheriting actor implementations
- hidden exceptions
- shared mutable global state; shared mutable pointers
- nondeterministic map or set iteration
- ambient filesystem / network / model / clock access — at run time or compile time
- arbitrary compile-time I/O; compile-time host introspection
- scheduler-dependent mailbox selection; scheduler arrival order as data
- semantics derived from canvas coordinates
- a new punctuation symbol for every conventional feature

## 45. Reserved and implementation-defined

The following are intentionally left open; a conforming implementation may specify them, but the language does not fix them:

- **Byzantine trust modes.** The CRDT laws (§22) guarantee convergence among honest replicas. The trust and evidence policy for dishonest peers is implementation-defined (`trust=` on merge routes).
- **Distributed termination detection.** The specific detector that distinguishes true termination from temporary quiescence (§20.11) is implementation-defined.
- **Scoring functions.** A scored branch must record its scores as facts so replay is exact (§21, §37.2); the scoring function itself is implementation-defined.
- **Four-stroke delimiters** (`::::`, `////`): reserved, undefined.
- **Backtick blocks**: reserved for raw or foreign-code embedding beyond §38, admitted only behind an authority wall with a pinned toolchain and artifact hash.
- **Explicit spatial predicates** (e.g. `#[inside=/district.north]`, `#[near=[station], distance<20m]`): reserved. Spatial layout is presentation only; geometry becomes semantic only when explicitly declared.

## 46. Conformance

An implementation conforms if it satisfies the following observable properties. They double as a test matrix.

| Property | Test |
|---|---|
| Formatting invariance | random spaces and line lengths retain the semantic hash |
| Two-surface isomorphism | a behavior block and its equivalent drawn routes produce identical canonical bytes |
| Scheduler invariance | randomized worker ordering retains the committed film |
| Replay exactness | a live run and its replay share all observables |
| Build invariance | the same inputs produce an identical build film and identical hashes on different hosts |
| Memoized-build soundness | reusing `(transform#, input#)` cache entries yields outputs identical to a cold build |
| Fragment hygiene | copied fragments do not alias local identities; rebuilds reproduce derived identities (§31.2) |
| Merge laws | fact union is commutative, associative, idempotent; the pinned join instance is identical across replicas of one program hash |
| Boundary safety | undeclared effects cannot cross walls; capability-capturing values cannot travel |
| Ranking stability | `oN.` is unaffected by arrival order |
| Numeric portability | `world`-profile simulations produce identical films across supported targets; `extern pure` artifacts honor their declared determinism class |
| Restore correctness | imported stale work prevents false termination |
| Resource safety | loops, mailboxes, streams, and expansion respect budgets and bounds |
| Portability | the same sealed film executes identically across runtimes |

---

*End of specification. The language becomes real when one small set of reading laws — shape says what a thing is, texture says how it moves, colons introduce and slashes bound, marks for architecture and words for computation — accurately expresses a bike race, a supervised server, a replicated document, a generated world, a biological pathway, a proof-carrying patch, and a versioned service, and all of them compile to one inspectable canonical graph whose build, execution, and history are equally replayable.*