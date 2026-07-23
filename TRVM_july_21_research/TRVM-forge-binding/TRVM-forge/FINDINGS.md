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

---

# Addendum 2026-07-11: distributed computational memory, compositional synthesis

Provenance: sandboxed research session (1 core; distribution = real OS processes
where stated, simulated otherwise). Five external adversarial review cycles;
several of this addendum's claims exist because a reviewer falsified their
predecessors. Every claim carries its test. Files under research/; repro
commands at the end.

## A. Computational memory at swarm scale (supgen_swarm{,2,3}.py)

- CAPTURE, not hit-rate: with shared canonical memory at K=8, capture
  efficiency eta = (solo-shared)/(solo-floor) = 97.0-99.6% across three shard
  localities (round-robin / contiguous / value-sorted; cost-multiplicity 5.04 /
  3.17 / 1.79). "savings = (m-1)/m" is algebraic once shared~floor; eta is the
  honest metric. [swarm2 A]
- CADENCE LAW: overhead is merge-cadence-dependent and width-independent.
  Corrected cadence (merge every 16 candidates, enforced per candidate):
  1.10-1.11x floor, flat K=8..512. The apparent 3.56x degradation at K=512 was
  a harness artifact (merge check outside the per-node loop => effective
  cadence "every K"). Synchronous bound = 1.00x. [swarm3 K]
- ASYNC CALM: value-closure search with no barriers, per-node rates, gossip
  latency U(1,L) for L in {2,10,40}, 20% duplication, 15% loss, anti-entropy:
  18/18 runs reach the same least fixed point ({1..100} under cap); replicas
  agree; trajectories genuinely distinct. Unowned duplication overhead is
  governed by K (155-177% at K=4; 656-830% at K=16), ~flat in L. [swarm3 ASYNC]
- OWNERSHIP: hash self-assignment of tasks (SPEC 4.3's owner rule applied to
  work) => 0.0% duplicated evaluations at K=16 under the same faults, still
  zero coordination messages. Latency's price converts from duplicated work to
  idle time. [swarm3 OWNED]
- SHARING ENABLES PRUNING: matched-coverage 2x2 (interactions to cover the
  exhaustive 64-value frontier): pruned+shared+owned 5,478 < exhaustive floor
  6,500 < pruned single-node 10,820 < exhaustive unshared 32,775 < pruned
  unshared 86,560. Shared owned pruning was cheapest; independent pruning was
  the most expensive measured condition. Value-space pruning loses without
  the shared frontier and beats the deduplicated floor with it. At evaluation time, pruning and
  memoization are substitutes (predicted multiplicative compounding:
  falsified). [swarm3 2x2; swarm2 B]
- ECONOMICS, three baselines (measured): cheap structural-key local memo
  0.07us vs p_total*C_red 53.6us -> pays; canonical-key shared vs cheap-key
  local: 38.9us vs p_cross*C_red 33.1us -> loses at ~7-interaction grain
  (python); shared vs no-memo pays. Native (ic32 ~28M i/s) break-even:
  ~1,782 interactions/task with string canonicalization; ~3 with carried
  recipe ids. Carried identity is a prerequisite for fine-grained memory, not
  an optimization. [swarm3 E3]

## B. Wire format (permanent regression)

Printed normal forms are not a semantics-preserving serialization for
nonlinear graphs. AND(x,x)'s NF renders its dup as a repeated variable
occurrence; re-parsing diverges (recursion blowup) though the dup-explicit
source evaluates correctly. Rule adopted everywhere since: NF strings are
TERMINAL artifacts (decode-only, never re-parsed into programs); program
transport is AST/source level. Regression vectors pinned in synth_bool3/4
LAWS. Real stores must ship dup-explicit graphs or carried ids.

## C. Synthesis ladder (synth_bool{,2,3,4}.py + synth_worker4.py)

- v1 REPLAY AMORTIZATION: Boolean synthesis on the substrate (every candidate
  a real IC term; behaviors = full truth tables). Accumulating store: L2
  A/B/C = 215,048 / 26,881 / 12,673 interactions; after XOR all 16/16
  2-input behaviors witnessed, remaining specs solved by frontier lookup at
  zero cost. Mechanism (externally verified over 20 randomized curricula):
  C pays for the deepest needed prefix of a deterministic candidate stream,
  order-invariantly. Cross-arity memo transfer measured exactly zero.
  Components-applied-to-variables: net loss (breadth tax) -- first
  compositional claim honestly failed.
