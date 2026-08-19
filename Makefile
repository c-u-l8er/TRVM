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
GOV     := governance
# The evidence plane reads the ONE canonical corpus; the embedded copy in the
# kernel is a fallback, and both commit to the same hash by corpus projection.
VECTORS := ../docs/spec/conformance/vectors/normalize.json

.PHONY: test conformance native native-selftest zig zig-selftest mojo mojo-selftest \
        wasm-smoke swarm research clean \
        governance gov-kernel gov-grid gov-world gov-negative gov-bridge gov-film gov-lower gov-strict gov-derive gov-harness

test: native zig mojo conformance native-selftest zig-selftest mojo-selftest \
      wasm-smoke swarm research governance
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

## --- evidence / law plane --------------------------------------------------
# The execution plane above computes; this plane identifies, constrains, and
# proves. They meet at the canonical corpus (same 24 vectors, same committed
# hash) and, since round 10, at canonical semantic bytes. A runtime change that
# moved semantics would now fail here rather than pass quietly.
# EVERY LINE BELOW CAPTURES BEFORE IT PRINTS. `cmd | tail -1` takes the exit
# status of TAIL, not of cmd, so a gate that CRASHED printed a stack trace's
# last line and the target stayed green -- which is how the derive battery ran
# broken for a full round after the envelope split. A gate that cannot fail is a
# display. law:evidence.clean-baseline@1 is about the fixture; this is the same
# disease in the runner.
governance: gov-kernel gov-grid gov-world gov-negative gov-bridge gov-film gov-lower gov-derive gov-harness
	@echo "  evidence plane green"

gov-kernel:
	@echo "==== [governance] law kernel — conformance + the periodic-law grid ===="
	@cd $(GOV) && out=$$(TRVM_VECTORS=$(VECTORS) $(NODE) trvm_law_kernel.mjs) && printf "%s\n" "$$out" | tail -2

gov-grid:
	@echo "==== [governance] invariant grid — registry, citations, engine-free receipts ===="
	@cd $(GOV) && $(NODE) grid_check.mjs

gov-world:
	@echo "==== [governance] World — warrants, maintenance, confinement ===="
	@cd $(GOV) && out=$$($(NODE) trvm_world.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && $(NODE) trvm_world.mjs --check-receipt

gov-negative:
	@echo "==== [governance] negative battery — every forgery must be caught ===="
	@cd $(GOV) && out=$$(./negative_battery.sh) && printf "%s\n" "$$out" | tail -1

gov-bridge: $(GOV)/bridge/ic32_canon
	@echo "==== [governance] cross-plane bridge — C canonical bytes vs the JS oracle ===="
	@cd $(GOV) && $(NODE) bridge/bridge_check.mjs

# The execution plane emitting the evidence plane's canonical bytes. ic32.c is
# included verbatim with its main renamed — the runtime under test is the
# runtime that ships.
$(GOV)/bridge/ic32_canon: $(GOV)/bridge/ic32_canon.c runtime/c/ic32.c
	$(CC) $(CFLAGS) -o $@ $<

# Round 23. For twenty-two rounds every semantic film in the tree was MADE by
# the law kernel: the C runtime could say what state it was in and could not say
# that it had moved. This emits a frame from ic32's own execution and hands it to
# the kernel's OWN replaySemFilm. ic32_film.c #includes ic32_canon.c under
# IC32_CANON_NO_MAIN, so the canonicalizer beneath the film is the same code the
# 48/48 bridge replays rather than a copy written for the occasion.
gov-film: $(GOV)/bridge/ic32_film
	@echo "==== [governance] native semantic film — C originates the evidence ===="
	@cd $(GOV) && out=$$($(NODE) bridge/film_check.mjs) && printf "%s\n" "$$out" | tail -1

$(GOV)/bridge/ic32_film: $(GOV)/bridge/ic32_film.c $(GOV)/bridge/ic32_canon.c runtime/c/ic32.c
	$(CC) $(CFLAGS) -o $@ $<

# Round 25. The source language reaches the governed runtime: canonical
# lowering, native execution the host observes, structural decode, and the
# refinement equality — three obligations, six identities, none collapsed. The
# native leg is OBSERVED and not FILM-EVIDENCED for this fixture, and the check
# asserts that refusal rather than working around it.
gov-lower: $(GOV)/bridge/ic32_film $(GOV)/bridge/ic32_canon
	@echo "==== [governance] lowering refinement — source == native target ===="
	@cd $(GOV) && out=$$($(NODE) lowering_check.mjs) && printf "%s\n" "$$out" | tail -1

# Release / pack-cut gate. CONF-2 may report NOT_APPLICABLE for a standalone
# oracle whose corpus file is absent — equality is then UNKNOWN, not agreed. An
# artifact that leaves the repository must never be cut from such a run, so this
# target makes an unreachable corpus fatal. Not part of `make test`, which is a
# development gate; this is the emission gate.
gov-strict:
	@echo "==== [governance] STRICT corpus identity — release / pack-cut gate ===="
	@cd $(GOV) && out=$$(TRVM_STRICT_CORPUS=1 TRVM_VECTORS=$(VECTORS) $(NODE) trvm_law_kernel.mjs) && printf "%s\n" "$$out" | tail -1

# law:evidence.harness-selftest@1 — six consecutive rounds found the defect in
# the INSTRUMENT rather than the engine, so the known failure species get a gate
# of their own. Bounded on purpose: nine enumerated shapes, and no recursion
# into tests of tests.
gov-harness:
	@echo "==== [governance] harness self-test — the apparatus is measured too ===="
	@cd $(GOV) && out=$$(./harness_selftest.sh) && printf "%s\n" "$$out" | tail -1
# law:evidence.clean-baseline@1, runner half — separate from the bounded nine
	@cd $(GOV) && out=$$(./runner_contract.sh) && printf "%s\n" "$$out" | tail -1

# The replacement for the falsified arbitrary-closure derivation API: program
# as data, canonical request/result, and a real worker crossing where structured
# cloning refuses callables outright.
gov-derive: $(GOV)/bridge/ic32_film
	@echo "==== [governance] serialized derivation boundary ===="
	@cd $(GOV) && out=$$($(NODE) derive_battery.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) derive_realm_battery.mjs) && printf "%s\n" "$$out" | tail -1
# The only PAIRED probe in the tree, and the only one that gates. Its siblings
# freeze a boundary that is DECLARED open, so they report a breach and that is
# the record. These two defects are repaired, so the probe runs each witness
# against the frozen v0.1.0 copy — where it must still reproduce, or the witness
# has gone vacuous and stopped measuring — and against live, where it must be
# confined. law:evidence.instrument-nonvacuity@1 applied to a repro.
	@cd $(GOV) && out=$$($(NODE) probe_derivegrant_v02_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_coresem_v03_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_stalegrant_v03_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_issuebind_v05_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_traceforge_v06_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_execclaim_v07_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_execreg_v08_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_execlaunch_v09_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_semoracle_v10_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_hostown_v11_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_snapshot_v12_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_reread_v13_repro.mjs) && printf "%s\n" "$$out" | tail -1

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
