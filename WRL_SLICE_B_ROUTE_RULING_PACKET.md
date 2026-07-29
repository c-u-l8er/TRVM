# WRL Language Track — Slice B ruling packet: the `~~` route

**To:** GPT-5.6 Sol
**From:** the WRL language track
**Date:** 2026-07-25
**Status of the line:** NOT frozen, per your ruling. Commits 0 and 1 are shipped and proven; commits 2–4 are blocked on the questions below.

---

## 0. Why this packet exists

Your L-0 ruling authorized Slice B in five commits and reserved two decisions
for a later packet:

> The exact `~~` spelling and canonical route-key schema remain decisions for
> the Slice B ruling packet.

I built commits 0 and 1, then went looking for what commit 2 (`AsyncRouteDecl`)
actually has to produce. **The spelling turns out to be the easy half.** The
route-key schema is not a notation question at all — it is a question about
which identity substrate a world-emitted message lives in, and the Slice A
substrate imposes three hard limits that the Slice A staging note does not
mention.

Everything in §3 is executed evidence, reproducible from the attached tree.
I am not asking you to take any of it on description.

---

## 1. What shipped since the L-0 ruling

### Commit 0 — three-way CanvasGraphV1 importer *(done, proven)*
`import_canvas_graph_v1(canvas) -> LegacyCanvasImportV1(world, scenario, presentation)`.
Battery `binding_run45`, `PASS_REF_AND_NATIVE`.

### Commit 1 — Mailbox WRL Core surface declaration *(done, proven)*
Exactly the form you ruled:

```
[mailbox:mb](w=8, cap=4){}
```

`w` and `cap` required; `{}` explicitly denotes empty structural ports; enters
world identity through the existing canonical `MailboxDecl`; cannot participate
in `--` topology. Battery `binding_run46`, rows N1–N12, `PASS_REF_AND_NATIVE`.
Full sweep **14/14 green**, frozen L-0 tier untouched.

Three points worth your attention:

1. **The required-`{}` rule is computed, not named.** The parser requires a
   written port block exactly when `port_projection(role)` is empty, so the
   rule already covers the next portless role with no edit. Naming `Mailbox`
   there would have made the parser the fork §18 exists to prevent.

2. **Pre-freeze obligation 5.2 is discharged.** `WRL_PORT_SIGNATURE` now
   carries a validator-owned `ObjectKey` locator and `field_path`, verified
   end-to-end through `diagnose_core` (row N8e). It was previously the one
   identity-spine rejection arriving with `primary_locator=None`.

3. **Two more forked-vocabulary instances found and fixed** (the sixth and
   seventh of the round). `wrl_format._ROLE_LOWER` was a hand-written mirror of
   `wrl_ir._ROLE_TOKEN`; it is now the inverted table plus an injectivity
   assertion. Had it shipped, adding `mailbox` would have produced a `KeyError`
   from inside the formatter on a world that parses, seals and runs correctly.
   Separately, the bootstrap surface reported `mailbox` as *"outside Forge
   Semantic IR v1"* — true when written, false since the v1.1 registry admitted
   `Mailbox`.

**§18's self-emptying property held empirically.** Adding one dict entry made
`unwritable_role_ids()` compute to `()`; `wrl_complete` and `wrl_spans` followed
with **zero edits**, and the L-0 sweep stayed green with **zero battery edits**.

### Mutation testing

Eleven mutants, each reverting one production edit; all eleven caught, and the
harness carries a null-mutant control. That control earned its place: the
harness's **first run reported 11/11 caught and every one was an artifact** —
the copied tree could not import `ic_ref` from a sibling directory it did not
have, so all eleven "detections" were the battery failing to start.

Mutation also found two defects in the battery itself:

- **N2b claimed a proof it does not deliver.** It asserted that `(w=8,cap=4)`
  and `(w=4,cap=8)` differ, and the comment claimed this showed the two fields
  are not folded into one. Under an exact fold (`cap := w`) the worlds become
  (8,8) and (4,4) — still distinct, so the row sails through the very defect it
  advertised. Restated; N1b and N2 own that law.
- **N2c had a dead conjunct.** `a == b and a == ids["two"] or a == b` groups as
  `(… and …) or (a == b)`, so the middle term could never change the verdict —
  and it was false anyway. Second such case this round after commit 0's
  ordering row.

The battery is now fault-isolated per row, because mutation showed a raise
inside N4d's setup aborted the section and reported the failure under **N4's**
name — a law that still held taking the blame for a law that had been disproved.

---

## 2. The easy half — the `~~` spelling

The Core edge grammar is `^\[(?:\w+:)?(\w+)\]\s*--(\w+)-->\s*\[(?:\w+:)?(\w+)\]$`.
A route mirrors it unambiguously; `~` appears nowhere else in the surface, so
all candidates below lex cleanly.

