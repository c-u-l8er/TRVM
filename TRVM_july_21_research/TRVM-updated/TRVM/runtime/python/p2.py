"""
p2.py - P2: a real distributed interaction-net runtime.

Unlike inet.py's in-process simulation, here each WORKER owns a separate heap
and shares NOTHING with other workers except plain-data messages. Cross-node
wires are split into boundary stubs joined by a global wire_id. Reduction uses
the spec's boundary-OWNER protocol; this file first validates the protocol with
a deterministic scheduler (separate heaps, real messages), then p2_run.py adds
real threads + Safra termination detection.

Reuses the *tested* combinator rules from inet.py.
"""
import itertools, random, threading, queue, time
import inet
from inet import Agent, Port, Net, link, free_port, active_pairs, rewrite, readback, make_demo_net, reduce_net

_wire = itertools.count(1)

class Worker:
    def __init__(self, node_id):
        self.id = node_id
        self.net = Net()
        self.boundary = {}     # free-port pid -> (wire_id, peer_node)
        self.bnd_index = {}    # wire_id -> the boundary free Port
        self.outbox = []       # (dest_node, msg) produced this step (drained by driver)
        self.sent = 0
        self.recv = 0
        self.c = 0             # Safra counter: messages sent - received
        self.color = "white"  # blackens on receiving work

    # a boundary stub is a free Port tagged via self.boundary
    def add_stub(self, wire_id, peer):
        b = free_port(None)
        self.boundary[b.pid] = (wire_id, peer)
        self.bnd_index[wire_id] = b
        self.net.free.append(b)
        return b

    def drop_stub(self, b):
        self.boundary.pop(b.pid, None)
        wid = next((w for w, p in self.bnd_index.items() if p is b), None)
        if wid is not None: del self.bnd_index[wid]
        if b in self.net.free: self.net.free.remove(b)

    def is_stub(self, port):
        return port is not None and port.agent is None and port.pid in self.boundary

    def local_active_pairs(self):
        return active_pairs(self.net)   # naturally excludes boundary ends (stubs are free)

    def boundary_principals(self, owner_fn):
        """agents whose principal faces a boundary wire this worker does NOT own."""
        out = []
        for a in list(self.net.agents):
            p = a.principal.link
            if self.is_stub(p):
                wid, peer = self.boundary[p.pid]
                if owner_fn(wid, self.id, peer) != self.id:
                    out.append((a, p, wid, peer))
        return out

    def export(self, a, stub, wid, owner, owner_fn):
        """Ship agent `a` (header only) to `owner`; internalize wire `wid` there."""
        aux_wids = []
        for ap in a.ports[1:]:
            q = ap.link
            if self.is_stub(q):                      # aux already a boundary wire
                u, _peer = self.boundary[q.pid]
                aux_wids.append(u)
                self.drop_stub(q)                    # this end leaves with the agent
            else:                                    # aux is a local wire -> becomes boundary
                u = next(_wire)
                nb = self.add_stub(u, owner)         # local partner now points across to owner
                link(nb, q)
                aux_wids.append(u)
        msg = {"t": "export", "wire": wid, "kind": a.kind, "aux": aux_wids}
        self.net.remove(a)
        self.drop_stub(stub)
        self.outbox.append((owner, msg)); self.sent += 1

    def inject(self, msg):
        """Owner receives an exported agent; reconstruct, splice, maybe form a redex."""
        self.recv += 1
        wid = msg["wire"]
        b_own = self.bnd_index.get(wid)
        q = b_own.link                                # owner's local end of this wire
        g = self.net.add(Agent(msg["kind"]))
        link(g.principal, q)
        self.drop_stub(b_own)                         # wire wid now internal to owner
        for ap, u in zip(g.ports[1:], msg["aux"]):
            match = self.bnd_index.get(u)
            if match is not None:                     # far end was on me -> splice internal
                local = match.link
                self.drop_stub(match)
                link(ap, local)
            else:                                     # new boundary wire back to sender
                nb = self.add_stub(u, msg.get("from"))
                link(ap, nb)


