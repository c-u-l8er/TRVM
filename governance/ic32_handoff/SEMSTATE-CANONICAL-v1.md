# TRVM Semantic State Canonical Form v1
### The language-neutral specification of `semStateId`, extracted from the frozen JS kernel (trvm_law_kernel.mjs v1.0.2) — the digest both implementations must reach through their own canonical bytes

Status: **extracted specification** (round 9, Lane A). Authority order: the frozen
laws (`law:state.semantic-quotient@1`, `law:state.exec-identity@1`,
`law:kernel.identity@2` in invariant-grid.json v1.5.0) > this document > any
implementation. The JS kernel is the **conformance oracle**: where this document
and the oracle's observable behavior disagree, the discrepancy is a falsifier to
send back to Lane A with an executable witness — never a license to change
semantics silently. Golden **digest** vectors already ship (see §7); golden
**pre-hash byte** vectors require the kernel 1.1.0 module interface and are Lane
A's committed next deliverable.

---

## 0. What this identity is, and is not

`semStateId` is SEMANTIC identity: two states digest equal iff they are the same
program state up to heap-id bijection, dead heap content, allocation order,
alpha-renaming of bound names, and DUP/SUP label bijection. It quotients exactly
what `execStateId` (execution identity: total heap in id order, dead entries
included, deliberately allocation-sensitive) does not. Cross-allocator and
cross-implementation claims bind `semStateId`, never the execution id. ic32
milestone #5 is: same semantic state ⇒ same canonical bytes ⇒ same SHA-256, with
the JS side producing the identical bytes.

## 1. The state

A state is `(frt, root)`:

- a term DAG rooted at `root`, with node kinds
  `Var{nam}`, `Era`, `Lam{nam, bod}`, `App{fun, arg}`, `Sup{lab, lft, rgt}`,
  `Dup{lab, lft, rgt, val, bod}`;
- a substitution store `frt.sub : name → term` (affine: a name is written at
  most once);
