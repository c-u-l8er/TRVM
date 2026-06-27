# The agent VM — planning as interaction-net reduction (result, and the close of the arc)

W1 asked the sharp question — not "can a behaviour run on the reducer" (everything can;
interaction nets are Turing-complete) but "what behaviour *exploits* the reducer's one
superpower, superposition?" The answer is **search**: planning by evaluating many futures at
once. `plan.py` builds exactly that on the real `inet.py` reducer and measures it.

## What it does
An agent superposes a horizon of N plans into ONE interaction-net term and evaluates them in a
single reduction. The readback confirms the mechanism — one reduction yields the superposition
of all N processed outcomes:
`out = DUP(DUP(.., ..), DUP(.., ..))` for N=4. "Consider every future at once" as literal
interaction-net reduction, not metaphor.

## What it measures (real inet.py interaction counts)

| N plans | superposed | separate |
|--------:|-----------:|---------:|
| 1       | 1          | 1        |
| 8       | 15         | 8        |
| 64      | 127        | 64       |

`separate = N`. `superposed = 2N-1` — the N leaves plus the N-1 internal DUP nodes of the
superposition tree. So superposed costs N-1 **more**, not less.

## The honest finding (it confirms the pre-build prediction)
Two distinct things are now demonstrated:

1. **Cognition-as-reduction works.** The agent's deliberation — exploring all N plans — *is*
   one interaction-net reduction. The IN engine can be the agent VM, not merely a distributed
   substrate. This is the load-bearing claim, and it holds.
2. **The toy reducer gives no free sharing.** Superposed evaluation costs the full per-plan sum
   plus the superposition-tree overhead. It buys parallel *representation* (all plans in one
   term) but not sublinear *cost*.

Why no sharing? Because these plans share no common sub-computation, and — more
fundamentally — we proved earlier that `inet.py`'s interaction count is **order-invariant**
(strong confluence). So no reduction-order trick can share work; sharing must come from
*structure* (matching-label duplicators annihilating, à la Lamping/Lévy optimal reduction),
which naive unlabeled symmetric IC does not exploit for general computation. Exactly as
predicted before building: the toy shows the mechanism but not the economy.

## This closes the whole arc
The superpower that makes planning *cheap* — evaluating many plans for less than their separate
sum, via beta-optimal sharing — is precisely **HVM4/5's** contribution (optimal reduction:
labels, the oracle, the sharing machinery). The toy proves confluence and coordination-free
distribution; HVM provides the reduction economy. The division of labour is now exact:

```
  TRVM  owns  DISTRIBUTION  (boundary ports, coordination-free, deterministic recovery)
  HVM   owns  REDUCTION     (optimal sharing: many plans / many agents, cheaply, per node)
  the agent world  needs  BOTH
```

And the loop the whole conversation traced finally closes:

```
  HVM's optimal evaluation
    -> cheap superposed planning   (one reduction, many futures, sublinear)
      -> affordable symbolic agents (cognition you can run by the million)
        -> the spatial agent world  (coordination-free across nodes, via TRVM)
```

The agents are cheap enough to *exist* because of HVM's sharing; they scale across a world
because of TRVM's coordination-freedom. Neither alone is the product — the world is what needs
both.

## W1-proper (the next measurement)
Re-run this exact experiment on HVM4/5 (or Bend), where matching-label duplicators annihilate
and shared sub-plans are evaluated once. Prediction: superposed cost grows with the *shared
plan-tree size*, not the *number of leaves* — sublinear in N wherever plans share structure.
That is the number that turns "consider many futures" from a representation trick into an
economic superpower. The toy got us to the threshold honestly; HVM is where you cross it.

Prototypes in this repo: `plan.py` (this), `world.py` (agent world), `p2.py` (distributed
runtime + Safra), `inet.py` (reducer + confluence oracle), `SPEC.md`, `AGENT_WORLD.md`, `DESIGN.md`.
