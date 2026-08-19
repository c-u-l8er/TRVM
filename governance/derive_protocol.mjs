/* ═══════════════════════════════════════════════════════════════════════════
   derive_protocol.mjs — v0.4.0 — the serialized derivation boundary

   law:derivation.environment-confinement@1 is FALSIFIED under the arbitrary-
   closure measureFn API, and the record says closure comes from REPLACING the
   API rather than hardening it. This is the replacement, built in-process
   first: get the protocol right where it is cheap to falsify, then move the
   same protocol across a realm boundary where the transport does the confining.

   Three things the closure API could not do, and this must:

   1. A PROGRAM IS DATA, not a callable. `program_sem_id` is H(canonical
      program), so it cannot be a caller-selected label — the 9D.4 witness
      showed that `measureFn = evilClosure` would otherwise simply become
      {"program_sem_id": "honest-program"} while arbitrary code ran. Rebinding
      an id to a different program is impossible rather than forbidden: the id
      IS the program's hash.
   2. THE SAME PROGRAM HAS ONE ID ACROSS IMPLEMENTATIONS. program_sem_id is
      computed from the program, never from the evaluator, so JS and C
      implementations of P agree on it by construction. implementation_id
      carries executable provenance separately, is ASSERTED BY THE EXECUTOR,
      and the caller may only state a requirement against it.
   3. THE BOUNDARY IS THE CANONICAL VALUE DOMAIN, not "structuredClone
      succeeded". The 9D.3 Map witness already disqualified that phrase by
      proving structuredClone and JSON.stringify disagree about what a value is.
      Function, Map, Set, Date, SharedArrayBuffer, MessagePort, class instances
      and transferable handles are refused: those are capabilities, not data.

   WHAT v0.2.0 CHANGES, AND WHY THE v0.1.0 PROSE WAS WRONG
   ───────────────────────────────────────────────────────
   v0.1.0 said "the footprint is the authority's record of what it read on the
   derivation's behalf". It was not. The worker sourced its read table from
   `canonical_inputs.__reads`, and `{op:"input", name:"__reads"}` retrieves any
   canonical input — so a program could consume the entire authority-supplied
   read table with witness.reads = 0 and an empty footprint. Frozen as W-1 in
   probe_derivegrant_v02_repro.mjs.

   The repair is not to redefine the footprint as the grant. They are two
   different evidence objects and collapsing them loses both:

       AUTHORITY GRANT  — what the authority made available.  A capability
       (`read_grants`, named   record. Broad by design: with data-dependent
        by `grant_id`)         traversal the authority cannot know in advance
             │                 which subset a program will need, so it hands
             ▼                 over a bounded canonical world SLICE.
       derivation realm
             │
             ▼
       READ FOOTPRINT   — what the program actually consumed. The DEPENDENCY
       (`read_footprint`)     record: freshness, invalidation, replay and
                              support analysis all key on this. Defining it as
                              the grant would over-invalidate every derivation
                              whose grant was wider than its reads — which,
                              under snapshot granting, is all of them.

   So: `input` can address only `canonical_inputs`; `read` and `scope` can
   address only `read_grants`; the footprint is the ACCESS SUBSET, recorded by
   the evaluator; and the authority validates it independently rather than
   trusting the executor's claim — `footprintWithinGrant` fires on its own
   evidence, before any re-derivation.

   Snapshot granting (model A) rather than read-RPC (model B) is a decision,
   not an oversight: it is deterministic, it films cleanly, and it does not
   turn every primitive evaluation into a cross-realm round trip. It costs
   least-authority — the grant may reveal more than the program reads. If
   confidentiality against the derivation realm ever matters, that is the
   trigger to move to B or a hybrid, and it is named in the grid rather than
   discovered later.

   What this file does NOT yet claim: host confinement, determinism of a
   long-lived evaluator, that implementation_id is bound to executable BYTES
   (it is a declared constant — impersonation is closed, provenance is not),
   or that any real derivation has been ported. Separate scopes, named
   separately in the grid.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";

const H = (s) => createHash("sha256").update(s).digest("hex");
export const PROTOCOL_VERSION = "0.4.0";

/* ── the canonical value domain, shared with the World ────────────────────
   Deliberately a copy of the World's rule rather than an import: this module
   must be movable across a realm boundary, and the boundary check has to hold
   on the far side where trvm_world.mjs is not present. The rule is identical
   and the negative battery asserts both refuse the same things. */
