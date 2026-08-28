# Round 27, pass P4.7.1 — the control plane is attacked, not described

**You were right to attack the lifecycle rather than accept it, and right that this is P4.7.1 rather
than P4.8.** All six findings reproduced before repair. The first one is the worst defect in this
entire line of work: the reveal boundary did not exist.

**Nothing changed in proof/DAG semantics, `citation_subject`, the holdout predicates, or the
warrant.** The experiment contract itself changed, so `experiment_revision` moved to **2** — which is
the case your instruction reserved for exactly this.

Pack: `TRVM/p471-review.zip` — **50/50 from a clean extraction**. Extract with `unzip`, not Python.

```
grid v1.61.0 (125 entries / 449 citations) · negative battery 392/392
EXPERIMENT-FALSIFIERS 10/10 · BLIND-PACKAGE · BLIND-RUN
HOLDOUT-HARNESS · HOLDOUT-INTEROP · SPEC-RELEASE · SPEC-VECTORS · SPEC-AGREEMENT
FIELD-AUDIT 46/46 · LIVE-DAG · NEST-FORGERIES 36/36 · harness 14/14 · runner 3/3

release  srel-550fc56e15597e69d8b3436925fd3e5c4f978dab8895811f492ce8d4a09c4ffe   exp revision 2
package  bpkg-bc7f251280d04dda6c59ee5f40d668dc05c41ab15573220aa3349fca775da381   49 files
run      brun-cffe125db2fec393f314afc69d1d8473d0b1ff7660bb3f37f4c07801d107ee10   PINNED
```

---

## 1. The reveal was a label — and it is the round's headline

Reproduced exactly as you described. A candidate whose entire body is

```js
writeFileSync("…/LEAK.json", readFileSync(process.argv[2])); process.exit(23);
```

frozen but **not** revealed, then an ordinary holdout run:

```
challenge ids the candidate received:  H1 H2 H3 H4 H5 H6 H7 H8 H9 H10
```

Your observation that `make governance` invokes that gate is the part that makes this decisive: the
experiment could have ended without anyone typing a command that says so.

**The gate is now in the frozen runner and deliberately not in the caller.** A rule enforced by
`holdout_score.mjs` — the mutable wrapper that *assembles the secret* — is a rule that wrapper can
drop. A rule inside `experiment_digest` cannot be dropped without moving `srel` and reddening the
pinned run. Concretely: a `reference` subject runs at every status (the challenges are already on its
own disk, so withholding them measures nothing); a `candidate` runs only at REVEALED or COMPLETE; and
**the challenges file is not written at all** when every candidate is withheld, so there is nothing on
disk to read. The withholding prints as `HOLDOUT-REVEAL-GATE: WITHHELD`.

## 2. The frozen subject was not the executed subject

Reproduced: repoint a frozen candidate's `command` and the `run_id` is byte-identical, BLIND-RUN
green. Your framing — *the identity of a subject must bind the authority by which that subject is
actually executed* — is the rule this tree has now rediscovered at the artifact layer, the citation
layer, the policy layer and now the experiment layer, so I put it in those words in the law.

`runCore` binds `command`, the sorted `package_files`, `binary_path`, `binary_digest` and
`environment`. Before spawn, `executionProblems()` re-verifies the executable's bytes — **a digest
checked earlier is a digest about an earlier file** — and:

- a **candidate must be launched as its own frozen executable**. I took your ruling that the binary is
  mandatory for this experiment: source is provenance, the executable bytes are the subject.
- an interpreter may only be handed a file **inside the frozen package**, and no command argument may
  name a path outside it.

## 3. Transitions trusted the state word

Reproduced: modify a candidate after freeze, `--reveal` succeeds and writes an immutable REVEALED
receipt. The immutability P4.7 added to make receipts trustworthy is what made the wrong claim
permanent.

`verifyLiveRun()` is your shared preflight, called by `--freeze-candidate`, `--reveal` and
`--complete`. **`--abort` is exempt, as you suggested** — a run that cannot be aborted when it is
broken is a trap.

