# Round 27, pass A.1 — P-7 closed, plus one you did not have

**Pack:** `TRVM_R27A1_REVIEW_PACK.tar.gz`. Extract anywhere and run `./verify.sh`.
It replays 24 gates and **generates** every number it prints; nothing in it transcribes a count.
This run: **24 attempted / 24 passed / 0 failed / 0 skipped**.

---

## 1. P-7 reproduced first, then repaired

I did not build against your report until I had the witness. Against the round-27A tree:

```
issued        request R → const(5)      psem-82eee05e…
executed                   const(999)   psem-3b198d80…
worker returned            999
accept(fresh time-varying copy, that result)
  → { ok:true, validated:true, fresh_at_check:true,
      implementation_provenance:"observed", implementation_id:"impl-js-derive-…" }
accept(FROZEN issued request, same result)
  → result-program-mismatch
```

Exactly as you described, including the part that makes it a forgery rather than luck: the only
difference between the accepted and the refused case is the caller's retained ownership.

**Repaired**, and your diagnosis of *why* was the useful part — the law was right and its reach was
the constructor. `derive_protocol.mjs` **0.13.0**:

- one exported `ownCanonical()` at the top of `authorize`, `wasIssued`, `execute`, `accept`,
  `observationOf`, `ProgramRegistry.bind`
- `#issued` keeps `{request_sem_id, request}` rather than the hash alone
- `wasIssued` returns the owned request; `execute`/`accept` read that
- `res` snapshotted once at `accept` entry; `intent` and `options` at `authorize` entry

---

## 2. Where I did not take your preferred form, and why

You preferred `execute(request_id)` / `accept(request_id, result)`, with the fallback of keeping the
signature and using the stored object. **I took the fallback, and not for ergonomics.**

An id is a **strictly weaker credential than the bytes.** Knowing the whole request implies knowing
its `request_id`; the converse is false. `execute(request_id)` turns the id into a bearer token —
anyone who has seen one can drive execution. Presenting the full request proves possession of every
field, and `wasIssued` is what checks it.

Keeping `(req, res)` gets **both**: full-bytes authentication *and* owned exercise. The retained
argument is now purely a claim to authenticate; nothing downstream reads it.

If you think the bearer-token concern is misplaced — e.g. because the request is handed to the caller
anyway and confidentiality of `request_id` was never a property — say so and I will move to the
stronger form. This is the one place I departed from your ruling.

---

## 3. P-7c — the same defect in the host, which your list did not reach

Auditing the remaining entrypoints under the widened law found one more, and it is worse than P-7:

```js
// ObservedExecutionHost.run(), v0.2.1
inputCanonical = canonicalBytes(invocation)   // read 1 — the observation KEY
runNodeWorker(entry, invocation)              // read 2 — what actually RUNS
```

An invocation honest on read 1 and hostile on read 2 is **keyed under one request and executed as
another**. Measured:

```
reads of `message`: 2
ran -> 999 for program psem-3b198d800a9
observation under HONEST request bytes:        PRESENT
observation under the bytes that ACTUALLY ran: absent
```

That is not "a forged observation cannot be found". It is a **true-looking observation for an
execution that did not happen**, sitting in the table round 23 built so that relabelling would *move*
the key.

It is unreachable through `DerivationAuthority.execute`, whose invocation is assembled from owned
parts. It is reachable by anything else holding a host — `FilmAuthority` and `lowering_check` both
drive it directly — and the host is the only writer of the observation table. So the rule I applied:

> **The obligation belongs to the entrypoint, not to its politest caller.**

`run()` now launches the snapshot it keyed (`JSON.parse(inputCanonical)`, zero extra reads). Host
**0.3.0**. Frozen as P-7c in the same paired probe.

---

## 4. Enforcement is an enumeration, not three more witnesses

Your point that the law had been applied where it was written down is the reason I did not just add
cases. `derive_realm_battery.mjs` hands **every** entrypoint a structurally identical argument whose
every field counts its own reads, and fails past a one-read-per-field floor:

```
authorize/intent 7/7 · authorize/options 1/1 · wasIssued/req 11/11 · execute/req 11/11
accept/req 11/11 · accept/res 18/18 · observationOf/req 11/11 · observationOf/res 18/18
bindProgram/ast 2/2
```

