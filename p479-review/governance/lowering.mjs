/* ═══════════════════════════════════════════════════════════════════════════
   lowering.mjs — v0.13.0 — the source language reaches the governed runtime

   Three logically independent relations, which is the whole design and not a
   decomposition for tidiness. Each can fail while the others hold: a lowering
   can be perfect while the decoder misreads the normal form; a decoder can be
   perfect while lowering emitted the wrong target term; and the runtime can
   execute a correctly lowered term incorrectly. Twenty-seven rounds have gone
   into separating claims that felt like one claim, so they get three
   obligations, three laws, and a chain of identities that may not collapse —
   DECLARED in REFINEMENT_CHAIN and counted nowhere, because the count in this
   sentence said "six" through the pass that made it seven.

       program_sem_id
             │  lowering_sem_id            ← commits to the TEMPLATE encoding
             ▼
       target_template_sem_id        ← TRVM-TARGET-TEMPLATE-v1, ports structural
             │  instantiation_sem_id + inputs_sem_id
             │  SUBSTITUTION ONLY. This arrow said "substitution THEN emission;
             │  emit() is INSIDE this relation" and ended at target_term_sem_id
             │  — the PRE-B2.1 architecture, for the seven passes after B2.1
             │  split emission out. GPT found it at B7. The rest of the file
             │  had been right the whole time, which is exactly what makes a
             │  header the last place a stale claim survives.
             ▼
       closed_template_sem_id        ← ctmpl-, a domain of its own even at bytes
             │  emission_sem_id            ← commits to the TEMPLATE encoding,
             │                                the EXECUTABLE encoding, AND the
             ▼                                MAP between them (EMISSION_RULES)
       target_term_sem_id            ← the closed executable ic32 term
             │  native ic32 execution
             ▼
       target_nf_sem_id
             │  decode_sem_id
             ▼
       target_outcome_sem_id
       source evaluator ──────────▶  source_outcome_sem_id

       REFINEMENT:  source_outcome_sem_id == target_outcome_sem_id
                    over canonical, FULLY BOUND input environments; see
                    REFINEMENT_SCOPE for what is declared open

   THE LOWERING GETS NO FILM, and that is a ruling rather than an omission. A
   semantic film is evidence for a TRANSITION SYSTEM; lowering is a relation
   DeriveProgram → TargetTerm. Filming it would invent a sequence of internal
   compiler steps and make implementation strategy semantic — the mistake the
   read-order ruling refused when it kept access order out of the footprint and
   out of the semantic projection. The instrument here is RE-LOWERING: lower
   again, independently, and compare canonical target-term identity. A film
   becomes appropriate only if the lowering engine itself ever becomes a
   governed transition system whose intermediate steps matter.

   TWO IDS, NOT ONE, and they are split before either is written. One id must
   not silently answer both "which lowering semantics is this?" and "what
   happened when we lowered this particular program?":

       lowering_sem_id      the RELATION — H over LOWERING_SEMANTICS alone
       LoweringReceipt      the APPLICATION — {program_sem_id, lowering_sem_id,
                            target_template_sem_id}, itself content-addressed

   DECIDED AT B1, COMPLETED AT B1.2. The inputs model is TWO LEVELS: lowering
   produces a parameterized TEMPLATE whose identity is a function of the program
   alone, and instantiation closes it against canonical inputs to produce the
   executable TERM. 'Parameterized versus instantiated' was a false choice — the
   template is parameterized AND the executed term is necessarily closed.

   B1 stated that and had no template: lower() emitted an ic32 STRING, so
   `input-port` had nowhere structural to live. B1.2 added
   TRVM-TARGET-TEMPLATE-v1, moved lowering's codomain onto it, and put the
   whole source fragment INCLUDING `input` into the hashed semantics so that
   implementing the frozen rule cannot move an identity.

   BUILT AT B2, and the point of the three passes before it is that THE ACT OF
   IMPLEMENTING MOVED NEITHER SEMANTIC ID. `input` lowers, instantiate() runs,
   both lifecycle flags are true, the falsifiers are WITNESSED — and none of
   that touched lsem or isem. That is the property B1.1 set out to make possible
   and B2 is the first round able to exercise it.

   BE EXACT, THOUGH: both ids DID move this round, for two changes that are not
   the implementation and are separable from it —

       lsem   op_lowering_rules went from ENGLISH to STRUCTURAL (below)
       isem   the emission SPLIT TRIGGER moved out of the hashed semantics into
              INSTANTIATION_STATUS, where a governance note belongs

   Both were ruled by GPT, both change what the semantic record SAYS, and
   neither is a consequence of code being written. The distinction is measured
   rather than asserted: flipping every lifecycle field on today's records moves
   nothing. Two further things changed shape here:

       op_lowering_rules is now STRUCTURAL and lower() INTERPRETS it, so the
       specification and the implementation are one object rather than two that
       can disagree. That moved lsem once, deliberately, and closes most of
       B1.1's declared-open prose brittleness.

       lower() NO LONGER RETURNS target_term. instantiate() is the only route to
       an executable term, so the shortcut path cannot survive as a second
       mechanism; the old equality is kept as a REGRESSION THEOREM.

   THIS HEADER WAS STALE FOR A ROUND, TWICE. It described the pre-B1 chain
   program_sem_id → target_term_sem_id and said the inputs model was undecided,
   while the sections below said the opposite — a file contradicting itself,
   which is the record-staleness class this tree does not tolerate elsewhere.

   CORRECTED AT B1.2.1: emit() WAS A HIDDEN SEMANTIC RELATION. B1.2 introduced
   the template and left the encoding commitments pointing where they had been
   pointing before there was one. Measured: changing the add combinator moved
   LOWERING_SEM_ID (lsem-d95ee1cb… → lsem-6e445936…) and left
   INSTANTIATION_SEM_ID, target_template_sem_id and the template-encoding id
   exactly where they were — so the executable term's bytes changed and the id
   of the relation that PRODUCES those bytes did not. Both halves were wrong and
   they are the same mistake facing opposite ways:

       UNDER-BOUND   INSTANTIATION_SEMANTICS named its codomain in PROSE
                     ("… via emit()"), so a semantic dependency was hiding
                     behind a symbol name.  Now: TARGET_EXECUTABLE_ENCODING_SEM_ID.

       OVER-BOUND    LOWERING_SEMANTICS still carried the whole TARGET_ENCODING,
                     a pre-template leftover — the same class as the
                     LoweringReceipt still ending at target_term_sem_id, which
                     B1.2 fixed one declaration away and missed here. An emitter
                     change re-identified every LoweringReceipt ever issued, for
                     a relation that had not changed.  Now: lowering commits to
                     the TEMPLATE encoding and to its own per-op rules.

   ── B6.3: THREE THINGS, NOT TWO, AND THE THIRD IS THE CODE ────────────────
   B6.2 split emission into a SEMANTIC relation and a SERIALIZATION profile, and
   the split was right and one term short. What produces bytes is:

       SEMANTIC ENCODING      what a target term MEANS — Church and add
       xenc / esem            structure, label EQUALITY and FRESHNESS, the
                              alpha/label quotient, the semantic refusals. Moves
                              only when meaning moves. No prose, no
                              serialization, no attribution, no ladder — three
                              of those four were still inside it at B6.2.

       SERIALIZATION PROFILE  the representative CHOICES, as VALUES emit()
       cemp-                  reads: counter start, label allocation order,
                              binder names. Moves when a choice moves. No field
                              in it contains a space, so prose cannot re-enter.

       EMITTER ARTIFACT       the implementation itself. Moves for ANY edit to
       cema-                  the code that produces bytes, comments included,
                              because it is PROVENANCE and provenance is allowed
                              to overmove.

   AND THE TWO THEOREMS ARE SCOPED TO WHAT EACH ACTUALLY OWNS:

       E-1a  same closed-template identity + same EMISSION_SEM_ID
                 -> same target_term_sem_id            (says nothing about bytes)
       E-1b  same closed template + same PROFILE + same ARTIFACT
                 -> same exact bytes                   (says nothing about meaning)

   B6.2 wrote E-1b with the artifact term missing, and GPT falsified it in one
   move: change {f0,f1} to {q0,q1} inside the combinator and the bytes differ on
   6 of 9 fixtures while the profile id — the id the theorem named as its whole
   precondition — stands still.

   THE THREE IDENTITIES THIS FILE PRODUCES ARE A LADDER, NOT A PAIR, and this is
   where that is said because it is a fact about the proof architecture rather
   than a property of any encoding — it was inside TARGET_ENCODING until B6.3
   and moved the encoding's identity every time it was reworded:

       exact emitted BYTES --quotient alpha and label spelling-->
       target_term_sem_id  --execute, normalise, decode--> outcome_sem_id

   Different bytes may share a target_term_sem_id; different target_term_sem_ids
   may share an outcome_sem_id. EMISSION PROVES THE MIDDLE ONE, and an
   EmissionReceipt carrying no byte digest does not claim these exact bytes were
   produced — nor could it, now that the bytes depend on two identities the
   receipt deliberately does not carry.

   ── B7: `sub`, AND THE FIRST TIME THE COMPILER IS SMALLER THAN THE LANGUAGE ─
   Every pass from B1 to B6.3.1 sharpened identities over a fragment of two
   operators. B7 adds a third, and the interesting thing is not the operator: it
   is that `sub` is the first construct whose SOURCE meaning does not fit in the
   TARGET, so it forces the chain to say what a partial compiler is.

       the source core       `sub` is true subtraction. sub(2,3) is -1 and the
                             core is right about that. CORE_SEM_ID does not move.
       the target encoding   represents NON-NEGATIVE Church naturals. -1 has no
                             image. Not a bug; a codomain.
       therefore             source language  ⊃  representable target fragment

   THREE WRONG PLACES TO PUT THAT, each of which looks reasonable until it is
   written down:

       SATURATE       emit Church monus, which answers 0 for sub(2,3). Measured
                      before it was rejected: (2-3)+2 then decodes to 2 against
                      the source's 1 — an answer that is itself representable, so
                      no downstream check on the RESULT can catch it. That is a
                      miscompilation, not a design choice.
       REFUSE AT      `lower-negative` cannot be written: sub(input x, input y)
       LOWERING       has no underflow FACT until an invocation binds the ports,
                      so lowering would have to refuse programs that are fine.
       REFUSE IN      changes the language to suit the compiler, and moves
       THE SOURCE     CORE_SEM_ID — re-identifying every program ever written.

   What is left is a refusal at EMISSION, by name, against the codomain:
   `emit-sub-underflow`. It is NOT source-refusal ↔ target-refusal preservation
   and must not be written as one — for sub(2,3) the source does not refuse at
   all, it evaluates to -1, and the COMPILER declines to produce a term. There
   is no target outcome to compare against, and the evidence says so rather than
   leaving a reader to infer it.

   AND IT IS DECIDED BEFORE ANY KNOB IS READ, which is the structural half:
   whether a closed template has an image is a property of the template and the
   codomain, so no serialization profile can turn a domain refusal into an
   acceptance or into a different refusal.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { canonicalBytes, ownCanonical, CORE_SEM_ID, programSemId } from "./derive_protocol.mjs";

const H = (s) => createHash("sha256").update(s).digest("hex");
/* ADDITIVE at B6.3: emit() gained an optional PROFILE parameter, and the module gained
   emitterProfileId, emitterArtifactId, CANONICAL_EMITTER_ARTIFACT_ID,
   CANONICAL_EMITTER_PROFILE_NOTES and SUPERSEDED_EXPLANATORY_PROSE_SEM_IDS.
   ADDITIVE AGAIN at B6.3.1: EMITTER_ARTIFACT_MEMBERS, EMITTER_ARTIFACT_INERT and
   emitterArtifactBundle joined it, and the module-private LABEL_ALLOC_ORDERS table
   moved inside labelAllocPreOrder — which is why cema- moved and no exported name
   was removed. Both bumps proved additive the way round 10 ruled such a claim must
   be proved — by cert_id, which is a08ee15d… across all of it — and never by a
   file hash.
   B7 IS THE FIRST BUMP IN THIS SERIES THAT IS NOT ADDITIVE-BY-EXPORT, and it says
   so rather than borrowing the previous rounds' sentence. The module gains T.sub,
   representableValue and PRED_COMBINATOR and removes nothing — but the FRAGMENT
   grew, so four semantic ids move ON PURPOSE and three stand still. Which four,
   and why the one everybody expects to stand still does not, is the movement
   table in the round brief: measured against the shipped B6.3.1 tree, not
   predicted from it. cert_id is still a08ee15d… — the calculus did not move.
   B7.1r THEN CORRECTED B7's OWN CONCLUSION about one of those four. The map came
   out of the codomain into EMISSION_RULES, ADD_COMBINATOR and PRED_COMBINATOR
   became VALUES rather than code, EMITTER_ARTIFACT_SEMANTIC joined the module,
   and TARGET_ENCODING lost every field that was about a map rather than about
   an ic32 term. See SUPERSEDED_MAP_IN_CODOMAIN_SEM_IDS.

   0.13.0 (B8.3) IS A TRUST-BOUNDARY EDIT AND MOVES NO SEMANTIC ID.
   `decodeOwned` → `decodeOwnedAgainst`, plus `makeTargetDecoder` binding the
   identity oracle at a composition root — B2.1.2's repair applied to the
   decoder, which had reproduced the caller-chosen-oracle shape at the OUTPUT
   end of the chain. DECODE_SEM_ID is unchanged and that is the check: who
   nominates the judge is a composition fact, not an encoding one. */
export const LOWERING_VERSION = "0.13.0";

/* ── THE EXECUTABLE TARGET ENCODING ───────────────────────────────────────
   ic32's interaction net is linear: a variable used twice needs an explicit
   dup. So Church numerals are emitted in LINEAR form with explicit dup labels,
   which is the shape the conformance corpus already uses for church_apply_N.
   THE LABEL POLICY IS *NOT* PART OF THE SEMANTIC ENCODING — corrected at B6.1
   and made structural at B6.2. This paragraph used to say the opposite: that
   two emissions differing only in which integers they hand the dups are two
   different emissions. They are not. The canonical signature is
   byte-equivariant under bijective label permutation (L-BYTES-1), so
   target_term_sem_id is IDENTICAL across them and the claim was refuted by the
   very codomain it appealed to. What is semantic is which labels are EQUAL and
   which are FRESH; which integers represent that is SERIALIZATION, and it now
   lives in CANONICAL_EMITTER_PROFILE with an identity of its own.

   THIS RECORD IS WHAT emit() IMPLEMENTS, and after B1.2.1 that is a commitment
   rather than a comment: TARGET_EXECUTABLE_ENCODING_SEM_ID hashes these bytes
   and INSTANTIATION_SEMANTICS names that id as its codomain, so changing the
   Church expansion, the add combinator or the dup label policy moves the
   identity of the relation that produces the executed term.

   ITS REFUSALS ARE EMISSION'S. Until B1.2.1 this list held four `lower-*`
   names — lower-unsupported-op, lower-non-integer-constant, lower-negative,
   lower-reads-undecided — which are facts about the SOURCE FRAGMENT and cannot
   arise while emitting. They were here, and emit's two refusals were over in
   LOWERING_SEMANTICS.refusal_semantics: the two vocabularies were CROSSED, and
   once these bytes carry an identity, renaming a source-fragment refusal would
   have moved the executable encoding's id without touching the encoding. */
export const TARGET_ENCODING = Object.freeze({
  target: "ic32 interaction net, SEMSTATE-CANONICAL-v1",
  // THE CONSTRUCTORS OF THE EXECUTABLE LANGUAGE, and after B7.1r that is all
  // this record is about. B7 added `sub` to the fragment and added NOTHING
  // here: no new constructor, no new runtime rule, and the measurement said so
  // explicitly — the declared pool was already sufficient. A macro realised in
  // Var/Lam/App/Dup/Sup/Era is not a widening of Var/Lam/App/Dup/Sup/Era.
  constructors: Object.freeze(["Var", "Lam", "App", "Dup", "Sup", "Era"]),
  binding: "λ binds one variable. A variable used MORE than once needs an explicit dup — the net is " +
    "linear in that direction — while a binder used ZERO times is dropped through the substitution " +
    "store and needs no Era node, which is the affine direction and is what lets an unused binder " +
    "appear without erasure syntax. Free names are free.",
  label_semantics: "WHAT IS SEMANTIC IS THE EQUALITY STRUCTURE, NOT THE SPELLING. &0/&1/&2 and " +
    "&7000/&7001/&7002 carrying the same equality pattern are the SAME target term: no rule can " +
    "distinguish them, and the canonicaliser says so. What IS semantic is which labels are EQUAL, " +
    "which are FRESH, and where a label is SHARED — collapsing two distinct dups onto one label " +
    "changes whether DUP-SUP= or DUP-SUP! fires, which is a different computation and a different " +
    "term. So this encoding commits to the equality/freshness relation among labels and to nothing " +
    "about the integers chosen to represent it.",
  quotient: "alpha-renaming and bijective label permutation, by asserted law (L-BYTES-1). The " +
    "canonical signature is byte-equivariant under both, so a term is identified up to them and an " +
    "emitter that only relabels has not produced a different term.",
  identity: "target_term_sem_id is the canonical semantic-state identity of a term under " +
    "SEMSTATE-CANONICAL-v1, minted by the kernel from the bytes and never by whatever produced them.",
  // NO REFUSALS. B7.1r, and the omission is the whole point of the split: this
  // record describes a LANGUAGE, and a language does not refuse — a MAP INTO it
  // refuses, when something in its domain has no image. `emit-unbound-port`,
  // `template-malformed` and `emit-sub-underflow` are all refusals of the
  // emission MAP and live in EMISSION_RULES. Until B7.1r they were here, and
  // that is why renaming an emission refusal moved the identity of the
  // executable language.
});

/** THE IDENTITY OF THE EXECUTABLE ENCODING. GPT's B1.2.1 find, and the reason
 *  it is content-bound rather than a label: INSTANTIATION_SEMANTICS used to name
 *  its codomain as the STRING "TRVM-TERM-CANON-v1 / ic32 executable text, via
 *  emit()". A name anyone may claim is not a commitment — the same objection the
 *  primitive ruling raised against a bare `componentReachability` — so the rule
 *  that decides how church(n) and add(a,b) become interaction-net terms could be
 *  rewritten with every downstream identity intact. Now the bytes are in the id
 *  and the id is in the relation. */
