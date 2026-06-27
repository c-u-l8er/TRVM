# Distributed Interaction Nets: design notes & validation ledger

*A coordination-free distributed runtime for interaction nets (HVM-style), and the open question that actually makes it hard.*

---

## 0. Thesis (one sentence)

Interaction-net reduction is **confluent by construction**, confluence is the
operational basis of **coordination-free** distributed execution, therefore a
multi-node interaction-net runtime can *reduce* without locks or consensus —
and the only place real coordination is forced is **distributed termination
detection** (knowing the whole net is in normal form).

---

## 1. What we validated (the honest ledger)

### CONFIRMED
- **Confluence ⇒ coordination-free is a real, load-bearing bridge.** In the
  distributed-systems literature, a confluent operation is one that "produces
  the same set of outputs for any nondeterministic ordering and batching of
  inputs," and confluence is explicitly *a generalization of commutativity*
  that **composes**: programs built by composing confluent operations are
  confluent regardless of message/step ordering within or across sites
  (Hellerstein; Akhtar et al. 2024). Interaction nets are *strongly confluent*
  as a theorem (Lafont 1990/1997), and the IN community already states the
  folklore — "no synchronisation is needed… guaranteed by the strong
  confluence property." We now have the matching formal vocabulary.
- **The combinator core.** Lafont's symmetric interaction combinators —
  three agents {ε, δ, γ}, one principal port each, six rules
  (3 annihilation + 3 commutation) — are a *universal model of distributed
  computation*. The prototype (`inet.py`) implements them and empirically
  confirms strong confluence: 300 random reduction orders of a depth-3
  duplication net all reach the same normal form in **exactly 15 interactions**
  (the interaction *count*, not just the result, is order-invariant).
- **Prior art for distribution exists** in the Geometry-of-Interaction /
  token-passing line: **PELCR** distributes Lévy-optimal λ-reduction over MPI
  using *directed virtual reduction*, with **message aggregation** to amortize
  communication and dynamic load balancing.

### CORRECTED (claims I had overstated)
- **"Monotone" → "confluent".** CALM's iff is stated over *monotonicity*
  (output never retracts as input grows). Pure reduction is not monotone in
  the naive "heap only grows" sense — annihilation *destroys* nodes. The
  correct framing: the observable is the **normal form**, and the lattice is
  over **reduction progress / information**, not heap size. Reduction only ever
  approaches the (unique) normal form and never retracts it. So the precise,
  defensible primitive is **confluence**; monotonicity is the sufficient
  condition CALM happens to use.
- **PELCR's scale.** PELCR was *designed* for distributed execution (MPI,
  message aggregation), but its headline 70–88%-of-ideal speedups were measured
  on **shared-memory multiprocessors**, not large clusters. The graph-rewriting
  line (MPINE, ingpu, HVM) is **single-machine** to date (multicore + GPU;
  HVM-CUDA reports ~45B interactions/s on one GPU). Multi-node *graph-rewriting*
  interaction nets remain effectively unexplored.

### GAP FOUND (the real research core)
- **Termination detection is the hard part, not reduction.** Reduction is
  coordination-free, but knowing *globally* that no active pair remains on
  *any* node is a distributed termination-detection problem. Vanilla CALM is
  **agnostic to timing/interactivity**: monotonicity can be "achieved" by
  waiting for all inputs, which says nothing about when a node may act on a
  partial result (Li & Lee 2025; cf. "free termination", Power/Koutris/
  Hellerstein 2025). In the prototype this shows up as the one global predicate
  the 2-node loop must evaluate ("are *both* nodes idle?"); in a real system
  that is the Safra / Dijkstra–Scholten layer.
- **Sharing complicates lineage-based recovery.** Determinism + confluence
  suggest Spark-RDD-style "recompute lost partitions from inputs" instead of
  checkpointing. But sharing — the entire point of HVM — means a partition's
  computation may be entangled with another's, so "what are a partition's
  inputs" is non-trivial. Recovery needs a sharing-aware lineage model.
- **Effects / superposition-collapse break confluence.** Pure reduction is
  confluent; IO, mutable refs, and the `&`-superposition *collapse* are the
  non-confluent fragment. Per Complete-CALM (2026), these are exactly where
  coordination must be (re)introduced — and where to draw the boundary is a
  real question.

---

## 2. SOTA map

| Lineage | Representatives | Distribution model | Status |
|---|---|---|---|
| Graph-rewriting | MPINE, ingpu, **HVM/Bend** | shared memory; locality + strong confluence ⇒ minimal sync | single-machine (multicore + GPU) |
| GoI / token-passing | **PELCR**, IAM | MPI, directed virtual reduction, message aggregation, dynamic load balance | distributed by design; benchmarked on SMP |
| Coordination-free theory | CALM, **Complete-CALM (2026)**, Hydro, CRDTs | monotonicity/confluence ⇒ no consensus; compile single program → distributed | active; not yet applied to interaction nets |

