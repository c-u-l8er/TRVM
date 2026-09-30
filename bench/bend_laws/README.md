# Laws 5 and 23 in Bend — the §7 experiment of `TRVM/BEND_LAWS_COMPARISON.md`

**2026-09-18.** `BEND_LAWS_COMPARISON.md` §7 named the bounded move: give each CANONICAL law that *is* a pure
statement a machine-checkable form beside its battery, and named Law 5 and Law 23 as the two that admit one.
This directory does that for both, against Bend 2.0.4's own checker, with one mutant each that the checker
must refuse. `./run.sh` is the gate; it prints its own verdict.

Measured on this laptop, 2026-09-18:

```
bend 2.0.4
PASS  PROOF5.bend       (All terms check.)
PASS  PROOF5_BAD.bend   (refused, as it must be)
PASS  PROOF23.bend      (All terms check.)
PASS  PROOF23_BAD.bend  (refused, as it must be)
verdict: 4/4 hold, 0 failing
```

## What each law became

**Law 5** — *a numeric threshold may change representation, never meaning.* Enforced in the tree by the
period-33 regression and the one-hot/binary counter equivalence. Here the smallest counter re-encoding:
`encode(n) = Nat.double(n)`, `decode` halves. The law (`LAW5.bend`):

```
law law5_roundtrip: for n: Nat {C.decode(C.encode(n)) == n : Nat}
```

proven by induction in `PROOF5.bend` (the guide's `add_zero` shape: base case `{==}`, step case one rewrite
with the induction hypothesis, then `{==}`). The mutant `decode_sat = Nat.min(decode(n), 33n)` is the
failure that earned the law — a count that saturates where a count was meant. `PROOF5_BAD.bend` states the
same law over it with the same proof and is **refused at the step case**: the checker prints that
`Bool.pick(..is_lt(..., 32n)..., 1n+decode(..), 33n)` does not compute to `1n+p`. That is the right reason:
the saturating decoder's step is not `1n +` its predecessor.

**Law 23** — *a memoization key must include every dimension over which the memoized generator ranges.*
Four dimensions here (`depth, size, profile, policy`). The first form, key-equality implies input-equality,
was written and refused by Bend's **affinity rule** — the equality proof `e` was consumed four times (one
`Equal.cong` per field) and a proof term is affine like any other value. The restatement is the better law
anyway: a key is complete exactly when the input can be read back from it (`LAW23.bend`):

```
law law23_complete_key: for d: C.Dims {C.unkey(C.key(d)) == d : C.Dims}
law law23_key_injective: for a b: C.Dims for e: {C.key(a) == C.key(b) : C.Key} {a == b : C.Dims}
law law23_key2_aliases: {C.key2(Dims{1n,1n,0n,True}) == C.key2(Dims{1n,1n,1n,False}) : C.Key2}
```

The first closes by `{==}` after a match; the second is one `Equal.cong` with `unkey` as the function, which
uses `e` once; the third is the aliasing witness in the shape the async-memokey bug was felt (two inputs
differing in profile and policy share the incomplete key), and it closes by computation. The mutant
`PROOF23_BAD.bend` claims the incomplete `key2` is complete via the best inverse that exists (`unkey2`
must invent `0n, True{}` for the two dropped fields) and is **refused**: expected `Dims{a, b, c, e}`,
observed `Dims{a, b, 0n, True{}}`. Again the right reason: the dropped dimensions cannot be recovered.

## What this shows, and what it does not

- **§7's claim is now measured, not argued:** Laws 5 and 23 have a machine-checkable form, an agent can
  iterate against it in a loop, and a wrong implementation is refused with the offending term printed.
  Cost: about an hour and four checker round trips, three of them Bend syntax and discipline
  (a `match` may not scrutinize a computed value — give it its own def; mutual recursion is forbidden, so the
  first mutant was rewritten as `Nat.min`; a proof term is affine).
- **It is an instance of each law's pure core, not the law.** Law 5's battery is the period-33 regression
  and the compiler-wide one-hot/binary equivalence; this is a doubling encoding. Law 23's witness is a patch
  against a real memo key; this is a four-field record. Neither Bend file replaces a battery or a citation in
  `TRVM/LAWS.md`; they sit *beside* them, which is what §7 asked for. Promotion of anything here is a human
  act, as for every CANONICAL law.
- **One forgery each is not the tree's negative-battery standard** ("every forgery it was written against").
  It is the first forgery, chosen to be the earning failure's shape.
- **Bend's trusted base is unchanged** (`Type : Type`, no positivity check, `bend.ts` ahead of its Lean
  mechanization, no published rejection battery). Two refusals here are two data points on the checker's
  rejection behaviour, in public, which §6 said nobody had priced.
- **Laws 4, 6, 13 and 26 were not attempted** and should not be: they are about measurement regimes,
  serialized runtime state, protocol channels and injected faults, none of which is a term that normalizes.

## Files

| file | role |
|---|---|
| `law5_code.bend`, `law23_code.bend` | the code the laws range over, including each mutant |
| `LAW5.bend`, `LAW23.bend` | the laws, open claims (Bend's `LAWS.bend` role) |
| `PROOF5.bend`, `PROOF23.bend` | the proofs (Bend's `PROOF.bend` role); must print `All terms check.` |
| `PROOF5_BAD.bend`, `PROOF23_BAD.bend` | the same laws over the mutants; must be refused |
| `run.sh` | the gate: all four outcomes or exit 1 |

Bend at `~/.bend/bin/bend` (override with `BEND=`), telemetry off, Bun on `PATH` from `~/.bun/bin`.