/* ── B6.2: THE CANONICAL EMITTER'S SERIALIZATION PROFILE ──────────────────
   The half of the old TARGET_ENCODING that was never semantic, given its own
   home and its own identity. GPT's B6.2 ruling, and B6.1's ontology finally
   made structural rather than only stated.

   THE FALSIFIER THAT FORCED IT, measured in both directions, and the defect is
   exactly inverted in each:

       edit the PROSE describing the counter  ->  EMISSION_SEM_ID MOVED
                                                  bytes unchanged, target term
                                                  unchanged — an identity moving
                                                  for nothing
       edit the ACTUAL counter in emit()      ->  bytes differ on 7 of 9 fixtures
                                                  EMISSION_SEM_ID UNCHANGED — an
                                                  identity standing still for a
                                                  real serialization change

   So the id was bound to a DESCRIPTION of the policy rather than to the policy,
   and was therefore doing the opposite of its job in both directions at once.
   That is B1.1's finding — governance prose inside a relation identity
   re-identifies the relation when it is reworded — recurring in the one field
   B6.1 corrected the prose of without moving.

   THE PROFILE IS INTERPRETED, NOT DESCRIBED. emit() READS label_counter_start
   from this object, exactly as lower() reads op_lowering_rules since B2.1: a
   policy cannot be edited without changing behaviour, and behaviour cannot
   change without moving this id. An English sentence beside a hard-coded
   constant is two artifacts that can disagree while only one is hashed, which
   is precisely how the field above came to be false in both directions.

   ── B6.3: "INTERPRETED" WAS TRUE OF ONE FIELD OUT OF SIX ──────────────────
   GPT replayed B6.2 and found the same defect one field over, then this pass
   found it two fields over and in the other direction as well. B6.2 shipped a
   profile of ONE interpreted knob and FIVE English sentences, and every
   sentence was hashed:

       reword `binder_spelling`          -> PROFILE ID MOVED, bytes unchanged
       change the ACTUAL binder spelling -> bytes differ on 6/9, PROFILE ID
       ({f0,f1} -> {q0,q1})                 STOOD STILL
       change the ACTUAL traversal       -> bytes differ on 5/9, PROFILE ID
       (add's label pre- not post-order)    STOOD STILL — and BOTH orders
                                            satisfy the `label_order` sentence,
                                            so the prose did not even DETERMINE
                                            the bytes it claimed to identify
       reword `determinism`              -> PROFILE ID MOVED, nothing else

   So the profile reproduced, inside itself, the exact defect it was created to
   fix. THE RULE THIS PASS APPLIES: a hashed field is a VALUE THE CODE READS or
   it is not hashed. Every field below is read by emit(); nothing below contains
   a space, so prose has no field it could occupy — the same structural form as
   TARGET_TEMPLATE_ENCODING.no_names_no_labels, and stronger than a promise not
   to write any. The prose is intact and unhashed in
   CANONICAL_EMITTER_PROFILE_NOTES.

   WHAT THE PROFILE STILL DOES NOT COVER IS NAMED, NOT IMPLIED: a profile is a
   CONFIGURATION, and emit() can be rewritten to ignore it. That residue belongs
   to CANONICAL_EMITTER_ARTIFACT_ID below, and E-1b is scoped to both. */
export const CANONICAL_EMITTER_PROFILE = Object.freeze({
  profile: "TRVM-CANONICAL-EMITTER-v1",
  // where the dup-label counter starts. Read by emit().
  label_counter_start: 0,
  // WHEN an add's own label is drawn relative to its operands'. A closed enum,
  // interpreted by emit() with a NAMED refusal for anything else — the
  // discipline evalPredicate has had since B2.1. It is two-valued because BOTH
  // values were reachable under B6.2's English (`depth-first, operands in
  // declared field order` distinguishes neither), which is how a sentence came
  // to be hashed as though it pinned the bytes.
  label_alloc_order: "operands-then-node",
  // THE ACTUAL NAMES, not a description of how they are chosen. Every binder in
  // emitted output is one of these plus an integer suffix, so a binder-spelling
  // change is an edit to THIS OBJECT and moves this id by construction.
  binder_names: Object.freeze({
    church: Object.freeze(["f", "x"]),        // λf.λx. of a Church numeral
    church_dup: Object.freeze(["a", "t"]),    // a<i> head, t<i> tail, linear expansion
    add: Object.freeze(["m", "n", "f", "x"]), // λm.λn.λf.λx. of the add combinator
    add_dup: Object.freeze(["f0", "f1"]),     // what add's single dup binds
    // B7. SEVEN, not six: the predecessor's two one-shot binders are spelled
    // apart (`u` is dropped, `w` is returned) even though lexical scoping would
    // let one name serve twice. A profile whose values are the ACTUAL names is
    // only useful if reading it tells you what the emitter emits, and two
    // distinct binders sharing a spelling is exactly the reading that needs a
    // second look at the code — which is the property B6.3 was built to remove.
    pred: Object.freeze(["n", "f", "x", "g", "h", "u", "w"]),
    // B8.2. THREE, and MUL is fully LINEAR — every binder used exactly once,
    // so it needs neither a dup nor a label, and unlike PRED it does not even
    // need a drop.
    mul: Object.freeze(["m", "n", "f"]),
  }),
});

/** NOT hashed into CANONICAL_EMITTER_PROFILE_ID, and that is the whole point of
 *  the object. Everything here is an explanation of the profile rather than a
 *  value the emitter reads, and B6.2 proved by measurement what hashing it
 *  costs: rewording `determinism` moved the profile id while no byte, no
 *  target term and no conformance case changed. Same pattern as
 *  INSTANTIATION_STATUS beside INSTANTIATION_SEMANTICS. */
export const CANONICAL_EMITTER_PROFILE_NOTES = Object.freeze({
  what: "the REPRESENTATIVE CHOICES this emitter makes when it serialises a semantic target term. " +
    "None of it is semantic: target_term_sem_id quotients every one of these away. It is here so " +
    "that byte-level reproducibility is a CHECKABLE property with an identity, rather than an " +
    "implementation detail nobody can cite.",
  label_order: "depth-first, operands walked in declared field order; one label per add and one per " +
    "dup inside a Church numeral's linear expansion. WHERE the add's own label falls in that walk is " +
    "label_alloc_order, which is a value rather than this sentence — because this sentence is true " +
    "of both orders and they emit different bytes.",
  binder_spelling: "positional, from binder_names, and the canonicaliser alpha-renames every one of " +
    "them away. Until B6.3 this sentence sat beside a hard-coded {f0,f1} in ADD_COMBINATOR: two " +
    "artifacts that could disagree while only one was hashed, so changing the spelling moved nothing " +
    "and rewording the sentence moved the id.",
  determinism: "the same closed template under the same profile AND THE SAME EMITTER ARTIFACT " +
    "produces byte-identical output. That is a SERIALIZATION guarantee about this implementation and " +
    "NOT a claim about the relation — two profiles disagreeing about bytes agree about the target " +
    "term. The artifact clause is B6.3's correction to E-1b: a profile is configuration, and " +
    "configuration does not bind an implementation that declines to read it.",
  not_semantic: "CHANGING ANYTHING IN THE PROFILE MUST NOT MOVE EMISSION_SEM_ID OR " +
    "TARGET_EXECUTABLE_ENCODING_SEM_ID, and must move CANONICAL_EMITTER_PROFILE_ID. Changing this " +
    "object must move NOTHING. Both directions are falsified in emission_conformance.mjs, because a " +
    "dual property with only one half tested is the half that goes wrong later.",
});

/** The SERIALIZATION CONFIGURATION identity. It may move freely when the bytes
 *  move; nothing semantic cites it, and the EmissionReceipt deliberately does
 *  not carry it — exact bytes are PROVENANCE and belong beside
 *  executable_artifact_id.
 *
 *  A FUNCTION, so an ALTERNATE profile can be identified too. B6.2 could only
 *  narrate its knob falsifier — the profile was a module-level constant and the
 *  measurement lived in the ledger. emission_conformance.mjs now RUNS it. */
export const emitterProfileId = (profile) =>
  "cemp-" + H("TRVM-CANONICAL-EMITTER-PROFILE-v1|" + canonicalBytes(profile));
export const CANONICAL_EMITTER_PROFILE_ID = emitterProfileId(CANONICAL_EMITTER_PROFILE);

/* ── B7.1r: THE EMISSION MAP, AND IT IS NOT THE CODOMAIN ──────────────────
   GPT's ruling on B7's one disagreement, and B7's own argument was the wrong
   decomposition. B1.2.1 fixed the shape of a relation identity —

       relation identity = domain encoding + codomain encoding + THE MAP

   — and B7 put the map's growth inside the codomain's identity. `sub` added no
   executable constructor and no runtime rule; the measurement said so in as
   many words (`RULES EXERCISED … DECLARED POOL NOT EXERCISED …`, no new rule).
   It added a MACRO realised in Var/Lam/App/Dup/Sup/Era, and a macro is not a
   widening of the language it expands into. `sub` does not survive emission:
   there is no SUB node in the runtime.

   So B7's `xenc-` movement was a real finding, and it was a finding about the
   OVER-BINDING rather than about `sub`: the Church expansion, the add
   combinator, the PRED/SUB construction, the operand inversion, the codomain
   restriction and the emission refusals were all sitting inside
   TARGET_EXECUTABLE_ENCODING_SEM_ID, and every one of them is a property of the
   MAP. That is B1.2.1's over-binding defect, in the one field B1.2.1 created to
   fix under-binding.

   THE TEST THIS BUYS, and it is the reason to care rather than a tidiness
   argument: after this split, `mul` must move tenc/lsem/isem/esem and leave
   xenc EXACTLY where it is — unless it needs a genuinely new executable
   constructor or calculus rule, in which case xenc moving is the signal. An id
   that moves for every compiler-library addition cannot answer that question.
   `E-2f` MEASURES both directions rather than waiting for `mul`.

   INTERPRETED WHERE IT CAN BE, AND HONEST ABOUT WHERE IT CANNOT. `op_lowering
   _rules` is the standard: emit() READS these rules, so a rule cannot be edited
   without changing behaviour and behaviour cannot change without moving
   EMISSION_SEM_ID. What is genuinely interpreted here:

       the combinator SHAPES        template strings with {slot} placeholders,
                                    substituted from binder_names and the label
                                    counter — so changing a combinator IS
                                    changing this record
       the OPERAND MAPPING          which template field becomes the APPLIED
                                    numeral and which becomes the ARGUMENT. For
                                    `sub` that is the whole correctness question
       the DOMAIN rules             church/add/sub value arithmetic and the
                                    `require` on sub, walked by
                                    representableValue()
       the REFUSAL names            thrown by name from the rule that owns them

   What is NOT interpreted, stated rather than implied: the Church expansion is
   a LOOP over n, so `church` carries a rule KIND that church() dispatches on
   with a NAMED refusal for anything else — the discipline evalPredicate has had
   since B2.1 — and the loop body itself is code, inside cema-. A record
   claiming to be fully interpreted while a loop sat beside it would be B6.2's
   defect wearing this round's clothes. */
export const EMISSION_RULES = Object.freeze({
  encoding: "TRVM-EMISSION-RULES-v1",
  // ── how each TEMPLATE node becomes executable structure ────────────────
  node_rules: Object.freeze({
    church: Object.freeze({
      kind: "linear-church",
      binders: "church",           // profile slot for λf.λx.
      dup_binders: "church_dup",   // profile slot for the linear expansion's heads/tails
      dups: "n-1",
      zero: "λ{F}.λ{X}.{X}",
      one: "λ{F}.λ{X}.({F} {X})",
    }),
    add: Object.freeze({
      kind: "combinator",
      binders: "add",
      dup_binders: "add_dup",
      labels: 1,
      shape: "λ{B0}.λ{B1}.λ{B2}.λ{B3}.!&{L0}{{D0},{D1}}={B2};(({B0} {D0}) (({B1} {D1}) {B3}))",
      // HOW THE COMBINATOR MEETS THE OPERANDS, as a VALUE. The first draft of
      // this rule carried an `applied`/`argument` PAIR, on the theory that add
      // and sub share one application shape and differ in which operand goes
      // where. THEY DO NOT: add is the combinator applied to both operands and
      // sub is the SUBTRAHEND applied to the combinator and then to the
      // minuend. Two shapes, not one shape with a permutation — and the pair
      // emitted `((2 ADD) 3)`, which is a different term that happens to parse.
      // Caught by reading the first emission rather than by a case, which is
      // the weaker way to find it.
      application: "(({COMB} {a}) {b})",
    }),
    sub: Object.freeze({
      kind: "combinator",
      binders: "pred",
      dup_binders: null,           // PRED is AFFINE: no dup, and therefore no label
      labels: 0,
      shape: "λ{B0}.λ{B1}.λ{B2}.((({B0} λ{B3}.λ{B4}.({B4} ({B3} {B1}))) λ{B5}.{B2}) λ{B6}.{B6})",
      // THE INVERSION, AS A VALUE, AND IT IS THE WHOLE CORRECTNESS QUESTION.
      // SUB(m,n) = ((n PRED) m): the SUBTRAHEND is the numeral APPLIED, because
      // it says how many predecessors to take, and PRED is its argument. The
      // template keeps the source's a-minus-b; this ONE STRING is where the
      // target's order is stated, and editing it moves EMISSION_SEM_ID in the
      // same edit that changes the meaning.
      application: "(({b} {COMB}) {a})",
    }),
    // ── B8.2 ────────────────────────────────────────────────────────────
    // MUL(m,n) = λm.λn.λf.(m (n f)) — m applications of (n f), which is m*n.
    // LINEAR: m, n and f are each used exactly once, so no dup, no label and no
    // drop. MEASURED before it was written down, on both implementations, and
    // the classic construction transplants unchanged.
    //
    // AND ADDING IT MOVED NO EXECUTABLE-TARGET IDENTITY, which is the property
    // B7.1r built and E-2f predicted against a synthetic version of this exact
    // rule: `mul` is a macro over Var/Lam/App, not a new constructor.
    mul: Object.freeze({
      kind: "combinator",
      binders: "mul",
      dup_binders: null,
      labels: 0,
      shape: "λ{B0}.λ{B1}.λ{B2}.({B0} ({B1} {B2}))",
      application: "(({COMB} {a}) {b})",
    }),
    port: Object.freeze({ kind: "refuse", refusal: "emit-unbound-port" }),
  }),
  // ── the DOMAIN of the map: which closed templates have an image ────────
  //   Interpreted by representableValue(). This is where the codomain
  //   restriction lives after B7.1r — it is a fact about what this MAP can
  //   represent, not about what an ic32 term can be.
  domain: Object.freeze({
    represents: "non-negative Church naturals",
    // THE ARITHMETIC IS A CLOSED OPERATOR VOCABULARY, INTERPRETED — B8.2, and
    // it is what stops the next operator being a code change. B7.1r wrote these
    // as the literal strings "a+b" and "a-b" and dispatched on them in
    // representableValue(), so `mul` would have meant editing the emitter's own
    // source and moving its ARTIFACT id for what is purely a rule addition.
    // Now a rule names an operator, the operator set is closed, and an unknown
    // one is a NAMED refusal — the evalPredicate discipline since B2.1.
    value_rules: Object.freeze({
      church: Object.freeze({ literal: "n" }),
      add: Object.freeze({ operator: "+" }),
      sub: Object.freeze({ operator: "-", require: "a>=b", refusal: "emit-sub-underflow" }),
      mul: Object.freeze({ operator: "*" }),
    }),
    recursive: "EVERY sub node, not only the root. (2-3)+2 has root value 1, which is emittable, and " +
      "raw Church monus would answer 2 — an inner underflow leaves NO trace in the outcome, so a " +
      "check on the RESULT cannot see it. Measured in measure_pred_sub.mjs before this rule existed.",
    not_saturating: "an underflow is REFUSED, never answered as 0. Church monus normalises ((n PRED) " +
      "m) to 0 whenever n >= m, and the frozen core's `sub` is true subtraction, so saturating is a " +
      "MISCOMPILATION rather than a design choice.",
    partiality: "the SOURCE LANGUAGE PROPERLY CONTAINS the fragment this map can represent, which is " +
      "the ordinary shape of a partial compiler. It is NOT source-refusal to target-refusal " +
      "preservation: for sub(2,3) the source does not refuse, it evaluates to -1, and the compiler " +
      "declines to produce a term.",
    decided_before_serialization: "representability is decided before any profile field is read, so " +
      "no serialization configuration can turn a domain refusal into an acceptance or into a " +
      "different refusal.",
  }),
  refusals: Object.freeze(["emit-unbound-port", "template-malformed", "emit-sub-underflow"]),
  not_interpreted: "the linear Church expansion is a LOOP over n and its body is CODE, inside " +
    "CANONICAL_EMITTER_ARTIFACT_ID. `kind` is dispatched on with a NAMED refusal for an unknown " +
    "value, which is the evalPredicate discipline, and this sentence is here because a record " +
    "claiming to be fully interpreted while a loop sits beside it is B6.2's defect in new clothes.",
});
export const EMISSION_RULES_SEM_ID =
  "erul-" + H("TRVM-EMISSION-RULES-v1|" + canonicalBytes(EMISSION_RULES));

export const TARGET_EXECUTABLE_ENCODING_SEM_ID =
  "xenc-" + H("TRVM-TARGET-EXECUTABLE-ENC-v1|" + canonicalBytes(TARGET_ENCODING));

/* ── B1.2: THE TARGET TEMPLATE, which is the layer B1 talked about and did
      not have ─────────────────────────────────────────────────────────────
   B1 ruled that a port is `{op:"input-port", source_name:"x"}` "at the
   canonical target-AST layer, BEFORE any textual or ic32 variable allocation".
   There was no such layer: lower() built an ic32 STRING directly. A port would
   therefore have had to be a string placeholder like `$input_x`, and spelling
   would have become semantics again — the exact defect the ruling forbids,
   reintroduced by the absence of the representation it presumes.

   So the codomain of lowering is a TEMPLATE, and emitting the executable term
   is a separate, deterministic serialization:

       source AST  ──lowering──▶  TRVM-TARGET-TEMPLATE-v1
                                        │  emit (allocates)
                                        ▼
                                  TRVM-TERM-CANON-v1 / ic32 text
                                        │  native execution
                                        ▼
                                  SEMSTATE-CANONICAL-v1

   WHY ALLOCATION CANNOT BE SEMANTIC, structurally rather than by promise: the
   template contains NO binder names and NO dup labels. Both are produced by
   emit(), from the template's shape, by the documented depth-first walk. Two
   implementations that allocate `_impl17` and `q93` do not differ in the
   template because the template has nowhere to put a name. I-4a is then a
   property of the data structure rather than a convention the emitter is asked
   to respect.

   MINIMAL ON PURPOSE — exactly the nodes today's fragment needs. It is not a
   general compiler IR and does not pretend to be; `read`, `scope` and `cite`
   have no nodes because they have no lowering. */
