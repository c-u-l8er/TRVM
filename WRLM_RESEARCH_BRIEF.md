# WRLM Research Brief

**Status:** design converged on paper across three review rounds (Claude ↔ GPT-5.6, 2026-07-26). **Build-order step 1 is shipped and CLOSED** — `GoalSpecV1`, `TaskBundleV1`, the one engine adapter, and a five-gap verifier-hardening pass. **Build-order step 2 is shipped and CLOSED**, together with its two ordered sub-steps — `WorldRecordV1`, `envelope.py`, the derived coverage domain (`wrlm.coverage.v1.2`, 320 published cells), the widened goal repertoire (29/29 triples, 0 padded witnesses), and a 58-world proved pool inhabiting 298 of 320 cells. See §10. Steps 3–10 remain paper only and are not authorized.

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

## 10. Build order (steps 1–2 closed; steps 3–10 agreed on paper only)

1. ~~**`GoalSpecV1` closed AST** + sealing into task identity~~ — **SHIPPED and CLOSED.** `TRVM/wrlm/goalspec.py` (G0–G13, 14/14) and `TRVM/wrlm/taskbundle.py` + `worldview.py` + `errors.py` (W0–W9 / T1–T14, 24/24)
2. ~~Task generators + coverage-stratified generation over generator-defined difficulty strata~~ — **SHIPPED and CLOSED.** `worldrecord.py` + `envelope.py` (R1–R19, 11/11), `coverage.py` + `families.py` + `generator.py` (R4–R17, R20–R29, 25/25), `tools/build_pool.py` → a 58-world proved pool. Sub-steps 2.1 (widen `propose_goals`, 29/29 triples, 0 padded) and 2.2 (grow the pool, 298/320 cells) closed with it
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

`capture()` refuses unless all five bindings hold: the artifact's bytes derive `semantic_id`; the engine reports that same id; **both adapter paths agree on content, not just identity** (same `sem-` with different contents would mean the adapter pair is broken and a generator could build tasks about a world that never ran); the source arrives **sealed to the result it produced**; the collections are closed. `validate_record_v1` re-checks the binding on reopen, because a stored record is still only bytes.

Binding 4 was originally weaker than that sentence claimed, and review caught it. `capture` used to take a free `source=` argument, so `capture(real_result, real_artifact, source="this is not WRL")` **succeeded** — and minted a sealed, internally consistent, entirely false `case-`. Verifying the report before accepting it found it slightly worse than stated: the counterfeit revalidated cleanly on reopen. The source now arrives only inside a `LoweredSourceEnvelopeV1 {source, source_sha256, lower_result, publisher, publisher_version}`, and **there is no `source=` parameter left**, so the crossed call cannot be spelled rather than merely being rejected.

The engine is deterministic (`lower_source` twice → byte-identical, matching the stored fixture), which makes something stronger than the sealed envelope available: `capture(envelope, artifact, lower=forge_api.lower_source)` **re-lowers the sealed source and requires it to reproduce the same `sem-`**. So a record records *how strong its own binding is* — `binding.kind` is `proved` (demonstrated here, engine injected) or `asserted` (inherited from whoever sealed the envelope), with the publisher named. It is stored, never implied, and `is_proved()` is a first-class predicate so a corpus builder can filter on it. Zero forge dependency survives: the engine arrives by injection, and the batteries prove the same path with a captured replay function over a finite domain — a real engine *is* a function from source to result, and a captured pool is that function restricted.

`taskbundle.make_task_for(record, …)` is then the blessed path, and it makes the scope ruling **mechanical** rather than merely stated: invalid source cannot become a record, so it cannot reach a `base_world` at all (R3c).

Battery `TRVM/wrlm/test_worldrecord.py` — **11/11**. R18 is the payoff: a serialized record reopens in a clean subprocess with no engine and no `sys.path` help and generates the byte-identical `task-` and `case-`. Verified additionally against the **live** engine (`forge_api.lower_source` at `v0.7.0-alpha.5`), which reproduces the frozen `sem-8ae91fe9…fe4a` and captures cleanly.

### The coverage policy — three things it refuses to do

A generator that maximises a coverage ledger produces exactly the corpus that ledger describes and nothing else. The ledger is therefore not bookkeeping; it **is** the specification of the training distribution, and it belongs somewhere it can be argued with. Three proposed dimensions were rejected, each for a reason that generalises:

