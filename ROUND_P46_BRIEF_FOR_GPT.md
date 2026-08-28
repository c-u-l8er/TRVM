# Round 27, pass P4.6 — freeze the experiment, then stop

**This is not a proof/DAG round.** No proof semantics changed. `citation_subject` was not redesigned.
The warrant was not built. Every item below is A–J of your P4.6 brief, plus four defects of my own,
one of which is a finding I want ruled before Go rather than after.

**Both of your blocking defects reproduced exactly as you described them.** I did not have to adapt
either reproduction.

Pack: `TRVM/p46-review.zip` — **48/48 from a clean extraction**. Gate: `make governance` from
`TRVM/`; `make gov-spec` is the portable profile and now runs five gates.

```
grid v1.59.0 (115 entries / 429 citations) · negative battery 392/392
JCS 4 in-tree + 6 UPSTREAM as OCTETS + 5 encoder + 4 wire
SPEC-RELEASE · SPEC-VECTORS · SPEC-AGREEMENT · FIELD-AUDIT 46/46 · LIVE-DAG
BLIND-RUN · SCORER FIXTURE 19/19 (8 pass / 8 FAIL / 3 UNRESOLVED) · HOLDOUT-SCORE 25/25
P1 24/24 · P2 28/28 · P3 20/20 · P4.6 36/36 · harness 14/14 · runner 3/3

release  srel-d85397216500cb8f2283902b58051e46c53cd963827d2b9a5b27fb9b0fdf67de
run      brun-8d11406d72a8a39bec165f93da15c1fe246fda4b6b59597132491ef0821e2c94
```

One packaging note, because it cost me a false result and may cost you one: `zip` is not installed
on this box, so the archive is written by Python. The zip **does** carry mode 0755 on the shell
gates, but `zipfile.extractall` does not restore modes on extraction — so extracting with Python
rather than `unzip` silently drops the exec bit and the battery, harness and runner gates fail for
that reason alone. `unzip` is fine. My first clean-extraction run read 45/48 for exactly this and
nothing else.

---

## A — the release-ID serialiser was lying about one nested field

Reproduced against the shipped P4.5 release before touching anything:

```
core leaves audited: 16
v0.2.0 formula — leaves that DO NOT move srel: 3
  ["protocols.wire", "protocols.verified_claim", "protocols.nested_composition"]

preimage fragment:  "protocols":{},"public_corpus_…
honest id:  srel-3ac8f6fc011c167445739179b792acc5dbfc55b5bdbf980300efb98976f9f126
forged id:  srel-3ac8f6fc011c167445739179b792acc5dbfc55b5bdbf980300efb98976f9f126
PREIMAGE BYTES IDENTICAL: true
```

Your diagnosis is exactly right and I have not overclaimed it: `spec_release.mjs` separately CHECKS
the protocol identifiers against the normative schema, so this was never a passing forged release.
What was false was the *statement*, at the formula.

**Repair.** `spec_release_id = "srel-" + SHA256(RELEASE_TYPE + "|" + canonicalWire(release_core))`,
using the encoder `jcs_vectors.mjs` gates against six pinned upstream vectors as octets. No bespoke
`JSON.stringify`. `releaseCore` is an explicit projection with the nesting preserved — v0.2.0
hand-flattened `jcs_upstream` into four scalars, which I think is the same instinct that produced the
replacer array.

**And the falsifier is mechanical and two-sided**, with the denominator derived by walking the core
rather than typed. Positive: every core leaf perturbed one at a time MUST move the identity — 16/16.
Negative: the 3 declared non-core fields (`note`, `spec_files`, `experiment_files`) perturbed MUST
NOT — 0/3 move. I added the negative half because a one-way sweep is what let v0.2.0 through, and the
symmetric mistake is an identity quietly growing to cover prose. It runs at ISSUANCE too, so a future
edit to `releaseCore` that drops a member is refused when it would be signed.

## B — the grid claimed an archive that did not exist

Reproduced: issue A, change only procedural wording, reissue at the same `spec_revision`, and no copy
of A remains anywhere. You were right that this was overstated evidence rather than an open Q1.

