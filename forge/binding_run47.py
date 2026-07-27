#!/usr/bin/env python3
"""binding_run47.py -- Slice B, Commit 2: the canonical AsyncRouteDecl.

GPT-5.6's ruling (2026-07-25) turned Slice B from "a recurring channel" into a
BOUNDED ONE-SHOT ROUTE, and fixed the identity of one:

    AsyncRouteDecl { source_id, route_tag, mailbox_id, body }
    RouteKey(source_id, route_tag, mailbox_id)      -- body EXCLUDED

Commit 2 is the canonical half only: the declaration, its locator, its
projection into the artifact, and its carriage through CompilePlanV1. There is
no `~~` surface yet (commit 3) and no runtime fold yet (commit 4), so every row
here builds routes by writing the record directly onto a `WrlGraph`.

The ruling names nine proofs. They are P1-P9 below, in its order. P0 is not in
the ruling and is the row I would most want if I were reviewing this: three
constants in `wrl_canonical` are DERIVED from ADMIT's frozen bounds and are
deliberately not imported from it, so the derivation has to be pinned or it is
just a coincidence waiting to stop being one.

Structure
---------
P0      the derived constants agree with ADMIT, checked not assumed
P1      AsyncRouteDecl is a declaration, not an edge in disguise
P2      the empty projection is canonically OMITTED, and there is only one of it
P3      route-free worlds are BYTE-identical to their pre-commit-2 selves
P4      `body` moves world identity; it does NOT move RouteKey
P5      authoring order does not move identity, and it fixes `sequence`
P6      a duplicate RouteKey is typed AND located; the budget is separate
P7      the plan carries routes, and the reconstruction re-hashes
P8      nothing PHYSICAL moved -- the same statement commit 1 made for mailboxes
P9      the legacy canvas.v1 door refuses, and WHICH loss fires is stated

Run:  python3 binding_run47.py      (TRVM_SKIP_NATIVE=1 for reference only)
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import admit as AD
import wrl_canonical as WC
import wrl_canvas as CV
import wrl_ir as W
import wrl_legacy as LG
import wrl_plan as WP
import binding_run3o as O
import binding_run5 as B5
from fixture import init_state_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

# ---------------------------------------------------------------- the pins
#
# THREE literal SemanticArtifactIDs for route-free worlds (P3). They are
# literals, not recomputed values, because a constant recomputed by the thing it
# pins proves nothing -- the lesson binding_run46 wrote down about L0_SEM.
#
# Provenance, so the next reader does not have to trust me: each was produced by
# hashing the artifact these sources lower to under the PRE-Slice-B
# `wrl_canonical.py` (`git show HEAD:forge/wrl_canonical.py`, commit 78cc124,
# "Ship Spinner Bench v0.7.0-alpha.5 and land Mailbox Slice A identity spine"),
# which has the Mailbox registry role but knows nothing about routes. If commit
# 2 had perturbed the canonical bytes of a route-free world by so much as a key
# order, these three would not match.
PRE_SLICE_B = {
    "none": "sem-be008e99d54e5a15d510d250b76a437ab05fdf0ce7fc8ae3317"
            "05636ce7c4db0",
    "one":  "sem-d3e555beaa94f47ca132b891c24a0134ead6d1faaa909f3e3d77"
            "74349da7950e",
    "two":  "sem-cd525d44c76adafd2a2412b9d8895a6e074bd8088858b13f3130"
            "3eb01ea7491e",
}

HEAD = """profile forge.world.core.v1

