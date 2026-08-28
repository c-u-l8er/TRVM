# Round 27, pass P4.7 — freeze the instrument, freeze both subjects, make disagreement observable

**Your verdict was right and I have not argued with any of it.** All seven findings reproduced
before repair, none needed adapting, and the first one is the decisive falsifier of P4.6 rather than
a hardening opportunity. The run is aborted, the instrument is content-bound, and both subjects are
digested.

**Not a proof/DAG round.** No proof semantics changed. `citation_subject` was not redesigned. The
warrant was not built.

Pack: `TRVM/p47-review.zip` — **49/49 from a clean extraction**. Extract with `unzip`, not Python — `zipfile.extractall` drops the exec
bit and three shell gates fail for that reason alone.

```
grid v1.60.0 (120 entries / 439 citations) · negative battery 392/392
SPEC-RELEASE · SPEC-VECTORS · SPEC-AGREEMENT · FIELD-AUDIT 46/46 · LIVE-DAG · JCS 4+6+5+4
BLIND-PACKAGE · BLIND-RUN · SCORER FIXTURE · HOLDOUT-HARNESS · HOLDOUT-INTEROP
P1 24/24 · P2 28/28 · P3 20/20 · P4.7 36/36 · harness 14/14 · runner 3/3

release  srel-a5f032c7e3cd93a98098cdf67d353349dafe2bacd7bc0ae7e8d6e9a9e9c9f091
package  bpkg-06da77b983094b07918c12d4f695f35fdc2378628c154c66ea113ecea7bbe486  (48 files)
run      brun-10dfef979af2780344d908fb4a587c9dbfbf56734b5b18d19c91d134d0d6034d  PINNED
aborted  brun-8d11406d72a8a39bec165f93da15c1fe246fda4b6b59597132491ef0821e2c94  (receipt written)
```

---

## The four blockers

### 1. The scorer is not frozen — reproduced exactly

```
insert  if (entry.id.startsWith("H")) { pass = true; continue; }

           BEFORE (P4.6)                    AFTER (P4.7)
SCORER FIXTURE   19/19 PASS                 19/19 PASS      ← still, and that is the point
HOLDOUT-SCORE    25/25 PASS                 FAIL
SPEC-RELEASE     PASS, SAME srel            FAIL
BLIND-RUN        PASS                       FAIL
```

Your framing is the one I adopted verbatim in the code comments: *a synthetic fixture proves that one
particular set of scorer behaviours works; it cannot prove that the scorer subsequently used on the
secret `H*` cases is the same scorer.* Note the fixture **still passes** under the attack — its cases
are `S*` — which is exactly why the fixture alone was never going to be sufficient, and why the
binding had to be content-addressed rather than behavioural.

The instrument is `docs/spec/proof-wire/experiment/`: `holdout_score_core.mjs`, `holdout_runner.mjs`,
`holdout_schema.mjs`, both schemas, and `fixtures/`. Inside `experiment_digest` → inside
`spec_release_id`. And the run pins `instrument_digest` separately — not redundantly, because moving
the instrument *out* of `experiment/` would **shrink** that digest rather than move it and would read
as an ordinary revision, so `blind_run.mjs` asserts membership as well as bytes.

**The adapter registry moved out of source into the run record**, per your point that registering Go
must not mean editing the instrument. Each adapter carries the digest of its own package and the
frozen runner verifies it *before executing*. For JavaScript the package is the implementation the
adapter reaches — `cas`, `nest_bundle`, `nest_check`, `derive_protocol`, `certificate`, `schema` — not
just the adapter file, since an adapter is a thin shell over a checker and freezing only the shell
freezes nothing.

**One thing the first repair left green, which I then closed.** With the instrument frozen, the attack
correctly reddened SPEC-RELEASE and BLIND-RUN — and `HOLDOUT-SCORE` still printed PASS, because it
checks the commitment and delegates. The whole `make governance` was red either way, but a green line
saying the holdout was scored while the thing that scored it had been altered is a green light on a
false claim. It runs the pin first and refuses now.

### 2. The Go implementation is not frozen — run record is now a state machine

```
PINNED  →  CANDIDATE_FROZEN  →  REVEALED  →  COMPLETE
   ↘            ↘                  ↘
              ABORTED
```

`CANDIDATE_FROZEN` requires `--files` (source digest, refused if empty or if any path is missing),
optional `--binary`, and a recorded environment (`--toolchain`, `--model`, `--tool-version`).
**`--reveal` refuses at any state other than `CANDIDATE_FROZEN`**, and says why. Every transition
writes an immutable receipt under `receipts/`; `run_id` binds every subject's package digest *and the
status*, so aborting produces a different record rather than an edit of the live one.

`brun-8d1140…` is ABORTED with a receipt that names all three demonstrated gaps and embeds the
superseded v1 record verbatim.

### 3. The observation schema is not enforced — it is executed now

`holdout_schema.mjs` validates the subset those documents use, **written rather than imported** so a
clean-room implementer can audit it in an afternoon. One extension keyword, named as an extension
rather than smuggled in: `x-sorted`, because a refusal set is compared for exact set equality by
byte-comparing sorted arrays and vanilla JSON Schema cannot express it — an unsorted set is not a
differently-presented set, it is a set that compares unequal to itself.

I took your suggestion of a **recipe schema** too, on the grounds you gave: the challenge language is
by now an experimental wire protocol.

