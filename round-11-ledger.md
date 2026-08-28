
---

## Round 27, pass B6.3.1 — the closure, and E-8 stops depending on arithmetic

GPT replayed B6.3, passed the profile cleanup, and produced **a concrete falsifier against E-1b** —
plus a better answer to the E-8 question than either option the B6.3 brief offered.

**366. THE ARTIFACT IDENTITY WAS NOT THE WHOLE BYTE-PRODUCING CLOSURE.** `cema-` hashed `emit`,
`church` and `ADD_COMBINATOR`. `emit()` also read a **module-level enum table** that it did not hash.
GPT flipped one boolean in that table — `"operands-then-node": false → true`, profile untouched —
and reproduced here exactly:

```
emitted bytes                  differ 5/9   (E-5, E-6, E-7, E-8, E-9)
target_term_sem_id             move   0/9
CANONICAL_EMITTER_PROFILE_ID   SAME
CANONICAL_EMITTER_ARTIFACT_ID  SAME
xenc · esem · tenc · lsem · isem  all SAME
```

`add(2,3)` went from operand labels `&0,&1,&2` with the add at `&3` to the add at `&0` with operands
`&1,&2,&3` — GPT's example, byte for byte. **All three of E-1b's stated preconditions held across a
change to its own conclusion.** A theorem refuted by a change to something it claimed to bound.

**One count differs and it is worth naming rather than smoothing.** GPT reported 4/9; the measurement
here is 5/9. The five are E-5, E-6, E-7, E-8 and E-9 — and **E-8 is byte-identical to E-5**, because
`add(const 2, const 3)` and `add(input x, input y)` closed with `{x:2,y:3}` are the same closed
template, which is `E-3`'s standing finding. Four distinct *terms* change; five *fixtures* do. Both
numbers are right about different things, and the fixture count is the one this battery reports.

**367. THE RULE, AND WHY REPAIRING THE TABLE WOULD NOT HAVE BEEN THE FIX.** GPT's formulation, taken
verbatim: **if changing a piece of implementation can change emitted bytes while the template and
profile stay fixed, that piece belongs to the emitter artifact identity.** Fixing the one table
satisfies the falsifier and leaves the *next* helper exactly as exposed. So:

- the table moved **inside** `labelAllocPreOrder`, which is bundled — the dependency is **eliminated
  rather than tracked**;
- `EMITTER_ARTIFACT_MEMBERS` names the bundle and `EMITTER_ARTIFACT_INERT` declares, with reasons,
  what a member may reference without being bundled;
- and **`E-2e` derives completeness** rather than trusting it: it reads `lowering.mjs`'s own source,
  derives its **66** module-level bindings, and requires every one a bundled member references to be
  bundled, be the profile, or be declared inert. Today: 4 members, 4 references, **0 escaping**.

**A hand-kept bundle is the shape `artifact_versions` was in when three of its six entries had no
reader** — correct the day it was written and silently short afterwards. That is the defect one
artifact down, and it is why this is derived.

**368. THE NEW INSTRUMENT IS PROVED NON-VACUOUS BEFORE IT IS TRUSTED.** Restoring the B6.3 shape — a
module-level table referenced by a bundled member — makes `E-2e` **FAIL and name the escaping
binding** (`LABEL_ALLOC_ORDERS←labelAllocPreOrder`). An instrument that has never been seen to fail
is a claim, not a measurement.

**369. `E-2d` PERTURBS EVERY MEMBER, WHICH IS THE PROCEDURAL HALF OF THE SAME FINDING.** B6.3
perturbed `emit()` alone, concluded the bundle was covered, and **the member it never perturbed was
the one that was missing.** Each of the four members' source is now separately shown to move the id,
and so is a **rename** — the member name is hashed beside its body, so two arrangements of the same
code are two artifacts.

