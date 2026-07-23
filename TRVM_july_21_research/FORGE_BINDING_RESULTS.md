# Forge Binding Results v0.9 — round 12 executed: the Spinner is a fixture citizen, film v0.5 carries pose

**SLICE 3b.5a PASS_REF_AND_NATIVE (146s), first run, all eight battery
items. The Spinner is now first-class: film v0.5 carries authoritative
pose state (numeric-policy id, lane geometry, big-endian
two's-complement lanes, controller relationship, fault latch), and the
compiled epoch term applies the rotor by Scott FUNCTION-selection on
the spinner's in-wire — the pose is consumed exactly once, and the
dead rotation branch erases before its interior reduces: idle epochs
cost 39 interactions inside a 1 MB term; firing epochs ~76.5k (Q4.4) /
~305k (Q8.8). Measured, not assumed.**

## Round-12 corrections, executed first

Transitivity wording corrected to the CONDITIONAL form (demonstrated
small-width equality + implication at Q32.32; closure assigned to the
3b.5c typed bridge). Separator table now carries the canonical
corrected-horizon figures: **19,979/20,000 divergent, wide-MAC
−1.919083e-05 vs oracle −2.015289e-05** — my own rerun log already
contained them; the ledger had quoted the stale pre-fix run.
E2_RESULTS retitled **v2.3 — Native Once Refreeze (28/28)**. Policy
identities registered in binlib: `legacy_spinner_pp_tz_nosat_v1`,
`forge_motor_widemac_tz_sat_v1`.

## The width-scoping decision (stated for ratification)

The binding Spinner is a Forge-layer object at fixture-declared proxy
width whose pose semantics are the PARAMETRIC ORACLE POLICY (proven ≡
`e2_model.qmul`, 3b.4 §A). The real Q32.32 World runs in lockstep as
the timing/structure anchor; its rotor is the exact `<<(32−n)` rescale
of the filmed proxy lanes, **asserted at every projection** (config
integrity has teeth). Q32.32 value parity closes at 3b.5c per the
round-12 ruling. Film v0.5's policy-id + lane-geometry fields make the
width explicit so nothing is silently conflated.

## Slice 3b.5a battery (all PASS, first run)

| item | result |
|---|---|
| pulser→wire→spinner latency+parity, Q4.4 T=45 | films exact; rotations at the closed form {4,7,…}; **idle 39 ints, firing 76,488–77,638** |
| independent init | boundary parity holds; **corrupted pose lane FAILS it** (teeth) |
| Q8.8 parity T=16 | films exact; firing 304,025–306,977 ints |
| dynamic multi-rotation (period 2, T=30) | 15 rotations, films exact every epoch |
| controller exclusivity + release | static double-socket → typed ValueError; live second LINK rejected as `controlled`; DELETE frees; relink succeeds |
| EV_CONFIG rotor at epoch 10 | model CFG (anchor rescale) + kernel swap keyed by (policy, rotor bytes); films exact across the change |
| determinism | same artifact+inputs twice → identical film sequences |
| NATIVE GATE (hard) | 8 full epochs of the 1 MB spinner term through ic32, films exact |

Overflow law status, per the ruling: the legacy policy has no
saturation; the film's fault bit is present and 0, wired for the
wide-MAC policy where it becomes authoritative (3b.5b).

## Ripple regressions under film v0.5

The version line bumps every film hash; both sides bump together. One
real break found and fixed: `state_from_projection` unpacked a
5-tuple — now accepts the v0.5 seven-tuple, ignoring pose sections in
discrete-only slices. run3e **PASS_REF_AND_NATIVE** (146s) · run2
**PASS** · run3 **PASS** · run1 smoke + NEG 4/4 · run3d rerun **PASS_REF_AND_NATIVE** (rc=0 under the v0.5 tree) ·
oracle 28/28 and `make test` unchanged (film is binding-layer only).

## The policy finding, reconciled with round 11's freeze

Round 11 froze the wide-MAC (exact products → sign-extend → ±
accumulate → ONE shift → ONE saturation) as **Forge numeric law for new
numerics**. The spinner is not new numerics: it is governed by the
frozen v2.2 oracle, whose policy is per-product truncation. Both live
in `binlib` (`dyn_mac4` = the law; `hcomp_case`/`rot_step_case`/
`dyn_rot_step` = the oracle's policy), and the live separator on the
real trajectory shows the stakes: **first divergence at rotation 2;
19,979 of 20,000 rotations diverge; wide-MAC drift −1.919083e-05 vs
the oracle's −2.015289e-05** (canonical, at the corrected horizon).
The policies are one ULP apart per component and ~5% apart in
century-scale drift.

## The K off-by-one — a lesson in not extrapolating a schedule

My first drift replication used K=19,999 rotations and missed the
documented figure in the 5th significant figure. The long run executes
epochs tc = 2 … **100,001** (build primes two epochs), so rotations at
tc≥6, (tc−6)%5==0 count to **K=20,000**. The fix is not a formula
patch but a method change: section B1 now validates the schedule and
function against the ACTUAL model — 200 epochs, pose exact every epoch
— and only then extrapolates. **K=20,000 → drift −2.015289e-05,
matching the documented figure to all printed digits (tol 1e-11).**

## Slice 3b.4 battery

| section | result |
|---|---|
| A. parametric policy ≡ `e2_model.qmul` at Q32.32, 2000 random quats | **PASS** |
| B1. schedule+function vs the actual model, 200 epochs pose-exact | **PASS** |
| B2. drift replication, K=20,000 → **−2.015289e-05** ≡ documented | **PASS** |
| C. policy separator LIVE on the real trajectory | measured (above) |
| D. hcomp (per-product policy, in-range flag) ×400; **const rotation trajectories pose-value-exact**: Q4.4 T=64, Q8.8 T=24 | **PASS** |
| E. **DYNAMIC rotation trajectories pose-value-exact**: Q4.4 T=32, Q8.8 T=8 | **PASS** |
| F. NATIVE GATE (hard): const ×6 + dynamic ×3 through ic32 | **PASS, 0 mismatches** |
| G. transitivity verdict (CONDITIONAL, per round 12) | the tested lowering implements the oracle's policy at Q4.4/Q8.8 (D,E) ∧ the same parametric policy ≡ oracle at Q32.32 (A) ∧ reproduces the documented drift (B) ⇒ **a correct Q32.32 instantiation of this lowering would reproduce the drift** — a demonstrated equality at small widths plus an implication at target width; Q32.32 parity closes at the 3b.5c typed bridge |

## The measured quaternion numbers (the round-11 optimization input)

Per rotation (8 nonzero products for ROT_Z90; zero-rotor products
skipped at emit — fixture constants compile in):

| form | Q4.4 | Q8.8 |
|---|---|---|
| constant | 71,056–72,392 (mean **71,216**) | 285,480–289,176 (mean **287,460**) |
| dynamic pose | 76,286–77,600 (mean **76,607**) | 303,998–307,526 (mean **305,938**) |

The dynamic tax at rotation scale is ~7%. The reviewer's 16-product
estimate (~577k) halves under zero-skipping for this rotor; a dense
rotor would land near it. **This is the datum the round-11 ruling
deferred the optimization decision to.**

## Round-11 conditions, executed

Registry **completed**: `mul_wide`/`shift_tz` registered (flat,
no-flag), `mac` registered (nested); **`dyn_mac4` promoted into binlib**
as the reusable frozen-policy combinator (verified ×8 vs golden);
`mac_headroom(w,k)` makes the accumulator-cannot-wrap claim an
**executable assertion** (Wacc = 2w+⌈log₂k⌉, strict bound checked).
`dyn_take_value` remains documented legacy/flat-only. Eager-class cost
claims formally moved to the packed-net venue (two-field cost records:
logical firings + wall-clock under named scheduler). **Native model
Once: narrow unfreeze granted — executing next**; until it lands, Law 6
remains horizon-scoped and the stale fixture.py sentence stands
condemned.

## Regressions — ALL rerun under the native-Once tree

run3d **PASS_REF_AND_NATIVE** (417s; drift −2.015289e-05 unchanged, as
the schedule requires) · run3c **PASS_REF_AND_NATIVE** (134s) · run3b
**PASS** (345s) · run3 **PASS** (once-heavy slice) · run2 **PASS** ·
run1 smoke + NEG 4/4 · oracle **28/28** · `make test` 13/13 (rulepack
hash moved with the edit, as content-addressing requires).

## Laws

1–7 unchanged. Round-11 commentary on Law 5: *two numeric policies are
two meanings — an encoding may not switch between them silently; a
policy change is an explicit act with a measured separator.*

## Deferred, stated

3b.5 Motor8 integration (film/pose fields,
compiler spinner support, constant-rotor multiplier specialization as a
measured optimization) — **gated on round-12 review with the quaternion
numbers above as input**. w-row/Booth multiplier for the product path.
Packed-net eager measurement. Framed WireIdentity; structural lowering;
persistent loop; ADMIT on-reducer; CUDA.

## Reproduce

```
cd forge
python3 binding_run3d.py     # 3b.4 quaternion proxy (~4-5 min)
python3 binding_run3c.py && python3 binding_run3b.py
python3 binding_run3.py && python3 binding_run2.py
python3 binding_run.py && python3 binding_run.py NEG
python3 e2_run.py && cd .. && make test
```