**16 boundary negatives, each of which must be REFUSED** — extra field at three levels, unsorted
refusal set, duplicate refusal code, malformed root, missing `fixture_root`, mismatched
`fixture_root`, wrong envelope const, wrong `spec_release_id`, bad verdict enum, node name outside the
frozen DAG, non-integer structure member, unknown recipe operator, unknown recipe member, missing
fixture root. A fixture whose every case is accepted cannot tell a validator from a pass-through,
which is what P4.6's was.

### 4. Interop compared verdict bits — reproduced, and it now compares observations

```
impl A: 25/25   impl B (H4.candidate.C1.artifact_root → root-0000…): 25/25
predicate result vectors IDENTICAL: true
observations actually differ:       true
```

`compareObservations` deep-compares the normalized documents — every member, excluding only the
producer label. Any difference is an `UNCLASSIFIED_FINDING` that **blocks completion rather than
printing underneath a PASS**. The comparator carries its own falsifier in the public fixture:
identical documents must report zero, and a mutated `artifact_root` that no predicate reads must be
**found**.

---

## The two highs

**`requirements/open/` was an unbound blind input.** Reproduced: edit it and both SPEC-RELEASE and
BLIND-RUN keep passing with identical identities. I took your `bpkg` design exactly as specified,
including the reasoning that this reuses the semantic-vs-artifact distinction instead of making
`requirements/` a special case. `bpkg` covers **everything** under the package root by construction —
stated as a directory rather than a list, because a list is an exception register and the failure mode
of an exception register is that the fourth thing is forgotten, which is precisely how
`requirements/open/` came to be unbound.

**Q3 was half-fixed.** You were right that checking the root after fetching by the label is a
different rule from the root being the lookup authority. The adapter resolves `cas/<root>.json` by the
address alone, re-derives the root from the bytes it got back, and treats the label as a claim about
the manifest checked second. **And I took your second half**: the observation now carries a required
`fixture_root`, and the frozen scorer independently requires it to equal the challenge's — because
nothing outside the adapter can otherwise tell the two orders apart, and an adapter checking itself is
the weaker half of the pattern you have objected to twice.

## The medium

**H10** derives its refusal set from `TRVM-NESTED-COMPOSITION-v2` now, with a written justification
per code — citation cross-wired (§7.2), certificate stale (§7.3), structure mismatch (§8: the real DAG
below D becomes {C1, C1} at 6 edges / 3 distinct / depth 2 against a carried 8 / 4 / 3) — then
cross-checks against JS and **throws rather than committing on a disagreement**, as H5 already did.
You were right that this was the same defect one layer down and that H5 had been repaired while this
was left.

## Your rulings

- **Q1 → (c), taken.** The corpus's English is as frozen as its numbers; a typo produces a new
  `public_corpus_revision` and not a protocol version; no unhashed prose sidecar, because that
  recreates the seat P3.1 retired.
- **Q2 → split the claims, built.** `HOLDOUT-HARNESS: PASS` and `HOLDOUT-INTEROP: NOT MEASURED — 1
  implementation`. Interop can never print PASS below two frozen implementations.
- **Q3 → both halves, done.** Above.

---

# Four of my own, and two were the same species one file apart

1. **The package's exclusion check forbade the substring `holdout`** — which flagged
   `holdout_score_core.mjs` and `holdout_schema.mjs`, *the frozen measuring instrument*, whose whole
   point is to be in the package.
2. **The second draft searched for the type token** `TRVM-PROOF-WIRE-HOLDOUT-v2` and flagged the two
   documents that **define** the challenge type. A name cannot tell the scorer from the challenges it
   scores. The exclusion is by **digest** and by **`H*`-id shape** now, and both arms are measured by
   planting a hidden challenge in the public corpus under an innocuous name — it is caught twice.
3. **The grid's mirror of that check repeated defect (1) verbatim** and failed loudly.
4. **The grid probe for the delegation anchored on `/experiment[\/]+holdout_runner\.mjs/`** and read
   FALSE, because the gate builds that path with `join(SPEC, "experiment", "holdout_runner.mjs")` and
   the concatenated string exists only at runtime. That is this tree's coincidental-search-text
   species **in its other direction** — a probe answered by the *absence* of text it had no reason to
   expect — and it reads exactly like a real defect.

And one reporting defect: the `gov-nest` recipe's `tail -1` printed only `HOLDOUT-SCORE` and swallowed
`HOLDOUT-HARNESS` and `HOLDOUT-INTEROP` — the two claims this round split apart so they could never be
read off one another. A gate that hides the distinction it exists to draw is the `| tail` defect
wearing a different hat.

---

# Where this leaves the round

You said P4.7 should be surgical and then we stop. I believe it is: five new laws, no proof-semantics
change, and every one of your seven findings closed with a reproduction on both sides.

**I have no questions this time, and I do not think there should be a P4.8.** The remaining honest
statement is that the freeze produced four defects of my own, all in the new machinery, all closed,
and three of them caught by this tree's existing laws rather than by me.

The next step is the one the contract describes: `node blind_package.mjs --emit <dir>` produces the
exact mount, `blind_run.mjs --freeze-candidate` digests the Go package before anything is revealed, and
`--reveal` refuses until it has. By §3a that implementer can be neither of us.

If you want one more thing before Go, the candidate I would nominate is not another mechanism but a
**dry run of the state machine** — freeze a deliberately trivial fake candidate, reveal, score, and
confirm the receipts and the interop path behave on two real adapters before the real one exists. That
would exercise `CANDIDATE_FROZEN → REVEALED → COMPLETE` and the interop comparator against something
that can actually disagree, rather than against a synthetic twin. It changes no frozen document. Say
the word and I will do it; otherwise I would start Go.
