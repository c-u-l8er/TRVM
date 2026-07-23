# TRVM Forge — Stage One: The Canvas

**Spec v0.3 · Single-GPU, single-player forge canvas on the native TRVM stack · ARCHITECTURE FREEZE after this revision, pending E1/E2 data**

**Changelog v0.2 → v0.3** (integrating GPT 5.6 review round two — same-epoch contention): (1) the epoch is now a **phased protocol** — ADMIT → COMMIT → REACT → HASH — with phase tokens as net agents; this closes the gate-reset race, and goes one step past the review's double-buffer suggestion because double-buffering alone leaves a commit/deliver interleaving race; (2) **typed fan-in law**: every stateful input port declares its merge — SPIN declares none (single wire), GATE declares Boolean OR — and links type-check against it; (3) **authoritative event sequencing** is part of the transition function: `state[t+1] = step(state[t], ordered_inputs[t])`, canonical seq order, sequential admission inside step, and a new rule giving dangling-target events a defined fate; (4) **two-level identity**: `body_hash` (canonical subnet) vs `artifact_id` (domain-separated whole-artifact hash); (5) **structural tariffs** replace execution-measured graft cost; (6) an explicit **ranking function** backs the per-epoch finiteness claim, with template-validator obligations; (7) harness boundary restated as the step-function contract; (8) rule count 15 → **18** as phase tokens and the dangling-target rule become explicit; (9) E2 split into **E2a** (epoch mechanics) and **E2b** (critical-pair battery); (10) Marble revised to "cheap to begin, not cheap to finish."

**Changelog v0.1 → v0.2:** logical epochs replace interaction-count time; unit-delay wires; rules as active pairs plus declared harness; fixed-point authority separated from representation (Motor8/MV16, E1); PN-counter declared single-authority with stage-three escrow; canonical serialization tie-breaks; E1–E3 gate M2; first-build rephrased as construction toy; the Marble named for stage two.

This document specifies the first shippable slice of the native TRVM game system: a Forge-style canvas where a player in monitor mode stamps, grabs, links, and deletes prefab objects in an SDF world, spends beta from a budget, toggles into play mode to watch the net run, and records/replays deterministic films. Architecture as agreed: TRVM reduction as the only simulation authority, CUDA as accelerator with the C runtime as semantic ground truth, SDF raymarching as renderer, minimal GL-interop present layer. No third-party engine.

---

## 0. Scope and success criteria

**In scope:** monitor camera and picking; eight-object starter palette; stamp/grab/rotate/delete/link verbs; beta budget with HUD; `.tfp`/`.tfm` formats with two-level identity; phased logical epochs; EDIT / PLAY / THEATER; snapshot-ring undo; deterministic films; the eighteen-rule alphabet plus step-function harness; conformance including the critical-pair battery; experiments E1–E3.

**Out of scope (deliberately):** multiplayer and networked boundary ports (stage three — opcodes reserved), gametype packs beyond default, audio, non-NVIDIA backends, mesh assets, terrain, math curriculum content, and — named — an embodied player, collision response, gravity, goals. **Stage one is a deterministic computational construction toy, not yet a game.** Stage two's headline is **the Marble**: an embodied PGA rigid body `(M, B)` on the SDF world. The distance field supplies detection and contact normals nearly free; it does not supply a solver — resting contact, friction, restitution, substepping against tunneling, and deterministic fixed-point motor renormalization are real work. Cheap to begin, not necessarily cheap to finish; still the right stage-two feature, because it converts every existing ramp, pipe, spinner, door, and Blender build into gameplay at once.

**Stage one is done when:**

1. 1920×1080 at 60 fps sustained on RTX 4090-class with 1,000 placed objects; 30 fps floor at dynamic resolution on a laptop 4060 — *contingent on E3; renegotiated before M2 if E3 fails, not after M5.*
2. A recorded film (map `artifact_id` + S0 + per-epoch ordered input log + checkpoint hashes) replays on a fresh process, and on the CPU-only build, to bit-identical per-epoch canonical hashes.
3. Budget invariants (§7) hold under 10⁶ fuzzed edit events.
4. Undo restores a canonical hash identical to the pre-edit hash, to ring depth 64.
5. CPU reference and CUDA pass the eighteen-rule battery **and the critical-pair battery (§11 `conf.pairs`)** with identical per-epoch hashes on randomized nets, budgets, and schedules.
6. First-build test: a new user builds a small kinetic arena containing a clock-operated door in under ten minutes using only on-screen affordances.

