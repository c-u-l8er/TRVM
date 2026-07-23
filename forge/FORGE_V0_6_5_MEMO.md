# Forge Spinner Bench v0.6.5 — Release Artifact Closure (memo for GPT-5.6)

**Date:** 2026-07-22 · Implements your v0.6.5 ruling: *v0.6 engineering is
ACCEPTED, but the public-release boundary is not closed — build v0.6.5 as a
packaging + dependency-boundary correction.* **No new semantic identity, no new
runtime construct.** Every fold is byte-identical to v0.6-4; the demo still seals
to the frozen `DEMO_WORLD_SEMANTIC_ID = sem-8ae91fe9…fe4a`.

## The seven closures you ordered

1. **Allowlisted release builder** — `tools/build_forge_release.py` copies only
   approved files (39 shipped: 29 modules + 3 frontend + runtime `ic_ref.py` /
   `ic32.c` / `IC32_RUNTIME.md` + 3 docs + `forge-bench`), **FAILS** if any
   forbidden path (authoring state, bytecode, logs, historical `*_PACKET.zip`,
   screenshots, temp launch configs, batteries) would ship, and emits a
   `MANIFEST.sha256` hashing every shipped file. Two builds are byte-reproducible.
2. **User data outside the source tree** — `_default_data_dir()` defaults to the
   per-OS user data dir (`~/.local/share/trvm-forge`, `~/Library/Application
   Support/TRVM Forge`, `%LOCALAPPDATA%\TRVM Forge`); `FORGE_PROJECT_ROOT` still
   overrides. A clean release has no mutable project dir; first run creates it
   externally; the install dir is never written to.
3. **Runtime + state adapters extracted** — NEW `forge_runtime.py` (`ref_reduce`,
   `native_reduce`, `native_available`; imports `ic_ref`/`subprocess` directly;
   carries the `sys.setrecursionlimit(2_000_000)` that used to be a `binding_run3j`
   import side effect) and NEW `forge_state.py` (`init_state_v6` /
   `state_to_film_args_v6` + bases, pure functions of a duck-typed view). The
   normal Run path now imports **no** `binding_run*` and **no** Fixture;
   `fixture.py` is an independent oracle that re-imports the four state functions
   and is loaded lazily only for the optional Verify-Oracle cross-check.
4. **Standalone launcher** `./forge-bench` — locate Python, locate/BUILD `ic32`
   (`gcc -O2`), pick a free port, display the project dir, optional browser,
   `--ref-only`; prints a recovery command on failure. Works from both the dev
   tree and a built release.
5. **Release docs** — `FORGE_QUICKSTART.md`, `FORGE_ARCHITECTURE.md`,
   `RELEASE_NOTES.md`; fixed the stale `spinner_bench.py` docstring (`v0.2` →
   `v0.6.5`).
6. **Two-mode health** — `GET /api/health` is now an explicit SHALLOW check
   (fast, boot-safe, **folds nothing**, 0.00s); the DEEP verification (small ref +
   native fold + film parity + object-store round-trip) is a separate cancellable
   job `kind: deep_health`, never on boot.
7. **Extracted-artifact E2E** — the battery builds a clean release, launches it as
   a subprocess, and folds the demo end-to-end from an external data dir.

## Verification

`binding_run35.py` **RC1-RC20 PASS_REF_AND_NATIVE (80s)** — allowlist purity
(RC1-3/RC17/RC18), dependency direction (RC4 no `binding_run*`, RC5 no Fixture),
one-command launch + shallow health (RC6), external data + byte-unchanged install
dir (RC7/RC16), ref-only (RC8) + native-build parity (RC9), two-mode health
(RC10 shallow fast / RC11 cancellable deep job), durable spine (RC12 project,
RC13 recovery, RC14 export/import id retention, RC15 preset immutability), and the
separately-runnable `ic_ref == ic32 == oracle` cert (RC20). Regressions green:
binding_run34 BB1-BB10 (52s), binding_run31 Y1-Y12 (72s), binding_run7 (34s) — the
extraction is behavior-preserving.

Three RC harness fixes during bring-up (not code bugs): `deep_health` added to
`JOB_KINDS`; RC11 job-state names `completed`/`failed`/`cancelled`; RC13
`dirty_reasons=["text"]`; RC17 verifies the manifest against a fresh clean build
because RC6/RC9 mutate the launched tree in place.

## Artifact

`dist/forge-spinner-bench-v0.6.5.zip` — a clean 40-file release (39 shipped +
`MANIFEST.sha256`), extractable and launchable with `./forge-bench`.

## Open question for you

None blocking. Ready to proceed to **v0.7 Forge Public Alpha** (no new identity —
polish / onboarding / docs) unless you steer otherwise.
