# Forge Semantic IR v1 — FROZEN

*Status: **FROZEN** (2026-07-21), per GPT-5.6 ruling. Profile: `forge.world.core.v1` — the **deterministic-circuit-world** profile. This is the sanctioned lowering target for WRL Core 0.1.1. WRL surface text NEVER lowers directly to interaction-calculus text; it lowers to this IR, which lowers to TRVM facts/films/reductions.*

**Scope statement (normative).** IR v1 defines static deterministic signal graphs containing the five built-in roles, persistent numeric/pose state, bounded ADMIT claim state, and the two grounded topology relations. It does **not** define mailboxes, arbitrary actor behavior, dynamic topology, fragments, capabilities, supervision, or distributed settlement. Any construct outside this scope MUST produce a clear unsupported-feature diagnostic, never a speculative lowering.

Predecessor: `FORGE_SEMANTIC_IR_v1_MEASURE.md` (the pre-freeze measure). Frozen core: `WRL_CORE_0.1.md` (rev 0.1.1). This freeze resolves decisions D1–D5 as ruled.

---

## 0. Three layers (D3)

IR v1 is three artifacts with three lifetimes. They are never conflated.

```
ArtifactIR (static)  +  RuntimeState (persistent)  +  EpochInput (per-epoch)
    → RuntimeState'  +  Observables
```

- **Static artifact** — durable topology + role configs + policy references + schema references. Content-addressed.
- **Persistent runtime state** — world state, claim facts, receipts, capacity-fault latches, clock/pose/rotor/fault state. Threads across epochs.
- **Epoch input** — the incoming claim batch (later: external / effect-wall observations).

Claim facts and receipts are **top-level runtime state**, not hidden inside a special actor. ADMIT's *policy identity* is static; its *facts and receipts* are runtime state; the incoming *claim batch* is epoch input.

---

## 1. Node envelope + five built-in roles (D1)

One structural node envelope is frozen:

```
Node {
    object_id
    role                 ; one of the five closed role IDs below
    static_config        ; role-specific frozen config
    state_schema_ref     ; semantic state signature (see §3)
    ports                ; frozen per-role port signature
}
```

The entire executable v1 role registry is these five (closed):

### PulserDecl
- **static_config:** clock mode `("periodic", period, phase)` | `("once", epoch)` (period ≥ 1, 0 ≤ phase < period, period < 1e9; epoch in [0,1e6)).
- **ports:** out `sig_out`.
- **state:** clock state (see §3).
- **invariant:** fires deterministically by clock mode; never data-dependent.

### RelayDecl
- **static_config:** none.
- **ports:** out `sig_out`; in `sig_in` (or-merge of incoming wires).
- **state:** `cur_out`, `next_out`.
- **invariant:** `next_out = OR(incoming .nxt)`; `cur_out' = next_out` at commit.

### DoorDecl
- **static_config:** none.
- **ports:** in `sig_in`.
- **state:** `open`, `next_open`.
- **invariant:** `open' = next_open`; `next_open' = incoming wire `.nxt`.

### SpinnerDecl
- **static_config:** lane geometry `(w, n)`, initial `rotor4`, `configurable` permission (fixed | configurable).
- **ports:** in `sig_in` (exactly one); out `socket` (exactly one).
- **state:** `rotor` (Q-fixed lanes, runtime STATE).
- **invariant:** exactly one sig-in + exactly one socket; fixed spinners REJECT runtime rotor writes (typed error); configurable accept `SetRotor` at COMMIT.

### OrbDecl
- **static_config:** none.
- **ports:** in `pose` (via socket).
- **state:** `pose4`, sticky `numeric_fault` bit.
- **invariant:** controller exclusivity (≤ 1 socket); `numeric_fault' = fault_base OR current_overflow` where `fault_base = 0 if ResetFault else old` (a reset cannot hide a same-epoch overflow).

**Frozen:** node envelope, the five role IDs, their config/port/state signatures, their invariants.
**Not frozen:** user-defined behaviors, mailboxes, supervision, generic behavior tables, dynamic role loading, the physical IC encoding of each state. New built-in roles are additive **v1.x**; a general actor-behavior system stays Experimental.

---

## 2. Edge vocabulary (D2)

Exactly two **structural topology edges** are frozen:

```
SignalWireDecl    { src.sig_out → dst.sig_in }   ; dst ∈ {Door, Relay, Spinner}
SocketControlDecl { spinner.socket → orb.pose }
```

Legal pairs: `(sig_out, sig_in)`, `(socket, pose)`. Any other edge variant MUST fail validation.

**Graph edges are not transition classes.** These are NOT structural edge kinds in v1:

| WRL texture | IR v1 status |
|---|---|
| Solid `--` | executable through `SignalWire` |
| Async `~~` | reserved in WRL, **absent** from IR v1 (no placeholder node) |
| Verified `==` | acceptance machinery grounded; route construct **absent** |
| Fault `!!` | fault state grounded; route/supervision construct **absent** |