export const TARGET_TEMPLATE_ENCODING = Object.freeze({
  encoding: "TRVM-TARGET-TEMPLATE-v1",
  grammar: "Template := church(n) | add(Template, Template) | sub(Template, Template) " +
    "| mul(Template, Template) | port(source_name)",
  nodes: Object.freeze({
    church: "{t:\"church\", n} — a non-negative integer literal. n stays a NUMBER here; how a target " +
      "realises a number is not stated in this language.",
    add: "{t:\"add\", a, b} — an ORDERED addition node over two templates, a then b, the core's own " +
      "evaluation order. Target-side rather than the source `add` op — the two languages are " +
      "separate even where a node happens to share a name.",
    // SCRUBBED AT B7.1r. This entry used to go on to say that the target
    // application order is the inverse and that the inversion happens inside
    // emit() — both TRUE, both facts about the emission MAP, and neither a
    // property of {t:"sub", a, b}. Carrying them here meant that replacing PRED
    // with a different, extensionally equal target construction would re-cut
    // tenc- and, through it, lsem- and isem-, for a change the TEMPLATE
    // LANGUAGE did not undergo. That realization detail lives in
    // EMISSION_RULES.node_rules.sub.application.
    sub: "{t:\"sub\", a, b} — an ORDERED subtraction node: `a` is the MINUEND and `b` the " +
      "SUBTRAHEND. The order is semantic here in a way add's is not: add(a,b) and add(b,a) denote " +
      "the same number and sub(a,b) and sub(b,a) do not. HOW a target realises that order is not " +
      "stated here.",
    mul: "{t:\"mul\", a, b} — an ORDERED multiplication node over two templates, a then b. Ordered " +
      "for the same reason add is — the core's own evaluation order is a then b — rather than " +
      "because the order changes the value, which for multiplication it does not.",
    port: "{t:\"port\", source_name} — an INPUT PORT, structural. Instantiation replaces it. A " +
      "template still holding one is OPEN, and an open template is not something any target can be " +
      "asked for; WHICH map refuses it, and under what name, is that map's business and not this " +
      "language's.",
  }),
  no_names_no_labels: "A TEMPLATE CONTAINS NO BINDER NAMES AND NO DUP LABELS. Allocation is therefore " +
    "not merely declared non-semantic here; THERE IS NO FIELD IT COULD OCCUPY, which is what makes " +
    "I-4a structural. WHICH integers a downstream emitter hands the dups is deliberately NOT stated " +
    "here — it was, until B6.2, and naming a counter start inside the template encoding meant that " +
    "changing an emitter's allocation policy re-cut the TEMPLATE, LOWERING and INSTANTIATION " +
    "identities. A layer whose whole claim is that no allocation exists in it cannot also commit to " +
    "how one is performed two layers down. The serialization policy lives in " +
    "CANONICAL_EMITTER_PROFILE and is cited from nowhere that is hashed.",
  determinism: "a template IS its canonical bytes. Two templates with equal bytes are the same " +
    "template, so any map out of this language is a function of those bytes and of nothing else — " +
    "which is the property this encoding claims, and it is claimed about the LANGUAGE rather than " +
    "about any particular map out of it. Until B7.1r this field described a specific emitter, so " +
    "an emitter change re-cut the template language's identity.",
  // ONE REFUSAL, AND B7.1r REMOVED THE OTHER TWO REASONS TO HAVE MORE.
  // `template-malformed` is this language's own: a structure that is not a
  // template of this grammar. `emit-unbound-port` was here and is EMISSION's —
  // an open template is perfectly well formed BY THIS GRAMMAR and it is a MAP
  // that has nothing to send it to. `emit-sub-underflow` was never here, for
  // the same reason one layer further out. Keeping either meant that renaming
  // an emission refusal re-cut the identity of the template LANGUAGE, which is
  // exactly the leak B6.2 removed when a counter start was named in this same
  // object.
  refusals: ["template-malformed"],
});
export const TARGET_TEMPLATE_ENCODING_SEM_ID =
  "tenc-" + H("TRVM-TARGET-TEMPLATE-ENC-v1|" + canonicalBytes(TARGET_TEMPLATE_ENCODING));

/* ── B2.1: EMISSION IS ITS OWN RELATION, because the trigger FIRED ────────
   B1.2.1 wrote down four conditions under which emission stops being part of
   instantiation and earns its own identity, and B2 tripped all four at once
   without noticing — which is the trigger working exactly as intended, and the
   reason it was written before it was needed rather than after.

       REUSED INDEPENDENTLY          emit() is exported and callable without
                                     instantiate()
       THEOREM-BEARING INDEPENDENTLY I-4a compares TWO emitters over one
                                     template and proves they reach the same
                                     normal form — a theorem about emission
                                     alone
       VERSIONED INDEPENDENTLY       the executable encoding already carries its
                                     own content identity (xenc-), and B2
                                     deliberately ran an alternate emitter
       INTERMEDIATE OBSERVED         instantiate() RETURNS closed_template to
                                     its caller

   The one that settles it is the second: once two emitters are compared over
   one closed template, an emitter upgrade re-cutting the semantic identity of
   PORT SUBSTITUTION is plainly wrong, and that is precisely what a merged
   relation does.

   THE CLOSED TEMPLATE GETS ITS OWN IDENTITY DOMAIN even when its bytes equal an
   open template's — `ctmpl-` against `tmpl-`. For add(2,3) with {} the two
   structures are byte-identical and they are not the same thing: one is what
   the COMPILER produced, the other is what an INVOCATION closed. Letting them
   share an id would make "this was instantiated" and "this needed no
   instantiation" indistinguishable, which is the collapse the whole chain
   exists to prevent. */
export const EMISSION_SEMANTICS = Object.freeze({
  relation: "closed target template -> executable ic32 term",
  domain_encoding_sem_id: TARGET_TEMPLATE_ENCODING_SEM_ID,
  // THE MAP ITSELF, BY ID — B7.1r, and this is the term B1.2.1's rule always
  // required and this relation never carried. It named its domain by id and its
  // codomain by id, and then relied on the CODOMAIN's record to hold the map,
  // so every addition to the compiler's library re-cut the identity of the
  // executable language. The map has its own record and its own id now.
  rules_sem_id: EMISSION_RULES_SEM_ID,
  domain_restriction: "the PORT-FREE, REPRESENTABLE subset. A template still holding a port is " +
    "refused by name; so is a closed template whose value or any subvalue falls outside the " +
    "non-negative naturals this map represents. Emission is total on that subset and refuses " +
    "outside it by name, the same discipline lowering has on its fragment. WHICH templates those " +
    "are is EMISSION_RULES.domain — a value representableValue() reads — rather than a sentence " +
    "here, so the acceptance semantics are content-bound to this relation without earning a " +
    "separate identity of their own.",
  codomain_encoding_sem_id: TARGET_EXECUTABLE_ENCODING_SEM_ID,
  // WHY THE REFUSAL IS THIS RELATION'S. Three tempting homes, each considered
  // and each wrong:
  //
  //   NOT lowering    sub(input x, input y) has no underflow FACT until the
  //                   ports bind, so lowering cannot know and a `lower-negative`
  //                   would have to refuse programs that are perfectly fine.
  //   NOT the source  the frozen core evaluates sub(2,3) to -1 and is right to.
  //                   Refusing there would be changing the language to suit the
  //                   compiler, and it would move CORE_SEM_ID.
  //   NOT the CODOMAIN, which is B7.1r's correction. An ic32 term is not
  //                   "a non-negative Church natural"; ic32 has no opinion about
  //                   naturals at all. "Non-negative Church naturals" is the
  //                   IMAGE of this map, and an image is a property of the map.
  //
  // What is left is a partial compiler: source language PROPERLY CONTAINS the
  // representable target fragment, and the compiler says so by name.
  allocation: "binder names and dup labels are INVENTED HERE, from the template's shape. This is the " +
    "only place in the chain where an allocation exists, which is what makes allocation-invariance a " +
    "property of everything upstream. WHICH representatives are chosen is NOT part of this relation: " +
    "the codomain quotients them, so committing to them here would bind the relation to a difference " +
    "its own output erases. The choices live in CANONICAL_EMITTER_PROFILE under " +
    "CANONICAL_EMITTER_PROFILE_ID, which may move whenever the bytes move, and no semantic id cites " +
    "it.",
  determinism: "a function: equal closed templates emit equal terms, labels included. Two emitters " +
    "may differ in the bytes they produce and must agree on what those bytes MEAN — that is a " +
    "theorem about this relation and it is why the relation is separate.",
  semantic_refusals: EMISSION_RULES.refusals,
});
export const EMISSION_SEM_ID =
  "esem-" + H("TRVM-EMISSION-SEM-v1|" + canonicalBytes(EMISSION_SEMANTICS));

/** The identity of a CLOSED template — a different domain from an open one's,
 *  deliberately, even at equal bytes. */
export const closedTemplateSemId = (closed) => "ctmpl-" +
  H("TRVM-CLOSED-TEMPLATE-v1|" + TARGET_TEMPLATE_ENCODING_SEM_ID + "|" + canonicalBytes(closed));

export const EMISSION_RECEIPT_FIELDS = Object.freeze([
  "closed_template_sem_id", "emission_sem_id", "target_term_sem_id"]);

/** Template constructors. Frozen plain data — canonicalBytes refuses anything
 *  else, so a template carrying a capability dies at its own identity. */
export const T = Object.freeze({
  church: (n) => Object.freeze({ t: "church", n }),
  add: (a, b) => Object.freeze({ t: "add", a, b }),
  // a MINUS b, source order. See TARGET_TEMPLATE_ENCODING.nodes.sub: the target
  // application order is inverted and that inversion lives in emit() alone.
  sub: (a, b) => Object.freeze({ t: "sub", a, b }),
  mul: (a, b) => Object.freeze({ t: "mul", a, b }),
  port: (source_name) => Object.freeze({ t: "port", source_name }),
});

/** The identity of a TEMPLATE. A different domain tag from target_term_sem_id
 *  even when the template has zero ports, because "the parameterized thing
 *  lowering produced" and "the closed thing the runtime executed" are different
 *  objects that happen to coincide in shape when there are no inputs. */
export const targetTemplateSemId = (template) => "tmpl-" +
  H("TRVM-TARGET-TEMPLATE-v1|" + TARGET_TEMPLATE_ENCODING_SEM_ID + "|" + canonicalBytes(template));

/** Every source input name the template actually consumes, in canonical order.
 *  NOT the same as the inputs supplied — that distinction is grant-vs-footprint
 *  from round 15, one layer down, and instantiation must not erase it. */
export function templatePorts(template) {
  const out = new Set();
  const walk = (n) => {
    if (!n || typeof n !== "object") throw new Error("template-malformed");
    if (n.t === "port") { out.add(n.source_name); return; }
    if (n.t === "church") return;
    if (n.t === "add" || n.t === "sub" || n.t === "mul") { walk(n.a); walk(n.b); return; }
    throw new Error("template-malformed: " + String(n.t));
  };
  walk(template);
  return [...out].sort();
}

/** TEMPLATE → ic32 text. The ONLY place binder names and dup labels are
 *  invented, which is the whole point of the layer.
 *
 *  THE PROFILE IS A PARAMETER as of B6.3, defaulting to the canonical one. Not
 *  a generality for its own sake: B6.2 asserted "changing a knob moves the
 *  bytes and the profile id and no semantic id" in a LEDGER PARAGRAPH, because
 *  a module-level frozen constant cannot be varied by the battery that is
 *  supposed to falsify it. A property this tree states and cannot run is
 *  exactly the shape three instruments at round 10 were found in. */
export function emit(template, profile = CANONICAL_EMITTER_PROFILE) {
  // ── B7: THE DOMAIN REFUSAL COMES FIRST, AND FIRST IS THE POINT ──────────
  // Whether a closed template has an image under the executable encoding is a
  // property of the template and the encoding. It is not a serialization
  // choice, so it is decided before a single knob is read: no profile can turn
  // a domain refusal into an acceptance, and none can turn it into a different
  // refusal either. The consequence is stated rather than discovered — a
  // malformed profile handed an underflowing template is answered
  // `emit-sub-underflow`, because the template was never emittable under any
  // profile at all.
  //
  // The returned value is DISCARDED. It exists to make the refusal decision and
  // nothing downstream sees it; go() below emits real PRED/SUB structure and
  // the runtime does the arithmetic. Constant-folding sub(5,2) to church(3)
  // would make every theorem about the target term a theorem about this
  // walk instead.
  representableValue(template);
  // INTERPRETED, not described: every knob below is READ. The names are read
  // too, which is B6.3's correction — until then ADD_COMBINATOR carried a
  // hard-coded {f0,f1} beside a sentence claiming the profile owned binder
  // spelling, so the spelling could change without moving the id that claimed
  // it and the sentence could change without moving anything else.
  // INTERPRETED, not described: every knob below is READ. The names are read
  // too, which is B6.3's correction — until then the add combinator carried a
  // hard-coded {f0,f1} beside a sentence claiming the profile owned binder
  // spelling, so the spelling could change without moving the id that claimed
  // it and the sentence could change without moving anything else.
  //
  // WHICH SLOTS ARE REQUIRED IS DERIVED FROM THE RULES, not enumerated here —
  // B7.1r. This guard listed church/church_dup/add/add_dup by hand, so adding
  // `pred` at B7 left a profile slot the emitter needs and the guard never
  // checked. A rule naming a binder slot the profile does not have is now a
  // NAMED refusal at the boundary rather than an `undefined` reaching a
  // destructure two frames down.
  const B = profile?.binder_names;
  if (!B || typeof B !== "object") throw new Error("emitter-profile-malformed: binder_names");
  for (const rule of Object.values(EMISSION_RULES.node_rules)) {
    for (const slot of [rule.binders, rule.dup_binders]) {
      if (slot === undefined || slot === null) continue;
      if (!Array.isArray(B[slot])) throw new Error("emitter-profile-malformed: binder_names." + slot);
    }
  }
  if (!Number.isInteger(profile.label_counter_start))
    throw new Error("emitter-profile-malformed: label_counter_start");
  const preOrder = labelAllocPreOrder(profile.label_alloc_order);
  if (preOrder === undefined)
    throw new Error("emitter-profile-unknown-label-alloc-order: " + String(profile.label_alloc_order));
  const labels = { n: profile.label_counter_start, next() { return this.n++; } };
  const R = EMISSION_RULES.node_rules;
  const go = (n) => {
    if (!n || typeof n !== "object") throw new Error("template-malformed");
    const rule = Object.prototype.hasOwnProperty.call(R, n.t) ? R[n.t] : undefined;
    if (rule === undefined) throw new Error("template-malformed: " + String(n.t));
    if (rule.kind === "refuse") throw new Error(rule.refusal + ": " + String(n.source_name));
    if (rule.kind === "linear-church") return church(n.n, labels, B, rule);
    // A COMBINATOR NODE. The APPLICATION SHAPE is a value — `(({COMB} {a}) {b})`
    // for add, `(({b} {COMB}) {a})` for sub — so the target's operand order is
    // data rather than a branch in the code, and `sub`'s inversion is one
    // string rather than a special case. Editing it moves EMISSION_SEM_ID in
    // the same edit that changes the meaning.
    //
    // THE WALK ORDER STAYS a-THEN-b, declared field order, whatever the
    // application shape says — the label counter must not start depending on an
    // operand order, or `label_alloc_order` would stop being the only thing
    // that decides where a label falls.
    if (preOrder && (rule.labels ?? 0) > 0) {
      const COMB = combinator(rule, labels, B);
      const a = go(n.a), b = go(n.b);
      return fill(rule.application, { COMB, a, b });
    }
    const a = go(n.a), b = go(n.b);
    return fill(rule.application, { COMB: combinator(rule, labels, B), a, b });
  };
  return go(template);
}

/* WHICH ops the CODE lowers today — an implementation status, not a semantics,
   and the name now says so. It was `LOWERED_OPS`, which read as the fragment
   itself and sat four lines from LOWERING_SEMANTICS.lowered_ops holding a
   DIFFERENT and larger list. Distinguishing "semantically specified" from
   "implemented" is the whole conceptual content of B1.2, so the one name in the
   file that blurred them was the wrong name to keep:

       LOWERING_SEMANTICS.lowered_ops   const · add · input · sub   SPECIFIED, frozen
       IMPLEMENTED_LOWERED_OPS          const · add · input · sub   WRITTEN

   AT B2 THE TWO LISTS COINCIDE, and that is a fact about this moment rather
   than a reason to merge the names. `input` was specified at B1.2 and written
   here; `read`, `scope` and `cite` have no lowering rule at all; `mul` and
   `len` are simply not encoded yet. The first of those to get a frozen rule
   ahead of its implementation separates the lists again, which is the state the
   distinction exists for. THE COMMENT HERE ONCE SAID `input` was absent
   "because the inputs model is undecided" — untrue since B1 decided it and
   doubly untrue since B1.2 froze the rule.

   B7 ADDS `sub` TO BOTH LISTS IN ONE PASS, and the reason is that its frozen
   rule and its implementation are the same edit: the rule is add's with the tag
   renamed, so there was no state in which specifying it without writing it
   would have taught anyone anything. What B7 does NOT do is put a
   representability precondition in that rule — see op_lowering_rules.sub. */
export const IMPLEMENTED_LOWERED_OPS = Object.freeze(["const", "add", "input", "sub", "mul"]);

/* ── B1: THE INPUTS MODEL, DECIDED ────────────────────────────────────────
   The question was posed as parameterized VERSUS instantiated. It is a FALSE
   CHOICE: the template is parameterized AND the executed term is necessarily
   closed. They are two relations, they compose, and they answer different
   questions, so they get two identities.

       program_sem_id
             │  lowering_sem_id
             ▼
       target_template_sem_id           reusable, independent of invocation data
             │  instantiation_sem_id + inputs_sem_id
             ▼
       target_term_sem_id               the closed executable term
             │  native semantic film
             ▼
       target_nf_sem_id
             │  decode_sem_id
             ▼
       target_outcome_sem_id  ==  source_outcome_sem_id

   WHY THEY MAY NOT BE MERGED, and this is the whole of the ruling: a template
   can be perfectly lowered while instantiation binds "x" to the port for "y".
   Merge the relations and a target failure becomes ambiguous between *the
   program was translated incorrectly* and *the runtime inputs were wired into a
   correct template incorrectly*. Twenty-seven rounds have gone into removing
   exactly that kind of ambiguity, and this one is cheap to keep out.

   DECIDED, NOT BUILT. `input` still does not lower. The refusal changes name
   from lower-inputs-undecided to lower-input-not-implemented, because "we have
   not ruled" and "we have ruled and not written it" are different states and a
   refusal that cannot tell them apart is a stale instrument waiting to happen. */
export const INPUT_PORT_SPEC = Object.freeze({
  namespace: "TRVM-INPUT-PORT-v1",
  identity_rule: "port_sem_id = H(\"TRVM-INPUT-PORT-v1|\" + canonicalBytes(source_input_name)). The " +
    "port's target-side identity is a function of the SOURCE NAME and the encoding, and never of " +
    "whichever variable the emitter happened to allocate.",
  canonical_form: "at the canonical target-AST layer a port is {op:\"input-port\", source_name:\"x\"}, " +
    "BEFORE any textual or ic32 variable allocation. Two implementations that internally allocate " +
    "_impl17 and q93 canonicalize to the same node and therefore to the same target_template_sem_id.",
  quotient: "internal target variable names are NON-SEMANTIC (alpha-equivalent); source input keys " +
    "are SEMANTIC. This is the INVERSE of the round-16 bug: there, identity depended on a spelling " +
    "that should not matter; here the danger is identity depending on an ALLOCATION that should not " +
    "matter while losing the SOURCE NAME that must.",
  no_normalization: "source input names are NOT Unicode-normalized. If the frozen core distinguishes " +
    "two code-point sequences as different names, the port identity preserves that exact distinction. " +
    "Normalizing would itself be a language-semantic change and belongs to the language, not to this " +
    "encoding — and a quotient introduced at the encoding layer is invisible to the source.",
});

/* ── WHAT IS HASHED, AND WHAT IS MERELY TRUE ──────────────────────────────
   B1's first cut hashed the WHOLE spec, lifecycle fields included, so
   `implemented: false -> true` moved LOWERING_SEM_ID from lsem-5673108765b4…
   to lsem-63f98923ed13… without one line of the relation's meaning changing.
   B2 becoming built would have re-identified a relation B1 froze. `decided_at`
   did the same, and INSTANTIATION_SEM_ID moved when the conformance-test STATUS
   sentence was reworded.

   That is round 16 arriving inside the compiler specification: an identity
   depending on something that should not matter. The split:

       SEMANTICS   what the relation DOES — changing it changes emitted terms
                   or accepted inputs.  HASHED.
       STATUS      what the project has done about it — rounds, evidence
                   grades, whether code exists yet.  NOT HASHED.

   DECLARED OPEN, because the split is real and not total: the semantic records
   below are still English. `dup_label_policy` and `substitution` are NORMATIVE
   prose — there is no formal encoding of them in this tree today — so rewording
   them still moves the id, and that is correct-but-brittle rather than solved.
   What has been removed is the class GPT measured: lifecycle and evidence
   status can no longer re-identify a relation. A formal target-AST grammar
   would close the rest, and it is not written.

   The B1 ids are kept below as OVERBOUND_TRANSITIONAL_SEM_IDS rather than
   erased: they were the honest identities of the overbound projection, and a
   record that quietly replaces them would be doing what this round is fixing. */
