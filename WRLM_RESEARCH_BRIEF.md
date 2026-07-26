# WRLM Research Brief

**Status:** design converged on paper across three review rounds (Claude ↔ GPT-5.6, 2026-07-26). **Build-order step 1 is shipped and CLOSED** — `GoalSpecV1`, `TaskBundleV1`, the one engine adapter, and a five-gap verifier-hardening pass. **Step 2 has begun** with `WorldRecordV1`. See §10. Steps 3–10 remain paper only and are not authorized.

**Scope:** this document is the design of record for WRLM-0 and its evaluation. It supersedes nothing in the shipped stack; WRL, TRVM, TRAAVIIS and Forge are unchanged and remain authoritative for their own layers.

---

## 1. What WRLM is, and what it is not

The shipped stack is a **substrate**: WRL seals worlds (`sem-`), TRVM reduces them deterministically (`ic_ref == ic32 == oracle`), Films replay them, TRAAVIIS admits episodes (`episode-`, `bundle-`). Every component is *deliberately dumb* — total, deterministic, content-addressed, non-statistical.

WRLM is the **only statistical component in the stack, and it does not exist yet.**

> The model proposes. The edit algebra constrains. TRVM disposes. TRAAVIIS admits.

WRLM is an **admitted generative transducer**: a probabilistic proposer over deterministic sealed worlds. It is not a world model, not a memory system, and not a replacement for anything already shipped.

### The layer boundary (the question that started this)

"TRAAVIIS already has worlds" is correct and is not the same thing. TRAAVIIS *holds, seals, replays and admits* worlds. WRLM *authors* them under supervision. Substrate vs. cortex. The substrate's guarantee is exactness; the cortex's job is proposal. Neither absorbs the other.

---

## 2. The oracle ladder

An early framing error (mine) described `sem_id(output) == sem_id(target)` as a total correctness oracle. It is one rung of four:

| Rung | Question | Oracle |
|---|---|---|
| 1. Validity | does it parse, seal, and lower? | total, free (`diagnose_core`, seal) |
| 2. Target identity | is it *the* intended world? | total, free (`sem-` equality) |
| 3. Goal satisfaction | does it meet a stated property? | total, free (`GoalSpecV1` evaluation) |
| 4. Subjective quality | is it *good*? | not available; out of scope for WRLM-0 |

WRLM-0 targets rungs 1–3 only. Rung 4 is explicitly deferred and must never be smuggled in via an LLM judge (see §7).

---

## 3. Architecture: Arm D′ (primary)

Direct emission of `GraphEditV1` ops (arm E) is expected to lose on accuracy per the edit-format literature. Full-text emission (arm D) is accurate but unconstrained. D′ is the synthesis:

```
model emits full WRL text
  → host parses into an isolated candidate buffer
  → diagnose_core
  → seal  (candidate_sem_id)
  → wrl_diff.semantic_diff(base, candidate)
  → derived GraphEditV1 op sequence
  → apply_edit(base, derived_ops)
  → assert resulting_sem_id == candidate_sem_id
```

**The ops are derived, not generated.** This is the whole trick. It captures D's accuracy (the model writes prose-like text, its strongest modality), E's safety (nothing reaches the world except through the six typed ops and the existing `apply_edit` seam), and E's trainability (the derived op sequence is clean typed supervision for later RLVR).

### D′ laws (must hold before the arm is trusted)

1. **Isolation** — a candidate never touches the active sealed world; failure leaves the draft byte-identical.
2. **Totality of diagnosis** — every rejection carries a typed `WRL_*` code; no raw exception escapes.
3. **Derivation soundness** — `apply_edit(base, semantic_diff(base, cand))` reproduces `sem_id(cand)` exactly, or the attempt is discarded as a host fault (not a model failure).
4. **Op closure** — derived sequences use only the six frozen ops; anything else is a host fault.
5. **No silent repair** — the host never edits the model's text.
6. **Attribution** — host faults and model failures are recorded in distinct channels and never pooled in the metrics.

