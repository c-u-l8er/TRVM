#!/usr/bin/env python3
# invariant-grid.json v1.2.0 -> v1.3.0 : round-8.1 (the write-mediation closure).
import json, collections

G = json.load(open("invariant-grid.json"), object_pairs_hook=collections.OrderedDict)
assert G["version"] == "1.2.0", "grid not at v1.2.0?"
G["version"] = "1.3.0"
G["law_registry"]["grid_version"] = "1.3.0"
by = {(e["id"], e["revision"]): e for e in G["law_registry"]["entries"]}

def E(id, rev, status, canonical, statement, evidence, **kw):
    x = collections.OrderedDict()
    x["id"] = id; x["revision"] = rev; x["status"] = status; x["canonical"] = canonical
    x["statement"] = statement; x["evidence"] = evidence
    for k, v in kw.items(): x[k] = v
    return x

vm = by[("world.version-monotone", 1)]
vm["evidence"] += (" Round 8.1: the audit found the battery's first version contained an "
  "assertion incapable of failing (`... || true`) — removed, and the battery strengthened "
  "to latest-read on all six live resources, the full deletion lifecycle with tombstones, "
  "and the per-history version=>hash map.")

G["law_registry"]["entries"].extend([
  E("world.write-mediated", 1, "PROPERTY-TESTED", True,
    "World state is WRITE-MEDIATED: a resource's observable value cannot "
    "change except through a version-advancing World transition — same "
    "version IMPLIES same canonical value; every observable world mutation "
    "induces an observable world identity transition. Mechanism: a "
    "canonical resource-value domain (null, boolean, finite number, "
    "string, arrays, plain objects with sorted keys; everything else "
    "refuses world-value-not-canonical), the store owning canonical BYTES "
    "under TRVM-VALUE-v1 content hashes, and fresh parses on every read — "
    "both alias directions (ingress after put, egress through read "
    "results) die at the boundary. Deletions are TOMBSTONES: the deletion "
    "version is observable, so 'deleted' and 'never existed' do not "
    "collapse at the version layer.",
    "Round-8B audit witness AUDIT-WORLD-ALIAS, reproduced executably "
    "against v0.2.0: world.read(r).value.push(2) mutated the world with no "
    "put, no version change — freshness said fresh while jailed replay "
    "said value-mismatch (the two verifiers disagreed); the ingress "
    "variant leaked {a:{b:[1,99]}}. v0.3.0: L-ALIAS-1 (the witness "
    "verbatim now a no-op with verifier agreement restored; ingress and "
    "nested aliases dead; 6/6 non-canonical refusals); L-WORLD-1 "
    "(tombstone lifecycle, version=>hash)."),
  E("warrant.fresh-replay-coherence", 1, "PROPERTY-TESTED", True,
    "FRESH implies REPLAY-COHERENT: for a deterministic derivation, if "
    "freshness(warrant, world) is fresh then jailed replay must succeed — "
    "the two verification mechanisms may not disagree. This is the "
    "corollary of write-mediation that warrant soundness actually "
    "consumes; the audit witness falsified exactly this implication on "
    "the aliasing substrate.",
    "trvm_world.mjs L-COHERE-1: 200 random histories with adversarial "
    "alias attempts (retained and fresh read references), unrelated "
    "writes, identical rewrites, and support deletions — every FRESH "
    "verdict (151/151) replayed ok; non-fresh verdicts agree with replay "
    "or are support_intact refresh candidates; per-history version=>hash "
    "invariant over all logged pairs, store cross-checked against its own "
    "log."),
])

G["artifact_versions"]["trvm_world.mjs"] = "0.3.0"

W = G["world"]
W["artifact"] = ("trvm_world.mjs v0.3.0 — a separate executable; the calculus "
  "kernel is FROZEN at v1.0.2 and has no world by design")
W["canonical_value_domain"] = ("null | boolean | finite number | string | "
  "array of canonical | plain object with canonical (sorted) key order. "
  "Everything else refuses world-value-not-canonical. The store owns "
  "canonical bytes; value_hash = H('TRVM-VALUE-v1' | bytes); every read is "
  "a fresh parse. (law:world.write-mediated@1)")
W["deletions"] = ("TOMBSTONES: del advances the vclock and the tombstone "
  "carries the deletion version; read returns {value: undefined, version: "
  "delVersion, deleted: true}; 'never existed' stays {version: 0}. names() "
  "and exists() are extensional (live only).")
W["round_8_1_witness"] = ("AUDIT-WORLD-ALIAS (external): state changed "
  "without an identity transition — read-aliased mutation left version and "
  "vclock fixed while freshness said fresh and replay said value-mismatch. "
  "The layer's own analog of the round-6 execution-vs-semantic identity "
  "problem: evidence cannot outrun the state identity of the world it "
  "describes. The law beneath warrant freshness is not merely that "
  "versions increase — it is that every observable mutation induces an "
  "identity transition.")

