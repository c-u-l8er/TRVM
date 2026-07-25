# Forge Spinner Bench v0.7.0-alpha.4 — v0.7-3.1 Template Reopen Closure (memo for GPT-5.6)

**Date:** 2026-07-23 · Implements your **v0.7-3.1** ruling in full: close the two
reopen gaps left by the Immutable Template Catalog **before** any visual polish.
**No new semantic profile, IR version, artifact identity, actor role, edge type,
graph transaction, or runtime law.** The Golden/Bench demo world still seals to
the frozen `DEMO_WORLD_SEMANTIC_ID = sem-8ae91fe9…fe4a`; the Blank keeps its own
`sem-0a8dab60…4c9f`; every fold is byte-identical to v0.6-4.

**Base commit:** `f30e88a6e7b5d9c8fc72e2638d24626e7eee7f70` (the last pushed
TRVM commit). The packet ships the full modified `wrl_project.py`, `wrl_converge.py`,
`spinner_bench.py`, and `spinner_bench.js`, plus `binding_run41.py`, so every
touched file is present as complete source (not just a diff).

**Your three tightening patches — all applied (this cut):**

1. **`CanvasSession` owns + validates the layout seed centrally.**
   `CanvasSession.__init__(draft, layout=None)` now does
   `seed = CV.validate_layout_v1(copy.deepcopy(layout)) if layout is not None else None`
   before `_layout_from_draft(seed=seed)`. The session deep-copies **and** validates
   at the API boundary, so callers (`_template_preview_payload`,
   `_template_use_payload`, `create_from_source`) pass the raw manifest layout with
   no pre-copy/pre-validate — the redundant call-site `copy.deepcopy` and the now-unused
   `import copy` in `spinner_bench.py` were removed.
2. **"presentation-equivalent by object ID + edge key"** replaces "byte-equivalent"
   everywhere (PC25/PC26 labels, this memo). The comparison is over stable
   `object_id` / `edge_key` presentation maps (order-independent), not literal bytes.
3. **PC30 native independently verifies the reopened project source.** The native
   gate now creates the Golden-derived project → changes layout → persists → reopens
   from a **fresh cache** → `_verify_payload(ov30n["view"]["text"], oracle=True)`, so
   the label and the assertion coincide exactly (it verifies the *reopened project
   source*, never the template source).

`presentation_revision` is **deferred to v0.7-5** per your ruling — not added here.

## The two gaps you flagged — both closed

### 1. The manifest `canvas_layout` is no longer dead data

It is now **applied identically in both the Explore (preview) and Use paths**, as
presentation metadata that **moves no semantic identity**.

- `wrl_converge.CanvasSession.__init__(draft, layout=None)` and
  `new_session(program_or_artifact, draft_id, layout=None)` accept a curated
  `CanvasLayoutV1` and reconcile it onto the draft's working graph via the
  existing `_layout_from_draft(seed=…)` (surviving objects/edges keep the seeded
  presentation by `object_id`/`edge_key`; newcomers get deterministic defaults;
  extras drop). Presentation never influences the `SemanticArtifactID`.
- `wrl_project.ProjectSessionCache.create_from_source(..., layout=None)` threads
  the seed into `new_session` and **persists** it with the project.
- `spinner_bench._template_preview_payload` and `_template_use_payload` now seed
  `copy.deepcopy(m["canvas_layout"])`.

**Invariant (your wording, tightened per Patch 2):** *Explore and Use begin with a
presentation-equivalent layout **by object ID and edge key**, while layout remains
outside semantic identity.* Verified by PC25 + PC26 (the comparison is over stable
`object_id` / `edge_key` presentation maps, order-independent — not literal bytes).

### 2. Template scenarios are rehydrated on reopen (the more serious bug)

Model: **templates seed projects; once created, the project owns its scenario
documents and no longer depends on the template catalog.**

- Server: `_project_open_payload`, `_project_fork_payload`, and
  `_template_use_payload` now return `scenario_documents` +
  `selected_scenario_document_id`, sourced from the **project doc on disk**
  (`_project_scenario_docs(pid)` → `PJ._scenarios_of(doc)`,
  `PJ._selected_scenario_of(doc)`). No catalog or provenance lookup on reopen.
- Client: new `loadProjectScenarios(scenarioDocs, selectedId)` builds
  `state.presets` from the project's persisted `{name, scenario_digest, scenario}`
  docs. `openSession(pid)` now calls it for **every** reopen (falling back to the
  global `/api/scenario` presets only for a legacy V1 project with no persisted
  scenarios). `doUseTemplate` no longer threads a template loader — the created
  project's own scenarios are loaded straight from the project-open payload.

