"""binding_run9.py -- Phase 3B-2: canonical WRL Core formatter battery (L1-L10).

GPT-5.6's 3B priority ruling leads broad 3B with "canonical formatter + source
spans". 3B-1 shipped the span sidecar; 3B-2 is `format_wrl_core(graph)` in the
new `wrl_format.py`. The formatter canonicalizes first, so it is a pure function
of the semantic graph -- declaration order, surface choice, and source
whitespace all wash out.

  L1  parse_wrl_core(format(graph)) == graph                (round-trip)
  L2  format(parse(format(src)))    == format(src)          (idempotent/stable)
  L3  a formatting-only edit keeps the SemanticArtifactID
  L4  a formatting-only edit keeps CompilePlanDigest + BackendArtifactID
  L5  bootstrap & core surfaces of one world format to the IDENTICAL text
  L6  the formatter emits real WRL Core (parses back; ports == frozen registry)
  L7  declaration-order shuffle formats to the IDENTICAL text
  L8  run inputs (claims) survive format -> parse (epoch_inputs identical)
  L9  spans over the formatted text resolve every canonical object/edge (3B-1)
  L10 the formatted text runs ic_ref == ic32 == golden       (native)

Native is gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
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


def _snap(g):
    """A canonical, comparable snapshot of a WrlGraph (== graph, for L1/L7)."""
    cg = WC.canonicalize_graph(g)
    return (cg.profile, cg.periods, list(cg.nodes), list(cg.edges),
            [list(b) for b in cg.batches])


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

    # ---- L1 parse(format(graph)) == graph
    l1 = True
    for nm, txt in WORLDS:
        g = W.parse_wrl_core(txt)
        if _snap(W.parse_wrl_core(F.format_wrl_core(g))) != _snap(g):
            l1 = False
    rep(l1, None, "L1) parse_wrl_core(format(graph)) == graph, "
                  f"{len(WORLDS)} worlds")

    # ---- L2 format(parse(format(src))) == format(src)
    l2 = True
    for nm, txt in WORLDS:
        f1 = F.format_wrl_core(W.parse_wrl_core(txt))
        f2 = F.format_wrl_core(W.parse_wrl_core(f1))
        if f1 != f2:
            l2 = False
    rep(l2, None, "L2) format(parse(format(src))) == format(src) (idempotent)")

    # ---- L3 a formatting-only edit keeps the SemanticArtifactID
    l3 = True
    for nm, txt in WORLDS:
        base = W.lower_program(txt, W.parse_wrl_core)
        fmt = W.lower_program(F.format_source(txt), W.parse_wrl_core)
        if base.semantic_artifact_id != fmt.semantic_artifact_id:
            l3 = False
    rep(l3, None, "L3) a formatting-only edit keeps the SemanticArtifactID")

    # ---- L4 a formatting-only edit keeps CompilePlanDigest + BackendArtifactID
    l4 = True
    prof = B7._prof("auto")
    for nm, txt in WORLDS:
        cb = W.compile_program(W.lower_program(txt, W.parse_wrl_core), prof)
        cf = W.compile_program(
            W.lower_program(F.format_source(txt), W.parse_wrl_core), prof)
        if (cb.sealed_plan.compile_plan_digest
                != cf.sealed_plan.compile_plan_digest
                or cb.backend_artifact_id != cf.backend_artifact_id
                or cb.backend_content_hash != cf.backend_content_hash):
            l4 = False
    rep(l4, None, "L4) a formatting-only edit keeps CompilePlanDigest + "
                  "BackendArtifactID")

    # ---- L5 bootstrap & core surfaces format to the IDENTICAL text
    fb = F.format_source(BOOT_SRC, W.parse_wrl_bootstrap)
    fc = F.format_source(CORE_SRC, W.parse_wrl_core)
    l5 = (fb == fc)
    rep(l5, None, "L5) bootstrap & core surfaces format to identical text")

    # ---- L6 the formatter emits real WRL Core (parses back; ports == registry)
    l6 = True
    for nm, txt in WORLDS:
        out = F.format_wrl_core(W.parse_wrl_core(txt))
        # every node line advertises exactly the frozen port projection
        g = W.parse_wrl_core(out)          # parses as WRL Core (not bootstrap)
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
        base = F.format_wrl_core(W.parse_wrl_core(txt))
        shuf = F.format_wrl_core(W.parse_wrl_core(_shuffle_core(txt)))
        if base != shuf:
            l7 = False
    rep(l7, None, "L7) a declaration-order shuffle formats to identical text")

    # ---- L8 run inputs (claims) survive format -> parse
    l8 = True
    for nm, txt in WORLDS:
        base = W.lower_program(txt, W.parse_wrl_core)
        fmt = W.lower_program(F.format_source(txt), W.parse_wrl_core)
        if base.epoch_inputs != fmt.epoch_inputs or base.run_plan != fmt.run_plan:
            l8 = False
    rep(l8, None, "L8) run inputs (claims) survive format -> parse")

    # ---- L9 spans over the formatted text resolve every canonical object/edge
    l9 = True
    for nm, txt in WORLDS:
        out = F.format_source(txt)
        sp, sm = S.lower_core_with_spans(out, "fmt_%s.wrl" % nm)
        if S.unresolved_ir_elements(sp.artifact, sm) != ():
            l9 = False
    rep(l9, None, "L9) spans over the formatted text resolve every canonical "
                  "object/edge (3B-1 interop)")

    # ---- L10 the formatted text runs ic_ref == ic32 == golden (native)
    fmt_core = F.format_source(B7.W_CORE, W.parse_wrl_core)
    prog = W.lower_program(fmt_core, W.parse_wrl_core)
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
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
