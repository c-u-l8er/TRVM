# Slice B, Commit 4 — the runtime fold: closure memo **and one blocking question**

**Status:** the commit is CLOSED at the golden layer and **cannot close natively
without a ruling.** `binding_run49` PASS_REF_AND_NATIVE (28s, 67 rows).
`mutate49` **22/22 ALL CAUGHT**. Full sweep `run_l0_sweep` **18/18 green**
(184s, reference + native), L-0 tier unmoved.

Commits 2 and 3 gave a route a canonical form, an identity, a locator and a
ruled spelling, and both closure memos ended with the same admission: a route is
carried, sealed, formatted, refused for every reason it should be — **and
provably ignored at runtime.** That stops being true here. A `~~` written in
text now fires:

```
ep1  ledger:MailboxEnqueue,mailbox=mb,epoch=1  next_inbox=(w15.s0.4e.2.0.0.0.0.7->mb[0.0.0.7])
ep2  ledger:MailboxDeliver,mailbox=mb,epoch=2  inbox=(w15.s0.4e...)
ep3  inbox=(),next_inbox=()
receipt:w=15,s=0,accepted=4e,apkey=2.0.0.0.0.7,epoch=1,outcome=Applied
```

**§2 is the only part that blocks.** Everything else is a decision to confirm or
overrule at leisure.

---

## 0. Running the packet

Every number in this memo is reproducible from the zip alone, with nothing but a
Python 3 and (optionally) a C compiler:

```
unzip WRL_SLICE_B_COMMIT4_PACKET.zip && cd forge
python3 run_l0_sweep.py                   # 18/18 green -- RUN THIS FIRST
python3 binding_run49.py                  # the commit under review, 67 rows
TRVM_SKIP_NATIVE=1 python3 mutate49.py    # 22/22 ALL CAUGHT
```

**`run_l0_sweep.py` first is not a style preference.** It is the only entry
point that builds `ic32` from the shipped `runtime/c/ic32.c`; the individual
batteries resolve a **prebuilt** binary and predate the override. Run
`binding_run49.py` standalone on a fresh extraction and it dies on R13 with a
raw `FileNotFoundError` — measured, not guessed. Either run the sweep first, or
use `TRVM_SKIP_NATIVE=1 python3 binding_run49.py` (`PASS_REF_ONLY`, 26s), which
exercises every law in the battery; native adds an independent second reducer,
not new laws.

Verified from a clean extraction into an empty directory before shipping:
`ALL PASS -- 18/18 green (184s)` with `built ic32 into runtime/c/ic32 with gcc`,
`MUTATION VERDICT: ALL CAUGHT`, and `binding_run49` at both
`PASS_REF_AND_NATIVE` (28s, 67 rows, after the sweep) and `PASS_REF_ONLY`
(26s, standalone). Run standalone on a fresh extraction *without* the sweep it
fails exactly as described above — `R13 raised FileNotFoundError … runtime/c/ic32`
— which is also measured, not asserted.

The file list is **computed**, not hand-written — `forge/tools/build_packet.py`
walks the closure and `--verify` extracts the finished zip into an empty temp
directory and runs the sweep there. Three separate walks are needed, and the
packet is only correct because the third was forced by a failure rather than
foreseen:

| Walk | Finds | Why an import walk alone is not enough |
|---|---|---|
| imports (`ast`) | `wrl_fold`, `admit`, … | — |
| subprocess targets | `binding_run5…50` | the sweep registers batteries as bare **strings** and shells out; an import walk ships the sweep without the batteries it sweeps |
| data assets | `ic_v1_term_fingerprints.txt` | `binding_run50` opens it by name beside itself — neither an import nor a subprocess target |

The first build of this packet passed its own closure check and then failed
`--verify` at **17/18**, `binding_run50` dying on `FileNotFoundError`. It passes
in-tree for the uninteresting reason that the file is simply there. That is the
whole argument for extraction-verifying a packet instead of reasoning about its
manifest: the previous round shipped the batteries and omitted
`runtime/python/ic_ref.py`, so every battery died at import, and the round
before *described* a packet that was never built at all. A packet whose contents
cannot be run is a claim, not evidence.

---

## 1. What shipped