[pulser:p0](mode=once, epoch=1){sig_out}
[door:d0]{sig_in}
[spinner:sp](w=8, n=4, rotor=16.0.0.0, configurable){sig_in, socket}
[orb:ob]{pose}
"""
TAIL = """
[pulser:p0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]
"""
MB1 = "[mailbox:mb](w=8, cap=4){}\n"
MB2 = "[mailbox:mc](w=16, cap=9){}\n"

LP1 = {"counter_encoding": "one_hot", "onehot_max": 32, "numeric_backend": "ic",
       "compiler_hash": "a" * 64, "target": "ic32",
       "lowering_profile_version": "1.0"}

_FAILED = []


def rep(ok, label):
    """Report one row. `ok` may be a bool OR a zero-arg callable; the callable
    form keeps a row that RAISES named as itself rather than aborting its
    section under a neighbour's name (binding_run46's mutation finding)."""
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


# ------------------------------------------------------------- constructors
def route(src="p0", tag="msg", mb="mb", body=(0, 0, 0, 7)):
    return {"source_id": src, "route_tag": tag, "mailbox_id": mb,
            "body": tuple(body)}


def world(*mailbox_lines):
    return HEAD + "".join(mailbox_lines) + TAIL


# A SECOND `once` Pulser, firing LATER. Commit 4 added the co-firing law
# (WRL_ROUTE_BATCH_OVERFLOW): every route hung on one firing epoch arrives in a
# single ADMIT observation batch, and that batch holds `admit.MAX_BATCH`. So the
# full MAX_ASYNC_ROUTES budget is only reachable across MORE THAN ONE epoch.
#
# The budget rows below were written before that law existed and spent the whole
# budget on p0 -- a shape that sealed but that the reducer could never have run.
# They now spend it the way an author actually would. This is not a weakening of
# the budget rows: P6g asserts the full budget is STILL reachable, which is the
# thing that would quietly be lost if the new law had narrowed the old one.
P1_DECL = "[pulser:p1](mode=once, epoch=2){sig_out}\n"


def world2(*mailbox_lines):
    """`world()` plus a second, later-firing `once` Pulser."""
    return HEAD + P1_DECL + "".join(mailbox_lines) + TAIL


def spread(n, mb="mb", first=None):
    """`n` distinct routes divided over `world2`'s two pulsers so that no single
    firing epoch exceeds `MAX_ROUTE_COFIRE`. `first` is how many go on p0."""
    first = WC.MAX_ROUTE_COFIRE if first is None else first
    return [route(src=("p0" if i < first else "p1"), tag="t%d" % i, mb=mb)
            for i in range(n)]


def graph(src, routes=()):
    """A parsed graph with routes written directly onto it.

    Commit 3 gives `~~` a spelling; until then this IS the authoring surface,
    and using it keeps commit 2's rows about the canonical layer rather than
    about a parser that does not exist yet."""
    g = W.parse_wrl_core(src)
    g.routes.extend(dict(r) for r in routes)
    return g


def lower(src, routes=()):
    return W.lower_graph(graph(src, routes))


def sem(src, routes=()):
    return lower(src, routes).semantic_artifact_id


def _raised(fn):
    try:
        fn()
    except WC.WrlValidationError as ex:
        return ex
    return None


def _typed(fn, code):
    ex = _raised(fn)
    return ex is not None and ex.code == code


# ------------------------------------------------------------------- P0
def p0_derived_constants():
    """The three route constants are DERIVED from ADMIT, not imported from it.

    `wrl_canonical` is the identity spine and imports nothing but the stdlib;
    importing the runtime reducer so the spine could learn one integer would
    invert the layering. So the values are restated with the derivation written
    down -- which is a FORK, and a fork drifts silently unless something checks
    it. This is that something.

    It is checked rather than shared for the same reason `MAILBOX_WIDTH_MAX` is
    (binding_run43 r10.18): if the spine imported ADMIT's bound, a wrong bound
    would be agreed on by both sides and the agreement would confirm nothing."""
    rep(WC.MAX_ASYNC_ROUTES == AD.MAX_FACTS,
        "P0) MAX_ASYNC_ROUTES == admit.MAX_FACTS (%d) -- the route budget IS "
        "the claim-fact budget, because every route mints one fact"
        % AD.MAX_FACTS)
    rep(WC.ROUTE_WRITER_ID == (1 << AD.WK) - 1,
        "P0b) ROUTE_WRITER_ID == 2**WK - 1 == %d -- the reserved writer is the "
        "TOP of ADMIT's %d-bit writer space, so widening WK would move it"
        % ((1 << AD.WK) - 1, AD.WK))

    # The body domain is a second spelling of `admit._op_outcome`'s
    # `0 <= v < (1 << w_)` test. Commit 4 folds them into one; until then the
    # two are compared on the cases that matter, INCLUDING the boundary, since
    # an off-by-one is the whole failure mode of a duplicated range check.
    def agrees():
        # A width that is not a positive int is not a narrower case of the
        # same law, it is a CALLER error -- the target was not a mailbox. The
        # predicate answers False rather than raising, so the caller's own
        # typed rejection is the one that surfaces.
        for bad_w in (None, "8", 0, -1, True, 8.0):
            try:
                if WC.route_body_in_range(bad_w, (0, 0, 0, 0)):
                    return False
            except TypeError:
                # "answers False" and "does not raise" are ONE law, so the
                # raise is caught HERE and reported as this row rather than
                # escaping to the section guard, which would report the
                # failure under the section's name instead of the law's.
                return False
        for w_ in (1, 4, 8, 16, 32):
            hi = (1 << w_) - 1
            cases = [((0, 0, 0, 0), True), ((hi, hi, hi, hi), True),
                     ((0, 0, 0, hi + 1), False), ((0, 0, 0, -1), False),
                     ((0, 0, 0), False), ((0, 0, 0, 0, 0), False),
                     ((0, 0, 0, True), False), ((0, 0, 0, "7"), False)]
            for body, want in cases:
                if WC.route_body_in_range(w_, body) is not want:
                    return False
        return True

    rep(agrees,
        "P0c) route_body_in_range agrees with ADMIT's body domain at both "
        "boundaries for w in {1,4,8,16,32}, rejects wrong arity, negatives and "
        "bools-as-ints, and answers False (never raises) for a non-width")
    rep(WC.ROUTE_BODY_LANES == 4,
        "P0d) ROUTE_BODY_LANES == 4 -- the Send payload's fixed lane count")

    # P0c compares the predicate against a TABLE, which is a third spelling of
    # the same law: admit could drift and P0c would stay green. Commit 4
    # investigated removing the fork and DECLINED (see the predicate's
    # docstring), so the pin has to be the real thing -- the same bodies folded
    # through `admit._op_outcome` itself.
    def agrees_with_admit():
        for w_ in (1, 4, 8, 16, 32):
            mb = "[mailbox:mb](w=%d, cap=4){}\n" % w_
            fx = W.ir_to_fixture(lower(world(mb)).artifact)
            hi = (1 << w_) - 1
            for body in ((0, 0, 0, 0), (hi, hi, hi, hi), (0, 0, 0, hi + 1),
                         (hi + 1, 0, 0, 0), (0, 0, 0, -1)):
                admit_ok = AD._op_outcome(fx, ("Send", "mb", body))[0] \
                    == "Applied"
                if WC.route_body_in_range(w_, body) is not admit_ok:
                    return False
        return True

    rep(agrees_with_admit,
        "P0e) ... and it agrees with `admit._op_outcome` ITSELF, not with a "
        "table restating it -- the fork is pinned against the thing it forked "
        "from, at both boundaries, for every legal mailbox width")
    rep(WC.MAX_ROUTE_COFIRE == AD.MAX_BATCH,
        "P0f) MAX_ROUTE_COFIRE == admit.MAX_BATCH (%d) -- routes hung on one "
        "firing epoch arrive in ONE observation batch, and `admit_step` "
        "asserts that bound rather than diagnosing it" % AD.MAX_BATCH)


# ------------------------------------------------------------------- P1
def p1_decl_not_edge():
    """A route is a DECLARATION, not an edge with a new kind.

    D8 is why. A mailbox has no port and is never wired, so a route could not
    have been an `EdgeDecl` even if that had been convenient: there is no port
    pair for it to be legal at. The row proves the separation three ways --
    the route does not land in `edges`, the same endpoints ARE refused as an
    edge, and the two locators are different types that never compare equal."""
    a_no = lower(world(MB1)).artifact
    a_rt = lower(world(MB1), [route()]).artifact
    rep(a_no["edges"] == a_rt["edges"] and "async_routes" not in a_no
        and len(a_rt["async_routes"]) == 1,
        "P1) adding a route leaves `edges` BYTE-identical and lands under "
        "`async_routes` -- AsyncRouteDecl is a separate declaration")

    # ... and the same (p0 -> mb) pair as an edge is refused, so "separate
    # declaration" is not merely a naming choice.
    def as_edge():
        g = W.parse_wrl_core(world(MB1))
        g.edges.append(("SignalWire", "p0", "mb"))
        return W.lower_graph(g)

    ex = _raised(as_edge)
    rep(ex is not None and ex.code in (WC.WRL_ILLEGAL_PORT_PAIR,
                                       WC.WRL_PORT_SIGNATURE),
        "P1b) the SAME endpoints spelled as an edge are refused (%s) -- D8 "
        "holds, so a route could never have been an edge kind"
        % (ex.code if ex else "NOT REFUSED"))

    k = WC.route_key(route())
    ek = WC.EdgeKey("SignalWire", "p0", "mb")
    rep(isinstance(k, WC.RouteKey) and not isinstance(k, WC.EdgeKey)
        and not isinstance(ek, WC.RouteKey) and k != ek
        and k.render() == "route p0 ~~msg~~> mb",
        "P1c) RouteKey is its own locator type, never equal to an EdgeKey, and "
        "renders as `%s`" % k.render())


# ------------------------------------------------------------------- P2
def p2_empty_omitted():
    """There is exactly ONE way to say "no routes".

    A field that may be absent OR empty is two encodings of one world, and two
    encodings of one world is two SemanticArtifactIDs for it. The ruling says
    so directly ("Do not permit both 'absent' and `[]` as distinct encodings");
    the enforcement is split on purpose -- the VALIDATOR refuses the second
    spelling outright, and the CANONICALIZER drops it, so a document that
    reaches the hasher by any path has only the first."""
    a_no = lower(world(MB1)).artifact
    rep("async_routes" not in a_no,
        "P2) a route-free world's artifact has NO `async_routes` key")

    empty = dict(a_no)
    empty["async_routes"] = []
    rep(lambda: _typed(lambda: WC.validate_artifact_v1(empty),
                       WC.WRL_MALFORMED_ARTIFACT),
        "P2b) an explicit `async_routes: []` is a typed rejection, not a "
        "second spelling of the same world")
    rep("async_routes" not in WC.canonicalize_artifact_v1(empty),
        "P2c) ... and canonicalization DROPS it, so the two spellings collapse "
        "to one identity before anything is hashed")

    # Round trip: add a route, take it away, arrive back at the exact byte.
    rep(sem(world(MB1), [route()]) != sem(world(MB1))
        and sem(world(MB1), []) == sem(world(MB1)),
        "P2d) a route moves the id and removing it returns to the EXACT "
        "route-free id -- the projection leaves no residue")


# ------------------------------------------------------------------- P3
def p3_route_free_unchanged():
    """Route-free worlds must be byte-identical to their pre-commit-2 selves.

    This is the row the whole commit is judged by. `async_routes` touched the
    artifact field tuple, the graph canonicalizer, the plan key set and the plan
    reconstruction -- four places any of which could have perturbed a hash. The
    pins were computed under HEAD's `wrl_canonical`; see PRE_SLICE_B above."""
    got = {"none": sem(world()), "one": sem(world(MB1)),
           "two": sem(world(MB1, MB2))}
    for k in ("none", "one", "two"):
        rep(got[k] == PRE_SLICE_B[k],
            "P3%s) the %s-mailbox route-free world still seals to its "
            "pre-Slice-B id %s"
            % ({"none": "", "one": "b", "two": "c"}[k], k, PRE_SLICE_B[k][:16]))
    rep(len(set(got.values())) == 3,
        "P3d) ... and the three are distinct, so P3-P3c are not three checks "
        "of one value")


