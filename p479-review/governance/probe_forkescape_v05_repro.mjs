/* ═══════════════════════════════════════════════════════════════════════════
   trvm_world.mjs — v0.5.0 — the WORLD layer: WorldRecord + Warrant v3,
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

   Run: node trvm_world.mjs [--quick|--check-receipt]  (exit 0 iff green)
   ═══════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
const WORLD_VERSION = "0.5.0";

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
  constructor() {
    this.res = new Map();     // name -> { bytes, hash, version, deleted }
    this.vclock = 0;
    this.log = [];            // { op, resource, version, prev, hash? }
    this.queries = new Map(); // qname -> fn(read: (name)=>value|undefined, names: ()=>[...])
  }
  put(name, value) {
    const bytes = canonicalBytes(value);            // refuses non-canonical; severs ingress aliases
    const hash = valueHashOf(bytes);
    const prev = this.res.get(name)?.version ?? 0;
    const version = ++this.vclock;
    this.res.set(name, { bytes, hash, version, deleted: false });
    this.log.push({ op: "put", resource: name, version, prev, hash });
    return version;
  }
  del(name) {
    const prev = this.res.get(name)?.version ?? 0;
    const version = ++this.vclock;
    this.res.set(name, { bytes: null, hash: null, version, deleted: true }); // TOMBSTONE:
    this.log.push({ op: "del", resource: name, version, prev });             // deleted != never-existed
    return version;
  }
  read(name) {
    const r = this.res.get(name);
    if (!r) return { value: undefined, version: 0 };
    if (r.deleted) return { value: undefined, version: r.version, deleted: true };
    return { value: JSON.parse(r.bytes), version: r.version };  // fresh copy: egress aliases sever here
  }
  valueHash(name) { const r = this.res.get(name); return r && !r.deleted ? r.hash : null; }
  exists(name) { const r = this.res.get(name); return !!r && !r.deleted; }
  names() { return [...this.res.entries()].filter(([, r]) => !r.deleted).map(([n]) => n).sort(); }
  registerQuery(qname, fn) { this.queries.set(qname, fn); }
  // a scope evaluation is REIFIED: digest of the canonical result set. The
  // query fn reads ONLY through the passed interface — never a captured
  // world reference — so queries survive World.fork() (round 9: the
  // maintenance pass runs on a fork and commits atomically).
  scopeEval(qname) {
    const fn = this.queries.get(qname);
    if (!fn) throw new Error("unknown scope query: " + qname);
    const iface = {
      value: (n) => this.read(n).value,
      version: (n) => this.read(n).version,
      names: () => this.names(),
      scope: (q) => this.scopeEval(q).digest,
    };
    const result = fn(iface);
    return { digest: H("TRVM-SCOPE-v1|" + qname + "|" + cj(result)), at_vclock: this.vclock };
  }
  // fork: an isolated copy sharing nothing mutable. Entries are frozen
  // byte-records; query fns are pure over the reader interface.
  fork() {
    const f = new World();
    for (const [n, e] of this.res) f.res.set(n, { ...e });
    f.vclock = this.vclock;
    f.log = [...this.log];
    f.queries = new Map(this.queries);
    return f;
  }
}

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
class Maintainer {
  constructor(world) {
    this.world = world;
    this.defs = new Map();   // name -> {kind, cites, spec}
    this.state = new Map();  // name -> current warrant
  }
  mfnOf(def) {
    if (def.kind === "ground") return def.spec.measureFn;
    return (view) => def.spec.measureFn(view, (n) => {
      view.scope("warrant-fresh:" + n); return view.read("warrant:" + n);
    });
  }
  addGround(name, spec) {
    if (this.defs.has(name)) throw new Error("maintainer: duplicate " + name);
    this.defs.set(name, { kind: "ground", cites: [], spec });
    const w = deriveWarrant(this.world, spec);
    this.state.set(name, w);
    publishWarrant(this.world, name, w);
    return w;
  }
  addComposite(name, cites, spec) {
    if (this.defs.has(name)) throw new Error("maintainer: duplicate " + name);
    for (const c of cites) if (!this.defs.has(c))
      throw new Error("maintenance-cycle-guard: " + name + " cites unknown " + c); // forward refs impossible
    this.defs.set(name, { kind: "composite", cites: [...cites], spec });
    const w = deriveComposite(this.world, spec);
    this.state.set(name, w);
    publishWarrant(this.world, name, w);
    return w;
  }
  register(name, warrant) {   // external ingest: the quarantine door
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
  pass() {
    const t = this.topoOrder();
    const before = this.snapshot(this.world);
    if (t.cycle) return this.sealReceipt({ refused: true, reason: "maintenance-cycle", cycle: t.cycle, before, after: before, steps: [], vb: this.world.vclock, va: this.world.vclock });
    const fork = this.world.fork();
    const staged = new Map(), steps = [];
    try {
      for (const name of t.order) {
        const def = this.defs.get(name);
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
      }
    } catch (e) {
      return this.sealReceipt({ aborted: true, at: e.maintName ?? "unknown", reason: String(e.message).slice(0, 120),
        before, after: before, steps, vb: this.world.vclock, va: this.world.vclock });
    }
    // ATOMIC APPLY: replay the staged publication sequence onto the real world
    for (const s of steps) if (staged.has(s.name)) {
      publishWarrant(this.world, s.name, staged.get(s.name));
      this.state.set(s.name, staged.get(s.name));
    }
    const after = this.snapshot(this.world);
    return this.sealReceipt({ before, after, steps, vb: before.vclock, va: after.vclock });
  }
  snapshot(world) {
    const pubs = {};
    for (const name of [...this.defs.keys()].sort()) {
      pubs[name] = { pub_version: world.read("warrant:" + name).version,
        warrant_id: (this.state.get(name) ?? {}).warrant_id ?? null };
    }
    return { vclock: world.vclock, pubs };
  }
  sealReceipt(r) {
    const receipt = {
      type: "MaintenanceReceipt", version: 1,
      refused: r.refused ?? false, aborted: r.aborted ?? false,
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
// ═══ AUDIT-FORK-ESCAPE: GPT's round-9B witness, against shipped v0.5.0 ════
const w = new World();
w.put("flag", 0);
const m = new Maintainer(w);
const realWorld = w;                                 // the captured authority
m.addGround("A", { measure: "escape", predicate: "flag", measureFn: (view) => {
  const f = view.read("flag");
  if (f === 1) { realWorld.put("leak", { escaped: true }); throw new Error("boom"); }
  return { value: f, witness: { f }, support: ["flag"] };
} });
w.put("flag", 1);                                    // dirty A, arm the bomb
const beforeVclock = w.vclock;
const rec = m.pass();
console.log("AUDIT-FORK-ESCAPE");
console.log("aborted:", rec.aborted, "| at:", rec.at);
console.log("real vclock:", w.vclock, "(pass entry was", beforeVclock + ")");
console.log("leak:", JSON.stringify(w.read("leak")));
console.log("receipt vclock_before:", rec.vclock_before, "| vclock_after:", rec.vclock_after);
console.log("ATOMIC =", w.vclock === beforeVclock && w.read("leak").version === 0);
console.log("RECEIPT TRUTH =", rec.vclock_before === beforeVclock,
  "(the 3->4 transition", rec.vclock_before === beforeVclock ? "is visible" : "was normalized into the alleged pre-state)");
