# Forge Spinner Bench v0.7.0-alpha.5 — v0.7-4 Visual / Responsive Closure (memo for GPT-5.6)

**Date:** 2026-07-23 · Implements your **v0.7-4** ruling in full: make the first-run
chooser a clear hierarchy, make the six-panel workspace responsive across the whole
device matrix, make read-only **Explore** obvious at every breakpoint, and close the
accessibility basics — **presentation only**. **No new semantic profile, IR version,
artifact identity, actor role, edge type, graph transaction, authoring op, or server
capability.** The Golden/Bench demo world still seals to the frozen
`DEMO_WORLD_SEMANTIC_ID = sem-8ae91fe9…fe4a`; the Blank keeps its own
`sem-0a8dab60…4c9f`; every fold is byte-identical to v0.6-4.

**Version cut:** this slice changes shipped CSS/JS/HTML, so it is a new deterministic
alpha — **v0.7.0-alpha.5** (alpha.4 = Template Catalog + v0.7-3.1 reopen closure).
The rolling version battery `binding_run37` (PA17 version-consistency across
server / header / docs / archive) re-verified green at alpha.5.

**Base commit:** `f30e88a6e7b5d9c8fc72e2638d24626e7eee7f70`. The packet ships the full
modified `spinner_bench.css`, `spinner_bench.js`, `spinner_bench.html`,
`spinner_bench.py`, the version-bumped launcher/builder/docs, plus the new
`binding_run42.py` — every touched file as complete source, and **one screenshot per
target width** (plus first-run + Explore evidence shots).

## The three tightening patches (from your v0.7-3.1 close) — already landed

Carried in the **same alpha.4** cut before this slice, re-stated for the record:

1. **`CanvasSession` owns + validates the layout seed centrally** — deep-copy +
   `validate_layout_v1` at the API boundary; callers pass raw manifest layout.
2. **"presentation-equivalent by object ID + edge key"** replaces "byte-equivalent"
   in PC25/PC26, `binding_run41` docstring, and the v0.7-3.1 memo.
3. **PC30 native independently verifies the reopened project source** (create →
   layout edit → persist → fresh-cache reopen → `_verify_payload(view.text, oracle)`).

`presentation_revision` stays **deferred to v0.7-5** per your ruling — not added here.

## What changed (all presentation)

**`spinner_bench.css` — one appended "v0.7-4 Visual / Responsive Closure" block:**

- **No horizontal overflow.** Grid children default to `min-width:auto`, which lets a
  wide panel push the row past the viewport. Pinned `.panel { min-width: 0 }` and
  `.grid { max-width: 100% }` (plus `.library select { min-width: 0 }`) so panels
  shrink instead of overflowing.
- **Responsive collapse 3 → 2 → 1 column.** `@media (max-width: 1024px)` collapses the
  six-panel grid to two columns (`grid-auto-rows: minmax(260px,1fr)`, diff/scenario
  span both); `@media (max-width: 760px)` collapses to a single column and turns the
  guided-demo rail into a **bottom sheet** (`.guide-rail` docks to the bottom, ≤46vh);
  the header + toolbar `flex-wrap: wrap`; `@media (max-width: 420px)` tightens
  padding/type for narrow phones.
- **Read-only Explore is obvious.** `.explore-banner` is `position: sticky; top: 0`
  with a lock glyph (`.eb-tag::before { content: "\1F512" }`) and `body.explore main`
  gets a **dashed warn-colored frame** (`outline: 2px dashed var(--warn)`) — shape +
  text + a persistent banner, **never color alone**.
- **Accessibility.** A global `:focus-visible` ring on every interactive element
  (`outline: 2px solid var(--accent)`), non-color status glyphs
  (`.status.ok::before "✓"`, `.status.err::before "✗"`), and a
  `@media (prefers-reduced-motion: reduce)` block that kills transitions, animations,
  and smooth scroll.

**`spinner_bench.js` — accessibility wiring on the chooser (no behavior change):**

- `renderTemplateCards()` marks the card list `role="list"` and each card
  `role="listitem"`; each button gets an accessible name
  (`aria-label "Explore <name> (read-only preview)"` /
  `"Use <name> (create an editable project)"`).
- The catalog-failure message is user-actionable:
  *"Templates are unavailable right now — you can still open an existing project below."*
- **No** `resize`/`onresize` handler and **no** `location.reload` anywhere —
  responsiveness is purely media-query driven (PC34).

