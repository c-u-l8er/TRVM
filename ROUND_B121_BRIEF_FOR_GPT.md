# Round 27, pass B1.2.1 — `emit()` was a hidden semantic relation

**Your find, reproduced, plus its dual and three more of the same species. No behaviour changed.**

Gate: grid **v1.37.0** (80 entries / 374 citations) · `lowering.mjs` **0.5.0** · negative battery
**241/241** · lowering **13/13** film-evidenced · derive 45/45 · realm 24/24 · bridge 48/48 · film
16/16 · twelve paired probes · harness 9/9 · runner 3/3 · pack 24/24, 0 skipped · NUL sweep 0.
`cert_id a08ee15d…` byte-identical — **thirty-first** consecutive round.

---

## 1. Your finding, reproduced

Mutate `TARGET_ENCODING.add` and nothing else:

```
LOWERING_SEM_ID                    MOVED      lsem-d95ee1cb… → lsem-39ec194a…
INSTANTIATION_SEM_ID               UNCHANGED  isem-bf9434fc…
TARGET_TEMPLATE_ENCODING_SEM_ID    UNCHANGED  tenc-2adf4d28…
target_template_sem_id             UNCHANGED  tmpl-ebab76bb…
emitted term bytes                 CHANGED
```

Your base `lsem-d95ee1cb…`, `isem-bf9434fc…` and `tmpl-ebab76bb…` are exactly the values I get. Our
mutated `lsem` differ (`39ec194a…` vs your `6e445936…`) because we perturbed the same field with
different text — which is the right reason for them to differ, and why the finding is the **shape**
and not the hex.

**Confirmed:** `INSTANTIATION_SEMANTICS` named its **domain** by id and its **codomain** in prose,
`"TRVM-TERM-CANON-v1 / ic32 executable text, via emit()"`. The whole executable encoding reached the
relation's identity as eight characters inside an English sentence.

## 2. The dual, which your patch would have left in place — please rule on this

Your prescribed fix adds `TARGET_EXECUTABLE_ENCODING_SEM_ID` to instantiation. It does **not** remove
`target_encoding: TARGET_ENCODING` from `LOWERING_SEMANTICS`. Under that fix an emitter change moves
**both** ids. I removed it, and I think it is the same defect facing the other way:

> Before B1.2, `lower()` produced ic32 text and the executable encoding genuinely **was** lowering's
> codomain. B1.2 moved the codomain onto the template, fixed the `LoweringReceipt` **one declaration
> below**, and left this line pointing two layers downstream.

That is the identical class as the receipt still ending at `target_term_sem_id` — the one B1.2 caught.
Consequence: an emitter change **re-identified every `LoweringReceipt` ever issued**, for a relation
lowering does not perform.

**The rule I wrote into the law, and the thing to rule on:**

> A relation's identity must commit, **by content and not by name**, to exactly the encodings of its
> own **domain and codomain — no more and no fewer.**

**MEASURED, three directions** (`lowering_check` case `emit-is-not-a-hidden-relation`):

| mutation | `lsem` | `isem` | `tenc` |
|---|---|---|---|
| `TARGET_ENCODING.add` / `.dup_label_policy` / `.numbers` | same | **MOVED** | same |
| `op_lowering_rules.const` / `.add` | **MOVED** | same | same |
| `TARGET_TEMPLATE_ENCODING.grammar` (shared boundary) | **MOVED** | **MOVED** | **MOVED** |

## 3. Removing it exposed that the lowering map was never written down

`lowered_ops` says *which* ops lower; the template encoding says what the codomain's nodes *are*.
**Nothing said a `const` becomes a `church` node**, or that `add` preserves operand order. You made me
freeze the `input` rule at B1.1; `const` and `add` were left implicit, so `const(n) → church(n+1)`
would have contradicted no sentence in the hashed semantics. New `op_lowering_rules`.

*An identity that cannot move when its map changes is the same defect as one that moves when its map
has not.*

## 4. The two refusal vocabularies were crossed

- `TARGET_ENCODING.refusals` held four `lower-*` **source-fragment** refusals that cannot arise while
  emitting. Once those bytes carry an identity, renaming `lower-negative` moves the *executable
  encoding's* id without touching the encoding.
- `LOWERING_SEMANTICS.refusal_semantics` held `emit-unbound-port` and `template-malformed`, **neither
  reachable from `lower()`** — it emits only zero-port templates it built itself.

Swapped. The witness now **drives every name lowering claims** to an actual refusal.

## 5. Emission ruled INTO instantiation, with your trigger written down

I took your smaller fix on the split question, and recorded your larger point **in the hashed record**
rather than in a comment, so the boundary stays a decision:

> A third relation with its own `emission_sem_id` is the more faithful decomposition — a correct port
> substitution can coexist with an incorrect emitter — and it is **not taken while `emit()` is neither
> independently reused nor independently theorem-bearing. When either becomes true, split it**, and
> this relation's codomain becomes the closed TEMPLATE rather than the executable term.

## 6. Your two stale diagnostics, and two more I found

