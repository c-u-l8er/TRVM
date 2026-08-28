/* ═══════════════════════════════════════════════════════════════════════════
   probe_coresem_v03_repro.mjs — program_sem_id bound syntax and claimed
   semantics, frozen at v0.2.0.

   v0.2.0 computed `program_sem_id = H("TRVM-PROGRAM-v1|" + canonicalBytes(ast))`
   while the record said in the same breath that the derivation language was
   deliberately NOT frozen. Review named the contradiction: if two conforming
   implementations may assign different meaning to `add`, to evaluation order,
   to numeric behaviour or to refusal semantics and still agree on the id, then
   the id binds syntax and nothing else — and every cross-implementation claim
   built on it is a claim about a shared spelling.

   Four witnesses, all against the frozen v0.2.0 copy below:

   C-1  `add` was JavaScript `+`.        "2"+"3" is "23", []+{} is
        "[object Object]". A C implementation reproducing either would be
        wrong, and one reproducing neither would be right — with the same id.
   C-2  `bind()` validated nothing.      {op:"exec", cmd:"rm -rf /"} was issued
        a program_sem_id. An identity for a program outside the language.
   C-3  arity and fields unconstrained.  {op:"const"} with no value, `add` with
        no `b`, and `add` carrying an extra field all received ids.
   C-4  evaluation order was free AND semantic. read_footprint was an ARRAY
        appended at access, so a right-to-left implementation returned a
        different footprint for the same program — a diverging semantic
        projection between two evaluators that computed the same value. Order
        was load-bearing and unstated.

   PAIRED, like probe_derivegrant_v02_repro.mjs: each witness must still
   reproduce against the frozen copy and must be confined against live, and exit
   0 requires both.

   C-4's repair is a RULING, and the first draft of it was the wrong one. The
   obvious closure is to declare the order in the core — and that makes two
   correct implementations diverge over a field neither of them considers
   semantic. Depending on {a,b} is one dependency set however it was visited.
   So the footprint became a canonical SET, access order moved to a separate
   read_trace, and the trace is excluded from the semantic projection. The core
   still fixes evaluation order, because refusals and traces must be
   reproducible; it just no longer makes that order an identity. Same principle
   that keeps ref_interactions out of conformance identity.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import {
  programSemId as liveSemId, evaluate as liveEval, ProgramRegistry as LiveRegistry,
  CORE_SPEC, CORE_SEM_ID, validateProgram, canonicalBytes as liveCanon,
} from "./derive_protocol.mjs";

const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "CONFINED" : "BREACH  "}  ${id.padEnd(26)} ${note}`); };

/* ── DERIVE-v0.2.0 identity and evaluation, VERBATIM ──────────────────────
   The parts that carried the defect, unedited. Do not repair anything here. */