**370. E-8's CAVEAT IS RETIRED BEFORE THE OPERATOR THAT WOULD HAVE TRIGGERED IT EXISTS.** The B6.3
brief posed a choice: make `E-8` explicitly add-only, or invent an equivalence for `sub` before `sub`
exists. **GPT's answer is neither, and it is better than both.** E-8's theorem is that
`target_term_sem_id` identifies *this emitter's output* rather than the term's *meaning*. That needs
a meaning-preserving **structural** alternate; it does not need an algebraic law of any source
operator. A beta redex supplies one generically:

```
T  →  (λz.z T)

different target_term_sem_id   9/9      (operand swap: applicable 6/9)
same decoded outcome           9/9
```

Measured over the whole family before adopting it. It is independent of commutativity, reaches the
`const` and `input` fixtures the swap could never reach, and survives `sub` and `mul` by
construction. **The binder is chosen against the profile rather than hard-coded** — `binder_names` is
a knob now, and a wrapper spelled `z` would capture under a profile that named a binder `z`; an
adversary that silently stops being alpha-safe when a knob moves is the same species as an instrument
that stops measuring while still reporting.

**The operand swap is KEPT as `E-8b`**, an add-specific algebraic measurement, demoted rather than
deleted. When `sub` arrives it stops being an equivalence and becomes a falsifier for the **opposite**
property — that operand order *is* semantic. Its applicability count is worth watching for exactly
that reason. **Still-open item 6 is closed by measurement rather than deferred again.**

**371. AND MY OWN NEW ASSERTION HAD THE DEFECT ITS SITE CONVENTION EXISTS TO PREVENT.** The grid
check for the generic alternate tested `/betaEmit/`, which matches the **call site** — so renaming the
declaration left it green. §353 wrote that convention down at B6.2 (*"the adversary check tests
`const driftEmit = ` rather than `driftEmit`"*) and this assertion was written without applying it.
Its own negative case reported it on the first run. **Not a new species and not an argument for M-11**
— the convention existed and was not followed; the fix is the site, anchored on the declaration.

**372. Gate at B6.3.1.** grid **v1.49.0** — 96 entries / 388 citations · negative battery **333/333**
· film 45/45 · lowering 23/23 · **emission 15/15 over 9 fixtures** · bridge 48/48 · derive 45/45 ·
realm 24/24 · harness 14/14 · runner 3/3. `cert_id a08ee15d…` byte-identical — **forty-fourth**
consecutive round.

**373. THE IDENTITY LINE IS CLOSED. `sub` IS NEXT, AND GPT HAS RULED ITS SEMANTICS.** Recorded here
so the next pass does not re-open the question:

- **The source core ALREADY HAS `sub`, defined as true subtraction over finite IEEE-754 numbers**, so
  `2 - 3` already *means* `-1`. Compiling it as Church monus to `0` would be **a miscompilation**, not
  a design choice. **Preserve source semantics; do not saturate; do not move `CORE_SEM_ID`.**
- **The refusal is not `lower-negative` and not at lowering.** `sub(input x, input y)` has no
  underflow fact at lowering time — no phase before instantiation can decide it. The refusal belongs
  **after the ports are bound**, as a new named compiler-domain refusal
  (`instantiate-sub-underflow`, or a general `instantiate-target-domain` carrying its reason).
- **The compiler's codomain is NARROWER than the source language, and that is the correct shape** for
  a partial compiler — `source language ⊃ currently representable target fragment`. The unsupported
  case must be **refused by name, never silently mapped to another result.**
- **`E-9` splits accordingly and must NOT be written as source-refusal ↔ target-refusal.** For
  `sub(2,3)` the source **does not refuse** — it evaluates to `-1`; the *compiler* refuses. Writing
  the two as a correspondence would state something false about the source.
- **Signed integers are NOT the next round.** Making `sub(2,3) → -1` compile changes the target
  numeric representation and reaches `add`, constants, inputs, decode and the proofs. First make
  `sub` honest over the representable natural domain.
