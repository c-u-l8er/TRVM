#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# harness_selftest.sh — the apparatus is now measured too.
#
# Five consecutive rounds found a defect in the INSTRUMENT rather than in the
# engine: an unset $SCRATCH so a case could never execute; a hand-typed 44/44;
# a version-lockstep forgery that replaced a literal a bump would have made a
# no-op; a probe line printing "directly assignable" while testing typeof; the
# false "9D-4 confined" from a witness that never entered its own path; a
# non-vacuity law registered one round before the harness implemented it; a
# one-sided diff that called a deletion vacuous; and — round 15 — two reads the
# artifact-root round said it had anchored, one of which scanned the empty
# string and reported success; and — round 17 — a negative battery whose every
# case had been running against a checker that was already red.
#
# That is no longer an occasional bug. It is a recurring threat to the validity
# of every number this tree prints, so the KNOWN FAILURE SPECIES get a gate.
#
# This is deliberately NOT a general test-of-tests. It encodes the NINE shapes
# that have actually gone wrong here, and it stops there. Each meta-case breaks
# an instrument on purpose and requires the harness to SAY SO — except M-9,
# which requires the harness to say NOTHING when nothing is wrong, because a
# contaminated baseline is the one failure a battery of forgeries cannot see.
#
# Run: ./harness_selftest.sh   (exit 0 iff every meta-falsifier is caught)
# ═══════════════════════════════════════════════════════════════════════════
BASE="$(cd "$(dirname "$0")" && pwd)"
SCRATCH="${SCRATCH:-/tmp/harness-selftest}"
rm -rf "$SCRATCH" && mkdir -p "$SCRATCH"
META=0; CAUGHT=0; FAILED=0

meta () {  # name, expectation, actual-output, grep-pattern
  local name="$1" want="$2" out="$3" rx="$4"
  META=$((META+1))
  if echo "$out" | grep -qE "$rx"; then
    CAUGHT=$((CAUGHT+1))
    echo "PASS  $name → $(echo "$out" | grep -m1 -E "$rx" | sed 's/^ *//' | cut -c1-92)"
  else
    echo "FAIL  $name (wanted /$rx/)"; echo "$out" | tail -4 | sed 's/^/        /'; FAILED=1
  fi
}

