r"""motor8.py -- Slice 3b.5b-1: the eight-lane PGA motor, pure composition.

THE ALGEBRA, frozen (verdict Round 13 "Approved 3b.5b scope"): the even
subalgebra of 3D Projective Geometric Algebra Cl(3,0,1) -- the 8-dim
"motor" algebra. Generators e1,e2,e3 square to +1 (Euclidean); e0 is the
ideal/degenerate generator with e0^2 = 0. The even blades (grades 0,2,4)
are exactly eight:

    [1, e23, e31, e12, e01, e02, e03, e0123]
     ^   \______ ______/  \______ ______/   ^
   scalar    rotational       translational  pseudoscalar
             (Euclidean)      (ideal, e0*)

Sign convention is NOT inferred from lane names: it is DERIVED from a
single canonical multiplication of sorted generator blades under the
metric (e0^2=0, ei^2=+1, all anticommute). GEO_TERMS below is that table,
computed once and frozen into the rulepack hash. e31 = -e13 is the only
lane whose canonical sorted blade carries a sign; every product is then
decomposed back onto the named basis exactly.

NUMERIC POLICY: the shipping Stage-One Spinner policy (verdict) --
forge_motor_widemac_tz_sat_v1: each output lane is a wide-MAC of its
signed blade products (exact w x w products, sign-extend, +/- accumulate
at Wacc = 2w + ceil(log2(#terms)) <= 2w+3, ONE toward-zero shift by n,
ONE symmetric saturation to w). Per-lane overflow bits OR into a single
authoritative numeric_fault bit -- the ninth slot of the motor result.
This is the wide-MAC (round-10 tight) side of the ULP separator, NOT the
legacy per-product policy of proc-e2.3's quaternion Spinner; the two are
versioned separately (POLICY_FORGE vs POLICY_LEGACY in binlib).

NORMALIZATION is deliberately absent here (verdict: "Do not normalize
inside the first composition battery"). 3b.5b-2 measures drift; a named
normalization operation with its own film-visible policy comes after.
"""
import os, sys, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compiler import TUPN, OR
from lower_e2a import T, F, _v, _spine, _dec_bool
from compiler import Alloc as _Alloc
import binlib as BL
from binlib import (enc_operand, dec_bits_list, dyn_mac, _chk_mul)

# --------------------------------------------------------------- algebra
GEN_SQ = {0: 0, 1: 1, 2: 1, 3: 1}      # e0^2 = 0 (ideal); e1,e2,e3 -> +1

def _blade_mul(t1, t2):
    """Geometric product of two sorted generator blades -> (sign, blade)
    or (0, ()) when the degenerate metric annihilates it."""
    arr = list(t1) + list(t2)
    sign = 1
    m = len(arr)
    for i in range(m):                 # bubble sort, counting transpositions
        for j in range(m - 1 - i):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                sign = -sign
    out = []
    i = 0
    while i < len(arr):                 # reduce adjacent equal generators
        if i + 1 < len(arr) and arr[i] == arr[i + 1]:
            if GEN_SQ[arr[i]] == 0:
                return 0, ()
            i += 2                      # ei^2 = +1 (no sign change)
        else:
            out.append(arr[i]); i += 1
    return sign, tuple(out)

BASIS_NAMES = ["1", "e23", "e31", "e12", "e01", "e02", "e03", "e0123"]
# named basis element -> (sign, canonical sorted blade)
BASIS = [
    (1, ()),
    (1, (2, 3)),
    (-1, (1, 3)),          # e31 = -e13
    (1, (1, 2)),
    (1, (0, 1)),
    (1, (0, 2)),
    (1, (0, 3)),
    (1, (0, 1, 2, 3)),
]
CANON2NAMED = {t: (k, s) for k, (s, t) in enumerate(BASIS)}

def _geo_terms():
    """For each output lane k, the list of (combined_sign, i, j) products
    a[i]*b[j] contributing to it (degenerate zero products dropped)."""
    terms = [[] for _ in range(8)]
    for i, (si, ti) in enumerate(BASIS):
        for j, (sj, tj) in enumerate(BASIS):
            bs, tt = _blade_mul(ti, tj)
            if bs == 0:
                continue
            k, sk = CANON2NAMED[tt]
            terms[k].append((si * sj * bs * sk, i, j))
    return terms

GEO_TERMS = _geo_terms()

