#!/usr/bin/env python3
# invariant-grid.json v0.6 -> v1.0.0 : round-6 (identity) edit.
# Key-order preserving; preconditions asserted; idempotence guarded.
import json, collections

G = json.load(open("invariant-grid.json"), object_pairs_hook=collections.OrderedDict)
assert G["version"] == "0.6", "grid not at v0.6?"
G["version"] = "1.0.0"
G["date"] = "2026-08-18"

REG = G["law_registry"]
REG["grid_version"] = "1.0.0"
by = {(e["id"], e["revision"]): e for e in REG["entries"]}

# ── strengthen sched.free.float@1 evidence (6 schedulers, 144 receipts) ───
sf = by[("sched.free.float", 1)]
assert sf["canonical"] is True
sf["evidence"] += (" Round 6: the certified battery widens to 6 schedulers — the four free "
    "ones plus two STARVATION ADVERSARIES (law:sched.adversarial.float@1) — 144 receipts, "
    "144/144 completed/NF-matched/readback-pure, max steps UNCHANGED at 91.")

def E(id, rev, status, canonical, statement, evidence, **kw):
    x = collections.OrderedDict()
    x["id"] = id; x["revision"] = rev; x["status"] = status; x["canonical"] = canonical
    x["statement"] = statement; x["evidence"] = evidence
    for k, v in kw.items(): x[k] = v
    return x

REG["entries"].extend([
  E("state.exec-identity", 1, "PROPERTY-TESTED", True,
    "execStateId (= floatDigest: total heap folded in id order, dead entries "
    "included, canonical alpha/label digest) is EXECUTION identity — "
    "deliberately allocation-sensitive, which is exactly what makes it "
    "replay-grade within one implementation and one allocator discipline. "
    "Films and certificate receipts bind THIS id, and only this id.",
    "L-SEMID-1 (the round-6 audit witness reproduced byte-for-byte: two "
    "behaviorally identical states, digests 18b4e47b... vs 6bca1878... under a "
    "heap-id swap — VARIANCE asserted, by declaration not by accident); "
    "L-REFINE-1 (execution films are allocator-bound: the descending "
    "allocator's films are refused by replayFloat on 17/24 vectors and "
    "bit-identical on the 7 single-dup ones)."),
  E("state.semantic-quotient", 1, "PROPERTY-TESTED", True,
    "semStateId is SEMANTIC identity: the LIVE heap folded in first-reachable "
    "DISCOVERY ORDER from the root, then the canonical digest. The quotient "
    "makes heap-id bijections, DEAD heap content, allocation order, "
    "alpha-renaming, and dup/sup label bijections unobservable. "
    "Cross-allocator and cross-implementation claims bind THIS id, never the "
    "execution id.",
    "L-SEMID-1 (invariance under the audit witness swap, dead-entry "
    "injection, alpha-rename, label bijection, the DESCENDING adversarial "
    "allocator, and mid-run random heap-id bijections — with execution "
    "identity varying alongside); L-SEMID-2 (adequacy, sampled: 0 collisions "
    "over all corpus pairs, the locked digest-adequacy pair separates "
    "semantically too, under the stated SHA-256 collision-resistance "
    "assumption); L-REFINE-1 (per-step semantic chains equal across "
    "allocators on all 24 vectors)."),
  E("kernel.identity", 1, "REGRESSION-LOCKED", True,
    "The executable may not disagree with the artifact identity: "
    "KERNEL_VERSION is a runtime constant; the source header carries it, the "
    "banner prints it, and the emitted certificate's generator string cites "
    "it. Locked, not property-tested: this guards a specific regression the "
    "round-6 audit witnessed (v0.6 source printing a v0.5 banner), one round "
    "after the evidence-binding round.",
    "L-ID-1 (source-header scan + certificate generator equality); grid_check "
    "v2.3 additionally locks grid.version to the kernel's KERNEL_VERSION "
    "(engine-free, source-text scan)."),
  E("refine.alloc-portability", 1, "PROPERTY-TESTED", True,
    "The refinement bridge: two allocators of the SAME relation "
    "(ascending FloatRt; adversarial descending DescFloatRt, the stand-in for "
    "a second implementation until ic32) run every vector in lockstep with "
    "equal per-step SEMANTIC chains, equal reference NFs, equal interaction "
    "counts. The SEMANTIC FILM — canonical loci, semantic pre/post ids, "
    "committed terminal (TRVM-SEMFILM-v1) — built on one allocator REPLAYS on "
    "the other by locus matching; execution films do not travel. A "
    "RefinementReceipt records the asymmetry per term.",
    "L-REFINE-1: 24/24 semantic chains equal; semantic films replay "
    "cross-allocator 24/24; execution film A replays 24/24, execution film B "
    "refused by replayFloat 17/24 and bit-identical 7/24 (single-dup states "
    "where fold order cannot differ) — refinement_receipt.json carries the "
    "per-term record and grid_check v2.3 recomputes its arithmetic and "
    "commitment engine-free."),
  E("sched.adversarial.float", 1, "PROPERTY-TESTED", True,
    "Persistent starvation of a redex CLASS does not break progress on the "
    "floating-dup relation: starve_dups fires an APP whenever any is enabled; "
    "starve_apps fires a heap DUP whenever any is enabled. Both complete, "
    "NF-agree, stay readback-pure, and preserve the schedule-invariant "
    "interaction count on the whole corpus — inside the certified battery, "
    "with receipts, not as a side experiment.",
    "L-SCHED-FLOAT-1 (144 receipts across 6 schedulers; max steps 91 — the "
    "adversaries did not even worsen the bound on this corpus); the "
    "SchedulerCertificate commits all six scheduler names and the checker "
    "re-executes every adversarial receipt like any other."),
])