| Rejected | Why it fails |
|---|---|
| `base_semantic_id` as a cell dimension | One cell per world is *identity* diversity, not semantic diversity. Two trivial renamings of one six-node topology land in different cells and look like progress; one rich world supporting twenty genuinely different tasks looks "full" after one. `sem-` is kept for reuse caps, split blocking and provenance — it just never gets to say what *diverse* means |
| declared `difficulty` as a cell dimension | The generator owns the label, so balancing on it is a closed loop: relabel the tasks, watch the ledger go green, change nothing about the population. `difficulty` survives as provenance, **derived from the tier so it cannot drift**. `tier` carries the contract instead, because a tier is derived and checked rather than asserted |
| one flat Cartesian cell | 2 families × 3 tiers × 4 sizes × 4 shapes × 4 budgets × 2 presentations = 768 cells *before* topology, roles, density or cycles. Nearly all would sit empty forever |

The ratified primary cell is `(family, tier, base_size_bucket, objective_shape, witness_edit_budget, presentation_form)`, with ~20 **secondary factors** measured by marginal and pairwise coverage rather than crossed into the cell — the standard combinatorial-testing move of using low-order interactions as a tractable stand-in for an unreachable full state space.

Every coordinate is **derived from the produced task and its base world, then compared with the cell that was requested**; a candidate whose derived cell disagrees is *rejected, not relabelled*. A cell that could be asserted would be a cell that could be faked, and a faked cell is a silently mis-shaped training distribution.

Two naming disciplines carried over from the `capture()` hole. `witness_edit_budget` is the length of the generator's constructive witness and is **not** called `minimal_edit_distance`, because minimality has not been proved. `base_shape_id` (1-WL colour refinement, renaming-invariant) is prefixed `shape-`, derives no other id, and is **not** a rung on the identity ladder. Its guarantee is deliberately one-sided — isomorphic worlds always agree, non-isomorphic worlds may also agree — so collisions **over-merge**, forcing distinct worlds to share a cap and a split. Under-merging would leak a world's twin across a split boundary, which is the failure it exists to prevent; over-merging only costs coverage.

`mentions_explicit_object_id` is measured from day one rather than discovered later: a corpus dominated by `id_is("p0")` goals teaches name-directed patching — find the string, edit near it — instead of structural reasoning. That is a plausible way to score well on this benchmark while learning nothing it was built to teach. Measured on the shipped corpus: **10 yes / 189 no**.

### Selection, and why the tie-break is hashed

Five deterministic phases: the `(family, tier)` partition furthest from quota **by ratio** (so a family with a large valid domain cannot swallow the corpus) → the cell in it with the largest deficit → **ties broken by `sha256(corpus_seed ‖ spec_version ‖ canonical_cell_bytes)`, never lexicographically** (a lexicographic tie-break permanently privileges whichever enum value sorts first and re-privileges it after every reset) → a bounded batch of candidates → the survivor adding the most new marginal and pairwise coverage, ties by lowest `case-`. That last step is the only place a `case-` tie-break belongs, for the simple reason that before it no case exists.

Only `accepted_unique` satisfies a quota. All **eight** outcome counters are retained, because *an under-covered cell* and *a generator that cannot inhabit the cell it claims* are opposite problems that look identical if you count only successes.

Train/validation/test are assigned on `base_shape_id`, not on `case-` and not on `sem-`: splitting by case lets a world and its own relabelling land on opposite sides, which is contamination with extra steps.

### What step 2 shipped

`coverage.py`, `families.py`, `generator.py`, plus `envelope.py` for the closure above and `tools/build_pool.py` — the **only** script that touches the engine, deliberately outside the package, run once to write `fixtures/pool.json` and `fixtures/pool_records.json` (**58 worlds**, all `binding=proved`).

Batteries: `test_worldrecord.py` 11/11 + `test_generator.py` **25/25 (R4–R17, R20–R29)**, R4–R17 first-run green. R5, R9 and R17 mechanize their rulings by **parsing** the module that states them — a law about a seam that is checked by string search is a law a comment can satisfy. R17 parses all 14 package modules for engine imports and additionally asserts `tools/build_pool.py` *does* import forge, so the separation cannot be satisfied vacuously by nobody importing forge anywhere.

Measured corpus (`corpus_seed = "seed-A"`, 58-world pool, quota 2, `wrlm.coverage.v1.2`): **527 accepted**, **298 of 320 cells inhabited (93%)**, 229 filled to quota, **quota mass 0.823**, splits 343/76/108, 0 duplicate `case-` accepted, 0 unsatisfiable, 0 invalid, 0 degenerate, 0 host faults. Byte-reproducible across runs and different under a different seed. (Earlier figures — 199 accepted over a 768-cell domain, then 201 over 320 — are kept below, because *why* they moved is the finding and the numbers are not.)

