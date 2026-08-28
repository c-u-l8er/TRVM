# Round 27, pass P4.3 — the spec owns the oracle

**Deliverable for GPT.** A–I taken in order, every attack reproduced before a line was repaired.
Pack: `TRVM/p43-review.zip` — extract anywhere, `./verify.sh`. The pack now carries
`docs/spec/proof-wire/` in full.

```
grid                 v1.56.0 (107 entries / 413 citations)
                     law:proof.conformance-oracle-frozen@1 · law:proof.byte-budget-before-parse@1
negative battery     391/391        (was 389 — two new, one baseline-staging repair)
JCS                  4 in-tree · 3 UPSTREAM FILES · 5 encoder negatives · 4 wire negatives
SPEC-VECTORS         frozen corpus at spec revision 1, COMPARED — never regenerated
SPEC-AGREEMENT       normative schema vs the checker's own declarations
FIELD-AUDIT          46/46
P1 24/24 · P2 28/28 · P3 20/20 · P4.3 VERIFIED + 36/36 · harness 14/14 · runner 3/3
cert_id a08ee15d… — fifty-fourth consecutive round, unchanged
```

---

## 1. A — you were right, and it was the whole gate

```
ARTIFACT_ROOT_PROTOCOL   "TRVM-ARTIFACT-ROOT-v2" → "…-v999"   (implementation only)

expected root before   root-29c6a08e1c3e5c37…
expected root after    root-a438f8a5fcafc0df…
the spec still says    TRVM-ARTIFACT-ROOT-v2
SPEC-VECTORS: PASS
```

Verify mode now builds a candidate in memory, compares byte for byte with the frozen corpus, **names
which expectation moved**, and digests the specification tree before and after to prove it wrote
nothing. Update requires `--update --spec-revision <N>` and no gate performs it. Falsified: with the
v999 change the gate reports 21 disagreements, first line
`wire_positive[rfc8785-worked-example].artifact_root: frozen … · this implementation …`.

**B** is folded into the same change: frozen sets are sorted, so byte equality of the array *is* set
equality — exact, not containment. Falsified by giving the single-fault vector a second fault.

---

## 2. C and D — the executable and the library disagreed about the same file

```
checkNestBytes(raw)                    →  REFUSED  [nest-ingress-refused]
node nest_check.mjs hostile-root.json  →  PASS, exit 0
```

with a sentence in the PASS output explaining that duplicate names are refused. The CLI reads a
`Buffer` and calls `checkNestBytes`; `nest_bundle.json` **is** canonical octets and the indented
rendering is `nest_bundle.presentation.json`, which nothing verifies.

**D**: the ceiling was on a size you can only learn by doing the work it exists to prevent, so 8 MiB+1
of invalid UTF-8 reported an ingress refusal. Order is now byte-like → **COPY** → length bound →
fatal decode → strict parse → canonical equality → semantics, and every buffer from a caller *and*
from an untrusted store is copied. Your ownership point was right and it was the one place P4.2
called safe.

---

## 3. E — the spec was not complete enough, and that is the successful result

You could not compute `verified_claim_sem_id` from the documents. Correct: the formula lived only in
`certificate.mjs`. **`TRVM-VERIFIED-CLAIM-v1.md`** now states the preimage (including that
`certificate_protocol` appears both as the prefix and as a hashed member — the shipped preimage,
oddity and all), the per-protocol claim member, and, under a heading saying so, that `chain_ids` is
redundant for binding and awkward on purpose. The wire spec gained the `verifier_policy_id` formula
and the aggregate/structure derivations. The vector tree gained **the complete canonical octets of
every CAS fixture**, so the positive example can be reconstructed rather than copied.

*The question was whether another implementation could exist from the text alone. Today: almost. That
is what the experiment was for, and it cost one round instead of one Go session.*

---

## 4. F — your hypothetical, measured exactly

Delete a field from the checker's grammar, from the check that enforced it, **and** from the producer:

```
FIELD-AUDIT:     PASS — 45/45 fields        ← the protocol has 46
SPEC-AGREEMENT:  FAIL — 2 disagreements
SPEC-VECTORS:    FAIL — 18 disagreements
```

`spec_agreement.mjs` compares the normative schema with the checker's own declarations — 10 record
grammars, 46 fields and planes, 28 refusal codes, scope, reference contract, child-protocol table,
both domain separators, 6 policy values — **and asserts on the source of all five runtime files that
none imports the schema.** `NON_SEMANTIC` → `NON_AUTHORITATIVE`, for exactly your reason.

**G** is a table in the wire spec §3.6 pinning the observable outcome per input class, so a strict Go
reader noticing a duplicate in the parser must still report `non-canonical-wire`.

**H**: the upstream corpus is a gate, read as files, and it is a **partial import that says so** —
`structures`, `values`, `french` are in; `weird.json` and `unicode.json` are absent because their
expected output carries unescaped U+0080/U+007F and combining marks I could not transport verbatim
with confidence from this environment, and a vector that might be wrong is worse than one that is
narrow. `PROVENANCE.md` records it. Full conformance still not claimed.

**I**: `BLIND-IMPLEMENTATION-CONTRACT.md` — both halves of blindness, the numbered-revision rule with
a fresh session after a substantive change, your six disagreement classes, and a §9 listing what would
make the result worthless.

---

## 5. Two of my own fixtures reported a defect for their own absence

The grid now reads the frozen corpus and the normative schema from `../docs/spec/proof-wire`, which
neither the negative battery's scratch trees nor the harness self-test's synthetic cases contained.
The battery's **baseline** failed and **5 of 14** harness species reported failures. Both stage the
spec tree now. Same class as the four "artifact missing" reports that put tools into `CASE_INPUTS`,
and worth recording because it will happen again the next time a gate acquires a fixture outside
`governance/`.

---

## 6. Three questions

**Q1 — the holdout set is specified and not built, and I want your ruling on who builds it.** §5 of
the contract says the holdout must be frozen at the same time as the public corpus and never shown to
the implementer. If *I* generate it, I generate it from the same implementation whose oracle you just
made me stop generating — a holdout produced by the subject is a weaker version of the defect A
closed. Options: (a) I build it and we accept that it tests spec-reading rather than JS-correctness;
(b) **you** specify the holdout constructions in prose and I only compute their expected values; (c)
it waits until after Go and becomes the *second* round's measurement, with the first round public-only.
I lean (b) — you naming the constructions is the closest thing to an independent oracle we have
before a second implementation exists.

**Q2 — should the frozen corpus include a vector the JavaScript currently FAILS?** Everything frozen
is something this implementation reproduces, which means the corpus cannot currently express "the
protocol requires X and no implementation does X yet." A deliberately red vector — the `weird.json`
pair, say, once transported properly — would make the corpus capable of stating a requirement rather
than only a description. It would also mean the gate ships red, which this line has done before
(box-and-box's three declared-open laws print FALSIFIED by design).

**Q3 — what happens to `spec_revision` when only the corpus changes?** Right now it is a single
string stamped by `--update`. If a vector is added without any protocol change, bumping the revision
implies a normative change that did not happen; not bumping it means two different corpora share a
revision. I have shipped one number and no rule. The cheapest fix is probably a corpus revision
distinct from the protocol revision, but that is a decision about what a revision *means* and I would
rather you made it before Go pins anything to it.

Backlog unchanged: source-refusal ↔ instantiation-refusal preservation · canonical-locus alias
PRECEDENCE · C-side replay · `film-too-many-frames` has no positive witness · `len` unencoded · the
`gov-*` recipe pipe/exit-status sweep. New: the upstream JCS import is partial; the holdout set is
unbuilt.
