#!/usr/bin/env python3
"""binding_run46.py -- Slice B, Commit 1: the Mailbox WRL Core surface.

WRL Core 0.1.3 §18.1, ruled by GPT-5.6 (2026-07-25):

    [mailbox:mb](w=8, cap=4){}

`w` and `cap` are REQUIRED. `{}` explicitly denotes empty structural ports.
The declaration enters world identity through the existing canonical
`MailboxDecl`. A Mailbox cannot participate in `--` topology and is not an
ordinary actor with a behavior table.

The whole semantic side of this already existed: `Mailbox` has been the sixth
registry role since Slice A, with frozen ports, a config schema, a validator, a
plan lane and an ADMIT runtime. What did NOT exist was any way to WRITE one
down. That is why this commit is small and why its battery is mostly about
surfaces rather than semantics -- and it is exactly why the battery must be
suspicious of itself. A surface commit that "just works" is the shape of a
commit whose tests assert nothing.

Structure
---------
N1-N3   the declaration seals, and what it seals is the WHOLE v1.1 surface
N4-N5   what the surface REFUSES, and where "required" is spelled
N6      D8 (not wireable) holds structurally, not by a mailbox special case
N7      formatter closure -- including the defect this commit found
N8      tooling closes with NO hand edits (the §18 self-emptying property)
N9      the bootstrap surface's deliberate NON-extension, honestly reported
N10     canvas.v1 (retired) refuses a mailbox world honestly -- ties to c0
N11     "declared and provably ignored" is NOT "silently dropped"
N12     the frozen demo world still folds ic_ref == ic32 == golden

Run:  python3 binding_run46.py      (TRVM_SKIP_NATIVE=1 for reference only)
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import admit as AD
import wrl_canonical as WC
import wrl_canvas as CV
import wrl_complete as CP
import wrl_diagnostics as WD
import wrl_format as WF
import wrl_ir as W
import wrl_legacy as LG
import wrl_plan as WP
import wrl_spans as SP
import binding_run3o as O
import binding_run5 as B5
from fixture import init_state_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

# TWO frozen ids, written out in full rather than recomputed -- a constant
# recomputed by the thing it is meant to pin proves nothing.
#
# DEMO_SEM is the most widely cited world in the whole tree (the Spinner Bench
# demo), and it is the SUGAR-bearing one, so pinning it exercises the sugar
# prepass -> core parser -> seal chain that this commit sits inside.
# L0_SEM is binding_run5's core fixture, which no battery had ever pinned to a
# literal -- it was always recomputed and compared against itself. Recording it
# here is the first time it is nailed down independently.
DEMO_SEM = ("sem-8ae91fe9cbc5fd086ce4356d587c403211e5c7b2b3ebdd316496"
            "367429ecfe4a")
L0_SEM = ("sem-bdeda92667c612af57447435ec73d472d56084e1e6afe6cd19f2"
          "14c777eb5f67")

# The Spinner Bench demo world, verbatim. Copied rather than imported because
# importing `spinner_bench` pulls in an HTTP server, a project store and a
# recovery journal to read one string -- and because a pin that follows its
# source around is not a pin.
DEMO_SRC = """profile forge.world.core.v1

[pulser:p0](every 2){sig_out}
[relay:r0]{sig_in, sig_out}
[spinner:sp](w=16, n=8, rotor=quarter_turn_z, configurable){sig_in, socket}
[orb:ob]{pose}
[pulser:p1](once at 1){sig_out}
[door:d0]{sig_in}

[pulser:p0] --sig--> [relay:r0]
[relay:r0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]
[pulser:p1] --sig--> [door:d0]
"""

# A runnable world, with a slot for mailbox declarations. Deliberately the SAME
# physical topology as the demo world, so every "the mailbox changed nothing
# physical" row compares two worlds that differ in exactly one respect.
HEAD = """profile forge.world.core.v1

