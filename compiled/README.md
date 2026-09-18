# The compiled backend for WRL worlds — CompilePlanV1 → one C step function, admitted by the interaction-calculus fold

**2026-09-18.** The re-layering Travis ruled this morning: keep `ic32` as the semantic oracle and the executor for small
worlds; build ONE compiled backend for WRL worlds (Forge IR → C state machine), **admitted only when its fold equals the IC
reference on every sealed world** (the compiled-home discipline of `FOUNDATION_LANE.md` §3b: the oracle exists before the
home does); the 9.2 MB demo epoch as the acceptance test. This directory is that backend and its admission.

Status: **BUILT and ADMITTED on this battery — 14 worlds, 41 (world, scenario) pairs, 746 epochs, film-equal AND
state-equal on every one; 11 of 11 emitter mutants caught. Development reading on the shared laptop.** Not claimed: a
new semantic identity (none moves), a Super integration, anything about worlds the battery does not contain, or a
production figure.

## 1. What it is

`emit_c.py` reads the same object every codec and signature already project — the CompilePlanV1 view (`wrl_plan.plan_view`,
the backend-neutral lowering contract) — and emits one C function `step_v6(st, ctl, out)` over a flat int64 state vector in
`compiler.state_layout` order (a one-hot or binary counter is one slot, a once-clock two, a wire/door/relay two, a pose or rotor
four lanes, a fault one). The laws are the ones `compiler.compile_step_v6` lowers to the calculus, written in C instead of
unrolled into a term: clocks fire at their phase and advance; a wire's next is its source's hot (a pulser's fire, a relay's
NEXT output); a door or relay takes its input wire's next; per orb the fault reset is COMMITTED, then the rotor config is
COMMITTED (`SetRotor` replaces, `NoChange` keeps), then the spinner REACTS over the committed rotor only if its input fires —
the wide-MAC quaternion step (`binlib.golden_rot_forge`: full-precision products, one toward-zero shift, one saturation, read
from the same `HAMILTON` table) and a sticky fault. The control vector is `enc_config_bundle`'s walk (per controlling spinner in
orb order a set flag and four lanes; per orb a reset flag). The source is deterministic in the view; it is compiled once
(`gcc -O2 -shared`, content-addressed under `~/.cache/trvm-compiled/`, never in the tree) and called through ctypes.

Identity: `cbknd-` + sha256(SemanticArtifactID + `compiled.c.step.v1` + the emitted source). It moves with the emitted code
and never with the semantic id — the split `wrl_canonical` names, at a fourth representation.

`fold.py` is `spinner_bench._run_traj` with one substitution. Scenario resolution, the sealed admission seams, the claim state,
the EpochControl and `film_hash_v7` are Forge's own, imported unchanged; only the step differs. `compiled_fold` calls the C
step; `ic_fold` is a twin with the calculus in the step that also returns the decoded state per epoch; `reference_films` is the
production `_run_traj` itself under Forge's reducer adapter.

## 2. The admission (`battery.py`, `results-battery.json`)

