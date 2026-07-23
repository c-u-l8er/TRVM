"""TRVM Forge — E2 semantic model, v2.2 (equivocation-convergence pass).

Round-six corrections:
  Q1  claim-set model: claims[event_id][payload_digest] = (status, receipt).
      Recognition (unknown / unambiguous / disputed) is DERIVED from the set,
      which is monotone and arrival-order independent. Retransmitting ANY
      previously observed claim is idempotent. Dispute evidence accumulates:
      every conflicting digest is retained, not just the first.
  Q2  acceptance policy is named separately from recognition. Stage One:
      first claim in canonical log order takes effect; within one admission
      batch the canonical order key is (seq, writer, payload_digest), so
      simultaneous conflicting claims resolve by digest, not host order.
      Later conflicting claims are recorded (contesting the receipt, which is
      derivable from |claims| > 1) but never undo the effect. Deterministic
      per ordered log; distributed settlement (defer / authority+digest /
      compensation / sequencer) is Stage Three's protocol problem, deferred
      explicitly.
  Q3  REACT has its own exactly-once machinery: participant delivery is
      counted against the registry, and every generated SIG/SIGW token gets a
      serial that must be consumed exactly once. Fault injection covers both
      phases and generated tokens.
  Q4  rulepack identity is content-addressed over the declarative semantic
      tables (prefab schemas, port types, legal pairs, merges, tariffs,
      numeric policy) plus a procedural-rules version commitment; full
      content addressing of rule bodies arrives with the portable encoding.
  Q5  EV_CONFIG gives tunable objects authoritative event semantics; test
      fixtures no longer mutate state outside step().
  Q6  H() serializes its arguments with structural framing (no concatenation
      ambiguity); events are schema-validated (writer:str, seq:int, known op)
      with malformed events deterministically rejected.
  Q7  the ceiling meters CHARGED SEMANTIC STEPS (events, grafts, erasures,
      removed wires, phase deliveries, reactions); membership scans and
      endpoint validation are uncharged bookkeeping, stated plainly.
      Adjacency-indexed full accounting belongs to the reducer, where the
      ranking function is native.
"""

import copy
import hashlib
import random

NUMERIC_POLICY = "Q32.32-trunc0-quatproxy"
PROC_RULES_VERSION = "proc-e2.3"   # errata: native Once clock (mode/epoch/done)

SHIFT = 32
ONE = 1 << SHIFT


def tmul(a, b):
    p = a * b
    q = abs(p) >> SHIFT
    return q if p >= 0 else -q


def qmul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return (
        tmul(w1, w2) - tmul(x1, x2) - tmul(y1, y2) - tmul(z1, z2),
        tmul(w1, x2) + tmul(x1, w2) + tmul(y1, z2) - tmul(z1, y2),
        tmul(w1, y2) - tmul(x1, z2) + tmul(y1, w2) + tmul(z1, x2),
        tmul(w1, z2) + tmul(x1, y2) - tmul(y1, x2) + tmul(z1, w2),
    )


QID = (ONE, 0, 0, 0)
C45 = int(0.7071067811865476 * ONE)
ROT_Z90 = (C45, 0, 0, C45)
ROT_X90 = (C45, C45, 0, 0)


def qnorm2(q):
    return sum(tmul(c, c) for c in q)


def _ser(x, out):
    if isinstance(x, dict):
        out.append(b"{")
        for k in sorted(x, key=str):
            out.append(str(k).encode()); out.append(b"=")
            _ser(x[k], out); out.append(b";")
        out.append(b"}")
    elif isinstance(x, (list, tuple)):
        out.append(b"[")
        for v in x:
            _ser(v, out); out.append(b",")
        out.append(b"]")
    elif isinstance(x, (set, frozenset)):
        _ser(sorted(x, key=str), out)
    else:
        out.append(repr(x).encode())


def H(*parts):
    out = []
    _ser(list(parts), out)                      # Q6: framed, not concatenated
    return hashlib.sha256(b"".join(out)).hexdigest()


def digest_event(ev):
    return H("payload", dict(ev))


