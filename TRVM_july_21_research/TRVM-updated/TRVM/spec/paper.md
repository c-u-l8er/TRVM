# A Coordination-Free Distributed Interaction-Calculus Runtime

*A correct, packed-word, WebAssembly interaction-calculus reducer, and the argument
and evidence that its reduction distributes across machines with no locks and no
consensus.*

---

## Abstract

Optimal interaction-net evaluators (the HVM lineage) compile the Interaction
Calculus to fast single-node machine code and are converging on parallel program
and proof **search** as their destination. We observe that the axis they are *not*
building is **distribution across machines**, and that it is both open and a
natural fit: interaction-net reduction is confluent by construction, which makes
single-net reduction *schedule-independent*. Coordination-freedom **across
machines** additionally requires the boundary-port discipline of §4.5 (owner-only
rewrite over monotone, never-retracting export grafts); we keep these two
guarantees distinct rather than collapsing distribution onto confluence alone. We
make this concrete. We (1) build a correct reducer for the
Interaction Calculus using the floating-duplication representation, fixing a
higher-order-duplication bug class that defeated several hand-rolled attempts; (2)
compile it to a packed-word native runtime that exhibits the optimal-evaluation
speedup (parity of 2²⁴ in 480 interactions) at ~22–34 M interactions/sec; (3)
compile that to a 9.9 KB dependency-free WebAssembly module that matches the
reference bit-for-bit; and (4) demonstrate coordination-free distributed reduction
in three regimes — a simulated boundary-port reducer (480 schedule/partition-
independent runs), the same protocol on real OS processes over real IPC, and the
WASM runtime running coordination-free across real isolated workers. The result is
a working, validated, browser-native, coordination-free, multi-node interaction-
calculus runtime. Every claim is backed by runnable, self-validating code; every
limitation is stated plainly.

---

## 1. Introduction

The HVM lineage (HVM2 → HVM4 → HVM5) crystallized the operational core of optimal
λ-reduction into the **Interaction Calculus** (IC): a small grammar — variables,
erasure, lambda, application, superposition, and labeled duplication — whose
reduction "matches optimal λ-reduction perfectly." HVM compiles IC to zero-overhead
native code (and to GPU), ships superposition-based program/proof search natively,
and is explicitly aimed at becoming a parallel theorem prover that "OOMs faster than
Lean." Its development is increasingly AI-driven and fast-moving; a new single-node
core is, by demonstration, a thing that can be rebuilt in days.

Racing that core is pointless. But there is a direction the lineage is *not*
pursuing: **reduction distributed across machines.** This paper argues it is the
right place to build, and provides a working substrate for it.

The thesis rests on one structural fact. **Interaction-net reduction is confluent
by construction** — interaction rules act on disjoint active pairs and the result is
independent of the order they fire. Confluence is precisely what makes distribution
coordination-free: if order does not matter, then *which node* fires a redex, and
*when*, does not matter either. So a single computation can be sharded across nodes
and reduced with **no locks and no consensus**. The only thing that must hold
globally is that everyone eventually stops — and even that, we show, is a
control-plane question that only arises in one of the distribution regimes. The
slogan: **reduction is the data plane and needs no coordination; only termination
is ever a control-plane question.**

A second motivation is **sovereignty**. If the runtime is WebAssembly, the same
artifact runs in any browser with no server. Multi-node compute then means
browser-to-browser, edge, client-side — which is the substrate an open,
decentralized agent stack wants.

We build the stack bottom-up, and at each step the artifact is runnable and
self-validating:

1. **A correct reducer** (`ic_ref.py`, then `ic_float.py`) — §3.
2. **A packed-word native runtime** (`ic32.c`) — §4.
3. **A WebAssembly build** (`ic32.wasm`) — §5.
4. **Coordination-free distribution**, in three regimes (`dist_ic.py`,
   `dist_real.py`, `swarm.js`) — §6.

---

## 2. Background

**The Interaction Calculus.** Terms are `VAR | ERA "*" | LAM "λx.t" | APP "(f a)" |
SUP "&L{a,b}" | DUP "!&L{x,y}=t;u"`. Variables are *affine* (occur at most once) and
globally unique; using a value twice requires an explicit `DUP`, and labels `L`
distinguish independent duplications. Reduction is a small set of local interaction
rules (beta `APP-LAM`; the duplication rules `DUP-LAM`, `DUP-SUP`; erasure; and the
"collapse" rules `DUP-VAR`/`DUP-APP` that copy free/stuck terms). Substitution is a
*global map* over the affine variables, not a tree rewrite — `x ← t` is just
`sub[x] = t`. Superpositions `&L{a,b}` let two computations share structure and be
reduced together; this is the basis of HVM's program search.

