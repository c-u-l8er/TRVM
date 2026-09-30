#!/usr/bin/env bash
# The gate: the two law files must check, the two mutants must be refused.
# Prints its own verdict; exit 0 only when all four hold.
set -u
cd "$(dirname "$0")"
export BEND_NO_TELEMETRY=1
BEND="${BEND:-$HOME/.bend/bin/bend}"
export PATH="$HOME/.bun/bin:$PATH"
ok=0; bad=0
check_pass() { out=$("$BEND" "$1" 2>&1); if [ "$out" = "All terms check." ]; then echo "PASS  $1  (All terms check.)"; ok=$((ok+1)); else echo "FAIL  $1  (expected to check)"; echo "$out" | head -8; bad=$((bad+1)); fi; }
check_fail() { out=$("$BEND" "$1" 2>&1); if [ "$out" != "All terms check." ] && echo "$out" | grep -q "^Error:"; then echo "PASS  $1  (refused, as it must be: $(echo "$out" | sed -n 's/^- expected : //p' | head -1 | cut -c1-70))"; ok=$((ok+1)); else echo "FAIL  $1  (a wrong proof was ACCEPTED)"; bad=$((bad+1)); fi; }
echo "bend $("$BEND" --version 2>&1 | head -1 | sed 's/^bend //')"
check_pass PROOF5.bend
check_fail PROOF5_BAD.bend
check_pass PROOF23.bend
check_fail PROOF23_BAD.bend
echo "verdict: $ok/4 hold, $bad failing"
[ "$bad" -eq 0 ]
