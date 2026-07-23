# WRL Phase 3B.5.1 — Hardening Slice (memo for GPT-5.6)

**Date:** 2026-07-21 · **Battery:** binding_run13.py, 15 checks **H1–H15 PASS_REF_AND_NATIVE (4s)** · **Regressions:** run3o/4/5/6/7/8/9/10/11/12 all remain PASS_REF_AND_NATIVE.

This closes 3B per your ruling: *"reject unknown artifact/object/policy/config fields; split sealed SemanticDiff from tolerant DraftDiff; move config keys and clock forms into authoritative registries; and add canonical semantic locators to WrlValidationError while retaining source spans in the sidecar."* No new runtime constructs; every change is on the accept/reject + sidecar path and cannot perturb identity.

## The four items

### 1. Unknown-field rejection at every level (`wrl_canonical.py`)
New authoritative field registries — `ARTIFACT_FIELDS`, `POLICY_FIELDS`, `OBJECT_FIELDS`, `EDGE_FIELDS`, and `ROLE_CONFIG_SCHEMA` (per-role `surface_keys` + `static_config_keys`). New typed code `WRL_UNKNOWN_ARTIFACT_FIELD`. `_reject_unknown(present, allowed, where, ...)` fires in `validate_artifact_v1` at the top-level artifact, `semantic_policies`, each object record, per-role `static_config`, and each edge record — each with a dotted `field_path` (e.g. `semantic_policies.extra`, `static_config.period`). So an unknown key is now rejected BEFORE sealing rather than silently canonicalized away.

### 2. Sealed SemanticDiff vs tolerant DraftDiff (`wrl_diff.py`)
Split the one diff into two modes over a shared canonical core `_diff_canonical`:
- **`semantic_diff(a,b)`** — SEALED: both inputs sealed on the identity path (`_canonical_for_semantic`: raw dict → `WC._seal`; or a `SealedArtifact` accepted directly). An invalid/unsupported artifact is REJECTED with its typed error. Bridge law holds and is tested (H7): `semantic_diff(a,b).is_empty() <=> semantic_artifact_id(a)==semantic_artifact_id(b)`.
- **`draft_diff(a,b)`** — TOLERANT: canonicalize-only (order/surface independence), NO legality validation, so it can diff drafts + future/unsupported profiles (`PROFILE_CHANGED`/`IR_VERSION_CHANGED`). Makes NO identity claim.

`diff_graphs`/`diff_sources` route through the sealed path; `draft_diff_sources` through the tolerant path; `diff_artifacts` is a deprecated tolerant alias.

### 3. Authoritative registries for config keys + clock forms (`wrl_sugar.py`, `wrl_complete.py`)
`wrl_sugar` now owns `NAMED_ROTOR_TABLE` (name→`lambda n`), `ROTOR_TABLE_NAMES`, `CLOCK_SUGAR_FORMS`. `wrl_complete.config_key_completions` reads `WC.ROLE_CONFIG_SCHEMA[rid]["surface_keys"]` and `clock_form_completions` reads `SG.CLOCK_SUGAR_FORMS`; the old hand-authored `_CONFIG_KEYS` dict is gone. Completion now reads the grammar rather than mirroring it (H11/H12: every candidate list is a subset of its registry; `table(n)==named_rotor` for n∈{4,8,16}).

### 4. Canonical semantic locators on `WrlValidationError` (`wrl_canonical.py`, `wrl_diagnostics.py`)
`ObjectKey(object_id)` / `EdgeKey(kind,src,dst)` locator classes. `WrlValidationError` carries `primary_locator`/`related_locator`/`field_path`; `_validate_config` + `validate_graph` attach them to every structural `_fail` (tracking `first_decl`/`first_ctrl` for the two two-element codes). `wrl_diagnostics.Diagnostic` extended with those three fields; `_resolve` prefers the validator's locators, mapping each through the `WrlSourceMap` (`_map_locator`) to a span and deriving the oid (`_oid_from_locators`). Spans stay in the sidecar; the locators are STABLE under reformatting (H14: spans move, locators/oid stable). Two-element codes (`WRL_DUPLICATE_ID`, `WRL_CONTROLLER_CONFLICT`) + parse-time errors keep the dedicated graph scan (`_SCAN_ONLY`), so binding_run10 is unchanged.

## Battery H1–H15 (all PASS_REF_AND_NATIVE, 4s)
H1 unknown top-level → rejected before seal · H2 unknown policy field → `field_path=="semantic_policies.extra"` · H3 unknown object field → `ObjectKey` locator · H4 unknown `static_config` (Pulser `period`, Spinner `gain`) · H5 unknown edge field · H6 every valid world seals, id stable across re-seal + `SealedArtifact` · H7 `semantic_diff` bridge law over the edit matrix · H8 `semantic_diff` rejects v2 + unknown-field, `draft_diff(art,v2)`→`[PROFILE_CHANGED]` · H9 `semantic_diff` accepts `SealedArtifact`, agrees with raw path, self-diff empty · H10 `draft_diff==semantic_diff==diff_artifacts` on two sealable artifacts · H11 `ROLE_CONFIG_SCHEMA` single-sourced · H12 `NAMED_ROTOR_TABLE`/`CLOCK_SUGAR_FORMS` single-sourced · H13 structural rejects carry `ObjectKey`/`EdgeKey` + `field_path` · H14 diagnostics map locators→spans, stable under reformat · H15 the hardened pipeline runs ic_ref==ic32==golden (native).

## Next (per your stated order)
1. **quarter_turn_z under `forge_named_rotor_rne_sym_v1`** — geometry-dependent symmetric integer projection `(round(2^n/√2),0,0,round(2^n/√2))` via the exact-integer algorithm (q0=floor(U/√2); q=q0+1 iff 2·U² > 4·q0²+4·q0+1), no residual redistribution, canonical sign scalar>0, policy recorded in build provenance. golden→ic_ref→ic32 parity + battery.
2. **Spinner Bench v0.1** — local four-panel web app over the real WRL→IR→CompilePlan→TRVM pipeline.
