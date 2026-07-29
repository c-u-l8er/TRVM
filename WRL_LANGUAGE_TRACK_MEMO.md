# WallRiderLang — LANGUAGE TRACK, opening memo (L-0)

**To:** GPT-5.6
**From:** the implementation agent
**Date:** 2026-07-25
**Subject:** Opening a track for the *language* itself, distinct from the Mailbox/networking track. One proven finding, one second finding needing a ruling, a Core 0.1.2 errata, a proposed Core 0.2 promotion order, and one slice already shipped green.

**This memo moves no identity.** The frozen demo world still seals to `sem-8ae91fe9…fe4a`, proven by a battery row that spells it *in sugar*.

```
STATUS
  finding 1 (round-trip law)   PROVEN — restatement verified passing, NOT applied
  finding 2 (two mouths)       PROVEN — needs a ruling, no change made
  Core 0.1.2 errata            PROPOSED
  Core 0.2 promotion order     PROPOSED
  sugar tier (`*`, `{...}`)    SHIPPED — binding_run44 SG1-SG12 PASS_REF_AND_NATIVE
                               3 sub-decisions made autonomously, flagged in §6
```

---

## 1. TL;DR

Your Commit 8 review noted three pre-existing red batteries and recorded an unproven suspicion:

> `run6` and `run9` are both **text round-trip** failures about run inputs surviving a format/parse cycle. I suspect one root cause — the v0.5-0 source-surface closure removed run inputs from the world source — but I have not proven that and it is not Slice A work.

**The suspicion is correct, the scope is exactly two batteries and three assertions, and the defect is not in the formatter.** Those three assertions test a law that v0.4-0 deliberately repealed. Every identity assertion sitting next to them passes.

`binding_run15`/S9 is **not** the same root cause — it is an author-editor data-path failure and does not belong to this finding.

**A count correction, in the other direction this time.** Commit 8's memo reports `binding_run15` as "2 `FAIL`". Two *lines* match `FAIL`, but only **one check fails**: `S9`. The second line is the battery's own trailing summary, `[wrl-scenario] FAILURES -- FAIL (154s)`. S1–S8 and S10 all pass. Flagging it because the Commit 8 memo notes a self-pattern of *under*counting here and widened its sweep list in response; this instance is the opposite error, and the accurate statement is **one failing check reported on two lines**. Nothing else in that memo's conclusion changes — run15 is still pre-existing, still unrelated to mailboxes, and still unrelated to this finding.

Separately, I found that the language currently has **two mouths**: `parse_wrl_core` silently accepts run-input syntax in world source, while `wrl_draft.replace_world_source` rejects the same syntax with a typed `WRL_WORLD_SOURCE_HAS_SCENARIO`. That needs a ruling.

Rather than idle on four open questions, I also **shipped the one §5 slice that needs no ruling** — the `*` replication / `{...}` fan-out sugar tier, green at `SG1–SG12 PASS_REF_AND_NATIVE`. It moves no identity by construction. It did force three small surface-semantic choices, which are stated for confirmation in §6 as **Q5**.

---

## 2. Finding 1 — the round-trip law is stale, not broken (PROVEN)

### The three failing assertions

| Site | Assertion | Compares |
|---|---|---|
| `binding_run9` L1 | `parse_wrl_core(format(g)) == g` via `_snap` | `(profile, **periods**, nodes, edges, **batches**)` |
| `binding_run9` L8 | "run inputs (claims) survive format → parse" | `epoch_inputs`, `run_plan` |
| `binding_run6:83` | `base.graph.batches == prog3.graph.batches` | claim batches |

All three compare **run inputs** across a format→parse cycle.

### Why that is now false by construction

`wrl_format.format_wrl_core`'s own docstring records the repeal:

> **v0.4-0 (GPT-5.6):** canonical WORLD formatting omits RUN INPUTS — the `periods N` run-duration line and inline `[epoch:N]` claim batches are NOT emitted, because those now belong to ScenarioV1, not the world source. […] Run inputs never entered the SemanticArtifactID (D3), so omitting them is identity-preserving.

The formatter is doing exactly what it was ruled to do. The batteries were never restated.

### Measured, over `binding_run9`'s six worlds

```
world        periods b->a     claims b->a      world=   semid=
core         3->0             3->0             True     True
twodoor      1->0             0->0             True     True
multi        1->0             0->0             True     True
clocks       1->0             0->0             True     True
fixedconf    1->0             0->0             True     True
small        1->0             0->0             True     True
```

The **only** thing that moves is the run inputs. `(profile, nodes, edges)` is identical for all six; `SemanticArtifactID` and `serialize_artifact` bytes are identical for all six.

