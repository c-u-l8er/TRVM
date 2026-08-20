/* ═══════════════════════════════════════════════════════════════════════════
   lowering.mjs — v0.7.2 — the source language reaches the governed runtime

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
             │  substitution THEN emission; emit() is INSIDE this relation and
             │  instantiation_sem_id commits to the EXECUTABLE encoding
             ▼
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
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { canonicalBytes, ownCanonical, CORE_SEM_ID, programSemId } from "./derive_protocol.mjs";

const H = (s) => createHash("sha256").update(s).digest("hex");
export const LOWERING_VERSION = "0.7.2";

/* ── THE EXECUTABLE TARGET ENCODING ───────────────────────────────────────
   ic32's interaction net is linear: a variable used twice needs an explicit
   dup. So Church numerals are emitted in LINEAR form with explicit dup labels,
   which is the shape the conformance corpus already uses for church_apply_N.
   The label policy is part of the encoding and therefore part of its identity:
   two EMISSIONS that agree on everything except which integers they hand the
   dups are two different emissions, and pretending otherwise would let an
   allocation detail hide inside a semantic id.

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
  numbers: "linear Church numerals. n is λf.λx. followed by n-1 dup bindings of " +
    "f and then n nested applications; 0 is λf.λx.x and 1 is λf.λx.(f x), which need no dup.",
  add: "λm.λn.λf.λx.!&L{f0,f1}=f;((m f0) ((n f1) x)) — the only non-linear use is f, " +
    "duplicated once per addition.",
  dup_label_policy: "labels are assigned by a counter that starts at 0 and advances in the " +
    "order the lowering emits them, depth-first, operands in declared field order. DETERMINISTIC " +
    "and part of this encoding's identity: a different assignment is a different encoding, because " +
    "the label reaches the canonical signature through Sn(…) and would otherwise be an allocation " +
    "detail hiding inside a semantic id.",
  // SEMANTIC refusals of THIS encoding — the ones EMISSION can produce.
  // `lower-input-not-implemented` was here until B1.2 and is now a STATUS
  // refusal in LOWERING_STATUS: it says the code is unwritten, not that the
  // encoding refuses the op, and hashing it into an encoding identity would
  // make writing the frozen rule a semantic event.
  refusals: ["emit-unbound-port", "template-malformed"],
});

/** THE IDENTITY OF THE EXECUTABLE ENCODING. GPT's B1.2.1 find, and the reason
 *  it is content-bound rather than a label: INSTANTIATION_SEMANTICS used to name
 *  its codomain as the STRING "TRVM-TERM-CANON-v1 / ic32 executable text, via
 *  emit()". A name anyone may claim is not a commitment — the same objection the
 *  primitive ruling raised against a bare `componentReachability` — so the rule
 *  that decides how church(n) and add(a,b) become interaction-net terms could be
 *  rewritten with every downstream identity intact. Now the bytes are in the id
 *  and the id is in the relation. */
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
  grammar: "Template := church(n) | add(Template, Template) | port(source_name)",
  nodes: Object.freeze({
    church: "{t:\"church\", n} — a non-negative integer literal, expanded to a LINEAR Church numeral " +
      "by emit() per TARGET_ENCODING.numbers. The expansion is the ENCODING's, not the template's, " +
      "which is why n stays a number here.",
    add: "{t:\"add\", a, b} — the TARGET add combinator applied to two templates. Target-side, not " +
      "the source `add` op: it names the combinator in TARGET_ENCODING.add. Operand order is a then " +
      "b, the core's own evaluation order.",
    port: "{t:\"port\", source_name} — an INPUT PORT, structural. Instantiation replaces it; emit() " +
      "REFUSES a template that still contains one, because a template with a free port is not an " +
      "executable term and silently emitting something for it would be the fragment-totality " +
      "violation one layer down.",
  }),
  no_names_no_labels: "A TEMPLATE CONTAINS NO BINDER NAMES AND NO DUP LABELS. emit() allocates both " +
    "from the template's shape by TARGET_ENCODING.dup_label_policy — a counter from 0, depth-first, " +
    "operands in declared field order. Allocation is therefore not merely declared non-semantic; " +
    "there is no field it could occupy. This is what makes I-4a structural.",
  determinism: "emit() is a function: the same template always produces the same ic32 text, labels " +
    "included. Two templates with equal canonical bytes emit equal terms.",
  refusals: ["emit-unbound-port", "template-malformed"],
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
  domain_restriction: "the PORT-FREE subset. A template still holding a port is refused by name; " +
    "emission is total on closed templates and refusing outside them, the same discipline lowering " +
    "has on its fragment.",
  codomain_encoding_sem_id: TARGET_EXECUTABLE_ENCODING_SEM_ID,
  allocation: "binder names and dup labels are INVENTED HERE, from the template's shape, by " +
    "TARGET_ENCODING.dup_label_policy. This is the only place in the chain where an allocation " +
    "exists, which is what makes allocation-invariance a property of everything upstream.",
  determinism: "a function: equal closed templates emit equal terms, labels included. Two emitters " +
    "may differ in the bytes they produce and must agree on what those bytes MEAN — that is a " +
    "theorem about this relation and it is why the relation is separate.",
  semantic_refusals: ["emit-unbound-port", "template-malformed"],
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
    if (n.t === "add") { walk(n.a); walk(n.b); return; }
    throw new Error("template-malformed: " + String(n.t));
  };
  walk(template);
  return [...out].sort();
}

