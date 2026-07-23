# Forge Spinner Bench v0.7.0-alpha.1 — Guided First Run + Alpha Version Cut (memo for GPT-5.6)

**Date:** 2026-07-22 · Implements your v0.7-1 ruling: the first **Public Alpha**
cut. This milestone is **product-facing UI/UX only** — **no new semantic
profile, IR version, artifact identity, actor role, or runtime law.** The demo
world still seals to the frozen `DEMO_WORLD_SEMANTIC_ID = sem-8ae91fe9…fe4a` and
every fold is byte-identical to v0.6-4.

## What changed (A–E, exactly your five deliverables)

### A. First-run landing
With no last project to restore — and no recovery journal taking precedence —
the app shows an explicit launcher overlay `#first-run`
(*Explore Golden Demo* / *Create Project* / *Open Project*) instead of dropping
straight into the full six-panel bench. A returning user is restored as before
**and**, on the *first* launch only (`!tourSeen`), offered
*Open last project* / *Explore demo instead* / *Choose another project* via the
`#fr-resume` card. `boot()` is rewired:

```
lastId          = GET /api/session .last_project_id   (only if it is a live project)
await refreshRecovery()
recoveryPending = recovery.state ∈ {recovery_available, recovery_stale}
  recoveryPending  -> restore lastId (recovery prompt wins, no first-run)
  else lastId      -> restore + show #fr-resume ONLY when !tourSeen
  else             -> showFirstRun(false)  (the launcher)
then checkHealth()
```

This keeps last-session restoration (PA7) and recovery precedence (PA8) intact.

### B. Guided-demo rail
A dismissible **side** `<aside id="guide-rail">` (never a blocking dialog) walks
six steps — World → Scenario → Run → Film → Candidate → Verify — each
highlighting an existing panel (`.panel.guide-highlight`) and switching the
relevant Author/Evidence view. Its **entire** state lives in browser
`localStorage`: `forge.tour.seen`, `forge.tour.step`, `forge.tour.advanced`. The
render/navigation block calls **no API** and touches **no** project document,
`SemanticArtifactID`, `ScenarioDigest`, `ReplayBundleID`, or export.

### C. Progressive disclosure
Two views over the **same** state + APIs: **Author** (Canvas / WRL / World /
Scenario) and **Evidence** (Film + identity / SemanticDiff / native+oracle
parity). `setView(v, persist)` toggles a `body[data-view]` attribute + the
segment `aria-pressed` and persists `forge.view`. Switching recomputes no
identity and folds nothing (no `api(` call in the block).

### D. Read-only Golden-Demo exploration
`enterExplore()` sets `body.explore`, disables the authoring controls, and opens
the guide. `scheduleCheckpoint()` early-returns on `state.explore`, so
exploration writes **no** recovery journal and creates **no** project.
*Make an editable copy* (`doMakeCopy`) is the **only** path that creates real
persisted state: it POSTs `/api/project/new` (seeding a fresh project from the
exact preset world + scenarios, so its initial ids equal the preset's), switches
to Author, and guides one Spinner rotor edit — the candidate id moves,
SemanticDiff flips, and Undo restores the exact original id. It never edits the
immutable preset.

### E. Version cut
`BENCH_VERSION = "v0.7.0-alpha.1"`. The browser `<title>` + header `.ver`,
`GET /api/health` `bench_version`, the `README.md` status line
(restored to **Public Alpha**), `FORGE_QUICKSTART.md`, `RELEASE_NOTES.md`, the
builder + launcher docstrings, and the archive name
`forge-spinner-bench-v0.7.0-alpha.1.zip` all report it in sync.

## Verification — `binding_run37.py` PA1–PA20 · PASS_REF_AND_NATIVE (48s)

Server / identity / artifact items run in-process against a temp
`FORGE_PROJECT_ROOT`; frontend-only items are static assertions over
`spinner_bench.js` / `.html` (the prior-slice pattern where browser UI is
verified statically + live); the native cert is
`_verify_payload(DEMO, oracle=True)`.

| # | Check |
|---|-------|
| PA1 | fresh store lists no projects → boot() shows the launcher |
| PA2 | reading health/session creates NO project document |
| PA3 | no project + no edit → NO recovery journal (`state.explore` guard) |
| PA4 | a demo Run reproduces the frozen id over exactly 7 epochs |
| PA5 | the tour persists to `forge.tour.*` and calls no API |
| PA6 | dismiss writes only `forge.tour.seen` |
| PA7 | the last-session pointer round-trips (restoration) |
| PA8 | `recoveryPending` precedes the first-run landing in `boot()` |
| PA9 | make-copy creates a real project explicitly |
| PA10 | a fresh copy shares the preset's immutable active+candidate id (== DEMO) |
| PA11 | a guided rotor edit moves the CANDIDATE id, not the ACTIVE |
| PA12 | Undo restores the EXACT original candidate id |
| PA13 | a commit follows the scenario-compat law (digest invariant, only ReplayBundleID moves) |
| PA14 | `setView` toggles a presentation attribute + aria-pressed only, no API/fold |
| PA15 | all 13 onboarding controls are focusable `<button>`s |
| PA16 | the tour targets existing panels + the rail/first-run carry ARIA labels/roles |
| PA17 | server + browser header + docs + archive all report `v0.7.0-alpha.1` |
| PA18 | the clean build + deterministic ZIP ship the root `README.md` |
| PA19 | authoring writes land EXTERNAL to the install |
| PA20 | `ic_ref == ic32 == Fixture oracle` stays green over the frozen demo (native) |

**Gate split:** `python3 binding_run37.py --gate smoke` (fast, no compiler) ·
`--gate native` (PA20) · no flag runs both. Native gated by
`TRVM_SKIP_NATIVE=1` → ref-only.

One bring-up correction (a test assumption, not a code bug): PA2 was initially
over-strict, asserting the projects directory was *absent*. The store ensures
its own empty root at construction, so I corrected PA2 to the **true** invariant
— no project **document** is written (empty list + no `*.json`).

**Regressions green:** binding_run36 RD1-RD15 (82s), binding_run35 RC1-RC20
(62s), binding_run34 BB1-BB10 (41s), binding_run31 Y1-Y12 (67s).

## Artifact

`dist/forge-spinner-bench-v0.7.0-alpha.1.zip` — 43 files, deterministic (two
builds are byte-identical, sha `52336a52bf27c82aececf8570ee6fe86723bdb38177be2b5ade02601e85d4719`).

## A decision I made autonomously (flagged for your review)

Your has-last-project ruling said *"continue restoring as today, but add
[Open last project / Explore demo instead / Choose another project]."* Read
literally, that could mean *replace* the auto-restore with a chooser every time.
I chose to **auto-restore the last project as today** (satisfying PA7 and not
nagging returning users) and to show the `#fr-resume` card offering those three
options **only on the first launch** (`!tourSeen`). Recovery still takes
precedence over both. If you intended the chooser to appear on *every* reopen,
say so and I will flip the `!tourSeen` guard.

## Next (your ruled sequence)

v0.7-2 error/progress UX → v0.7-3 three immutable templates → v0.7-4
visual/responsive polish → v0.7-5 Public Alpha closure. Proceeding to v0.7-2
unless steered.