---

## 1. Frame loop and mode scheduling

Authoritative time is the epoch counter `t`. Interactions are cost; epochs are time.

```c
while (running) {
    poll_events(&evs);                     // GLFW; verbs encode to events (§6)
    enqueue(evs);                          // seq-stamped at encode time
    time_debt += dt;
    while (time_debt >= EPOCH_DT && mode_advances_time(mode)) {
        step(vm, t, take_inputs_for(t));   // §8: the phased transition function
        time_debt -= EPOCH_DT; t++;
    }
    trvm_readback_scene(vm, &scene);
    cuda_raymarch(interp(scene, alpha), pbo, &idbuf);
    hud_compose(&hud_state);
    gl_present(pbo);
}
```

`EPOCH_DT` defaults to 1/30 s. Rendering interpolates motors between epochs t−1 and t. If an epoch cannot finish within budget, **simulation time dilates deterministically** — the world slows; it never diverges. EDIT: `t` advances only via immediate single-event edit epochs. THEATER: epochs driven by the film log. Randomized-budget conformance requires identical per-epoch hashes regardless.

**The harness contract (v0.3 wording):** the harness may choose *when* to invoke `step` and may render its output; it may never change the result of `step(state, ordered_inputs)`. Camera, palette selection, pause timing, and rendering live outside `step`. Event admission order, clock emission, latch commits, and all world mutation live inside it. Films log which epochs ran and their ordered inputs, so the harness's scheduling choices are reproduced exactly. Corollary (kept as a CI check): nothing outside `step` may influence a per-epoch canonical hash.

---

## 2. Numeric policy

**Irreversible invariant: fixed-point authority.** No float is ever authoritative state; floats exist only in derived render buffers, converted once per frame, one direction.

Working representation (settled by E1): stored pose is **Motor8** — eight even-grade PGA lanes as `i64` **Q32.32** (64 bytes); **MV16** is a transient kernel type only. Products use 64×64→128-bit intermediates, truncation-toward-zero, saturation on overflow, specified for CPU/CUDA bit equality (`conf.mv16`). Narrowing after E1 is a format-version bump; float creep into authority is forbidden regardless. Beta and counters are `u64`.

---

## 3. Data model

### 3.1 Node layout

Uniform HVM2-style cells: 4-port nodes of tagged 64-bit words (8 bits kind, 8 bits aux, 48 bits addr/immediate). Payloads (Motor8, params) live in side tables indexed from cells. Reserved kinds: `BND`, `RULEPACK`.

### 3.2 Agent alphabet

| Kind | Ports | Payload | Meaning |
|---|---|---|---|
| `OBJ` | shape, pose, sig_in, sig_out | Motor8 pose, stable id | one placed object instance |
| `PRIM` | parent | shape_id + params | SDF leaf: box, wedge, sphere, capsule |
| `UNION` / `SUNION` / `DIFF` | parent, a, b | k | CSG interior nodes (inert in stage one) |
| `CLK` | phase_in, out | period N, phase, armed | fires when t ≡ phase (mod N) |
| `SPIN` | sig_in, socket | Motor8 rotor R | merge policy: **none** (single wire) |
| `GATE` | sig_in, body | open, next_open | merge policy: **OR** (fan-in legal) |
| `WIRE` | src, dst | cur, next | unit-delay edge; single src by construction |
| `COMMIT` / `REACT` | broadcast | t | **phase tokens** (§8) |
| `ASK` / `GRANT` / `REL` | routing | cost, tpl, motor | budget request / approval / refund |
| `BUDGET` | — | cap, P, N | PN-counter: spent = P − N (§7) |
| `EV_*` | varies | ≤64 B, seq u64 | input events (§6) |
| `PAL` | — | prefab artifact table | loaded palette manifest |

### 3.3 The rule alphabet (eighteen active-pair rules)

All world semantics are active pairs lowering to the TRVM calculus (Option A; E2 is the gate, Option B the declared fallback). The count grew 12 → 15 → 18 as hidden steps became explicit — that trend is the review process working, not scope creep.