**Confluence.** Interaction systems are strongly confluent by construction. This is
the load-bearing property for everything in §6.

**CALM and CRDTs.** The CALM theorem (Hellerstein) states that a computation has a
coordination-free distributed implementation **iff** it is monotone. Conflict-free
replicated data types (CRDTs) are the standard monotone building block; a grow-only
set under union is the simplest. These two notions are *related but not identical*,
and the distinction is load-bearing for §6. **Confluence** (Church–Rosser)
conserves the *normal form* of a **fixed, closed net** under reordering of its
internal reduction steps. **CALM-monotonicity** conserves the *observable output*
as a ⊆-monotone function of a **growing input set** in an **open** system. A
boundary-port (BND) wire arrival is not a reduction step but a *structural
extension* of the net — exactly the event Church–Rosser assumes away — so
confluence alone does not discharge the open-system obligation. What confluence
supplies is schedule-independence; coordination-freedom across machines is supplied
by the BND ownership + monotone-export discipline (§4.5). Concretely: the set of
*fired* boundary pairs is grow-only and CALM-safe, but *reading out a partial
normal form* gated on cross-boundary fan resolution is not monotone — which is why
global termination (§4.6) is the one residual coordination point.

---

## 3. A correct reducer

### 3.1 The bug class

Several hand-rolled reducers reconstructed the interaction rules by **rewiring
ports** and all hit the same wall: a *higher-order duplication* bug. Concretely,
duplicating a Church numeral and applying a copy of it to another higher-order term
(e.g. computing `2 2` in Church encoding, where one numeral is duplicated and
applied to another) corrupted the term into stuck fans with dangling wires.

The fix was not a cleverer patch but to follow the reference faithfully. Three
things the reference does that the hand-rolled versions did not:

1. **Substitution is a global map**, not port rewiring. Affine + globally-unique
   variables make `x ← t` a single dictionary insertion, eliminating the name-
   capture and rewiring errors entirely.
2. **Every interaction is total** — including the collapse rules `DUP-VAR` /
   `DUP-APP` that give a defined reduction for duplicating a free or stuck term.
   Without these, those cases silently wedged.
3. **Correct `DUP-LAM` wiring with distinct labels per duplication**, so
   duplicating a value that itself contains duplications does not wrongly
   annihilate.

`ic_ref.py` transcribes the rules one-to-one and is self-validating. It reproduces
the reference's "tests all interactions" term to `λa.λb.a` in **exactly 16
interactions** (matching the reference count), computes Church exponentiation
correctly — `(2 2)=4, (3 2)=8, (2 3)=9, (3 3)=27` — and handles Church-N applied to
`NOT`. The middle results are precisely the computations that defeated the hand-
rolled versions.

### 3.2 The floating-duplication representation

`ic_ref.py`'s simple "body-carrying" representation diverges on one pattern:
duplicate a higher-order numeral, then apply a *copy* to another higher-order
lambda. Its eager whole-structure traversal loops. The fix is the representation
HVM actually uses (`ic_float.py`): **duplications carry no body and float on the
heap**, reached only through their projection variables `DP0`/`DP1`, and they fire
**lazily and incrementally** — one split when a projection is demanded. The
duplicated structure is never eagerly walked, so the pattern terminates.

Validated against `ic_ref.py` as oracle: identical normal forms on every
terminating term (23 in the battery), and **correct termination on all four cases
`ic_ref` diverges on**, including using both copies of a duplicated numeral and a
deeper `church3`. (Honest note: on terminating arithmetic the floating version
records *more* interaction-rule firings, because its collapse rules are explicit;
the two representations do different bookkeeping but produce identical normal
forms. Its value is generality and being the correct compilation target.)

---

## 4. A packed-word native runtime

`ic32.c` re-expresses the floating-dup rules over a flat heap of 64-bit tagged
words. The word format follows an earlier in-house spec (`addr<<32 | label<<4 |
tag`), with the one spare bit used as the IC32 substitution flag. Substitution is
**in-place at the binder's slot**: a variable's address points at its binder node;
when the binder is consumed the substituted term is written there with the
substitution bit set. Duplications are bodyless heap nodes reached only through
their projection variables. Allocation is a bump pointer.

