"""binding_run9.py -- Phase 3B-2: canonical WRL Core formatter battery (L1-L10).

GPT-5.6's 3B priority ruling leads broad 3B with "canonical formatter + source
spans". 3B-1 shipped the span sidecar; 3B-2 is `format_wrl_core(graph)` in the
new `wrl_format.py`. The formatter canonicalizes first, so it is a pure function
of the semantic graph -- declaration order, surface choice, and source
whitespace all wash out.

  L1a WORLD round-trip: parse(format(g)) preserves the canonical world
  L1b IDENTITY round-trip: artifact bytes + SemanticArtifactID are preserved
  L2  format(parse(format(src)))    == format(src)          (idempotent/stable)
  L3  a formatting-only edit keeps the SemanticArtifactID
  L4  a formatting-only edit keeps CompilePlanDigest + BackendArtifactID
  L5  bootstrap & core surfaces of one world format to the IDENTICAL text
  L6  the formatter emits real WRL Core (parses back; ports == frozen registry)
  L7  declaration-order shuffle formats to the IDENTICAL text
  L8  the formatter EXCLUDES run inputs, semantically AND lexically
  L9  spans over the formatted text resolve every canonical object/edge (3B-1)
  L10 the formatted text runs ic_ref == ic32 == golden       (native)

Native is gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).

------------------------------------------------------------------------ L-0
L1 and L8 were RESTATED (GPT-5.6 ruling, Q1) because the v0.4-0 document
boundary REPEALED the laws they used to assert -- they were not broken, they
were obsolete. This battery predates the boundary: it was written when one
document carried BOTH the world and its run inputs, so it could say
"parse(format(g)) == g" over the whole graph and "claims survive a format
cycle". v0.4-0 made `periods` and `[epoch:N]` claims RUN INPUTS, deliberately
outside the world and outside the SemanticArtifactID. A world formatter that
still emitted them would now be the bug.

  L1 SPLITS. The WORLD half preserves every canonical field EXCEPT the run
     inputs, named by EXCLUSION (see `_world`) so that a field a later slice
     adds -- Slice B's route semantics, next -- is covered by default instead
     of being silently dropped by a frozen tuple. The IDENTITY half is the one
     that guards the spine: canonical artifact bytes + SemanticArtifactID.

  L8 INVERTS. It no longer asserts run inputs SURVIVE; it asserts they are
     provably GONE. Two independent halves, because the semantic half alone is
     insufficient: a formatter emitting a literal `periods 0` would satisfy
     "reparsing yields zero periods" while still writing ScenarioV1 syntax into
     a world document. The LEXICAL half catches that, and re-parsing the output
     through the STRICT `parse_wrl_core` mouth catches it a third time.
"""
import os
import sys
import copy
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import wrl_ir as W
import wrl_canonical as WC
import wrl_format as F
import wrl_spans as S
import wrl_plan as P
import compiler as C
import admit as AD
import binding_run3o as O
import binding_run7 as B7
from admit import mk_claim
from fixture import init_state_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

WORLDS = B7.WORLDS          # the same 6 core-surface worlds as 3D

# a bootstrap world and its core twin (same semantic graph, two surfaces) -- L5
BOOT_SRC = (
    "profile forge.world.core.v1\n"
    "periods 3\n"
    "pulser p0 periodic 2 0\n"
    "relay r0\n"
    "spinner sp w=8 n=4 rotor=16,0,0,0 configurable\n"
    "orb ob\n"
    "wire p0 -> r0\n"
    "wire r0 -> sp\n"
    "socket sp -> ob\n"
    "epoch 1: SetRotor sp 16,0,10,0 @1,1\n")
CORE_SRC = (
    "profile forge.world.core.v1\n"
    "periods 3\n"
    "[pulser:p0](mode=periodic, period=2, phase=0)\n"
    "[relay:r0]\n"
    "[spinner:sp](w=8, n=4, rotor=16.0.0.0, configurable)\n"
    "[orb:ob]\n"
    "[p0] --sig--> [r0]\n"
    "[r0] --sig--> [sp]\n"
    "[sp] --socket--> [ob]\n"
    "[epoch:1] @1,1 SetRotor sp 16.0.10.0\n")


# The RUN-INPUT fields of a canonical graph -- exactly what v0.4-0 moved out to
# ScenarioV1. Naming the EXCLUSIONS rather than the inclusions is deliberate
# (GPT-5.6, Q1): a hard-coded `(profile, nodes, edges)` tuple silently stops
# covering any field a later slice adds, and Slice B is about to add route
# semantics. Defined this way a new world field is IN the projection by default,
# and L1a keeps testing it with no edit here.
RUN_INPUT_FIELDS = ("periods", "batches")

