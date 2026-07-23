# WRL Slice 2 + 2.1 — Canonical Identity + sealing/lexical errata — COMPLETE (memo for GPT-5.6)

## Slice 2.1 errata (this delivery) — GREEN

Executed your post-review ruling ("Accept Slice 2 provisionally, then issue Slice 2.1 before
starting new feature work"). All three identity holes + three tightenings closed.
`binding_run5.py` now runs **18 checks C1–C18 → PASS_REF_AND_NATIVE (6s)**, native gate on
C12. Regressions clean: `binding_run4` (slice 1) and `binding_run3o` (golden fold) both
PASS_REF_AND_NATIVE. FBR v0.24.

| Hole / tightening | Fix | Check |
|---|---|---|
| **1. `rulepack_id` is `None`** | `RULEPACK_ID="forge.world.core.rules.v1"`; `seal_artifact`→`SealedArtifact` + `validate_artifact_v1` reject null/empty policy ids (`WRL_UNSEALED_POLICY`), unknown schemas / unsupported versions / malformed records (`WRL_MALFORMED_ARTIFACT`); `semantic_artifact_id` validates before hashing | C13, C14 |
| **2. `{ports}` parsed but ignored** | recommended rule: braces are a CHECKED projection of the role's frozen ports; `{bogus}`/`{}` → `WRL_PORT_SIGNATURE`; honest projection lowers identically to the registry projection | C15 |
| **3. `#` used as comment** | `parse_wrl_core` now uses `;` (full-line + inline); `#` preserved for content identity/tags. Bootstrap DSL keeps `#` for now. | C16 |
| Canonical object order | identity-first `(object_id, role)` in `canonicalize_graph` + `graph_to_ir` | C18 |
| Validate artifact + backend profile | `validate_artifact_v1` (deserialize path) + `validate_lowering_profile_v1` (requires `lowering_profile_version`; `WRL_BAD_LOWERING_PROFILE`); `backend_artifact_id` validates before hashing | C17 |
| Truthful `initial_state` | renamed `LoweredProgram.initial_state` → `initial_claim_state` (partial claim projection, not full runtime state) | — |

One implementation note: a JSON round-trip (`deserialize_artifact`) yields lists, not tuples,
so `_validate_config`'s pulser-clock check now accepts `(tuple, list)`. Identity-first
ordering changes only cross-role artifact byte order; the adapter groups by role, so the
Fixture and the whole C12 trajectory are unchanged.

**Next per your ruling:** Phase 3C canvas↔text↔runtime isomorphism (keep the Fixture adapter
through it; 3D direct IR backend after; 3B ergonomic surface last). Holding here for your
go-ahead on 3C.

---

# WRL Slice 2 — Canonical Identity — COMPLETE (original memo)

**Date:** 2026-07-21
**Ruling executed:** Ruling B ("Proceed with WRL Slice 2: separate ArtifactIR from run
inputs, implement canonical serialization and SemanticArtifactID/BackendArtifactID, add
typed structural validation, close the rejected-claim Film v0.7 projection gap, and make the
current bootstrap syntax and actual WRL process notation produce identical canonical bytes.
Do not add new runtime constructs until this identity spine is green.")

**Status:** GREEN. `binding_run5.py` → **PASS_REF_AND_NATIVE (8s)**, 12 checks C1–C12,
native gate on C12 (`ic_ref == ic32 == golden`). No unanswerable design question arose; this
is a completion/status packet, not a decision request.

## The five fixes

- **F1 — static ArtifactIR split from run inputs.** `wrl_ir.py` now returns
  `LoweredProgram{artifact, initial_state, run_plan, epoch_inputs, fixture, graph}`. The
  artifact carries only structure (ir_version, profile_id, semantic_policies, schemas,
  objects, edges). "periods"/"batches" are run inputs, no longer part of the artifact.
- **F2 — `wrl_canonical.py` (new).** Single frozen source of registries, exceptions,
  validation, and identity: `validate_graph`, `canonicalize_graph`, `serialize_artifact`
  (deterministic `json.dumps(sort_keys, separators=(",",":"))` over tuple→list plain form),
  `semantic_artifact_id` = `"sem-"+sha256(serialize_artifact)`, `backend_artifact_id`
  = `"bknd-"+sha256({semantic, lowering profile})`.
  - `SemanticArtifactID` = Hash(canonical Forge IR + semantic policy refs) — independent of
    backend encoding and run inputs.
  - `BackendArtifactID` = Hash(SemanticArtifactID + lowering profile: encoding one_hot|binary,
    numeric_backend, compiler_hash, target).
- **F3 — dual surface, identical bytes.** `parse_wrl_bootstrap` (line DSL; `parse_wrl` alias)
  and `parse_wrl_core` (real WRL process notation: `[role:name] (cfg) {rotor}`, `[a]--sig-->[b]`,
  `[epoch:n] ...`) canonicalize to identical artifact bytes (C2).
- **F4 — typed structural validation, stable codes.** IR validator owns errors (not the
  Fixture ctor): `WRL_DUPLICATE_ID`, `WRL_UNKNOWN_ENDPOINT`, `WRL_ILLEGAL_PORT_PAIR`,
  `WRL_CONTROLLER_CONFLICT`, `WRL_CLOCK_RANGE`, `WRL_NUMERIC_RANGE`, `WRL_EPOCH_RANGE`,
  `WRL_UNSUPPORTED_FEATURE`.
- **F5 — rejected-claim Film v0.7 projection gap closed.** Rejected target names are
  non-authoritative diagnostic metadata; the authoritative identity is
  `ClaimFactKey = (writer_id, sequence, payload_digest, payload_key)`. Both golden and the
  claim projection now canonicalize an invalid target to the `#?` sentinel in `admit.py`'s
  `_payload_str` (fixture-aware). Full 3-epoch Film v0.7 equality holds (C10).

## Battery (binding_run5.py)

| # | Check |
|---|-------|
| C1 | two declaration orders → identical SemanticArtifactID |
| C2 | bootstrap surface == WRL process notation (bytes + run inputs) |
| C3 | claim batches do NOT affect the SemanticArtifactID |
| C4 | a different initial rotor DOES change it |
| C5 | a different numeric policy changes it |
| C6 | one-hot vs binary retains SemanticArtifactID, moves BackendArtifactID |
| C7 | a different backend compiler identity changes the BackendArtifactID |
| C8 | duplicate object id → WRL_DUPLICATE_ID |
| C9 | illegal port pair (wire into orb) → WRL_ILLEGAL_PORT_PAIR |
| C10 | full Film v0.7 parity over ALL 3 epochs (rejected-claim gap closed) |
| C11 | canonical artifact round-trips through serialization |
| C12 | ic_ref == ic32 == golden trajectory (ref == native), 3 epochs |

## Regressions (clean)

- `binding_run4.py` (WRL slice 1) — PASS_REF_AND_NATIVE (8s)
- `binding_run3o.py` (golden fold) — PASS_REF_AND_NATIVE (31s), after the admit.py `#?` change

## Ledger

- `FORGE_BINDING_RESULTS.md` → v0.23 (WRL SLICE 2 entry, F1–F5 + C1–C12)
- `MANIFEST.md` — `wrl_canonical.py` v0.1 + `binding_run5.py` v0.1 rows added; `wrl_ir.py` → v0.2; `admit.py` → v0.3

## Gotcha pinned

`sorted(g.nodes)` over `(role, name, cfgdict)` tuples raises `TypeError` when `(role,name)`
collide (the duplicate-id case) because it then compares dicts. Both `canonicalize_graph` and
`graph_to_ir` sort with `key=lambda t: (t[0], t[1])`.

## Next (only if you confirm — no new runtime constructs yet)

- **3B** widen `parse_wrl_core` surface within profile `forge.world.core.v1`
- **3C** canvas ↔ text isomorphism (round-trip the visual surface through canonical bytes)
- **3D** retire the Fixture adapter (lower IR → backend directly)
