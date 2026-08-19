# Round 25 — brief for review

**Pack:** `TRVM_R25_REVIEW_PACK.tar.gz` (64 files). Extract anywhere, `./verify.sh`.
Replayed here: **attempted 21 · passed 21 · failed 0 · skipped 0**.

Two things happened: **P-4 closed**, and then the **lowering spike ran end to end**.

Cheap decisive pair:

```
cd governance && node probe_semoracle_v10_repro.mjs && node lowering_check.mjs
```

(the second needs `gcc -O2 -o bridge/ic32_canon bridge/ic32_canon.c` and the same for `ic32_film`.)

---

## P-4, confirmed and closed

I reproduced your attack verbatim before touching anything: an issued `const(5)` request accepted as
**999** under `{verify: () => ({ok:true}), get: () => const(999)}`, with the identical result refused
as `foreign-result-divergence` by the real registry. Your reading is exactly right — re-derivation
was working perfectly, it re-derived against the program the *claimant* nominated and agreed with
itself.

Repaired as you specified: `new DerivationAuthority(reader, programImage, host)`, the authority
**builds** its own `ProgramRegistry` from canonical data (`bind` severs through `canonicalBytes`),
and `execute(req)` / `accept(req, res)` take no registry.

I added **P-4b** because the ownership point deserved a witness that isn't a duck: the oracle is a
*genuine* `ProgramRegistry` instance holding a different program. `instanceof` passes. That case is
in the probe so a future session cannot "fix" this with a type check — and the law says so in its
own statement, with a negative case (`ownership-becomes-a-typecheck`) that fires if that sentence is
removed.

`bindProgram` stays and needs no second rule: ids are content-bound, so `const(999)` gets its own.
There's a live case proving it can't repoint an issued id.

The probe's last two cases check the ladder **as a set** rather than one rung at a time — a ladder
is only closed if the list is finite and someone wrote the list down.

## The lowering spike ran

```
add(const 2, const 3)   inputs = {}
   │ lowering_sem_id                      re-lowered independently and compared
   ▼
one canonical ic32 term  ──▶ target_term_sem_id     kernel AND ic32_canon agree
   │ native ic32, launched by ObservedExecutionHost from a catalog entry
   ▼
L0(L1(A(N0,A(N0,A(N0,A(N0,A(N0,N1)))))))  ──▶ target_nf_sem_id
   │ decode_sem_id
   ▼
{status:"value", value:5}  ──▶ target_outcome_sem_id
source evaluator ────────▶ {status:"value", value:5} ──▶ source_outcome_sem_id
                          EQUAL
```

`lowering_check.mjs` **9/9**. Six identities, six distinct values, asserted.

All three rulings taken: decode is its own law; lowering gets **no film** and is verified by
**re-lowering** (`add(3,2)` reaches a different `target_term_sem_id`, so the check isn't vacuous);
`lowering_id` split into the relation's id and a `LoweringReceipt`.

One thing I decided that you didn't specify: **the decoder reads the canonical signature, not the
readback string.** That means it reads the same bytes the 48/48 bridge has agreed on since round 12
and cannot be misled by a binder name — which is precisely how round 23's first film emitter went
wrong. Consequence: §5 compaction is irreversible, so a compacted signature is **refused**
(`decode-signature-compacted`) rather than guessed at. That bounds the decodable numerals at roughly
a dozen applications. Stated in the law rather than discovered later. Tell me if you'd rather the
decoder read the readback and accept the binder-name risk.

## The gap, and it is the reason this brief exists

**The native execution leg is OBSERVED, not FILM-EVIDENCED**, and I could not close that this round.

Every lowered addition carries a dup cell **by construction** — Church addition uses its function
argument twice and ic32's net is linear — and `ic32_film` v0.1.0 is the dup-free one-step fragment.
So the film emitter refuses this exact fixture, and `lowering_check.mjs` **asserts that refusal**
(`native-film-absent-by-refusal`) rather than routing around it. The gap is measured at the fixture
the refinement runs on.

The law therefore names **two grades of evidence for the execution leg** and claims only the first:

```
OBSERVED         the host hashed a catalogued binary and then ran it
FILM-EVIDENCED   the kernel independently replayed the transition sequence
```

with a negative case (`execution-grades-collapsed`) that fires if the distinction is ever smoothed
away, and another (`film-gap-unlocated`) if the statement stops naming *where* the gap is.

This is the first place in twenty-five rounds where separating two claims cost something rather than
buying something, and I want you to check that I priced it right. **Is "observed, not film-evidenced"
an acceptable grade for a refinement witness, or does the refinement theorem only mean what you want
it to mean once the transition sequence is replayed?** If the latter, the round's headline should be
weaker than I've written it.

Closing it is concretely scoped now rather than named in the abstract: DUP-LAM · DUP-SUP= ·
DUP-SUP! · DUP-ERA · DUP-VAR · DUP-APP in the emitter, the `d:` and `v:` loci (which is where the
canonical locus stops being a tree path and becomes a discovery index), and multi-frame films. That
upgrades **this same witness** from observed to film-evidenced without changing the fixture.

## Inputs model: deferred, named, and mechanically refused

`INPUTS_MODEL.decided` is `false`, the grid checks it, and `lower({op:"input"})` returns
`lower-inputs-undecided`. Four other out-of-fragment refusals are named and checked. So the question
cannot be answered by accident while implementing the op — which was your point.

## Gate

```
grid v1.27.0 — 71 entries / 363 citations
derive_protocol.mjs 0.10.0 · observed_execution_host.mjs 0.1.0 · lowering.mjs 0.1.0
negative battery      159/159  (sixteen new forgeries across the two rounds)
cross-plane bridge     48/48
native semantic film   14/14
lowering refinement     9/9    ← new
derive battery         45/45   realm battery 20/20
nine paired probes, all breaching frozen and confined live
harness self-test       9/9    runner contract 3/3
review pack            21/21 green from an arbitrary directory
```

`scheduler_certificate.json` byte-identical — **twenty-first consecutive round**. This is the first
one where that number means more than hygiene: a source program was compiled, executed on a
different runtime in a different language, decoded, and found to agree, and the calculus underneath
did not move by a byte.

Ledger items **132–144**. The seam list is ten long; the newest is **re-derivation vs the oracle it
re-derives against**.

---

## What I want from you

1. **Is there a P-5?** The supplier ladder is empty as far as I can find it — a caller supplies an
   intent and a result to validate. But I have now been wrong about that four times, and each time
   the next rung was in the parameter I had stopped looking at because it was "obviously
   infrastructure".
2. **The film-grade question above**, which changes how strongly this round should be stated.
3. **Whether the dup work is the right next round**, or whether the parameterized-vs-instantiated
   ruling should come first. My instinct is dup-first, because it upgrades an existing witness
   without adding a new claim — but that is also the easier thing to want.
