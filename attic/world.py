"""
world.py - A coordination-free spatial agent world (sketch).

The smallest thing that makes the whole arc load-bearing. Agents live in a space
split into REGIONS (TRVM shards), interact only with neighbours, and carry state
across region boundaries by moving (the p2.py handoff, abstracted). Their
interaction here is MONOTONE knowledge spread -- a CRDT join-semilattice -- the
confluent fragment that, by CALM, needs no coordination. So the agent world
INHERITS the runtime's property: within a tick, regions process in any order /
concurrently and the outcome is identical; no region ever talks to another, yet
knowledge spreads globally purely through agents crossing boundaries.

Coordination concentrates only at the tick barrier (the control plane) -- exactly
as it concentrated at termination detection in the runtime. Agent COGNITION here
is pure-symbolic and dirt cheap (scales to millions). The doc covers where
symbolic-via-interaction-nets and sparse-LLM minds slot in.
"""
import random

WIDTH, REGIONS, N_MEMES = 40, 2, 6
def region_of(pos): return min(REGIONS - 1, pos * REGIONS // WIDTH)

class Agent:
    __slots__ = ("aid", "pos", "knows")
    def __init__(self, aid, pos, knows):
        self.aid, self.pos, self.knows = aid, pos, set(knows)

def make_world(n_agents=80, seed=0):
    rng = random.Random(seed)
    agents = [Agent(i, rng.randrange(WIDTH), set()) for i in range(n_agents)]
    for m in range(N_MEMES):
        agents[m].knows.add(m)            # seed each meme with one carrier
    return agents

def precompute_paths(agents, ticks, seed=0):
    """Fixed movement intent per agent per tick, so ONLY scheduling varies."""
    rng = random.Random(seed * 7919 + 1); paths = {}
    for a in agents:
        p, steps = a.pos, []
        for _ in range(ticks):
            p = max(0, min(WIDTH - 1, p + rng.choice((-1, -1, 0, 1, 1))))
            steps.append(p)
        paths[a.aid] = steps
    return paths

def run(agents, paths, ticks, region_order_seed=0, track=False):
    rng = random.Random(region_order_seed); history = []; crossings = 0
    prev = {a.aid: region_of(a.pos) for a in agents}
    for t in range(ticks):
        # (1) move phase: positions advance per fixed paths; region recomputed.
        for a in agents:
            a.pos = paths[a.aid][t]
            r = region_of(a.pos)
            if r != prev[a.aid]: crossings += 1; prev[a.aid] = r   # a boundary handoff
        # (2) interact phase: regions processed in RANDOM order (must not matter);
        #     within a region, co-located agents merge knowledge (a CRDT join).
        order = list(range(REGIONS)); rng.shuffle(order)
        for r in order:
            cells = {}
            for a in agents:
                if region_of(a.pos) == r:
                    cells.setdefault(a.pos, []).append(a)
            for group in cells.values():
                if len(group) > 1:
                    merged = set().union(*(g.knows for g in group))
                    for g in group: g.knows = set(merged)
        if track:
            history.append({m: sum(1 for a in agents if m in a.knows) for m in range(N_MEMES)})
    return history, crossings

def snapshot(agents):
    return tuple(sorted((a.aid, frozenset(a.knows)) for a in agents))

if __name__ == "__main__":
    TICKS = 60
    seed_world = lambda: make_world(seed=1)
    paths = precompute_paths(seed_world(), TICKS, seed=1)

    # Coordination-free claim: identical outcome regardless of how regions are
    # scheduled within each tick.
    results = []
    for sched in range(40):
        agents = seed_world(); run(agents, paths, TICKS, region_order_seed=sched)
        results.append(snapshot(agents))
    ok = all(r == results[0] for r in results)
    print("coordination-free check: 40 random within-tick region schedulings")
    print(f"  -> identical final knowledge distribution every time: {ok}")

    # Show global spread achieved with ZERO cross-region coordination.
    agents = seed_world(); hist, crossings = run(agents, paths, TICKS, track=True)
    total = len(agents)
    print(f"\nknowledge spread: {total} agents, {REGIONS} regions, monotone interactions")
    for t in (0, 14, 29, 59):
        bars = "  ".join(f"m{m}:{hist[t][m]:2d}" for m in range(N_MEMES))
        print(f"  tick {t:2d}: {bars}")
    knows_all = sum(1 for a in agents if len(a.knows) == N_MEMES)
    print(f"\n  boundary crossings over run: {crossings}  (the only inter-region flow)")
    print(f"  agents knowing ALL {N_MEMES} memes by tick {TICKS}: {knows_all}/{total}")
    print("  -> memes reached the far region only by agents physically carrying them across.")