# ------------------------------------------------------------------- P4
def p4_body_moves_id_not_key():
    """`body` is in the artifact but OUT of RouteKey (ruling Q2).

    That is a deliberate asymmetry and it has a consequence worth stating in
    one place: two routes that differ only in body are the SAME route as far as
    identity-of-declaration goes (so declaring both is a duplicate, P6) while
    being DIFFERENT worlds as far as the hash goes. Both halves are asserted
    here, together, because either alone reads as a bug."""
    ids = {b: sem(world(MB1), [route(body=b)])
           for b in ((0, 0, 0, 7), (0, 0, 0, 8), (7, 0, 0, 0), (0, 0, 0, 0))}
    rep(len(set(ids.values())) == 4,
        "P4) four bodies over ONE RouteKey give four distinct "
        "SemanticArtifactIDs -- the body is world structure")

    keys = {WC.route_key(route(body=b)) for b in ids}
    rep(len(keys) == 1,
        "P4b) ... and all four share ONE RouteKey -- the body is excluded from "
        "the locator, exactly as ruled")

    # A body lane out of the MAILBOX's range is a typed refusal, and the range
    # is the mailbox's own `w`, not a global constant: the same body is legal
    # against a wider mailbox.
    rep(lambda: _typed(lambda: lower(world(MB1), [route(body=(0, 0, 0, 256))]),
                       WC.WRL_NUMERIC_RANGE),
        "P4c) a lane >= 2**w for the TARGET mailbox is WRL_NUMERIC_RANGE")
    rep(lambda: sem(world(MB1, MB2), [route(mb="mc", body=(0, 0, 0, 256))])
        is not None,
        "P4d) ... while the same body is legal against a w=16 mailbox -- the "
        "bound is read from the target, not from a global")