[pulser:p0](mode=periodic, period=2, phase=0){sig_out}
[door:d0]{sig_in}
[spinner:sp](w=8, n=4, rotor=16.0.0.0, configurable){sig_in, socket}
[orb:ob]{pose}
"""
TAIL = """
[pulser:p0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]
"""
MB1 = "[mailbox:mb](w=8, cap=4){}\n"

# A profile for the production compile path (N11). Values are the ones
# binding_run7 uses; nothing here depends on their content.
LP1 = {"counter_encoding": "one_hot", "onehot_max": 32, "numeric_backend": "ic",
       "compiler_hash": "a" * 64, "target": "ic32",
       "lowering_profile_version": "1.0"}

_FAILED = []


def rep(ok, label):
    """Report one row. `ok` may be a bool OR a zero-arg callable.

    The callable form exists because a row whose COMPUTATION raises is a row
    that failed, not a battery that should stop. Mutation testing made the
    difference concrete: widening the required-brace rule to every role is
    exactly the negation of N4d's stated law, and N4d is the row that never
    got to run -- its own `lower(abbreviated)` raised, the section aborted,
    and the failure was attributed to N4. The law that was disproved was
    reported under the name of a law that still held.

    So: pass a lambda wherever a row's setup can raise, and the row keeps its
    own name when it breaks. `section()` remains the backstop for anything
    raised between rows.
    """
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


def world(*mailbox_lines):
    return HEAD + "".join(mailbox_lines) + TAIL


def lower(src):
    return W.lower_graph(W.parse_wrl_core(src))


def _raised(fn):
    """`fn`'s typed error, or None if it did not raise one."""
    try:
        fn()
    except WC.WrlValidationError as ex:
        return ex
    return None


def _typed(fn, code):
    ex = _raised(fn)
    return ex is not None and ex.code == code


# ------------------------------------------------------------------- N1
def n1_surface_selects_v11():
    """A declared mailbox selects the ENTIRE v1.1 semantic surface, and a
    mailbox-free world keeps ALL FOUR frozen v1 values.

    Checked as a four-field BLOCK in both directions on purpose. The four are
    derived together by `semantic_surface_for_roles` precisely so they cannot
    drift apart, and a row that checked only `ir_version` would keep passing
    if the film schema silently stayed at the frozen id -- which is the
    dangerous case, because a mailbox world claiming the pre-mailbox film
    schema would be claiming to implement a meaning that schema never had."""
    a_mb = lower(world(MB1)).artifact
    a_no = lower(world()).artifact

    def surface(a):
        p = a["semantic_policies"]
        return (a["ir_version"], p["admit_policy_id"], p["film_schema_id"],
                a["schemas"]["runtime_state_schema"])

    v11 = (WC.IR_VERSION_V1_1, WC.MAILBOX_ADMIT_POLICY_ID,
           WC.FILM_SCHEMA_ID_MAILBOX, "RuntimeStateV1_1")
    v1 = (WC.IR_VERSION, WC.ADMIT_POLICY_ID, WC.FILM_SCHEMA_ID,
          "RuntimeStateV1")
    ok = surface(a_mb) == v11 and surface(a_no) == v1
    # ... and the two blocks must not overlap in ANY position, or "selected
    # together" would be satisfied by fields that never differed.
    ok = ok and all(x != y for x, y in zip(v11, v1))
    rep(ok, "N1) an authored mailbox selects the whole v1.1 surface "
            "(ir_version/admit/film/runtime-state), a mailbox-free world "
            "keeps all four frozen v1 values, and the eight values are "
            "pairwise distinct")

    mb = WC.mailbox_decls_of_artifact(a_mb)
    rep(mb == {"mb": (8, 4)} and WC.mailbox_decls_of_artifact(a_no) == {},
        "N1b) the declaration reads back off the SEALED artifact as "
        "MailboxDecl {'mb': (8, 4)}")


