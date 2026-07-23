# STEP 2 — superposed search, distributed coordination-free

**File:** `dsearch.py` — `python3 dsearch.py` (Part A) · `python3 dsearch.py dist` (Part B)
**Depends on:** `ic_ref.py` (the correct reducer from step 1)
**Status:** ✅ both parts validated against a brute-force oracle.

This is the payload step. Step 1 gave a *correct* single-node engine. Step 2 runs
the workload that is actually our contribution — **search** — on that engine, and
then distributes it across isolated nodes with **no coordination**, because the
workload is monotone and CALM says monotone ⇒ coordination-free.

## The toy problem (small, but it exercises the real machinery)

Find every `n` in `{0..N-1}` that's odd, with the predicate computed *inside the
calculus*: `NOT^n(FALSE)` is `TRUE` iff `n` is odd, and `NOT^n` is just Church
numeral `n` applied to `NOT`. So each candidate's test is `((church(n) NOT) FALSE)`.

## Why the candidates are pairs and the selector is dup-free

`ic_ref`'s body-carrying representation diverges on exactly one pattern:
*duplicate a higher-order numeral, then apply a copy of it to another higher-order
lambda.* (HVM's packed floating-dup runtime handles this; our simple rep doesn't.)

So the encoding is built to **never duplicate a numeral**:

```
candidate(i) = λs.((s church(i)) T_i)           -- pair: (numeral, free-var tag)
selector     = λnum.λtag.((((num NOT) FALSE) tag) *)   -- dup-free; num & tag used once
term         = ( &7{cand_0, &7{cand_1, ...}}  selector )
```

`APP-SUP` fans the **selector** across the candidates (FAN label 7). The selector
has no internal duplications, so each copy of it is clean. Every numeral lives in
one candidate and is consumed once. The divergent pattern never arises. One
reduction collapses to a superposed tree of `{tag_i (odd) | * (even)}`; flattening
it recovers the odd numbers.

> Labels: numerals use distinct labels `≥1000`, disjoint from the FAN label `7`, so
> the selector-duplication fan never wrongly annihilates against numeral-internal
> duplications.

## Part A — superposition reduces correctly on the fixed core

| domain | oracle | superposed result | interactions (superposed / separate) |
|---|---|---|---|
| 0..3  | 1,3            | ✅ same | 133 / 70 |
| 0..5  | 1,3,5          | ✅ same | 272 / 167 |
| 0..7  | 1,3,5,7        | ✅ same | 455 / 308 |
| 0..9  | 1,3,5,7,9      | ✅ same | 682 / 493 |

**Honest finding:** superposition costs **more** interactions than evaluating the
candidates separately. That's correct and expected — these candidates are
*independent* (distinct numerals, no shared sub-computation), so there's nothing
to share, and the superposition machinery (the fan in/out of the selector) is pure
overhead. Superposition only *wins* when candidates share structure; that win is
real and measured separately at **6–13×** in `SHARING.md`. What Part A proves is
the thing step 1 unblocked: **superposition reduces correctly** on higher-order
content. (Before the reducer fix, this didn't even terminate with the right
answer.)

## Part B — the same search, distributed with zero coordination

Each node is its **own OS process**, hence its own reducer heap — faithful to
"node = isolated heap" (the same stance `p2.py` took for the boundary-crossing
reducer). The domain is partitioned round-robin; each node runs a superposed
search on its slice and returns a solution **set**; sets merge by **union** — a
grow-only set (G-Set), the canonical CRDT join (commutative, idempotent, monotone).

```
ran 18 configs   (W ∈ {1,2,3,4,6,8})  ×  (3 merge orders)
every result == oracle : True
distinct results       : 1     ← schedule-independent
```

One distinct result across every node count and every merge order is the property
that matters: **the answer does not depend on the schedule.** That's monotonicity
⇒ coordination-freedom made concrete, exactly as CALM predicts for a G-Set-union
computation.

**Honest points:**

- **Termination is a plain `join()`.** There are no in-flight cross-node messages,
  so the Safra distributed-termination detector that `p2.py` needed (for a reducer
  that *passes redexes across* node boundaries mid-computation) is unnecessary
  here. This search is *embarrassingly* monotone — the strongest CALM-safe form.
  The boundary-crossing case is the harder one and is where `p2.py`'s machinery
  earns its keep; this workload simply doesn't need it.
- **No speedup at this scale.** Wall-clock got *worse* with more nodes
  (W=1: 10ms → W=4: 23ms) because process-pool startup dwarfs millisecond
  reductions. Reported as-is. Part B's claim is **coordination-free correctness**
  (any partition, any merge order, same answer), not performance. Real speedup is a
  separate question that needs a non-toy per-node workload and persistent workers.

## Where this sits in the arc

HVM4's destination is parallel **program/proof search** on a compiled Interaction
Calculus, single-node. Search is monotone, so the axis HVM isn't building —
**coordination-free distribution across machines** — is both open and a natural
fit. Part B is a working, validated micro-instance of that: the distributed
version of HVM's destination, on our boundary-port/CRDT model.

**Next:**
1. **The WASM core.** Port `ic_ref`'s exact rules to the packed-word
   representation and compile to WASM. `ic_ref.py` becomes the conformance oracle
   that port is tested against. This is the sovereignty/edge substrate.
2. **OpenSentience mapping.** Place this search-as-monotone-workload under the
   `&reason` / SCOPE / CRDT story: cheap symbolic agents as IC sub-nets,
   coordination-free across browsers/edge, with the box-and-box governance floor
   verified *on* the WASM IC engine.

The through-line: a correct core (step 1), a monotone workload that distributes
without locks or consensus (step 2), then the same thing in WASM unified with the
[&] / OpenSentience stack.