This kills the old bug where `/api/scenario` served the global golden/bench
presets, so a reopened **Blank** ran Golden.

## Verification — `binding_run41.py` PC25–PC30 · PASS_REF_AND_NATIVE (smoke 30s + native 75s)

| # | Check |
|---|-------|
| PC25 | Explore (preview) applies the manifest `canvas_layout` exactly (presentation matches for every node + edge, order-independent) |
| PC26 | Use applies the **same** manifest layout to the new project; Explore + Use begin with a **presentation-equivalent** layout **by object ID + edge key** (outside semantic identity) |
| PC27 | reopening the Acceptance Bench restores its bound default (`bench`) and folds the full 9-epoch run from the **project's own** scenario docs (both `golden`+`bench` docs restored) |
| PC28 | **REAL RESTART**: create-from-Blank → persist → **drop the in-memory cache** (fresh `ProjectSessionCache` over the same on-disk root) → reopen → open payload selects `idle` → run → **exactly one epoch** over the Blank's own world (never Golden/Bench) |
| PC29 | reopen restores the project's own scenarios with **no template/provenance lookup** — passes with the catalog set to `None` **and** the provenance sidecar removed |
| PC30 | a presentation-only layout edit moves **no** semantic identity and **no** template bytes (persists across a fresh-cache reopen); native (tightened per Patch 3): the gate itself creates the Golden-derived project → changes layout → persists → reopens from a **fresh cache** → verifies the **reopened project source** (`ov30n["view"]["text"]`, never the template source) still folds `ic_ref == ic32 == Fixture` |

**Gate split:** `--gate smoke` (PC25–PC29 + PC30 smoke half, no compiler) ·
`--gate native` (PC30 native half) · default runs both. `TRVM_SKIP_NATIVE=1` →
ref-only.

**Regressions green:** binding_run40 PC1–PC24 (98s, template catalog),
binding_run37 PA1–PA20 (55s, rolling version).

## Smaller corrections — status (all already reflected in code)

1. **PC10 wording.** binding_run40 PC10 reads *"the Blank Spinner World is exactly
   one Spinner + one Orb + one SocketControl connection … one idle epoch, and
   folds cleanly (**minimal scaffold**)."* We describe it as a **minimal Spinner
   authoring scaffold**, not a "provably minimal valid WRL world" — matching your
   ruling that the honest theorem is shape-based, not "smaller worlds are rejected."
2. **"Immutable" clarified.** `wrl_templates.py` docstring (the `template_id`
   bullet): *the sealed content (world source + scenario content) may never
   silently change meaning — changing it requires a **new version** (`.v2`), never
   overwriting `.v1`; **layout/wording/guide copy MAY change** between app releases
   without a new template version.* Per your ruling `presentation_revision` is
   **deferred to v0.7-5** (when the initial public presentation freezes). Contract
   on arrival: integer beginning at **1**; **not** in world/scenario/replay identity;
   **not** consulted on reopen; layout/wording/guide changes increment it;
   world/scenario-content changes require a new template ID (`.v2`, resets to 1);
   best-effort provenance may record it.
3. **Fail-closed is subsystem-scoped, not an app-startup abort.** The catalog load
   is wrapped `try/except` at import: on failure `_TEMPLATE_CATALOG = None`,
   `_TEMPLATE_ERROR = ex`, and **the app keeps running** — demo, projects,
   run/verify all work; only the four template endpoints return `_err`, and
   shallow `GET /api/health` reports `templates_ok: false`. Fail-closed governs the
   template subsystem, never process startup.
4. **Provenance is best-effort.** `_write_provenance` docstring: *"Best-effort: a
   provenance write never blocks project creation."* And reopen never consults it
   (PC29).

## Two prior flagged decisions — you upheld both

- **PC10 shape-based minimality** (kept; you called it "honest and better than
  forcing a false theorem").
- **Blank ships un-driven** (kept). Golden verifies `ic_ref==ic32==Fixture`; the
  un-driven Blank is outside the Fixture oracle's constructible domain (its spinner
  has zero sig-in), so it verifies `ic_ref==ic32` only — a strength, not a gap.

## Next (your ruled sequence)

With the reopen closure + the three tightening patches landed, we **proceed to
v0.7-4 Visual/Responsive Closure** (presentation only — no semantic/identity/
schema/template-content/runtime/authoring-op/server-capability change): first-run
chooser hierarchy, workspace responsiveness across the 320×700 … 1440×900 matrix,
a visually-obvious read-only Explore, and accessibility (keyboard, focus, ARIA,
reduced-motion, no color-only info, contrast). Battery **PC31–PC38**, one
screenshot per target width in the packet. `presentation_revision` stays deferred
to **v0.7-5**, which freezes the initial public presentation.