# ------------------------------------------------------------------- P5
def p5_order_inert():
    """Authoring order does not move identity, and it does not move `sequence`.

    The second half is the load-bearing one. Ruling Q4 defines a route's ADMIT
    `sequence` as its zero-based CANONICAL RouteKey ordinal, so if canonical
    order depended on authoring order then two byte-identical worlds could mint
    different claim facts -- a world whose runtime meaning depended on the order
    someone happened to type things in."""
    rs = [route(tag="a"), route(tag="b", body=(0, 0, 1, 0)),
          route(src="p0", tag="c", body=(0, 0, 2, 0))]
    orders = [rs, list(reversed(rs)), [rs[1], rs[2], rs[0]]]
    ids = {sem(world(MB1), o) for o in orders}
    rep(len(ids) == 1,
        "P5) three authoring orders of the same three routes seal to ONE "
        "SemanticArtifactID")

    canon = [tuple(WC.route_key(r) for r in
                   lower(world(MB1), o).artifact["async_routes"])
             for o in orders]
    rep(len(set(canon)) == 1 and list(canon[0]) == sorted(canon[0]),
        "P5b) ... the projected list is the SAME canonical RouteKey sort in "
        "all three")

    # `canonicalize_graph` must be a NORMAL FORM for routes, exactly as it
    # already is for nodes and edges. Without this row the graph-level sort is
    # unobservable -- `graph_to_ir` sorts again on its own path and
    # `route_claim_identity` sorts internally, so removing the canonicalizer's
    # sort entirely broke nothing any row could see. That is a survivor of the
    # mutation harness and the reason this row exists; the sort becomes
    # load-bearing for real in commit 3, when the formatter emits `~~` lines
    # from the canonical graph.
    cgs = [tuple(map(WC.route_key, WC.canonicalize_graph(graph(world(MB1), o))
                     .routes)) for o in orders]
    rep(len(set(cgs)) == 1 and list(cgs[0]) == sorted(cgs[0]),
        "P5d) canonicalize_graph is a NORMAL FORM for routes -- three "
        "authoring orders give one canonically sorted route list")

    seqs = [WC.route_claim_identity(o) for o in orders]
    rep(all(s == seqs[0] for s in seqs)
        and sorted(seqs[0].values()) == [(WC.ROUTE_WRITER_ID, i)
                                         for i in range(3)],
        "P5c) ... and each route's ADMIT (writer_id, sequence) is the same in "
        "all three, numbered 0..2 under writer %d" % WC.ROUTE_WRITER_ID)