# ── state_identity: the standing question is ANSWERED and CLOSED ──────────
G["state_identity"] = collections.OrderedDict([
  ("resolution", "The v0.5/v0.6 open question — is floatDigest invariant under "
    "heap-id permutation? — is answered NO, by an external-audit witness "
    "reproduced here byte-for-byte: two states with identical behavior (same "
    "enabled rules, same NF ((X Y) (X Y)), same counts) digest to "
    "18b4e47b34d38339... vs 6bca1878284b4dfd... under a heap-id swap, and a "
    "DEAD heap entry perturbs the digest while the live state is untouched. "
    "The verdict adopted is the audit's: this is not a bug in the digest — it "
    "is the WRONG QUOTIENT for semantic claims. Identity SPLITS."),
  ("execution_identity", "execStateId (= floatDigest) — total heap, id-order "
    "fold, dead entries included. Allocation-sensitive BY DECLARATION; "
    "replay-grade; bound by films and certificate receipts "
    "(law:state.exec-identity@1)."),
  ("semantic_identity", "semStateId — LIVE heap only, folded in "
    "first-reachable discovery order, canonical alpha/label digest. "
    "Quotients heap-id bijections, dead content, allocation order, alpha, "
    "labels (law:state.semantic-quotient@1). Bound by semantic films and the "
    "RefinementReceipt; the id a second implementation must reproduce."),
  ("design_rule", "One digest is never forced to mean two things: portable "
    "claims name semStateId, replay claims name execStateId, and any "
    "artifact that binds one of them says WHICH. (Adopted from the round-6 "
    "review's execution_state_id / semantic_state_id proposal.)"),
  ("open", "Cross-IMPLEMENTATION invariance (ic32) is constructed-for but "
    "not yet exercised: DescFloatRt is an adversarial stand-in, not a second "
    "implementation. The semantic-film replay protocol is the interface ic32 "
    "must satisfy."),
])