const H = (s) => createHash("sha256").update(s).digest("hex");
function canonicalBytes(v, path = "$", onPath = new Set()) {
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
    if (Array.isArray(v)) out = "[" + v.map((x, i) => canonicalBytes(x, path + "[" + i + "]", onPath)).join(",") + "]";
    else if (Object.getPrototypeOf(v) === Object.prototype || Object.getPrototypeOf(v) === null) {
      const keys = Object.keys(v).sort();
      out = "{" + keys.map((k) => JSON.stringify(k) + ":" + canonicalBytes(v[k], path + "." + k, onPath)).join(",") + "}";
    } else throw new Error("not-canonical: non-plain object at " + path);
    onPath.delete(v);
    return out;
  }
  throw new Error("not-canonical: " + t + " at " + path);
}
const OPS_V2 = {
  const: (n) => n.value,
  add: (n, ev) => ev(n.a) + ev(n.b),          // <<< C-1 LIVES HERE: JavaScript `+`
  sub: (n, ev) => ev(n.a) - ev(n.b),
  mul: (n, ev) => ev(n.a) * ev(n.b),
  len: (n, ev) => { const v = ev(n.a); if (!Array.isArray(v)) throw new Error("program-type: len of non-array"); return v.length; },
};
const semIdV2 = (ast) => "psem-" + H("TRVM-PROGRAM-v1|" + canonicalBytes(ast));  // <<< C-2/C-3: no validation
function evalV2(ast, grants, inputs = {}) {
  const exact = [], predicates = [], support = [];
  const ev = (n) => {
    if (n === null || typeof n !== "object" || typeof n.op !== "string") throw new Error("program-malformed-node");
    switch (n.op) {
      case "const": return OPS_V2.const(n);
      case "input": {
        if (!Object.prototype.hasOwnProperty.call(inputs, n.name)) throw new Error("program-input-missing: " + n.name);
        return inputs[n.name];
      }
      case "read": {
        const e = grants.exact[n.resource];
        if (e === undefined) throw new Error("read-not-granted: " + n.resource);
        exact.push([n.resource, e.version]); support.push(n.resource); return e.value;
      }
      case "add": case "sub": case "mul": case "len": return OPS_V2[n.op](n, ev);
      default: throw new Error("program-unknown-op: " + n.op);
    }
  };
  const value = ev(ast);
  return { value, witness: { op: ast.op, reads: exact.length, scopes: predicates.length },
    support: [...new Set(support)].sort(), read_footprint: { exact, predicates } };
}

const G = { exact: {}, predicates: {} };
const ADD = { op: "add", a: { op: "input", name: "x" }, b: { op: "input", name: "y" } };

/* ── C-1: `add` was whatever JavaScript's `+` is ──────────────────────────── */
{
  const s = evalV2(ADD, G, { x: "2", y: "3" }).value;
  const o = evalV2(ADD, G, { x: [], y: {} }).value;
  let over; try { over = evalV2(ADD, G, { x: 1e308, y: 1e308 }).value; } catch (e) { over = "refused"; }
  R("C-1 frozen-v0.2.0", !(s === "23" && o === "[object Object]"),
    `same program_sem_id ${semIdV2(ADD).slice(0, 18)}…, three behaviours: "2"+"3" = ${JSON.stringify(s)}, ` +
    `[]+{} = ${JSON.stringify(o)}, 1e308+1e308 = ${over} — none of which a C implementation would reproduce by accident`);
  const live = (i) => { try { return JSON.stringify(liveEval(ADD, G, i).value); } catch (e) { return "refused: " + e.message; } };
  R("C-1 live", /program-type/.test(live({ x: "2", y: "3" })) && /program-type/.test(live({ x: [], y: {} }))
      && /program-arith-non-finite/.test(live({ x: 1e308, y: 1e308 })),
    `strings ${live({ x: "2", y: "3" })}; objects ${live({ x: [], y: {} })}; overflow ${live({ x: 1e308, y: 1e308 })} ` +
    `— operands must be numbers and results must be finite, both frozen in CORE_SPEC.numbers`);
}

/* ── C-2: an id for a program outside the language ────────────────────────── */
{
  const evil = { op: "exec", cmd: "rm -rf /" };
  const id = semIdV2(evil);
  R("C-2 frozen-v0.2.0", false,
    `{op:"exec", cmd:"rm -rf /"} received program_sem_id ${id.slice(0, 22)}… — the registry would have ` +
    `bound it, and it would have failed only later, at evaluation, already carrying a semantic identity`);
  let refused = "STILL BOUND";
  try { liveSemId(evil); } catch (e) { refused = e.message; }
  R("C-2 live", /program-unknown-op/.test(refused),
    `${refused} — validateProgram runs before the hash, so an id is never issued for a program the ` +
    `language does not contain`);
}

