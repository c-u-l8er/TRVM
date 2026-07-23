# Forge Binding Results v0.66 — Spinner Bench v0.7.0-alpha.1 (Guided First Run + Alpha Version Cut — GPT-5.6 ruled the first PUBLIC ALPHA cut: a PRODUCT-FACING UI/UX milestone ONLY, with **NO new semantic profile, IR version, artifact identity, actor role, or runtime law** — the demo world still seals to the frozen `DEMO_WORLD_SEMANTIC_ID = sem-8ae91fe9…fe4a` and every fold is byte-identical to v0.6-4. Five deliverables. (A) FIRST-RUN LANDING — with no last project to restore (and no recovery journal taking precedence) the app shows an explicit launcher overlay `#first-run` — *Explore Golden Demo* / *Create Project* / *Open Project* — instead of dropping straight into the full six-panel bench; a returning user is restored as before AND, on FIRST launch only (`!tourSeen`), offered *Open last project* / *Explore demo instead* / *Choose another project* via the `#fr-resume` card. `boot()` is rewired: `GET /api/session` → `lastId`, `await refreshRecovery()`, `recoveryPending = recovery.state ∈ {recovery_available, recovery_stale}` takes PRECEDENCE (skips first-run), else `lastId` auto-restores + shows the resume card only when unseen, else `showFirstRun(false)`. (B) GUIDED-DEMO RAIL — a dismissible SIDE `<aside id=\"guide-rail\">` (never a blocking dialog) walks six steps World→Scenario→Run→Film→Candidate→Verify, each highlighting an existing panel via `.panel.guide-highlight` and switching the relevant Author/Evidence view; its ENTIRE state (tour seen / current step / advanced expanded) lives in browser `localStorage` (`forge.tour.seen|step|advanced`) — the render/nav block calls NO API and touches NO project doc, `SemanticArtifactID`, `ScenarioDigest`, `ReplayBundleID`, or export. (C) PROGRESSIVE DISCLOSURE — two views over the SAME state + APIs: **Author** (Canvas/WRL/World/Scenario) and **Evidence** (Film + identity / SemanticDiff / native+oracle). `setView(v, persist)` toggles a `body[data-view]` attribute + `.seg` `aria-pressed` and persists `forge.view`; switching recomputes NO identity and folds nothing (no `api(` call in the block). (D) READ-ONLY GOLDEN-DEMO EXPLORE — `enterExplore()` sets `body.explore`, disables the authoring buttons, and opens the guide; `scheduleCheckpoint()` early-returns on `state.explore` so exploration writes NO recovery journal and creates NO project. *Make an editable copy* (`doMakeCopy`) is the ONLY path that creates real persisted state: it POSTs `/api/project/new` (seeds a fresh project from the exact preset world + scenarios so its initial ids equal the preset's), switches to Author, and guides one Spinner rotor edit — the candidate id moves, SemanticDiff flips, and Undo restores the exact original id; it never edits the immutable preset. (E) VERSION CUT — `BENCH_VERSION=\"v0.7.0-alpha.1\"`, the `<title>` + header `.ver`, `GET /api/health` `bench_version`, `README.md` status line (`Public Alpha`), `FORGE_QUICKSTART.md`, `RELEASE_NOTES.md`, the builder + launcher docstrings, and the archive name `forge-spinner-bench-v0.7.0-alpha.1.zip` all report it in sync. Battery `binding_run37.py` **PA1-PA20 PASS_REF_AND_NATIVE (48s)** — server/identity/artifact items in-process against a temp `FORGE_PROJECT_ROOT`, frontend-only items via static assertions over `spinner_bench.js`/`.html` (following the prior-slice live-verification pattern), the native cert via `_verify_payload(DEMO, oracle=True)`: PA1 fresh store lists no projects → launcher; PA2 reading health/session creates NO project document; PA3 no project/edit writes NO recovery journal (`state.explore` guard); PA4 a demo Run reproduces the frozen id over exactly 7 epochs; PA5 the tour persists to `forge.tour.*` + calls no API; PA6 dismiss writes only `forge.tour.seen`; PA7 the last-session pointer round-trips; PA8 `recoveryPending` precedes the first-run landing in `boot()`; PA9 make-copy creates a real project explicitly; PA10 a fresh copy shares the preset's immutable active+candidate id (== DEMO); PA11 a guided rotor edit (`rotor=quarter_turn_z`→`rotor=identity`) moves the CANDIDATE id while the ACTIVE stays the preset's; PA12 Undo restores the EXACT original candidate id; PA13 a commit follows the scenario-compat law (world moved, ScenarioDigest INVARIANT, only ReplayBundleID moved); PA14 `setView` toggles a presentation attribute + `aria-pressed` only, no API/fold; PA15 all 13 onboarding controls are focusable `<button>`s; PA16 the tour targets existing panels + the rail/first-run overlay carry ARIA labels/roles; PA17 the server (`/api/health` + `BENCH_VERSION`), browser header, Release Notes, Quickstart, and README all report `v0.7.0-alpha.1`; PA18 the clean build + deterministic ZIP ship the root `README.md` (manifest + archive both list it, 43 files); PA19 authoring writes land EXTERNAL to the install (project + recovery dirs outside the install dir); PA20 `ic_ref == ic32 == Fixture oracle` stays green over the frozen demo. Bring-up: PA2 initially over-strict (asserted the projects dir was absent) — corrected to the TRUE invariant that no project DOCUMENT is written (empty list + no `*.json`), since the store ensures its empty root at construction. Regressions green: binding_run36 RD1-RD15 (82s), binding_run35 RC1-RC20 (62s), binding_run34 BB1-BB10 (41s), binding_run31 Y1-Y12 (67s) — the UI/version edits are behavior-preserving over the frozen spine. Artifact `dist/forge-spinner-bench-v0.7.0-alpha.1.zip` (43 files, deterministic — two builds byte-identical sha `52336a52…`); memo `FORGE_V0_7_1_MEMO.md`. NEXT (ruled): v0.7-2 error/progress UX → v0.7-3 three immutable templates → v0.7-4 visual/responsive polish → v0.7-5 Public Alpha closure.)

---

# Forge Binding Results v0.65 — Spinner Bench v0.6.5.1 (Read-Only Installation Closure — GPT-5.6 ruled v0.6.5 a strong release candidate but the read-only-installation law NOT yet true: first launch wrote 25 `__pycache__/*.pyc` files into the install, and native launch additionally compiled `runtime/c/ic32` into the install; RC7/RC16 missed it because they hashed the app tree AFTER `_launch`/startup. v0.6.5.1 is a packaging correction ONLY — **NO new semantic identity, NO new runtime construct**, every fold byte-identical to v0.6-4, demo still seals to `sem-8ae91fe9…fe4a`. Six changes: (1) NATIVE COMPILATION → EXTERNAL RUNTIME CACHE — NEW `forge_paths.py` owns the per-OS cache (`~/.cache/trvm-forge` / `~/Library/Caches/TRVM Forge` / `%LOCALAPPDATA%\\TRVM Forge\\cache`; `FORGE_RUNTIME_CACHE` overrides), binary keyed `ic32-<source-sha256>-<os>-<arch>`, built TRANSACTIONALLY (mkstemp in cache → `cc -O2` → verify executable → atomic `os.replace`), launcher passes it via `TRVM_IC32_PATH` which `forge_runtime.py` now PREFERS over the dev-tree `runtime/c/ic32` fallback — so a read-only install never needs a writable `runtime/c/`, multiple versions reuse a compatible binary, edited `ic32.c` auto-rebuilds under a fresh key. (2) BYTECODE OUT OF THE INSTALL — `forge-bench` sets `sys.dont_write_bytecode` in its OWN process (so importing `forge_paths` seeds nothing) + exports `PYTHONPYCACHEPREFIX=<cache>/pycache/py<tag>` to the server child (retains bytecode perf; `PYTHONDONTWRITEBYTECODE=1` fallback). (3) LICENSE ships — repo `LICENSE` added to the allowlist at release root, referenced from Quickstart/Architecture/Release Notes. (4) SIX PANELS — docs+launcher+server docstring corrected from five to six (6th = Scenario author), matching the HTML. (5) DETERMINISTIC ZIP — `--zip` writes fixed 1980 timestamps + 0644/0755 perms + sorted order + DEFLATE → two builds BYTE-IDENTICAL (v0.6.5 was only content-reproducible). (6) DIRECT-RUN DOCS — public cmd is `./forge-bench`; `PYTHONPATH=… python3 spinner_bench.py` retained under a developer note only. `binding_run36.py` **RD1-RD15 PASS_REF_AND_NATIVE (94s)** tests from a GENUINELY read-only (chmod a-w) extraction with the PRE-launch hash as baseline: ref (RD1) + native (RD2) launch from read-only tree leaving it byte-identical (RD8); no bytecode (RD3) / no native binary (RD4) in install; binary in external cache (RD5) passed via `TRVM_IC32_PATH` (RD6); changed source re-keys (RD7); all caches external (RD9); ref-only needs no compiler/cache (RD10); LICENSE (RD11); six-panel docs (RD12); manifest verifies (RD13); deterministic zip byte-identical across a 1.1s gap (RD14); `ic_ref==ic32==Fixture oracle` cert green over the cache binary (RD15). Operational gate split: `--gate smoke|native|stress|all`. RD1 harness gotcha: `/api/draft/source` requires a non-empty `replace_id`. Regressions green: binding_run35 RC1-RC20 (80s — proves the forge_runtime/builder edits are behavior-preserving), binding_run34 BB1-BB10 (53s), binding_run31 Y1-Y12 (74s). Artifact `dist/forge-spinner-bench-v0.6.5.1.zip` (42 files, deterministic); packet `WRL_SPINNER_BENCH_V0_6_5_1_PACKET.zip` (11 files); memo `FORGE_V0_6_5_1_MEMO.md`. NEXT (ruled): v0.7 Forge Public Alpha — no new identity, polish/onboarding/docs.)

---

# Forge Binding Results v0.64 — Spinner Bench v0.6.5 (Release Artifact Closure — GPT-5.6 ruled v0.6 engineering ACCEPTED but the PUBLIC-RELEASE BOUNDARY not closed; v0.6.5 is a packaging + dependency-boundary correction with **NO new semantic identity and NO new runtime construct** — every fold stays byte-identical to v0.6-4 and the demo still seals to the frozen `DEMO_WORLD_SEMANTIC_ID = sem-8ae91fe9…fe4a`. Seven closures: (1) PRODUCTION/TEST SEPARATION — NEW `forge_runtime.py` (the reducer adapter `ref_reduce`/`native_reduce`/`native_available`, importing `ic_ref`/`subprocess` directly; carries the `sys.setrecursionlimit(2_000_000)` that used to be a `binding_run3j` import side effect) and NEW `forge_state.py` (the state adapter `init_state_v6`/`state_to_film_args_v6` + bases, PURE functions of a duck-typed lowering view) are extracted so the normal Run path imports **no** `binding_run*` module and **no** Fixture; `spinner_bench.py` now `import forge_runtime as O` (was `binding_run3o`) and `from forge_state import …` (was `from fixture`), all `O.norm`→`O.ref_reduce` / `O.native`→`O.native_reduce`. `fixture.py` becomes an INDEPENDENT test oracle that re-imports the four state functions from `forge_state` so every battery keeps working, loaded LAZILY only for the optional Verify-Oracle cross-check. (2) USER DATA OUTSIDE THE INSTALL TREE — `_default_data_dir()` defaults projects to the per-OS user data dir (`~/.local/share/trvm-forge`, `~/Library/Application Support/TRVM Forge`, `%LOCALAPPDATA%\\TRVM Forge`); `FORGE_PROJECT_ROOT` still overrides; a clean release contains NO mutable project dir, first run creates it externally, the install dir is never written to. (3) TWO-MODE HEALTH — `GET /api/health` is now an explicit SHALLOW check (fast, boot-safe: demo identity, project+recovery writability, schema, native availability, cache occupancy — **folds nothing**, 0.00s); the DEEP verification (small ref + native fold + film parity + object-store round-trip) is a SEPARATE cancellable job `kind: deep_health` (added to `wrl_jobs.JOB_KINDS`), never on boot. (4) STANDALONE LAUNCHER `./forge-bench` — locate Python, locate/BUILD `ic32` from source (`gcc -O2`), choose a free port, display the project dir, `--ref-only`/`--port`/`--project-dir`/`--open`/`--host`, print a recovery command on failure; works from both the dev tree and a built release. (5) DISTRIBUTION TOOLING — NEW `tools/build_forge_release.py`, an ALLOWLISTED builder that copies only approved files (29 modules + 3 frontend + runtime `ic_ref.py`/`ic32.c`/`IC32_RUNTIME.md` + 3 docs + `forge-bench` = 39 shipped), FAILS if any forbidden path (authoring state, bytecode, logs, historical `*_PACKET.zip`, screenshots, temp launch configs, batteries) would ship, and emits a `MANIFEST.sha256` hashing every shipped file; two builds are byte-reproducible. (6) RELEASE DOCS — NEW `FORGE_QUICKSTART.md`, `FORGE_ARCHITECTURE.md`, `RELEASE_NOTES.md`; fixed the stale `spinner_bench.py` docstring version (was \"v0.2\" → \"v0.6.5\", `BENCH_VERSION=\"v0.6.5\"`). (7) EXTRACTED-ARTIFACT E2E — the battery builds a clean release, launches it as a subprocess, and folds the demo end-to-end from an external data dir. Battery `binding_run35.py` RC1-RC20 **PASS_REF_AND_NATIVE (80s)**: RC1-3 allowlist purity (no authoring state / bytecode / packets / last-session pointer ship); RC4 the Run path imports NO `binding_run*`; RC5 imports NO Fixture (lazy oracle only); RC6 a clean extraction LAUNCHES with one command + answers a shallow `/api/health`; RC7/RC16 first run writes OUTSIDE a byte-unchanged install dir; RC8 ref-only run folds the 7-epoch demo to the frozen id; RC9 native mode BUILDS ic32 from source + folds `ic_ref == ic32` with parity; RC10 shallow health is FAST (0.00s, folds nothing) + identity-correct + reports dir writability; RC11 deep verification runs as a cancellable `deep_health` job; RC12/RC13 saved projects + recovery journals survive a restart; RC14 full export/import retains the authoritative SemanticArtifactID; RC15 golden/bench presets immutable + deterministic; RC17 MANIFEST hashes EVERY shipped file (39, recomputed against a PRISTINE build); RC18 two clean builds reproducible; RC19 fast release smoke bounded; RC20 full `ic_ref == ic32 == fixture oracle` certification runnable + separate from the smoke. Regressions green: binding_run34 BB1-BB10 (52s), binding_run31 Y1-Y12 (72s), binding_run7 3d (34s) all PASS_REF_AND_NATIVE — the extraction is behavior-preserving. Three RC test-harness fixes during bring-up (not code bugs): `deep_health` added to `JOB_KINDS`; RC11 job-state names `completed`/`failed`/`cancelled` (were `done`/`error`); RC13 `dirty_reasons=[\"text\"]` (was an invalid reason); RC17 verifies the manifest against a fresh clean build since RC6/RC9 mutate the launched tree in-place. NO new identity, NO new runtime construct — a packaging + dependency-boundary closure over the frozen v0.6 spine. NEXT per the ruling: v0.7 Forge Public Alpha (no new identity — polish/onboarding/docs)) + Spinner Bench v0.6-4 (Forge World Library phase 11 — Perf/release closure, the FINAL v0.6 slice — **v0.6 SERIES COMPLETE**: two load-bearing release gaps close at once. (a) UNBOUNDED MEMORY — the two hot memos `_PROG_CACHE` (sealed program by source) and `_TRAJ_CACHE` (reference trajectory by `(SemanticArtifactID, reducer, ScenarioDigest)`) were plain dicts that only grew, so a long editing/release session lowering thousands of distinct sources grows memory without limit. They become bounded thread-safe `_LruCache(_CACHE_CAP=256)` — a `collections.OrderedDict` + a `threading.Lock`, `get` moves-to-end on hit / returns None on miss, `put` moves-to-end + evicts the least-recently-used over cap. A cache is a PURE memo (an entry is a pure function of its key) so an evicted key RECOMPUTES to byte-identical bytes on the next miss — bounding caps memory WITHOUT moving any identity; the only call-site change is `[k]=v` → `.put(k,v)`. (b) TRUST-ME IDENTITY — the build only asserted `DEMO_WORLD_SEMANTIC_ID` at import time as a constant. NEW `_health_payload()` + `GET /api/health` re-lowers the demo world FRESH via `W.lower_program(SG.desugar_core(DEMO_WORLD_SOURCE), W.parse_wrl_core)` — BYPASSING `_prog`/`_PROG_CACHE` — and confirms it STILL reproduces `DEMO_WORLD_SEMANTIC_ID`, returning `{ok, bench_version, skip_native, demo_semantic_id, identity_ok, caches:{prog:{size,cap}, traj:{size,cap}}}` — a PURE READ that computes+compares ids and reports bounded-cache occupancy, never minting/memoizing/perturbing an id. The frontend `checkHealth()` (awaited last in `boot()`) stamps the header `.ver` with `bench_version` + a self-check tooltip on `identity_ok`, or flags `.ver.bad` red on failure (non-blocking). Battery `binding_run34.py` BB1-BB10 PASS_REF_AND_NATIVE (58s): BB1 `_LruCache` bounds at cap (oldest evicted); BB2 LRU order (a get() moves an old key to the recent end so it survives the next eviction); BB3 PURE MEMO prog — flooding past cap evicts the demo yet it re-lowers to the SAME `SemanticArtifactID`, cache never exceeds cap; BB4 PURE MEMO traj — flooding bounds it + a real demo run still yields the correct 7-epoch films; BB5 `_health_payload` shape/values; BB6 identity_ok True + every cap == `_CACHE_CAP`; BB7 the self-check is a PURE READ — a `_health_payload` call does not mutate `_PROG_CACHE` occupancy and does not move `DEMO_SEM`; BB8 THREAD-SAFE — 6 threads hammering put/get never exceed the cap and never raise; BB9 IDENTITY INVARIANT — bounding/eviction/health churn leaves the demo `SemanticArtifactID` + per-epoch films byte-for-byte equal; BB10 NATIVE — after the cache churn the demo folds `ic_ref == ic32 == the Fixture oracle`. Regressions stay green (binding_run33 AA1-AA10 58s + binding_run30 X1-X18 62s — the `.put()` swap is byte-identical). Verified LIVE (port 8765): `GET /api/health` → `{ok:true, bench_version:"v0.6-4", identity_ok:true, demo_semantic_id: sem-8ae9…fe4a, caches:{prog:{cap:256}, traj:{cap:256}}}`; the header stamps `v0.6-4` + the self-check tooltip. NO new identity, NO new runtime construct — caching + a runtime self-check over the frozen identity spine. The v0.6 series (v0.6-0 recovery journal → v0.6-1 job lifecycle → v0.6-2 startup UX → v0.6-3 migration → v0.6-4 perf/release) is COMPLETE; no ruled slice exists beyond this — HOLDING for GPT-5.6's next-milestone steer) + Spinner Bench v0.6-3 (Forge World Library phase 10 — Migration: the v0.5.1 workspace package writes `forge.project.v2` docs but `ForgeProjectStore.save` deliberately REFUSES to write a V2 doc over an on-disk V1 (`WRL_BAD_PROJECT`, "a project is not silently up/down-graded on save") — so every legacy `forge.project.v1` project was READ-ONLY under the current package. v0.6-3 closes that with one EXPLICIT (never auto-on-open — the v0.6-0 no-silent-mutate principle), FORWARD-ONLY (V1→V2, never reverse), IDENTITY-PRESERVING upgrade. `wrl_project.py` adds the pure `migrate_project_v1_to_v2(doc)` which REUSES the validated reopen seam — it canonicalizes the V1 doc, re-opens through the SAME `open_session_from_project` (which re-lowers `world_source` and ASSERTS it reproduces `active_world_semantic_id`), re-serializes via `session_to_project_v2` at the SAME `revision`, then asserts `v2.active_world.semantic_id == v1.active_world_semantic_id` else `WRL_PROJECT_MIGRATION`; V1 `scenarios → scenario_documents`, `commits → commit_history`. It advances NO revision and moves NO `SemanticArtifactID` (a representation upgrade, not a workspace edit). `ForgeProjectStore.migrate(pid)` refuses a non-V1 (`WRL_PROJECT_MIGRATION`) / missing (`WRL_PROJECT_MISSING`) doc and atomic-writes at the SAME path/revision; `ProjectSessionCache.migrate` delegates then pops + re-opens the session via `open_session_from_project_any`, recovery journal intact; `list_project_infos` now tags each summary with `project_version`. `spinner_bench.py` adds `_project_migrate_payload` + `POST /api/project/migrate`; the frontend `renderLibrary()` tags a `forge.project.v1` option `· v1` and shows `#lib-migrate` only for a legacy current project, `doMigrateProject()` migrates → refreshes → re-opens the now-V2 session (`migrated … → v2 · rev N ✓`). Battery `binding_run33.py` AA1-AA10 PASS_REF_AND_NATIVE (45s) — AA7 proves the read-only gap is closed (V2 persist over V1 raises `WRL_BAD_PROJECT` before migrate, Saves succeed after), AA8 the migrated run films are byte-equal + revision unchanged, AA10 the migrated demo folds `ic_ref == ic32 == oracle`. NO new identity, NO new runtime construct — a project-DOC representation upgrade over the frozen identity spine) + Spinner Bench v0.6-2 (Forge World Library phase 9 — Startup/Project UX: a reload used to re-dump the demo world even after the author had opened a named project; a NEW non-authoritative `LastSessionPointerV1` (`forge.last_session.v1`) records the LAST opened project so a reload lands back in it — the pointer advances NO `project_revision`, moves NO `SemanticArtifactID`, and SELF-HEALS a pointer at a trashed/removed project to null so startup never reopens a gone project. `wrl_project.py` adds `LastSessionStore` (a single dotted `.last_session.json` in the project root — a leading dot keeps it out of `ForgeProjectStore.list_projects`) with `set`/`get`/`clear` + `validate/canonicalize/serialize_last_session` (typed `WRL_BAD_SESSION_POINTER`) + `resolve_last_session(session_store, project_store)` which returns the id only if it still exists else clears + returns None; `spinner_bench.py` writes the pointer on every open/new/fork and adds `GET /api/session` (self-healing resolve); the frontend `restoreLastSession()` runs at boot after `loadProjects()` — if the pointer names a live project it `openSession`s it (`resumed last project X ✓`), else it keeps the demo. Battery `binding_run32.py` Z1-Z10 PASS_REF_AND_NATIVE (49s) — NO new identity, NO new runtime construct) + Spinner Bench v0.6-1 (Forge World Library phase 8 — Runtime-Job Lifecycle: the long ic-reducer folds (`/api/run` + `/api/verify`, especially native `ic32` verify) become CANCELLABLE background jobs with an observable state machine `queued → running → completed|failed|cancelled` + progress, over a bounded in-memory ring. A NEW module `wrl_jobs.py` (`RUNTIME_JOB_VERSION="forge.runtime_job.v1"`) is PURE orchestration — a single-worker `JobRegistry(execute, lock=None, max_jobs=64, worker=True)` takes an INJECTED `execute(kind, request, progress, should_cancel)` callable, so the FULL lifecycle is deterministic without the HTTP server or a real reducer; cooperative cancellation is checked at EPOCH BOUNDARIES (a single-epoch fold is atomic), jobs are EPHEMERAL/in-memory (the v0.6-0 recovery journal owns durability), and the synchronous `/api/run` + `/api/verify` endpoints STAY (batteries + Fixture-oracle path + backward compat) — jobs are an ADDITIVE async lane. `spinner_bench.py` threads OPTIONAL `progress`/`cancel` no-op hooks through `_run_traj`/`_run_traj_fixture`/`_run_payload`/`_verify_payload` (regressions byte-identical), adds `_JOB_REGISTRY` over the `_PIPELINE_LOCK`, `POST/GET /api/jobs` + `/api/jobs/<id>` + `/api/jobs/<id>/cancel`, and HARDENS `_send` against `BrokenPipeError`/`ConnectionResetError` so a client that navigates away no longer trips a benign traceback. The frontend runs Run/Verify AS jobs (submit → poll ~220ms → live `state… phase done/total` status) with a Cancel button that stops at the next epoch. Battery `binding_run31.py` Y1-Y12 PASS_REF_AND_NATIVE — NO new identity, NO new runtime construct) + Spinner Bench v0.6-0 (Forge World Library phase 7 — Crash-Recovery Journal: a SEPARATE, atomic, NON-authoritative `RecoveryJournalV1` (`forge.recovery.v1`) checkpoints the UNSAVED workspace into its own `.recovery/<project_id>.json` root — a SIBLING of `projects/`, never nested in a bundle — WITHOUT modifying `ForgeProjectV2`, advancing `project_revision`, moving any `SemanticArtifactID`, activating a candidate, or weakening explicit Save; it REUSES `wrl_converge.session_state` verbatim and mirrors the V2 `{name, scenario_digest, scenario}` scenario shape; a restart OFFERS but never auto-applies it; Save/Commit clear it only after a durable write while a failed Save preserves it; a diverged base is typed `WRL_RECOVERY_STALE` and opens as a fresh copy, never an auto-merge; battery `binding_run30.py` X1-X18 PASS_REF_AND_NATIVE — NO new identity that governs a run, NO new runtime construct) + Spinner Bench v0.5.1 (Forge World Library phase 6 — Workspace Persistence Closure: the Library now persists the COMPLETE authoring workspace, not just the last committed world. A NEW project-doc version `ForgeProjectV2` (`forge.project.v2` — a project-doc version, moves NO SemanticArtifactID) carries `{project_id, name, project_revision, active_world{semantic_id, canonical_source}, draft{…+ layout_undo_history}, source_document{raw_source, source_revision, parse_status, diagnostics}, canvas_layout, scenario_documents, selected_scenario_document_id, scenario_compatibility, commit_history}`; SAVE persists exactly what the author sees (a valid OR invalid draft, syntax-error editor text, layout, scenario selection, undo + idempotency state) WITHOUT activating a candidate, COMMIT still moves the active id only on a validated id-matched candidate (and also saves). `wrl_draft.draft_state/restore_draft` + `wrl_converge.session_state/restore_session` are the lossless workspace roundtrip; version dispatch (`project_version_of`/`canonicalize_project`/`_revision_of`/`open_session_from_project_any`) lets a V2 cache still read any on-disk V1 project. `TrashEntryV1` tombstones make trash restorable + NON-DESTRUCTIVE (restore original id when free, else a caller id, never a silent clobber). Two frozen export modes in `wrl_bundle.py` — FULL (default, closes over the active + candidate + every undo-snapshot + every commit-history world; a commit world with no reopenable source needs a `world_store` else `WRL_BUNDLE_UNRESOLVED`, never a silent downgrade) and THIN (explicit, active + scenarios only, marks `shallow_history=true`). Battery `binding_run29.py` W1-W22 PASS_REF_AND_NATIVE (56s): W1 valid uncommitted draft survives restart (not activated); W2 invalid draft survives (typed candidate_error verbatim); W3 syntax-error raw source survives (draft untouched); W4 active sealed world runnable beside an invalid draft; W5 candidate id + source_document diagnostics restore exactly; W6 semantic + layout revisions exact; W7 accepted replace-id idempotency ledger survives (retry no-ops); W8 undo depth survives; W9 undo after reopen restores the exact prior (id, layout) pair; W10 selected scenario restores; W11 incompatible scenario compatibility restores; W12 label change without moving a ScenarioDigest; W13 Fork Saved reproduces the complete saved workspace; W14 unsaved edits excluded from Fork Saved; W15 trashed project restorable; W16 restore collision typed WRL_PROJECT_EXISTS + non-destructive; W17 full bundle carries every history world; W18 unresolvable history world → WRL_BUNDLE_UNRESOLVED; W19 thin bundle marked shallow + drops history; W20 export→import preserves an invalid editable draft; W21 NATIVE reopened/imported world folds ic_ref==ic32==oracle; W22 golden presets immutable. V1 bundle battery (binding_run28 R1-R8) stays byte-identical green — V2 added additively via version dispatch. Frontend: a Save button + dirty indicator, Fork→"Fork Saved" label, a Restore… control, and a full/thin export-mode selector. NO new identity that governs a run, NO new runtime construct; ForgeProjectV2 is pure workspace projection over the frozen identity spine) + Spinner Bench v0.5-5 (Forge World Library phase 5 — project import/export + closure: a project is now PORTABLE as a self-contained `ForgeBundleV1`. A NEW module `wrl_bundle.py` packs a `ForgeProjectV1` document TOGETHER WITH every immutable object it references — `{bundle_version="forge.bundle.v1", project, worlds{sem-…: b64 SealedArtifact bytes}, scenarios{scen-…: b64 ScenarioDigest-domain bytes}}` — carrying its own content id `bundle-`+sha (just an export hash, NOT a runtime/semantic construct). Three laws: SELF-SUFFICIENCY (`build_bundle` derives the REQUIRED objects — the active world by re-lowering `world_source`, each scenario runtime from its ScenarioV1 doc — straight from the document, so a bundle is complete even if the source stores were empty; an optional source WorldObjectStore lets it ALSO carry historical commit-log worlds best-effort), CLOSURE (`verify_bundle_closure` refuses unless {active_world}∪{scenario digests} all resolve → `WRL_BUNDLE_UNRESOLVED`; history NOT required since `world_source` only reproduces the active world), IDENTITY (import re-lowers the imported `world_source` and asserts it reproduces `active_world_semantic_id` → `WRL_BUNDLE_IDENTITY`; each bundled object is content-addressed so `_put_bytes` re-hashes it on the way in, and the bundle is checked key-vs-bytes before any write → `WRL_BUNDLE_CORRUPT`/`WRL_BAD_BUNDLE`). `import_bundle` writes the objects (idempotent), verifies closure+identity, then CREATEs the project at revision 0 (never clobbers, `project_id`/`name` override lands under a new id). Only LIVE projects export (trashed tombstones live under `.trash/`, invisible to the store). `spinner_bench.py` wires module-level content-addressed `_WORLD_STORE`/`_SCEN_STORE` under `<root>/.objects/` + `POST /api/project/export|import`; the browser Library bar gains Export (download `<pid>.forge.json`) + Import (file picker → open). Battery `binding_run28.py` R1-R8 PASS_REF_AND_NATIVE (45s): R1 self-contained bundle + deterministic bundle_id; R2 export→import into a FRESH store family reproduces the project byte-for-byte + reopens to the active world; R3 closure passes, empty stores → `WRL_BUNDLE_UNRESOLVED`; R4 tamper → `WRL_BUNDLE_CORRUPT`, non-b64/bad-version → `WRL_BAD_BUNDLE`; R5 world_source≠active → `WRL_BUNDLE_IDENTITY`; R6 no-clobber + id/name override + idempotent object writes (no duplicate files); R7 an edited+committed world round-trips + reopens EDITED + history carried best-effort with a source store; R8 NATIVE — a world routed THROUGH export→import folds ic_ref==ic32==oracle. Verified LIVE (port 8796, temp root): open main → export (`bundle-c70056d6…`) → import under `copy` (same active `sem-8ae91fe9…`, one shared world object on disk, no duplicate) → re-import keeping `main` refuses (`WRL_PROJECT_EXISTS`) → tampered payload → `WRL_BUNDLE_CORRUPT` → missing export → `WRL_PROJECT_MISSING`; the browser Export button downloads the bundle (status `exported main (bundle-c70056d6…) ✓`, no console errors). NO new identity that governs a run, NO new runtime construct; `RemoveObject` stays non-cascading, multi-op atomic deletion DEFERRED) + Spinner Bench v0.5-4 (Forge World Library phase 4 — Library management: the store + cache + browser go PLURAL. `wrl_project.py` gains `ForgeProjectStore.list_project_infos` (named per-project summaries), `.rename` (display name only — `project_id` is the immutable identity key — with exact-CAS on the revision), `.fork` (copy a project's SAVED state — world reference + source + layout + scenarios + commit log — into a NEW id at revision 0, world/scenario objects shared by REFERENCE since they are content-addressed in the immutable substrate) and `.trash` (SOFT-delete: move the mutable `<id>.json` into a `.trash/` subdir — reversible, a single mutable-file op distinct from the DEFERRED multi-op atomic graph-object deletion, never touches shared immutable objects); `ProjectSessionCache` gains matching `list_infos`/`create_new`/`fork`/`rename`/`trash`. `spinner_bench.py` adds `GET /api/projects` + `POST /api/project/new|open|fork|rename|trash` (pure store/cache ops off `_DRAFT_LOCK`), and every draft endpoint now keys on the request's `session_id` (== project_id). The frontend adds a panel-1 Library bar — a project `<select>` + New/Fork/Rename/Trash — tracking `state.session`; switching a project opens it and syncs editor text + canvas + scenario + run. Battery `binding_run27.py` Q1-Q8 PASS_REF_AND_NATIVE (56s) — a FORKED world folds ic_ref==ic32==oracle — AND verified LIVE (port 8794, temp root): new `alpha`, dup→WRL_PROJECT_EXISTS, rename→rev 1, fork alpha→beta, open beta (6 nodes, canonical text), trash beta (moved to `.trash/beta.0.json`, `alpha`+`main` remain), re-trash→WRL_PROJECT_MISSING; the Library `<select>` change switches `state.session` correctly. Fork/Trash semantics chosen as defensible minimums (flagged for GPT-5.6 review). NO new identity, NO new runtime construct, `RemoveObject` stays non-cascading) + Spinner Bench v0.5-3 (Forge World Library phase 3 — session migration onto the durable store: the live server's ephemeral `_DRAFT_SESSIONS` dict is replaced by a NEW `wrl_project.ProjectSessionCache` that backs each `project_id` with a persisted `ForgeProjectV1` document (rooted at `FORGE_PROJECT_ROOT`, default `.forge_projects/`). A first access lazily CREATES a default project from the demo world (+ the two scenario presets golden/bench); a COMMIT is the persistence boundary — `_draft_commit_payload` now calls `cache.persist(project_id)` which writes the session's now-active world back with per-project exact-CAS, so committed edits survive a server RESTART, while uncommitted draft edits + the undo stack stay session-local (the v0.5-2 rule); `reset` reverts a session to its saved state (revert-to-saved, never wipes the project — authoring a NEW world is deferred to the v0.5-4 Library UI). Battery `binding_run26.py` P1-P8 PASS_REF_AND_NATIVE — the committed-then-persisted-then-reopened world folds ic_ref==ic32==oracle — AND verified LIVE: an edit committed on port 8791 (`project_rev 1`) reopens as the active world across a full process restart (4 nodes, commit log intact), not the demo. NO new identity, NO new runtime construct) + Spinner Bench v0.5-2 (Forge World Library phase 2 — the `ForgeProjectV1` project document store: a NEW `wrl_project.py` layers the MUTABLE, named, per-project document OVER the v0.5-1 immutable substrate — `{project_version, project_id, name, revision, active_world_semantic_id, world_source, layout, scenarios[{name, scenario_digest, scenario}], commits[…]}` — validated by a strict typed gate (`WRL_BAD_PROJECT`) and canonicalized (scenarios sorted by name + digests recomputed, commits in index order, layout validated). Because it is NAMED not content-addressed, `ForgeProjectStore` gives it atomic writes (the SAME persistence law reused from `wrl_store._atomic_write`: validate → serialize → temp file → flush+fsync → atomic rename) plus PER-PROJECT EXACT-CAS revision — `save(doc, expected_revision)` refuses to write unless the on-disk revision is EXACTLY `expected_revision` (`WRL_PROJECT_STALE`, no auto-merge) then bumps by one; `create` refuses to clobber (`WRL_PROJECT_EXISTS`), a `load`/`save` of an absent id is `WRL_PROJECT_MISSING`. Identity discipline unchanged: the project stores its world by REFERENCE (`active_world_semantic_id` + reopenable `world_source`); `session_to_project` builds a project from a valid `CanvasSession`, `open_session_from_project` re-lowers `world_source` and ASSERTS it reproduces `active_world_semantic_id` (closure) before restoring layout + commit log, and `sync_project_objects` puts the world + scenarios into the immutable stores so every reference resolves. Battery `binding_run25.py` O1-O8 PASS_REF_AND_NATIVE — a world persisted through a project stays natively runnable ic_ref==ic32==oracle; NO new identity, NO new runtime construct, `RemoveObject` stays non-cascading, multi-op atomic deletion DEFERRED) + Spinner Bench v0.5-1 (Forge World Library phase 1 — immutable content-addressed object stores: a NEW `wrl_store.py` adds three filesystem-backed, content-addressed stores keyed by the existing identity ladder — `WorldObjectStore` (`sem-`), `ScenarioRuntimeStore` (`scen-`), `ReplayBundleStore` (`replay-`) — each idempotent on write and HASH-VERIFIED on read (bit-rot/tampering → typed `WRL_STORE_CORRUPT`, absent id → `WRL_STORE_MISSING`, malformed bundle ref → `WRL_STORE_BAD_REF`); the on-disk key IS the hash of the stored canonical bytes so reorder-/label-equivalent inputs collapse to one file; persistence is the atomic-write law `validate → serialize → temp file → flush+fsync → atomic rename` (+ dir fsync); NO new identity and NO new runtime construct; battery `binding_run24.py` N1-N8 PASS_REF_AND_NATIVE — a world routed through the store stays natively runnable ic_ref==ic32==oracle) + Spinner Bench v0.5-0 (Source Surface Closure: the world SOURCE surface is now closed — the editor seed `DEMO_WORLD_SOURCE` is WORLD-ONLY (the `periods N` run-input line is gone; run inputs live in the two named `ScenarioV1` documents `GOLDEN_DEMO_SCENARIO` / `ACCEPTANCE_BENCH_SCENARIO`), and `wrl_draft.replace_world_source` now DESUGARS approved WRL sugar before parsing so a paste of the ergonomic surface (`every 2`, `rotor=quarter_turn_z`) Applies directly instead of leaking a raw `KeyError: 'period'`; the order is load-bearing — SCAN the raw source for forbidden run-input syntax FIRST, THEN `SG.desugar_core`, THEN `parse_wrl_core`, THEN seal, so run-input tokens are never lost by a source-to-source rewrite; every desugar/parse failure crosses the endpoint as a stable TYPED diagnostic (`WRL_SUGAR_MALFORMED` for a Python `ValueError`/`KeyError`/`IndexError`, a `WrlUnsupported` code otherwise), never a raw exception; desugar is a source pre-pass NOT a compiler gate so a sugar spelling and its numeric expansion seal to the SAME `SemanticArtifactID` and a sugar-only re-expression is a genuine semantic no-op; source spans are taken over the DESUGARED core (line-preserving, so span line numbers still index the raw source); battery `binding_run23.py` M1-M5 PASS_REF_AND_NATIVE + verified LIVE; multi-op atomic deletion stays DEFERRED, `RemoveObject` stays non-cascading; NO new runtime construct) + Spinner Bench v0.4-5 (native + golden closure through the LIVE endpoints + commit/undo history + scenario-compatibility rebind surfacing: the editing UI is closed — a session edit → commit → run over the running server yields a natively runnable world that folds `ic_ref == ic32 == the independent Fixture oracle` re-lowered from the returned view text, the `POST /api/draft/commit` endpoint promotes the sealed candidate to the active world and returns an append-only commit log entry plus the `scenario_compat` law surfacing — a committed world CHANGE keeps the `ScenarioDigest` INVARIANT while moving ONLY the `ReplayBundleID`, an UNEDITED commit is a no-op that leaves the demo id and golden films intact — the new panel-1 `#draft-commits` strip renders the monotone commit log (`#idx → active_semantic_id`), the undo depth, and the rebind block (`.cx-move` ScenarioDigest invariant ✓ / ReplayBundleID old→new · `.cx-noop` no-op), and a `GET /api/draft/history` endpoint reports `{commits, undo_depth, can_undo}`; battery `binding_run22.py` K1-K8 PASS_REF_AND_NATIVE, NO new runtime construct — the commit log is pure session bookkeeping) + Spinner Bench v0.4-4c (live text→canvas convergence in the browser: the WRL editor's text now drives the SVG Canvas through a server-side `wrl_converge.CanvasSession` — the `Apply → canvas` button POSTs the editor buffer to a NEW `POST /api/draft/source` endpoint which runs the v0.4-4b `ReplaceWorldSourceV1` transaction and returns the reconciled draft view, so one paste = one revision = one DraftDiff, a formatting/comment-only paste is a `semantic_noop` that leaves the revision unchanged, a parseable-but-invalid graph keeps the Canvas editable with a NULL candidate id while the active sealed world stays runnable, and `Undo draft` walks the monotone draft history; five stdlib endpoints `GET /api/draft` · `POST /api/draft/source` · `/api/draft/reset` · `/api/draft/undo` · `/api/draft/commit` stay OFF the `_PIPELINE_LOCK` since they are pure editor state; a session store `_DRAFT_SESSIONS` keyed by session_id lazily opens a CanvasSession over the demo world; verified LIVE in the browser across candidate_valid / semantic_noop / semantic_invalid / syntax_error / undo; NO new runtime construct and NO new battery — the endpoints reuse the J1-J18-covered `replace_world_source`/`apply_text`) + Spinner Bench v0.4-4b (free-form text→canvas convergence: a wholesale WRL Core text paste is applied by the ATOMIC `wrl_draft.replace_world_source` transaction — a SEPARATE `ReplaceWorldSourceV1`, NOT a multi-op GraphEditV1 — and the `CanvasSession.apply_text` routes it through, snapshotting the layout in LOCK-STEP with the draft's own history so ONE paste = ONE revision = ONE DraftDiff = ONE undo; idempotency is checked BEFORE the exact-revision CAS, the endpoint rejects legacy run-input syntax with a typed `WRL_WORLD_SOURCE_HAS_SCENARIO`, formatting/comments are non-semantic no-ops, a parseable-but-invalid graph stays editable with a null candidate id while the active sealed world stays runnable, `RemoveObject` stays non-cascading, and native folds hold ic_ref==ic32==Fixture oracle) + Spinner Bench v0.4-4a (canvas↔semantic binding: a `wrl_converge.CanvasSession` binds the WorldDraftV1 semantic draft to a CanvasLayoutV1 presentation document so a canvas GESTURE lowers 1:1 to a GraphEditV1 and drives the draft, the layout reconciles in lockstep, and the candidate SemanticArtifactID comes PURELY from the draft — presentation stays strictly non-identity, a canvas round-trips to text through the same canonical graph, and native folds hold; the free-form text→canvas reconciliation half is DEFERRED to v0.4-4b pending a GPT-5.6 contract ruling) + Spinner Bench v0.4-3 (object lifecycle: GraphEditV1 completes with AddObject/RemoveObject over the SAME exact-CAS + candidate-sealing + explicit-commit + monotone-undo contract; a lifecycle op enforces only its own precondition — object_id present/absent — the seal is the sole judge of structural legality; RemoveObject is NON-cascading so removing a wired node yields an invalid-but-editable candidate WRL_UNKNOWN_ENDPOINT that never commits, the honest delete is RemoveEdge then RemoveObject; no new runtime construct, a committed added-node world folds ic_ref==ic32 and a remove+re-add round-trip returns to the EXACT demo SemanticArtifactID) + Spinner Bench v0.4-2 (topology edits: GraphEditV1 extends to AddEdge/RemoveEdge/ReconnectEdge over the SAME exact-CAS + candidate-sealing + explicit-commit + monotone-undo contract; a topology op enforces only its own precondition, the seal is the sole judge of structural legality — unknown endpoint / illegal port pair / controller conflict — so an illegal rewire is an invalid-but-editable candidate that never commits; no new runtime construct, a committed rewire folds ic_ref==ic32 and a Remove+Add round-trip returns to the EXACT demo SemanticArtifactID) + Spinner Bench v0.4-1 (revisioned WorldDraftV1 draft store: the world is now editable through a monotone-revision draft with exact-CAS + idempotent edit_id + typed candidate sealing + explicit content-checked CommitDraftV1 + monotone undo restoring the exact prior SemanticArtifactID; SetObjectConfig only; no new runtime construct, a committed world folds through the unchanged plan/view path at ic_ref==ic32) + Spinner Bench v0.4-0 (document-boundary preflight: the three documents are separated at the IDENTITY layer before any editing UI — CanvasLayoutV1 is presentation-only with NO run inputs/semantic config, the ScenarioDigest now excludes UI labels as well as the world id, and scenario/world binding is enforced at run time; all identity-preserving, goldens byte-identical) + Spinner Bench v0.3-s5 (Demo | Author mode toggle: the scenario author panel is regression-safe by default — Demo locks a preset read-only, Author edits a throwaway copy; a pure presentation-layer split that cannot touch identity) + Spinner Bench v0.3-s4 (ADMIT Acceptance Bench: a second immutable preset walking all seven roadmap acceptance behaviours on the demo world with no new runtime construct + preset selector) + Spinner Bench v0.3-s3 (editable scenario table + author gestures: add-claim/reset/idle · retransmit · equivocate · delete · run-this-scenario, live ScenarioDigest with world identity untouched) + Spinner Bench v0.3-s2 (upgraded Film panel: ADMIT claim-state projection as a pure sidecar) + Spinner Bench v0.3-s1 (ScenarioV1 run-input document + ScenarioDigest, scenario-driven run path, `/api/scenario`) + Spinner Bench v0.3-pre (engineering preflight: Fixture-free run path + narrowed lock + identity caches) + Spinner Bench v0.2 (fifth SemanticDiff panel) + Spinner Bench v0.1 (four-panel web app over the real pipeline) + quarter_turn_z (forge_named_rotor_rne_sym_v1) + WRL Phase 3B.5.1 (tooling-contract closure) + WRL Phase 3B-5 (SemanticDiff + completion metadata) + WRL Phase 3B-4 (named rotor constants + concise clocks) + WRL Phase 3B-3 (stable diagnostics) + WRL Phase 3B-2 (canonical WRL Core formatter) + WRL Phase 3B-1 (source spans + origin mapping) + WRL Phase 3D.1.1 (Sealed Object Integrity) + WRL Phase 3D.1 (Backend Identity Closure) + WRL Phase 3D (CompilePlanV1 convergence + Fixture retirement) + WRL Phase 3C (canvas↔text↔runtime isomorphism) + 3C-0 sealing preflight + WRL slice 2.1 (sealing + lexical errata) + WRL slice 2 (Canonical Identity spine) + WRL slice 1 (WRL Core → Forge Semantic IR v1 → Fixture → TRVM → Film v0.7) + 3b.5f-2b BUILD/MEASURE + 3b.5f-2a BUILD/MEASURE + 3b.5f-1 (golden ADMIT + Film v0.7 + two golden repairs)