export const INSTANTIATION_SEMANTICS = Object.freeze({
  relation: "target_template + inputs -> CLOSED target template",
  // BOTH ENCODINGS NAMED **BY IDENTITY**, because instantiation is the map
  // between them and a relation that does not commit to its own domain and
  // codomain is a relation whose id cannot distinguish two different maps.
  //
  // B1.2 named the domain by id and the codomain by PROSE, and the asymmetry
  // was the defect: `TARGET_ENCODING` reached this record only as the eight
  // characters "emit()" inside an English sentence, so the whole executable
  // encoding was a semantic dependency hiding behind a symbol name.
  domain_encoding_sem_id: TARGET_TEMPLATE_ENCODING_SEM_ID,
  // THE CODOMAIN MOVED AT B2.1, when the emission trigger fired. Instantiation
  // ends at a CLOSED TEMPLATE; turning that into executable bytes is EMISSION's
  // relation. Same encoding as the domain — a closed template is a template —
  // restricted to the port-free subset, and carrying its own identity domain
  // (ctmpl-) because "what the compiler produced" and "what an invocation
  // closed" are different things at equal bytes.
  codomain_encoding: "TRVM-TARGET-TEMPLATE-v1, PORT-FREE subset",
  codomain_encoding_sem_id: TARGET_TEMPLATE_ENCODING_SEM_ID,
  codomain_identity_domain: "ctmpl-",
  // EMISSION IS INSIDE THIS RELATION, and that is a ruling with a stated
  // condition for being revisited rather than a convenience. Instantiation is
  // substitution THEN emission: ports are replaced by canonically encoded
  // values, and the resulting closed template is serialized to ic32 text by the
  // codomain encoding above. A THIRD relation with its own emission_sem_id
  // would be the more faithful decomposition — a correct port substitution can
  // coexist with an incorrect emitter, and that is exactly the kind of pair
  // this tree splits — and it is NOT taken here because emit() is neither
  // independently reused nor independently theorem-bearing today. WHEN EITHER
  // BECOMES TRUE, SPLIT IT: the trigger is written down so the boundary stays a
  // decision rather than an accident, which is the whole complaint B1.2.1 is
  // answering one layer up.
  // THE OPERATIVE STATEMENT ONLY. The CONDITIONS under which emission should be
  // split into its own relation moved to INSTANTIATION_STATUS at B2: they are a
  // rule about what the project should do next, not about what this relation
  // does, and keeping governance prose in a hashed record is how rewording a
  // note re-identifies a relation — B1.1's whole finding, which this record was
  // quietly re-committing.
  emission: "NOT PART OF THIS RELATION as of B2.1. Instantiation is SUBSTITUTION ALONE: ports are " +
    "replaced by canonically encoded values and the result is a closed template. Emission has its own " +
    "relation and its own identity (EMISSION_SEM_ID) because B2 tripped every condition the split " +
    "trigger declared — emit() is independently reused, I-4a is a theorem about emission alone, the " +
    "executable encoding is independently versioned, and the closed template is returned to callers.",
  entry_snapshot: "BOTH ARGUMENTS ARE CANONICALLY SNAPSHOT AT ENTRY and everything downstream reads " +
    "the snapshot. The bytes inputs_sem_id identifies are exactly the bytes every substituted value " +
    "was derived from. B2 read the caller's inputs twice — once to bind and once to identify — so a " +
    "getter returning 2 then 999 produced a term meaning x=2 beside an identity committing to " +
    "{x:999}: the relation misbinding its own input identity while the runtime was blameless. That is " +
    "the entry-snapshot rule arriving in the compiler layer.",
  consumed_inputs: "instantiation substitutes ONLY the ports the template declares. The inputs " +
    "SUPPLIED and the inputs CONSUMED are different sets and the difference is not erased: it is " +
    "grant-versus-footprint from round 15, one layer down. inputs_sem_id commits to the whole " +
    "supplied record; the executable term depends only on the consumed part. No input_footprint is " +
    "emitted yet and that is named rather than implied.",
  port_namespace: INPUT_PORT_SPEC.namespace,
  port_identity: Object.freeze({
    source_name_semantic: true,
    target_allocation_semantic: false,
    unicode_normalization: false,
    rule: INPUT_PORT_SPEC.identity_rule,
    canonical_form: INPUT_PORT_SPEC.canonical_form,
  }),
  substitution: "each {op:\"input-port\", source_name:N} node is replaced by the canonical target " +
    "encoding of the value bound to N. Substitution is simultaneous and capture-free: an embedded " +
    "value's own binders are alpha-renamed away from the template's, because a value that captured a " +
    "template binder would make the term depend on the emitter's naming, which is exactly the " +
    "allocation dependence the port rule exists to remove.",
  missing_input: "REFUSED by name — instantiate-missing-input:<source_name>. Not defaulted: a default " +
    "is a value nobody supplied appearing inside an identity. NOTE that the SOURCE evaluator refuses " +
    "the same situation as program-input-missing:<name>, at a different layer and under a different " +
    "code; refusal-preservation between the two is DECLARED OPEN and is named in " +
    "REFINEMENT_SCOPE below rather than assumed.",
  // REVISED AT B1.1, and the first version was wrong twice over.
  extra_input: "IGNORED. An input the template has no port for does not participate in the term. " +
    "B1 froze this as a refusal on the argument that accepting it would let inputs_sem_id vary while " +
    "target_term_sem_id did not, 'so the receipt would stop being a function'. That argument is " +
    "FALSE — a function may be many-to-one, and (template, {x:2}) and (template, {x:2, unused:999}) " +
    "mapping to the same term is exactly such a function. And the rule contradicted the SOURCE: " +
    "evaluate({op:\"input\",name:\"x\"}, {}, {x:2, y:999}) returns 2, so refusing extras at the " +
    "target would have broken refinement BY CONSTRUCTION on the first program that had one. " +
    "different inputs_sem_id -> same target_term_sem_id is not an identity defect; it is the correct " +
    "statement that executable semantics do not depend on unused data. Making extras invalid would " +
    "be a SOURCE-LANGUAGE change requiring a new CORE_SEM_ID, and the instantiator may not impose it " +
    "unilaterally.",
  input_value_embedding: "a supplied value is embedded by the SAME target encoding lowering uses for " +
    "a constant of that type. A value the encoding cannot express is REFUSED by name rather than " +
    "approximated, on the same rule that makes lowering total-or-refusing on its fragment.",
  // EMISSION'S REFUSALS ARE THIS RELATION'S, because emission is. They were in
  // LOWERING_SEMANTICS.refusal_semantics until B1.2.1, where neither is
  // reachable: lower() calls emit() only on a template with zero ports, and it
  // builds every template it emits, so `emit-unbound-port` and
  // `template-malformed` were names lowering claimed and could not produce.
  semantic_refusals: ["instantiate-missing-input", "instantiate-unencodable-input",
    "emit-unbound-port", "template-malformed"],
});

/** NOT hashed into INSTANTIATION_SEM_ID. Everything here is a fact about the
 *  project rather than about the relation, and B2 will change all of it. */
export const INSTANTIATION_STATUS = Object.freeze({
  decided_at: "round 27, pass B1",
  semantics_corrected_at: "round 27, pass B1.1 — extra_input and the semantic/status split",
  codomain_bound_at: "round 27, pass B1.2.1 — TARGET_EXECUTABLE_ENCODING_SEM_ID",
  implemented_at: "round 27, pass B2",
  implemented: true,
  operational_refusals: ["instantiate-inputs-not-canonical"],
  // GPT's B2 ruling, and the reason it lives here rather than in the hashed
  // semantics: it is a rule about when the PROJECT should change the
  // architecture, so rewording it must be free. B1.2.1 put a two-condition
  // version inside INSTANTIATION_SEMANTICS and was re-committing the exact
  // defect B1.1 found — governance prose inside a relation identity.
  //
  // The underlying rule, in GPT's words: keep A∘B one relation while nobody
  // needs to name, vary, verify, reuse or observe A independently of B.
  emission_split_trigger: "SPLIT emission into its own relation, with its own emission_sem_id and " +
    "this relation's codomain becoming the CLOSED TEMPLATE rather than the executable term, as soon " +
    "as any of four things becomes true: emission is (1) independently REUSED, (2) independently " +
    "THEOREM- or EVIDENCE-BEARING, (3) independently VERSIONED or REPLACEABLE, or (4) the closed-" +
    "template intermediate becomes an INDEPENDENTLY IDENTIFIED or EXTERNALLY OBSERVED artifact. " +
    "(3) and (4) are GPT's additions at B2 and they are the ones that will fire first: the moment two " +
    "emitters are compared over one closed template, an emitter upgrade re-cutting the semantic " +
    "identity of PORT SUBSTITUTION becomes plainly wrong. None of the four holds today.",
  conformance_vectors: "WRITTEN AT B2. All three falsifiers in INSTANTIATION_FALSIFIERS are " +
    "WITNESSED, I-4c end to end through native execution.",
  no_film: "instantiation gets NO FILM. It is a deterministic RELATION, not a transition system, so " +
    "its instrument is independent RE-INSTANTIATION — the same argument that gives lowering " +
    "re-lowering rather than a film. This is a statement about the INSTRUMENT, not about the " +
    "relation's meaning, which is why it lives here and is not hashed.",
});

/** A reader's view. Not hashed; the two halves above are the sources. */
export const INSTANTIATION_SPEC = Object.freeze({
  semantics: INSTANTIATION_SEMANTICS, status: INSTANTIATION_STATUS });

/** THE DOMAIN OF THE REFINEMENT CLAIM, stated before anything is built so that
 *  B2's first green witness cannot quietly be read as more than it is. */
export const REFINEMENT_SCOPE = Object.freeze({
  holds_over: "canonical, fully bound input environments — every port the template declares has a " +
    "value in canonical_inputs, and instantiation succeeds",
  extra_inputs: "IN SCOPE: unused canonical inputs are ignored by both source and target, and the " +
    "witness includes one",
  declared_open: "SOURCE-REFUSAL <-> INSTANTIATION-REFUSAL. The source refuses a missing input as " +
    "program-input-missing:<name> during EVALUATION; instantiation refuses it as " +
    "instantiate-missing-input:<name> before any target term exists. Those are different layers, " +
    "different codes and different moments, and refinement over refusals is a separate theorem that " +
    "is not attempted here. Claiming refusal preservation without it would be the two-grades-of-" +
    "evidence mistake round 26 made about films.",
  // B7, and it is here to stop `emit-sub-underflow` being read as the item
  // above getting closed. It is not that item and it is not even that SHAPE.
  representable_only: "OUT OF SCOPE BY CONSTRUCTION: closed templates whose value, at the root or at " +
    "any subexpression, falls outside the target's non-negative naturals. Emission refuses them as " +
    "emit-sub-underflow and NO TARGET OUTCOME EXISTS, so there is nothing for the refinement equation " +
    "to have two sides of. THIS IS NOT REFUSAL PRESERVATION and must not be counted as progress on " +
    "the item above: for sub(2,3) the SOURCE DOES NOT REFUSE — it evaluates to -1, correctly — and " +
    "the compiler declines. The honest shape is `source language PROPERLY CONTAINS the representable " +
    "target fragment`, which is what a partial compiler is, and the pairing of a source refusal with " +
    "a target refusal remains untouched and open.",
});

/** THE CHAIN, MACHINE-READABLE, so the anti-collapse test cannot fall behind it.
 *
 *  lowering_check asserted that SIX identities stay distinct. B1.2 introduced
 *  target_template_sem_id as an independently identified semantic object and did
 *  not add it to that set, so the check went on proving a six-way distinctness
 *  about a seven-node chain — green, and one node short of what it claimed. That
 *  is a hand-typed count drifting from the thing it counts, which this tree has
 *  now watched happen to a law count, a case count, a rung count and a set.
 *
 *  So the count is not written down anywhere. The check DERIVES its set from
 *  this list, requires a value for every node marked exercised, and NAMES the
 *  unexercised ones in its output — because a node that is silently absent and a
 *  node that is declared absent are the difference between a stale instrument
 *  and a scoped one. B2 flips two flags here and the set grows by itself. */
export const REFINEMENT_CHAIN = Object.freeze([
  Object.freeze({ id: "program_sem_id", kind: "object", exercised: true,
    of: "the source program, committing the frozen core's semantics" }),
  Object.freeze({ id: "lowering_sem_id", kind: "relation", exercised: true,
    of: "source AST -> target template" }),
  Object.freeze({ id: "target_template_sem_id", kind: "object", exercised: true,
    of: "the parameterized template. ADDED TO THE CHAIN AT B1.2 AND TO THIS SET AT B1.2.1" }),
  Object.freeze({ id: "instantiation_sem_id", kind: "relation", exercised: true,
    of: "template + inputs -> closed executable term. EXERCISED AT B2: every term the witness " +
      "executes now reaches native code through instantiate(), because lower() no longer emits one." }),
  Object.freeze({ id: "inputs_sem_id", kind: "data", exercised: true,
    of: "one invocation's canonical inputs. EXERCISED AT B2, and it is what makes extras checkable: " +
      "{x:2,y:3} and {x:2,y:3,unused:999} have DIFFERENT inputs_sem_id and reach the SAME term." }),
  Object.freeze({ id: "closed_template_sem_id", kind: "object", exercised: true,
    of: "the invocation-CLOSED template. ADDED AT B2.1 when the emission split fired: its own " +
      "identity domain (ctmpl-) even where its bytes equal the open template's, because what the " +
      "compiler produced and what an invocation closed are different things" }),
  Object.freeze({ id: "emission_sem_id", kind: "relation", exercised: true,
    of: "closed template -> executable ic32 term. The only place an allocation exists" }),
  Object.freeze({ id: "target_term_sem_id", kind: "object", exercised: true,
    of: "the closed executable ic32 term, minted by the kernel and agreed by C" }),
  Object.freeze({ id: "target_nf_sem_id", kind: "object", exercised: true,
    of: "the canonical normal form the native runtime reached" }),
  Object.freeze({ id: "decode_sem_id", kind: "relation", exercised: true,
    of: "canonical signature -> structural outcome" }),
  Object.freeze({ id: "outcome_sem_id", kind: "object", exercised: true,
    of: "the outcome, where source and target must be EQUAL — the one coincidence the chain wants" }),
]);

/** The three falsifiers that must hold before `input` becomes executable
 *  semantics. Declared as DATA so B2 writes them against a frozen statement and
 *  so a future reader can see which of them exist — the alternative is a prose
 *  list that drifts from the suite, which this tree has now watched happen to a
 *  law count, a case count and a rung count. */
export const INSTANTIATION_FALSIFIERS = Object.freeze([
  Object.freeze({ id: "I-4a", name: "allocation-invariance", status: "WITNESSED",
    claim: "same source input name, different internal target variable allocation " +
      "(_impl17 vs q93) -> the SAME target_template_sem_id",
    proves: "the emitter's allocation is not semantic" }),
  Object.freeze({ id: "I-4b", name: "source-name-sensitivity", status: "WITNESSED",
    claim: "different source input names, same allocation strategy -> DIFFERENT " +
      "target_template_sem_id",
    proves: "the source input key IS semantic, so the quotient did not throw it away" }),
  Object.freeze({ id: "I-4c", name: "binding-has-force", status: "WITNESSED",
    claim: "x/y port binding swapped during instantiation -> the target term or outcome changes, or " +
      "is refused; and it must NEVER validate under the correct instantiation receipt",
    proves: "instantiation HONOURS the port identity rather than carrying it decoratively — " +
      "without this one, a and b prove only that a label is being copied around",
    // THE FIXTURE IS MANDATED, because the obvious one cannot fail. add(x, y)
    // with x=2, y=3 gives 5 under the correct binding and 5 under the swap:
    // addition is commutative, so a symmetric witness is green whether or not
    // the binding was honoured. That is a test whose output cannot reveal the
    // defect it is named for — the species this tree has caught four times.
    fixture: "add(input(\"x\"), add(input(\"x\"), input(\"y\"))) with x=2, y=3. Correct binding " +
      "evaluates to 7 and the x/y swap to 8, verified against the SOURCE evaluator, so the witness " +
      "reaches a different target term, a different native result and a different " +
      "target_outcome_sem_id rather than merely different target bytes.",
    fixture_is_mandatory: "a symmetric fixture such as add(input(\"x\"), input(\"y\")) is REFUSED " +
      "for this falsifier: 2+3 == 3+2, so it would pass under a swapped binding and prove nothing" }),
]);

