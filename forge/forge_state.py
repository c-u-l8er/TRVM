"""forge_state.py -- the PRODUCTION state adapter (v0.6.5 release closure).

The Spinner Bench release needs exactly two state operations, and both are pure
functions of a duck-typed lowering VIEW (the production `_PlanView`, or the
Fixture oracle in Verify-Oracle mode -- either object answers the same read
interface):

  * init_state_v6(view)             -- the initial world state from the plan/view
  * state_to_film_args_v6(view, st, t) -- project a world state to Film v0.7 args

Before v0.6.5 these lived in `fixture.py`, so `spinner_bench` imported the
Fixture module (and thus the whole oracle) just to seed and project state on the
NORMAL Run path. GPT-5.6's v0.6.5 ruling required the production run to import NO
Fixture; this module is that extraction. The bodies are byte-for-byte the same
computation that previously lived in `fixture.py` (a dependency-boundary
correction, not a behavior change). `fixture.py` now re-imports these names so
every existing battery keeps working unchanged.

Nothing here imports `fixture`; the functions consume only the duck-typed read
interface (pulsers/orbs/wires/doors/relays/spinners/sockets + counter_spec,
controller_of, orb_of, is_configurable, out_wires) that both a `_PlanView` and a
`Fixture` provide. That is exactly why the normal Run path is Fixture-free.
"""


def state_to_film_args(fx, st, t):
    """nf is derived from the DECODED COUNTER, never from t -- that is
    the point: a counter inconsistent with t must change the film."""
    pulsers = []
    for r in sorted(fx.pulsers):
        spec = fx.pulsers[r]
        if spec[0] == "once":
            done, k = int(st["c_" + r][0]), st["c_" + r][1]
            nf = -1 if done else spec[1] - (k - 1)
            pulsers.append((r, "once", spec[1], spec[1], 0, done, nf))
        else:
            p, ph = spec[1], spec[2]
            c = st["c_" + r]                     # (t+1) mod p, decoded
            pulsers.append((r, "periodic", p, ph, 0, 0,
                            ((ph - c) % p) + 1))
    doors = [(r, st[r][0], st[r][1]) for r in fx.doors]
    relays = [(r, st[r][0], st[r][1]) for r in fx.relays]
    wires = [(wr, st[wr][0], st[wr][1]) for wr in fx.wires()]
    spinners = []
    for s in sorted(fx.spinners):
        w_, n_, rq = fx.spinners[s]
        sock = next(o for (ss, o) in fx.sockets if ss == s)
        spinners.append((s, "legacy_spinner_pp_tz_nosat_v1", w_, n_,
                         tuple(rq), sock))
    orbs = []
    for o in fx.orbs:
        s = fx.controller_of(o)
        w_, n_, _ = fx.spinners[s] if s else (8, 4, None)
        orbs.append((o, "legacy_spinner_pp_tz_nosat_v1", w_, n_,
                     tuple(st["pose_" + o]), s, 0))
    return t, pulsers, doors, relays, wires, spinners, orbs


def init_state(fx, t0=2):
    """Independent initial-world construction from the fixture artifact
    alone (review round 7): no model projection is consulted. The
    two-epoch build recipe is part of the artifact contract: epoch 0
    stamps objects (default params, no wires -- any default-param firing
    is inert); epoch 1 admits configs THEN links, then commits with the
    CONFIGURED params -- so a clock that fires at t=1 (periodic with
    1 % period == phase, or once with epoch == 1) seeds its out-wires'
    nxt at the t0=2 boundary. Once(0) never fires model-side (its config
    lands after its moment; the native done latches at the admit-epoch
    commit), so both sides agree it never fires at ANY t -- the old
    period-10**9 sentinel and its horizon caveat are gone (proc-e2.3).
    Everything else is zero."""
    assert t0 == 2, "init_state encodes the two-epoch build recipe"
    st = {}
    fired1 = set()
    for r in sorted(fx.pulsers):
        spec = fx.counter_spec(r)
        ps = fx.pulsers[r]
        if spec[0] in ("onehot", "binp"):
            st["c_" + r] = t0 % spec[1]
        else:
            e, w_ = spec[1], spec[2]
            st["c_" + r] = (int(e < t0), t0 % (1 << w_))
        # fired-at-1 predicate, native per mode (proc-e2.3): a periodic
        # clock fires at t=1 iff 1 % period == phase; a once clock iff
        # its epoch is 1 (the construction-priming recipe).
        if (ps[0] == "periodic" and (1 % ps[1]) == ps[2]) or \
           (ps[0] == "once" and ps[1] == 1):
            fired1.add(r)
    for o in fx.orbs:
        s = fx.controller_of(o)
        w_, n_, _ = fx.spinners[s] if s else (8, 4, None)
        st["pose_" + o] = (1 << n_, 0, 0, 0)     # proxy identity
    for wr in fx.wires():
        st[wr] = (False, False)
    for r in fired1:
        for wr in fx.out_wires(r):
            st[wr] = (False, True)
    for f in fx.doors + fx.relays:
        st[f] = (False, False)
    return st


def init_state_v6(fx, t0=2):
    """v0.6 initial state: the v0.5 discrete build PLUS, per orb, a
    proxy-identity pose and a cleared fault, and per controlling spinner
    the rotor SEEDED from the fixture initialization data (thereafter the
    current rotor lives only in state)."""
    st = init_state(fx, t0)
    for o in fx.orbs:
        st["fault_" + o] = 0
    for o in fx.orbs:
        s = fx.controller_of(o)
        if not s:
            continue
        w_, n_, rq = fx.spinners[s]
        st["rotor_" + s] = tuple(rq)        # init data -> state
    return st


def state_to_film_args_v6(fx, st, t):
    """v0.6 film args: rotor read from st['rotor_'+s], fault from
    st['fault_'+o], forge policy, and the config PERMISSION per spinner."""
    from binlib import POLICY_FORGE
    t2, pulsers, doors, relays, wires, _sp0, _ob0 = \
        state_to_film_args(fx, st, t)
    spinners = []
    for s in sorted(fx.spinners):
        w_, n_, _ = fx.spinners[s]
        sock = fx.orb_of(s)
        perm = "configurable" if fx.is_configurable(s) else "fixed"
        spinners.append((s, POLICY_FORGE, w_, n_,
                         tuple(st["rotor_" + s]), sock, perm))
    orbs = []
    for o in fx.orbs:
        s = fx.controller_of(o)
        w_, n_, _ = fx.spinners[s] if s else (8, 4, None)
        orbs.append((o, POLICY_FORGE, w_, n_, tuple(st["pose_" + o]),
                     s, int(st.get("fault_" + o, 0))))
    return t, pulsers, doors, relays, wires, spinners, orbs
