#!/usr/bin/env python3
"""binding_run48.py -- Slice B, Commit 3: the `~~` surface.

Commit 2 gave a route a canonical FORM and an identity; it had no spelling, so
every commit-2 row wrote the record straight onto a `WrlGraph`. Commit 3 gives
it the ruled spelling, in both directions:

    [p0] ~~msg~~> [mb] (body=0.0.0.7)

and closes the two things that spelling makes reachable -- the Q4 writer-15
reservation, and a silent world substitution in the authoring draft.

Structure
---------
Q0   the ruled spelling parses to EXACTLY the ruled record
Q1   the body group is REQUIRED, and every surface error is typed AND route-named
Q2   route texture is never mistaken for an edge or for "unrecognized notation"
Q3   round-trip: parse(format(w)) is the same world, and format is a normal form
Q4   authoring ORDER in text is inert -- and it still fixes the ADMIT `sequence`
Q5   a route-FREE world's text and identity are byte-unchanged (the c2 pins)
Q6   the bootstrap surface refuses `~~` HONESTLY (and !!/== keep their message)
Q7   the seal's laws reach the surface WITHOUT being restated in the parser
Q8   writer 15 is reserved by COMPATIBILITY, never by the document validator
Q9   a route-bearing world cannot silently become a route-free one in a draft
Q10  the frozen demo world still folds ic_ref == ic32 == golden

On Q9 -- this is not a ruled proof. It is a defect commit 3 CREATES: a
`WorldDraft` stores a world as `(objects, edges)`, so opening a route-bearing
world for editing does not crash and does not error, it quietly yields the
route-free world. That world is legal and has a good id, which is what makes it
dangerous. Commit 2 could ignore it because no surface could reach it; commit 3
cannot, so the guard ships here.

Fixtures, the pre-Slice-B identity pins and the fold harness are IMPORTED from
binding_run47 rather than retyped. A second copy of a pin is not a copy, it is a
fork -- the defect this whole round has been about.

Run:  python3 binding_run48.py      (TRVM_SKIP_NATIVE=1 for reference only)
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import admit as AD
import wrl_canonical as WC
import wrl_draft as D
import wrl_format as F
import wrl_ir as W
import wrl_scenario as SC
import binding_run5 as B5
import binding_run47 as B47

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

# The commit-2 fixtures and pins, SHARED not copied. `PRE_SLICE_B` holds three
# literal SemanticArtifactIDs computed under the pre-Slice-B spine (commit
# 78cc124); commit 3 must not move them either, and it must not move them
# through the FORMATTER, which is a path commit 2 never exercised.
PRE_SLICE_B = B47.PRE_SLICE_B
HEAD, TAIL, MB1, MB2 = B47.HEAD, B47.TAIL, B47.MB1, B47.MB2
world = B47.world

# The ruled spelling, written once. Every row that needs "a route line" builds
# it from `route_line` so that no row can accidentally test a spelling the
# ruling did not give.
ROUTE_LINE = "[p0] ~~msg~~> [mb] (body=0.0.0.7)"

_FAILED = []


def rep(ok, label):
    """One row. `ok` may be a bool or a zero-arg callable; the callable form
    keeps a row that RAISES named as itself instead of aborting its section
    under a neighbour's name."""
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
def route_line(src="p0", tag="msg", mb="mb", body="0.0.0.7"):
    return "[%s] ~~%s~~> [%s] (body=%s)" % (src, tag, mb, body)


def wsrc(*route_lines, **kw):
    """A route-bearing WORLD SOURCE: the commit-2 fixture world plus route
    lines, as TEXT. Commit 3's whole subject is that this is now writable."""
    mailboxes = kw.pop("mailboxes", (MB1,))
    two_pulsers = kw.pop("two_pulsers", False)
    assert not kw, kw
    body = (B47.world2 if two_pulsers else world)(*mailboxes)
    if route_lines:
        body += "\n" + "\n".join(route_lines) + "\n"
    return body


def parse(src):
    return W.parse_wrl_core(src)


def sem(src):
    return W.lower_program(src, W.parse_wrl_core).semantic_artifact_id


def _raised(fn):
    try:
        fn()
    except WC.WrlValidationError as ex:
        return ex
    return None


def _typed(fn, code):
    ex = _raised(fn)
    return ex is not None and ex.code == code


def refuses(fn, code, phrase):
    """Typed rejection AND a distinguishing message fragment.

    Nearly every surface rejection in this file wears WRL_UNSUPPORTED_FEATURE,
    so a code-only assertion is satisfied by any of them -- binding_run47's
    mutation round found exactly that (a row passed because a DIFFERENT law
    raised the same code). The phrase is what makes each row about its own
    law."""
    ex = _raised(fn)
    return (ex is not None and ex.code == code
            and phrase in str(ex))