CASE_INPUTS=$(python3 -c "
import json,re,os
m=json.load(open('$BASE/artifacts.json'))
fs=list(m['case_inputs']) + list(m.get('tools', []))
fs+=sorted(f for f in os.listdir('$BASE') if re.match(m['ledgers_pattern'],f))
print(' '.join(fs))")
mkcase () { local d="$SCRATCH/$1"; rm -rf "$d"; mkdir -p "$d"; for f in $CASE_INPUTS; do cp "$BASE/$f" "$d/"; done; echo "$d"; }

# ── M-1. the checker must not depend on the working directory ───────────────
# Round 15's finding, as a standing gate. The citation scan read whatever sat
# beside the process, and the banned-phrase tripwire scanned the EMPTY STRING
# when its file was absent — reporting clean while measuring nothing.
{
  # asserts IDENTITY of the three runs, not that they pass. The property under
  # test is cwd-independence; if the tree is red, all three must be identically
  # red. Requiring PASS here would make this meta-case fail for reasons that
  # have nothing to do with what it measures — which is its own failure species.
  a=$(cd "$BASE" && node grid_check.mjs 2>&1)
  b=$(cd / && node "$BASE/grid_check.mjs" 2>&1)
  c=$(cd /tmp && TRVM_GOV_ROOT="$BASE" node "$BASE/grid_check.mjs" 2>&1)
  if [ "$a" = "$b" ] && [ "$b" = "$c" ]; then out="IDENTICAL: $(echo "$a" | tail -1)"; else
    out="DIVERGED
  from governance/: $a
  from /:           $b
  from /tmp+ROOT:   $c"; fi
  meta "M-1 cwd-independence" "byte-identical output from three directories" "$out" "^IDENTICAL:"
}

# ── M-2. a declared artifact that is absent must fail LOUDLY ────────────────
{
  d=$(mkcase m2); rm "$d/refinement_receipt.json"
  meta "M-2 missing-artifact" "loud failure" "$(cd "$d" && node grid_check.mjs 2>&1)" "artifact missing: refinement_receipt.json"
}

# ── M-3. an artifact present but undeclared must fail ──────────────────────
# The silent direction: an undeclared file is never copied into a case and is
# therefore never tested, while the roster keeps counting.
{
  d=$(mkcase m3); echo '{"smuggled": true}' > "$d/extra_artifact.json"
  meta "M-3 undeclared-artifact" "coverage refusal" "$(cd "$d" && node grid_check.mjs 2>&1)" "present but UNDECLARED"
}

# ── M-4..M-7. the negative battery's own instrument checks ─────────────────
# One scratch battery carrying four deliberately-broken cases. Reusing the real
# runner rather than reimplementing it: a self-test that reimplements the thing
# it tests measures its own copy.
{
  d=$(mkcase m47); cp "$BASE/negative_battery.sh" "$d/"
  python3 - "$d" <<'PY'
import sys, re
d = sys.argv[1]
src = open(d + "/negative_battery.sh").read()
# split at the first INVOCATION, not at the function definition — `run_case () {`
# also starts with "run_case ", and splitting there produced a battery whose
# runner was undefined. Found by running this self-test, which is the point.
head = src[:re.search(r"^run_case [^(]", src, re.M).start()]
tail = '\necho; [ $FAILED -eq 0 ] && echo "META BATTERY: $CASES/$CASES" || echo "META BATTERY: FAILURES ($CAUGHT/$CASES)"\nexit $FAILED\n'

cases = r'''
# M-4 VACUOUS: a forgery that forges nothing. The roster would still count it.
run_case meta-vacuous "artifact_roots missing" "
pass"

# M-5 DELETION: the detector's own first defect was a one-sided diff that could
# not see a removed file and reported a deleting case as vacuous.
run_case meta-deletion "artifact missing: kappa_witnesses.mjs" "
import os
os.remove('kappa_witnesses.mjs')"

# M-6 TARGET MISMATCH: the script declares one target and moves two. The extra
# write is hidden behind a variable so intended_targets cannot see it, which is
# exactly how an accidental extra edit would look.
run_case meta-wrong-target "artifact_roots missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['artifact_roots']
json.dump(g, open('invariant-grid.json','w'), indent=1)
other = 'refinement_receipt.json'
open(other,'a').write(' ')"

# M-7 WRONG DIAGNOSTIC: a real forgery whose expected reason is not the one the
# checker gives. The case must fail rather than pass on any nonzero exit.
run_case meta-wrong-diagnostic "the moon is made of cheese" "
import json
g = json.load(open('invariant-grid.json'))
del g['artifact_roots']
json.dump(g, open('invariant-grid.json','w'), indent=1)"
'''
open(d + "/meta_battery.sh", "w").write(head + cases + tail)
PY
  chmod +x "$d/meta_battery.sh"
  out=$(cd "$d" && SCRATCH="$SCRATCH/m47cases" ./meta_battery.sh 2>&1)
  meta "M-4 vacuity-detected"     "VACUOUS"         "$out" "meta-vacuous \(VACUOUS"
  meta "M-5 deletion-detected"    "deletion is a change" "$out" "PASS  meta-deletion"
  meta "M-6 wrong-target-caught"  "TARGET MISMATCH" "$out" "meta-wrong-target \(TARGET MISMATCH"
  meta "M-7 wrong-diagnostic"     "case must fail"  "$out" "FAIL  meta-wrong-diagnostic \(exit=1"
}

# ── M-8. a paired probe must fail if EITHER side is broken ─────────────────
# The reason the derive probes are paired at all: a one-directional repro passes
# just as happily when the frozen copy is quietly replaced with the repaired
# one, at which point it documents nothing and still prints a number.
{
  d="$SCRATCH/m8"; rm -rf "$d"; mkdir -p "$d"
  cp "$BASE/derive_protocol.mjs" "$BASE/derive_worker.mjs" "$BASE/probe_derivegrant_v02_repro.mjs" "$d/"
  # repair the FROZEN copy — the witness now has nothing to witness
  python3 - "$d" <<'PY'
import sys
d = sys.argv[1]
p = d + "/probe_derivegrant_v02_repro.mjs"
s = open(p).read()
# The repair has to actually neutralise the witness. The first draft of this
# meta-case emptied the frozen `reads` table, and W-1 kept reproducing — because
# W-1 never performs a read: it reaches the grant table through the `input` op,
# since v0.1.0 carried the table INSIDE canonical_inputs. Stripping __reads from
# the inputs is the repair; the earlier one was a meta-case testing nothing,
# caught by this self-test failing on its own first draft.
s = s.replace("const out = evaluate(ast, reader, req.canonical_inputs);",
              "const { __reads: _gone, ...safe } = req.canonical_inputs;\n"
              "    const out = evaluate(ast, reader, safe);")   # frozen copy silently repaired
open(p, "w").write(s)
PY
  out=$(cd "$d" && node probe_derivegrant_v02_repro.mjs 2>&1)
  meta "M-8 vacuous-frozen-side" "VACUOUS" "$out" "VACUOUS: W-1 frozen"
}

# ── M-9. an UNPERTURBED case tree must pass ───────────────────────────────
# Round 17's find, and the most embarrassing of the nine: artifacts.json
# declares `tools` as well as `case_inputs`, grid_check requires every DECLARED
# artifact to exist, and the case tree only ever copied case_inputs. So four
# unrelated failures preceded every forgery since round 14. Each case still
# found its own diagnostic, so nothing was falsely green — but a checker that is
# already failing is not measuring what a negative case believes it is, and the
# only way to notice was to read output nobody had reason to read.
{
  d=$(mkcase m9)
  out=$(cd "$d" && node grid_check.mjs 2>&1; echo "EXIT=$?")
  meta "M-9 clean-case-baseline" "no forgery, no failures" "$out" "EXIT=0"
}

echo
[ $FAILED -eq 0 ] \
  && echo "HARNESS SELFTEST: $META/$META known apparatus failure species caught" \
  || echo "HARNESS SELFTEST: FAILURES PRESENT ($CAUGHT/$META caught)"
exit $FAILED
