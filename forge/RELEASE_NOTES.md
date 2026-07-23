# Forge Spinner Bench -- Release Notes

## v0.7.0-alpha.4 -- Immutable Template Catalog

A closure on top of `v0.7.0-alpha.3` (which is **not** replaced -- its release
archive remains). This slice adds a curated, read-only starting catalog: **no new
semantic profile, IR version, artifact identity, actor role, edge type, graph
transaction, or runtime law.** The demo world still seals to the frozen
`DEMO_WORLD_SEMANTIC_ID` and every fold is byte-identical to v0.6-4.

### What is new

- **Three release-owned templates.** A `templates/` directory ships a
  `catalog.json` index plus one `TemplateManifestV1` (`forge.template.v1`) JSON
  per template: **Golden ADMIT Demo** (the frozen 6-node world + 7-epoch golden
  run), **ADMIT Acceptance Bench** (the *same* semantic world, defaulting to the
  9-epoch acceptance scenario), and **Blank Spinner World** (the empirically
  smallest valid Spinner->Orb scaffold, with its own genuine semantic identity).
  Each manifest carries its `world_semantic_id`, per-scenario `ScenarioDigest`,
  and `ReplayBundleID`.
- **Fail-closed identity verification.** At startup the catalog is loaded,
  schema-validated, and every identity is **recomputed from the sealed world
  source + scenario documents**. Any drift fails closed with
  `FORGE_TEMPLATE_IDENTITY`; shallow `GET /api/health` reports `templates_ok` and
  `template_count`. The catalog + files are covered by the release
  `MANIFEST.sha256`.
- **Template chooser.** The first-run launcher is now a 3-card chooser (Golden
  Demo recommended). Each card offers **Explore** -- a project-free, read-only
  preview that creates no project, recovery journal, or last-session pointer and
  locks every authoring surface while still allowing Run / Verify / Film / guide
  -- or **Use**, which explicitly asks for a project id and instantiates an
  **independent** `ForgeProjectV2` preserving the template's initial identities.
  "Open Existing Project" stays separately visible.
- **Non-authoritative provenance.** A `created_from_template` sidecar records the
  originating template id + release version. It lives outside every Forge
  identity (a `.provenance/` sidecar, never the project document).

### Version

`BENCH_VERSION`, the browser header, `GET /api/health`, this file, the
Quickstart, the landing `README.md`, and the release archive name all report
**v0.7.0-alpha.4**.

## v0.7.0-alpha.3 -- Error and Progress UX Closure

A closure on top of `v0.7.0-alpha.2` (which is **not** replaced -- its release
archive remains). This slice is presentation only: **no new semantic profile, IR
version, artifact identity, actor role, or runtime law.** The demo world still
seals to the frozen `DEMO_WORLD_SEMANTIC_ID` and every fold is byte-identical to
v0.6-4.

### What is new

- **Typed, browser-safe errors.** Every API failure now carries a stable
  `ErrorPresentationV1` sidecar (`forge.error.v1`) -- a machine `code`, a human
  title + message, a severity, a retryable flag, a suggested action, and a
  category (source / project-recovery / runtime-native / bundle / request). A raw
  Python exception **never** crosses to the browser: an unknown error is
  sanitized to a generic internal presentation with a correlation `error_id`,
  and the full traceback stays in the developer log. A malformed request body
  becomes a structured **400**.
- **Located errors.** A source error carries a `source_span` the WRL editor
  highlights; an object/edge error carries an `object_id` the canvas highlights.
  An invalid world stays a typed, editable draft while the active world keeps
  running; a stale revision offers **Reload** (never a silent overwrite); a
  project-id collision **re-prompts** with the entered form preserved.
- **Runtime clarity.** Native failures distinguish *unavailable* (offers
  reference-only) from *build failure* (retryable, with cache/compiler guidance)
  from *parity mismatch*.
- **Persistent job progress.** A non-modal progress component shows the
  monotonic `queued -> running -> completed | failed | cancelled` state, phase,
  and epoch count; it stays visible after a job settles so the result is
  inspectable, survives view switches, and styles **cancelled** distinctly from
  **failed**. A browser disconnect mid-response never tracebacks.
- **Accessible in-app dialogs.** Create / Make-editable-copy / Fork / Rename /
  Trash / Restore / Import / Recovery all use an in-app `role="dialog"`
  (aria-modal, Escape to cancel, Enter to confirm, a Tab focus-trap) -- no
  browser `prompt()` / `alert()` / `confirm()` remain.

### Version

`BENCH_VERSION`, the browser header, `GET /api/health`, this file, the
Quickstart, the landing `README.md`, and the release archive name all report
**v0.7.0-alpha.3**.