# ------------------------------------------------------------------- P6
def p6_duplicate_and_budget():
    """A duplicate RouteKey is typed AND located; the budget is a SEPARATE law.

    Order matters here and is asserted: duplicates are checked BEFORE the
    budget. Seven identical routes are one route declared seven times, and
    reporting that as "too many routes" would send the author to count them
    instead of to the two lines that collide."""
    dup = [route(body=(0, 0, 0, 1)), route(body=(0, 0, 0, 2))]
    ex = _raised(lambda: lower(world(MB1), dup))
    rep(ex is not None and ex.code == WC.WRL_DUPLICATE_ROUTE,
        "P6) two routes with one RouteKey and DIFFERENT bodies are "
        "WRL_DUPLICATE_ROUTE (got %s)" % (ex.code if ex else "no error"))
    rep(ex is not None and isinstance(ex.primary_locator, WC.RouteKey)
        and ex.primary_locator == WC.route_key(dup[0]),
        "P6b) ... and the error CARRIES the RouteKey as its primary locator, "
        "so a diagnostic can point at the declaration")
    rep(ex is not None and str((0, 0, 0, 1)) in ex.message
        and str((0, 0, 0, 2)) in ex.message,
        "P6c) ... and names BOTH bodies, because the one thing the author "
        "cannot see from the locator is why the two lines differ")

    seven_same = [route(body=(0, 0, 0, i % 2)) for i in range(7)]
    rep(lambda: _typed(lambda: lower(world(MB1), seven_same),
                       WC.WRL_DUPLICATE_ROUTE),
        "P6d) SEVEN copies of one route is a duplicate, not a budget overrun "
        "-- duplicates are judged first")

    # SPREAD across two firing epochs (see `world2`). Commit 4's co-firing law
    # makes the whole budget unreachable from a single pulser, so these two
    # rows now also carry the claim that the budget is still SPENDABLE IN FULL
    # -- a co-firing law that had quietly become a route-count law would show
    # up here as P6e going red, not as a silent narrowing.
    six = spread(WC.MAX_ASYNC_ROUTES)
    rep(lambda: sem(world2(MB1), six) is not None,
        "P6e) %d distinct routes seal when spread over two firing epochs -- "
        "the budget is reachable in full" % WC.MAX_ASYNC_ROUTES)
    rep(lambda: _typed(lambda: lower(world2(MB1),
                                     spread(WC.MAX_ASYNC_ROUTES + 1)),
                       WC.WRL_ROUTE_BUDGET),
        "P6f) the %dth distinct route is WRL_ROUTE_BUDGET -- and it is the "
        "BUDGET that refuses it, not the per-epoch bound"
        % (WC.MAX_ASYNC_ROUTES + 1))

    # The endpoint laws, both ends through ONE code (the WRL_ILLEGAL_PORT_PAIR
    # precedent: one code for both ends of a relation).
    rep(lambda: _typed(lambda: lower(world(MB1), [route(src="nope")]),
                       WC.WRL_UNKNOWN_ENDPOINT),
        "P6g) an undeclared source is WRL_UNKNOWN_ENDPOINT")
    rep(lambda: _typed(lambda: lower(world(MB1), [route(mb="nope")]),
                       WC.WRL_UNKNOWN_ENDPOINT),
        "P6h) an undeclared mailbox is WRL_UNKNOWN_ENDPOINT")
    # The two role rules assert the MESSAGE as well as the code, and that is
    # not belt-and-braces. Mutation testing found both passing for the wrong
    # reason: with the source-role rule switched off, a Spinner source falls
    # through to the one-shot rule, which finds no clock at all and raises the
    # SAME code -- so the row stayed green while the law it names was gone.
    # A code plus a distinguishing phrase is what separates the two.
    def role_refusal(r, phrase):
        ex = _raised(lambda: lower(world(MB1), [r]))
        return (ex is not None and ex.code == WC.WRL_ILLEGAL_ROUTE_ENDPOINT
                and phrase in ex.message
                and isinstance(ex.primary_locator, WC.RouteKey))

    rep(lambda: role_refusal(route(mb="d0"), "a route addresses a Mailbox"),
        "P6i) a target that exists but is NOT a Mailbox is refused BY THE "
        "TARGET RULE (code + message + locator)")
    rep(lambda: role_refusal(route(src="sp"), "only a Pulser may emit"),
        "P6j) a source that is not a Pulser is refused BY THE SOURCE RULE "
        "(ruling Q5), not by the one-shot rule downstream of it")

    # The rest of Q5 -- `mode=once` and `epoch >= 1` -- is CODE in commit 2
    # although the ruling schedules its PROOFS for commit 3. Shipping the code
    # without the rows would leave a window in which a demonstrably dead world
    # seals, and it would leave two production branches that no mutation could
    # be shown to catch. So the rows are here, early, rather than the code
    # being held back.
    periodic = HEAD.replace("(mode=once, epoch=1)",
                            "(mode=periodic, period=2, phase=0)")
    rep(lambda: _typed(lambda: W.lower_graph(
        graph(periodic + MB1 + TAIL, [route()])),
        WC.WRL_ILLEGAL_ROUTE_ENDPOINT),
        "P6k) a route from a PERIODIC pulser is refused -- Slice B is "
        "one-shot, and a recurring route is deferred to forge.world.async.v1")
    zero = HEAD.replace("epoch=1", "epoch=0")
    rep(lambda: _typed(lambda: W.lower_graph(
        graph(zero + MB1 + TAIL, [route()])), WC.WRL_EPOCH_RANGE),
        "P6l) a route from a `once(0)` pulser is WRL_EPOCH_RANGE -- it could "
        "never fire, and a world that is dead by construction should say so "
        "at seal time, not in the film")
    rep(lambda: sem(zero + MB1 + TAIL) is not None,
        "P6m) ... while the SAME `once(0)` pulser without a route still seals "
        "-- the rule belongs to the route, not to the pulser")