**SPINNER BENCH v0.6-2 — Startup/Project UX (GPT-5.6's v0.6 sequence put startup/project UX after the v0.6-1 runtime-job lifecycle. The gap it closes: the backend already had rich durable projects + a crash-recovery journal, but STARTUP ignored them — `boot()` always re-lowered the hardcoded demo world and left `state.session === "main"` even when the author had spent a session inside a named project, so a reload silently threw away *which project you were in*. v0.6-2 adds session continuity WITHOUT any new runtime construct or identity.). A NEW `LastSessionPointerV1` (`LAST_SESSION_VERSION = "forge.last_session.v1"`, fields EXACTLY `{last_session_version, last_project_id, updated_at}`) is a single non-authoritative pointer at the LAST opened project. `wrl_project.py` adds: `validate_last_session`/`canonicalize_last_session`/`serialize_last_session` (a strict typed gate `WRL_BAD_SESSION_POINTER` — non-dict, bad version, missing/extra field, a `last_project_id` that isn't a valid project id, a non-numeric/bool `updated_at`); `LastSessionStore(root)` persisting ONE dotted `.last_session.json` in the project root (`set(project_id, now=None)` atomic-overwrites via `wrl_store._atomic_write`, `get()` returns the canonical pointer or None on absence — NEVER raises, `clear()` is idempotent), the leading dot keeping it out of `ForgeProjectStore.list_projects`; and `resolve_last_session(session_store, project_store)` which returns `last_project_id` ONLY if that project still `exists`, else CLEARS the dangling pointer and returns None (self-heal, so startup never tries to reopen a trashed/removed project). `spinner_bench.py`: a module-level `_LAST_SESSION = PJ.LastSessionStore(_PROJECT_ROOT)`, `_LAST_SESSION.set(pid)` on every successful `/api/project/open|new|fork`, and `GET /api/session` → `{ok, last_project_id}` via `resolve_last_session(_LAST_SESSION, _FORGE_STORE)` (self-healing under `_DRAFT_LOCK`, off the `_PIPELINE_LOCK` — pure store state). The frontend (`spinner_bench.js`): `restoreLastSession()` runs in `boot()` after `loadProjects()` — it GETs `/api/session` and, if the id is live and differs from the current session, `openSession`s it (which already refreshes recovery) and sets `resumed last project X ✓`; otherwise `boot()` keeps the demo and refreshes recovery itself. Battery `binding_run32.py` Z1-Z10 PASS_REF_AND_NATIVE (49s): Z1 validate/canonicalize/serialize round-trips + idempotent + byte-stable; Z2 every malformed pointer is a typed `WRL_BAD_SESSION_POINTER`; Z3 an empty store get() → None (no raise) + clear() no-op; Z4 set(pid) then get() returns it with a wall clock + writes the file; Z5 set is an atomic overwrite + refuses a bad id; Z6 clear() drops the pointer + is idempotent; Z7 the `.last_session.json` pointer is NEVER listed as a project (dotted-file exclusion); Z8 `resolve_last_session` self-heals — a live pointer resolves, a pointer at a gone project resolves to None AND is cleared; Z9 IDENTITY INVARIANT — pointer set/clear/resolve churn moves NO project revision and leaves the demo world's SemanticArtifactID + per-epoch films byte-for-byte unchanged; Z10 NATIVE — with pointer churn interleaved, the demo verify folds `ic_ref == ic32 == the Fixture oracle`. Regressions stay green (binding_run31 Y1-Y12 83s, binding_run30 X1-X18 57s, both PASS_REF_AND_NATIVE). Verified LIVE (port 8765, server restarted): fresh `GET /api/session` → null → demo; create project `beta` → pointer tracks `beta` → RELOAD resumes into `beta` (`#lib-select` = "beta", status `resumed last project beta ✓`, 7 film rows, correct demo sem id); trash `beta` → `GET /api/session` self-heals to null (and stays null) → RELOAD falls back cleanly to the `main` demo (`ran 7 epochs (ic_ref) ✓`, no crash). NO new identity and NO new runtime construct — the pointer is additive startup state beside the durable project + recovery stores; the frozen lowering/fold and every prior endpoint are unchanged. Per the ruling, NEXT is v0.6-3 migration/packaging, then v0.6-4 perf/release closure.**
GPT-5.6's v0.6 ruling: v0.6 release hardening — v0.6-0 Crash-Recovery Journal ✓ → v0.6-1 Runtime-Job Lifecycle ✓ → v0.6-2 Startup/Project UX ✓ → v0.6-3 Migration ✓ → **v0.6-4 Perf/release closure — THIS SLICE, DONE (BB1-BB10 PASS_REF_AND_NATIVE) — v0.6 SERIES COMPLETE**. Bounded thread-safe LRU memos (`_LruCache`, cap 256) for `_PROG_CACHE`/`_TRAJ_CACHE` (a pure memo → an evicted key recomputes byte-identical → caps memory without moving identity) + a `GET /api/health` runtime self-check that re-lowers the demo FRESH and re-proves `DEMO_WORLD_SEMANTIC_ID`; NO new identity, NO new runtime construct. Batteries BB1-BB10 + AA1-AA10 + Z1-Z10 + Y1-Y12 + X1-X18 + W1-W22 + R1-R8 all green.
NEXT: the v0.6 series is COMPLETE — no ruled slice exists beyond v0.6-4. HOLDING for GPT-5.6's next-milestone steer (candidates: pinned Spinner Bench demo polish + public release build · resume the 3B ergonomic-surface ladder · a v0.7 identity/runtime feature).

---

