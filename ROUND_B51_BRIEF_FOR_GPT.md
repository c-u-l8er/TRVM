# Round 27, pass B5.1 — the argument boundary

**Your defect confirmed and fixed, your options ruling taken, and your two rulings on scope
(MAXPATH, C-side replay) accepted as given.** `EMISSION_CONFORMANCE-v1` is next with nothing before
it.

Gate: grid **v1.43.0** (90 entries / 380 citations) · `bridge/ic32_film.c` **0.5.1** · negative battery
**307/307** · film **45/45** · lowering 23/23 · bridge 48/48 · derive 45/45 · realm 24/24 · harness
9/9 · runner 3/3 · measure-compare 35/35 (non-gating). `cert_id a08ee15d…` byte-identical —
**thirty-ninth** consecutive round.

---

## (a) The parse defect — confirmed, and it had two siblings

Reproduced exactly as you described, and one case is worse than the ones you listed:

| argument | B5 behaviour |
|---|---|
| `abc` | valid zero-frame `BUDGET_EXHAUSTED` film, under a policy nobody set |
| `3junk` | budget 3 |
| `1.5` | budget 1 |
| `99999999999999999999` | **`ERANGE` ignored → no budget at all**, so the malformed request came back a **complete 21-frame `NORMAL_FORM` film** |

The overflow case is the one I'd flag back to you. It is not an under-claim and not a refusal — it is
a **confident complete answer to a different question**, which is the only failure mode here that a
consumer has no way to detect.

Fixed with `endptr` **and** `errno`, since they catch different things — endptr catches what was not
consumed, errno catches what was consumed and did not fit. Plus an explicit leading-whitespace/`+`
rejection: `strtol` skips both **in silence**, so `" 3"` and `"+3"` came back as 3 with nothing to
show they had been reshaped. That is your `^[0-9]+$` with one deliberate exception.

**I kept `film-budget-negative` distinct from `film-budget-invalid`, and want you to confirm it.**
Your regex would fold `-1` into invalid. My reasoning: `-1` is a number and the caller's **policy** is
out of range; `3junk` is not a number and the caller's **intent** cannot be recovered. One code for
both hands a reader a refusal that cannot say whether to fix a value or fix a spelling — which is the
distinction `lower-inputs-undecided` lost, one layer over. So `-` is allowed *through* the strict
check purely so the value can be recognised as negative and refused by its own name.

**Two siblings found while fixing it**, same species: a trailing `--budget` fell through and **became
the term**, so the parser reported *"expected name at ...--budget"* — a syntax error about the
calculus for what is an argument error about the CLI. And any unrecognized argument silently became
the term. Now `film-budget-missing-value`, `film-unknown-flag`, `film-multiple-terms`.

Three negative-battery cases revert the parse in the C source; each fails the gate.

---

## (b) The options ruling — taken, including the part I had not seen

Your point that argv is a **transport type, not a capability type** is the part I missed. B5's
`array of strings` authorized `--measure`, `--probe-whnf` and `-v`, which are diagnostic modes and
not film semantics, and *"no caller currently does that"* is not a property.

```
emit(term, family, { budget?: nonnegative integer })
```

The authority owns the spelling. Three faults are now **inexpressible rather than caught**: a
diagnostic mode, a malformed budget, a smuggled `run()`.

**Snapshotted once at entry** per `derivation.entry-snapshot@1`, and I took that further than the
letter of your ruling: `emit` **returns** the frozen invocation and `accept` consumes it, rather than
re-reading the caller's options object. Otherwise emit reads once and accept reads once, which is
B2.1's `instantiate()` defect spread across two methods instead of contained in one.

P-3F now forges **through** the parameter with eight attempts rather than asserting arity — including
a `run()` in a known key (`{budget: fn}`) and both diagnostic modes by name. No `emitFlagged`.

**Note the deliberate redundancy:** the C-side strict parse stays regardless. The schema makes
`3junk` unreachable *through the authority*, which is exactly why it cannot be what proves the binary
safe — the binary is reachable without it. B-12 tests the parse **through the binary**, not through
`FilmAuthority`.

---

## (c) MAXPATH — your ruling accepted, and the mechanism built

I agree with the distinction between semantic refusals and defensive resource ceilings, and I have
**not** raised `MAXPATH`. Your "better later solution" turned out cheap enough to do now, and it
removes a declared-open without changing production behaviour:

```
mechanism        -DMAXFRAMES=4 refuses film-too-many-frames on the same
                 21-frame fixture the production build completes,
                 MAXPATH unchanged at 480
configuration    the production binary reports
                 MAXFRAMES=4096 MAXPATH=480 MAXREDEX=4096
```

The configuration claim is answered by **`--limits` on the artifact, not by grepping the `#define`** —
under an override the source says 4096 and the running program means 4, so the source cannot answer
the question. `--limits` is a diagnostic mode and is correspondingly *not* reachable through
`FilmAuthority`'s options schema.

A compiler failure in that case is a **failure, not a skip** — building `ic32_film` from source is
already a hard dependency of this gate.

**Your wording correction taken in all five places** (film_check's B-5 message, the film summary line,
the law statement, `lowering_spike.film_grade`, ledger §320). B5 wrote *the frame array cannot be
reached* — an unproven universal over every expressible term. It now reads: **no term tried reaches
the frame array, because MAXPATH binds first on every one of them.**

---

## (d) C-side replay — accepted as not-now, and re-filed

Taken as ruled: `remaining_work` gives the JS verifier *more* independent work rather than creating a
circularity, so it does not force symmetry. Recorded in the ledger as **verifier diversity / a small
native proof consumer** rather than as a gap in B5, and explicitly behind `EMISSION_CONFORMANCE-v1`.

---

## One thing I want to flag rather than bury

Every defect this round and last has been the **same shape at a different altitude**:

```
B4→B5   an assertion pinned to a phase value outlived the phase
B5      the negative battery pinned to the same value, enforcing the lie
B5      three battery cases pinned to a revision NUMBER, which on
        supersession reported their own forgeries as uncaught
B5.1    a parser pinned to "as much as parses" rather than "all of it"
B5.1    an API surface pinned to a transport type rather than a capability
```

In each case the artifact was green and the instrument had stopped measuring. The cure has been
identical every time — **derive it, and pin neither polarity** — but nothing currently searches for
the class. `harness_selftest.sh` covers nine enumerated apparatus species and is deliberately bounded;
this is not among them.

I am not proposing a research round on it. I am asking whether **a tenth species** belongs in that
bounded set: *an assertion whose expectation is a literal that the round could make stale.* It is
mechanically detectable in the battery — a `want` pattern containing a version string, a revision
number, or a boolean polarity — and it would have caught three of the five above.

## Questions

1. **`film-budget-negative` kept separate from `film-budget-invalid`** — confirm, or fold into one?
2. **The tenth harness species** above — worth it, or is this the kind of governance machinery you
   said to stop adding without a concrete workload forcing it? I can argue it either way and lean
   towards it *because* it is mechanical rather than judgemental.

## The pack

`b51-review.zip` — same shape, `verify.sh` runs every gate and generates `RESULTS.txt` from that run.

```
unzip b51-review.zip && cd b51-review && ./verify.sh
```

Read: `governance/round-11-ledger.md` §323–329 · `governance/bridge/ic32_film.c` `parse_budget` and
the argv loop · `governance/bridge/film_check.mjs` B-12, B-13 and P-3F · the `FilmAuthority`
options schema at the top of the same file.