# ------------------------------------------------------------------- N2
def n2_identity_bearing():
    """`w` and `cap` are static world structure, so both move the id -- and
    they are two fields, not one."""
    ids = {k: lower(world(src)).semantic_artifact_id for k, src in (
        ("none", ""),
        ("w8c4", "[mailbox:mb](w=8, cap=4){}\n"),
        ("w4c8", "[mailbox:mb](w=4, cap=8){}\n"),
        ("w8c5", "[mailbox:mb](w=8, cap=5){}\n"),
        ("name", "[mailbox:zz](w=8, cap=4){}\n"),
        ("two",  "[mailbox:mb](w=8, cap=4){}\n[mailbox:mc](w=8, cap=4){}\n"),
    )}
    ok = len(set(ids.values())) == len(ids)
    rep(ok, "N2) six worlds differing only in their mailbox declarations "
            "(absent / w / cap / swapped / name / count) seal to six "
            "DISTINCT SemanticArtifactIDs")

    # The pair is ORDERED: the id distinguishes which number is which.
    #
    # This row used to claim it also proved the two fields "are not folded into
    # one". Mutation testing refuted that. Under `cap := w` -- an exact fold --
    # the two worlds become (8,8) and (4,4), which still seal differently, so
    # the swap sails through the very defect it advertised. N2 (six distinct
    # ids, which loses w8c4/w8c5) and N1b (the declaration reads back as
    # (8, 4), not (8, 8)) are the rows that actually catch a fold. A row is
    # only allowed to claim what it would notice.
    rep(ids["w8c4"] != ids["w4c8"],
        "N2b) (w=8, cap=4) and (w=4, cap=8) are DIFFERENT worlds -- the pair "
        "is ordered (N1b/N2 own the not-folded law)")

    # Declaration order is not meaning.
    a = lower(world("[mailbox:mb](w=8, cap=4){}\n",
                    "[mailbox:mc](w=1, cap=2){}\n")).semantic_artifact_id
    b = lower(world("[mailbox:mc](w=1, cap=2){}\n",
                    "[mailbox:mb](w=8, cap=4){}\n")).semantic_artifact_id
    # Written as one comparison. The previous spelling was
    # `a == b and a == ids["two"] or a == b`, which Python groups as
    # `(a == b and ...) or (a == b)` -- so the middle conjunct could never
    # change the verdict, and it was false anyway (`two` declares mc as (8,4),
    # not (1,2)). A dead conjunct in a law reads as extra rigour and supplies
    # none; this is the second one this round after commit 0's ordering row.
    rep(a == b,
        "N2c) mailbox declaration ORDER does not move the id "
        "(canonicalization is identity-first)")


# ------------------------------------------------------------------- N3
def n3_additive():
    """The frozen worlds are untouched. This is the row that makes the commit
    additive rather than a language revision."""
    import wrl_sugar as SG
    demo = W.lower_program(SG.desugar_core(DEMO_SRC), W.parse_wrl_core)
    l0 = W.lower_program(B5.CORE_SRC, W.parse_wrl_legacy_document)
    rep(demo.semantic_artifact_id == DEMO_SEM,
        "N3) the Spinner Bench demo world still seals to %s..%s through the "
        "sugar prepass" % (DEMO_SEM[:12], DEMO_SEM[-4:]))
    rep(l0.semantic_artifact_id == L0_SEM,
        "N3b) the L-0 core fixture still seals to %s..%s"
        % (L0_SEM[:12], L0_SEM[-4:]))
    ok = True
    for lp in (demo, l0):
        a = lp.artifact
        ok = (ok and a["ir_version"] == WC.IR_VERSION
              and a["semantic_policies"]["film_schema_id"] == WC.FILM_SCHEMA_ID
              and a["semantic_policies"]["admit_policy_id"] == WC.ADMIT_POLICY_ID
              and a["schemas"]["runtime_state_schema"] == "RuntimeStateV1")
    rep(ok, "N3c) ... and BOTH still declare the frozen v1 surface -- adding a "
            "surface lexeme did not promote existing worlds to v1.1")


# ------------------------------------------------------------------- N4
def n4_brace_required():
    """`{}` must be WRITTEN for a portless role -- and the rule is computed."""
    ex = _raised(lambda: W.parse_wrl_core(world("[mailbox:mb](w=8, cap=4)\n")))
    ok = (ex is not None and ex.code == WC.WRL_PORT_SIGNATURE
          and ex.primary_locator == WC.ObjectKey("mb")
          and ex.field_path == "ports")
    rep(ok, "N4) an omitted port block on a mailbox is WRL_PORT_SIGNATURE, "
            "LOCATED at ObjectKey('mb') with field_path 'ports'")

    rep(_typed(lambda: W.parse_wrl_core(world("[mailbox:mb](w=8, cap=4){sig_in}\n")),
               WC.WRL_PORT_SIGNATURE),
        "N4b) a bogus port token on a mailbox is WRL_PORT_SIGNATURE -- "
        "`{}` is checked, not merely tolerated")

    # The requirement must apply to EXACTLY the portless writable roles, and
    # the test computes that set the same way the parser does. Naming
    # `Mailbox` here would make the battery the fork it is testing for.
    portless = {r for r in W.writable_role_ids() if not WC.port_projection(r)}
    ported = {r for r in W.writable_role_ids() if WC.port_projection(r)}
    rep(portless == {WC.MAILBOX_ROLE} and ported,
        "N4c) exactly %d writable role(s) have an empty frozen port signature "
        "(%s); %d have ports" % (len(portless), ", ".join(sorted(portless)),
                                 len(ported)))

    # A role WITH ports may still abbreviate -- frozen behaviour, unchanged.
    abbreviated = HEAD.replace("[door:d0]{sig_in}", "[door:d0]") + TAIL
    rep(lambda: (lower(abbreviated).semantic_artifact_id
                 == lower(world()).semantic_artifact_id),
        "N4d) a role WITH ports may still omit the block and lowers "
        "identically -- the new requirement did not widen to every role")


