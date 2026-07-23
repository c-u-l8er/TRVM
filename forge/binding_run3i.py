"""binding_run3i.py -- Slice 3b.5e: persistent epochs.

3b.5d-2 proved a single v0.6 transition `λcfg.λst -> st'` (rotor-as-state,
committed config, sticky fault). This slice proves that transition COMPOSES
under the interaction calculus' own reduction: a world runs K epochs from one
initial state entirely INSIDE one normalization -- no Python decode/re-encode
between epochs -- carrying counters + wires + doors + poses + ROTORS + faults
as pure IC data, and emitting the whole film sequence from that one normal
form. Firing is driven by the world's OWN clock (the periodic pulser through
the delayed wire), NOT by manual per-epoch wire injection.

The finding: persistence is INTRINSIC to the compiled term. The internally
persistent K-epoch world is state-for-state and film-for-film identical to the
harness-stepped world (which decodes and re-encodes state every epoch), and
the identity holds on the native runtime too.

NARROW first slice per the roadmap: fixed graph, no ADMIT, no dynamic sockets,
no claim replication. Stateful rotor changes (already proven in 3b.5d-2) flow
through the internal fold as a fixed pre-encoded config stream.

Battery:
  1 persistence identity   (internal == harness, state + film, all epochs)
  2 config-stream persist  (a mid-stream rotor change composes internally)
  3 sticky-fault persist   (a saturating rotor latches; stays latched inside)
  4 determinism            (one driver normalized twice -> identical films)
  5 multi-controller       (two spinners persist independently, no crosstalk)
  6 NATIVE hard gate       (internal driver ic_ref == ic32 == harness)
"""
import os, sys, time, subprocess, copy
sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import binlib as BL
import compiler as C
from compiler import Alloc, TUPN
from lower_e2a import _v, _spine
from fixture import Fixture, init_state_v6, state_to_film_args_v6
from film import film_bytes_v6, film_hash_v6
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


def film6(fx, st, t):
    return film_bytes_v6(*state_to_film_args_v6(fx, st, t))


# ------------------------------------------------------- persistent driver
def drive_k(step, st0_src, cfg_srcs):
    """Fold the v0.6 transition over a fixed config stream, entirely in IC.
    Returns one source term that normalizes to TUPN([s_1, ..., s_K]) -- the
    K post-states in a single normal form. Each intermediate state is affine-
    duplicated: one copy feeds the next epoch, one copy is emitted."""
    K = len(cfg_srcs)
    vs = [_v("s") for _ in range(K)]
    outs = [None] * K

    def build(i, forward):
        stepped = f"(({step} {cfg_srcs[i]}) {forward})"
        v = vs[i]
        if i == K - 1:
            outs[i] = v
            body = TUPN([outs[j] for j in range(K)])
            return f"(λ{v}.{body} {stepped})"
        la = Alloc()
        va, vb = la.copies(v, 2)
        outs[i] = vb
        inner = build(i + 1, va)
        body = "".join(la.prefix) + inner
        return f"(λ{v}.{body} {stepped})"

    return build(0, st0_src)


def harness_run(fx, step, st0, streams, runner=norm):
    """Reference: step epoch by epoch, DECODING and RE-ENCODING state each
    time (state leaves the calculus between epochs). Genuine clock dynamics
    -- no manual wire injection."""
    st = copy.deepcopy(st0)
    states = []
    for cfgm in streams:
        cfg = C.enc_config_bundle(fx, cfgm)
        enc = C.enc_state_v6(fx, st)
        st = C.dec_state_v6(fx, runner(f"(({step} {cfg}) {enc})"))
        states.append(copy.deepcopy(st))
    return states


def internal_run(fx, step, st0, streams, runner=norm):
    """One normal form for all K epochs; state never leaves the calculus."""
    st0_src = C.enc_state_v6(fx, st0)
    cfg_srcs = [C.enc_config_bundle(fx, m) for m in streams]
    nf = runner(drive_k(step, st0_src, cfg_srcs))
    xs = _spine(nf, len(streams))
    return [C.dec_state_v6(fx, x) for x in xs]