export function canonicalBytes(v, path = "$", onPath = new Set()) {
  if (v === null) return "null";
  const t = typeof v;
  if (t === "boolean") return v ? "true" : "false";
  if (t === "number") {
    if (!Number.isFinite(v)) throw new Error("not-canonical: non-finite number at " + path);
    return JSON.stringify(v);
  }
  if (t === "string") return JSON.stringify(v);
  if (t === "object") {
    if (onPath.has(v)) throw new Error("not-canonical: cycle at " + path);
    onPath.add(v);
    let out;
    if (Array.isArray(v)) {
      out = "[" + v.map((x, i) => canonicalBytes(x, path + "[" + i + "]", onPath)).join(",") + "]";
    } else if (Object.getPrototypeOf(v) === Object.prototype || Object.getPrototypeOf(v) === null) {
      const keys = Object.keys(v).sort();
      out = "{" + keys.map((k) => JSON.stringify(k) + ":" +
        canonicalBytes(v[k], path + "." + k, onPath)).join(",") + "}";
    } else {
      // Map, Set, Date, class instances, MessagePort, SharedArrayBuffer …
      throw new Error("not-canonical: non-plain object (" +
        (v.constructor?.name ?? "anonymous") + ") at " + path);
    }
    onPath.delete(v);
    return out;
  }
  throw new Error("not-canonical: " + t + " at " + path);
}

/* ── TRVM-DERIVE-CORE-v1: the frozen core, and why freezing it was urgent ──
   v0.2.0 computed program_sem_id as H("TRVM-PROGRAM-v1|" + canonicalBytes(ast))
   while the record simultaneously said the language was deliberately NOT frozen.
   Those two cannot both be true: the id bound SYNTAX and claimed to bind
   semantics. Four gaps sat behind one id, all reproduced before this repair
   (probe_coresem_v03_repro.mjs):

     add was JavaScript `+`      "2"+"3" -> "23"; []+{} -> "[object Object]"
     bind() validated nothing    {op:"exec", cmd:"rm -rf /"} received an id
     arity/fields unconstrained  {op:"const"} and add-without-b received ids
     evaluation order was free   the footprint was an ARRAY appended at access,
                                 so a right-to-left implementation returned a
                                 different — and therefore diverging — semantic
                                 projection for a program it computed identically

   A C implementation could satisfy every one of those differently and agree on
   program_sem_id, which is exactly the property the id exists to deny.

   The fourth is closed by RULING rather than by declaration: the footprint is
   now a canonical dependency SET and access order lives in a separate
   read_trace outside the semantic projection. Declaring an order would have
   made two correct implementations disagree over a field neither considers
   semantic; depending on {a,b} is one dependency set however it was visited.
   Execution strategy does not silently become semantic identity — the same
   principle that keeps ref_interactions out of conformance identity.

   So the core is frozen HERE, as a canonical record, and its identity is
   CONTENT-BOUND rather than a label: core_sem_id = H(canonical CORE_SPEC). A
   bare "TRVM-DERIVE-CORE-v1" string would be the same defect the primitive
   ruling already refuses for "componentReachability" — a name anyone can claim.
   Change what `add` means and core_sem_id moves and every program id moves with
   it, which is the property that makes the id semantic.

   BREAKING, deliberately, and now: every program_sem_id changes. No second
   implementation exists yet, which is the only reason this is cheap, and is the
   reason it happens before the C work rather than after it. */