**Correctness.** Against the Python oracles on the full battery (24 terms): exact
match, and **identical interaction counts** — the packed reduction is the same
strategy, just packed. It also terminates on the divergent-pattern cases with the
same counts.

**Optimal sharing.** Computing the parity of `2ᴺ` as `NOT^(2ᴺ)(FALSE)` costs ~`80 +
20N` interactions — *linear in N* while `2ᴺ` is exponential. Parity of `2²⁴ =
16,777,216` takes **480 interactions**. This is the optimal-λ-evaluation speedup
(the reason the lineage exists), and it falls out of the runtime unforced: the
repeated `NOT` applications are shared, not expanded.

**Throughput.** ~22–34 M interactions/sec, handling 100K-interaction reductions in
milliseconds.

**Self-validation and deep terms.** The runtime is self-validating: `./ic32 --test`
runs an in-binary battery (thirteen cases — eight correctness checks, three church-arithmetic
checks, two deep-depth stresses), so conformance no longer depends on an external harness. The
*parser*, the normaliser, and the readback are all **iterative**, using explicit growable
stacks rather than C recursion, and the binder/free name tables grow, so a term of arbitrary
nesting depth parses, normalizes, and reads back without overflowing the stack — the battery
parses a 200,000-deep input end-to-end and reads back a 500,000-deep normal form, and via
stdin both 500k-deep applications and 60k-deep lambdas work, where a recursive-descent version
overflowed around ~4k.

Like HVM's core, `ic32` is a *low-level* runtime: it expects interaction nets in which
independent duplicators carry **distinct labels** (the discipline a compiler supplies — `lc2`
assigns a fresh fan label per numeral for exactly this purpose). Given correctly-labeled,
explicitly-duplicated input it computes church **multiplication and exponentiation** correctly
(`clin(3)·clin(2)` reduces to church 8, `mult(7,3)` to church 21 — both in `--test`).
Naively-written church numerals — non-linear binders, or a single shared duplicator label
across independent numerals — reduce incorrectly, because same-label duplicators wrongly
annihilate; this is the standard interaction-net labeling requirement, not a defect in the
reduction engine, which matches `ic_ref` exactly on the 24-term oracle and reduces the dup-free
`NOT` correctly through the 2²⁴-parity computation. Garbage collection is now incremental
(free-list recycling of consumed nodes plus eraser propagation — see the maturity notes below);
the remaining runtime piece is the ERA-DUP rule, plus porting GC to the wasm build.

---

## 5. WebAssembly: the sovereignty substrate

`ic32.wasm` is the same runtime compiled **freestanding** with clang to a wasm32
module — no `emscripten`, no `wasi-libc`, no JS glue runtime. The heap is a static
array in linear memory (the existing bump allocator), and the few libc primitives
needed are a handful of lines. The module is **9.9 KB** and exposes a five-function
ABI (`memory`, `input_ptr`, `output_ptr`, `run`, `last_interactions`); a ~25-line
host writes a term into memory, calls `run`, and reads the result.

**Validation.** Driven over the same battery, **28/28 terms match the Python
oracle** (including the divergent-pattern cases). Interaction counts are **identical
to the native build** — the strategy survives compilation. Optimal sharing survives
the compile (parity of `2ᴺ` stays linear). In-process throughput (startup
amortized) is **~34 M interactions/sec**, native-comparable.

**Honest limitation.** The recursive `normal`/`whnf` overflow V8's WASM call stack
on deeply-nested output: depth-8192 readbacks run fine, but a 59049-deep readback
throws. The native build handles it (a larger C stack). The fix is an iterative
`normal` with an explicit work-stack — mechanical, not yet done. Every battery term
and realistic agent/search term is far shallower.

---

## 6. Coordination-free distribution

The thesis is that confluence makes reduction coordination-free. We demonstrate it
in three regimes, which together span simulation and reality.

### 6.1 The boundary-port protocol, in simulation (`dist_ic.py`)

A single term's heap is **sharded across nodes**; a reference is a global
`(node, addr)`. Each interaction is performed by the node that **owns its
principal** (the lambda, the superposition, the floating dup), dereferencing across
boundaries on demand. No node ever needs a lock or a global agreement to fire a
redex. The test that this is real: vary the partition (which node owns what) and the
evaluation order (which child is normalized first) and confirm the answer is
invariant.