def films_of(fx, states, t0=3):
    return [film_bytes_v6(*state_to_film_args_v6(fx, s, t0 + k))
            for k, s in enumerate(states)]


def main():
    print(f"[BINDING slice 3b.5e] persistent epochs ({POLICY_FORGE})")
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
    K = 6

    # ---- 1) persistence identity: set a rotor at epoch 0, then run under the
    # world's own clock; the internal fold must equal the harness trajectory
    # state-for-state AND film-for-film.
    streams1 = [{"sp": (Cq, 0, 0, Cq)}] + [{"sp": None}] * (K - 1)
    href = harness_run(fx, step, st0, streams1)
    iref = internal_run(fx, step, st0, streams1)
    ok1 = (href == iref
           and films_of(fx, href) == films_of(fx, iref)
           and len(iref) == K)
    # sanity: the pose actually moved across the run (non-trivial trajectory)
    ok1 &= tuple(iref[-1]["pose_ob"]) != tuple(st0["pose_ob"])
    allok &= ok1
    print(f"  [{'PASS' if ok1 else 'FAIL'}] 1) persistence identity: "
          f"internal {K}-epoch fold == harness, state + film, every epoch "
          f"(final pose {tuple(iref[-1]['pose_ob'])})")

    # ---- 2) config-stream persistence: a rotor CHANGE mid-stream composes
    # inside the single normal form (the rotor field changes at the right
    # epoch and controls subsequent rotations).
    streams2 = [{"sp": (Cq, 0, 0, Cq)}, {"sp": None},
                {"sp": (0, Cq, Cq, 0)}, {"sp": None},
                {"sp": None}, {"sp": None}]
    href2 = harness_run(fx, step, st0, streams2)
    iref2 = internal_run(fx, step, st0, streams2)
    ok2 = (href2 == iref2
           and films_of(fx, href2) == films_of(fx, iref2)
           and tuple(iref2[0]["rotor_sp"]) == (Cq, 0, 0, Cq)
           and tuple(iref2[2]["rotor_sp"]) == (0, Cq, Cq, 0)
           and tuple(iref2[3]["rotor_sp"]) == (0, Cq, Cq, 0))
    allok &= ok2
    print(f"  [{'PASS' if ok2 else 'FAIL'}] 2) config-stream persistence: a "
          f"mid-stream rotor change composes internally == harness; rotor "
          f"field tracks the committed value across epochs")

    # ---- 3) sticky-fault persistence: a saturating rotor latches the fault
    # INSIDE the fold and it stays latched for the rest of the internal run.
    # The pulser fires the spinner on odd epochs (one-epoch wire delay), so the
    # saturating rotor must be COMMITTED at a firing epoch (config->COMMIT->
    # REACT: the just-committed rotor controls the rotation). Commit it at
    # epoch 1 with the pose still large -> the rotation overflows and latches.
    st_big = copy.deepcopy(st0); st_big["pose_ob"] = (big, big, 0, 0)
    streams3 = [{"sp": None}, {"sp": (big, big, 0, 0)}] \
        + [{"sp": None}] * (K - 2)
    href3 = harness_run(fx, step, st_big, streams3)
    iref3 = internal_run(fx, step, st_big, streams3)
    faults = [s["fault_ob"] for s in iref3]
    first1 = faults.index(1) if 1 in faults else None
    sticky = first1 is not None and all(f == 1 for f in faults[first1:])
    ok3 = (href3 == iref3 and sticky)
    allok &= ok3
    print(f"  [{'PASS' if ok3 else 'FAIL'}] 3) sticky-fault persistence: a "
          f"saturating rotor latches numeric_fault inside the fold; faults "
          f"per epoch = {faults} (stays 1 once set) == harness")

    # ---- 4) determinism: one driver term, normalized twice -> identical
    st0_src = C.enc_state_v6(fx, st0)
    cfg_srcs = [C.enc_config_bundle(fx, m) for m in streams1]
    drv = drive_k(step, st0_src, cfg_srcs)
    a = [film_hash_v6(*state_to_film_args_v6(fx, C.dec_state_v6(fx, x), 3 + k))
         for k, x in enumerate(_spine(norm(drv), K))]
    b = [film_hash_v6(*state_to_film_args_v6(fx, C.dec_state_v6(fx, x), 3 + k))
         for k, x in enumerate(_spine(norm(drv), K))]
    ok4 = (a == b)
    allok &= ok4
    print(f"  [{'PASS' if ok4 else 'FAIL'}] 4) determinism: the single "
          f"persistent driver normalized twice -> identical film-hash "
          f"sequence")

    # ---- 5) multi-controller persistence: two spinners on DIFFERENT pulser
    # periods (so they fire on independent schedules) with distinct rotors.
    # Their rotor/pose/fault states must persist INDEPENDENTLY through the same
    # fold -- no cross-contamination between controllers -- internal == harness.
    fx2 = Fixture({"p0": ("periodic", 2, 0), "p1": ("periodic", 3, 0)},
                  [], ["d0"], [("p0", "sp0"), ("p1", "sp1")],
                  spinners={"sp0": (w, n, (one, 0, 0, 0)),
                            "sp1": (w, n, (one, 0, 0, 0))},
                  orbs=["ob0", "ob1"],
                  sockets=[("sp0", "ob0"), ("sp1", "ob1")])
    step2, _ = C.compile_step_v6(fx2)
    st0_2 = init_state_v6(fx2)
    streams5 = [{"sp0": (Cq, 0, 0, Cq), "sp1": (0, Cq, Cq, 0)}] \
        + [{"sp0": None, "sp1": None}] * (K - 1)
    href5 = harness_run(fx2, step2, st0_2, streams5)
    iref5 = internal_run(fx2, step2, st0_2, streams5)
    ok5 = (href5 == iref5
           and films_of(fx2, href5) == films_of(fx2, iref5)
           and all(tuple(s["rotor_sp0"]) == (Cq, 0, 0, Cq) for s in iref5)
           and all(tuple(s["rotor_sp1"]) == (0, Cq, Cq, 0) for s in iref5)
           and tuple(iref5[-1]["pose_ob0"]) != tuple(iref5[-1]["pose_ob1"]))
    allok &= ok5
    print(f"  [{'PASS' if ok5 else 'FAIL'}] 5) multi-controller persistence: "
          f"two spinners (periods 2,3) with distinct rotors persist "
          f"independently through the fold == harness; ob0 pose "
          f"{tuple(iref5[-1]['pose_ob0'])} != ob1 {tuple(iref5[-1]['pose_ob1'])}")

    # ---- 6) NATIVE hard gate: the internal driver on ic32 == ic_ref, and
    # equals the harness reference, state-for-state, all epochs.
    if SKIP_NATIVE:
        native_status = "PASS_REF_ONLY (native skipped)"
        print("  [SKIP] 6) native gate skipped (TRVM_SKIP_NATIVE=1)")
    else:
        iref_ref = internal_run(fx, step, st0, streams2, runner=norm)
        iref_nat = internal_run(fx, step, st0, streams2, runner=native)
        href_ref = harness_run(fx, step, st0, streams2, runner=norm)
        ok6 = (iref_ref == iref_nat == href_ref)
        allok &= ok6
        st_ok = "PASS" if ok6 else "FAIL"
        if not ok6:
            native_status = "REF_ONLY (native MISMATCH)"
        print(f"  [{st_ok}] 6) native gate: internal {len(streams2)}-epoch "
              f"driver ic_ref == ic32 == harness (state-for-state)")

    dt = time.time() - t0
    verdict = native_status if allok else "FAIL"
    print(f"\n[slice 3b.5e] {'ALL PASS' if allok else 'FAILURES'} -- "
          f"{verdict} ({dt:.0f}s)")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