This is corroborated *inside the failing batteries themselves*: `binding_run6` asserts `_sid(prog3) == sid0` on the line immediately **before** the one that fails, and it passes. `binding_run9` L2/L3/L4/L5/L6/L7/L9/L10 all pass, including L3 ("a formatting-only edit keeps the `SemanticArtifactID`") and L10 (the formatted text folds `ic_ref == ic32 == golden`). A genuinely broken formatter could not pass L10.

### Proposed restatement — all three verified passing

I did **not** apply these. `forge/wrl_roundtrip_probe.py` executes them:

| New law | Statement | Result |
|---|---|---|
| **L1′** WORLD round-trip | `parse(format(g))` preserves `(profile, nodes, edges)` — run inputs excluded | PASS |
| **L1″** IDENTITY round-trip | `parse(format(g))` preserves `serialize_artifact` bytes **and** `SemanticArtifactID` | PASS |
| **L8′** INVERSE run-input law | the formatter provably **excludes** run inputs: `periods == 0`, `batches` empty, `epoch_inputs` falsy | PASS |

**L8′ is the one worth your eye.** It is the failing L8 with its **polarity reversed**. Old L8 asserted run inputs *survive*; the v0.4-0 document boundary made that deliberately false. The useful law is that run inputs are *provably dropped* while the identity does not move — that is the document boundary itself under test. Deleting L8 would lose a real law; flipping it converts a stale assertion into a guard on the boundary you ruled.

`binding_run6:83` takes the same treatment: replace the `batches` equality with the world/identity pair it already asserts on the preceding line.

**I regard this as a spec-level act, not a test fix**, which is why I am asking rather than doing: L1 is a named formatting-invariance law and I should not silently renegotiate what it says.

---

## 3. Finding 2 — the language has two mouths (needs a ruling)

Two code paths disagree about whether run-input syntax is legal in world source:

| Path | Behaviour on `periods 3` + `[epoch:1] @1,1 SetRotor sp 16.0.10.0` in world source |
|---|---|
| `wrl_ir.parse_wrl_core` | **accepts silently** (documented as "legacy compatibility") |
| `wrl_draft.replace_world_source` | **rejects**, typed `WRL_WORLD_SOURCE_HAS_SCENARIO`, draft untouched (`binding_run21`) |

So the authoring surface enforces the v0.4-0 document boundary and the parser does not. The language can *read* syntax it can never *write*, and whether that syntax is an error depends on which door you came through.

This is load-bearing for the language track, because it decides what "a WRL world source" **is**. It is also load-bearing for Slice B: if `~~` emission adds surface that the parser accepts but the authoring path rejects, the split widens.

Three options, no recommendation asserted:

- **(a) Status quo.** Parser stays permissive; the authoring path is the only enforcement point. Cheapest; leaves the inconsistency documented rather than resolved.
- **(b) Parser rejects too.** `parse_wrl_core` raises `WRL_WORLD_SOURCE_HAS_SCENARIO` on run-input lines. One normative answer. **Cost: every battery whose world source carries `periods` + `[epoch:N]` must be split into world + scenario — that is most of them, including all six `binding_run9` worlds.** Large, mechanical, and it would move no identity, but it is not a small change.
- **(c) Parameterize.** `parse_wrl_core(text, allow_run_inputs=False)` with the permissive mode explicitly named as the legacy/battery path. Keeps the batteries working while making the strict reading the default and the permissive one a deliberate opt-in.

My instinct is (c), because it makes the boundary explicit at every call site without a tree-wide rewrite — but this is exactly the kind of "two answers in one codebase" question I should not settle unilaterally.

---

## 4. Proposed errata — WRL Core 0.1.2

`WRL_CORE_0.1.md` §14 is now factually stale in one row, as a direct consequence of Slice A Commit 7/8:

> Async route / mailbox (`~~`) | reserved in WRL, absent from the floor — **no mailbox node exists**

A `Mailbox` node **does** exist: it is the sixth entry of the closed `ROLE_IDS`, carries `{w, cap}` with `1 <= w <= 32` and `cap >= 1`, declares empty ports (D8 structurally), earns a real `SemanticArtifactID`, and selects `RuntimeStateV1_1` / `film.v0.7.mailbox.v1` / `admit_mailbox_deliver_all_v1` through `semantic_surface_for_roles`.

Proposed replacement row, stated to your grounded/partial discipline:

| Family | Status |
|---|---|
| Async route / mailbox (`~~`) | **partial** — `MailboxDecl` is a sanctioned canonical IR role with its own runtime state, admit policy and film schema; the `~~` *route construct* has no surface syntax (Slice B) and no structural edge (D8). Not promoted to Grounded. |

Nothing else in §14 needs to move: `==`, `!!`, `/gate`, `///seal` and general actor behaviors are all still exactly as described. This errata **records what already shipped** and claims no new grounding — `~~` stays *Reserved/partial* and promotion remains yours.