/* ── LOWERING: the same split ────────────────────────────────────────────── */
export const LOWERING_SEMANTICS = Object.freeze({
  language: "TRVM-DERIVE-CORE",
  source_core_sem_id: CORE_SEM_ID,
  // THE CODOMAIN IS THE TEMPLATE, and naming its encoding BY ID is what makes
  // that a semantic commitment rather than a sentence in a header.
  //
  // `target_encoding: TARGET_ENCODING` was here until B1.2.1 and it was a
  // PRE-TEMPLATE LEFTOVER. Before B1.2, lower() produced ic32 text and the
  // executable encoding genuinely was lowering's codomain; B1.2 moved the
  // codomain onto the template, fixed the LoweringReceipt one declaration
  // below, and left this line pointing two layers downstream. The consequence
  // was measured: changing the add combinator moved LOWERING_SEM_ID, so every
  // LoweringReceipt ever issued was re-identified by a change to a relation
  // lowering does not perform.
  codomain: "TRVM-TARGET-TEMPLATE-v1",
  target_template_encoding_sem_id: TARGET_TEMPLATE_ENCODING_SEM_ID,
  // THE PER-OP MAP, STRUCTURAL AND INTERPRETED. Removing target_encoding at
  // B1.2.1 exposed that it had been standing in for rules that were never
  // stated: `lowered_ops` says WHICH ops lower and the template encoding says
  // what the codomain's nodes ARE, but nothing said that a const becomes a
  // church node, so const(n) -> church(n+1) contradicted no sentence.
  //
  // B1.2.1 wrote them as ENGLISH and GPT ruled that insufficient for the same
  // reason the codomain-in-prose was: a normative sentence beside a hand-coded
  // implementation is TWO artifacts that can disagree, and only one of them is
  // hashed. So `lower()` INTERPRETS this table. The specification and the
  // implementation are now the SAME OBJECT — a rule cannot be edited without
  // changing behaviour, and behaviour cannot be changed without moving
  // LOWERING_SEM_ID. Measured in lowering_check: mutating a rule moves the id
  // AND the emitted template, together, every time.
  //
  // `transform: "identity"` on the port's source_name is INPUT_PORT_SPEC's
  // no-normalization ruling made structural. It was a sentence saying names are
  // not Unicode-normalized; it is now the absence of any other transform in a
  // table the compiler reads, which is a much harder thing to violate by
  // accident. This closes most of B1.1's declared-open brittleness: the rules
  // no longer move an identity when reworded, because there is no prose left in
  // them to reword. It does NOT close all of it — `substitution` and
  // `dup_label_policy` are still English elsewhere.
  // THE VOCABULARY'S MEANING, CONTENT-BOUND. B2 gave rules a CLOSED set of
  // predicate and transform NAMES and stopped there, which left exactly the
  // defect B1.2.1 removed from emit(): a semantic dependency behind a symbol.
  // GPT measured it — change `integer` from Number.isInteger to () => true and
  // const(1.5) lowers successfully instead of refusing, with LOWERING_SEM_ID
  // UNCHANGED. `identity` was worse: it could have been made to normalize a
  // source input name, silently undoing the no-normalization ruling.
  //
  // So the vocabulary stays closed AND its definitions are data. A rule names
  // `integer`; `integer` IS {kind:"number-is-integer"}; the interpreter
  // implements a handful of kinds. Changing what a name means now means editing
  // these bytes, which moves the id.
  //
  // WHERE THE TRUST BOUNDARY NOW SITS, stated rather than implied: the KIND
  // INTERPRETER is trusted code, like canonicalBytes and emit(). What has been
  // removed is the rule LANGUAGE's ability to hide meaning; what remains is the
  // ordinary trust every implementation of a specification requires. A rule may
  // NOT name a predicate by JavaScript reference or by a bare string resolved
  // elsewhere. When the core exports reusable semantic predicates, a rule
  // references one by its predicate_sem_id and this record commits to that id.
  predicate_semantics: Object.freeze({
    integer: Object.freeze({ kind: "number-is-integer" }),
    nonnegative: Object.freeze({ kind: "number-compare", operator: ">=", rhs: 0 }),
  }),
  transform_semantics: Object.freeze({
    identity: Object.freeze({ kind: "identity" }),
  }),
  op_lowering_rules: Object.freeze({
    const: Object.freeze({
      source_op: "const",
      preconditions: Object.freeze([
        Object.freeze({ field: "value", holds: "integer", refusal: "lower-non-integer-constant" }),
        Object.freeze({ field: "value", holds: "nonnegative", refusal: "lower-negative" }),
      ]),
      target: Object.freeze({ t: "church", n: Object.freeze({ from_field: "value" }) }),
    }),
    add: Object.freeze({
      source_op: "add",
      preconditions: Object.freeze([]),
      // OPERAND ORDER IS THE FIELD ORDER OF THIS RECORD's targets, a then b,
      // which is the core's own evaluation order. Swapping them here swaps the
      // emitted template, because this table is what runs.
      target: Object.freeze({ t: "add",
        a: Object.freeze({ recurse_field: "a" }), b: Object.freeze({ recurse_field: "b" }) }),
    }),
    // B7. STRUCTURALLY IDENTICAL TO add's RULE, AND THAT IS THE CLAIM: lowering
    // a subtraction is a rename of the node tag and nothing else. It has NO
    // preconditions — sub(2,3) lowers, and must, because the source language
    // evaluates it to -1 and the compiler's inability to represent that is a
    // fact about the codomain which this relation does not reach. A
    // precondition here would be `lower-negative` under another name, and it
    // could not even be written for sub(input x, input y), which has no
    // underflow fact until an invocation binds the ports.
    sub: Object.freeze({
      source_op: "sub",
      preconditions: Object.freeze([]),
      // OPERAND ORDER IS THIS RECORD'S FIELD ORDER, a then b, and unlike add's
      // it is not recoverable from the result: swapping these two swaps the
      // meaning rather than preserving it.
      target: Object.freeze({ t: "sub",
        a: Object.freeze({ recurse_field: "a" }), b: Object.freeze({ recurse_field: "b" }) }),
    }),
    // B8.2. add's rule with the tag renamed, again — and this time the ONLY
    // reason it is not literally a copy is the tag. `mul` has no precondition
    // and needs none: the target represents every product of two non-negative
    // naturals it can represent an operand of.
    mul: Object.freeze({
      source_op: "mul",
      preconditions: Object.freeze([]),
      target: Object.freeze({ t: "mul",
        a: Object.freeze({ recurse_field: "a" }), b: Object.freeze({ recurse_field: "b" }) }),
    }),
    input: Object.freeze({
      source_op: "input",
      preconditions: Object.freeze([]),
      target: Object.freeze({ t: "port",
        source_name: Object.freeze({ from_field: "name", transform: "identity" }) }),
    }),
  }),
  // THE FULL SOURCE FRAGMENT, `input` INCLUDED. B1 left `input` out of the
  // hashed semantics, so B2 adding it would have moved LOWERING_SEM_ID — which
  // is precisely what B1.1 set out to make impossible. The rule is frozen here
  // and the implementation is absent; those are different facts and only the
  // first one is hashed.
  lowered_ops: Object.freeze(["const", "add", "input", "sub", "mul"]),
  inputs: Object.freeze({
    model: "template-then-instantiation",
    input_lowering_rule: "{op:\"input\", name:N} lowers to the structural template node " +
      "{t:\"port\", source_name:N}. N is carried through UNCHANGED — not normalized, not renamed, " +
      "not indexed — because the source key is semantic and the target's own naming is not.",
    ruling: "TWO LEVELS, TWO IDENTITIES. Lowering produces a PARAMETERIZED target TEMPLATE whose " +
      "identity is a function of the program alone; instantiation closes that template against " +
      "canonical inputs and produces the executable TERM. 'Parameterized versus instantiated' was a " +
      "false choice — the template is parameterized AND the executed term is necessarily closed.",
    template_identity_rule: "target_template_sem_id — a function of program_sem_id and " +
      "lowering_sem_id, reusable across invocations and independent of invocation data",
    executable_term_identity_rule: "target_term_sem_id — a function of target_template_sem_id, " +
      "instantiation_sem_id and inputs_sem_id",
    instantiation_sem_id_is_separate: true,
  }),
  // SEMANTIC refusals only, and only ones LOWER() CAN ACTUALLY PRODUCE.
  // `lower-input-not-implemented` is a STATUS refusal and lives in
  // LOWERING_STATUS: it says the code is unwritten, not that the language
  // refuses the op, and hashing it here would make implementing a frozen rule a
  // semantic event. `emit-unbound-port` and `template-malformed` were in this
  // list until B1.2.1 and are EMISSION's, now in INSTANTIATION_SEMANTICS —
  // neither is reachable from lower(), which emits only zero-port templates it
  // built itself, so lowering was claiming a refusal vocabulary it does not
  // have. Every name below is reachable, and lowering_check drives all four.
  refusal_semantics: Object.freeze(["lower-unsupported-op", "lower-non-integer-constant",
    "lower-negative", "lower-reads-undecided"]),
  totality: "lowering is TOTAL on the lowered fragment and REFUSES by name outside it. A lowering " +
    "that silently emitted something for an op it does not encode would make the refinement theorem " +
    "a statement about whatever it happened to emit.",
});

/** NOT hashed. Rounds, evidence grades, and whether the code exists. */
export const LOWERING_STATUS = Object.freeze({
  decided_at: "round 27, pass B1",
  semantics_corrected_at: "round 27, pass B1.1",
  codomain_corrected_at: "round 27, pass B1.2.1 — the executable encoding unbound from this relation",
  rules_made_structural_at: "round 27, pass B2 — op_lowering_rules is INTERPRETED by lower()",
  implemented_at: "round 27, pass B2",
  implemented: true,
  why_decided_before_implemented: "an unstated variable inside target_term_sem_id is the round-16 " +
    "hidden-identity bug class. Deciding this while writing `input` is how it gets in. The first " +
    "lowering witness used inputs={} and therefore decided nothing, which is why the decision is a " +
    "separate act rather than a consequence of the next commit.",
  falsifiers: "INSTANTIATION_FALSIFIERS — three, all WITNESSED at B2",
  refinement_scope: REFINEMENT_SCOPE,
  // NAMED AT B1.2.1, because the alternative is a code shape quietly
  // contradicting the record above it. Once emission belongs to the
  // INSTANTIATION relation, lower() calling emit() means lowering performs part
  // of instantiation — and lowering_check's whole refinement witness runs off
  // `low.target_term`, so the 12-case chain reaches native execution WITHOUT
  // passing through the relation whose identity this round just made
  // load-bearing. Nothing identity-bearing flows from the field: the
  // LoweringReceipt ends at the template and the term's id is minted by the
  // kernel. But it is a debt with a named closer, and B2's restatement of
  // add(2,3) through instantiate({}) is therefore MANDATORY rather than tidy.
  emission_debt: "PAID AT B2. lower() no longer returns `target_term` at all — the convenience field " +
    "was a SECOND PATH to an executable term beside the official one, and GPT ruled it out on the " +
    "rule this tree keeps re-learning: a mechanism built twice will disagree with itself, and every " +
    "future reader has to remember which copy carries the semantics. instantiate() is now the only " +
    "way to a term, including at the empty environment. The equality survives as a REGRESSION " +
    "THEOREM rather than an API: instantiate(template, {}) reproduces the exact 129 bytes the " +
    "shortcut used to return, with the same six-frame film, the same normal form and the same 5.",
});

/** The inputs model, as the batteries and the grid read it. Semantics live in
 *  LOWERING_SEMANTICS.inputs; the two lifecycle flags live here and are the
 *  reason this object is NOT hashed into any identity. */
export const INPUTS_MODEL = Object.freeze({
  decided: true,
  implemented: true,
  semantics: LOWERING_SEMANTICS.inputs,
  status: LOWERING_STATUS,
  why_two_relations: "a template can be perfectly lowered while instantiation binds \"x\" to the port " +
    "for \"y\". Merged, a target failure is ambiguous between a mistranslated program and correctly " +
    "translated code with miswired inputs. Separated, each is independently falsifiable.",
  receipt: "InstantiationReceipt {target_template_sem_id, instantiation_sem_id, inputs_sem_id, " +
    "closed_template_sem_id} then EmissionReceipt {closed_template_sem_id, emission_sem_id, " +
    "target_term_sem_id}, each verified by INDEPENDENT RECOMPUTATION of its own relation — and " +
    "verifying instantiation needs no runtime canonicaliser at all now that it ends at a structure " +
    "this module owns",
});

/** A reader's view. NOT hashed — LOWERING_SEMANTICS is what the id commits to. */
export const LOWERING_SPEC = Object.freeze({
  semantics: LOWERING_SEMANTICS, status: LOWERING_STATUS });

/** The identity of the RELATION. Content-bound, like every other id here: a
 *  bare "TRVM-LOWERING-v1" label would be a name anyone could claim, which the
 *  primitive ruling already refuses for `componentReachability`.
 *
 *  IT MOVED AT B1, AND THAT WAS RIGHT: deciding the inputs model changed what
 *  the relation MEANS, and an id surviving that ruling unchanged would claim the
 *  decision was not part of the relation.
 *
 *  IT MOVED AGAIN AT B1.1, AND THAT IS A FIX. v1 hashed the whole spec including
 *  lifecycle, so `implemented: false -> true` re-identified the relation. v2
 *  hashes LOWERING_SEMANTICS only, so B2 becoming BUILT cannot move it. */
export const LOWERING_SEM_ID =
  "lsem-" + H("TRVM-LOWERING-SEM-v2|" + canonicalBytes(LOWERING_SEMANTICS));

/** The identity of the INSTANTIATION relation — separate from lowering's,
 *  because they are separate relations. See INPUTS_MODEL.why_two_relations.
 *  Semantics only, for the reason above. */
export const INSTANTIATION_SEM_ID =
  "isem-" + H("TRVM-INSTANTIATION-SEM-v2|" + canonicalBytes(INSTANTIATION_SEMANTICS));

/** THE OVERBOUND B1 IDENTITIES, kept rather than erased. They were the honest
 *  ids of the projection B1 shipped, and a record that silently replaced them
 *  would be doing the thing this correction is about. Anything citing them cites
 *  a relation whose id was a function of round numbers and evidence prose. */
export const OVERBOUND_TRANSITIONAL_SEM_IDS = Object.freeze({
  note: "B1 (round 27) hashed the full spec, lifecycle fields included. Superseded at B1.1 by the " +
    "TRVM-*-SEM-v2 projections above, which hash semantics only.",
  lowering_sem_id_v1: "lsem-5673108765b400bc9abff5a7b7b8fcb4375cf9894c5dbd50201efec3df79ccbc",
  instantiation_sem_id_v1: "isem-c6b793933e30c1e6ad29dfd1cd1cc04c42c06858bea816bbe7750806626435a5",
  measured: "flipping only `implemented` moved lowering to lsem-63f98923ed13…; rewording only the " +
    "conformance-test STATUS sentence moved instantiation. Neither changed a rule.",
});

/** THE B1.2 IDENTITIES, kept for the same reason and superseded for a different
 *  one. B1.1's ids were overbound to LIFECYCLE. These were bound to the wrong
 *  CODOMAIN — lowering to the executable encoding two layers downstream,
 *  instantiation to no encoding at all — which is a defect of the same family
 *  and not the same instance, so it gets its own record rather than a sentence
 *  appended to the one above.
 *
 *  THE MEASUREMENT THAT CONDEMNED THEM, reproduced by GPT and again here:
 *  change TARGET_ENCODING.add and nothing else, and the executable term's bytes
 *  change while isem-bf9434fc…, the template id and the template-encoding id all
 *  stand still. lsem-d95ee1cb… moved — the wrong id, for the wrong reason. */
export const SUPERSEDED_CODOMAIN_SEM_IDS = Object.freeze({
  note: "B1.2 (round 27) bound LOWERING_SEMANTICS to TARGET_ENCODING and named INSTANTIATION's " +
    "codomain in prose. Superseded at B1.2.1: lowering commits to the TEMPLATE encoding plus its own " +
    "per-op rules, instantiation commits to TARGET_EXECUTABLE_ENCODING_SEM_ID.",
  lowering_sem_id_b12: "lsem-d95ee1cbc0e8f37806adf8fc9db377afc1e448ac05087254841e920651d76814",
  instantiation_sem_id_b12: "isem-bf9434fc751a2fb4cd2f6fb482afb13cd630a1b298a9faa232782f04ecb69441",
  measured: "mutating TARGET_ENCODING.add and nothing else moved lowering to lsem-39ec194a… and left " +
    "instantiation, the template id and the template-encoding id UNCHANGED, while the emitted term's " +
    "bytes differed. The relation whose codomain those bytes are had the same identity before and " +
    "after. GPT measured the same contradiction independently against a different mutation of the " +
    "same field (its lsem landed on 6e445936…), which is why the finding is the SHAPE and not the hex.",
});

/** THE B1.2.1 IDENTITIES, and this record claims NO DEFECT — which is the whole
 *  reason it is separate from the two above. Those ids were bound to lifecycle
 *  (B1) and to the wrong codomain (B1.2); these were bound correctly, to an
 *  ENGLISH expression of a correct map. B1.1 declared that brittleness open in
 *  the same breath as it fixed the lifecycle overbinding, and B2 closes most of
 *  it by making the rules structural and INTERPRETED.
 *
 *  Recorded because they are the values against which "implementing B2 moved
 *  neither id" has to be checked, and because a reader deserves to know which
 *  of the four generations was a correction and which was a refinement. */
/** THE B6 IDENTITIES, superseded at B6.1 for a reason none of the earlier
 *  supersessions had: not overbinding, not the wrong codomain, but a JUSTIFYING
 *  CLAIM THAT WAS FALSE ABOUT THE CODOMAIN ITSELF.
 *
 *  dup_label_policy said a different label assignment is a different encoding
 *  "because the label reaches the canonical signature". EMISSION_CONFORMANCE-v1
 *  measured the opposite on all eight fixtures — relabelling leaves
 *  target_term_sem_id identical — and the canonicaliser asserts it as a law
 *  (L-BYTES-1, byte-level equivariance under alpha and label permutation). So
 *  the encoding was claiming to distinguish something its own codomain erases.
 *
 *  THE MEASUREMENT THAT SCOPES THE MOVE, and it is an equation rather than an
 *  assertion: correcting only dup_label_policy moved TARGET_EXECUTABLE_ENCODING
 *  _SEM_ID and, through it, EMISSION_SEM_ID — and left LOWERING_SEM_ID,
 *  INSTANTIATION_SEM_ID, TARGET_TEMPLATE_ENCODING_SEM_ID and DECODE_SEM_ID
 *  EXACTLY where they were. The executable encoding's semantics changed and
 *  nothing else did, which is what makes this a correction rather than a
 *  re-cutting of the chain. */
export const SUPERSEDED_LABEL_SEMANTICS_SEM_IDS = Object.freeze({
  note: "B6 (round 27) justified the label allocation as semantic on the ground that labels reach " +
    "the canonical signature. B6's own conformance battery measured that they do not. Superseded at " +
    "B6.1: the encoding now commits to label EQUALITY AND FRESHNESS structure and says nothing about " +
    "the integers representing it.",
  emission_sem_id_b6: "esem-aab30fb53c6ce8944e2f6e0d5b5be1116d097d2fcae9af2790315f17ad3cb84e",
  target_executable_encoding_sem_id_b6:
    "xenc-7ce8f33f6c1efae199a53b0aaaf0b7064a7d7e592aecfaf199e2c27aa40dd2c5",
  measured: "correcting ONLY dup_label_policy moved these two and left lowering, instantiation, the " +
    "TEMPLATE encoding and decode byte-identical — so the round changed the executable encoding's " +
    "semantics and nothing else. The defect class is new to this line: not overbinding (B1.1) and " +
    "not the wrong codomain (B1.2), but a justification that was FALSE ABOUT THE CODOMAIN.",
});

/** THE B6.2 IDENTITIES, superseded at B6.3. Same defect FAMILY as B1.1 —
 *  non-semantic prose inside a hashed identity — and a different INSTANCE:
 *  B1.1's was governance prose (lifecycle, "what the project should do next"),
 *  this was EXPLANATORY prose, an accurate account of the proof architecture
 *  sitting inside the encoding it describes.
 *
 *  THE MEASUREMENT, reproduced by GPT and again here before anything was
 *  changed: rewording `three_grades` alone — the same claim, different
 *  sentence — moved TARGET_EXECUTABLE_ENCODING_SEM_ID and, through it,
 *  EMISSION_SEM_ID, while emitted bytes were identical on 9/9,
 *  target_term_sem_id was identical on 9/9, and all 11 conformance cases still
 *  passed. An identity moving with nothing behind it.
 *
 *  THE PROFILE ID MOVED IN THE SAME PASS FOR A DIFFERENT REASON, and it is not
 *  a supersession of the same kind: the profile's SHAPE changed — five
 *  sentences left it and two knobs joined it — so its id had to move. It is
 *  recorded here because a reader comparing B6.2's pack to this one will see
 *  three ids move and deserves to know which two were corrections and which
 *  one was a redefinition. */
export const SUPERSEDED_EXPLANATORY_PROSE_SEM_IDS = Object.freeze({
  note: "B6.2 (round 27) hashed `three_grades` — the bytes -> target term -> outcome ladder — and a " +
    "B6-era attribution sentence into TARGET_ENCODING. Both are true and neither is a property of " +
    "the executable encoding. Superseded at B6.3: the ladder is stated in this file's header, in " +
    "emission_conformance.mjs and in derivation.emission-conformance, none of which is hashed.",
  target_executable_encoding_sem_id_b62:
    "xenc-e6e411d71f8082f937b2440fe17407c2fc79d639a2ab60537c53cfee05cf7ba6",
  emission_sem_id_b62: "esem-67aba59f5d7b6717d6d77a16cf4e13aa6714d1a67970be2e64af8dcbad13b638",
  canonical_emitter_profile_id_b62:
    "cemp-bb6b7f163bbbcc1cb7597191e43d5042646bf40d22fcd59c4656e2598adaab77",
  measured: "rewording ONLY three_grades moved xenc and esem and left the TEMPLATE encoding, " +
    "lowering, instantiation and every emitted byte untouched — an identity moving for a change that " +
    "did nothing. The profile id moved separately and legitimately: label_alloc_order and " +
    "binder_names became knobs and five sentences became CANONICAL_EMITTER_PROFILE_NOTES. Across the " +
    "whole pass emitted bytes are IDENTICAL on 9/9 fixtures, which is what makes it a projection " +
    "correction rather than an emitter change.",
});

