#!/usr/bin/env python3
"""binding_run49.py -- Slice B, Commit 4: the runtime fold.

Commits 2 and 3 gave `~~` a canonical form, an identity, a locator and a ruled
spelling, and every battery row for both closed with the same admission: a route
is carried, sealed, formatted, refused for every reason it should be -- and
PROVABLY IGNORED at runtime. This battery is where that stops being true.

    R1   a route's runtime image is exactly ONE ADMIT claim
    R2   ... observed in the epoch its source Pulser fires, and only there
    R3   the fold is canonically ordered and does not mutate its input
    R4   BOTH batch producers fold identically -- one seam, not two
    R5   the EXPLICIT TWIN: a fired route == the same claim written by hand
    R6   a route DOES something: enqueue at the firing epoch, deliver at the
         next boundary (D7)
    R7   the declared-policy seam -- and what the default reading LOSES
    R8   a short run is a run input (D3), not a broken world
    R9   the seal refuses routes that co-fire past one observation batch
    R10  the pairing door refuses two individually-legal documents that do
    R11  route-free worlds are still byte-identical
    R12  the IC boundary, MEASURED: the world half crosses, the claim half does not
    R13  the frozen demo world still folds ic_ref == ic32 == golden

R7 and R12 are not in the ruling. R7 is a defect this commit found while
rendering its first film: a sealed world DECLARES its acceptance policy and film
schema and nothing in the tree read them, so a mailbox-bearing world was being
folded by a reducer that does not know what a mailbox is. R12 is the reason this
battery cannot close natively, and it is stated as a measurement rather than an
excuse -- see the module note at the bottom.

Run:  python3 binding_run49.py      (TRVM_SKIP_NATIVE=1 for reference only)
"""
import copy
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import admit as AD
import admit_ic as X
import compiler as C
import wrl_canonical as WC
import wrl_fold as FD
import wrl_ir as W
import wrl_scenario as SC
import binding_run3o as O
import binding_run5 as B5
import binding_run47 as B47
from admit import film_bytes_v7, mk_claim
from forge_state import init_state_v6, state_to_film_args_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

# commit 2/3's fixtures, reused rather than re-spelled. A third hand-rolled
# `HEAD`/`TAIL` here would be the forked vocabulary this slice keeps finding.
world, world2, MB1, MB2, route, spread = (
    B47.world, B47.world2, B47.MB1, B47.MB2, B47.route, B47.spread)
lower, sem = B47.lower, B47.sem

_FAILED = []


def rep(ok, label):
    if callable(ok):
        try:
            ok = bool(ok())
        except WC.WrlValidationError as ex:
            print("  [FAIL] %s\n         (raised %s)" % (label, ex))
            _FAILED.append(label)
            return
    print("  [%s] %s" % ("PASS" if ok else "FAIL", label))
    if not ok:
        _FAILED.append(label)


def _raised(fn):
    try:
        fn()
    except WC.WrlValidationError as ex:
        return ex
    return None


def _typed(fn, code):
    ex = _raised(fn)
    return ex is not None and ex.code == code


# --------------------------------------------------------------- the driver
_DECLARED = object()          # "read it off the artifact" sentinel


def gfilms(artifact, fx, batches, epoch0=1, policy=_DECLARED,
           mailboxes=_DECLARED):
    """Fold `batches` and return one Film v0.7 per epoch.

    GOLDEN ONLY, deliberately. `binding_run3o._golden_traj` would be the shared
    spelling, but it also projects each epoch's claim state into IC ClaimFactKeys
    -- that projection is its COMPARISON SURFACE against the reduced profile, and
    the reduced profile is precisely what a `Send` cannot cross (R12). Borrowing
    it here would make every row in this battery die inside a diagnostic that has
    nothing to do with what the row is asserting.

    `policy` and `mailboxes` default to what the WORLD DECLARED. They are
    parameters and not constants so that R7 can fold the same world both ways and
    show what the old default reading was silently losing."""
    # Core 0.2.1 §8c: WHICH SEAM this fold uses is decided here, and it is
    # decided by the PROVENANCE of the policy rather than by its value. Left at
    # the default, the fold is a WORLD EXECUTION and runs through the sealed
    # seam; given an explicit policy it is a CONFORMANCE PROBE and runs through
    # the probe. Both paths must be reachable from one function, because R7's
    # whole content is folding ONE world both ways -- a comparison that cannot
    # be written is not a weaker check, it is no check.
    #
    # There are THREE cases here and not two, which is a correction: the first
    # cut of this dispatch read "declared or probe" and sent R7/R11 -- which
    # pass `policy=None` on purpose, to fold a mailbox world under the FROZEN
    # policy -- into `admit_policy_probe`, whose whole contract is that it
    # refuses `None`. `None` is not an under-specified probe. It NAMES the
    # frozen default, and the entry point that means exactly that is
    # `admit_step`. Collapsing "no policy named" into "some policy named"
    # loses the distinction §8c is built on.
    sealed = policy is _DECLARED and mailboxes is _DECLARED
    seams = FD.runtime_seams(artifact, fx) if sealed else None
    if policy is _DECLARED:
        policy = FD.admit_policy_of(artifact)
    if mailboxes is _DECLARED:
        mailboxes = FD.film_mailboxes(fx)
    claim = AD.init_claimstate(fx)
    wstate = init_state_v6(fx)
    step, _ = C.compile_step_v6(fx)
    out = []
    for e, batch in enumerate(batches):
        if sealed:
            claim, cfg, resets = FD.admit_step_sealed(claim, batch,
                                                      epoch0 + e, fx, seams)
        elif policy is None:
            claim, cfg, resets = AD.admit_step(claim, batch, epoch0 + e, fx)
        else:
            claim, cfg, resets = AD.admit_policy_probe(claim, batch,
                                                       epoch0 + e, fx, policy)
        ec = C.enc_config_bundle(fx, cfg, resets)
        wstate = C.dec_state_v6(fx, O.norm("((%s %s) %s)"
                                           % (step, ec,
                                              C.enc_state_v6(fx, wstate))))
        # `policy` feeds BOTH the step and the film label, from one local. That
        # is the point of the Core 0.2.0 change: `admit:policy=` reports the
        # seam that produced the receipts below it, and a label computed from a
        # different expression than the reduction is free to disagree with it.
        # Sharing the variable makes disagreement unspellable rather than
        # merely unlikely. `policy=None` stays the frozen default on both.
        out.append(film_bytes_v7(*state_to_film_args_v6(fx, wstate, epoch0 + e),
                                 state=claim, mailboxes=mailboxes,
                                 policy_id=policy))
    return out


