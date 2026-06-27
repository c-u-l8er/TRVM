"""
linet.py - our reduction net, upgraded with LABELED duplicators (the mechanism
HVM uses to get sharing, which Lafont's plain symmetric combinators lack).

A duplicator now carries a label. The rule change is the whole point:
    DUP[a] >< DUP[a]   (same label)      -> ANNIHILATE   (a matched fan pair: the
                                            duplication completes -> shared)
    DUP[a] >< DUP[b]   (different label)  -> COMMUTE      (unrelated fans pass
                                            through -> correct duplication)
    CON   >< DUP[a]                       -> COMMUTE
    CON   >< CON                          -> ANNIHILATE
    EPS   >< X                            -> ERASE
Plain combinators have one unlabeled DUP, so two DUPs ALWAYS annihilate -- which
silently collapses nested duplications (wrong) and never shares. Labels fix both.
"""
import itertools, random
_ac = itertools.count()

class Agent:
    __slots__ = ("kind", "label", "ports", "aid")
    def __init__(self, kind, label=None):
        self.kind, self.label, self.aid = kind, label, next(_ac)
        self.ports = [Port(self, i) for i in range(1 if kind == "EPS" else 3)]
    @property
    def principal(self): return self.ports[0]

class Port:
    __slots__ = ("agent", "idx", "link", "flabel")
    def __init__(self, agent, idx):
        self.agent, self.idx, self.link, self.flabel = agent, idx, None, None

def link(p, q): p.link = q; q.link = p
def free_port(lbl):
    p = Port(None, -1); p.flabel = lbl; return p

class Net:
    def __init__(self): self.agents, self.free = [], []
    def add(self, a): self.agents.append(a); return a
    def remove(self, a): self.agents.remove(a)

def same(a, b): return a.kind == b.kind and a.label == b.label

def active_pairs(net):
    seen, out = set(), []
    for a in net.agents:
        q = a.principal.link
        if q is not None and q.agent is not None and q.idx == 0 and a.aid != q.agent.aid:
            k = frozenset((a.aid, q.agent.aid))
            if k not in seen: seen.add(k); out.append((a, q.agent))
    return out

def rewrite(net, a, b):
    if a.kind == "EPS" and b.kind == "EPS": net.remove(a); net.remove(b); return
    if a.kind == "EPS" or b.kind == "EPS":
        e, g = (a, b) if a.kind == "EPS" else (b, a)
        g1, g2 = g.ports[1].link, g.ports[2].link
        net.remove(e); net.remove(g)
        link(net.add(Agent("EPS")).principal, g1)
        link(net.add(Agent("EPS")).principal, g2); return
    if same(a, b):                                   # ANNIHILATE
        a1, a2 = a.ports[1].link, a.ports[2].link
        b1, b2 = b.ports[1].link, b.ports[2].link
        net.remove(a); net.remove(b); link(a1, b1); link(a2, b2); return
    # COMMUTE (different binary agents, incl. DUP[a] vs DUP[b], a!=b)
    a1, a2 = a.ports[1].link, a.ports[2].link
    b1, b2 = b.ports[1].link, b.ports[2].link
    net.remove(a); net.remove(b)
    B1 = net.add(Agent(b.kind, b.label)); B2 = net.add(Agent(b.kind, b.label))
    A1 = net.add(Agent(a.kind, a.label)); A2 = net.add(Agent(a.kind, a.label))
    link(B1.principal, a1); link(B2.principal, a2)
    link(A1.principal, b1); link(A2.principal, b2)
    link(B1.ports[1], A1.ports[1]); link(B1.ports[2], A2.ports[1])
    link(B2.ports[1], A1.ports[2]); link(B2.ports[2], A2.ports[2])

def reduce_net(net, policy="first", rng=None):
    rng = rng or random.Random(); n = 0
    while True:
        ap = active_pairs(net)
        if not ap: break
        a, b = ap[0] if policy == "first" else ap[-1] if policy == "last" else rng.choice(ap)
        rewrite(net, a, b); n += 1
    return n

def readback(net, budget=4000, maxd=20):
    """Cycle-safe: interaction nets have aux-to-aux cycles, so cap depth AND
    total nodes (naive two-way recursion on a cyclic graph is exponential)."""
    b = [budget]
    def enc(p, d):
        if p is None: return "0"
        if p.agent is None: return f"<{p.flabel}>"
        b[0] -= 1
        if d > maxd or b[0] < 0: return "*"
        g = p.agent
        if g.kind == "EPS": return "e"
        lbl = "" if g.label is None else str(g.label)
        return f"{g.kind}{lbl}({enc(g.ports[1].link,d+1)},{enc(g.ports[2].link,d+1)})"
    return " | ".join(f"{f.flabel}={enc(f.link,0)}"
                      for f in sorted(net.free, key=lambda p: p.flabel))

# ---- helpers ----
def era(net): return net.add(Agent("EPS")).principal
def con(net, a, b):
    c = net.add(Agent("CON")); link(c.ports[1], a); link(c.ports[2], b); return c.principal
def dup(net, lbl, a, b):
    d = net.add(Agent("DUP", lbl)); link(d.ports[1], a); link(d.ports[2], b); return d.principal
def mark(net, k):                       # a distinguishable value: spine of depth k
    p = era(net)
    for _ in range(k): p = con(net, era(net), p)
    return p

if __name__ == "__main__":
    # Minimal DUP-DUP collision: an outer fan's principal meets an inner fan's
    # principal directly. The LABEL decides the rule, and thus the result.
    def collide(lo, li):
        net = Net(); A, B, C, D = (free_port(x) for x in "ABCD"); net.free = [A, B, C, D]
        o = net.add(Agent("DUP", lo)); i = net.add(Agent("DUP", li))
        link(o.principal, i.principal)
        link(o.ports[1], A); link(o.ports[2], B); link(i.ports[1], C); link(i.ports[2], D)
        n = reduce_net(net, "first")
        return n, len(net.agents)
    n1, a1 = collide(0, 0)
    n2, a2 = collide(0, 1)
    print(f"same label (0,0): {n1} interaction, {a1} agents left  (ANNIHILATE: A->C, B->D)")
    print(f"diff label (0,1): {n2} interaction, {a2} agents left  (COMMUTE: each fan copies the other)")
    print("labels change the reduction:", "YES" if (n1, a1) != (n2, a2) else "no")