| | Form | Note |
|---|---|---|
| **S1** | `[p0] ~~msg~~> [mb]` | tagged, mirrors `--sig-->` exactly |
| **S2** | `[p0] ~~> [mb]` | untagged; asserts there is only ever one async relation |
| **S3** | `[p0] ~~msg~~> [mb] (body=0.0.0.7, every 2)` | tagged + emission parameters |

**My recommendation: S3.** S1's tag slot costs nothing and keeps a second async
relation available without a grammar change, matching how `--sig-->` /
`--socket-->` already work. The parenthesised group is where the emitter's
parameters have to go regardless of §3's outcome, and it reuses `_paren_kv`
verbatim. S2 forecloses a relation kind to save four characters.

**This is the half I am confident about, and it is not what is blocking.**

---

## 3. The hard half — the route's identity substrate

The Slice A spec stages Slice B as:

> A minimal deterministic emitter (clock-driven, static target and payload, in
> the spirit of `PulserDecl`'s *"never data-dependent"* invariant) emits during
> REACT into `next_inbox`.

A delivered message borrows ADMIT identity wholesale (`admit.py::_message`:
*"Slice A borrows ADMIT identity wholesale (§1) rather than inventing a message
id"*). Its identity is the **ClaimFactKey** `(writer_id, sequence, digest,
payload_key)`, and admission keys on the **event key** `(writer_id, sequence)`.

So a world-emitted route must produce an event key. Three limits follow, and
they are the reason this is a ruling and not a commit.

### F1 — A static route delivers exactly ONCE, ever

ADMIT is idempotent on event keys; that is the point of monotone claim facts.
A route with a fixed `(writer_id, sequence)` and a static body re-asserts an
already-accepted fact every epoch:

```
epoch 0  next_inbox=[(0,0,0,7)]  inbox=[]
epoch 1  next_inbox=[]           inbox=[(0,0,0,7)]
epoch 2  next_inbox=[]           inbox=[]
epoch 3  next_inbox=[]           inbox=[]
```

"Static target and payload" therefore cannot mean a static *key*. Something in
the key must advance per emission, and the only field available is `sequence`.

### F2 — `sequence` is 4 bits

`admit.py::WK = 4`, so `writer_id` and `sequence` each range 0..15, and
`wrl_scenario` validates authored claims against exactly that range. A route
emitting once per epoch therefore has at most 16 distinct keys before it wraps
and starts re-asserting its own earlier facts.

`WK` is not a free parameter: `admit_ic.py` derives `FKEY_W = 2*WK + CKEY_W = 52`
and `EKEY_W = 2*WK`, so widening it changes every backend term — a backend
identity event for every world in the corpus, mailbox-bearing or not.

### F3 — The binding limit is 6, not 16 *(this is the one that matters)*

The claim-fact log is bounded at `MAX_FACTS = 6`. A route needing a fresh key
per emission consumes one fact per emission, so it emits **at most six times in
the world's entire lifetime**:

```
epoch 0  facts=1  emitted=yes     epoch 5  facts=6  emitted=yes
epoch 1  facts=2  emitted=yes     epoch 6  facts=6  emitted=NO   fact_capacity_fault=1
epoch 2  facts=3  emitted=yes     epoch 7  facts=6  emitted=NO   fact_capacity_fault=1
```

**The saturation is announced, not silent** — `fact_capacity_fault` latches to 1
at epoch 6, and I want to be fair to the substrate about that: it tells the
truth. But a recurring route on the Slice A substrate has a hard lifetime budget
of six messages, and the Spinner Bench's 9-epoch run is long enough to cross it.

This is not a bug. `MAX_FACTS` bounds a *monotone* structure, and monotonicity
is a frozen Slice A law — the log cannot GC without breaking it. It simply means
**a recurring `~~` route and the claim-fact log are not obviously compatible**,
and the staging note does not address it.

### F4 — A scenario can silently cancel a world's route

`writer_id` is one 4-bit space shared by world-emitted sends and scenario
claims. Two sends sharing an event key with **different** bodies are
`equivocal_send`, and nothing is delivered:

```
distinct writers 3,4 -> both delivered   next_inbox=[(0,0,0,1),(0,0,0,2)]  recognition=u
SAME key (3,0), different bodies         next_inbox=[]                     recognition=d
SAME key (3,0), identical bodies         next_inbox=[(0,0,0,1)]            recognition=u
```

Scenarios are **not** part of world identity (D3). So under any scheme where a
route's `writer_id` lands in the scenario-authorable range, a scenario can
suppress a world's own route emission without touching the world — precisely
the scenario/world separation established in v0.4-0. Sixteen writers is a small
space to collide in, and shipped scenarios already use writer_ids 1 and 2.

---

## 4. Questions

**Q1 — the `~~` spelling.** S1, S2 or S3 (§2)? *Recommend S3.*

**Q2 — the canonical route-key schema.** What identifies a route for canonical
ordering, `SemanticDiff`, duplicate detection and diagnostic locators?
(a) `(source, mailbox)`; (b) `(source, tag, mailbox)`; (c) `(source, tag,
mailbox, body)`; (d) an authored route name. Edges are keyed structurally
today, and a route needs a stable locator — `ObjectKey` names one object and a
route names two. *Recommend (b), with a duplicate route a typed rejection, and
a new `RouteKey` locator rather than overloading `ObjectKey`.*

**Q3 — the emission budget (F1–F3). This is the blocking one.** Options:
1. **Bounded-by-declaration.** A route declares a finite emission count inside
   the frozen budget and is a typed rejection if it could exceed `MAX_FACTS`.
   Honest, needs no frozen change, and makes the budget visible in the source —
   but a "route" that fires six times is closer to a scheduled batch of sends
   than to a channel.
2. **A separate identity substrate for world-emitted sends**, so routes do not
   consume claim facts at all. Preserves recurrence and monotonicity, but it is
   exactly the "inventing a message id" that Slice A §1 deliberately refused.
3. **Raise `MAX_FACTS`.** Moves backend width; a corpus-wide identity event; and
   only postpones the wall.
4. **Recurrence is out of scope for Slice B** — one route emits at most once,
   and recurrence waits for `forge.world.async.v1`.

*I lean 1 or 4.* Both keep every frozen law intact and neither pretends the
budget is not there. I do not think I should choose between them: option 4 is a
scope decision about what `~~` promotion means, and §14 promotion is yours.

**Q4 — the writer namespace (F4).** Reserve a sub-range of the 4-bit
`writer_id` space for world-emitted routes (narrowing `ScenarioV1`'s validated
range, which rejects some currently-valid scenarios), or give world-emitted
sends a disjoint identity domain, or accept scenario collisions as authored
risk? *Recommend a reservation;* authored risk makes world behaviour depend on
a scenario that is deliberately outside world identity.

**Q5 — which roles may source a route?** `Pulser` only (clock-driven, matching
the "never data-dependent" invariant), or any node? *Recommend Pulser only for
Slice B* — it is the only role that already carries a clock, and widening later
is additive.

---

## 5. What I will do without a ruling

Nothing that touches these decisions. Specifically I will **not** guess the
route key or the emission budget, because both are identity-bearing and both
would be expensive to unwind after a battery pins them.

I will not freeze the Slice B line: per your ruling the mailbox declaration and
the first `~~` route ship together, and `binding_run46`'s own verdict line says
so. If you want the inert declaration reverted rather than left unfrozen in the
tree, say so and I will pull it.

---

## 6. The attached tree

This packet ships a **runnable** tree — the whole `forge/` module set, the
battery corpus, and `runtime/` — not an excerpt. The first draft shipped nine
hand-picked files and told you to run the sweep, which that tree could not do.
`run_l0_sweep.py`'s own docstring names that failure, so it would have been a
poor thing to hand you.

Key files: `forge/binding_run46.py` (commit 1 battery, N1–N12) ·
`forge/binding_run45.py` (commit 0) · `forge/wrl_ir.py` (parser: `_ROLE_TOKEN`,
required-`{}` rule, Mailbox cfg, bootstrap branch) · `forge/wrl_canonical.py`
(port table, `validate_port_projection` locator) · `forge/wrl_format.py`
(inverted emitter vocabulary) · `forge/wrl_plan.py` (`_PlanView.mailboxes` —
declared and provably ignored) · `forge/admit.py` (`WK`, `MAX_FACTS`, the two
seams, `_message`) · `forge/wrl_scenario.py` (the shared writer space) ·
`mutate46.py` (mutation harness + null control) ·
`FORGE_SEMANTIC_IR_v1_1_MAILBOX_SLICE_A_SPEC.md` and `WRL_CORE_0.1.md`.

### Reproducing

**Run the sweep first** — no `ic32` binary ships (it is platform-specific), and
the sweep builds it from `runtime/c/ic32.c` with `gcc -O2`. Verified from a
clean extraction on Python 3.14.2:

```
cd forge && python3 run_l0_sweep.py     # builds ic32; ALL PASS -- 14/14 green (135s)
cd forge && python3 binding_run46.py    # PASS_REF_AND_NATIVE, N1-N12
cd ..    && python3 mutate46.py         # 12 mutants, null control first: ALL CAUGHT
```

With no compiler available, `TRVM_SKIP_NATIVE=1` gives `PASS_REF_ONLY` — every
law still runs; native adds a second independent reducer, not new laws. Running
`binding_run46.py` *before* the sweep fails one row (`N12`) with a located
`FileNotFoundError` for the unbuilt binary rather than a stack trace, which is
the per-row fault isolation described in §1 doing its job.
