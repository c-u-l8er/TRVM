# DERIVE-v0.3 — your five rulings, built

**For:** review of TRVM round 16 (`TRVM/governance/`, branch `merge/governance-plane`)
**Built by:** Claude (Opus 5), session 2026-08-18
**Predecessor:** your review of round 15, and commit `d8cc288` — Round 15 landed as you ruled, staged
to its own paths only; the unrelated `LICENSE` deletion and `site/amp-nav.js` were left alone
(the LICENSE has since been restored by Travis, not by this session).
**Status:** shipped, whole gate green, **not committed**.

```
cd code
node derive_battery.mjs              # 30/30 in-process
node derive_realm_battery.mjs        # 10/10 across a real worker_threads boundary
node probe_coresem_v03_repro.mjs     #  4/4 frozen · 5/5 live
node probe_stalegrant_v03_repro.mjs  #  5/5
node probe_derivegrant_v02_repro.mjs #  2/2 frozen · 2/2 live
```

`record/harness_selftest.sh` needs the full governance tree; its output is in `gate/`.

---

## 0. Your central catch reproduced, and it was worse than described

You said the id binds syntax but not stable program semantics. Verified before anything changed —
four gaps behind one `program_sem_id`, now frozen as C-1…C-4 in `code/probe_coresem_v03_repro.mjs`:

```
C-1  add was JavaScript +      "2"+"3" = "23" · []+{} = "[object Object]" · 1e308+1e308 = Infinity
C-2  bind() validated nothing  {op:"exec", cmd:"rm -rf /"}  →  psem-177f6b6b00b56c347…
C-3  arity unconstrained       {op:"const"} · add-without-b · add-with-an-extra-field  → all bound
C-4  evaluation order free     read_footprint is an ARRAY: [["b",1],["a",1]]
```

**C-4 was not in your list and is the one I'd flag back.** The footprint is a *sequence* appended at
access, so a right-to-left implementation returns different canonical bytes for a program it
computed identically — `foreign-result-divergence` between two correct evaluators, over a field
neither of them would think of as semantic. Evaluation order was load-bearing and unstated. It is
now in `CORE_SPEC.evaluation_order` explicitly, including the sentence that the footprint's order is
part of the result.

---

## 1. Ruling by ruling

**Freeze the core — done, and content-bound rather than labelled.** `TRVM-DERIVE-CORE-v1` is a frozen
canonical record (`record/CORE_SPEC.json`) covering grammar, value domain, arithmetic, evaluation
order, footprint ordering, totality and the refusal vocabulary. One deviation from your wording: you
said *"make that semantic namespace load-bearing in the ID"*, and I did not use the string. A bare
`"TRVM-DERIVE-CORE-v1"` is exactly the caller-selected identity your own primitive ruling refuses
for `"componentReachability"` — the record would have committed the defect one layer up while
forbidding it one layer down. So:

```
core_sem_id    = H("TRVM-DERIVE-CORE-SPEC-v1|" + canonicalBytes(CORE_SPEC))
program_sem_id = H("TRVM-PROGRAM-v2|" + core_sem_id + "|" + canonicalBytes(ast))
```

Change what `add` means and `core_sem_id` moves and every program id moves with it. `psem(P)` moved
`psem-f154679c…` → `psem-e5568a1f…`; **every v0.2.0 id is retired**, which is cheap exactly once.
Grammar is validated *before* the hash, so no identity is ever issued for a program outside the
language. The primitive catalog stays unfrozen and a `prim` extension bumps the core version.

**Freshness — done, and kept out of `footprintWithinGrant` as you ruled.** Your witness is
`code/probe_stalegrant_v03_repro.mjs`, verbatim: grant `fb@1=5`, derive, World moves to `fb@2=9`,
then `checkResult` PASS · `footprintWithinGrant` PASS · `validateForeignResult` PASS — all three
correct — and live freshness refuses `stale-read: fb granted@1 live@2`. Keyed on the footprint, never
on a vclock; the negative half (`unrelated-write-ignored`) is witnessed, and `grid_check` refuses a
law text that drops the phrase. The scope half turned out to reach further than expected:
`stale-scope: kind:node` is the World's phantom-scope case arriving at the derivation boundary.
Acceptance is one call, and the lock requirement is stated in the source and the law rather than
assumed — `acceptForeignResult` does not and cannot take the World's lock.

**Grant signing — not added, topology fixed instead, as you ruled.** `DeriveIntent` →
`GrantIssuer.authorize` → `DeriveRequest`; the issuer is the only constructor and records what it
cut, so a *different* `GrantIssuer` instance refuses the byte-identical request with
`grant-not-issued-by-this-authority`. Your four triggers for adding a MAC are written into
`law:derivation.grant-issuance@1` so the crypto arrives for a reason.

**`implementation_id` measured outside the executable — declared, not built.** Your launcher model
(descriptor + `artifact_sha256`, measured by the trusted loader, never hashed into itself) is
recorded in the roadmap as *"measured implementation provenance: the trusted launcher hashes what it
launches"*. The current constant still closes impersonation only, and the law still says
`DECLARED OPEN` in its own statement. Not built this round because it belongs with the C executor
that will be the first thing to need it.

**Apparatus gate — done, bounded at eight.** `record/harness_selftest.sh`, 8/8, exactly your list:
different CWD · missing artifact · undeclared artifact · no-op perturbation · deletion rather than
modification · wrong target · wrong diagnostic · a paired probe with one side broken. And it stopped
there, per your "don't create infinite tests of tests".

**The lowering spike — declared with your constraints, not built.** `record/grid-derivation-sections.json`
→ `lowering_spike`: pure fragment only (`const`/`input`/arithmetic/`len`, explicitly **not**
`read`/`scope`/`cite`), your three properties, your three separate identities
(`program_sem_id` / `lowering_id` / `target_term_sem_id`, with `program_sem_id` explicitly not
replaced), and a decision rule that permits the answer *no*.

---

## 2. The self-test caught three defects in its own first draft

Worth reporting because it is the only evidence that it works:

1. the scratch-battery builder split the real runner at the first line starting `run_case ` — which
   is the function **definition** — producing a meta-battery whose runner was undefined;
2. M-8's "silent repair" emptied the frozen `reads` table and **W-1 kept reproducing**, because W-1
   never performs a read: it reaches the grant table through the `input` op. A meta-case testing
   nothing is the exact thing the file exists to refuse, and it refused its own;
3. M-1 first asserted that all three directories produced a *passing* verdict rather than an
   *identical* one, so it failed on an unrelated version-lockstep error — a meta-case failing for a
   reason outside its own subject, which is itself one of the eight species. It now asserts identity.

---

## 3. Open, and what I'd ask this pass

1. **C-4 (footprint ordering).** Is declaring evaluation order in the core the right closure, or
   should the footprint be an order-independent structure (a sorted set of `[resource, version]`)
   with ordering kept only in a separate trace? Declaring the order is cheaper and makes the
   sequence part of the semantics; the alternative makes two correct-but-differently-ordered
   implementations agree without either being wrong. I took the first and am not certain.
2. **Does the frozen core need `sub`'s and `mul`'s overflow behaviour tested, or is
   `program-arith-non-finite` sufficient?** Currently one refusal covers all three ops, and I have
   only witnessed it on `add`.
3. **The lowering spike's target syntax.** "The same AST lowers to byte-identical target syntax"
   needs a target *notation* to be byte-identical in. Is that ic32's textual term syntax, or does
   the spike need a canonical serialization of the interaction-net term first — which would make it
   depend on the very thing (SEMSTATE-CANONICAL-v1 in C) the film round is supposed to deliver?
   That ordering question is the one thing in your sequence I could not resolve from the record.
4. **`acceptForeignResult` and the World's lock.** I stated the requirement rather than enforcing
   it, because enforcing would mean this module holding a lock token — a second authority. Is a
   lock-token *parameter* (the caller passes proof it holds the lock, the World validates) worth it,
   or is the stated requirement plus the World's own receipt machinery the right amount?
5. **Whether round 16 should have been two rounds.** It carries a breaking identity change, a new
   protocol phase, a new evidence question and a meta-gate. The record's habit is one theorem per
   round and I did not follow it.

---

## 4. Bundle contents

```
README.md                                   this file
code/                                       7 files, run standalone on Node ≥18
gate/                                       verbatim output, incl. runs from OUTSIDE the repo
record/CORE_SPEC.json                       the frozen core as it hashes
record/grid-derivation-sections.json        9 laws + derivation_language + lowering_spike + film_planes + roadmap
record/artifacts-derivation-boundary.json   claimed / not_claimed / three_questions / issuance
record/harness_selftest.sh                  the apparatus gate
record/negative-cases-round16.sh            the 9 new forgeries, each with its expected diagnostic
record/round-16-ledger-section.md           §64–§73
MANIFEST.sha256
```

**Gate:** grid v1.17.0 — 61 entries / 343 citations · `derive_protocol.mjs` 0.3.0 · kernel PASS ·
World 0.12.0 PASS · `--check-receipt` PASS · negative battery **85/85** · bridge 48/48 · derive
**30/30 · 10/10** · probes **2/2+2/2 · 4/4+5/5 · 5/5** · harness **8/8**.
`scheduler_certificate.json` byte-identical — `cert_id` unmoved, calculus untouched for an eleventh
consecutive round.


---

# APPENDIX — every file inlined

The zip is the same content. This single file exists so it can be pasted if an upload is refused.

## `code/derive_protocol.mjs`

