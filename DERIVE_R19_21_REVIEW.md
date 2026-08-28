# Rounds 19 / 20 / 21 — the trace forgery, the clean baseline, and a gate that could not fail

**For:** review of TRVM rounds 19–21 (`TRVM/governance/`, branch `merge/governance-plane`)
**Built by:** Claude (Opus 5), session 2026-08-18
**Predecessor:** your trace-forgery finding and the four rulings on it
**Status:** three independent commits, each gated before the next began.

```
0e5ec7d  Restore a grid section the split lost …                    (round 21)
189768d  The gate could not fail                                    (round 21)
35184fb  A perturbation result needs a declared clean baseline      (round 20)
4cd8403  Outside the semantic projection had become unchecked       (round 19)
b475232  The apparatus is measured too                              (round 18)
242d319  Issuance authenticated the grant …                         (round 17)
583e742  The identity bound a spelling                              (round 16)
```

```
cd code
node derive_battery.mjs              # 40/40      node probe_traceforge_v06_repro.mjs  # 1/1 · 4/4
node derive_realm_battery.mjs        # 10/10      node probe_issuebind_v05_repro.mjs   # 3/3 · 4/4
node probe_coresem_v03_repro.mjs     # 4/4 · 5/5  node probe_stalegrant_v03_repro.mjs  # 5/5
```

`record/negative_battery.sh` and `record/harness_selftest.sh` need the full tree; their output is in
`gate/`. You noted last time that the bundle can't carry the whole tree — `record/Makefile.txt` is
included this time because round 21 is about the Makefile.

---

## 0. Your finding reproduced

```
honest trace   [["a",1],["b",1]]
forged trace   [["b",1],["a",1]]     footprint and value untouched
validateForeignResult: {"ok":true}
authority.accept     : {"ok":true,"validated":true,"fresh_at_check":true}
```

Frozen as T-1 in `code/probe_traceforge_v06_repro.mjs`.

Fixed with the separate envelope you preferred **and** the conformance check, because the envelope
alone would still have left the trace unchecked:

```
semantic_result      value · witness · support · read_footprint
execution_evidence   implementation_id · read_trace
```

`validateTraceConformance` compares the foreign trace against the authority's own re-derivation and
refuses `trace-nonconforming`. The two verdicts are reported separately —
`semantic_agreement: true, trace_conforms: false` — which is exactly the distinction you asked for.
The law's opening clause is now the sentence: **non-semantic does not mean unverified.**

---

## 1. Your four rulings

**`fresh_at_check` — kept, unchanged.** Nothing added, nothing strengthened.

**`read_trace` — separate envelope, plus the conformance rule.** As above. Answering your question
#2 back at you: the trace stays *in* `DeriveResult` rather than moving to a side channel, because it
is now checked there and the envelope makes its trust status structural rather than commentary.
That's the choice I'd want tested next.

**M-9 → `law:evidence.clean-baseline@1`**, promoted exactly as you framed it — **declared** baseline,
not silence — with your per-family table, your five phases, and the self-test still **bounded at
nine**. One addition of my own: the baseline is established once (every case builds its fixture by
the same recipe), and each case then proves its own pre-perturbation digest *equals the baselined
tree's*, failing `FIXTURE DRIFT` otherwise. Establishing a baseline once and assuming later trees
match it is the assumption the law exists to remove. The one-directional 9D probes are **declared
open**: their baselines are not established in code.

Round 17's ledger entry is **annotated, not rewritten**, in your words: not false-green, but not
isolated-cause evidence either.

**Fourth identity → `outcome_sem_id`.** Recorded with your four-layer chain, the refinement
obligation, and the point that refusal is also semantics. Declared, not built.

**A correction you should have first.** My round-16/17/18 brief said `TRVM-TERM-CANON-v1` was
*"recorded in `lowering_spike`"*. **It was not.** The combined round-16 draft carried that section;
splitting it into three rounds rebuilt the grid from the round-15 base and the section was never
re-added. The machine-readable extract in that same bundle shipped `"lowering_spike": null` — the
prose was wrong and the data was right, and neither of us noticed. It surfaced here through an
unrelated edit failing with `KeyError: 'lowering_spike'`. Restored now, in full, with your fourth
identity, locked by `grid_check` and given its own forgery — and recorded in the ledger as §99,
because the lesson is not "check the prose" but that shipping the machine-readable half of a claim
is worth doing precisely because it can contradict the sentence beside it. Anything you concluded
from that brief about `TRVM-TERM-CANON-v1` being on the record should be re-read against
`record/grid-sections.json` in THIS bundle.

---

## 2. Two findings of our own, and the second is bad

**Round 20's own edit inflated a counter.** The phase insertion matched in *both* runners, so the
engine case incremented `CASES` twice and the printed total read **101** where the case set was 100.
Caught only because the number moved when nothing about the case set had — which is what round 10's
repair to *derive* these totals rather than hand-type them was for.

**Round 21: the gate could not fail.** The round-19 envelope split missed one call site in
`derive_battery.mjs`. The battery **crashed** on it, and `make governance` reported green for rounds
19 *and* 20, because every governance recipe was

```make
@cd $(GOV) && $(NODE) derive_battery.mjs | tail -1
```

and `cmd | tail -1` takes **tail's** exit status. A crashing subject printed a stack trace's last
line where its verdict should have been. I found it assembling this bundle, by reading a line of
output — not by the gate, and not by the harness self-test, which does not cover the runner.

All thirteen recipe lines now capture output *and* status before printing. Verified in both
directions: an unresolvable import (crash) and a false assertion (exit 1) each fail the target.
`clean-baseline@1` gains this as its **runner half** — the baseline clause is about the fixture,
this is the same disease in the runner.

And the first crash test I wrote for it was **vacuous**: `throw` appended after `process.exit`,
which never runs, so it reported the gate as surviving a crash it never experienced.

---

## 3. What I'd ask this pass

1. **Should the harness self-test cover the runner?** It has nine species about fixtures, cases and
   probes, and none about the *invocation*. M-10 would be "a gate whose subject crashes must fail
   the target" — which is a tenth species with an actual history now. That breaks the bounded nine,
   and you were explicit about keeping it bounded. Which wins?
2. **Is `trace_conforms` in the acceptance result a mistake in the same family as `committable`?**
   `accept()` now returns `{validated, fresh_at_check, trace_conforms, implementation_id}`. Three of
   those are observations; I am no longer sure a caller should get a boolean per check rather than a
   single verdict plus a reason.
3. **Seven rounds, six apparatus defects.** 15 footprint · 16 identity · 17 issuance · 19 trace ·
   20 counter · 21 gate. The calculus has not moved in sixteen rounds. Is that ratio evidence that
   the apparatus is under-designed, or that this is simply what building an evidence system looks
   like from the inside? I genuinely cannot tell from here, and it bears on whether the next round
   should be more machinery or the lowering spike.
4. **The bundle problem you named.** You can rerun the standalone code but not the full tree. Is
   there a shape of bundle that would let you independently rerun `negative_battery.sh` — it needs
   `grid_check.mjs`, the grid, the receipts and the ledgers, roughly 30 files — or is the captured
   gate the right boundary?

---

## 4. Bundle contents

```
README.md                                  this file
code/                                      9 files, run standalone on Node ≥18
gate/                                      verbatim, incl. runs from OUTSIDE the repo, with exit codes
record/CORE_SPEC.json                      the frozen core + both envelopes
record/grid-sections.json                  10 laws + clean_baseline + lowering_spike + film_planes
record/artifacts-derivation-boundary.json  claimed / not_claimed / two_envelopes / issuance
record/negative_battery.sh                 the perturbation harness, with its baseline phase
record/harness_selftest.sh                 the apparatus gate, 9 species
record/Makefile.txt                        round 21's subject
record/rounds-19-21-ledger.md              §85–§100
record/commits.txt
MANIFEST.sha256
```

**Gate:** grid v1.22.0 — 63 entries / 346 citations · `derive_protocol.mjs` 0.6.0 · kernel PASS ·
World 0.12.0 PASS · `--check-receipt` PASS · negative battery **105/105** with a declared baseline ·
bridge 48/48 · derive **40/40 · 10/10** · probes **2/2+2/2 · 4/4+5/5 · 5/5 · 3/3+4/4 · 1/1+4/4** ·
harness **9/9**. `scheduler_certificate.json` byte-identical across all six commits — `cert_id`
unmoved, the calculus untouched for a sixteenth round.


---

# APPENDIX — every file inlined

## `code/derive_protocol.mjs`

```javascript
/* ═══════════════════════════════════════════════════════════════════════════
   derive_protocol.mjs — v0.6.0 — the serialized derivation boundary

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
export const PROTOCOL_VERSION = "0.6.0";

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
export const JS_IMPLEMENTATION_ID = "impl-js-derive-v0.6.0";

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
    grant_id: req.grant_id,
    semantic_result: {
      value: out.value, witness: out.witness,
      support: out.support, read_footprint: out.read_footprint,
    },
    execution_evidence: { implementation_id: implementationId, read_trace: out.read_trace },
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
  const fw = footprintWithinGrant(res.semantic_result.read_footprint, req.read_grants);
  if (!fw.ok) return { ok: false, reason: fw.reason };
  const impl = res.execution_evidence.implementation_id;
  if ("expected_implementation_id" in req && impl !== req.expected_implementation_id)
    return { ok: false, reason: "implementation-mismatch: want " + req.expected_implementation_id +
      ", result claims " + impl };
  // the local re-derivation is JS by definition, so the caller's requirement —
  // which may name a foreign executor — is dropped rather than applied to us
  const { expected_implementation_id: _requirement, ...localReq } = req;
  const mine = deriveLocally(registry, localReq);
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
  return { ok: true, semantic_agreement: true, trace_conforms: true, implementation_id: impl };
}

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

export function checkIntent(intent) {
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

/** THE AUTHORITY. It holds the World reader and the issuance table, it is the
 *  only constructor of a DeriveRequest, and acceptance is one of its methods so
 *  that neither proof can arrive as an argument. */
export class DerivationAuthority {
  #issued = new Map();
  #reader;
  constructor(reader) {
    if (!reader || typeof reader.read !== "function" || typeof reader.scope !== "function")
      throw new Error("authority-requires-a-world-reader");
    this.#reader = reader;
    Object.freeze(this);
  }

  /** intent in — authority-issued, owned, frozen request out */
  authorize(intent, options = {}) {
    const c = checkIntent(intent);
    if (!c.ok) return { ok: false, reason: c.reason };
    const unknown = Object.keys(options).filter((k) => !AUTHORIZE_OPTIONS.includes(k)).sort();
    if (unknown.length)
      return { ok: false, reason: "authorize-options-unknown: [" + unknown.join(",") + "]" };
    if ("expected_implementation_id" in options && typeof options.expected_implementation_id !== "string")
      return { ok: false, reason: "authorize-expected-implementation-malformed" };
    let g;
    try { g = resolveGrants(this.#reader, intent.requested_resources); }
    catch (e) { return { ok: false, reason: e.message }; }
    const body = {
      program_sem_id: intent.program_sem_id,
      canonical_inputs: intent.canonical_inputs,
      read_grants: g.read_grants,
      grant_id: g.grant_id,
      ...("expected_implementation_id" in options
        ? { expected_implementation_id: options.expected_implementation_id } : {}),
    };
    const request_id = "req-" + H("TRVM-REQUEST-v1|" + intent.intent_id + "|" + canonicalBytes(body));
    // owned and severed through canonicalBytes — the same rule the World uses,
    // not a second clone algorithm — then deep-frozen
    const req = deepFreeze(JSON.parse(canonicalBytes({ request_id, ...body })));
    const rc = checkRequest(req);
    if (!rc.ok) return { ok: false, reason: rc.reason };
    this.#issued.set(request_id, requestSemId(req));
    return { ok: true, request: req };
  }

  /** Was THIS request — every field of it — issued by THIS authority? */
  wasIssued(req) {
    const stored = this.#issued.get(req?.request_id);
    if (stored === undefined) return { ok: false, reason: "grant-not-issued-by-this-authority" };
    let mine;
    try { mine = requestSemId(req); }
    catch (e) { return { ok: false, reason: "request-not-canonical: " + e.message }; }
    return stored === mine ? { ok: true } : { ok: false, reason: "request-not-as-issued" };
  }

  /** ACCEPTANCE — everything a result must clear before an authority may act on
   *  it, in one call, in an order where each stage fails on its own evidence:
   *
   *    1. issuance   this request, whole, is one THIS authority issued
   *    2. validation schema, footprint-within-grant, re-derivation
   *    3. freshness  the footprint's dependencies are still live NOW
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
  accept(registry, req, res) {
    const iss = this.wasIssued(req);
    if (!iss.ok) return { ok: false, reason: iss.reason };
    const v = validateForeignResult(registry, req, res);
    if (!v.ok) return v;
    const f = validateFootprintFresh(this.#reader, res.semantic_result.read_footprint);
    if (!f.ok) return { ok: false, reason: f.reason };
    return { ok: true, validated: true, fresh_at_check: true, trace_conforms: v.trace_conforms,
      implementation_id: res.execution_evidence.implementation_id };
  }
}
Object.freeze(DerivationAuthority.prototype);
```

## `code/derive_worker.mjs`

```javascript
/* derive_worker.mjs — v0.6.0 — the far side of the realm boundary.
   Holds NO parent reference of any kind: it receives canonical data on a
   message port, resolves the program from its OWN registry by id, evaluates
   against the grant snapshot the request carries, and posts back canonical
   data. It cannot read the World — and does not need to, because resolving
   reads is an AUTHORITY operation performed by the parent before the request
   is sent, while computation is not. That split is what makes the worker's
   capability set empty: it holds none because it needs none.

   Two things this file must NOT do, each of which it did at v0.1.0:

   1. It must not source its read table from `canonical_inputs`. The language
      has `{op:"input", name:…}`, so anything reachable as an input is
      reachable WITHOUT a tracked read — which made the read footprint
      bypassable and the round-14 claim about it false. Reads now come from
      `read_grants`, a separate request field the `input` op cannot address,
      and the evaluator builds its own reader from it.
   2. It must not echo the caller's implementation_id. The executor ASSERTS
      its identity; the caller may only state a REQUIREMENT, which this worker
      refuses when it cannot satisfy it. A field the caller sets and nobody
      checks is decoration, and the film identity split needs provenance.

   Scope, unchanged and still not claimed: this is object confinement. A worker
   holding `let counter = 0` leaks no parent authority and still fails to make
   program_sem_id denote a stable function, and Date.now, Math.random, the
   filesystem and the network remain reachable from here. */
import { parentPort, workerData } from "node:worker_threads";
import { ProgramRegistry, evaluate, checkRequest, JS_IMPLEMENTATION_ID } from "./derive_protocol.mjs";

const reg = new ProgramRegistry();
for (const ast of workerData.programs) reg.bind(ast);   // resolved HERE, from data

parentPort.on("message", (req) => {
  const c = checkRequest(req);
  if (!c.ok) { parentPort.postMessage({ ok: false, reason: c.reason }); return; }
  // the caller's expectation is a requirement on the EXECUTOR, and this
  // executor is the only thing that knows what it is
  if ("expected_implementation_id" in req && req.expected_implementation_id !== JS_IMPLEMENTATION_ID) {
    parentPort.postMessage({ ok: false, reason: "implementation-mismatch: want " +
      req.expected_implementation_id + ", this is " + JS_IMPLEMENTATION_ID });
    return;
  }
  const v = reg.verify(req.program_sem_id);
  if (!v.ok) { parentPort.postMessage({ ok: false, reason: v.reason }); return; }
  const ast = reg.get(req.program_sem_id);
  try {
    // reads come from the grant snapshot and nowhere else; the evaluator is
    // handed canonical data rather than a reader callable
    const out = evaluate(ast, req.read_grants, req.canonical_inputs);
    parentPort.postMessage({ ok: true, result: {
      request_id: req.request_id, program_sem_id: req.program_sem_id, grant_id: req.grant_id,
      semantic_result: { value: out.value, witness: out.witness,
        support: out.support, read_footprint: out.read_footprint },
      execution_evidence: { implementation_id: JS_IMPLEMENTATION_ID, read_trace: out.read_trace } } });
  } catch (e) { parentPort.postMessage({ ok: false, reason: "derivation-threw: " + e.message }); }
});
```

## `code/derive_battery.mjs`

```javascript
/* derive_battery.mjs — falsifiers for the serialized derivation boundary, v0.4.0.
   Written before the protocol is believed, per the house rule. Every case that
   must be refused asserts the EXACT refusal string, so a repair that changes
   what is refused cannot pass by refusing for a different reason.
   Run: node derive_battery.mjs   (exit 0 iff green) */
import {
  ProgramRegistry, programSemId, canonicalBytes, checkRequest, checkResult,
  deriveLocally, validateForeignResult, evaluate, resolveGrants, grantId,
  footprintWithinGrant, semanticProjection, JS_IMPLEMENTATION_ID,
  CORE_SPEC, CORE_SEM_ID, validateProgram, SEMANTIC_RESULT_FIELDS, EXECUTION_ENVELOPE_FIELDS,
  validateTraceConformance,
  validateFootprintFresh, DerivationAuthority, checkIntent, requestSemId,
} from "./derive_protocol.mjs";
import { createHash } from "node:crypto";

// forgeries must now reach INSIDE the envelope they are forging, which is
// itself the round's point: the shape says which trust status a field carries
const withSem = (r, o) => ({ ...r, semantic_result: { ...r.semantic_result, ...o } });
const withExec = (r, o) => ({ ...r, execution_evidence: { ...r.execution_evidence, ...o } });

const rows = [];
let fail = false;
const R = (id, ok, note) => { if (!ok) fail = true; rows.push({ id, ok, note });
  console.log(`${ok ? "PASS" : "FAIL"}  ${id.padEnd(34)} ${note}`); };

// a tiny deterministic program: (read fb) + input(bias)
const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const reg = new ProgramRegistry();
const PID = reg.bind(P);

// the World-side reader the AUTHORITY uses to resolve a snapshot. It never
// crosses the boundary; it is used once, here, on the authoritative side.
const worldReader = (vals) => ({
  read: (r) => ({ value: vals[r], version: 1 }),
  scope: (q) => "scope:" + q,
});
const snapshot = (vals, want = { exact: Object.keys(vals) }) =>
  resolveGrants(worldReader(vals), want);

const mkReq = (over = {}) => {
  const { read_grants, grant_id } = snapshot({ fb: 5 });
  return { request_id: "req-1", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, read_grants, grant_id, ...over };
};

// ── 1. the id is the program, so a caller cannot choose it ────────────────
{
  const other = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "const", value: 1000 } };
  const otherId = programSemId(other);
  R("program-id-is-content", PID !== otherId && PID === programSemId(P),
    `two programs, two ids (${PID.slice(0, 14)}… vs ${otherId.slice(0, 14)}…); recomputing P's id reproduces it`);
  // the 9D.4 shape: claim an honest program id while meaning a different program
  const reg2 = new ProgramRegistry();
  reg2.bind(other);
  const r = deriveLocally(reg2, mkReq());
  R("label-substitution-refused", !r.ok && r.reason === "program-unknown",
    `a request naming P against a registry holding only the evil program is refused: ${r.reason} ` +
    `— an id cannot be pointed at different code, because the id IS the code's hash`);
}

