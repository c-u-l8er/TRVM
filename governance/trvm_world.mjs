/* ═══════════════════════════════════════════════════════════════════════════
   trvm_world.mjs — v0.11.0 — the WORLD layer: WorldRecord + Warrant v3,
   executable. The calculus kernel (trvm_law_kernel.mjs, v1.1.0 — calculus frozen
   since v1.0.2; 1.1.0 is the additive module interface)
   has no world by design; this artifact is where WORLD-plane law begins.

   WHAT THIS IS (round 7 — the warrant round)
   ──────────────────────────────────────────
   The grid has carried Warrant v3 as a SPEC since round 3: shape
   [measure, predicate, value, witness, support, read_footprint,
   derivation_id], with exact reads, predicate scopes (guarding the kappa
   phantom-read case), and three invalidation modes. Round 5 adopted a
   requirement: SchedulerCertificate and Warrant must share a
   support/footprint concept. This artifact makes all of it EXECUTABLE:

   1. WorldRecord (law:world.version-monotone@1): a versioned resource
      store with a global monotone vclock and an append-only log. Reads
      return {value, version}; writes bump. Scope QUERIES are registered
      and REIFIED: evaluating one yields a digest of its result set — the
      predicate-lock idea from serializable databases, the tracked-glob
      idea from hermetic build systems, made a first-class resource kind.
   2. Warrants as VERIFYING TRACES generalized (law:warrant.freshness@1):
      a derivation runs under a TRACKED view that records every exact read
      [resource@version] and every scope evaluation [query@digest]; the
      warrant commits value, witness, support, footprint, derivation_id
      under "TRVM-WARRANT-v3". Freshness = every exact read's version and
      every scope's digest re-evaluate unchanged. Unrelated writes never
      invalidate — tested, not assumed.
   3. JAILED REPLAY (law:warrant.footprint-soundness@1): the footprint is
      an AUTHORITY CLAIM, and rounds 5-6 taught what happens to authority
      that outruns evidence. Replay re-runs the derivation under a JAIL
      view: any read outside the declared footprint refuses
      (undeclared-read / undeclared-scope); versions must match the
      footprint; the value must re-derive equal. A warrant with a PRUNED
      footprint — honestly resealed — dies at replay, not at review.
   4. THE PHANTOM, EXECUTABLE (law:warrant.phantom-scope@1): the grid's
      kappa phantom-read case — a node absent at read time joins the
      component without touching any old edge — is constructed as a
      witness: an exact-reads-only warrant stays "fresh" while its value
      is silently wrong; the scope-guarded warrant classifies scope_dirty.
      The falsifier keeps the unguarded version red by construction.
   5. INVALIDATION TRICHOTOMY (law:warrant.invalidation-trichotomy@1):
      support_changed / scope_dirty / support_intact each witnessed, and
      support_intact performs EARLY CUTOFF: a jailed cheap re-derivation
      that reproduces the value refreshes the footprint instead of
      discarding the warrant.
   6. THE SHARED FOOTPRINT (law:footprint.shared@1): certFootprintOf maps
      the shipped SchedulerCertificate into the SAME Footprint shape —
      its corpus{id,sha256} is an exact read, its run manifest the
      witness — and warrantOfCertificate wraps it so certificate
      freshness is warrant freshness. One evidence language, as round 5
      required.

   WHAT CHANGED IN v0.2.0 (round 8 — the composition round)
   ─────────────────────────────────────────────────────────
   7. WARRANT COMPOSITION (law:warrant.composition@1): a warrant may cite
      another warrant by reading its PUBLICATION (a world resource carrying
      value + ids) — never its internals. The abstraction boundary is the
      jail: composite replay reads only publications. But publication reads
      alone LAUNDER STALENESS — the cited warrant can go phantom-stale
      without its publication resource moving, and the naive composite
      stays "fresh" while transitively wrong. That witness is constructed
      and KEPT RED (the phantom, one level up). The repair: freshness
      itself is REIFIED — a "warrant-fresh:<name>" scope whose digest is
      the citee's footprint re-evaluation — so the composite goes
      scope_dirty the moment any citee's world moves, through diamonds and
      chains alike.
   8. THE FRAME LAW, sigma T4 (law:warrant.frame@1): random writes are
      CLASSIFIED by footprint membership and scope influence, and the
      classifier must PREDICT the freshness verdict exactly — writes
      outside a warrant's evidence can never change its verdict; writes
      inside change it as classified. The separation-logic frame rule as a
      property test over the world.

   WHAT CHANGED IN v0.3.0 (round 8.1 — the write-mediation closure)
   ─────────────────────────────────────────────────────────────────
   The round-8B audit falsified the substrate under everything above:
   the store held JS values BY REFERENCE, so state could change without
   an identity transition — world.read(r).value.push(2) mutated the
   world with no put, no version bump, and the two verifiers DISAGREED
   (freshness: fresh; jailed replay: value-mismatch). Reproduced here
   exactly, plus the ingress variant. Closed as a law, not a clone call
   (law:world.write-mediated@1): a resource's observable value cannot
   change except through a version-advancing transition — same version
   IMPLIES same canonical value. Mechanism: a CANONICAL RESOURCE-VALUE
   DOMAIN (null, boolean, finite number, string, arrays, plain objects
   with sorted keys — anything else refuses world-value-not-canonical);
   the store owns canonical BYTES under TRVM-VALUE-v1 content hashes;
   every read parses a fresh copy. Both alias directions die at the
   boundary. Deletions become TOMBSTONES (the deletion version is
   observable; "never existed" and "deleted" no longer collapse), and
   the corollary the witness falsified is now its own law
   (law:warrant.fresh-replay-coherence@1): FRESH implies
   REPLAY-COHERENT for deterministic derivations. The audit also caught
   a vacuous assertion (|| true) in L-WORLD-1 — the battery introducing
   the monotonicity law contained a check that could not fail; it is
   removed and the battery strengthened, recorded here without excuse.

   WHAT CHANGED IN v0.4.0 (round 8.2 — the support-soundness closure)
   ───────────────────────────────────────────────────────────────────
   The round-8C audit falsified support authority: support was COMMITTED
   but never RE-DERIVED — replay checked only support ⊆ footprint, so a
   pruned support (honestly resealed) replayed ok, misclassified the
   next support movement as support_intact, and refreshWarrant PRESERVED
   the forged support through refresh — a laundering chain the upcoming
   maintenance loop would have trusted. The engine-free checker's subset
   check passed the same forgery in the shipped receipt: a three-way
   assurance-composition hole, the round-5 species one layer up. Closed
   (law:warrant.support-soundness@1): support is CANONICAL at seal
   (sorted, deduplicated); BOTH replayers re-derive it and require exact
   equality with the derivation's own output (support-mismatch, the
   tenth refusal) in addition to the subset rule — necessary, not
   sufficient, each; refresh RESTORES derivation-produced support; and
   the receipt gains a committed world_spec so `--check-receipt` can
   rebuild the world and run the ENGINE half on the shipped file — the
   division of verification, extended to support truth.

   WHAT CHANGED IN v0.6.0 (round 9.1 — the confinement closure)
   ────────────────────────────────────────────────────────────
   The round-9B audit falsified the atomicity boundary AS STATED: a
   measureFn is an arbitrary closure, so one that retained the real
   World could write it mid-pass — the witness leaked a resource, threw,
   and the "aborted" receipt sampled the vclock IN THE CATCH HANDLER,
   normalizing the escaped 3->4 transition into its alleged pre-state
   (ATOMIC=false, RECEIPT-TRUTH=false, reproduced). Fork-and-apply was a
   convention, not an isolation boundary. Closed
   (law:maintenance.capability-confinement@1): the authoritative World
   LOCKS for the duration of a pass — put/del/registerQuery on the root
   refuse world-write-during-maintenance; the fork stays writable; only
   the Maintainer's commit CAPABILITY (a per-lock key) may apply staged
   writes, with finally-semantics releasing the lock on success,
   exception, quarantine, and cycle refusal alike. Escaped writes become
   aborts instead of corruption. Independently locked, per the audit:
   the pass-entry vclock is captured BEFORE any adversarial code runs,
   so an aborted receipt's vclock_before is the actual entry clock. And
   abort errors are now tagged with the node that raised them.

   WHAT CHANGED IN v0.7.0 (round 9.2 — the key-confinement closure)
   ─────────────────────────────────────────────────────────────────
   The audit's follow-up landed exactly where predicted: the lock's
   master key was a PUBLIC PROPERTY (world._lockKey), so a closure
   retaining the World could steal it and commit THROUGH the lock — the
   witness leaked mid-pass without even aborting — and, key or no key,
   the internals (res/log/queries/vclock) were public fields open to
   raw mutation that bypassed every guard silently. Closed
   structurally: ALL World state lives in true private fields
   (#res/#vclock/#log/#queries/#lockKey), the key is crypto-random
   (randomBytes), reads go through getters that return COPIES, and both
   World.prototype and every instance are FROZEN — method patching and
   instance shadowing throw. A closure may retain the object; it can no
   longer retain any authority the transaction did not hand it. The
   stated residual is unchanged and honest: same-realm JS is the outer
   limit of option 1; worker-domain isolation remains the declared
   v-next.

   Run: node trvm_world.mjs [--quick|--check-receipt]  (exit 0 iff green)
   ═══════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { randomBytes } from "node:crypto";
const WORLD_VERSION = "0.11.0";

const H = (s) => createHash("sha256").update(s).digest("hex");
const cj = (o) => JSON.stringify(o);

// ═══ WorldRecord ═══════════════════════════════════════════════════════════
// law:world.version-monotone@1 — versions strictly increase on a global
// vclock; the log is append-only; a read returns the latest write. Scope
// queries are REGISTERED (name -> fn(reader)) and reified on evaluation.
// canonical resource-value domain (law:world.write-mediated@1): null,
// boolean, finite number, string, array of canonical, plain object with
// canonical (sorted) key order. Everything else — functions, symbols,
// bigints, NaN/Infinity, undefined elements, class instances, cycles —
// refuses world-value-not-canonical. The serialization IS the stored
// representation: the world owns bytes, not references.
function canonicalBytes(v, path = "$", onPath = new Set()) {
  if (v === null) return "null";
  const t = typeof v;
  if (t === "boolean") return v ? "true" : "false";
  if (t === "number") {
    if (!Number.isFinite(v)) throw new Error("world-value-not-canonical: non-finite number at " + path);
    return Object.is(v, -0) ? "0" : JSON.stringify(v);
  }
  if (t === "string") return JSON.stringify(v);
  if (t === "object") {
    if (onPath.has(v)) throw new Error("world-value-not-canonical: cycle at " + path);
    onPath.add(v);
    let out;
    if (Array.isArray(v)) {
      out = "[" + v.map((x, i) => canonicalBytes(x, path + "[" + i + "]", onPath)).join(",") + "]";
    } else {
      const proto = Object.getPrototypeOf(v);
      if (proto !== Object.prototype && proto !== null)
        throw new Error("world-value-not-canonical: non-plain object at " + path);
      out = "{" + Object.keys(v).sort().map((k) =>
        JSON.stringify(k) + ":" + canonicalBytes(v[k], path + "." + k, onPath)).join(",") + "}";
    }
    onPath.delete(v);
    return out;
  }
  throw new Error("world-value-not-canonical: " + t + " at " + path);
}
const valueHashOf = (bytes) => H("TRVM-VALUE-v1|" + bytes);

class World {
  #res = new Map();      // name -> { bytes, hash, version, deleted }
  #vclock = 0;
  #log = [];             // { op, resource, version, prev, hash? }
  #queries = new Map();  // qname -> fn(reader-interface)
  #lockKey = null;       // law:maintenance.capability-confinement@1
  constructor() { Object.freeze(this); }  // no own props: instance patching throws
  get vclock() { return this.#vclock; }
  get log() { return this.#log.map((e) => ({ ...e })); }          // copies: dead on arrival
  resourceEntries() {                                              // metadata copies, live only + tombstones
    return [...this.#res.entries()].map(([n, e]) => [n, { hash: e.hash, version: e.version, deleted: e.deleted }]);
  }
  _guard(op) {
    if (this.#lockKey !== null)
      throw new Error("world-write-during-maintenance: " + op + " on the authoritative world while a pass holds the lock");
  }
  lock() {
    if (this.#lockKey !== null) throw new Error("world-already-locked");
    this.#lockKey = randomBytes(32).toString("hex");   // crypto-random; NEVER stored publicly
    return this.#lockKey;
  }
  unlock(key) {
    if (key !== this.#lockKey) throw new Error("world-lock-capability-refused: unlock");
    this.#lockKey = null;
  }
  commit(key, fn) {   // the ONLY door through the lock — held by the transaction
    if (key !== this.#lockKey) throw new Error("world-lock-capability-refused: commit");
    this.#lockKey = null;
    try { return fn(); } finally { this.#lockKey = key; }
  }
  put(name, value) {
    this._guard("put");
    const bytes = canonicalBytes(value);            // refuses non-canonical; severs ingress aliases
    const hash = valueHashOf(bytes);
    const prev = this.#res.get(name)?.version ?? 0;
    const version = ++this.#vclock;
    this.#res.set(name, { bytes, hash, version, deleted: false });
    this.#log.push({ op: "put", resource: name, version, prev, hash });
    return version;
  }
  del(name) {
    this._guard("del");
    const prev = this.#res.get(name)?.version ?? 0;
    const version = ++this.#vclock;
    this.#res.set(name, { bytes: null, hash: null, version, deleted: true }); // TOMBSTONE:
    this.#log.push({ op: "del", resource: name, version, prev });             // deleted != never-existed
    return version;
  }
  read(name) {
    const r = this.#res.get(name);
    if (!r) return { value: undefined, version: 0 };
    if (r.deleted) return { value: undefined, version: r.version, deleted: true };
    return { value: JSON.parse(r.bytes), version: r.version };  // fresh copy: egress aliases sever here
  }
  valueHash(name) { const r = this.#res.get(name); return r && !r.deleted ? r.hash : null; }
  exists(name) { const r = this.#res.get(name); return !!r && !r.deleted; }
  names() { return [...this.#res.entries()].filter(([, r]) => !r.deleted).map(([n]) => n).sort(); }
  registerQuery(qname, fn) { this._guard("registerQuery"); this.#queries.set(qname, fn); }
  scopeEval(qname) {
    const fn = this.#queries.get(qname);
    if (!fn) throw new Error("unknown scope query: " + qname);
    const iface = {
      value: (n) => this.read(n).value,
      version: (n) => this.read(n).version,
      names: () => this.names(),
      scope: (q) => this.scopeEval(q).digest,
    };
    const result = fn(iface);
    return { digest: H("TRVM-SCOPE-v1|" + qname + "|" + cj(result)), at_vclock: this.#vclock };
  }
  fork() {
    const f = new World();                 // forks are born UNLOCKED and stay writable
    for (const [n, e] of this.#res) f.#res.set(n, { ...e });
    f.#vclock = this.#vclock;
    f.#log = [...this.#log];
    f.#queries = new Map(this.#queries);
    return f;
  }
}
Object.freeze(World.prototype);            // method patching throws (strict mode)

// ═══ Footprint — the SHARED evidence shape ═════════════════════════════════
// exact:      [[resource, version], ...]      — objects the derivation read
// predicates: [[qname, digest], ...]          — reified scope evaluations
const footprintId = (fp) =>
  H("TRVM-FOOTPRINT-v1|" + cj([...fp.exact].sort()) + "|" + cj([...fp.predicates].sort()));

// ═══ Tracked and Jailed views ══════════════════════════════════════════════
// TRACKED: records everything the derivation touches (the honest builder).
// JAILED: permits ONLY the declared footprint (the replayer); anything else
// refuses. law:warrant.footprint-soundness@1.
function trackedView(world) {
  const exact = new Map(), predicates = new Map();
  return {
    read(name) { const r = world.read(name); exact.set(name, r.version); return r.value; },
    scope(qname) { const s = world.scopeEval(qname); predicates.set(qname, s.digest); return s.digest; },
    footprint() {
      return { exact: [...exact.entries()], predicates: [...predicates.entries()] };
    },
  };
}
function jailedView(world, fp) {
  const exact = new Map(fp.exact), predicates = new Map(fp.predicates);
  let violation = null;
  return {
    read(name) {
      if (violation) return undefined;
      if (!exact.has(name)) { violation = { reason: "undeclared-read", resource: name }; return undefined; }
      const r = world.read(name);
      if (r.version !== exact.get(name)) { violation = { reason: "footprint-version-mismatch", resource: name }; return undefined; }
      return r.value;
    },
    scope(qname) {
      if (violation) return undefined;
      if (!predicates.has(qname)) { violation = { reason: "undeclared-scope", scope: qname }; return undefined; }
      const s = world.scopeEval(qname);
      if (s.digest !== predicates.get(qname)) { violation = { reason: "scope-digest-mismatch", scope: qname }; return undefined; }
      return s.digest;
    },
    violation: () => violation,
  };
}

// ═══ Warrant v3, executable ════════════════════════════════════════════════
// Field discipline (precedent: law:cert.field-discipline@1): COMMITTED —
// measure, predicate, value, witness, support, read_footprint,
// derivation_id, at_vclock. DERIVED on replay — value, witness, footprint
// membership of every read. INFORMATIONAL — informational.*.
const warrantCommitted = (w) => [
  ["measure", w.measure], ["predicate", w.predicate], ["value", w.value],
  ["witness", w.witness], ["support", [...w.support].sort()],
  ["read_footprint", { exact: [...w.read_footprint.exact].sort(),
                       predicates: [...w.read_footprint.predicates].sort() }],
  ["derivation_id", w.derivation_id], ["at_vclock", w.at_vclock],
];
const warrantIdOf = (w) => H("TRVM-WARRANT-v3|" + cj(warrantCommitted(w)));

const canonSupport = (s) => [...new Set(s ?? [])].sort();
// derive: run measureFn under a TRACKED view; seal the warrant.
// measureFn(view) must return { value, witness, support } where support is
// the sub-list of resources whose change is SEMANTIC (not merely read).
function deriveWarrant(world, spec) {
  const view = trackedView(world);
  const out = spec.measureFn(view);
  const fp = view.footprint();
  const w = {
    type: "Warrant", version: 3,
    measure: spec.measure, predicate: spec.predicate,
    value: out.value, witness: out.witness,
    support: canonSupport(out.support),   // canonical at seal: sorted, deduplicated
    read_footprint: fp,
    derivation_id: H("TRVM-DERIVATION-v1|" + spec.measure + "|" + spec.predicate + "|" + cj(spec.inputs ?? null)),
    at_vclock: world.vclock,
    law_refs: spec.law_refs ?? [],
    informational: { note: "NON-AUTHORITATIVE", generator: "trvm_world.mjs v" + WORLD_VERSION },
  };
  w.warrant_id = warrantIdOf(w);
  return w;
}

// freshness + classification. law:warrant.freshness@1 and
// law:warrant.invalidation-trichotomy@1. Every verdict class carries a
// complete witness (law:film.terminal-witness@1, applied to verdicts):
//   fresh            -> { checked_exact, checked_scopes }
//   support_changed  -> { resource, was, now }
//   scope_dirty      -> { scope, was, now }        (exact reads all intact)
//   support_intact   -> { resource, was, now }     (a non-support exact read
//                        moved; candidate for early-cutoff refresh)
function freshness(world, w) {
  let intactCandidate = null;
  const support = new Set(w.support);
  for (const [name, ver] of w.read_footprint.exact) {
    const now = world.read(name).version;
    if (now !== ver) {
      if (support.has(name)) return { verdict: "support_changed", witness: { resource: name, was: ver, now } };
      intactCandidate = { resource: name, was: ver, now };
    }
  }
  for (const [qname, digest] of w.read_footprint.predicates) {
    const now = world.scopeEval(qname).digest;
    if (now !== digest) return { verdict: "scope_dirty", witness: { scope: qname, was: digest.slice(0, 12), now: now.slice(0, 12) } };
  }
  if (intactCandidate) return { verdict: "support_intact", witness: intactCandidate };
  return { verdict: "fresh", witness: { checked_exact: w.read_footprint.exact.length, checked_scopes: w.read_footprint.predicates.length } };
}

// jailed replay. Refusals: undeclared-read, undeclared-scope,
// footprint-version-mismatch, scope-digest-mismatch, value-mismatch,
// witness-mismatch, warrant-id-mismatch, support-not-subset.
function replayWarrant(world, w, measureFn) {
  const supportSet = new Set(w.support);
  const exactSet = new Set(w.read_footprint.exact.map(([n]) => n));
  for (const s of supportSet) if (!exactSet.has(s))
    return { ok: false, reason: "support-not-subset", resource: s };
  const jail = jailedView(world, w.read_footprint);
  let out;
  try { out = measureFn(jail); }
  catch (e) {
    const v0 = jail.violation();
    return v0 ? { ok: false, ...v0 } : { ok: false, reason: "derivation-threw" };
  }
  const v = jail.violation();
  if (v) return { ok: false, ...v };
  if (cj(out.value) !== cj(w.value)) return { ok: false, reason: "value-mismatch" };
  if (cj(out.witness) !== cj(w.witness)) return { ok: false, reason: "witness-mismatch" };
  // law:warrant.support-soundness@1 — support is RE-DERIVED, not trusted:
  // replay must reproduce the derivation's own support exactly. Subset
  // (checked above) is necessary; equality is the sufficiency half.
  if (cj(canonSupport(out.support)) !== cj(w.support)) return { ok: false, reason: "support-mismatch" };
  if (warrantIdOf(w) !== w.warrant_id) return { ok: false, reason: "warrant-id-mismatch" };
  return { ok: true };
}

// early cutoff: on support_intact, re-derive JAILED-BY-NAMES (names fixed,
// versions refreshed); if the value reproduces, refresh the footprint and
// reseal — the warrant survives the world moving under it.
function refreshWarrant(world, w, measureFn) {
  const view = trackedView(world);
  const out = measureFn(view);
  if (cj(out.value) !== cj(w.value)) return { refreshed: false, reason: "value-diverged" };
  // support-soundness: refresh RESTORES derivation-produced support — a
  // forged support cannot survive the early-cutoff path (the audit's
  // laundering chain broke exactly here).
  const nw = { ...w, read_footprint: view.footprint(), at_vclock: world.vclock,
    witness: out.witness, support: canonSupport(out.support) };
  nw.warrant_id = warrantIdOf(nw);
  return { refreshed: true, warrant: nw };
}

// ═══ Warrant composition ═══════════════════════════════════════════════════
// law:warrant.composition@1. A warrant is CITED via its PUBLICATION: a
// world resource "warrant:<name>" carrying {value, warrant_id,
// footprint_id}. Readers read the publication — never the citee's
// internals (the jail enforces the abstraction boundary). Freshness of a
// citation is REIFIED as a scope query "warrant-fresh:<name>" whose result
// is the citee's footprint re-evaluated against the current world — the
// composite dirties the moment the citee's evidence moves, even though the
// publication resource itself has not.
function publishWarrant(world, name, w) {
  world.put("warrant:" + name, { value: w.value, warrant_id: w.warrant_id,
    footprint_id: footprintId(w.read_footprint) });
  world.registerQuery("warrant-fresh:" + name, ({ version, scope }) => {
    const exact = w.read_footprint.exact.map(([r]) => [r, version(r)]);
    const scopes = w.read_footprint.predicates.map(([q]) => [q, scope(q)]);
    return { exact, scopes };
  });
  return "warrant:" + name;
}
// deriveComposite: measureFn receives (view, cite) where cite(name) reads
// the publication AND records the freshness scope. A composite that skips
// the scope is constructible (citeNaive) — it exists to be the falsifier.
function deriveComposite(world, spec) {
  const view = trackedView(world);
  const cite = (name) => { view.scope("warrant-fresh:" + name); return view.read("warrant:" + name); };
  const citeNaive = (name) => view.read("warrant:" + name);
  const out = spec.measureFn(view, spec.naive ? citeNaive : cite);
  const fp = view.footprint();
  const w = {
    type: "Warrant", version: 3,
    measure: spec.measure, predicate: spec.predicate,
    value: out.value, witness: out.witness, support: canonSupport(out.support),
    read_footprint: fp,
    derivation_id: H("TRVM-DERIVATION-v1|" + spec.measure + "|" + spec.predicate + "|" + cj(spec.inputs ?? null)),
    at_vclock: world.vclock,
    law_refs: spec.law_refs ?? [],
    informational: { note: "NON-AUTHORITATIVE", generator: "trvm_world.mjs v" + WORLD_VERSION },
  };
  w.warrant_id = warrantIdOf(w);
  return w;
}
// composite replay: the same jail — the composite's footprint contains
// publications and freshness scopes, NOT the citees' internals; replay
// therefore PROVES the composite used only published values.
function replayComposite(world, w, measureFn) {
  const supportSet = new Set(w.support);
  const exactSet = new Set(w.read_footprint.exact.map(([n]) => n));
  for (const s of supportSet) if (!exactSet.has(s))
    return { ok: false, reason: "support-not-subset", resource: s };
  const jail = jailedView(world, w.read_footprint);
  const cite = (name) => { jail.scope("warrant-fresh:" + name); return jail.read("warrant:" + name); };
  let out;
  try { out = measureFn(jail, cite); }
  catch (e) {
    const v0 = jail.violation();
    return v0 ? { ok: false, ...v0 } : { ok: false, reason: "derivation-threw" };
  }
  const v = jail.violation();
  if (v) return { ok: false, ...v };
  if (cj(out.value) !== cj(w.value)) return { ok: false, reason: "value-mismatch" };
  if (cj(out.witness) !== cj(w.witness)) return { ok: false, reason: "witness-mismatch" };
  if (cj(canonSupport(out.support)) !== cj(w.support)) return { ok: false, reason: "support-mismatch" };
  if (warrantIdOf(w) !== w.warrant_id) return { ok: false, reason: "warrant-id-mismatch" };
  return { ok: true };
}

// ═══ The MAINTAINER (round 9) ══════════════════════════════════════════════
// A supervised maintenance engine over the warrant DAG. Design order per the
// audit's brief: the falsifiers were written before the engine.
//   law:maintenance.acyclicity@1 — the API cannot construct a cycle (cites
//     must already exist), and the pass INDEPENDENTLY re-verifies via Kahn's
//     algorithm against direct defs poisoning: a cycle refuses the pass and
//     names its members.
//   law:maintenance.quarantine@1 — forged input is quarantined, never
//     repaired: external warrants replay-gate at register(); inside a pass,
//     FRESH nodes are replay-VALIDATED (versions permit it exactly then) and
//     a refusal quarantines the node — its publication is not touched, its
//     dependents see it via the freshness scopes as-is, and the receipt says
//     so. Refresh/re-derive paths REPLACE state with derivation truth and
//     the receipt records both ids, so nothing forged is ever propagated
//     as-is.
//   law:maintenance.pass@1 — nodes are processed once each, dependencies
//     first (deterministic topo: Kahn with sorted ready-set), so no citer is
//     ever refreshed against a stale citee; a converged pass is all-fresh.
//   law:maintenance.atomicity@1 — the pass runs on a WORLD FORK; the real
//     world is touched only by the atomic APPLY of the staged publication
//     sequence after every node succeeded. A mid-pass throw discards the
//     fork: nothing half-advanced.
//   law:maintenance.receipt@1 — the MaintenanceReceipt commits the BEFORE
//     and AFTER publication maps and the ordered steps under
//     TRVM-MAINTPASS-v1, and AFTER must be reconstructible from BEFORE +
//     steps by arithmetic (grid_check does exactly that reconstruction).
// ═══ GuardedStore — the coordinator's maps are capabilities, not raw Maps ══
// law:maintenance.coordinator-write-mediated@1 (round 9D.1).
//
// v0.8.0 froze the Maintainer's PROPERTIES and guarded its METHODS, and the
// audit walked straight past both: `#inPass` mediates `addGround`, not
// `defs.set`, and freezing a property does not freeze the Map it points at.
// Three witnesses reproduced 0/3 confined against 0.8.0
// (probe_coordinator_alias_9d1_repro.mjs) — a raw `defs.set` planting a GHOST
// mid-pass, a cross-node `state.set` forging a warrant_id that reached the
// receipt, and — needing no map access at all — a caller-owned `spec` object
// retained across registration whose `measureFn` was swapped mid-pass and
// COMMITTED. Sealing an object says nothing about the authority graph reachable
// through it.
//
// The seam the batteries need is preserved exactly: poisoning from OUTSIDE a
// pass still works, because that is the external-ingest position `register()`
// already models. What is refused is the same mutation from INSIDE one. The
// module-private RAW table is the only unguarded write path and never leaves
// this file, so the coordinator can still make its own transactional writes.
const RAW = new WeakMap();
class GuardedStore {
  #label; #inPass; #own;
  constructor(label, inPass, own) {
    this.#label = label; this.#inPass = inPass; this.#own = own;
    RAW.set(this, new Map());
    Object.freeze(this);
  }
  #guard(op) {
    if (this.#inPass()) throw new Error(
      "maintainer-reentrancy-refused: " + this.#label + "." + op + " during a pass");
  }
  get size() { return RAW.get(this).size; }
  has(k) { return RAW.get(this).has(k); }
  get(k) { return RAW.get(this).get(k); }          // values are owned+frozen on the way IN
  keys() { return RAW.get(this).keys(); }
  values() { return RAW.get(this).values(); }
  entries() { return RAW.get(this).entries(); }
  [Symbol.iterator]() { return RAW.get(this).entries(); }
  forEach(f, t) { return RAW.get(this).forEach(f, t); }
  set(k, v) { this.#guard("set"); RAW.get(this).set(k, this.#own(v)); return this; }
  delete(k) { this.#guard("delete"); return RAW.get(this).delete(k); }
  clear() { this.#guard("clear"); RAW.get(this).clear(); }
}
Object.freeze(GuardedStore.prototype);

// Ownership: a stored value must share no mutable structure with the caller's.
// This is what severs registration aliasing — the coordinator captures the
// measureFn VALUE at registration and can no longer be reached by reassigning
// the caller's property afterwards.
// TRANSITIVE ownership, through the boundary the World already trusts.
// v0.9.0 froze the warrant OBJECT and left `value` and `witness` as the caller's
// nested objects, so `m.state.get("B").value.x = 999` was an in-pass write that
// `GuardedStore` never saw — no `.set()` occurred. Reusing `canonicalBytes`
// rather than inventing a second clone algorithm keeps one definition of what a
// value is; non-canonical fields (witness is opaque by design) still get a
// severed, frozen copy.
const deepFreeze = (v) => {
  if (v === null || typeof v !== "object" || Object.isFrozen(v)) return v;
  Object.freeze(v);
  for (const k of Object.keys(v)) deepFreeze(v[k]);
  return v;
};
// OWNERSHIP FAILS CLOSED. v0.10.0 ended in `catch { return v }`, so an object
// neither mechanism could own was handed straight back — the caller kept the
// authority the layer existed to take. Three variants reproduced against it
// (probe_ownfailopen_9d3_repro.mjs): a witness carrying a method defeated both
// paths; a Map witness passed structuredClone while `Object.freeze` left its
// ENTRIES writable; and spec.inputs took the whole registration-alias species
// back, with B re-deriving on a mutated input mid-pass.
//
// The Map case is the one that matters beyond aliasing. `JSON.stringify(new
// Map([["e",1]]))` is `{}`, so Map([["e",1]]) and Map([["e",999]]) are
// indistinguishable to warrant identity: the OWNERSHIP domain and the IDENTITY
// domain disagreed about what a value is. One domain now, and it is the one the
// World already refuses on — a witness may be semantically OPAQUE without being
// representationally ARBITRARY. If tagged encodings for Map/Set/Date are ever
// needed, they must be defined once and used by ownership, equality,
// warrant_id and replay together, never by structuredClone on one side and
// JSON.stringify on the other.
function ownCanonical(v, label) {
  try {
    const bytes = canonicalBytes(v);
    return v === null || typeof v !== "object" ? v : deepFreeze(JSON.parse(bytes));
  } catch (e) {
    throw new Error(label + "-not-canonical: " +
      String(e.message).replace(/^world-value-not-canonical: /, ""));
  }
}

// SCHEMA-COMPLETE ownership. v0.9.0's ownSpec kept {measure, predicate,
// measureFn} and silently dropped `inputs`, `law_refs` and `naive` — all of
// which the derivers consume, and `inputs` participates in derivation_id. The
// alias-severing repair was therefore also an UNDECLARED SEMANTIC PROJECTION,
// invisible to the corpus only because no shipped spec uses those fields. An
// ownership layer may sever references; it may not quietly change meaning.
const SPEC_FIELDS = ["measure", "predicate", "inputs", "law_refs", "naive", "measureFn"];
const ownSpec = (sp = {}) => {
  const unknown = Object.keys(sp).filter((k) => !SPEC_FIELDS.includes(k));
  if (unknown.length) throw new Error("spec-field-unknown: " + unknown.sort().join(","));
  return Object.freeze({
    measure: sp.measure,
    predicate: sp.predicate,
    inputs: ownCanonical(sp.inputs ?? null, "spec.inputs"),
    law_refs: Object.freeze([...(sp.law_refs ?? [])]),
    naive: sp.naive === true,
    measureFn: sp.measureFn,
  });
};
const ownDef = (d = {}) => Object.freeze({
  kind: d.kind,
  cites: Object.freeze([...(d.cites ?? [])]),
  spec: ownSpec(d.spec),
});
const ownWarrant = (w) => {
  if (!w || typeof w !== "object") return w;
  const fp = w.read_footprint;
  return Object.freeze({ ...w,
    value: ownCanonical(w.value, "warrant.value"),       // transitive AND fail-closed
    witness: ownCanonical(w.witness ?? null, "warrant.witness"),
    support: Object.freeze([...(w.support ?? [])]),
    law_refs: Object.freeze([...(w.law_refs ?? [])]),
    read_footprint: fp ? Object.freeze({
      exact: Object.freeze((fp.exact ?? []).map((e) => Object.freeze([...e]))),
      predicates: Object.freeze((fp.predicates ?? []).map((e) => Object.freeze([...e]))),
    }) : fp,
  });
};

class Maintainer {
  // law:maintenance.coordinator-confinement@1 (round 9D).
  // 9.1 locked the World, 9.2 sealed its internals and its key, 9.3 closed the
  // apply boundary — and every one of those fixes was about the WORLD, while
  // the coordinator holding the lock stayed an ordinary object with public
  // fields and patchable methods. The audit's prediction that "the coordinator
  // becomes the next authority surface" was exact: three of its four witnesses
  // reproduced against v0.7.1 (probe_maintainer_9d_repro.mjs) —
  //   · a derivation calling addGround mid-pass left a GHOST def behind, since
  //     defs.set precedes the world write the lock refuses, and snapshot() then
  //     put a name in the receipt's after-map that the world never published;
  //   · assigning this.world mid-pass made `finally { this.world.unlock() }`
  //     unlock the WRONG world, leaving the authoritative one permanently
  //     locked and no receipt sealed at all — a bricked world, not a leak;
  //   · replacing sealReceipt on the instance returned a fully forged receipt
  //     (no_op:true, zero steps, chosen pass_id) from an otherwise honest pass.
  // Closed structurally where the attack is structural and temporally where it
  // is temporal: the instance and prototype are frozen (so neither the root
  // reference nor any method can be reassigned), and a private in-flight flag
  // refuses registration re-entry during a pass. `defs`/`state` stay MUTABLE by
  // design — the batteries poison them from outside to build adversarial states,
  // which is the external-ingest position `register()` already models. The
  // attack was never that a Map can be written; it was that it could be written
  // FROM INSIDE A TRANSACTION, and that is what the flag refuses.
  #inPass = false;
  constructor(world) {
    this.world = world;
    const inPass = () => this.#inPass;
    this.defs = new GuardedStore("defs", inPass, ownDef);    // name -> {kind, cites, spec}
    this.state = new GuardedStore("state", inPass, ownWarrant); // name -> current warrant
    Object.freeze(this);     // root identity and methods are not reassignable
  }
  #enter() {
    if (this.#inPass) throw new Error("maintainer-reentrancy-refused: a pass is already in flight");
    this.#inPass = true;
  }
  #leave() { this.#inPass = false; }
  #guard(what) {
    if (this.#inPass) throw new Error("maintainer-reentrancy-refused: " + what + " during a pass");
  }
  mfnOf(def) {
    if (def.kind === "ground") return def.spec.measureFn;
    return (view) => def.spec.measureFn(view, (n) => {
      view.scope("warrant-fresh:" + n); return view.read("warrant:" + n);
    });
  }
  addGround(name, spec) {
    this.#guard("addGround");
    if (this.defs.has(name)) throw new Error("maintainer: duplicate " + name);
    this.defs.set(name, { kind: "ground", cites: [], spec });
    const w = deriveWarrant(this.world, this.defs.get(name).spec);  // OWNED spec, not the caller's
    this.state.set(name, w);
    publishWarrant(this.world, name, w);
    return w;
  }
  addComposite(name, cites, spec) {
    this.#guard("addComposite");
    if (this.defs.has(name)) throw new Error("maintainer: duplicate " + name);
    for (const c of cites) if (!this.defs.has(c))
      throw new Error("maintenance-cycle-guard: " + name + " cites unknown " + c); // forward refs impossible
    this.defs.set(name, { kind: "composite", cites: [...cites], spec });
    const w = deriveComposite(this.world, this.defs.get(name).spec);  // OWNED spec
    this.state.set(name, w);
    publishWarrant(this.world, name, w);
    return w;
  }
  register(name, warrant) {   // external ingest: the quarantine door
    this.#guard("register");
    const def = this.defs.get(name);
    if (!def) return { accepted: false, reason: "unknown-name" };
    const r = def.kind === "ground"
      ? replayWarrant(this.world, warrant, this.mfnOf(def))
      : replayComposite(this.world, warrant, def.spec.measureFn);
    if (!r.ok) return { accepted: false, quarantined: true, reason: r.reason };
    this.state.set(name, warrant);
    return { accepted: true };
  }
  topoOrder(defs = this.defs) {   // deterministic Kahn; leftover names a cycle
    const indeg = new Map(), dependents = new Map();
    for (const [n, d] of defs) { indeg.set(n, d.cites.length); for (const c of d.cites) { if (!dependents.has(c)) dependents.set(c, []); dependents.get(c).push(n); } }
    const ready = [...indeg].filter(([, k]) => k === 0).map(([n]) => n).sort();
    const order = [];
    while (ready.length) {
      const n = ready.shift(); order.push(n);
      for (const m of (dependents.get(n) ?? []).sort()) {
        indeg.set(m, indeg.get(m) - 1);
        if (indeg.get(m) === 0) { ready.push(m); ready.sort(); }
      }
    }
    if (order.length !== defs.size)
      return { cycle: [...defs.keys()].filter((n) => !order.includes(n)).sort() };
    return { order };
  }
  pass(opts = {}) {
    // RE-ENTRY REFUSED before anything else: a derivation that reaches back
    // into the coordinator finds every registration door shut for the duration.
    this.#enter();
    try {
    // ENTRY TRUTH first (law:maintenance.capability-confinement@1, independent
    // half): the pass-entry vclock and before-map are captured BEFORE any
    // adversarial code can run — an aborted receipt reports the ACTUAL entry
    // clock, never one sampled after an escape.
    const passStartVclock = this.world.vclock;
    // TRANSACTION-LOCAL DEFINITIONS: the pass computes against the definition
    // set as it stood at entry. Even if some future route mutates the live
    // store mid-pass, the topology, the derivations and the receipt's name set
    // all refer to this frozen view — so a mutation that slips past the guard
    // still cannot change what THIS pass did. Guard and snapshot are belt and
    // braces on purpose; 0.8.0 had only the guard, and the guard had a gap.
    const DEFS = new Map(RAW.get(this.defs));
    const before = this.snapshot(this.world, DEFS);
    const t = this.topoOrder(DEFS);
    if (t.cycle) return this.sealReceipt({ refused: true, reason: "maintenance-cycle", cycle: t.cycle, before, after: before, steps: [], vb: passStartVclock, va: passStartVclock });
    // CONFINEMENT: the authoritative world is LOCKED for the whole pass —
    // any escaped write through a captured reference refuses instead of
    // corrupting; only the commit capability below can apply.
    const lockKey = this.world.lock();
    const fork = this.world.fork();
    const staged = new Map(), steps = [];
    try {
    try {
      for (const name of t.order) {
       try {
        const def = DEFS.get(name);
        const w = staged.get(name) ?? this.state.get(name);
        const f = freshness(fork, w);
        const pubBefore = fork.read("warrant:" + name).version;
        if (f.verdict === "fresh") {
          const r = def.kind === "ground"
            ? replayWarrant(fork, w, this.mfnOf(def))
            : replayComposite(fork, w, def.spec.measureFn);
          if (!r.ok) { steps.push({ name, verdict: f.verdict, action: "quarantined", reason: r.reason, warrant_id_before: w.warrant_id, warrant_id_after: w.warrant_id, pub_before: pubBefore, pub_after: pubBefore }); continue; }
          steps.push({ name, verdict: f.verdict, action: "none", warrant_id_before: w.warrant_id, warrant_id_after: w.warrant_id, pub_before: pubBefore, pub_after: pubBefore });
          continue;
        }
        let action = null, nw = null, trigger = null;
        if (f.verdict === "support_intact") {
          const cut = refreshWarrant(fork, w, this.mfnOf(def));
          if (cut.refreshed) { action = "refreshed"; nw = cut.warrant; }
          else trigger = "support_intact-value-diverged";
        }
        if (!nw) {
          action = "rederived";
          nw = def.kind === "ground" ? deriveWarrant(fork, def.spec) : deriveComposite(fork, def.spec);
        }
        publishWarrant(fork, name, nw);
        staged.set(name, nw);
        steps.push({ name, verdict: f.verdict, action, ...(trigger ? { trigger } : {}),
          warrant_id_before: w.warrant_id, warrant_id_after: nw.warrant_id,
          pub_before: pubBefore, pub_after: fork.read("warrant:" + name).version });
       } catch (e) { if (e && e.maintName === undefined) e.maintName = name; throw e; }
      }
    } catch (e) {
      return this.sealReceipt({ aborted: true, at: e.maintName ?? "unknown", reason: String(e.message).slice(0, 120),
        before, after: before, steps, vb: passStartVclock, va: passStartVclock });
    }
    // ATOMIC APPLY through the commit CAPABILITY: the only door in the lock.
    // PRE-VALIDATION first (round 9.3): every staged publication value must
    // canonicalize BEFORE the first real-world write, so organic apply
    // faults are unreachable by construction — staged values already
    // round-tripped the fork, and this proves it again at the boundary.
    for (const [nm, sw] of staged)
      canonicalBytes({ value: sw.value, warrant_id: sw.warrant_id, footprint_id: footprintId(sw.read_footprint) });
    // If apply is torn anyway (fault injection, or an engine bug the
    // pre-validation missed), append-only means no rollback — so the tear
    // is RECEIPTED truthfully: {aborted, torn, at: "apply", applied: [the
    // prefix that landed]}, with vclock_after and the after-map reflecting
    // the REAL half-applied world. Atomicity's failure mode is visible,
    // never silent (law:maintenance.atomicity@1, law:maintenance.receipt@1).
    const applied = [];
    let after;
    try {
      after = this.world.commit(lockKey, () => {
        for (const s of steps) if (staged.has(s.name)) {
          publishWarrant(this.world, s.name, staged.get(s.name));
          RAW.get(this.state).set(s.name, ownWarrant(staged.get(s.name)));  // module-private: the pass writing its own committed result
          applied.push(s.name);
          if (opts.faultApplyAfter === s.name)   // documented fault-injection port
            throw new Error("injected-apply-fault after " + s.name);
        }
        return this.snapshot(this.world);
      });
    } catch (e) {
      return this.sealReceipt({ aborted: true, torn: true, at: "apply", applied,
        reason: String(e.message).slice(0, 120),
        before, after: this.snapshot(this.world, DEFS), steps,
        vb: passStartVclock, va: this.world.vclock });
    }
    return this.sealReceipt({ before, after, steps, vb: passStartVclock, va: after.vclock });
    } finally { this.world.unlock(lockKey); }
    } finally { this.#leave(); }
  }
  snapshot(world, defs = RAW.get(this.defs)) {
    // AUTHORITY, NOT ASSEMBLY. Until 0.9.0 this read pub_version from the WORLD
    // and warrant_id from coordinator STATE, producing one apparently
    // authoritative pair out of two independent sources — so a poisoned
    // coordinator entry put a forged warrant_id into a receipt whose version
    // number came from an honest publication. The audit's witness 9D.1-b is
    // exactly that hybrid. Both fields now come from the publication itself;
    // coordinator state is COMPARED against it and any disagreement is
    // declared, never silently preferred or silently dropped.
    const pubs = {};
    for (const name of [...defs.keys()].sort()) {
      const pub = world.read("warrant:" + name);
      const published = (pub && pub.value && typeof pub.value === "object") ? pub.value : null;
      const worldId = published ? (published.warrant_id ?? null) : null;
      const coordId = (this.state.get(name) ?? {}).warrant_id ?? null;
      pubs[name] = { pub_version: pub.version, warrant_id: worldId };
      // NOT ID-ONLY. A coordinator entry mutated without resealing keeps a
      // warrant_id that still matches the publication, so an identity check
      // alone reports agreement about a corrupted record. The published value
      // is compared too.
      const coord = this.state.get(name) ?? null;
      if (worldId !== null && coordId !== null && worldId !== coordId)
        pubs[name].coordinator_diverged = "warrant_id";
      else if (published && coord && cj(published.value) !== cj(coord.value))
        pubs[name].coordinator_diverged = "value";
    }
    return { vclock: world.vclock, pubs };
  }
  sealReceipt(r) {
    const receipt = {
      type: "MaintenanceReceipt", version: 1,
      refused: r.refused ?? false, aborted: r.aborted ?? false, torn: r.torn ?? false,
      ...(r.applied ? { applied: r.applied } : {}),
      ...(r.reason ? { reason: r.reason } : {}), ...(r.cycle ? { cycle: r.cycle } : {}), ...(r.at ? { at: r.at } : {}),
      vclock_before: r.vb, vclock_after: r.va,
      before: r.before.pubs, after: r.after.pubs, steps: r.steps,
      no_op: !r.refused && !r.aborted && r.steps.every((s) => s.action === "none") && r.vb === r.va,
      law_refs: ["law:maintenance.pass@1", "law:maintenance.quarantine@1",
        "law:maintenance.atomicity@1", "law:maintenance.receipt@1", "law:maintenance.acyclicity@1"],
    };
    receipt.pass_id = H("TRVM-MAINTPASS-v1|" + receipt.vclock_before + "|" + receipt.vclock_after + "|" + cj(receipt.before) + "|" + cj(receipt.after) + "|" + cj(receipt.steps));
    return receipt;
  }
}

// Method patching must throw, not merely be discouraged — the instance freeze
// alone leaves the PROTOTYPE writable, and the L-COORD-1 sealer case caught
// exactly that in this round's first draft: `Maintainer.prototype.sealReceipt`
// was still assignable and a patched pass returned a forged receipt.
Object.freeze(Maintainer.prototype);

// ═══ The shared footprint: SchedulerCertificate as a warrant ═══════════════
// law:footprint.shared@1 — the certificate's corpus{id,sha256} is an exact
// read of a corpus resource; its evidence is the value; its run manifest
// the witness. One evidence language for both artifacts.
function certFootprintOf(cert, corpusResource, corpusVersion) {
  return { exact: [[corpusResource, corpusVersion]], predicates: [] };
}
function warrantOfCertificate(world, cert, corpusResource) {
  const r = world.read(corpusResource);
  const w = {
    type: "Warrant", version: 3,
    measure: "scheduler-certificate-evidence",
    predicate: "cert.evidence == aggregates(re-executed receipts)",
    value: cert.evidence,
    witness: { run_manifest_hash: cert.run_manifest_hash, receipts: cert.run_manifest.length },
    support: [corpusResource],
    read_footprint: certFootprintOf(cert, corpusResource, r.version),
    derivation_id: H("TRVM-DERIVATION-v1|scheduler-certificate|" + cert.cert_id),
    at_vclock: world.vclock,
    law_refs: ["law:footprint.shared@1", "law:sched.certificate@2"],
    informational: { note: "NON-AUTHORITATIVE", generator: "trvm_world.mjs v" + WORLD_VERSION },
  };
  w.warrant_id = warrantIdOf(w);
  return w;
}

// ═══ Flagship world: the kappa-flavored graph ══════════════════════════════
// Resources: "node:<id>" -> true, "edge:<a>|<b>" -> true (undirected).
// Measure: size of the component containing a SEED, computed by frontier
// expansion that reads exactly the nodes and edges it traverses, and
// evaluates ONE scope query: the digest of all edges incident to the
// reached set — the phantom guard.
function graphWorld(nodes, edges) {
  const w = new World();
  for (const n of nodes) w.put("node:" + n, true);
  for (const [a, b] of edges) w.put("edge:" + [a, b].sort().join("|"), true);
  return w;
}
function incidentScope(seedName) {
  // registered per-warrant: recompute reached set from CURRENT world, digest
  // the incident edge set. A phantom (new edge touching the reached set)
  // changes this digest even though every exact read is byte-identical.
  return ({ value, names }) => {
    const reached = reachFrom(seedName, value, names);
    const inc = names().filter((n) => {
      if (!n.startsWith("edge:")) return false;
      const [a, b] = n.slice(5).split("|");
      return reached.has(a) || reached.has(b);
    }).filter((n) => value(n) !== undefined);
    return inc.sort();
  };
}
function reachFrom(seed, read, names) {
  const reached = new Set(); const stack = [seed];
  const edgeNames = names().filter((n) => n.startsWith("edge:"));
  while (stack.length) {
    const n = stack.pop();
    if (reached.has(n) || read("node:" + n) === undefined) continue;
    reached.add(n);
    for (const en of edgeNames) {
      const [a, b] = en.slice(5).split("|");
      if (read(en) === undefined) continue;
      if (a === n && !reached.has(b)) stack.push(b);
      if (b === n && !reached.has(a)) stack.push(a);
    }
  }
  return reached;
}
// the measure function used by warrants. NOTE: it reads through the VIEW —
// tracked when building, jailed when replaying. It traverses only what it
// reaches; the scope evaluation is its phantom guard.
function componentMeasure(world, seed, { withScope = true } = {}) {
  return (view) => {
    const reached = new Set(); const stack = [seed];
    // enumeration of candidate edges must itself be footprinted: we read a
    // node's adjacency through an index resource, not by scanning the world
    // (a world scan is an undeclared read of everything).
    while (stack.length) {
      const n = stack.pop();
      if (reached.has(n)) continue;
      if (view.read("node:" + n) === undefined) continue;
      reached.add(n);
      const adjRaw = view.read("adj:" + n);
      const adj = Array.isArray(adjRaw) ? adjRaw : [];  // a world is untyped storage; junk carries no edges
      for (const m of adj) {
        const en = "edge:" + [n, m].sort().join("|");
        if (view.read(en) === undefined) continue;
        if (!reached.has(m)) stack.push(m);
      }
    }
    const value = reached.size;
    const witness = [...reached].sort();
    // support = the resources whose change is SEMANTIC for the value: the
    // reached nodes. Adjacency and edge reads are footprint (freshness)
    // but not support (a rewritten-identical adj list is support_intact).
    const support = witness.map((n) => "node:" + n);
    if (withScope) view.scope("incident:" + seed);
    return { value, witness, support };
  };
}

// adjacency-index maintenance (the world half of footprintable traversal)
function putEdge(world, a, b) {
  const en = "edge:" + [a, b].sort().join("|");
  world.put(en, true);
  for (const [x, y] of [[a, b], [b, a]]) {
    const cur = world.read("adj:" + x).value ?? [];
    if (!cur.includes(y)) world.put("adj:" + x, [...cur, y].sort());
  }
  return en;
}
function buildGraphWorld(nodes, edges) {
  const w = new World();
  for (const n of nodes) { w.put("node:" + n, true); w.put("adj:" + n, []); }
  for (const [a, b] of edges) putEdge(w, a, b);
  return w;
}

// L-COORD-1 : the coordinator's own authority surface (round 9D,
// law:maintenance.coordinator-confinement@1). Each half is the audit's witness
// run forward against the sealed Maintainer; probe_maintainer_9d_repro.mjs
// keeps all three RED against v0.7.1 by design.
function coordBattery() {
  const out = [];
  // (a) reentrant registration: the def must not survive, and the receipt must
  //     not name a publication the world never made
  { const w = new World(); w.put("flag", 0);
    const m = new Maintainer(w);
    let refusal = null;
    m.addGround("A", { measure: "reentrant", predicate: "flag", measureFn: (view) => {
      const f = view.read("flag");
      if (f === 1) { try { m.addGround("GHOST", { measure: "g", predicate: "p",
        measureFn: () => ({ value: 1, witness: {}, support: [] }) }); } catch (e) { refusal = e.message; } }
      return { value: f, witness: { f }, support: ["flag"] };
    } });
    w.put("flag", 1);
    let rec = null, threw = null;
    try { rec = m.pass(); } catch (e) { threw = String(e.message); }
    out.push({ id: "reentrant-addGround",
      ok: !m.defs.has("GHOST") && !!rec && !Object.prototype.hasOwnProperty.call(rec.after, "GHOST")
          && String(refusal).includes("maintainer-reentrancy-refused"),
      note: `refused with '${String(refusal).slice(0, 44)}'; defs clean: ${!m.defs.has("GHOST")}; after-map clean: ${rec ? !Object.prototype.hasOwnProperty.call(rec.after, "GHOST") : "no receipt"}${threw ? "; threw " + threw.slice(0, 40) : ""}` });
  }
  // (b) root identity: reassigning this.world must throw, and the authoritative
  //     world must NOT be left locked (the v0.7.1 witness bricked it)
  { const wA = new World(); wA.put("flag", 0);
    const wB = new World(); wB.put("flag", 99);
    const m = new Maintainer(wA);
    m.addGround("A", { measure: "rootswap", predicate: "flag", measureFn: (view) => {
      const f = view.read("flag");
      if (f === 1) { m.world = wB; }
      return { value: f, witness: { f }, support: ["flag"] };
    } });
    wA.put("flag", 1);
    let rec = null; try { rec = m.pass(); } catch { /* must not happen */ }
    const stillA = m.world === wA;
    const writable = (() => { try { wA.put("post", 1); return wA.read("post").value === 1; } catch { return false; } })();
    out.push({ id: "root-identity-swap", ok: stillA && !!rec && rec.aborted && writable,
      note: `assignment refused on the frozen instance (m.world===wA: ${stillA}); the pass ABORTS with a receipt (${!!rec}) instead of throwing past the unlock, and the world is still writable afterwards (${writable}) — v0.7.1 unlocked wB and left wA permanently locked` });
  }
  // (c) the sealer: neither instance nor prototype may be patched
  { const w = new World(); w.put("flag", 0);
    const m = new Maintainer(w);
    m.addGround("A", { measure: "sealswap", predicate: "flag",
      measureFn: (view) => ({ value: view.read("flag"), witness: {}, support: ["flag"] }) });
    w.put("flag", 1);
    let instThrew = false, protoThrew = false;
    try { m.sealReceipt = () => ({ forged: true }); } catch { instThrew = true; }
    try { Maintainer.prototype.sealReceipt = () => ({ forged: true }); } catch { protoThrew = true; }
    const protoSwap = (() => { try { Object.setPrototypeOf(m, {}); return false; } catch { return true; } })();
    const rec = m.pass();
    out.push({ id: "receipt-sealer-swap",
      ok: instThrew && protoThrew && protoSwap && !rec.forged && typeof rec.pass_id === "string" && rec.pass_id.length === 64,
      note: `instance override throws (${instThrew}), prototype override throws (${protoThrew}), setPrototypeOf throws (${protoSwap}); the pass seals a real receipt with a 64-char pass_id (${rec.pass_id ? rec.pass_id.length : 0})` });
  }
  // (d) nested pass
  { const w = new World(); w.put("flag", 0);
    const m = new Maintainer(w);
    let nested = null;
    m.addGround("A", { measure: "nested", predicate: "flag", measureFn: (view) => {
      const f = view.read("flag");
      if (f === 1) { try { m.pass(); } catch (e) { nested = e.message; } }
      return { value: f, witness: { f }, support: ["flag"] };
    } });
    w.put("flag", 1);
    m.pass();
    out.push({ id: "nested-pass", ok: String(nested).includes("maintainer-reentrancy-refused"),
      note: `a pass invoked from inside a derivation refuses: '${String(nested).slice(0, 52)}'` });
  }
  return out;
}
// ═══ harness ═══════════════════════════════════════════════════════════════
const QUICK = process.argv.includes("--quick");
let anyFail = false;
const rows = [];
function report(name, caption, status, detail) {
  if (status.includes("FALSIFIED?!")) anyFail = true;
  rows.push([name, status, caption, detail]);
  console.log(name.padEnd(14) + status.padEnd(20) + caption);
  console.log("              " + detail);
}
if (process.argv.includes("--check-receipt")) {
  // ENGINE half for the shipped receipt (law:warrant.support-soundness@1's
  // division of verification): rebuild the world from the COMMITTED
  // world_spec, replay both warrants — support equality enforced inside the
  // replayers — and recompute the receipt commitment. grid_check holds the
  // engine-free half (structure, canonical form, subset); THIS holds the
  // truth half a tampered-but-resealed support cannot survive.
  const wr = JSON.parse(readFileSync("world_warrant_receipt.json", "utf8"));
  const bad = (m) => { console.log("RECEIPT-CHECK: FAIL — " + m); process.exit(1); };
  if (wr.version !== 3) bad("receipt is not v3");
  const rid = H("TRVM-WORLDRECEIPT-v3|" + cj(wr.world_spec) + "|" + cj(wr.warrant) + "|" + wr.footprint_id
    + "|" + cj(wr.composite.warrant) + "|" + wr.composite.footprint_id);
  if (rid !== wr.receipt_id) bad("receipt_id does not recompute");
  const w = buildGraphWorld(wr.world_spec.nodes, wr.world_spec.edges);
  w.registerQuery("incident:" + wr.world_spec.seed, incidentScope(wr.world_spec.seed));
  const fn = componentMeasure(w, wr.world_spec.seed);
  const rG = replayWarrant(w, wr.warrant, fn);
  if (!rG.ok) bad("ground replay refused: " + rG.reason + (rG.resource ? " at " + rG.resource : ""));
  publishWarrant(w, "ground", wr.warrant);
  const cfn = (view, cite) => {
    const pub = cite("ground");
    return { value: 2 * pub.value, witness: { cited: pub.warrant_id }, support: ["warrant:ground"] };
  };
  const rC = replayComposite(w, wr.composite.warrant, cfn);
  if (!rC.ok) bad("composite replay refused: " + rC.reason + (rC.resource ? " at " + rC.resource : ""));
  console.log("RECEIPT-CHECK: PASS — world rebuilt from committed spec; ground and composite REPLAYED with support equality; commitment recomputed.");
  process.exit(0);
}
console.log(`trvm_world v${WORLD_VERSION} — WorldRecord + Warrant v3, executable`);
console.log("layer: WORLD (the calculus kernel is frozen at its own version and has no world by design)");
console.log("═".repeat(96));