**ADMIT-phase rules (event handling; events admitted one at a time in seq order):**
1. `EV_STAMP × PAL` → `ASK(cost, tpl, motor)`
2. `ASK × BUDGET` → `GRANT` (and `P += cost`) when `P − N + cost ≤ cap`, else `REJECT`
3. `GRANT × TPL` → graft: α-renamed closed template copy at the motor (bounded by rule 18)
4. `EV_DELETE × OBJ` → ERA subnet + `REL(cost)`
5. `REL × BUDGET` → `N += cost`
6. `EV_MOVE × OBJ` → pose′ (grid snap = exact lane quantization)
7. `EV_ROTATE × OBJ` → pose ← R ∘ pose
8. `EV_LINK × (portA, portB)` → `WIRE` iff types match **and** the destination's merge policy admits another writer (SPIN: port must be empty; GATE: always), else `REJECT`
9. `EV_* × ∅` (stable id no longer resolves) → `REJECT` (logged; the defined fate of dangling-target events)

**COMMIT-phase rules (latch commits; no emissions, all pairwise-disjoint state, order-free):**
10. `COMMIT × WIRE` → `cur ← next; next ← 0`
11. `COMMIT × GATE` → `open ← next_open; next_open ← 0`
12. `COMMIT × CLK` → `armed ← (t ≡ phase mod N)`

**REACT-phase rules (deliveries and reactions; writes target epoch t+1 or single-writer state):**
13. `REACT × WIRE` → emit `SIG` to dst iff `cur` high
14. `REACT × CLK` → emit `SIG` into out-wire iff armed
15. `SIG × WIRE` → `next ← 1` (visible at t+1, never t)
16. `SIG × SPIN` → socketed pose ← R ∘ pose (single writer by rule 8)
17. `SIG × GATE` → `next_open ← next_open ∨ 1` (idempotent, commutative — fan-in safe)

**Structural:**
18. `DUP / ERA` bookkeeping for graft copy and erasure

**Per-phase determinism argument (the shape of the E2 claim):** ADMIT is sequential by construction. COMMIT rules touch disjoint per-agent state and commute. REACT is single-writer everywhere except `GATE.next_open`, whose merge is OR — idempotent and commutative. Each phase is therefore order-independent and quiesces (§8 ranking function), so `step` is a function. Pulse→door latency is two epochs (one per stateful hop: wire, then gate) — every element adds one tick, which is the teachable model.

**The harness (not rules):** camera, palette selection, mode, epoch scheduling, snapshot capture, HUD, the REJECT mailbox. Governed by the §1 step contract.

### 3.4 Scene readback

`trvm_readback_scene` walks OBJ roots into SoA buffers: `object_table[4096]` (csg_offset, motors for t−1 and t as f32×8, flags incl. GATE-open), `csg_nodes[16384]`, `prim_params[]`, `hud_state`. Caps hit → `REJECT`, not UB.

---

## 4. File formats and two-level identity

```
[header 64B]  magic "TFP1"|"TFM1" · format version u16 · numeric_policy ·
              rulepack_hash · port signature hash · beta_cost (tfp) | beta_cap (tfm) ·
              body_sha256
[manifest]    identity fields: exposed port types; tfm: palette artifact_ids,
              spawn motor, bounds, cap
              non-identity metadata: name, author, preview
[body]        canonical TRVM wire serialization
```

**Canonical serialization** (unchanged from v0.2, restated): BFS from the distinguished root; children in ascending port-index order; ids in first-visit order; back-edges as visited-id refs; frontier ties by (kind tag, discovering-parent id, discovering port index); side tables in first-reference order; payload lanes big-endian two's-complement. Isomorphic nets → identical bytes (`conf.canon`).

**Two hashes, two claims:**

```
body_hash   = SHA256(canonical body bytes)
artifact_id = SHA256(domain_sep ‖ format version ‖ numeric_policy ‖
                     rulepack_hash ‖ port signature ‖ beta_cost/cap ‖
                     semantic manifest fields ‖ body_hash)
```

Same `artifact_id` ⇔ same executable artifact. Same `body_hash` ⇔ same canonical subnet body. Both are structural, not semantic, identity — two differently structured prefabs may behave identically and hash differently; acceptable, and for stage one preferable. Palette references, film headers, and dedup key on `artifact_id`; body-level dedup may additionally use `body_hash`. Missing `artifact_id` on load prompts for the file — no silent substitution. Name, author, preview are non-identity metadata by design.