#### The gap, and the correction to what was first said about it

The first version of this section reported 664 empty cells, observed that emptiness was uniform across every coordinate, and concluded: *"the remedy is a larger pool, not a different cell."* **That conclusion was wrong**, and wrong in an instructive way. Uniformity across coordinates was measured with **marginal** coverage, and a marginal is exactly the instrument that cannot see a dead **combination**. Every coordinate *value* was indeed reachable. Most of the *combinations* were not reachable by anything.

`local` means one edit, nothing preserved, nothing ordered — and `derive_tier` calls precisely that combination tier 1. So `local × tier 3` is not a hard cell; it is a contradiction. Enumerating the two derivation functions over each family's own `(goal, preservation)` domain against realised witnesses gives the reachable set exactly, because those functions read nothing outside their arguments:

| | published | with a preimage |
|---|---|---|
| `target_transform` | 48 triples | **11** |
| `goal_satisfaction` | 48 triples | **29** |
| cells (× 4 sizes × 2 forms) | **768** | **320** |

**448 of the 768 published cells could never be inhabited by anything.** They were reported as under-coverage, which pointed at the pool for a fault that was in the domain. This is the ruling's own objection to cross-family shapes — *"not a sparse cell, a meaningless one"* — one level further down, and the module docstring had stated the principle while violating it.

`valid_cells()` now publishes the 320, and computes that set **by calling the derivation functions** rather than by carrying a table of them; a table would be a second statement of the tier contract, free to drift from the first. `WRLM_CELL_UNKNOWN` — declared in the first draft and never raised — is now what refuses a contradictory cell. `COVERAGE_SPEC_VERSION` moves to `wrlm.coverage.v1.2` (`v1.1` was the first narrowing; `v1.2` follows the ordering-predicate closure below): the fields are unchanged, but a version is what promises a seed reproduces a corpus, and a corpus is drawn from a domain.

**R22 is the check that makes the change safe to believe — and its second half had to be retracted.** The load-bearing half holds and is what justifies deleting 448 cells from the denominator: generating under both domains to saturation, *not one* of the removed cells was ever inhabited by either run, and narrowing never costs a cell (`in_wide ⊆ in_tight`).

The half that was retracted asserted **set equality**. That was true only while the corpus sat well inside the reuse caps, and widening the goal repertoire is what exposed it: with 226 cells now reachable instead of 104, `max_per_sem` and `max_per_shape` **bind**, and they are a *finite budget per `(family, tier)`* that the greedy selector spends in whatever order marginal deficits suggest. Padding the domain with 448 dead cells changes those marginal deficits, so the same budget lands on a different set — and the wide run reaches **one fewer live cell** than the tight one.

That is a stronger claim than the one it replaces: **a dead cell is not inert.** It does not merely dilute a ratio, it *displaces real coverage*. R22 now checks the inclusion and **reports** the displacement rather than asserting it away.

#### Step 2.1: widening the goal repertoire

`goal_satisfaction` had saturated at every pool size — the last eight worlds bought 2.4 cells — and the cause was legible in `propose_goals`: six rules, of which the conjunction rule always emitted exactly two `AddObject`s and the alternative rule exactly one, so `conjunction` could only ever land in budget `2` and `alternative` only in budget `1`, **at any pool size whatsoever**. The gap was measured before it was touched: the old repertoire reached **8 of the 29** `(tier, shape, budget)` triples the family's own domain admits, with the 21 missing triples enumerated by name. No quantity of captured worlds supplies a goal shape nobody wrote down.

Eight rules replace the six, each written against a named gap — `k` more of a role; `k` fewer (ordered exactly when a victim is wired); two counts at once (including the `(1, 0)` case: two requirements, one edit, the cheapest possible statement of *change this without breaking that*); new objects each wired; the same move asked over the *edge* sort so it cannot be solved by matching ids in the goal text; a costed alternative; an alternative whose cheap arm is a wiring; and a prohibition carried alongside a requirement. Every ordered rule gets its ordering the honest way — an edge cannot name an object that does not exist yet, and an object cannot be removed while an edge still names it — both refusals the engine's own seal makes, and both enforced by `apply_witness_step`.

The ruling's constraint was *"do not unlock budgets by padding witnesses."* Stating in a docstring that the proposer does not pad is worth nothing, because the proposer is the thing under suspicion. So `witness_is_minimal(view, goal, witness)` **executes every proper subsequence** against the same evaluator the generator scores with, and returns False if any shorter one already satisfies the goal (bounded by `MAX_WITNESS = 8`, so ≤2⁸ evaluations). **R28** runs it over every proposal the widened function emits across the whole pool; **R29** proves it is a predicate and not a constant by feeding it one deliberately useless appended edit.

