# Round 27 pass P4.7.7 — EVIDENCE IS UNAMBIGUOUS AT THE BYTE BOUNDARY AND AT THE VOCABULARY BOUNDARY

```
release  srel-e7ee2900151f5227aa46b8b878df4b767d16e3dd003a21ff00d93946835ba723   exp revision 8
package  bpkg-15588547f87245be2cacfc2cdd1d7b8028950bd883eafc748b72d60662000f4a   59 files
run      brun-f21542d9cad3285e390fea324d3cb091d1f0b7726cf2752e937ffca303d9637b   PINNED
grid     v1.67.0   136 entries / 475 citations across 16 artifacts
```

Every number above is derived by `brief_identity.mjs`, and `make_review_pack.sh` refuses to build
around a brief that does not carry the block verbatim. **The grid line is new to this round** — see
§6, which is your reporting defect.

Gate: negative battery 392/392 · **EXPERIMENT-FALSIFIERS 44/44** · **EVIDENCE-READER 43 vectors** ·
SPEC-RELEASE · SPEC-VECTORS · SPEC-AGREEMENT · JCS 4+6-as-octets+5+4 · BLIND-PACKAGE · BLIND-RUN ·
HOLDOUT-COMMITMENT · HOLDOUT-AUTHORITY · HOLDOUT-HARNESS · HOLDOUT-INTEROP · FIELD-AUDIT 46/46 ·
LIVE-DAG · harness 14/14. Ledger items 581–592. **NOT COMMITTED.**

---

## 0. Your tenth defect, reproduced first

Before repairing anything I reproduced all six primitives against the shipped P4.7.6 tree, in
sandbox worlds built the way the battery builds them:

```
AA1  raw bytes carry BOTH statuses.  first-occurrence: REVEALED · Node: PINNED
     BLIND-RUN: PASS — brun-6805c3e5… — PINNED, WITNESSED by a receipt chain…
AA5  run carries revealed:true + verdict_override      BLIND-RUN: PASS
AA6  adapter carries blindness:"DISQUALIFIED"          BLIND-RUN: PASS
AA7  instrument_files[0].sha256 → 000000…, digest honest   BLIND-RUN: PASS
AA2  a reachable receipt carries two statuses          BLIND-RUN: PASS
AA4  observation names TWO implementations             scorer accepts, exit 0
```

You were right on every count, including the framing: the phrase *an authenticated evidence artifact
has exactly one reading* was true of parsed objects and false of bytes, and P4.7.6's own citation of
P4.1 is what makes that a defect rather than an omission.

**One correction to your report, and it is in your favour.** You wrote that `instrument_files` is
"explicitly excluded from `runCore()` because it is supposed to be a rendering of
`instrument_digest`, but the verifier doesn't check that rendering." That is exactly right, and the
same sentence is true of a member you did not name: `blind_contract_revision` **is** in `runCore`,
is bound into `run_id`, and was never compared with the release it claims to be a revision of. A
record re-identified around `blind_contract_revision: 999` verified. Same class, one line down.

---

## 1. `law:proof.evidence-bytes-unambiguous@1` — the reader is the instrument's own

New file `docs/spec/proof-wire/experiment/evidence.mjs`, inside `INSTRUMENT`, therefore inside
`experiment_digest`, therefore inside `srel`. The order you asked for is the order it enforces:

```
RAW BYTES → strict evidence boundary → parsed object → shape/value verification
```

**It parses rather than validating-then-parsing.** You offered both options; I took the tokenizer,
and the reason is the reason this line of work keeps producing defects. Scanning for duplicates and
then handing the bytes to `JSON.parse` is *two implementations of what the bytes mean*, and two
implementations of one question is the species P4.1, P4.2, P4.3 and P4.7.6 each closed in a
different place. One parser that both refuses and constructs gives an accepted artifact exactly one
reading by construction.

**It is not `cas.mjs`.** Agreed, for your reason and one more: a canonical equality would be a second
JCS implementation to keep in agreement, which is the argument `run_state.mjs` already makes for
rendering its preimage as `field<TAB>JSON-scalar` lines instead of as JSON.

**The property that makes a hand-written parser safe, asserted by `--selftest` over 43 vectors:**

> For every input this reader ACCEPTS, `JSON.parse` of the same bytes produces a deeply equal value.
> It is allowed to be STRICTER than JSON. It is never allowed to be DIFFERENT.