- v2 TYPED IDENTITY IS LOAD-BEARING: arity-less program ids leaked 2-input
  signatures into 3-input searches and corrupted rep frontiers (C failed
  MAJ3 where fresh-store B passed). Fix: identity = hash(semver, type
  descriptor, canonical AST). First compositional certificate: XOR3 as
  nested AP references to the learned XOR, unreachable raw within budget.
- v3 SCHEDULE INDEPENDENCE, SPLIT: semantic determinism (preferred maps) is a
  property of the lattice + deterministic candidate language; economic
  determinism additionally depends on visibility cadence (in-flight window).
  L2: both hold exactly for K in {1..16}, shuffled folds. Preferences are
  DERIVED from ProgramRecords (ref, exp, intrinsic cost, pid), never stored
  in BehaviorRecords -- eliminates stale duplicated state. Intrinsic vs
  marginal cost recorded separately. Layered identity effect: expansion-
  identical, structurally distinct programs share evaluation records
  (modular identity above, canonical computation identity below).
- v4/v4.1 CROSS-PROCESS MILESTONE: 4 real OS worker processes; the only
  cross-boundary state is canonical-JSON semilattice deltas over pipes;
  children independently regenerate their owned candidate slices from
  serialized state; merge-on-arrival under genuine OS completion order, with
  sorted-remerge asserted equal (join laws demonstrated under real
  nondeterminism). FULL canonical four-store state (program / behavior /
  evaluation / context) asserted identical to a matched in-process run:
  425,895 paid / 4,425 novel, both sides. Same content-addressed XOR3
  witness as in-process. Certificates mechanical: witness-pid absence from
  each component-producing task's classified set, grammar-lacked-AP,
  transitive dependency walk, AP-free-witness existence -- all checked
  against the store. Hardened imports recompute type/ref/exp/deps, verify
  referential integrity, and reconstruct cost_i from imported evaluation
  records (structurally linked); forged ref/exp/cost_i/type/fake-dep/
  dangling-alt all rejected.
- v4.2 PROTOCOL INTEGRITY: workers submit observations, not authority.
  Behavior associations are checked against signatures DERIVED from imported
  evaluations (false associations rejected); imported evaluations are
  re-executed on a seeded sample and must match in normal form and cost
  (forged results caught); provenance and search contexts are stamped from
  orchestrator job manifests, never taken from worker claims (the stamping
  immediately surfaced a real claim/manifest divergence: the child's
  hardcoded max_size). MP budgets check post-level; solution levels complete
  with a one-level reserve, overrun reported. Accurate label:
  trusted-orchestrator, structurally validated, spot-verified cross-process
  synthesis. Redundant/trace-based verification, signatures, and
  decentralized manifests remain open.
- v4.3 AUTHORITY REMOVAL: workers supply candidate reductions, all fully
  re-verified at Boolean scale (p=1.0
  re-execution of every imported evaluation; a guaranteed minimum one
  unpredictable check per program exists for sampled modes). Behavior
  associations are verified for EVERY alternative, delta-side or
  receiver-resident (the sigmap gap); cost_i=INF marks a program unverified:
  admissible to ProgramStore, excluded from behavior records and preference
  (the INF bypass); classified sets, ownership, level membership, novel
  counts, paid totals, and per-program marginal costs are DERIVED by the
  orchestrator from its own candidate stream and verified evaluations --
  eighteen forgery classes rejected in the LAWS battery, honest deltas
  derive to exactly equal accounting. Protocol validation raises
  InvalidDelta (assert vanishes under python -O). Deltas ship
  value-changed records, not merely unseen keys (a latent async bug).
  Milestone unchanged under all of it: same witnesses, full four-store
  equality, 425,895/4,425 both sides.