export const SUPERSEDED_PROSE_RULE_SEM_IDS = Object.freeze({
  note: "B1.2.1 hashed a correct map expressed in NORMATIVE ENGLISH. Superseded at B2 by the " +
    "structural op_lowering_rules that lower() interprets. NOT A DEFECT — no false verdict was " +
    "possible and no id was bound to anything it should not have been.",
  lowering_sem_id_b121: "lsem-84c9344790a0403975430d270e6d567f4124cf7f848761cf19e4f997bc330244",
  instantiation_sem_id_b121: "isem-6ac0ea7b0d1a2f2cf3d749072b5ac38d8a7f332f7b4b1b10c61b923f6cb03e39",
  why_each_moved: "lsem moved because op_lowering_rules became structural; isem moved because the " +
    "emission SPLIT TRIGGER left the hashed semantics for INSTANTIATION_STATUS. NEITHER moved because " +
    "code was written: implementing `input`, writing instantiate(), removing lower()'s target_term " +
    "and flipping every lifecycle flag move nothing, and lowering_check measures exactly that.",
});

/** THE B2 IDENTITIES. Kept because the revert-and-compare witness that used to
 *  reproduce them was retired at B2.1 when its premise expired, and a record
 *  whose only evidence was a deleted test should at least name the values.
 *
 *  NO DEFECT IS CLAIMED, on the same footing as the B1.2.1 generation: B2's ids
 *  were correctly bound. They moved because B2.1 content-bound the predicate
 *  vocabulary, split emission out into its own relation, and added the entry
 *  snapshot — three changes to what the relations MEAN, each ruled before it
 *  was made. */
export const SUPERSEDED_B2_SEM_IDS = Object.freeze({
  note: "B2 (round 27) hashed a lowering record whose predicate and transform vocabulary was a set " +
    "of bare NAMES, and an instantiation record whose relation included emission and permitted two " +
    "reads of the caller's inputs. Superseded at B2.1.",
  lowering_sem_id_b2: "lsem-2014bdc8add9981442b9bbf42672a00bc477eb2b23c38918b93fdc8d9f1a99a2",
  instantiation_sem_id_b2: "isem-481a1fbda7d5c2d0a0d5c9947bc8d56c29d5de2006d3fc31cb88bf94a630cfc2",
  why_each_moved: "lsem because predicate_semantics and transform_semantics were added — `integer` " +
    "was a name whose meaning lived in a JavaScript function body, so redefining it changed behaviour " +
    "and moved no id. isem because emission left the relation and the entry-snapshot obligation " +
    "joined it. Both are changes to MEANING, not to lifecycle.",
});

/** THE B6.3.1 IDENTITIES, and this is the FIRST SUPERSESSION IN THIS LINE WITH
 *  NOTHING WRONG BEHIND IT AT ALL. Every generation above moved for a defect or
 *  a re-expression: overbound to LIFECYCLE (B1.1), bound to the WRONG CODOMAIN
 *  (B1.2), a justification FALSE ABOUT THE CODOMAIN (B6), EXPLANATORY PROSE
 *  inside an encoding (B6.2), a correct map in ENGLISH made structural (B2).
 *  B7 moves four ids because THE THING THEY IDENTIFY GOT BIGGER — the fragment
 *  gained an operator — which is the reason a semantic identity is supposed to
 *  move, and the first time this chain has exercised it.
 *
 *  ONE OF THE FOUR CONTRADICTS THE ROUND'S OWN PREDICTION, and it is recorded
 *  as a disagreement rather than quietly reconciled. B7's brief predicted
 *  TARGET_EXECUTABLE_ENCODING_SEM_ID would STAND STILL, on the reasoning that
 *  `sub` is a compiler/template growth. It cannot stand still: the executable
 *  encoding is what says how a target construct becomes an interaction-net
 *  term, and B7 gives it a construct it did not have. An xenc- that did not
 *  move here would be B1.2.1's UNDER-BOUND defect exactly — the identity of the
 *  encoding standing still across a change to the bytes that encoding produces.
 *
 *  MEASURED, NOT ARGUED: delete precisely B7's three additions from the live
 *  TARGET_ENCODING — `sub`, `domain`, `saturation` — and drop
 *  `emit-sub-underflow` from its refusal list, and the recomputed id is the
 *  B6.3.1 value below, to the byte. So the move is attributable to those four
 *  edits and to nothing else that drifted this round. emission_conformance.mjs
 *  runs that subtraction as a case rather than leaving it a claim. */
export const SUPERSEDED_PRE_SUB_SEM_IDS = Object.freeze({
  note: "B6.3.1 (round 27) identified a target fragment of church and add. B7 widened it with `sub` " +
    "and stated the codomain's domain. NO DEFECT IS CLAIMED in either direction: these ids were " +
    "correct for the fragment they identified, and they are not correct for this one.",
  target_executable_encoding_sem_id_b631:
    "xenc-69a5ffbf44ba0eaa20bd5668fa49c4af83a0e5feeaa3775859719cbfa1c45bc1",
  target_template_encoding_sem_id_b631:
    "tenc-b4b5c4a403b908f77e64c8d5a0b468cd13969c4790418694e6fecabff9e35c14",
  lowering_sem_id_b631: "lsem-51fda904a5a9486e75078640cfe4fd9d5ae69559ac1bc473c3f41ad7dbfa17ee",
  instantiation_sem_id_b631: "isem-7418dc41caefbc4e00abd4ab8563e2301947a11040aea59c5920b249e8c38e9f",
  emission_sem_id_b631: "esem-b6958270b2e50dd02a12869d4c55f8968eec7a43a9b2ab8ff4efeeadd12738b5",
  canonical_emitter_profile_id_b631:
    "cemp-c546742f9876a758624330ba6f10ed9472800d04a1d6a54e9345ff87e61369b0",
  stood_still: "CORE_SEM_ID and DECODE_SEM_ID, and both matter. The core already had `sub` as true " +
    "IEEE-754 subtraction, so nothing about the SOURCE LANGUAGE changed and no program was " +
    "re-identified. The decoder already read Church numerals out of a canonical signature, and a " +
    "subtraction's normal form is a Church numeral, so it needed no widening either.",
  measured: "removing exactly TARGET_ENCODING.sub, .domain, .saturation and the `emit-sub-underflow` " +
    "refusal from the LIVE object reproduces xenc-69a5ffbf… byte for byte. The profile id moved for a " +
    "separable reason — binder_names gained `pred`, which is a VALUE emit() reads — and would have " +
    "moved for that alone.",
});

/** THE B7 IDENTITIES, superseded ONE PASS LATER, and the reason is that B7 drew
 *  the wrong conclusion from its own correct measurement.
 *
 *  B7 observed TARGET_EXECUTABLE_ENCODING_SEM_ID move when `sub` landed and
 *  defended the movement: the executable encoding is what says how a construct
 *  becomes an interaction-net term, so a new construct must move it. GPT ruled
 *  otherwise and the ruling is right. B1.2.1's shape is
 *
 *      relation identity = domain encoding + codomain encoding + THE MAP
 *
 *  and `sub` added NO executable constructor and NO runtime rule — B7's own
 *  measurement says so in as many words. It added a macro expanded into
 *  Var/Lam/App/Dup/Sup/Era, and a macro is not a widening of the language it
 *  expands into. There is no SUB node in the runtime; `sub` does not survive
 *  emission at all.
 *
 *  SO THE MOVEMENT WAS REAL AND ITS CAUSE WAS NOT `sub`. The Church expansion,
 *  the combinators, the operand order, the codomain restriction and the emission
 *  refusals were all sitting inside the CODOMAIN's identity, and every one of
 *  them belongs to the MAP. That is B1.2.1's OVER-BINDING defect — in the field
 *  B1.2.1 created to fix UNDER-binding, which is why it survived the pass that
 *  went looking for exactly this.
 *
 *  WHAT THE SPLIT BUYS, and it is a capability rather than tidiness: after
 *  B7.1r, `mul` must move tenc/lsem/isem/esem and leave xenc EXACTLY where it
 *  is — unless it needs a genuinely new executable constructor or calculus rule,
 *  in which case xenc moving is the SIGNAL. An id that moves for every addition
 *  to the compiler's library cannot answer that question. E-2f measures both
 *  directions against a synthetic `mul` rule, so the property is established
 *  before `mul` exists rather than discovered by it.
 *
 *  AND THE TEMPLATE ENCODING CARRIED THE SAME LEAK IN MINIATURE. B7's `sub`
 *  node stated that the target application order is inverted and that the
 *  inversion happens inside emit(); B7.1r scrubbed it, and the STRUCTURAL check
 *  written to enforce the scrub immediately found the same leak in the `add` and
 *  `church` nodes, in `determinism`, and in a refusal list — four more places
 *  the round had not been asked to look. Repairing only what the ruling named
 *  would have left the neighbours exactly as exposed, which is B6.3.1's finding
 *  about a table and its next helper. */
export const SUPERSEDED_MAP_IN_CODOMAIN_SEM_IDS = Object.freeze({
  note: "B7 (round 27) hashed the emission MAP — Church expansion, add and sub combinators, operand " +
    "order, codomain restriction and emission refusals — inside TARGET_ENCODING, and the template " +
    "encoding described the emitter's realization of a sub. Superseded at B7.1r: the map is " +
    "EMISSION_RULES with its own id, EMISSION_SEMANTICS names it as its third term, and " +
    "TARGET_ENCODING describes only what is true of an executable ic32 term.",
  target_executable_encoding_sem_id_b7:
    "xenc-f422ea284b059efbb1a2ec21fbf8e33c0e5c3ba0e6dc85bcbfe8dd8fdb8fa3c9",
  target_template_encoding_sem_id_b7:
    "tenc-48c966690d24033e4a3ec36cbe98b4b3e0e26cb0e21d18e05dee00b2b1b0b25f",
  correction: "B7's brief argued the xenc- movement was correct and necessary. IT WAS NEITHER. The " +
    "movement was a genuine finding and the finding was about OVER-BINDING, not about `sub`. Both " +
    "records are kept because a round that defended the wrong decomposition and a round that fixed " +
    "it are different facts, and the first one is the more useful to a later reader.",
  measured: "E-2f: a synthetic `mul` rule moves EMISSION_RULES_SEM_ID and EMISSION_SEM_ID while " +
    "TARGET_EXECUTABLE_ENCODING_SEM_ID stands still; adding an executable CONSTRUCTOR moves it, and " +
    "so does changing the alpha/label QUOTIENT. Both directions, and the recomputation reproduces " +
    "all three live ids before mutating anything.",
});

/** The identity of a particular INVOCATION's inputs. This is where `x=5` lives,
 *  and it is deliberately not inside INSTANTIATION_SEM_ID: one names the rule,
 *  the other names the data the rule was applied to. Same shape as programSemId
 *  and grantId — one canonical traversal, no second read — and like them it is
 *  called on data the authority already owns. */
export const inputsSemId = (inputs) => "insem-" + H("TRVM-INPUTS-v1|" + canonicalBytes(inputs));

/** The port's target-side identity: a function of the SOURCE NAME, never of the
 *  emitter's allocation. Defined here so B2's falsifiers have something to be
 *  falsified against; nothing calls it yet. */
export const portSemId = (source_name) =>
  "psem-port-" + H(INPUT_PORT_SPEC.namespace + "|" + canonicalBytes(source_name));

/** The receipt SHAPE, frozen; the verifier is B2's work. Named fields rather
 *  than a tuple because a receipt whose positions carry meaning is a receipt
 *  that can be read wrong. */
export const INSTANTIATION_RECEIPT_FIELDS = Object.freeze([
  "target_template_sem_id", "instantiation_sem_id", "inputs_sem_id", "closed_template_sem_id"]);

/** INSTANTIATION, which now ENDS AT THE CLOSED TEMPLATE. Emission is a separate
 *  relation from B2.1 — see EMISSION_SEMANTICS.
 *
 *  BOTH ARGUMENTS ARE SNAPSHOT AT ENTRY, and B2 did not do this. GPT's find,
 *  reproduced here: `instantiate` read the caller's `inputs` twice — once to
 *  bind values into the term and once to compute `inputs_sem_id` — so a getter
 *  returning 2 and then 999 produced a term meaning x=2 beside an identity
 *  committing to {x:999}. The relation misbound its own input identity while
 *  nothing about the runtime was wrong.
 *
 *  That is round 27A.1's entry-snapshot rule arriving in the compiler layer, and
 *  the mechanism is the same one: ONE canonical snapshot at entry, everything
 *  downstream reads the snapshot. The template is snapshot too, because this
 *  function is exported and walks it three times.
 *
 *  THE INVARIANT: the bytes `inputs_sem_id` identifies are exactly the bytes
 *  from which every substituted value was derived. */
export function instantiate(template, inputs) {
  try {
    if (!inputs || typeof inputs !== "object" || Array.isArray(inputs))
      throw new Error("instantiate-inputs-not-canonical");
    const tmpl = ownCanonical(template);
    const own = ownCanonical(inputs);
    // CONSUMED, not SUPPLIED. The port set comes from the TEMPLATE, so an input
    // the template has no port for cannot participate — which is how extras are
    // ignored structurally rather than by a filtering step someone could forget.
    const consumed = templatePorts(tmpl);
    const bound = Object.create(null);
    for (const name of consumed) {
      if (!Object.prototype.hasOwnProperty.call(own, name))
        throw new Error("instantiate-missing-input: " + name);
      // A VALUE IS EMBEDDED BY THE SAME ENCODING A CONSTANT OF ITS TYPE GETS.
      // Not a second encoding for inputs: a value that lowered differently from
      // the constant it equals would make refinement depend on where a number
      // entered the program.
      const v = own[name];
      if (!Number.isInteger(v) || v < 0)
        throw new Error("instantiate-unencodable-input: " + name);
      bound[name] = T.church(v);
    }
    // SIMULTANEOUS substitution: one walk, every port replaced from `bound`,
    // so a value containing a port could not capture one. (No value can today —
    // integers only — and doing it in one pass is what keeps that true when
    // they can.)
    const subst = (n) => {
      if (n.t === "port") return bound[n.source_name];
      if (n.t === "church") return T.church(n.n);
      if (n.t === "add") return T.add(subst(n.a), subst(n.b));
      // B7. INSTANTIATION DOES NOT CHECK REPRESENTABILITY, and that is a
      // ruling. `sub(input x, input y)` closed with {x:2,y:5} is a perfectly
      // well-formed closed template of a program that is perfectly well-formed;
      // what has no image is its EMISSION. Refusing here would put a codomain
      // fact in the relation that closes ports, and would leave the closed
      // template — the thing a receipt identifies — unbuildable for a case the
      // compiler needs to be able to name.
      if (n.t === "sub") return T.sub(subst(n.a), subst(n.b));
      if (n.t === "mul") return T.mul(subst(n.a), subst(n.b));
      throw new Error("template-malformed: " + String(n.t));
    };
    const closed = subst(tmpl);
    // The CLOSED TEMPLATE's id is computed here, and the TERM's is not. A
    // structure this module owns and canonicalises may be identified by it; the
    // bytes a runtime executes may not. Same line lower() draws.
    return { ok: true, closed_template: closed,
      closed_template_sem_id: closedTemplateSemId(closed),
      inputs_sem_id: inputsSemId(own), consumed_inputs: consumed };
  } catch (e) { return { ok: false, reason: e.message }; }
}

/** THE APPLICATION RECORD FOR INSTANTIATION, and the reason it takes
 *  `target_term_sem_id` as an ARGUMENT rather than computing it.
 *
 *  GPT's B2 constraint, and it is the same discipline `loweringReceipt` already
 *  follows: the runtime owns the identity of the thing it executes. An
 *  `instantiate()` that emitted bytes and then certified their semantic id would
 *  be grading its own homework — the certificate and the artifact would come from
 *  one source, so a wrong emission would carry a matching id and verify. The id
 *  must be minted by the kernel's canonicaliser from the bytes, and only then
 *  does a receipt get built around it.
 *
 *  THIS COMMENT WAS ONE RELATION BEHIND. It drew instantiation producing "closed
 *  term BYTES" and needing the runtime canonicaliser — the pre-B2.1 world, before
 *  the split trigger fired. The implementation was correct and its own
 *  explanation described the previous architecture, which is the staleness class
 *  this file has now been caught on three times. The current shape:
 *
 *      instantiate(template, inputs) ──▶ CLOSED TEMPLATE
 *                                              │  this module owns and
 *                                              │  canonicalises it, so it may
 *                                              ▼  identify it
 *                                        closed_template_sem_id
 *                                              │
 *                                              ▼  instantiationReceipt(…)
 *
 *  and the runtime canonicaliser is EMISSION's business, one relation down.
 *  Verification re-instantiates and compares — never asks the instantiator
 *  whether it agrees with itself, and no longer needs a runtime oracle at all. */
export function instantiationReceipt(target_template_sem_id, inputs_sem_id, closed_template_sem_id) {
  const receipt = { target_template_sem_id, instantiation_sem_id: INSTANTIATION_SEM_ID,
    inputs_sem_id, closed_template_sem_id };
  for (const f of INSTANTIATION_RECEIPT_FIELDS)
    if (receipt[f] === undefined) throw new Error("instantiation-receipt-incomplete: " + f);
  return Object.freeze({ ...receipt,
    instantiation_receipt_id: "irec-" + H("TRVM-INSTANTIATION-RECEIPT-v1|" + canonicalBytes(receipt)) });
}

/** THE APPLICATION RECORD FOR EMISSION. Unlike instantiation's, this one takes
 *  `target_term_sem_id` from OUTSIDE, because it is the identity of bytes a
 *  runtime executes and emission may not certify its own output. */
export function emissionReceipt(closed_template_sem_id, target_term_sem_id) {
  const receipt = { closed_template_sem_id, emission_sem_id: EMISSION_SEM_ID, target_term_sem_id };
  for (const f of EMISSION_RECEIPT_FIELDS)
    if (receipt[f] === undefined) throw new Error("emission-receipt-incomplete: " + f);
  return Object.freeze({ ...receipt,
    emission_receipt_id: "erec-" + H("TRVM-EMISSION-RECEIPT-v1|" + canonicalBytes(receipt)) });
}

/* ── THE VERIFIERS, as production functions ───────────────────────────────
   B2 verified receipts inside lowering_check and nowhere else, so the only
   implementation of "does this receipt hold?" was test code — a relation whose
   verification procedure exists only in its own test suite is a relation
   nobody else can check. GPT's find.

   AND THE SPLIT MADE THEM CLEANER, which is an argument for the split rather
   than a consequence of it: verifying instantiation needs NO runtime
   canonicaliser at all, because the relation now ends at a structure this
   module owns. Only emission needs one, and it takes it as a parameter rather
   than importing a kernel — the module that defines the relation must not also
   choose the oracle that judges it. */

/* ── THE VERIFIERS OWN THEIR ARGUMENTS, and B2.1's first version did not ──
   GPT's find against B2.1, reproduced before repair. B2.1 fixed *the relation*
   may not bind one snapshot and identify another, and then wrote a verifier
   that did the same thing one layer up: **the proof checker may not verify one
   snapshot and authenticate another.**

   verifyInstantiationReceipt called instantiate(), which snapshots the template
   internally, and then called targetTemplateSemId(ownCanonical(template)) — a
   SECOND traversal of the caller's object. A template whose source_name answers
   "x" then "y" therefore satisfied a receipt claiming

       target_template_sem_id = identity of port("y")
       inputs_sem_id          = identity of {x:2}
       closed_template_sem_id = identity of church(2)

   which NO single immutable template satisfies: port("x") with {x:2} gives
   church(2), and port("y") with {x:2) refuses as instantiate-missing-input.
   The verifier returned ok:true because the first traversal supplied the
   instantiation half and the second supplied the source-identity half.
   verifyEmissionReceipt had the identical defect across its two ownCanonical
   calls.

   THE RECEIPT IS UNTRUSTED TOO and is snapshot with the rest: it arrives from
   whoever is asking to be believed, and a receipt whose fields answer
   differently on successive reads is the same attack wearing the other hat.

   The *Owned suffix is the round-27A.2 convention and it is a PRECONDITION:
   those functions may only be handed authority-owned data, and they never reach
   back to a caller object. A relation-verifier TOCTOU, not a supplier rung. */

