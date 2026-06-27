# TRVM — Specification (v0.1, draft for implementation)

**TRVM** = a **distribution-native** interaction-net runtime. Its reason to exist is *not*
single-node speed (HVM5 shows an AI-assisted reducer reaches ~10x over its predecessor in days —
that loop is a commodity). TRVM's value is the layer HVM does not have and cannot easily grow:
**boundary ports, coordination-free reduction across machines, exactly-once boundary interactions,
termination detection, and deterministic-recompute fault tolerance.**

This document is written to be handed to coding agents. Normative requirements use MUST / MUST NOT /
SHOULD. The executable reference semantics for the rule table and the distribution protocol live in
`inet.py` (tested); this spec adds the production memory representation, the wire protocol, the
embedding API, and the conformance suite.

---

## 1. Computational model (the correctness bedrock)

TRVM evaluates **interaction nets** (Lafont). Agents have exactly one **principal port** and zero or
more **auxiliary ports**. The core agent set is the symmetric interaction combinators plus the
machinery needed for a real runtime:

| Agent | Aux | Meaning |
|---|---|---|
| `ERA` (ε) | 0 | eraser |
| `CON` (γ) | 2 | constructor / application (binary; n-ary allowed, see §3.4) |
| `DUP` (δ) | 2 | duplicator (labelled; the label is the DUP "color") |
| `REF` | 0 | reference to a named definition (lazy unfold; needed for recursion) |
| `BND` | * | **boundary port**: the wire's peer lives on another node (TRVM-specific) |

A **wire** connects exactly two ports. An **active pair** (redex) is a wire connecting two principal
ports. Reduction rewrites one active pair at a time; rewriting is **local** (touches only the two
agents and their wires) and the system is **strongly confluent**: the normal form, and even the
*number of interactions*, is independent of reduction order. (Reference: `inet.py` demo [1] —
300 random orders reach the same normal form in exactly 15 interactions on the test net.)

> **Why this matters for distribution.** Confluence is the operational basis of coordination-free
> execution: a confluent operation yields the same result under any ordering/batching of inputs, and
> confluent operations *compose*, so order-independence holds across distributed sites. TRVM's pure
> fragment (the table in §3.1–§3.4) is confluent and therefore reducible with **no locks and no
> consensus**. The non-confluent fragment (native numbers/ops, IO, the superposition *collapse*) is
> quarantined in §3.5 and is the *only* place coordination is reintroduced — besides termination
> detection (§4.4).

---

## 2. Memory representation (the IR)

Grounded in HVM2/HVM-core's layout (a node is two aux-port pointers; the principal port is *implicit*,
represented by whatever points at the node; nets are a heap of nodes plus a bag of redexes).

### 2.1 Port (a 64-bit tagged word)

```
 bits:  [ 63 .. 32 ]   [ 31 .. 4 ]   [ 3 .. 0 ]
        |   addr     | |  label   | |  tag    |
```
- `tag` (4 bits): one of `VAR, REF, ERA, CON, DUP, NUM, OP2, SWI, BND` (room for 16).
- `label` (28 bits): DUP color, OP2 operator code, BND-table index, or REF symbol id.
- `addr` (32 bits): heap index of the target node (2 GB/instance; widen to 48 bits if needed).

A `VAR` port names a wire whose other end is an aux port (the two halves share a slot; substitution
follows the var). A principal-port reference is any non-VAR port pointing at a node.

### 2.2 Node, redex, net

```c
typedef uint64_t Port;
typedef struct { Port aux1, aux2; } Node;          // principal is implicit
typedef struct { Port a, b; }       Redex;         // a wire between two principal ports
typedef struct {
    Port   root;                                   // single free/interface wire
    Redex *redexes; size_t n_redexes;              // the active-pair bag (work queue)
    Node  *heap;    size_t heap_len;               // bump-allocated arena
    Bnd   *bnd;     size_t n_bnd;                  // boundary table (§4.1)
} Net;
```
- Allocation MUST be a bump/linear allocator over `heap`; all allocations are ≤ one `Node`.
- The runtime is **GC-free**: the `ERA` rules free memory; an optional `collect()` may reclaim
  unreachable subnets but MUST produce results identical to running erasure.

### 2.3 Textual IR (for tests, debugging, serialization seed)

Adapted from HVM-core: `(a b)` = CON, `{a b}` = DUP (with `{a b}#k` for color `k`), `*` = ERA,
`@name` = REF, lowercase = VAR (aux-to-aux wire), `& A ~ B` = an active pair, `R` = root wire.
A boundary port is written `?w` where `w` is a global wire id (§4.1).