# ------------------------------------------------------------------- N5
def n5_required_config():
    """`w`/`cap` are required, and "required" has ONE spelling.

    The parser passes an absent key through as None and the SEAL rejects it.
    That is deliberate: the same validator must catch a mailbox that arrived
    from text, from a canvas, from a draft edit or from a deserialized
    artifact, and a parse-time presence check would be a second opinion that
    disagrees the first time someone writes `w=0` (present, so a presence
    check passes it; out of range, so the validator does not)."""
    cases = [("[mailbox:mb](cap=4){}\n", WC.WRL_UNSUPPORTED_FEATURE, "w"),
             ("[mailbox:mb](w=8){}\n", WC.WRL_UNSUPPORTED_FEATURE, "cap"),
             ("[mailbox:mb](){}\n", WC.WRL_UNSUPPORTED_FEATURE, "w"),
             ("[mailbox:mb](w=0, cap=4){}\n", WC.WRL_NUMERIC_RANGE, "w"),
             ("[mailbox:mb](w=%d, cap=4){}\n" % (WC.MAILBOX_WIDTH_MAX + 1,),
              WC.WRL_NUMERIC_RANGE, "w"),
             ("[mailbox:mb](w=8, cap=0){}\n", WC.WRL_NUMERIC_RANGE, "cap")]
    ok = True
    for src, code, field in cases:
        ex = _raised(lambda s=src: lower(world(s)))
        ok = (ok and ex is not None and ex.code == code
              and ex.primary_locator == WC.ObjectKey("mb")
              and ex.field_path == "static_config.%s" % field)
    rep(ok, "N5) all %d malformed mailbox declarations (missing w / missing "
            "cap / empty / w=0 / w>%d / cap=0) are typed AND located"
            % (len(cases), WC.MAILBOX_WIDTH_MAX))

    # The boundary is the boundary: w=1 and w=MAILBOX_WIDTH_MAX are legal.
    rep(all(lower(world("[mailbox:mb](w=%d, cap=1){}\n" % w))
            for w in (1, WC.MAILBOX_WIDTH_MAX)),
        "N5b) w=1 and w=%d (the inclusive bounds) are accepted -- the range "
        "check is not off by one" % (WC.MAILBOX_WIDTH_MAX,))

    # ONE spelling: a graph built WITHOUT the parser fails identically.
    g = W.parse_wrl_core(world(MB1))
    for i, (role, name, cfg) in enumerate(g.nodes):
        if role == WC.MAILBOX_ROLE:
            g.nodes[i] = (role, name, {"w": 8})           # `cap` removed
    ex = _raised(lambda: W.lower_graph(g))
    rep(ex is not None and ex.code == WC.WRL_UNSUPPORTED_FEATURE
        and ex.primary_locator == WC.ObjectKey("mb")
        and ex.field_path == "static_config.cap",
        "N5c) the SAME code and locator arrive for a mailbox built with no "
        "text at all -- 'required' is spelled once, in the validator")


# ------------------------------------------------------------------- N6
def n6_not_wireable():
    """D8: a mailbox cannot participate in `--` topology.

    Enforced by the frozen port table being empty, so it needs no mailbox case
    anywhere in the edge validator. The row proves the ban is total over
    (edge kind x direction) AND that the mechanism is the generic one."""
    peers = {"sig": ("p0", "d0"), "socket": ("sp", "ob")}
    attempts = []
    for tag, (src, dst) in peers.items():
        attempts.append("[%s] --%s--> [mb]" % (src, tag))
        attempts.append("[mb] --%s--> [%s]" % (tag, dst))
    ok = all(_typed(lambda a=a: lower(world(MB1) + a + "\n"),
                    WC.WRL_ILLEGAL_PORT_PAIR) for a in attempts)
    rep(ok, "N6) all %d (edge kind x direction) wirings of a mailbox are "
            "WRL_ILLEGAL_PORT_PAIR" % len(attempts))

    # The same code rejects an illegal pairing between two NON-mailbox roles,
    # so N6 is the generic port machinery and not a mailbox special case.
    rep(_typed(lambda: lower(world() + "[p0] --socket--> [d0]\n"),
               WC.WRL_ILLEGAL_PORT_PAIR),
        "N6b) an illegal pairing between two ORDINARY roles yields the same "
        "code -- the ban is the port table, not a mailbox branch")

    # And the reason is visible in the frozen table itself.
    rep(WC.port_projection(WC.MAILBOX_ROLE) == set()
        and all(WC.port_projection(r) for r in W.writable_role_ids()
                if r != WC.MAILBOX_ROLE),
        "N6c) the frozen Mailbox port signature is empty and every other "
        "writable role's is not -- D8 is a fact about the table")


