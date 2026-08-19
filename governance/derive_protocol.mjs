/* ═══════════════════════════════════════════════════════════════════════════
   derive_protocol.mjs — v0.14.0 — the serialized derivation boundary

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

   WHAT v0.13.0 CHANGES: THE LAW WAS RIGHT AND IT STOPPED AT THE CONSTRUCTOR
   ─────────────────────────────────────────────────────────────────────────
   v0.12.0 wrote the rule below and applied it wherever authority state was
   being CONSTRUCTED — the executor catalog, the program registry, the issued
   request. Method arguments kept the older shape: authenticate the caller's
   object, then go on reading the caller's object.

       execute(req)   wasIssued(req)   → hashes ONE read of every field: PASSES
                      req.expected_implementation_id   → read again
                      { message: req } → read again by the host, and again by
                                         the worker's structured clone

   A request whose `program_sem_id` answers const(5) to the first read and
   const(999) to every read after it is therefore ISSUED as one program and
   EXECUTED as another. Both programs exist in the registry, so nothing is
   malformed and nothing fails closed. Acceptance, handed a fresh copy of the
   same time-varying object, re-derives 999 against 999, finds the provenance of
   an execution the authority genuinely drove, and returns

       { ok: true, validated: true, implementation_provenance: "observed" }

   for a result the authority never authorized. The same frozen request paired
   with the same 999 result is correctly refused as result-program-mismatch, so
   this is not fail-closed hygiene: the forgery is exactly the caller's retained
   ownership and nothing else. Frozen as P-7 in probe_reread_v13_repro.mjs.

       @7  the caller supplied MUTABLE DATA AUTHENTICATED ONCE, then read again
           while the authority exercised the authority that authentication bought

   @6 and @7 are one rule seen at two moments. @6: validate external X, read X
   again, store X'. @7: authenticate external X, then exercise authority using
   X'. The generalisation the ladder has been converging on, stated so that it
   covers arguments and not only constructor data:

       EVERY AUTHORITY OPERATION CONSUMES EITHER AN AUTHORITY-OWNED OBJECT OR
       ONE CANONICAL SNAPSHOT MADE AT ENTRY. No trust decision authenticates one
       read of external state and exercises authority using another.

   Mechanically: `ownCanonical` is called once at the top of every method taking
   a non-root data argument, `#issued` keeps the REQUEST and not merely its
   hash — "were these bytes issued?" was answerable before, "what did I issue?"
   was not, and every method that needed the second question had no choice but
   to re-read the caller — and `wasIssued` returns that owned request, which is
   what execute() and accept() use from there. The result side was closed in the
   same round rather than waiting to be found: `res` was read by six checks in
   sequence, and one argument to the right is where this ladder keeps going next.

   WHAT v0.12.0 CHANGED: SEVER BEFORE VALIDATING, NOT AFTER
   ────────────────────────────────────────────────────────
   v0.11.0 turned every authority-bearing OBJECT into constructor DATA — and
   then validated that data while the caller still owned it, copying afterwards.
   A getter is read more than once, and the reads need not agree.

       bind(ast)   read 1-2 → programSemId(ast) → the id of const(5)
                   read 3   → canonicalBytes(ast) → stores const(999)

   so the registry ends up keyed by one program's identity and holding another.
   `verify()` catches it later as program-id-mismatch — the system fails closed —
   but bind() has created the state its own comment calls impossible, and
   authorize() will issue a request for that id in the meantime. Frozen as P-6b
   in probe_snapshot_v12_repro.mjs, with P-6 the same defect in the executor
   catalog, where it does NOT fail closed: a getter that answers honestly for
   the three validating reads and maliciously for the fourth puts an entrypoint
   OUTSIDE its own hashed closure into the frozen internal catalog, and the
   un-hashed worker really runs.

       Untrusted data must be SEVERED BEFORE it is validated, not validated
       before it is severed.

   So the rule, and it is the one that should finally terminate this ladder:

       Every untrusted structure that becomes authority state is canonicalised
       into an OWNED SNAPSHOT exactly once; validation, identity computation and
       storage then operate only on that snapshot. No unowned mutable object is
       consulted twice across a trust decision.

   @6 is the sixth rung and the first that is not an object at all: label, name,
   action, semantic oracle, authority-bearing object, and now MUTABLE DATA READ
   TWICE. Round 24 already knew that canonicalBytes refuses a capability; what
   it did not say is that reading through it twice reintroduces one.

   WHAT v0.11.0 CHANGED: AN instanceof GUARD IS SATISFIED BY A SUBCLASS
   ────────────────────────────────────────────────────────────────────
   v0.10.0 built its own semantic registry from data — and one argument later
   still ACCEPTED a ready-made ObservedExecutionHost behind an `instanceof`
   guard. A two-method subclass passes it: override run() to throw, override
   observationOf() to return whatever provenance you like, and acceptance
   reports `observed` for an implementation that never ran. Frozen as P-5 in
   probe_hostown_v11_repro.mjs.

       @1 LABEL · @2 NAME · @3 ACTION · @4 SEMANTIC ORACLE · @5 the
       EXECUTION-AUTHORITY OBJECT ITSELF

   `instanceof` asks what a thing is DESCENDED FROM; the question is WHO BUILT
   IT. A tighter predicate would be the same mistake with a longer expression —
   `Object.getPrototypeOf(host) === ObservedExecutionHost.prototype` excludes
   the subclass and admits a Proxy. So the third constructor argument is an
   EXECUTOR CATALOG, which is data, and the authority calls
   `new ObservedExecutionHost(catalog)` itself against this module's own class
   binding, which no caller can substitute.

   WHAT v0.10.0 CHANGED: ACCEPTANCE TOOK ITS SEMANTIC ORACLE FROM THE CLAIMANT
   ───────────────────────────────────────────────────────────────────────────
   By v0.9.0 the authority owned issuance, the World reader, execution
   observations and freshness. It did not own the thing that says what a
   `program_sem_id` MEANS — `accept(registry, req, res)` took that, every time,
   from whoever was presenting the result. Issue a request for `const(5)`, hand
   acceptance `{verify: () => ({ok:true}), get: () => ({op:"const",value:999})}`,
   and 999 is accepted under the issued id. Re-derivation was working perfectly:
   it re-derived against the program the CLAIMANT nominated and agreed with
   itself. Frozen as P-4 in probe_semoracle_v10_repro.mjs.

       An authority cannot validate a semantic claim using a program resolver
       supplied by the claimant. Acceptance takes no proof from its caller,
       INCLUDING the mapping from semantic identity to semantic program.

   The supplier ladder as it stood at v0.10.0 — four rungs and one shape. It is
   seven now; SUPPLIER_LADDER below is the record, and every live surface derives
   its count and wording from that rather than from a sentence like this one:

       @1  the caller supplied the implementation LABEL
       @2  the caller supplied the registration NAME
       @3  the caller supplied the ACTION beside the artifact evidence
       @4  the caller supplied the SEMANTIC ORACLE used at acceptance

   An `instanceof ProgramRegistry` check would not have closed it: a Proxy, or a
   real registry the caller populated differently, satisfies the type and leaves
   the ownership wrong. So the registry is built at CONSTRUCTION from canonical
   program data — severed through canonicalBytes by ProgramRegistry.bind, which
   the authority calls itself — and no registry parameter crosses `execute` or
   `accept` again. `bindProgram` stays as an explicit authority operation and
   needs no second rule: ids are content-bound, so teaching the authority
   `const(999)` gives it a NEW id and cannot repoint `const(5)`'s.

   What a caller supplies is now an INTENT and a RESULT TO VALIDATE.

   WHAT v0.9.0 CHANGED: THE AUTHORITY HASHED ONE THING AND EXECUTED ANOTHER
   ───────────────────────────────────────────────────────────────────────
   v0.8.0 made the authority read and hash the artifact itself instead of
   believing a name, and then called a function the same caller had supplied
   beside the declaration:

       { artifact_files: X,   ← the EVIDENCE, hashed by the authority
         spawn: Y }           ← an INDEPENDENT caller-controlled ACTION

   Declare the genuine JS worker closure, name that digest as C, hand over a
   spawn() that evaluates in-process and stamps the result C, and acceptance
   returned implementation_provenance "observed" with no C anywhere. Frozen as
   P-3 in probe_execlaunch_v09_repro.mjs. The proposition "read bytes X, so
   launched X" did not follow; what held was "read bytes X, then invoked Y".

       Artifact observation does not establish execution provenance unless the
       mechanism invoked is mechanically DERIVED FROM the artifact observed.

   So the launcher argument is DELETED and there is no caller-supplied callable
   on this path at all. Launching moves to ObservedExecutionHost, constructed
   with an IMMUTABLE EXECUTOR CATALOG from which entrypoint and transport are
   both consequences of one entry. `nameArtifact` goes with it: the catalog IS
   the naming policy, and it is fixed before the authority exists. The far
   side's program image now comes from the authority's own registry rather than
   from a list the caller passed to the launcher.

   WHAT v0.8.0 CHANGED: EXECUTOR EXISTENCE IS NOT EXECUTION PROVENANCE
   ───────────────────────────────────────────────────────────────────
   v0.7.0 said "the host observes what it launched" and then shipped
   `registerExecutor(implementation_id)`, which launched nothing and observed
   nothing: it took a string, put it in a private Map, and returned a handle
   carrying a private Symbol. The Symbol proved *this authority minted this
   handle*. It did not prove *this authority observed this implementation
   execute this request and produce this result* — and that last sentence is
   the whole object. Frozen as P-2 in probe_execreg_v08_repro.mjs.

   Worse, `accept(registry, req, res, executor)` put a proof back in the
   caller's hands, which is exactly the shape round 17 removed from issuance.
   Even had registration really launched C, a valid C handle could have been
   paired with bytes produced anywhere else. So:

       request provenance   don't authenticate the grant;
                            authenticate the WHOLE REQUEST.        (round 17)
       execution provenance don't authenticate the executor handle;
                            authenticate the WHOLE EXECUTION EVENT. (here)

   Manual registration is DELETED. The authority is now the thing that runs an
   executor: `execute(req, launcher)` reads the artifact's bytes ITSELF and
   hashes them, looks that digest up in its own naming policy, spawns, sends
   THIS request, receives THESE bytes, and only then records an observation
   keyed by H(request_sem_id | canonical(the whole result)). `accept` takes no
   provenance argument and consults that privately held table. Change any byte
   of the result — including implementation_id — and the key misses.

   THREE IDENTITIES, because one string was answering three questions:

       implementation_family_id   what protocol implementation this is
       executable_artifact_id     H(the bytes the authority hashed)
       executor_session_id        this particular authority-driven launch

   The digest→name direction is a NAMING POLICY (`nameArtifact`) and is not an
   observation: it says "bytes with this digest are what we call impl-c-…",
   never that anything ran. It cannot be abused into the P-2 attack, because
   attributing a result to C now requires presenting an artifact whose bytes
   actually hash to C's digest.

   DECLARED OPEN, and stated conservatively on purpose. Hashing a path and then
   spawning that path proves *the host observed artifact X immediately before
   requesting execution of path P*. It is not a proof that the OS executed
   those exact bytes under every filesystem race, and it is NOT hardware-
   attested executable identity. That gap stays open and named.

   What this file does NOT yet claim: host confinement, determinism of a
   long-lived evaluator, TOCTOU-free artifact identity, or that any real
   derivation has been ported. Separate scopes, named separately in the grid.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
// Launching lives in ObservedExecutionHost and nowhere else. It holds no TRVM
// semantics — it cannot re-derive a result or say what one means — so importing
// it here couples the authority to a mechanism, not to a second opinion.
import { ObservedExecutionHost, digestArtifactFiles } from "./observed_execution_host.mjs";
export { digestArtifactFiles };

const H = (s) => createHash("sha256").update(s).digest("hex");
export const PROTOCOL_VERSION = "0.14.0";

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
    // SEVER FIRST. v0.11.0 hashed the caller's object and then cloned it, two
    // reads of state the caller still owned, so a getter could give the id one
    // program and the store another (P-6b). Everything below now reads `owned`,
    // which nobody else has a reference to.
    const owned = ownCanonical(ast);
    const id = programSemId(owned);
    const frozen = owned;
    const existing = this.#byId.get(id);
    if (existing && canonicalBytes(existing) !== canonicalBytes(frozen))
      throw new Error("program-rebind-refused: " + id);   // unreachable by construction; asserted anyway
    this.#byId.set(id, frozen);
    return id;
  }
  get(id) { return this.#byId.get(id); }
  has(id) { return this.#byId.has(id); }
  /** The registry's contents as canonical DATA, for an executor the authority
   *  launches. v0.8.0 let the caller hand the launcher its own program list,
   *  which meant the far side's registry was the caller's choice; the authority
   *  holds one already and there was never a reason to ask. */
  image() { return [...this.#byId.values()]; }
  ids() { return [...this.#byId.keys()].sort(); }
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

/** THE SNAPSHOT. One read of every field, and what comes back is ours.
 *
 *  This is the whole of the round-27 law expressed as a function, and it exists
 *  as a function rather than as a discipline for a reason: v0.12.0 stated the
 *  law correctly and then applied it only where authority state was being
 *  CONSTRUCTED. Method arguments kept their old shape — authenticate the
 *  caller's object, then keep reading the caller's object — which is P-7.
 *  A rule that must be remembered at each new entrypoint is a rule that will be
 *  forgotten at the next one, so there is one call, at the top of each method,
 *  and everything below it reads a value nobody else holds a reference to.
 *
 *  canonicalBytes does the severing AND the refusing: a function, a Map, a
 *  cycle or a non-finite number dies here, before any field has been examined.
 *  That ordering is round 27's other half — sever BEFORE validating.
 *
 *  DECLARED OPEN, and the distinction matters enough to state precisely.
 *  Elsewhere this module says "canonicalBytes refuses a capability". That is
 *  true of a capability as a VALUE — `{evil: () => …}` dies. It is NOT true
 *  that canonicalisation never runs caller code: reading `{get x() {…}}`
 *  executes a function, and a Proxy runs traps for ownKeys,
 *  getOwnPropertyDescriptor, getPrototypeOf, has and get while being
 *  serialised. So the accurate claim is
 *
 *      ownCanonical prevents caller-owned BEHAVIOUR FROM SURVIVING the
 *      canonicalisation boundary
 *
 *  and not
 *
 *      canonicalisation never invokes caller behaviour.
 *
 *  No such behaviour participates in any authority decision, because every
 *  decision happens on the captured value afterwards and nothing below the
 *  snapshot holds a reference to the external object — that is the invariant,
 *  and derive_realm_battery.mjs measures the full trap surface to detect a
 *  regression in it. But "no hostile same-realm code executes at ingestion" is
 *  a STRONGER property this API shape cannot have: an arbitrary JavaScript
 *  object can never be that boundary. Reaching it needs
 *
 *      canonical serialized text  →  parser owned by the authority  →  data
 *
 *  because a primitive string has no getters and no traps. That is the future
 *  serialized-wire boundary and it is not built. Named here rather than
 *  discovered later. */
export function ownCanonical(v) {
  return deepFreeze(JSON.parse(canonicalBytes(v)));
}

/** THE SUPPLIER LADDER, as data, because the prose copies drifted.
 *
 *  Every rung was found the same way: a caller-controlled field on the path to
 *  a verdict became the verdict. The count and the wording were hand-maintained
 *  in a module header, a battery diagnostic and each probe, and by round 27A the
 *  live battery was still printing "Four rungs" against a six-rung mechanism —
 *  a stale instrument in a tree whose recurring finding is stale instruments.
 *  Live surfaces derive both from here now. The frozen probes keep their own
 *  era's wording on purpose: each records the ladder as it stood when its
 *  witness was cut, and rewriting that would be falsifying a dated record. */
export const SUPPLIER_LADDER = Object.freeze([
  Object.freeze({ rung: 1, supplied: "LABEL",
    what: "the implementation label, deriveLocally's third parameter" }),
  Object.freeze({ rung: 2, supplied: "NAME",
    what: "the registration name, registerExecutor" }),
  Object.freeze({ rung: 3, supplied: "ACTION",
    what: "the action beside the artifact evidence, a launcher's spawn" }),
  Object.freeze({ rung: 4, supplied: "SEMANTIC ORACLE",
    what: "the program resolver used at acceptance, accept's registry parameter" }),
  Object.freeze({ rung: 5, supplied: "AUTHORITY-BEARING OBJECT",
    what: "the execution host itself, behind an instanceof guard" }),
  Object.freeze({ rung: 6, supplied: "MUTABLE DATA READ TWICE",
    what: "data validated while the caller still owned it, then read again to store" }),
  Object.freeze({ rung: 7, supplied: "MUTABLE DATA AUTHENTICATED ONCE",
    what: "a request proved issued, then read again to decide what to execute" }),
]);
export const LADDER_RUNGS = SUPPLIER_LADDER.length;
/** "label · name · action · …" — one string, derived, for diagnostics. */
export const ladderPhrase = () =>
  SUPPLIER_LADDER.map((r) => r.supplied.toLowerCase()).join(" · ");

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
/* ── TWO ENVELOPES, because non-semantic did not mean unverified ──────────
   v0.5.0 kept read_trace as a sibling of value and read_footprint, excluded it
   from the semantic projection, and then checked nothing about it. A foreign
   result whose trace was simply REVERSED — same footprint, same value — passed
   validateForeignResult and was accepted. Frozen as T-1 in
   probe_traceforge_v06_repro.mjs.

   The exclusion was right and the flat shape was what made it read as
   permission. A field inside DeriveResult looks authenticated by the same
   machinery as its neighbours; this one was not. So the envelopes are now
   explicit, and each carries its own rule:

     SEMANTIC RESULT      value · witness · support · read_footprint
       determines portable meaning. Two conforming implementations must agree
       on these canonical bytes, and this is what cross-implementation
       validation compares.

     EXECUTION EVIDENCE   implementation_id · read_trace
       conformance and provenance, NOT semantic identity. Excluded from the
       comparison and NOT excluded from checking: the core promises
       deterministic left-to-right evaluation, so a trace that disagrees with
       the authority's own re-derivation is a conformance failure of the
       implementation rather than a disagreement about the program.

   NON-SEMANTIC DOES NOT MEAN UNVERIFIED. That sentence is the whole round.
   Later, the semantic film supersedes this trace check — it witnesses the
   target machine's execution properly — and execution_evidence is where it
   will live. */
const RESULT_FIELDS = ["request_id", "program_sem_id", "grant_id", "semantic_result", "execution_evidence"];
const SEMANTIC_ENVELOPE = ["value", "witness", "support", "read_footprint"];
const EXECUTION_ENVELOPE = ["implementation_id", "read_trace"];
/** the portable half: the binding plus the semantic envelope, and nothing from
 *  execution evidence. Two implementations of the same program produce
 *  different provenance and different-but-conforming strategy metadata while
 *  meaning the same thing. */
export const SEMANTIC_RESULT_FIELDS = ["request_id", "program_sem_id", "grant_id", "semantic_result"];
export const SEMANTIC_ENVELOPE_FIELDS = SEMANTIC_ENVELOPE;
export const EXECUTION_ENVELOPE_FIELDS = EXECUTION_ENVELOPE;

export function semanticProjection(res) {
  const out = {};
  for (const f of SEMANTIC_RESULT_FIELDS) out[f] = res[f];
  return out;
}

/** TRACE CONFORMANCE — the check v0.5.0 did not have.
 *  The core fixes evaluation order (depth-first, `a` before `b`) precisely so
 *  that refusals and traces reproduce. An implementation whose trace disagrees
 *  with an honest re-derivation has not implemented TRVM-DERIVE-CORE-v1, even
 *  when it computed the same value from the same dependencies — so this is a
 *  CONFORMANCE verdict about the executor, reported separately from semantic
 *  agreement rather than folded into it. */
export function validateTraceConformance(localTrace, foreignTrace) {
  for (const kind of ["exact", "predicates"]) {
    if (canonicalBytes(foreignTrace?.[kind] ?? null) !== canonicalBytes(localTrace[kind]))
      return { ok: false, reason: "trace-nonconforming: " + kind };
  }
  return { ok: true };
}

export function checkRequestOwned(req) {
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

export function checkResultOwned(res, req) {
  if (res === null || typeof res !== "object" || Array.isArray(res))
    return { ok: false, reason: "result-not-an-object" };
  const keys = Object.keys(res).sort();
  if (canonicalBytes(keys) !== canonicalBytes([...RESULT_FIELDS].sort()))
    return { ok: false, reason: "result-schema: [" + keys.join(",") + "]" };
  try { canonicalBytes(res); }
  catch (e) { return { ok: false, reason: "result-" + e.message }; }
  for (const [field, want] of [["semantic_result", SEMANTIC_ENVELOPE], ["execution_evidence", EXECUTION_ENVELOPE]]) {
    const env = res[field];
    if (env === null || typeof env !== "object" || Array.isArray(env))
      return { ok: false, reason: "result-" + field + "-not-an-object" };
    const ek = Object.keys(env).sort();
    if (canonicalBytes(ek) !== canonicalBytes([...want].sort()))
      return { ok: false, reason: "result-" + field + "-schema: [" + ek.join(",") + "]" };
  }
  // a result may not claim to be about a different request, program or grant
  if (res.request_id !== req.request_id) return { ok: false, reason: "result-request-mismatch" };
  if (res.program_sem_id !== req.program_sem_id) return { ok: false, reason: "result-program-mismatch" };
  if (res.grant_id !== req.grant_id) return { ok: false, reason: "result-grant-mismatch" };
  const impl = res.execution_evidence.implementation_id;
  if (typeof impl !== "string" || !impl.startsWith("impl-"))
    return { ok: false, reason: "result-implementation-id-malformed" };
  const fp = res.semantic_result.read_footprint;
  if (fp === null || typeof fp !== "object" || !Array.isArray(fp.exact) || !Array.isArray(fp.predicates))
    return { ok: false, reason: "result-footprint-malformed" };
  const tr = res.execution_evidence.read_trace;
  if (tr === null || typeof tr !== "object" || !Array.isArray(tr.exact) || !Array.isArray(tr.predicates))
    return { ok: false, reason: "result-trace-malformed" };
  // the footprint must BE the canonical set of the trace: sorted, deduplicated.
  // A result carrying a sequence where a set is required is refused rather than
  // silently normalized, because normalizing on receipt would let two
  // implementations disagree about the bytes they each committed to.
  for (const kind of ["exact", "predicates"]) {
    const seen = new Map();
    for (const pr of tr[kind]) seen.set(canonicalBytes(pr), pr);
    const want = [...seen.values()].sort((x, y) => canonicalBytes(x) < canonicalBytes(y) ? -1 : 1);
    if (canonicalBytes(fp[kind]) !== canonicalBytes(want))
      return { ok: false, reason: "result-footprint-not-canonical-set: " + kind };
  }
  // the witness must agree with the footprint it accompanies, checked before
  // any re-derivation so a lying claim is refused on its own evidence
  const w = res.semantic_result.witness;
  if (w?.reads !== fp.exact.length || w?.scopes !== fp.predicates.length)
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
export const JS_IMPLEMENTATION_ID = "impl-js-derive-v0.14.0";

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
export function deriveLocallyOwned(registry, req) {
  // NO implementation parameter. v0.6.0 took one, defaulted to JS, and let a
  // caller stamp the JS evaluator's output "impl-c-derive-…" — after which the
  // authority compared the caller's expectation against the caller's own label
  // and agreed with itself. Frozen as P-1 in probe_execclaim_v07_repro.mjs.
  // An implementation's identity comes from the implementation.
  const implementationId = JS_IMPLEMENTATION_ID;
  const rc = checkRequestOwned(req);
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
    grant_id: req.grant_id,
    semantic_result: {
      value: out.value, witness: out.witness,
      support: out.support, read_footprint: out.read_footprint,
    },
    execution_evidence: { implementation_id: implementationId, read_trace: out.read_trace },
  };
  const rr = checkResultOwned(res, req);
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
export function validateForeignResultOwned(registry, req, res) {
  const rr = checkResultOwned(res, req);
  if (!rr.ok) return { ok: false, reason: rr.reason };
  const fw = footprintWithinGrant(res.semantic_result.read_footprint, req.read_grants);
  if (!fw.ok) return { ok: false, reason: fw.reason };
  // NO PROVENANCE HERE. This function establishes semantic agreement and trace
  // conformance. Comparing req.expected_implementation_id against the string
  // inside the result compares a claim with a claim: a canonical result arriving
  // from outside is an untrusted EXECUTION CLAIM however perfect its bytes are.
  // Provenance is the authority's job, against what the host OBSERVED it launch.
  const impl = res.execution_evidence.implementation_id;
  // the local re-derivation is JS by definition, so the caller's requirement —
  // which may name a foreign executor — is dropped rather than applied to us
  const { expected_implementation_id: _requirement, ...localReq } = req;
  const mine = deriveLocallyOwned(registry, localReq);
  if (!mine.ok) return { ok: false, reason: mine.reason };
  const a = canonicalBytes(semanticProjection(mine.result));
  const b = canonicalBytes(semanticProjection(res));
  if (a !== b) return { ok: false, reason: "foreign-result-divergence", semantic_agreement: false };
  // SEMANTIC AGREEMENT AND TRACE CONFORMANCE ARE TWO VERDICTS. Reporting them
  // separately is the point: "same meaning, different strategy" and "wrong
  // answer" are different diagnoses, and v0.5.0 could make neither because it
  // never looked at the trace at all.
  const tc = validateTraceConformance(mine.result.execution_evidence.read_trace,
    res.execution_evidence.read_trace);
  if (!tc.ok) return { ok: false, reason: tc.reason, semantic_agreement: true, trace_conforms: false };
  // implementation_claimed, not implementation_id: this is what the result SAYS
  return { ok: true, semantic_agreement: true, trace_conforms: true, implementation_claimed: impl };
}

/* ── THE PUBLIC EDGE OF THE VALIDATORS ────────────────────────────────────
   The five functions above end in `Owned`, and the suffix is a PRECONDITION
   rather than a decoration: they read their arguments field by field, several
   times, and they are only sound over structures the caller already owns.
   `DerivationAuthority` satisfies that mechanically — every call site passes
   `issued`, `ownRes` or `ownIntent` — which is why v0.13.0 has no forgery here.

   They are also EXPORTED, and that is the hazard. Measured against a Proxy-
   wrapped but otherwise valid request, one `checkRequestOwned` call touches

       ownKeys 2 · getOwnPropertyDescriptor 10 · getPrototypeOf 1 · get 13 · has 1

   so "a pure function over data the caller already owns" is only the second
   half of a sentence whose first half is a precondition nothing was enforcing.
   A second authority built on these exports would recreate P-7 without writing
   a line of new trust logic.

   So the reusable names snapshot once and delegate. The authority keeps calling
   the `Owned` forms directly, because paying for a second canonicalisation of
   something it just canonicalised would be ceremony, not safety. */
export const checkRequest = (req) => {
  try { return checkRequestOwned(ownCanonical(req)); }
  catch (e) { return { ok: false, reason: "request-not-canonical: " + e.message }; }
};
export const checkResult = (res, req) => {
  try { return checkResultOwned(ownCanonical(res), ownCanonical(req)); }
  catch (e) { return { ok: false, reason: "result-not-canonical: " + e.message }; }
};
export const checkIntent = (intent) => {
  try { return checkIntentOwned(ownCanonical(intent)); }
  catch (e) { return { ok: false, reason: "intent-not-canonical: " + e.message }; }
};
export const deriveLocally = (registry, req) => {
  try { return deriveLocallyOwned(registry, ownCanonical(req)); }
  catch (e) { return { ok: false, reason: "request-not-canonical: " + e.message }; }
};
export const validateForeignResult = (registry, req, res) => {
  try { return validateForeignResultOwned(registry, ownCanonical(req), ownCanonical(res)); }
  catch (e) { return { ok: false, reason: "result-not-canonical: " + e.message }; }
};

/* ── FRESHNESS: a different question from containment ─────────────────────
   footprintWithinGrant answers a HISTORICAL question — was every claimed read
   inside the snapshot this derivation received? validateFootprintFresh answers
   a TEMPORAL one — are those dependencies still current NOW, at the moment of
   acceptance? Both can be satisfied about a World that has moved: executor and
   authority agree perfectly about an old snapshot, so re-derivation can never
   detect staleness. That witness is frozen in probe_stalegrant_v03_repro.mjs.

   It keys on the FOOTPRINT, never on a global vclock. An unrelated write must
   not invalidate a derivation that did not depend on it — that is the whole
   reason the footprint is the dependency record and the grant is not, and a
   vclock rule would undo the separation from the other side. */
export function validateFootprintFresh(liveReader, footprint) {
  for (const [r, ver] of footprint.exact ?? []) {
    let cur;
    try { cur = liveReader.read(r); }
    catch (e) { return { ok: false, reason: "stale-read-unreadable: " + r + " (" + e.message + ")" }; }
    if (cur?.version !== ver)
      return { ok: false, reason: "stale-read: " + r + " granted@" + ver + " live@" + cur?.version };
  }
  for (const [q, d] of footprint.predicates ?? []) {
    let cur;
    try { cur = liveReader.scope(q); }
    catch (e) { return { ok: false, reason: "stale-scope-unreadable: " + q + " (" + e.message + ")" }; }
    if (canonicalBytes(cur) !== canonicalBytes(d))
      return { ok: false, reason: "stale-scope: " + q };
  }
  return { ok: true };
}

/* ── ISSUANCE: what an authority-issued request actually authenticates ────
   grant_id is a hash of the grant, and a hash authenticates content to itself.
   The first draft of this layer recorded `request_id -> grant_id` and derived
   request_id from (intent_id, grant_id) — so "was this issued?" was answered
   about a GRANT while the thing being accepted was a REQUEST. Swapping
   canonical_inputs under an untouched request_id passed. Frozen as I-1..I-3 in
   probe_issuebind_v05_repro.mjs.

   Three changes, none of them cryptographic:

   1. ISSUANCE BINDS THE WHOLE REQUEST. request_sem_id = H(canonical request),
      recorded at issue and recomputed at acceptance. Any change to any field is
      a different request rather than the same request with different content.
   2. THE OPTIONS BAG IS GONE. It spread `...over` after every authority-decided
      field. A caller may now REQUEST exactly one thing —
      expected_implementation_id — which is a requirement on the executor, not
      authority content.
   3. ACCEPTANCE IS A METHOD, NOT A FUNCTION WITH PARAMETERS. The issuance table
      and the live reader are closed over. A free function taking `issuer` and
      `liveReader` as arguments — with issuer defaulting to null — let the
      caller supply both proofs of its own authority, and a fake reader replayed
      a stale grant into an acceptance.

   A signature or MAC is added when — and only when — the grant crosses a real
   trust boundary, is persisted and replayed later, is delegated between
   authorities, or must be proved to an independent verifier. Adding one today
   would authenticate the authority to itself. */
const INTENT_REQUIRED = ["intent_id", "program_sem_id", "canonical_inputs", "requested_resources"];
const AUTHORIZE_OPTIONS = ["expected_implementation_id"];

export function checkIntentOwned(intent) {
  if (intent === null || typeof intent !== "object" || Array.isArray(intent))
    return { ok: false, reason: "intent-not-an-object" };
  const keys = Object.keys(intent).sort();
  if (canonicalBytes(keys) !== canonicalBytes([...INTENT_REQUIRED].sort()))
    return { ok: false, reason: "intent-schema: [" + keys.join(",") + "]" };
  try { canonicalBytes(intent); }
  catch (e) { return { ok: false, reason: "intent-" + e.message }; }
  if (typeof intent.program_sem_id !== "string" || !intent.program_sem_id.startsWith("psem-"))
    return { ok: false, reason: "intent-program-id-malformed" };
  if (typeof intent.intent_id !== "string" || intent.intent_id.length === 0)
    return { ok: false, reason: "intent-id-malformed" };
  const rr = intent.requested_resources;
  if (rr === null || typeof rr !== "object" || Array.isArray(rr))
    return { ok: false, reason: "intent-requested-resources-not-an-object" };
  const rk = Object.keys(rr).sort();
  if (canonicalBytes(rk) !== canonicalBytes(["exact", "predicates"]))
    return { ok: false, reason: "intent-requested-resources-schema: [" + rk.join(",") + "]" };
  for (const kind of ["exact", "predicates"])
    if (!Array.isArray(rr[kind]) || rr[kind].some((x) => typeof x !== "string"))
      return { ok: false, reason: "intent-requested-" + kind + "-not-a-string-list" };
  if (intent.canonical_inputs === null || typeof intent.canonical_inputs !== "object" ||
      Array.isArray(intent.canonical_inputs))
    return { ok: false, reason: "intent-inputs-not-an-object" };
  return { ok: true };
}

/** The identity of a request AS A WHOLE. This is what issuance records and what
 *  acceptance recomputes, which is the entire content of the I-1 repair. */
export function requestSemId(req) {
  return "rsem-" + H("TRVM-REQUEST-SEM-v1|" + canonicalBytes(req));
}

/** The identity of an EXECUTION EVENT as a whole: which request went out, and
 *  which bytes came back. This is the round-17 lesson applied one level up.
 *  Round 17: don't authenticate the grant, authenticate the whole request.
 *  Here:     don't authenticate the executor handle, authenticate the whole
 *            execution event.
 *
 *  Because the key covers `canonicalBytes(res)` and not a projection of it,
 *  relabelling a result AFTER execution — the F-7 forgery — moves the key and
 *  the observation is simply not there. That is why there is no separate
 *  "was this relabelled?" check: the question cannot be asked of a table it
 *  cannot be found in. */
export const DERIVE_EXEC_DOMAIN = "TRVM-DERIVE-EXEC-v1";

/** THE AUTHORITY. It holds the World reader and the issuance table, it is the
 *  only constructor of a DeriveRequest, and acceptance is one of its methods so
 *  that neither proof can arrive as an argument. */
export class DerivationAuthority {
  #issued = new Map();
  /** request_id → the canonical invocation bytes THIS authority actually sent,
   *  one entry per distinct invocation.
   *
   *  WHY THIS EXISTS. Acceptance used to ask the observation table about a past
   *  execution by REBUILDING the invocation out of `this.#registry.image()` —
   *  that is, out of state as it stands now. `bindProgram()` is an explicit and
   *  legitimate authority operation, and it grows that image, so installing an
   *  unrelated program B silently made the provenance of an earlier, genuine
   *  execution of A disappear:
   *
   *      execute(A) → accept → implementation_provenance "observed"
   *      bindProgram(B)
   *      accept(same request, same result) → implementation-provenance-unavailable
   *
   *  It fails closed, so it forges nothing. It is still wrong: unrelated future
   *  configuration must not erase the evidence of what previously ran. A list
   *  rather than one entry because executing the same request before and after
   *  a bind produces two genuinely different invocations, and both happened. */
  #executions = new Map();
  #registry = new ProgramRegistry();
  #host;
  #reader;
  /** EVERY ORACLE THIS AUTHORITY CONSULTS IS FIXED HERE.
   *
   *  The World reader (round 17), the semantic registry (P-4) and the execution
   *  host with its immutable catalog (P-3) are all constructor-time. The
   *  registry is BUILT rather than accepted: `programImage` is canonical program
   *  DATA, and ProgramRegistry.bind severs it through canonicalBytes, so the
   *  authority ends up owning its semantic oracle rather than sharing an object
   *  with whoever built it. Passing a ready-made registry would satisfy any type
   *  check and leave the ownership exactly where P-4 found it. */
  constructor(reader, programImage = [], executorCatalog = null) {
    if (!reader || typeof reader.read !== "function" || typeof reader.scope !== "function")
      throw new Error("authority-requires-a-world-reader");
    if (!Array.isArray(programImage))
      throw new Error("authority-program-image-must-be-a-list");
    this.#reader = reader;
    // THE HOST IS BUILT, NOT ACCEPTED. v0.10.0 took one behind an instanceof
    // guard, which a two-method subclass satisfies while overriding both the
    // execution and the observation (P-5). `new` here binds this module's own
    // class, so there is nothing for a caller to substitute and no method for
    // it to shadow.
    this.#host = executorCatalog === null ? null : new ObservedExecutionHost(executorCatalog);
    for (const ast of programImage) this.#registry.bind(ast);
    Object.freeze(this);
  }

  /** Teaching the authority a new program is an explicit AUTHORITY operation,
   *  and it is safe for the reason the id exists at all: the id IS the
   *  program's hash, so `const(999)` gets its own and cannot become `const(5)`.
   *  Growing the registry therefore needs no second rule. */
  bindProgram(ast) { return this.#registry.bind(ast); }
  programIds() { return this.#registry.ids(); }
  programOf(id) { return this.#registry.get(id); }

  /** intent in — authority-issued, owned, frozen request out.
   *
   *  BOTH arguments are snapshotted at entry. v0.12.0 validated `intent` in
   *  place and then read it four more times to build the body, and read
   *  `options.expected_implementation_id` twice; the issued request was severed
   *  at the end, so the outcome was self-consistent and the ordering was still
   *  wrong. The law is about every non-root data argument, not only the ones
   *  where a witness has been written. */
  authorize(intent, options = {}) {
    let ownIntent, ownOptions;
    try { ownIntent = ownCanonical(intent); }
    catch (e) { return { ok: false, reason: "intent-not-canonical: " + e.message }; }
    try { ownOptions = ownCanonical(options); }
    catch (e) { return { ok: false, reason: "authorize-options-not-canonical: " + e.message }; }
    if (ownOptions === null || typeof ownOptions !== "object" || Array.isArray(ownOptions))
      return { ok: false, reason: "authorize-options-not-an-object" };
    const c = checkIntentOwned(ownIntent);
    if (!c.ok) return { ok: false, reason: c.reason };
    const unknown = Object.keys(ownOptions).filter((k) => !AUTHORIZE_OPTIONS.includes(k)).sort();
    if (unknown.length)
      return { ok: false, reason: "authorize-options-unknown: [" + unknown.join(",") + "]" };
    if ("expected_implementation_id" in ownOptions &&
        typeof ownOptions.expected_implementation_id !== "string")
      return { ok: false, reason: "authorize-expected-implementation-malformed" };
    let g;
    try { g = resolveGrants(this.#reader, ownIntent.requested_resources); }
    catch (e) { return { ok: false, reason: e.message }; }
    const body = {
      program_sem_id: ownIntent.program_sem_id,
      canonical_inputs: ownIntent.canonical_inputs,
      read_grants: g.read_grants,
      grant_id: g.grant_id,
      ...("expected_implementation_id" in ownOptions
        ? { expected_implementation_id: ownOptions.expected_implementation_id } : {}),
    };
    const request_id = "req-" + H("TRVM-REQUEST-v1|" + ownIntent.intent_id + "|" + canonicalBytes(body));
    const req = ownCanonical({ request_id, ...body });
    const rc = checkRequestOwned(req);
    if (!rc.ok) return { ok: false, reason: rc.reason };
    // THE ISSUED REQUEST ITSELF IS KEPT, not only its identity. v0.12.0 stored
    // the semantic hash, which can answer "were these bytes issued?" and cannot
    // answer "what did I issue?" — so every method that needed the second
    // question had no choice but to re-read the caller's object. That is P-7.
    this.#issued.set(request_id, Object.freeze({ request_sem_id: requestSemId(req), request: req }));
    return { ok: true, request: req };
  }

  /** THE AUTHORITY RUNS THE EXECUTOR, AND CANNOT BE HANDED ONE.
   *
   *  v0.8.0 took a `launcher` whose `artifact_files` it hashed and whose
   *  `spawn` it then called — two fields of one caller-supplied object, with
   *  nothing binding them. Declaring the real JS closure while spawning
   *  something else produced provenance "observed" for an implementation that
   *  never ran (P-3). So there is no launcher parameter. The family is named by
   *  the REQUEST (or by the single catalogued default), the entrypoint and the
   *  transport are both read from the host's immutable catalog, and the far
   *  side's program image comes from THIS registry rather than from a list a
   *  caller passed alongside.
   *
   *  What crosses is data: `{init, message}`, refused outright if it carries a
   *  callable, which is the mechanical reason an action cannot ride along with
   *  a declaration any more. */
  async execute(req) {
    if (!this.#host) return { ok: false, reason: "authority-has-no-execution-host" };
    const iss = this.wasIssued(req);
    if (!iss.ok) return { ok: false, reason: iss.reason };
    // FROM HERE THE ARGUMENT IS NOT READ AGAIN. v0.12.0 authenticated `req` and
    // then kept reading it — once for the family, once more when the host
    // canonicalised the invocation, once more when the worker cloned it — so a
    // request whose program_sem_id answered const(5) to wasIssued and const(999)
    // to everyone after it was issued as one program and EXECUTED as another
    // (P-7). `issued` is the authority's own copy of what it actually issued.
    const issued = iss.request;
    let family = issued.expected_implementation_id;
    if (family === undefined) {
      const fams = this.#host.families();
      if (fams.length !== 1)
        return { ok: false, reason: "execute-implementation-ambiguous: catalog holds [" +
          fams.join(",") + "] and the request names none" };
      family = fams[0];
    }
    const invocation = { init: { programs: this.#registry.image() }, message: issued };
    const r = await this.#host.run(family, DERIVE_EXEC_DOMAIN, invocation);
    if (!r.ok) return { ok: false, reason: r.reason };
    // RECORD WHAT ACTUALLY CROSSED, in the host's own bytes rather than in a
    // reconstruction of them. This is the historical fact acceptance needs.
    if (typeof r.input_canonical === "string") {
      const seen = this.#executions.get(issued.request_id) ?? [];
      if (!seen.includes(r.input_canonical)) seen.push(r.input_canonical);
      this.#executions.set(issued.request_id, seen);
    }
    if (!r.output?.ok) return { ok: false, reason: r.output?.reason ?? "execution-returned-nothing" };
    return { ok: true, result: r.output.result,
      executor_session_id: r.executor_session_id,
      executable_artifact_id: r.executable_artifact_id };
  }

  /** Read-only view, for batteries and diagnostics. Returns a COPY.
   *  Severs both arguments, because a diagnostic that reads a live object twice
   *  is the same defect wearing a smaller hat. */
  observationOf(req, res) {
    if (!this.#host) return null;
    let ownReq, ownRes;
    try { ownReq = ownCanonical(req); ownRes = ownCanonical(res); }
    catch { return null; }
    // THE INVOCATIONS THIS AUTHORITY ACTUALLY SENT FOR THIS REQUEST, not one
    // rebuilt from the registry as it stands now. A request this authority
    // never executed has no entry and gets null, which is the honest answer:
    // there is no execution of it for the authority to have observed.
    const sent = this.#executions.get(ownReq?.request_id) ?? [];
    const hits = [];
    for (const ic of sent) {
      const o = this.#host.observationOfCanonical(DERIVE_EXEC_DOMAIN, ic,
        { ok: true, result: ownRes });
      if (o) hits.push(o);
    }
    if (!hits.length) return null;
    // MERGED, not first-hit, and for the round-24 reason. The same request run
    // before and after a bindProgram() is two invocations; if both produced
    // these bytes, both are things this authority observed, and returning the
    // first would report one launch as though it were the only one. What is
    // true is "these recorded sessions are known to have produced these
    // request/result bytes", and where there are several they are all here.
    const families = [...new Set(hits.flatMap((o) => o.implementation_families))];
    return {
      implementation_family_id: families.length === 1 ? families[0] : null,
      implementation_families: families,
      executable_artifact_id: hits[0].executable_artifact_id,
      executor_sessions: [...new Set(hits.flatMap((o) => o.executor_sessions))],
    };
  }

  /** Was THIS request — every field of it — issued by THIS authority?
   *
   *  AND, WHEN IT WAS, WHICH ONE. The second half is the P-7 repair. Answering
   *  only the first question forces every caller of this method to go on using
   *  the object it just authenticated, and an object that is authenticated is
   *  not thereby owned: the bytes that passed are one read, and the next read
   *  need not agree with them. So the argument is severed once — that snapshot
   *  is what gets hashed and compared — and what comes back is the AUTHORITY'S
   *  OWN copy of the request, which is what every caller uses from here.
   *
   *  `request` is deep-frozen and safe to hand out; it is the same object the
   *  caller was given at authorize() time. */
  wasIssued(req) {
    let snapshot;
    try { snapshot = ownCanonical(req); }
    catch (e) { return { ok: false, reason: "request-not-canonical: " + e.message }; }
    const stored = this.#issued.get(snapshot?.request_id);
    if (stored === undefined) return { ok: false, reason: "grant-not-issued-by-this-authority" };
    return stored.request_sem_id === requestSemId(snapshot)
      ? { ok: true, request: stored.request }
      : { ok: false, reason: "request-not-as-issued" };
  }

  /** ACCEPTANCE — everything a result must clear before an authority may act on
   *  it, in one call, in an order where each stage fails on its own evidence:
   *
   *    1. issuance   this request, whole, is one THIS authority issued
   *    2. validation schema, footprint-within-grant, re-derivation, trace
   *    3. provenance the OBSERVED execution event, not a proof handed in
   *    4. freshness  the footprint's dependencies are still live NOW
   *
   *  IT TAKES NO PROVENANCE ARGUMENT, and v0.7.0's taking one was the round-17
   *  defect reintroduced one level up: `accept(registry, req, res, executor)`
   *  put a proof back in the caller's hands. Provenance is now looked up from
   *  the authority's own observation table, under a key computed over the whole
   *  execution event, so there is nothing for a caller to supply and nothing
   *  for it to pair wrongly.
   *
   *  IT DOES NOT RETURN `committable`, and the earlier draft's doing so was
   *  wrong. One call cannot make a result committable, because the World can
   *  move between this returning and the caller applying. What it establishes
   *  is `validated` and `fresh_at_check` — an observation at a moment. The
   *  composition that actually commits belongs to the World/Maintainer:
   *
   *      acquire the authoritative lock
   *        accept()            <- this
   *        prepared apply      <- deterministic, no hostile callback between
   *        seal the receipt
   *      release
   *
   *  No lock capability is exported to reach that: rounds 9B-9C are the record
   *  of what happens when transaction authority gets passed around. */
  accept(req, res) {
    const iss = this.wasIssued(req);
    if (!iss.ok) return { ok: false, reason: iss.reason };
    // BOTH SIDES ARE OWNED BEFORE ANY CHECK RUNS. The request is the
    // authority's own copy of what it issued; the result is snapshotted once,
    // here, and the six checks below — schema, footprint containment,
    // re-derivation, trace conformance, provenance lookup, freshness — every
    // one of which used to read the caller's live object, all read this.
    //
    // The request side is P-7. The result side is its sibling and was closed at
    // the same time on purpose: a caller who cannot vary the request while it is
    // being validated can still vary the result, and "the same class of defect
    // one argument to the right" is how this ladder has gone seven times.
    const issued = iss.request;
    let ownRes;
    try { ownRes = ownCanonical(res); }
    catch (e) { return { ok: false, reason: "result-not-canonical: " + e.message }; }
    // THE ORACLE IS THIS AUTHORITY'S OWN. v0.9.0 took it as the first parameter,
    // so re-derivation ran against the program the CLAIMANT nominated and
    // agreed with itself (P-4). Nothing about re-derivation was wrong; what was
    // wrong was who chose the program it re-derived.
    const v = validateForeignResultOwned(this.#registry, issued, ownRes);
    if (!v.ok) return v;

    // ── PROVENANCE, against an execution event this authority drove ───────
    // The lookup is the check. A result produced by JS and relabelled C hashes
    // to a different key and is simply absent; a genuine C observation cannot
    // be "attached" to other bytes because nothing is attached to anything.
    // The table lives in the HOST, which is the only thing that launches, so
    // there is no second place an observation could come from.
    const observed = this.observationOf(issued, ownRes) ?? undefined;
    if ("expected_implementation_id" in issued) {
      if (observed === undefined)
        return { ok: false, reason: "implementation-provenance-unavailable" };
      if (observed.implementation_family_id !== issued.expected_implementation_id)
        return { ok: false, reason: "implementation-mismatch: want " +
          issued.expected_implementation_id + ", observed " + observed.implementation_family_id };
    }
    // Still has content, and a narrower one than it had: with the whole result
    // inside the key this can no longer fire on relabelling. It fires when an
    // EXECUTOR's self-assertion disagrees with the name its own bytes carry
    // under the authority's policy — a conformance fault of the implementation.
    if (observed !== undefined && v.implementation_claimed !== observed.implementation_family_id)
      return { ok: false, reason: "implementation-claim-contradicts-observation: claims " +
        v.implementation_claimed + ", observed " + observed.implementation_family_id };

    const f = validateFootprintFresh(this.#reader, ownRes.semantic_result.read_footprint);
    if (!f.ok) return { ok: false, reason: f.reason };

    // trace_conforms is NOT in the success shape. On success it is redundant —
    // acceptance could not have got here without it — and a boolean per check
    // invites a reader to weigh them. It stays in validateForeignResult and in
    // the failure diagnostics, where `semantic_agreement: true, trace_conforms:
    // false` is exactly the distinction worth having. fresh_at_check stays
    // because its temporal limitation is meaningful: it is an observation at a
    // moment, not a promise about the next one.
    //
    // THREE IDENTITIES on success, because one string was answering three
    // questions. The family says what implementation this is; the artifact
    // digest says which bytes the authority hashed; the session id says which
    // launch. In-process deriveLocally produces none of them and reports
    // "unavailable" — the authority ran the evaluator in its own realm and
    // there is no launch to observe, so manufacturing an observation for it
    // would be the same category error P-2 is about.
    // executor_sessionS, plural, and that is a correction rather than a style
    // choice. The key is over BYTES, so two launches producing byte-identical
    // output share it; v0.8.0 overwrote the first and then reported one
    // executor_session_id as though it named the launch that produced the copy
    // in hand. It never did. What is true is "these recorded sessions are known
    // to have produced these request/result bytes", and where there are several
    // they are all here.
    return observed === undefined
      ? { ok: true, validated: true, fresh_at_check: true,
          implementation_provenance: "unavailable" }
      : { ok: true, validated: true, fresh_at_check: true,
          implementation_provenance: "observed",
          implementation_id: observed.implementation_family_id,
          executable_artifact_id: observed.executable_artifact_id,
          executor_sessions: observed.executor_sessions };
  }
}
Object.freeze(DerivationAuthority.prototype);
