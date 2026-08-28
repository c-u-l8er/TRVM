# The blind implementation contract

**Status: PROCEDURAL, not normative.** This document does not define the protocol. It defines the
experiment the protocol is about to be subjected to, and what would make its result meaningless.

---

## 1. The question

> Can a second implementation, written from the specification rather than from the source, construct
> the same proof objects and predict the same failures?

Not *can somebody port the JavaScript*. If the second implementer learns the protocol by reading the
checker, the result is a port, and a port agreeing with its original measures nothing.

---

## 2. What the implementer receives

A run is against **one immutable release, named by its identity**, not against "the spec tree as it
stands". The release package is:

```
docs/spec/proof-wire/SPEC-RELEASE.json         the CURRENT pointer
docs/spec/proof-wire/releases/<srel>.json      the immutable archived record
docs/spec/proof-wire/TRVM-PROOF-WIRE-v1.md
docs/spec/proof-wire/TRVM-VERIFIED-CLAIM-v1.md
docs/spec/proof-wire/TRVM-NESTED-COMPOSITION-v2.md
docs/spec/proof-wire/schema/
docs/spec/proof-wire/vectors/                  public corpus + pinned JCS import
docs/spec/proof-wire/requirements/open/        what is DECLARED-OPEN and why
docs/spec/proof-wire/experiment/               this contract, the recipe grammar,
                                               the observation grammar and schema,
                                               and the synthetic adapter fixture
RFC 8785, RFC 8259, and any public JCS implementation
```

and the implementer is told, in writing, **which `spec_release_id` and which `blind_package_id` the
run selects**. `srel` is recomputable from the package — it is
`srel-SHA256("TRVM-PROOF-WIRE-SPEC-RELEASE-v1|" + canonicalWire(release_core))` — and computing it is
a fair first conformance exercise, because it uses the same canonical encoder as everything else.

**Two identities, because they answer two questions.** `srel` says what the specification *means*;
`bpkg` says which *bytes* were delivered. They are the same split as `verified_claim_sem_id` versus
`artifact_root`, and both are needed: `requirements/open/` is deliberately outside `spec_digest` so
that a declared-open register may grow without implying a protocol change, and it is deliberately
inside `bpkg`, because the implementer reads it. Editing it moves `bpkg` and not `srel`, and that is
the correct behaviour of both.

The selection lives in a **run record** (`TRVM-BLIND-IMPLEMENTATION-RUN-v3`) that points at the
release. The release does not point back at the run: `spec_release_id` already binds
`experiment_digest`, so putting the run inside the experiment surface would make the identity depend
on a record that names it.

If a later release is issued while a run is in progress, **the run does not silently move.** It
remains pinned to the `srel` it selected. A substantive change aborts that run and starts a new run
record against the new release; that is a human act and no gate performs it.

### 2.0 What the mount is, exactly

The implementer's project is a **closed artifact**: the mount contains **exactly** the regular files
that contribute to `bpkg`, and nothing else.

- **No symlinks and no special files.** The package walk uses `lstat` and refuses a symbolic link, a
  FIFO, a socket or a device outright — including a link whose target is inside the package, because
  a special case is a place to hide. Independently, every packaged file's `realpath` must lie inside
  the package root. Until P4.7.8 the walk followed links, so
  `innocent.md -> ../../../governance/round-11-ledger.md` was manifested as an ordinary file with a
  digest and delivered a round ledger into the clean room.
- **No manifest inside the workspace.** `BLIND-PACKAGE.json` used to be written into the mount and
  then exempted from the equality check — 59 files manifested, 60 delivered, and the sixtieth was
  outside `bpkg` by construction. It is written *beside* the mount now, on request, and never inside
  it. **Which `srel` and which `bpkg` were selected is told to the implementer in writing**, here and
  in the run record; the workspace needs no self-description.
- **The mount is written from the manifest**, file by file, rather than copied as a directory.
  Copying a directory delivers whatever is in it; copying a manifest delivers what was measured.