```javascript
/* ═══════════════════════════════════════════════════════════════════════════
   derive_protocol.mjs — v0.3.0 — the serialized derivation boundary

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
export const PROTOCOL_VERSION = "0.3.0";

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
     evaluation order was free   the footprint is an ARRAY, so a right-to-left
                                 implementation returns a different — and
                                 therefore diverging — semantic projection

   A C implementation could satisfy every one of those differently and agree on
   program_sem_id, which is exactly the property the id exists to deny.

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
  evaluation_order: "depth-first, operands in declared field order: `a` fully evaluated before `b`. " +
    "read and scope append to the footprint AT ACCESS, so read_footprint is a SEQUENCE whose order " +
    "is part of the result — two implementations differing in evaluation order produce different " +
    "semantic projections and will diverge, by design.",
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
  "value", "witness", "support", "read_footprint"];
/** the portable half of a result: everything two implementations must agree on.
 *  implementation_id is deliberately OUT — two conforming implementations of
 *  the same program produce different executable provenance and identical
 *  semantics, and comparing whole results would make cross-implementation
 *  validation fail by construction. */
export const SEMANTIC_RESULT_FIELDS = RESULT_FIELDS.filter((f) => f !== "implementation_id");

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
export const JS_IMPLEMENTATION_ID = "impl-js-derive-v0.3.0";

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
  return {
    value,
    witness: { op: ast.op, reads: exact.length, scopes: predicates.length },
    support: [...new Set(support)].sort(),
    read_footprint: { exact, predicates },
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
    support: out.support, read_footprint: out.read_footprint,
  };
  const rr = checkResult(res, req);
  if (!rr.ok) return { ok: false, reason: rr.reason };
  return { ok: true, result: res };
}

/* ── FRESHNESS: a different question from containment ─────────────────────
   footprintWithinGrant answers a HISTORICAL question — was every claimed read
   inside the snapshot this derivation received? validateFootprintFresh answers
   a TEMPORAL one — are those dependencies still current NOW, at the moment of
   acceptance? Both can pass and the result still be uncommittable: executor and
   authority can agree perfectly about a snapshot the World has moved past. That
   witness is frozen in probe_stalegrant_v03_repro.mjs.

   It keys on the FOOTPRINT, never on a global vclock. An unrelated write must
   not invalidate a derivation that did not depend on it — that is the whole
   reason the footprint is the dependency record and the grant is not. */
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

/* ── ISSUANCE: grant_id proves integrity, NOT authority ───────────────────
   A caller can construct a read_grants of its own and a grant_id that matches
   it, because grant_id is a hash of content and a hash authenticates content to
   itself. v0.2.0's schema separated the grant from the inputs and did not
   separate the ISSUER from the caller — the same party did both, so the
   distinction was structural in the message and absent from the topology.

   The fix is topology, not crypto. A caller submits a DeriveIntent, which names
   what it WANTS to read; the authority resolves the snapshot and is the only
   party that constructs a DeriveRequest; and the authority remembers what it
   issued, so a request carrying a grant it did not cut is refused by name.

   A signature/MAC becomes necessary — and only then — when the grant crosses an
   actual trust boundary, is persisted and replayed later, is delegated between
   authorities, or must be proved to an independent verifier. Recorded so the
   crypto is added for a reason rather than for reassurance. */
const INTENT_REQUIRED = ["intent_id", "program_sem_id", "canonical_inputs", "requested_resources"];

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
  const rr = intent.requested_resources;
  if (rr === null || typeof rr !== "object" || Array.isArray(rr))
    return { ok: false, reason: "intent-requested-resources-not-an-object" };
  const rk = Object.keys(rr).sort();
  if (canonicalBytes(rk) !== canonicalBytes(["exact", "predicates"]))
    return { ok: false, reason: "intent-requested-resources-schema: [" + rk.join(",") + "]" };
  for (const kind of ["exact", "predicates"])
    if (!Array.isArray(rr[kind]) || rr[kind].some((x) => typeof x !== "string"))
      return { ok: false, reason: "intent-requested-" + kind + "-not-a-string-list" };
  return { ok: true };
}

/** The authority. It is the only constructor of a DeriveRequest in this API,
 *  and it remembers what it issued so acceptance can refuse a grant it did not
 *  cut. Deliberately NOT a signature: this closes the in-process topology, and
 *  the record names the four conditions under which crypto becomes required. */
export class GrantIssuer {
  #issued = new Map();
  #reader;
  constructor(reader) { this.#reader = reader; Object.freeze(this); }
  /** intent in, authority-issued request out */
  authorize(intent, over = {}) {
    const c = checkIntent(intent);
    if (!c.ok) return { ok: false, reason: c.reason };
    let g;
    try { g = resolveGrants(this.#reader, intent.requested_resources); }
    catch (e) { return { ok: false, reason: e.message }; }
    const req = {
      request_id: "req-" + H("TRVM-REQUEST-v1|" + intent.intent_id + "|" + g.grant_id),
      program_sem_id: intent.program_sem_id,
      canonical_inputs: intent.canonical_inputs,
      read_grants: g.read_grants, grant_id: g.grant_id, ...over,
    };
    const rc = checkRequest(req);
    if (!rc.ok) return { ok: false, reason: rc.reason };
    this.#issued.set(req.request_id, g.grant_id);
    return { ok: true, request: req };
  }
  wasIssued(request_id, grant_id) { return this.#issued.get(request_id) === grant_id; }
}
Object.freeze(GrantIssuer.prototype);

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

/** ACCEPTANCE — the whole gate a result must clear before it may be committed,
 *  in one call, in an order where each stage fails on its own evidence:
 *
 *    1. issuance   the grant is one THIS authority cut (topology, not crypto)
 *    2. validation schema, footprint-within-grant, re-derivation
 *    3. freshness  the footprint's dependencies are still live NOW
 *
 *  Freshness is LAST and deliberately inside the same call as the rest, because
 *  a freshness check that returns to the caller before the commit is a TOCTOU
 *  window — check, world moves, commit stale — which is the same species as the
 *  transaction defects rounds 9B–9D.4 spent six rounds removing.
 *
 *  THIS FUNCTION DOES NOT TAKE THE LOCK. It cannot: the World owns that, and a
 *  lock acquired here would be a second lock. The caller MUST hold the World's
 *  commit lock across this call and the commit that follows it, and the World's
 *  own receipt machinery is what proves it did. Stated rather than assumed. */
export function acceptForeignResult(registry, req, res, liveReader, issuer = null) {
  if (issuer && !issuer.wasIssued(req.request_id, req.grant_id))
    return { ok: false, reason: "grant-not-issued-by-this-authority" };
  const v = validateForeignResult(registry, req, res);
  if (!v.ok) return v;
  const f = validateFootprintFresh(liveReader, res.read_footprint);
  if (!f.ok) return { ok: false, reason: f.reason };
  return { ok: true, implementation_id: res.implementation_id, committable: true };
}
```

## `code/derive_worker.mjs`

```javascript
/* derive_worker.mjs — v0.3.0 — the far side of the realm boundary.
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
      request_id: req.request_id, program_sem_id: req.program_sem_id,
      implementation_id: JS_IMPLEMENTATION_ID, grant_id: req.grant_id,
      value: out.value, witness: out.witness, support: out.support,
      read_footprint: out.read_footprint } });
  } catch (e) { parentPort.postMessage({ ok: false, reason: "derivation-threw: " + e.message }); }
});
```

## `code/derive_battery.mjs`

