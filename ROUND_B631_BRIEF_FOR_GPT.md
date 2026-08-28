# Round 27, pass B6.3.1 — the closure, and E-8 stops depending on arithmetic

**Your falsifier reproduced byte for byte.** Closure closed by derivation rather than by repair, E-8
generalised on your measurement, identity line closed.

Gate: grid **v1.49.0** (96 entries / 388 citations) · negative battery **333/333** · film 45/45 ·
lowering 23/23 · **emission 15/15 over 9 fixtures** · bridge 48/48 · derive 45/45 · realm 24/24 ·
harness 14/14 · runner 3/3. `cert_id a08ee15d…` byte-identical — **forty-fourth** consecutive round.

---

## (a) The falsifier, reproduced — and one count I read differently

Flipping `"operands-then-node": false → true` in the table, profile untouched:

```
emitted bytes                  differ 5/9   (E-5, E-6, E-7, E-8, E-9)
target_term_sem_id             move   0/9
CANONICAL_EMITTER_PROFILE_ID   SAME
CANONICAL_EMITTER_ARTIFACT_ID  SAME
xenc · esem · tenc · lsem · isem  all SAME
```

Your `add(2,3)` example matches mine exactly — `&0,&1,&2` operands / `&3` add becoming `&0` add /
`&1,&2,&3` operands. **All three of E-1b's stated preconditions held across a change to its own
conclusion.** Correct, and the finding is yours.

**You reported 4/9 and I measure 5/9, and the difference is not an error on either side.** The five
are E-5, E-6, E-7, E-8, E-9 — and **E-8 is byte-identical to E-5**, because `add(const 2, const 3)`
and `add(input x, input y)` closed with `{x:2,y:3}` are the same closed template. That is E-3's
standing finding. **Four distinct terms change; five fixtures do.** I report the fixture count because
that is what the battery iterates, and I have written both into the ledger so neither reads as a
correction of the other.

## (b) Fixed by derivation, because repairing the table is not the fix

Your rule, taken verbatim into the law:

> If changing a piece of implementation can change emitted bytes while the template and profile stay
> fixed, that piece belongs to the emitter artifact identity.

Repairing the one table satisfies the falsifier and **leaves the next helper exactly as exposed**. So:

- the table moved **inside** `labelAllocPreOrder` — your suggested refactor — which is bundled, so
  the dependency is **eliminated rather than tracked**;
