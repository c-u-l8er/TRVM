"""
plan.py - Agent planning as interaction-net reduction (the "agent VM" test).

An agent superposes a horizon of plans into ONE term and evaluates them in a
single reduction of the real inet.py reducer. We measure interactions vs.
evaluating each plan separately, to locate exactly where the toy reducer ends
and HVM's optimal evaluation must begin.
"""
import inet
from inet import Agent, Net, link, free_port, reduce_net, readback

def era(net): return net.add(Agent("EPS")).principal
def con(net, a, b):
    c = net.add(Agent("CON")); link(c.ports[1], a); link(c.ports[2], b); return c.principal
def dup(net, a, b):
    d = net.add(Agent("DUP")); link(d.ports[1], a); link(d.ports[2], b); return d.principal

def plan_value(net, i):
    """Distinct outcome net for plan i (a left spine of depth i)."""
    p = era(net)
    for _ in range(i): p = con(net, era(net), p)
    return p

def superpose(net, roots):
    """Fold N plan-values into ONE superposition via a binary DUP tree."""
    while len(roots) > 1:
        nxt = []
        for i in range(0, len(roots) - 1, 2):
            nxt.append(dup(net, roots[i], roots[i + 1]))
        if len(roots) % 2: nxt.append(roots[-1])
        roots = nxt
    return roots[0]

def apply_scorer(net, value_root):
    """The shared op: a CON whose PRINCIPAL meets value_root -> an ACTIVE PAIR,
    so reduction fires. Under superposition it distributes to every plan."""
    out, tag = free_port("out"), free_port("tag")
    s = net.add(Agent("CON"))
    link(s.ports[0], value_root)            # principal <-> principal == redex
    link(s.ports[1], tag); link(s.ports[2], out)
    net.free = [out, tag]
    return out

def superposed_eval(n):
    net = Net()
    handle = superpose(net, [plan_value(net, i + 1) for i in range(n)])
    apply_scorer(net, handle)
    return reduce_net(net, "first"), net

def separate_eval(n):
    total = 0
    for i in range(n):
        net = Net(); apply_scorer(net, plan_value(net, i + 1))
        total += reduce_net(net, "first")
    return total

if __name__ == "__main__":
    print("agent planning as interaction-net reduction\n")
    print("  N | superposed | separate | note")
    print(" ---+------------+----------+------")
    for n in (1, 2, 4, 8, 16, 32, 64):
        sup_i, _ = superposed_eval(n); sep_i = separate_eval(n)
        delta = sup_i - sep_i
        print(f" {n:3d}|   {sup_i:6d}   |  {sep_i:5d}   | superposed - separate = {delta:+d}")
    _, net = superposed_eval(4)
    rb = readback(net)
    print("\none superposed reduction evaluates ALL plans together; readback:")
    print("  " + rb)
