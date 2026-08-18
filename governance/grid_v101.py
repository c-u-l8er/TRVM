#!/usr/bin/env python3
# invariant-grid.json v1.0.0 -> v1.0.1 : round-6.1 (terminal-witness closure).
import json, collections

G = json.load(open("invariant-grid.json"), object_pairs_hook=collections.OrderedDict)
assert G["version"] == "1.0.0", "grid not at v1.0.0?"
G["version"] = "1.0.1"
G["law_registry"]["grid_version"] = "1.0.1"

def E(id, rev, status, canonical, statement, evidence, **kw):
    x = collections.OrderedDict()
    x["id"] = id; x["revision"] = rev; x["status"] = status; x["canonical"] = canonical
    x["statement"] = statement; x["evidence"] = evidence
    for k, v in kw.items(): x[k] = v
    return x

G["law_registry"]["entries"].append(
  E("film.terminal-witness", 1, "PROPERTY-TESTED", True,
    "Every terminal class a replay accepts must have a complete DECLARED "
    "witness schema; every witness field is COMMITTED into the film id; and "
    "replay independently RE-DERIVES every witness field. A terminal that is "
    "accepted but not proven is a forgery channel, whatever the rest of the "
    "chain proves. (Generalizes the round-4 execution-film terminal closure "
    "and the round-5 enabledness closure to a schema-level obligation on "
    "EVERY replay implementation, present and future — ic32 included.)",
    "Round-6B audit witness AUDIT-SEM-BUDGET, reproduced executably: a "
    "zero-frame BUDGET_EXHAUSTED semantic film over an enabled state "
    "replayed ok under TRVM-SEMFILM-v1, and budget/remaining_work mutations "
    "did not change film_id (budget_mutation_preserves_id: true). Closed by "
    "TRVM-SEMFILM-v1.1: both witness fields committed; replay re-derives "
    "the budget terminal (integers, remaining_work == live enabled count "
    "under the declared pool, steps === budget, remaining_work > 0). "
    "L-SEMTERM-1: honest 7-step partial film replays on BOTH allocators; "
    "12/12 forgeries refused, each on its declared reason, including the "
    "audit witness honestly resealed."))

SF = G["semantic_film"]
SF["law"] = ("law:refine.alloc-portability@1 with law:state.semantic-quotient@1 "
  "and law:film.terminal-witness@1")
SF["domain_tag"] = "TRVM-SEMFILM-v1.1"
SF["supersedes_domain"] = ("TRVM-SEMFILM-v1 (round-6.1: accepted BUDGET_EXHAUSTED "
  "while committing and re-deriving none of its witness fields — the audit's "
  "AUDIT-SEM-BUDGET forged it with a zero-frame film)")
SF["terminal_fields"] = ["termination", "steps", "last_frame",
  "final_sem_id", "normal_form_id", "planes (RULE pool, as in execution films)",
  "budget (BUDGET_EXHAUSTED witness, committed)",
  "remaining_work (BUDGET_EXHAUSTED witness, committed, re-derived as the "
  "live enabled count under the declared pool)"]
SF["replay"] = (SF["replay"] + " For BUDGET_EXHAUSTED the terminal witness is "
  "re-derived, not accepted: budget and remaining_work must be integers, "
  "remaining_work must equal the live enabled count under the declared pool "
  "at the replayed final state, steps must EQUAL the declared budget, and "
  "remaining_work must be > 0.")
SF["replay_refusals"] = SF["replay_refusals"] + [
  "sem-terminal-work-mismatch", "sem-budget-mismatch", "sem-no-remaining-work"]
SF["strictness_delta_vs_execution_films"] = (
  "Deliberate: semantic replay requires steps === budget (execution replay "
  "requires steps >= budget) and remaining_work > 0 (execution replay "
  "accepts 0). The honest generator stops exactly at steps === budget, and "
  "a BUDGET_EXHAUSTED claim on a quiescent state is an under-claim — "
  "tolerated in the local evidence object, refused in the portable one "
  "where the terminal class IS the claim. Revisit at film.evidence-chain@6 "
  "if execution films should be tightened to match.")