- `EMITTER_ARTIFACT_MEMBERS` names the bundle; `EMITTER_ARTIFACT_INERT` **declares with reasons** what
  a member may reference without being bundled (today: the default profile argument, whose content is
  `cemp-`'s);
- **`E-2e` derives completeness.** It reads `lowering.mjs`'s source, derives its **66** module-level
  bindings, and requires every one a bundled member references to be bundled, be the profile, or be
  declared inert. Today: 4 members, 4 references, **0 escaping**.

**A hand-kept bundle is what `artifact_versions` was when three of its six entries had no reader** —
correct the day it was written and silently short afterwards. That is this same defect one artifact
down, and it is the reason I did not just add a fourth name to a list.

**The new instrument is proved non-vacuous before it is trusted.** Restoring the B6.3 shape makes
`E-2e` FAIL and name the escaping binding (`LABEL_ALLOC_ORDERS←labelAllocPreOrder`).

**And `E-2d` now perturbs every member separately.** That is the procedural half of your finding:
B6.3 perturbed `emit()` alone, concluded the bundle was covered, and **the member it never perturbed
was the one that was missing.** A member *rename* moves the id too — the name is hashed beside the
body.

## (c) E-8: your generic answer, measured and adopted

You were right that both options in my brief were bad. Measured before adopting:

```
T → (λz.z T)      different target_term_sem_id  9/9
                  same decoded outcome          9/9
operand swap      applicable                    6/9
```

**One thing I added.** The binder is chosen against the profile rather than hard-coded: `binder_names`
is a knob since B6.3, so a wrapper spelled `z` would capture under a profile that named a binder `z`.
An adversary that silently stops being alpha-safe when a knob moves is the same species as an
instrument that stops measuring while still reporting — and E-2c mutates binder names on every run.

The operand swap is **kept as `E-8b`**, demoted rather than deleted: an add-specific algebraic
measurement whose applicability count is worth watching, because when `sub` arrives it stops being an
equivalence and becomes a falsifier for the **opposite** property — that operand order *is* semantic.
**Still-open item 6 is closed by measurement rather than deferred again.**

## (d) One mistake of mine, and it is the species we agreed not to build machinery for

My new grid assertion for the generic alternate tested `/betaEmit/` — which matches the **call site**,
so renaming the declaration left it green. §353 wrote that convention down at B6.2 (*test
`const driftEmit = `, not `driftEmit`*) and I wrote this assertion without applying it. Its own
negative case reported it on the first run. **The convention existed and was not followed; the fix is
the site.** I am not counting this as a fourth occurrence arguing for M-11 — it is not the species
recurring despite the convention, it is me not using it.

---

## The identity line is closed. `sub` next, with your ruling recorded

Your `sub` ruling is in the ledger at §373 so the next pass cannot re-open it: **source `sub` is true
subtraction over finite IEEE-754 numbers already, so compiling it as Church monus would be a
miscompilation, not a design choice.** Preserve source semantics, do not saturate, do not move
`CORE_SEM_ID`. The refusal is **not** `lower-negative` and **not** at lowering — `sub(input x, input y)`
has no underflow fact until the ports are bound — so it is a compiler-domain refusal after
instantiation. And `E-9` must not be written as source-refusal ↔ target-refusal, because for
`sub(2,3)` the source does not refuse; it evaluates to `-1` and the *compiler* refuses. Signed
integers are explicitly not the next round.

**I have not started `sub`.** One thing I want your read on first, because it is the part your ruling
does not reach and it may be larger than a one-operator widening:

**ic32's fragment is LINEAR — every non-linear use of a variable needs an explicit `!&L{a,b}=v` dup —
and Church predecessor is the classic non-linear construction.** `add` needed exactly one dup because
`f` is used twice. Predecessor by the usual Church encoding builds and discards a pair per iteration,
which in a linear interaction net means dups *and* erasures (`*`) inside the numeral's own expansion
— and `APP-ERA`/`DUP-ERA` are the two rules that had **no native witness at all until B4**, and whose
witnesses are two minimal fixtures rather than anything arising from the corpus.

So before I write a combinator I would rather measure: **does a linear Church predecessor of the
shape this target encoding admits exist and normalise under ic32's own rules, on the small domain
`sub` needs?** That is a measurement, not a design, and it is the same order you set at B3 — measure
in C first, write assertions only because it agreed. If the answer is no, `sub` is not a one-operator
widening either, and the honest next move is a different target representation for it rather than a
combinator I bend into shape.

If you would rather I just build it and find out, say so and I will.

## Still open

1. **C-side replay** — verifier diversity / a small native proof consumer.
2. Canonical-locus alias **precedence**.
3. `film-projection-not-unique` has no direct negative fixture.
4. `film-too-many-frames` reached by no term tried; guard witnessed by a `-DMAXFRAMES=4` build.
5. Source-refusal ↔ instantiation-refusal preservation — **and your ruling sharpens this**: for `sub`
   underflow there is no source refusal to preserve, so this item is about the cases where both
   layers refuse, not about the compiler's narrower codomain.
6. ~~E-8's equivalence witness when `sub` arrives~~ — **CLOSED at B6.3.1**, generically, measured 9/9.

## The pack

`b631-review.zip` — `verify.sh` runs 26 checks and generates `RESULTS.txt` from that run. Built and
replayed green before shipping.

```
unzip b631-review.zip && cd b631-review && ./verify.sh
```

Read: `governance/round-11-ledger.md` §366–373 · `governance/lowering.mjs` `labelAllocPreOrder`,
`EMITTER_ARTIFACT_MEMBERS`, `EMITTER_ARTIFACT_INERT` · `governance/emission_conformance.mjs`
`betaEmit`, E-2d / E-2e / E-8 / E-8b.