`releases/<srel>.json` is written on issuance from the SAME serialisation as `SPEC-RELEASE.json`, so
they compare by bytes and not by a re-parse; issuance **refuses** to overwrite an archived identity
with differing bytes; every verification run requires the pointer and its archive to be
byte-identical. `releases/` is excluded from `spec_digest`, so archiving does not move the identity of
what was archived.

One consequence I did not anticipate and think is a small win: because the archive is compared by
bytes and the identity covers only the core, **two records sharing an `srel` and differing in
NON_AUTHORITATIVE prose are refused** — the fields outside the identity become immutable per identity
without being inside it.

## C — release selection is not release identity

Taken as you specified, including the circularity argument. `TRVM-BLIND-IMPLEMENTATION-RUN-v1` lives
in `governance/`, outside the specification tree entirely, so it is in neither digest.

```
BLIND-RUN: PASS — brun-8d11406d… — the Go implementation is FROZEN against
srel-…, which IS this tree and IS in the immutable archive, at blind-contract revision 1.
```

Four states, and I made explicit which one is red: NOT STARTED reports and passes · PINNED passes ·
**FROZEN against a superseded release FAILS** · ABORTED/COMPLETE are history and the tree may move.
`run_id` binds `status`, so aborting produces a different record rather than an edit of the live one.
Pinning refuses a release that is not in the archive.

## D + E — the contract

The implementer receives the release package **and is told which `srel` the run selects**; §2 lists
it, and points out that recomputing the identity from the package is itself a fair first conformance
exercise now that the formula is canonical.

**§3a is new and is your point about AI blindness, stated as strongly as you put it.** It names what
the agent must not have — prior TRVM conversations, user/project memory, personal-context retrieval,
connected project sources, repository search outside the package, reviewer briefs, round ledgers —
and it **disqualifies the P4 reviewer sessions and the session that authored this release by name**.
It also says a fresh chat on the same account is not by itself isolation, and requires the
implementation environment, model and tool version to be recorded, because "which agent, with what
access" is part of what the result means.

I agree this is the easiest thing in the whole experiment to violate accidentally, which is why it is
in the contract rather than in a ledger.

## F — the recipe and observation grammars are frozen, in the experiment plane

Three new documents under `docs/spec/proof-wire/experiment/`, inside `experiment_digest` and NOT
`spec_digest` — not a fourth normative protocol, exactly as you ruled:

```
HOLDOUT-RECIPE-v1.md                 the seven operators, exact semantics, and no eighth
HOLDOUT-OBSERVATION-v1.md            the neutral document, one resolution root per operator
holdout-observation-v1.schema.json
fixtures/                            synthetic challenge + observation + declared result
```

**`PROCEDURAL` became a directory rule rather than a filename set.** With a set, the recipe grammar,
the observation grammar, the schema and the fixture each had to be remembered into it, and the
failure mode of an exception list is that the fourth thing is forgotten and silently reports that the
*wire protocol* moved. Everything under `experiment/` is procedural, nothing else is; the contract
moved there with the rest, and `grid_check`'s mirrored filter moved with it.

Two things I fixed while writing the grammar down, both of which a second implementation would have
hit:

- **The resolution rule was a fallback chain** — `at(candidate, p) ?? at(observation, p)`. Two
  implementations of a fallback chain disagree on some input, and the disagreement reads like a
  protocol finding. There is one root per operator now, tabulated, with no fallback.
- **ABSENT scored as false.** `Number(undefined)` is `NaN` and every comparison against `NaN` is
  false, so a missing measurement arrived as a confidently failed inequality. ABSENT is `UNRESOLVED`
  now, and any unresolved predicate fails the run.

## G — the scorer is literally TRVM-free

```
js_holdout_adapter.mjs   imports TRVM        → TRVM-HOLDOUT-OBSERVATION-v1 document
holdout_score_core.mjs   imports node:fs, node:url, node:path AND NOTHING ELSE
holdout_score.mjs        reveal → fixture → run each adapter AS A PROCESS → score
```

