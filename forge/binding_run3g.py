"""binding_run3g.py -- Slice 3b.5d-1: the dynamic Spinner.

The 3b.5c pose authority bakes a CONSTANT rotor into the circuit
(dyn_rot_step_forge): a rotor change needs a recompile (the 3b.5a
EV_CONFIG kernel cache, keyed by rotor bytes). This slice makes the rotor
flow as DATA -- dyn_rot_step_forge_dyn is λR.λP, both operands runtime
TUP4 -- so a single compiled term applies ANY rotor with no recompilation,
under the same shipping forge wide-MAC policy (forge_motor_widemac_tz_sat_v1).

This is measure-before-building for 3b.5d-2 (wiring a dynamic rotor into
the fixture/state): section D prices the rotor-as-data step against the
baked-in constant-rotor step, so the fixture change is decided on a number.

Sections:
  A) dynamic forge step golden == ic_ref == ic32, both proxy widths (+ fault).
  B) equivalence: the dynamic path == the constant-rotor path for one rotor.
  C) runtime rotor change: ONE compiled term, a sequence of distinct rotors,
     each == its golden -- the dynamic Spinner capability, no recompile.
  D) cost: dynamic-rotor vs constant-rotor step interactions (the price of
     flowing the rotor as data).
  E) NATIVE hard gate.
"""
import os, sys, time, subprocess
sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import binlib as BL
from ic_ref import parse, normal, reset_runtime, ctr

IC32 = os.path.join(HERE, "..", "runtime", "c", "ic32")
SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"
POLICY_FORGE = "forge_motor_widemac_tz_sat_v1"


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


def golden(w, n, rotor, pose):
    mask = (1 << w) - 1
    g, flt = BL.golden_rot_forge(w, n, tuple(c & mask for c in rotor),
                                 tuple(c & mask for c in pose))
    return tuple(sgn(x & mask, w) for x in g), flt


def dyn_apply(w, n, rotor, pose, runner):
    src = (f"(({BL.dyn_rot_step_forge_dyn(w, n)} {BL.enc_pose(rotor, w)}) "
           f"{BL.enc_pose(pose, w)})")
    return tuple(sgn(x & ((1 << w) - 1), w)
                 for x in BL.dec_pose(runner(src), w))


