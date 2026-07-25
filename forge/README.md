# Forge Spinner Bench

*A deterministic world-authoring environment that keeps world meaning, execution
inputs, and runtime evidence separately identifiable.*

A local, six-panel web app that authors a **WallRiderLang (WRL)** world, lowers
it through the real **WRL → IR → CompilePlan → TRVM** pipeline, folds it with the
interaction-calculus runtime, and shows the sealed identity plus the per-epoch
film. It is the reference authoring surface for the TRVM Forge world model.

> **Status: Public Alpha (v0.7.0-alpha.5).** The `forge.world.core.v1` profile,
> the identity rules, and the Golden Demo are **frozen** and parity-checked
> (`ic_ref == ic32`); the product interface remains **alpha**. Expect UI and doc
> changes; the on-disk formats are versioned and forward-only.

## Run it

```
./forge-bench                 # build/locate the native reducer, pick a port, serve
./forge-bench --open          # ...and open a browser
./forge-bench --ref-only      # skip the native reducer entirely (pure Python)
./forge-bench --port 9000 --project-dir ~/forge-data
```

`./forge-bench` is the only command you need. It locates the Python running it,
locates or **builds** the native reducer from `ic32.c` into an external cache,
picks the first free port, prints the URL (default `http://127.0.0.1:8765/`),
and — if startup fails — prints the exact command to run the server by hand.

The extracted release is a **read-only installation**: launching it never writes
back into the install directory. Native binaries and Python bytecode live in an
external per-OS cache; your projects live in your OS data dir. Deleting the
release folder never loses a project. See **FORGE_QUICKSTART.md** for the exact
paths and overrides.

## The six panels

1. **Canvas** — the world as a graph; drag to lay it out (presentation only).
2. **WRL editor** — the world's canonical source text; edit and re-lower it.
3. **World disc** — the sealed world: its `SemanticArtifactID` and object roster.
4. **Film + identity** — Run/Verify results and the per-epoch Film v0.7 hashes.
5. **SemanticDiff** — a live `is_empty() ⇔ sem_id(a) == sem_id(b)` between the
   active world and your in-editor candidate.
6. **Scenario author** — the run inputs (rotor/fault claims per epoch); a
   scenario is a *run input*, never part of the world's identity.

## The identity model in one line

The **active** world is the sealed `SemanticArtifactID` you have **committed**;
the **candidate** is your in-editor draft with its own (possibly invalid)
identity until you commit it. Presentation-only edits (position, color, wire
curve) never move identity; a rotor or wiring change does.

## Where to go next

| Document                   | What it covers                                        |
|----------------------------|-------------------------------------------------------|
| **FORGE_QUICKSTART.md**    | run flags, cache/project paths, Save vs Commit, Run vs Verify, export modes |
| **FORGE_ARCHITECTURE.md**  | the dependency boundary, the lowering pipeline, the read-only-install design |
| **RELEASE_NOTES.md**       | what changed in each release                          |
| **LICENSE**                | the terms this software ships under                   |

## Identity, at a glance

- **No fold is trusted blindly.** `GET /api/health` re-lowers the demo world on
  demand and confirms it reproduces the frozen `DEMO_WORLD_SEMANTIC_ID`.
- **Native parity is a hard gate.** Verify re-folds through the compiled `ic32`
  and asserts `ic_ref == ic32`; with the oracle on, also `== fixture`.
- **Nothing is written into the install.** Caches and projects are external.
