#!/usr/bin/env python3
# invariant-grid.json v1.4.0 -> v1.5.0 : round-9 (the maintenance round).
import json, collections
G = json.load(open("invariant-grid.json"), object_pairs_hook=collections.OrderedDict)
assert G["version"] == "1.4.0"
G["version"] = "1.5.0"
G["law_registry"]["grid_version"] = "1.5.0"

def E(id, rev, status, canonical, statement, evidence, **kw):
    x = collections.OrderedDict()
    x["id"] = id; x["revision"] = rev; x["status"] = status; x["canonical"] = canonical
    x["statement"] = statement; x["evidence"] = evidence
    for k, v in kw.items(): x[k] = v
    return x

G["law_registry"]["entries"].extend([
  E("maintenance.pass", 1, "PROPERTY-TESTED", True,
    "A maintenance pass visits every maintained warrant EXACTLY ONCE in a "
    "deterministic dependency order (Kahn, sorted ready-set): no citer is "
    "classified or refreshed before its citees are current, diamonds "
    "re-derive the shared citee once (not once per path), and a completed "
    "pass leaves every non-quarantined publication FRESH. Classification "
    "drives action: fresh -> replay-validate (no-op); support_intact -> "
    "refresh (escalating to re-derive on value divergence); "
    "support_changed / scope_dirty -> re-derive.",
    "trvm_world.mjs L-MAINT-1 (chain A<-B<-C: order asserted from the "
    "receipt, convergence to all-fresh, values correct, B's new footprint "
    "cites A's NEW publication; the wrong-order counterfactual — C "
    "re-derived before A — carries the wrong value AND is detectably "
    "non-fresh, kept red); L-MAINT-4 (diamond: exactly 4 steps, join after "
    "both arms, identical pass_ids across identical runs)."),
  E("maintenance.quarantine", 1, "PROPERTY-TESTED", True,
    "Forged input is QUARANTINED, never repaired or propagated: external "
    "warrants replay-gate at register(); inside a pass, FRESH nodes are "
    "replay-validated (footprint versions permit replay exactly then) and "
    "a refusal quarantines the node — publication untouched, ids unchanged "
    "in the step record. Refresh/re-derive paths replace state with "
    "derivation truth and the receipt records both ids, so nothing forged "
    "ever ships as-is.",
    "trvm_world.mjs L-MAINT-3: the support-forged warrant refused at the "
    "register() door (support-mismatch) AND quarantined when poisoned "
    "directly into maintainer state — publication version unmoved."),
  E("maintenance.atomicity", 1, "PROPERTY-TESTED", True,
    "The pass runs on a WORLD FORK; the real world is touched only by the "
    "atomic APPLY of the staged publication sequence after every node "
    "succeeded. A mid-pass failure discards the fork: publications, "
    "vclock, and maintainer state are byte-identical to before, and the "
    "receipt records {aborted, at} with completed steps for forensics.",
    "trvm_world.mjs L-MAINT-6: A re-derives on the fork, then B's measure "
    "throws — real world and state untouched. Enabled by the round-9 "
    "refactor: scope queries read through an interface, never a captured "
    "world reference, so World.fork() is total."),
  E("maintenance.receipt", 1, "PROPERTY-TESTED", True,
    "The MaintenanceReceipt PROVES the pass rather than narrating it: the "
    "BEFORE and AFTER publication maps and the ordered steps are committed "
    "(pass_id = H('TRVM-MAINTPASS-v1' | vclocks | before | after | steps)), "
    "and AFTER must be reconstructible from BEFORE + steps by arithmetic — "
    "none/quarantined steps preserve ids and versions, refreshed/rederived "
    "steps advance the publication version and change the warrant_id. A "
    "converged pass is a receipted NO-OP: all-none steps, vclock unmoved, "
    "before == after.",
    "trvm_world.mjs L-MAINT-2 (the no-op pass proven, not asserted); "
    "grid_check v2.9 recomputes the commitment and performs the full "
    "before+steps=after reconstruction engine-free on the shipped "
    "maintenance_receipt.json; the maintenance receipt is deterministic "
    "across identical runs."),
  E("maintenance.acyclicity", 1, "PROPERTY-TESTED", True,
    "The warrant DAG is PROVED acyclic, not assumed: the construction API "
    "cannot express a forward reference (cites must already exist), and "
    "every pass independently re-verifies via Kahn leftover against direct "
    "defs poisoning — a cycle refuses the WHOLE pass, names its members, "
    "and leaves the world untouched.",
    "trvm_world.mjs L-MAINT-5: addComposite citing an unknown name refuses "
    "at the guard; a 2-cycle poisoned directly into defs refuses the pass "
    "with maintenance-cycle naming [X,Y], zero steps, vclock unmoved."),
])

