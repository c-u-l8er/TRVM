"""binding_run10.py -- Phase 3B-3: stable diagnostics battery (G1-G12).

3B-1 gave stable source spans; 3B-2 gave canonical text; 3B-3 renders a typed
rejection as a portable record `Diagnostic{code, message, primary_span,
related_span, canonical_object_id}` (wrl_diagnostics.py). The diagnostic is a
PURE SIDECAR: the verdict is still the untouched validator's, the code/message
come from the real exception, and the spans come from the 3B-1 scan -- so a
diagnostic can never move an identity and its code/object_id are stable under
reformatting.

  G1  a clean source yields NO diagnostics                       (all 6 worlds)
  G2  duplicate id  -> code + object_id + primary(2nd) + related(1st decl)
  G3  unknown endpoint -> code + edge primary span + missing-name object_id
  G4  illegal port pair (wire into an orb) -> code + edge primary span
  G5  controller conflict -> code + primary(2nd) + related(1st) controller edge
  G6  clock range (phase >= period) -> code + node span (authoritative locator)
  G7  every primary span, sliced from source, CONTAINS the offending token
  G8  reformatting (comments/blanks/indent) keeps code+object_id; spans MOVE
  G9  running the diagnostic pass never perturbs identity (sealed bytes+sem id)
  G10 render() is deterministic (same source -> byte-identical string)
  G11 spans/file_id never appear in the sealed artifact bytes of a clean world
  G12 a clean world (zero diagnostics) still runs ic_ref==ic32==golden (native)

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
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
import wrl_diagnostics as DG
import wrl_plan as P
import compiler as C
import admit as AD
import binding_run3o as O
import binding_run7 as B7
from admit import mk_claim
from fixture import init_state_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

WORLDS = B7.WORLDS

GOOD = (
    "profile forge.world.core.v1\n"
    "periods 1\n"
    "[pulser:p0](mode=periodic, period=2, phase=0)\n"
    "[door:d0]\n"
    "[door:d1]\n"
    "[p0] --sig--> [d0]\n")

DUP = (
    "profile forge.world.core.v1\n"
    "periods 1\n"
    "[pulser:p0](mode=periodic, period=2, phase=0)\n"
    "[door:d0]\n"
    "[door:d0]\n"
    "[p0] --sig--> [d0]\n")

UNKNOWN_EP = (
    "profile forge.world.core.v1\n"
    "periods 1\n"
    "[pulser:p0](mode=periodic, period=2, phase=0)\n"
    "[door:d0]\n"
    "[p0] --sig--> [dX]\n")

WIRE_INTO_ORB = (
    "profile forge.world.core.v1\n"
    "periods 1\n"
    "[pulser:p0](mode=periodic, period=2, phase=0)\n"
    "[orb:ob]\n"
    "[p0] --sig--> [ob]\n")

TWO_CONTROLLERS = (
    "profile forge.world.core.v1\n"
    "periods 1\n"
    "[pulser:p0](mode=periodic, period=2, phase=0)\n"
    "[spinner:sa](w=8, n=4, rotor=1.0.0.0)\n"
    "[spinner:sb](w=8, n=4, rotor=1.0.0.0)\n"
    "[orb:ob]\n"
    "[p0] --sig--> [sa]\n"
    "[p0] --sig--> [sb]\n"
    "[sa] --socket--> [ob]\n"
    "[sb] --socket--> [ob]\n")

BAD_CLOCK = (
    "profile forge.world.core.v1\n"
    "periods 1\n"
    "[pulser:p0](mode=periodic, period=2, phase=5)\n"
    "[door:d0]\n"
    "[p0] --sig--> [d0]\n")


def _slice(src, span):
    return src[span.start_offset:span.end_offset]


def _reformat(src):
    """A formatting-only edit: blank lines, indentation, and `;` comments --
    semantically identical WRL Core (mirrors 3B-2's formatting-only edits)."""
    out = []
    for ln in src.splitlines():
        if ln.strip():
            out.append("   " + ln + "    ; note")
        out.append("")
    return "\n".join(out) + "\n"


def main():
    print("[BINDING wrl-3b3] stable diagnostics")
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

    # ---- G1 clean sources yield NO diagnostics
    g1 = all(DG.diagnose_legacy_document(txt) == () for _nm, txt in WORLDS)
    g1 = g1 and DG.diagnose_legacy_document(GOOD) == ()
    rep(g1, None, "G1) a clean source yields no diagnostics (6 worlds + GOOD)")

    # ---- G2 duplicate id
    d = DG.diagnose_legacy_document(DUP)
    g2 = (len(d) == 1 and d[0].code == WC.WRL_DUPLICATE_ID
          and d[0].canonical_object_id == "d0"
          and d[0].primary_span is not None and d[0].related_span is not None
          # primary is the SECOND declaration, related the FIRST
          and d[0].primary_span.start_line > d[0].related_span.start_line)
    rep(g2, None, "G2) duplicate id -> code + object_id + primary(2nd) + "
                  "related(1st decl)")

    # ---- G3 unknown endpoint
    d = DG.diagnose_legacy_document(UNKNOWN_EP)
    g3 = (len(d) == 1 and d[0].code == WC.WRL_UNKNOWN_ENDPOINT
          and d[0].canonical_object_id == "dX"
          and d[0].primary_span is not None)
    rep(g3, None, "G3) unknown endpoint -> code + edge primary span + "
                  "missing-name object_id")

    # ---- G4 illegal port pair (a signal wire into an orb)
    d = DG.diagnose_legacy_document(WIRE_INTO_ORB)
    g4 = (len(d) == 1 and d[0].code == WC.WRL_ILLEGAL_PORT_PAIR
          and d[0].canonical_object_id == "ob"
          and d[0].primary_span is not None)
    rep(g4, None, "G4) illegal port pair (wire into orb) -> code + edge "
                  "primary span")

    # ---- G5 controller conflict
    d = DG.diagnose_legacy_document(TWO_CONTROLLERS)
    g5 = (len(d) == 1 and d[0].code == WC.WRL_CONTROLLER_CONFLICT
          and d[0].canonical_object_id == "ob"
          and d[0].primary_span is not None and d[0].related_span is not None
          and d[0].primary_span.start_line > d[0].related_span.start_line)
    rep(g5, None, "G5) controller conflict -> code + primary(2nd) + "
                  "related(1st) controller edge")

    # ---- G6 clock range (authoritative per-node locator)
    d = DG.diagnose_legacy_document(BAD_CLOCK)
    g6 = (len(d) == 1 and d[0].code == WC.WRL_CLOCK_RANGE
          and d[0].canonical_object_id == "p0"
          and d[0].primary_span is not None)
    rep(g6, None, "G6) clock range (phase>=period) -> code + node span "
                  "(reuses WC._validate_config)")

    # ---- G7 every primary span slices to the offending token
    g7 = True
    checks = [(DUP, "d0"), (UNKNOWN_EP, "dX"), (WIRE_INTO_ORB, "ob"),
              (TWO_CONTROLLERS, "ob"), (BAD_CLOCK, "p0")]
    for src, tok in checks:
        dd = DG.diagnose_legacy_document(src)
        if not dd or dd[0].primary_span is None:
            g7 = False
            continue
        if tok not in _slice(src, dd[0].primary_span):
            g7 = False
    rep(g7, None, "G7) every primary span, sliced from source, contains the "
                  "offending token")

    # ---- G8 reformatting keeps code+object_id; spans MOVE
    g8 = True
    for src in (DUP, WIRE_INTO_ORB, TWO_CONTROLLERS, BAD_CLOCK):
        a = DG.diagnose_legacy_document(src)[0]
        b = DG.diagnose_legacy_document(_reformat(src))[0]
        if (a.code != b.code
                or a.canonical_object_id != b.canonical_object_id):
            g8 = False
        # spans must have moved (formatting changed the offsets)
        if a.primary_span is not None and b.primary_span is not None:
            if a.primary_span.start_offset == b.primary_span.start_offset:
                g8 = False
    rep(g8, None, "G8) reformatting keeps code+object_id; spans move "
                  "(diagnostic stability)")

    # ---- G9 running the diagnostic pass never perturbs identity
    g9 = True
    for _nm, txt in WORLDS:
        base = W.lower_program(txt, W.parse_wrl_legacy_document)
        _ = DG.diagnose_legacy_document(txt)               # side-effect-free sidecar
        after = W.lower_program(txt, W.parse_wrl_legacy_document)
        if (base.sealed_artifact.artifact != after.sealed_artifact.artifact
                or base.semantic_artifact_id != after.semantic_artifact_id):
            g9 = False
    rep(g9, None, "G9) running the diagnostic pass never perturbs identity "
                  "(sealed bytes + sem id)")

    # ---- G10 render() is deterministic
    g10 = True
    for src in (DUP, UNKNOWN_EP, WIRE_INTO_ORB, TWO_CONTROLLERS, BAD_CLOCK):
        r1 = DG.diagnose_legacy_document(src)[0].render()
        r2 = DG.diagnose_legacy_document(src)[0].render()
        if r1 != r2 or not r1:
            g10 = False
    rep(g10, None, "G10) render() is deterministic (same source -> identical "
                   "string)")

    # ---- G11 spans/file_id never appear in the sealed artifact bytes
    # (a distinctive sentinel file_id proves it too; "file_id" alone is a
    # substring of the legitimate "profile_id" artifact key, so we check the
    # SourceSpan field names + the sentinel value, not the bare word)
    SENTINEL = "SENTINEL_FILE_marker_zzq"
    g11 = True
    for _nm, txt in WORLDS:
        prog = W.lower_program(txt, W.parse_wrl_legacy_document)
        _ = DG.diagnose_legacy_document(txt, SENTINEL)     # run the sidecar with a sentinel
        blob = WC.serialize_artifact(prog.sealed_artifact.artifact)
        if isinstance(blob, bytes):
            blob = blob.decode("utf-8")
        if ("start_offset" in blob or "end_offset" in blob
                or "start_line" in blob or "primary_span" in blob
                or SENTINEL in blob or DG.DEFAULT_FILE_ID in blob):
            g11 = False
    rep(g11, None, "G11) span fields + sentinel file_id never appear in the "
                   "sealed artifact bytes")

    # ---- G12 a clean world still runs ic_ref==ic32==golden (native)
    prog = W.lower_program(B7.W_CORE, W.parse_wrl_legacy_document)
    assert DG.diagnose_legacy_document(B7.W_CORE) == ()      # clean world, no diagnostics
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
    g12r = all(ref[e] == gold[e][0] for e in range(len(batches)))
    g12n = None
    if not SKIP_NATIVE:
        nat = _traj(O.native)
        g12n = all(nat[e] == gold[e][0] for e in range(len(batches)))
    rep(g12r, g12n, "G12) a clean world (zero diagnostics) runs "
                    "ic_ref==ic32==golden")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-3b3] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] a diagnostic is a pure sidecar: the verdict stays the "
          "untouched validator's, the code/message come from the real "
          "exception, the spans come from the 3B-1 scan -- so it can never "
          "move an identity.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
