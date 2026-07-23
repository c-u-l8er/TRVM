# Forge Semantic IR v1 — MEASURE (pre-freeze memo)

*Status: **MEASURE only — NOT frozen.** This is the "measure before building" artifact for WRL Phase 2 (freeze Forge Semantic IR v1). It inventories the IR vocabulary the forge lowering has ALREADY grounded, maps the frozen WRL Core 0.1 families onto it, and isolates the open freeze-decisions that need a GPT-5.6 ruling before anything is frozen.*

Per the WRL architectural rule: WRL Core → **Forge Semantic IR** → TRVM facts/films/reductions. WRL surface text never lowers directly to interaction-calculus text. IR v1 is that middle layer. This memo measures what it must contain.

---

## 1. What is already grounded (the de-facto IR)

The forge lowering (`fixture.py` → `compiler.py`/`lower_e2a.py`/`admit_ic.py` → IC) already consumes a structured graph description and a per-epoch input. That structure IS a proto-IR. Measured surface:

### 1.1 Node kinds (5, closed today)
| Kind | Params | Grounded in |
|---|---|---|
| `pulser` | clock mode: `("periodic", period, phase)` \| `("once", epoch)` | fixture.py; native "once" since proc-e2.3 |
| `relay` | — (sig_out; or-merge sig_in) | e2_model / lower_e2a |
| `door` | — (gate; sig_in) | lower_e2a |
| `spinner` | lane geom `(w, n)`, init `rotor4`, `configurable` permission | 3b.5a/3b.5d-2 |
| `orb` | — (holds pose4 + sticky numeric-fault bit) | 3b.5c/3b.5d-2 |

### 1.2 Ports + edge kinds (2 edge kinds, closed today)
- `OUT_PORTS = {pulser: sig_out, relay: sig_out, spinner: socket}`
- Receiving ports: `sig_in` (door/relay/spinner), `pose` (orb).
- `LEGAL_PAIRS = {(sig_out, sig_in), (socket, pose)}` → **two edge kinds**: **sig-wire** and **socket**.
- Constraints frozen in fixture schema: spinner needs exactly one sig-in + one socket; orb controller exclusivity (≤1 socket).

### 1.3 State schema (per-node field shapes)
- counters: one-hot Scott enum (period ≤ 32) or binary ripple counter — same semantics (Binding Law 5).
- wire: `cur` / `nxt`; door: `open` / `next_open`; relay: `cur_out` / `next_out`.
- spinner: `rotor` as **runtime STATE** (Q32.32 lanes), permission fixed\|configurable.
- orb: `pose4` + authoritative **sticky** `numeric_fault` bit.

### 1.4 Epoch input (ADMIT layer)
- Input = batch of typed **prehashed claim envelopes** `SetRotor(spinner, rotor4)` \| `ResetFault(orb)`.
- Reducer output = **EpochControl** = `TUP(rotor_bundle, fault_bundle)` = per-spinner `NoChange|SetRotor(rotor4)` + per-orb `KeepFault|ResetFault`.
- Claim state = bounded sorted **fact vector** + separate immutable **receipt vector** (Option A occupied-prefix sorted); CandidateKey identity.

### 1.5 Transition law + observability
- Per epoch `t`: **ADMIT → COMMIT (rotor writes + fault resets) → REACT (token cascade) → latch overflow → FILM**.
- Identity: content-addressed rulepack hash; oid↔role binding; CandidateKey for claims.
- Film: **v0.6** (physical: rotor-as-state, spinner permission, orb sticky fault) / **v0.7** (claim-aware: policy id + facts + receipts/outcomes + recognition + capacity faults).

---

## 2. WRL Core 0.1 family → IR vocabulary map