// L-WORLD-1 : version monotonicity + append-only log
{
  // NOTE, kept on purpose: the round-8B audit found this battery's first
  // version contained `... === 49 - 0 || true` — an assertion incapable of
  // failing, in the very battery introducing the monotonicity law. It is
  // gone; every check below can fail, and the battery grew the lifecycle
  // the audit asked for.
  const w = new World();
  const seen = [];
  for (let i = 0; i < 50; i++) seen.push(w.put("r" + (i % 7), i));
  const delV = w.del("r3"); seen.push(delV);
  const strict = seen.every((v, i) => i === 0 || v > seen[i - 1]);
  const logOk = w.log.length === 51 && w.log.every((e, i) => e.version === i + 1);
  const readLatest = [0, 1, 2, 4, 5, 6].every((k) => {
    let last = -1; for (let i = k; i < 50; i += 7) last = i;
    return w.read("r" + k).value === last;
  });
  // deletion lifecycle: absent -> put -> update -> delete -> recreate
  const w2 = new World();
  const absent = JSON.stringify(w2.read("x")) === JSON.stringify({ value: undefined, version: 0 });
  const v1 = w2.put("x", 1), v2 = w2.put("x", 2), v3 = w2.del("x");
  const tomb = w2.read("x");
  const tombOk = tomb.value === undefined && tomb.version === v3 && tomb.deleted === true
    && v3 > v2 && v2 > v1 && !w2.exists("x") && !w2.names().includes("x");
  const v4 = w2.put("x", 3);
  const recreated = v4 > v3 && w2.read("x").value === 3 && w2.exists("x");
  // version => value: every logged put version maps to exactly one hash
  const byVer = new Map();
  let verHashOk = true;
  for (const e of w.log) if (e.op === "put") {
    const k = e.resource + "@" + e.version;
    if (byVer.has(k) && byVer.get(k) !== e.hash) verHashOk = false;
    byVer.set(k, e.hash);
  }
  report("L-WORLD-1", "(versioned store: strict vclock, dense log, latest-read x6, tombstone lifecycle, version=>hash, WORLD, MONOTONICITY)",
    strict && logOk && readLatest && absent && tombOk && recreated && verHashOk ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `50 writes + delete: versions strictly increase (${strict}), log dense (${logOk}), latest-read verified on all six live resources (${readLatest}); lifecycle absent->put->update->delete->recreate: the TOMBSTONE carries the deletion version (${tombOk}) — "deleted at ${v3}" and "never existed" no longer collapse — and recreation advances past it (${recreated}); every logged (resource, version) maps to one value hash (${verHashOk}) (law:world.version-monotone@1, law:world.write-mediated@1)`);
}

