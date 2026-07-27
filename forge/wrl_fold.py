"""wrl_fold.py -- Slice B commit 4: the ONE place a world's static routes become
runtime claims.

Commits 2 and 3 gave `~~` a canonical form, an identity, a locator and a ruled
spelling. Through all of that a route did nothing: it was carried, sealed,
formatted, refused for every reason it should be -- and provably ignored at
runtime. This module is where it stops being ignored.

WHAT A ROUTE IS AT RUNTIME
--------------------------
A route is a STATIC, WORLD-GENERATED, ONE-SHOT `Send`. It is not an edge (D8: a
mailbox is never wired) and it is not a scenario claim (D3: run inputs are not
world identity). Its runtime image is exactly one ADMIT claim envelope:

    mk_claim(ROUTE_WRITER_ID, sequence, ("Send", mailbox_id, body))

observed in the batch of the epoch its source Pulser fires. `sequence` is the
route's zero-based canonical RouteKey ordinal (ruling Q4) and comes from
`WC.route_claim_identity`, never from a second numbering here.

WHY THIS IS ITS OWN MODULE
--------------------------
There are TWO batch producers in the tree -- `LoweredProgram.epoch_inputs` (the
legacy inline claim syntax that L-0 batteries fold) and
`wrl_scenario.scenario_to_script` (the ScenarioV1 document the bench runs). If
each grew its own injection the two would answer "what does this world send?"
differently, and the difference would only ever be visible in a film. So the
injection is written once, over the one shape both reduce to -- an ordered list
of batches -- and both producers call it.

It is also why this is NOT in `wrl_canonical`: the fold needs `admit`, and the
identity spine imports nothing but the standard library so that it stays
portable (it has a verified browser port). `wrl_fold` sits above both.

WHAT ELSE LIVES HERE
--------------------
The declared-policy seam (`admit_policy_of` / `film_mailboxes` /
`runtime_seams`). It landed in commit 4 because building the first film of a
firing route exposed it, and it is the same defect one layer down: a sealed
world declares an acceptance policy and a film schema, and nothing read them.
The long comment above those functions has the measurement.

WHAT THIS MODULE DOES NOT DO
----------------------------
It does not decide legality. A world whose routes overrun one epoch's batch is
refused at SEAL time (`WRL_ROUTE_BATCH_OVERFLOW`); a world+scenario PAIRING that
overruns it is refused by `check_epoch_batch_capacity` below, before anything
runs. By the time a batch reaches `admit_step` the bound is already known to
hold. `_assert_capacity` is a belt-and-braces restatement, and it is deliberately
a typed refusal rather than the reducer's bare AssertionError.
"""
import collections as _collections

import wrl_canonical as WC
from admit import mk_claim, mailboxes_of, MAX_BATCH


# The one-shot fold's frozen ADMIT operation. Named so that the day a recurring
# route lands (`forge.world.async.v1`, deferred by ruling Q3) the grep for "what
# does a route emit" has exactly one hit.
ROUTE_OPERATION = "Send"


