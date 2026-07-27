"""wrl_roundtrip_probe.py -- WRL language track, finding L-0.

A standalone, timing-free probe that answers ONE question:

    are binding_run6:83 / binding_run9 L1 / binding_run9 L8 failing because the
    formatter is BROKEN, or because they assert a law that v0.4-0 REPEALED?

It is deliberately NOT a battery edit. It changes no shipped module and asserts
no new law; it measures the existing ones so the restatement can be ruled on
evidence rather than on argument.

Run:
    cd TRVM/forge
    PYTHONPATH=../runtime/python:../research python3 wrl_roundtrip_probe.py

PART 1 -- what actually differs across `parse(format(g))`.
PART 2 -- the three proposed restatements, each executed.

    L1'  WORLD round-trip      canonical (profile, nodes, edges) is preserved
    L1"  IDENTITY round-trip   serialize_artifact bytes + SemanticArtifactID preserved
    L8'  INVERSE run-input law the formatter EXCLUDES run inputs (periods/batches/epoch_inputs)

L8' is the interesting one: it is the same assertion as the failing L8 with its
POLARITY REVERSED. The old L8 asserted run inputs survive a format cycle; the
v0.4-0 document boundary made that deliberately false, so the useful law is that
they are provably dropped while the identity does not move.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import wrl_ir as W
import wrl_canonical as WC
import wrl_format as F
import binding_run9 as B9


# The RUN-INPUT fields of a canonical graph -- exactly what v0.4-0 moved out to
# ScenarioV1. Naming the EXCLUSIONS rather than the inclusions is deliberate
# (GPT-5.6, Q1): a hard-coded `(profile, nodes, edges)` tuple silently stops
# covering any field a later slice adds, and Slice B is about to add route
# semantics. Defined this way, a new world field is IN the projection by default
# and the law keeps testing it without anyone remembering to widen a tuple.
RUN_INPUT_FIELDS = ("periods", "batches")


def _world(cg):
    """The WORLD projection: every canonical field EXCEPT the run inputs.

    Reflective on purpose. When Slice B adds route semantics to WrlGraph, that
    field joins this projection automatically and L1' starts covering it with
    no edit here."""
    return tuple((f, getattr(cg, f)) for f in sorted(vars(cg))
                 if f not in RUN_INPUT_FIELDS)


def _run_inputs(cg):
    """The RUN-INPUT projection -- exactly what v0.4-0 moved to ScenarioV1."""
    return (cg.periods, sum(len(b) for b in cg.batches))


# The LEXICAL half of L8'. It must assert the formatter never EMITS ScenarioV1
# syntax, not merely that reparsing yields zero periods -- a formatter that
# wrote a literal `periods 0` would satisfy the weak form while still leaking
# run-input syntax into a world document.
#
# The vocabulary is DELEGATED to `binding_run9._has_scenario_syntax`, which in
# turn delegates to the authoritative `wrl_ir.is_run_input_line`. This probe
# used to keep its own substring tuple -- a third spelling of one definition.
# Three spellings of a boundary is three chances to disagree with the parser
# about where the boundary is, and a lexical law that disagrees with the parser
# tests a private opinion rather than the language.
_has_scenario_syntax = B9._has_scenario_syntax


def main():
    print("[wrl-roundtrip-probe] format -> parse, over binding_run9's 6 worlds")
    print()
    print("PART 1 -- what differs")
    print("  %-12s %-16s %-16s %-8s %-8s" %
          ("world", "periods b->a", "claims b->a", "world=", "semid="))
    allsame_world = allsame_id = True
    for nm, txt in B9.WORLDS:
        # the INPUT is a pre-v0.4-0 COMBINED document, so it needs the explicit
        # compatibility mouth; the OUTPUT must parse under the STRICT world
        # parser -- that asymmetry IS the document boundary, mechanised.
        g = W.parse_wrl_legacy_document(txt)
        ftxt = F.format_wrl_core(g)
        g2 = W.parse_wrl_core(ftxt)
        a, b = WC.canonicalize_graph(g), WC.canonicalize_graph(g2)
        p1 = W.lower_program(txt, W.parse_wrl_legacy_document)
        p2 = W.lower_program(ftxt, W.parse_wrl_core)
        same_world = _world(a) == _world(b)
        same_id = p1.semantic_artifact_id == p2.semantic_artifact_id
        allsame_world &= same_world
        allsame_id &= same_id
        ra, rb = _run_inputs(a), _run_inputs(b)
        print("  %-12s %-16s %-16s %-8s %-8s"
              % (nm, "%d->%d" % (ra[0], rb[0]), "%d->%d" % (ra[1], rb[1]),
                 same_world, same_id))
    print()
    print("  => the ONLY thing that moves is the run inputs (periods, claims).")
    print("     world projection identical : %s" % allsame_world)
    print("     SemanticArtifactID identical: %s" % allsame_id)
    print()

    print("PART 2 -- the proposed restatements")
    l1w = l1i = l8i = True
    for nm, txt in B9.WORLDS:
        g = W.parse_wrl_legacy_document(txt)
        ftxt = F.format_wrl_core(g)
        g2 = W.parse_wrl_core(ftxt)
        a, b = WC.canonicalize_graph(g), WC.canonicalize_graph(g2)
        p1 = W.lower_program(txt, W.parse_wrl_legacy_document)
        p2 = W.lower_program(ftxt, W.parse_wrl_core)

        l1w &= _world(a) == _world(b)
        l1i &= (p1.semantic_artifact_id == p2.semantic_artifact_id
                and WC.serialize_artifact(p1.artifact)
                == WC.serialize_artifact(p2.artifact))
        # L8' has TWO halves. The SEMANTIC half (what reparsing yields) is not
        # sufficient on its own: a formatter emitting a literal `periods 0` line
        # would pass it while still writing ScenarioV1 syntax into a world
        # document. So the LEXICAL half asserts the emitted TEXT is clean.
        semantic_clean = (b.periods == 0
                          and all(len(x) == 0 for x in b.batches)
                          and not p2.epoch_inputs)
        lexical_clean = not _has_scenario_syntax(ftxt)
        l8i &= semantic_clean and lexical_clean

    for ok, label in (
        (l1w, "L1') WORLD round-trip: every canonical field except run inputs"),
        (l1i, "L1\") IDENTITY round-trip: artifact bytes + SemanticArtifactID"),
        (l8i, "L8') INVERSE: the formatter excludes run inputs SEMANTICALLY "
              "and LEXICALLY"),
    ):
        print("  [%s] %s" % ("PASS" if ok else "FAIL", label))
    print()

    # PART 3 -- NEGATIVE CONTROL. An assertion that has never been observed to
    # fail is not yet evidence. This proves the LEXICAL half of L8' is the thing
    # doing the work: a formatter that emitted a literal `periods 0` would still
    # satisfy the semantic half (reparsing yields 0 periods and no claims), and
    # the strengthened law must catch it anyway.
    print("PART 3 -- negative control: does the LEXICAL half actually bite?")
    g = W.parse_wrl_legacy_document(B9.WORLDS[0][1])
    leaky = F.format_wrl_core(g) + "periods 0\n"
    lg = W.parse_wrl_legacy_document(leaky)
    lc = WC.canonicalize_graph(lg)
    weak_ok = (lc.periods == 0 and all(len(x) == 0 for x in lc.batches))
    strong_ok = not _has_scenario_syntax(leaky)
    # a THIRD, independent witness: the strict world parser itself refuses the
    # leaky text. The lexical half and the strict parser agree, which is what
    # makes the restatement mechanically enforced rather than merely asserted.
    try:
        W.parse_wrl_core(leaky)
        strict_ok = True
    except WC.WrlValidationError as e:
        strict_ok = (e.code != W.WRL_WORLD_SOURCE_HAS_SCENARIO)
    bites = weak_ok and not strong_ok and not strict_ok
    print("     a formatter emitting a literal `periods 0`:")
    print("       semantic-only L8' (the weak form) : %s"
          % ("PASSES -- would not catch it" if weak_ok else "fails"))
    print("       lexical L8'     (the ruled form)  : %s"
          % ("passes" if strong_ok else "FAILS -- catches it"))
    print("       strict parse_wrl_core (Q2 mouth)  : %s"
          % ("accepts" if strict_ok else "REJECTS -- catches it"))
    print("  [%s] L8'-control) the lexical half is load-bearing, not vacuous"
          % ("PASS" if bites else "FAIL"))
    print()
    ok = l1w and l1i and l8i and bites
    print("[wrl-roundtrip-probe] %s" % ("ALL PASS" if ok else "FAILURES"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