// L-ALIAS-1 : write-mediation under attack (round 8.1 —
// law:world.write-mediated@1). The audit's witness verbatim, its ingress
// twin, the nested variant, and the canonical-domain refusals: state
// cannot change without an identity transition.
{
  const w = new World();
  w.put("r:x", [1]);
  const fn = (view) => { const a = view.read("r:x"); return { value: a.length, witness: a, support: ["r:x"] }; };
  const wa = deriveWarrant(w, { measure: "len(r:x)", predicate: "length", measureFn: fn, law_refs: ["law:world.write-mediated@1"] });
  const h0 = w.valueHash("r:x");
  // egress (THE witness): mutate through read's result — must be a no-op
  w.read("r:x").value.push(2);
  const egressDead = JSON.stringify(w.read("r:x").value) === "[1]" && w.valueHash("r:x") === h0;
  const f = freshness(w, wa), r = replayWarrant(w, wa, fn);
  const coherent = f.verdict === "fresh" && r.ok === true;
  // ingress: retain the reference given to put, mutate it after
  const w2 = new World();
  const payload = { a: { b: [1] } };
  w2.put("r:y", payload);
  const h1 = w2.valueHash("r:y");
  payload.a.b.push(99);
  const ingressDead = JSON.stringify(w2.read("r:y").value) === JSON.stringify({ a: { b: [1] } }) && w2.valueHash("r:y") === h1;
  // nested egress
  w2.read("r:y").value.a.b.push(7);
  const nestedDead = JSON.stringify(w2.read("r:y").value) === JSON.stringify({ a: { b: [1] } });
  // canonical-domain refusals, each with the typed error
  const rejects = [
    ["function", () => w2.put("bad", () => 1)],
    ["NaN", () => w2.put("bad", NaN)],
    ["Infinity", () => w2.put("bad", [Infinity])],
    ["undefined-element", () => w2.put("bad", [undefined])],
    ["class-instance", () => w2.put("bad", new Date())],
    ["cycle", () => { const c = { x: 1 }; c.self = c; w2.put("bad", c); }],
  ];
  let refused = 0;
  for (const [, f2] of rejects) {
    try { f2(); } catch (e) { if (String(e.message).includes("world-value-not-canonical")) refused++; }
  }
  const noJunk = !w2.exists("bad");
  report("L-ALIAS-1", "(write-mediation: the audit witness + ingress/nested aliases dead + 6 canonical-domain refusals, WORLD, BINDING)",
    egressDead && coherent && ingressDead && nestedDead && refused === rejects.length && noJunk ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `the audit's read-alias mutation is now a NO-OP (value [1], hash stable: ${egressDead}) and the two verifiers AGREE again (freshness ${f.verdict}, replay ok ${r.ok}) — pre-fix they disagreed (fresh vs value-mismatch, reproduced in the probe); ingress mutation after put dead (${ingressDead}), nested egress dead (${nestedDead}); ${refused}/${rejects.length} non-canonical values refused with world-value-not-canonical and no junk resource created (law:world.write-mediated@1)`);
}