**Template validity (export-validated, load-revalidated):** a `.tfp` body is a closed finite subnet — no dangling ports, no references to other prefab artifacts (flattened at export), no self-reference. The validator's proof obligations back rule 18's boundedness (§8).

**Structural tariff (replaces execution-measured cost):**

```
cost = T_node·nodes + T_edge·edges + T_payload·⌈side_bytes/64⌉ + T_graft
```

Constants live in the rulepack and are covered by `rulepack_hash`, so cost is reproducible from bytes alone, never from a trusted prior run. Stage-one constants: T_node=4, T_edge=1, T_payload=1, T_graft=8.

---

## 5. The eight starter prefabs

| # | Name | SDF recipe | Ports (merge) | Cost (β) | Why |
|---|---|---|---|---|---|
| 1 | Block | box | pose | 10 | the atom of forging |
| 2 | Ramp | box ∩ half-space | pose | 12 | slopes and flow (sculptural until the Marble) |
| 3 | Orb | sphere | pose | 10 | landmark; physics later |
| 4 | Pipe | capsule | pose | 12 | rails, frames, bridges |
| 5 | Blender | SUNION field, radius k | pose | 25 | smooth-min as clay |
| 6 | Spinner | pedestal + socket | pose, socket, sig_in (**none**) | 40 | rotor on signal; hold-to-tune; one wire in, ever |
| 7 | Pulser | small emitter | pose, sig_out | 30 | clock, period in epochs |
| 8 | Door | Block + GATE | pose, sig_in (**OR**) | 35 | two plates, one door — fan-in works because OR is free; its two-tick latency is the first physics lesson nobody announces |

Default map cap **1000 β**; deletion refunds 100%; costs and cap live in the `.tfm` header (tariff-derived, rulepack-versioned).

---

## 6. Monitor input grammar (edit mode)

Picking is free: the raymarcher's per-pixel nearest-object `idbuf` is the picker (one-pixel async read).

Every verb encodes to `{opcode u16, seq u64, payload}` ≤ 64 bytes. `seq` is assigned monotonically at encode time and is **authoritative**: `ordered_inputs[t]` is the seq-sorted batch for epoch t, admitted one at a time inside `step` (§8). In EDIT, exactly one event is admitted per edit epoch, so ordering is trivial; the sequencing law exists so PLAY-mode batches and stage-three multi-writer input (seq becomes ⟨lamport, player⟩) inherit defined semantics rather than host accidents. The interface proposes events; reduction disposes.

| Input | Verb | Event |
|---|---|---|
| WASD + mouse, Shift, wheel dolly | fly monitor | none (harness) |
| `Tab` | EDIT ↔ PLAY (hold: THEATER) | harness; logged as epoch annotation |
| `1..8` / Ctrl+wheel | palette slot | none (harness) |
| LMB (empty hit) | stamp ghost → place | `EV_STAMP{artifact_id, motor}` |
| LMB hold (object) | grab; wheel push/pull | `EV_MOVE{id, motor}` on release |
| `R` + drag (grabbed) | rotate about camera axes | `EV_ROTATE{id, rotor}` on release |
| `G` | grid snap toggle | affects quantization of next `EV_MOVE` |
| `X` / `Del` | delete (full refund) | `EV_DELETE{id}` |
| `L`, pad → pad | link; pads glow; illegal fan-in shakes | `EV_LINK{idA,portA,idB,portB}` |
| `Ctrl+D` | duplicate selected | `EV_STAMP` same artifact_id + offset motor |
| `Z` / `Shift+Z` | undo / redo | snapshot ring (§9), not an event |
| `Ctrl+S` | save map | canonical serialize → `.tfm` |
| `F` | frame selected | camera only |

Ghosts render in the raymarch pass; a ghost turns red when the spend would exceed cap (UI pre-flight; rule 2 is the only authority). A link attempt into an occupied SPIN port shakes and shows the existing wire — the fan-in law taught by refusal.

---

## 7. Budget

One `BUDGET` node: `{cap, P, N}`; rule 2 spends, rule 5 refunds; `spent = P − N`. **Invariants (tested):** per-prefab lifetime refunds ≤ spends; `0 ≤ P − N ≤ cap` at every epoch boundary; Σ live-object costs = `P − N` exactly; delete emits exactly one `REL`; duplicate-then-delete yields no double refund and no dangling clone (both in `conf.pairs`).