KE = G["kernel_evidence"]
KE["round_6_1"] = collections.OrderedDict([
  ("headline", "The terminal-witness closure: the round-6B audit falsified "
    "TRVM-SEMFILM-v1's BUDGET_EXHAUSTED contract (accepted, unproven, "
    "uncommitted) — the same species as the round-4 execution-film terminal "
    "hole, reintroduced by the third replay implementation. Closed as a "
    "schema-level LAW (law:film.terminal-witness@1), not a patch."),
  ("audit_verification", [
    "AUDIT-SEM-BUDGET reproduced exactly: enabled0=1, "
    "budget_mutation_preserves_id=true, r1.ok=true, r2.ok=true against "
    "v1.0.0 before the fix.",
    "Root cause pair: semFilmIdOf omitted budget/remaining_work from the "
    "commitment; replaySemFilm had no BUDGET_EXHAUSTED re-derivation branch "
    "at all.",
    "L-REFINE-1 NOT retracted, per the audit's own scoping: its 24 films "
    "all terminate NORMAL_FORM, a path that does re-derive quiescence and "
    "the NF."]),
  ("new_positive", "Honest PARTIAL semantic films replay across allocators "
    "(L-SEMTERM-1's positive direction) — portable checkpoints, the "
    "checkpointing primitive long cross-implementation runs will need."),
  ("batteries", "L-SEMTERM-1 (12 forgeries, each on its declared refusal, "
    "including the audit witness honestly resealed under v1.1)."),
])

V1C = G["v1_criteria"]["criteria"]
V1C["films"] = ("execution films with live-relation enabledness (18 refusals) "
  "AND portable semantic films (19 refusals) with a CLOSED terminal contract "
  "— every accepted terminal class carries a complete, committed, re-derived "
  "witness schema — law:film.evidence-chain@5, law:film.terminal-witness@1, "
  "semantic_film section")

CH = [
  "THE TERMINAL CONTRACT, FALSIFIED AND CLOSED AS A LAW. Round-6B audit: a "
  "zero-frame BUDGET_EXHAUSTED semantic film over an enabled state replayed "
  "ok under TRVM-SEMFILM-v1, and budget/remaining_work were outside the "
  "commitment entirely (budget_mutation_preserves_id: true). Reproduced "
  "byte-for-byte, then closed at the SCHEMA level "
  "(law:film.terminal-witness@1): every accepted terminal class must have "
  "a complete declared witness schema, every witness field committed, "
  "every witness field re-derived on replay. TRVM-SEMFILM-v1.1 commits "
  "budget and remaining_work; replay re-derives the budget terminal, "
  "TIGHTER than execution films where the honest generator permits "
  "(steps === budget; remaining_work > 0). The third replay implementation "
  "was not entitled to inherit the correctness of the first two — recorded "
  "twice now, and the law exists so ic32 (the fourth) inherits the "
  "OBLIGATION instead.",
  "L-REFINE-1 STANDS, SCOPED HONESTLY. Per the audit's own analysis, the "
  "24/24 cross-allocator result holds: every refinement film terminates "
  "NORMAL_FORM, the path that always re-derived its terminal. What was "
  "false was the PROTOCOL's claim to be closed over every terminal it "
  "accepts — the v1_criteria films line now says what is actually proven.",
  "A NEW POSITIVE FELL OUT: honest PARTIAL semantic films replay across "
  "allocators (portable checkpoints) — L-SEMTERM-1's positive direction, "
  "the primitive long cross-implementation runs will need.",
]
NG = collections.OrderedDict()
for k, v in G.items():
    NG[k] = v
    if k == "changelog_from_0_6":
        NG["changelog_from_1_0_0"] = CH
assert "changelog_from_1_0_0" in NG
json.dump(NG, open("invariant-grid.json", "w"), indent=1, ensure_ascii=False)
open("invariant-grid.json", "a").write("\n")
print("grid v1.0.1 written:", len(G["law_registry"]["entries"]), "entries,",
      len(SF["replay_refusals"]), "sem refusals")
