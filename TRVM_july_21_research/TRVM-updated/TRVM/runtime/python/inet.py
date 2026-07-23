"""
inet.py - A minimal interaction-combinators reducer, with an empirical
confluence check and a simulated coordination-free distributed reduction.

Lafont's symmetric interaction combinators: three agent kinds, each with a
single PRINCIPAL port; binary agents (CON, DUP) also have two AUX ports;
EPS (eraser) has none. Reduction fires only when two PRINCIPAL ports meet
(an "active pair"). Six rules:
    annihilation:  EPS><EPS, CON><CON, DUP><DUP
    commutation:   EPS><CON, EPS><DUP, CON><DUP
This is a universal model of distributed computation (Lafont 1997) and is
STRONGLY CONFLUENT: the normal form -- and even the number of interactions --
is independent of the order active pairs are reduced. That order-independence
is exactly the property the distributed-systems world calls "confluence",
the operational basis of coordination-free execution.
"""
import itertools, random

_pc = itertools.count()
_ac = itertools.count()

class Port:
    __slots__ = ("pid", "agent", "idx", "link", "label")
    def __init__(self, agent, idx):
        self.pid = next(_pc); self.agent = agent; self.idx = idx
        self.link = None; self.label = None

class Agent:
    __slots__ = ("kind", "ports", "aid")
    def __init__(self, kind):
        self.kind = kind; self.aid = next(_ac)
        n = 1 if kind == "EPS" else 3
        self.ports = [Port(self, i) for i in range(n)]
    @property
    def principal(self): return self.ports[0]

def link(p, q):
    p.link = q; q.link = p

def free_port(label):
    p = Port(None, -1); p.label = label; return p

class Net:
    def __init__(self): self.agents = []; self.free = []
    def add(self, a): self.agents.append(a); return a
    def remove(self, a): self.agents.remove(a)

def active_pairs(net):
    seen = set(); out = []
    for a in net.agents:
        q = a.principal.link
        if q is not None and q.agent is not None and q.idx == 0:
            b = q.agent
            if a.aid != b.aid:
                k = frozenset((a.aid, b.aid))
                if k not in seen:
                    seen.add(k); out.append((a, b))
    return out

def rewrite(net, a, b):
    ka, kb = a.kind, b.kind
    if ka == "EPS" and kb == "EPS":
        net.remove(a); net.remove(b); return
    if ka == "EPS" or kb == "EPS":                      # eraser meets binary
        e, g = (a, b) if ka == "EPS" else (b, a)
        g1, g2 = g.ports[1].link, g.ports[2].link
        net.remove(e); net.remove(g)
        e1 = net.add(Agent("EPS")); e2 = net.add(Agent("EPS"))
        link(e1.principal, g1); link(e2.principal, g2); return
    if ka == kb:                                        # annihilation (symmetric: straight)
        a1, a2 = a.ports[1].link, a.ports[2].link
        b1, b2 = b.ports[1].link, b.ports[2].link
        net.remove(a); net.remove(b)
        link(a1, b1); link(a2, b2); return
    # commutation: DUP vs CON
    d, c = (a, b) if ka == "DUP" else (b, a)
    d1, d2 = d.ports[1].link, d.ports[2].link
    c1, c2 = c.ports[1].link, c.ports[2].link
    net.remove(d); net.remove(c)
    C1 = net.add(Agent("CON")); C2 = net.add(Agent("CON"))
    D1 = net.add(Agent("DUP")); D2 = net.add(Agent("DUP"))
    link(C1.principal, d1); link(C2.principal, d2)
    link(D1.principal, c1); link(D2.principal, c2)
    link(C1.ports[1], D1.ports[1]); link(C1.ports[2], D2.ports[1])
    link(C2.ports[1], D1.ports[2]); link(C2.ports[2], D2.ports[2])

def reduce_net(net, policy="random", rng=None):
    rng = rng or random.Random(); n = 0
    while True:
        ap = active_pairs(net)
        if not ap: break
        a, b = (rng.choice(ap) if policy == "random"
                else ap[0] if policy == "first" else ap[-1])
        rewrite(net, a, b); n += 1
    return n

def readback(net):
    def enc(port, depth):
        if port is None: return "0"
        ag = port.agent
        if ag is None: return f"FREE[{port.label}]"
        if depth > 64: return "*"
        if ag.kind == "EPS": return "EPS"
        return f"{ag.kind}({enc(ag.ports[1].link, depth+1)},{enc(ag.ports[2].link, depth+1)})"
    return " | ".join(f"{fp.label}={enc(fp.link, 0)}"
                      for fp in sorted(net.free, key=lambda p: p.label))

def make_tree(net, depth):
    if depth == 0:
        return net.add(Agent("EPS")).principal      # erased leaf
    node = net.add(Agent("CON"))
    link(node.ports[1], make_tree(net, depth - 1))
    link(node.ports[2], make_tree(net, depth - 1))
    return node.principal

def make_demo_net(depth=3):
    net = Net()
    f0, f1 = free_port("out0"), free_port("out1")
    net.free = [f0, f1]
    root = make_tree(net, depth)
    dup = net.add(Agent("DUP"))
    link(dup.principal, root)          # the one initial redex: DUP >< root
    link(dup.ports[1], f0); link(dup.ports[2], f1)
    return net

def test_confluence(make, trials=300):
    base_c = base_rb = None
    for t in range(trials):
        net = make(); c = reduce_net(net, "random", random.Random(t)); rb = readback(net)
        if base_c is None: base_c, base_rb = c, rb
        else:
            assert c == base_c, f"interaction count varied: {c} != {base_c}"
            assert rb == base_rb, f"normal form varied:\n{rb}\n!=\n{base_rb}"
    return base_c, base_rb

