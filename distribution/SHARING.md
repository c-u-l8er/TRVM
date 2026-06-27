# Sharing in our reducer — measured, with an honest correction

## The correction I owe
Two turns ago I concluded the reducer "can't share, that's HVM's job." That was
wrong on two counts. First, `plan.py` showed no sharing because those plans were
*independent* (each leaf its own outcome, trivial scorer) — there was nothing
shared to amortize, so superposition only added tree overhead. Second, I never
actually gave the reducer a shared reducible computation and measured it. Now I have.

## The measurement (`share_win.py`, verified correct)
A shared computation = a chain of L pass-through stages around a tiny value z
(cost ~2L interactions, result = z). Shared to N consumers via a fan vs. N
independent chains:

| L | N | shared | separate | saved | ratio |
|--:|--:|-------:|---------:|------:|------:|
| 100 |  8 | 275 | 1640 | 1365 | 5.96x |
| 100 | 16 | 355 | 3280 | 2925 | 9.24x |
| 100 | 32 | 515 | 6560 | 6045 | 12.74x |
| 200 | 16 | 555 | 6480 | 5925 | 11.68x |

`saved` is (N-1)*2L every row: **the chain is evaluated exactly once and shared.**
The shared run scales as `2L + O(N)` (compute once + linear result-delivery); the
separate run as `N*2L`. Ratio approaches N as the shared computation grows.

Correctness is checked first: `chain(8)` on `val(2)` returns `CON(e,CON(e,e))` — z
unchanged — in 16 interactions. The numbers are on a correct net, not a malformed one.

## What this is, precisely (no overclaiming)
This is the **basic DAG-sharing** interaction nets do *without labels*: a reduced
result fanned out is computed once. It needs no `linet.py` machinery — plain
combinators already do it. Its direct consequence for the agent VM: plans that
share a common prefix get the prefix evaluated once and fanned to the plans that
share it. That is "cheap planning," grounded at the substrate — and it's exactly
what `plan.py` couldn't show, because those plans shared nothing.

## What this is NOT yet (the real frontier)
The hard sharing — the exponential-to-polynomial win — is when the *shared
computation itself contains duplication* (Church numerals, recursion, nested
fans), where plain unlabeled fans collide incorrectly. That is what the **labeled
duplicators** in `linet.py` are for; the collision test proved labels change the
reduction (same-label annihilate vs different-label commute). But having the
mechanism is not the same as the correct *label-management discipline* (fresh
labels on nested duplication, matched dup/sup pairs) that makes optimal sharing
both correct and complete. That discipline is the genuinely hard core of HVM —
where HVM itself has had bugs — and it is the next milestone, not a solved thing.

## Status
Banked, honestly: (1) measured basic sharing in our reducer; (2) the labeled-fan
mechanism for advanced sharing. Remaining: correct label management to get the
duplication-heavy (Church-numeral) sharing — the real proof that this is a better HVM.

Files: `share_win.py` (this), `linet.py` (labeled reducer), `inet.py` (base reducer +
confluence oracle), `plan.py`, `world.py`, `p2.py`, `SPEC.md`.
