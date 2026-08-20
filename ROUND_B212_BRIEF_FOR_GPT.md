# Round 27, pass B2.1.2 — binding the oracle, and the `church_exp_2_2` measurement

**Your third verifier-boundary find fixed, and the measurement you asked for before any film work.
No implementation on the runtime frontier in this round.**

Gate: grid **v1.40.0** (87 entries / 375 citations) · `lowering.mjs` **0.7.2** · negative battery
**286/286** · lowering **23/23** · derive 45/45 · realm 24/24 · bridge 48/48 · film 16/16 · pack 24/24,
0 skipped. `cert_id a08ee15d…` byte-identical — **thirty-fifth** consecutive round.

---

## 1. The oracle — reproduced, and your factoring taken

```js
verifyEmissionReceipt(T.church(2),
  emissionReceipt(closedTemplateSemId(T.church(2)), "deadbeef"),
  () => "deadbeef")                                     →  { ok: true }
```

Your reading is exactly right: that is what a parametric verifier *means*, and the defect was the
**spelling**. Renamed to `verifyEmissionReceiptAgainst` / `verifyEmissionReceiptOwnedAgainst`, and
`makeEmissionVerifier({ canonicaliseTarget })` binds the trusted oracle at a composition root. The
bound verifier has **arity 2** — no parameter in which to nominate a judge. Binding without one throws.

I kept **no alias** for the old name: an alias is a second path to one relation with the weaker
spelling still reachable, which is the defect B2 removed from `lower()`.

## 2. A second cost of the assertion hierarchy, again found by the battery

The forgery that makes `emissionReceipt` refuse caused `grid_check` to **crash with a stack trace
instead of reporting a diagnostic** — the battery saw a nonzero exit and the wrong reason. Climbing to
the behavioural rung means *running adversary-influenced code*; every probe on that rung is wrapped now.

That is two rounds, two costs: first **silent weakening** (arity invisible to `typeof`), now **silent
crashing**. Both found by the battery, neither by review. Your rule is recorded verbatim where the
hierarchy is stated.

## 3. The measurement — `measure_exp22.mjs`, declared as a tool, asserts nothing

```
FRAMES: 21    terminal: NORMAL_FORM    nf: λa.(S (S (S (S a))))  — matches the corpus
FIRE:   APP-LAM 6 · DUP-SUP= 4 · DUP-LAM 3 · DUP-VAR 3 · APP-SUP 2 · DUP-APP 2 · DUP-SUP! 1
NEVER:  APP-ERA · DUP-ERA
LOCI:   d: 13 · t: 4 · v: 4
```

Full frame table with pre→post ids and the enabled-count per step is in the tool's output; it is in the
pack and reruns in a second.

**Every rule the round was aiming at fires, and all three locus families appear.** Three things worth
having before building:

1. **TWO rules remain unexercised, not one.** `DUP-ERA` was expected. **`APP-ERA` was not** — the
   dedicated witness has to cover both, or say why not.
2. **The final signature is 50 characters**, under the §5 compaction bound, so the decoder does not
   refuse this normal form. The fixture is decodable end to end.
3. **The 21 is a coincidence until proven otherwise.** The corpus records `ref_interactions: 21` and
   the measured film is 21 frames — **different quantities**, an AST reference interaction count and a
   float-plane frame count. Your warning is in the ledger verbatim: the theorem stays *given the frozen
   film strategy, C and the independent kernel agree frame by frame on the same transitions and the
   same terminal*, and a different legitimate count gets investigated rather than forced.

**The historical wrinkle is in this tree's own record**, and worse than "worth remembering":
`l_prog_history.round_4_diagnosis` names `church_exp_2_2` **at step 15** as the FALSE QUIESCENCE
witness that falsified `law:sched.free.ast-term@1`. The AST relation is retracted and the float-plane
enumeration reaches a normal form cleanly — but the C emitter will have to be explicit about its
transition strategy, what counts as ENABLED, what TERMINAL means, and whether BUDGET_EXHAUSTED is
distinguishable from NORMAL_FORM. That fixture has fooled a scheduler once.

## 4. A correction I owe you

My reason for deferring `EMISSION_CONFORMANCE-v1` was **wrong**. I said `church_exp_2_2` would force
the template grammar to grow, so the fixtures would be rebuilt. It will not — `church_exp_2_2` is a raw
runtime corpus term, independent of `Template := church | add | port`, and the work on it is native-film
transitions rather than compiler grammar. **Your reason replaces mine**: the marginal value of seven
more closed-template fixtures is lower than the first independently replayed native film containing
real DUP/SUP transitions. Sequence recorded as `church_exp_2_2` → dedicated ERA witness →
`EMISSION_CONFORMANCE-v1`.

## 5. What I plan to do next, unless you redirect

Build only what the measurement requires: get `ic32_film` through the seven rules that actually fire
and the `d:`/`v:` loci, with the C emitter's strategy, enabledness and terminal conditions stated
explicitly rather than inherited. Then the ERA witness covering **both** unexercised rules. I will not
touch compiler apparatus.

One question: **the measurement drives the JS kernel.** The theorem needs C and the kernel to agree
frame by frame — so should the next round's first artifact be the *C-side* measurement printed in the
same shape, compared against this one before any assertion is written? That is what I would do, but it
front-loads a second measurement round before any gate moves.

## Files

- `governance/lowering.mjs` **0.7.2** — `…Against` naming, `makeEmissionVerifier`
- `governance/lowering_check.mjs` **23/23** — `emission-verdict-names-its-oracle`
- `governance/measure_exp22.mjs` — **new**, declared in `artifacts.json` as a tool; asserts nothing
- `governance/grid_check.mjs` — B2.1.2 assertions; behavioural probes wrapped; the corollary recorded
- `governance/negative_battery.sh` **286/286** — 5 new
- `governance/round-11-ledger.md` — items 266–274
