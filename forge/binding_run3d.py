"""binding_run3d.py -- Slice 3b.4: the quaternion proxy (round 11).

THE POLICY FINDING, verified before building: the frozen oracle's
Hamilton product is PER-PRODUCT-ROUNDED (each tmul truncates toward
zero at SHIFT before the +/- accumulation) with NO saturation --
the opposite side of round 10's ULP separator from the wide-MAC.
Drift-as-regression-input decides: the lowering implements the ORACLE's
policy; the wide-MAC remains the tighter numerics Forge could adopt by
an explicit future policy change, with the live separator (section C)
measuring exactly what that change would alter.

Transitivity chain (section G): the lowered rotation step equals the
parametric Python policy per epoch (D, E, value-exact); the parametric
policy equals e2_model.qmul at Q32.32 (A, exact); the parametric policy
reproduces the documented drift over the documented horizon (B).
Therefore the lowered policy's drift IS the oracle's drift -- without
running 100,000 epochs x ~71k interactions on the tree harness.
"""
import os, sys, time, random, statistics, subprocess
sys.setrecursionlimit(700000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import binlib as BL
import e2_model as M
from ic_ref import parse, normal, reset_runtime, ctr

IC32 = os.path.join(HERE, "..", "runtime", "c", "ic32")
SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"
DOCUMENTED_DRIFT = -2.015289e-05          # e2_run's observational line

def norm(src, budget=300_000_000):
    reset_runtime()
    return normal(parse(src), budget=budget)

def native(src, timeout=120):
    r = subprocess.run([IC32], input=src.encode(), capture_output=True,
                       timeout=timeout)
    out = r.stdout.decode().strip().splitlines()
    if r.returncode != 0 or not out:
        raise RuntimeError(f"ic32 rc={r.returncode}")
    reset_runtime()
    return parse(out[0])

def s_of(v, w):
    return v - (1 << w) if v >= (1 << (w - 1)) else v

def wide_mac_qmul_py(w, n, A, B):
    """The OTHER policy: full-precision accumulate, ONE trunc0 shift."""
    def s(v):
        return v - (1 << w) if v >= (1 << (w - 1)) else v
    out = []
    for row in BL.HAMILTON:
        acc = sum(sg * s(A[i]) * s(B[j]) for sg, i, j in row)
        out.append(BL.tz_shift_py(acc, n) & ((1 << w) - 1))
    return tuple(out)

def main():
    print("[BINDING slice 3b.4] quaternion proxy under the ORACLE's "
          "per-product policy")
    allok = True
    native_status = "PASS_REF_AND_NATIVE"
    t_start = time.time()
    rng = random.Random(31)

    # --- A) parametric policy == e2_model.qmul at Q32.32
    W64 = (1 << 64) - 1
    def s64(v):
        return v - (1 << 64) if v >= (1 << 63) else v
    bad = 0
    for _ in range(2000):
        A = tuple(rng.randrange(-M.ONE, M.ONE) & W64 for _ in range(4))
        B = tuple(rng.randrange(-M.ONE, M.ONE) & W64 for _ in range(4))
        got = BL.oracle_qmul_py(64, 32, A, B)
        exp = M.qmul(tuple(s64(a) for a in A), tuple(s64(b) for b in B))
        bad += tuple(s64(g) for g in got) != exp
    allok &= bad == 0
    print(f"  [{'PASS' if not bad else 'FAIL'}] parametric policy == "
          f"e2_model.qmul at Q32.32, 2000 random quats")

    # --- B) drift replication over the documented horizon
    # B1: validate the rotation schedule + function against the ACTUAL
    # model at a reduced horizon, pose-exact every epoch (no guessed
    # formulas: the model itself certifies the schedule)
    from e2_run import build_e2a
    from e2_model import RandomChooser
    wld = build_e2a()
    ch = RandomChooser(random.Random(31337))
    rep = list(M.QID)
    b1_bad = 0
    for _ in range(200):
        wld.step([], ch)
        tc = wld.t - 1
        if tc >= 6 and (tc - 6) % 5 == 0:
            rep = list(M.qmul(M.ROT_Z90, tuple(rep)))
        if tuple(wld.objs[wld._orb]["pose"][0:4]) != tuple(rep):
            b1_bad += 1
    allok &= b1_bad == 0
    print(f"  [{'PASS' if not b1_bad else 'FAIL'}] schedule+function "
          f"validated against the model: 200 epochs, pose exact every "
          f"epoch (rotations at tc>=6, (tc-6)%5==0)")
    # B2: the documented horizon. The long run executes epochs
    # tc = 2 .. 2+long_epochs-1 = 100,001 (the round's off-by-one:
    # extrapolating range(2, long_epochs) undercounts by exactly one
    # rotation and misses the drift in the 5th significant figure).
    long_epochs = 100_000
    t_last = 2 + long_epochs - 1
    K = (t_last - 6) // 5 + 1
    pose = list(M.QID)
    for _ in range(K):
        pose = list(M.qmul(M.ROT_Z90, tuple(pose)))
    q0 = M.qnorm2(M.QID)
    drift = (M.qnorm2(tuple(pose)) - q0) / M.ONE
    okB = abs(drift - DOCUMENTED_DRIFT) < 1e-11
    allok &= okB
    print(f"  [{'PASS' if okB else 'FAIL'}] drift replication: K={K:,} "
          f"rotations (epochs to tc={t_last:,}) -> |q|^2-1 = "
          f"{drift:+.6e} (documented {DOCUMENTED_DRIFT:+.6e})")

    # --- C) the policy separator, LIVE on the real trajectory (Q32.32)
    pp = list(M.QID)
    wm = list(M.QID)
    first_div, ndiv = None, 0
    def u64(t):
        return tuple(c & W64 for c in t)
    for k in range(K):
        pp = list(M.qmul(M.ROT_Z90, tuple(pp)))
        wmn = wide_mac_qmul_py(64, 32, u64(M.ROT_Z90), u64(tuple(wm)))
        wm = [s64(c) for c in wmn]
        if tuple(pp) != tuple(wm):
            ndiv += 1
            if first_div is None:
                first_div = k + 1
    wm_drift = (M.qnorm2(tuple(wm)) - q0) / M.ONE
    print(f"  [INFO] policy separator on the real trajectory: first "
          f"divergence at rotation {first_div}; {ndiv:,}/{K:,} rotations "
          f"diverged; wide-MAC drift would be {wm_drift:+.6e} vs "
          f"oracle {drift:+.6e} -- what a policy change would alter, "
          f"measured")

    # --- D) proxy parity, constant path
    hbad = 0
    for _ in range(400):
        w = 8
        n = 4
        terms = [(rng.choice([1, -1]), rng.randrange(1 << w),
                  rng.randrange(1 << w)) for _ in range(4)]
        try:
            golden = 0
            for sg, a, b in terms:
                golden += sg * BL.tz_shift_py(s_of(a, w) * s_of(b, w), n)
            if not -(1 << (w - 1)) <= golden <= (1 << (w - 1)) - 1:
                continue
            t = norm(BL.hcomp_case(w, n, terms))
            xs = BL._spine(t, 2)
            v = BL.dec_bits_list(BL._spine(xs[0], w))
            fl = int(BL._dec_bool(BL._spine(xs[1], 1)[0])) \
                if False else int(BL._dec_bool(xs[1]))
            if s_of(v, w) != golden or fl != 1:
                hbad += 1
        except Exception:
            hbad += 1
    allok &= hbad == 0
    print(f"  [{'PASS' if not hbad else 'FAIL'}] hcomp (oracle policy, "
          f"per-product shift, in-range flag) random x400 in-range sets")
    for (w, n, T) in [(8, 4, 64), (16, 8, 24)]:
        C = int(0.7071067811865476 * (1 << n))
        rotor = (C, 0, 0, C)
        pose = ((1 << n), 0, 0, 0)
        costs, bad2 = [], 0
        for e in range(T):
            t = norm(BL.rot_step_case(w, n, rotor, pose))
            costs.append(sum(ctr.values()))
            got = BL.dec_pose(t, w)
            exp = BL.oracle_qmul_py(w, n, rotor, pose)
            bad2 += got != exp
            pose = exp
        allok &= bad2 == 0
        print(f"  [{'PASS' if not bad2 else 'FAIL'}] const rotation "
              f"trajectory Q{w-n}.{n}, T={T}: pose value-exact every "
              f"epoch; cost {min(costs)}-{max(costs)}/rotation (mean "
              f"{statistics.mean(costs):.0f})")

    # --- E) dynamic rotation step (dyn pose, constant rotor)
    for (w, n, T) in [(8, 4, 32), (16, 8, 8)]:
        C = int(0.7071067811865476 * (1 << n))
        rotor = (C, 0, 0, C)
        pose = ((1 << n), 0, 0, 0)
        costs, bad3 = [], 0
        for e in range(T):
            t = norm(f"({BL.dyn_rot_step(w, n, rotor)} "
                     f"{BL.enc_pose(pose, w)})")
            costs.append(sum(ctr.values()))
            got = BL.dec_pose(t, w)
            exp = BL.oracle_qmul_py(w, n, rotor, pose)
            bad3 += got != exp
            pose = exp
        allok &= bad3 == 0
        print(f"  [{'PASS' if not bad3 else 'FAIL'}] DYNAMIC rotation "
              f"trajectory Q{w-n}.{n}, T={T}: pose value-exact; cost "
              f"{min(costs)}-{max(costs)}/rotation (mean "
              f"{statistics.mean(costs):.0f})")

    # --- F) native hard gate
    if SKIP_NATIVE:
        native_status = "SKIP_NATIVE_EXPLICITLY"
        print("  [SKIP] native gate skipped by TRVM_SKIP_NATIVE=1")
    else:
        try:
            nb = 0
            w, n = 8, 4
            C = int(0.7071067811865476 * (1 << n))
            rotor = (C, 0, 0, C)
            pose = ((1 << n), 0, 0, 0)
            for _ in range(6):
                got = BL.dec_pose(native(
                    BL.rot_step_case(w, n, rotor, pose)), w)
                exp = BL.oracle_qmul_py(w, n, rotor, pose)
                nb += got != exp
                pose = exp
            pose = ((1 << n), 0, 0, 0)
            for _ in range(3):
                got = BL.dec_pose(native(
                    f"({BL.dyn_rot_step(w, n, rotor)} "
                    f"{BL.enc_pose(pose, w)})"), w)
                exp = BL.oracle_qmul_py(w, n, rotor, pose)
                nb += got != exp
                pose = exp
            if nb:
                native_status = "FAIL_NATIVE"
                allok = False
            print(f"  [{'PASS' if nb == 0 else 'FAIL'}] NATIVE GATE "
                  f"(hard): const rotation x6 + dynamic x3 through ic32 "
                  f"-- {nb} mismatches")
        except Exception as ex:
            native_status = "FAIL_NATIVE"
            allok = False
            print(f"  [FAIL] NATIVE GATE: {type(ex).__name__}: {ex}")

    # --- G) transitivity verdict
    print("  [VERDICT RATIONALE] lowered == parametric policy per epoch "
          "(D,E) ; parametric == oracle qmul at Q32.32 (A) ; parametric "
          "reproduces documented drift over the documented horizon (B). "
          "By transitivity the lowered policy's drift IS the oracle's "
          "drift; the tree harness never needs the 100k-epoch run.")

    dt = time.time() - t_start
    headline = ("PASS_REF_AND_NATIVE" if allok and
                native_status == "PASS_REF_AND_NATIVE"
                else "PASS_REF_ONLY" if allok else "FAIL")
    print(f"\n  SLICE 3b.4: {headline} ({dt:.0f}s)  [native: "
          f"{native_status}]")
    return 0 if allok else 1

if __name__ == "__main__":
    raise SystemExit(main())