- v4.4 OMISSION REMOVAL + PROTOCOL FREEZE: the review demonstrated workers
  retained NEGATIVE authority (suppress a true behavior; withhold a program
  record; forge or suppress the solution signal; claim another connection's
  identity) and that Law 13 preceded its implementation by one release (only
  behavior deltas were value-compared). Closed: behavior records are
  RECEIVER-DERIVED from verified programs and evaluations (worker records are
  hints, verified then replaced); solution existence is read off the verified
  lattice, never a reply field; each connection is bound to its assigned
  worker index with exactly one reply required per owner; slice completeness
  is checked both directions against the level-start snapshot (withholding a
  discovered program is detectable); value-changed deltas now ship for all
  four stores; timeouts and payload caps added. Twenty forgery/omission
  classes rejected in LAWS; milestone still byte-identical.
  VERIFICATION ECONOMICS, measured (reviewer first, reproduced to the digit;
  benchmark scope, cap probe reported separately as a regression):
  worker-paid 425,895; verifier re-execution 556,426; unique canonical
  computation 328,730; total physical reduction 982,321 (~2.31x
  worker-paid). v4.x demonstrates SECURE ACCEPTANCE UNDER FULL RE-EXECUTION,
  not useful outsourcing of computation.
- v4.5 FINAL SYNCHRONOUS PATCH: the review found the mirror of the
  program-omission channel -- "the receiver derives exactly which programs a
  worker owes, but not yet exactly which evaluation records those programs
  entail." An injected unrelated evaluation (cost -999, forged provenance)
  was accepted and stamped legitimate. Closed: the expected evaluation-key
  delta is derived from the owned programs' verification keys against the
  level-start snapshot and required exactly (injection, omission, and
  duplicate-accounting all rejected); evaluation costs must parse as
  nonnegative integers. Two more findings closed with it: the quarantine
  model had no exit (an INF program upgraded to verified was rejected as
  excess -- expected results are now those NEW OR AWAITING UPGRADE, with
  novel/upgrade accounting split), and an INF result for an assigned
  candidate crashed accounting with a raw KeyError -- now Policy A: assigned
  work returns verified finite results or is rejected as InvalidDelta.
  Law 13 is true orchestrator-to-worker; worker-to-orchestrator updates of
  existing records are limited to the promotion path -- candidate
  completeness and fact updates are DISTINCT protocol channels and must not
  share one set-equality rule (pre-async requirement). Hostile-network
  transport (length-prefixed framing, pre-allocation limits, per-worker
  error isolation) is documented future work; local processes unaffected.
  THE SYNCHRONOUS PROTOCOL IS FROZEN AT v4.5. Remaining boundary:
  verification asymmetry (traces, redundancy, stakes), network
  identity/signatures, unresponsive-worker liveness.

## D. Falsification table (additions)

