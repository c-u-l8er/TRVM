"""fixture.py v0.2 -- typed static-fixture descriptions.

v0.2 (review round 6): EXPLICIT CLOCK MODES and a real schema.

Clock modes -- a numeric threshold may change representation, never
meaning (Binding Law 5):
    ("periodic", period, phase)   fires every t with t % period == phase
    ("once", epoch)               fires exactly at t == epoch
Model-side, "once" is NATIVE as of proc-e2.3 (mode/epoch/done on the
clock object); the old period-10**9 sentinel is gone, and the bound is
stated, so the realization is exact within any feasible run.

Schema validation (all raise ValueError):
    role identifiers: nonempty [A-Za-z0-9_]+, no "__" substring (wire
      display names are delimiter-joined; "__" in a role forges them);
    role names unique ACROSS kinds;
    periodic: period >= 1 and 0 <= phase < period; once: epoch >= 0;
    every edge endpoint declared; no duplicate edges.
The canonical wire identity is the typed endpoint tuple (src, "sig_out",
dst, "sig_in"); the display role "w__src__dst" is unambiguous only
because "__" is banned in roles -- both facts are enforced, not assumed.
"""
import re
import random as _random
from e2_model import World, OUT_PORTS, LEGAL_PAIRS
from e2_run import E, CFG, SIG, placed_id, ZeroChooser

ONEHOT_MAX = 32          # representation bound only: periodic clocks up
                         # to this compile as one-hot enums, above it as
                         # binary counters. Same semantics either side.

_ROLE = re.compile(r"^[A-Za-z0-9_]+$")

def _chk(cond, msg):
    if not cond:
        raise ValueError(msg)

class Fixture:
    def __init__(self, pulsers, relays, doors, edges, spinners=None,
                 orbs=None, sockets=None):
        # round 12 (3b.5a): spinners = {role: (w, n, rotor4)} at the
        # LEGACY numeric policy (proc-e2.3 per-product trunc0, no sat);
        # orbs = [roles]; sockets = [(spinner, orb)] -- socket edges are
        # NOT wires (different mechanism, LEGAL_PAIRS (socket, pose)).
        self.spinners = dict(spinners or {})
        self.orbs = list(orbs or [])
        self.sockets = list(sockets or [])
        """pulsers: {role: ("periodic", period, phase) | ("once", epoch)};
        relays/doors: [role]; edges: [(src_role, dst_role)] sig wires."""
        self.pulsers = {}
        for r, spec in dict(pulsers).items():
            _chk(isinstance(spec, tuple) and spec and spec[0] in
                 ("periodic", "once"),
                 f"pulser {r!r}: clock mode must be explicit "
                 f"('periodic', p, ph) or ('once', e); got {spec!r}")
            if spec[0] == "periodic":
                _, p, ph = spec
                _chk(isinstance(p, int) and p >= 1, f"{r}: period >= 1")
                _chk(isinstance(ph, int) and 0 <= ph < p,
                     f"{r}: phase in [0, period)")
                _chk(p < 10 ** 9, f"{r}: period too large")
            else:
                _, e = spec
                _chk(isinstance(e, int) and 0 <= e < 10 ** 6,
                     f"{r}: once epoch in [0, 1e6)")
            self.pulsers[r] = spec
        self.relays = sorted(relays)
        self.doors = sorted(doors)
        roles = (list(self.pulsers) + self.relays + self.doors
                 + sorted(self.spinners) + self.orbs)
        for r in roles:
            _chk(_ROLE.match(r) and "__" not in r,
                 f"bad role identifier {r!r} (alnum/_ only, no '__')")
        _chk(len(set(roles)) == len(roles),
             f"role names must be unique across kinds: {sorted(roles)}")
        kinds = self.kinds()
        _chk(len(set(edges)) == len(edges), "duplicate edge")
        for s, d in edges:
            _chk(s in kinds, f"edge source {s!r} not declared")
            _chk(d in kinds, f"edge destination {d!r} not declared")
            _chk("sig_out" in OUT_PORTS.get(kinds[s], ()),
                 f"{s} ({kinds[s]}) has no sig_out")
            _chk(kinds[d] in ("door", "relay", "spinner"),
                 f"{d} ({kinds[d]}) cannot receive sig")
            assert ("sig_out", "sig_in") in LEGAL_PAIRS
        self.edges = sorted(edges)
        for s, (w_, n_, rq) in self.spinners.items():
            _chk(isinstance(w_, int) and w_ > 0 and 0 <= n_ <= w_,
                 f"{s}: bad lane geometry")
            _chk(isinstance(rq, tuple) and len(rq) == 4
                 and all(isinstance(v, int) and 0 <= v < (1 << w_)
                         for v in rq), f"{s}: rotor lanes out of range")
            ins = [e for e in self.edges if e[1] == s]
            _chk(len(ins) == 1, f"{s}: spinner requires exactly one "
                 f"sig-in (model SIG_MERGE none)")
            socks = [x for x in self.sockets if x[0] == s]
            _chk(len(socks) == 1, f"{s}: spinner requires exactly one "
                 f"socket")
        for (s, o) in self.sockets:
            _chk(s in self.spinners and o in self.orbs,
                 f"socket {s}->{o}: unknown role")
        for o in self.orbs:
            ctl = [s for (s, oo) in self.sockets if oo == o]
            _chk(len(ctl) <= 1, f"{o}: controller exclusivity violated "
                 f"(model rejects the second socket LINK as controlled)")

    def kinds(self):
        k = {r: "pulser" for r in self.pulsers}
        k.update({r: "relay" for r in self.relays})
        k.update({r: "door" for r in self.doors})
        k.update({r: "spinner" for r in self.spinners})
        k.update({r: "orb" for r in self.orbs})
        return k

    def controller_of(self, orb):
        for (s, o) in self.sockets:
            if o == orb:
                return s
        return ""

    def model_params(self, role):
        """Native model config per proc-e2.3: periodic -> (period,
        phase) pairs; once -> (mode, epoch) pairs."""
        spec = self.pulsers[role]
        if spec[0] == "periodic":
            return [("period", spec[1]), ("phase", spec[2])]
        return [("mode", "once"), ("epoch", spec[1])]

    def wire_role(self, s, d):
        return f"w__{s}__{d}"

    def wires(self):
        return sorted(self.wire_role(s, d) for s, d in self.edges)

    def layout(self):
        return (sorted(self.pulsers), self.wires(), self.doors, self.relays)

    def counter_spec(self, role):
        """('onehot', period, phase) | ('binp', period, phase, width) |
        ('once', epoch, width)"""
        spec = self.pulsers[role]
        if spec[0] == "once":
            e = spec[1]
            return ("once", e, max(1, (e + 1).bit_length()))
        _, p, ph = spec
        if p <= ONEHOT_MAX:
            return ("onehot", p, ph)
        return ("binp", p, ph, p.bit_length())

    def in_wires(self, role):
        return sorted(self.wire_role(s, d) for s, d in self.edges
                      if d == role)

    def out_wires(self, role):
        return sorted(self.wire_role(s, d) for s, d in self.edges
                      if s == role)