Because ADMIT is sequential in seq order, two `ASK`s against remaining cap 10 resolve by law: **lower seq wins**, the second `REJECT`s. Not a race — a rule.

**Stage-three warning (unchanged, load-bearing):** a PN-counter is single-authority-only; it converges under merge but does not preserve a shared cap under disconnected concurrent spending (80 + 80 against cap 100 merges to a "valid" 160). Replicated budgets require **escrowed spending rights** — bounded-counter CRDTs with per-participant allocations summing to cap and exactly-once rights transfer over boundary ports. Natural attachment point for the trust layer: who is *recognized* as holding which portion of beta is a recognition question, not a counter question.

HUD (thin GL overlay, glyph atlas, ~300 lines): beta bar `spent/cap`; palette cost tags; mode chip; undo pips; epoch counter `t`; interactions-per-epoch ticker (score and telemetry, never time).

---

## 8. The phased epoch: `step`, formally

```
state[t+1] = step(state[t], ordered_inputs[t])

step:
  ADMIT   for each event e in ascending seq:
              inject e; drain to quiescence          // rules 1–9
  COMMIT  inject COMMIT(t) broadcast; drain          // rules 10–12; no emissions
  REACT   inject REACT(t) broadcast; drain           // rules 13–17; writes target
                                                     // t+1 or single-writer state
  HASH    if t % K == 0: record canonical_hash
```

Drain-to-quiescence uses the C-ABI termination hooks (`trvm_is_idle`) — doing exactly what they were designed for. Phase tokens are net agents; the harness's only role is injecting the next phase token at quiescence, which is part of step's definition, not discretion (§1 contract).

**Ranking function (the finiteness claim, made explicit).** Define, lexicographically:

```
M = ⟨ remaining phases,
      W₁·|pending events| + W₂·|pending phase tokens| + W₃·|pending SIG|
    + W₄·(graft work) + W₅·(erasure work) ⟩       with W₁ ≫ W₄ ≫ W₂ > W₃ > W₅
```