// ── 2. the boundary is the canonical domain, not "structuredClone worked" ─
{
  const cases = [
    ["Function", () => {}], ["Map", new Map([["a", 1]])], ["Set", new Set([1])],
    ["Date", new Date(0)], ["class instance", new (class Cap {})()],
  ];
  const results = cases.map(([name, v]) => {
    const c = checkRequest(mkReq({ canonical_inputs: { bias: 0, sneak: v } }));
    return [name, !c.ok && /not-canonical/.test(c.reason), c.reason];
  });
  R("capabilities-refused-at-boundary", results.every((x) => x[1]),
    results.map(([n, ok]) => `${n}:${ok ? "refused" : "ADMITTED"}`).join(" ") +
    ` — structuredClone would have accepted Map, Set and Date; the canonical domain does not`);
  // and the schema itself is closed in both directions
  const extra = checkRequest({ ...mkReq(), extra_capability: 1 });
  const missing = checkRequest({ request_id: "r", program_sem_id: PID });
  R("request-schema-closed", !extra.ok && /unknown \[extra_capability\]/.test(extra.reason)
      && !missing.ok && /missing \[/.test(missing.reason),
    `an unknown field is refused (${extra.reason}) and a short request names what it lacks ` +
    `(${missing.reason.slice(0, 62)}…)`);
}

// ── 3. an honest derivation, and its footprint ───────────────────────────
{
  const r = deriveLocally(reg, mkReq());
  const r2 = deriveLocally(reg, mkReq({ canonical_inputs: { bias: 1000 } }));
  R("derivation-honest", r.ok && r.result.semantic_result.value === 5 && r2.ok && r2.result.semantic_result.value === 1005,
    `bias 0 -> ${r.ok && r.result.semantic_result.value}, bias 1000 -> ${r2.ok && r2.result.semantic_result.value}; the bias is an ` +
    `INPUT of the request, so it is visible in canonical_inputs instead of hiding in a lexical cell`);
  R("footprint-recorded", r.ok && canonicalBytes(r.result.semantic_result.read_footprint.exact) === canonicalBytes([["fb", 1]])
      && r.result.semantic_result.witness.reads === 1,
    `read_footprint.exact = ${JSON.stringify(r.ok && r.result.semantic_result.read_footprint.exact)} — reads are tracked ` +
    `by the evaluator on access, not declared by the caller`);
}

// ── 4. the 9D.4 witness has nowhere to live ──────────────────────────────
// The whole attack was a shared lexical cell mutated between derivations. A
// program is data and the evaluator is handed canonical grants and inputs;
// there is no captured environment to mutate, and two derivations of the same
// request must agree.
{
  const req = mkReq();
  const a = deriveLocally(reg, req);
  const b = deriveLocally(reg, req);
  R("no-ambient-cell", a.ok && b.ok && canonicalBytes(a.result) === canonicalBytes(b.result),
    `the same request derives identically twice; there is no environment between them to mutate ` +
    `(law:derivation.environment-confinement@1 is FALSIFIED for the closure API and this is the replacement path)`);
  // v0.2.0: the reader is no longer a caller-supplied callable either
  let readerRefusal = "IT WAS ACCEPTED";
  try { evaluate(P, { read: () => ({ value: 9, version: 1 }), scope: () => "s" }, { bias: 0 }); }
  catch (e) { readerRefusal = e.message; }
  R("reader-is-not-a-callable", readerRefusal === "grants-schema: [read,scope]",
    `evaluate(ast, read_grants, inputs) builds its own reader from canonical grant data. A pair of ` +
    `reader CALLABLES in the grant position is refused as data (${readerRefusal}) — v0.1.0 took the ` +
    `reader as a parameter, which was the closure-authority shape in miniature`);
}

// ── 5. THE GRANT AND THE FOOTPRINT ARE TWO RECORDS (the v0.1.0 defect) ───
{
  // W-1: a program that addresses the grant table as an input gets inputs only
  const exfil = { op: "input", name: "__reads" };
  const reg3 = new ProgramRegistry(); const XID = reg3.bind(exfil);
  const { read_grants, grant_id } = snapshot({ "secret:key": 42 });
  const r = deriveLocally(reg3, { request_id: "x", program_sem_id: XID,
    canonical_inputs: { __reads: "an ordinary input" }, read_grants, grant_id });
  R("grant-not-reachable-as-input", r.ok && r.result.semantic_result.value === "an ordinary input"
      && r.result.semantic_result.read_footprint.exact.length === 0,
    `{op:"input",name:"__reads"} returns ${JSON.stringify(r.ok && r.result.semantic_result.value)} — at v0.1.0 it ` +
    `returned the entire authority grant table with witness.reads = 0. read_grants is a separate ` +
    `request field and the input op cannot address it (W-1, frozen in probe_derivegrant_v02_repro.mjs)`);

  // the grant may be WIDER than the footprint, and that is the point: freshness
  // keys on what was read, not on what was made available
  const wide = snapshot({ fb: 5, unused_a: 1, unused_b: 2 });
  const r2 = deriveLocally(reg, { request_id: "w", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, read_grants: wide.read_grants, grant_id: wide.grant_id });
  R("footprint-is-the-access-subset",
    r2.ok && Object.keys(wide.read_grants.exact).length === 3 && r2.result.semantic_result.read_footprint.exact.length === 1,
    `grant covers ${Object.keys(wide.read_grants.exact).sort().join(",")} (3 resources); the footprint ` +
    `records ${JSON.stringify(r2.result.semantic_result.read_footprint.exact)} (1). Defining the footprint AS the grant ` +
    `would invalidate this derivation whenever unused_a moved, which it does not depend on`);

  // grant_id binds the snapshot: naming one grant while carrying another fails
  const tampered = { exact: { fb: { value: 1005, version: 1 } }, predicates: {} };
  const c = checkRequest({ ...mkReq(), read_grants: tampered });
  R("grant-id-binds-the-snapshot", !c.ok && c.reason === "request-grant-id-mismatch",
    `a request carrying a swapped snapshot under the original grant_id is refused: ${c.reason} ` +
    `— the id is H(canonical read_grants), so the snapshot cannot be edited in flight`);
}

// ── 6. the authority validates the footprint on its OWN evidence ─────────
{
  const req = mkReq();
  const honest = deriveLocally(reg, req).result;
  // over-claiming: a footprint naming a resource the authority never granted
  const overclaim = validateForeignResult(reg, req, {
    ...honest,
    semantic_result: { ...honest.semantic_result,
      witness: { ...honest.semantic_result.witness, reads: 2 },
      read_footprint: { exact: [["fb", 1], ["secret:key", 1]], predicates: [] } },
    execution_evidence: { ...honest.execution_evidence,
      read_trace: { exact: [["fb", 1], ["secret:key", 1]], predicates: [] } } });
  // version forgery: the right resource at a version the grant does not carry
  const wrongVer = validateForeignResult(reg, req, {
    ...honest,
    semantic_result: { ...honest.semantic_result, read_footprint: { exact: [["fb", 99]], predicates: [] } },
    execution_evidence: { ...honest.execution_evidence, read_trace: { exact: [["fb", 99]], predicates: [] } } });
  // and the subset check is INDEPENDENT of re-derivation: it fires here even
  // though the value is honest and would have re-derived equal
  const direct = footprintWithinGrant({ exact: [["nope", 1]], predicates: [] }, req.read_grants);
  R("footprint-validated-independently",
    !overclaim.ok && overclaim.reason === "footprint-ungranted-read: secret:key"
      && !wrongVer.ok && wrongVer.reason === "footprint-version-mismatch: fb"
      && !direct.ok && direct.reason === "footprint-ungranted-read: nope",
    `over-claimed read -> ${overclaim.reason}; forged version -> ${wrongVer.reason}. Both refused ` +
    `against the SNAPSHOT rather than against the executor's word, before any re-derivation`);
  // the witness may not disagree with the footprint it accompanies
  const inconsistent = checkResult(withSem(honest, { witness: { op: "add", reads: 7, scopes: 0 } }), req);
  R("witness-matches-footprint", !inconsistent.ok && inconsistent.reason === "result-witness-inconsistent",
    `a result claiming 7 reads with a 1-entry footprint is refused: ${inconsistent.reason}`);
}

// ── 7. a foreign result is a CLAIM until the authority re-derives it ─────
{
  const req = mkReq();
  const honest = deriveLocally(reg, req).result;
  const good = validateForeignResult(reg, req, honest);
  const lied = validateForeignResult(reg, req, withSem(honest, { value: 1005 }));
  const wrongReq = validateForeignResult(reg, req, { ...honest, request_id: "req-2" });
  const wrongProg = validateForeignResult(reg, req, { ...honest, program_sem_id: programSemId({ op: "const", value: 1 }) });
  const wrongGrant = validateForeignResult(reg, req, { ...honest, grant_id: grantId({ exact: {}, predicates: {} }) });
  R("foreign-result-revalidated",
    good.ok && !lied.ok && lied.reason === "foreign-result-divergence"
      && !wrongReq.ok && wrongReq.reason === "result-request-mismatch"
      && !wrongProg.ok && wrongProg.reason === "result-program-mismatch"
      && !wrongGrant.ok && wrongGrant.reason === "result-grant-mismatch",
    `honest accepted; inflated value -> ${lied.reason}; re-labelled request -> ${wrongReq.reason}; ` +
    `re-labelled program -> ${wrongProg.reason}; re-labelled grant -> ${wrongGrant.reason}. Across a ` +
    `realm this is the entire trust story: the far side produces a claim, the authority reproduces it`);
}

// ── 8. implementation_id is the EXECUTOR's assertion, not the caller's ───
{
  const req = mkReq();
  const honest = deriveLocally(reg, req).result;
  R("implementation-id-asserted", honest.execution_evidence.implementation_id === JS_IMPLEMENTATION_ID,
    `the result carries ${honest.execution_evidence.implementation_id}, emitted by the evaluator that ran. At v0.1.0 the ` +
    `REQUEST carried implementation_id, nothing checked it and the result carried none (W-2)`);
  const demand = deriveLocally(reg, { ...req, expected_implementation_id: "impl-c-pretend-v9" });
  R("implementation-requirement-refused", !demand.ok
      && demand.reason === "implementation-mismatch: want impl-c-pretend-v9, this is " + JS_IMPLEMENTATION_ID,
    `a request demanding a C executor is refused BY the JS executor (${demand.reason}) — the caller's ` +
    `field states a requirement and the executor answers it, so impersonation has no path`);
  const malformed = checkResult(withExec(honest, { implementation_id: "js" }), req);
  R("implementation-id-well-formed", !malformed.ok && malformed.reason === "result-implementation-id-malformed",
    `a result whose implementation_id is not an impl- identity is refused: ${malformed.reason}`);

  // THE POINT OF THE SPLIT: a conforming foreign implementation validates, and
  // its provenance is reported rather than compared away. Comparing whole
  // results would make cross-implementation validation fail by construction.
  const asIfC = withExec(honest, { implementation_id: "impl-c-derive-v0.6.0" });
  const v = validateForeignResult(reg, req, asIfC);
  const sameSemantics = canonicalBytes(semanticProjection(asIfC)) === canonicalBytes(semanticProjection(honest));
  R("semantic-projection-is-portable", v.ok && v.implementation_id === "impl-c-derive-v0.6.0" && sameSemantics,
    `a result identical in semantics but produced by impl-c-derive-v0.2.0 validates, and the authority ` +
    `records WHO ran it (${v.implementation_id}). program_sem_id is equal across implementations; ` +
    `implementation_id is outside the semantic projection, which is what makes a portable film possible`);
  // and the requirement is enforced against the foreign claim too
  const mismatched = validateForeignResult(reg, { ...req, expected_implementation_id: JS_IMPLEMENTATION_ID }, asIfC);
  R("implementation-requirement-checked-on-result", !mismatched.ok && /implementation-mismatch: want/.test(mismatched.reason),
    `a result from a different executor than the one required is refused: ${mismatched.reason}`);
}

// ── 9. the registry cannot be made to lie ────────────────────────────────
{
  const v = reg.verify(PID);
  const unknown = reg.verify("psem-" + "0".repeat(64));
  R("registry-binding-verified", v.ok && !unknown.ok && unknown.reason === "program-unknown",
    `verify(PID) recomputes the hash and agrees; an unbound id is refused (${unknown.reason})`);
  const stored = reg.get(PID);
  let frozen = false;
  try { stored.op = "mul"; } catch { frozen = true; }
  R("registry-entry-frozen", frozen && reg.get(PID).op === "add",
    `the stored program is deep-frozen; mutating it throws and the registry still reads 'add'`);
}

// ── 10. TRVM-DERIVE-CORE-v1: the id commits SEMANTICS, not just syntax ──
{
  R("core-id-is-content-bound", CORE_SEM_ID === "core-" + createHash("sha256")
      .update("TRVM-DERIVE-CORE-SPEC-v1|" + canonicalBytes(CORE_SPEC)).digest("hex")
      && Object.isFrozen(CORE_SPEC),
    `CORE_SEM_ID recomputes from the frozen CORE_SPEC (${CORE_SEM_ID.slice(0, 20)}…). A bare label ` +
    `"TRVM-DERIVE-CORE-v1" would be the caller-selected-name defect the primitive ruling already refuses`);
  R("program-id-commits-the-core", programSemId(P) === "psem-" + createHash("sha256")
      .update("TRVM-PROGRAM-v2|" + CORE_SEM_ID + "|" + canonicalBytes(P)).digest("hex"),
    `program_sem_id = H("TRVM-PROGRAM-v2|" + core_sem_id + "|" + canonicalBytes(ast)) — change what ` +
    `add means and the core moves and every program id moves with it, which is what makes the id semantic`);
  // the grammar refuses out-of-language programs BEFORE issuing an identity
  const malformed = [
    ["unknown op", { op: "exec", cmd: "rm -rf /" }, /program-unknown-op/],
    ["missing field", { op: "const" }, /program-node-fields/],
    ["extra field", { op: "add", a: { op: "const", value: 1 }, b: { op: "const", value: 2 }, x: 1 }, /program-node-fields/],
    ["non-string name", { op: "input", name: 7 }, /program-node-fields|program-name-not-a-string/],
    ["bad child", { op: "add", a: { op: "const", value: 1 }, b: { op: "nope" } }, /program-unknown-op/],
    ["non-canonical const", { op: "const", value: new Map() }, /program-const-not-canonical/],
  ];
  const got = malformed.map(([l, ast, rx]) => {
    const v = validateProgram(ast);
    let threw = "ISSUED AN ID";
    try { programSemId(ast); } catch (e) { threw = e.message; }
    return [l, !v.ok && rx.test(v.reason) && rx.test(threw)];
  });
  R("grammar-refuses-before-id", got.every((x) => x[1]),
    got.map(([l, ok]) => `${l}:${ok ? "refused" : "ADMITTED"}`).join(" ") +
    ` — v0.2.0 issued a program_sem_id to {op:"exec", cmd:"rm -rf /"}, which failed only later at ` +
    `evaluation, having already been given a semantic identity`);
  // arithmetic is typed and total: no coercion, no non-finite result
  const A = { op: "add", a: { op: "input", name: "x" }, b: { op: "input", name: "y" } };
  const ev = (i) => { try { return "=" + JSON.stringify(evaluate(A, { exact: {}, predicates: {} }, i).value); }
    catch (e) { return e.message; } };
  R("arithmetic-typed-and-total",
    ev({ x: 2, y: 3 }) === "=5" && /program-type: add of non-number/.test(ev({ x: "2", y: "3" }))
      && /program-type: add of non-number/.test(ev({ x: [], y: {} }))
      && /program-arith-non-finite: add/.test(ev({ x: 1e308, y: 1e308 })),
    `2+3 ${ev({ x: 2, y: 3 })} · "2"+"3" ${ev({ x: "2", y: "3" })} · []+{} ${ev({ x: [], y: {} })} · ` +
    `1e308+1e308 ${ev({ x: 1e308, y: 1e308 })}. v0.2.0's add was JavaScript's + and produced "23" and ` +
    `"[object Object]" under the same program_sem_id`);
}


// ── 11. the footprint is a SET; the trace keeps order ────────────────────
{
  // b is visited first and twice; a once. Three accesses, two dependencies.
  const RD = { op: "add", a: { op: "read", resource: "b" },
    b: { op: "add", a: { op: "read", resource: "a" }, b: { op: "read", resource: "b" } } };
  const g = { exact: { a: { value: 1, version: 1 }, b: { value: 2, version: 1 } }, predicates: {} };
  const out = evaluate(RD, g, {});
  R("footprint-is-a-canonical-set",
    canonicalBytes(out.read_footprint.exact) === canonicalBytes([["a", 1], ["b", 1]])
      && canonicalBytes(out.read_trace.exact) === canonicalBytes([["b", 1], ["a", 1], ["b", 1]])
      && out.witness.reads === 2,
    `three accesses in order ${JSON.stringify(out.read_trace.exact)} produce the dependency set ` +
    `${JSON.stringify(out.read_footprint.exact)}. Depending on {a,b} is ONE dependency set however it ` +
    `was visited — declaring the order semantic would make two correct implementations diverge over a ` +
    `field neither of them considers semantic`);
  R("trace-is-outside-the-semantic-projection",
    !SEMANTIC_RESULT_FIELDS.includes("execution_evidence")
      && SEMANTIC_RESULT_FIELDS.includes("semantic_result")
      && canonicalBytes(EXECUTION_ENVELOPE_FIELDS) === canonicalBytes(["implementation_id", "read_trace"]),
    `semantic projection = [${SEMANTIC_RESULT_FIELDS.join(", ")}]; execution evidence = ` +
    `[${EXECUTION_ENVELOPE_FIELDS.join(", ")}]. Excluded from the comparison and NOT excluded from ` +
    `checking — non-semantic does not mean unverified, which is what v0.5.0 got wrong`);
  // a result carrying a sequence where the set is required is REFUSED, not normalized
  const req = mkReq();
  const honest = deriveLocally(reg, req).result;
  const resequenced = withSem(honest, { read_footprint: { exact: [["fb", 1], ["fb", 1]], predicates: [] } });
  const c = checkResult(resequenced, req);
  R("footprint-set-is-checked-not-normalized",
    !c.ok && c.reason === "result-footprint-not-canonical-set: exact",
    `${c.reason} — normalizing on receipt would let two implementations commit to different bytes and ` +
    `still be told they agreed`);
}

// ── 12. the arithmetic edge matrix, all three operators ──────────────────
{
  const g = { exact: {}, predicates: {} };
  const bin = (op) => ({ op, a: { op: "input", name: "x" }, b: { op: "input", name: "y" } });
  const run = (op, i) => { try { return "=" + JSON.stringify(evaluate(bin(op), g, i).value); }
    catch (e) { return e.message; } };
  const overflow = [["add", { x: 1e308, y: 1e308 }], ["sub", { x: -1e308, y: 1e308 }], ["mul", { x: 1e308, y: 2 }]];
  const typed = [["add", { x: "2", y: "3" }], ["sub", { x: [], y: 1 }], ["mul", { x: 1, y: {} }]];
  R("overflow-refused-on-every-operator",
    overflow.every(([op, i]) => run(op, i) === "program-arith-non-finite: " + op),
    overflow.map(([op, i]) => `${op}:${run(op, i)}`).join(" · ") +
    ` — one refusal string, three separately frozen semantic surfaces, each witnessed`);
  R("coercion-refused-on-every-operator",
    typed.every(([op, i]) => run(op, i) === "program-type: " + op + " of non-number"),
    typed.map(([op, i]) => `${op}:${run(op, i)}`).join(" · "));
  // signed zero: the canonical quotient identifies -0 with +0, and says so
  const negZero = evaluate(bin("mul"), g, { x: -1, y: 0 }).value;
  R("signed-zero-identified", Object.is(negZero, -0) && canonicalBytes(negZero) === "0"
      && canonicalBytes(-0) === canonicalBytes(0) && /IDENTIFIES -0 with \+0/.test(CORE_SPEC.signed_zero),
    `mul(-1, 0) evaluates to ${Object.is(negZero, -0) ? "-0" : "+0"} and canonicalizes to ` +
    `${canonicalBytes(negZero)} — the canonical numeric quotient identifies them, which was already ` +
    `true of the domain and unstated. A C implementation would otherwise have decided it by accident`);
}


// ── 13. freshness is a DIFFERENT question from containment ──────────────
{
  const live = { res: { fb: { value: 5, version: 1 }, other: { value: 0, version: 1 } },
    read(r) { return { ...this.res[r] }; }, scope(q) { return "scope:" + q; } };
  const auth = new DerivationAuthority(live);
  const { request: req } = auth.authorize({ intent_id: "f1", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const res = deriveLocally(reg, req).result;
  const before = auth.accept(reg, req, res);
  live.res.fb = { value: 9, version: 2 };                 // the World moves
  const containment = footprintWithinGrant(res.semantic_result.read_footprint, req.read_grants);
  const rederive = validateForeignResult(reg, req, res);
  const after = auth.accept(reg, req, res);
  R("freshness-is-not-containment",
    before.ok && containment.ok && rederive.ok
      && !after.ok && after.reason === "stale-read: fb granted@1 live@2",
    `after fb moves 1→2: footprintWithinGrant ${containment.ok ? "PASS" : containment.reason}, ` +
    `re-derivation ${rederive.ok ? "PASS" : rederive.reason} — both CORRECT about the snapshot — and ` +
    `acceptance ${after.reason}. Containment is historical, freshness is temporal, and a protocol that ` +
    `stops at re-derivation commits a value the World has already contradicted`);
  live.res.fb = { value: 5, version: 1 };
  live.res.other = { value: 999, version: 2 };            // a write nothing read
  const unrelated = auth.accept(reg, req, res);
  R("unrelated-write-does-not-invalidate", unrelated.ok && unrelated.fresh_at_check === true,
    `other@1→2 moved and acceptance still passes — freshness keys on the FOOTPRINT, never on a global ` +
    `vclock. A vclock rule would invalidate every derivation on every unrelated write, undoing the ` +
    `grant/footprint separation from the other side`);
  R("acceptance-does-not-claim-committable",
    unrelated.committable === undefined && unrelated.validated === true && unrelated.fresh_at_check === true,
    `accept() returns {validated, fresh_at_check} and NOT committable. One call cannot make a result ` +
    `committable: the World can move between this returning and the caller applying. The composition ` +
    `that commits belongs to the World — lock, accept, prepared apply, receipt, unlock — and no lock ` +
    `capability is exported to reach it`);
}

// ── 14. issuance binds the WHOLE request, and cannot be handed to a caller ─
{
  const live = { res: { fb: { value: 5, version: 1 } }, read(r) { return { ...this.res[r] }; },
    scope(q) { return "scope:" + q; } };
  const auth = new DerivationAuthority(live);
  const intent = { intent_id: "i1", program_sem_id: PID, canonical_inputs: { bias: 0 },
    requested_resources: { exact: ["fb"], predicates: [] } };
  const a = auth.authorize(intent);
  const res = deriveLocally(reg, a.request).result;
  const mine = auth.accept(reg, a.request, res);
  const theirs = new DerivationAuthority(live).accept(reg, a.request, res);
  // the defect: same request_id, same grant_id, different inputs
  const swapped = { ...a.request, canonical_inputs: { bias: 1000 } };
  const swappedRes = deriveLocally(reg, swapped).result;
  const swapAcc = auth.accept(reg, swapped, swappedRes);
  R("issuance-binds-the-whole-request",
    a.ok && mine.ok && !theirs.ok && theirs.reason === "grant-not-issued-by-this-authority"
      && swappedRes.semantic_result.value === 1005 && !swapAcc.ok && swapAcc.reason === "request-not-as-issued",
    `the issuing authority accepts; a different instance refuses (${theirs.reason}); and an input swap ` +
    `under an UNTOUCHED request_id and grant_id — which derives to ${swappedRes.semantic_result.value} — is refused ` +
    `(${swapAcc.reason}). The draft bound request_id → grant_id and answered "was this issued?" about a ` +
    `GRANT while the thing being accepted was a REQUEST`);
  R("request-sem-id-recomputes",
    requestSemId(a.request) === requestSemId(JSON.parse(canonicalBytes(a.request)))
      && requestSemId(a.request) !== requestSemId(swapped),
    `request_sem_id = H(canonical request) recomputes over an owned copy and differs for the swapped ` +
    `request — which is the whole mechanism`);
  const bagged = auth.authorize(intent, { canonical_inputs: { bias: 1000 } });
  const impl = auth.authorize({ ...intent, intent_id: "i2" }, { expected_implementation_id: "impl-c-derive-v0.5.0" });
  R("authorize-options-whitelisted",
    !bagged.ok && bagged.reason === "authorize-options-unknown: [canonical_inputs]"
      && impl.ok && impl.request.expected_implementation_id === "impl-c-derive-v0.5.0",
    `${bagged.reason} — the draft spread \`...over\` after every authority-decided field, so a caller ` +
    `could overwrite canonical_inputs on an authority-ISSUED request. Exactly one field may be requested`);
  let froze = false;
  try { a.request.canonical_inputs.bias = 1000; } catch { froze = true; }
  R("issued-request-is-owned-and-frozen", froze && a.request.canonical_inputs.bias === 0,
    `the issued request is owned through canonicalBytes and deep-frozen; mutating it throws. Defence in ` +
    `depth — the BINDING is what refuses a modified request; this stops accidental modification inside ` +
    `the authority's own process`);
  const badIntents = [
    ["extra field", { ...intent, sneak: 1 }, /intent-schema/],
    ["missing field", { intent_id: "x", program_sem_id: PID }, /intent-schema/],
    ["resources not lists", { ...intent, requested_resources: { exact: "fb", predicates: [] } }, /intent-requested-exact-not-a-string-list/],
    ["capability in inputs", { ...intent, canonical_inputs: { f: () => 1 } }, /not-canonical/],
  ];
  R("intent-schema-closed", badIntents.every(([, i, rx]) => { const c = checkIntent(i); return !c.ok && rx.test(c.reason); }),
    badIntents.map(([l, i]) => `${l}:${checkIntent(i).ok ? "ADMITTED" : "refused"}`).join(" ") +
    ` — the untrusted half of the two-phase protocol is validated as strictly as the authority's half`);
  let noReader = "ACCEPTED";
  try { new DerivationAuthority({}); } catch (e) { noReader = e.message; }
  R("authority-requires-a-world", noReader === "authority-requires-a-world-reader",
    `${noReader} — an authority without a World cannot answer the temporal question, and one that ` +
    `silently could not would report fresh by never looking`);
}

console.log("═".repeat(96));
console.log(fail
  ? `DERIVE-BATTERY: FAIL — ${rows.filter((r) => !r.ok).length}/${rows.length}`
  : `DERIVE-BATTERY: PASS — ${rows.length}/${rows.length}. The program is data and its id commits the ` +
    `frozen core's semantics, not just its syntax; the grant is what the authority made available and ` +
    `the footprint is what the program consumed — a canonical dependency SET whose access order is a ` +
    `separate trace, outside semantics; the executor asserts its own identity; containment is ` +
    `historical and freshness is temporal; and issuance binds the whole request to the authority that ` +
    `cut it, which no caller can supply on its behalf.`);
process.exit(fail ? 1 : 0);
```

## `code/derive_realm_battery.mjs`

```javascript
/* derive_realm_battery.mjs — the crossing itself, v0.6.0.
   The claim under test is narrow and stated as such: OBJECT authority does not
   cross, the derivation realm reads only what it was granted, and the executor
   — not the caller — says which implementation ran. Determinism and host
   confinement are separate scopes and this battery does not touch them.
   Run: node derive_realm_battery.mjs */
import { Worker } from "node:worker_threads";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  ProgramRegistry, programSemId, canonicalBytes, validateForeignResult,
  resolveGrants, grantId, semanticProjection, JS_IMPLEMENTATION_ID,
  DerivationAuthority,
} from "./derive_protocol.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const reg = new ProgramRegistry(); const PID = reg.bind(P);
let fail = false;
const R = (id, ok, note) => { if (!ok) fail = true; console.log(`${ok ? "PASS" : "FAIL"}  ${id.padEnd(32)} ${note}`); };

const w = new Worker(join(HERE, "derive_worker.mjs"), { workerData: { programs: [P] } });
const ask = (req) => new Promise((res) => { w.once("message", res); w.postMessage(req); });

// the authority resolves the snapshot on the authoritative side, once
const worldReader = { read: (r) => ({ value: { fb: 5, "secret:key": 42 }[r], version: 1 }),
  scope: (q) => "scope:" + q };
const { read_grants, grant_id } = resolveGrants(worldReader, { exact: ["fb"] });
const mkReq = (over = {}) => ({ request_id: "r1", program_sem_id: PID,
  canonical_inputs: { bias: 0 }, read_grants, grant_id, ...over });

// 1. a callable cannot cross at all — the transport refuses it
{
  let threw = null;
  try { w.postMessage({ ...mkReq(), canonical_inputs: { bias: 0, evil: () => 1 } }); }
  catch (e) { threw = e.name + ": " + String(e.message).slice(0, 60); }
  R("closure-cannot-cross", threw !== null,
    `postMessage of a request carrying a function throws — ${threw ?? "IT CROSSED"}. ` +
    `The 9D.4 lexical-cell attack has no transport: structured cloning refuses callables, ` +
    `so the confinement is done by the boundary rather than by object discipline`);
}

// 2. an honest derivation crosses and comes back as a CLAIM, stamped by its executor
const honest = await ask(mkReq());
R("crossing-derives", honest.ok && honest.result.semantic_result.value === 5
    && honest.result.execution_evidence.implementation_id === JS_IMPLEMENTATION_ID && honest.result.grant_id === grant_id,
  `worker returned value ${honest.ok && honest.result.semantic_result.value} for fb=5 bias=0, resolving the program from ` +
  `its OWN registry by id and stamping the result ${honest.ok && honest.result.execution_evidence.implementation_id} against ` +
  `grant ${grant_id.slice(0, 18)}…`);

// 3. and the claim is only evidence once the authority re-derives it
{
  const req = mkReq();
  const local = validateForeignResult(reg, req, honest.result);
  const lied = validateForeignResult(reg, req, { ...honest.result,
    semantic_result: { ...honest.result.semantic_result, value: 1005 } });
  R("claim-revalidated-at-home", local.ok && !lied.ok && lied.reason === "foreign-result-divergence",
    `the worker's honest result reproduces locally against the same snapshot; an inflated one is ` +
    `refused (${lied.reason})`);
}

// 4. the worker cannot read anything it was not granted
{
  const empty = { exact: {}, predicates: {} };
  const r = await ask(mkReq({ read_grants: empty, grant_id: grantId(empty) }));
  R("ungranted-read-refused", !r.ok && /read-not-granted: fb/.test(r.reason),
    `${r.reason} — resolving reads is an AUTHORITY operation the parent performs; the worker holds no ` +
    `world and needs none`);
}

// 5. an unknown program is refused on the far side too
{
  const r = await ask(mkReq({ program_sem_id: programSemId({ op: "const", value: 1 }) }));
  R("unknown-program-refused", !r.ok && r.reason === "program-unknown",
    `${r.reason} — the worker resolves ids against its own registry, so a caller cannot name code the ` +
    `worker does not hold`);
}

// 6. THE GRANT TABLE IS NOT AN INPUT (W-1, across the boundary this time)
{
  const exfil = { op: "input", name: "__reads" };
  const reg2 = new ProgramRegistry(); const XID = reg2.bind(exfil);
  const w2 = new Worker(join(HERE, "derive_worker.mjs"), { workerData: { programs: [exfil] } });
  const ask2 = (req) => new Promise((res) => { w2.once("message", res); w2.postMessage(req); });
  const wide = resolveGrants(worldReader, { exact: ["fb", "secret:key"] });
  const r = await ask2({ request_id: "x", program_sem_id: XID,
    canonical_inputs: { __reads: "an ordinary input" },
    read_grants: wide.read_grants, grant_id: wide.grant_id });
  R("grant-not-reachable-as-input", r.ok && r.result.semantic_result.value === "an ordinary input"
      && r.result.semantic_result.read_footprint.exact.length === 0 && r.result.semantic_result.witness.reads === 0,
    `the worker granted fb and secret:key returns ${JSON.stringify(r.ok && r.result.semantic_result.value)} for ` +
    `{op:"input",name:"__reads"} — at v0.1.0 this returned the whole grant table across the same ` +
    `boundary, with an empty footprint and zero tracked reads`);
  await w2.terminate();
}

// 7. the far side asserts its identity, and refuses a requirement it cannot meet
{
  const r = await ask(mkReq({ expected_implementation_id: "impl-c-pretend-v9" }));
  const ok2 = await ask(mkReq({ expected_implementation_id: JS_IMPLEMENTATION_ID }));
  R("executor-asserts-implementation", !r.ok && /implementation-mismatch: want impl-c-pretend-v9/.test(r.reason)
      && ok2.ok && ok2.result.execution_evidence.implementation_id === JS_IMPLEMENTATION_ID,
    `a request demanding a C executor is refused by the JS worker (${r.reason}); one demanding JS runs ` +
    `and returns its own id. The caller states a requirement; the executor answers it`);
}

// 8. a forged footprint from the far side dies against the snapshot
{
  const req = mkReq();
  const forged = { ...honest.result,
    semantic_result: { ...honest.result.semantic_result,
      witness: { ...honest.result.semantic_result.witness, reads: 2 },
      read_footprint: { exact: [["fb", 1], ["secret:key", 1]], predicates: [] } },
    execution_evidence: { ...honest.result.execution_evidence,
      read_trace: { exact: [["fb", 1], ["secret:key", 1]], predicates: [] } } };
  const v = validateForeignResult(reg, req, forged);
  R("foreign-footprint-refused", !v.ok && v.reason === "footprint-ungranted-read: secret:key",
    `${v.reason} — the authority checks the returned footprint against the grant it issued, on its own ` +
    `evidence. The footprint is the dependency record and the grant is the capability record; the ` +
    `round-14 prose collapsed them and the mechanism supported neither`);
}

// 9. a conforming foreign implementation validates on the semantic projection
{
  const req = mkReq();
  const asIfC = { ...honest.result,
    execution_evidence: { ...honest.result.execution_evidence, implementation_id: "impl-c-derive-v0.6.0" } };
  const v = validateForeignResult(reg, req, asIfC);
  R("cross-implementation-shape", v.ok && v.implementation_id === "impl-c-derive-v0.6.0"
      && canonicalBytes(semanticProjection(asIfC)) === canonicalBytes(semanticProjection(honest.result)),
    `the same result stamped by a C executor validates and its provenance is RECORDED rather than ` +
    `compared away. This is the shape a real C implementation plugs into — it is not a claim that one ` +
    `exists, and this battery does not have one`);
}

// 10. intent → authority → realm → acceptance, and the World moving underneath
{
  const live = { res: { fb: { value: 5, version: 1 } }, read(r) { return { ...this.res[r] }; },
    scope(q) { return "scope:" + q; } };
  const auth = new DerivationAuthority(live);
  const a = auth.authorize({ intent_id: "i-realm", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const crossed = await ask(a.request);
  const accepted = auth.accept(reg, a.request, crossed.result);
  live.res.fb = { value: 9, version: 2 };                 // the World moves after the crossing
  const stale = auth.accept(reg, a.request, crossed.result);
  R("intent-to-acceptance", a.ok && crossed.ok && crossed.result.semantic_result.value === 5
      && accepted.ok && accepted.fresh_at_check === true
      && !stale.ok && stale.reason === "stale-read: fb granted@1 live@2",
    `a caller's INTENT is authorized into a request by the authority, crosses to a realm holding no ` +
    `world, returns a claim, and is accepted (fresh_at_check ${accepted.fresh_at_check}) — then the ` +
    `same claim is refused once fb moves 1→2 (${stale.reason}). The worker never learns the World exists`);
}

await w.terminate();
console.log("═".repeat(96));
console.log(fail ? "DERIVE-REALM: FAIL"
  : "DERIVE-REALM: PASS — object authority does not cross the boundary, the realm reads only its grant, " +
    "and the executor names itself. Determinism and host confinement are SEPARATE scopes and are not claimed here.");
process.exit(fail ? 1 : 0);
```

## `code/probe_traceforge_v06_repro.mjs`

```javascript
/* ═══════════════════════════════════════════════════════════════════════════
   probe_traceforge_v06_repro.mjs — "outside the semantic projection" had
   quietly become "unchecked".

   Round 16 ruled that access ORDER is execution strategy and must not be
   semantic identity: depending on {a,b} is one dependency set however it was
   visited. That ruling was right and remains. What it did not say — and what
   v0.5.0 therefore did not do — is that a field excluded from the comparison
   still needs a rule of its own.

   T-1  A FORGED TRACE VALIDATED AND WAS ACCEPTED. A program reading `a` then
        `b` honestly traces [["a",1],["b",1]]. Reverse ONLY the trace, leave the
        canonical footprint and the value untouched, and against v0.5.0:

            validateForeignResult  -> { ok: true }
            authority.accept       -> { ok: true, validated: true,
                                        fresh_at_check: true }

        checkResult compared the footprint to the SET of the trace — which a
        reversal does not change — and validateForeignResult compared only the
        semantic projection, from which the trace was excluded. So the one field
        carrying execution evidence was the one field nothing looked at.

   WHY THE FLAT SHAPE WAS PART OF THE DEFECT. read_trace sat as a sibling of
   value, support and read_footprint. A field inside DeriveResult reads as
   authenticated by the same machinery as its neighbours, and this one was not.
   v0.6.0 makes the envelopes explicit — `semantic_result` and
   `execution_evidence` — so that the trust status of each is visible in the
   shape rather than only in a comment.

   AND THE RULE ITSELF: the core PROMISES deterministic left-to-right
   evaluation, so a trace disagreeing with an honest re-derivation is a
   CONFORMANCE failure of the implementation, not a disagreement about the
   program. It is refused, and the two verdicts are reported separately —
   `semantic_agreement: true, trace_conforms: false` — because "same meaning,
   different strategy" and "wrong answer" are different diagnoses and v0.5.0
   could make neither.

   NON-SEMANTIC DOES NOT MEAN UNVERIFIED.

   PAIRED, and it gates.
   ═══════════════════════════════════════════════════════════════════════════ */
import {
  ProgramRegistry, DerivationAuthority, deriveLocally, validateForeignResult,
  canonicalBytes, SEMANTIC_RESULT_FIELDS, EXECUTION_ENVELOPE_FIELDS, validateTraceConformance,
} from "./derive_protocol.mjs";

const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "CONFINED" : "BREACH  "}  ${id.padEnd(22)} ${note}`); };

const P = { op: "add", a: { op: "read", resource: "a" }, b: { op: "read", resource: "b" } };
const mkWorld = () => ({ res: { a: { value: 1, version: 1 }, b: { value: 2, version: 1 } },
  read(r) { return { ...this.res[r] }; }, scope(q) { return "scope:" + q; } });
const reg = new ProgramRegistry(); const PID = reg.bind(P);
const intent = { intent_id: "t-1", program_sem_id: PID, canonical_inputs: {},
  requested_resources: { exact: ["a", "b"], predicates: [] } };

/* ── v0.5.0's validation of a result, VERBATIM in its essentials ──────────
   The flat result shape, the footprint-is-the-set-of-the-trace check, and a
   semantic projection that excluded implementation_id and read_trace — after
   which nothing else looked at the trace. Do not repair anything here. */
const V5_SEMANTIC = ["request_id", "program_sem_id", "grant_id", "value", "witness", "support", "read_footprint"];
const v5Flatten = (res) => ({
  request_id: res.request_id, program_sem_id: res.program_sem_id, grant_id: res.grant_id,
  implementation_id: res.execution_evidence.implementation_id,
  value: res.semantic_result.value, witness: res.semantic_result.witness,
  support: res.semantic_result.support, read_footprint: res.semantic_result.read_footprint,
  read_trace: res.execution_evidence.read_trace,
});
function v5Validate(registry, req, res) {
  // schema-ish: the footprint must be the canonical SET of the trace
  for (const kind of ["exact", "predicates"]) {
    const seen = new Map();
    for (const pr of res.read_trace[kind]) seen.set(canonicalBytes(pr), pr);
    const want = [...seen.values()].sort((x, y) => canonicalBytes(x) < canonicalBytes(y) ? -1 : 1);
    if (canonicalBytes(res.read_footprint[kind]) !== canonicalBytes(want))
      return { ok: false, reason: "result-footprint-not-canonical-set: " + kind };
  }
  const mine = v5Flatten(deriveLocally(registry, req).result);
  const proj = (r) => { const o = {}; for (const f of V5_SEMANTIC) o[f] = r[f]; return o; };
  return canonicalBytes(proj(mine)) === canonicalBytes(proj(res))
    ? { ok: true } : { ok: false, reason: "foreign-result-divergence" };
}

/* ── T-1 against the frozen v0.5.0 validation ─────────────────────────────── */
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request: req } = auth.authorize(intent);
  const honest = v5Flatten(deriveLocally(reg, req).result);
  const forged = { ...honest, read_trace: { exact: [...honest.read_trace.exact].reverse(), predicates: [] } };
  const v = v5Validate(reg, req, forged);
  R("T-1 frozen-v0.5.0", !v.ok,
    `honest trace ${JSON.stringify(honest.read_trace.exact)} reversed to ` +
    `${JSON.stringify(forged.read_trace.exact)} with the footprint ` +
    `${JSON.stringify(forged.read_footprint.exact)} and the value ${forged.value} untouched: ` +
    `validateForeignResult -> ok=${v.ok}. The footprint check compares the SET, which a reversal does ` +
    `not change, and the semantic projection excluded the trace — so nothing looked at it`);
}

/* ── the same forgery against live ────────────────────────────────────────── */
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request: req } = auth.authorize(intent);
  const honest = deriveLocally(reg, req).result;
  const forged = { ...honest, execution_evidence: { ...honest.execution_evidence,
    read_trace: { exact: [...honest.execution_evidence.read_trace.exact].reverse(), predicates: [] } } };
  const v = validateForeignResult(reg, req, forged);
  const acc = auth.accept(reg, req, forged);
  R("T-1 live", !v.ok && v.reason === "trace-nonconforming: exact"
      && v.semantic_agreement === true && v.trace_conforms === false
      && !acc.ok && acc.reason === "trace-nonconforming: exact",
    `${v.reason} — and the two verdicts are reported SEPARATELY: semantic_agreement ` +
    `${v.semantic_agreement}, trace_conforms ${v.trace_conforms}. "Same meaning, different strategy" ` +
    `and "wrong answer" are different diagnoses, and v0.5.0 could make neither`);
}

/* ── the honest result still passes, and reports both verdicts ────────────── */
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request: req } = auth.authorize(intent);
  const honest = deriveLocally(reg, req).result;
  const acc = auth.accept(reg, req, honest);
  R("honest-still-accepted", acc.ok && acc.trace_conforms === true && acc.validated === true
      && acc.committable === undefined,
    `an honest result is accepted with validated ${acc.validated}, trace_conforms ${acc.trace_conforms} ` +
    `and still NO committable — the new check refuses a forgery without inventing a stronger claim ` +
    `about the honest case`);
}

/* ── and the shape now says which fields carry which trust status ─────────── */
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request: req } = auth.authorize(intent);
  const honest = deriveLocally(reg, req).result;
  R("envelopes-are-explicit",
    canonicalBytes(Object.keys(honest).sort()) ===
      canonicalBytes(["execution_evidence", "grant_id", "program_sem_id", "request_id", "semantic_result"])
      && canonicalBytes(EXECUTION_ENVELOPE_FIELDS) === canonicalBytes(["implementation_id", "read_trace"])
      && !SEMANTIC_RESULT_FIELDS.includes("execution_evidence"),
    `the result is {${Object.keys(honest).sort().join(", ")}} and the semantic projection is ` +
    `[${SEMANTIC_RESULT_FIELDS.join(", ")}]. At v0.5.0 read_trace was a SIBLING of value and ` +
    `read_footprint, which reads as authenticated by the same machinery as its neighbours — and was not`);
  // the conformance rule is a real function with its own verdict, not a comment
  const t = validateTraceConformance({ exact: [["a", 1]], predicates: [] }, { exact: [["b", 1]], predicates: [] });
  R("trace-rule-is-executable", !t.ok && t.reason === "trace-nonconforming: exact",
    `validateTraceConformance is exported and refuses by name (${t.reason}) — the core FIXES evaluation ` +
    `order so refusals and traces reproduce, so a disagreeing trace is a conformance failure of the ` +
    `implementation rather than a disagreement about the program`);
}

console.log("=".repeat(100));
const frozenHeld = results.filter((r) => r.id.includes("frozen") && r.held);
const liveBreached = results.filter((r) => !r.id.includes("frozen") && !r.held);
console.log(
  `TRACE-FORGE v0.6 REPRO: ${results.filter((r) => r.id.includes("frozen") && !r.held).length}/1 reproduce ` +
  `against the frozen v0.5.0 · ${results.filter((r) => !r.id.includes("frozen") && r.held).length}/4 confined against live` +
  (frozenHeld.length ? ` — VACUOUS: ${frozenHeld.map((r) => r.id).join(", ")}` : "") +
  (liveBreached.length ? ` — REGRESSION: ${liveBreached.map((r) => r.id).join(", ")}` : ""));
process.exit(frozenHeld.length + liveBreached.length ? 1 : 0);
```

## `code/probe_issuebind_v05_repro.mjs`

```javascript
/* ═══════════════════════════════════════════════════════════════════════════
   probe_issuebind_v05_repro.mjs — issuance authenticated the grant, not the
   request; and acceptance took both of its proofs from the caller.

   The draft authority (never committed, frozen below) recorded

       request_id -> grant_id

   and derived `request_id = H(intent_id | grant_id)`. Neither binds the
   program, the inputs, or the implementation requirement — so "was this
   issued?" was answered about a *grant*, while the thing being accepted was a
   *request*. Three consequences, all reproduced:

   I-1  SWAP THE INPUTS. Take an honest request with canonical_inputs.bias = 0,
        change only bias to 1000, keep request_id and grant_id. wasIssued says
        true, the derivation returns 1005, acceptance returns committable.
        The authority accepted request content it never issued.

   I-2  INJECT THROUGH THE OPTIONS BAG. `authorize(intent, over)` applied
        `...over` AFTER every authority-created field, so the caller could
        overwrite canonical_inputs on an authority-ISSUED request. Same 1005,
        with the authority's own stamp on it.

   I-3  OMIT THE AUTHORITY ENTIRELY. `acceptForeignResult(..., issuer = null)`
        defaulted issuance checking to OFF, and took `liveReader` as a
        parameter. So a wholly self-made request with a self-made grant was
        accepted with no issuer; and after the World moved fb@1 -> fb@2, a fake
        liveReader that simply replayed the old grant turned a refusal back
        into committable. Acceptance was a pure function whose caller supplied
        both proofs of authority.

   THE SHAPE OF THE REPAIR, because it is not "add a signature". A signature
   would authenticate the authority to itself while caller and authority are the
   same party. What was missing is binding: issuance now records
   `request_id -> request_sem_id = H(canonical request)`, recomputed at
   acceptance, so any change to any field is a different request. The options
   bag is gone and only `expected_implementation_id` may be requested. The
   returned request is owned and frozen through canonicalBytes. And acceptance
   is a METHOD ON THE AUTHORITY, closing over its own issuance table and its own
   live reader — neither is a parameter any more, because a caller that can pass
   the proof is not being checked by it.

   PAIRED, and it gates. Exit 0 requires each witness to still reproduce against
   the frozen draft AND to be confined against live.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import {
  ProgramRegistry, deriveLocally, grantId, resolveGrants, canonicalBytes,
  DerivationAuthority, requestSemId,
} from "./derive_protocol.mjs";

const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "CONFINED" : "BREACH  "}  ${id.padEnd(24)} ${note}`); };

const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const mkWorld = () => ({
  res: { fb: { value: 5, version: 1 } },
  read(r) { const e = this.res[r]; if (!e) throw new Error("no-such-resource: " + r); return { ...e }; },
  scope(q) { return "scope:" + q; },
  write(r, v) { this.res[r] = { value: v, version: (this.res[r]?.version ?? 0) + 1 }; },
});

/* ── THE DRAFT AUTHORITY, VERBATIM ────────────────────────────────────────
   request_id from (intent_id, grant_id); issuance table keyed on grant_id;
   an options bag applied last; acceptance a free function with a defaulted
   issuer and a caller-supplied reader. Do not repair anything here. */
const H = (s) => createHash("sha256").update(s).digest("hex");
class DraftIssuer {
  #issued = new Map();
  #reader;
  constructor(reader) { this.#reader = reader; Object.freeze(this); }
  authorize(intent, over = {}) {
    const g = resolveGrants(this.#reader, intent.requested_resources);
    const req = {
      request_id: "req-" + H("TRVM-REQUEST-v1|" + intent.intent_id + "|" + g.grant_id),
      program_sem_id: intent.program_sem_id,
      canonical_inputs: intent.canonical_inputs,
      read_grants: g.read_grants, grant_id: g.grant_id, ...over,   // <<< I-2 LIVES HERE
    };
    this.#issued.set(req.request_id, g.grant_id);                  // <<< I-1: binds the GRANT only
    return { ok: true, request: req };
  }
  wasIssued(request_id, grant_id) { return this.#issued.get(request_id) === grant_id; }
}
function draftAccept(registry, req, res, liveReader, issuer = null) {   // <<< I-3: both are parameters
  if (issuer && !issuer.wasIssued(req.request_id, req.grant_id))
    return { ok: false, reason: "grant-not-issued-by-this-authority" };
  const mine = deriveLocally(registry, req);
  if (!mine.ok) return mine;
  if (canonicalBytes(mine.result) !== canonicalBytes(res)) return { ok: false, reason: "foreign-result-divergence" };
  for (const [r, ver] of res.semantic_result.read_footprint.exact ?? []) {
    const cur = liveReader.read(r);
    if (cur?.version !== ver) return { ok: false, reason: "stale-read: " + r + " granted@" + ver + " live@" + cur?.version };
  }
  return { ok: true, committable: true };
}

const reg = new ProgramRegistry(); const PID = reg.bind(P);
const intent = { intent_id: "i-1", program_sem_id: PID, canonical_inputs: { bias: 0 },
  requested_resources: { exact: ["fb"], predicates: [] } };

/* ── I-1 against the draft: swap the inputs, keep the ids ─────────────────── */
{
  const world = mkWorld(); const iss = new DraftIssuer(world);
  const { request: req } = iss.authorize(intent);
  const forged = { ...req, canonical_inputs: { bias: 1000 } };
  const res = deriveLocally(reg, forged).result;
  const acc = draftAccept(reg, forged, res, world, iss);
  R("I-1 frozen-draft", !(iss.wasIssued(forged.request_id, forged.grant_id) && acc.ok),
    `bias 0 -> 1000 with request_id and grant_id untouched: wasIssued ${iss.wasIssued(forged.request_id, forged.grant_id)}, ` +
    `value ${res.semantic_result.value}, accept ok=${acc.ok} committable=${acc.committable} — the authority accepted ` +
    `request content it never issued, because issuance was keyed on the GRANT`);
}
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request: req } = auth.authorize(intent);
  const forged = { ...req, canonical_inputs: { bias: 1000 } };
  const res = deriveLocally(reg, forged).result;
  const acc = auth.accept(reg, forged, res);
  R("I-1 live", !acc.ok && acc.reason === "request-not-as-issued",
    `the same swap is refused: ${acc.reason}. Issuance records request_id -> ` +
    `requestSemId = H(canonical request), recomputed at acceptance, so any change to any field is a ` +
    `different request rather than the same one with different content`);
}

/* ── I-2: the options bag overwrote authority-created fields ──────────────── */
{
  const world = mkWorld(); const iss = new DraftIssuer(world);
  const { request } = iss.authorize(intent, { canonical_inputs: { bias: 1000 } });
  const res = deriveLocally(reg, request).result;
  const acc = draftAccept(reg, request, res, world, iss);
  R("I-2 frozen-draft", !(acc.ok && res.semantic_result.value === 1005),
    `authorize(intent, {canonical_inputs:{bias:1000}}) produced an AUTHORITY-ISSUED request evaluating ` +
    `to ${res.semantic_result.value}, accepted (committable ${acc.committable}) — \`...over\` was spread after every ` +
    `field the authority had just decided`);
}
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const bad = auth.authorize(intent, { canonical_inputs: { bias: 1000 } });
  const okImpl = auth.authorize(intent, { expected_implementation_id: "impl-c-derive-v0.5.0" });
  R("I-2 live", !bad.ok && /authorize-options-unknown/.test(bad.reason)
      && okImpl.ok && okImpl.request.expected_implementation_id === "impl-c-derive-v0.5.0",
    `${bad.reason} — the options bag is gone; exactly one field may be REQUESTED by a caller, and it is ` +
    `a requirement on the executor rather than authority content`);
}

/* ── I-3: acceptance took both of its proofs from the caller ──────────────── */
{
  const world = mkWorld();
  const g = { exact: { fb: { value: 5, version: 1 } }, predicates: {} };
  const self = { request_id: "req-self-made", program_sem_id: PID, canonical_inputs: { bias: 1000 },
    read_grants: g, grant_id: grantId(g) };
  const res = deriveLocally(reg, self).result;
  const noIssuer = draftAccept(reg, self, res, world);          // issuer omitted entirely
  const iss = new DraftIssuer(world);
  const { request: honest } = iss.authorize(intent);
  const hres = deriveLocally(reg, honest).result;
  world.write("fb", 9);
  const real = draftAccept(reg, honest, hres, world, iss);
  const fake = draftAccept(reg, honest, hres,
    { read: () => ({ value: 5, version: 1 }), scope: (q) => "scope:" + q }, iss);
  R("I-3 frozen-draft", !(noIssuer.ok && !real.ok && fake.ok),
    `a wholly self-made request accepted with the issuer OMITTED (ok=${noIssuer.ok}, value ${res.semantic_result.value}); ` +
    `and after fb@1->fb@2 the real reader refuses (${real.reason}) while a fake reader replaying the ` +
    `grant returns committable=${fake.committable}. Acceptance was a pure function whose caller ` +
    `supplied both proofs of authority`);
}
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const g = { exact: { fb: { value: 5, version: 1 } }, predicates: {} };
  const self = { request_id: "req-self-made", program_sem_id: PID, canonical_inputs: { bias: 1000 },
    read_grants: g, grant_id: grantId(g) };
  const res = deriveLocally(reg, self).result;
  const selfMade = auth.accept(reg, self, res);
  const { request: honest } = auth.authorize(intent);
  const hres = deriveLocally(reg, honest).result;
  const before = auth.accept(reg, honest, hres);
  world.write("fb", 9);
  const after = auth.accept(reg, honest, hres);
  R("I-3 live", !selfMade.ok && selfMade.reason === "grant-not-issued-by-this-authority"
      && before.ok && before.fresh_at_check === true && before.committable === undefined
      && !after.ok && /^stale-read: fb granted@1 live@2/.test(after.reason),
    `self-made request -> ${selfMade.reason}; honest request -> ok with fresh_at_check ` +
    `${before.fresh_at_check} and NO committable field; after fb moves -> ${after.reason}. ` +
    `accept() is a method: the issuance table and the live reader are closed over, not passed in, ` +
    `and there is no argument a caller can supply to switch either off`);
}