# quaternion embedding: the rotational bivectors {e23,e31,e12} with the
# scalar form a quaternion subalgebra ISOMORPHIC to Hamilton's, but only
# under the sign map I=-e23, J=-e31, K=-e12 (derived, asserted in the
# battery). So quat (q0,q1,q2,q3) <-> motor lanes (q0,-q1,-q2,-q3).
QUAT_EMB = (1, -1, -1, -1)

def _s(v, w):
    return v - (1 << w) if v >= (1 << (w - 1)) else v

def quat_to_motor(q, w):
    """Signed quaternion -> unsigned w-bit motor lane patterns (rotor)."""
    mask = (1 << w) - 1
    lanes = [0] * 8
    for i in range(4):
        lanes[i] = (QUAT_EMB[i] * _s(q[i] & mask, w)) & mask
    return tuple(lanes)

def motor_to_quat(m, w):
    """Rotor motor lanes -> signed quaternion (inverse of quat_to_motor)."""
    return tuple(_s(m[i], w) * QUAT_EMB[i] for i in range(4))

# ------------------------------------------------------------- goldens
def golden_geo(A, B):
    """Exact integer geometric product (no rounding). A,B: 8 ints."""
    out = [0] * 8
    for k in range(8):
        out[k] = sum(sg * A[i] * B[j] for sg, i, j in GEO_TERMS[k])
    return out

def golden_fixed(w, n, A, B):
    """Fixed-point motor product under forge_motor_widemac_tz_sat_v1.
    A,B: 8 unsigned w-bit lane patterns. Returns (lanes, fault)."""
    mask = (1 << w) - 1
    lanes, fault = [], 0
    for k in range(8):
        terms = [(sg, A[i] & mask, B[j] & mask) for sg, i, j in GEO_TERMS[k]]
        if terms:
            v, ov = BL.golden_mac(w, n, terms)
        else:
            v, ov = 0, 0
        lanes.append(v)
        fault |= ov
    return tuple(lanes), fault

# ------------------------------------------------------------- motor norm
# The reversal ~M flips the sign of every grade-2 blade (indices 1..6),
# leaving grade 0 (scalar) and grade 4 (pseudoscalar) unchanged. The motor
# "norm" is the study number M~M = a + b*e0123: its REAL part (lane 0) is
# the Euclidean rotor norm^2 = s^2 + x^2 + y^2 + z^2 (translational lanes
# annihilate under the degenerate e0 metric), and its IDEAL part (lane 7,
# e0123) is the translation-coupling that a unit motor must hold at zero.
# This is the drift metric for 3b.5b-2 (measurement only; normalization is
# a later slice). On the rotor subalgebra it coincides exactly with the
# quaternion norm^2 that proc-e2.3's drift line uses.
def reverse(M):
    """Clifford reversal of an even-subalgebra motor (grade-2 lanes flip)."""
    return tuple(-M[i] if 1 <= i <= 6 else M[i] for i in range(8))

def motor_norm2(A):
    """Exact study-number norm M~M as (real, ideal) = (lane0, lane7) ints."""
    g = golden_geo(list(A), list(reverse(A)))
    return g[0], g[7]

def motor_norm2_real(A):
    """Euclidean (real) part of the motor norm^2; == qnorm2 on rotors."""
    return motor_norm2(A)[0]

# ------------------------------------------------------- normalization
# Policy forge_motor_renorm_tz_sat_v1 (slice 3b.5b-3), designed against the
# 3b.5b-2 drift datum. FIRST-ORDER renormalization: for a motor near unit
# real-norm^2 == ONE^2, the scale that restores it is s = 1/sqrt(x) with
# x = norm2/ONE^2; the first Newton term about x=1 is s ~= (3 - x)/2, i.e.
# in Q(n) fixed point  s = (3*ONE^2 - norm2) >> (n+1)  (toward zero), then
# saturated to w; every lane is scaled by s under the SAME wide-MAC policy
# (exact product, ONE toward-zero shift, ONE saturation). No sqrt: the
# measured per-step drift near unit is small, so first-order fits (validated
# 25x/64x tighter at Q8.8/Q16.16 in motor8_drift). Overflow of the scale or
# any lane ORs into the ninth-slot numeric_fault.
def golden_renorm(w, n, M):
    """Exact first-order motor renormalization. M: 8 unsigned w-bit lanes.
    Returns (lanes, fault) -- fault excludes any input fault (structural)."""
    ONE = 1 << n
    mask = (1 << w) - 1
    def sgn(v):
        return v - (1 << w) if v >= (1 << (w - 1)) else v
    Ms = [sgn(M[i] & mask) for i in range(8)]
    norm2 = sum(Ms[i] * Ms[i] for i in range(4))       # full precision, >=0
    num = 3 * ONE * ONE - norm2                          # signed
    s_raw = num >> (n + 1) if num >= 0 else -((-num) >> (n + 1))  # toward zero
    lo, hi = -(1 << (w - 1)), (1 << (w - 1)) - 1
    fault = int(not lo <= s_raw <= hi)
    s = max(lo, min(hi, s_raw))
    lanes = []
    for k in range(8):
        v, ov = BL.golden_mac(w, n, [(1, M[k] & mask, s & mask)])
        lanes.append(v)
        fault |= ov
    return tuple(lanes), fault