```javascript
/* derive_battery.mjs — falsifiers for the serialized derivation boundary, v0.2.0.
   Written before the protocol is believed, per the house rule. Every case that
   must be refused asserts the EXACT refusal string, so a repair that changes
   what is refused cannot pass by refusing for a different reason.
   Run: node derive_battery.mjs   (exit 0 iff green) */
import {
  ProgramRegistry, programSemId, canonicalBytes, checkRequest, checkResult,
  deriveLocally, validateForeignResult, evaluate, resolveGrants, grantId,
  footprintWithinGrant, semanticProjection, JS_IMPLEMENTATION_ID,
  CORE_SPEC, CORE_SEM_ID, validateProgram, validateFootprintFresh,
  acceptForeignResult, GrantIssuer, checkIntent,
} from "./derive_protocol.mjs";
import { createHash } from "node:crypto";

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
  R("derivation-honest", r.ok && r.result.value === 5 && r2.ok && r2.result.value === 1005,
    `bias 0 -> ${r.ok && r.result.value}, bias 1000 -> ${r2.ok && r2.result.value}; the bias is an ` +
    `INPUT of the request, so it is visible in canonical_inputs instead of hiding in a lexical cell`);
  R("footprint-recorded", r.ok && canonicalBytes(r.result.read_footprint.exact) === canonicalBytes([["fb", 1]])
      && r.result.witness.reads === 1,
    `read_footprint.exact = ${JSON.stringify(r.ok && r.result.read_footprint.exact)} — reads are tracked ` +
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
  R("grant-not-reachable-as-input", r.ok && r.result.value === "an ordinary input"
      && r.result.read_footprint.exact.length === 0,
    `{op:"input",name:"__reads"} returns ${JSON.stringify(r.ok && r.result.value)} — at v0.1.0 it ` +
    `returned the entire authority grant table with witness.reads = 0. read_grants is a separate ` +
    `request field and the input op cannot address it (W-1, frozen in probe_derivegrant_v02_repro.mjs)`);

  // the grant may be WIDER than the footprint, and that is the point: freshness
  // keys on what was read, not on what was made available
  const wide = snapshot({ fb: 5, unused_a: 1, unused_b: 2 });
  const r2 = deriveLocally(reg, { request_id: "w", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, read_grants: wide.read_grants, grant_id: wide.grant_id });
  R("footprint-is-the-access-subset",
    r2.ok && Object.keys(wide.read_grants.exact).length === 3 && r2.result.read_footprint.exact.length === 1,
    `grant covers ${Object.keys(wide.read_grants.exact).sort().join(",")} (3 resources); the footprint ` +
    `records ${JSON.stringify(r2.result.read_footprint.exact)} (1). Defining the footprint AS the grant ` +
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
  const overclaim = validateForeignResult(reg, req, { ...honest,
    witness: { ...honest.witness, reads: 2 },
    read_footprint: { exact: [["fb", 1], ["secret:key", 1]], predicates: [] } });
  // version forgery: the right resource at a version the grant does not carry
  const wrongVer = validateForeignResult(reg, req, { ...honest,
    read_footprint: { exact: [["fb", 99]], predicates: [] } });
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
  const inconsistent = checkResult({ ...honest, witness: { op: "add", reads: 7, scopes: 0 } }, req);
  R("witness-matches-footprint", !inconsistent.ok && inconsistent.reason === "result-witness-inconsistent",
    `a result claiming 7 reads with a 1-entry footprint is refused: ${inconsistent.reason}`);
}

// ── 7. a foreign result is a CLAIM until the authority re-derives it ─────
{
  const req = mkReq();
  const honest = deriveLocally(reg, req).result;
  const good = validateForeignResult(reg, req, honest);
  const lied = validateForeignResult(reg, req, { ...honest, value: 1005 });
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
  R("implementation-id-asserted", honest.implementation_id === JS_IMPLEMENTATION_ID,
    `the result carries ${honest.implementation_id}, emitted by the evaluator that ran. At v0.1.0 the ` +
    `REQUEST carried implementation_id, nothing checked it and the result carried none (W-2)`);
  const demand = deriveLocally(reg, { ...req, expected_implementation_id: "impl-c-pretend-v9" });
  R("implementation-requirement-refused", !demand.ok
      && demand.reason === "implementation-mismatch: want impl-c-pretend-v9, this is " + JS_IMPLEMENTATION_ID,
    `a request demanding a C executor is refused BY the JS executor (${demand.reason}) — the caller's ` +
    `field states a requirement and the executor answers it, so impersonation has no path`);
  const malformed = checkResult({ ...honest, implementation_id: "js" }, req);
  R("implementation-id-well-formed", !malformed.ok && malformed.reason === "result-implementation-id-malformed",
    `a result whose implementation_id is not an impl- identity is refused: ${malformed.reason}`);

  // THE POINT OF THE SPLIT: a conforming foreign implementation validates, and
  // its provenance is reported rather than compared away. Comparing whole
  // results would make cross-implementation validation fail by construction.
  const asIfC = { ...honest, implementation_id: "impl-c-derive-v0.2.0" };
  const v = validateForeignResult(reg, req, asIfC);
  const sameSemantics = canonicalBytes(semanticProjection(asIfC)) === canonicalBytes(semanticProjection(honest));
  R("semantic-projection-is-portable", v.ok && v.implementation_id === "impl-c-derive-v0.2.0" && sameSemantics,
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

// ── 11. freshness is a DIFFERENT question from containment ──────────────
{
  const live = { res: { fb: { value: 5, version: 1 }, other: { value: 0, version: 1 } },
    read(r) { return { ...this.res[r] }; }, scope(q) { return "scope:" + q; } };
  const { read_grants, grant_id } = resolveGrants(live, { exact: ["fb"] });
  const req = { request_id: "f1", program_sem_id: PID, canonical_inputs: { bias: 0 }, read_grants, grant_id };
  const res = deriveLocally(reg, req).result;
  const freshBefore = validateFootprintFresh(live, res.read_footprint);
  live.res.fb = { value: 9, version: 2 };                 // the World moves
  const containment = footprintWithinGrant(res.read_footprint, req.read_grants);
  const rederive = validateForeignResult(reg, req, res);
  const freshAfter = validateFootprintFresh(live, res.read_footprint);
  R("freshness-is-not-containment",
    freshBefore.ok && containment.ok && rederive.ok
      && !freshAfter.ok && freshAfter.reason === "stale-read: fb granted@1 live@2",
    `after fb moves 1→2: footprintWithinGrant ${containment.ok ? "PASS" : containment.reason}, ` +
    `re-derivation ${rederive.ok ? "PASS" : rederive.reason} — both CORRECT about the snapshot — and ` +
    `freshness ${freshAfter.reason}. Containment is historical, freshness is temporal, and a protocol ` +
    `that stops at re-derivation commits a value the World has already contradicted`);
  live.res.fb = { value: 5, version: 1 };
  live.res.other = { value: 999, version: 2 };            // a write nothing read
  const unrelated = validateFootprintFresh(live, res.read_footprint);
  R("unrelated-write-does-not-invalidate", unrelated.ok,
    `other@1→2 moved and freshness still passes — it keys on the FOOTPRINT, never on a global vclock. ` +
    `A vclock rule would invalidate every derivation on every unrelated write, undoing the ` +
    `grant/footprint separation from the other side`);
}

// ── 12. issuance: grant_id proves integrity, the issuer proves authority ──
{
  const live = { res: { fb: { value: 5, version: 1 } }, read(r) { return { ...this.res[r] }; },
    scope(q) { return "scope:" + q; } };
  const issuer = new GrantIssuer(live);
  const intent = { intent_id: "i1", program_sem_id: PID, canonical_inputs: { bias: 0 },
    requested_resources: { exact: ["fb"], predicates: [] } };
  const a = issuer.authorize(intent);
  const res = deriveLocally(reg, a.request).result;
  const mine = acceptForeignResult(reg, a.request, res, live, issuer);
  const theirs = acceptForeignResult(reg, a.request, res, live, new GrantIssuer(live));
  R("issuance-is-not-content-identity",
    a.ok && mine.ok && mine.committable === true
      && !theirs.ok && theirs.reason === "grant-not-issued-by-this-authority",
    `the issuing authority accepts (committable ${mine.committable}); a different authority instance ` +
    `refuses the byte-identical request (${theirs.reason}). grant_id = H(read_grants) authenticates ` +
    `content to itself — a caller can build a grant AND a matching grant_id, so the hash proves ` +
    `integrity and says nothing about who cut it`);
  const badIntents = [
    ["extra field", { ...intent, sneak: 1 }, /intent-schema/],
    ["missing field", { intent_id: "x", program_sem_id: PID }, /intent-schema/],
    ["resources not lists", { ...intent, requested_resources: { exact: "fb", predicates: [] } }, /intent-requested-exact-not-a-string-list/],
    ["capability in inputs", { ...intent, canonical_inputs: { f: () => 1 } }, /not-canonical/],
  ];
  R("intent-schema-closed", badIntents.every(([, i, rx]) => { const c = checkIntent(i); return !c.ok && rx.test(c.reason); }),
    badIntents.map(([l, i]) => `${l}:${checkIntent(i).ok ? "ADMITTED" : "refused"}`).join(" ") +
    ` — the untrusted half of the two-phase protocol is validated as strictly as the authority's half`);
  R("authority-is-the-only-request-constructor",
    typeof issuer.authorize === "function" && a.request.grant_id === grantId(a.request.read_grants)
      && issuer.wasIssued(a.request.request_id, a.request.grant_id)
      && !issuer.wasIssued("req-self-made", a.request.grant_id),
    `authorize() resolves the snapshot from the live world and records what it issued; a self-chosen ` +
    `request_id is not in the table. A signature is NOT added here: it would authenticate the authority ` +
    `to itself. The named triggers are a real trust boundary, persistence and replay, delegation, or an ` +
    `independent verifier`);
}

console.log("═".repeat(96));
console.log(fail
  ? `DERIVE-BATTERY: FAIL — ${rows.filter((r) => !r.ok).length}/${rows.length}`
  : `DERIVE-BATTERY: PASS — ${rows.length}/${rows.length}. The program is data and its id commits the ` +
    `frozen core's semantics, not just its syntax; the grant is what the authority made available and ` +
    `the footprint is what the program consumed; containment is historical and freshness is temporal; ` +
    `the executor asserts its own identity; and issuance is a topology, not a hash.`);
process.exit(fail ? 1 : 0);
```

## `code/derive_realm_battery.mjs`

```javascript
/* derive_realm_battery.mjs — the crossing itself, v0.2.0.
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
  GrantIssuer, acceptForeignResult,
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
R("crossing-derives", honest.ok && honest.result.value === 5
    && honest.result.implementation_id === JS_IMPLEMENTATION_ID && honest.result.grant_id === grant_id,
  `worker returned value ${honest.ok && honest.result.value} for fb=5 bias=0, resolving the program from ` +
  `its OWN registry by id and stamping the result ${honest.ok && honest.result.implementation_id} against ` +
  `grant ${grant_id.slice(0, 18)}…`);

// 3. and the claim is only evidence once the authority re-derives it
{
  const req = mkReq();
  const local = validateForeignResult(reg, req, honest.result);
  const lied = validateForeignResult(reg, req, { ...honest.result, value: 1005 });
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
  R("grant-not-reachable-as-input", r.ok && r.result.value === "an ordinary input"
      && r.result.read_footprint.exact.length === 0 && r.result.witness.reads === 0,
    `the worker granted fb and secret:key returns ${JSON.stringify(r.ok && r.result.value)} for ` +
    `{op:"input",name:"__reads"} — at v0.1.0 this returned the whole grant table across the same ` +
    `boundary, with an empty footprint and zero tracked reads`);
  await w2.terminate();
}

// 7. the far side asserts its identity, and refuses a requirement it cannot meet
{
  const r = await ask(mkReq({ expected_implementation_id: "impl-c-pretend-v9" }));
  const ok2 = await ask(mkReq({ expected_implementation_id: JS_IMPLEMENTATION_ID }));
  R("executor-asserts-implementation", !r.ok && /implementation-mismatch: want impl-c-pretend-v9/.test(r.reason)
      && ok2.ok && ok2.result.implementation_id === JS_IMPLEMENTATION_ID,
    `a request demanding a C executor is refused by the JS worker (${r.reason}); one demanding JS runs ` +
    `and returns its own id. The caller states a requirement; the executor answers it`);
}

// 8. a forged footprint from the far side dies against the snapshot
{
  const req = mkReq();
  const forged = { ...honest.result, witness: { ...honest.result.witness, reads: 2 },
    read_footprint: { exact: [["fb", 1], ["secret:key", 1]], predicates: [] } };
  const v = validateForeignResult(reg, req, forged);
  R("foreign-footprint-refused", !v.ok && v.reason === "footprint-ungranted-read: secret:key",
    `${v.reason} — the authority checks the returned footprint against the grant it issued, on its own ` +
    `evidence. The footprint is the dependency record and the grant is the capability record; the ` +
    `round-14 prose collapsed them and the mechanism supported neither`);
}

// 9. a conforming foreign implementation validates on the semantic projection
{
  const req = mkReq();
  const asIfC = { ...honest.result, implementation_id: "impl-c-derive-v0.2.0" };
  const v = validateForeignResult(reg, req, asIfC);
  R("cross-implementation-shape", v.ok && v.implementation_id === "impl-c-derive-v0.2.0"
      && canonicalBytes(semanticProjection(asIfC)) === canonicalBytes(semanticProjection(honest.result)),
    `the same result stamped by a C executor validates and its provenance is RECORDED rather than ` +
    `compared away. This is the shape a real C implementation plugs into — it is not a claim that one ` +
    `exists, and this battery does not have one`);
}

// 10. the whole v0.3 path across the boundary: intent → authority → realm →
//     acceptance, and the same path with the World moving underneath it
{
  const live = { res: { fb: { value: 5, version: 1 } }, read(r) { return { ...this.res[r] }; },
    scope(q) { return "scope:" + q; } };
  const issuer = new GrantIssuer(live);
  const a = issuer.authorize({ intent_id: "i-realm", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const crossed = await ask(a.request);
  const accepted = acceptForeignResult(reg, a.request, crossed.result, live, issuer);
  live.res.fb = { value: 9, version: 2 };                 // the World moves after the crossing
  const stale = acceptForeignResult(reg, a.request, crossed.result, live, issuer);
  R("intent-to-acceptance", a.ok && crossed.ok && crossed.result.value === 5
      && accepted.ok && accepted.committable === true
      && !stale.ok && stale.reason === "stale-read: fb granted@1 live@2",
    `a caller's INTENT is authorized into a request by the authority, crosses to a realm holding no ` +
    `world, returns a claim, and is accepted (committable ${accepted.committable}) — then the same ` +
    `claim is refused once fb moves 1→2 (${stale.reason}). The worker never learns the World exists`);
}

await w.terminate();
console.log("═".repeat(96));
console.log(fail ? "DERIVE-REALM: FAIL"
  : "DERIVE-REALM: PASS — object authority does not cross the boundary, the realm reads only its grant, " +
    "and the executor names itself. Determinism and host confinement are SEPARATE scopes and are not claimed here.");
process.exit(fail ? 1 : 0);
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
   C-4  evaluation order was free.       read_footprint is an ARRAY appended at
        access, so a right-to-left implementation returns a different footprint
        for the same program — and therefore a diverging semantic projection.
        Order was load-bearing and unstated.

   PAIRED, like probe_derivegrant_v02_repro.mjs: each witness must still
   reproduce against the frozen copy and must be confined against live, and exit
   0 requires both. C-4 is the exception and says so — it is a witness that
   order MATTERS, not that v0.2.0 ordered wrongly. v0.2.0 evaluated `a` before
   `b` exactly as v0.3.0 does; what it lacked was any statement that it must.
   So C-4 is confined by the CORE_SPEC declaring the order, and the live half
   checks that the declaration is present and load-bearing in the id rather
   than that behaviour changed.
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
    `read_footprint is a SEQUENCE — ${JSON.stringify(fp)} — and a right-to-left implementation returns ` +
    `${JSON.stringify(rev)} for the same program. Different canonical bytes, therefore ` +
    `foreign-result-divergence between two implementations that compute the same value. v0.2.0 evaluated ` +
    `a-before-b and never said it had to; this witness is that ORDER MATTERS, not that v0.2.0 ordered wrongly`);
  const liveFp = liveEval(RD, grants, {}).read_footprint.exact;
  R("C-4 live", CORE_SPEC.evaluation_order.includes("`a` fully evaluated before `b`")
      && CORE_SPEC.evaluation_order.includes("SEQUENCE")
      && liveCanon(liveFp) === liveCanon(fp),
    `CORE_SPEC.evaluation_order states the order AND that the footprint is a sequence, and CORE_SEM_ID ` +
    `is inside program_sem_id — so an implementation ordering differently is a different core, not a ` +
    `disagreement about one program. Behaviour unchanged: ${JSON.stringify(liveFp)}`);
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
  ProgramRegistry, resolveGrants, checkResult, footprintWithinGrant,
  validateForeignResult, validateFootprintFresh, acceptForeignResult, deriveLocally,
  GrantIssuer, JS_IMPLEMENTATION_ID,
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
const issuer = new GrantIssuer(world);

const intent = { intent_id: "i-1", program_sem_id: PID, canonical_inputs: { bias: 0 },
  requested_resources: { exact: ["fb"], predicates: [] } };
const { request: req } = issuer.authorize(intent);
const res = deriveLocally(reg, req).result;

console.log(`grant ${req.grant_id.slice(0, 20)}… cut at fb@1=5 · derived value ${res.value} · ` +
  `footprint ${JSON.stringify(res.read_footprint.exact)}`);

/* ── the World moves under the derivation ─────────────────────────────────── */
world.write("fb", 9);
console.log(`World moved: fb is now @${world.res.fb.version}=${world.res.fb.value}\n`);

{
  const a = checkResult(res, req);
  const b = footprintWithinGrant(res.read_footprint, req.read_grants);
  const c = validateForeignResult(reg, req, res);
  R("v0.2.0-era checks", false,
    `checkResult ${a.ok ? "PASS" : a.reason} · footprintWithinGrant ${b.ok ? "PASS" : b.reason} · ` +
    `validateForeignResult ${c.ok ? "PASS" : c.reason} — all three CORRECT, and the value 5 is now wrong ` +
    `in a World where fb is 9. Re-derivation against the same snapshot can never notice this`);

  const f = validateFootprintFresh(world, res.read_footprint);
  R("live freshness", !f.ok && /^stale-read: fb granted@1 live@2/.test(f.reason),
    `${f.reason} — the temporal question, asked against the LIVE world and keyed on the footprint`);

  const acc = acceptForeignResult(reg, req, res, world, issuer);
  R("acceptance refuses", !acc.ok && /^stale-read: fb/.test(acc.reason),
    `${acc.reason} — issuance, validation and freshness in ONE call, so there is no window between ` +
    `the check and the commit for the World to move in`);
}

/* ── the negative half: an unrelated write must NOT invalidate ────────────── */
{
  world.res.fb = { value: 5, version: 1 };          // restore the granted state
  world.write("other", 999);                        // a write the derivation never read
  const acc = acceptForeignResult(reg, req, res, world, issuer);
  R("unrelated-write-ignored", acc.ok && acc.committable === true,
    `other@${world.res.other.version} moved and acceptance still passes (committable ${acc.committable}) — ` +
    `freshness keys on the FOOTPRINT, not on a global vclock. A vclock rule would invalidate every ` +
    `derivation on every unrelated write and quietly undo the grant/footprint separation`);
}

/* ── a scope whose result set moved, with no exact read touched ───────────── */
{
  const S = { op: "len", a: { op: "scope", query: "kind:node" } };
  const reg2 = new ProgramRegistry(); const SID = reg2.bind(S);
  const iss2 = new GrantIssuer(world);
  const { request: r2 } = iss2.authorize({ intent_id: "i-2", program_sem_id: SID,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: ["kind:node"] } });
  const s2 = deriveLocally(reg2, r2).result;
  world.scopes["kind:node"] = ["a", "b", "c"];       // the phantom: a node joins
  const acc = acceptForeignResult(reg2, r2, s2, world, iss2);
  R("scope-digest-staleness", !acc.ok && acc.reason === "stale-scope: kind:node",
    `${acc.reason} — value ${s2.value} was derived over 2 nodes and the query now answers 3, with no ` +
    `exact read having moved. This is the World's phantom-scope case (law:warrant.phantom-scope@1) ` +
    `reaching the derivation boundary`);
}

