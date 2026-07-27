# TRVM — coordination-free distributed interaction-calculus runtime
# `make test` runs the full conformance battery across every implementation.

CC      ?= gcc
CFLAGS  ?= -O2
PY      ?= python3
NODE    ?= node
ZIG     ?= zig
ZIGFLAGS?= -OReleaseFast
# Mojo ships inside a pixi environment (runtime/mojo/pixi.toml). Either a bare `mojo`
# on PATH or a pixi that can materialise one will do; MOJO_RUN resolves at recipe time.
MOJO     ?= mojo
MOJOFLAGS?= -O3
PIXI     ?= pixi

IC32    := runtime/c/ic32
IC32Z   := runtime/zig/ic32z
IC32M   := runtime/mojo/ic32m
WASM    := runtime/wasm/ic32.wasm
PYPATH  := runtime/python:distribution:research

.PHONY: test conformance native native-selftest zig zig-selftest mojo mojo-selftest \
        wasm-smoke swarm research clean

test: native zig mojo conformance native-selftest zig-selftest mojo-selftest \
      wasm-smoke swarm research
	@echo ""
	@echo "==== TRVM full battery complete ===="

## --- native runtime --------------------------------------------------------
native: $(IC32)

$(IC32): runtime/c/ic32.c
	$(CC) $(CFLAGS) -o $@ $<

native-selftest: native
	@echo "==== [native] ic32 --test ===="
	@$(IC32) --test

## --- zig runtime (second conformant backend) -------------------------------
# Soft dependency: a missing Zig toolchain SKIPS the backend, it does not fail the
# build. The conformance runner then reports it as skipped rather than passing — an
# unbuilt backend must be visible, not invisible.
zig:
	@if command -v $(ZIG) >/dev/null 2>&1; then \
	  $(ZIG) build-exe $(ZIGFLAGS) runtime/zig/ic32.zig -femit-bin=$(IC32Z) && \
	  rm -f $(IC32Z).o; \
	else echo "  (zig not found — skipping zig backend)"; fi

zig-selftest: zig
	@echo "==== [zig] ic32z --test ===="
	@if [ -x $(IC32Z) ]; then $(IC32Z) --test; else echo "  (ic32z not built — skipped)"; fi

## --- mojo runtime (third conformant backend) -------------------------------
# Same soft dependency as Zig. Two ways to reach a compiler, tried in order: a bare
# `mojo` on PATH, else pixi driving runtime/mojo/pixi.toml (pixi's own installer puts
# it in ~/.pixi/bin, which is frequently not on a non-login shell's PATH, so look there
# too). Build output is captured and only replayed on failure -- the current nightly
# emits an `alias`-is-deprecated warning per constant, and forty lines of that on every
# `make test` trains people to stop reading the build log.
mojo:
	@if command -v $(MOJO) >/dev/null 2>&1; then \
	  MOJO_RUN="$(MOJO)"; \
	elif command -v $(PIXI) >/dev/null 2>&1; then \
	  MOJO_RUN="$(PIXI) run --manifest-path runtime/mojo/pixi.toml mojo"; \
	elif [ -x "$$HOME/.pixi/bin/pixi" ]; then \
	  MOJO_RUN="$$HOME/.pixi/bin/pixi run --manifest-path runtime/mojo/pixi.toml mojo"; \
	else MOJO_RUN=""; fi; \
	if [ -n "$$MOJO_RUN" ]; then \
	  if ! out=$$($$MOJO_RUN build $(MOJOFLAGS) runtime/mojo/ic32.mojo -o $(IC32M) 2>&1); \
	  then echo "$$out"; exit 1; fi; \
	else echo "  (mojo not found — skipping mojo backend)"; fi

mojo-selftest: mojo
	@echo "==== [mojo] ic32m --test ===="
	@if [ -x $(IC32M) ]; then $(IC32M) --test; else echo "  (ic32m not built — skipped)"; fi

## --- portable conformance runner (vectors + §6.1–§6.3) ---------------------
conformance: native zig mojo
	@echo "==== [conformance] vectors + SPEC §6 batteries ===="
	@$(PY) runtime/python/conformance.py

## --- wasm smoke ------------------------------------------------------------
wasm-smoke:
	@echo "==== [wasm] ic32.wasm via node ===="
	@if command -v $(NODE) >/dev/null 2>&1; then \
	  printf '%s' 'λx.x' | $(NODE) runtime/wasm/wrun.js && echo "  wasm identity OK"; \
	else echo "  (node not found — skipping wasm smoke)"; fi

## --- distributed capstone (real workers) -----------------------------------
swarm:
	@echo "==== [swarm] ic32.wasm coordination-free across worker_threads ===="
	@if command -v $(NODE) >/dev/null 2>&1; then $(NODE) runtime/js/swarm.js | tail -4; \
	else echo "  (node not found — skipping swarm)"; fi

## --- identity/memory result ------------------------------------------------
research:
	@echo "==== [research] merge-is-a-CvRDT (semilattice laws + SEC) ===="
	@PYTHONPATH=$(PYPATH) $(PY) research/semilattice.py | tail -3

## --- wasm rebuild (optional; needs clang-15 + lld-15) ----------------------
wasm:
	bash runtime/wasm/build.sh

clean:
	rm -f $(IC32) ic32 $(IC32Z) $(IC32Z).o $(IC32M)
	rm -rf runtime/zig/.zig-cache
	rm -f runtime/mojo/*.o
	@# runtime/mojo/.pixi/envs is deliberately NOT removed: it is a multi-minute
	@# toolchain download, not a build artifact of this repo.
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