**SPINNER BENCH v0.6-1 — Runtime-Job Lifecycle (GPT-5.6's v0.6 ruling put a runtime-JOB lifecycle after the v0.6-0 crash-recovery journal: turn the long ic-reducer folds into cancellable background jobs with an observable state machine + progress, so a client that navigates away neither aborts the compute nor trips a `BrokenPipeError` writing to a dead socket — the compute is DECOUPLED from the request that observes it). A NEW module `wrl_jobs.py` (`RUNTIME_JOB_VERSION="forge.runtime_job.v1"`, `JOB_KINDS=("run","verify")`) is PURE orchestration — it knows nothing about the reducer, the identity ladder, or the HTTP server. The state machine is `queued → running → completed | failed | cancelled` (cancelled reachable from queued OR running). `_Job` is an internal MUTABLE record (`__slots__`); callers only ever see an immutable `_snapshot` dict with EXACTLY `RUNTIME_JOB_FIELDS = (runtime_job_version, job_id, kind, state, progress{done,total,phase}, request, result, error, cancel_requested, created_at, started_at, finished_at)`. `JobRegistry(execute, lock=None, max_jobs=64, clock=None, worker=True)` takes an INJECTED `execute(kind, request, progress, should_cancel) -> result_dict`: it calls `progress(done, total, phase)` as it advances and `should_cancel()` at each epoch boundary, raising `JobCancelled` when True; any OTHER exception marks `failed` with a typed message, a normal return marks `completed`. `submit(kind, request)` validates kind∈JOB_KINDS + dict request (→ typed `WRL_BAD_JOB`) and enqueues at `queued`; `get`/`cancel` of an unknown id → `WRL_JOB_MISSING`; `cancel` is idempotent on terminal jobs, cancels a `queued` job IMMEDIATELY (the worker skips it), and sets a `threading.Event` on a `running` job so it stops at the next epoch. `_evict_locked` bounds the ring — it drops the OLDEST TERMINAL jobs past the cap but NEVER a queued/running job (so the ring may transiently exceed `max_jobs` rather than evict pending work). A single background worker thread drains a `queue.Queue`; `worker=False` + `run_pending()` drives the queue SYNCHRONOUSLY on the calling thread for tests. The injected `lock` (the server passes its `_PIPELINE_LOCK`) is held for the duration of `execute` so a job serializes against the legacy synchronous `/api/run`. `spinner_bench.py`: `_run_traj`/`_run_traj_fixture` gain OPTIONAL `progress=None, cancel=None, phase=None` (default no-op — the cache-hit branch reports `progress(total,total)` then returns, the loop checks `cancel()` and reports `progress(ep,total,phase)` per epoch, raising `WJ.JobCancelled` on cancel); `_run_payload`/`_verify_payload` thread them through with `except WJ.JobCancelled: raise` guards BEFORE the broad except so a cancel is `cancelled`, never `failed`; `_job_execute(kind, request, progress, should_cancel)` dispatches run→`_run_payload`, verify→`_verify_payload`; `_JOB_REGISTRY = WJ.JobRegistry(_job_execute, lock=_PIPELINE_LOCK, max_jobs=64)`; endpoints `POST /api/jobs` (submit), `GET /api/jobs` (list newest-first), `GET /api/jobs/<id>` (snapshot), `POST /api/jobs/<id>/cancel` (cancel); and `_send` is wrapped so a `BrokenPipeError`/`ConnectionResetError` on a dead socket sets `close_connection` instead of raising. The frontend (`spinner_bench.js`): `state.job`, `runJob(kind, extra)` submits then polls `/api/jobs/<id>` every 220ms updating the status line `kind state… phase done/total`, returning the result on `completed` / null on `failed|cancelled`; `doRun`/`doVerify` route through it; a Cancel button (`#btn-cancel`, hidden until a job is live) POSTs `/api/jobs/<id>/cancel`. Battery `binding_run31.py` Y1-Y12 PASS_REF_AND_NATIVE (96s): Y1 a submitted job runs queued→completed + returns the executor result; Y2 progress is reported monotonically and reaches (total,total); Y3 a job cancelled while QUEUED never runs (executor not invoked) and ends cancelled; Y4 a job cancelled while RUNNING stops at the next epoch → cancelled (partial, no result); Y5 an executor exception → failed with a typed message + the registry keeps working; Y6 unknown id → WRL_JOB_MISSING, bad kind / malformed request → WRL_BAD_JOB; Y7 the bounded ring evicts the oldest TERMINAL jobs past the cap but NEVER a queued/running job (three unrun jobs all stay queued, the ring exceeds the cap rather than drop pending work); Y8 cancellation propagates PAST `_run_payload`'s broad except AS `JobCancelled` (a cancel is `cancelled`, never a failed result); Y9 a REAL run job == the synchronous `_run_payload` (same SemanticArtifactID + per-epoch films); Y10 a job snapshot is the exact typed contract (RUNTIME_JOB_FIELDS, versioned); Y11 the synchronous `_run_payload` is unchanged with no hooks (default no-op progress/cancel); Y12 NATIVE — a real verify job (`oracle=true`) folds `ic_ref == ic32 == the independent Fixture oracle`, == synchronous `_verify_payload`. All prior batteries stay green (binding_run30 X1-X18 re-run PASS_REF_AND_NATIVE 52s; no regression from the `_run_traj` signature change). Verified LIVE (port 8765): a real `#btn-run` click streams progress and yields `ran 7 epochs (ic_ref) ✓` (7 film rows, Cancel auto-hidden), and a native verify cancel streams `0/7 → 1/7 → cancelled` at epoch 2. NO new identity and NO new runtime construct — jobs carry an opaque request + a result produced by the SAME lowering/fold as before; the synchronous endpoints + frozen lowering/fold are unchanged. Per the ruling, NEXT is v0.6-2 startup/project UX, then v0.6-3 migration/packaging, v0.6-4 perf/release closure.**
GPT-5.6's v0.6 ruling: v0.6 release hardening — v0.6-0 Crash-Recovery Journal ✓ → **v0.6-1 Runtime-Job Lifecycle — THIS SLICE, DONE (Y1-Y12 PASS_REF_AND_NATIVE)**. Ephemeral in-memory jobs (recovery journal owns durability), cooperative cancellation at epoch boundaries, synchronous endpoints kept as an additive baseline, `_send` hardened vs client disconnect. Batteries Y1-Y12 + X1-X18 + W1-W22 + R1-R8 all green.
NEXT (v0.6-2): startup/project UX, then v0.6-3 migration/packaging, v0.6-4 perf/release closure. Proceeding autonomously under the standing order unless GPT-5.6 steers.

---

**SPINNER BENCH v0.6-0 — Crash-Recovery Journal (GPT-5.6's v0.6-0 ruling: v0.5.1's explicit Save persists the complete workspace, but an author who never clicks Save loses everything on a crash; add a SEPARATE, atomic, NON-authoritative recovery overlay that checkpoints the UNSAVED workspace WITHOUT touching the authoritative project or weakening Save). A NEW `RecoveryJournalV1` (`recovery_version="forge.recovery.v1"`) in `wrl_project.py` has shape `{recovery_version, project_id, base_project_revision, recovery_revision, checkpointed_at, session_state, scenario_documents, selected_scenario_document_id, dirty_reasons}` — `session_state` REUSES `wrl_converge.session_state`/`restore_session` VERBATIM (the same lossless CanvasSession spine v0.5.1 froze), and `scenario_documents` mirror the V2 `{name, scenario_digest, scenario}` entry shape. `validate_recovery_journal`/`canonicalize_recovery_journal`/`serialize_recovery_journal` are a strict typed gate (`WRL_BAD_RECOVERY`) delegating session_state to `CG.validate_session_state`, checking the project_id regex, non-negative base/recovery revisions, a numeric timestamp, and `dirty_reasons ⊆ {text, graph, presentation, scenario, undo, selection, compatibility}`. A NEW `RecoveryJournalStore` is a directory of `<project_id>.json` overlays in its OWN `.recovery/` root — a SIBLING of `projects/` (`os.path.dirname(store._root)/.recovery`), NEVER nested in a project or bundle — obeying the SAME atomic-write law as every other store (validate → serialize → temp → flush+fsync → atomic rename), with idempotent delete. `ProjectSessionCache` grows the recovery contract, all NON-authoritative: `checkpoint(project_id, scenario_documents=None, selected_scenario_document_id=None, dirty_reasons=None)` writes a journal for the live UNSAVED session — a PURE overlay write that NEVER calls the project store, so it cannot advance `project_revision`, move a `SemanticArtifactID`, activate a candidate, or touch Fork/export (scenario_documents default to the SAVED project's when omitted); `recovery_status` reports the PERSISTED state a restart would find (`saved` / `recovery_available` / `recovery_stale`); `inspect_recovery` is a read-only summary (checkpoint age, `draft_valid`, active-vs-candidate id, `candidate_differs`, source parse status, undo depth, scenario count, staleness); `recover` loads the journal as the live UNSAVED dirty workspace (`restore_session`, the saved project + its revision UNTOUCHED, the candidate NOT activated — the user must still explicitly Save; a stale journal is refused `WRL_RECOVERY_STALE`); `discard_recovery` drops it; `open_as_recovered_copy` materializes a stale (or any) journal into a BRAND-NEW V2 project (never an auto-merge into the diverged saved project). Clear-triggers are ONLY Save/Commit/Discard: `persist` (Save) clears the journal ONLY AFTER `store.save` returns durably (a failed Save — which raises `WRL_PROJECT_STALE`/`WRL_PROJECT_MISSING` before the clear — PRESERVES it); Commit = `session.commit` + `persist`, so it clears through the same durable path; `trash` clears (an orphan overlay of a trashed project is meaningless). CRITICALLY `reset` (revert-to-saved) does NOT clear — revert-to-saved is ALSO the server boot/reopen path, and a reopen must NEVER auto-clear or auto-apply a crash journal. `spinner_bench.py` adds `POST /api/recovery/checkpoint|status|inspect|recover|discard|open-as-copy` + `GET /api/recovery/status` (all off `_DRAFT_LOCK`, keyed on session_id); the frontend adds a `#recovery-indicator` badge (`ck`/`avail`/`stale`/`err`), a ~1000ms debounced `scheduleCheckpoint(reason)` fired by `doApplyDraft`/`doDraftUndo` (NOT by film scrubbing/completion/diagnostics/view-only reads), and a reopen prompt (Inspect → Recover/Discard/later, or open-as-copy for a stale journal); Commit/Save clear the timer + badge. Two v0.6-0 cleanups: (1) the stale V1 "only committed state durable / undo session-local" docstrings in `wrl_project.py` are corrected to note that rule is V1-only (V2 persists the complete workspace); (2) `wrl_draft.replace_world_source`'s idempotent-replay path now NULLS the non-JSON `WrlSourceMap` in the persisted replace ledger so a retry BEFORE vs AFTER a restart is structurally identical. Battery `binding_run30.py` X1-X18 PASS_REF_AND_NATIVE (57s): X1 an unsaved VALID draft creates a journal (→ recovery_available); X2 an unsaved INVALID draft creates one (inspect draft_valid False, typed candidate_error preserved); X3 a syntax-error editor buffer is captured in session_state (the draft untouched); X4 a recovery write does NOT advance project_revision; X5 nor move the active semantic id (journal + saved project both keep the committed active world); X6 a RESTART detects but does NOT auto-apply (the reopened session reflects the SAVE); X7 Recover restores the EXACT workspace as a dirty session (session_state byte-equal, revision NOT advanced); X8 Recover does NOT activate the candidate (active stays committed, the uncommitted candidate returns); X9 Discard removes the journal + leaves the SAVED workspace intact; X10 Save clears the journal ONLY after a durable write; X11 Commit clears it ONLY after a durable write; X12 a FAILED Save (stale CAS) PRESERVES the journal; X13 a diverged base → `WRL_RECOVERY_STALE` (Recover refuses, status recovery_stale); X14 a stale journal opens as a BRAND-NEW recovered copy (original journal consumed, diverged project untouched); X15 Fork Saved EXCLUDES the journal (fork reflects the SAVE, source journal untouched); X16 normal FULL + THIN exports EXCLUDE the journal (no recovery data in a bundle, the on-disk journal not consumed); X17 the persisted indicator tracks the real on-disk state saved→recovery_available→saved; X18 NATIVE — a RECOVERED session's active sealed world still folds `ic_ref == ic32 == the independent Fixture oracle`. All prior batteries stay green (binding_run29 W1-W22, binding_run28 R1-R8 byte-identical). NO new identity that governs a run, NO new runtime construct — the journal is an emergency overlay, `ForgeProjectV2` + explicit Save are unchanged; the pinned Spinner Bench demo world stays natively runnable end to end. Per the ruling, v0.6-1 runtime jobs (queued/running/completed/failed/cancelled + progress/cancellation) is next.**
GPT-5.6's v0.6-0 ruling: v0.6 release hardening opens with **v0.6-0 Crash-Recovery Journal — THIS SLICE, DONE (X1-X18 PASS_REF_AND_NATIVE)**. RecoveryJournalV1 is a separate, atomic, non-authoritative overlay in its own `.recovery/` root; it never modifies ForgeProjectV2, advances no revision, moves no SemanticArtifactID, and is never auto-applied on reopen. Two cleanups landed (V1-docstring correction; idempotent-replay source_map frozen null). Batteries X1-X18 + W1-W22 + R1-R8 all green.
NEXT (v0.6-1): runtime jobs — queued/running/completed/failed/cancelled lifecycle + progress + cancellation (fixing the benign BrokenPipeError), then v0.6-2 startup/project UX, v0.6-3 migration/packaging, v0.6-4 perf/release closure. Proceeding autonomously under the standing order unless GPT-5.6 steers.

---

**SPINNER BENCH v0.5-5 — the Forge World Library closes: project import/export + closure. With the plural Library (v0.5-4) in place, GPT-5.6's v0.5-5 makes a project PORTABLE. A NEW module `wrl_bundle.py` defines `ForgeBundleV1` — `{bundle_version="forge.bundle.v1", project (a canonical ForgeProjectV1 doc), worlds{sem-<64hex>: base64 SealedArtifact canonical bytes}, scenarios{scen-<64hex>: base64 ScenarioDigest-domain bytes}}` — carrying its own content id `ForgeBundleID = bundle-`+sha256(canonical bundle bytes), which is PURELY the hash of an export artifact (NOT a new runtime/semantic construct; the world's `SemanticArtifactID` and each `ScenarioDigest` remain the only identities that matter). `build_bundle(doc, world_store=None)` is SELF-SUFFICIENT: it derives the REQUIRED objects straight from the document (the active world by re-lowering `world_source` — identity-checked — and each scenario's runtime domain from its ScenarioV1 doc), so an export is complete even if the source object stores were never populated; the optional source `WorldObjectStore` lets it ALSO carry historical commit-log worlds best-effort (those have no reopenable source, so they can only be copied when already present). `validate_bundle_v1` is a strict typed gate that also checks every bundled object's key AGAINST its bytes (`WRL_BUNDLE_CORRUPT`) and rejects non-base64 payloads / unknown `bundle_version` (`WRL_BAD_BUNDLE`). `verify_bundle_closure(doc, world_store, scenario_store)` enforces the CLOSURE law — the REQUIRED reference set is `{active_world_semantic_id} ∪ {scenario digests}`, each must resolve in the target stores (`WRL_BUNDLE_UNRESOLVED`) with a hash-verified read; historical commit worlds are NOT required (only `require_history=True` checks them) since `world_source` only reproduces the active world. `import_bundle(bundle, project_store, world_store, scenario_store, project_id=None, name=None)` writes every bundled object first (idempotent, content-addressed, `_put_bytes` re-hashes each against its claimed key on the way in), verifies closure + IDENTITY (the imported `world_source` re-lowers to `active_world_semantic_id` → `WRL_BUNDLE_IDENTITY`), then CREATEs the project at revision 0 (never clobbers — `WRL_PROJECT_EXISTS`); a `project_id`/`name` override lands the bundle under a new id without colliding. Only LIVE projects export — `export_project` loads through the `ForgeProjectStore`, which never sees `.trash/` tombstones, so a trashed project is excluded by construction (answering the v0.5-4 OPEN question: export = LIVE projects only). `spinner_bench.py` wires a module-level content-addressed object substrate `_WORLD_STORE`/`_SCEN_STORE` under `<FORGE_PROJECT_ROOT>/.objects/` (a dotted sibling dir the ForgeProjectStore never lists as a project), plus `POST /api/project/export` (build the bundle from the on-disk doc + carry history from `_WORLD_STORE`, return `{bundle, bundle_id}`) and `POST /api/project/import` (unpack an untrusted bundle → open the new project → return the projects list + view), both pure store ops off `_DRAFT_LOCK`. The frontend Library bar gains Export (fetch the bundle → download `<pid>.forge.json` via a Blob) + Import (hidden file picker → JSON.parse → optional id override → import → open). Battery `binding_run28.py` R1-R8 PASS_REF_AND_NATIVE (45s): R1 build_bundle packs a self-contained bundle (active world + every scenario object present; validates; deterministic content-addressed `bundle_id`); R2 export → import into a FRESH `(project, world, scenario)` store family reproduces the project byte-for-byte (`serialize_project` identical) and the reopened session re-lowers to the active world; R3 CLOSURE passes after import, empty target stores → `WRL_BUNDLE_UNRESOLVED`; R4 a tampered bundled object → `WRL_BUNDLE_CORRUPT`, non-base64 → `WRL_BAD_BUNDLE`, unknown `bundle_version` → `WRL_BAD_BUNDLE`; R5 a project whose `world_source` no longer lowers to its active id → `WRL_BUNDLE_IDENTITY` at build time; R6 import refuses to clobber (`WRL_PROJECT_EXISTS`), an id/name override lands under a new id, and content-addressed object writes are idempotent (`tw.ids()`/`ts.ids()` unchanged — no duplicate world/scenario files); R7 an EDITED + committed project exports/imports and reopens to the EDITED world, closes WITHOUT history, and a source WorldObjectStore lets it ALSO carry the historical (previous_active) commit world; R8 NATIVE — a world routed THROUGH export → import (read back from the imported `WorldObjectStore` → `P.artifact_to_compile_plan_v1` → plan view) folds `ic_ref == ic32 == the independent Fixture oracle` over its demo scenario. VERIFIED LIVE (port 8796, temp `FORGE_PROJECT_ROOT`): open `main` (demo world `sem-8ae91fe9…`, 6 nodes) → `POST /api/project/export` returns `bundle-c70056d6…` (1 world, 2 scenarios) → `POST /api/project/import` under new id `copy` reopens the SAME active world (`sem-8ae91fe9…`, projects `[copy, main]`) → re-import keeping `main` → `WRL_PROJECT_EXISTS` → a tampered world payload → `WRL_BUNDLE_CORRUPT` (key vs recomputed hash surfaced) → export of a missing project → `WRL_PROJECT_MISSING`; `<root>/.objects/worlds/` holds ONE world file shared by both projects (idempotency), `.objects/scen/` holds two scenario files; the browser Library Export button downloads the bundle (status `exported main (bundle-c70056d6…) ✓`) with NO console errors. Fork/Trash minimums from v0.5-4 stand (project_id immutable; fork shares immutable objects by reference; trash = reversible soft-delete of the mutable project file) — still flagged for GPT-5.6 confirmation. NO new identity that governs a run, NO new runtime construct, `RemoveObject` stays non-cascading, multi-op atomic deletion DEFERRED. This closes GPT-5.6's v0.5 order (0→5 all done); the pinned Spinner Bench demo world stays natively runnable end to end.**
GPT-5.6's v0.5 order: v0.5-0 Source Surface Closure ✓ → v0.5-1 immutable content-addressed object stores ✓ → v0.5-2 `ForgeProjectV1` project document store ✓ → v0.5-3 session migration ✓ → v0.5-4 Library UI panel ✓ → **v0.5-5 import/export + closure — THIS SLICE, DONE (v0.5 COMPLETE)**. Filesystem-first (NO database/cloud/multiplayer). Battery target M1-M20 met (N/O/P/Q/R batteries green).
NEXT: v0.5 is COMPLETE. HALTING for GPT-5.6 direction — confirm the v0.5-4 Fork/Trash minimums + v0.5-5 export=live-only decision, and rule the next milestone (candidate: a whole-Library export/import bundle carrying multiple projects + shared objects; or the deferred multi-op atomic graph-object deletion; or the pinned Spinner Bench demo polish).

---

**SPINNER BENCH v0.5.1 — Workspace Persistence Closure (GPT-5.6's post-v0.5 ruling: v0.5's committed-project Library was ACCEPTED but NOT fully closed — a SAVE must persist the COMPLETE authoring workspace, not merely the last committed world). A NEW project-doc version `ForgeProjectV2` (`project_version="forge.project.v2"`) is layered beside V1 via version dispatch; it is a PROJECT-DOC version, NOT a semantic-world version — it moves NO `SemanticArtifactID`. Its shape: `{project_version, project_id, name, project_revision, active_world{semantic_id, canonical_source}, draft{draft_id, profile_id, base/active/candidate_semantic_id, candidate_error, objects, edges, semantic_revision, undo_history, accepted_edit_ids, accepted_replace_ids, layout_undo_history}, source_document{raw_source, source_revision, parse_status, diagnostics}, canvas_layout, scenario_documents[{name, scenario_digest, scenario}], selected_scenario_document_id, scenario_compatibility, commit_history}`. The persistence spine is a LOSSLESS workspace roundtrip: `wrl_draft.draft_state`/`restore_draft` serialize the exact working graph (valid OR invalid — `validate_draft_state` re-seals it, catching sub-id tamper) plus the undo snapshots and the idempotency ledgers; `wrl_converge.session_state`/`restore_session` add the paired layout undo stack (equal depth), the presentation, the commit log, the raw editor buffer + parse status, the retained active-world source, and the scenario selection/compatibility. `session_to_project_v2`/`open_session_from_project_v2` fold the layout undo stack INTO the draft block (`layout_undo_history`) and back; `active_world` retains the LAST COMMITTED world (id + canonical source), independent of a possibly-diverged/invalid working graph, so the sealed active world stays runnable BESIDE an invalid draft. `ProjectSessionCache(store, default_world_source, scenarios_for, project_version=…)` dispatches on version — a V2 cache SAVEs the full workspace (`persist`), reopens it (`open` → `open_session_from_project_any`), and still reads any pre-existing V1 project. SAVE vs COMMIT are now distinct persistence boundaries: SAVE persists exactly what the author sees without activating a candidate; COMMIT still moves `active_semantic_id` only when the candidate validates AND its expected id matches, and COMMIT also saves. Trash is restorable + NON-DESTRUCTIVE: a `TrashEntryV1` tombstone `{trash_id, original_project_id, deleted_project_revision, deleted_at, project_document}` records the FULL document; `restore(trash_id, new_project_id=None)` restores under the original id when free, else a caller id, and REFUSES to overwrite a live project (`WRL_PROJECT_EXISTS`) — never a silent clobber; the tombstone is written durable-first, dropped only after the restore lands. Two frozen export modes in `wrl_bundle.py` (`ForgeBundleV2` = `{bundle_version="forge.bundle.v2", export_mode, shallow_history, project (V2 doc), worlds, scenarios}`): FULL (default) closes over EVERY world the workspace references — the active world (re-lowered from `active_world.canonical_source`), the candidate world when the draft is valid, every valid undo-history snapshot world (all self-derivable from the graphs embedded in the doc), AND every commit-history world (which has no reopenable source, so a `world_store` MUST resolve each one else `WRL_BUNDLE_UNRESOLVED` — never a silent downgrade); THIN (explicit) carries ONLY the active world + scenario objects + the reopenable project doc and marks `shallow_history=true`. `verify_bundle_v2_closure` checks the bundle against its OWN object maps (a V2 doc is already reopenable from its embedded graphs); `import_bundle_v2` verifies closure, writes every carried object (idempotent, content-addressed, hash-verified), then CREATEs at `project_revision` 0. ALL V1 bundle functions kept byte-identical (dispatch on `bundle_version`/`project_version`), so `binding_run28` R1-R8 stays green. Battery `binding_run29.py` W1-W22 PASS_REF_AND_NATIVE (56s): W1 a VALID uncommitted draft survives a restart (candidate id + validity restored; the active world NOT activated); W2 an INVALID draft survives (candidate None; the typed `WRL_CONTROLLER_CONFLICT` candidate_error restored verbatim); W3 a syntax-error raw source survives (the draft is untouched but the editor buffer + `parse_status` come back); W4 the active sealed world re-lowers to its id beside an invalid draft; W5 the candidate id AND the `source_document` (diagnostics included) restore exactly; W6 the semantic revision AND the canvas layout restore exactly; W7 the accepted replace-id idempotency ledger survives — a retry after restart no-ops (no new revision); W8 the undo depth (two edits → 2) survives; W9 undo AFTER a reopen restores the exact prior (semantic id, layout) pair; W10 the selected scenario restores; W11 a detached/incompatible scenario_compatibility restores; W12 a display-name change restores WITHOUT moving a ScenarioDigest; W13 Fork Saved reproduces the COMPLETE saved workspace (invalid draft included — `session_state` byte-equal); W14 unsaved edits are EXCLUDED from Fork Saved (the fork reflects the SAVE); W15 a trashed project is restorable from its tombstone; W16 restoring over a LIVE id is typed `WRL_PROJECT_EXISTS` and non-destructive (a new id restores cleanly, the live project untouched); W17 a FULL bundle carries every history-referenced world (with a source `world_store`); W18 a FULL bundle that cannot resolve a commit-history world → `WRL_BUNDLE_UNRESOLVED` (undo snapshots cleared so `previous_active` is only referenced by the commit log); W19 a THIN bundle is `shallow_history=true`, drops the history world, stays self-closed; W20 export→import preserves an INVALID, still-editable draft (same candidate_error, then a valid edit makes it valid again); W21 NATIVE — a reopened/imported active world folds `ic_ref == ic32 == the independent Fixture oracle`; W22 the golden scenario presets are immutable (a fresh project carries the exact canonical golden + bench presets). Frontend (`spinner_bench.html/js/css`): a Save button with a `•` dirty indicator (apply/undo set dirty, commit/open clear it), the Fork command relabelled "Fork Saved", a Restore… control (GET `/api/project/trash` → pick → POST `/api/project/restore`, offers a new id on a live collision), and a full/thin export-mode selector (thin downloads `<pid>.thin.forge.json`, status marks "history stripped"); server endpoints `POST /api/project/save`, GET `/api/project/trash`, `POST /api/project/restore`, and `export_mode` on export. NO new identity that governs a run, NO new runtime construct — ForgeProjectV2 is pure workspace projection over the frozen identity spine; the pinned Spinner Bench demo world stays natively runnable end to end. Per the ruling, v0.6 Spinner Bench release hardening (Save/dirty/recovery UX polish) is next; whole-Library bundles + multi-op atomic deletion stay DEFERRED.**
GPT-5.6's v0.5.1 ruling: v0.5 ACCEPTED but not fully closed → **v0.5.1 Workspace Persistence Closure — THIS SLICE, DONE (W1-W22 PASS_REF_AND_NATIVE)**. Filesystem-first; ForgeProjectV2 is version-dispatched beside V1 (moves no SemanticArtifactID). Battery W1-W22 green; binding_run28 R1-R8 (V1 bundle) stays byte-identical green.
NEXT (v0.6): Spinner Bench release hardening — Save/dirty/recovery indicators + UX polish (the ruling scoped these to v0.6). HALTING for GPT-5.6 confirmation of the v0.5.1 closure + direction on v0.6 scope (candidate deferrals: whole-Library multi-project bundles; multi-op atomic graph-object deletion).

---

**SPINNER BENCH v0.5-4 — the Forge World Library goes PLURAL (Library management). v0.5-3 migrated the live session onto ONE durable project; v0.5-4 makes the store + cache + browser manage MULTIPLE named, persisted worlds. `wrl_project.py`: `ForgeProjectStore.list_project_infos()` returns lightweight `{project_id, name, revision, active_world_semantic_id, scenarios, commits}` summaries (reads each doc, no re-lowering, sorted by name then id); `.rename(pid, new_name, expected_revision)` changes ONLY the display name (the `project_id` is the immutable identity key) with the same exact-CAS as any save; `.fork(src_pid, new_pid, new_name=None)` loads the source's SAVED state and `create`s a NEW project at revision 0 carrying the same `world_source`/`active_world_semantic_id`/layout/scenarios/commits — the world + scenario OBJECTS are shared by REFERENCE (content-addressed in the immutable substrate, nothing duplicated there) and a clobber refuses via `WRL_PROJECT_EXISTS`; `.trash(pid)` SOFT-deletes by `os.replace`-ing the mutable `<id>.json` into a `.trash/<id>.<n>.json` slot (reversible, never touches shared immutable objects, absent id → `WRL_PROJECT_MISSING`). `ProjectSessionCache` gains `list_infos`/`create_new`/`fork`/`rename`/`trash` (rename keeps any open session's tracked revision coherent; trash drops the open session). `spinner_bench.py` adds `GET /api/projects` + `POST /api/project/new|open|fork|rename|trash`, all pure store/cache ops serialized only by `_DRAFT_LOCK`, and every draft endpoint keys on the request's `session_id` (== project_id). Frontend: a panel-1 Library bar (`#library` — a `<select>` + New/Fork/Rename/Trash) tracks `state.session`; `openSession(pid)` opens a project and syncs the WRL editor text + canvas + draft status + commit log + scenario + run. Battery `binding_run27.py` Q1-Q8 PASS_REF_AND_NATIVE (56s): Q1 create_new mints a new project (demo world, rev 0) listed with its display name; Q2 create_new refuses to clobber (`WRL_PROJECT_EXISTS`); Q3 rename changes only the display name (project_id + world invariant, exact-CAS bumps revision); Q4 fork copies the SAVED state into a new id at rev 0 (same world/source/layout/scenarios/commits, source intact, re-fork refuses); Q5 fork forks the COMMITTED not an open session's uncommitted edit; Q6 trash soft-deletes (id leaves list_projects, file under `.trash/`, shared immutable world survives, absent trash → `WRL_PROJECT_MISSING`); Q7 list_project_infos summarizes + sorts; Q8 NATIVE — a FORKED world folds ic_ref==ic32==the independent Fixture oracle. Verified LIVE (port 8794, temp `FORGE_PROJECT_ROOT`): the endpoint sequence new/dup/rename/fork/open/trash/re-trash behaves exactly as the battery, `.trash/beta.0.json` appears on disk, and the browser Library `<select>` change flips `state.session`. Fork/Trash semantics are DEFENSIBLE MINIMUMS consistent with prior rulings (project_id immutable; fork shares immutable objects by reference; trash is a reversible soft-delete of the single mutable project file, NOT the deferred multi-op graph deletion) — flagged for GPT-5.6 review. NO new identity, NO new runtime construct, `RemoveObject` stays non-cascading, multi-op atomic deletion DEFERRED.**
GPT-5.6's v0.5 order: v0.5-0 Source Surface Closure ✓ → v0.5-1 immutable content-addressed object stores ✓ → v0.5-2 `ForgeProjectV1` project document store ✓ → v0.5-3 session migration ✓ → **v0.5-4 Library UI panel (New/Open/Fork/Rename/Trash) — THIS SLICE** → v0.5-5 import/export + closure. Battery target M1-M20 (running total N/O/P/Q batteries green). Filesystem-first (NO database/cloud/multiplayer).
NEXT (v0.5-5): project import/export + closure — export a project + its referenced immutable world/scenario objects as a self-contained bundle, import it into a fresh store, verify closure (every reference resolves) and identity (re-lowered world reproduces `active_world_semantic_id`). OPEN for GPT-5.6: confirm the v0.5-4 Fork/Trash minimums, and whether v0.5-5 export should include the `.trash/` tombstones or only live projects.

**SPINNER BENCH v0.4-0 — the document-boundary preflight for v0.4 (Semantic Canvas Editing). GPT-5.6 froze the v0.4 edit semantics and ruled the MIGRATION slice first: separate the three documents at the IDENTITY layer before building any editing UI. Three corrections land here, all identity-preserving. (1) Run inputs leave the canvas: canonical WORLD formatting (`wrl_format.format_wrl_core`) no longer emits the `periods N` line or inline `[epoch:N]` claim batches (the parser still ACCEPTS a legacy `periods` line for compat), and a NEW presentation-only `wrl_canvas.CanvasLayoutV1` (`graph_to_layout` / `validate_layout_v1` / `edge_key` / `layout_from_canvas_v1`) carries ONLY `{layout_version, profile_id, nodes[object_id, presentation], edges[edge_key, presentation]}` — a strict typed gate rejects any injected `periods` / `batches` / per-node `static_config`; the legacy `canvas.v1` funcs are retained as the compat loader. (2) Labels leave the ScenarioDigest: `wrl_scenario` replaces `_run_inputs` with `_digest_domain` = `{initial_runtime, [canonical claim batch per epoch]}` — UI labels (and the world id, already excluded) are DELIBERATELY omitted, so a label-only edit moves NEITHER identity while a claim edit still moves the digest; labels stay in the editable document. The trajectory cache (keyed by the label-free ScenarioDigest) now re-attaches the CURRENT scenario's labels on a cache HIT (`spinner_bench._with_labels`), so a label-only edit updates the display without recompute. (3) Scenario/world binding is enforced at run time: `wrl_scenario.check_world_binding` (called from `spinner_bench._resolve_scenario`) raises typed `WRL_SCENARIO_WORLD_MISMATCH` when a scenario is bound to a different world than the active one; structural validation still accepts the out-of-world CLAIM target (`zz`, a Rejected-receipt case, not a mismatch). Battery `binding_run16.py` (E1-E4, E17, E21) PASS_REF_AND_NATIVE (120 s): E1 layout has no run inputs/config + gate rejects injections + compat loader drops them; E2 label-only edit preserves the digest (claim edit moves it); E3 label-only edit updates displayed labels despite a cache hit (same digest + same films, new labels); E4 mismatched binding → `WRL_SCENARIO_WORLD_MISMATCH`, correct binding folds; E17 `zz` claim stays valid → Rejected(unknown_spinner); E21 demo reproduces the golden SCRIPT films, bench latches `[0,0,0,0,0,1,0,1,1]`, and canonical world format omits periods+batches yet re-parses to the SAME SemanticArtifactID (periods/batches never entered it — D3), ic_ref == ic32. No new runtime construct.**
GPT-5.6's v0.4 order: **v0.4-0 (identity/document migration — THIS SLICE)** → v0.4-1 (revisioned WorldDraftV1 draft store + explicit CommitDraftV1 + stale-revision CAS + idempotent edit_id + undo restoring exact SemanticArtifactID, SetObjectConfig only) → v0.4-2 (topology edits) → v0.4-3 (object lifecycle) → v0.4-4 (interactive canvas/text convergence) → v0.4-5 (native + golden closure). The v0.4 document model is FROZEN: WorldDraftV1 (semantic, earns the id) / CanvasLayoutV1 (presentation, never identity) / ScenarioV1 (run inputs, own ScenarioDigest); GraphEditV1 ops AddObject/RemoveObject/SetObjectConfig/AddEdge/RemoveEdge/ReconnectEdge; exact CAS (`base_revision == current` else `WRL_STALE_DRAFT`, no auto-merge); invalid drafts stay editable but never replace the active sealed world; undo restores the exact prior SemanticArtifactID (monotonic revision). Preset ruling: KEEP the nine-epoch ADMIT Acceptance Bench (no third tight-7-epoch world). **Identity-safety proven before touching the spine: `periods`/`batches` are excluded from the SemanticArtifactID (graph_to_ir, D3), so removing them from format/canvas is identity-preserving (E21).**
NEXT (v0.4-1): revisioned WorldDraftV1 draft store — candidate sealing + explicit commit + stale-revision rejection + idempotent edit_id + undo restoring exact IDs, initially SetObjectConfig only.

---

**SPINNER BENCH v0.5-3 — Forge World Library phase 3: session migration onto the durable store. With the immutable substrate (v0.5-1) and the mutable per-project document (v0.5-2) in place, GPT-5.6's v0.5-3 migrates the live server's editing sessions onto them so committed edits survive a restart. A NEW class `wrl_project.ProjectSessionCache(store, default_world_source, scenarios_for=None)` backs each `project_id` with ONE live `CanvasSession` over a persisted `ForgeProjectV1` document: `open(project_id)` lazily CREATES a default project from `default_world_source` (+ optional `scenarios_for(sem_id)` entries) if none exists, then re-opens the session via `open_session_from_project` (which re-lowers `world_source` and ASSERTS closure); `persist(project_id)` writes the session's now-active world + layout + commit log back with per-project EXACT-CAS on a tracked revision; `reset(project_id)` reverts the session to its saved document (revert-to-saved). Only the COMMITTED state is durable — the uncommitted draft working graph and the undo stack stay session-local (the v0.5-2 rule), so a commit is the single persistence boundary. `spinner_bench.py` drops the bare `_DRAFT_SESSIONS` dict for a module-level `_PROJECT_CACHE = PJ.ProjectSessionCache(PJ.ForgeProjectStore(_PROJECT_ROOT), DEMO_WORLD_SOURCE, scenarios_for=_default_scenarios)` (root `FORGE_PROJECT_ROOT`, default `HERE/.forge_projects`); `_get_or_open_session` → `_PROJECT_CACHE.open`, `_open_session` (reset) → `_PROJECT_CACHE.reset` (the legacy `src` override intentionally dropped), and `_draft_commit_payload` calls `_PROJECT_CACHE.persist(sid)` after a successful commit, returning the new `project_id` + `project_revision` in the commit envelope. All draft endpoints remain OFF the `_PIPELINE_LOCK` (serialized only by `_DRAFT_LOCK`). Battery `binding_run26.py` (P1-P8) PASS_REF_AND_NATIVE (50 s): P1 a first access lazily CREATES a default project from the demo world at revision 0 and the opened session reproduces the demo SemanticArtifactID; P2 an UNCOMMITTED `apply_text` edit moves the candidate but does NOT persist (the on-disk project stays the demo world at revision 0); P3 commit + persist writes the committed world (revision → 1, `active_world_semantic_id` moves to the committed id) and a FRESH cache over the same store reopens the session at exactly that world (restart-durable, `to_text()` re-lowers to the committed id); P4 exact-CAS is monotone — a second edit + commit + persist bumps the revision to 2 and the cache tracks it; P5 `reset` after an uncommitted edit reverts the session to the persisted (committed) world, NOT the demo, leaving the on-disk project unchanged; P6 the demo scenario presets (golden + bench) persist + survive reload (validate, digests match); P7 the reopened session's commit log is restored (length + last active id); P8 NATIVE — the committed-then-persisted-then-reopened world folds `ic_ref == ic32 == the independent Fixture oracle` over its demo scenario. VERIFIED LIVE (headless, port 8791, temp `FORGE_PROJECT_ROOT`): `/api/draft` opens the demo world (`sem-8ae91fe9…`, rev 0, 6 nodes); `POST /api/draft/source` applies the drop-p1+d0 edit (`candidate_valid`, `sem-67e954cf…`, rev 1); `POST /api/draft/commit` persists (`active sem-67e954cf…`, `project_revision 1`); after a FULL process restart `/api/draft` reopens the COMMITTED world (`sem-67e954cf…`, 4 nodes, commit log length 1), not the demo. NO new identity, NO new runtime construct.**
GPT-5.6's v0.5 order: v0.5-0 (Source Surface Closure — DONE) → v0.5-1 (immutable content-addressed object stores — DONE) → v0.5-2 (`ForgeProjectV1` project document store — DONE) → **v0.5-3 (session migration — THIS SLICE, DONE)** → v0.5-4 (Library UI panel: New/Open/Save/Fork/Rename/Trash) → v0.5-5 (import/export + closure). Filesystem-first (NO database server / cloud / multiplayer). Multi-op atomic deletion stays DEFERRED (`RemoveObject` non-cascading). Battery target M1-M20.
NEXT (v0.5-4): the Library UI panel — New / Open / Save / Fork / Rename / Trash over `ForgeProjectStore.list_projects` + project-scoped `/api/project/*` endpoints, so a user can name, switch between, and manage multiple persisted worlds from the browser.

---

**SPINNER BENCH v0.5-2 — Forge World Library phase 2: the `ForgeProjectV1` project document store. With the immutable substrate in place (v0.5-1), GPT-5.6's v0.5-2 layers the MUTABLE, named, per-project document OVER it. A NEW module `wrl_project.py` defines `ForgeProjectV1` — `{project_version="forge.project.v1", project_id, name, revision, active_world_semantic_id, world_source, layout (CanvasLayoutV1), scenarios[{name, scenario_digest, scenario}], commits[{index, semantic_revision, previous_active, active_semantic_id}]}` — the durable, reopenable state of one editing project. `validate_project_v1` is a strict typed gate (`WRL_BAD_PROJECT`): version, `project_id` regex, non-empty name, revision int≥0, `active_world_semantic_id` via the frozen `_SEM_ID_RE`, non-empty `world_source`, `CV.validate_layout_v1(layout)`, each scenario `{name, scenario_digest, scenario}` (validated + digest re-matched + unique names), each commit `{index==position, …}`. `canonicalize_project_v1` sorts scenarios by name (each canonicalized + digest recomputed), keeps commits in index order, re-validates the layout — two projects differing only in scenario order (or a scenario's claim order) canonicalize identically. Because a project is a NAMED, mutable record (NOT content-addressed), `ForgeProjectStore(root)` gives it optimistic-concurrency control instead: ATOMIC WRITES via the SAME persistence law as the object stores (reusing `wrl_store._atomic_write`: validate → serialize → temp file → flush+fsync → atomic rename), and PER-PROJECT EXACT-CAS revision — `create(doc)` forces revision 0 and refuses to clobber (`WRL_PROJECT_EXISTS`), `load(pid)` of an absent id is `WRL_PROJECT_MISSING`, and `save(doc, expected_revision)` refuses to write unless the on-disk revision is EXACTLY `expected_revision` (`WRL_PROJECT_STALE`, no auto-merge, mirroring the WorldDraft's exact-CAS) then bumps the revision by one. Identity discipline is unchanged: the project stores the world by REFERENCE (`active_world_semantic_id` + the reopenable `world_source`); the world's identity still comes ONLY from the sealed graph, presentation stays in the layout, run inputs stay in the ScenarioV1 documents. `session_to_project(session, project_id, name, scenarios)` builds a project from a CanvasSession's durable state (requires a VALID working graph — `candidate_error is None` — else `WRL_BAD_PROJECT`), `make_scenario_entry(name, scenario)` builds a `{name, scenario_digest, scenario}` entry, `open_session_from_project(doc)` re-lowers `SG.desugar_core(world_source)` to a fresh CanvasSession and ASSERTS it reproduces `active_world_semantic_id` (closure) before restoring the persisted layout + commit log (the undo stack is session-local, deliberately NOT persisted — a reopened project starts at undo_depth 0 over its durable `world_source`), and `sync_project_objects(doc, world_store, scenario_store)` ties the project to the immutable substrate (puts the world + each scenario runtime so every reference resolves, idempotent). Battery `binding_run25.py` (O1-O8) PASS_REF_AND_NATIVE (54 s): O1 a project built from a CanvasSession persists + reloads to byte-identical canonical bytes at revision 0 (`list_projects`/`exists` correct); O2 EXACT-CAS — `save` bumps the revision by one on a matching expectation, and a STALE expected revision is a TYPED `WRL_PROJECT_STALE` (no auto-merge, on-disk untouched); O3 durability — a FRESH store instance over the same root reloads the saved revision (no in-memory index); O4 create-clobber → `WRL_PROJECT_EXISTS`, load/save of an absent id → `WRL_PROJECT_MISSING` (never a raw `OSError`); O5 malformed documents → `WRL_BAD_PROJECT` (bad id, unknown field, mismatched scenario digest, a `world_source` that lowers to a different sem id); O6 closure — `sync_project_objects` puts the world + scenarios into the immutable stores so every reference resolves (idempotent — a second sync adds no files); O7 reopen — `open_session_from_project` re-lowers `world_source`, reproduces the active sem id (closure) and restores layout + commit log (`to_text()` byte-identical to the original session); O8 NATIVE — a world persisted THROUGH a project (create → load → reopened session → re-lowered) folds `ic_ref == ic32 == the independent Fixture oracle`. NO new identity, NO new runtime construct; `RemoveObject` stays non-cascading, multi-op atomic deletion DEFERRED.**
GPT-5.6's v0.5 order: v0.5-0 (Source Surface Closure — DONE) → v0.5-1 (immutable content-addressed object stores — DONE) → **v0.5-2 (`ForgeProjectV1` project document store — THIS SLICE, DONE)** → v0.5-3 (session migration: replace the single in-memory `_DRAFT_SESSIONS["main"]` with a ProjectStore + ProjectSessionCache, project-scoped endpoints) → v0.5-4 (Library UI panel: New/Open/Save/Fork/Rename/Trash) → v0.5-5 (import/export + closure). Filesystem-first (NO database server / cloud / multiplayer). Multi-op atomic deletion stays DEFERRED (`RemoveObject` non-cascading). Battery target M1-M20.
NEXT (v0.5-3): session migration — replace the single in-memory `_DRAFT_SESSIONS["main"]` with a `ForgeProjectStore` + a project-session cache, and make the `/api/draft/*` endpoints project-scoped so edits persist across restarts.

---

**SPINNER BENCH v0.5-1 — Forge World Library phase 1: immutable content-addressed object stores. With the world SOURCE surface closed (v0.5-0), GPT-5.6's v0.5 = Forge World Library / project persistence begins with the IMMUTABLE substrate. A NEW module `wrl_store.py` adds three filesystem-backed, content-addressed stores, each keyed by an EXISTING identity from the frozen ladder (wrl_scenario.py) — NO new identity, NO new runtime construct: `WorldObjectStore` (keyed by `SemanticArtifactID`, stores a `SealedArtifact`'s frozen canonical bytes), `ScenarioRuntimeStore` (keyed by `ScenarioDigest`, stores the digest DOMAIN `{initial_runtime, epoch_batches}` ONLY — world-id- and label-independent by construction), `ReplayBundleStore` (keyed by `ReplayBundleID`, stores `[world_semantic_id, scenario_digest, {numeric_faults}]`). Two laws hold in every store. (1) CONTENT ADDRESSING — the on-disk key IS the hash of the stored canonical bytes; a put recomputes the id from the bytes and REFUSES to persist a mislabeled object (`WRL_STORE_ID_MISMATCH`), writes are naturally idempotent (same content → same id → same single file), and reorder-/label-equivalent inputs collapse to one file. (2) HASH-VERIFIED READ — every get re-hashes the file bytes and refuses to return an object whose content no longer matches its key (`WRL_STORE_CORRUPT`), so bit-rot/tampering surfaces as a TYPED diagnostic, never silent bad data; an absent id is `WRL_STORE_MISSING` (never a raw `OSError`), a malformed bundle ref is `WRL_STORE_BAD_REF`. Persistence is the standard atomic-write law GPT-5.6 named: `validate → serialize → write a temp file → flush + fsync → atomic rename` (+ a best-effort directory fsync so the rename is durable); a crash mid-write can only leave a `.tmp-*` stub, never a torn object file. The stores hold NO in-memory index — a fresh instance over the same root reads exactly what is on disk. Battery `binding_run24.py` (N1-N8) PASS_REF_AND_NATIVE (55 s): N1 `WorldObjectStore` round-trips a sealed world by its `SemanticArtifactID` (byte-identical canonical bytes, `has()` true, re-put idempotent, one file); N2 a reorder-equivalent world (node declarations reversed) collapses to the SAME id and SAME single file; N3 a tampered on-disk world → typed `WRL_STORE_CORRUPT` (never silent bad data); N4 a get of an absent id → typed `WRL_STORE_MISSING` (never a raw `OSError`); N5 `ScenarioRuntimeStore` keys by `ScenarioDigest` and stores the runtime DOMAIN only — a label-only edit collapses to the SAME file (world-id/label excluded, `id_lbl == scen_id`, one file); N6 `ReplayBundleStore` keys by `ReplayBundleID` — a world edit (drop the once-at-1 pulser + door) moves the bundle id while the scenario store is untouched, and malformed refs (`not-a-sem`, `not-a-scen`) are typed `WRL_STORE_BAD_REF`; N7 a FRESH store instance over the same root reads + verifies what the first instance wrote (no in-memory index); N8 NATIVE — a demo world routed THROUGH the `WorldObjectStore` (put → get → re-lowered from the stored canonical artifact via `P.artifact_to_compile_plan_v1`) folds `ic_ref == ic32 == the independent Fixture oracle` over its demo scenario. This phase is REF-only by nature (the stores touch no runtime/backend); N8 is the required native anchor. NO new identity, NO new runtime construct; the identity ladder is reused verbatim.**
GPT-5.6's v0.5 order: v0.5-0 (Source Surface Closure — DONE) → **v0.5-1 (immutable content-addressed object stores — THIS SLICE, DONE)** → v0.5-2 (`ForgeProjectV1` project document store: atomic writes, per-project exact-CAS revision, persistent drafts/layouts/scenarios/commit history) → v0.5-3 (session migration: replace the single in-memory `_DRAFT_SESSIONS["main"]` with a ProjectStore + ProjectSessionCache, project-scoped endpoints) → v0.5-4 (Library UI panel: New/Open/Save/Fork/Rename/Trash) → v0.5-5 (import/export + closure). Filesystem-first (NO database server / cloud / multiplayer). Multi-op atomic deletion stays DEFERRED (`RemoveObject` non-cascading). Battery target M1-M20.
NEXT (v0.5-2): the `ForgeProjectV1` project document store — a mutable, per-project versioned document (name, active world sem-id, draft state, layout, scenarios, commit history) written atomically with per-project exact-CAS revision, layered OVER the immutable object stores.

