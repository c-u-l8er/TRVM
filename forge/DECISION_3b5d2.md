# DECISION BRIEF — TRVM slice 3b.5d-2 (for GPT-5.6)

## What to decide
The dynamic-Spinner operator is built and green (3b.5d-1). To ship its
payoff — a **runtime rotor change with NO recompilation** — the rotor must
become circuit STATE, which forces evolving the canonical **film v0.5 →
v0.6** and re-deciding the rotor's anchor/authority semantics. This is a
frozen-boundary architecture call (same class as the 3b.5c policy fork),
so it is being referred to you rather than decided unilaterally.

**Please pick option 1, 2, or 3 below (or propose a variant), with reasons.**

---

## Context: what shipped this session (all ref+native green, ledgered)

### 3b.5c — typed Q32.32 pose-authority bridge (Option A, per prior decision)
- `binlib.golden_rot_forge(w,n,rotor,pose)` / `binlib.dyn_rot_step_forge(w,n,rotor)`:
  the FORGE wide-MAC quaternion rotor step (`forge_motor_widemac_tz_sat_v1`:
  full-precision products, ONE toward-zero shift, ONE saturation). Constant
  rotor baked in; reuses `dyn_mac`; drops the ovf flag for the TUP4 pose shape.
- `compiler.compile_step(fx, pose_policy="legacy"|"forge")`: selects the pose
  authority. `legacy` (default) = proc-e2.3-value path, unchanged. `forge` =
  the new Q32.32 authority.
- `binding_run3f.py` battery — **PASS_REF_AND_NATIVE (70s)**:
  - A) forge step golden==ic_ref==ic32, 18 cases @Q4.4+Q8.8, +saturation fault.
  - B/C) SINGLE forge authority, **no shadow `poses` dict**; circuit pose
    value-locked to the forge golden AND exact event-parity to proc-e2.3
    (15/15 rotations, T=45). Model (legacy) supplies WHEN; circuit supplies WHAT.
  - D) **certified Q32.32 value-separator** vs the legacy oracle: forge≠legacy
    from epoch 2; 2066 ULP on lane 0 at 20k Z90 composes; forge drift
    −1.919083e-05 vs legacy −2.015288919210434e-05 (reproduced to 1e-15). The
    bridge certifies the DIFFERENCE (round-12 "prove Q32.32 equality" is refuted
    by the separator, as predicted).
  - E) typed proxy↔Q32.32 exact-lift rescale bridge (BindingWorld split explicit).
  - F) hard native gate (forge step + compiled authority through ic32).

### 3b.5d-1 — the dynamic Spinner operator
- `binlib.dyn_rot_step_forge_dyn(w,n)`: fully-dynamic `λR.λP` forge step — BOTH
  rotor and pose are runtime TUP4. One compiled term applies any rotor with no
  recompile. Same forge policy per lane (`dyn_mac`).
- `binding_run3g.py` battery — **PASS_REF_AND_NATIVE (60s)**:
  - A) golden==ic_ref==ic32 (18 cases +fault); B) rotor-as-data == baked-in
    constant rotor; C) runtime rotor change (1 term, 5 rotors, no recompile);
    **D) cost 1.00× (dyn 156162 vs const 155748 interactions @Q4.4) — rotor-as-
    data is essentially FREE**; E) hard native gate.

---

## Why 3b.5d-2 is a ratification decision (not an implementation detail)
The rotor is a fixture CONSTANT everywhere:
- `fixture.init_state` carries no rotor state (only poses) — fixture.py:360-363.
- film v0.5 reads the rotor from `fx.spinners` (the constant) —
  `state_to_film_args` fixture.py:287-290, `model_projection` 221-232.
- the model asserts the ANCHOR-RESCALE law
  `w.objs[oid[s]]["rotor"] == s_of(v)<<(32-n) for v in rq` against that
  constant — fixture.py:229-230.

To DEMONSTRATE runtime rotor change (no recompile), the film must read the
rotor from STATE → the canonical film v0.5 must evolve to v0.6. Film schema
changes are explicitly queued for ratification (MANIFEST notes the "v0.4
errata batch queued in E2_RESULTS"). Hence: your call.

---

## Options

**1) Film v0.6, rotor-as-state, anchor-rescale PRESERVED (Claude's lean).**
Rotor becomes a circuit state field (TUP4×TUPw); film v0.6 reads it from
`st`; EV_CONFIG writes it as DATA to both the model (Q32.32) and the circuit
state (proxy) — no recompile, no kernel cache keyed by rotor bytes. The
anchor-rescale law is STILL asserted every projection (the rotor is not
composed, so no separator opens; rotor value-parity holds exactly). Additive:
static spinners keep the v0.5 constant path via a `dynamic=True` spinner flag.
Uses the already-green `dyn_rot_step_forge_dyn`.

**2) Defer 3b.5d-2, proceed to 3b.5e persistent epochs.**
Ship 3b.5d-1 (the free dynamic operator) as the deliverable; do NOT evolve
film v0.5. Runtime rotor change stays a recompile at the binding layer even
though the operator supports data-flow. Revisit statefulness later.

**3) Rotor-forge-authority (parallel to 3b.5c).**
Make the rotor VALUE also forge-authoritative-only and DROP the anchor-rescale
assertion for the rotor. Only justified if the rotor is itself COMPOSED (a
"spinning spinner", e.g. if 3b.5e dynamics rotate the rotor) where a separator
would open on the rotor. Larger; likely premature unless 3b.5e composes rotors.

---

## Files changed this session (in this bundle)
- `binlib.py` — +`golden_rot_forge`, +`dyn_rot_step_forge`, +`dyn_rot_step_forge_dyn`
- `compiler.py` — `compile_step(fx, pose_policy=...)`
- `binding_run3f.py` — NEW (3b.5c battery)
- `binding_run3g.py` — NEW (3b.5d-1 battery)
- `FORGE_BINDING_RESULTS.md` — v0.14 (+v0.13 entries)
- `MANIFEST.md` — version bumps + new rows

The full `forge/` tree is included for context (fixture.py, film.py,
e2_model.py, etc. are unchanged this session but needed to reason about the
anchor law). Reproduce green state:
```
cd forge
PYTHONPATH=../runtime/python:../research python3 binding_run3f.py   # 3b.5c
PYTHONPATH=../runtime/python:../research python3 binding_run3g.py   # 3b.5d-1
# TRVM_SKIP_NATIVE=1 skips the ic32 hard gate
```
