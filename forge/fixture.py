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

from lowering_policy import DEFAULT_ONEHOT_MAX, counter_spec_for
ONEHOT_MAX = DEFAULT_ONEHOT_MAX  # re-export: the canonical threshold now lives
                                 # in lowering_policy (Phase 3D.1-D); the Fixture
                                 # oracle lowers at the `auto` default policy.

# The state seed / film-projection functions moved to forge_state.py in v0.6.5
# (the PRODUCTION Run path must import no Fixture). They are pure functions of a
# duck-typed view, so the Fixture oracle uses the SAME implementations; re-export
# them here so every existing `from fixture import ...` battery keeps working.
from forge_state import (init_state, state_to_film_args,
                         init_state_v6, state_to_film_args_v6)

_ROLE = re.compile(r"^[A-Za-z0-9_]+$")

def _chk(cond, msg):
    if not cond:
        raise ValueError(msg)

class Fixture:
    def __init__(self, pulsers, relays, doors, edges, spinners=None,
                 orbs=None, sockets=None, configurable=None, mailboxes=None):
        # round 12 (3b.5a): spinners = {role: (w, n, rotor4)} at the
        # LEGACY numeric policy (proc-e2.3 per-product trunc0, no sat);
        # orbs = [roles]; sockets = [(spinner, orb)] -- socket edges are
        # NOT wires (different mechanism, LEGAL_PAIRS (socket, pose)).
        # v0.6 (3b.5d-2): the fixture rotor is INITIALIZATION DATA ONLY --
        # after init the current rotor lives in circuit STATE. configurable
        # is the set of spinner roles that ACCEPT runtime rotor writes;
        # None means every spinner is configurable (the dynamic operator is
        # the v0.6 default). "fixed" vs "configurable" is a PERMISSION
        # distinction, not a state-layout distinction: every v0.6 spinner
        # carries its rotor as state regardless.
        # IR v1.1 / Mailbox Slice A (D7): MailboxDecl, the SIXTH built-in
        # role. {mailbox_id: (width, capacity)}. Additive and defaulted, so
        # every pre-v1.1 fixture is byte-for-byte unchanged.
        # D8: a mailbox has NO structural port and NO structural edge --
        # sends address it by id exactly as SetRotor names a spinner. It is
        # therefore absent from the edge/port machinery entirely.
        self.mailboxes = dict(mailboxes or {})
        self.spinners = dict(spinners or {})
        self.orbs = list(orbs or [])
        self.sockets = list(sockets or [])
        self.configurable = (None if configurable is None
                             else set(configurable))
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
                 + sorted(self.spinners) + self.orbs
                 + sorted(self.mailboxes))
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
        for m, spec in self.mailboxes.items():
            _chk(isinstance(spec, tuple) and len(spec) == 2,
                 f"{m}: mailbox spec must be (width, capacity)")
            w_, cap = spec
            _chk(isinstance(w_, int) and 0 < w_ <= 32,
                 f"{m}: mailbox body lane width out of range")
            _chk(isinstance(cap, int) and cap >= 1,
                 f"{m}: mailbox capacity must be >= 1 (D7)")
            _chk(not [e for e in self.edges if m in e],
                 f"{m}: a mailbox has NO structural edge (D8) -- sends "
                 f"address it by id, never by wire")

    def kinds(self):
        k = {r: "pulser" for r in self.pulsers}
        k.update({r: "relay" for r in self.relays})
        k.update({r: "door" for r in self.doors})
        k.update({r: "spinner" for r in self.spinners})
        k.update({r: "orb" for r in self.orbs})
        k.update({r: "mailbox" for r in self.mailboxes})
        return k

    def controller_of(self, orb):
        for (s, o) in self.sockets:
            if o == orb:
                return s
        return ""

    def is_configurable(self, spinner):
        """v0.6 PERMISSION: does this spinner accept runtime rotor writes?
        None-set means all spinners are configurable (dynamic default)."""
        if self.configurable is None:
            return True
        return spinner in self.configurable

    def orb_of(self, spinner):
        for (s, o) in self.sockets:
            if s == spinner:
                return o
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
        ('once', epoch, width). The Fixture oracle lowers at the shared `auto`
        default policy (Phase 3D.1-D); the production shim may pin a profile."""
        return counter_spec_for(self.pulsers[role], "auto", ONEHOT_MAX)

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


# ============================================================ v0.6 (3b.5d-2)
# Rotor-as-state, authoritative sticky fault, config-before-rotation.
# The fixture rotor is INITIALIZATION DATA ONLY; the film and every
# transition read the current rotor from circuit STATE.

def lift_rotor(w_, n_, rotor_proxy):
    """The anchor embedding: exact Q32.32 lift of a proxy rotor. The rotor
    is ASSIGNED, never composed, so a plain rescale (sign-extend then
    <<(32-n)) is exact -- no wide-MAC separator opens on it (contrast the
    POSE, which IS composed and does separate at Q32.32, slice 3b.5c)."""
    def s_of(v):
        return v - (1 << w_) if v >= (1 << (w_ - 1)) else v
    return tuple(s_of(v) << (32 - n_) for v in rotor_proxy)


def model_projection_v6(fx, w, oid, wid_role, t, st):
    """v0.6 model projection. The anchor invariant is REDEFINED: the model
    rotor must equal the exact lift of the circuit rotor STATE (not of a
    fixture constant). Pose/fault are supplied by the authoritative circuit
    state; the model side carries the WHEN/structure oracle. The discrete
    projection is computed directly (the v0.5 model_projection asserts the
    OLD fixture-constant anchor, which a runtime SetRotor legitimately
    breaks)."""
    from binlib import POLICY_FORGE
    ob = w.objs
    for r in fx.pulsers:
        assert ob[oid[r]]["armed"] == 0, "boundary armed nonzero"
    pulsers = []
    for r in sorted(fx.pulsers):
        spec = fx.pulsers[r]
        if spec[0] == "once":
            e = spec[1]
            done = int(ob[oid[r]]["done"])
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
    spinners = []
    for s in sorted(fx.spinners):
        w_, n_, _ = fx.spinners[s]
        sock = fx.orb_of(s)
        perm = "configurable" if fx.is_configurable(s) else "fixed"
        assert tuple(w.objs[oid[s]]["rotor"]) == lift_rotor(
            w_, n_, tuple(st["rotor_" + s])), \
            "model rotor != exact lift of circuit rotor STATE"
        spinners.append((s, POLICY_FORGE, w_, n_,
                         tuple(st["rotor_" + s]), sock, perm))
    orbs = []
    for o in fx.orbs:
        s = fx.controller_of(o)
        w_, n_, _ = fx.spinners[s] if s else (8, 4, None)
        orbs.append((o, POLICY_FORGE, w_, n_, tuple(st["pose_" + o]),
                     s, int(st.get("fault_" + o, 0))))
    return t, pulsers, doors, relays, wires, spinners, orbs