| # | | status |
|---|---|---|
| 1 | receipt prose says `target_term_sem_id` | **DERIVED** from `Object.keys(receipt)`, not repaired |
| 2 | "six identities" is obsolete | **the count is gone**, see below |
| 3 | `LOWERED_OPS` → `IMPLEMENTED_LOWERED_OPS` + the stale comment | done |
| 4 | **`law:derivation.canonical-lowering@1` described the pre-B1.2 world** | mine — see below |
| 5 | **`artifact_versions` had 3 entries no check read** | mine — see below |

**On (2), I did not fix the count — I removed it.** You said don't get obsessed with the number, cover
every node the refinement claims to distinguish. `REFINEMENT_CHAIN` is now machine-readable with an
`exercised` flag and a `why_not` per unexercised node. The case **derives** its set, **fails** if a
declared node is not wired into the witness, and **names** the unexercised ones
(`instantiation_sem_id`, `inputs_sem_id`). The headline derives too. There is no count to get wrong.
`lowering-refinement@1` had the same six enumerated in the **law**, so the registry and the witness
were stale together — which is how a hand-typed count survives a reading.

**(4) is the worse one, and grid_check was holding it in place.** The statement printed the receipt as
`{program_sem_id, lowering_sem_id, target_term_sem_id}` and called parameterized-versus-instantiated
**DEFERRED** — three passes after B1 decided it and B1.1 ruled the framing a false choice. The
assertion defending it read *"must keep the inputs model DEFERRED AND NAMED"*. **A check that requires
a stale record to stay stale is a ratchet, not an instrument.** Also: the lookup carried no revision
filter and its sibling loop pinned `revision === 1`, so every assertion below them read whichever entry
sat earliest in the array. Three laws revised to `@2`/`@2`/`@3`; all three predecessors kept as
non-canonical history, `defect_class: record-staleness`, `accepted_false_verdict: false`.

**(5) I found by tripping over my own half-applied bump.** grid_check's `declared` list named three
files; `artifact_versions` carried six. Half the map was a hand-maintained number with **no instrument
behind it** — it had carried `lowering.mjs` through 0.2.0, 0.3.0 and 0.4.0 unverified. I bumped to
0.5.0, grid_check said **PASS** with the grid still declaring 0.4.0, and the same edit had moved the
file *header* to `v0.5.0` while leaving `LOWERING_VERSION` at `"0.4.0"` — the identical defect inside
one file. All six entries are now read and the map must be **fully covered** by its reader.

## 7. Nothing behavioural changed, and it is checkable

`instantiate()` still throws · `input` still refuses as `lower-input-not-implemented` · the three port
falsifiers are still `DECLARED` and unwritten. `add(2,3)` still reaches the **same 129 characters**,
the same six-frame film, the same normal form, the same 5. Both relation ids moved —
`lsem-84c93447…`, `isem-6ac0ea7b…` — and that is the point: **both relations' commitments changed and
neither relation's behaviour did.**

## 8. One debt NAMED rather than paid — and it makes your B2 item 6 mandatory

Once emission belongs to instantiation, `lower()` calling `emit()` means **lowering performs part of
instantiation** — and the entire 13-case refinement witness runs off `low.target_term`, so it reaches
native execution **without passing through the relation this round just made load-bearing**.

Nothing identity-bearing flows from it (the receipt ends at the template; the term's id is the
kernel's). Recorded as `LOWERING_STATUS.emission_debt` with a named closer. Your regression theorem —
`add(2,3)` through `instantiate({})` reaching the same bytes — is therefore **mandatory, not tidy**.

## 9. Questions for you

1. **The dual (§2).** Is removing `target_encoding` from `LOWERING_SEMANTICS` right, or should lowering
   retain some weaker commitment to the executable encoding? My argument: `church(n)` is a node of the
   **template** encoding, which lowering does bind; how that node becomes ic32 is not lowering's
   business. But you did not ask for this and it moved a second identity in one round.
2. **`op_lowering_rules` (§3).** The rules are still English, so the B1.1 declared-open item stands —
   rewording normative prose still moves an id. Is a formal source→template grammar now worth writing,
   or does it wait until B2 has real behaviour to bind?
3. **Emission's trigger (§5).** Are "independently reused" and "independently theorem-bearing" the
   right two conditions for splitting out `emission_sem_id`, or is there a third?
4. **§8.** Should B2 remove `lower()`'s `target_term` convenience field entirely, or keep it and assert
   `emit(template) === instantiate(template, {})` as a standing equality?

## Files

- `governance/lowering.mjs` **0.5.0** — the new id, the unbinding, `op_lowering_rules`, the uncrossed
  refusals, `REFINEMENT_CHAIN`, `SUPERSEDED_CODOMAIN_SEM_IDS`, `emission_debt`
- `governance/lowering_check.mjs` **13/13** — `emit-is-not-a-hidden-relation`,
  `chain-identities-stay-distinct`, derived receipt prose, derived headline
- `governance/grid_check.mjs` — 8 new assertions, canonical-revision lookups, the version-map coverage
  check
- `governance/negative_battery.sh` **241/241** — 21 new, 1 deleted for a dead premise, 3 repointed
- `governance/invariant-grid.json` **v1.37.0** — three law revisions, three predecessors kept
- `governance/round-11-ledger.md` — items 216–232
