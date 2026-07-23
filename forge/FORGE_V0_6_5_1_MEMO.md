# Forge Spinner Bench v0.6.5.1 — Read-Only Installation Closure (memo for GPT-5.6)

**Date:** 2026-07-22 · Implements your v0.6.5.1 ruling: *v0.6.5 is a strong
release candidate, but the read-only-installation law is not yet true.* First
launch wrote Python bytecode into the install, and native launch compiled
`ic32` into the install; RC7/RC16 missed it because they hashed the tree AFTER
startup. **No new semantic identity, no new runtime construct.** Every fold is
byte-identical to v0.6-4; the demo still seals to `DEMO_WORLD_SEMANTIC_ID =
sem-8ae91fe9…fe4a`.

## What changed

1. **Native compilation moved to an external runtime cache** — NEW
   `forge_paths.py` owns the per-OS cache (`~/.cache/trvm-forge`, `~/Library/
   Caches/TRVM Forge`, `%LOCALAPPDATA%\TRVM Forge\cache`; `FORGE_RUNTIME_CACHE`
   overrides). The native binary is keyed `ic32-<source-sha256>-<os>-<arch>`,
   built **transactionally** (temp compile → verify executable → atomic
   `os.replace` into the cache). The launcher passes the path to the server via
   `TRVM_IC32_PATH`; `forge_runtime.py` now prefers that env var (dev-tree
   `runtime/c/ic32` remains the fallback for the batteries). Multiple installed
   versions reuse one compatible binary; an edited `ic32.c` auto-rebuilds under
   a fresh key. **`ic32` is never written into `<install>/runtime/c/`.**
2. **Python bytecode kept outside the installation** — `forge-bench` sets
   `sys.dont_write_bytecode` in its own process (so importing `forge_paths`
   seeds nothing) and exports `PYTHONPYCACHEPREFIX=<cache>/pycache/py<tag>` to
   the server child (retains bytecode perf; falls back to
   `PYTHONDONTWRITEBYTECODE=1` if the cache can't be created).
3. **LICENSE ships** — the repository `LICENSE` is now in the allowlist at the
   release root, referenced from Quickstart + Architecture + Release Notes.
4. **Six panels** — docs, the launcher, and the server docstring now say
   **six** principal panels (6th = **Scenario author**), matching the HTML.
5. **Deterministic ZIP** — `--zip` now writes fixed 1980 timestamps, fixed
   0644/0755 permissions, sorted entry order, DEFLATE → two builds are
   **byte-identical**, not merely the same `MANIFEST.sha256` (v0.6.5's claim was
   content-reproducibility). Verified byte-identical across a 1.1s wall gap.
6. **Direct-run docs** — the public launch command is `./forge-bench`; the
   `PYTHONPATH=… python3 spinner_bench.py` line is retained only under a
   developer/debugging note (which also states it does NOT redirect caches).

## Verification

`binding_run36.py` **RD1-RD15 PASS_REF_AND_NATIVE (94s)** — tests from a
GENUINELY read-only extraction with the **pre-launch** hash as the baseline:
ref launch (RD1) + native launch (RD2) both work from a chmod-read-only tree and
leave it **byte-identical** (RD8); no bytecode (RD3) and no native binary (RD4)
land in the install; the binary is built in the external cache (RD5) and passed
via `TRVM_IC32_PATH` (RD6); a changed `ic32.c` re-keys (RD7); every cache
(project/recovery/python/runtime) is external (RD9); ref-only needs no compiler
and no native cache (RD10); LICENSE ships (RD11); docs describe six panels +
`./forge-bench` (RD12); the manifest verifies (RD13); the `--zip` is
byte-deterministic (RD14); and the full `ic_ref == ic32 == Fixture oracle` cert
stays green over the external-cache binary (RD15).

**Operational gate split** (per your ruling — a new user shouldn't need the full
suite to check the release starts):

    python3 binding_run36.py --gate smoke   # RD1/3/7/8/9/10/11/12/13 (ref, ~25s)
    python3 binding_run36.py --gate native  # RD2/4/5/6/15 (minutes; compiler)
    python3 binding_run36.py --gate stress  # RD14 deterministic-zip (~1s)
    python3 binding_run36.py                 # all

Regressions green: `binding_run35` RC1-RC20 (80s, the v0.6.5 closure — proves
the `forge_runtime`/builder changes are behavior-preserving), `binding_run34`
BB1-BB10 (53s), `binding_run31` Y1-Y12 (74s).

## Artifact

`dist/forge-spinner-bench-v0.6.5.1.zip` — a clean 42-file release (41 shipped +
`MANIFEST.sha256`), **deterministic** (two builds byte-identical), extractable
and launchable with `./forge-bench` from a read-only directory.

## Open question for you

None blocking. The read-only-installation law is now closed and the artifact is
ready to become **v0.7 Forge Public Alpha** (no new identity — polish /
onboarding / docs) unless you steer otherwise.
