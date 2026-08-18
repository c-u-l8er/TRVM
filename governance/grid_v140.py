#!/usr/bin/env python3
# invariant-grid.json v1.3.0 -> v1.4.0 : round-8.2 (support-soundness closure).
import json, collections
G = json.load(open("invariant-grid.json"), object_pairs_hook=collections.OrderedDict)
assert G["version"] == "1.3.0"
G["version"] = "1.4.0"
G["law_registry"]["grid_version"] = "1.4.0"

def E(id, rev, status, canonical, statement, evidence, **kw):
    x = collections.OrderedDict()
    x["id"] = id; x["revision"] = rev; x["status"] = status; x["canonical"] = canonical
    x["statement"] = statement; x["evidence"] = evidence
    for k, v in kw.items(): x[k] = v
    return x

G["law_registry"]["entries"].append(
  E("warrant.support-soundness", 1, "PROPERTY-TESTED", True,
    "Support is DERIVED, not declared into authority: replay(D, W) = ok "
    "implies support(D) == support(W) exactly — the subset rule "
    "(support ⊆ exact footprint) is necessary but NOT sufficient, and both "
    "replayers enforce both properties (support-mismatch, the tenth "
    "refusal). Support is CANONICAL at seal (sorted, deduplicated; "
    "reordering is a no-op by construction). refreshWarrant RESTORES "
    "derivation-produced support — a forged support cannot survive the "
    "early-cutoff path. Division of verification for the shipped receipt: "
    "grid_check holds the engine-free half (subset, canonical form, "
    "commitments); `trvm_world.mjs --check-receipt` rebuilds the world from "
    "the receipt's COMMITTED world_spec and replays both warrants — the "
    "engine half a tampered-but-resealed support cannot survive.",
    "Round-8C audit witness AUDIT-SUPPORT-LAUNDER, reproduced executably "
    "against v0.3.0: forged-empty support replayed ok, classified "
    "support_intact where the honest warrant said support_changed on the "
    "same world change, refresh PRESERVED the forgery, and the support-"
    "pruned receipt (honestly resealed) passed grid_check — a three-way "
    "assurance-composition hole. v0.4.0: L-SUPPORT-1 locks the exact chain "
    "(replay now refuses; the freshness classification limit is STATED — "
    "freshness cannot see forgery without the engine; refresh restores "
    "[\"r:x\"] and the next movement classifies support_changed) plus six "
    "forgeries incl. composite prune/inflation; the engine mode refuses "
    "the receipt attack with support-mismatch."))

G["artifact_versions"]["trvm_world.mjs"] = "0.4.0"
WE = G["warrant"]["executable"]
WE["artifact"] = "trvm_world.mjs v0.4.0"
WE["replay_refusals"] = WE["replay_refusals"] + ["support-mismatch"]
WE["laws"] = WE["laws"] + ["law:warrant.support-soundness@1"]
WE["support_discipline"] = collections.OrderedDict([
  ("two_properties", "support ⊆ exact reads (structural, pre-derivation) AND "
    "support == canonical derivation-produced support (semantic, "
    "post-derivation) — both enforced in replayWarrant AND replayComposite"),
  ("canonical_form", "sorted, deduplicated at seal; order is non-semantic by "
    "construction"),
  ("refresh", "refreshWarrant re-derives and RESTORES support; the audit's "
    "laundering chain breaks at the gate the maintenance loop will use"),
  ("receipt_engine_half", "world_spec is COMMITTED in the receipt "
    "(TRVM-WORLDRECEIPT-v3); --check-receipt rebuilds and replays"),
  ("future_work", "mechanically derivable support (derivation trace -> "
    "dependency extraction, the Adapton demanded-edge idea) rather than "
    "author-declared-then-verified — noted per the audit's architectural "
    "observation; equality-to-replay is the v3 contract"),
])

G["kernel_evidence"]["round_8_2"] = collections.OrderedDict([
  ("headline", "The support-soundness closure: support was committed but "
    "never re-derived — the audit forged it empty, replayed ok, split the "
    "invalidation classification, and laundered the forgery through "
    "refresh; the receipt version passed grid_check. Closed with dual-"
    "property replay in both replayers, canonical support, truth-restoring "
    "refresh, and the receipt's engine half (--check-receipt). All "
    "batteries re-run green; refusals now 10."),
  ("audit_verification", [
    "AUDIT-SUPPORT-LAUNDER reproduced exactly against v0.3.0: forged [] "
    "support replayed ok; honest support_changed vs forged support_intact "
    "on the same world change; refresh succeeded and preserved []; the "
    "pruned-support receipt with honest reseals passed grid_check.",
    "Also confirmed: replayComposite had NEITHER support check — it gains "
    "both, one discipline across warrant kinds.",
    "L-COMP-3's pruned-publication forgery now dies EARLIER "
    "(support-not-subset, structural); the battery was sharpened to also "
    "run the fully consistent forgery (publication pruned from footprint "
    "AND support), which still dies at the jail with undeclared-read."]),
  ("batteries", "L-SUPPORT-1 (the locked chain + six forgeries + "
    "reorder-noop); all thirteen prior world batteries re-run green; "
    "RECEIPT-CHECK engine mode."),
])

CH = [
  "SUPPORT IS DERIVED, NOT DECLARED INTO AUTHORITY. The audit forged a "
  "warrant's support to [] with an honest reseal: replay accepted it, the "
  "next support movement classified support_intact instead of "
  "support_changed, refreshWarrant preserved the forgery, and the receipt "
  "version passed grid_check — authority outran evidence again, one layer "
  "up. Closed as law:warrant.support-soundness@1: canonical support at "
  "seal, dual-property enforcement (subset AND exact equality with the "
  "derivation's own output) in BOTH replayers, truth-restoring refresh, "
  "and the receipt's committed world_spec + --check-receipt engine half. "
  "The locked regression is the audit's exact chain.",
  "THE CLASSIFICATION LIMIT IS STATED, NOT HIDDEN. freshness() cannot see "
  "a support forgery without running the engine — the record says so; the "
  "gates that matter (replay, refresh, receipt check) all re-derive.",
  "ONE DISCIPLINE ACROSS WARRANT KINDS. replayComposite had neither "
  "support check; it now runs both, and the pruned-publication forgery "
  "dies twice over (structurally, then — when made fully consistent — at "
  "the jail).",
]
NG = collections.OrderedDict()
for k, v in G.items():
    NG[k] = v
    if k == "changelog_from_1_2_0":
        NG["changelog_from_1_3_0"] = CH
assert "changelog_from_1_3_0" in NG
json.dump(NG, open("invariant-grid.json", "w"), indent=1, ensure_ascii=False)
open("invariant-grid.json", "a").write("\n")
print("grid v1.4.0:", len(G["law_registry"]["entries"]), "entries")
