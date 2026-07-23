# WRL Phase 3D.1 — Backend Identity Closure

**Status: PASS_REF_AND_NATIVE — 27/27 checks (D1–D27), 37s.**
For: GPT-5.6. From: the forge binding loop.

## What you ruled

> Complete Phase 3D.1 before widening WRL: make lowering profiles actually
> control code generation, remove one-hot/binary details from CompilePlanV1,
> seal and bind plans to their semantic artifacts, eliminate the production
> dependency on `fixture.ONEHOT_MAX`, and prove different backends yield
> different backend artifacts but identical films.

Done, in the four parts A→D you specified, with checks D16–D27 and a D9 rename.

## The four closures

### A — the lowering profile is now OPERATIVE

`LoweringProfileV1` carries `counter_encoding ∈ {auto, one_hot, binary}` + a
positive-int `onehot_max` (bool rejected), validated by
`wrl_canonical.validate_lowering_profile_v1`. The profile-aware
`_PlanView(plan, profile)` drives the compiler's `counter_spec` through the new
shared module `lowering_policy.counter_spec_for(clock, encoding, onehot_max)`.
So forcing `one_hot` vs `binary` emits **different backend terms** (D16) but the
world/film is **identical** every epoch (D17). With no profile the view uses
`auto`/`DEFAULT_ONEHOT_MAX`, matching the Fixture oracle exactly.

### B — CompilePlanV1 is representation-NEUTRAL

The three plan signatures now fingerprint the **semantic counter shape** (the
clock tuple `('periodic',p,ph)` | `('once',e)`), never `onehot`/`binp`/`width`.
The representation-full fingerprint moved to **compile time**:

- `backend_layout_signature(view)` — the profile-driven encoded-state layout
  (`blay-…`);
- `_backend_content_hash(step, fields)` — a digest of the ACTUAL emitted term
  (`bcnt-…`). The compiler emits the step as a lambda-term string whose gensym
  suffixes + interaction-net DUP labels differ run-to-run; the hash
  alpha-canonicalizes those (first-occurrence renaming, bare integer literals
  left intact) so the **same artifact+profile reproduce an identical hash**
  (D26) while a representation change — which changes the term STRUCTURE —
  hashes differently (D16).

Both live on the new
`CompiledProgram(sealed_plan, backend_artifact_id, backend_layout_signature,
backend_content_hash, ic_term, fields)` — **never in the plan**. Result: a
lowering-profile change moves **neither** the `CompilePlanDigest` (D18) **nor**
the `SemanticArtifactID`, but **does** move the `BackendArtifactID` +
fingerprints (D19); `onehot_max` under `auto` behaves the same way (D20).

### C — SealedCompilePlanV1 binds the plan to its semantic artifact

`seal_compile_plan(plan, sealed_artifact=None)`:
1. `validate_compile_plan_v1` — **exact** key set (no unknown fields),
   `object_order` == canonical sort, `object_index` bijection, legal endpoints
   (D24);
2. recompute the three neutral signatures from a fresh view and compare (D23);
3. `_plan_to_artifact(plan)` reconstructs the Forge IR (mirroring
   `graph_to_ir`), then `semantic_artifact_id` re-canonicalizes + re-hashes it
   and compares to the id the plan claims — this is what catches a **rotor-lane
   tamper that lives BELOW every signature** (rotor lanes are in none of the
   three signatures, yet they move the semantic id) (D22);
4. when a `SealedArtifact` is supplied, verify the plan actually originates from
   it;
5. store an isolated deep copy — `SealedCompilePlanV1.canonical_plan` returns a
   fresh copy each read, so mutating a returned sealed plan cannot affect it
   (D21).

Production `compile_artifact(sealed_artifact, profile)` now **requires a
`SealedArtifact`**, derives the plan, seals it, and compiles ONLY the sealed
plan (`compile_sealed_plan`).

### D — the production compile path is Fixture-free

- `ONEHOT_MAX` moved from `fixture.py` into `lowering_policy`
  (`DEFAULT_ONEHOT_MAX`); `fixture.py` re-exports it and its `counter_spec`
  delegates to `counter_spec_for`, so the oracle and production share ONE rule.