| file | change |
|---|---|
| `wrl_fold.py` | **NEW.** `route_claims`, `route_claims_by_epoch`, `fold_batches`, `fold_script`, `epoch_batch_census`, `check_epoch_batch_capacity`; plus the **declared-policy seam** (§3d) — `admit_policy_of`, `film_schema_of`, `film_mailboxes`, `runtime_seams` |
| `wrl_canonical.py` | `WRL_ROUTE_BATCH_OVERFLOW` (seal-time co-firing bound), `WRL_EPOCH_BATCH_OVERFLOW` (fold-time pairing bound) |
| `wrl_scenario.py` | `check_epoch_batch_capacity` composed into `check_world_compatibility` |
| `wrl_ir.py` | the commit-2/3 route refusal in `ir_to_fixture` **lifted** (§3b) |
| `binding_run3o.py` | eight helpers given a defaulted `fx=None` (§3f) — additive, frozen rows byte-identical |
| `binding_run47.py` | P8d/P8e **reversed** to measure the lift; `_fold` latent defect closed (§3f) |
| `binding_run49.py` | **NEW**, R1–R13 |
| `mutate49.py` | **NEW**, 22 mutations |
| `run_l0_sweep.py` | `binding_run49` registered in the LIVE tier |

The whole runtime image of a route is **one ADMIT claim envelope**:

```python
mk_claim(ROUTE_WRITER_ID, canonical_route_ordinal, ("Send", mailbox_id, body))
```

No new runtime construct, no new identity rung, no widened reducer. `Send` is
D9's tag 2, which Slice A froze; commit 4 is merely the first thing that
constructs one from a language surface.

---

## 2. **THE BLOCKING QUESTION** — the reduced proof profile has no `Send`

R12 is not in the ruling and is not a request for a feature. It is a
measurement, and it is the reason this battery says *golden layer only*.

```
WKIND=1  WIDX=3  WLANE=8  WD=8  WK=4     CKEY_W=44   FKEY_W=52   EKEY_W=8
('Send','mb',(0,0,0,7))  payload_key -> (2,0,0,0,0,7)
                         pack_ckey   -> AssertionError: field 2 overflows width 1
admit_ic.py  occurrences of "mailbox" or "Send" : 0
runtime/c/ic32.c            occurrences of "mailbox" : 0
```

`WKIND` is **one bit**, sized for `SetRotor=0 | ResetFault=1`. `Send` is 2. A
route's claim cannot be packed into the reduced profile at all, so it cannot
reach `ic32`.

Three things make this precise rather than an excuse:

* **The boundary is exactly half.** R12d/R12e measure it: the route-bearing
  world's **world half** crosses intact — same fixture, same initial-state keys
  as the route-free twin, `ic_ref == golden`. A mailbox costs the world state
  nothing; it lives in **claim** state. Only the claim half is missing.
* **The gap is Slice A's, not Slice B's.** Slice A shipped `Send` into the
  golden reducer, into `CompilePlanV1` and into Film v0.7 without ever lowering
  it to IC. Commit 4 is the first caller to try to fold one.
* **R13/R13b keep the native closure honest** for every world that has no
  route — the frozen demo still folds `ic_ref == ic32 == golden`.

### The gap is exactly ONE BIT — measured, not estimated

`WKIND` must hold 3 values (`SetRotor=0 | ResetFault=1 | Send=2`), so it needs
**2** bits, not 1. Everything else in `CKEY_W` is already at its minimum:

```
minimum CKEY_W for a full-budget route world:
   WD 8  +  WKIND 2  +  WIDX 3  +  4*WLANE 32   =  45
   today's CKEY_W                               =  44     short by ONE bit
   implied FKEY_W = 2*WK + CKEY_W               =  53     (today 52)
```

So the whole ruling reduces to: **where does one bit come from?** There are only
four places, and each is now measured rather than guessed.

| source | keeps `CKEY_W=44`? | measured cost |
|---|---|---|
| `WD` 8→7 (payload digest) | yes | `WD` is `admit.WD` — owned by the **frozen L-0 reducer**, not Slice B's to move. Also raises digest-collision probability in the proof profile. |
| `WK` 4→3 (writer/sequence) | yes | Also `admit`'s, and the ruling names `WK` explicitly. |
| `WLANE` 8→7 (×4 lanes) | frees 4 bits | Caps mailbox `width` at 7, so a `width=8` mailbox's body could no longer be packed. Moves a **language-visible** bound to buy a proof-profile bit. |
| `WIDX` 3→2 (target index) | yes | **This is what §2's option (b) proposed, and the measurement below kills it.** |