# ---------------------------------------------------------------- model side
def build_model(fx):
    w = World()
    order = (sorted(fx.pulsers) + fx.relays + fx.doors
             + sorted(fx.spinners) + fx.orbs)
    kinds = fx.kinds()
    stamps = [E(i + 1, "STAMP", kind=kinds[r]) for i, r in enumerate(order)]
    w.step(stamps, ZeroChooser())
    oid = {r: placed_id(w, i + 1) for i, r in enumerate(order)}
    seq = [100]
    def nxt():
        seq[0] += 1
        return seq[0]
    batch = []
    for r in sorted(fx.pulsers):
        for field, val in fx.model_params(r):
            batch.append(CFG(nxt(), oid[r], field, val))
    for s, (w_, n_, rq) in sorted(fx.spinners.items()):
        # model-side rotor: EXACT rescale of the proxy lanes to Q32.32
        # (the anchor embedding; the proxy geometry is the filmed
        # contract, the rescale keeps the Q32.32 world structurally in
        # lockstep and configured through the same CFG machinery)
        def s_of(v):
            return v - (1 << w_) if v >= (1 << (w_ - 1)) else v
        r32 = tuple(s_of(v) << (32 - n_) for v in rq)
        batch.append(CFG(nxt(), oid[s], "rotor", r32))
    for s, d in fx.edges:
        batch.append(E(nxt(), "LINK", target=oid[s], dst=oid[d], **SIG))
    for s, o in fx.sockets:
        batch.append(E(nxt(), "LINK", target=oid[s], dst=oid[o],
                       src_port="socket", dst_port="pose"))
    w.step(batch, ZeroChooser())
    wid_role = {}
    inv = {v: k for k, v in oid.items()}
    for wid, wd in w.wires.items():
        wid_role[wid] = fx.wire_role(inv[wd["src_id"]], inv[wd["dst_id"]])
    return w, oid, wid_role

