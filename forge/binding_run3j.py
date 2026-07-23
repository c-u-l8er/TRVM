"""binding_run3j.py -- fault-reset op (GPT-5.6 ruling, pre-ADMIT slice).

Fault reset is a SEPARATE per-orb control input, NOT part of RotorConfigInput:
rotor config targets a Spinner, numeric fault belongs to the controlled Orb.
The v0.6 EpochControl is now TUP(rotor_bundle, fault_bundle); fault_bundle is
one KeepFault(F) | ResetFault(T) flag per orb. A global reset is user syntax
that expands to per-orb ResetFault flags -- not a canonical primitive.

Ordering (the safety property): COMMIT clears the historical fault first
(fault_base = 0 if ResetFault else old_fault); REACT then ORs in THIS epoch's
arithmetic overflow (new_fault = fault_base OR current_overflow). So a reset can
never conceal a fault generated in the same epoch.

Battery:
  1 reset clears an old fault during an idle epoch
  2 reset + clean rotation clears
  3 reset + overflow relatches immediately
  4 reset affects only its target Orb
  5 repeated reset is idempotent
  6 global UI reset expands to independent per-orb controls
  7 persistent fold equals harness
  8 NATIVE hard gate (ic_ref == ic32)
"""
import os, sys, time, subprocess, copy
sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import binlib as BL
import compiler as C
from fixture import (Fixture, init_state_v6, state_to_film_args_v6)
from film import film_bytes_v6
from binding_run3i import drive_k
from lower_e2a import _spine
from ic_ref import parse, normal, reset_runtime

IC32 = os.path.join(HERE, "..", "runtime", "c", "ic32")
SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"
POLICY_FORGE = BL.POLICY_FORGE


def norm(src, budget=2_000_000_000):
    reset_runtime()
    return normal(parse(src), budget=budget)


def native(src, timeout=600):
    r = subprocess.run([IC32], input=src.encode(), capture_output=True,
                       timeout=timeout)
    out = r.stdout.decode().strip().splitlines()
    if r.returncode != 0 or not out:
        raise RuntimeError(f"ic32 rc={r.returncode}")
    reset_runtime()
    return parse(out[0])


def mkfx(w, n, rotor0=None):
    one = 1 << n
    rq = rotor0 if rotor0 is not None else (one, 0, 0, 0)
    return Fixture({"p0": ("periodic", 2, 0)}, [], ["d0"], [("p0", "sp")],
                   spinners={"sp": (w, n, rq)}, orbs=["ob"],
                   sockets=[("sp", "ob")])


def mkfx2(w, n):
    one = 1 << n
    return Fixture({"p0": ("periodic", 2, 0), "p1": ("periodic", 2, 0)},
                   [], ["d0"], [("p0", "sp0"), ("p1", "sp1")],
                   spinners={"sp0": (w, n, (one, 0, 0, 0)),
                             "sp1": (w, n, (one, 0, 0, 0))},
                   orbs=["ob0", "ob1"], sockets=[("sp0", "ob0"),
                                                 ("sp1", "ob1")])


def step_once(fx, step, st, cfg_map, resets, fire_wire, runner=norm):
    """Force a hot signal on the given in-wire (fire_wire: role->bool), commit
    the EpochControl (rotor + fault resets), step once."""
    st = copy.deepcopy(st)
    for role, fire in fire_wire.items():
        wr = fx.in_wires(role)[0]
        st[wr] = (st[wr][0], fire)
    ec = C.enc_config_bundle(fx, cfg_map, resets)
    enc = C.enc_state_v6(fx, st)
    return C.dec_state_v6(fx, runner(f"(({step} {ec}) {enc})"))


def global_reset(fx):
    """User-facing global reset -> the set of per-orb ResetFault flags."""
    return {o: True for o in fx.orbs}


