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
mkdir -p "$SCRATCH" && cp "$BASE/../Makefile" "$SCRATCH/Makefile" 2>/dev/null || true
BASELINE_DIGEST=""
establish_baseline () {
  local d=$SCRATCH/__baseline
  rm -rf "$d" && mkdir -p "$d"
  for f in $CASE_INPUTS; do mkdir -p "$d/$(dirname "$f")" && cp "$BASE/$f" "$d/$f"; done
  local out; out=$(cd "$d" && node grid_check.mjs 2>&1); local code=$?
  if [ $code -ne 0 ]; then
    echo "FAIL  BASELINE (the unperturbed fixture does not pass; no case below is isolated-cause evidence)"
    echo "$out" | grep -E "^ -" | head -6 | sed "s/^/        /"
    FAILED=1; return 1
  fi
  BASELINE_DIGEST=$(file_digests "$d")
  echo "BASELINE  grid_check exits 0 on the unperturbed fixture ($(echo "$BASELINE_DIGEST" | wc -l) artifacts)"
}

run_case () {  # name, expected-grep, setup-script(python)
  local name="$1" want="$2" py="$3"
  local d=$SCRATCH/$name
  rm -rf "$d" && mkdir -p "$d"
  for f in $CASE_INPUTS; do mkdir -p "$d/$(dirname "$f")" && cp "$BASE/$f" "$d/$f"; done
  # law:evidence.instrument-nonvacuity@1 — a forgery that forges NOTHING is
  # vacuous, and a vacuous falsifier is worse than an absent one because the
  # roster still counts it. Six apparatus failures across four rounds would each
  # have been caught here; the hard-coded "1.0.2" replacement is the exact shape.
  local pre; pre=$(file_digests "$d")
  # PHASE 1 of law:evidence.clean-baseline@1 — this case's fixture must BE the
  # one that was baselined, not merely one built by the same recipe
  CASES=$((CASES+1))
  if [ -n "$BASELINE_DIGEST" ] && [ "$pre" != "$BASELINE_DIGEST" ]; then
    echo "FAIL  $name (FIXTURE DRIFT — this case's tree differs from the baselined one)"; FAILED=1; return
  fi
  ( cd "$d" && python3 -c "$py" )
  local post; post=$(file_digests "$d")
  local touched; touched=$(changed_files "$pre" "$post")
  if [ -z "$touched" ]; then
    echo "FAIL  $name (VACUOUS — the forgery changed no artifact; nothing was tested)"; FAILED=1; return
  fi
  local intended; intended=$(intended_targets "$py")
  if [ -n "$intended" ] && [ "$intended" != "$touched" ]; then
    echo "FAIL  $name (TARGET MISMATCH — script intends [$intended], run changed [$touched])"; FAILED=1; return
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
    if e['id']=='sched.certificate' and e['revision']==1: e['canonical']=True
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
  local d="$SCRATCH/$name"
  rm -rf "$d" && mkdir -p "$d" || { echo "FAIL  $name (scratch unusable: $d)"; CASES=$((CASES+1)); FAILED=1; return; }
  for f in $CASE_INPUTS; do mkdir -p "$d/$(dirname "$f")" && cp "$BASE/$f" "$d/$f"; done
  local pre; pre=$(file_digests "$d")
  # PHASE 1 of law:evidence.clean-baseline@1 — this case's fixture must BE the
  # one that was baselined, not merely one built by the same recipe
  CASES=$((CASES+1))
  if [ -n "$BASELINE_DIGEST" ] && [ "$pre" != "$BASELINE_DIGEST" ]; then
    echo "FAIL  $name (FIXTURE DRIFT — this case's tree differs from the baselined one)"; FAILED=1; return
  fi
  ( cd "$d" && python3 -c "$py" )
  local post; post=$(file_digests "$d")
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
src = src.replace('this.#issued.set(request_id, requestSemId(req));',
                  'this.#issued.set(request_id, body.grant_id);')
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
src = src.replace('export function deriveLocally(registry, req) {',
                  'export function deriveLocally(registry, req, caller_id) {')
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
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.implementation-provenance' and e['revision'] == 2:
        e['statement'] = 'provenance is established by the executor handle.'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case false-claim-history-scrubbed "must stay on the record AS a false claim" "
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
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if not (e['id'] == 'derivation.implementation-provenance' and e['revision'] == 3)]
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case attestation-overclaimed "must state conservatively what hash-then-spawn" "
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
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.implementation-provenance' and e['revision'] == 2:
        e['canonical'] = True
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── round 23: the execution plane originates evidence ───────────────────────
run_case film-law-deleted "law film.native-emission@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'film.native-emission']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-scope-inflated "no longer states its scope as CHECKED refusals" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'film.native-emission':
        e['statement'] = e['statement'].replace('DUP-FREE fragment', 'whole corpus').replace(
            'REFUSED BY NAME', 'handled')
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