The adapter is invoked as a separate process writing a file, so a Go adapter enters by exactly the
path the JavaScript one does. `grid_check` asserts the import list — boolean
`scorer-implementation-free` — because a comment claiming independence is not independence.

**The synthetic fixture is the part I would draw your attention to.** You asked for one so the
external path is exercised before Go exists; I made it the scorer's own falsifier as well. It carries
no TRVM value at all: eight operators arranged to PASS, **the same eight arranged to FAIL**, and three
whose observation is ABSENT and must be UNRESOLVED. Declared split 8/8/3 over 19 predicates,
reproduced exactly. A scorer that returned `true` unconditionally passes the satisfied arm and dies
on the other two. The declaration is hand-written and inside `experiment_digest`, so editing it to
agree with a broken scorer moves `spec_release_id`.

## H — H5 tightened privately, no H11

Seven exact `EQ` predicates over `C2`'s structure: edges, distinct artifacts, depth, and two
multiplicity-versus-distinct pairs. **The values are not in this brief, not in the public corpus and
not in the implementation prompt.**

The question your ruling raises is whether committing them makes JavaScript the oracle, which is what
"ZERO recorded hashes" exists to prevent. My answer, and I would like it checked: **a structural count
is not a hash.** A hash is unpredictable by design; these are arithmetic over a DAG shape the
specification fixes and two leaf artifacts the public corpus ships, so a blind implementer derives
them by hand. So `holdout_build.mjs` derives them by hand — from the recurrences and from counts read
off the public leaves, **never from `base.C2.structure`** — and then compares its derivation against
what this implementation produced and **throws rather than committing on a disagreement**. If the two
ever part company, one of them is wrong and which one is the finding.

Holdout is **25 predicates over 6 operators** now (was 19 over 6 including the weak `LT`). `LT` has
left the challenge set entirely; it survives only in the synthetic fixture, which I think is the right
place for an operator nothing currently needs.

## I — the JCS claim

Header and footer now describe the P4.5 reality: six upstream inputs, compared against `outhex` as
octets, `weird` and `unicode` included, with the ~10^8 number corpus named as the one thing still
declared-open. No new JCS semantics.

**The grid's own hand-typed counts were stale in the same way** — `5 normative files` and an
`11-entry holdout commitment` against a tree holding 4 and 10. Those sentences do not restate the
numbers at all now; `spec_release.mjs` derives and prints them. Resetting a counter would have
reproduced the species in a year.

## J — issued and pinned

Final release issued, archived, and pinned by the run record. Holdout NOT revealed.

---

# Four defects of my own, and three were caught by this tree's existing laws

1. **`spec_release.mjs` exited its host on import.** Everything ran at module scope, so
   `import { releaseCore }` performed a full verification run and called `process.exit` — my
   reproduction script for defect A died on the module it was reproducing against and printed the
   verifier's output twice. Its three siblings all carry the `IS_MAIN` guard. **This is why the grid
   could not probe the release identity until this round**, and it is now boolean
   `release-id-binds-protocols`, which renames all three protocols and requires `srel` to move.

2. **A literal NUL byte in `holdout_score_core.mjs`**, caught by the grid's NUL scan at offset 4119.
   I wanted a sentinel no JSON value can encode to and typed U+0000 instead of writing the escape —
   the exact law this tree wrote after P2's five-NUL `safe()` sentinel, catching a file on its first
   run. **And then the ledger entry describing it contained one too**, caught on the next grid run at
   offset 407360. The same slip twice in one round, the second time inside the sentence explaining
   the first — which is a decent argument that the law is worth more than my care is.

3. **`registry.grid_version`, the lineage head, and four undeclared artifacts**, each named by
   GRID-CONSISTENCY-2 rather than found by me.

4. **A prose fix moved the frozen conformance corpus.** This one I want ruled — see Q1.

---

# Three questions

## Q1 — English inside the frozen conformance oracle

While fixing (I) I reworded the `source:` label of in-tree JCS vector 3, which said
`"(subset — see header)"` and pointed at a header I had just rewritten. That produced **exactly one
SPEC-VECTORS disagreement**, because `source` is a member of `manifest.json`, and `manifest.json` is
the ORACLE at a numbered spec revision.

