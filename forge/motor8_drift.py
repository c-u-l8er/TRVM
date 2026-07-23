r"""motor8_drift.py -- Slice 3b.5b-2: measure the drift, name the target.

The verdict froze 3b.5b-1 with normalization DELIBERATELY ABSENT ("Do not
normalize inside the first composition battery. 3b.5b-2 measures drift; a
named normalization operation with its own film-visible policy comes
after"). This is that measurement -- and only that. It does NOT build a
normalization operator; it quantifies the datum that a later slice must
correct, so the correction is designed against a number, not a guess
(Law: measure before building).

WHAT DRIFTS. A mathematically unit rotor holds real-norm^2 == ONE^2 under
composition (a product of unit rotors is a unit rotor). The shipping
fixed-point policy forge_motor_widemac_tz_sat_v1 rounds ONCE per lane,
toward zero, after a wide accumulation. Toward-zero truncation is a
BIASED rounding: repeated composition bleeds magnitude out of the rotor,
so the real norm wanders below ONE^2 and never self-corrects. This file
measures that wander over a horizon, at two precisions, against the
irreducible single-rotor quantization floor -- and states the target
(named, reserved, film-visible) that 3b.5b-3 normalization must hit.

The drift metric is proc-e2.3's exact convention lifted to the motor:
(motor_norm2_real(pose) - ONE^2) / ONE, in ULP-relative units. On the
rotor subalgebra motor_norm2_real IS the quaternion norm^2 (asserted in
3b.5b-1 and re-asserted in section A), so this number is directly
comparable to the -2.015289e-05 rotor drift already in the ledger.

Measurement only: golden-level (the fixed-point policy is already proven
== IC exhaustively in 3b.5b-1). One IC spot-check keeps the golden==IC
chain unbroken for the specific trajectory measured here.
"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.setrecursionlimit(700000)
import motor8 as MO
import binlib as BL
from ic_ref import parse, normal, reset_runtime

W, N = 8, 4
ONE = 1 << N
IDEAL = ONE * ONE                       # unit rotor real-norm^2 target
RENORM_POLICY = "forge_motor_renorm_tz_sat_v1"   # reserved; built in 3b.5b-3

def _s(v):
    return MO._s(v, W)

def sgn_lanes(m):
    """unsigned w-bit motor -> signed int lanes."""
    return [_s(x) for x in m]

def real_drift(m):
    """(real-norm^2(m) - ONE^2)/ONE in ULP-relative units."""
    return (MO.motor_norm2_real(sgn_lanes(m)) - IDEAL) / ONE

def unit_rotor(deg, w=W, n=N):
    """Nearest fixed-point rotor for a rotation of `deg` about +z."""
    th = math.radians(deg) / 2.0
    one = 1 << n
    q = (round(math.cos(th) * one), 0, 0, round(math.sin(th) * one))
    return MO.quat_to_motor(q, w)

def compose(A, B):
    """One fixed-point motor product under the shipping policy."""
    lanes, fault = MO.golden_fixed(W, N, A, B)
    return tuple(lanes), fault

def ref_motor(A, B):
    """golden_fixed via the IC reference runtime (lanes, fault)."""
    reset_runtime()
    src = f"({MO.dyn_motor_mul(W, N, A)} {MO.enc_motor(B, W)})"
    return MO.dec_motor(normal(parse(src), budget=300_000_000), W)

def trajectory(rotor, K):
    """Compose `rotor` onto itself K times; return the per-step drift list
    and the running OR of the numeric_fault latch."""
    m = MO.quat_to_motor((ONE, 0, 0, 0), W)   # identity rotor
    drifts, fault = [], 0
    for _ in range(K):
        m, ov = compose(rotor, m)
        fault |= ov
        drifts.append(real_drift(m))
    return m, drifts, fault


def main():
    print("[BINDING slice 3b.5b-2] Motor8 drift measurement "
          "(forge_motor_widemac_tz_sat_v1)")
    ok = True

    # --- A) the norm metric IS the quaternion norm on rotors -----------
    a_ok = True
    for deg in range(0, 360, 7):
        m = unit_rotor(deg)
        real, ideal = MO.motor_norm2(sgn_lanes(m))
        q = MO.motor_to_quat(m, W)
        if real != sum(c * c for c in q) or ideal != 0:
            a_ok = False
    ok &= a_ok
    print(f"  [{'PASS' if a_ok else 'FAIL'}] norm metric: motor_norm2_real "
          f"== quaternion norm^2 on rotors; ideal part 0 (x{len(range(0,360,7))})")

    # --- B) irreducible single-rotor quantization floor ----------------
    floors = [abs(real_drift(unit_rotor(deg))) for deg in range(1, 360)]
    fmax, fmean = max(floors), sum(floors) / len(floors)
    print(f"  [DATUM] single-rotor quantization floor: max {fmax:+.6e}, "
          f"mean {fmean:+.6e} ULP-rel (one encode, no composition)")

    # --- C) drift over a composition horizon ---------------------------
    # 11.25-deg rotor (a Z90/8 tooth), composed K times: mathematically
    # this is a pure rotation, so the ideal real norm is constant at ONE^2.
    # Toward-zero truncation is biased, so the rotor bleeds magnitude and
    # -- at low precision -- collapses toward a sub-unit fixed point.
    rotor = unit_rotor(90.0 / 8.0)
    K = 128
    mK, drifts, fault = trajectory(rotor, K)
    dK = drifts[-1]
    relK = dK / ONE                       # fraction of unit norm^2 lost
    decayed = dK < -fmax
    plateaued = drifts[-1] == drifts[-64] # reached a fixed point in the lattice
    print(f"  [DATUM] Q4.4 rotor(11.25 deg) x{K}: drift {dK:+.6e} ULP-rel "
          f"= {relK*100:+.1f}% of unit norm^2; fault {fault}; "
          f"{'biased decay' if decayed else 'within floor'}"
          f"{'; NORM COLLAPSE to sub-unit fixed point' if plateaued else ''}")
    print(f"          trajectory drift @[1,8,32,64,128] = "
          + ", ".join(f"{drifts[i-1]:+.4e}" for i in (1, 8, 32, 64, 128)))

    # C2) same trajectory at Q8.8 -- more precision, tighter RELATIVE drift
    w2, n2 = 16, 8
    one2 = 1 << n2
    ideal2 = one2 * one2
    th = math.radians(90.0 / 8.0) / 2.0
    r2 = MO.quat_to_motor((round(math.cos(th) * one2), 0, 0,
                           round(math.sin(th) * one2)), w2)
    m2 = MO.quat_to_motor((one2, 0, 0, 0), w2)
    f2 = 0
    for _ in range(K):
        lanes, ov = MO.golden_fixed(w2, n2, r2, m2)
        m2 = tuple(lanes); f2 |= ov
    d2 = (MO.motor_norm2_real([MO._s(x, w2) for x in m2]) - ideal2) / one2
    rel2 = d2 / one2
    print(f"  [DATUM] Q8.8 rotor(11.25 deg) x{K}: drift {d2:+.6e} ULP-rel "
          f"= {rel2*100:+.1f}% of unit norm^2; fault {f2}  "
          f"(relative decay {abs(relK/rel2):.1f}x smaller than Q4.4)")

    # --- D) IC == golden spot-check on this trajectory -----------------
    # keep the golden==IC chain unbroken for the exact motors measured.
    d_ok = True
    m = MO.quat_to_motor((ONE, 0, 0, 0), W)
    for step in range(6):
        m_next, ov = compose(rotor, m)
        rl, rf = ref_motor(rotor, m)
        if tuple(rl) != m_next or rf != ov:
            d_ok = False
        m = m_next
    ok &= d_ok
    print(f"  [{'PASS' if d_ok else 'FAIL'}] IC == golden along trajectory "
          f"(6 steps through ic_ref): drift is a property of the proven policy")

    # --- E) ideal-part behaviour for a motor with translation ----------
    # A proper rigid motion has study-number IDEAL part == 0 (the constraint
    # defining the motor group). We compose a screw (rotor * translator) and
    # watch whether fixed-point rounding kicks the ideal part off zero -- a
    # SECOND invariant a normalizer must eventually protect.
    transl = tuple(  # small +x translation motor (rotor scalar + e01)
        (v & ((1 << W) - 1)) for v in (ONE, 0, 0, 0, ONE // 4, 0, 0, 0))
    m = transl
    ideal_track = []
    for _ in range(32):
        m, _ov = compose(rotor, m)
        ideal_track.append(MO.motor_norm2(sgn_lanes(m))[1] / ONE)
    imax = max(abs(v) for v in ideal_track)
    print(f"  [DATUM] screw(rotor*transl) x32: ideal-part |drift| max "
          f"{imax:+.6e} ULP-rel "
          f"({'rigid constraint held at 0 in this lattice' if imax == 0 else 'perturbed off 0 by rounding'})")

    # --- the reserved target ------------------------------------------
    print(f"  [TARGET] a unit motor must hold real-norm^2 == ONE^2 "
          f"(ideal 0); measured deficit to correct at Q4.4/x{K} is "
          f"{dK:+.6e} ULP-rel.")
    print(f"           normalization policy RESERVED (not built here): "
          f"{RENORM_POLICY}  -- slice 3b.5b-3, designed against this datum.")

    verdict = "PASS_MEASUREMENT" if ok else "FAIL"
    print(f"\n  SLICE 3b.5b-2: {verdict} (drift quantified; normalization deferred)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
