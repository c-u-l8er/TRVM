# IN-CRDT — is `merge = union + reduce` a confluent, mergeable *computation*?

**Files:** `incrdt.py`, `incrdt2.py`, `incrdt3.py`, `incrdt4.py`, `incrdt5.py`, `incrdt6.py`, `incrdt7.py`, `idtest.py`, `iceg.py`, `tiers.py`, `frontier.py`, `slotted.py` (each self-validating); plus `compmem.py` and `compmem_ic.py`, the capstones (`python3 compmem.py` / `compmem_ic.py`)
**Status:** ✅ a confluent merge of computation works — operationally and
automatically — for closed sub-terms; and the label problem is now *tested*: sharing
is lost entirely across independently-labeled replicas but **fully recovered, soundly,
by label canonicalization**, narrowing the residual to a globally-collision-free
labeling discipline.

This is the forward result the external-review thread converged on: not "distribute
reduction" (the runtime already does that), but **merge knowledge such that the
object replicated is computation, not data** — a CRDT whose elements are
interaction-calculus derivations. The question is whether reduction *preserves* the
CRDT properties, and whether overlapping knowledge can be merged without paying
twice for already-discovered work.

## The operator

`merge(A, B) = NF(A ∪ B)` — reduce the content-addressed union of two knowledge
sets *as one net*, so shared sub-structure is reduced once and stays shared.

## Level 1 — the axioms (`incrdt.py`)

Knowledge = a set of derivations (`((churchN NOT) bool)`, normal form = a parity
fact). Measured under NAIVE (multiset union) vs CA (content-addressed dedup):

- **Commutativity & associativity hold** — identical facts, work, and size
  regardless of order (confluence + set union).
- **Idempotence is the crux.** `merge(A,A)` vs `A`:
  - RESULT (set of facts): idempotent either way (identical normal forms collapse —
    a *data* CRDT over the facts is a trivial G-Set).
  - SIZE / WORK: **naive fails** (82→164 nodes, 92→184 interactions — two copies,
    re-reduced); **content-addressing restores it** (46→46, 92→92).
- Sub-computation sharing (one shared `NOT⁴` across two uses): 76→49 interactions
  (1.55×) — a first sign that sharing helps even across *distinct* derivations.

**So `merge = union + reduce` is a CRDT iff the union is content-addressed.**

## Level 2 — does reduction *preserve* the properties? (`incrdt2.py`)

Four metrics, because semantic idempotence can hold while operational idempotence
fails:

- **Commutativity/associativity across incremental merges** hold:
  `NF(NF(A∪B)∪C) = NF(A∪NF(B∪C))` — normalizing intermediate merges doesn't break
  confluence.
- **Operational idempotence, all four metrics.** With content-addressing,
  `merge(A,A)` costs *exactly* what `A` costs — rewrites 92→92, nodes 13→13, depth
  6→6. Bag union doubles all three while the normal form stays equal: **Failure 2
  confirmed** (a CRDT semantically, useless operationally).
- **Sharing survives reduction, with an exact cost law.** N derivations sharing
  `(church6 NOT)`: unshared `= 60·N`, shared `= 49 + 11·N`. The expensive core is
  built **once**; you pay ~11 per genuinely-distinct use. This is the "doesn't pay
  repeatedly for already-discovered work" property, measured.
- **Failure 3 — merge becomes inference.** A rule `λx.((church3 NOT) x)` and a fact
  `TRUE`, each individually in normal form, compose to `λa.λb.b` — a *new* fact
  (FALSE) neither held, in 28 rewrites. When pieces share an interface, accumulation
  produces new knowledge. (Honest: this needs composition/wiring, not bare union —
  strictly more than a data structure, and strictly more powerful.)

## Level 3 — the frontier: *automatic* content-addressing (`incrdt3.py`)

Level 2 hand-encoded the DUP sharing. Can a pass find it automatically, and does the
sharing survive reduction when the shared term itself contains dups (Church numerals
do — the hard case)?

`auto_share` finds CLOSED sub-terms repeated ≥2× across the forest, hoists one copy,
and shares it through a DUP fan, guarded by an NF-equality check.

```
auto-share found (church6 NOT): size 34, reused 3x
unshared 180  ->  auto-shared 82      NF(auto)==NF(unshared): True   (2.20x less)

N   unshared   auto   NF ok   ratio
2   120        71     True    1.69
3   180        82     True    2.20
4   240        93     True    2.58
6   360        115    True    3.13
```

The automatic numbers **equal the hand-encoded ones exactly** (`49 + 11·N`), sound at
every N. So: automatic content-addressed merge preserves sharing under reduction —
the dup-of-a-dup case resolves soundly, and the IN-CRDT is real not just
axiomatically but **operationally and automatically**.

## The open problem, now tested (`incrdt4.py`)

