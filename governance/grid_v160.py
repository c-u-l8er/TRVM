#!/usr/bin/env python3
# invariant-grid.json v1.5.0 -> v1.6.0 : round-9.1 (the confinement closure).
import json, collections
G = json.load(open("invariant-grid.json"), object_pairs_hook=collections.OrderedDict)
assert G["version"] == "1.5.0"
G["version"] = "1.6.0"
G["law_registry"]["grid_version"] = "1.6.0"
by = {(e["id"], e["revision"]): e for e in G["law_registry"]["entries"]}

def E(id, rev, status, canonical, statement, evidence, **kw):
    x = collections.OrderedDict()
    x["id"] = id; x["revision"] = rev; x["status"] = status; x["canonical"] = canonical
    x["statement"] = statement; x["evidence"] = evidence
    for k, v in kw.items(): x[k] = v
    return x

at = by[("maintenance.atomicity", 1)]
at["evidence"] += (" Round-9B audit FALSIFIED the unconditional reading: a measureFn that "
  "retained the authoritative World wrote it mid-pass and threw — the 'aborted' pass left "
  "vclock 3->4 and a leaked resource, and the receipt sampled the vclock in the catch "
  "handler, reporting vclock_before=4 (the escaped transition normalized into the alleged "
  "pre-state). ATOMIC=false, RECEIPT-TRUTH=false, reproduced and frozen in "
  "probe_forkescape_v05_repro.mjs. The statement is made UNCONDITIONAL by "
  "law:maintenance.capability-confinement@1 (the world lock) plus the entry-clock capture; "
  "L-CONFINE-1 locks the witness.")

G["law_registry"]["entries"].append(
  E("maintenance.capability-confinement", 1, "PROPERTY-TESTED", True,
    "Code executing within a maintenance pass cannot MUTATE the authoritative "
    "World except through capabilities explicitly supplied by the "
    "transaction: for the duration of a pass the root World is LOCKED — "
    "put/del/registerQuery refuse world-write-during-maintenance — the fork "
    "stays writable, and only the pass's commit CAPABILITY (a per-lock key) "
    "may apply staged writes; finally-semantics release the lock on success, "
    "exception, quarantine, and cycle refusal alike. Escaped writes become "
    "aborts, never corruption. Independently: the pass-entry vclock is "
    "captured BEFORE any adversarial code runs, so aborted receipts report "
    "the ACTUAL entry clock. Fork-and-apply is thereby an isolation "
    "boundary, not a convention. Scope: PASSES — register/addGround derive "
    "on the live world by design and their writes are ordinary mediated "
    "transitions; execution in a separate authority domain (worker "
    "isolation) is the declared v-next for portable/ic32 derivations.",
    "Round-9B witness AUDIT-FORK-ESCAPE reproduced against v0.5.0 "
    "(ATOMIC=false; receipt vclock_before reported the already-mutated "
    "clock) and frozen. v0.6.0: L-CONFINE-1 (the witness verbatim: the "
    "escaped write REFUSES, the pass aborts tagged at its node, world "
    "byte-untouched, receipt reports the entry clock, lock released); "
    "L-CONFINE-2 (composite del-escape, armed poisoned-query escape, "
    "refresh-path escape each abort with the world untouched; a "
    "fresh-validation escape is converted to QUARANTINE; the lock survives "
    "cycle refusal; forged commit / double lock / wrong-key unlock each "
    "refuse). All twenty prior batteries re-ran green under the lock."))

G["artifact_versions"]["trvm_world.mjs"] = "0.6.0"
M = G["maintenance"]
M["artifact"] = "trvm_world.mjs v0.6.0 (Maintainer)"
M["confinement"] = collections.OrderedDict([
  ("lock", "world.lock() -> key; put/del/registerQuery refuse "
    "world-write-during-maintenance while held; world.unlock(key) and "
    "world.commit(key, fn) refuse wrong keys (world-lock-capability-refused); "
    "re-entrant lock refuses (world-already-locked); forks are born unlocked"),
  ("entry_truth", "passStartVclock and the before-map are captured before "
    "topo/fork/any user code; refused and aborted receipts carry them"),
  ("error_attribution", "per-node execution tags escaping errors with the "
    "node name; aborted receipts report {at: <node>}"),
  ("scope_note", "register/addGround validate and derive against the LIVE "
    "world by design — not transactional; their writes are ordinary "
    "mediated transitions. Worker-domain isolation is the declared v-next "
    "(the audit's option 2), aligned with portable/ic32 derivations."),
])

G["kernel_evidence"]["round_9_1"] = collections.OrderedDict([
  ("headline", "The confinement closure: the audit falsified fork-and-apply "
    "as stated — a captured-authority write escaped an 'aborted' pass and "
    "the receipt normalized the escaped transition into its alleged "
    "pre-state. Closed by locking the authoritative World for the pass "
    "duration behind a commit capability, capturing the entry clock before "
    "any adversarial code, and tagging abort errors with their node. "
    "Escapes are now aborts (or quarantines, on the fresh-validation "
    "path), never corruption."),
  ("batteries", "L-CONFINE-1 (the frozen witness), L-CONFINE-2 (the "
    "escape matrix + lock lifecycle + capability refusals); twenty prior "
    "batteries re-run green under the lock."),
])

CH = [
  "COMPUTATION INSIDE A TRANSACTION CANNOT ESCAPE ITS AUTHORITY BOUNDARY. "
  "The audit's witness retained the real World in a measureFn, wrote it "
  "mid-pass, and threw: the 'aborted' pass had moved the authoritative "
  "vclock, and the receipt — sampling the clock in the catch handler — "
  "reported the escaped transition's RESULT as its own pre-state. Closed as "
  "law:maintenance.capability-confinement@1: the root World locks for the "
  "pass (writes refuse world-write-during-maintenance), apply goes through "
  "a per-lock commit capability, finally releases on every exit path, and "
  "the entry clock is captured before any adversarial code runs. "
  "Fork-and-apply is an isolation boundary now, not a convention.",
  "THE RHYME EXTENDS ONE MORE LAYER, in the audit's own words: 8.1 — state "
  "cannot change without World identity changing; 8.2 — semantic support "
  "cannot be asserted without derivational evidence; 9.1 — computation "
  "inside a transaction cannot escape the transaction's authority. Each is "
  "the same law wearing the next layer's clothes.",
  "SCOPE STATED, NOT SMUGGLED: register/addGround derive against the live "
  "world by design and are not transactional; worker-domain isolation for "
  "derivations (the audit's stronger option) is declared as the v-next, "
  "aligned with what portable/ic32 derivations need anyway.",
]
NG = collections.OrderedDict()
for k, v in G.items():
    NG[k] = v
    if k == "changelog_from_1_4_0":
        NG["changelog_from_1_5_0"] = CH
assert "changelog_from_1_5_0" in NG
json.dump(NG, open("invariant-grid.json", "w"), indent=1, ensure_ascii=False)
open("invariant-grid.json", "a").write("\n")
print("grid v1.6.0:", len(G["law_registry"]["entries"]), "entries")
