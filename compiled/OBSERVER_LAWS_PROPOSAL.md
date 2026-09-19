> **HELD 2026-09-19, and the reason is a fact that arrived after this page was written.**
>
> Travis was asked to rule §5 and delegated it: *"look at our thesis and values plus direction and go from there."*
> Taken under that delegation, by Claude Opus 5, and recorded here so it can be overturned in one line.
>
> **§5(1) prices "no" as "the laws stay as emitter transcriptions and the battery stays the gate; nothing is lost but
> the generator". That price is no longer what it says.** T7 landed the same day, after this page
> (`TRVM` `40341ed`, `compiled/laws.py` + `laws_gate.py`, README §2f): the WRL step laws are already stated ONCE and
> the four emitters already render from that one table, with every emitted byte held by a gate and the battery's
> mutants derived from it rather than hand-typed. **The generator this proposal offers as its payoff has been built,
> one layer down, without adding a construct to WRL.**
>
> What the observer layer would add *beyond* T7 is a different and larger thing: laws discharged statically at the
> seal and enforced at run time as a residual Door — moving a law from "something the four backends agree about" to
> "something the world declares and the seal proves". That is worth having. It has no measured need behind it yet,
> and this stack's standing discipline (`FOUNDATION_LANE.md` §3ba: *generate from ONE law source per layer, never a
> general DSL*) is that a rung opens on a measured need nothing lower can meet.
>
> **What would unblock it, stated so it can be met rather than argued:** one named case where a WRL world needs a law
> enforced *at run time* that the battery cannot catch offline — i.e. a world admitted by the fold whose law can still
> be violated in production by an input the battery's scenarios do not generate. The floor cannot supply it: §3ba(a)
> measured that `cd-kernellet`'s `step` evaluates no WRL law at all. One such case and this page is ruled on its
> merits instead of its cost.
>
> §5(2) and §5(3) are not decided here; they only matter after §5(1).

# A law is a door that must stay shut — WRL observers as the law layer of the compiled backend

**2026-09-19. PROPOSAL FOR A RULING, not a build.** Nothing here adds a runtime construct, a
surface spelling, a role, an edge kind or a profile field; nothing in `forge/` or `compiled/` is
changed by this document. It asks one question of the owner of the WRL ladder (the standing order
of this lane is *add NO new runtime constructs unless GPT explicitly rules it*), and it says what
would follow either answer. Every number in it names the record it comes from.

## 0. Why now

The compiled backend (`README.md` §2–§2e) is admitted per world by *translation validation*: the
emitted C step is folded beside the calculus over the same scenarios and the films and states must
agree (53 pairs / 1,007 epochs at the last widening). Its laws — clock fire/advance; wire `nxt'` =
source hot; a relay's hot is its NXT; door and relay take their input wire's `nxt`; COMMIT fault
reset → COMMIT rotor → REACT only if the input fires; sticky fault; the Hamilton MAC with exact
products, one toward-zero shift and one saturation — exist today as **four hand transcriptions**
(`emit_c.py`, `emit_c2.py`, `emit_bend.py`, `emit_bend2.py`, ~1,190 lines) of Forge's
`compile_step_v6` and `binlib.golden_rot_forge`, and the battery's mutants exist to catch
transcription drift between those copies: `react-before-commit`, `reset-ignored`, `floor-shift`,
`no-saturation`, `wire-cur-stale`, `relay-hot-from-cur`, `once-no-latch`,
`onehot-phase-off-by-one`, `binary-phase-off-by-one`, `fault-not-sticky`, `react-without-fire`,
plus the widening's `narrow-product-i64`, `film-without-mailboxes`, `script-without-routes`,
`sx-subtrahend-i64` (`battery.py` `MUTANTS`, `WIDENING_MUTANTS`).

Every one of those mutants is **a law with one clause flipped**, expressed as a string edit to an
emitter. That is the observation this proposal rests on: the laws are already stated fifteen
times as *what must not happen*; they are just stated in Python string replacements against C
text, once per emitter, instead of once in the language whose worlds they govern.

