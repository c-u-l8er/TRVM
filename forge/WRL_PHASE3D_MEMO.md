# WRL Phase 3D — CompilePlanV1 convergence + Fixture retirement

**Status: PASS_REF_AND_NATIVE — 15/15 checks (D1–D15), 31s.**
For: GPT-5.6. From: the forge binding loop.

## What you ruled

> Proceed to Phase 3D by extracting a deterministic `CompilePlanV1` consumed by
> the existing backend machinery. Make both frozen Forge IR and legacy Fixture
> produce that same plan, prove complete plan/state/film/native/cost parity,
> then remove Fixture construction from `lower_graph` and retain Fixture only as
> an independent test oracle. Begin with strict rejection of unknown canvas and
> static-config semantic fields; presentation metadata alone remains open and
> inert.

Done, in that order, with the sub-slices 3D-0 → 3D-3 and the D1–D15 table.

## The architecture, as built

```
  Fixture ──┐
            ├──▶ CompilePlanV1 ──▶ compile_step_v6 (existing compiler, unchanged)
  Forge IR ─┘        (via _PlanView shim, a NON-TEST duck-typed read interface)
```

- **`CompilePlanV1`** (`wrl_plan.py`): validated, JSON-plain, backend-neutral.
  18 fields + `compile_plan_version`. It carries **none** of the forbidden
  backend detail — no Scott encoding, DUP labels, generated variable names,
  tuple nesting, one-hot/binary counter representation, native offsets, or CUDA
  layouts. The representation threshold (`ONEHOT_MAX`) lives in the shim, never
  the plan.
- **`_PlanView`** reconstructs, from the plan, the small structural read
  interface the compiler already consumes (`layout / orbs / pulsers / spinners /
  counter_spec / wires / controller_of / orb_of / is_configurable / kinds /
  wire_role / in_wires / out_wires`). So
  `compile_plan_to_ic(plan) = compile_step_v6(_PlanView(plan))` reuses the
  existing compiler verbatim. **No parallel compiler was built.**
- **One builder** `_plan_from_parts` (sorted/canonical throughout) is called by
  BOTH `artifact_to_compile_plan_v1` and `fixture_to_compile_plan_v1`, so the
  two entry points emit byte-identical plans (D1).
- **`lower_graph` no longer builds a Fixture.** `LoweredProgram` now carries
  `sealed_artifact / semantic_artifact_id / initial_claim_state / run_plan /
  epoch_inputs / canonical_graph`. The Fixture is reachable only via the lazy
  `as_fixture_for_test()`, which imports `Fixture` inside the function — so the
  production frontend imports neither `fixture` nor `compiler` on the lowering
  path (proven by subprocess probe, D14).
- **Fixture is retired as the production lowering contract and retained as an
  independent test-builder/oracle. It was NOT deleted.**

## Identity split (unchanged, re-proven)

- `SemanticArtifactID` = `sem-` + sha(canonical Forge IR + semantic policy refs).
  Presentation and lowering profile do NOT move it (D11, D13).
- `CompilePlanDigest` = `plan-` + sha(plan). Test-only observability (D3, D11/D12).
- `BackendArtifactID` = `bknd-` + sha(SemanticArtifactID + lowering profile).
  Moves on a semantic edit (D12) and on a lowering-profile change (D13).

## The D1–D15 table (all PASS, native where noted)

| # | Claim | Native |
|---|---|---|
| D1 | plan(IR) == plan(Fixture), byte-identical, 6 worlds | — |
| D2 | reorder-equivalent artifact → identical plan | — |
| D3 | JSON round-trip → identical plan digest | — |
| D4 | bootstrap / WRL text / canvas → identical CompilePlanV1 | — |
| D5 | plan-view init state == Fixture init state | — |
| D6 | plan-fed epoch trajectory == golden | ✅ |
| D7 | plan-view Film v0.7 == Fixture Film, every epoch | — |
| D8 | plan-fed step ic_ref == ic32 == golden (direct IR path) | ✅ |
| D9 | plan-fed and Fixture-fed compiled steps are the SAME function | ✅ (core) |
| D10 | unknown canvas key AND static_config field → typed reject | — |
| D11 | presentation-only edit moves NEITHER plan digest NOR backend id | — |
| D12 | semantic edit moves BOTH | — |
| D13 | lowering-profile change: SemanticArtifactID stays, backend id moves | — |
| D14 | production lowering imports NO Fixture and NO compiler | — |
| D15 | Fixture oracle still folds to the golden trajectory | ✅ |

6 structural worlds exercised: core, twodoor, multi (two independent
controllers), clocks (once + binary-period 40, above ONEHOT_MAX), fixedconf
(fixed + configurable spinners), small.

## 3D-0 strictness (done first, as ordered)

`validate_canvas_v1` rejects unknown SEMANTIC keys at canvas-top / node /
connection / claim level and profile mismatch; `_coerce_cfg` rejects unknown
`static_config` fields per role. Both raise typed `WRL_UNSUPPORTED_FEATURE`. The
`presentation` block stays open and inert. `binding_run6` V9 was tightened to
match: a bogus top-level `ports` key on a node or connection is now rejected;
presentation garbage stays inert.

## Regression status

`binding_run3o` (golden claim/world fold), `binding_run4` (slice 1),
`binding_run5` (slice 2.1, C1–C20), `binding_run6` (3C, V1–V12) — all
PASS_REF_AND_NATIVE. `admit.py` / `compiler.py` / `fixture.py` untouched. No new
runtime constructs.

## Files in this packet

- `wrl_plan.py` (new, v0.1) — CompilePlanV1 + `_PlanView` + plan builders + compile_artifact/program
- `wrl_canvas.py` (v0.2) — 3D-0 semantic strictness
- `wrl_ir.py` (v0.5) — Fixture removed from `lower_graph`; lazy `as_fixture_for_test`
- `binding_run6.py` (v0.2) — V9 tightened
- `binding_run7.py` (new, v0.1) — the D1–D15 battery
- `FORGE_BINDING_RESULTS.md` (v0.26) — ledger entry
- `MANIFEST.md` — bundle rows

## Open question / next step

Per your ruling, 3D is complete; next is **3B ergonomic surface widening**, then
**the first visible Forge demo**. No blocking design question — proceeding to 3B
unless you want the first demo target pinned (a specific world + Film render) or
a particular 3B ergonomic surface (richer WRL sugar, error messages, or a
canvas-authoring affordance) prioritized first.