# ---------------------------------------------------------------------------
# THE DECLARED-POLICY SEAM
#
# Found while building commit 4's first film, and it is the same defect as the
# route itself one layer down. A sealed world CARRIES its acceptance policy and
# its film schema:
#
#     semantic_policies = {..., "admit_policy_id": "admit_mailbox_deliver_all_v1",
#                               "film_schema_id":  "film.v0.7.mailbox.v1"}
#
# and until now NOTHING READ THEM. `admit_step`'s `policy_id` defaults to the
# mailbox-FREE `admit_candidate_min_firstreceipt_v1`, and `film_bytes_v7`'s
# `mailboxes` argument defaults to None, so every fold harness in the tree was
# running a mailbox-bearing world under a reducer that does not know what a
# mailbox is and rendering it with a projection that cannot show one.
#
# That is not a cosmetic loss. Measured on the first route-bearing world:
#
#   under the DEFAULT policy   claim ... payload=Send:#?:0.0.0.7
#                              (no admit_mailbox line, no mailbox line, no ledger)
#   under the DECLARED policy  claim ... payload=Send:mb:0.0.0.7
#                              ledger:MailboxEnqueue,mailbox=mb,epoch=1
#                              ledger:MailboxDeliver,mailbox=mb,epoch=2
#
# So the default reading loses the route's ENTIRE effect and, worse, renders the
# target as `#?` -- Film v0.7's INVALID_TARGET -- because a world with no
# declared mailboxes has no declared `mb`. A film that says the route addressed
# a target that does not exist is not a partial answer, it is a wrong one.
#
# Commit 4 is the commit that makes a route do something, so it is the commit
# that has to make the world's own policies reach the runtime. The seam lives
# HERE for the reason the claim fold does: two batch producers means two places
# to forget, and forgetting is exactly what happened.
# ---------------------------------------------------------------------------
def admit_policy_of(artifact):
    """The acceptance policy a SEALED world DECLARES, for `admit_step`.

    Read from the artifact rather than re-derived from its roles, because the
    seal already pinned it: `semantic_surface_for_roles` chose it at lowering
    time and it is inside the SemanticArtifactID. Re-deriving here would fork
    that choice, and the fork would be invisible until the two disagreed.

    Total over the two SEALED carriers of that field: the artifact mapping
    itself, and the lowered plan view that the backend executes (which carries
    `admit_policy_id` as an attribute, having taken it from the same seal).
    Both are the seal; neither is a caller option. Accepting only the first
    would have forced the bench to spell the lookup a second way, which is the
    fork this function exists to prevent."""
    if isinstance(artifact, dict):
        return (artifact.get("semantic_policies") or {}).get("admit_policy_id")
    return getattr(artifact, "admit_policy_id", None)


def film_schema_of(artifact):
    """The film schema a SEALED world DECLARES. Not consumed by
    `film_bytes_v7` (which has one shape and gates the mailbox block on its
    `mailboxes` argument), so it is exposed to be ASSERTED against: a world
    claiming `film.v0.7.mailbox.v1` whose fixture has no mailbox is a lowering
    defect, and the only way to notice is to compare the two."""
    return (artifact.get("semantic_policies") or {}).get("film_schema_id")


def film_mailboxes(fx):
    """`film_bytes_v7`'s `mailboxes` argument: `[(id, width, capacity), ...]`.

    One spelling. This was hand-rolled in binding_run43 as `mb_records`, and a
    second hand-rolling here is how the film's mailbox block and the reducer's
    mailbox table drift apart. An EMPTY list is deliberate and load-bearing:
    `film_bytes_v7` gates its whole mailbox block on `if mailboxes:`, so a
    route-free, mailbox-free world passing `[]` renders byte-identically to one
    passing nothing -- which is what makes this safe to call unconditionally."""
    return [(m, w, c) for m, (w, c) in sorted(mailboxes_of(fx).items())]


class RuntimeSeamsV1(_collections.namedtuple(
        "RuntimeSeamsV1", "admit_policy_id film_mailboxes accept_rule")):
    """What a SEALED world declares, as one value.

    A `namedtuple` on purpose, twice over. First, every existing caller
    unpacks the 3-tuple `runtime_seams` used to return, and this keeps all of
    them working unchanged -- the split below moved a parameter, not a
    trajectory. Second, it makes the production seam's precondition
    expressible as a type: `admit_step_sealed` requires an instance, and the
    only function that builds one is `runtime_seams`, which requires a sealed
    artifact.

    That is the whole enforcement mechanism for Core 0.2.1 §8c, and it is
    deliberately structural rather than defensive. There is no branding, no
    registry and no attempt to prove provenance -- a caller determined to
    forge one can (the C.4 lesson: a serializer does not *prove* provenance).
    What it does is make the honest path the shortest one and the dishonest
    path visible at the call site, which is what a greppable seam buys."""
    __slots__ = ()