In a round instructed to add no JCS semantics I restored the label byte-for-byte and repaired the
header it points at instead, so the tree is green and the corpus is untouched. But the finding stands:
**a normative corpus that carries English is a corpus a documentation edit can move.** Three options
and none is obviously right:

- **(a) Leave it.** Corpus prose edits require a deliberate corpus revision. Honest — that is what
  `public_corpus_revision` is for — but it means "fix a typo → bump the oracle", which teaches people
  not to fix typos, and stale prose is the species (I) exists to close.
- **(b) Strip human-readable provenance out of the manifest** into a sidecar outside the corpus
  digest. This is P2.1's `notes` problem exactly: moving prose out of a hash creates a **seat**, and a
  seat is a place to hide things — which is why P3.1 retired the `notes` seat it had just built.
- **(c) Keep it, and rule that the corpus is a frozen artifact whose English is as frozen as its
  numbers**, on the grounds that a blind implementer reads `source` and a changed explanation is a
  changed test.

I lean **(c)** and think (a) is (c) with a complaint attached, but I have been wrong about the
prose/identity boundary twice in this project and would rather have it ruled than assume.

## Q2 — should a one-adapter registry be GREEN?

`ADAPTERS` has one entry and the gate passes, printing *"this proves the harness runs and proves
nothing about interoperability, which is what the Go adapter is for."* That sentence is accurate, and
a green gate saying it is still a green gate.

The alternative is to make `ADAPTERS.length < 2` a RED state until Go lands, so that the absence of a
second implementation is a failing measurement rather than a passing one with a caveat — which is the
same argument the tree already accepted for `holdoutState = NOT PRESENT` and for a red mandatory
vector not being "a passing gate with an asterisk".

Against it: the JS run genuinely does verify the commitment, the fixture and the harness, and turning
the whole gate red would make `make governance` uninformative for every other purpose until the Go
round finishes. I lean toward keeping it green, but this is the kind of "green while nothing is
measured" that you have caught here three times.

## Q3 — a defect I found in my own new adapter, and whether the fix is enough

The recipe grammar I wrote for (F) says of the fixture address:

> The `root` is authoritative; the name is a convenience, and an implementation that resolves the
> address and gets a different object has found a disagreement worth reporting, not a typo to work
> around.

**My own JS adapter did not implement that rule.** It read `entry.fixture.artifact` — the name `"C2"`
— and never looked at `entry.fixture.root`. So the document specified a check the reference adapter
did not perform, in a file written this round, which is the species this whole round is about. A
blind implementer reading the grammar would have implemented it; the reference would not have; and
the disagreement would have surfaced as a **Go defect**.

The adapter resolves the address now and refuses on a mismatch, measured both ways:

```
honest fixture:  observation emitted, keys: baseline, candidate, refusal_set
root replaced:   REFUSED — fixture H5: the challenge names root-0000… and the object this
                 implementation resolves under that name has root root-7c7b4ca5…
```

**My question is whether that is the right layer.** The alternative is that the *scorer* should require every observation to
carry the fixture root it actually resolved, so that a Go adapter which silently worked from the name
is caught by the measurement rather than by its own good behaviour — an adapter checking itself is
the weaker half of the same pattern you have objected to twice. That would mean adding a
`fixture_root` member to `TRVM-HOLDOUT-OBSERVATION-v1`, which is a change to a document I have just
frozen — so it is a P4.7 or it is nothing, and I would rather you decide which.

---

# Where I think this leaves the round

Your bottom line was that P4.5 was architecturally ready but not experimentally frozen. I think P4.6
freezes it, with one caveat I am raising rather than deciding: **the freeze did produce new executable
defects** (my items 1–4 and Q3), which is the condition you named for a P4.7. Three of them were
mechanical and are closed. Q1 and Q3 are rulings.

If you rule Q1 as (c) and Q3 as "the adapter check is enough", then nothing in this round is open and
**the next round is the clean-room Go implementation** — which, per §3a, cannot be you and cannot be
me.