**Result.** Single-node reduction over the sharded store matches the oracle on 20
terms. Each term run under **24 configurations** (worker counts × {round-robin,
block, randomized} partitions × {left-first, right-first} order) — **480 runs
total** — every one produces the single-node normal form. One distinct result.
Cross-node interaction counts range from 0 (a partition that co-locates interacting
nodes) up to the full count (maximally scattered) — real communication, invariant
answer. Including the cases `ic_ref` diverges on.

In this **demand-driven** model termination is **structural**: the computation is
done when the root normalization returns; there are no autonomously-firing redexes
in flight, so no distributed termination detector is needed.

### 6.2 The same protocol on real OS processes (`dist_real.py`)

We take the protocol off the simulation: each node is a genuinely isolated OS
process holding a heap shard in its own memory, and **every cross-shard reference is
a real message** over a `multiprocessing` channel. The reducer is `dist_ic.py`'s,
unchanged — it is parameterized over a `net` whose `read`/`write`/`alloc` are now
IPC calls.

To stay deadlock-free without re-entrant workers, we use the simplest sound split:
**workers are passive shard servers** (read/write/alloc, never blocking on each
other) and a single coordinator runs the reduction over real messages. The **state
is genuinely distributed; the control flow is centralized.**

**Result.** Every term, every worker count, every partition equals the single-node
oracle (including the divergent cases), with real IPC reported (66–514 messages per
reduction) and cross-shard interaction counts **identical to the simulation**. The
protocol behaves the same over real channels.

The honest cost of centralized control flow is chattiness — Ex5 does 16 interactions
but 139 IPC messages, because every slot access is a round trip. A distributed-
control-flow system would perform each interaction on the owning worker, collapsing
messages to boundary-crossings only (9 for Ex5). That needs re-entrant workers
(threads + per-shard locks) or a CPS scheduler, and is where parallel speedup would
come from. Neither is claimed here.

### 6.3 The WASM runtime, coordination-free across real workers (`swarm.js`)

The capstone runs `ic32.wasm` across Node `worker_threads` — the Web Worker analog;
in a browser these are literally Web Workers, with separate JS realms and separate
WASM linear memory. **Each worker is a genuinely isolated node** with its own WASM
instance and heap. The workers partition a search and each reduces its slice
*through the WASM runtime* (the per-candidate predicate `NOT^n(FALSE)` is a real
reduction). Their solution sets merge by **union — a grow-only-set CRDT join**.

Because the merge is monotone, CALM guarantees the answer is independent of worker
count and merge order.

**Result.** Across worker counts `W ∈ {1,2,3,4,6,8}` and multiple merge orders,
there is **one distinct merged result, equal to the brute-force oracle**, with the
total interaction count constant (1264) across all partitions. Coordination-free
correctness on the real WASM runtime: any worker count, any merge order, same answer.

**Honest limitation.** At this toy scale worker-thread startup dominates wall-clock,
so more workers is not faster. The claim is coordination-free correctness, not
speed; speedup needs a heavier per-worker workload or the distributed-control-flow
regime.

### 6.4 The regimes, together

| | model | nodes | cross-node | termination | status |
|---|---|---|---|---|---|
| `dsearch.py` | superposed/independent **search** | (sim) | none | trivial | coordination-free |
| `swarm.js` | search on the WASM runtime | **real workers** | none (CRDT merge) | trivial | **real, coordination-free** |
| `dist_ic.py` | one term, sharded **reduction** | sim | owner interaction | structural | coordination-free |
| `dist_real.py` | the same reduction | **real processes** | real IPC | structural | **real, coordination-free** |
| `p2.py` | one combinator net | real threads | owner = `min` | **Safra detector** | real, autonomous |

The harder regime — **autonomous redex bags**, where every node drains its own work
and pushes across boundaries with no central call/return structure — is where global
quiescence becomes nontrivial and needs a Safra-style termination token. `p2.py`
implements that for the interaction-combinator model (40/40 reductions matched the
oracle; 20/20 terminations detected). The IC32 autonomous regime, which would unlock
parallel speedup, reuses that detector and is the principal remaining engineering
step.

### 6.5 What the evidence certifies — precisely

Three scope notes, so the demonstrations are not read for more than they support:

- **WASM/native bit-for-bit parity (§5) certifies sequential implementation
  correctness** — closed-net normal-form agreement on a single schedule. It is
  necessary, not sufficient, for the open/boundary-port regime, which it does not
  exercise.
- **`dist_ic.py`'s 480 runs vary both schedule and partition**, but under a
  **centralized control plane** (a single coordinator drives root normalization,
  §6.2). They certify partition- and schedule-invariance of a *demand-driven*
  reduction — not of an *autonomous* one where nodes fire boundary redexes with no
  central call/return structure.
- **`swarm.js` is partition-independent for independent search** (disjoint slices
  merged by monotone union). It does not exercise a *shared sharing graph* whose
  fan (DUP) auxiliary ports straddle a partition — the case where ownership of a
  cross-partition active pair is genuinely ambiguous.

The regime that exercises all of these at once — autonomous IC32 sharded reduction
over a shared sharing graph with no central coordinator — is unbuilt (§6.4; the
`p2.py` autonomous detector covers interaction-combinators only). There the
standing open question is whether boundary-port reconnection can introduce a *new
active pair*; the equality of interaction counts across configurations holds only
under the currently-unstated precondition that it cannot.

---

## 7. Results (consolidated)

- **Reducer correctness:** reference "all-interactions" term → `λa.λb.a` in 16
  interactions (exact); Church arithmetic and exponentiation correct; the higher-
  order-duplication bug class eliminated.
- **General reducer:** `ic_float` matches `ic_ref` on 23 terms and terminates
  correctly on 4 cases `ic_ref` diverges on.
- **Native runtime:** 24/24 oracle match with identical interaction counts; optimal
  sharing (parity of 2²⁴ in 480 interactions); ~22–34 M interactions/sec.
- **WebAssembly:** 9.9 KB, 28/28 oracle match, counts identical to native, ~34 M
  interactions/sec in-process.
- **Distribution (sim):** 480 schedule/partition-independent runs, all equal to
  single-node.
- **Distribution (real processes):** all runs equal single-node over real IPC;
  cross-shard counts identical to simulation.
- **Distribution (WASM workers):** one distinct result across all worker-count ×
  merge-order configurations, equal to the oracle.

All artifacts are self-validating (each prints its own pass/fail).

---

## 8. Limitations

We state these plainly because the value of the work depends on them being honest.

- **No parallel speedup is demonstrated.** Every distribution result is
  coordination-free *correct*, not faster. Speedup needs concurrent workers actually
  reducing at once (the autonomous / distributed-control-flow regime), not the
  demand-driven or passive-server models used here. What `parallel.py` *does* establish,
  short of that, is the two pieces that bracket the missing one: it measures the
  **available parallelism** of a confluent workload machine-independently — work over span,
  ≈65-way on a fold of 96 independent leaves (work 297,789 interactions, span 4,606) — which
  by Brent's bound is the linear speedup real multi-core hardware would realize; and it
  confirms the **coordination-freedom** that makes the split safe (the merged result is
  identical across worker counts and finish orders, no shared state, no locks). The gap is
  purely the wall-clock realization, which needs more than one core (the sandbox has one),
  and a fine-grained span — causal depth of a single term's reduction — would quantify the
  automatic-parallelism claim beyond the coarse fold.
- **Centralized control flow in the real-process reducer.** `dist_real.py`
  distributes state but not control; messages are therefore chattier than a
  distributed-control system would need.
- **Recursive normaliser depth limit.** `normal`/`whnf` recurse; on deeply-nested
  output this overflows V8's WASM stack (and Python's recursion limit). The
  iterative rewrite is mechanical but unimplemented.
- **Garbage collection (Phases 1-2).** Consumed redex nodes are recycled via size-classed free
  lists (no tracing, no pauses, as befits local confluent reduction; 33-40% lower heap high-water
  on dup-heavy reduction, `./ic32 --gcstats`), and eraser propagation reclaims directly-discarded
  sub-nets at APP-ERA (`./ic32 --erasestats`: a 2000-deep erased spine, 4002 live slots -> 2);
  13/13 self-test unchanged. Measured limit: under lazy reduction the discarded thing is usually
  an unevaluated var binding, so var-indirect and affine-unused cases do not reclaim -- closing
  them is substitution-aware reclamation or compiler-inserted erasers (the ERA-DUP rule remains),
  not a tracing collector. Formerly: a single very large
  reduction is bounded by the static heap.
