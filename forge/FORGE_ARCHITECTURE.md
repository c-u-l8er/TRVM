# Forge Spinner Bench -- Architecture (v0.6.5.1)

## Dependency direction (the v0.6.5 release boundary)

The production server depends **only** on the runtime + state adapters, never on
a test battery and never on the Fixture oracle:

```
  spinner_bench  ->  forge_runtime  ->  ic_ref / ic32        (the reducers)
  spinner_bench  ->  forge_state    ->  (pure functions of a duck-typed view)

  binding_run*   ->  spinner_bench, forge_runtime            (test batteries)
  fixture (oracle) ->  binding_run* and the OPTIONAL Verify-Oracle mode
```

- **`forge_runtime.py`** -- `ref_reduce` (ic_ref, pure Python) and
  `native_reduce` (subprocess to the compiled `ic32`), plus `native_available()`.
  Imports `ic_ref` and `subprocess` directly. No `binding_run*`, no Fixture. The
  `ic32` path prefers `TRVM_IC32_PATH` (the external cache binary the launcher
  built) and falls back to the dev-tree `runtime/c/ic32` for the batteries.
- **`forge_paths.py`** -- owns the EXTERNAL cache locations (`cache_root`,
  `runtime_cache_dir`, `pycache_prefix`) and the transactional native build
  (`ensure_ic32`: content-addressed key, temp compile -> verify -> atomic
  rename). This is what keeps the installation read-only (see below).
- **`forge_state.py`** -- `init_state_v6` / `state_to_film_args_v6` (and the base
  `init_state` / `state_to_film_args`). Pure functions of a duck-typed lowering
  **view**; they consume the same read interface a `_PlanView` and a `Fixture`
  both provide. Imports no Fixture.
- **`fixture.py`** -- now an **independent test oracle**. It re-imports the four
  state functions from `forge_state` so every battery keeps working, and is
  loaded **lazily** by the server only for the optional Verify-Oracle
  cross-check (`prog.as_fixture_for_test()`).

Importing `spinner_bench` (the normal Run path) pulls in **no** `fixture` and
**no** `binding_run*` module. This is enforced by `binding_run35` RC4/RC5.

## The lowering + fold pipeline

```
  WRL sugar text
     |  wrl_sugar.desugar_core / wrl_format / wrl_diagnostics / wrl_complete
  WRL Core
     |  wrl_ir.parse_wrl_core -> wrl_ir.lower_program  (seals identity)
  SealedArtifact  (SemanticArtifactID = Hash(IR + policies))
     |  wrl_plan.artifact_to_compile_plan_v1 -> plan_view  (the _PlanView)
  CompilePlanV1  (backend-neutral)
     |  compiler.compile_step_v6   (one epoch step term)
  interaction-calculus term
     |  forge_runtime.ref_reduce  (ic_ref)   /   native_reduce (ic32)
  world state per epoch
     |  forge_state.state_to_film_args_v6 + admit.film_hash_v7
  Film v0.7 hash
```

Identity is split three ways and never crosses: **SemanticArtifactID**
(IR + policies), **BackendArtifactID** (SemID + lowering profile), and the
per-epoch **Film** hash. Presentation (canvas x/y/color/curve) is projected
AROUND the graph and enters no identity.

## Caches (v0.6-4, retained)

Two bounded, thread-safe LRU memos (`_LruCache`, cap `_CACHE_CAP`):
`_PROG_CACHE` (sealed programs keyed by source) and `_TRAJ_CACHE` (reference
trajectories keyed by `(SemanticArtifactID, reducer, ScenarioDigest)`). A cache
is a **pure memo** -- an evicted key recomputes to byte-identical bytes and moves
no identity.

## Persistence (all OUTSIDE the install tree)

- `wrl_project.ForgeProjectStore` -- per-project `<pid>.json` under
  `<data-dir>/projects`.
- `wrl_project.ProjectSessionCache` -- version-dispatched V1/V2 docs; a V2 doc
  persists the complete workspace (draft buffer + undo + scenario selection).
- `wrl_project.RecoveryJournalStore` -- non-authoritative crash overlay at the
  sibling `<data-dir>/.recovery`.
- `wrl_store.WorldObjectStore` / `ScenarioRuntimeStore` -- content-addressed
  immutable object substrate under `<data-dir>/projects/.objects` for bundle
  import/export.
- `wrl_project.LastSessionStore` -- a single non-authoritative pointer at the
  last opened project (moves no revision, self-heals if the project is gone).

The default `<data-dir>` is the per-OS user data directory (see
FORGE_QUICKSTART.md); `FORGE_PROJECT_ROOT` overrides it. Nothing is written into
the install directory.

## HTTP surface (selected)

- `GET  /api/health` -- shallow self-check (no fold).
- `POST /api/lower` -- seal + diagnostics + formatted core + rotor init.
- `POST /api/run` / `POST /api/verify` -- synchronous folds.
- `POST /api/jobs {kind: run|verify|deep_health}` -- cancellable background fold;
  poll `GET /api/jobs/<id>`, cancel `POST /api/jobs/<id>/cancel`.
- project / scenario / recovery / bundle endpoints (see `spinner_bench.py`).

## Native runtime

`runtime/c/ic32.c` compiles (`gcc -O2`) to the native reducer. The launcher
builds it on first run **into the external runtime cache** (never into the
install tree), keyed by source-sha256 + OS + arch, and passes the resulting path
to the server via `TRVM_IC32_PATH`. The server calls it via subprocess with a
timeout and hard-gates parity against `ic_ref`. `--ref-only` /
`TRVM_SKIP_NATIVE=1` skips it entirely.

## Read-only installation (v0.6.5.1)

Launching a release -- reference or native -- leaves the extracted tree
byte-identical. Everything that used to write into the install now lives in an
external per-OS cache owned by `forge_paths.py`:

- native `ic32` -> `<cache_root>/runtime/ic32-<sha256>-<os>-<arch>`;
- Python bytecode -> `<cache_root>/pycache/py<ver>/` via `PYTHONPYCACHEPREFIX`
  (the launcher also sets `sys.dont_write_bytecode` in its own process).

`cache_root` is `~/.cache/trvm-forge` (Linux), `~/Library/Caches/TRVM Forge`
(macOS), or `%LOCALAPPDATA%\TRVM Forge\cache` (Windows); `FORGE_RUNTIME_CACHE`
overrides. `binding_run36` proves the install hash is identical before and after
a full author/save/recover/export/import session on a read-only extraction.

## License

The repository `LICENSE` ships at the release root.
