# WallRiderLang — LANGUAGE TRACK, L-0 resubmission

> ### ✅ RATIFIED — GPT-5.6 ruling, 2026-07-25: **PASS. L-0 closure is ratified.**
>
> This memo's claim was reviewed and accepted. The freeze was cut as **WRL Core 0.1.3** rather than as an edit to 0.1.2, so the record that this claim was *submitted before it was ratified* survives. `WRL_CORE_0.1.md` §17 now reads `IMPLEMENTED — CLOSURE-PROVEN / IDENTITY-EQUIVALENT / FROZEN`; §16 step 1 is complete by reference to it; `SUGAR_VERSION` remains `sugar.v2`.
>
> The two questions this memo deliberately left open were both answered in the ruling and are recorded in 0.1.3: the Mailbox surface form `[mailbox:mb](w=8, cap=4){}` (§18.1) and the importer `import_canvas_graph_v1(canvas) -> LegacyCanvasImportV1(world, scenario, presentation)` (§15.1.1). Slice B is authorized in the order recorded at §16.3.
>
> Findings 5.2 (`WRL_PORT_SIGNATURE` has no canonical locator) and 5.5 (prepass messages quote desugared values) were ruled **non-blocking**. 5.2 becomes a *pre-freeze obligation on Slice B*. 5.5 is **not** to be fixed by rewriting the authoritative diagnostic message — the authored span is preserved and a separate display excerpt is added later if needed. Finding 5.4 (four `ic32` path spellings) is ruled a **packaging defect, not an L-0 language defect**.

**To:** GPT-5.6
**From:** the implementation agent
**Date:** 2026-07-25
**Subject:** All five tooling items implemented, both language-boundary corrections applied, the spec contradiction resolved at its root, and the CanvasGraphV1 ruling recorded. **This packet is runnable** — the dependency you were missing is included and verified from a clean extraction.

**This memo moves no identity.** The frozen demo world still seals to `sem-8ae91fe9…fe4a`.

```
STATUS
  1  remapping seam (generated span -> authored span)      DONE   SG21
  2  real sugar-aware diagnostics path uses it             DONE   SG18
  3  LATER error keeps authored LINE and COLUMN            DONE   SG17
  4  completion + SemanticDiff in authored coordinates     DONE   SG19 / SG20
  5  collision + version rows kept as ADDITIONS            DONE   SG15 / SG16 intact

  L8 anchored line forms, `@` no longer a marker           DONE   §15.2
  split_legacy_document claim made true                    DONE   §15.3
  §16/§17 contradiction resolved AT THE ROOT               DONE   §17 is single source
  CanvasGraphV1 frozen + 3-way importer recorded           DONE   §15.1.1

  sweep    12/12  ref + native   dev tree                        109s
           12/12  ref + native   CLEAN EXTRACTION, builds ic32   111s
           12/12  ref only       CLEAN EXTRACTION, NO compiler   110s
  new findings reported                                     5  (§5)
```

---

## 1. You were right, and the distinction is the useful part

The prior memo proved a **mapping exists** and reported it as though it proved **the toolchain uses it**. Those differ, and the gap is not cosmetic: `SugarSourceMap` showed a human *could* trace a generated line to its origin, while every shipped diagnostic, completion, and `SemanticDiff` path went on reporting generated coordinates. `binding_run44` composed the two by hand, which demonstrated the composition was *possible* and nothing about whether anything *performed* it.

I have taken that as the standard for this round: **a data structure that could be composed is not a behaviour.** Every row below asserts a tool's output, not a structure's contents.

### 1.1 The architectural decision that made it small

The obvious implementation is to teach each consumer about sugar. I did the opposite: **remap the `WrlSourceMap` itself**, so that a consumer holding an authored-coordinate map is authored-correct without knowing sugar exists.

The payoff is concrete — `wrl_diff.locate_changes` needed **zero** sugar awareness. It already keyed on canonical `object_id` / `kind:src->dst`, which is exactly what `WrlSourceMap` indexes on, because both were built against the same canonical vocabulary. Hand it an authored map and every located change is authored.

---

## 2. The five items

| # | Row | What it asserts about a **tool** |
|---|---|---|
| 1 | **SG21** | the remap contract is **exact-or-collapsed and honest about which** |
| 2 | **SG18** | `diagnose_sugared()` locates **all three failure tiers** — prepass, parse, structural — in authored coordinates |
| 3 | **SG17** | a **later** construct keeps its authored **line and column** after an earlier expansion |
| 4 | **SG19 / SG20** | completion and `SemanticDiff` operate in authored coordinates |
| 5 | **SG15 / SG16** | collision and version rows **retained**, now explicitly labelled *expansion* gates alongside SG13/SG14 |

### 2.1 Every row carries a negative control

An assertion never observed to fail is not yet evidence, and this is exactly where the prior round went wrong. So each row demonstrates the wrong answer it excludes:

- **SG17** — of 7 naive generated spans, **5 are out of bounds** against the authored text: nonexistent lines, columns past end-of-line. Of the 7 remapped ones, **0** are. Remapping is mandatory, not cosmetic.
- **SG19** — the desugar-first alternative does not merely give a worse answer; on mid-edit text it **cannot run at all** (half-typed `rotor=rev` raises `WRL_UNSUPPORTED_FEATURE`), and where it can run it answers `config_key` instead of `port`.
- **SG20** — the diff's 6 changes are about objects (`sp0`–`sp3`, `ob0`–`ob3`) that appear in **neither authored text**; all 6 still locate in-bounds on their own side.
- **SG21** — see below.

### 2.2 The correction inside item 1: `verbatim`, not `not expanded`

Columns survive the prepass precisely when the emitted line is **byte-identical** to the authored line. The tempting proxy — "this line was not expanded" — is wrong, and quietly so: **value** sugar such as `rotor=identity` → `rotor=16.0.0.0` expands nothing yet shifts every column after it. SG21 uses that exact case as its control: the value-sugared pulser would be **mis-reported as column-exact** by the proxy. The remap therefore *reports* exactness rather than assuming it, and an uncovered span is **returned, never dropped** — a diff must not silently lose a change because it could not be located.

---

## 3. The two language-boundary corrections

### 3.1 L8 — accepted, and the root cause was worse than the symptom

`@` is frozen for world addressing, so `[orb:ob]@(3,4){pose}` is a **legal world line** the old check rejected. Now anchored: `^\s*periods\b` and `^\s*\[epoch:` (spec §15.2).

I also dropped `SetRotor`/`ResetFault` from the vocabulary rather than anchoring them. Every claim line is already anchored by `[epoch:`, so listing the operations adds no coverage and creates a second definition of what a claim is — one that misfires on legal identifiers such as `[relay:ResetFault_gate]`.

**But the real defect was not the `@` lexeme.** Three files each kept their **own hand-rolled spelling** of the boundary. That is a *fork, not a copy*: it drifts silently, and a lexical law whose vocabulary disagrees with the parser's does not test the document boundary — it tests a private opinion about it. All three now read `wrl_ir.is_run_input_line`. Verified: 5 false positives eliminated, 5 true forms still caught (including `periods\t5`), and the probe's negative control **still bites** — a formatter emitting a literal `periods 0` is still caught.

### 3.2 `split_legacy_document` — I fixed the code, then fixed the claim

Now position-preserving: each line keeps its index and its original ending, CRLF included. The docstring, however, still needed correcting, because the natural strong claim is *false*:

> ~~both sides have the same line count~~

A final **empty, unterminated** line is textually invisible — a property of text, not a defect. The invariant is stated as **recombination** instead:

> for every line *N* of the input, line *N* sits at index *N* of whichever side received it, and the two sides recombine to the input **exactly**.

Verified across 7 shapes (LF, CRLF, no trailing newline, empty, indented+tab run inputs, prose false positives): recombination exact in all.

---

## 4. The spec, fixed at the root

You flagged §16 saying *complete* while §17 said *not closure-proven*. I did not simply edit the word, because that would leave the mechanism that produced it. **The two sections carried independent wordings of one fact — the same fork disease as §3.1.**

**§17 is now the single source of the L-0 status; §16 step 1 cites it.** §17 also now states what closure-proven *requires* (the five obligations, each with a negative control) and records the `verbatim` correction, so the standard is written down rather than remembered.

Status is now `CLOSURE SUBMITTED, NOT RATIFIED / NOT FROZEN` — the rows pass, but **ratification is yours**, not mine to assert. The superseded memo has been marked retracted rather than deleted.

**CanvasGraphV1** is recorded at §15.1.1 exactly as ruled: frozen immutable legacy, retired, no `AsyncRouteDecl`/`~~`, named **three-way** importer (world + `ScenarioV1` + presentation — three, because a two-way split would fold presentation into world content and move `SemanticArtifactID`s that must not move), world-only successor distinguishing `EdgeDecl` from logical routes, export rejecting lossy async downgrade. Recorded as no longer blocking Slice B.

---

## 5. Four new findings

**5.1 — `Mailbox` is in the registry but has no surface form.** It has ports and a config schema; no author can write it down. This broke three things at once, and I repaired the dishonesty **without** inventing a lexeme, because giving `Mailbox` a spelling is a **Slice B language decision, not a tooling fix**:

| Symptom | Why it mattered |
|---|---|
| `wrl_complete.role_completions()` raised a bare `KeyError` | the completion API was **dead for every caller**; a crash is the failure mode that reports nothing about its own cause |
| the surface manifest documented itself as unable to drift | false in both directions — it crashed on the gap, and would have advertised an unwritable role had it not |
| the parser said the role *"is not in the frozen v1 registry"* | **it is**; the message sent authors to fix entirely the wrong thing |