def run(src, routes=(), k=3, **kw):
    """Lower `src` (+ routes), fold k epochs of EMPTY authored batches with the
    world's routes injected, and return (lowered, fixture, batches, films)."""
    lp = lower(src, routes)
    fx = W.ir_to_fixture(lp.artifact)
    batches = FD.fold_batches(lp.artifact, [[] for _ in range(k)])
    return lp, fx, batches, gfilms(lp.artifact, fx, batches, **kw)


def _lines(film, *keys):
    return [ln for ln in film.decode().split("\n")
            if any(k in ln for k in keys)]


# ------------------------------------------------------------------- R1
def r1_runtime_image():
    """A route's runtime image is exactly one ADMIT claim envelope.

    Not one-and-a-bit: the row checks the whole envelope, because the parts that
    are NOT checked are the parts that drift. `writer_id` is the Q4 reservation,
    `sequence` is the canonical RouteKey ordinal (and must come from
    `route_claim_identity`, not from a second numbering inside the fold), the
    payload is D9's `Send` triple, and the digest is `admit`'s own."""
    lp = lower(world(MB1), [route()])
    claims = FD.route_claims(lp.artifact)
    rep(len(claims) == 1, "R1) one declared route mints exactly ONE claim")
    if not claims:
        return
    epoch, env = claims[0]
    want = mk_claim(WC.ROUTE_WRITER_ID, 0, ("Send", "mb", (0, 0, 0, 7)))
    rep(env == want,
        "R1b) ... and it is EXACTLY mk_claim(%d, 0, (Send, mb, 0.0.0.7)) -- "
        "writer, sequence, payload AND digest, not merely a claim that looks "
        "similar" % WC.ROUTE_WRITER_ID)

    # The sequence must be the CANONICAL ordinal, which is only visible when
    # authoring order and canonical order disagree.
    #
    # The bodies are DISTINCT on purpose. A route's claim carries ("Send",
    # mailbox, body) and NOT its tag, so a check that only compares the
    # multiset of sequences -- which is what this row did until `mutate49`'s
    # M7 walked straight through it -- cannot tell canonical numbering from
    # storage-order numbering: both mint {0, 1}. Distinct bodies are what let
    # each claim be attributed back to the route that minted it.
    rs = [route(tag="zz", body=(0, 0, 0, 1)),
          route(tag="aa", body=(0, 0, 0, 2))]
    art = lower(world(MB1), rs).artifact
    ident = WC.route_claim_identity(WC.routes_of_artifact(art))
    want_seq = {k.route_tag: s for k, (_w, s) in ident.items()}
    body_tag = {tuple(r["body"]): r["route_tag"] for r in rs}
    got_seq = {body_tag[c["payload"][2]]: c["sequence"]
               for _e, c in FD.route_claims(art)}
    rep(want_seq == {"aa": 0, "zz": 1} and got_seq == want_seq,
        "R1c) `sequence` is the CANONICAL RouteKey ordinal PER ROUTE (aa=0 "
        "though it was authored second), taken from `route_claim_identity` "
        "rather than renumbered here -- one numbering, not two")

    rep(FD.ROUTE_OPERATION == "Send" and AD.payload_key(
        W.ir_to_fixture(lp.artifact), want["payload"])[0] == 2,
        "R1d) the operation is D9's `Send` (payload tag 2), the tag Slice A "
        "already froze -- commit 4 adds no runtime construct")

    # R1c is necessary and NOT sufficient, and `mutate49`'s M7 is what proved
    # it. Replacing `route_claim_identity(routes)` with a bare
    # `enumerate(routes)` -- numbering by STORAGE position instead of by key --
    # survived every row above, because canonicalization ALREADY sorts
    # `async_routes` into RouteKey order before sealing. On a sealed artifact
    # the two numberings agree by construction, so authoring order alone can
    # never separate them: `lower()` has re-sorted the list before the fold
    # ever sees it.
    #
    # So the discriminating input is one the seal does not produce. The
    # artifact below is canonical in every respect EXCEPT that its route list
    # has been reversed out of canonical order after the fact. A fold that
    # numbers by key is unmoved by that; a fold that numbers by position swaps
    # aa and zz. This is the only row in the file that hands a consumer an
    # artifact the seal would not have minted, and it does so deliberately:
    # the claim being measured is "the numbering is derived from the KEY", and
    # that claim is unobservable on inputs where key order and list order are
    # the same thing.
    scrambled = copy.deepcopy(art)
    scrambled["async_routes"] = list(reversed(scrambled["async_routes"]))
    stored = [r["route_tag"] for r in scrambled["async_routes"]]
    scr_seq = {body_tag[c["payload"][2]]: c["sequence"]
               for _e, c in FD.route_claims(scrambled)}
    rep(stored == ["zz", "aa"] and scr_seq == want_seq,
        "R1e) reversing a sealed world's stored route list (now %s) moves NO "
        "sequence -- the ordinal comes from the RouteKey, not from the list "
        "position, which is exactly what canonical storage order hides"
        % (stored,))

    scr_order = [c["sequence"] for _e, c in FD.route_claims(scrambled)]
    rep(scr_order == sorted(scr_order),
        "R1f) ... and the emitted claims are STILL canonically ordered, so "
        "the fold's output does not inherit the disorder of its input")


