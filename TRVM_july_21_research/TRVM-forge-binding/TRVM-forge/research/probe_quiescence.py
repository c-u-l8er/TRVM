"""Probe: is the reported fault-run coverage a TRUE fixed point of
merge -> derive frontier -> generate -> evaluate -> merge, or just the
union of what each node found before the harness stopped?

Method: reproduce run_async's driver verbatim, capture coverage at the
exact point run_async returns, THEN continue running work()+full
anti-entropy to a genuine fixed point (no node changes, all queues empty,
no node still flagged gen_stamp=None with generatable candidates), and
report coverage again. If it rises, the harness stopped short of closure.
"""
import json, random, itertools
import synth_async as sa
from synth_async import Node

def coverage(nodes, nvars=2):
    n0 = nodes[0]
    return len([1 for (nv, s) in n0.beh if nv == nvars])

def states_agree(nodes):
    return len({n.full_state() for n in nodes}) == 1

def run_and_probe(N=4, nvars=2, max_size=8, seed=0, L=4, dup_p=0.15,
                  drop_p=0.1, anti=40, restart=None, partition=None,
                  cap_ticks=120000):
    rng = random.Random(seed)
    nodes = [Node(i, N, nvars, max_size, None, True, rng) for i in range(N)]
    tick = 0; snaps = {}; last_change = [0] * N
    def blocked(a, b):
        if not partition: return False
        (pn, t0, t1) = partition
        return t0 <= tick <= t1 and (a == pn or b == pn)
    while tick < cap_ticks:
        tick += 1
        for n in nodes:
            if rng.random() > n.rate: continue
            due = [m for m in n.inbox if m[0] <= tick]
            n.inbox = [m for m in n.inbox if m[0] > tick]
            for _, m in due: n.import_msg(m)
            n.reconcile(); n.work()
            blob = n.flush()
            if blob:
                last_change[n.nid] = tick
                for peer in rng.sample(nodes, min(2, N)):
                    if peer is n or blocked(n.nid, peer.nid): continue
                    for _ in range(1 + (rng.random() < dup_p)):
                        if rng.random() < drop_p: continue
                        peer.inbox.append((tick + rng.randint(1, L),
                                           ("D", None, blob)))
            if tick % anti == 0 and rng.random() < 0.5:
                peer = rng.choice(nodes)
                if peer is not n and not blocked(n.nid, peer.nid):
                    peer.inbox.append((tick + 1, ("F", n.state_h(),
                                                  n.full_state())))
            if tick % 50 == 0: snaps[n.nid] = (tick, n.full_state())
        if restart and tick == restart[1]:
            j = restart[0]; old = snaps.get(j)
            if old:
                nodes[j] = nodes[j].restore(old[1], rng); nodes[j].inbox = []
        stable = tick - max(last_change) > 3 * anti + L + 5
        if stable and all(n.depth >= max_size and not n.queue
                          and not n.pending for n in nodes):
            break
    # ---- run_async's final forced anti-entropy (verbatim) ----
    for _ in range(4):
        for n in nodes:
            s = n.full_state(); h = n.state_h()
            for peer in nodes:
                if peer is not n:
                    peer.import_msg(("F", h, s)); peer.reconcile()

    cov_at_return = coverage(nodes)
    agree_at_return = states_agree(nodes)
    stale_flags = [n.nid for n in nodes if n.gen_stamp is None]
    nonempty_q = [n.nid for n in nodes if n.queue]

    # ---- NOW drive to a genuine fixed point ----
    extra = 0
    while True:
        changed = False
        for n in nodes:
            before = n.state_h()
            n.reconcile()
            # exhaust this node's generation/evaluation
            guard = 0
            while n.work():
                guard += 1
                if guard > 100000: break
            if n.state_h() != before: changed = True
        # full anti-entropy so newly generated facts propagate
        for n in nodes:
            s = n.full_state(); h = n.state_h()
            for peer in nodes:
                if peer is not n:
                    peer.import_msg(("F", h, s)); peer.reconcile()
        extra += 1
        if not changed or extra > 200: break

    cov_closed = coverage(nodes)
    agree_closed = states_agree(nodes)
    return dict(cov_at_return=cov_at_return, agree_at_return=agree_at_return,
                stale_flags=stale_flags, nonempty_q=nonempty_q,
                cov_closed=cov_closed, agree_closed=agree_closed,
                extra_rounds=extra, progs_closed=set(nodes[0].prog))

CFGS = [("L=2",            dict(L=2, seed=1)),
        ("L=20",           dict(L=20, seed=2)),
        ("dup30/loss30",   dict(L=8, dup_p=.3, drop_p=.3, seed=3)),
        ("restart n1@stale",dict(L=6, restart=(1, 900), seed=4)),
        ("partition n2",   dict(L=8, partition=(2, 200, 900), seed=5)),
        ("L=8 seed6",      dict(L=8, seed=6))]

if __name__ == "__main__":
    print(f"{'config':>18} {'cov@return':>11} {'agree@ret':>9} "
          f"{'stale':>7} {'queued':>7} | {'cov CLOSED':>10} {'agree':>6} "
          f"{'+rounds':>7}")
    for name, kw in CFGS:
        r = run_and_probe(**kw)
        flag = "  <-- ROSE" if r["cov_closed"] > r["cov_at_return"] else ""
        print(f"{name:>18} {r['cov_at_return']:>9}/16 {str(r['agree_at_return']):>9} "
              f"{str(r['stale_flags']):>7} {str(r['nonempty_q']):>7} | "
              f"{r['cov_closed']:>8}/16 {str(r['agree_closed']):>6} "
              f"{r['extra_rounds']:>7}{flag}")