def runtime_seams(artifact, fx):
    """`(admit_policy_id, film_mailboxes, accept_rule)` -- the arguments a fold
    needs to honour what a world declared, fetched together so a caller cannot
    honour one and forget the other. That is not hypothetical: every harness in
    the tree forgot the first two, and each of them alone still produces a
    plausible film.

    The third (commit 5c) is the SAME sealed field as the first, read for the
    OTHER runtime: `admit_policy_id` tells GOLDEN which seam-1 table to
    dispatch through, and `accept_rule` tells the IC LOWERING which seam-1 rule
    to emit. They are returned by one call because they are one declaration,
    and because the defect this closes was exactly a runtime honouring the
    declared policy on one side while the other applied an older rule -- a
    sealed world whose golden refused an equivocal event key while its
    reduction minted a receipt and delivered the message anyway.

    It is derived from the sealed `admit_policy_id` and from nothing else. Not
    from the proof profile (`admit_ic.profile_for_artifact`, which keys on
    ROUTES), not from mailbox presence, not from `mcap`, not from whether the
    world contains a `Send`, and not from a caller-supplied option. All of
    those CORRELATE with the policy in today's two worlds; the proof profile
    and the acceptance policy are separate semantic axes, and every one of
    those shortcuts would be wrong the first time a world declared the other
    combination."""
    # Lazy: `admit_ic` is the IC lowering and imports this module back (for
    # `admit_policy_of`, from `accept_rule_for_artifact`). The cycle is real,
    # and deferring the edge to call time is what keeps either importable
    # first.
    import admit_ic as X
    pid = admit_policy_of(artifact)
    return RuntimeSeamsV1(pid, film_mailboxes(fx),
                          X.accept_rule_for_policy(pid))


# ---------------------------------------------------------------------------
# THE PRODUCTION WORLD-EXECUTION SEAM (Slice B commit 5d; Core 0.2.1 §8c)
#
# §8 consequence 1 froze that the acceptance policy is read from the seal "and
# never from a caller-supplied option". Through 0.2.0 that was true of every
# call site and false of the API: `admit_step` still took `policy_id`, so the
# ordinary reducer entry point contradicted the freeze it was supposed to
# implement. The functions below are the seam that makes the statement
# enforceable instead of merely observed.
#
# The shape of the fix is worth stating because it is not "delete the
# parameter". Deleting it would have removed the illegitimate user (application
# code running a world under semantics it did not seal) together with the
# legitimate one (a battery asserting a law about the POLICY TABLE, which by
# construction must reach world/policy pairings no seal can express). What
# distinguishes them is not the value passed but WHERE IT CAME FROM, so the
# split is by provenance: production takes a `RuntimeSeamsV1` that only a
# sealed artifact can produce, conformance takes a bare string through a
# function whose name says so (`admit.admit_policy_probe`).
# ---------------------------------------------------------------------------
def admit_step_sealed(state, batch, epoch, fx, seams):
    """One ADMIT reduction under the policy a world SEALED.

    `seams` must be a `RuntimeSeamsV1` -- the policy arrives attached to the
    world that declared it, so it cannot be substituted at the call site
    without first constructing a different world."""
    if not isinstance(seams, RuntimeSeamsV1):
        WC._fail(WC.WRL_UNSEALED_POLICY,
                 "admit_step_sealed requires a RuntimeSeamsV1 built by "
                 "runtime_seams(artifact, fx); got %r. A bare policy id is a "
                 "conformance probe (admit.admit_policy_probe), not a world "
                 "execution." % (type(seams).__name__,))
    import admit as AD
    return AD._admit_step_with_policy(state, batch, epoch, fx,
                                      seams.admit_policy_id)


def film_sealed(seams, *film_args, **kw):
    """Film v0.7 rendered with BOTH halves of what the world declared.

    The mailbox table and the policy label come from the same `seams` value
    that drove the reduction, which is what makes the film's `admit:policy=`
    line a report of the seam that produced the receipts below it rather than
    an independently computed guess. 5c measured what happens when they are
    computed from different expressions: they are free to disagree, and they
    did, for the whole 0.1.x line."""
    import admit as AD
    kw.setdefault("mailboxes", seams.film_mailboxes)
    kw.setdefault("policy_id", seams.admit_policy_id)
    return AD.film_bytes_v7(*film_args, **kw)


