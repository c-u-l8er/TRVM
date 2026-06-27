"""
share_win.py - does our reducer evaluate a SHARED reducible computation once?

Shared computation = a chain of L pass-through stages around a tiny value z.
Each stage is a clean CON-CON annihilation that threads the value through (NO
self-loops). Cost ~2L interactions; result = z (tiny). We share that result to
N consumers via a fan and compare to N independent chains. Sharing => the chain's
~2L cost is paid ONCE; recompute => paid N times.
"""
from linet import Net, Agent, link, free_port, reduce_net, readback

def era(net): return net.add(Agent("EPS")).principal
def val(net, k=2):
    p = era(net)
    for _ in range(k):
        c = net.add(Agent("CON")); link(c.ports[1], era(net)); link(c.ports[2], p); p = c.principal
    return p

def chain(net, length, z_port):
    """Thread z_port through `length` CON-CON annihilation stages. Each stage:
    A.principal<->B.principal (redex); A.aux1=incoming, B.aux1=outgoing; the spare
    aux are erased. Annihilation links incoming<->outgoing: value passes through."""
    cur = z_port
    for _ in range(length):
        A = net.add(Agent("CON")); B = net.add(Agent("CON"))
        link(A.principal, B.principal)
        link(A.ports[1], cur); link(A.ports[2], era(net))
        link(B.ports[2], era(net)); cur = B.ports[1]
    return cur

def fan_to_n(net, n):
    roots = [era(net) for _ in range(n)]
    while len(roots) > 1:
        nxt = []
        for i in range(0, len(roots) - 1, 2):
            d = net.add(Agent("DUP", 0)); link(d.ports[1], roots[i]); link(d.ports[2], roots[i + 1])
            nxt.append(d.principal)
        if len(roots) % 2: nxt.append(roots[-1])
        roots = nxt
    return roots[0]

def shared(L, n):
    net = Net(); link(chain(net, L, val(net)), fan_to_n(net, n)); net.free = []
    return reduce_net(net, "first")

def separate(L, n):
    total = 0
    for _ in range(n):
        net = Net(); link(chain(net, L, val(net)), era(net)); net.free = []
        total += reduce_net(net, "first")
    return total

# CORRECTNESS FIRST: the chain must return z unchanged.
net = Net(); out = free_port("r"); link(out, chain(net, 8, val(net, 2))); net.free = [out]
c = reduce_net(net, "first")
rb = readback(net)
print(f"chain(8) on val(2): {c} interactions -> {rb}")
print("correct (== spine CON(e,CON(e,e))):", rb == "r=CON(e,CON(e,e))", "\n")

print(" L (chain cost) | N | shared | separate | saved | ratio")
print("----------------+---+--------+----------+-------+------")
for (L, n) in [(100, 8), (100, 16), (100, 32), (200, 16), (50, 16)]:
    s, p = shared(L, n), separate(L, n)
    print(f"      {L:4d}      |{n:3d}| {s:6d} | {p:8d} | {p-s:5d} | {p/s:.2f}x")
