#!/usr/bin/env python3
"""Mutation harness for binding_run49 (Slice B commit 4, the runtime fold).

Every production edit this commit made is REVERTED, one at a time, in an
isolated copy of the tree, and a battery row must then go red. A mutation that
nobody notices is a row that proves nothing.

The three disciplines carried from `mutate46`/`47`/`48`, unchanged:

  * M0 is the NULL MUTANT. Without a control, "caught" means "the copy is
    broken" -- which is what `mutate46`'s first run actually reported.
  * A mutation whose anchor does not appear EXACTLY ONCE is NOT A RESULT.
  * A deliberate `@noop:` must SURVIVE, or every other CAUGHT in the run is
    worthless.

WHAT IS DIFFERENT ABOUT THIS ONE. Commits 2 and 3 mutated a SURFACE -- a parser,
an emitter, a validator -- where a broken mutant is loud. Commit 4 mutates a
FOLD, and the characteristic commit-4 defect is quiet: the world still seals,
the run still completes, every film is still a well-formed Film v0.7. It is
just a film of a different world. So the mutations below are deliberately
weighted towards edits that CANNOT crash:

    M4  fires the route one epoch late          (a legal run of a legal world)
    M5  numbers the claims by storage order      (identical films, different id)
    M6  drops the canonical sort                 (ditto)
    M8  merges into the caller's list            (correct, until called twice)
    M11 honours the policy but not the mailboxes (the R7 defect, restored)

Each of those is a green run that answers a different question than the one
asked, which is the only failure mode a fold really has.
"""
import sys

from mutate_harness import run

ROOT_NOTE = (
    "The harness driver -- the null control, the anchor-exactly-once rule, the"
    " @noop-must-survive rule and the crash-is-not-a-catch rule -- used to be"
    " copied into every mutate*.py. It is `mutate_harness.run` now. Nothing"
    " about THIS file's mutations changed when it moved: the report below is"
    " byte-identical to the hand-rolled driver's, which is the only evidence"
    " that the extraction was faithful rather than merely tidy.")