```
@main = R                       // a closed net with one free wire R
  & {a b} ~ (x x)               // an active pair: DUP applied to a CON
```

### 2.4 Wire serialization (cross-node + disk)

A serialized net/fragment is: a varint count, then a flat list of `Node`s, then the redex bag, then
the boundary table, then `root`. Ports are little-endian u64. This format is used by `trvm_load`,
`trvm_snapshot`, and the boundary `Export` payload (§4.2).

---

## 3. Rule table (normative)

Exactly one rule per unordered pair of principal tags. Wiring below is the tested wiring from
`inet.py`. `peer(p)` = the port wired to `p` (captured **before** any node is freed).

### 3.1 Annihilation (same kind)
- **ERA ~ ERA**: free both. (No aux.)
- **CON ~ CON** / **DUP ~ DUP** (same DUP color): free both; then `link(peer(A.aux1), peer(B.aux1))`
  and `link(peer(A.aux2), peer(B.aux2))`. (Symmetric IC: straight-through.)

### 3.2 Commutation, eraser vs binary
- **ERA ~ CON** / **ERA ~ DUP**: free both; allocate two `ERA`; `link(ERA1, peer(g.aux1))`,
  `link(ERA2, peer(g.aux2))`. (The eraser propagates, capping both wires.)

### 3.3 Commutation, CON vs DUP (different kinds, or different DUP colors)
- Free both; allocate `CON1, CON2, DUP1, DUP2`; wire the 2×2 grid:
  ```
  link(CON1.p, peer(DUP.aux1)); link(CON2.p, peer(DUP.aux2))
  link(DUP1.p, peer(CON.aux1)); link(DUP2.p, peer(CON.aux2))
  link(CON1.aux1, DUP1.aux1); link(CON1.aux2, DUP2.aux1)
  link(CON2.aux1, DUP1.aux2); link(CON2.aux2, DUP2.aux2)
  ```
  (DUP of the same color annihilates instead — §3.1 — which is how labelled duplication avoids the
  "DUP duplicating its own copies" pathology.)

### 3.4 n-ary constructors & REF
- An n-ary `CON` generalizes §3.1/§3.3 pointwise (DUP distributes over all n aux; ERA caps all n).
- **REF ~ anything**: the REF MUST first *unfold* to its definition's net (copied into the heap),
  producing new redexes. Eager evaluators MUST compile recursion to **supercombinators** and unfold
  REFs lazily, or they will expand recursive bodies forever.

### 3.5 Extension fragment (NON-confluent — quarantined)
`NUM`, `OP2`, `SWI` (native numbers/operators/match) and any IO are NOT part of the confluent core.
Implementations MAY support them, but MUST mark redexes touching them as **coordination-required**:
such a redex MUST be owned and reduced by a single node and MUST NOT be speculatively duplicated.
The `&`-superposition **collapse** is likewise in this fragment.

---

## 4. Boundary ports & the distribution protocol (the heart)

This is the network generalization of HVM2's intra-machine safety rule — *the thread holding a redex
owns both its trees*. TRVM lifts "thread" to "node" and makes ownership a **deterministic function of
the wire**, so the two endpoints agree without a round-trip.

### 4.1 Boundary table

A `BND` port's `label` indexes the per-node boundary table:
```c
typedef struct {
    uint64_t wire_id;     // globally unique id of this cross-node wire
    uint32_t owner_node;  // the node that performs rewrites on this wire (see 4.3)
    uint32_t peer_node;   // where the wire's other end currently lives
} Bnd;
```
`wire_id` MUST be globally unique and stable for the life of the wire (e.g. `(creator_node << 40) |
local_counter`).

### 4.2 Export descriptor (the only cross-node message for reduction)

When a node must hand a boundary agent to an owner, it sends:
```
Export {
  wire_id    : u64           // the active-pair wire
  kind, label: agent header  // CON/DUP/ERA/..., + DUP color etc.
  aux_wires  : [u64]         // the wire_id each aux port connects to (NOT the subtrees)
}
```
**Only the agent header travels — never its reachable subtree.** This keeps every message proportional
to the *cut*, not the net size, and preserves sharing. (Echoes PELCR's message-aggregation discipline
and the distributed-graph pattern of shipping vertex updates, not subgraphs.)

### 4.3 Ownership rule

For a boundary wire `w` between nodes `A` and `B`, define `owner(w)` deterministically. Default:
`owner(w) = min(A, B)`. (A hash `owner(w) = h(wire_id) mod live_nodes` MAY be used instead for load
balance; it MUST be agreed by both endpoints from `wire_id` alone.)

### 4.4 Reduction protocol

