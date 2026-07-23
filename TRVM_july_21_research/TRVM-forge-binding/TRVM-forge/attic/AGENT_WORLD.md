# The Agent World — design sketch (the agent-model fork)

A persistent spatial world where **people's own agents live**, interact locally, and
**humans sign in to join them**. This is the framing where the whole stack we built
finally composes instead of competing: TRVM is the space, interaction nets are the
cognition, `&memory` is the agents' memory, and coordination-freedom is what lets it
scale. This doc starts where everything hangs: the agent model.

Lineage (this is a live frontier, not a graveyard): Stanford's generative agents
(25 LLM agents with memory in a sandbox town) → Altera's Project Sid (1000+ agents in
Minecraft that specialized into professions, minted a currency, voted on a constitution,
spread a religion). The fresh twist here: agents are **user-owned residents**, the world
is a **persistent shared multiplayer space**, and **humans are co-present** — not a
terrarium you watch, but a populated world you enter.

---

## 1. The fork: what is an agent?

| Model | Per-agent cost | Intelligence | Is our runtime load-bearing? |
|---|---|---|---|
| **LLM agent** (Smallville/Sid) | High (an inference call per think) | High (language, planning) | **No** — runtime is just a spatial DB under LLM agents; Tile38 would do |
| **Symbolic agent** (interaction-net program) | Tiny (a few rewrites) | Low/scripted (no language) | **Yes** — the IN engine *is* the cognition; distribution scales it |
| **Hybrid** (symbolic body + sparse LLM mind) | Mostly tiny, occasionally high | Tunable | **Yes** for the 99% symbolic substrate; LLM only at the moments that matter |

**Recommendation: hybrid, with a symbolic core.** A million LLM agents is economically
impossible (Sid at 1000 is already expensive, and that inference cost dwarfs any
coordination savings). The only way to afford a real population is to make the *default*
agent tick dirt cheap and reach for an LLM rarely. That also happens to be the only design
in which the entire HVM→TRVM arc you've already built is doing work rather than sitting
underneath as plumbing.

---

## 2. The symbolic agent (the load-bearing part)

A symbolic agent is a **sub-net**: a small interaction-net term encoding its behaviour and
state. The mapping is almost a pun — Lafont's interaction nets literally call their nodes
*agents*, and here the world-agents *are* the net's agents:

- **Perception = meeting.** Two nearby agents' nets form an **active pair**; reducing it is
  the interaction. Spatial proximity is just which nets are wired to interact.
- **Action / state update = reduction.** The active pair reduces to (updated agents +
  effects). Behaviour is a rewrite rule, not an inference call.
- **Movement across a region = a boundary port.** An agent leaving one shard for the next
  is exactly p2.py's export/inject. Within a shard, agents reduce coordination-free; only
  boundary crossings are messages.
- **The world is one big interaction net**, partitioned into spatial shards (TRVM), reduced
  coordination-free, with confluence guaranteeing a consistent world-state regardless of
  reduction order.

`world.py` is the minimal proof of this shape. Its agents carry **monotone knowledge**
(a CRDT join-semilattice) and spread it on contact — the confluent fragment that, by CALM,
needs no coordination. Validated: across **40 random within-tick region schedulings the
final world-state is identical**, and 6 memes spread from a handful of carriers to 66/80
agents — reaching the far region **only** via agents physically crossing the boundary, with
**zero inter-region coordination**. That is the runtime's property, inherited by the world.

---

## 3. How it composes the whole stack

```
  human signs in  ─────────────┐
                               ▼
  &space  =  TRVM            [ a spatial shard ]  ←→ boundary handoff ←→ [ next shard ]
  (where agents live)          │  coordination-free local reduction
                               ▼
  cognition = interaction nets  agent behaviour = active-pair reduction (cheap, parallel)
                               │
  &memory = Graphonomous-style  per-agent knowledge graph (episodic/semantic), CRDT-merged
                               │
  control plane = the clock     coordination concentrates at the tick barrier ONLY
```