# ------------------------------------------------------------------- P7
def p7_plan_carries_routes():
    """The plan carries routes, and the reconstruction re-hashes.

    `_plan_to_artifact` is not a convenience: `seal_compile_plan` rebuilds the
    artifact from the plan and re-derives the SemanticArtifactID, so a plan that
    forgot routes would not merely lose information, it would FAIL TO COMPILE
    every route-bearing world. That makes this row the one that has to pass
    before any of commit 4 is reachable."""
    lp = lower(world(MB1, MB2), [route(), route(mb="mc", body=(1, 2, 3, 4))])
    plan = WP.artifact_to_compile_plan_v1(lp.sealed_artifact)
    WP.validate_compile_plan_v1(plan)
    rep(len(plan["async_routes"]) == 2
        and set(plan["async_routes"][0]) == set(WC.ROUTE_FIELDS)
        and plan["async_routes"] == json.loads(json.dumps(
            plan["async_routes"])),
        "P7) the plan declares both routes with the exact AsyncRouteDecl field "
        "set, JSON-shaped (lists, not tuples) so it survives a round trip")

    rep(WC.semantic_artifact_id(WP._plan_to_artifact(plan))
        == lp.semantic_artifact_id,
        "P7b) the plan reconstruction re-hashes to the id the plan claims")
    rep(lambda: WP.seal_compile_plan(plan, lp.sealed_artifact) is not None,
        "P7c) ... so a route-bearing world SEALS a compile plan at all")

    # Tamper below every signature: routes are in no neutral signature (P8), so
    # only the reconstruction can catch this.
    bad = json.loads(json.dumps(plan))
    bad["async_routes"][0]["body"] = [0, 0, 0, 9]
    rep(WC.semantic_artifact_id(WP._plan_to_artifact(bad))
        != plan["semantic_artifact_id"],
        "P7d) a tampered route body in the plan breaks the re-hash -- routes "
        "sit below every neutral signature, so this is the ONLY check that "
        "sees it")
    rep(lambda: _typed(lambda: WP.seal_compile_plan(bad, lp.sealed_artifact),
                       WP.WRL_BAD_COMPILE_PLAN),
        "P7e) ... and sealing it is a typed refusal")

    # The plan's own gate, which has to exist because a plan can arrive from a
    # file without ever having been an artifact.
    #
    # Each row pins a distinguishing PHRASE, not just the code. Every rejection
    # in this gate shares one code (WRL_BAD_COMPILE_PLAN), so a code-only row
    # is satisfied by any of the five -- and mutation testing showed exactly
    # that: switching the target check off made the body check fire instead,
    # with the same code, and the row stayed green.
    def refuses(p, phrase):
        ex = _raised(lambda: WP.validate_compile_plan_v1(p))
        return (ex is not None and ex.code == WP.WRL_BAD_COMPILE_PLAN
                and phrase in ex.message)

    for label, mutate, phrase, why in (
            ("order", lambda p: p["async_routes"].reverse(),
             "canonical RouteKey order", "are out of canonical RouteKey order"),
            ("dup", lambda p: p["async_routes"].__setitem__(
                1, dict(p["async_routes"][0])),
             "duplicate-free", "collide under RouteKey"),
            ("target", lambda p: p["async_routes"][0].__setitem__(
                "mailbox_id", "nope"),
             "is not a declared mailbox", "target an undeclared mailbox"),
            ("source", lambda p: p["async_routes"][0].__setitem__(
                "source_id", "d0"),
             "is not a declared Pulser", "source from a non-Pulser"),
            ("body", lambda p: p["async_routes"][0].__setitem__(
                "body", [0, 0, 0, 999]),
             "lanes in", "carry an out-of-range body")):
        p = json.loads(json.dumps(plan))
        mutate(p)
        rep(lambda p=p, phrase=phrase: refuses(p, phrase),
            "P7f-%s) validate_compile_plan_v1 refuses a plan whose routes %s "
            "-- and refuses it BY THAT RULE, not by a neighbour sharing the "
            "code" % (label, why))

    # A route-free plan must still be exactly what it was.
    pf = WP.artifact_to_compile_plan_v1(lower(world(MB1)).sealed_artifact)
    rep(pf["async_routes"] == []
        and "async_routes" not in WP._plan_to_artifact(pf),
        "P7g) a route-free plan carries an EMPTY list (the plan key set is "
        "fixed) yet reconstructs an artifact with NO key (the artifact's is "
        "not) -- two different rules, both deliberate")


