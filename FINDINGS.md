# TRVM — Findings and Synthesis

*The legible entry point. Read this first. For the runtime in detail see `spec/paper.md`; for the
identity/memory thread see `research/INCRDT.md`; for prior-art boundaries see `spec/RELATED_WORK.md`;
for the per-file index and reproduction commands see `README.md`.*

---

## What this is

A coordination-free **computational-memory substrate** built on an interaction-calculus runtime.

The intellectual center is deliberately *not* the runtime. Interaction nets are Lafont 1989, and
optimal sharing is Lamping/Lévy; a from-scratch reimplementation of them is table stakes, not a
result. What sits on top is the contribution: a way to give running computations **canonical
identities**, **content-address** them, and **merge replicas without coordination**. In that
framing the runtime is the evaluation engine *for the memory*, not the headline.

This document states three things, because the second and third are as much the contribution as
the first:

1. what was **demonstrated**,
2. what was **investigated and falsified** (the sequence of negative results), and
3. what is **honestly open**.

The through-line is a method — *measure before theorizing* — and across this project the cheap
measurement was, every single time, more informative than the narrative it replaced.

---

## The arc that survived

Every speculative extension was measured. Most were narrowed or cut (see the falsification table
below). One spine survived every measurement:

> **Confluence → Canonical computational identity → Content-addressed computation →
> Coordination-free computational memory**

- **Confluence.** Interaction calculus (like the λ-calculus) is confluent: reduction order does
  not change the normal form. This is the foundation everything else stands on — it is what makes
  a computation's *result* a well-defined object independent of how it was evaluated. *(Lafont
  1989; exercised throughout — `ic_ref.py` is the oracle, `dist_ic.py` confirms 480 distributed
  runs equal the single-node result.)*

- **Canonical computational identity.** Given confluence, a computation can be assigned a
  canonical identity. There is a spectrum: **structural** identity (alpha- and label-canonical,
  computed with *zero* reduction) at one end, **semantic** identity (the normal form) at the
  other. `compmem_ic.py`'s `ic_canon = canon(label_renumber(parse_tree(src)))` is the structural
  layer, and it is **load-bearing** — it is where the real work happens. *(`compmem_ic.py`,
  `slotted.py`.)*

- **Content-addressed computation.** Address a computation by its canonical identity. Two
  syntactically different computations with the same identity get the same address. This is
  Unison's idea — content-addressing code — pushed from syntactic toward *semantic* identity.
  *(`compmem.py`, `compmem_ic.py`.)*

- **Coordination-free computational memory.** A replicated, grow-only store of content-addressed
  computations: merge is set **union**, which forms a join-semilattice, hence a CvRDT — replicas
  converge without coordination. *(`semilattice.py` verifies the lattice laws, semantic dedup,
  inflationarity, and strong eventual consistency over 200 trials.)*

**The precise claim.** The strongest sentence in earlier drafts — *"the merge of confluent
computation is a CvRDT by construction"* — hid where the work was being done. The honest, and
paradoxically stronger, statement is:

> **canonicalize → content-address → union → reduce**

The semilattice does not appear from computation alone; it appears from computation **plus a
canonical identity layer**. The win is not *avoiding* reduction but **sharing and remembering**
it. This is Shapiro 2011 (CvRDTs) *instantiated on a new object* (computations, deduplicated
semantically), not a new theorem.

---

## What is demonstrated

| Claim | Status | Evidence |
|---|---|---|
| A correct, self-validating IC runtime (packed-word native) | **Demonstrated** — 13/13 self-tests, fully iterative parse/normalize/readback, depth-robust to 500k+, ~22–34M interactions/s | `ic32.c --test`; `paper.md §4` |
| Church arithmetic incl. exponentiation reduces correctly | **Demonstrated** — given the labeling discipline a compiler supplies (linear numerals, distinct labels) | `ic32.c --test`; `ic_float.py` oracle (23 terms agree with `ic_ref`) |
| Coordination-free distributed reduction is *correct* | **Demonstrated** — 480 runs (20 terms × 24 configs) byte-identical to single-node | `dist_ic.py` |
| Distributed reduction is *faster* (wall-clock) | **Not demonstrated** — no speedup at toy scale on a single core (hardware-bound, not a design claim) | `swarm.js`, `dist_real.py` |
| Computational memory saves work | **Demonstrated, modest** — semantic dedup of results at the normal form + ~18% memoization across a corpus | `dedup_reduce.py`, `compmem_ic.py` |
| Canonical computational identity is the load-bearing layer | **Demonstrated** — structural identity is free; semantic identity is content-addressable at the normal form | `compmem_ic.py`, `slotted.py` |
| Merge of computations is a CvRDT (precisely: canonicalize→address→union→reduce) | **Demonstrated** — lattice laws + SEC verified, 200 trials | `semilattice.py` |