- **The native runtime is still tree-walking**, not the redex-bag/SIMD core HVM
  compiles to; it is the correct *representation*, fast, but not the fastest
  possible engine.
- **`SPEC.md`'s node model differs from what was built.** The word *format* is
  reused; the *node* model is IC32 typed-node (so it validates against the reducer),
  not the spec's older combinator nodes. The combinator model and its boundary-port
  (`BND`) machinery remain the basis for the autonomous distribution regime.

---

## 9. Related work

> A fuller prior-art map, with an explicit and deliberately conservative bound on what is
> novel here, is in `RELATED_WORK.md`. In short: the coordination-free-reduction property is
> Lafont's (the defining property of interaction nets, 1989); optimal sharing is
> Lévy/Lamping; CRDTs-as-semilattices is Shapiro and the monotonicity link is CALM;
> content-addressing is Unison/Nix; e-graphs and the slotted technique are egg/egglog and
> Schneider–Koehler–Steuwer (PLDI 2025); and sigma-as-H¹-consistency is Robinson/Ghrist/Hansen
> (with the sheaf-over-lattices direction already underway). None of those is original here.
> What is plausibly novel is the *synthesis* and the *measurements*: the merged object being
> *computation*, the tier/invariant-absorption framework, and the specific end-to-end
> combination. The text below is the original, shorter version.

**HVM / Interaction Calculus** (Higher Order Co.) is the single-node optimal
evaluator this work builds on and deliberately does not compete with; our
contribution is orthogonal (distribution). **Lamping/Asperti** optimal λ-reduction
is the theory behind the sharing in §4. **PELCR** distributes interaction nets via
Geometry-of-Interaction token passing but is shared-memory only; the graph-rewriting
line (MPINE, HVM) is single-machine. To our knowledge **no multi-node graph-
rewriting interaction-net runtime exists**, which is the niche here. **CALM**
(Hellerstein) and **CRDTs** are the coordination-freedom theory in §6. **Safra's
algorithm** is the distributed termination detector reused for the autonomous
regime.

---

## 10. Conclusion and destination

We set out to occupy the axis the HVM lineage is not building — distribution across
machines — on the structural ground that interaction-net reduction is confluent and
therefore coordination-free, and on a sovereign WebAssembly substrate. The result is
a correct reducer, a fast packed-word runtime, a tiny WASM build that matches it
bit-for-bit, and coordination-free distributed reduction demonstrated in simulation,
on real OS processes, and on the WASM runtime across real isolated workers. Reduction
is the data plane and needs no coordination; only termination, and only in the
autonomous regime, is a control-plane question — for which a known detector applies.

The destination is integration with an open, decentralized cognitive-architecture
stack: cheap symbolic agents as interaction-calculus sub-nets running on the WASM
engine by the thousands, a verified governance floor evaluated *on* that same
engine, and coordination-free state and search across browsers and edge via the
CRDT and boundary-port models shown here. The substrate now exists. The principal
remaining runtime step is the autonomous regime (re-entrant workers + Safra) that
turns coordination-free *correctness* into parallel *speedup*; the principal
remaining product step is wiring the engine into that stack.

---

## 11. Postscript: a confluent merge of computation (the IN-CRDT experiments)

External review of this work converged on a sharper forward question than "distribute
reduction": can knowledge be *merged* across replicas such that the object replicated
is **computation, not data** — a CRDT whose elements are interaction-calculus
derivations? Confluence already gives the commutativity and associativity a CRDT
needs; the open question is whether reduction *preserves* those properties and, above
all, whether **idempotence holds operationally** — does merging a replica with itself
re-pay for work already done? We ran the cheap decisive experiments
(`incrdt.py`, `incrdt2.py`, `incrdt3.py`; full account in `INCRDT.md`).

The operator is `merge(A,B) = NF(A ∪ B)`: reduce the content-addressed union as one
net. The findings, all on runnable code:

- **The axioms are preserved.** `NF(A∪B) = NF(B∪A)`, and across incremental merges
  `NF(NF(A∪B)∪C) = NF(A∪NF(B∪C))` — staging does not change the facts.
- **Idempotence is the crux, and it splits.** The *set of facts* is idempotent for
  free (identical normal forms collapse — a data CRDT over the facts is a trivial
  G-Set). But operationally, a naive (multiset) union is **not** idempotent: it
  doubles work, storage, and depth while leaving the normal form equal — a CRDT
  semantically, useless operationally. **Content-addressing restores operational
  idempotence on all four metrics** (rewrites, nodes, depth): `merge(A,A)` costs
  exactly what `A` costs.