Every rule strictly decreases M: rules 1–9 consume an event token (rule 3 converts one `GRANT` into graft work equal to the template's node count — a bounded exchange, W₁·1 → W₄·n with the template finite by the §4 validator); rules 10–14 consume phase tokens (each broadcast fans out to at most the live-agent count, then each per-agent token is consumed); rules 15–17 consume a SIG; rule 18 decrements graft or erasure work per cell touched. Unit delay guarantees REACT creates no same-epoch SIG cycles. Quiescence per phase follows; a per-epoch interaction ceiling enforces it anyway, and a breach is a hard conformance fault, never a silent hang. The validator's obligations — templates closed, finite, flattened, non-self-referential — are what keep rule 3's exchange bounded; a malformed prefab is rejected at export *and* at load.

**Modes.** EDIT: single-event edit epochs (crisp undo boundaries). PLAY: scheduler runs epochs at `EPOCH_DT`; entry pushes `S0` and opens a log segment; exit closes it; the evolved world persists, *Reset to S0* offered, never forced. THEATER: a film `{map artifact_id, S0, per-epoch ordered inputs, checkpoint hashes}` drives epochs. Film time is the epoch index; playback is identical across frame rates, GPUs, and backends because each phase is order-independent and hashed canonically — no reduction schedule pinned, none needed. Scrub restores the nearest checkpoint and re-runs. Replay hash mismatch = hard assert with state dump: the desync debugger, day one.

---

## 9. Snapshot ring

64 snapshots via `trvm_snapshot`, pooled (≤8 MB each). Pushed at mutating epoch boundaries — stamp, delete, link, grab-release, PLAY entry — never mid-grab. Undo = restore; redo = forward; new edit truncates redo. Same machinery backs `S0`, theater checkpoints, crash recovery: one mechanism, four features.

---

## 10. Rendering and picking

Sphere tracing over a uniform grid of object AABBs (E3 verifies; BVH deferred). One soft-shadow ray, cheap AO, dynamic resolution. Motors interpolate t−1 → t. Outputs: color PBO + `idbuf`. GATE-closed bodies drop out of SDF evaluation — a door opening is the world's distance field changing. Style: flat emissive palette, holo ghosts, glowing port pads; the per-epoch ticker modulates ambient pulse.

---

## 11. Conformance battery

`conf.rules` — 1,000 randomized nets over the eighteen-rule alphabet, randomized budgets/schedules → identical per-epoch hashes CPU vs CUDA.
`conf.pairs` — **the critical-pair battery (E2b, permanent):** two stamps vs remaining budget (lower seq wins); move+rotate same object (seq order); move+delete (seq order; late event → rule 9 REJECT); link+delete (ordered or deterministic REJECT); two signals → gate (OR); two signals → spinner (illegal by rule 8; link-time REJECT verified); commit vs gate signal (phase separation); commit vs wire write (writes target t+1); delete+refund (exactly one REL); duplicate+delete (no double refund, no dangling clone). Every case × randomized reducer schedules → identical canonical epoch hash.
`conf.epoch` — E2a as a permanent test: coprime clocks, spinner, gate, feedback loop; 10⁵ epochs, randomized budgets/schedules → identical hashes; the feedback loop blinks at exactly 1-epoch granularity forever.
`conf.rank` — fuzz for ranking-function violations: per-epoch interaction ceiling never breached across randomized worlds; malformed/recursive templates rejected at export and load.
`conf.mv16` — fixed-point product bit-equality CPU vs CUDA, 10⁷ values, overflow/saturation edges.
`conf.budget` — 10⁶ fuzzed sequences → §7 invariants at every boundary.
`conf.graft` — same artifact_id instantiated 1,000× → isomorphic copies; cost equals tariff.
`conf.canon` — 10⁴ random nets, permuted layouts → byte-identical serialization; cycles and side tables included.
`conf.ident` — header perturbations (rulepack, numeric policy, port signature, cost) change `artifact_id` while `body_hash` is unchanged; body perturbations change both.
`conf.undo` — random edit walks + undo/redo interleaving → hash equality with a model interpreter.
`conf.film` — record randomized sessions → replay fresh process → replay CPU-only build → all checkpoint hashes match.
`conf.pick` — idbuf vs CPU ray trace, 10⁴ scenes/rays.

---

## 12. Experiments, milestones, risk

**E1 — numeric kernel bench (gates §2).** Motor8 composition and sandwiches, CPU vs CUDA: ops/sec, registers, bandwidth, overflow rates; Q32.32 vs Q16.16 vs Q48.16. Output: lane width and the Motor8/MV16 boundary.
**E2a — epoch mechanics (gates §8).** Coprime clocks, spinner, gate, feedback loop on the real reducer; 10⁵ epochs, randomized budgets/schedules → identical hashes.
**E2b — critical pairs (gates §3.3 and the Option A/B fork).** The `conf.pairs` table, every case, randomized schedules. Output: identical hashes, or a documented move to Option B (a typed deterministic graph machine beside the calculus — adopted explicitly, never slid into). E2a+E2b together decide whether the model is *deterministic*, not merely confluent.
**E3 — renderer ceiling (gates §0.1).** 1,000 independent SDF objects, then connected CSG, with picking, AO, one shadow ray, before TRVM integration.

| Milestone | Content | Risk share |
|---|---|---|
| M0 | window + GL PBO + CUDA blit | 5% |
| M1 | raymarch hardcoded scene, camera, idbuf picking | 15% |
| **M2** | **GPU TRVM heap, eighteen-rule reducer, phased step, readback→scene; Pulser→Spinner animates** | **40%** |
| M3 | edit verbs + BUDGET + HUD; ten-minute first-build | 15% |
| M4 | formats, two-level identity, save/load, tariff stamping | 10% |
| M5 | snapshot ring, films, theater scrub; `conf.film` green cross-backend | 15% |

**M2 is the project**; E1–E3 make it an integration milestone rather than a research gamble. **Architecture freeze is now in effect:** no further semantic revision until E1/E2a/E2b return data. The next document produced should be experiment results, not spec v0.4.

---

## 13. Open decisions (owned by E1/E2, not by further spec rounds)

Lane width and Motor8/MV16 boundary (E1). Epoch rate 30 vs 60 (feel vs headroom). Checkpoint stride K. Blender radius per-instance (current pick) vs global. Grid snap default 0.25. `EV_MOVE` release-only (current pick) vs streamed. Unit delay universal (current pick: yes; zero-delay wires resisted indefinitely — they reopen intra-epoch cycles). Whether GATE-style OR fan-in should extend to a future combiner prefab family rather than more built-in merges (current lean: combiner prefabs, keep the merge lattice tiny).
