# Bend's `LAWS.bend` and this stack's laws — the same shape, two different objects

**2026-09-17.** Written from Bend 2.0.4's own guide (`bend guide`, saved at `~/.cache/bench/bend-guide.md`, "Laws and Proofs",
"Recursion and Termination", "Under the Hood"), bend-lang.com and the repository README, against `TRVM/LAWS.md`, the governance
ledger (`TRVM/governance/round-11-ledger.md`, rounds 11–28), `box-and-box`'s README and law manifest, and the evidence rules the FCB
and WEK lanes work under. It exists so that no public sentence about "laws an AI cannot break" is written here without knowing what
Bend already says with the same words. It is a comparison, not a ranking, and it names what would change it (§7).

## 1. What each one is

**Bend.** A `law` is a typed proposition: `law add_zero: for x: Nat  {Nat.add(x, 0n) == x : Nat}`. It is proven by a `def` of the
same name whose body is a term of that type — no tactics; `{==}` closes a goal when both sides compute to the same term, a `match`
refines the goal per case, a recursive call is the induction hypothesis, `%e : P` rewrites. By convention `LAWS.bend` holds the laws
(the human writes it, "the AI does not touch it") and `PROOF.bend` holds the proofs and the code (the AI writes them). **The gate is
`bend PROOF.bend`: it fails while any law is open or false and prints "All terms check." when every law holds.** Termination is
mandatory, mutual recursion forbidden, `@unsafe` opts a def out of the proof guarantees. The theory has one universe
(`Type : Type`) and no positivity check; consistency comes from a wall between *live* checking (code that runs must terminate)
and *dead* checking (types, erased arguments, equations may loop or inhabit `Empty`), and "nothing dead ever counts as live
evidence". `bend2/bend.lean` mechanizes the theory "though it lags `bend.ts`". The site's headline example:
`law you_cant_win: for moves: List<Game.Move> ... {Game.is_won(Game.replay(Game.start(), moves)) == False{} : Bool}` — an AI
that introduces a winning bug cannot merge, because no proof of that law exists for the buggy code.

**This stack.** Three layers that are often said in one breath and must not be:

- `TRVM/LAWS.md` — each law is "a **retracted claim converted into a permanent rule** — an invariant earned from a specific
  failure and enforced by a specific battery." Law 4: every reported reduction cost names its strategy. Law 5: a numeric threshold
  may change representation, never meaning (earned by the period-33 horizon bug). Law 6: a canonical observable carries every state
  variable that can determine future behaviour — if two states can lead to different futures, their Film bytes differ. Law 13:
  candidate completeness and fact updates are distinct protocol channels. Law 23: a memo key includes every dimension the generator
  ranges over. Law 26: a fault-injection test asserts the fault actually fired. Each carries the failure that earned it, the code
  that cites it and the battery that enforces it; tiers are CANONICAL / RECONSTRUCTED / RESERVED, and **promotion to CANONICAL is a
  human act — an agent may not backfill canonical text from its own paraphrase.**
- The governance plane — a grid of law entries (v1.71.0: 141 entries, 509 citations), each **property-tested** (world battery 29 laws)
  and each with a **negative battery** that must catch every forgery it was written against (404/404); warrants that are **bound to
  the lineage that gives them meaning** (TRVM-WARRANT-v4, round 28: a lineage bound outside `warrant_id` is a label, not a binding);
  "a citation is a name, not a warrant"; "the store is untrusted by construction"; a receipt may not join fields from disagreeing
  authorities.
- `box-and-box` — the [&] governance kernel: 210 property-tested laws over an eight-rung modality ladder; a bridge `feasible ▸
  permitted ▸ best` over a safety floor that **no utility, however large, can buy off** (a vetoed option's score is `0̲`, which
  annihilates through any `⊗`); every verdict ships a certificate; the reflexive rung entrenches a ring-0 core the rules may not
  weaken.

And the working rules the batteries live under, which are the part that actually resembles Bend's gate: NON-EVIDENTIARY is a
status a receipt prints about itself; a mutant a fast reader never exercises is not a control; a check you can satisfy by building
its argument is not a check; a result is quoted only at the level its campaign measured.

## 2. The same shape

Both put a file of laws the agent may not edit next to code the agent writes, both make an executable gate the agent must pass by
supplying something (a proof term; evidence, a mutant caught, a certificate), both refuse a change on failure rather than warning,
and both divide labour the same way: the human states, the machine judges, the agent satisfies. Bend's "law-driven development"
paragraph and `FOUNDATION_LANE.md` §5's "bounded RSI: fixed external verifier, human on the loop" describe the same loop. Bend's
"All terms check." and this tree's "ALL GUARDS PASS" are the same sentence. That is why the comparison has to be written down: read
quickly, the two pitches are indistinguishable, and only one of them says "mathematically impossible".

## 3. What a law ranges over — the first real difference

A Bend law is a proposition about **total functions over inductive data inside one language**: equalities that compute, existence
witnesses, negations through `Empty`. It can say "for every list, `sort` returns the same elements ascending"; it can say "no move
sequence wins". It says these things *completely*, for all inputs, once.

This stack's laws are almost never of that kind. Law 26 is about whether an injected **network partition actually bit** during a
run. Law 4 is about **how a number was measured**. Law 6 is about whether **serialized bytes** carry every hidden state variable of a
runtime. Law 13 is about which **protocol channel** a message may travel. The FCB gates are about a **source process's lateness**
and a **hardware counter's window edges**. WEK's rules are about **journal landings and leases across a crash**. These are properties
of runtimes, batteries, processes, hosts and protocols — most of them across C, Zig, Mojo, Rust, Erlang, Go, Python and JavaScript —
and many are about the world outside any program (a host was loaded; a fault fired; a write landed after its lease). Bend's law
language has no term for any of them, and this stack has no formal statement language in which "sorted for every list" is a theorem.
Neither lack is a defect; they are different objects that happen to share a noun.

