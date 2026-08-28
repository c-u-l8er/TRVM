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
        governance gov-kernel gov-grid gov-world gov-negative gov-bridge gov-film gov-lower gov-emission gov-strict gov-derive gov-proof gov-harness

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
governance: gov-kernel gov-grid gov-world gov-negative gov-bridge gov-film gov-lower gov-emission gov-derive gov-proof gov-nest gov-harness
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

# THE FAILING CASE MUST SURVIVE THE RECIPE. This read
#   out=$$(./negative_battery.sh) && printf ... | tail -1
# so on a nonzero exit the `&&` short-circuited and the battery's own diagnosis
# was DISCARDED — `make governance` printed `Error 1` and nothing else, and the
# only way to learn which of 377 cases failed was to re-run it by hand. That is
# the gov-proof `| tail` defect (P1, ledger item 410) in its other direction: a
# gate that swallows the reason it failed. Capture, print the failures on
# failure, print the summary on success, and preserve the exit code.
gov-negative:
	@echo "==== [governance] negative battery — every forgery must be caught ===="
	@cd $(GOV) && out=$$(./negative_battery.sh); rc=$$?; \
	  if [ $$rc -ne 0 ]; then printf "%s\n" "$$out" | grep -E "^FAIL|FAILURES PRESENT" | head -20; \
	  else printf "%s\n" "$$out" | tail -1; fi; exit $$rc

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

# Round 27 B3, and DELIBERATELY NOT IN `governance`. The C↔JS float-plane
# measurement diff: both relations run over the whole 24-vector corpus and the
# film fixtures, and the tool reports whether they are the same measurement. It
# is the instrument the conformance round was built ON, not the gate — measure
# first, and only then write down what a test expects. It exits nonzero on
# disagreement, because a comparator that cannot report a difference is a
# display; putting it in the gate would be a different claim than the one it
# makes, which is a measurement and not a theorem.
gov-measure: $(GOV)/bridge/ic32_film $(GOV)/bridge/ic32_canon
	@echo "==== [governance] MEASUREMENT (non-gating) — native float plane vs the JS oracle ===="
	@cd $(GOV) && $(NODE) bridge/measure_compare.mjs
	@echo "==== [governance] MEASUREMENT (non-gating) — B7.1 predecessor and raw Church subtraction ===="
	@cd $(GOV) && $(NODE) measure_pred_sub.mjs

# Round 25. The source language reaches the governed runtime: canonical
# lowering, native execution the host observes, structural decode, and the
# refinement equality — three obligations, six identities, none collapsed. The
# native leg is OBSERVED and not FILM-EVIDENCED for this fixture, and the check
# asserts that refusal rather than working around it.
gov-lower: $(GOV)/bridge/ic32_film $(GOV)/bridge/ic32_canon
	@echo "==== [governance] lowering refinement — source == native target ===="
	@cd $(GOV) && out=$$($(NODE) lowering_check.mjs) && printf "%s\n" "$$out" | tail -1

# Round 27 B6. EMISSION_CONFORMANCE-v1: the compiler relation
# {closed_template -> target_term_sem_id} over a FAMILY of fixtures rather than
# the single witness it had inside gov-lower. Deliberately needs no native
# binary: the transition relation carries its own evidence, and defining the
# emitter's correctness by what its output computes would put the runtime
# inside the compiler's contract.
gov-emission:
	@echo "==== [governance] emission conformance — the compiler relation, over a family ===="
	@cd $(GOV) && out=$$($(NODE) emission_conformance.mjs) && printf "%s\n" "$$out" | tail -1

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
# Round 27 B8.3+. THE FIRST BOUNDED PROOF-PRODUCING WORKLOAD. Three steps and
# they are deliberately three: GENERATE the evidence bundle (needs the native
# runtime, one film per side per case), CHECK it with an aggregate checker that
# re-derives the domain and every receipt, then run the checker's own FORGERIES
# so its PASS means something. A checker nobody has made refuse is a checker
# nobody has tested.
gov-proof: $(GOV)/bridge/ic32_film
	@echo "==== [governance] bounded proof bundle — the chain produces a theorem-shaped artifact ===="
	@cd $(GOV) && out=$$($(NODE) proof_bundle.mjs) && printf "%s\n" "$$out" | tail -4
	@cd $(GOV) && out=$$($(NODE) proof_check.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) proof_forgeries.mjs) && printf "%s\n" "$$out" | tail -1
	@echo "==== [governance] bounded DOMAIN certificate — where the chain must STOP ===="
	@cd $(GOV) && out=$$($(NODE) domain_bundle.mjs) && printf "%s\n" "$$out" | tail -5
	@cd $(GOV) && out=$$($(NODE) domain_check.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) domain_forgeries.mjs) && printf "%s\n" "$$out" | tail -1
