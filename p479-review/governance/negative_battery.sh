#!/bin/bash
# Round-5 negative battery: 4 cert-layer forgeries (engine-free) + 7 registry/
# phrase/citation regressions (the six round-4 cases, with ref_coherent now
# tested at BOTH its targets — grid kernel_evidence and certificate evidence).
# Runs against the artifact set in this script's own directory; every case
# must make grid_check exit nonzero with the expected diagnostic.
# Each case: scratch copy of the full tree, one forgery, grid_check MUST exit nonzero
# with a reason matching the expected pattern.
BASE="$(cd "$(dirname "$0")" && pwd)"
# Scratch root for every case. This was previously spelled out in run_case and
# left UNSET in run_case_engine, so the one engine-mode case tried to mkdir at
# the filesystem root and could never execute in a clean shell — it reported
# FAIL for want of an out.txt while the forgery it targets was being refused
# correctly all along. Named once, defaulted, and asserted per case below.
SCRATCH="${SCRATCH:-/tmp/neg5}"
# The case input set is DECLARED in artifacts.json, not hand-maintained here.
# Both runners use the same list: run_case_engine previously omitted
# maintenance_receipt.json for no stated reason, which is exactly the kind of
# silent divergence between two copies of a list that this replaces.
# case_inputs AND tools: grid_check requires every DECLARED artifact to exist,
# so a case tree carrying only case_inputs made the checker report four
# unrelated failures before any forgery was applied. Every case then found its
# expected diagnostic among noise, and an unperturbed tree did not pass — which
# is a contaminated instrument, not a passing one. Since round 14. Found by
# adding a case whose expected pattern did not match and reading what else was
# in the output.
CASE_INPUTS=$(python3 -c "
import json,re,os
m=json.load(open('$BASE/artifacts.json'))
fs=list(m['case_inputs']) + list(m.get('tools', []))
fs+=sorted(f for f in os.listdir('$BASE') if re.match(m['ledgers_pattern'],f))
# Round 23: subdir artifacts too. grid_check asserts invariants on bridge/*, and
# a flat case tree made the UNPERTURBED baseline fail on four absent files.
fs+=list(m.get('subdir_case_inputs', []))
fs+=list(m.get('gating_probes', []))
print(' '.join(fs))")
# law:evidence.instrument-nonvacuity@1 — the mechanised half.
# A per-file digest, not a whole-tree one: "something changed" is weaker than
# "the intended target changed", and the law says target. changed_files() names
# what the perturbation actually moved, so a case that edits the wrong artifact
# is as visible as one that edits nothing.
file_digests () { ( cd "$1" && find . -type f | sed "s|^\./||" | sort | while read -r f; do printf "%s %s\n" "$(sha256sum "$f" | cut -d" " -f1)" "$f"; done | sort ); }
# Symmetric difference, not one-sided: a case that DELETES an artifact removes a
# line from the "after" set, which a one-sided comm cannot see. The first draft
# used comm -13 and duly reported refine-receipt-missing — a case that deletes
# refinement_receipt.json — as VACUOUS. The non-vacuity detector's own first
# defect was a vacuity blind spot, found by running it. Recorded rather than
# quietly fixed, because that is the law's whole point.
changed_files () { { printf "%s\n" "$1"; printf "%s\n" "$2"; } | sort | uniq -u | awk "{print \$2}" | sort -u | tr "\n" "," | sed "s/,$//"; }

# law:evidence.instrument-nonvacuity@1 clause 1 — the INTENDED target.
# "Something changed" is weaker than "the intended thing changed". The target is
# derived from the perturbation script itself (files opened for writing, files
# removed) and compared against what actually moved, so a case that edits the
# wrong artifact — or edits an extra one by accident — fails as loudly as one
# that edits nothing. Declaration and effect are checked against each other
# rather than either being trusted alone.
intended_targets () { python3 -c "
import re,sys
py = sys.argv[1]
t  = set(re.findall(r\"open\\(['\\\"]([^'\\\"]+)['\\\"]\\s*,\\s*['\\\"]w\", py))
t |= set(re.findall(r\"os\\.remove\\(['\\\"]([^'\\\"]+)\", py))
print(','.join(sorted(t)))" "$1"; }

# law:evidence.clean-baseline@1 — the phase this runner did not have.
# A perturbation-based result is admissible only if the IDENTICAL verifier,
# fixture, environment and artifact set satisfy their DECLARED baseline before
# the perturbation is applied. This runner's declared baseline is: grid_check
# exits 0 on the unperturbed fixture. Between round 14 and round 17 it did not,
# and every case found its diagnostic among four unrelated failures — nothing
# was falsely green, but no case was isolated-cause evidence either.
#
# The baseline is established ONCE, because every case builds its fixture from
# the same source by the same recipe. That is verified rather than assumed: each
# case compares its own pre-perturbation digest against the baselined tree, so a
# fixture that drifts is a FIXTURE DRIFT failure rather than a silent difference.
# v1.24: grid_check reads ../Makefile and used to SKIP its two recipe checks
# when it was absent — a checker reporting clean while measuring nothing.
# The case trees live at $SCRATCH/<case>, so one copy at $SCRATCH/Makefile
# serves every case and makes absence a failure rather than a pass.
# THE NORMATIVE SPEC TRAVELS WITH EVERY CASE. grid_check reads the frozen
# conformance corpus and the normative schema from ../docs/spec/proof-wire, and
# a case tree without them makes both P4.3 probes answer false — which is a gate
# reporting a defect for its own missing fixture. Same class as the four
# "artifact missing" reports that put tools into CASE_INPUTS in the first place.
# PER-CASE, NOT SHARED. grid_check resolves the spec tree as ../docs from the
# case root, so one copy at $SCRATCH/docs would be written by any case that
# mutates a normative file and READ by every case after it — a forgery leaking
# into its neighbours, which is the cross-contamination species run_case exists
# to prevent. Each case root is $SCRATCH/<case>/gov, so ../docs is its own.
copy_spec_tree() {
  local d="$1"
  mkdir -p "$d/../docs/spec" 2>/dev/null || true
  cp -r "$BASE/../docs/spec/proof-wire" "$d/../docs/spec/" 2>/dev/null || true
  # WITHOUT THE CAS FIXTURES. grid_check reads the release, the normative
  # documents, the schema and the corpus MANIFEST -- never the leaf artifacts,
  # which are 1.27 MB each. Copying them into all 392 cases put 3.3 GB into a
  # 16 GB tmpfs and produced nothing: exactly the half-gigabyte-per-run cost
  # artifacts.json's own note gives as the reason proof_bundle.json is declared
  # generated_evidence rather than a case input. Staging a fixture per case is
  # right; staging a megabyte of it that nothing reads is not.
  rm -rf "$d/../docs/spec/proof-wire/vectors/public/cas" 2>/dev/null || true
  # AND THE MAKEFILE, for the same reason: grid_check reads ../Makefile to
  # cross-check the gating list, and moving the case root one level deeper for
  # spec isolation moved that out from under it. It reported "../Makefile
  # absent, so the recipe checks scanned nothing and passed vacuously" — a gate
  # correctly announcing its own missing fixture, which is why it is a message
  # and not a silent pass.
  cp "$BASE/../Makefile" "$d/../Makefile" 2>/dev/null || true
}

mkdir -p "$SCRATCH" && cp "$BASE/../Makefile" "$SCRATCH/Makefile" 2>/dev/null || true
BASELINE_DIGEST=""
establish_baseline () {
  local d=$SCRATCH/__baseline/gov
  rm -rf "$d" && mkdir -p "$d"
  for f in $CASE_INPUTS; do mkdir -p "$d/$(dirname "$f")" && cp "$BASE/$f" "$d/$f"; done
  copy_spec_tree "$d"
  local out; out=$(cd "$d" && node grid_check.mjs 2>&1); local code=$?
  if [ $code -ne 0 ]; then
    echo "FAIL  BASELINE (the unperturbed fixture does not pass; no case below is isolated-cause evidence)"
    echo "$out" | grep -E "^ -" | head -6 | sed "s/^/        /"
    FAILED=1; return 1
  fi
  BASELINE_DIGEST=$(file_digests "$d"; file_digests "$d/../docs" 2>/dev/null || true)
  echo "BASELINE  grid_check exits 0 on the unperturbed fixture ($(echo "$BASELINE_DIGEST" | wc -l) artifacts)"
}

run_case () {  # name, expected-grep, setup-script(python)
  local name="$1" want="$2" py="$3"
  local d=$SCRATCH/$name/gov
  rm -rf "$d" && mkdir -p "$d"
  for f in $CASE_INPUTS; do mkdir -p "$d/$(dirname "$f")" && cp "$BASE/$f" "$d/$f"; done
  copy_spec_tree "$d"
  # law:evidence.instrument-nonvacuity@1 — a forgery that forges NOTHING is
  # vacuous, and a vacuous falsifier is worse than an absent one because the
  # roster still counts it. Six apparatus failures across four rounds would each
  # have been caught here; the hard-coded "1.0.2" replacement is the exact shape.
  # THE SPEC TREE IS PART OF THE FIXTURE, so it is part of the snapshot. A case
  # mutating a normative document changed nothing the detector could see and was
  # reported VACUOUS while it had forged exactly what it claimed to —
  # law:evidence.instrument-nonvacuity@1's own instrument, blind to a fixture
  # that had moved outside the directory it was watching.
  local pre; pre=$(file_digests "$d"; file_digests "$d/../docs" 2>/dev/null || true)
  # PHASE 1 of law:evidence.clean-baseline@1 — this case's fixture must BE the
  # one that was baselined, not merely one built by the same recipe
  CASES=$((CASES+1))
  if [ -n "$BASELINE_DIGEST" ] && [ "$pre" != "$BASELINE_DIGEST" ]; then
    echo "FAIL  $name (FIXTURE DRIFT — this case's tree differs from the baselined one)"; FAILED=1; return
  fi
  ( cd "$d" && python3 -c "$py" )
  local post; post=$(file_digests "$d"; file_digests "$d/../docs" 2>/dev/null || true)
  local touched; touched=$(changed_files "$pre" "$post")
  if [ -z "$touched" ]; then
    echo "FAIL  $name (VACUOUS — the forgery changed no artifact; nothing was tested)"; FAILED=1; return
  fi
  local intended; intended=$(intended_targets "$py")
  if [ -n "$intended" ] && [ "$intended" != "$touched" ]; then
    echo "FAIL  $name (TARGET MISMATCH — script intends [$intended], run changed [$touched])"; FAILED=1; return
  fi
  # M-10 — PHASE-PINNED LIVE TARGET. History may be pinned; live state must be
  # derived. Every check above this line is BLIND to the species: a case
  # selecting `revision == 3` after @4 became canonical still mutates a file, so
  # it is neither vacuous nor target-mismatched — it has simply stopped testing
  # the thing it names. Three of them did exactly that this round. That was the
  # LOUD version, where the case reported its own forgery uncaught; the quiet
  # version is a neighbouring assertion catching the mutation anyway, and this
  # tree has hit that five times.
  local body="$d/.case_body.py"; printf '%s' "$py" > "$body"
  local pinout; pinout=$(python3 "$BASE/phase_pin_lint.py" "$body" "$want" 2>&1); local pinrc=$?
  rm -f "$body"
  if [ $pinrc -ne 0 ]; then
    echo "FAIL  $name (M-10 PHASE-PINNED LIVE TARGET — $pinout)"
    echo "        add '# HISTORY_PIN_OK: <why>' if this case's subject really IS history"; FAILED=1; return
  fi
  local out; out=$(cd "$d" && node grid_check.mjs 2>&1); local code=$?
  if [ $code -ne 0 ] && echo "$out" | grep -qE "$want"; then
    CAUGHT=$((CAUGHT+1))
    echo "PASS  $name [$touched] → $(echo "$out" | grep -m1 -E "$want" | sed 's/^ *//' | cut -c1-96)"
  else
    echo "FAIL  $name (exit=$code; wanted /$want/)"; echo "$out" | head -5; FAILED=1
  fi
}
FAILED=0
CASES=0; CAUGHT=0
establish_baseline || exit 1

RESEAL='
import json, hashlib
def committed_view(c):
    return [["type",c["type"]],["version",c["version"]],["representation",c["representation"]],
     ["plane_profile",{"INTERACT":list(c["plane_profile"]["INTERACT"]),"COLLAPSE_GATED":list(c["plane_profile"]["COLLAPSE_GATED"])}],
     ["quiescence_criterion",c["quiescence_criterion"]],
     ["strategy",{"kind":c["strategy"]["kind"],"schedulers":list(c["strategy"]["schedulers"])}],
     ["budget",c["budget"]],["corpus",{"id":c["corpus"]["id"],"sha256":c["corpus"]["sha256"]}],
     ["claims",list(c["claims"])],["law_refs",list(c["law_refs"])],
     ["run_manifest_hash",c["run_manifest_hash"]],
     ["exhibit_film_ids",list(c["exhibit_film_ids"])]]
def js(o):  # JSON.stringify-compatible: no spaces, keys in insertion order
    return json.dumps(o, separators=(",",":"), ensure_ascii=False)
def reseal(c):
    c["run_manifest_hash"] = hashlib.sha256(js(c["run_manifest"]).encode()).hexdigest()
    c["exhibit_film_ids"] = [e["film"]["film_id"] for e in c["exhibit_films"]]
    c["cert_id"] = hashlib.sha256(("TRVM-SCHEDCERT-v2|"+js(committed_view(c))).encode()).hexdigest()
c = json.load(open("scheduler_certificate.json"))
'

# ── A. cert-layer forgeries (engine-free detection required) ──────────────
run_case hollow-resealed "cert|receipt|runs|evidence" "$RESEAL
c['run_manifest']=[]; c['exhibit_films']=[]
c['evidence']={'schedulers':4,'terms':24,'runs':999999,'completed':999999,'nf_matched':999999,'readback_pure':999999,'max_steps':1}
reseal(c); json.dump(c, open('scheduler_certificate.json','w'), indent=1)"

run_case inflation-resealed "evidence|aggregate" "$RESEAL
c['evidence']=dict(c['evidence']); c['evidence']['runs']=9600; c['evidence']['completed']=9600
reseal(c); json.dump(c, open('scheduler_certificate.json','w'), indent=1)"

run_case profile-broadened-resealed "profile" "$RESEAL
c['plane_profile']['INTERACT'] = list(c['plane_profile']['INTERACT']) + ['RULE-OF-COOL']
reseal(c); json.dump(c, open('scheduler_certificate.json','w'), indent=1)"

run_case receipt-tamper-unsealed "manifest|cert_id|cert-id" "
import json
c = json.load(open('scheduler_certificate.json'))
c['run_manifest'][0]['steps'] = 12345
json.dump(c, open('scheduler_certificate.json','w'), indent=1)"

# ── B. round-4 regression negatives ───────────────────────────────────────
run_case stale-citation "non-canonical" "
s = open('kappa_witnesses.mjs').read()
open('kappa_witnesses.mjs','w').write(s + '\n// fresh claim per law:sched.certificate@1\n')"

run_case banned-phrase "banned phrase" "
s = open('trvm_law_kernel.mjs').read()
open('trvm_law_kernel.mjs','w').write(s + '\n// the CALM property that licenses this optimization\n')"

run_case unknown-citation "unknown law|unresolved" "
s = open('trvm_law_kernel.mjs').read()
open('trvm_law_kernel.mjs','w').write(s + '\n// justified by law:total.nonsense@9\n')"

run_case double-canonical "canonical" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id']=='sched.certificate' and not e.get('canonical'): e['canonical']=True
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case ref-coherent-key-grid "ref_coherent" "
import json
g = json.load(open('invariant-grid.json'))
g['kernel_evidence']['ref_coherent'] = True
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case ref-coherent-key-cert "honest keys|ref_coherent" "$RESEAL
c['evidence'] = {('ref_coherent' if k=='readback_pure' else k): v for k, v in c['evidence'].items()}
json.dump(c, open('scheduler_certificate.json','w'), indent=1)"

run_case flagship-drift "flagship" "
import json
g = json.load(open('invariant-grid.json'))
g['flagship_pair']['law_ref'] = 'law:kappa.internal-edge.monotonicity@3'
json.dump(g, open('invariant-grid.json','w'), indent=1)"


run_case_engine() {  # like run_case but the verifier is the WORLD ENGINE mode
  local name="$1" want="$2" py="$3"
  local d="$SCRATCH/$name/gov"
  rm -rf "$d" && mkdir -p "$d" || { echo "FAIL  $name (scratch unusable: $d)"; CASES=$((CASES+1)); FAILED=1; return; }
  for f in $CASE_INPUTS; do mkdir -p "$d/$(dirname "$f")" && cp "$BASE/$f" "$d/$f"; done
  copy_spec_tree "$d"
  # THE SPEC TREE IS PART OF THE FIXTURE, so it is part of the snapshot. A case
  # mutating a normative document changed nothing the detector could see and was
  # reported VACUOUS while it had forged exactly what it claimed to —
  # law:evidence.instrument-nonvacuity@1's own instrument, blind to a fixture
  # that had moved outside the directory it was watching.
  local pre; pre=$(file_digests "$d"; file_digests "$d/../docs" 2>/dev/null || true)
  # PHASE 1 of law:evidence.clean-baseline@1 — this case's fixture must BE the
  # one that was baselined, not merely one built by the same recipe
  CASES=$((CASES+1))
  if [ -n "$BASELINE_DIGEST" ] && [ "$pre" != "$BASELINE_DIGEST" ]; then
    echo "FAIL  $name (FIXTURE DRIFT — this case's tree differs from the baselined one)"; FAILED=1; return
  fi
  ( cd "$d" && python3 -c "$py" )
  local post; post=$(file_digests "$d"; file_digests "$d/../docs" 2>/dev/null || true)
  local touched; touched=$(changed_files "$pre" "$post")
  # the counter lives in the baseline phase now; incrementing here too made the
  # engine case count twice and the printed total read 101 where it was 100.
  # Caught because the number moved when nothing about the case set had.
  if [ -z "$touched" ]; then
    echo "FAIL  $name (VACUOUS — the forgery changed no artifact; nothing was tested)"; FAILED=1; return
  fi
  local intended; intended=$(intended_targets "$py")
  if [ -n "$intended" ] && [ "$intended" != "$touched" ]; then
    echo "FAIL  $name (TARGET MISMATCH — script intends [$intended], run changed [$touched])"; FAILED=1; return
  fi
  # M-10 — PHASE-PINNED LIVE TARGET. History may be pinned; live state must be
  # derived. Every check above this line is BLIND to the species: a case
  # selecting `revision == 3` after @4 became canonical still mutates a file, so
  # it is neither vacuous nor target-mismatched — it has simply stopped testing
  # the thing it names. Three of them did exactly that this round. That was the
  # LOUD version, where the case reported its own forgery uncaught; the quiet
  # version is a neighbouring assertion catching the mutation anyway, and this
  # tree has hit that five times.
  local body="$d/.case_body.py"; printf '%s' "$py" > "$body"
  local pinout; pinout=$(python3 "$BASE/phase_pin_lint.py" "$body" "$want" 2>&1); local pinrc=$?
  rm -f "$body"
  if [ $pinrc -ne 0 ]; then
    echo "FAIL  $name (M-10 PHASE-PINNED LIVE TARGET — $pinout)"
    echo "        add '# HISTORY_PIN_OK: <why>' if this case's subject really IS history"; FAILED=1; return
  fi
  ( cd "$d" && node trvm_world.mjs --check-receipt > out.txt 2>&1 )
  local code=$?
  local msg=$(grep -aoE "$want" "$d/out.txt" | head -1)
  if [ $code -ne 0 ] && [ -n "$msg" ]; then
    CAUGHT=$((CAUGHT+1))
    echo "PASS  $name [$touched] → engine: $msg"
  else
    echo "FAIL  $name (engine exit=$code; wanted /$want/)"; FAILED=1
  fi
}

# ── C. round-6 forgeries: identity lockstep + refinement receipt ──────────
RESEAL_RR='
import json, hashlib
def js(o): return json.dumps(o, separators=(",",":"), ensure_ascii=False)
r = json.load(open("refinement_receipt.json"))
def reseal():
    r["receipt_id"] = hashlib.sha256(("TRVM-REFINE-v1|"+js(r["per_term"])+"|"+js(r["summary"])).encode()).hexdigest()
'

run_case version-lockstep-grid "not the head of the declared lineage|KERNEL_VERSION" "
import json
g = json.load(open('invariant-grid.json'))
g['version'] = '0.9'; g['law_registry']['grid_version'] = '0.9'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case version-lockstep-kernel "KERNEL_VERSION|header does not carry" "
s = open('trvm_law_kernel.mjs').read()
import re
s2 = re.sub(r'const KERNEL_VERSION = \"[^\"]+\";', 'const KERNEL_VERSION = \"0.6\";', s, count=1)
assert s2 != s, 'version-lockstep-kernel forged nothing — the KERNEL_VERSION pattern no longer matches'
open('trvm_law_kernel.mjs','w').write(s2)"

run_case refine-tamper-unsealed "receipt_id does not recompute" "$RESEAL_RR
r['per_term'][0]['steps'] = 777
json.dump(r, open('refinement_receipt.json','w'), indent=1)"

run_case refine-inflation-resealed "does not recompute from per_term" "$RESEAL_RR
r['summary']['sem_chains_equal'] = 25
reseal()
json.dump(r, open('refinement_receipt.json','w'), indent=1)"

run_case refine-lawref-swap-resealed "law_refs" "$RESEAL_RR
r['law_refs'][0] = 'law:sched.free.float@1'
reseal()
json.dump(r, open('refinement_receipt.json','w'), indent=1)"

run_case refine-chainflag-resealed "sem_chains_equal does not recompute|partition" "$RESEAL_RR
r['per_term'][3]['sem_chain_equal'] = False
reseal()
json.dump(r, open('refinement_receipt.json','w'), indent=1)"

run_case refine-receipt-missing "refinement_receipt.json missing" "
import os; os.remove('refinement_receipt.json')"

run_case semid-canonical-corrupt "canonical|non-canonical" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id']=='state.semantic-quotient': e['canonical']=False
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case sem-refusal-dropped "19 replay refusals" "
import json
g = json.load(open('invariant-grid.json'))
g['semantic_film']['replay_refusals'].remove('sem-locus-not-enabled')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case budget-refusal-dropped "19 replay refusals" "
import json
g = json.load(open('invariant-grid.json'))
g['semantic_film']['replay_refusals'].remove('sem-budget-mismatch')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case terminal-witness-schema-dropped "terminal_fields must declare" "
import json
g = json.load(open('invariant-grid.json'))
g['semantic_film']['terminal_fields'] = [f for f in g['semantic_film']['terminal_fields'] if not f.startswith('budget')]
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case world-version-map-drift "declares .* but artifact_versions says|artifact_versions missing" "
import json
g = json.load(open('invariant-grid.json'))
g['artifact_versions']['trvm_world.mjs'] = '9.9.9'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case world-warrant-value-flip-resealed "warrant_id does not recompute|receipt_id does not recompute" "
import json, hashlib
def js(o): return json.dumps(o, separators=(',',':'), ensure_ascii=False)
r = json.load(open('world_warrant_receipt.json'))
r['warrant']['value'] = 99
r['receipt_id'] = hashlib.sha256(('TRVM-WORLDRECEIPT-v1|'+js(r['warrant'])+'|'+r['footprint_id']).encode()).hexdigest()
json.dump(r, open('world_warrant_receipt.json','w'), indent=1)"

run_case world-footprint-prune-in-receipt "footprint_id does not recompute|warrant_id does not recompute|support is not a subset" "
import json
r = json.load(open('world_warrant_receipt.json'))
r['warrant']['read_footprint']['exact'] = r['warrant']['read_footprint']['exact'][1:]
json.dump(r, open('world_warrant_receipt.json','w'), indent=1)"

run_case world-refusal-dropped "10 replay refusals" "
import json
g = json.load(open('invariant-grid.json'))
g['warrant']['executable']['replay_refusals'].remove('undeclared-read')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case composite-pairing-pruned "without its paired warrant-fresh scope|footprint_id does not recompute|warrant_id does not recompute" "
import json
r = json.load(open('world_warrant_receipt.json'))
c = r['composite']['warrant']['read_footprint']
c['predicates'] = [p for p in c['predicates'] if not p[0].startswith('warrant-fresh:')]
json.dump(r, open('world_warrant_receipt.json','w'), indent=1)"

run_case composite-value-flip-resealed "composite warrant_id does not recompute|receipt_id does not recompute" "
import json
r = json.load(open('world_warrant_receipt.json'))
r['composite']['warrant']['value'] = 12345
json.dump(r, open('world_warrant_receipt.json','w'), indent=1)"

run_case composite-stale-at-emit "composite must be emitted fresh|receipt_id does not recompute" "
import json
r = json.load(open('world_warrant_receipt.json'))
r['composite_freshness_at_emit'] = {'verdict': 'scope_dirty', 'witness': {'scope': 'x', 'was': 'a', 'now': 'b'}}
json.dump(r, open('world_warrant_receipt.json','w'), indent=1)"

run_case canonical-domain-declaration-dropped "canonical_value_domain or deletions" "
import json
g = json.load(open('invariant-grid.json'))
del g['world']['canonical_value_domain']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case write-mediated-law-corrupt "canonical|non-canonical" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id']=='world.write-mediated': e['canonical']=False
json.dump(g, open('invariant-grid.json','w'), indent=1)"

RESEAL_WR='
import json, hashlib
def js(o): return json.dumps(o, separators=(",",":"), ensure_ascii=False)
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
r = json.load(open("world_warrant_receipt.json"))
def committed(x):
    return [["measure",x["measure"]],["predicate",x["predicate"]],["value",x["value"]],
            ["witness",x["witness"]],["support",sorted(x["support"])],
            ["read_footprint",{"exact":sorted(map(list,x["read_footprint"]["exact"])),
                               "predicates":sorted(map(list,x["read_footprint"]["predicates"]))}],
            ["derivation_id",x["derivation_id"]],["at_vclock",x["at_vclock"]]]
def reseal_all():
    r["warrant"]["warrant_id"] = sha("TRVM-WARRANT-v3|" + js(committed(r["warrant"])))
    r["receipt_id"] = sha("TRVM-WORLDRECEIPT-v3|" + js(r["world_spec"]) + "|" + js(r["warrant"]) + "|" + r["footprint_id"]
                          + "|" + js(r["composite"]["warrant"]) + "|" + r["composite"]["footprint_id"])
'

run_case_engine receipt-support-prune-engine "support-mismatch" "$RESEAL_WR
r['warrant']['support'] = r['warrant']['support'][:-1]
reseal_all()
json.dump(r, open('world_warrant_receipt.json','w'), indent=1)"

run_case receipt-support-uncanonical "not canonical" "$RESEAL_WR
r['warrant']['support'] = list(reversed(r['warrant']['support']))
reseal_all()
json.dump(r, open('world_warrant_receipt.json','w'), indent=1)"

MAINT_RESEAL='
import json, hashlib
def js(o): return json.dumps(o, separators=(",",":"), ensure_ascii=False)
r = json.load(open("maintenance_receipt.json"))
def reseal():
    r["pass_id"] = hashlib.sha256(("TRVM-MAINTPASS-v1|"+str(r["vclock_before"])+"|"+str(r["vclock_after"])+"|"+js(r["before"])+"|"+js(r["after"])+"|"+js(r["steps"])).encode()).hexdigest()
'

run_case maint-step-erased-resealed "hides publication" "$MAINT_RESEAL
r['steps'] = [s for s in r['steps'] if s['name'] != 'B']
reseal()
json.dump(r, open('maintenance_receipt.json','w'), indent=1)"

run_case maint-action-flip-resealed "must not move the publication|must advance the publication" "$MAINT_RESEAL
r['steps'][0]['action'] = 'none'
reseal()
json.dump(r, open('maintenance_receipt.json','w'), indent=1)"

run_case maint-noop-lie-resealed "no_op flag does not recompute" "$MAINT_RESEAL
r['no_op'] = True
reseal()
json.dump(r, open('maintenance_receipt.json','w'), indent=1)"

run_case maint-aftermap-inflated-resealed "after-map disagrees with the step record" "$MAINT_RESEAL
list(r['after'].values())[0]['pub_version'] = 999
r['after']['A']['pub_version'] = 999
reseal()
json.dump(r, open('maintenance_receipt.json','w'), indent=1)"

run_case confinement-guard-stripped "missing confinement refusal" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('world-write-during-maintenance', 'oops-no-guard'))"

run_case key-privacy-stripped "key-confinement construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('#lockKey', '_lockKey'))"

run_case prototype-freeze-stripped "key-confinement construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('Object.freeze(World.prototype)', '/* unfrozen */'))"

run_case confinement-law-corrupt "canonical|non-canonical" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id']=='maintenance.capability-confinement': e['canonical']=False
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case maint-torn-inconsistent "torn receipts must be aborted|unapplied .* must show the before-side|applied .* must show" "$MAINT_RESEAL
r['torn'] = True
r['applied'] = []
reseal()
json.dump(r, open('maintenance_receipt.json','w'), indent=1)"

run_case world-law-canonical-corrupt "canonical|non-canonical" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id']=='warrant.phantom-scope': e['canonical']=False
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case sched-declaration-drift "strategy_schedulers" "
import json
g = json.load(open('invariant-grid.json'))
g['scheduler_certificate']['strategy_schedulers'] = ['leftmost','deepest','middle','random','starve_dups']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── E. round-10 forgeries: the golden pre-hash byte vectors ───────────────
# Each aims at a different one of the three bindings, so a single fix cannot
# quiet all four. The commitment is resealed where the forgery would otherwise
# die on vectors_id alone — an attacker who can edit the file can also rehash
# it, and a checker that only recomputes its own commitment proves nothing
# about whether the bytes describe this corpus.
PRESEAL='
import json, hashlib
def js(o): return json.dumps(o, separators=(",",":"), ensure_ascii=False)
v = json.load(open("golden_prehash_vectors.json"))
def reseal():
    v["vectors_id"] = hashlib.sha256(("TRVM-PREHASH-VECTORS-v1|"+js(v["per_term"])+"|"+js(v["compaction"])+"|"+js(v["corpus"])).encode()).hexdigest()
'

# 1. a signature byte flipped and the file honestly resealed: the digest it
#    claims to explain is no longer its sha256 preimage
run_case prehash-signature-tampered "does not hash to its sem_state_id" "$PRESEAL
t = v['per_term'][0]
t['initial']['sem_signature'] = t['initial']['sem_signature'].replace('N0', 'N1')
reseal(); json.dump(v, open('golden_prehash_vectors.json','w'), indent=1)"

# 2. the harder direction — signature AND id moved together so they are
#    internally consistent. Only the anchor to shipped evidence catches it.
run_case prehash-id-resealed "not anchored to the refinement receipt|different refinement receipt" "$PRESEAL
import hashlib
t = v['per_term'][0]
sig = 'L0(N0)FORGED'
t['normal_form']['sem_signature'] = sig
t['normal_form']['sem_state_id'] = hashlib.sha256(sig.encode()).hexdigest()
t['normal_form']['nf_id'] = 'sem-' + hashlib.sha256(b'whatever').hexdigest()
reseal(); json.dump(v, open('golden_prehash_vectors.json','w'), indent=1)"

# 3. vectors that describe a corpus the shipped receipts never ran
run_case prehash-nfid-unanchored "no refinement receipt row to anchor to" "$PRESEAL
v['per_term'][0]['name'] = 'identity_prime'
reseal(); json.dump(v, open('golden_prehash_vectors.json','w'), indent=1)"

# 4. the compaction boundary claimed but not demonstrated: the row says what
#    was compacted, and the reconstruction must hash to what was emitted
run_case prehash-compaction-lie "does not hash to the emitted compacted signature|does not exceed the threshold" "$PRESEAL
v['compaction']['first_compacted_precompaction']['signature'] += 'X'
v['compaction']['first_compacted_precompaction']['length'] += 1
reseal(); json.dump(v, open('golden_prehash_vectors.json','w'), indent=1)"

# 5. an over-threshold signature shipped uncompacted — §5 is structural, and a
#    published vector that ignores it teaches a second implementation the wrong
#    boundary while still hashing consistently with itself
run_case prehash-uncompacted-oversize "violates the §5 compaction rule" "$PRESEAL
import hashlib
t = v['per_term'][0]
sig = 'A(' + 'Ffree:LONG,'*12 + 'Ffree:END)'
t['initial']['sem_signature'] = sig
t['initial']['sem_state_id'] = hashlib.sha256(sig.encode()).hexdigest()
reseal(); json.dump(v, open('golden_prehash_vectors.json','w'), indent=1)"


# ── F. round-9D forgeries: the coordinator's guards ───────────────────────
# Each strips one construct the coordinator-confinement law names. These are
# artifact-tamper cases in the same family as confinement-guard-stripped and
# prototype-freeze-stripped: the law is only as real as the source that carries
# it, so removing the guard must fail the checker even though nothing else moved.
run_case coordinator-freeze-stripped "coordinator-confinement construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('Object.freeze(Maintainer.prototype);',''))"

run_case coordinator-reentrancy-stripped "coordinator-confinement construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('maintainer-reentrancy-refused','maintainer-allows-reentry'))"

run_case coordinator-inpass-stripped "coordinator-confinement construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('#inPass','_openPass'))"

run_case coordinator-law-corrupt "canonical flag of maintenance.coordinator-confinement" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id']=='maintenance.coordinator-confinement': e['canonical']=False
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case coordinator-section-dropped "coordinator_confinement missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['maintenance']['confinement']['coordinator_confinement']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── G. round-9D.1 forgeries: the reachable authority graph ────────────────
run_case writemediation-store-stripped "write-mediation construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('class GuardedStore','class UnguardedStore'))"

run_case writemediation-ownership-stripped "write-mediation construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('ownSpec','passthruSpec'))"

run_case writemediation-divergence-stripped "write-mediation construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('coordinator_diverged','coordinator_ok'))"

run_case writemediation-section-dropped "write_mediation missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['maintenance']['confinement']['write_mediation']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── H. round-9D.3 forgeries: ownership must fail closed ──────────────────
run_case ownership-failopen-restored "fail-open ownership path" "
s = open('trvm_world.mjs').read()
i = s.index('function ownCanonical')
j = s.index('}', s.index('throw new Error(label', i)) + 1
open('trvm_world.mjs','w').write(s[:i] + 'function ownCanonical(v, label) { try { return v; } catch { return v; } }' + s[j+1:])"

run_case ownership-refusal-stripped "total-ownership construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('-not-canonical: ','-not-canonical_'))"

run_case film-identity-declaration-dropped "film_identity_forward_declaration missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['film_identity_forward_declaration']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── I. the declared boundary failure must stay declared ──────────────────
run_case closure-law-greenwashed "not FALSIFIED" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id']=='derivation.environment-confinement': e['status']='PROPERTY-TESTED'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case closure-law-deleted "environment-confinement@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries'] if e['id']!='derivation.environment-confinement']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case realm-roadmap-dropped "realm_roadmap missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['realm_roadmap']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── J. artifact-root / coverage forgeries ────────────────────────────────
run_case artifact-undeclared "present but UNDECLARED" "
import json
m = json.load(open('artifacts.json'))
m['case_inputs'] = [f for f in m['case_inputs'] if f != 'kappa_witnesses.mjs']
json.dump(m, open('artifacts.json','w'), indent=1)"

run_case artifact-manifest-corrupt "artifacts.json missing or not v1" "
import json
m = json.load(open('artifacts.json'))
m['type'] = 'TRVM-GOV-ARTIFACTS-v0'
json.dump(m, open('artifacts.json','w'), indent=1)"

run_case artifact-roots-declaration-dropped "artifact_roots missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['artifact_roots']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── round 15: the two DERIVE-v0.1.0 defects, and the record of them ──────────
# Both defects were one line of the worker each and both read as harmless — a
# convenient place for the read table, and a field passed through from the
# request. Each forgery below restores one of them, or removes the record that
# says why they were wrong.

run_case derive-reads-via-inputs "sources the read table from canonical_inputs again" "
src = open('derive_worker.mjs').read()
src = src.replace('const out = evaluate(ast, req.read_grants, req.canonical_inputs);',
                  'const reads = req.canonical_inputs.__reads ?? {};\n    const out = evaluate(ast, reads, req.canonical_inputs);')
open('derive_worker.mjs','w').write(src)"

run_case derive-impl-echoed "must ASSERT its own implementation_id" "
src = open('derive_worker.mjs').read()
src = src.replace('implementation_id: JS_IMPLEMENTATION_ID,', 'implementation_id: req.expected_implementation_id,')
open('derive_worker.mjs','w').write(src)"

run_case derive-semantic-projection-widened "execution_evidence envelope OUTSIDE the semantic projection" "
src = open('derive_protocol.mjs').read()
src = src.replace('SEMANTIC_RESULT_FIELDS = [\"request_id\", \"program_sem_id\", \"grant_id\", \"semantic_result\"]',
                  'SEMANTIC_RESULT_FIELDS = [\"request_id\", \"program_sem_id\", \"grant_id\", \"semantic_result\", \"execution_evidence\"]')
open('derive_protocol.mjs','w').write(src)"

run_case derive-footprint-check-removed "missing v0.2.0 construct" "
src = open('derive_protocol.mjs').read()
src = src.replace('export function footprintWithinGrant', 'function footprintWithinGrant')
open('derive_protocol.mjs','w').write(src)"

run_case derive-grant-law-deleted "grant-footprint-separation@1 missing or non-canonical" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'derivation.grant-footprint-separation']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case derive-provenance-open-half-dropped "no longer declares its open half" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.implementation-provenance':
        e['statement'] = e['statement'].split('DECLARED OPEN')[0]
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case derivation-language-ruling-dropped "derivation_language missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['derivation_language']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-planes-dropped "film_planes missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['film_planes']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case derive-boundary-record-collapsed "two_evidence_objects or granting_model" "
import json
m = json.load(open('artifacts.json'))
del m['derivation_boundary']['two_evidence_objects']
json.dump(m, open('artifacts.json','w'), indent=1)"

# ── round 16: the frozen core ────────────────────────────────────────────────

run_case derive-core-not-committed "program_sem_id must commit CORE_SEM_ID" "
src = open('derive_protocol.mjs').read()
src = src.replace('H(\"TRVM-PROGRAM-v2|\" + CORE_SEM_ID + \"|\" + canonicalBytes(ast))',
                  'H(\"TRVM-PROGRAM-v2|\" + canonicalBytes(ast))')
open('derive_protocol.mjs','w').write(src)"

run_case derive-grammar-unchecked "must validate the grammar BEFORE hashing" "
src = open('derive_protocol.mjs').read()
src = src.replace('  const v = validateProgram(ast);\n  if (!v.ok) throw new Error(v.reason);\n', '')
open('derive_protocol.mjs','w').write(src)"

run_case derive-arith-coercion-restored "must refuse non-number operands" "
src = open('derive_protocol.mjs').read()
src = src.replace('throw new Error(\"program-type: \" + op + \" of non-number\")', 'void 0')
open('derive_protocol.mjs','w').write(src)"

run_case derive-trace-made-semantic "execution_evidence envelope OUTSIDE the semantic projection" "
src = open('derive_protocol.mjs').read()
src = src.replace('EXECUTION_ENVELOPE = [\"implementation_id\", \"read_trace\"]',
                  'EXECUTION_ENVELOPE = [\"implementation_id\"]')
open('derive_protocol.mjs','w').write(src)"

run_case footprint-set-ruling-dropped "dependency SET" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.core-semantics':
        e['statement'] = e['statement'].replace('canonical DEPENDENCY SET', 'sequence')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case core-freeze-undeclared "derivation_language.frozen missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['derivation_language']['frozen']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case core-law-deleted "law derivation.core-semantics@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'derivation.core-semantics']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case core-record-collapsed "frozen_core or footprint_is_a_set" "
import json
m = json.load(open('artifacts.json'))
del m['derivation_boundary']['footprint_is_a_set']
json.dump(m, open('artifacts.json','w'), indent=1)"


# ── round 17: the derivation authority ──────────────────────────────────────

run_case issuance-binds-the-grant-again "issuance must bind request_sem_id" "
src = open('derive_protocol.mjs').read()
src = src.replace('this.#issued.set(request_id, Object.freeze({ request_sem_id: requestSemId(req), request: req }));',
                  'this.#issued.set(request_id, Object.freeze({ request_sem_id: body.grant_id, request: req }));')
open('derive_protocol.mjs','w').write(src)"

run_case acceptance-made-a-free-function "acceptance must be a METHOD" "
src = open('derive_protocol.mjs').read()
src = src.replace('export class DerivationAuthority', 'export function acceptForeignResult(){}\nexport class DerivationAuthority')
open('derive_protocol.mjs','w').write(src)"

run_case acceptance-claims-committable "must not return .committable" "
src = open('derive_protocol.mjs').read()
src = src.replace('{ ok: true, validated: true, fresh_at_check: true,',
                  '{ ok: true, validated: true, fresh_at_check: true, committable: true,')
open('derive_protocol.mjs','w').write(src)"

run_case authorize-options-reopened "must whitelist its options" "
src = open('derive_protocol.mjs').read()
src = src.replace('AUTHORIZE_OPTIONS = [\"expected_implementation_id\"]', 'AUTHORIZE_OPTIONS = [\"expected_implementation_id\", \"canonical_inputs\"]')
open('derive_protocol.mjs','w').write(src)"

run_case freshness-vclock-restored "never on a global vclock" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.footprint-freshness':
        e['statement'] = e['statement'].replace('never on a global vclock', 'on the world vclock')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case committability-claim-restored "no longer states that acceptance does not establish" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.footprint-freshness':
        e['statement'] = e['statement'].replace('ACCEPTANCE DOES NOT ESTABLISH COMMITTABILITY', 'ACCEPTANCE ESTABLISHES COMMITTABILITY')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case issuance-law-deleted "law derivation.grant-issuance@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'derivation.grant-issuance']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case acceptance-record-dropped "acceptance_is_not_commitment" "
import json
m = json.load(open('artifacts.json'))
del m['derivation_boundary']['acceptance_is_not_commitment']
json.dump(m, open('artifacts.json','w'), indent=1)"


# ── round 18: the apparatus gate ────────────────────────────────────────────

run_case harness-selftest-law-deleted "law evidence.harness-selftest@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'evidence.harness-selftest']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case clean-baseline-species-dropped "no longer requires the clean-baseline" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'evidence.harness-selftest':
        e['statement'] = e['statement'].replace('UNPERTURBED case tree', 'perturbed case tree')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case harness-selftest-undeclared "does not declare harness_selftest.sh" "
import json
m = json.load(open('artifacts.json'))
m['tools'] = [t for t in m['tools'] if t != 'harness_selftest.sh']
json.dump(m, open('artifacts.json','w'), indent=1)"


# ── round 19: execution evidence has its own rule ───────────────────────────

run_case trace-conformance-removed "missing validateTraceConformance" "
src = open('derive_protocol.mjs').read()
src = src.replace('export function validateTraceConformance', 'function validateTraceConformance')
open('derive_protocol.mjs','w').write(src)"

run_case verdicts-collapsed "report semantic agreement and trace conformance SEPARATELY" "
src = open('derive_protocol.mjs').read()
src = src.replace('semantic_agreement: true, trace_conforms: false', 'trace_conforms: false')
open('derive_protocol.mjs','w').write(src)"

run_case execution-evidence-law-deleted "law derivation.execution-evidence@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'derivation.execution-evidence']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case unverified-sentence-dropped "non-semantic does not mean unverified" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.execution-evidence':
        e['statement'] = e['statement'].replace('NON-SEMANTIC DOES NOT MEAN UNVERIFIED. ', '')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case envelope-record-dropped "missing two_envelopes" "
import json
m = json.load(open('artifacts.json'))
del m['derivation_boundary']['two_envelopes']
json.dump(m, open('artifacts.json','w'), indent=1)"


# ── round 20: the clean baseline ────────────────────────────────────────────

run_case clean-baseline-law-deleted "law evidence.clean-baseline@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'evidence.clean-baseline']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case baseline-becomes-silence "no longer says the baseline is DECLARED" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'evidence.clean-baseline':
        e['statement'] = e['statement'].replace('DECLARED, not silent', 'silent')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case baseline-families-dropped "clean_baseline missing its phase list" "
import json
g = json.load(open('invariant-grid.json'))
del g['clean_baseline']['declared_baselines']
json.dump(g, open('invariant-grid.json','w'), indent=1)"


run_case gate-can-swallow-failure "no longer carries its runner half" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'evidence.clean-baseline':
        e['statement'] = e['statement'].replace('AND A GATE MUST BE ABLE TO FAIL', 'AND A GATE REPORTS')
json.dump(g, open('invariant-grid.json','w'), indent=1)"


run_case lowering-spike-dropped "lowering_spike missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['lowering_spike']
json.dump(g, open('invariant-grid.json','w'), indent=1)"


# ── round 22: an execution claim is not provenance ──────────────────────────

run_case derive-caller-picks-implementation "deriveLocally must take NO implementation parameter" "
src = open('derive_protocol.mjs').read()
src = src.replace('export function deriveLocallyOwned(registry, req) {',
                  'export function deriveLocallyOwned(registry, req, caller_id) {')
open('derive_protocol.mjs','w').write(src)"

run_case provenance-observation-removed "must observe what the host launched" "
src = open('derive_protocol.mjs').read()
src = src.replace('implementation-claim-contradicts-observation', 'implementation-claim-ok')
open('derive_protocol.mjs','w').write(src)"

run_case validator-does-provenance-again "must report implementation_claimed" "
src = open('derive_protocol.mjs').read()
src = src.replace('implementation_claimed: impl', 'implementation_id: impl')
open('derive_protocol.mjs','w').write(src)"

run_case provenance-law-v2-scrubbed "no longer opens with 'an execution claim is not" "
# HISTORY_PIN_OK: subject is @2, superseded and retained; the pin IS the test
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.implementation-provenance' and e['revision'] == 2:
        e['statement'] = 'provenance is established by the executor handle.'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case false-claim-history-scrubbed "must stay on the record AS a false claim" "
# HISTORY_PIN_OK: subject is @1, kept on the record AS a false claim
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.implementation-provenance' and e['revision'] == 1:
        e['revision_note'] = 'superseded by a later revision'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case runner-contract-dropped "clean_baseline.runner_contract missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['clean_baseline']['runner_contract']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case outcome-hashes-a-sentence "encodes refusal STRUCTURALLY" "
import json
g = json.load(open('invariant-grid.json'))
del g['lowering_spike']['identities']['outcome_encoding']
json.dump(g, open('invariant-grid.json','w'), indent=1)"


# ── round 23: executor existence is not execution provenance ────────────────
run_case registration-api-restored "registerExecutor must be DELETED" "
src = open('derive_protocol.mjs').read()
src = src.replace('  async execute(req) {',
  '  registerExecutor(id) { return Object.freeze({ token: Symbol(id) }); }\n'
  '  async execute(registry, req) {')
open('derive_protocol.mjs','w').write(src)"

run_case acceptance-takes-a-proof-again "must be a METHOD on the authority taking EXACTLY" "
src = open('derive_protocol.mjs').read()
src = src.replace('accept(req, res) {', 'accept(req, res, executor = null) {')
open('derive_protocol.mjs','w').write(src)"

run_case authority-hashes-on-its-own "artifact hashing must live in the host" "
src = open('derive_protocol.mjs').read()
src = src.replace('const invocation = {', 'const _d = digestArtifactFiles([]); const invocation = {')
open('derive_protocol.mjs','w').write(src)"

run_case observation-key-projected "keyed over the WHOLE execution event" "
src = open('observed_execution_host.mjs').read()
src = src.replace('canonicalBytes(output)', 'String(output.ok)')
open('observed_execution_host.mjs','w').write(src)"

run_case second-observation-writer "exactly one writer" "
src = open('observed_execution_host.mjs').read()
src = src.replace('  observationOf(domain, invocation, output) {',
  '  vouch(k, o) { this.#observed.set(k, [o]); }\n'
  '  observationOf(domain, invocation, output) {')
open('observed_execution_host.mjs','w').write(src)"

run_case provenance-law-v3-deleted "implementation-provenance@3 missing" "
# HISTORY_PIN_OK: subject is @3, superseded history
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if not (e['id'] == 'derivation.implementation-provenance' and e['revision'] == 3)]
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case attestation-overclaimed "must state conservatively what hash-then-spawn" "
# HISTORY_PIN_OK: subject is @3's own conservative sentence, a historical record
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.implementation-provenance' and e['revision'] == 3:
        e['statement'] = e['statement'].replace(
            'It is NOT a proof that the OS executed those exact bytes under every filesystem race, and '
            'it is not hardware-attested executable identity.',
            'This is hardware-grade executable identity.')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case superseded-law-made-current "must stay on the record as history" "