def verify_replay_policy(artifact, recorded_policy_id):
    """Refuse a ReplayBundle whose recorded policy is not the world's seal.

    §8b made `policy_ids` load-bearing: it is the only serialization of the
    seam a trajectory ran under, so a bundle carrying the wrong one cannot
    reproduce its own frames. This is the check that makes the record mean
    something. Returns the verified policy id so a caller can use the result
    of the check rather than re-reading the field it just validated -- the
    same reason `route_claim_identity` returns the mapping it computed."""
    sealed = admit_policy_of(artifact)
    if recorded_policy_id != sealed:
        WC._fail(WC.WRL_REPLAY_POLICY_MISMATCH,
                 "replay records acceptance policy %r but the initial "
                 "artifact seals %r; the bundle's frames were not produced "
                 "by the policy it carries" % (recorded_policy_id, sealed),
                 field_path="policy_ids.admit_policy_id")
    return sealed


def fold_world(artifact, fx, batches, epoch0=1, reducer=None):
    """Execute a SEALED world and return one Film v0.7 per epoch.

    This is the production path named in Core 0.2.1 §8c:

        fold_world(artifact, ...)
          -> RuntimeSeamsV1 derived from the artifact
          -> admit reduction
          -> film

    There is deliberately NO policy parameter. A world runs under the policy
    its own artifact seals, or it does not run. Changing the semantics a world
    executes under therefore requires changing the world, which moves its
    `SemanticArtifactID` -- acceptance semantics are reachable only through
    identity (§8c consequence 1).

    `reducer` is injected rather than imported at module scope for the reason
    `JobRegistry.execute` is: it is the one substitutable part (reference vs
    native), and a battery that wants to prove the two agree needs to supply
    both to the SAME fold. Defaulting it to the reference reducer keeps the
    ordinary call one argument shorter without hiding the seam.

    The heavy imports are function-local. `wrl_fold` is imported by the
    lowering path, and the compiler/runtime are not needed to fold a batch --
    paying for them at import time would put the whole backend behind every
    `admit_policy_of` call."""
    import compiler as C
    import forge_runtime as O
    from forge_state import init_state_v6, state_to_film_args_v6
    reduce_ = O.ref_reduce if reducer is None else reducer
    import admit as AD

    seams = runtime_seams(artifact, fx)
    claim = AD.init_claimstate(fx)
    wstate = init_state_v6(fx)
    step, _ = C.compile_step_v6(fx)
    films = []
    for e, batch in enumerate(batches):
        epoch = epoch0 + e
        claim, cfg, resets = admit_step_sealed(claim, batch, epoch, fx, seams)
        ec = C.enc_config_bundle(fx, cfg, resets)
        wstate = C.dec_state_v6(fx, reduce_("((%s %s) %s)"
                                            % (step, ec,
                                               C.enc_state_v6(fx, wstate))))
        films.append(film_sealed(seams,
                                 *state_to_film_args_v6(fx, wstate, epoch),
                                 state=claim))
    return films


def route_claims(artifact):
    """`[(epoch, envelope), ...]` -- a world's routes as runtime claims.

    Ordered by (epoch, sequence), which is canonical: `sequence` IS the
    canonical RouteKey ordinal, so this ordering is derived from the artifact's
    identity rather than from the order routes happen to be stored in. ADMIT is
    order-independent within a batch, so this fixes the digest, not the effect.
    """
    routes = WC.routes_of_artifact(artifact)
    if not routes:
        # Not merely "none found": a route-free world HAS no runtime image to
        # fold, and every world shipped before Slice B is route-free. The early
        # return keeps them off this path entirely -- and is the reason a
        # route-free fold is byte-identical to the pre-Slice-B fold rather than
        # merely equal to it.
        return []
    ident = WC.route_claim_identity(routes)
    cfg = {o["object_id"]: (o.get("static_config") or {})
           for o in artifact["objects"]}
    out = []
    for r in routes:
        key = WC.route_key(r)
        writer, sequence = ident[key]
        epoch = WC.once_epoch(cfg[key.source_id].get("clock"))
        if epoch is None:
            # Unreachable through the seal, which refuses a non-`once` source.
            # Stated anyway, and stated as a typed refusal, because the failure
            # it guards is "a route silently stopped firing".
            WC._fail(WC.WRL_ILLEGAL_ROUTE_ENDPOINT,
                     "route %s has a source that is not `once`; a sealed world "
                     "cannot reach here" % key.render(), primary_locator=key)
        payload = (ROUTE_OPERATION, key.mailbox_id, tuple(r["body"]))
        out.append((epoch, sequence, mk_claim(writer, sequence, payload)))
    out.sort(key=lambda t: (t[0], t[1]))
    return [(e, c) for e, _s, c in out]