export const CORE_SPEC = Object.freeze({
  language: "TRVM-DERIVE-CORE",
  version: 1,
  value_domain: "null | boolean | finite number | string | canonical array | canonical plain object. " +
    "Non-finite numbers, cycles, and non-plain objects (Map, Set, Date, class instances, " +
    "transferable handles) are not values and are refused wherever they appear.",
  numbers: "IEEE-754 binary64. Every arithmetic OPERAND must be a number — there is no coercion, " +
    "no string concatenation and no object stringification — and every arithmetic RESULT must be " +
    "finite. Overflow is a refusal at the operation, not a non-finite value handed onward.",
  signed_zero: "the canonical numeric quotient IDENTIFIES -0 with +0. canonicalBytes serializes " +
    "both as \"0\", so they are one value in the message domain, in warrant_id, in replay and in " +
    "every equality this system takes. An implementation must not distinguish them at the boundary " +
    "even where its own arithmetic does. Stated because it was already true of the canonical " +
    "domain and unstated — which is how a C implementation would have decided it by accident.",
  evaluation_order: "depth-first, operands in declared field order: `a` fully evaluated before `b`. " +
    "This is DETERMINISTIC so that refusals, short-circuiting and the execution trace are the same " +
    "everywhere. It is deliberately NOT semantic identity: see read_footprint.",
  read_footprint: "a canonical DEPENDENCY SET, not a sequence — sorted and deduplicated. Depending " +
    "on {a,b} must not become a different semantic identity because one correct implementation " +
    "visited a then b and another visited b then a. Execution strategy does not silently become " +
    "semantics unless the calculus requires it, which is the same principle that keeps " +
    "ref_interactions out of conformance identity. Access ORDER, with repeats, is preserved " +
    "separately in read_trace, which is evidence-plane material and is excluded from the semantic " +
    "projection.",
  ops: {
    const: { fields: ["value"], returns: "the literal, which must be a canonical value" },
    input: { fields: ["name"], reads: "canonical_inputs ONLY — never read_grants" },
    read: { fields: ["resource"], reads: "read_grants.exact; appends [resource, version] to the footprint" },
    scope: { fields: ["query"], reads: "read_grants.predicates; appends [query, digest] to the footprint" },
    cite: { fields: ["name"], reads: 'read_grants.exact under the key "warrant:" + name; returns .value.value' },
    add: { fields: ["a", "b"], returns: "numeric sum" },
    sub: { fields: ["a", "b"], returns: "numeric difference" },
    mul: { fields: ["a", "b"], returns: "numeric product" },
    len: { fields: ["a"], returns: "array length; a non-array operand is refused" },
  },
  grammar: "every node is a plain object whose key set is EXACTLY {op} union the op's declared " +
    "fields. Unknown ops, missing fields and extra fields are all refused at bind time, so an id " +
    "is never issued for a program outside the language.",
  refusals: [
    "program-malformed-node", "program-unknown-op", "program-node-fields",
    "program-name-not-a-string", "program-const-not-canonical",
    "program-input-missing", "program-type", "program-arith-non-finite",
    "read-not-granted", "scope-not-granted",
  ],
  totality: "the core is TOTAL: no recursion, no unbounded loop, no general function. Every " +
    "program terminates in a number of steps bounded by its own node count.",
  extension: "new behaviour arrives as {op:'prim', primitive_sem_id, args} with a content-bound " +
    "primitive identity, never as if/while/function/closure/eval. A prim extension bumps the CORE " +
    "version and therefore every program id, which is intended: a program written against a " +
    "different language is a different program.",
});
export const CORE_SEM_ID = "core-" + H("TRVM-DERIVE-CORE-SPEC-v1|" + canonicalBytes(CORE_SPEC));

const OPS = {
  const: (n) => n.value,
  read: null, scope: null, cite: null,          // effectful — handled by the evaluator
  add: (n, ev) => arith("add", ev(n.a), ev(n.b), (x, y) => x + y),
  sub: (n, ev) => arith("sub", ev(n.a), ev(n.b), (x, y) => x - y),
  mul: (n, ev) => arith("mul", ev(n.a), ev(n.b), (x, y) => x * y),
  len: (n, ev) => { const v = ev(n.a); if (!Array.isArray(v)) throw new Error("program-type: len of non-array"); return v.length; },
  input: null,
};