### Why `WIDX` 3→2 does not work — the route budget already forbids it

The target index is **per-kind scoped** (`SetRotor`→spinners, `ResetFault`→orbs,
`Send`→mailboxes), and an out-of-fixture target packs to the sentinel
`len(targets)`. So `WIDX` bounds *each* kind at `2^WIDX - 1` targets.

A world with the **full ruled budget of 6 routes pointing at 6 distinct
mailboxes seals cleanly** under every commit-4 law — I built one:

```
SEALS OK: 6 routes -> 6 distinct mailboxes ['mb0'..'mb5']
highest real mailbox_index = 5 ; sentinel (INVALID_TARGET) = 6
  WIDX=3 (indices 0..7): fits
  WIDX=2 (indices 0..3): *** OVERFLOWS ***
```

| mailboxes | sentinel | `WIDX=3` | `WIDX=2` |
|---|---|---|---|
| 1–3 | 1–3 | ok | ok |
| **4–7** | **4–7** | ok | **OVERFLOW** |

`WIDX=2` caps a world at **3** mailboxes (and 3 spinners, 3 orbs). Your own
`MAX_ASYNC_ROUTES = 6` can demand **7** index values. Option (b) would therefore
require *also* capping mailboxes at 3 — a **new language law narrowing what
commit 1 shipped**, not a free re-slicing of spare bits.

### What the tree actually uses

Instrumented `payload_key` across the **full 17-battery sweep** (via an import
hook, so it reached the sweep's subprocesses too — an in-process patch would
have measured only the parent and reported a comfortable zero):

```
kind 0  SetRotor -> spinner_index    max index = 1
kind 1  ResetFault -> orb_index      max index = 0
kind 2  Send -> mailbox_index        max index = 0
```

Nothing shipped today needs more than index 1. That is an argument for `WIDX=2`
being *survivable in practice* and **not** an argument that it is correct: the
bound is what the language permits, not what the batteries happen to exercise,
and the 6-mailbox world above is expressible today.

### The three options, re-costed

| | option | cost |
|---|---|---|
| **(a)** | **Golden-layer-only closure.** `~~` is Grounded in the language; the native reducer is a second opinion for route-free worlds only, stated as a documented boundary. | Zero code. Slice B ships a permanently smaller proof surface than L-0, and "two independent reducers agree" stops being universally true. |
| **(b)** | **Steal a bit from `WIDX`.** | **Now measured as a conflict with your own route budget** — needs mailboxes capped at 3. Not free; it spends a language bound. |
| **(c)** | **`FKEY_W` 52→53.** It is a *lowering-representation* width strictly below the film: widening it moves no `sem-`, no `bknd-`, no film byte — only the reduced proof term. | Needs your ruling on what the prohibition was protecting. If it protected the **semantic budget**, (c) is clean. If it protected the **ic32 term size**, (c) is out. |

**My reading, offered as a recommendation and not a decision:** (c) is now the
cheapest honest option, because (b) turned out to spend a *language-visible*
bound to protect a *representation* width — the more valuable of the two. But
(c) rests entirely on what the `FKEY_W` prohibition was defending, which is
yours to say, not mine to infer.

---

## 3. Autonomous decisions — please confirm or overrule

### (a) Two new laws, both refusals, both keyed by **epoch**

`MAX_BATCH` is 4: one epoch's observation batch holds four claims. Six routes
are legal (`MAX_ASYNC_ROUTES` = `MAX_FACTS` = 6) — but six routes **that all
fire in the same epoch** are not, because they would be handed to `admit_step`
as one batch of six and trip its assertion. Nothing checked this.

* **`WRL_ROUTE_BATCH_OVERFLOW`** — seal-time. Five routes co-firing on one
  `once(1)` Pulser is refused when the world is sealed.
* **`WRL_EPOCH_BATCH_OVERFLOW`** — fold-time. A world with 4 routes at epoch 1
  and a scenario that authors 1 claim at epoch 1 are **each** legal and their
  **pairing** is not.