# ------------------------------------------------------------------- R2
def r2_fires_at_its_epoch():
    """The claim is observed in the epoch its source Pulser fires -- and in no
    other. A route that fires in every epoch is a recurring channel, which is
    the thing ruling Q3 deferred; a route that fires in none is the status quo
    ante. Both failures look like "it works" from a single-epoch test."""
    lp = lower(world2(MB1), [route(src="p0", tag="a"),
                             route(src="p1", tag="b")])
    by = FD.route_claims_by_epoch(lp.artifact)
    rep(sorted(by) == [1, 2] and len(by[1]) == 1 and len(by[2]) == 1,
        "R2) two routes on two `once` Pulsers land in epochs {1: 1 claim, "
        "2: 1 claim} -- the firing epoch is the SOURCE's, not the fold's")

    batches = FD.fold_batches(lp.artifact, [[] for _ in range(4)])
    rep([len(b) for b in batches] == [1, 1, 0, 0],
        "R2b) ... and each is a ONE-SHOT: epochs 3 and 4 observe nothing, so "
        "the route is not silently recurring (ruling Q3)")

    # The firing epoch must come from the SAME accessor the seal's co-firing
    # tally uses, or the two can disagree about which batch a route joins.
    rep(WC.once_epoch(("once", 2)) == 2 and WC.once_epoch(("periodic", 1, 0))
        is None and WC.once_epoch(["once", 2]) == 2,
        "R2c) `once_epoch` is the ONE spelling of \"when does this fire\" -- "
        "shared by the seal and the fold, and tolerant of the JSON round-trip")


# ------------------------------------------------------------------- R3
def r3_order_and_purity():
    """The fold is canonically ordered and returns a NEW list.

    ADMIT is order-independent within a batch, so ordering here fixes the
    DIGEST, not the effect -- which is exactly why it has to be checked: an
    ordering defect is invisible in every film and shows up only in an id."""
    rs = [route(tag="z"), route(tag="a"), route(tag="m")]
    lp = lower(world(MB1), rs)
    seq = [c["sequence"] for _e, c in FD.route_claims(lp.artifact)]
    rep(seq == sorted(seq),
        "R3) route claims come out in (epoch, sequence) order, which is "
        "derived from the artifact's IDENTITY rather than from storage order")

    # ... and EPOCH is the primary key, which the row above cannot see: a
    # sealed artifact already stores its routes in canonical RouteKey order, so
    # for any single-epoch world the sort is a no-op and deleting it changes
    # nothing (`mutate49` M8 measured exactly that). It becomes load-bearing
    # only where canonical order and epoch order DISAGREE -- so this builds
    # that world: p0 fires SECOND, so the route that sorts first fires last.
    late = world(MB1).replace("[pulser:p0](mode=once, epoch=1){sig_out}\n",
                              "[pulser:p0](mode=once, epoch=2){sig_out}\n"
                              "[pulser:p2](mode=once, epoch=1){sig_out}\n")
    lp2 = lower(late, [route(src="p0", tag="a"), route(src="p2", tag="b")])
    pairs = [(e, c["sequence"]) for e, c in FD.route_claims(lp2.artifact)]
    rep(pairs == [(1, 1), (2, 0)],
        "R3b) ... and EPOCH outranks sequence: the route with canonical "
        "sequence 0 fires at epoch 2, so a correct fold emits (1,1) before "
        "(2,0) -- ordering by sequence alone would invert them")

    authored = [[mk_claim(1, 1, ("ResetFault", "ob"))], []]
    before = copy.deepcopy(authored)
    merged = FD.fold_batches(lp.artifact, authored)
    rep(authored == before and merged is not authored
        and merged[0] is not authored[0],
        "R3c) ... and `fold_batches` MUTATES NOTHING: the caller's batches are "
        "byte-equal afterwards, and no inner list is shared")
    rep(len(merged[0]) == 4 and merged[0][0] == authored[0][0],
        "R3d) ... authored claims keep their place and the routes are appended "
        "-- 1 authored + 3 routed = 4")

    # A route-FREE world must take the early return, not merely produce an
    # empty result: that is what makes a route-free fold byte-identical to the
    # pre-Slice-B fold rather than only equal to it.
    rf = lower(world(MB1)).artifact
    rep(FD.route_claims(rf) == [] and FD.route_claims_by_epoch(rf) == {}
        and FD.fold_batches(rf, authored) == authored,
        "R3e) a route-free world folds to its input EXACTLY -- every world "
        "shipped before Slice B stays on the path it was on")


# ------------------------------------------------------------------- R4
def r4_one_seam():
    """BOTH batch producers fold identically.

    `LoweredProgram.epoch_inputs` (the legacy inline claim syntax the L-0
    batteries use) and `wrl_scenario.scenario_to_script` (the ScenarioV1
    document the bench runs) are two answers to "what does this world observe".
    If each grew its own injection they would eventually disagree, and the
    disagreement would only ever be visible in a film. This row is the reason
    `wrl_fold` is a module and not two copies of a loop."""
    # THREE co-firing routes, not one. With a single route every plausible
    # second injection -- including one that truncates an epoch to its first
    # claim -- agrees with the real fold by coincidence, which is how
    # `mutate49`'s M10 survived this row's first spelling. A co-firing epoch is
    # the smallest world in which "both producers inject" and "both producers
    # inject EVERYTHING" are different statements.
    lp = lower(world(MB1), spread(3, first=99))
    scen = SC.demo_scenario(lp.semantic_artifact_id)
    _faults, script = SC.scenario_to_script(scen)

    folded_script = FD.fold_script(lp.artifact, script)
    folded_plain = FD.fold_batches(lp.artifact, [b for _l, b in script])
    rep([b for _l, b in folded_script] == folded_plain,
        "R4) `fold_script` and `fold_batches` agree claim-for-claim -- the "
        "script form is a label-preserving wrapper, not a second injection")
    rep([l for l, _b in folded_script] == [l for l, _b in script],
        "R4b) ... and every LABEL is untouched: a label is documentation, and "
        "a route firing is not something the scenario's author wrote")

    # The same claims reach both producers' epoch 1 -- ALL of them, which is
    # the half a truncating injection gets wrong.
    inline = FD.fold_batches(lp.artifact, [[], [], []])
    n = len(FD.route_claims_by_epoch(lp.artifact)[1])
    rep(n == 3 and inline[0] == folded_plain[0][-n:],
        "R4c) all %d route envelopes land in epoch 1 of BOTH producers -- one "
        "seam, checked by comparing its two consumers over an epoch big "
        "enough for them to differ" % 3)


