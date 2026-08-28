# DERIVE-v0.2 — the micro-round you asked for, built and gated

**For:** review of TRVM round 15 (`TRVM/governance/`, branch `merge/governance-plane`)
**Built by:** Claude (Opus 5), session 2026-08-18
**Predecessor:** your review of round 14 (artifact roots + realm crossing, commit `5b25a08`)
**Status:** shipped, whole gate green, **not committed** — `make governance` passes and the
calculus has not moved (`scheduler_certificate.json` reproduced byte-identically, `cert_id`
unmoved for a tenth consecutive round).

Everything in `code/` runs standalone on Node ≥18 with no repository around it. Verbatim output
of every run is in `gate/`, captured before this file was written.

```
cd code
node derive_battery.mjs              # 21/21 in-process
node derive_realm_battery.mjs        #  9/9 across a real worker_threads boundary
node probe_derivegrant_v02_repro.mjs # 2/2 reproduce frozen · 2/2 confined live
```

---

## 0. Both witnesses reproduced before anything was changed

Not taken on trust. Verbatim, against the round-14 tree:

```
W-1  value.secret.value       42
     witness.reads             0
     support                   []
     read_footprint.exact      []
     read_footprint.predicates []

W-2  request implementation_id "impl-c-pretend-v9" → ok:true, executed by the JS evaluator
     result fields: program_sem_id, read_footprint, request_id, support, value, witness
     (no implementation_id at all)
```

Both are now frozen in `code/probe_derivegrant_v02_repro.mjs`, which embeds v0.1.0 verbatim as a
`data:` URL and runs it in a real worker. See §4 for why that probe is shaped differently from its
siblings.

---

## 1. All seven items of DERIVE-v0.2, and where I deviated

| your item | done | note |
|---|---|---|
| remove `__reads` from `canonical_inputs` | ✅ | `input` addresses `canonical_inputs` only; `read`/`scope` address `read_grants` only |
| make grants real | ✅ | `read_grants: {exact, predicates}`, validated by `checkGrants` |
| `grant_id` / snapshot binding | ✅ | `grant_id = "grant-" + H("TRVM-GRANT-v1\|" + canonicalBytes(read_grants))`; `checkRequest` recomputes and refuses `request-grant-id-mismatch` |
| actual footprint is access subset | ✅ | recorded by the evaluator on access; battery shows a 3-resource grant against a 1-entry footprint |
| parent independently validates footprint | ✅ | `footprintWithinGrant` fires **before** re-derivation, on the snapshot rather than on the executor's word |
| executor asserts `implementation_id` | ✅ | worker emits its own constant; result carries it; `checkResult` requires an `impl-` identity |
| caller cannot impersonate implementation | ✅ | caller may only set `expected_implementation_id`, a **requirement**; the executor refuses one it cannot meet |

**Deviation 1 — grants are keyed objects, not lists of triples.** You wrote
`exact: [[resource, version, value], …]`. I used `exact: { [resource]: {value, version} }`.
Reason: canonical objects sort their keys, so `grant_id` does not depend on the order the
authority happened to resolve resources in, and a duplicate resource carrying two versions cannot
be expressed at all. With a list both are live: `grant_id` becomes resolution-order-sensitive, and
`[["fb",1,5],["fb",2,9]]` is a representable grant with no defined meaning. If you want the list
form for wire reasons, the fix is a canonical sort plus a duplicate-key refusal, and I'd rather
have the impossibility than the check.

**Deviation 2 — `deriveLocally` no longer takes a reader at all.** Not just the grant/input split:
the whole reader parameter is gone, on both sides. §3 explains why.

**Deviation 3 — the semantic projection.** You said portable evidence commits `program_sem_id`
while execution provenance additionally commits `implementation_id`. I made that operative rather
than declarative: `SEMANTIC_RESULT_FIELDS = RESULT_FIELDS.filter(f => f !== "implementation_id")`,
and `validateForeignResult` compares **only** that projection. Without it, cross-implementation
validation fails by construction — the parent re-derives with JS, the foreign result says C, and
whole-result byte equality can never hold. This is the field that makes a C executor pluggable,
and there is a battery case (`semantic-projection-is-portable`) plus a negative case that catches
its removal.

---

## 2. Reads: I kept your two-object model and did not redefine the footprint

Adopted as ruled, and the record now states it as a law
(`law:derivation.grant-footprint-separation@1`). The argument that carried it is the
over-invalidation one: under snapshot granting the grant is *always* wider than the footprint, so
defining the footprint as the grant would invalidate every derivation whenever any
granted-but-unread resource moved.

`granting_model` is recorded as a **decision** rather than a default — snapshot (A) over read-RPC
(B), per your §5 — with its cost named where it will bite: the grant may reveal more than the
program reads, so **confidentiality against the derivation realm is the stated trigger to move to
B or a hybrid**, not a property this design already has.

**One thing I did not do and want your read on.** The authority resolves grants *and* the request
carries them, so "the authority" and "the caller" are the same party in the current shape (parent
resolves, worker executes). The separation is structural in the schema but not yet in the trust
topology. If a third party can construct a `DeriveRequest`, they can construct its `read_grants`
and a matching `grant_id`, and nothing signs the grant as authority-issued. Is that worth closing
now with a grant signature / authority key, or does it wait until there is a caller that is not
the authority?

---

## 3. A third defect, found while repairing the first two