| WRL Core family | Forge IR grounding | Coverage |
|---|---|---|
| Actor `[x]` (identity) | 5 node kinds (pulser/relay/door/spinner/orb) | GROUNDED (concrete) |
| State `(x)` | §1.3 state schema | GROUNDED |
| Wiring `{x}` | edges (sig/socket) + ports + permission | GROUNDED |
| Route: solid `--` | sig-wire deterministic delivery | GROUNDED |
| Route: verified `==` | ADMIT accepted receipt / COMMIT | GROUNDED |
| Route: fault `!!` | numeric_fault latch | GROUNDED |
| Route: async `~~` | mailbox append | **NOT grounded** (no mailbox node yet; ADMIT batch is the only async-ish input) |
| Period | epoch `t` + COMMIT/REACT phases | GROUNDED |
| Film | film_bytes_v6/v7 | GROUNDED |
| Hash / content-id | rulepack hash + CandidateKey | GROUNDED |
| Fact-merge union | claim-fact SET UNION | GROUNDED |
| Boundary gate/commit/seal | COMMIT (rotor writes) + acceptance receipt + ADMIT gate | PARTIAL (commit grounded; explicit `/gate` capability node + `///seal` artifact registry not yet a node kind) |

**Reading:** 10 of 12 Core families are grounded by the concrete forge vocabulary. Two are not: **async route/mailbox** and **explicit capability-gate / seal boundary nodes**.

---

## 3. Open freeze-decisions (need a GPT-5.6 ruling)

These are the genuinely undecidable-without-authority questions. Each has a recommended option, but freezing is high-commitment and prior IR/spec freezes all went through GPT-5.6.

**D1 — Abstraction level of the node vocabulary.**
WRL Core says *Actor* is ONE kind; forge has FIVE concrete kinds. Is IR v1 frozen at the **concrete** layer (pulser/relay/door/spinner/orb as IR primitives) or the **abstract** layer (one `Actor` primitive parameterized by a behavior/state schema, with the 5 as library prefabs)?
*Recommendation: freeze CONCRETE (the 5 grounded kinds are what actually lower + film; an abstract actor is Experimental until a second instantiation exists).*

**D2 — Edge vocabulary closure.**
Freeze **2** grounded edge kinds (sig-wire, socket) or reserve all **4** WRL route textures (adding async `~~` + fault `!!` as declared-but-unlowered)?
*Recommendation: freeze 2 as IR-normative; RESERVE async/fault names as declared-only (no lowering), mirroring how WRL.md reserves undefined forms.*

**D3 — Is ADMIT graph structure or epoch input?**
Currently claims/receipts/EpochControl are a per-epoch INPUT, not graph topology. Does IR v1 (a) keep ADMIT as a separate "epoch-input IR" beside the graph IR, or (b) fold claim/receipt vectors into node state?
*Recommendation: (a) — keep the graph IR (durable topology + state schema) separate from the epoch-input IR (batch → EpochControl). They have different lifetimes; conflating them re-introduces the merge problem the ruling warned about.*

**D4 — State schema: part of IR v1 or a sidecar?**
Per-node field shapes (Q32.32 rotor, sticky fault, one-hot/binary counter) — frozen INSIDE IR v1 as each node kind's typed state signature, or a separate versioned "state schema" so representation (Law 5) can evolve without rev'ing the IR?
*Recommendation: freeze the state SIGNATURE (field names + semantic types) in IR v1; leave REPRESENTATION (one-hot vs binary, lane width) to a sidecar (Law 5: representation ≠ meaning).*

**D5 — Scope: freeze now, or after a second grounded instantiation?**
IR v1 would freeze on a SINGLE grounded instantiation (the E2a circuit + SetRotor/ResetFault ADMIT). Freeze v1 now on that basis, or hold until a second, structurally different graph is lowered (to avoid baking in E2a-specific shape)?
*Recommendation: this is the crux for GPT-5.6. Freezing on one instantiation risks over-fitting; waiting delays the sanctioned lowering target. Prior discipline ("measure before building", finite-before-open-ended) leans toward: freeze a **minimal v1 core** (D1 concrete + D2 two-edge + D3 separate + D4 signature) explicitly SCOPED to the grounded surface, versioned so a second instantiation drives v1.1 — rather than a speculative general IR.*

---

## 4. Recommendation summary (for ruling)

Freeze **Forge Semantic IR v1** as a MINIMAL, grounded-only core:
- 5 concrete node kinds (D1), 2 edge kinds + 2 reserved route names (D2),
- graph IR separate from epoch-input IR (D3),
- typed state signatures with representation as a sidecar (D4),
- explicitly scoped to the single grounded instantiation, versioned for a second (D5).

**Halting for GPT-5.6 on D1–D5 before writing the frozen `FORGE_SEMANTIC_IR_v1.md`.** No freeze is committed until these are ruled.