- **Sharing survives reduction, with an exact cost law.** N derivations sharing a
  sub-computation `(church6 NOT)` cost `60·N` unshared but `49 + 11·N` shared — the
  expensive core is built once; you pay only for what is genuinely new. This is the
  "does not pay repeatedly for already-discovered work" property, measured.
- **Automatic, not hand-encoded.** A content-addressing pass that finds repeated
  *closed* sub-terms and shares them through a DUP fan reproduces the hand-encoded
  numbers exactly, with the normal form unchanged at every N — so the sharing is
  sound even though the shared sub-term itself contains dups (the dup-of-a-dup case
  that makes maximal sharing hard).
- **Merge can become inference.** Two pieces individually in normal form, composed,
  reduce to a *new* fact neither held — accumulation producing new knowledge, when
  the pieces share an interface.

The isolated open problem is **labeling**, and we tested it (`incrdt4.py`). When N
replicas independently derive the *same* computation with *different* duplication
labels, label-sensitive content-addressing loses the sharing entirely — idempotence
breaks across replicas, `merge(A,A')` paying twice for one computation. But
**label-canonical** content-addressing (alpha-renaming labels by first encounter)
recovers it: the differently-labeled replicas are detected as one computation, reduced
once, the cost goes nearly constant (recovered up to 4.8× at N=6), and the normal form
is unchanged at every N. So canonicalization is most of the *solution*, not just the
problem — the loss is catastrophic without it and soundly recovered with it. The
residual is narrower than "labeling": a **globally collision-free canonical labeling**
(canonical for matching, fresh-on-copy for soundness, since canonicalizing distinct
computations into overlapping label ranges can trigger spurious duplication
annihilation), which is the exact analogue of de Bruijn naming plus freshening for
variables, and the same canonical-form-under-confluent-rewriting problem that
**e-graphs / equality saturation** solve in their setting. Cost-wise this is
encouraging: recognizing a duplicate computation is *structural* canonicalization,
O(n) with hash-consing (paid once per distinct computation on insert), and measures as
a net win even with a naive O(n²) prototype; the genuine remaining difficulty is one
tier up — *semantic* identity (same function, different derivation), which is
undecidable and is exactly the tier equality saturation approximates. We probed that
tier too (`incrdt6.py`): a minimal e-graph with a church-arithmetic ruleset and
congruence closure recognizes `church(6) ≡ mult(church2,church3) ≡ …` *without
evaluating them*, in a handful of rewrite firings versus the interactions it would
take to reduce them — semantic identity recognized by rewriting, not reduction. The
honest residual: that works because the algebra's rules were supplied (program
equivalence has no finite complete ruleset, so saturation is inherently a
semi-procedure), and the e-graph reasoned over a symbolic abstraction rather than the
raw terms (saturation directly over interaction-calculus terms needs binders in the
e-graph — the known-hard "e-graphs with binders" problem). We then carried that binder
problem forward. `incrdt7.py` puts an e-graph directly on de Bruijn lambda terms with
beta and eta, closing the binder case for pure lambda (alpha-equivalence free; eta even
finds equalities reduction alone cannot). `idtest.py` settled which way to go next: three
terms with identical normal forms but different derivations (`church(6)`, `mult(2,3)`,
`mult(3,2)`) give three distinct canonical keys before reduction and coincide only at
full reduction, so the identity layer is a *syntactic* congruence (alpha + label
renaming) — the route to semantic identity is e-graphs, not better canonicalization.
`iceg.py` builds that IC-aware e-graph: e-node identity is de Bruijn over both lambda
*and* dup binders plus label renaming (so the same computation across label namespaces is
one e-class for free, dups and all), and a church-arithmetic rule plus congruence
recognizes `mult(2,3) ≡ church(6)` on the real dup-bearing terms, across namespaces, in
one firing versus sixteen interactions — verified sound against `ic_float`, merging
exactly the normal-form-equal pairs and no others. This lifts both the cheap recognition
and the binder handling onto interaction-calculus terms. The residual narrows but does
not vanish: the rule is the supplied algebra (program equivalence has no finite complete
ruleset), numerals are matched via a finite canonical-key table, and the
substitution-heavy interaction rules — full reduction inside the e-graph, the
slotted-e-graph problem — remain open. We then took the first step on that problem
(`slotted.py`): a slotted-style e-graph whose e-class identity is the slotted canonical
form — bound variables de Bruijn, free variables positional slots, labels renumbered —
which gives the open-subterm sharing the de Bruijn key cannot (the subterm `λy.(x y)`, and
the dup-bearing `!&L{a,b}=x;(a b)`, are one e-class in any context, where de Bruijn assigns
them context-dependent indices), and which runs beta *inside* the e-graph so that
`mult(2,3) ≡ church(6)` is recognized by actual reduction — removing the finite key table
and the supplied algebra that `iceg` had leaned on. We then took the next step on the IC
side (`slotted_ic.py`): the IC *interaction* rules as slotted rewrites over dup/sup-bearing
terms. Six of the rule types now reduce inside the e-graph and validate normal-form-equal to
`ic_float` on an eight-term battery — APP-LAM, APP-SUP, APP-ERA, DUP-SUP annihilation, DUP-SUP
commute (different labels), and DUP-ERA — including the fresh-variable-generating APP-SUP and
DUP-SUP-commute. The sharp finding is that fresh-variable generation is *not* the obstacle; the
single rule that cannot be expressed in a lexical reducer is DUP-LAM, because the two copies of
a duplicated lambda must share its bound variable through a superposition — an interaction-net
wire that capture-avoiding substitution is obliged to rename away. That one rule needs net
wiring or explicit substitution (the reason HVM does not use lexical substitution), and the
full *dynamic* slotted e-graph (slots through e-class merges, congruence modulo renaming,
equality saturation — the `slotted` library, PLDI 2025) remains. So the undecidable core
relocates into ruleset curation and that one remaining binder/substitution problem, now
materially advanced from both the lambda and the interaction-rule sides. What
is demonstrated, then, is best named **structurally (and, relative to a
ruleset, semantically) content-addressed computation with confluent merge**. The
realized object is a replicated *computational* structure — agent memories, theorem corpora, planning
graphs, world models, merged across nodes with no coordination and each reduced once
— which is precisely the persistent substrate the broader stack ("intelligence is
structured accumulation, not generation") is built around. That, rather than faster
reduction, is where a result distinctly beyond existing interaction-net work would
live. A capstone (`compmem.py`) assembles these pieces into one running artifact — a
content-addressed store of computations whose merge is a confluent CRDT (commutative,
associative, idempotent), where structural identity dedupes and shares reduction for
free, and different derivations of the same value collapse to a single fact — i.e. the
substrate itself, in miniature, coordination-free. A further capstone (`compmem_ic.py`)
puts that store on the real optimal-sharing runtime: the canonical key handles lambda
*and* dup binders plus labels, so the same computation on different machines collapses;
the CRDT laws hold; within-computation sharing (`ic32`'s optimal reduction) composes with
cross-computation dedup; and parity of 2²⁴ — value 16,777,216, reduced in 478
interactions — is stored once, not twice, across machines, unifying the runtime spine
with the merge thread.

Finally, the thread is closed with a formal statement (`semilattice.py`): the state — a
grow-only set of computations content-addressed by *normal form*, merged by union — is a
join-semilattice (union is idempotent, commutative, associative, and is the least upper bound),
its updates are inflationary (reduction adds a normal form and never removes one), and so, by
Shapiro, Preguiça, Baquero & Zawirski (2011), it is a state-based CRDT enjoying strong eventual
consistency, verified across two hundred shuffled-order trials that all converge to the same
join. Because the content-id is the normal form, that convergence performs *semantic*
deduplication. This is Shapiro's theorem *instantiated on the computation object*, not a new
CRDT theorem — the novelty is the object and the dedup it yields — but it turns the rest of the
IN-CRDT thread into corollaries: each `incrdt*.py` / `compmem*.py` experiment is an instance of
this semilattice, `dist_ic.py`'s coordination-freedom is its strong eventual consistency, and
the e-graph line (`iceg` / `slotted` / `slotted_ic`) refines the content-id from structural to
semantic while extending the same monotone structure — equalities as a grow-only set, merges
never undone — to partial, non-normalizing computation.

---

*All claims in this paper correspond to runnable, self-validating artifacts in the
accompanying bundle. See `README.md` for the file map and how to reproduce each
result.*