# ── semantic_film: the portable evidence object ───────────────────────────
G["semantic_film"] = collections.OrderedDict([
  ("law", "law:refine.alloc-portability@1 with law:state.semantic-quotient@1"),
  ("domain_tag", "TRVM-SEMFILM-v1"),
  ("frame_fields", ["i (non-authoritative)", "plane", "rule",
    "locus (CANONICAL: t:<path> | d:<discovery-ix> | v:<discovery-ix>:<path>)",
    "pre (semStateId)", "post (semStateId)", "prev", "frame_id"]),
  ("terminal_fields", ["termination", "steps", "last_frame",
    "final_sem_id", "normal_form_id", "planes (RULE pool, as in execution films)"]),
  ("replay", "replaySemFilm(term, film, RtClass): extrude on a FRESH runtime "
    "of ANY class implementing the relation; per frame, the rule must be in "
    "the declared pool, the semantic pre must match, the canonical locus must "
    "MATCH an enabled redex (enabledness is inherent — an unmatched locus "
    "refuses), the rule/plane/post/chain re-derive; the terminal re-derives "
    "including semantic quiescence and the NF."),
  ("replay_refusals", ["sem-terminal-missing", "sem-plane-not-permitted",
    "sem-revision-mismatch", "sem-locus-not-enabled", "sem-not-a-redex",
    "sem-rule-mismatch", "sem-plane-mismatch", "sem-post-mismatch",
    "sem-chain-mismatch", "sem-terminal-last-frame-mismatch",
    "sem-terminal-steps-mismatch", "sem-terminal-state-mismatch",
    "sem-false-normal-form", "sem-terminal-nf-mismatch",
    "sem-terminal-malformed", "sem-film-id-mismatch"]),
  ("relation_to_execution_films", "Execution films (film_v3_1) stay the "
    "LOCAL evidence: allocator-bound, replayed by replayFloat on the same "
    "discipline that made them. Semantic films are the PORTABLE evidence: "
    "what travels across allocators today and implementations tomorrow. "
    "L-REFINE-1 exhibits both directions on every vector."),
])

# ── refinement_receipt: machine-readable shape for grid_check ─────────────
G["refinement_receipt"] = collections.OrderedDict([
  ("type", "RefinementReceipt"), ("version", 1),
  ("law_refs_expected", ["law:refine.alloc-portability@1",
    "law:state.semantic-quotient@1", "law:state.exec-identity@1"]),
  ("relation", "floating-dup-heap-v1"),
  ("allocators", collections.OrderedDict([
    ("A", "ascending (FloatRt)"),
    ("B", "descending-stride-13 (DescFloatRt), an adversarial stand-in for a "
      "second implementation until ic32")])),
  ("per_term_fields", ["name", "steps", "interactions", "sem_chain_equal",
    "nf_id", "sem_film_id", "exec_film_id_A", "exec_film_id_B",
    "exec_films_equal", "sem_film_replay_on_B", "exec_film_B_replay"]),
  ("commitment", "receipt_id = H(\"TRVM-REFINE-v1\" | JSON(per_term) | "
    "JSON(summary))"),
  ("summary_arithmetic", "sem_chains_equal = count(per_term.sem_chain_equal); "
    "exec_films_B_refused_by_A_replay = count(exec_film_B_replay startswith "
    "'refused'); exec_films_identical_across_allocators = "
    "count(exec_films_equal); refused + identical = terms; "
    "sem_films_replayed_on_B = count(sem_film_replay_on_B == 'ok'). "
    "grid_check v2.3 recomputes ALL of these engine-free and recomputes the "
    "commitment; the kernel battery re-derives the underlying runs."),
])

# ── scheduler_certificate: 6 schedulers, 144 receipts ─────────────────────
SC = G["scheduler_certificate"]
SC["strategy_schedulers"] = ["leftmost", "deepest", "middle", "random",
  "starve_dups", "starve_apps"]
SC["evidence_snapshot"] = collections.OrderedDict([
  ("schedulers", 6), ("terms", 24), ("runs", 144), ("completed", 144),
  ("nf_matched", 144), ("readback_pure", 144), ("max_steps", 91)])