G["artifact_versions"]["trvm_world.mjs"] = "0.5.0"
G["maintenance"] = collections.OrderedDict([
  ("artifact", "trvm_world.mjs v0.5.0 (Maintainer)"),
  ("receipt_domain", "TRVM-MAINTPASS-v1"),
  ("actions", ["none (fresh, replay-validated)", "refreshed (support_intact, "
    "early cutoff)", "rederived (support_changed / scope_dirty / "
    "support_intact-value-diverged)", "quarantined (replay refused on a "
    "fresh node)"]),
  ("receipt_fields", ["refused/aborted flags (+reason/cycle/at)",
    "vclock_before/after", "before/after publication maps "
    "{pub_version, warrant_id}", "steps [{name, verdict, action, "
    "warrant_id_before/after, pub_before/after, trigger?}]", "no_op",
    "pass_id"]),
  ("reconstruction_rule", "after == apply(before, steps): none/quarantined "
    "preserve ids+versions; refreshed/rederived require pub_after > "
    "pub_before AND warrant_id_after != warrant_id_before; no_op iff all "
    "steps none and vclock unmoved and before == after. grid_check v2.9 "
    "verifies all of it engine-free."),
  ("fork_and_apply", "the pass runs on World.fork(); apply replays the "
    "staged publish sequence so real-world versions equal fork versions; "
    "enabled by interface-reading scope queries (no captured world refs)"),
  ("falsifiers_designed_first", "the audit's seven: quarantine-not-repair, "
    "converged-no-op, dependency-order-real, diamond-dedup, cycle-refusal, "
    "failure-atomicity, receipt-completeness — each is a battery or a "
    "grid_check rule, and the wrong-order counterfactual is kept red"),
])

G["kernel_evidence"]["round_9"] = collections.OrderedDict([
  ("headline", "The maintenance round: a supervised engine over the warrant "
    "DAG — deterministic topo passes, quarantine at both doors, "
    "fork-and-apply atomicity, and a MaintenanceReceipt that PROVES the "
    "pass (before + steps reconstruct after, verified engine-free). The "
    "audit's seven falsifiers were designed first; all six batteries "
    "green; the wrong-order counterfactual kept red. One self-catch: a "
    "junk ||-clause of exactly the species the audit found last round was "
    "caught in skeptical re-read before shipping."),
  ("batteries", "L-MAINT-1..6; maintenance_receipt.json (deterministic) "
    "checked by grid_check v2.9."),
])

CH = [
  "MAINTENANCE EXISTS, AND ITS FALSIFIERS CAME FIRST. The audit's seven "
  "obligations were implemented as batteries before the engine was trusted: "
  "dependency order is real (the wrong-order counterfactual carries the "
  "wrong value and is detectably non-fresh — kept red), diamonds re-derive "
  "the shared citee once with identical receipts across identical runs, "
  "converged passes are receipted no-ops, forged input is quarantined at "
  "register() and in-pass (never repaired or republished), cycles refuse "
  "the whole pass by Kahn-leftover proof, and a mid-pass failure discards "
  "the world fork — nothing half-advanced (laws maintenance.pass/"
  "quarantine/atomicity/receipt/acyclicity @1).",
  "THE RECEIPT PROVES THE PASS. before/after publication maps and ordered "
  "steps are committed under TRVM-MAINTPASS-v1, and grid_check v2.9 "
  "reconstructs after from before+steps by arithmetic — the round-5 "
  "danger zone the audit flagged, closed on arrival rather than after.",
  "FORK-AND-APPLY REQUIRED AN HONEST REFACTOR. Scope queries now read "
  "through an interface instead of captured world references, making "
  "World.fork() total — the atomicity law's enabling condition, and a "
  "cleaner query contract besides.",
]
NG = collections.OrderedDict()
for k, v in G.items():
    NG[k] = v
    if k == "changelog_from_1_3_0":
        NG["changelog_from_1_4_0"] = CH
assert "changelog_from_1_4_0" in NG
json.dump(NG, open("invariant-grid.json", "w"), indent=1, ensure_ascii=False)
open("invariant-grid.json", "a").write("\n")
print("grid v1.5.0:", len(G["law_registry"]["entries"]), "entries")