PREFABS = {
    "block":   dict(nodes=3, edges=2, pay=2, parts=0, react=0, mut=0, sig=0, caps=0),
    "ramp":    dict(nodes=4, edges=3, pay=2, parts=0, react=0, mut=0, sig=0, caps=0),
    "orb":     dict(nodes=3, edges=2, pay=2, parts=0, react=0, mut=0, sig=0, caps=0),
    "pipe":    dict(nodes=4, edges=3, pay=2, parts=0, react=0, mut=0, sig=0, caps=0),
    "blender": dict(nodes=4, edges=3, pay=3, parts=0, react=0, mut=0, sig=0, caps=0),
    "spinner": dict(nodes=4, edges=3, pay=3, parts=0, react=1, mut=1, sig=1, caps=1),
    "pulser":  dict(nodes=4, edges=3, pay=2, parts=1, react=1, mut=1, sig=1, caps=0),
    "door":    dict(nodes=4, edges=3, pay=2, parts=1, react=1, mut=2, sig=1, caps=0),
    "relay":   dict(nodes=4, edges=3, pay=2, parts=1, react=1, mut=2, sig=2, caps=0),
}
OUT_PORTS = {"pulser": {"sig_out"}, "relay": {"sig_out"}, "spinner": {"socket"}}
LEGAL_PAIRS = {("sig_out", "sig_in"), ("socket", "pose")}
SIG_MERGE = {"door": "or", "relay": "or", "spinner": "none"}
CONFIGURABLE = {"pulser": {"period": ("int", 1), "phase": ("int", 0),
                           "mode": ("enum", ("periodic", "once")),
                           "epoch": ("int", 0)},
                "spinner": {"rotor": ("quat", None)}}
TARIFF_V03 = dict(T_node=4, T_edge=1, T_payload=1, T_graft=8)
OPS = {"STAMP", "DELETE", "MOVE", "ROTATE", "LINK", "CONFIG"}


def compute_rulepack(prefabs, out_ports, legal_pairs, sig_merge, configurable,
                     tariff, numeric, proc):
    return H("rulepack", prefabs, out_ports, legal_pairs, sig_merge,
             configurable, tariff, numeric, proc)              # Q4


RULEPACK_HASH = compute_rulepack(PREFABS, OUT_PORTS, LEGAL_PAIRS, SIG_MERGE,
                                 CONFIGURABLE, TARIFF_V03, NUMERIC_POLICY,
                                 PROC_RULES_VERSION)
ARTIFACT_ID = {k: H("artifact", k, RULEPACK_HASH) for k in PREFABS}


def tariff_cost(kind, T=None):
    T = T or TARIFF_V03
    p = PREFABS[kind]
    return (T["T_node"] * p["nodes"] + T["T_edge"] * p["edges"]
            + T["T_payload"] * p["pay"] + T.get("T_graft", 0)
            + T.get("T_part", 0) * p["parts"] + T.get("T_react", 0) * p["react"]
            + T.get("T_mut", 0) * p["mut"] + T.get("T_sig", 0) * p["sig"]
            + T.get("T_cap", 0) * p["caps"])


class PhaseFault(AssertionError):
    pass


class StepCeiling(RuntimeError):
    pass


class RandomChooser:
    def __init__(self, rng):
        self.rng = rng
    def __call__(self, n):
        return self.rng.randrange(n)


class ZeroChooser:
    def __call__(self, n):
        return 0


class PathChooser:
    def __init__(self, path=None):
        self.path = list(path or [])
        self.arities = []
        self.pos = 0
    def __call__(self, n):
        if n <= 1:
            return 0
        if self.pos < len(self.path):
            c = self.path[self.pos]
        else:
            self.path.append(0); c = 0
        if self.pos < len(self.arities):
            self.arities[self.pos] = n
        else:
            self.arities.append(n)
        self.pos += 1
        return c
    def advance(self):
        i = len(self.path) - 1
        while i >= 0:
            if self.path[i] + 1 < self.arities[i]:
                self.path[i] += 1
                del self.path[i + 1:]; del self.arities[i + 1:]
                return True
            i -= 1
        return False


def valid_event(ev):
    return (isinstance(ev, dict) and isinstance(ev.get("seq"), int)
            and not isinstance(ev.get("seq"), bool)
            and isinstance(ev.get("writer", "local"), str)
            and ev.get("op") in OPS)