Each node runs its own redex bag with **no locking**. Per redex:

1. **Both principals local** → reduce immediately (§3). New nodes stay on this node.
2. **One principal is `BND`** (boundary active pair on wire `w`):
   - If this node is **not** `owner(w)`: emit `Export` for *its* agent to `owner(w)`, then delete the
     agent locally; its aux wires are now owned by `owner(w)`. Do **not** rewrite.
   - If this node **is** `owner(w)`: **wait** for the peer's `Export`. On arrival, reconstruct the peer
     agent locally (a node whose aux ports are `BND`s to `aux_wires`), which forms a local redex →
     reduce it via §3. Products whose ports reference remote wires become new `BND` ports / outgoing
     `Export`s as needed.

> **A boundary active pair is reduced exactly once — by its owner, upon receiving the peer's export.**

**Channel requirement (found while building P2).** Exporting an agent mints new boundary wires for
its aux ports; a *child* export may reference a wire that a *parent* export created on the owner.
Therefore message channels MUST be **per-directed-pair FIFO** (the owner must inject the parent before
the child). TCP and BEAM distribution both provide this for free, so it costs no consensus and does
not weaken coordination-freedom — but arbitrary global reordering is *not* tolerated, and an
implementation over an unordered transport MUST buffer out-of-order injects until their wire exists.

### 4.5 Why this is confluent & coordination-free

1. **No local race.** An agent has one principal port, so its *only* possible redex is on that
   principal. A boundary agent's principal faces the boundary wire, so it cannot also be in a local
   redex. (Direct consequence of the single-principal discipline.)
2. **Exactly-once.** Each boundary wire has one owner; only the owner rewrites; the non-owner only
   exports. No double-spend even if both endpoints observe the wire simultaneously.
3. **Reorder-robust.** Export messages only ever *graft* wires (monotone — they never retract a
   result), so any delivery order yields the same normal form.

**Validated** (`inet.py` demo [3]): 50 runs, deterministic owners, **randomized message-delivery
order**, agents randomly partitioned — every run reaches the identical normal form in the same 15
interactions, and `exports == boundary_rewrites` in every run (exactly-once).

### 4.6 What this does NOT solve

- **Global termination detection.** Local reduction is coordination-free, but knowing *all* nodes are
  idle and *no* messages are in flight is a separate problem. TRVM MUST expose the hooks in §5.4 so a
  **Safra / Dijkstra–Scholten** detector can run on top. This is the residual coordination point.
- **The non-confluent fragment** (§3.5).
- **Sharing-aware recovery** (§6, open).

---

## 5. Embedding API (C ABI — drives both a Rustler/zigler NIF and a WASM build)

A single core compiles to (a) a C-ABI shared object for a BEAM NIF (Elixir-macro surface) and
(b) `wasm32` for a JavaScript surface. The surface language is decoupled from this API.

```c
// ---- lifecycle ----
TRVM*  trvm_new(uint32_t node_id, size_t heap_words);
void   trvm_free(TRVM*);
int    trvm_load(TRVM*, const uint8_t* net_bytes, size_t len);   // §2.4 -> heap + redex bag
size_t trvm_readback(TRVM*, uint8_t* out, size_t cap);           // serialize current net

// ---- reduction (bounded burst; the budget is the coarsening knob) ----
typedef struct { uint8_t* data; size_t len; } Bytes;
typedef enum { TRVM_IDLE = 0, TRVM_ACTIVE = 1 } TrvmStatus;
typedef struct {
    TrvmStatus status;            // ACTIVE if local redexes remain
    uint64_t   interactions;      // rewrites performed this call
    Bytes*     exports; size_t n_exports;   // outgoing Export descriptors (§4.2) for the fabric
} ReduceResult;
ReduceResult trvm_reduce_batch(TRVM*, uint64_t budget);          // reduce <= budget LOCAL redexes

// ---- boundary I/O (the fabric calls these) ----
int    trvm_inject(TRVM*, const uint8_t* export_bytes, size_t len);  // deliver a peer's Export
int    trvm_open_boundary(TRVM*, uint64_t wire_id, uint32_t peer_node); // graft a BND port

// ---- termination-detection hooks (§4.6) ----
int      trvm_is_idle(TRVM*);                 // no local redexes AND no pending exports
uint64_t trvm_msgs_sent(TRVM*);
uint64_t trvm_msgs_recv(TRVM*);

// ---- fault tolerance (§6) ----
size_t trvm_snapshot(TRVM*, uint8_t* out, size_t cap);           // serialize for recovery
int    trvm_restore(TRVM*, const uint8_t* snap, size_t len);
```

