"""motor8_run.py -- Slice 3b.5b-1 battery: Motor8 PURE COMPOSITION.

The verdict's required 3b.5b-1 batteries, in order:
  A) all 64 basis-blade multiplication pairs (canonical table closure)
  B) identity motor on both sides
  C) pure rotor composition + rotor-only == quaternion subsystem
  D) pure translator composition (subspace closure)
  E) mixed rotation/translation + noncommutativity witnesses
  F) overflow and saturation edges (authoritative numeric_fault)
  G) per-lane wide accumulator oracle (Wacc = 2w + ceil(log2 k) bound)
  H) reduced-width reference/native parity (ic_ref + ic32 hard gate)

Normalization is NOT exercised here (verdict: measure drift first, in
3b.5b-2). Every arithmetic claim is checked against golden_fixed, the
wide-MAC reference; the rotor subsystem is additionally checked against
an INDEPENDENT Hamilton wide-MAC oracle through the frozen embedding.
"""
import os, sys, time, random, statistics, subprocess
sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import binlib as BL
import motor8 as MO
from ic_ref import parse, normal, reset_runtime, ctr

IC32 = os.path.join(HERE, "..", "runtime", "c", "ic32")
SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

def norm(src, budget=400_000_000):
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

def s_of(v, w):
    return v - (1 << w) if v >= (1 << (w - 1)) else v

def qwide(w, n, qa, qb):
    """INDEPENDENT wide-MAC Hamilton oracle on signed quaternions ->
    (signed lanes, fault). Same policy as Motor8, computed from
    binlib.HAMILTON with no reference to the motor algebra."""
    mask = (1 << w) - 1
    lanes, fault = [], 0
    for row in BL.HAMILTON:
        terms = [(sg, qa[i] & mask, qb[j] & mask) for sg, i, j in row]
        v, ov = BL.golden_mac(w, n, terms)
        lanes.append(s_of(v, w))
        fault |= ov
    return lanes, fault

def ref_product(w, n, A, B):
    """Compile A (constant) o B (dynamic) and reduce through ic_ref."""
    t = norm(f"({MO.dyn_motor_mul(w, n, A)} {MO.enc_motor(B, w)})")
    return MO.dec_motor(t, w)

