"""Probe: what do the coordination-free dynamics do WITHOUT the oracle?

run_async reports its fixed point via a SEMANTIC SATURATION phase (all-to-all
full-state exchange + centrally driven work exhaustion). That is a measurement
oracle: it computes the point the dynamics converge toward, but does not show
the pairwise gossip scheduler reaching it under its own protocol. This probe
removes the oracle and measures the autonomous dynamics directly.

Findings it reproduces (deterministic seeds):

A) At the default anti-entropy rate the stability heuristic stops the loop
   mid-propagation: replicas DISAGREE and one config is still 15/16 on some
   replica. The oracle was manufacturing agreement, not just measuring coverage.

B) Latency / duplication / loss battery (NO partition), adequate anti-entropy:
   every replica on every run reaches 16/16 (per-node, asserted) -- coverage
   closure is autonomous and robust. Fact-store agreement at the heuristic stop
   is frequent but not guaranteed; at every non-agreeing stop measured, all
   inboxes were EMPTY -- the differing facts sat in one replica's store
   awaiting a FUTURE random anti-entropy pairing (not "in flight"), and
   continued ordinary gossip reached agreement in tens of ticks. The layered
   result: SIGNATURE-SET agreement (which 16 behaviors exist) and usually
   PREFERRED-MAP agreement stabilize before FACT-STORE agreement.
   NOTE this heuristic-specific wording: the demonstrated gap is that THIS
   local stability heuristic cannot establish fact agreement. Certified
   termination (acknowledgements, version vectors, termination-detection
   protocols) is a distinct, unbuilt layer -- not an impossibility.

C) Temporary partition with STAGED HEALING (the corrected experiment; the
   earlier config partition=(2,300,900) was INVALID as labeled -- with adequate
   anti-entropy the runs stopped at ticks ~238-318, i.e. 7/8 BEFORE the
   partition began, so it mostly measured no-partition dynamics). Here the
   partition provably overlaps execution (asserted), heals, and the ordinary
   protocol runs on: we measure per-node coverage at heal (the partitioned
   node is typically BELOW 16/16 -- the fault bites), then time from heal to
   full per-node coverage and to fact agreement.

D) For every non-agreeing heuristic stop in B, continuing the same protocol
   reaches agreement autonomously (ticks reported).
"""
import random
from synth_async import Node

NV = 2

def covs(nodes):
    return [len([1 for (nv, s) in n.beh if nv == NV]) for n in nodes]

def sig_sets_agree(nodes):
    return len({frozenset(s for (nv, s) in n.beh if nv == NV)
                for n in nodes}) == 1

def pref_maps_agree(nodes):
    import json
    return len({json.dumps(sorted((str(s), t[2]) for s, t in
                                  n.reps(NV).items())) for n in nodes}) == 1

def fact_agree(nodes):
    return len({n.state_h() for n in nodes}) == 1