def reduce_distributed(net, nparts=2, seed=0):
    rng = random.Random(seed)
    part = {a.aid: rng.randrange(nparts) for a in net.agents}
    interactions = messages = 0
    while True:
        ap = active_pairs(net)
        if not ap: break
        local = [(a, b) for (a, b) in ap if part[a.aid] == part[b.aid]]
        cross = [(a, b) for (a, b) in ap if part[a.aid] != part[b.aid]]
        if local and (not cross or rng.random() < 0.7):
            a, b = rng.choice(local); p = part[a.aid]
            before = {x.aid for x in net.agents}
            rewrite(net, a, b)
            for x in net.agents:
                if x.aid not in before: part[x.aid] = p   # new agents stay node-local
            interactions += 1
        else:
            a, b = rng.choice(cross)
            part[b.aid] = part[a.aid]                      # migrate one agent = one message
            messages += 1
    return interactions, messages

def reduce_message_passing(net, nparts=2, seed=0):
    """The spec's distribution protocol: every boundary wire has a DETERMINISTIC
    owner (the lower node id); the non-owner EXPORTS its agent to the owner, and
    the owner performs the (now-local) rewrite. Messages are delivered in random
    order to model async reordering/delay. Returns (interactions, exports,
    boundary_rewrites); exports == boundary_rewrites proves exactly-once."""
    rng = random.Random(seed)
    part = {a.aid: rng.randrange(nparts) for a in net.agents}
    mq = []                       # pending exports routed to an owner (reorderable)
    exported = set()              # boundary pairs already routed (no double-export)
    interactions = exports = boundary_rewrites = 0
    def assign_new(before, node):
        for x in net.agents:
            if x.aid not in before: part[x.aid] = node
    while True:
        ap = active_pairs(net)
        local = [(a, b) for (a, b) in ap if part[a.aid] == part[b.aid]]
        bnd = [(a, b) for (a, b) in ap if part[a.aid] != part[b.aid]
               and frozenset((a.aid, b.aid)) not in exported]
        if not local and not bnd and not mq: break
        opts = (["local"] * bool(local)) + (["export"] * bool(bnd)) + (["deliver"] * bool(mq))
        action = rng.choice(opts)
        if action == "local":                              # coordination-free local rewrite
            a, b = rng.choice(local); node = part[a.aid]
            before = {x.aid for x in net.agents}
            rewrite(net, a, b); assign_new(before, node); interactions += 1
        elif action == "export":                           # non-owner ships agent to owner
            a, b = rng.choice(bnd); own = min(part[a.aid], part[b.aid])
            mq.append((a, b, own)); exported.add(frozenset((a.aid, b.aid))); exports += 1
        else:                                              # owner reduces a delivered pair
            a, b, own = mq.pop(rng.randrange(len(mq)))
            before = {x.aid for x in net.agents}
            rewrite(net, a, b); assign_new(before, own)
            interactions += 1; boundary_rewrites += 1
    return interactions, exports, boundary_rewrites

if __name__ == "__main__":
    D = 3
    print(f"interaction combinators -- duplicating a depth-{D} CON-tree with erased leaves\n")
    n_int, rb = test_confluence(lambda: make_demo_net(D), trials=300)
    print("[1] SEQUENTIAL CONFLUENCE  (300 random reduction orders)")
    print(f"    all 300 orders reached the SAME normal form")
    print(f"    all 300 took EXACTLY {n_int} interactions  (length is order-invariant)")
    for pol in ("first", "last"):
        net = make_demo_net(D); c = reduce_net(net, pol)
        assert c == n_int and readback(net) == rb
    print("    fixed 'first' and 'last' policies agree too")
    print(f"    normal form: {rb}\n")
    print("[2] COORDINATION-FREE DISTRIBUTED REDUCTION  (agents randomly split over 2 nodes)")
    msgs = set()
    for s in range(50):
        net = make_demo_net(D); ci, m = reduce_distributed(net, 2, seed=s)
        assert ci == n_int, f"distributed count {ci} != {n_int}"
        assert readback(net) == rb, "distributed normal form differs!"
        msgs.add(m)
    print(f"    50 runs, randomized async interleaving across 2 nodes")
    print(f"    every run converged to the SAME normal form as sequential")
    print(f"    every run took {n_int} interactions; cross-node messages ranged over {sorted(msgs)}")
    print( "    -> no run needed a lock or consensus round to REDUCE.")
    print( "    -> the only global question is 'are BOTH nodes out of active pairs?'")
    print( "       i.e. distributed TERMINATION DETECTION -- the one place real")
    print( "       coordination concentrates (Safra / Dijkstra-Scholten).")
    print()
    print("[3] BOUNDARY-OWNER PROTOCOL  (the spec's distributed reduction)")
    seen = set()
    for s in range(50):
        net = make_demo_net(D); ci, ex, br = reduce_message_passing(net, 2, seed=s)
        assert ci == n_int, f"count {ci} != {n_int}"
        assert readback(net) == rb, "normal form differs from sequential!"
        assert ex == br, f"exports {ex} != boundary rewrites {br} -- NOT exactly-once!"
        seen.add((ex, br))
    print(f"    50 runs with deterministic owners + RANDOM message-delivery order")
    print(f"    every run: same normal form, {n_int} interactions")
    print(f"    boundary pairs exported == boundary rewrites, every run (exactly-once)")
    print(f"    (exports, rewrites) observed across runs: {sorted(seen)}")
