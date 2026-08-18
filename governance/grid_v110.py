#!/usr/bin/env python3
# invariant-grid.json v1.0.1 -> v1.1.0 : round-7 (the warrant round).
import json, collections

G = json.load(open("invariant-grid.json"), object_pairs_hook=collections.OrderedDict)
assert G["version"] == "1.0.1", "grid not at v1.0.1?"
G["version"] = "1.1.0"
G["law_registry"]["grid_version"] = "1.1.0"
by = {(e["id"], e["revision"]): e for e in G["law_registry"]["entries"]}

def E(id, rev, status, canonical, statement, evidence, **kw):
    x = collections.OrderedDict()
    x["id"] = id; x["revision"] = rev; x["status"] = status; x["canonical"] = canonical
    x["statement"] = statement; x["evidence"] = evidence
    for k, v in kw.items(): x[k] = v
    return x

# ── kernel.identity@1 -> @2 : multi-artifact identity ─────────────────────
ki = by[("kernel.identity", 1)]
assert ki["canonical"] is True
ki["canonical"] = False
ki["superseded_by"] = "kernel.identity@2"
ki["evidence"] += (" Superseded in round 7: with a second executable "
    "(trvm_world.mjs) the single grid.version==KERNEL_VERSION lockstep is the "
    "wrong shape — identity became a MAP.")

G["law_registry"]["entries"].extend([
  E("kernel.identity", 2, "REGRESSION-LOCKED", True,
    "No executable may disagree with its artifact identity, and the RECORD "
    "may not disagree with any of them: every shipped executable declares a "
    "version constant; the grid carries artifact_versions, a map from "
    "artifact to declared version; grid_check parses each constant from "
    "source and locks the map. grid.version is the RECORD's own lineage "
    "version, decoupled from any single artifact.",
    "L-ID-1 (kernel-side: header == constant == certificate generator); "
    "grid_check v2.5 (engine-free: KERNEL_VERSION and WORLD_VERSION parsed "
    "from source, each locked to artifact_versions). Supersedes @1, whose "
    "single-artifact lockstep round 7 outgrew."),
  E("world.version-monotone", 1, "PROPERTY-TESTED", True,
    "The WorldRecord's versions strictly increase on a global vclock; the "
    "log is append-only and dense; a read returns the latest write. Scope "
    "queries are REGISTERED and their evaluations REIFIED as digests of "
    "canonical result sets — a predicate observation is itself a versioned "
    "observable, not an ambient fact.",
    "trvm_world.mjs L-WORLD-1 (50 writes + delete: strict vclock, dense "
    "append-only log, latest-read)."),
  E("warrant.freshness", 1, "PROPERTY-TESTED", True,
    "A warrant is a VERIFYING TRACE generalized: freshness(warrant, world) "
    "iff every exact read [resource@version] and every predicate scope "
    "[query@digest] re-evaluates unchanged. Unrelated writes never "
    "invalidate — freshness reads the footprint, not the world's write "
    "counter. (The build-systems verifying-trace idea, plus the "
    "predicate-lock idea from serializable databases, as one shape.)",
    "trvm_world.mjs L-WAR-1: component-size warrant fresh at seal and "
    "STILL fresh after 50 unrelated writes; goes stale precisely when its "
    "footprint moves (L-WAR-4)."),
  E("warrant.footprint-soundness", 1, "PROPERTY-TESTED", True,
    "The read footprint is an AUTHORITY CLAIM, so replay is JAILED: the "
    "derivation re-runs under a view that permits only the declared "
    "footprint — an undeclared read or scope refuses (undeclared-read, "
    "undeclared-scope), versions must match (footprint-version-mismatch), "
    "scopes must re-digest (scope-digest-mismatch), and value/witness/"
    "commitment re-derive (value-mismatch, witness-mismatch, "
    "warrant-id-mismatch, support-not-subset). A pruned footprint dies at "
    "the jail even when honestly resealed. Authority must not outrun "
    "evidence — the rounds-5/6 law, applied to reads.",
    "trvm_world.mjs L-WAR-2: honest replay ok; pruned-footprint, "
    "inflated-value, unsealed-mutation, and support-beyond-footprint "
    "forgeries each refused on their declared reason."),
  E("warrant.phantom-scope", 1, "PROPERTY-TESTED", True,
    "Exact reads alone cannot witness membership of a set that grew: a "
    "resource absent at read time can join the measured structure without "
    "touching any read resource (the kappa phantom case, executable). The "
    "guard is a predicate scope: a reified query whose digest is committed "
    "in the footprint; the phantom flips the digest and classifies "
    "scope_dirty even though every exact read is byte-identical. The "
    "UNGUARDED warrant's fresh-while-wrong witness is kept red by "
    "construction.",
    "trvm_world.mjs L-WAR-3: phantom constructed (new node + edge via a "
    "writer that leaves every read resource untouched): true size 3 vs "
    "warranted 2 with the naked warrant 'fresh'; the scope-guarded warrant "
    "classifies scope_dirty on the incident-edge digest."),
  E("warrant.invalidation-trichotomy", 1, "PROPERTY-TESTED", True,
    "Staleness is classified, each verdict with a complete witness "
    "(law:film.terminal-witness@1 applied to verdicts): support_changed "
    "(a support resource moved — re-derive), scope_dirty (a predicate "
    "scope moved — re-derive; the phantom lives here), support_intact (a "
    "read-but-not-support resource moved — eligible for EARLY CUTOFF: "
    "jailed re-derivation that reproduces the value refreshes the "
    "footprint and reseals instead of discarding).",
    "trvm_world.mjs L-WAR-4: three worlds, one verdict each, witnesses "
    "asserted; the support_intact case refreshes — value preserved, "
    "footprint reversioned, warrant_id resealed, refreshed warrant fresh."),
  E("footprint.shared", 1, "PROPERTY-TESTED", True,
    "Warrants and certificates speak ONE evidence language: a Footprint "
    "{exact, predicates} with footprint_id. The SchedulerCertificate maps "
    "into it — corpus{id,sha256} is one exact read, evidence is the value, "
    "the run-manifest hash is the witness — so certificate freshness IS "
    "warrant freshness. (The requirement round 5 adopted, discharged.)",
    "trvm_world.mjs L-WAR-5: the shipped 144-receipt certificate wrapped "
    "as a Warrant v3; fresh at seal, fresh under unrelated writes, "
    "support_changed exactly when the corpus resource moves."),
])