```
EVIDENCE-READER: PASS — 13 accepted and 30 refused over 43 vectors. Every ACCEPTED vector reads
deeply-equal to JSON.parse … 6 of the refusals are documents JSON.parse accepts — duplicate member
names and unpaired surrogates — and those are the ones the boundary exists for.
```

Refused beyond RFC 8259, each because the same bytes have two readings in two conforming readers:

| refused | the two readings |
|---|---|
| a duplicate object member name, at any depth | first-occurrence vs last-occurrence |
| **an unpaired surrogate** `"\uD800"` | Node keeps it; Go's `encoding/json` writes U+FFFD |
| invalid UTF-8, or a BOM | a replacement character the producer never wrote |
| trailing content | a file holding two documents |

The surrogate case is the one I want to flag ahead of the Go run: **left open, it would have surfaced
as an interoperability FINDING against a correct Go implementation.** Refused at the boundary, it
cannot.

`__proto__` is built with `Object.defineProperty`, matching `JSON.parse` exactly, so the agreement
property holds for it too rather than being dodged.

**Where the boundary is applied.** `run_state.mjs` (the run record, every receipt, the RESULT, every
archived observation, the challenge set, `SPEC-RELEASE.json`), `holdout_runner.mjs` (the release, the
record, **and every live adapter's observation document, refused before it is scored**),
`holdout_score_core.mjs` (both schemas, all four fixtures, both CLI inputs), and `blind_run.mjs` (the
record, the release, the measurement summary, and each observation document **before it is
archived**).

**And the frozen side reads the record itself now.** `verifyRun` took an already-parsed object from
mutable `governance/`, which left the *reading* of the record — the one thing duplicate members make
ambiguous — outside the freeze. With no bytes supplied it reads `resolveState(repoRoot).runPath`
directly; a caller holding a record that is not on disk yet passes `renderRun(r)` and thereby
verifies the exact bytes it is about to write. `renderRun` is the frozen module's, so the written
shape and the verified shape are one decision in one file.

**A receipt refusal is reported where the walk asks for it.** `readReceipts` used to `continue` past
anything that did not parse, so a refused receipt would have masqueraded as an absent one and drawn
the far less useful *"NO PINNED receipt names …"*. Refusals are recorded and surfaced only for the
`run_id|status` the chain actually requests — unreachable history stays unvalidated, as the chain
rule says it is.

---

## 2. `law:proof.run-record-vocabulary-closed@1` — and three seats removed

`RUN_MEMBERS`, `RUN_ADAPTER_MEMBERS`, `ROLES = [reference, candidate]`, applied by `runProblems()`
**before any semantic check**, refusing without attempting a further one.

**There is no `NON_AUTHORITATIVE` member in the run record at all**, because the three that would
have been one are gone:

- **`instrument_files` — removed**, your preference and mine. Derivable from `instrument_digest` +
  the frozen `INSTRUMENT` set + the tree, and BLIND-RUN already recomputes the live instrument. It
  is the authenticated-rendering-nobody-consumes class P4.7.6 removed from the RESULT, still sitting
  in the record the RESULT is about.
- **`note` — removed.** Prose in a machine record is P3.1's retired notes seat.
- **`supersedes` — removed, and here is my reasoning, because it is not the option you offered.**
  Classifying it `NON_AUTHORITATIVE` is defensible; checking it is not. The only honest check —
  "the run it names has a terminal receipt" — *requires a receipt the chain rule expressly declines
  to require*, since receipts unreachable from the record are declared superseded history that is
  neither validated nor required absent. A rule that contradicts a rule one function away is where
  the next defect lives. The superseded id is printed by `--pin`, which is a human act, and recorded
  in the ledger, which is prose on purpose.

**One I found while removing those: `abort_reason`.** `--abort` wrote it into the record, undeclared,
and the reason was *already* in the ABORTED receipt's `note` — a declared `NON_AUTHORITATIVE` seat
in an immutable artifact. Same species, same round, removed the same way.

**`role` is a vocabulary now, not a string to hash.** It was bound into `runCore` and therefore into
`run_id`, so `role: "arbiter"` merely moved the identity: re-identify and the record is legal.
Which subject is the REFERENCE and which the CANDIDATE is most of what a completed run means.

**`blind_contract_revision` is checked against the release** (§0), gated the same way as the release
comparison — not for ABORTED/COMPLETE, where the tree is allowed to have moved on.

---

## 3. Falsifiers — AA1…AA10, and AA8 runs first

`EXPERIMENT-FALSIFIERS: PASS — 44/44, EACH IN ITS OWN WORLD.`

```
AA8  an honest PINNED → CANDIDATE_FROZEN → REVEALED → COMPLETE run's every evidence artifact
     reads unambiguously and still verifies — 10 artifact(s) across a 4-link chain, 0 refused
AA1  duplicate "status" in the run record's BYTES — first-occurrence "REVEALED" · Node "COMPLETE"
AA2  duplicate "status" in a reachable transition receipt — first-occurrence "REVEALED" · Node "COMPLETE"
AA3  a duplicate semantic member in the RESULT, refused BEFORE its semantics — first 999 · Node 10
AA4  an archived observation naming TWO implementations, refused before it is scored
     — first "evil-first-reader" · Node "javascript" · digest updated to match
AA5  revealed:true + verdict_override, run_id untouched
AA6  blindness:"DISQUALIFIED" on a run adapter
AA7  the instrument_files seat put back, zeroed, with an honest instrument_digest
AA9  one raw 0xFF inside a member name
AA10 role "arbiter", and the record RE-IDENTIFIED around it so run_id agrees
```

Four notes on how these are written, since the battery's construction has been a source of defects
of its own:

1. **AA8 runs first**, for the P4.7.1 destroyed-fixture reason: if the honest artifact does not
   survive the new boundary, every refusal after it is a refusal of something else. It walks the
   receipt chain from COMPLETE and reads all ten artifacts through the strict reader.
2. **Every attack inserts the bogus member FIRST**, and **each case prints BOTH readings** — the
   defect is the pair, not the duplicate.
3. **AA4 updates the RESULT's recorded digest to match the bent bytes.** That is the case's whole
   point and yours: a digest authenticates BYTES and not their READING, so the document re-digests
   perfectly and attributes the measurement two different ways. This is the one that has to hold
   when the producer is Go.
4. **AA3 asserts the refusal came from the byte boundary** and that the RESULT's `holdout_entries`
   semantics were never reached, so "refused before it is checked" is measured rather than intended.
   AA1, AA2, AA4 assert the same; AA9 asserts the UTF-8 refusal by name.

`Z` still holds: the authoritative record is byte-identical, 25 receipts present and none written by
the battery, 10 sandbox worlds built and removed.

---

## 4. Two of my own, and the first is a scope defect worth your attention

**(1) `holdout_score_core.mjs` contained a literal NUL byte, at line 79, in the sentinel whose own
comment says it is written as an escape.**

```js
if (v === ABSENT) return "\x00ABSENT";   /* a sentinel no JSON value can encode to, written as
                                            an ESCAPE because a literal NUL makes file(1) … */
```

The grid has had a NUL law since v1.33, written *because* this exact thing had happened twice in this
exact file, and its own comment says "a rule that has to be remembered is a rule that will be
forgotten, so it is checked." **Its scope was a hand-typed directory list — `["", "bridge"]` — and
P4.6 moved the scorer into `docs/spec/proof-wire/experiment/` to put it inside `experiment_digest`.
The file walked out from under the rule written for it.** `/usr/bin/grep` reports the module as
"binary file matches" and every text tool skips it silently, which is how I found it: a grep for the
scorer's imports returned nothing, and nothing reads exactly like an answer.

The scan is recursive over the spec tree now. And the same species one probe over: the grid's
`INSTRUMENT_MEMBERS` was a hand-typed copy of the frozen `INSTRUMENT` list, deliberately independent
— which is right — but nothing compared them, so they could silently diverge. They must be equal
now, so a divergence is *reported* rather than quietly shrinking what "the instrument" means. Adding
`evidence.mjs` to one and not the other is exactly the edit that would have done it.

**(2) In the machinery built to remove hand-typed numbers, a greedy `v([0-9.]+)` swallowed the full
stop ending the gate's sentence and derived `grid v1.67.0.`** Caught by reading the output. Anchored
to three components now.

**(3) Three refusal paths that would have crashed rather than reported**, found auditing the new
boundary against itself: `loadChallenges`, the runner's release read, and `blind_run.mjs`'s
`readRun()` all **threw** on an ambiguous artifact where every other refusal in this plane reports —
a stack trace from the gate instead of a verdict, and in `--abort`'s case a record that could not be
aborted without a diagnosis. All three report now.

**(4) And three ACCEPT vectors were missing** for classes I had reasoned through and not measured: a
raw astral character (two UTF-16 units, and this reader walks units), a raw DEL, and an **escaped**
NUL. Writing that last one put **a literal NUL into `evidence.mjs`** — defect (1), committed while
adding the vector for it — and the reader refused its own corpus in the same minute. I am reporting
it because it is the cleanest possible demonstration of why that grid law exists.

**(5) And the review pack you are reading reported three failures over a green tree.** `verify.sh`
invoked its shell gates as `./negative_battery.sh`, which needs the executable bit to have survived
the archive. `unzip` restores modes; Python's `zipfile.extractall` — the obvious fallback, and what
this machine has — does not. All three printed `Permission denied`, showed no detail, and the pack
said `FAILURES PRESENT` over 392/392, 14/14 and 3/3. **That is the false-red dual of everything this
plane has been fixing**, and a reviewer cannot distinguish it from a real failure without redoing the
work the pack exists to save. Found by running `verify.sh` the way you would rather than trusting it
built. It names the interpreter now; if a previous pack ever showed you a bare `FAIL` with no output
under those three labels, that was this.

---

## 5. What is NOT claimed

- The wire's parser-strictness table (`TRVM-PROOF-WIRE-v1.md` §3.6) is **unchanged**, and the blind
  contract's deliverable 2 still requires those observable outcomes. This boundary governs the
  document an implementation writes *about* that work. New **§4.1** of the contract states it, which
  is why `experiment_revision` is **8** and `blind_contract_revision` moved with it.
- No proof/DAG work, no holdout changes, no scorer semantics, no new experiment semantics — as you
  scoped it. `holdout_score_core.mjs` changed only in its read path and its NUL.
- The reader is stricter than JSON *for evidence*. It cannot stop an operator with write access from
  writing unambiguous bytes that lie; it stops one artifact meaning two things.

---

## 6. Your reporting defect: fixed by deriving, not by another architecture

You were right, and right about the remedy. `brief_identity.mjs` derived the three **identities** and
`--check` passed while the brief said `469 citations` twice and a clean replay said `471`. Deriving
some fields of a document and hand-entering the adjacent one is this round's species, in the round's
own brief.

The grid line is derived now — **by running the gate and reading its own summary**, because the
citation total spans `invariant-grid.json` and every shipped artifact and ledger, and re-counting it
here would be that second implementation again. A gate that does not pass has no quotable number, so
a red tree refuses rather than reporting a stale one.

One consequence, stated because it is a real constraint and not an accident: the ledger is one of
the sixteen artifacts the citation scan reads, so **writing the ledger moves the number this brief
must quote**. The brief is therefore finalised after the ledger, and `--check` is what enforces the
ordering rather than my remembering it.

**And carrying the derived line is necessary, not sufficient** — the P4.7.6 brief would have carried
it and still said 469 in prose beside it. So `--check` also refuses **any** `N entries / M citations`
anywhere in the brief that disagrees with the tree, and any `grid vX.Y.Z` that is not this tree's.

---

## 7. Where this leaves us

```
P4.7.3  COMPLETE didn't require evidence
P4.7.4  COMPLETE requires evidence + replays interoperability
P4.7.5  COMPLETE also replays conformance
P4.7.6  parsed evidence collections cannot equivocate
P4.7.7  evidence BYTES and the RUN record itself cannot equivocate
```

Ten defects over seven passes; **the last five were defects in repairs made one or two passes
earlier**, and this one was a repair that stopped one boundary short of its own stated claim. That
remains a property of this work and is recorded as one.

Still not P4.8. Same closure sequence, narrow fix.

**AA1–AA8 survive, plus AA9 and AA10.** If you cannot produce another ordinary-interface
disclosure / completion / conformance / evidence-equivocation attack, the next thing is the
clean-room harness and the Qwen3 → Go run — `blind_package.mjs --emit <empty-dir>` → isolated env →
Go from the package alone → `--freeze-candidate --binary` → `--reveal` → `--complete`.

Two things I would like you to attack specifically, because they are new interfaces and a new
interface is a new place for the binding rule to be violated:

1. **The reader itself.** It is hand-written. The `--selftest` claim is *accept ⊆ agree-with-JSON*,
   over 43 vectors I chose. If you can find bytes it ACCEPTS that `JSON.parse` reads differently,
   that is a worse defect than the one it fixes.
2. **`verifyRun` reading from disk by default.** The pre-write callers pass rendered bytes. If there
   is a path where the bytes verified are not the bytes that end up on disk, the freeze has a gap in
   it exactly where P4.7.1's was.
