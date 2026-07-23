"""random_order.py -- a randomized-redex normalizer over ic_ref's exact
interaction rules (binding hardening, per review).

ic_ref's normal() is one deterministic lazy strategy. The Forge model
randomizes REACT scheduling every epoch, but slice 1 normalized the
lowered terms under that single reducer policy. This module closes the
gap the review named: it enumerates EVERY applicable redex in the whole
term tree each step, picks one uniformly at random, applies ic_ref's own
rule functions, and repeats to normal form -- then asserts that every
random order reaches the SAME decoded state with the SAME interaction
count as the reference strategy.

Faithfulness note: the collapse rules (DUP-VAR / DUP-APP) fire in the
reference only on genuinely stuck values (a free variable, or a spine
headed by one). The randomized enumerator preserves that: a Dup is a
redex when its value resolves to Lam/Sup/Era, or when it is a *stuck*
free-headed spine -- never on a still-reducible application. Bound Vars
with pending substitutions are resolved eagerly (affine: each name is
substituted at most once; resolution is not an interaction and is not
counted, matching the reference's accounting).

SCOPE, narrowed per review round 6: this is a CONSERVATIVE SCHEDULE
CLASS, not every legal IC redex order. The reference fires DUP-VAR on
ANY unresolved variable after whnf -- including lambda-bound variables
under an unapplied binder -- while this enumerator fires it only on
globally free variables. Executable boundary example (pinned by
boundary_check()):

    λx.!&1{a,b}=x;a   ->  ic_ref: λa.a, 1 interaction
                          this class: residual Dup, 0 interactions

Widening the condition is NOT safe on this substrate: firing DUP-VAR on
a bound variable creates two references to one name, which collides with
(a) this module's substitution-pop during resolution and (b) in-place
tree rewriting over the reference's aliasing global-sub representation.
The faithful all-order test belongs on the packed cell/net
representation, where rewrites are local by construction. Claims made
with this module are therefore of the form: invariant under the
conservative randomized/deterministic whole-tree schedule class.
"""
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "runtime", "python"))
import ic_ref
from ic_ref import (Var, Era, Lam, App, Sup, Dup, sub, ctr,
                    app_lam, app_sup, app_era, dup_lam, dup_sup, dup_era,
                    dup_var, dup_app, reset_runtime, parse)


def _resolve(t):
    """Chase pending substitutions on a Var (each fires at most once)."""
    while isinstance(t, Var) and not isinstance(t.nam, tuple) \
            and t.nam in sub:
        t = sub.pop(t.nam)
    return t


def _stuck_spine(t):
    """True iff t is a free Var or an App spine headed by one (genuinely
    stuck -- the only case the reference's collapse rules ever see)."""
    while isinstance(t, App):
        t = t.fun
        # a bound var with a pending sub is not stuck; caller resolves
        if isinstance(t, Var) and not isinstance(t.nam, tuple) \
                and t.nam in sub:
            return False
    return isinstance(t, Var)


FIELDS = {Lam: ("bod",), App: ("fun", "arg"), Sup: ("lft", "rgt"),
          Dup: ("val", "bod")}


def _redex_step(t):
    """If t is itself a redex after resolving its scrutinee, return the
    reduct; else None."""
    if isinstance(t, App):
        f = _resolve(t.fun)
        t.fun = f
        if isinstance(f, Lam):
            return app_lam(t, f)
        if isinstance(f, Sup):
            return app_sup(t, f)
        if isinstance(f, Era):
            return app_era(t, f)
        return None
    if isinstance(t, Dup):
        v = _resolve(t.val)
        t.val = v
        if isinstance(v, Lam):
            return dup_lam(t, v)
        if isinstance(v, Sup):
            return dup_sup(t, v)
        if isinstance(v, Era):
            return dup_era(t, v)
        if isinstance(v, Var) and isinstance(v.nam, tuple):
            return dup_var(t, v)                    # free var: stuck
        if isinstance(v, App) and _stuck_spine(v):
            return dup_app(t, v)                    # stuck spine
        return None
    return None


def _enumerate(root):
    """All (parent, field) slots holding a redex, plus whether root is one."""
    out = []
    stack = [(None, None, root)]
    while stack:
        par, fld, t = stack.pop()
        t = _resolve(t)
        if par is None:
            root = t
        else:
            setattr(par, fld, t)
        if isinstance(t, (App, Dup)):
            # probe redex-ness without applying: mimic _redex_step's tests
            scrut = _resolve(t.fun if isinstance(t, App) else t.val)
            if isinstance(t, App):
                t.fun = scrut
            else:
                t.val = scrut
            hot = isinstance(scrut, (Lam, Sup, Era)) or (
                isinstance(t, Dup) and (
                    (isinstance(scrut, Var) and isinstance(scrut.nam, tuple))
                    or (isinstance(scrut, App) and _stuck_spine(scrut))))
            if hot:
                out.append((par, fld, t))
        for f in FIELDS.get(type(t), ()):
            stack.append((t, f, getattr(t, f)))
    return root, out