/* ── and the request the authority hands back is owned and frozen ─────────── */
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request } = auth.authorize(intent);
  let froze = false;
  try { request.canonical_inputs.bias = 1000; } catch { froze = true; }
  const acc = auth.accept(reg, request, deriveLocally(reg, request).result);
  R("issued-request-is-owned", froze && request.canonical_inputs.bias === 0 && acc.ok
      && requestSemId(request) === requestSemId(JSON.parse(canonicalBytes(request))),
    `mutating the issued request throws and it still reads bias ${request.canonical_inputs.bias}. ` +
    `Defence in depth rather than the boundary: the binding is what refuses a modified request, and ` +
    `the freeze is what stops one being modified by accident in the authority's own process`);
}

console.log("=".repeat(100));
const frozenHeld = results.filter((r) => r.id.includes("frozen") && r.held);
const liveBreached = results.filter((r) => !r.id.includes("frozen") && !r.held);
console.log(
  `ISSUE-BIND v0.5 REPRO: ${results.filter((r) => r.id.includes("frozen") && !r.held).length}/3 reproduce ` +
  `against the frozen draft · ${results.filter((r) => !r.id.includes("frozen") && r.held).length}/4 confined against live` +
  (frozenHeld.length ? ` — VACUOUS: ${frozenHeld.map((r) => r.id).join(", ")}` : "") +
  (liveBreached.length ? ` — REGRESSION: ${liveBreached.map((r) => r.id).join(", ")}` : ""));
process.exit(frozenHeld.length + liveBreached.length ? 1 : 0);
```

## `code/probe_stalegrant_v03_repro.mjs`

```javascript
/* ═══════════════════════════════════════════════════════════════════════════
   probe_stalegrant_v03_repro.mjs — every check passed and the result was not
   committable.

   This one is not a regression witness. It is a GAP witness: v0.2.0 had no
   freshness check at all, and the shape of the hole is what makes it worth
   freezing. Review put it precisely — `footprintWithinGrant` answers a
   HISTORICAL question (was every claimed read inside the snapshot this
   derivation received?) and freshness answers a TEMPORAL one (are those
   dependencies still current NOW, at acceptance?). Both can be satisfied about
   a world that has moved.

   The witness:

       cut grant           fb@1 = 5
       derive against it   value 5, footprint [["fb",1]]
       World moves         fb@2 = 9

       checkResult                 PASS
       footprintWithinGrant        PASS
       validateForeignResult       PASS   (re-derives against the same snapshot)
       ─────────────────────────────────
       live freshness              MUST REFUSE

   All three passing checks are CORRECT. Nothing lied. The executor and the
   authority agree perfectly about a snapshot, and the snapshot is stale — so a
   protocol that stops at re-derivation commits a value the World has already
   contradicted.

   It also witnesses the negative half, which matters as much: an UNRELATED
   write must not invalidate. Freshness keys on the footprint, never on a global
   vclock — that is the whole reason the footprint is the dependency record and
   the grant is not, and a vclock rule would silently undo it.

   And the TOCTOU shape is witnessed rather than asserted: a freshness check
   that returns to the caller before the commit is a window, so acceptance is
   one call and the caller must hold the World's commit lock across it.
   ═══════════════════════════════════════════════════════════════════════════ */
import {
  ProgramRegistry, checkResult, footprintWithinGrant, validateForeignResult,
  validateFootprintFresh, deriveLocally, DerivationAuthority,
} from "./derive_protocol.mjs";

const results = [];
// "GAP" is reserved for the one row that is the finding rather than a property:
// the v0.2.0-era checks pass on a stale result, correctly, and that is the hole.
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "HOLDS" : "GAP  "}  ${id.padEnd(30)} ${note}`); };

/* a tiny mutable World: versioned resources plus one registered scope query */
const world = {
  res: { fb: { value: 5, version: 1 }, other: { value: 0, version: 1 } },
  scopes: { "kind:node": ["a", "b"] },
  read(r) { const e = this.res[r]; if (!e) throw new Error("no-such-resource: " + r); return { ...e }; },
  scope(q) { const s = this.scopes[q]; if (!s) throw new Error("no-such-scope: " + q); return [...s]; },
  write(r, value) { const e = this.res[r]; this.res[r] = { value, version: (e?.version ?? 0) + 1 }; },
};

const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const reg = new ProgramRegistry(); const PID = reg.bind(P);
const authority = new DerivationAuthority(world);

const intent = { intent_id: "i-1", program_sem_id: PID, canonical_inputs: { bias: 0 },
  requested_resources: { exact: ["fb"], predicates: [] } };
const { request: req } = authority.authorize(intent);
const res = deriveLocally(reg, req).result;

console.log(`grant ${req.grant_id.slice(0, 20)}… cut at fb@1=5 · derived value ${res.semantic_result.value} · ` +
  `footprint ${JSON.stringify(res.semantic_result.read_footprint.exact)}`);

/* ── the World moves under the derivation ─────────────────────────────────── */
world.write("fb", 9);
console.log(`World moved: fb is now @${world.res.fb.version}=${world.res.fb.value}\n`);

{
  const a = checkResult(res, req);
  const b = footprintWithinGrant(res.semantic_result.read_footprint, req.read_grants);
  const c = validateForeignResult(reg, req, res);
  R("containment-era checks", false,
    `checkResult ${a.ok ? "PASS" : a.reason} · footprintWithinGrant ${b.ok ? "PASS" : b.reason} · ` +
    `validateForeignResult ${c.ok ? "PASS" : c.reason} — all three CORRECT, and the value 5 is now wrong ` +
    `in a World where fb is 9. Re-derivation against the same snapshot can never notice this`);

  const f = validateFootprintFresh(world, res.semantic_result.read_footprint);
  R("live freshness", !f.ok && /^stale-read: fb granted@1 live@2/.test(f.reason),
    `${f.reason} — the temporal question, asked against the LIVE world and keyed on the footprint`);

  const acc = authority.accept(reg, req, res);
  R("acceptance refuses", !acc.ok && /^stale-read: fb/.test(acc.reason),
    `${acc.reason} — issuance, validation and freshness in ONE call on the AUTHORITY, which closes over ` +
    `its own reader and issuance table so neither proof can arrive as an argument`);
}

/* ── the negative half: an unrelated write must NOT invalidate ────────────── */
{
  world.res.fb = { value: 5, version: 1 };          // restore the granted state
  world.write("other", 999);                        // a write the derivation never read
  const acc = authority.accept(reg, req, res);
  R("unrelated-write-ignored", acc.ok && acc.fresh_at_check === true && acc.committable === undefined,
    `other@${world.res.other.version} moved and acceptance still passes (fresh_at_check ${acc.fresh_at_check}, ` +
    `and NO committable field — one call cannot make a result committable, only observed fresh) — ` +
    `freshness keys on the FOOTPRINT, not on a global vclock. A vclock rule would invalidate every ` +
    `derivation on every unrelated write and quietly undo the grant/footprint separation`);
}

/* ── a scope whose result set moved, with no exact read touched ───────────── */
{
  const S = { op: "len", a: { op: "scope", query: "kind:node" } };
  const reg2 = new ProgramRegistry(); const SID = reg2.bind(S);
  const auth2 = new DerivationAuthority(world);
  const { request: r2 } = auth2.authorize({ intent_id: "i-2", program_sem_id: SID,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: ["kind:node"] } });
  const s2 = deriveLocally(reg2, r2).result;
  world.scopes["kind:node"] = ["a", "b", "c"];       // the phantom: a node joins
  const acc = auth2.accept(reg2, r2, s2);
  R("scope-digest-staleness", !acc.ok && acc.reason === "stale-scope: kind:node",
    `${acc.reason} — value ${s2.semantic_result.value} was derived over 2 nodes and the query now answers 3, with no ` +
    `exact read having moved. This is the World's phantom-scope case (law:warrant.phantom-scope@1) ` +
    `reaching the derivation boundary`);
}