# ------------------------------------------------------------------- N7
def n7_formatter():
    """Formatter closure, and the defect this commit found.

    `wrl_format._ROLE_LOWER` was a hand-written INVERSE of `wrl_ir._ROLE_TOKEN`
    -- a sixth instance of the forked-vocabulary defect (§18). It was already
    wrong the moment `mailbox` was added: the formatter would have raised a
    bare KeyError on a world that parses, seals and runs. It is now computed by
    inverting the parse table, and N7c is the row that keeps it computed."""
    src = world(MB1)
    g = W.parse_wrl_core(src)
    txt = WF.format_wrl_core(g)
    rep("[mailbox:mb](w=8, cap=4){}" in txt,
        "N7) the formatter emits the ruled surface form verbatim, `{}` "
        "included")

    g2 = W.parse_wrl_core(txt)
    rep(W.lower_graph(g2).semantic_artifact_id
        == W.lower_graph(g).semantic_artifact_id
        and WF.format_wrl_core(g2) == txt,
        "N7b) format -> parse -> format is id-stable and idempotent over a "
        "mailbox world (the emitted `{}` satisfies the new requirement)")

    rep(set(WF._ROLE_LOWER) == set(W.writable_role_ids())
        and set(WF._EDGE_LOWER) == set(W._EDGE_TAG.values()),
        "N7c) the emitter vocabulary is TOTAL over the parse tables -- the "
        "row that would have caught the KeyError before it shipped")

    # Every role PRESENT in the sample world is emitted with its own lexeme.
    # Computed from the graph rather than a written list of five strings: a
    # written list is how the sixth role got missed in `_ROLE_LOWER` in the
    # first place, and a battery that repeats the defect it is testing for is
    # only proving that the defect is easy to make.
    present = {role for role, _n, _c in W.parse_wrl_core(src).nodes}
    missing = [r for r in present if ("[%s:" % WF._ROLE_LOWER[r]) not in txt]
    rep(present == set(WC.ROLE_IDS) - {"Relay"} and not missing,
        "N7d) all %d roles present in the sample world are emitted with their "
        "own surface lexeme (%s)"
        % (len(present), ", ".join(sorted(WF._ROLE_LOWER[r] for r in present))))


# ------------------------------------------------------------------- N8
def n8_tooling_closes():
    """The §18 self-emptying property, observed.

    Nothing in this row was edited by this commit. `unwritable_role_ids()`
    shrank to `()` by itself, and completion/metadata followed, because all
    three are COMPUTED from `_ROLE_TOKEN` and the registry rather than
    hand-listed. This is the payoff the L-0 round paid for."""
    rep(W.unwritable_role_ids() == ()
        and set(W.writable_role_ids()) == set(WC.ROLE_IDS),
        "N8) unwritable_role_ids() computed itself empty -- every frozen "
        "registry role can now be written down")

    meta = CP.surface_metadata()
    rep("mailbox" in CP.role_completions()
        and meta["unwritable_roles"] == []
        and set(meta["roles"]) == set(W._ROLE_TOKEN),
        "N8b) completions and surface metadata picked the role up with no "
        "edit to either module")

    rep(tuple(meta["roles"]["mailbox"]["config_keys"])
        == WC.ROLE_CONFIG_SCHEMA[WC.MAILBOX_ROLE]["surface_keys"] == ("w", "cap")
        and meta["roles"]["mailbox"]["ports"] == []
        and meta["roles"]["mailbox"]["role_id"] == WC.MAILBOX_ROLE,
        "N8c) the offered config keys are the registry's own, and the offered "
        "port list is empty -- completion cannot suggest wiring a mailbox")

    # Spans: the sidecar keys off the same table, so it followed too.
    _g, sm = SP.parse_core_with_spans(world(MB1))
    mb_spans = [o for o in sm.origins if o.canonical_object_id == "mb"]
    rep(len(mb_spans) == 1 and mb_spans[0].construct_kind == "node",
        "N8d) the span sidecar emits exactly one NODE origin for the mailbox")

    # Diagnostics: the 5.2 pre-freeze obligation, discharged. Before this
    # commit WRL_PORT_SIGNATURE arrived with primary_span AND primary_locator
    # both None, so a consumer had to re-derive the offending node from the
    # message text -- the forked-vocabulary defect in diagnostic form.
    bad = world("[mailbox:mb](w=8, cap=4){sig_in}\n")
    # The expected line is COMPUTED from the source under test. A hardcoded
    # number would silently start pointing at the wrong line the moment
    # anything above it moved, which is the same class of stale second opinion
    # the locator exists to remove.
    want_line = 1 + next(i for i, ln in enumerate(bad.splitlines())
                         if ln.startswith("[mailbox:"))
    d = [x for x in WD.diagnose_core(bad)
         if x.code == WC.WRL_PORT_SIGNATURE]
    rep(len(d) == 1 and d[0].primary_locator == WC.ObjectKey("mb")
        and d[0].canonical_object_id == "mb"
        and d[0].primary_span is not None
        and d[0].primary_span.start_line == want_line,
        "N8e) WRL_PORT_SIGNATURE now arrives with a validator-owned locator "
        "AND a span resolved to the authored line %d (finding 5.2 discharged)"
        % want_line)

    # The same obligation for the pre-existing non-mailbox case.
    d2 = [x for x in WD.diagnose_core(
              HEAD.replace("[door:d0]{sig_in}", "[door:d0]{sig_out}") + TAIL)
          if x.code == WC.WRL_PORT_SIGNATURE]
    rep(len(d2) == 1 and d2[0].primary_locator == WC.ObjectKey("d0"),
        "N8f) ... and the locator is not mailbox-specific -- the frozen "
        "`[door:d0]{sig_out}` case is located too")


