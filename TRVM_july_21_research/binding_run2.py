"""binding_run2.py -- Option A, slice 2: the graph-driven compiler.

Decides whether slice 1 was a reusable architecture or a one-fixture
encoding. One typed Fixture description drives both sides: the model
builds it through real events; the compiler lowers the same description
to a closed IC term. Checks:

  A) regression -- the reduced-E2a description, compiled generically,
     matches the model film-for-film (and therefore the slice-1 hand
     lowering, which already matches the model);
  B) three hand topologies with hand-derived closed forms asserted on
     BOTH sides: fan-in (two coprime pulsers OR-merged into one door),
     fan-out (one relay driving two doors), and a three-relay ring
     (period 6);
  C) a 30-fixture random parity sweep (200 epochs each, randomized model
     schedules) with ic32 spot-checks on the first five fixtures;
  D) description-level mutation negatives: a mis-described fixture must
     diverge from the true model.
"""
import os, sys, subprocess, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import ic_ref
from ic_ref import parse, normal, reset_runtime, ctr
from e2_model import RandomChooser, RULEPACK_HASH
import film
import fixture as FX
import compiler as C

IC32 = os.path.join(HERE, "..", "runtime", "c", "ic32")

def model_films(fx, T, seed_base=9000):
    w, oid, wid_role = FX.build_model(fx)
    t0 = w.t
    proj0 = FX.model_projection(fx, w, oid, wid_role, t0 - 1)
    films, projs = [], []
    for e in range(T):
        w.step([], RandomChooser(random.Random(seed_base + e)))
        p = FX.model_projection(fx, w, oid, wid_role, w.t - 1)
        films.append(film.film_hash(*p))
        projs.append(p)
    return t0, proj0, films, projs, oid

def ic_films(fx, t0, proj0, T, runner="ref"):
    src, _ = C.compile_step(fx)
    st = FX.state_from_projection(fx, proj0, t0)
    films, costs = [], []
    for e in range(T):
        tc = t0 + e
        term_src = f"({src} {C.enc_state(fx, st)})"
        if runner == "ref":
            reset_runtime()
            nf = normal(parse(term_src), budget=4_000_000)
            costs.append(sum(ctr.values()))
        else:
            r = subprocess.run([IC32], input=term_src.encode(),
                               capture_output=True, timeout=30)
            out = r.stdout.decode().strip().splitlines()
            assert out, f"ic32 empty: {r.stderr.decode()[:200]}"
            reset_runtime()
            nf = parse(out[0])
        st = C.dec_state(fx, nf)
        films.append(film.film_hash(*FX.state_to_film_args(fx, st, tc)))
    return films, costs, st

def parity(fx, T, tag, ic32_T=0):
    t0, proj0, mf, projs, _ = model_films(fx, T)
    rf, costs, _ = ic_films(fx, t0, proj0, T)
    div = next((i for i, (a, b) in enumerate(zip(mf, rf)) if a != b), None)
    ok = div is None
    msg = (f"{T}/{T} films identical"
           if ok else f"DIVERGED at t={t0 + div}")
    extra = ""
    if ok and ic32_T:
        cf, _, _ = ic_films(fx, t0, proj0, ic32_T, runner="c")
        okc = cf == mf[:ic32_T]
        extra = f"; ic32 {ic32_T}/{ic32_T}" if okc else "; ic32 DIVERGED"
        ok &= okc
    print(f"  [{'PASS' if ok else 'FAIL'}] {tag}: {msg} "
          f"(cost {min(costs)}-{max(costs)}/epoch){extra}")
    return ok, t0, mf, projs