Reintroducing the defect in `execute` alone → **`execute/req 33/11`**, and the case names the
offender. A method added later with a live argument fails here with nobody remembering to come back.

*Falsification of my own instrument:* the first version scored `accept/res 0/0` — the fixture
under-granted, `run.result` was `undefined`, and the result-side probes passed by measuring nothing.
It now throws if the fixture does not execute and accept.

---

## 5. The stale diagnostic, and two more like it

You flagged the `derive_realm_battery.mjs` "Four rungs" print. Fixed, and derived: `SUPPLIER_LADDER`
is one frozen record in `derive_protocol.mjs`, and every **live** surface takes its count and wording
from it. The frozen probes keep their own era's wording deliberately — each records the ladder as it
stood when its witness was cut, and rewriting that would falsify a dated record.

Two others surfaced in the same pass:

- **`derive_battery.mjs`'s `issuance-binds-the-whole-request` had been calling the deleted
  three-argument `accept(reg, req, res)` since v0.10.0.** `reg` landed in the `req` slot,
  `reg.request_id` was `undefined`, and the issuance table's miss on `undefined` produced the expected
  string `grant-not-issued-by-this-authority` **by accident**. It asserted that string for eighteen
  rounds and never exercised the sentence it printed. Snapshot-at-entry is what surfaced it — a
  `ProgramRegistry` is not canonical data, so it now fails loudly instead of quietly agreeing. The
  *behaviour* was always correct; only the instrument was wrong.
- **`observed_execution_host.mjs` separated artifact-closure paths with a raw NUL byte in the
  source.** `file(1)` classified the module as `data`; ugrep and every other text tool skipped it in
  silence. *A grep over that file returned nothing and read like an answer.* Now the `\u0000` escape —
  identical string, visible module.

---

## 6. Gate

grid **v1.30.0** — 74 entries / 368 citations · `derive_protocol.mjs` **0.13.0** ·
`observed_execution_host.mjs` **0.3.0** · negative battery **182/182** (eight new forgeries; three
repointed off source text this round deleted) · bridge 48/48 · native film 16/16 · lowering refinement
9/9 film-evidenced · derive **45/45** · realm **22/22** · **twelve** paired probes (newest: 3/3
frozen, 6/6 live) · harness 9/9 · runner 3/3 · review pack **24/24, 0 skipped**.
`scheduler_certificate.json` byte-identical — **twenty-fourth** consecutive round.

New law `law:derivation.entry-snapshot@1`:

> Every authority operation consumes either an authority-owned object or one canonical snapshot made
> at entry. No trust decision authenticates one read of external state and exercises authority using
> another.

---

## 7. Questions

1. **The `execute(request_id)` disagreement** (§2). Bearer-token concern valid, or is `request_id`
   confidentiality a property TRVM never had and never wanted?
2. **Scope statement I want ruled.** The module's free functions — `deriveLocally`,
   `validateForeignResult`, `checkRequest`, `checkIntent` — do **not** snapshot. The authority never
   passes them unowned data (verified: every call site now takes `issued`/`ownRes`/`ownIntent`). But
   they are exported, and a second authority built on them inherits the obligation without inheriting
   the mechanism. Is "authority operations snapshot; free validators are pure functions over data the
   caller already owns" the right line, or should the free functions carry it too? This is the most
   likely home of an @8.
3. **Is the read-count enumeration the right terminating instrument**, or is there an argument class
   it structurally cannot see? It counts property reads on a plain-object copy; a Proxy with an
   `ownKeys` trap is read once by `canonicalBytes` and I believe that is coherent, but I would rather
   you attacked it than that I asserted it.

---

## 8. Pass B — your rulings taken as given

Recorded in `governance/round-11-ledger.md` items 166–167, not to be re-litigated: separate
`instantiation_sem_id` with its own law; the relation-not-invocation split against `inputs_sem_id`;
the `InstantiationReceipt` verified by independent re-instantiation, no film; I-4 as the inverse of
round 16 with `input-port("x")` at the canonical target-AST layer and **no Unicode normalization** of
source input strings; the three falsifiers rather than one; Fixture A `church_exp_2_2` and Fixture B a
purpose-built DUP-ERA witness.

Posture change accepted: no more proactive P-hunting. Next is the inputs decision record, then the
`church_exp_2_2` DUP film.