/* ── issuance: grant_id proves integrity, not authority ───────────────────── */
{
  const forged = { ...req, request_id: "req-self-made" };
  const acc = acceptForeignResult(reg, req, res, world, new GrantIssuer(world));
  const accForged = acceptForeignResult(reg, forged, { ...res, request_id: "req-self-made" }, world, issuer);
  R("grant-id-is-not-issuance", !acc.ok && acc.reason === "grant-not-issued-by-this-authority"
      && !accForged.ok && accForged.reason === "grant-not-issued-by-this-authority",
    `a DIFFERENT authority instance refuses the same well-formed request (${acc.reason}), and a ` +
    `self-made request_id is refused by the issuing one. grant_id = H(read_grants) authenticates ` +
    `content to itself and proves nothing about who cut it; the issuance table is what does`);
}

console.log("=".repeat(100));
const bad = results.filter((r) => r.id === "v0.2.0-era checks" ? r.held : !r.held);
console.log(`STALE-GRANT v0.3 WITNESS: ${results.filter((r) => r.id !== "v0.2.0-era checks" && r.held).length}/5 ` +
  `hold; the three v0.2.0-era checks pass on a stale result BY DESIGN, which is the finding` +
  (bad.length ? ` — FAILURES: ${bad.map((r) => r.id).join(", ")}` : ""));
process.exit(bad.length ? 1 : 0);
```

## `code/probe_derivegrant_v02_repro.mjs`

```javascript
/* ═══════════════════════════════════════════════════════════════════════════
   probe_derivegrant_v02_repro.mjs — the two defects in DERIVE-v0.1.0, frozen.

   Round 14 shipped the serialized derivation boundary and wrote two sentences
   about it that the mechanism did not support. External review supplied a
   witness for each; both reproduced here verbatim before anything was changed.

   W-1  THE READ FOOTPRINT WAS BYPASSABLE.
        The worker sourced its read table from `req.canonical_inputs.__reads`,
        and the language has `{op:"input", name:…}`, which retrieves ANY
        canonical input. So the one-node program {op:"input", name:"__reads"}
        returns the entire authority-supplied read table with witness.reads = 0,
        support = [] and read_footprint = {exact:[],predicates:[]}. The round-14
        ledger's claim — "the footprint is now the authority's record of what it
        read on the derivation's behalf" — describes a mechanism that did not
        exist: nothing forced a consumed read to be a TRACKED read.

   W-2  implementation_id WAS DECORATION.
        DeriveRequest carried it, no executor checked it, and DeriveResult did
        not carry it at all. A request asserting `impl-c-pretend-v9` was executed
        by the JavaScript evaluator and returned success. The grid's own
        film_identity_forward_declaration makes implementation_id the executable
        provenance half of the film identity split; a field the caller asserts
        and no one verifies cannot carry provenance.

   WHY THIS PROBE GATES, WHERE ITS SIBLINGS DOCUMENT
   ─────────────────────────────────────────────────
   probe_closureenv / probe_realm_9d2 / probe_ownfailopen freeze a boundary that
   is declared open, so they report a breach and that is the record. These two
   defects ARE repaired, so this probe runs each witness TWICE — against the
   frozen v0.1.0 copy below, where it must still breach, and against the live
   modules, where it must be confined. Exit 0 requires both directions.

   That is law:evidence.instrument-nonvacuity@1 applied to a repro: a witness
   that stops reproducing against the version it was written for has stopped
   measuring, and six apparatus failures across four rounds were exactly that.
   A one-directional probe here would pass just as happily if the frozen copy
   were replaced with the repaired one.

   The frozen copy is embedded as a data: URL and run in a REAL worker_threads
   realm, because W-1 is a defect in the worker's reader wiring rather than in
   the shared evaluator — the in-process path took a reader argument and never
   had it. Nothing is written to the artifact tree.
   ═══════════════════════════════════════════════════════════════════════════ */
import { Worker } from "node:worker_threads";
import {
  ProgramRegistry as LiveRegistry, JS_IMPLEMENTATION_ID as LIVE_IMPL, grantId as liveGrantId,
} from "./derive_protocol.mjs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "CONFINED" : "BREACH  "}  ${id.padEnd(34)} ${note}`); };

/* ── DERIVE-v0.1.0, VERBATIM ──────────────────────────────────────────────
   derive_protocol.mjs and derive_worker.mjs as shipped in commit 5b25a08,
   concatenated so the worker resolves nothing from the repository. Do not
   "fix" anything in this string: its job is to keep failing. */
const FROZEN_V010 = `
import { parentPort, workerData } from "node:worker_threads";
import { createHash } from "node:crypto";
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
    if (Array.isArray(v)) {
      out = "[" + v.map((x, i) => canonicalBytes(x, path + "[" + i + "]", onPath)).join(",") + "]";
    } else if (Object.getPrototypeOf(v) === Object.prototype || Object.getPrototypeOf(v) === null) {
      const keys = Object.keys(v).sort();
      out = "{" + keys.map((k) => JSON.stringify(k) + ":" +
        canonicalBytes(v[k], path + "." + k, onPath)).join(",") + "}";
    } else {
      throw new Error("not-canonical: non-plain object at " + path);
    }
    onPath.delete(v);
    return out;
  }
  throw new Error("not-canonical: " + t + " at " + path);
}
const OPS = {
  const: (n) => n.value,
  add: (n, ev) => ev(n.a) + ev(n.b),
  sub: (n, ev) => ev(n.a) - ev(n.b),
  mul: (n, ev) => ev(n.a) * ev(n.b),
  len: (n, ev) => { const v = ev(n.a); if (!Array.isArray(v)) throw new Error("program-type: len of non-array"); return v.length; },
};
function programSemId(ast) { return "psem-" + H("TRVM-PROGRAM-v1|" + canonicalBytes(ast)); }
function deepFreeze(v) {
  if (v === null || typeof v !== "object" || Object.isFrozen(v)) return v;
  Object.freeze(v);
  for (const k of Object.keys(v)) deepFreeze(v[k]);
  return v;
}
class ProgramRegistry {
  #byId = new Map();
  constructor() { Object.freeze(this); }
  bind(ast) {
    const id = programSemId(ast);
    const frozen = JSON.parse(canonicalBytes(ast));
    deepFreeze(frozen);
    this.#byId.set(id, frozen);
    return id;
  }
  get(id) { return this.#byId.get(id); }
  verify(id) {
    const ast = this.#byId.get(id);
    if (!ast) return { ok: false, reason: "program-unknown" };
    return programSemId(ast) === id ? { ok: true } : { ok: false, reason: "program-id-mismatch" };
  }
}
const REQUEST_FIELDS = ["request_id", "program_sem_id", "implementation_id", "canonical_inputs", "grants"];
function checkRequest(req) {
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
function evaluate(ast, reader, inputs = {}) {
  const exact = [], predicates = [], support = [];
  const ev = (n) => {
    if (n === null || typeof n !== "object" || typeof n.op !== "string")
      throw new Error("program-malformed-node");
    switch (n.op) {
      case "const": return OPS.const(n);
      case "input": {
        if (!Object.prototype.hasOwnProperty.call(inputs, n.name))
          throw new Error("program-input-missing: " + n.name);
        return inputs[n.name];                       // <<< W-1 LIVES HERE: any canonical input
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
  return { value, witness: { op: ast.op, reads: exact.length },
    support: [...new Set(support)].sort(), read_footprint: { exact, predicates } };
}

/* derive_worker.mjs v0.1.0, verbatim */
const reg = new ProgramRegistry();
for (const ast of workerData.programs) reg.bind(ast);
parentPort.on("message", (req) => {
  const c = checkRequest(req);
  if (!c.ok) { parentPort.postMessage({ ok: false, reason: c.reason }); return; }
  const v = reg.verify(req.program_sem_id);
  if (!v.ok) { parentPort.postMessage({ ok: false, reason: v.reason }); return; }
  const ast = reg.get(req.program_sem_id);
  const reads = req.canonical_inputs.__reads ?? {};   // <<< W-1: the grant table IS an input
  const reader = {
    read: (r) => { if (!(r in reads)) throw new Error("read-not-granted: " + r); return reads[r]; },
    scope: (q) => { if (!(q in reads)) throw new Error("scope-not-granted: " + q); return reads[q].value; },
  };
  try {
    const out = evaluate(ast, reader, req.canonical_inputs);
    parentPort.postMessage({ ok: true, result: {                 // <<< W-2: no implementation_id
      request_id: req.request_id, program_sem_id: req.program_sem_id,
      value: out.value, witness: out.witness, support: out.support,
      read_footprint: out.read_footprint } });
  } catch (e) { parentPort.postMessage({ ok: false, reason: "derivation-threw: " + e.message }); }
});
`;

const frozenURL = new URL("data:text/javascript," + encodeURIComponent(FROZEN_V010));
const spawn = (src, programs) => {
  const w = src === "frozen"
    ? new Worker(frozenURL, { workerData: { programs } })
    : new Worker(join(HERE, "derive_worker.mjs"), { workerData: { programs } });
  return { w, ask: (req) => new Promise((res) => { w.once("message", res); w.postMessage(req); }) };
};

/* ── W-1 against the frozen v0.1.0: the read table is reachable as an input ── */
const EXFIL = { op: "input", name: "__reads" };
{
  const { w, ask } = spawn("frozen", [EXFIL]);
  const pid = "psem-" + (await import("node:crypto")).createHash("sha256")
    .update('TRVM-PROGRAM-v1|{"name":"__reads","op":"input"}').digest("hex");
  const r = await ask({
    request_id: "w1", program_sem_id: pid, implementation_id: "impl-js-derive-v0.1.0",
    canonical_inputs: { __reads: { "secret:key": { value: 42, version: 7 } } }, grants: [],
  });
  const got = r.ok ? r.result.value?.["secret:key"]?.value : null;
  const tracked = r.ok ? r.result.read_footprint.exact.length : -1;
  R("W-1 frozen-v0.1.0", !(got === 42 && tracked === 0),
    `program {op:"input",name:"__reads"} returned the whole grant table (secret:key = ${got}) ` +
    `with witness.reads = ${r.ok && r.result.witness.reads}, support = ${JSON.stringify(r.ok && r.result.support)}, ` +
    `read_footprint.exact = ${JSON.stringify(r.ok && r.result.read_footprint.exact)} — ` +
    `a read that consumed authority data and produced no dependency record`);
  await w.terminate();
}

/* ── W-2 against the frozen v0.1.0: the caller names the executor ─────────── */
{
  const P = { op: "const", value: 1 };
  const { w, ask } = spawn("frozen", [P]);
  const pid = "psem-" + (await import("node:crypto")).createHash("sha256")
    .update('TRVM-PROGRAM-v1|{"op":"const","value":1}').digest("hex");
  const r = await ask({
    request_id: "w2", program_sem_id: pid, implementation_id: "impl-c-pretend-v9",
    canonical_inputs: {}, grants: [],
  });
  R("W-2 frozen-v0.1.0", !(r.ok && !("implementation_id" in r.result)),
    `a request asserting implementation_id "impl-c-pretend-v9" was executed by the JS evaluator ` +
    `and returned ok=${r.ok}; the result carries no implementation_id at all ` +
    `(fields: ${r.ok ? Object.keys(r.result).sort().join(",") : "—"}) — nothing to verify against`);
  await w.terminate();
}

/* ── the same two witnesses against the LIVE modules ──────────────────────── */
{
  const reg = new LiveRegistry(); const pid = reg.bind(EXFIL);
  const { w, ask } = spawn("live", [EXFIL]);
  const grants = { exact: { "secret:key": { value: 42, version: 7 } }, predicates: {} };
  const r = await ask({
    request_id: "w1b", program_sem_id: pid, canonical_inputs: { __reads: "not the grant table" },
    read_grants: grants, grant_id: liveGrantId(grants),
  });
  R("W-1 live", r.ok && r.result.value === "not the grant table",
    `the same program now returns only what the CALLER put in canonical_inputs ` +
    `(${JSON.stringify(r.ok ? r.result.value : r.reason)}); read_grants is a separate field the ` +
    `input op cannot address, so the grant table is not reachable without a tracked read`);
  await w.terminate();
}
{
  const P = { op: "const", value: 1 };
  const reg = new LiveRegistry(); const pid = reg.bind(P);
  const { w, ask } = spawn("live", [P]);
  const grants = { exact: {}, predicates: {} };
  const base = { request_id: "w2b", program_sem_id: pid, canonical_inputs: {},
    read_grants: grants, grant_id: liveGrantId(grants) };
  const honest = await ask(base);
  const impersonated = await ask({ ...base, expected_implementation_id: "impl-c-pretend-v9" });
  R("W-2 live", honest.ok && honest.result.implementation_id === LIVE_IMPL
      && !impersonated.ok && /implementation-mismatch/.test(impersonated.reason),
    `the executor asserts its own id (${honest.ok && honest.result.implementation_id}); a request ` +
    `demanding "impl-c-pretend-v9" is refused by the executor itself (${impersonated.reason}) ` +
    `— the caller's field is a REQUIREMENT, the result's field is an ASSERTION`);
  await w.terminate();
}