# ------------------------------------------------------------------- R5
def r5_explicit_twin():
    """THE TWIN. A fired route must be indistinguishable from the same claim
    written out by hand against the route-FREE world.

    This is the row that makes `ir_to_fixture`'s lifted refusal honest. Commit 2
    refused to build a Fixture for a route-bearing world because it would have
    silently dropped the routes; commit 4 says the dropping is CORRECT because a
    route is a claim and not structure. That is a claim about the world, so it
    gets measured against a world that contains no routes at all.

    NOTE, and it is a finding: the twin's claim is built with `mk_claim`, not
    written as a ScenarioV1 claim, because SCENARIOV1 CANNOT EXPRESS A `Send` --
    `_OPERATIONS` is `("SetRotor", "ResetFault")`. So the Q4 writer-15
    reservation is guarding a door that is already shut for a second, independent
    reason. Worth flagging: the reservation is not thereby useless (a scenario
    can still author a writer-15 SetRotor and collide on the fact key), but it is
    not the only thing stopping a scenario from forging a route."""
    routed = lower(world(MB1), [route()])
    twin = lower(world(MB1))
    rep(routed.semantic_artifact_id != twin.semantic_artifact_id,
        "R5) the route-bearing world and its route-free twin are DIFFERENT "
        "worlds -- without this the rest of the section is vacuous")

    fx_r = W.ir_to_fixture(routed.artifact)
    fx_t = W.ir_to_fixture(twin.artifact)
    hand = [[mk_claim(WC.ROUTE_WRITER_ID, 0, ("Send", "mb", (0, 0, 0, 7)))],
            [], []]
    films_routed = run(world(MB1), [route()], k=3)[3]
    films_twin = gfilms(twin.artifact, fx_t, hand)
    rep(films_routed == films_twin,
        "R5b) ... yet the route-bearing world's %d films are BYTE-IDENTICAL to "
        "the twin's with the same claim written by hand -- a route IS a claim"
        % len(films_routed))

    rep(FD.film_mailboxes(fx_r) == FD.film_mailboxes(fx_t)
        and sorted(AD.mailboxes_of(fx_r)) == sorted(AD.mailboxes_of(fx_t)),
        "R5c) ... and the two Fixtures are the same Fixture, which is why the "
        "oracle a route-bearing world compiles against is not an approximation")

    # And the twin WITHOUT the claim must differ, or R5b is comparing two
    # foldings of nothing.
    rep(gfilms(twin.artifact, fx_t, [[], [], []]) != films_twin,
        "R5d) ... while the twin folded with NO claim differs, so R5b is a "
        "match between two things that had a chance to disagree")


# ------------------------------------------------------------------- R6
def r6_a_route_does_something():
    """The whole point. A route declared in text now moves observable state.

    D7 puts the send commit on the EPOCH BOUNDARY, so the message is enqueued in
    the epoch the route fires and only becomes observable in the next one. Both
    halves are checked: an implementation that delivered immediately would pass a
    test that only looked for the message somewhere."""
    _lp, _fx, _b, films = run(world(MB1), [route()], k=3)
    led = [_lines(f, "ledger:") for f in films]
    rep(len(led[0]) == 1 and "MailboxEnqueue" in led[0][0]
        and "epoch=1" in led[0][0],
        "R6) epoch 1 -- the route's message is ENQUEUED (ledger:MailboxEnqueue, "
        "mailbox=mb)")
    rep(len(led[1]) == 1 and "MailboxDeliver" in led[1][0]
        and "epoch=2" in led[1][0],
        "R6b) epoch 2 -- and DELIVERED at the boundary, not on arrival (D7)")

    mb = [_lines(f, "mailbox:mb")[0] for f in films]
    rep("inbox=()" in mb[0] and "next_inbox=(w15.s0" in mb[0],
        "R6c) ... which the cur/next projection agrees with: epoch 1 has the "
        "message in `next_inbox` and NOTHING observable in `inbox`")
    rep("inbox=(w15.s0" in mb[1] and "next_inbox=()" in mb[1],
        "R6d) ... and epoch 2 has it in `inbox` -- the same cur/next idiom the "
        "v0.6 film already uses for relays and doors")
    rep("inbox=(),next_inbox=()" in mb[2],
        "R6e) ... and epoch 3 is drained: one shot, delivered once")

    rec = _lines(films[0], "receipt:w=15")
    rep(len(rec) == 1 and "outcome=Applied" in rec[0] and "epoch=1" in rec[0],
        "R6f) the route's claim was ACCEPTED (outcome=Applied at epoch 1), not "
        "merely observed -- a rejected claim would also produce a film")