def route_claims_by_epoch(artifact):
    """`{epoch: [envelope, ...]}`, canonically ordered within each epoch."""
    by = {}
    for epoch, claim in route_claims(artifact):
        by.setdefault(epoch, []).append(claim)
    return by


def _assert_capacity(epoch, batch):
    if len(batch) > MAX_BATCH:
        WC._fail(WC.WRL_EPOCH_BATCH_OVERFLOW,
                 "epoch %s would observe %d claims; one batch holds %d"
                 % (epoch, len(batch), MAX_BATCH))


def fold_batches(artifact, batches, epoch0=1):
    """Merge a world's route claims into an ordered list of claim batches.

    `batches[i]` is observed at epoch `epoch0 + i` -- the same numbering
    `LoweredProgram.run_plan["epoch0"]` carries and the same one the admit
    driver folds. Returns a NEW list; the input is not mutated.

    A route whose epoch lies past the end of the run simply does not fire, and
    that is NOT an error: run length is a RUN INPUT (D3), not world structure,
    so a three-epoch run of a world whose route fires at epoch 5 is a short run,
    not a broken world. Refusing it here would make the world's legality depend
    on a document that is deliberately not part of its identity.
    """
    by = route_claims_by_epoch(artifact)
    out = []
    for i, batch in enumerate(batches):
        merged = list(batch) + by.get(epoch0 + i, [])
        _assert_capacity(epoch0 + i, merged)
        out.append(merged)
    return out


def fold_script(artifact, script, epoch0=1):
    """`fold_batches` over the `[(label, batch), ...]` shape the ADMIT driver
    folds. Labels are untouched: a label is documentation, and a route firing
    is not something the scenario's author wrote."""
    batches = fold_batches(artifact, [b for _lbl, b in script], epoch0)
    return [(lbl, batches[i]) for i, (lbl, _b) in enumerate(script)]


def epoch_batch_census(artifact, batches, epoch0=1):
    """`{epoch: (n_authored, n_route)}` for every epoch either side contributes
    to. The evidence a capacity refusal is built from, exposed separately so a
    diagnostic can say WHICH half is large rather than only that the sum is."""
    by = route_claims_by_epoch(artifact)
    census = {}
    for i, batch in enumerate(batches):
        census[epoch0 + i] = (len(batch), len(by.get(epoch0 + i, ())))
    for epoch, claims in by.items():
        census.setdefault(epoch, (0, len(claims)))
    return census


def check_epoch_batch_capacity(artifact, batches, epoch0=1):
    """Refuse a world+run-inputs PAIRING whose combined per-epoch observation
    overruns `admit.MAX_BATCH`.

    Both documents can be individually legal and still not fit: the seal bounds
    a world's co-firing routes and `validate_scenario_v1` bounds a scenario's
    per-epoch claims, each against the SAME batch, so four of each is two legal
    documents and eight claims. Neither document is at fault, which is why this
    is a compatibility check with its own code and not a narrowing of either
    validator -- the same shape as the Q4 writer reservation.

    Epochs the run never reaches are ignored, for the reason `fold_batches`
    gives: a short run is a run input, not a defect.
    """
    census = epoch_batch_census(artifact, batches, epoch0)
    for epoch in sorted(census):
        if epoch >= epoch0 + len(batches):
            continue
        authored, routed = census[epoch]
        if authored + routed > MAX_BATCH:
            WC._fail(WC.WRL_EPOCH_BATCH_OVERFLOW,
                     "epoch %d observes %d authored claim(s) plus %d route "
                     "claim(s) = %d; one observation batch holds %d. Neither "
                     "document is over its own bound -- move a claim to "
                     "another epoch, or fire a route on another one."
                     % (epoch, authored, routed, authored + routed, MAX_BATCH),
                     field_path="epochs[%d].claims" % epoch)
    return batches
