"""binding_run3.py -- Slice 3a: binary clock counters (review round 6).

The period-33 bug: the v0.1 compiler silently compiled any period > 32
as a saturating one-shot; the model has no one-shot type, so the second
firing (t = period) diverged -- beyond every horizon the v0.1 sweep
tested. Fixed by explicit clock modes (fixture v0.2) plus binary
ripple-carry counters (compiler v0.2). This battery:

  A) reconstructs the old bug as a permanent negative: a Once-compiled
     clock against a periodic-33 model MUST diverge at t=33;
  B) long-horizon parity per the review's table -- (33,0) x150,
     (64,7) x300, (257,100) x700, Once@40 x400 -- with fire-pattern
     closed forms on both sides and ic32 spot checks;
  C) a mixed random sweep over ALL clock modes (20 fixtures x 250);
  D) the five schema negatives (must raise);
  E) cost notes: interactions/epoch by counter representation;
  F) the composed-cost strategy report, reproducible from the package.
"""
import os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import fixture as FX
import compiler as C
import binding_run2 as B2
import random_order as RO

def fired(fx, role, tau):
    spec = fx.pulsers[role]
    if spec[0] == "periodic":
        return tau % spec[1] == spec[2]
    return tau == spec[1]

def main():
    print("[BINDING slice 3a] binary clock counters")
    allok = True

    # --- A) the old bug, reconstructed as a negative. The v0.1 compiler
    # emitted a one-shot REPRESENTATION for a declared periodic-33 -- the
    # static labels (period=33) were identical on both sides; only the
    # dynamics diverged, at the second firing. Reconstruct exactly that:
    # once-compiled dynamics rendered under the TRUTH fixture's labels.
    truth = FX.Fixture({"p": ("periodic", 33, 0)}, [], ["d"], [("p", "d")])
    bug = FX.Fixture({"p": ("once", 0)}, [], ["d"], [("p", "d")])
    t0, proj0, mf, _, _ = B2.model_films(truth, 40)
    st = FX.state_from_projection(bug, proj0, t0)
    src, _ = C.compile_step(bug)
    div = None
    import film
    from ic_ref import parse, normal, reset_runtime
    for e in range(40):
        reset_runtime()
        nf = normal(parse(f"({src} {C.enc_state(bug, st)})"),
                    budget=4_000_000)
        st = C.dec_state(bug, nf)
        args = FX.state_to_film_args(bug, st, t0 + e)
        nfv = ((0 - ((t0 + e + 1) % 33)) % 33) + 1
        args = (args[0], [("p", "periodic", 33, 0, 0, 0, nfv)],
                *args[2:])   # truth's labels
        h = film.film_hash(*args)
        if h != mf[e]:
            div = t0 + e
            break
    ok = div == 33
    allok &= ok
    print(f"  [{'PASS' if ok else 'FAIL'}] horizon-bug regression: "
          f"once-compiled clock vs periodic-33 model diverges at t={div} "
          f"(must be 33)")

    # --- B) long-horizon binary parity, closed forms both sides
    cases = [("periodic 33 phase 0", ("periodic", 33, 0), 150),
             ("periodic 64 phase 7", ("periodic", 64, 7), 300),
             ("periodic 257 phase 100", ("periodic", 257, 100), 700),
             ("once at 40", ("once", 40), 400)]
    for name, spec, T in cases:
        fx = FX.Fixture({"p": spec}, [], ["d"], [("p", "d")])
        ok, t0, mf, projs = B2.parity(fx, T, f"{name} x{T}",
                                      ic32_T=30)
        allok &= ok
        cf = True
        fires = 0
        for p in projs:
            t = p[0]
            if t - 2 >= t0:
                exp = 1 if fired(fx, "p", t - 2) else 0
                fires += exp
                cf &= (p[2][0][1] == exp)
        print(f"    closed form (open(t)=fired(t-2)): {cf}; "
              f"firings observed in horizon: {fires}")
        allok &= cf and fires >= 1
        if spec[0] == "periodic":
            allok &= fires >= 2      # the bug class: second firing seen

    # --- C) mixed sweep over all clock modes
    print("  mixed sweep: 20 fixtures x 250 epochs (all clock modes; "
          "ic32 spot: first 4 x 40):")
    sweep_ok = True
    for i in range(20):
        fx = FX.random_fixture(random.Random(7000 + i))
        modes = "".join(sorted(s[0][0] for s in fx.pulsers.values()))
        try:
            ok, *_ = B2.parity(fx, 250,
                               f"fx{i:02d} [{modes}] "
                               f"({len(fx.pulsers)}p/{len(fx.relays)}r/"
                               f"{len(fx.doors)}d/{len(fx.edges)}e)",
                               ic32_T=40 if i < 4 else 0)
        except Exception as ex:
            print(f"  [FAIL] fx{i:02d}: {type(ex).__name__}: {ex}")
            ok = False
        sweep_ok &= ok
    allok &= sweep_ok
    print(f"  sweep: {'20/20 at full parity' if sweep_ok else 'FAILURES'}")

    # --- D) schema negatives
    negs = [
        ("role-kind collision",
         lambda: FX.Fixture({"x": ("periodic", 3, 0)}, ["x"], ["d"],
                            [("x", "d")])),
        ("double-underscore role",
         lambda: FX.Fixture({"a__b": ("periodic", 3, 0)}, [], ["c"],
                            [("a__b", "c")])),
        ("phase >= period",
         lambda: FX.Fixture({"p": ("periodic", 3, 3)}, [], ["d"],
                            [("p", "d")])),
        ("implicit clock tuple",
         lambda: FX.Fixture({"p": (33, 0)}, [], ["d"], [("p", "d")])),
        ("undeclared endpoint",
         lambda: FX.Fixture({"p": ("periodic", 3, 0)}, [], ["d"],
                            [("p", "ghost")])),
    ]
    neg_ok = True
    for name, f in negs:
        try:
            f()
            print(f"  [MISSED  ] schema: {name}")
            neg_ok = False
        except ValueError:
            print(f"  [REJECTED] schema: {name}")
    allok &= neg_ok

    # --- E) cost DISTRIBUTIONS by representation (review round 7: a
    # first-epoch sample is not a cost model -- binary cost varies with
    # bit pattern, carry length, reset and firing; report the
    # distribution over at least one full cycle, and name the strategy)
    import statistics
    print("  cost distributions (lazy reference, one full cycle+):")
    for name, spec, T in [("one-hot p=3", ("periodic", 3, 0), 12),
                          ("binary p=33 (w=6)", ("periodic", 33, 0), 70),
                          ("binary p=257 (w=9)", ("periodic", 257, 100),
                           264),
                          ("once e=40", ("once", 40), 90)]:
        fx = FX.Fixture({"p": spec}, [], ["d"], [("p", "d")])
        t0, proj0, mf, _, _ = B2.model_films(fx, T)
        _, costs, _ = B2.ic_films(fx, t0, proj0, T)
        cs = sorted(costs)
        p95 = cs[min(len(cs) - 1, int(0.95 * len(cs)))]
        u = len(set(cs))
        print(f"    {name:>20}: min {cs[0]} / mean "
              f"{statistics.mean(cs):.2f} / median {cs[len(cs) // 2]} / "
              f"p95 {p95} / max {cs[-1]}  ({u} unique over {T} epochs)")
        if spec[0] != "periodic" or spec[1] > 32:
            allok &= u >= 2          # variance is the point being fixed
    from ic_ref import parse as _p, reset_runtime as _rr
    fxE = FX.Fixture({"p": ("periodic", 33, 0)}, [], ["d"], [("p", "d")])
    srcE, _ = C.compile_step(fxE)
    stE = FX.init_state(fxE)
    eager = []
    for e in range(10):
        term = f"({srcE} {C.enc_state(fxE, stE)})"
        _rr()
        nf, n = RO.strategy_normal(_p(term), lambda rs: rs[0])
        stE = C.dec_state(fxE, nf)
        eager.append(n)
    print(f"    eager 'first' strategy sample (p=33, 10 epochs): "
          f"min {min(eager)} / max {max(eager)}  "
          f"(vs lazy min above -- strategies named, per Law 4)")

    # --- F) composed-cost strategy report (reproducible)
    print("  composed-cost strategy report (random_order.cost_report):")
    rep = RO.cost_report(k=5, n_random=20)
    for k_, v in rep.items():
        print(f"    {k_:>16}: {v}")
    lazy = rep["lazy-reference"][0]
    eager = {v[0] if isinstance(v[0], int) else v[0][0]
             for k_, v in rep.items() if k_ != "lazy-reference"}
    allok &= all(v[1] for v in rep.values()) and len(eager) == 1 \
        and lazy < min(eager)
    print(f"    state parity all strategies; eager class "
          f"{sorted(eager)} vs lazy {lazy}")

    print(f"\n  {'SLICE 3a: PASS -- arbitrary periods and true once-clocks, horizon bug dead' if allok else 'SLICE 3a: FAIL'}")
    return 0 if allok else 1

if __name__ == "__main__":
    raise SystemExit(main())