## 4. Proof versus evidence — the second

Bend's law, once proven, holds for all inputs by construction, modulo its trusted base: the type theory (with `Type : Type` and the
live/dead wall standing in for positivity), the checker `bend.ts` (which the Lean mechanization lags), Bun, clang, and the
convention that `@unsafe` is not used where it matters. Within that base the claim "the AI cannot break the law" is a theorem, and
"mathematically impossible" is the right register for it.

This stack's law holds **as far as it has been shown to fail to be broken**: 2,000 property trials per law, a negative battery of
forgeries every one of which must turn a named row red, mutants that the suite must catch before a timing run counts, receipts that
say NON-EVIDENTIARY about themselves when the host was shared. The evidence states are graded — PROPERTY-TESTED, FALSIFIED-KEPT-RED,
PROVED *in its domain*, NON-EVIDENTIARY — and the register never rises to "impossible", because the thing being governed (a runtime, a
host, a protocol) is not a term that normalizes. The asymmetry is honest in both directions: **Bend can claim more, about less; this
stack claims less, about more.** Anyone who writes "our laws are like Bend's, but for runtimes" has claimed Bend's register for
evidence that cannot carry it, and anyone who writes "Bend only checks pure code" has missed that within that scope its guarantee is
stronger than anything here.

## 5. Where the gate runs — the third, and the one that matters for products

`bend PROOF.bend` runs **once, at check time, on code**. A proven program is then compiled and run, and its `IO` — printing, files,
network, the `Window` and `Audio` foreign effects — is outside the laws: Bend's laws are about pure functions, and nothing in the
guide gates an effect at the moment it happens. A proven-correct `sort` can still be called on the wrong file.

This stack's gates run **at the effect boundary, at run time**: a Worker's output is data, never authority; a write needs a warrant
bound to a lineage, and a store that has seen a later token refuses an earlier one (WEK's fence-at-the-store); an action is judged
`feasible ▸ permitted ▸ best` when it is proposed and the verdict ships a certificate; an FCB row that begins a transition after the
deadline has its work executed, uncounted, rolled back and reported. That is a different layer, not a competing one: Bend governs
**what code is**; this stack governs **what is allowed to happen**. The right composition, if one were ever wanted, is obvious —
Bend-style proofs on the pure core of a Worker, this stack's warrants and floor at the boundary where the Worker touches a world.
Nothing here builds that today and nothing should be claimed about it.

## 6. Three smaller differences worth stating exactly

- **Who may promote a law.** In Bend the proof is the promotion and the checker is the authority; a law is either proven or open.
  Here, the *statement* of a law is provenance-bearing (the failure that earned it) and moves to CANONICAL only by a human ruling;
  an agent's evidence can register a candidate law as PROPERTY-TESTED but cannot ratify it. Bend does not need this because its laws
  are stated by the human to begin with and have no provenance to lose; this stack needs it because its laws were reconstructed from
  history and an agent backfilling canonical text would be fabricating provenance.
- **What protects the law file.** Bend's separation of `LAWS.bend` from `PROOF.bend` is a **convention** ("the AI does not touch it")
  enforced by nothing in Bend; an agent with repository write access can edit a law. This stack has exactly the same exposure at the
  repository — and adds the ledger, lineage-bound warrants and the reflexive rung's entrenched core, so that a rewritten law appears
  as a new lineage rather than as the same law with a different text. Neither is immune to a compromised repository; only one makes
  the rewrite visible after the fact.
- **The negative battery.** This stack does not trust a gate until the gate has been shown to fail: every law has forgeries it must
  catch, every control has a mutant it must expose, and a control that cannot fail is not a control. Bend's checker has a
  mechanization that lags its implementation and, as far as the guide, the site and the README show, no published battery of
  wrong proofs it was shown to reject. That is not evidence the checker is unsound; it is evidence that its unsoundness has not
  been priced in public, which is the thing this stack's rules would ask of it first.

## 7. What Bend has that this stack should notice, and what would change this note

**Notice:** a decidable, fast, tactic-free statement language in which a law is executable and an agent can iterate against it in
a loop. `TRVM/LAWS.md` has no statement language: Law 6 is prose plus a battery, and the citation from code to law is a string. The
governance grid's property-tested entries are the nearest thing, and WRL's `==` verified route (Core 0.3, next in the promotion
order) is the first place a law-shaped declaration meets an executable gate. The bounded, honest move is not to adopt BendTT but to
give each CANONICAL law that *is* a pure statement a machine-checkable form beside its battery — Law 5's one-hot/binary equivalence
and Law 23's memo-key completeness are type-level statements; Law 4, 6, 13 and 26 are not and should not be pretended to be.

**Would change this note:** Bend adding laws over effects (an `IO` contract the checker enforces at the boundary); BendTT's Lean
mechanization catching up to `bend.ts`, or a published rejection battery for the checker; this stack acquiring a formal statement
language for the laws that admit one. Any of the three moves a sentence in §3–§6 and would be recorded here with a date.

## 8. Claim discipline for anything public

- Never "mathematically impossible", "cannot be broken", or "guaranteed" for this stack's laws. Say **evidence-graded**,
  **execution-gated**, **cross-language**, **at the effect boundary**, and name the grade.
- Never "Bend only checks pure code" as a dismissal. Say Bend's laws are **proofs over pure code**, stronger than anything here
  within that scope, and silent at the effect boundary.
- Never "like Bend's LAWS.bend". The words coincide; the objects do not. If the comparison must be made in one sentence: *Bend proves
  what a function is; this stack governs what an action may do, and says how sure it is.*