- **`--emit` refuses a package the run never pinned**, so the delivered bytes are the selected bytes.
- **Exactly the directories the manifest implies, and no others.** The permitted directories are
  derived from the parent paths of the manifested files, so nothing is added to `bpkg` and the check
  is arithmetic. An empty directory carries no bytes for a digest to notice and its **name** is still
  something the implementer can read.
- **One filesystem link per file, and an ordinary directory at the root.** A hard link is a regular
  file that `lstat` cannot distinguish, and a symlink standing in for the root is a name that can be
  re-pointed after it has been checked.
- **Portable path segments only** — `[A-Za-z0-9._+-]`, NFC, and no two paths equal after ASCII
  case-folding. Two names differing only by case are **one object** on a case-insensitive filesystem,
  which is the hard-link defect one layer up.

### 2.0.1 And the mount is a private object, not a set of digests

**A digest is a statement about bytes at an instant, and an object with a second name has no single
instant.** Until P4.7.9 this section told a harness to verify the mount immediately before the first
model request and then mount it read-only. **That sequence is not sufficient, and the demonstration
needs no package byte to be wrong**: replace a file with a hard link to identical bytes outside the
mount and verification passes — every digest is correct, because at that instant the bytes *are*
correct — then write to the outside name, and the verified package changes with it. A read-only bind
makes *that mount point* read-only and leaves the object underneath writable through every other name
it has.

So the clean-room artifact is **an exact filesystem namespace of privately owned immutable objects**,
and the harness *establishes* that rather than checking for it:

```
unshare a mount namespace           the view has no name outside it
    ↓
mount a fresh tmpfs                 new inodes · one link each · no older descriptor
    ↓
emit the package into it            from the manifest, refused unless it is the pinned bpkg
    ↓
remount read-only                   in the SUPERBLOCK sense, asserted against the kernel
    ↓
verify THE FINAL VIEW               in the process that will serve it, as its first act
    ↓
serve the bytes that were verified  never the path — the package is not read from disk again
```

The verification happens **after** the isolation exists, not before it, and the program that verifies
is the program that serves. Verifying one pathname and later resolving another is the same defect one
layer up.

**The implementer reads the package through two functions** — `list_files()` and `read_file(path)` —
over a dictionary whose keys are the manifested paths. That is not a filesystem, so `..`, an absolute
path, a symlink, a case-folded name and a race are not defended against; they are unrepresentable.
Source goes back through `write_source(path, content)` into a **separate, writable workspace**, which
is never part of the package.

**What is not claimed.** None of this defends against an operator with write access to the
repository — the declared threat ceiling of the whole experiment — and it cannot make a model
provider honest about which weights answered. It removes ordinary aliasing and every window between
verification and use.

### 2.1 What is frozen, and when

```
PINNED             srel + bpkg + the measuring instrument + the reference implementation
CANDIDATE_FROZEN   + the candidate's source digest, binary digest and recorded environment
REVEALED           the challenge set is opened — REFUSED before CANDIDATE_FROZEN
COMPLETE           scored, with no unclassified interop finding outstanding
ABORTED            terminal
```

**The reveal is refused before `CANDIDATE_FROZEN`, and that is the transition the record exists to
guard.** Opening the challenge set first is how an implementation comes to be adjusted in the light
of the thing it is about to be measured on. A status word that names an implementation without
digesting it does not freeze anything.

Every transition writes an **immutable receipt**, rather than overwriting the only record of what the
experiment was.

The **measuring instrument** — the scorer, the runner, both schemas and the synthetic fixtures — is
inside the package you receive and inside `experiment_digest`. That is not a convenience: it means a
change to how you are scored moves `srel` and reddens the run. You may read the scorer. You cannot
read the challenges.

## 3. What the implementer does NOT receive

```
any file under governance/                — checkers, producers, schema helpers,
                                            grammar constants, canonicaliser
the holdout challenge set                 — see §5. Its GRAMMAR is public
                                            (experiment/HOLDOUT-RECIPE-v1.md);
                                            its CONTENTS are not
```

