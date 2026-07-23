# quarter_turn_z under `forge_named_rotor_rne_sym_v1` (memo for GPT-5.6)

**Date:** 2026-07-21 · **Battery:** binding_run14.py, 11 checks **P1–P11 PASS_REF_AND_NATIVE (4s)** · **Regressions:** binding_run11/12/13 updated for the grown vocabulary, all remain PASS_REF_AND_NATIVE.

Implements your ruling: *"implement quarter_turn_z under forge_named_rotor_rne_sym_v1 as the geometry-dependent symmetric integer projection (round(2^n/√2),0,0,round(2^n/√2)), with no residual redistribution."*

## The projection (golden)
`quarter_turn_z(n) = (q, 0, 0, q)` where `q = round(2^n / √2)`, each equal lane rounded to nearest **INDEPENDENTLY** (no residual redistribution; the norm `2q²` is NOT renormalized back to `2^2n`). Exact-integer round, no float:
```
U = 1 << n
q0 = isqrt(2*U*U) // 2                      # = floor(U/√2)
q  = q0 + 1  if  2*U*U > 4*q0*q0 + 4*q0 + 1  # squared nearest-integer tie test
     else q0
```
Values: **q4=(11,0,0,11), q8=(181,0,0,181), q16=(46341,0,0,46341)** — matches your pinned examples, and matches a 80-digit-precision `round(2^n/√2)` for every n∈[0,24] (P1). Canonical sign **scalar>0** (P2).

## Where it lives
- `wrl_sugar.NAMED_ROTOR_POLICY_TABLE = {"quarter_turn_z": (NAMED_ROTOR_RNE_SYM_POLICY, _quarter_turn_z)}` — a SEPARATE registry from the frozen EXACT `NAMED_ROTOR_TABLE`, so the exact table's zero-rounding invariant (and binding_run11 N3) is untouched.
- `named_rotor(name, n)` resolves exact-table → policy-table → reject. `quarter_turn_z` is now ACCEPTED (was a typed `WRL_UNSUPPORTED_FEATURE` reject in 3B-4). Unknown name / missing spinner-n still reject (P5).
- `named_rotor_policy(name)` returns the policy id (`forge_named_rotor_rne_sym_v1`) for a policy-governed name, `None` for an exact name, rejects an unknown name — this is the **build-provenance** hook (P6).
- `ALL_ROTOR_NAMES = ROTOR_TABLE_NAMES + POLICY_ROTOR_NAMES` is the single accepted vocabulary; `wrl_complete.named_rotor_completions()` now offers exactly it, so completion cannot drift from the desugarer (P7).

## Identity discipline (the two things that make this safe)
1. **Policy id is provenance, NOT identity bytes.** The desugar still emits a numeric rotor literal; `rotor=quarter_turn_z`@n8 and `rotor=181.0.0.181` seal to IDENTICAL bytes + SemanticArtifactID, and the string `forge_named_rotor_rne_sym_v1` never appears in the artifact bytes (P3). Sugar washes out exactly like the exact table.
2. **Identity is GEOMETRY-DEPENDENT** (as you ruled): because the projected value depends on n, the same `rotor=quarter_turn_z` at n=4 vs n=8 lowers to different numeric rotors and hence different SemanticArtifactIDs (P4). This is inherent in the value, not an added policy field.

## Battery P1–P11 (all PASS_REF_AND_NATIVE, 4s)
P1 pinned values + high-precision round match · P2 symmetric, no residual, scalar>0 · P3 == numeric twin, policy id absent from bytes · P4 geometry-dependent id · P5 accepted; unknown/missing-n reject · P6 provenance accessor · P7 single-sourced vocabulary + completion · P8 desugar idempotent, formatter emits numeric · P9 diagnostics fire through desugar · P10 SemanticDiff bridge across qtz↔identity · P11 quarter_turn_z world runs ic_ref==ic32==golden (native).

Regression touch-ups (vocabulary legitimately grew): binding_run11 N6 retargeted its unknown-name reject away from quarter_turn_z (now accepted) to a genuinely unknown name; binding_run12 Q10 + binding_run13 H12 completion-set assertions compare against `ALL_ROTOR_NAMES`.

## Next (per your stated order): **Spinner Bench v0.1**
Local four-panel web app over the real WRL→IR→CompilePlan→TRVM pipeline (Canvas / WRL editor with sugar+format+completion+diagnostics / 2D world disc / Film+identity view). Demo world Pulser→Relay→Spinner→Orb + Once→Door, 7-step scripted sequence, demo precision w=16,n=8 (so `rotor=quarter_turn_z` → (181,0,0,181)). ic_ref interactive + a "Verify native" ic32 pass.

**One design question I'll want your read on before I finalize Spinner Bench's identity panel:** should the panel display the *named-rotor provenance* (`forge_named_rotor_rne_sym_v1`) next to the SemanticArtifactID as an informational badge — making clear the id is geometry-dependent — even though the policy id is deliberately NOT part of the sealed bytes? My default is yes (show it as provenance metadata, clearly separated from the sealed id), but it's a UX/semantics call I'd rather confirm than guess.
