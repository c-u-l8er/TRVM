#!/usr/bin/env bash
# The resident host's mutant controls. Each mutant is a textual patch applied to a COPY of the resident directory
# (the checked module and ../experimental are reached through symlinks, so the copy sees the same pinned bytes);
# the harness runs over the copy, and the line printed for the mutant says which cases went red and whether that
# is exactly the set the mutant was written to flip. A patch that does not change its file is a refusal, not a
# control. Exit status is nonzero if the unmutated copy is not green or any mutant's red set is not the expected one.
#   bash controls/run-controls.sh [OUT_DIR]       → OUT_DIR/SUMMARY.txt (default: controls/)
set -u
HERE="$(cd "$(dirname "$0")/.." && pwd)"          # runtime/wasm/resident
WASM="$(cd "$HERE/.." && pwd)"                    # runtime/wasm
OUT="${1:-$HERE/controls}"; mkdir -p "$OUT"
TMP="${TMPDIR:-/tmp}/resident-controls.$$"; trap 'rm -rf "$TMP"' EXIT
SUMMARY="$OUT/SUMMARY.txt"; : > "$SUMMARY"
status=0

# name | file | expected red cases (comma-separated, order-free) | python replacement (old ⇒ new, exact)
run_one() {
  local name="$1" file="$2" expected="$3" old="$4" new="$5"
  rm -rf "$TMP"; mkdir -p "$TMP/wasm"
  cp -r "$HERE" "$TMP/wasm/resident"; rm -rf "$TMP/wasm/resident/controls"
  ln -s "$WASM/ic32_checked.wasm" "$TMP/wasm/ic32_checked.wasm"; ln -s "$WASM/experimental" "$TMP/wasm/experimental"
  if [ "$name" != "unmutated" ]; then
    local target="$TMP/wasm/resident/$file"
    OLD="$old" NEW="$new" python3 - "$target" <<'PY' || { echo "control=$name PATCH-REFUSED (pattern not found exactly once in $file)" | tee -a "$SUMMARY"; status=1; return; }
import os, sys
p = sys.argv[1]; s = open(p).read(); old = os.environ['OLD']; new = os.environ['NEW']
if s.count(old) != 1: sys.exit(1)
open(p, 'w').write(s.replace(old, new))
PY
  fi
  local tap; tap="$(cd "$TMP/wasm/resident" && timeout 180 node --test --test-isolation=none --test-reporter=tap --test-timeout=30000 --test-force-exit resident.test.mjs 2>&1)"
  local exit_code=$?
  local failing; failing="$(printf '%s\n' "$tap" | grep -E '^not ok' | sed -E 's/^not ok [0-9]+ - ([A-Z][0-9]+) .*/\1/' | sort | tr '\n' ',' )"
  local passed; passed="$(printf '%s\n' "$tap" | grep -E '^# pass' | awk '{print $3}')"
  local failed; failed="$(printf '%s\n' "$tap" | grep -E '^# fail' | awk '{print $3}')"
  local want; want="$(printf '%s' "$expected" | tr ',' '\n' | sed '/^$/d' | sort | tr '\n' ',')"
  local verdict
  if [ "$name" = "unmutated" ]; then
    if [ "$exit_code" = 0 ] && [ -z "$failing" ]; then verdict="GREEN"; else verdict="NOT-GREEN"; status=1; fi
  elif [ "$failing" = "$want" ] && [ -n "$failing" ]; then verdict="RED-AS-EXPECTED"; else verdict="UNEXPECTED"; status=1; fi
  echo "control=$name harness_exit=$exit_code (${passed:-?} pass, ${failed:-?} fail; failing: ${failing:-none}) expected: ${want:-none} → $verdict" | tee -a "$SUMMARY"
  printf '%s\n' "$tap" > "$OUT/$name.tap"
}

run_one unmutated - "" "" ""

run_one no-terminate-on-deadline resident.mjs "D1,C2,L1,U1" \
  "    try { await w.worker.terminate(); exited = true; }" \
  "    try { exited = true; }"

run_one no-replace-after-confirmed-exit resident.mjs "D1,C2,W1" \
  "    if (exited) { if (!this.#closed) { this.#stats.replaced++; this.#spawn(); }" \
  "    if (exited) { if (!this.#closed) { this.#stats.replaced++; }"

run_one late-reply-accepted resident.mjs "L1" \
  "    if (performance.now() >= w.job.expires) w.job.settle({ status: 'deadline' }, true);
    else w.job.settle" \
  "    w.job.settle"

run_one unbounded-queue resident.mjs "Q1" \
  "    else if (this.#queue.length < this.#maxQueue) {" \
  "    else if (true) {"

run_one reuse-instance resident-worker.mjs "F1,I1,X1,P1" \
  "    const ex = new WebAssembly.Instance(module, {}).exports;" \
  "    const ex = (globalThis.__ex ??= new WebAssembly.Instance(module, {}).exports);"

run_one skip-digest-check resident.mjs "M1" \
  "  if (digest !== DIGEST) throw Error('module-digest-mismatch');" \
  "  void DIGEST;"

run_one accept-foreign-job-id resident.mjs "R1" \
  "    if (!w.job || m?.id !== w.job.id) return;" \
  "    if (!w.job) return;"

echo "---" | tee -a "$SUMMARY"
if [ "$status" = 0 ]; then echo "ALL CONTROLS AS EXPECTED" | tee -a "$SUMMARY"; else echo "CONTROL MISMATCH" | tee -a "$SUMMARY"; fi
exit $status