# Round P3. THE FIRST COMPOSED PROOF OBJECT, and it runs LAST because its inputs
# are the two artifacts above. Same three steps for the same reason — generate,
# check, forge — but the checker here re-derives NOTHING: it hands each carried
# child to that child's own checker and reasons over two verdicts rather than
# over 138 films. That is the whole claim, and `compose_forgeries.mjs` is where
# it is made to fail.
	@echo "==== [governance] COMPOSED certificate — a verified proof as another proof's evidence ===="
	@cd $(GOV) && out=$$($(NODE) compose_bundle.mjs) && printf "%s\n" "$$out" | tail -4
	@cd $(GOV) && out=$$($(NODE) compose_check.mjs) && printf "%s\n" "$$out" | tail -4
	@cd $(GOV) && out=$$($(NODE) compose_forgeries.mjs) && printf "%s\n" "$$out" | tail -1

# Round P4. NESTED COMPOSITION over a CONTENT-ADDRESSED STORE. It runs after
# gov-proof because it resolves the two artifacts that target generates, and it
# is its own target rather than three more lines inside gov-proof because what
# it gates is a different claim: not "a proof can be evidence" but "a proof can
# NAME its evidence without carrying it, and a name is still not a warrant."
#
# The recipe uses gov-negative's shape rather than gov-proof's. `out=$$(...) &&
# printf` short-circuits on a nonzero exit and throws away the diagnosis, which
# is ledger item 410 in reverse and which P3.1 repaired in exactly one place.
# The other targets above still have it; repairing them is a mechanical sweep
# and is filed, not smuggled into this round.
# P4.5 (E). TWO PROFILES. `gov-spec` is PORTABLE — it needs no native compiler
# and no local producer, so a distributed proof-wire package can run it. The full
# `gov-nest` requires both, because a semantic identity that moved locally is a
# defect and must stay red. A compiler that emits different binary bytes moves
# provenance and complete roots and stays green; that distinction is the point.
.PHONY: gov-spec
gov-spec:
	@echo "==== [governance] PORTABLE spec conformance — no producer, no compiler ===="
	@cd $(GOV) && out=$$($(NODE) spec_release.mjs); rc=$$?; printf "%s\n" "$$out" | tail -1; exit $$rc
	@cd $(GOV) && out=$$($(NODE) jcs_vectors.mjs); rc=$$?; printf "%s\n" "$$out" | tail -1; exit $$rc
	@cd $(GOV) && out=$$($(NODE) spec_vectors.mjs); rc=$$?; printf "%s\n" "$$out" | tail -1; exit $$rc
	@cd $(GOV) && out=$$($(NODE) spec_agreement.mjs); rc=$$?; printf "%s\n" "$$out" | tail -1; exit $$rc
# P4.7. THE BYTES DELIVERED TO THE CLEAN ROOM have an identity of their own.
# `srel` says what the specification MEANS; `bpkg` says which BYTES were sent.
# requirements/open/ is handed to the implementer and excluded from spec_digest
# by construction, so editing it moved nothing at all until this existed.
	@cd $(GOV) && out=$$($(NODE) ../docs/spec/proof-wire/experiment/evidence.mjs --selftest); rc=$$?; printf "%s\n" "$$out" | tail -1; exit $$rc
	@cd $(GOV) && out=$$($(NODE) blind_package.mjs); rc=$$?; printf "%s\n" "$$out" | tail -1; exit $$rc
# P4.6 (C) / P4.7. WHICH release, WHICH bytes, WHICH instrument and WHICH
# subjects the blind experiment is measured over. A run that is not ABORTED or
# COMPLETE against a release the tree has moved past is RED: continuing would
# measure an implementation written against one specification using another.
	@cd $(GOV) && out=$$($(NODE) blind_run.mjs); rc=$$?; printf "%s\n" "$$out" | tail -1; exit $$rc