def main():
    print("[BINDING slice 3b.5b-1] Motor8 PGA even-subalgebra pure "
          "composition, wide-MAC policy")
    allok = True
    native_status = "PASS_REF_AND_NATIVE"
    t_start = time.time()
    rng = random.Random(853)
    w, n = 8, 4
    ONE = 1 << n
    C45 = int(0.7071067811865476 * ONE)
    rp = MO.rulepack(w, n)

    # ---- A) canonical multiplication table: all 64 basis pairs -----------
    # Each basis blade product must decode to exactly one named lane with a
    # definite sign (or annihilate under the degenerate metric). We rebuild
    # the table from unit basis motors and require golden_geo to agree with
    # GEO_TERMS, then require closure (every survivor lands on a named lane).
    a_bad = 0
    survivors = 0
    for i in range(8):
        for j in range(8):
            ei = [1 if x == i else 0 for x in range(8)]
            ej = [1 if x == j else 0 for x in range(8)]
            got = MO.golden_geo(ei, ej)
            # expected from the frozen table: sum over terms with (i,j)
            exp = [0] * 8
            for k in range(8):
                for sg, ti, tj in MO.GEO_TERMS[k]:
                    if ti == i and tj == j:
                        exp[k] += sg
            nz = [x for x in got if x != 0]
            if got != exp or len(nz) > 1:
                a_bad += 1
            survivors += len(nz)
    allok &= a_bad == 0
    print(f"  [{'PASS' if not a_bad else 'FAIL'}] 64 basis-blade pairs: "
          f"table closure exact, each product single-lane (or annihilated); "
          f"{survivors}/64 nonzero; rulepack {rp['rulepack_id']} "
          f"({rp['policy_id']})")

    # ---- B) identity motor on both sides ---------------------------------
    ident = (ONE, 0, 0, 0, 0, 0, 0, 0)
    b_bad = 0
    for _ in range(60):
        # in-range operand: small signed lanes so no lane overflows
        B = tuple(rng.randrange(-ONE, ONE) & ((1 << w) - 1) for _ in range(8))
        gl, gf = MO.golden_fixed(w, n, ident, B)
        rl, rf = ref_product(w, n, ident, B)
        # I o B must equal B lane-for-lane, no fault
        expB = tuple(BL.tz_shift_py(s_of(b, w) * ONE, n) & ((1 << w) - 1)
                     for b in B)
        if not (rl == gl == expB and rf == gf == 0):
            b_bad += 1
        # B o I (B constant, identity dynamic)
        gl2, gf2 = MO.golden_fixed(w, n, B, ident)
        rl2, rf2 = ref_product(w, n, B, ident)
        if not (rl2 == gl2 == expB and rf2 == gf2 == 0):
            b_bad += 1
    allok &= b_bad == 0
    print(f"  [{'PASS' if not b_bad else 'FAIL'}] identity both sides: "
          f"I o B == B o I == B lane-exact, fault 0 (x60x2, ref)")

    # ---- C) pure rotor composition + quaternion-subsystem match ----------
    def rotor(q):
        return MO.quat_to_motor(q, w)
    c_bad = 0
    q_bad = 0
    rots = [(ONE, 0, 0, 0), (C45, 0, 0, C45), (C45, C45, 0, 0),
            (C45, 0, C45, 0), (0, ONE, 0, 0)]
    for qa in rots:
        for qb in rots:
            ma, mb = rotor(qa), rotor(qb)
            gl, gf = MO.golden_fixed(w, n, ma, mb)
            rl, rf = ref_product(w, n, ma, mb)
            # rotor o rotor stays rotational: translational + pseudoscalar 0
            trans_zero = all(rl[k] == 0 for k in (4, 5, 6, 7))
            # independent quaternion oracle through the embedding
            ql, qfl = qwide(w, n, list(qa), list(qb))
            rquat = MO.motor_to_quat(rl, w)
            if not (rl == gl and rf == gf):
                c_bad += 1
            if not (trans_zero and list(rquat) == ql and rf == qfl):
                q_bad += 1
    allok &= (c_bad == 0 and q_bad == 0)
    print(f"  [{'PASS' if not c_bad else 'FAIL'}] pure rotor composition: "
          f"ref == golden across {len(rots)**2} rotor pairs")
    print(f"  [{'PASS' if not q_bad else 'FAIL'}] rotor-only == quaternion "
          f"subsystem: translational lanes 0; motor rotor lanes == "
          f"independent Hamilton wide-MAC (embedded), fault matched")

    # rotor trajectory: repeated Z90 compose, value-exact every step
    traj_bad = 0
    pose = rotor((ONE, 0, 0, 0))
    rz = rotor((C45, 0, 0, C45))
    costs = []
    for _ in range(16):
        rl, rf = ref_product(w, n, rz, pose)
        costs.append(sum(ctr.values()))
        gl, gf = MO.golden_fixed(w, n, rz, pose)
        if (rl, rf) != (gl, gf):
            traj_bad += 1
        pose = rl
    allok &= traj_bad == 0
    print(f"  [{'PASS' if not traj_bad else 'FAIL'}] rotor trajectory "
          f"(Z90 x16): value-exact every compose; cost {min(costs)}-"
          f"{max(costs)}/compose (mean {statistics.mean(costs):.0f})")

    # ---- D) pure translator composition (subspace closure) ---------------
    def translator(tx, ty, tz):
        return (ONE, 0, 0, 0, tx & ((1 << w) - 1), ty & ((1 << w) - 1),
                tz & ((1 << w) - 1), 0)
    d_bad = 0
    for _ in range(40):
        t1 = translator(rng.randrange(-4, 4), rng.randrange(-4, 4),
                        rng.randrange(-4, 4))
        t2 = translator(rng.randrange(-4, 4), rng.randrange(-4, 4),
                        rng.randrange(-4, 4))
        gl, gf = MO.golden_fixed(w, n, t1, t2)
        rl, rf = ref_product(w, n, t1, t2)
        # translator subspace: rotational lanes {1,2,3} and pseudoscalar 0
        closed = all(rl[k] == 0 for k in (1, 2, 3, 7))
        if not (rl == gl and rf == gf and closed):
            d_bad += 1
    allok &= d_bad == 0
    print(f"  [{'PASS' if not d_bad else 'FAIL'}] pure translator "
          f"composition: ref == golden; stays in translator subspace "
          f"(rotational+pseudoscalar lanes 0) (x40)")

    # ---- E) mixed rotation/translation + noncommutativity ----------------
    e_bad = 0
    nc_seen = 0
    for _ in range(40):
        R = rotor(rng.choice(rots[1:]))
        Tt = translator(rng.randrange(-3, 4), rng.randrange(-3, 4),
                        rng.randrange(-3, 4))
        for A, B in ((R, Tt), (Tt, R)):
            gl, gf = MO.golden_fixed(w, n, A, B)
            rl, rf = ref_product(w, n, A, B)
            if (rl, rf) != (gl, gf):
                e_bad += 1
        # noncommutativity witness: R o T vs T o R differ in general
        rt, _ = MO.golden_fixed(w, n, R, Tt)
        tr, _ = MO.golden_fixed(w, n, Tt, R)
        if rt != tr:
            nc_seen += 1
    allok &= e_bad == 0
    ncok = nc_seen > 0
    allok &= ncok
    print(f"  [{'PASS' if not e_bad else 'FAIL'}] mixed rotor/translator: "
          f"ref == golden (x40x2)")
    print(f"  [{'PASS' if ncok else 'FAIL'}] noncommutativity witnessed: "
          f"{nc_seen}/40 mixed pairs have A o B != B o A")

    # ---- F) overflow and saturation edges --------------------------------
    f_bad = 0
    # saturating case: large lanes force per-lane overflow -> fault=1
    big = tuple([(1 << (w - 1)) - 1] * 8)   # all lanes = +MAX pattern
    gl, gf = MO.golden_fixed(w, n, big, big)
    rl, rf = ref_product(w, n, big, big)
    if not (rl == gl and rf == gf == 1):
        f_bad += 1
    # a deliberately clamped single lane: verify clamp value matches golden
    over_ok = 0
    for _ in range(30):
        A = tuple(rng.randrange(1 << w) for _ in range(8))
        B = tuple(rng.randrange(1 << w) for _ in range(8))
        gl, gf = MO.golden_fixed(w, n, A, B)
        rl, rf = ref_product(w, n, A, B)
        if (rl, rf) == (gl, gf):
            over_ok += 1
        else:
            f_bad += 1
    allok &= f_bad == 0
    print(f"  [{'PASS' if not f_bad else 'FAIL'}] overflow/saturation: "
          f"all-MAX product faults (fault=1, clamped == golden); random "
          f"wide products ref == golden incl. saturation ({over_ok}/30)")

    # ---- G) per-lane wide accumulator oracle -----------------------------
    # Wacc bound is impossible-to-wrap by construction for <=8 terms.
    Wacc = BL.mac_headroom(w, 8)
    # executable worst case: 8 max-magnitude products cannot reach 2^(Wacc-1)
    worst = 8 * ((1 << (w - 1)) ** 2)
    g_ok = (Wacc == 2 * w + 3) and (worst < (1 << (Wacc - 1)))
    # and confirm every lane's true accumulator stayed within Wacc on a
    # random adversarial sweep (golden uses full-precision ints)
    for _ in range(200):
        A = [rng.randrange(1 << w) for _ in range(8)]
        B = [rng.randrange(1 << w) for _ in range(8)]
        for k in range(8):
            acc = sum(sg * s_of(A[i], w) * s_of(B[j], w)
                      for sg, i, j in MO.GEO_TERMS[k])
            if not (-(1 << (Wacc - 1)) <= acc < (1 << (Wacc - 1))):
                g_ok = False
    allok &= g_ok
    print(f"  [{'PASS' if g_ok else 'FAIL'}] per-lane wide accumulator: "
          f"Wacc = 2w+3 = {Wacc} bits; worst-case |acc| < 2^(Wacc-1) by "
          f"construction and over 200 adversarial motors")

    # ---- H) native hard gate ---------------------------------------------
    if SKIP_NATIVE:
        native_status = "SKIP_NATIVE_EXPLICITLY"
        print("  [SKIP] native gate skipped by TRVM_SKIP_NATIVE=1")
    else:
        try:
            nb = 0
            cases = [
                (rotor((C45, 0, 0, C45)), rotor((C45, C45, 0, 0))),
                (ident, rotor((C45, 0, C45, 0))),
                (translator(2, -1, 3), translator(-2, 1, 1)),
                (rotor((C45, 0, 0, C45)), translator(1, 2, -3)),
                (big, big),
            ]
            for A, B in cases:
                got = MO.dec_motor(native(
                    f"({MO.dyn_motor_mul(w, n, A)} {MO.enc_motor(B, w)})"), w)
                exp = MO.golden_fixed(w, n, A, B)
                nb += got != exp
            if nb:
                native_status = "FAIL_NATIVE"
                allok = False
            print(f"  [{'PASS' if nb == 0 else 'FAIL'}] NATIVE GATE (hard): "
                  f"{len(cases)} motor products through ic32 -- {nb} "
                  f"mismatches vs golden_fixed")
        except Exception as ex:
            native_status = "FAIL_NATIVE"
            allok = False
            print(f"  [FAIL] NATIVE GATE: {type(ex).__name__}: {ex}")

    dt = time.time() - t_start
    headline = ("PASS_REF_AND_NATIVE" if allok and
                native_status == "PASS_REF_AND_NATIVE"
                else "PASS_REF_ONLY" if allok else "FAIL")
    print(f"\n  SLICE 3b.5b-1: {headline} ({dt:.0f}s)  [native: "
          f"{native_status}]")
    return 0 if allok else 1

if __name__ == "__main__":
    raise SystemExit(main())