---

**SPINNER BENCH v0.5-0 — Source Surface Closure (the mandatory correction that opens v0.5 = Forge World Library / project persistence). GPT-5.6 ruled: before any persistence work, close a correctness gap in the world SOURCE surface. The v0.4 editor seed shipped a `periods 7` run-input line AND the ergonomic WRL sugar (`every 2`, `once at 1`, `rotor=quarter_turn_z`) that the `Apply → canvas` path parsed with `parse_wrl_core` WITHOUT desugaring — so pasting the seed back leaked a raw `KeyError: 'period'` (a Format-then-Apply dance was required). Two changes close it. (1) The demo constant is SPLIT (`spinner_bench.py`): `DEMO_WORLD_SOURCE` is now WORLD-ONLY (no `periods`, no `[epoch:N]`), and the run inputs live in two NAMED `ScenarioV1` documents built once from the sealed demo world — `GOLDEN_DEMO_SCENARIO = SC.demo_scenario(DEMO_WORLD_SEMANTIC_ID)` and `ACCEPTANCE_BENCH_SCENARIO = SC.bench_scenario(DEMO_WORLD_SEMANTIC_ID)`; `/api/demo` seeds the world-only source and derives its script labels from `GOLDEN_DEMO_SCENARIO["epochs"]`, `/api/scenario` serves the two named presets. The independent hand-written `SCRIPT` claim oracle is RETAINED (it carries no source syntax) as the second encoding the synthesized golden scenario must reproduce. (2) `wrl_draft.replace_world_source` (the `ReplaceWorldSourceV1` transaction) now runs the load-bearing order GPT-5.6 mandated: SCAN the RAW source for forbidden run-input syntax FIRST (so a source-to-source rewrite can never silently drop a `periods`/`[epoch]` token) → `SG.desugar_core(source)` → `parse_wrl_core(core)` → seal; source spans are taken over the DESUGARED core (desugar is line-preserving, so span line numbers still index the raw source). Desugar is a source PRE-PASS, NOT a compiler gate: a sugar spelling and its numeric expansion parse to the same graph and seal to the SAME candidate `SemanticArtifactID`, so a sugar-only re-expression of the current graph is a genuine `semantic_noop`. Every desugar/parse failure is converted to a stable TYPED diagnostic — a `WrlUnsupported` (`_exc_diag`, e.g. `WRL_UNSUPPORTED_FEATURE` for an unknown named rotor) or, for a raw Python `ValueError`/`KeyError`/`IndexError` from a malformed spelling, the NEW `WRL_SUGAR_MALFORMED` code — so NO raw Python exception may cross the endpoint. `wrl_draft` gains `import wrl_sugar as SG` + the `WRL_SUGAR_MALFORMED` constant. Battery `binding_run23.py` (M1-M5) PASS_REF_AND_NATIVE (56 s): M1 the default editor world source is WORLD-ONLY (`_scan_world_source_scenario(DEMO_WORLD_SOURCE) is None`) and round-trips through Apply as a `semantic_noop`; M2 a sugar Apply and the canonical numeric Apply of the SAME edited world produce the SAME candidate id (both `candidate_valid`, both ≠ the demo id — proven with a real desugar expansion `period`∈core, `every 2`∉core); M3 a sugar-only re-expression of the current graph is a `semantic_noop` (revision unchanged); M4 invalid sugar (unknown rotor → `WRL_UNSUPPORTED_FEATURE`; `(every)` → `WRL_SUGAR_MALFORMED`) returns a TYPED diagnostic through the endpoint with the draft UNTOUCHED (revision 0, candidate == demo id) and the endpoint staying `ok:True` — never a raw Python exception; M5 NATIVE — the sugar-Applied edited world (re-lowered from its canonical view text) folds `ic_ref == ic32 == the independent Fixture oracle` over its demo scenario. Verified LIVE in the running preview (port 8765): `/api/demo` seeds the world-only source (no `periods`), the WRL editor status is "clean · no diagnostics", pasting the sugar seed to `POST /api/draft/source` yields `semantic_noop` (candidate `sem-8ae91fe9cbc5fd08…` = `DEMO_WORLD_SEMANTIC_ID`), a bad rotor → `{ok:true, status:"syntax_error", diagnostics:[{code:"WRL_UNSUPPORTED_FEATURE"}]}`, and `(every)` → `{ok:true, status:"syntax_error", diagnostics:[{code:"WRL_SUGAR_MALFORMED", message:"malformed WRL sugar: list index out of range"}]}`. NO new runtime construct; desugar is a pure source-to-source pre-pass over the frozen identity spine.**
GPT-5.6's v0.5 order: **v0.5-0 (Source Surface Closure — THIS SLICE, DONE)** → v0.5-1 (immutable content-addressed object stores: WorldObjectStore/ScenarioRuntimeStore/ReplayBundleStore, hash-verified on read) → v0.5-2 (`ForgeProjectV1` project document store: atomic writes, per-project exact-CAS revision, persistent drafts/layouts/scenarios/commit history) → v0.5-3 (session migration: replace the single in-memory `_DRAFT_SESSIONS["main"]` with a ProjectStore + ProjectSessionCache, project-scoped endpoints) → v0.5-4 (Library UI panel: New/Open/Save/Fork/Rename/Trash) → v0.5-5 (import/export + closure). Filesystem-first (NO database server / cloud / multiplayer); persistence law `validate → serialize → write temp file → flush → atomic rename`. Multi-op atomic deletion stays DEFERRED (`RemoveObject` non-cascading, never changed silently). Battery target M1-M20.
NEXT (v0.5-1): the immutable content-addressed object stores — `WorldObjectStore` (sem-hash), `ScenarioRuntimeStore` (scen-hash), `ReplayBundleStore` (replay-hash), each content-addressed and hash-verified on read, filesystem-backed.

---