- a floating-dup heap `frt.heap : id → {lab, l, r, val}` — the two projection
  names `l`, `r` are how tree terms reference a heap entry (a `Var` whose name
  is some entry's `l` or `r`).

**Names.** A name is *free* iff it is a string starting with `"free:"`; free
names are constructors and are never canonicalized (they carry their literal
spelling into the digest). Every other name is bound (binders and pending
wires) and is subject to canonical renumbering.

**Child order (normative, used by every traversal below):**
`Var: []`, `Era: []`, `Lam: [bod]`, `App: [fun, arg]`, `Sup: [lft, rgt]`,
`Dup: [val, bod]`.

## 2. `chase` — transparent substitution resolution

Every traversal reads nodes through `chase`, a structural lookup (not an
interaction): while the node is a bound `Var` whose name is present in
`frt.sub`, replace it by the stored term. (The oracle carries a ≥64-hop
knot-detector that returns the `Var` itself on an indirection cycle; a correct
state never reaches it — an implementation may treat an indirection cycle as
ill-formed.)

## 3. Live-heap discovery order

`liveDiscoveryOrder(frt, root)` produces the sequence of heap ids **in first
reach order from the root**. Precompute `heapByProj : projName → id` mapping
each entry's `l` and `r` to its id. Then run an explicit-stack DFS, `chase`-ing
every popped node, skipping already-seen node objects:

- pop a `Var`: if its name maps to a heap id not yet recorded, **record the id**
  (this is the discovery order) and push that entry's `val`;
- pop a `Lam`: push `bod`;
- pop an `App`: push `arg`, then `fun` — so `fun` is visited first;
- pop a `Sup`: push `rgt`, then `lft` — so `lft` is visited first;
- pop a tree `Dup`: push `bod`, then `val` — so `val` is visited first.

The result is the canonical order in which the live heap is folded, and the
index of an id in this order is its **discovery index** (used by semantic loci,
§6). Dead entries — ids never reached — do not appear: that is the quotient
over dead heap content.

## 4. Canonical live fold

`foldCanonicalLive(frt, root)`: rebuild a single tree by wrapping the root with
one `Dup` node per live heap entry, iterating the discovery order **in
reverse** so the first-discovered entry is outermost:

```
acc := root
for i from |order|-1 down to 0:
    d := frt.heap[order[i]]
    acc := Dup{lab: d.lab, lft: d.l, rgt: d.r, val: d.val, bod: acc}
```

`semStateId(frt, root) = stateDigest(frt, acc)`.

## 5. `stateDigest` — the canonical, binder-faithful, equivariant digest (v2)

Two phases over the folded term, both reading through `chase` and both
deduplicating on node identity (a shared subterm is visited once — the digest
is over the DAG, not its unfolding).

**Phase 1 — canonical ids by first occurrence.** Two counters, `nn` for names
and `ln` for labels, both starting at 0. Walk the DAG in the same
explicit-stack preorder as §3 (identical push orders). At each node:

- `Var`: if bound, assign the name the next `nn` (first occurrence only);
- `Lam`: assign `nam`, push `bod`;
- `App`: push `arg`, `fun`;
- `Sup`: assign `lab` the next `ln`, push `rgt`, `lft`;
- `Dup`: assign `lab`, then assign `lft`, then `rgt` (in that order), push
  `bod`, `val`.

First-occurrence numbering is what makes the digest alpha- and
label-equivariant by construction.

**Phase 2 — memoized post-order signature.** Each node gets a signature
string over canonical ids (children's signatures are the memoized results of
their `chase`d nodes):

| node | signature |
|---|---|
| free `Var` | `F` + literal name |
| bound `Var` | `N` + nameId |
| `Era` | `E` |
| `Lam` | `L` + nameId + `(` + sig(bod) + `)` |
| `App` | `A(` + sig(fun) + `,` + sig(arg) + `)` |
| `Sup` | `S` + labId + `(` + sig(lft) + `,` + sig(rgt) + `)` |
| `Dup` | `D` + labId + `[` + nameId(lft) + `,` + nameId(rgt) + `](` + sig(val) + `,` + sig(bod) + `)` |

Ids print in decimal with no padding. **Internal compaction:** any signature
whose length exceeds 80 characters is replaced by `#` + lowercase-hex
SHA-256 of the signature string (UTF-8) — full width, never truncated, so an
inner node cannot undercut the outer commitment.

**Result:** `stateDigest = lowercase-hex SHA-256 (UTF-8) of the root's
signature`. Evidence identities are never truncated.

### 5.1 Worked examples — verified against shipped oracle output

Every hash below was hand-derived from this document alone and checked against
an id the oracle already shipped; the matching artifact row is named. These are
the byte-level anchors until the kernel-1.1.0 pre-hash vectors land.

**(a) `λx.x` — the `identity` vector's initial state (heap empty, so
`execStateId = semStateId`).** Phase 1: `{x → 0}`. Phase 2: `Var → "N0"`,
`Lam → "L0(N0)"`.

```
semStateId = SHA-256("L0(N0)")
           = 546334a80cfb56f8163e59ffb85a0b1edec290fc2e4948fe1de3dbd43748be45
```

**Verified**: equals `scheduler_certificate.json`
`run_manifest[identity/leftmost].final_state_id` (a 0-step run, so final =
initial state).

**(b) Free-variable signing (mechanical; byte form follows §5's table
directly).** The tree `(S Z)` with free `S`, `Z` signs `A(Ffree:S,Ffree:Z)` —
note the `free:` prefix is inside the digest bytes while the printer (§9)
strips it. No shipped digest isolates this state; cross-check against the
oracle before treating any derived hash as golden.

**(c) Compaction boundary (mechanical).** A signature of exactly 80 characters
passes through; 81 becomes the 65-character `#`+hash form. Property-test the
boundary.

## 6. Semantic loci (used by semantic films)

For a redex `rx`, with `order` the discovery order of §3 and `ix(id)` the
decimal discovery index (`"?"` if absent):

- tree application: `"t:" + path.join(".")` (path = child keys from root);
- heap dup: `"d:" + ix(id)`;
- var-position redex: `"v:" + ix(id) + ":" + path.join(".")`.

