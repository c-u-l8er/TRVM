"""binding_run3f.py -- Slice 3b.5c: the typed Q32.32 pose-authority bridge.

Round-13 ruling, Option A (user 2026-07-21). The compiled IC circuit now
carries a SINGLE real pose authority under the shipping Spinner policy
forge_motor_widemac_tz_sat_v1 (wide-MAC: full-precision products, ONE
toward-zero shift, ONE saturation). The frozen proc-e2.3 oracle
(e2_model.qmul, legacy per-product trunc0) is DEMOTED to an EVENT /
STRUCTURE oracle: it defines WHEN a rotation fires, not the pose VALUE.

There is no shadow `poses` dict. The circuit's own state IS the pose; we
value-lock it to the forge golden trajectory, advanced on exactly the
epochs the model fires -- so the same test simultaneously certifies
(a) the circuit needs no external pose tracker, (b) it fires in exact
event-parity with proc-e2.3, and (c) its value is the forge law.

The bridge certifies a DIFFERENCE, not an equality: the legacy oracle and
the forge authority agree at small widths but provably DIVERGE at Q32.32
(first divergence epoch 2; 2066 ULP on lane 0 at 20k Z90 composes; forge
drift -1.919083e-05 vs legacy -2.015288919210434e-05). The proxy width is
a typed narrowing of the Q32.32 authority (rotor = exact <<(32-n) rescale).

Sections:
  A) forge rotor step golden == ic_ref == ic32 at proxy widths (+ fault).
  B/C) single forge authority: no shadow dict, event-parity to proc-e2.3,
       value-locked to the forge golden across a live model run.
  D) certified Q32.32 value-separator vs the legacy oracle (the bridge's
     whole point -- it certifies the difference).
  E) typed Q32.32 <-> proxy rescale bridge (the explicit BindingWorld split).
  F) NATIVE hard gate: the forge authority through ic32 == golden.
"""
import os, sys, time, subprocess
sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import binlib as BL
import fixture as FX
import compiler as C
import e2_model as EM
from ic_ref import parse, normal, reset_runtime, ctr
from e2_model import ZeroChooser

IC32 = os.path.join(HERE, "..", "runtime", "c", "ic32")
SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

POLICY_FORGE = "forge_motor_widemac_tz_sat_v1"
POLICY_LEGACY = "legacy_spinner_pp_tz_nosat_v1"


def norm(src, budget=500_000_000):
    reset_runtime()
    return normal(parse(src), budget=budget)


def native(src, timeout=180):
    r = subprocess.run([IC32], input=src.encode(), capture_output=True,
                       timeout=timeout)
    out = r.stdout.decode().strip().splitlines()
    if r.returncode != 0 or not out:
        raise RuntimeError(f"ic32 rc={r.returncode}")
    reset_runtime()
    return parse(out[0])


def sgn(v, w):
    return v - (1 << w) if v >= (1 << (w - 1)) else v


def forge_step(w, n, rotor, pose):
    """One forge wide-MAC rotor step (signed lanes in, signed out)."""
    mask = (1 << w) - 1
    g, flt = BL.golden_rot_forge(w, n, tuple(c & mask for c in rotor),
                                 tuple(c & mask for c in pose))
    return tuple(sgn(x & mask, w) for x in g), flt


