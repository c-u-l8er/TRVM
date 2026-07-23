# IC_FLOAT — the floating-dup reducer (removes ic_ref's one limitation)

**File:** `ic_float.py` (self-validating: `python3 ic_float.py`)
**Status:** ✅ agrees with `ic_ref` on every terminating case tested (23 terms); ✅
terminates correctly on the 4 cases `ic_ref` diverges on.

## The problem it fixes

`ic_ref.py` is correct but uses a **body-carrying** representation: each `DUP`
stores a body, and reaching it **eagerly** reduces the duplicated value and pushes
the duplication through the whole structure. That loops forever on one pattern —
*duplicate a higher-order numeral, then apply a copy of it to another higher-order
lambda*:

```
!&8{na,nb} = church2 ; ((na NOT) FALSE)       -- ic_ref: never terminates
```

We had been routing around this in `dsearch.py` by keeping numerals linear (the
pair + dup-free-selector trick). That workaround is now unnecessary.

## What's different

This follows the **IC32** design from the reference README:

- **No `DUP` node in the AST.** A duplication `!&L{a,b}=v; K` becomes a `DupNode`
  that *floats on the heap* holding only `v`. The names `a`,`b` become projection
  variables `Dp(node,0)` / `Dp(node,1)` that appear in `K`. The bodyless,
  floating dup is exactly what the README specifies: `λx.!&0{x0,x1}=x;&0{x0,x1}`
  and `!&0{x0,x1}=x;λx.&0{x0,x1}` are stored identically.

- **Lazy, incremental firing.** A `DupNode` fires only when one of its projection
  variables is actually demanded, and does **one split at a time**. The first
  demand reduces `v` to WHNF, produces the two halves — whose sub-parts are again
  *lazy* `Dp` variables — caches them on the node, and returns the demanded side;
  the sibling variable later picks up the other half.

That laziness is the entire fix. The duplicated structure is never eagerly walked,
so duplicating a numeral and applying one copy to `NOT` reduces the numeral only as
far as each demand requires, and terminates.

## Validation

`python3 ic_float.py` runs two checks:

1. **Equivalence sweep (23 terms).** Against `ic_ref` as oracle — the 5 README
   examples, Church identity n=0..6, exponentiation `(a b)=bᵃ` for several a,b,
   and Church-N applied to `NOT`. *All agree.* (Same canonical normal forms.)

2. **Divergent-pattern cases (4).** Each duplicates a higher-order numeral and
   applies a copy to `NOT`:

   | term | `ic_ref` | `ic_float` |
   |---|---|---|
   | `!&8{na,nb}=church2; ((((na NOT) FALSE) A) B)` | diverges | `B` ✅ |
   | dup church2, both copies→NOT, project NOT²(FALSE) | diverges | `λa.λb.b` ✅ |
   | dup church2, both copies→NOT, project NOT²(TRUE) | diverges | `λa.λb.a` ✅ |
   | dup **church3**, both copies→NOT, project NOT³(FALSE) | diverges | `λa.λb.a` ✅ |

   *All four:* `ic_ref` diverges, `ic_float` terminates with the correct answer —
   including using **both** copies and a deeper numeral.

## Honest notes

- **Interaction counts aren't lower here.** On the terminating arithmetic cases
  `ic_float` records *more* interactions than `ic_ref` (e.g. exponentiation `(2 2)`:
  21 vs 17). The two representations do different bookkeeping — `ic_float` makes
  the collapse rules (DUP-VAR/DUP-APP, copying a free `S` step by step) and APP-SUP
  dups explicit, which `ic_ref`'s eager body-carrying version folds differently. So
  the counts are **not** directly comparable as a speed metric, and neither should
  be read as "more efficient." The invariant that matters is that they produce the
  **same normal forms**. `ic_float`'s value is *generality* (it handles what
  `ic_ref` can't) and being the correct substrate to compile — not a step count on
  toy terms.

- **Still a tree-walking interpreter.** This is the correct *representation*, not
  the fast *runtime*. HVM packs each term into a 32/64-bit tagged word
  (`VAR`/`LAM`/`APP`/`SUP{L}`/`CX{L}`/`CY{L}`…) with the heap as a flat array. That
  packing is the next, mechanical step.

## Where this goes

`ic_float` is now the **conformance spec for the WASM port**. The plan:

1. **Port to packed words → WASM.** Re-express these exact rules over a flat heap
   of tagged words (the IC32 layout), in C-via-Emscripten or Rust/Zig→WASM. Test
   the WASM output against `ic_float` (general) and `ic_ref` (simple oracle) on the
   same term battery. This is the sovereignty/edge substrate.

2. **Simplify `dsearch`.** With general duplication available, the search
   candidates no longer need the linear pair/selector encoding — they can be
   duplicated directly. (The coordination-free distribution result is unaffected;
   only the per-node encoding gets simpler.)

3. **OpenSentience mapping.** Cheap symbolic agents as IC sub-nets on the WASM
   engine; `&reason` governance verified *on* that engine; coordination-free across
   browsers/edge via the CRDT + boundary-port model.

Order so far: correct simple core (`ic_ref`) → monotone workload that distributes
without coordination (`dsearch`) → correct **general** core (`ic_float`, this file)
→ packed-word WASM runtime → unification with [&]/OpenSentience.