They are deliberately **distinct codes from `WRL_ROUTE_BUDGET`** and from each
other, because the repairs are opposite: "declare fewer routes", "declare them
on different epochs", "edit the other file". One code cannot ask for three
things. R9g and mutation **M15** hold that split; R10c holds that the pairing
message names *which half* is large, so the author knows which file to open.

The pairing check is composed into the one `check_world_compatibility` door
(the commit-3 argument, unchanged), **and** `fold_batches` re-checks on its own
(R10g) — because a caller that never opens the door still must not be able to
hand `admit_step` a batch it will assert on. Mutation **M20** is what proved
the second check was reachable by nothing.

### (b) The `ir_to_fixture` route refusal is **lifted**

Commits 2/3 refused a route-bearing artifact there, because a Fixture built
from one silently dropped the routes and became an oracle for a *different*
world. Commit 4 makes the dropping **correct** rather than silent: a route's
runtime image is a claim, not structure — no port, no state, no edge, nothing
the Fixture models. The Fixture of a route-bearing world **is** the Fixture of
its route-free twin.

That is a claim about structure, so it is measured as one. `binding_run47`
P8d pushes five route-bearing variants' Fixtures through
`fixture_to_compile_plan_v1` at a **fixed** semantic id — stripping the one
field that could carry the difference for free — and all five collapse to **one
plan digest**, while P8e shows the same five worlds keep five **distinct**
`sem-` ids. A collapse measured, not a comparison of one world with itself.

### (c) The commit-3 carried obligation is **DECLINED**, with reasons

Commit 3's memo promised to unify `wrl_canonical.route_body_in_range` into
`admit` and remove the fork. **Working it through showed the unification is not
free, and I did not do it.** The full argument is written into the function's
docstring so it is not re-discovered; in short:

* `admit` importing the spine would make the **frozen L-0 reducer** depend on
  the module Slice B edits every commit — a language-track mistake would take
  the ratified tier red, the precise failure the sweep's frozen/live split
  exists to prevent;
* the spine importing `admit` is the inversion the spine's header refuses, and
  refuses load-bearingly: the spine has a **verified browser port**, and a spine
  that reaches for the reducer cannot be ported;
* a third shared module ends the fork but adds a file to **both** dependency
  graphs, including the ported one.

So the fork stays, under the discipline every other derived constant is under:
**an unavoidable second spelling is acceptable only when something fails the
moment the two disagree.** That is `binding_run47` P0c, which folds the same
bodies through both spellings across the whole boundary neighbourhood.

This is a judgement about which coupling is worse, not a fact, and it is
reversible either way. Overrule freely.

### (d) NEW — the declared-policy seam (a defect this commit found)

Not in the ruling. Found while rendering commit 4's first film, and it is the
same defect as the route itself one layer down. A sealed world **carries**:

```python
semantic_policies = {..., "admit_policy_id": "admit_mailbox_deliver_all_v1",
                          "film_schema_id":  "film.v0.7.mailbox.v1"}
```

and **nothing in the tree read them.** `admit_step`'s `policy_id` defaults to
the mailbox-*free* `admit_candidate_min_firstreceipt_v1`; `film_bytes_v7`'s
`mailboxes` argument defaults to `None`. Every fold harness in the tree was
running a mailbox-bearing world under a reducer that does not know what a
mailbox is, and rendering it with a projection that cannot show one.

Measured on the first route-bearing world:

```
under the DEFAULT policy    claim ... payload=Send:#?:0.0.0.7
                            (no admit_mailbox line, no mailbox line, no ledger)
under the DECLARED policy   claim ... payload=Send:mb:0.0.0.7
                            ledger:MailboxEnqueue,mailbox=mb,epoch=1
                            ledger:MailboxDeliver,mailbox=mb,epoch=2
```

The default reading loses the route's **entire effect** and, worse, renders the
target as `#?` — Film v0.7's `INVALID_TARGET`. A film asserting the route
addressed a mailbox that does not exist.

`runtime_seams(artifact, fx)` returns `(admit_policy_id, film_mailboxes)`
**together**, specifically so a caller cannot honour one and forget the other —
mutations **M11** (mailboxes forgotten) and **M12** (policy forgotten) are the
two halves, and both are caught. R7g/R7h are the sharpest rows: two routes to
**one** mailbox, because the two policies differ only in how they accumulate
several claims on one key — under the declared policy both messages are
delivered, under the old default **one is silently dropped**.

