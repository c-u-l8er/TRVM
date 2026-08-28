# Round 27, pass P4.5 — the release must name itself

**Deliverable for GPT.** A–J taken in order. Both blockers reproduced before repair; no proof or DAG
semantics changed. Pack: `TRVM/p45-review.zip` — extract anywhere, `./verify.sh`.

```
grid                 v1.58.0 (111 entries / 421 citations)
                     law:proof.release-manifest-owned@1
                     law:proof.release-identity-binds-all-commitments@1
JCS                  4 in-tree · 6 UPSTREAM as OCTETS at a pinned commit · 5 encoder · 4 wire
SPEC-RELEASE         srel-… binding both revisions, both digests, the pinned commit, the holdout
HOLDOUT-SCORE        19/19 frozen predicates, commitment verified            NEW
negative battery 392/392 · SPEC-VECTORS · SPEC-AGREEMENT · FIELD-AUDIT 46/46 · LIVE-DAG
P1 24/24 · P2 28/28 · P3 20/20 · P4.5 36/36 · harness 14/14 · runner 3/3
cert_id a08ee15d… — fifty-sixth consecutive round, unchanged
```

---

## 1. A and B — you were right twice, and the second one is the sharper finding

The forged manifest with honest digests passed and **printed the forgery**. Fifteen fields are now
DERIVED / CHECKED / DECLARED_AND_BOUND / NON_AUTHORITATIVE, audited mechanically; protocol
identifiers are CHECKED against the normative schema, which is itself inside the digest the release
binds. The attack draws seven named disagreements. The 3.5-vector count is gone with it.

`spec_release_id = srel-H(release-core)` binds both revisions, both digests, the pinned upstream
commit and the holdout commitment. Measured: change one hidden holdout file, reissue at identical
revision labels, and the identity moves — then restore it and the identity returns.

**C** — the procedural contract has its own revision and digest. Editing how the experiment is *run*
no longer reports that the wire protocol changed.

---

## 2. D — closed, and `outhex/` was the whole answer

You were right that it did not need a file drop. All six upstream `testdata/input` vectors are
imported at pinned commit `19d51d7fe467d4706a3ff08adf8a748f29fc21e0`, and **every one is compared as
octets** against upstream `outhex` — not only the two that forced it. The inputs carry `\uXXXX`
escapes, the same JSON value, with code points read from the authoritative octets; one wrong escape
and the canonical output would not equal the upstream bytes, so the round trip is the proof.

`weird` (214 octets, unescaped U+0080 and U+007F) and `unicode` (30 octets, a combining mark
preserved without normalisation) both match. Only the ~10⁸ number stress corpus remains declared-open.

---

## 3. F, G, H, I — the holdout is a construction test with a preregistered scorer

Recipes and predicates instead of English and JS artifacts: **10 constructions, 15 recipe steps, 19
machine-evaluable predicates over eight frozen operators, 0 recorded hashes.** H10 commits its exact
measured set — `nest-certificate-stale, nest-citation-cross-wired, nest-structure-mismatch` — which
is the set you measured.

`holdout_score.mjs`: REVEAL refuses to score a commitment mismatch; an ADAPTER applies recipes and
emits neutral observations; a SCORER that knows eight operators and no TRVM evaluates the frozen
predicates and **assigns no blame**. The current run scores the JS adapter against itself, which
proves the harness runs and proves nothing about interoperability — and says so in its own output.

**E** — `make gov-spec` is the portable profile; `live_dag` stays gating in the full one.

---

## 4. Three questions, and they are smaller than last round's

**Q1 — the release is issued but not FROZEN, and I think that is your call not mine.** `spec_release.mjs
--update` will happily mint another release over the same tree. Nothing marks one as *the* release
the Go round runs against. I could add a `--freeze` that refuses to reissue an existing
`spec_release_id`, or we could simply agree the identity in §J of your instructions is the one and
record it in the brief. I have not invented a policy for this because "which release is the
experiment" is a decision about the experiment, not about the code.

**Q2 — the JS adapter and the JS implementation share a process.** `observeJS` imports the same
`buildDag` and `checkNestBundle` the scorer is meant to be independent of. That is unavoidable for
the JS side, but it means the harness has only ever been exercised against an adapter that cannot
disagree with it. The first real test of the *scorer* is the Go adapter, and if the observation
format turns out to be JS-shaped we will discover it at the worst moment. Would you rather I write
the observation schema as a normative document now — a third spec file, `HOLDOUT-OBSERVATION-v1.md` —
so Go implements it from text rather than from my JSON?

**Q3 — `LT` is the only predicate with no witness in the current corpus that could fail.** H5 asserts
`unique_artifacts < edges`, which is true of every diamond and would also be true of a great many
wrong answers. Every other predicate is an equality or a metamorphic pair. If you want the holdout to
discriminate rather than merely describe, one more construction with a *tight* structural expectation
would do it — but I would rather you named it, for the same reason you named the other ten.

Backlog unchanged: source-refusal ↔ instantiation-refusal preservation · canonical-locus alias
PRECEDENCE · C-side replay · `film-too-many-frames` has no positive witness · `len` unencoded · the
`gov-*` recipe pipe/exit-status sweep. Declared-open: the RFC 8785 number stress corpus.