# ------------------------------------------------------------------- R7
def r7_declared_policy_seam():
    """NOT IN THE RULING. A sealed world declares its acceptance policy and its
    film schema, and until this commit NOTHING READ THEM.

    `admit_step`'s `policy_id` defaults to the mailbox-FREE
    `admit_candidate_min_firstreceipt_v1`; `film_bytes_v7`'s `mailboxes`
    defaults to None. So every fold harness in the tree was running a
    mailbox-bearing world under a reducer that does not model mailboxes, and
    rendering it with a projection that cannot show one.

    The failure is not a missing line. It is a WRONG line: with no declared
    mailboxes, Film v0.7's Guard 3 canonicalizes the route's target to
    INVALID_TARGET, so the default reading produces a film asserting the route
    addressed something that does not exist."""
    lp = lower(world(MB1), [route()])
    fx = W.ir_to_fixture(lp.artifact)
    batches = FD.fold_batches(lp.artifact, [[], [], []])

    pol, mbs, arule = FD.runtime_seams(lp.artifact, fx)
    rep(pol == AD.MAILBOX_POLICY_ID and mbs == [("mb", 8, 4)],
        "R7) the sealed world DECLARES %s and one mailbox record -- read off "
        "the artifact, not re-derived from its roles" % AD.MAILBOX_POLICY_ID)
    rep(arule.policy_id == pol and arule.reject_equivocal,
        "R7a) ... and the SAME declaration selects the IC ACCEPT rule, so the "
        "reduction refuses an equivocal event key exactly where golden does")
    rep(FD.film_schema_of(lp.artifact) == "film.v0.7.mailbox.v1",
        "R7b) ... and declares the mailbox film schema too, which is exposed "
        "so a lowering that claims it without a mailbox can be caught")

    declared = gfilms(lp.artifact, fx, batches)
    default = gfilms(lp.artifact, fx, batches, policy=None, mailboxes=None)
    rep(declared != default,
        "R7c) folding the SAME world under the declared policy and under the "
        "old default gives DIFFERENT films -- the defaults were not harmless")
    # REWRITTEN at the Core 0.2.0 cut, because the fact it asserted stopped
    # being true and the reason is worth keeping rather than patching over.
    #
    # This row used to read "the default LOSES the route's entire effect: no
    # ledger, no mailbox line, no enqueue". The ledger half was an artefact of
    # a defect one layer down: `film_bytes_v7` rendered its EventLedger loop
    # INSIDE `if mailboxes:`, so passing `mailboxes=None` suppressed history
    # that had already been computed. 0.2.0 hoisted the loop out (a reject is
    # seam 1 refusing an event key, not a mailbox event), so the ledger now
    # renders under BOTH readings.
    #
    # What that exposes is strictly stronger than what was lost. The default
    # film does not merely omit the mailbox -- it CONTRADICTS ITSELF. Film
    # v0.7's Guard 3 canonicalizes the claim's target to INVALID_TARGET
    # because `mb` is not a live fixture object under this reading, while the
    # ledger line on the same page names `mailbox=mb`. One film, two answers
    # to "does mb exist".
    #
    # A wrong reading that is loudly self-inconsistent is a better outcome
    # than one that is quietly incomplete, and it is the same direction taken
    # for the reject projection: never invent, but do not hide either.
    # GOTCHA, recorded because it made the first spelling of this row FAIL for
    # a reason that had nothing to do with what it asserts: `_lines` matches by
    # SUBSTRING, so the key "mailbox:" also selects the "admit_mailbox:" line.
    # A count written against the obvious key is off by one on the declared
    # side and would have been silently satisfiable on the other. The keys
    # below are spelled so that each selects exactly one kind of line.
    dtxt, gtxt = default[0].decode(), declared[0].decode()
    rep("mailbox:mb:w=" not in dtxt
        and "admit_mailbox:" not in dtxt
        and "mailbox:mb:w=" in gtxt
        and "admit_mailbox:" in gtxt
        and len(_lines(default[0], "ledger:")) == 1
        and len(_lines(declared[0], "ledger:")) == 1
        and "payload=Send:%s:" % AD.INVALID_TARGET in dtxt
        and "ledger:MailboxEnqueue,mailbox=mb," in dtxt,
        "R7d) ... and what the default LOSES is the mailbox STATE -- no "
        "`mailbox:` line, no `admit_mailbox:` line -- while the EventLedger "
        "survives, so the default film CONTRADICTS ITSELF: the claim's target "
        "canonicalizes to `%s` and the ledger on the same page names "
        "`mailbox=mb`" % AD.INVALID_TARGET)
    rep("payload=Send:%s:" % AD.INVALID_TARGET in default[0].decode()
        and "payload=Send:mb:" in declared[0].decode(),
        "R7e) ... and worse, it renders the target as `%s` -- a film that says "
        "the route addressed a mailbox that does not exist" % AD.INVALID_TARGET)

    # THE POLICY HALF, ON ITS OWN. Everything above discriminates the MAILBOX
    # half: fold the one-route world with `policy=None` and the films are
    # byte-identical, because a single message is accepted the same way by
    # both policies. So `mutate49`'s M12 -- forget the policy, keep the
    # mailboxes -- walked through this whole section.
    #
    # The two policies differ in how they accumulate SEVERAL claims addressed
    # to one key: the declared `admit_mailbox_deliver_all_v1` appends each,
    # the default `admit_candidate_min_firstreceipt_v1` collapses them to the
    # minimum. So the smallest world that can tell them apart is one that
    # sends TWICE to the SAME mailbox -- and the failure is not a missing
    # line, it is a DROPPED MESSAGE: the world sent two, the film shows one.
    two = lower(world(MB1), [route(tag="a", body=(0, 0, 0, 7)),
                             route(tag="b", body=(0, 0, 0, 9))])
    fx2 = W.ir_to_fixture(two.artifact)
    b2 = FD.fold_batches(two.artifact, [[], [], []])
    dec2 = gfilms(two.artifact, fx2, b2)
    pol2 = gfilms(two.artifact, fx2, b2, policy=None)
    box_d = _lines(dec2[1], "mailbox:mb")[0]
    box_p = _lines(pol2[1], "mailbox:mb")[0]
    rep(box_d.count("->mb[") == 2,
        "R7g) two routes to ONE mailbox: under the DECLARED policy both "
        "messages are delivered")
    rep(box_p.count("->mb[") == 1 and dec2 != pol2,
        "R7h) ... and under the old default one is SILENTLY DROPPED -- the "
        "policy half is not cosmetic, and this is the only shape that can "
        "tell it apart from the mailbox half (one message cannot)")

    # The seam must be inert where it is supposed to be inert, or it is a
    # behaviour change to every route-free world in the tree.
    tf = lower(world())
    fxf = W.ir_to_fixture(tf.artifact)
    rep(FD.admit_policy_of(tf.artifact) == AD.ACCEPTANCE_POLICY_ID
        and FD.film_mailboxes(fxf) == [],
        "R7i) a mailbox-free world declares the ORIGINAL policy and an empty "
        "mailbox list, so honouring the declaration changes nothing for it")


