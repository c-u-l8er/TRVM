# TRVM — coordination-free distributed interaction-calculus runtime
# `make test` runs the full conformance battery across every implementation.

CC      ?= gcc
CFLAGS  ?= -O2
PY      ?= python3
NODE    ?= node

IC32    := runtime/c/ic32
WASM    := runtime/wasm/ic32.wasm
PYPATH  := runtime/python:distribution:research

.PHONY: test conformance native wasm-smoke swarm research clean

test: native conformance native-selftest wasm-smoke swarm research
	@echo ""
	@echo "==== TRVM full battery complete ===="

## --- native runtime --------------------------------------------------------
native: $(IC32)

$(IC32): runtime/c/ic32.c
	$(CC) $(CFLAGS) -o $@ $<

native-selftest: native
	@echo "==== [native] ic32 --test ===="
	@$(IC32) --test

## --- portable conformance runner (vectors + §6.1–§6.3) ---------------------
conformance: native
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
	rm -f $(IC32) ic32
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
