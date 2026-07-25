# Forge Spinner Bench -- Quickstart (v0.7.0-alpha.5)

A local, six-panel web app that authors a **WRL** world, lowers it through the
real **WRL -> IR -> CompilePlan -> TRVM** pipeline, folds it with the
interaction-calculus runtime, and shows the sealed identity + per-epoch film.
The six panels are **Canvas**, **WRL editor**, **World disc**, **Film + identity**,
**SemanticDiff**, and **Scenario author**.

## First run

On a fresh launch (no project to restore) the app opens a small landing surface
rather than the full bench: **Explore Golden Demo** (a read-only tour that creates
nothing), **Create Project**, or **Open Project**. A dismissible **guided-demo
rail** walks six steps over the existing panels; its state is browser-local only.
Two workspace views -- **Author** and **Evidence** -- toggle in the header and share
the same state and APIs. From a demo exploration, **Make an editable copy** is the
one path that creates a real, persisted project.

## Run it

```
./forge-bench                 # build/locate native reducer, pick a port, serve
./forge-bench --open          # ...and open a browser
./forge-bench --ref-only      # skip the native reducer entirely (pure Python)
./forge-bench --port 9000 --project-dir ~/forge-data
```

Then open the printed URL (default `http://127.0.0.1:8765/`).

`./forge-bench` is the only command you need. It locates the Python running it,
locates or **builds** the native reducer from `ic32.c` (`gcc -O2`) into an
**external cache** (see below), chooses the first free port, displays the
project + cache dirs, and -- if startup fails -- prints the exact command to run
the server by hand.

## Read-only installation

The extracted release is **read-only**: launching it never writes back into the
install directory. Two things that used to write there now live in an external
per-OS cache instead:

| What            | Where (Linux)                        | Overrides                     |
|-----------------|--------------------------------------|-------------------------------|
| native `ic32`   | `~/.cache/trvm-forge/runtime/`       | `FORGE_RUNTIME_CACHE`, `TRVM_IC32_PATH` |
| Python bytecode | `~/.cache/trvm-forge/pycache/py<ver>/` | `FORGE_RUNTIME_CACHE`         |

(macOS uses `~/Library/Caches/TRVM Forge/`; Windows uses
`%LOCALAPPDATA%\TRVM Forge\cache\`.) The native binary is keyed by the `ic32.c`
source hash + OS + arch, so multiple installed versions share one compatible
binary and an edited source auto-rebuilds. You can delete the release folder or
mark it read-only; a launch still works.

## Where your projects are stored

Authoring state lives **outside** the install directory, in your OS data dir:

| OS       | Default project dir                              |
|----------|--------------------------------------------------|
| Linux    | `~/.local/share/trvm-forge/projects`             |
| macOS    | `~/Library/Application Support/TRVM Forge/projects` |
| Windows  | `%LOCALAPPDATA%\TRVM Forge\projects`             |

Override with `--project-dir DIR` or the `FORGE_PROJECT_ROOT` env var. The
crash-recovery journal is a sibling `.../.recovery`. **The install directory is
never written to** -- deleting the release folder never loses a project.

### Back up a project

Copy the project data dir (above), or use **Export -> full project bundle** in
the app (a self-contained, content-addressed bundle you can re-import anywhere).

## The two identities: active vs candidate

- **Active** identity is the sealed `SemanticArtifactID` of the world you have
  **committed**. It is what a Run/Verify folds.
- **Candidate** is your in-editor draft. It has its own (possibly different, or
  invalid) identity until you commit it. Presentation-only edits (x/y position,
  color, wire curve) never move identity; a rotor or wiring change does.

The SemanticDiff panel shows `is_empty() <=> sem_id(a) == sem_id(b)` live between
the two.

## Save vs Commit

- **Save** persists your whole workspace (draft buffer, undo stack, scenario
  selection) to the project doc on disk. A Save of an *uncommitted* draft
  survives a restart but does **not** change the active identity.
- **Commit** promotes the candidate to the active world -- it advances the
  project revision and is what a Run folds. Committed edits survive a restart.

## Recovery journals

While you edit an unsaved workspace the app periodically checkpoints a
non-authoritative **RecoveryJournalV1** to `.../.recovery`. If the server exits
unexpectedly, reopening the project offers to recover the unsaved draft. It never
overwrites a saved project silently.

## Run vs Verify Native

- **Run** folds every epoch through the **reference** reducer (`ic_ref`, pure
  Python) and shows the per-epoch Film v0.7 hash.
- **Verify Native** re-folds the SAME scenario through the compiled **`ic32`**
  reducer and asserts world + film parity (`ic_ref == ic32`). With **oracle**
  on, it ALSO cross-checks against the independent Fixture oracle
  (`ic_ref == ic32 == fixture`). Native is gated off by `--ref-only` /
  `TRVM_SKIP_NATIVE=1`, in which case Verify reports ref-only.

Long folds run as **cancellable background jobs** (`POST /api/jobs`); navigate
away and they keep going, cancel them with `POST /api/jobs/<id>/cancel`.

## Health

- `GET /api/health` -- **shallow**, fast, boot-safe: re-lowers the demo world and
  confirms the frozen `DEMO_WORLD_SEMANTIC_ID`, reports whether the project +
  recovery dirs are writable, the project schema, native availability, and cache
  occupancy. It folds nothing.
- A **deep** check (small ref + native fold + film parity + object-store
  round-trip) is a separate cancellable job (`POST /api/jobs {"kind":"deep_health"}`)
  -- never run on boot.

## Full vs thin export

- **Full project bundle** -- self-contained: the sealed world bytes, scenarios,
  and everything needed to re-import with all authoritative IDs intact.
- **Thin export** -- references content by id without inlining the object bytes;
  smaller, but the target must already have those objects.

## License

See the `LICENSE` file at the release root for the terms this software ships
under.