# ------------------------------------------------------------------- R8
def r8_short_run_is_a_run_input():
    """A route whose epoch lies past the end of the run does not fire, and that
    is NOT an error (D3). Run length is a RUN INPUT; refusing a short run here
    would make a world's legality depend on a document that is deliberately not
    part of its identity."""
    lp = lower(world2(MB1), [route(src="p1", tag="late")])
    rep(sorted(FD.route_claims_by_epoch(lp.artifact)) == [2],
        "R8) the route fires at epoch 2 -- without this the next row is "
        "vacuous")
    short = FD.fold_batches(lp.artifact, [[]])
    rep(len(short) == 1 and short[0] == [],
        "R8b) a ONE-epoch run of that world is a legal, empty fold: the route "
        "simply does not fire (D3 -- a short run is a run input, not a defect)")

    census = FD.epoch_batch_census(lp.artifact, [[]])
    rep(census == {1: (0, 0), 2: (0, 1)},
        "R8c) ... and the census still REPORTS the unreached epoch (2 carries "
        "1 route claim), so \"did not fire\" is visible rather than erased")
    rep(SC.check_epoch_batch_capacity(
        SC.demo_scenario(lp.semantic_artifact_id), lp.artifact) is not None,
        "R8d) ... and the capacity door ignores epochs the run never reaches, "
        "for the same reason")


# ------------------------------------------------------------------- R9
def r9_cofire_bound():
    """NOT IN THE RULING, and the reason it exists is a measurement.

    Every Slice B route is `once`, so co-firing is not exotic: it is what
    happens the moment an author hangs a second route on a pulser. `admit_step`
    opens with a bare `assert len(batch) <= MAX_BATCH` -- an AssertionError,
    raised by the reducer, about a world that sealed perfectly. Before this law
    existed, worlds with 5 and 6 routes on one `once(1)` pulser both SEALED and
    would have crashed on epoch 1."""
    ok4 = lower(world(MB1), spread(WC.MAX_ROUTE_COFIRE, first=99))
    rep(ok4.semantic_artifact_id.startswith("sem-"),
        "R9) %d routes on one `once` Pulser still seal -- the bound is the "
        "batch, not a discouragement" % WC.MAX_ROUTE_COFIRE)
    rep(len(FD.fold_batches(ok4.artifact, [[]])[0]) == AD.MAX_BATCH,
        "R9b) ... and they exactly fill one observation batch (%d)"
        % AD.MAX_BATCH)

    over = spread(WC.MAX_ROUTE_COFIRE + 1, first=99)
    rep(_typed(lambda: lower(world(MB1), over), WC.WRL_ROUTE_BATCH_OVERFLOW),
        "R9c) one more is refused at SEAL time as WRL_ROUTE_BATCH_OVERFLOW -- "
        "a typed refusal, not the reducer's bare AssertionError")

    # Keyed by EPOCH, not by source: a per-source tally would wave this through.
    two = [route(src="p0", tag="a"), route(src="p0", tag="b"),
           route(src="p0", tag="c"), route(src="p1", tag="d"),
           route(src="p1", tag="e")]
    rep(sem(world2(MB1), two) is not None,
        "R9d) 3 routes at epoch 1 + 2 at epoch 2 seal -- the law bounds an "
        "EPOCH, so spreading them is the repair the message names")
    three_each = [route(src="p0", tag="a%d" % i) for i in range(3)] + \
                 [route(src="p1", tag="b%d" % i) for i in range(3)]
    rep(sem(world2(MB1), three_each) is not None,
        "R9e) ... and the full budget of %d is STILL reachable across two "
        "epochs, so the new law did not quietly narrow the old one"
        % WC.MAX_ASYNC_ROUTES)

    # Two DIFFERENT pulsers firing at the SAME epoch is the case a per-source
    # tally misses entirely.
    same = world(MB1).replace("[door:d0]{sig_in}\n",
                              "[door:d0]{sig_in}\n"
                              "[pulser:p2](mode=once, epoch=1){sig_out}\n")
    both = [route(src="p0", tag="a%d" % i) for i in range(3)] + \
           [route(src="p2", tag="b%d" % i) for i in range(3)]
    rep(_typed(lambda: lower(same, both), WC.WRL_ROUTE_BATCH_OVERFLOW),
        "R9f) TWO `once(1)` Pulsers with 3 routes each is also refused -- the "
        "tally is keyed by epoch, which is the only key that catches this")

    ex = _raised(lambda: lower(world(MB1), over))
    rep(ex is not None and "epoch" in str(ex) and ex.code
        != WC.WRL_ROUTE_BUDGET,
        "R9g) ... and it is a DISTINCT code from WRL_ROUTE_BUDGET, because "
        "\"declare fewer routes\" and \"declare them on different epochs\" are "
        "opposite repairs and one code cannot ask for both")