Existing seams reused: `wrl_draft.py` (draft store, `ReplaceWorldSourceV1`, invalid-but-editable candidates), `wrl_converge.py` (`CanvasSession`, gesture→`GraphEditV1`), `wrl_canonical.py` (seal/validate), `wrl_diff.semantic_diff`, `diagnose_core`, `apply_edit`, ~61 typed `WRL_*` codes. **No new runtime construct. No new identity rung.**

---

## 4. Objectives: `TargetSpecV1` + `GoalSpecV1`

### The template-leakage tension

> An exact `sem-id` oracle requires a **uniquely determined target**. A uniquely determined target requires an **over-specified objective**. An over-specified objective **is a template for the answer**.

A structural-family train/test split does **not** catch this, because the template generalizes even when the graph structure does not.

### Resolution

`TargetSpecV1` (exact `sem-` target) is **retained**, not replaced — it is the only *total* oracle available and giving it up is strictly worse. `GoalSpecV1` (underdetermined predicate objectives) **supplements** it and is gated by tier.

`GoalSpecV1` is a **closed serialized AST, not a language.** Two reasons, the second of which is load-bearing:

1. An open predicate language accidentally becomes a second WRL — a language-design project nobody authorized.
2. **The restricted closed AST, evaluated over finite bounded WRL worlds, keeps satisfaction decidable by construction** — the closure of the AST alone does not guarantee this; the bounded finite semantics do. That decidability is what makes the `S` baseline (§5) implementable at all. An open language, or unbounded world semantics, makes `S` undecidable and silently kills the most important baseline.

**The AST must be sealed into task identity.** Otherwise the suite is not reproducible and the sealed-objective hole reopens.

---

## 5. Baselines: the floor, and why it is the whole experiment

The original 5-arm design (A–E) contained **no floor**. Every arm was a model arm, so the *verifier loop's own contribution as a search algorithm* could not be separated from the model's contribution.

| Arm | What it is | Cost |
|---|---|---|
| `∅` | random legal edits | $0 |
| `∅+` | diagnostic rule table (~61 codes → ~300 lines of if-statements) | $0 |
| `R` | retrieval over prior worlds | $0 |
| `S` | bounded symbolic search (beam / A*) over `GoalSpecV1` | $0 |
| **`best-of-k`** | **k i.i.d. model attempts, diagnostics withheld** | **= cost of the loop arm** |

All four $0 baselines are a **mandatory spending gate**: they run before any paid call, and they are gated per task family.

> If 300 lines of if-statements beat a frontier model on Tier 2, the task is not measuring understanding — and you will have paid to discover that.

### The baselines are also the hackability audit

The 2026 reward-hacking literature (§8) finds that verifiers fail because they are **partial**. A total `sem-` equality oracle eliminates that class outright — you cannot partially satisfy a hash. But the risk **relocates to the task generator**: with a total oracle, the only remaining route to a fake-high score is a leaked target.

`∅+` scoring 94% on a tier is exactly "a test suite weak enough that an incorrect patch passes," transposed. **The $0 baselines are the environment-hardening procedure, not merely a scientific control.**

### `best-of-k` is non-negotiable and outranks `S`

`S` tests whether the *model* is needed. `best-of-k` tests whether the *loop* is needed — which is the more load-bearing claim, since the loop is the thesis. Same token spend as the loop arm; the only difference is that diagnostics are withheld between attempts.

`B − best-of-k` is the **only** quantity that isolates feedback from resampling.

---

## 6. Experimental design

### Three paid trajectories, four reported conditions

The two counts are not the same and must never be conflated in a cost table or a results table. **Three trajectories are purchased; four conditions are reported**, because the first trajectory yields two nested conditions.

