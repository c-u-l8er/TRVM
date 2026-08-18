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
# law:evidence.instrument-nonvacuity@1 — the mechanised half.
# A per-file digest, not a whole-tree one: "something changed" is weaker than
# "the intended target changed", and the law says target. changed_files() names
# what the perturbation actually moved, so a case that edits the wrong artifact
# is as visible as one that edits nothing.
file_digests () { ( cd "$1" && for f in *; do [ -f "$f" ] && printf "%s %s\n" "$(sha256sum "$f" | cut -d" " -f1)" "$f"; done | sort ); }
# Symmetric difference, not one-sided: a case that DELETES an artifact removes a
# line from the "after" set, which a one-sided comm cannot see. The first draft
# used comm -13 and duly reported refine-receipt-missing — a case that deletes
# refinement_receipt.json — as VACUOUS. The non-vacuity detector's own first
# defect was a vacuity blind spot, found by running it. Recorded rather than
# quietly fixed, because that is the law's whole point.
changed_files () { { printf "%s\n" "$1"; printf "%s\n" "$2"; } | sort | uniq -u | awk "{print \$2}" | sort -u | tr "\n" "," | sed "s/,$//"; }

run_case () {  # name, expected-grep, setup-script(python)
  local name="$1" want="$2" py="$3"
  local d=$SCRATCH/$name
  rm -rf "$d" && mkdir -p "$d"
  cp $BASE/invariant-grid.json $BASE/trvm_law_kernel.mjs $BASE/grid_check.mjs \
     $BASE/kappa_witnesses.mjs $BASE/scheduler_certificate.json $BASE/refinement_receipt.json $BASE/golden_prehash_vectors.json \
     $BASE/trvm_world.mjs $BASE/world_warrant_receipt.json $BASE/maintenance_receipt.json \
     $BASE/round-3-ledger.md $BASE/round-4-ledger.md $BASE/round-5-ledger.md $BASE/round-6-ledger.md $BASE/round-7-ledger.md $BASE/round-8-ledger.md $BASE/round-9-ledger.md "$d/"
  # law:evidence.instrument-nonvacuity@1 — a forgery that forges NOTHING is
  # vacuous, and a vacuous falsifier is worse than an absent one because the
  # roster still counts it. Six apparatus failures across four rounds would each
  # have been caught here; the hard-coded "1.0.2" replacement is the exact shape.
  local pre; pre=$(file_digests "$d")
  ( cd "$d" && python3 -c "$py" )
  local post; post=$(file_digests "$d")
  CASES=$((CASES+1))
  local touched; touched=$(changed_files "$pre" "$post")
  if [ -z "$touched" ]; then
    echo "FAIL  $name (VACUOUS — the forgery changed no artifact; nothing was tested)"; FAILED=1; return
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
  cp $BASE/invariant-grid.json $BASE/trvm_law_kernel.mjs $BASE/grid_check.mjs      $BASE/kappa_witnesses.mjs $BASE/scheduler_certificate.json $BASE/refinement_receipt.json $BASE/golden_prehash_vectors.json      $BASE/trvm_world.mjs $BASE/world_warrant_receipt.json      $BASE/round-3-ledger.md $BASE/round-4-ledger.md $BASE/round-5-ledger.md $BASE/round-6-ledger.md $BASE/round-7-ledger.md $BASE/round-8-ledger.md $BASE/round-9-ledger.md "$d/"
  local pre; pre=$(file_digests "$d")
  ( cd "$d" && python3 -c "$py" )
  local post; post=$(file_digests "$d")
  local touched; touched=$(changed_files "$pre" "$post")
  CASES=$((CASES+1))
  if [ -z "$touched" ]; then
    echo "FAIL  $name (VACUOUS — the forgery changed no artifact; nothing was tested)"; FAILED=1; return
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

echo; [ $FAILED -eq 0 ] && echo "NEGATIVE BATTERY: $CASES/$CASES forgeries caught" || echo "NEGATIVE BATTERY: FAILURES PRESENT ($CAUGHT/$CASES caught)"
exit $FAILED