# ------------------------------------------------------------------- P8
def p8_nothing_physical_moved():
    """Routes are logical. The backend must not have noticed.

    This is commit 1's N11 restated for routes, and it is restated rather than
    reused because "the mailbox is not physical" and "the route is not
    physical" are two claims, and commit 2 could have broken the second while
    leaving the first true -- the plan builder is where a route could most
    easily have leaked into `object_order`."""
    variants = [
        [],
        [route()],
        [route(body=(1, 1, 1, 1))],
        [route(tag="other")],
        [route(), route(tag="other", body=(0, 0, 0, 1))],
    ]
    lows = [lower(world(MB1), v) for v in variants]
    plans = [WP.artifact_to_compile_plan_v1(lp.sealed_artifact) for lp in lows]
    comps = [WP.compile_artifact(lp.sealed_artifact, LP1) for lp in lows]

    phys = {(tuple(p["object_order"]), p["state_layout_signature"],
             p["epoch_input_signature"], p["observable_signature"])
            for p in plans}
    back = {(c.backend_layout_signature, c.backend_content_hash)
            for c in comps}
    rep(len(phys) == 1 and len(back) == 1,
        "P8) %d route variants share ONE object_order, ONE of each neutral "
        "signature, and ONE backend term (layout AND content)" % len(variants))
    rep(len({lp.semantic_artifact_id for lp in lows}) == len(variants)
        and len({WP.compile_plan_digest(p) for p in plans}) == len(variants),
        "P8b) ... while all %d SemanticArtifactIDs and CompilePlanDigests "
        "differ -- declared, and provably ignored" % len(variants))

    # And the mailbox-free physical twin is the SAME term, so P8's "one backend
    # term" is not one term shared only among mailbox worlds.
    twin = WP.compile_artifact(lower(world()).sealed_artifact, LP1)
    rep((twin.backend_layout_signature, twin.backend_content_hash)
        in back,
        "P8c) ... and it is the SAME term the mailbox-free, route-free world "
        "compiles to -- neither construct reaches the backend")

    # COMMIT 4 REVERSED THESE TWO ROWS, and the reversal is the point.
    #
    # Through commits 2 and 3 `ir_to_fixture` REFUSED a route-bearing artifact,
    # and these rows asserted the refusal. The reason was sound: the Fixture is
    # the INDEPENDENT oracle, it had no route surface, and building one anyway
    # would have produced an oracle for a DIFFERENT world that agreed with the
    # reducer on every row -- a cross-check that confirms the wrong thing, which
    # is worse than none because it reports green.
    #
    # Commit 4 makes the drop CORRECT rather than silent. A route's runtime
    # image is a CLAIM (`wrl_fold.route_claims`), not structure: no port, no
    # state, no edge, nothing the Fixture models. So the Fixture of a
    # route-bearing world is not an approximation of it -- it is exactly the
    # right Fixture, and the entire difference between the two worlds now lives
    # in the observation batch where the reducer can see it.
    #
    # That is a claim about STRUCTURE, so it is measured as one: every variant's
    # Fixture is pushed back through `fixture_to_compile_plan_v1` at a FIXED
    # semantic id, which strips the one field that could carry the difference
    # for free. One digest across all variants is the whole assertion.
    def fixtures_collapse():
        sem0 = lows[0].semantic_artifact_id          # variants[0] is route-free
        digs = set()
        for v in variants:
            fx = W.ir_to_fixture(lower(world(MB1), v).artifact)
            digs.add(WP.compile_plan_digest(
                WP.fixture_to_compile_plan_v1(fx, sem0)))
        return len(digs) == 1

    rep(fixtures_collapse,
        "P8d) `ir_to_fixture` now BUILDS a Fixture for a route-bearing "
        "artifact, and all %d variants' Fixtures collapse to ONE plan -- a "
        "route is not structure, so the oracle is the twin's and that is "
        "correct, not lossy" % len(variants))
    rep(len({lp.semantic_artifact_id for lp in lows}) == len(variants),
        "P8e) ... while those same %d worlds keep %d DISTINCT identities, so "
        "P8d is a measured collapse and not a comparison of one world with "
        "itself" % (len(variants), len(variants)))


# ------------------------------------------------------------------- P9
def p9_canvas_refuses():
    """The retired canvas.v1 door refuses a route-bearing world -- and this row
    says WHICH loss fires, because the honest answer is not the flattering one.

    `canvas_v1_export_loss` is COMPUTED: it emits, reads back through V1's own
    reader, and compares. Nothing in it names a construct, which is why it
    learned about routes without being edited. But a route-bearing world is
    NECESSARILY mailbox-bearing (the target must be a declared Mailbox), and
    the mailbox rejection fires first, so the refusal is not evidence that
    anything on the legacy path knows what a route is.

    A route gate was written into `graph_to_canvas` and then removed: canvas.v1
    is frozen (§15.1.1 point 1) and binding_run46 N10c already recorded that
    adding a rejection to it would be a behaviour change to a frozen module.
    Applying that rule to the mailbox and not to the route would have been a
    fork in the policy itself."""
    g = graph(world(MB1), [route()])
    ex = _raised(lambda: LG.export_canvas_graph_v1(g))
    rep(ex is not None and ex.code == LG.WRL_LEGACY_EXPORT_LOSSY,
        "P9) exporting a route-bearing world to canvas.v1 is a typed refusal")

    loss = LG.canvas_v1_export_loss(g)
    rep(len(loss) == 1 and "Mailbox" in loss[0],
        "P9b) ... and the reason names the MAILBOX, not the route -- stated "
        "here so nobody later reads P9 as route-awareness on the legacy path")

    # The route loss is nevertheless REAL, and that is checkable without any
    # gate: the emitted document has nowhere to put a route, so the route_tag
    # appears nowhere in it.
    doc = json.dumps(CV.graph_to_canvas(g))
    rep("msg" not in doc and "async" not in doc,
        "P9c) the emitted canvas.v1 document contains no trace of the route "
        "under any key -- the loss the refusal prevents is a real one")


