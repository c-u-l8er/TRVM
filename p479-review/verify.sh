#!/bin/bash
# Verify this pack from wherever it was extracted. No existing checkout needed.
#   ./verify.sh                     every gate is required; a skip is a PARTIAL
#   ./verify.sh --allow-skip-bridge the native gates may be skipped, and then
#                                   the verdict is PARTIAL and never "green"
#
# Checks MANIFEST.sha256, then RUNS every gate and writes RESULTS.txt from the
# runs themselves. Exits nonzero if any gate fails — this pack is a gate, not a
# transcript, and round 21 is the reason that distinction is in the file name.
#
# Round 23 fixed three things here, all of them the same fault in miniature:
#   · a SKIPPED gate left FAILED=0 and the footer still said "every gate
#     replayed green". A skip is not green. The native gates are required by
#     default now, and --allow-skip-bridge downgrades the verdict rather than
#     hiding the hole.
#   · the prose said "all eighteen gates" and the script ran a different
#     number. The tally below is COUNTED by the runner, so there is no sentence
#     left to keep in sync.
#   · a failed manifest carried on executing the very files whose integrity had
#     just failed. It aborts now.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE" || exit 1
ALLOW_SKIP=0
for a in "$@"; do case "$a" in --allow-skip-bridge) ALLOW_SKIP=1 ;;
  *) echo "unknown option: $a" >&2; exit 2 ;; esac; done
FAILED=0 ATTEMPTED=0 PASSED=0 SKIPPED=0
say () { printf '%s\n' "$*" | tee -a RESULTS.txt; }
: > RESULTS.txt
say "TRVM governance review pack — replayed $(date -u +%Y-%m-%dT%H:%MZ) on node $(node -v 2>/dev/null || echo MISSING)"
say ""

command -v node >/dev/null 2>&1 || { say "FATAL: node not found"; exit 1; }
command -v python3 >/dev/null 2>&1 || { say "FATAL: python3 not found"; exit 1; }

say "── manifest ──────────────────────────────────────────────────────────"
if sha256sum -c MANIFEST.sha256 --quiet 2>/dev/null; then
  say "MANIFEST: all $(grep -c . MANIFEST.sha256) files verify"
else
  # ABORT. Continuing would execute files whose integrity has already failed and
  # report their output as evidence, which is how round 21's pack came to carry
  # a green README over a broken capture.
  say "MANIFEST: FAILED — aborting before running anything"
  sha256sum -c MANIFEST.sha256 2>&1 | grep -v ': OK$' | head -20 | sed 's/^/        /' | tee -a RESULTS.txt >/dev/null
  say ""
  say "REVIEW PACK: ABORTED (manifest integrity)"
  exit 1
fi
say ""
say "── replayed gates (every number below was produced by this run) ───────"

run () {  # label, dir, command...
  local label="$1" dir="$2"; shift 2
  ATTEMPTED=$((ATTEMPTED + 1))
  local out; out=$(cd "$dir" && "$@" 2>&1); local code=$?
  local last; last=$(printf '%s\n' "$out" | tail -1)
  if [ $code -ne 0 ]; then FAILED=1; say "FAIL  $label"; printf '%s\n' "$out" | tail -6 | sed 's/^/        /' | tee -a RESULTS.txt >/dev/null
  else PASSED=$((PASSED + 1)); say "PASS  $label — $last"; fi
}
skip () {  # label, why — a skip is COUNTED, never silently green
  SKIPPED=$((SKIPPED + 1))
  if [ $ALLOW_SKIP -eq 0 ]; then FAILED=1; say "FAIL  $1 — REQUIRED and not run ($2)"
  else say "SKIP  $1 ($2) — verdict downgraded to PARTIAL"; fi
}