# ── artifact identity map ─────────────────────────────────────────────────
G["artifact_versions"] = collections.OrderedDict([
  ("trvm_law_kernel.mjs", "1.0.1"),
  ("trvm_world.mjs", "0.1.0"),
])

# ── warrant section: the spec gains its executable half ──────────────────
W = G["warrant"]
W["executable"] = collections.OrderedDict([
  ("artifact", "trvm_world.mjs v0.1.0"),
  ("commitment", "warrant_id = H(\"TRVM-WARRANT-v3\" | canonical committed "
    "fields [measure, predicate, value, witness, support(sorted), "
    "read_footprint(sorted), derivation_id, at_vclock]); "
    "footprint_id = H(\"TRVM-FOOTPRINT-v1\" | exact | predicates)"),
  ("field_discipline", "COMMITTED: measure, predicate, value, witness, "
    "support, read_footprint, derivation_id, at_vclock. DERIVED on jailed "
    "replay: value, witness, every read's footprint membership and "
    "version, every scope digest. INFORMATIONAL: informational.* "
    "(precedent law:cert.field-discipline@1)."),
  ("replay_refusals", ["undeclared-read", "undeclared-scope",
    "footprint-version-mismatch", "scope-digest-mismatch", "value-mismatch",
    "witness-mismatch", "warrant-id-mismatch", "support-not-subset"]),
  ("freshness_verdicts", ["fresh", "support_changed", "scope_dirty",
    "support_intact"]),
  ("verdict_witnesses", "every verdict carries a complete witness: fresh -> "
    "{checked_exact, checked_scopes}; support_changed/support_intact -> "
    "{resource, was, now}; scope_dirty -> {scope, was, now} "
    "(law:film.terminal-witness@1 applied to verdicts)"),
  ("laws", ["law:world.version-monotone@1", "law:warrant.freshness@1",
    "law:warrant.footprint-soundness@1", "law:warrant.phantom-scope@1",
    "law:warrant.invalidation-trichotomy@1", "law:footprint.shared@1"]),
])

# ── world section ─────────────────────────────────────────────────────────
G["world"] = collections.OrderedDict([
  ("artifact", "trvm_world.mjs v0.1.0 — a separate executable; the calculus "
    "kernel is FROZEN at v1.0.1 and has no world by design"),
  ("record", "versioned resource store (name -> {value, version}) on a "
    "global monotone vclock; append-only dense log; registered scope "
    "queries reified as digests (domain TRVM-SCOPE-v1)"),
  ("views", collections.OrderedDict([
    ("tracked", "the honest builder: records every exact read "
      "[resource@version] and every scope evaluation [query@digest] into "
      "the footprint"),
    ("jailed", "the replayer: permits ONLY the declared footprint; "
      "undeclared access refuses — authority must not outrun evidence"),
  ])),
  ("flagship", "the kappa-flavored graph world: nodes, edges, and forward "
    "adjacency indices as resources; component-size measures whose "
    "footprints are their traversals; the phantom constructed via a writer "
    "that adds a member without touching any read resource"),
  ("research_anchors", "verifying/constructive traces and early cutoff "
    "(build systems a la carte); demanded computation graphs and nominal "
    "identifiers (Adapton family); predicate locks / SSI phantom "
    "protection (serializable databases); reified tracked queries "
    "(hermetic build glob tracking). The warrant is the common shape: a "
    "portable verifying trace with predicate scopes and a jailed replayer."),
])