/** Re-instantiate independently and compare. No target canonicaliser needed. */
export function verifyInstantiationReceipt(template, inputs, receipt) {
  let owned;
  try { owned = [ownCanonical(template), ownCanonical(inputs), ownCanonical(receipt)]; }
  catch (e) { return { ok: false, reason: "verify-instantiation-not-canonical: " + e.message }; }
  return verifyInstantiationReceiptOwned(...owned);
}

/** PRECONDITION: every argument is already an authority-owned snapshot. */
export function verifyInstantiationReceiptOwned(template, inputs, receipt) {
  const again = instantiate(template, inputs);
  if (!again.ok) return { ok: false, reason: "verify-instantiation-refused: " + again.reason };
  if (receipt?.instantiation_sem_id !== INSTANTIATION_SEM_ID)
    return { ok: false, reason: "verify-instantiation-relation-mismatch" };
  // the SAME owned template the instantiation above consumed — never a second
  // ownCanonical of whatever the caller is still holding
  for (const [f, got] of [
    ["target_template_sem_id", targetTemplateSemId(template)],
    ["inputs_sem_id", again.inputs_sem_id],
    ["closed_template_sem_id", again.closed_template_sem_id]])
    if (receipt[f] !== got) return { ok: false, reason: "verify-instantiation-mismatch: " + f };
  return { ok: true, closed_template: again.closed_template };
}

/* ── THE EMISSION VERDICT IS RELATIVE TO AN ORACLE, and the name says so ──
   B2.1.1 named this `verifyEmissionReceipt` and returned {ok:true}, which reads
   as an absolute judgment. It is not. GPT's find:

       verifyEmissionReceipt(T.church(2),
         emissionReceipt(closedTemplateSemId(T.church(2)), "deadbeef"),
         () => "deadbeef")                              →  { ok: true }

   The receipt claims the emitted term's identity is `deadbeef`, and it verifies,
   because the caller supplied an oracle that agrees. What the function proves is
   *this receipt verifies AGAINST THIS CANONICALISER* — a perfectly good
   parametric judgment, and a dangerous thing to spell like an absolute one in a
   tree whose recurring finding is that a claimant must not nominate the oracle
   that certifies the claim.

   NOT A RUNG: no authority takes this function from an untrusted claimant and
   turns its result into a verdict. The repair is the SHAPE, before something
   does. `Against` in the name, and `makeEmissionVerifier` for the composition
   root to bind the trusted canonicaliser ONCE so ordinary callers cannot pass
   one at all. The relation module still does not choose the judge; the trusted
   root does, which is where every other oracle in this tree is chosen.

   NO ALIAS is kept for the old name. An alias would be a second path to the
   same relation with the weaker spelling still available — the defect B2 removed
   from lower(). */

/** Re-emit independently and compare AGAINST A SUPPLIED ORACLE. The verdict is
 *  relative to `canonicaliseTarget`; prefer a verifier bound by
 *  makeEmissionVerifier at a trusted composition root. */
export function verifyEmissionReceiptAgainst(closed_template, receipt, canonicaliseTarget) {
  // the canonicaliser is a CAPABILITY the caller grants, not data to snapshot —
  // the module defining a relation must not choose the oracle that judges it
  if (typeof canonicaliseTarget !== "function")
    return { ok: false, reason: "verify-emission-no-canonicaliser" };
  let owned;
  try { owned = [ownCanonical(closed_template), ownCanonical(receipt)]; }
  catch (e) { return { ok: false, reason: "verify-emission-not-canonical: " + e.message }; }
  return verifyEmissionReceiptOwnedAgainst(owned[0], owned[1], canonicaliseTarget);
}

/** Bind the trusted target canonicaliser ONCE, at a composition root that is
 *  entitled to choose it, and hand out a two-argument verifier. Ordinary code
 *  then cannot supply an oracle, because there is no parameter for one. */
export function makeEmissionVerifier({ canonicaliseTarget }) {
  if (typeof canonicaliseTarget !== "function")
    throw new Error("emission-verifier-no-canonicaliser");
  const bound = canonicaliseTarget;
  return Object.freeze((closed_template, receipt) =>
    verifyEmissionReceiptAgainst(closed_template, receipt, bound));
}

/** PRECONDITION: closed_template and receipt are already owned snapshots. */
export function verifyEmissionReceiptOwnedAgainst(closed_template, receipt, canonicaliseTarget) {
  if (receipt?.emission_sem_id !== EMISSION_SEM_ID)
    return { ok: false, reason: "verify-emission-relation-mismatch" };
  let term;
  try { term = emit(closed_template); }
  catch (e) { return { ok: false, reason: "verify-emission-refused: " + e.message }; }
  // ONE owned value behind both the emission and the identity
  if (receipt.closed_template_sem_id !== closedTemplateSemId(closed_template))
    return { ok: false, reason: "verify-emission-mismatch: closed_template_sem_id" };
  if (receipt.target_term_sem_id !== canonicaliseTarget(term))
    return { ok: false, reason: "verify-emission-mismatch: target_term_sem_id" };
  return { ok: true, target_term: term };
}

/* ── the lowering ─────────────────────────────────────────────────────────── */

/** THE CLOSED ENUM label_alloc_order ranges over, interpreted: true means the
 *  add's own label is drawn BEFORE its operands are walked. A table rather than
 *  a string comparison so that an unknown value is a lookup miss and therefore
 *  a NAMED refusal — never a silent default, which is `evalPredicate`'s rule
 *  since B2.1 and for the same reason.
 *
 *  THE TABLE LIVES INSIDE THE FUNCTION, and that is B6.3.1 rather than a style
 *  choice. At B6.3 it was a module-level `LABEL_ALLOC_ORDERS` const that emit()
 *  read and that CANONICAL_EMITTER_ARTIFACT_ID did not hash, so GPT flipped one
 *  boolean in it — `"operands-then-node": false -> true`, profile untouched —
 *  and the emitted bytes moved on 5 of 9 fixtures while the closed template,
 *  the profile id AND the artifact id all stood still. E-1b's three stated
 *  preconditions all held and its byte conclusion was false.
 *
 *  Inside the function, `toString()` captures it, so the dependency is
 *  ELIMINATED rather than tracked. The general rule, which E-2e now enforces
 *  by derivation instead of by care: IF CHANGING A PIECE OF IMPLEMENTATION CAN
 *  CHANGE EMITTED BYTES WHILE THE TEMPLATE AND PROFILE STAY FIXED, THAT PIECE
 *  BELONGS TO THE EMITTER ARTIFACT IDENTITY. */
function labelAllocPreOrder(order) {
  const ORDERS = { "operands-then-node": false, "node-then-operands": true };
  return Object.prototype.hasOwnProperty.call(ORDERS, order) ? ORDERS[order] : undefined;
}

/** Linear Church numeral. n uses f exactly n times, so n-1 dups.
 *  BINDER NAMES COME FROM THE PROFILE (B6.3) — `f`, `x`, `a`, `t` were literals
 *  here while the profile claimed to own binder spelling. */
function church(n, labels, B, rule) {
  // THE KIND IS DISPATCHED ON, WITH A NAMED REFUSAL. B7.1r: the expansion is a
  // loop and stays code, but WHICH expansion is a value this function reads, so
  // an unknown kind is a lookup miss rather than a silent default — the
  // evalPredicate discipline since B2.1, and the labelAllocPreOrder discipline
  // since B6.3.1.
  if (rule?.kind !== "linear-church")
    throw new Error("emission-rule-unknown-kind: church " + String(rule?.kind));
  const [F, X] = B[rule.binders];
  const [HEAD, TAIL] = B[rule.dup_binders];
  if (n === 0) return fill(rule.zero, { F, X });
  if (n === 1) return fill(rule.one, { F, X });
  const binds = [];
  let cur = F;
  for (let i = 0; i < n - 1; i++) {
    const L = labels.next();
    if (i < n - 2) { binds.push(`!&${L}{${HEAD}${i},${TAIL}${i}}=${cur};`); cur = `${TAIL}${i}`; }
    else binds.push(`!&${L}{${HEAD}${i},${HEAD}${i + 1}}=${cur};`);
  }
  let body = X;
  for (let i = n - 1; i >= 0; i--) body = `(${HEAD}${i} ${body})`;
  return `λ${F}.λ${X}.${binds.join("")}${body}`;
}

/** {slot} substitution for the combinator SHAPES in EMISSION_RULES. Refuses an
 *  unfilled slot by name rather than emitting a literal brace — an emitter that
 *  silently shipped `{B7}` would produce a term that parses as an application
 *  of free names and normalises to something. */
function fill(shape, slots) {
  const out = String(shape).replace(/\{([A-Za-z0-9_]+)\}/g, (m, k) =>
    Object.prototype.hasOwnProperty.call(slots, k) ? slots[k] : m);
  const left = /\{[A-Za-z0-9_]+\}/.exec(out);
  if (left) throw new Error("emission-rule-unfilled-slot: " + left[0]);
  return out;
}

/** A combinator rule's SHAPE, with its binder slots and labels filled from the
 *  profile and the counter. B7.1r replaces ADD_COMBINATOR and PRED_COMBINATOR:
 *  the shapes were code, so changing a combinator changed the bytes and moved
 *  only cema-. They are values EMISSION_SEM_ID hashes now. */
function combinator(rule, labels, B) {
  if (rule.kind !== "combinator")
    throw new Error("emission-rule-unknown-kind: " + String(rule.kind));
  const slots = {};
  (B[rule.binders] ?? []).forEach((nm, i) => { slots["B" + i] = nm; });
  if (rule.dup_binders) (B[rule.dup_binders] ?? []).forEach((nm, i) => { slots["D" + i] = nm; });
  for (let i = 0; i < (rule.labels ?? 0); i++) slots["L" + i] = String(labels.next());
  return fill(rule.shape, slots);
}

/* ADD_COMBINATOR and PRED_COMBINATOR WERE HERE UNTIL B7.1r, as arrow functions
   building their shapes in code. That made every combinator a property of
   CANONICAL_EMITTER_ARTIFACT_ID and of nothing semantic — so replacing PRED with
   a different, extensionally equal predecessor moved only the provenance id,
   while the RELATION that maps sub(a,b) to a target term claimed not to have
   changed. The shapes are values in EMISSION_RULES.node_rules now, filled by
   combinator() above, and editing one moves EMISSION_SEM_ID in the same edit. */

/** IS THIS CLOSED TEMPLATE IN THE CODOMAIN? — B7, and it is a DECISION
 *  PROCEDURE rather than a compiler pass.
 *
 *  It evaluates the closed template under the SOURCE arithmetic (church(n) is
 *  n, add is +, sub is -) far enough to answer one question: does any sub node
 *  go negative? The executable encoding represents non-negative Church naturals
 *  and has no image for anything else, so a template that does has no emission
 *  and emission says so by name.
 *
 *  THE NESTED CASE IS THE WHOLE REASON THIS IS RECURSIVE. Checking only the
 *  root would accept (2-3)+2, whose root value is 1 and perfectly emittable,
 *  while the inner monus silently answers 2. An underflow leaves NO TRACE in
 *  the outcome, so it cannot be caught downstream by looking at the answer.
 *
 *  IT IS NOT A CONSTANT FOLDER, and the distinction is worth being exact about
 *  because the code looks identical to one. A folder's output is its value;
 *  this returns a number that emit() throws away. sub(5,2) emits PRED applied
 *  to two Church numerals and the interaction net computes 3 in 96 frames — it
 *  does NOT emit church(3). Folding would make E-9 a theorem about this
 *  function rather than about the runtime, which is the layer collapse the
 *  whole chain exists to refuse.
 *
 *  PORTS AND MALFORMED NODES KEEP THEIR EXISTING NAMES. This walk runs before
 *  go(), so it is the first thing an open or malformed template meets, and it
 *  answers exactly what go() answered before — same names, same depth-first
 *  a-then-b order, so which port an open template is refused for is unchanged. */
export function representableValue(node, rules = EMISSION_RULES) {
  /* THE RULES ARE A PARAMETER — B8.2, and the reason is B6.2's, one object
     over: a module-level frozen constant cannot be varied by the battery meant
     to falsify it, so "an unknown operator is a NAMED refusal" was a property
     this tree could state and not run. It defaults to the canonical rules, and
     nothing in the chain passes anything else. */
  if (!node || typeof node !== "object") throw new Error("template-malformed");
  const R = rules?.node_rules ?? {};
  const V = rules?.domain?.value_rules ?? {};
  const rule = Object.prototype.hasOwnProperty.call(R, node.t) ? R[node.t] : undefined;
  if (rule === undefined) throw new Error("template-malformed: " + String(node.t));
  // A NODE THE MAP REFUSES OUTRIGHT — today only `port`. The refusal NAME comes
  // from the rule, so emit() and this walk cannot disagree about what an
  // unbound port is called.
  if (rule.kind === "refuse") throw new Error(rule.refusal + ": " + String(node.source_name));
  const spec = Object.prototype.hasOwnProperty.call(V, node.t) ? V[node.t] : undefined;
  if (spec === undefined) throw new Error("emission-rule-no-domain-value: " + String(node.t));
  /* THE OPERATOR TABLE LIVES INSIDE THE FUNCTION, which is B6.3.1's rule
     rather than a style choice: a module-level table this function reads would
     be a byte-affecting dependency the artifact id does not hash, and flipping
     an entry in it would change what emits while template, profile and artifact
     id all stood still. Inside, toString() captures it. */
  const OPS = { "+": (x, y) => x + y, "-": (x, y) => x - y, "*": (x, y) => x * y };
  if (spec.literal === "n") {
    // The template grammar says n is a non-negative integer. A template that
    // says otherwise is MALFORMED rather than unrepresentable: there is no
    // arithmetic to do on it and reporting an underflow would name the wrong
    // fault. (lower() cannot build one — `const` refuses on both predicates —
    // but emit() is exported and instantiate() is not the only caller.)
    if (!Number.isInteger(node.n) || node.n < 0)
      throw new Error("template-malformed: church " + String(node.n));
    return node.n;
  }
  const a = representableValue(node.a, rules), b = representableValue(node.b, rules);
  // THE REQUIREMENT IS A VALUE, and it is checked BEFORE the arithmetic it
  // guards. Today the vocabulary is one entry; an unknown one is a NAMED
  // refusal rather than a silently satisfied guard, which is the discipline
  // evalPredicate has had since B2.1 and labelAllocPreOrder since B6.3.1.
  if (spec.require !== undefined) {
    if (spec.require !== "a>=b") throw new Error("emission-rule-unknown-require: " + String(spec.require));
    if (a < b) throw new Error(spec.refusal + ": " + a + " - " + b);
  }
  if (!Object.prototype.hasOwnProperty.call(OPS, spec.operator))
    throw new Error("emission-rule-unknown-operator: " + String(spec.operator));
  return OPS[spec.operator](a, b);
}

/** THE EMITTER IMPLEMENTATION'S OWN IDENTITY — B6.3, and GPT's ruling that
 *  E-1b was scoped one term short.
 *
 *  A PROFILE IS CONFIGURATION AND AN IMPLEMENTATION CAN DECLINE TO READ IT.
 *  Every knob emit() consults now moves this id when it changes, but the walk
 *  itself, the refusal order, the string concatenation — all of it is code, and
 *  code can be edited without touching a knob. GPT demonstrated exactly that
 *  against B6.2: {f0,f1} -> {q0,q1} inside ADD_COMBINATOR changed the bytes on
 *  6 of 9 fixtures while the profile id stood still. B6.3 makes those two
 *  particular names knobs; it does NOT and cannot make the implementation one.
 *
 *  So byte reproducibility is scoped to THREE terms, not two:
 *
 *      same closed template + same emitter PROFILE + same emitter ARTIFACT
 *          -> same exact bytes
 *
 *  while E-1a stays where it was: same closed-template semantic identity +
 *  same EMISSION_SEM_ID -> same target_term_sem_id, and it says nothing about
 *  bytes at all.
 *
 *  IT IS PROVENANCE AND IT IS ALLOWED TO OVERMOVE. This hashes the source text
 *  of every function that produces bytes, so a comment inside emit() moves it.
 *  That would be a defect in a SEMANTIC id — B1.1's whole finding — and is the
 *  correct behaviour for an artifact identity, whose claim is "these exact
 *  implementation bytes", nothing more. Nothing semantic cites it, no receipt
 *  carries it, and it names what a byte-reproducibility claim is relative to
 *  rather than pretending the claim is absolute.
 *
 *  ── B6.3.1: "EVERY FUNCTION" WAS THREE FUNCTIONS AND A TABLE ──────────────
 *  B6.3 bundled emit, church and ADD_COMBINATOR and missed the module-level
 *  enum table emit() reads. GPT flipped one boolean in it with the profile
 *  untouched: the emitted bytes moved on 5 of 9 fixtures while the closed
 *  template, the profile id AND the artifact id all stood still — E-1b's three
 *  stated preconditions all holding across a change to its own conclusion. The
 *  table now lives inside labelAllocPreOrder, which is bundled, so the
 *  dependency is eliminated rather than tracked.
 *
 *  THE MEMBERSHIP IS CHECKED BY DERIVATION, NOT BY CARE. A hand-listed bundle
 *  is the shape artifact_versions was in when three of its six entries had no
 *  reader: correct the day it was written and silently short afterwards. E-2e
 *  reads this module's source, derives its module-level bindings, and requires
 *  every one referenced by a bundled member to be bundled itself, to be the
 *  profile, or to be DECLARED byte-inert below. Adding a helper emit() calls
 *  now fails a case instead of waiting for a reviewer to flip a boolean in it.
 *
 *  THE NAME IS HASHED BESIDE THE SOURCE, so renaming a member moves the id: a
 *  bundle identifying bodies alone would call two different arrangements of the
 *  same code one artifact. */
export const emitterArtifactId = (src) =>
  "cema-" + H("TRVM-CANONICAL-EMITTER-ARTIFACT-v1|" + src);

/** The byte-producing surface, by name, in one place. Order is part of the
 *  hash: a reordering is a different bundle and provenance may say so. */
export const EMITTER_ARTIFACT_MEMBERS = Object.freeze([
  Object.freeze(["emit", emit]),
  Object.freeze(["church", church]),
  // ADD_COMBINATOR AND PRED_COMBINATOR LEFT THIS BUNDLE AT B7.1r, and that is
  // the split working rather than coverage shrinking: the combinator SHAPES are
  // values in EMISSION_RULES now, so changing one moves EMISSION_SEM_ID — a
  // SEMANTIC id — instead of moving only this provenance one. What replaces
  // them here are the two INTERPRETERS, `combinator` and `fill`, which are
  // still code and can still change bytes with the rules held fixed.
  Object.freeze(["combinator", combinator]),
  Object.freeze(["fill", fill]),
  Object.freeze(["labelAllocPreOrder", labelAllocPreOrder]),
  // B7. PRED_COMBINATOR produces bytes, so it is here for the obvious reason.
  // representableValue produces NONE — and is here anyway, because the rule is
  // about what can CHANGE the bytes and not about what writes them: relax one
  // comparison in it and a template that emitted nothing starts emitting a full
  // term, with the closed template and the profile untouched. "No bytes" is a
  // byte-level outcome. E-2e would have forced this by derivation in any case,
  // which is the point of deriving it.
  Object.freeze(["representableValue", representableValue]),
]);

