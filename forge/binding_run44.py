"""binding_run44.py -- WRL language track L-0 sugar tier: `*` replication and
`{...}` fan-out (SG1-SG12).

Two frozen-but-dead surface symbols are activated as PURE source-to-source
expansions in `wrl_sugar.py`. Because they are a prepass, they inherit the whole
3B-4 discipline and CANNOT introduce an identity: a sugared world and its
explicit twin must lower to identical canonical bytes.

  SG1  `*` in declaration position mints N objects with identical config
  SG2  a sugared world and its EXPLICIT TWIN seal to the SAME SemanticArtifactID
  SG3  `{...}` fan-out expands to one edge per member; twin-identical
  SG4  `*` on both endpoints pairs POSITIONALLY (D-b), not cartesian
  SG5  `*` on one endpoint broadcasts to the whole group
  SG6  desugar is IDEMPOTENT
  SG7  desugar is a byte-exact NO-OP on sugar-free source
  SG8  the frozen DEMO world, re-spelled with sugar, still seals to sem-8ae91fe9...
  SG9  expansion judges only its own precondition -- an illegal fan-IN reaches
       the SEAL and is rejected there (WRL_CONTROLLER_CONFLICT), not silently
  SG10 malformed sugar is a TYPED rejection, never a silent guess
  SG11 the formatter emits only the EXPLICIT surface (sugar washes out of output)
  SG12 a sugared world folds ic_ref == ic32 == the explicit twin's film (native)

Native is gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import wrl_ir as W
import wrl_canonical as WC
import wrl_sugar as SG
import wrl_format as F
import wrl_plan as P
import compiler as C
import admit as AD
import forge_runtime as O
from admit import film_hash_v7
from forge_state import init_state_v6, state_to_film_args_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

# SG12 runs a fixed, scenario-free script: three epochs of EMPTY claim batches.
# Nothing is admitted, so the film is a pure function of the WORLD -- which is
# exactly the thing the sugar prepass is forbidden to change.
FOLD_EPOCHS = 3


def _fold(src, reducer):
    """Fold `src` (sugared or not) through the production lowering seam."""
    prog = W.lower_program(SG.desugar_core(src), W.parse_wrl_core)
    view = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
    return _fold_view(view, view, reducer)


def _fold_fixture(src, reducer):
    """Fold the same world through the INDEPENDENT Fixture oracle."""
    prog = W.lower_program(SG.desugar_core(src), W.parse_wrl_core)
    view = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
    return _fold_view(view, prog.as_fixture_for_test(), reducer)


def _fold_view(view, shape, reducer):
    world = init_state_v6(shape)
    claim = AD.init_claimstate()
    step, _ = C.compile_step_v6(view)
    films = []
    for ep in range(1, FOLD_EPOCHS + 1):
        claim, cfg_map, resets = AD.admit_step(claim, [], ep, shape)
        ec = C.enc_config_bundle(view, cfg_map, resets)
        world = C.dec_state_v6(view, reducer(
            "((%s %s) %s)" % (step, ec, C.enc_state_v6(view, world))))
        films.append(film_hash_v7(*state_to_film_args_v6(shape, world, ep),
                                  state=claim))
    return films

# ---------------------------------------------------------------- fixtures
SUGARED = """profile forge.world.core.v1

[pulser:p0](every 2){sig_out}
[relay:r*3]{sig_in, sig_out}
[spinner:sp*3](w=8, n=4, rotor=identity){sig_in, socket}
[orb:ob*3]{pose}

[pulser:p0] --sig--> [relay:r0]
[r*3] --sig--> [sp*3]
[sp*3] --socket--> [ob*3]
"""

# the hand-written EXPLICIT twin -- deliberately a SECOND encoding, in a
# different declaration order, so SG2 proves canonical equivalence rather than
# textual similarity.
EXPLICIT = """profile forge.world.core.v1

[orb:ob2]{pose}
[spinner:sp0](w=8, n=4, rotor=16.0.0.0){sig_in, socket}
[relay:r0]{sig_in, sig_out}
[orb:ob0]{pose}
[spinner:sp1](w=8, n=4, rotor=16.0.0.0){sig_in, socket}
[relay:r1]{sig_in, sig_out}
[orb:ob1]{pose}
[spinner:sp2](w=8, n=4, rotor=16.0.0.0){sig_in, socket}
[relay:r2]{sig_in, sig_out}
[pulser:p0](mode=periodic, period=2, phase=0){sig_out}

[sp2] --socket--> [ob2]
[r1] --sig--> [sp1]
[pulser:p0] --sig--> [relay:r0]
[sp0] --socket--> [ob0]
[r2] --sig--> [sp2]
[r0] --sig--> [sp0]
[sp1] --socket--> [ob1]
"""

FANOUT = """profile forge.world.core.v1