# HISTORY_PIN_OK: subject is @2, superseded; the case exists to keep it superseded
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.implementation-provenance' and e['revision'] == 2:
        e['canonical'] = True
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── round 23: the execution plane originates evidence ───────────────────────
run_case film-law-deleted "film.native-emission has no canonical PROPERTY-TESTED revision" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'film.native-emission']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-history-scrubbed "must have EXACTLY ONE canonical revision, that revision must be the" "
# HISTORY_PIN_OK: subject is film.native-emission@1 and the readback record only it carries
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if not (e['id'] == 'film.native-emission' and e['revision'] == 1)]
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-history-unannotated "must have EXACTLY ONE canonical revision, that revision must be the" "
# HISTORY_PIN_OK: subject is film.native-emission@2, superseded history
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'film.native-emission' and e['revision'] == 2:
        e.pop('revision_note', None)
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-two-canonical "must have EXACTLY ONE canonical revision, that revision must be the" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'film.native-emission' and not e.get('canonical'):
        e['canonical'] = True   # a SECOND canonical; which superseded one is irrelevant
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-orders-collapsed "ENUMERATION order and the LOCUS INDEX order are different" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'film.native-emission' and e.get('canonical'):
        e['statement'] = e['statement'].replace('BOTH ARE LOAD-BEARING', 'they are equivalent')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-measurement-unrecorded "measured before it was asserted" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'film.native-emission' and e.get('canonical'):
        e['statement'] = e['statement'].replace('TRANSCRIPTION THEOREM', 'weaker claim')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-terminal-by-loop-exit "concluded only after a fresh full-pool enumeration" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'film.native-emission' and e.get('canonical'):
        e['statement'] = e['statement'].replace('FRESH FULL-POOL ENUMERATION', 'loop exit')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# B5.1. The strict budget parse and the argument-shape guards are C-source