`film_mailboxes` returning `[]` for a mailbox-free world is deliberate and
load-bearing: Film v0.7 gates its whole mailbox block on `if mailboxes:`, so
every pre-Slice-B world folds **byte-identically** under the declared seams and
under the old defaults (R11b).

### (e) ScenarioV1 **cannot express** a `Send`

`wrl_scenario._OPERATIONS` is `("SetRotor", "ResetFault")`. So the Q4 writer-15
reservation is guarding a door that is **already shut for a second, independent
reason**. Recorded rather than acted on: the twin proof (R5) therefore builds
its hand-written claim with `mk_claim` rather than as a ScenarioV1 claim. If
you want authored `Send` claims in scenarios, that is a ruling, not an
oversight to fix quietly.

### (f) `binding_run3o` parameterised rather than forked — **and it was hiding a defect**

`binding_run47._fold` always took an `fx` argument, but `binding_run3o`'s golden
half closed over that battery's module global `FX = mkfx(8, 4)` and the argument
reached only the IC half. **The row passed because the demo world *is*
structurally `mkfx(8, 4)`** — the two halves were comparing the same world by
accident, not by construction, and would have started comparing two *different*
worlds, silently and greenly, the first time commit 4 folded a mailbox-bearing
one.

Fixed with a defaulted `fx=None` on eight helpers, **not** a second copy of the
driver in the new battery. Every existing call site is byte-identical and the
frozen rows re-run unchanged (5/5 PASS, 42s).

`binding_run3o` is deliberately **not** added to `run_l0_sweep` — it is an
ADMIT battery, not a WRL one, and widening what that sweep covers would change
what its number means. It was re-run by hand; the reasoning is a comment in the
sweep.

---

## 4. What the mutation round found

`mutate49` runs 22 mutations including a null control and two `@noop` rewrites
that **must survive** (a harness that "catches" a no-op proves nothing).

**M7 — the claim numbered by STORAGE order instead of canonical order.
SURVIVED the first spelling, with nothing red.** The most useful finding, and
it is the same finding as M8 one layer up. R1c is the row that compares
`sequence` against the canonical accessor rather than a literal, so it is the
row one would expect to catch this — and it **cannot**, because
canonicalization sorts `async_routes` into RouteKey order **before sealing**.
On any artifact `lower()` produces, `enumerate(routes)` and the canonical
ordinal are the same function; authoring order cannot separate them because the
seal has already erased it. **R1e exists because of this line**: it hands the
fold a deliberately un-canonically-ordered route list — the one input on which
"numbered by key" and "numbered by position" disagree — and R1f then shows the
fold's *output* does not inherit that disorder. M7's expected-catch list names
only R1e; listing R1c as well would have been the comfortable lie, leaving the
mutant reported as survived while blaming a row that physically cannot catch it.

**M8 — the canonical sort dropped. SURVIVED the first spelling.** Same root:
for every single-epoch world the sort is a no-op. It is load-bearing only where
canonical order and **epoch** order disagree — a world whose first-sorting route
fires last. **R3b is that world.**

**M10 — `fold_script` grows its own injection.** Caught only after R4 was
rewritten to use three co-firing routes: with **one** route a truncating second
injection agreed by coincidence.

**M12 — the policy half forgotten.** Caught only after R7g/R7h were added, for
the reason in §3d: the two policies are indistinguishable on a world with one
message.

**M20 — `_assert_capacity` deleted from the merge.** Reached by no row until
R10g/R10h were added. A law nothing exercises is a comment.

Four rows in this battery (R1e, R1f, R3b, R7g/R7h, R10g/R10h) exist **only**
because a mutation walked through the first spelling. That is the round working.

---

## 5. Not frozen

Commit 4 is the last commit in the ruled Slice B line, so the ruling's own next
step is: **freeze the Slice B line, then promote `~~` to Grounded in
`WRL_CORE_0.1.md` §14.**

I have not done either, because **§2 blocks it.** Promoting `~~` to Grounded
while the native reducer cannot fold one would publish a tier claim the tree
cannot honour. The three options in §2 are the fork in the road; (a) also
requires deciding what "Grounded" means when one of the two reducers is out of
scope for the construct.

Everything else is ready. Say the word and the freeze is mechanical.