/** Module-level bindings a bundled member may reference WITHOUT being bundled,
 *  each with the reason it cannot change a byte. DECLARED rather than assumed,
 *  and read by E-2e — an allowlist nobody checks is how the table got in. */
export const EMITTER_ARTIFACT_INERT = Object.freeze({
  CANONICAL_EMITTER_PROFILE: "emit()'s default profile argument. Its CONTENT is covered by " +
    "CANONICAL_EMITTER_PROFILE_ID and varying it is E-2c; WHICH object is named as the default is " +
    "part of emit()'s own source text and therefore already inside this id.",
});

/** A FOURTH HONEST ANSWER, and B7.1r had to add it rather than lie in the third.
 *
 *  E-2e's rule was: a module-level binding a bundled member references must be
 *  BUNDLED, be the PROFILE, or be DECLARED BYTE-INERT. `EMISSION_RULES` is none
 *  of those — changing it changes emitted bytes, so calling it inert would be
 *  false, and bundling it would put a SEMANTIC record inside a PROVENANCE id
 *  that overmoves for comments.
 *
 *  The honest answer is that its content is covered by a SEMANTIC identity,
 *  which is STRICTLY STRONGER than the artifact id: editing a rule moves
 *  EMISSION_SEM_ID, and a relation's identity moving is a louder event than a
 *  provenance id moving. Each entry names the id that covers it, and E-2e
 *  checks that id EXISTS on the module rather than accepting the name — an
 *  allowlist whose entries are unverified strings is how the enum table got in.
 *
 *  THE DIRECTION THAT WOULD BE WRONG: this is not a place to park a dependency
 *  because bundling it is inconvenient. The test is whether the named id
 *  actually moves when the binding's content changes, and E-2e measures it. */
export const EMITTER_ARTIFACT_SEMANTIC = Object.freeze({
  EMISSION_RULES: "covered_by EMISSION_RULES_SEM_ID. The combinator shapes, the application shapes, " +
    "the operand order and the domain rules are values emit() and representableValue() READ, and " +
    "editing any of them moves EMISSION_SEM_ID through EMISSION_RULES_SEM_ID — a semantic relation " +
    "identity rather than this provenance one. Bundling it instead would mean a comment inside a " +
    "rule re-cut the emitter artifact, and a reworded rule is not a new emitter.",
});

/** " " SPELLED OUT, not typed. A literal NUL makes file(1) report this
 *  module as `data` and makes grep skip it silently — grid_check has refused
 *  one since v1.31 and refused this one, which is the lint working. */
export const emitterArtifactBundle = (members) =>
  members.map(([name, f]) => name + "\u0000" + f.toString()).join("\u0000");
export const CANONICAL_EMITTER_ARTIFACT_ID =
  emitterArtifactId(emitterArtifactBundle(EMITTER_ARTIFACT_MEMBERS));

/* ── THE KIND INTERPRETER ─────────────────────────────────────────────────
   The small fixed set of KINDS the rule vocabulary's definitions may use. This
   replaces two tables of bare JavaScript functions, which is where B2 left a
   name with no content behind it: `integer` meant whatever the function said,
   and the function could say anything without moving an identity.

   Now the MEANING is in LOWERING_SEMANTICS.predicate_semantics — hashed — and
   this dispatches on it. An unknown kind is a NAMED refusal, never a default:
   a vocabulary that silently accepts an entry it cannot evaluate would be
   exactly the "specification and implementation are two things" problem the
   structural rules were introduced to end. */
const evalPredicate = (spec, v) => {
  if (spec?.kind === "number-is-integer") return Number.isInteger(v);
  if (spec?.kind === "number-compare") {
    if (typeof v !== "number") return false;
    if (spec.operator === ">=") return v >= spec.rhs;
    throw new Error("lowering-rule-malformed: unknown operator " + String(spec.operator));
  }
  throw new Error("lowering-rule-malformed: unknown predicate kind " + String(spec?.kind));
};
const evalTransform = (spec, v) => {
  if (spec?.kind === "identity") return v;
  throw new Error("lowering-rule-malformed: unknown transform kind " + String(spec?.kind));
};

/** program AST → target TEMPLATE, or a NAMED refusal, by INTERPRETING
 *  LOWERING_SEMANTICS.op_lowering_rules. There is no second hand-coded copy of
 *  the map to drift from the hashed one — editing a rule changes what this
 *  function does and moves LOWERING_SEM_ID in the same edit. */
export function lower(ast) {
  const go = (node) => {
    if (!node || typeof node !== "object") throw new Error("lower-unsupported-op");
    const rule = LOWERING_SEMANTICS.op_lowering_rules[node.op];
    if (!rule || !IMPLEMENTED_LOWERED_OPS.includes(node.op)) {
      if (["read", "scope", "cite"].includes(node.op)) throw new Error("lower-reads-undecided");
      throw new Error("lower-unsupported-op: " + String(node.op));
    }
    for (const p of rule.preconditions) {
      const spec = LOWERING_SEMANTICS.predicate_semantics[p.holds];
      if (!spec) throw new Error("lowering-rule-malformed: unknown predicate " + String(p.holds));
      if (!evalPredicate(spec, node[p.field])) throw new Error(p.refusal);
    }
    const out = {};
    for (const [key, spec] of Object.entries(rule.target)) {
      if (typeof spec === "string") { out[key] = spec; continue; }          // t: "church"
      if ("recurse_field" in spec) { out[key] = go(node[spec.recurse_field]); continue; }
      if ("from_field" in spec) {
        const tf = LOWERING_SEMANTICS.transform_semantics[spec.transform ?? "identity"];
        if (!tf) throw new Error("lowering-rule-malformed: unknown transform " + String(spec.transform));
        out[key] = evalTransform(tf, node[spec.from_field]);
        continue;
      }
      throw new Error("lowering-rule-malformed: " + key);
    }
    return Object.freeze(out);
  };
  try {
    const template = go(ast);
    // NO `target_term` FIELD. It was a convenience that emitted a closed
    // template directly, and once emission belongs to the instantiation
    // relation it was a SECOND PATH to an executable term — the official one
    // through instantiate() and a shortcut through lowering, with every future
    // reader having to remember which carried the semantics. GPT ruled it out
    // and the reasoning is the one this tree keeps re-learning: a mechanism
    // built twice is a mechanism that will disagree with itself. instantiate()
    // is now the ONLY way to an executable term, including for zero-port
    // templates, and the migration theorem proves that path reproduces the
    // exact bytes the shortcut used to return.
    return { ok: true, template, target_template_sem_id: targetTemplateSemId(template),
      ports: templatePorts(template) };
  } catch (e) { return { ok: false, reason: e.message }; }
}

/** The APPLICATION record. It ends at the TEMPLATE, because that is what
 *  lowering produces after B1: saying it produced the executable term is the
 *  pre-B1 relation, and a receipt that keeps claiming it would be asserting the
 *  thing the two-level ruling denies. The closed term's identity belongs to the
 *  InstantiationReceipt.
 *
 *  target_template_sem_id is computed here rather than supplied because it is a
 *  property of a structure this module owns and canonicalises. The TERM's id
 *  stays the kernel's to mint — a lowering that minted the identity of the
 *  thing the runtime executes would be grading its own homework. */
export function loweringReceipt(program_sem_id, target_template_sem_id) {
  const receipt = { program_sem_id, lowering_sem_id: LOWERING_SEM_ID, target_template_sem_id };
  return Object.freeze({ ...receipt,
    lowering_receipt_id: "lrec-" + H("TRVM-LOWERING-RECEIPT-v2|" + canonicalBytes(receipt)) });
}

/* ── the decoder ──────────────────────────────────────────────────────────
   ── B8.1: IT READS THE OBJECT NOW, NOT THE OBJECT'S IDENTITY ──────────────
   GPT's ruling, and the defect is one this tree has a name for: IDENTITY IS
   NOT THE OBJECT. Until B8.1 the decoder consumed the CANONICAL SEMANTIC
   SIGNATURE — a serialization built for identification, which §5 replaces with
   its own hash above 80 characters. So the decoder was trying to recover
   semantic structure from a representation deliberately made lossy, and it
   hit the wall exactly where the next workload starts:

       Church 11  ->  signature 76 chars  ->  decodes
       Church 12  ->  signature 82 chars  ->  COMPACTED  ->  refused

   while the runtime computes 12 perfectly well and the normal form EXISTS.
   That is not a runtime limitation and not a semantic-state-identity
   limitation. It is a DECODER INTERFACE limitation, and the fix belongs in the
   decoder rather than in the compaction policy.

   §5 COMPACTION IS NOT TOUCHED, and that is a ruling rather than caution. The
   80-character bound is frozen into SEMSTATE-CANONICAL-v1, the golden pre-hash
   vectors, the 48/48 bridge agreement, every semantic state id and every native
   film. Moving it because the decoder picked the wrong input representation
   would re-cut a large body of evidence for no semantic reason, and would put
   the forty-five-round unchanged calculus certificate in play over a decoder
   bug.

   SO THE SHAPE IS:

       owned target normal form
             ├── identify ──▶ target_nf_sem_id     (oracle, HANDED IN)
             └── decode  ───▶ outcome

   ONE snapshot, TWO consumers, and the decoder does not consume the other
   consumer's output. `decodeOwned` takes the identity oracle as a PARAMETER for
   the reason `makeEmissionVerifier` does: the module that defines a relation
   must not also choose the oracle that judges it. And both read the SAME frozen
   snapshot, so there is no opportunity to identify one state and decode
   another — the B2.1.1 verifier defect, one relation downstream.

   WHAT IS RECOGNISED IS BINDING STRUCTURE, NOT SPELLING. A Church numeral is
   λf.λx. whose body is n applications of THE VARIABLE BOUND BY THE FIRST LAMBDA
   to THE VARIABLE BOUND BY THE SECOND. The decoder compares binder identities,
   so it is invariant under alpha-renaming by construction rather than by the
   canonicaliser having renamed things first.

   AND `decode-signature-compacted` IS GONE, not repointed. It named a fact
   about a representation the decoder no longer reads. Keeping it would leave a
   refusal that can never fire, which is the stale-instrument species this tree
   has now caught four times. What replaces it is NOT a partial result: a term
   that normalises to Church 12 is a COMPLETE computation with an EXISTING
   normal form, and conflating that with BUDGET_EXHAUSTED would undo exactly the
   distinction B5 went to trouble to make. */
export const DECODER_SPEC = Object.freeze({
  reads: "the OWNED target normal-form semantic object — the reference normal form, frozen once and " +
    "read by the identity oracle and by this decoder alike. NOT its canonical signature: that is an " +
    "identity serialization, and §5 replaces it with a hash above 80 characters, so a decoder " +
    "reading it cannot tell a wrong term from a large one.",
  numbers: "STRUCTURAL. Lam(f, Lam(x, body)) where body is either the variable BOUND BY THE SECOND " +
    "lambda — which is 0 — or n applications of the variable BOUND BY THE FIRST lambda, ending in " +
    "the second's. Binder IDENTITY is compared, never a binder NAME, so alpha-invariance is a " +
    "property of the recognition rather than of a prior canonicalisation.",
  outcome_shape: "STRUCTURAL — {status:'value', value} or {status:'refused', code, locus}. Never a " +
    "rendered reason: hashing rendered English would recreate round 16's 'the identity bound a " +
    "spelling' one layer up, where two conforming decoders differ by a comma.",
  refusals: ["decode-not-a-church-numeral", "decode-numeral-exceeds-bound"],
  bound: "a numeral longer than decode_walk_bound applications is refused rather than walked. The " +
    "bound exists because this decoder walks an object it did not build and a cyclic or adversarial " +
    "structure must terminate; it is NOT a bound on what the runtime can compute, and it is stated " +
    "here rather than discovered.",
  decode_walk_bound: 100000,
});
export const DECODE_SEM_ID = "dsem-" + H("TRVM-DECODE-v2|" + canonicalBytes(DECODER_SPEC));

/** THE B7 DECODER, superseded at B8.1. NO DEFECT IN ITS RECOGNITION: it read
 *  Church numerals correctly out of every signature it was given. What was wrong
 *  was its DOMAIN — an identity serialization rather than the object — and the
 *  consequence was a hard ceiling at Church 11 that the runtime did not share.
 *
 *  MEASURED at the boundary before it was replaced: Church 11 signs in 76
 *  characters and decodes; Church 12 signs in 82, is replaced by its own hash,
 *  and is refused. `mul(4,3)` is 12. */
export const SUPERSEDED_SIGNATURE_DECODER_SEM_ID = Object.freeze({
  note: "B7 and earlier decoded the CANONICAL SIGNATURE and refused a §5-compacted one. Superseded " +
    "at B8.1: the decoder reads the owned normal-form OBJECT, and the identity oracle reads the same " +
    "snapshot. SEMSTATE-CANONICAL-v1 and the 80-character compaction are UNCHANGED.",
  decode_sem_id_b7: "dsem-71f531c6b821c3bd6a91e9f3c2ae35511aee0b955d6b8a223d49030b5cd46c61",
  retired_refusal: "decode-signature-compacted — it named a fact about a representation this decoder " +
    "no longer reads, and a refusal that can never fire is a stale instrument.",
  measured: "Church 11 -> 76 chars -> decoded; Church 12 -> 82 chars -> compacted -> refused, while " +
    "the runtime reached the normal form in both cases and the OWNED OBJECT was intact in both.",
});

/** B8.3 — A HISTORY PIN WITH ITS REASON STATED, which is what M-10 requires of
 *  a literal. B8.3 renamed the decoder's parametric entry point and added a
 *  composition root; the CLAIM of that pass is that the RELATION did not change,
 *  and a claim about movement needs a fixed point to be measured against. This
 *  is DECODE_SEM_ID as B8.1 minted it and as B8.3 left it — asserted EQUAL, not
 *  superseded. The opposite pin would be the ratchet: if a later round widens
 *  the decoder's domain again this must move, so the assertion is equality
 *  against THIS declared value and never "the id is dsem-1f4b58c6…" spelled
 *  into a checker. */
export const DECODE_SEM_ID_UNMOVED_AT_B83 = Object.freeze({
  // HISTORY_PIN_OK: the fixed point a no-movement claim is measured against.
  id: "dsem-1f4b58c6f63c1f36d6004a6061ec8cfca9f204dec0b2677bf6d0af7c4e26e620",
  minted_at: "B8.1, when the decoder's domain became the owned object",
  why_it_must_not_move: "B8.3 changed WHO NOMINATES THE IDENTITY ORACLE. That is a composition " +
    "fact. The relation owned-normal-form -> outcome is untouched, and an encoding identity that " +
    "moved for a trust-boundary rename would be over-binding of exactly the species B1.2.1 " +
    "recorded — an id bound to a spelling rather than to a meaning.",
});

/** THE STRUCTURAL RECOGNISER. Takes an OWNED normal-form object; returns the
 *  same {ok, outcome} / {ok:false, reason} shape the signature decoder did. */
export function decodeNormalFormOwned(nf) {
  const bad = { ok: false, reason: "decode-not-a-church-numeral" };
  if (!nf || typeof nf !== "object" || nf.t !== "Lam") return bad;
  if (!nf.bod || nf.bod.t !== "Lam") return bad;
  const F = nf.nam, X = nf.bod.nam;
  // Distinct binders. Two lambdas sharing a binder identity is not a term this
  // runtime produces, and admitting it would make `n` ambiguous.
  if (F === undefined || X === undefined || F === X) return bad;
  let body = nf.bod.bod, n = 0;
  for (;;) {
    if (body && body.t === "Var" && body.nam === X) return { ok: true, outcome: { status: "value", value: n } };
    if (!body || body.t !== "App") return bad;
    if (!body.fun || body.fun.t !== "Var" || body.fun.nam !== F) return bad;
    body = body.arg;
    if (++n > DECODER_SPEC.decode_walk_bound) return { ok: false, reason: "decode-numeral-exceeds-bound" };
  }
}

/* B8.3 — THE DECODER RECREATED B2.1.2's CALLER-CHOSEN-ORACLE SHAPE, and this
   is the second time in this tree, so the repair is the same one and named the
   same way. Reproduced before it was changed:

       decodeOwned(churchZeroNF, () => "nf-DEADBEEF")
         →  { ok: true, outcome: {status:"value", value:0},
              target_nf_sem_id: "nf-DEADBEEF" }

   THE DECODING IS CORRECT. Church zero really is zero, and the function really
   does mean *decode this normal form against the identity oracle supplied to
   this call* — which is what parametric means and is not a defect. The defect is
   that the NAME and the RESULT SHAPE read as an absolute verdict: a caller gets
   back an `ok:true` object carrying a `target_nf_sem_id` it nominated itself.

   B2.1.2 took exactly this shape out of emission —
   `verifyEmissionReceipt → verifyEmissionReceiptAgainst + makeEmissionVerifier`
   — and this is the same relation one layer downstream, at the OUTPUT end of
   the chain rather than the input end.

   NOT A NEW SEMANTIC LAYER: DECODE_SEM_ID does not move, and must not. The
   relation `owned normal form → outcome` is unchanged; what changes is who is
   allowed to nominate the judge, and that is a composition fact, not an
   encoding one. NO ALIAS for the old name, for the reason B2.1.2 gave: an alias
   is a second path to the same relation with the weaker spelling still
   available. */

/** Decode an owned normal form AGAINST A SUPPLIED IDENTITY ORACLE. The
 *  `target_nf_sem_id` in the result is whatever that oracle says; prefer a
 *  decoder bound by makeTargetDecoder at a trusted composition root.
 *
 *  ONE SNAPSHOT, TWO CONSUMERS: the normal form is frozen once and the SAME
 *  frozen object goes to the oracle and to the recogniser, so "identify one
 *  state and decode another" is not an available mistake — B2.1.1's verifier
 *  finding applied at the output end of the chain. */
export function decodeOwnedAgainst(nf, identifyNormalForm) {
  if (typeof identifyNormalForm !== "function")
    throw new Error("decode-oracle-required");
  let own;
  try { own = ownCanonical(nf); }
  catch (e) { return { ok: false, reason: "decode-normal-form-not-canonical: " + e.message }; }
  const decoded = decodeNormalFormOwned(own);
  return { ...decoded, target_nf_sem_id: identifyNormalForm(own), owned: own };
}

/** Bind the trusted normal-form identity oracle ONCE, at a composition root
 *  entitled to choose it, and hand out a ONE-ARGUMENT decoder. Ordinary code
 *  then cannot supply an oracle, because there is no parameter for one —
 *  `makeEmissionVerifier`'s bound arity-2 verifier, one relation over. */
export function makeTargetDecoder({ identifyNormalForm }) {
  if (typeof identifyNormalForm !== "function")
    throw new Error("target-decoder-no-oracle");
  const bound = identifyNormalForm;
  return Object.freeze((nf) => decodeOwnedAgainst(nf, bound));
}

/** TRVM-DERIVE-OUTCOME-v1, ruled in round 22 before it was built: the identity
 *  encodes STRUCTURALLY and never hashes a human-readable reason. */
export function outcomeSemId(outcome) {
  return "osem-" + H("TRVM-DERIVE-OUTCOME-v1|" + canonicalBytes(outcome));
}

/** The source side of the refinement, in the same structural shape. */
export function sourceOutcome(deriveResult) {
  return deriveResult.ok
    ? { status: "value", value: deriveResult.result.semantic_result.value }
    : { status: "refused", code: String(deriveResult.reason).split(":")[0], locus: "$" };
}

export { programSemId };