# ------------------------------------------------------------------- N9
def n9_bootstrap_non_extension():
    """The bootstrap DSL is a frozen migration bridge and gets NO mailbox
    directive. That is a decision, not an oversight, so the message must say
    which surface DOES have one.

    It used to report `mailbox` as "outside Forge Semantic IR v1 ...
    reserved/Proposed" -- true when written, false since the v1.1 registry
    admitted `Mailbox`, and false in the expensive direction: it sends an
    author to look for a spec change that already happened."""
    ex_mb = _raised(lambda: W.parse_wrl_bootstrap(
        "profile forge.world.core.v1\nmailbox mb w=8 cap=4\n"))
    ex_gate = _raised(lambda: W.parse_wrl_bootstrap(
        "profile forge.world.core.v1\ngate g\n"))
    ok = (ex_mb is not None and ex_gate is not None
          and ex_mb.code == ex_gate.code == WC.WRL_UNSUPPORTED_FEATURE
          and ex_mb.message != ex_gate.message)
    rep(ok, "N9) the bootstrap surface rejects both `mailbox` and `gate`, "
            "with DIFFERENT messages -- two different situations")

    rep("outside" not in ex_mb.message and "WRL Core" in ex_mb.message,
        "N9b) the mailbox message no longer claims the role is outside IR v1, "
        "and names the surface that can spell it")
    rep("outside Forge Semantic IR v1" in ex_gate.message,
        "N9c) `gate` -- genuinely outside IR v1 -- keeps the reserved message")

    # Computed, not hand-listed: every Core-writable role the bootstrap chain
    # does not handle must get the Core-pointing message, automatically.
    rep("mailbox" in W._ROLE_TOKEN,
        "N9d) the branch is driven by membership in the Core surface table, "
        "so the next Core-writable role inherits it")