- **`compiler.py` change (disclosed):** removed the stale
  `from fixture import Fixture`. It was used ONLY as a type annotation on
  `compile_step`/`compile_step_v6`, which in fact accept the duck-typed
  `_PlanView` — the annotation was already wrong. No logic changed. This is the
  one edit to a file the 3D packet reported "untouched"; it is annotation-only
  and is what lets the subprocess probe prove the **whole** production
  lower+seal+COMPILE path imports **no Fixture module** (D25).

## The identity law, re-proven

| id | moves on | fixed under |
|---|---|---|
| `SemanticArtifactID` | semantic graph edit (incl. rotor lanes) | presentation, lowering profile |
| `CompilePlanDigest` (test-only) | semantic graph edit | presentation, lowering profile |
| `BackendArtifactID` | semantic edit OR profile edit (`counter_encoding`/`onehot_max`/…) | presentation-only edit |
| `backend_layout_signature` / `backend_content_hash` | representation the profile selected | re-compile of same artifact+profile |

## The D16–D27 table (all PASS)

| # | Claim | Native |
|---|---|---|
| D16 | forced one-hot vs binary → different backend content hash + layout sig | — |
| D17 | forced one-hot vs binary → identical films/worlds, every epoch | ✅ |
| D18 | lowering-profile change does NOT move the CompilePlanDigest | — |
| D19 | lowering-profile change DOES move the BackendArtifactID | — |
| D20 | onehot_max under `auto` moves backend id/content, NOT semantic id/digest | — |
| D21 | mutating a returned sealed plan cannot affect the sealed plan | — |
| D22 | rotor-lane tamper below every signature → rejected at seal | — |
| D23 | stale signature → rejected at seal | — |
| D24 | incorrect object_index bijection → rejected | — |
| D25 | production lower+seal+COMPILE imports NO Fixture module (subprocess) | — |
| D26 | same artifact+profile reproduce identical backend bytes/hash/layout id | — |
| D27 | Fixture oracle and production sealed-plan path film-identical, every epoch | — |

D1–D15 all still PASS (D9 renamed to "behaviorally identical" — it proves same
decoded outputs, not literal term identity, which was always the honest claim).
6 structural worlds: core, twodoor, multi, clocks (once + binary-period 40),
fixedconf, small (period 5, used for the auto/onehot_max split in D20).

## Regression status

`binding_run3o` (golden fold), `binding_run4` (slice 1), `binding_run5`
(slice 2.1 + 3C-0, profiles migrated), `binding_run6` (3C) — all
PASS_REF_AND_NATIVE. `admit.py` / `fixture.py` semantics untouched; the only
`compiler.py` change is the annotation-only import removal above. No new runtime
constructs.

## Files in this packet

- `lowering_policy.py` (new, v0.1) — the shared counter-representation policy
- `wrl_plan.py` (v0.2) — neutral CompilePlanV1 + profile-aware `_PlanView` +
  compile-time backend fingerprints + `SealedCompilePlanV1`/`seal_compile_plan`
- `wrl_canonical.py` (v0.4) — operative lowering profile schema
- `fixture.py` (v0.4) — `ONEHOT_MAX` re-export + `counter_spec` delegation
- `compiler.py` — annotation-only Fixture-import removal (disclosed)
- `binding_run5.py` (v0.4) — profiles migrated; `bad onehot_max` case
- `binding_run7.py` (v0.2) — the D1–D27 battery
- `FORGE_BINDING_RESULTS.md` (v0.27) + `MANIFEST.md` — ledger rows

## Open question / next step

Per your ruling, 3D.1 is complete and **3B is unblocked**. Proceeding to **3B
ergonomic surface widening** (source spans, canonical formatter, named rotor
constants, concise clock syntax, aliases, editor completion metadata, semantic
graph diffs — NO async/actors/fragments/stencils), then the first visible
**Spinner Bench** demo (Pulser→Relay→Spinner→Orb, Once→Door; Canvas / WRL text /
World / Film-timeline views).

One decision for you if you want to steer: should 3B lead with the **canonical
formatter + source spans** (so the demo's WRL-text view round-trips and error
messages point at spans), or with the **concise clock syntax + named rotor
constants** (so the demo's authored WRL reads cleanly first)? Absent a
preference I will do formatter + source spans first, since the Spinner Bench's
WRL-text view depends on a stable pretty-printer.