def random_normal(term, rng, step_cap=1_000_000):
    """Normalize by uniformly random redex choice; return (nf, count)."""
    steps = 0
    while True:
        term, redexes = _enumerate(term)
        if not redexes:
            return term, steps
        par, fld, t = rng.choice(redexes)
        red = _redex_step(t)
        assert red is not None, "enumerated non-redex"
        steps += 1
        if steps > step_cap:
            raise RuntimeError("random_normal: step cap")
        if par is None:
            term = red
        else:
            setattr(par, fld, red)


def check_orders(src, n_orders, decode, seed0=0):
    """Reduce the same source under the reference strategy and n_orders
    random strategies; return (ref_state, ref_count, states_agree,
    counts_seen)."""
    reset_runtime()
    ref_nf = ic_ref.normal(parse(src), budget=4_000_000)
    ref_count = sum(ctr.values())
    ref_state = decode(ref_nf)
    counts = set()
    ok = True
    for k in range(n_orders):
        reset_runtime()
        nf, n = random_normal(parse(src), random.Random(seed0 + k))
        counts.add(n)
        ok &= (decode(nf) == ref_state)
    return ref_state, ref_count, ok, sorted(counts)


def strategy_normal(term, pick, step_cap=1_000_000):
    """Normalize with a caller-chosen redex selector over the same
    conservative class; pick(redexes) -> (parent, field, node)."""
    steps = 0
    while True:
        term, redexes = _enumerate(term)
        if not redexes:
            return term, steps
        par, fld, t = pick(redexes)
        red = _redex_step(t)
        assert red is not None
        steps += 1
        if steps > step_cap:
            raise RuntimeError("strategy_normal: step cap")
        if par is None:
            term = red
        else:
            setattr(par, fld, red)


def boundary_check():
    """Pin the known class boundary: the reference reduces the bound-var
    dup; the conservative class does not. Both facts asserted."""
    src_ = "λx.!&1{a,b}=x;a"
    reset_runtime()
    nf = ic_ref.normal(parse(src_))
    ref_n = sum(ctr.values())
    reset_runtime()
    nf2, n2 = random_normal(parse(src_), random.Random(0))
    def has_dup(t):
        if isinstance(t, Dup):
            return True
        return any(has_dup(getattr(t, f))
                   for f in FIELDS.get(type(t), ()))
    assert ref_n == 1 and n2 == 0 and has_dup(nf2), \
        "class boundary shifted -- update the scope statement"
    return ref_n, n2


def cost_report(k=5, seed=0, n_random=50):
    """Reproduce the strategy-cost finding on a composed K-epoch term:
    lazy reference vs random / first / middle / last whole-tree
    strategies. Returns {strategy: (count, states_ok)}."""
    import lower_e2a as L
    import binding_run as B
    L._LBL[0] = 9000 + 137 * k
    src_ = L.compose_src(k, L.enc_state(B.ic_init_state(2)))
    reset_runtime()
    ref_nf = ic_ref.normal(parse(src_), budget=8_000_000)
    ref_states = L.dec_list(ref_nf)
    out = {"lazy-reference": (sum(ctr.values()), True)}
    def run(pick):
        reset_runtime()
        nf, n = strategy_normal(parse(src_), pick, step_cap=4_000_000)
        return n, L.dec_list(nf) == ref_states
    rng = random.Random(seed)
    counts = set()
    ok_all = True
    for _ in range(n_random):
        n, ok = run(lambda rs: rng.choice(rs))
        counts.add(n)
        ok_all &= ok
    out[f"random x{n_random}"] = (sorted(counts), ok_all)
    for name, pick in [("first", lambda rs: rs[0]),
                       ("middle", lambda rs: rs[len(rs) // 2]),
                       ("last", lambda rs: rs[-1])]:
        out[name] = run(pick)
    return out


if __name__ == "__main__":
    print("boundary_check (ref interactions, conservative-class "
          "interactions):", boundary_check())
    print("cost_report(k=5):")
    for k_, v in cost_report().items():
        print(f"  {k_:>16}: {v}")