# properties the grid asserts, so reverting either in the source must fail the
# gate. `--budget abc` under the reverted parse emits a valid-looking
# zero-frame film, which is the whole reason a text-tier assertion is worth
# having here: the artifact stays green while answering a question nobody asked.
# M-10 — the guard itself must be wired. A lint present in the tree and called
# by nothing is the instrument-nonvacuity species wearing a new noun, and this
# law is specifically about instruments that stopped measuring.
# B6 — EMISSION_CONFORMANCE-v1. The source properties that make the battery a
# conformance theorem rather than a transcription theorem, plus the two
# corrections the fixtures produced rather than confirmed.
# The pack must RUN the gate it ships. It did not, for one build: the gate was
# in the Makefile, the file was in case_inputs, and verify.sh never called it.
# A shipped-but-unrun gate is worse than a skipped one -- a skip is at least
# visible in the count.
# B6.1 — the three defects GPT's replay found, each forged where it lived.
# B6.2 — the projection must match the ontology, in BOTH directions.
run_case emitter-profile-merged-back "SERIALIZATION profile must be its own object with its own identity" "
src = open('lowering.mjs').read()
src = src.replace('export const CANONICAL_EMITTER_PROFILE = Object.freeze', 'const _merged_CANONICAL_EMITTER_PROFILE = Object.freeze')
open('lowering.mjs','w').write(src)"

run_case emitter-profile-described-not-read "must READ label_counter_start from the profile" "
src = open('lowering.mjs').read()
src = src.replace('const labels = { n: profile.label_counter_start, next()', 'const labels = { n: 0, next()')
open('lowering.mjs','w').write(src)"

# B6.3 — the same defect, one field over, in both directions. This case's
# ANCHOR is the thing that moved: B6.2's forgery replaced
# `CANONICAL_EMITTER_PROFILE.label_counter_start, next()`, which B6.3's
# parameterisation turned into a no-op, and the case above reported VACUOUS
# rather than silently passing. That is law:evidence.instrument-nonvacuity@1
# doing exactly what round 10's hand-typed \"1.0.2\" replacement taught it to.
run_case emitter-profile-prose-not-values "must hold the allocation ORDER and the binder NAMES as interpreted VALUES" "
src = open('lowering.mjs').read()
src = src.replace('  label_alloc_order: \"operands-then-node\",', '  label_alloc_order_note: \"depth-first, operands in declared field order\",')
open('lowering.mjs','w').write(src)"

run_case emitter-profile-notes-rehashed "PROSE must live in an unhashed NOTES sibling" "
src = open('lowering.mjs').read()
src = src.replace('export const CANONICAL_EMITTER_PROFILE_NOTES = Object.freeze', 'const _gone_CANONICAL_EMITTER_PROFILE_NOTES = Object.freeze')
open('lowering.mjs','w').write(src)"

run_case emitter-artifact-id-dropped "emitter IMPLEMENTATION must carry its own identity" "
src = open('lowering.mjs').read()
src = src.replace('export const CANONICAL_EMITTER_ARTIFACT_ID =', 'const _dropped_CANONICAL_EMITTER_ARTIFACT_ID =')
open('lowering.mjs','w').write(src)"

run_case ladder-prose-back-in-xenc "LADDER must be GONE from TARGET_ENCODING" "
src = open('lowering.mjs').read()
Q = chr(34)
head = 'export const TARGET_ENCODING = Object.freeze({' + chr(10)
assert head in src, 'ladder-prose-back-in-xenc: the TARGET_ENCODING declaration no longer matches'
ladder = ('  three_grades: ' + Q + 'exact emitted BYTES --quotient alpha and label spelling--> '
          'target_term_sem_id --execute, normalise, decode--> outcome_sem_id.' + Q + ',' + chr(10))
src = src.replace(head, head + ladder, 1)
open('lowering.mjs','w').write(src)"

run_case emission-knob-falsifier-narrated "both serialization directions must be MEASURED here rather than narrated" "
src = open('emission_conformance.mjs').read()
src = src.replace('E-2c a KNOB moves bytes and the profile id, and NO semantic id', 'E-2c the knob result, as recorded in the ledger')
open('emission_conformance.mjs','w').write(src)"

# B6.3.1 — GPT's falsifier against B6.3, and the instrument that ends the species.
# The first case restores the exact shape GPT broke: a module-level table emit()
# reads that the artifact id does not hash. It must be refused by the DERIVED
# closure check, not by a rule naming this one table.
# The exact shape GPT broke: the enum table back at module level, where emit()
# reads it and the artifact id does not hash it.
run_case emitter-artifact-table-escapes-bundle "must name its members, DECLARE what may be referenced" "
src = open('lowering.mjs').read()
src = src.replace('function labelAllocPreOrder(order) {',
                  'const LABEL_ALLOC_ORDERS = Object.freeze({});' + chr(10) + 'function labelAllocPreOrder(order) {', 1)
open('lowering.mjs','w').write(src)"

run_case emitter-artifact-inert-undeclared "must name its members, DECLARE what may be referenced" "
src = open('lowering.mjs').read()
src = src.replace('export const EMITTER_ARTIFACT_INERT = Object.freeze', 'const _undeclared_EMITTER_ARTIFACT_INERT = Object.freeze')
open('lowering.mjs','w').write(src)"

run_case emitter-artifact-closure-not-derived "must be DERIVED from lowering.mjs" "
src = open('emission_conformance.mjs').read()
src = src.replace('E-2e the artifact bundle is the WHOLE byte-producing closure', 'E-2e the artifact bundle members, as listed')
open('emission_conformance.mjs','w').write(src)"

run_case e8-alternate-back-to-add-only "alternate must be GENERIC" "
src = open('emission_conformance.mjs').read()
src = src.replace('const betaEmit = (r) => {', 'const notTheGenericAlternate = (r) => {')
open('emission_conformance.mjs','w').write(src)"

run_case template-hashes-downstream-counter "must not name a downstream counter start" "
src = open('lowering.mjs').read()
src = src.replace('THERE IS NO FIELD IT COULD OCCUPY', 'emit() allocates both from the template shape by TARGET_ENCODING.dup_label_policy — a counter from 0, depth-first, and there is no field it could occupy')
open('lowering.mjs','w').write(src)"

run_case emission-determinisms-merged "must test the two determinisms SEPARATELY" "
src = open('emission_conformance.mjs').read()
src = src.replace('E-1a SEMANTIC relation determinism', 'E-1 determinism')
open('emission_conformance.mjs','w').write(src)"

run_case emission-headline-hand-written "PASS headline must be DERIVED from fields the cases write" "
src = open('emission_conformance.mjs').read()
src = src.replace('const MEASURED = {};', 'const MEASURED_ = {};').replace('MEASURED.', 'MEASURED_.')
open('emission_conformance.mjs','w').write(src)"

run_case emission-adversaries-refused "canonical-drift adversary and the semantic-equivalence adversary must be SEPARATE" "
src = open('emission_conformance.mjs').read()
src = src.replace('const driftEmit = (r) => {', 'const notTheDriftEmitter = (r) => {')
open('emission_conformance.mjs','w').write(src)"

run_case emission-i4c-fixture-dropped "must carry the ACTUAL I-4c" "
src = open('emission_conformance.mjs').read()
src = src.replace('ADD(IN(\"x\"), ADD(IN(\"x\"), IN(\"y\")))', 'ADD(IN(\"x\"), IN(\"y\"))')
open('emission_conformance.mjs','w').write(src)"

run_case label-allocation-claimed-semantic "must separate label EQUALITY/FRESHNESS structure" "
src = open('lowering.mjs').read()
src = src.replace('label_semantics:', 'label_notes:')
open('lowering.mjs','w').write(src)"

run_case label-superseded-ids-erased "B6 emission and executable-encoding ids must be KEPT on the record" "
src = open('lowering.mjs').read()
src = src.replace('export const SUPERSEDED_LABEL_SEMANTICS_SEM_IDS', 'const _dropped_SUPERSEDED_LABEL')
open('lowering.mjs','w').write(src)"

run_case emission-ladder-flattened "must state the identity LADDER" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.emission-conformance' and e.get('canonical'):
        e['statement'] = e['statement'].replace('THREE IDENTITIES FORM A LADDER, AND EMISSION PROVES THE MIDDLE ONE', 'Two properties are proved separately')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case emission-gate-not-in-pack "verify.sh must RUN emission_conformance" "
src = open('make_review_pack.sh').read()
src = src.replace('run \"emission conformance\" governance node emission_conformance.mjs', '')
open('make_review_pack.sh','w').write(src)"

run_case emission-expected-table "must contain NO expected identity literals" "
src = open('emission_conformance.mjs').read()
src = src.replace('const RECORDS = FIXTURES.map', 'const EXPECTED = \"ctmpl-d0105d4f5dc3e4aa\";\nconst RECORDS = FIXTURES.map')
open('emission_conformance.mjs','w').write(src)"

run_case emission-integration-unlabelled "must be LABELLED an integration theorem" "
src = open('emission_conformance.mjs').read()
src = src.replace('INTEGRATION', 'downstream')
open('emission_conformance.mjs','w').write(src)"

run_case emission-domain-claim-lost "must record that emission's domain is the CLOSED TEMPLATE" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.emission-conformance' and e.get('canonical'):
        e['statement'] = e['statement'].replace('FUNCTION OF THE CLOSED TEMPLATE AND NOT OF THE PROGRAM', 'function of the program')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case emission-alpha-correction-lost "ALPHA-EQUIVALENT alternate emitter produces the IDENTICAL" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.emission-conformance' and e.get('canonical'):
        e['statement'] = e['statement'].replace('byte-equivariant under alpha-renaming and label permutation', 'sensitive to renaming')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case phase-pin-lint-unwired "must exist and be INVOKED by both negative runners" "
src = open('negative_battery.sh').read()
src = src.replace('python3 \"\$BASE/phase_pin_lint.py\"', 'true \"\$BASE/phase_pin_lint.py\"', 1)
open('negative_battery.sh','w').write(src)"

run_case phase-pin-exemption-unused "history exemption must be BOTH implemented in the lint and USED" "
src = open('negative_battery.sh').read()
src = src.replace('# HISTORY_PIN_OK:', '# history pin:')
open('negative_battery.sh','w').write(src)"

run_case film-budget-parse-lax "must parse --budget with strtol.s ENDPTR checked" "
src = open('bridge/ic32_film.c').read()
src = src.replace('long v = strtol(s, &end, 10);', 'long v = strtol(s, NULL, 10); end = NULL;')
open('bridge/ic32_film.c','w').write(src)"

run_case film-budget-overflow-ignored "errno" "
src = open('bridge/ic32_film.c').read()
src = src.replace('if (errno == ERANGE)  refuse(\"film-budget-invalid\");', '')
open('bridge/ic32_film.c','w').write(src)"

run_case film-unknown-flag-becomes-term "must refuse an argument it cannot use" "
src = open('bridge/ic32_film.c').read()
src = src.replace('else if (argv[i][0] == \'-\' && argv[i][1]) refuse(\"film-unknown-flag\");', '')
open('bridge/ic32_film.c','w').write(src)"