run "law kernel"         governance env TRVM_VECTORS=../docs/spec/conformance/vectors/normalize.json node trvm_law_kernel.mjs
run "invariant grid"     governance node grid_check.mjs
run "World"              governance node trvm_world.mjs
run "World receipt"      governance node trvm_world.mjs --check-receipt
# THE SHELL GATES ARE INVOKED THROUGH `bash`, NOT THROUGH THE EXECUTABLE BIT.
# `./negative_battery.sh` needs mode 0755 to have survived being archived and
# unpacked, and it does not always: Python's zipfile.extractall — the obvious
# way to open a .zip when `unzip` is not installed — restores bytes and not
# modes, so all three shell gates came back "Permission denied", printed no
# detail, and the pack reported FAILURES PRESENT over a tree that is green.
# A REVIEWER CANNOT TELL A FALSE RED FROM A REAL ONE WITHOUT DOING THE WORK
# AGAIN, which is the whole cost this pack exists to avoid. The interpreter is
# named, so the bit is not load-bearing.
run "negative battery"   governance bash ./negative_battery.sh
run "harness self-test"  governance bash ./harness_selftest.sh
run "runner contract"    governance bash ./runner_contract.sh
run "derive battery"     governance node derive_battery.mjs
run "realm battery"      governance node derive_realm_battery.mjs
# The GATING probes, from the registry — never a glob and never a second
# hand-typed list. Round 23's first cut globbed probe_*_repro.mjs and reported
# four failures for witnesses that exit nonzero BY DESIGN: they freeze a
# boundary that is declared open, and a witness behaving correctly is not a
# gate failing. The distinction is data, so it is read from the registry.
GATING=$(cd governance && python3 -c "
import json; print(' '.join(json.load(open('artifacts.json'))['gating_probes']))")
for p in $GATING; do run "$(basename "$p" .mjs)" governance node "$p"; done
# EMISSION_CONFORMANCE-v1 runs HERE, outside the gcc block, and that placement
# is the claim: the compiler relation is proved without a native binary. Put it
# beside the film gate and a reviewer without a compiler would see it SKIPPED,
# which would read as "emission conformance needs the runtime" — the exact
# layer collapse the battery exists to refuse. It was missing from this list for
# one build of the pack: the gate shipped, the file shipped, and nothing ran it.
run "emission conformance" governance node emission_conformance.mjs
NONGATING=$(cd governance && ls probe_*_repro.mjs 2>/dev/null | grep -vxF "$(printf '%s\n' $GATING)" | wc -l)
say "note  $NONGATING further probe_*_repro.mjs freeze DECLARED-OPEN boundaries and exit nonzero by"
say "      design; they are witnesses, not gates, and are not run here. artifacts.json says which."
if ! command -v gcc >/dev/null 2>&1; then
  skip "cross-plane bridge" "no gcc"; skip "native semantic film" "no gcc"
elif [ ! -f runtime/c/ic32.c ]; then
  skip "cross-plane bridge" "runtime/c/ic32.c absent"; skip "native semantic film" "runtime/c/ic32.c absent"
else
  if gcc -O2 -o governance/bridge/ic32_canon governance/bridge/ic32_canon.c 2>/dev/null
  then run "cross-plane bridge" governance node bridge/bridge_check.mjs
  else skip "cross-plane bridge" "ic32_canon.c did not compile here"; fi
  if gcc -O2 -o governance/bridge/ic32_film governance/bridge/ic32_film.c 2>/dev/null
  then run "native semantic film"   governance node bridge/film_check.mjs
       run "lowering refinement"    governance node lowering_check.mjs
       # NON-GATING, and run anyway. measure_compare.mjs is the instrument the
       # float-plane round was built on, not part of `make governance`; a
       # reviewer should be able to re-derive the C-vs-JS agreement over the
       # whole corpus rather than read that it held. It exits nonzero on
       # disagreement, so `run` reports it honestly — but a difference here is a
       # MEASUREMENT result and the verdict line below says so.
       run "measurement (non-gating)" governance node bridge/measure_compare.mjs
       # B7.1, and it is the reason `sub` exists in this pack at all. The round
       # was allowed to proceed only because this measurement agreed FIRST:
       # B6.3.1 left open whether a Church predecessor normalises in a linear
       # fragment, and the instruction was to stop and report a disagreement
       # rather than force the construction. A reviewer should be able to
       # re-derive that rather than read that it held. Non-gating, run anyway.
       run "pred/sub measurement (non-gating)" governance node measure_pred_sub.mjs
       # B8.3+, THE BOUNDED PROOF BUNDLE, and it needs the native runtime
       # because each of its 128 chains carries a film the runtime originated.
       # Three steps, and they are three on purpose: GENERATE, CHECK, then run
       # the checker's own FORGERIES. A checker nobody has made refuse is a
       # checker nobody has tested, and its PASS is the fastest gate in the
       # pack — a third of a second over 64 cases — which is exactly the kind
       # of number that means nothing on its own.
       run "proof bundle (generate)"  governance node proof_bundle.mjs
       run "proof bundle (check)"     governance node proof_check.mjs
       run "proof bundle (forgeries)" governance node proof_forgeries.mjs
       # P2 — the bounded DOMAIN certificate. Same three steps, and the third
       # matters more here than it did for P1: a certificate whose refusal cases
       # assert the ABSENCE of downstream evidence is only as good as a checker
       # that has been made to refuse a refusal carrying it.
       run "domain certificate (generate)"  governance node domain_bundle.mjs
       run "domain certificate (check)"     governance node domain_check.mjs
       run "domain certificate (forgeries)" governance node domain_forgeries.mjs
       # P3 — COMPOSITION, and it runs last because its inputs are the two
       # artifacts above. The check is the fastest in the pack for a reason
       # worth stating: it re-derives NOTHING. Each carried child goes to its
       # own protocol's checker and the parent reasons over two verdicts rather
       # than over 138 films — so a reviewer watching the clock is watching the
       # claim. The forgeries are where a citation is made to go stale.
       run "composed certificate (generate)"  governance node compose_bundle.mjs
       run "composed certificate (check)"     governance node compose_check.mjs
       run "composed certificate (forgeries)" governance node compose_forgeries.mjs
       # P4 — NESTED COMPOSITION over a CONTENT-ADDRESSED STORE, and it runs
       # last because its inputs are everything above. What a reviewer should
       # watch here is not the clock but two numbers the check prints: the
       # artifact is a few kilobytes and names megabytes of proof, and its
       # child-checker invocations EXCEED its distinct artifacts. The second is
       # the honest one — the same bytes are verified more than once, because
       # resolving an address is not accepting an artifact and nothing in this
       # tree is entitled to issue a warrant that would make it so.
       run "canonical wire vs RFC 8785"     governance node jcs_vectors.mjs
       run "nested composition (generate)"  governance node nest_bundle.mjs
       run "nested composition (check)"     governance node nest_check.mjs
       run "spec release binding"            governance node spec_release.mjs
       run "spec conformance vectors"        governance node spec_vectors.mjs
       run "spec vs checker agreement"       governance node spec_agreement.mjs
       run "field audit (every field classified)" governance node field_audit.mjs
       run "live end-to-end DAG"            governance node live_dag.mjs
       # P4.6 — WHICH release the blind experiment is measured against, and the
       # SCORER'S OWN FALSIFIER before the scorer is used on anything. The
       # fixture carries no TRVM value at all: eight operators arranged to pass,
       # the same eight arranged to fail, and three that must be UNRESOLVED. A
       # scorer that returned true unconditionally passes the first arm.
       run "blind package (delivered bytes)" governance node blind_package.mjs
       run "blind run selection"            governance node blind_run.mjs
       run "scorer fixture (no TRVM)"       governance node ../docs/spec/proof-wire/experiment/holdout_score_core.mjs --fixture
       run "holdout reveal + score"         governance node holdout_score.mjs
       # THE COUNT IS NOT IN THE LABEL. The battery derives and prints its own
       # tally, and a hand-typed one in the runner is a second number to keep in
       # agreement with it — which is how the published and printed law counts
       # came apart elsewhere in this portfolio.
       run "experiment falsifiers"          governance node experiment_falsifiers.mjs
       run "nested composition (forgeries)" governance node nest_forgeries.mjs
  else skip "native semantic film" "ic32_film.c did not compile here"
       skip "lowering refinement"  "ic32_film.c did not compile here"
       skip "proof bundle (generate)"  "ic32_film.c did not compile here"
       skip "proof bundle (check)"     "ic32_film.c did not compile here"
       skip "proof bundle (forgeries)" "ic32_film.c did not compile here"
       skip "domain certificate (generate)"  "ic32_film.c did not compile here"
       skip "domain certificate (check)"     "ic32_film.c did not compile here"
       skip "domain certificate (forgeries)" "ic32_film.c did not compile here"
       skip "composed certificate (generate)"  "ic32_film.c did not compile here"
       skip "composed certificate (check)"     "ic32_film.c did not compile here"
       skip "composed certificate (forgeries)" "ic32_film.c did not compile here"
       skip "canonical wire vs RFC 8785"     "ic32_film.c did not compile here"
       skip "nested composition (generate)"  "ic32_film.c did not compile here"
       skip "nested composition (check)"     "ic32_film.c did not compile here"
       skip "spec release binding"            "ic32_film.c did not compile here"
       skip "spec conformance vectors"        "ic32_film.c did not compile here"
       skip "spec vs checker agreement"       "ic32_film.c did not compile here"
       skip "field audit (every field classified)" "ic32_film.c did not compile here"
       skip "live end-to-end DAG"            "ic32_film.c did not compile here"
       skip "blind package (delivered bytes)" "ic32_film.c did not compile here"
       skip "blind run selection"            "ic32_film.c did not compile here"
       skip "scorer fixture (no TRVM)"       "ic32_film.c did not compile here"
       skip "holdout reveal + score"         "ic32_film.c did not compile here"
       skip "experiment falsifiers"          "ic32_film.c did not compile here"
       skip "nested composition (forgeries)" "ic32_film.c did not compile here"; fi
fi

say ""
say "checks attempted $((ATTEMPTED + SKIPPED))"
say "         passed  $PASSED"
say "         failed  $((ATTEMPTED - PASSED))"
say "         skipped $SKIPPED"
if [ $FAILED -ne 0 ]; then say "REVIEW PACK: FAILURES PRESENT (see above)"
elif [ $SKIPPED -ne 0 ]; then say "REVIEW PACK: PARTIAL — $SKIPPED gate(s) not run; this is NOT a green replay"
else say "REVIEW PACK: every gate replayed green"; fi
say "Counts above are from THIS run. Nothing in this pack transcribes a number."
exit $FAILED