A translated or transliterated `canonicalBytes` is disqualifying. An independent RFC 8785
implementation is not: **independence from TRVM's implementation is the point; independence from RFC
8785 is not a virtue.**

---

## 3a. Blindness is a property of the AGENT, not only of the directory

For every other round in this project, letting a session read the other sessions' work is an
advantage and is deliberately encouraged. **For this one experiment it is contamination**, and
hiding `governance/` on disk does not remove it: a model that has already discussed
`nested_claim_sem_id` in another conversation is not implementing from the specification, it is
recalling an implementation, and the run would measure nothing while looking like it measured
something.

So the implementing agent or session MUST NOT have access to:

```
previous TRVM conversations or their summaries
user memory, project memory, or personal-context retrieval
connected project sources, or repository search outside the released package
reviewer briefs, review packs, or round ledgers
the holdout challenge set
```

**The P4 reviewer sessions and the session that authored this release are DISQUALIFIED as blind
implementers.** They have read the JavaScript, the checker architecture, the holdout construction
and the scoring design. So is a fresh session on the same account if its harness can retrieve any of
the above — a new chat window is not by itself isolation.

Use an isolated coding workspace whose mounted project is the frozen release package and allowed
public dependencies, and nothing else. **Record the implementation environment, model and tool
version in the findings**, because "which agent, with what access" is part of what the result means.

This section is the reason the experiment can produce a measurement at all, and it is the easiest
one to violate accidentally.

---

## 4. Deliverables

1. Parse and emit canonical wire octets; reproduce every `wire_positive` vector and every
   `jcs-upstream/` pair.
2. Produce every `wire_negative` outcome from `TRVM-PROOF-WIRE-v1.md` §3.3, including the
   normalisation in §3.6 — the internal stage at which a strict parser notices a duplicate member
   name or invalid UTF-8 is **not** the observable outcome.
3. Compute `artifact_root`, `verified_claim_sem_id`, `nested_claim_sem_id`, `aggregate_id`,
   `structure_sem_id` and `verifier_policy_id` from the specifications, and reproduce the frozen
   positive fixture's values.
4. **Construct a FAMILY of artifacts the implementation asserts are VALID** — not one golden example.
   At minimum: an annotation-only variation; a permutation of the reference set (a SET, per
   `TRVM-NESTED-COMPOSITION-v2.md` §6.3); an operand-order variation (ordered, per §4.1, and
   therefore a *different claim*); a variation with a different but valid child combination; and a
   shared-child diamond variant.
5. Construct known-invalid artifacts with **predicted refusal sets**, compared for exact set equality.
6. **Ship a holdout ADAPTER**: a program that reads a challenge in the frozen recipe grammar
   (`HOLDOUT-RECIPE-v1.md`), applies it to the named frozen fixture, and writes a
   `TRVM-HOLDOUT-OBSERVATION-v1` document (`HOLDOUT-OBSERVATION-v1.md`,
   `holdout-observation-v1.schema.json`). The adapter is written **before** the challenges are
   revealed, against the published grammar and the synthetic fixture in `experiment/fixtures/`.

   This is deliverable 6 rather than a footnote because it is the interface the measurement runs
   over. If the shape of a Go observation were decided after the challenge set was revealed, the
   measuring instrument would have been modified in the light of what it was about to measure, and
   the preregistration in §5 would be worth nothing.

### 4.1 The observation document is read at a byte boundary that is stricter than JSON

The measuring instrument reads every evidence artifact — including the adapter's observation
document — through its own strict reader (`experiment/evidence.mjs`), **before** any of it is
scored. A document that does not cross that boundary is **REFUSED**, and a refused observation is
not a failing measurement: it is an absent one.

Beyond RFC 8259 the reader refuses four things, and each is a case where the same bytes have two
readings in two conforming implementations:

| refused | why it is not merely pedantry |
|---|---|
| a **duplicate object member name**, at any depth | `JSON.parse` keeps the last; a first-occurrence reader keeps the first. An observation whose bytes read `"implementation":"evil","implementation":"honest"` attributes the measurement two ways |
| an **unpaired surrogate** (`"\uD800"`) | Node keeps it; Go's `encoding/json` substitutes U+FFFD. This one would otherwise surface as an interoperability *finding* against a correct implementation |
| **invalid UTF-8**, or a byte-order mark | a replacement character supplied by a lenient decoder is a character the producer never wrote |
| **anything after the document** | a file holding two documents has two readings |

This is a property of the INSTRUMENT, not of the protocol under test. `TRVM-PROOF-WIRE-v1.md` §3.6
still pins what a conforming implementation must do with each of these classes *on the wire*, and
deliverable 2 still requires exactly those observable outcomes. The boundary described here governs
the document the implementation writes ABOUT that work, and its purpose is that parser permissiveness
stops being an accidental property of whichever implementation happens to be doing the measuring.

The reference adapter's own output satisfies it, and `node experiment/evidence.mjs --selftest`
states the reader's two claims: every input it accepts is read exactly as `JSON.parse` reads it, and
the inputs it refuses beyond JSON are the ambiguous ones.

---

## 5. Blindness has three halves

**Source-blind** — §3. **Agent-blind** — §3a.

**Answer-key-blind** — a **holdout** challenge set is frozen at the same time as the public corpus,
committed by digest in the release, and not given to the implementer. Public vectors are for
development; the holdout is the measurement. An implementation tuned until the public vectors pass
has been fitted, not written.

The holdout records **no SHA-256 value that any implementation produced**. It records constructions,
recipe steps, and machine-evaluable predicates — because recording this implementation's answers and
hiding them would make it the oracle by virtue of having gone first. Where the specification fixes an
exact structural quantity, the holdout may commit that quantity, since it is derivable from the
specification by hand and is not a hash.

---

## 6. When the implementer has to ask

**Do not silently patch the specification and continue.** That turns the experiment into
co-authoring and destroys the only measurement it produces.

Record, against the frozen revision:

```
frozen_spec_revision
the question, verbatim
why the specification was insufficient
the ruling
classification (§7)
the superseding spec revision, if any
```

Then publish a **numbered** revision. **After a substantive revision, restart the implementation from
a fresh session against the revised specification** if the result is still to be called blind — the
implementer who asked now holds knowledge the document does not contain.

---

## 7. A disagreement is a finding before it is a fault

```
SPEC_GAP                     the document does not say
SPEC_IMPLEMENTATION_CONFLICT the document says something the JS does not do
JS_CHECKER_DEFECT            the JS is wrong
GO_PRODUCER_DEFECT           the second implementation is wrong
VECTOR_ORACLE_DEFECT         the frozen corpus is wrong
JCS_DEPENDENCY_DIVERGENCE    two RFC 8785 implementations disagree
```

**The highest-value event available in this round is:**

```
the second implementation says VALID   →   the JavaScript checker REFUSES it
```

because it cannot be predicted, and because at least one of the six classes above must apply. It is
investigated before it is assigned.

---

## 8. Why Go

Not because its default behaviour differs by magic. Because it forces a genuinely different runtime
and type system, produces a standalone binary that shares nothing with Node, and — with
`encoding/json/v2` — offers a **strict byte-oriented JSON boundary that rejects duplicate member
names and invalid UTF-8 by default**, where the legacy library and Node both accept duplicates and
substitute U+FFFD.

That difference is the reason §3.6 of the wire specification exists. A strict reader will notice
these inputs at a different stage than the JavaScript does, and the protocol must already have
decided what both are required to *report*. Settling that while debugging an interop failure would be
settling it with a thumb on the scale.

---

## 9. What would make the result worthless

- The implementer reads `governance/`.
- The specification is edited during the run without a numbered revision.
- The holdout set is consulted before the implementation is frozen.
- The conformance corpus is regenerated by anything other than a deliberate human update
  (`law:proof.conformance-oracle-frozen@1` — the corpus was, until P4.3, rewritten by the very run
  that checked it).
- A Go/JS disagreement is closed by changing Go without first classifying it under §7.