---

## What was investigated and falsified

This table is a first-class result. The literature is full of papers that stop at an *interesting
witness* and extrapolate to a *general phenomenon*. This project repeatedly did the opposite —
witness → distribution → boundary condition — and reported the boundary even when it deflated the
story.

| Hypothesis | Measurement | Result |
|---|---|---|
| Distributed reduction yields practical speedup | `swarm.js`, single core | **No** — correctness yes, wall-clock speedup no |
| A runtime implies a *theorem* (new CRDT / new result) | prior-art map | **No** — synthesis, not a theorem (`RELATED_WORK.md`) |
| Semantic identity is recognizable *before* reduction | `dedup_reduce.py` | **Partly** — only *structural* identity is free; semantic identity costs ≤ normalization, recognized at the first shared form, which is sometimes intermediate but usually the normal form |
| Early trajectory convergence is common (a major source of sharing) | `convergence_map.py`, 578 pairs | **No** — World 1: ~6% converge before the normal form (8% under call-by-value), the deepest being a single algebraic family `add(k,k) ≡ mul(2,k)` |
| IC's optimal sharing creates convergence that beta hides | `ic_convergence.py` | **Not cleanly measurable** — the measurement failed its sanity check; faithfully canonicalizing partial IC states is itself the open problem (see *circularity* below). Beta stays World 1; IC is plausibly-but-unproven World 1 |
| The IC runtime mis-duplicates dup-bearing lambdas (a reduction "bug") | pure-beta ground truth + reading `lc2.py` | **No bug** — the failing tests were mis-encoded; the runtime is correct and the discipline is the input's (`paper.md §4`) |
| Label namespace divergence is fatal to replicated computation | `incrdt*.py` | **No** — canonicalization recovers it; a catastrophic/full-recovery phase transition, not a wall |

**The circularity (the most interesting negative).** The IC convergence closure test could not
be answered cleanly, and *why* is the finding: to measure rigorously whether a dynamic slotted
e-graph is worth building, you need e-graph-grade canonical identity for **partial** IC states
(open subterms, floating dups, label namespaces) — the very machinery you'd be deciding whether
to build. The cheap experiment ran into the thing it was trying to evaluate. Net effect: the
e-graph build is **not justified** — both because beta is World 1 and because the question can't
even be posed without first paying for the answer.

---

## What is novel — and what is not

Stated plainly to avoid over-claiming:

**Not novel.** The interaction-net runtime (Lafont 1989). Optimal sharing (Lamping/Lévy).
Coordination-free reduction *as a consequence of confluence* (foundational, not new). CvRDTs and
the union semilattice (Shapiro 2011). Content addressing of code (Unison). E-graphs and slotted
e-graphs (egg; PLDI 2025). **None of the components is a new theorem.**

**The contribution is the synthesis** — and within it, two things are genuinely the project's own:

1. The **object**: treating a *computation* (content-addressed by semantic identity) as the
   element of a CvRDT, so that *merging confluent computation* is coordination-free by
   construction once the canonical identity layer is in place.
2. The **measured map** of where that works: structural identity is free; semantic identity costs
   ≈ normalization; early convergence is rare (World 1); the substrate's value is sharing and
   remembering reduction, not avoiding it. Most of this is *negative* knowledge, and it is sharp.

---

## The method is the through-line

The most transferable thing here is not the runtime or the memory. It is the discipline:

- **Measure before theorizing.** Every exciting direction was given a cheap experiment before any
  machinery was built. Distributed speedup, semantic-identity-before-reduction, trajectory
  convergence, the reduction "bug," the label catastrophe — each narrative met a measurement, and
  the measurement won.
- **A failed sanity check is a result, not an embarrassment.** The IC convergence test offered two
  publishable-looking numbers (55% and 2%); a sanity check built to catch exactly this rejected
  both. Reporting the blockage — and finding the circularity behind it — was worth more than either
  number would have been.
