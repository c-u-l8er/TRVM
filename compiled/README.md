# The compiled backend for WRL worlds — CompilePlanV1 → one C step function, admitted by the interaction-calculus fold

**2026-09-18.** The re-layering Travis ruled this morning: keep `ic32` as the semantic oracle and the executor for small
worlds; build ONE compiled backend for WRL worlds (Forge IR → C state machine), **admitted only when its fold equals the IC
reference on every sealed world** (the compiled-home discipline of `FOUNDATION_LANE.md` §3b: the oracle exists before the
home does); the 9.2 MB demo epoch as the acceptance test. This directory is that backend and its admission.

Status: **BUILT and ADMITTED on this battery — 17 worlds, 53 (world, scenario) pairs, 983 epochs, film-equal AND
state-equal on every one; 14 of 14 mutants caught, each by exactly the worlds expected. Development reading on the shared
laptop.** Widened 2026-09-18 afternoon (§2b): two mailbox worlds with `~~` routes and a 33-lane spinner, each with a mutant
only it catches. Not claimed: a new semantic identity (none moves), a Super integration, anything about worlds the battery
does not contain, or a production figure. The morning record (14 worlds / 41 pairs / 746 epochs / 11 mutants) is superseded
by this one; `results-battery.json` is the afternoon run.

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
and never with the semantic id — the split `wrl_canonical` names, at a fourth representation. (So every `cbknd-` of the
morning record moved when the emitter changed in the afternoon — `sx` now sign-extends in i128 so lanes to 63 bits are
emitted — while every semantic id stayed; and the two mailbox worlds emit byte-identical C, `eaef13aa…`, under two different
`cbknd-` ids, which is D8 read off the backend: the mailbox contributes nothing physical.)

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
| mailbox-routes / mailbox-overflow (§2b) | 2.64–2.81 M | ic_ref 0.70–0.95 s | 8–12 µs | 8 · 158 | AGREE (films differ from the mailbox-free twin's from epoch 1) |
| spinner-w33-n16 (§2b; 46 MB term) | 46,223,509 | ic32 file mode **6.5–8.1 s** (ic_ref 34 s on epoch 1) | 6–13 µs | 4 · 79 | AGREE (demo scenario: ic_ref and ic32 -reparse agree) |

**BATTERY: ALL AGREE (53 pairs, 3,222 s wall, almost all of it the calculus; the morning's 41 pairs took 1,066 s).** On the
acceptance test — the demo world's 9.5 MB epoch — the compiled step is about 25,000× the ic32 reduction and about
400,000× ic_ref; on `two-spinners` about 350,000× ic_ref; on the 33-lane spinner about 800,000× ic32. The compiled step's
cost is linear in the world (chain120 at 91 µs is the largest), and the Python encode/decode around the C call is most of
every microsecond figure; the C itself is well under that.

**The term-bytes drift, explained.** The morning record measured the demo epoch term at 9,509,628 B against 9,177,234 B on
2026-09-16 (§3ai) with identical films and could not say why. The cause: Forge's lowering names binders from a
process-global counter, so `compile_step_v6(view)` returns a different text on every call — chain10's step is 1,888 B on a
fresh counter, 2,080 B on the next call, 2,986 B after the demo world has been lowered in the same process; pulser-relay's
epoch term is 738 B in the battery (after sixteen worlds) and 474 B when run first. The term's byte size is a property of
the process's history, not of the world; the normal form printed canonically (`ic_ref.show`) is the same. Quote a term size
only with the process that produced it, and never as identity — `wek/b2/trvm/COMPILED_EXECUTOR_PROPOSAL.md` §3 says what
that means for `term_sha256`.

### 2b. The widening (2026-09-18, afternoon) — what each new shape admits, and why each needed its own mutant

The morning record listed mailbox worlds, `~~` routes and lane widths over 32 as refused or unadmitted. Each is now in the
battery with a reference fold and a mutant that only it catches; the rule was that a widening whose mutant an older world
already catches has not widened anything.

- **Mailbox worlds and `~~` routes** (`mailbox-routes`: a mailbox of capacity 2 receiving one route at epoch 2 and one at
  epoch 3 from two `once` pulsers; `mailbox-overflow`: capacity 1 receiving two routes in the same epoch, so the capacity
  fault latches). A mailbox is CLAIM state, not world state (D8; Slice B commit 5b put it there), so the compiled STEP never
  sees it — `state_layout` yields no mailbox field and the two worlds emit the same C as their mailbox-free twin. What these
  worlds admit is the compiled FOLD's plumbing: that `_script_for` folds the world's route Sends into the scenario's
  batches and that `film_hash_v7` renders the mailbox block and ledger — the two halves the memo for Slice B commit 4 says a
  run path forgets first ("green, plausible, and wrong"). Their mutants are therefore mutants of `fold.py`, not of the
  emitter: `film-without-mailboxes` (the film rendered with `mailboxes=None`) and `script-without-routes` (the scenario's
  claims without the world's own Sends). Each is caught by both mailbox worlds at epoch 1 and 2 respectively, and by no other
  world, because a route-free world's film and script are byte-identical under either mutant. The fuzz scenarios' writer ids
  now run 1..14: writer 15 is `WC.ROUTE_WRITER_ID`, reserved for a world's routes, and a scenario writing under it is refused
  against a route-bearing world (no earlier scenario reached the sequence where `% 15` would first have minted it, so the
  morning's fuzz digests are unchanged).
- **A 33-lane spinner** (`spinner-w33-n16`, the first width over 32). The emitter's bound was 32 because `sx` sign-extended
  in i64 (`1 << w` overflows at 63) — now `sx` works in i128 and the bound is 63, the last width whose 4-term accumulator
  `|acc| ≤ 2^(2w)` fits `__int128` and whose lanes fit an int64 slot. Its epoch term is 46 MB: over the **16 MiB `static
  char buf[1<<24]` ic32 reads from stdin** (`runtime/c/ic32.c`; a wider term is silently truncated and refused as `parse
  error: expected name` at the end of input — the checked-host lane's file, not changed here), so the calculus reaches it
  through `fold.ic32_reparse`: ic32's `-reparse STEP ARGS` file mode, which rebuilds and reduces the same text
  `((STEP CONFIG) STATE)`. The reference is the production `_run_traj` handing that adapter its own term (`fold.split_term`
  finds the two small tails from the end by paren depth, because the step cannot be regenerated to find the boundary — see
  the drift above); on the demo scenario ic_ref is the reference (34 s per epoch) and ic32 -reparse the cross-check, and
  they agree. Its mutant, `narrow-product-i64`, forms each rotor·pose product in 64 bits (wrapping deterministically through
  uint64): exact for every lane under 2^31.5, so no earlier world can see it; caught by the wide world's first fuzz scenario
  at epoch 8, when both a rotor and a pose lane sit at full scale.

Not widened: lane widths between 34 and 63 are emitted and unadmitted (no world in battery); width 64 is refused;
`~~` routes with a source that is not a `once` pulser do not exist (the seal refuses them); recurring routes
(`forge.world.async.v1`) are deferred by ruling Q3 and not lowered by anything.

## 3. Controls (`battery.py --controls`)

Fourteen textual mutants — twelve of the emitter, two of the fold — each applied to a copy loaded as its own module (a
pattern that does not occur exactly once is a refusal), and since the afternoon folded over EVERY pair (the compiled fold is
microseconds, so the full catch set costs nothing), so the record says which worlds catch a mutant, not only that one did.
**Every one caught, and the three widening mutants each caught only by the worlds their widening added** (`controls/SUMMARY.txt`):

```
react-before-commit        CAUGHT golden-demo fuzz-20260918 epoch 6     by the 8 spinner worlds (all but w16-fixed)
reset-ignored              CAUGHT golden-demo demo          epoch 4     by the 9 spinner worlds
floor-shift                CAUGHT golden-demo fuzz-20260918 epoch 6     by 8 spinner worlds -- NOT the 33-lane one (its fuzz never left a negative remainder)
no-saturation              CAUGHT golden-demo fuzz-20260918 epoch 8     by the 8 configurable-spinner worlds
wire-cur-stale             CAUGHT golden-demo demo          epoch 1     by all 16 wired worlds
relay-hot-from-cur         CAUGHT golden-demo demo          epoch 3     by the 9 worlds with a relay
once-no-latch              CAUGHT golden-demo demo          epoch 4     by the 5 worlds with a once-pulser
onehot-phase-off-by-one    CAUGHT golden-demo demo          epoch 1     by 13 worlds
binary-phase-off-by-one    CAUGHT binary-40-phase-3 demo    epoch 2     by binary-40-phase-3 ONLY
fault-not-sticky           CAUGHT golden-demo fuzz-20260919 epoch 4     by the 9 spinner worlds
react-without-fire         CAUGHT golden-demo demo          epoch 1     by the 9 spinner worlds
narrow-product-i64         CAUGHT spinner-w33-n16 fuzz-20260918 epoch 8 by spinner-w33-n16 ONLY   (widening, as expected)
film-without-mailboxes     CAUGHT mailbox-routes demo       epoch 1     by the 2 mailbox worlds ONLY (widening, as expected)
script-without-routes      CAUGHT mailbox-routes demo       epoch 2     by the 2 mailbox worlds ONLY (widening, as expected)
```

Three of the four numeric mutants (toward-zero shift, saturation, commit-before-react) are caught only by the random
scenarios, not by the demo scenario: the demo's rotors are the unit and full scale, and its products never carry a negative
remainder or exceed the lane. That is the reason the fuzz exists; without it those three would be "harmless". The catch
sets are a second kind of evidence: a world that catches nothing a smaller world does not catch is not earning its place,
and each of the seventeen now catches something in a set no strict subset of the others covers — except the two mailbox
worlds, which catch the same set as each other by construction (their C is identical) and exist for the capacity fault.

## 4. What this establishes and what it does not

- The backend reproduces the calculus's per-epoch state and Film v0.7 on every world and scenario in the battery, including
  the flagship demo world whose epochs the checked Wasm host refuses (64 KiB) and whose reduction the persistent host
  (`runtime/wasm/resident/`) would still pay 0.2 s for, and a 33-lane spinner whose 46 MB epochs ic32 cannot even read from
  stdin. A WRL world that fits the battery's shapes can now be folded in microseconds with the calculus as the oracle beside it.
- **Its state renders to the calculus's exact normal-form bytes** (`payload.py` → `results-payload.json`):
  `ic_ref.show(ic_ref.parse(enc_state_v6(view, state)))` is byte-identical to the line ic32 prints for the same epoch on every
  epoch of every world's demo scenario (17 worlds, 119 epochs; the 30-relay world's epoch 1 renders to the 3,260 B whose
  sha256 `2318bd82…` the vertical witness receipts). The rendering costs 0.03–4.6 ms in Python (chain120 the largest), 10–70×
  the step. This is what lets the compiled step be proposed as a second `trvm.reduce` executor kind under the witness's
  unchanged reference gate — `wek/b2/trvm/COMPILED_EXECUTOR_PROPOSAL.md`, design only, waiting on the resident host's admission.
- It is not a replacement for the calculus: the calculus is the semantics, the reference and the identity spine. The
  compiled step is admitted per world by the fold, and a world outside the battery's shapes (a lane width over 63 is refused
  by the emitter; widths 34–63 and any field kind `state_layout` does not yield today are unadmitted) is refused or
  unadmitted, not assumed. Mailbox worlds, `~~` routes and w=33 are inside the shapes since §2b.
- Nothing about Super: no bridge, no executor profile, no receipt. Where this would sit in the vertical witness — as a second
  `trvm.reduce` executor kind whose result the reference gate checks the same way — is a proposal for Codex, not a change.
- No performance claim beyond the table above: shared laptop, one run, medians over 7–24 epochs.

## 5. Reproduce

```bash
cd TRVM/compiled
PYTHONDONTWRITEBYTECODE=1 python3 -B battery.py --quick             # ~10 min: ic32 on the large worlds, one fuzz seed, ic32 file mode on the wide world
PYTHONDONTWRITEBYTECODE=1 python3 -B battery.py --controls          # ~55 min: the full run above + the fourteen mutants over every pair
PYTHONDONTWRITEBYTECODE=1 python3 -B payload.py                     # ~2 min: the compiled state as the calculus's normal-form bytes, every world
PYTHONDONTWRITEBYTECODE=1 python3 -B battery.py --quick --worlds mailbox-routes,spinner-w33-n16   # a development subset; not an admission
```

Run with `-B` from this directory: the forge tree is another lane's and no bytecode may be written into it. The `.so` cache is
`~/.cache/trvm-compiled/` (override with `TRVM_COMPILED_CACHE`; the wide world's 46 MB step files land under `reparse/` there
and are not cleaned by the run); the ic32 binary is `runtime/c/ic32` (sha256 `30d1245d…`, built from the checked-host lane's
uncommitted `ic32.c`) or `TRVM_IC32_PATH`. ic_ref on the wide world's demo scenario needs ~4 min and a few GB; the run was
made under `ulimit -v 14000000` once to be sure it fits this laptop.
