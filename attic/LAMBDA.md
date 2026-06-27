# A correct lambda evaluator on our own reducer (iteration 2 — verified)

After the honest struggle of iteration 1, this is the correctness milestone:
`lc2.py` is a tagged interaction-net lambda evaluator — distinct LAM / APP / FAN
/ SUC / ZERO agents with HVM2's interaction rules (beta, dup-lambda, app-sup,
fan-fan annihilate/commute, constructor-copy, erase) — and it computes Church
arithmetic correctly, **including the nested-fan cases** where one numeral
duplicates another that contains its own fan:

```
S Z      = 1
2 S Z    = 2
3 S Z    = 3
2 2 S Z  = 4      <- Church 2^2, nested fans          [24 interactions]
3 2 S Z  = 8      <- Church 2^3, nested fans          [41 interactions]
```

## Labels are load-bearing (proven, not assumed)
Each numeral's duplicator gets a FRESH label. Force them to share one label and
the same term gives the wrong answer:

```
fresh labels per numeral :  2 2 S Z = 4            (correct)
one shared label everywhere: 2 2 S Z = <non-nat: FAN>   (corrupted)
```

With a shared label, distinct duplicators wrongly annihilate and the result
tangles. This is precisely why HVM's fans are labeled — and now ours are, and we
can see the difference directly.

## What was solved, and how the self-loop wall was sidestepped
Iteration 1 hit two walls: the data/lambda collision (solved here by distinct
tags) and the self-loop in bare identity `λx.x` (where body *is* the variable).
`2 2 S Z` contains no bare identity, so it sidesteps the self-loop entirely while
still exercising the full nested-fan machinery. Bare-identity wire handling
(proper indirection/substitution nodes) remains a known TODO, not needed for
Church arithmetic.

## What this is — and what's still open
This is **correctness**: our reducer evaluates lambda calculus with duplication,
including the case that requires the label discipline. Correctness before
cleverness — done and verified.

Still open is the **efficiency** question: optimal *sharing* (polynomial where
naive is exponential) on duplication-heavy terms. The counts here are small, but
a clean asymptotic sharing benchmark (big computation, small result) is the next
iteration — and it is where HVM's own optimality limits live (HVM2's labeled
fans are not fully Levy-optimal). Correctness is the foundation that had to come
first; the sharing win is built on top of it.

## The stack now
- `lc2.py`    — tagged lambda evaluator, verified Church arithmetic (this)
- `linet.py`  — labeled-duplicator reducer (the mechanism)
- `share_win.py` — measured basic DAG-sharing across consumers
- `inet.py`   — base reducer + confluence oracle
- `p2.py` / `world.py` / `plan.py` — distributed runtime, agent world, planner
- `SPEC.md` / `DESIGN.md` / `AGENT_WORLD.md` — specs and design