## v0.7.0-alpha.2 -- First-Run State Closure

A correction on top of `v0.7.0-alpha.1` (which is **not** replaced -- its release
archive remains). This slice is product-facing UI/UX only: **no new semantic
profile, IR version, artifact identity, actor role, or runtime law.** The demo
world still seals to the frozen `DEMO_WORLD_SEMANTIC_ID` and every fold is
byte-identical to v0.6-4.

### What is fixed

- **Shell-first startup.** `boot()` no longer lowers or runs any world before you
  choose. It resolves the startup *path* from cheap metadata only -- project list,
  last-session pointer, recovery status, onboarding preference -- then hands off to
  exactly one path: **Explore / Open / Create / Recover**. A fresh user sees the
  launcher *before* any fold runs under it.
- **Explicit Golden Demo loading.** *Explore* now loads `DEMO_WORLD_SOURCE` and the
  golden scenario explicitly and resets the displayed identity to the demo. It
  never reuses whatever project happened to be open, so the banner and the canvas
  can no longer disagree.
- **Genuinely read-only exploration.** Explore now locks every authoritative
  surface -- the WRL editor, the SemanticDiff variant editor, the Scenario Author
  toggle, the preset selector, every scenario mutation, Apply / Save / Commit /
  Undo / Format, and all Library mutations. Run, Verify, Cancel, the epoch
  scrubber, Author/Evidence view, and the Guide stay usable. *Make an editable
  copy* remains the only persistence transition.
- **Recovery before run.** A last project's crash-recovery journal is surfaced
  *before* that project is ever folded.
- **Home control.** A persistent, non-modal **Home** button reopens the
  Explore / Open / Create chooser at any time. Normal reopen still auto-restores
  the last project without a modal.

## v0.7.0-alpha.1 -- Guided First Run + Alpha Version Cut

The first **Public Alpha** cut. This milestone is product-facing UI/UX only:
there is **no new semantic profile, IR version, artifact identity, actor role, or
runtime law**. The demo world still seals to the frozen `DEMO_WORLD_SEMANTIC_ID`
and every fold is byte-identical to v0.6-4.

### What is new

- **First-run landing.** With no last project to restore (and no recovery journal
  taking precedence), the app shows an explicit landing surface --
  *Explore Golden Demo* / *Create Project* / *Open Project* -- instead of dropping
  you straight into the full six-panel bench. A returning user is restored as
  before and, on first launch, offered *Open last project* / *Explore demo
  instead* / *Choose another project*.
- **Guided-demo rail.** A dismissible **side** rail (never a blocking dialog) walks
  six steps -- World, Scenario, Run, Film, Candidate, Verify -- highlighting the
  existing panels. Its entire state (seen / current step / advanced expanded) lives
  in browser `localStorage`; it never touches a project document or any sealed id.
- **Progressive disclosure.** Two workspace views over the *same* state and APIs:
  **Author** (Canvas / WRL / World / Scenario) and **Evidence** (Film + identity /
  SemanticDiff / native+oracle parity / provenance). Switching views recomputes no
  identity and folds nothing.
