# Round 27, pass B2.1 — the emission split fires, and two defects behind it

**Both of your findings reproduced and fixed. All seven items of your B2.1 list done. Nothing
proceeds to `church_exp_2_2` in this round.**

Gate: grid **v1.39.0** (86 entries / 374 citations) · `lowering.mjs` **0.7.0** · negative battery
**275/275** · lowering **21/21**, eleven chain nodes all exercised, I-4c film-evidenced · derive 45/45
· realm 24/24 · bridge 48/48 · film 16/16 · pack 24/24, 0 skipped · NUL sweep 0.
`cert_id a08ee15d…` byte-identical — **thirty-third** consecutive round.

---

## 1. The two-read input binding — reproduced exactly

```
reads: 2 · term: Church 2 · inputs_sem_id: inputsSemId({x:999})
matches {x:2}: false   matches {x:999}: true
```

Your reading is the right one: the runtime is blameless, the **relation misbound its own input
identity**. It is `derivation.entry-snapshot@1` in the compiler layer, and I used the same mechanism —
`ownCanonical` on **both** arguments at entry. The template too, for your stated reason: `instantiate()`
is exported and walks it three times, so a hostile template could otherwise declare one port set and be
substituted against another. There is a falsifier for that half as well.

After: **one read**, term means x=2, `inputs_sem_id` commits to `{x:2}`.

Invariant recorded as you stated it: *the bytes `inputs_sem_id` identifies are exactly the bytes from
which instantiation derived every substituted value.* Agreed it is not a P-rung.

## 2. The vocabulary — you were right, and `identity` was the worse half

`integer → () => true` made `const(1.5)` lower successfully with `LOWERING_SEM_ID` unchanged. But
`identity` could have been made to NFC-normalize a source input name, **silently undoing the port
ruling three passes after it was made**. Definitions are data now, exactly the shape you sketched;
the vocabulary stays closed and carries no functions. Falsifiers measure that redefining `integer`,
shifting `nonnegative`'s `rhs` to −1, or making `identity` normalize each moves `lsem`.

I recorded where the trust boundary now sits rather than leaving it implicit: **the kind interpreter
is trusted code like `canonicalBytes`; what has been removed is the rule language's ability to hide
meaning.** Your answer to my question 3 is taken verbatim on the external-predicate case — a rule may
reference a core predicate only by `predicate_sem_id`.

## 3. The split — you are right that B2 tripped all four

I had written the trigger and then not looked at it. Split done:

```
program → template → CLOSED TEMPLATE → term → nf → outcome
  lowering   instantiation   emission     film   decode
```

`ctmpl-` against `tmpl-` **even at equal bytes**, for your reason: for `add(2,3)` with `{}` the two
structures are byte-identical and sharing an id would make "this was instantiated" and "this needed no
instantiation" indistinguishable. Both receipts as you specified, each verified by recomputation of
its own relation, neither filmed.

**And you were right that the split makes the verifiers cleaner** — that is now the strongest argument
for it. `verifyInstantiationReceipt` needs **no runtime canonicaliser at all**; only
`verifyEmissionReceipt` takes one, **as a parameter**, because the module that defines a relation must
not also choose the oracle that judges it. Both are exported production functions — your point that a
relation whose verification lives only in its own test suite is one nobody else can check.

## 4. I-4c is film-evidenced, and it cost nothing

Reproduced your measurement: **12 frames, all APP-LAM, terminal NORMAL_FORM**, replayed by the kernel
on two runtime classes. The case now asserts it. I recorded your qualification in the law rather than
only the brief: **this does not advance the runtime frontier** — every frame is APP-LAM at tree loci,
and the six DUP-* rules, the `d:`/`v:` loci and BUDGET_EXHAUSTED are exactly as unexercised as before.
`church_exp_2_2` remains the next substantive fixture.

## 5. One case retired, and one instrument of mine caught answering with the wrong text

`implementing-moved-neither-id` reverted the two fields B2 changed and required the B1.2.1 ids to
return. B2.1 ended its premise — the delta is no longer two fields, and keeping it would have meant
**growing an embedded copy of the module inside its own test**, at which point it stops being an
independent check. Retired; the live property is still measured by `semantic-ids-track-semantics-only`;
the B2 ids are kept in `SUPERSEDED_B2_SEM_IDS`.

And a grid assertion I wrote this round tested for the **string** `"ctmpl-"`, which also appears in
`INSTANTIATION_SEMANTICS.codomain_identity_domain` — so renaming the actual constructor's prefix left
it green. The battery caught it at `exit=0`. **This is the third consecutive round in which an
assertion was satisfied by a coincidental second occurrence of the text it was looking for** — after
`consumed_inputs` answered by the implementation field, and `implemented: false` answered by a comment
explaining the bug. I do not yet have a general defence against that class; scoping each assertion to
the block it means is working but is per-site.

## Questions

1. **Is the third occurrence a pattern worth a mechanism?** Three rounds, three assertions answered by
   a coincidental second occurrence. Options I can see: require every source assertion to name the
   block it applies to (mechanical, verbose), or assert on *parsed* structure rather than text. The
   second is a real project — `lowering.mjs` would need to be readable as data by the checker. Worth
   it, or is per-site scoping plus the battery enough?
2. **`consumed_inputs` vs an `input_footprint` identity.** Round 15's grant-vs-footprint is now
   literally present: supplied inputs (`inputs_sem_id`) and consumed inputs (`consumed_inputs`, a
   derived list with no identity). Does the footprint earn its own id at `church_exp_2_2`, or does it
   wait for an invocation environment large enough to make the distinction load-bearing?
3. **Emission and the corpus.** `EMISSION_SEMANTICS` is now the record a second ic32 emitter would
   have to conform to. Does the 24-vector conformance corpus become emission's conformance set, or is
   that a category error — the corpus tests a *runtime*, and emission produces the input to one?

## Files

- `governance/lowering.mjs` **0.7.0** — entry snapshots, `predicate_semantics`/`transform_semantics`,
  `EMISSION_SEMANTICS`/`EMISSION_SEM_ID`/`closedTemplateSemId`, both verifiers, `SUPERSEDED_B2_SEM_IDS`
- `governance/lowering_check.mjs` **21/21** — three new cases, I-4c filmed, one retired with its reason
- `governance/grid_check.mjs` — five B2.1 assertions; one of mine repaired after the battery caught it
- `governance/negative_battery.sh` **275/275** — 16 new
- `governance/invariant-grid.json` **v1.39.0** — three law revisions, predecessors kept
- `governance/round-11-ledger.md` — items 248–257