# =================================================================== Q0
def q0_ruled_spelling():
    """The ruled spelling parses, and parses to EXACTLY the ruled record."""
    g = parse(wsrc(ROUTE_LINE))
    rep(len(g.routes) == 1,
        "Q0) `%s` parses to exactly ONE AsyncRouteDecl" % ROUTE_LINE)
    r = g.routes[0] if g.routes else {}
    rep(sorted(r) == sorted(WC.ROUTE_FIELDS),
        "Q0b) it carries EXACTLY the frozen ROUTE_FIELDS %s -- the parser "
        "invents no field and omits none" % (sorted(WC.ROUTE_FIELDS),))
    rep((r.get("source_id"), r.get("route_tag"), r.get("mailbox_id"),
         tuple(r.get("body") or ())) == ("p0", "msg", "mb", (0, 0, 0, 7)),
        "Q0c) the three RouteKey parts and the four body lanes are read off "
        "the text positionally, with the body in b0..b3 order")

    # The role prefix is optional at both ends, exactly as on an edge -- the
    # role is already fixed by the object's own declaration line, so requiring
    # it here would be a second place a role is written down.
    rep(sem(wsrc("[pulser:p0] ~~msg~~> [mailbox:mb] (body=0.0.0.7)"))
        == sem(wsrc(ROUTE_LINE)),
        "Q0d) the role prefix is OPTIONAL at both ends and inert, as on an "
        "edge -- `[pulser:p0] ~~msg~~> [mailbox:mb]` is the same route")

    # `~~` is not an edge kind and must not become one: the edge list of a
    # route-bearing world is exactly the edge list of its route-free twin.
    rep(parse(wsrc(ROUTE_LINE)).edges == parse(wsrc()).edges,
        "Q0e) a route adds NOTHING to `edges` -- D8 survives the surface: a "
        "mailbox is still never wired")


# =================================================================== Q1
def q1_body_required():
    """Q1 ruled the body STATIC and REQUIRED. Required means refused, typed,
    and named -- not defaulted, and not reported as a mystery."""
    rep(refuses(lambda: parse(wsrc("[p0] ~~msg~~> [mb]")),
                WC.WRL_UNSUPPORTED_FEATURE, "has no body"),
        "Q1) a route with NO body group is refused and the message says so -- "
        "a defaulted body would put an identity-bearing field in the compiler "
        "and not in the source")
    rep(refuses(lambda: parse(wsrc("[p0] ~~msg~~> [mb] ()")),
                WC.WRL_UNSUPPORTED_FEATURE, "missing `body`"),
        "Q1b) an EMPTY body group is refused too -- `()` is a written group, "
        "so it cannot be confused with a forgotten one and gets its own message")
    rep(refuses(lambda: parse(wsrc("[p0] ~~msg~~> [mb] (body=0.0.0.7, cap=2)")),
                WC.WRL_UNSUPPORTED_FEATURE, "unknown key"),
        "Q1c) an unknown key in the body group is refused, so the group cannot "
        "quietly accumulate a vocabulary the artifact does not have")
    rep(refuses(lambda: parse(wsrc("[p0] ~~msg~~> [mb] (body=0.0.7)")),
                WC.WRL_NUMERIC_RANGE, "must have %d lanes" % WC.ROUTE_BODY_LANES),
        "Q1d) a body of the wrong arity is WRL_NUMERIC_RANGE and the message "
        "says ROUTE BODY, not `rotor` -- two constants that coincide today are "
        "not one constant")
    rep(refuses(lambda: parse(wsrc("[p0] ~~msg~~> [mb] (body=0.0.0.x)")),
                WC.WRL_NUMERIC_RANGE, "must be integers"),
        "Q1e) a non-numeric lane is a TYPED rejection, never a bare ValueError "
        "escaping the parser")

    # The lane count is read from the constant, not from a literal 4. This is a
    # RELATIVE law: it proves the parser is driven by ROUTE_BODY_LANES, not
    # that ROUTE_BODY_LANES is right -- binding_run47 P0d pins that.
    lanes = ".".join("0" * 1 for _ in range(WC.ROUTE_BODY_LANES))
    rep(len(parse(wsrc("[p0] ~~msg~~> [mb] (body=%s)" % lanes)).routes) == 1,
        "Q1f) a body of exactly ROUTE_BODY_LANES lanes is accepted -- the "
        "parser reads the constant, so moving it moves the surface")