## 4. The emitted mount was not `bpkg`

Reproduced: planted `REVIEW-BRIEF.md` survived, while emission announced itself as the mount. The
irony you noted is exact — a reviewer brief is one of the classes the source-side detector forbids.
The destination must be absent or empty, and the delivered tree is re-walked and required to equal the
manifest, with `BLIND-PACKAGE.json` the only permitted derived file.

## 5 / 6 / 7 — `--complete`, provenance, attribution

`--complete` exists and is a **measurement, not a status word**: it re-runs the frozen instrument over
the frozen subjects and refuses unless every adapter executed, every document validated, every
predicate was satisfied, interop was actually measured across ≥2 implementations, and zero findings
are outstanding. It writes an immutable RESULT receipt with the challenge commitment, every subject's
package and binary digest, **every observation document's digest**, the totals and the interop
outcome — so the measurement is re-checkable without trusting the record.

`toolchain`, `model` and `tool_version` are required; a provenance field that may be empty is one that
will be. And an observation's self-declared `implementation` must equal the adapter the run launched,
with duplicate labels rejected — otherwise the interop comparison is between labels.

---

# The falsifier battery — and the dry run is in it

`experiment_falsifiers.mjs`, wired into `gov-nest`, exactly your list:

```
PASS  A  CANDIDATE_FROZEN + a scoring run       → candidate receives ZERO H* bytes
PASS  B  modify candidate after freeze, reveal  → REFUSED, and NO receipt written
PASS  C  alter the command after freeze         → run identity moves, verification FAILS
PASS  D  command points outside the subject     → REFUSED before execution
PASS  E  omit model/toolchain/tool-version      → freeze REFUSED
PASS  F  emit into a dirty destination          → REFUSED
PASS  G  --complete from the wrong state        → REFUSED
PASS  H  two AGREEING subjects at REVEALED      → COMPLETE + immutable RESULT receipt
PASS  I  one observation disagreement           → UNCLASSIFIED_FINDING, COMPLETE REFUSED
PASS  Z  the battery restored the tree          → verified by digest, 0 stray receipts
```

**H and I are the dry run**, and you were right that it was not optional polish — you had effectively
begun it and it found real defects. It reaches COMPLETE over three subjects with interoperability
measured across three pairs, and a single mutated `artifact_root` that **no frozen predicate reads**
blocks completion. That is the comparison P4.6 could not make at all and P4.7 could only make against
a synthetic twin.

I added case Z because of a defect of my own, below.

---

# Two of my own

1. **The battery destroyed its own fixture.** `restore()` wiped the staging directory — which holds
   the reference observation document every fake subject reads — so H and I ran subjects that *could
   not start* and reported `COMPLETE REFUSED` for a reason with nothing to do with what they were
   testing. **A cleanup that destroys the fixture is indistinguishable from a defect in the thing
   under test**, and it cost me two passes before I checked the subject's own exit status. Restoring
   the run and cleaning the stage are separate operations now.

2. **My manual debugging left the run record at `REVEALED`** against a scratch subject, and the
   battery then captured that as its baseline and failed three cases for it — the fixture-drift trap
   in a new location. That is why case Z exists: the battery asserts, as its last act, that it left
   the tree exactly as it found it.

---

# Where this leaves it

I agree with your stopping rule and I am not going to invent P4.8. Every defect you found is closed
with a reproduction on both sides and an executable falsifier, and nothing about the experiment
remains open on my side.

The next step is the one the contract describes:

```
node governance/blind_package.mjs --emit <empty-dir>     # bpkg-bc7f2512…, 49 files
#   isolated environment, no TRVM memory / context / repository access
#   build Go from the package alone
node governance/blind_run.mjs --freeze-candidate --implementation go \
     --files <go-src> --binary <go-bin> --toolchain <…> --model <…> --tool-version <…>
node governance/blind_run.mjs --reveal
node governance/blind_run.mjs --complete
```

By §3a that implementer can be neither of us. I agree with your closing point: what TRVM needs now is
foreign evidence, not more self-description.
