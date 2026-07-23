r"""motor8_renorm_run.py -- Slice 3b.5b-3: the named normalization operator.

3b.5b-2 measured the drift (unnormalized Q4.4 rotor composition collapses
-90% to a sub-unit fixed point under biased toward-zero truncation) and
RESERVED forge_motor_renorm_tz_sat_v1. This slice builds that operator and
gates it golden -> ic_ref -> ic32, and demonstrates it arrests the measured
drift. First-order (Newton) renormalization: no sqrt -- the per-step drift
near unit is small, so a scalar s ~= (3 - norm2/ONE^2)/2 applied under the
shipping wide-MAC policy is the tool the data indicates.

Sections:
  A) golden == ic_ref, lane-exact + fault, over rotors and random motors;
     input-fault propagation.
  B) drift ARREST: renorm-every-step vs uncorrected across Q4.4/Q8.8/Q16.16
     -- the operator strictly reduces worst-case drift (25x/64x at 8.8/16.16).
  C) properties: near-unit renorm is near-identity; a collapsed rotor
     recovers toward unit; a saturating scale latches the fault.
  D) NATIVE hard gate: motor renorms through ic32 == golden_renorm.
"""
import os, sys, time, math, random, subprocess
sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import motor8 as MO
from compiler import TUPN
from binlib import enc_operand
from lower_e2a import T, F
from ic_ref import parse, normal, reset_runtime

IC32 = os.path.join(HERE, "..", "runtime", "c", "ic32")
SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"


def enc9(M, w, fin=0):
    """Encode a 9-tuple motor (8 w-bit lanes + fault bit)."""
    mask = (1 << w) - 1
    return TUPN([enc_operand(c & mask, w) for c in M] + [T if fin else F])


def norm_src(src, budget=300_000_000):
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


def unit_rotor(deg, w, n):
    one = 1 << n
    th = math.radians(deg) / 2.0
    return MO.quat_to_motor((round(math.cos(th) * one), 0, 0,
                             round(math.sin(th) * one)), w)


def worst_drift(w, n, renorm_every, K=128):
    """Worst |real-norm^2 - ONE^2|/ONE^2 (%) over a rotor trajectory, with
    optional first-order renorm every `renorm_every` steps."""
    ONE = 1 << n
    ideal = ONE * ONE
    rotor = unit_rotor(90.0 / 8.0, w, n)
    m = MO.quat_to_motor((ONE, 0, 0, 0), w)
    worst = 0.0
    for step in range(K):
        m, _ = MO.golden_fixed(w, n, rotor, m)
        if renorm_every and (step + 1) % renorm_every == 0:
            m, _ = MO.golden_renorm(w, n, m)
        d = abs(MO.motor_norm2_real([sgn(x, w) for x in m]) - ideal) / ideal
        worst = max(worst, d)
    return worst * 100.0


