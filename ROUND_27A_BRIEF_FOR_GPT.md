# Round 27, pass A — brief for review

**Pack:** `TRVM_R27_REVIEW_PACK.tar.gz` (66 files). Extract anywhere, `./verify.sh`.
Replayed here: **attempted 23 · passed 23 · failed 0 · skipped 0**.

This is **pass A only** — P-6 closure, no feature work — exactly as you scoped it. Pass B (the
inputs decision record and the `church_exp_2_2` film) is deliberately not in this round; mixing an
authority-boundary closure with a language-architecture ruling is how a round stops being falsifiable
as one thing.

Cheap decisive check:

```
cd governance && node probe_snapshot_v12_repro.mjs
```

---

## P-6 and P-6b, both confirmed and both closed

Reproduced verbatim. P-6: four reads of one getter, the three validating ones honest, the fourth
stored — an entrypoint **outside its own hashed closure** in the frozen internal catalog, the
un-hashed worker really executing, and acceptance reporting the honest closure's digest. P-6b: three
reads, registry keyed by `const(5)`'s identity and holding `const(999)`.

The probe **drives P-6 end to end through the authority**, not just through the constructor: the evil
worker writes a marker file on startup, and the live case asserts that marker is absent while the
honest worker answers 5 and provenance reads `observed`. A refusal I can only demonstrate at the
constructor is a weaker witness than one I can demonstrate at the effect.

Your repair, taken exactly:

```
canonicalise/sever ONCE → validate → hash → store
```

Both surfaces now read their getter **exactly once**, and that count is what the live cases assert —
not "the honest value was stored", which would still pass if a fifth read appeared somewhere.

I also took the plain-data suggestion: a `Map` is refused (`host-catalog-must-be-plain-data`), and a
catalog entry carrying a function is now refused by `canonicalBytes` **before any field is examined**,
which is earlier than the schema check that used to catch it. Two existing assertions had to be
updated to expect the earlier refusal, which is itself a small piece of evidence that the boundary
moved rather than just tightened.

## On P-6b failing closed

I froze it anyway and put the reason in the law, because I think this is the interesting part: `bind`
fails closed only because `verify()` recomputes the id from what was stored. **A second mechanism
catching the first is not the first working.** `bind()` reached the state its own comment calls
impossible, and `authorize()` will issue a request against that id in the meantime. A negative case
fires if that sentence is ever softened to "this one is caught downstream".

## The generalisation, stated as you framed it

> Every untrusted structure that becomes authority state is canonicalised into an **owned snapshot**
> exactly once; validation, identity computation and storage then operate only on that snapshot. **No
> unowned mutable object is consulted twice across a trust decision.**

Six rungs — label, name, action, semantic oracle, authority-bearing object, and **mutable data read
twice**. The sixth is the first that is not an object a caller handed over; it is a thing a caller
*kept*. `canonicalBytes` has refused a capability since v0.1.0, and what was never said is that
reading **through** it twice reintroduces one: the second read *is* the capability.

I've written the law to be the terminating statement you described rather than an instance-list, and
`grid_check` refuses a version of it narrowed back to the two cases.

## Gate

```
grid v1.29.0 — 73 entries / 366 citations
derive_protocol.mjs 0.12.0 · observed_execution_host.mjs 0.2.0
lowering.mjs 0.1.0 · bridge/ic32_film.c 0.2.0
negative battery      174/174  (six new forgeries)
cross-plane bridge     48/48
native semantic film   16/16
lowering refinement     9/9    film-evidenced
derive battery         45/45   realm battery 20/20
eleven paired probes, all breaching frozen and confined live
harness self-test       9/9    runner contract 3/3
review pack            23/23 green from an arbitrary directory
```

`scheduler_certificate.json` byte-identical — twenty-third consecutive round.

Ledger items **152–156**. The seam list is twelve long; the newest is **a value read once vs a value
read twice**.

---

## Pass B, and what I want ruled before I start it

I've taken your three answers as decided and will not re-litigate them:

- **Inputs: freeze now, before implementing `input`**, with the two-identity model —
  `program_sem_id → target_template_sem_id` (reusable, independent of invocation data) and
  `target_template_sem_id + inputs_sem_id → target_term_sem_id` (the closed executable term). That
  is better than what I had: my "parameterized vs instantiated" framing was a false choice, because
  the template is parameterized *and* the executed term is necessarily closed.
- **`church_exp_2_2`** as fixture A — DUP-LAM, DUP-SUP=, DUP-SUP!, DUP-VAR, DUP-APP, APP-SUP,
  APP-LAM, and all three locus families, 21 frames — with a purpose-built **DUP-ERA** witness as
  fixture B rather than claiming six rules because one large term happened to terminate. Coverage by
  construction beats coverage by hope, and I would not have picked that.

Two things I'd like your view on before building:

1. **`instantiation_sem_id`.** Your chain has `target_template_sem_id + instantiation_sem_id +
   inputs_sem_id → target_term_sem_id`. Is instantiation a *third* content-bound relation identity
   alongside `lowering_sem_id` and `decode_sem_id` — i.e. a fourth law — or is it part of the
   lowering relation, since the same lowering spec determines both how ports are emitted and how
   they are filled? I lean toward **its own identity**, on the same argument that separated decode:
   a template can be right while the instantiation binds the wrong port.

2. **I-4, canonical input name mapping.** This is the falsifier I expect to be hardest, and I want
   to make sure I read it the way you meant. `input("x")` must lower to a port whose target-side
   identity is a function of `"x"` and the encoding — never of whichever fresh variable the emitter
   happened to allocate. That is round 16's "the identity bound a spelling" in the *other* direction:
   there the danger was an identity depending on a name that should not matter, here it is an
   identity depending on an allocation that should not matter. If that's right, I-4 wants a witness
   where two lowerings that allocate different internal names must reach the **same**
   `target_template_sem_id`.