Loci are allocation-independent by construction. Semantic film frames carry
the canonical locus and semantic pre/post ids; the film commitment domain is
`"TRVM-SEMFILM-v1.1"` (v1.1 commits budget and remaining_work in the terminal
witness — see the grid's `semantic_film` section and
`law:film.terminal-witness@1` lineage). Replay refusals to reproduce
verbatim: `sem-revision-mismatch`, `sem-terminal-state-mismatch` (full
vocabulary in the grid's semantic_film section).

## 7. The relation — rules, gating, planes (what a step *is*)

Nine rule names from eight schemata (the two `DUP-SUP` cases split on label
equality). `f0,f1,x0,x1,a0,a1,b0,b1` are fresh names; `alloc` creates a heap
entry; `setSub` writes the write-once store; a fired heap entry is **deleted
before** its rule body runs.

**Tree App redexes** — an `App` node whose `chase(fun)` is:

- `APP-LAM` — `(λn.B A)` ⇒ `setSub(n, A)`; the node becomes `B`.
- `APP-SUP` — `(&L{F,G} A)` ⇒ `alloc(L, x0, x1, A)`; becomes
  `&L{(F x0),(G x1)}`.
- `APP-ERA` — `(* A)` ⇒ becomes `*`.

**Heap dup redexes** — entry `d = {lab,l,r,val}` classified on
`v = chase(val)`:

- `DUP-LAM` (`v = λn.B`) ⇒ `setSub(l, λx0.f0)`, `setSub(r, λx1.f1)`,
  `setSub(n, &lab{x0,x1})`, `alloc(lab, f0, f1, B)`.
- `DUP-SUP=` (`v = &lab{L,R}`, label equal) ⇒ `setSub(l, L)`, `setSub(r, R)`.
- `DUP-SUP!` (`v = &M{L,R}`, `M ≠ lab`) ⇒ `setSub(l, &M{a0,b0})`,
  `setSub(r, &M{a1,b1})`, `alloc(lab, a0, a1, L)`, `alloc(lab, b0, b1, R)`.
- `DUP-ERA` (`v = *`) ⇒ `setSub(l, *)`, `setSub(r, *)`.
- `DUP-VAR` (`v` a **free** `Var`) ⇒ `setSub(l, v)`, `setSub(r, v)`.
- `DUP-APP` (`v` a **genuinely stuck** `App`) ⇒ `setSub(l, (f0 x0))`,
  `setSub(r, (f1 x1))`, `alloc(lab, f0, f1, v.fun)`,
  `alloc(lab, x0, x1, v.arg)`.

**Gating (WAIT is not a redex).** A dup whose `chase(val)` is a *bound* `Var`
with no sub entry, or a *reducible* `App`, does not fire — the wire's peer has
not arrived. *Genuinely stuck* (`isStuckApp`): the App's head chases to a
**free** `Var` through zero or more stuck Apps.

**Planes** (`law:plane.rule-partition@1`):
`INTERACT = {APP-LAM, APP-SUP, APP-ERA, DUP-LAM, DUP-SUP=, DUP-SUP!, DUP-ERA}`,
`COLLAPSE = {DUP-VAR, DUP-APP}` (gated as above). The declared hybrid pool is
their union in exactly this insertion order — this string appears verbatim in
film-id preimages (§10.2):

```
APP-LAM,APP-SUP,APP-ERA,DUP-LAM,DUP-SUP=,DUP-SUP!,DUP-ERA,DUP-VAR,DUP-APP
```

A film names its plane pool; silent mixing refuses at replay. **Liveness gates
firing too**: only *live* dups (one projection reachable from the root through
subs and live heap values) may fire — a dead `DUP-LAM` on a shared lambda would
write that lambda's binder a second time, the double consumption affinity
forbids. Garbage does not compute.

## 8. Redex enumeration — the order the golden films bind

Replay (§10.5) matches loci and never needs an order, and `remaining_work` is a
count. But the golden `sem_film_id`s were generated under the **rotating
free-choice schedule** — at step `k`, fire `enabled[k mod |enabled|]`, an index
into this enumeration — so reproducing them requires reproducing the order
exactly.

`findFloatRedexes(state, pool)` returns, in order:

1. **Tree App redexes** from `findAppRedexes(root)`: explicit-stack **preorder**
   DFS, children pushed in *reverse* field order (so visited fun-before-arg,
   lft-before-rgt), `chase` at every node, visited-node dedup; `path` = the
   child-field-name sequence from the root; emit `{kind:"app", path, rule}` as
   encountered.
2. For each live dup id **in `liveHeap` insertion order** (see below): the dup
   redex `{kind:"dup", id, rule}` if classified and pool-admitted, then
3. that dup's value's App redexes `{kind:"dupval", id, path, rule}` via
   `findAppRedexes(val)`.

**`liveHeap` insertion order** (deliberately different from §3's discovery
order): explicit-stack DFS from the root; per popped node `n = chase(·)`: if
`n` is a bound `Var` projecting an undiscovered dup, insert that dup's id and
push its `val`; then push `n`'s children **in natural field order** — LIFO, so
they are visited *last-child-first* (an `App`'s `arg` before its `fun`). Same
discovered *set* as §3, different *sequence*. §3's order is the semantic one
(loci, canonical fold); this one only sequences enumeration.

## 9. Readback, the canonical printer, and `semId`

`nf_id` is a hash of a *printed string*, so the printer is normative.

**Readback** (`budget` default 2,000,000 driver steps): (1) fold the **live**
heap, ascending id order, as `Dup` wrappers around the root (dead entries stay
dropped); (2) normalize with the reference normal-order driver: `whnf` descends
the spine through subs, pushing `App`/`Dup` frames, and on reaching
`Lam`/`Sup`/`Era`/free-or-unsubbed `Var` combines frames upward by §7's
schemata in tree form (a stuck `App` frame is rebuilt and popping continues; a
`Dup` frame over a bound-but-unsubbed `Var` collapses `DUP-VAR` on it);
`normalRef` rebuilds post-order with `whnf` at every node entry. **Purity
obligation:** from pool-quiescence, readback fires **zero INTERACT rules** —
only `DUP-VAR` collapse, bounded by the residual live-dup count.

**Canonical printer** (`show`): names assigned at first *print-traversal*
occurrence — occurrence 0–25 → `a`…`z`, then `v26`, `v27`, …; free variables
print **without** the `free:` prefix; forms `λ<n>.<bod>`, `*`,
`(<fun> <arg>)` (exactly one space), `&<lab>{<lft>,<rgt>}` (label always
printed, even 0), `!&<lab>{<l>,<r>}=<val>;<bod>`; no other whitespace.

**`semId(nfString) = "sem-" + SHA-256hex(nfString)`.** Verified against
`refinement_receipt.json` `per_term[*].nf_id`:

```
semId("λa.a")          = sem-1f10ab22e7733422758958046a42f4522b020c1ac1b2a8368382b131a1064aa6   (identity)
semId("&0{λa.a,λb.b}") = sem-5811ddb9fc66feb4…   (sup_app — pins the &0{…} printer form)
semId("(S (S Z))")     = sem-30d719c1b7be5cad…   (church_apply_2 — pins free-var printing and App spacing)
semId("λa.(a λb.b)")   = sem-05e42f83c7a14591…   (apply_id)
```

## 10. Films — the portable evidence objects

### 10.1 Frames and the chain

`{i, plane, rule, locus, pre, post, prev, frame_id}` — `i` and `prev` are
**declared non-authoritative** (replay counts and re-chains for itself).

```
frame_id = SHA-256hex( prev | pre | plane | rule | locus | post )
```

joined by the single byte `|`; `prev` is the previous `frame_id` or the
literal `genesis`.

### 10.2 Terminal and film id

Terminal fields: `{last_frame, termination, steps, <final id>,
normal_form_id?, budget?, remaining_work?, planes?}` — `<final id>` is
`final_state_id` (exec) or `final_sem_id` (sem). Absent optional fields render
as `-` in the preimage; `steps` renders in minimal decimal; `planes` joins by
`,` in pool order (§7).

```
exec: film_id = SHA-256hex("TRVM-FILM-v3.1"    |last_frame|termination|steps|final_state_id|nf-or-"-"|budget-or-"-"|remaining-or-"-"|planes)
sem:  film_id = SHA-256hex("TRVM-SEMFILM-v1.1" |last_frame|termination|steps|final_sem_id  |nf-or-"-"|budget-or-"-"|remaining-or-"-"|planes)
```

The v1.1 sem revision **commits the budget-terminal witness fields**
(`law:film.terminal-witness@1` — the round-6B audit forged a v1 terminal; the
outcome is inside the commitment).

**Verified example** (identity; 0 steps; §7 pool; no budget fields):

```
exec preimage: TRVM-FILM-v3.1|genesis|NORMAL_FORM|0|546334a8…be45|sem-1f10ab22…4aa6|-|-|APP-LAM,APP-SUP,APP-ERA,DUP-LAM,DUP-SUP=,DUP-SUP!,DUP-ERA,DUP-VAR,DUP-APP
  → 6196cb0d1510b80ffa4db6e8b4c02c17203b7195c571001ce0869015c0cfa7bf   (= cert run_manifest[0].film_id)
sem  preimage: TRVM-SEMFILM-v1.1|genesis|NORMAL_FORM|0|546334a8…be45|sem-1f10ab22…4aa6|-|-|<same pool>
  → 0a9e6c0d6895e82f650ca5fb560b940a37cc97cbc3e312057c291dae40471ea5   (= refinement per_term[identity].sem_film_id)
```

### 10.3 Semantic film generation

At each step along any schedule: `pre = semStateId(state)`; choose an enabled
redex `rx`; `locus = semLocusOf(rx, liveDiscoveryOrder(state))` (§6); fire;
`post = semStateId(state′)`; chain per §10.1. Sealing derives `final_sem_id`;
for `NORMAL_FORM` terminals, `normal_form_id` via readback+`semId` (null if
readback exceeds its budget); for `BUDGET_EXHAUSTED`, `remaining_work` as the
**live enumeration count under the declared pool at the sealed state**.

### 10.4 Terminal obligations — re-derived at replay, never accepted

- `NORMAL_FORM`: zero enabled redexes in the pool at the end
  (`sem-false-normal-form`); a non-null `normal_form_id` must re-derive
  (`sem-terminal-nf-mismatch`).
- `BUDGET_EXHAUSTED` (`law:film.terminal-witness@1`): `budget` and
  `remaining_work` integers (`sem-terminal-malformed`); end-state enumeration
  count `== remaining_work` (`sem-terminal-work-mismatch`); `steps == budget`
  — one-step integral progression, no resumed films (`sem-budget-mismatch`);
  `remaining_work > 0` — a `BUDGET_EXHAUSTED` claim on a quiescent state
  refuses (`sem-no-remaining-work`).
- any other termination string: `sem-terminal-malformed`.

(Deliberately stricter than execution films, which accept `steps >= budget`
and `remaining_work == 0` — the portable terminal class IS the claim; see the
grid's `semantic_film.strictness_delta_vs_execution_films`.)

### 10.5 Semantic replay (`replaySemFilm`) — ic32's conformance mode

Given the source term, a film, and **any** runtime implementing the relation:

```
state := extrude(parse(srcTerm));  prev := "genesis";  n := 0
for each frame:
  1  frame.rule ∈ pool                           else sem-plane-not-permitted
  2  semStateId(state) == frame.pre              else sem-revision-mismatch
  3  rx := enabled redex with semLocusOf == frame.locus
                                                 else sem-locus-not-enabled
  4  fire rx; not refused                        else sem-not-a-redex
  5  fired rule == frame.rule                    else sem-rule-mismatch
  6  plane(rule) == frame.plane                  else sem-plane-mismatch
  7  semStateId(state′) == frame.post            else sem-post-mismatch
  8  frameId(prev,pre,plane,rule,locus,post) == frame.frame_id
                                                 else sem-chain-mismatch
  prev := frame.frame_id;  n += 1
then:
  terminal present, termination a string         else sem-terminal-missing
  terminal.last_frame == prev                    else sem-terminal-last-frame-mismatch
  terminal.steps == n                            else sem-terminal-steps-mismatch
  terminal.final_sem_id == semStateId(state)     else sem-terminal-state-mismatch
  §10.4 obligations for the termination kind
  semFilmIdOf(terminal) == film.film_id          else sem-film-id-mismatch
```

Enabledness is inherent: an unmatched locus refuses. The full vocabulary
(19 refusals, verbatim, matching the grid's `semantic_film.replay_refusals`):
`sem-terminal-missing, sem-plane-not-permitted, sem-revision-mismatch,
sem-locus-not-enabled, sem-not-a-redex, sem-rule-mismatch, sem-plane-mismatch,
sem-post-mismatch, sem-chain-mismatch, sem-terminal-last-frame-mismatch,
sem-terminal-steps-mismatch, sem-terminal-state-mismatch,
sem-false-normal-form, sem-terminal-nf-mismatch, sem-terminal-malformed,
sem-terminal-work-mismatch, sem-budget-mismatch, sem-no-remaining-work,
sem-film-id-mismatch`.

**Exec replay contrast**: `replayFloat` is the same shape over execution loci
and `execStateId`, intentionally non-portable — the shipped refinement run
replayed the descending allocator's exec films on the ascending oracle and
**refused on 17/24** (`refinement_receipt.json` `summary`); the refusals are
the demonstration that execution identity does not travel.

## 11. What the oracle already pins down (golden fixtures, shipped)

- `refinement_receipt.json` (24 terms) — **the parity targets**: per-term
  `nf_id`, `sem_film_id` (rotating schedule, §8), `exec_film_id_A/B`, with
  `sem_chain_equal: true` and `sem_film_replay_on_B: ok` across all 24;
  `receipt_id = SHA-256("TRVM-REFINE-v1|" + JSON(per_term) + "|" +
  JSON(summary))`.
- `scheduler_certificate.json` (144 receipts = 24 vectors × 6 schedulers):
  per-run `final_state_id` (execution id — expect these to *differ* from
  yours), `nf_id` (semantic — expect these to *match*), `film_id`; corpus
  commitment `{id: "conformance-vectors", sha256: c2775f7b…}`.
- `golden_sem_ids.json` — convenience projection joining each vector's source
  term, expected nf string, and reference interaction count with its receipt
  row, plus provenance digests. Derived; the receipt is authoritative.

**Conformance ladder (digest-level, available now):**

1. **Parse/print round-trip** on the 24 source terms.
2. **NF parity** — normalize under *any* pool schedule; printed string equals
   the vector's `nf`; `semId` of it equals the receipt `nf_id` (24 targets).
3. **Initial-state sem id** — one shipped anchor today (identity, §5.1a); the
   rest arrive with the kernel-1.1.0 vector extraction.
4. **Rotating-schedule sem film** — regenerate each vector's film under §8's
   schedule; `sem_film_id` equals the receipt's (24 targets — transitively
   checks per-step `semStateId`, loci, enumeration order, chaining, terminal).
5. **Cross-replay** — ic32 films on the JS oracle and oracle films on ic32
   (frame serialization to coordinate with Lane A); every refusal must be one
   of §10.5's nineteen, and every refusal is a falsifier deliverable.
6. **Exec split** — implement `execStateId` under ic32's own allocator and
   demonstrate the §0 split (sem parity, exec divergence). Exec divergence is
   *expected*; sem divergence anywhere is a stop-the-line falsifier.

The conformance criterion for milestone #5 is: ic32's ids reach the shipped
digests through ic32's **own** implementation of §§2–10 — never by
transliterating the oracle's code.

## 12. Falsifiers to run before believing your implementation

Ascending vs descending allocator (equal sem id); random heap-id bijections,
including mid-run (invariant); dead-entry injection (exec differs, sem equal);
alpha-renaming (equal); label permutation (equal); same semantic state via
different allocator histories (equal); intentionally wrong DUP behavior
(digests apart); one altered canonical locus in a film (replay refuses);
JS-film-replayed-by-ic32 and the reverse (both ok). The kernel's own batteries
prove each on the oracle side; ic32 must reproduce them independently.