run_case film-projection-guess "must REFUSE rather than choose when a dup cell" "
src = open('bridge/ic32_film.c').read()
src = src.replace('film-projection-not-unique', 'film-projection-picked')
open('bridge/ic32_film.c','w').write(src)"

run_case film-expected-table-in-emitter "contains the church_exp_2_2 fixture term" "
src = open('bridge/ic32_film.c').read()
src = src.replace('#define PLANE_POOL ',
  '#define EXPECTED_FIXTURE \"((lf.lx.!&1001{c0,c1}=f;(c0 (c1 x)) X) S)\"\n#define PLANE_POOL ')
open('bridge/ic32_film.c','w').write(src)"

run_case film-expected-table-in-comparator "contains the church_exp_2_2 fixture term" "
src = open('bridge/measure_compare.mjs').read()
src = src.replace('const BUDGET = 4096;',
  'const BUDGET = 4096;\nconst EXPECTED = { term: \"!&1001{c0,c1}\", frames: 21 };')
open('bridge/measure_compare.mjs','w').write(src)"

run_case film-comparator-absent "cites bridge/measure_compare.mjs, which is absent" "
import os
os.remove('bridge/measure_compare.mjs')"

run_case film-scope-inflated "no longer states its scope as CHECKED refusals" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'film.native-emission':
        e['statement'] = e['statement'].replace('REFUSED BY NAME', 'handled')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-planes-collapsed "must keep the two transition systems apart" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'film.native-emission':
        e['statement'] = e['statement'].replace('film_planes', 'one unified relation')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-canonicalizer-copied "must INCLUDE ic32_canon.c rather than copy it" "
src = open('bridge/ic32_film.c').read()
src = src.replace('#define IC32_CANON_NO_MAIN 1', '/* copied instead */')
open('bridge/ic32_film.c','w').write(src)"

run_case film-quiescence-asserted "must CHECK pool-quiescence at the terminal" "
src = open('bridge/ic32_film.c').read()
src = src.replace('film-not-quiescent-at-terminal', 'film-terminal-noted')
open('bridge/ic32_film.c','w').write(src)"

run_case film-unhandled-rule-unnamed "refuse an unhandled enumerated rule BY NAME" "
src = open('bridge/ic32_film.c').read()
src = src.replace('film-rule-not-implemented', 'film-rule-skipped')
open('bridge/ic32_film.c','w').write(src)"

run_case film-locus-alias-blessed "must REFUSE a canonical-locus alias" "
src = open('bridge/ic32_film.c').read()
src = src.replace('film-locus-alias', 'film-locus-duplicate-ok')
open('bridge/ic32_film.c','w').write(src)"

run_case film-budget-untyped "must have a TYPED REFUSAL for the budget" "
src = open('bridge/ic32_film.c').read()
src = src.replace('film-budget-exhausted', 'film-stopped-early')
open('bridge/ic32_film.c','w').write(src)"

run_case accidental-check-unrecorded "must record why the readback INTERACTION-COUNT check" "
src = open('bridge/ic32_film.c').read()
src = src.replace('ACCIDENTALLY TRUE', 'previously verified')
open('bridge/ic32_film.c','w').write(src)"

run_case film-law-accident-scrubbed "must keep the record of the readback check that was removed" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'film.native-emission':
        e['statement'] = e['statement'].replace('ACCIDENTALLY TRUE', 'redundant')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-emitter-absent "cites bridge/film_check.mjs, which is absent" "
import os
os.remove('bridge/film_check.mjs')"

# ── round 23: a skipped gate is not a green one ─────────────────────────────
run_case skip-reads-as-green "must make the native gates REQUIRED by default" "
src = open('make_review_pack.sh').read()
src = src.replace('verdict downgraded to PARTIAL', 'not run')
open('make_review_pack.sh','w').write(src)"

run_case pack-transcribes-its-count "must COUNT what it ran" "
src = open('make_review_pack.sh').read()
src = src.replace('ATTEMPTED=\$((ATTEMPTED + 1))', ': # counted elsewhere')
open('make_review_pack.sh','w').write(src)"

run_case pack-runs-past-a-bad-manifest "failed manifest must ABORT the review pack" "
src = open('make_review_pack.sh').read()
src = src.replace('aborting before running anything', 'continuing anyway')
open('make_review_pack.sh','w').write(src)"

run_case gating-probes-undeclared "must declare gating_probes" "
import json
m = json.load(open('artifacts.json'))
del m['gating_probes']
json.dump(m, open('artifacts.json','w'), indent=2)"

run_case pack-globs-the-probes "must READ gating_probes rather than glob" "
src = open('make_review_pack.sh').read()
src = src.replace(chr(36) + \"(cd governance && python3 -c \\\"\\nimport json; print(' '.join(json.load(open('artifacts.json'))['gating_probes'])))\\\"\", 'probe_*_repro.mjs')
src = src.replace(\"json.load(open('artifacts.json'))['gating_probes']\", \"['probe_execreg_v08_repro.mjs']\")
open('make_review_pack.sh','w').write(src)"

run_case gate-list-drifts-from-registry "gating probe list and artifacts.json's gating_probes disagree" "
import json
m = json.load(open('artifacts.json'))
m['gating_probes'] = [p for p in m['gating_probes'] if p != 'probe_execreg_v08_repro.mjs']
json.dump(m, open('artifacts.json','w'), indent=2)"


# ── round 24: a launch descriptor may not carry an action ───────────────────
run_case execute-takes-a-launcher-again "execute must take no" "
src = open('derive_protocol.mjs').read()
src = src.replace('async execute(req) {', 'async execute(req, launcher) {')
open('derive_protocol.mjs','w').write(src)"

run_case naming-setter-restored "nameArtifact must be gone from the authority" "
src = open('derive_protocol.mjs').read()
src = src.replace('  async execute(req) {',
  '  nameArtifact(d, f) { return { ok: true }; }\n  async execute(registry, req) {')
open('derive_protocol.mjs','w').write(src)"

run_case host-module-deleted "observed_execution_host.mjs absent" "
import os
os.remove('observed_execution_host.mjs')"

run_case entrypoint-escapes-its-closure "entrypoint is not inside the closure it hashes" "
src = open('observed_execution_host.mjs').read()
src = src.replace('catalog-entrypoint-outside-closure', 'catalog-entrypoint-noted')
open('observed_execution_host.mjs','w').write(src)"

run_case catalog-accepts-extra-fields "carrying any field beyond" "
src = open('observed_execution_host.mjs').read()
src = src.replace('catalog-entry-extra-field', 'catalog-entry-extra-ok')
open('observed_execution_host.mjs','w').write(src)"

run_case invocation-may-be-a-callable "must canonicalise the invocation" "
src = open('observed_execution_host.mjs').read()
src = src.replace('canonicalBytes(invocation)', 'JSON.stringify(invocation)')
open('observed_execution_host.mjs','w').write(src)"

run_case sessions-collapse-to-one "must report executor_sessionS" "
src = open('derive_protocol.mjs').read()
src = src.replace('executor_sessions: observed.executor_sessions',
                  'executor_session_id: observed.executor_sessions[0]')
open('derive_protocol.mjs','w').write(src)"

run_case authority-keeps-its-own-table "authority must hold NO observation table" "
src = open('derive_protocol.mjs').read()
src = src.replace('  #issued = new Map();', '  #issued = new Map();\n  #observed = new Map();')
open('derive_protocol.mjs','w').write(src)"

run_case provenance-law-v4-deleted "implementation-provenance@4 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if not (e['id'] == 'derivation.implementation-provenance' and e.get('canonical'))]
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case launch-descriptor-rule-dropped "no longer carries the launch-descriptor rule" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.implementation-provenance' and e.get('canonical'):
        e['statement'] = e['statement'].replace(
            'a launch descriptor may not carry both the evidence and an independent executable action',
            'the authority hashes what it launches')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case v3-history-made-current "implementation-provenance@3 must stay on the record as history" "
# HISTORY_PIN_OK: subject is @3, superseded; the case exists to keep it history
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.implementation-provenance' and e['revision'] == 3:
        e['canonical'] = True
json.dump(g, open('invariant-grid.json','w'), indent=1)"


# ── round 25: acceptance takes no semantic oracle either ────────────────────
run_case acceptance-takes-a-registry "taking EXACTLY" "
src = open('derive_protocol.mjs').read()
src = src.replace('  accept(req, res) {', '  accept(registry, req, res) {')
open('derive_protocol.mjs','w').write(src)"

run_case registry-accepted-not-built "must BUILD its registry at construction" "
src = open('derive_protocol.mjs').read()
src = src.replace('constructor(reader, programImage = [], executorCatalog = null) {',
                  'constructor(reader, programImage, executorCatalog = null) {')
open('derive_protocol.mjs','w').write(src)"

run_case oracle-comes-from-outside "must re-derive through the authority" "
src = open('derive_protocol.mjs').read()
src = src.replace('validateForeignResultOwned(this.#registry, issued, ownRes)',
                  'validateForeignResultOwned(arguments[2] ?? this.#registry, issued, ownRes)')
open('derive_protocol.mjs','w').write(src)"

run_case worker-image-from-a-parameter "program image must be the AUTHORITY" "
src = open('derive_protocol.mjs').read()
src = src.replace('programs: this.#registry.image()', 'programs: []')
open('derive_protocol.mjs','w').write(src)"

run_case acceptance-law-deleted "law derivation.acceptance-authority@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'derivation.acceptance-authority']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case ownership-becomes-a-typecheck "must say why a type check does not close it" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.acceptance-authority':
        e['statement'] = e['statement'].replace('instanceof', 'a suitable')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case supplier-list-left-open "must name what a caller may still supply" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.acceptance-authority':
        e['statement'] = e['statement'].replace('an INTENT and a RESULT TO ', 'whatever remains to ')
json.dump(g, open('invariant-grid.json','w'), indent=1)"


# ── round 25: the source language reaches the governed runtime ──────────────
run_case lowering-module-deleted "lowering.mjs absent" "
import os
os.remove('lowering.mjs')"

run_case lowering-law-downgraded "derivation.canonical-lowering has no canonical" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.canonical-lowering':
        e['status'] = 'OPEN'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case lowering-gets-a-film "must rule that lowering gets NO film" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.canonical-lowering':
        e['statement'] = e['statement'].replace('THE INSTRUMENT IS RE-LOWERING, NOT A FILM',
                                                'lowering emits a film per pass')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# inputs-model-decided-by-accident was here until B1.2.1. It required
# canonical-lowering to KEEP the wording "DEFERRED AND NAMED: whether lowering
# is PARAMETERIZED or INSTANTIATED", and B1.2.1 revised the law to record the
# DECISION instead — B1 decided the model and B1.1 ruled the framing a false
# choice, so for three passes both the law and this case were defending a
# question that had been answered. The assertion it perturbs no longer exists,
# so the case had stopped having a subject. DELETED, not repointed, on the B1
# precedent below. Its live replacement is inputs-model-deferred-again.

# inputs-silently-lowered was here until B1: it flipped decided:false -> true and
# asserted "must record the inputs model as UNDECIDED". B1 decided the model, so
# its perturbation became the live state and the case went VACUOUS -- it changed
# no artifact and tested nothing. DELETED rather than repointed, because its
# premise is what the round reversed; inputs-model-reverted above is the same
# guard for the new state, in the new direction.

run_case execution-grades-collapsed "must separate OBSERVED execution from FILM-EVIDENCED" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.lowering-refinement':
        e['statement'] = e['statement'].replace('TWO GRADES OF EVIDENCE FOR THE EXECUTION LEG',
                                                'the execution is evidenced')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-gap-unlocated "must name exactly WHAT is still open on the execution leg" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.lowering-refinement':
        e['statement'] = e['statement'].replace('DUP-* rule actually becomes enabled',
                                                'harder case remains')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-gap-not-measured "must assert the execution leg" "
src = open('lowering_check.mjs').read()
src = src.replace('execution-leg-is-film-evidenced', 'execution-leg-noted')
open('lowering_check.mjs','w').write(src)"

run_case identities-may-collapse "must assert the chain's identities differ" "
src = open('lowering_check.mjs').read()
src = src.replace('chain-identities-stay-distinct', 'chain-identities-listed')
open('lowering_check.mjs','w').write(src)"


# ── round 26: an instanceof guard is satisfied by a subclass ────────────────
run_case host-accepted-not-built "must BUILD its execution host from CATALOG DATA" "
src = open('derive_protocol.mjs').read()
src = src.replace('this.#host = executorCatalog === null ? null : new ObservedExecutionHost(executorCatalog);',
  'this.#host = executorCatalog instanceof ObservedExecutionHost ? executorCatalog : null;')
open('derive_protocol.mjs','w').write(src)"

run_case ownership-becomes-a-prototype-check "NOT with a tighter type check" "
src = open('derive_protocol.mjs').read()
src = src.replace('this.#reader = reader;',
  'if (executorCatalog && Object.getPrototypeOf( host ) === null) {}\n    this.#reader = reader;', 1)
open('derive_protocol.mjs','w').write(src)"

run_case host-ownership-law-deleted "law derivation.host-ownership@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'derivation.host-ownership']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case ownership-question-restated "must say that the question is who built the object" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.host-ownership':
        e['statement'] = e['statement'].replace('WHO BUILT IT', 'what it descends from')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case spike-status-reverted "still says the spike is not built" "
import json
g = json.load(open('invariant-grid.json'))
g['lowering_spike']['status'] = 'DECLARED, not built.'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case execution-grades-merged-in-record "must carry the two execution grades separately" "
import json
g = json.load(open('invariant-grid.json'))
del g['lowering_spike']['film_grade']
json.dump(g, open('invariant-grid.json','w'), indent=1)"


# ── round 27: sever before validating ───────────────────────────────────────
run_case bind-hashes-before-severing "must SEVER the AST before computing its identity" "
src = open('derive_protocol.mjs').read()
src = src.replace('const owned = ownCanonical(ast);\n    const id = programSemId(owned);',
                  'const id = programSemId(ast);\n    const owned = ownCanonical(ast);')
open('derive_protocol.mjs','w').write(src)"

run_case catalog-validated-in-place "catalog must be snapshotted ONCE before validation" "
src = open('observed_execution_host.mjs').read()
src = src.replace('JSON.parse(canonicalBytes(catalog))', 'catalog')
open('observed_execution_host.mjs','w').write(src)"

run_case catalog-accepts-a-map "must be canonical plain" "
src = open('observed_execution_host.mjs').read()
src = src.replace('host-catalog-must-be-plain-data', 'host-catalog-map-ok')
open('observed_execution_host.mjs','w').write(src)"

run_case snapshot-law-deleted "law derivation.owned-snapshot@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'derivation.owned-snapshot']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── round 27A.1: authenticate once, then act on a later read ────────────────
run_case execute-runs-the-presented-request "must carry the ISSUED request" "
src = open('derive_protocol.mjs').read()
src = src.replace('message: issued }', 'message: req }')
open('derive_protocol.mjs','w').write(src)"

run_case wasissued-answers-only-yes "must return the issued request and not only a boolean" "
src = open('derive_protocol.mjs').read()
src = src.replace('? { ok: true, request: stored.request }', '? { ok: true }')
open('derive_protocol.mjs','w').write(src)"

run_case accept-reads-the-live-result "accept/res must be snapshotted at method entry" "
src = open('derive_protocol.mjs').read()
src = src.replace('ownRes = ownCanonical(res);', 'ownRes = res;')
open('derive_protocol.mjs','w').write(src)"

run_case authorize-reads-the-live-intent "authorize/intent must be snapshotted at method entry" "
src = open('derive_protocol.mjs').read()
src = src.replace('ownIntent = ownCanonical(intent);', 'ownIntent = intent;')
open('derive_protocol.mjs','w').write(src)"

run_case snapshot-helper-inlined "snapshot must be ONE exported function" "
src = open('derive_protocol.mjs').read()
src = src.replace('export function ownCanonical(v) {', 'function ownCanonical(v) {')
open('derive_protocol.mjs','w').write(src)"

run_case host-runs-the-presented-invocation "must launch the SNAPSHOT it keyed" "
src = open('observed_execution_host.mjs').read()
src = src.replace('runNodeWorker(entry, owned)', 'runNodeWorker(entry, invocation)')
open('observed_execution_host.mjs','w').write(src)"

# ── round 27A.2: GPT's four cleanups ───────────────────────────────────────
run_case acceptance-rebuilds-the-invocation "invocation THAT ACTUALLY CROSSED" "
src = open('derive_protocol.mjs').read()
src = src.replace('this.#executions.get(ownReq?.request_id)', '[]')
open('derive_protocol.mjs','w').write(src)"

run_case host-hides-what-it-keyed "must return the invocation bytes it keyed" "
src = open('observed_execution_host.mjs').read()
src = src.replace('input_canonical: inputCanonical', 'input_canonical: undefined')
open('observed_execution_host.mjs','w').write(src)"

run_case validators-exported-unsnapshotted "must exist as checkRequestOwned" "
src = open('derive_protocol.mjs').read()
src = src.replace('export const checkRequest = (req) => {', 'const checkRequest = (req) => {')
open('derive_protocol.mjs','w').write(src)"

run_case accessor-execution-scope-dropped "must DECLARE OPEN that canonicalisation runs caller accessor" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.entry-snapshot':
        e['statement'] = e['statement'].replace('MAY INVOKE JavaScript accessor and Proxy behaviour',
                                                'never invokes caller behaviour')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case read-count-called-terminating "must say that the read-count enumeration does not terminate" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.entry-snapshot':
        e['statement'] = e['statement'].replace('REGRESSION DETECTOR AND NOT A TERMINATING PROOF',
                                                'a terminating proof')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case historical-fact-clause-dropped "must record that acceptance may not rebuild a past invocation" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.entry-snapshot':
        e['statement'] = e['statement'].replace('HISTORICAL FACT IS NOT A FUNCTION OF CURRENT CONFIGURATION',
                                                'state is state')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── round 27A.3: multiplicity must preserve correlation ────────────────────
run_case artifact-id-decorrelated "must be built from TUPLES" "
src = open('observed_execution_host.mjs').read()
src = src.replace('executable_artifact_id: artifacts.length === 1 ? artifacts[0] : null,',
                  'executable_artifact_id: artifacts[0],')
open('observed_execution_host.mjs','w').write(src)"

run_case authority-merges-field-by-field "must go through the host's summariser" "
src = open('derive_protocol.mjs').read()
src = src.replace('return summariseObservations(hits.flatMap((o) => o.execution_observations));',
                  'return hits[0];')
open('derive_protocol.mjs','w').write(src)"

run_case acceptance-hides-the-tuples "must surface the correlated evidence" "
src = open('derive_protocol.mjs').read()
src = src.replace('execution_observations: observed.execution_observations',
                  'execution_observations: undefined')
open('derive_protocol.mjs','w').write(src)"

run_case multiplicity-law-deleted "law derivation.observation-multiplicity@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'derivation.observation-multiplicity']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case multiplicity-law-narrowed "must state the general rule" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.observation-multiplicity':
        e['statement'] = e['statement'].replace(
            'EVIDENCE FIELDS THAT VARY TOGETHER MAY NOT BE INDEPENDENTLY COLLAPSED',
            'the artifact id must be reported too and must not be collapsed')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case multiplicity-severity-inflated "must carry its severity as STRUCTURED metadata" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.observation-multiplicity':
        e['defect_class'] = 'authority-forgery'
        e['accepted_false_verdict'] = True
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case severity-contrast-erased "must be expressed in DATA" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.entry-snapshot':
        e['accepted_false_verdict'] = False
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case defect-class-off-vocabulary "not in defect_class_vocabulary" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.observation-multiplicity':
        e['defect_class'] = 'mild-oopsie'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case defect-class-without-answers "declares a defect_class without answering both severity questions" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.observation-multiplicity':
        del e['underlying_observations_genuine']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case literal-nul-in-source "contains a literal NUL byte" "
b = open('observed_execution_host.mjs','rb').read()
b = b.replace(b'\\\\u0000', b'\\x00')
open('observed_execution_host.mjs','wb').write(b)"

# ── B1: the inputs model, decided and not built ────────────────────────────
run_case inputs-model-reverted "must record the inputs model as DECIDED" "
src = open('lowering.mjs').read()
src = src.replace('  decided: true,', '  decided: false,')
open('lowering.mjs','w').write(src)"

# decided-reads-as-implemented was here until B2. It flipped `implemented`
# false -> true, and at B2 that IS the live state, so the perturbation had
# nothing left to change. Its inverse is the live case now:
# inputs-model-reads-unimplemented, below.

run_case instantiation-id-merged-into-lowering "instantiation must have its OWN relation identity" "
src = open('lowering.mjs').read()
src = src.replace('export const INSTANTIATION_SEM_ID =', 'const INSTANTIATION_SEM_ID =')
open('lowering.mjs','w').write(src)"

run_case falsifier-dropped "must declare all THREE port witnesses" "
src = open('lowering.mjs').read()
src = src.replace('id: \"I-4c\"', 'id: \"I-4c-disabled\"')
open('lowering.mjs','w').write(src)"

run_case port-names-normalized "must refuse Unicode normalization" "
src = open('lowering.mjs').read()
src = src.replace('NOT Unicode-normalized', 'Unicode-normalized (NFC)')
open('lowering.mjs','w').write(src)"

# ── B1.1: semantics are hashed, lifecycle is not ───────────────────────────
run_case semantic-id-hashes-lifecycle "must hash the SEMANTICS records and never the combined spec" "
src = open('lowering.mjs').read()
src = src.replace('canonicalBytes(LOWERING_SEMANTICS)', 'canonicalBytes(LOWERING_SPEC)')
open('lowering.mjs','w').write(src)"

run_case semantics-status-merged "must separate SEMANTICS" "
src = open('lowering.mjs').read()
src = src.replace('export const LOWERING_STATUS = Object.freeze', 'const LOWERING_STATUS = Object.freeze')
open('lowering.mjs','w').write(src)"

run_case transitional-ids-erased "overbound B1 identities must be KEPT" "
src = open('lowering.mjs').read()
src = src.replace('export const OVERBOUND_TRANSITIONAL_SEM_IDS', 'const OVERBOUND_TRANSITIONAL_SEM_IDS')
open('lowering.mjs','w').write(src)"

run_case sem-v2-tag-reverted "corrected projections must carry a NEW domain tag" "
src = open('lowering.mjs').read()
src = src.replace('TRVM-LOWERING-SEM-v2', 'TRVM-LOWERING-v1')
open('lowering.mjs','w').write(src)"

run_case extras-refused-again "extra canonical inputs must be IGNORED" "
src = open('lowering.mjs').read()
src = src.replace('extra_input: \"IGNORED.', 'extra_input: \"REFUSED.')
open('lowering.mjs','w').write(src)"

run_case refinement-scope-dropped "must state its DOMAIN before B2 builds anything" "
src = open('lowering.mjs').read()
src = src.replace('export const REFINEMENT_SCOPE = Object.freeze', 'const REFINEMENT_SCOPE_UNUSED = Object.freeze')
open('lowering.mjs','w').write(src)"

run_case i4c-fixture-unmandated "I-4c must MANDATE an asymmetric fixture" "
src = open('lowering.mjs').read()
src = src.replace('fixture_is_mandatory:', 'fixture_note:')
open('lowering.mjs','w').write(src)"

run_case instantiation-law-head-deleted "derivation.instantiation-identity has no canonical" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if not (e['id'] == 'derivation.instantiation-identity'
                                        and e.get('canonical'))]
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case spike-record-contradicts-source "still says the inputs model is UNDECIDED" "
import json
g = json.load(open('invariant-grid.json'))
g['lowering_spike']['status'] = g['lowering_spike']['status'] + ' Also: inputs model UNDECIDED.'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# THE FORGERY REVERSED, BECAUSE THE FACT REVERSED. This case used to set
# implemented=True and expect "must stay false" — correct while the port was
# open, and after B2 built it the case was enforcing a lie: the battery, the
# grid and grid_check all agreed with each other and all three disagreed with
# the code. A negative case pinned to a phase value is the same ratchet as the
# assertion it guards, and it is the reason the stale record survived four
# passes with a green 298/298 beside it. Both directions are forged now, and
# neither expectation names a polarity.
run_case spike-record-denies-implemented "must EQUAL INPUTS_MODEL.implemented" "
import json
g = json.load(open('invariant-grid.json'))
g['lowering_spike']['inputs_model']['implemented'] = False
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case spike-status-denies-implemented "still says .input. is NOT IMPLEMENTED" "
import json
g = json.load(open('invariant-grid.json'))
g['lowering_spike']['status'] = g['lowering_spike']['status'] + ' Also: input NOT IMPLEMENTED.'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case spike-falsifiers-reported-unwritten "must agree with the STATUS FIELDS of INSTANTIATION_FALSIFIERS" "
import json
g = json.load(open('invariant-grid.json'))
g['lowering_spike']['inputs_model']['falsifier_status'] = 'DECLARED, none written; B2 writes them'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# The two chain strings, each forged the way it was ACTUALLY stale: one lost
# nodes, the other had them in an order the data does not have.
run_case spike-chain-drops-emission "inputs_model.chain names the chain nodes" "
import json
g = json.load(open('invariant-grid.json'))
im = g['lowering_spike']['inputs_model']
im['chain'] = im['chain'].replace('closed_template_sem_id -(emission_sem_id)-> ', '')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case spike-chain-reordered "identities.chain names the chain nodes" "
import json
g = json.load(open('invariant-grid.json'))
i = g['lowering_spike']['identities']
i['chain'] = i['chain'].replace('target_nf_sem_id -(decode_sem_id)-> outcome_sem_id',
                                'outcome_sem_id -(decode_sem_id)-> target_nf_sem_id')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case spike-film-scope-outlives-the-law "still lists BUDGET_EXHAUSTED as an OPEN gap" "
import json
g = json.load(open('invariant-grid.json'))
g['lowering_spike']['film_grade'] += ' STILL OPEN: BUDGET_EXHAUSTED as native film evidence rather than a typed refusal.'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case spike-scope-stale-op-list "scope must name the BUILT ops" "
import json
g = json.load(open('invariant-grid.json'))
g['lowering_spike']['scope'] = 'the PURE fragment only - const and add first, then input/sub/mul/len.'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case instantiation-history-erased "cites unknown law derivation.instantiation-identity@1" "
# HISTORY_PIN_OK: subject is instantiation-identity@1, cited history
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if not (e['id'] == 'derivation.instantiation-identity'
                                        and e['revision'] == 1)]
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case instantiation-law-picks-a-side "must record that PARAMETERIZED versus INSTANTIATED was a false choice" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.instantiation-identity':
        e['statement'] = e['statement'].replace('FALSE CHOICE', 'settled question')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case instantiation-law-overclaims "evidence must say that the three falsifiers are DECLARED" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.instantiation-identity':
        e['evidence'] = e['evidence'].replace('carries NO claim about instantiation behaviour',
                                              'establishes instantiation behaviour')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── B1.2: the template layer ───────────────────────────────────────────────