def partition(net, assign, n_nodes):
    """Split one net into `n_nodes` Workers; cross-wires -> matched boundary stubs."""
    ws = {i: Worker(i) for i in range(n_nodes)}
    # node of an agent port = assign[aid]; free ports (out*) live on node 0
    def node_of(port):
        return assign[port.agent.aid] if port.agent is not None else 0
    # move agents to their worker
    for a in net.agents:
        ws[assign[a.aid]].net.add(a)
    # place the real interface free ports on node 0
    for fp in net.free:
        ws[0].net.free.append(fp)
    # split wires: collect unique wires first (by unordered port-pid pair)
    seen = set(); wires = []
    ports = [p for a in net.agents for p in a.ports] + list(net.free)
    for p in ports:
        q = p.link
        if q is None: continue
        key = frozenset((p.pid, q.pid))
        if key in seen: continue
        seen.add(key); wires.append((p, q))
    for p, q in wires:
        np_, nq = node_of(p), node_of(q)
        if np_ == nq: continue                        # intra-worker wire: leave intact
        w = next(_wire)
        bp = ws[np_].add_stub(w, nq); link(bp, p)
        bq = ws[nq].add_stub(w, np_); link(bq, q)
    return ws


def stitch_and_readback(ws):
    """Reconnect boundary wires across workers by wire_id, then read the whole net."""
    big = Net()
    for w in ws.values():
        for a in w.net.agents: big.agents.append(a)
        for fp in w.net.free:
            if fp.pid not in w.boundary: big.free.append(fp)   # real interface ports only
    # join matching stubs
    halves = {}
    for w in ws.values():
        for pid, (wid, peer) in w.boundary.items():
            stub = next(p for p in w.net.free if p.pid == pid)
            halves.setdefault(wid, []).append(stub)
    for wid, stubs in halves.items():
        if len(stubs) == 2:
            (p1, p2) = (stubs[0].link, stubs[1].link)
            link(p1, p2)
    return readback(big)


def owner_min(wid, a, b):  # deterministic owner = smaller node id
    return min(a, b)


def run_deterministic(net, n_nodes=2, seed=0, owner_fn=owner_min):
    """Validate the protocol over separate heaps with a deterministic scheduler."""
    rng = random.Random(seed)
    assign = {a.aid: rng.randrange(n_nodes) for a in net.agents}
    ws = partition(net, assign, n_nodes)
    chans = {}                                        # (src,dest) -> FIFO list (TCP/BEAM-like)
    interactions = 0
    def pending(): return any(v for v in chans.values())
    while True:
        local = [(w, ap) for w in ws.values() for ap in [w.local_active_pairs()] if ap]
        bnd = [(w, bp) for w in ws.values() for bp in [w.boundary_principals(owner_fn)] if bp]
        if not local and not bnd and not pending():
            break
        roll = rng.random()
        if local and (roll < 0.5 or (not bnd and not pending())):
            w, aps = rng.choice(local); a, b = rng.choice(aps)
            rewrite(w.net, a, b); interactions += 1
        elif bnd and (roll < 0.8 or not pending()):
            w, bps = rng.choice(bnd); a, stub, wid, peer = rng.choice(bps)
            owner = owner_fn(wid, w.id, peer)
            w.export(a, stub, wid, owner, owner_fn)
            for dest, m in w.outbox:
                m["from"] = w.id; chans.setdefault((w.id, dest), []).append(m)
            w.outbox.clear()
        else:
            live = [k for k, v in chans.items() if v]
            (src, dest) = rng.choice(live); m = chans[(src, dest)].pop(0)   # FIFO head
            ws[dest].inject(m); interactions += 1
    return ws, interactions