/** No coercion, and overflow refused at the operation. `+` on two strings is
 *  concatenation in JavaScript and would be something else in C; the core says
 *  neither implementation may guess. */
function arith(op, x, y, f) {
  if (typeof x !== "number" || typeof y !== "number")
    throw new Error("program-type: " + op + " of non-number");
  const r = f(x, y);
  if (!Number.isFinite(r)) throw new Error("program-arith-non-finite: " + op);
  return r;
}

/** The grammar check. An id may not be issued for a program outside the
 *  language — v0.2.0 handed one to {op:"exec", cmd:"rm -rf /"}, which failed
 *  only later, at evaluation, having already been given a semantic identity. */
export function validateProgram(ast, path = "$") {
  if (ast === null || typeof ast !== "object" || Array.isArray(ast))
    return { ok: false, reason: "program-malformed-node at " + path };
  const spec = CORE_SPEC.ops[ast.op];
  if (typeof ast.op !== "string" || !spec)
    return { ok: false, reason: "program-unknown-op: " + String(ast.op) + " at " + path };
  const want = ["op", ...spec.fields].sort();
  const got = Object.keys(ast).sort();
  if (canonicalBytes(got) !== canonicalBytes(want))
    return { ok: false, reason: "program-node-fields at " + path + ": [" + got.join(",") +
      "] wanted [" + want.join(",") + "]" };
  for (const f of ["name", "resource", "query"])
    if (spec.fields.includes(f) && typeof ast[f] !== "string")
      return { ok: false, reason: "program-name-not-a-string at " + path + "." + f };
  if (ast.op === "const") {
    try { canonicalBytes(ast.value); }
    catch (e) { return { ok: false, reason: "program-const-not-canonical at " + path + ": " + e.message }; }
  }
  for (const f of ["a", "b"]) if (spec.fields.includes(f)) {
    const sub = validateProgram(ast[f], path + "." + f);
    if (!sub.ok) return sub;
  }
  return { ok: true };
}

/** program_sem_id commits the CORE SEMANTICS as well as the syntax. */
export function programSemId(ast) {
  const v = validateProgram(ast);
  if (!v.ok) throw new Error(v.reason);
  return "psem-" + H("TRVM-PROGRAM-v2|" + CORE_SEM_ID + "|" + canonicalBytes(ast));
}

/* A program registry whose binding cannot be forged: the key IS the hash of
   the value. `bind` recomputes and refuses a mismatch, so "register this AST
   under that id" is not an operation the API offers. */