run_case film-quiescence-asserted "must CHECK quiescence and readback purity" "
src = open('bridge/ic32_film.c').read()
src = src.replace('film-readback-was-not-pure', 'film-readback-assumed-pure')
open('bridge/ic32_film.c','w').write(src)"

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
                                if not (e['id'] == 'derivation.implementation-provenance' and e['revision'] == 4)]
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case launch-descriptor-rule-dropped "no longer carries the launch-descriptor rule" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.implementation-provenance' and e['revision'] == 4:
        e['statement'] = e['statement'].replace(
            'a launch descriptor may not carry both the evidence and an independent executable action',
            'the authority hashes what it launches')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case v3-history-made-current "implementation-provenance@3 must stay on the record as history" "
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
src = src.replace('constructor(reader, programImage = [], host = null) {',
                  'constructor(reader, programImage, host = null) {')
open('derive_protocol.mjs','w').write(src)"

run_case oracle-comes-from-outside "must re-derive through the authority" "
src = open('derive_protocol.mjs').read()
src = src.replace('validateForeignResult(this.#registry, req, res)',
                  'validateForeignResult(arguments[2] ?? this.#registry, req, res)')
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

run_case lowering-law-downgraded "law derivation.canonical-lowering@1 missing" "
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

run_case inputs-model-decided-by-accident "must keep the inputs model DEFERRED AND NAMED" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.canonical-lowering':
        e['statement'] = e['statement'].replace('PARAMETERIZED', 'the obvious model')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case inputs-silently-lowered "must record the inputs model as UNDECIDED" "
src = open('lowering.mjs').read()
src = src.replace('decided: false', 'decided: true')
open('lowering.mjs','w').write(src)"

run_case execution-grades-collapsed "must separate OBSERVED execution from FILM-EVIDENCED" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.lowering-refinement':
        e['statement'] = e['statement'].replace('TWO GRADES OF EVIDENCE FOR THE EXECUTION LEG',
                                                'the execution is evidenced')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-gap-unlocated "must name WHERE the film gap is" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.lowering-refinement':
        e['statement'] = e['statement'].replace('film-dup-cell-present', 'a refusal').replace(
            'dup-free one-step', 'a narrower')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-gap-not-measured "must ASSERT the film refusal at the fixture" "
src = open('lowering_check.mjs').read()
src = src.replace('native-film-absent-by-refusal', 'native-film-noted')
open('lowering_check.mjs','w').write(src)"

run_case identities-may-collapse "must assert the six identities differ" "
src = open('lowering_check.mjs').read()
src = src.replace('six-identities-stay-distinct', 'six-identities-listed')
open('lowering_check.mjs','w').write(src)"


echo; [ $FAILED -eq 0 ] && echo "NEGATIVE BATTERY: $CASES/$CASES forgeries caught" || echo "NEGATIVE BATTERY: FAILURES PRESENT ($CAUGHT/$CASES caught)"
exit $FAILED