# (label, file, old, new, rows that MUST go red)
MUTATIONS = [
    ("M0 NULL MUTANT (control: this one must PASS)",
     "wrl_fold.py", 'ROUTE_OPERATION = "Send"', 'ROUTE_OPERATION = "Send"', []),

    ("M0b @noop rewrite of the by-epoch bucket (harness self-check)",
     "wrl_fold.py",
     "    for epoch, claim in route_claims(artifact):\n"
     "        by.setdefault(epoch, []).append(claim)",
     "    for epoch, claim in list(route_claims(artifact)):\n"
     "        by.setdefault(epoch, []).append(claim)",
     "@noop:a rewrite that changes nothing must not be scored as caught"),

    # -------------------------------------------- the runtime image (R1, R6)
    ("M1 the fold mints no claim at all (commit 3's status quo restored)",
     "wrl_fold.py",
     "    routes = WC.routes_of_artifact(artifact)\n    if not routes:",
     "    routes = WC.routes_of_artifact(artifact)\n    if True:",
     # The whole commit, reverted. Worth keeping even though it is the loudest
     # mutation here: it is the state commits 2 and 3 BOTH closed green in, so
     # it is the one shape that is known to pass every earlier battery.
     ["R1", "R6"]),

    ("M2 the route's writer is not the reserved one",
     "wrl_fold.py",
     "        writer, sequence = ident[key]",
     "        writer, sequence = 1, ident[key][1]",
     # Writer 15 is the Q4 reservation. A route that writes as writer 1 can
     # collide on a fact key with a claim the scenario author wrote, and the
     # collision is silent -- ADMIT's first-receipt rule simply keeps one.
     ["R1b"]),

    ("M3 the operation reverted to a SetRotor",
     "wrl_fold.py",
     'ROUTE_OPERATION = "Send"\n',
     'ROUTE_OPERATION = "SetRotor"\n',
     # NOT R1: one route still mints exactly one claim, which is all R1 says.
     # Predicting R1 here was a harness error, and it is worth keeping the
     # note: a mutation that is caught by the WRONG row is a survivor of the
     # row you thought was doing the work.
     ["R1b", "R1d"]),

    # ------------------------------------------------ the firing epoch (R2)
    ("M4 the route fires ONE EPOCH LATE",
     "wrl_fold.py",
     "        epoch = WC.once_epoch(cfg[key.source_id].get(\"clock\"))",
     "        epoch = (WC.once_epoch(cfg[key.source_id].get(\"clock\")) or 0) + 1",
     # The quiet one. Nothing crashes, nothing is refused, the message is still
     # enqueued and still delivered exactly once -- one epoch after the pulser
     # that was supposed to send it. Only a row that names the epoch can see it.
     ["R2", "R6"]),

    ("M5 the epoch derived from the route instead of its SOURCE",
     "wrl_fold.py",
     "        epoch = WC.once_epoch(cfg[key.source_id].get(\"clock\"))",
     "        epoch = 1",
     # "Routes fire at the start" is a plausible reading, and it is right for
     # every world whose sources are all `once(1)` -- which is most of the
     # fixtures. R2 uses two pulsers precisely so that it is not one of them.
     ["R2"]),

    ("M6 `once_epoch` stops tolerating the JSON round-trip",
     "wrl_canonical.py",
     "    c = tuple(clock or ())\n"
     "    return c[1] if len(c) == 2 and c[0] == \"once\" else None",
     "    c = clock or ()\n"
     "    return c[1] if isinstance(c, tuple) and len(c) == 2 "
     "and c[0] == \"once\" else None",
     # A deserialized artifact carries LISTS. This mutant works perfectly on
     # every in-memory artifact and returns None for every artifact that has
     # been through a store -- so the route silently stops firing after a
     # save/load round-trip, which is the exact failure `once_epoch`'s
     # docstring names.
     ["R2"]),

    # ----------------------------------------------- canonical order (R1, R3)
    ("M7 the claim numbered by STORAGE order, not canonical order",
     "wrl_fold.py",
     "    ident = WC.route_claim_identity(routes)",
     "    ident = {WC.route_key(r): (WC.ROUTE_WRITER_ID, i)\n"
     "             for i, r in enumerate(routes)}",
     # A second numbering, which is what `route_claim_identity` exists to
     # prevent. Films are IDENTICAL (ADMIT is order-independent within a
     # batch); only the digest moves -- invisible in every observable except
     # an id.
     #
     # R1c IS DELIBERATELY NOT LISTED HERE, and that omission is the finding.
     # R1c is the row that compares `sequence` against the canonical accessor
     # instead of against a literal, so it is the row one would EXPECT to catch
     # this -- and it does not, because canonicalization sorts `async_routes`
     # into RouteKey order BEFORE sealing. On any artifact `lower()` produces,
     # `enumerate(routes)` and the canonical ordinal are the same function;
     # authoring order cannot separate them because the seal has already
     # erased it. (M8 is the same finding one layer down: its sort is a no-op
     # for exactly the same reason.)
     #
     # Listing R1c anyway would be the comfortable lie -- it would leave this
     # mutant reported as SURVIVED with a note blaming a row that cannot
     # physically catch it. R1e is what actually catches it: it hands the fold
     # a deliberately un-canonically-ordered route list, the one input on which
     # "numbered by key" and "numbered by position" disagree.
     ["R1e"]),

    ("M8 the canonical sort dropped",
     "wrl_fold.py",
     "    out.sort(key=lambda t: (t[0], t[1]))",
     "    pass",
     # This one SURVIVED, and the finding is worth more than the catch. A
     # sealed artifact ALREADY stores its routes in canonical RouteKey order,
     # so for every single-epoch world the sort is a no-op and deleting it
     # changes nothing observable. It becomes load-bearing only where
     # canonical order and EPOCH order disagree -- a world whose first-sorting
     # route fires last. R3b is that world, and it exists because of this
     # mutation.
     ["R3b"]),

    # -------------------------------------------------------- purity (R3)
    ("M9 the fold MERGES INTO the caller's batches",
     "wrl_fold.py",
     "        merged = list(batch) + by.get(epoch0 + i, [])",
     "        merged = batch + by.get(epoch0 + i, []) if False else batch\n"
     "        merged.extend(by.get(epoch0 + i, []))",
     # Correct on the first call and wrong on the second. The bench folds the
     # same script twice (production path + Fixture oracle), so this mutant
     # sends every message twice and the oracle cross-check disagrees with the
     # path it is supposed to confirm.
     ["R3c"]),

    # ------------------------------------------------------- one seam (R4)
    ("M10 `fold_script` grows its OWN injection",
     "wrl_fold.py",
     "    batches = fold_batches(artifact, [b for _lbl, b in script], epoch0)\n"
     "    return [(lbl, batches[i]) for i, (lbl, _b) in enumerate(script)]",
     "    by = route_claims_by_epoch(artifact)\n"
     "    return [(lbl, list(b) + by.get(epoch0 + i, [])[:1])\n"
     "            for i, (lbl, b) in enumerate(script)]",
     # The second injection `wrl_fold` exists to prevent, written the way it
     # would actually be written: a loop that looks right and quietly truncates
     # a co-firing epoch to one claim. The two producers now disagree, and only
     # a row that compares them can tell.
     ["R4"]),

    ("M11 the fold honours the policy but NOT the declared mailboxes",
     "wrl_fold.py",
     "    return [(m, w, c) for m, (w, c) in sorted(mailboxes_of(fx).items())]",
     "    return []",
     # The R7 defect, restored to exactly the state the whole tree was in
     # before this commit. Nothing crashes; Film v0.7 simply drops its mailbox
     # block and canonicalizes the route's target to INVALID_TARGET, so the run
     # produces a film asserting the route addressed a mailbox that does not
     # exist. This is the mutation that row exists for.
     ["R6", "R7"]),

    ("M12 the policy half forgotten instead",
     "wrl_fold.py",
     '    return (artifact.get("semantic_policies") or {}).get("admit_policy_id")',
     "    return None",
     # The mirror of M11, and the reason `runtime_seams` returns both together.
     # It first SURVIVED everything except R7/R7i, and chasing that produced
     # the sharpest finding in this commit: the two policies differ only in
     # how they accumulate SEVERAL claims on one key (append vs collapse-to-
     # min), so a world that sends ONE message folds byte-identically under
     # both. Every row here sent one message. The real defect the mutant
     # causes is a DROPPED MESSAGE on the second send, and R7g/R7h are the
     # rows that say so.
     ["R7", "R7h"]),

    # ------------------------------------------------- the co-firing bound (R9)
    ("M13 the seal's co-firing bound removed",
     "wrl_canonical.py",
     "        if len(keys) > MAX_ROUTE_COFIRE:",
     "        if False:",
     # Reverts to the measured defect: a world with five routes on one pulser
     # SEALS, and then dies inside `admit_step` on a bare `assert` -- the
     # reducer raising an untyped error about a world that validated.
     ["R9c"]),

    ("M14 the co-firing tally keyed by SOURCE instead of by epoch",
     "wrl_canonical.py",
     "    for ep in sorted(by_epoch):\n        keys = by_epoch[ep]",
     "    for ep in sorted(by_epoch):\n"
     "        keys = [k for k in by_epoch[ep]\n"
     "                if k.source_id == sorted(by_epoch[ep])[0].source_id]",
     # The plausible wrong key. Every single-pulser world still behaves, so
     # R9/R9b/R9c all stay green; only two pulsers firing at the same epoch can
     # see it, which is why R9f is a row.
     ["R9f"]),

    ("M15 the co-firing refusal reuses WRL_ROUTE_BUDGET",
     "wrl_canonical.py",
     "            _fail(WRL_ROUTE_BATCH_OVERFLOW,",
     "            _fail(WRL_ROUTE_BUDGET,",
     # One code cannot ask for two opposite repairs. "Declare fewer routes" and
     # "declare them on different epochs" are the two, and a world that is over
     # only the co-firing bound gets told to delete work it is allowed to have.
     ["R9c", "R9g"]),

    # --------------------------------------------------- the pairing door (R10)
    ("M16 the pairing check dropped from the compatibility door",
     "wrl_scenario.py",
     "    check_route_writer_reservation(scenario, artifact)\n"
     "    check_epoch_batch_capacity(scenario, artifact)",
     "    check_route_writer_reservation(scenario, artifact)",
     # The check still exists and is still correct -- R10b calls it by name and
     # stays green. Only the row that goes through the door production uses can
     # see that the door stopped asking.
     ["R10d"]),

    ("M17 @noop the pairing check's scope guard removed",
     "wrl_scenario.py",
     "    if not WC.routes_of_artifact(artifact):\n"
     "        return scenario                   # the rule does not apply",
     "    if False:\n"
     "        return scenario                   # the rule does not apply",
     # Recorded as a NO-OP because that is what it measured. The guard reads
     # like a behaviour gate and is not one: a route-free world contributes 0
     # to every epoch's route count, so running the check anyway refuses
     # nothing it would not otherwise refuse. It is an assertion of SCOPE
     # ("this rule is about routes") plus a saved `scenario_to_script`, and
     # scope is not something a battery row can observe. Predicting R10e was a
     # harness error; R10e says a route-free pairing still passes, and under
     # this mutant it still does.
     "@noop:the scope guard is behaviourally inert -- see the comment"),

    ("M18 the capacity refusal counts only the AUTHORED half",
     "wrl_fold.py",
     "        if authored + routed > MAX_BATCH:",
     "        if authored > MAX_BATCH:",
     # The refusal survives, and refuses nothing it did not already refuse:
     # `validate_scenario_v1` already bounds the authored half. A door that
     # only re-asks a question another validator already answered.
     ["R10b"]),

    ("M19 the census forgets epochs the run never reaches",
     "wrl_fold.py",
     "    for epoch, claims in by.items():\n"
     "        census.setdefault(epoch, (0, len(claims)))",
     "    pass",
     # D3 says a short run is a run input, not a defect -- but "did not fire"
     # still has to be VISIBLE, or a route that silently never fires and a
     # route that fires past the end of the run look the same from the census.
     ["R8c"]),

    ("M20 `_assert_capacity` deleted from the merge",
     "wrl_fold.py",
     "        _assert_capacity(epoch0 + i, merged)",
     "        pass",
     # The last line of defence, below the seal and below the pairing door: a
     # caller that assembles batches itself still cannot hand `admit_step` a
     # batch it will assert on. It SURVIVED first time round -- every R10 row
     # went through the scenario door, and the door calls
     # `FD.check_epoch_batch_capacity`, which does its own arithmetic and never
     # reaches `_assert_capacity` at all. R10g/R10h are the rows that do.
     ["R10g"]),
]


def main():
    return run("binding_run49.py", MUTATIONS, prefix="R")


if __name__ == "__main__":
    sys.exit(main())