# =================================================================== Q2
def q2_texture_is_diagnosed():
    """A `~~` line is judged AS A ROUTE, however malformed.

    The corrected `mailbox` rejection in commit 1 is the precedent: a message
    that denies a construct exists sends an author to look for a spec change
    that already happened. A route with one tilde too few must not be reported
    as "unrecognized WRL notation"."""
    for bad in ("[p0] ~~msg~> [mb] (body=0.0.0.7)",
                "[p0] ~msg~~> [mb] (body=0.0.0.7)",
                "[p0] ~~msg~~ [mb] (body=0.0.0.7)",
                "[p0] ~~~~> [mb] (body=0.0.0.7)",
                "p0 ~~msg~~> mb (body=0.0.0.7)"):
        rep(refuses(lambda b=bad: parse(wsrc(b)),
                    WC.WRL_UNSUPPORTED_FEATURE, "bad async route notation"),
            "Q2) %r is diagnosed as a malformed ROUTE and shown the form -- "
            "never as unknown notation" % bad)

    # The texture test runs BEFORE the edge test, and neither steals the
    # other's lines. `~~>` does not contain `-->`, so this is belt and braces
    # -- but the ordering is the thing that would silently change.
    rep(refuses(lambda: parse(wsrc("[p0] --wat--> [sp]")),
                WC.WRL_UNSUPPORTED_FEATURE, "edge tag"),
        "Q2b) an EDGE line is still judged as an edge -- the route branch did "
        "not capture the arrow forms")
    rep(_typed(lambda: parse(wsrc("[p0] ~wat~ [sp]")),
               WC.WRL_UNSUPPORTED_FEATURE),
        "Q2c) a single-tilde line is not route texture and falls through to "
        "the ordinary rejection")


# =================================================================== Q3
def q3_round_trip():
    """The two halves of the surface agree.

    `_ROUTE_RE` (parse) and the emitter's format string are two spellings of
    one syntax and cannot be merged without building a grammar. They are a
    fork, so the fork is CHECKED: everything the emitter writes, the parser
    reads back to the same world."""
    src = wsrc(ROUTE_LINE)
    g = parse(src)
    txt = F.format_wrl_core(g)
    rep(sem(txt) == sem(src),
        "Q3) parse(format(w)) is the SAME world -- identical "
        "SemanticArtifactID through the formatter (%s)" % sem(src)[:16])
    rep(F.format_wrl_core(parse(txt)) == txt,
        "Q3b) formatting is IDEMPOTENT on a route-bearing world -- the "
        "canonical text is a fixed point")

    # The emitted line is not merely re-parseable, it is the ruled spelling.
    emitted = [ln for ln in txt.splitlines() if "~~" in ln]
    rep(len(emitted) == 1 and W._ROUTE_RE.match(emitted[0]) is not None,
        "Q3c) the emitted route line matches the PARSER's own `_ROUTE_RE` -- "
        "the emitter cannot drift into a dialect only it can write")
    rep(emitted == [ROUTE_LINE],
        "Q3d) ...and it is byte-for-byte the ruled spelling %r" % ROUTE_LINE)

    # A body of every lane width survives the text round trip. `_emit_body`
    # renders ints; a lane that lost its value in the text would come back as
    # a different -- and still legal -- world.
    wide = wsrc(route_line(mb="mc", body="0.1.255.65535"), mailboxes=(MB2,))
    rep(sem(F.format_wrl_core(parse(wide))) == sem(wide),
        "Q3e) a wide body (0.1.255.65535, w=16) survives the round trip "
        "lane-for-lane -- a dropped lane would yield a legal WRONG world")

    # Comments and whitespace are non-semantic on a route line exactly as they
    # are everywhere else; this is the property that makes formatting safe.
    noisy = wsrc("   [p0]   ~~msg~~>   [mb]   (body=0.0.0.7)   ; a route")
    rep(sem(noisy) == sem(src),
        "Q3f) leading/inner whitespace and a `;` comment on a route line are "
        "non-semantic")