- **Narrow, don't abandon.** The project was never systematically *wrong*; it was systematically
  *narrowed*. Each measurement turned a big claim into a smaller, stronger one. The arc that
  survived is small, but it survived everything.

---

## Honest limits / standing gaps

- **Garbage collection — Phases 1–2.** `ic32.c` recycles consumed redex nodes via size-classed
  free lists (Phase 1: a redex is dead the instant its rule fires — local + confluent, so no
  tracing and no pauses; measured 33–40% lower heap high-water on dup-heavy reduction,
  `./ic32 --gcstats`). Phase 2 adds eraser **propagation**: `APP-ERA` now collects the discarded
  sub-net — `./ic32 --erasestats` shows a directly-erased 2000-deep spine drop from 4002 live
  slots to 2. The 13/13 self-test (incl. the 500k-deep stress) is unchanged throughout.
  **Measured limit (a finding neither obvious nor predicted):** under *lazy* reduction the
  discarded thing is usually an unevaluated *variable binding*, not built structure, so it sits in
  a binder slot that eraser propagation can't reach — the var-indirect and affine-unused cases do
  not reclaim. Closing those needs substitution-aware reclamation (free a binder once its variable
  is provably dead) or compiler-inserted erasers (wire discarded variables to `*` so the eraser
  meets real structure) — front-end / bookkeeping work, still no tracing collector. The ERA-DUP
  dup-projection case is the one remaining runtime rule. Net: an interaction calculus really does
  mostly manage its own memory, and what's left is precisely characterized rather than hand-waved.
- **Single core.** The sandbox has one CPU, so wall-clock parallel speedup cannot be demonstrated;
  the distributed claims are *correctness* claims only.
- **IC convergence is blocked, not closed by a number.** See the circularity above.
- **`slotted_ic.py` DUP-LAM holdout.** Duplicating a lambda shares its bound variable through a
  superposition wire that lexical capture-avoidance must rename away — the open-term-identity
  problem. The *runtime* handles this fine (via net wiring / labels); the *lexical-rewrite*
  formulation does not. The two are related but the runtime is on the right side of the line.
- **Novelty is bounded to synthesis.** No component is a new theorem; the value is the object plus
  the measured map.

---

## Map to the artifacts

**Runtime spine (the evaluation engine).**
`ic_ref.py` (oracle) → `ic_float.py` (floating-dup reducer; opt-in interaction `BUDGET`, default
off) → `ic32.c` (packed-word native, iterative, self-validating, GC-less) →
`ic32_wasm.c`/`wrun.js` (freestanding wasm32) → `dist_ic.py`/`dist_real.py`/`swarm.js`
(coordination-free distributed reduction: correct, no toy-scale speedup).

**Identity / memory spine (the result).**
`incrdt*.py` (the IN-CRDT thread) → `compmem.py`/`compmem_ic.py` (replicated content-addressed
computational memory; `ic_canon` is the load-bearing structural-identity layer) →
`semilattice.py` (merge-is-a-CvRDT, precisely stated, laws verified) → `dedup_reduce.py`
(identity-recognition budget) → `convergence_map.py` (early-convergence distribution, World 1) →
`ic_convergence.py` (IC closure test — documented **negative/blocked** result + the circularity).
Supporting: `slotted.py`/`slotted_ic.py` (slotted e-graph for λ/IC; DUP-LAM holdout), `iceg.py`
(IC-aware e-graph, limits noted), `tiers.py`/`frontier.py` (tiered identity).

**Documents.**
`paper.md` (the runtime, in full) · `INCRDT.md` (the identity/memory thread, in full) ·
`RELATED_WORK.md` (prior-art boundaries) · `README.md` (per-file index + reproduction) · this file
(the synthesis).

---

*Reproduce the load-bearing checks from a clean checkout (or just `make test`):*
`gcc -O2 -o runtime/c/ic32 runtime/c/ic32.c && runtime/c/ic32 --test` *(13/13)* ·
`python3 runtime/python/ic_float.py` *(23 terms agree)* ·
`PYTHONPATH=runtime/python:research python3 research/semilattice.py` *(ALL CONDITIONS HOLD)* ·
`PYTHONPATH=runtime/python:research python3 research/convergence_map.py` *(World 1)* ·
`PYTHONPATH=runtime/python:research python3 research/ic_convergence.py` *(reports itself blocked, honestly)*.
