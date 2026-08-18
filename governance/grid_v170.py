#!/usr/bin/env python3
# invariant-grid.json v1.6.0 -> v1.7.0 : round-9.2 (the key-confinement closure).
import json, collections
G = json.load(open("invariant-grid.json"), object_pairs_hook=collections.OrderedDict)
assert G["version"] == "1.6.0"
G["version"] = "1.7.0"
G["law_registry"]["grid_version"] = "1.7.0"
by = {(e["id"], e["revision"]): e for e in G["law_registry"]["entries"]}

cc = by[("maintenance.capability-confinement", 1)]
cc["evidence"] += (" Round-9C audit follow-up FALSIFIED the implementation again, exactly where "
  "the audit predicted: the lock key was a PUBLIC property (world._lockKey), so a retained "
  "closure stole it and committed THROUGH the lock — the witness leaked mid-pass without "
  "even aborting (vclock 3->5) — and, key or no key, res/log/queries/vclock were public "
  "fields open to raw mutation bypassing every guard (world.res.set landed a ghost resource "
  "silently). Both reproduced and frozen in probe_keytheft_v06_repro.mjs. v0.7.0 closes "
  "structurally: all state in true private fields (#res/#vclock/#log/#queries/#lockKey), "
  "crypto-random key (randomBytes), read surface via copying getters, World.prototype and "
  "every instance FROZEN (patching throws). L-CONFINE-3 locks the theft witness and the "
  "sealed-internals matrix. Stated residual unchanged: same-realm JS is option 1's outer "
  "limit; worker-domain isolation remains the declared v-next.")

G["artifact_versions"]["trvm_world.mjs"] = "0.7.0"
M = G["maintenance"]
M["artifact"] = "trvm_world.mjs v0.7.0 (Maintainer)"
M["confinement"]["key_confinement"] = ("the lock key is crypto-random (randomBytes) and "
  "lives in a true private field (#lockKey) — no public property or method returns it "
  "except lock() to the locker; ALL World state is private (#res/#vclock/#log/#queries); "
  "vclock is a getter, log returns dead copies, resourceEntries() returns metadata copies; "
  "World.prototype and every instance are frozen, so method patching and instance "
  "shadowing throw. A retained World reference carries no authority the transaction did "
  "not hand it.")

G["kernel_evidence"]["round_9_2"] = collections.OrderedDict([
  ("headline", "The key-confinement closure: the audit's predicted follow-up was real — "
    "the master key hung on the object as a public property (stolen key committed THROUGH "
    "the lock, no abort) and the internals were public fields (raw res mutation, no key "
    "needed). Closed structurally: private fields, crypto-random key, copying getters, "
    "frozen prototype and instances. All twenty-two prior batteries re-run green on the "
    "sealed World."),
  ("batteries", "L-CONFINE-3 (theft witness dead + sealed-internals matrix + freeze "
    "assertions); probe_keytheft_v06_repro.mjs frozen pre-fix."),
])

CH = [
  "THE MASTER KEY WAS HANGING ON THE OBJECT — the audit named the risk before finding it, "
  "and it was real twice over: world._lockKey was public (a retained closure stole it and "
  "committed THROUGH the lock, leaking mid-pass with no abort), and the internals "
  "(res/log/queries/vclock) were public fields open to guard-free raw mutation. Closed at "
  "the structure, not the convention: true private fields for all state, a crypto-random "
  "key, copying read surfaces, and frozen prototype + instances — a retained reference now "
  "carries no authority the transaction did not hand it "
  "(law:maintenance.capability-confinement@1, evidence amended with the arc).",
  "OPTION 1'S OUTER LIMIT IS NOW ACTUALLY REACHED, and the record says where it sits: "
  "same-realm JavaScript with sealed objects. What remains beyond it — realm/worker "
  "isolation for derivations — stays the declared v-next, aligned with portable/ic32 "
  "execution.",
]
NG = collections.OrderedDict()
for k, v in G.items():
    NG[k] = v
    if k == "changelog_from_1_5_0":
        NG["changelog_from_1_6_0"] = CH
assert "changelog_from_1_6_0" in NG
json.dump(NG, open("invariant-grid.json", "w"), indent=1, ensure_ascii=False)
open("invariant-grid.json", "a").write("\n")
print("grid v1.7.0:", len(G["law_registry"]["entries"]), "entries")
