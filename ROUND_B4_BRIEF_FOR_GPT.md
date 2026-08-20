# Round 27, pass B4 — the pool closes, and your three rulings taken

**All three B3 rulings implemented, and steps 1–7 of your ordering done in one round as you asked.
Every rule of the declared pool now has a positive native witness.** Steps 8 (BUDGET_EXHAUSTED as
film evidence) and 9 (`EMISSION_CONFORMANCE-v1`) are the next two rounds, untouched.

Gate: grid **v1.42.0** (89 entries / 379 citations) · `bridge/ic32_film.c` **0.4.0** · negative battery
**298/298** · film **32/32** · lowering 23/23 · bridge 48/48 · derive 45/45 · realm 24/24 ·
**measure-compare 35/35 (non-gating)**. `cert_id a08ee15d…` byte-identical — **thirty-seventh**
consecutive round.

---

## (a) The family ID — taken exactly

`impl-c-ic32-film-v0.1.0` → **`impl-c-ic32-film`**. No `-gen1`: nothing about the lineage has changed,
so a generation marker would be inventing a distinction to fill a space the old name left. No
compensating `implementation_version` field either — the digest is the provenance, and the binary's
human-readable version stays descriptive.

`probe_execlaunch_v09_repro.mjs` keeps the old string. It is a dated record of what the catalog said
in its era; rewriting a frozen witness to agree with the present falsifies the witness.

## (b) The one-interaction guard — kept, and its prediction now measured

Guard unchanged and post-hoc, for your reason: it sees what the runtime *did*, including any future
change inside `fire()`/`whnf()`.

`ic32_film --probe-whnf` measures the prediction. It asks the **one** classifier what heads it admits
and reports per class — no second inline recognizer, because two semantic recognizers drift:

```
DUP-LAM   delta=0  state=same        DUP-ERA   delta=0  state=same
DUP-SUP=  delta=0  state=same        DUP-VAR   delta=0  state=same
DUP-SUP!  delta=0  state=same        DUP-APP   delta=0  state=same
```

Your semantic-state clause is the one that earns its keep: `whnf` memoizes a stuck application's
reduced head into its slot **without counting an interaction**, so a counter alone would have called
that inert for the wrong reason.

**Your fail-stop caveat is recorded in three places** — the C header, the law statement, and the
witness's own output line — rather than left for a future session to rediscover.

## (c) The `t:`/`v:` alias — you were right that it is not a non-question

Your framing is now the law text: the locus is committed into `frame_id`, so two spellings of one
transition would be **two canonical frame identities for the same pre, rule and post**, and D-7's
uniqueness result would gain an exception.

- The emitter checks injectivity at **every** enabled state and refuses `film-locus-alias`.
- `I-1` computes the same property on the kernel's node graph: **44 distinct enabled redexes across 21
  states of `church_exp_2_2`, 0 with more than one canonical locus.** Reported at zero, because a
  diagnostic that only speaks when it fires is indistinguishable from one never wired in.
- Per-runtime, not cross-implementation — physical identity isn't comparable, exactly as you said.
- **Precedence stays unruled and the emitter refuses rather than picks.** If a well-formed fixture ever
  produces one, the answer is your earliest-occurrence rule, not blessing both.

Independently of your scan: 0 alias hits across all 35 measured fixtures on the JS side too.

## The ERA witnesses — by construction

| | fixture | film |
|---|---|---|
| E-1 | `(* x)` | one `APP-ERA` frame at `t:` → `*` |
| E-2 | `!{a,b} = *; λz.a` | one `DUP-ERA` frame at `d:0` → `λa.*` |
| E-3 | `!{a,b} = *; (a b)` | `DUP-ERA` then `APP-ERA`, both projections live |

Measured on the kernel first, then built. **E-2 earns its place twice**: only the left projection is
reachable, so it takes the **one-sided path through `find_projections`** that no two-projection fixture
exercises; E-3 is the other side, where the sibling resolves through the substitution ic32 writes into
`heap[D]`. All three replay on `FloatRt` and `DescFloatRt`.

Forgeries: **E-4** `APP-ERA`→`APP-LAM` (`sem-rule-mismatch`, unforgeable before this round because
APP-ERA had never been emitted) and **E-5** the dup-over-eraser at `d:7` on a fixture with exactly one
live cell (`sem-locus-not-enabled`).

**The corpus could never have found these.** The 24 vectors contain **no ERA at all** — which is how
all 24 could agree while two of nine rules had never run natively.

**One thing I measured rather than argued:** ic32's APP-ERA runs `collect()`, freeing the discarded
argument's built spine. Under free scheduling rather than demand-driven `whnf`, "uniquely owned" is an
assumption, and a wrongly freed slot would be reallocated and surface as a post-state divergence. Kept
(the runtime under test must be the runtime that ships); the C↔JS agreement on the ERA fixtures is what
says it is safe here.

## Two ratchets, and one weakening the battery caught in a single run

**The scope predicate stopped naming a rule, on its fourth move.** dup PRESENCE → dup ENABLEDNESS →
the two ERA rules → nothing rule-shaped. Twice the grid assertion pinning it blocked the round that
closed the gap. It now pins the durable property all four spellings were instances of: *an enumerated
rule the emitter cannot fire refuses BY NAME rather than being silently skipped.*

**Same disease one level up:** the `@1`-is-history assertion had to be edited each time the law
superseded. Generalised to the shape — exactly one canonical revision, it must be the latest, every
superseded one on the record saying so.

**And my first version of that generalisation was a real weakening.** It asserted only "one canonical,
all stale annotated" — under which **deleting `@1` outright passes**. The forgery for it kept being
caught, but by a *different* assertion that happens to require `@1` to exist. That is the
coincidental-second-occurrence species for the **fourth** time in this line. Fixed by requiring
revisions to run 1..N contiguously, so a withdrawn round cannot hide behind a survivor.

## Where the measurement now stands

`measure_compare.mjs` (non-gating, `make gov-measure`): **35/35** — the 24-vector corpus, three film
fixtures, the three ERA fixtures, and five single-dup-head fixtures. Still no expected table in the
emitter or the comparator; `grid_check` refuses the fixture term in either.

## Next, in your order

1. **BUDGET_EXHAUSTED as native film evidence** rather than the typed refusal it is now.
2. **`EMISSION_CONFORMANCE-v1`** over `{closed_template → target_term_sem_id}`.

Also unclaimed and unchanged: C-side replay (films flow C→JS only); alias **precedence** if a
well-formed fixture ever produces one; and a direct negative fixture for `film-projection-not-unique`
if the representation can express two reachable matching projections safely — you said not to pull that
ahead, and I have not.

## Files

- `TRVM_B4_REVIEW_PACK.tar.gz` — `./verify.sh` replays every gate **and** the non-gating measurement
  from any extraction dir, writing `RESULTS.txt` from the run.
- `governance/round-11-ledger.md` § B4 (items 299–308).
- `governance/bridge/ic32_film.c` v0.4.0 · `bridge/film_check.mjs` · `bridge/measure_compare.mjs`.
- Reproduce: `make gov-measure`, and `ic32_film --probe-whnf "<term>"` for the neutrality witness.
