"""binding_run3e.py -- Slice 3b.5a: pose + Spinner integration (round 12).

The Spinner is now a first-class fixture citizen: film v0.5 carries
authoritative pose state (policy id, lane geometry, big-endian
two's-complement lanes, controller relationship, fault latch); the
compiled epoch term applies the rotor by Scott FUNCTION-selection on
the spinner's in-wire, so the pose is consumed exactly once and
non-firing epochs erase the dead rotation branch before it reduces
(~39 interactions vs ~77k on firing epochs -- measured, not assumed).

Width scoping (stated for ratification): the binding spinner is a
Forge-layer object at fixture-declared proxy width whose pose semantics
are the PARAMETRIC ORACLE POLICY (proven == e2_model.qmul, slice 3b.4
section A); the real Q32.32 World runs in lockstep as the timing and
structure anchor, its rotor the exact <<(32-n) rescale of the filmed
proxy lanes (asserted every projection). Q32.32 value parity closes at
the 3b.5c typed bridge per the round-12 ruling.
"""
import os, sys, time, random, subprocess
sys.setrecursionlimit(700000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import binlib as BL
import fixture as FX
import compiler as C
import film
from ic_ref import parse, normal, reset_runtime, ctr
from e2_model import ZeroChooser
from e2_run import E, CFG, SIG

IC32 = os.path.join(HERE, "..", "runtime", "c", "ic32")
SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

def norm(src, budget=500_000_000):
    reset_runtime()
    return normal(parse(src), budget=budget)

def rotq(w):
    return int(0.7071067811865476 * (1 << (w // 2)))

def run_pair(fx, T, poses0, tag, native_epochs=0):
    """Step model+tracker vs compiled circuit T epochs; return
    (all_films_equal, film_seq, costs, rotation_epochs, final_state)."""
    w, oid, wid_role = FX.build_model(fx)
    poses = dict(poses0)
    st = FX.init_state(fx)
    step_src, _ = C.compile_step(fx)
    m0 = film.film_hash(*FX.model_projection(fx, w, oid, wid_role, 1,
                                             poses))
    i0 = film.film_hash(*FX.state_to_film_args(fx, st, 1))
    ok = m0 == i0
    seq, costs, rots = [m0], [], []
    prev = {o: tuple(w.objs[oid[o]]["pose"][0:4]) for o in fx.orbs}
    for e in range(T):
        w.step([], ZeroChooser())
        for o in fx.orbs:
            cur = tuple(w.objs[oid[o]]["pose"][0:4])
            if cur != prev[o]:
                s = fx.controller_of(o)
                w_, n_, rq = fx.spinners[s]
                poses[o] = BL.oracle_qmul_py(w_, n_, rq, poses[o])
                rots.append(w.t - 1)
            prev[o] = cur
        mh = film.film_hash(*FX.model_projection(fx, w, oid, wid_role,
                                                 w.t - 1, poses))
        src = f"({step_src} {C.enc_state(fx, st)})"
        if native_epochs and e < native_epochs:
            r = subprocess.run([IC32], input=src.encode(),
                               capture_output=True, timeout=180)
            out = r.stdout.decode().strip().splitlines()
            if r.returncode != 0 or not out:
                return False, seq, costs, rots, st
            reset_runtime()
            t = parse(out[0])
        else:
            t = norm(src)
        costs.append(sum(ctr.values()))
        st = C.dec_state(fx, t)
        chh = film.film_hash(*FX.state_to_film_args(fx, st, w.t - 1))
        ok &= mh == chh
        seq.append(chh)
    return ok, seq, costs, rots, st

def main():
    print("[BINDING slice 3b.5a] pose + Spinner integration, film v0.5")
    allok = True
    t_start = time.time()
    native_status = "PASS_REF_AND_NATIVE"

    # --- A) latency + parity, Q4.4
    Cq = rotq(8)
    fx = FX.Fixture({"p": ("periodic", 3, 0)}, [], ["d"],
                    [("p", "d"), ("p", "s")],
                    spinners={"s": (8, 4, (Cq, 0, 0, Cq))},
                    orbs=["o"], sockets=[("s", "o")])
    ok, seq, costs, rots, _ = run_pair(fx, 45, {"o": (16, 0, 0, 0)}, "A")
    exp_rots = [t for t in range(2, 47) if t >= 4 and (t - 4) % 3 == 0]
    okA = ok and rots == exp_rots
    allok &= okA
    fire = [c for c in costs if c > 1000]
    idle = [c for c in costs if c <= 1000]
    print(f"  [{'PASS' if okA else 'FAIL'}] pulser->wire->spinner "
          f"latency+parity Q4.4, T=45: films exact; rotations at "
          f"{{4,7,...}} as the closed form requires; firing epochs "
          f"{min(fire)}-{max(fire)} ints, idle {min(idle)}-{max(idle)} "
          f"(dead branch erased)")

    # --- B) independent init + teeth
    st0 = FX.init_state(fx)
    w, oid, wid_role = FX.build_model(fx)
    m0 = film.film_hash(*FX.model_projection(fx, w, oid, wid_role, 1,
                                             {"o": (16, 0, 0, 0)}))
    good = film.film_hash(*FX.state_to_film_args(fx, st0, 1)) == m0
    bad = dict(st0)
    bad["pose_o"] = (17, 0, 0, 0)
    teeth = film.film_hash(*FX.state_to_film_args(fx, bad, 1)) != m0
    allok &= good and teeth
    print(f"  [{'PASS' if good and teeth else 'FAIL'}] independent init: "
          f"boundary parity holds; corrupted pose lane FAILS it (teeth)")

    # --- C) Q8.8 parity
    C16 = rotq(16)
    fx8 = FX.Fixture({"p": ("periodic", 4, 1)}, [], [],
                     [("p", "s")],
                     spinners={"s": (16, 8, (C16, 0, 0, C16))},
                     orbs=["o"], sockets=[("s", "o")])
    ok8, _, costs8, rots8, _ = run_pair(fx8, 16, {"o": (256, 0, 0, 0)},
                                        "C")
    allok &= ok8 and len(rots8) >= 3
    f8 = [c for c in costs8 if c > 1000]
    print(f"  [{'PASS' if ok8 else 'FAIL'}] Q8.8 parity T=16: films "
          f"exact; {len(rots8)} rotations; firing {min(f8)}-{max(f8)} "
          f"ints")

    # --- D) dynamic multi-rotation
    fx2 = FX.Fixture({"p": ("periodic", 2, 0)}, [], [],
                     [("p", "s")],
                     spinners={"s": (8, 4, (Cq, 0, 0, Cq))},
                     orbs=["o"], sockets=[("s", "o")])
    okD, _, _, rotsD, _ = run_pair(fx2, 30, {"o": (16, 0, 0, 0)}, "D")
    allok &= okD and len(rotsD) >= 13
    print(f"  [{'PASS' if okD else 'FAIL'}] multi-rotation (period 2) "
          f"T=30: {len(rotsD)} rotations, films exact every epoch")

    # --- E) controller exclusivity + release
    try:
        FX.Fixture({"p": ("periodic", 3, 0)}, [], [],
                   [("p", "s1"), ("p", "s2")],
                   spinners={"s1": (8, 4, (Cq, 0, 0, Cq)),
                             "s2": (8, 4, (0, 16, 0, 0))},
                   orbs=["o"], sockets=[("s1", "o"), ("s2", "o")])
        stat = False
    except ValueError:
        stat = True
    # dynamic: second LINK rejected on the live model; DELETE releases
    w, oid, wid_role = FX.build_model(fx)
    w.step([E(500, "STAMP", kind="spinner")], ZeroChooser())
    from e2_run import placed_id
    s2 = placed_id(w, 500)
    r = w.step([E(501, "LINK", target=s2, dst=oid["o"],
                  src_port="socket", dst_port="pose")], ZeroChooser())
    rej = w.objs[oid["o"]]["controller"] == oid["s"]
    w.step([E(502, "DELETE", target=oid["s"])], ZeroChooser())
    freed = w.objs[oid["o"]].get("controller", "") == ""
    w.step([E(503, "LINK", target=s2, dst=oid["o"],
              src_port="socket", dst_port="pose")], ZeroChooser())
    relinked = w.objs[oid["o"]]["controller"] == s2
    okE = stat and rej and freed and relinked
    allok &= okE
    print(f"  [{'PASS' if okE else 'FAIL'}] exclusivity+release: static "
          f"double-socket rejected (typed); live second LINK rejected "
          f"as controlled; DELETE frees; relink succeeds")

    # --- F) EV_CONFIG rotor change (recompile-on-config, cache noted)
    fxA = fx
    rq2 = (0, Cq, 0, Cq)   # a different unit-ish rotor (X*Z blend)
    fxB = FX.Fixture({"p": ("periodic", 3, 0)}, [], ["d"],
                     [("p", "d"), ("p", "s")],
                     spinners={"s": (8, 4, rq2)},
                     orbs=["o"], sockets=[("s", "o")])
    w, oid, wid_role = FX.build_model(fxA)
    poses = {"o": (16, 0, 0, 0)}
    st = FX.init_state(fxA)
    stepA, _ = C.compile_step(fxA)
    stepB, _ = C.compile_step(fxB)     # the "kernel cache" holds both,
                                       # keyed by (policy, rotor bytes)
    okF = True
    cur_fx, cur_step = fxA, stepA
    prev = tuple(w.objs[oid["o"]]["pose"][0:4])
    for e in range(20):
        evs = []
        if e == 10:
            def s_of(v):
                return v - 256 if v >= 128 else v
            r32 = tuple(s_of(v) << 28 for v in rq2)
            evs = [CFG(900, oid["s"], "rotor", r32)]
            cur_fx, cur_step = fxB, stepB
        w.step(evs, ZeroChooser())
        curp = tuple(w.objs[oid["o"]]["pose"][0:4])
        if curp != prev:
            w_, n_, rq = cur_fx.spinners["s"]
            poses["o"] = BL.oracle_qmul_py(w_, n_, rq, poses["o"])
        prev = curp
        mh = film.film_hash(*FX.model_projection(cur_fx, w, oid,
                                                 wid_role, w.t - 1,
                                                 poses))
        t = norm(f"({cur_step} {C.enc_state(cur_fx, st)})")
        st = C.dec_state(cur_fx, t)
        chh = film.film_hash(*FX.state_to_film_args(cur_fx, st,
                                                    w.t - 1))
        okF &= mh == chh
    allok &= okF
    print(f"  [{'PASS' if okF else 'FAIL'}] EV_CONFIG rotor at epoch 10: "
          f"model CFG (anchor rescale) + kernel swap keyed by rotor "
          f"bytes; films exact across the change (T=20)")

    # --- G) determinism
    ok1, seq1, *_ = run_pair(fx, 18, {"o": (16, 0, 0, 0)}, "G1")
    ok2, seq2, *_ = run_pair(fx, 18, {"o": (16, 0, 0, 0)}, "G2")
    okG = ok1 and ok2 and seq1 == seq2
    allok &= okG
    print(f"  [{'PASS' if okG else 'FAIL'}] determinism: same artifact + "
          f"inputs twice -> identical film sequences ({len(seq1)} "
          f"hashes)")

    # --- H) native gate
    if SKIP_NATIVE:
        native_status = "SKIP_NATIVE_EXPLICITLY"
        print("  [SKIP] native gate skipped by TRVM_SKIP_NATIVE=1")
    else:
        okH, *_ = run_pair(fx, 8, {"o": (16, 0, 0, 0)}, "H",
                           native_epochs=8)
        if not okH:
            native_status = "FAIL_NATIVE"
            allok = False
        print(f"  [{'PASS' if okH else 'FAIL'}] NATIVE GATE (hard): 8 "
              f"epochs of the spinner fixture through ic32, films exact")

    dt = time.time() - t_start
    headline = ("PASS_REF_AND_NATIVE" if allok and
                native_status == "PASS_REF_AND_NATIVE"
                else "PASS_REF_ONLY" if allok else "FAIL")
    print(f"\n  SLICE 3b.5a: {headline} ({dt:.0f}s)  [native: "
          f"{native_status}]")
    return 0 if allok else 1

if __name__ == "__main__":
    raise SystemExit(main())
