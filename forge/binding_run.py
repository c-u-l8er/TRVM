"""binding_run.py -- Option A, slice 1: per-epoch canonical film parity
between the semantic model (e2_model, the golden oracle) and the real
interaction-calculus reducers (runtime/python/ic_ref.py and runtime/c/ic32)
on the reduced E2a clocked fixture.

Three grounds of truth, compared per epoch:
  1. e2_model.World driven by real events, randomized REACT schedules.
  2. ic_ref: the lowered STEP term, one epoch per normalization (shuttle).
  3. ic32 (C runtime): the same source text piped through the native binary.
Plus: K epochs composed inside ONE term (the reducer chains epochs itself,
film decoded from a single normal form) and closed-form assertions on both
sides independently (door period-3 from t=5; r1 period-4 from t=5).
"""
import os, sys, subprocess, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import random
import ic_ref
from ic_ref import parse, normal, reset_runtime, ctr
from e2_model import World, RandomChooser, RULEPACK_HASH
from e2_run import E, CFG, SIG, placed_id, ZeroChooser
import film
import lower_e2a as L

IC32 = os.path.join(HERE, "..", "runtime", "c", "ic32")

# ---------------------------------------------------------------- model side
def build_fixture():
    w = World()
    w.step([E(1, "STAMP", kind="pulser"), E(2, "STAMP", kind="door"),
            E(3, "STAMP", kind="relay"), E(4, "STAMP", kind="relay"),
            E(5, "STAMP", kind="pulser")], ZeroChooser())
    p3, d = placed_id(w, 1), placed_id(w, 2)
    r1, r2, seed = placed_id(w, 3), placed_id(w, 4), placed_id(w, 5)
    w.step([CFG(10, p3, "period", 3),
            CFG(11, seed, "period", 10 ** 9), CFG(12, seed, "phase", 3),
            E(13, "LINK", target=p3, dst=d, **SIG),
            E(14, "LINK", target=seed, dst=r1, **SIG),
            E(15, "LINK", target=r1, dst=r2, **SIG),
            E(16, "LINK", target=r2, dst=r1, **SIG)], ZeroChooser())
    roles = dict(p3=p3, door=d, r1=r1, r2=r2, seed=seed)
    wid_role = {}
    for wid, wd in w.wires.items():
        key = (wd["src_id"], wd["dst_id"])
        wid_role[wid] = {(p3, d): "w_pd", (seed, r1): "w_sr",
                         (r1, r2): "w_12", (r2, r1): "w_21"}[key]
    return w, roles, wid_role

def model_projection(w, roles, wid_role, t):
    ob = w.objs
    for r in ("p3", "seed"):
        assert ob[roles[r]]["armed"] == 0, "boundary armed nonzero"
    c3 = (t + 1) % 3
    sd = int(3 <= t)
    pulsers = [("p3", "periodic", 3, 0, 0, 0, ((0 - c3) % 3) + 1),
               ("seed", "once", 3, 3, 0, sd, -1 if sd else 3 - t)]
    doors = [("door", ob[roles["door"]]["open"],
              ob[roles["door"]]["next_open"])]
    relays = [(r, ob[roles[r]]["cur_out"], ob[roles[r]]["next_out"])
              for r in ("r1", "r2")]
    wires = sorted((wid_role[wid], wd["cur"], wd["nxt"])
                   for wid, wd in w.wires.items())
    return t, pulsers, doors, relays, wires

def closed_forms_ok(tc, door_open, r1_cur):
    d_exp = 1 if tc >= 5 and (tc - 5) % 3 == 0 else 0
    r_exp = 1 if tc >= 5 and (tc - 5) % 4 == 0 else 0
    return door_open == d_exp and r1_cur == r_exp

# ------------------------------------------------------------------ ic sides
def ic_init_state(t0):
    z = (0, 0)
    return dict(c3=t0 % 3, cs=min(t0, 4), w_pd=z, w_sr=z, w_12=z,
                w_21=z, door=z, r1=z, r2=z)

def ic_ref_epoch(step_txt, st):
    reset_runtime()
    t = parse(f"({step_txt} {L.enc_state(st)})")
    nf = normal(t, budget=2_000_000)
    return L.dec_state(nf), sum(ctr.values())