# ------------------------------------------------------------------ R10
def r10_pairing_bound():
    """The PAIRING half of the same bound, and the newest reason the
    compatibility door exists: it is the first check that NEITHER document
    could have made on its own.

    The seal bounds a world's co-firing routes and `validate_scenario_v1` bounds
    a scenario's per-epoch claims, each against the SAME batch. So four of each
    is two legal documents and eight claims -- an AssertionError inside
    `admit_step` about two documents that both validated."""
    lp = lower(world(MB1), spread(WC.MAX_ROUTE_COFIRE, first=99))
    scen = SC.demo_scenario(lp.semantic_artifact_id)
    rep(SC.validate_scenario_v1(scen) is not None
        and lp.semantic_artifact_id.startswith("sem-"),
        "R10) the world and the scenario are EACH legal -- neither document is "
        "over its own bound")

    ex = _raised(lambda: SC.check_epoch_batch_capacity(scen, lp.artifact))
    rep(ex is not None and ex.code == WC.WRL_EPOCH_BATCH_OVERFLOW,
        "R10b) ... and their PAIRING is refused as WRL_EPOCH_BATCH_OVERFLOW")
    rep(ex is not None and "authored" in str(ex) and "route" in str(ex),
        "R10c) ... by a message that names WHICH HALF is large, so the author "
        "knows which of the two files to edit")
    rep(_typed(lambda: SC.check_world_compatibility(
        scen, lp.artifact, lp.semantic_artifact_id),
        WC.WRL_EPOCH_BATCH_OVERFLOW),
        "R10d) ... and it is composed into the ONE compatibility door, not "
        "left as a check a caller has to remember")

    # It must not fire on worlds it does not apply to.
    rf = lower(world(MB1))
    rep(SC.check_world_compatibility(
        SC.demo_scenario(rf.semantic_artifact_id), rf.artifact,
        rf.semantic_artifact_id) is not None,
        "R10e) a route-free world + the same scenario still passes -- the rule "
        "does not apply, rather than applying and happening to fit")

    census = FD.epoch_batch_census(lp.artifact,
                                   [b for _l, b in
                                    SC.scenario_to_script(scen)[1]])
    rep(census[1] == (1, WC.MAX_ROUTE_COFIRE),
        "R10f) the census the refusal is built from is exposed separately, and "
        "it reports (1 authored, %d routed) at epoch 1 -- evidence, not a "
        "verdict" % WC.MAX_ROUTE_COFIRE)

    # THE LAST LINE OF DEFENCE. Everything above goes through the SCENARIO
    # door, and a caller that assembles batches itself never opens it -- which
    # is every L-0 battery, and the bench's own oracle path. `fold_batches`
    # therefore re-checks capacity at the merge, and until `mutate49`'s M20
    # deleted that check and nothing went red, no row had ever reached it.
    hand = [[mk_claim(1, 1, ("ResetFault", "ob"))]]
    rep(_typed(lambda: FD.fold_batches(lp.artifact, hand),
               WC.WRL_EPOCH_BATCH_OVERFLOW),
        "R10g) `fold_batches` REFUSES the same overrun on its own, without a "
        "scenario -- so a caller that never opens the compatibility door "
        "still cannot hand `admit_step` a batch it will assert on")
    rep(hand == [[mk_claim(1, 1, ("ResetFault", "ob"))]],
        "R10h) ... and refuses without having mutated the caller's batches, "
        "so a refused fold leaves nothing half-merged behind")


# ------------------------------------------------------------------ R11
def r11_route_free_unchanged():
    """Route-free worlds are still byte-identical.

    Commit 4 edited the seal, added a module, and changed which policy a fold
    honours. Any of the three could have moved a world that has no routes."""
    for name, src in (("none", world()), ("one", world(MB1)),
                      ("two", world(MB1 + MB2))):
        rep(sem(src) == B47.PRE_SLICE_B[name],
            "R11-%s) the route-free world still seals to its PRE-Slice-B id "
            "(%s..)" % (name, B47.PRE_SLICE_B[name][:16]))

    # And a mailbox-FREE world folds identically whether or not the caller
    # honours the declaration -- which is what makes the R7 seam safe to call
    # unconditionally rather than a behaviour change to the whole tree.
    lp = lower(world())
    fx = W.ir_to_fixture(lp.artifact)
    batches = [[mk_claim(1, 1, ("SetRotor", "sp", (16, 0, 20, 0)))], [], []]
    rep(gfilms(lp.artifact, fx, batches)
        == gfilms(lp.artifact, fx, batches, policy=None, mailboxes=None),
        "R11b) a mailbox-free world folds BYTE-identically under the declared "
        "seams and under the old defaults -- `film_mailboxes` returns [] and "
        "Film v0.7 gates its whole mailbox block on that")


# ------------------------------------------------------------------ R12
def r12_ic_boundary():
    """NOT IN THE RULING. The IC boundary, measured rather than described.

    `admit_ic` is the REDUCED PROOF PROFILE the native reducer folds. It packs a
    claim into one integer:

        CKEY_W = WD + WKIND + WIDX + 4*WLANE = 8 + 1 + 3 + 32 = 44
        FKEY_W = 2*WK + CKEY_W                                = 52

    `WKIND` is ONE BIT, sized for `SetRotor=0 | ResetFault=1`. D9's `Send` is
    tag 2. So a route's claim cannot be packed at all, and the file contains
    ZERO occurrences of "mailbox" or "Send".

    THIS GAP IS NOT SLICE B's. Slice A shipped `Send` into the golden reducer,
    the plan, and Film v0.7 without ever lowering it to IC; commit 4 is simply
    the first thing that tried to fold one. The ruling says "do not widen WK,
    MAX_FACTS, FKEY_W, EKEY_W", and widening `WKIND` moves `CKEY_W` 44 -> 45 and
    `FKEY_W` 52 -> 53. That is the open question in the commit 4 memo.

    What this section does is fix the boundary precisely, so the memo asks about
    a measured thing: the WORLD half of a route-bearing world crosses to the
    native reducer intact, and only the CLAIM half does not."""
    rep(X.WKIND == 1 and X.CKEY_W == 44 and X.FKEY_W == 52,
        "R12) the reduced profile is WKIND=%d, CKEY_W=%d, FKEY_W=%d -- pinned "
        "here so the memo's question is about a measured width"
        % (X.WKIND, X.CKEY_W, X.FKEY_W))

    lp = lower(world(MB1), [route()])
    fx = W.ir_to_fixture(lp.artifact)
    pay = ("Send", "mb", (0, 0, 0, 7))
    rep(AD.payload_key(fx, pay)[0] == 2 and (1 << X.WKIND) <= 2,
        "R12b) ... and D9's `Send` is payload tag 2, which does not fit in one "
        "bit -- the gap is arithmetic, not an oversight in this commit")

    def packs():
        try:
            X.pack_ckey(fx, pay)
        except AssertionError as ex:
            return "overflows width 1" in str(ex)
        return False
    rep(packs,
        "R12c) `pack_ckey` on a route's claim is an AssertionError (\"field 2 "
        "overflows width 1\"), so a route-bearing fold cannot reach ic32 today")

    # The WORLD half is unaffected, and that is the load-bearing half of the
    # boundary: it says the gap is confined to the claim encoding.
    twin = lower(world(MB1))
    fx_t = W.ir_to_fixture(twin.artifact)
    _t, _K, fr, fg = B47._fold(fx_t, [[], [], []])
    rep(fr == fg,
        "R12d) ... while the SAME fixture with no claim folds ic_ref == golden "
        "-- a mailbox costs the world state nothing, so only the claim "
        "encoding is missing")
    rep(sorted(init_state_v6(fx)) == sorted(init_state_v6(fx_t)),
        "R12e) ... and the route-bearing world's initial state is key-for-key "
        "the twin's: a mailbox lives in CLAIM state, not world state")

    # R12f/R12g SIZE the gap, because "widen something" is not a ruling until
    # somebody says WHICH width and by how much.
    #
    # The obvious repair is to steal a bit rather than grow the key: `WIDX` 3->2
    # while `WKIND` 1->2 holds CKEY_W at exactly 44, so FKEY_W and EKEY_W never
    # move and the ruling's prohibition is honoured to the letter. It does not
    # work, and the reason is a law THIS COMMIT wrote.
    #
    # The target index is PER-KIND scoped (SetRotor->spinners, ResetFault->orbs,
    # Send->mailboxes) and an out-of-fixture target packs to the sentinel
    # `len(targets)`. So WIDX bounds each kind at 2^WIDX - 1 targets. A world
    # with the full ruled budget of MAX_ASYNC_ROUTES routes aimed at that many
    # DISTINCT mailboxes is legal under every commit-4 law -- it is built below
    # rather than described -- and it needs a sentinel of 6, i.e. WIDX >= 3.
    #
    # Measured here rather than asserted in the memo because a memo cannot go
    # red. If a later slice bounds mailboxes, or moves MAX_ASYNC_ROUTES, this
    # row changes with it and the ruling request stops being true on paper only.
    n = WC.MAX_ASYNC_ROUTES
    mbs = "".join(MB1.replace("mb", "mb%d" % i) for i in range(n))
    wide = lower(world2(mbs), [route(src=("p0" if i < WC.MAX_ROUTE_COFIRE
                                          else "p1"),
                                     tag="t%d" % i, mb="mb%d" % i)
                               for i in range(n)])
    fx_w = W.ir_to_fixture(wide.artifact)
    names = sorted(AD.mailboxes_of(fx_w))
    sentinel = len(names)
    rep(len(names) == n,
        "R12f) the FULL ruled budget of %d routes aimed at %d DISTINCT "
        "mailboxes seals cleanly -- so this world is not a hypothetical" % (n, n))
    rep(sentinel > (1 << 2) - 1 and sentinel <= (1 << X.WIDX) - 1,
        "R12g) ... and its INVALID_TARGET sentinel is index %d, which fits "
        "WIDX=%d but NOT WIDX=2 -- so `WIDX 3->2 while WKIND 1->2` cannot be "
        "the repair: holding CKEY_W at 44 that way would cap a world at 3 "
        "mailboxes, and the route budget already permits %d"
        % (sentinel, X.WIDX, n))