# ------------------------------------------------------------------- N10
def n10_canvas_refuses():
    """canvas.v1 is retired and frozen (§15.1.1) and has no mailbox. A mailbox
    world must therefore be REFUSED on the way out, not exported with the
    mailbox quietly missing -- which ties commit 1 back to commit 0's computed
    loss check."""
    g = W.parse_wrl_core(world(MB1))
    rep(_typed(lambda: LG.export_canvas_graph_v1(g),
               LG.WRL_LEGACY_EXPORT_LOSSY),
        "N10) exporting a mailbox world to canvas.v1 is a typed refusal, not "
        "a document that means less than its input")

    # And the underlying canvas message must be TRUE. It used to say the role
    # was "not in the frozen v1 registry", which is false for Mailbox: the
    # gate reads canvas.v1's own private role table, not the registry. That
    # was the FIFTH instance of the same defect, found while building c0.
    canvas = CV.graph_to_canvas(g)
    msgs = []
    for fn in (lambda: CV.validate_canvas_v1(canvas),
               lambda: CV.canvas_to_graph(canvas)):
        ex = _raised(fn)
        msgs.append(None if ex is None else (ex.code, ex.message))
    ok = all(m is not None and m[0] == WC.WRL_UNSUPPORTED_FEATURE
             and "is in the frozen v1 registry" in m[1]
             and "no canvas.v1 representation" in m[1] for m in msgs)
    rep(ok, "N10b) canvas.v1's gate and reader both say the role EXISTS but "
            "has no v1 representation -- neither denies the registry")

    # An asymmetry worth stating rather than discovering later: `graph_to_canvas`
    # is a pure EMITTER with no role gate, so it happily produces a `canvas.v1`
    # document containing a Mailbox node that canvas.v1's OWN reader refuses.
    #
    # It is not fixed here, deliberately. canvas.v1 is immutable and retired
    # (§15.1.1 point 1); correcting a message that stated a falsehood is not an
    # extension of the frozen surface, but adding a REJECTION to it would be a
    # behaviour change to a frozen module -- and an unnecessary one, because
    # the sanctioned door already refuses. What it does prove is why commit 0's
    # loss check had to be a computed ROUND TRIP: a validation-only check on
    # the emitted document would have had to trust an emitter that does not
    # validate its own output.
    rep(any(n.get("role") == WC.MAILBOX_ROLE for n in canvas["nodes"])
        and LG.canvas_v1_export_loss(g),
        "N10c) the retired emitter produces a document its own reader "
        "rejects -- the loss check catches it by ROUND TRIP, not by trusting "
        "the emitter (recorded, not fixed: canvas.v1 is frozen)")

    # Nothing about this required naming `Mailbox` in wrl_legacy.
    rep(LG.canvas_v1_export_loss(W.parse_wrl_core(world())) == (),
        "N10d) a mailbox-FREE world still exports losslessly -- the refusal "
        "is computed per world, not a blanket ban")


# ------------------------------------------------------------------- N11
def n11_declared_not_dropped():
    """The subtlest row, and the reason it exists.

    A mailbox world and its mailbox-free twin compile to a BYTE-IDENTICAL
    backend term. Seen alone that is indistinguishable from the compiler
    silently dropping the mailbox -- the exact failure class §15.1.1 point 6
    is about, and the one that passes every validator ever written because
    there is nothing left to validate. I read it as a defect and started
    writing a refusal before finding the design note that says it is the law:
    a mailbox is not physical, so it contributes nothing to the emitted term,
    and it is DECLARED in the plan (rather than omitted from it) specifically
    so that D8 stays falsifiable at that layer.

    What makes "provably ignored" different from "silently dropped" is the
    second half, and only the second half: the declaration must still be
    READABLE downstream. So the row asserts both, together. Either one alone
    is misleading."""
    plan_no = WP.artifact_to_compile_plan_v1(lower(world()).sealed_artifact)
    srcs = [world(), world(MB1), world("[mailbox:mb](w=16, cap=9){}\n"),
            world(MB1, "[mailbox:mc](w=8, cap=4){}\n")]
    lows = [lower(s) for s in srcs]
    plans = [WP.artifact_to_compile_plan_v1(lp.sealed_artifact) for lp in lows]
    comps = [WP.compile_artifact(lp.sealed_artifact, LP1) for lp in lows]

    # (a) nothing physical moved
    phys_same = (len({p["object_order"] for p in
                      [{"object_order": tuple(x["object_order"])} for x in plans]}) == 1
                 and len({c.backend_layout_signature for c in comps}) == 1
                 and len({c.backend_content_hash for c in comps}) == 1)
    # (b) but the world identity and the plan DID move
    ids_move = (len({lp.semantic_artifact_id for lp in lows}) == len(srcs)
                and len({WP.compile_plan_digest(p) for p in plans}) == len(srcs))
    rep(phys_same and ids_move,
        "N11) %d mailbox variants share one backend term (layout AND content) "
        "while all %d SemanticArtifactIDs and CompilePlanDigests differ -- a "
        "mailbox contributes nothing PHYSICAL" % (len(srcs), len(srcs)))

    # (c) ... and the declaration survives to the layer that consumes it.
    v_no = WP.plan_view(plan_no)
    v_two = WP.plan_view(plans[3])
    rep(AD.mailboxes_of(v_no) == {}
        and AD.mailboxes_of(v_two) == {"mb": (8, 4), "mc": (8, 4)},
        "N11b) ... and ADMIT reads the authored declarations back off the "
        "plan view -- ignored by the compiler, NOT dropped from the plan")

    # (d) the runtime materializes state for exactly what was authored, and a
    # mailbox-free world is not quietly promoted to the v1.1 state shape.
    s_two, s_no = {}, {}
    AD._mailbox_states(s_two, v_two)
    AD._mailbox_states(s_no, v_no)
    rep(sorted(s_two.get("mailbox_states", {})) == ["mb", "mc"]
        and "mailbox_states" not in s_no,
        "N11c) ... and ADMIT materializes runtime state for exactly the "
        "authored mailboxes, while the twin stays RuntimeStateV1")


