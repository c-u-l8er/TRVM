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
# Round 23: subdir artifacts too — grid_check asserts invariants on bridge/*,
# and a flat case tree fails the CLEAN BASELINE (M-9) before any perturbation.
# The same one-line omission in negative_battery.sh and here, found the same way.
fs+=list(m.get('subdir_case_inputs', []))
fs+=list(m.get('gating_probes', []))
print(' '.join(fs))")
# v1.24: grid_check reads ../Makefile and used to SKIP its two recipe checks
# when it was absent — a checker reporting clean while measuring nothing.
# The case trees live at $SCRATCH/<case>, so one copy at $SCRATCH/Makefile
# serves every case and makes absence a failure rather than a pass.
mkdir -p "$SCRATCH" && cp "$BASE/../Makefile" "$SCRATCH/Makefile" 2>/dev/null || true
# THE NORMATIVE SPEC TRAVELS WITH A CASE TREE. grid_check reads the frozen
# conformance corpus and the normative schema from ../docs/spec/proof-wire at
# P4.3; a synthetic case without them makes both probes answer false, and a
# gate reporting a defect for its own missing fixture is the species this
# whole file exists to catch. Same reason tools joined CASE_INPUTS.
mkcase () { local d="$SCRATCH/$1"; rm -rf "$d"; mkdir -p "$d"; for f in $CASE_INPUTS; do mkdir -p "$d/$(dirname "$f")"; cp "$BASE/$f" "$d/$f"; done; mkdir -p "$d/../docs/spec" 2>/dev/null || true; cp -r "$BASE/../docs/spec/proof-wire" "$d/../docs/spec/" 2>/dev/null || true; rm -rf "$d/../docs/spec/proof-wire/vectors/public/cas" 2>/dev/null || true; echo "$d"; }

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
  # The tree is the DECLARED case-input tree, not a hand-typed three-file copy.
  # Round 24 moved launching into observed_execution_host.mjs, derive_protocol
  # began importing it, and this meta-case broke on a missing module — because
  # its list was maintained by hand. A fourth hand-maintained copy of "which
  # files does this need" is a fourth place for it to drift.
  d=$(mkcase m8)
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