run_case template-layer-removed "must have a TARGET TEMPLATE layer" "
src = open('lowering.mjs').read()
src = src.replace('export function emit(template, profile', 'function emit(template, profile')
open('lowering.mjs','w').write(src)"

run_case receipt-ends-at-the-term "LoweringReceipt must end there" "
src = open('lowering.mjs').read()
src = src.replace('export function loweringReceipt(program_sem_id, target_template_sem_id)',
                  'export function loweringReceipt(program_sem_id, target_term_sem_id)')
open('lowering.mjs','w').write(src)"

# B7: THIS CASE WENT VACUOUS THE MOMENT THE FRAGMENT GREW. It hard-typed
# ['const','add','input'] and B7 made the list ['const','add','input','sub'], so
# the replacement stopped matching and the runner reported VACUOUS rather than a
# missed forgery — the non-vacuity detector earning its keep for the fourth time
# in this line. The subject of the case is that `input` may not leave the hashed
# semantics, so `input` is what it removes, from whatever the list happens to be.
run_case input-dropped-from-semantics "hashed lowering semantics must include" "
import re
src = open('lowering.mjs').read()
m = re.search(r'lowered_ops: Object\.freeze\(\[(.*?)\]\)', src)
assert m, 'input-dropped-from-semantics: lowered_ops no longer matches'
kept = [x for x in m.group(1).split(', ') if 'input' not in x]
assert len(kept) < len(m.group(1).split(', ')), 'input-dropped-from-semantics: no input entry to drop'
src = src[:m.start()] + 'lowered_ops: Object.freeze([' + ', '.join(kept) + '])' + src[m.end():]
open('lowering.mjs','w').write(src)"

run_case status-refusal-made-semantic "must NOT be a semantic refusal" "
src = open('lowering.mjs').read()
src = src.replace('\"lower-negative\", \"lower-reads-undecided\"]),',
                  '\"lower-negative\", \"lower-reads-undecided\", \"lower-input-not-implemented\"]),')
open('lowering.mjs','w').write(src)"

run_case consumed-inputs-collapsed "must keep SUPPLIED and CONSUMED inputs distinct" "
src = open('lowering.mjs').read()
src = src.replace('  consumed_inputs:', '  consumed_inputs_removed:')
open('lowering.mjs','w').write(src)"

run_case template-allows-allocation "must record WHY allocation cannot be semantic" "
src = open('lowering.mjs').read()
src = src.replace('  no_names_no_labels:', '  binder_naming:')
open('lowering.mjs','w').write(src)"

# ── B1.2.1: emit() is not a hidden semantic relation ───────────────────────
# GPT's find. B1.2 named instantiation's codomain in PROSE, so changing the add
# combinator changed the executable term and moved no id that owns it.
run_case executable-encoding-unbound "must be CONTENT-BOUND and named as instantiation's codomain" "
src = open('lowering.mjs').read()
src = src.replace('  codomain_encoding_sem_id: TARGET_EXECUTABLE_ENCODING_SEM_ID,', '')
open('lowering.mjs','w').write(src)"

run_case executable-encoding-id-is-a-label "must be CONTENT-BOUND" "
src = open('lowering.mjs').read()
src = src.replace('H(\"TRVM-TARGET-EXECUTABLE-ENC-v1|\" + canonicalBytes(TARGET_ENCODING))',
                  'H(\"TRVM-TARGET-EXECUTABLE-ENC-v1\")')
open('lowering.mjs','w').write(src)"

# THE DUAL: lowering re-bound to the emitter two layers downstream.
run_case lowering-rebound-to-the-emitter "must NOT bind the executable encoding" "
src = open('lowering.mjs').read()
src = src.replace('  codomain: \"TRVM-TARGET-TEMPLATE-v1\",',
                  '  target_encoding: TARGET_ENCODING,\n  codomain: \"TRVM-TARGET-TEMPLATE-v1\",')
open('lowering.mjs','w').write(src)"

run_case per-op-lowering-rules-dropped "must state its per-op map instead" "
src = open('lowering.mjs').read()
src = src.replace('  op_lowering_rules: Object.freeze', '  op_lowering_notes: Object.freeze')
open('lowering.mjs','w').write(src)"

# THE REFUSAL VOCABULARIES, crossed back the way B1.2 had them.
# B7.1r: THE VOCABULARY MOVED TO THE MAP, so this case moved with it. Its
# subject is unchanged — a source-fragment refusal may not sit in the record
# that owns emission's — and the owner is EMISSION_RULES now, because a LANGUAGE
# does not refuse and a MAP into it does.
run_case source-refusals-in-the-encoding "refusal vocabularies must belong to the records that own them" "
src = open('lowering.mjs').read()
head = src.index('export const EMISSION_RULES = Object.freeze({')
tail = src.index(chr(10) + '});' + chr(10), head)
j = src.index('  refusals: Object.freeze([', head)
k = src.index(']', j)
assert j < tail, 'source-refusals-in-the-encoding: no refusals list inside EMISSION_RULES'
Q = chr(34)
src = src[:j] + '  refusals: Object.freeze([' + Q + 'lower-unsupported-op' + Q + ', ' + Q + 'lower-negative' + Q + src[k:]
open('lowering.mjs','w').write(src)"

run_case lowering-claims-emit-refusals "may not claim emit-unbound-port" "
src = open('lowering.mjs').read()
src = src.replace('\"lower-negative\", \"lower-reads-undecided\"]),',
                  '\"lower-negative\", \"lower-reads-undecided\", \"emit-unbound-port\"]),')
open('lowering.mjs','w').write(src)"

run_case b12-ids-erased "B1.2 identities must be KEPT" "
src = open('lowering.mjs').read()
src = src.replace('export const SUPERSEDED_CODOMAIN_SEM_IDS', 'const SUPERSEDED_CODOMAIN_SEM_IDS')
open('lowering.mjs','w').write(src)"

run_case implemented-ops-name-blurred "must be named IMPLEMENTED_LOWERED_OPS" "
src = open('lowering.mjs').read()
src = src.replace('IMPLEMENTED_LOWERED_OPS', 'LOWERED_OPS')
open('lowering.mjs','w').write(src)"

run_case chain-not-machine-readable "identity chain must be MACHINE-READABLE" "
src = open('lowering.mjs').read()
src = src.replace('export const REFINEMENT_CHAIN = Object.freeze',
                  'const REFINEMENT_CHAIN_UNUSED = Object.freeze')
open('lowering.mjs','w').write(src)"

# unexercised-node-unexplained was here until B2. It renamed `why_not:`, which
# only exists on an UNEXERCISED chain node — and B2 exercised all nine, so there
# was nothing to rename. The mechanism is still guarded: the assertion requires
# an exercised flag on every node and a why_not on every node lacking one, and
# chain-flag-not-boolean below breaks it from the other side.
run_case chain-flag-not-boolean "identity chain must be MACHINE-READABLE" "
src = open('lowering.mjs').read()
src = src.replace('exercised: true,', 'exercised: \'yes\',')
open('lowering.mjs','w').write(src)"

run_case identity-set-hand-counted "must assert the chain's identities differ and DERIVE the set" "
src = open('lowering_check.mjs').read()
src = src.replace('chain-identities-stay-distinct', 'six-identities-stay-distinct')
open('lowering_check.mjs','w').write(src)"

run_case identity-set-stops-deriving "DERIVE the set from REFINEMENT_CHAIN" "
src = open('lowering_check.mjs').read()
src = src.replace('REFINEMENT_CHAIN.filter((n) => n.exercised)', 'REFINEMENT_CHAIN.slice(0, 6)')
open('lowering_check.mjs','w').write(src)"

run_case three-way-separation-unmeasured "must MEASURE the three-way separation" "
src = open('lowering_check.mjs').read()
src = src.replace('emit-is-not-a-hidden-relation', 'emit-is-documented')
open('lowering_check.mjs','w').write(src)"

# ── B2: the inputs relation becomes executable ─────────────────────────────
run_case rules-revert-to-prose "op_lowering_rules must be STRUCTURAL" "
src = open('lowering.mjs').read()
src = src.replace('    target: Object.freeze({ t: \"church\", n: Object.freeze({ from_field: \"value\" }) }),',
                  '    target: \"a const becomes a church node\",')
open('lowering.mjs','w').write(src)"

run_case lower-stops-interpreting-the-table "must INTERPRET it" "
src = open('lowering.mjs').read()
src = src.replace('const rule = LOWERING_SEMANTICS.op_lowering_rules[node.op];',
                  'const rule = HARDCODED_RULES[node.op];')
open('lowering.mjs','w').write(src)"

run_case port-transform-dropped "the no-normalization ruling made structural" "
src = open('lowering.mjs').read()
src = src.replace('source_name: Object.freeze({ from_field: \"name\", transform: \"identity\" })',
                  'source_name: Object.freeze({ from_field: \"name\" })')
open('lowering.mjs','w').write(src)"

run_case shortcut-path-restored "must not return a target_term" "
src = open('lowering.mjs').read()
src = src.replace('    return { ok: true, template, target_template_sem_id: targetTemplateSemId(template),',
                  '    return { ok: true, template, target_term: emit(template), target_template_sem_id: targetTemplateSemId(template),')
open('lowering.mjs','w').write(src)"

run_case instantiate-mints-its-own-id "must not compute target_term_sem_id" "
src = open('lowering.mjs').read()
src = src.replace('    return { ok: true, closed_template: closed,',
                  '    return { ok: true, target_term_sem_id: \"self-certified\", closed_template: closed,')
open('lowering.mjs','w').write(src)"

run_case receipt-completeness-unchecked "must not compute target_term_sem_id" "
src = open('lowering.mjs').read()
src = src.replace('instantiation-receipt-incomplete', 'instantiation-receipt-partial')
open('lowering.mjs','w').write(src)"

run_case split-trigger-back-in-the-semantics "emission SPLIT TRIGGER must live in STATUS" "
src = open('lowering.mjs').read()
src = src.replace('  emission_split_trigger: \"SPLIT emission', '  emission_split_trigger_moved: \"SPLIT emission')
open('lowering.mjs','w').write(src)"

run_case split-trigger-loses-gpt-conditions "must live in STATUS and carry all four conditions" "
src = open('lowering.mjs').read()
src = src.replace('independently VERSIONED or REPLACEABLE', 'independently interesting')
open('lowering.mjs','w').write(src)"

run_case b121-ids-erased "B1.2.1 identities must be kept AND distinguished" "
src = open('lowering.mjs').read()
src = src.replace('export const SUPERSEDED_PROSE_RULE_SEM_IDS', 'const SUPERSEDED_PROSE_RULE_SEM_IDS')
open('lowering.mjs','w').write(src)"

run_case b121-ids-called-a-defect "the record must say NO DEFECT is claimed" "
src = open('lowering.mjs').read()
src = src.replace('NOT A DEFECT', 'A DEFECT of the same family')
open('lowering.mjs','w').write(src)"

run_case inputs-model-reads-unimplemented "must record the inputs model as DECIDED and IMPLEMENTED" "
src = open('lowering.mjs').read()
src = src.replace('  decided: true,\n  implemented: true,', '  decided: true,\n  implemented: false,')
open('lowering.mjs','w').write(src)"

run_case dead-refusal-name-returns "BOTH dead refusal names gone" "
src = open('lowering.mjs').read()
src = src.replace('throw new Error(\"lower-unsupported-op: \" + String(node.op));',
                  'throw new Error(\"lower-input-not-implemented\");')
open('lowering.mjs','w').write(src)"

run_case falsifiers-still-declared "must declare all THREE port witnesses as data" "
src = open('lowering.mjs').read()
src = src.replace('status: \"WITNESSED\"', 'status: \"DECLARED\"')
open('lowering.mjs','w').write(src)"

run_case chain-node-loses-its-flag "identity chain must be MACHINE-READABLE" "
src = open('lowering.mjs').read()
src = src.replace('{ id: \"decode_sem_id\", kind: \"relation\", exercised: true,',
                  '{ id: \"decode_sem_id\", kind: \"relation\",')
open('lowering.mjs','w').write(src)"

run_case migration-theorem-dropped "must carry migration-preserves-the-old-bytes" "
src = open('lowering_check.mjs').read()
src = src.replace('migration-preserves-the-old-bytes', 'migration-noted')
open('lowering_check.mjs','w').write(src)"

run_case receipt-selfcert-case-dropped "must carry receipt-is-not-self-certified" "
src = open('lowering_check.mjs').read()
src = src.replace('receipt-is-not-self-certified', 'receipt-built')
open('lowering_check.mjs','w').write(src)"

run_case i4a-case-dropped "must carry I-4a-allocation-is-not-semantic" "
src = open('lowering_check.mjs').read()
src = src.replace('I-4a-allocation-is-not-semantic', 'I-4a-noted')
open('lowering_check.mjs','w').write(src)"

run_case i4b-case-dropped "must carry I-4b-the-source-name-is-semantic" "
src = open('lowering_check.mjs').read()
src = src.replace('I-4b-the-source-name-is-semantic', 'I-4b-noted')
open('lowering_check.mjs','w').write(src)"

run_case i4c-case-dropped "must carry I-4c-binding-has-force" "
src = open('lowering_check.mjs').read()
src = src.replace('I-4c-binding-has-force', 'I-4c-noted')
open('lowering_check.mjs','w').write(src)"

# implementing-id-case-dropped was here until B2.1, when the case it guarded was
# RETIRED — its premise (only two fields changed since B1.2.1) expired, and
# keeping it would have meant growing an embedded copy of the module inside its
# own test. The three B2.1 cases above replace it.

# ── B2.1.2: the emission verdict is relative to its oracle ─────────────────
run_case emission-verifier-unnamed-relativity "must NAME its relativity" "
src = open('lowering.mjs').read()
src = src.replace('export function verifyEmissionReceiptAgainst(', 'export function verifyEmissionReceipt(')
src = src.replace('verifyEmissionReceiptAgainst(closed_template, receipt, bound)',
                  'verifyEmissionReceipt(closed_template, receipt, bound)')
open('lowering.mjs','w').write(src)"