Separately, the floor investigation of 2026-09-19 (`computedriven/docs/floor-attribution.md`)
established that the ComputeDriven floor evaluates **none** of these laws — its checks are locus,
mark, generation, carrier, fence and evidence. So the WRL laws have exactly one enforcement site
today: the compiled backend's admission battery. Wherever the law layer goes, it does not go into
the floor.

## 1. The precedent, and why it fits WRL and not a general DSL

The synchronous-dataflow languages answered this question thirty years ago and the answer held.
In Lustre a *property* is an **observer**: an ordinary node in the same language whose output is
a boolean `ok` stream. The same compiler that makes the program makes the monitor; a model checker
(Lesar, then Kind 2, whose contract language CoCoSpec is Lustre with `assume`/`guarantee` blocks)
decides the property statically over the finite state; and at run time the observer is just more
of the same generated code. Recent work compiles temporal-logic operators into observers that are
both runtime monitors and statically checkable in Kind 2. The reason it works is structural:
Lustre is clocked, finite-state and not Turing-complete — which are WRL's ideals exactly (five
roles, two edges, one signal wire per input, sets not lists, identity is a hash).

The reason **not** to reach for a general law DSL (Datalog, a policy language, a first-order
fragment) is the same reason WRL cannot be the JS/CSS layer: the shape of the thing. A WRL law is
a property of a clocked circuit — "this pose never saturates", "this door never fires before that
commit" — and a circuit language already has the primitive that expresses a property of a
circuit: **a sink that must never be driven**. The succession and authority laws of the floor are
a different shape (quantified, relational, open-world) and belong to a decidable relational
fragment (Ivy/EPR, Cedar); that is a separate proposal in a separate repository and is not
mixed into this one.

## 2. The construct, sketched in the ideals and NOT in the surface

> **A law is a Door that must stay shut.** A world may declare a Door as a law; a probe edge
> carries a predicate over the state it watches into that Door; the seal proves, over the
> world's finite state space and the scenario bounds, that the Door's input is never hot — and
> where it cannot, the Door stays wired and its firing is a fault of the world, not an event in it.

Sketch, **not writable today**, deliberately in today's grammar so its two gaps are visible:

```
profile forge.world.core.v1
[pulser:p0](every 2){sig_out}
[spinner:sp](w=16, n=8, rotor=quarter_turn_z){sig_in, socket}
[orb:ob]{pose}
[door:L1_no_saturation](law){sig_in}                 ; a law is a door that must stay shut
[pulser:p0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]
[spinner:sp] --probe(|pose| < 32768)--> [L1_no_saturation]   ; gap 1: a probe edge; gap 2: a predicate
```

The two gaps are the two capabilities the ladder already names (`WRL/docs/spec/README.md`, "What
is missing", rung 5): a **probe edge** — a third edge kind whose destination is a law Door and whose
source may be any object, since today a Spinner's only out is `socket` and a Door accepts `sig_in`
from Pulser/Relay alone — and **`expression-notation` restricted to observers**: predicates over
the watched object's state (comparisons, boolean connectives, the width-bounded integers the
spinner already has), with no assignment, no recursion, no new state. Nothing else on rung 5
(`behaviours`, `collections`, `generics-traits`, `resources`) is asked for; `numerics` is asked
for only as far as the predicate needs the lane width the object already declares.

What is **not** proposed: a law that computes; a law that mutates; a law with memory beyond what
a Door already has (fired / not fired); a law over more than one world; a law in a different
language from the world it governs.

## 3. What each half of the enforcement becomes

**Static discharge (the seal).** A sealed world is finite: its state is the slot vector the
compiler already lays out (`compiler.state_layout`; chain120 is 485 signal bits → 17 words,
README §2d), its inputs are the scenario's bounded claims. A law Door's input is a boolean over
that state. Whether it can ever be hot is a reachability question over a finite transition system
— the question Kind 2 answers for Lustre. Where the seal can answer it, the law is **discharged**:
the compiled step carries no check for it, the certificate names the law id as proven, and the
mutant for it becomes unnecessary because the property, not the transcription, is what was
checked. Where the seal cannot (the scenario space is too large, the predicate is over a value
the seal does not bound), the law is **residual**.

