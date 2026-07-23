"""binding_run3h.py -- Slice 3b.5d-2: Film v0.6, rotor-as-state.

GPT-5.6 ruling 1A: every v0.6 Spinner carries its CURRENT rotor as
canonical runtime STATE; the fixture rotor is initialization data only.
"fixed" vs "configurable" is a PERMISSION distinction (enforced at the
config-acceptance gate), NOT two state layouts or two film paths. The
anchor invariant is redefined and preserved: model_rotor == exact lift of
the circuit rotor STATE (rotor is ASSIGNED not composed -> the rescale is
exact, no separator opens on it). The dynamic fault-returning operator
(dyn_rot_step_forge_dyn_f: λR.λP -> TUP(pose4, overflow)) is the default;
the world transition commits an already-accepted RotorConfigInput to the
rotor state BEFORE reacting, and latches numeric_fault = old OR overflow
(sticky). Film v0.6 reads the rotor and the fault from state.

Battery (all 15 required cases + a direct Law-6 witness):
  1 initial-construction     2 film sensitivity      3 future sensitivity
  4 runtime rotor change     5 no-recompilation      6 model anchor
  7 corrupt state            8 no-signal config      9 config+signal epoch
 10 fixed rejected (typed)  11 configurable accepted 12 fault (sat) latches
 13 type mismatch rejected  14 determinism           15 NATIVE hard gate
  + Law 6 witness (same pose/clock/wire/controller, R1 != R2 -> film differs)
"""
import os, sys, time, subprocess, copy
sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import binlib as BL
import compiler as C
from fixture import (Fixture, build_model, init_state_v6,
                     state_to_film_args_v6, model_projection_v6,
                     lift_rotor)
from film import film_bytes_v6, film_hash_v6
from e2_run import CFG, ZeroChooser
from ic_ref import parse, normal, reset_runtime

IC32 = os.path.join(HERE, "..", "runtime", "c", "ic32")
SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"
POLICY_FORGE = BL.POLICY_FORGE


def norm(src, budget=800_000_000):
    reset_runtime()
    return normal(parse(src), budget=budget)


def native(src, timeout=300):
    r = subprocess.run([IC32], input=src.encode(), capture_output=True,
                       timeout=timeout)
    out = r.stdout.decode().strip().splitlines()
    if r.returncode != 0 or not out:
        raise RuntimeError(f"ic32 rc={r.returncode}")
    reset_runtime()
    return parse(out[0])


def mkfx(w, n, rotor0=None, configurable=None):
    one = 1 << n
    rq = rotor0 if rotor0 is not None else (one, 0, 0, 0)
    return Fixture({"p0": ("periodic", 2, 0)}, [], ["d0"], [("p0", "sp")],
                   spinners={"sp": (w, n, rq)}, orbs=["ob"],
                   sockets=[("sp", "ob")], configurable=configurable)


def sgn4(t, w):
    return tuple(v - (1 << w) if v >= (1 << (w - 1)) else v for v in t)


def apply_step(fx, step, st, cfg_map, fire, runner=norm):
    """Present a hot signal by setting the spinner's in-wire nxt (the wire
    mechanism itself is certified by prior slices); commit cfg_map and step
    the compiled v0.6 transition once."""
    st = copy.deepcopy(st)
    wr = fx.in_wires("sp")[0]
    st[wr] = (st[wr][0], fire)
    cfg = C.enc_config_bundle(fx, cfg_map)
    enc = C.enc_state_v6(fx, st)
    return C.dec_state_v6(fx, runner(f"(({step} {cfg}) {enc})"))


def golden(w, n, rotor, pose):
    mask = (1 << w) - 1
    g, flt = BL.golden_rot_forge(w, n, tuple(c & mask for c in rotor),
                                 tuple(c & mask for c in pose))
    return sgn4(tuple(x & mask for x in g), w), flt


def film6(fx, st, t):
    return film_bytes_v6(*state_to_film_args_v6(fx, st, t))