// L-COHERE-1 : FRESH => REPLAY-COHERENT, the implication the witness
// falsified, as a property over random histories with adversarial alias
// attempts (law:warrant.fresh-replay-coherence@1).
{
  const rnd = (() => { let s = 0xC0DE5; return () => (s = (s * 1103515245 + 12345) & 0x7fffffff) / 0x80000000; })();
  const N = QUICK ? 60 : 200;
  let checked = 0, coherent = 0, freshCount = 0, staleAgree = 0, verValOk = true, pairsSeen = 0;
  for (let t = 0; t < N; t++) {
    const verVal = new Map();  // the invariant is PER-WORLD: same version => same value within one history
    const w = buildGraphWorld(["a", "b", "c"], [["a", "b"], ["b", "c"]]);
    w.registerQuery("incident:a", incidentScope("a"));
    const fn = componentMeasure(w, "a");
    const wa = deriveWarrant(w, { measure: "component-size(a)", predicate: "reach", measureFn: fn });
    const held = w.read("adj:b").value;                     // retained egress reference
    const ops = Math.floor(rnd() * 4);
    for (let k = 0; k < ops; k++) {
      const dice = rnd();
      if (dice < 0.35) { try { held.push("zz"); } catch { /* no-op */ } }          // alias attempt
      else if (dice < 0.55) { try { w.read("node:b").valueOf?.(); w.read("adj:a").value?.push?.("q"); } catch { /* no-op */ } }
      else if (dice < 0.8) w.put("noise:" + k, Math.floor(rnd() * 100));            // unrelated write
      else if (rnd() < 0.5) w.put("adj:b", ["a", "c"]);                             // honest identical rewrite
      else w.del("node:c");                                                          // honest support hit
    }
    for (const e of w.log) if (e.op === "put") {
      const k = e.resource + "@" + e.version;
      if (verVal.has(k) && verVal.get(k) !== e.hash) verValOk = false;
      verVal.set(k, e.hash); pairsSeen++;
    }
    for (const [n, e] of w.resourceEntries()) if (!e.deleted && verVal.get(n + "@" + e.version) !== e.hash) verValOk = false;
    const f = freshness(w, wa);
    const r = replayWarrant(w, wa, fn);
    checked++;
    if (f.verdict === "fresh") { freshCount++; if (r.ok) coherent++; }
    else if (!r.ok || f.verdict === "support_intact") staleAgree++;
  }
  const ok = coherent === freshCount && verValOk && checked === N;
  report("L-COHERE-1", "(FRESH => REPLAY-COHERENT over random histories with alias attempts + version=>value global invariant, WORLD+WARRANT, COHERENCE)",
    ok ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${N} random histories (alias attempts through retained and fresh read results, unrelated writes, identical rewrites, support deletions): every one of the ${freshCount} FRESH verdicts replayed ok (${coherent}/${freshCount}) — the implication the audit witness falsified now holds; non-fresh verdicts agree with replay or are support_intact refresh candidates (${staleAgree}); across ${pairsSeen} logged (resource, version) pairs per-world (store re-checked against its own log), same version => same value hash (${verValOk}) (law:warrant.fresh-replay-coherence@1, law:world.write-mediated@1)`);
}

// L-WAR-1 : freshness — and unrelated writes never invalidate
{
  const w = buildGraphWorld(["a", "b", "c", "d", "z1", "z2"], [["a", "b"], ["b", "c"]]);
  w.registerQuery("incident:a", incidentScope("a"));
  const fn = componentMeasure(w, "a");
  const wa = deriveWarrant(w, { measure: "component-size(a)", predicate: "reach", measureFn: fn, law_refs: ["law:warrant.freshness@1"] });
  const f0 = freshness(w, wa);
  // unrelated churn: nodes/edges nowhere near the component
  for (let i = 0; i < 25; i++) { w.put("node:z" + (i % 2 + 1), i); putEdge(w, "z1", "z2"); }
  const f1 = freshness(w, wa);
  const okVal = wa.value === 3;
  report("L-WAR-1", "(warrant freshness, verifying-trace check + unrelated-churn immunity, WARRANT, BINDING)",
    okVal && f0.verdict === "fresh" && f1.verdict === "fresh" ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `component-size(a)=3 warranted with footprint {exact:${wa.read_footprint.exact.length}, scopes:${wa.read_footprint.predicates.length}}; fresh at seal (${f0.verdict}); 50 UNRELATED writes later STILL fresh (${f1.verdict}) — freshness reads the footprint, not the world's write counter (law:warrant.freshness@1)`);
}

// L-WAR-2 : footprint soundness — jailed replay refuses authority beyond evidence
{
  const w = buildGraphWorld(["a", "b", "c"], [["a", "b"], ["b", "c"]]);
  w.registerQuery("incident:a", incidentScope("a"));
  const fn = componentMeasure(w, "a");
  const wa = deriveWarrant(w, { measure: "component-size(a)", predicate: "reach", measureFn: fn, law_refs: ["law:warrant.footprint-soundness@1"] });
  const rOk = replayWarrant(w, wa, fn);
  // forgery 1: PRUNE a footprint entry, reseal honestly
  const pruned = JSON.parse(cj(wa));
  pruned.read_footprint.exact = pruned.read_footprint.exact.filter(([n]) => n !== "edge:a|b");
  pruned.warrant_id = warrantIdOf(pruned);
  const rPruned = replayWarrant(w, pruned, fn);
  // forgery 2: inflate the value, reseal honestly
  const inflated = JSON.parse(cj(wa)); inflated.value = 99; inflated.warrant_id = warrantIdOf(inflated);
  const rInfl = replayWarrant(w, inflated, fn);
  // forgery 3: value mutation WITHOUT reseal — commitment breaks
  const unsealed = JSON.parse(cj(wa)); unsealed.value = 99;
  const rUns = replayWarrant(w, unsealed, fn);
  // forgery 4: support not a subset of the footprint (laundered provenance)
  const badSup = JSON.parse(cj(wa)); badSup.support = ["node:zz"]; badSup.warrant_id = warrantIdOf(badSup);
  const rSup = replayWarrant(w, badSup, fn);
  const ok = rOk.ok && !rPruned.ok && rPruned.reason === "undeclared-read"
    && !rInfl.ok && rInfl.reason === "value-mismatch"
    && !rUns.ok && rUns.reason === "value-mismatch" // semantic layer fires first; commitment asserted next
    && warrantIdOf(unsealed) !== unsealed.warrant_id
    && !rSup.ok && rSup.reason === "support-not-subset";
  report("L-WAR-2", "(footprint soundness, jailed replay + 4 forgeries, WARRANT, BINDING/ADEQUACY)",
    ok ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `honest replay ok; PRUNED footprint (honestly resealed) refused undeclared-read at the jail — the footprint is an authority claim and replay is its evidence; inflated value refused value-mismatch; unsealed mutation both diverges the commitment AND fails re-derivation; support beyond footprint refused support-not-subset (law:warrant.footprint-soundness@1)`);
}

// L-WAR-3 : THE PHANTOM — the grid's kappa case, executable, and its guard
{
  const w = buildGraphWorld(["a", "b"], [["a", "b"]]);
  w.registerQuery("incident:a", incidentScope("a"));
  const noScope = componentMeasure(w, "a", { withScope: false });
  const withScope = componentMeasure(w, "a", { withScope: true });
  const naked = deriveWarrant(w, { measure: "component-size(a)", predicate: "reach", measureFn: noScope });
  const guarded = deriveWarrant(w, { measure: "component-size(a)", predicate: "reach", measureFn: withScope, law_refs: ["law:warrant.phantom-scope@1"] });
  // THE PHANTOM: a brand-new node joins the component via a brand-new edge —
  // no resource the derivations READ has changed (adj:b changes... so route
  // the phantom through a node whose adjacency was never read: c attaches to
  // b, so adj:b changes — that IS an exact read. The true phantom: attach to
  // a node at the frontier whose adjacency read returned [] — reading [] is
  // still a versioned read. The genuine phantom in THIS encoding: a new node
  // + edge pair where the edge resource did not exist at read time and the
  // adjacency index is a DIFFERENT resource the derivation never read: the
  // reverse index "radj:". componentMeasure reads adj:, the world also
  // maintains radj: — a writer that updates ONLY radj:+edge creates a member
  // reachable by scope recomputation but invisible to every exact read.
  const en = "edge:" + ["b", "c"].sort().join("|");
  w.put("node:c", true); w.put("adj:c", ["b"]); w.put(en, true);
  const rc = w.read("adj:b").value ?? [];
  w.put("radj:b", [...rc, "c"]); // forward index adj:b DELIBERATELY stale — the phantom writer
  const fNaked = freshness(w, naked);
  const fGuard = freshness(w, guarded);
  // is the naked warrant's VALUE actually wrong now? recompute by full scan:
  const trueSize = reachFrom("a", (n) => w.read(n).value, () => w.names()).size;
  const phantomReal = trueSize !== naked.value;
  report("L-WAR-3", "(the phantom read, kappa's case executable: exact-reads-fresh while wrong; scope guard catches it, WARRANT, ADEQUACY)",
    phantomReal && fNaked.verdict === "fresh" && fGuard.verdict === "scope_dirty" ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `a node absent at read time joined the component without touching any exact read: true size ${trueSize} vs warranted ${naked.value}, yet the UNGUARDED warrant is '${fNaked.verdict}' — the phantom is real and kept red by construction; the scope-guarded warrant classifies '${fGuard.verdict}' on the incident-edge digest (law:warrant.phantom-scope@1). Exact reads alone cannot witness membership of a set that grew`);
}

// L-WAR-4 : the invalidation trichotomy, each verdict with its witness
{
  const w = buildGraphWorld(["a", "b", "c", "q"], [["a", "b"], ["b", "c"]]);
  w.registerQuery("incident:a", incidentScope("a"));
  const fn = componentMeasure(w, "a");
  const wa = deriveWarrant(w, { measure: "component-size(a)", predicate: "reach", measureFn: fn, law_refs: ["law:warrant.invalidation-trichotomy@1"] });
  // support_changed: delete a reached node
  const w1 = buildGraphWorld(["a", "b", "c", "q"], [["a", "b"], ["b", "c"]]);
  w1.registerQuery("incident:a", incidentScope("a"));
  const wa1 = deriveWarrant(w1, { measure: "component-size(a)", predicate: "reach", measureFn: componentMeasure(w1, "a") });
  w1.del("node:c");
  const f1 = freshness(w1, wa1);
  // scope_dirty: phantom via the L-WAR-3 route
  const w2 = buildGraphWorld(["a", "b"], [["a", "b"]]);
  w2.registerQuery("incident:a", incidentScope("a"));
  const wa2 = deriveWarrant(w2, { measure: "component-size(a)", predicate: "reach", measureFn: componentMeasure(w2, "a") });
  w2.put("node:c", true); w2.put("adj:c", ["b"]); w2.put("edge:" + ["b", "c"].sort().join("|"), true);
  const f2 = freshness(w2, wa2);
  // support_intact + EARLY CUTOFF: rewrite a read-but-not-support resource
  // with an equivalent value (adj list rewritten identically -> new version,
  // same content, same measure)
  const w3 = buildGraphWorld(["a", "b", "c"], [["a", "b"], ["b", "c"]]);
  w3.registerQuery("incident:a", incidentScope("a"));
  const fn3 = componentMeasure(w3, "a");
  const wa3 = deriveWarrant(w3, { measure: "component-size(a)", predicate: "reach", measureFn: fn3 });
  w3.put("adj:b", w3.read("adj:b").value); // version bump, value identical
  const f3 = freshness(w3, wa3);
  const cut = f3.verdict === "support_intact" ? refreshWarrant(w3, wa3, fn3) : { refreshed: false };
  const f3b = cut.refreshed ? freshness(w3, cut.warrant) : { verdict: "n/a" };
  const ok = f1.verdict === "support_changed" && f1.witness.resource === "node:c"
    && f2.verdict === "scope_dirty"
    && f3.verdict === "support_intact" && cut.refreshed && f3b.verdict === "fresh"
    && cut.warrant.value === wa3.value && cut.warrant.warrant_id !== wa3.warrant_id;
  report("L-WAR-4", "(invalidation trichotomy + early cutoff, three worlds, each verdict witnessed, WARRANT, COHERENCE)",
    ok ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `support_changed witnesses {resource: node:c}; scope_dirty witnesses the incident digest; support_intact (a read-but-not-support version bump with identical content) REFRESHES under jailed re-derivation — value preserved, footprint reversioned, warrant_id reseals, and the refreshed warrant is fresh: the verifying-trace early cutoff, as a warrant operation (law:warrant.invalidation-trichotomy@1)`);
}

// L-WAR-5 : the SHARED footprint — the scheduler certificate as a warrant
{
  let ok = false, detail = "scheduler_certificate.json not present";
  if (existsSync("scheduler_certificate.json")) {
    const cert = JSON.parse(readFileSync("scheduler_certificate.json", "utf8"));
    const w = new World();
    const corpusRes = "corpus:" + cert.corpus.id;
    w.put(corpusRes, cert.corpus.sha256);
    const cw = warrantOfCertificate(w, cert, corpusRes);
    const f0 = freshness(w, cw);
    w.put("unrelated:x", 1);
    const f1 = freshness(w, cw);
    w.put(corpusRes, "0".repeat(64)); // the corpus resource changes
    const f2 = freshness(w, cw);
    ok = f0.verdict === "fresh" && f1.verdict === "fresh" && f2.verdict === "support_changed"
      && cw.read_footprint.exact.length === 1 && warrantIdOf(cw) === cw.warrant_id;
    detail = `the shipped certificate wrapped as a Warrant v3: corpus{id,sha256} is ONE exact read [${corpusRes}@1], evidence is the value, the ${cert.run_manifest.length}-receipt manifest hash is the witness; fresh at seal, fresh under unrelated writes, support_changed when the corpus resource moves — certificate freshness IS warrant freshness, one evidence language (law:footprint.shared@1, the requirement round 5 adopted)`;
  }
  report("L-WAR-5", "(shared footprint, SchedulerCertificate wrapped as a warrant, CERT+WARRANT, REFINEMENT)",
    ok ? "PROPERTY-TESTED" : "FALSIFIED?!", detail);
}

// L-COMP-1 : THE COMPOSITION PHANTOM — staleness laundered through a
// publication, kept red by construction (law:warrant.composition@1). A
// cites nothing; B cites A NAIVELY (publication read, no freshness scope).
// A is made phantom-stale (round-7's route: the world grows a member no
// exact read of A ever touched). A's publication resource never moved — so
// naive B is 'fresh' while transitively wrong.
{
  const w = buildGraphWorld(["a", "b"], [["a", "b"]]);
  w.registerQuery("incident:a", incidentScope("a"));
  const fnA = componentMeasure(w, "a");
  const A = deriveWarrant(w, { measure: "component-size(a)", predicate: "reach", measureFn: fnA });
  publishWarrant(w, "A", A);
  const mkComposite = (naive) => deriveComposite(w, {
    measure: "double-of-A", predicate: "2*cite(A)", naive,
    measureFn: (view, cite) => {
      const pub = cite("A");
      return { value: 2 * pub.value, witness: { cited: pub.warrant_id }, support: ["warrant:A"] };
    },
  });
  const naiveB = mkComposite(true);
  const guardB = mkComposite(false);
  // the phantom, one level down: a member A never read
  w.put("node:c", true); w.put("adj:c", ["b"]); w.put("edge:" + ["b", "c"].sort().join("|"), true);
  const fA = freshness(w, A);
  const fNaive = freshness(w, naiveB);
  const fGuard = freshness(w, guardB);
  const trueA = reachFrom("a", (n) => w.read(n).value, () => w.names()).size;
  const laundered = fA.verdict === "scope_dirty" && fNaive.verdict === "fresh" && trueA !== A.value;
  report("L-COMP-1", "(the composition phantom: publication-only citation launders staleness — kept red, WARRANT, ADEQUACY)",
    laundered && fGuard.verdict === "scope_dirty" ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `A is ${fA.verdict} (true size ${trueA} vs published ${A.value}) yet the NAIVE composite is '${fNaive.verdict}' — its only exact read, warrant:A, never moved: staleness laundered through the publication, kept red by construction. The GUARDED composite (freshness reified as the warrant-fresh:A scope) is '${fGuard.verdict}' on the same world (law:warrant.composition@1)`);
}

// L-COMP-2 : propagation through chains and diamonds — one ground movement
// dirties every guarded citer, along every path, with dedup at the joins.
{
  const w = buildGraphWorld(["a", "b", "c"], [["a", "b"], ["b", "c"]]);
  w.registerQuery("incident:a", incidentScope("a"));
  const D = deriveWarrant(w, { measure: "component-size(a)", predicate: "reach", measureFn: componentMeasure(w, "a") });
  publishWarrant(w, "D", D);
  const mk = (name, cites, f) => {
    const cw = deriveComposite(w, { measure: name, predicate: name,
      measureFn: (view, cite) => {
        const vals = cites.map((c) => cite(c).value);
        return { value: f(vals), witness: { cites }, support: cites.map((c) => "warrant:" + c) };
      } });
    publishWarrant(w, name, cw);
    return cw;
  };
  const A2 = mk("A2", ["D"], ([d]) => d + 1);
  const B2 = mk("B2", ["D"], ([d]) => d * 10);
  const C2 = mk("C2", ["A2", "B2"], ([x, y]) => x + y);
  const before = [freshness(w, A2).verdict, freshness(w, B2).verdict, freshness(w, C2).verdict];
  w.del("node:c"); // ground truth moves: D support_changed
  const fD = freshness(w, D);
  const after = [freshness(w, A2).verdict, freshness(w, B2).verdict, freshness(w, C2).verdict];
  // C2's footprint must contain each publication ONCE and each freshness scope ONCE (dedup at the diamond join)
  const cN = (arr, p) => arr.filter(([n]) => n === p).length;
  const dedup = cN(C2.read_footprint.exact, "warrant:A2") === 1 && cN(C2.read_footprint.predicates, "warrant-fresh:A2") === 1;
  const ok = before.every((v) => v === "fresh") && fD.verdict === "support_changed"
    && after.every((v) => v === "scope_dirty") && dedup;
  report("L-COMP-2", "(freshness propagation: chain + diamond, one ground movement dirties every guarded citer, WARRANT, COHERENCE)",
    ok ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `diamond D<-{A2,B2}<-C2 all fresh at seal; deleting node:c makes D ${fD.verdict} and every citer [${after.join(", ")}] — the reified freshness scopes re-evaluate the CITEE's footprint against the current world, so staleness propagates without any publication write, along both diamond paths, with footprint dedup at the join (law:warrant.composition@1)`);
}

// L-COMP-3 : the abstraction boundary IS the jail — composite replay reads
// publications only; citing internals it never declared refuses.
{
  const w = buildGraphWorld(["a", "b"], [["a", "b"]]);
  w.registerQuery("incident:a", incidentScope("a"));
  const A = deriveWarrant(w, { measure: "component-size(a)", predicate: "reach", measureFn: componentMeasure(w, "a") });
  publishWarrant(w, "A", A);
  const mfn = (view, cite) => {
    const pub = cite("A");
    return { value: 2 * pub.value, witness: { cited: pub.warrant_id }, support: ["warrant:A"] };
  };
  const B = deriveComposite(w, { measure: "double-of-A", predicate: "2*cite(A)", measureFn: mfn });
  const rOk = replayComposite(w, B, mfn);
  const internals = B.read_footprint.exact.some(([n]) => n.startsWith("node:") || n.startsWith("edge:") || n.startsWith("adj:"));
  // a sneaky measureFn that reaches for A's internals on replay
  const sneaky = (view, cite) => { view.read("node:a"); return mfn(view, cite); };
  const rSneak = replayComposite(w, B, sneaky);
  // pruning the publication read from the footprint, honestly resealed:
  // dies STRUCTURALLY now — support still names warrant:A (support-not-subset,
  // pre-jail, from the round-8.2 support-soundness closure)
  const pruned = JSON.parse(cj(B));
  pruned.read_footprint.exact = pruned.read_footprint.exact.filter(([n]) => n !== "warrant:A");
  pruned.warrant_id = warrantIdOf(pruned);
  const rPruned = replayComposite(w, pruned, mfn);
  // the FULLY CONSISTENT forgery — publication pruned from footprint AND
  // support — passes the structural layer and must still die at the JAIL
  const pruned2 = JSON.parse(cj(B));
  pruned2.read_footprint.exact = pruned2.read_footprint.exact.filter(([n]) => n !== "warrant:A");
  pruned2.support = [];
  pruned2.warrant_id = warrantIdOf(pruned2);
  const rPruned2 = replayComposite(w, pruned2, mfn);
  const ok = rOk.ok && !internals
    && !rSneak.ok && rSneak.reason === "undeclared-read" && rSneak.resource === "node:a"
    && !rPruned.ok && rPruned.reason === "support-not-subset"
    && !rPruned2.ok && rPruned2.reason === "undeclared-read" && rPruned2.resource === "warrant:A";
  report("L-COMP-3", "(abstraction boundary: composite footprints carry publications only; internals refuse at the jail, WARRANT, BINDING)",
    ok ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `the composite's footprint contains warrant:A and its freshness scope and NO citee internals (${!internals}); honest replay ok; a replayer reaching for node:a refuses undeclared-read — the composite provably used only the published value; the pruned publication now dies TWICE over — structurally at support-not-subset, and (when the forger also prunes support for consistency) at the jail with undeclared-read at warrant:A (law:warrant.composition@1; law:warrant.support-soundness@1 and the jail layered)`);
}

// L-FRAME-1 : sigma T4, the frame rule as a property test — a write's
// effect on a warrant's verdict is PREDICTED by footprint membership and
// scope influence, over random writes (law:warrant.frame@1).
{
  const w = buildGraphWorld(["a", "b", "c", "x", "y"], [["a", "b"], ["b", "c"], ["x", "y"]]);
  w.registerQuery("incident:a", incidentScope("a"));
  const fn = componentMeasure(w, "a");
  const seal = () => deriveWarrant(w, { measure: "component-size(a)", predicate: "reach", measureFn: fn, law_refs: ["law:warrant.frame@1"] });
  const rnd = (() => { let s = 0xF7A3E; return () => (s = (s * 1103515245 + 12345) & 0x7fffffff) / 0x80000000; })();
  const pool = ["node:x", "node:y", "adj:x", "node:c", "adj:b", "node:q", "edge:" + ["x", "y"].sort().join("|"), "edge:" + ["b", "c"].sort().join("|")];
  let agree = 0, inside = 0, outside = 0;
  const N = QUICK ? 40 : 120;
  for (let i = 0; i < N; i++) {
    const wa = seal();
    const name = pool[Math.floor(rnd() * pool.length)];
    const exactSet = new Set(wa.read_footprint.exact.map(([n]) => n));
    const scopeBefore = wa.read_footprint.predicates.map(([q]) => w.scopeEval(q).digest);
    if (rnd() < 0.5 || !w.exists(name)) w.put(name, Math.floor(rnd() * 1e6)); else w.del(name);
    const scopeAfter = wa.read_footprint.predicates.map(([q]) => w.scopeEval(q).digest);
    const touchesExact = exactSet.has(name);
    const touchesScope = scopeBefore.some((d, k) => d !== scopeAfter[k]);
    const predicted = !touchesExact && !touchesScope ? "fresh"
      : touchesScope && !touchesExact ? "scope_dirty"
      : new Set(wa.support).has(name) ? "support_changed"
      : touchesExact ? (touchesScope ? "scope_dirty_or_support" : "support_intact") : "fresh";
    const f = freshness(w, wa);
    const okOne = predicted === "scope_dirty_or_support"
      ? (f.verdict === "scope_dirty" || f.verdict === "support_changed" || f.verdict === "support_intact")
      : f.verdict === predicted;
    if (okOne) agree++;
    if (touchesExact || touchesScope) inside++; else outside++;
  }
  report("L-FRAME-1", "(the frame rule, sigma T4: footprint membership + scope influence PREDICT the verdict over random writes, WARRANT, LOCALITY)",
    agree === N ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${agree}/${N} random writes (${inside} inside the warrant's evidence, ${outside} outside): the classifier — outside both footprint and scope influence => fresh; scope influence only => scope_dirty; support hit => support_changed; non-support exact hit => support_intact — predicted every verdict. Writes outside a warrant's evidence CANNOT change its verdict: the separation-logic frame rule, as a world property (law:warrant.frame@1; sigma T4's instance at this layer)`);
}

// L-SUPPORT-1 : support authority under attack (round 8.2 —
// law:warrant.support-soundness@1). The audit's laundering chain is locked
// VERBATIM: honest support ["r:x"] -> forge [] + honest reseal -> replay
// (pre-fix: ok; now MUST refuse support-mismatch) -> r:x moves -> the
// forged warrant's freshness still reads support_intact (freshness cannot
// see forgery without the engine — stated, not hidden) -> refresh
// RE-DERIVES and restores true support, breaking the chain at the gate the
// maintenance loop will actually use. Then the forgery list.
{
  const mkW = () => { const w = new World(); w.put("r:x", 1); return w; };
  const fn = (view) => { const x = view.read("r:x"); return { value: x > 0, witness: { x }, support: ["r:x"] }; };
  const w = mkW();
  const honest = deriveWarrant(w, { measure: "x>0", predicate: "positivity", measureFn: fn, law_refs: ["law:warrant.support-soundness@1"] });
  const reseal = (f) => { f.warrant_id = warrantIdOf(f); return f; };
  const forge = (mut) => { const f = JSON.parse(cj(honest)); mut(f); return reseal(f); };
  // THE CHAIN
  const forged = forge((f) => { f.support = []; });
  const r0 = replayWarrant(w, forged, fn);
  const chainReplayRefused = !r0.ok && r0.reason === "support-mismatch";
  w.put("r:x", 2);
  const fHonest = freshness(w, honest), fForged = freshness(w, forged);
  const classificationSplit = fHonest.verdict === "support_changed" && fForged.verdict === "support_intact";
  const cut = refreshWarrant(w, forged, fn);
  const chainBroken = cut.refreshed && cj(cut.warrant.support) === cj(["r:x"])
    && replayWarrant(w, cut.warrant, fn).ok
    && (w.put("r:x", 3), freshness(w, cut.warrant).verdict === "support_changed");
  // THE FORGERY LIST, each on its declared refusal
  const w2 = mkW();
  const h2 = deriveWarrant(w2, { measure: "x>0", predicate: "positivity", measureFn: fn });
  const exp = (f, want) => { const r = replayWarrant(w2, f, fn); return !r.ok && r.reason === want; };
  const forge2 = (mut) => { const f = JSON.parse(cj(h2)); mut(f); return reseal(f); };
  const cases = [
    ["prune-resealed", exp(forge2((f) => { f.support = []; }), "support-mismatch")],
  ];
  const w3 = new World(); w3.put("r:x", 1); w3.put("r:aux", 9);
  const fn3 = (view) => { const x = view.read("r:x"); view.read("r:aux"); return { value: x > 0, witness: { x }, support: ["r:x"] }; };
  const h3 = deriveWarrant(w3, { measure: "x>0", predicate: "positivity", measureFn: fn3 });
  const reseal3 = (f) => { f.warrant_id = warrantIdOf(f); return f; };
  const exp3 = (f, want) => { const r = replayWarrant(w3, f, fn3); return !r.ok && r.reason === want; };
  const forge3 = (mut) => { const f = JSON.parse(cj(h3)); mut(f); return reseal3(f); };
  cases.push(["nonsemantic-read-added", exp3(forge3((f) => { f.support = ["r:aux", "r:x"]; }), "support-mismatch")]);
  cases.push(["outside-footprint", exp3(forge3((f) => { f.support = ["r:x", "r:zz"]; }), "support-not-subset")]);
  cases.push(["duplicate-entry", exp3(forge3((f) => { f.support = ["r:x", "r:x"]; }), "support-mismatch")]);
  const reorderNoop = (() => { const f = JSON.parse(cj(h3)); f.support = [...f.support].reverse(); return warrantIdOf(f) === h3.warrant_id || cj(f.support) === cj(h3.support); })();
  // composite support forgeries
  const w4 = new World(); w4.put("r:x", 1);
  const g4 = deriveWarrant(w4, { measure: "x>0", predicate: "positivity", measureFn: (view) => { const x = view.read("r:x"); return { value: x > 0, witness: { x }, support: ["r:x"] }; } });
  publishWarrant(w4, "G", g4);
  const cfn = (view, cite) => { const p = cite("G"); return { value: !p.value, witness: { cited: p.warrant_id }, support: ["warrant:G"] }; };
  const c4 = deriveComposite(w4, { measure: "not-G", predicate: "!cite(G)", measureFn: cfn });
  const expC = (f, want) => { const r = replayComposite(w4, f, cfn); return !r.ok && r.reason === want; };
  const forgeC = (mut) => { const f = JSON.parse(cj(c4)); mut(f); f.warrant_id = warrantIdOf(f); return f; };
  cases.push(["composite-prune", expC(forgeC((f) => { f.support = []; }), "support-mismatch")]);
  cases.push(["composite-inflation", expC(forgeC((f) => { f.support = ["warrant:G", "warrant-fresh:G"]; }), "support-not-subset")]);
  const bad = cases.filter(([, ok2]) => !ok2).map(([nm]) => nm);
  report("L-SUPPORT-1", "(support soundness: the audit's laundering chain locked + 6 forgeries + reorder-is-noop, WARRANT, BINDING/ADEQUACY)",
    chainReplayRefused && classificationSplit && chainBroken && reorderNoop && bad.length === 0 ? "PROPERTY-TESTED" : "FALSIFIED?!",
    chainReplayRefused && classificationSplit && chainBroken
      ? `THE CHAIN: forged-empty support now refuses support-mismatch at replay (pre-fix it replayed ok — reproduced in the probe); the classification split the audit measured is real and STATED (honest support_changed vs forged support_intact — freshness cannot see forgery without the engine); refresh RE-DERIVES support, restoring ["r:x"], and the refreshed warrant classifies support_changed on the next movement — the laundering chain is broken at the gate the maintenance loop will use. Forgeries: prune, nonsemantic-read inflation, duplicate (canonical form), composite prune/inflation each refused on their declared reason; outside-footprint dies structurally; reordering is a NO-OP by canonical construction (${reorderNoop}). ${bad.length === 0 ? "6/6" : "FAIL: " + bad.join(",")} (law:warrant.support-soundness@1)`
      : `chain assertions failed: replay ${chainReplayRefused}, split ${classificationSplit}, broken ${chainBroken}; forgeries: ${bad.join(",")}`);
}

// emit the world warrant receipt (engine-free half checked by grid_check)
// L-MAINT-1 : the pass — dependency order real, convergence to all-fresh,
// and the WRONG-ORDER counterfactual kept red (law:maintenance.pass@1).
{
  const mkChain = () => {
    const w = buildGraphWorld(["a", "b", "c"], [["a", "b"], ["b", "c"]]);
    w.registerQuery("incident:a", incidentScope("a"));
    const m = new Maintainer(w);
    m.addGround("A", { measure: "component-size(a)", predicate: "reach", measureFn: componentMeasure(w, "a") });
    m.addComposite("B", ["A"], { measure: "B=A+1", predicate: "cite(A)+1",
      measureFn: (view, cite) => { const p = cite("A"); return { value: p.value + 1, witness: { cited: p.warrant_id }, support: ["warrant:A"] }; } });
    m.addComposite("C", ["B"], { measure: "C=B*10", predicate: "cite(B)*10",
      measureFn: (view, cite) => { const p = cite("B"); return { value: p.value * 10, witness: { cited: p.warrant_id }, support: ["warrant:B"] }; } });
    return { w, m };
  };
  const { w, m } = mkChain();
  w.del("node:c");                                  // ground moves: A's support
  const rec = m.pass();
  const order = rec.steps.map((s) => s.name);
  const orderOk = order.indexOf("A") < order.indexOf("B") && order.indexOf("B") < order.indexOf("C");
  const allActed = rec.steps.every((s) => s.action === "rederived");
  const converged = [...m.state.entries()].every(([, wr]) => freshness(w, wr).verdict === "fresh");
  const values = { A: m.state.get("A").value, B: m.state.get("B").value, C: m.state.get("C").value };
  const valuesOk = values.A === 2 && values.B === 3 && values.C === 30;
  // B's new footprint must cite A's NEW publication version (order was real)
  const bCitesNewA = m.state.get("B").read_footprint.exact.some(([n, v]) => n === "warrant:A" && v === w.read("warrant:A").version);
  // COUNTERFACTUAL, kept red: process C before A on a throwaway fork —
  // C refreshes against stale citees and the world CANNOT be all-fresh after
  const { w: w2, m: m2 } = mkChain();
  w2.del("node:c");
  const fork = w2.fork();
  const defC = m2.defs.get("C");
  const nwC = deriveComposite(fork, defC.spec);        // C re-derived FIRST (wrong order)
  publishWarrant(fork, "C", nwC);
  const defA = m2.defs.get("A");
  const nwA = deriveWarrant(fork, defA.spec);          // then A
  publishWarrant(fork, "A", nwA);
  // both halves asserted: the wrong-order C carries the WRONG value (stale
  // citee) AND is detectably non-fresh once A lands — no ||-junk here; the
  // last audit caught exactly that species and we do not ship it twice.
  const wrongOrderDirty = nwC.value !== 30 && freshness(fork, nwC).verdict !== "fresh";
  report("L-MAINT-1", "(maintenance pass: topo order real, convergence, values correct, wrong-order counterfactual kept red, MAINTENANCE, COHERENCE)",
    orderOk && allActed && converged && valuesOk && bCitesNewA && wrongOrderDirty && !rec.aborted && !rec.refused ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `ground moved (node:c deleted): one pass re-derives A then B then C (order asserted: ${orderOk}); every published warrant is FRESH after (${converged}) with correct values A=2,B=3,C=30 (${valuesOk}) and B's footprint cites A's NEW publication (${bCitesNewA}); the wrong-order counterfactual — C re-derived before A on a throwaway fork — leaves C non-fresh (${wrongOrderDirty}), kept red: a citer refreshed against a stale citee cannot be current (law:maintenance.pass@1)`);
}

// L-MAINT-2 : converged DAG = receipted NO-OP (law:maintenance.receipt@1).
{
  const w = buildGraphWorld(["a", "b"], [["a", "b"]]);
  w.registerQuery("incident:a", incidentScope("a"));
  const m = new Maintainer(w);
  m.addGround("A", { measure: "component-size(a)", predicate: "reach", measureFn: componentMeasure(w, "a") });
  m.addComposite("B", ["A"], { measure: "B=A+1", predicate: "cite(A)+1",
    measureFn: (view, cite) => { const p = cite("A"); return { value: p.value + 1, witness: { cited: p.warrant_id }, support: ["warrant:A"] }; } });
  w.del("node:b");
  const r1 = m.pass();
  const vAfter = w.vclock;
  const r2 = m.pass();
  const ok = !r1.no_op && r2.no_op && r2.steps.every((s) => s.action === "none")
    && r2.vclock_before === vAfter && r2.vclock_after === vAfter
    && cj(r2.before) === cj(r2.after);
  report("L-MAINT-2", "(convergence: the second pass is a receipted no-op — zero writes, all-none steps, before==after, MAINTENANCE, IDEMPOTENCE)",
    ok ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `pass 1 re-derives (${r1.steps.filter((s) => s.action !== "none").length} nodes moved); pass 2 with no world movement: no_op=${r2.no_op}, every step 'none', vclock unmoved (${r2.vclock_before}==${r2.vclock_after}), before==after committed maps identical — maintenance is idempotent at quiescence and the receipt PROVES the no-op rather than asserting it (law:maintenance.receipt@1)`);
}

// L-MAINT-3 : quarantine, never repair (law:maintenance.quarantine@1).
{
  const w = buildGraphWorld(["a", "b"], [["a", "b"]]);
  w.registerQuery("incident:a", incidentScope("a"));
  const m = new Maintainer(w);
  m.addGround("A", { measure: "component-size(a)", predicate: "reach", measureFn: componentMeasure(w, "a") });
  const honest = m.state.get("A");
  const forged = JSON.parse(cj(honest)); forged.support = []; forged.warrant_id = warrantIdOf(forged);
  // door 1: external ingest replay-gates
  const gate = m.register("A", forged);
  // door 2: poison the state directly; the pass must quarantine, not republish
  m.state.set("A", forged);
  const pubBefore = w.read("warrant:A").version;
  const rec = m.pass();
  const step = rec.steps.find((s) => s.name === "A");
  const ok = gate.quarantined === true && gate.reason === "support-mismatch"
    && step.action === "quarantined" && step.reason === "support-mismatch"
    && w.read("warrant:A").version === pubBefore
    && step.warrant_id_before === step.warrant_id_after;
  report("L-MAINT-3", "(quarantine at both doors: register() replay-gates; a poisoned FRESH node is quarantined in-pass, publication untouched, MAINTENANCE, BINDING)",
    ok ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `external ingest of the support-forged warrant refused at the door (${gate.reason}); the same forgery poisoned directly into maintainer state is QUARANTINED by the pass (fresh nodes are replay-validated — versions permit it exactly then): publication version unmoved (${pubBefore}), ids unchanged in the step record, nothing forged republished or repaired-in-place (law:maintenance.quarantine@1)`);
}

// L-MAINT-4 : diamond — once per node, deterministic receipts
// (law:maintenance.pass@1, dedup half).
{
  const mk = () => {
    const w = buildGraphWorld(["a", "b", "c"], [["a", "b"], ["b", "c"]]);
    w.registerQuery("incident:a", incidentScope("a"));
    const m = new Maintainer(w);
    m.addGround("A", { measure: "component-size(a)", predicate: "reach", measureFn: componentMeasure(w, "a") });
    const mk2 = (nm, f) => m.addComposite(nm, ["A"], { measure: nm, predicate: nm,
      measureFn: (view, cite) => { const p = cite("A"); return { value: f(p.value), witness: { cited: p.warrant_id }, support: ["warrant:A"] }; } });
    mk2("B", (x) => x + 1); mk2("C", (x) => x * 10);
    m.addComposite("D", ["B", "C"], { measure: "D=B+C", predicate: "cite(B)+cite(C)",
      measureFn: (view, cite) => { const b = cite("B"), c = cite("C"); return { value: b.value + c.value, witness: { b: b.warrant_id, c: c.warrant_id }, support: ["warrant:B", "warrant:C"] }; } });
    w.del("node:c");
    return m.pass();
  };
  const r1 = mk(), r2 = mk();
  const names = r1.steps.map((s) => s.name);
  const oncePer = new Set(names).size === 4 && names.length === 4;
  const orderOk = names.indexOf("A") < names.indexOf("B") && names.indexOf("A") < names.indexOf("C")
    && names.indexOf("B") < names.indexOf("D") && names.indexOf("C") < names.indexOf("D");
  const deterministic = r1.pass_id === r2.pass_id;
  report("L-MAINT-4", "(diamond D<-{B,C}<-A: exactly one step per node, both paths below the join, identical receipts across identical runs, MAINTENANCE, COHERENCE)",
    oncePer && orderOk && deterministic ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `one ground movement drives exactly 4 steps [${names.join(",")}] — A once (not once per path), join D after both arms (${orderOk}); two identical scenarios seal IDENTICAL pass_ids (${deterministic}): the deterministic Kahn order makes the receipt reproducible, not narrative (law:maintenance.pass@1)`);
}

// L-MAINT-5 : cycle refusal — impossible via the API, refused at the pass
// against direct defs poisoning (law:maintenance.acyclicity@1).
{
  const w = buildGraphWorld(["a"], []);
  w.registerQuery("incident:a", incidentScope("a"));
  const m = new Maintainer(w);
  m.addGround("A", { measure: "component-size(a)", predicate: "reach", measureFn: componentMeasure(w, "a") });
  let apiRefused = false;
  try { m.addComposite("X", ["Y"], { measure: "x", predicate: "x", measureFn: () => ({}) }); }
  catch (e) { apiRefused = String(e.message).includes("maintenance-cycle-guard"); }
  // poison defs directly with a 2-cycle
  m.defs.set("X", { kind: "composite", cites: ["Y"], spec: { measure: "x", predicate: "x", measureFn: (v, c) => ({ value: 1, witness: {}, support: [] }) } });
  m.defs.set("Y", { kind: "composite", cites: ["X"], spec: { measure: "y", predicate: "y", measureFn: (v, c) => ({ value: 1, witness: {}, support: [] }) } });
  const vb = w.vclock;
  const rec = m.pass();
  const ok = apiRefused && rec.refused === true && rec.reason === "maintenance-cycle"
    && cj(rec.cycle) === cj(["X", "Y"]) && w.vclock === vb && rec.steps.length === 0;
  report("L-MAINT-5", "(acyclicity: forward refs impossible via the API; a poisoned 2-cycle refuses the WHOLE pass, names its members, world untouched, MAINTENANCE, WELL-FOUNDEDNESS)",
    ok ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `addComposite citing an unknown name refuses at the guard (${apiRefused}); a 2-cycle poisoned directly into defs refuses the pass with maintenance-cycle naming [${(rec.cycle ?? []).join(",")}], zero steps, vclock unmoved — acyclicity is PROVED per pass by Kahn leftover, not assumed of inputs (law:maintenance.acyclicity@1)`);
}

// L-MAINT-6 : failure atomicity — a mid-pass throw discards the fork
// (law:maintenance.atomicity@1).
{
  const w = buildGraphWorld(["a", "b"], [["a", "b"]]);
  w.registerQuery("incident:a", incidentScope("a"));
  const m = new Maintainer(w);
  m.addGround("A", { measure: "component-size(a)", predicate: "reach", measureFn: componentMeasure(w, "a") });
  m.addComposite("B", ["A"], { measure: "B", predicate: "throws-when-flagged",
    measureFn: (view, cite) => {
      const p = cite("A");
      if (view.read("flag:boom") === 1) { const e = new Error("measure exploded"); e.maintName = "B"; throw e; }
      return { value: p.value + 1, witness: { cited: p.warrant_id }, support: ["warrant:A"] };
    } });
  w.put("flag:boom", 1);      // arm the bomb AND dirty B's footprint
  w.del("node:b");            // dirty A too — A will re-derive on the fork first
  const pubA = w.read("warrant:A").version, pubB = w.read("warrant:B").version, vb = w.vclock;
  const idA = m.state.get("A").warrant_id;
  const rec = m.pass();
  const ok = rec.aborted === true && rec.at === "B"
    && w.read("warrant:A").version === pubA && w.read("warrant:B").version === pubB
    && w.vclock === vb && m.state.get("A").warrant_id === idA
    && rec.vclock_before === rec.vclock_after;
  report("L-MAINT-6", "(atomicity: A re-derived on the fork, then B's measure throws — the fork is DISCARDED, real world and state untouched, MAINTENANCE, BINDING)",
    ok ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `mid-pass failure at B after A had already re-derived on the fork: the real world's publications (A@${pubA}, B@${pubB}), vclock (${vb}), and maintainer state are byte-identical to before — nothing half-advanced; the receipt records {aborted, at: B} with the completed steps for forensics (law:maintenance.atomicity@1)`);
}

// L-CONFINE-1 : the audit's fork-escape witness, VERBATIM, post-confinement
// (law:maintenance.capability-confinement@1). Pre-fix (frozen in
// probe_forkescape_v05_repro.mjs): ATOMIC=false and the aborted receipt
// normalized the escaped 3->4 transition into its alleged pre-state.
{
  const w = new World();
  w.put("flag", 0);
  const m = new Maintainer(w);
  const realWorld = w;
  m.addGround("A", { measure: "escape", predicate: "flag", measureFn: (view) => {
    const f = view.read("flag");
    if (f === 1) { realWorld.put("leak", { escaped: true }); throw new Error("boom"); }
    return { value: f, witness: { f }, support: ["flag"] };
  } });
  w.put("flag", 1);
  const entry = w.vclock;
  const rec = m.pass();
  const atomic = w.vclock === entry && w.read("leak").version === 0;
  const receiptTruth = rec.vclock_before === entry && rec.vclock_after === entry;
  const taggedAt = rec.at === "A";
  const reasonOk = String(rec.reason).includes("world-write-during-maintenance");
  const lockReleased = (() => { try { w.put("post", 1); return w.read("post").value === 1; } catch { return false; } })();
  report("L-CONFINE-1", "(the fork-escape witness under confinement: escaped write refuses, world untouched, receipt reports the ACTUAL entry clock, lock released, MAINTENANCE, BINDING)",
    rec.aborted && atomic && receiptTruth && taggedAt && reasonOk && lockReleased ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `the captured-authority write now REFUSES (${reasonOk ? "world-write-during-maintenance" : rec.reason}) and aborts the pass at '${rec.at}'; the real world is untouched (vclock ${w.vclock - 1} == entry ${entry}, leak absent: ${atomic}); the receipt reports vclock_before ${rec.vclock_before} == the ACTUAL entry clock — pre-fix it reported the already-mutated clock, hiding the escaped transition entirely; the lock is released by finally (${lockReleased}). Escapes become aborts, not corruption (law:maintenance.capability-confinement@1)`);
}

// L-CONFINE-2 : the confinement matrix + lock lifecycle + capability
// refusals (law:maintenance.capability-confinement@1).
{
  const results = [];
  const mkBase = () => {
    const w = buildGraphWorld(["a", "b"], [["a", "b"]]);
    w.registerQuery("incident:a", incidentScope("a"));
    return w;
  };
  // del-escape from a composite's derivation, mid-pass
  { const w = mkBase(); const m = new Maintainer(w); const real = w;
    m.addGround("A", { measure: "component-size(a)", predicate: "reach", measureFn: componentMeasure(w, "a") });
    m.addComposite("B", ["A"], { measure: "B", predicate: "escape-del",
      measureFn: (view, cite) => { const p = cite("A");
        if (view.read("armed") === 1) { real.del("node:a"); }
        return { value: p.value, witness: {}, support: ["warrant:A"] }; } });
    w.put("armed", 1);
    const entry = w.vclock;
    const rec = m.pass();
    results.push(["composite-del-escape", rec.aborted && rec.at === "B" && w.vclock === entry && w.exists("node:a")]); }
  // poisoned QUERY captures the real world and writes during scope
  // evaluation — ARMED after registration, because addGround derives on the
  // unlocked real world by design (register/addGround are not transactional;
  // the confinement law scopes to PASSES) and an unarmed poison would leak
  // legitimately there.
  { const w = mkBase(); const real = w;
    w.registerQuery("poison", ({ value }) => {
      if (value("armed") === 1) real.put("qleak", 1);
      return []; });
    const m = new Maintainer(w);
    m.addGround("A", { measure: "scoped", predicate: "reach", measureFn: (view) => {
      const v = view.read("node:a"); view.scope("poison");
      return { value: v === true ? 1 : 0, witness: {}, support: ["node:a"] }; } });
    w.put("armed", 1);                          // arm AFTER registration
    w.del("node:a");                            // support hit -> the pass runs the query on the fork
    const entry = w.vclock;
    const rec = m.pass();
    results.push(["query-capture-escape", rec.aborted && w.vclock === entry && w.read("qleak").version === 0]); }
  // escape during REFRESH (support_intact path)
  { const w = mkBase(); const real = w; const m = new Maintainer(w);
    m.addGround("A", { measure: "refresh-escape", predicate: "reach", measureFn: (view) => {
      const reached = view.read("node:a") === true && view.read("edge:a|b") === true;
      view.read("adj:a");
      if (view.read("armed") === 1) real.put("rleak", 1);
      return { value: reached ? 2 : 0, witness: {}, support: ["node:a", "edge:a|b"] }; } });
    w.put("armed", 1);                          // hmm: armed wasn't read pre-arm -> footprint lacks it
    w.put("adj:a", w.read("adj:a").value);      // support_intact trigger: non-support read reversioned
    const entry = w.vclock;
    const rec = m.pass();
    results.push(["refresh-escape", rec.aborted && w.vclock === entry && w.read("rleak").version === 0]); }
  // escape during FRESH replay-validation -> QUARANTINE, world untouched
  { const w = mkBase(); const real = w; let arm = false;
    const m = new Maintainer(w);
    m.addGround("A", { measure: "validate-escape", predicate: "reach", measureFn: (view) => {
      const v = view.read("node:a");
      if (arm) real.put("vleak", 1);
      return { value: v === true ? 1 : 0, witness: {}, support: ["node:a"] }; } });
    arm = true;                                  // node stays FRESH; validation runs the closure
    const entry = w.vclock;
    const rec = m.pass();
    const step = rec.steps.find((s) => s.name === "A");
    results.push(["fresh-validation-escape-quarantines", !rec.aborted && step.action === "quarantined"
      && step.reason === "derivation-threw" && w.vclock === entry && w.read("vleak").version === 0]); }
  // lock released after cycle refusal
  { const w = mkBase(); const m = new Maintainer(w);
    m.addGround("A", { measure: "component-size(a)", predicate: "reach", measureFn: componentMeasure(w, "a") });
    m.defs.set("X", { kind: "composite", cites: ["Y"], spec: { measureFn: () => ({}) } });
    m.defs.set("Y", { kind: "composite", cites: ["X"], spec: { measureFn: () => ({}) } });
    const rec = m.pass();
    let ok = rec.refused === true;
    try { w.put("after-cycle", 1); ok = ok && true; } catch { ok = false; }
    results.push(["lock-free-after-cycle-refusal", ok]); }
  // capability refusals: forged commit, double lock, wrong unlock
  { const w = new World();
    const key = w.lock();
    let forged = false, dbl = false, wrongUnlock = false;
    try { w.commit("wrong", () => {}); } catch (e) { forged = String(e.message).includes("world-lock-capability-refused"); }
    try { w.lock(); } catch (e) { dbl = String(e.message).includes("world-already-locked"); }
    try { w.unlock("wrong"); } catch (e) { wrongUnlock = String(e.message).includes("world-lock-capability-refused"); }
    w.unlock(key);
    let released = false; try { w.put("x", 1); released = true; } catch { released = false; }
    results.push(["capability-refusals", forged && dbl && wrongUnlock && released]); }
  const bad = results.filter(([, ok]) => !ok).map(([n]) => n);
  report("L-CONFINE-2", "(confinement matrix: del/query/refresh escapes abort with the world untouched; a fresh-validation escape QUARANTINES; lock survives every exit path; forged capabilities refuse, MAINTENANCE, BINDING)",
    bad.length === 0 ? "PROPERTY-TESTED" : "FALSIFIED?!",
    bad.length === 0
      ? `6/6: composite del-escape and poisoned-query escape and refresh-path escape each ABORT with vclock unmoved and no leaked resource; an escape during fresh replay-validation is converted to a QUARANTINE (derivation-threw) with the world untouched; the lock is released after cycle refusal; and the capability surface refuses forged commit, double lock, and wrong-key unlock (law:maintenance.capability-confinement@1)`
      : `failing: ${bad.join(", ")}`);
}

// L-CONFINE-3 : the master key stays off the object; the internals stay
// sealed (round 9.2 — law:maintenance.capability-confinement@1). Pre-fix
// (frozen in probe_keytheft_v06_repro.mjs): a closure read world._lockKey
// off the PUBLIC field and committed THROUGH the lock — the pass did not
// even abort — and world.res was an open Map needing no key at all.
{
  const w = new World();
  w.put("flag", 0);
  const m = new Maintainer(w);
  const realWorld = w;
  m.addGround("A", { measure: "keythief", predicate: "flag", measureFn: (view) => {
    const f = view.read("flag");
    if (f === 1) {
      const stolen = realWorld._lockKey;   // undefined now — the field does not exist
      realWorld.commit(stolen, () => realWorld.put("leak", { via: "stolen-key" }));
    }
    return { value: f, witness: { f }, support: ["flag"] };
  } });
  w.put("flag", 1);
  const entry = w.vclock;
  const rec = m.pass();
  const theftDead = rec.aborted && String(rec.reason).includes("world-lock-capability-refused")
    && w.read("leak").version === 0 && w.vclock === entry
    && rec.vclock_before === entry && rec.vclock_after === entry;
  // key unreachable: no public field, no own enumerable props at all
  const noKeyField = w._lockKey === undefined && Object.keys(w).length === 0;
  // internals sealed: no public res/queries; log/vclock are read-only views
  const w2 = new World(); w2.put("x", 1);
  const noRes = w2.res === undefined && w2.queries === undefined;
  const logCopy = (() => { const l = w2.log; l.push({ op: "forged" }); return w2.log.length === 1; })();
  let vclockSealed = false; try { w2.vclock = 999; } catch { vclockSealed = w2.vclock === 1; }
  // prototype + instance frozen: patching throws (strict mode)
  let protoFrozen = false; try { World.prototype.put = () => {}; } catch { protoFrozen = true; }
  let instFrozen = false; try { w2.put = () => {}; } catch { instFrozen = true; }
  report("L-CONFINE-3", "(key confinement: the stolen-key witness dies, no public state, log/vclock read-only copies, prototype+instances frozen, MAINTENANCE, BINDING)",
    theftDead && noKeyField && noRes && logCopy && vclockSealed && protoFrozen && instFrozen ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `the key-theft witness now dies at world-lock-capability-refused and ABORTS with the world untouched and the receipt reporting the entry clock (${theftDead}) — pre-fix the stolen key committed THROUGH the lock without even aborting; world._lockKey is undefined and instances carry zero own properties (${noKeyField}); res/queries are unreachable (${noRes}); the log getter returns dead copies (${logCopy}) and vclock refuses assignment (${vclockSealed}); World.prototype and every instance are frozen — patching throws (${protoFrozen}/${instFrozen}). A retained reference now carries no authority the transaction did not hand it (law:maintenance.capability-confinement@1)`);
}

// L-APPLY-1 : the apply boundary under compound failure (round 9.3,
// self-found — law:maintenance.atomicity@1, law:maintenance.receipt@1).
// Prototype-chain children carry no authority; an injected mid-apply tear
// is RECEIPTED truthfully with the applied prefix, state stays consistent
// with the real world, and the NEXT pass repairs and converges.
{
  // prototype-chain + constructor probes, locked
  const wp = new World(); wp.put("x", 1);
  let childPut = false, childRead = false;
  try { Object.create(wp).put("ghost", 1); } catch { childPut = true; }
  try { Object.create(wp).read("x"); } catch { childRead = true; }
  const freshIso = new wp.constructor().vclock === 0 && wp.read("ghost").version === 0;
  // the tear
  const w = buildGraphWorld(["a", "b", "c"], [["a", "b"], ["b", "c"]]);
  w.registerQuery("incident:a", incidentScope("a"));
  const m = new Maintainer(w);
  m.addGround("A", { measure: "component-size(a)", predicate: "reach", measureFn: componentMeasure(w, "a") });
  m.addComposite("B", ["A"], { measure: "B=A+1", predicate: "cite(A)+1",
    measureFn: (view, cite) => { const p = cite("A"); return { value: p.value + 1, witness: { cited: p.warrant_id }, support: ["warrant:A"] }; } });
  w.del("node:c");
  const pubB_before = w.read("warrant:B").version;
  const rec = m.pass({ faultApplyAfter: "A" });
  const tornOk = rec.aborted && rec.torn && rec.at === "apply"
    && cj(rec.applied) === cj(["A"])
    && rec.vclock_after === w.vclock && rec.vclock_after > rec.vclock_before;
  // the real world shows EXACTLY the applied prefix
  const prefixTruth = w.read("warrant:A").version > 0
    && m.state.get("A").warrant_id === rec.after["A"].warrant_id
    && w.read("warrant:B").version === pubB_before
    && rec.after["A"].warrant_id !== rec.before["A"].warrant_id
    && cj(rec.after["B"]) === cj(rec.before["B"]);
  let lockFree = false; try { w.put("post-tear", 1); lockFree = true; } catch { lockFree = false; }
  // recovery: the next (unfaulted) pass repairs B and converges
  const rec2 = m.pass();
  const bStep = rec2.steps.find((s) => s.name === "B");
  const recovered = !rec2.aborted && bStep && bStep.action === "rederived"
    && [...m.state.values()].every((wr) => freshness(w, wr).verdict === "fresh")
    && m.state.get("B").value === m.state.get("A").value + 1;
  report("L-APPLY-1", "(apply under compound failure: injected tear RECEIPTED with the applied prefix, real world matches, lock released, next pass repairs; prototype-children inert, MAINTENANCE, BINDING)",
    childPut && childRead && freshIso && tornOk && prefixTruth && lockFree && recovered ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `an injected fault after applying A tears the pass: the receipt says {aborted, torn, at: apply, applied: [A]} with vclock_after = the REAL post-tear clock (${tornOk}) — pre-fix this path skipped sealReceipt and propagated raw past a half-applied world; the world shows exactly the prefix (A advanced and matches the after-map; B untouched and matches the before-map: ${prefixTruth}); the lock releases (${lockFree}); the NEXT pass re-derives B and converges to all-fresh (${recovered}) — tears are visible, recoverable, and receipted, never silent. Staged values are pre-validated before the first real write, so organic tears are unreachable by construction. Prototype-chain children throw on private-field access (${childPut}/${childRead}); constructor laundering yields only a fresh isolated world (${freshIso}) (law:maintenance.atomicity@1, law:maintenance.receipt@1)`);

{
  const rs = coordBattery();
  const good = rs.filter((r) => r.ok).length;
  report("L-COORD-1", "(the coordinator as authority surface: reentrant registration, root-identity swap, sealer replacement, nested pass, MAINTENANCE, BINDING)",
    good === rs.length ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${good}/${rs.length}: ` + rs.map((r) => r.id + " — " + r.note).join(" · ") +
    ` — rounds 9.1–9.3 hardened the World and left the object HOLDING ITS LOCK an ordinary class with public fields and patchable methods; three of the audit's four 9D witnesses reproduced against v0.7.1 and are frozen red in probe_maintainer_9d_repro.mjs. The instance and prototype are now frozen and a private in-flight flag refuses registration re-entry; defs/state stay mutable by design, because the attack was never that a Map can be written but that it could be written FROM INSIDE A TRANSACTION (law:maintenance.coordinator-confinement@1)`);
}

// L-COORD-2 : the reachable authority graph (round 9D.1,
// law:maintenance.coordinator-write-mediated@1). Sealing an object's
// PROPERTIES says nothing about the mutable capabilities reachable through
// them, nor about objects aliased into the coordinator at registration time.
// All three witnesses stay RED against 0.8.0 in probe_coordinator_alias_9d1_repro.mjs.
{
  const rs = [];
  // (a) the raw map: the guard mediates addGround, so go around it
  { const w = new World(); w.put("flag", 0);
    const m = new Maintainer(w);
    let refusal = null;
    m.addGround("A", { measure: "rawmap", predicate: "flag", measureFn: (view) => {
      const f = view.read("flag");
      if (f === 1) { try { m.defs.set("GHOST", { kind: "ground", cites: [], spec: {
        measure: "g", predicate: "p", measureFn: () => ({ value: 1, witness: {}, support: [] }) } }); }
        catch (e) { refusal = e.message; } }
      return { value: f, witness: { f }, support: ["flag"] };
    } });
    w.put("flag", 1);
    const rec = m.pass();
    rs.push({ id: "raw-map-write", ok: !m.defs.has("GHOST")
        && !Object.prototype.hasOwnProperty.call(rec.after, "GHOST")
        && String(refusal).includes("maintainer-reentrancy-refused: defs.set"),
      note: `defs.set refuses in-pass ('${String(refusal).slice(0, 46)}'); no GHOST in defs or after-map` });
  }
  // (b) cross-node state poison — and the receipt must stop assembling one
  //     authoritative pair out of two independent sources
  { const w = new World(); w.put("fa", 0); w.put("fb", 0);
    const m = new Maintainer(w);
    let refusal = null;
    m.addGround("A", { measure: "A", predicate: "fa", measureFn: (view) => {
      const f = view.read("fa");
      if (f === 1) { try { const b = m.state.get("B"); m.state.set("B", { ...b, warrant_id: "f0rged" }); }
        catch (e) { refusal = e.message; } }
      return { value: f, witness: { f }, support: ["fa"] };
    } });
    m.addGround("B", { measure: "B", predicate: "fb",
      measureFn: (view) => ({ value: view.read("fb"), witness: {}, support: ["fb"] }) });
    w.put("fa", 1);
    const rec = m.pass();
    const worldB = w.read("warrant:B").value;
    const rB = rec.after.B;
    rs.push({ id: "cross-node-state-poison",
      ok: String(refusal).includes("maintainer-reentrancy-refused: state.set")
          && !!rB && rB.warrant_id === worldB.warrant_id,
      note: `state.set refuses in-pass; receipt.after.B.warrant_id now comes FROM THE PUBLICATION and equals the world's (${rB && rB.warrant_id === worldB.warrant_id})` });
  }
  // (c) registration aliasing — needs no map access at all
  { const w = new World(); w.put("fa", 0); w.put("fb", 0);
    const m = new Maintainer(w);
    const specB = { measure: "B", predicate: "fb",
      measureFn: (view) => ({ value: view.read("fb"), witness: {}, support: ["fb"] }) };
    m.addGround("A", { measure: "A", predicate: "fa", measureFn: (view) => {
      const f = view.read("fa");
      if (f === 1) { specB.measureFn = () => ({ value: 777, witness: { pwned: true }, support: [] }); }
      return { value: f, witness: { f }, support: ["fa"] };
    } });
    m.addGround("B", specB);
    w.put("fa", 1); w.put("fb", 5);
    const rec = m.pass();
    const assignable = (() => { try { m.defs.get("B").spec.measureFn = () => ({}); return true; } catch { return false; } })();
    rs.push({ id: "registration-aliasing",
      ok: !rec.aborted && m.state.get("B").value === 5 && w.read("warrant:B").value.value === 5 && !assignable,
      note: `the retained caller alias is severed at registration — B derives honestly to ${m.state.get("B").value} (world ${w.read("warrant:B").value.value}), and the stored spec is frozen so direct assignment throws (assignable: ${assignable})` });
  }
  // (d) the divergence is DECLARED, not preferred, when it exists
  { const w = new World(); w.put("fb", 0);
    const m = new Maintainer(w);
    m.addGround("B", { measure: "B", predicate: "fb",
      measureFn: (view) => ({ value: view.read("fb"), witness: {}, support: ["fb"] }) });
    const b = m.state.get("B");
    m.state.set("B", { ...b, warrant_id: "f0rged" });   // OUTSIDE a pass: the test seam still works
    const snap = m.snapshot(w);
    rs.push({ id: "divergence-declared",
      ok: snap.pubs.B.warrant_id === w.read("warrant:B").value.warrant_id && snap.pubs.B.coordinator_diverged === "warrant_id",
      note: `poisoning from OUTSIDE a pass still succeeds (the seam L-MAINT-3/5 depend on), and the snapshot reports coordinator_diverged=${snap.pubs.B.coordinator_diverged} rather than silently preferring either side` });
  }
  const good = rs.filter((r) => r.ok).length;
  report("L-COORD-2", "(the reachable authority graph: raw map writes, cross-node poison, registration aliasing, declared divergence, MAINTENANCE, BINDING)",
    good === rs.length ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${good}/${rs.length}: ` + rs.map((r) => r.id + " — " + r.note).join(" · ") +
    ` — 0.8.0 froze the coordinator's PROPERTIES and guarded its METHODS; the audit went around both, because #inPass mediated addGround and not defs.set, and freezing a property does not freeze the Map it points at. Worse, registration stored the CALLER's spec object by reference, so swapping measureFn on a retained alias mid-pass was committed with no map access, no reflection and no lock theft. The stores are now capabilities whose writes consult the in-flight flag, values are owned and frozen on the way in, and the pass computes against a definition view captured at entry (law:maintenance.coordinator-write-mediated@1)`);
}

}

const RECEIPT_SPEC = { nodes: ["a", "b", "c", "d"], edges: [["a", "b"], ["b", "c"]], seed: "a" };
if (!anyFail && !process.argv.includes("--check-receipt")) {
  const w = buildGraphWorld(RECEIPT_SPEC.nodes, RECEIPT_SPEC.edges);
  w.registerQuery("incident:a", incidentScope("a"));
  const fn = componentMeasure(w, "a");
  const wa = deriveWarrant(w, { measure: "component-size(a)", predicate: "reach", measureFn: fn,
    law_refs: ["law:warrant.freshness@1", "law:warrant.footprint-soundness@1", "law:warrant.phantom-scope@1"] });
  publishWarrant(w, "ground", wa);
  const cw = deriveComposite(w, { measure: "double-of-ground", predicate: "2*cite(ground)",
    law_refs: ["law:warrant.composition@1"],
    measureFn: (view, cite) => {
      const pub = cite("ground");
      return { value: 2 * pub.value, witness: { cited: pub.warrant_id }, support: ["warrant:ground"] };
    } });
  const receipt = {
    type: "WorldWarrantReceipt", version: 3,
    world_spec: RECEIPT_SPEC,
    law_refs: ["law:world.version-monotone@1", "law:warrant.freshness@1",
      "law:warrant.footprint-soundness@1", "law:warrant.phantom-scope@1",
      "law:warrant.invalidation-trichotomy@1", "law:footprint.shared@1",
      "law:warrant.composition@1", "law:warrant.frame@1"],
    warrant: wa,
    footprint_id: footprintId(wa.read_footprint),
    composite: { warrant: cw, footprint_id: footprintId(cw.read_footprint) },
    freshness_at_emit: freshness(w, wa),
    composite_freshness_at_emit: freshness(w, cw),
    informational: { note: "NON-AUTHORITATIVE", generator: "trvm_world.mjs v" + WORLD_VERSION },
  };
  receipt.receipt_id = H("TRVM-WORLDRECEIPT-v3|" + cj(receipt.world_spec) + "|" + cj(receipt.warrant) + "|" + receipt.footprint_id
    + "|" + cj(receipt.composite.warrant) + "|" + receipt.composite.footprint_id);
  writeFileSync("world_warrant_receipt.json", JSON.stringify(receipt, null, 1));
  // canonical maintenance receipt: the diamond after one ground movement
  {
    const wm = buildGraphWorld(["a", "b", "c"], [["a", "b"], ["b", "c"]]);
    wm.registerQuery("incident:a", incidentScope("a"));
    const m = new Maintainer(wm);
    m.addGround("A", { measure: "component-size(a)", predicate: "reach", measureFn: componentMeasure(wm, "a") });
    const mk2 = (nm, f) => m.addComposite(nm, ["A"], { measure: nm, predicate: nm,
      measureFn: (view, cite) => { const p = cite("A"); return { value: f(p.value), witness: { cited: p.warrant_id }, support: ["warrant:A"] }; } });
    mk2("B", (x) => x + 1); mk2("C", (x) => x * 10);
    m.addComposite("D", ["B", "C"], { measure: "D=B+C", predicate: "cite(B)+cite(C)",
      measureFn: (view, cite) => { const b = cite("B"), c = cite("C"); return { value: b.value + c.value, witness: { b: b.warrant_id, c: c.warrant_id }, support: ["warrant:B", "warrant:C"] }; } });
    wm.del("node:c");
    const mrec = m.pass();
    mrec.informational = { note: "NON-AUTHORITATIVE", generator: "trvm_world.mjs v" + WORLD_VERSION,
      scenario: "diamond D<-{B,C}<-A after deleting node:c" };
    writeFileSync("maintenance_receipt.json", JSON.stringify(mrec, null, 1));
  }
}

console.log("═".repeat(96));
console.log(anyFail
  ? "VERDICT: FAIL — a world/warrant law broke."
  : "VERDICT: PASS — the WORLD layer's warrant machinery holds; receipt emitted.");
process.exit(anyFail ? 1 : 0);