For every (world, scenario) pair: the production fold's films (ic_ref, or ic32 on the ~10 MB-epoch worlds; on the Golden demo
scenario BOTH, and they agree) and the calculus twin's decoded states against the compiled fold's films and states, epoch by
epoch. Worlds: the Golden demo, relay chains of 10/30/120, pulser→relay, pulser→door (once at 1), a bare relay, spinners at
w=4/n=2, w=8/n=4, w=16/n=8 (fixed), a binary counter (period 40, phase 3 — above the one-hot threshold), a once-clock at 5, a
relay fanning out to a spinner and a door, and two spinners (w=8 and w=12) on two orbs. Scenarios: each world's own demo
scenario, and for the ten worlds with a spinner or a non-one-hot counter, three seeded random scenarios of 24 epochs (random
rotors biased to the lane extremes — 0, ±full scale, the unit, its complement — random fault resets, random initial faults;
writer/sequence within the scenario schema's 4-bit bounds). WRL admits one signal wire into an object, so there is no
merge world; the emitter's `merge_in` therefore only ever sees one wire in a sealed world.

| world | epoch term (B) | calculus per epoch | compiled per epoch | pairs · epochs | verdict |
|---|---:|---:|---:|---|---|
| **golden-demo** (w=16, n=8) | 9,509,628 (demo) / 10.2–10.3 M (fuzz) | ic32 **0.22 s** (ic_ref 3–7 s on the demo scenario) | **8–11 µs** | 4 · 79 | AGREE, films = the seven recorded 2026-09-16 (`56a2980e…` … `8c7bf5ed…`) |
| two-spinners (w=8 + w=12) | 8,466,671 | ic_ref 3.4–3.8 s | 10 µs | 4 · 79 | AGREE |
| spinner-w16-n8-fixed | 10,298,876 | ic32 0.24 s | 6–7 µs | 4 · 79 | AGREE |
| spinner-w8-n4 / fanout | 2.63 M | ic_ref 0.66–0.92 s | 6–9 µs | 8 · 158 | AGREE |
| spinner-w4-n2 | 703,340 | ic_ref 0.14–0.18 s | 6–7 µs | 4 · 79 | AGREE |
| chain120 / chain30 / chain10 | 48,498 / 12,678 / 4,718 | ic_ref 37 ms / ic32 2 ms / ic_ref 1 ms | 91 / 18 / 10 µs | 3 · 21 | AGREE |
| binary-40-phase-3 / once-at-5 / pulser-door | 3,724 / 2,153 / 1,402 | ic_ref < 1 ms | 3–4 µs | 12 · 237 | AGREE |
| pulser-relay / relay-only | 738 / 337 | ic_ref < 1 ms | 3 µs | 2 · 14 | AGREE |

**BATTERY: ALL AGREE (41 pairs, 1,066 s wall, almost all of it the calculus).** On the acceptance test — the demo world's
9.5 MB epoch — the compiled step is about 25,000× the ic32 reduction and about 400,000× ic_ref; on `two-spinners` about
350,000× ic_ref. The compiled step's cost is linear in the world (chain120 at 91 µs is the largest), and the Python
encode/decode around the C call is most of every microsecond figure; the C itself is well under that.

One number this run disagrees with an older record on: the demo epoch term measured 9,509,628 B today against 9,177,234 B on
2026-09-16 (§3ai). The seven films are byte-identical to the ones recorded then, so the semantics did not move; the term
bytes did, and this record does not explain why (the forge tree is clean in git; the earlier figure came from a tree state
this session cannot reconstruct).

## 3. Controls (`battery.py --controls`)

Eleven textual mutants of the emitter, each applied to a copy loaded as its own module (a pattern that does not occur exactly
once is a refusal), folded over the same 41 pairs against the cached references. **Every one caught**, at the first
(world, scenario, epoch) whose film diverged:

```
react-before-commit        CAUGHT golden-demo fuzz-20260918 epoch 6     (the reaction read the old rotor)
reset-ignored              CAUGHT golden-demo demo          epoch 4     (the demo's fault reset)
floor-shift                CAUGHT golden-demo fuzz-20260918 epoch 6     (arithmetic shift instead of toward-zero)
no-saturation              CAUGHT golden-demo fuzz-20260918 epoch 8     (wrap instead of clamp)
wire-cur-stale             CAUGHT golden-demo demo          epoch 1
relay-hot-from-cur         CAUGHT golden-demo demo          epoch 3
once-no-latch              CAUGHT golden-demo demo          epoch 4     (p1 once-at-1 refires when k wraps at 4)
onehot-phase-off-by-one    CAUGHT golden-demo demo          epoch 1
binary-phase-off-by-one    CAUGHT binary-40-phase-3 demo    epoch 2     (the only mutant the demo world cannot see)
fault-not-sticky           CAUGHT golden-demo fuzz-20260919 epoch 4
react-without-fire         CAUGHT golden-demo demo          epoch 1
```

Three of the four numeric mutants (toward-zero shift, saturation, commit-before-react) are caught only by the random
scenarios, not by the demo scenario: the demo's rotors are the unit and full scale, and its products never carry a negative
remainder or exceed the lane. That is the reason the fuzz exists; without it those three would be "harmless".

## 4. What this establishes and what it does not

- The backend reproduces the calculus's per-epoch state and Film v0.7 on every world and scenario in the battery, including
  the flagship demo world whose epochs the checked Wasm host refuses (64 KiB) and whose reduction the persistent host
  (`runtime/wasm/resident/`) would still pay 0.2 s for. A WRL world that fits the battery's shapes can now be folded in
  microseconds with the calculus as the oracle beside it.
- It is not a replacement for the calculus: the calculus is the semantics, the reference and the identity spine. The
  compiled step is admitted per world by the fold, and a world outside the battery's shapes (mailbox worlds, `~~` routes, a
  lane width over 32, any field kind `state_layout` does not yield today) is refused by the emitter or unadmitted, not assumed.
- Nothing about Super: no bridge, no executor profile, no receipt. Where this would sit in the vertical witness — as a second
  `trvm.reduce` executor kind whose result the reference gate checks the same way — is a proposal for Codex, not a change.
- No performance claim beyond the table above: shared laptop, one run, medians over 7–24 epochs.

## 5. Reproduce

```bash
cd TRVM/compiled
PYTHONDONTWRITEBYTECODE=1 python3 -B battery.py --quick             # ~3 min: ic32 on the large worlds, one fuzz seed
PYTHONDONTWRITEBYTECODE=1 python3 -B battery.py --controls          # ~18 min: the full run above + the eleven mutants
```

Run with `-B` from this directory: the forge tree is another lane's and no bytecode may be written into it. The `.so` cache is
`~/.cache/trvm-compiled/` (override with `TRVM_COMPILED_CACHE`); the ic32 binary is `runtime/c/ic32` (sha256 `30d1245d…`, built
from the checked-host lane's uncommitted `ic32.c`) or `TRVM_IC32_PATH`.