/* ── issuance: grant_id proves integrity, not authority ───────────────────── */
{
  const forged = { ...req, request_id: "req-self-made" };
  const acc = new DerivationAuthority(world).accept(reg, req, res);
  const accForged = authority.accept(reg, forged, { ...res, request_id: "req-self-made" });
  R("grant-id-is-not-issuance", !acc.ok && acc.reason === "grant-not-issued-by-this-authority"
      && !accForged.ok && accForged.reason === "grant-not-issued-by-this-authority",
    `a DIFFERENT authority instance refuses the same well-formed request (${acc.reason}), and a ` +
    `self-made request_id is refused by the issuing one. grant_id = H(read_grants) authenticates ` +
    `content to itself and proves nothing about who cut it; the issuance table is what does`);
}

console.log("=".repeat(100));
const bad = results.filter((r) => r.id === "containment-era checks" ? r.held : !r.held);
console.log(`STALE-GRANT v0.3 WITNESS: ${results.filter((r) => r.id !== "containment-era checks" && r.held).length}/5 ` +
  `hold; the three containment-era checks pass on a stale result BY DESIGN, which is the finding` +
  (bad.length ? ` — FAILURES: ${bad.map((r) => r.id).join(", ")}` : ""));
process.exit(bad.length ? 1 : 0);
```

## `code/probe_coresem_v03_repro.mjs`

```javascript
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
```

## `record/CORE_SPEC.json`

```json
{
 "PROTOCOL_VERSION": "0.6.0",
 "JS_IMPLEMENTATION_ID": "impl-js-derive-v0.6.0",
 "CORE_SEM_ID": "core-0930d6f10070a8e7867b99cbaf6297234fe6fbc174ed25a72388dac9944f3afe",
 "SEMANTIC_RESULT_FIELDS": [
  "request_id",
  "program_sem_id",
  "grant_id",
  "semantic_result"
 ],
 "EXECUTION_ENVELOPE_FIELDS": [
  "implementation_id",
  "read_trace"
 ],
 "CORE_SPEC": {
  "language": "TRVM-DERIVE-CORE",
  "version": 1,
  "value_domain": "null | boolean | finite number | string | canonical array | canonical plain object. Non-finite numbers, cycles, and non-plain objects (Map, Set, Date, class instances, transferable handles) are not values and are refused wherever they appear.",
  "numbers": "IEEE-754 binary64. Every arithmetic OPERAND must be a number — there is no coercion, no string concatenation and no object stringification — and every arithmetic RESULT must be finite. Overflow is a refusal at the operation, not a non-finite value handed onward.",
  "signed_zero": "the canonical numeric quotient IDENTIFIES -0 with +0. canonicalBytes serializes both as \"0\", so they are one value in the message domain, in warrant_id, in replay and in every equality this system takes. An implementation must not distinguish them at the boundary even where its own arithmetic does. Stated because it was already true of the canonical domain and unstated — which is how a C implementation would have decided it by accident.",
  "evaluation_order": "depth-first, operands in declared field order: `a` fully evaluated before `b`. This is DETERMINISTIC so that refusals, short-circuiting and the execution trace are the same everywhere. It is deliberately NOT semantic identity: see read_footprint.",
  "read_footprint": "a canonical DEPENDENCY SET, not a sequence — sorted and deduplicated. Depending on {a,b} must not become a different semantic identity because one correct implementation visited a then b and another visited b then a. Execution strategy does not silently become semantics unless the calculus requires it, which is the same principle that keeps ref_interactions out of conformance identity. Access ORDER, with repeats, is preserved separately in read_trace, which is evidence-plane material and is excluded from the semantic projection.",
  "ops": {
   "const": {
    "fields": [
     "value"
    ],
    "returns": "the literal, which must be a canonical value"
   },
   "input": {
    "fields": [
     "name"
    ],
    "reads": "canonical_inputs ONLY — never read_grants"
   },
   "read": {
    "fields": [
     "resource"
    ],
    "reads": "read_grants.exact; appends [resource, version] to the footprint"
   },
   "scope": {
    "fields": [
     "query"
    ],
    "reads": "read_grants.predicates; appends [query, digest] to the footprint"
   },
   "cite": {
    "fields": [
     "name"
    ],
    "reads": "read_grants.exact under the key \"warrant:\" + name; returns .value.value"
   },
   "add": {
    "fields": [
     "a",
     "b"
    ],
    "returns": "numeric sum"
   },
   "sub": {
    "fields": [
     "a",
     "b"
    ],
    "returns": "numeric difference"
   },
   "mul": {
    "fields": [
     "a",
     "b"
    ],
    "returns": "numeric product"
   },
   "len": {
    "fields": [
     "a"
    ],
    "returns": "array length; a non-array operand is refused"
   }
  },
  "grammar": "every node is a plain object whose key set is EXACTLY {op} union the op's declared fields. Unknown ops, missing fields and extra fields are all refused at bind time, so an id is never issued for a program outside the language.",
  "refusals": [
   "program-malformed-node",
   "program-unknown-op",
   "program-node-fields",
   "program-name-not-a-string",
   "program-const-not-canonical",
   "program-input-missing",
   "program-type",
   "program-arith-non-finite",
   "read-not-granted",
   "scope-not-granted"
  ],
  "totality": "the core is TOTAL: no recursion, no unbounded loop, no general function. Every program terminates in a number of steps bounded by its own node count.",
  "extension": "new behaviour arrives as {op:'prim', primitive_sem_id, args} with a content-bound primitive identity, never as if/while/function/closure/eval. A prim extension bumps the CORE version and therefore every program id, which is intended: a program written against a different language is a different program."
 }
}
```

## `record/grid-sections.json`

```json
{
 "_note": "TRVM/governance/invariant-grid.json v1.22.0 — derivation + evidence sections only.",
 "grid_version": "1.22.0",
 "law_registry_entries": [
  {
   "id": "evidence.instrument-nonvacuity",
   "revision": 1,
   "status": "PROPERTY-TESTED",
   "canonical": true,
   "statement": "An audit result is creditable only if the instrument independently proves that the intended perturbation occurred, the intended execution path was exercised, and the measured predicate is the one reported. A falsifier that forges nothing, runs nothing, or measures a different predicate than it names is VACUOUS, and a vacuous falsifier is worse than an absent one because the roster still counts it. Mutation cases must show before_hash != after_hash before the detector's verdict counts.",
   "evidence": "negative_battery.sh computes a pre- and post-perturbation digest of every scratch tree and refuses to credit a case whose forgery changed nothing (diagnostic: VACUOUS). This law is retrospective as much as prospective: it covers the unset $SCRATCH that meant a case could never execute, the hand-typed 44/44 that stopped counting the cases, the hard-coded \"1.0.2\" replacement that a version bump would have turned into a no-op, the prototype half of the authority graph that went untested, the false '9D-4 confined' produced by poisoning a node whose semantic path the pass overwrote, and a probe line that printed 'directly assignable' while testing typeof === 'function'. Six apparatus failures across four rounds, every one of which this rule would have caught mechanically. MECHANISED (both runners, v1.14.0): clause 1 — the intended target is DERIVED from the perturbation script (files opened for writing, files removed) and must EQUAL the set that actually changed, so a case editing the wrong artifact, or an extra one, fails as loudly as one editing nothing; clauses 2-3 — per-file digests before and after, refusing VACUOUS and naming the artifact perturbed; clause 5 — the specific diagnostic must match; clause 6 — CAUGHT increments only after all of the above. Both detectors were verified to FIRE by deliberately breaking a case (VACUOUS: 57/58; TARGET MISMATCH: 63/64) and restoring it. STILL DECLARED OPEN: clause 4, independent evidence that the intended EXECUTION PATH ran — the diagnostic match is a weak proxy, and the false '9D-4 confined' result came from a witness that never entered the semantic path it was written for. Closing it needs the verifier to report which rules it evaluated, not merely which one failed."
  },
  {
   "id": "evidence.harness-selftest",
   "revision": 1,
   "status": "REGRESSION-LOCKED",
   "canonical": true,
   "statement": "The apparatus is measured by a gate, not by attention. law:evidence.instrument-nonvacuity@1 requires each falsifier to be non-vacuous; this requires the HARNESS ITSELF to demonstrate that it detects the failure species that have actually occurred in this tree. Nine are enumerated and each has a meta-falsifier: working-directory dependence, an absent declared artifact, a present undeclared artifact, a perturbation that changes nothing, a case that DELETES rather than modifies, a case that moves an artifact it did not declare, a case whose expected diagnostic is not the one produced, a paired probe whose frozen side has been silently repaired, and — the one a battery of forgeries cannot see — an UNPERTURBED case tree that does not pass the checker. Eight require the harness to SAY SO; the ninth requires it to say nothing when nothing is wrong. Deliberately BOUNDED: this encodes the known failure species and does not recurse into tests of tests.",
   "evidence": "harness_selftest.sh, 9/9. The motivating record is six consecutive rounds in which the instrument rather than the engine was wrong: the unset $SCRATCH, the hand-typed 44/44, the hard-coded \"1.0.2\" version forgery, the probe line printing 'directly assignable' while testing typeof, the false '9D-4 confined' from a witness that never entered its path, a non-vacuity law registered one round before its harness implemented it, a one-sided diff that called a deleting case vacuous, round 15's two CWD-relative reads — one of which scanned the empty string and reported success — and round 17's contaminated baseline, where every negative case since round 14 had run against a checker already reporting four unrelated failures. The self-test caught three defects in its own first draft: a header split that captured the run_case DEFINITION rather than its first invocation, an M-8 repair that did not neutralise the witness it was meant to neutralise, and an M-1 that asserted a PASSING verdict where its subject was an IDENTICAL one."
  },
  {
   "id": "evidence.clean-baseline",
   "revision": 1,
   "status": "REGRESSION-LOCKED",
   "canonical": true,
   "statement": "A perturbation-based result is admissible only if the IDENTICAL verifier, fixture, environment and artifact set satisfy their DECLARED baseline before the perturbation is applied. The word is DECLARED, not silent: each falsifier family names what its own clean state looks like. The negative battery's baseline is grid_check exiting 0 on the unperturbed fixture; the C bridge's is 48/48 byte equality; the kernel's is the canonical certificate and gates matching; a World attack probe's is the honest fixture satisfying the World invariants it is about to attack. Every perturbation harness implements five phases in order: establish_baseline, perturb, assert_perturbation (non-vacuity and target-match), run_subject, assert_specific_diagnostic. POSITIVE gates — kernel, World, bridge — need no additional 'must report nothing' test, because they ARE baseline observations. What needs this invariant is any claim of the form 'I changed X and therefore X caused this failure', which is exactly what a negative case asserts. Between round 14 and round 17 the negative battery's baseline was red and no case was isolated-cause evidence; nothing was falsely green, and that is a different and weaker property than the one the roster was reporting. AND A GATE MUST BE ABLE TO FAIL. A runner that pipes its subject into another command takes the exit status of the PIPE, not of the subject, so a gate whose subject CRASHED prints a stack trace's last line and reports success. Every governance recipe therefore captures its subject's output and status before printing, and the failure is verified in both directions: an unresolvable import and a failing assertion must each fail the target.",
   "evidence": "negative_battery.sh: establish_baseline() runs grid_check on the unperturbed fixture and refuses the whole run if it does not exit 0, printing that no case below is isolated-cause evidence. The baseline is established once because every case builds its fixture by the same recipe from the same source — and that is VERIFIED rather than assumed: each case compares its own pre-perturbation digest against the baselined tree and fails FIXTURE DRIFT otherwise. harness_selftest.sh M-9 keeps the species in the bounded nine. Paired probes satisfy the convention by construction, since their live half IS the baseline and must be confined for the probe to pass. DECLARED OPEN: the one-directional 9D probes (maintainer, coordinator_alias, realm, ownfailopen, closureenv) assert a breach without first asserting that the honest fixture holds the invariants they attack; their baselines are not yet established in code."
  },
  {
   "id": "derivation.serialized-boundary",
   "revision": 1,
   "status": "PROPERTY-TESTED",
   "canonical": false,
   "statement": "A derivation crosses an authority boundary as DATA or not at all. The program is a canonical AST and program_sem_id is H(canonical program), so it cannot be a caller-selected label and cannot be rebound — the id IS the program's hash, and the same program has the same id under every conforming implementation while implementation_id carries executable provenance separately. The message domain is TRVM's canonical value domain, never 'structuredClone succeeded': Function, Map, Set, Date, class instances and transferable handles are refused, because those are capabilities rather than data. Reads are an AUTHORITY operation performed on the authoritative side and passed as explicit grants, so the derivation realm holds no world reference and needs none. A result produced on the far side is a CLAIM; it becomes evidence only when the authority re-derives it and the canonical bytes agree.",
   "evidence": "derive_battery.mjs 10/10 in-process and derive_realm_battery.mjs 5/5 across a real worker_threads boundary. The decisive one is empirical: posting a request carrying a closure throws DataCloneError, so the 9D.4 lexical-cell attack — which no Object.freeze, deepFreeze, canonicalBytes, #private field or GuardedStore could reach — has NO TRANSPORT. The confinement is performed by the boundary rather than by object discipline, which is why replacing the API was the right response to law:derivation.environment-confinement@1 rather than hardening it further. SCOPE, stated rather than implied: this closes derivation-object-confinement only. Determinism of a long-lived evaluator (a worker holding `let counter = 0` leaks no parent authority and still fails to make program_sem_id denote a stable function) and host confinement (Date.now, Math.random, filesystem, network) are separate scopes, unclaimed here.",
   "superseded_by": "derivation.serialized-boundary@2",
   "revision_note": "kept as history, and it is the honest record of an overclaim. Two sentences of this statement were not supported by the mechanism: 'reads are an AUTHORITY operation performed on the authoritative side and passed as explicit grants' described a worker that actually sourced its read table from canonical_inputs, where {op:'input', name:'__reads'} retrieved the whole table with zero tracked reads; and implementation_id was a caller-asserted field that no executor verified and no result carried. Both reproduced (probe_derivegrant_v02_repro.mjs, W-1 and W-2). Revision 2 states what the v0.2.0 mechanism does."
  },
  {
   "id": "derivation.serialized-boundary",
   "revision": 2,
   "status": "PROPERTY-TESTED",
   "canonical": false,
   "supersedes": "derivation.serialized-boundary@1",
   "statement": "A derivation crosses an authority boundary as DATA or not at all. The program is a canonical AST and program_sem_id is H(canonical program), so it cannot be a caller-selected label and cannot be rebound — the id IS the program's hash, and the same program has the same id under every conforming implementation. The message domain is TRVM's canonical value domain, never 'structuredClone succeeded': Function, Map, Set, Date, class instances and transferable handles are refused, because those are capabilities rather than data. The derivation realm holds no world reference and reads ONLY the grant snapshot the authority resolved for it, addressed through read/scope — never through input, which addresses canonical_inputs alone. A result produced on the far side is a CLAIM; it becomes evidence only when the authority validates its footprint against the grant it issued and re-derives the SEMANTIC PROJECTION of the result — every field but implementation_id — to the same canonical bytes.",
   "evidence": "derive_battery.mjs 21/21 in-process and derive_realm_battery.mjs 9/9 across a real worker_threads boundary. The decisive one is still empirical: posting a request carrying a closure throws DataCloneError, so the 9D.4 lexical-cell attack — which no Object.freeze, deepFreeze, canonicalBytes, #private field or GuardedStore could reach — has NO TRANSPORT. v0.2.0 additionally removes the last callable from the derivation path: evaluate() builds its reader from canonical grant data instead of taking a reader parameter, and a pair of reader callables in the grant position is refused as data (grants-schema: [read,scope]). SCOPE, stated rather than implied: this closes derivation-object-confinement only. Determinism of a long-lived evaluator and host confinement (Date.now, Math.random, filesystem, network) are separate scopes, unclaimed here.",
   "superseded_by": "derivation.serialized-boundary@3",
   "revision_note": "kept as history. @2 said program_sem_id 'cannot be a caller-selected label' and that 'the same program has the same id under every conforming implementation' — both true of the SYNTAX and neither established for the SEMANTICS, because the id was H('TRVM-PROGRAM-v1|' + canonical AST) over an unfrozen language. Four behaviours could differ behind one id and all four were reproduced: add was JavaScript '+', bind() validated nothing, arity and field sets were unconstrained, and evaluation order was free while the footprint was an ordered sequence inside the semantic projection. Frozen as C-1..C-4 in probe_coresem_v03_repro.mjs."
  },
  {
   "id": "derivation.serialized-boundary",
   "revision": 3,
   "status": "PROPERTY-TESTED",
   "canonical": true,
   "supersedes": "derivation.serialized-boundary@2",
   "statement": "A derivation crosses an authority boundary as DATA or not at all, and its identity commits the SEMANTICS of the language it is written in. program_sem_id = H('TRVM-PROGRAM-v2' | core_sem_id | canonical AST), where core_sem_id = H(canonical TRVM-DERIVE-CORE specification) — so a caller cannot select an id, an id cannot be rebound, AND an implementation cannot assign different meaning to an operation while agreeing on the id: a different core is a different program. The grammar is validated BEFORE an id is issued, so no identity exists for a program outside the language. The message domain is TRVM's canonical value domain, never 'structuredClone succeeded'. The derivation realm holds no world reference and reads ONLY its grant snapshot, addressed through read/scope and never through input. A result produced on the far side is a CLAIM; it becomes evidence only when the authority validates its footprint against the grant it issued and re-derives the semantic projection — every field but implementation_id and read_trace — to the same canonical bytes.",
   "evidence": "derive_battery.mjs 31/31 in-process and derive_realm_battery.mjs 9/9 across a real worker_threads boundary, plus probe_coresem_v03_repro.mjs 4/4 frozen and 5/5 live. The decisive confinement result is still empirical: posting a request carrying a closure throws DataCloneError, so the 9D.4 lexical-cell attack has NO TRANSPORT. SCOPE: object confinement only. Determinism of a long-lived evaluator and host confinement are separate scopes, unclaimed here."
  },
  {
   "id": "derivation.core-semantics",
   "revision": 1,
   "status": "REGRESSION-LOCKED",
   "canonical": true,
   "statement": "TRVM-DERIVE-CORE-v1 is FROZEN and its identity is content-bound. The record declares the grammar (every node's key set is exactly {op} union the op's declared fields), the value domain, arithmetic (IEEE-754 binary64, no coercion — operands must be numbers and results must be finite, overflow refused AT the operation), the identification of -0 with +0 in the canonical numeric quotient, evaluation order (depth-first, `a` before `b`, DETERMINISTIC so that refusals and traces reproduce but deliberately NOT semantic identity), read_footprint as a canonical DEPENDENCY SET with access order preserved separately in read_trace outside the semantic projection, totality (no recursion, no loop, no general function), and the exact refusal vocabulary. core_sem_id = H(canonical CORE_SPEC) rather than the label 'TRVM-DERIVE-CORE-v1', because a bare name is precisely the caller-selected identity the primitive ruling already refuses for 'componentReachability'. Changing what add means moves core_sem_id and therefore every program_sem_id, which is the property that makes the identity semantic rather than syntactic. A prim extension bumps the core version and every program id with it: a program written against a different language is a different program.",
   "evidence": "probe_coresem_v03_repro.mjs — C-1 (add was JavaScript '+'), C-2 ({op:'exec', cmd:'rm -rf /'} was issued an id), C-3 (const-without-value, add-without-b and add-with-an-extra-field all issued ids), C-4 (the footprint was an ordered sequence, so a right-to-left implementation returned different canonical bytes for a program it computed identically) — 4/4 reproduce against the frozen v0.2.0 copy, 5/5 confined live. derive_battery.mjs: core-id-is-content-bound, program-id-commits-the-core, grammar-refuses-before-id (6 malformed programs), arithmetic-typed-and-total, footprint-is-a-canonical-set, trace-is-outside-the-semantic-projection, footprint-set-is-checked-not-normalized, overflow-refused-on-every-operator, coercion-refused-on-every-operator, signed-zero-identified. BREAKING BY DESIGN: every v0.2.0 program id is retired, done now precisely because no second implementation exists to be broken by it."
  },
  {
   "id": "derivation.execution-evidence",
   "revision": 1,
   "status": "PROPERTY-TESTED",
   "canonical": true,
   "statement": "NON-SEMANTIC DOES NOT MEAN UNVERIFIED. A DeriveResult carries two explicit envelopes with different trust rules. semantic_result (value, witness, support, read_footprint) determines portable meaning and is what cross-implementation validation compares. execution_evidence (implementation_id, read_trace) carries conformance and provenance: it is EXCLUDED from that comparison and NOT excluded from checking. The core fixes evaluation order — depth-first, `a` before `b` — precisely so that refusals and traces reproduce, so a returned trace that disagrees with the authority's own re-derivation is a CONFORMANCE failure of the implementation rather than a disagreement about the program, and it is refused as trace-nonconforming. The two verdicts are reported SEPARATELY — semantic_agreement and trace_conforms — because 'same meaning, different strategy' and 'wrong answer' are different diagnoses. The flat shape was part of the defect: a field sitting beside value and read_footprint reads as authenticated by the same machinery as its neighbours. Later the semantic film supersedes the trace check and lives in this same envelope.",
   "evidence": "probe_traceforge_v06_repro.mjs — T-1: a program reading a then b, with ONLY the trace reversed and the canonical footprint and value untouched, passed validateForeignResult and was accepted with validated + fresh_at_check under v0.5.0. checkResult compared the footprint to the SET of the trace, which a reversal does not change, and the semantic projection excluded the trace — so the one field carrying execution evidence was the one field nothing looked at. 1/1 reproduces against the frozen v0.5.0 validation and 4/4 confined live. derive_battery.mjs: trace-is-outside-the-semantic-projection, plus the envelope schema checks in checkResult."
  },
  {
   "id": "derivation.footprint-freshness",
   "revision": 1,
   "status": "PROPERTY-TESTED",
   "canonical": true,
   "statement": "Containment and freshness are different questions and a protocol needs both. footprintWithinGrant asks a HISTORICAL question — was every claimed read inside the snapshot this derivation received? validateFootprintFresh asks a TEMPORAL one — are those dependencies still current at the moment of acceptance? Both can be satisfied about a World that has moved, so re-derivation against the grant can never detect staleness: executor and authority agree perfectly about an old snapshot. Freshness keys on the FOOTPRINT and never on a global vclock — an unrelated write must not invalidate a derivation that did not depend on it, or the grant/footprint separation is undone from the other side. Exact reads compare versions; scope predicates compare digests, which is the World's phantom-scope case reaching the derivation boundary. ACCEPTANCE DOES NOT ESTABLISH COMMITTABILITY. One call cannot: the World can move between it returning and the caller applying. It establishes `validated` and `fresh_at_check` — an observation at a moment — and the composition that commits belongs to the World: acquire the authoritative lock, accept, deterministic prepared apply with no hostile callback in between, seal the receipt, release. No lock capability is exported to reach that, because rounds 9B-9C are the record of what happens when transaction authority gets passed around.",
   "evidence": "probe_stalegrant_v03_repro.mjs: grant cut at fb@1=5, derived, World moved to fb@2=9 — checkResult PASS, footprintWithinGrant PASS, validateForeignResult PASS, all three CORRECT, and acceptance refuses 'stale-read: fb granted@1 live@2'. Plus the negative half (unrelated-write-ignored) and the scope half (stale-scope: kind:node, a node joining a query with no exact read moving). derive_battery.mjs: freshness-is-not-containment, unrelated-write-does-not-invalidate, acceptance-does-not-claim-committable. derive_realm_battery.mjs: intent-to-acceptance across a real worker."
  },
  {
   "id": "derivation.grant-issuance",
   "revision": 1,
   "status": "PROPERTY-TESTED",
   "canonical": true,
   "statement": "An authority-issued request authenticates THE WHOLE REQUEST, and acceptance takes no proof from its caller. grant_id is a hash of the grant and a hash authenticates content to itself, so it proves integrity and says nothing about issuance; binding request_id to grant_id answers 'was this issued?' about a GRANT while the thing being accepted is a REQUEST. Issuance therefore records request_id -> request_sem_id = H(canonical request), recomputed at acceptance, so any change to any field is a different request rather than the same request with different content. The authority is the only constructor of a DeriveRequest; a caller submits a DeriveIntent and may REQUEST exactly one thing, expected_implementation_id, which is a requirement on the executor rather than authority content — an open options bag spread after the authority's own fields is a caller writing authority content. Acceptance is a METHOD on the authority, closing over its issuance table and its live World reader: a free function taking those as parameters, with the issuer defaulting to absent, lets the caller supply both proofs of its own authority. The issued request is owned through canonicalBytes and deep-frozen as defence in depth, not as the boundary — the binding is the boundary. A signature or MAC is added when, and only when, the grant crosses a real trust boundary, is persisted and replayed later, is delegated between authorities, or must be proved to an independent verifier.",
   "evidence": "probe_issuebind_v05_repro.mjs, 3/3 reproduced against the frozen draft and 4/4 confined live. I-1: swapping canonical_inputs under an untouched request_id and grant_id passed wasIssued, derived 1005 where an honest request derives 5, and was accepted as committable. I-2: authorize(intent, {canonical_inputs:{bias:1000}}) produced an AUTHORITY-ISSUED request evaluating to 1005. I-3: acceptance with the issuer argument OMITTED accepted a wholly self-made request, and a fake liveReader replaying the granted version turned a stale-read refusal back into an acceptance. derive_battery.mjs: issuance-binds-the-whole-request, request-sem-id-recomputes, authorize-options-whitelisted, issued-request-is-owned-and-frozen, intent-schema-closed, authority-requires-a-world."
  },
  {
   "id": "derivation.grant-footprint-separation",
   "revision": 1,
   "status": "PROPERTY-TESTED",
   "canonical": true,
   "statement": "The authority grant and the read footprint are TWO evidence objects and may not be collapsed into one. The grant (read_grants, named by grant_id = H(canonical read_grants)) is a CAPABILITY record: what the authority made available, resolved on the authoritative side, deliberately permitted to be broader than what is read because under data-dependent traversal the needed subset is not knowable in advance. The footprint is the DEPENDENCY record: what the program actually consumed through a tracked read or scope, recorded by the evaluator on access. Freshness, invalidation, replay and support analysis key on the footprint alone — defining it as the grant would over-invalidate every derivation whose grant was wider than its reads, which under snapshot granting is all of them. The authority validates the footprint as a SUBSET of the grant, at the granted versions and scope digests, on its own evidence and BEFORE any re-derivation.",
   "evidence": "derive_battery.mjs: grant-not-reachable-as-input, footprint-is-the-access-subset (a 3-resource grant against a 1-entry footprint), grant-id-binds-the-snapshot (a swapped snapshot under the original grant_id is refused request-grant-id-mismatch), footprint-validated-independently (footprint-ungranted-read / footprint-version-mismatch, both fired on an otherwise honest result), witness-matches-footprint. derive_realm_battery.mjs repeats the input-reachability and forged-footprint cases across a real worker. The v0.1.0 defect is frozen as W-1 in probe_derivegrant_v02_repro.mjs and must keep reproducing there. GRANTING MODEL, decided rather than defaulted: snapshot (A) not read-RPC (B) — deterministic, films cleanly, no cross-realm round trip per primitive. Its cost is least-authority, since the grant may reveal more than the program reads; confidentiality against the derivation realm is the stated trigger to revisit."
  },
  {
   "id": "derivation.implementation-provenance",
   "revision": 1,
   "status": "PROPERTY-TESTED",
   "canonical": true,
   "statement": "Execution identity is ASSERTED BY THE EXECUTOR and may only be REQUIRED by the caller. DeriveResult carries implementation_id, emitted by the evaluator that ran; DeriveRequest carries at most expected_implementation_id, which an executor that cannot satisfy it refuses by name. A caller therefore cannot cause a result to claim an implementation that did not produce it. The field is excluded from the semantic projection that cross-implementation validation compares, which is what lets a C result and a JS result of the same program_sem_id agree while their provenance stays distinguishable — the film_identity_forward_declaration split, made operative. DECLARED OPEN: implementation_id is a declared constant, not a digest of executable bytes, so this closes IMPERSONATION and does not yet establish PROVENANCE — a modified JS worker still emits impl-js-derive-v0.2.0. Binding it to a source/binary digest is the next revision and is named here rather than implied.",
   "evidence": "derive_battery.mjs: implementation-id-asserted, implementation-requirement-refused, implementation-id-well-formed, semantic-projection-is-portable (a result stamped impl-c-derive-v0.2.0 validates and its provenance is reported rather than compared away), implementation-requirement-checked-on-result. derive_realm_battery.mjs: executor-asserts-implementation across the worker boundary, and cross-implementation-shape — which is the SHAPE a real C implementation plugs into and explicitly not a claim that one exists. The v0.1.0 defect is frozen as W-2: a request asserting impl-c-pretend-v9 was executed by the JS evaluator and returned success, with no implementation_id in the result at all."
  }
 ],
 "clean_baseline": {
  "phases": [
   "establish_baseline",
   "perturb",
   "assert_perturbation",
   "run_subject",
   "assert_specific_diagnostic"
  ],
  "declared_baselines": {
   "negative_battery.sh": "grid_check exits 0 on the unperturbed fixture, and each case's pre-perturbation digest equals the baselined tree's — IMPLEMENTED",
   "paired probes (derivegrant, coresem, stalegrant, issuebind, traceforge)": "the live half is confined; a probe fails if either direction is wrong — IMPLEMENTED by construction",
   "one-directional 9D probes": "the honest fixture satisfies the World invariants under attack — DECLARED OPEN, not established in code",
   "bridge_check.mjs": "48/48 byte equality — a POSITIVE gate, itself a baseline observation; needs nothing added",
   "trvm_law_kernel.mjs": "canonical certificate and gates match — a POSITIVE gate; needs nothing added",
   "trvm_world.mjs": "warrant machinery holds and the receipt recomputes — a POSITIVE gate; needs nothing added"
  },
  "why_not_more_meta_cases": "the harness self-test stays BOUNDED at the nine historically observed species. This law is the general principle promoted out of M-9 and applied as a PRECONDITION of every falsifier family, rather than as more meta-cases. Turning nine into fifteen would be the infinite regress the self-test was written to avoid.",
  "historical_note": "pre-round-18 negative results are ANNOTATED, not rewritten. Those batteries did find their requested diagnostics, so they were not false-green; but the verifier was already red, so they were not isolated-cause evidence either. The contamination stays in the record as evidence about the development process. See round-11-ledger.md §77.",
  "gate_must_be_able_to_fail": "`cmd | tail -1` takes tail's exit status. The derive battery ran BROKEN for a full round after the round-19 envelope split — printing a stack trace's last line where its verdict should have been — and make governance stayed green. Every gov- recipe now uses out=$(cmd) && printf ... so the subject's own status is what the recipe fails on. Verified by injecting an unresolvable import (crash) and a false assertion (exit 1): both fail the target. Discovered while assembling a review bundle, not by the gate."
 },
 "derivation_language": {
  "decided": "before the expressiveness round, not during it — the same discipline as film_identity_forward_declaration",
  "core": [
   "const",
   "read",
   "scope",
   "cite",
   "input",
   "add",
   "sub",
   "mul",
   "len"
  ],
  "ruling": "SMALL TOTAL CORE plus NAMED SEMANTIC PRIMITIVES. The core stays small and total. Complex behaviour arrives as {op:'prim', primitive_sem_id, args}, never as if/while/function/closure/recursion/eval. The reason is the one this whole line of work has been establishing: a general programming language at the derivation boundary re-admits the unbounded capability container that law:derivation.environment-confinement@1 was falsified by, in a form that serializes.",
  "primitive_identity": "primitive_sem_id must be content-bound, not a name. H(primitive language/version + canonical input/output contract + semantic specification identity + conformance-vector identity). 'componentReachability' as a bare string would be exactly the caller-selected label the program_sem_id design refuses. program_sem_id contains primitive_sem_id; each implementation of the primitive carries refinement evidence beneath it.",
  "first_primitive": "component reachability, and it is chosen because it is materially harder than arithmetic: graph traversal, data-dependent reads, support, adjacency footprints and the phantom-scope case all appear in it at once. It also has a total semantic definition over a finite canonical grant snapshot — general recursion is not required to express it, which is the property that keeps the core total.",
  "data_dependent_reads": "traversal discovers what to read as it goes (read adj:a -> discover b -> read edge:a|b -> ...), which is precisely why the grant may be broader than the footprint. Under the snapshot model the authority hands over a bounded world slice and the evaluator logs the subset consumed. This is the concrete case law:derivation.grant-footprint-separation@1 exists for.",
  "not_built": "no prim op exists. The core is frozen; the primitive CATALOG is not, and a prim extension bumps the core version and therefore every program id, deliberately.",
  "frozen": "TRVM-DERIVE-CORE-v1 is FROZEN as of round 16 — grammar, value domain, arithmetic, signed zero, evaluation order, footprint-as-set, totality and refusal vocabulary — with a content-bound core_sem_id load-bearing inside every program_sem_id. See law:derivation.core-semantics@1."
 },
 "lowering_spike": {
  "status": "DECLARED, not built.",
  "record_correction": "This section was LOST between drafts. The combined round-16 draft carried it; when that draft was split into rounds 16/17/18 the grid was rebuilt from the round-15 base and this section was not re-added. The round-16/17/18 review brief nonetheless stated that TRVM-TERM-CANON-v1 was 'recorded in lowering_spike', while the machine-readable extract shipped alongside it contained lowering_spike: null. The brief was wrong and the extract was right. Restored here, in round 21, together with the fourth identity the review then supplied.",
  "scope": "the PURE fragment only — const and add first, then input/sub/mul/len. NOT read/scope/cite: authority-sensitive operations carry footprint semantics that would muddy the question the spike exists to answer. If add(const 2, const 3) already gives an ugly lowering, that is valuable information before a compiler is built around the idea.",
  "target_encoding": {
   "name": "TRVM-TERM-CANON-v1",
   "what": "a canonical encoding of the TARGET TERM, before heap allocation — a different object from the runtime heap state that SEMSTATE-CANONICAL-v1 identifies.",
   "why": "it resolves an ordering inversion. 'The same AST lowers to byte-identical target syntax' needs a target NOTATION to be byte-identical in; if that notation were the runtime-state canonicaliser, the spike would depend on the very C work the film round is supposed to deliver. Term identity and runtime-state identity are separate, so the spike does not wait for the film.",
   "caveat": "ic32's existing textual syntax may serve IF it has a proven unique parse/format round trip and canonical variable naming. If not, do not bless pretty-printed text — use a small canonical target AST / prefix serialization."
  },
  "three_properties": [
   "the same Derive AST lowers to byte-identical target-term bytes",
   "JS evaluate(source) and ic32(normalize(target)) decode to the same outcome",
   "the resulting ic32 execution emits and replays an ordinary TRVM transition film"
  ],
  "identities": {
   "chain": "program_sem_id --lowering_id--> target_term_sem_id --native execution film--> target_nf_sem_id --decode_id--> outcome_sem_id",
   "reference_side": "the JS derivation evaluator independently produces outcome_sem_id from program_sem_id + inputs",
   "refinement_obligation": "source_outcome_sem_id == decoded_target_outcome_sem_id",
   "program_sem_id_is_not_replaced": "the lowered term's id must NOT replace program_sem_id. Keeping them distinct is what makes the chain a refinement STATEMENT rather than a renaming.",
   "why_outcome_not_value": "REFUSAL IS ALSO SEMANTICS. An outcome is {status:'value', value} or {status:'refused', reason} content-addressed under TRVM-DERIVE-OUTCOME-v1. A value-only identity cannot state that two implementations agreed about program-arith-non-finite, which is exactly the agreement the frozen core exists to make checkable."
  },
  "layer_separation": "lowering proves source program -> target term; the FILM proves target term -> target normal form transitions; DECODING proves target normal form -> target outcome; the refinement receipt proves source outcome == target outcome. The film must not be asked to prove source-language equivalence — its job is to witness the target machine's execution.",
  "decision_rule": "if the spike is clean, lowering into ic32 is preferred over a second dedicated C interpreter beside it — one execution substrate rather than two. If the mapping is awkward, it is NOT adopted. The point of a spike is that it can fail."
 },
 "film_planes": {
  "why_this_section_exists": "Two different transition systems have started to be discussed in the same words, and the failure mode is specific: finishing C<->JS cross-replay on the tiny derivation AST and then writing 'cross-implementation semantic films complete' while native ic32 still emits none.",
  "trvm_calculus_film": {
   "relation": "semantic pre-state -> (rule + canonical locus) -> semantic post-state",
   "subject": "the ic32 interaction-net rewrite relation, in C / Zig / Mojo / WASM",
   "contract": "docs/spec/conformance §10 / §10.5; SEMSTATE-CANONICAL-v1",
   "status": "canonical bytes agree C<->JS at 48/48 (bridge_check). NO native runtime emits films yet.",
   "this_is_the_pack_v3_gap": "handoff milestones 5, 9, 10, 11 — canonical serialization, films, cross-replay, refinement receipts"
  },
  "derivation_evidence": {
   "relation": "DeriveRequest -> evaluate program -> DeriveResult",
   "subject": "the derivation AST protocol of derive_protocol.mjs",
   "contract": "law:derivation.serialized-boundary@3 + law:derivation.grant-footprint-separation@1",
   "status": "JS executor only; the cross-implementation SHAPE is tested, no second implementation exists"
  },
  "ruling": "The native ic32 semantic-film round is NOT gated on the derivation language, and porting the derivation AST to C would be a SECOND cross-implementation theorem rather than a discharge of the first. They converge only if derivation programs are eventually LOWERED into TRVM terms — DeriveProgram AST -> canonical lowering -> interaction-net term -> ic32 -> semantic film — which would make one execution substrate out of two runtimes and is the reason not to build so much dedicated derivation-interpreter machinery that the option closes. Not adopted this round; recorded so it stays reachable."
 },
 "realm_roadmap": {
  "decision": "Realm separation moves AHEAD of the C semantic-film round. The criterion was stated in advance — a fourth ownership variant means the object-discipline surface is too large to enumerate — and it was met by probe_closureenv_repro.mjs.",
  "not_a_failure_of_0_11_0": "ordinary object ownership was pushed far enough that the remaining counterexample is no longer a forgotten freeze; it is a lexical cell, which no object discipline reaches.",
  "message_domain": "the realm boundary accepts ONLY TRVM's canonical value domain — null, boolean, finite number, string, canonical arrays, canonical plain objects — plus explicitly specified tagged extensions later. Function, Map, Set, Date, SharedArrayBuffer, MessagePort, class instances and transferable handles are REFUSED. 'structuredClone succeeded' must never become the definition of authority-safe: the Map witness of 9D.3 already proved structuredClone and JSON.stringify disagree about what a value is. If it cannot be represented in the canonical request language, it cannot accidentally become derivation authority.",
  "program_identity_binding": "program_sem_id may NOT be a caller-selected label, or evilClosure simply becomes {\"program_sem_id\":\"honest-program\"} while arbitrary code runs. It must be an immutable binding — H(canonical semantic program representation), or a registry entry whose rebinding is itself an authority-bearing operation — with per-implementation refinement evidence beneath it.",
  "three_separate_scopes": [
   "derivation-object-confinement — a worker isolate can close this: no parent World, Maintainer, closure cell, Map or function object crosses a serialization boundary",
   "derivation-determinism — a persistent worker holding `let counter = 0` leaks no parent authority yet program_sem_id=P still fails to denote a stable function. Nondeterministic inputs must be impossible, reset between derivations, or committed explicitly in the film",
   "derivation-host-confinement — Date.now, Math.random, worker globals, env, filesystem, network. Needs an OS-level sandbox; a worker isolate does not reach it"
  ],
  "convergence": "realm separation and transition portability are ONE round, not two. A derivation that must name a program instead of shipping a closure is already most of what a film needs to identify a step, so the first target is one tiny deterministic program with a JS and a C implementation, proving JS-film -> C-checker accepts and C-film -> JS-checker accepts. That closes closure authority, program-semantic identity, cross-realm execution, cross-implementation transition semantics and the film gap together.",
  "order": [
   "freeze the lexical-cell witness (done)",
   "record same-realm closure ownership as a declared boundary failure, not a patch target (done)",
   "artifact-root resolver + manifest-driven falsifiers + the open instrument-nonvacuity clauses (done, round 14)",
   "DeriveRequest/DeriveResult canonical schemas (done, round 14)",
   "immutable program_sem_id binding (done, round 14)",
   "move one derivation across a worker boundary with no callable crossing (done, round 14)",
   "separate the authority grant from the observed read footprint; make implementation_id executor-asserted (done, round 15)",
   "native ic32 semantic-film emission against the existing §10/§10.5 contract, starting with C — NOT gated on the derivation language, see film_planes",
   "cross-replay: ic32 C film -> JS kernel, JS film -> C checker",
   "the first named semantic primitive (component reachability), per derivation_language",
   "bind implementation_id to executable bytes rather than a declared constant",
   "root release identity",
   "physical governance subdivision",
   "Zig/Mojo/WASM",
   "worker object confinement strengthened to host/process confinement"
  ],
  "sequencing_correction": "The previous order read 'that same program as the first C<->JS film / cross-replay witness', which conflated the two transition systems now separated in film_planes. Cross-replay of the DERIVATION AST is a different theorem from cross-replay of the ic32 REWRITE RELATION, and the pack-v3 film gap is the latter. The film round proceeds on the existing conformance contract and does not wait for the derivation language to grow."
 },
 "changelog_from_1_19_0": [
  "new law derivation.execution-evidence@1. Round 16 correctly moved read_trace out of semantic identity; v0.5.0 then checked nothing about it, and a REVERSED trace with an untouched footprint and value validated and was accepted. Frozen as T-1.",
  "DeriveResult is now two explicit envelopes — semantic_result and execution_evidence — so the trust status of a field is visible in the shape rather than only in a comment.",
  "validateTraceConformance compares the foreign trace against the authority's own re-derivation and refuses trace-nonconforming; semantic_agreement and trace_conforms are reported separately.",
  "the ruling that access order is not semantic identity is UNCHANGED. What changed is that being outside the semantic projection is no longer the same as being unchecked."
 ],
 "changelog_from_1_20_0": [
  "new law evidence.clean-baseline@1, promoted out of M-9: a perturbation-based result is admissible only if the identical verifier, fixture, environment and artifact set satisfy their DECLARED baseline first.",
  "negative_battery.sh implements the five phases; the baseline is established once and each case proves its own fixture is the baselined one (FIXTURE DRIFT otherwise).",
  "the harness self-test stays bounded at nine. The general principle is a precondition of every falsifier family rather than more meta-cases.",
  "declared open and named: the one-directional 9D probes do not yet establish their baselines in code.",
  "positive gates are themselves baseline observations and need nothing added — the invariant is for claims of the form 'I changed X, therefore X caused this'."
 ],
 "changelog_from_1_21_0": [
  "evidence.clean-baseline@1 gains its runner half: a gate must be able to fail. `cmd | tail -1` takes the PIPE's exit status, so a crashing subject reported success — the derive battery ran broken for a full round after the envelope split and make governance stayed green.",
  "all 13 governance recipe lines capture output and status before printing; verified to fail on both an unresolvable import and a false assertion.",
  "the first crash test written for this was itself vacuous — a throw appended AFTER process.exit, which never runs. Recorded because it is the same species the harness self-test exists for.",
  "lowering_spike RESTORED after being lost in the round-16 split, with TRVM-TERM-CANON-v1, the three properties, the decision rule, and the fourth identity (outcome_sem_id under TRVM-DERIVE-OUTCOME-v1, because refusal is also semantics). The round-16/17/18 review brief claimed this section was recorded while the extract shipped beside it read null."
 ],
 "artifact_versions": {
  "trvm_law_kernel.mjs": "1.1.0",
  "trvm_world.mjs": "0.12.0",
  "derive_protocol.mjs": "0.6.0"
 }
}
```

## `record/artifacts-derivation-boundary.json`

```json
{
 "derivation_boundary": {
  "status": "v0.6.0 — protocol proven in-process and across a worker; NOT yet the production derivation path",
  "files": {
   "derive_protocol.mjs": "program-as-data over a FROZEN core, canonical request/result schemas, authority grants separated from the observed read footprint, live-footprint freshness, and a DerivationAuthority that is the only constructor of a request and the only holder of acceptance",
   "derive_battery.mjs": "40 falsifiers, in-process",
   "derive_worker.mjs": "the far side; holds no parent reference, resolves programs from its own registry, reads only its grant snapshot, and asserts its own implementation_id",
   "derive_realm_battery.mjs": "10 falsifiers across a real worker boundary",
   "probe_derivegrant_v02_repro.mjs": "the two v0.1.0 defects, frozen — and the same witnesses run against live, which is what makes it a gate rather than a document",
   "probe_coresem_v03_repro.mjs": "the four semantic gaps behind one program_sem_id, frozen at v0.2.0",
   "probe_stalegrant_v03_repro.mjs": "every check passing on a result the World has moved past",
   "probe_issuebind_v05_repro.mjs": "issuance bound to the grant instead of the request, frozen",
   "probe_traceforge_v06_repro.mjs": "a forged execution trace accepted as evidence, frozen"
  },
  "two_evidence_objects": {
   "read_grants + grant_id": "the AUTHORITY GRANT — what the authority made available. A capability record, deliberately allowed to be broader than what is read, because under data-dependent traversal the authority cannot know the needed subset in advance. grant_id = H(canonical read_grants) binds the snapshot so it cannot be edited in flight.",
   "read_footprint": "the OBSERVED DEPENDENCY RECORD — what the program actually consumed through a tracked read or scope. Freshness, invalidation, replay and support analysis key on THIS. Defining it as the grant would over-invalidate every derivation whose grant was wider than its reads, which under snapshot granting is all of them.",
   "why_separate": "v0.1.0's prose said the footprint was 'the authority's record of what it read on the derivation's behalf'. That was two errors at once: it described a collapse that would break freshness, and the mechanism did not even implement the collapse — the worker sourced its read table from canonical_inputs, and {op:'input', name:'__reads'} returned the whole table with zero tracked reads."
  },
  "granting_model": "SNAPSHOT (model A): the authority resolves a bounded canonical world slice once, and both the executor and the re-deriving authority evaluate against those same bytes. Chosen over read-RPC (model B) because it is deterministic, films cleanly, and does not turn every primitive evaluation into a cross-realm round trip. The cost is least-authority: the grant may reveal more than the program reads. Confidentiality against the derivation realm is the trigger to revisit, and it is named here rather than discovered later.",
  "claimed": "OBJECT authority does not cross: structured cloning refuses callables (DataCloneError), the worker resolves program_sem_id against its own registry, it can read only the grant snapshot the authority resolved, the returned footprint is validated as a SUBSET of that grant on the authority's own evidence before any re-derivation, the executor asserts implementation_id and the caller may only state a requirement against it, and a returned result is re-derived by the authority — on the semantic projection, so a conforming foreign implementation can agree — before it is evidence.",
  "not_claimed": "determinism of a long-lived evaluator; host confinement; that any existing measureFn has been ported; that implementation_id is bound to executable BYTES (it is a declared constant, so impersonation is closed and provenance is not — the trusted-launcher measurement is declared and not built); that the World's lock composition around acceptance has been BUILT (it is specified and the caller's obligation is stated, not enforced); and that any lowering into TRVM terms has been attempted.",
  "frozen_core": "TRVM-DERIVE-CORE-v1. program_sem_id = H('TRVM-PROGRAM-v2' | core_sem_id | canonical AST) where core_sem_id = H(canonical CORE_SPEC), so the id commits SEMANTICS and not only syntax. v0.2.0 hashed the AST alone while the record said the language was deliberately not frozen — the two cannot both be true, and four behaviours could differ behind one id. Every v0.2.0 program id is retired.",
  "footprint_is_a_set": "read_footprint is a canonical DEPENDENCY SET, sorted and deduplicated; access order with repeats lives in read_trace, which is excluded from the semantic projection alongside implementation_id. Depending on {a,b} must not become a different identity because one implementation visited a then b — execution strategy does not silently become semantics, the same principle that keeps ref_interactions out of conformance identity. The core still FIXES evaluation order so refusals and traces reproduce.",
  "three_questions": {
   "containment": "footprintWithinGrant — was every claimed read inside the snapshot this derivation received? HISTORICAL.",
   "agreement": "validateForeignResult — does the semantic projection re-derive to the same canonical bytes? Also historical: it evaluates against the same snapshot.",
   "freshness": "validateFootprintFresh — are those dependencies still current NOW? TEMPORAL, keyed on the footprint and never on a global vclock. All three are required; the first two can pass about a World that has moved."
  },
  "issuance": "An authority-issued request authenticates THE WHOLE REQUEST: issuance records request_id -> request_sem_id = H(canonical request), recomputed at acceptance. grant_id proves integrity only — a hash authenticates content to itself. The authority is the only constructor of a request, exactly one option (expected_implementation_id) may be requested, and acceptance is a METHOD closing over the issuance table and the live reader so no proof can arrive as an argument. A signature is added when the grant crosses a real trust boundary, is persisted and replayed, is delegated, or must be proved to an independent verifier.",
  "acceptance_is_not_commitment": "accept() returns {validated, fresh_at_check} and NOT committable. One call cannot establish committability: the World can move between it returning and the caller applying. The composition that commits belongs to the World — acquire the authoritative lock, accept, deterministic prepared apply with no hostile callback in between, seal the receipt, release — and no lock capability is exported to reach it.",
  "two_envelopes": {
   "semantic_result": "value · witness · support · read_footprint. Determines portable meaning; this is what cross-implementation validation compares.",
   "execution_evidence": "implementation_id · read_trace. Conformance and provenance. EXCLUDED from the comparison and NOT excluded from checking — the core fixes evaluation order, so a disagreeing trace is a conformance failure of the implementation. The semantic film will live here.",
   "why": "v0.5.0 kept read_trace as a sibling of value and read_footprint, excluded it from the projection, and checked nothing about it: a reversed trace validated and was accepted. Non-semantic does not mean unverified, and a flat shape made the exclusion read as permission."
  }
 },
 "probe_roles": {
  "probe_semid.mjs": "round 6 — semantic state identity",
  "probe_cert.mjs": "round 5 — scheduler certificate",
  "probe_worldalias_v02_repro.mjs": "round 8 — world aliasing",
  "probe_support_v03_repro.mjs": "round 8.2 — support soundness",
  "probe_sembudget_v1_repro.mjs": "round 6B — semantic film budget",
  "probe_forkescape_v05_repro.mjs": "9B — the fork was not a boundary",
  "probe_keytheft_v06_repro.mjs": "9C — the hidden key was not hidden",
  "probe_maintainer_9d_repro.mjs": "9D — the coordinator was not sealed",
  "probe_coordinator_alias_9d1_repro.mjs": "9D.1 — reachable aliases",
  "probe_realm_9d2_repro.mjs": "9D.2 — nested values, and the shared realm",
  "probe_ownfailopen_9d3_repro.mjs": "9D.3 — ownership failed open",
  "probe_closureenv_repro.mjs": "9D.4 — the authority that was never an object; DECLARED, not repaired",
  "probe_derivegrant_v02_repro.mjs": "DERIVE-v0.2 — the bypassable read footprint and the unverified implementation_id, frozen against v0.1.0 and CONFINED against live; the only PAIRED probe, and it gates",
  "probe_coresem_v03_repro.mjs": "DERIVE-CORE-v1 — program_sem_id bound syntax and claimed semantics: add was JavaScript '+', bind() validated nothing, arity was unconstrained, and the footprint's ORDER was inside the semantic projection. Frozen against v0.2.0, CONFINED against live; PAIRED, and it gates",
  "probe_stalegrant_v03_repro.mjs": "ROUND 17 — the GAP witness: containment, re-derivation and schema all pass on a result whose World has moved. Not a regression repro; there was no freshness check at all before it",
  "probe_issuebind_v05_repro.mjs": "ROUND 17 — issuance authenticated the grant rather than the request, an options bag let a caller write authority content, and acceptance took both of its proofs from its caller. Frozen against the draft, CONFINED against live; PAIRED, and it gates",
  "probe_traceforge_v06_repro.mjs": "ROUND 19 — read_trace was outside the semantic projection and therefore unchecked: a reversed trace validated and was accepted. Frozen against v0.5.0, CONFINED against live; PAIRED, and it gates"
 }
}
```

## `record/negative_battery.sh`

```bash
#!/bin/bash
# Round-5 negative battery: 4 cert-layer forgeries (engine-free) + 7 registry/
# phrase/citation regressions (the six round-4 cases, with ref_coherent now
# tested at BOTH its targets — grid kernel_evidence and certificate evidence).
# Runs against the artifact set in this script's own directory; every case
# must make grid_check exit nonzero with the expected diagnostic.
# Each case: scratch copy of the full tree, one forgery, grid_check MUST exit nonzero
# with a reason matching the expected pattern.
BASE="$(cd "$(dirname "$0")" && pwd)"
# Scratch root for every case. This was previously spelled out in run_case and
# left UNSET in run_case_engine, so the one engine-mode case tried to mkdir at
# the filesystem root and could never execute in a clean shell — it reported
# FAIL for want of an out.txt while the forgery it targets was being refused
# correctly all along. Named once, defaulted, and asserted per case below.
SCRATCH="${SCRATCH:-/tmp/neg5}"
# The case input set is DECLARED in artifacts.json, not hand-maintained here.
# Both runners use the same list: run_case_engine previously omitted
# maintenance_receipt.json for no stated reason, which is exactly the kind of
# silent divergence between two copies of a list that this replaces.
# case_inputs AND tools: grid_check requires every DECLARED artifact to exist,
# so a case tree carrying only case_inputs made the checker report four
# unrelated failures before any forgery was applied. Every case then found its
# expected diagnostic among noise, and an unperturbed tree did not pass — which
# is a contaminated instrument, not a passing one. Since round 14. Found by
# adding a case whose expected pattern did not match and reading what else was
# in the output.
CASE_INPUTS=$(python3 -c "
import json,re,os
m=json.load(open('$BASE/artifacts.json'))
fs=list(m['case_inputs']) + list(m.get('tools', []))
fs+=sorted(f for f in os.listdir('$BASE') if re.match(m['ledgers_pattern'],f))
print(' '.join(fs))")
# law:evidence.instrument-nonvacuity@1 — the mechanised half.
# A per-file digest, not a whole-tree one: "something changed" is weaker than
# "the intended target changed", and the law says target. changed_files() names
# what the perturbation actually moved, so a case that edits the wrong artifact
# is as visible as one that edits nothing.
file_digests () { ( cd "$1" && for f in *; do [ -f "$f" ] && printf "%s %s\n" "$(sha256sum "$f" | cut -d" " -f1)" "$f"; done | sort ); }
# Symmetric difference, not one-sided: a case that DELETES an artifact removes a
# line from the "after" set, which a one-sided comm cannot see. The first draft
# used comm -13 and duly reported refine-receipt-missing — a case that deletes
# refinement_receipt.json — as VACUOUS. The non-vacuity detector's own first
# defect was a vacuity blind spot, found by running it. Recorded rather than
# quietly fixed, because that is the law's whole point.
changed_files () { { printf "%s\n" "$1"; printf "%s\n" "$2"; } | sort | uniq -u | awk "{print \$2}" | sort -u | tr "\n" "," | sed "s/,$//"; }

# law:evidence.instrument-nonvacuity@1 clause 1 — the INTENDED target.
# "Something changed" is weaker than "the intended thing changed". The target is
# derived from the perturbation script itself (files opened for writing, files
# removed) and compared against what actually moved, so a case that edits the
# wrong artifact — or edits an extra one by accident — fails as loudly as one
# that edits nothing. Declaration and effect are checked against each other
# rather than either being trusted alone.
intended_targets () { python3 -c "
import re,sys
py = sys.argv[1]
t  = set(re.findall(r\"open\\(['\\\"]([^'\\\"]+)['\\\"]\\s*,\\s*['\\\"]w\", py))
t |= set(re.findall(r\"os\\.remove\\(['\\\"]([^'\\\"]+)\", py))
print(','.join(sorted(t)))" "$1"; }

# law:evidence.clean-baseline@1 — the phase this runner did not have.
# A perturbation-based result is admissible only if the IDENTICAL verifier,
# fixture, environment and artifact set satisfy their DECLARED baseline before
# the perturbation is applied. This runner's declared baseline is: grid_check
# exits 0 on the unperturbed fixture. Between round 14 and round 17 it did not,
# and every case found its diagnostic among four unrelated failures — nothing
# was falsely green, but no case was isolated-cause evidence either.
#
# The baseline is established ONCE, because every case builds its fixture from
# the same source by the same recipe. That is verified rather than assumed: each
# case compares its own pre-perturbation digest against the baselined tree, so a
# fixture that drifts is a FIXTURE DRIFT failure rather than a silent difference.
BASELINE_DIGEST=""
establish_baseline () {
  local d=$SCRATCH/__baseline
  rm -rf "$d" && mkdir -p "$d"
  for f in $CASE_INPUTS; do cp "$BASE/$f" "$d/"; done
  local out; out=$(cd "$d" && node grid_check.mjs 2>&1); local code=$?
  if [ $code -ne 0 ]; then
    echo "FAIL  BASELINE (the unperturbed fixture does not pass; no case below is isolated-cause evidence)"
    echo "$out" | grep -E "^ -" | head -6 | sed "s/^/        /"
    FAILED=1; return 1
  fi
  BASELINE_DIGEST=$(file_digests "$d")
  echo "BASELINE  grid_check exits 0 on the unperturbed fixture ($(echo "$BASELINE_DIGEST" | wc -l) artifacts)"
}

run_case () {  # name, expected-grep, setup-script(python)
  local name="$1" want="$2" py="$3"
  local d=$SCRATCH/$name
  rm -rf "$d" && mkdir -p "$d"
  for f in $CASE_INPUTS; do cp "$BASE/$f" "$d/"; done
  # law:evidence.instrument-nonvacuity@1 — a forgery that forges NOTHING is
  # vacuous, and a vacuous falsifier is worse than an absent one because the
  # roster still counts it. Six apparatus failures across four rounds would each
  # have been caught here; the hard-coded "1.0.2" replacement is the exact shape.
  local pre; pre=$(file_digests "$d")
  # PHASE 1 of law:evidence.clean-baseline@1 — this case's fixture must BE the
  # one that was baselined, not merely one built by the same recipe
  CASES=$((CASES+1))
  if [ -n "$BASELINE_DIGEST" ] && [ "$pre" != "$BASELINE_DIGEST" ]; then
    echo "FAIL  $name (FIXTURE DRIFT — this case's tree differs from the baselined one)"; FAILED=1; return
  fi
  ( cd "$d" && python3 -c "$py" )
  local post; post=$(file_digests "$d")
  local touched; touched=$(changed_files "$pre" "$post")
  if [ -z "$touched" ]; then
    echo "FAIL  $name (VACUOUS — the forgery changed no artifact; nothing was tested)"; FAILED=1; return
  fi
  local intended; intended=$(intended_targets "$py")
  if [ -n "$intended" ] && [ "$intended" != "$touched" ]; then
    echo "FAIL  $name (TARGET MISMATCH — script intends [$intended], run changed [$touched])"; FAILED=1; return
  fi
  local out; out=$(cd "$d" && node grid_check.mjs 2>&1); local code=$?
  if [ $code -ne 0 ] && echo "$out" | grep -qE "$want"; then
    CAUGHT=$((CAUGHT+1))
    echo "PASS  $name [$touched] → $(echo "$out" | grep -m1 -E "$want" | sed 's/^ *//' | cut -c1-96)"
  else
    echo "FAIL  $name (exit=$code; wanted /$want/)"; echo "$out" | head -5; FAILED=1
  fi
}
FAILED=0
CASES=0; CAUGHT=0
establish_baseline || exit 1

RESEAL='
import json, hashlib
def committed_view(c):
    return [["type",c["type"]],["version",c["version"]],["representation",c["representation"]],
     ["plane_profile",{"INTERACT":list(c["plane_profile"]["INTERACT"]),"COLLAPSE_GATED":list(c["plane_profile"]["COLLAPSE_GATED"])}],
     ["quiescence_criterion",c["quiescence_criterion"]],
     ["strategy",{"kind":c["strategy"]["kind"],"schedulers":list(c["strategy"]["schedulers"])}],
     ["budget",c["budget"]],["corpus",{"id":c["corpus"]["id"],"sha256":c["corpus"]["sha256"]}],
     ["claims",list(c["claims"])],["law_refs",list(c["law_refs"])],
     ["run_manifest_hash",c["run_manifest_hash"]],
     ["exhibit_film_ids",list(c["exhibit_film_ids"])]]
def js(o):  # JSON.stringify-compatible: no spaces, keys in insertion order
    return json.dumps(o, separators=(",",":"), ensure_ascii=False)
def reseal(c):
    c["run_manifest_hash"] = hashlib.sha256(js(c["run_manifest"]).encode()).hexdigest()
    c["exhibit_film_ids"] = [e["film"]["film_id"] for e in c["exhibit_films"]]
    c["cert_id"] = hashlib.sha256(("TRVM-SCHEDCERT-v2|"+js(committed_view(c))).encode()).hexdigest()
c = json.load(open("scheduler_certificate.json"))
'

# ── A. cert-layer forgeries (engine-free detection required) ──────────────
run_case hollow-resealed "cert|receipt|runs|evidence" "$RESEAL
c['run_manifest']=[]; c['exhibit_films']=[]
c['evidence']={'schedulers':4,'terms':24,'runs':999999,'completed':999999,'nf_matched':999999,'readback_pure':999999,'max_steps':1}
reseal(c); json.dump(c, open('scheduler_certificate.json','w'), indent=1)"

run_case inflation-resealed "evidence|aggregate" "$RESEAL
c['evidence']=dict(c['evidence']); c['evidence']['runs']=9600; c['evidence']['completed']=9600
reseal(c); json.dump(c, open('scheduler_certificate.json','w'), indent=1)"

run_case profile-broadened-resealed "profile" "$RESEAL
c['plane_profile']['INTERACT'] = list(c['plane_profile']['INTERACT']) + ['RULE-OF-COOL']
reseal(c); json.dump(c, open('scheduler_certificate.json','w'), indent=1)"

run_case receipt-tamper-unsealed "manifest|cert_id|cert-id" "
import json
c = json.load(open('scheduler_certificate.json'))
c['run_manifest'][0]['steps'] = 12345
json.dump(c, open('scheduler_certificate.json','w'), indent=1)"

# ── B. round-4 regression negatives ───────────────────────────────────────
run_case stale-citation "non-canonical" "
s = open('kappa_witnesses.mjs').read()
open('kappa_witnesses.mjs','w').write(s + '\n// fresh claim per law:sched.certificate@1\n')"

run_case banned-phrase "banned phrase" "
s = open('trvm_law_kernel.mjs').read()
open('trvm_law_kernel.mjs','w').write(s + '\n// the CALM property that licenses this optimization\n')"

run_case unknown-citation "unknown law|unresolved" "
s = open('trvm_law_kernel.mjs').read()
open('trvm_law_kernel.mjs','w').write(s + '\n// justified by law:total.nonsense@9\n')"

run_case double-canonical "canonical" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id']=='sched.certificate' and e['revision']==1: e['canonical']=True
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case ref-coherent-key-grid "ref_coherent" "
import json
g = json.load(open('invariant-grid.json'))
g['kernel_evidence']['ref_coherent'] = True
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case ref-coherent-key-cert "honest keys|ref_coherent" "$RESEAL
c['evidence'] = {('ref_coherent' if k=='readback_pure' else k): v for k, v in c['evidence'].items()}
json.dump(c, open('scheduler_certificate.json','w'), indent=1)"

run_case flagship-drift "flagship" "
import json
g = json.load(open('invariant-grid.json'))
g['flagship_pair']['law_ref'] = 'law:kappa.internal-edge.monotonicity@3'
json.dump(g, open('invariant-grid.json','w'), indent=1)"


run_case_engine() {  # like run_case but the verifier is the WORLD ENGINE mode
  local name="$1" want="$2" py="$3"
  local d="$SCRATCH/$name"
  rm -rf "$d" && mkdir -p "$d" || { echo "FAIL  $name (scratch unusable: $d)"; CASES=$((CASES+1)); FAILED=1; return; }
  for f in $CASE_INPUTS; do cp "$BASE/$f" "$d/"; done
  local pre; pre=$(file_digests "$d")
  # PHASE 1 of law:evidence.clean-baseline@1 — this case's fixture must BE the
  # one that was baselined, not merely one built by the same recipe
  CASES=$((CASES+1))
  if [ -n "$BASELINE_DIGEST" ] && [ "$pre" != "$BASELINE_DIGEST" ]; then
    echo "FAIL  $name (FIXTURE DRIFT — this case's tree differs from the baselined one)"; FAILED=1; return
  fi
  ( cd "$d" && python3 -c "$py" )
  local post; post=$(file_digests "$d")
  local touched; touched=$(changed_files "$pre" "$post")
  # the counter lives in the baseline phase now; incrementing here too made the
  # engine case count twice and the printed total read 101 where it was 100.
  # Caught because the number moved when nothing about the case set had.
  if [ -z "$touched" ]; then
    echo "FAIL  $name (VACUOUS — the forgery changed no artifact; nothing was tested)"; FAILED=1; return
  fi
  local intended; intended=$(intended_targets "$py")
  if [ -n "$intended" ] && [ "$intended" != "$touched" ]; then
    echo "FAIL  $name (TARGET MISMATCH — script intends [$intended], run changed [$touched])"; FAILED=1; return
  fi
  ( cd "$d" && node trvm_world.mjs --check-receipt > out.txt 2>&1 )
  local code=$?
  local msg=$(grep -aoE "$want" "$d/out.txt" | head -1)
  if [ $code -ne 0 ] && [ -n "$msg" ]; then
    CAUGHT=$((CAUGHT+1))
    echo "PASS  $name [$touched] → engine: $msg"
  else
    echo "FAIL  $name (engine exit=$code; wanted /$want/)"; FAILED=1
  fi
}

# ── C. round-6 forgeries: identity lockstep + refinement receipt ──────────
RESEAL_RR='
import json, hashlib
def js(o): return json.dumps(o, separators=(",",":"), ensure_ascii=False)
r = json.load(open("refinement_receipt.json"))
def reseal():
    r["receipt_id"] = hashlib.sha256(("TRVM-REFINE-v1|"+js(r["per_term"])+"|"+js(r["summary"])).encode()).hexdigest()
'

run_case version-lockstep-grid "not the head of the declared lineage|KERNEL_VERSION" "
import json
g = json.load(open('invariant-grid.json'))
g['version'] = '0.9'; g['law_registry']['grid_version'] = '0.9'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case version-lockstep-kernel "KERNEL_VERSION|header does not carry" "
s = open('trvm_law_kernel.mjs').read()
import re
s2 = re.sub(r'const KERNEL_VERSION = \"[^\"]+\";', 'const KERNEL_VERSION = \"0.6\";', s, count=1)
assert s2 != s, 'version-lockstep-kernel forged nothing — the KERNEL_VERSION pattern no longer matches'
open('trvm_law_kernel.mjs','w').write(s2)"

run_case refine-tamper-unsealed "receipt_id does not recompute" "$RESEAL_RR
r['per_term'][0]['steps'] = 777
json.dump(r, open('refinement_receipt.json','w'), indent=1)"

run_case refine-inflation-resealed "does not recompute from per_term" "$RESEAL_RR
r['summary']['sem_chains_equal'] = 25
reseal()
json.dump(r, open('refinement_receipt.json','w'), indent=1)"

run_case refine-lawref-swap-resealed "law_refs" "$RESEAL_RR
r['law_refs'][0] = 'law:sched.free.float@1'
reseal()
json.dump(r, open('refinement_receipt.json','w'), indent=1)"

run_case refine-chainflag-resealed "sem_chains_equal does not recompute|partition" "$RESEAL_RR
r['per_term'][3]['sem_chain_equal'] = False
reseal()
json.dump(r, open('refinement_receipt.json','w'), indent=1)"

run_case refine-receipt-missing "refinement_receipt.json missing" "
import os; os.remove('refinement_receipt.json')"

run_case semid-canonical-corrupt "canonical|non-canonical" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id']=='state.semantic-quotient': e['canonical']=False
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case sem-refusal-dropped "19 replay refusals" "
import json
g = json.load(open('invariant-grid.json'))
g['semantic_film']['replay_refusals'].remove('sem-locus-not-enabled')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case budget-refusal-dropped "19 replay refusals" "
import json
g = json.load(open('invariant-grid.json'))
g['semantic_film']['replay_refusals'].remove('sem-budget-mismatch')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case terminal-witness-schema-dropped "terminal_fields must declare" "
import json
g = json.load(open('invariant-grid.json'))
g['semantic_film']['terminal_fields'] = [f for f in g['semantic_film']['terminal_fields'] if not f.startswith('budget')]
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case world-version-map-drift "declares .* but artifact_versions says|artifact_versions missing" "
import json
g = json.load(open('invariant-grid.json'))
g['artifact_versions']['trvm_world.mjs'] = '9.9.9'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case world-warrant-value-flip-resealed "warrant_id does not recompute|receipt_id does not recompute" "
import json, hashlib
def js(o): return json.dumps(o, separators=(',',':'), ensure_ascii=False)
r = json.load(open('world_warrant_receipt.json'))
r['warrant']['value'] = 99
r['receipt_id'] = hashlib.sha256(('TRVM-WORLDRECEIPT-v1|'+js(r['warrant'])+'|'+r['footprint_id']).encode()).hexdigest()
json.dump(r, open('world_warrant_receipt.json','w'), indent=1)"

run_case world-footprint-prune-in-receipt "footprint_id does not recompute|warrant_id does not recompute|support is not a subset" "
import json
r = json.load(open('world_warrant_receipt.json'))
r['warrant']['read_footprint']['exact'] = r['warrant']['read_footprint']['exact'][1:]
json.dump(r, open('world_warrant_receipt.json','w'), indent=1)"

run_case world-refusal-dropped "10 replay refusals" "
import json
g = json.load(open('invariant-grid.json'))
g['warrant']['executable']['replay_refusals'].remove('undeclared-read')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case composite-pairing-pruned "without its paired warrant-fresh scope|footprint_id does not recompute|warrant_id does not recompute" "
import json
r = json.load(open('world_warrant_receipt.json'))
c = r['composite']['warrant']['read_footprint']
c['predicates'] = [p for p in c['predicates'] if not p[0].startswith('warrant-fresh:')]
json.dump(r, open('world_warrant_receipt.json','w'), indent=1)"

run_case composite-value-flip-resealed "composite warrant_id does not recompute|receipt_id does not recompute" "
import json
r = json.load(open('world_warrant_receipt.json'))
r['composite']['warrant']['value'] = 12345
json.dump(r, open('world_warrant_receipt.json','w'), indent=1)"

run_case composite-stale-at-emit "composite must be emitted fresh|receipt_id does not recompute" "
import json
r = json.load(open('world_warrant_receipt.json'))
r['composite_freshness_at_emit'] = {'verdict': 'scope_dirty', 'witness': {'scope': 'x', 'was': 'a', 'now': 'b'}}
json.dump(r, open('world_warrant_receipt.json','w'), indent=1)"

run_case canonical-domain-declaration-dropped "canonical_value_domain or deletions" "
import json
g = json.load(open('invariant-grid.json'))
del g['world']['canonical_value_domain']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case write-mediated-law-corrupt "canonical|non-canonical" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id']=='world.write-mediated': e['canonical']=False
json.dump(g, open('invariant-grid.json','w'), indent=1)"

RESEAL_WR='
import json, hashlib
def js(o): return json.dumps(o, separators=(",",":"), ensure_ascii=False)
def sha(s): return hashlib.sha256(s.encode()).hexdigest()
r = json.load(open("world_warrant_receipt.json"))
def committed(x):
    return [["measure",x["measure"]],["predicate",x["predicate"]],["value",x["value"]],
            ["witness",x["witness"]],["support",sorted(x["support"])],
            ["read_footprint",{"exact":sorted(map(list,x["read_footprint"]["exact"])),
                               "predicates":sorted(map(list,x["read_footprint"]["predicates"]))}],
            ["derivation_id",x["derivation_id"]],["at_vclock",x["at_vclock"]]]
def reseal_all():
    r["warrant"]["warrant_id"] = sha("TRVM-WARRANT-v3|" + js(committed(r["warrant"])))
    r["receipt_id"] = sha("TRVM-WORLDRECEIPT-v3|" + js(r["world_spec"]) + "|" + js(r["warrant"]) + "|" + r["footprint_id"]
                          + "|" + js(r["composite"]["warrant"]) + "|" + r["composite"]["footprint_id"])
'

run_case_engine receipt-support-prune-engine "support-mismatch" "$RESEAL_WR
r['warrant']['support'] = r['warrant']['support'][:-1]
reseal_all()
json.dump(r, open('world_warrant_receipt.json','w'), indent=1)"

run_case receipt-support-uncanonical "not canonical" "$RESEAL_WR
r['warrant']['support'] = list(reversed(r['warrant']['support']))
reseal_all()
json.dump(r, open('world_warrant_receipt.json','w'), indent=1)"

MAINT_RESEAL='
import json, hashlib
def js(o): return json.dumps(o, separators=(",",":"), ensure_ascii=False)
r = json.load(open("maintenance_receipt.json"))
def reseal():
    r["pass_id"] = hashlib.sha256(("TRVM-MAINTPASS-v1|"+str(r["vclock_before"])+"|"+str(r["vclock_after"])+"|"+js(r["before"])+"|"+js(r["after"])+"|"+js(r["steps"])).encode()).hexdigest()
'

run_case maint-step-erased-resealed "hides publication" "$MAINT_RESEAL
r['steps'] = [s for s in r['steps'] if s['name'] != 'B']
reseal()
json.dump(r, open('maintenance_receipt.json','w'), indent=1)"

run_case maint-action-flip-resealed "must not move the publication|must advance the publication" "$MAINT_RESEAL
r['steps'][0]['action'] = 'none'
reseal()
json.dump(r, open('maintenance_receipt.json','w'), indent=1)"

run_case maint-noop-lie-resealed "no_op flag does not recompute" "$MAINT_RESEAL
r['no_op'] = True
reseal()
json.dump(r, open('maintenance_receipt.json','w'), indent=1)"

run_case maint-aftermap-inflated-resealed "after-map disagrees with the step record" "$MAINT_RESEAL
list(r['after'].values())[0]['pub_version'] = 999
r['after']['A']['pub_version'] = 999
reseal()
json.dump(r, open('maintenance_receipt.json','w'), indent=1)"

run_case confinement-guard-stripped "missing confinement refusal" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('world-write-during-maintenance', 'oops-no-guard'))"

run_case key-privacy-stripped "key-confinement construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('#lockKey', '_lockKey'))"

run_case prototype-freeze-stripped "key-confinement construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('Object.freeze(World.prototype)', '/* unfrozen */'))"

run_case confinement-law-corrupt "canonical|non-canonical" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id']=='maintenance.capability-confinement': e['canonical']=False
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case maint-torn-inconsistent "torn receipts must be aborted|unapplied .* must show the before-side|applied .* must show" "$MAINT_RESEAL
r['torn'] = True
r['applied'] = []
reseal()
json.dump(r, open('maintenance_receipt.json','w'), indent=1)"

run_case world-law-canonical-corrupt "canonical|non-canonical" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id']=='warrant.phantom-scope': e['canonical']=False
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case sched-declaration-drift "strategy_schedulers" "
import json
g = json.load(open('invariant-grid.json'))
g['scheduler_certificate']['strategy_schedulers'] = ['leftmost','deepest','middle','random','starve_dups']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── E. round-10 forgeries: the golden pre-hash byte vectors ───────────────
# Each aims at a different one of the three bindings, so a single fix cannot
# quiet all four. The commitment is resealed where the forgery would otherwise
# die on vectors_id alone — an attacker who can edit the file can also rehash
# it, and a checker that only recomputes its own commitment proves nothing
# about whether the bytes describe this corpus.
PRESEAL='
import json, hashlib
def js(o): return json.dumps(o, separators=(",",":"), ensure_ascii=False)
v = json.load(open("golden_prehash_vectors.json"))
def reseal():
    v["vectors_id"] = hashlib.sha256(("TRVM-PREHASH-VECTORS-v1|"+js(v["per_term"])+"|"+js(v["compaction"])+"|"+js(v["corpus"])).encode()).hexdigest()
'

# 1. a signature byte flipped and the file honestly resealed: the digest it
#    claims to explain is no longer its sha256 preimage
run_case prehash-signature-tampered "does not hash to its sem_state_id" "$PRESEAL
t = v['per_term'][0]
t['initial']['sem_signature'] = t['initial']['sem_signature'].replace('N0', 'N1')
reseal(); json.dump(v, open('golden_prehash_vectors.json','w'), indent=1)"

# 2. the harder direction — signature AND id moved together so they are
#    internally consistent. Only the anchor to shipped evidence catches it.
run_case prehash-id-resealed "not anchored to the refinement receipt|different refinement receipt" "$PRESEAL
import hashlib
t = v['per_term'][0]
sig = 'L0(N0)FORGED'
t['normal_form']['sem_signature'] = sig
t['normal_form']['sem_state_id'] = hashlib.sha256(sig.encode()).hexdigest()
t['normal_form']['nf_id'] = 'sem-' + hashlib.sha256(b'whatever').hexdigest()
reseal(); json.dump(v, open('golden_prehash_vectors.json','w'), indent=1)"

# 3. vectors that describe a corpus the shipped receipts never ran
run_case prehash-nfid-unanchored "no refinement receipt row to anchor to" "$PRESEAL
v['per_term'][0]['name'] = 'identity_prime'
reseal(); json.dump(v, open('golden_prehash_vectors.json','w'), indent=1)"

# 4. the compaction boundary claimed but not demonstrated: the row says what
#    was compacted, and the reconstruction must hash to what was emitted
run_case prehash-compaction-lie "does not hash to the emitted compacted signature|does not exceed the threshold" "$PRESEAL
v['compaction']['first_compacted_precompaction']['signature'] += 'X'
v['compaction']['first_compacted_precompaction']['length'] += 1
reseal(); json.dump(v, open('golden_prehash_vectors.json','w'), indent=1)"

# 5. an over-threshold signature shipped uncompacted — §5 is structural, and a
#    published vector that ignores it teaches a second implementation the wrong
#    boundary while still hashing consistently with itself
run_case prehash-uncompacted-oversize "violates the §5 compaction rule" "$PRESEAL
import hashlib
t = v['per_term'][0]
sig = 'A(' + 'Ffree:LONG,'*12 + 'Ffree:END)'
t['initial']['sem_signature'] = sig
t['initial']['sem_state_id'] = hashlib.sha256(sig.encode()).hexdigest()
reseal(); json.dump(v, open('golden_prehash_vectors.json','w'), indent=1)"


# ── F. round-9D forgeries: the coordinator's guards ───────────────────────
# Each strips one construct the coordinator-confinement law names. These are
# artifact-tamper cases in the same family as confinement-guard-stripped and
# prototype-freeze-stripped: the law is only as real as the source that carries
# it, so removing the guard must fail the checker even though nothing else moved.
run_case coordinator-freeze-stripped "coordinator-confinement construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('Object.freeze(Maintainer.prototype);',''))"

run_case coordinator-reentrancy-stripped "coordinator-confinement construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('maintainer-reentrancy-refused','maintainer-allows-reentry'))"

run_case coordinator-inpass-stripped "coordinator-confinement construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('#inPass','_openPass'))"

run_case coordinator-law-corrupt "canonical flag of maintenance.coordinator-confinement" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id']=='maintenance.coordinator-confinement': e['canonical']=False
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case coordinator-section-dropped "coordinator_confinement missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['maintenance']['confinement']['coordinator_confinement']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── G. round-9D.1 forgeries: the reachable authority graph ────────────────
run_case writemediation-store-stripped "write-mediation construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('class GuardedStore','class UnguardedStore'))"

run_case writemediation-ownership-stripped "write-mediation construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('ownSpec','passthruSpec'))"

run_case writemediation-divergence-stripped "write-mediation construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('coordinator_diverged','coordinator_ok'))"

run_case writemediation-section-dropped "write_mediation missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['maintenance']['confinement']['write_mediation']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── H. round-9D.3 forgeries: ownership must fail closed ──────────────────
run_case ownership-failopen-restored "fail-open ownership path" "
s = open('trvm_world.mjs').read()
i = s.index('function ownCanonical')
j = s.index('}', s.index('throw new Error(label', i)) + 1
open('trvm_world.mjs','w').write(s[:i] + 'function ownCanonical(v, label) { try { return v; } catch { return v; } }' + s[j+1:])"

run_case ownership-refusal-stripped "total-ownership construct" "
s = open('trvm_world.mjs').read()
open('trvm_world.mjs','w').write(s.replace('-not-canonical: ','-not-canonical_'))"

run_case film-identity-declaration-dropped "film_identity_forward_declaration missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['film_identity_forward_declaration']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── I. the declared boundary failure must stay declared ──────────────────
run_case closure-law-greenwashed "not FALSIFIED" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id']=='derivation.environment-confinement': e['status']='PROPERTY-TESTED'
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case closure-law-deleted "environment-confinement@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries'] if e['id']!='derivation.environment-confinement']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case realm-roadmap-dropped "realm_roadmap missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['realm_roadmap']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── J. artifact-root / coverage forgeries ────────────────────────────────
run_case artifact-undeclared "present but UNDECLARED" "
import json
m = json.load(open('artifacts.json'))
m['case_inputs'] = [f for f in m['case_inputs'] if f != 'kappa_witnesses.mjs']
json.dump(m, open('artifacts.json','w'), indent=1)"

run_case artifact-manifest-corrupt "artifacts.json missing or not v1" "
import json
m = json.load(open('artifacts.json'))
m['type'] = 'TRVM-GOV-ARTIFACTS-v0'
json.dump(m, open('artifacts.json','w'), indent=1)"

run_case artifact-roots-declaration-dropped "artifact_roots missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['artifact_roots']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

# ── round 15: the two DERIVE-v0.1.0 defects, and the record of them ──────────
# Both defects were one line of the worker each and both read as harmless — a
# convenient place for the read table, and a field passed through from the
# request. Each forgery below restores one of them, or removes the record that
# says why they were wrong.

run_case derive-reads-via-inputs "sources the read table from canonical_inputs again" "
src = open('derive_worker.mjs').read()
src = src.replace('const out = evaluate(ast, req.read_grants, req.canonical_inputs);',
                  'const reads = req.canonical_inputs.__reads ?? {};\n    const out = evaluate(ast, reads, req.canonical_inputs);')
open('derive_worker.mjs','w').write(src)"

run_case derive-impl-echoed "must ASSERT its own implementation_id" "
src = open('derive_worker.mjs').read()
src = src.replace('implementation_id: JS_IMPLEMENTATION_ID,', 'implementation_id: req.expected_implementation_id,')
open('derive_worker.mjs','w').write(src)"

run_case derive-semantic-projection-widened "execution_evidence envelope OUTSIDE the semantic projection" "
src = open('derive_protocol.mjs').read()
src = src.replace('SEMANTIC_RESULT_FIELDS = [\"request_id\", \"program_sem_id\", \"grant_id\", \"semantic_result\"]',
                  'SEMANTIC_RESULT_FIELDS = [\"request_id\", \"program_sem_id\", \"grant_id\", \"semantic_result\", \"execution_evidence\"]')
open('derive_protocol.mjs','w').write(src)"

run_case derive-footprint-check-removed "missing v0.2.0 construct" "
src = open('derive_protocol.mjs').read()
src = src.replace('export function footprintWithinGrant', 'function footprintWithinGrant')
open('derive_protocol.mjs','w').write(src)"

run_case derive-grant-law-deleted "grant-footprint-separation@1 missing or non-canonical" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'derivation.grant-footprint-separation']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case derive-provenance-open-half-dropped "no longer declares its open half" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.implementation-provenance':
        e['statement'] = e['statement'].split('DECLARED OPEN')[0]
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case derivation-language-ruling-dropped "derivation_language missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['derivation_language']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case film-planes-dropped "film_planes missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['film_planes']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case derive-boundary-record-collapsed "two_evidence_objects or granting_model" "
import json
m = json.load(open('artifacts.json'))
del m['derivation_boundary']['two_evidence_objects']
json.dump(m, open('artifacts.json','w'), indent=1)"

# ── round 16: the frozen core ────────────────────────────────────────────────

run_case derive-core-not-committed "program_sem_id must commit CORE_SEM_ID" "
src = open('derive_protocol.mjs').read()
src = src.replace('H(\"TRVM-PROGRAM-v2|\" + CORE_SEM_ID + \"|\" + canonicalBytes(ast))',
                  'H(\"TRVM-PROGRAM-v2|\" + canonicalBytes(ast))')
open('derive_protocol.mjs','w').write(src)"

run_case derive-grammar-unchecked "must validate the grammar BEFORE hashing" "
src = open('derive_protocol.mjs').read()
src = src.replace('  const v = validateProgram(ast);\n  if (!v.ok) throw new Error(v.reason);\n', '')
open('derive_protocol.mjs','w').write(src)"

run_case derive-arith-coercion-restored "must refuse non-number operands" "
src = open('derive_protocol.mjs').read()
src = src.replace('throw new Error(\"program-type: \" + op + \" of non-number\")', 'void 0')
open('derive_protocol.mjs','w').write(src)"

run_case derive-trace-made-semantic "execution_evidence envelope OUTSIDE the semantic projection" "
src = open('derive_protocol.mjs').read()
src = src.replace('EXECUTION_ENVELOPE = [\"implementation_id\", \"read_trace\"]',
                  'EXECUTION_ENVELOPE = [\"implementation_id\"]')
open('derive_protocol.mjs','w').write(src)"

run_case footprint-set-ruling-dropped "dependency SET" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.core-semantics':
        e['statement'] = e['statement'].replace('canonical DEPENDENCY SET', 'sequence')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case core-freeze-undeclared "derivation_language.frozen missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['derivation_language']['frozen']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case core-law-deleted "law derivation.core-semantics@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'derivation.core-semantics']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case core-record-collapsed "frozen_core or footprint_is_a_set" "
import json
m = json.load(open('artifacts.json'))
del m['derivation_boundary']['footprint_is_a_set']
json.dump(m, open('artifacts.json','w'), indent=1)"


# ── round 17: the derivation authority ──────────────────────────────────────

run_case issuance-binds-the-grant-again "issuance must bind request_sem_id" "
src = open('derive_protocol.mjs').read()
src = src.replace('this.#issued.set(request_id, requestSemId(req));',
                  'this.#issued.set(request_id, body.grant_id);')
open('derive_protocol.mjs','w').write(src)"

run_case acceptance-made-a-free-function "acceptance must be a METHOD" "
src = open('derive_protocol.mjs').read()
src = src.replace('export class DerivationAuthority', 'export function acceptForeignResult(){}\nexport class DerivationAuthority')
open('derive_protocol.mjs','w').write(src)"

run_case acceptance-claims-committable "must not return .committable" "
src = open('derive_protocol.mjs').read()
src = src.replace('return { ok: true, validated: true, fresh_at_check: true, trace_conforms: v.trace_conforms,',
                  'return { ok: true, validated: true, fresh_at_check: true, committable: true, trace_conforms: v.trace_conforms,')
open('derive_protocol.mjs','w').write(src)"

run_case authorize-options-reopened "must whitelist its options" "
src = open('derive_protocol.mjs').read()
src = src.replace('AUTHORIZE_OPTIONS = [\"expected_implementation_id\"]', 'AUTHORIZE_OPTIONS = [\"expected_implementation_id\", \"canonical_inputs\"]')
open('derive_protocol.mjs','w').write(src)"

run_case freshness-vclock-restored "never on a global vclock" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.footprint-freshness':
        e['statement'] = e['statement'].replace('never on a global vclock', 'on the world vclock')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case committability-claim-restored "no longer states that acceptance does not establish" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.footprint-freshness':
        e['statement'] = e['statement'].replace('ACCEPTANCE DOES NOT ESTABLISH COMMITTABILITY', 'ACCEPTANCE ESTABLISHES COMMITTABILITY')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case issuance-law-deleted "law derivation.grant-issuance@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'derivation.grant-issuance']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case acceptance-record-dropped "acceptance_is_not_commitment" "
import json
m = json.load(open('artifacts.json'))
del m['derivation_boundary']['acceptance_is_not_commitment']
json.dump(m, open('artifacts.json','w'), indent=1)"


# ── round 18: the apparatus gate ────────────────────────────────────────────

run_case harness-selftest-law-deleted "law evidence.harness-selftest@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'evidence.harness-selftest']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case clean-baseline-species-dropped "no longer requires the clean-baseline" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'evidence.harness-selftest':
        e['statement'] = e['statement'].replace('UNPERTURBED case tree', 'perturbed case tree')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case harness-selftest-undeclared "does not declare harness_selftest.sh" "
import json
m = json.load(open('artifacts.json'))
m['tools'] = [t for t in m['tools'] if t != 'harness_selftest.sh']
json.dump(m, open('artifacts.json','w'), indent=1)"


# ── round 19: execution evidence has its own rule ───────────────────────────

run_case trace-conformance-removed "missing validateTraceConformance" "
src = open('derive_protocol.mjs').read()
src = src.replace('export function validateTraceConformance', 'function validateTraceConformance')
open('derive_protocol.mjs','w').write(src)"

run_case verdicts-collapsed "report semantic agreement and trace conformance SEPARATELY" "
src = open('derive_protocol.mjs').read()
src = src.replace('semantic_agreement: true, trace_conforms: false', 'trace_conforms: false')
open('derive_protocol.mjs','w').write(src)"

run_case execution-evidence-law-deleted "law derivation.execution-evidence@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'derivation.execution-evidence']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case unverified-sentence-dropped "non-semantic does not mean unverified" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.execution-evidence':
        e['statement'] = e['statement'].replace('NON-SEMANTIC DOES NOT MEAN UNVERIFIED. ', '')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case envelope-record-dropped "missing two_envelopes" "
import json
m = json.load(open('artifacts.json'))
del m['derivation_boundary']['two_envelopes']
json.dump(m, open('artifacts.json','w'), indent=1)"


# ── round 20: the clean baseline ────────────────────────────────────────────

run_case clean-baseline-law-deleted "law evidence.clean-baseline@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'evidence.clean-baseline']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case baseline-becomes-silence "no longer says the baseline is DECLARED" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'evidence.clean-baseline':
        e['statement'] = e['statement'].replace('DECLARED, not silent', 'silent')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case baseline-families-dropped "clean_baseline missing its phase list" "
import json
g = json.load(open('invariant-grid.json'))
del g['clean_baseline']['declared_baselines']
json.dump(g, open('invariant-grid.json','w'), indent=1)"


run_case gate-can-swallow-failure "no longer carries its runner half" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'evidence.clean-baseline':
        e['statement'] = e['statement'].replace('AND A GATE MUST BE ABLE TO FAIL', 'AND A GATE REPORTS')
json.dump(g, open('invariant-grid.json','w'), indent=1)"


run_case lowering-spike-dropped "lowering_spike missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['lowering_spike']
json.dump(g, open('invariant-grid.json','w'), indent=1)"


echo; [ $FAILED -eq 0 ] && echo "NEGATIVE BATTERY: $CASES/$CASES forgeries caught" || echo "NEGATIVE BATTERY: FAILURES PRESENT ($CAUGHT/$CASES caught)"
exit $FAILED
```

## `record/harness_selftest.sh`

```bash
#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# harness_selftest.sh — the apparatus is now measured too.
#
# Five consecutive rounds found a defect in the INSTRUMENT rather than in the
# engine: an unset $SCRATCH so a case could never execute; a hand-typed 44/44;
# a version-lockstep forgery that replaced a literal a bump would have made a
# no-op; a probe line printing "directly assignable" while testing typeof; the
# false "9D-4 confined" from a witness that never entered its own path; a
# non-vacuity law registered one round before the harness implemented it; a
# one-sided diff that called a deletion vacuous; and — round 15 — two reads the
# artifact-root round said it had anchored, one of which scanned the empty
# string and reported success; and — round 17 — a negative battery whose every
# case had been running against a checker that was already red.
#
# That is no longer an occasional bug. It is a recurring threat to the validity
# of every number this tree prints, so the KNOWN FAILURE SPECIES get a gate.
#
# This is deliberately NOT a general test-of-tests. It encodes the NINE shapes
# that have actually gone wrong here, and it stops there. Each meta-case breaks
# an instrument on purpose and requires the harness to SAY SO — except M-9,
# which requires the harness to say NOTHING when nothing is wrong, because a
# contaminated baseline is the one failure a battery of forgeries cannot see.
#
# Run: ./harness_selftest.sh   (exit 0 iff every meta-falsifier is caught)
# ═══════════════════════════════════════════════════════════════════════════
BASE="$(cd "$(dirname "$0")" && pwd)"
SCRATCH="${SCRATCH:-/tmp/harness-selftest}"
rm -rf "$SCRATCH" && mkdir -p "$SCRATCH"
META=0; CAUGHT=0; FAILED=0

meta () {  # name, expectation, actual-output, grep-pattern
  local name="$1" want="$2" out="$3" rx="$4"
  META=$((META+1))
  if echo "$out" | grep -qE "$rx"; then
    CAUGHT=$((CAUGHT+1))
    echo "PASS  $name → $(echo "$out" | grep -m1 -E "$rx" | sed 's/^ *//' | cut -c1-92)"
  else
    echo "FAIL  $name (wanted /$rx/)"; echo "$out" | tail -4 | sed 's/^/        /'; FAILED=1
  fi
}

CASE_INPUTS=$(python3 -c "
import json,re,os
m=json.load(open('$BASE/artifacts.json'))
fs=list(m['case_inputs']) + list(m.get('tools', []))
fs+=sorted(f for f in os.listdir('$BASE') if re.match(m['ledgers_pattern'],f))
print(' '.join(fs))")
mkcase () { local d="$SCRATCH/$1"; rm -rf "$d"; mkdir -p "$d"; for f in $CASE_INPUTS; do cp "$BASE/$f" "$d/"; done; echo "$d"; }

# ── M-1. the checker must not depend on the working directory ───────────────
# Round 15's finding, as a standing gate. The citation scan read whatever sat
# beside the process, and the banned-phrase tripwire scanned the EMPTY STRING
# when its file was absent — reporting clean while measuring nothing.
{
  # asserts IDENTITY of the three runs, not that they pass. The property under
  # test is cwd-independence; if the tree is red, all three must be identically
  # red. Requiring PASS here would make this meta-case fail for reasons that
  # have nothing to do with what it measures — which is its own failure species.
  a=$(cd "$BASE" && node grid_check.mjs 2>&1)
  b=$(cd / && node "$BASE/grid_check.mjs" 2>&1)
  c=$(cd /tmp && TRVM_GOV_ROOT="$BASE" node "$BASE/grid_check.mjs" 2>&1)
  if [ "$a" = "$b" ] && [ "$b" = "$c" ]; then out="IDENTICAL: $(echo "$a" | tail -1)"; else
    out="DIVERGED
  from governance/: $a
  from /:           $b
  from /tmp+ROOT:   $c"; fi
  meta "M-1 cwd-independence" "byte-identical output from three directories" "$out" "^IDENTICAL:"
}

# ── M-2. a declared artifact that is absent must fail LOUDLY ────────────────
{
  d=$(mkcase m2); rm "$d/refinement_receipt.json"
  meta "M-2 missing-artifact" "loud failure" "$(cd "$d" && node grid_check.mjs 2>&1)" "artifact missing: refinement_receipt.json"
}

# ── M-3. an artifact present but undeclared must fail ──────────────────────
# The silent direction: an undeclared file is never copied into a case and is
# therefore never tested, while the roster keeps counting.
{
  d=$(mkcase m3); echo '{"smuggled": true}' > "$d/extra_artifact.json"
  meta "M-3 undeclared-artifact" "coverage refusal" "$(cd "$d" && node grid_check.mjs 2>&1)" "present but UNDECLARED"
}

# ── M-4..M-7. the negative battery's own instrument checks ─────────────────
# One scratch battery carrying four deliberately-broken cases. Reusing the real
# runner rather than reimplementing it: a self-test that reimplements the thing
# it tests measures its own copy.
{
  d=$(mkcase m47); cp "$BASE/negative_battery.sh" "$d/"
  python3 - "$d" <<'PY'
import sys, re
d = sys.argv[1]
src = open(d + "/negative_battery.sh").read()
# split at the first INVOCATION, not at the function definition — `run_case () {`
# also starts with "run_case ", and splitting there produced a battery whose
# runner was undefined. Found by running this self-test, which is the point.
head = src[:re.search(r"^run_case [^(]", src, re.M).start()]
tail = '\necho; [ $FAILED -eq 0 ] && echo "META BATTERY: $CASES/$CASES" || echo "META BATTERY: FAILURES ($CAUGHT/$CASES)"\nexit $FAILED\n'

cases = r'''
# M-4 VACUOUS: a forgery that forges nothing. The roster would still count it.
run_case meta-vacuous "artifact_roots missing" "
pass"

# M-5 DELETION: the detector's own first defect was a one-sided diff that could
# not see a removed file and reported a deleting case as vacuous.
run_case meta-deletion "artifact missing: kappa_witnesses.mjs" "
import os
os.remove('kappa_witnesses.mjs')"

# M-6 TARGET MISMATCH: the script declares one target and moves two. The extra
# write is hidden behind a variable so intended_targets cannot see it, which is
# exactly how an accidental extra edit would look.
run_case meta-wrong-target "artifact_roots missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['artifact_roots']
json.dump(g, open('invariant-grid.json','w'), indent=1)
other = 'refinement_receipt.json'
open(other,'a').write(' ')"

# M-7 WRONG DIAGNOSTIC: a real forgery whose expected reason is not the one the
# checker gives. The case must fail rather than pass on any nonzero exit.
run_case meta-wrong-diagnostic "the moon is made of cheese" "
import json
g = json.load(open('invariant-grid.json'))
del g['artifact_roots']
json.dump(g, open('invariant-grid.json','w'), indent=1)"
'''
open(d + "/meta_battery.sh", "w").write(head + cases + tail)
PY
  chmod +x "$d/meta_battery.sh"
  out=$(cd "$d" && SCRATCH="$SCRATCH/m47cases" ./meta_battery.sh 2>&1)
  meta "M-4 vacuity-detected"     "VACUOUS"         "$out" "meta-vacuous \(VACUOUS"
  meta "M-5 deletion-detected"    "deletion is a change" "$out" "PASS  meta-deletion"
  meta "M-6 wrong-target-caught"  "TARGET MISMATCH" "$out" "meta-wrong-target \(TARGET MISMATCH"
  meta "M-7 wrong-diagnostic"     "case must fail"  "$out" "FAIL  meta-wrong-diagnostic \(exit=1"
}

# ── M-8. a paired probe must fail if EITHER side is broken ─────────────────
# The reason the derive probes are paired at all: a one-directional repro passes
# just as happily when the frozen copy is quietly replaced with the repaired
# one, at which point it documents nothing and still prints a number.
{
  d="$SCRATCH/m8"; rm -rf "$d"; mkdir -p "$d"
  cp "$BASE/derive_protocol.mjs" "$BASE/derive_worker.mjs" "$BASE/probe_derivegrant_v02_repro.mjs" "$d/"
  # repair the FROZEN copy — the witness now has nothing to witness
  python3 - "$d" <<'PY'
import sys
d = sys.argv[1]
p = d + "/probe_derivegrant_v02_repro.mjs"
s = open(p).read()
# The repair has to actually neutralise the witness. The first draft of this
# meta-case emptied the frozen `reads` table, and W-1 kept reproducing — because
# W-1 never performs a read: it reaches the grant table through the `input` op,
# since v0.1.0 carried the table INSIDE canonical_inputs. Stripping __reads from
# the inputs is the repair; the earlier one was a meta-case testing nothing,
# caught by this self-test failing on its own first draft.
s = s.replace("const out = evaluate(ast, reader, req.canonical_inputs);",
              "const { __reads: _gone, ...safe } = req.canonical_inputs;\n"
              "    const out = evaluate(ast, reader, safe);")   # frozen copy silently repaired
open(p, "w").write(s)
PY
  out=$(cd "$d" && node probe_derivegrant_v02_repro.mjs 2>&1)
  meta "M-8 vacuous-frozen-side" "VACUOUS" "$out" "VACUOUS: W-1 frozen"
}

# ── M-9. an UNPERTURBED case tree must pass ───────────────────────────────
# Round 17's find, and the most embarrassing of the nine: artifacts.json
# declares `tools` as well as `case_inputs`, grid_check requires every DECLARED
# artifact to exist, and the case tree only ever copied case_inputs. So four
# unrelated failures preceded every forgery since round 14. Each case still
# found its own diagnostic, so nothing was falsely green — but a checker that is
# already failing is not measuring what a negative case believes it is, and the
# only way to notice was to read output nobody had reason to read.
{
  d=$(mkcase m9)
  out=$(cd "$d" && node grid_check.mjs 2>&1; echo "EXIT=$?")
  meta "M-9 clean-case-baseline" "no forgery, no failures" "$out" "EXIT=0"
}

echo
[ $FAILED -eq 0 ] \
  && echo "HARNESS SELFTEST: $META/$META known apparatus failure species caught" \
  || echo "HARNESS SELFTEST: FAILURES PRESENT ($CAUGHT/$META caught)"
exit $FAILED
```

## `record/Makefile.txt`

```make
# TRVM — coordination-free distributed interaction-calculus runtime
# `make test` runs the full conformance battery across every implementation.

CC      ?= gcc
CFLAGS  ?= -O2
PY      ?= python3
NODE    ?= node
ZIG     ?= zig
ZIGFLAGS?= -OReleaseFast
# Mojo ships inside a pixi environment (runtime/mojo/pixi.toml). Either a bare `mojo`
# on PATH or a pixi that can materialise one will do; MOJO_RUN resolves at recipe time.
MOJO     ?= mojo
MOJOFLAGS?= -O3
PIXI     ?= pixi

IC32    := runtime/c/ic32
IC32Z   := runtime/zig/ic32z
IC32M   := runtime/mojo/ic32m
WASM    := runtime/wasm/ic32.wasm
PYPATH  := runtime/python:distribution:research
GOV     := governance
# The evidence plane reads the ONE canonical corpus; the embedded copy in the
# kernel is a fallback, and both commit to the same hash by corpus projection.
VECTORS := ../docs/spec/conformance/vectors/normalize.json

.PHONY: test conformance native native-selftest zig zig-selftest mojo mojo-selftest \
        wasm-smoke swarm research clean \
        governance gov-kernel gov-grid gov-world gov-negative gov-bridge gov-strict gov-derive gov-harness

test: native zig mojo conformance native-selftest zig-selftest mojo-selftest \
      wasm-smoke swarm research governance
	@echo ""
	@echo "==== TRVM full battery complete ===="

## --- native runtime --------------------------------------------------------
native: $(IC32)

$(IC32): runtime/c/ic32.c
	$(CC) $(CFLAGS) -o $@ $<

native-selftest: native
	@echo "==== [native] ic32 --test ===="
	@$(IC32) --test

## --- zig runtime (second conformant backend) -------------------------------
# Soft dependency: a missing Zig toolchain SKIPS the backend, it does not fail the
# build. The conformance runner then reports it as skipped rather than passing — an
# unbuilt backend must be visible, not invisible.
zig:
	@if command -v $(ZIG) >/dev/null 2>&1; then \
	  $(ZIG) build-exe $(ZIGFLAGS) runtime/zig/ic32.zig -femit-bin=$(IC32Z) && \
	  rm -f $(IC32Z).o; \
	else echo "  (zig not found — skipping zig backend)"; fi

zig-selftest: zig
	@echo "==== [zig] ic32z --test ===="
	@if [ -x $(IC32Z) ]; then $(IC32Z) --test; else echo "  (ic32z not built — skipped)"; fi

## --- mojo runtime (third conformant backend) -------------------------------
# Same soft dependency as Zig. Two ways to reach a compiler, tried in order: a bare
# `mojo` on PATH, else pixi driving runtime/mojo/pixi.toml (pixi's own installer puts
# it in ~/.pixi/bin, which is frequently not on a non-login shell's PATH, so look there
# too). Build output is captured and only replayed on failure -- the current nightly
# emits an `alias`-is-deprecated warning per constant, and forty lines of that on every
# `make test` trains people to stop reading the build log.
mojo:
	@if command -v $(MOJO) >/dev/null 2>&1; then \
	  MOJO_RUN="$(MOJO)"; \
	elif command -v $(PIXI) >/dev/null 2>&1; then \
	  MOJO_RUN="$(PIXI) run --manifest-path runtime/mojo/pixi.toml mojo"; \
	elif [ -x "$$HOME/.pixi/bin/pixi" ]; then \
	  MOJO_RUN="$$HOME/.pixi/bin/pixi run --manifest-path runtime/mojo/pixi.toml mojo"; \
	else MOJO_RUN=""; fi; \
	if [ -n "$$MOJO_RUN" ]; then \
	  if ! out=$$($$MOJO_RUN build $(MOJOFLAGS) runtime/mojo/ic32.mojo -o $(IC32M) 2>&1); \
	  then echo "$$out"; exit 1; fi; \
	else echo "  (mojo not found — skipping mojo backend)"; fi

mojo-selftest: mojo
	@echo "==== [mojo] ic32m --test ===="
	@if [ -x $(IC32M) ]; then $(IC32M) --test; else echo "  (ic32m not built — skipped)"; fi

## --- portable conformance runner (vectors + §6.1–§6.3) ---------------------
conformance: native zig mojo
	@echo "==== [conformance] vectors + SPEC §6 batteries ===="
	@$(PY) runtime/python/conformance.py

## --- wasm smoke ------------------------------------------------------------
wasm-smoke:
	@echo "==== [wasm] ic32.wasm via node ===="
	@if command -v $(NODE) >/dev/null 2>&1; then \
	  printf '%s' 'λx.x' | $(NODE) runtime/wasm/wrun.js && echo "  wasm identity OK"; \
	else echo "  (node not found — skipping wasm smoke)"; fi

## --- distributed capstone (real workers) -----------------------------------
swarm:
	@echo "==== [swarm] ic32.wasm coordination-free across worker_threads ===="
	@if command -v $(NODE) >/dev/null 2>&1; then $(NODE) runtime/js/swarm.js | tail -4; \
	else echo "  (node not found — skipping swarm)"; fi

## --- evidence / law plane --------------------------------------------------
# The execution plane above computes; this plane identifies, constrains, and
# proves. They meet at the canonical corpus (same 24 vectors, same committed
# hash) and, since round 10, at canonical semantic bytes. A runtime change that
# moved semantics would now fail here rather than pass quietly.
# EVERY LINE BELOW CAPTURES BEFORE IT PRINTS. `cmd | tail -1` takes the exit
# status of TAIL, not of cmd, so a gate that CRASHED printed a stack trace's
# last line and the target stayed green -- which is how the derive battery ran
# broken for a full round after the envelope split. A gate that cannot fail is a
# display. law:evidence.clean-baseline@1 is about the fixture; this is the same
# disease in the runner.
governance: gov-kernel gov-grid gov-world gov-negative gov-bridge gov-derive gov-harness
	@echo "  evidence plane green"

gov-kernel:
	@echo "==== [governance] law kernel — conformance + the periodic-law grid ===="
	@cd $(GOV) && out=$$(TRVM_VECTORS=$(VECTORS) $(NODE) trvm_law_kernel.mjs) && printf "%s\n" "$$out" | tail -2

gov-grid:
	@echo "==== [governance] invariant grid — registry, citations, engine-free receipts ===="
	@cd $(GOV) && $(NODE) grid_check.mjs

gov-world:
	@echo "==== [governance] World — warrants, maintenance, confinement ===="
	@cd $(GOV) && out=$$($(NODE) trvm_world.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && $(NODE) trvm_world.mjs --check-receipt

gov-negative:
	@echo "==== [governance] negative battery — every forgery must be caught ===="
	@cd $(GOV) && out=$$(./negative_battery.sh) && printf "%s\n" "$$out" | tail -1

gov-bridge: $(GOV)/bridge/ic32_canon
	@echo "==== [governance] cross-plane bridge — C canonical bytes vs the JS oracle ===="
	@cd $(GOV) && $(NODE) bridge/bridge_check.mjs

# The execution plane emitting the evidence plane's canonical bytes. ic32.c is
# included verbatim with its main renamed — the runtime under test is the
# runtime that ships.
$(GOV)/bridge/ic32_canon: $(GOV)/bridge/ic32_canon.c runtime/c/ic32.c
	$(CC) $(CFLAGS) -o $@ $<

# Release / pack-cut gate. CONF-2 may report NOT_APPLICABLE for a standalone
# oracle whose corpus file is absent — equality is then UNKNOWN, not agreed. An
# artifact that leaves the repository must never be cut from such a run, so this
# target makes an unreachable corpus fatal. Not part of `make test`, which is a
# development gate; this is the emission gate.
gov-strict:
	@echo "==== [governance] STRICT corpus identity — release / pack-cut gate ===="
	@cd $(GOV) && out=$$(TRVM_STRICT_CORPUS=1 TRVM_VECTORS=$(VECTORS) $(NODE) trvm_law_kernel.mjs) && printf "%s\n" "$$out" | tail -1

# law:evidence.harness-selftest@1 — six consecutive rounds found the defect in
# the INSTRUMENT rather than the engine, so the known failure species get a gate
# of their own. Bounded on purpose: nine enumerated shapes, and no recursion
# into tests of tests.
gov-harness:
	@echo "==== [governance] harness self-test — the apparatus is measured too ===="
	@cd $(GOV) && out=$$(./harness_selftest.sh) && printf "%s\n" "$$out" | tail -1

# The replacement for the falsified arbitrary-closure derivation API: program
# as data, canonical request/result, and a real worker crossing where structured
# cloning refuses callables outright.
gov-derive:
	@echo "==== [governance] serialized derivation boundary ===="
	@cd $(GOV) && out=$$($(NODE) derive_battery.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) derive_realm_battery.mjs) && printf "%s\n" "$$out" | tail -1
# The only PAIRED probe in the tree, and the only one that gates. Its siblings
# freeze a boundary that is DECLARED open, so they report a breach and that is
# the record. These two defects are repaired, so the probe runs each witness
# against the frozen v0.1.0 copy — where it must still reproduce, or the witness
# has gone vacuous and stopped measuring — and against live, where it must be
# confined. law:evidence.instrument-nonvacuity@1 applied to a repro.
	@cd $(GOV) && out=$$($(NODE) probe_derivegrant_v02_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_coresem_v03_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_stalegrant_v03_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_issuebind_v05_repro.mjs) && printf "%s\n" "$$out" | tail -1
	@cd $(GOV) && out=$$($(NODE) probe_traceforge_v06_repro.mjs) && printf "%s\n" "$$out" | tail -1

## --- identity/memory result ------------------------------------------------
research:
	@echo "==== [research] merge-is-a-CvRDT (semilattice laws + SEC) ===="
	@PYTHONPATH=$(PYPATH) $(PY) research/semilattice.py | tail -3

## --- wasm rebuild (optional; needs clang-15 + lld-15) ----------------------
wasm:
	bash runtime/wasm/build.sh

clean:
	rm -f $(IC32) ic32 $(IC32Z) $(IC32Z).o $(IC32M)
	rm -rf runtime/zig/.zig-cache
	rm -f runtime/mojo/*.o
	@# runtime/mojo/.pixi/envs is deliberately NOT removed: it is a multi-minute
	@# toolchain download, not a build artifact of this repo.
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
```

## `record/commits.txt`

```text
0e5ec7d Restore a grid section the split lost, and the brief that claimed it was there
189768d The gate could not fail
35184fb A perturbation result needs a declared clean baseline
4cd8403 Outside the semantic projection had become unchecked
b475232 The apparatus is measured too
242d319 Issuance authenticated the grant, and acceptance took both proofs from its caller
583e742 The identity bound a spelling
d8cc288 The record said the footprint was the grant, and the mechanism said neither
```

## `gate/negative_battery.txt`

```text
$ ./negative_battery.sh
/bin/bash: line 16: cd: governance: No such file or directory
```

## `gate/harness_selftest.txt`

```text
$ ./harness_selftest.sh
PASS  M-1 cwd-independence → IDENTICAL: GRID-CONSISTENCY-2: PASS — registry valid (63 entries), 347 citations resolved ac
PASS  M-2 missing-artifact → - artifact missing: refinement_receipt.json
PASS  M-3 undeclared-artifact → - governance artifact extra_artifact.json is present but UNDECLARED in artifacts.json — the 
PASS  M-4 vacuity-detected → FAIL  meta-vacuous (VACUOUS — the forgery changed no artifact; nothing was tested)
PASS  M-5 deletion-detected → PASS  meta-deletion [kappa_witnesses.mjs] → - artifact missing: kappa_witnesses.mjs
PASS  M-6 wrong-target-caught → FAIL  meta-wrong-target (TARGET MISMATCH — script intends [invariant-grid.json], run changed
PASS  M-7 wrong-diagnostic → FAIL  meta-wrong-diagnostic (exit=1; wanted /the moon is made of cheese/)
PASS  M-8 vacuous-frozen-side → DERIVE-GRANT-v0.2 REPRO: 1/2 reproduce against the frozen v0.1.0 · 2/2 confined against live
PASS  M-9 clean-case-baseline → EXIT=0

HARNESS SELFTEST: 9/9 known apparatus failure species caught
```

## `gate/derive_battery.txt`

```text
$ cd code && node derive_battery.mjs
PASS  program-id-is-content              two programs, two ids (psem-fa4ca55b1… vs psem-6501d078a…); recomputing P's id reproduces it
PASS  label-substitution-refused         a request naming P against a registry holding only the evil program is refused: program-unknown — an id cannot be pointed at different code, because the id IS the code's hash
PASS  capabilities-refused-at-boundary   Function:refused Map:refused Set:refused Date:refused class instance:refused — structuredClone would have accepted Map, Set and Date; the canonical domain does not
PASS  request-schema-closed              an unknown field is refused (request-schema: unknown [extra_capability]) and a short request names what it lacks (request-schema: missing [canonical_inputs,grant_id,read_grants…)
PASS  derivation-honest                  bias 0 -> 5, bias 1000 -> 1005; the bias is an INPUT of the request, so it is visible in canonical_inputs instead of hiding in a lexical cell
PASS  footprint-recorded                 read_footprint.exact = [["fb",1]] — reads are tracked by the evaluator on access, not declared by the caller
PASS  no-ambient-cell                    the same request derives identically twice; there is no environment between them to mutate (law:derivation.environment-confinement@1 is FALSIFIED for the closure API and this is the replacement path)
PASS  reader-is-not-a-callable           evaluate(ast, read_grants, inputs) builds its own reader from canonical grant data. A pair of reader CALLABLES in the grant position is refused as data (grants-schema: [read,scope]) — v0.1.0 took the reader as a parameter, which was the closure-authority shape in miniature
PASS  grant-not-reachable-as-input       {op:"input",name:"__reads"} returns "an ordinary input" — at v0.1.0 it returned the entire authority grant table with witness.reads = 0. read_grants is a separate request field and the input op cannot address it (W-1, frozen in probe_derivegrant_v02_repro.mjs)
PASS  footprint-is-the-access-subset     grant covers fb,unused_a,unused_b (3 resources); the footprint records [["fb",1]] (1). Defining the footprint AS the grant would invalidate this derivation whenever unused_a moved, which it does not depend on
PASS  grant-id-binds-the-snapshot        a request carrying a swapped snapshot under the original grant_id is refused: request-grant-id-mismatch — the id is H(canonical read_grants), so the snapshot cannot be edited in flight
PASS  footprint-validated-independently  over-claimed read -> footprint-ungranted-read: secret:key; forged version -> footprint-version-mismatch: fb. Both refused against the SNAPSHOT rather than against the executor's word, before any re-derivation
PASS  witness-matches-footprint          a result claiming 7 reads with a 1-entry footprint is refused: result-witness-inconsistent
PASS  foreign-result-revalidated         honest accepted; inflated value -> foreign-result-divergence; re-labelled request -> result-request-mismatch; re-labelled program -> result-program-mismatch; re-labelled grant -> result-grant-mismatch. Across a realm this is the entire trust story: the far side produces a claim, the authority reproduces it
PASS  implementation-id-asserted         the result carries impl-js-derive-v0.6.0, emitted by the evaluator that ran. At v0.1.0 the REQUEST carried implementation_id, nothing checked it and the result carried none (W-2)
PASS  implementation-requirement-refused a request demanding a C executor is refused BY the JS executor (implementation-mismatch: want impl-c-pretend-v9, this is impl-js-derive-v0.6.0) — the caller's field states a requirement and the executor answers it, so impersonation has no path
PASS  implementation-id-well-formed      a result whose implementation_id is not an impl- identity is refused: result-implementation-id-malformed
PASS  semantic-projection-is-portable    a result identical in semantics but produced by impl-c-derive-v0.2.0 validates, and the authority records WHO ran it (impl-c-derive-v0.6.0). program_sem_id is equal across implementations; implementation_id is outside the semantic projection, which is what makes a portable film possible
PASS  implementation-requirement-checked-on-result a result from a different executor than the one required is refused: implementation-mismatch: want impl-js-derive-v0.6.0, result claims impl-c-derive-v0.6.0
PASS  registry-binding-verified          verify(PID) recomputes the hash and agrees; an unbound id is refused (program-unknown)
PASS  registry-entry-frozen              the stored program is deep-frozen; mutating it throws and the registry still reads 'add'
PASS  core-id-is-content-bound           CORE_SEM_ID recomputes from the frozen CORE_SPEC (core-0930d6f10070a8e…). A bare label "TRVM-DERIVE-CORE-v1" would be the caller-selected-name defect the primitive ruling already refuses
PASS  program-id-commits-the-core        program_sem_id = H("TRVM-PROGRAM-v2|" + core_sem_id + "|" + canonicalBytes(ast)) — change what add means and the core moves and every program id moves with it, which is what makes the id semantic
PASS  grammar-refuses-before-id          unknown op:refused missing field:refused extra field:refused non-string name:refused bad child:refused non-canonical const:refused — v0.2.0 issued a program_sem_id to {op:"exec", cmd:"rm -rf /"}, which failed only later at evaluation, having already been given a semantic identity
PASS  arithmetic-typed-and-total         2+3 =5 · "2"+"3" program-type: add of non-number · []+{} program-type: add of non-number · 1e308+1e308 program-arith-non-finite: add. v0.2.0's add was JavaScript's + and produced "23" and "[object Object]" under the same program_sem_id
PASS  footprint-is-a-canonical-set       three accesses in order [["b",1],["a",1],["b",1]] produce the dependency set [["a",1],["b",1]]. Depending on {a,b} is ONE dependency set however it was visited — declaring the order semantic would make two correct implementations diverge over a field neither of them considers semantic
PASS  trace-is-outside-the-semantic-projection semantic projection = [request_id, program_sem_id, grant_id, semantic_result]; execution evidence = [implementation_id, read_trace]. Excluded from the comparison and NOT excluded from checking — non-semantic does not mean unverified, which is what v0.5.0 got wrong
PASS  footprint-set-is-checked-not-normalized result-footprint-not-canonical-set: exact — normalizing on receipt would let two implementations commit to different bytes and still be told they agreed
PASS  overflow-refused-on-every-operator add:program-arith-non-finite: add · sub:program-arith-non-finite: sub · mul:program-arith-non-finite: mul — one refusal string, three separately frozen semantic surfaces, each witnessed
PASS  coercion-refused-on-every-operator add:program-type: add of non-number · sub:program-type: sub of non-number · mul:program-type: mul of non-number
PASS  signed-zero-identified             mul(-1, 0) evaluates to -0 and canonicalizes to 0 — the canonical numeric quotient identifies them, which was already true of the domain and unstated. A C implementation would otherwise have decided it by accident
PASS  freshness-is-not-containment       after fb moves 1→2: footprintWithinGrant PASS, re-derivation PASS — both CORRECT about the snapshot — and acceptance stale-read: fb granted@1 live@2. Containment is historical, freshness is temporal, and a protocol that stops at re-derivation commits a value the World has already contradicted
PASS  unrelated-write-does-not-invalidate other@1→2 moved and acceptance still passes — freshness keys on the FOOTPRINT, never on a global vclock. A vclock rule would invalidate every derivation on every unrelated write, undoing the grant/footprint separation from the other side
PASS  acceptance-does-not-claim-committable accept() returns {validated, fresh_at_check} and NOT committable. One call cannot make a result committable: the World can move between this returning and the caller applying. The composition that commits belongs to the World — lock, accept, prepared apply, receipt, unlock — and no lock capability is exported to reach it
PASS  issuance-binds-the-whole-request   the issuing authority accepts; a different instance refuses (grant-not-issued-by-this-authority); and an input swap under an UNTOUCHED request_id and grant_id — which derives to 1005 — is refused (request-not-as-issued). The draft bound request_id → grant_id and answered "was this issued?" about a GRANT while the thing being accepted was a REQUEST
PASS  request-sem-id-recomputes          request_sem_id = H(canonical request) recomputes over an owned copy and differs for the swapped request — which is the whole mechanism
PASS  authorize-options-whitelisted      authorize-options-unknown: [canonical_inputs] — the draft spread `...over` after every authority-decided field, so a caller could overwrite canonical_inputs on an authority-ISSUED request. Exactly one field may be requested
PASS  issued-request-is-owned-and-frozen the issued request is owned through canonicalBytes and deep-frozen; mutating it throws. Defence in depth — the BINDING is what refuses a modified request; this stops accidental modification inside the authority's own process
PASS  intent-schema-closed               extra field:refused missing field:refused resources not lists:refused capability in inputs:refused — the untrusted half of the two-phase protocol is validated as strictly as the authority's half
PASS  authority-requires-a-world         authority-requires-a-world-reader — an authority without a World cannot answer the temporal question, and one that silently could not would report fresh by never looking
════════════════════════════════════════════════════════════════════════════════════════════════
DERIVE-BATTERY: PASS — 40/40. The program is data and its id commits the frozen core's semantics, not just its syntax; the grant is what the authority made available and the footprint is what the program consumed — a canonical dependency SET whose access order is a separate trace, outside semantics; the executor asserts its own identity; containment is historical and freshness is temporal; and issuance binds the whole request to the authority that cut it, which no caller can supply on its behalf.
exit=0
```

## `gate/probe_traceforge_v06_repro.txt`

```text
$ cd code && node probe_traceforge_v06_repro.mjs
BREACH    T-1 frozen-v0.5.0      honest trace [["a",1],["b",1]] reversed to [["b",1],["a",1]] with the footprint [["a",1],["b",1]] and the value 3 untouched: validateForeignResult -> ok=true. The footprint check compares the SET, which a reversal does not change, and the semantic projection excluded the trace — so nothing looked at it
CONFINED  T-1 live               trace-nonconforming: exact — and the two verdicts are reported SEPARATELY: semantic_agreement true, trace_conforms false. "Same meaning, different strategy" and "wrong answer" are different diagnoses, and v0.5.0 could make neither
CONFINED  honest-still-accepted  an honest result is accepted with validated true, trace_conforms true and still NO committable — the new check refuses a forgery without inventing a stronger claim about the honest case
CONFINED  envelopes-are-explicit the result is {execution_evidence, grant_id, program_sem_id, request_id, semantic_result} and the semantic projection is [request_id, program_sem_id, grant_id, semantic_result]. At v0.5.0 read_trace was a SIBLING of value and read_footprint, which reads as authenticated by the same machinery as its neighbours — and was not
CONFINED  trace-rule-is-executable validateTraceConformance is exported and refuses by name (trace-nonconforming: exact) — the core FIXES evaluation order so refusals and traces reproduce, so a disagreeing trace is a conformance failure of the implementation rather than a disagreement about the program
====================================================================================================
TRACE-FORGE v0.6 REPRO: 1/1 reproduce against the frozen v0.5.0 · 4/4 confined against live
exit=0
```

## `gate/make-governance.txt`

```text
# make governance — verbatim, 2026-08-19T03:21Z, node v25.2.1

make: *** No rule to make target 'governance'.  Stop.
```

## `record/rounds-19-21-ledger.md`

## Round 19 — outside the semantic projection had become unchecked

**85. Round 16's ruling was right and left a hole nobody had named.** Access order is execution strategy and must not be semantic identity — that stands. What round 16 did not say, and what v0.5.0 therefore did not do, is that a field excluded from the *comparison* still needs a rule of its own. **T-1**, frozen in `probe_traceforge_v06_repro.mjs`: a program reading `a` then `b` traces `[["a",1],["b",1]]`; reverse **only** the trace, leave the canonical footprint and the value untouched, and against v0.5.0 —

```
validateForeignResult  → { ok: true }
authority.accept       → { ok: true, validated: true, fresh_at_check: true }
```

`checkResult` compared the footprint to the *set* of the trace, which a reversal does not change, and `validateForeignResult` compared only the semantic projection, from which the trace was excluded. So the one field carrying execution evidence was the one field nothing looked at.

**86. The flat shape was part of the defect.** `read_trace` sat as a sibling of `value`, `support` and `read_footprint`. A field inside `DeriveResult` reads as authenticated by the same machinery as its neighbours, and this one was not — the exclusion was a comment, and comments do not hold. The envelopes are now explicit, and the trust status of each field is visible in the shape:

```
semantic_result      value · witness · support · read_footprint
                     determines portable meaning; this is what
                     cross-implementation validation compares

execution_evidence   implementation_id · read_trace
                     conformance and provenance; excluded from the
                     comparison and NOT excluded from checking
```

**87. NON-SEMANTIC DOES NOT MEAN UNVERIFIED.** That sentence is the whole round, and it is now the opening clause of `law:derivation.execution-evidence@1`. The core *fixes* evaluation order precisely so that refusals and traces reproduce, so a returned trace disagreeing with the authority's own re-derivation is a **conformance failure of the implementation**, not a disagreement about the program — refused as `trace-nonconforming`. And the two verdicts are reported **separately**: `semantic_agreement: true, trace_conforms: false`. *"Same meaning, different strategy"* and *"wrong answer"* are different diagnoses, and v0.5.0 could make neither because it never looked.

**88. The non-vacuity detector caught two more falsifiers this round's own edits had killed.** `derive-trace-made-semantic` and `derive-semantic-projection-widened` both targeted the literal `NON_SEMANTIC_RESULT_FIELDS`, which the envelope split removed, and `acceptance-claims-committable` targeted a return statement this round rewrote. All three changed nothing and were reported `VACUOUS` rather than passing. That is the third, fourth and fifth time this session — and every one was found by the mechanism rather than by a reader.

**89. Gate.** grid **v1.20.0** — 62 entries / 343 citations · `derive_protocol.mjs` **0.6.0** · kernel PASS · World 0.12.0 PASS · `--check-receipt` PASS · negative battery **100/100** with five new forgeries · bridge 48/48 · derive **41/41 in-process, 10/10 across a realm** · probes **2/2+2/2**, **4/4+5/5**, **5/5**, **3/3+4/4**, **1/1+4/4** · harness **9/9**. `scheduler_certificate.json` byte-identical — fourteenth consecutive round.

**The shape of the last four rounds.** 16 froze what a program *means*. 17 fixed what an authority *authenticates* and what acceptance may *claim*. 18 measured the measurer. 19 is the one that says the quiet part: this system now has enough distinct evidence classes — semantic, execution, transaction — that each needs its own explicit trust boundary, and a field is not safe merely because it has been excluded from someone else's.


---

## Round 20 — a perturbation result needs a declared clean baseline

**90. M-9 generalises, and the wrong generalisation was the obvious one.** "Every gate must report nothing when nothing is wrong" fails immediately: the kernel, the World and the bridge all legitimately print their results, and they are not perturbation experiments — they ARE baseline observations. The invariant belongs to a narrower and much more common claim: *"I changed X, and therefore X caused this failure."* Only a falsifier asserts that, and only a falsifier can be wrong about it in the way round 17 found.

**91. `law:evidence.clean-baseline@1`, and the word is DECLARED rather than silent.** A perturbation-based result is admissible only if the identical verifier, fixture, environment and artifact set satisfy their **declared** baseline before the perturbation is applied — and each falsifier family names its own:

| family | declared baseline |
|---|---|
| `negative_battery.sh` | `grid_check` exits 0 on the unperturbed fixture — **implemented** |
| paired probes | the live half is confined; both directions required — **implemented by construction** |
| one-directional 9D probes | the honest fixture holds the invariants under attack — **declared open** |
| bridge / kernel / World | positive gates; themselves baseline observations — nothing added |

Five phases, in order: `establish_baseline` · `perturb` · `assert_perturbation` · `run_subject` · `assert_specific_diagnostic`.

**92. The baseline is established once and each case proves it inherited it.** Every case builds its fixture by the same recipe from the same source, so one baseline run covers them all — but that is exactly the sort of "obviously true" step this record keeps finding to be false. So it is verified rather than assumed: each case compares its own pre-perturbation digest against the baselined tree and fails **FIXTURE DRIFT** if they differ. A failed baseline aborts the whole run and says why, in the words that matter: *no case below is isolated-cause evidence.*

**93. The self-test stays bounded at nine, deliberately.** Promoting M-9 into a law applied as a **precondition** of every falsifier family is not the same as adding six more meta-cases for the kernel, the World and the bridge. The second is the infinite regress the self-test was written to avoid, and the bounded suite is worth more than a larger one precisely because its boundary is defensible.

**94. And this round's own edit inflated a counter by one.** The phase insertion matched in both runners — `run_case` and `run_case_engine` — so the engine case incremented `CASES` twice and the printed total read **101** where the case set was 100. Caught because the number moved when nothing about the case set had, which is the only reason a derived total is worth having: the round-10 repair that made these counters derived rather than hand-typed is what made this visible at all.

**95. Gate.** grid **v1.21.0** — 63 entries / 344 citations · kernel PASS · World 0.12.0 PASS · `--check-receipt` PASS · negative battery **103/103**, with a declared baseline established and every fixture proved to inherit it · bridge 48/48 · derive **41/41 · 10/10** · probes **2/2+2/2**, **4/4+5/5**, **5/5**, **3/3+4/4**, **1/1+4/4** · harness **9/9**. `scheduler_certificate.json` byte-identical — fifteenth consecutive round without the calculus moving.


---

## Round 21 — the gate could not fail

**96. The derive battery ran BROKEN for a full round and `make governance` stayed green.** The round-19 envelope split moved `read_footprint` inside `semantic_result`, and one call site in `derive_battery.mjs` was missed. The battery crashed on it — `TypeError: Cannot read properties of undefined (reading 'exact')` — and the gate reported success for round 19 and round 20, because every governance recipe was written

```make
@cd $(GOV) && $(NODE) derive_battery.mjs | tail -1
```

and **`cmd | tail -1` takes the exit status of `tail`**. A crashing subject printed a stack trace's last line where its verdict should have been, and the pipeline exited 0. Found while assembling a review bundle — by reading a line of output, not by the gate.

**97. A gate that cannot fail is a display.** All thirteen governance recipe lines now capture the subject's output *and* status before printing (`out=$(cmd) && printf …`), so the recipe fails on the subject's own status. Verified in both directions rather than asserted: an **unresolvable import** (a crash) and a **false assertion** (exit 1) each fail the target, and the restored file passes. `law:evidence.clean-baseline@1` gains this as its runner half — the baseline clause is about the *fixture*, and this is the same disease in the *runner*.

**98. And the first crash test written for it was vacuous.** Appending `throw new Error("deliberate crash")` to the end of the battery proved nothing: the file ends in `process.exit(fail ? 1 : 0)`, so the throw is unreachable. The test reported the gate as passing a crash it never experienced. That is the ninth species — a falsifier that does not perturb what it claims to — committed while building the fix for a tenth, and it is recorded rather than quietly corrected because the alternative is a record that only contains the mistakes I noticed in time.

**99. A section of the grid was lost in the round-16 split, and a review brief asserted it was there.** The combined round-16 draft carried `lowering_spike` — `TRVM-TERM-CANON-v1`, the three properties, the decision rule. Splitting that draft into rounds 16/17/18 rebuilt the grid from the round-15 base, and the section was never re-added. The review brief for 16/17/18 then stated that `TRVM-TERM-CANON-v1` was *"recorded in `lowering_spike`"*, while the machine-readable extract shipped in the same bundle contained `"lowering_spike": null`. **The prose was wrong and the extract was right**, which is the only reason it is knowable at all — and it was found by an unrelated edit failing with `KeyError: 'lowering_spike'`, not by anyone reading either. Restored in this round with the fourth identity the review supplied, locked by `grid_check`, and given its own forgery. The lesson is not "check the prose": it is that the machine-readable half of a claim is worth shipping precisely because it can contradict the sentence beside it.

**100. Gate.** grid **v1.22.0** — 63 entries / 346 citations · negative battery **105/105** · derive **40/40 · 10/10** · probes **2/2+2/2**, **4/4+5/5**, **5/5**, **3/3+4/4**, **1/1+4/4** · harness **9/9** · bridge 48/48 · kernel PASS · World 0.12.0 PASS. `scheduler_certificate.json` byte-identical — sixteenth consecutive round.

**The uncomfortable summary of rounds 15 through 21.** Seven consecutive rounds, and in six of them the defect was in the evidence apparatus rather than in the thing it measures: a footprint that could be produced without a read, an identity that bound a spelling, an issuance that authenticated the wrong object, a trace excluded from comparison and therefore from checking, a fixture that was already red, and a gate that could not fail. The calculus has not moved in sixteen rounds. What keeps moving is the machinery that claims to be watching it.