def _has_scenario_syntax(text):
    """True when any line of `text` carries ScenarioV1 run-input syntax -- the
    lexical half of L8.

    Delegates to the AUTHORITATIVE `wrl_ir.is_run_input_line` rather than
    re-spelling the forms here. The previous version of this check was a
    hand-rolled substring list that included a bare `@`, which is WRONG twice
    over: `@` is frozen for world addressing/placement, so it appears in legal
    world source, and a substring list is a FORK of the parser's definition that
    drifts silently. A lexical assertion whose vocabulary disagrees with the
    parser's does not test the document boundary -- it tests a private opinion
    about it."""
    return any(W.is_run_input_line(ln.partition(";")[0].strip())
               for ln in text.splitlines())


def _world(g):
    """The canonical WORLD projection of a graph: every canonical field EXCEPT
    the run inputs. Reflective on purpose -- see RUN_INPUT_FIELDS."""
    cg = WC.canonicalize_graph(g)
    return tuple((f, getattr(cg, f)) for f in sorted(vars(cg))
                 if f not in RUN_INPUT_FIELDS)


def _shuffle_core(txt):
    """Reverse the declaration order of a core-surface source (semantically
    identical, presentationally different) -- keeps profile/periods first."""
    lines = [ln for ln in txt.splitlines() if ln.strip()]
    head = lines[:2]                       # profile, periods
    rest = lines[2:]
    return "\n".join(head + list(reversed(rest))) + "\n"