SC["round_6_note"] = ("Two of the six schedulers are starvation adversaries "
  "(law:sched.adversarial.float@1); the certificate shape, laws, and checker "
  "are unchanged — the battery widened and the receipts carry it.")

# ── kernel_evidence.round_6 ───────────────────────────────────────────────
KE = G["kernel_evidence"]
KE["round_6"] = collections.OrderedDict([
  ("headline", "The identity round: the standing Coherence question answered "
    "NO by external audit and CLOSED by a SPLIT — execution identity "
    "(allocation-sensitive, replay-grade) vs semantic identity (live-only, "
    "discovery-ordered, id/dead/alpha/label/allocation-invariant) — plus the "
    "executable ic32 bridge (semantic films replay across an adversarial "
    "allocator) and starvation-adversarial scheduling inside the certified "
    "battery. v1.0.0: the calculus layer's law set is closed over its own "
    "claims."),
  ("audit_verification", [
    "GPT's heap-id-swap witness reproduced byte-for-byte (18b4e47b... vs "
    "6bca1878...; behaviors verified identical: enabled DUP-VAR,DUP-VAR; "
    "NF ((X Y) (X Y)); 2 steps; 2 interactions).",
    "Extension found here: a DEAD heap entry also perturbs floatDigest while "
    "the live state (and semStateId) is unchanged.",
    "Design probe: a MONOTONE allocator perturbation is invisible to sorted "
    "folds — the separation witness requires NON-monotone (order-reversing) "
    "allocation; DescFloatRt is built accordingly.",
    "Version regression confirmed: v0.6 source printed a v0.5 banner; "
    "build_v06.py described itself as assembling v0.5. Both locked "
    "(law:kernel.identity@1)."]),
  ("batteries", "L-SEMID-1 (split, adversarial), L-SEMID-2 (adequacy, "
    "sampled), L-REFINE-1 (dual-allocator lockstep + cross-replay + "
    "RefinementReceipt), L-ID-1 (identity lock), L-SCHED-FLOAT-1 widened to "
    "144 receipts."),
])

# ── meta_laws: COHERENCE advances ─────────────────────────────────────────
coh = next(m for m in G["meta_laws"] if m["id"] == "COHERENCE")
coh["evidence"].append(
  "Round 6: the heap-order obligation named in v0.5 is RESOLVED by splitting "
  "identity (law:state.exec-identity@1, law:state.semantic-quotient@1) — and "
  "the semantic quotient immediately pays: per-step semantic chains equal "
  "across an adversarial allocator on the whole corpus "
  "(law:refine.alloc-portability@1)")

# ── v1 criteria ───────────────────────────────────────────────────────────
V1 = collections.OrderedDict([
  ("scope", "v1.0.0 covers the CALCULUS LAYER only. WORLD and EFFECT planes, "
    "the sigma profile, CP5-CP7 PhaseSpan, and Warrant v3 (with the shared "
    "support/footprint concept adopted in round 5) are TRVM/WRL layers above "
    "this kernel: named here, built next, not debt of the kernel."),
  ("criteria", collections.OrderedDict([
    ("conformance", "reference semantics reproduced on the vector corpus — "
      "CONF-1"),
    ("dual_state_identity", "execution + semantic identities, each "
      "adversarially tested, scopes declared — L-SEMID-1/2, "
      "law:state.exec-identity@1, law:state.semantic-quotient@1"),
    ("progress_free_and_adversarial", "completion, NF agreement, readback "
      "purity, count invariance under 6 schedulers incl. 2 starvation "
      "adversaries, receipts for every run — L-SCHED-FLOAT-1, "
      "law:sched.free.float@1, law:sched.adversarial.float@1"),
    ("plane_partition", "INTERACT/COLLAPSE as executable relations with the "
      "measured interleaved fixpoint — law:plane.rule-partition@1, "
      "law:plane.separation.fixpoint@1"),
    ("films", "execution films with live-relation enabledness (18 refusals) "
      "AND portable semantic films (16 refusals) — "
      "law:film.evidence-chain@5, semantic_film section"),
    ("certificates", "receipt-based SchedulerCertificate v2, field "
      "discipline, full re-execution checker, engine-free grid half — "
      "law:sched.certificate@2, law:cert.field-discipline@1"),
    ("refinement_bridge", "cross-allocator semantic-chain equality and "
      "semantic-film replay, receipted — law:refine.alloc-portability@1"),
    ("artifact_identity", "executable == artifact, locked — "
      "law:kernel.identity@1"),
    ("self_falsification", "every by-design red row still red; the registry, "
      "citations, and this record checked by grid_check — "
      "law:grid.consistency@2"),
  ])),
  ("declared_not_met_by_design", "cross-IMPLEMENTATION refinement (ic32) — "
    "the interface exists (semantic films, RefinementReceipt), the second "
    "implementation does not yet."),
])