gov-nest: $(GOV)/bridge/ic32_film
	@echo "==== [governance] NESTED composition — a proof DAG resolved by content address ===="
# P4.1 puts the CAS on canonical wire bytes, so the encoder doing the
# canonicalising has to BE the standard rather than look like it. This runs
# first because everything below it assumes one root names one byte string.
	@cd $(GOV) && out=$$($(NODE) jcs_vectors.mjs); rc=$$?; \
	  printf "%s\n" "$$out" | tail -1; exit $$rc
	@cd $(GOV) && out=$$($(NODE) nest_bundle.mjs); rc=$$?; \
	  printf "%s\n" "$$out" | tail -6; exit $$rc
	@cd $(GOV) && out=$$($(NODE) nest_check.mjs); rc=$$?; \
	  printf "%s\n" "$$out" | tail -4; exit $$rc
# P4.2. The mechanical B6.3 sweep: every field of every record classified and
# PERTURBED, because the twelve before nested_verdict were all found by hand.
# P4.2 (F). The conformance corpus the independent producer will receive, in
# docs/spec/proof-wire/vectors/ beside the normative text — GENERATED, because a
# hand-copied expected value is a number nobody re-derived.
# P4.4 (B). The normative RELEASE: every normative document, the schema, the
# public corpus, the pinned JCS provenance and the holdout COMMITMENT, bound by
# digest. Editing a normative sentence without issuing a revision fails here —
# before this object existed it failed nowhere.
	@cd $(GOV) && out=$$($(NODE) spec_release.mjs); rc=$$?; \
	  if [ $$rc -ne 0 ]; then printf "%s\n" "$$out" | head -14; \
	  else printf "%s\n" "$$out" | tail -1; fi; exit $$rc
	@cd $(GOV) && out=$$($(NODE) spec_vectors.mjs); rc=$$?; \
	  if [ $$rc -ne 0 ]; then printf "%s\n" "$$out" | head -14; \
	  else printf "%s\n" "$$out" | tail -1; fi; exit $$rc
# P4.3 (F). The NORMATIVE schema against the checker's OWN declarations — the
# gate field_audit cannot be, because its denominator is the checker's grammar.
	@cd $(GOV) && out=$$($(NODE) spec_agreement.mjs); rc=$$?; \
	  if [ $$rc -ne 0 ]; then printf "%s\n" "$$out" | head -14; \
	  else printf "%s\n" "$$out" | tail -1; fi; exit $$rc
	@cd $(GOV) && out=$$($(NODE) field_audit.mjs); rc=$$?; \
	  if [ $$rc -ne 0 ]; then printf "%s\n" "$$out" | grep -E "^FAIL" | head -20; \
	  else printf "%s\n" "$$out" | tail -1; fi; exit $$rc
# P4.4 (A). LOCAL end-to-end, and deliberately NOT a conformance claim: it
# asserts semantic identities and internal consistency, and REPORTS the complete
# artifact root rather than demanding this machine reproduce another machine's
# compiler output.
	@cd $(GOV) && out=$$($(NODE) live_dag.mjs); rc=$$?; \
	  printf "%s\n" "$$out" | tail -1; exit $$rc
# P4.6 (C). WHICH release the blind experiment is measured against. This ALSO
# runs in the portable `gov-spec` profile — but `gov-spec` is not part of the
# `governance` target, so gating the pin only there would have left the main gate
# never checking it, which is the same shape as a claim nothing executes.
	@cd $(GOV) && out=$$($(NODE) blind_package.mjs); rc=$$?; \
	  if [ $$rc -ne 0 ]; then printf "%s\n" "$$out" | head -8; \
	  else printf "%s\n" "$$out" | tail -1; fi; exit $$rc
	@cd $(GOV) && out=$$($(NODE) blind_run.mjs); rc=$$?; \
	  if [ $$rc -ne 0 ]; then printf "%s\n" "$$out" | head -8; \
	  else printf "%s\n" "$$out" | tail -1; fi; exit $$rc