[pulser:p0](every 2){sig_out}
[door:d0]{sig_in}
[door:d1]{sig_in}
[door:d2]{sig_in}

[p0] --sig--> {[d0], [d1], [d2]}
"""

FANOUT_TWIN = """profile forge.world.core.v1

[pulser:p0](mode=periodic, period=2, phase=0){sig_out}
[door:d0]{sig_in}
[door:d1]{sig_in}
[door:d2]{sig_in}

[p0] --sig--> [d0]
[p0] --sig--> [d1]
[p0] --sig--> [d2]
"""

# the frozen demo world, re-spelled with sugar where it is expressible. The
# demo has no repeated structure, so the sugar exercised here is the concise
# clock + named rotor + a single-member fan-out group.
DEMO_SUGARED = """profile forge.world.core.v1

[pulser:p0](every 2){sig_out}
[relay:r0]{sig_in, sig_out}
[spinner:sp](w=16, n=8, rotor=quarter_turn_z, configurable){sig_in, socket}
[orb:ob]{pose}
[pulser:p1](once at 1){sig_out}
[door:d0]{sig_in}

[pulser:p0] --sig--> {[relay:r0]}
[relay:r0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]
[pulser:p1] --sig--> [door:d0]
"""

DEMO_SEM = ("sem-8ae91fe9cbc5fd086ce4356d587c403211e5c7b2b3ebdd316496367429ec"
            "fe4a")

# an illegal fan-IN: three sources into one door. Expansion is happy; the frozen
# registry admits at most one sig_in, so the SEAL must reject it.
FANIN_BAD = """profile forge.world.core.v1

[pulser:pp*3](every 2){sig_out}
[door:d0]{sig_in}

[pp*3] --sig--> [d0]
"""

# a GENERATED name colliding with an EXPLICIT one. `r*3` mints r0,r1,r2 and the
# author has also hand-written r1. Expansion must not police this -- it is an
# ordinary duplicate id, and the SEAL owns duplicate ids (SG15).
COLLIDE_BAD = """profile forge.world.core.v1

[relay:r*3]{sig_in, sig_out}
[relay:r1]{sig_in, sig_out}
"""

# spellings that must be REFUSED BEFORE any list is allocated (SG13).
HUGE_DECL = ("profile forge.world.core.v1\n\n"
             "[spinner:sp*1000000000](w=8, n=4, rotor=identity)"
             "{sig_in, socket}\n")
HUGE_DIGITS = ("profile forge.world.core.v1\n\n"
               "[spinner:sp*" + "9" * 400 + "](w=8, n=4){sig_in, socket}\n")
HUGE_EDGE = ("profile forge.world.core.v1\n\n"
             "[a*2000000] --sig--> [b*2000000]\n")


# ------------------------------------------------- the TOOLING-CLOSURE fixtures
# SG17-SG21 answer the question SG14 did not: SG14 shows a mapping EXISTS and
# can be traced by hand; these show the TOOLING USES IT. Every one of them is
# built around a construct that appears BELOW an expansion, because that is the
# only place where generated and authored coordinates disagree.
#
# `LATER` is deliberately INDENTED. Column stability is vacuous at column 0 --
# any implementation, including one that discards columns entirely, would pass.
# With four spaces of indentation the authored start_column is 4, and a later
# line's span must still report 4 after three lines have been inserted above it.
LATER = """profile forge.world.core.v1

[spinner:sp*3](w=8, n=4, rotor=identity){sig_in, socket}
    [pulser:p0](every 2){sig_out}
    [door:d0]{sig_in}
    [p0] --sig--> [d0]
"""

# the same world with the sugar written out by hand -- the AUTHORED coordinates
# of the sugared spelling must describe the sugared text, never this one.
LATER_LINES = LATER.splitlines()

# a structural rejection whose offending element is text the author NEVER TYPED:
# `r*3` mints r1, and the author also declared r1 explicitly. The diagnostic's
# PRIMARY span must land on the explicit declaration and its RELATED span on the
# sugar that generated the collision -- both in authored coordinates.
DIAG_COLLIDE = """profile forge.world.core.v1

[relay:r*3]{sig_in, sig_out}
[relay:r1]{sig_in, sig_out}
"""

# a PREPASS rejection on a LATER, INDENTED line. This is the tier with no graph
# and no desugared text, so without a locator it would carry no position at all.
DIAG_PREPASS = """profile forge.world.core.v1

[door:d0]{sig_in}
    [spinner:s0](w=8, n=4, rotor=barrel_roll){sig_in, socket}
"""

# the two sides of an authored-coordinate SemanticDiff. `sp*3` -> `sp*4` adds a
# member and the rotor changes, so the changes are ABOUT generated objects
# (sp0..sp3) that appear nowhere in either authored text.
DIFF_A = """profile forge.world.core.v1

