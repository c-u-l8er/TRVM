# Round 27, pass A.2 — your four cleanups, done

**Pack:** `TRVM_R27A2_REVIEW_PACK.tar.gz`. Extract anywhere, run `./verify.sh`.
This run: **24 attempted / 24 passed / 0 failed / 0 skipped.**

All four rulings taken. Nothing here is a forgery; one was a real bug. Round deliberately small.

---

## 1. The credential claim — you were right, and the correction is the useful part

I withdrew the argument, not just the wording. Running three things together was the error:

```
request_id            locator / identity
whole request bytes   CONTENT WITNESS
execution capability  AUTHORIZATION
```

Possession of the request is not authentication of the caller unless TRVM promises the request is
secret, and it does not — a logged, cached or transmitted request is bearer data too. The full
request is a strictly stronger **content witness**; neither it nor `request_id` should quietly become
the capability. **If "only party X may cause this issued request to execute" is ever needed, it
becomes an explicit capability/delegation rule.** Recorded in the ledger, and item 158 is
back-annotated in place so the wrong argument stays visible with its correction attached.

## 2. The `bindProgram` bug — reproduced, and it was exactly as you described

```
execute(A) · accept                      → implementation_provenance "observed"
bindProgram(B)                             an unrelated program
accept(same request, same result)        → implementation-provenance-unavailable
```

Acceptance rebuilt the invocation from `this.#registry.image()` — present state, not historical fact.

> **Historical fact is not a function of current configuration.**

`run()` now returns `input_canonical`; `execute()` records the bytes **the host itself keyed**;
acceptance looks those up. A **list**, because the same request run before and after a bind is two
genuinely different invocations and both happened — and observations across them are **merged, not
first-hit**, which I want you to check: returning the first would report one launch as though it were
the only one, the same overclaim round 24 fixed for `executor_session_id`. Verified:

```
run1 accept: observed · run2 accept: observed
sessions for run2: 2 | results identical bytes: true
```

## 3. The exported validators — your factoring, and your measurement reproduced exactly

`checkRequest` over a Proxy-wrapped valid request, before:

```
ownKeys 2 · getOwnPropertyDescriptor 10 · getPrototypeOf 1 · get 13 · has 1
```

Identical to your numbers. Now `checkRequestOwned` / `checkIntentOwned` / `checkResultOwned` /
`deriveLocallyOwned` / `validateForeignResultOwned` are the implementations — the suffix is a
**precondition** — and the exported names snapshot once and delegate. The authority keeps calling the
`Owned` forms; paying to canonicalise what it just canonicalised would be ceremony. After:

```
ownKeys 1 · getOwnPropertyDescriptor 5 · getPrototypeOf 1 · get 5
```

i.e. exactly one `ownCanonical` traversal. **Not numbered as a rung**, per your ruling — a hazard the
law predicts, not a false verdict.

## 4. The enumeration is a detector, not a proof — and the accessor scope is declared

Item 161 oversold it; corrected in the record. New case `meta-operations-stop-at-one-traversal`:
twelve entrypoints, including the reusable exports, each handed a **recursively** Proxy-wrapped
argument counting `ownKeys · getOwnPropertyDescriptor · getPrototypeOf · has · get`, each required to
equal one `ownCanonical` traversal exactly (`wasIssued/req gOPD:11 get:11 getPrototypeOf:6
ownKeys:6`). The invariant defended is the architectural one you named: *after `ownCanonical()`
returns, nothing below it holds a reference to the external value.*

And the sharper statement, now `DECLARED OPEN` in `derivation.entry-snapshot@1` and in
`ownCanonical`'s own comment:

> `ownCanonical` prevents caller-owned **behaviour from surviving** the canonicalisation boundary.
> Not: canonicalisation never invokes caller behaviour.

with the note that the stronger property is unreachable for any API whose boundary is an arbitrary
JavaScript object, and needs `canonical text → authority-owned parser → data`, which is not built.
Three grid_check assertions and three forgeries defend those sentences, so the scope cannot be
quietly widened later.

## 5. Nit fixed

`lowering_check.mjs` said `make gov-film builds both`. It does not — `gov-lower` does. That is
exactly why your first rebuild left it correctly refusing.

---

## Gate

grid **v1.31.0** — 74 entries / 368 citations · `derive_protocol.mjs` **0.14.0** ·
`observed_execution_host.mjs` **0.4.0** · negative battery **188/188** (six new forgeries; two
repointed onto the `Owned` names) · bridge 48/48 · native film 16/16 · lowering 9/9 film-evidenced ·
derive 45/45 · realm **23/23** · twelve paired probes · harness 9/9 · runner 3/3 · pack **24/24, 0
skipped**. `cert_id a08ee15d…` byte-identical — **twenty-fifth** consecutive round.

---

## What I am doing next, unless you say otherwise

Taking your judgment: the supplier-ladder line stops being the main activity. No proactive P-8 hunt.

**Pass B, in your order:**

1. The **inputs decision record** — freezing the two-level identity architecture as ruled:
   `program_sem_id →(lowering_sem_id)→ target_template_sem_id →(instantiation_sem_id + inputs_sem_id)→
   target_term_sem_id →(native film)→ target_nf_sem_id →(decode_sem_id)→ target_outcome_sem_id`, with
   `instantiation_sem_id` as its own relation identity and its own law, an `InstantiationReceipt`
   verified by independent re-instantiation, and no film for instantiation.
2. **I-4** as three witnesses: same source name + different allocation → same
   `target_template_sem_id`; different source name + same allocation → different; x/y swapped at
   instantiation → refuses or diverges, and never validates under the correct receipt. Port identity
   at the canonical target-AST layer as `input-port("x")`, before variable allocation. **No Unicode
   normalization.**
3. **`church_exp_2_2`** for the DUP film — DUP-LAM, DUP-SUP=, DUP-SUP!, DUP-VAR, DUP-APP, APP-SUP,
   APP-LAM across `t:`/`d:`/`v:` — then a dedicated **DUP-ERA** witness, because coverage by hope is
   not coverage.

The decision record comes before any `input` implementation, per your round-25 ruling that
`INPUTS_MODEL.decided` gates `lower({op:"input"})`.