# ------------------------------------------------------------- rulepack
def _table_repr():
    return {BASIS_NAMES[k]: [[sg, BASIS_NAMES[i], BASIS_NAMES[j]]
                             for sg, i, j in GEO_TERMS[k]] for k in range(8)}

def rulepack(w, n):
    """The Motor8 rulepack IDENTITY (verdict: must cover basis ordering,
    metric/signature, multiplication table, lane width, fraction bits,
    rounding, saturation, normalization policy). SHA-256 over the
    canonical JSON is the content-addressed rulepack id."""
    body = {
        "algebra": "pga3d_even_subalgebra_motor",
        "basis_order": BASIS_NAMES,
        "metric_signature": {"e0": 0, "e1": 1, "e2": 1, "e3": 1},
        "multiplication_table": _table_repr(),
        "lane_width": w,
        "fraction_bits": n,
        "rounding": "toward_zero",
        "saturation": "symmetric_signed_clamp",
        "normalization": "none_in_composition",
        "policy_id": BL.POLICY_FORGE,
    }
    blob = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    body["rulepack_id"] = hashlib.sha256(blob).hexdigest()[:16]
    return body

# --------------------------------------------------------- encode/decode
def enc_motor(m, w):
    mask = (1 << w) - 1
    return TUPN([enc_operand(c & mask, w) for c in m])

def dec_motor(t, w):
    xs = _spine(t, 9)
    lanes = tuple(dec_bits_list(_spine(xs[i], w)) for i in range(8))
    return lanes, int(_dec_bool(xs[8]))

def _app(fn, args):
    s = fn
    for a in args:
        s = f"({s} {a})"
    return s

# --------------------------------------------------------- term compiler
def dyn_motor_mul(w, n, A):
    """Constant motor A composed onto a DYNAMIC motor B:
        λB -> TUP(lane0..lane7, fault)
    Each lane is a wide-MAC over its surviving blade products; terms whose
    constant A-lane is zero fold out at emit time (like dyn_rot_step's
    zero-rotor skip). The eight lane overflow bits OR into the ninth-slot
    numeric_fault. Fresh stage instances throughout (the compose law)."""
    _chk_mul(w, n, 0, 0)
    mask = (1 << w) - 1
    Am = [a & mask for a in A]
    lane_terms = [[(sg, i, j) for sg, i, j in GEO_TERMS[k] if Am[i] != 0]
                  for k in range(8)]
    uses = [0] * 8
    for lt in lane_terms:
        for sg, i, j in lt:
            uses[j] += 1
    Bv = _v("B")
    bvars = [_v("b") for _ in range(8)]
    alloc = _Alloc()
    bcopies = [alloc.copies(bvars[j], uses[j]) for j in range(8)]
    bidx = [0] * 8
    def b_src(j):
        s = bcopies[j][bidx[j]]; bidx[j] += 1; return s
    lane_res = []
    for k in range(8):
        lt = lane_terms[k]
        if not lt:
            lane_res.append(None)
            continue
        signs = [sg for sg, i, j in lt]
        args = []
        for sg, i, j in lt:
            args.append(enc_operand(Am[i], w))   # constant A[i]
            args.append(b_src(j))                # fresh B[j] copy
        lane_res.append(_app(dyn_mac(w, n, signs), args))
    nz = [k for k in range(8) if lane_res[k] is not None]
    vvars = {k: _v("mv") for k in nz}
    fvars = {k: _v("mf") for k in nz}
    zero_val = TUPN([F] * w)
    vals = [vvars[k] if lane_res[k] is not None else zero_val
            for k in range(8)]
    faults = [fvars[k] for k in nz]
    fexpr = faults[0] if faults else F
    for f in faults[1:]:
        fexpr = OR(fexpr, f)
    body = TUPN(vals + [fexpr])
    for k in reversed(nz):
        body = f"({lane_res[k]} λ{vvars[k]}.λ{fvars[k]}.{body})"
    inner = "".join(alloc.prefix) + body
    inner = f"({Bv} λ" + ".λ".join(bvars) + f".{inner})"
    return f"λ{Bv}.{inner}"


