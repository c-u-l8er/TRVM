#!/usr/bin/env python3
# invariant-grid.json v1.1.0 -> v1.2.0 : round-8 (the composition round).
import json, collections

G = json.load(open("invariant-grid.json"), object_pairs_hook=collections.OrderedDict)
assert G["version"] == "1.1.0", "grid not at v1.1.0?"
G["version"] = "1.2.0"
G["law_registry"]["grid_version"] = "1.2.0"

def E(id, rev, status, canonical, statement, evidence, **kw):
    x = collections.OrderedDict()
    x["id"] = id; x["revision"] = rev; x["status"] = status; x["canonical"] = canonical
    x["statement"] = statement; x["evidence"] = evidence
    for k, v in kw.items(): x[k] = v
    return x

G["law_registry"]["entries"].extend([
  E("warrant.composition", 1, "PROPERTY-TESTED", True,
    "A warrant cites another warrant ONLY through its publication — a world "
    "resource carrying {value, warrant_id, footprint_id} — and every "
    "publication read in a composite footprint is PAIRED with a reified "
    "freshness scope (warrant-fresh:<name>, the citee's footprint "
    "re-evaluated against the current world). Publication reads alone "
    "LAUNDER STALENESS: the citee can go phantom-stale without its "
    "publication moving, and the naive composite stays fresh while "
    "transitively wrong — that witness is constructed and kept red. The "
    "jail is the abstraction boundary: composite replay reads publications "
    "and freshness scopes, never citee internals.",
    "trvm_world.mjs L-COMP-1 (the composition phantom: citee scope_dirty "
    "and provably wrong, naive composite 'fresh', guarded composite "
    "scope_dirty on the same world); L-COMP-2 (chain + diamond: one ground "
    "movement dirties every guarded citer along both paths, with footprint "
    "dedup at the join); L-COMP-3 (honest composite replay ok; a replayer "
    "reaching for citee internals refuses undeclared-read; the pruned "
    "publication refuses undeclared-read)."),
  E("warrant.frame", 1, "PROPERTY-TESTED", True,
    "The frame rule at the world layer (sigma T4's instance): a write's "
    "effect on a warrant's verdict is exactly predicted by footprint "
    "membership and scope influence. Writes outside a warrant's evidence "
    "(neither an exact-read resource nor influencing any scope result) "
    "can NEVER change its verdict; writes inside change it as classified "
    "(support hit -> support_changed; scope influence -> scope_dirty; "
    "non-support exact hit -> support_intact).",
    "trvm_world.mjs L-FRAME-1: 120/120 random writes (23 inside the "
    "evidence, 97 outside) with the predicted verdict matching the actual "
    "freshness classification on every draw."),
])

# artifact + executable-surface updates
G["artifact_versions"]["trvm_world.mjs"] = "0.2.0"
WE = G["warrant"]["executable"]
WE["artifact"] = "trvm_world.mjs v0.2.0"
WE["replay_refusals"] = WE["replay_refusals"] + ["derivation-threw"]
WE["laws"] = WE["laws"] + ["law:warrant.composition@1", "law:warrant.frame@1"]
WE["composition"] = collections.OrderedDict([
  ("publication", "publishWarrant(world, name, w) writes warrant:<name> = "
    "{value, warrant_id, footprint_id} and registers the reified freshness "
    "scope warrant-fresh:<name> (the citee's footprint re-evaluated)"),
  ("pairing_rule", "every warrant:<name> exact read in a composite "
    "footprint MUST be paired with the warrant-fresh:<name> predicate — "
    "grid_check enforces the pairing on the shipped receipt; the naive "
    "unpaired composite exists in the battery as the kept-red laundering "
    "witness"),
  ("replay", "replayComposite jails to the composite's own footprint: "
    "publications and freshness scopes only, never citee internals; a "
    "derivation that throws without a jail violation refuses "
    "derivation-threw"),
])

# sigma profile: the world-layer instantiation
G["sigma_profile"] = collections.OrderedDict([
  ("note", "sigma T1/T2/T4 named as instances in the schemas since round 3; "
    "this section records their WORLD-layer instantiations, executable."),
  ("T1_derivation", "derivation_id = H(canonical inputs) on every warrant; "
    "the DERIVATION schema's kernel instances (CONF-1, L-DERIV-*) carry the "
    "calculus half — law:warrant.freshness@1 carries the world half"),
  ("T2_monotonicity", "the WorldRecord's global vclock and append-only "
    "dense log — law:world.version-monotone@1 (L-WORLD-1)"),
  ("T4_frame", "writes outside a warrant's evidence never change its "
    "verdict — law:warrant.frame@1 (L-FRAME-1, 120/120 predicted); the "
    "separation-logic frame rule as a world property"),
])

G["kernel_evidence"]["round_8"] = collections.OrderedDict([
  ("headline", "The composition round: warrants cite warrants through "
    "publications paired with REIFIED FRESHNESS scopes — the composition "
    "phantom (staleness laundered through a publication that never moved) "
    "constructed and kept red; propagation proved through chains and "
    "diamonds with footprint dedup; the jail doubles as the abstraction "
    "boundary (citee internals refuse). Plus sigma T4 executable: the "
    "frame rule as a 120/120 verdict-prediction property over random "
    "writes. trvm_world.mjs v0.2.0; kernel untouched."),
  ("batteries", "L-COMP-1..3, L-FRAME-1; receipt v2 carries a ground and a "
    "composite warrant, both id-recomputed engine-free."),
])

CH = [
  "COMPOSITION WITHOUT LAUNDERING. A warrant cites a warrant only through "
  "its PUBLICATION, and the battery constructs what publication-only "
  "citation costs: the citee goes phantom-stale, its publication never "
  "moves, and the naive composite is 'fresh' while transitively wrong — "
  "the phantom, one level up, kept red. The repair reifies freshness "
  "itself as a scope (warrant-fresh:<name> = the citee's footprint "
  "re-evaluated), so one ground movement dirties every guarded citer "
  "through chains and diamonds without any publication write "
  "(law:warrant.composition@1).",
  "THE JAIL IS THE ABSTRACTION BOUNDARY. Composite replay reads "
  "publications and freshness scopes — never citee internals; a replayer "
  "reaching inside refuses undeclared-read, and a derivation that throws "
  "without a jail violation refuses derivation-threw (ninth refusal). "
  "Composites provably use only published values.",
  "SIGMA T4, EXECUTABLE. The frame rule as a property test: footprint "
  "membership + scope influence PREDICT the freshness verdict on 120/120 "
  "random writes — writes outside a warrant's evidence cannot change its "
  "verdict (law:warrant.frame@1). The sigma_profile section records the "
  "T1/T2/T4 world-layer instantiations.",
]
NG = collections.OrderedDict()
for k, v in G.items():
    NG[k] = v
    if k == "changelog_from_1_0_1":
        NG["changelog_from_1_1_0"] = CH
assert "changelog_from_1_1_0" in NG
json.dump(NG, open("invariant-grid.json", "w"), indent=1, ensure_ascii=False)
open("invariant-grid.json", "a").write("\n")
print("grid v1.2.0:", len(G["law_registry"]["entries"]), "entries")