# =================================================================== Q4
def q4_order_inert():
    """Authoring order carries no identity -- and still decides `sequence`.

    Both halves matter and they are easy to confuse. The ORDER THE AUTHOR TYPED
    is inert. The CANONICAL order is not: per Q4 a route's zero-based ordinal
    in RouteKey order IS the ADMIT `sequence` it will mint. So a re-ordering
    edit must move nothing at all, while a genuinely new route may renumber its
    neighbours."""
    a = route_line(tag="alpha", body="0.0.0.1")
    b = route_line(tag="beta", body="0.0.0.2")
    c = route_line(tag="gamma", body="0.0.0.3")
    ids = {sem(wsrc(*order)) for order in
           ((a, b, c), (c, b, a), (b, c, a), (c, a, b))}
    rep(len(ids) == 1,
        "Q4) four authoring orders of the same three routes seal to ONE id")
    texts = {F.format_wrl_core(parse(wsrc(*order))) for order in
             ((a, b, c), (c, b, a), (b, a, c))}
    rep(len(texts) == 1,
        "Q4b) ...and format to ONE canonical text -- the formatter is a NORMAL "
        "FORM for route order, not merely order-preserving")

    g = parse(wsrc(c, a, b))
    ident = WC.route_claim_identity(g.routes)
    seqs = sorted((k.route_tag, v[1]) for k, v in ident.items())
    rep(seqs == [("alpha", 0), ("beta", 1), ("gamma", 2)],
        "Q4c) the minted (writer, sequence) pairs follow CANONICAL order, not "
        "the order typed: %s" % (seqs,))
    rep(all(v[0] == WC.ROUTE_WRITER_ID for v in ident.values()),
        "Q4d) every route mints under the reserved writer %d"
        % WC.ROUTE_WRITER_ID)


# =================================================================== Q5
def q5_route_free_unchanged():
    """A route-free world is byte-unchanged, THROUGH THE FORMATTER.

    Commit 2 pinned the three route-free ids for the lowering path. Commit 3
    edits the formatter, which commit 2 never touched, so the pins are re-run
    across format -> parse -> seal. If the emitter had grown a blank line, an
    empty route section, or a trailing separator, these would move."""
    cases = (("none", world()), ("one", world(MB1)), ("two", world(MB1, MB2)))
    for name, src in cases:
        rep(sem(src) == PRE_SLICE_B[name],
            "Q5) the %s-mailbox route-free world still seals to its "
            "pre-Slice-B id %s.." % (name, PRE_SLICE_B[name][:16]))
        rep(sem(F.format_wrl_core(parse(src))) == PRE_SLICE_B[name],
            "Q5b) ...and still does after a FORMAT round trip -- the emitter "
            "grew a route section that a route-free world must not see")
    # Stronger and cheaper to read: the formatted text itself has no trace.
    rep(all("~~" not in F.format_wrl_core(parse(s)) for _n, s in cases),
        "Q5c) no route-free world's canonical text contains the `~~` texture")

    # `wrl_format` claims a BYTE law in its own comment -- a route-free world
    # emits EXACTLY the pre-Slice-B text, "no blank separator, no empty
    # section". Neither Q5 nor Q5b can see it: a stray blank line is
    # non-semantic and washes out at the seal, so the ids stay pinned while
    # every canonical FILE in the tree moves. The mutation round proved the
    # gap by emitting the separator unconditionally, with nothing going red.
    #
    # Stated structurally, not as a literal. Pinning the expected text here
    # would be a second copy of the emitter, which is the defect this round is
    # about; what is actually claimed is that the route SECTION IS ABSENT
    # rather than present-and-empty, and that is visible at the tail.
    for name, src in cases:
        txt = F.format_wrl_core(parse(src))
        tail = txt.rstrip("\n").splitlines()[-1] if txt.strip() else ""
        rep(txt.endswith("\n") and not txt.endswith("\n\n") and "-->" in tail,
            "Q5d) the %s-mailbox route-free world's canonical text ENDS at its "
            "last edge, with no trailing separator -- the route section is "
            "ABSENT, not empty, so no route-free world's BYTES moved" % name)


# =================================================================== Q6
def q6_bootstrap_honest():
    """The bootstrap DSL still has no route -- and now says the true reason.

    `~~` used to be rejected as "a transition class, not an IR v1 edge". That
    is now false twice: a route IS an IR v1.1 construct, and it was never an
    edge (D8). This is the identical correction commit 1 made for `mailbox`,
    and it is here because a rejection message that denies a shipped construct
    costs an author a search through the spec for a change that already
    happened."""
    line = "wire p0 -> sp\n" + ROUTE_LINE + "\n"
    ex = _raised(lambda: W.parse_wrl_bootstrap(line))
    rep(ex is not None and ex.code == WC.WRL_UNSUPPORTED_FEATURE,
        "Q6) the bootstrap surface still refuses `~~` -- a frozen migration "
        "bridge does not grow a route directive")
    rep(ex is not None and "WRL Core" in str(ex),
        "Q6b) ...and points at the surface that DOES have one")
    rep(ex is not None and "not IR v1 edges" not in str(ex),
        "Q6c) ...and no longer claims routes are not IR constructs")
    # NOT `gate a !! b`: a `gate` head is intercepted by the EARLIER
    # reserved-head branch ("outside Forge Semantic IR v1") and never reaches
    # the texture branch this row is about. A plain head is what actually
    # exercises the line under test -- a row that passes for the wrong reason
    # would keep passing after the branch it names had been deleted.
    for tex in ("a !! b", "a == b"):
        rep(refuses(lambda t=tex: W.parse_wrl_bootstrap(t + "\n"),
                    WC.WRL_UNSUPPORTED_FEATURE, "transition classes"),
            "Q6d) `%s` keeps the transition-class message -- only `~~` "
            "graduated" % tex)


