# Related work, and an honest bound on novelty

This bundle sits at the intersection of several mature lines. Each component has strong
prior art; the contribution is their *synthesis* and the *measured characterization*, not
any individual mechanism. The prior art is stated precisely because the credibility of the
novelty claim depends on bounding it correctly — this is the overclaim a referee removes
first.

## Coordination-free reduction and parallelism — foundational, not novel here
Interaction nets (Lafont 1989), generalizing the proof structures of linear logic, are by
construction an inherently distributed model: reductions can occur simultaneously in many
parts of a net with no synchronization, guaranteed by strong confluence. The property this
bundle leans on — confluence implies coordination-free, order-independent reduction — is
therefore the *defining* property of interaction nets, due to Lafont, not original here.
Distributed implementations of the linear-graph family go back to Bawden (connection
graphs, 1986; PhD 1992) and Bawden & Mairson (1998), who spread a linear graph across nodes
that migrate to enable rewrites. Distributed optimal reduction was realized in PELCR
(Pedicini & Quaglia). HVM / Bend (Higher Order Co.) is the modern optimal-sharing
interaction-combinator runtime targeting massively parallel CPU/GPU execution. This bundle
adds no new parallel-reduction capability; it depends on this foundation and, candidly, does
not yet demonstrate wall-clock parallel speedup (see `paper.md` limitations; `parallel.py`
measures available parallelism and coordination-freedom but the speedup needs >1 core).

## Optimal sharing — Lévy / Lamping, not novel
That a fully-shared reduction can be asymptotically smaller than its unshared form is
optimal lambda-reduction: Lévy (1978) defined optimality; Lamping (1990) gave the first
algorithm; Gonthier, Abadi & Lévy (1992) recast it via the geometry of interaction. The
bundle's "parity of 2^24 in ~480 interactions" measures this known phenomenon; it does not
discover it.

## CRDTs and coordination-freedom as a discipline — Shapiro / CALM / LVars
Conflict-free replicated data types (Shapiro, Preguiça, Baquero, Zawirski 2011) are exactly
join-semilattice objects: a value set forming a semilattice with least-upper-bound merge,
under monotone updates, is a CRDT. CALM (Hellerstein; Laddad et al., "Keep CALM and CRDT
On", VLDB 2022) establishes the monotonicity-equals-coordination-freedom correspondence.
LVars (Kuper & Newton) use lattice-structured shared state for deterministic parallelism;
delta-state CRDTs address merge cost. The bundle's claim that "merge of confluent
computation obeys the CRDT laws" is a *special case applied to a new object* (computation
rather than data); its tier framework is best read as a finer-grained, substrate-relative
refinement of CALM's monotone/non-monotone dichotomy — not a replacement for it.

## Content-addressing — Unison / Nix / Merkle, structural only
Unison (1.0, Nov 2025) identifies definitions by a hash of the syntax tree (SHA3-512),
giving build-free, relocatable, perfectly-cached *code*; its identity is purely structural
(one character changed gives a different hash). Nix and Bazel remote-execution CAS
content-address build artifacts by input hash, also structural. The bundle's structural
identity is the same idea; its *semantic* identity (recognizing differently-derived
computations as equal) is what these systems do not attempt, and is where the e-graph layer
enters.

## E-graphs and equality saturation — egg / egglog / slotted
egg (Willsey, Nandi, Wang, Flatt, Tatlock, Panchekha; POPL 2021) and egglog are the modern
equality-saturation engines; the binder problem is addressed by slotted e-graphs (Schneider,
Koehler, Steuwer; PLDI 2025; Rust library `slotted`), which parameterize e-classes with
slots to represent terms uniquely up to variable renaming and avoid the de-Bruijn blowup
under beta. The bundle's `iceg.py` and `slotted.py` apply these techniques to
interaction-calculus terms (dup/sup binders); the engines and the slotted technique are
prior art, the IC-specific application is the increment.

## Sheaf-theoretic consistency — Robinson / Ghrist / Hansen, not novel
Using cellular sheaves to encode local-to-global constraints and detect global consistency
in networks is due to Robinson, Ghrist, Hansen and collaborators. The precise statement the
bundle uses — local sections glue iff the first cohomology obstruction vanishes, i.e.
H^1 = 0 iff global consistency — is standard there. A sheaf-theoretic characterization of
distributed-task solvability (arXiv 2503.02556, 2025) proves terminating solutions are
global sections and that obstructions to global sections encode unsolvability, with
cohomology giving a linear-algebraic description of the decision space; Ghrist & Cooperband
quantify global inconsistency by non-trivial H^1 classes. Most directly relevant, Ghrist,
Riess and collaborators are developing sheaf cohomology for cellular sheaves valued in
*lattices* — exactly the sheaf-meets-semilattice direction the bundle's sigma-as-conflict-
freedom touches. The bundle's sigma analysis is therefore downstream of and consistent with
this line, not ahead of it; its only local move is to identify "sigma-resolution built for
H^1 = 0" with the conflict-freedom its confluent merge already provides for the replica case
(see `frontier.py`, `provenance.py`).

## What is, then, plausibly novel
Bounding to what the prior art does not already cover, the genuine contributions are the
synthesis and the measurements, not the mechanisms:

1. Treating the replicated / merged object as *computation* (partial normal forms,
   dup-bearing IC terms) rather than data, code, or state — and showing the CRDT laws,
   structural and (relative to a ruleset) semantic dedup, and the two asymmetries
   (cost != size, merge-cost != copies) hold there, in tested code.
2. The **tier framework / invariant absorption**: a substrate-relative classification of how
   far a given invariant can be pushed into the representation (structural /
   reduction-checkable / oracle-needed; two flavors of tier-1), and the finding that the
   periodic-table invariants, defined as structure measures, stay decidable — with beta,
   sigma-by-construction, and the provenance G-Set as structural results and delta marking
   the coordination-hard edge.
3. The specific *combination* — optimal-sharing IC reduction + confluent merge +
   content-addressed identity + slotted e-graph identity — assembled and exercised end to
   end, which no single prior system occupies.

None of these is a new theorem about reduction, sharing, CRDTs, or sheaves; they are an
integration and an empirical characterization. That is the honest scope of the claim.
