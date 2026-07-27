# Slice B, Commit 3 — the `~~` surface: closure memo

**Status:** CLOSED. `binding_run48` PASS_REF_AND_NATIVE (6s, 71 rows).
`mutate48` **19/19 ALL CAUGHT**. Full sweep `run_l0_sweep` **16/16 green** (141s,
reference + native), L-0 tier unmoved.

Commit 2 gave a route a canonical form and an identity but no spelling. Commit 3
gives it the ruled spelling in both directions:

```
[p0] ~~msg~~> [mb] (body=0.0.0.7)
```

and closes the two things that spelling makes reachable — the Q4 writer-15
reservation, and a silent world substitution in the authoring draft.

---

## 1. What shipped

| file | change |
|---|---|
| `wrl_ir.py` | `_ROUTE_RE`, `_ROUTE_KEYS`, `_body_dots`, the route branch in `_parse_core_permissive`; bootstrap `~~` message split off from `!!`/`==` |
| `wrl_format.py` | route section emitted after the edges, `_emit_body` |
| `wrl_canonical.py` | `WRL_ROUTE_WRITER_RESERVED`, `routes_of_artifact` |
| `wrl_scenario.py` | `check_route_writer_reservation`, `check_world_compatibility` |
| `wrl_draft.py` | `WRL_DRAFT_LOSSY_WORLD`, the computed `_draft_loss` round-trip, both draft doors |
| `spinner_bench.py` | call site widened to the composed door |
| `binding_run47.py` | closing NOTE corrected (it said "there is no `~~` surface") |

The parser's job stops at *"this line says a route."* Endpoint roles, the
one-shot source law, the body range, duplicates and the budget are all the
seal's, and they are the seal's for a route arriving from **any** surface. Every
Q7 row proves this twice: the parse **succeeds** and the seal **refuses**. A
parser that had helpfully re-implemented one of these fails the first half.

---

## 2. Five autonomous decisions — please confirm or overrule

### (a) The draft **REFUSES** route-bearing worlds rather than being widened

A `WorldDraft` stores a world as `(objects, edges)`. A route is neither, so it
was invisible. **Measured before the guard was written:** opening the one-route
world for editing produced no error and yielded `sem-d3e555be…` — the route-free
twin, a perfectly good world with a perfectly good id. Legal, which is what
makes it dangerous.

Widening the draft to carry routes is not a language change: it is a new
revision of **every persisted authoring document** — `ForgeProjectV2`, the
v0.6-0 recovery journal, the draft-state ledger, the canvas reconciler. That is
a document-format migration and it does not belong inside a language slice, so
commit 3 ships a **refusal** and defers the widening.

The guard is a **computed round-trip**, not a construct blacklist:

```python
want = W.lower_graph(g).semantic_artifact_id
got, err = _seal(objects, edges, profile)
if err is None and got == want: return None      # nothing was lost
```

It names no construct, so it will refuse the *next* unrepresentable construct
without being edited — the same property that made
`wrl_legacy.export_canvas_graph_v1` learn about routes on its own.

### (b) The loss refusal reports `syntax_error`

`REPLACE_STATUS` has four frozen terminal values. `syntax_error` is the only one
whose **behaviour** is exactly this case (refused, draft untouched, nothing for
the author to repair). It is an imperfect *name*; the diagnostic carries the
honest code `WRL_DRAFT_LOSSY_WORLD`. Inventing a fifth status is a change to a
published contract, not a language decision — hence the deferral.

### (c) Routes emit **after** the edges, not interleaved

Sorting a route into edge order would need one comparison key spanning two
vocabularies, and the two orderings are canonical for different reasons: an
edge's order is **presentational**, a route's order **IS its minted ADMIT
`sequence`** (Q4). Interleaving would make an identity-bearing order look like a
formatting choice. A route-free world therefore emits *exactly* the pre-Slice-B
text — no separator, no empty section (proved by `Q5d`, see §3).

### (d) `check_world_compatibility` composes binding + reservation into one door

Both halves stay callable by name, but production goes through the composed
door, because the failure mode of two independent checks is that a call site
grows one and not the other — and the forgotten half is whichever was added
second. Today that is the reservation. `Q8i` and mutation **M16** are the rows
that hold this.

### (e) The bootstrap DSL gets **no** route directive

It is a frozen migration bridge. Its `~~` rejection was corrected, though: it
used to say *"a transition class, not an IR v1 edge"*, which is now false twice
over — a route **is** an IR v1.1 construct, and it was never an edge (D8). It
now points at the surface that does have one. `!!` and `==` keep the old
message. This is the identical correction commit 1 made for `mailbox`.

---

## 3. What the mutation round found

Three survivors on the first pass, all three real. Recorded because they are the
useful part.

**M9 — the route separator emitted unconditionally. SURVIVED with nothing red.**
The most useful finding. Whitespace is non-semantic, so no identity moved and
`Q5`/`Q5b` stayed green. And the formatter is `graph -> text`, not
`text -> text`, so the extra blank line is a **fixed point** — `Q3b`
(idempotence) stayed green too; the prediction that it would catch this was
simply wrong. Meanwhile the canonical **bytes** of every route-free world in the
tree had moved — the exact law `wrl_format`'s own comment claims ("no blank
separator, no empty section") and which nothing checked. **`Q5d` exists because
of this line**, and states the law structurally (a route-free world's text ends
at its last edge) rather than pinning a literal, which would fork the emitter.

**M11 — `replace_world_source`'s guard removed. `Q9e` stayed green.**
`Q9e` claims "the draft is UNTOUCHED". True, but for the wrong reason: the
route-free twin of that source *is* the draft's current world, so a missing
guard falls through to the semantic-noop branch and leaves revision 0 with the
right candidate. `Q9e` is structurally unable to tell *refused* from *silently
accepted as a no-op*. **`Q9h`/`Q9i`/`Q9j` were added**: a paste whose lost world
is a **different** world (two mailboxes + a route), plus a vacuity check that
the twin really does differ.

**M14 — the reservation widened to every world. Reported as "Q8 raised".**
Not a production defect but a reporting one: `Q8b` raised, and `section()`
renamed the failure after its neighbour — so a reservation made too **strong**
read as a reservation that was **broken**. `Q8b`/`Q8c` are callables now and
keep their own names. (This is the same lesson as run47's "many laws share one
error code": a row must be identifiable as itself when it fails.)

Also worth recording: **M5** (body arity forked onto `_rotor_dots`) is caught
only at section granularity, and `Q1d` cannot see it at all — the rotor message
happens to contain the same `"must have 4 lanes"` while saying *rotor* about a
*body*. That is exactly the drift `_body_dots`'s docstring refuses, and it is
why the two 4s are not one constant.

---

## 4. Not frozen

A route can now be **written, canonicalized, sealed, formatted, and refused for
every reason it should be** — and it still does nothing at runtime. Commit 4
folds it. Freeze the Slice B line after Commit 4, then promote `~~` to Grounded
in `WRL_CORE_0.1.md` §14.

Carried obligation into Commit 4: unify `route_body_in_range` into `admit` to
remove the fork (the obligation is written into the function's docstring).