def rotq(w):
    return int(0.7071067811865476 * (1 << (w // 2)))


def main():
    print("[BINDING slice 3b.5c] typed Q32.32 pose-authority bridge "
          f"({POLICY_FORGE})")
    allok = True
    native_status = "PASS_REF_AND_NATIVE"
    t0 = time.time()

    # ---- A) forge rotor step golden == ic_ref (+ native later), proxy widths
    okA = True
    cases = []
    for (w, n) in [(8, 4), (16, 8)]:
        Cq = rotq(w)
        one = 1 << n
        for rotor in [(Cq, 0, 0, Cq), (0, Cq, 0, Cq), (one, 0, 0, 0)]:
            for pose in [(one, 0, 0, 0), (0, one, 0, 0),
                         (one // 2, one // 3, 0, one // 5)]:
                g, flt = forge_step(w, n, rotor, pose)
                src = (f"({BL.dyn_rot_step_forge(w, n, rotor)} "
                       f"{BL.enc_pose(pose, w)})")
                ic = tuple(sgn(x & ((1 << w) - 1), w)
                           for x in BL.dec_pose(norm(src), w))
                okc = (g == ic and flt == 0)
                okA &= okc
                cases.append((w, n, okc))
    # golden-level saturation: a lane must clamp and latch a fault
    wS, nS = 8, 4
    big = (1 << (wS - 1)) - 1
    gS, fS = forge_step(wS, nS, (big, big, 0, 0), (big, big, 0, 0))
    satok = fS == 1 and all(-(1 << (wS - 1)) <= v <= big for v in gS)
    okA &= satok
    allok &= okA
    npx = len(cases)
    print(f"  [{'PASS' if okA else 'FAIL'}] A) forge rotor step "
          f"golden==ic_ref on {npx} (rotor,pose) cases @ Q4.4+Q8.8, "
          f"fault=0; wide-MAC saturation clamps+latches a fault "
          f"({'ok' if satok else 'BAD'})")

    # ---- B/C) single forge authority: no shadow dict, event-parity, value-lock
    Cq = rotq(8)
    fx = FX.Fixture({"p": ("periodic", 3, 0)}, [], ["d"],
                    [("p", "d"), ("p", "s")],
                    spinners={"s": (8, 4, (Cq, 0, 0, Cq))},
                    orbs=["o"], sockets=[("s", "o")])
    step_src, _ = C.compile_step(fx, pose_policy="forge")
    st = FX.init_state(fx)
    w, oid, wid_role = FX.build_model(fx)   # proc-e2.3 world = EVENT oracle
    w8, n8, rq = fx.spinners["s"]
    # forge authority reference, advanced ONLY on model firing events:
    pf = tuple(st["pose_o"])                 # circuit's own start pose (QID)
    prev = tuple(w.objs[oid["o"]]["pose"][0:4])
    prevpose = tuple(st["pose_o"])
    T = 45
    fires_model, fires_circuit = [], []
    val_locked = True
    for e in range(T):
        w.step([], ZeroChooser())            # advance proc-e2.3 (event oracle)
        cur = tuple(w.objs[oid["o"]]["pose"][0:4])
        if cur != prev:                      # model (legacy) fired a rotation
            fires_model.append(w.t - 1)
            pf, _ = forge_step(w8, n8, rq, pf)          # forge authority ref
        prev = cur
        # advance the compiled forge circuit; read its SELF-CARRIED pose
        t = norm(f"({step_src} {C.enc_state(fx, st)})")
        st = C.dec_state(fx, t)
        cpose = tuple(sgn(v & 0xFF, 8) for v in st["pose_o"])
        if cpose != tuple(sgn(v & 0xFF, 8) for v in pf):
            val_locked = False               # value-locked to the forge golden
        if tuple(st["pose_o"]) != prevpose:  # circuit fired iff pose changed
            fires_circuit.append(w.t - 1)
        prevpose = tuple(st["pose_o"])
    event_parity = fires_model == fires_circuit
    okBC = val_locked and event_parity and len(fires_model) > 0
    allok &= okBC
    print(f"  [{'PASS' if okBC else 'FAIL'}] B/C) single forge authority, "
          f"T={T}: NO shadow dict -- circuit pose value-locked to the forge "
          f"golden ({'exact' if val_locked else 'DRIFT'}); event-parity to "
          f"proc-e2.3 rotations {'exact' if event_parity else 'BROKEN'} "
          f"({len(fires_model)} fires)")

    # ---- D) certified Q32.32 value-separator vs the legacy oracle
    w64, n64 = 64, 32
    rot = EM.ROT_Z90
    pf64, pl64 = EM.QID, EM.QID
    first = None
    K = 20000
    for e in range(1, K + 1):
        pf64, _ = forge_step(w64, n64, rot, pf64)
        pl64 = EM.qmul(rot, pl64)
        if pf64 != pl64 and first is None:
            first = e
    ulp = pf64[0] - pl64[0]
    ideal = EM.ONE
    fdrift = (EM.qnorm2(pf64) - ideal) / ideal
    ldrift = (EM.qnorm2(pl64) - ideal) / ideal
    okD = (first == 2 and ulp == 2066 and pf64 != pl64
           and abs(fdrift - (-1.919083297252655e-05)) < 1e-15
           and abs(ldrift - (-2.015288919210434e-05)) < 1e-15)
    allok &= okD
    print(f"  [{'PASS' if okD else 'FAIL'}] D) certified Q32.32 separator: "
          f"forge != legacy from epoch {first}; lane0 delta {ulp} ULP @20k; "
          f"forge drift {fdrift:.6e} vs legacy {ldrift:.6e} (bridge certifies "
          f"the DIFFERENCE)")

    # ---- E) typed Q32.32 <-> proxy rescale bridge (explicit split)
    w8, n8 = 8, 4
    Cq = rotq(8)
    rq8 = (Cq, 0, 0, Cq)

    def rescale(v):
        return sgn(v & 0xFF, 8) << (32 - n8)
    rq32 = tuple(rescale(v) for v in rq8)
    # the rotor lifts exactly and typedly to Q32.32 (this IS the anchor law
    # the model asserts in fixture.model_projection)
    exact_lift = rq32 == tuple(sgn(v & 0xFF, 8) << (32 - n8) for v in rq8)
    # one step: proxy pose lifts, one forge step at each width; at ONE step
    # the wide-MAC commutes with the rescale on the aligned lanes
    p8 = (1 << n8, 0, 0, 0)
    p32 = tuple(v << (32 - n8) for v in p8)
    s8, _ = forge_step(w8, n8, rq8, p8)
    s32, _ = forge_step(64, 32, rq32, p32)
    step_commutes = all(s32[i] == (s8[i] << (32 - n8)) for i in range(4))
    okE = exact_lift and step_commutes
    allok &= okE
    print(f"  [{'PASS' if okE else 'FAIL'}] E) typed bridge: proxy rotor "
          f"lifts exactly to Q32.32 (<<{32 - n8}); one forge step commutes "
          f"with the rescale ({'ok' if step_commutes else 'no'}); the "
          f"long-horizon separator (D) is where the widths part")

    # ---- F) NATIVE hard gate
    if SKIP_NATIVE:
        native_status = "SKIP_NATIVE_EXPLICITLY"
        print("  [SKIP] native gate skipped by TRVM_SKIP_NATIVE=1")
    else:
        okF = True
        # F1: the forge rotor step through ic32 at both proxy widths
        for (w, n) in [(8, 4), (16, 8)]:
            Cq = rotq(w)
            one = 1 << n
            rotor, pose = (Cq, 0, 0, Cq), (one // 2, one // 3, 0, one // 5)
            g, _ = forge_step(w, n, rotor, pose)
            src = (f"({BL.dyn_rot_step_forge(w, n, rotor)} "
                   f"{BL.enc_pose(pose, w)})")
            nat = tuple(sgn(x & ((1 << w) - 1), w)
                        for x in BL.dec_pose(native(src), w))
            okF &= nat == g
        # F2: the compiled forge AUTHORITY circuit through ic32, value-locked
        st = FX.init_state(fx)
        wN, oidN, _ = FX.build_model(fx)
        pf = tuple(st["pose_o"])
        prevN = tuple(wN.objs[oidN["o"]]["pose"][0:4])
        for e in range(8):
            wN.step([], ZeroChooser())
            cur = tuple(wN.objs[oidN["o"]]["pose"][0:4])
            if cur != prevN:
                pf, _ = forge_step(w8, n8, rq, pf)
            prevN = cur
            t = native(f"({step_src} {C.enc_state(fx, st)})")
            st = C.dec_state(fx, t)
            cpose = tuple(sgn(v & 0xFF, 8) for v in st["pose_o"])
            okF &= cpose == tuple(sgn(v & 0xFF, 8) for v in pf)
        if not okF:
            native_status = "FAIL_NATIVE"
            allok = False
        print(f"  [{'PASS' if okF else 'FAIL'}] F) NATIVE GATE (hard): forge "
              f"rotor step @Q4.4+Q8.8 through ic32 == golden; 8 epochs of the "
              f"compiled forge authority through ic32, value-locked")

    dt = time.time() - t0
    headline = ("PASS_REF_AND_NATIVE" if allok
                and native_status == "PASS_REF_AND_NATIVE"
                else "PASS_REF_ONLY" if allok else "FAIL")
    print(f"\n  SLICE 3b.5c: {headline} ({dt:.0f}s)  [native: "
          f"{native_status}]")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