coh = next(m for m in G["meta_laws"] if m["id"] == "COHERENCE")
coh["evidence"].append(
  "Round 8.1: the world layer's identity law — every observable mutation "
  "induces an identity transition (law:world.write-mediated@1) — and its "
  "warrant corollary FRESH => REPLAY-COHERENT "
  "(law:warrant.fresh-replay-coherence@1); the audit witness that "
  "falsified the implication on the aliasing substrate is reproduced and "
  "kept in the record")

G["kernel_evidence"]["round_8_1"] = collections.OrderedDict([
  ("headline", "The write-mediation closure: the round-8B audit falsified "
    "the substrate under the whole warrant layer — JS reference aliasing "
    "let state change without an identity transition, splitting the two "
    "verifiers (freshness fresh, replay value-mismatch). Closed as a law: "
    "canonical resource-value domain, store-owned bytes with content "
    "hashes, fresh parses on read, tombstoned deletions "
    "(law:world.write-mediated@1), plus the corollary FRESH => "
    "REPLAY-COHERENT (law:warrant.fresh-replay-coherence@1). All thirteen "
    "world batteries green on the fixed substrate."),
  ("audit_verification", [
    "AUDIT-WORLD-ALIAS reproduced exactly against v0.2.0: version 1 "
    "unchanged, freshness fresh, replay value-mismatch after "
    "read(r).value.push(2); ingress variant leaked {a:{b:[1,99]}}; "
    "deletion read back at version 0 while the vclock said 2.",
    "The audit also caught a vacuous assertion (`... || true`) in "
    "L-WORLD-1 — the battery introducing the monotonicity law contained a "
    "check that could not fail. Removed; battery strengthened; recorded "
    "without excuse.",
    "Composition (round 8) was built before this audit arrived; it is not "
    "retracted — every composition battery re-ran green on the "
    "write-mediated substrate, and the composition laws' statements did "
    "not depend on the aliasing hole."]),
  ("batteries", "L-WORLD-1 (strengthened), L-ALIAS-1, L-COHERE-1; all ten "
    "prior world batteries re-run green."),
])

CH = [
  "STATE CANNOT CHANGE WITHOUT AN IDENTITY TRANSITION. The audit's "
  "AUDIT-WORLD-ALIAS falsified the substrate: the store held JS values by "
  "reference, so world.read(r).value.push(2) mutated the world with no "
  "put and no version movement — and the two verifiers DISAGREED "
  "(freshness: fresh; jailed replay: value-mismatch). Closed as "
  "law:world.write-mediated@1: a canonical resource-value domain, "
  "store-owned bytes under TRVM-VALUE-v1 content hashes, fresh parses on "
  "every read, both alias directions dead at the boundary — same version "
  "implies same canonical value. The witness is reproduced and kept.",
  "DELETED IS NOT NEVER-EXISTED. Deletions are tombstones carrying the "
  "deletion version; the version layer no longer collapses the two "
  "histories, and the lifecycle (absent -> put -> update -> delete -> "
  "recreate) is a battery.",
  "FRESH => REPLAY-COHERENT, AS ITS OWN LAW. The implication the witness "
  "falsified is now law:warrant.fresh-replay-coherence@1, property-tested "
  "over 200 random histories with adversarial alias attempts: every fresh "
  "verdict replays ok, and the per-history version=>hash invariant holds "
  "with the store cross-checked against its own log.",
  "AN AUDIT CAUGHT A VACUOUS ASSERTION. L-WORLD-1's first version "
  "contained `... || true` — incapable of failing, in the battery "
  "introducing the monotonicity law. Removed, battery strengthened "
  "(latest-read on all six live resources, tombstone lifecycle, "
  "version=>hash), and confessed in the evidence line rather than "
  "silently fixed.",
  "THE LAYERS' LESSONS RHYME, AND THE RECORD SAYS SO. Round 5: authority "
  "must not outrun evidence. Round 6: identity must know what it "
  "identifies. Round 8.1: evidence cannot outrun the state identity of "
  "the world it describes — the world-layer analog of the "
  "execution-vs-semantic split, recorded in world.round_8_1_witness.",
]
NG = collections.OrderedDict()
for k, v in G.items():
    NG[k] = v
    if k == "changelog_from_1_1_0":
        NG["changelog_from_1_2_0"] = CH
assert "changelog_from_1_2_0" in NG
json.dump(NG, open("invariant-grid.json", "w"), indent=1, ensure_ascii=False)
open("invariant-grid.json", "a").write("\n")
print("grid v1.3.0:", len(G["law_registry"]["entries"]), "entries")