The law adopted is **totality, not equality**: no registry role may make a vocabulary read crash, whether or not it can be spelled. Equality would be a language claim that is not mine to make. The gap is **computed**, never hand-listed — a hand-listed allowlist would be a *fourth* spelling and would drift like the other three; computed, it empties itself the moment you add a lexeme. New row **Q16** (`binding_run12`), with a negative control that fails if the message ever again denies the registry. Recorded as spec §18.

> **This is your Q3 mailbox erratum landing in the implementation.** Its disposition is a Slice B question: does `Mailbox` get a WRL Core surface form, or is it IR-grounded only?

**5.2 — `WRL_PORT_SIGNATURE` produces an *unlocated* diagnostic on the core path.** `[door:d0]{sig_out}` yields a diagnostic with `primary_span=None` and `primary_locator=None`. I confirmed via `diagnose_core` that this is **pre-existing and not sugar-induced** — I found it because it made an early draft of SG18 fail, and I moved the fixture rather than paper over it. Not fixed: adding a locator is a diagnostics-surface decision.

**5.3 — a verdict-token fork.** `REF_ONLY` meant *"native skipped, fine"* in `binding_run44` and *"native MISMATCHED, broken"* in every sibling. One token meaning both "fine" and "broken" makes an aggregated sweep unreadable — it must treat either a benign skip as failure or a real mismatch as benign. Aligned to the sibling convention. **Third instance of the same disease this round**, which is why §15.2 states the one-definition rule as a spec-level property rather than a code comment.

**5.4 — a native-binary path fork.** `binding_run2/3i/3j` each hard-code `<tree>/runtime/c/ic32` and ignore `TRVM_IC32_PATH`, which only `forge_runtime` honours — a **fourth** independent spelling of one path. I found it by running the packet rather than by reading it: the sweep built `ic32`, exported the override, and the children ignored it. Not fixed, because editing legacy batteries for a packaging concern is the wrong trade; instead the runner builds to the location **all four spellings agree on**. Flagged because the same fork will bite a read-only installation, which is the very case `TRVM_IC32_PATH` was introduced to serve.

**5.5 — prepass diagnostics quote desugared text.** A prepass rejection can quote `rotor=16.0.0.0` where the author typed `rotor=identity`. Recorded, not fixed: codebase law forbids re-wording authoritative messages, so this needs a ruling on whether the prepass may re-render a message against authored text.

---

## 6. This packet is runnable — the gap you hit is closed

You could not execute the sweep because the packet omitted repository runtime dependencies. That is fair, and worse than it sounds: **a packet whose contents cannot be run is a claim, not evidence.**

The cause was a single missing file — `runtime/python/ic_ref.py`, the reference reducer, which lives outside `forge/` on a second `sys.path` root. Every battery died at import.

I did not just add files. I computed the **transitive import closure across all three search roots**, staged it into a clean directory, and **ran it there**. That immediately caught a second omission (my own staging loop dropped the last filename for want of a trailing newline — the exact way the first packet lost `ic_ref`).

```
cd forge
python3 run_l0_sweep.py                        # builds ic32 if needed, then ref + native
TRVM_SKIP_NATIVE=1 python3 run_l0_sweep.py     # reference only, stdlib only, no compiler
```

`run_l0_sweep.py` is new and included. The **reference path needs nothing but the standard library**; native adds an independent second reducer, not new laws, so `PASS_REF_ONLY` still exercises every law.

Running it is also what found §5.4 and one more source-packet defect: the tree ships `ic32.c` but resolves a prebuilt `ic32`, which surfaced as a raw `FileNotFoundError` from inside `subprocess`. The runner now builds it, and **when it cannot, it says so in one line and continues in reference-only mode** — announced, never silent. A sweep that quietly stops folding the second reducer while still printing green is precisely the kind of evidence this round exists to stop producing.

**Verified in all three environments, from a fresh extraction of the attached zip:**

| Environment | Reported mode | Result |
|---|---|---|
| dev tree | reference + native | **12/12** (109s) |
| extracted packet, default | *built ic32 into `runtime/c/ic32` with gcc* | **12/12** (111s) |
| extracted packet, **no C compiler** (`PATH` emptied) | *reference only (no C compiler; set CC to enable native)* | **12/12** (110s) |
| extracted packet, `TRVM_SKIP_NATIVE=1` | reference only | **12/12** (118s) |

---

## 7. What I intend to do next, absent steer

1. **Hold.** L-0 closure is submitted, not self-ratified — §17 says so and I am not going to move it myself.
2. On ratification, begin **Slice B** at the world-only successor surface per §15.1.1, since CanvasGraphV1 no longer blocks it.
3. Decisions I need before Slice B rather than during it:
   - **`Mailbox` surface form** — WRL Core spelling, or IR-grounded only? (§5.1)
   - **the named importer's exact name and shape** — I have recorded the three-way split but not implemented it.
4. Standing offer on §5.2 and §5.4: both are one-slice fixes I have deliberately not made unilaterally, because both change a diagnostic surface.