# =================================================================== Q7
def q7_laws_reach_the_surface():
    """Every route law reaches text -- and NONE of them is restated in the
    parser.

    The parser's job stops at "this line says a route". Endpoint roles, the
    one-shot source law, the body range, duplicates and the budget are the
    SEAL's, and they are the seal's for a route that arrived from any surface.
    So each row below is proved twice over: the PARSE succeeds and the SEAL
    refuses. A parser that had helpfully re-implemented one of these would
    fail the first half."""
    # -- Q5 of the ruling: source must be a Pulser, `once`, epoch >= 1.
    periodic = HEAD.replace("[pulser:p0](mode=once, epoch=1)",
                            "[pulser:p0](mode=periodic, period=2, phase=0)")
    per_src = periodic + MB1 + TAIL + "\n" + ROUTE_LINE + "\n"
    rep(len(parse(per_src).routes) == 1,
        "Q7) a route from a PERIODIC pulser PARSES -- the surface does not "
        "duplicate the source law")
    rep(refuses(lambda: W.lower_program(per_src, W.parse_wrl_core),
                WC.WRL_ILLEGAL_ROUTE_ENDPOINT, "ONE-SHOT"),
        "Q7b) ...and the SEAL refuses it: Slice B routes are one-shot")

    zero = HEAD.replace("epoch=1", "epoch=0")
    zero_src = zero + MB1 + TAIL + "\n" + ROUTE_LINE + "\n"
    rep(refuses(lambda: W.lower_program(zero_src, W.parse_wrl_core),
                WC.WRL_EPOCH_RANGE, "could never fire"),
        "Q7c) a route from `once(0)` is refused as WRL_EPOCH_RANGE -- epochs "
        "start at 1, so it is a world dead the moment it is written; the "
        "fault is the EPOCH, not the endpoint, and the code says which")

    # -- endpoints
    rep(refuses(lambda: W.lower_program(wsrc(route_line(mb="sp")),
                                        W.parse_wrl_core),
                WC.WRL_ILLEGAL_ROUTE_ENDPOINT, "route target"),
        "Q7d) a route addressed at a SPINNER is refused -- a route addresses "
        "a mailbox")
    rep(refuses(lambda: W.lower_program(wsrc(route_line(src="sp")),
                                        W.parse_wrl_core),
                WC.WRL_ILLEGAL_ROUTE_ENDPOINT, "only a Pulser"),
        "Q7e) a route emitted BY a spinner is refused -- only a Pulser emits")
    rep(_typed(lambda: W.lower_program(wsrc(route_line(mb="nope")),
                                       W.parse_wrl_core),
               WC.WRL_UNKNOWN_ENDPOINT),
        "Q7f) a route to an UNDECLARED mailbox is WRL_UNKNOWN_ENDPOINT -- the "
        "code an undeclared endpoint already had, not a new one")

    # -- body range, read from the TARGET mailbox's declared width
    rep(len(parse(wsrc(route_line(body="0.0.0.256"))).routes) == 1,
        "Q7g) an out-of-range body PARSES -- the range is a property of the "
        "target, which the parser has not resolved yet")
    rep(refuses(lambda: W.lower_program(wsrc(route_line(body="0.0.0.256")),
                                        W.parse_wrl_core),
                WC.WRL_NUMERIC_RANGE, "body"),
        "Q7h) ...and the seal refuses it against mb's w=8 (255 fits, 256 does "
        "not)")
    rep(sem(wsrc(route_line(body="0.0.0.255"))) is not None,
        "Q7i) ...while 255 seals -- the bound is the mailbox's, inclusive")
    rep(sem(wsrc(route_line(mb="mc", body="0.0.0.256"),
                 mailboxes=(MB1, MB2))) is not None,
        "Q7j) ...and the SAME body seals when addressed at mc (w=16) -- the "
        "bound is read from the target, never from a global")

    # -- duplicates and the budget, written in text
    dup = route_line(body="0.0.0.1"), route_line(body="0.0.0.2")
    rep(refuses(lambda: W.lower_program(wsrc(*dup), W.parse_wrl_core),
                WC.WRL_DUPLICATE_ROUTE, "one route declared twice"),
        "Q7k) two text lines with the same RouteKey and DIFFERENT bodies are "
        "one route declared twice -- the body is not part of the key")
    # SPREAD over two firing epochs. Commit 4's co-firing law makes the whole
    # budget unreachable from one pulser, so a budget row written on a single
    # pulser would now be refused by the WRONG law and would keep "passing"
    # after the budget itself had been deleted.
    over = tuple(route_line(src=("p0" if i < WC.MAX_ROUTE_COFIRE else "p1"),
                            tag="t%d" % i, body="0.0.0.%d" % i)
                 for i in range(WC.MAX_ASYNC_ROUTES + 1))
    rep(refuses(lambda: W.lower_program(wsrc(*over, two_pulsers=True),
                                        W.parse_wrl_core),
                WC.WRL_ROUTE_BUDGET, "the bound is"),
        "Q7l) %d routes in text exceed the budget of %d"
        % (WC.MAX_ASYNC_ROUTES + 1, WC.MAX_ASYNC_ROUTES))
    rep(sem(wsrc(*over[:-1], two_pulsers=True)) is not None,
        "Q7m) ...and exactly %d seal -- the budget is inclusive"
        % WC.MAX_ASYNC_ROUTES)


