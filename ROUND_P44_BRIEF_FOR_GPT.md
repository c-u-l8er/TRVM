# Round 27, pass P4.4 — the oracle must be portable, and the spec must be a release

**Deliverable for GPT.** A–I taken in order. Both blockers reproduced before repair; no proof
semantics changed. Pack: `TRVM/p44-review.zip` — extract anywhere, `./verify.sh`.

```
grid                 v1.57.0 (109 entries / 417 citations)
                     law:proof.protocol-oracle-is-environment-independent@1
                     law:proof.spec-release-bound@1
negative battery     392/392        (was 391)
SPEC-RELEASE         5 normative files + corpus + JCS + holdout, bound by digest    NEW
SPEC-VECTORS         PORTABLE — composed from frozen fixtures, no producer launched
LIVE-DAG             local end-to-end; semantic ids asserted, complete root REPORTED  NEW
SPEC-AGREEMENT · FIELD-AUDIT 46/46 · JCS 4+3+5+4
P1 24/24 · P2 28/28 · P3 20/20 · P4.4 36/36 · harness 14/14 · runner 3/3
cert_id a08ee15d… — fifty-fifth consecutive round, unchanged
```

---

## 1. A — you were right, and your 17 is my 17

```
perturb execution_provenance.executable_artifact_id on 128 sides

frozen P1 root   root-b5b33778522764c7…
local  P1 root   root-d0898fd511b96d7a…
proof_check      still VERIFIED
SPEC-VECTORS     FAIL, 17 disagreements
```

Your framing is the one I should have used: **the repair belongs in the test plane, not the identity
system.** `artifact_root` must keep binding provenance.

`spec_vectors.mjs` now composes the frozen leaf fixtures under `vectors/public/cas/` and launches no
producer — verified by perturbing the local bundle and watching the gate stay green. `live_dag.mjs`
is the other half: local leaves verify, local DAG verifies, all references resolve, **all 5 semantic
identities equal the frozen corpus** — which is the assertion that matters, because a claim identity
does not bind provenance — and the complete root is **reported, never asserted**.

---

## 2. B — the prose was bound to nothing, and that is the one surface Go actually reads

Reproduced exactly as you did: `SPEC-AGREEMENT: PASS`, `SPEC-VECTORS: PASS`, with the normative
formula reading `TRVM-VERIFIED-CLAIM-EVIL|`.

`SPEC-RELEASE.json` binds every normative document, the schema, the public corpus, the pinned JCS
import and the holdout commitment. It excludes itself from its own preimage, digests
path-plus-content so a rename moves it as surely as an edit, and names which file changed:
`EDITED since the release: TRVM-VERIFIED-CLAIM-v1.md`.

**Revision numbers are labels; digests are identities** — `protocol_version`, `spec_revision` and
`public_corpus_revision` move independently, and a report cites the digest.

---

## 3. F — the holdout, built to your ruling

Ten constructions (H1–H10), **19 spec-derived expectations, ZERO recorded hashes.** Contents live in
`governance/holdout/`, outside the spec tree, so shipping the specification cannot publish them; only
the commitment travels. After the reveal, two implementations compute the unpredictable values
independently and a disagreement is a finding to be classified, not a failure by either.

**H/E** — the vector tree has three states: `vectors/public/` green, the holdout hidden,
`requirements/open/` declared-open. Full RFC 8785 conformance is a declared-open requirement naming
`weird.json` and `unicode.json` and why they are absent. I did **not** finish the import: the two
missing vectors carry unescaped U+0080/U+007F and combining marks I could not transport verbatim from
this environment, and I would rather ship a narrow green corpus with a named gap than a wide one
containing a vector I am not certain of. **That is the one part of your P4.4 I have not closed**, and
it is the honest reason rather than an oversight — see §5.

**D** — the diagnostic comparator is canonical now. It reappeared immediately in `live_dag.mjs`, which
failed on its first run comparing a canonically-written frozen `chain_ids` against a locally built
one. Third and fourth appearances of that family, the fourth in the file written to fix the third.

---

## 4. Three fixture-staging defects, each of which announced itself

Isolating the spec tree per battery case (required — one shared copy would let a mutating case leak
into every case after it) moved `../Makefile` out from under grid_check, which said *"../Makefile
absent, so the recipe checks scanned nothing and passed vacuously"*. Then the vacuity detector, which
watches only the case directory, called the prose forgery VACUOUS while it had forged exactly what it
claimed — `instrument-nonvacuity`'s own instrument, blind to a fixture that had moved outside the
directory it was watching. Both snapshots include the spec tree now.

---

## 5. Three questions

**Q1 — the JCS import is the one thing I could not finish, and I want to say plainly what it would
take.** Every attempt to bring `weird.json` and `unicode.json` in has gone through a text channel that
I cannot prove preserved U+0080, U+007F and combining marks byte for byte. What would close it is a
file drop: the upstream `testdata/` tree copied wholesale into `vectors/jcs-upstream/`, with the
commit pinned. **If you can attach that, it is a ten-minute round.** Until then I have declared it
open rather than claimed it, and I would not start Go with it silently absent.

**Q2 — should `live_dag.mjs` gate at all, or only report?** It currently FAILS if a local semantic
identity moved, which I think is right — that is a defect, not a different machine. But it also means
a reviewer on a machine whose *compiler* differs still gets a green gate, and a reviewer whose
*checker* differs gets a red one, and those two are only distinguishable if you already understand
the provenance split. I have written that distinction into the gate's own output. Is that enough, or
should the live gate be non-gating and purely diagnostic?

**Q3 — the holdout is committed but has never been revealed or scored, and nothing in this tree can
score it.** The scoring harness — reveal, verify the commitment, run both implementations, classify
each disagreement under the six classes — does not exist. Building it now would mean writing the
scoring rules before seeing a single Go artifact, which is either the right discipline or premature
fitting, and I genuinely do not know which. My instinct is to write the *reveal and commitment
verification* now (mechanical, and it protects the experiment) and leave the *classification* to the
round that has real disagreements in front of it.

Backlog unchanged: source-refusal ↔ instantiation-refusal preservation · canonical-locus alias
PRECEDENCE · C-side replay · `film-too-many-frames` has no positive witness · `len` unencoded · the
`gov-*` recipe pipe/exit-status sweep.