**Version:** `BENCH_VERSION = "v0.7.0-alpha.5"` (server), `spinner_bench.html`
title + header, `forge-bench`, `tools/build_forge_release.py`, `README.md`,
`FORGE_QUICKSTART.md`, and a new `RELEASE_NOTES.md` section.

## Verification — `binding_run42.py` PC31–PC38 · PASS_REF_AND_NATIVE (smoke 19s + native 44s)

| # | Check |
|---|-------|
| PC31 | **No horizontal overflow** — grid pins `min-width:0`, caps at `100%`, and collapses 3→2→1 column with a wrapping header |
| PC32 | The template chooser is **keyboard-operable** — real `<button>`s + a visible `:focus-visible` ring + accessible names (`aria-label`, `role=list`) |
| PC33 | Read-only **Explore is visually obvious at every breakpoint** (sticky banner + lock glyph + dashed frame) **and creates no project** (listdir unchanged across a preview) |
| PC34 | Resizing **only re-flows CSS** — no `resize`/`reload` handler mutates state; responsiveness is media-query driven |
| PC35 | A **catalog failure disables only template ops** (list/preview/use fail closed) while `run` / `health` / pipeline keep working; `health.templates_ok=false`, the demo still folds to `DEMO_SEM` |
| PC36 | `prefers-reduced-motion` is honored (the reduce block zeroes transitions + animations + smooth scroll) |
| PC37 | **No server errors** (health/templates/preview/use/open/run all structured) + a11y wiring references only **real ids** present in the HTML |
| PC38 | **Native — the visual slice moves NO identity**: preview + template-use reproduce the frozen ids and the demo still folds `ic_ref == ic32 == Fixture` to `DEMO_SEM` |

**Gate split:** `--gate smoke` (PC31–PC37, no compiler) · `--gate native` (PC35/PC37/PC38
plus the smoke half) · default runs both. `TRVM_SKIP_NATIVE=1` → ref-only. The
`[forge-error …]` dev-log lines during PC35 are the **intended** output of the
simulated catalog failure, not real errors.

**Regressions green:** binding_run41 PC25–PC30 (reopen closure), binding_run40 PC1–PC24
(template catalog), binding_run37 PA1–PA20 (rolling version, now certifying alpha.5).

## Screenshots — one per target width, captured live at alpha.5

`screenshots_v0_7_4/` (all captured against a live server booting into the restored
Golden-derived `Shots` project so the panels hold a real world + its 7-epoch run):

| File | What it shows |
|------|----------------|
| `workspace_320x700.png` | single-column stack; header + toolbar wrap; RUN 7/7; **no horizontal overflow** |
| `workspace_375x812.png` | narrow-phone single column |
| `workspace_768x1024.png` | tablet two-column collapse |
| `workspace_1024x768.png` | two-column landscape |
| `workspace_1280x800.png` | full six-panel grid |
| `workspace_1440x900.png` | full grid — Canvas + WRL editor, World disc dial (epoch 1/7), Scenario author golden table, ScenarioDigest / world id / ReplayBundle strip |
| `first-run-chooser_1280x800.png` · `first-run-chooser_375x812.png` | the chooser hierarchy (Golden RECOMMENDED / Bench CORE / Blank INTRO, Explore + Use per card, Open Existing) at desktop + mobile |
| `explore-readonly_1280x800.png` · `explore-readonly_375x812.png` | Explore mode: **🔒 READ-ONLY** sticky banner, dashed warn frame around `main`, "Make an editable copy" as the only creation path, Save/Commit/Import disabled |

Each of the six workspace widths is a distinct capture (54 KB → 119 KB, scaling with
width) — genuine reflow, not the same frame.

## Prior flagged decisions — still upheld

- **PC10 shape-based minimality** (Blank = minimal Spinner authoring scaffold).
- **Blank ships un-driven** — Golden verifies `ic_ref==ic32==Fixture`; the un-driven
  Blank is outside the Fixture oracle's constructible domain, so it verifies
  `ic_ref==ic32` only.

## Next (your ruled sequence)

v0.7-4 closes the visual/responsive/accessibility surface with **no identity
movement**. Ready for **v0.7-5 Public Alpha closure** — freeze the initial public
presentation (this is where `presentation_revision:1` is introduced per its deferred
contract), final copy/layouts, clean-install docs, browser/native requirements, a
full source packet with manifest hashes, and fresh-machine acceptance.
