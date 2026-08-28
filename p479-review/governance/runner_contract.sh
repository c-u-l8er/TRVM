#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# runner_contract.sh — the runner half of law:evidence.clean-baseline@1,
# executable.
#
# Round 21 found that `cmd | tail -1` takes TAIL's exit status, so a governance
# target whose subject CRASHED printed a stack trace's last line and reported
# success. The derive battery ran broken for two rounds behind that.
#
# This is deliberately NOT a tenth harness species. The nine in
# harness_selftest.sh are about falsifier and instrument NON-VACUITY — whether a
# case perturbs what it claims to. Process-status propagation is a different
# layer: whether the runner can hear the subject at all. Separate contract,
# separate file, three cases, and it stops there.
#
#   success  -> the target succeeds
#   exit 1   -> the target fails
#   crash    -> the target fails
#
# Run: ./runner_contract.sh   (exit 0 iff the runner can hear all three)
# ═══════════════════════════════════════════════════════════════════════════
BASE="$(cd "$(dirname "$0")" && pwd)"
TRVM="$(cd "$BASE/.." && pwd)"
SCRATCH="${SCRATCH:-/tmp/runner-contract}"
rm -rf "$SCRATCH" && mkdir -p "$SCRATCH"
FAILED=0; N=0; OK=0

# A throwaway make target shaped exactly like the governance ones, so this
# tests the RECIPE FORM the real targets use rather than a paraphrase of it.
RECIPE=$(grep -m1 -F 'out=$$($(NODE) derive_battery.mjs)' "$TRVM/Makefile")
if [ -z "$RECIPE" ]; then
  echo "FAIL  the governance recipe form was not found in the Makefile — this contract tests the form"
  echo "      the real targets use, and it cannot do that if it cannot find one"
  exit 1
fi

case_run () {  # name, subject-js, expected-make-status (0 = success, nonzero = failure)
  local name="$1" body="$2" want="$3"
  N=$((N+1))
  local d="$SCRATCH/$name"; mkdir -p "$d"
  printf '%s\n' "$body" > "$d/subject.mjs"
  { printf 'NODE ?= node\nGOV := .\n\ncheck:\n'
    printf '%s\n' "$RECIPE" | sed 's/derive_battery\.mjs/subject.mjs/'
  } > "$d/Makefile"
  ( cd "$d" && make check >/dev/null 2>&1 )
  local got=$?
  local pass
  if [ "$want" = "0" ]; then [ $got -eq 0 ] && pass=1 || pass=0
  else [ $got -ne 0 ] && pass=1 || pass=0; fi
  if [ $pass -eq 1 ]; then
    OK=$((OK+1)); echo "PASS  $name (make exit=$got, wanted $( [ "$want" = 0 ] && echo 0 || echo nonzero ))"
  else
    echo "FAIL  $name (make exit=$got, wanted $( [ "$want" = 0 ] && echo 0 || echo nonzero ))"; FAILED=1
  fi
}

case_run runner-hears-success 'console.log("VERDICT: PASS"); process.exit(0);' 0
case_run runner-hears-exit-1  'console.log("VERDICT: FAIL"); process.exit(1);' 1
# a crash is not exit 1: it writes to stderr and dies, which is what the piped
# form swallowed. The subject prints nothing on stdout at all.
case_run runner-hears-crash   'throw new Error("subject crashed before printing a verdict");' 1

echo
[ $FAILED -eq 0 ] \
  && echo "RUNNER CONTRACT: $N/$N — the runner hears success, failure and crash" \
  || echo "RUNNER CONTRACT: FAILURES PRESENT ($OK/$N)"
exit $FAILED