[spinner:sp*3](w=8, n=4, rotor=identity){sig_in, socket}
[orb:ob*3]{pose}
[sp*3] --socket--> [ob*3]
"""
DIFF_B = """profile forge.world.core.v1

[spinner:sp*4](w=8, n=4, rotor=reverse_x){sig_in, socket}
[orb:ob*4]{pose}
[sp*4] --socket--> [ob*4]
"""

# a cursor placed inside a LATER spinner's config, below an expansion, in text
# that is MID-EDIT -- `rotor=rev` is a half-typed name. This is the normal state
# of an editor buffer, and it is where the desugar-first alternative does not
# merely answer wrongly but cannot run at all: `rev` is not in the rotor
# vocabulary, so desugaring RAISES. Completion must never require its input to
# be well-formed.
COMPLETE_SRC = """profile forge.world.core.v1

[spinner:sp*3](w=8, n=4, rotor=identity){sig_in, socket}
[pulser:p0](every 2){sig_out}
[spinner:s9](w=8, n=4, rotor=rev"""

# the second prong: text that DOES desugar cleanly, so the alternative runs --
# and still answers a different question, because the offset lands inside a
# generated member rather than the port group the author is typing.
COMPLETE_OK = """profile forge.world.core.v1

[spinner:sp*3](w=8, n=4, rotor=identity){sig_in, socket}
[pulser:p0](every 2){sig_out}
[spinner:s9](w=8, n=4, rotor=identity){sig_in, """


def _in_bounds(span, lines):
    """True when a span actually describes real text in `lines` -- the honest
    test of whether a coordinate is authored. A generated-coordinate span
    routinely names a line that does not exist, or a column past the end of the
    line it names."""
    if span is None:
        return False
    if span.start_line < 1 or span.start_line > len(lines):
        return False
    return span.end_column <= len(lines[span.start_line - 1])


def _text_of(span, lines):
    return lines[span.start_line - 1][span.start_column:span.end_column]


def _sid(src):
    return W.lower_program(SG.desugar_core(src),
                           W.parse_wrl_core).semantic_artifact_id


def _bytes(src):
    p = W.lower_program(SG.desugar_core(src), W.parse_wrl_core)
    return WC.serialize_artifact(p.artifact)


def main():
    print("[BINDING wrl-L0-sugar] `*` replication + `{...}` fan-out")
    allok = True
    native_ok = True
    t0 = time.time()

    def rep(ok, okn, label):
        nonlocal allok, native_ok
        allok &= bool(ok)
        tag = "PASS" if ok else "FAIL"
        if okn is False:
            native_ok = False
            tag = "FAIL(native)"
        print(f"  [{tag}] {label}")

    # ---- SG1 declaration replication mints N identical objects
    g = W.parse_wrl_core(SG.desugar_core(SUGARED))
    names = sorted(n for _r, n, _c in g.nodes)
    cfgs = [c for r, n, c in g.nodes if r == "Spinner"]
    sg1 = (names == ["ob0", "ob1", "ob2", "p0", "r0", "r1", "r2",
                     "sp0", "sp1", "sp2"]
           and len(cfgs) == 3 and all(c == cfgs[0] for c in cfgs))
    rep(sg1, None, "SG1) `*` declaration mints N objects, config identical")

    # ---- SG2 sugared == explicit twin, byte for byte
    sg2 = (_sid(SUGARED) == _sid(EXPLICIT)
           and _bytes(SUGARED) == _bytes(EXPLICIT))
    rep(sg2, None, "SG2) sugared world and explicit twin: same "
                   "SemanticArtifactID AND same bytes")

    # ---- SG3 fan-out
    gf = W.parse_wrl_core(SG.desugar_core(FANOUT))
    sg3 = (len(gf.edges) == 3
           and _sid(FANOUT) == _sid(FANOUT_TWIN)
           and _bytes(FANOUT) == _bytes(FANOUT_TWIN))
    rep(sg3, None, "SG3) `{...}` fan-out -> one edge per member; twin-identical")

    # ---- SG4 positional pairing, NOT cartesian (D-b)
    pairs = sorted((s, d) for _k, s, d in g.edges if _k == "SignalWire"
                   and s.startswith("r"))
    sg4 = pairs == [("r0", "sp0"), ("r1", "sp1"), ("r2", "sp2")]
    rep(sg4, None, "SG4) `*` on both endpoints pairs POSITIONALLY (3 edges, "
                   "not 9)")

    # ---- SG5 one-sided broadcast
    b = SG.desugar_core("[p0] --sig--> [d*3]\n").strip().splitlines()
    sg5 = b == ["[p0] --sig--> [d0]", "[p0] --sig--> [d1]",
                "[p0] --sig--> [d2]"]
    rep(sg5, None, "SG5) `*` on one endpoint broadcasts to the whole group")

    # ---- SG6 idempotent
    once = SG.desugar_core(SUGARED)
    sg6 = SG.desugar_core(once) == once and SG.desugar_core(
        SG.desugar_core(FANOUT)) == SG.desugar_core(FANOUT)
    rep(sg6, None, "SG6) desugar is idempotent")

    # ---- SG7 byte-exact no-op on sugar-free source
    sg7 = (SG.desugar_core(EXPLICIT) == EXPLICIT
           and SG.desugar_core(FANOUT_TWIN) == FANOUT_TWIN)
    rep(sg7, None, "SG7) desugar is a byte-exact NO-OP on sugar-free source")

    # ---- SG8 the frozen demo world, re-spelled with sugar
    sg8 = _sid(DEMO_SUGARED) == DEMO_SEM
    rep(sg8, None, "SG8) sugar-spelled DEMO world still seals to "
                   "sem-8ae91fe9...fe4a")

    # ---- SG9 the SEAL judges topology, not the expansion
    sg9 = False
    try:
        W.lower_program(SG.desugar_core(FANIN_BAD), W.parse_wrl_core)
    except WC.WrlValidationError as e:
        sg9 = e.code == WC.WRL_CONTROLLER_CONFLICT
    rep(sg9, None, "SG9) illegal fan-IN expands, then the SEAL rejects it "
                   "(WRL_CONTROLLER_CONFLICT)")

    # ---- SG10 malformed sugar is typed
    def _typed(src, code=None, through_seal=False):
        """True iff `src` is refused with a TYPED WrlValidationError (optionally
        an exact code). `through_seal` runs the whole prepass -> parse -> seal
        pipeline, for rejections the sugar layer is NOT supposed to own."""
        try:
            if through_seal:
                W.lower_program(SG.desugar_core(src), W.parse_wrl_core)
            else:
                SG.desugar_core(src)
        except WC.WrlValidationError as e:
            return code is None or e.code == code
        except Exception:
            return False          # a raw Python exception is a FAILURE
        return False

    sg10 = (_typed("[relay:r*0]{sig_in, sig_out}\n")          # count < 1
            and _typed("[a*2] --sig--> [b*3]\n")              # unequal counts
            and _typed("[p0] --sig--> {}\n")                  # empty group
            and _typed("[p0] --sig--> {d0}\n"))               # unbracketed
    rep(sg10, None, "SG10) malformed sugar -> typed WrlValidationError, never "
                    "a raw exception or a silent guess")

    # ---- SG11 the formatter emits only the explicit surface
    ftxt = F.format_wrl_core(W.parse_wrl_core(SG.desugar_core(SUGARED)))
    sg11 = ("*" not in ftxt and "{[" not in ftxt
            and _sid(ftxt) == _sid(SUGARED))
    rep(sg11, None, "SG11) formatter emits only the EXPLICIT surface "
                    "(sugar washes out of output)")

    # ---- SG12 native: sugared world folds identically to the explicit twin
    #
    # The sugared source and its explicit twin already seal to identical bytes
    # (SG2), so this row is not re-proving the identity -- it is proving that a
    # world a human SPELLED WITH SUGAR is actually RUNNABLE, and runnable the
    # same way on both reducers and on the independent Fixture oracle. It is the
    # row that would catch a desugar that produced a well-formed-but-wrong graph.
    ref_s = _fold(SUGARED, O.ref_reduce)
    ref_e = _fold(EXPLICIT, O.ref_reduce)
    orc_s = _fold_fixture(SUGARED, O.ref_reduce)
    sg12r = (ref_s == ref_e and ref_s == orc_s and len(ref_s) == 3)
    sg12n = None
    if not SKIP_NATIVE:
        sg12n = (_fold(SUGARED, O.native_reduce) == ref_s)
    rep(sg12r, sg12n,
        "SG12) NATIVE -- the sugar-spelled world RUNS: ic_ref == ic32 == the "
        "Fixture oracle, and equals the explicit twin's film")

    # ================================================================ L-0 CLOSURE
    # The four rows below are the gates GPT-5.6 made mandatory before the sugar
    # tier may be called closed. SG1-SG12 proved the sugar is CORRECT; these
    # prove it is SAFE (SG13), TOOLABLE (SG14), correctly SCOPED (SG15) and
    # honestly VERSIONED (SG16).

    # ---- SG13 bounded expansion: refused BEFORE anything is allocated
    #
    # The point is not merely that the spelling is rejected -- it is that it is
    # rejected CHEAPLY. A guard placed after the list comprehension would still
    # "reject", having first tried to build a billion strings. So this row is
    # also a WALL-CLOCK assertion: three pathological spellings, all refused,
    # in well under a second combined.
    t13 = time.time()
    bounded = all(_typed(s) for s in (HUGE_DECL, HUGE_DIGITS, HUGE_EDGE))
    dt13 = time.time() - t13
    # ...and the bound is a real cliff, not a coincidence: MAX passes, MAX+1 does not
    at_max = "[door:dd*%d]{sig_in}\n" % SG.REPLICATION_MAX
    over_max = "[door:dd*%d]{sig_in}\n" % (SG.REPLICATION_MAX + 1)
    cliff = (len(SG.desugar_core(at_max).splitlines()) == SG.REPLICATION_MAX
             and _typed("profile forge.world.core.v1\n\n" + over_max))
    sg13 = bounded and cliff and dt13 < 1.0
    rep(sg13, None,
        "SG13) unbounded expansion is refused BEFORE allocation -- `sp*1e9`, a "
        "400-digit count and a 2e6 x 2e6 edge are all typed rejects in %dms; "
        "REPLICATION_MAX=%d is an exact cliff" % (int(dt13 * 1000),
                                                  SG.REPLICATION_MAX))

    # ---- SG14 one-to-many expansion preserves the AUTHORED source position
    #
    # This is the row that makes sugar tool-able. `wrl_spans` maps canonical ids
    # to spans in the text it was HANDED -- which, for a sugared program, is the
    # GENERATED text. Composed with the SugarSourceMap, a canonical object must
    # trace all the way back to the line the human typed. All three members of a
    # `*` group must land on that ONE authored line, and it must still read
    # `sp*3` -- not `sp2`, which appears nowhere in the authored source.
    import wrl_spans as SP
    dtext, smap = SG.desugar_core_mapped(SUGARED)
    _, span_map = SP.parse_core_with_spans(dtext)
    authored = {}
    for oid in ("sp0", "sp1", "sp2"):
        o = span_map.origin_for_object(oid)
        authored[oid] = smap.origin_for_emitted_line(o.span.start_line)
    src_lines = SUGARED.splitlines()
    one_line = len({a.source_line for a in authored.values()}) == 1
    aline = authored["sp2"].source_line
    sg14 = (one_line
            and "sp*3" in src_lines[aline - 1]
            and "sp2" not in src_lines[aline - 1]
            and all(a.expanded and a.member_count == 3
                    for a in authored.values())
            and authored["sp2"].member_index == 2
            # the inverse arrow: one authored line -> its whole expansion
            and len(smap.group_for_source_line(aline)) == 3
            # and a sugar-free source moves NOTHING
            and SG.desugar_core_mapped(EXPLICIT)[1].is_identity()
            and not SG.desugar_core_mapped(SUGARED)[1].is_identity())
    rep(sg14, None,
        "SG14) expansion preserves AUTHORED spans -- sp0/sp1/sp2 all trace "
        "through wrl_spans + SugarSourceMap back to the ONE line that reads "
        "`sp*3`; sugar-free source maps to identity")

    # ---- SG15 a GENERATED name collides like any other name -- the SEAL owns it
    sg15 = _typed(COLLIDE_BAD, code=WC.WRL_DUPLICATE_ID, through_seal=True)
    # and the expansion itself is perfectly happy to produce it
    expanded_ok = "[relay:r1]" in SG.desugar_core(COLLIDE_BAD)
    rep(sg15 and expanded_ok, None,
        "SG15) a generated name colliding with an explicit one EXPANDS, then "
        "the SEAL rejects it as an ordinary WRL_DUPLICATE_ID (sugar gets no "
        "private namespace and no private veto)")

    # ---- SG16 the surface version is bumped, and the map is byte-honest
    sg16 = (SG.SUGAR_VERSION == "sugar.v2"
            and all(SG.desugar_core_mapped(s)[0] == SG.desugar_core(s)
                    for s in (SUGARED, EXPLICIT, FANOUT, DEMO_SUGARED)))
    rep(sg16, None,
        "SG16) SUGAR_VERSION == %r, and desugar_core_mapped()[0] is "
        "byte-identical to desugar_core() (the map is strictly additive)"
        % (SG.SUGAR_VERSION,))

    # ================================================================ SG17-SG21
    # THE TOOLING-CLOSURE ROWS. SG14-SG16 remain exactly as they were; these are
    # ADDITIONS, not substitutions. The distinction they enforce is the one that
    # separates "a mapping exists" from "the toolchain is correct": a data
    # structure that COULD be composed by hand proves nothing about the
    # behaviour of tools that do not compose it.

    # ---- SG17 a LATER construct keeps its authored LINE and COLUMN
    #
    # Three lines are inserted above by `sp*3`, so every construct below it sits
    # at a different line in generated coordinates. The authored span must
    # report the line the author typed and the column they indented to -- and
    # the negative control must show the naive generated span does NOT, or the
    # row is measuring nothing.
    import wrl_spans as SP
    dtext17, smap17 = SG.desugar_core_mapped(LATER)
    gen17 = SP._scan_core_spans(dtext17, SP.DEFAULT_FILE_ID)
    auth17 = SG.authored_source_map(smap17, gen17)

    # the door is authored on line 5 at column 4; `sp*3` pushes it to line 7.
    ga = gen17.origin_for_object("d0").span
    aa = auth17.origin_for_object("d0").span
    later_line_ok = (aa.start_line == 5 and ga.start_line == 7)
    later_col_ok = (aa.start_column == 4 and aa.end_column == 21
                    and _text_of(aa, LATER_LINES) == "[door:d0]{sig_in}")
    # ...and the same for a later EDGE, which is a different index path
    ea = auth17.origin_for_edge("SignalWire", "p0", "d0").span
    later_edge_ok = (ea.start_line == 6 and ea.start_column == 4
                     and _text_of(ea, LATER_LINES) == "[p0] --sig--> [d0]")
    # NEGATIVE CONTROL: the generated spans are not merely different, they are
    # OUT OF BOUNDS against the authored text -- they name lines or columns that
    # do not exist there. That is what makes remapping mandatory, not cosmetic.
    naive_bad = sum(1 for o in gen17.origins
                    if not _in_bounds(o.span, LATER_LINES))
    all_authored = all(_in_bounds(o.span, LATER_LINES) for o in auth17.origins)
    # value sugar moves COLUMNS without expanding, so `verbatim` (not `expanded`)
    # is the correct precondition for column-exactness -- the pulser line is the
    # witness: it did not expand, yet its generated end_column overruns.
    puls_gen = gen17.origin_for_object("p0").span
    value_col_moved = (not _in_bounds(puls_gen, LATER_LINES)
                       and _in_bounds(auth17.origin_for_object("p0").span,
                                      LATER_LINES))
    sg17 = (later_line_ok and later_col_ok and later_edge_ok
            and naive_bad >= 3 and all_authored and value_col_moved)
    rep(sg17, None,
        "SG17) a LATER construct keeps its authored LINE and COLUMN -- d0 is "
        "authored L5 c4 and generated L7; %d/%d naive generated spans are OUT "
        "OF BOUNDS against the authored text, 0/%d remapped ones are"
        % (naive_bad, len(gen17.origins), len(auth17.origins)))

    # ---- SG18 the DIAGNOSTICS path is sugar-aware, not merely remappable
    #
    # The ruling's actual demand: not that a remap exists, but that a real
    # diagnostic path performs it. Three tiers, all located in authored
    # coordinates, plus the law that the sugared mouth is INDISTINGUISHABLE from
    # the core mouth on sugar-free source.
    import wrl_diagnostics as DG
    dc = DG.diagnose_sugared(DIAG_COLLIDE)
    dcl = DIAG_COLLIDE.splitlines()
    # the collision: PRIMARY on the explicit declaration the author typed,
    # RELATED on the SUGAR that generated the colliding name.
    collide_ok = (len(dc) == 1 and dc[0].code == WC.WRL_DUPLICATE_ID
                  and _in_bounds(dc[0].primary_span, dcl)
                  and _text_of(dc[0].primary_span, dcl)
                  == "[relay:r1]{sig_in, sig_out}"
                  and _in_bounds(dc[0].related_span, dcl)
                  and "r*3" in _text_of(dc[0].related_span, dcl))
    # the PREPASS tier: no graph, no desugared text -- still located, on the
    # later indented line, at its authored column.
    dp = DG.diagnose_sugared(DIAG_PREPASS)
    dpl = DIAG_PREPASS.splitlines()
    prepass_ok = (len(dp) == 1 and dp[0].code == WC.WRL_UNSUPPORTED_FEATURE
                  and _in_bounds(dp[0].primary_span, dpl)
                  and dp[0].primary_span.start_line == 4
                  and dp[0].primary_span.start_column == 4
                  and "barrel_roll" in _text_of(dp[0].primary_span, dpl))
    # the STRUCTURAL tier on a later INDENTED line, below an expansion. The
    # offending edge is authored on line 6 at column 4 and generated on line 8.
    bad_later = LATER.replace("--sig--> [d0]", "--sig--> [dX]")
    bl_lines = bad_later.splitlines()
    dl = DG.diagnose_sugared(bad_later)
    later_diag_ok = (len(dl) == 1 and dl[0].code == WC.WRL_UNKNOWN_ENDPOINT
                     and _in_bounds(dl[0].primary_span, bl_lines)
                     and dl[0].primary_span.start_line == 6
                     and dl[0].primary_span.start_column == 4
                     and _text_of(dl[0].primary_span, bl_lines)
                     == "[p0] --sig--> [dX]")
    # THE AGREEMENT LAW: on sugar-free source the sugared mouth must be
    # byte-identical to the core mouth. A sugar-aware path that answered
    # DIFFERENTLY on sugar-free text would have invented a sugar-specific
    # behaviour, which is exactly what the prepass discipline forbids.
    agree = all(DG.diagnose_sugared(s) == DG.diagnose_core(s)
                for s in (EXPLICIT, FANOUT_TWIN,
                          EXPLICIT.replace("[relay:r0]", "[relay:r2]")))
    sg18 = collide_ok and prepass_ok and later_diag_ok and agree
    rep(sg18, None,
        "SG18) diagnose_sugared() locates ALL THREE tiers in authored "
        "coordinates -- prepass (no graph yet), parse, and structural; a "
        "generated-name collision points PRIMARY at the explicit decl and "
        "RELATED at the `r*3` sugar; and it is byte-identical to diagnose_core "
        "on sugar-free source")

    # ---- SG19 COMPLETION operates in authored coordinates
    #
    # Completion is authored-NATIVE by construction: `completions_at` takes a
    # raw offset into the text it is given and never desugars. That is a design
    # property, and an untested design property is a comment. The negative
    # control is what makes this a test: at the SAME offset the desugar-first
    # alternative answers a DIFFERENT QUESTION, because the offset lands inside
    # a generated member.
    import wrl_complete as CP
    off = len(COMPLETE_SRC)
    a19 = CP.completions_at(COMPLETE_SRC, off)
    authored_right = (a19.context == CP.ROTOR_VALUE and a19.prefix == "rev"
                      and a19.candidates
                      == ("reverse_x", "reverse_y", "reverse_z"))
    # CONTROL PRONG 1 -- the decisive one. On mid-edit text the desugar-first
    # alternative cannot even RUN: `rotor=rev` is a half-typed name, so the
    # prepass raises. Completion is the one tool whose input is ALWAYS
    # potentially ill-formed, which is why it must never desugar.
    try:
        CP.completions_at(SG.desugar_core(COMPLETE_SRC), off)
        control_cannot_run = False
    except WC.WrlValidationError:
        control_cannot_run = True
    # CONTROL PRONG 2 -- even where the alternative CAN run, it answers a
    # different question, because the offset lands inside a generated member.
    off2 = len(COMPLETE_OK)
    a19b = CP.completions_at(COMPLETE_OK, off2)
    n19b = CP.completions_at(SG.desugar_core(COMPLETE_OK), off2)
    ports_right = (a19b.context == CP.PORT
                   and a19b.candidates == CP.port_completions("spinner"))
    control_diverges = (n19b.context, n19b.candidates) != (a19b.context,
                                                           a19b.candidates)
    # and the vocabulary offered is still a pure registry projection
    vocab_ok = set(a19.candidates) <= set(SG.ALL_ROTOR_NAMES)
    sg19 = (authored_right and ports_right and control_cannot_run
            and control_diverges and vocab_ok)
    rep(sg19, None,
        "SG19) completion is authored-native -- it offers %s at a rotor cursor "
        "and %s at a port cursor, on MID-EDIT text; the desugar-first "
        "alternative cannot even run there (half-typed `rotor=rev` raises) and "
        "answers %s instead of %s where it can"
        % (list(a19.candidates), list(a19b.candidates), n19b.context,
           a19b.context))

    # ---- SG20 SEMANTIC DIFF reports changes in authored coordinates
    #
    # Every change here is ABOUT a generated object (sp0..sp3, ob0..ob3) that
    # appears in NEITHER authored text. So a diff that cannot speak authored
    # coordinates cannot point at a sugared edit at all.
    import wrl_diff as DF
    diff20, loc20 = SG.diff_sugared_sources_located(DIFF_A, DIFF_B)
    al20, bl20 = DIFF_A.splitlines(), DIFF_B.splitlines()
    added = [lc for lc in loc20 if lc.change.kind == DF.OBJECT_ADDED]
    changed = [lc for lc in loc20 if lc.change.kind == DF.OBJECT_CHANGED]
    edges20 = [lc for lc in loc20 if lc.change.kind == DF.EDGE_ADDED]
    # the added 4th member is located on the authored `sp*4` line
    added_ok = (sorted(lc.change.key for lc in added) == ["ob3", "sp3"]
                and all(_in_bounds(lc.span, bl20) for lc in added)
                and any("sp*4" in _text_of(lc.span, bl20)
                        for lc in added if lc.change.key == "sp3"))
    # the rotor edit is reported per generated object, all on the ONE authored line
    rotor_ok = (len(changed) == 3
                and all(lc.change.detail == ("static_config.rotor",)
                        for lc in changed)
                and len({lc.span.start_line for lc in changed}) == 1
                and all(_in_bounds(lc.span, bl20) for lc in changed))
    edge_ok = (len(edges20) == 1
               and _in_bounds(edges20[0].span, bl20)
               and "sp*4" in _text_of(edges20[0].span, bl20))
    # EVERY located change is in authored bounds, on the side it belongs to
    all_loc_ok = all(_in_bounds(lc.span, al20 if lc.side == DF.BEFORE else bl20)
                     for lc in loc20 if lc.span is not None)
    # the locator itself stays sugar-UNAWARE: it never sees sugared text, only
    # the authored-coordinate maps -- so the identity bridge law is untouched.
    bridge = (DF.diff_sources(SG.desugar_core(DIFF_A),
                              SG.desugar_core(DIFF_A)).is_empty()
              and not diff20.is_empty())
    sg20 = added_ok and rotor_ok and edge_ok and all_loc_ok and bridge
    rep(sg20, None,
        "SG20) SemanticDiff reports in authored coordinates -- %d changes, all "
        "about objects (sp0-sp3/ob0-ob3) that appear in NEITHER authored text, "
        "every one located in-bounds on its own side of the diff"
        % (len(loc20),))

    # ---- SG21 the remap contract is EXACT-or-COLLAPSED, and says which
    #
    # A remap that silently reported an approximate column as exact would be
    # worse than one that reported nothing: a caller cannot tell it is being
    # lied to. So the seam distinguishes the two, and the distinction must track
    # `verbatim` (byte-identical passthrough) rather than `not expanded`.
    def _remap_of(oid):
        return smap17.remap(gen17.origin_for_object(oid).span)
    r_door = _remap_of("d0")          # untouched line -> EXACT
    r_puls = _remap_of("p0")          # value sugar, NOT expanded -> COLLAPSED
    r_spin = _remap_of("sp1")         # generated member -> COLLAPSED
    exact_contract = (r_door.exact and not r_puls.exact and not r_spin.exact)
    # the pulser is the whole point: it did NOT expand, so `not expanded` would
    # have wrongly called it exact and kept an overrunning column.
    proxy_would_lie = not r_puls.origin.expanded and not r_puls.origin.verbatim
    # a span the map does not cover is returned, never dropped
    ghost = SP.SourceSpan("<wrl>", 0, 1, 999, 0, 999, 1)
    ghost_kept = (smap17.remap(ghost).span == ghost
                  and not smap17.remap(ghost).exact)
    sg21 = exact_contract and proxy_would_lie and ghost_kept
    rep(sg21, None,
        "SG21) the remap contract is EXACT-or-COLLAPSED and honest about which "
        "-- exactness tracks `verbatim`, not `not expanded` (the value-sugared "
        "pulser is unexpanded yet column-shifted, and would be MIS-reported as "
        "exact by the proxy); an uncovered span is returned, never dropped")

    dt = int(time.time() - t0)
    # The verdict VOCABULARY is shared with every sibling battery, and this line
    # used to disagree with it: `REF_ONLY` means "native MISMATCHED" everywhere
    # else, and was used here to mean "native was skipped". One token meaning
    # both "fine" and "broken" makes an aggregated sweep unreadable -- it must
    # either treat a benign skip as a failure or a real mismatch as benign.
    # Same fork, third instance; the wording now matches the siblings exactly.
    mode = ("PASS_REF_ONLY (native skipped)" if SKIP_NATIVE
            else ("PASS_REF_AND_NATIVE" if native_ok
                  else "REF_ONLY (native MISMATCH)"))
    print()
    print("[wrl-L0-sugar] %s -- %s (%ds)"
          % ("ALL PASS" if allok else "FAILURES", mode, dt))
    print("  [note] THE LAW is NO SUGAR-SPECIFIC IDENTITY: `*` and `{...}` are "
          "erased before the\n         graph is built, so the sugared spelling "
          "mints no identity of its own and\n         seals byte-identically to "
          "its explicit twin (SG2/SG3/SG8). It is NOT the\n         claim that "
          "a sugar edit cannot move an identity -- `sp*3` -> `sp*4` is a\n"
          "         different program and moves it, exactly as the explicit "
          "spelling would.\n         SG13-SG16 are the EXPANSION gates: bounded "
          "expansion, an authored-span\n         mapping, collisions judged by "
          "the seal, an honest surface version.")
    print("  [note] SG17-SG21 are the TOOLING-CLOSURE gates, and they assert a "
          "STRICTLY\n         STRONGER thing than SG14. SG14 shows a mapping "
          "EXISTS and can be traced\n         by hand; a data structure that "
          "COULD be composed proves nothing about\n         tools that do not "
          "compose it. SG17-SG21 show the TOOLS USE IT: a later\n         "
          "construct keeps its authored line AND column (SG17), a real "
          "diagnostics\n         path locates all three failure tiers in "
          "authored coordinates (SG18),\n         completion and SemanticDiff "
          "operate in authored coordinates (SG19/SG20),\n         and the remap "
          "is honest about when a column is exact (SG21).\n"
          "         Each carries a NEGATIVE CONTROL, because an assertion never "
          "observed to\n         fail is not yet evidence: 5 of 7 naive spans "
          "are OUT OF BOUNDS against the\n         authored text, and "
          "desugar-first completion cannot even RUN on mid-edit\n         text. "
          "Remapping is therefore mandatory, not cosmetic.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