| # | Reported condition | Source | Paid? |
|---|---|---|---|
| 1 | attempt-1 / plain | trajectory 1, first attempt | (nested — no separate spend) |
| 2 | feedback loop | trajectory 1, final result | trajectory 1 |
| 3 | sealed D′ loop | trajectory 2 | trajectory 2 |
| 4 | best-of-k, no feedback | trajectory 3 | trajectory 3 |

Conditions 1 and 2 come from the *same* purchased trajectory — that is the 2→3 collapse and the source of the nesting below. Conditions 2 and 4 cost the same tokens by construction; that equality is what makes `B − best-of-k` a clean test.

### The 2→3 collapse is nested; report it as nested

Two trajectories per task, collapsed to three conditions, with Arm A = attempt 1 of the raw trajectory and Arm B = the final result of *that same* trajectory. The token saving is legitimate. Two consequences must be respected:

1. **`P(B) ≥ P(A)` is arithmetic, not a finding.** B ⊇ A by construction. The comparison cannot fail. Never run an independent-samples test on it; never report "B beats A" as evidence for the loop.
2. The only informative estimand is **conditional closure**:

   > `P(success by attempt k | attempt 1 failed)` — a single proportion over the failed subset, Wilson interval, no comparison required.

### Metrics discipline

**Do not use pass@k.** Attempts within a trajectory are dependent and feedback-conditioned; pass@k assumes i.i.d. draws. Use instead:

- success within attempt budget
- closure-by-attempt curve
- attempts to closure
- **cost to closure** (the honest headline metric)
- diagnostic reduction per attempt

**The task is the statistical unit**, not the attempt.

If `S` wins a family at $0, the model earns its place only where `S` fails. That is a product win, not a research failure — and the result worth publishing is **the frontier curve of which method owns which task family**, not "model good."

### Statistical power

n ≈ 60–100 paired tasks for ~15pp detection at 80% power. **n = 20 is uninformative for inference** and should not be run as if it were.

### IRT is deferred — on statistical grounds, not sequencing

An earlier recommendation to lift `PRISM/lib/prism/irt/model.ex` was **wrong**. IRT calibrates item parameters from many *examinees* per item; WRLM-0 will have 2–4 model conditions. A 3PL with 4 examinees is unidentified; even Rasch wants ~100+ responses per item. **Generator-defined difficulty strata are the only correct choice at this n**, not a lesser substitute.

---

## 7. Acceptance policy: `box-and-box`, not an ad-hoc DSL

Admission is governed by the existing `box-and-box` kernel (`AmpersandBoxDesign/box-and-box/`) — eight-rung modality ladder, 116 property-tested laws, zero runtime deps, ships certificates. No new policy language.