# =================================================================== Q8
def q8_writer_reservation():
    """Writer %d is reserved by COMPATIBILITY, not by the document.

    The ruling is explicit that `ScenarioV1` must NOT be narrowed globally. A
    scenario is authored before it is bound to a world and is meant to be
    reusable; writer 15 is perfectly legal in every route-free world, which is
    every world shipped so far. Narrowing the validator would retroactively
    invalidate stored scenarios over a property of a world they may never run
    against.""" % WC.ROUTE_WRITER_ID
    r_prog = W.lower_program(wsrc(ROUTE_LINE), W.parse_wrl_core)
    f_prog = W.lower_program(wsrc(), W.parse_wrl_core)

    def scen(prog, wid):
        s = SC.demo_scenario(prog.semantic_artifact_id)
        s["epochs"][0]["claims"][0]["writer_id"] = wid
        return s

    def compat(prog, wid):
        return SC.check_world_compatibility(scen(prog, wid), prog.artifact,
                                            prog.semantic_artifact_id)

    rep(refuses(lambda: compat(r_prog, WC.ROUTE_WRITER_ID),
                WC.WRL_ROUTE_WRITER_RESERVED, "RESERVED"),
        "Q8) against a ROUTE-BEARING world, a scenario claim under writer %d "
        "is refused" % WC.ROUTE_WRITER_ID)
    # Callable form on purpose. These two rows assert that something is
    # ACCEPTED, so the way they break is by RAISING -- and an eager bool would
    # let the section guard rename the failure after its neighbour. The
    # mutation round found exactly that: widening the reservation to every
    # world was reported as "Q8 raised", which reads as the reservation being
    # broken when in fact it had been made too strong.
    rep(lambda: compat(f_prog, WC.ROUTE_WRITER_ID) is not None,
        "Q8b) against a ROUTE-FREE world the very same claim is ACCEPTED -- "
        "the reservation is a property of the pairing, not of the scenario")
    rep(lambda: compat(r_prog, WC.ROUTE_WRITER_ID - 1) is not None,
        "Q8c) writer %d is accepted against the route-bearing world -- only "
        "the top of the namespace is reserved"
        % (WC.ROUTE_WRITER_ID - 1))

    # The document validator must stay ignorant. This is the row that fails if
    # somebody "helpfully" moves the check into validate_scenario_v1.
    rep(SC.validate_scenario_v1(scen(r_prog, WC.ROUTE_WRITER_ID)) is not None,
        "Q8d) `validate_scenario_v1` still ACCEPTS writer %d -- ScenarioV1 is "
        "NOT narrowed" % WC.ROUTE_WRITER_ID)
    rep(SC.scenario_digest(scen(r_prog, WC.ROUTE_WRITER_ID)).startswith("scen-"),
        "Q8e) ...and such a scenario still has a ScenarioDigest: it is a "
        "well-formed document that is merely incompatible with THIS world")

    # Located, and located at the epoch that actually carries the claim.
    s = SC.demo_scenario(r_prog.semantic_artifact_id)
    s["epochs"][4]["claims"][0]["writer_id"] = WC.ROUTE_WRITER_ID
    ex = _raised(lambda: SC.check_route_writer_reservation(s, r_prog.artifact))
    rep(ex is not None and "epoch 5" in str(ex),
        "Q8f) the rejection NAMES the offending epoch (5), so the author is "
        "not left scanning a nine-epoch document")
    rep(ex is not None and getattr(ex, "field_path", None)
        and "writer_id" in ex.field_path,
        "Q8g) ...and carries a field_path into the claim: %r"
        % (getattr(ex, "field_path", None),))

    # The reserved id is READ, not spelled. A relative law: it shows the check
    # is driven by the constant. binding_run47 P0b pins the constant itself.
    rep(WC.ROUTE_WRITER_ID == (1 << AD.WK) - 1,
        "Q8h) the reserved writer is still ADMIT's top writer id (2**%d - 1 = "
        "%d) -- widening WK moves the reservation with it"
        % (AD.WK, (1 << AD.WK) - 1))

    # The composed door is the one production uses; both halves must fire
    # through it, or a call site will grow one and not the other.
    other = f_prog.semantic_artifact_id
    rep(_typed(lambda: SC.check_world_compatibility(
        scen(r_prog, 1), r_prog.artifact, other),
        SC.WRL_SCENARIO_WORLD_MISMATCH),
        "Q8i) the composed door still enforces the v0.4-0 world BINDING -- "
        "adding the reservation did not displace the check it joined")