def main():
    print(f"[BINDING slice 3b.5d-2] Film v0.6 rotor-as-state ({POLICY_FORGE})")
    allok = True
    native_status = "PASS_REF_AND_NATIVE"
    t0 = time.time()
    w, n = 8, 4
    one = 1 << n
    Cq = int(0.7071067811865476 * one)
    big = (1 << (w - 1)) - 1
    fx = mkfx(w, n)
    step, fields = C.compile_step_v6(fx)
    st0 = init_state_v6(fx)

    # ---- 1) initial construction: rotor state == fixture init; roundtrip
    ok1 = (tuple(st0["rotor_sp"]) == (one, 0, 0, 0)
           and st0["fault_ob"] == 0
           and tuple(st0["pose_ob"]) == (one, 0, 0, 0))
    rt = C.dec_state_v6(fx, parse(C.enc_state_v6(fx, st0)))   # enc->dec id
    ok1 &= (tuple(rt["rotor_sp"]) == (one, 0, 0, 0)
            and "FILM v0.6" in film6(fx, st0, 2).decode())
    allok &= ok1
    print(f"  [{'PASS' if ok1 else 'FAIL'}] 1) initial construction: rotor "
          f"state == fixture init {st0['rotor_sp']}, fault=0, film v0.6")

    # ---- 2) film sensitivity: same pose, different rotor -> different film
    sta = copy.deepcopy(st0); sta["rotor_sp"] = (Cq, 0, 0, Cq)
    stb = copy.deepcopy(st0); stb["rotor_sp"] = (0, Cq, Cq, 0)
    ok2 = (film6(fx, sta, 2) != film6(fx, stb, 2)
           and film6(fx, sta, 2) == film6(fx, sta, 2))
    allok &= ok2
    print(f"  [{'PASS' if ok2 else 'FAIL'}] 2) film sensitivity: identical "
          f"pose, distinct rotor state -> distinct v0.6 film")

    # ---- 3) future sensitivity: same hot signal, distinct rotor diverges
    s_a = apply_step(fx, step, st0, {"sp": (Cq, 0, 0, Cq)}, True)
    s_b = apply_step(fx, step, st0, {"sp": (0, Cq, Cq, 0)}, True)
    ok3 = tuple(s_a["pose_ob"]) != tuple(s_b["pose_ob"])
    allok &= ok3
    print(f"  [{'PASS' if ok3 else 'FAIL'}] 3) future sensitivity: same hot "
          f"signal, distinct rotor -> distinct next pose "
          f"{sgn4(s_a['pose_ob'], w)} != {sgn4(s_b['pose_ob'], w)}")

    # ---- 4) runtime rotor change: ONE term, a sequence of rotors
    rotors = [(Cq, 0, 0, Cq), (0, Cq, 0, Cq), (one, 0, 0, 0),
              (Cq, Cq, 0, 0), (0, 0, Cq, Cq)]
    ok4 = True
    for rq in rotors:
        s = apply_step(fx, step, st0, {"sp": rq}, True)
        g, _ = golden(w, n, rq, st0["pose_ob"])
        ok4 &= (sgn4(s["pose_ob"], w) == g and tuple(s["rotor_sp"]) == rq)
    allok &= ok4
    print(f"  [{'PASS' if ok4 else 'FAIL'}] 4) runtime rotor change: one "
          f"compiled term, {len(rotors)} rotors, each pose == golden, each "
          f"rotor committed to state")

    # ---- 5) no recompilation: ONE `step` term handled every rotor in (4);
    # the compiled term is a function of fx GEOMETRY only -- no rotor value
    # is baked in (contrast dyn_rot_step_forge, which bakes a constant).
    ok5 = ok4 and all(str(rq) not in step for rq in rotors)
    allok &= ok5
    print(f"  [{'PASS' if ok5 else 'FAIL'}] 5) no recompilation: the single "
          f"`step` term applied every rotor in (4); no rotor value baked in")

    # ---- 6) model anchor: model Q32.32 rotor == exact lift of circuit state
    w_m, oid, wid_role = build_model(fx)
    ok6 = True
    try:
        model_projection_v6(fx, w_m, oid, wid_role, 2, st0)  # init holds
    except AssertionError:
        ok6 = False
    # reconfigure BOTH sides to a new rotor, anchor must still hold
    rot_new = (Cq, 0, 0, Cq)
    w_m.step([CFG(9001, oid["sp"], "rotor",
                  lift_rotor(w, n, rot_new))], ZeroChooser())
    st_new = copy.deepcopy(st0); st_new["rotor_sp"] = rot_new
    try:
        model_projection_v6(fx, w_m, oid, wid_role, 2, st_new)
    except AssertionError:
        ok6 = False
    # negative: circuit rotor moves but model does not -> anchor must FAIL
    st_bad = copy.deepcopy(st0); st_bad["rotor_sp"] = (0, Cq, Cq, 0)
    caught = False
    try:
        model_projection_v6(fx, w_m, oid, wid_role, 2, st_bad)
    except AssertionError:
        caught = True
    ok6 &= caught
    allok &= ok6
    print(f"  [{'PASS' if ok6 else 'FAIL'}] 6) model anchor: model Q32.32 "
          f"rotor == exact lift of circuit rotor STATE (holds at init + "
          f"after config; a desynced rotor is rejected)")

    # ---- 7) corrupt state: a tampered rotor field diverges the film
    st_corrupt = copy.deepcopy(st0); st_corrupt["rotor_sp"] = (Cq, 1, 2, 3)
    ok7 = film6(fx, st_corrupt, 2) != film6(fx, st0, 2)
    allok &= ok7
    print(f"  [{'PASS' if ok7 else 'FAIL'}] 7) corrupt state: a tampered "
          f"rotor state field fails boundary-film parity")

    # ---- 8) no-signal config: rotor changes, pose does not
    s8 = apply_step(fx, step, st0, {"sp": (Cq, 0, 0, Cq)}, False)
    ok8 = (tuple(s8["rotor_sp"]) == (Cq, 0, 0, Cq)
           and tuple(s8["pose_ob"]) == tuple(st0["pose_ob"])
           and s8["fault_ob"] == 0)
    allok &= ok8
    print(f"  [{'PASS' if ok8 else 'FAIL'}] 8) no-signal config: SetRotor "
          f"with no hot signal commits the rotor, pose unchanged")

    # ---- 9) config + signal same epoch: the NEW rotor controls the rotation
    s9 = apply_step(fx, step, st0, {"sp": (Cq, 0, 0, Cq)}, True)
    g9, _ = golden(w, n, (Cq, 0, 0, Cq), st0["pose_ob"])
    # contrast: had the OLD (identity) rotor controlled, pose would be st0
    ok9 = (sgn4(s9["pose_ob"], w) == g9
           and sgn4(s9["pose_ob"], w) != sgn4(st0["pose_ob"], w))
    allok &= ok9
    print(f"  [{'PASS' if ok9 else 'FAIL'}] 9) config+signal same epoch: the "
          f"committed rotor (not the prior one) controls the rotation")

    # ---- 10) fixed spinner: rotor write rejected with a typed error
    fx_fixed = mkfx(w, n, configurable=[])          # sp is fixed
    ok10 = False
    try:
        C.accept_rotor_config(fx_fixed, "sp", (Cq, 0, 0, Cq))
    except C.RotorConfigError:
        ok10 = True
    # NoChange is always accepted, even on a fixed spinner
    ok10 &= (C.accept_rotor_config(fx_fixed, "sp", None) is None)
    allok &= ok10
    print(f"  [{'PASS' if ok10 else 'FAIL'}] 10) fixed spinner: SetRotor "
          f"rejected (typed RotorConfigError); NoChange still accepted")

    # ---- 11) configurable spinner: accepted, NO kernel replacement
    fx_cfg = mkfx(w, n, configurable=["sp"])
    accepted = C.accept_rotor_config(fx_cfg, "sp", (Cq, 0, 0, Cq))
    step_cfg, _ = C.compile_step_v6(fx_cfg)
    s11 = apply_step(fx_cfg, step_cfg, init_state_v6(fx_cfg),
                     {"sp": accepted}, True)
    g11, _ = golden(w, n, (Cq, 0, 0, Cq), st0["pose_ob"])
    # a SECOND distinct rotor on the SAME term (no recompile)
    s11b = apply_step(fx_cfg, step_cfg, init_state_v6(fx_cfg),
                      {"sp": (0, Cq, Cq, 0)}, True)
    ok11 = (accepted == (Cq, 0, 0, Cq)
            and sgn4(s11["pose_ob"], w) == g11
            and tuple(s11b["rotor_sp"]) == (0, Cq, Cq, 0))
    allok &= ok11
    print(f"  [{'PASS' if ok11 else 'FAIL'}] 11) configurable spinner: rotor "
          f"write accepted and applied on the SAME compiled term (no swap)")

    # ---- 12) fault case: a saturating rotor latches the authoritative fault
    st_big = copy.deepcopy(st0); st_big["pose_ob"] = (big, big, 0, 0)
    s12 = apply_step(fx, step, st_big, {"sp": (big, big, 0, 0)}, True)
    _, gflt = golden(w, n, (big, big, 0, 0), (big, big, 0, 0))
    latched = (s12["fault_ob"] == 1 == gflt)
    # sticky: a subsequent clean firing epoch does NOT clear it
    s12b = apply_step(fx, step, s12, {"sp": (one, 0, 0, 0)}, True)
    s12c = apply_step(fx, step, s12, {"sp": (one, 0, 0, 0)}, False)
    ok12 = latched and s12b["fault_ob"] == 1 and s12c["fault_ob"] == 1
    allok &= ok12
    print(f"  [{'PASS' if ok12 else 'FAIL'}] 12) fault: saturating rotor "
          f"latches numeric_fault=1; sticky across firing and idle epochs")

    # ---- 13) type mismatch: wrong geometry / range rejected
    ok13 = True
    for bad in [(Cq, 0, 0), (Cq, 0, 0, 0, 0), (1 << w, 0, 0, 0),
                (-1, 0, 0, 0)]:
        try:
            C.accept_rotor_config(fx_cfg, "sp", bad)
            ok13 = False
        except C.RotorConfigError:
            pass
    allok &= ok13
    print(f"  [{'PASS' if ok13 else 'FAIL'}] 13) type mismatch: wrong lane "
          f"count / out-of-range rotor rejected (typed)")

    # ---- 14) determinism: same init + config stream -> same film sequence
    def trajectory():
        st = init_state_v6(fx)
        films = [film_hash_v6(*state_to_film_args_v6(fx, st, 2))]
        stream = [(True, (Cq, 0, 0, Cq)), (False, (0, Cq, Cq, 0)),
                  (True, None), (True, (big, big, 0, 0))]
        stp = copy.deepcopy(st); stp["pose_ob"] = (big, big, 0, 0)
        st = stp
        for k, (fire, rq) in enumerate(stream):
            st = apply_step(fx, step, st, {"sp": rq}, fire)
            films.append(film_hash_v6(*state_to_film_args_v6(fx, st, 3 + k)))
        return films
    ok14 = trajectory() == trajectory()
    allok &= ok14
    print(f"  [{'PASS' if ok14 else 'FAIL'}] 14) determinism: identical "
          f"init+config stream -> identical v0.6 film-hash sequence")

    # ---- LAW 6 witness: same pose/clock/wire/controller, R1 != R2 -> differ
    stA = copy.deepcopy(st0); stA["rotor_sp"] = (Cq, 0, 0, Cq)
    stB = copy.deepcopy(st0); stB["rotor_sp"] = (0, 0, Cq, Cq)
    okL6 = film6(fx, stA, 2) != film6(fx, stB, 2)
    allok &= okL6
    print(f"  [{'PASS' if okL6 else 'FAIL'}] L6) Law-6 witness: worlds "
          f"agreeing on pose/clock/wire/controller but R1!=R2 -> v0.6 films "
          f"MUST differ")

    # ---- 15) NATIVE hard gate: a config trajectory through ic32
    if SKIP_NATIVE:
        native_status = "PASS_REF_ONLY (native skipped)"
        print("  [SKIP] 15) native gate skipped (TRVM_SKIP_NATIVE=1)")
    else:
        ok15 = True
        traj = [(True, (Cq, 0, 0, Cq)), (False, (0, Cq, Cq, 0)),
                (True, None), (True, (Cq, Cq, 0, 0))]
        st_r = init_state_v6(fx)
        st_c = init_state_v6(fx)
        for (fire, rq) in traj:
            st_r = apply_step(fx, step, st_r, {"sp": rq}, fire, runner=norm)
            st_c = apply_step(fx, step, st_c, {"sp": rq}, fire, runner=native)
            ok15 &= (st_r == st_c)
        allok &= ok15
        st_ok = "PASS" if ok15 else "FAIL"
        if not ok15:
            native_status = "REF_ONLY (native MISMATCH)"
        print(f"  [{st_ok}] 15) native gate: {len(traj)}-epoch config "
              f"trajectory ic_ref == ic32 (rotor+pose+fault, epoch for epoch)")

    dt = time.time() - t0
    verdict = native_status if allok else "FAIL"
    print(f"\n[slice 3b.5d-2] {'ALL PASS' if allok else 'FAILURES'} -- "
          f"{verdict} ({dt:.0f}s)")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