export class ProgramRegistry {
  #byId = new Map();
  constructor() { Object.freeze(this); }
  bind(ast) {
    const id = programSemId(ast);
    const frozen = JSON.parse(canonicalBytes(ast));       // owned, severed
    deepFreeze(frozen);
    const existing = this.#byId.get(id);
    if (existing && canonicalBytes(existing) !== canonicalBytes(frozen))
      throw new Error("program-rebind-refused: " + id);   // unreachable by construction; asserted anyway
    this.#byId.set(id, frozen);
    return id;
  }
  get(id) { return this.#byId.get(id); }
  has(id) { return this.#byId.has(id); }
  /** the check that makes the id load-bearing rather than decorative */
  verify(id) {
    const ast = this.#byId.get(id);
    if (!ast) return { ok: false, reason: "program-unknown" };
    const recomputed = programSemId(ast);
    return recomputed === id ? { ok: true } : { ok: false, reason: "program-id-mismatch" };
  }
}
Object.freeze(ProgramRegistry.prototype);

function deepFreeze(v) {
  if (v === null || typeof v !== "object" || Object.isFrozen(v)) return v;
  Object.freeze(v);
  for (const k of Object.keys(v)) deepFreeze(v[k]);
  return v;
}

/* ── THE AUTHORITY GRANT ──────────────────────────────────────────────────
   A bounded canonical world slice, keyed by resource. Keyed objects rather
   than the obvious list of triples, for two reasons that are not stylistic:
   canonical objects sort their keys, so `grant_id` does not depend on the
   order the authority happened to resolve resources in; and a duplicate
   resource with two versions cannot be expressed at all. */
export function grantId(read_grants) {
  return "grant-" + H("TRVM-GRANT-v1|" + canonicalBytes(read_grants));
}

export function checkGrants(g) {
  if (g === null || typeof g !== "object" || Array.isArray(g))
    return { ok: false, reason: "grants-not-an-object" };
  const keys = Object.keys(g).sort();
  if (canonicalBytes(keys) !== canonicalBytes(["exact", "predicates"]))
    return { ok: false, reason: "grants-schema: [" + keys.join(",") + "]" };
  for (const kind of ["exact", "predicates"]) {
    const t = g[kind];
    if (t === null || typeof t !== "object" || Array.isArray(t))
      return { ok: false, reason: "grants-" + kind + "-not-an-object" };
  }
  for (const [r, e] of Object.entries(g.exact)) {
    if (e === null || typeof e !== "object" || Array.isArray(e))
      return { ok: false, reason: "grant-entry-not-an-object: " + r };
    const ek = Object.keys(e).sort();
    if (canonicalBytes(ek) !== canonicalBytes(["value", "version"]))
      return { ok: false, reason: "grant-entry-schema: " + r + " [" + ek.join(",") + "]" };
    if (typeof e.version !== "number" && typeof e.version !== "string")
      return { ok: false, reason: "grant-entry-version-malformed: " + r };
  }
  try { canonicalBytes(g); }
  catch (e) { return { ok: false, reason: "grants-" + e.message }; }
  return { ok: true };
}

/** The authority resolves a world slice ONCE, on the authoritative side, and
 *  the snapshot is what both the executor and the re-deriving authority
 *  evaluate against. `reader` here is the World's own interface and never
 *  crosses the boundary — it is the last callable on the derivation path and
 *  it lives entirely on the side that owns the World. */
export function resolveGrants(reader, want = {}) {
  const g = { exact: {}, predicates: {} };
  for (const r of want.exact ?? []) {
    const v = reader.read(r);
    g.exact[r] = { value: v.value, version: v.version };
  }
  for (const q of want.predicates ?? []) g.predicates[q] = reader.scope(q);
  const c = checkGrants(g);
  if (!c.ok) throw new Error("grant-resolution: " + c.reason);
  return { read_grants: g, grant_id: grantId(g) };
}

/* ── the request/result schemas ───────────────────────────────────────────
   Everything crossing the boundary is checked against the canonical domain
   FIRST. A request that cannot be represented cannot become authority.

   `expected_implementation_id` is OPTIONAL and is a REQUIREMENT, not an
   assertion: the executor refuses a request it cannot satisfy. The result's
   `implementation_id` is the executor's own, which is the whole difference
   between provenance and decoration. */
const REQUEST_REQUIRED = ["request_id", "program_sem_id", "canonical_inputs", "read_grants", "grant_id"];
const REQUEST_OPTIONAL = ["expected_implementation_id"];
const RESULT_FIELDS = ["request_id", "program_sem_id", "implementation_id", "grant_id",
  "value", "witness", "support", "read_footprint", "read_trace"];
/** the portable half of a result: everything two implementations must agree on.
 *  TWO fields are deliberately OUT.
 *    implementation_id — two conforming implementations of the same program
 *      produce different executable provenance and identical semantics, and
 *      comparing whole results would make cross-implementation validation fail
 *      by construction.
 *    read_trace — access ORDER with repeats is execution strategy. Depending on
 *      {a,b} is one dependency set however it was visited, and a-then-b must not
 *      be a different semantic identity from b-then-a. The trace is kept because
 *      the film plane wants it, and kept OUT because semantics do not. */
const NON_SEMANTIC_RESULT_FIELDS = ["implementation_id", "read_trace"];
export const SEMANTIC_RESULT_FIELDS = RESULT_FIELDS.filter((f) => !NON_SEMANTIC_RESULT_FIELDS.includes(f));

export function semanticProjection(res) {
  const out = {};
  for (const f of SEMANTIC_RESULT_FIELDS) out[f] = res[f];
  return out;
}

export function checkRequest(req) {
  if (req === null || typeof req !== "object" || Array.isArray(req))
    return { ok: false, reason: "request-not-an-object" };
  const keys = Object.keys(req);
  const allowed = new Set([...REQUEST_REQUIRED, ...REQUEST_OPTIONAL]);
  const unknown = keys.filter((k) => !allowed.has(k)).sort();
  const missing = REQUEST_REQUIRED.filter((k) => !keys.includes(k)).sort();
  if (unknown.length || missing.length)
    return { ok: false, reason: "request-schema:" +
      (missing.length ? " missing [" + missing.join(",") + "]" : "") +
      (unknown.length ? " unknown [" + unknown.join(",") + "]" : "") };
  try { canonicalBytes(req); }
  catch (e) { return { ok: false, reason: "request-" + e.message }; }
  if (typeof req.program_sem_id !== "string" || !req.program_sem_id.startsWith("psem-"))
    return { ok: false, reason: "request-program-id-malformed" };
  const cg = checkGrants(req.read_grants);
  if (!cg.ok) return { ok: false, reason: "request-" + cg.reason };
  // the grant_id BINDS the snapshot: a request may not name one grant and carry another
  if (req.grant_id !== grantId(req.read_grants))
    return { ok: false, reason: "request-grant-id-mismatch" };
  if ("expected_implementation_id" in req && typeof req.expected_implementation_id !== "string")
    return { ok: false, reason: "request-expected-implementation-malformed" };
  if (req.canonical_inputs === null || typeof req.canonical_inputs !== "object" ||
      Array.isArray(req.canonical_inputs))
    return { ok: false, reason: "request-inputs-not-an-object" };
  return { ok: true };
}

export function checkResult(res, req) {
  if (res === null || typeof res !== "object" || Array.isArray(res))
    return { ok: false, reason: "result-not-an-object" };
  const keys = Object.keys(res).sort();
  const want = [...RESULT_FIELDS].sort();
  if (canonicalBytes(keys) !== canonicalBytes(want))
    return { ok: false, reason: "result-schema: [" + keys.join(",") + "]" };
  try { canonicalBytes(res); }
  catch (e) { return { ok: false, reason: "result-" + e.message }; }
  // a result may not claim to be about a different request, program or grant
  if (res.request_id !== req.request_id) return { ok: false, reason: "result-request-mismatch" };
  if (res.program_sem_id !== req.program_sem_id) return { ok: false, reason: "result-program-mismatch" };
  if (res.grant_id !== req.grant_id) return { ok: false, reason: "result-grant-mismatch" };
  if (typeof res.implementation_id !== "string" || !res.implementation_id.startsWith("impl-"))
    return { ok: false, reason: "result-implementation-id-malformed" };
  const fp = res.read_footprint;
  if (fp === null || typeof fp !== "object" || !Array.isArray(fp.exact) || !Array.isArray(fp.predicates))
    return { ok: false, reason: "result-footprint-malformed" };
  const tr = res.read_trace;
  if (tr === null || typeof tr !== "object" || !Array.isArray(tr.exact) || !Array.isArray(tr.predicates))
    return { ok: false, reason: "result-trace-malformed" };
  // the footprint must BE the canonical set: sorted, deduplicated. A result
  // carrying a sequence where a set is required is refused rather than
  // silently normalized, because normalizing on receipt would let two
  // implementations disagree about the bytes they each committed to.
  for (const kind of ["exact", "predicates"]) {
    const seen = new Map();
    for (const p of tr[kind]) seen.set(canonicalBytes(p), p);
    const want = [...seen.values()].sort((x, y) => canonicalBytes(x) < canonicalBytes(y) ? -1 : 1);
    if (canonicalBytes(fp[kind]) !== canonicalBytes(want))
      return { ok: false, reason: "result-footprint-not-canonical-set: " + kind };
  }
  // the witness must agree with the footprint it accompanies, checked before
  // any re-derivation so a lying claim is refused on its own evidence
  if (res.witness?.reads !== fp.exact.length || res.witness?.scopes !== fp.predicates.length)
    return { ok: false, reason: "result-witness-inconsistent" };
  return { ok: true };
}

/* ── FOOTPRINT VALIDATION, independent of re-derivation ───────────────────
   The authority does not have to take the executor's word for what it read,
   and does not have to re-derive first to find out: every claimed access must
   be IN the snapshot it was granted, at the version it was granted at. This
   fires on its own evidence — it catches a footprint naming a resource the
   authority never granted even when the value happens to be right. */
export function footprintWithinGrant(fp, read_grants) {
  for (const entry of fp.exact ?? []) {
    if (!Array.isArray(entry) || entry.length !== 2)
      return { ok: false, reason: "footprint-exact-entry-malformed" };
    const [r, ver] = entry;
    const g = read_grants.exact[r];
    if (g === undefined) return { ok: false, reason: "footprint-ungranted-read: " + r };
    if (g.version !== ver) return { ok: false, reason: "footprint-version-mismatch: " + r };
  }
  for (const entry of fp.predicates ?? []) {
    if (!Array.isArray(entry) || entry.length !== 2)
      return { ok: false, reason: "footprint-predicate-entry-malformed" };
    const [q, d] = entry;
    if (!(q in read_grants.predicates)) return { ok: false, reason: "footprint-ungranted-scope: " + q };
    if (canonicalBytes(read_grants.predicates[q]) !== canonicalBytes(d))
      return { ok: false, reason: "footprint-scope-digest-mismatch: " + q };
  }
  return { ok: true };
}

/* ── the JS evaluator (implementation_id names THIS, not the program) ─────
   The reader is BUILT FROM THE GRANT rather than passed in. v0.1.0 took a
   reader callable, which was the closure-authority shape this whole line of
   work exists to remove — in-process only, but the same species. Now the
   evaluator receives nothing but canonical data. */
export const JS_IMPLEMENTATION_ID = "impl-js-derive-v0.4.0";

function readerFromGrants(read_grants) {
  return {
    read: (r) => {
      const e = read_grants.exact[r];
      if (e === undefined) throw new Error("read-not-granted: " + r);
      return e;
    },
    scope: (q) => {
      if (!(q in read_grants.predicates)) throw new Error("scope-not-granted: " + q);
      return read_grants.predicates[q];
    },
  };
}

export function evaluate(ast, read_grants, inputs = {}) {
  // total over its input domain rather than only over the domain its callers
  // happen to supply: deriveLocally and the worker both validate first, but
  // `evaluate` is exported, and a raw TypeError is not a refusal
  const cg = checkGrants(read_grants);
  if (!cg.ok) throw new Error(cg.reason);
  const reader = readerFromGrants(read_grants);
  const exact = [], predicates = [], support = [];
  const ev = (n) => {
    if (n === null || typeof n !== "object" || typeof n.op !== "string")
      throw new Error("program-malformed-node");
    switch (n.op) {
      case "const": return OPS.const(n);
      case "input": {
        // inputs ONLY. The grant table is not addressable from here, which is
        // the entire content of the W-1 repair.
        if (!Object.prototype.hasOwnProperty.call(inputs, n.name))
          throw new Error("program-input-missing: " + n.name);
        return inputs[n.name];
      }
      case "read": {
        const r = reader.read(n.resource);
        exact.push([n.resource, r.version]);
        support.push(n.resource);
        return r.value;
      }
      case "scope": {
        const d = reader.scope(n.query);
        predicates.push([n.query, d]);
        return d;
      }
      case "cite": {
        const r = reader.read("warrant:" + n.name);
        exact.push(["warrant:" + n.name, r.version]);
        support.push("warrant:" + n.name);
        return r.value?.value;
      }
      case "add": case "sub": case "mul": case "len":
        return OPS[n.op](n, ev);
      default: throw new Error("program-unknown-op: " + n.op);
    }
  };
  const value = ev(ast);
  // the footprint is a canonical dependency SET; the trace keeps access order
  // and repeats. Two implementations that visit the same dependencies in
  // different orders agree on the first and differ on the second, which is why
  // only the first is inside the semantic projection.
  const dedupe = (pairs) => {
    const seen = new Map();
    for (const p of pairs) seen.set(canonicalBytes(p), p);
    return [...seen.values()].sort((x, y) => canonicalBytes(x) < canonicalBytes(y) ? -1 : 1);
  };
  return {
    value,
    witness: { op: ast.op, reads: dedupe(exact).length, scopes: dedupe(predicates).length },
    support: [...new Set(support)].sort(),
    read_footprint: { exact: dedupe(exact), predicates: dedupe(predicates) },
    read_trace: { exact, predicates },
  };
}

/* ── the authoritative side: request in, validated result out ─────────────
   No reader parameter: once a request exists, its grant snapshot IS the world
   slice the derivation is defined against, so the authority re-derives from
   the same bytes the executor had. Freshness against the LIVE world is a
   separate operation keyed on the footprint, which is exactly why the two
   records must not be collapsed. */
export function deriveLocally(registry, req, implementationId = JS_IMPLEMENTATION_ID) {
  const rc = checkRequest(req);
  if (!rc.ok) return { ok: false, reason: rc.reason };
  if ("expected_implementation_id" in req && req.expected_implementation_id !== implementationId)
    return { ok: false, reason: "implementation-mismatch: want " + req.expected_implementation_id +
      ", this is " + implementationId };
  const v = registry.verify(req.program_sem_id);
  if (!v.ok) return { ok: false, reason: v.reason };
  const ast = registry.get(req.program_sem_id);
  let out;
  try { out = evaluate(ast, req.read_grants, req.canonical_inputs); }
  catch (e) { return { ok: false, reason: "derivation-threw: " + e.message }; }
  const res = {
    request_id: req.request_id,
    program_sem_id: req.program_sem_id,
    implementation_id: implementationId,
    grant_id: req.grant_id,
    value: out.value, witness: out.witness,
    support: out.support, read_footprint: out.read_footprint, read_trace: out.read_trace,
  };
  const rr = checkResult(res, req);
  if (!rr.ok) return { ok: false, reason: rr.reason };
  return { ok: true, result: res };
}

/** Validate a result produced ELSEWHERE. Three independent checks, in an order
 *  chosen so each can fail on its own evidence:
 *    1. schema + request/program/grant binding + witness/footprint agreement
 *    2. the footprint is a SUBSET of the grant, at the granted versions —
 *       validated against the snapshot, not against the executor's word
 *    3. re-derivation, compared on the SEMANTIC projection only, so a C
 *       result and a JS result of the same program can agree
 *  implementation_id is checked against the caller's requirement if one was
 *  stated, and returned either way so the caller records who ran it. */
export function validateForeignResult(registry, req, res) {
  const rr = checkResult(res, req);
  if (!rr.ok) return { ok: false, reason: rr.reason };
  const fw = footprintWithinGrant(res.read_footprint, req.read_grants);
  if (!fw.ok) return { ok: false, reason: fw.reason };
  if ("expected_implementation_id" in req && res.implementation_id !== req.expected_implementation_id)
    return { ok: false, reason: "implementation-mismatch: want " + req.expected_implementation_id +
      ", result claims " + res.implementation_id };
  // the local re-derivation is JS by definition, so the caller's requirement —
  // which may name a foreign executor — is dropped rather than applied to us
  const { expected_implementation_id: _requirement, ...localReq } = req;
  const mine = deriveLocally(registry, localReq);
  if (!mine.ok) return { ok: false, reason: mine.reason };
  const a = canonicalBytes(semanticProjection(mine.result));
  const b = canonicalBytes(semanticProjection(res));
  return a === b
    ? { ok: true, implementation_id: res.implementation_id }
    : { ok: false, reason: "foreign-result-divergence" };
}