def model_projection(fx, w, oid, wid_role, t, poses=None):
    ob = w.objs
    for r in fx.pulsers:
        assert ob[oid[r]]["armed"] == 0, "boundary armed nonzero"
    pulsers = []
    for r in sorted(fx.pulsers):
        spec = fx.pulsers[r]
        if spec[0] == "once":
            e = spec[1]
            done = int(ob[oid[r]]["done"])       # STATE-authoritative
            pulsers.append((r, "once", e, e, 0, done,
                            -1 if done else e - t))
        else:
            p, ph = spec[1], spec[2]
            c = (t + 1) % p
            pulsers.append((r, "periodic", p, ph, 0, 0,
                            ((ph - c) % p) + 1))
    doors = [(r, ob[oid[r]]["open"], ob[oid[r]]["next_open"])
             for r in fx.doors]
    relays = [(r, ob[oid[r]]["cur_out"], ob[oid[r]]["next_out"])
              for r in fx.relays]
    wires = sorted((wid_role[wid], wd["cur"], wd["nxt"])
                   for wid, wd in w.wires.items())
    inv = {v: k for k, v in oid.items()}
    spinners = []
    for s in sorted(fx.spinners):
        w_, n_, rq = fx.spinners[s]
        sock_id = w.objs[oid[s]].get("socket", "")
        sock = inv.get(sock_id, "")
        # config-integrity: the model rotor must equal the anchor
        # rescale of the filmed proxy lanes
        def s_of(v):
            return v - (1 << w_) if v >= (1 << (w_ - 1)) else v
        assert tuple(w.objs[oid[s]]["rotor"]) == tuple(
            s_of(v) << (32 - n_) for v in rq), "model rotor != anchor"
        spinners.append((s, "legacy_spinner_pp_tz_nosat_v1", w_, n_,
                         tuple(rq), sock))
    orbs = []
    for o in fx.orbs:
        ctl_id = w.objs[oid[o]].get("controller", "")
        ctl = inv.get(ctl_id, "")
        s = fx.controller_of(o)
        w_, n_, _ = fx.spinners[s] if s else (8, 4, None)
        pl = tuple((poses or {}).get(o, (1 << n_, 0, 0, 0)))
        orbs.append((o, "legacy_spinner_pp_tz_nosat_v1", w_, n_, pl,
                     ctl, 0))
    return t, pulsers, doors, relays, wires, spinners, orbs

def state_from_projection(fx, proj, t0):
    t, pulsers, doors, relays, wires, *rest = proj
    # film v0.5 appends (spinners, orbs); discrete reconstruction
    # ignores them here -- pose state is carried by the harness for
    # spinner fixtures (binding_run3e), and this helper serves the
    # discrete-only slices.
    st = {}
    for r in sorted(fx.pulsers):
        spec = fx.counter_spec(r)
        if spec[0] in ("onehot", "binp"):
            p = spec[1]
            st["c_" + r] = t0 % p
        else:
            e, w_ = spec[1], spec[2]
            st["c_" + r] = (int(e < t0), t0 % (1 << w_))   # (done, k)
    for (role, c, n) in wires:
        st[role] = (bool(c), bool(n))
    for (role, o, n) in doors:
        st[role] = (bool(o), bool(n))
    for (role, c, n) in relays:
        st[role] = (bool(c), bool(n))
    return st

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

# ----------------------------------------------------------------- generator
def random_fixture(rng):
    """Random legal fixture over ALL clock modes: one-hot periodics (2-6),
    binary periodics (33-90: a 200+-epoch horizon sees >= 2 firings), and
    once-clocks (epoch 3-8: the fire AND the long silence both land in
    the horizon)."""
    pulsers = {}
    for i in range(rng.randint(1, 3)):
        u = rng.random()
        if u < 0.25:
            pulsers[f"p{i}"] = ("once", rng.randint(3, 8))
        elif u < 0.5:
            p = rng.randint(33, 90)
            pulsers[f"p{i}"] = ("periodic", p, rng.randint(0, p - 1))
        else:
            p = rng.randint(2, 6)
            pulsers[f"p{i}"] = ("periodic", p, rng.randint(0, p - 1))
    relays = [f"r{i}" for i in range(rng.randint(0, 3))]
    doors = [f"d{i}" for i in range(rng.randint(1, 2))]
    srcs = list(pulsers) + relays
    dsts = relays + doors
    edges = set()
    for d in doors:
        edges.add((rng.choice(srcs), d))
    for r in relays:
        edges.add((rng.choice(srcs), r))
    for _ in range(rng.randint(0, 4)):
        edges.add((rng.choice(srcs), rng.choice(dsts)))
    return Fixture(pulsers, relays, doors, sorted(edges))


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