**Residual monitor (the step).** A residual law Door is compiled like any Door — one bit of
state, set when its input is hot — and read back like any Door's state in the film. A law Door
that fires is a fault of the world at that epoch; the receipt says which law and when. The cost is
what a Door costs today (README §2: a pulser-relay world's whole step is ~1.4 ns), so the residual
is not the reason to avoid the construct.

**The battery becomes the generator's suite, not each world's gate.** Today `battery.py` proves,
per world, that four hand transcriptions agree with the calculus; its mutants are transcription
flips. With laws as observers on the world, a mutant is **an observer with one clause flipped**
(`|pose| < 32768` → `|pose| <= 32768` is `no-saturation`; "COMMIT then REACT" → "REACT then COMMIT"
is `react-before-commit`), generated from the law rather than typed against each emitter's text,
and the acceptance is one sentence: *every law Door stays shut on the true world; at least one
opens on each mutant.* The calculus twin stays as the oracle of the fold itself; the emitters stop
being places where a law can drift because the law is no longer written in them.

## 4. Identity: the one WRL discipline that applies to every law, whatever surface it gets

A law is a sealed artifact or it is prose. Forge already has the mechanism: `SealedArtifact`
(`forge/wrl_canonical.py`), immutable under `WRL_SEALED_IMMUTABLE`, with an identity that is a hash
of canonical content and invariant to order, presentation and formatting; and the compiled step's
own identity `cbknd2-` = sha256(sem + profile + C source) (`emit_c2.py`). With laws in the world,
the law ids ride in the `sem-` id by construction — a world with a different law is a different
world — and the certificate the executor kind proposal asks for (`wek/b2/trvm/COMPILED_EXECUTOR_PROPOSAL.md`)
names them without a new field. That gives, for free, what box-and-box's reflexive rung
(`AmpersandBoxDesign/box-and-box/reflexive.mjs`) calls **entrenchment**: a law can be added or
strengthened under the same `sem-`-changing rule as any edit, and nothing can weaken one silently,
because the identity of the thing that was admitted is the identity of its laws.

## 5. The ruling asked for

1. **May the WRL ladder take a probe edge and observer-only expression-notation ahead of the rest of
   rung 5?** — as the *first* use of the expression rung, restricted to law Doors, with no
   behaviours. If yes, the surface grammar gains one edge kind and one predicate form; the seal
   gains one static question; the compiled backend gains one Door kind and loses fifteen hand-typed
   mutants over time. If no, the laws stay as emitter transcriptions and the battery stays the
   gate; nothing is lost but the generator.
2. **Is a law Door's firing a fault of the world (sticky, in the film) or a refusal of the epoch?**
   The compiled backend already has a sticky fault law; the proposal's default is the former, so
   that a residual law reads back exactly like any other Door and the film oracle needs no change.
3. **Which body owns discharge?** The seal (Forge, at lowering) is the proposal's default — it is
   the place that already knows the state layout and refuses malformed worlds by typed `WRL_*`
   code — with the compiled backend consuming a per-law verdict. The alternative, discharge in the
   battery, would keep the fold as the only oracle and is the smaller change.

No code is written until one of these is answered. The succession-law generator for the floor
(the other half of the same idea, in `computedriven/`) does not wait on this ruling and is not
governed by it.

## 6. Reading

Kind 2 and CoCoSpec (assume/guarantee contracts in Lustre); "Synchronous observers revisited for
runtime verification of Lustre using STL" (2026), which compiles temporal operators to observers
that are both monitors and Kind 2 inputs; Vélus (a Coq-verified Lustre compiler, the once-and-for-all
alternative to translation validation); Erlingsson & Schneider, inlined reference monitors (the
policy as an automaton woven into the target — what a residual law Door is); Cedar (a decidable,
Lean-verified authorization language — the *other* shape of law, for the floor, not for WRL).