**SPINNER BENCH v0.4-5 — native + golden closure through the LIVE endpoints + commit/undo history + scenario-compatibility rebind surfacing (the final v0.4 slice; the editing UI is now CLOSED end-to-end). GPT-5.6 ordered v0.4-5 as "native + golden closure, scenario-compatibility UI, commit/undo history, golden-preset byte invariance." Server (`spinner_bench.py`): `_scenario_compat(prev_world, new_world)` builds the demo scenario over the previously-active world, computes its `ScenarioDigest` + `ReplayBundleID`, and — if the committed world CHANGED — calls `wrl_scenario.rebind_scenario` and returns `{changed:True, scenario_digest, digest_invariant, replay_bundle_old, replay_bundle_new, replay_bundle_moved:True}`; an UNCHANGED world returns `{changed:False, …, replay_bundle_moved:False}`. `POST /api/draft/commit` now captures `prev_world = sess.draft.active_semantic_id` BEFORE the commit and returns `{ok, commit:{…, previous_active}, scenario_compat, view}`. `_draft_view` gained `undo_depth` + `commits` (the session's append-only log). `CanvasSession` (`wrl_converge.py`) keeps a pure-bookkeeping `self.commits` list — `commit()` appends `{index, semantic_revision, previous_active, active_semantic_id}` — and exposes `history()` → `{commits, undo_depth, can_undo}`, surfaced by a NEW `GET /api/draft/history?session_id=…` endpoint (`_draft_history_payload`), all OFF the `_PIPELINE_LOCK`. Frontend (`spinner_bench.html/.js/.css`): a `Commit` button + a panel-1 `#draft-commits` strip; `doCommit()` POSTs `/api/draft/commit`, redraws canvas/status, sets `#sem-id` to the new active id, and calls `renderCommits(view, scenario_compat)` which renders the monotone commit log (`#idx → <code>active_semantic_id</code>` · joined), the undo depth, and the compat block — `.cx-noop` (no-op commit, world unchanged, digest invariant, ReplayBundleID unchanged) or `.cx-move` (world changed → scenario rebinds: ScenarioDigest invariant ✓ + ReplayBundleID old → new). `renderCommits` is also called from `doApplyDraft`/`doDraftUndo`/`resetDraft`. Battery `binding_run22.py` (K1-K8) PASS_REF_AND_NATIVE (206 s): K1 the reset endpoint yields a clean view (rev 0, active == candidate == demo id, 6 nodes/4 edges, empty commit log, undo_depth 0); K2 the source endpoint applies a valid free-form edit (candidate_valid, rev 1, undo_depth 1, candidate id ≠ demo id, DraftDiff removes d0+p1); K3 the commit endpoint promotes the candidate (new active == candidate, previous_active == demo id), logs one commit, and surfaces the scenario-compat law (digest INVARIANT, ReplayBundleID MOVED); K4 NATIVE — the endpoint-committed world (re-lowered from the returned view text via `W.lower_program(text, W.parse_wrl_core)`) folds `ic_ref == ic32 == the independent Fixture oracle`; K5 golden invariance — an UNEDITED commit leaves active == the demo id, the compat is a no-op (digest invariant, replay bundle NOT moved), and the demo world still reproduces the golden SCRIPT films; K6 the commit log is append-only + monotone (two commits, indices 0/1, previous_active chains to the prior active_semantic_id); K7 the undo endpoint restores the EXACT prior candidate id (monotone revision increment) and reports undo_depth honestly; K8 NATIVE — the Golden Demo reproduces the golden SCRIPT films and the nine-epoch Acceptance Bench still folds ic_ref == ic32 (v0.4-5 did not perturb the presets). Verified LIVE in the running preview (port 8765): a canonical multi-line edit (remove door d0 + pulser p1) applied through `Apply → canvas` then `Commit` promotes the active id to sem-67e954… and the `#draft-commits` strip renders the `.cx-move` rebind block (ScenarioDigest scen-2be578… invariant ✓, ReplayBundleID replay-cd3ad… → replay-a4f531…); an unedited `Commit` renders the `.cx-noop` block (world unchanged, ReplayBundleID unchanged); the Format→Apply path canonicalizes the sugar demo to a `semantic_noop` (identity-preserving). No new runtime construct; the commit log is pure session bookkeeping.**
GPT-5.6's v0.4 order: v0.4-0 (identity/document migration — DONE) → v0.4-1 (revisioned WorldDraftV1 draft store — DONE) → v0.4-2 (topology edits — DONE) → v0.4-3 (object lifecycle — DONE) → v0.4-4 (interactive canvas/text convergence — DONE) → **v0.4-5 (native + golden closure — DONE)**. **v0.4 is COMPLETE: the Semantic Canvas Editing arc runs end-to-end — canvas ⇄ text ⇄ sealed candidate ⇄ explicit commit ⇄ native run — with presentation strictly non-identity, the seal the sole judge of structural legality, the ScenarioDigest invariant across a world rebind (only the ReplayBundleID moves), and the golden presets byte-invariant.**
NEXT: v0.4 is closed. The next major phase (v0.5?) needs a GPT-5.6 ruling on direction — candidates surfaced along the way: (a) the demo textarea ships WRL SUGAR (`every 2`, `quarter_turn_z`) which the CORE parser (used by `Apply → canvas`) rejects until `Format` canonicalizes it — a deliberate "sugar · format · complete" editor flow, but worth a ruling on whether Apply should accept sugar directly; (b) a persisted/named world library beyond the single in-memory `_DRAFT_SESSIONS["main"]`; (c) multi-op atomic deletion (RemoveObject is still deliberately NON-cascading). Halting for GPT-5.6's direction on v0.5 scope.

---

**SPINNER BENCH v0.4-4c — live text→canvas convergence in the browser (steps 3+4 of the v0.4-4 slice, deferred as UI in v0.4-4b). The reverse half's transaction (`ReplaceWorldSourceV1` / `apply_text`) is now WIRED to the running Spinner Bench SPA. Server (`spinner_bench.py`): a process-wide `_DRAFT_SESSIONS` store (guarded by `_DRAFT_LOCK`) lazily opens a `wrl_converge.CanvasSession` over the demo world per `session_id` (default `"main"`); a `_draft_view(session)` helper pairs each `draft.objects` entry with its `CanvasLayoutV1` node presentation and each `draft.edges` entry with its edge-route presentation, returning `{draft_id, profile_id, semantic_revision, candidate_semantic_id, candidate_valid, candidate_error, active_semantic_id, nodes[{id,role,static_config,presentation}], edges[{kind,src,dst,edge_key,presentation}], text (session.to_text()), can_undo}`. FIVE new endpoints, ALL in the pure-editor group OFF the `_PIPELINE_LOCK`: `GET /api/draft` (current view), `POST /api/draft/source` (runs `session.apply_text` with an auto-based `ReplaceWorldSourceV1` — `replace_id` from the client, `base_revision` defaulting to the session's current revision — and returns `{ok, apply:{replace_id, semantic_revision, status, semantic_noop, candidate_semantic_id, candidate_valid, canonical_wrl, diagnostics, draft_diff, active_semantic_id}, view}`; the `source_map` WrlSourceMap object is excluded as non-JSON), `POST /api/draft/reset` (fresh session), `POST /api/draft/undo` (monotone `session.undo()`), `POST /api/draft/commit` (content-checked `session.commit`, the SealedArtifact object stripped to `{draft_id, semantic_revision, active_semantic_id}`). Frontend (`spinner_bench.html/.js/.css`): panel 1 gains a `#draft-status` strip and the toolbar gains `Apply → canvas` + `Undo draft` buttons; `doApplyDraft()` POSTs the editor text with a monotone `replace_id` (`ui-<ts>-<seq>`, no client base_revision → auto-based server-side), then redraws the Canvas from the returned view and renders `drawDraftStatus(view, apply)` (a status badge ok/noop/invalid/err + revision + short candidate id + the DraftDiff line +obj/−obj/~obj/+edge/−edge + diagnostics); `doDraftUndo()`/`resetDraft()` mirror the undo/reset endpoints; `boot()` opens with `resetDraft()`. Presentation stays strictly non-identity: the Canvas is redrawn from the draft view but the candidate `SemanticArtifactID` comes PURELY from the sealed draft. Verified LIVE in the running preview (serverId, port 8765) across every transaction path: OPEN (6 nodes/4 edges, candidate valid rev 0, demo sem-8ae91fe9…); appending `[orb:orbX]{pose}` → `candidate_valid` rev 1, 7 nodes incl. orbX (default presentation x=480 color=#4d5061), DraftDiff `+obj orbX`, sem id moves to sem-89611b153714a72c…; a formatting-only re-paste → `semantic_noop` (blue badge, revision unchanged); an illegal port pair → `semantic_invalid` (candidate —, `WRL_ILLEGAL_PORT_PAIR` diagnostic, Canvas tracks the invalid graph, active world still runnable); a parse failure → `syntax_error` (`WRL_UNSUPPORTED_FEATURE`, revision unchanged); `Undo draft` → monotone rev increment back to the prior candidate-valid state. NO new runtime construct; NO new battery — the endpoints are a thin session/HTTP shell over the J1-J18-covered `wrl_draft.replace_world_source` + `wrl_converge.CanvasSession.apply_text` (the v0.3-s2..s5 UI slices set the precedent that a pure-UI slice is verified LIVE in preview against the existing battery, not with a fresh binding_run).**
GPT-5.6's v0.4 order: v0.4-0 (identity/document migration — DONE) → v0.4-1 (revisioned WorldDraftV1 draft store — DONE) → v0.4-2 (topology edits — DONE) → v0.4-3 (object lifecycle — DONE) → **v0.4-4 (interactive canvas/text convergence — v0.4-4a canvas→semantic→text DONE, v0.4-4b text→canvas transaction DONE, v0.4-4c live browser wiring DONE)** → v0.4-5 (native + golden closure). **v0.4-4c completes the v0.4-4 slice: the full text ⇄ canvas convergence loop now runs end-to-end in the browser over the real transaction, with presentation strictly non-identity and the seal the sole judge of structural legality.**
NEXT (per GPT-5.6's ordered plan): v0.4-5 — native + golden closure: prove a session-edited-then-committed world folds ic_ref==ic32==Fixture oracle from the LIVE endpoints, a scenario-compatibility UI (rebind + ScenarioDigest-invariant / ReplayBundleID-moves surfacing), a commit/undo history panel, and golden-preset byte invariance across the whole editing UI.

---

**SPINNER BENCH v0.4-4b — free-form text→canvas convergence (the reverse half of v0.4-4). GPT-5.6 ruled the free-form multi-change text edit as a SEPARATE atomic idempotent transaction `ReplaceWorldSourceV1` — NOT a `GraphEditV1.ReplaceGraph` (the 6 typed graph ops stay reserved for single-op edits). `wrl_draft.replace_world_source(draft, request)` implements the frozen processing law in order: (1) envelope gate (typed `WRL_BAD_EDIT`) + draft_id match; (2) IDEMPOTENCY on `replace_id` checked BEFORE the CAS (only MUTATING replaces are recorded, so a retry of a now-stale mutating replace still no-ops); (3) exact-revision CAS → `WRL_STALE_DRAFT` (no auto-merge, no decomposition); (4) parse the COMPLETE source — the endpoint REJECTS legacy run-input syntax (`periods N` / `[epoch:N] …`) with a typed `WRL_WORLD_SOURCE_HAS_SCENARIO` (world authoring and ScenarioV1 authoring are separate surfaces) and a parse failure yields `syntax_error` — BOTH leave the draft/revision/ids/layout/undo UNTOUCHED (the raw buffer is never the authoritative graph); (5) semantic NO-OP detection (equal canonical bytes to the current valid candidate → `semantic_noop`, no revision advance, no undo entry — formatting/comments are non-semantic); (6) otherwise replace the working graph ATOMICALLY — one snapshot, one revision increment, exactly one undo entry, seal a candidate → `candidate_valid` (+ candidate id, canonical_wrl, DraftDiff, source_map, diagnostics=[]) or, for a parseable-but-invalid graph, `semantic_invalid` (candidate id NULL + typed diagnostic + DraftDiff, revision still advances once, the invalid working graph is preserved editable, and the previously-active sealed world stays runnable). The `ReplaceWorldSourceResult` carries `{replace_id, semantic_revision, status∈(syntax_error|semantic_noop|semantic_invalid|candidate_valid), candidate_semantic_id|null, canonical_wrl|null, diagnostics, draft_diff, source_map, active_semantic_id}`. `wrl_converge.CanvasSession.apply_text(request)` routes the paste through the transaction and snapshots the layout in LOCK-STEP with the draft's own history — a layout snapshot is pushed and the canvas reconciled IFF the revision advanced (candidate_valid / semantic_invalid), so a syntax_error, a semantic_noop, and an idempotent replay leave BOTH the draft and the layout untouched, and `undo()` restores matching (semantic id, presentation) pairs. Canvas reconciliation: surviving object ids keep their node presentation, surviving edge keys keep their route presentation, new objects/edges get the deterministic default, removed disappear. `wrl_scenario.rebind_scenario(scenario, new_world_semantic_id)` (NEW) is the compatible branch of the commit-time scenario procedure — it moves ONLY the `world_semantic_id` VALIDATION METADATA (excluded from the digest domain), so the `ScenarioDigest` is invariant while the `ReplayBundleID` moves; `RemoveObject` stays NON-cascading (GPT-5.6 closed: reserve multi-op deletion for a future explicitly-atomic construct). Battery `binding_run21.py` (J1-J18) PASS_REF_AND_NATIVE (179 s): J1 a syntax failure leaves the revision/ids/canvas UNCHANGED (no undo entry); J2 the endpoint rejects `periods N` AND `[epoch:N] …` with `WRL_WORLD_SOURCE_HAS_SCENARIO`, draft untouched; J3 a formatting/comment-only replacement is a semantic NO-OP (no revision, no undo, id unchanged); J4 a multi-object replacement advances EXACTLY ONE revision and the canvas reconciles to the new object set; J5 a mutating replacement leaves EXACTLY ONE undo entry in both the draft history and the parallel layout history; J6 undo restores the EXACT prior SemanticArtifactID AND the EXACT prior layout (survivor presentation included); J7 a repeated `replace_id` is idempotent (same result, no further revision/undo); J8 a stale base_revision → `WRL_STALE_DRAFT`; J9 a parseable-but-invalid graph stays editable with a NULL candidate id + typed diagnostic, and a follow-up replacement repairs it; J10 an invalid replacement leaves the active sealed world (== demo id) runnable, ic_ref == ic32; J11 surviving objects/edges RETAIN their node/route presentation across a text replacement; J12 a new object gets the DETERMINISTIC default presentation; J13 text→draft→canvas→text reproduces the canonical bytes and the EXACT candidate id (re-applying `to_text()` is a semantic_noop); J14 a candidate replacement does NOT change the ScenarioDigest or the scenario's world binding (untouched until commit); J15 commit-time compatibility rebinds the world metadata, RETAINS the ScenarioDigest, and moves ONLY the ReplayBundleID; J16 RemoveObject remains NON-cascading (a still-wired removal keeps its dangling wires and seals an invalid-but-editable candidate); J17 NATIVE — a valid text-edited world folds ic_ref == ic32 == the independent Fixture oracle; J18 NATIVE — the Golden Demo reproduces the golden SCRIPT films and the nine-epoch Acceptance Bench still folds ic_ref == ic32 (v0.4-4b did not perturb the presets). No new runtime construct.**
GPT-5.6's v0.4 order: v0.4-0 (identity/document migration — DONE) → v0.4-1 (revisioned WorldDraftV1 draft store — DONE) → v0.4-2 (topology edits — DONE) → v0.4-3 (object lifecycle — DONE) → **v0.4-4 (interactive canvas/text convergence — v0.4-4a canvas→semantic→text DONE, v0.4-4b text→canvas DONE)** → v0.4-5 (native + golden closure). **v0.4-4b closes the TEXT → CANVAS direction with a SEPARATE atomic `ReplaceWorldSourceV1` transaction (kept distinct from the 6 single-op GraphEditV1 ops), preserving the "one edit = one revision = one undo" contract while admitting a wholesale multi-change paste. The world-authoring surface and the ScenarioV1 run-input surface stay separate (WRL_WORLD_SOURCE_HAS_SCENARIO); presentation stays strictly non-identity through the reconciliation; the seal remains the sole judge of structural legality (parseable-but-invalid ⇒ editable candidate, active world untouched); native folds hold ic_ref==ic32==Fixture oracle.**
NEXT (per GPT-5.6's ordered plan): v0.4-4c — connect the gesture layer to a live SVG canvas (drag/click/reconnect gestures → GraphEditV1 through the existing session), and a POST /api/draft/source editor endpoint with browser convergence (debounce, explicit Apply, preserve invalid raw text, canvas only after parse success). Then v0.4-5 — native closure, scenario-compatibility UI, commit/undo history, golden-preset byte invariance.

---

**SPINNER BENCH v0.4-4a — canvas↔semantic binding (the unambiguous half of v0.4-4). A NEW `wrl_converge.CanvasSession` binds the PRESENTATION document (`wrl_canvas.CanvasLayoutV1`) to the SEMANTIC `wrl_draft.WorldDraft`, delivering the CANVAS → SEMANTIC → TEXT direction of the v0.4-4 convergence over the existing identity + draft spine with NO new runtime construct AND no new draft-contract construct. Two gesture classes: a SEMANTIC gesture (`add_node`/`remove_node`/`add_wire`/`remove_wire`/`reconnect_wire`/`set_config`) is translated 1:1 by `gesture_to_edit` into a frozen GraphEditV1 and applied through the UNCHANGED `wrl_draft.apply_edit` (every draft rule — exact CAS, idempotent edit_id, candidate sealing, monotone undo — still holds), then the layout is reconciled to the working graph (survivors keep their presentation via a seed, newcomers get default presentation); a PRESENTATION gesture (`set_presentation`) mutates ONLY the layout, proving presentation is non-identity. The session's `candidate_semantic_id` comes PURELY from the draft; `to_text()` = `format_wrl_core(draft graph)` re-parses (`parse_wrl_core` → `lower_graph`) to the EXACT candidate id (canvas == text through the SAME canonical graph). `undo()` restores BOTH the exact prior candidate id and the exact prior presentation (a layout snapshot rides each semantic edit). Battery `binding_run20.py` (I1-I9) PASS_REF_AND_NATIVE (73 s): I1 an `add_node` gesture emits the correct AddObject GraphEditV1, moves the candidate to exactly the independently-lowered world, and the layout gains a default-presentation node (candidate id independent of the layout); I2 a `set_presentation` gesture leaves the draft, candidate id, and revision UNTOUCHED, mutating only the node's presentation block; I3 layout lockstep — after add/remove object + edge the layout's node set == the draft's object ids and its edge set == the draft's edge keys, and a survivor keeps its presentation across an unrelated semantic edit; I4 canvas → text identity — `to_text()` re-parses to the EXACT candidate SemanticArtifactID; I5 `gesture_to_edit` maps every semantic gesture to the right op (add_node→AddObject, remove_node→RemoveObject, add_wire→AddEdge, remove_wire→RemoveEdge, reconnect_wire→ReconnectEdge, set_config→SetObjectConfig), a presentation gesture is not semantic, and a malformed gesture raises WRL_BAD_GESTURE; I6 presentation is STRICTLY non-identity — injecting arbitrary x/y/color/collapsed into a node's presentation never changes the candidate id and the layout still passes `validate_layout_v1`; I7 the inherited draft contract holds through the session — an illegal `remove_node` of a still-wired node seals an invalid-but-editable candidate (WRL_UNKNOWN_ENDPOINT) while the layout reconciles, `undo` restores the exact prior candidate id AND presentation, and a stale pinned base → WRL_STALE_DRAFT; I8 NATIVE — committing a session that added a disconnected Orb yields a NEW active SemanticArtifactID and a scenario bound to it folds ic_ref == ic32; I9 NATIVE — committing a session that made ONLY presentation gestures leaves active == the demo SemanticArtifactID and reproduces the golden SCRIPT films byte-for-byte, ic_ref == ic32. No new runtime construct.**
GPT-5.6's v0.4 order: v0.4-0 (identity/document migration — DONE) → v0.4-1 (revisioned WorldDraftV1 draft store — DONE) → v0.4-2 (topology edits — DONE) → v0.4-3 (object lifecycle — DONE) → **v0.4-4 (interactive canvas/text convergence — v0.4-4a canvas→semantic→text DONE, v0.4-4b text→canvas DEFERRED for a ruling)** → v0.4-5 (native + golden closure). **v0.4-4 splits cleanly: the CANVAS → SEMANTIC → TEXT direction is fully dictated by the frozen contract (a gesture is just a 1:1 GraphEditV1, the layout is presentation-only, canvas serializes to canonical text) and is DONE here; the TEXT → CANVAS direction of a free-form multi-change edit is a genuine CONTRACT fork that needs GPT-5.6 (see NEXT).**
NEXT (v0.4-4b — HALTING for a ruling): how should a free-form multi-change WRL Core text edit map onto the incremental GraphEditV1 draft model? **Option A** — decompose the diff into a SEQUENCE of single-op GraphEditV1 edits (uses ONLY existing constructs, but the revision jumps by N, the edit is non-atomic, and undo granularity is per-op). **Option B** — a single atomic re-base / `ReplaceGraph` edit (one revision, one undo, cleaner UX, but a NEW draft-contract op that must be ruled). Recommendation: Option A if the ruling wants zero new constructs and is content with per-op undo; Option B if atomic multi-change text edits are a first-class UX goal. ALSO still open from v0.4-3: keep `RemoveObject` NON-cascading (honest RemoveEdge-then-RemoveObject, dangling caught by the seal) or make it cascade its incident edges. `apply_text` is NOT built until this is ruled.

---

**SPINNER BENCH v0.4-3 — object lifecycle. `GraphEditV1` is now COMPLETE: `wrl_draft` v0.4-3 admits the two OBJECT-LIFECYCLE ops — `AddObject` (carries an `object` = {object_id, role, static_config}) / `RemoveObject` (carries a `target` object_id) — over the SAME exact-CAS + candidate-sealing + explicit-commit + monotone-undo contract as v0.4-1/2, still NO new runtime construct. Design invariant preserved: a lifecycle op enforces ONLY its own precondition in `_apply_operation` (AddObject: the object_id is not already present → else WRL_BAD_EDIT; RemoveObject: the target IS present → else WRL_BAD_EDIT) — structural legality of the RESULT (an unknown `role` `WRL_UNSUPPORTED_FEATURE`, a bad static_config, or an edge left DANGLING by a NON-cascading RemoveObject `WRL_UNKNOWN_ENDPOINT`) is DEFERRED to the seal, so an illegal lifecycle edit yields an invalid-but-editable candidate (candidate id None + typed error) that never commits, never a raise. `RemoveObject` is deliberately NON-cascading — it drops ONLY the object, so removing a still-wired node leaves a dangling edge the seal rejects; the honest delete is `RemoveEdge` the node's wires first, then `RemoveObject`. `validate_edit_v1` gains a shape-only `_validate_object_spec` (typed WRL_BAD_EDIT: missing/malformed/unknown-field `object`, missing RemoveObject `target`). Battery `binding_run19.py` (H1-H9) PASS_REF_AND_NATIVE (71 s): H1 AddObject(disconnected Orb) moves the candidate to exactly the independently-lowered world, re-adding an existing object_id → WRL_BAD_EDIT (precondition, never reaches the seal); H2 RemoveObject of a still-wired node dangles its socket wire → seals invalid (WRL_UNKNOWN_ENDPOINT) yet stays editable + undoes clean, removing an absent target → WRL_BAD_EDIT; H3 RemoveEdge(sp→ob) then RemoveObject(ob) composes to exactly the independently-lowered world (node AND wire both gone); H4 the object-spec gate (missing/malformed/unknown-field object, missing target) all → WRL_BAD_EDIT; H5 AddObject with an unknown role seals invalid (WRL_UNSUPPORTED_FEATURE) yet stays editable + undoes clean — role legality is the seal's job; H6 lifecycle ops inherit the whole contract (stale base → WRL_STALE_DRAFT, idempotent edit_id no-ops, undo restores the exact prior id with the revision incrementing, commit needs the expected candidate then advances active); H7 an invalid lifecycle edit never commits (a dangling RemoveObject → WRL_INVALID_CANDIDATE, undo repairs); H8 NATIVE — committing a disconnected AddObject(Orb) yields a NEW active SemanticArtifactID and a scenario bound to that world folds ic_ref == ic32 (a world with an added node is natively runnable); H9 NATIVE — unwire+RemoveObject(ob) then AddObject(ob)+rewire round-trips to the EXACT demo SemanticArtifactID and the committed round-tripped world reproduces the golden SCRIPT films byte-for-byte, ic_ref == ic32. No new runtime construct.**
GPT-5.6's v0.4 order: v0.4-0 (identity/document migration — DONE) → v0.4-1 (revisioned WorldDraftV1 draft store — DONE) → v0.4-2 (topology edits — DONE) → **v0.4-3 (object lifecycle: AddObject/RemoveObject — THIS SLICE)** → v0.4-4 (interactive canvas/text convergence) → v0.4-5 (native + golden closure). **The full GraphEditV1 op set is now implemented (SetObjectConfig + AddEdge/RemoveEdge/ReconnectEdge + AddObject/RemoveObject); every op's candidate `SemanticArtifactID` is proven to equal an independently-lowered world (H1/H3/H8), the seal alone judges structural legality (H2/H5/H7), and lifecycle edits round-trip to the EXACT demo id (H9) — the draft store still rides the existing identity + plan/view spine, adding no compiler and no runtime term.**
NEXT (v0.4-4): interactive canvas/text convergence — wire the CanvasLayoutV1 presentation document to the WorldDraftV1 semantic edits so a canvas gesture emits a GraphEditV1 and a text edit reflects in the canvas, both converging on the SAME candidate SemanticArtifactID, with presentation staying strictly non-identity (per the v0.4 document model).

---

**SPINNER BENCH v0.4-2 — topology edits. `GraphEditV1` now admits the three TOPOLOGY ops (`wrl_draft` v0.4-2): `AddEdge` / `RemoveEdge` / `ReconnectEdge` (each carries an `edge` = {kind, src, dst}; ReconnectEdge also a `to` edge), over the SAME exact-CAS + candidate-sealing + explicit-commit + monotone-undo contract as v0.4-1 — still NO new runtime construct. `AddObject`/`RemoveObject` stay frozen-but-DEFERRED to v0.4-3 (object lifecycle). Design invariant: a topology op enforces ONLY its own precondition in `_apply_operation` (AddEdge: the edge is not already present; RemoveEdge/ReconnectEdge-source: the edge IS present; ReconnectEdge-target: the `to` edge is not already present) — structural legality of the RESULT (unknown endpoint `WRL_UNKNOWN_ENDPOINT`, illegal port pair `WRL_ILLEGAL_PORT_PAIR`, or a controller conflict `WRL_CONTROLLER_CONFLICT` = >1 signal-wire / socket into one node) is DEFERRED to the seal exactly like a bad static_config, so an illegal rewire yields an invalid-but-editable candidate (candidate id None + typed error) that never commits, never a raise. `validate_edit_v1` gains a shape-only `_validate_edge_spec` (typed WRL_BAD_EDIT: missing/malformed/unknown-field edge, missing ReconnectEdge `to`). Battery `binding_run18.py` (G1-G8) PASS_REF_AND_NATIVE (78 s): G1 AddEdge overloading r0 seals invalid (WRL_CONTROLLER_CONFLICT) yet stays editable + undoes clean, re-adding an existing edge → WRL_BAD_EDIT (precondition, never reaches the seal); G2 RemoveEdge moves the candidate to exactly the independently-lowered world, removing an absent edge → WRL_BAD_EDIT; G3 ReconnectEdge re-points a wire to exactly the independently-lowered rewired world, a missing source edge or a target that already exists → WRL_BAD_EDIT; G4 the edge-spec gate + DEFERRED AddObject/RemoveObject all → WRL_BAD_EDIT; G5 topology ops inherit the whole contract (stale base → WRL_STALE_DRAFT, idempotent edit_id no-ops, undo restores the exact prior id with the revision incrementing, commit needs the expected candidate then advances active); G6 an illegal rewire never commits (WRL_INVALID_CANDIDATE, undo repairs); G7 NATIVE — committing a legal pulser SWAP (two ReconnectEdges, p0↔p1 across r0 and d0) yields a NEW active SemanticArtifactID and a scenario bound to that rewired world folds ic_ref == ic32 (a rewired world born from editing is natively runnable); G8 NATIVE — RemoveEdge(p0→r0) then AddEdge(p0→r0) round-trips to the EXACT demo SemanticArtifactID and the committed round-tripped world reproduces the golden SCRIPT films byte-for-byte, ic_ref == ic32. No new runtime construct.**
GPT-5.6's v0.4 order: v0.4-0 (identity/document migration — DONE) → v0.4-1 (revisioned WorldDraftV1 draft store — DONE) → **v0.4-2 (topology edits — THIS SLICE)** → v0.4-3 (object lifecycle: AddObject/RemoveObject) → v0.4-4 (interactive canvas/text convergence) → v0.4-5 (native + golden closure). **Every wire change's candidate `SemanticArtifactID` is proven to equal an independently-lowered rewired world (G2/G3/G7), the seal alone judges structural legality (G1/G6), and topology edits round-trip to the EXACT demo id (G8) — the draft store still rides the existing identity + plan/view spine, adding no compiler and no runtime term.**
NEXT (v0.4-3): object lifecycle — extend `GraphEditV1` to AddObject / RemoveObject over the same contract; adding an object (role + static_config) and removing one (with its incident edges) must move the candidate id exactly as an independently-lowered world, an object removal that orphans a wire must be caught by the seal (invalid-but-editable), and a committed world with a lifecycle edit must fold ic_ref == ic32.

---

**SPINNER BENCH v0.4-1 — the revisioned WorldDraftV1 draft store. GPT-5.6 froze the v0.4 edit semantics; this slice makes the WORLD editable through a monotone-revision draft (`wrl_draft.WorldDraft` / `new_draft` / `apply_edit` / `undo` / `commit_draft`) WITHOUT ever silently replacing the active sealed world. The draft is pure DATA over the existing identity spine (`wrl_ir.lower_graph` / `wrl_canonical`) — NO new runtime construct. Five load-bearing rules, all frozen by the ruling: (1) EXACT CAS — `apply_edit`/`commit_draft` require `base_revision == current semantic_revision` else `WRL_STALE_DRAFT`, NO auto-merge; (2) idempotent `edit_id` — a retry returns the ORIGINAL result and does not advance the revision twice (the idempotency check runs BEFORE the CAS so a retry of a now-old base still no-ops); (3) typed candidate sealing — every edit re-seals the working graph and records the resulting `candidate_semantic_id`, or, when the edit makes the graph invalid, marks the candidate invalid + records the typed error while the draft STAYS EDITABLE (never commits, never replaces the active world); (4) explicit, content-checked commit — `commit_draft` requires the CAS base_revision AND an `expected_candidate_semantic_id` matching the current candidate (`WRL_COMMIT_MISMATCH`) and refuses an invalid candidate (`WRL_INVALID_CANDIDATE`) before `active_semantic_id` advances; (5) monotone undo — `undo` restores the working graph to its pre-edit bytes so `candidate_semantic_id` returns to the EXACT prior SemanticArtifactID, but `semantic_revision` still INCREMENTS (never decrements, so a concurrent stale base can never alias a revived one). v0.4-1 admits exactly ONE op kind, `SetObjectConfig` (replace one object's static_config); Add/Remove object/edge + Reconnect are frozen in the model but DEFERRED to v0.4-2/3 (their validation error names the deferral honestly). Battery `binding_run17.py` (F1-F10) PASS_REF_AND_NATIVE (85 s): F1 new_draft starts rev0 with base==active==candidate==exact sem-id, 6 objects/4 edges, `to_document()` = frozen WorldDraftV1 shape (no private history/ledger); F2 SetObjectConfig moves the candidate to the independently-lowered edited world (rev→1) while active is UNTOUCHED; F3 idempotent edit_id retry no-ops; F4 stale base → `WRL_STALE_DRAFT`, correct base applies; F5 monotone undo restores the exact prior sem-id (revision increments), empty history → `WRL_BAD_DRAFT`; F6 an unknown-config-key edit seals invalid (candidate None + typed error) yet stays editable + further edits apply + undo repairs, and commit refuses it `WRL_INVALID_CANDIDATE`; F7 `validate_edit_v1` typed gate rejects unknown version / missing field / wrong draft / unknown op / DEFERRED `AddObject` / missing target — all `WRL_BAD_EDIT`; F8 commit requires CAS + `expected_candidate` match then advances active, draft stays open; F9 NATIVE golden gate — a committed identity-preserving no-op leaves active == the demo sem-id and the committed sealed artifact drives the plan/view fold to reproduce the golden SCRIPT films, ic_ref == ic32; F10 NATIVE edited-world gate — a committed genuine rotor edit yields a NEW active sem-id and a scenario bound to that world folds through the plan/view path at ic_ref == ic32 (a world BORN from the editing path is natively runnable). No new runtime construct; the draft store cannot perturb any sealed world it does not explicitly commit.**
GPT-5.6's v0.4 order: v0.4-0 (identity/document migration — DONE) → **v0.4-1 (revisioned WorldDraftV1 draft store — THIS SLICE)** → v0.4-2 (topology edits: AddEdge/RemoveEdge/ReconnectEdge) → v0.4-3 (object lifecycle: AddObject/RemoveObject) → v0.4-4 (interactive canvas/text convergence) → v0.4-5 (native + golden closure). The frozen v0.4 document model is unchanged: WorldDraftV1 (semantic, earns the id) / CanvasLayoutV1 (presentation, never identity) / ScenarioV1 (run inputs, own ScenarioDigest). **The candidate `SemanticArtifactID` is proven to equal an independently-lowered edited world (F2) and to fold natively (F9/F10) — the draft store rides the existing identity + plan/view spine, adding no compiler and no runtime term.**
NEXT (v0.4-2): topology edits — extend `GraphEditV1` to AddEdge / RemoveEdge / ReconnectEdge over the same CAS + candidate-sealing + commit + undo contract (still no new runtime construct); the wire changes must move the candidate id exactly as an independently-lowered rewired world, and a committed rewired world must fold ic_ref == ic32.

---

**SPINNER BENCH v0.3-s5 — the scenario author panel is now REGRESSION-SAFE BY DEFAULT. A `Demo | Author` segmented toggle sits at the head of panel 6. In `Demo` (the default) the selected preset renders as an IMMUTABLE read-only table: every claim is plain text (no inputs, no delete, no row selection), all mutating gestures (`+ claim`, `+ reset`, `+ idle epoch`, `retransmit`, `equivocate`, `↺ preset`) are disabled, and the mode tag reads `<preset> · preset (read-only)`. In `Author` the panel starts from a FRESH editable copy of the same preset (inputs + gestures live) with the tag `<preset> · editing a copy`. Toggling either way re-copies the pristine preset from `state.presets`, so switching to Demo DISCARDS any edits and switching to Author always starts clean — the golden regression view can never be silently mutated. This is a pure presentation-layer split: no backend change, no new endpoint, no battery change (S1–S10 unchanged), and — like every bench feature — it cannot perturb the SemanticArtifactID or ScenarioDigest. `Run this scenario` stays enabled in both modes (running an immutable preset is the whole point of Demo).**
GPT-5.6's v0.3 slice order (ScenarioV1 → upgraded Film panel → editable table → new
golden preset → **Demo|Author**) is COMPLETE at slice 5. The toggle is `spinner_bench.js`
`setMode(m)`: it flips the `.on` class on the two seg buttons, enables/disables the six
gesture buttons via `setGesturesEnabled`, and calls `applyPreset(state.scenPreset)` to reload
the pristine copy; `renderScenario()` branches on `state.mode === "demo"` to emit read-only
rows. **No new runtime construct; no Python touched; the world identity and every digest are
untouched by the mode.** **Verified (running preview):** Demo default → 6 gestures disabled,
0 table inputs, 8 read-only rows, tag `Golden ADMIT Demo · preset (read-only)`; click Author →
gestures enabled, 29 inputs, 0 read-only rows, tag `… · editing a copy`; add an idle epoch then
switch to Demo → edit discarded (back to pristine read-only) → switch back to Author → the
added epoch is gone (fresh copy). `Run this scenario` still folds in both modes.
NEXT: v0.3 is COMPLETE. v0.4 (Semantic Canvas Editing — DraftGraphV1 / GraphEditV1 / revision
protection) is the next major phase but should be confirmed/ruled by GPT-5.6 before starting.

---

**SPINNER BENCH v0.3-s4 — the ADMIT Acceptance Bench: a SECOND immutable preset that walks all seven roadmap acceptance behaviours end-to-end, on the SAME demo world, with NO new runtime construct. New `wrl_scenario.bench_scenario(world_semantic_id)` is a 9-epoch ScenarioV1 (additional to `demo_scenario`, which is untouched) where each behaviour gets its own headroom so it reads cleanly: ep1 accept a full-scale (32767) SetRotor → `w1s1` receipt Applied; ep2 EXACT retransmit → no new fact, empty EpochControl (item 3, no 2nd effect); ep3 conflicting same-key payload (`w3s3` twice) → recognition `disputed`, first receipt immutable, and — crucially — only 3 observed facts so it is a TRUE dispute, never a capacity fault; ep4/ep5 idle saturation runway; ep6 the saturating rotor overflows → orb fault LATCHES (0→1); ep7 a reset on a non-firing epoch CLEARS it (1→0); ep8 a reset on a firing epoch is re-latched by the same-epoch overflow (COMMIT clears the old fault, REACT re-latches → stays 1); ep9 idle/replay → still latched + deterministic. The whole 9-epoch fold is ic_ref == ic32 == golden Film v0.7. Total observed facts = 5 (≤ MAX_FACTS = 6). Panel 6 gains a `<select>` preset picker (`Golden ADMIT Demo` / `ADMIT Acceptance Bench`); `GET /api/scenario` now returns BOTH presets in a `presets` map (golden default preserved for existing callers). Battery `binding_run15.py` grows to S10 (PASS_REF_AND_NATIVE, 151 s): it folds `bench_scenario` and asserts all seven behaviours at both the `_admit_projection` level (facts / receipts / recognition / EpochControl / no capacity fault) AND the world-fault level (`fault_ob` per epoch), plus native parity and deterministic replay.**
GPT-5.6's v0.3 slice order (ScenarioV1 → upgraded Film panel → editable table → **new
golden preset** → Demo|Author) reaches slice 4. The saturation physics are ENTIRELY existing:
the demo spinner is w=16 (full-scale rotor = 2^15−1 = 32767) driven by an every-2 pulser, so
the max rotor set in ep1 needs two firings to overflow → the first fault latch lands at ep6.
Because overflow recurs on firing (even) epochs, a reset on an ODD epoch (ep7) clears cleanly
while a reset on an EVEN firing epoch (ep8) is immediately re-latched — the two are the same
`ResetFault ob` claim landing on different phases of the world clock. **No new runtime
construct; the world identity is untouched; the golden preset is preserved verbatim.**
**Verified (running preview, native separately PASS):** switching the picker to
`ADMIT Acceptance Bench` loads the 9-epoch table + a new ScenarioDigest
(`scen-e97664cb…`) with the world sem-id fixed; `Run this scenario` folds 9 epochs ic_ref; the
World disc reads `orb fault: LATCHED` at ep6, the ADMIT panel shows `w3·s3 disputed` over 3
facts with an immutable first receipt at ep3, `ResetFault ob` clears at ep7, and `ResetFault ob`
+ overflow stays LATCHED at ep8; ep9 stays latched.
NEXT (slice 5): Demo | Author mode toggle (Demo immutable/regression-friendly; Author edits a
copy of the selected preset).

---

**SPINNER BENCH v0.3-s3 — the scenario table is now editable, and every edit is honest. Panel 6 "Scenario author" renders the working ScenarioV1 as an editable table (per-claim writer/sequence/op/target/payload inputs + delete) with author gestures: `+ claim`, `+ reset`, `+ idle epoch`, `retransmit`, `equivocate`, `↺ preset`, `Run this scenario`. Every mutation POSTs to the pure `/api/scenario` endpoint (`spinner_bench._scenario_payload`, no runtime lock) and updates the live ScenarioDigest + ReplayBundleID — while the world's SemanticArtifactID stays fixed (acceptance 1 & 2, live). The immutable "Golden ADMIT Demo · preset" is restorable at any time. Battery `binding_run15.py` grows to S9 (PASS_REF_AND_NATIVE, 65 s): the editor's data path (`_scenario_payload` validate+digest+replay, typed `WRL_BAD_SCENARIO` on junk), RETRANSMIT of an exact envelope (no fact/receipt, no EpochControl → item 3, no 2nd effect), and EQUIVOCATE with fact headroom (same key + different payload → `disputed` over 2 facts, first receipt immutable → item 4). Verified live: retransmit/equivocate append epochs that MOVE the digest with sem-id fixed; on the fact-saturated golden preset EQUIVOCATE honestly overflows (a capacity fault, not a dispute); a 9-epoch edited scenario runs ic_ref end-to-end.**
GPT-5.6's v0.3 slice order (ScenarioV1 → upgraded Film panel → **editable table** → new
golden preset → Demo|Author) reaches slice 3. The scenario author panel keeps a client-side
ScenarioV1 in `state.scen`; each gesture mutates it and calls `pushScenario()` → POST
`/api/scenario`. `_scenario_payload` VALIDATES (typed `WRL_BAD_SCENARIO`) and returns the
`{world_semantic_id, scenario_digest, replay_bundle_id}` triple — it computes the two
identities, it never mints or perturbs one, and it takes no `_PIPELINE_LOCK` (so the editor
stays responsive while a run/verify holds the runtime). `retransmit` appends a later epoch
carrying an EXACT copy of the selected claim (first-receipt policy ⇒ no second effect);
`equivocate` appends a same-key/different-payload claim (⇒ disputed where there is fact
headroom, overflow on the saturated preset). `Run this scenario` folds the edited ScenarioV1
through the UNCHANGED `_run_traj` plan/view path. **No new runtime construct; the world
identity is untouched by anything the editor does.** **Battery S9 (PASS_REF_AND_NATIVE):**
`_scenario_payload` mirrors the pure identity module and rejects junk; a retransmit fold has
byte-identical fact/receipt sets to the un-retransmitted fold and applies empty EpochControl;
a small headroom equivocate fold makes `w1s1` recognition `disputed` over 2 observed facts
while its receipt stays `Applied`.

**SPINNER BENCH v0.3-s2 — upgraded Film panel: the ADMIT claim-state, projected. New `spinner_bench._admit_projection` renders the selected epoch's admit ledger (observed facts / acceptance receipts / derived recognition / applied EpochControl / capacity-fault badges). Battery `binding_run15.py` S8 PASS_REF_AND_NATIVE (79 s). Pure sidecar — film hash byte-identical.**
GPT-5.6's v0.3 slice order (ScenarioV1 → **upgraded Film panel** → editable table → new
golden preset → Demo|Author) reaches slice 2. Each `/api/run` row now carries an `admit`
projection: `spinner_bench._admit_projection(view, claim, cfg_map, resets)` reads the golden
admit claim-state (from `admit.py`, UNCHANGED) and returns `{policy, fact_capacity_fault,
receipt_capacity_fault, capacity_fault, facts[], receipts[], recognition[], epoch_control}`
— facts sorted by `_fact_key`, receipts by writer with `_outcome_str`, recognition derived
per writer. The Film panel renders it in a scrollable region (`.film-scroll`): a policy line +
capacity-fault badges, the applied EpochControl (SetRotor/ResetFault), then a 3-column grid of
observed facts / acceptance receipts (Applied vs Rejected) / derived recognition
(unambiguous/disputed/unknown); selecting an epoch auto-scrolls the projection into view.
**It is a pure SIDECAR — an additive row field the Film v0.7 seal never reads.** The film
hash is byte-identical whether or not the projection is computed. **Battery S8
(PASS_REF_AND_NATIVE):** folds the demo through the plan/view, builds `_admit_projection`
per epoch, and asserts (a) `side_films == ref_films` (S7's reference fold — the sidecar
perturbs nothing); (b) e4's applied EpochControl is `ResetFault ob`; (c) e7 has 6 observed
facts, receipts are 5×Applied + 1×`Rejected(unknown_spinner)` (the out-of-world `zz` claim
canonicalized to an `INVALID_TARGET` SetRotor), every recognition `unambiguous`,
`set_rotor.sp == 10.0.0.0`, policy `admit_candidate_min_firstreceipt_v1`, `capacity_fault==0`.
**Verified (running preview, native ON):** after a run, epoch 1 shows `SetRotor sp=181.0.0.181`,
1 fact, 1 Applied receipt; epoch 4 shows the ResetFault; epoch 7 shows all 6 facts incl.
`SetRotor:#?:9.0.0.0` (the `zz` claim) with its `Rejected(unknown_spinner)` receipt; the 7 film
hashes are unchanged (`56a2980e/23c7c0cd/b9cd725a/2c2d8ac2/7cf6b32b/fb270e91/8c7bf5ed`).
NEXT (slice 3): editable scenario table + buttons (add claim / retransmit / equivocate / add
reset / insert idle / run / verify) → new 7-step golden preset → Demo | Author mode.

---

**SPINNER BENCH v0.3-s1 — ScenarioV1: the RUN-INPUT document earns its own identity (`ScenarioDigest`), orthogonal to the world's `SemanticArtifactID`. New `wrl_scenario.py` + battery `binding_run15.py` (S1–S7 PASS_REF_AND_NATIVE, 40 s) + `/api/scenario` + scenario-driven run path.**
GPT-5.6's three-documents ruling made concrete: the world (WorldDraftV1 →
`SemanticArtifactID`), its presentation (CanvasLayoutV1, never identity) and its RUN
INPUTS (ScenarioV1) are never conflated. `wrl_scenario.py` gives ScenarioV1 a
structured shape — `{scenario_version, world_semantic_id, initial_runtime{numeric_faults},
epochs[{epoch,label,claims[{writer_id,sequence,operation,target,payload}]}]}` — a typed
structural gate `validate_scenario_v1` (WRL_BAD_SCENARIO), an order-independent
`canonicalize_scenario_v1`, and `scenario_digest` = `scen-`+sha256 over the CANONICAL run
inputs **only** (initial_runtime + epochs; `world_semantic_id` is deliberately EXCLUDED),
plus `replay_bundle_id` = H(SemanticArtifactID, ScenarioDigest, initial runtime).
`scenario_to_script` lowers a ScenarioV1 to the exact `(initial_faults, script)` the
untouched admit driver folds; `demo_scenario` re-expresses the Golden ADMIT Demo as a
ScenarioV1 (the immutable preset). It is a pure DATA document — NO new runtime construct.
**Battery `binding_run15.py` (S1–S7, PASS_REF_AND_NATIVE 40 s):** S1 typed gate rejects
bad version/keys/world-id/epoch-gap/over-MAX_BATCH/op/payload while a well-formed scenario
(incl. the out-of-world `zz` Rejected-path target) passes; S2 canonical+digest are claim-
AND fault-order-independent; **S3 (acceptance 1 & 2)** a scenario edit moves the
ScenarioDigest with the SemanticArtifactID fixed, and a world edit moves the
SemanticArtifactID with the ScenarioDigest fixed; S4 identical inputs on different worlds
share a ScenarioDigest (world id excluded); S5 ReplayBundleID moves on world/scenario/
initial-runtime change and is otherwise stable; S6 `scenario_to_script(demo)` claim
envelopes are byte-identical to the historical hard-coded SCRIPT; **S7** demo_scenario
folded via the plan/view path reproduces the SCRIPT films byte-for-byte, ic_ref == ic32 ==
golden. **Bench wired:** `_run_traj`/`_run_traj_fixture` now fold a ScenarioV1's
`(initial_faults, script)` (no hard-coded SCRIPT), trajectory cache re-keyed by
`(SemanticArtifactID, reducer, ScenarioDigest)`; `/api/run` + `/api/verify` accept an
optional `scenario`; new GET `/api/scenario` serves the Golden demo scenario + its digest.
**Verified (running preview, native ON):** GET `/api/scenario` → 7 epochs, `scen-7a4fb6d9…`,
world `sem-8ae91fe9…`; default `/api/run` (synthesizes demo scenario) and an explicit
posted-scenario run produce IDENTICAL films + digest; an edited scenario (fill idle epoch 2)
→ new `scen-3f77f834…` with the **same** `sem-8ae91fe9…` (acceptance 1 & 2 LIVE); a
malformed scenario → typed `WRL_BAD_SCENARIO`; `/api/verify {oracle:true}` →
`parity:true` (ic_ref==ic32 all 7) **and** `oracle.match:true` (plan/view == Fixture oracle)
through the scenario-driven path. Acceptance items 1, 2, 3–8 (via the golden preset), 9–12
now demonstrable on the ScenarioV1 substrate. NEXT: upgraded Film panel (observed facts /
recognition / receipt / EpochControl / overflow / numeric fault) → editable scenario table +
buttons → new 7-step golden preset → Demo | Author mode.

---

**SPINNER BENCH v0.3-pre — engineering preflight GPT-5.6 ordered BEFORE scenario authoring. Three backend corrections, all pure sidecars that cannot perturb identity; verified byte-identical.**
(1) **Fixture removed from the normal run path.** `_run_traj` now folds over the
CompilePlan `_PlanView` alone (`init_state_v6`/`admit_step`/`state_to_film_args_v6`
all consume the view — it duck-types the whole Fixture read interface); `_lower_payload`
derives `rotor_init` from the view too. No `as_fixture_for_test()` on any normal path.
The Fixture is RETAINED as a **selectable oracle**: `/api/verify {oracle:true}` also
folds the SAME script through the reconstructed Fixture and asserts the plan/view films
equal the oracle films (acceptance item 9) — the only path that builds a Fixture.
(2) **Initial fault is now EXPLICIT scenario state**, not a hidden `world["fault_ob"]=1`:
`_run_traj(initial_faults=…)` seeds the ScenarioV1 `initial_runtime.numeric_faults`
(default = every orb faulted). (3) **No hard-coded `sp`/`ob`**: rows carry generalized
per-object `rotors`/`poses`/`faults` dicts (scalar `rotor`/`pose`/`fault` kept as
first-spinner/first-orb convenience for the current disc UI). (4) **Lock narrowed**:
only `/api/run` + `/api/verify` take `_PIPELINE_LOCK`; `/api/lower`, `/api/diff`,
`/api/complete` stay responsive. (5) **Identity caches**: sealed program memoized by
source; reference trajectory memoized by `(SemanticArtifactID, reducer, initial-fault seed)`.
**Verified (running preview, native ON):** `/api/verify {oracle:true}` → `parity:true`
(ic_ref==ic32 all 7 epochs) **and** `oracle.match:true` (plan/view films == Fixture-oracle
films), same `sem-8ae91fe9cbc5fd08…`; during that 27 s native fold `/api/lower` returned
in **31 ms** and `/api/diff` in **37 ms** (lock narrowed); a cache-warm `/api/run`
returned in **4 ms**; page reload → "ran 7 epochs (ic_ref) ✓". Preflight complete;
v0.3 scenario authoring (ScenarioV1 + ScenarioDigest + editable table + upgraded Film
panel + new 7-step golden preset + Demo|Author mode) is UNBLOCKED.