def main():
    print("[BINDING slice 3b.5b-3] Motor8 normalization "
          "(forge_motor_renorm_tz_sat_v1)")
    ok = True
    native_status = "PASS_REF_AND_NATIVE"
    t0 = time.time()
    w, n = 8, 4
    ONE = 1 << n
    mask = (1 << w) - 1
    rng = random.Random(3053)

    def ref_renorm(M, fin=0):
        t = norm_src(f"({MO.dyn_motor_renorm(w, n)} {enc9(M, w, fin)})")
        return MO.dec_motor(t, w)

    # ---- A) golden == ic_ref --------------------------------------------
    a_bad = 0
    cases = [unit_rotor(d, w, n) for d in (0, 30, 45, 90, 137, 200, 315)]
    cases += [tuple(rng.randint(0, mask) for _ in range(8)) for _ in range(18)]
    for M in cases:
        gl, gf = MO.golden_renorm(w, n, M)
        rl, rf = ref_renorm(M, 0)
        if tuple(rl) != gl or rf != gf:
            a_bad += 1
    # input-fault propagation
    pl, pf = ref_renorm(cases[0], 1)
    prop_ok = (pf == 1 and tuple(pl) == MO.golden_renorm(w, n, cases[0])[0])
    ok &= (a_bad == 0 and prop_ok)
    print(f"  [{'PASS' if a_bad == 0 and prop_ok else 'FAIL'}] golden == ic_ref: "
          f"{len(cases)-a_bad}/{len(cases)} lane-exact + fault; "
          f"input fault propagates {prop_ok}")

    # ---- B) drift ARREST across precisions ------------------------------
    b_ok = True
    rows = []
    for (ww, nn) in ((8, 4), (16, 8), (32, 16)):
        unc = worst_drift(ww, nn, 0)
        ren = worst_drift(ww, nn, 1)
        rows.append((nn, unc, ren, unc / ren if ren else float("inf")))
        if not (ren < unc):
            b_ok = False
    ok &= b_ok
    print(f"  [{'PASS' if b_ok else 'FAIL'}] drift ARREST (renorm/step < "
          f"uncorrected worst, all precisions):")
    for nn, unc, ren, fac in rows:
        print(f"          Q{nn}.{nn}: uncorrected {unc:6.2f}%  ->  "
              f"renorm/step {ren:7.4f}%  ({fac:5.1f}x tighter)")

    # ---- C) properties ---------------------------------------------------
    # near-unit rotor: renorm brings drift toward zero, does not worsen it
    near = unit_rotor(37.0, w, n)
    d_before = abs(MO.motor_norm2_real([sgn(x, w) for x in near]) - ONE * ONE)
    nr, _ = MO.golden_renorm(w, n, near)
    d_after = abs(MO.motor_norm2_real([sgn(x, w) for x in nr]) - ONE * ONE)
    c1 = d_after <= d_before
    # collapsed rotor: real norm strictly increases toward unit
    collapsed = (ONE // 2, 0, 0, 0, 0, 0, 0, 0)     # scalar 0.5, norm^2 = ONE^2/4
    cn2_before = MO.motor_norm2_real([sgn(x, w) for x in collapsed])
    cr, _ = MO.golden_renorm(w, n, collapsed)
    cn2_after = MO.motor_norm2_real([sgn(x, w) for x in cr])
    c2 = cn2_after > cn2_before
    # lane overflow latches fault: tiny rotor lanes (-> large scale s) with a
    # large TRANSLATIONAL lane (does not enter norm^2) forces a lane clamp.
    ovf = (1, 0, 0, 0, (1 << (w - 1)) - 1, 0, 0, 0)   # e01 lane = +max, s>ONE
    ol, of = MO.golden_renorm(w, n, ovf)
    c3 = of == 1
    ok &= (c1 and c2 and c3)
    print(f"  [{'PASS' if c1 and c2 and c3 else 'FAIL'}] properties: "
          f"near-unit renorm non-worsening {c1}; collapsed rotor recovers "
          f"({cn2_before}->{cn2_after}) {c2}; lane overflow faults {c3}")

    # ---- D) native hard gate --------------------------------------------
    if SKIP_NATIVE:
        native_status = "SKIP_NATIVE_EXPLICITLY"
        print("  [SKIP] native gate skipped by TRVM_SKIP_NATIVE=1")
    else:
        try:
            nb = 0
            ncases = [unit_rotor(45, w, n), unit_rotor(90, w, n),
                      collapsed, tuple(rng.randint(0, mask) for _ in range(8)),
                      (ONE, 3, 0, 0, 5, 0, 0, 0)]
            for M in ncases:
                got = MO.dec_motor(native(
                    f"({MO.dyn_motor_renorm(w, n)} {enc9(M, w, 0)})"), w)
                exp = MO.golden_renorm(w, n, M)
                nb += got != exp
            # one fault-propagation case through native
            gotp = MO.dec_motor(native(
                f"({MO.dyn_motor_renorm(w, n)} {enc9(ncases[0], w, 1)})"), w)
            nb += gotp[1] != 1
            if nb:
                native_status = "FAIL_NATIVE"
                ok = False
            print(f"  [{'PASS' if nb == 0 else 'FAIL'}] NATIVE GATE (hard): "
                  f"{len(ncases)} renorms + 1 fault-prop through ic32 -- "
                  f"{nb} mismatches vs golden_renorm")
        except Exception as ex:
            native_status = "FAIL_NATIVE"
            ok = False
            print(f"  [FAIL] NATIVE GATE: {type(ex).__name__}: {ex}")

    dt = time.time() - t0
    headline = ("PASS_REF_AND_NATIVE" if ok and
                native_status == "PASS_REF_AND_NATIVE"
                else "PASS_REF_ONLY" if ok else "FAIL")
    print(f"\n  SLICE 3b.5b-3: {headline} ({dt:.0f}s)  [native: {native_status}]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