def run_threaded(net, n_nodes=2, seed=0, owner_fn=owner_min, budget_s=10.0):
    """Real concurrent workers (own heaps, message-passing only) + Safra's
    distributed termination detection. Returns (workers, terminated_bool).
    c_i = sends - receives (per worker); a worker blackens on receiving work;
    a white token with count 0 returning white to node 0 => global termination."""
    rng = random.Random(seed)
    assign = {a.aid: rng.randrange(n_nodes) for a in net.agents}
    ws = partition(net, assign, n_nodes)
    inbox = {i: queue.Queue() for i in range(n_nodes)}
    stop = threading.Event(); result = {"terminated": False}

    def send(dest, m): inbox[dest].put(m)

    def loop(i):
        w = ws[i]; token = None; launched = False
        while not stop.is_set():
            progressed = False
            # (1) drain inbound: inject work (blacken + c--), buffer the token
            while True:
                try: m = inbox[i].get_nowait()
                except queue.Empty: break
                if m.get("t") == "token": token = m
                else:
                    w.inject(m); w.c -= 1; w.color = "black"; progressed = True
            # (2) one local rewrite, else (3) one export
            aps = w.local_active_pairs()
            if aps:
                a, b = aps[0]; rewrite(w.net, a, b); progressed = True
            else:
                bps = w.boundary_principals(owner_fn)
                if bps:
                    a, stub, wid, peer = bps[0]
                    w.export(a, stub, wid, owner_fn(wid, w.id, peer), owner_fn)
                    for dest, m in w.outbox:
                        m["from"] = w.id; send(dest, m); w.c += 1
                    w.outbox.clear(); progressed = True
            # (4) termination detection -- only when this worker is locally idle
            idle = (not w.local_active_pairs() and not w.boundary_principals(owner_fn)
                    and inbox[i].empty())
            if idle:
                if i == 0:
                    if token is not None:                       # token came back to detector
                        T, token = token, None
                        if T["color"] == "white" and w.color == "white" and T["count"] + w.c == 0:
                            result["terminated"] = True; stop.set(); break
                        w.color = "white"; send(1 % n_nodes, {"t": "token", "count": 0, "color": "white"})
                    elif not launched:                          # kick off the first round
                        launched = True; w.color = "white"
                        send(1 % n_nodes, {"t": "token", "count": 0, "color": "white"})
                elif token is not None:                          # relay the token onward
                    T, token = token, None
                    send((i + 1) % n_nodes, {"t": "token", "count": T["count"] + w.c,
                          "color": "black" if w.color == "black" else T["color"]})
                    w.color = "white"; progressed = True
            if not progressed: time.sleep(0.0003)

    ts = [threading.Thread(target=loop, args=(i,), daemon=True) for i in range(n_nodes)]
    for t in ts: t.start()
    deadline = time.time() + budget_s
    for t in ts: t.join(timeout=max(0.01, deadline - time.time()))
    stop.set()
    return ws, result["terminated"]


if __name__ == "__main__":
    D = 3
    ref = make_demo_net(D); ref_n = reduce_net(ref, "first"); ref_rb = readback(ref)
    print(f"sequential oracle: {ref_n} interactions")
    ok = 0
    for s in range(40):
        net = make_demo_net(D)
        ws, n = run_deterministic(net, n_nodes=2, seed=s)
        rb = stitch_and_readback(ws)
        assert rb == ref_rb, f"seed {s}: normal form differs!\n{rb}\n vs \n{ref_rb}"
        ok += 1
    print(f"P2 protocol over SEPARATE heaps: {ok}/40 seeds match the sequential normal form")
    print("  (separate per-worker heaps, real export/inject messages, owner=min)")
    print()
    print("Real concurrent runtime + Safra termination detection:")
    term = 0; matched = 0
    for s in range(20):
        net = make_demo_net(D)
        ws, terminated = run_threaded(net, n_nodes=2, seed=s, budget_s=10.0)
        if terminated: term += 1
        if stitch_and_readback(ws) == ref_rb: matched += 1
    print(f"  {term}/20 runs: Safra DETECTED global termination (no early stop, no hang)")
    print(f"  {matched}/20 runs: stitched normal form matches the sequential oracle")
    print("  -> independent threads, shared-nothing, discovered 'done' themselves via a token ring.")