def main():
    print(f"[BINDING fault-reset] per-orb fault control ({POLICY_FORGE})")
    allok = True
    native_status = "PASS_REF_AND_NATIVE"
    t0 = time.time()
    w, n = 8, 4
    one = 1 << n
    big = (1 << (w - 1)) - 1
    fx = mkfx(w, n)
    step, _ = C.compile_step_v6(fx)
    st0 = init_state_v6(fx)

    # ---- 1) reset clears an old fault during an idle epoch
    st_f = copy.deepcopy(st0); st_f["fault_ob"] = 1
    s1r = step_once(fx, step, st_f, {"sp": None}, {"ob": True}, {"sp": False})
    s1k = step_once(fx, step, st_f, {"sp": None}, {"ob": False}, {"sp": False})
    ok1 = (s1r["fault_ob"] == 0 and s1k["fault_ob"] == 1)
    allok &= ok1
    print(f"  [{'PASS' if ok1 else 'FAIL'}] 1) idle reset clears an old fault "
          f"(reset->{s1r['fault_ob']}, keep->{s1k['fault_ob']})")

    # ---- 2) reset + clean rotation clears (identity rotor, no overflow)
    s2 = step_once(fx, step, st_f, {"sp": (one, 0, 0, 0)}, {"ob": True},
                   {"sp": True})
    ok2 = (s2["fault_ob"] == 0)
    allok &= ok2
    print(f"  [{'PASS' if ok2 else 'FAIL'}] 2) reset + clean rotation clears "
          f"(fault->{s2['fault_ob']})")

    # ---- 3) reset + overflowing rotation relatches immediately
    st_big = copy.deepcopy(st0); st_big["pose_ob"] = (big, big, 0, 0)
    s3 = step_once(fx, step, st_big, {"sp": (big, big, 0, 0)}, {"ob": True},
                   {"sp": True})
    _, gflt = BL.golden_rot_forge(w, n, (big, big, 0, 0), (big, big, 0, 0))
    ok3 = (s3["fault_ob"] == 1 == gflt)
    allok &= ok3
    print(f"  [{'PASS' if ok3 else 'FAIL'}] 3) reset + overflow relatches "
          f"(a reset cannot hide a same-epoch fault -> {s3['fault_ob']})")

    # ---- 4) reset affects only its target Orb
    fx2 = mkfx2(w, n)
    step2, _ = C.compile_step_v6(fx2)
    st2 = init_state_v6(fx2); st2["fault_ob0"] = 1; st2["fault_ob1"] = 1
    s4 = step_once(fx2, step2, st2, {"sp0": None, "sp1": None},
                   {"ob0": True}, {"sp0": False, "sp1": False})
    ok4 = (s4["fault_ob0"] == 0 and s4["fault_ob1"] == 1)
    allok &= ok4
    print(f"  [{'PASS' if ok4 else 'FAIL'}] 4) reset is per-orb: ob0->"
          f"{s4['fault_ob0']} (reset), ob1->{s4['fault_ob1']} (untouched)")

    # ---- 5) reset is idempotent: resetting an already-clean fault is a no-op
    # (identical to KeepFault under the same clock step), so a second reset --
    # or a reset on a fault-free orb -- changes nothing.
    s5r = step_once(fx, step, st0, {"sp": None}, {"ob": True}, {"sp": False})
    s5k = step_once(fx, step, st0, {"sp": None}, {"ob": False}, {"sp": False})
    ok5 = (s5r == s5k and s5r["fault_ob"] == 0)
    allok &= ok5
    print(f"  [{'PASS' if ok5 else 'FAIL'}] 5) reset idempotent: resetting a "
          f"clean fault is a no-op (identical to KeepFault, fault stays 0)")

    # ---- 6) global UI reset expands to independent per-orb controls
    st2b = init_state_v6(fx2); st2b["fault_ob0"] = 1; st2b["fault_ob1"] = 1
    s6g = step_once(fx2, step2, st2b, {"sp0": None, "sp1": None},
                    global_reset(fx2), {"sp0": False, "sp1": False})
    s6m = step_once(fx2, step2, st2b, {"sp0": None, "sp1": None},
                    {"ob0": True, "ob1": True}, {"sp0": False, "sp1": False})
    ok6 = (s6g["fault_ob0"] == 0 and s6g["fault_ob1"] == 0 and s6g == s6m)
    allok &= ok6
    print(f"  [{'PASS' if ok6 else 'FAIL'}] 6) global reset == the set of "
          f"per-orb resets (both faults cleared, identical state)")

    # ---- 7) persistent fold equals harness (a reset lands mid-stream, at a
    # firing epoch, on top of a fault set earlier in the same in-calculus run)
    K = 6
    # streams: (cfg_map, resets). fault is set at firing epoch 1 by a saturating
    # rotor, then reset at firing epoch 3; must clear and stay clear after.
    streams = [({"sp": None}, {}),
               ({"sp": (big, big, 0, 0)}, {}),
               ({"sp": None}, {}),
               ({"sp": (one, 0, 0, 0)}, {"ob": True}),
               ({"sp": None}, {}),
               ({"sp": None}, {})]
    st_p = copy.deepcopy(st0); st_p["pose_ob"] = (big, big, 0, 0)

    def harness(runner=norm):
        st = copy.deepcopy(st_p)
        out = []
        for cfgm, rst in streams:
            ec = C.enc_config_bundle(fx, cfgm, rst)
            enc = C.enc_state_v6(fx, st)
            st = C.dec_state_v6(fx, runner(f"(({step} {ec}) {enc})"))
            out.append(copy.deepcopy(st))
        return out

    def internal(runner=norm):
        st0_src = C.enc_state_v6(fx, st_p)
        cfg_srcs = [C.enc_config_bundle(fx, m, r) for m, r in streams]
        nf = runner(drive_k(step, st0_src, cfg_srcs))
        return [C.dec_state_v6(fx, x) for x in _spine(nf, len(streams))]

    hh = harness(); ii = internal()
    faults = [s["fault_ob"] for s in ii]
    films_h = [film_bytes_v6(*state_to_film_args_v6(fx, s, 3 + k))
               for k, s in enumerate(hh)]
    films_i = [film_bytes_v6(*state_to_film_args_v6(fx, s, 3 + k))
               for k, s in enumerate(ii)]
    # fault set at epoch 1, cleared at the epoch-3 reset, stays 0 after
    ok7 = (hh == ii and films_h == films_i
           and faults[1] == 1 and faults[3] == 0 and faults[4] == 0
           and faults[5] == 0)
    allok &= ok7
    print(f"  [{'PASS' if ok7 else 'FAIL'}] 7) persistent fold == harness "
          f"(state + film); fault trajectory {faults} (set@1, reset@3, stays 0)")

    # ---- 8) NATIVE hard gate
    if SKIP_NATIVE:
        native_status = "PASS_REF_ONLY (native skipped)"
        print("  [SKIP] 8) native gate skipped (TRVM_SKIP_NATIVE=1)")
    else:
        ok8 = (internal(runner=norm) == internal(runner=native) == harness())
        allok &= ok8
        st_ok = "PASS" if ok8 else "FAIL"
        if not ok8:
            native_status = "REF_ONLY (native MISMATCH)"
        print(f"  [{st_ok}] 8) native gate: reset trajectory ic_ref == ic32 "
              f"== harness (state-for-state)")

    dt = time.time() - t0
    verdict = native_status if allok else "FAIL"
    print(f"\n[fault-reset] {'ALL PASS' if allok else 'FAILURES'} -- "
          f"{verdict} ({dt:.0f}s)")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