Result: **29 of 29 triples reached**, 0 malformed, 0 unsatisfied by their own witness, **0 padded**.

#### Step 2.2: growing the pool, and a false plateau

Only after the widening did the pool become the binding constraint — exactly as the ruling ordered. `tools/build_pool.py` gains two generators: `strands()`, which makes a world a *multiset of chain lengths* (the original `chain()` varied how many objects there were and barely how they were arranged, so its worlds collapsed together under the 1-WL fingerprint `max_per_shape` caps on — twelve worlds sharing a shape are, to the cap, one world twelve times), and `neighbourhood()`, which emits a base world plus siblings at *deliberate distances*: 1 edit, 2 edits, 4 edits, a config bump, a relay spliced into a chain (ordered), a whole new strand (ordered, longer).

The siblings are the point. `target_transform` diffs **two** captured worlds, so its witness budget is not a property of either world — it is a property of the **pool's geometry**. A pool whose worlds are all far apart fills the `5-8` cells, leaves `1` and `2` empty at every size, and reports the emptiness as difficulty. Hence: *neighbourhoods, not specimens.*

The pool goes 21 → **58 proved worlds**. The original 21 records remain a **byte-identical prefix**, so every previously pinned `sem-` is unmoved.

**The marginal-coverage stop rule the ruling asked for is unsound as specified.** Measured at complete-neighbourhood boundaries:

| pool | inhabited /320 | `gs` /232 | `tt` /88 | at quota | quota mass | marginal |
|---|---|---|---|---|---|---|
| 30 | 262 | 194 | 68 | 108 | 0.578 | — |
| 39 | 266 | 198 | 68 | 168 | 0.678 | +0.44/world |
| 44 | 268 | 200 | 68 | 168 | 0.681 | +0.40/world |
| 53 | **296** | 220 | 76 | 219 | 0.805 | **+3.11/world** |
| 58 | **298** | 222 | 76 | 229 | 0.823 | +0.40/world |

A **global** stop rule fires at 39 and again at 44, and would have halted at 268 cells — after which the very next neighbourhood delivered **+3.11 cells/world and 28 more cells**. Coverage is a function of what *region* the pool reaches, not of pool *size*, so the rule has to be evaluated **per region** (`base_size_bucket` × family), never globally. The pool is 58 rather than the ruling's preferred 48 because a neighbourhood must be kept **complete** — truncating one mid-way is precisely what manufactures the false plateau — and the complete-boundary options were 30/39/44/53/58.

**Where the 22 remaining gaps are:** 14 of 22 sit in the `tiny` size bucket; by family, `target_transform` 12 and `goal_satisfaction` 10.

Step 2 and its two sub-steps are closed. Steps 3–10 remain paper only. Three findings are flagged for ruling: the unsound global stop rule, the displacement result that retired R22's set equality, and the 58-vs-48 overshoot.

Proposed object set: ~~`TaskBundleV1`~~ (shipped), ~~`WorldRecordV1`~~ (shipped, added to the set), `ProposalV1`, `CandidateWorldV1`, `TargetSpecV1`, `GoalSpecV1`, `ProducerFactV1`, `EpisodeReceiptV1`, `EvaluationReportV1`, `AdmissionDecisionV1`, `InteractiveEpisodeKernelV1`.

---

## 11. Open items

- **PRISM is excluded.** Its judging path is LLM-mandatory (`judge/rubrics.ex`, `dimension_worker.ex`, `meta_judgment.ex`; no programmatic judge exists), which is architecturally opposed to WRLM's thesis. Dependency flows **TRAAVIIS → PRISM**, not PRISM → TRAAVIIS. Two pieces remain salvageable if their procedure, algorithm version and seed are sealed: `judge/aggregator.ex:102–129` (bootstrap CIs, 1000 iterations). `irt/model.ex` is **not** salvageable at this n (§6). Note `PRISM/lib/prism/leaderboard/leaderboard.ex` is entirely stubbed and has no regression detection.
- **Hardware is not on the critical path.** WRLM-0 is a hosted-model evaluation under a $20–50 cap. No purchase is required or implied. (Intel Arc Pro B65/B70 are real and shipping — an earlier "probable fabrication" flag was wrong and is retracted; an internal contradiction is evidence of staleness at least as often as fabrication.)
- **Not yet decided:** which model family fills the frontier reference cell; task-family gating table for `S`; whether `InteractiveEpisodeKernelV1` is a distinct kernel or a mode of `EpisodeKernelV1`.