run_case emission-binder-removed "must NAME its relativity and offer a BOUND form" "
src = open('lowering.mjs').read()
src = src.replace('export function makeEmissionVerifier', 'function makeEmissionVerifier')
open('lowering.mjs','w').write(src)"

run_case emission-binder-takes-an-oracle-late "must NAME its relativity and offer a BOUND form" "
src = open('lowering.mjs').read()
src = src.replace('  return Object.freeze((closed_template, receipt) =>\n    verifyEmissionReceiptAgainst(closed_template, receipt, bound));',
                  '  return Object.freeze((closed_template, receipt, oracle) =>\n    verifyEmissionReceiptAgainst(closed_template, receipt, oracle || bound));')
open('lowering.mjs','w').write(src)"

run_case emission-binder-trusts-anything "must NAME its relativity and offer a BOUND form" "
src = open('lowering.mjs').read()
src = src.replace('    throw new Error(\"emission-verifier-no-canonicaliser\");',
                  '    canonicaliseTarget = () => \"anything\";')
open('lowering.mjs','w').write(src)"

run_case oracle-witness-dropped "must carry emission-verdict-names-its-oracle" "
src = open('lowering_check.mjs').read()
src = src.replace('emission-verdict-names-its-oracle', 'emission-oracle-noted')
open('lowering_check.mjs','w').write(src)"

# ── B2.1.1: the verifier may not authenticate a second snapshot ────────────
run_case verifier-resnapshots-the-template "verifiers must OWN what they authenticate" "
src = open('lowering.mjs').read()
src = src.replace('    [\"target_template_sem_id\", targetTemplateSemId(template)],',
                  '    [\"target_template_sem_id\", targetTemplateSemId(ownCanonical(template))],')
open('lowering.mjs','w').write(src)"

run_case verifier-entry-unowned "verifiers must OWN what they authenticate" "
src = open('lowering.mjs').read()
src = src.replace('  return verifyInstantiationReceiptOwned(...owned);',
                  '  return verifyInstantiationReceiptOwned(template, inputs, receipt);')
open('lowering.mjs','w').write(src)"

run_case emission-verifier-resnapshots "verifiers must OWN what they authenticate" "
src = open('lowering.mjs').read()
src = src.replace('  if (receipt.closed_template_sem_id !== closedTemplateSemId(closed_template))',
                  '  if (receipt.closed_template_sem_id !== closedTemplateSemId(ownCanonical(closed_template)))')
open('lowering.mjs','w').write(src)"

run_case owned-verifier-unexported "verifiers must OWN what they authenticate" "
src = open('lowering.mjs').read()
src = src.replace('export function verifyInstantiationReceiptOwned', 'function verifyInstantiationReceiptOwned')
open('lowering.mjs','w').write(src)"

run_case verifier-witness-dropped "must carry verifiers-own-what-they-authenticate" "
src = open('lowering_check.mjs').read()
src = src.replace('verifiers-own-what-they-authenticate', 'verifiers-noted')
open('lowering_check.mjs','w').write(src)"

run_case grid-stops-importing-the-module "lowering.mjs could not be imported" "
src = open('lowering.mjs').read()
src = src.replace('export const LOWERING_VERSION', 'export const LOWERING_VERSION; syntax error here =')
open('lowering.mjs','w').write(src)"

# ── B2.1: the snapshot bug, the bare vocabulary, the emission split ────────
run_case instantiate-reads-inputs-twice "must SNAPSHOT both arguments at entry" "
src = open('lowering.mjs').read()
src = src.replace('inputs_sem_id: inputsSemId(own),', 'inputs_sem_id: inputsSemId(inputs),')
open('lowering.mjs','w').write(src)"

run_case instantiate-template-unsnapshotted "must SNAPSHOT both arguments at entry" "
src = open('lowering.mjs').read()
src = src.replace('const tmpl = ownCanonical(template);', 'const tmpl = template;')
open('lowering.mjs','w').write(src)"

run_case entry-snapshot-rule-unstated "must SNAPSHOT both arguments at entry" "
src = open('lowering.mjs').read()
src = src.replace('  entry_snapshot:', '  entry_note:')
open('lowering.mjs','w').write(src)"

run_case vocabulary-back-to-bare-names "vocabulary's MEANING must be content-bound" "
src = open('lowering.mjs').read()
src = src.replace('  predicate_semantics: Object.freeze', '  predicate_names: Object.freeze')
open('lowering.mjs','w').write(src)"

run_case predicate-kind-hardcoded "vocabulary's MEANING must be content-bound" "
src = open('lowering.mjs').read()
src = src.replace('const spec = LOWERING_SEMANTICS.predicate_semantics[p.holds];',
                  'const spec = {kind: \"number-is-integer\"};')
open('lowering.mjs','w').write(src)"

run_case predicate-becomes-a-function "vocabulary's MEANING must be content-bound" "
src = open('lowering.mjs').read()
src = src.replace('    integer: Object.freeze({ kind: \"number-is-integer\" }),',
                  '    integer: (v) => Number.isInteger(v),')
open('lowering.mjs','w').write(src)"

run_case emission-not-split-out "EMISSION must be its own relation" "
src = open('lowering.mjs').read()
src = src.replace('export const EMISSION_SEM_ID =', 'const EMISSION_SEM_ID =')
open('lowering.mjs','w').write(src)"

run_case closed-template-shares-the-open-domain "EMISSION must be its own relation" "
src = open('lowering.mjs').read()
src = src.replace('export const closedTemplateSemId = (closed) => \"ctmpl-\" +',
                  'export const closedTemplateSemId = (closed) => \"tmpl-\" +')
open('lowering.mjs','w').write(src)"

run_case instantiation-keeps-the-executable-codomain "EMISSION must be its own relation" "
src = open('lowering.mjs').read()
src = src.replace('  codomain_encoding_sem_id: TARGET_TEMPLATE_ENCODING_SEM_ID,\n  codomain_identity_domain',
                  '  codomain_encoding_sem_id: TARGET_EXECUTABLE_ENCODING_SEM_ID,\n  codomain_identity_domain')
open('lowering.mjs','w').write(src)"

run_case verifiers-stay-test-only "receipt VERIFICATION must be a production function" "
src = open('lowering.mjs').read()
src = src.replace('export function verifyInstantiationReceipt', 'function verifyInstantiationReceipt')
open('lowering.mjs','w').write(src)"

run_case emission-verifier-imports-its-own-oracle "receipt VERIFICATION must be a production function" "
src = open('lowering.mjs').read()
src = src.replace('export function verifyEmissionReceiptAgainst(closed_template, receipt, canonicaliseTarget)',
                  'export function verifyEmissionReceiptAgainst(closed_template, receipt)')
open('lowering.mjs','w').write(src)"

run_case b2-ids-erased "B2 identities must be kept" "
src = open('lowering.mjs').read()
src = src.replace('export const SUPERSEDED_B2_SEM_IDS', 'const SUPERSEDED_B2_SEM_IDS')
open('lowering.mjs','w').write(src)"

run_case emission-receipt-missing "must not compute target_term_sem_id" "
src = open('lowering.mjs').read()
src = src.replace('export function emissionReceipt(closed_template_sem_id, target_term_sem_id)',
                  'export function emissionReceipt(closed_template_sem_id)')
open('lowering.mjs','w').write(src)"

run_case snapshot-case-dropped "must carry instantiation-snapshots-its-inputs" "
src = open('lowering_check.mjs').read()
src = src.replace('instantiation-snapshots-its-inputs', 'instantiation-notes-its-inputs')
open('lowering_check.mjs','w').write(src)"

run_case vocabulary-case-dropped "must carry rule-vocabulary-is-content-bound" "
src = open('lowering_check.mjs').read()
src = src.replace('rule-vocabulary-is-content-bound', 'rule-vocabulary-noted')
open('lowering_check.mjs','w').write(src)"

run_case emission-split-case-dropped "must carry emission-is-its-own-relation" "
src = open('lowering_check.mjs').read()
src = src.replace('emission-is-its-own-relation', 'emission-noted')
open('lowering_check.mjs','w').write(src)"

# ── B1.2.1: the version map had three entries no check read ────────────────
run_case version-map-entry-unread "and no check reads it" "
import json
g = json.load(open('invariant-grid.json'))
g['artifact_versions']['grid_v170.py'] = '1.7.0'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# THE ROUND-10 SPECIES, FOUND AGAIN AT B6.3 AND IN THE OTHER HALF OF THE PAIR.
# Round 10 caught version-lockstep-kernel forging by a hard-typed \"1.0.2\" and
# rewrote it to a DERIVED pattern with its own assert (line 293). This case,
# written later, hard-typed \"0.7.2\" — and B6.3's additive bump to 0.8.0 turned
# it into a no-op. The nonvacuity instrument reported it rather than the case
# passing while testing nothing, which is the whole reason that instrument
# exists. Derived now, on the same pattern as its sibling.
run_case lowering-version-drifts "artifact_versions says" "
import re
s = open('lowering.mjs').read()
s2 = re.sub(r'export const LOWERING_VERSION = \"[^\"]+\";',
            'export const LOWERING_VERSION = \"0.9.9\";', s, count=1)
assert s2 != s, 'lowering-version-drifts forged nothing — the LOWERING_VERSION pattern no longer matches'
open('lowering.mjs','w').write(s2)"

# SAME SPECIES, PRE-EMPTIVELY. Not machinery — the third site of a two-site
# species, derived at the cost of one regex, so the NEXT additive bump does not
# have to be the instrument that finds it.
run_case host-version-drifts "artifact_versions says" "
import re
s = open('observed_execution_host.mjs').read()
s2 = re.sub(r'export const HOST_VERSION = \"[^\"]+\";',
            'export const HOST_VERSION = \"0.9.9\";', s, count=1)
assert s2 != s, 'host-version-drifts forged nothing — the HOST_VERSION pattern no longer matches'
open('observed_execution_host.mjs','w').write(s2)"

run_case film-emitter-version-drifts "artifact_versions says" "
src = open('bridge/ic32_film.c').read()
import re
src = re.sub(r'(emitter_version\\\\\":\\\\\")[0-9.]+', r'\\g<1>9.9.9', src)
open('bridge/ic32_film.c','w').write(src)"

# ── B1.2.1: the three stale law statements ─────────────────────────────────
run_case inputs-model-deferred-again "must record the inputs model as DECIDED and print the CURRENT" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.canonical-lowering' and e.get('canonical'):
        e['statement'] = e['statement'].replace('FALSE CHOICE', 'question still open')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case receipt-shape-reverted-in-law "must record the inputs model as DECIDED and print the CURRENT" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.canonical-lowering' and e.get('canonical'):
        e['statement'] = e['statement'].replace(
            'LoweringReceipt {program_sem_id, lowering_sem_id, target_template_sem_id}',
            'LoweringReceipt {program_sem_id, lowering_sem_id, target_term_sem_id}')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case codomain-rule-dropped-from-law "must state the B1.2.1 rule" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.canonical-lowering' and e.get('canonical'):
        e['statement'] = e['statement'].replace(
            'A RELATION\'S IDENTITY MUST COMMIT, BY CONTENT AND NOT BY NAME, TO EXACTLY THE ENCODINGS OF ITS OWN DOMAIN AND CODOMAIN',
            'A relation should describe its encodings')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case superseded-lowering-law-erased "has no canonical PROPERTY-TESTED revision" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if not (e['id'] == 'derivation.canonical-lowering'
                                        and e.get('canonical'))]
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case entry-snapshot-law-deleted "law derivation.entry-snapshot@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'derivation.entry-snapshot']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case entry-snapshot-scoped-to-constructors "must state the rule over AUTHORITY OPERATIONS" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.entry-snapshot':
        e['statement'] = e['statement'].replace(
            'AUTHENTICATES ONE READ OF EXTERNAL STATE AND EXERCISES AUTHORITY USING ANOTHER',
            'validates constructor data twice')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case snapshot-rule-narrowed "must state the general rule and not only the two instances" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.owned-snapshot':
        e['statement'] = e['statement'].replace('CONSULTED TWICE ACROSS A TRUST DECISION',
                                                'read twice by the catalog')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case fail-closed-treated-as-fine "must say why P-6b counts even though it fails closed" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.owned-snapshot':
        e['statement'] = e['statement'].replace('THE MILDER OUTCOME IS NOT A DEFENCE',
                                                'This one is caught downstream')
json.dump(g, open('invariant-grid.json','w'), indent=1)"



# ── B7: `sub`, AND THE WAYS THE REFUSAL COULD DRIFT OFF ITS LAYER ─────────
# Every case below breaks ONE of the things B7 had to get right, and each must
# be caught by the assertion written for it rather than by a neighbour. The
# species guarded against is not a wrong answer: it is a refusal that quietly
# relocates to a layer that cannot hold it, which the arithmetic would go on
# agreeing with for every fixture that happens to be representable.

# 1. SATURATION. The single most dangerous edit in this round: relax the
#    comparison and Church monus answers 0 where the source says -1. Every
#    existing fixture whose operands do not underflow stays green.
run_case sub-saturates-instead-of-refusing "must LOWER, INSTANTIATE, and then be refused at EMISSION" "
src = open('lowering.mjs').read()
Q = chr(34)
old = 'if (a < b) throw new Error(spec.refusal + ' + Q + ': ' + Q + ' + a + ' + Q + ' - ' + Q + ' + b);'
assert old in src, 'sub-saturates: the underflow throw no longer matches'
src = src.replace(old, 'if (a < b) return 0;', 1)
open('lowering.mjs','w').write(src)"

# 2. THE REFUSAL MOVES TO LOWERING. A precondition on the sub rule looks like
#    catching it early and cannot be written correctly — sub(input x, input y)
#    has no underflow fact until an invocation binds the ports.
run_case sub-refusal-moved-to-lowering "op_lowering_rules.sub must carry NO precondition" "
src = open('lowering.mjs').read()
Q = chr(34)
old = '      source_op: ' + Q + 'sub' + Q + ',' + chr(10) + '      preconditions: Object.freeze([]),'
assert old in src, 'sub-refusal-moved-to-lowering: the sub rule no longer matches'
new = ('      source_op: ' + Q + 'sub' + Q + ',' + chr(10)
       + '      preconditions: Object.freeze([Object.freeze({ field: ' + Q + 'a' + Q
       + ', holds: ' + Q + 'nonnegative' + Q + ', refusal: ' + Q + 'lower-negative' + Q + ' })]),')
src = src.replace(old, new, 1)
open('lowering.mjs','w').write(src)"

# 3. THE REFUSAL LEAVES THE CODOMAIN'S VOCABULARY. If the executable encoding
#    stops listing it, an encoding that refuses a whole class of values no
#    longer says so in the record its identity is taken over.
run_case sub-underflow-dropped-from-encoding "must be a refusal of the EMISSION MAP" "
src = open('lowering.mjs').read()
Q = chr(34)
old = ('  refusals: Object.freeze([' + Q + 'emit-unbound-port' + Q + ', ' + Q + 'template-malformed' + Q
       + ', ' + Q + 'emit-sub-underflow' + Q + ']),')
assert old in src, 'sub-underflow-dropped: the map refusal list no longer matches'
new = '  refusals: Object.freeze([' + Q + 'emit-unbound-port' + Q + ', ' + Q + 'template-malformed' + Q + ']),'
src = src.replace(old, new, 1)
open('lowering.mjs','w').write(src)"

# 4. THE CHECK BECOMES CONFIGURABLE. Moving representability after the profile
#    validation makes which templates are emittable depend on a serialization
#    knob — and a broken profile then answers a domain question.
run_case sub-representability-after-profile "must be decided BEFORE the serialization profile is read" "
src = open('lowering.mjs').read()
call = '  representableValue(template);' + chr(10)
assert call in src, 'sub-representability-after-profile: the gate call no longer matches'
src = src.replace(call, '', 1)
anchor = '  const labels = { n: profile.label_counter_start, next() { return this.n++; } };'
assert anchor in src, 'sub-representability-after-profile: the label anchor no longer matches'
src = src.replace(anchor, call + anchor, 1)
open('lowering.mjs','w').write(src)"

# 5. THE ROOT-ONLY CHECK. This is the nested falsifier as a forgery: check the
#    root value alone and (2-3)+2 is accepted, because 1 is representable. The
#    inner monus then answers 2 and NOTHING downstream can see it.
run_case sub-underflow-root-only "must be refused at EMISSION even though its ROOT value is 1" "
src = open('lowering.mjs').read()
Q = chr(34)
old = '  const a = representableValue(node.a, rules), b = representableValue(node.b, rules);'
assert old in src, 'sub-underflow-root-only: the recursive descent no longer matches'
new = '  const a = looseValue(node.a), b = looseValue(node.b);'
src = src.replace(old, new, 1)
helper = ('function looseValue(n) {' + chr(10)
  + '  if (n.t === ' + Q + 'church' + Q + ') return n.n;' + chr(10)
  + '  if (n.t === ' + Q + 'add' + Q + ') return looseValue(n.a) + looseValue(n.b);' + chr(10)
  + '  if (n.t === ' + Q + 'sub' + Q + ') return looseValue(n.a) - looseValue(n.b);' + chr(10)
  + '  throw new Error(' + Q + 'template-malformed' + Q + ');' + chr(10) + '}' + chr(10))
src = src.replace('export function representableValue(node) {', helper + 'export function representableValue(node) {', 1)
open('lowering.mjs','w').write(src)"

# 6. THE FOLD. One line from the representability walk to a constant folder,
#    and every integration theorem still passes while the compiler has stopped
#    compiling. The BYTES are what catches it; the answer never would.
run_case sub-constant-folded "must not be emit" "
src = open('lowering.mjs').read()
Q = chr(34)
old = '    const a = go(n.a), b = go(n.b);' + chr(10) + '    return fill(rule.application, { COMB: combinator(rule, labels, B), a, b });'
assert old in src, 'sub-constant-folded: the combinator emit branch no longer matches'
new = ('    if (n.t === ' + Q + 'sub' + Q + ') return church(representableValue(n), labels, R.church);'
       + chr(10) + old)
src = src.replace(old, new, 1)
open('lowering.mjs','w').write(src)"

# 7. THE OPEN ITEM GETS BOOKED AS CLOSED. emit-sub-underflow is not
#    source-refusal to target-refusal preservation, and recording it as such
#    would claim a theorem about refusals the source never makes.
run_case sub-refusal-claimed-as-preservation "must keep source-refusal to instantiation-refusal DECLARED OPEN" "
src = open('lowering.mjs').read()
old = 'THIS IS NOT REFUSAL PRESERVATION'
assert old in src, 'sub-refusal-claimed-as-preservation: the scope sentence no longer matches'
src = src.replace(old, 'this closes refusal preservation', 1)
open('lowering.mjs','w').write(src)"

# 8. THE FRAGMENT LIST DISAGREES WITH ITSELF. The two grid assertions B7 had to
#    un-pin now check that the SPECIFIED list and the IMPLEMENTED list agree,
#    which is what they were always about; drifting either one apart must fail.
# B8.2: THIS CASE HARD-TYPED THE FRAGMENT AND `mul` TRIPPED IT — the same
# ratchet species B7 derived out of two grid assertions and two lowering_check
# cases, surviving in the battery because nobody looked there. Its subject is
# that the SPECIFIED list and the IMPLEMENTED list must agree, so it drops the
# LAST entry of whichever list is there rather than naming one. The assert is
# what made it fail loudly instead of going vacuous.
run_case fragment-lists-disagree "hashed lowering semantics must include" "
import re
src = open('lowering.mjs').read()
m = re.search(r'lowered_ops: Object\.freeze\(\[(.*?)\]\)', src)
assert m, 'fragment-lists-disagree: lowered_ops no longer matches'
items = m.group(1).split(', ')
assert len(items) > 1, 'fragment-lists-disagree: nothing to drop'
src = src[:m.start()] + 'lowered_ops: Object.freeze([' + ', '.join(items[:-1]) + '])' + src[m.end():]
open('lowering.mjs','w').write(src)"


# ── B8.1: THE DECODER READS THE OBJECT, AND THE WAYS IT COULD STOP ───────
# The defect B8.1 fixed was a DOMAIN defect, not a recognition defect: the old
# decoder read Church numerals correctly out of every signature it was handed,
# and inherited that representation's §5 ceiling at Church 11. Each case below
# puts one piece of that back.

# 1. THE CEILING RETURNS. Cap the walk at the value the signature decoder could
#    reach and everything already shipped stays green — every existing fixture
#    decodes to 5 or less. mul(4,3) is 12.
run_case decoder-ceiling-restored "Church 12 and 20 must decode" "
src = open('lowering.mjs').read()
old = '  decode_walk_bound: 100000,'
assert old in src, 'decoder-ceiling-restored: the walk bound no longer matches'
src = src.replace(old, '  decode_walk_bound: 11,', 1)
open('lowering.mjs','w').write(src)"