The automatic pass above worked partly *because* both replicas generate `church(6)`
with **identical fixed labels**, so the shared sub-term is byte-canonical. The pushed
experiment: break that — have N replicas independently derive the *same* computation
`NOT⁶(FALSE)` with *different* labels — and measure whether sharing survives, under
two content-addressing schemes (label-sensitive vs label-canonical, the latter
alpha-renaming labels by first encounter).

```
same computation, different labels:
  label-sensitive canon equal : False   (content-addressing misses the match)
  label-canonical canon equal : True    (match recovered)

N   unshared  sensitive  canonical  canon NF ok  recovered
1   60        60         60         True         1.00x
2   120       128        63         True         1.90x
3   180       196        66         True         2.73x
4   240       264        69         True         3.48x
6   360       400        75         True         4.80x
```

- **Without canonicalization, the loss is catastrophic.** Label-sensitive
  content-addressing performs like the unshared baseline (in fact slightly worse — it
  wastes a DUP fan sharing the cheap repeated `NOT` while the expensive `church6`
  fails to match across labels). Idempotence breaks *across replicas*: `merge(A,A')`
  costs ~2× even though `A` and `A'` are the same computation.
- **With canonicalization, it is fully recovered, and sound.** Label-canonical
  content-addressing detects the differently-labeled replicas as one computation,
  reduces it once, and the cost goes nearly **constant** (60→75 across N=1→6,
  recovered up to 4.80×) with the normal form unchanged at every N.

So label canonicalization is not merely the problem — it is most of the **solution**.
The loss is catastrophic without it and (here) fully recovered with it.

**The residual, now narrowed.** Soundness held because the shared copy's labels do not
collide with other dups in the surrounding derivations (here there are none). In
general, canonicalizing two *different* computations into overlapping label ranges,
then duplicating copies that later meet, can trigger spurious DUP–DUP annihilation.
So the remaining hard part is narrower than "label canonicalization": it is a
**globally collision-free canonical labeling** — canonical for matching, fresh-on-copy
for soundness — the exact analogue of de Bruijn naming plus freshening for variables,
and the same canonical-form-under-confluent-rewriting problem **e-graphs** solve. The
label problem is therefore not a wall; it is a known-shaped problem, and more of the
distance is already crossed than a fixed-label demo would suggest.

## Does canonicalization scale? (`incrdt5.py`)

If recognizing a duplicate computation costs more than the work it saves, the whole
scheme is pointless — the e-graph-rebuild-overwhelms-the-benefit failure. Measured
(N=4 replicas of `NOT^M(FALSE)`, canon vs reduction, milliseconds):

```
M    termsize  canon_ms  shared_red_ms  unshared_red_ms  canon/red
8    46        0.07      0.28           0.76             0.26
16   78        0.13      0.41           1.48             0.32
32   142       0.25      0.84           3.56             0.30
64   270       0.86      1.85           7.42             0.47
128  526       2.73      3.81           15.95            0.72
```

- **As literally implemented, canon does not stay subdominant.** `canon/red` climbs
  0.26→0.72 and extrapolates to cross shared-reduction near M≈200 — because the
  canonicalizer here rebuilds canonical strings per-subterm, O(n²).
- **But it is still a net win, and the crossover is an artifact.** canon + shared-
  reduce (6.54 ms) still beats unshared-reduce (15.95) by ~2.4× at M=128. Structural
  canonicalization is O(n) with proper hash-consing, paid once per distinct
  computation on insert (amortized over all future merges), lookups O(1) — exactly how
  e-graphs stay cheap. The prototype simply hasn't implemented the linear version.
- **Crucial caveat (the binding one).** This is the **structural** tier — same
  derivation, different labels — which is cheap and decidable. It does *not* measure
  **semantic** identity — same function, different derivation — which is undecidable
  and is the tier e-graphs approximate via equality saturation. Converting *structural*
  equivalence into computational idempotence is shown; converting *semantic*
  equivalence is the open, harder problem, and the scarce resource the whole IN-CRDT
  direction turns on.

The accurate name for what is demonstrated is therefore **structurally content-
addressed computation with confluent merge**.

## Semantic identity via equality saturation (`incrdt6.py`)

Structural canonicalization recognizes "same derivation, different labels." It misses
"same function, different derivation" — `church(6)` vs `mult(church2,church3)` reduce
to the same normal form but are structurally unrelated. Recognizing *those* is program
equivalence, undecidable in general. The e-graph bet: can a small rewrite-ruleset +
congruence closure recognize such equalities for less than the cost of reducing both?

A minimal e-graph (union-find over e-classes, hash-consed e-nodes, congruence rebuild;
self-test passes — merging `a=b` discovers `f(a)=f(b)` and `g(f(a))=g(f(b))`) with a
church-arithmetic ruleset (`fold`, `commutativity`):