---

**SPINNER BENCH v0.2 — fifth SemanticDiff panel surfacing the sealed `wrl_diff` with its live identity bridge law. New `/api/diff` endpoint + `#panel-diff` (A=editor source, B=editable variant).**
The panel diffs two WRL sources through the EXISTING sealed `wrl_diff.semantic_diff`
(desugaring both to core first, exactly as `_prog` seals), reporting each `Change`
(kind/key/detail), whether the diff is empty, both SemanticArtifactIDs, and the
headline **bridge law verdict** `is_empty() ⇔ sem_id(a)==sem_id(b)` rendered LIVE.
Pure identity-layer sidecar: it computes ids but never mints or perturbs one; a
side that cannot seal (invalid/unsupported) is reported with its typed
`WrlValidationError` and falls back to the tolerant `draft_diff` (no id claim).
**Verified (module + preview browser):** presentation-only edit (trailing comment)
→ empty diff, `sem(A)==sem(B)`, bridge HOLDS ✓ (green); rotor `n=8→n=6` →
`OBJECT_CHANGED sp: static_config.n, static_config.rotor`, ids differ, bridge HOLDS ✓
(blue); drop-door variant → `OBJECT_REMOVED d0/p1` + `EDGE_REMOVED SignalWire:p1->d0`;
two-sig-in door → clean `ok:false` `WRL_CONTROLLER_CONFLICT`. This is the
lowest-risk of the three v0.2 options posed in the v0.1 memo (it reuses a proven
sealed module and adds no runtime construct); the other two (structurally-editable
Canvas, author-able script) remain HELD for a GPT-5.6 direction ruling.

---

**SPINNER BENCH v0.1 — a local four-panel web application over the REAL WRL→IR→CompilePlan→TRVM pipeline. `spinner_bench.py` (stdlib HTTP backend, zero third-party deps) + `spinner_bench.html/.js/.css` (SPA).**
Closes GPT-5.6's post-quarter_turn_z order. Each request drives the production
lowering (`SG.desugar_core → W.lower_program → P.artifact_to_compile_plan_v1 →
P.plan_view → C.compile_step_v6`) and folds claim batches through `admit.admit_step`
+ the SAME ic_ref/ic32 reducers as the batteries (`binding_run3o.norm/.native`), so
the bench cannot diverge from the compiler — it *is* the compiler. Four panels:
**Canvas** (graph roles+typed edges from the sealed artifact), **WRL editor**
(sugar + `wrl_format`/`wrl_complete`/`wrl_diagnostics`, none entering identity),
**World disc** (per-epoch rotor/pose arrows + fault ring, 7-epoch scrubber), and
**Film+identity** (sealed SemanticArtifactID + per-epoch Film v0.7 + the
`forge_named_rotor_rne_sym_v1` named-rotor provenance badge, shown clearly SEPARATED
and labelled NOT-SEALED / geometry-dependent — the default resolution of the open
UX question). Endpoints `/api/{demo,lower,run,verify,complete}`; `/api/verify`
re-folds the script through native ic32 and asserts world+film parity per epoch
(gated by `TRVM_SKIP_NATIVE=1`). Demo world Pulser→Relay→Spinner(quarter_turn_z@n8)
→Orb + Once→Door, w=16 n=8, 7-step script; **verified end-to-end via agent-browser:
ic_ref trajectory + native ic32 == ic_ref, all 7 epochs (world + Film v0.7 identical),
SEM `sem-8ae91fe9…`, initial rotor (181,0,0,181).** Concurrency: the ic_ref runtime
`reset_runtime()`s module-global state, so a process-wide `_PIPELINE_LOCK` serializes
all pipeline requests (two concurrent `/api/verify` deadlocked without it).

---

**QUARTER_TURN_Z (forge_named_rotor_rne_sym_v1) PASS_REF_AND_NATIVE (4s, 11 checks P1–P11) — `wrl_sugar.py`, `wrl_complete.py` (edited) + `binding_run14.py` (new); `binding_run11/12/13` assertions updated for the grown vocabulary.**
GPT-5.6's post-3B.5.1 ruling implements `quarter_turn_z` (a 90-degree turn about z)
as the geometry-dependent SYMMETRIC INTEGER projection under the named policy
`forge_named_rotor_rne_sym_v1`:

    quarter_turn_z(n) = (round(2^n / sqrt(2)), 0, 0, round(2^n / sqrt(2)))

with **NO residual redistribution** — the two equal lanes are each rounded to
nearest INDEPENDENTLY and the norm is NOT renormalized back to 2^2n. `round(2^n/√2)`
is computed by EXACT INTEGER arithmetic (no float): with U=2^n, `q0 = isqrt(2·U·U)//2`
(= floor(U/√2)) and `q = q0+1 iff 2·U·U > 4·q0²+4·q0+1` (the squared nearest-integer
tie test), so **q4=(11,0,0,11), q8=(181,0,0,181), q16=(46341,0,0,46341)**; matches a
high-precision `round(2^n/√2)` for every n∈[0,24] (P1). Canonical sign scalar>0 (P2).
The name is added as a **policy-governed** entry in a SEPARATE registry
`wrl_sugar.NAMED_ROTOR_POLICY_TABLE` (name→`(policy_id, projection)`), leaving the
EXACT table (identity + axis reversals) and its zero-rounding invariant untouched;
`named_rotor` resolves exact-then-policy, `named_rotor_policy(name)` exposes the
policy id as **build provenance**. The policy id NEVER enters the artifact bytes —
`rotor=quarter_turn_z`@n8 and its numeric twin `rotor=181.0.0.181` seal to IDENTICAL
bytes + SemanticArtifactID (P3), so the sugar-washes-out pre-pass discipline holds;
but because the projected value depends on n, the identity is **GEOMETRY-DEPENDENT**
(same name at n=4 vs n=8 → different sem id, P4) — exactly as ruled. quarter_turn_z
is now ACCEPTED (was a typed reject in 3B-4); an unknown name / missing-n still
reject (P5). The accepted vocabulary is single-sourced `ALL_ROTOR_NAMES` (exact +
policy) and completion offers exactly it (P7). Formatter still emits the numeric
surface (P8); 3B-3 diagnostics fire through the desugar (P9); the SemanticDiff
bridge holds across a quarter_turn_z↔identity edit (P10); a quarter_turn_z world
runs **ic_ref==ic32==golden** (native, P11, reuses the persistent K-epoch fold). No
new runtime constructs. `binding_run11` N6 (quarter_turn_z was the reject fixture)
retargeted to an unknown name; `binding_run12` Q10 + `binding_run13` H12 completion-
set assertions now compare against `ALL_ROTOR_NAMES`. All regressions remain green.

**WRL PHASE 3B.5.1 PASS_REF_AND_NATIVE (4s, 15 checks H1–H15) — `wrl_canonical.py`, `wrl_sugar.py`, `wrl_complete.py`, `wrl_diff.py`, `wrl_diagnostics.py` (all edited) + `binding_run13.py` (new).**
GPT-5.6's pre-Spinner-Bench hardening ruling closes the four seams the 3B tools
leaned on but never sealed. **(1) Exact key sets.** `validate_artifact_v1` now
rejects ANY field not in the frozen set at every level — artifact
(`ir_version/profile_id/semantic_policies/schemas/objects/edges`), policy block,
object record (`object_id/role/static_config/state_schema_ref/ports`), edge
record (`kind/src/dst`), and per-role `static_config` (Pulser is `clock`-only;
Spinner is `w/n/rotor/configurable`; Relay/Door/Orb are empty) — via a new
`WRL_UNKNOWN_ARTIFACT_FIELD` code, raised BEFORE sealing so no meaning-bearing
field can smuggle past the identity spine by being silently dropped in
canonicalization (H1–H5). **(2) Sealed vs tolerant diff.** `wrl_diff` splits into
`semantic_diff(a,b)` — seals+validates both sides (or accepts a `SealedArtifact`),
REJECTS invalid/unsupported artifacts, and GUARANTEES the bridge law
`semantic_diff(a,b).is_empty() <=> semantic_artifact_id(a) == semantic_artifact_id(b)`
(H7,H9) — and `draft_diff(a,b)` — tolerant, canonicalizes for order independence
but does NOT validate legality, makes NO identity claim, so it previews a
future/unsupported profile as `PROFILE_CHANGED` (H8). `diff_artifacts` is retained
as a tolerant alias; `diff_graphs`/`diff_sources` are the sealed path (graphs
already seal). **(3) Authoritative registries.** Config keys move into
`wrl_canonical.ROLE_CONFIG_SCHEMA` (a `surface_keys`/`static_config_keys` pair —
Pulser's verbose surface folds to one positional `clock` field), and the
named-rotor table + concise-clock forms move into `wrl_sugar.NAMED_ROTOR_TABLE`
(name → a pure function of n) and `wrl_sugar.CLOCK_SUGAR_FORMS`; validator, sugar
and completion all CONSUME them, so completion reads the grammar rather than
mirroring it and provably cannot drift (H11–H12). **(4) Canonical semantic
locators.** `WrlValidationError` gains `primary_locator`/`related_locator`
(`ObjectKey(object_id)` / `EdgeKey(kind,src,dst)`) + a dotted `field_path`
(`static_config.rotor`) — all on the identity spine, NO source spans or filenames
— and `wrl_diagnostics` MAPS them through the `WrlSourceMap` to spans and carries
them on the `Diagnostic` record for a canvas to highlight; the two-element codes
(`WRL_DUPLICATE_ID`, `WRL_CONTROLLER_CONFLICT`) keep the dedicated scan since one
locator cannot name two elements of the same kind (H13–H14). The hardened
pipeline still runs ic_ref==ic32==golden (H15, native). No new runtime constructs;
regressions run8/9/10/11/12 all remain PASS_REF_AND_NATIVE. **3B fully closed;
next: `quarter_turn_z` under `forge_named_rotor_rne_sym_v1`, then Spinner Bench v0.1.** Prior: **WRL PHASE 3B-5 PASS_REF_AND_NATIVE (5s, 15 checks Q1–Q15) — `wrl_diff.py` (new, v0.1) + `wrl_complete.py` (new, v0.1) + `binding_run12.py` (new).**
3B-5 closes GPT-5.6's 3B ergonomics arc (formatter, spans, diagnostics, sugar)
with two pure, identity-free tools. **SemanticDiff** (`wrl_diff.py`) is a
STRUCTURED canonical difference between two Forge Semantic artifacts, keyed by the
same canonical keys the rest of 3B uses (object_id, `kind:src->dst` edge key). It
CANONICALIZES both inputs first (`canonicalize_artifact_v1`), so declaration
order / surface / whitespace wash out exactly as they do for the
SemanticArtifactID, and it covers EVERY identity-bearing top-level key
(ir_version, profile_id, semantic_policies, schemas, objects, edges). The
headline law: `diff_artifacts(a,b).is_empty() <=> semantic_artifact_id(a) ==
semantic_artifact_id(b)` (Q2) — an empty diff means the two canonical dicts agree
on every field → identical deterministic bytes → identical id, so the diff can
never disagree with the identity spine. Change kinds: `IR_VERSION_CHANGED`,
`PROFILE_CHANGED`, `POLICY_CHANGED` (per policy sub-key), `SCHEMA_CHANGED`,
`OBJECT_ADDED/REMOVED/CHANGED` (a rotor edit reports `static_config.rotor`, not
the whole config), `EDGE_ADDED/REMOVED`. **Completion metadata**
(`wrl_complete.py`) exposes the frozen WRL Core vocabulary as a structured
manifest (`surface_metadata()`) plus a cursor-aware `completions_at(src,
offset)`. Every candidate is a PURE PROJECTION of the frozen registries
(`ROLE_IDS`/`PORTS`/`EDGE_PORTS` + the 3B-4 named-rotor/concise-clock sugar) —
never a hand-authored constant or an invented token — so a completion can only
ever offer something the parser already accepts, and completion never touches a
graph so it cannot perturb identity. Six cursor contexts classify: role (after
`[`), port (inside `{}`), edge tag (after `--`), rotor value (after `rotor=`),
clock form (a Pulser paren with no `=`), config key (inside `(`). Proven
(binding_run12): identical artifacts → empty diff (Q1); the bridge law over an
edit matrix (Q2); a rotor edit → `OBJECT_CHANGED sp` (Q3); edge remove/add
antisymmetric (Q4/Q8); profile→`PROFILE_CHANGED`, policy→`POLICY_CHANGED` (Q5);
declaration-order shuffle / format-only edit → empty diff + same sem id (Q6, the
diff twin of 3B-2 L3); a run-input-only claim-batch edit → empty semantic diff
(Q7, D3); deterministic `render()` (Q9); every candidate ⊆ its frozen registry
(Q10); `surface_metadata` is a pure projection of the registries (Q11); all six
contexts classify correctly (Q12); every applied completion parses (Q13);
named-rotor completions == the frozen 3B-4 table + clock forms desugar (Q14); an
edited world still runs ic_ref==ic32==golden (Q15, native). No new runtime
constructs; regressions run5/6/8/9/10/11 all PASS_REF_AND_NATIVE. **3B ergonomics
arc complete (spans → formatter → diagnostics → sugar → diff+completion). Next:
the pinned Spinner Bench demo — the first visible Forge demo.** Prior: **WRL PHASE 3B-4 PASS_REF_AND_NATIVE (4s, 9 checks N1–N9) — `wrl_sugar.py` (new, v0.1) + `binding_run11.py` (new).**
GPT-5.6's 3B priority ruling closes the ergonomics arc (formatter, spans,
diagnostics) with 3B-4 surface SUGAR that canonicalizes to the frozen numeric
values. Two families: concise pulser clocks (`every 2` → `mode=periodic,
period=2, phase=0`; `every 3, phase 1`; `once at 5` → `mode=once, epoch=5`) and
named rotor constants (`rotor=identity` → `rotor=<2^n>.0.0.0`, plus the three
axis 180-degree reversals `reverse_x/y/z`, each projected to the spinner's own
fractional width n). Sugar is a source-to-source PRE-PASS — `desugar_core(src)`
rewrites the sugar to canonical WRL Core text, then the UNTOUCHED
`wrl_ir.parse_wrl_core` builds the graph — so a sugared program and its numeric
twin lower to IDENTICAL BYTES (N1, N8) and sugar can never introduce a new
identity, exactly the 3B-1/3B-3 sidecar discipline applied to the accept path.
The canonical formatter (3B-2) still emits the numeric surface, so named sugar
washes out like whitespace (N5). The FROZEN NAMED-ROTOR TABLE v1 is deliberately
EXACT-ONLY: identity + the axis reversals have quaternion components in {0,1},
representable with zero rounding at ANY n (N3). Irrational-valued names such as
`quarter_turn_z` (a 90-degree turn = √2/2 per component) are NOT frozen — their
numeric value depends on a rounding+normalization policy at the spinner's n that
permanently affects the SemanticArtifactID; that is a GPT-5.6 numeric-policy
decision, so an unknown/irrational name (and a named rotor with no n on the
declaration) is a typed `WRL_UNSUPPORTED_FEATURE` rejection, never a silent guess
(N6). Proven (binding_run11): named rotor == numeric twin over 4 names × 2
geometries, sem id + sealed bytes (N1); concise clock == verbose form (N2);
frozen exact table values (N3); desugar idempotent + a no-op on already-numeric
source (N4); formatter emits the numeric surface (N5); typed rejections (N6);
3B-3 diagnostics still fire through desugar — a dup id in a sugared source (N7);
a full sugared world == its numeric twin, bytes + sem id (N8); a sugared world
runs ic_ref==ic32==golden (N9, native). No new runtime constructs; regressions
run5/6/8/9/10 all PASS_REF_AND_NATIVE. **Open question flagged to GPT-5.6: the
`quarter_turn_z` (irrational named rotor) rounding+normalization policy at the
spinner n — pin it and the frozen table extends past exact-only.** **Next: 3B-5
SemanticDiff + completion metadata, then the pinned Spinner Bench demo.** Prior: **WRL PHASE 3B-3 PASS_REF_AND_NATIVE (4s, 12 checks G1–G12) — `wrl_diagnostics.py` (new, v0.1) + `binding_run10.py` (new).**
GPT-5.6's 3B priority ruling leads broad 3B with "canonical formatter + source
spans" — 3B-1 shipped the span sidecar, 3B-2 the canonical formatter, and 3B-3
renders a typed rejection as a portable record `Diagnostic{code, message,
primary_span, related_span, canonical_object_id}` with a stable `render()`. A
diagnostic is a PURE SIDECAR, exactly like the 3B-1 span map: the authoritative
accept/reject VERDICT is still the untouched `wrl_canonical` validators'
(`validate_graph`, `_validate_config`) and `wrl_ir`'s parsers'; the diagnostic
layer only CATCHES the real `WrlValidationError` (so code + message are verbatim,
never re-worded) and DECORATES it with the 3B-1 spans by locating the offending
object/edge. Locators cover the structural family — WRL_DUPLICATE_ID (primary =
2nd decl, related = 1st decl), WRL_UNKNOWN_ENDPOINT (edge span + missing-name
id), WRL_ILLEGAL_PORT_PAIR (edge span), WRL_CONTROLLER_CONFLICT (primary/related
= the two competing controller edges), WRL_CLOCK_RANGE / WRL_NUMERIC_RANGE (node
span, located by REUSING the authoritative `WC._validate_config`, zero logic
duplicated). Proven (binding_run10): clean sources yield no diagnostics (G1); the
five located codes carry code + object_id + spans (G2–G6); every primary span
slices to the offending token (G7); reformatting keeps code+object_id and moves
only the spans (G8, the diagnostic-stability twin of 3B-2 L3); running the pass
never perturbs identity (G9); `render()` is deterministic (G10); span fields +
sentinel file_id never appear in the sealed artifact bytes (G11); and a clean
world still runs ic_ref==ic32==golden (G12, native). If a locator cannot pin an
element (a parse-time reject before a graph exists), the span/object-id degrade
to None honestly. No new runtime constructs; regressions run5/6/8/9 all
PASS_REF_AND_NATIVE. **Next: 3B-4 named rotor constants + concise clocks
(`clock every 2` / `once at 5`; `rotor identity/quarter_turn_z/reverse_x`)
canonicalizing to the frozen numeric values.** Prior: **WRL PHASE 3B-2 PASS_REF_AND_NATIVE (5s, 10 checks L1–L10) — `wrl_format.py` (new, v0.1) + `wrl_canvas.py` (re-export) + `binding_run9.py` (new).**
GPT-5.6's 3B priority ruling leads broad 3B with "canonical formatter + source
spans" — 3B-1 shipped the span sidecar, 3B-2 is the formatter. **`format_wrl_core(graph)`
now lives in a first-class `wrl_format.py`** (the emitter was relocated from
`wrl_canvas.py`, which re-exports `graph_to_wrl_core` for back-compat). It renders
actual WRL Core process notation (`[role:name](k=v){ports}`, `[a] --tag--> [b]`,
`[epoch:N] @w,s Op args`) — NOT the bootstrap DSL — and **canonicalizes first**, so
formatting is a pure function of the semantic graph: declaration order, surface
choice, and source whitespace all wash out. Laws proven: `parse_wrl_core(format(g))
== g` (**L1**), `format(parse(format(src))) == format(src)` (**L2**, idempotent), a
formatting-only edit keeps the SemanticArtifactID (**L3**) AND CompilePlanDigest +
BackendArtifactID (**L4**). Bootstrap & core surfaces of one world format to the
IDENTICAL text (**L5**); the output parses back as real WRL Core with ports ==
the frozen registry and is rejected by the bootstrap parser (**L6**); a
declaration-order shuffle formats to identical text (**L7**); run inputs (claims)
survive format→parse (**L8**); 3B-1 spans over the formatted text resolve every
canonical object/edge (**L9**); and the formatted text runs ic_ref == ic32 ==
golden (**L10**, native). No new runtime constructs;
`wrl_ir.py`/`wrl_canonical.py`/`wrl_plan.py` untouched. Regressions clean:
`binding_run5`/`binding_run6` (which call `CV.graph_to_wrl_core`) + `binding_run7`
+ `binding_run8` all PASS_REF_AND_NATIVE. **3B-2 complete — next is 3B-3 stable
diagnostics (code + message + primary span + optional related span + canonical
object id), now that stable spans + canonical text exist.**


**WRL PHASE 3B-1 PASS_REF_AND_NATIVE (5s, 13 checks S1–S13) — `wrl_spans.py` (new, v0.1) + `binding_run8.py` (new).**
GPT-5.6's 3B priority ruling leads broad 3B with "canonical formatter + source
spans" — NOT concise clocks or named rotors first. 3B-1 is the span layer.
**Parsing now emits source information ALONGSIDE — but strictly OUTSIDE — the
semantic graph.** `SourceSpan{file_id, start_offset, end_offset, start_line,
start_column, end_line, end_column}` and `SourceOrigin{canonical_object_id,
construct_kind∈node|edge|claim|directive, span}` are collected into a read-only
`WrlSourceMap` keyed by canonical object_id / canonical edge key / claim key. The
authoritative canonical graph is still built by the UNTOUCHED
`parse_wrl_bootstrap`/`parse_wrl_core`; the span pass is an INDEPENDENT scan over
the same text, so capturing spans provably cannot perturb any identity —
`parse_bootstrap_with_spans`/`parse_core_with_spans` return `(graph, source_map)`
and `lower_*_with_spans` return `(LoweredProgram, source_map)` byte-identical to
the plain path (**S1**). A file_id change leaves SemanticArtifactID (**S2**),
CompilePlanDigest AND BackendArtifactID (**S3**) unchanged; reformatting the same
source (comments/blank lines/indent) moves spans but not the SemanticArtifactID
(**S4** — a taste of 3B-2). Every canonical IR object (**S5**) and edge (**S6**)
resolves to an origin span, and each span slice actually contains the token it
names (**S7**). The bridge **source span ↔ WrlGraph object/edge ↔ Forge IR
object/edge ↔ canvas element** holds by shared canonical key: bootstrap & core
surfaces yield the same sem id AND identical origin keys equal to the artifact's
object/edge keys (**S8**), and every canvas node/connection resolves to an origin
(**S9**). Reverse lookup `origin_at(offset)` inside a node span returns that node
(**S10** — the canvas-click/cursor primitive). The sidecar is immutable
(`WrlSourceMap` read-only; `SourceSpan`/`SourceOrigin` namedtuples) (**S11**), and
file_id + span fields never appear anywhere in the sealed artifact bytes
(**S12**). A spanned-lowered program still runs ic_ref == ic32 == golden
(**S13**, native). No new runtime constructs on the identity path;
`wrl_ir.py`/`wrl_canonical.py`/`wrl_plan.py`/`compiler.py`/`admit.py` untouched.
Regressions clean: `binding_run7` (D1–D36) PASS_REF_AND_NATIVE. **3B-1 complete —
next is 3B-2 `format_wrl_core(graph)` (the canonical formatter).**


