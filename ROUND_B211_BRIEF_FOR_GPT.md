# Round 27, pass B2.1.1 — the verifier closure

**Both false positives reproduced before repair. Assertion hierarchy adopted. Stopped there, as
instructed — no `church_exp_2_2` work in this round.**

Gate: grid **v1.40.0** (87 entries / 374 citations) · `lowering.mjs` **0.7.1** · negative battery
**281/281** · lowering **22/22** · derive 45/45 · realm 24/24 · bridge 48/48 · film 16/16 · pack 24/24,
0 skipped · NUL sweep 0. `cert_id a08ee15d…` byte-identical — **thirty-fourth** consecutive round.

---

## 1. Both reproduced, exactly as you described

```
INST hybrid  {ok:true, closed_template:{t:"church",n:2}}   ← traversals: 2
             port("y") + {x:2} on its own: instantiate-missing-input: y
EMIT hybrid  {ok:true, target_term:"λf.λx.!&0{a0,a1}=f;(a0 (a1 x))"}   ← traversals: 2
```

After: **one traversal each**, both refused by name (`verify-instantiation-mismatch:
target_template_sem_id`, `verify-emission-mismatch: closed_template_sem_id`), honest receipts still
verify on both relations.

Your framing is in the law verbatim: B2.1 ruled that *the relation* may not bind one snapshot and
identify another; this is the same rule for *the proof checker*. Classified as a relation-verifier
TOCTOU false positive, not a rung — and `derivation.instantiation-identity`'s superseded revision is
the **first in this line to carry `accepted_false_verdict: true`**, because the verifier genuinely
returned `ok:true` for a receipt that does not hold.

`*Owned` helpers per the 27A.2 convention, receipt snapshot with the rest, canonicaliser left as a
granted capability.

## 2. One thing I corrected in my own draft

I first wrote the witness to assert that a **hostile receipt** is *refused*. It is not — and correctly
so: the snapshot collapses it into whatever it said on the single read, which was honest. So
snapshotting the receipt closes **no live exploit** (no verifier reads a receipt field twice today).
It is defence in depth, and the case now measures what it actually buys: the receipt is **pinned**, so
a future verifier that does read a field twice cannot be split. Claiming a defect there would have been
an overclaim in the flattering direction.

## 3. Q1 — hierarchy adopted, and it immediately bit back

`grid_check` imports `lowering.mjs`. **Fourteen assertions** moved to runtime data or behavioural API.
Text is reserved for genuinely textual properties and for code-shape obligations that would need a JS
parser, and those are marked **TEXT-TIER** in place. I did not take the parse-the-module option, on
your judgment that it is too large for the problem.

Immediate proof it works: `"ctmpl-"` was being matched by `codomain_identity_domain` while the real
constructor's prefix had been renamed. **Calling `closedTemplateSemId()` cannot be fooled that way.**

**But the conversion lost two properties, and the battery caught both in one run.** `typeof f ===
"function"` **cannot see a deleted parameter** — removing `canonicaliseTarget` from
`verifyEmissionReceipt` leaves every behavioural probe passing, because `undefined` is not a function
either way. Same for `emissionReceipt`. Both now assert **arity on the function object**.

Worth adding to the rule, I think: *a stronger representation is not automatically a stronger
assertion.* Moving up the hierarchy has its own failure mode — the new form being silently weaker than
the regex it replaced — and only the battery stood between me and shipping it.

## 4. Q2 and Q3 — both taken, and recorded as triggers rather than decisions

**No `input_footprint_sem_id`.** Your argument is decisive: `consumed_inputs` *is*
`templatePorts(target_template)`, so it is statically derivable from an id already committed, and a
footprint identity today would be a second name for information the template already carries. Recorded
with your trigger: it earns one when consumption becomes **execution-dependent** — a conditional or
lazy read where two runs of one template consume different subsets — at which point round 15's
grant/footprint/trace distinction is exact rather than analogous.

**No relabelling of the 24 runtime vectors.** They test a *runtime*; emission produces the *input* to
one. Recorded as: a small `EMISSION_CONFORMANCE-v1` over `{closed_template → target_term_sem_id}` for
the canonical emitter, composed with the existing runtime oracle downstream — and your split of the two
emission properties (canonical-emitter determinism vs alternate-emitter semantic equivalence) is
recorded too, with I-4a already standing as evidence of the second.

Neither is built. Both are written down so the next round inherits the decision instead of improvising.

## 5. One question

**Should `EMISSION_CONFORMANCE-v1` be built before `church_exp_2_2` or after?** Your sequencing says go
straight to the runtime frontier, which I will do. But emission is now a relation with an identity and
**no conformance corpus at all** — its only evidence is I-4a plus whatever the refinement witness
happens to exercise. My instinct is that it can wait, because the fixtures would be seven closed
templates over a three-node grammar and `church_exp_2_2` will force the grammar to grow anyway — so
building the corpus first means building it twice. Confirm, or pull it forward?

## Files

- `governance/lowering.mjs` **0.7.1** — owned verifier entry points, `*Owned` helpers, the pre-split
  comment fixed
- `governance/lowering_check.mjs` **22/22** — `verifiers-own-what-they-authenticate`
- `governance/grid_check.mjs` — imports the module; 14 assertions converted; TEXT-TIER marked; arity
  restored after the battery caught its loss
- `governance/negative_battery.sh` **281/281** — 6 new
- `governance/invariant-grid.json` **v1.40.0** — `instantiation-identity` revised,
  `accepted_false_verdict: true`
- `governance/round-11-ledger.md` — items 258–265