# ------------------------------------------------------------------- P10
def _fold(fx, batches):
    """binding_run46 N12's fold harness, now honestly fx-parameterised.

    COMMIT 4 FIXED A LATENT DEFECT HERE. This helper always took `fx`, but
    `binding_run3o`'s golden half closed over that battery's own module global
    `FX = mkfx(8, 4)` and the argument reached only the IC half. The row passed
    because the demo world IS structurally `mkfx(8, 4)`, so the two halves were
    comparing the same world by accident, not by construction -- and it would
    have started comparing two DIFFERENT worlds, silently and greenly, the first
    time commit 4 folded a mailbox-bearing one. `binding_run3o`'s helpers now
    take a defaulted `fx`; this passes it."""
    import admit_ic as X
    from compiler import enc_state_v6
    world0 = init_state_v6(fx)
    claim0 = AD.init_claimstate(fx)
    gold = O._golden_traj(claim0, world0, batches, epoch0=1, fx=fx)
    term = O._build_fold(batches, X.enc_factvec([], O.CAP),
                         X.enc_factvec([], O.RCAP), enc_state_v6(fx, world0),
                         fx=fx)
    K = len(batches)
    dec_ref = O._decode_fold(O.norm(term), K, fx=fx)
    claims_ref = O._project_claims(dec_ref, epoch0=1, fx=fx)
    films_ref = [O._film(dec_ref[e][0], claims_ref[e], e + 1, fx=fx)
                 for e in range(K)]
    films_gold = [O._film(gold[e][0], gold[e][1], e + 1, fx=fx)
                  for e in range(K)]
    return term, K, films_ref, films_gold


def p10_native():
    """The frozen world still folds three ways.

    Commit 2 has no runtime component at all, which is precisely why this runs:
    it touched the plan builder and the plan reconstruction, and both sit
    directly upstream of the term the reducer folds."""
    lp = W.lower_program(B5.CORE_SRC, W.parse_wrl_legacy_document)
    batches = B5._batches_from_program(lp)
    term, K, films_ref, films_gold = _fold(lp.fixture, batches)
    rep(films_ref == films_gold,
        "P10) the frozen demo world folds ic_ref == golden over %d epochs "
        "(unchanged by the route projection)" % K)
    if SKIP_NATIVE:
        print("       (native skipped: TRVM_SKIP_NATIVE=1)")
        return False
    dec_nat = O._decode_fold(O.native(term), K)
    claims_nat = O._project_claims(dec_nat, epoch0=1)
    films_nat = [O._film(dec_nat[e][0], claims_nat[e], e + 1) for e in range(K)]
    nat_ok = films_nat == films_ref == films_gold
    rep(nat_ok, "P10b) ic_ref == ic32 == golden")
    return nat_ok


def section(fn):
    """Run one section; an UNEXPECTED exception becomes a named FAIL rather
    than a traceback that hides every later row."""
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
    print("[BINDING wrl-sliceB-c2] the canonical AsyncRouteDecl")
    t0 = time.time()
    section(p0_derived_constants)
    section(p1_decl_not_edge)
    section(p2_empty_omitted)
    section(p3_route_free_unchanged)
    section(p4_body_moves_id_not_key)
    section(p5_order_inert)
    section(p6_duplicate_and_budget)
    section(p7_plan_carries_routes)
    section(p8_nothing_physical_moved)
    section(p9_canvas_refuses)
    native_ok = section(p10_native)

    print()
    if _FAILED:
        for f in _FAILED:
            print("  FAILED: %s" % f)
        print("VERDICT: FAILURES (%d) in %ds" % (len(_FAILED), time.time() - t0))
        return 1
    mode = ("PASS_REF_ONLY (native skipped)" if SKIP_NATIVE
            else ("PASS_REF_AND_NATIVE" if native_ok
                  else "REF_ONLY (native MISMATCH)"))
    print("VERDICT: %s -- Slice B Commit 2 (AsyncRouteDecl) closed in %ds"
          % (mode, time.time() - t0))
    print("NOTE: NOT frozen. This battery covers the CANONICAL layer only -- "
          "the `~~` surface shipped in commit 3 (binding_run48), the runtime "
          "fold is commit 4. A route declared today is carried and provably "
          "ignored, which is a canonical claim, not a working one.")
    return 0 if (SKIP_NATIVE or native_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