def main():
    print("[BINDING slice 2] graph-driven compiler")
    allok = True

    # --- A) regression: reduced E2a through the generic compiler
    e2a = FX.Fixture({"p3": (3, 0), "seed": (10 ** 9, 3)},
                     ["r1", "r2"], ["door"],
                     [("p3", "door"), ("seed", "r1"),
                      ("r1", "r2"), ("r2", "r1")])
    ok, t0, mf, projs = parity(e2a, 300, "reduced E2a (regression)",
                               ic32_T=60)
    allok &= ok

    # --- B) hand topologies with closed forms on both sides
    fanin = FX.Fixture({"p3": (3, 0), "pA": (5, 1)}, [], ["door"],
                       [("p3", "door"), ("pA", "door")])
    ok, t0, mf, projs = parity(fanin, 300, "fan-in: p3+pA -> door (OR)",
                               ic32_T=60)
    allok &= ok
    cf_ok = True
    for p in projs:
        t = p[0]
        if t - 2 >= t0:
            exp = 1 if ((t - 2) % 3 == 0) or ((t - 2) % 5 == 1) else 0
            cf_ok &= (p[2][0][1] == exp)
    print(f"    fan-in closed form (open(t) = fired3(t-2) OR fired5(t-2)): "
          f"{cf_ok}")
    allok &= cf_ok

    fanout = FX.Fixture({"pB": (4, 2)}, ["rX"], ["dA", "dB"],
                        [("pB", "rX"), ("rX", "dA"), ("rX", "dB")])
    ok, t0, mf, projs = parity(fanout, 300, "fan-out: pB -> rX -> dA,dB",
                               ic32_T=60)
    allok &= ok
    cf_ok = True
    for p in projs:
        t = p[0]
        if t - 4 >= t0:
            exp = 1 if (t - 4) % 4 == 2 else 0
            dA = next(x for x in p[2] if x[0] == "dA")[1]
            dB = next(x for x in p[2] if x[0] == "dB")[1]
            cf_ok &= (dA == exp and dB == exp and dA == dB)
    print(f"    fan-out closed form (both doors open(t) = firedB(t-4), "
          f"identical): {cf_ok}")
    allok &= cf_ok

    ring3 = FX.Fixture({"seed": (10 ** 9, 3)}, ["rA", "rB", "rC"], ["door"],
                       [("seed", "rA"), ("rA", "rB"), ("rB", "rC"),
                        ("rC", "rA"), ("rA", "door")])
    ok, t0, mf, projs = parity(ring3, 300, "ring-3 + tap: seed -> "
                               "rA->rB->rC->rA, rA -> door", ic32_T=60)
    allok &= ok
    cf_ok = True
    for p in projs:
        t = p[0]
        rA = next(x for x in p[3] if x[0] == "rA")[1]
        exp = 1 if t >= 5 and (t - 5) % 6 == 0 else 0
        cf_ok &= (rA == exp)
        if t >= 7:
            d = p[2][0][1]
            cf_ok &= (d == (1 if (t - 7) % 6 == 0 else 0))
    print(f"    ring-3 closed form (rA period 6 from t=5; door t=7): {cf_ok}")
    allok &= cf_ok

    # --- C) random fixture sweep
    print("  random sweep: 30 fixtures x 200 epochs, model vs ic_ref "
          "(ic32 spot: first 5 x 50):")
    sweep_ok = True
    for i in range(30):
        fx = FX.random_fixture(random.Random(4000 + i))
        try:
            ok, *_ = parity(fx, 200,
                            f"fx{i:02d} ({len(fx.pulsers)}p/"
                            f"{len(fx.relays)}r/{len(fx.doors)}d/"
                            f"{len(fx.edges)}e)",
                            ic32_T=50 if i < 5 else 0)
        except Exception as ex:
            print(f"  [FAIL] fx{i:02d}: {type(ex).__name__}: {ex}")
            ok = False
        sweep_ok &= ok
    allok &= sweep_ok
    print(f"  sweep: {'30/30 fixtures at full parity' if sweep_ok else 'FAILURES above'}")

    # --- D) description-level mutation negatives
    print("  description mutations (must diverge from the true model):")
    muts = [
        ("edge redirected: p3->door becomes p3->r1",
         FX.Fixture({"p3": (3, 0), "seed": (10 ** 9, 3)},
                    ["r1", "r2"], ["door"],
                    [("p3", "r1"), ("seed", "r1"),
                     ("r1", "r2"), ("r2", "r1")])),
        ("phase off by one: p3 phase 1",
         FX.Fixture({"p3": (3, 1), "seed": (10 ** 9, 3)},
                    ["r1", "r2"], ["door"],
                    [("p3", "door"), ("seed", "r1"),
                     ("r1", "r2"), ("r2", "r1")])),
        ("period changed: p3 period 4",
         FX.Fixture({"p3": (4, 0), "seed": (10 ** 9, 3)},
                    ["r1", "r2"], ["door"],
                    [("p3", "door"), ("seed", "r1"),
                     ("r1", "r2"), ("r2", "r1")])),
    ]
    t0, proj0, mf, _, _ = model_films(e2a, 40)
    def mutant_init(bad, proj, t0):
        pruned = (proj[0], [p for p in proj[1] if p[0] in bad.pulsers],
                  proj[2], proj[3],
                  [w for w in proj[4] if w[0] in bad.wires()])
        st = FX.state_from_projection(bad, pruned, t0)
        for wr in bad.wires():          # wires the true world never had
            st.setdefault(wr, (False, False))
        return st
    neg_ok = True
    for name, bad in muts:
        src, _ = C.compile_step(bad)
        st = mutant_init(bad, proj0, t0)
        div = None
        for e in range(40):
            reset_runtime()
            nf = normal(parse(f"({src} {C.enc_state(bad, st)})"),
                        budget=4_000_000)
            st = C.dec_state(bad, nf)
            h = film.film_hash(*FX.state_to_film_args(bad, st, t0 + e))
            if h != mf[e]:
                div = t0 + e
                break
        det = div is not None
        neg_ok &= det
        print(f"  [{'DETECTED' if det else 'MISSED  '}] {name}: "
              f"divergence at {div}")
    allok &= neg_ok

    print(f"\n  {'SLICE 2: PASS -- the lowering is a reusable compiler, not a one-fixture encoding' if allok else 'SLICE 2: FAIL'}")
    return 0 if allok else 1

if __name__ == "__main__":
    raise SystemExit(main())