`evaluate(ast, reader, inputs)` took the reader as a **callable parameter**, and `deriveLocally`
passed the caller's — in the module whose header explains why an arbitrary closure is an unbounded
capability container.

It was not a boundary hole: the worker built its own reader from data and no function survives
`postMessage`. But it is the same species living in the authority's own path, in the file built to
remove that species. The evaluator now builds its reader from canonical grant data and nothing
else, and a pair of reader callables in the grant position is refused **as data**:

```
grants-schema: [read,scope]
```

Related, found by the battery rather than by reading: `evaluate` was not total over its input
domain — a malformed grant produced a raw `TypeError` instead of a named refusal. Fixed in the
code, not in the assertion that caught it.

---

## 4. The probe is paired, and it is the first probe in this tree that gates

Its siblings (`probe_closureenv`, `probe_realm_9d2`, `probe_ownfailopen`) freeze a boundary that
is *declared open*, so they report a breach and that is the record. These two defects are
repaired, so a one-directional probe would pass just as happily if the frozen copy were quietly
replaced with the repaired one.

So it runs each witness twice: against the embedded v0.1.0, where it **must still reproduce** — a
witness that stops reproducing against the version it was written for has stopped measuring — and
against live, where it must be confined. Exit 0 requires both directions.
`law:evidence.instrument-nonvacuity@1` applied to a repro.

---

## 5. Films: your ruling adopted, and recorded so it cannot be walked back

`film_planes` (in `record/grid-derivation-sections.json`) separates the two transition systems and
names the exact failure mode you identified — finishing C↔JS cross-replay on the tiny derivation
AST and writing *"cross-implementation semantic films complete"* while native ic32 emits none.

The roadmap is re-ordered accordingly: **native ic32 film emission is not gated on the derivation
language** and proceeds on the existing §10/§10.5 conformance contract. The previous order read
*"that same program as the first C↔JS film / cross-replay witness"*, which was the conflation.

Your lowering idea — `DeriveProgram AST → canonical lowering → interaction-net term → ic32 →
semantic film`, one execution substrate instead of a derivation interpreter beside a rewrite
runtime — is recorded as **reachable and not adopted**, explicitly as the reason not to build so
much dedicated interpreter machinery that the option closes. That is the one piece of your
analysis I'd most like pushed further (see §7).

---

## 6. What is open, stated rather than implied

1. **`implementation_id` is a declared constant, not a digest of executable bytes.** So
   impersonation is closed and **provenance is not** — a modified JS worker still emits
   `impl-js-derive-v0.2.0`. This is written into the law's own statement as `DECLARED OPEN`, and a
   negative case catches its removal. I considered hashing the module source at import and
   rejected it: the module must be movable across a realm boundary, and reading its own source at
   load re-introduces a filesystem dependency into the one file that deliberately has no artifact
   root. **What is the right binding for a C executable and a JS module and a wasm binary that
   does not do that?**
2. **`TRVM-DERIVE-v1` is not frozen.** Your step 2 asked for the small total core to be frozen as
   a v1 spec. I ruled the language in the grid (`derivation_language`: small total core + named
   semantic primitives, content-bound `primitive_sem_id`, component reachability first) and
   versioned the module 0.2.0 under `artifact_versions` — but there is no frozen spec document.
   Deliberate: freezing a language before its first non-arithmetic primitive exists seemed likely
   to freeze the wrong thing.
3. **No `prim` op exists.** The ruling is recorded; nothing is built.
4. **Determinism and host confinement** remain unclaimed, unchanged from round 14.
5. **No derivation has been ported.** `componentMeasure` still cannot be expressed.

---

## 7. What I would most like from this pass

1. **The lowering question (§5).** Is `DeriveProgram → TRVM term → ic32 → film` the right target,
   and if so, what is the smallest thing that would *test* the idea before it is committed to? A
   lowering of `add`/`const` alone would be cheap and might be enough to find out whether the
   canonical-lowering step has a stable identity.
2. **The grant-issuance topology (§2).** Authority and caller are the same party today. Sign the
   grant now, or wait for a caller that isn't the authority?
3. **The `implementation_id` binding (§6.1).** Concretely: what does the C executable commit to,
   given it has no module URL and the JS module must stay filesystem-free?
4. **Whether `footprintWithinGrant` should also be a freshness check.** Right now it validates
   subset-of-grant. Freshness against the *live* world is a separate operation keyed on the
   footprint, and I have not built it — the grant snapshot is what both sides evaluate against, so
   nothing in v0.2.0 detects that the world moved after the grant was cut. That feels like the
   next real gap and I would rather you name its shape than have me guess it.
5. **Anything in `record/round-15-ledger-section.md` §63.** Round 14 claimed ambient CWD discovery
   had been replaced across `grid_check`; two reads had not been, and one of them —
   `existsSync(f) ? readFileSync(f) : ""` — scanned the **empty string** and passed vacuously from
   any directory but `governance/`. Fixed at v2.21. Five rounds running, the instrument has been
   the thing that was wrong, and I would like a second opinion on whether the apparatus discipline
   is now sufficient or whether it needs its own gate.

---

## 8. Bundle contents