# ── kernel_evidence.round_7 ───────────────────────────────────────────────
G["kernel_evidence"]["round_7"] = collections.OrderedDict([
  ("headline", "The warrant round: Warrant v3 goes from grid spec to "
    "executable machinery in a NEW artifact (trvm_world.mjs v0.1.0) — "
    "verifying-trace freshness with reified predicate scopes, JAILED "
    "replay (undeclared reads refuse), the kappa phantom constructed and "
    "guarded, the invalidation trichotomy with early cutoff, and the "
    "round-5 shared-footprint requirement discharged by wrapping the "
    "shipped SchedulerCertificate as a warrant. Kernel untouched at "
    "v1.0.1; identity becomes a MAP (kernel.identity@2)."),
  ("first_run", "all six batteries passed on first execution; skeptical "
    "re-review confirmed each assertion bites (notably: the phantom's "
    "true-size-3-vs-warranted-2 while 'fresh' is a genuine wrong-answer "
    "witness, and the unrelated-churn immunity covers 50 writes)."),
  ("batteries", "L-WORLD-1, L-WAR-1..5 in trvm_world.mjs; "
    "world_warrant_receipt.json checked engine-free by grid_check v2.5."),
])

# ── changelog_from_1_0_1 ──────────────────────────────────────────────────
CH = [
  "THE WARRANT BECAME EXECUTABLE, IN ITS OWN ARTIFACT. Warrant v3 had been "
  "a grid spec since round 3; trvm_world.mjs v0.1.0 implements it whole: "
  "WorldRecord (monotone vclock, append-only log, reified scope queries), "
  "tracked derivation views, warrant commitment under TRVM-WARRANT-v3 with "
  "round-5 field discipline, freshness as a generalized verifying trace, "
  "and JAILED replay where an undeclared read refuses — the "
  "authority-must-not-outrun-evidence law applied to reads "
  "(law:warrant.footprint-soundness@1). The calculus kernel is FROZEN at "
  "v1.0.1, per the closure audit's own recommendation.",
  "THE PHANTOM IS NO LONGER A SENTENCE IN A SPEC. The kappa phantom-read "
  "case — a member joining the measured structure without touching any "
  "read resource — is CONSTRUCTED: true component size 3, warranted value "
  "2, unguarded warrant 'fresh'. Kept red by construction. The guard is a "
  "reified predicate scope whose digest lives in the footprint; the same "
  "phantom classifies scope_dirty under it (law:warrant.phantom-scope@1).",
  "STALENESS IS A CLASSIFICATION WITH WITNESSES, AND ONE CLASS IS CHEAP. "
  "support_changed / scope_dirty / support_intact each carry a complete "
  "verdict witness (film.terminal-witness applied to verdicts); "
  "support_intact performs EARLY CUTOFF — jailed re-derivation reproducing "
  "the value refreshes the footprint and reseals instead of discarding "
  "(law:warrant.invalidation-trichotomy@1).",
  "ONE EVIDENCE LANGUAGE. The round-5 requirement — certificate and "
  "warrant share a support/footprint concept — is discharged executably: "
  "the shipped 144-receipt SchedulerCertificate wraps as a Warrant v3 "
  "whose single exact read is the corpus resource; certificate freshness "
  "IS warrant freshness (law:footprint.shared@1).",
  "IDENTITY BECAME A MAP. Two executables now ship; grid.version is the "
  "record's own lineage and artifact_versions locks each executable's "
  "declared constant (kernel.identity@2 supersedes @1; grid_check v2.5 "
  "parses both constants from source).",
]
NG = collections.OrderedDict()
for k, v in G.items():
    NG[k] = v
    if k == "changelog_from_1_0_0":
        NG["changelog_from_1_0_1"] = CH
assert "changelog_from_1_0_1" in NG
json.dump(NG, open("invariant-grid.json", "w"), indent=1, ensure_ascii=False)
open("invariant-grid.json", "a").write("\n")
print("grid v1.1.0 written:", len(G["law_registry"]["entries"]), "entries")