console.log("=".repeat(100));
const frozenHeld = results.filter((r) => r.id.includes("frozen") && r.held);
const liveBreached = results.filter((r) => r.id.includes("live") && !r.held);
const bad = frozenHeld.length + liveBreached.length;
console.log(
  `DERIVE-GRANT-v0.2 REPRO: ${results.filter((r) => r.id.includes("frozen") && !r.held).length}/2 reproduce against ` +
  `the frozen v0.1.0 · ${results.filter((r) => r.id.includes("live") && r.held).length}/2 confined against live` +
  (frozenHeld.length ? ` — VACUOUS: ${frozenHeld.map((r) => r.id).join(", ")} no longer reproduces, so it has stopped measuring` : "") +
  (liveBreached.length ? ` — REGRESSION: ${liveBreached.map((r) => r.id).join(", ")}` : ""));
process.exit(bad ? 1 : 0);
```

## `record/CORE_SPEC.json`

```json
{
 "CORE_SEM_ID": "core-06485b250ac283ffe831c575c8c698a7dfefb31c776babd2bfbd1467099fb036",
 "PROTOCOL_VERSION": "0.3.0",
 "JS_IMPLEMENTATION_ID": "impl-js-derive-v0.3.0",
 "CORE_SPEC": {
  "language": "TRVM-DERIVE-CORE",
  "version": 1,
  "value_domain": "null | boolean | finite number | string | canonical array | canonical plain object. Non-finite numbers, cycles, and non-plain objects (Map, Set, Date, class instances, transferable handles) are not values and are refused wherever they appear.",
  "numbers": "IEEE-754 binary64. Every arithmetic OPERAND must be a number — there is no coercion, no string concatenation and no object stringification — and every arithmetic RESULT must be finite. Overflow is a refusal at the operation, not a non-finite value handed onward.",
  "evaluation_order": "depth-first, operands in declared field order: `a` fully evaluated before `b`. read and scope append to the footprint AT ACCESS, so read_footprint is a SEQUENCE whose order is part of the result — two implementations differing in evaluation order produce different semantic projections and will diverge, by design.",
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

## `record/grid-derivation-sections.json`

```json
{
 "_note": "Extracted from TRVM/governance/invariant-grid.json v1.17.0 — derivation-relevant sections only.",
 "grid_version": "1.17.0",
 "law_registry_derivation_entries": [
  {
   "id": "evidence.instrument-nonvacuity",
   "revision": 1,
   "status": "PROPERTY-TESTED",
   "canonical": true,
   "statement": "An audit result is creditable only if the instrument independently proves that the intended perturbation occurred, the intended execution path was exercised, and the measured predicate is the one reported. A falsifier that forges nothing, runs nothing, or measures a different predicate than it names is VACUOUS, and a vacuous falsifier is worse than an absent one because the roster still counts it. Mutation cases must show before_hash != after_hash before the detector's verdict counts.",
   "evidence": "negative_battery.sh computes a pre- and post-perturbation digest of every scratch tree and refuses to credit a case whose forgery changed nothing (diagnostic: VACUOUS). This law is retrospective as much as prospective: it covers the unset $SCRATCH that meant a case could never execute, the hand-typed 44/44 that stopped counting the cases, the hard-coded \"1.0.2\" replacement that a version bump would have turned into a no-op, the prototype half of the authority graph that went untested, the false '9D-4 confined' produced by poisoning a node whose semantic path the pass overwrote, and a probe line that printed 'directly assignable' while testing typeof === 'function'. Six apparatus failures across four rounds, every one of which this rule would have caught mechanically. MECHANISED (both runners, v1.14.0): clause 1 — the intended target is DERIVED from the perturbation script (files opened for writing, files removed) and must EQUAL the set that actually changed, so a case editing the wrong artifact, or an extra one, fails as loudly as one editing nothing; clauses 2-3 — per-file digests before and after, refusing VACUOUS and naming the artifact perturbed; clause 5 — the specific diagnostic must match; clause 6 — CAUGHT increments only after all of the above. Both detectors were verified to FIRE by deliberately breaking a case (VACUOUS: 57/58; TARGET MISMATCH: 63/64) and restoring it. STILL DECLARED OPEN: clause 4, independent evidence that the intended EXECUTION PATH ran — the diagnostic match is a weak proxy, and the false '9D-4 confined' result came from a witness that never entered the semantic path it was written for. Closing it needs the verifier to report which rules it evaluated, not merely which one failed."
  },
  {
   "id": "derivation.environment-confinement",
   "revision": 1,
   "status": "FALSIFIED",
   "canonical": true,
   "statement": "A derivation's authority must be bounded by what the coordinator can own. Under the current same-realm arbitrary-closure measureFn API it is NOT, and this law is FALSIFIED BY DESIGN rather than repaired: capturing an arbitrary callable does not capture its semantics, and a function reference may retain mutable authority that is neither enumerable nor ownable. The witness needs no mutable object at all — a `let bias = 0` shared by two closures. Object.freeze, deepFreeze, structuredClone, canonicalBytes, #private fields, GuardedStore and the pass-entry snapshot are all INAPPLICABLE, because JavaScript provides no mechanism to enumerate, copy, canonicalize or freeze a captured lexical environment; freezing measureFn itself does not help either. A second theorem fails with it: derivation_id is computed from measure/predicate/inputs and therefore does NOT identify a derivation's semantics — the witness holds derivation_id constant while behaviour changes from fb to fb+1000. Tolerable as an acknowledged limit of the closure API; NOT tolerable once semantic films assert that an identified program performed a particular transition. Closure is by REPLACING the API, not by hardening it: see realm_roadmap.",
   "evidence": "probe_closureenv_repro.mjs against World 0.11.0 — B is support_changed and re-derives to 1005 where an honest B is 5, in both the coordinator and the World, with derivation_id unchanged and the pass not aborted. Frozen and deliberately NOT gated: the probe exits 0 because it documents a boundary rather than a regression. Four ownership rounds (9D.1 raw maps and caller objects, 9D.2 nested values, 9D.3 fail-open ownership, and this) converged on the conclusion that an arbitrary closure is an unbounded capability container — an architectural boundary, not a missing Object.freeze."
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
   "revision_note": "kept as history. @2 said program_sem_id 'cannot be a caller-selected label' and that 'the same program has the same id under every conforming implementation' — both true of the SYNTAX and neither established for the SEMANTICS, because the id was H('TRVM-PROGRAM-v1|' + canonical AST) over an unfrozen language. Four behaviours could differ behind one id and all four were reproduced: add was JavaScript '+', bind() validated nothing, arity and field sets were unconstrained, and evaluation order was free while the footprint is an ordered sequence. Frozen as C-1..C-4 in probe_coresem_v03_repro.mjs."
  },
  {
   "id": "derivation.serialized-boundary",
   "revision": 3,
   "status": "PROPERTY-TESTED",
   "canonical": true,
   "supersedes": "derivation.serialized-boundary@2",
   "statement": "A derivation crosses an authority boundary as DATA or not at all, and its identity commits the SEMANTICS of the language it is written in. program_sem_id = H('TRVM-PROGRAM-v2' | core_sem_id | canonical AST), where core_sem_id = H(canonical TRVM-DERIVE-CORE specification) — so a caller cannot select an id, an id cannot be rebound, AND an implementation cannot assign different meaning to an operation while agreeing on the id: a different core is a different program. The grammar is validated BEFORE an id is issued, so no identity exists for a program outside the language. The message domain is TRVM's canonical value domain, never 'structuredClone succeeded'. The derivation realm holds no world reference and reads ONLY its grant snapshot, addressed through read/scope and never through input. A result produced on the far side is a CLAIM; it becomes evidence only when the authority validates its footprint against the grant it issued and re-derives the semantic projection — every field but implementation_id — to the same canonical bytes.",
   "evidence": "derive_battery.mjs 30/30 in-process and derive_realm_battery.mjs 10/10 across a real worker_threads boundary, plus probe_coresem_v03_repro.mjs 4/4 frozen and 5/5 live. The decisive confinement result is still empirical: posting a request carrying a closure throws DataCloneError, so the 9D.4 lexical-cell attack has NO TRANSPORT. SCOPE: object confinement only. Determinism of a long-lived evaluator and host confinement are separate scopes, unclaimed here."
  },
  {
   "id": "derivation.core-semantics",
   "revision": 1,
   "status": "REGRESSION-LOCKED",
   "canonical": true,
   "statement": "TRVM-DERIVE-CORE-v1 is FROZEN and its identity is content-bound. The record declares the grammar (every node's key set is exactly {op} union the op's declared fields), the value domain, arithmetic (IEEE-754 binary64, no coercion — operands must be numbers and results must be finite, overflow refused AT the operation), evaluation order (depth-first, `a` before `b`), the fact that read_footprint is an ordered SEQUENCE appended at access and therefore part of the result, totality (no recursion, no loop, no general function), and the exact refusal vocabulary. core_sem_id = H(canonical CORE_SPEC) rather than the label 'TRVM-DERIVE-CORE-v1', because a bare name is precisely the caller-selected identity the primitive ruling already refuses for 'componentReachability'. Changing what add means moves core_sem_id and therefore every program_sem_id, which is the property that makes the identity semantic rather than syntactic. A prim extension bumps the core version and every program id with it: a program written against a different language is a different program.",
   "evidence": "probe_coresem_v03_repro.mjs — C-1 (add was JavaScript '+': \"2\"+\"3\" = \"23\", []+{} = \"[object Object]\", 1e308+1e308 = Infinity, all under one program_sem_id), C-2 ({op:'exec', cmd:'rm -rf /'} was issued an id), C-3 (const-without-value, add-without-b and add-with-an-extra-field were all issued ids), C-4 (the footprint is a sequence, so a right-to-left implementation returns different canonical bytes for the same program) — 4/4 reproduce against the frozen v0.2.0 copy and 5/5 are confined live. derive_battery.mjs: core-id-is-content-bound, program-id-commits-the-core, grammar-refuses-before-id (6 malformed programs), arithmetic-typed-and-total. BREAKING BY DESIGN: every v0.2.0 program id is retired. Done now precisely because no second implementation exists to be broken by it, which is the only moment it is cheap."
  },
  {
   "id": "derivation.footprint-freshness",
   "revision": 1,
   "status": "PROPERTY-TESTED",
   "canonical": true,
   "statement": "Containment and freshness are different questions and a protocol needs both. footprintWithinGrant asks a HISTORICAL question — was every claimed read inside the snapshot this derivation received? validateFootprintFresh asks a TEMPORAL one — are those dependencies still current at the moment of acceptance? Both can be satisfied about a World that has moved, so re-derivation against the grant can never detect staleness: executor and authority agree perfectly about an old snapshot. Freshness keys on the FOOTPRINT and never on a global vclock — an unrelated write must not invalidate a derivation that did not depend on it, or the grant/footprint separation is undone from the other side. Exact reads compare versions; scope predicates compare digests, which is the World's phantom-scope case reaching the derivation boundary. Acceptance — issuance, validation, freshness — is ONE call, because a freshness check that returns to the caller before the commit is a TOCTOU window of the same species as the transaction defects rounds 9B-9D.4 removed. The caller MUST hold the World's commit lock across acceptance and commit; acceptForeignResult does not and cannot take that lock, and says so.",
   "evidence": "probe_stalegrant_v03_repro.mjs: grant cut at fb@1=5, derived, World moved to fb@2=9 — checkResult PASS, footprintWithinGrant PASS, validateForeignResult PASS, all three CORRECT, and live freshness refuses 'stale-read: fb granted@1 live@2'. Plus the negative half (unrelated-write-ignored: other@1->2 moves and acceptance still passes) and the scope half (stale-scope: kind:node, a node joining a query with no exact read moving). derive_battery.mjs: freshness-is-not-containment, unrelated-write-does-not-invalidate. derive_realm_battery.mjs: intent-to-acceptance, the same claim accepted then refused once the World moves."
  },
  {
   "id": "derivation.grant-issuance",
   "revision": 1,
   "status": "PROPERTY-TESTED",
   "canonical": true,
   "statement": "grant_id proves INTEGRITY and not AUTHORITY. It is a hash of content, and a hash authenticates content to itself: a caller can construct a read_grants of its own together with a matching grant_id. v0.2.0 separated the grant from the inputs in the MESSAGE and did not separate the issuer from the caller in the TOPOLOGY, because the same party did both. The fix is topology, not crypto: a caller submits a DeriveIntent naming what it wants to read; the authority resolves the snapshot and is the only constructor of a DeriveRequest; and the authority records what it issued, so a request carrying a grant it did not cut is refused grant-not-issued-by-this-authority. A signature or MAC is added when — and only when — the grant crosses a real trust boundary, is persisted and replayed later, is delegated between authorities, or must be proved to an independent verifier. Adding one now would authenticate the authority to itself.",
   "evidence": "derive_battery.mjs: issuance-is-not-content-identity (the issuing authority accepts; a different GrantIssuer instance refuses the byte-identical request), intent-schema-closed (4 malformed intents, including a callable in canonical_inputs), authority-is-the-only-request-constructor. probe_stalegrant_v03_repro.mjs: grant-id-is-not-issuance. derive_realm_battery.mjs: intent-to-acceptance end to end."
  },
  {
   "id": "evidence.harness-selftest",
   "revision": 1,
   "status": "REGRESSION-LOCKED",
   "canonical": true,
   "statement": "The apparatus is measured by a gate, not by attention. law:evidence.instrument-nonvacuity@1 requires each falsifier to be non-vacuous; this requires the HARNESS ITSELF to demonstrate that it detects the failure species that have actually occurred in this tree. Eight are enumerated and each has a meta-falsifier that breaks an instrument deliberately and requires the harness to say so: working-directory dependence, an absent declared artifact, a present undeclared artifact, a perturbation that changes nothing, a case that DELETES rather than modifies, a case that moves an artifact it did not declare, a case whose expected diagnostic is not the one produced, and a paired probe whose frozen side has been silently repaired. Deliberately BOUNDED: this encodes the known failure species and does not recurse into tests of tests.",
   "evidence": "harness_selftest.sh, 8/8. The motivating record is five consecutive rounds in which the instrument rather than the engine was wrong: the unset $SCRATCH, the hand-typed 44/44, the hard-coded \"1.0.2\" version forgery, the probe line printing 'directly assignable' while testing typeof, the false '9D-4 confined' from a witness that never entered its path, a non-vacuity law registered one round before its harness implemented it, a one-sided diff that called a deleting case vacuous, and round 15's two CWD-relative reads — one of which scanned the empty string and reported success. The self-test caught two defects in its own first draft (a header split that captured the run_case DEFINITION, and an M-8 repair that did not neutralise the witness it was meant to neutralise), which is the behaviour it exists to have."
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
  "frozen": "TRVM-DERIVE-CORE-v1 is FROZEN as of round 16 — grammar, value domain, arithmetic, evaluation order, footprint ordering, totality and refusal vocabulary — and its identity is content-bound (core_sem_id = H(canonical CORE_SPEC)), load-bearing inside every program_sem_id. See law:derivation.core-semantics@1."
 },
 "lowering_spike": {
  "status": "DECLARED, not built",
  "scope": "the PURE fragment only — const, input, add/sub/mul, possibly len. NOT read/scope/cite: authority-sensitive operations carry footprint semantics that would muddy the question the spike exists to answer.",
  "shape": "Derive AST P --canonical lower-v0--> TRVM term T --ic32--> normal form / decoded value, compared against evaluate_JS(P, inputs).",
  "three_properties": [
   "the same AST lowers to byte-identical target syntax",
   "JS and ic32 decode to the same value",
   "the resulting ic32 execution emits and replays an ordinary TRVM transition film"
  ],
  "identities_stay_separate": "program_sem_id (identity of the source semantic program), lowering_id (identity/version of the lowering relation) and target_term_sem_id (identity of the resulting TRVM term) are three identities, not one. program_sem_id must NOT be replaced by the lowered term's id. Keeping them distinct is what makes 'program_sem_id --lowering_id--> target_term_sem_id' an actual refinement statement rather than a renaming.",
  "decision_rule": "if the spike is clean, lowering into ic32 is preferred over a second dedicated C interpreter beside it — one execution substrate rather than two. If the mapping is awkward, it is not adopted. The point of a spike is that it can fail."
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
   "freeze TRVM-DERIVE-CORE-v1 and make the semantic namespace load-bearing in program_sem_id (done, round 16)",
   "live-footprint freshness at acceptance, inside the commit boundary (done, round 16)",
   "DeriveIntent/authorize: grant_id is integrity, the issuer is authority (done, round 16)",
   "a gate for the apparatus itself (done, round 16)",
   "a tiny PURE lowering spike: const/input/arithmetic only, no read/scope/cite, proving byte-identical target syntax and equal decoded values before committing to the architecture",
   "native ic32 semantic-film emission against the existing §10/§10.5 contract, starting with C — NOT gated on the derivation language, see film_planes",
   "cross-replay: ic32 C film -> JS kernel, JS film -> C checker",
   "the first named semantic primitive (component reachability), per derivation_language",
   "measured implementation provenance: the trusted launcher hashes what it launches",
   "root release identity",
   "physical governance subdivision",
   "Zig/Mojo/WASM",
   "worker object confinement strengthened to host/process confinement"
  ],
  "sequencing_correction": "The previous order read 'that same program as the first C<->JS film / cross-replay witness', which conflated the two transition systems now separated in film_planes. Cross-replay of the DERIVATION AST is a different theorem from cross-replay of the ic32 REWRITE RELATION, and the pack-v3 film gap is the latter. The film round proceeds on the existing conformance contract and does not wait for the derivation language to grow."
 },
 "changelog_from_1_16_0": [
  "TRVM-DERIVE-CORE-v1 FROZEN and content-bound: core_sem_id = H(canonical CORE_SPEC) is inside every program_sem_id, so an implementation assigning different meaning to add, to evaluation order or to numeric behaviour is a different core rather than a disagreement about one program. Every v0.2.0 program id is retired, deliberately, while no second implementation exists.",
  "grammar validated BEFORE an id is issued — v0.2.0 gave {op:'exec', cmd:'rm -rf /'} a program_sem_id.",
  "arithmetic is typed and total: no coercion (v0.2.0's add was JavaScript '+', so \"2\"+\"3\" was \"23\"), and a non-finite result is refused at the operation.",
  "new law derivation.footprint-freshness@1: containment is historical, freshness is temporal, both are required, freshness keys on the footprint and never on a global vclock, and acceptance is one call because a returned freshness check is a TOCTOU window.",
  "new law derivation.grant-issuance@1: grant_id proves integrity, the issuer proves authority. DeriveIntent/GrantIssuer.authorize is the two-phase fix, and the four conditions that would require a signature are named rather than the crypto being added for reassurance.",
  "new law evidence.harness-selftest@1 and harness_selftest.sh, 8/8: the eight apparatus failure species that have actually occurred here now have meta-falsifiers. It caught two defects in its own first draft.",
  "serialized-boundary@2 superseded by @3.",
  "lowering_spike declared: the PURE fragment only, three properties, three separate identities, and an explicit decision rule that permits the answer 'no'."
 ],
 "artifact_versions": {
  "trvm_law_kernel.mjs": "1.1.0",
  "trvm_world.mjs": "0.12.0",
  "derive_protocol.mjs": "0.3.0"
 }
}
```

## `record/artifacts-derivation-boundary.json`

```json
{
 "derivation_boundary": {
  "status": "v0.3.0 — protocol proven in-process and across a worker; NOT yet the production derivation path",
  "files": {
   "derive_protocol.mjs": "program-as-data over a FROZEN core (TRVM-DERIVE-CORE-v1, content-bound core_sem_id inside every program_sem_id), canonical request/result schemas, authority grants separated from the observed read footprint, live-footprint freshness, and DeriveIntent/GrantIssuer issuance",
   "derive_battery.mjs": "30 falsifiers, in-process",
   "derive_worker.mjs": "the far side; holds no parent reference, resolves programs from its own registry, reads only its grant snapshot, and asserts its own implementation_id",
   "derive_realm_battery.mjs": "10 falsifiers across a real worker boundary",
   "probe_derivegrant_v02_repro.mjs": "the two v0.1.0 defects, frozen — and the same witnesses run against live, which is what makes it a gate rather than a document",
   "probe_coresem_v03_repro.mjs": "the four semantic gaps behind one program_sem_id, frozen at v0.2.0",
   "probe_stalegrant_v03_repro.mjs": "every check passing on a result the World has moved past"
  },
  "two_evidence_objects": {
   "read_grants + grant_id": "the AUTHORITY GRANT — what the authority made available. A capability record, deliberately allowed to be broader than what is read, because under data-dependent traversal the authority cannot know the needed subset in advance. grant_id = H(canonical read_grants) binds the snapshot so it cannot be edited in flight.",
   "read_footprint": "the OBSERVED DEPENDENCY RECORD — what the program actually consumed through a tracked read or scope. Freshness, invalidation, replay and support analysis key on THIS. Defining it as the grant would over-invalidate every derivation whose grant was wider than its reads, which under snapshot granting is all of them.",
   "why_separate": "v0.1.0's prose said the footprint was 'the authority's record of what it read on the derivation's behalf'. That was two errors at once: it described a collapse that would break freshness, and the mechanism did not even implement the collapse — the worker sourced its read table from canonical_inputs, and {op:'input', name:'__reads'} returned the whole table with zero tracked reads."
  },
  "granting_model": "SNAPSHOT (model A): the authority resolves a bounded canonical world slice once, and both the executor and the re-deriving authority evaluate against those same bytes. Chosen over read-RPC (model B) because it is deterministic, films cleanly, and does not turn every primitive evaluation into a cross-realm round trip. The cost is least-authority: the grant may reveal more than the program reads. Confidentiality against the derivation realm is the trigger to revisit, and it is named here rather than discovered later.",
  "claimed": "OBJECT authority does not cross: structured cloning refuses callables (DataCloneError), the worker resolves program_sem_id against its own registry, it can read only the grant snapshot the authority resolved, the returned footprint is validated as a SUBSET of that grant on the authority's own evidence before any re-derivation, the executor asserts implementation_id and the caller may only state a requirement against it, and a returned result is re-derived by the authority — on the semantic projection, so a conforming foreign implementation can agree — before it is evidence.",
  "not_claimed": "determinism of a long-lived evaluator; host confinement; that any existing measureFn has been ported; that implementation_id is bound to executable BYTES (it is a declared constant, so impersonation is closed and provenance is not — the trusted-launcher measurement is declared and not built); and that any lowering into TRVM terms has been attempted. Named separately in realm_roadmap, derivation_language and lowering_spike.",
  "frozen_core": "TRVM-DERIVE-CORE-v1. program_sem_id = H('TRVM-PROGRAM-v2' | core_sem_id | canonical AST) where core_sem_id = H(canonical CORE_SPEC), so the id commits SEMANTICS and not only syntax. v0.2.0 hashed the AST alone while the record said the language was deliberately not frozen — the two cannot both be true, and four behaviours could differ behind one id. Every v0.2.0 program id is retired.",
  "three_questions": {
   "containment": "footprintWithinGrant — was every claimed read inside the snapshot this derivation received? HISTORICAL.",
   "agreement": "validateForeignResult — does the semantic projection re-derive to the same canonical bytes? Also historical: it evaluates against the same snapshot.",
   "freshness": "validateFootprintFresh — are those dependencies still current NOW? TEMPORAL, keyed on the footprint and never on a global vclock. All three are required; the first two can pass about a World that has moved."
  },
  "issuance": "grant_id proves INTEGRITY, not AUTHORITY — a hash authenticates content to itself. A caller submits a DeriveIntent; the authority resolves the snapshot and is the only constructor of a DeriveRequest; GrantIssuer records what it issued. A signature is added when the grant crosses a real trust boundary, is persisted and replayed, is delegated, or must be proved to an independent verifier — not before, because today it would authenticate the authority to itself."
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
  "probe_coresem_v03_repro.mjs": "DERIVE-v0.3 — program_sem_id bound syntax and claimed semantics: add was JavaScript '+', bind() validated nothing, arity was unconstrained, evaluation order was free. Frozen against v0.2.0, CONFINED against live; PAIRED, and it gates",
  "probe_stalegrant_v03_repro.mjs": "DERIVE-v0.3 — the GAP witness: containment, re-derivation and schema all pass on a result whose World has moved. Not a regression repro; v0.2.0 had no freshness at all"
 }
}
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
# string and reported success.
#
# That is no longer an occasional bug. It is a recurring threat to the validity
# of every number this tree prints, so the KNOWN FAILURE SPECIES get a gate.
#
# This is deliberately NOT a general test-of-tests. It encodes the eight shapes
# that have actually gone wrong here, and it stops there. Each meta-case breaks
# an instrument on purpose and requires the harness to SAY SO.
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
fs=list(m['case_inputs'])
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

echo
[ $FAILED -eq 0 ] \
  && echo "HARNESS SELFTEST: $META/$META known apparatus failure species caught" \
  || echo "HARNESS SELFTEST: FAILURES PRESENT ($CAUGHT/$META caught)"
exit $FAILED
```

## `record/negative-cases-round16.sh`

```bash
# ── round 16: the frozen core, freshness, issuance, and the apparatus gate ───

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

run_case derive-freshness-removed "missing v0.3.0 construct" "
src = open('derive_protocol.mjs').read()
src = src.replace('export function validateFootprintFresh', 'function validateFootprintFresh')
open('derive_protocol.mjs','w').write(src)"

run_case derive-vclock-freshness "never on a global vclock" "
import json
g = json.load(open('invariant-grid.json'))
for e in g['law_registry']['entries']:
    if e['id'] == 'derivation.footprint-freshness':
        e['statement'] = e['statement'].replace('never on a global vclock', 'on the world vclock')
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case derive-issuance-law-deleted "law derivation.grant-issuance@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'derivation.grant-issuance']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case harness-selftest-law-deleted "law evidence.harness-selftest@1 missing" "
import json
g = json.load(open('invariant-grid.json'))
g['law_registry']['entries'] = [e for e in g['law_registry']['entries']
                                if e['id'] != 'evidence.harness-selftest']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case lowering-spike-dropped "lowering_spike missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['lowering_spike']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

run_case core-freeze-undeclared "derivation_language.frozen missing" "
import json
g = json.load(open('invariant-grid.json'))
del g['derivation_language']['frozen']
json.dump(g, open('invariant-grid.json','w'), indent=1)"

echo; [ $FAILED -eq 0 ] && echo "NEGATIVE BATTERY: $CASES/$CASES forgeries caught" || echo "NEGATIVE BATTERY: FAILURES PRESENT ($CAUGHT/$CASES caught)"
exit $FAILED
```

## `gate/derive_battery.txt`

```text
$ cd code && node derive_battery.mjs
PASS  program-id-is-content              two programs, two ids (psem-e5568a1ff… vs psem-55a4b30d1…); recomputing P's id reproduces it
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
PASS  implementation-id-asserted         the result carries impl-js-derive-v0.3.0, emitted by the evaluator that ran. At v0.1.0 the REQUEST carried implementation_id, nothing checked it and the result carried none (W-2)
PASS  implementation-requirement-refused a request demanding a C executor is refused BY the JS executor (implementation-mismatch: want impl-c-pretend-v9, this is impl-js-derive-v0.3.0) — the caller's field states a requirement and the executor answers it, so impersonation has no path
PASS  implementation-id-well-formed      a result whose implementation_id is not an impl- identity is refused: result-implementation-id-malformed
PASS  semantic-projection-is-portable    a result identical in semantics but produced by impl-c-derive-v0.2.0 validates, and the authority records WHO ran it (impl-c-derive-v0.2.0). program_sem_id is equal across implementations; implementation_id is outside the semantic projection, which is what makes a portable film possible
PASS  implementation-requirement-checked-on-result a result from a different executor than the one required is refused: implementation-mismatch: want impl-js-derive-v0.3.0, result claims impl-c-derive-v0.2.0
PASS  registry-binding-verified          verify(PID) recomputes the hash and agrees; an unbound id is refused (program-unknown)
PASS  registry-entry-frozen              the stored program is deep-frozen; mutating it throws and the registry still reads 'add'
PASS  core-id-is-content-bound           CORE_SEM_ID recomputes from the frozen CORE_SPEC (core-06485b250ac283f…). A bare label "TRVM-DERIVE-CORE-v1" would be the caller-selected-name defect the primitive ruling already refuses
PASS  program-id-commits-the-core        program_sem_id = H("TRVM-PROGRAM-v2|" + core_sem_id + "|" + canonicalBytes(ast)) — change what add means and the core moves and every program id moves with it, which is what makes the id semantic
PASS  grammar-refuses-before-id          unknown op:refused missing field:refused extra field:refused non-string name:refused bad child:refused non-canonical const:refused — v0.2.0 issued a program_sem_id to {op:"exec", cmd:"rm -rf /"}, which failed only later at evaluation, having already been given a semantic identity
PASS  arithmetic-typed-and-total         2+3 =5 · "2"+"3" program-type: add of non-number · []+{} program-type: add of non-number · 1e308+1e308 program-arith-non-finite: add. v0.2.0's add was JavaScript's + and produced "23" and "[object Object]" under the same program_sem_id
PASS  freshness-is-not-containment       after fb moves 1→2: footprintWithinGrant PASS, re-derivation PASS — both CORRECT about the snapshot — and freshness stale-read: fb granted@1 live@2. Containment is historical, freshness is temporal, and a protocol that stops at re-derivation commits a value the World has already contradicted
PASS  unrelated-write-does-not-invalidate other@1→2 moved and freshness still passes — it keys on the FOOTPRINT, never on a global vclock. A vclock rule would invalidate every derivation on every unrelated write, undoing the grant/footprint separation from the other side
PASS  issuance-is-not-content-identity   the issuing authority accepts (committable true); a different authority instance refuses the byte-identical request (grant-not-issued-by-this-authority). grant_id = H(read_grants) authenticates content to itself — a caller can build a grant AND a matching grant_id, so the hash proves integrity and says nothing about who cut it
PASS  intent-schema-closed               extra field:refused missing field:refused resources not lists:refused capability in inputs:refused — the untrusted half of the two-phase protocol is validated as strictly as the authority's half
PASS  authority-is-the-only-request-constructor authorize() resolves the snapshot from the live world and records what it issued; a self-chosen request_id is not in the table. A signature is NOT added here: it would authenticate the authority to itself. The named triggers are a real trust boundary, persistence and replay, delegation, or an independent verifier
════════════════════════════════════════════════════════════════════════════════════════════════
DERIVE-BATTERY: PASS — 30/30. The program is data and its id commits the frozen core's semantics, not just its syntax; the grant is what the authority made available and the footprint is what the program consumed; containment is historical and freshness is temporal; the executor asserts its own identity; and issuance is a topology, not a hash.
```

## `gate/derive_realm_battery.txt`

```text
$ cd code && node derive_realm_battery.mjs
PASS  closure-cannot-cross             postMessage of a request carrying a function throws — DataCloneError: () => 1 could not be cloned.. The 9D.4 lexical-cell attack has no transport: structured cloning refuses callables, so the confinement is done by the boundary rather than by object discipline
PASS  crossing-derives                 worker returned value 5 for fb=5 bias=0, resolving the program from its OWN registry by id and stamping the result impl-js-derive-v0.3.0 against grant grant-d32ef00d02de…
PASS  claim-revalidated-at-home        the worker's honest result reproduces locally against the same snapshot; an inflated one is refused (foreign-result-divergence)
PASS  ungranted-read-refused           derivation-threw: read-not-granted: fb — resolving reads is an AUTHORITY operation the parent performs; the worker holds no world and needs none
PASS  unknown-program-refused          program-unknown — the worker resolves ids against its own registry, so a caller cannot name code the worker does not hold
PASS  grant-not-reachable-as-input     the worker granted fb and secret:key returns "an ordinary input" for {op:"input",name:"__reads"} — at v0.1.0 this returned the whole grant table across the same boundary, with an empty footprint and zero tracked reads
PASS  executor-asserts-implementation  a request demanding a C executor is refused by the JS worker (implementation-mismatch: want impl-c-pretend-v9, this is impl-js-derive-v0.3.0); one demanding JS runs and returns its own id. The caller states a requirement; the executor answers it
PASS  foreign-footprint-refused        footprint-ungranted-read: secret:key — the authority checks the returned footprint against the grant it issued, on its own evidence. The footprint is the dependency record and the grant is the capability record; the round-14 prose collapsed them and the mechanism supported neither
PASS  cross-implementation-shape       the same result stamped by a C executor validates and its provenance is RECORDED rather than compared away. This is the shape a real C implementation plugs into — it is not a claim that one exists, and this battery does not have one
PASS  intent-to-acceptance             a caller's INTENT is authorized into a request by the authority, crosses to a realm holding no world, returns a claim, and is accepted (committable true) — then the same claim is refused once fb moves 1→2 (stale-read: fb granted@1 live@2). The worker never learns the World exists
════════════════════════════════════════════════════════════════════════════════════════════════
DERIVE-REALM: PASS — object authority does not cross the boundary, the realm reads only its grant, and the executor names itself. Determinism and host confinement are SEPARATE scopes and are not claimed here.
```

## `gate/probe_coresem_v03_repro.txt`

```text
$ cd code && node probe_coresem_v03_repro.mjs
BREACH    C-1 frozen-v0.2.0          same program_sem_id psem-f9865dcea5bab…, three behaviours: "2"+"3" = "23", []+{} = "[object Object]", 1e308+1e308 = Infinity — none of which a C implementation would reproduce by accident
CONFINED  C-1 live                   strings refused: program-type: add of non-number; objects refused: program-type: add of non-number; overflow refused: program-arith-non-finite: add — operands must be numbers and results must be finite, both frozen in CORE_SPEC.numbers
BREACH    C-2 frozen-v0.2.0          {op:"exec", cmd:"rm -rf /"} received program_sem_id psem-177f6b6b00b56c347… — the registry would have bound it, and it would have failed only later, at evaluation, already carrying a semantic identity
CONFINED  C-2 live                   program-unknown-op: exec at $ — validateProgram runs before the hash, so an id is never issued for a program the language does not contain
BREACH    C-3 frozen-v0.2.0          three malformed programs, three ids: const, no value -> psem-4b3c8b1d8… · add, missing b -> psem-5e38b6fec… · add + extra field -> psem-7eb739729…
CONFINED  C-3 live                   const, no value -> program-node-fields at $ · add, missing b -> program-node-fields at $ · add + extra field -> program-node-fields at $ — the key set must be EXACTLY {op} union the op's declared fields
BREACH    C-4 frozen-v0.2.0          read_footprint is a SEQUENCE — [["b",1],["a",1]] — and a right-to-left implementation returns [["a",1],["b",1]] for the same program. Different canonical bytes, therefore foreign-result-divergence between two implementations that compute the same value. v0.2.0 evaluated a-before-b and never said it had to; this witness is that ORDER MATTERS, not that v0.2.0 ordered wrongly
CONFINED  C-4 live                   CORE_SPEC.evaluation_order states the order AND that the footprint is a sequence, and CORE_SEM_ID is inside program_sem_id — so an implementation ordering differently is a different core, not a disagreement about one program. Behaviour unchanged: [["b",1],["a",1]]
CONFINED  identity-is-semantic       psem(P) moved psem-f154679ca23… -> psem-e5568a1ff4a… because CORE_SEM_ID core-06485b250ac… is now inside it. Every v0.2.0 program id is retired, deliberately and now, while no second implementation exists to be broken by it
====================================================================================================
CORE-SEM-v0.3 REPRO: 4/4 reproduce against the frozen v0.2.0 · 5/5 confined against live
```

## `gate/probe_stalegrant_v03_repro.txt`

```text
$ cd code && node probe_stalegrant_v03_repro.mjs
grant grant-d32ef00d02de83… cut at fb@1=5 · derived value 5 · footprint [["fb",1]]
World moved: fb is now @2=9

GAP    v0.2.0-era checks              checkResult PASS · footprintWithinGrant PASS · validateForeignResult PASS — all three CORRECT, and the value 5 is now wrong in a World where fb is 9. Re-derivation against the same snapshot can never notice this
HOLDS  live freshness                 stale-read: fb granted@1 live@2 — the temporal question, asked against the LIVE world and keyed on the footprint
HOLDS  acceptance refuses             stale-read: fb granted@1 live@2 — issuance, validation and freshness in ONE call, so there is no window between the check and the commit for the World to move in
HOLDS  unrelated-write-ignored        other@2 moved and acceptance still passes (committable true) — freshness keys on the FOOTPRINT, not on a global vclock. A vclock rule would invalidate every derivation on every unrelated write and quietly undo the grant/footprint separation
HOLDS  scope-digest-staleness         stale-scope: kind:node — value 2 was derived over 2 nodes and the query now answers 3, with no exact read having moved. This is the World's phantom-scope case (law:warrant.phantom-scope@1) reaching the derivation boundary
HOLDS  grant-id-is-not-issuance       a DIFFERENT authority instance refuses the same well-formed request (grant-not-issued-by-this-authority), and a self-made request_id is refused by the issuing one. grant_id = H(read_grants) authenticates content to itself and proves nothing about who cut it; the issuance table is what does
====================================================================================================
STALE-GRANT v0.3 WITNESS: 5/5 hold; the three v0.2.0-era checks pass on a stale result BY DESIGN, which is the finding
```

## `gate/harness_selftest.txt`

```text
$ ./harness_selftest.sh
PASS  M-1 cwd-independence → IDENTICAL: GRID-CONSISTENCY-2: PASS — registry valid (61 entries), 343 citations resolved ac
PASS  M-2 missing-artifact → - artifact missing: refinement_receipt.json
PASS  M-3 undeclared-artifact → - governance artifact extra_artifact.json is present but UNDECLARED in artifacts.json — the 
PASS  M-4 vacuity-detected → FAIL  meta-vacuous (VACUOUS — the forgery changed no artifact; nothing was tested)
PASS  M-5 deletion-detected → PASS  meta-deletion [kappa_witnesses.mjs] → - artifact missing: kappa_witnesses.mjs
PASS  M-6 wrong-target-caught → FAIL  meta-wrong-target (TARGET MISMATCH — script intends [invariant-grid.json], run changed
PASS  M-7 wrong-diagnostic → FAIL  meta-wrong-diagnostic (exit=1; wanted /the moon is made of cheese/)
PASS  M-8 vacuous-frozen-side → DERIVE-GRANT-v0.2 REPRO: 1/2 reproduce against the frozen v0.1.0 · 2/2 confined against live

HARNESS SELFTEST: 8/8 known apparatus failure species caught
```

## `gate/make-governance.txt`

```text
# make governance — verbatim, 2026-08-19T01:48Z, node v25.2.1

==== [governance] law kernel — conformance + the periodic-law grid ====
════════════════════════════════════════════════════════════════════════════════════════════════
VERDICT: PASS — conformant; every asserted law holds; every by-design falsification still fails; certificate emitted.
==== [governance] invariant grid — registry, citations, engine-free receipts ====
GRID-CONSISTENCY-2: PASS — registry valid (61 entries), 343 citations resolved across 16 artifacts, no banned stale claims, structure coherent with v1.17.0. [root /home/travis/ProjectAmp2/TRVM/governance]
==== [governance] World — warrants, maintenance, confinement ====
VERDICT: PASS — the WORLD layer's warrant machinery holds; receipt emitted.
RECEIPT-CHECK: PASS — world rebuilt from committed spec; ground and composite REPLAYED with support equality; commitment recomputed.
==== [governance] negative battery — every forgery must be caught ====
NEGATIVE BATTERY: 85/85 forgeries caught
==== [governance] cross-plane bridge — C canonical bytes vs the JS oracle ====
BRIDGE-CHECK: PASS — 48/48 states byte-identical across implementations (24 vectors x {initial, normal form}); C packed-word heap and JS node graph reach the same canonical signature STRING, not merely the same digest.
==== [governance] serialized derivation boundary ====
DERIVE-BATTERY: PASS — 30/30. The program is data and its id commits the frozen core's semantics, not just its syntax; the grant is what the authority made available and the footprint is what the program consumed; containment is historical and freshness is temporal; the executor asserts its own identity; and issuance is a topology, not a hash.
DERIVE-REALM: PASS — object authority does not cross the boundary, the realm reads only its grant, and the executor names itself. Determinism and host confinement are SEPARATE scopes and are not claimed here.
DERIVE-GRANT-v0.2 REPRO: 2/2 reproduce against the frozen v0.1.0 · 2/2 confined against live
CORE-SEM-v0.3 REPRO: 4/4 reproduce against the frozen v0.2.0 · 5/5 confined against live
STALE-GRANT v0.3 WITNESS: 5/5 hold; the three v0.2.0-era checks pass on a stale result BY DESIGN, which is the finding
==== [governance] harness self-test — the apparatus is measured too ====
HARNESS SELFTEST: 8/8 known apparatus failure species caught
  evidence plane green
```

## `record/round-16-ledger-section.md`

## Round 16 — the identity bound a spelling

**64. `program_sem_id` committed syntax and the record claimed it committed semantics, and those cannot both be true.** Review put the contradiction in one line: `programSemId` computed `H("TRVM-PROGRAM-v1|" + canonicalBytes(ast))` while `derivation_language` said the core was deliberately *not* frozen. If two conforming implementations may assign different meaning to `add`, to evaluation order, to numeric behaviour or to refusal semantics and still agree on the id, the id names a spelling. Four gaps sat behind it, all reproduced before anything was changed and frozen as C-1…C-4 in `probe_coresem_v03_repro.mjs`:

| | |
|---|---|
| **C-1** | `add` was JavaScript `+` — `"2"+"3"` is `"23"`, `[]+{}` is `"[object Object]"`, `1e308+1e308` is `Infinity` |
| **C-2** | `bind()` validated nothing — `{op:"exec", cmd:"rm -rf /"}` was issued a `program_sem_id` |
| **C-3** | arity and field sets unconstrained — `{op:"const"}` with no value, `add` with no `b`, and `add` with an extra field all received ids |
| **C-4** | evaluation order free — `read_footprint` is an ordered **sequence** appended at access, so a right-to-left implementation returns different canonical bytes, hence `foreign-result-divergence`, for a program it computed identically |

C-4 is the one that would have been hardest to find later, because it is not a bug in either implementation: two correct evaluators disagreeing about a field neither of them thinks is semantic.

**65. The core is frozen, and its identity is content-bound rather than a label.** `TRVM-DERIVE-CORE-v1` (`law:derivation.core-semantics@1`) declares the grammar, the value domain, arithmetic — IEEE-754 binary64, **no coercion**, operands must be numbers and results must be finite with overflow refused *at* the operation — evaluation order, the footprint's ordering as part of the result, totality, and the exact refusal vocabulary. `core_sem_id = H(canonical CORE_SPEC)`, **not** the string `"TRVM-DERIVE-CORE-v1"`, because a bare name is precisely the caller-selected identity the primitive ruling already refuses for `"componentReachability"` — the record would have committed the same defect one layer up while forbidding it one layer down. `program_sem_id = H("TRVM-PROGRAM-v2" | core_sem_id | canonical AST)`, and the grammar is validated **before** the hash, so no identity exists for a program outside the language.

**66. Every v0.2.0 program id is retired, deliberately, and the timing is the whole argument.** `psem-f154679c…` became `psem-e5568a1f…` for the same AST. This is cheap exactly once — while no second implementation exists to be broken by it — and expensive forever after. The alternative review offered was to mark the domain separator explicitly draft; freezing was preferred because `add`, `read`, `input`, evaluation order, canonical values and the refusal vocabulary do not need `componentReachability` to exist before their meaning can be settled. The primitive *catalog* stays unfrozen, and a `prim` extension bumps the core version and every program id with it: a program written against a different language is a different program.

**67. Freshness is a different question from containment, and the witness is that all three existing checks can be correct while the result is not committable.** `probe_stalegrant_v03_repro.mjs`: cut a grant at `fb@1=5`, derive, move the World to `fb@2=9` — then `checkResult` **PASS**, `footprintWithinGrant` **PASS**, `validateForeignResult` **PASS**, all three *correct*, and the value 5 is now wrong. Re-derivation against the snapshot can never notice, because executor and authority are agreeing about the same stale bytes. `validateFootprintFresh` asks the temporal question against the live World and refuses `stale-read: fb granted@1 live@2`. It keys on the **footprint, never on a global vclock** — the negative half is witnessed too, and `grid_check` refuses a law text that drops the phrase, because a vclock rule would invalidate every derivation on every unrelated write and undo the grant/footprint separation from the other side. The scope half reaches further than expected: a node joining a query with no exact read moving is `stale-scope: kind:node` — the World's phantom-scope case arriving at the derivation boundary.

**68. Acceptance is one call, and the lock it needs is named rather than assumed.** `acceptForeignResult` runs issuance → validation → freshness in a single operation, because a freshness check that returns to the caller before the commit is a TOCTOU window of exactly the species rounds 9B–9D.4 spent six rounds removing. It **does not take the World's lock and cannot** — the World owns that, and a second lock would be a second authority — so the requirement is stated in the source and in the law: the caller must hold the commit lock across acceptance and commit.

**69. `grant_id` proves integrity and says nothing about who issued it.** A hash authenticates content to itself; a caller can build a `read_grants` *and* a matching `grant_id`. v0.2.0 separated the grant from the inputs in the **message** and left the issuer and the caller as the same party in the **topology**, so the separation was structural and not yet real. Fixed as topology rather than crypto: a caller submits a `DeriveIntent` naming what it wants to read, `GrantIssuer.authorize` is the only constructor of a `DeriveRequest`, and the authority records what it issued — a different `GrantIssuer` instance refuses the byte-identical request with `grant-not-issued-by-this-authority`. **A signature was deliberately not added.** It would currently authenticate the authority to itself. The four conditions that will require one — a real trust boundary, persistence and replay, delegation between authorities, an independent verifier — are named in the law so the crypto arrives for a reason.

**70. The apparatus gets a gate, because five consecutive rounds found the instrument wrong rather than the engine.** `law:evidence.harness-selftest@1` and `harness_selftest.sh`, **8/8**: working-directory dependence, an absent declared artifact, a present undeclared one, a perturbation that changes nothing, a case that *deletes* rather than modifies, a case that moves an artifact it did not declare, a case whose expected diagnostic is not the one produced, and a paired probe whose frozen side has been silently repaired. Bounded on purpose — it encodes the failure species that have actually occurred here and does not recurse into tests of tests.

**71. It caught two defects in its own first draft, which is the behaviour it exists to have.** The scratch-battery builder split the real runner at the first line beginning `run_case ` — which is the function *definition*, `run_case () {` — producing a meta-battery whose runner was undefined; every meta-case then "failed" for a reason unrelated to what it measured. And M-8's silent repair emptied the frozen `reads` table, after which W-1 **kept reproducing** — because W-1 never performs a read: it reaches the grant table through the `input` op, since v0.1.0 carried the table inside `canonical_inputs`. A meta-case that tests nothing is the exact thing this file exists to refuse, and it refused its own. Separately, M-1 first asserted that all three directories produced a *passing* verdict rather than an *identical* one, so it failed on an unrelated version-lockstep error — a meta-case failing for a reason outside its own subject, which is itself one of the species. It now asserts identity alone.

**72. Gate.** grid **v1.17.0** — 61 entries / 341 citations · `derive_protocol.mjs` **0.3.0** · kernel PASS (CONF-1 24/24 · CONF-2 REGRESSION-LOCKED) · World 0.12.0 PASS · `--check-receipt` PASS · negative battery **85/85** with nine new forgeries · bridge 48/48 · derive **30/30 in-process, 10/10 across a realm** · probes **2/2+2/2**, **4/4+5/5**, **5/5** · harness self-test **8/8**. `scheduler_certificate.json` byte-identical — `cert_id` unmoved, the calculus untouched for an eleventh consecutive round.

**73. What is declared and not built, in the order it will be attempted.** The `lowering_spike` is recorded with a decision rule that permits the answer *no*: the **pure fragment only** — `const`, `input`, arithmetic, possibly `len`, and explicitly **not** `read`/`scope`/`cite`, whose footprint semantics would muddy the question — proving three properties (the same AST lowers to byte-identical target syntax; JS and ic32 decode to the same value; the resulting execution emits and replays an ordinary TRVM film). Three identities stay distinct — `program_sem_id`, `lowering_id`, `target_term_sem_id` — because collapsing them turns a refinement statement into a renaming. Then native ic32 films, still **not gated** on the derivation language. Then the first primitive. Then measured implementation provenance: the trusted launcher hashes the artifact it is about to execute, rather than an executable hashing itself into itself.

**Where the ladder is now.** Nine rounds moved a seal outward until the authority stopped being an object. Round 14 replaced the API. Round 15 found the defect in the record rather than the boundary. **Round 16 found it in the identity** — the one thing every later cross-implementation claim was going to rest on, unfrozen, one round before the implementation that would have discovered it the expensive way.