```
README.md                                   this file
code/derive_protocol.mjs                    v0.2.0 — the protocol (runs standalone)
code/derive_worker.mjs                      v0.2.0 — the far side
code/derive_battery.mjs                     21 falsifiers, in-process
code/derive_realm_battery.mjs               9 falsifiers across a real worker
code/probe_derivegrant_v02_repro.mjs        W-1 and W-2 frozen + live, paired
gate/make-governance.txt                    the whole evidence-plane gate, verbatim
gate/derive_battery.txt                     run from OUTSIDE the repo, to prove it is standalone
gate/derive_realm_battery.txt
gate/probe_derivegrant.txt
record/round-15-ledger-section.md           §53–§63, the round's own account
record/grid-derivation-sections.json        the 4 derivation laws + derivation_language + film_planes + realm_roadmap
record/artifacts-derivation-boundary.json   the manifest's claimed / not_claimed / two_evidence_objects
record/grid_check-derivation-assertions.mjs.txt   the source locks that keep W-1 and W-2 from returning
record/negative-cases-round15.sh            the 9 new forgeries, each with its expected diagnostic
MANIFEST.sha256
```

**Gate as shipped:** grid v1.16.0 — 56 entries / 339 citations · kernel PASS (CONF-1 24/24,
CONF-2 REGRESSION-LOCKED) · World 0.12.0 PASS · `--check-receipt` PASS · negative battery
**76/76** (9 new) · bridge 48/48 · derive **21/21 · 9/9 · 2/2 + 2/2**.


---

# APPENDIX — every file inlined

The zip is the same content. This single file exists so it can be pasted if an upload is refused.

## `code/derive_protocol.mjs`

```javascript
/* ═══════════════════════════════════════════════════════════════════════════
   derive_protocol.mjs — v0.2.0 — the serialized derivation boundary

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
export const PROTOCOL_VERSION = "0.2.0";

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
   Small on purpose, and the grid rules it stays that way: a small TOTAL core
   plus named semantic primitives, never a general programming language. The
   point of the first round is not expressive power; it is that the thing
   crossing the boundary is DATA whose identity is its content. Growing the
   language must not change existing program ids, which is why every node is a
   plain tagged object and the id is taken over canonical bytes. */
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
export const JS_IMPLEMENTATION_ID = "impl-js-derive-v0.2.0";

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
```

## `code/derive_worker.mjs`