class Sim:
    """The exact autonomous event loop of run_async (pairwise delta gossip +
    periodic random pairwise anti-entropy), stepped externally so experiments
    can observe / continue without changing the protocol."""
    def __init__(self, N=4, max_size=8, seed=0, L=4, dup_p=0.15, drop_p=0.1,
                 anti=40, partition=None):
        self.rng = random.Random(seed)
        self.nodes = [Node(i, N, NV, max_size, None, True, self.rng)
                      for i in range(N)]
        self.N = N; self.L = L; self.dup_p = dup_p; self.drop_p = drop_p
        self.anti = anti; self.partition = partition
        self.tick = 0; self.last = [0] * N; self.bytes_tx = 0
        self.partition_ticks_seen = 0

    def blocked(self, a, b):
        if not self.partition: return False
        pn, t0, t1 = self.partition
        return t0 <= self.tick <= t1 and (a == pn or b == pn)

    def step(self):
        self.tick += 1
        if self.partition:
            pn, t0, t1 = self.partition
            if t0 <= self.tick <= t1: self.partition_ticks_seen += 1
        for n in self.nodes:
            if self.rng.random() > n.rate: continue
            due = [m for m in n.inbox if m[0] <= self.tick]
            n.inbox = [m for m in n.inbox if m[0] > self.tick]
            for _, m in due: n.import_msg(m)
            n.reconcile(); n.work()
            blob = n.flush()
            if blob:
                self.last[n.nid] = self.tick
                for peer in self.rng.sample(self.nodes, min(2, self.N)):
                    if peer is n or self.blocked(n.nid, peer.nid): continue
                    for _ in range(1 + (self.rng.random() < self.dup_p)):
                        if self.rng.random() < self.drop_p: continue
                        peer.inbox.append((self.tick +
                                           self.rng.randint(1, self.L),
                                           ("D", None, blob)))
                        self.bytes_tx += len(blob)
            if self.tick % self.anti == 0 and self.rng.random() < 0.5:
                peer = self.rng.choice(self.nodes)
                if peer is not n and not self.blocked(n.nid, peer.nid):
                    b2 = n.full_state()
                    peer.inbox.append((self.tick + 1, ("F", n.state_h(), b2)))
                    self.bytes_tx += len(b2)

    def heuristic_fires(self, window_mult):
        stable = self.tick - max(self.last) > window_mult * self.anti + \
                 self.L + 5
        return (stable and
                all(n.gen_stamp is not None for n in self.nodes) and
                all(n.depth >= 8 and not n.queue and not n.pending
                    for n in self.nodes))

def run_heuristic(seed, L, anti=5, wm=8, dup_p=0.15, drop_p=0.1,
                  partition=None, cap=800000, extra_cap=40000):
    """Run to the stability-heuristic stop; report per-node coverage and the
    three agreement layers; if fact stores disagree, continue the SAME
    protocol and report ticks to autonomous agreement."""
    s = Sim(seed=seed, L=L, dup_p=dup_p, drop_p=drop_p, anti=anti,
            partition=partition)
    while s.tick < cap:
        s.step()
        if s.heuristic_fires(wm): break
    out = dict(qtick=s.tick, covs=covs(s.nodes),
               sig=sig_sets_agree(s.nodes), pref=pref_maps_agree(s.nodes),
               fact=fact_agree(s.nodes), kb=s.bytes_tx // 1024,
               extra_to_agree=0)
    if not out["fact"]:
        t0 = s.tick
        while s.tick < t0 + extra_cap and not fact_agree(s.nodes):
            s.step()
        out["extra_to_agree"] = (s.tick - t0 if fact_agree(s.nodes) else -1)
    return out

def run_partition_heal(seed, t0, t1, L=6, anti=5, wm=8, cap=60000):
    """Staged healing experiment: assert the partition overlaps execution,
    record per-node coverage at heal, then measure ticks from heal to full
    per-node coverage and to fact agreement under the UNCHANGED protocol.
    Also record when the stability heuristic first fires post-heal, to compare
    the heuristic's stopping time against actual agreement."""
    s = Sim(seed=seed, L=L, anti=anti, partition=(2, t0, t1))
    covs_at_heal = None; t_cov = None; t_agree = None; t_heur = None
    while s.tick < cap:
        s.step()
        if s.tick == t1: covs_at_heal = covs(s.nodes)
        if s.tick >= t1:
            if t_cov is None and all(c == 16 for c in covs(s.nodes)):
                t_cov = s.tick - t1
            if t_agree is None and fact_agree(s.nodes):
                t_agree = s.tick - t1
            if t_heur is None and s.heuristic_fires(wm):
                t_heur = s.tick - t1
            if t_cov is not None and t_agree is not None and \
               t_heur is not None:
                break
    assert s.partition_ticks_seen > 0, "partition never overlapped execution"
    return dict(seen=s.partition_ticks_seen, covs_at_heal=covs_at_heal,
                t_cov=t_cov, t_agree=t_agree, t_heur=t_heur)

BATTERY = [("L=2", dict(L=2)), ("L=20", dict(L=20)),
           ("dup30/loss30", dict(L=8, dup_p=.3, drop_p=.3)),
           ("L=8", dict(L=8))]