def dyn_motor_renorm(w, n):
    """First-order motor renormalization on a DYNAMIC 9-tuple motor:
        λM(lane0..lane7, fault_in) -> TUP(lane0'..lane7', fault_out)
    Policy forge_motor_renorm_tz_sat_v1 (== golden_renorm). The scale
      s = sat_w( (3*ONE^2 - (l0^2+l1^2+l2^2+l3^2)) >> (n+1) )   (toward zero)
    is computed once from the rotor (real-norm) lanes at full precision
    Wn = mac_headroom(w, 4), then every lane is scaled by s under the
    shipping wide-MAC policy (dyn_mac 1-term: exact product, ONE toward-zero
    shift, ONE saturation). Scale overflow, any lane overflow, AND the input
    fault all OR into the ninth-slot fault_out. Fresh instances throughout."""
    _chk_mul(w, n, 0, 0)
    ONE = 1 << n
    Wn = BL.mac_headroom(w, 4)
    assert 3 * ONE * ONE < (1 << (Wn - 1)), "renorm constant overflows Wn"
    Mv = _v("M")
    mvars = [_v("m") for _ in range(8)]
    finv = _v("fin")
    alloc_m = _Alloc()
    # lanes 0..3: squared (2 copies) + scaled (1 copy) = 3; lanes 4..7: 1
    mc = [alloc_m.copies(mvars[k], 3 if k < 4 else 1) for k in range(8)]
    # --- norm^2 = sum of squares of the four real-norm lanes, full width Wn
    sq = [f"({BL.dyn_sext(2 * w, Wn)} (({BL.dyn_mul_wide(w)} {mc[k][0]}) "
          f"{mc[k][1]}))" for k in range(4)]
    acc = sq[0]
    for e in sq[1:]:
        acc = (f"({BL.take_value_of('add', Wn)} "
               f"(({BL.dyn_case('add', Wn)} {acc}) {e}))")
    # --- num = 3*ONE^2 - norm^2  (add the constant to the negated accumulator)
    negn = f"({BL.take_value_of('neg', Wn)} ({BL.dyn_neg(Wn)} {acc}))"
    const = enc_operand(3 * ONE * ONE, Wn)
    num = (f"({BL.take_value_of('add', Wn)} "
           f"(({BL.dyn_case('add', Wn)} {const}) {negn}))")
    # --- s = sat_w( num >> (n+1) toward zero )  -> nested TUP(value, ovf)
    s_full = (f"({BL.dyn_sat(Wn - (n + 1), w)} "
              f"({BL.dyn_shift_tz(Wn, n + 1)} {num}))")
    svv, sfv = _v("sv"), _v("sf")
    alloc_s = _Alloc()
    svc = alloc_s.copies(svv, 8)                 # scale used by all 8 lanes
    scale_src = [mc[k][2] if k < 4 else mc[k][0] for k in range(8)]
    lane_res = [_app(dyn_mac(w, n, [1]), [scale_src[k], svc[k]])
                for k in range(8)]
    lvs = [_v("lv") for _ in range(8)]
    lfs = [_v("lf") for _ in range(8)]
    fexpr = OR(finv, sfv)
    for f in lfs:
        fexpr = OR(fexpr, f)
    body = TUPN(lvs + [fexpr])
    for k in reversed(range(8)):
        body = f"({lane_res[k]} λ{lvs[k]}.λ{lfs[k]}.{body})"
    body = "".join(alloc_s.prefix) + body
    body = f"({s_full} λ{svv}.λ{sfv}.{body})"
    body = "".join(alloc_m.prefix) + body
    inner = f"({Mv} λ" + ".λ".join(mvars + [finv]) + f".{body})"
    return f"λ{Mv}.{inner}"