# ── M-10. a phase-pinned LIVE target ───────────────────────────────────────
# HISTORY MAY BE PINNED. LIVE STATE MUST BE DERIVED.
#
# The tenth species, and it is here because it repeated four times in two
# rounds: an assertion pinned to `implemented === false` outlived the phase; the
# negative case guarding it forged the opposite and expected the stale value, so
# the battery ENFORCED the lie while printing 298/298; grid_check selected the
# canonical law by `revision === 3` and was hand-edited on every supersession;
# and three battery cases did the same, then went on mutating a superseded
# revision nothing asserts over.
#
# WHY IT NEEDS ITS OWN GUARD: every other check in run_case is blind to it. The
# case is not VACUOUS — a superseded revision still exists, so the mutation
# really changes the file. Its TARGET matches. The clean baseline is clean. It
# has simply stopped testing the thing it names, and the only two outcomes are a
# failure that reads like an engine defect, or silence when a neighbouring
# assertion happens to catch the mutation anyway.
#
# This meta-case proves all three parts: the blindness is real, the lint sees
# it, and the history exemption is not decorative.
{
  d=$(mkcase m10)
  # (a) THE BLINDNESS, MEASURED RATHER THAN ASSERTED. Apply a live-pinned
  #     mutation — one selecting the canonical law by its CURRENT number — and
  #     show that the file really changed. run_case's vacuity and target
  #     guards both pass on this, which is the whole problem.
  pinned=$(python3 - "$d" <<'PY'
import json, sys
d = sys.argv[1]
g = json.load(open(d + "/invariant-grid.json"))
ents = g["law_registry"]["entries"]
canon = next(e for e in ents if e["id"] == "film.native-emission" and e.get("canonical"))
n = canon["revision"]
before = json.dumps(g, sort_keys=True)
# the case a session would write TODAY, pinned to today's canonical number
for e in ents:
    if e["id"] == "film.native-emission" and e["revision"] == n:
        e["statement"] = "weakened"
after = json.dumps(g, sort_keys=True)
# now SIMULATE THE NEXT ROUND: canonicity moves to a new revision, and the
# pinned case goes on mutating a revision nothing asserts over.
g2 = json.load(open(d + "/invariant-grid.json"))
e2 = g2["law_registry"]["entries"]
c2 = next(e for e in e2 if e["id"] == "film.native-emission" and e.get("canonical"))
c2["canonical"] = False
bumped = dict(c2); bumped["revision"] = n + 1; bumped["canonical"] = True
e2.append(bumped)
b0 = json.dumps(g2, sort_keys=True)
for e in e2:
    if e["id"] == "film.native-emission" and e["revision"] == n:   # the SAME pinned selector
        e["statement"] = "weakened"
b1 = json.dumps(g2, sort_keys=True)
still_mutates = b0 != b1
hits_canonical = any(e.get("canonical") and e["statement"] == "weakened" for e in e2
                     if e["id"] == "film.native-emission")
print(f"{n} {before != after} {still_mutates} {hits_canonical}")
PY
)
  set -- $pinned
  # today: mutates AND hits the canonical law. after the bump: still mutates
  # (so nothing existing objects) and no longer touches the canonical law.
  blind="revN=$1 today_mutates=$2 after_bump_mutates=$3 after_bump_hits_canonical=$4"
  meta "M-10a phase-pin-goes-blind-and-nothing-notices" "still mutates, no longer canonical" \
    "$blind" "today_mutates=True after_bump_mutates=True after_bump_hits_canonical=False"

  # (b) THE LINT SEES IT. Same case body, handed to the apparatus guard.
  cat > "$d/.m10_live.py" <<'PY'
for e in g['law_registry']['entries']:
    if e['id'] == 'film.native-emission' and e['revision'] == 4:
        e['statement'] = 'weakened'
PY
  out=$(python3 "$BASE/phase_pin_lint.py" "$d/.m10_live.py" "must be the LATEST" 2>&1; echo "EXIT=$?")
  meta "M-10b lint-refuses-a-live-phase-pin" "refused" "$out" "revision-selected-by-number"

  # (c) THE EXEMPTION IS REAL. A case whose subject genuinely IS history must
  #     still be allowed to pin it — otherwise the rule would force nine
  #     history cases to stop testing history, which is the same defect
  #     pointing the other way.
  { echo "# HISTORY_PIN_OK: subject is @1, kept as history"; cat "$d/.m10_live.py"; } > "$d/.m10_hist.py"
  out=$(python3 "$BASE/phase_pin_lint.py" "$d/.m10_hist.py" "must be the LATEST" 2>&1; echo "EXIT=$?")
  meta "M-10c history-pin-exemption-honoured" "EXIT=0" "$out" "EXIT=0"

  # (d) AND THE LINT MUST NOT REPORT CLEAN ON A SUBJECT IT CANNOT READ — M-1's
  #     species inside the instrument that was added to catch a different one.
  out=$(python3 "$BASE/phase_pin_lint.py" "$d/.m10_absent.py" "anything" 2>&1; echo "EXIT=$?")
  meta "M-10d lint-unreadable-subject-is-not-clean" "EXIT=1" "$out" "refusing to report clean"

  # (e) THE POLARITY HALF. `must stay false` is the expectation shape that made
  #     the negative battery enforce a stale record for four passes.
  echo "g['x'] = False" > "$d/.m10_pol.py"
  out=$(python3 "$BASE/phase_pin_lint.py" "$d/.m10_pol.py" "implemented must stay false" 2>&1; echo "EXIT=$?")
  meta "M-10e lint-refuses-a-pinned-polarity" "refused" "$out" "polarity-pinned-expectation"
}

echo
[ $FAILED -eq 0 ] \
  && echo "HARNESS SELFTEST: $META/$META known apparatus failure species caught" \
  || echo "HARNESS SELFTEST: FAILURES PRESENT ($CAUGHT/$META caught)"
exit $FAILED