Gate order (GPT-5.6's reordering, accepted):

```
feasible ▸ permitted ▸ resource-compliant ▸ best
```

Rung mapping: **alethic** (can this world exist / does it seal) → **deontic** (is this edit permitted by the op algebra) → **resource** (affine ledger: token budget, attempt budget) → **axiological** (ranking among admissible candidates).

**The eight rungs are orthogonal to PULSE's five phase kinds.** The rungs govern a single decision; PULSE sequences a loop over time. Do not claim a 1:1 mapping.

### Two-stage admission

1. **Artifact admission** — is this exactly adapter X? (digest equality)
2. **Behavioral admission** — did X meet policy P over suite S? (sealed evaluation)

These are separate certificates and must not be conflated.

### No LLM judge

Rung 4 (subjective quality) is out of scope. Introducing an LLM judge would reintroduce the partial-verifier failure class the whole design exists to eliminate.

---

## 8. Prior art position (read before making any public claim)

### On RLVR provenance — the exclusivity claim does NOT survive as stated

- **ATLAS** ([2605.26971](https://arxiv.org/pdf/2605.26971), May 2026) traced 1,450,827 instances across 16 open RLVR datasets to 20 atomic sources, attributing 99.7%. Dataset lineage for RLVR is an established subfield with a flagship result.
- The intended pitch is already the field's *stated* open problem, near-verbatim: *"a lineage graph that connects where each of the task, the verifier, and the reward signal came from represents the next battleground."*

**What survives, and may be asserted:**

> ATLAS is *retrospective statistical attribution over corpora never designed to be traceable*. `bundle- → episode-* → adapter digest → admission certificate` is *prospective per-episode identity minted at generation time*. Archaeology vs. birth certificates.

Narrower, defensible, holdable.

### On reward hacking — the literature validates the thesis

- [2606.16062](https://arxiv.org/pdf/2606.16062) — on a 49-task sample of **SWE-bench Verified**, **28.5% of tasks have test suites weak enough that a Docker-verified incorrect patch passes.** On the field's gold-standard *verified* benchmark.
- [2604.15149](https://arxiv.org/pdf/2604.15149) "LLMs Gaming Verifiers" (ICLR 2026 workshop)
- [2605.20744](https://arxiv.org/html/2605.20744) "Hack-Verifiable Environments"
- [2606.04923](https://arxiv.org/pdf/2606.04923) — 15,247 training episodes, six detection algorithms, 78.4% precision / 81.7% recall

Common cause: **partial verifiers are gameable because the proxy can be satisfied without the goal.** A total oracle removes the class. See §5 for where the risk relocates.

### Assurance-stack neighbours (complementary, non-overlapping)

| Layer | Who | Proves |
|---|---|---|
| Artifact integrity | OpenSSF / Sigstore model-signing | these are the bytes |
| Execution proof | EZKL / ZKML | this inference ran |
| **Semantic outcome** | **TRAAVIIS** | **this result is re-derivable** |
| Prospective per-episode training lineage | (underoccupied) | this data came from somewhere real, and was minted traceable |

### Related work confirmed real

`arXiv 2607.14169` (play-adequacy; submitted 2026-07-15, revised 07-19) — earlier flagged unverified by Claude due to a search-indexing miss. **Confirmed real by GPT-5.6; citation is usable.** Supporting: 2606.30639 (Self-Evolving World Models), 2606.09032 (Text World Models).

### Bend / HVM

Complementary, not competing, **not a dependency today**. Bend is parallel computation scale-out; TRVM/WRLM is intelligence crossing an exactness boundary.

Nuance worth keeping: both bet on **confluence** — HVM's optimal reduction and `ic_ref == ic32` are the same statement, *the answer does not depend on the schedule*. If WRLM ever parallel-evaluates many candidate worlds (the k-attempt loop literally is k independent sealed candidates per task), an HVM-style backend is the natural place to look. Not now: the bottleneck is model tokens by ~3 orders of magnitude.

---

## 9. Cost model

Reference walkthrough (GPT-5.6): `2,400 calls × 2.5k in = 6.0M in`; `× 600 out = 1.44M out`; at `$0.30 / $1.80` per M → `$1.80 + $2.59 = **$4.39**`. Arithmetic verified correct.

Per-provider reference: Qwen3.5 Plus $4.39 · GLM 5.2 $10.02 · GPT-5.5 (reference cell) $12.20 · pilot ~$2 · contingency $5–20. **Total envelope $20–50.**

### Two pressures on the assumptions

- Under D′ the model emits **full WRL text**, not a diff. 600 output tokens covers ~15 nodes, not Tiers 4–6.
- Attempt *n* carries attempt *n−1* plus diagnostics, so input grows monotonically within a trajectory. 2.5k is the *attempt-1* number.

**Realistic landing: $7–10, not $4.39.** Still trivial.

### Budget rule

**Set the hard OpenRouter cap at 3× the point estimate, not at the estimate.** A cap set at exactly the estimate turns a routine 2× underestimate into a mid-run breach, and a half-finished suite is worth $0.

Affordable configuration: `N = 100 tasks, 3 paid trajectories × 3 tiers = 9 paid cells, mid-tier models + one frontier reference cell`. That is **9 purchased cells yielding 12 reported conditions** (4 per tier) — see §6. The rejected configuration (`200 tasks × 30k tok × 30 cells ≈ 180M tokens ≈ $900` at frontier prices) buys no additional inferential power.

---

## 10. Build order (step 1 closed; step 2 begun; steps 3–10 agreed on paper only)

1. ~~**`GoalSpecV1` closed AST** + sealing into task identity~~ — **SHIPPED and CLOSED.** `TRVM/wrlm/goalspec.py` (G0–G13, 14/14) and `TRVM/wrlm/taskbundle.py` + `worldview.py` + `errors.py` (W0–W9 / T1–T14, 24/24)
2. Task generators + coverage-stratified generation over generator-defined difficulty strata — **begun:** `WorldRecordV1` shipped (`TRVM/wrlm/worldrecord.py`, R-battery 8/8). `generator.py`, `coverage.py`, `families.py` still to build
3. `TargetSpecV1` alongside, tier-gated
4. **D′ host** (parse → diagnose → seal → diff → derive → apply → assert), with the six laws as the test battery
5. **$0 baselines** `∅`, `∅+`, `R`, `S` — mandatory spending gate, run before any paid call
6. **`best-of-k`** control
7. Paid arms, under hard cap
8. `box-and-box` acceptance policy + certificates
9. Two-stage admission (artifact / behavioral)
10. `wrlm.adapter.v1` substrate registration

### What step 1 actually shipped

`TRVM/wrlm/goalspec.py` — no dependency on `forge/` (the v1 vocabulary is duplicated and **pinned by parsing** `wrl_canonical.py`, never by importing or grepping it).

**Two-sorted closed AST**, 4 goal kinds + 9 filter kinds, exact-key validation:

```
Goal   ::= all[Goal*] | any[Goal*] | not(Goal) | count(domain, where, cmp, n)
Filter ::= filter_all | filter_any | filter_not
         | role_is | id_is | config_eq | degree        -- object-sorted
         | edge_kind_is | endpoint(side, where)        -- edge-sorted
```

`count` is the only quantifier and subsumes the rest: `exists` = `count ≥ 1`, `forall P` = `count(¬P) = 0`, `exactly n` = `count = n`. `all[]` is TRUE, `any[]` is FALSE. `endpoint` is the single legal sort crossing (an edge filter ranging over the object the edge names); every other crossing is `WRLM_GOAL_SORT`.

**Decidability, concretely.** Every quantifier ranges over `artifact["objects"]` / `artifact["edges"]` — finite lists materialized before evaluation. No recursion, no fixpoint, no reachability operator, no floats. `MAX_GOAL_DEPTH = 8` / `MAX_GOAL_NODES = 64` bound the AST itself so an adversarial goal cannot blow up `S` even on a small world. Evaluation is a terminating fold, `O(|AST| × (|O|+|E|) × |E|)` worst case, and is **total** — a dangling endpoint or a malformed world yields `False`, never an exception.

**Identity.** `goal-<sha256>` over canonical bytes, same discipline as `sem-` (`sort_keys=True, separators=(",",":")`). Canonicalization is **order + dedupe only**, on the commutative idempotent combinators. Stated caveat, because it bears on task identity: `not(not(X))` and `X` are semantically equal but seal to **different** ids. Goal identity is syntactic up to commutativity — it is not a decision procedure for goal equivalence and must never be used as one.

Four typed codes: `WRLM_BAD_GOAL`, `WRLM_GOAL_SORT`, `WRLM_GOAL_BOUNDS`, `WRLM_SEALED_IMMUTABLE`. `SealedGoal` mirrors `SealedArtifact` — canonical bytes are the object, id is re-derived from them, `.node` is a fresh copy, writes refused, `open_sealed_goal(blob, expect_id=…)` refuses a mismatch.

**Deliberate v1 boundaries** (not oversights): structural only — goals are predicates over the sealed *static* artifact, not over films; no reachability operator (bounded and decidable, but it materially complicates `S`, so deferred until `S` exists and can be measured).

Battery `TRVM/wrlm/test_goalspec.py` — **G0–G13, 14/14, 0.2s**. G13 evaluates 11 predicates against the **real frozen demo artifact**, and first proves the vendored fixture *is* that world by re-deriving `sem-8ae91fe9…fe4a` from its own bytes with pure `json`+`hashlib`.

### What step 1's second half shipped — `task-`, the rung below an attempt

A goal is not a task. A task is a goal *plus the world it starts from*, plus enough provenance to say where it came from, under one id. `TRVM/wrlm/taskbundle.py` closes the chain `sem-` (world, forge) → `goal-` (objective) → **`task-`** (the pair + provenance); everything above it (`episode-`, `bundle-`) already exists in TRAAVIIS.

```
TaskBundleV1 = {task_version, base_world{semantic_id, source},
                objective{goal, goal_spec_id, target_semantic_id},
                stratum{family, tier, difficulty},
                generator{generator_id, generator_version, seed}}
task_id = "task-" + sha256(canonical bytes)
```

Three laws carry the weight:

- **An objective is mandatory.** A bundle may carry a goal, a `target_semantic_id`, or both — never neither. A task with no objective is unfalsifiable, which is exactly the failure class the `sem-` spine exists to remove. (`WRLM_TASK_NO_OBJECTIVE`.)
- **A carried id is never trusted.** `goal_spec_id` is re-derived from the goal node and compared; storing it is a convenience for readers, believing it would make the seal decorative. (`WRLM_TASK_ID_MISMATCH`.)
- **Degeneracy is refused, and the check is split in two.** `target == base` is caught by the *pure* validator because it needs no world. A goal the base world *already satisfies* cannot be — deciding that requires the objects and edges — so it lives in an explicitly impure `check_task_nondegenerate(task, base_view)`, called by a generator that has the world in hand. That split is what lets a task be validated offline, in a corpus, with no engine present. (`WRLM_TASK_DEGENERATE`.)

`difficulty` is a coarse **declared** ordinal owned by the generator, not a fitted latent trait — at 2–4 examinees an IRT parameter is unidentified (§6), so the honest move is a stratum the analysis can condition on.

**`TRVM/wrlm/worldview.py` — the one adapter.** `forge_api.lower_source()` returns a `LowerResultV1` whose `graph.nodes[*]` keys the object as **`id`**; a canonical artifact keys it as **`object_id`**. Letting the evaluator accept both shapes would be the beginning of an identity bug — two spellings of "the same" world, silently interchangeable. So the rename happens once, here, under test, and `goalspec` reads exactly one shape. The adapter pins `forge.lower-result.v1` and fails loudly on a bump rather than mis-evaluating against a shape it no longer understands; a source that did not lower becomes `NotLoweredError` carrying the **engine's own** typed diagnostics, never a paraphrase. It imports nothing from `forge/`.

Battery `TRVM/wrlm/test_taskbundle.py` — **W1–W6 + T1–T12, 18/18, 0.2s**. W1 asserts the shape *mismatch* itself, so the adapter cannot quietly become dead weight; W2 proves a lowered source and the stored artifact converge on the same view; T12 runs the end-to-end shape a WRLM-0 episode takes — engine payload → view → `task-` → unsolved at attempt 0, solved once the world gains the object the goal asks for.

### Step 1 contract closure — the verifier is attack surface

A review pass (GPT-5.6, 2026-07-26) found four contract gaps in the shipped step 1, and building the reproductions turned up a fifth. All five were verified empirically before being accepted; all five are now closed, with a check each.

| # | Gap | Why it mattered | Closed by |
|---|---|---|---|
| 1 | `from_artifact` **trusted** a caller's `semantic_id` | `{"objects":[],"edges":[]}` could present itself as any world in the corpus. A target-bearing task is scored by comparing `sem-`, so this was a direct **false-positive** path: an empty world claiming to be the solution | identity is now **derived**; a supplied id is an *assertion* that is checked, never believed (W7) |
| 2 | The layer was not importable as a package | `import wrlm.taskbundle` → `ModuleNotFoundError`. The batteries only passed because they inserted their own directory on `sys.path`. Step 2 would have developed against a layout TRAAVIIS could not import | `__init__.py` + package-relative imports; W0 asks a **clean subprocess** with no path help, because a test that patches `sys.path` cannot prove importability |
| 3 | "Total on malformed data" was **too strong a claim** | `{"objects": 1}` raised an untyped `TypeError`; `deserialize_*(123)` likewise | malformed containers are typed rejections at the adapter; the evaluator is genuinely total; deserializers type-check their input (W8, W9) |
| 4 | `from_artifact` **silently dropped** non-dict members | A corrupt artifact quietly shrank into a smaller *valid-looking* world — under which a goal like "no Spinner exists" would **pass** | members are typed rejections, never filtered (W8) |
| 5 | `satisfied_by` returned `False` for a target clause scored against a bare artifact | The same world gave opposite verdicts through two spellings. A **solved** episode silently scored as **failed** | an identity-less world is now a typed rejection with a fix-it message (T13) |

Gap 5 was the worst of the five and the least visible. A crash gets noticed; a silently unrewarded success gets *trained against*.

That framing is not ours alone. Ray, *Before the Model Learns the Bug: Fuzzing RLVR Verifiers* (arXiv 2606.01066), fuzzes reward verifiers and reports five failure classes — malformed-input handling, false negatives, false positives, normalization inconsistency, and identity/state-consistency failures — which map almost one-to-one onto gaps 3, 5, 1+4, the `case-`/`task-` split below, and gap 1 again. Its thesis is a timing argument: catch verifier bugs *before* a model internalizes them. WRLM has not generated its first task, so this is exactly the right moment to pay that cost, and the reason the closures preceded any generator work.

### `case-` vs `task-` — the statistical unit is not the receipt

`task-` includes `family`, `difficulty`, `generator_id`, `generator_version` and `seed`. That is correct for provenance and **wrong** for counting. A generator emitting one problem under 20 seeds mints 20 distinct `task-` ids; treating those as 20 independent trials multiplies *n* by 20 and shrinks every confidence interval by ~4.5× on nothing at all.

So the two questions are split, both **derived** from the bundle's own bytes and neither stored (there is nothing here for a generator to misreport):

```
case-   what the model is ASKED       base sem- + presented source + canonical objective
task-   that case, plus HOW it arose  + family, difficulty, generator, version, seed
```

Both `sem-` and presented source belong in a case: sugar and its numeric twin seal to the **same** `sem-` while showing the model **different text**, so they are genuinely different questions about the same world. Coverage ledgers and all statistical analysis deduplicate on `case-`; receipts carry `task-`.

This is the in-corpus half of a problem the 2026 contamination literature treats as the default assumption rather than an edge case — exact and near-duplicate items *within* and *across* benchmarks, with measured inflation on held-out duplicates in the 10–11pp range. We cannot control what a model saw in pretraining, but we can refuse to manufacture duplicates ourselves and then count them as evidence.

### Scope ruling: `base_world` means a sealed VALID world

The planned diagnostic-repair family starts from *invalid* WRL. Invalid WRL has no `sem-`. So the repair family **cannot** be honestly expressed as a `TaskBundleV1`, and it is out of scope for WRLM-0 step 2. Repair examples remain useful as training records; they are not benchmark instances yet.

The workaround that must not happen is pairing invalid source with some other world's `sem-` — an internally contradictory bundle. When the family's turn comes it gets its own object, keyed on what it actually has:

```
DraftRepairTaskV1 = {draft_source, diagnostics, origin_semantic_id?,
                     objective (target sem- or "seals at all"), mutation provenance}
```

### `WorldRecordV1` — why step 2 starts here and not with a generator

`TaskBundleV1.base_world = {semantic_id, source}` is an **unverifiable pairing inside a pure validator**: deciding whether *this* source lowers to *that* `sem-` requires the engine, and the whole point of the pure/impure split is that tasks validate offline. So the pair sits at the base of every task as a claim nobody local can check.

The fix is not to weaken `base_world` — it is to move verification to the one moment someone *does* have an engine, and make the result durable:

```
live Forge caller --lower_source--> LowerResultV1
                                          |
                                 capture + verify   (once)
                                          |
                                    WorldRecordV1
                                          |
                    offline generation, no engine present, forever after
```

`capture()` refuses unless all five bindings hold: the artifact's bytes derive `semantic_id`; the engine reports that same id; **both adapter paths agree on content, not just identity** (same `sem-` with different contents would mean the adapter pair is broken and a generator could build tasks about a world that never ran); the source is non-empty; the collections are closed. `validate_record_v1` re-checks the binding on reopen, because a stored record is still only bytes.

`taskbundle.make_task_for(record, …)` is then the blessed path, and it makes the scope ruling **mechanical** rather than merely stated: invalid source cannot become a record, so it cannot reach a `base_world` at all (R3c).

Battery `TRVM/wrlm/test_worldrecord.py` — **8/8**. R18 is the payoff: a serialized record reopens in a clean subprocess with no engine and no `sys.path` help and generates the byte-identical `task-` and `case-`. Verified additionally against the **live** engine (`forge_api.lower_source` at `v0.7.0-alpha.5`), which reproduces the frozen `sem-8ae91fe9…fe4a` and captures cleanly.

Still open for step 2: `generator.py` (deterministic `generate(world_record, stratum, seed) → SealedTask`, no ambient RNG), `coverage.py` (least-covered-cell selection, counting proposed *and* accepted-nondegenerate-unique), `families.py` (two families only — exact target transformation, and structural goal satisfaction). Remaining R-checks R4–R17 land with those.

Proposed object set: ~~`TaskBundleV1`~~ (shipped), ~~`WorldRecordV1`~~ (shipped, added to the set), `ProposalV1`, `CandidateWorldV1`, `TargetSpecV1`, `GoalSpecV1`, `ProducerFactV1`, `EpisodeReceiptV1`, `EvaluationReportV1`, `AdmissionDecisionV1`, `InteractiveEpisodeKernelV1`.

---

## 11. Open items

- **PRISM is excluded.** Its judging path is LLM-mandatory (`judge/rubrics.ex`, `dimension_worker.ex`, `meta_judgment.ex`; no programmatic judge exists), which is architecturally opposed to WRLM's thesis. Dependency flows **TRAAVIIS → PRISM**, not PRISM → TRAAVIIS. Two pieces remain salvageable if their procedure, algorithm version and seed are sealed: `judge/aggregator.ex:102–129` (bootstrap CIs, 1000 iterations). `irt/model.ex` is **not** salvageable at this n (§6). Note `PRISM/lib/prism/leaderboard/leaderboard.ex` is entirely stubbed and has no regression detection.
- **Hardware is not on the critical path.** WRLM-0 is a hosted-model evaluation under a $20–50 cap. No purchase is required or implied. (Intel Arc Pro B65/B70 are real and shipping — an earlier "probable fabrication" flag was wrong and is retracted; an internal contradiction is evidence of staleness at least as often as fabrication.)
- **Not yet decided:** which model family fills the frontier reference cell; task-family gating table for `S`; whether `InteractiveEpisodeKernelV1` is a distinct kernel or a mode of `EpisodeKernelV1`.