# =================================================================== Q9
def q9_draft_cannot_lose_a_route():
    """A route-bearing world cannot silently become a route-free one.

    A `WorldDraft` stores a world as `(objects, edges)` and that pair is what
    the entire authoring workspace is built on -- undo snapshots, the
    ForgeProjectV2 draft block, the v0.6-0 recovery journal, the canvas
    reconciliation. A route is neither an object nor an edge, so it was
    invisible to all of it.

    Measured before the guard was written: opening the one-route world for
    editing produced NO error and yielded `PRE_SLICE_B["one"]` -- the route-free
    twin, a perfectly good world with a perfectly good id. That is the shape of
    failure this whole slice exists to prevent, so it is closed in the same
    commit that made it reachable."""
    rsrc = wsrc(ROUTE_LINE)
    rprog = W.lower_program(rsrc, W.parse_wrl_core)
    fprog = W.lower_program(wsrc(), W.parse_wrl_core)

    rep(refuses(lambda: D.new_draft(rprog, "dr"),
                D.WRL_DRAFT_LOSSY_WORLD, "does not survive"),
        "Q9) opening a route-bearing world as a draft is REFUSED, typed")
    ex = _raised(lambda: D.new_draft(rprog, "dr"))
    rep(ex is not None and PRE_SLICE_B["one"][:20] in str(ex),
        "Q9b) ...and the message names the world it WOULD have become (%s..) "
        "-- the loss is legal, which is what makes it dangerous"
        % PRE_SLICE_B["one"][:16])

    # The guard is COMPUTED, so it costs route-free worlds nothing.
    d = D.new_draft(fprog, "dr")
    rep(d.candidate_semantic_id == fprog.semantic_artifact_id
        and d.semantic_revision == 0,
        "Q9c) a route-free world still opens unchanged at revision 0 -- the "
        "guard is a round-trip, not a construct blacklist")

    # The paste door: same refusal, and the draft must be UNTOUCHED, because
    # nothing about the author's text is wrong.
    res = D.replace_world_source(d, {
        "replace_version": D.REPLACE_VERSION, "replace_id": "rr",
        "draft_id": "dr", "base_revision": 0, "source": rsrc})
    codes = [x["code"] for x in res["diagnostics"]]
    rep(codes == [D.WRL_DRAFT_LOSSY_WORLD],
        "Q9d) pasting route-bearing source into a draft is refused with the "
        "same typed code (got %s)" % codes)
    rep(d.semantic_revision == 0
        and d.candidate_semantic_id == fprog.semantic_artifact_id
        and not d._history,
        "Q9e) ...and the draft is UNTOUCHED -- no revision, no snapshot, no "
        "undo entry; there is nothing in the text for the author to repair")
    rep(res["status"] in D.REPLACE_STATUS,
        "Q9f) the refusal reports one of the FOUR frozen terminal states "
        "(%r) -- a fifth status is a contract change, not a language one; "
        "flagged to GPT-5.6" % res["status"])

    # Q9d/Q9e cannot, on their own, tell REFUSED from SILENTLY ACCEPTED. The
    # route-free twin of that source is the draft's own current world, so a
    # missing guard reaches step (5), reports `semantic_noop`, and leaves the
    # draft at revision 0 with the right candidate -- Q9e green for the wrong
    # reason. The mutation round found exactly this. The discriminating case
    # is a paste whose LOST world is a DIFFERENT world.
    twin = sem(wsrc(mailboxes=(MB1, MB2)))
    rep(twin == PRE_SLICE_B["two"] != fprog.semantic_artifact_id,
        "Q9h) the two-mailbox route-free twin (%s..) is NOT the draft's "
        "current world -- without this the next row is vacuous" % twin[:16])
    res3 = D.replace_world_source(d, {
        "replace_version": D.REPLACE_VERSION, "replace_id": "rx",
        "draft_id": "dr", "base_revision": 0,
        "source": wsrc(route_line(mb="mc"), mailboxes=(MB1, MB2))})
    rep([x["code"] for x in res3["diagnostics"]] == [D.WRL_DRAFT_LOSSY_WORLD],
        "Q9i) a paste whose lost world DIFFERS from the current one is refused "
        "the same way -- the guard is not a no-op detector")
    rep(d.semantic_revision == 0
        and d.candidate_semantic_id == fprog.semantic_artifact_id
        and not d._history,
        "Q9j) ...and the draft did NOT quietly become %s.. -- this is the "
        "substitution Q9e is structurally unable to see" % twin[:16])

    # And the guard must not be a route check wearing a general name: an
    # ordinary invalid world still gets the ordinary diagnosis.
    broken = wsrc().replace("[spinner:sp] --socket--> [orb:ob]",
                            "[spinner:sp] --socket--> [nope]")
    res2 = D.replace_world_source(d, {
        "replace_version": D.REPLACE_VERSION, "replace_id": "r2",
        "draft_id": "dr", "base_revision": 0, "source": broken})
    rep([x["code"] for x in res2["diagnostics"]] == [WC.WRL_UNKNOWN_ENDPOINT],
        "Q9g) an ordinary illegal world is still diagnosed as itself "
        "(WRL_UNKNOWN_ENDPOINT), not as a loss -- the guard defers to the seal")