A numeric-fault latch is *not* the lowering of a `!!fault!!>` route; an acceptance receipt is *not* a complete lowering of a `==verified==>` route. Reserved WRL syntax needs no placeholder canonical IR node.

---

## 3. State schema — semantic vs backend (D4)

IR v1 freezes **semantic signatures**; it excludes **backend encodings**.

**Semantic (in the artifact or a referenced policy/schema):** signedness; lane width; fractional bits; numeric-policy identity; saturation behavior; rounding behavior; sticky-fault behavior; fixed-vs-configurable permission; fact/receipt capacity (when exhaustion is observable); rotor & pose lane counts; claim & receipt field meanings.

**Backend (excluded — belongs to a lowering profile):** Scott encoding; tuple nesting; DUP labels; one-hot vs binary clock counter; packed-word layout; IC variable names; native struct padding; CUDA memory layout.

**Identity split (frozen):**

```
SemanticArtifactID = hash( canonical Forge IR + semantic policy references )
BackendArtifactID  = hash( SemanticArtifactID + lowering profile + compiler hash + backend representation )
```

Changing one-hot → binary changes the **BackendArtifactID** only (not the world identity or WorldFrame). Changing Q32.32 → Q16.16 changes the **SemanticArtifactID**.

---

## 4. Frozen top-level forms

```
ForgeSemanticArtifactV1 {
    ir_version
    profile_id                 ; "forge.world.core.v1" (deterministic-circuit-world)
    semantic_policies {
        rulepack_id
        numeric_policy_ids
        admit_policy_id        ; e.g. admit_candidate_min_firstreceipt_v1
        film_schema_id
    }
    schemas {
        runtime_state_schema
        epoch_input_schema
        observable_schema
    }
    objects: [ PulserDecl, RelayDecl, DoorDecl, SpinnerDecl, OrbDecl ]
    edges:   [ SignalWireDecl, SocketControlDecl ]
    initial_state
}

RuntimeStateV1 {
    epoch
    clock_states
    signal_states
    door_states
    relay_states
    spinner_rotors
    orb_poses
    numeric_faults
    claim_facts
    acceptance_receipts
    capacity_faults
}

EpochInputV1 { claim_batch }          ; ClaimBatch of SetRotor|ResetFault envelopes

EpochResultV1 { runtime_state, world_frame, ledger_entries }
```

---

## 5. Transition law (frozen)

Per epoch the transition is the WRL Core 0.1.1 cycle:

```
OBSERVE → ACCEPT → MAP → COMMIT → REACT → FILM
```

For claim-free epochs OBSERVE/ACCEPT/MAP degenerate to identity but remain in the model. COMMIT applies MAP'd controls (SetRotor writes + fault resets) to owned cells; REACT runs the deterministic within-period token cascade to fixpoint and latches overflow; FILM emits the **WorldFrame** (physical, Film v0.6 family) + **EventLedger** entries (claim-aware, Film v0.7 family). Canonical ordering is policy-pinned (the ADMIT profile pins `CandidateKey`).

---

## 6. Versioning (D5)

- **v1** freezes on the grounded `deterministic-circuit-world` profile — sufficient evidence exists (multiple clock modes, randomized topologies, fan-in/out, cycles, multiple controllers, dynamic rotors, persistent multi-epoch state, claims/receipts, fault reset, pose authority, native+reference reducers). It does **not** claim to be the universal final Forge IR.
- **v1.1** — additive role/field variants when a second world family arrives.
- **v1.x** — additive optional feature declarations.
- **v2** — any change to the meaning of an existing field. A second implementation must NOT silently reinterpret v1 fields.

---

## 7. First WRL vertical slice (what the compiler supports)

```
WRL Core text/canvas → canonical WRL graph → Forge Semantic IR v1
    → current Fixture adapter → TRVM compiler → ic_ref / ic32 → Film v0.7
```

Supported: Pulser, Relay, Door, Spinner, Orb; signal wires; socket control; fixed-point policy declarations; `SetRotor`; `ResetFault`; a fixed number of periods. Everything else → clear unsupported-feature diagnostic.

---

## 8. Conformance (what IR v1 does NOT define)

> IR v1 defines static deterministic signal graphs containing the five built-in roles, persistent numeric pose state, bounded ADMIT claim state, and the two grounded topology relations. It does not define mailboxes, arbitrary actor behavior, dynamic topology, fragments, capabilities, supervision, or distributed settlement.

---

## D1–D5 resolution

| Decision | Ruling (frozen) |
|---|---|
| D1 node vocabulary | stable node envelope + five closed built-in roles |
| D2 edge vocabulary | two structural edge kinds only; async/fault/verified are transition-class reserved, not edges |
| D3 ADMIT | static policy + top-level runtime ClaimState + separate EpochInput (three layers) |
| D4 state schema | semantic signature frozen in artifact; physical representation excluded to backend profile; Semantic/Backend artifact-ID split |
| D5 freeze timing | freeze now as restricted `deterministic-circuit-world` profile; v1.1 additive, v2 semantic |