```
(A) ground truth: church(6), mult(2,3), mult(3,2), mult(6,1) all reduce to church6
                  (semantically equal); reduction costs 5 / 16 / 20 / 30
(B) structural canon: 4 distinct keys of 4 -> FAILS to recognize them
(C) e-graph: 4 rewrite-firings; all four in ONE e-class -> RECOGNIZED
             recognize-by-rules 4 firings  vs  recognize-by-reducing 71 interactions
```

The e-graph recognizes all four as equal **without evaluating any of them** — the
recognition-without-reduction that is the whole point of equality saturation.

Three honest caveats:

- **Units.** A "firing" is not an "interaction"; the real e-graph cost is the
  saturation/congruence loop, and e-graphs can *explode* for the wrong ruleset. This is
  a small-case illustration that rules can beat reduction, not a law.
- **Binders (the real bridge).** The e-graph reasoned over a symbolic algebra supplied
  by hand (`Cn:6`, `Mul`, …), separate from the raw interaction-calculus terms. Lifting
  saturation to operate directly on IC terms means putting binders in the e-graph and
  using beta/eta as rules — the known-hard "e-graphs with binders" problem (slotted /
  colored e-graphs). Demonstrated on the algebra; the marriage to the reducer is the
  remaining engineering, and it has a literature.
- **Undecidable floor.** It worked because the church-arithmetic rules were supplied.
  For arbitrary programs there is no finite complete ruleset (program equivalence is
  undecidable), so any saturation pass is a semi-procedure — it recognizes what its
  rules span, bounded by fuel.

**Resolution.** The conundrum doesn't dissolve; it relocates — from "recognize semantic
identity (undecidable)" to "how complete is your ruleset, and can you saturate over
terms with binders." The first is provably irreducible, so it becomes *curation*, not a
bug (the bargain egg makes everywhere); the second is real engineering with prior art.
Marrying the recognizers — hash-consing (structural identity; it *is* the e-graph's
e-node table) plus a ruleset + congruence (semantic identity) — yields the unifying
object the whole thread was circling: **structurally + semantically content-addressed
computation with confluent merge**, where "how semantic" is exactly "how complete the
ruleset."

## E-graphs with binders: semantic identity on real terms (`incrdt7.py`)

`incrdt6` reasoned over a hand-supplied symbolic algebra. The gap: those weren't the
real terms. `incrdt7` runs an e-graph **directly on lambda terms with binders**, in de
Bruijn form (so α-equivalence is automatic), with the *general* rules beta and eta —
the known-hard "e-graphs with binders" setting. Findings:

- **α-equivalence is free** — two α-variants share one e-class on insert (de Bruijn).
- **Beta saturation recognizes** `church(6) ≡ mult(church2,church3) ≡ mult(church3,church2)`
  — but at ~reduction cost (≈19 firings vs ≈16 reduction steps). With *general* rules,
  semantic recognition costs about as much as reducing; the cheap recognition in
  `incrdt6` came from *domain* rules. No free lunch from beta alone.
- **Eta finds a non-confluent equality** reduction alone can't: `(λ. f 0) ≡ f`, where
  `(λ. f 0)` is already its own beta-normal form. The e-graph keeps all equal forms
  rather than committing to one — its genuine edge even on the real terms.

The binder problem is handled by de Bruijn for pure lambda; the interaction-calculus
`dup`/`sup` binders are the next extension, and substitution-in-e-graphs (slotted
e-graphs) is the scaling path so beta doesn't blow up the graph.

## Capstone: a replicated computational memory (`compmem.py`)

All the pieces, assembled into the artifact the thread was circling — a content-
addressed store of computations whose merge is a confluent CRDT, with structural
identity free (de Bruijn) and semantic identity layered on. Two agents with
overlapping knowledge merge:

```
MERGE IS A CRDT:  commutative ✓  associative ✓  idempotent ✓
STRUCTURAL IDENTITY (free):  6 raw entries -> 4 after merge (ID + mult(2,3) collapse)
NO PAYING TWICE:  independent eval 30 steps -> merged eval 23 (mult(2,3) once; saved 7)
SEMANTIC IDENTITY:  4 structural entries -> 3 semantic facts (mult(2,3) == mult(3,2))
COORDINATION-FREE:  same facts regardless of merge order ✓
```

The merged object is partially-evaluated *computation*, not data; replicas combine with
no coordination; structurally-shared computation is reduced once, not per agent; and
different derivations of the same value collapse to one fact. The one honest
inefficiency: `mult(3,2)` is reduced even though it equals `mult(2,3)` — they collapse
only *after* reduction, because structural identity doesn't see them as equal.
Recognizing it *before* reducing is the cheap algebra-rule path (`incrdt6`) or the
e-graph (`incrdt7`), turning reduce-then-dedup into dedup-then-reduce. This is the
thread's destination as one running artifact: **structurally (and, with a ruleset,
semantically) content-addressed computation with confluent merge** — a coordination-free
substrate for accumulated agent memory. (Pure lambda; the dup/sup runtime and slotted
e-graphs are the engineering frontier.)