# =================================================================== Q10
def q10_native():
    """The frozen demo world still folds three ways.

    Commit 3 edited the PARSER and the FORMATTER, both of which sit directly
    upstream of the term the reducer folds."""
    lp = W.lower_program(B5.CORE_SRC, W.parse_wrl_legacy_document)
    batches = B5._batches_from_program(lp)
    term, K, films_ref, films_gold = B47._fold(lp.fixture, batches)
    rep(films_ref == films_gold,
        "Q10) the frozen demo world folds ic_ref == golden over %d epochs "
        "(unchanged by the `~~` surface)" % K)
    if SKIP_NATIVE:
        print("       (native skipped: TRVM_SKIP_NATIVE=1)")
        return False
    import binding_run3o as O
    dec_nat = O._decode_fold(O.native(term), K)
    claims_nat = O._project_claims(dec_nat, epoch0=1)
    films_nat = [O._film(dec_nat[e][0], claims_nat[e], e + 1) for e in range(K)]
    nat_ok = films_nat == films_ref == films_gold
    rep(nat_ok, "Q10b) ic_ref == ic32 == golden")
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
    print("[BINDING wrl-sliceB-c3] the `~~` surface")
    t0 = time.time()
    section(q0_ruled_spelling)
    section(q1_body_required)
    section(q2_texture_is_diagnosed)
    section(q3_round_trip)
    section(q4_order_inert)
    section(q5_route_free_unchanged)
    section(q6_bootstrap_honest)
    section(q7_laws_reach_the_surface)
    section(q8_writer_reservation)
    section(q9_draft_cannot_lose_a_route)
    native_ok = section(q10_native)

    print()
    if _FAILED:
        for f in _FAILED:
            print("  FAILED: %s" % f)
        print("VERDICT: FAILURES (%d) in %ds" % (len(_FAILED), time.time() - t0))
        return 1
    mode = ("PASS_REF_ONLY (native skipped)" if SKIP_NATIVE
            else ("PASS_REF_AND_NATIVE" if native_ok
                  else "REF_ONLY (native MISMATCH)"))
    print("VERDICT: %s -- Slice B Commit 3 (the `~~` surface) closed in %ds"
          % (mode, time.time() - t0))
    print("NOTE: still NOT frozen. A route can now be WRITTEN, canonicalized, "
          "sealed, formatted and refused for every reason it should be -- and "
          "it still does nothing at runtime. Commit 4 folds it; freeze after "
          "that.")
    return 0 if (SKIP_NATIVE or native_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