# ── changelog_from_0_6 + key-order rebuild ────────────────────────────────
CH = [
  "THE IDENTITY QUESTION, ANSWERED AGAINST US AND CLOSED. External audit "
  "constructed the witness this record had named-but-not-built: floatDigest "
  "varies under heap-id permutation on behaviorally identical states "
  "(18b4e47b... vs 6bca1878...). Reproduced byte-for-byte, extended (dead "
  "entries perturb it too), and resolved by a SPLIT, not a weakening: "
  "execStateId stays allocation-sensitive and replay-grade "
  "(law:state.exec-identity@1); semStateId folds the LIVE heap in discovery "
  "order and quotients ids, dead content, allocation order, alpha, and "
  "labels (law:state.semantic-quotient@1). One digest is never forced to "
  "mean two things.",
  "THE IC32 BRIDGE IS EXECUTABLE TODAY. An adversarial DESCENDING allocator "
  "— chosen because a monotone perturbation is invisible to sorted folds — "
  "runs every vector in lockstep with the standard one: per-step semantic "
  "chains equal 24/24, NFs reference-equal, counts equal. SEMANTIC FILMS "
  "(canonical loci, semantic pre/post, TRVM-SEMFILM-v1 commitment) replay "
  "across allocators 24/24; execution films are refused 17/24 and "
  "bit-identical 7/24. refinement_receipt.json records the asymmetry "
  "(law:refine.alloc-portability@1); grid_check recomputes its arithmetic "
  "and commitment engine-free.",
  "STARVATION INSIDE THE CERTIFICATE. starve_dups and starve_apps join the "
  "battery — 144 receipts, six committed scheduler names, max steps "
  "unchanged at 91 (law:sched.adversarial.float@1). Fairness evidence "
  "travels in the same receipts as freedom evidence.",
  "THE EXECUTABLE MAY NOT DISAGREE WITH THE ARTIFACT. The audit caught v0.6 "
  "source printing a v0.5 banner one round after evidence-binding. "
  "KERNEL_VERSION is a constant; header, banner, and certificate generator "
  "must agree (L-ID-1, REGRESSION-LOCKED, law:kernel.identity@1), and "
  "grid_check locks grid.version to the kernel source.",
  "V1.0.0 DECLARED, WITH ITS SCOPE STATED. The calculus layer's law set is "
  "closed over its own claims (see v1_criteria); WORLD/EFFECT, sigma, "
  "CP5-CP7, and Warrant v3 with the shared support/footprint concept are "
  "the named next layers. The one criterion declared NOT met by design: a "
  "second implementation — the interface for it is what this round built.",
]
NG = collections.OrderedDict()
for k, v in G.items():
    NG[k] = v
    if k == "date":
        NG["v1_criteria"] = V1
    if k == "changelog_from_0_5":
        NG["changelog_from_0_6"] = CH
assert "changelog_from_0_6" in NG and "v1_criteria" in NG
json.dump(NG, open("invariant-grid.json", "w"), indent=1, ensure_ascii=False)
open("invariant-grid.json", "a").write("\n")
print("grid v1.0.0 written:", len(REG["entries"]), "registry entries")