```javascript
/* derive_worker.mjs — v0.2.0 — the far side of the realm boundary.
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
} from "./derive_protocol.mjs";

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

console.log("═".repeat(96));
console.log(fail
  ? `DERIVE-BATTERY: FAIL — ${rows.filter((r) => !r.ok).length}/${rows.length}`
  : `DERIVE-BATTERY: PASS — ${rows.length}/${rows.length}. The program is data and its id is its hash; the ` +
    `grant is what the authority made available and the footprint is what the program consumed; the ` +
    `executor asserts its own identity; and a foreign result is re-derived before it is evidence.`);
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

await w.terminate();
console.log("═".repeat(96));
console.log(fail ? "DERIVE-REALM: FAIL"
  : "DERIVE-REALM: PASS — object authority does not cross the boundary, the realm reads only its grant, " +
    "and the executor names itself. Determinism and host confinement are SEPARATE scopes and are not claimed here.");
process.exit(fail ? 1 : 0);
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

## `record/grid-derivation-sections.json`

```json
{
 "_note": "Extracted from TRVM/governance/invariant-grid.json v1.16.0. Full grid is ~1600 lines; these are the derivation-relevant sections only.",
 "grid_version": "1.16.0",
 "law_registry_derivation_entries": [
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
   "canonical": true,
   "supersedes": "derivation.serialized-boundary@1",
   "statement": "A derivation crosses an authority boundary as DATA or not at all. The program is a canonical AST and program_sem_id is H(canonical program), so it cannot be a caller-selected label and cannot be rebound — the id IS the program's hash, and the same program has the same id under every conforming implementation. The message domain is TRVM's canonical value domain, never 'structuredClone succeeded': Function, Map, Set, Date, class instances and transferable handles are refused, because those are capabilities rather than data. The derivation realm holds no world reference and reads ONLY the grant snapshot the authority resolved for it, addressed through read/scope — never through input, which addresses canonical_inputs alone. A result produced on the far side is a CLAIM; it becomes evidence only when the authority validates its footprint against the grant it issued and re-derives the SEMANTIC PROJECTION of the result — every field but implementation_id — to the same canonical bytes.",
   "evidence": "derive_battery.mjs 21/21 in-process and derive_realm_battery.mjs 9/9 across a real worker_threads boundary. The decisive one is still empirical: posting a request carrying a closure throws DataCloneError, so the 9D.4 lexical-cell attack — which no Object.freeze, deepFreeze, canonicalBytes, #private field or GuardedStore could reach — has NO TRANSPORT. v0.2.0 additionally removes the last callable from the derivation path: evaluate() builds its reader from canonical grant data instead of taking a reader parameter, and a pair of reader callables in the grant position is refused as data (grants-schema: [read,scope]). SCOPE, stated rather than implied: this closes derivation-object-confinement only. Determinism of a long-lived evaluator and host confinement (Date.now, Math.random, filesystem, network) are separate scopes, unclaimed here."
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
  "not_built": "no prim op exists at v0.2.0. This is a ruling, not an implementation."
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
   "contract": "law:derivation.serialized-boundary@2 + law:derivation.grant-footprint-separation@1",
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
 "film_identity_forward_declaration": {
  "decided": "before the C semantic-film round, not during it",
  "split": "program_sem_id (the semantic derivation/program identity, EQUAL across conforming implementations) vs implementation_id (executable provenance — a hash of ic32.c, the JS module, or the wasm binary)",
  "why": "a portable film must commit the first. Committing an executable hash would give the JS, C and WASM implementations of the same program different program_ids and make cross-runtime films implementation-specific by construction — defeating the purpose of the exercise.",
  "shape": "DeriveRequest{program_sem_id, implementation_id, canonical_inputs, granted_resources}; the portable film commits program_sem_id, while refinement and release receipts may commit both.",
  "note": "this also converges with realm separation: structured cloning refuses functions, so a derivation crossing a worker boundary must name a program rather than ship a closure — which is most of what a film needs to identify a step."
 },
 "changelog_from_1_15_0": [
  "derivation.serialized-boundary@1 SUPERSEDED by @2. Two sentences of @1 were not supported by the mechanism, both reproduced by external review and frozen as probe_derivegrant_v02_repro.mjs: the read footprint was bypassable via {op:'input', name:'__reads'}, and implementation_id was a caller-asserted field nothing verified.",
  "new law derivation.grant-footprint-separation@1: the authority grant and the observed footprint are two evidence objects; the grant may be broader; freshness keys on the footprint; the authority validates the footprint as a subset of the grant on its own evidence, before re-deriving.",
  "new law derivation.implementation-provenance@1: the executor asserts implementation_id and the caller may only require it. Excluded from the semantic projection, so cross-implementation validation can agree on semantics while provenance stays distinguishable. Byte-binding declared open.",
  "derive_protocol.mjs 0.2.0 joins artifact_versions: read_grants/grant_id, footprintWithinGrant, semanticProjection, and an evaluator that builds its reader from canonical grant data instead of taking a reader callable.",
  "derivation_language ruled: small total core plus named semantic primitives with content-bound primitive_sem_id — never if/while/closure/eval. Component reachability is the first primitive. Declared, not built.",
  "film_planes separates the ic32 interaction-net film from the derivation evidence relation, so cross-replay of the tiny derivation AST cannot be reported as the pack-v3 semantic-film gap being closed. The native film round is not gated on the derivation language."
 ],
 "artifact_versions": {
  "trvm_law_kernel.mjs": "1.1.0",
  "trvm_world.mjs": "0.12.0",
  "derive_protocol.mjs": "0.2.0"
 }
}
```

## `record/artifacts-derivation-boundary.json`

```json
{
 "derivation_boundary": {
  "status": "v0.2.0 — protocol proven in-process and across a worker; NOT yet the production derivation path",
  "files": {
   "derive_protocol.mjs": "program-as-data, canonical request/result schemas, program registry whose key is the program's hash, authority grants separated from the observed read footprint",
   "derive_battery.mjs": "21 falsifiers, in-process",
   "derive_worker.mjs": "the far side; holds no parent reference, resolves programs from its own registry, reads only its grant snapshot, and asserts its own implementation_id",
   "derive_realm_battery.mjs": "9 falsifiers across a real worker boundary",
   "probe_derivegrant_v02_repro.mjs": "the two v0.1.0 defects, frozen — and the same witnesses run against live, which is what makes it a gate rather than a document"
  },
  "two_evidence_objects": {
   "read_grants + grant_id": "the AUTHORITY GRANT — what the authority made available. A capability record, deliberately allowed to be broader than what is read, because under data-dependent traversal the authority cannot know the needed subset in advance. grant_id = H(canonical read_grants) binds the snapshot so it cannot be edited in flight.",
   "read_footprint": "the OBSERVED DEPENDENCY RECORD — what the program actually consumed through a tracked read or scope. Freshness, invalidation, replay and support analysis key on THIS. Defining it as the grant would over-invalidate every derivation whose grant was wider than its reads, which under snapshot granting is all of them.",
   "why_separate": "v0.1.0's prose said the footprint was 'the authority's record of what it read on the derivation's behalf'. That was two errors at once: it described a collapse that would break freshness, and the mechanism did not even implement the collapse — the worker sourced its read table from canonical_inputs, and {op:'input', name:'__reads'} returned the whole table with zero tracked reads."
  },
  "granting_model": "SNAPSHOT (model A): the authority resolves a bounded canonical world slice once, and both the executor and the re-deriving authority evaluate against those same bytes. Chosen over read-RPC (model B) because it is deterministic, films cleanly, and does not turn every primitive evaluation into a cross-realm round trip. The cost is least-authority: the grant may reveal more than the program reads. Confidentiality against the derivation realm is the trigger to revisit, and it is named here rather than discovered later.",
  "claimed": "OBJECT authority does not cross: structured cloning refuses callables (DataCloneError), the worker resolves program_sem_id against its own registry, it can read only the grant snapshot the authority resolved, the returned footprint is validated as a SUBSET of that grant on the authority's own evidence before any re-derivation, the executor asserts implementation_id and the caller may only state a requirement against it, and a returned result is re-derived by the authority — on the semantic projection, so a conforming foreign implementation can agree — before it is evidence.",
  "not_claimed": "determinism of a long-lived evaluator; host confinement; that any existing measureFn has been ported; and that implementation_id is bound to executable BYTES — it is a declared constant, so impersonation is closed and provenance is not. A modified JS worker still emits impl-js-derive-v0.2.0. Four separate scopes, named separately in realm_roadmap and derivation_language."
 },
 "probe_roles_derive": "DERIVE-v0.2 — the bypassable read footprint and the unverified implementation_id, frozen against v0.1.0 and CONFINED against live; the only PAIRED probe, and it gates",
 "case_input_note": "derive_protocol.mjs and derive_worker.mjs moved from tools to case_inputs at v1.16: their SOURCE now carries invariants grid_check asserts (no __reads path, reads from read_grants, executor-asserted implementation_id), so they must be present in every scratch case for those assertions to run. The batteries stay tools — they are runners, not artifacts under test."
}
```

## `record/grid_check-derivation-assertions.mjs.txt`

```javascript
  }
  // ── the serialized derivation boundary at v0.2.0 (v1.16) ────────────────
  // Both v0.1.0 defects were reachable through ONE LINE of the worker each, and
  // both are the kind that reads as harmless: a convenient place to put the read
  // table, and a field passed through from the request. Locked at the source.
  {
    const dsrc = existsSync(A("derive_protocol.mjs")) ? readFileSync(A("derive_protocol.mjs"), "utf8") : "";
    const wsrcD = existsSync(A("derive_worker.mjs")) ? readFileSync(A("derive_worker.mjs"), "utf8") : "";
    ok(dsrc.length > 0 && wsrcD.length > 0, "derive_protocol.mjs or derive_worker.mjs absent (v1.16)");
    // comments stripped first: these files DOCUMENT the defect they must not
    // contain, and a scan that cannot tell the code from the account of the code
    // fires on its own record. Scoped to this check rather than made general —
    // a naive strip is wrong on a string carrying "//", and neither file has one.
    const codeOnly = (s) => s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/[^\n]*/g, "");
    ok(!/canonical_inputs\.__reads|canonical_inputs\["__reads"\]/.test(codeOnly(dsrc) + codeOnly(wsrcD)),
      "the derivation boundary sources the read table from canonical_inputs again (W-1) — the language " +
      "has {op:'input', name:…}, so anything reachable as an input is reachable with NO tracked read, " +
      "which is what made the v0.1.0 read footprint bypassable");
    ok(wsrcD.includes("evaluate(ast, req.read_grants, req.canonical_inputs)"),
      "derive_worker.mjs does not evaluate against req.read_grants — reads must come from the authority's " +
      "grant snapshot and from nowhere else");
    ok(wsrcD.includes("implementation_id: JS_IMPLEMENTATION_ID") && !/implementation_id:\s*req\./.test(wsrcD),
      "derive_worker.mjs must ASSERT its own implementation_id and must not echo the request's (W-2) — " +
      "a field the caller sets and no executor checks is decoration, not provenance");
    for (const s of ["export function grantId", "export function footprintWithinGrant",
      "export const SEMANTIC_RESULT_FIELDS", "footprint-ungranted-read", "request-grant-id-mismatch",
      "implementation-mismatch: want"])
      ok(dsrc.includes(s), `derive_protocol.mjs missing v0.2.0 construct "${s}"`);
    ok(/SEMANTIC_RESULT_FIELDS = RESULT_FIELDS\.filter\(\(f\) => f !== "implementation_id"\)/.test(dsrc),
      "derive_protocol.mjs must exclude implementation_id from the semantic projection — including it " +
      "would make cross-implementation validation fail by construction, which is the whole reason the " +
      "film identity split exists");
    ok(!!g.derivation_language && g.derivation_language.not_built != null,
      "grid derivation_language missing (v1.16) — small total core plus named semantic primitives is a " +
      "RULING made before the expressiveness round, and it must not quietly become a general language");
    ok(!!g.film_planes?.ruling,
      "grid film_planes missing (v1.16) — the ic32 interaction-net film and the derivation evidence " +
      "relation are two transition systems, and cross-replay of one may not be reported as the other");
    const gf = entries.find((x) => x.id === "derivation.grant-footprint-separation");
    ok(!!gf && gf.canonical === true,
      "law derivation.grant-footprint-separation@1 missing or non-canonical — collapsing the grant into " +
      "the footprint breaks freshness, and the record has already made that mistake once");
    const ip = entries.find((x) => x.id === "derivation.implementation-provenance");
    ok(!!ip && /DECLARED OPEN/.test(ip.statement ?? ""),
      "law derivation.implementation-provenance@1 missing, or no longer declares its open half — " +
      "implementation_id is a constant, so IMPERSONATION is closed and PROVENANCE is not, and that " +
      "limit may not fall off the record");
  }
  ok(!!g.film_identity_forward_declaration,
```

## `record/negative-cases-round15.sh`

```bash
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

run_case derive-semantic-projection-widened "exclude implementation_id from the semantic projection" "
src = open('derive_protocol.mjs').read()
src = src.replace('RESULT_FIELDS.filter((f) => f !== \"implementation_id\")', 'RESULT_FIELDS.slice()')
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

echo; [ $FAILED -eq 0 ] && echo "NEGATIVE BATTERY: $CASES/$CASES forgeries caught" || echo "NEGATIVE BATTERY: FAILURES PRESENT ($CAUGHT/$CASES caught)"
exit $FAILED
```

## `gate/derive_battery.txt`

```text
$ cd code && node derive_battery.mjs
PASS  program-id-is-content              two programs, two ids (psem-f154679ca… vs psem-98a7236cc…); recomputing P's id reproduces it
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
PASS  implementation-id-asserted         the result carries impl-js-derive-v0.2.0, emitted by the evaluator that ran. At v0.1.0 the REQUEST carried implementation_id, nothing checked it and the result carried none (W-2)
PASS  implementation-requirement-refused a request demanding a C executor is refused BY the JS executor (implementation-mismatch: want impl-c-pretend-v9, this is impl-js-derive-v0.2.0) — the caller's field states a requirement and the executor answers it, so impersonation has no path
PASS  implementation-id-well-formed      a result whose implementation_id is not an impl- identity is refused: result-implementation-id-malformed
PASS  semantic-projection-is-portable    a result identical in semantics but produced by impl-c-derive-v0.2.0 validates, and the authority records WHO ran it (impl-c-derive-v0.2.0). program_sem_id is equal across implementations; implementation_id is outside the semantic projection, which is what makes a portable film possible
PASS  implementation-requirement-checked-on-result a result from a different executor than the one required is refused: implementation-mismatch: want impl-js-derive-v0.2.0, result claims impl-c-derive-v0.2.0
PASS  registry-binding-verified          verify(PID) recomputes the hash and agrees; an unbound id is refused (program-unknown)
PASS  registry-entry-frozen              the stored program is deep-frozen; mutating it throws and the registry still reads 'add'
════════════════════════════════════════════════════════════════════════════════════════════════
DERIVE-BATTERY: PASS — 21/21. The program is data and its id is its hash; the grant is what the authority made available and the footprint is what the program consumed; the executor asserts its own identity; and a foreign result is re-derived before it is evidence.
```

## `gate/derive_realm_battery.txt`

```text
$ cd code && node derive_realm_battery.mjs
PASS  closure-cannot-cross             postMessage of a request carrying a function throws — DataCloneError: () => 1 could not be cloned.. The 9D.4 lexical-cell attack has no transport: structured cloning refuses callables, so the confinement is done by the boundary rather than by object discipline
PASS  crossing-derives                 worker returned value 5 for fb=5 bias=0, resolving the program from its OWN registry by id and stamping the result impl-js-derive-v0.2.0 against grant grant-d32ef00d02de…
PASS  claim-revalidated-at-home        the worker's honest result reproduces locally against the same snapshot; an inflated one is refused (foreign-result-divergence)
PASS  ungranted-read-refused           derivation-threw: read-not-granted: fb — resolving reads is an AUTHORITY operation the parent performs; the worker holds no world and needs none
PASS  unknown-program-refused          program-unknown — the worker resolves ids against its own registry, so a caller cannot name code the worker does not hold
PASS  grant-not-reachable-as-input     the worker granted fb and secret:key returns "an ordinary input" for {op:"input",name:"__reads"} — at v0.1.0 this returned the whole grant table across the same boundary, with an empty footprint and zero tracked reads
PASS  executor-asserts-implementation  a request demanding a C executor is refused by the JS worker (implementation-mismatch: want impl-c-pretend-v9, this is impl-js-derive-v0.2.0); one demanding JS runs and returns its own id. The caller states a requirement; the executor answers it
PASS  foreign-footprint-refused        footprint-ungranted-read: secret:key — the authority checks the returned footprint against the grant it issued, on its own evidence. The footprint is the dependency record and the grant is the capability record; the round-14 prose collapsed them and the mechanism supported neither
PASS  cross-implementation-shape       the same result stamped by a C executor validates and its provenance is RECORDED rather than compared away. This is the shape a real C implementation plugs into — it is not a claim that one exists, and this battery does not have one
════════════════════════════════════════════════════════════════════════════════════════════════
DERIVE-REALM: PASS — object authority does not cross the boundary, the realm reads only its grant, and the executor names itself. Determinism and host confinement are SEPARATE scopes and are not claimed here.
```

## `gate/probe_derivegrant.txt`

```text
$ cd code && node probe_derivegrant_v02_repro.mjs
BREACH    W-1 frozen-v0.1.0                  program {op:"input",name:"__reads"} returned the whole grant table (secret:key = 42) with witness.reads = 0, support = [], read_footprint.exact = [] — a read that consumed authority data and produced no dependency record
BREACH    W-2 frozen-v0.1.0                  a request asserting implementation_id "impl-c-pretend-v9" was executed by the JS evaluator and returned ok=true; the result carries no implementation_id at all (fields: program_sem_id,read_footprint,request_id,support,value,witness) — nothing to verify against
CONFINED  W-1 live                           the same program now returns only what the CALLER put in canonical_inputs ("not the grant table"); read_grants is a separate field the input op cannot address, so the grant table is not reachable without a tracked read
CONFINED  W-2 live                           the executor asserts its own id (impl-js-derive-v0.2.0); a request demanding "impl-c-pretend-v9" is refused by the executor itself (implementation-mismatch: want impl-c-pretend-v9, this is impl-js-derive-v0.2.0) — the caller's field is a REQUIREMENT, the result's field is an ASSERTION
====================================================================================================
DERIVE-GRANT-v0.2 REPRO: 2/2 reproduce against the frozen v0.1.0 · 2/2 confined against live
```

## `gate/make-governance.txt`

```text
# Gate output, captured verbatim — 2026-08-19T01:22Z, node v25.2.1

$ make governance
==== [governance] law kernel — conformance + the periodic-law grid ====
════════════════════════════════════════════════════════════════════════════════════════════════
VERDICT: PASS — conformant; every asserted law holds; every by-design falsification still fails; certificate emitted.
==== [governance] invariant grid — registry, citations, engine-free receipts ====
GRID-CONSISTENCY-2: PASS — registry valid (56 entries), 339 citations resolved across 16 artifacts, no banned stale claims, structure coherent with v1.16.0. [root /home/travis/ProjectAmp2/TRVM/governance]
==== [governance] World — warrants, maintenance, confinement ====
VERDICT: PASS — the WORLD layer's warrant machinery holds; receipt emitted.
RECEIPT-CHECK: PASS — world rebuilt from committed spec; ground and composite REPLAYED with support equality; commitment recomputed.
==== [governance] negative battery — every forgery must be caught ====
NEGATIVE BATTERY: 76/76 forgeries caught
==== [governance] cross-plane bridge — C canonical bytes vs the JS oracle ====
BRIDGE-CHECK: PASS — 48/48 states byte-identical across implementations (24 vectors x {initial, normal form}); C packed-word heap and JS node graph reach the same canonical signature STRING, not merely the same digest.
==== [governance] serialized derivation boundary ====
DERIVE-BATTERY: PASS — 21/21. The program is data and its id is its hash; the grant is what the authority made available and the footprint is what the program consumed; the executor asserts its own identity; and a foreign result is re-derived before it is evidence.
DERIVE-REALM: PASS — object authority does not cross the boundary, the realm reads only its grant, and the executor names itself. Determinism and host confinement are SEPARATE scopes and are not claimed here.
DERIVE-GRANT-v0.2 REPRO: 2/2 reproduce against the frozen v0.1.0 · 2/2 confined against live
  evidence plane green
```

## `record/round-15-ledger-section.md`

## Round 15 — the record said the footprint was the grant, and the mechanism said neither

**53. Two sentences of round 14 were not supported by the code, and both witnesses reproduced verbatim before anything was changed.** Review supplied them; they are frozen in `probe_derivegrant_v02_repro.mjs`. **W-1**: the worker sourced its read table from `req.canonical_inputs.__reads`, and the language has `{op:"input", name:…}`, which retrieves *any* canonical input — so the one-node program `{op:"input", name:"__reads"}` returned the entire authority-supplied read table with `witness.reads = 0`, `support = []` and `read_footprint = {exact:[],predicates:[]}`. A derivation consumed authority data and produced no dependency record. **W-2**: a request asserting `implementation_id: "impl-c-pretend-v9"` was executed by the JavaScript evaluator and returned success, and `DeriveResult` carried no `implementation_id` at all. Neither defect needed more than one line of the worker, and both read as harmless: a convenient place to put the read table, and a field passed through from the request.

**54. The repair is not to redefine the footprint as the grant — they are two evidence objects and collapsing them loses both.** The **grant** (`read_grants`, named by `grant_id = H(canonical read_grants)`) is a *capability* record: what the authority made available. It is allowed to be broader than what is read, and under data-dependent traversal it must be — `read adj:a → discover b → read edge:a|b` cannot be pre-resolved to its exact subset. The **footprint** is the *dependency* record: what the program consumed through a tracked read. Freshness, invalidation, replay and support analysis key on the footprint alone, so defining it as the grant would invalidate every derivation whenever any granted-but-unread resource moved — which under snapshot granting is every derivation. The battery states it as arithmetic: a 3-resource grant against a 1-entry footprint, with the two unused resources named. `input` now addresses `canonical_inputs` only; `read`/`scope` address `read_grants` only; and the authority validates the returned footprint as a **subset of the grant it issued**, at the granted versions and scope digests, *on its own evidence and before any re-derivation* — `footprint-ungranted-read: secret:key` fires against an otherwise honest result whose value would have re-derived equal.

**55. `law:derivation.serialized-boundary@1` is superseded by `@2` rather than edited.** Revision 1 is kept as the honest record of an overclaim, with a `revision_note` naming both unsupported sentences. Two new laws carry what @1 was reaching for: `law:derivation.grant-footprint-separation@1` and `law:derivation.implementation-provenance@1`. The **granting model is now a decision rather than a default** — snapshot (A) over read-RPC (B), because it is deterministic, films cleanly and does not turn every primitive evaluation into a cross-realm round trip. Its cost is stated where it will be needed: the grant may reveal more than the program reads, so confidentiality against the derivation realm is the trigger to revisit, not a property this design already has.

**56. `implementation_id` becomes load-bearing in one direction, and the other is declared open rather than implied.** The executor **asserts** it; the caller may only state `expected_implementation_id`, which an executor that cannot satisfy it refuses by name — so impersonation has no path, and the JS worker refuses a request demanding a C executor across a real boundary. It is excluded from the **semantic projection** that cross-implementation validation compares, which is the operative half of the `program_sem_id`/`implementation_id` split: a result stamped `impl-c-derive-v0.2.0` validates against a JS re-derivation and its provenance is *recorded* rather than compared away. Comparing whole results would have made cross-implementation validation fail by construction. **Still open, and stated in the law's own text:** `implementation_id` is a declared constant, not a digest of executable bytes, so a *modified* JS worker still emits `impl-js-derive-v0.2.0`. Impersonation is closed; provenance is not.

**57. §49 is retracted.** It read: *"the footprint is now the authority's record of what it read on the derivation's behalf, not the derivation's claim about what it touched."* That was wrong twice over — it described a collapse that would break freshness, and the mechanism did not implement even the collapse it described. What is true at v0.2.0 is the sentence §49 should have contained: the authority decides and records what data crosses into the derivation realm; the derivation records what it consumed; and the authority validates the second against the first. §51's *scope* statement stands unchanged.

**58. A third defect, found while repairing the first two, in the module built to remove exactly this.** `evaluate(ast, reader, inputs)` took the reader as a **callable parameter**, and `deriveLocally` passed the caller's. That is the closure-authority shape in miniature — not a boundary hole, since the worker built its own reader from data and no function survives `postMessage`, but the same species living in the authority's own path in the file whose header describes why closures are unbounded capability containers. The evaluator now builds its reader from canonical grant data and nothing else, and a pair of reader callables in the grant position is refused *as data*: `grants-schema: [read,scope]`. Related, and found by the battery rather than by reading: `evaluate` was not total over its input domain — a malformed grant produced a raw `TypeError` instead of a named refusal. Fixed in the code, not in the assertion that caught it.

**59. The probe is PAIRED, and it is the first probe in this tree that gates.** Its siblings freeze a boundary that is *declared* open, so they report a breach and that is the record. These two defects are repaired, so a one-directional probe would pass just as happily if the frozen copy were quietly replaced with the repaired one. It therefore runs each witness twice: against the embedded v0.1.0 copy, where it **must still reproduce** — a witness that stops reproducing against the version it was written for has stopped measuring — and against the live modules, where it must be confined. `law:evidence.instrument-nonvacuity@1` applied to a repro. The frozen copy runs in a real `worker_threads` realm from a `data:` URL, because W-1 was a defect in the worker's *wiring* rather than in the shared evaluator, and nothing is written to the artifact tree.

**60. The language is ruled before the expressiveness round, not during it.** **Small total core plus named semantic primitives.** The nine-op core stays; complex behaviour arrives as `{op:"prim", primitive_sem_id, args}` and never as `if`/`while`/`function`/`closure`/`recursion`/`eval`. A general programming language at the derivation boundary re-admits the unbounded capability container that `law:derivation.environment-confinement@1` was falsified by, in a form that serializes. `primitive_sem_id` must be **content-bound** — H(primitive language/version + canonical input/output contract + semantic specification identity + conformance-vector identity) — because `"componentReachability"` as a bare string is exactly the caller-selected label `program_sem_id` refuses. Component reachability is the first primitive, chosen because it is materially harder than arithmetic: traversal, data-dependent reads, support, adjacency footprints and the phantom-scope case all appear in it at once, and it still has a total semantic definition over a finite grant snapshot. Declared; not built.

**61. Two transition systems had started to be discussed in the same words, and the failure mode is specific.** `film_planes` separates them. The **TRVM calculus film** is `semantic pre-state → (rule + canonical locus) → semantic post-state` over the ic32 interaction-net relation, contracted by conformance §10/§10.5 — canonical bytes agree C↔JS at 48/48 and **no native runtime emits films yet**. The **derivation evidence** relation is `DeriveRequest → evaluate → DeriveResult`, and it has one implementation. Porting `add`/`read`/`input` to C would prove the second and would **not** close the first. Without that distinction a session could finish cross-replay on the tiny derivation AST and write *"cross-implementation semantic films complete"* while pack-v3's milestones 5, 9, 10 and 11 stand untouched. So the roadmap is re-ordered: **native ic32 film emission is not gated on the derivation language** and proceeds on the existing conformance contract. The convergence that would make them one system — `DeriveProgram AST → canonical lowering → interaction-net term → ic32 → semantic film`, one execution substrate rather than a derivation interpreter beside a rewrite runtime — is recorded as reachable and **not adopted**, which is the reason not to build so much dedicated interpreter machinery that the option closes.

**62. Gate.** grid **v1.16.0** — 56 entries / 339 citations · `derive_protocol.mjs` **0.2.0** joins `artifact_versions` · kernel PASS (CONF-1 24/24 · CONF-2 REGRESSION-LOCKED) · World 0.12.0 PASS · `--check-receipt` PASS · negative battery **76/76** with nine new forgeries, each caught by its own diagnostic · bridge 48/48 · derive **21/21 in-process, 9/9 across a realm, 2/2 + 2/2 paired**. `scheduler_certificate.json` reproduced byte-identically — `cert_id` unmoved, the calculus untouched for a tenth consecutive round.

**63. And the artifact-root round had two reads it said it had closed.** Round 14 recorded that ambient CWD discovery was *"replaced by explicit roots anchored at `import.meta.url`"* across `grid_check`. The root was introduced and `A()` applied to most reads — but the **citation scan**, the primary evidence loop of the whole checker, still resolved every artifact against the working directory, and so did the **banned-phrase tripwire**. Found by running the checker from one directory up, which is not a clever test. The two failure modes differ, and the second is the one that matters: the citation scan reported `artifact missing` for all sixteen artifacts and failed loudly, while the banned-phrase loop was written `existsSync(f) ? readFileSync(f) : ""` — an absent file scanned the **empty string** and every banned-phrase check passed vacuously. From any directory but `governance/` the tripwire reported clean while measuring nothing. Both anchored at `ROOT` at v2.21, absence is now a failure rather than an empty scan, and the checker produces identical output from `governance/`, from `TRVM/`, and from `/` under `TRVM_GOV_ROOT`. The round-14 claim was not false about its intent and was false about its extent, which is the difference the record cares about: **five rounds running, the instrument has been the thing that was wrong.**

**Where this leaves the ladder.** Rounds 9B–9D.4 walked a seal outward until the authority stopped being an object. Round 14 replaced the API and proved the transport does the confining. **Round 15 is the first round in that sequence where the defect was in the record rather than in the boundary** — the mechanism was sound about what crossed and wrong about what it was recording, and a footprint that can be produced without a read is not a weaker dependency record, it is not one. The next boundary is still the process. The next *evidence* is a native film.