**NIF discipline (MUST):** `trvm_reduce_batch` runs on a **dirty CPU scheduler** and MUST return after
`budget` interactions so the BEAM scheduler stays responsive and fault-isolated. The heap is held as
an opaque resource (Rustler `ResourceArc` / zigler resource); BEAM exchanges only `Export` bytes,
never the heap.

---

## 6. Invariants & conformance suite (the oracle)

Any implementation MUST pass these — they are how AI-written code is audited (the HVM5 arity bug is
exactly a property-test failure).

**Structural invariants (check after every rewrite in debug mode):**
- Every port is wired to exactly one other port (no dangling, no double-link).
- Every agent has exactly one principal port.
- After `ERA` rules, freed nodes are unreachable (GC-free property).
- `wire_id`s are unique among live `BND`s.

**Behavioral conformance (port from `inet.py`):**
1. **Confluence** — for a battery of nets, N random reduction orders MUST yield identical normal form
   *and* identical interaction count. (demo [1])
2. **Distributed = sequential** — `reduce_message_passing` under random partitions and random
   message-delivery order MUST match the sequential normal form and interaction count. (demo [3])
3. **Exactly-once boundary** — exports MUST equal boundary rewrites in every run. (demo [3])
4. **Snapshot round-trip** — `restore(snapshot(net))` MUST reduce to the same normal form as `net`.
5. **REF unfolding** — recursive supercombinator definitions MUST terminate where the math says they
   should and MUST NOT expand eagerly.

---

## 7. Implementation guidance

- **Language.** Surface ≠ runtime. Runtime options: **Zig** (best for hand-crafting: arena-friendly
  pointer-graph code, first-class `wasm32` target, clean C-ABI NIFs via `zigler`; cost: pre-1.0);
  **C** (best if you fork HVM5 or let agents write the loop — matches the domain, trivially WASM-able
  and NIF-able; offset unsafety with the §6 suite); **Rust** (conservative/safe; borrow-checker tax on
  the graph). Lean Zig to craft, C to fork.
- **Workflow.** Own the spec and the §6 oracle; let coding agents implement and optimize the inner
  loop against the oracle. This is HVM5's model with a correctness net the original lacked.
- **What to borrow.** HVM2/HVM-core for the heap encoding, redex bag, and bump allocator; HVM5's C
  loop if forking; PELCR for message aggregation; `inet.py` for the rule wiring and the test battery.
- **Phased plan.**
  - **P0** single-node core passing conformance §6.1 (port `inet.py` to the flat heap).
  - **P1** in-process multi-node passing §6.2–§6.3 (already modeled by `reduce_message_passing`).
  - **P2** real two-process runtime: NIF on a dirty scheduler + BEAM/OTP fabric, `Export` over
    distributed Erlang, Safra termination detector. (The Elixir `Partition` GenServer is the `:reduce`
    / `:wire` loop already prototyped.)
  - **P3** locality-aware partitioner + sequentiality analysis.
  - **P4** fault tolerance via deterministic recomputation of lost partitions.
- **Surfaces.** Elixir-macro `defnet` DSL → IR + OTP scaffolding (and the distributed runtime lives
  here). JS/WASM surface → single-node playground + visualizer (no BEAM, so no distribution there).

---

## 8. Open questions (carried forward)
1. Can termination detection itself be made (near-)coordination-free, or what is the *minimal*
   coordination for the global "done" signal? (Frame via Complete-CALM's "fragile structure".)
2. Sharing-aware lineage recovery: a partition's reduction may share nodes with another's, so
   "recompute from inputs" needs a sharing-aware lineage model.
3. Where exactly does the confluent fragment end once §3.5 and effects are admitted?

---

## 9. References
- Lafont, *Interaction Combinators*, Inf. Comput. 137 (1997).
- HVM-core / HVM2 memory layout & redex-ownership: https://docs.rs/crate/hvm-core/latest ; HVM2 PAPER https://docs.rs/crate/hvm/latest/source/paper/PAPER.pdf
- HVM5 (AI-assisted, ~3k lines C, ~10x over HVM4): Taelin, June 2026.
- Pedicini & Quaglia, *PELCR* (distributed optimal reduction, message aggregation): https://arxiv.org/abs/cs/0407055
- Hellerstein & Alvaro, *Keeping CALM* (CACM 2020): https://cacm.acm.org/research/keeping-calm/ ; *Complete CALM* (2026): https://arxiv.org/html/2602.09435
- Confluence composes / generalizes commutativity: https://arxiv.org/abs/2409.09934
- Reference semantics & conformance battery: `inet.py` (this repo).