def ic32_epoch(step_txt, st):
    src = f"({step_txt} {L.enc_state(st)})"
    r = subprocess.run([IC32], input=src.encode(), capture_output=True,
                       timeout=30)
    out = r.stdout.decode().strip().splitlines()
    assert out, f"ic32 empty output: {r.stderr.decode()[:200]}"
    reset_runtime()
    return L.dec_state(parse(out[0]))

# ---------------------------------------------------------------------- main
def main(T=2000, T_c=2000, K=60):
    print("[BINDING slice 1] reduced E2a fixture: p3->door, seed->r1, "
          "r1<->r2 ring")
    w, roles, wid_role = build_fixture()
    t0 = w.t
    edges = [("p3", "sig_out", "door", "sig_in"),
             ("seed", "sig_out", "r1", "sig_in"),
             ("r1", "sig_out", "r2", "sig_in"),
             ("r2", "sig_out", "r1", "sig_in")]
    cfgs = [("p3", "period", 3), ("p3", "phase", 0),
            ("seed", "period", 10 ** 9), ("seed", "phase", 3)]
    _, fx_hash, _diag = film.fixture_manifest(edges, cfgs, RULEPACK_HASH, roles)
    print(f"  fixture {fx_hash[:16]}  rulepack {RULEPACK_HASH[:16]}  t0={t0}")

    # initial handoff must agree before any epoch runs
    m0 = film.film_hash(*model_projection(w, roles, wid_role, t0 - 1))
    i0 = film.film_hash(*L.state_to_film_args(ic_init_state(t0), t0 - 1))
    assert m0 == i0, "initial projections differ"

    # --- model films, randomized schedule per epoch
    mf, m_states = [], []
    for e in range(T):
        w.step([], RandomChooser(random.Random(9000 + e)))
        tc = w.t - 1
        proj = model_projection(w, roles, wid_role, tc)
        mf.append(film.film_hash(*proj))
        d_open = proj[2][0][1]
        r1_cur = proj[3][0][1]
        assert closed_forms_ok(tc, d_open, r1_cur), f"model closed form t={tc}"
        m_states.append((tc, d_open, r1_cur))
    print(f"  model:  {T} epochs, films computed, closed forms hold "
          f"(t={t0}..{t0 + T - 1})")

    # --- ic_ref shuttle
    step_txt = L.step_src()
    st = ic_init_state(t0)
    rf, costs = [], []
    for e in range(T):
        tc = t0 + e
        st, n_int = ic_ref_epoch(step_txt, st)
        costs.append(n_int)
        rf.append(film.film_hash(*L.state_to_film_args(st, tc)))
        assert closed_forms_ok(tc, int(st["door"][0]), int(st["r1"][0])), \
            f"ic_ref closed form t={tc}"
    div = next((i for i, (a, b) in enumerate(zip(mf, rf)) if a != b), None)
    print(f"  ic_ref: {T} epochs, {min(costs)}-{max(costs)} interactions/"
          f"epoch (median {int(statistics.median(costs))}), closed forms "
          f"hold")
    if div is None:
        print(f"  PARITY model==ic_ref: {T}/{T} film hashes identical")
    else:
        print(f"  DIVERGENCE at epoch {t0 + div}:")
        print(f"    model  {mf[div]}\n    ic_ref {rf[div]}")
    ok_ref = div is None

    # --- composed single term: K epochs, one normalization
    L._LBL[0] = 5000
    src = L.compose_src(K, L.enc_state(ic_init_state(t0)))
    reset_runtime()
    nf = normal(parse(src), budget=8_000_000)
    states = L.dec_list(nf)
    tot = sum(ctr.values())
    cf = [film.film_hash(*L.state_to_film_args(s, t0 + i))
          for i, s in enumerate(states)]
    ok_comp = (len(cf) == K and cf == mf[:K])
    print(f"  composed: {K} epochs in ONE term -> {len(states)} states, "
          f"{tot:,} interactions, film parity with model: {ok_comp}")

    # --- ic32 three-way
    ok_c = True
    if os.path.exists(IC32):
        st = ic_init_state(t0)
        cf32 = []
        for e in range(T_c):
            tc = t0 + e
            st = ic32_epoch(step_txt, st)
            cf32.append(film.film_hash(*L.state_to_film_args(st, tc)))
        div32 = next((i for i, (a, b) in enumerate(zip(mf, cf32))
                      if a != b), None)
        ok_c = div32 is None
        print(f"  ic32:   {T_c} epochs via native C runtime, parity with "
              f"model: {'%d/%d identical' % (T_c, T_c) if ok_c else 'DIVERGED at %d' % (t0 + div32)}")
    else:
        print("  ic32:   binary not present, skipped")

    verdict = ok_ref and ok_comp and ok_c
    print(f"\n  {'OPTION A SLICE 1: PASS' if verdict else 'SLICE 1: FAIL'} "
          f"-- the real reducers reproduce the semantic oracle's films "
          f"{'hash-for-hash' if verdict else '(see divergence above)'}")
    return 0 if verdict else 1

