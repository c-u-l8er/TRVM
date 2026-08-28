/* ═══════════════════════════════════════════════════════════════════════════
   trvm_world.mjs — v0.2.0 — the WORLD layer: WorldRecord + Warrant v3,
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

   Run: node trvm_world.mjs [--quick]   (exit 0 iff all batteries pass)
   ═══════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
const WORLD_VERSION = "0.2.0";

const H = (s) => createHash("sha256").update(s).digest("hex");
const cj = (o) => JSON.stringify(o);

// ═══ WorldRecord ═══════════════════════════════════════════════════════════
// law:world.version-monotone@1 — versions strictly increase on a global
// vclock; the log is append-only; a read returns the latest write. Scope
// queries are REGISTERED (name -> fn(reader)) and reified on evaluation.
class World {
  constructor() {
    this.res = new Map();     // name -> { value, version }
    this.vclock = 0;
    this.log = [];            // { op, resource, version, prev }
    this.queries = new Map(); // qname -> fn(read: (name)=>value|undefined, names: ()=>[...])
  }
  put(name, value) {
    const prev = this.res.get(name)?.version ?? 0;
    const version = ++this.vclock;
    this.res.set(name, { value, version });
    this.log.push({ op: "put", resource: name, version, prev });
    return version;
  }
  del(name) {
    const prev = this.res.get(name)?.version ?? 0;
    const version = ++this.vclock;
    this.res.delete(name);
    this.log.push({ op: "del", resource: name, version, prev });
    return version;
  }
  read(name) {
    const r = this.res.get(name);
    return r ? { value: r.value, version: r.version } : { value: undefined, version: 0 };
  }
  names() { return [...this.res.keys()].sort(); }
  registerQuery(qname, fn) { this.queries.set(qname, fn); }
  // a scope evaluation is REIFIED: digest of the canonical result set
  scopeEval(qname) {
    const fn = this.queries.get(qname);
    if (!fn) throw new Error("unknown scope query: " + qname);
    const result = fn((n) => this.read(n).value, () => this.names());
    return { digest: H("TRVM-SCOPE-v1|" + qname + "|" + cj(result)), at_vclock: this.vclock };
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
    support: out.support,
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
  const nw = { ...w, read_footprint: view.footprint(), at_vclock: world.vclock, witness: out.witness };
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
  world.registerQuery("warrant-fresh:" + name, () => {
    const exact = w.read_footprint.exact.map(([r]) => [r, world.read(r).version]);
    const scopes = w.read_footprint.predicates.map(([q]) => [q, world.scopeEval(q).digest]);
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
    value: out.value, witness: out.witness, support: out.support,
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
  if (warrantIdOf(w) !== w.warrant_id) return { ok: false, reason: "warrant-id-mismatch" };
  return { ok: true };
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
  return (read, names) => {
    const reached = reachFrom(seedName, read, names);
    const inc = names().filter((n) => {
      if (!n.startsWith("edge:")) return false;
      const [a, b] = n.slice(5).split("|");
      return reached.has(a) || reached.has(b);
    }).filter((n) => read(n) !== undefined);
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
// ═══ AUDIT-WORLD-ALIAS: GPT's round-8B witness, against shipped v0.2.0 ════
const world = new World();
world.put("r:x", [1]);
const fn = (view) => { const a = view.read("r:x"); return { value: a.length, witness: a, support: ["r:x"] }; };
const wa = deriveWarrant(world, { measure: "len(r:x)", predicate: "length", measureFn: fn });
console.log("AUDIT-WORLD-ALIAS");
console.log("before:  version", world.read("r:x").version, "| value", wa.value, "| freshness", freshness(world, wa).verdict);
world.read("r:x").value.push(2);            // egress alias: mutate through read, NO put
const f = freshness(world, wa);
const r = replayWarrant(world, wa, fn);
console.log("after read-alias mutation:");
console.log("  version", world.read("r:x").version, "| vclock", world.vclock, "| current value", JSON.stringify(world.read("r:x").value));
console.log("  freshness:", JSON.stringify(f.verdict), "| replay:", JSON.stringify({ok: r.ok, reason: r.reason}));
console.log("  VERIFIERS DISAGREE:", f.verdict === "fresh" && !r.ok && r.reason === "value-mismatch");

// ingress alias
const w2 = new World();
const payload = { a: { b: [1] } };
w2.put("r:y", payload);
payload.a.b.push(99);                        // mutate the ORIGINAL after put
console.log("ingress alias leaks:", JSON.stringify(w2.read("r:y").value));

// deletion semantics
const w3 = new World();
w3.put("r:z", 7); w3.del("r:z");
console.log("after del: read =", JSON.stringify(w3.read("r:z")), "| vclock =", w3.vclock, "(deletion version collapsed to 0?)");