- **Read-only Golden Demo exploration.** *Explore Golden Demo* creates no project
  and writes no recovery journal -- there is no surprise persistence, commit,
  native compile, or world mutation. *Make an editable copy* is the only path that
  creates real, persisted state: it seeds a fresh project from the exact preset
  world + scenarios (so its initial ids equal the preset's), switches to Author,
  and guides one Spinner rotor edit -- the candidate id moves, SemanticDiff flips
  to MOVED, and Undo restores the exact original id.

### Version

`BENCH_VERSION`, the browser header, `GET /api/health`, this file, the Quickstart,
the landing `README.md`, and the release archive name all report
**v0.7.0-alpha.1**.

## v0.6.5.1 -- Read-Only Installation Closure

v0.6.5.1 makes the extracted release a genuinely **read-only installation**:
launching it -- reference *or* native -- leaves the extracted tree byte-identical.
There is **no new semantic identity and no new runtime construct**; the demo
world still seals to the frozen `DEMO_WORLD_SEMANTIC_ID` and every fold is
byte-identical to v0.6-4.

### Everything writable moved outside the install tree

- New **`forge_paths.py`** owns the external cache locations and a
  **transactional** native build. The native `ic32` is compiled into an external
  runtime cache (`~/.cache/trvm-forge/runtime/` on Linux; `FORGE_RUNTIME_CACHE`
  overrides), **keyed by source-sha256 + OS + arch**, built temp -> verify ->
  atomic rename. The path is passed to the server via `TRVM_IC32_PATH`, which
  `forge_runtime.py` now prefers. **`ic32` is no longer written into
  `<install>/runtime/c/`.**
- The launcher redirects Python bytecode to an external `PYTHONPYCACHEPREFIX`
  (and sets `sys.dont_write_bytecode` in its own process), so **no `__pycache__`
  appears in the installation**.

### Other release corrections

- The repository **`LICENSE`** now ships at the release root (referenced here and
  in the Quickstart).
- Docs and the launcher now consistently describe **six** principal panels (the
  sixth is **Scenario author**).
- `--zip` now produces a **deterministic** archive (fixed 1980 timestamps, fixed
  0644/0755 permissions, sorted entry order, DEFLATE) -- two builds of the same
  content are byte-identical, not merely the same `MANIFEST.sha256`. (v0.6.5's
  reproducibility was **content**-reproducibility: identical manifests.)
- The `spinner_bench.py` direct-run line is now documented as a developer path;
  the public launch command is `./forge-bench`.

### Verification

- `binding_run36.py` -- the RD1-RD15 read-only-install battery: launches from a
  genuinely read-only extraction (ref + native), proves no bytecode / no native
  binary lands in the installation, the native binary is built in the external
  cache and passed via `TRVM_IC32_PATH`, a changed `ic32.c` changes the cache
  key, the installation hash is identical **before and after** launch/use (the
  pre-launch hash is the baseline), all caches are external, ref-only needs no
  compiler, the `LICENSE` ships, docs describe six panels, the manifest and a
  deterministic ZIP verify, and the full `ic_ref == ic32 == Fixture oracle` cert
  stays green.
- `binding_run35.py` (RC1-RC20) and all prior regressions stay green.

## v0.6.5 -- Release Artifact Closure

v0.6.5 closes the **distributable** boundary. There is **no new semantic
identity and no new runtime construct**; the demo world still seals to the frozen
`DEMO_WORLD_SEMANTIC_ID` and every fold is byte-identical to v0.6-4. This release
is a packaging + dependency-boundary correction.

### Production/test separation

- New **`forge_runtime.py`** -- the production reducer adapter (`ref_reduce`,
  `native_reduce`, `native_available`), importing `ic_ref` / `subprocess`
  directly. The normal Run path imports **no** `binding_run*` module.
- New **`forge_state.py`** -- the production state adapter (`init_state_v6`,
  `state_to_film_args_v6` + their bases), pure functions of a duck-typed view.
  The normal Run path imports **no** Fixture; `fixture.py` is now an independent
  oracle, loaded lazily only for the optional Verify-Oracle mode, and it
  re-imports these functions so every battery keeps working.

### User data outside the install tree

- Projects now default to the per-OS user data dir
  (`~/.local/share/trvm-forge`, `~/Library/Application Support/TRVM Forge`,
  `%LOCALAPPDATA%\TRVM Forge`); `FORGE_PROJECT_ROOT` still overrides. A clean
  release contains **no** mutable project dir; first run creates it externally.
  The install directory is never written to.

### Two-mode health

- `GET /api/health` is now an explicit **shallow** check (fast, boot-safe): demo
  identity, project + recovery dir writability, project schema, native
  availability, cache occupancy -- **no fold**.
- The **deep** verification (small ref + native fold + film parity +
  object-store round-trip) is a separate cancellable job (`kind: deep_health`),
  never on boot.

### Distribution tooling

- New **`forge-bench`** launcher: locate Python, locate/build `ic32`, choose a
  free port, display the project dir, optionally open a browser, and print a
  recovery command on failure. `--ref-only` supported.
- New **`tools/build_forge_release.py`**: an allowlisted builder that copies only
  approved files, **fails** if any forbidden path (authoring state, bytecode,
  logs, historical packet ZIPs, screenshots, temp launch configs, batteries)
  would ship, and emits a `MANIFEST.sha256` hashing every shipped file.
- New docs: `FORGE_QUICKSTART.md`, `FORGE_ARCHITECTURE.md`, these notes.
- Fixed the stale `spinner_bench.py` docstring version (was "v0.2").

### Verification

- `binding_run35.py` -- the RC1-RC20 release-closure battery (allowlist purity,
  dependency direction, external data dir, ref-only + native modes, two-mode
  health, project/recovery/bundle round-trips, reproducible manifest) plus a
  clean extracted-artifact end-to-end test.
- `binding_run34.py` (v0.6-4 BB1-BB10) and all prior regressions stay green.

## v0.6-4 -- Perf/Release closure (prior)

Bounded, thread-safe LRU memos for sealed programs + reference trajectories; a
runtime `/api/health` self-check that re-lowers the demo fresh and proves the
identity spine. BB1-BB10.