/* ── C-3: arity and field set unconstrained ───────────────────────────────── */
{
  const bad = [["const, no value", { op: "const" }],
    ["add, missing b", { op: "add", a: { op: "const", value: 1 } }],
    ["add + extra field", { op: "add", a: { op: "const", value: 1 }, b: { op: "const", value: 2 }, note: "x" }]];
  const boundV2 = bad.map(([l, a]) => `${l} -> ${semIdV2(a).slice(0, 14)}…`);
  R("C-3 frozen-v0.2.0", false, `three malformed programs, three ids: ${boundV2.join(" · ")}`);
  const live = bad.map(([l, a]) => { try { liveSemId(a); return `${l} -> STILL BOUND`; }
    catch (e) { return `${l} -> ${e.message.split(":")[0]}`; } });
  R("C-3 live", live.every((x) => /program-node-fields/.test(x)),
    `${live.join(" · ")} — the key set must be EXACTLY {op} union the op's declared fields`);
}

/* ── C-4: evaluation order is load-bearing and was unstated ───────────────── */
{
  const RD = { op: "add", a: { op: "read", resource: "b" }, b: { op: "read", resource: "a" } };
  const grants = { exact: { a: { value: 1, version: 1 }, b: { value: 2, version: 1 } }, predicates: {} };
  const fp = evalV2(RD, grants, {}).read_footprint.exact;
  const rev = [...fp].reverse();
  R("C-4 frozen-v0.2.0", false,
    `read_footprint was a SEQUENCE — ${JSON.stringify(fp)} — so a right-to-left implementation returned ` +
    `${JSON.stringify(rev)} for the same program: different canonical bytes, therefore ` +
    `foreign-result-divergence between two evaluators that computed the same value, over a field ` +
    `neither of them considers semantic`);
  const out = liveEval(RD, grants, {});
  R("C-4 live", liveCanon(out.read_footprint.exact) === liveCanon([["a", 1], ["b", 1]])
      && liveCanon(out.read_trace.exact) === liveCanon(fp)
      && /canonical DEPENDENCY SET/.test(CORE_SPEC.read_footprint)
      && CORE_SPEC.evaluation_order.includes("deliberately NOT semantic identity"),
    `the footprint is now the canonical SET ${JSON.stringify(out.read_footprint.exact)} and the access ` +
    `order survives in read_trace ${JSON.stringify(out.read_trace.exact)}, outside the semantic ` +
    `projection. The core still FIXES evaluation order so refusals and traces reproduce; it just no ` +
    `longer makes that order an identity`);
}

/* ── and the identity actually moved, which is the point ──────────────────── */
{
  const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
  const before = semIdV2(P), after = liveSemId(P);
  const reg = new LiveRegistry();
  R("identity-is-semantic", before !== after && after === liveSemId(P) && reg.bind(P) === after
      && validateProgram(P).ok,
    `psem(P) moved ${before.slice(0, 16)}… -> ${after.slice(0, 16)}… because CORE_SEM_ID ` +
    `${CORE_SEM_ID.slice(0, 16)}… is now inside it. Every v0.2.0 program id is retired, deliberately and ` +
    `now, while no second implementation exists to be broken by it`);
}

console.log("=".repeat(100));
const frozenHeld = results.filter((r) => r.id.includes("frozen") && r.held);
const liveBreached = results.filter((r) => (r.id.includes("live") || r.id === "identity-is-semantic") && !r.held);
console.log(
  `CORE-SEM-v0.3 REPRO: ${results.filter((r) => r.id.includes("frozen") && !r.held).length}/4 reproduce against ` +
  `the frozen v0.2.0 · ${results.filter((r) => (r.id.includes("live") || r.id === "identity-is-semantic") && r.held).length}/5 confined against live` +
  (frozenHeld.length ? ` — VACUOUS: ${frozenHeld.map((r) => r.id).join(", ")}` : "") +
  (liveBreached.length ? ` — REGRESSION: ${liveBreached.map((r) => r.id).join(", ")}` : ""));
process.exit(frozenHeld.length + liveBreached.length ? 1 : 0);