if __name__ == "__main__":
    print("[AUTONOMOUS] pairwise gossip only -- NO all-to-all saturation oracle")

    print("\nA) default anti-entropy (anti=40, win=3): stops mid-propagation")
    print(f"   {'config':>14} {'min-cov':>8} {'fact':>5} {'qtick':>7}")
    for name, kw in BATTERY + [("partition n2",
                                dict(L=6, partition=(2, 300, 900)))]:
        r = run_heuristic(seed=2, anti=40, wm=3, **kw)
        print(f"   {name:>14} {min(r['covs']):>6}/16 {str(r['fact']):>5} "
              f"{r['qtick']:>7}")

    print("\nB) latency/dup/loss battery (NO partition), anti=5, seeds 1-8:")
    print(f"   {'config':>14} {'allnodes16':>10} {'sig':>5} {'pref':>5} "
          f"{'fact':>5} {'cont->agree ticks':>18}")
    tot = c16 = sg = pf = fa = 0; conts = []
    for name, kw in BATTERY:
        a16 = s_ = p_ = f_ = 0; ct = []
        for sd in range(1, 9):
            r = run_heuristic(seed=sd, anti=5, wm=8, **kw)
            tot += 1
            ok16 = all(c == 16 for c in r["covs"])
            a16 += ok16; c16 += ok16
            s_ += r["sig"]; sg += r["sig"]
            p_ += r["pref"]; pf += r["pref"]
            f_ += r["fact"]; fa += r["fact"]
            if not r["fact"]:
                ct.append(r["extra_to_agree"]); conts.append(r["extra_to_agree"])
        print(f"   {name:>14} {str(a16)+'/8':>10} {str(s_)+'/8':>5} "
              f"{str(p_)+'/8':>5} {str(f_)+'/8':>5} "
              f"{str(sorted(ct)) if ct else '-':>18}")
    print(f"   TOTAL: per-node coverage {c16}/{tot}; signature-set agree "
          f"{sg}/{tot}; preferred-map agree {pf}/{tot}; fact agree {fa}/{tot}")
    print(f"   every non-agreeing stop -> autonomous agreement on "
          f"continuation, ticks: {sorted(conts)}")
    assert c16 == tot, "a replica ended below 16/16 in the no-partition battery"
    assert all(t >= 0 for t in conts), "a continuation failed to agree"

    print("\nC) STAGED PARTITION HEALING (node 2 cut t0..t1, then heals;")
    print("   protocol unchanged; measured post-heal). seeds 1-8:")
    print(f"   {'window':>10} {'partition bit?':>14} {'cov@heal(min)':>13} "
          f"{'t->cov16':>9} {'t->agree':>9} {'heur<agree':>10}")
    for (t0, t1) in [(50, 150), (50, 250), (100, 250)]:
        bit = 0; cmin = []; tcs = []; tas = []; hb = 0
        for sd in range(1, 9):
            r = run_partition_heal(sd, t0, t1)
            bit += (min(r["covs_at_heal"]) < 16)
            cmin.append(min(r["covs_at_heal"]))
            tcs.append(r["t_cov"]); tas.append(r["t_agree"])
            hb += (r["t_heur"] is not None and r["t_agree"] is not None
                   and r["t_heur"] < r["t_agree"])
        tcs = sorted(t if t is not None else -1 for t in tcs)
        tas = sorted(t if t is not None else -1 for t in tas)
        print(f"   {str((t0,t1)):>10} {str(bit)+'/8':>14} "
              f"{str(sorted(cmin)):>13} "
              f"med {tcs[4]:>4} max {tcs[-1]:>4} "
              f"med {tas[4]:>4} max {tas[-1]:>4} {str(hb)+'/8':>10}")
        assert all(t >= 0 for t in tcs) and all(t >= 0 for t in tas), \
            "a partition run failed to recover"
    print("   -> the fault bites (partitioned node below 16 at heal), and the")
    print("      UNCHANGED protocol recovers full per-node coverage and fact")
    print("      agreement autonomously after healing. The stability heuristic")
    print("      often fires before agreement -- consistent with (B).")