| claim | test | status |
|---|---|---|
| shared memory pins swarm cost to floor | K sweep, corrected cadence | CONDITIONAL: cadence-dependent, width-independent to K=512 |
| savings track demand multiplicity | 3 shardings, exact solo | partly algebraic; use capture eta (97-99.6%) |
| pruning x memoization compound multiplicatively | sync pruning x-hit | FALSIFIED: substitutes at eval time; sharing is pruning's enabler |
| frontier schedule-independent (async) | 18 fault-injected runs | HOLDS: same lfp, distinct trajectories |
| unowned async propagation outruns rediscovery | latency sweep | FALSIFIED at K>=4: 155-830% dup; ownership -> 0.0% |
| string identity pays vs python | 3-leg measurement | SPLIT: pays vs no-memo; loses vs cheap-key local at small grain |
| carried ids repair economics | measured key cost | SUPPORTED: break-even ~1,800 -> ~3 interactions |
| printed NF round-trips | AND(x,x) vector | FALSIFIED: NFs are terminal artifacts |
| cross-task learning = C beats B | A/B/C ladders | HOLDS within arity (replay); zero cross-arity memo |
| components-over-variables help | matched B/C/C+ | FALSIFIED: breadth tax, no compression of MAJ3 |
| untyped structural pid suffices | v2 cross-arity run | FALSIFIED: corrupted frontiers; type in identity |
| compositional transfer achievable | v2-4 certificates | HOLDS: XOR3 via referenced XOR; no raw witness in the accumulated store; mechanical checks |
| active search schedule-independent | v3 battery + reviewer perturbation | HOLDS after derived-preference fix; economic invariance cadence-bounded |
| MP == IP at matched cadence | four-store canonical compare | HOLDS exactly (asserted) |
| async synthesis is "pure wiring" | reviewer analysis | RETRACTED: monotone facts replicate; schedules derive locally |
| divergent stale schedules purchase coverage (16/16 vs canonical 14/16) | depth-instrumented CONV rerun | FALSIFIED: memo-key bug -- Node.refill() regen stamp was depth-blind, skipped the size-8 band; XOR/XNOR build from single reps at size 8 |
| canonical single schedule reaches full behavior coverage (2-input, size<=8) | fixed CONV, seed sweep | HOLDS: deterministic 16/16 = all 16 two-input functions, (16,134 / 280) == [synth_bool4 DET] cross-engine, pid-for-pid (16/16 is the Boolean-function ceiling for this experiment, not a completeness ceiling for programs) |
| async divergence changes final behavior coverage (either direction) | 6 configs saturated + resume probe + autonomous probe 40/40 | FALSIFIED both ways: coverage reaches 16/16 in all tested configs (autonomously robust); the one 15/16 was a harness artifact (coverage read before the enriched frontier closed), resumes to 16/16. "All tested configs", not proven schedule-invariance |
| divergence buys implementation multiplicity as a BENEFIT | preferred-rep quality across configs | HALF-FALSIFIED: the multiplicity is real (280 canonical; healthy N=4 346-399; faults 427-508; not nested) but NOT a demonstrated benefit -- of the preferred reps that differ from canonical, none is strictly better in (ref, exp, cost); they differ only by hash tie-break |
| autonomous nodes AGREE under faults (deterministically) | remove the saturation oracle, run pairwise gossip only | REFINED: per-replica coverage-closure is autonomous and robust (32/32 no-partition battery, per-node asserted -- the earlier "40/40" read node 0 only and included a mislabeled partition row), but fact agreement at a stability stop is eventual (31/32; the miss agrees after 43 ticks of continued gossip). Deterministic agreement was manufactured by the oracle |
| non-agreeing stops are due to messages in flight | inbox inspection at both misses | FALSIFIED mechanism: inboxes were EMPTY [0,0,0,0]; the differing facts sat in one replica's store ([325,321,321,323] / [351,351,351,348] programs) awaiting a FUTURE random anti-entropy pairing; continued ordinary gossip agreed in 6 and 43 ticks |
| the autonomous "partition" row tested partition recovery | stop-tick audit vs partition window | INVALID TEST: partition (2,300,900) vs stops at ticks 238-318 -- 7/8 runs ended before the partition began, none saw healing; it measured no-partition dynamics under a partition label. Law 26 |
| the protocol recovers autonomously after a partition heals | staged-healing probe: partition asserted to bite (isolated node 14-15/16 at heal), then unchanged protocol | HOLDS: full per-replica coverage in median 31-38 ticks post-heal, fact agreement median ~91 (max 212), across 3 windows x 8 seeds; the stability heuristic often fires BEFORE agreement (1/8 to 8/8 by window), consistent with the eventual-agreement finding |
| semantic recognition requires synchronized evidence histories | layered agreement at the heuristic stop | FALSIFIED: signature-set agreement 32/32 and preferred-map agreement 32/32 while fact-store agreement 31/32 -- replicas recognized identical behaviors and identical preferred representatives while holding different implementation-fact collections |
| restart divergence % is valid as reported | counter audit | FALSIFIED then fixed: restore() zeroed paid/vpaid, so dup=worker-unique went negative (-6,238); run-level carried counters restore it, dup>=0 by construction |

## E. Design laws distilled

1. Report capture efficiency, not hit rates.
2. Overhead follows propagation cadence, not swarm width (both layers).
3. Ownership is day-one architecture: hash self-assignment, zero messages.
4. Carried canonical identity is a prerequisite at native grain.
5. Normal forms are terminal artifacts; never re-parse them.
6. Identities are layered (program / computation / behavior) and typed.
7. All shared records are join-semilattices; preferences are derived on
   demand from monotone facts, never stored beside them.
8. Deltas verify against the receiver's environment; verification is a
   post-parse phase (two placement bugs earned this sentence).
9. Budgets are vectors; solution-bearing levels run to completion.
10. For async synthesis: replicate immutable facts (programs, behaviors,
    evaluations, contexts); derive representative choices, queues, and
    priorities locally. Known-behavior sets are monotone; the generating
    schedule is not.