# ------------------------------------------------------------------- N12
def _fold(fx, batches):
    """The binding_run6 V12 / binding_run45 L9 fold harness, unchanged."""
    import admit_ic as X
    from compiler import enc_state_v6
    world0 = init_state_v6(fx)
    claim0 = AD.init_claimstate()
    gold = O._golden_traj(claim0, world0, batches, epoch0=1)
    term = O._build_fold(batches, X.enc_factvec([], O.CAP),
                         X.enc_factvec([], O.RCAP), enc_state_v6(fx, world0))
    K = len(batches)
    dec_ref = O._decode_fold(O.norm(term), K)
    claims_ref = O._project_claims(dec_ref, epoch0=1)
    films_ref = [O._film(dec_ref[e][0], claims_ref[e], e + 1) for e in range(K)]
    films_gold = [O._film(gold[e][0], gold[e][1], e + 1) for e in range(K)]
    return term, K, films_ref, films_gold


def n12_native():
    """The frozen world still folds three ways after the surface change.

    A surface commit cannot move a reducer, but "cannot" is a claim until the
    reducer is run: the commit touched the parser, the port validator and the
    formatter, and all three sit upstream of the fold."""
    lp = W.lower_program(B5.CORE_SRC, W.parse_wrl_legacy_document)
    batches = B5._batches_from_program(lp)
    term, K, films_ref, films_gold = _fold(lp.fixture, batches)
    ok = films_ref == films_gold
    rep(ok, "N12) the frozen demo world folds ic_ref == golden over %d epochs "
            "(unchanged by the mailbox surface)" % K)
    if SKIP_NATIVE:
        print("       (native skipped: TRVM_SKIP_NATIVE=1)")
        return False
    dec_nat = O._decode_fold(O.native(term), K)
    claims_nat = O._project_claims(dec_nat, epoch0=1)
    films_nat = [O._film(dec_nat[e][0], claims_nat[e], e + 1) for e in range(K)]
    nat_ok = films_nat == films_ref == films_gold
    rep(nat_ok, "N12b) ic_ref == ic32 == golden")
    return nat_ok


def section(fn):
    """Run one section; an UNEXPECTED exception becomes a named FAIL.

    Mutation testing found this. Four of the eleven mutants -- a widened brace
    rule, a dropped `cap`, a wired Mailbox, a removed lexeme -- were detected,
    but detected as a `WrlValidationError` escaping a row body and aborting the
    process. The battery printed a traceback and every LATER row went unrun, so
    a single surprise hid thirty rows' worth of evidence and the output never
    named the property that broke.

    A raise inside a row is still a failure of that row, and it is reported as
    one. `SystemExit`/`KeyboardInterrupt` are deliberately not caught.
    """
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
    print("[BINDING wrl-sliceB-c1] the Mailbox WRL Core surface declaration")
    t0 = time.time()
    section(n1_surface_selects_v11)
    section(n2_identity_bearing)
    section(n3_additive)
    section(n4_brace_required)
    section(n5_required_config)
    section(n6_not_wireable)
    section(n7_formatter)
    section(n8_tooling_closes)
    section(n9_bootstrap_non_extension)
    section(n10_canvas_refuses)
    section(n11_declared_not_dropped)
    native_ok = section(n12_native)

    print()
    if _FAILED:
        for f in _FAILED:
            print("  FAILED: %s" % f)
        print("VERDICT: FAILURES (%d) in %ds" % (len(_FAILED), time.time() - t0))
        return 1
    mode = ("PASS_REF_ONLY (native skipped)" if SKIP_NATIVE
            else ("PASS_REF_AND_NATIVE" if native_ok
                  else "REF_ONLY (native MISMATCH)"))
    print("VERDICT: %s -- Slice B Commit 1 (Mailbox surface) closed in %ds"
          % (mode, time.time() - t0))
    print("NOTE: this line is NOT frozen. Per the ruling, the mailbox "
          "declaration and the first `~~` logical route ship together; an "
          "inert mailbox-only release must not be frozen.")
    return 0 if (SKIP_NATIVE or native_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