The opportunity sits in the empty cell: **multi-node graph-rewriting**, with a
**Complete-CALM-grounded** correctness story. The folklore ("no sync, by
confluence") lives in the IN world; the formal coordination-free machinery
lives in the DB/distributed-systems world; **the explicit bridge is unwritten.**

---

## 3. Architecture

```
                 +-------------------------------------------+
   (P3) locality | partitioner + sequentiality analysis      |
                 |  - keep frequently-interacting agents       |
                 |    co-located; don't distribute             |
                 |    inherently-sequential fragments          |
                 +---------------------+---------------------+
                                       |
   (P0/P1) core  +--------------------v----------------------+
 coordination-   | LOCAL REDUCTION (no locks, no consensus)  |
 free            |  each node runs a worklist of its own       |
                 |  active pairs; confluence guarantees the    |
                 |  global normal form is order-independent    |
                 +--------+----------------------+------------+
                          |                      |
   cross-node wires  +----v-----+          +-----v----+
                     | message  |  <---->  | message  |   (P2) message
                     | aggreg.  |          | aggreg.  |   aggregation a la PELCR
                     +----+-----+          +-----+----+
                          |                      |
   (P2) THE HARD PART +---v----------------------v---+
                      | distributed TERMINATION       |
                      | DETECTION  (Safra / D-S)      |   <- the one coordination point
                      +------------------------------+

   (P4) fault tolerance: deterministic recomputation of lost partitions
        (sharing-aware lineage), not checkpointing
```

**Cross-node wire** = a wire whose two ports live on different nodes. When an
active pair straddles a boundary, either migrate one agent (the prototype's
strategy = one message) or do a remote rewrite. Either way: amortize with
message aggregation, since a single rewrite is ~ns and a message is ~μs–ms —
**coarsening/locality is the whole game**, not the rewrite mechanics.

---

## 4. Open research questions (the publishable core)

1. **Characterize the coordination-free fragment.** Cast interaction-net
   reduction as a Complete-CALM specification (refinement order = reduction
   order; observation interface = readback). Prove the pure fragment is
   distributed-monotone; locate exactly where effects/collapse force coordination.
2. **Can termination detection itself be made (near-)coordination-free?**
   Or: what is the *minimal* coordination — the "fragile structure" in
   Complete-CALM terms — for an interaction net's "done" signal?
3. **Sharing-aware lineage recovery.** A determinism+confluence recovery model
   that handles cross-partition sharing without recomputing the world.
4. **Locality metric & partitioner.** What net statistic predicts good cuts,
   and can it be maintained online as the net morphs?

---

## 5. Phased build plan

- **P0 — single-node reducer + confluence harness.**  *DONE* (`inet.py`):
  combinators, random/fixed reduction policies, empirical strong-confluence test.
- **P1 — in-process multi-node simulation.**  *DONE* (`inet.py`):
  agents partitioned over N nodes, randomized async interleaving, migration =
  message; asserts identical normal form + interaction count vs sequential.
- **P2 — real two-process runtime.** Two OS processes (or BEAM/NATS), async
  message passing for cross-node wires, message aggregation, and a real
  Safra/Dijkstra–Scholten termination detector. *This is where the thesis meets
  the network.*
- **P3 — partitioning + locality / sequentiality analysis.**
- **P4 — fault tolerance via deterministic recomputation.**

Fastest external shortcut for P2/P3: stand on **Ray** (object store = the
distributed heap, actors = node workers) rather than building the fabric.

---

## 6. References
- Lafont, *Interaction Combinators*, Inf. Comput. 137 (1997). https://www.semanticscholar.org/paper/6cfe09aa6e5da6ce98077b7a048cb1badd78cc76
- Interaction nets (folklore: no sync, by strong confluence). https://handwiki.org/wiki/Interaction_nets
- Pedicini & Quaglia, *PELCR: Parallel Environment for Optimal Lambda-Calculus Reduction* (2004). https://arxiv.org/abs/cs/0407055
- Jiresch, *Towards a GPU-based implementation of interaction nets* (2014). https://arxiv.org/abs/1404.0076
- Hellerstein & Alvaro, *Keeping CALM: When Distributed Consistency is Easy*, CACM (2020). https://cacm.acm.org/research/keeping-calm/
- *Complete CALM: A Coordination Criterion for Specifications* (2026). https://arxiv.org/html/2602.09435
- Akhtar et al., *Coordination-free Collaborative Replication based on Operational Transformation* (2024) — confluence = generalization of commutativity, composes. https://arxiv.org/abs/2409.09934
- Li & Lee, *A Preliminary Model of Coordination-free Consistency* (2025) — CALM is timing-agnostic. https://arxiv.org/abs/2504.01141
- Hydro project (compile single program → distributed). https://hydro.run/research/
- Higher Order Co. — HVM3. https://github.com/HigherOrderCO/HVM3