11. Workers submit observations, not authority: behavior facts derive from
    evaluations; evaluation claims are re-executed; provenance is a claim
    until a manifest or signature grounds it; accounting is derived from the
    orchestrator's own stream, never read from replies.
12. Protocol validation raises explicit errors; assert is for internal
    impossibilities only (it vanishes under python -O).
13. State-based deltas transmit changed record VALUES, not merely unseen
    keys -- semilattice fields grow under existing keys.
14. Derive accounting against the snapshot the worker actually saw, not the
    receiver's mid-merge state (earlier-arriving siblings otherwise make
    honest payments look forged).
15. Closing positive authority is half the problem: omission is authority
    too. Any fact the receiver can derive (behaviors, solutions, coverage),
    it must derive -- workers can then withhold only labor, never knowledge.
16. Account work four ways -- worker-paid, verifier, unique canonical, total
    physical -- and never present worker-paid as system cost while
    verification re-executes. Keep benchmark and regression scopes separate.
17. Completeness rules must cover every store symmetrically; closing one
    store's omission channel spotlights its neighbor's.
18. Quarantined facts need explicit promotion paths: a lattice bottom (INF)
    without an upgrade rule is a trap, and the upgrade must survive the
    completeness checks that guard against omission.
19. Candidate completeness and fact updates are distinct protocol channels;
    one set-equality rule cannot serve both.

## F. Repro

    make test
    PYTHONPATH=runtime/python:research python3 research/supgen_swarm.py
    PYTHONPATH=runtime/python:research python3 research/supgen_swarm2.py
    PYTHONPATH=runtime/python:research python3 research/supgen_swarm3.py K
    PYTHONPATH=runtime/python:research python3 research/supgen_swarm3.py ASYNC 2
    PYTHONPATH=runtime/python:research python3 research/supgen_swarm3.py OWNED 2 10
    PYTHONPATH=runtime/python:research python3 research/supgen_swarm3.py AB E3
    PYTHONPATH=runtime/python:research python3 research/synth_bool.py SELFTEST L2
    PYTHONPATH=runtime/python:research python3 research/synth_bool2.py L3 B C CP
    PYTHONPATH=runtime/python:research python3 research/synth_bool3.py LAWS DET
    PYTHONPATH=runtime/python:research python3 research/synth_bool3.py L3 B C CP
    PYTHONPATH=runtime/python:research python3 research/synth_bool4.py LAWS DET
    PYTHONPATH=runtime/python:research python3 research/synth_bool4.py MP

Open: Pareto representatives + cost-guided enumeration; runtime REF linking
(AP still macro-expands at compile); asynchronous process synthesis per law
10; normative wire encoding (RFC 8785 / canonical CBOR) so content identity
never depends on host-language serialization; verification asymmetry
(traces, redundant execution, or stakes so checking costs less than doing);
signatures and decentralized manifests; heterogeneous-backend result-id
comparison (printed NFs are evaluator-scoped).

## G. Asynchronous autonomous synthesis (synth_async.py)

No central controller. Each node: replicated monotone facts (programs,
versioned evaluations, verification marks), locally derived everything else
(behaviors, preferred reps, queue, depth). Quarantine+promotion handles
structure and evidence arriving in any order. All replicated state crosses a
JSON serialization boundary per message (single-process scheduler; process
isolation demonstrated in v4.x). Verifier marks mean "I executed this" --
the both-mark version created an N-round gossip echo; no-op joins must not
re-gossip (a second echo); quiescence is detected by STABILITY, never by
momentary inbox emptiness. Verification-dedup (one re-execution per
immutable fact per verifier) reduced sync verifier work 556,426 -> 328,730
exactly as the reviewer predicted.

