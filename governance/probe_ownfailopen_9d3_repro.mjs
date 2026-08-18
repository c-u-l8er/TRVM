/* ═══════════════════════════════════════════════════════════════════════════
   trvm_world.mjs — v0.10.0 — the WORLD layer: WorldRecord + Warrant v3,
   executable. The calculus kernel (trvm_law_kernel.mjs, frozen at v1.0.1)
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
const WORLD_VERSION = "0.10.0";

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
const ownValue = (v) => {
  if (v === null || typeof v !== "object") return v;
  try { return deepFreeze(JSON.parse(canonicalBytes(v))); }
  catch { try { return deepFreeze(structuredClone(v)); } catch { return v; } }
};

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
    inputs: ownValue(sp.inputs ?? null),
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
    value: ownValue(w.value),           // v0.10.0: transitive, not shallow
    witness: ownValue(w.witness),
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

// ═══════════════════════════════════════════════════════════════════════════
// AUDIT-9D.3 — ownership that fails OPEN
// ownValue ends in `catch { return v; }`. An ownership boundary that cannot own
// an object must REFUSE it, never hand back the caller's reference.
// Run: node probe_ownfailopen_9d3_repro.mjs
// ═══════════════════════════════════════════════════════════════════════════
const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(`${id.padEnd(30)} ${held ? "CONFINED" : "*** BREACH ***"}  ${note}`); };
console.log("AUDIT-9D.3 — against World " + WORLD_VERSION);
console.log("=".repeat(100));

// (a) both mechanisms reject → the caller's object comes straight back
{
  const w = new World(); w.put("fb", 1);
  const m = new Maintainer(w);
  const externalWitness = { evidence: 1, helper() {} };
  let ok = true, stored = null;
  try {
    m.addGround("B", { measure: "B", predicate: "fb",
      measureFn: () => ({ value: 1, witness: externalWitness, support: ["fb"] }) });
    stored = m.state.get("B").witness;
    externalWitness.evidence = 999;
    ok = stored !== externalWitness && Object.isFrozen(stored);
  } catch (e) { ok = String(e.message).includes("not-canonical"); stored = "REFUSED: " + String(e.message).slice(0, 40); }
  R("9D.3-a witness-fail-open", ok,
    typeof stored === "string" ? stored
      : `stored === caller object: ${stored === externalWitness} | isFrozen: ${Object.isFrozen(stored)}` +
        ` | caller wrote 999, stored now reads: ${stored && stored.evidence}`);
}

// (b) Map: structuredClone SUCCEEDS, freeze does not reach entries, and
//     JSON.stringify collapses it to {} so warrant identity cannot see it
{
  const w = new World(); w.put("fb", 1);
  const m = new Maintainer(w);
  let ok = true, note = "";
  try {
    m.addGround("B", { measure: "B", predicate: "fb",
      measureFn: () => ({ value: 1, witness: new Map([["evidence", 1]]), support: ["fb"] }) });
    const wit = m.state.get("B").witness;
    const before = m.state.get("B").warrant_id;
    let mutated = false;
    try { wit.set("evidence", 999); mutated = true; } catch { mutated = false; }
    ok = !mutated;
    note = `witness instanceof Map: ${wit instanceof Map} | isFrozen(wrapper): ${Object.isFrozen(wit)}` +
      ` | .set() succeeds: ${mutated} | JSON.stringify(Map) = ${JSON.stringify(wit)}` +
      ` | warrant_id unchanged: ${before === m.state.get("B").warrant_id} — the OWNERSHIP domain and the IDENTITY domain disagree about what a value is`;
  } catch (e) { ok = String(e.message).includes("not-canonical"); note = "REFUSED: " + String(e.message).slice(0, 46); }
  R("9D.3-b map-witness", ok, note);
}

// (c) the registration-alias species returns through spec.inputs
{
  const w = new World(); w.put("fa", 0); w.put("fb", 0);
  const m = new Maintainer(w);
  const inputsB = { x: 1, helper() {} };
  let ok = true, note = "";
  try {
    m.addGround("A", { measure: "A", predicate: "fa", measureFn: (view) => {
      const f = view.read("fa");
      if (f === 1) { inputsB.x = 999; }
      return { value: f, witness: { f }, support: ["fa"] };
    } });
    m.addGround("B", { measure: "B", predicate: "fb", inputs: inputsB,
      measureFn: (view) => ({ value: view.read("fb"), witness: {}, support: ["fb"] }) });
    const storedInputs = m.defs.get("B").spec.inputs;
    const idBefore = m.state.get("B").derivation_id;
    w.put("fa", 1); w.put("fb", 5);
    const rec = m.pass();
    const stepB = (rec.steps || []).find((s) => s.name === "B");
    ok = storedInputs !== inputsB;
    note = `stored inputs === caller inputs: ${storedInputs === inputsB} | after the pass stored.x = ${storedInputs && storedInputs.x}` +
      ` | derivation_id changed: ${idBefore !== m.state.get("B").derivation_id} | B action: ${stepB && stepB.action}`;
  } catch (e) { ok = String(e.message).includes("not-canonical"); note = "REFUSED: " + String(e.message).slice(0, 46); }
  R("9D.3-c inputs-fail-open", ok, note);
}

console.log("=".repeat(100));
const breaches = results.filter((r) => !r.held);
console.log(`AUDIT-9D.3: ${results.length - breaches.length}/${results.length} confined` +
  (breaches.length ? ` — ${breaches.length} BREACH: ${breaches.map((b) => b.id).join(", ")}` : ""));
process.exit(breaches.length ? 1 : 0);