**WRL PHASE 3D.1.1 PASS_REF_AND_NATIVE (34s, 36 checks D1–D36) — `wrl_canonical.py` (v0.5) + `wrl_plan.py` (v0.3) + `binding_run7.py` (v0.3).**
GPT-5.6 accepted the 3D.1 backend-policy architecture but found the sealed
wrappers were NOT fully closed — two concrete implementation holes: (1)
`SealedArtifact` exposed writable `artifact`/`semantic_id` slots and `.artifact`
returned the STORED dict, so a caller could mutate the sealed body while
`semantic_artifact_id` still trusted the stale stored id; (2) `compile_sealed_plan`
accepted any duck-typed object and did not reseal, so a counterfeit wrapper
carrying a fabricated semantic id compiled into a BackendArtifactID. **Fix — seal
CANONICAL BYTES, not a mutable dict.** `SealedArtifact` now stores
`_canonical_bytes` + a constructor-derived `_semantic_id`; `.artifact` deserializes
a FRESH copy every read; the object blocks all attribute assignment/deletion with
a typed `WRL_SEALED_IMMUTABLE`; and `semantic_artifact_id(sealed)` recomputes from
the bytes rather than trusting a field (**D28/D29/D30/D35**). `SealedCompilePlanV1`
likewise stores `_canonical_bytes` with read-only `canonical_plan`
(deserialize-fresh) / `semantic_artifact_id` / `compile_plan_digest` properties and
the same immutability barrier (**D31/D32**). **Tightened compile boundary:**
`compile_sealed_plan` now rejects anything that is not EXACTLY a
`SealedCompilePlanV1` (**D33**) and re-verifies the seal's own integrity from its
canonical bytes — the bytes must still hash to the claimed CompilePlanDigest AND
the plan reconstructed from them must still re-hash to the claimed
SemanticArtifactID, so tampered bytes fail at compile rather than silently
compiling a counterfeit id (**D34**). Same sealed bytes reproduce identical ids +
backend content (**D36**). New error code `WRL_SEALED_IMMUTABLE`; no new runtime
constructs; `admit.py`/`fixture.py`/`compiler.py` semantics untouched. Regressions
clean: `binding_run3o`/`binding_run4`/`binding_run5`/`binding_run6` all
PASS_REF_AND_NATIVE. **3D.1.1 complete — 3B ergonomics (formatter + source spans
first, per GPT-5.6's ruling) is now unblocked.**


**WRL PHASE 3D.1 PASS_REF_AND_NATIVE (37s, 27 checks D1–D27) — `lowering_policy.py` (new) + `wrl_plan.py` (v0.2) + `wrl_canonical.py` (v0.4) + `fixture.py` + `compiler.py` (annotation-only) + `binding_run5.py` + `binding_run7.py` (v0.2).**
GPT-5.6 accepted the 3D architecture but blocked 3B on four Backend-Identity gaps.
**(A — operative profile)** `LoweringProfileV1` now carries `counter_encoding`
(`auto|one_hot|binary`) + a positive int `onehot_max`; `validate_lowering_profile_v1`
enforces the domain, and the profile-aware `_PlanView(plan, profile)` drives the
compiler's `counter_spec` through the shared `lowering_policy.counter_spec_for`,
so forcing one-hot vs binary emits DIFFERENT backend terms but IDENTICAL films
(**D16/D17**). **(B — representation-neutral plan)** the three CompilePlanV1
signatures now fingerprint the SEMANTIC counter SHAPE (the clock), never
onehot/binp/width; the representation-full fingerprint became a COMPILE-time
`backend_layout_signature` + an alpha-canonicalized `backend_content_hash`, both on
the new `CompiledProgram(sealed_plan, backend_artifact_id, backend_layout_signature,
backend_content_hash, ic_term, fields)` — never in the plan. A profile change moves
neither the CompilePlanDigest (**D18**) nor the SemanticArtifactID but does move the
BackendArtifactID + backend fingerprints (**D19/D20**). **(C — seal + bind)**
`SealedCompilePlanV1` + `seal_compile_plan` recompute the three neutral signatures
(**D23**), reconstruct the Forge IR from the plan via `_plan_to_artifact` and
re-hash it to prove the plan is BOUND to its SemanticArtifactID (**D22** — catches
a rotor-lane tamper that lives BELOW every signature), verify exact key set +
object_order sort + object_index bijection (**D24**), and store an isolated deep
copy so mutating a returned sealed plan cannot affect it (**D21**); production
`compile_artifact` requires a `SealedArtifact` and compiles ONLY the sealed plan.
**(D — no Fixture on the compile path)** `ONEHOT_MAX` moved from `fixture.py` into
`lowering_policy` (fixture re-exports it), and `compiler.py`'s stale decorative
`from fixture import Fixture` (used only as a now-wrong type annotation on
`compile_step`/`compile_step_v6`, which actually accept the duck-typed `_PlanView`)
was removed — so the whole production lower+seal+COMPILE path imports NO Fixture
module (**D25**, subprocess probe). Same artifact+profile reproduce identical
backend bytes/hash/layout id (**D26**); the retained Fixture oracle and the
production sealed-plan path stay film-identical every epoch (**D27**). D9 renamed
(behavioral parity, not literal term identity). Regressions clean:
`binding_run3o`/`binding_run4`/`binding_run5`/`binding_run6` all PASS_REF_AND_NATIVE.
`admit.py` / `fixture.py` semantics untouched; no new runtime constructs. **3D.1
complete — 3B ergonomics is now unblocked.**


**WRL PHASE 3D PASS_REF_AND_NATIVE (31s, 15 checks D1–D15) — `wrl_plan.py` (new) + `wrl_ir.py` + `wrl_canvas.py` + `binding_run6.py` + `binding_run7.py` (new).**
GPT-5.6 ordered a deterministic **CompilePlanV1** extracted between the frozen
Forge IR and the existing backend, so both the sealed IR and the legacy Fixture
converge on ONE plan; then remove Fixture construction from `lower_graph`,
keeping the Fixture only as an independent test oracle. **(3D-0)** semantic
strictness first: `validate_canvas_v1` rejects unknown canvas/node/connection
SEMANTIC keys (presentation stays open + inert) and `_coerce_cfg` rejects
unknown `static_config` fields per role (`_CFG_KEYS`) — both typed
`WRL_UNSUPPORTED_FEATURE`. **(3D-1)** `wrl_plan.py` adds **CompilePlanV1** — a
validated, JSON-plain, backend-neutral preparation (18 GPT-5.6 fields +
`compile_plan_version`); it carries NO Scott encoding, DUP labels, generated
variable names, tuple nesting, one-hot/binary counter representation, native
offsets, or CUDA layouts. `_PlanView` duck-types the small structural read
interface the compiler already consumes (layout/orbs/pulsers/spinners/
counter_spec/wires/controller_of/orb_of/is_configurable/kinds/wire_role), so
`compile_plan_to_ic(plan) = compile_step_v6(_PlanView(plan))` reuses the
existing compiler UNCHANGED — no parallel compiler. A single builder
`_plan_from_parts` (sorted/canonical throughout) is called by BOTH
`artifact_to_compile_plan_v1` and `fixture_to_compile_plan_v1`, so the two
entry points emit byte-identical plans. **(3D-2)** `compile_artifact` /
`compile_program` return a `CompiledProgram` (plan, ic_term, fields,
BackendArtifactID); the representation threshold (`ONEHOT_MAX`) stays inside the
shim, not the plan. **(3D-3)** `lower_graph` no longer builds a Fixture:
`LoweredProgram` now carries `sealed_artifact / semantic_artifact_id /
initial_claim_state / run_plan / epoch_inputs / canonical_graph`; the Fixture is
reachable only via the lazy `as_fixture_for_test()` (imports `Fixture` inside the
function). D1 plan(IR)==plan(Fixture) byte-identical over 6 structural worlds;
D2 reorder-equivalent artifact → identical plan; D3 JSON round-trip → identical
digest; D4 bootstrap/text/canvas → identical plan; D5 plan-view init state ==
Fixture init state; **D6/D8** native-gated plan-fed epoch trajectory + step ==
**ic_ref == ic32 == golden**; D7 plan-view Film v0.7 == Fixture Film every epoch;
D9 plan-fed and Fixture-fed compiled steps are the SAME function over randomized
reachable states (native on core); D10 unknown canvas key AND unknown
static_config field are typed rejects; D11 presentation-only edit moves NEITHER
plan digest NOR BackendArtifactID; D12 semantic edit moves BOTH; D13
lowering-profile change preserves SemanticArtifactID, moves BackendArtifactID;
D14 a subprocess probe proves production lowering imports NO Fixture and NO
compiler; D15 the retained Fixture oracle still folds to the golden trajectory
(native). Regressions clean: `binding_run3o` (golden fold), `binding_run4`
(slice 1), `binding_run5` (slice 2.1), `binding_run6` (3C) all
PASS_REF_AND_NATIVE. `admit.py` / `compiler.py` / `fixture.py` untouched; no new
runtime constructs. **Fixture is retired as the production lowering contract
(CompilePlanV1 replaces it) and retained as an independent test-builder/oracle —
NOT deleted.** Next per ruling: 3B ergonomic surface widening, then the first
visible Forge demo.

# Forge Binding Results v0.25 — WRL Phase 3C (canvas↔text↔runtime isomorphism) + 3C-0 sealing preflight + WRL slice 2.1 (sealing + lexical errata) + WRL slice 2 (Canonical Identity spine) + WRL slice 1 (WRL Core → Forge Semantic IR v1 → Fixture → TRVM → Film v0.7) + 3b.5f-2b BUILD/MEASURE + 3b.5f-2a BUILD/MEASURE + 3b.5f-1 (golden ADMIT + Film v0.7 + two golden repairs)

**WRL PHASE 3C PASS_REF_AND_NATIVE (8s, 12 checks V1–V12) — `wrl_canvas.py` + `binding_run6.py`; 3C-0 preflight folded into `binding_run5.py` (now 20 checks C1–C20).**
GPT-5.6 approved Phase 3C with a mandatory identity preflight. **(3C-0)** canonical
artifact SEALING is now the identity path: `canonicalize_artifact_v1` normalizes a
valid-shaped artifact (objects by `(object_id, role)`, edges by `(kind, src, dst)`,
`numeric_policy_ids` and each port array sorted; rotor lanes/clock stay POSITIONAL),
and `_seal` = validate → canonicalize → re-validate → serialize. `SealedArtifact`
carries a fresh ISOLATED canonical copy, so caller mutation after sealing cannot
change an issued identity; `semantic_artifact_id` routes through `_seal`. The
backend identity domain is strict: `validate_semantic_id` requires `sem-<64 lowercase
hex>` and `validate_lowering_profile_v1` requires `encoding ∈ {one_hot, binary}` +
the pinned `lowering_profile_version`, else `WRL_BAD_LOWERING_PROFILE`. New **C19**
reorder-equivalent artifacts (reversed objects/edges, reordered policy ids, JSON
round-trip) seal to identical bytes + SemanticArtifactID and the sealed value is
isolated from caller mutation; **C20** malformed/short/uppercase-hex sem ids, unknown
encodings, and unsupported profile versions are all `WRL_BAD_LOWERING_PROFILE`.
**(3C-1)** `wrl_canvas.py` adds CanvasGraphV1 — presentation metadata AROUND, not
inside, the canonical WRL graph. Each node/connection keeps SEMANTIC fields at top
level (object_id/role/static_config; kind/src/dst) and a separate `presentation`
block (x/y/width/height/color/label_style/collapsed/layer; control_points/
line_length/texture_style/paint/label_position). Ports are NOT stored — they derive
from the frozen role registry. `graph_to_canvas` / `canvas_to_graph` /
`graph_to_wrl_core` / `lower_canvas` convert; `canvas_to_graph` reads ONLY semantic
keys, so presentation is structurally unreachable from the lowering path. All three
surfaces share the new `wrl_ir.lower_graph` seam. **(3C-2/3/4)** `binding_run6.py`
proves V1 text→graph→canvas→graph retains the id (bytes + batches); V2
canvas→graph→WRL text→graph retains it; V3 move / V4 line geometry / V5 recolor do
NOT change it; V6 rotor / V7 reconnect DO; V8 duplicate Orb controller in the canvas
→ `WRL_CONTROLLER_CONFLICT`; V9 canvas derives / text checks the SAME frozen port
signature and a corrupted/deleted presentation cannot override the identity; V10
bootstrap / WRL text / canvas lower to IDENTICAL bytes; V11 every presented node is
anchored to a real object id; V12 native-gated **ic_ref == ic32 == golden** over the
whole trajectory lowered FROM A CANVAS. Regressions clean: slice-2.1 (`binding_run5`,
now C1–C20) and slice-1 (`binding_run4`) PASS_REF_AND_NATIVE; golden `binding_run3o`
unaffected (`admit.py` untouched). No new runtime constructs; the Fixture adapter is
kept through 3C. Next per ruling: 3D direct IR→backend (retire the adapter), then 3B
ergonomic surface widening.

**WRL SLICE 2.1 PASS_REF_AND_NATIVE (6s, 18 checks C1–C18) — `wrl_canonical.py` + `wrl_ir.py` + `binding_run5.py`.**
GPT-5.6 accepted Slice 2 provisionally and ordered a sealing/lexical errata
before Phase 3C. Closed three identity holes plus three tightenings. **(E1)**
`rulepack_id` is no longer `None` — it names the transition law
`forge.world.core.rules.v1`; new `seal_artifact` → `SealedArtifact` and
`validate_artifact_v1` reject null/empty policy ids (`WRL_UNSEALED_POLICY`),
unknown schema blocks, unsupported ir/profile versions, and malformed
object/edge records; `semantic_artifact_id` now VALIDATES before hashing, so an
unsealed policy can never earn an identity. **(E2)** a WRL `{ports}` brace group
is a CHECKED projection of the role's frozen ports — `validate_port_projection`
rejects `{bogus}`/`{}` with `WRL_PORT_SIGNATURE`; visible source is never
silently ignored, and the honest projection lowers identically to the
registry-derived ports. **(E3)** `parse_wrl_core` obeys WRL's lexical law: `;`
comments (full-line + inline) and `#` is preserved for content identity/tags
(never a comment marker); the bootstrap DSL keeps `#` comments for now. **(E4)**
objects are canonicalized IDENTITY-FIRST by `(object_id, role)` — stable if the
role registry expands. **(E5)** `validate_lowering_profile_v1` requires
encoding/numeric_backend/compiler_hash/target/lowering_profile_version, so a
half-specified backend cannot earn a `BackendArtifactID`
(`WRL_BAD_LOWERING_PROFILE`); `backend_artifact_id` validates before hashing.
**(E6)** `LoweredProgram.initial_state` → `initial_claim_state`: a partial claim
projection is no longer misnamed the full initial runtime state. New checks
**C13** unsealed rulepack → `WRL_UNSEALED_POLICY`; **C14** a different
`rulepack_id` moves the SemanticArtifactID; **C15** bogus/empty `{ports}` →
`WRL_PORT_SIGNATURE`, honest projection lowers identically; **C16** `;` comments
obeyed and `#` preserved; **C17** half-specified lowering profile →
`WRL_BAD_LOWERING_PROFILE`; **C18** objects in identity-first order. C1–C12
unchanged and still green (C12 native-gated **ic_ref == ic32 == golden**).
slice-1 (`binding_run4`) and golden `binding_run3o` regressions stay
PASS_REF_AND_NATIVE. No new runtime constructs. Next per ruling: Phase 3C
canvas↔text isomorphism (keep the Fixture adapter through it).

**WRL SLICE 2 PASS_REF_AND_NATIVE (8s, 12 checks C1–C12) — `wrl_canonical.py` + `binding_run5.py`.**
GPT-5.6 Ruling B: freeze the identity spine before widening WRL features.
Delivered the five ruled fixes and proved them: **(F1)** the STATIC semantic
artifact is separated from run inputs — `lower_program` returns a
`LoweredProgram{artifact, initial_state, run_plan, epoch_inputs, fixture,
graph}`; `graph_to_ir` no longer emits `periods`/`batches` (D3). **(F2)**
`wrl_canonical.py` is the single source of the frozen registries plus
`validate_graph` / `canonicalize_graph` / `serialize_artifact` (deterministic
sorted-key bytes) / `semantic_artifact_id` (`sem-…`) / `backend_artifact_id`
(`bknd-…`); the SemanticArtifactID is a pure function of the frozen semantic
graph (objects+static_config, structural edges, semantic policy ids) and the
BackendArtifactID folds in the lowering profile (encoding, numeric backend,
compiler hash, target). **(F3)** two surfaces — `parse_wrl_bootstrap` (the
line DSL) and `parse_wrl_core` (WRL process notation
`[pulser:p0](mode=periodic, period=2, phase=0){sig_out}` /
`[p0] --sig--> [sp]`) — lower to IDENTICAL canonical bytes and run inputs.
**(F4)** typed structural validation with stable codes
(`WRL_DUPLICATE_ID`, `WRL_UNKNOWN_ENDPOINT`, `WRL_ILLEGAL_PORT_PAIR`,
`WRL_CONTROLLER_CONFLICT`, `WRL_CLOCK_RANGE`, `WRL_NUMERIC_RANGE`,
`WRL_EPOCH_RANGE`, `WRL_UNSUPPORTED_FEATURE`) — the IR validator owns them, not
the Fixture ctor (`WrlValidationError(WrlUnsupported)` keeps `except
WrlUnsupported` working). **(F5)** the rejected-claim Film v0.7 projection gap
is closed: an out-of-fixture target name is non-authoritative diagnostic
metadata, so `film_bytes_v7` renders it as the canonical sentinel `#?` on BOTH
the golden side (literal `zz`) and the lossy projection (`?`) — full 3-epoch
film parity now holds. Checks: **C1** two declaration orders → identical
SemanticArtifactID; **C2** bootstrap == process-notation (bytes + run inputs);
**C3** claim batches do NOT affect the SemanticArtifactID; **C4** a different
initial rotor DOES; **C5** a different numeric policy DOES; **C6** one-hot vs
binary keeps the SemanticArtifactID, moves the BackendArtifactID; **C7** a
different compiler identity moves the BackendArtifactID; **C8/C9** duplicate id
and illegal port pair are typed rejections; **C10** ALL 3 epochs (incl. the
rejected invalid-target claim) have full Film v0.7 parity; **C11** the
canonical artifact round-trips through serialization; **C12** **ic_ref == ic32
== golden** over the whole WRL-lowered trajectory (native-gated). No new
runtime constructs were added — the spine is green. `admit.py` gained the
fixture-aware `_payload_str` sentinel; slice-1 (`binding_run4`) and the golden
`binding_run3o` regressions stay PASS_REF_AND_NATIVE.

**WRL SLICE 1 PASS_REF_AND_NATIVE (6s, 4 cases W1–W4) — `wrl_ir.py` + `binding_run4.py`.**
The first sanctioned WRL lowering, end to end on the grounded
deterministic-circuit-world (GPT-5.6 ruling: freeze Forge Semantic IR v1 as
profile `forge.world.core.v1`, then implement one vertical slice). Pipeline:
**WRL Core text → canonical WRL graph → ForgeSemanticArtifactV1 → current
Fixture adapter → TRVM `compile_step_v6` + ADMIT reducer → ic_ref/ic32 → Film
v0.7.** `wrl_ir.py`: a minimal restricted WRL surface parser (5 built-in roles
Pulser/Relay/Door/Spinner/Orb, 2 structural edges SignalWire/SocketControl,
fixed-point rotor decls, SetRotor/ResetFault, N periods), `graph_to_ir`
(frozen top-level form + role/edge-registry closure), `ir_to_fixture` (the
adapter; static artifact only — EpochInput threaded separately, D3), and
`WrlUnsupported` diagnostics for everything out of scope. Cases: **W1** WRL
text → IR v1 → Fixture reproduces hand-built `mkfx(8,4)` EXACTLY
(pulsers/doors/edges/spinners/orbs/sockets); **W2** emitted artifact carries
the frozen shape (profile, 5-role + 2-edge closure, `admit_candidate_min_firstreceipt_v1`
pinned, NO backend encoding — D4 semantic/backend split); **W3** the SAME WRL
program folds over K=3 epochs in ONE IC term whose single native normalization
renders the IDENTICAL Film v0.7 trajectory as golden `admit_step`+world-step
(**ic_ref == ic32 == golden**, reusing the 3b.5f-2b `binding_run3o` fold since
the adapter fixture == `binding_run3o.FX`; valid-target epochs 1–2 for film
parity per the run3n/run3o projection-limit discipline); **W4** async `~~`
route, capability `gate`, `seal`, a sixth role, and an out-of-registry edge
each raise a clear `WrlUnsupported` — NEVER a speculative lowering. Frozen
specs (TRVM-root, not the forge E2 bundle): `FORGE_SEMANTIC_IR_v1.md`
(profile `forge.world.core.v1`; node envelope + 5 roles; 2 edges; static policy
refs; top-level runtime ClaimState; separate EpochInput; semantic signatures
with Semantic/Backend artifact-ID split; v1.1 additive / v2 semantic) and
`WRL_CORE_0.1.md` rev **0.1.1** errata (cycle OBSERVE→ACCEPT→MAP→COMMIT→REACT→FILM;
narrowed conflicts-dissolve; policy-pinned canonical key; WorldFrame/EventLedger/BuildFilm;
corrected grounding table).

**SLICE 3b.5f-2b BUILD (FOLD) PASS_REF_AND_NATIVE (34s, 5 cases) —
`admit_ic.py` (`ic_reduce` made linear in `rv`) + `binding_run3o.py`.** The
single-epoch reducer (3b.5f-2a) is folded over K epochs into ONE
interaction-calculus term that threads BOTH the persistent ClaimState (fact
vector + receipt vector) AND the WorldState (v0.6 encoded physical state) across
epochs, gated by a SINGLE native normalization producing the WHOLE trajectory
(one `native()` call yields every epoch's world + claim state). Per epoch e:
`red_e = ic_reduce(fv_e, rv_e, batch_srcs[e])` → `world_{e+1} =
((compile_step_v6 EC) world_e)` — the reducer's emitted `EpochControl` is fed
DIRECTLY into `compile_step_v6` (3b.5f-2b MEASURE proved it equals golden
`enc_config_bundle`). Each epoch emits `(world', fv', rv', fobs, facc)`; the K
epochs are a flat `TUP(5·K)` in ONE term, decoded via `_spine(nf, 5·K)`.

**Two load-bearing IC facts pinned here.** (1) **Linearity fix:** `ic_reduce`
reads its receipt input in BOTH `ic_accept` and `ic_map`, so it now binds
`rv_in_src` once and `!&`-dups it — the reducer is linear in `rv` and thus
composable when `rv` is a bound variable from the previous epoch (a literal
still works; all 3b.5f-2a cases re-pass native). (2) **This IC grammar has NO
parenthesized-single-term rule:** `(X)` is ALWAYS an application `(f a)`; to
apply a lambda whose body is bounded, write `(λx.BODY arg)` NOT `((λx.BODY) arg)`
(the latter parses `(λx.BODY)` as an app with a missing operand).

Battery (all native-gated): **O1** three-epoch persistence (rotor → rotor+reset
→ invalid-NoChange; facts accumulate [1,3,4], receipts first-authoritative, the
physical world evolves and the pre-existing `fault_ob` is reset in epoch 2);
**O2** two-epoch canonical (epoch-1 later-canonical rotor `(16,0,99,0)` commits,
epoch-2 reset); **O3 arrival-order independence (O2 epoch-1 batch reversed →
IDENTICAL trajectory) — PERMANENT REGRESSION**; **O4** first-receipt
authoritative ACROSS epochs ((1,1) receipted in epoch 1 keeps its `0xf6` digest,
NOT remapped by a re-claim in epoch 2; fresh (2,2) reset applies); **O5 Film
v0.7 trajectory parity** — every epoch's fold projection renders the IDENTICAL
v0.7 film (physical + claim + receipt-with-epoch) as the golden `admit_step` +
world-step trajectory. **Receipt `accepted_epoch` is NOT carried in the IC
receipt vector** (a receipt is identified by its CandidateKey; epoch is
provenance) — the projection recovers it faithfully as the epoch of a receipt's
FIRST appearance in the trajectory, which is exactly the epoch `admit_step`
accepted it. **One honest projection limit:** a REJECTED SetRotor at an INVALID
target keeps only its packed CandidateKey (`kind|idx`) in the fact vector — the
original target NAME is not carried (idx has no spinner ⇒ renders `?`), so O5
asserts Film parity over VALID-target trajectories (same discipline as
`binding_run3n` R9); the fact/receipt/world TRAJECTORY is nonetheless exact and
O1 exercises the invalid→NoChange world case in full.

---

**SLICE 3b.5f-2b MEASURE (BRIDGE) PASS_REF_AND_NATIVE (4 cases) — `admit_ic.py`
+ `compiler.py` (`compile_step_v6`, `enc_config_bundle`).** Measure-before-
building for the world wiring: the reducer's emitted `EpochControl` (field 2 of
the `TUP5`, projected via `λa.λb.λc.λd.λe.c`), fed DIRECTLY into
`compile_step_v6`, drives the v0.6 world state IDENTICALLY to the golden
`enc_config_bundle` EC — `dec_state_v6` equal, ref == native — over
setrotor+reset, setrotor-only, reset-only, and invalid→NoChange (with a
pre-existing `fault_ob=1` reset). Confirms `ic_map`'s `rotor_cfg` matches
`enc_rotor_config` exactly and `_PAIR(rotor_bundle, fault_bundle)` ==
`enc_config_bundle` for `mkfx(8,4)`, so the reducer EC is directly consumable by
the step function. This licensed the 3b.5f-2b fold.

---

**SLICE 3b.5f-2a BUILD (REDUCER) PASS_REF_AND_NATIVE (11s, 9 cases) —
`admit_ic.py` (`ic_insert_sorted`, `ic_observe`, `ic_accept`, `ic_map`,
`ic_reduce`) + `binding_run3n.py`.** The single-epoch ADMIT reducer is now
composed as ONE interaction-calculus term and gated by a SINGLE native
normalization per case (`ic_ref == ic32 == golden`). `ic_reduce` threads
facts + receipts through all three phases —
`ic_observe` (atomic compare-shift insert + distinct-new count + capacity
gate + dedup) → `ic_accept` (per-event-group MIN via sorted order, first
receipt authoritative, atomic receipt gate) → `ic_map` (newly-accepted
Applied ops → `EpochControl = TUP(rotor_bundle, fault_bundle)`) — over
**Option A occupied-prefix sorted structural vectors** (empty slots = ALL-ONES
key, sinks to bottom, present DERIVED). The load-bearing composition insight:
**ACCEPT and MAP both read the PRE-accept receipt vector** (facts are monotone,
so the post-OBSERVE fact vector `fv'` feeds ACCEPT, MAP, and the output, dup'd
three ways; `rv_in` is pure data, inlined into both). Output is
`TUP5(fact_vec', receipt_vec', EpochControl, fact_capacity_fault,
receipt_capacity_fault)`.

Battery (all native-gated): R1 SetRotor+ResetFault → EC + facts + receipts;
R2 later-canonical-wins (canonically-later rotor committed); **R3 arrival-order
independence (R2 reversed → identical output) — PERMANENT REGRESSION**; R4
first-receipt authoritative (pre-receipted event not remapped, fresh event in
same batch still applies); R5 invalid target → Rejected → NoChange; **R6
collision 0xf6 (two payloads, one reduced digest, DISTINCT fkeys) → OBSERVE
keeps BOTH facts (disputed), ACCEPT/MAP pick the min-ckey group leader —
Correction 1 through the whole reducer**; R7 fact-capacity overflow (batch
that does not fit latches `fact_capacity_fault`, inserts NONE, NoChange);
**R8 fact-overflow reversed batch → identical reject verdict — PERMANENT
REGRESSION**; R9 **Film v0.7 parity** — the reducer output, projected to a
reconstructed claim state, renders the IDENTICAL v0.7 film as the golden
`admit_step` state (valid fresh cases). **Receipt-capacity fault is
structurally UNREACHABLE in the composed single-epoch reducer** (MAX_EVENTS ==
MAX_FACTS == 6, facts monotone, ≥1 fact/event ⇒ needed = events − R ≤ 6 − R =
remaining); its mechanism stays gated at the `ic_accept` unit level
(`binding_run3m` B5, 7 event keys). **3b.5f-2b (above) now wires the reducer's
emitted `EpochControl` through `compile_step_v6` into the v0.6 world and folds
the persistent claim/world state over K epochs as one native trajectory.**

---

**SLICE 3b.5f-2a MEASURE PASS_REF_AND_NATIVE (0s, 6 cases) — `admit_ic.py` +
`binding_run3l.py`.** Measure-before-building for the IC lowering: the golden
reducer decides everything downstream from two key comparisons (`min
CandidateKey` for acceptance, key `==` for set distinctness) plus one scalar
(`occ+nnew ≤ cap`, atomic capacity). This sub-slice lowers exactly those three
onto the calculus over the **packed-key representation** — the one
representation choice the ruling left to me: pack each key as ONE fixed-width
unsigned integer, fields MSB→LSB in the SAME order the golden tuple compares
them (`ckey = digest|kind|idx|r0|r1|r2|r3`, 44b; `fkey = writer|seq|ckey`, 52b),
**measured order- and equality-faithful vs the golden Python tuple comparison
(324/324 payload pairs, incl. the 0xf6 collision pair)**. Then `min CandidateKey`
= unsigned `ic_min2(CKEY_W)` (ltu→mux) and distinctness = `dyn_case("eq")`, both
native-gated: M1 candidate-min == golden min (24 pairs); M2 collision 0xf6 packs
DISTINCT, min picks the smaller pkey; M3 fact-key `==` == golden set identity;
M4 recognition via IC eq (distinct→disputed, retransmit→unambiguous); M5 atomic
capacity `fits == (occ+nnew≤6)`; M6 overflow verdict order-independent. Both
golden-repair witnesses are now **pure-term** regressions. BUILD (assembly)
remaining for 3b.5f-2a: occupied-prefix sorted fact/receipt vectors, OBSERVE
compare-shift insert, per-event-group min, MAP → EpochControl, single reducer
native gate through `compile_step_v6`.

---

**SLICE 3b.5f-1 PASS_REF_AND_NATIVE (10s, 16 cases).** The bounded, typed,
prehashed ADMIT semantic core, pinned as a Python golden. The key insight:
**ADMIT is a claim-state reducer that PRODUCES the EpochControl the v0.6 world
already consumes** — the world effect (COMMIT+REACT: rotor/pose/fault) is
already proven, so the whole new surface is
`observed claim batch + persistent ClaimState → EpochControl`. Raw wrt
ACCEPTANCE (the reducer receives UNACCEPTED claims and decides recognition /
acceptance / effect) but NOT raw wrt crypto parsing (claims arrive as canonical
typed PREHASHED envelopes; **no pure-term SHA-256** this slice).

## Two golden repairs GPT-5.6 required before the 3b.5f-2 IC lowering

Both are now permanent battery regressions. GPT-5.6 also ruled the container:
**Option A — occupied-prefix sorted structural vectors** for facts and receipts
(canonical Film order + adjacent equivocations + deterministic scans, free; a
credible bounded sorted-union path). Policy renamed
`admit_digestmin_firstreceipt_v1` → **`admit_candidate_min_firstreceipt_v1`**
because acceptance now orders a full candidate, not just a digest.

- **Correction 1 — reduced-digest collisions are semantically visible.** WD=8
  collides: `SetRotor("sp",(16,0,10,0))` and `SetRotor("sp",(16,1,5,0))` share
  digest **0xf6** (the battery's search rediscovers exactly 0xf6). A digest-only
  identity collapses two distinct payloads into one fact → wrongly
  `unambiguous`, one payload lost, receipt can't name the accepted one. FIX: a
  COMPLETE candidate key with an injective fixture-scoped `payload_key`
  (`SetRotor→(0,spinner_index,r0..r3)`, `ResetFault→(1,orb_index,0,0,0,0)` —
  collision-free by construction). `CandidateKey=(digest,payload_key)`;
  `ClaimFactKey=(writer,seq,digest,payload_key)`; same-batch acceptance = **MIN
  CandidateKey** (digest-min stays primary, payload_key is the tie-break);
  receipts store the full accepted candidate; **recognition counts distinct
  candidate keys** (a collision still reads `disputed`).
- **Correction 2 — capacity exhaustion must be arrival-order independent.** An
  insert-until-full loop kept different facts when the same overflowing batch
  was reversed. FIX: OBSERVE/ACCEPT are **ATOMIC per epoch batch** —
  canonicalize+dedup the batch, drop already-present, sort by ClaimFactKey; if
  the new facts don't ALL fit, latch **`fact_capacity_fault`**, insert NONE,
  create no receipts/effects. The same atomic law governs receipts
  (**`receipt_capacity_fault`**, separate flag; combined `capacity_fault`
  derived for presentation). Never evict, never partially apply. Caps are proof
  parameters (`MAX_FACTS=MAX_EVENTS=6`, added **`MAX_BATCH=4`**), not language
  limits. NB: Option A prepares SET-UNION merge but is NOT yet a full bounded
  CRDT — `unique(left∪right) > MAX_FACTS` is a future distributed-slice choice.

## The model (bounded, canonical, monotone)

- **Payload** `SetRotor(spinner, rotor4) | ResetFault(orb)`; `pdigest` = a
  reduced-width (WD=8) canonical id, a pure function of the canonical payload
  string ⇒ recognition is **arrival-order independent by construction**.
- **ClaimFact** `{event_key:(writer,seq), digest, payload_key, payload}` — a
  bounded canonical SET distinct by **ClaimFactKey `(writer,seq,digest,
  payload_key)`** (Correction 1); equivocation (incl. digest collisions) is ≥2
  facts under one event_key. **Recognition is DERIVED** from distinct candidate
  keys (0→unknown, 1→unambiguous, 2+→disputed), never stored.
- **AcceptanceReceipt** `{event_key, accepted_digest, accepted_payload_key,
  accepted_epoch, outcome}` kept **SEPARATE** from facts
  (`outcome = Applied | Rejected(reason)`); one immutable receipt per event_key,
  **first receipt authoritative**.
- **ClaimState** `{facts[≤MAX_FACTS], receipts[≤MAX_EVENTS],
  fact_capacity_fault, receipt_capacity_fault}`. On exhaustion **never evict /
  never partially apply** (atomic per batch); combined `capacity_fault` derived.

## Acceptance policy `admit_candidate_min_firstreceipt_v1`

Same-batch same event-key multiple distinct payloads → accepted = **MIN
CandidateKey `(digest, payload_key)`** (**order-independent**, collision-safe).
Cross-batch with an existing receipt → keep it; a later conflicting claim joins
the observed set and flips recognition to **disputed** but **never
undoes/retries** the earlier effect. Distinct events apply in
`(sequence, writer, digest, payload_key)` order; two accepted events writing the
same rotor the same epoch → the **later canonical event's** write is committed.
Phases: **OBSERVE → ACCEPT → MAP → [COMMIT+REACT in the v0.6 world] → HASH/FILM**.

- `admit.py` — golden reducer (`admit_step`) + **Film v0.7** (`film_bytes_v7`
  extends v0.6 with `acceptance_policy_id`, both capacity faults, the claim fact
  set with `payload_key`, receipts + accepted candidate + outcomes, derived
  recognition).
- `binding_run3k.py` — **16-case battery**: new unambiguous claim; accepted
  retransmission; same-batch equivocation (candidate-min, host-order
  independent); cross-batch equivocation (first receipt kept); conflicting
  retransmission (monotone set unchanged); recognition convergence (3 arrival
  patterns → same candidates); acceptance separation (two logs retain different
  receipts); later conflict no rollback (committed rotor survives dispute);
  rejected accepted op (Rejected receipt persists, retransmit no retry); two
  distinct rotor events (canonical-last wins); reset claim (Ruling-1 semantics
  via ADMIT); reset+overflow (current overflow relatches); **digest collision
  witness** (Correction 1 — shared digest 0xf6, distinct payloads stay disputed,
  candidate-min pkey wins); **fact capacity atomic + reversed** (Correction 2 —
  overflowing batch rejected whole, reversed == forward, no evict/partial);
  **receipt capacity atomic** (no receipts/controls from an over-capacity accept
  batch, facts kept); **Law 6 witness** (World A no receipt vs World B receipt
  for E → Film v0.7 already differs BEFORE E retransmitted → divergent effect
  licensed). World effect runs through the already-proven `compile_step_v6`; a
  representative native gate confirms `ic_ref == ic32` on the produced controls.

**DEFERRED to 3b.5f-2 (IC lowering):** the persistent in-calculus claim-log
fold and the FULL native gate on a **Scott-encoded bounded sorted claim SET +
receipts** (the hard part — pure-term OBSERVE/ACCEPT/MAP). **DEFERRED further:**
SHA-256 in terms, unbounded maps, STAMP/DELETE, dynamic sockets, claim
replication, receipt merging, rollback, sequencer, signatures. First distributed
rule stays: claim facts merge by **SET UNION**; receipts do **not** blindly merge.

---

# Forge Binding Results v0.17 — fault-reset op executed (GPT-5.6 ruling 1): separate per-orb fault control

**FAULT-RESET PASS_REF_AND_NATIVE (28s).** Per GPT-5.6's ruling, numeric-fault
reset is a **separate per-orb control input**, not part of `RotorConfigInput`:
rotor config targets a **Spinner**, numeric fault belongs to the controlled
**Orb** (it may outlive/lose/change its controller). The v0.6 EpochControl is
now `TUP(rotor_bundle, fault_bundle)`; `fault_bundle` is one
`KeepFault(F) | ResetFault(T)` flag per orb. A **global reset** is user-facing
syntax that **expands to a set of per-orb ResetFault flags** — not a canonical
primitive.

## The safety ordering (COMMIT clears, then REACT ORs)

`ADMIT accepted controls → COMMIT rotor writes AND fault resets → REACT →
latch current arithmetic overflow`. Per orb:
`fault_base = 0 if ResetFault else old_fault; new_fault = fault_base OR
current_epoch_overflow`. So **a reset can never conceal a fault generated in
the same epoch**: reset+overflow → fault stays 1; reset+clean/idle → clears.

- `compiler.py`: `enc_config_bundle(fx, cfgs, resets=None)` now emits the
  EpochControl pair (default `resets=None` → all KeepFault, so slices 3b.5d-2
  and 3b.5e are behavior-identical and stay green ref+native). `compile_step_v6`
  destructures `(ec λrb.λfb.…)`, computes `fault_base = ((reset F) old_fault)`,
  and folds this epoch's overflow into `fault_base` (not `old_fault`).
- `binding_run3j.py` — 8-case battery: (1) idle reset clears an old fault;
  (2) reset + clean rotation clears; (3) reset + overflow relatches immediately
  (the safety property); (4) reset is per-orb (only the target orb clears);
  (5) reset idempotent (resetting a clean fault is a no-op == KeepFault);
  (6) global reset == the set of per-orb resets (identical state); (7)
  persistent fold == harness with a reset landing mid-stream on a fault set
  earlier in the same in-calculus run (`[0,1,1,0,0,0]`, set@1 reset@3 stays 0);
  (8) hard native gate ic_ref == ic32 == harness.
- Reset authority is separate from Spinner configurability; this pre-ADMIT
  slice accepts an already-authorized reset. Under 3b.5f, authorization
  belongs to the accepted `ResetFault` event. Film v0.6 does not record the
  transient reset pulse (it already records the resulting authoritative fault);
  the later claim-aware Film v0.7 records the accepted reset RECEIPT.

**Next: 3b.5f bounded ADMIT semantic core** for `SetRotor`/`ResetFault` —
monotone canonical claim facts, separate immutable acceptance receipts,
digest-min same-batch selection, first-receipt cross-batch, canonical
event-order application, Film v0.7 claim/receipt observability, persistent-fold
parity, hard native gate. Prehashed typed envelopes (no pure-term SHA-256).

---

# Forge Binding Results v0.16 — slice 3b.5e executed: persistent epochs (the v0.6 transition composes in-calculus)

**SLICE 3b.5e PASS_REF_AND_NATIVE (48s).** 3b.5d-2 proved a single v0.6
transition `λcfg.λst → st'`. This slice proves that transition **composes
under the interaction calculus' own reduction**: a world runs **K epochs from
one initial state entirely inside one normalization** — no Python
decode/re-encode between epochs — carrying counters + wires + doors + poses +
**rotors** + faults as pure IC data, and emits the whole film sequence from
that one normal form. Firing is driven by the world's **own clock** (the
periodic pulser through the one-epoch-delayed wire), **not** by manual
per-epoch wire injection.

## The finding

Persistence is **intrinsic to the compiled term**, not an artifact of the
harness re-injecting state. The internally-persistent K-epoch world is
**state-for-state and film-for-film identical** to the harness-stepped world
(which decodes and re-encodes state every epoch), and the identity holds on
the **native** runtime too.

- **The persistent driver** (`binding_run3i.drive_k`) folds the fixed step
  over a fixed pre-encoded config stream: each intermediate state is
  **affine-duplicated** (one copy feeds the next epoch, one copy is emitted),
  producing one term that normalizes to `TUPN([s₁ … s_K])`. State never leaves
  the calculus between epochs.
- **Battery** (K=6): (1) persistence identity — internal fold == harness,
  state + film, every epoch (final pose `(246,0,0,10)` under a genuine
  pulser-driven trajectory); (2) config-stream persistence — a mid-stream
  rotor change composes internally and the rotor field tracks the committed
  value across epochs; (3) sticky-fault persistence — a saturating rotor
  **committed at a firing epoch** latches `numeric_fault` inside the fold
  (`[0,1,1,1,1,1]`) and stays latched == harness; (4) determinism — one driver
  normalized twice → identical film-hash sequence; (5) **multi-controller
  persistence** — two spinners on different pulser periods (2, 3) with distinct
  rotors persist **independently** through the same fold, no cross-contamination
  (`ob0 (246,0,0,10) != ob1 (241,0,0,0)`) == harness; (6) **native hard gate**
  — the internal driver on ic32 == ic_ref == harness, state-for-state.
- **Scope (narrow, per roadmap)**: fixed graph, no ADMIT, no dynamic sockets,
  no claim replication. Stateful rotor changes flow through the fold as a fixed
  pre-encoded config stream. Run: `PYTHONPATH=../runtime/python:../research
  python3 binding_run3i.py` (`TRVM_SKIP_NATIVE=1` skips the native gate).
- **Design note**: because firing carries a one-epoch wire delay and config is
  applied **config→COMMIT→REACT**, a saturating rotor must be **committed at a
  firing epoch** to overflow the reacting rotation (committing it a tick early
  is overwritten by the next epoch's committed rotor before the spinner reads
  it — the same COMMIT-then-REACT ordering certified in 3b.5d-2 case 9).

**Next: raw ADMIT/claim-set lowering** (deferred through 3b.5d-2/3b.5e) — the
first slice to lower an accepted claim set onto compiled world state, or a
multi-orb / multi-controller persistent graph. Measure before building.

---

# Forge Binding Results v0.15 — slice 3b.5d-2 executed: Film v0.6, rotor-as-state (GPT-5.6 ruling 1A)

**SLICE 3b.5d-2 PASS_REF_AND_NATIVE (16s).** The dynamic Spinner (3b.5d-1)
made the rotor flow as data for essentially free (1.00×); this slice makes
the rotor **canonical runtime STATE** and evolves the canonical film
**v0.5 → v0.6**, per GPT-5.6's Option **1A** ruling: every v0.6 Spinner
carries its current rotor as state (a `TUP4×TUPw` field); the fixture rotor
is **initialization data only**. "Fixed" vs "configurable" is a **permission
distinction** enforced at the config-acceptance gate — **not** two state
layouts or two film paths. v0.5 is retained **replay-only**.

## The authority model (preserved + redefined)

- **Anchor invariant redefined + preserved**: `model_rotor == exact_lift(circuit_rotor_STATE)`
  (was `exact_lift(fixture_constant)`). The rotor is **assigned, never
  composed**, so a plain sign-extend-then-`<<(32−n)` rescale is exact — **no
  separator opens on the rotor** (contrast the POSE, which IS composed and
  does separate at Q32.32, slice 3b.5c). `fixture.lift_rotor` + a direct
  `model_projection_v6` assertion every epoch.
- **Authoritative sticky fault (the prerequisite fix)**:
  `binlib.dyn_rot_step_forge_dyn_f(w,n)` = the fully-dynamic `λR.λP` forge
  step that now **returns `RotationResult{pose:Quat4, overflow:Bool}`** —
  each lane's wide-MAC overflow flag is kept and the four are OR-reduced.
  The v0.6 transition latches `numeric_fault = old OR overflow`, **sticky**
  until an explicit reset op; Film v0.6 records it.
- **Config semantics**: `RotorConfigInput = NoChange | SetRotor(typed)`;
  transition order = **accepted config write → COMMIT (to rotor state) →
  REACT (rotate reading the just-committed rotor)**, so config + hot signal
  in the **same epoch → the NEW rotor controls the rotation** (case 9). A
  fixed spinner rejects rotor writes with a typed `RotorConfigError`; a
  configurable one accepts **without kernel replacement**; wrong
  geometry/range is rejected. This slice applies an **already-accepted**
  config to compiled world state; raw ADMIT/claim-set lowering stays
  **deferred** (GPT).

## What the battery proves (`binding_run3h.py`, all 15 + a Law-6 witness)

1 initial-construction (state rotor == fixture init, film v0.6) · 2 film
sensitivity (same pose, diff rotor → diff film) · 3 future sensitivity
(same hot signal, diff rotor → diff next pose) · 4 runtime rotor change
(one term, 5 rotors) · 5 no-recompilation (no rotor value baked in) · 6
model anchor (model Q32.32 == exact lift of circuit rotor STATE at init +
after config; a desynced rotor is rejected) · 7 corrupt state (tampered
rotor fails boundary-film parity) · 8 no-signal config (rotor commits,
pose unchanged) · 9 config+signal same epoch (committed rotor controls) ·
10 fixed spinner (SetRotor typed-rejected; NoChange still accepted) · 11
configurable spinner (accepted, applied on the same term, no swap) · 12
fault (saturating rotor latches fault=1; sticky across firing + idle) ·
13 type mismatch (wrong lane count / out-of-range rejected) · 14
determinism (same init+config stream → same film-hash sequence) · 15
**NATIVE hard gate** (4-epoch config trajectory `ic_ref == ic32`, rotor +
pose + fault, epoch for epoch) · **L6** (worlds agreeing on
pose/clock/wire/controller but R1≠R2 → v0.6 films MUST differ).

New surface: `binlib.dyn_rot_step_forge_dyn_f`; `compiler.compile_step_v6`,
`enc_state_v6`/`dec_state_v6`, `enc_rotor_config`/`enc_config_bundle`,
`accept_rotor_config`/`RotorConfigError`, `_v6_fields`; `fixture`
`configurable` permission + `is_configurable`/`orb_of`/`lift_rotor`/
`init_state_v6`/`state_to_film_args_v6`/`model_projection_v6`;
`film.film_bytes_v6`/`film_hash_v6` ("FILM v0.6"). Reproduce:
`PYTHONPATH=../runtime/python:../research python3 binding_run3h.py`
(`TRVM_SKIP_NATIVE=1` skips the native gate). Next: **3b.5e persistent
epochs** (state tuple carries clocks + wires + doors + relays + poses +
rotors + numeric faults; K epochs from one initial state, compare
harness-stepped vs internally-persistent v0.6 world epoch for epoch).

---

# Forge Binding Results v0.14 — slice 3b.5d-1 executed: the dynamic Spinner — rotor-as-data is essentially free

**SLICE 3b.5d-1 PASS_REF_AND_NATIVE (60s).** The 3b.5c pose authority bakes
a *constant* rotor into the circuit (`dyn_rot_step_forge`); a rotor change
needs a recompile (the 3b.5a EV_CONFIG kernel cache, keyed by rotor bytes).
This slice makes the rotor flow as **data**: `binlib.dyn_rot_step_forge_dyn`
is `λR.λP` — both rotor and pose are runtime TUP4 — so **one compiled term
applies any rotor with no recompilation**, under the same shipping forge
wide-MAC policy.

## What the battery proves (`binding_run3g.py`)

- **A) golden == ic_ref == ic32**: 18 (rotor,pose) cases at Q4.4 + Q8.8,
  fault 0; wide-MAC saturation latches a fault.