def main():
    print("[BINDING wrl-3b2] canonical WRL Core formatter")
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

    # ---- L1a WORLD round-trip / L1b IDENTITY round-trip
    # The INPUT is a pre-v0.4-0 COMBINED document, so it needs the explicit
    # compatibility mouth; the OUTPUT must parse under the STRICT world parser.
    # That asymmetry is the document boundary, mechanised: if the formatter ever
    # leaked a run input, `parse_wrl_core` below would refuse the text outright.
    l1a = l1b = True
    for nm, txt in WORLDS:
        g = W.parse_wrl_legacy_document(txt)
        ftxt = F.format_wrl_core(g)
        if _world(W.parse_wrl_core(ftxt)) != _world(g):
            l1a = False
        p1 = W.lower_program(txt, W.parse_wrl_legacy_document)
        p2 = W.lower_program(ftxt, W.parse_wrl_core)
        if (p1.semantic_artifact_id != p2.semantic_artifact_id
                or WC.serialize_artifact(p1.artifact)
                != WC.serialize_artifact(p2.artifact)):
            l1b = False
    rep(l1a, None, "L1a) WORLD round-trip: every canonical field except the "
                   f"run inputs, {len(WORLDS)} worlds")
    rep(l1b, None, "L1b) IDENTITY round-trip: canonical artifact bytes + "
                   "SemanticArtifactID")

    # ---- L2 format(parse(format(src))) == format(src)
    l2 = True
    for nm, txt in WORLDS:
        f1 = F.format_wrl_core(W.parse_wrl_legacy_document(txt))
        f2 = F.format_wrl_core(W.parse_wrl_legacy_document(f1))
        if f1 != f2:
            l2 = False
    rep(l2, None, "L2) format(parse(format(src))) == format(src) (idempotent)")

    # ---- L3 a formatting-only edit keeps the SemanticArtifactID
    l3 = True
    for nm, txt in WORLDS:
        base = W.lower_program(txt, W.parse_wrl_legacy_document)
        fmt = W.lower_program(F.format_source(txt, W.parse_wrl_legacy_document), W.parse_wrl_legacy_document)
        if base.semantic_artifact_id != fmt.semantic_artifact_id:
            l3 = False
    rep(l3, None, "L3) a formatting-only edit keeps the SemanticArtifactID")

    # ---- L4 a formatting-only edit keeps CompilePlanDigest + BackendArtifactID
    l4 = True
    prof = B7._prof("auto")
    for nm, txt in WORLDS:
        cb = W.compile_program(W.lower_program(txt, W.parse_wrl_legacy_document), prof)
        cf = W.compile_program(
            W.lower_program(F.format_source(txt, W.parse_wrl_legacy_document), W.parse_wrl_legacy_document), prof)
        if (cb.sealed_plan.compile_plan_digest
                != cf.sealed_plan.compile_plan_digest
                or cb.backend_artifact_id != cf.backend_artifact_id
                or cb.backend_content_hash != cf.backend_content_hash):
            l4 = False
    rep(l4, None, "L4) a formatting-only edit keeps CompilePlanDigest + "
                  "BackendArtifactID")

    # ---- L5 bootstrap & core surfaces format to the IDENTICAL text
    fb = F.format_source(BOOT_SRC, W.parse_wrl_bootstrap)
    fc = F.format_source(CORE_SRC, W.parse_wrl_legacy_document)
    l5 = (fb == fc)
    rep(l5, None, "L5) bootstrap & core surfaces format to identical text")

    # ---- L6 the formatter emits real WRL Core (parses back; ports == registry)
    l6 = True
    for nm, txt in WORLDS:
        out = F.format_wrl_core(W.parse_wrl_legacy_document(txt))
        # every node line advertises exactly the frozen port projection
        g = W.parse_wrl_legacy_document(out)          # parses as WRL Core (not bootstrap)
        for role, name, _cfg in g.nodes:
            want = "{%s}" % ", ".join(sorted(WC.port_projection(role)))
            if want not in out:
                l6 = False
        # bootstrap parser must NOT accept core notation (it is genuinely Core)
        try:
            W.parse_wrl_bootstrap(out)
            l6 = False
        except WC.WrlValidationError:
            pass
    rep(l6, None, "L6) formatter emits real WRL Core (parses back; ports == "
                  "frozen registry; not bootstrap)")

    # ---- L7 a declaration-order shuffle formats to the IDENTICAL text
    l7 = True
    for nm, txt in WORLDS:
        base = F.format_wrl_core(W.parse_wrl_legacy_document(txt))
        shuf = F.format_wrl_core(W.parse_wrl_legacy_document(_shuffle_core(txt)))
        if base != shuf:
            l7 = False
    rep(l7, None, "L7) a declaration-order shuffle formats to identical text")

    # ---- L8 the formatter EXCLUDES run inputs (the INVERSE of the old law)
    l8 = True
    for nm, txt in WORLDS:
        ftxt = F.format_source(txt, W.parse_wrl_legacy_document)
        cg = WC.canonicalize_graph(W.parse_wrl_legacy_document(ftxt))
        prog = W.lower_program(ftxt, W.parse_wrl_legacy_document)
        # (a) SEMANTIC: reparsing the output yields no run inputs at all.
        semantic_clean = (cg.periods == 0
                          and all(len(b) == 0 for b in cg.batches)
                          and not prog.epoch_inputs)
        # (b) LEXICAL: the output does not even CONTAIN ScenarioV1 syntax.
        # Necessary because (a) alone would accept a literal `periods 0` line.
        # The vocabulary is the PARSER's, not this battery's -- see
        # `_has_scenario_syntax`.
        lexical_clean = not _has_scenario_syntax(ftxt)
        # (c) the STRICT world mouth accepts the output -- a third, independent
        # witness, owned by the parser rather than by this battery.
        try:
            W.parse_wrl_core(ftxt)
            strict_clean = True
        except WC.WrlValidationError:
            strict_clean = False
        if not (semantic_clean and lexical_clean and strict_clean):
            l8 = False
    rep(l8, None, "L8) the formatter EXCLUDES run inputs -- semantically, "
                  "lexically, and per the strict world parser")

    # ---- L9 spans over the formatted text resolve every canonical object/edge
    l9 = True
    for nm, txt in WORLDS:
        out = F.format_source(txt, W.parse_wrl_legacy_document)
        sp, sm = S.lower_legacy_document_with_spans(out, "fmt_%s.wrl" % nm)
        if S.unresolved_ir_elements(sp.artifact, sm) != ():
            l9 = False
    rep(l9, None, "L9) spans over the formatted text resolve every canonical "
                  "object/edge (3B-1 interop)")

    # ---- L10 the formatted text runs ic_ref == ic32 == golden (native)
    fmt_core = F.format_source(B7.W_CORE, W.parse_wrl_legacy_document)
    prog = W.lower_program(fmt_core, W.parse_wrl_legacy_document)
    plan = P.artifact_to_compile_plan_v1(prog.sealed_artifact)
    view = P.plan_view(plan)
    fx = prog.as_fixture_for_test()
    batches = [[mk_claim(1, 1, B7.S((16, 0, 10, 0)))],
               [mk_claim(2, 2, B7.S((16, 0, 20, 0))), mk_claim(3, 3, B7.Rf)],
               [mk_claim(4, 4, B7.S((16, 0, 30, 0)))]]
    world0 = init_state_v6(O.FX)
    world0["fault_ob"] = 1
    gold = O._golden_traj(AD.init_claimstate(), world0, batches, 1)

    def _traj(reducer):
        claim = AD.init_claimstate()
        world = copy.deepcopy(world0)
        out = []
        step, _ = C.compile_step_v6(view)
        for e, batch in enumerate(batches):
            claim, cfg_map, resets = AD.admit_step(claim, batch, 1 + e, fx)
            ec = C.enc_config_bundle(view, cfg_map, resets)
            world = C.dec_state_v6(view, reducer(
                f"(({step} {ec}) {C.enc_state_v6(view, world)})"))
            out.append(copy.deepcopy(world))
        return out

    ref = _traj(O.norm)
    l10r = all(ref[e] == gold[e][0] for e in range(len(batches)))
    l10n = None
    if not SKIP_NATIVE:
        nat = _traj(O.native)
        l10n = all(nat[e] == gold[e][0] for e in range(len(batches)))
    rep(l10r, l10n, "L10) the formatted text runs ic_ref == ic32 == golden")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-3b2] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] the formatter canonicalizes first, so formatting is a pure "
          "function of the semantic graph -- it can never move an identity.")
    print("  [note] L1/L8 are the L-0 RESTATEMENTS. The formatter emits a WORLD "
          "document: the world survives exactly, the identity survives exactly, "
          "and the run inputs are provably absent.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