def rotq(w):
    return int(0.7071067811865476 * (1 << (w // 2)))


def main():
    print(f"[BINDING slice 3b.5d-1] the dynamic Spinner ({POLICY_FORGE})")
    allok = True
    native_status = "PASS_REF_AND_NATIVE"
    t0 = time.time()

    # ---- A) dynamic forge step golden == ic_ref, both widths (+ fault)
    okA = True
    ncases = 0
    for (w, n) in [(8, 4), (16, 8)]:
        Cq = rotq(w)
        one = 1 << n
        for rotor in [(Cq, 0, 0, Cq), (0, Cq, 0, Cq), (one, 0, 0, 0)]:
            for pose in [(one, 0, 0, 0), (0, one, 0, 0),
                         (one // 2, one // 3, 0, one // 5)]:
                g, flt = golden(w, n, rotor, pose)
                ic = dyn_apply(w, n, rotor, pose, norm)
                okA &= (g == ic and flt == 0)
                ncases += 1
    wS, nS = 8, 4
    big = (1 << (wS - 1)) - 1
    gS, fS = golden(wS, nS, (big, big, 0, 0), (big, big, 0, 0))
    satok = fS == 1
    okA &= satok
    allok &= okA
    print(f"  [{'PASS' if okA else 'FAIL'}] A) dynamic forge step "
          f"golden==ic_ref on {ncases} (rotor,pose) cases @ Q4.4+Q8.8, "
          f"fault=0; wide-MAC saturation latches a fault "
          f"({'ok' if satok else 'BAD'})")

    # ---- B) dynamic path == constant-rotor (baked-in) path
    okB = True
    for (w, n) in [(8, 4), (16, 8)]:
        Cq = rotq(w)
        one = 1 << n
        rotor, pose = (Cq, 0, 0, Cq), (one // 2, one // 3, 0, one // 5)
        g, _ = golden(w, n, rotor, pose)
        dyn = dyn_apply(w, n, rotor, pose, norm)
        const_src = (f"({BL.dyn_rot_step_forge(w, n, rotor)} "
                     f"{BL.enc_pose(pose, w)})")
        const = tuple(sgn(x & ((1 << w) - 1), w)
                      for x in BL.dec_pose(norm(const_src), w))
        okB &= (dyn == const == g)
    allok &= okB
    print(f"  [{'PASS' if okB else 'FAIL'}] B) rotor-as-data == baked-in "
          f"constant rotor (same forge policy, both widths)")

    # ---- C) runtime rotor change: ONE compiled term, a rotor sequence
    w, n = 8, 4
    one = 1 << n
    Cq = rotq(w)
    term = BL.dyn_rot_step_forge_dyn(w, n)   # compiled ONCE
    rotors = [(Cq, 0, 0, Cq), (0, Cq, 0, Cq), (one, 0, 0, 0),
              (Cq, Cq, 0, 0), (0, 0, Cq, Cq)]
    pose = (one // 2, 0, one // 3, 0)
    okC = True
    for rq in rotors:
        g, _ = golden(w, n, rq, pose)
        src = (f"(({term} {BL.enc_pose(rq, w)}) {BL.enc_pose(pose, w)})")
        ic = tuple(sgn(x & ((1 << w) - 1), w)
                   for x in BL.dec_pose(norm(src), w))
        okC &= (ic == g)
    allok &= okC
    print(f"  [{'PASS' if okC else 'FAIL'}] C) runtime rotor change: one "
          f"compiled term, {len(rotors)} distinct rotors, each == golden "
          f"-- NO recompilation (the dynamic Spinner)")

    # ---- D) cost: dynamic-rotor vs constant-rotor step
    w, n = 8, 4
    Cq = rotq(w)
    rotor, pose = (Cq, 0, 0, Cq), (one // 2, one // 3, 0, one // 5)
    dsrc = (f"(({BL.dyn_rot_step_forge_dyn(w, n)} {BL.enc_pose(rotor, w)}) "
            f"{BL.enc_pose(pose, w)})")
    norm(dsrc)
    dyn_cost = sum(ctr.values())
    csrc = (f"({BL.dyn_rot_step_forge(w, n, rotor)} "
            f"{BL.enc_pose(pose, w)})")
    norm(csrc)
    const_cost = sum(ctr.values())
    ratio = dyn_cost / const_cost if const_cost else 0.0
    print(f"  [MEAS] D) Q4.4 step cost: dynamic-rotor {dyn_cost} vs "
          f"constant-rotor {const_cost} interactions ({ratio:.2f}x) -- the "
          f"price of flowing the rotor as data")

    # ---- E) NATIVE hard gate
    if SKIP_NATIVE:
        native_status = "SKIP_NATIVE_EXPLICITLY"
        print("  [SKIP] native gate skipped by TRVM_SKIP_NATIVE=1")
    else:
        okE = True
        for (w, n) in [(8, 4), (16, 8)]:
            Cq = rotq(w)
            one = 1 << n
            rotor, pose = (Cq, 0, 0, Cq), (one // 2, one // 3, 0, one // 5)
            g, _ = golden(w, n, rotor, pose)
            nat = dyn_apply(w, n, rotor, pose, native)
            okE &= (nat == g)
        # runtime rotor change through ic32 (one term, two rotors)
        w, n = 8, 4
        one = 1 << n
        Cq = rotq(w)
        term = BL.dyn_rot_step_forge_dyn(w, n)
        pose = (one // 2, 0, one // 3, 0)
        for rq in [(Cq, 0, 0, Cq), (0, Cq, 0, Cq)]:
            g, _ = golden(w, n, rq, pose)
            src = (f"(({term} {BL.enc_pose(rq, w)}) {BL.enc_pose(pose, w)})")
            nat = tuple(sgn(x & ((1 << w) - 1), w)
                        for x in BL.dec_pose(native(src), w))
            okE &= (nat == g)
        if not okE:
            native_status = "FAIL_NATIVE"
            allok = False
        print(f"  [{'PASS' if okE else 'FAIL'}] E) NATIVE GATE (hard): "
              f"dynamic forge step @Q4.4+Q8.8 + runtime rotor change through "
              f"ic32 == golden")

    dt = time.time() - t0
    headline = ("PASS_REF_AND_NATIVE" if allok
                and native_status == "PASS_REF_AND_NATIVE"
                else "PASS_REF_ONLY" if allok else "FAIL")
    print(f"\n  SLICE 3b.5d-1: {headline} ({dt:.0f}s)  [native: "
          f"{native_status}]")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
