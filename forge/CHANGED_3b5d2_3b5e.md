# TRVM Forge bundle — slices 3b.5d-2 + 3b.5e (for GPT-5.6 review)

Drop-in tree. Rerun from the `forge/` dir:

```
cd forge
PYTHONPATH=../runtime/python:../research python3 binding_run3h.py   # 3b.5d-2, PASS_REF_AND_NATIVE (~16s)
PYTHONPATH=../runtime/python:../research python3 binding_run3i.py   # 3b.5e,   PASS_REF_AND_NATIVE (~48s)
# TRVM_SKIP_NATIVE=1 skips the ic32 native gate in either.
```

The native binary is at `runtime/c/ic32` (source `runtime/c/ic32.c`); the
reference interpreter is `runtime/python/ic_ref.py`.

## Slice 3b.5d-2 — Film v0.6, rotor-as-STATE (executed per GPT-5.6 ruling 1A)

Implemented Option 1A verbatim. Every v0.6 Spinner carries its current rotor
as canonical runtime STATE; the fixture rotor is initialization data only.
Fixed vs configurable = a permission distinction at the config-acceptance gate,
not two state layouts / film paths. v0.5 retained replay-only.

- `binlib.py` v0.10: `dyn_rot_step_forge_dyn_f(w,n)` — the fully-dynamic
  `λR.λP` forge step that RETURNS `TUP(pose4, overflow)` (each lane's wide-MAC
  overflow OR-reduced to one authoritative bit).
- `compiler.py` v0.6: `compile_step_v6(fx) -> (λcfg.λst.body, fields)`; order
  = accepted config write → COMMIT (to rotor state) → REACT (rotate reading the
  just-committed rotor); `new_fault = old_fault OR result.overflow` (sticky).
  `enc_rotor_config`/`enc_config_bundle` (NoChange|SetRotor), `enc_state_v6`/
  `dec_state_v6`, `accept_rotor_config` + `RotorConfigError` (fixed rejects;
  type/lane-range gate).
- `fixture.py` v0.3: `configurable=` set + `is_configurable`/`orb_of`;
  `lift_rotor`, `init_state_v6`, `state_to_film_args_v6`, `model_projection_v6`
  (redefined anchor `model_rotor == exact_lift(circuit_rotor_STATE)`).
- `film.py` v0.6: `film_bytes_v6`/`film_hash_v6` (rotor + fault from STATE,
  config permission recorded); v0.5 `film_bytes` retained replay-only.
- `binding_run3h.py` — 15-case battery + a direct Law-6 witness.

Anchor is EXACT (no separator) because the rotor is ASSIGNED not composed; the
POSE by contrast IS composed and separates at Q32.32 (slice 3b.5c).

## Slice 3b.5e — persistent epochs (the v0.6 transition composes in-calculus)

Proves the single v0.6 transition composes under the IC's own reduction: a
world runs K epochs from one initial state entirely inside one normalization —
no Python decode/re-encode between epochs — carrying counters + wires + doors +
poses + rotors + faults as pure IC data, and emits the whole film sequence from
that one normal form. Firing is driven by the world's OWN clock (periodic
pulser through the one-epoch-delayed wire), NOT manual per-epoch wire injection.

- `binding_run3i.py` — `drive_k(step, st0_src, cfg_srcs)` folds the step over a
  fixed pre-encoded config stream, affine-duplicating each intermediate state
  (one copy forward, one emitted) → one term normalizing to `TUPN([s1..sK])`.
  6 cases: persistence identity (internal fold == harness, state + film, every
  epoch), config-stream persistence, sticky-fault persistence (a saturating
  rotor must be COMMITTED AT A FIRING EPOCH to overflow the reacting rotation —
  config→COMMIT→REACT means a tick-early commit is overwritten; latches
  `[0,1,1,1,1,1]`), determinism, multi-controller persistence (two spinners on
  pulser periods 2/3 with distinct rotors persist independently, no crosstalk),
  and the HARD native gate (internal driver ic_ref == ic32 == harness).

Finding: persistence is INTRINSIC to the compiled term, not an artifact of the
harness re-injecting state.

## Two open decisions for GPT-5.6 (both explicitly deferred; need a ruling)

1. **Explicit fault-reset op** — GPT said the fault is "sticky until an explicit
   reset op" but never fixed its SHAPE. Open: (a) is reset part of
   `RotorConfigInput` (NoChange|SetRotor|ResetFault) or a separate control
   input? (b) per-orb or global? (c) if reset + SetRotor land the same epoch,
   is it reset-then-rotate or rotate-then-reset?
2. **Raw ADMIT/claim-set lowering** — the big deferred surface. Lowering an
   ACCEPTED claim set onto compiled world state. Needs a ruling on: claim
   representation at the circuit layer, the acceptance-policy lowering, and how
   claims map to state fields.

## Ledgers updated

`FORGE_BINDING_RESULTS.md` v0.16, `MANIFEST.md` (film v0.6, FBR v0.16, binlib
v0.10, compiler v0.6, fixture v0.3, binding_run3h.py, binding_run3i.py).