# 2. RECOGNITION BY NAME INSTEAD OF BY BINDING IDENTITY. Alpha-invariance stops
#    being a property of the recognition and becomes a hope about whatever
#    canonicalised the term first.
run_case decoder-recognises-by-name "recognition must be by BINDING IDENTITY" "
src = open('lowering.mjs').read()
old = '    if (!body.fun || body.fun.t !== ' + chr(34) + 'Var' + chr(34) + ' || body.fun.nam !== F) return bad;'
assert old in src, 'decoder-recognises-by-name: the head check no longer matches'
new = '    if (!body.fun || body.fun.t !== ' + chr(34) + 'Var' + chr(34) + ' || String(body.fun.nam) !== ' + chr(34) + '1' + chr(34) + ') return bad;'
src = src.replace(old, new, 1)
open('lowering.mjs','w').write(src)"

# 3. THE ORACLE BECOMES OPTIONAL. Then a caller can decode an object whose
#    identity nobody computed — the B2.1.1 verifier defect at the output end.
run_case decoder-oracle-optional "parametric decoder must refuse without an identity oracle" "
src = open('lowering.mjs').read()
old = '''  if (typeof identifyNormalForm !== 'function')
    throw new Error('decode-oracle-required');'''.replace(chr(39), chr(34))
assert old in src, 'decoder-oracle-optional: the oracle guard no longer matches'
src = src.replace(old, '  if (typeof identifyNormalForm !== ' + chr(34) + 'function' + chr(34) + ') identifyNormalForm = () => null;', 1)
open('lowering.mjs','w').write(src)"

# 4. THE RETIRED REFUSAL COMES BACK INTO THE SPEC. A refusal that can never fire
#    is a stale instrument, and one naming a representation the decoder no
#    longer reads is a reader's licence to go looking for it.
run_case decoder-compaction-refusal-restored "decode-signature-compacted must be GONE" "
src = open('lowering.mjs').read()
Q = chr(34)
old = '  refusals: [' + Q + 'decode-not-a-church-numeral' + Q + ', ' + Q + 'decode-numeral-exceeds-bound' + Q + '],'
assert old in src, 'decoder-compaction-refusal-restored: the decoder refusal list no longer matches'
new = ('  refusals: [' + Q + 'decode-not-a-church-numeral' + Q + ', ' + Q + 'decode-numeral-exceeds-bound' + Q
       + ', ' + Q + 'decode-signature-compacted' + Q + '],')
src = src.replace(old, new, 1)
open('lowering.mjs','w').write(src)"

# 5. THE SPEC GOES BACK TO READING A SIGNATURE. The prose half of the same
#    defect: a domain stated as an identity serialization.
run_case decoder-domain-back-to-signature "must read the OWNED normal-form OBJECT" "
src = open('lowering.mjs').read()
old = 'the OWNED target normal-form semantic object'
assert old in src, 'decoder-domain-back-to-signature: the spec domain no longer matches'
src = src.replace(old, 'the SEMSTATE-CANONICAL-v1 signature of the target normal form', 1)
open('lowering.mjs','w').write(src)"

# 6. THE COMPACTION BOUND MOVES. This is the edit GPT ruled OUT: raising 80
#    because the decoder chose the wrong input representation would re-cut
#    SEMSTATE-CANONICAL-v1, the golden pre-hash vectors, the bridge agreement,
#    every semantic state id and every native film. It must be refused even
#    though it would ALSO have made the old decoder read Church 12.
run_case semstate-compaction-bound-raised "80-character compaction must still fire" "
src = open('trvm_law_kernel.mjs').read()
old = 'if (sig.length > 80) sig ='
assert old in src, 'semstate-compaction-bound-raised: the compaction test no longer matches'
src = src.replace(old, 'if (sig.length > 8000) sig =', 1)
open('trvm_law_kernel.mjs','w').write(src)"

# 7. THE SUPERSESSION IS ERASED. The old decoder's id and the measured 11/12
#    boundary are the record of why the widening happened; deleting them leaves
#    DECODE_SEM_ID having moved with nothing saying what moved it.
run_case decoder-supersession-erased "the decoder must read the OWNED normal-form OBJECT" "
src = open('lowering.mjs').read()
old = 'export const SUPERSEDED_SIGNATURE_DECODER_SEM_ID'
assert old in src, 'decoder-supersession-erased: the supersession record no longer matches'
src = src.replace(old, 'const _dropped_SUPERSEDED_SIGNATURE_DECODER', 1)
open('lowering.mjs','w').write(src)"


# ── B8.2: `mul`, AND THE READBACK FOLD DEFECT IT FOUND ───────────────────

# 1. THE FOLD GOES BACK TO INFERRING ORDER FROM THE ID INTEGER. This is the
#    shipped defect, restored: correct under FloatRt, wrong under the class that
#    exists to break exactly that assumption.
run_case foldlive-orders-by-heap-id "RECORDED ALLOCATION ORDER" "
src = open('trvm_law_kernel.mjs').read()
old = '  const order = live.sort((a, b) => frt.heap.get(a).seq - frt.heap.get(b).seq);'
assert old in src, 'foldlive-orders-by-heap-id: the fold order no longer matches'
src = src.replace(old, '  const order = live.sort((a, b) => a - b);', 1)
open('trvm_law_kernel.mjs','w').write(src)"

# 2. THE FOLD USES DISCOVERY ORDER. The intermediate repair: it fixes the
#    descending class and breaks (2+3)*4 under the ascending one, because a
#    traversal order is not a topological order on dup dependency.
run_case foldlive-orders-by-discovery "RECORDED ALLOCATION ORDER" "
src = open('trvm_law_kernel.mjs').read()
old = '  const order = live.sort((a, b) => frt.heap.get(a).seq - frt.heap.get(b).seq);'
assert old in src, 'foldlive-orders-by-discovery: the fold order no longer matches'
src = src.replace(old, '  const order = liveDiscoveryOrder(frt, root);', 1)
open('trvm_law_kernel.mjs','w').write(src)"

# 3. THE ADVERSARIAL CLASS STOPS BEING ADVERSARIAL. If DescFloatRt allocated
#    ascending ids it would agree with FloatRt about everything and prove
#    nothing — an adversary that has stopped adversing is a green check with no
#    content, which is the instrument-vacuity species.
run_case desc-runtime-stops-descending "RECORDED ALLOCATION ORDER|adversarial" "
src = open('trvm_law_kernel.mjs').read()
old = '2_000_000 - 13 * this.ka'
assert old in src, 'desc-runtime-stops-descending: the descending allocation no longer matches'
src = src.replace(old, '9_000_000 + 13 * this.ka', 1)
open('trvm_law_kernel.mjs','w').write(src)"

# 4. THE ALLOCATION STAMP IS DROPPED. Then the fold falls back to the id and the
#    defect returns silently on the next chained-dup term.
run_case allocation-stamp-dropped "monotone allocation stamp" "
src = open('trvm_law_kernel.mjs').read()
old = 'this.heap.set(id, { lab, l, r, val, seq: ++this.aseq });'
assert old in src, 'allocation-stamp-dropped: the stamp no longer matches'
src = src.replace(old, 'this.heap.set(id, { lab, l, r, val });', 1)
open('trvm_law_kernel.mjs','w').write(src)"

# 5. mul LEAVES THE FRAGMENT'S EMISSION RULES while the lowering rule stays, so
#    a program lowers to a template nothing can emit.
# CAUGHT BY THE ASSERTION WRITTEN FOR IT, not by a neighbour: the first want
# string matched the FOLD assertion, which fails because emit() throws inside
# its own probe — a coincidental catch, and the fifth in this line. The op-list
# agreement check is the one whose subject this is.
run_case mul-emission-rule-dropped "every implemented lowered op must have an EMISSION rule" "
src = open('lowering.mjs').read()
i = src.index('    mul: Object.freeze({')
j = src.index('    port: Object.freeze({ kind:', i)
src = src[:i] + src[j:]
open('lowering.mjs','w').write(src)"

# 6. THE DOMAIN ARITHMETIC LOSES ITS CLOSED VOCABULARY. An unknown operator must
#    be a NAMED refusal, never a silently satisfied guard — evalPredicate's rule
#    since B2.1.
run_case emission-operator-vocabulary-open "unknown domain OPERATOR must be a NAMED refusal" "
src = open('lowering.mjs').read()
old = '''  if (!Object.prototype.hasOwnProperty.call(OPS, spec.operator))
    throw new Error('emission-rule-unknown-operator: ' + String(spec.operator));
  return OPS[spec.operator](a, b);'''.replace(chr(39), chr(34))
assert old in src, 'emission-operator-vocabulary-open: the operator guard no longer matches'
src = src.replace(old, '  return (OPS[spec.operator] ?? ((x, y) => x + y))(a, b);', 1)
open('lowering.mjs','w').write(src)"


# ═══ B8.3 — THE PRE-PROOF CLOSURE ══════════════════════════════════════════
# Seven forgeries against the two repairs and the census. Each names the
# assertion whose subject it is, because a forgery caught by a NEIGHBOUR is a
# green report that says nothing about the check it was written for — this line
# has recorded that five times.

# 1. THE `seq ?? id` FALLBACK RETURNS. This is the shipped B8.2 code, and it is
#    the whole reason B8.3 exists: under a missing stamp it quietly resumes
#    inferring allocation order from the id integer. MEASURED — it succeeds
#    SILENTLY under ascending ids and reports `budget` under descending ones, so
#    a broken invariant arrives as a term that is too long.
run_case readback-allocation-fallback-returns "NAMED FAIL-CLOSED condition in readback" "
src = open('trvm_law_kernel.mjs').read()
old = '''  const live = [...liveHeap(frt, root)];
  const seen = new Map();
  for (const id of live) {
    const d = frt.heap.get(id);
    if (!d || !Number.isInteger(d.seq))
      throw new ReadbackInvariantError('readback-allocation-order-missing');
    if (seen.has(d.seq))
      throw new ReadbackInvariantError('readback-allocation-order-duplicate');
    seen.set(d.seq, id);
  }
  const order = live.sort((a, b) => frt.heap.get(a).seq - frt.heap.get(b).seq);'''.replace(chr(39), chr(34))
assert old in src, 'the fail-closed block no longer matches'
new = '''  const order = [...liveHeap(frt, root)].sort((a, b) =>
    (frt.heap.get(a)?.seq ?? a) - (frt.heap.get(b)?.seq ?? b));'''
src = src.replace(old, new, 1)
open('trvm_law_kernel.mjs','w').write(src)"

# 2. A DUPLICATE STAMP IS ACCEPTED. Two dups claiming the same allocation
#    position is not an order at all, and the sort would then pick between them
#    by whatever the engine's sort stability happens to be.
run_case readback-duplicate-stamp-accepted "NAMED FAIL-CLOSED condition in readback" "
src = open('trvm_law_kernel.mjs').read()
old = '''    if (seen.has(d.seq))
      throw new ReadbackInvariantError('readback-allocation-order-duplicate');
'''.replace(chr(39), chr(34))
assert old in src, 'the duplicate guard no longer matches'
src = src.replace(old, '', 1)
open('trvm_law_kernel.mjs','w').write(src)"

# 3. THE FAIL-CLOSED CONDITION IS ABSORBED BY THE BUDGET CATCH. sealSemFilm
#    wraps readback in a try because a readback can legitimately run out of
#    budget; if it swallows this too, a NORMAL_FORM film seals with no
#    normal-form id and nothing anywhere says why.
run_case sealsemfilm-swallows-invariant "NAMED FAIL-CLOSED condition in readback" "
src = open('trvm_law_kernel.mjs').read()
old = '''    try { t.normal_form_id = semId(readback(frt, root).str); }
    catch (e) { if (isReadbackInvariant(e)) throw e; t.normal_form_id = null; }'''
assert old in src, 'the sealSemFilm rethrow no longer matches'
new = '''    try { t.normal_form_id = semId(readback(frt, root).str); }
    catch { t.normal_form_id = null; }'''
src = src.replace(old, new, 1)
open('trvm_law_kernel.mjs','w').write(src)"

# 4. A NEW ORDERING SITE APPEARS AND THE CENSUS DOES NOT NOTICE. The census
#    exists because B8.2's site sat unclassified through eight passes; a
#    denominator that cannot count a new site is the same blindness with a
#    record beside it.
run_case heapid-census-misses-a-new-site "census must stay COMPLETE" "
src = open('trvm_law_kernel.mjs').read()
old = 'function wellFormedFloat(frt, root) {'
assert old in src, 'the anchor function no longer matches'
new = '''function heapIdsAscending(frt) { return [...frt.heap.keys()].sort((a, b) => a - b); }
function wellFormedFloat(frt, root) {'''
src = src.replace(old, new, 1)
open('trvm_law_kernel.mjs','w').write(src)"

# 5. THE CENSUS IS SATISFIED BY A HAND-TYPED DENOMINATOR. Flagging a site that
#    does not sort inflates the declared count to match the source, and the
#    check goes green over a census that has stopped being derived from it.
run_case heapid-census-denominator-typed "census must stay COMPLETE" "
src = open('trvm_law_kernel.mjs').read()
old = 'fn: \"semLocusOf\", sorts: false,'
assert old in src, 'the census entry no longer matches'
src = src.replace(old, 'fn: \"semLocusOf\", sorts: true,', 1)
open('trvm_law_kernel.mjs','w').write(src)"

# 6. THE BOUND DECODER TAKES A JUDGE AGAIN. B2.1.2's repair is the SHAPE: a
#    composition root handing back a function with a parameter for an oracle has
#    bound nothing, and the caller-chosen verdict is available again under a
#    name that reads as though it is not.
run_case target-decoder-takes-a-judge "BOUND AT A COMPOSITION ROOT" "
src = open('lowering.mjs').read()
old = '  return Object.freeze((nf) => decodeOwnedAgainst(nf, bound));'
assert old in src, 'the bound decoder no longer matches'
new = '  return Object.freeze((nf, oracle) => decodeOwnedAgainst(nf, oracle ?? bound));'
src = src.replace(old, new, 1)
open('lowering.mjs','w').write(src)"

# 7. THE OLD SPELLING COMES BACK AS AN ALIAS. B2.1.2 ruled against exactly this
#    for emission: an alias is a second path to the same relation with the
#    weaker spelling still available.
run_case decode-owned-alias-restored "BOUND AT A COMPOSITION ROOT" "
src = open('lowering.mjs').read()
old = 'export function makeTargetDecoder({ identifyNormalForm }) {'
assert old in src, 'the composition root no longer matches'
new = 'export const decodeOwned = decodeOwnedAgainst;\nexport function makeTargetDecoder({ identifyNormalForm }) {'
src = src.replace(old, new, 1)
open('lowering.mjs','w').write(src)"


# ═══ B8.3+ — THE BOUNDED PROOF BUNDLE ══════════════════════════════════════
# Three forgeries against the checker's INDEPENDENCE. The bundle's own thirteen
# forgeries live in proof_forgeries.mjs and mutate the evidence in memory —
# a sharper instrument for a data artifact than a source mutation. These three
# are the ones that are invisible in a passing run, because each of them leaves
# the checker reporting PASS over a bundle it has stopped independently
# checking.

# 1. THE CHECKER IMPORTS THE GENERATOR'S ENUMERATION. Then "the 64 cases cover
#    the domain" is a tautology about one function rather than two
#    implementations of the same set agreeing.
run_case proof-checker-imports-generator-domain "must be INDEPENDENT of the generator" "
src = open('proof_check.mjs').read()
old = 'export function productByIndex(variables, domains) {'
assert old in src, 'the independent product no longer matches'
i2 = src.index('} from ' + chr(34) + './proof_bundle.mjs' + chr(34) + ';')
src = src[:i2] + '  cartesian,\n' + src[i2:]
src = src.replace(old, 'export function productByIndexUnused(variables, domains) {', 1)
src = src.replace('const derived = productByIndex(variables, domains);', 'const derived = cartesian(variables, domains);', 1)
open('proof_check.mjs','w').write(src)"

# 2. THE CHECKER READS THE VERDICT INSTEAD OF COMPUTING ONE. An aggregate that
#    certifies itself is B2's instantiate() defect at the END of the chain.
#    AND THIS CASE WAS ANCHORED ON A LOCAL VARIABLE NAME. It matched
#    `const computed = refusals.length === 0 …`, and P3.1 renamed that variable
#    to `evidence_verdict` while making the public result STRICTLY STRONGER --
#    so the case aborted the whole battery on its own assert, and the grid gate
#    beside it went red, from one rename that fixed a defect. Twelfth
#    text-anchored instance in this line and the second in two rounds caused by
#    an improvement rather than a regression.
#    Anchored on the PROTOCOL FIELD NAME now -- `bounded_claim_verdict` is
#    vocabulary the grammar owns, so it cannot be renamed without a protocol
#    revision, which is exactly the property that makes it safe to match.
run_case proof-checker-reads-the-verdict "must be INDEPENDENT of the generator" "
src = open('proof_check.mjs').read()
import re
m = re.search(r'const (\\w+) = refusals\\.length === 0 \\? .VERIFIED. : .REFUSED.;', src)
assert m, 'the checker no longer derives a verdict from its own refusals'
src = src.replace(m.group(0), 'const ' + m.group(1) + ' = agg.bounded_claim_verdict;', 1)
open('proof_check.mjs','w').write(src)"

# 3. THE BOUNDED SCOPE LEAVES THE ARTIFACT. 64 assignments verified
#    exhaustively is not distributivity over the naturals, and the artifact has
#    to be the thing that says so — a ledger sentence does not travel with it.
run_case proof-scope-drops-the-bound "must be INDEPENDENT of the generator" "
src = open('proof_bundle.mjs').read()
old = 'NOT a proof of distributivity over the naturals'
assert old in src, 'the scope disclaimer no longer matches'
src = src.replace(old, 'a verification of distributivity', 1)
open('proof_bundle.mjs','w').write(src)"


# ═══ P1.1 — THE SCOPE BECOMES STRUCTURAL ═══════════════════════════════════
# P1 shipped the bounded scope as prose and proof_check.mjs read none of it:
# deleting claim.scope, and rewriting it to an unbounded all-naturals claim,
# BOTH verified with zero refusals. Those two live in proof_forgeries.mjs, which
# mutates the evidence. These four mutate the CODE, which is where the property
# can be removed without any bundle looking wrong.

# 1. THE CHECKER STOPS READING THE SCOPE. Back to P1 exactly: a checker that
#    derives a bounded product correctly and never looks at what the artifact
#    says it has proved.
run_case proof-checker-ignores-scope "machine-readable VALUES" "
src = open('proof_check.mjs').read()
old = 'refuse(' + chr(34) + 'proof-scope-mismatch' + chr(34)
assert old in src, 'the scope refusal no longer matches'
src = src.replace(old, 'noop_scope(', 1)
src = src.replace('function checkBundleInner(bundle) {', 'const noop_scope = () => false;\nfunction checkBundleInner(bundle) {', 1)
open('proof_check.mjs','w').write(src)"

# 2. THE SCOPE GOES BACK TO PROSE. A hashed field holding a sentence is a field
#    whose identity moves when somebody rewords the warning -- and a warning
#    that can be reworded into agreement is not a constraint.
run_case proof-scope-returns-to-prose "machine-readable VALUES" "
src = open('proof_bundle.mjs').read()
old = 'kind: ' + chr(34) + 'BOUNDED_EXHAUSTIVE_VERIFICATION' + chr(34) + ','
assert old in src, 'the scope kind no longer matches'
src = src.replace(old, 'kind: ' + chr(34) + 'BOUNDED EXHAUSTIVE VERIFICATION' + chr(34) + ',', 1)
open('proof_bundle.mjs','w').write(src)"

# 3. THE CHECKER IMPORTS THE SCOPE IT IS SUPPOSED TO REQUIRE. Then it compares
#    the bundle's claim to the bundle's own idea of that claim -- the tautology
#    productByIndex exists to avoid, one field over.
run_case proof-checker-imports-its-own-scope "machine-readable VALUES" "
src = open('proof_check.mjs').read()
old = 'export const IMPLEMENTED_SCOPE = Object.freeze({'
assert old in src, 'the declared scope no longer matches'
i = src.index(old); j = src.index('});', i) + 3
src = src[:i] + 'export const IMPLEMENTED_SCOPE = BOUNDED_CLAIM_SCOPE;' + src[j:]
src = src.replace('  caseSetCommitment, aggregateId, boundedClaimSemId, chainIds,', '  caseSetCommitment, aggregateId, boundedClaimSemId, chainIds, BOUNDED_CLAIM_SCOPE,', 1)
open('proof_check.mjs','w').write(src)"

