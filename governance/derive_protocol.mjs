/* ═══════════════════════════════════════════════════════════════════════════
   derive_protocol.mjs — v0.1.0 — the serialized derivation boundary

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
      carries executable provenance separately. Committing an executable hash
      into the semantic id would have made cross-runtime films
      implementation-specific — the reason the split was declared before this
      round rather than during it.
   3. THE BOUNDARY IS THE CANONICAL VALUE DOMAIN, not "structuredClone
      succeeded". The 9D.3 Map witness already disqualified that phrase by
      proving structuredClone and JSON.stringify disagree about what a value is.
      Function, Map, Set, Date, SharedArrayBuffer, MessagePort, class instances
      and transferable handles are refused: those are capabilities, not data.

   What this file does NOT yet claim: host confinement, determinism of a
   long-lived evaluator, or that any real derivation has been ported. Those are
   separate scopes and the grid names them separately.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";

const H = (s) => createHash("sha256").update(s).digest("hex");

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

/* ── PROGRAM: a canonical AST, not a closure ──────────────────────────────
   Small on purpose. The point of the first round is not expressive power; it
   is that the thing crossing the boundary is DATA whose identity is its
   content. Growing the language later must not change existing program ids,
   which is why every node is a plain tagged object and the id is taken over
   canonical bytes. */
const OPS = {
  const: (n) => n.value,
  read: null, scope: null, cite: null,          // effectful — handled by the evaluator
  add: (n, ev) => ev(n.a) + ev(n.b),
  sub: (n, ev) => ev(n.a) - ev(n.b),
  mul: (n, ev) => ev(n.a) * ev(n.b),
  len: (n, ev) => { const v = ev(n.a); if (!Array.isArray(v)) throw new Error("program-type: len of non-array"); return v.length; },
  input: null,
};

export function programSemId(ast) {
  return "psem-" + H("TRVM-PROGRAM-v1|" + canonicalBytes(ast));
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

/* ── the request/result schemas ───────────────────────────────────────────
   Everything crossing the boundary is checked against the canonical domain
   FIRST. A request that cannot be represented cannot become authority. */
const REQUEST_FIELDS = ["request_id", "program_sem_id", "implementation_id", "canonical_inputs", "grants"];
const RESULT_FIELDS = ["request_id", "program_sem_id", "value", "witness", "support", "read_footprint"];

export function checkRequest(req) {
  if (req === null || typeof req !== "object" || Array.isArray(req))
    return { ok: false, reason: "request-not-an-object" };
  const keys = Object.keys(req).sort();
  const want = [...REQUEST_FIELDS].sort();
  if (canonicalBytes(keys) !== canonicalBytes(want))
    return { ok: false, reason: "request-schema: [" + keys.join(",") + "]" };
  try { canonicalBytes(req); }
  catch (e) { return { ok: false, reason: "request-" + e.message }; }
  if (typeof req.program_sem_id !== "string" || !req.program_sem_id.startsWith("psem-"))
    return { ok: false, reason: "request-program-id-malformed" };
  if (!Array.isArray(req.grants)) return { ok: false, reason: "request-grants-not-a-list" };
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
  // a result may not claim to be about a different request or a different program
  if (res.request_id !== req.request_id) return { ok: false, reason: "result-request-mismatch" };
  if (res.program_sem_id !== req.program_sem_id) return { ok: false, reason: "result-program-mismatch" };
  return { ok: true };
}

/* ── the JS evaluator (implementation_id names THIS, not the program) ─────
   Reads go through a supplied reader interface, exactly as the World's scope
   queries do — the evaluator holds no world reference and cannot acquire one,
   because it is handed a function and a program and nothing else. */
export const JS_IMPLEMENTATION_ID = "impl-js-derive-v0.1.0";

export function evaluate(ast, reader, inputs = {}) {
  const exact = [], predicates = [], support = [];
  const ev = (n) => {
    if (n === null || typeof n !== "object" || typeof n.op !== "string")
      throw new Error("program-malformed-node");
    switch (n.op) {
      case "const": return OPS.const(n);
      case "input": {
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
  return {
    value,
    witness: { op: ast.op, reads: exact.length },
    support: [...new Set(support)].sort(),
    read_footprint: { exact, predicates },
  };
}

/* ── the authoritative side: request in, validated result out ─────────────
   The validator RE-DERIVES rather than trusting. That is what makes the
   boundary safe to move: on the far side of a realm the result is a claim, and
   a claim is only evidence once the authority has reproduced it. */
export function deriveLocally(registry, req, reader) {
  const rc = checkRequest(req);
  if (!rc.ok) return { ok: false, reason: rc.reason };
  const v = registry.verify(req.program_sem_id);
  if (!v.ok) return { ok: false, reason: v.reason };
  const ast = registry.get(req.program_sem_id);
  let out;
  try { out = evaluate(ast, reader, req.canonical_inputs); }
  catch (e) { return { ok: false, reason: "derivation-threw: " + e.message }; }
  const res = {
    request_id: req.request_id,
    program_sem_id: req.program_sem_id,
    value: out.value, witness: out.witness,
    support: out.support, read_footprint: out.read_footprint,
  };
  const rr = checkResult(res, req);
  if (!rr.ok) return { ok: false, reason: rr.reason };
  return { ok: true, result: res };
}

/** Validate a result produced ELSEWHERE by re-deriving it here. This is the
 *  operation a worker/process boundary turns into the whole trust story. */
export function validateForeignResult(registry, req, res, reader) {
  const rr = checkResult(res, req);
  if (!rr.ok) return { ok: false, reason: rr.reason };
  const mine = deriveLocally(registry, req, reader);
  if (!mine.ok) return { ok: false, reason: mine.reason };
  const a = canonicalBytes(mine.result), b = canonicalBytes(res);
  return a === b ? { ok: true } : { ok: false, reason: "foreign-result-divergence" };
}