## On the real runtime, with dramatic sharing (`compmem_ic.py`)

`compmem.py` was pure lambda with a toy reducer (no sharing). `compmem_ic.py` runs the
same store-with-confluent-merge on the actual **dup-based interaction-calculus terms**,
evaluated by `ic_float` — and, for the dramatic cases, by the native `ic32` runtime.
Two things become real:

- **Identity over dup-bearing terms.** The store's key is `ic_canon` = de Bruijn over
  *both* lambda and dup binders, plus alpha-renaming of duplication labels (the
  `incrdt4` result). So the same computation derived on two machines with *different
  labels* collapses — demonstrated for `church(6)` and for `mult(2,3)` across label
  namespaces, and the CRDT merge laws hold over these terms.
- **Two levels of sharing compose.** Cross-computation (the store's CRDT dedup — shared
  work reduced once across agents; 98 `ic_float` interactions saved in the demo) and
  within-computation (the runtime's dups; reusing `NOT⁵` twice costs 60 vs 98 spelled
  out, 1.63×).

Wiring the evaluator to the native `ic32` runtime brings the **dramatic optimal
sharing** the Python reducer can't reach: an entry holding *parity of 2²⁴* — value
16,777,216 applications — reduces in **478 interactions**, and because two machines'
differently-labelled derivations of it collapse under `ic_canon`, the merged store
reduces it **once** (478) not twice (956). An entry of astronomical value, stored,
merged coordination-free, and evaluated cheaply — the runtime spine (`ic32`) and the
computational-memory thread, unified.

Honest residual: semantic identity here is still reduce-then-dedup, and an
interaction-rule e-graph *over IC terms* (dup/sup binders inside e-graphs) remains the
open frontier.

## Is the identity layer syntactic or semantic? (`idtest.py`)

A diagnostic answering whether `ic_canon` is secretly semantic or merely syntactic.
Three IC terms with the *same* normal form but different derivations — `church(6)`,
`mult(2,3)`, `mult(3,2)` — canonicalized *before* reduction:

```
NF(A)=NF(B)=NF(C)? True                         (semantically equal: ground truth)
ic_canon before reduction -> 3 distinct keys of 3; collapse? False     => SYNTACTIC
   church(6) @ different labels collapse : True   (alpha + label renaming)
   church(6) vs mult(2,3) collapse       : False  (different derivation)
bounded normalization: mult(2,3) matches church(6) only at k=7 = its FULL reduction
```

So `ic_canon` is a **syntactic congruence** — alpha-equivalence plus duplication-label
renaming — and bounded normalization doesn't rescue it (the terms coincide only at full
reduction). This answers the fork "better canonicalization vs IC-aware e-graphs": the
next step is **IC-aware e-graphs**, since no syntactic canonicalization equates
different derivations of the same value, while `incrdt6`'s ruleset already recognized
`mult(2,3) ≡ church(6)` in 4 firings without reducing. Identity thus has two tiers: a
cheap syntactic congruence (in hand) and **semantic equivalence = program equivalence**
(undecidable; approximable only by a curated ruleset + congruence — the egg bargain).
That semantic tier, not the runtime, is where the project's intellectual weight now sits.

## An IC-aware e-graph: rules + congruence over dup-bearing terms (`iceg.py`)

`idtest` answered the fork — the next step is IC-aware e-graphs, not better
canonicalization. `iceg.py` builds one, in two parts:

- **Identity (the IC-aware part):** e-node keys are de Bruijn over *both* lambda and dup
  binders, plus duplication-label renaming. So `church(6)` built on two machines with
  different label namespaces is ONE e-class with no rules — the syntactic congruence
  `idtest` measured, now living inside the e-graph, dups and all.
- **Semantics:** a church-arithmetic rewrite rule (mult fold) plus congruence recognizes
  `mult(2,3) == church(6)` on the REAL dup-bearing terms, across label namespaces,
  *without reducing*.

```
ground truth: NF(church(6)) == NF(mult(2,3))? True   (mult(2,3) reduces in 16 interactions)
IDENTITY: church(6) across labels share one e-class, no rules: True
SEMANTICS: mult(2,3) vs church(6) -> same class after 1 firing (vs 16 interactions)
four derivations (church(6), mult(2,3), mult(3,2), mult(6,1)): one e-class, 3 firings
soundness (6 probes, cross-checked vs ic_float): merges EXACTLY the NF-equal pairs: True
```