Note the recurring pattern: in the runtime, coordination concentrated at **termination
detection**; in the world, it concentrates at the **clock/tick barrier**. Same architecture
— a coordination-free data plane (local interaction) and a thin control plane (when/what-time).

---

## 4. Where the LLM mind slots in (the hybrid)

Keep LLM calls **sparse and event-driven**, never per-tick:

- **Human interaction.** When a person engages an agent, spin up an LLM "mind" for that
  exchange. Cost scales with *human attention*, which is bounded — not with population.
- **Reflection.** Periodically (or on a surprise/novelty signal), an agent summarizes its
  recent episodic memory into semantic memory via one LLM call — Sid's and Smallville's
  reflection step.
- **Novelty / escalation.** Most situations are handled by symbolic reflexes; only the
  genuinely novel ones escalate to a mind.

So the bill is: millions of agents × cheap symbolic ticks + (humans online) × occasional
minds. That is affordable in a way a-million-LLM-agents never is.

---

## 5. Honest limits

- **Not every interaction is confluent.** Monotone things (knowledge spread, presence,
  gossip, trade *offers*) are coordination-free and scale beautifully. Order-dependent
  things (combat, contention for a scarce resource, 3-party deals) are **not** confluent and
  need a **region authority** to serialize them — losing pure coordination-freedom for those
  events. This is the same split as the games analysis; design the social fabric to be as
  monotone as possible and quarantine the order-dependent bits.
- **The substrate is necessary at scale but is not the value.** Whether people want to *visit*
  is an agent-design and world-design problem, not a runtime one. Cheap symbolic agents are,
  by construction, not very smart — the craft is making them *interesting* in aggregate
  (emergence) and compelling up close (the sparse LLM minds).
- **Global time is itself coordination.** Discrete ticks are a synchronization barrier.
  Fully async stepping (regions advancing independently) is the hard distributed-simulation
  time-sync problem (conservative/optimistic synchronization); start with ticks, treat async
  as a research upgrade.
- **Cost is still the wall, just a movable one.** The hybrid makes a population affordable;
  it does not make it free. Watch the ratio of symbolic ticks to LLM calls like a hawk.

---

## 6. Minimal build plan

- **W0** — `world.py` as is: symbolic agents, one machine, monotone interactions, the
  coordination-free property demonstrated. *Done.*
- **W1** — richer symbolic behaviour: compile a tiny agent behaviour DSL to interaction-net
  terms and run them on the real reducer (`inet.py`), so cognition is genuinely IN reduction,
  not a stand-in. Add a region authority for one order-dependent interaction (e.g. picking up
  a unique item) to exercise the non-confluent path.
- **W2** — put it on TRVM/`p2.py`: two real shards, agents handed off across the boundary by
  the export/inject protocol, a human client that connects to a shard and pokes an agent.
- **W3** — the hybrid mind: wire one agent's "talk to a human" path to a single LLM call;
  measure the symbolic-tick : LLM-call ratio (the number that decides whether scale is
  affordable).
- **W4** — `&memory`: give agents a Graphonomous-style knowledge graph with reflection.

---

## 7. What this is

Probably not a business that beats HiveKit — but a genuinely novel thing on a real frontier,
that makes every piece of infrastructure you've built tangible, and that has a sharp technical
reason your specific (weird) stack is the right one: **cheap symbolic agents, by the millions,
living spatially in a coordination-free distributed world, with LLM minds only where humans
touch them.** That is the one design where interaction nets stop being the proof that made the
runtime correct and start being the thing doing the work. The whole arc, finally pointing at
one buildable object.

Reference prototypes (this repo): `world.py` (the agent world), `p2.py` (the distributed
runtime + Safra), `inet.py` (the reducer + confluence oracle), `SPEC.md` (the runtime spec).