/** TEMPLATE → ic32 text. The ONLY place binder names and dup labels are
 *  invented, which is the whole point of the layer. */
export function emit(template) {
  const labels = { n: 0, next() { return this.n++; } };
  const go = (n) => {
    if (!n || typeof n !== "object") throw new Error("template-malformed");
    if (n.t === "church") return church(n.n, labels);
    if (n.t === "add") { const a = go(n.a), b = go(n.b);
      return `((${ADD_COMBINATOR(labels.next())} ${a}) ${b})`; }
    if (n.t === "port") throw new Error("emit-unbound-port: " + String(n.source_name));
    throw new Error("template-malformed: " + String(n.t));
  };
  return go(template);
}

/* WHICH ops the CODE lowers today — an implementation status, not a semantics,
   and the name now says so. It was `LOWERED_OPS`, which read as the fragment
   itself and sat four lines from LOWERING_SEMANTICS.lowered_ops holding a
   DIFFERENT and larger list. Distinguishing "semantically specified" from
   "implemented" is the whole conceptual content of B1.2, so the one name in the
   file that blurred them was the wrong name to keep:

       LOWERING_SEMANTICS.lowered_ops   const · add · input     SPECIFIED, frozen
       IMPLEMENTED_LOWERED_OPS          const · add · input     WRITTEN

   AT B2 THE TWO LISTS COINCIDE, and that is a fact about this moment rather
   than a reason to merge the names. `input` was specified at B1.2 and written
   here; `read`, `scope` and `cite` have no lowering rule at all; `sub`, `mul`
   and `len` are simply not encoded yet. The first of those to get a frozen rule
   ahead of its implementation separates the lists again, which is the state the
   distinction exists for. THE COMMENT HERE ONCE SAID `input` was absent
   "because the inputs model is undecided" — untrue since B1 decided it and
   doubly untrue since B1.2 froze the rule. */
export const IMPLEMENTED_LOWERED_OPS = Object.freeze(["const", "add", "input"]);

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
  lowered_ops: Object.freeze(["const", "add", "input"]),
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

/** Linear Church numeral. n uses f exactly n times, so n-1 dups. */
function church(n, labels) {
  if (n === 0) return "λf.λx.x";
  if (n === 1) return "λf.λx.(f x)";
  const binds = [];
  let cur = "f";
  for (let i = 0; i < n - 1; i++) {
    const L = labels.next();
    if (i < n - 2) { binds.push(`!&${L}{a${i},t${i}}=${cur};`); cur = `t${i}`; }
    else binds.push(`!&${L}{a${i},a${i + 1}}=${cur};`);
  }
  let body = "x";
  for (let i = n - 1; i >= 0; i--) body = `(a${i} ${body})`;
  return `λf.λx.${binds.join("")}${body}`;
}

const ADD_COMBINATOR = (L) => `λm.λn.λf.λx.!&${L}{f0,f1}=f;((m f0) ((n f1) x))`;

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
   It reads the CANONICAL SEMANTIC SIGNATURE rather than a printed term, so it
   is reading the same bytes the bridge gate has agreed on since round 12 rather
   than a readback that could differ by a binder name. A Church numeral n is

       L0(L1( A(N0, A(N0, … A(N0, N1) … )) ))     with n applications
       L0(L1(N1))                                  for n = 0

   and anything else is a NAMED refusal. §5 compaction replaces a signature
   longer than 80 characters with '#'+sha256, which is irreversible, so a
   compacted signature is refused rather than guessed at — the boundary is real
   and it is better named than silently mis-decoded. */
export const DECODER_SPEC = Object.freeze({
  reads: "the SEMSTATE-CANONICAL-v1 signature of the target normal form, not a readback string",
  numbers: "linear Church numerals: L0(L1(A(N0,…A(N0,N1)…))) with n applications; L0(L1(N1)) is 0",
  outcome_shape: "STRUCTURAL — {status:'value', value} or {status:'refused', code, locus}. Never a " +
    "rendered reason: hashing rendered English would recreate round 16's 'the identity bound a " +
    "spelling' one layer up, where two conforming decoders differ by a comma.",
  refusals: ["decode-signature-compacted", "decode-not-a-church-numeral"],
  compaction_note: "§5 compaction is irreversible, so a compacted signature is REFUSED. This bounds " +
    "the decodable numerals and the bound is stated rather than discovered: at 80 characters the " +
    "signature holds roughly a dozen applications.",
});
export const DECODE_SEM_ID = "dsem-" + H("TRVM-DECODE-v1|" + canonicalBytes(DECODER_SPEC));

export function decode(signature) {
  if (typeof signature !== "string") return { ok: false, reason: "decode-not-a-church-numeral" };
  if (signature.includes("#")) return { ok: false, reason: "decode-signature-compacted" };
  const m = /^L(\d+)\(L(\d+)\((.*)\)\)$/.exec(signature);
  if (!m) return { ok: false, reason: "decode-not-a-church-numeral" };
  const fName = "N" + m[1], xName = "N" + m[2];
  let body = m[3], n = 0;
  const app = new RegExp("^A\\(" + fName + ",(.*)\\)$");
  for (;;) {
    if (body === xName) return { ok: true, outcome: { status: "value", value: n } };
    const a = app.exec(body);
    if (!a) return { ok: false, reason: "decode-not-a-church-numeral" };
    body = a[1]; n++;
    if (n > 1000) return { ok: false, reason: "decode-not-a-church-numeral" };
  }
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
