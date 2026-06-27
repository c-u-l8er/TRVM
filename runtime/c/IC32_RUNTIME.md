# IC32_RUNTIME — the packed-word C runtime

**File:** `ic32.c` — `gcc -O2 -o ic32 ic32.c`, then `echo 'TERM' | ./ic32`
**Validates against:** `ic_float.py` / `ic_ref.py` (same normal forms, identical
interaction counts).
**Status:** ✅ correct on the full term battery (24 terms, exact match) and on the
cases `ic_ref` diverges on; demonstrates optimal sharing; ~22–33 M interactions/s.

This is the step that turns the pinned semantics into a real runtime: terms packed
into 64-bit words over a flat heap, in C, so it both runs fast and compiles cleanly
to WASM later. It implements the **IC32 typed-node, floating-dup** model — the
representation `ic_float.py` pins down and HVM3 uses.

## Word layout (faithful to `SPEC.md` §2.1)

`SPEC.md` specs a 64-bit port as `addr(32) | label(28) | tag(4)`. IC32 also needs a
*substitution* flag, which I carve from the one bit `SPEC.md` leaves spare (the top
label bit):

```
 bits [63..32] addr  (32)   heap index of the target node
 bit  [31]     sub   (1)    set when this slot holds a substitution
 bits [30..4]  label (27)   DUP / SUP color  (134M colors; tests use < 2000)
 bits [3..0]   tag   (4)    VAR LAM APP ERA SUP DP0 DP1
```

**Substitution is in-place at the binder's slot** (the IC32 trick, not a side map):
a `VAR` or `DPk` term's `addr` points at its binder node's heap slot; when the
binder is consumed, the substituted term is written there with the `sub` bit set,
and reading the variable retrieves it (clearing the bit). **DUP nodes are bodyless
and float on the heap**, reached only through `DP0`/`DP1` variables, fired lazily —
which is what makes the divergent pattern terminate, exactly as in `ic_float`.

A node is a run of consecutive words (`Lam`: 1 = body slot; `App`/`Sup`: 2;
`Dup`: 1 = the duplicated value). Allocation is a bump pointer with size-classed free lists that
recycle consumed redex nodes (Phase-1 GC; erasure frees;
this prototype doesn't yet reclaim, matching the spec's "optional collect()").

## Validation — identical to the Python oracles

Driver pipes each term to `./ic32` and compares stdout to `ic_float.run`.

- **Equivalence battery (24 terms): exact match.** README examples, Church
  identity n=0..6, exponentiation `(a b)=bᵃ` for many a,b, Church-N applied to `NOT`.
- **The cases `ic_ref` diverges on (4): all terminate with the correct answer**, and
  the interaction counts match `ic_float` *exactly* (26, 27, 27, 41) — i.e. this is
  the same reduction strategy, just packed.
- **Interaction counts match Python** wherever both complete (e.g. `(9 2)` readback:
  1128 in both). Same algorithm, verified by count, not just by output.

## Optimal sharing (the headline property)

Computing the **parity of 2ᴺ** as `NOT^(2ᴺ)(FALSE)`:

| 2ᴺ | interactions |
|---|---|
| 2⁴ = 16 | 80 |
| 2⁸ = 256 | 160 |
| 2¹² = 4096 | 240 |
| 2¹⁶ = 65536 | 320 |
| 2²⁰ = 1048576 | 400 |
| 2²⁴ = 16777216 | 480 |

Interactions grow **linearly in N** (~`80 + 20N`) while `2ᴺ` grows exponentially.
Parity of 16.7 million in **480 interactions**. This is the optimal-λ-evaluation
speedup (the reason the whole HVM lineage exists), and it falls out of the runtime
unforced — the repeated `NOT` applications are *shared*, not expanded.

## Throughput

Exponentiation readback (forces an output of size `bᵃ`; reduction timed internally,
excluding process startup and stringify):

| `bᵃ` | C interactions | C ms | C M/s | py ms | speedup |
|---|---|---|---|---|---|
| 128 | 334 | 0.01 | 33 | 0.8 | 84× |
| 512 | 1128 | 0.05 | 23 | 2.8 | 55× |
| 8192 | 16540 | 0.62 | 27 | — | — |
| 59049 | 118268 | 5.08 | 23 | — | — |

55–84× faster than the Python reference where both complete. Beyond ~2000-deep
output the Python reference hits its **recursion-depth limit** (deep `normal()`),
*not* an interaction-count difference — the C runtime keeps going, handling 118K
interactions on a 59049-deep result in ~5 ms.

## Honest notes

- **This is single-node and still tree-walking** (recursive `whnf`/`normal` over the
  heap). It's the correct *packed representation* and it's fast, but it is not yet
  the redex-bag/work-queue engine `SPEC.md` describes for parallelism, nor the
  GPU/SIMD-style core HVM compiles to. Those are further steps.
- **GC, Phases 1-2.** Consumed redex nodes (App/Sup) are recycled via size-classed free lists
  (`./ic32 --gcstats`: 33-40% lower heap high-water on dup-heavy reduction), and eraser
  propagation collects directly-discarded sub-nets at APP-ERA (`./ic32 --erasestats`). Lazy
  reduction limits the latter's reach (discarded args are usually var bindings); var-indirect and
  affine-unused leaks remain (substitution-aware reclamation / compiler erasers). A long-running
  reduction can still exhaust the 16M-slot
  heap; erasure-based reclamation (`collect()`) is unimplemented.
- **Word format is `SPEC.md`'s; the node model is IC32, not `SPEC.md`'s combinator
  model.** `SPEC.md`'s uniform two-aux-port CON/DUP/ERA nodes predate the typed-node
  floating-dup model the lineage settled on. I used IC32 typed nodes (so it ports
  `ic_float` directly and validates cleanly) while keeping `SPEC.md`'s `tag|label|addr`
  word. The combinator model + `BND` boundary ports remain the basis for the
  *distribution* layer.
- **The Python recursion-limit caveat** above means the speedup numbers understate
  the gap at scale (Python simply can't run the larger cases without restructuring).

## Where this goes

1. **WASM.** Compile this with Emscripten → `ic32.wasm`, run under Node/`wasmtime`,
   and validate the WASM output against `ic_float`/`ic_ref` on the same battery. The
   word format and rules don't change — only the build target. This is the
   sovereignty/edge substrate.
2. **Distribution.** Layer the boundary-port model (`SPEC.md` §4, `p2.py`'s
   owner/Safra protocol) over this heap so redexes can cross node boundaries
   coordination-free — the distributed version of HVM's destination.
3. **Simplify `dsearch`.** General duplication now works in a real runtime, so the
   search candidates can drop the linear pair/selector workaround.

Order so far: correct simple core (`ic_ref`) → monotone workload distributed without
coordination (`dsearch`) → correct **general** core (`ic_float`) → **packed-word
runtime** (`ic32.c`, this file) → WASM build → boundary-port distribution → [&]/
OpenSentience unification.
