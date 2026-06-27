# IC_REF — a correct, reference-faithful Interaction Calculus reducer

**File:** `ic_ref.py` (self-validating: `python3 ic_ref.py`)
**Status:** ✅ correct on the reference's own test suite + the bug class that broke every prior hand-rolled attempt.

## Why this exists

Across `lc2.py`, `linet.py`, and `plan.py` I kept reconstructing the interaction
rules from memory by **rewiring ports**, and kept hitting the same wall: a
*higher-order duplication* bug. Concretely, `lc2.py` computed first-order Church
arithmetic correctly but corrupted `2 NOT TRUE`-style terms (duplicating a
higher-order lambda) into `<non-nat: FAN>` — two stuck fans and a dangling wire.

The fix was not a cleverer patch. It was to **stop reconstructing and follow the
reference** (`github.com/VictorTaelin/Interaction-Calculus`, the calculus HVM3/HVM4
implement). The reference gets three things right that I wasn't doing:

1. **Substitution is a global map, not port rewiring.**
   Variables are *affine* (occur ≤ 1 time) and *globally unique*, so `x <- t` is
   literally `sub[x] = t`. No term traversal, no name-capture handling. This is
   the single biggest simplification — and the source of most of my old bugs.

2. **Every interaction is total — there are no stuck states.**
   APP-ERA, DUP-ERA, and crucially the *collapse* rules **DUP-VAR** and **DUP-APP**
   give a defined reduction for duplicating a free/stuck term (e.g. copying a free
   `S`). I had no equivalent, so those cases silently wedged.

3. **DUP-LAM wiring + label discipline.**
   Duplicating `λx.f` creates two lambdas, rebinds `x` to a *superposition* of the
   two fresh binders, and pushes a fresh DUP through the body. Distinct labels per
   duplication keep `DUP-SUP` from wrongly annihilating when you duplicate a term
   that itself contains duplications (the heart of correct exponentiation).

The rules and `whnf`/`normal` drivers are transcribed one-to-one from the spec
pseudocode. No improvisation.

## What's verified

Run `python3 ic_ref.py`. It checks:

| Test | Result |
|---|---|
| Reference Ex5 ("tests all interactions") `((λf.λx.!{f0,f1}=f;(f0 (f1 x)) NOT) TRUE)` | `λa.λb.a` in **exactly 16 interactions** — matches the reference's stated count |
| Reference Ex0, Ex3, Ex4 | match (Ex4 correctly yields a superposition `{λr.r,λs.s}`) |
| Church identity `n → n` | ✅ n = 0..6 |
| **Exponentiation `(a b) → bᵃ`** (higher-order duplication) | ✅ (2 2)=4, (3 2)=8, (2 3)=9, (2 4)=16, (3 3)=27, (4 2)=16 |
| **Church-N applied to `NOT`** (the Ex5 pattern, generalized) | ✅ correct parity for N = 2..5 |

The middle two rows are the exact computations that corrupted `lc2.py`. They now
reduce correctly.

> Note on Ex1: the fetched README *renders* the result of
> `(λb.λt.λf.((b f) t) λT.λF.T)` as `λt.λf.t`, but careful hand-evaluation (and
> this reducer) give `λt.λf.f` — `((b f) t)` with `b = λT.λF.T` selects `f`. That
> README line has a rendering artifact; Ex5 matching exactly (result **and** the
> 16-interaction count) is the authoritative correctness signal.

## What this is and isn't

- **Is:** a correct *semantic oracle* for the Interaction Calculus, in ~250 lines
  of dependency-free Python — parser, the 8 interaction rules + 2 collapse rules,
  WHNF/normal-order drivers, stringifier. Correct on higher-order duplication.
- **Isn't:** fast or low-level. It uses Python objects and a dict for `sub`, not
  the packed 32/64-bit tagged words HVM uses (`VAR`/`LAM`/`APP`/`SUP{L}`/`CX{L}`…).
  Speed was never the point of *this* file — correctness was. The packed memory
  layout is a separate, mechanical port once the semantics are pinned down (which
  they now are).

## The bridge to what's next

This was **step 1** of the plan: get a correct single-node engine so we stop
fighting reducer bugs. With the semantics pinned:

- **Step 2 — distribution.** Put the coordination-free layer (`p2.py`'s
  boundary-owner protocol + Safra termination detection) over this engine, with
  **superposed search** as the workload. Program/proof search is *monotone*
  (found solutions only accumulate) ⇒ coordination-free by CALM ⇒ the ideal fit
  for the boundary-port model. This is the distributed version of HVM4's
  destination (parallel proof/program search), which is the axis HVM itself isn't
  building.

- **Eventual JS/WASM port.** The packed-word version of *these exact rules* is
  what compiles cleanly to WASM for the sovereignty/edge story. The semantics in
  this file are the spec that port must match — `ic_ref.py` becomes the
  conformance oracle the WASM build is tested against.

The hand-rolled-bug era is closed. From here we build *on top of* a known-correct
core instead of repeatedly rediscovering why port rewiring breaks.