- **B) rotor-as-data == baked-in constant rotor**: the dynamic path is
  bit-identical to `dyn_rot_step_forge` for the same rotor, both widths.
- **C) runtime rotor change**: ONE compiled term, **5 distinct rotors**,
  each == its golden — the dynamic Spinner, **no recompile**.
- **D) cost (measure before building)**: Q4.4 step is **dynamic-rotor
  156162 vs constant-rotor 155748 interactions = 1.00×** — flowing the
  rotor as data is **essentially free** (~0.3%). This decisively motivates
  wiring it into the fixture (3b.5d-2): the flexibility (runtime rotor
  change, no kernel cache keyed by rotor bytes) costs almost nothing.
- **E) NATIVE GATE (hard)**: dynamic forge step @Q4.4+Q8.8 + a runtime
  rotor change through `ic32` == golden.

New surface: `binlib.dyn_rot_step_forge_dyn(w, n)` (fully-dynamic forge
wide-MAC quaternion step, reuses `dyn_mac`); `binding_run3g.py` (battery).
Reproduce: `PYTHONPATH=../runtime/python:../research python3
binding_run3g.py` (`TRVM_SKIP_NATIVE=1` skips the native gate). Next:
**3b.5d-2** — carry the rotor as circuit STATE, EV_CONFIG as a data write
(not a recompile) — then **3b.5e persistent epochs**.

---

# Forge Binding Results v0.13 — slice 3b.5c executed: the typed Q32.32 pose-authority bridge, one forge authority, the shadow dict gone

**SLICE 3b.5c PASS_REF_AND_NATIVE (70s).** The compiled IC circuit now
carries a **single real pose authority** under the shipping Spinner policy
`forge_motor_widemac_tz_sat_v1` (wide-MAC: full-precision products, ONE
toward-zero shift, ONE saturation). The frozen `proc-e2.3` oracle
(`e2_model.qmul`, legacy per-product trunc0) is **demoted to an
EVENT/STRUCTURE oracle** — it defines *when* a rotation fires, not the pose
*value*. This is **Option A** of the round-13 policy fork (user decision
2026-07-21): no `proc-e2.3` edit; the shipped pose value differs from the
frozen model's by the certified separator — **accepted and certified, not
equal**. The bridge certifies a *difference*.

New surface: `binlib.golden_rot_forge` / `binlib.dyn_rot_step_forge` (the
forge wide-MAC quaternion rotor step, golden + λP IC term, reusing
`dyn_mac`); `compiler.compile_step(fx, pose_policy=...)` selects `legacy`
(unchanged proc-e2.3-value path, still default) or `forge` (the new Q32.32
authority); `binding_run3f.py` (the battery). **The shadow `poses` dict is
gone**: the circuit's own state IS the pose, value-locked to the forge
golden across a live model run.

## What the battery proves

- **A) forge step golden == ic_ref == ic32**: 18 (rotor,pose) cases at
  Q4.4 + Q8.8, fault 0; a wide-MAC lane that overflows **clamps and latches
  a fault** (the saturation the legacy policy lacks).
- **B/C) single forge authority, no shadow dict** (T=45 live proc-e2.3
  run): the compiled circuit's self-carried pose is **value-locked to the
  forge golden every epoch**, and it fires in **exact event-parity with
  proc-e2.3** (15 rotations, same epochs). The model (legacy) supplies only
  *when*; the circuit supplies *what*. Same facts compel the same recognized
  behavior; the value is independently the forge law.
- **D) certified Q32.32 value-separator** (20,000 Z90 composes, authority
  width): forge ≠ legacy **from epoch 2**; lane-0 delta **2066 ULP** at 20k;
  forge drift **−1.919083e-05** vs legacy **−2.015289e-05** (the ledger
  separator, reproduced to 1e-15). The bridge **certifies the DIFFERENCE** —
  the round-12 "prove Q32.32 equality" expectation is *refuted* by the
  separator, exactly as the 3b.5c blocker predicted; the certificate is the
  honest artifact.
- **E) typed Q32.32 ↔ proxy bridge**: the proxy rotor **lifts exactly** to
  Q32.32 (`<<(32−n)` — the anchor law `fixture.model_projection` already
  asserts); **one** forge step commutes with the rescale on aligned lanes;
  the long-horizon separator (D) is where the widths part. The
  proxy/Q32.32 BindingWorld split is now **explicit**: proxy is a typed
  narrowing of the Q32.32 authority.
- **F) NATIVE GATE (hard)**: the forge rotor step at Q4.4 + Q8.8 through
  `ic32` == golden; **8 epochs of the compiled forge authority** through
  `ic32`, value-locked — 0 mismatches.

## The certificate (typed, shipped)

| claim | status |
|---|---|
| event-parity to proc-e2.3 | **exact** — circuit fires iff the model fires (15/15 epochs, T=45) |
| pose authority | **single, forge wide-MAC**, carried by the circuit; **no shadow `poses` dict** |
| value vs legacy @ small width | agree (proxy) |
| value vs legacy @ Q32.32 | **certified-different**: epoch-2 divergence, 2066 ULP @20k, drift separator reproduced |
| proxy ↔ Q32.32 | typed exact rotor lift; one-step rescale-commutes; long-horizon separation is the certificate |
| golden == ic_ref == ic32 | forge step + compiled authority, hard native gate green |

Slice 3b.5c is complete. The legacy `pose_policy` default keeps 3b.5a
(`binding_run3e.py`) green unchanged (PASS_REF_ONLY re-verified). Reproduce:
`PYTHONPATH=../runtime/python:../research python3 binding_run3f.py`
(`TRVM_SKIP_NATIVE=1` skips the native gate). Next: **3b.5d dynamic
Spinner**, then **3b.5e persistent epochs**.

---

# Forge Binding Results v0.12 — slice 3b.5b-3 executed: the normalization operator, built against the datum, ref+native green

**SLICE 3b.5b-3 PASS_REF_AND_NATIVE (13s).** The reserved
`forge_motor_renorm_tz_sat_v1` is now a first-class IC operator, gated
golden → ic_ref → ic32, and it arrests the 3b.5b-2 drift. Designed
*against the measured datum*, not guessed: first-order (Newton)
renormalization, **no sqrt** — the per-step drift near unit is small, so
the scale `s = sat_w((3·ONE² − norm2) >> (n+1))` (toward zero) applied to
every lane under the shipping wide-MAC policy (exact product, ONE
toward-zero shift, ONE saturation) is exactly the tool the data indicates.
`norm2` is the real-norm² (rotor lanes 0..3 squared) at full width
`Wn = mac_headroom(w,4)`; scale-overflow, any lane-overflow, and the input
fault all OR into the ninth-slot `numeric_fault`.

## What the battery proves

- **golden == ic_ref**: 25/25 lane-exact + fault (rotor sweep + random
  motors); input fault propagates through the operator.
- **drift ARREST** (renorm-every-step vs uncorrected worst, all
  precisions): Q4.4 90.23% → 24.61% (3.7×), **Q8.8 38.93% → 1.56% (25×)**,
  **Q16.16 0.40% → 0.0062% (64×)**. The operator strictly reduces
  worst-case norm error at every precision; at practical widths it holds
  the rotor to a fraction of a percent.
- **Properties**: near-unit renorm is non-worsening; a collapsed rotor
  recovers toward unit (real-norm² 64 → 121 of ONE²=256 at Q4.4); a large
  translational lane (which does not enter norm², so the scale stays >ONE)
  latches the lane-overflow fault. *Design note recorded: the first-order
  scale itself is bounded ≈3·ONE/2 and cannot saturate — only lane scaling
  can fault.*
- **NATIVE GATE (hard)**: 5 renorms + 1 fault-propagation through `ic32` —
  0 mismatches vs `golden_renorm`.

New surface: `motor8.golden_renorm` (exact, reuses `golden_mac`),
`motor8.dyn_motor_renorm` (the λM 9-tuple IC term), `motor8_renorm_run.py`
(the battery). The composition rulepack keeps `normalization =
none_in_composition` (renorm is a *separate* named op, applied by the
caller when it chooses); slice 3b.5b (Motor8) is now complete —
composition, drift, and normalization all ref+native green. Reproduce:
`PYTHONPATH=../runtime/python:../research python3 motor8_renorm_run.py`.

---

# Forge Binding Results v0.11 — slice 3b.5b-2 executed: the drift is measured, the collapse is named, normalization is reserved

**SLICE 3b.5b-2 PASS_MEASUREMENT — measurement only, per the verdict
("Do not normalize inside the first composition battery; 3b.5b-2 measures
drift; a named normalization operation with its own film-visible policy
comes after"). This slice quantifies the datum a later slice must
correct, so the correction is designed against a number.**

The drift metric is proc-e2.3's convention lifted to the motor:
`(motor_norm2_real(pose) − ONE²)/ONE` in ULP-relative units. The motor
"norm" is the study number `M~M = a + b·e0123` (`reverse` flips grade-2
lane signs); its REAL part (lane 0) is the Euclidean rotor norm², its
IDEAL part (lane 7) is the rigid-motion coupling a unit motor holds at 0.
On the rotor subalgebra `motor_norm2_real` IS the quaternion norm² —
asserted here (52 rotors) — so the number is directly comparable to the
ledger's −2.015289e-05 Q32.32 rotor drift.

## What was measured

- **Single-rotor quantization floor** (one encode, no composition): max
  +1.125e+00, mean +4.81e-01 ULP-rel — the irreducible per-rotor error.
- **Composition drift, Q4.4, rotor(11.25°) ×128**: **−14.4375 ULP-rel =
  −90.2% of unit norm², fault 0** — toward-zero truncation is *biased*,
  so the rotor bleeds magnitude and **collapses to a sub-unit fixed point**
  (drift plateaus by step ~32: +0.25 → −5.75 → −14.44 → −14.44 → −14.44).
  This is the headline: unnormalized fixed-point rotor composition does
  not merely wander, it *decays into a stable sub-unit attractor*.
- **Same trajectory, Q8.8 ×128**: −38.9% of unit norm² — **relative decay
  2.3× smaller** than Q4.4 (precision helps, but 39% loss over 128 steps
  still demands normalization).
- **Rigid (ideal-part) constraint**: for a screw (rotor·translator) ×32
  the study-number ideal part **held at exactly 0** in this lattice — the
  second invariant a normalizer must protect, currently clean.
- **IC == golden along the trajectory** (6 steps through `ic_ref`): the
  drift is a property of the *proven* policy, not a harness artifact — the
  golden==IC chain from 3b.5b-1 is unbroken for these exact motors.

## The reserved target

A unit motor must hold real-norm² == ONE² (ideal 0). Measured deficit to
correct at Q4.4/×128 is −14.4375 ULP-rel. Normalization policy **reserved,
not built here**: `forge_motor_renorm_tz_sat_v1` — slice 3b.5b-3, designed
against this datum (first-order renormalization is the indicated tool: the
per-step drift near unit is small, so a scalar ≈ 1/‖M‖ correction applied
periodically fits the measured regime; a full rsqrt is not warranted by
the data).

New surface: `motor8.reverse` / `motor_norm2` / `motor_norm2_real`;
`motor8_drift.py` (the measurement battery). Reproduce:
`PYTHONPATH=../runtime/python:../research python3 motor8_drift.py`.

---

# Forge Binding Results v0.10 — slice 3b.5b-1 executed: the eight-lane Motor8 composes, wide-MAC policy, ref+native green

**SLICE 3b.5b-1 PASS_REF_AND_NATIVE (373s), first green run, ten battery
sections.** The even subalgebra of 3D PGA Cl(3,0,1) — the 8-blade motor
`[1, e23, e31, e12, e01, e02, e03, e0123]` — now composes as a pure IC
term under the shipping `forge_motor_widemac_tz_sat_v1` policy. Signs are
DERIVED from a single canonical blade multiplication under the metric
(e0²=0, eᵢ²=+1, all anticommute), not read off lane names; `e31 = −e13`
is the only signed canonical. Each output lane is a wide-MAC over its
surviving signed blade products (per-lane term counts [4,4,4,4,8,8,8,8],
so Wacc = 2w+3 = 19 bits at w=8, the strict no-wrap bound), one
toward-zero shift, one symmetric saturation; the eight lane overflow bits
OR into the ninth-slot authoritative `numeric_fault`. Content-addressed
rulepack id `5d5b1231ac6cb1bb` covers basis order, metric signature, full
multiplication table, lane width, fraction bits, rounding, saturation,
and normalization=`none_in_composition`.

## What the battery proves (ref, then hard native gate)

- **64 basis-blade pairs**: table closure exact vs `golden_geo`; each
  product single-lane or degenerately annihilated; 48/64 nonzero.
- **Identity both sides**: I∘B == B∘I == B lane-exact, fault 0.
- **Pure rotor composition**: ref == golden across 25 rotor pairs; the
  rotational bivectors + scalar reproduce the independent Hamilton
  wide-MAC oracle under the embedding I=−e23, J=−e31, K=−e12
  (`QUAT_EMB=(1,−1,−1,−1)`); translational lanes stay 0; Z90 trajectory
  ×16 value-exact (~153k interactions/compose).
- **Pure translator composition**: stays in the translator subspace
  (rotational+pseudoscalar lanes 0), ref == golden.
- **Mixed rotor/translator**: ref == golden; noncommutativity witnessed
  (36/40 pairs A∘B ≠ B∘A).
- **Overflow/saturation**: all-MAX products latch fault=1 and clamp ==
  golden; random wide products ref == golden through saturation.
- **Per-lane wide accumulator oracle**: |acc| < 2^(Wacc−1) by
  construction and over 200 adversarial motors.
- **NATIVE GATE (hard)**: 5 motor products through `ic32` — 0 mismatches
  vs `golden_fixed`.

New surface: `binlib.dyn_mac(w,n,signs)` (general k-term wide-MAC,
arbitrary-arity generalization of `dyn_mac4`, verified vs `golden_mac`
across k∈{1,2,3,5,8}); `motor8.py` (algebra, derived GEO_TERMS, goldens,
rulepack, `dyn_motor_mul` constant-A-onto-dynamic-B compiler with
zero-lane fold at emit time); `motor8_run.py` (the battery).
Normalization is deliberately absent (verdict) — 3b.5b-2 measures drift
before any named normalization op is introduced.

## Reproduce (3b.5b-1)

```
cd forge
PYTHONPATH=../runtime/python:../research python3 motor8_run.py            # ref + native, 373s
PYTHONPATH=../runtime/python:../research TRVM_SKIP_NATIVE=1 python3 motor8_run.py   # ref only
```

---

# Forge Binding Results v0.9 — round 12 executed: the Spinner is a fixture citizen, film v0.5 carries pose

**SLICE 3b.5a PASS_REF_AND_NATIVE (146s), first run, all eight battery
items. The Spinner is now first-class: film v0.5 carries authoritative
pose state (numeric-policy id, lane geometry, big-endian
two's-complement lanes, controller relationship, fault latch), and the
compiled epoch term applies the rotor by Scott FUNCTION-selection on
the spinner's in-wire — the pose is consumed exactly once, and the
dead rotation branch erases before its interior reduces: idle epochs
cost 39 interactions inside a 1 MB term; firing epochs ~76.5k (Q4.4) /
~305k (Q8.8). Measured, not assumed.**

## Round-12 corrections, executed first

Transitivity wording corrected to the CONDITIONAL form (demonstrated
small-width equality + implication at Q32.32; closure assigned to the
3b.5c typed bridge). Separator table now carries the canonical
corrected-horizon figures: **19,979/20,000 divergent, wide-MAC
−1.919083e-05 vs oracle −2.015289e-05** — my own rerun log already
contained them; the ledger had quoted the stale pre-fix run.
E2_RESULTS retitled **v2.3 — Native Once Refreeze (28/28)**. Policy
identities registered in binlib: `legacy_spinner_pp_tz_nosat_v1`,
`forge_motor_widemac_tz_sat_v1`.

## The width-scoping decision (stated for ratification)

The binding Spinner is a Forge-layer object at fixture-declared proxy
width whose pose semantics are the PARAMETRIC ORACLE POLICY (proven ≡
`e2_model.qmul`, 3b.4 §A). The real Q32.32 World runs in lockstep as
the timing/structure anchor; its rotor is the exact `<<(32−n)` rescale
of the filmed proxy lanes, **asserted at every projection** (config
integrity has teeth). Q32.32 value parity closes at 3b.5c per the
round-12 ruling. Film v0.5's policy-id + lane-geometry fields make the
width explicit so nothing is silently conflated.

## Slice 3b.5a battery (all PASS, first run)

| item | result |
|---|---|
| pulser→wire→spinner latency+parity, Q4.4 T=45 | films exact; rotations at the closed form {4,7,…}; **idle 39 ints, firing 76,488–77,638** |
| independent init | boundary parity holds; **corrupted pose lane FAILS it** (teeth) |
| Q8.8 parity T=16 | films exact; firing 304,025–306,977 ints |
| dynamic multi-rotation (period 2, T=30) | 15 rotations, films exact every epoch |
| controller exclusivity + release | static double-socket → typed ValueError; live second LINK rejected as `controlled`; DELETE frees; relink succeeds |
| EV_CONFIG rotor at epoch 10 | model CFG (anchor rescale) + kernel swap keyed by (policy, rotor bytes); films exact across the change |
| determinism | same artifact+inputs twice → identical film sequences |
| NATIVE GATE (hard) | 8 full epochs of the 1 MB spinner term through ic32, films exact |

Overflow law status, per the ruling: the legacy policy has no
saturation; the film's fault bit is present and 0, wired for the
wide-MAC policy where it becomes authoritative (3b.5b).

## Ripple regressions under film v0.5

The version line bumps every film hash; both sides bump together. One
real break found and fixed: `state_from_projection` unpacked a
5-tuple — now accepts the v0.5 seven-tuple, ignoring pose sections in
discrete-only slices. run3e **PASS_REF_AND_NATIVE** (146s) · run2
**PASS** · run3 **PASS** · run1 smoke + NEG 4/4 · run3d rerun **PASS_REF_AND_NATIVE** (rc=0 under the v0.5 tree) ·
oracle 28/28 and `make test` unchanged (film is binding-layer only).

## The policy finding, reconciled with round 11's freeze

Round 11 froze the wide-MAC (exact products → sign-extend → ±
accumulate → ONE shift → ONE saturation) as **Forge numeric law for new
numerics**. The spinner is not new numerics: it is governed by the
frozen v2.2 oracle, whose policy is per-product truncation. Both live
in `binlib` (`dyn_mac4` = the law; `hcomp_case`/`rot_step_case`/
`dyn_rot_step` = the oracle's policy), and the live separator on the
real trajectory shows the stakes: **first divergence at rotation 2;
19,979 of 20,000 rotations diverge; wide-MAC drift −1.919083e-05 vs
the oracle's −2.015289e-05** (canonical, at the corrected horizon).
The policies are one ULP apart per component and ~5% apart in
century-scale drift.

## The K off-by-one — a lesson in not extrapolating a schedule

My first drift replication used K=19,999 rotations and missed the
documented figure in the 5th significant figure. The long run executes
epochs tc = 2 … **100,001** (build primes two epochs), so rotations at
tc≥6, (tc−6)%5==0 count to **K=20,000**. The fix is not a formula
patch but a method change: section B1 now validates the schedule and
function against the ACTUAL model — 200 epochs, pose exact every epoch
— and only then extrapolates. **K=20,000 → drift −2.015289e-05,
matching the documented figure to all printed digits (tol 1e-11).**

## Slice 3b.4 battery

| section | result |
|---|---|
| A. parametric policy ≡ `e2_model.qmul` at Q32.32, 2000 random quats | **PASS** |
| B1. schedule+function vs the actual model, 200 epochs pose-exact | **PASS** |
| B2. drift replication, K=20,000 → **−2.015289e-05** ≡ documented | **PASS** |
| C. policy separator LIVE on the real trajectory | measured (above) |
| D. hcomp (per-product policy, in-range flag) ×400; **const rotation trajectories pose-value-exact**: Q4.4 T=64, Q8.8 T=24 | **PASS** |
| E. **DYNAMIC rotation trajectories pose-value-exact**: Q4.4 T=32, Q8.8 T=8 | **PASS** |
| F. NATIVE GATE (hard): const ×6 + dynamic ×3 through ic32 | **PASS, 0 mismatches** |
| G. transitivity verdict (CONDITIONAL, per round 12) | the tested lowering implements the oracle's policy at Q4.4/Q8.8 (D,E) ∧ the same parametric policy ≡ oracle at Q32.32 (A) ∧ reproduces the documented drift (B) ⇒ **a correct Q32.32 instantiation of this lowering would reproduce the drift** — a demonstrated equality at small widths plus an implication at target width; Q32.32 parity closes at the 3b.5c typed bridge |

## The measured quaternion numbers (the round-11 optimization input)

Per rotation (8 nonzero products for ROT_Z90; zero-rotor products
skipped at emit — fixture constants compile in):

| form | Q4.4 | Q8.8 |
|---|---|---|
| constant | 71,056–72,392 (mean **71,216**) | 285,480–289,176 (mean **287,460**) |
| dynamic pose | 76,286–77,600 (mean **76,607**) | 303,998–307,526 (mean **305,938**) |

The dynamic tax at rotation scale is ~7%. The reviewer's 16-product
estimate (~577k) halves under zero-skipping for this rotor; a dense
rotor would land near it. **This is the datum the round-11 ruling
deferred the optimization decision to.**

## Round-11 conditions, executed

Registry **completed**: `mul_wide`/`shift_tz` registered (flat,
no-flag), `mac` registered (nested); **`dyn_mac4` promoted into binlib**
as the reusable frozen-policy combinator (verified ×8 vs golden);
`mac_headroom(w,k)` makes the accumulator-cannot-wrap claim an
**executable assertion** (Wacc = 2w+⌈log₂k⌉, strict bound checked).
`dyn_take_value` remains documented legacy/flat-only. Eager-class cost
claims formally moved to the packed-net venue (two-field cost records:
logical firings + wall-clock under named scheduler). **Native model
Once: narrow unfreeze granted — executing next**; until it lands, Law 6
remains horizon-scoped and the stale fixture.py sentence stands
condemned.

## Regressions — ALL rerun under the native-Once tree

run3d **PASS_REF_AND_NATIVE** (417s; drift −2.015289e-05 unchanged, as
the schedule requires) · run3c **PASS_REF_AND_NATIVE** (134s) · run3b
**PASS** (345s) · run3 **PASS** (once-heavy slice) · run2 **PASS** ·
run1 smoke + NEG 4/4 · oracle **28/28** · `make test` 13/13 (rulepack
hash moved with the edit, as content-addressing requires).

## Laws

1–7 unchanged. Round-11 commentary on Law 5: *two numeric policies are
two meanings — an encoding may not switch between them silently; a
policy change is an explicit act with a measured separator.*

## Deferred, stated

3b.5 Motor8 integration (film/pose fields,
compiler spinner support, constant-rotor multiplier specialization as a
measured optimization) — **gated on round-12 review with the quaternion
numbers above as input**. w-row/Booth multiplier for the product path.
Packed-net eager measurement. Framed WireIdentity; structural lowering;
persistent loop; ADMIT on-reducer; CUDA.

## Reproduce

```
cd forge
python3 binding_run3d.py     # 3b.4 quaternion proxy (~4-5 min)
python3 binding_run3c.py && python3 binding_run3b.py
python3 binding_run3.py && python3 binding_run2.py
python3 binding_run.py && python3 binding_run.py NEG
python3 e2_run.py && cd .. && make test
```