# P4.7.7. THE BYTE BOUNDARY BEFORE THE INSTRUMENT. Forty vectors stating the
# evidence reader's two claims: every input it ACCEPTS is read deeply-equal to
# JSON.parse, and the inputs it refuses beyond JSON — duplicate member names,
# unpaired surrogates, invalid UTF-8, trailing content — are the ambiguous ones.
# It runs BEFORE the scorer's own fixture because every artifact below it,
# including that fixture, is now read across this boundary: a reader that were
# wrong would make every refusal underneath it a refusal of something else.
	@cd $(GOV) && out=$$($(NODE) ../docs/spec/proof-wire/experiment/evidence.mjs --selftest); rc=$$?; \
	  if [ $$rc -ne 0 ]; then printf "%s\n" "$$out" | head -12; \
	  else printf "%s\n" "$$out" | tail -1; fi; exit $$rc
# P4.6 (G). THE INSTRUMENT BEFORE THE MEASUREMENT. Three synthetic challenges
# carrying no TRVM value: eight operators arranged to PASS, the same eight
# arranged to FAIL, and three whose observation is ABSENT and must therefore be
# UNRESOLVED. A scorer that returned true unconditionally passes the satisfied
# arm and dies here. Runs on its own line so a failure names itself rather than
# arriving as a holdout failure.
	@cd $(GOV) && out=$$($(NODE) ../docs/spec/proof-wire/experiment/holdout_score_core.mjs --fixture); rc=$$?; \
	  if [ $$rc -ne 0 ]; then printf "%s\n" "$$out" | head -12; \
	  else printf "%s\n" "$$out" | tail -1; fi; exit $$rc
# P4.5 (F). The measurement is built BEFORE the independent implementation
# exists. This run scores the JS adapter against frozen predicates: it proves the
# harness runs and proves nothing about interoperability, which is the Go
# adapter's job. P4.6 (G) put a DOCUMENT between them — the adapter is a separate
# process emitting TRVM-HOLDOUT-OBSERVATION-v1, so a Go adapter enters by exactly
# the path this one does.
# THE LAST LINE IS NOT THE WHOLE ANSWER. `tail -1` printed only HOLDOUT-SCORE and
# swallowed HOLDOUT-HARNESS and HOLDOUT-INTEROP — the two claims P4.7 split apart
# precisely so that "the apparatus ran" and "two implementations agreed" could
# never again be read off one another. A gate that hides the distinction it
# exists to draw is the `| tail` defect wearing a different hat.
# AND `tail -3` SWALLOWED TWO MORE OF THEM AT P4.7.2, which added
# HOLDOUT-COMMITMENT and HOLDOUT-AUTHORITY — the lines that say the secret is the
# committed one and that the run's status is WITNESSED rather than asserted. A
# hand-typed N is the same species as a hand-typed count: it goes stale the
# moment the thing it counts grows. The filter is DERIVED from the claim prefix
# now, so a new HOLDOUT-* line prints because it is one.
	@cd $(GOV) && out=$$($(NODE) holdout_score.mjs); rc=$$?; \
	  if [ $$rc -ne 0 ]; then printf "%s\n" "$$out" | head -12; \
	  else printf "%s\n" "$$out" | grep -E "^HOLDOUT-"; fi; exit $$rc
# P4.7.1. THE CONTROL PLANE IS ATTACKED, NOT DESCRIBED. Ten cases against the
# candidate lifecycle, including the DRY RUN: two agreeing subjects reach
# COMPLETE and one mutated artifact_root that no frozen predicate reads blocks
# it. Runs LAST among the nest gates because it drives the run record through
# every state and restores it; a battery that left the experiment altered would
# have falsified the experiment.
	@cd $(GOV) && out=$$($(NODE) experiment_falsifiers.mjs); rc=$$?; \
	  if [ $$rc -ne 0 ]; then printf "%s\n" "$$out" | grep -E "^  FAIL|^EXPERIMENT" | head -12; \
	  else printf "%s\n" "$$out" | tail -1; fi; exit $$rc
	@cd $(GOV) && out=$$($(NODE) nest_forgeries.mjs); rc=$$?; \
	  if [ $$rc -ne 0 ]; then printf "%s\n" "$$out" | grep -E "^FAIL" | head -20; \
	  else printf "%s\n" "$$out" | tail -1; fi; exit $$rc

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