A bug worth recording: `to_db` numbers duplication labels with one counter over the whole
term, so an embedded numeral (`church3` inside `mult(2,3)`) inherits labels offset by
whatever preceded it (`{1,2}`) and fails to match a standalone numeral's key (`{0,1}`).
The de Bruijn *indices* are fine — they're position-independent for closed subterms — it
is purely the global label numbering that breaks the match. The fix is to relabel
*locally* when matching (renumber a subterm's labels from zero), which preserves which
dups share a label (sound) while making the key position-independent.

This lifts `incrdt6`'s cheap recognition and `incrdt7`'s binder handling onto IC terms
with dup/sup binders — the frontier `idtest` named. **Limits:** the rule is the
church-arithmetic algebra (domain-specific); numerals are recognized via a finite
precomputed canonical-key table; and the substitution-heavy interaction rules (full IC
reduction inside the e-graph — the slotted-e-graph problem) are NOT done — the algebra
rule sidesteps substitution. General program equivalence remains undecidable; this buys
exactly what the ruleset spans, the egg bargain, now on interaction-calculus terms.

## Sorting invariants by how far they push into the substrate (`tiers.py`)

If invariants are negative space *and* the expensive layer — each one is something you
*check* — the question is what sits beneath them. The answer is a representation where the
same guarantee is **structural**: true by construction, nothing to check. Every invariant
then sorts into three tiers by how far down it can be pushed:

1. **Structural** — baked into the representation, unviolatable, zero cost.
2. **Reduction-checkable** — not structural, but settled by reducing and inspecting.
3. **Oracle-needed** — behavioral/semantic; no reduction settles it.

`tiers.py` runs three invariants through the sort on the IC substrate:

```
beta (cost):  tier 1 -- church(6) beta=5, mult(2,3) beta=16 (deterministic); and over a
                        content-addressed store beta is a G-Counter (commutative,
                        associative, idempotent; mult(2,3) counted once across replicas)
NF-equality:  tier 2 -- structural keys say church(6) != mult(2,3); reduction says equal.
                        REDUCTION settles it (cost = one reduction); iceg pulls chosen
                        instances to a 1-firing rule, the general case stays tier 2
termination:  tier 3 -- omega unsettled at every budget, indistinguishable from
                        slow-but-halting; reduction is halts-yes only (undecidable)
```

The point is the **representation change** that moves beta to tier 1: it stops being a
predicate asserted after reducing and becomes a count the reduce-loop maintains (no
reduction omits the increment, so conservation is structural) that merges as a counter
keyed by computation-identity (so it is itself a G-Counter CRDT). This is the same move as
the four structural guarantees the IC already gives — idempotence from content-addressing,
conservation from linearity, merge-commutativity from confluence, well-formedness from
typed ports — the CRDT laws plus resource safety, free in the representation rather than
checked. The engineering goal of a *substrate* is to push invariants down a tier; what
remains in the verifier's library is only the invariants that resist it (tiers 2 and 3),
which is why substrate work shrinks the CEGIS/Daikon loop rather than competing with it.

## The tier-1 frontier and its edge (`frontier.py`)

Running the periodic-table invariants — κ routing (Tarjan SCC + min-cut), σ resolution
(dim H¹ of a sheaf), β persistence (across a filtration) — through the tier sort surfaces
a frontier and an edge. `frontier.py` makes three of the findings concrete:

```
sigma -> TIER 1 by construction: an arbitrary sheaf has an H1 gluing obstruction
         (965/1000 random cochains; detecting it is linear algebra = tier 2), but
         differences from a shared potential telescope to zero (0/1000) -- a gluing
         failure is unrepresentable. H1 = 0 by construction IS conflict-freedom, the
         genuine third representation-structural result after beta and the G-Set.
kappa -> the incremental-SCC route is a MAINTAINED INDEX, not structural: the cached
         "on a cycle?" diverges from truth if an update is skipped (cache=False,
         truth=True). The guarantee lives in the maintenance, not the representation.
         Fast (O(1) query) but tier-1.5, with a residual correctness obligation.
delta -> the edge, and the culprit is PROPORTIONALITY x transactions, not time:
         proportional demurrage does not commute with a deposit (135 vs 140); fixed
         demurrage does (147 = 147). Gesell's percentage holding cost therefore cannot
         be a coordination-free currency beside deposits; only a fixed/per-capita one
         stays mergeable. A concrete warning for the v0.5 economic layer.
```

Two flavors of tier-1 separate here: **representation-structural** (β, σ-by-construction,
content-addressing — the violating state is unrepresentable, no code need be correct)
versus **maintained-index** (incremental-SCC — O(1) queries, but the cache can go stale).
Only the first escapes the verifier entirely, so the honest count of structural results is
β, the provenance G-Set, and now σ; κ is a fast path. And the multi-currency thesis gets a
computability-side justification independent of the ecology: β is tier-1/free, κ and σ are
tier-2/computed-from-structure, δ is tier-2 and reintroduces coordination — four invariants
with four merge-and-cost profiles that a single token cannot express.

## A slotted e-graph: free variables as slots, beta inside (`slotted.py`)

`iceg` carried two caveats: a de Bruijn e-node key (which the slotted-e-graph literature
shows breaks sharing for open subterms and blows up under beta) and a finite key table
plus a domain-specific rule standing in for semantic equality. `slotted.py` removes both.
Its e-class identity is the slotted canonical form — bound variables de Bruijn (alpha-free),
free variables positional slots (context-independent), labels renumbered (dup/sup binders
handled) — and beta runs as a rewrite *inside* the e-graph.

```
identity:  alpha-equivalence free; free-var renaming shares ((x y) == (a b) != (x x));
           open subterm S = λy.(x y) is ONE e-class in any context, while the de Bruijn
           key gives it ('i',1) inside λx.S vs ('i',2) inside λx.λz.S -- no sharing. The
           same holds for an IC dup-bearing subterm !&L{a,b}=x;(a b): slotted shares, de
           Bruijn does not. The slotted identity carries the IC binders.
beta:      (λx.x) a, (λx.λy.x) a b, (λx.x y) a, and mult(2,3) all reduce inside the e-graph
           and merge with their normal forms; mult(2,3) == church(6) is recognized by
           ACTUAL reduction -- no key table, no domain rule, and free vars never shift.
```

This brings the slotted-e-graph frontier (Schneider–Koehler–Steuwer, PLDI 2025; Rust lib
`slotted`) onto the IC's identity layer plus beta. **Frontier remaining:** the full
*dynamic* slotted e-graph (slots maintained through e-class merges, congruence modulo
renaming, full equality saturation) is the production library; and the complete IC dup/sup
*interaction* rule-set as slotted rewrites — beyond beta on the lambda subset — is the next
step. What is delivered is the identity layer (open-subterm sharing de Bruijn cannot do,
dup/sup included) and reduction-inside (semantic equality by reducing, not by lookup) —
the two things `iceg` could not do.

## IC interaction rules as slotted rewrites (`slotted_ic.py`)

`slotted.py` ran beta on the lambda fragment inside the slotted e-graph. `slotted_ic.py`
takes the next step on the frontier: the IC *interaction* rules as rewrites over dup/sup-bearing
terms, with the slotted identity, each validated NF-equal to `ic_float`.

```
implemented + validated (8/8 against ic_float, reduced inside a slotted union-find e-graph):
  APP-LAM, APP-SUP, APP-ERA, DUP-SUP annihilate (same label), DUP-SUP commute (different
  labels), DUP-ERA -- six rule types, including the fresh-variable-generating APP-SUP and
  DUP-SUP-commute.
remainder: DUP-LAM (duplicating a lambda) -- the ONE rule that cannot be expressed here.
```

The sharp finding: it is *not* fresh-variable generation that is hard -- APP-SUP and
DUP-SUP-commute both generate fresh variables and validate. The single remaining rule is
DUP-LAM, and for a precise representational reason: the two copies of a duplicated lambda must
share its bound variable through a superposition, which is an interaction-net *wire*. A lexical
rule would need the new binder to capture a variable that capture-avoiding substitution is
obliged to rename away -- so it cannot be written in this representation at all; it needs net
wiring, De Bruijn levels, or explicit substitution. This is exactly why HVM does not use naive
lexical substitution. That one rule, plus the full *dynamic* slotted e-graph (slots through
merges, equality saturation = the `slotted` library), is the remainder.

A debugging note kept in the file: one term first appeared to fail validation, but the cause
was `ic_float`'s pretty-printer naming a fresh binder `a` and capturing a free `a` on re-parse,
not the reducer; free-var names outside `ic_float`'s bound-var namespace fix the round-trip.
The identity layer and a validated subset of the interaction rules are done; the
duplication-of-binders rules are the next step.

## Economic-layer mergeability triage (`econ_triage.py`)

Generalizing `frontier.py`'s delta finding into a test across currency *forms*. A currency is
coordination-free when (1) its state has an order-independent CRDT merge and (2) for a
transacted balance, its update commutes with deposits.

```
additive accumulation (G-Counter)   CRDT-merge yes   commutes with deposit yes   -> FREE
max- / min-register                 CRDT-merge yes   commutes with deposit no
grow-only set (G-Set)               CRDT-merge yes   n/a
proportional / decay (scalar *)     CRDT-merge no    commutes with deposit no     -> HARD
```

So beta (additive) is a coordination-free currency and delta (Gesell's proportional demurrage)
is coordination-hard -- no order-independent value merge, and it breaks transacted balances.
**Design rule for the v0.5 economic layer:** a holding cost must be ADDITIVE / per-capita (a
fixed per-epoch drain keyed idempotently = a PN-counter), not PROPORTIONAL, to remain a
coordination-free currency. The multi-currency design is sound; the *form* of each currency is
the constraint. (Placing all seven v0.5 invariants precisely needs their exact update rules;
the form test is the tool.)

## The provenance G-Set, and the inter-agent sigma scope (`provenance.py`)

Two results. First, a third representation-structural tier-1 invariant alongside beta (a
counter) and sigma-by-construction: derivation facts `(term, rule, premises)` form a grow-only
set merged by union -- the canonical CRDT (commutative, associative, idempotent). A duplicate
provenance fact is unstorable (set membership); two *different* derivations of the same term are
kept distinct. The merge records *how* each result was reached, coordination-free, no
double-counting.

Second, the honest scope of `frontier.py`'s sigma. Sigma-resolution is tier-1 for *replicas*:
the confluent merge reconciles them to a shared value, so the gluing obstruction H^1 = 0 by
construction. But two independent *agents* can hold views that genuinely disagree -- overlap
claims of +2 around a 3-cycle give H^1 = 6 != 0, no global section -- a real conflict the
substrate *measures* (computing the cycle sum, tier-2) rather than dissolving. Conflict-freedom
is a property the merge *gives* replicas, not one it can *impose* on disagreeing agents. That is
the non-overclaimed statement.

## The capstone: merge of confluent computation is a CvRDT by construction (`semilattice.py`)

The whole IN-CRDT thread asked, in effect, whether merge = union + reduce is a CRDT.
`semilattice.py` answers it precisely by *instantiating* Shapiro, Preguiça, Baquero & Zawirski
(2011) on the computation object — not by proving a new CRDT theorem. State = a grow-only set of
computations content-addressed by **normal form**; merge = union.

```
verified:
  join-semilattice  : union idempotent/commutative/associative, = least upper bound under
                      subset (2000 random instances). merge = join.
  semantic dedup    : cid(mult(2,3)) == cid(church(6)) == cid(add(3,3)) -- the content-id IS
                      the normal form, so differently-derived equal computations collapse.
  inflationary      : add(c) and reduce(c) satisfy s <= update(s) -- reduction adds a normal
                      form, never removes one. monotone by construction.
  strong eventual   : 200 trials, 3 replicas, shuffled update + merge orders, all converge to
    consistency       the identical state = the join (7 updates collapse to 4 computations).
```

**Theorem (Shapiro instantiated).** A grow-only set of computations content-addressed by normal
form, merged by union, is a join-semilattice with inflationary updates, hence a CvRDT, hence
strongly eventually consistent; and because the content-id is the normal form, convergence
performs *semantic* deduplication of computation.

**Corollaries.** Every `incrdt*.py` / `compmem*.py` experiment is an instance of this
join-semilattice; `dist_ic.py`'s coordination-free reduction is its strong eventual consistency;
`iceg` / `slotted` / `slotted_ic` refine the content-id from structural to semantic and extend
the same monotone structure to partial computation by making the *equalities* a grow-only set
(merges are never undone — itself a join-semilattice).

**Scope (honest).** The novelty is the *object* and the semantic dedup it yields, not the CRDT
theorem (which is Shapiro's). For non-normalizing terms the content-id falls back to a structural
key (tier-1 identity only); semantic identity holds exactly where reduction terminates — the
`tiers.py` boundary, restated as a lattice.

## When is identity recognizable? The reduction budget of computational identity (`dedup_reduce.py`)

External review asked a sharp question: can two computations be recognized as identical *before*
either is normalized — "dedup-then-reduce" instead of "reduce-then-dedup"? `dedup_reduce.py`
measures the answer over pure-lambda church arithmetic, separating three regimes:

```
(0) STRUCTURAL identity (alpha/label canonical): free, zero reduction -- but recognizes only
    alpha/label-equal terms. mult(2,3) is NOT church(6) structurally. (= compmem_ic tier-1.)
(R) SEMANTIC identity: recognized at the FIRST form the two reduction paths SHARE. measured:
    sometimes an INTERMEDIATE form -- mult(2,3) and add(3,3) meet at step 3, before their
    normal form at 6-7 -- and sometimes only the normal form (when one side is already normal).
    recognition costs <= normalization but is never zero; the convergence point is not
    knowable a priori.
(M) COMPUTATIONAL MEMORY: processing a corpus while content-addressing every intermediate form
    and memoizing normal forms lets a new computation SHORT-CIRCUIT on reaching a known form.
    measured: ~18% fewer reduction steps and 10 computations -> 5 distinct results.
```

**Finding.** The *strong* inversion ("identity before reduction") fails — only structural
identity is free. The *weak* one ("identity before FULL normalization, when reduction paths
converge") holds for some pairs, and a content-addressed computational memory operationalizes it
as dedup-DURING-reduce: short-circuiting at known convergence points plus semantic dedup of
results. This is the precise, load-bearing-layer-explicit reading of "merge of confluent
computation": canonicalize → content-address → (reduce, sharing the work) → dedup. The win is
not avoiding reduction but *sharing and remembering* it — and, where paths converge early,
stopping sooner.

## Is early convergence common? A distribution, not a witness (`convergence_map.py`)

`dedup_reduce.py` found a *witness* — `mult(2,3)` and `add(3,3)` become identical before
normalization. External review reframed this as "deduplicating trajectories, not results" and
asked the right next question: witness or distribution? `convergence_map.py` measures it over 578
equivalent church-arithmetic pairs (grouped by value), reducing each pair in lockstep and
recording the first common form.

```
RESULT -- WORLD 1 (early convergence is RARE):
  6% of equivalent pairs converge before the normal form (8% under call-by-value -- robust to
    reduction order); 94% share a form only at the normal form.
  the early pairs are shallow (mean depth-ratio 0.65); the DEEPEST (ratio 0.43) are one
    algebraic-coincidence family, add(k,k) == mul(2,k): both reduce to "(church-k applied to f)
    applied TWICE to x", so the identity k+k = 2*k surfaces as a shared reduction intermediate.
  generic equivalent pairs (church(v) vs add(a,b) vs succ-chains) share NO intermediate.
  sanity: non-equivalent (different-value) pairs never share a form.
```

**Implication.** "Deduplicating trajectories" is not a general phenomenon here — it is a narrow
algebraic coincidence. The dynamic-e-graph path is therefore *not* justified by this evidence:
trajectories rarely cross before the normal form, so a cross-computation e-graph has little
pre-NF structure to share, and the ~18% corpus memoization (`dedup_reduce.py`) is near the
ceiling. The substrate's value is semantic dedup of *results* at the normal form, not trajectories.

**Honest scope.** Measured on church arithmetic under beta/CBV. IC's optimal sharing and other
term families are unmeasured; arithmetic is a structured domain, so World 1 here is suggestive
(not proof) that generic computation is no denser. This is the cheap experiment doing its job —
deflating an exciting narrative before paying for the machinery it would have required.

## The IC convergence closure test: a blocked measurement and a circularity (`ic_convergence.py`)

`convergence_map.py` established World 1 under beta. The remaining decision-relevant question
(raised in review): does IC's optimal sharing — dup + superposition — create convergence
structure that beta hides? `ic_convergence.py` attempted the closure test: church arithmetic
encoded in IC with explicit linear dups and fresh distinct labels (validated — 42/42 encodings
reduce to `s^value`), trajectories captured by running `ic_float` with an opt-in interaction
budget, convergence measured with a coarse (over-counting, upper-bound) canon and a finer one.

**The measurement failed its sanity check, and is reported as such — not as a verdict.**
Different-value computations — which have different normal forms and, reduction being
deterministic, cannot share a state — showed spurious shared forms (21 coarse, 4 fine), and the
two canons disagreed 55% vs 2%. Neither number is trustworthy.

Two genuine reasons, both worth recording:
1. Budget-limited `normal()` does not yield faithful IC *states*; it yields order-dependent
   partial mixtures, not the net-state-after-k-interactions a trajectory needs.
2. Canonicalizing a partial IC net with floating dups (open subterms, shared dup nodes, label
   namespaces) is the open-term-identity / slotted-e-graph problem — the same one `slotted_ic.py`
   hit at DUP-LAM.

**The circularity is the real finding:** to measure rigorously whether a dynamic slotted e-graph
is worth building, you need e-graph-grade canonical identity for partial IC states — the very
thing you are deciding whether to build. So the IC convergence question is not cleanly answerable
with current tools.

**Defensible status.** Beta is World 1 (clean, stands). IC is technically open, but the beta
result plus the fact that IC states carry *more* distinguishing structure (so false-positive-free
coincidence is rarer, not more common) both point to World 1. Either way the e-graph build is not
justified — and, more decisively, can't even be assessed without first building the identity
machinery in question. The substrate's demonstrated value remains semantic dedup of *results* at
the normal form plus modest memoization. `ic_convergence.py` is kept as a documented
negative/blocked result.

## What is and isn't shown

- **Shown:** confluence ⇒ commutativity + associativity (incl. across incremental
  merges); content-addressing ⇒ operational idempotence (all four metrics); sharing
  survives reduction with an exact cost law; automatic detection + sharing of one
  repeated closed sub-term is sound and cheaper; merge can become inference.
- **Not shown:** sharing of *open* sub-terms (the full-laziness restriction); sharing
  *all* repeated sub-terms (only the most impactful one, per run — extensible by
  standard CSE); soundness as a *theorem* rather than a guarded measurement; and,
  crucially, the **label-canonicalization** that a real cross-replica merge needs.
  Small scale throughout (a handful of derivations, Church ≤ 6).