RESULTS (N=4, 2-input closure to size 8; six fault configs: latency 2-20,
30% dup + 30% loss, restart from stale snapshot, temporary partition):
SEMANTIC convergence in 6/6 -- identical serialized fact states, derived
behavior maps, preferred maps. Duplicate execution: ZERO OBSERVED in this
workload; structurally guaranteed per PROGRAM (ownership), statistical per
EVALUATION KEY (expansion-identical programs owned by different nodes can
race within the gossip window -- the cadence law at the evaluation layer;
reviewer demonstrated nonzero duplicates on a colliding-key workload).
Verifier work: zero UNDER TRUST -- the trust dividend, not architecture;
measured trust=False on the same config: verifier = 3.00x unique (exactly N-1) (each
importer re-executes; the N-1 replication cost, now measured). Divergence
cost: 58-90% extra worker interactions vs the single-schedule reference
(this now INCLUDES the work of closing the merged frontier to a genuine
fixed point -- see the second correction below; the earlier 20-85% was
measured with a harness that stopped short of closure and with broken
restart accounting, both now fixed).
CORRECTED -- was "CONDITIONAL EMERGENT EFFECT" (a MEMO-KEY BUG, not an
emergent effect): the earlier claim that divergent stale schedules reach
16/16 where the canonical single schedule reaches only 14/16 was an
artifact of a depth-blind regeneration guard. Node.refill()'s memo stamp
keyed on the frontier (reps) alone; because depth is advanced by a
recursion that leaves the frontier unchanged, the guard fired the instant
depth first reached max_size and skipped the ENTIRE size-8 candidate band
forever -- so the canonical N=1 schedule was crippled to 14/16 (missing
XOR, XNOR, both constructible at size 8 from single preferred reps, e.g.
AND[OR(a,b), NOT(AND(a,b))]). Any fault that churned the frontier changed
the stamp, re-opened the band, and cleared that artificially low bar; the
"emergence" was churn getting credit for work the canonical schedule
should have done alone. Fix: stamp on (depth, frontier) -- still quiesces,
no longer truncates. The canonical single schedule now reaches
FULL BEHAVIOR COVERAGE for this experiment -- all 16 two-input Boolean
functions -- deterministically: 16/16 every seed (asserted over a seed
sweep) at identical cost (unique 16,134, programs 280), matching
[synth_bool4 DET] pid-for-pid cross-engine. (16/16 is the Boolean-function
ceiling for 2-input size<=8, NOT a completeness ceiling for programs or
evaluations -- those keep growing with divergence, see below.) SECOND CORRECTION (this session, from a reviewer applying the project's own
"separate agreement from closure" rule): an intermediate build then over-
claimed the OPPOSITE -- that under faults "a node quiesces on a stale
frontier and the collective settles BELOW the ceiling" -- on the strength
of one 15/16 run. That was a harness artifact, the SAME premature-
termination error as the memo bug, one level up: run_async broke on local
quiescence, did a final fact merge, and REPORTED coverage without CLOSING
the merged frontier. A merge can hand a node a frontier richer than any it
generated against (a peer's facts fill a gap in its preferred reps),
setting gen_stamp=None -- the node KNEW it was stale but was never stepped
again. A resume probe (research/probe_quiescence.py) closes that 15/16 run
to 16/16 in <=3 rounds; every other config was already closed. After the
merged facts are saturated (run_async now does this), behavior coverage
reaches the full 16-function set in ALL SIX TESTED configs. So NEITHER claim
survives -- divergence neither purchases coverage nor loses it. (Coverage
being invariant across the tested schedules is well-motivated -- the fixed
point is the closure of the reachable size<=8 program space -- but "all
tested configs" is the earned wording, not a proven schedule-invariance.)
  What IS schedule-dependent is the PROGRAM lattice, the SET of
implementations realizing those 16 behaviors: canonical N=1 closes at 280
programs; healthy N=4 at 346-399 (seed-dependent); faults at 427-508; and
the sets are not even nested (one healthy seed misses 15 canonical programs
while adding 95). Divergence accumulates implementation MULTIPLICITY -- but
this is a STRUCTURAL effect, not a demonstrated benefit: of the preferred
representatives that differ from canonical, NONE is strictly better in
(ref, exp, cost); they differ only by the content-hash tie-break. Whether
that multiplicity ever helps (larger-horizon closure, resilience after
program removal, composition, a richer quality metric) is open -- measure it.

THIRD CORRECTION (this session): the round-2 "genuine fixed point" was
reached by a SATURATION ORACLE -- run_async forces all-to-all full-state
exchange (no loss/delay) plus centrally driven work exhaustion. That
computes the point the dynamics converge toward, but does not show the
pairwise gossip scheduler reaching it on its own. Removing the oracle
(research/probe_autonomous.py) exposes what the coordination-free dynamics
actually do: (a) full COVERAGE closure IS autonomous and robust once
anti-entropy is adequate; but (b) AGREEMENT is EVENTUAL, not immediate:
at the default (throttled) anti-entropy the autonomous loop stops
DISAGREEING (and a replica can still be below 16); at adequate anti-entropy
fact agreement usually holds at the stop but is not guaranteed. Precisely:
THIS local stability heuristic cannot establish fact agreement -- it only
observes that nothing changed recently. That is a property of the heuristic,
NOT an impossibility: certified termination (acknowledgements, version
vectors, distributed termination-detection protocols) is a distinct,
unbuilt layer. The stopping-mode ladder the project now distinguishes:
local stability < local closure < semantic (signature-set) agreement <
preferred-map agreement < fact agreement < saturated closure < certified
termination. The autonomous loop has the first two; saturation computes
the fifth and sixth; the seventh does not exist yet. So the honest split
is: coverage-closure is an autonomous property; DETERMINISTIC agreement at
a chosen stopping time is what the saturation phase buys. The KB figures
now include the saturation bytes (previously an accounting asymmetry,
fixed); adequate autonomous anti-entropy roughly doubles bandwidth.
  The invariant that survives all three passes: replicas that have received
the same facts derive identical behavior and preferred-representative maps
(a CvRDT property). Getting every replica the same facts is eventual under
loss, and terminating a measurement at the right moment is a separate
problem. (The old "single-preferred-rep closure is behavior-incomplete at
tight horizons -- the Pareto gap" was also the memo bug. Whether single-rep
closure is complete at ALL horizons is separable and genuinely open.)
  Restart accounting was also broken and is fixed: restore() built a fresh
node with paid=vpaid=0, so a rolled-back node's already-performed (and
already-gossiped) work vanished from the totals and dup=worker-unique went
NEGATIVE (-6,238, impossible under its own definition). Run-level carried
counters preserve it; dup is now >=0 by construction.

FOURTH CORRECTION (this session, continuing the same review loop; reviewer
right on all four points). (1) The autonomous-probe "partition" row was an
INVALID TEST as labeled: at adequate anti-entropy the runs stop at ticks
~238-318, but the configured partition was (2, 300, 900) -- 7/8 runs ended
BEFORE the partition began, one saw 18 ticks of it, none saw healing. It
measured no-partition dynamics wearing a partition label. (In the MAIN
harness the same window IS active at quiescence, so that row measures
"partition active at stop; the saturation oracle reunites the node" --
now annotated; autonomous healing was untested everywhere.) The rebuilt
staged-healing experiment (probe part C) asserts the partition overlaps
execution, records per-node coverage at heal, then lets the UNCHANGED
protocol run: the fault bites in 8/8 runs per window (the isolated node
sits at 14-15/16 at heal -- it cannot see the program space owned by its
peers), and the protocol recovers autonomously: median 31-38 ticks from
heal to full per-node coverage, median ~91 (max 212) to fact agreement,
across windows (50,150), (50,250), (100,250) x 8 seeds. Autonomous
partition recovery is now DEMONSTRATED, not assumed. (2) The earlier
explanation of non-agreeing stops ("a fact still in flight") was WRONG in
its mechanism: at both measured misses all inboxes were EMPTY
([0,0,0,0]); the differing facts sat quietly in one replica's store
([325,321,321,323] and [351,351,351,348] programs) AWAITING A FUTURE
random anti-entropy pairing, and continuing the ordinary protocol reached
agreement in 6 and 43 ticks. Nothing was in flight; the next necessary
exchange simply had not been scheduled yet. This strengthens the eventual-
consistency reading: the system converges once communication continues.
(3) The probe's coverage metric read NODE 0 only, so its "40/40" formally
asserted node 0's coverage; the stronger per-replica claim happened to be
true but was unenforced. covs() is now per-node and the battery asserts
EVERY replica at 16/16 (32/32 in the no-partition battery). (4) Agreement
is now measured in LAYERS, and the layering is the result: signature-set
agreement (which 16 behaviors exist) 32/32 and preferred-map agreement
32/32 at the heuristic stop, fact-store agreement 31/32 -- SEMANTIC
RECOGNITION STABILIZES BEFORE THE SUPPORTING EVIDENCE HISTORY
SYNCHRONIZES. Replicas can recognize identical behaviors, and even
identical preferred representatives, while still holding different
implementation-fact collections.
FLAG: XOR3 emerges compositionally in the async-converged store (witness
5779c31e, intrinsic 416, no AP-free witness) referencing component cd8b128e.
The WITNESS is regime-dependent (a different composed form than the
synchronous 6b663124); the COMPONENT is regime-invariant -- the same content
address across orchestrated and autonomous execution. Composition varies
with schedule; identity does not. (cd8b128e is the size-8 XOR the corrected
canonical schedule now generates deterministically; surfacing it no longer
depends on fault-driven library churn.) Laws earned: 20 verifier marks
assert execution, not agreement; 21 no-op joins are silent; 22 quiescence
is stability; 23 a regeneration memo key must include EVERY dimension the
generator ranges over (depth AND frontier) -- a depth-blind key silently
truncated the search band and masqueraded as an emergent coverage effect;
24 measure coverage only at a GENUINE FIXED POINT of merge -> derive
frontier -> generate -> evaluate -> merge, never at the union reached when
local queues first empty -- a fact merge can enrich a node's frontier and
mark it stale (gen_stamp=None), and reporting before it re-closes
UNDERSTATES coverage (this produced a spurious 15/16 "settles below the
ceiling" claim; closed, every TESTED schedule is 16/16). Behavior coverage
at the saturated fixed point is invariant across the tested schedules; the
program lattice is not. Both the "divergence purchases coverage" and the
mirror "divergence settles below" claims were these two premature-
termination bugs, retracted. 25 distinguish the autonomous DYNAMICS from a
measurement ORACLE: a saturation phase (forced all-to-all exchange + central
work exhaustion) computes the fixed point but does not demonstrate the
pairwise scheduler reaching it; measured separately, full coverage IS
reached autonomously and robustly (per-replica, asserted), but fact
agreement at a stability stop is only EVENTUAL -- THIS heuristic observes
recent silence, not agreement; certified termination is a distinct, unbuilt
layer. Deterministic agreement at a chosen stopping time is what the oracle
buys, not an autonomous guarantee. Account for its bytes symmetrically with
its work. 26 a fault-injection test must ASSERT the fault actually
overlapped execution -- the autonomous partition row configured a partition
at ticks 300-900 while adequate anti-entropy finished runs by ~240-320, so
7/8 "partition" runs contained no partition at all; a test whose fault never
fires measures the wrong hypothesis while reporting success (the staged-
healing probe now asserts partition_ticks_seen > 0 and records coverage
at heal to prove the fault bit).

Answer to the session's final question: autonomous nodes with stale,
divergent, locally derived schedules DO converge under faults -- and after
four correction passes the structure of that convergence is precise. Full
behavior coverage (all 16 two-input functions) is reached AUTONOMOUSLY on
EVERY REPLICA: 32/32 runs in the latency/duplication/loss battery
(per-node, asserted), no central phase required. After a temporary
partition that provably bites (the isolated node at 14-15/16 at heal), the
UNCHANGED protocol recovers full per-replica coverage in ~31-38 ticks
(median) and full fact agreement in ~91 (max 212). Agreement is LAYERED
and the layering is the finding: at the stability stop, signature-set and
preferred-map agreement held in 32/32 runs while fact-store agreement held
in 31/32 -- semantic recognition stabilizes BEFORE the supporting evidence
history synchronizes. The one non-agreeing stop had empty inboxes; the
differing facts sat in a replica's store awaiting a future anti-entropy
pairing, and ordinary continued gossip agreed in 43 ticks. Divergence
changes neither the behavior set (it does not purchase coverage, nor
settle below it -- both earlier claims were premature-termination bugs) but
it does change the PROGRAM lattice: divergent schedules accumulate more,
different implementations of those same behaviors (280 canonical, 346-399
healthy N=4, 427-508 faults, not nested), at 58-90% extra worker
interactions -- so far a structural effect only; no divergent run produced
a strictly better preferred representative. The durable one-liner: same
facts compel the same recognized behaviors -- and recognition can be
shared before, and independently of, the full evidence history being
shared. The schedule, the program set, the cost, and the moment of fact
agreement all vary; the recognized projection does not.