def order_key(ev):
    """Q2: canonical order = (seq, writer, payload digest). Stage three:
    <lamport, writer, seq, digest>."""
    return (ev["seq"], ev.get("writer", "local"), digest_event(ev))


class World:
    TRANSIENT = {"last_steps"}

    def __init__(self, cap=1000, lineage="map0", ceiling=100_000):
        self.lineage = lineage
        self.cap, self.P, self.N = cap, 0, 0
        self.handles = {}
        self.objs = {}
        self.wires = {}
        self.registry = {}
        self.claims = {}        # event_id -> {digest: (status, receipt)} (Q1)
        self.rejects = []       # (seq|"malformed", writer|digest, reason)
        self.t = 0
        self.ceiling = ceiling
        self.last_steps = 0

    # ---- recognition is derived, never stored (Q1)
    def recognition(self, eid):
        c = self.claims.get(eid)
        if not c:
            return "unknown"
        return "unambiguous" if len(c) == 1 else "disputed"

    def state_dict(self):
        d = {k: v for k, v in vars(self).items() if k not in self.TRANSIENT}
        d["rulepack_hash"] = RULEPACK_HASH
        d["numeric"] = NUMERIC_POLICY
        return d

    def canonical_hash(self):
        out = []
        _ser(self.state_dict(), out)
        return hashlib.sha256(b"".join(out)).hexdigest()

    def charge(self, n=1):
        self.last_steps += n
        if self.last_steps > self.ceiling:
            raise StepCeiling("charged-semantic-step ceiling breached")

    def _scan_participants(self):        # uncharged bookkeeping (Q7)
        exp = {wid: "wire" for wid in self.wires}
        for oid, o in self.objs.items():
            role = {"pulser": "clk", "door": "gate", "relay": "relay"}.get(o["kind"])
            if role:
                exp[oid] = role
        return exp

    def _graft(self, kind, event_id):
        iid = H("instance", self.lineage, event_id, ARTIFACT_ID[kind])
        self.handles[iid] = "live"
        o = dict(kind=kind, pose=list((*QID, 0, 0, 0)), cost=tariff_cost(kind))
        if kind == "pulser":
            o.update(period=3, phase=0, armed=0, mode="periodic", epoch=0,
                     done=0); self.registry[iid] = "clk"
        if kind == "door":
            o.update(open=0, next_open=0); self.registry[iid] = "gate"
        if kind == "relay":
            o.update(cur_out=0, next_out=0); self.registry[iid] = "relay"
        if kind == "spinner":
            o.update(rotor=ROT_Z90, socket="")
        self.objs[iid] = o
        self.charge(PREFABS[kind]["nodes"])
        return iid

    def _admit_one(self, ev):
        seq = ev["seq"]
        writer = ev.get("writer", "local")
        eid = H("event", writer, seq)
        dg = digest_event(ev)
        c = self.claims.get(eid)
        if c is not None:
            if dg in c:
                return c[dg][1]              # Q1: ANY observed claim idempotent
            c[dg] = ("conflict", ("conflict",))   # Q1: evidence accumulates
            return ("conflict",)             # Q2: never undoes the effect
        receipt = self._execute(ev, ev["op"], seq, writer, eid)
        self.claims[eid] = {dg: ("accepted", receipt)}
        return receipt

    def _execute(self, ev, op, seq, writer, eid):
        if op == "STAMP":
            kind = ev["kind"]; cost = tariff_cost(kind)
            if self.P - self.N + cost <= self.cap:
                self.P += cost
                iid = self._graft(kind, eid)
                if "pose" in ev:
                    self.objs[iid]["pose"] = list(ev["pose"])
                return ("placed", iid)
            self.rejects.append((seq, writer, "budget"))
            return ("rejected",)
        tid = ev.get("target", "")
        st = self.handles.get(tid)
        if st != "live":
            self.rejects.append((seq, writer, "dangling" if st else "unknown"))
            return ("rejected",)
        return self._execute_live(ev, op, seq, writer, tid, eid)

    def _execute_live(self, ev, op, seq, writer, tid, eid):
        o = self.objs[tid]
        if op == "DELETE":
            for wid in [w for w, ww in self.wires.items()
                        if tid in (ww["dst_id"], ww["src_id"])]:
                self.wires.pop(wid); self.registry.pop(wid, None)
                self.charge()                              # Q7
            tgt = o.get("socket", "")
            if tgt and tgt in self.objs:
                self.objs[tgt]["controller"] = ""
            for other in self.objs.values():
                if other.get("controller") == tid:
                    other["controller"] = ""
                if other.get("socket") == tid:
                    other["socket"] = ""
            self.registry.pop(tid, None)
            self.N += o["cost"]
            self.charge(PREFABS[o["kind"]]["nodes"])
            self.objs.pop(tid)
            self.handles[tid] = "tombstone"
            return ("deleted", tid)
        if op == "MOVE":
            o["pose"][4:7] = ev["dpos"]; return ("moved", tid)
        if op == "ROTATE":
            o["pose"][0:4] = qmul(ev["rotor"], tuple(o["pose"][0:4]))
            return ("rotated", tid)
        if op == "CONFIG":                                  # Q5
            field, value = ev.get("field"), ev.get("value")
            spec = CONFIGURABLE.get(o["kind"], {}).get(field)
            ok = spec is not None and (
                (spec[0] == "int" and isinstance(value, int)
                 and not isinstance(value, bool)
                 and (spec[1] is None or value >= spec[1]))
                or (spec[0] == "enum" and value in spec[1])
                or (spec[0] == "quat" and isinstance(value, (tuple, list))
                    and len(value) == 4
                    and all(isinstance(v, int) for v in value)))
            if not ok:
                self.rejects.append((seq, writer, "config"))
                return ("rejected",)
            o[field] = tuple(value) if spec[0] == "quat" else value
            return ("configured", tid, field)
        if op == "LINK":
            dst_id = ev["dst"]
            sp, dp = ev.get("src_port", ""), ev.get("dst_port", "")
            if self.handles.get(dst_id) != "live":
                self.rejects.append((seq, writer, "dangling")); return ("rejected",)
            if sp not in OUT_PORTS.get(o["kind"], set()):
                self.rejects.append((seq, writer, "nosrcport")); return ("rejected",)
            if (sp, dp) not in LEGAL_PAIRS:
                self.rejects.append((seq, writer, "type")); return ("rejected",)
            d = self.objs[dst_id]
            if dp == "sig_in":
                merge = SIG_MERGE.get(d["kind"])
                if merge is None:
                    self.rejects.append((seq, writer, "notyped")); return ("rejected",)
                if merge == "none" and any(
                        w["dst_id"] == dst_id and w["dst_port"] == "sig_in"
                        for w in self.wires.values()):
                    self.rejects.append((seq, writer, "fanin")); return ("rejected",)
                wid = H("wire", self.lineage, eid)
                self.wires[wid] = dict(src_id=tid, dst_id=dst_id,
                                       dst_port="sig_in", cur=0, nxt=0)
                self.registry[wid] = "wire"
                return ("linked", wid)
            if dp == "pose":
                if d.get("controller", ""):
                    self.rejects.append((seq, writer, "controlled")); return ("rejected",)
                o["socket"] = dst_id; d["controller"] = tid
                return ("socketed", dst_id)
        return ("rejected",)

    def _deliver(self, dst_id, port):
        if self.handles.get(dst_id) != "live":
            return
        d = self.objs[dst_id]; k = d["kind"]
        if k == "door":
            d["next_open"] = 1
        elif k == "relay":
            d["next_out"] = 1
        elif k == "spinner":
            tgt = d.get("socket", "")
            if tgt and self.handles.get(tgt) == "live":
                p = self.objs[tgt]["pose"]
                p[0:4] = qmul(d["rotor"], tuple(p[0:4]))

    def _distribute(self, phase, chooser, fault, apply_fn):
        tokens = sorted(self.registry)
        if fault == f"{phase}-dup" and tokens:
            tokens.append(tokens[0])
        if fault == f"{phase}-omit" and tokens:
            tokens.pop()
        if fault == f"{phase}-stale":
            tokens.append(H("stale", phase))
        delivered = {}
        order = []
        while tokens:
            i = chooser(len(tokens))
            pid = tokens.pop(i)
            delivered[pid] = delivered.get(pid, 0) + 1
            order.append(pid)
            self.charge()
        if set(delivered) != set(self.registry) or \
           any(v != 1 for v in delivered.values()):
            raise PhaseFault(f"{phase}: participant exactly-once violated")
        return order

    def step(self, events, chooser, fault=None, drop_registry=None):
        self.last_steps = 0
        good = [e for e in events if valid_event(e)]
        bad = [e for e in events if not valid_event(e)]
        for dg in sorted(digest_event(e) for e in bad):        # Q6
            self.rejects.append(("malformed", dg, "schema"))
            self.charge()
        for ev in sorted(good, key=order_key):                 # Q2
            self._admit_one(ev)
            self.charge()
        if drop_registry:
            self.registry.pop(drop_registry, None)
        exp = self._scan_participants()
        if exp != self.registry:
            raise PhaseFault("registry membership mismatch")

        def commit(pid, role):
            if role == "wire":
                w = self.wires[pid]; w["cur"], w["nxt"] = w["nxt"], 0
            elif role == "gate":
                o = self.objs[pid]; o["open"], o["next_open"] = o["next_open"], 0
            elif role == "clk":
                o = self.objs[pid]
                if o["mode"] == "once":
                    # native Once (proc-e2.3 errata): fires iff the
                    # commit epoch equals the target; done latches at
                    # first commit at-or-after the target, so a config
                    # admitted late latches WITHOUT firing, and no
                    # second firing exists at any t (no sentinel).
                    if not o["done"] and self.t >= o["epoch"]:
                        o["armed"] = 1 if self.t == o["epoch"] else 0
                        o["done"] = 1
                    else:
                        o["armed"] = 0
                else:
                    o["armed"] = 1 if (self.t % o["period"]) == o["phase"] else 0
            elif role == "relay":
                o = self.objs[pid]; o["cur_out"], o["next_out"] = o["next_out"], 0

        for pid in self._distribute("commit", chooser, fault, lambda *a: None):
            pass
        # apply commits in the drawn order (order-free; disjoint state)
        for pid in sorted(self.registry):
            commit(pid, self.registry[pid])

        # REACT: participant delivery counted; generated tokens serialized (Q3)
        react = [("REACT", pid, role) for pid, role in sorted(self.registry.items())]
        if fault == "react-dup" and react:
            react.append(react[0])
        if fault == "react-omit" and react:
            react.pop()
        if fault == "react-stale":
            react.append(("REACT", H("stale", "react"), "wire"))
        delivered_r = {}
        produced, consumed = {}, {}
        serial = [0]

        def emit(tok):
            serial[0] += 1
            s = serial[0]
            produced[s] = True
            full = tok + (s,)
            if fault == "sig-omit" and s == 1:
                return                                        # produced, dropped
            tokens.append(full)
            if fault == "sig-dup" and s == 1:
                tokens.append(full)

        tokens = react
        while tokens:
            i = chooser(len(tokens))
            tok = tokens.pop(i)
            self.charge()
            if tok[0] == "REACT":
                pid, role = tok[1], tok[2]
                delivered_r[pid] = delivered_r.get(pid, 0) + 1
                if role == "wire":
                    w = self.wires.get(pid)
                    if w and w["cur"]:
                        emit(("SIG", w["dst_id"], w["dst_port"]))
                elif role in ("clk", "relay"):
                    o = self.objs.get(pid)
                    hot = o and (o["armed"] if role == "clk" else o["cur_out"])
                    if hot:
                        if role == "clk":
                            o["armed"] = 0
                        for wid in sorted(self.wires):
                            if self.wires[wid]["src_id"] == pid:
                                emit(("SIGW", wid))
            elif tok[0] == "SIGW":
                consumed[tok[2]] = consumed.get(tok[2], 0) + 1
                self.wires[tok[1]]["nxt"] = 1
            elif tok[0] == "SIG":
                consumed[tok[3]] = consumed.get(tok[3], 0) + 1
                self._deliver(tok[1], tok[2])
        if set(delivered_r) != set(self.registry) or \
           any(v != 1 for v in delivered_r.values()):
            raise PhaseFault("react: participant exactly-once violated")
        if set(consumed) != set(produced) or any(v != 1 for v in consumed.values()):
            raise PhaseFault("react: generated-token exactly-once violated")
        self.t += 1
        return self.canonical_hash()