# 4. THE CHECKER CRASHES INSTEAD OF REFUSING. Every byte it reads comes from an
#    untrusted producer; a stack trace is not a verdict. B2.1.2's finding, and
#    the scope-deleted forgery reproduced it here on the first run.
run_case proof-checker-throws-on-hostile-input "machine-readable VALUES" "
src = open('proof_check.mjs').read()
old = '''  try { return checkBundleInner(owned); }'''
assert old in src, 'the outer guard no longer matches'
src = src.replace(old, '''  if (true) { return checkBundleInner(bundle); }
  try { return checkBundleInner(bundle); }''', 1)
src = src.replace('const safe = (f) => { try { return f(); } catch { return THREW; } };', 'const safe = (f) => f();', 1)
open('proof_check.mjs','w').write(src)"


# ═══ P2 — THE BOUNDED DOMAIN CERTIFICATE ═══════════════════════════════════
# The certificate's own fourteen forgeries live in domain_forgeries.mjs and
# mutate the evidence. These three mutate the CODE, and each removes a property
# that leaves every answer correct -- which is why none of them is visible in a
# passing run.

# 1. THE CHECKER ASKS THE COMPILER. Importing representableValue makes the
#    certificate prove that the compiler agrees with itself, and every case
#    still comes out right, so nothing looks wrong.
run_case domain-checker-asks-the-compiler "WITHOUT asking the compiler" "
src = open('domain_check.mjs').read()
old = '  makeEmissionVerifier, verifyInstantiationReceipt,'
assert old in src, 'the lowering import list no longer matches'
src = src.replace(old, '  makeEmissionVerifier, verifyInstantiationReceipt, representableValue,', 1)
open('domain_check.mjs','w').write(src)"

# 2. THE DISPOSITION IS DECIDED FROM THE RESULT. (0-1)+2 is 1, a perfectly
#    representable natural, and would be accepted -- along with four more of the
#    six refusals. B7 measured why that is a miscompilation: Church monus turns
#    the inner underflow into 0 in silence.
run_case domain-disposition-from-the-result "WITHOUT asking the compiler" "
src = open('domain_check.mjs').read()
old = '    disposition: firstUnderflow ? ' + chr(34) + 'REFUSED' + chr(34) + ' : ' + chr(34) + 'EMITTED' + chr(34) + ','
assert old in src, 'the structural disposition no longer matches'
new = '    disposition: (Number.isInteger(value) && value >= 0) ? ' + chr(34) + 'EMITTED' + chr(34) + ' : ' + chr(34) + 'REFUSED' + chr(34) + ','
src = src.replace(old, new, 1)
open('domain_check.mjs','w').write(src)"

# 3. A REFUSAL STOPS ASSERTING ITS ABSENCE. Then a refused case may carry the
#    receipt of the step it says did not happen, and the negative evidence has
#    stopped being evidence.
#
#    THIS CASE HAD NEVER RUN THE CODE. Until P2.1 the mutation was
#    `refuse("domain-refusal-carries-evidence"` → `noop_absence(`, which leaves
#    the argument list's leading comma behind — `noop_absence(,` — and that is a
#    SYNTAX ERROR. The module never loaded, `DC` stayed null, and what reported
#    the catch was the SEPARATE structural-disposition probe going null against
#    a null import. Four rounds green on an inert forgery, and the gate it named
#    was a grep that two surviving occurrences of the same string satisfied
#    anyway. The mutation below parses, loads, and removes exactly the
#    enumeration; the gate is now behavioural.
run_case domain-refusal-absence-unenforced "INCLUDING ITS ABSENCE \(false\)" "
src = open('domain_check.mjs').read()
old = 'for (const f of DOWNSTREAM) if (r[f] !== undefined)'
assert old in src, 'the absence enumeration no longer matches'
src = src.replace(old, 'for (const f of []) if (r[f] !== undefined)', 1)
open('domain_check.mjs','w').write(src)"

# ═══ P2.1 — THE ABSENCE CONTRACT IS THE CHECKER'S ═════════════════════════
# P2 read the absent-set out of `claim.downstream_of_emission`, so the claimant
# defined what its own negative evidence meant. Narrow the list, narrow every
# case's `absent` to match, hang a real film on a refusal, reseal -- ok:true,
# zero refusals. These two are the regression guards for that.

# 4. BOTH BARRIERS REMOVED. The enumeration goes back to reading the bundle AND
#    the contract comparison is disabled. Either one alone still refuses the
#    attack, which is the point of having two; together they reopen it exactly.
run_case domain-absence-contract-unowned "NOT THE CERTIFICATE'S \(false\)" "
src = open('domain_check.mjs').read()
a = 'const DOWNSTREAM = IMPLEMENTED_REFUSAL_CONTRACT.downstream_absent;'
b = 'if (canon(contract) !== MINE)'
assert a in src, 'the checker-owned enumeration no longer matches'
assert b in src, 'the contract comparison no longer matches'
src = src.replace(a, 'const DOWNSTREAM = claim.refusal_contract.downstream_absent;', 1)
src = src.replace(b, 'if (MINE !== MINE)', 1)
open('domain_check.mjs','w').write(src)"

# 5. THE CLAIM IDENTITY STOPS BINDING THE CONTRACT. Then the meaning of the
#    negative evidence can change while the identity of the bounded claim stands
#    still -- which is what P2 shipped, and it is under-binding of the same
#    species P1.1 closed for scope.
run_case domain-claim-id-unbound-from-contract "BINDS THE CLAIM'S IDENTITY \(false\)" "
src = open('domain_bundle.mjs').read()
old = 'protocol: DOMAIN_PROTOCOL, program_sem_id, domain_sem_id, scope, refusal_contract }));'
assert old in src, 'the domain claim identity no longer matches'
src = src.replace(old, 'protocol: DOMAIN_PROTOCOL, program_sem_id, domain_sem_id, scope }));', 1)
open('domain_bundle.mjs','w').write(src)"

# ═══ P3 — COMPOSITION ═════════════════════════════════════════════════════
# The parent's whole claim is that it treats a child as an object with a checker
# rather than as a pile of receipts. Both halves of that are falsifiable.

# 6. THE PARENT TRUSTS THE CITATION. It stops running the child's own checker
#    and takes VERIFIED from the name it cites. Every hash still agrees, so
#    nothing else in the artifact can notice -- a citation would have become a
#    warrant, and there is no registry in this tree entitled to issue one.
run_case compose-citation-treated-as-a-warrant "CITATION IS NOT A WARRANT \(false\)" "
src = open('compose_check.mjs').read()
old = 'const r = safe(() => spec.check(child));'
assert old in src, 'the child dispatch no longer matches'
src = src.replace(old, 'const r = { ok: true, verdict: ' + chr(34) + 'VERIFIED' + chr(34) + ', refusals: [] };', 1)
open('compose_check.mjs','w').write(src)"

# 7. THE PARENT FLATTENS ITS CHILDREN. Importing the kernel makes
#    '0 films replayed by the parent' a measurement that can quietly stop being
#    true, rather than a structural fact about what this file can even do.
#    THE `want` IS ANCHORED ON THE MEASURED VALUE, NOT ON THE SENTENCE. Its
#    first draft matched "NONE of the flattening modules", and a later pass
#    reworded that single word to lower case while making the claim more
#    precise — so the forgery was still caught, grid_check still failed, and the
#    case reported FAIL because its own grep no longer matched. Fail-loud rather
#    than fail-silent, and caught by the review pack rather than by the source
#    tree, but it is B6.1's convention (match the DECLARATION, not the prose)
#    arriving for the tenth time in this line. The array below is the
#    FLATTENING constant's own contents.
run_case compose-parent-can-flatten "flattening modules \[.*\] \(false\)" "
src = open('compose_check.mjs').read()
old = 'import { verifiedClaimSemId, certificateOf } from ' + chr(34) + './certificate.mjs' + chr(34) + ';'
assert old in src, 'the certificate import no longer matches'
src = src.replace(old, old + '\nimport { FloatRt } from ' + chr(34) + './trvm_law_kernel.mjs' + chr(34) + ';', 1)
open('compose_check.mjs','w').write(src)"

# ═══ P3.1 — THE CHECKER OWNS THE GRAMMAR ══════════════════════════════════
# law:proof.semantic-vocabulary-closed@1. Every repair before this one owned the
# VALUES of fields the checker knew about. None owned the FIELD SET, so a
# claimant could add `scope.proves_all_naturals = true`, reseal, and be VERIFIED
# without touching anything the checker read.

# 8. THE VOCABULARY REOPENS. grammar() stops reporting unknown keys, so a
#    semantic record may carry anything at all beside the fields that are
#    checked -- and every value the checker reads is still correct.
run_case grammar-accepts-unknown-keys "VOCABULARY IS CLOSED \\(false\\)" "
src = open('schema.mjs').read()
old = 'if (!known.has(k))'
assert old in src, 'the unknown-key branch no longer matches'
src = src.replace(old, 'if (false)', 1)
open('schema.mjs','w').write(src)"

# 9. THE PUBLIC RESULT GOES INCOHERENT AGAIN: ok:false beside verdict:VERIFIED,
#    which is what all three checkers used to answer for a forged aggregate
#    verdict. Harmless inside one checker; a trap under nesting.
run_case public-result-incoherent "verdict and compares the bundle's to it \(false\)" "
src = open('schema.mjs').read()
old = 'const verdict = list.length === 0 ? ' + chr(34) + 'VERIFIED' + chr(34) + ' : ' + chr(34) + 'REFUSED' + chr(34) + ';'
assert old in src, 'the verdict derivation no longer matches'
src = src.replace(old, 'const verdict = evidence_verdict ?? (list.length === 0 ? ' + chr(34) + 'VERIFIED' + chr(34) + ' : ' + chr(34) + 'REFUSED' + chr(34) + ');', 1)
open('schema.mjs','w').write(src)"

# ═══ P4.1 — FOUR PLANES, AND ONE CANONICAL WIRE ═══════════════════════════
# law:proof.content-address-is-not-a-warrant@1 · law:proof.canonical-wire@1
# law:proof.reference-is-not-claim@1 · law:proof.verifier-policy-owned@1
#
# EVERY `want` BELOW IS A REFUSAL CODE OR A DERIVED BOOLEAN NAME AND A MEASURED
# VALUE, AND NOTHING ELSE — the rule earned three times over in P3.1: a gate may
# match a DERIVATION, a MEASUREMENT, or PROTOCOL VOCABULARY, which cannot be
# renamed without a protocol revision. It may not match a local name or a
# sentence. Cases 6 and 7 above still match prose because the assertions they
# name still print prose beside their booleans.

# 10. THE STORE BECOMES TRUSTED. resolveArtifact stops re-deriving the root from
#     the bytes that came back, so a store may answer any address with any
#     artifact. Every hash INSIDE both artifacts is still correct; the MAPPING
#     is the lie, and this is the only check that could ever see it.
run_case nest-store-trusted "nest-artifact-root-mismatch=false" "
src = open('cas.mjs').read()
old = 'if (derived !== root)'
assert old in src, 'the root re-derivation no longer matches'
src = src.replace(old, 'if (false)', 1)
open('cas.mjs','w').write(src)"

# 11. THE WIRE STOPS BEING CANONICAL. The bytes no longer have to BE the
#     canonical encoding of what they parse to, so a DUPLICATE member name —
#     which JSON.parse resolves in favour of the last one — is authenticated as
#     the honest artifact. That is the P4 defect exactly, and it is a
#     cross-implementation hazard rather than a formatting one.
run_case nest-wire-not-canonical "nest-artifact-non-canonical=false" "
src = open('cas.mjs').read()
old = 'if (!canonical.equals(bytes))'
assert old in src, 'the canonical-wire equality no longer matches'
src = src.replace(old, 'if (false)', 1)
open('cas.mjs','w').write(src)"

# 12. THE STORE STOPS BEING CONFINED. directoryStore builds a path from whatever
#     string arrived, so an untrusted citation steers a filesystem read — P4
#     returned 1.31 MB from outside the store this way.
run_case nest-store-not-confined "store-answers-only-roots=false" "
src = open('cas.mjs').read()
old = '      if (!isRoot(root)) return null;'
assert old in src, 'the store grammar guard no longer matches'
src = src.replace(old, '      if (false) return null;', 1)
open('cas.mjs','w').write(src)"

# 13. THE ADDRESS BECOMES A WARRANT. The child dispatch stops running the
#     child's own checker and takes VERIFIED from the fact that the bytes
#     resolved and re-hashed correctly. Under content addressing the resolution
#     FEELS like verification: something was checked, and it was the wrong thing.
run_case nest-address-treated-as-a-warrant "nest-child-refused=false" "
src = open('nest_check.mjs').read()
old = 'const r = safe(() => spec.check(child));'
assert old in src, 'the child dispatch no longer matches'
src = src.replace(old, 'const r = { ok: true, verdict: ' + chr(34) + 'VERIFIED' + chr(34) + ', refusals: [], measured: {} };', 1)
open('nest_check.mjs','w').write(src)"

# 14. THE POLICY BECOMES THE CALLER'S AGAIN. effectivePolicy stops comparing a
#     requested bound against the shipped one, so max_depth:1000 is obeyed and
#     the 40-deep chain verifies — which is what P4 did.
run_case nest-policy-caller-owned "nest-policy-weakened=false" "
src = open('nest_check.mjs').read()
old = 'if (v > SHIPPED_POLICY[k])'
assert old in src, 'the policy comparison no longer matches'
src = src.replace(old, 'if (false)', 1)
open('nest_check.mjs','w').write(src)"

# 15. THE OPERAND VOCABULARY REOPENS FOR A WARRANT.
run_case nest-operand-admits-a-warrant-field "nest-vocabulary-unknown:warrant=false" "
src = open('nest_check.mjs').read()
old = 'operand: { required: [...CITATION_FIELDS], optional: [] },'
assert old in src, 'the operand grammar no longer matches'
src = src.replace(old, 'operand: { required: [...CITATION_FIELDS], optional: [' + chr(34) + 'already_verified' + chr(34) + ', ' + chr(34) + 'warrant' + chr(34) + '] },', 1)
open('nest_check.mjs','w').write(src)"

# 16. THE OPERAND VOCABULARY REOPENS FOR AN ADDRESS, which is the one that
#     matters for law:proof.reference-is-not-claim@1: the claim id hashes the
#     operand record, so it is blind to artifact_root ONLY because an operand
#     may not carry one. Admit it and a locator is back inside the theorem.
run_case nest-operand-admits-an-address "nest-vocabulary-unknown:artifact_root=false" "
src = open('nest_check.mjs').read()
old = 'operand: { required: [...CITATION_FIELDS], optional: [] },'
assert old in src, 'the operand grammar no longer matches'
src = src.replace(old, 'operand: { required: [...CITATION_FIELDS], optional: [' + chr(34) + 'artifact_root' + chr(34) + '] },', 1)
open('nest_check.mjs','w').write(src)"

# 17. THE PARENT FLATTENS. Importing the kernel makes films_replayed_by_parent
#     = 0 a measurement that can quietly stop being true rather than a fact
#     about what this file can express.
run_case nest-parent-can-flatten "flattening-imports=false" "
src = open('nest_check.mjs').read()
old = 'import { grammar, publicResult, ownSnapshot } from ' + chr(34) + './schema.mjs' + chr(34) + ';'
assert old in src, 'the schema import no longer matches'
src = src.replace(old, old + '\nimport { FloatRt } from ' + chr(34) + './trvm_law_kernel.mjs' + chr(34) + ';', 1)
open('nest_check.mjs','w').write(src)"

# 18. THE CERTIFICATE IDENTITY STOPS REQUIRING A CHAIN — the defect P4 was built
#     on, restored: verifiedClaimSemId hashes H(undefined) for the missing chain
#     instead of refusing, which composes perfectly well and names two artifacts
#     checked under different compilers identically.
run_case nest-certificate-nameable-without-a-chain "certificate-incomplete:chain_ids=false" "
src = open('certificate.mjs').read()
old = 'if (!chain_ids || typeof chain_ids !== ' + chr(34) + 'object' + chr(34) + ')'
assert old in src, 'the chain_ids requirement no longer matches'
src = src.replace(old, 'if (false)', 1)
open('certificate.mjs','w').write(src)"


# 19. THE WIRE STOPS BEING BYTES. The fatal decoder becomes the forgiving one,
#     so an invalid byte is substituted with U+FFFD before the canonical
#     equality can see it — two byte strings, one wire artifact, which is the
#     P4.1 defect one layer below the one P4.1 closed.
run_case nest-wire-decoded-forgivingly "nest-artifact-invalid-utf8=false" "
src = open('cas.mjs').read()
old = 'try { text = UTF8.decode(bytes); }'
assert old in src, 'the fatal decode no longer matches'
src = src.replace(old, 'try { text = bytes.toString(' + chr(34) + 'utf8' + chr(34) + '); }', 1)
open('cas.mjs','w').write(src)"

# 20. THE ROOT ARTIFACT BECOMES EXEMPT FROM ITS OWN POLICY. P4.1 bounded only
#     what came through the CAS, so a 9.4 MB root verified under an 8 MiB
#     ceiling — the one artifact handed in directly was the one not measured.
run_case nest-root-exempt-from-its-own-policy "nest-budget-exceeded=false" "
src = open('nest_check.mjs').read()
old = 'if (ownBytes > policy.max_artifact_bytes)'
assert old in src, 'the root byte bound no longer matches'
src = src.replace(old, 'if (false)', 1)
open('nest_check.mjs','w').write(src)"

# 21. THE VERIFIER STOPS OWNING ITS INPUT. ownSnapshot returns the caller's
#     object, so every checker reads live caller-owned state again and a getter
#     means one thing to the check and another to everyone afterwards.
run_case nest-input-not-owned "input-read-once=false" "
src = open('schema.mjs').read()
old = '  return JSON.parse(canonicalBytes(value));'
assert old in src, 'the ingress snapshot no longer matches'
src = src.replace(old, '  return value;', 1)
open('schema.mjs','w').write(src)"


# 22. THE IMPLEMENTATION REWRITES ITS OWN ANSWER KEY. The artifact-root domain
#     separator changes in the implementation only; the normative spec and the
#     frozen corpus are untouched. That is a catastrophic protocol
#     incompatibility, and before P4.3 the conformance gate reported PASS
#     because it asked the implementation what the answer should be.
run_case nest-oracle-not-frozen "conformance-oracle-frozen=false" "
src = open('cas.mjs').read()
old = 'TRVM-ARTIFACT-ROOT-v2'
assert old in src, 'the artifact-root domain separator no longer matches'
src = src.replace(old, 'TRVM-ARTIFACT-ROOT-v999', 1)
open('cas.mjs','w').write(src)"

# 23. THE CHECKER'S GRAMMAR SHRINKS AWAY FROM THE NORMATIVE ONE. field_audit's
#     denominator is the checker's own grammar, so deleting a field from the
#     checker AND its enforcement AND the producer leaves it reporting 45/45
#     PASS while the protocol still has 46 fields. This is the gate that sees it.
run_case nest-spec-grammar-disagrees "spec-grammar-agrees=false" "
src = open('nest_check.mjs').read()
old = 'chain_ids: { required: [' + chr(34) + 'leaf_chains' + chr(34) + '], optional: [] },'
assert old in src, 'the chain_ids grammar no longer matches'
src = src.replace(old, 'chain_ids: { required: [], optional: [] },', 1)
open('nest_check.mjs','w').write(src)"


# 24. THE NORMATIVE PROSE IS EDITED WITHOUT A RELEASE. The citation-identity
#     formula in the normative Markdown changes; no code, no schema, no vector
#     moves. Before SPEC-RELEASE.json existed, SPEC-AGREEMENT and SPEC-VECTORS
#     were both green -- neither reads the prose, which is the one surface a
#     blind implementer reads and no gate executes.
run_case nest-normative-prose-unbound "spec-release-bound=false" "
import io
p = '../docs/spec/proof-wire/TRVM-VERIFIED-CLAIM-v1.md'
src = io.open(p, encoding='utf-8').read()
old = 'TRVM-VERIFIED-CLAIM-v1|'
assert old in src, 'the normative citation formula no longer matches'
io.open(p,'w',encoding='utf-8').write(src.replace(old, 'TRVM-VERIFIED-CLAIM-EVIL|'))"

echo; [ $FAILED -eq 0 ] && echo "NEGATIVE BATTERY: $CASES/$CASES forgeries caught" || echo "NEGATIVE BATTERY: FAILURES PRESENT ($CAUGHT/$CASES caught)"
exit $FAILED