# ------------------------------------------------------------------ R13
def r13_native():
    """The frozen demo world still folds three ways.

    Commit 4 edited the seal, `binding_run3o`'s helpers (defaulted parameters),
    and the fold path -- all upstream of the term the reducer folds."""
    lp = W.lower_program(B5.CORE_SRC, W.parse_wrl_legacy_document)
    batches = B5._batches_from_program(lp)
    term, K, films_ref, films_gold = B47._fold(lp.fixture, batches)
    rep(films_ref == films_gold,
        "R13) the frozen demo world folds ic_ref == golden over %d epochs "
        "(unchanged by the runtime fold)" % K)
    if SKIP_NATIVE:
        print("       (native skipped: TRVM_SKIP_NATIVE=1)")
        return False
    dec_nat = O._decode_fold(O.native(term), K, fx=lp.fixture)
    claims_nat = O._project_claims(dec_nat, epoch0=1, fx=lp.fixture)
    films_nat = [O._film(dec_nat[e][0], claims_nat[e], e + 1, fx=lp.fixture)
                 for e in range(K)]
    nat_ok = films_nat == films_ref == films_gold
    rep(nat_ok, "R13b) ic_ref == ic32 == golden")
    return nat_ok


def section(fn):
    try:
        return fn()
    except BaseException as ex:                       # noqa: BLE001
        if isinstance(ex, (SystemExit, KeyboardInterrupt)):
            raise
        rep(False, "%s) raised %s: %s -- the section aborted before its "
                   "remaining rows could run"
            % (fn.__name__.split("_")[0].upper(), type(ex).__name__, ex))
        return False


def main():
    print("[BINDING wrl-sliceB-c4] the runtime fold")
    t0 = time.time()
    section(r1_runtime_image)
    section(r2_fires_at_its_epoch)
    section(r3_order_and_purity)
    section(r4_one_seam)
    section(r5_explicit_twin)
    section(r6_a_route_does_something)
    section(r7_declared_policy_seam)
    section(r8_short_run_is_a_run_input)
    section(r9_cofire_bound)
    section(r10_pairing_bound)
    section(r11_route_free_unchanged)
    section(r12_ic_boundary)
    native_ok = section(r13_native)

    print()
    if _FAILED:
        for f in _FAILED:
            print("  FAILED: %s" % f)
        print("VERDICT: FAILURES (%d) in %ds" % (len(_FAILED), time.time() - t0))
        return 1
    mode = ("PASS_REF_ONLY (native skipped)" if SKIP_NATIVE
            else ("PASS_REF_AND_NATIVE" if native_ok
                  else "REF_ONLY (native MISMATCH)"))
    print("VERDICT: %s -- Slice B Commit 4 (the runtime fold) closed in %ds"
          % (mode, time.time() - t0))
    print("NOTE: a `~~` written in text now FIRES -- enqueued at its epoch, "
          "delivered at the next boundary, visible in Film v0.7. NOT YET "
          "FROZEN: R12 measures a boundary this commit cannot cross alone. The "
          "route-bearing fold is closed at the GOLDEN layer only, because the "
          "reduced proof profile has no `Send` encoding and no mailbox at all "
          "-- a Slice A gap that commit 4 is merely the first to reach. R13 "
          "keeps the native closure honest for every world that has no route.")
    return 0 if (SKIP_NATIVE or native_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