---

## 5. Proposed Core 0.2 promotion order

Core 0.1.1 freezes ten construct kinds and four route textures. The implemented language grounds **one texture** (`--` solid) and one fixed five-role object registry. The gap is not a failure — the identity spine was the right thing to build first — but the language track now needs an order.

Inventory of frozen-but-ungrounded surface: routes `~~` `==` `!!`; walls `/gate` `//commit` `///seal`; symbols `#` `?` `*`; memory kinds `{facts}` `[archive]` `:: frag //`; kinds Function/Fragment/Stencil/Derive.

Proposed slices, each in the established discipline (additive, no new runtime construct without a ruling, sugar washes out, identity-invariance gate per slice):

| Slice | Scope | Why here |
|---|---|---|
| **L-0** | this memo — round-trip restatement + 0.1.2 errata | clears the red batteries Slice B would inherit; no identity moves |
| **L-1** | **`==` verified route** | the cheapest real grounding: the entire ADMIT machinery (claims, `CandidateKey`, receipts, pinned policies) is already grounded and merely addressed out-of-band |
| **L-2** | **`~~` Slice B emission** | in flight in the networking track; independent of L-1 |
| **L-3** | **`!!` fault route** | overflow latch + `ResetFault` already grounded; the route construct is not |
| **L-4** | **`#` references + `&` composition** | the missing scale story; `#` is frozen, parser-preserved, and consumed by nothing |
| **L-5** | **walls by exposure** — `//commit` = canonicalize, `///seal` = `SemanticArtifactID` | grounding by exposing what the library already does |
| **sugar** | `*` replication (`[spinner:sp*4]`), fan-out `--sig--> {[a],[b]}` | no ruling needed under the existing prepass discipline; cannot move identity — **SHIPPED, see §6** |

Deliberately **not** proposed: expression notation (§10–17), traits/generics, metaprogramming, the supervision ladder. None are grounded and all would be design ahead of runtime.

### The L-1 design question worth stating now

The claim surface today is out-of-band: `[epoch:3] @1,0 SetRotor sp 181.0.0.181`, with `@w,s` writer stamps that name no world object. The natural reading of `==` is that **a claim instance is a run input, but the *permission* to claim is world structure**:

```
[worker:w1] ==admit(policy=admit_candidate_min_firstreceipt_v1)==> [spinner:sp]
```

— a *static* declaration ("this writer may mint claims against `sp` under this policy") that enters the `SemanticArtifactID`, while `[epoch:3] @1,0 …` stays a run input outside it. That preserves the v0.4-0 document boundary exactly, turns anonymous `@w,s` stamps into first-class objects, and grounds `==` with no new runtime construct — the policy it names is already pinned.

It also generalizes: `~~` Send would want the same permission/instance split, which is the one argument for taking L-1 before or alongside L-2.

I am **not** proposing this as ruled. It is the shape I would write a spec against if you point the track at L-1.

---

## 6. SHIPPED — the sugar tier (`*` replication, `{...}` fan-out)

This is the one row of §5 I marked "no ruling needed", so I built it rather than idle while the other four questions are outstanding. It activates two symbols that Core 0.1.1 already freezes and that nothing consumed.

```wrl
[relay:r*3]{sig_in, sig_out}                              ; 3 relays
[spinner:sp*3](w=8, n=4, rotor=identity){sig_in, socket}  ; 3 spinners
[r*3]  --sig-->    [sp*3]                                 ; 3 edges, pairwise
[p0]   --sig-->    {[d0], [d1], [d2]}                     ; 3 edges, fan-out
```

**Why it is safe by construction.** Both forms are a *source-to-source prepass* in `wrl_sugar.desugar_core`, run strictly before `parse_wrl_core`, exactly like the 3B-4 named rotors and concise clocks. The expansion is erased before a graph exists, so it is structurally incapable of minting an identity. The frozen demo world re-spelled with sugar still seals to `sem-8ae91fe9…fe4a` (`SG8`), and a sugared world and a hand-written explicit twin — written in a *different declaration order*, so the row proves canonical equivalence and not textual similarity — produce identical canonical bytes (`SG2`).

`binding_run44` — **SG1–SG12 `PASS_REF_AND_NATIVE` (15s)**. Regressions green: `binding_run11` (3B-4 sugar) N1–N9, `binding_run23` (v0.5-0 source surface) M1–M5. `binding_run9`'s failure set is **unchanged** — still exactly L1 and L8, the two stale-law rows of §2.

