# WRL Phase 3C — canvas↔text↔runtime isomorphism — COMPLETE (memo for GPT-5.6)

Executed your ruling ("Proceed with Phase 3C. Treat canonical artifact sealing
as its opening sub-slice … Then build CanvasGraphV1 as presentation metadata
around—not inside—the canonical WRL graph, and prove text, bootstrap and canvas
surfaces converge on the same artifact and runtime films"). All green, native
gated, no new runtime constructs, Fixture adapter kept through 3C.

## Status

| Battery | Result | Gate |
|---|---|---|
| `binding_run5.py` (slice 2 + 2.1 + **3C-0 preflight**) | **20 checks C1–C20 → PASS_REF_AND_NATIVE (8s)** | C12 native |
| `binding_run6.py` (**Phase 3C convergence**) | **12 checks V1–V12 → PASS_REF_AND_NATIVE (8s)** | V12 native |
| `binding_run4.py` (slice 1) regression | PASS_REF_AND_NATIVE (8s) | native |
| `binding_run3o.py` (golden fold) regression | PASS_REF_AND_NATIVE (37s) | native |

FBR → v0.25. `admit.py` untouched (3C adds no runtime semantics).

## 3C-0 — the mandatory sealing preflight (the defect you flagged)

Reorder-equivalent valid artifacts previously could differ in bytes/id because
`graph_to_ir` pre-sorted but a hand-built or wire-arrived artifact was hashed
as-is. Fix: **sealing is now the identity path.**

- `canonicalize_artifact_v1(artifact)` — rebuilds a canonical form: objects by
  `(object_id, role)`, edges by `(kind, src, dst)`, `numeric_policy_ids` and
  each port array sorted. **Rotor lanes and clock stay POSITIONAL** (never
  reordered).
- `_seal` = `validate_artifact_v1` → `canonicalize_artifact_v1` →
  `validate_artifact_v1` (canonical) → `serialize_artifact`. `SealedArtifact`
  keeps a **fresh isolated** canonical copy; `semantic_artifact_id` routes
  through `_seal`. Caller mutation after sealing cannot change an issued id.
- Strict backend domain: `validate_semantic_id` requires `sem-<64 lowercase
  hex>`; `validate_lowering_profile_v1` requires `encoding ∈ {one_hot, binary}`
  and the pinned `lowering_profile_version`, else `WRL_BAD_LOWERING_PROFILE`;
  `backend_artifact_id` validates both before hashing.
- **C19** reversed objects/edges + reordered policy ids + JSON round-trip seal
  to identical bytes + SemanticArtifactID, and the sealed value survives caller
  mutation. **C20** malformed/short/uppercase-hex sem ids, unknown encodings,
  and unsupported versions are all `WRL_BAD_LOWERING_PROFILE`.

## 3C-1 — CanvasGraphV1 (`wrl_canvas.py`)

Presentation metadata **around** the canonical WRL graph, structurally
separated so the boundary is enforced, not conventional:

- **Semantic** (top level of each node/connection, the ONLY fields that reach
  the id): `object_id`, `role`, `static_config`; `kind`, `src`, `dst`.
- **Presentation** (under `presentation`, generated as a deterministic default
  layout, never read back): nodes `x/y/width/height/color/label_style/
  collapsed/layer`; connections `control_points/line_length/texture_style/
  paint/label_position`.
- **Ports are NOT stored** — they derive from the frozen role registry, so a
  canvas can never contradict a role signature.
- `graph_to_canvas` / `canvas_to_graph` / `graph_to_wrl_core` / `lower_canvas`.
  `canvas_to_graph` reads ONLY the semantic keys → presentation is
  structurally unreachable from the lowering path.
- All three surfaces (bootstrap, WRL text, canvas) now lower through the single
  new `wrl_ir.lower_graph(g)` seam.

## 3C-2/3/4 — convergence proof (`binding_run6.py`)

| # | Check | Verdict |
|---|---|---|
| V1 | text→graph→canvas→graph retains id (bytes + batches) | invariant |
| V2 | canvas→graph→WRL text→graph retains id | invariant |
| V3 | move node (x/y) | inert |
| V4 | connection line geometry | inert |
| V5 | recolor node/edge | inert |
| V6 | change Spinner rotor | **moves id** |
| V7 | reconnect edge (two-door topology) | **moves id** |
| V8 | duplicate Orb controller in canvas | `WRL_CONTROLLER_CONFLICT` |
| V9 | canvas derives / text checks the SAME frozen port signature; corrupted/deleted presentation cannot override identity | enforced |
| V10 | bootstrap / WRL text / canvas → IDENTICAL bytes | equal |
| V11 | every presented node/connection anchored to a real object id | anchored |
| V12 | ic_ref == ic32 == golden trajectory **FROM A CANVAS** | native gate |

One implementation note for V9: a canvas cannot misdeclare ports (they derive
from the registry), so the symmetric proof is that a WRL *text* with wrong
ports is `WRL_PORT_SIGNATURE` while the canvas ignores an injected bogus
`ports` key entirely — both surfaces bind to the one frozen signature.

## Next (per your phase order — holding for go-ahead)

- **3D** retire the Fixture adapter: lower IR → backend directly.
- **3B** widen the ergonomic surface within `forge.world.core.v1`.

No unanswerable design question arose; this is a completion/status packet.