def mutation_negatives(T=40):
    """A parity harness that cannot fail is not evidence. Mutate the
    lowering and require detected divergence against the model within T
    epochs, at the exact first epoch the mutation matters."""
    w, roles, wid_role = build_fixture()
    t0 = w.t
    mf = []
    for e in range(T):
        w.step([], RandomChooser(random.Random(9000 + e)))
        mf.append(film.film_hash(
            *model_projection(w, roles, wid_role, w.t - 1)))
    step0 = L.step_src()
    # concrete mutations of a fresh STEP term (three textual, one structural)
    def m_or_to_and(src):
        # OR(a,b) = ((a T) b)  ->  AND(a,b) = ((a b) F): swap on the r1 line
        i = src.rindex("λbt.λbf.bt) ")           # the OR's T constant
        return src[:i] + "λbt.λbf.bf) " + src[i + len("λbt.λbf.bt) "):]
    def m_fire_off_by_one(src):
        # IS0_3: (c3 T F F) -> fires on c3==1 instead of 0
        i = src.index("λbt.λbf.bt) λbt.λbf.bf) λbt.λbf.bf")
        return (src[:i] + "λbt.λbf.bf) λbt.λbf.bt) λbt.λbf.bf"
                + src[i + len("λbt.λbf.bt) λbt.λbf.bf) λbt.λbf.bf"):])
    def m_drop_seed(src):
        # FIRES: make the seed never fire (S3 arm F instead of T)
        i = src.index("λbt.λbf.bf) λbt.λbf.bf) λbt.λbf.bt) λbt.λbf.bf")
        return (src[:i] + "λbt.λbf.bf) λbt.λbf.bf) λbt.λbf.bf) λbt.λbf.bf"
                + src[i + len("λbt.λbf.bf) λbt.λbf.bf) λbt.λbf.bt) λbt.λbf.bf"):])
    def m_swap_ring(src):
        # structural mis-wiring: a name swap consistent with binders is an
        # alpha-rename (identity) -- the missed mutation that taught us so
        return L.step_src(ring_swap=True)
    results = []
    for name, mut in [("ring OR->AND at r1", m_or_to_and),
                      ("p3 fires at t%3==1 (off-by-one)", m_fire_off_by_one),
                      ("seed never fires", m_drop_seed),
                      ("ring wires swapped", m_swap_ring)]:
        src = mut(L.step_src())
        st = ic_init_state(t0)
        first_div = None
        try:
            for e in range(T):
                st, _ = ic_ref_epoch(src, st)
                h = film.film_hash(*L.state_to_film_args(st, t0 + e))
                if h != mf[e]:
                    first_div = t0 + e
                    break
        except Exception as ex:
            first_div = f"structural ({type(ex).__name__})"
        results.append((name, first_div))
        print(f"  [{'DETECTED' if first_div is not None else 'MISSED  '}] "
              f"{name}: divergence at {first_div}")
    missed = [n for n, d in results if d is None]
    print(f"  mutation sensitivity: {len(results) - len(missed)}/"
          f"{len(results)} detected")
    return 0 if not missed else 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "NEG":
        raise SystemExit(mutation_negatives())
    raise SystemExit(main())