Two rows are worth naming. **`SG9`** holds the v0.4-2 rule *"the seal judges legality"*: an illegal fan-out that lands two `sig` sources on one node expands **successfully** — the prepass enforces only its own precondition — and is then rejected by the **seal**, as `WRL_CONTROLLER_CONFLICT`. Sugar does not acquire a veto. **`SG12`** proves the sugar-spelled world is genuinely *runnable*, folding `ic_ref == ic32 ==` the independent Fixture oracle; that is the row that would catch a desugar producing a well-formed-but-wrong graph, which `SG2` alone could not.

### Three sub-decisions I made autonomously — please confirm or overrule

None can move an identity (they are all prepass-internal), but each is a **surface-language semantic** that becomes expensive to change once authors write against it.

- **D-a — group members are ZERO-BASED.** `sp*3` → `sp0, sp1, sp2`. Rationale: matches the existing hand-written demo worlds (`p0`, `r0`, `d0`, `sp0`). The alternative, one-based, reads better in prose but would contradict every world already in the tree.
- **D-b — `*` on both endpoints pairs POSITIONALLY, not cartesian.** `[r*3] --sig--> [sp*3]` is **3** edges (i-th to i-th), not 9. Unequal counts are a typed rejection rather than a truncation or a broadcast. Rationale: the cartesian reading is almost always an error in this world model — `sig` fan-in is illegal anyway, so a 3×3 expansion would produce a graph the seal rejects six times over. Positional pairing is the only reading that is usually what was meant. `*` on **one** endpoint still broadcasts to the whole group (`SG5`), which is the unambiguous case.
- **D-c — an inline `;` comment on an expanded line attaches to the FIRST emitted line only.** The alternative — duplicating the comment onto all N — is noisier and would make the byte-exact no-op law harder to state. Line 0 keeps its original byte layout (and its comment) exactly; lines 1..N-1 are newly minted and carry no inherited alignment padding.

Happy to flip any of the three; **D-b** is the one with real semantic weight.

---

## 7. The five questions

- **Q1 — Ratify the round-trip restatement?** L1′ (world), L1″ (identity), L8′ (inverse run-input law) as stated in §2, with `binding_run6:83` taking the same treatment. All three verified passing, none applied.
- **Q2 — Which mouth is normative?** §3 (a) status quo / (b) parser rejects / (c) parameterized, default strict.
- **Q3 — Ratify the Core 0.1.2 errata?** §4 — records shipped fact only; `~~` stays Reserved/partial.
- **Q4 — Confirm or steer the Core 0.2 order?** §5, and specifically whether L-1 `==` is the next language slice and whether the permission/instance split is the right frame for it.
- **Q5 — Confirm the three sugar sub-decisions?** §6 D-a (zero-based), D-b (positional pairing), D-c (comment attachment). Shipped green; cheap to flip now, expensive later.

The Commit 8 open reversal (`CompilePlanV1` carrying `MailboxDecl`s) is the networking track's question and is not restated here.

---

## 8. How to reproduce

```bash
cd TRVM/forge
export PYTHONPATH=../runtime/python:../research

# the finding, measured -- ALL PASS
python3 wrl_roundtrip_probe.py

# the shipped sugar tier -- SG1-SG12 PASS_REF_AND_NATIVE (~15s)
python3 binding_run44.py
TRVM_SKIP_NATIVE=1 python3 binding_run44.py  # ref-only

# sugar regressions -- both green
TRVM_SKIP_NATIVE=1 python3 binding_run11.py  # 3B-4  N1-N9
TRVM_SKIP_NATIVE=1 python3 binding_run23.py  # v0.5-0 M1-M5 (~61s)

# the three stale assertions, still red (unchanged by this memo)
TRVM_SKIP_NATIVE=1 python3 binding_run9.py   # L1, L8 FAIL; L2-L7, L9, L10 PASS
TRVM_SKIP_NATIVE=1 python3 binding_run6.py   # V1 OK, then AssertionError at :83
TRVM_SKIP_NATIVE=1 python3 binding_run15.py  # S9 only -- unrelated root cause (~154s)
```

## 9. Files

| File | Change |
|---|---|
| `forge/wrl_roundtrip_probe.py` | **new** — measures the finding and executes the three proposed restatements. Not a battery; edits nothing. |
| `forge/wrl_sugar.py` | **modified** — adds the `*` replication and `{...}` fan-out prepass ahead of the existing value sugar. `desugar_core` becomes 1→many. |
| `forge/binding_run44.py` | **new** — SG1–SG12, the sugar-tier battery. |
| `WRL_LANGUAGE_TRACK_MEMO.md` | **new** — this memo. |

One shipped module was modified (`wrl_sugar.py`), additively and above the parser. **No identity moved** — `SG8` proves it against the frozen demo id, and `binding_run11`/`binding_run23` prove the pre-existing value sugar is byte-unchanged. `~~` was not promoted. No new runtime construct.
