/* ═══════════════════════════════════════════════════════════════════════════
   trvm_law_kernel.mjs — v1.0.0 — a law-governed Interaction Calculus kernel
   for TRVM whose contribution is GOVERNANCE: the periodic-law grid compiled
   into the runtime's own falsifier — with evidence artifacts whose
   AUTHORITY cannot outrun their evidence, and now a state identity that
   knows WHAT it identifies.

   WHAT v1.0.0 MEANS (and does not)
   ────────────────────────────────
   v1 = the CALCULUS LAYER's law set is complete and closed over its own
   claims: dual state identity (execution + semantic quotient), progress
   under free AND adversarial choice, plane partition, films with
   live-relation enabledness, receipt-based certificates, and the
   allocation-portability bridge that a second implementation (ic32) will
   replay against. WORLD and EFFECT planes, the σ profile, CP5–CP7
   PhaseSpan, and Warrant v3 are TRVM/WRL layers ABOVE this kernel — they
   are named in the grid, and they are the post-v1 roadmap, not debt.

   WHAT CHANGED IN v1.0.0 (round 6 — the identity round)
   ─────────────────────────────────────────────────────
   1. External audit answered the standing Coherence question in the
      NEGATIVE with an executable witness: two behaviorally identical
      states (same enabled rules, same NF ((X Y) (X Y)), same counts)
      whose floatDigests differ under a heap-id swap — reproduced here
      byte-for-byte (18b4e47b… vs 6bca1878…), and extended: a DEAD heap
      entry also perturbs the digest while the live state is untouched.
      Verdict adopted: not a bug in the digest — the wrong QUOTIENT for
      semantic claims. Identity SPLITS (law:state.exec-identity@1,
      law:state.semantic-quotient@1): execStateId (= floatDigest) is
      allocation-sensitive and replay-grade — films and receipts keep it;
      semStateId folds the LIVE heap in first-reachable discovery order
      and inherits the digest's alpha/label equivariance — heap-id
      bijections, dead content, and allocation order all quotient away.
   2. The ic32 bridge exists and is exercised (law:refine.alloc-portability@1):
      an adversarial DESCENDING allocator runs every vector in lockstep
      with the standard one — per-step SEMANTIC chains equal, NFs and
      counts equal, execution identities allocator-bound. A SEMANTIC FILM
      (canonical loci, semantic pre/post ids) built on one allocator
      replays on the other; the execution film does not. A
      RefinementReceipt records the asymmetry per term.
   3. Free choice is now sampled ADVERSARIALLY too: two starvation
      schedulers (starve_dups, starve_apps) join the four free ones —
      144 certified receipts (law:sched.adversarial.float@1).
   4. The executable can no longer disagree with the artifact identity:
      KERNEL_VERSION is a constant, the banner prints it, the source
      header carries it, the certificate's generator cites it, and
      L-ID-1 REGRESSION-LOCKS the agreement (law:kernel.identity@1) —
      the round-6 audit caught a v0.6 source printing a v0.5 banner.

   CARRIED FROM v0.6 (round 5 — the evidence-binding round)
   ──────────────────────────────────────────────────────────
   1. External audit FORGED the certificate. All 10 single-field mutations
      (representation, quiescence criterion, strategy, budget, evidence
      inflation to 999,999 runs, claims erased, law refs erased, corpus id,
      ALL exhibits erased, plane profile broadened with a fake rule) were
      ACCEPTED by checkSchedulerCertificate v1, and a hollow zero-exhibit
      certificate ALSO passed grid_check — an assurance COMPOSITION bug: two
      checkers each verified fragments and their union still did not verify
      the substantive claim. Verified here by probe before the fix (10/10 +
      hollow). SchedulerCertificate v2 (law:sched.certificate@2) answers with
      a field discipline (law:cert.field-discipline@1): every field is
      DERIVED (checker recomputes it), COMMITTED (inside cert_id; silent
      edits break the commitment, laundered edits must survive semantic
      re-derivation), or INFORMATIONAL (declared non-authoritative, outside
      cert_id, forbidden from supporting law claims). The EVIDENCE BASIS is a
      RUN MANIFEST — one receipt per run, every receipt re-EXECUTED
      deterministically by the checker — exhibits are demoted to witnesses.
      "96/96" is now a derived property of receipts, never trusted JSON.
   2. Film replay gains ENABLEDNESS (law:film.evidence-chain@5, superseding
      @4): round-5 probes built digest-consistent, honestly-committed films
      that fired DEAD heap loci — transitions mechanically firable but
      OUTSIDE the live relation the film claims to witness — and v0.5 replay
      accepted them (227 adversarial prefer-dead runs). Replay now re-derives
      per-frame membership in the live enumeration under the film's DECLARED
      planes; two new typed refusals (illegal-transition,
      plane-not-permitted) bring the vocabulary to 18. Digest consistency is
      necessary but NOT sufficient.
   3. Round-4's Bug-A diagnosis is REVISED. 400+ dead-firing runs — including
      an exact replication of the pre-fix fuzz stream (176 dead-firing runs)
      — produced ZERO NF divergence: the λa.b corruption round 4 attributed
      to dead-dup "affinity double-consumption" is attributable to the
      READBACK hole (Bug B, residual live dups invisible to bare normalRef).
      Dead enumeration's real harms are ILLEGAL-RELATION transitions and
      quiescence distortion; the live-only relation stands, its evidence
      story corrected. A red row must be diagnosed before it is narrated —
      applied to my own bug narrative this time.

   CARRIED FROM v0.5 (round 4 — the retraction round)
   ─────────────────────────────────────────────────────
   1. L-PROG-1's v0.4 interpretation is RETRACTED. External adversarial review
      claimed — and instrumentation here verified — that the six "progress
      failures" never exhausted the 20k scheduler budget. They reached
      findRedexes()==[] after 15–37 steps (FALSE QUIESCENCE) and the reference
      normalizer then burned its whole 2M budget structurally unfolding a
      cyclic-through-substitution state while firing ~0 interactions. The old
      battery compared two DIFFERENT operational relations. Kept red forever
      as L-FQ-AST-1 (law:sched.free.ast-term@1, FALSIFIED by design).
   2. Root cause is the REPRESENTATION, not (only) plane mixing: even
      pure-INTERACT free ordering knots the same six terms, because positional
      rule output on a body-carrying AST can park a Dup node inside another
      Dup's val slot — a configuration whose readiness cycle the term-level
      enumerator cannot break. The FLOATING-DUP engine below extrudes every
      Dup to a heap: chase(dup.val) can never yield Dup, the knot becomes
      unrepresentable, and — measured, not assumed — 4 schedulers × 24
      vectors complete 24/24 with the reference NF, readback from quiescence
      fires ZERO INTERACT-plane rules (pure collapse, bounded by the
      residual live-dup count), and the interaction count is
      schedule-invariant and EQUAL to the reference count on every term
      (law:sched.free.float@1, law:deriv.count-invariance.float@1).
      Engineering lesson recorded: the enumeration must match the
      representation — heap values are reduction roots too; omitting them
      reproduced a different wait-knot before this shipped.
   3. INTERACT and COLLAPSE are now distinct EXECUTABLE relations
      (law:plane.rule-partition@1). INTERACT: APP-LAM, APP-SUP, APP-ERA,
      DUP-LAM, DUP-SUP=, DUP-SUP!, DUP-ERA. COLLAPSE: DUP-VAR (gated to free
      vars), DUP-APP (gated to genuinely stuck apps) — matching upstream IC,
      where these live under the separate Collapsing extension. Measured
      discovery: the planes compose as an interleaved FIXPOINT, not a
      pipeline — collapse can re-enable interact (1–28 extra INTERACT steps
      on the exp terms after a collapse phase; law:plane.separation.fixpoint@1).
      A certificate must name its plane profile; silent mixing is refused.
   4. FILM v3.1: the terminal record is now INSIDE the commitment. v3 bound
      the chain of transitions but not the claimed outcome — external review
      mutated termination/steps/last_frame on a sealed film and replay still
      said ok. Now film_id = H("TRVM-FILM-v3.1" | last_frame | terminal
      fields), replay re-derives the outcome (terminal-last-frame/steps/state
      checks, false-normal-form detection by re-enumerating the declared
      planes, budget/remaining-work witnesses), and frame.i is DECLARED
      non-authoritative metadata (mutating it must NOT refuse replay).
      law:film.evidence-chain@4 superseded in v0.6 by @5 (enabledness).
   5. A SchedulerCertificate whose v1 checker verified corpus hash, plane
      membership, and exhibit replay — superseded in v0.6 by v2 above
      (law:sched.certificate@1 superseded by @2) after the audit showed
      every other field was unbound.
   6. Evidence vocabulary gains REGRESSION-LOCKED (a specific counterexample
      is closed and locked; weaker than PROPERTY-TESTED). L-ADEQ-1 is
      reclassified to it; L-ADEQ-2 adds the sampled property with the
      SHA-256 collision-resistance assumption stated.

   WHAT THIS STILL IS
   ──────────────────
   A faithful, independent port of the reference semantics (whnf/normalRef,
   the conformance path) plus the small-step engines; the LAW TABLE where
   each law is data compiled into property/exhaustive checks; sealing,
   films, replay with typed refusal; and the discipline that a by-design
   falsification which starts passing FAILS the build, because it means the
   semantics changed. The calculus layer only — WORLD (ADMIT, mailboxes,
   epochs) and EFFECT (seal/revalidate/settle) planes are named in the grid
   and live elsewhere.

   Run:  node trvm_law_kernel.mjs            (laws + conformance + fuzz)
         node trvm_law_kernel.mjs --quick    (smaller trial counts)
   Writes scheduler_certificate.json on a passing L-SCHED-FLOAT battery.
   Exit 0 iff conformance passes, all asserted laws hold, and every
   by-design falsification still fails.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
const KERNEL_VERSION = "1.0.0";

// ── deterministic RNG ──────────────────────────────────────────────────────
function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ── terms ──────────────────────────────────────────────────────────────────
const Var = (nam) => ({ t: "Var", nam });
const Era = () => ({ t: "Era" });
const Lam = (nam, bod) => ({ t: "Lam", nam, bod });
const App = (fun, arg) => ({ t: "App", fun, arg });
const Sup = (lab, lft, rgt) => ({ t: "Sup", lab, lft, rgt });
const Dup = (lab, lft, rgt, val, bod) => ({ t: "Dup", lab, lft, rgt, val, bod });
const isFree = (nam) => typeof nam === "string" && nam.startsWith("free:");

// ── runtime: global-but-encapsulated affine substitution store ─────────────
class Rt {
  constructor() {
    this.sub = new Map();       // name(int) -> term   WRITE-ONCE (checked)
    this.subWrites = 0;         // monotone counter
    this.overwrites = 0;        // MUST stay 0 — single-assignment law
    this.fresh_ = 0;
    this.ctr = new Map();       // rule -> count
  }
  fresh() { return ++this.fresh_; }
  bump(rule) { this.ctr.set(rule, (this.ctr.get(rule) ?? 0) + 1); }
  setSub(nam, term) {
    if (this.sub.has(nam)) this.overwrites++;      // never happens if affine
    this.sub.set(nam, term); this.subWrites++;
  }
  total() { let s = 0; for (const v of this.ctr.values()) s += v; return s; }
}

// ── the eight rules (verbatim semantics from ic_ref.py) ───────────────────
function app_lam(rt, app, lam) { rt.bump("APP-LAM"); rt.setSub(lam.nam, app.arg); return lam.bod; }
function app_sup(rt, app, sup) {
  rt.bump("APP-SUP");
  const x0 = rt.fresh(), x1 = rt.fresh();
  return Dup(sup.lab, x0, x1, app.arg,
    Sup(sup.lab, App(sup.lft, Var(x0)), App(sup.rgt, Var(x1))));
}
function app_era(rt) { rt.bump("APP-ERA"); return Era(); }
function dup_lam(rt, dup, lam) {
  rt.bump("DUP-LAM");
  const x0 = rt.fresh(), x1 = rt.fresh(), f0 = rt.fresh(), f1 = rt.fresh();
  rt.setSub(dup.lft, Lam(x0, Var(f0)));
  rt.setSub(dup.rgt, Lam(x1, Var(f1)));
  rt.setSub(lam.nam, Sup(dup.lab, Var(x0), Var(x1)));
  return Dup(dup.lab, f0, f1, lam.bod, dup.bod);
}
function dup_sup(rt, dup, sup) {
  if (dup.lab === sup.lab) {
    rt.bump("DUP-SUP=");
    rt.setSub(dup.lft, sup.lft); rt.setSub(dup.rgt, sup.rgt);
    return dup.bod;
  }
  rt.bump("DUP-SUP!");
  const a0 = rt.fresh(), a1 = rt.fresh(), b0 = rt.fresh(), b1 = rt.fresh();
  rt.setSub(dup.lft, Sup(sup.lab, Var(a0), Var(b0)));
  rt.setSub(dup.rgt, Sup(sup.lab, Var(a1), Var(b1)));
  return Dup(dup.lab, a0, a1, sup.lft, Dup(dup.lab, b0, b1, sup.rgt, dup.bod));
}
function dup_era(rt, dup) { rt.bump("DUP-ERA"); rt.setSub(dup.lft, Era()); rt.setSub(dup.rgt, Era()); return dup.bod; }
function dup_var(rt, dup, v) { rt.bump("DUP-VAR"); rt.setSub(dup.lft, v); rt.setSub(dup.rgt, v); return dup.bod; }
function dup_app(rt, dup, app) {
  rt.bump("DUP-APP");
  const f0 = rt.fresh(), f1 = rt.fresh(), x0 = rt.fresh(), x1 = rt.fresh();
  rt.setSub(dup.lft, App(Var(f0), Var(x0)));
  rt.setSub(dup.rgt, App(Var(f1), Var(x1)));
  return Dup(dup.lab, f0, f1, app.fun, Dup(dup.lab, x0, x1, app.arg, dup.bod));
}

// ── reference normal-order driver (conformance path) ──────────────────────
const CHILDREN = { Var: [], Era: [], Lam: ["bod"], App: ["fun", "arg"], Sup: ["lft", "rgt"], Dup: ["val", "bod"] };
function whnf(rt, term, budget) {
  const stack = [];
  outer: for (;;) {
    if (--budget.n <= 0) throw new Error("budget");
    if (term.t === "Var" && !isFree(term.nam) && rt.sub.has(term.nam)) { term = rt.sub.get(term.nam); continue; }
    if (term.t === "App") { stack.push({ k: "app", node: term }); term = term.fun; continue; }
    if (term.t === "Dup") { stack.push({ k: "dup", node: term }); term = term.val; continue; }
    // term is Lam / Sup / Era / free-or-unsubbed Var — combine upward
    while (stack.length) {
      const f = stack.pop();
      if (f.k === "app") {
        if (term.t === "Lam") { term = app_lam(rt, f.node, term); continue outer; }
        if (term.t === "Sup") { term = app_sup(rt, f.node, term); continue outer; }
        if (term.t === "Era") { term = app_era(rt); continue outer; }
        term = App(term, f.node.arg);              // stuck application: keep popping
      } else {
        if (term.t === "Lam") { term = dup_lam(rt, f.node, term); continue outer; }
        if (term.t === "Sup") { term = dup_sup(rt, f.node, term); continue outer; }
        if (term.t === "Era") { term = dup_era(rt, f.node); continue outer; }
        if (term.t === "App") { term = dup_app(rt, f.node, term); continue outer; }
        term = dup_var(rt, f.node, term); continue outer;   // Var (free or never-to-be-bound)
      }
    }
    return term;
  }
}
function normalRef(rt, term, budget = { n: 2_000_000 }) {
  // iterative post-order rebuild; whnf on entry of every node
  const root = { kids: [null] };
  const st = [{ node: whnf(rt, term, budget), parent: root, slot: 0, stage: 0 }];
  while (st.length) {
    const f = st[st.length - 1];
    const n = f.node, keys = CHILDREN[n.t];
    if (f.stage === 0) { f.out = { ...n }; f.kids = keys; f.i = 0; f.stage = 1; }
    if (f.i < f.kids.length) {
      const k = f.kids[f.i++];
      st.push({ node: whnf(rt, n[k], budget), parent: f.out, slot: k, stage: 0 });
    } else {
      st.pop();
      f.parent[f.slot !== undefined ? f.slot : "kids"] = f.out ?? n;
      if (f.parent === root) root.kids[0] = f.out ?? n;
      else f.parent[f.slot] = f.out ?? n;
    }
  }
  return root.kids[0];
}
// ── parser (lexical alpha-renaming to globally unique ints) ───────────────
function parse(rt, txt) {
  let i = 0; const scope = [];
  const ws = () => { while (i < txt.length && " \t\n\r".includes(txt[i])) i++; };
  const peek = () => (ws(), i < txt.length ? txt[i] : "");
  const eat = (c) => { ws(); if (txt[i] !== c) throw new SyntaxError(`expected ${c} at ${i}`); i++; };
  const name = () => {
    ws(); const j = i;
    while (i < txt.length && /[A-Za-z0-9_]/.test(txt[i])) i++;
    if (i === j) throw new SyntaxError(`expected name at ${i}`);
    return txt.slice(j, i);
  };
  const uint = () => { ws(); const j = i; while (i < txt.length && /[0-9]/.test(txt[i])) i++; return i > j ? parseInt(txt.slice(j, i)) : 0; };
  const lookup = (src) => { for (let k = scope.length - 1; k >= 0; k--) if (src in scope[k]) return scope[k][src]; return null; };
  function term() {
    const c = peek();
    if (c === "λ" || c === "\\") {
      i++; const src = name(); eat(".");
      const u = rt.fresh(); scope.push({ [src]: u });
      const bod = term(); scope.pop();
      return Lam(u, bod);
    }
    if (c === "*") { i++; return Era(); }
    if (c === "(") { eat("("); const f = term(); const a = term(); eat(")"); return App(f, a); }
    if (c === "&") { eat("&"); const lab = uint(); eat("{"); const l = term(); eat(","); const r = term(); eat("}"); return Sup(lab, l, r); }
    if (c === "{") { eat("{"); const l = term(); eat(","); const r = term(); eat("}"); return Sup(0, l, r); }
    if (c === "!") {
      eat("!"); let lab = 0;
      if (peek() === "&") { eat("&"); lab = uint(); }
      eat("{"); const a = name(); eat(","); const b = name(); eat("}"); eat("=");
      const val = term(); eat(";");
      const ua = rt.fresh(), ub = rt.fresh();
      scope.push({ [a]: ua, [b]: ub });
      const bod = term(); scope.pop();
      return Dup(lab, ua, ub, val, bod);
    }
    const src = name(); const u = lookup(src);
    return u !== null ? Var(u) : Var("free:" + src);
  }
  const t = term(); ws();
  if (i !== txt.length) throw new SyntaxError(`trailing input at ${i}`);
  return t;
}

// ── printer (canonical: names assigned in print-traversal order) ──────────
function show(term) {
  const names = new Map(); let c = 0;
  const nm = (u) => {
    if (!names.has(u)) { names.set(u, c < 26 ? String.fromCharCode(97 + c) : "v" + c); c++; }
    return names.get(u);
  };
  const go = (t) => {
    switch (t.t) {
      case "Var": return isFree(t.nam) ? t.nam.slice(5) : nm(t.nam);
      case "Era": return "*";
      case "Lam": return `λ${nm(t.nam)}.${go(t.bod)}`;
      case "App": return `(${go(t.fun)} ${go(t.arg)})`;
      case "Sup": return `&${t.lab}{${go(t.lft)},${go(t.rgt)}}`;
      case "Dup": return `!&${t.lab}{${nm(t.lft)},${nm(t.rgt)}}=${go(t.val)};${go(t.bod)}`;
    }
  };
  return go(term);
}
// ── state digest & free-name set (sub-resolving, DAG-memoized) ────────────
function stateDigest(rt, root) {
  // CANONICAL, BINDER-FAITHFUL, EQUIVARIANT digest (v2 — fixes a real hole
  // found by external review: v1 collapsed every bound variable to "V", so
  // two different programs digested identically and film BINDING was
  // binding a lossy shadow of the state).
  // Phase 1: canonical ids for every name (binders and pending wires) and
  // every DUP/SUP label, by first occurrence in a deterministic sub-chasing
  // preorder DFS — renaming-equivariant by construction, linear in DAG size.
  // Phase 2: memoized post-order DAG hash over canonical ids. Alpha-variant
  // states digest equal; behaviorally different states digest apart.
  const nid = new Map(), lid = new Map();
  let nn = 0, ln = 0;
  const cn = (nam) => { if (!nid.has(nam)) nid.set(nam, nn++); return nid.get(nam); };
  const cl = (lab) => { if (!lid.has(lab)) lid.set(lab, ln++); return lid.get(lab); };
  { // phase 1
    const seen = new Set(); const st = [root];
    while (st.length) {
      const n = chase(rt, st.pop());
      if (seen.has(n)) continue; seen.add(n);
      switch (n.t) {
        case "Var": if (!isFree(n.nam)) cn(n.nam); break;
        case "Lam": cn(n.nam); st.push(n.bod); break;
        case "App": st.push(n.arg); st.push(n.fun); break;
        case "Sup": cl(n.lab); st.push(n.rgt); st.push(n.lft); break;
        case "Dup": cl(n.lab); cn(n.lft); cn(n.rgt); st.push(n.bod); st.push(n.val); break;
      }
    }
  }
  // phase 2
  const memo = new Map();
  const st = [{ n: root, stage: 0 }];
  while (st.length) {
    const f = st[st.length - 1]; const n = chase(rt, f.n);
    if (memo.has(n)) { st.pop(); continue; }
    const keys = CHILDREN[n.t];
    if (f.stage === 0) { f.stage = 1; for (let i = keys.length - 1; i >= 0; i--) st.push({ n: n[keys[i]], stage: 0 }); continue; }
    let sig;
    switch (n.t) {
      case "Var": sig = isFree(n.nam) ? "F" + n.nam : "N" + cn(n.nam); break;
      case "Era": sig = "E"; break;
      case "Lam": sig = "L" + cn(n.nam) + "(" + memo.get(chase(rt, n.bod)) + ")"; break;
      case "App": sig = "A(" + memo.get(chase(rt, n.fun)) + "," + memo.get(chase(rt, n.arg)) + ")"; break;
      case "Sup": sig = "S" + cl(n.lab) + "(" + memo.get(chase(rt, n.lft)) + "," + memo.get(chase(rt, n.rgt)) + ")"; break;
      case "Dup": sig = "D" + cl(n.lab) + "[" + cn(n.lft) + "," + cn(n.rgt) + "](" + memo.get(chase(rt, n.val)) + "," + memo.get(chase(rt, n.bod)) + ")"; break;
    }
    if (sig.length > 80) sig = "#" + createHash("sha256").update(sig).digest("hex");   // full-width internal compaction: a truncated inner node would undercut the outer commitment
    memo.set(n, sig); st.pop();
  }
  return createHash("sha256").update(memo.get(chase(rt, root))).digest("hex");        // ArtifactHash256: evidence identities are never truncated
}
function freeNames(rt, root) {
  const seen = new Set(); const acc = new Set(); const st = [root];
  while (st.length) {
    let n = chase(rt, st.pop());
    if (seen.has(n)) continue; seen.add(n);
    if (n.t === "Var") { if (isFree(n.nam)) acc.add(n.nam); continue; }
    for (const k of CHILDREN[n.t]) st.push(n[k]);
  }
  return acc;
}const semId = (nfString) => "sem-" + createHash("sha256").update(nfString).digest("hex");

// ── small-step engine: redexes as positions, schedules as choices ─────────
// A path is an array of child keys from the root. chase() resolves Var→sub
// transparently (structural lookup, not an interaction).
function chase(rt, t) {
  let hops = 0, seen = null;
  while (t.t === "Var" && !isFree(t.nam) && rt.sub.has(t.nam)) {
    if (++hops > 64) {
      seen ??= new Set();
      if (seen.has(t.nam)) return t;      // indirection knot: treat as stuck (should be unreachable after the DUP gating below)
      seen.add(t.nam);
    }
    t = rt.sub.get(t.nam);
  }
  return t;
}
// A stuck application: its head chases to a FREE variable (a constructor like
// S/Z/X) through zero or more stuck apps. Only these may be DUP-APP-copied
// under free scheduling; a reducible or not-yet-bound head must wait.
function isStuckApp(rt, app, depth = 0) {
  if (depth > 10000) return false;
  const f = chase(rt, app.fun);
  if (f.t === "Var") return isFree(f.nam);
  if (f.t === "App") return isStuckApp(rt, f, depth + 1);
  return false;
}

// ── SEMANTIC PLANES (law:plane.rule-partition@1) ──────────────────────────
// R1 INTERACT: genuine computational interactions. R2 COLLAPSE: observation/
// readback, gated (DUP-VAR on free vars, DUP-APP on genuinely stuck apps),
// matching the upstream Collapsing extension. R3 WORLD and R4 EFFECT are
// named in the grid; they are not this kernel's scope. A law row or
// certificate names its plane profile — silent mixing is refused.
const PLANES = {
  INTERACT: new Set(["APP-LAM", "APP-SUP", "APP-ERA", "DUP-LAM", "DUP-SUP=", "DUP-SUP!", "DUP-ERA"]),
  COLLAPSE: new Set(["DUP-VAR", "DUP-APP"]),
};
const PLANE_OF = {};
for (const [p, rules] of Object.entries(PLANES)) for (const r of rules) PLANE_OF[r] = p;
const PLANE_POOL_FREE = new Set([...PLANES.INTERACT, ...PLANES.COLLAPSE]); // the declared hybrid pool

// ── AST small-step engine — THE RETRACTED RELATION, kept as a witness ─────
// law:sched.free.ast-term@1 FALSIFIED (by design). Term-level enumeration on
// the body-carrying AST is NOT a sound model of IC scheduling freedom:
// positional rule output can park a Dup inside another Dup's val slot, whose
// readiness cycle this relation can neither fire nor escape (false
// quiescence; witness church_exp_2_2@15 in L-FQ-AST-1). Kept executable so
// the witness keeps failing; scheduling claims live on the FLOAT engine.
function redexRule(rt, node) {
  if (node.t === "App") {
    const f = chase(rt, node.fun);
    if (f.t === "Lam") return "APP-LAM";
    if (f.t === "Sup") return "APP-SUP";
    if (f.t === "Era") return "APP-ERA";
    return null;
  }
  if (node.t === "Dup") {
    const v = chase(rt, node.val);
    if (v.t === "Lam") return "DUP-LAM";
    if (v.t === "Sup") return v.lab === node.lab ? "DUP-SUP=" : "DUP-SUP!";
    if (v.t === "Era") return "DUP-ERA";
    // SCHEDULER-SAFETY GATE — independently rediscovered here, then found
    // already enforced in forge/random_order.py, and matching upstream IC,
    // where DUP-VAR/DUP-APP live under the separate Collapsing extension.
    // Reading: INTERACT and COLLAPSE are different semantic planes with
    // different readiness conditions. Normative gate:
    // collapse rules may fire under free scheduling only on GENUINELY stuck
    // values. A bound-but-unsubbed Var is a wire whose peer hasn't arrived;
    // copying it early can tie sub[x]=Var(a), sub[a]=Var(x) — a black hole
    // the normal-order driver can never reach. Same for reducible Apps.
    if (v.t === "Var") return isFree(v.nam) ? "DUP-VAR" : null;
    if (v.t === "App") return isStuckApp(rt, v) ? "DUP-APP" : null;
    return null;
  }
  return null;
}

function findRedexes(rt, root, cap = Infinity) {
  const out = []; const seen = new Set();
  const st = [{ n: root, path: [] }];
  while (st.length && out.length < cap) {
    const { n, path } = st.pop();
    const r = chase(rt, n);
    if (seen.has(r)) continue; seen.add(r);
    const rule = redexRule(rt, r);
    if (rule) out.push({ path, rule });
    const keys = CHILDREN[r.t];
    for (let i = keys.length - 1; i >= 0; i--) st.push({ n: r[keys[i]], path: path.concat(keys[i]) });
  }
  return out;
}
// rebuild along path with the node at `path` replaced by fire(resolved-node)
function applyAt(rt, root, path) {
  function rec(t, i) {
    const r = chase(rt, t);                 // splice through Var indirection
    if (i === path.length) {
      const rule = redexRule(rt, r);
      if (!rule) return { refused: true };
      let out;
      if (r.t === "App") {
        const f = chase(rt, r.fun);
        out = rule === "APP-LAM" ? app_lam(rt, r, f)
            : rule === "APP-SUP" ? app_sup(rt, r, f)
            : app_era(rt);
      } else {
        const v = chase(rt, r.val);
        out = rule === "DUP-LAM" ? dup_lam(rt, r, v)
            : rule.startsWith("DUP-SUP") ? dup_sup(rt, r, v)
            : rule === "DUP-ERA" ? dup_era(rt, r)
            : rule === "DUP-VAR" ? dup_var(rt, r, v)
            : dup_app(rt, r, v);
      }
      return { node: out, rule };
    }
    const k = path[i];
    if (!CHILDREN[r.t].includes(k)) return { refused: true };
    const sub = rec(r[k], i + 1);
    if (sub.refused) return sub;
    const copy = { ...r }; copy[k] = sub.node;
    return { node: copy, rule: sub.rule };
  }
  const res = rec(root, 0);
  return res.refused ? { refused: true, root } : { refused: false, root: res.node, rule: res.rule };
}

// ═══ FLOATING-DUP ENGINE — the authoritative free-scheduling relation ═════
// (law:sched.free.float@1). Dups are HEAP OBJECTS, never tree nodes: extrude
// hoists every source Dup to the heap, and every rule that would create a
// Dup allocates instead. Consequence, by construction: chase(dup.val) can
// never yield Dup, so the AST knot configuration is unrepresentable.
// Enumeration is graph-complete: the root tree AND every heap value are
// reduction roots (omitting heap values reproduced a wait-knot in testing —
// the representation alone is not enough; the enumeration must match it).
class FloatRt extends Rt {
  constructor() { super(); this.heap = new Map(); this.did = 0; } // id -> {lab,l,r,val}
  alloc(lab, l, r, val) { this.heap.set(++this.did, { lab, l, r, val }); return this.did; }
}
// Adversarial allocator (law:state.exec-identity@1, law:refine.alloc-portability@1):
// heap ids DESCEND and name ints stride downward — injective, ORDER-REVERSING.
// A monotone perturbation is invisible to sorted folds; this one is not. It
// exists to separate execution identity from semantic identity, and to stand
// in for a second implementation until ic32 does.
class DescFloatRt extends FloatRt {
  constructor() { super(); this.ka = 0; this.kf = 0; }
  alloc(lab, l, r, val) { this.ka++; const id = 2_000_000 - 13 * this.ka; this.heap.set(id, { lab, l, r, val }); return id; }
  fresh() { this.kf++; return 3_000_000 - 7 * this.kf; }
}
// extrude: AST -> dup-free tree + heap entries.  !{l,r}=V;B  ⇒  heap += {V}, yield B
function extrude(frt, t) {
  switch (t.t) {
    case "Var": case "Era": return t;
    case "Lam": return Lam(t.nam, extrude(frt, t.bod));
    case "App": return App(extrude(frt, t.fun), extrude(frt, t.arg));
    case "Sup": return Sup(t.lab, extrude(frt, t.lft), extrude(frt, t.rgt));
    case "Dup": { frt.alloc(t.lab, t.lft, t.rgt, extrude(frt, t.val)); return extrude(frt, t.bod); }
  }
}
// classify a heap dup: which rule (if any) is it ready to fire? Bound-but-
// unsubbed Var and reducible App mean WAIT — the wire's peer hasn't arrived.
function dupRule(frt, d) {
  const v = chase(frt, d.val);
  if (v.t === "Lam") return "DUP-LAM";
  if (v.t === "Sup") return v.lab === d.lab ? "DUP-SUP=" : "DUP-SUP!";
  if (v.t === "Era") return "DUP-ERA";
  if (v.t === "Var") return isFree(v.nam) ? "DUP-VAR" : null;
  if (v.t === "App") return isStuckApp(frt, v) ? "DUP-APP" : null;
  return null; // Dup is impossible here — the theorem this representation buys
}
function fireDup(frt, id) {
  const d = frt.heap.get(id);
  if (!d) return { refused: true };
  const rule = dupRule(frt, d);
  if (!rule) return { refused: true };
  const v = chase(frt, d.val);
  frt.heap.delete(id);
  frt.bump(rule);
  if (rule === "DUP-LAM") {
    const x0 = frt.fresh(), x1 = frt.fresh(), f0 = frt.fresh(), f1 = frt.fresh();
    frt.setSub(d.l, Lam(x0, Var(f0)));
    frt.setSub(d.r, Lam(x1, Var(f1)));
    frt.setSub(v.nam, Sup(d.lab, Var(x0), Var(x1)));
    frt.alloc(d.lab, f0, f1, v.bod);
  } else if (rule === "DUP-SUP=") {
    frt.setSub(d.l, v.lft); frt.setSub(d.r, v.rgt);
  } else if (rule === "DUP-SUP!") {
    const a0 = frt.fresh(), a1 = frt.fresh(), b0 = frt.fresh(), b1 = frt.fresh();
    frt.setSub(d.l, Sup(v.lab, Var(a0), Var(b0)));
    frt.setSub(d.r, Sup(v.lab, Var(a1), Var(b1)));
    frt.alloc(d.lab, a0, a1, v.lft); frt.alloc(d.lab, b0, b1, v.rgt);
  } else if (rule === "DUP-ERA") {
    frt.setSub(d.l, Era()); frt.setSub(d.r, Era());
  } else if (rule === "DUP-VAR") {
    frt.setSub(d.l, v); frt.setSub(d.r, v);
  } else { // DUP-APP on a genuinely stuck application
    const f0 = frt.fresh(), f1 = frt.fresh(), x0 = frt.fresh(), x1 = frt.fresh();
    frt.setSub(d.l, App(Var(f0), Var(x0)));
    frt.setSub(d.r, App(Var(f1), Var(x1)));
    frt.alloc(d.lab, f0, f1, v.fun); frt.alloc(d.lab, x0, x1, v.arg);
  }
  return { refused: false, rule };
}
// App redexes on a dup-free tree; APP-SUP allocates a heap dup
function findAppRedexes(frt, root, cap = 4096) {
  const out = [], seen = new Set(), st = [{ n: root, path: [] }];
  while (st.length && out.length < cap) {
    const { n, path } = st.pop();
    const r = chase(frt, n);
    if (seen.has(r)) continue; seen.add(r);
    if (r.t === "App") {
      const f = chase(frt, r.fun);
      if (f.t === "Lam") out.push({ path, rule: "APP-LAM" });
      else if (f.t === "Sup") out.push({ path, rule: "APP-SUP" });
      else if (f.t === "Era") out.push({ path, rule: "APP-ERA" });
    }
    const keys = CHILDREN[r.t];
    for (let i = keys.length - 1; i >= 0; i--) st.push({ n: r[keys[i]], path: path.concat(keys[i]) });
  }
  return out;
}
function applyAppAt(frt, root, path) {
  function rec(t, i) {
    const r = chase(frt, t);
    if (i === path.length) {
      if (r.t !== "App") return { refused: true };
      const f = chase(frt, r.fun);
      let out, rule;
      if (f.t === "Lam") { rule = "APP-LAM"; frt.bump(rule); frt.setSub(f.nam, r.arg); out = f.bod; }
      else if (f.t === "Sup") {
        rule = "APP-SUP"; frt.bump(rule);
        const x0 = frt.fresh(), x1 = frt.fresh();
        frt.alloc(f.lab, x0, x1, r.arg);
        out = Sup(f.lab, App(f.lft, Var(x0)), App(f.rgt, Var(x1)));
      }
      else if (f.t === "Era") { rule = "APP-ERA"; frt.bump(rule); out = Era(); }
      else return { refused: true };
      return { node: out, rule };
    }
    const k = path[i];
    if (!CHILDREN[r.t].includes(k)) return { refused: true };
    const s = rec(r[k], i + 1);
    if (s.refused) return s;
    const c = { ...r }; c[k] = s.node;
    return { node: c, rule: s.rule };
  }
  const res = rec(root, 0);
  return res.refused ? { refused: true, root } : { refused: false, root: res.node, rule: res.rule };
}
// GRAPH-COMPLETE and DEMAND-DRIVEN enumeration: the root tree and every
// LIVE heap value are reduction roots; each redex is plane-tagged and
// pool-filtered. Liveness matters for AFFINITY, not just economy: a dead
// dup (no projection reachable from the root) that fires DUP-LAM on a
// shared lambda writes that lambda's binder sub a SECOND time — the
// illegal double consumption the reference's unreachability makes
// impossible. The fuzzer found exactly this within one round of the naive
// enumerate-everything version (dead dups stole live values); garbage must
// not compute. Enumeration is the policy; fireFloat stays mechanism-only,
// and replay's per-frame digests defend against forged dead-locus frames.
function findFloatRedexes(frt, root, planes) {
  const out = [];
  for (const a of findAppRedexes(frt, root)) if (planes.has(a.rule)) out.push({ kind: "app", ...a });
  const live = liveHeap(frt, root);
  for (const id of live) {
    const d = frt.heap.get(id);
    const rule = dupRule(frt, d);
    if (rule && planes.has(rule)) out.push({ kind: "dup", id, rule });
    for (const a of findAppRedexes(frt, d.val)) if (planes.has(a.rule)) out.push({ kind: "dupval", id, ...a });
  }
  return out;
}
function fireFloat(frt, root, rx) {
  if (rx.kind === "app") { const r = applyAppAt(frt, root, rx.path); return { root: r.root, rule: r.rule, refused: r.refused }; }
  if (rx.kind === "dupval") {
    const d = frt.heap.get(rx.id);
    if (!d) return { root, refused: true };
    const r = applyAppAt(frt, d.val, rx.path);
    if (!r.refused) d.val = r.root;
    return { root, rule: r.rule, refused: r.refused };
  }
  const r = fireDup(frt, rx.id);
  return { root, rule: r.rule, refused: r.refused };
}
// GC classification: a heap dup is LIVE iff one of its projections is
// reachable from the root (through subs and live heap values).
function liveHeap(frt, root) {
  const heapByProj = new Map();
  for (const [id, d] of frt.heap) { heapByProj.set(d.l, id); heapByProj.set(d.r, id); }
  const seen = new Set(), live = new Set(), st = [root];
  while (st.length) {
    const n = chase(frt, st.pop());
    if (seen.has(n)) continue; seen.add(n);
    if (n.t === "Var" && !isFree(n.nam)) {
      const id = heapByProj.get(n.nam);
      if (id !== undefined && !live.has(id)) { live.add(id); st.push(frt.heap.get(id).val); }
    }
    for (const k of CHILDREN[n.t]) st.push(n[k]);
  }
  return live;
}
// deterministic composite state for films: fold heap entries (ascending id,
// innermost-first) back around the root as Dup nodes, then digest. BINDING-
// grade (adequate for evidence identity along one schedule); equivalence
// across heap orderings is future Coherence work, recorded in the grid.
function foldHeap(frt, root) {
  const ids = [...frt.heap.keys()].sort((a, b) => a - b);
  let acc = root;
  for (let i = ids.length - 1; i >= 0; i--) {
    const d = frt.heap.get(ids[i]);
    acc = Dup(d.lab, d.l, d.r, d.val, acc);
  }
  return acc;
}
function floatDigest(frt, root) { return stateDigest(frt, foldHeap(frt, root)); }

// ═══ STATE IDENTITY, SPLIT (round 6) ══════════════════════════════════════
// law:state.exec-identity@1 — execStateId (= floatDigest) is EXECUTION
// identity: total heap in id order, dead entries included. It is
// deliberately allocation-sensitive — that is what makes it replay-grade
// within one implementation and one allocator discipline. Films and
// certificate receipts bind THIS id.
// law:state.semantic-quotient@1 — semStateId is SEMANTIC identity: the
// LIVE heap folded in FIRST-REACHABLE DISCOVERY ORDER from the root, then
// the canonical digest (which is already alpha- and label-equivariant by
// first-occurrence numbering). Under this quotient, heap-id bijections,
// dead heap content, and allocation order are unobservable — the round-6
// audit witness (18b4e47b… ≠ 6bca1878… on behaviorally identical states)
// digests EQUAL here. Cross-allocator and cross-implementation claims
// bind THIS id, never the execution id.
const execStateId = floatDigest;
function liveDiscoveryOrder(frt, root) {
  const heapByProj = new Map();
  for (const [id, d] of frt.heap) { heapByProj.set(d.l, id); heapByProj.set(d.r, id); }
  const order = [], seenDup = new Set(), seenNode = new Set(), st = [root];
  while (st.length) {
    const n = chase(frt, st.pop());
    if (!n || typeof n !== "object" || seenNode.has(n)) continue;
    seenNode.add(n);
    switch (n.t) {
      case "Var": {
        const id = heapByProj.get(n.nam);
        if (id !== undefined && !seenDup.has(id)) {
          seenDup.add(id); order.push(id);
          st.push(frt.heap.get(id).val);
        }
        break;
      }
      case "Lam": st.push(n.bod); break;
      case "App": st.push(n.arg); st.push(n.fun); break;
      case "Sup": st.push(n.rgt); st.push(n.lft); break;
      case "Dup": st.push(n.bod); st.push(n.val); break;
    }
  }
  return order;
}
function foldCanonicalLive(frt, root) {
  const order = liveDiscoveryOrder(frt, root);
  let acc = root;
  for (let i = order.length - 1; i >= 0; i--) {
    const d = frt.heap.get(order[i]);
    acc = Dup(d.lab, d.l, d.r, d.val, acc);
  }
  return { acc, order };
}
function semStateId(frt, root) { return stateDigest(frt, foldCanonicalLive(frt, root).acc); }
// canonical (semantic) locus for a redex: structural path for tree apps,
// discovery index for heap dups — allocation-independent by construction.
function semLocusOf(rx, order) {
  const ix = (id) => { const i = order.indexOf(id); return i < 0 ? "?" : String(i); };
  if (rx.kind === "app") return "t:" + rx.path.join(".");
  if (rx.kind === "dup") return "d:" + ix(rx.id);
  return "v:" + ix(rx.id) + ":" + rx.path.join(".");
}

// ═══ SEMANTIC FILM (round 6) — the portable evidence object ═══════════════
// Frames carry the CANONICAL locus and SEMANTIC pre/post ids; the chain and
// terminal are committed exactly like execution films but in the semantic
// domain ("TRVM-SEMFILM-v1"). Replay is by locus MATCHING against the live
// enumeration of a fresh runtime — ANY runtime class implementing the
// relation (here: FloatRt or the adversarial DescFloatRt; eventually ic32).
// Enabledness is inherent: an unmatched locus refuses.
function newSemFilm() { return { frames: [], terminal: null, film_id: null }; }
const semFilmIdOf = (t) =>
  createHash("sha256").update(["TRVM-SEMFILM-v1", t.last_frame, t.termination, t.steps,
    t.final_sem_id, t.normal_form_id ?? "-", (t.planes ?? []).join(",")].join("|")).digest("hex");
function sealSemFilm(film, frt, root, t) {
  t.final_sem_id = semStateId(frt, root);
  if (t.termination === "NORMAL_FORM" && t.normal_form_id === undefined) {
    try { t.normal_form_id = semId(readback(frt, root).str); } catch { t.normal_form_id = null; }
  }
  film.terminal = t; film.film_id = semFilmIdOf(t);
  return film;
}
function replaySemFilm(srcTerm, film, RtClass = FloatRt) {
  const frt = new RtClass();
  let root = extrude(frt, parse(frt, srcTerm));
  const t = film.terminal;
  if (!t || typeof t.termination !== "string") return { ok: false, reason: "sem-terminal-missing" };
  const permitted = new Set(t.planes ?? [...PLANE_POOL_FREE]);
  let prev = "genesis", n = 0;
  for (const frame of film.frames) {
    if (!permitted.has(frame.rule)) return { ok: false, at: n, reason: "sem-plane-not-permitted" };  // permitted is a RULE pool (see replayFloat)
    if (semStateId(frt, root) !== frame.pre) return { ok: false, at: n, reason: "sem-revision-mismatch" };
    const rs = findFloatRedexes(frt, root, permitted);
    const order = liveDiscoveryOrder(frt, root);
    const rx = rs.find((r) => semLocusOf(r, order) === frame.locus);
    if (!rx) return { ok: false, at: n, reason: "sem-locus-not-enabled" };
    const r = fireFloat(frt, root, rx);
    if (r.refused || r.rule !== frame.rule)
      return { ok: false, at: n, reason: r.refused ? "sem-not-a-redex" : "sem-rule-mismatch" };
    if (PLANE_OF[r.rule] !== frame.plane) return { ok: false, at: n, reason: "sem-plane-mismatch" };
    root = r.root;
    const post = semStateId(frt, root);
    if (post !== frame.post) return { ok: false, at: n, reason: "sem-post-mismatch" };
    if (frameId31(prev, frame.pre, frame.plane, frame.rule, frame.locus, post) !== frame.frame_id)
      return { ok: false, at: n, reason: "sem-chain-mismatch" };
    prev = frame.frame_id; n++;
  }
  if (t.last_frame !== prev) return { ok: false, reason: "sem-terminal-last-frame-mismatch" };
  if (t.steps !== n) return { ok: false, reason: "sem-terminal-steps-mismatch" };
  if (t.final_sem_id !== semStateId(frt, root)) return { ok: false, reason: "sem-terminal-state-mismatch" };
  if (t.termination === "NORMAL_FORM") {
    if (findFloatRedexes(frt, root, permitted).length !== 0)
      return { ok: false, reason: "sem-false-normal-form" };
    if (t.normal_form_id != null) {
      let nfid = null;
      try { nfid = semId(readback(frt, root, 200000).str); } catch { /* stays null */ }
      if (nfid !== t.normal_form_id) return { ok: false, reason: "sem-terminal-nf-mismatch" };
    }
  } else if (t.termination !== "BUDGET_EXHAUSTED") return { ok: false, reason: "sem-terminal-malformed" };
  if (semFilmIdOf(t) !== film.film_id) return { ok: false, reason: "sem-film-id-mismatch" };
  return { ok: true, root, frt };
}
// READBACK = fold the LIVE heap into the tree, then run the reference
// driver. Live residual dups at pool-quiescence are legitimate COLLAPSE
// work (a dup whose value is a bound variable in normal-form position can
// only be resolved contextually); dead entries stay dropped — garbage does
// not compute. The readback is instrumented so batteries can assert its
// PURITY: from pool-quiescence it must fire ZERO INTERACT-plane rules —
// only DUP-VAR collapse, bounded by the residual live-dup count. (The AST
// relation's false quiescence violated exactly this: its readback fired
// INTERACT rules and diverged.)
function foldLive(frt, root) {
  const live = liveHeap(frt, root);
  const ids = [...live].sort((a, b) => a - b);
  let acc = root;
  for (let i = ids.length - 1; i >= 0; i--) {
    const d = frt.heap.get(ids[i]);
    acc = Dup(d.lab, d.l, d.r, d.val, acc);
  }
  return { acc, liveCount: ids.length };
}
function readback(frt, root, budget = 2_000_000) {
  const before = new Map(frt.ctr);
  const { acc, liveCount } = foldLive(frt, root);
  const nf = normalRef(frt, acc, { n: budget });
  let interactFired = 0, collapseFired = 0;
  for (const [rule, n] of frt.ctr) {
    const d = n - (before.get(rule) ?? 0);
    if (d <= 0) continue;
    if (PLANES.INTERACT.has(rule)) interactFired += d; else collapseFired += d;
  }
  return { nf, str: show(nf), interactFired, collapseFired, liveCount };
}
function wellFormedFloat(frt, root) {
  if (!wellFormed(frt, root)) return false;
  for (const [, d] of frt.heap) {
    if (!(Number.isInteger(d.l) && Number.isInteger(d.r) && Number.isInteger(d.lab))) return false;
    if (!wellFormed(frt, d.val)) return false;
  }
  return true;
}
function freeNamesFloat(frt, root) {
  const acc = freeNames(frt, root);
  for (const [, d] of frt.heap) for (const n of freeNames(frt, d.val)) acc.add(n);
  return acc;
}

// ═══ FILM v3.1 — the outcome is inside the commitment ═════════════════════
// law:film.evidence-chain@5 (format unchanged since @4; the @5 revision is
// REPLAY: per-frame enabledness in the live relation — see replayFloat.
// @4 superseded @3, whose replay verified the frame
// chain but never read film.terminal — external review mutated termination,
// steps and last_frame on a sealed film and replay still accepted it).
// frame_id = H(prev | pre | plane | rule | locus | post); frames carry i as
// DECLARED NON-AUTHORITATIVE metadata (replay counts for itself);
// film_id = H("TRVM-FILM-v3.1" | last_frame | terminal fields).
const frameId31 = (prev, pre, plane, rule, locus, post) =>
  createHash("sha256").update([prev, pre, plane, rule, locus, post].join("|")).digest("hex");
const filmIdOf = (t) =>
  createHash("sha256").update(["TRVM-FILM-v3.1", t.last_frame, t.termination, t.steps,
    t.final_state_id, t.normal_form_id ?? "-", t.budget ?? "-", t.remaining_work ?? "-",
    (t.planes ?? []).join(",")].join("|")).digest("hex");
const newFilm = () => ({ frames: [], terminal: null, film_id: null });
const encodeLocus = (rx) =>
  rx.kind === "app" ? "t:" + rx.path.join(".")
  : rx.kind === "dup" ? "d:" + rx.id
  : "v:" + rx.id + ":" + rx.path.join(".");
function decodeLocus(s) {
  if (s.startsWith("t:")) return { kind: "app", path: s.slice(2).split(".").filter(Boolean) };
  if (s.startsWith("d:")) return { kind: "dup", id: parseInt(s.slice(2)) };
  const m = /^v:(\d+):(.*)$/.exec(s);
  return { kind: "dupval", id: parseInt(m[1]), path: m[2].split(".").filter(Boolean) };
}
function sealFilm(film, frt, root, t) {
  t.final_state_id = floatDigest(frt, root);
  if (t.termination === "NORMAL_FORM") {
    try { t.normal_form_id = semId(readback(frt, root, 200000).str); }
    catch { t.normal_form_id = null; }
  }
  film.terminal = t;
  film.film_id = filmIdOf(t);
}
function normalizeFloat(frt, root, pick, rnd, opts = {}) {
  const budget = opts.budget ?? 20000;
  const planes = opts.planes ?? PLANE_POOL_FREE;
  const film = opts.film ?? null;
  let steps = 0, prev = "genesis";
  for (;;) {
    const rs = findFloatRedexes(frt, root, planes);
    if (rs.length === 0) {
      if (film) sealFilm(film, frt, root,
        { termination: "NORMAL_FORM", steps, last_frame: prev, planes: [...planes] });
      return { root, steps, termination: "NORMAL_FORM" };
    }
    if (steps >= budget) {
      if (film) sealFilm(film, frt, root,
        { termination: "BUDGET_EXHAUSTED", steps, last_frame: prev, budget,
          remaining_work: rs.length, planes: [...planes] });
      return { root, steps, termination: "BUDGET_EXHAUSTED", remaining: rs.length };
    }
    const rx = pick(rs, rnd);
    const pre = film ? floatDigest(frt, root) : null;
    const r = fireFloat(frt, root, rx);
    if (r.refused) throw new Error("enabled redex refused — engine bug");
    root = r.root;
    steps++;
    if (film) {
      const post = floatDigest(frt, root);
      const plane = PLANE_OF[r.rule];
      const locus = encodeLocus(rx);
      const fid = frameId31(prev, pre, plane, r.rule, locus, post);
      film.frames.push({ i: film.frames.length, plane, rule: r.rule, locus, pre, post, prev, frame_id: fid });
      prev = fid;
    }
  }
}
// replay v3.1r (law:film.evidence-chain@5, supersedes @4): frames verified
// against digests AND against the RELATION — each frame's locus must be
// ENABLED in the live enumeration under the film's DECLARED planes before
// it may fire. Round-5 audit: digest-consistent, honestly-committed films
// firing DEAD heap loci (mechanically firable, outside the live relation)
// replayed ok under @4. Digest consistency is necessary but NOT sufficient:
// a film witnesses a derivation in the certified relation, so replay
// re-derives per-frame membership. Then the TERMINAL is RE-DERIVED and the
// film_id commitment recomputed. Typed refusals throughout (18).
function replayFloat(srcTerm, film) {
  const t = film.terminal;
  if (!t || typeof t.termination !== "string") return { ok: false, reason: "terminal-missing" };
  const permitted = new Set(t.planes ?? [...PLANE_POOL_FREE]);
  const frt = new FloatRt();
  let root = extrude(frt, parse(frt, srcTerm));
  let prev = "genesis", n = 0;
  for (const frame of film.frames) {
    const now = floatDigest(frt, root);
    if (now !== frame.pre) return { ok: false, at: n, reason: "revision-mismatch" };
    if (!permitted.has(frame.rule)) return { ok: false, at: n, reason: "plane-not-permitted" };
    const enabled = findFloatRedexes(frt, root, permitted);
    if (!enabled.some((r) => encodeLocus(r) === frame.locus))
      return { ok: false, at: n, reason: "illegal-transition" };
    const r = fireFloat(frt, root, decodeLocus(frame.locus));
    if (r.refused || r.rule !== frame.rule)
      return { ok: false, at: n, reason: r.refused ? "not-a-redex" : "rule-mismatch" };
    if (PLANE_OF[r.rule] !== frame.plane) return { ok: false, at: n, reason: "plane-mismatch" };
    root = r.root;
    const post = floatDigest(frt, root);
    if (post !== frame.post) return { ok: false, at: n, reason: "post-state-mismatch" };
    if (frameId31(prev, frame.pre, frame.plane, frame.rule, frame.locus, post) !== frame.frame_id)
      return { ok: false, at: n, reason: "chain-mismatch" };
    prev = frame.frame_id; n++;
  }
  if (t.last_frame !== prev) return { ok: false, reason: "terminal-last-frame-mismatch" };
  if (t.steps !== n) return { ok: false, reason: "terminal-steps-mismatch" };
  if (t.final_state_id !== floatDigest(frt, root)) return { ok: false, reason: "terminal-state-mismatch" };
  const rs = findFloatRedexes(frt, root, permitted);
  if (t.termination === "NORMAL_FORM") {
    if (rs.length !== 0) return { ok: false, reason: "false-normal-form" };
    if (t.normal_form_id != null) {
      let nfid = null;
      try { nfid = semId(readback(frt, root, 200000).str); } catch { /* nfid stays null */ }
      if (nfid !== t.normal_form_id) return { ok: false, reason: "terminal-nf-mismatch" };
    }
  } else if (t.termination === "BUDGET_EXHAUSTED") {
    if (!Number.isInteger(t.budget) || !Number.isInteger(t.remaining_work))
      return { ok: false, reason: "terminal-malformed" };
    if (rs.length !== t.remaining_work) return { ok: false, reason: "terminal-work-mismatch" };
    if (n < t.budget) return { ok: false, reason: "terminal-budget-mismatch" };
  } else return { ok: false, reason: "terminal-malformed" };
  if (filmIdOf(t) !== film.film_id) return { ok: false, reason: "film-id-mismatch" };
  return { ok: true, root, frt };
}

// ═══ SCHEDULER CERTIFICATE v2 + independent full-re-execution checker ═════
// law:sched.certificate@2 (supersedes @1 — round-5 external audit forged
// 10/10 single-field mutations and a hollow zero-exhibit certificate past
// the v1 checker, which re-derived only the corpus hash and replayed only
// what it was handed; a hollow certificate also passed grid_check: an
// assurance COMPOSITION bug — fragment verifiers whose union did not verify
// the substantive claim).
//
// v2 field discipline (law:cert.field-discipline@1):
//   DERIVED       — the checker RECOMPUTES it: every receipt via full
//                   deterministic re-execution, evidence aggregates by
//                   arithmetic over verified receipts, corpus hash from the
//                   vectors it is handed.
//   COMMITTED     — inside cert_id = H("TRVM-SCHEDCERT-v2" | canonical
//                   serialization). Silent edits die at cert-id-mismatch;
//                   laundered edits (commitment honestly recomputed) must
//                   survive the semantic re-derivations instead — and don't.
//   INFORMATIONAL — declared non-authoritative, outside cert_id, forbidden
//                   from supporting a law claim.
// The EVIDENCE BASIS is the RUN MANIFEST (one receipt per run), not the
// exhibit films: exhibits are pedagogical witnesses for the historically
// load-bearing exp terms; receipts are what gets re-executed. "96/96" is a
// derived property of receipts, never trusted JSON.
const CERT_REPRESENTATION = "floating-dup-heap-v1";
const CERT_QUIESCENCE = "no enabled redex in the root tree or any LIVE heap value (pool-quiescence); residual live dups resolved by pure-collapse readback";
const CERT_CLAIM_REQUIREMENTS = {
  "law:sched.free.float@1": ["completion", "nf-agreement-with-reference", "readback-purity"],
  "law:plane.rule-partition@1": [],
  "law:deriv.count-invariance.float@1": ["interaction-count-invariance", "spec-count-equality"],
};
const CERT_KNOWN_CLAIMS = new Set(["completion", "nf-agreement-with-reference",
  "readback-purity", "interaction-count-invariance", "spec-count-equality"]);
const CERT_EXHIBIT_TERMS = ["church_exp_2_2", "church_exp_3_2", "church_exp_2_3",
  "church_exp_3_3", "church_exp_4_2", "church_exp_2_4"];
// canonical serialization: FIXED key order, shared by maker and checker
const committedView = (c) => [
  ["type", c.type], ["version", c.version], ["representation", c.representation],
  ["plane_profile", { INTERACT: [...(c.plane_profile?.INTERACT ?? [])],
                      COLLAPSE_GATED: [...(c.plane_profile?.COLLAPSE_GATED ?? [])] }],
  ["quiescence_criterion", c.quiescence_criterion],
  ["strategy", { kind: c.strategy?.kind, schedulers: [...(c.strategy?.schedulers ?? [])] }],
  ["budget", c.budget],
  ["corpus", { id: c.corpus?.id, sha256: c.corpus?.sha256 }],
  ["claims", [...(c.claims ?? [])]], ["law_refs", [...(c.law_refs ?? [])]],
  ["run_manifest_hash", c.run_manifest_hash],
  ["exhibit_film_ids", [...(c.exhibit_film_ids ?? [])]],
];
const certIdOf = (c) =>
  createHash("sha256").update("TRVM-SCHEDCERT-v2|" + JSON.stringify(committedView(c))).digest("hex");
const manifestHashOf = (receipts) =>
  createHash("sha256").update(JSON.stringify(receipts)).digest("hex");

// one certified run = one receipt (+ its in-memory film for film_id)
function certifiedRun(term, schedName, pick, seed, budget) {
  const frt = new FloatRt();
  const root0 = extrude(frt, parse(frt, term));
  const film = newFilm();
  const out = normalizeFloat(frt, root0, pick, mulberry32(seed), { film, budget });
  let rb = null, nf_id = null;
  if (out.termination === "NORMAL_FORM") { rb = readback(frt, out.root); nf_id = semId(rb.str); }
  return {
    receipt: { term_name: null, scheduler: schedName, seed, steps: out.steps,
      interactions: frt.total(), termination: out.termination,
      final_state_id: film.terminal.final_state_id, nf_id, nf_matched: null,
      readback: rb ? { interact: rb.interactFired, collapse: rb.collapseFired, live: rb.liveCount } : null,
      film_id: film.film_id },
    film };
}
function runCertifiedBattery(vectors, schedulerTable, budget) {
  const receipts = [], exhibits = [];
  const refId = new Map(vectors.map((v) => [v.name, semId(v.nf)]));
  let idx = 0;
  for (const [sn, pick] of Object.entries(schedulerTable)) {
    for (const v of vectors) {
      const seed = 0xC5000 + 4099 * idx; idx++;
      const r = certifiedRun(v.term, sn, pick, seed, budget);
      r.receipt.term_name = v.name;
      r.receipt.nf_matched = r.receipt.nf_id != null && r.receipt.nf_id === refId.get(v.name);
      receipts.push(r.receipt);
      if (sn === "random" && CERT_EXHIBIT_TERMS.includes(v.name))
        exhibits.push({ name: v.name, scheduler: sn, src: v.term, film: r.film });
    }
  }
  return { receipts, exhibits };
}
// DERIVED evidence: pure arithmetic over receipts (grid_check repeats this
// engine-free; the kernel checker verifies the receipts themselves first)
function aggregateReceipts(receipts) {
  const schedulers = new Set(), terms = new Set();
  let completed = 0, nf_matched = 0, readback_pure = 0, max_steps = 0;
  for (const r of receipts) {
    schedulers.add(r.scheduler); terms.add(r.term_name);
    if (r.termination === "NORMAL_FORM") completed++;
    if (r.nf_matched === true) nf_matched++;
    if (r.readback && r.readback.interact === 0) readback_pure++;
    max_steps = Math.max(max_steps, r.steps);
  }
  return { schedulers: schedulers.size, terms: terms.size, runs: receipts.length,
    completed, nf_matched, readback_pure, max_steps };
}
function buildSchedulerCertificateV2(corpusId, vectors, schedulerTable, budget, battery) {
  const cert = {
    type: "SchedulerCertificate", version: 2,
    representation: CERT_REPRESENTATION,
    plane_profile: { INTERACT: [...PLANES.INTERACT], COLLAPSE_GATED: [...PLANES.COLLAPSE] },
    quiescence_criterion: CERT_QUIESCENCE,
    strategy: { kind: "free-choice-sample", schedulers: Object.keys(schedulerTable) },
    budget,
    corpus: { id: corpusId, sha256: createHash("sha256").update(JSON.stringify(vectors)).digest("hex") },
    claims: [...CERT_KNOWN_CLAIMS],
    law_refs: Object.keys(CERT_CLAIM_REQUIREMENTS),
    run_manifest: battery.receipts,
    run_manifest_hash: manifestHashOf(battery.receipts),
    exhibit_films: battery.exhibits,
    exhibit_film_ids: battery.exhibits.map((e) => e.film.film_id),
    evidence: aggregateReceipts(battery.receipts),
    informational: { note: "NON-AUTHORITATIVE: outside cert_id, forbidden from supporting law claims",
      generator: "trvm_law_kernel.mjs v" + KERNEL_VERSION, node: process.version },
  };
  cert.cert_id = certIdOf(cert);
  return cert;
}
function checkSchedulerCertificateV2(cert, corpusId, vectors, schedulerTable) {
  const reasons = [];
  const R = (c, m) => { if (!c) reasons.push(m); };
  if (cert?.type !== "SchedulerCertificate" || cert?.version !== 2)
    return { ok: false, reasons: ["not-a-v2-certificate"] };
  // commitments first — silent edits die here
  R(certIdOf(cert) === cert.cert_id, "cert-id-mismatch");
  R(manifestHashOf(cert.run_manifest ?? []) === cert.run_manifest_hash, "manifest-hash-mismatch");
  // representation authority: THIS checker is floating-dup-heap-v1; a
  // certificate naming anything else cannot be verified by it
  R(cert.representation === CERT_REPRESENTATION, "unknown-representation");
  R(cert.quiescence_criterion === CERT_QUIESCENCE, "criterion-mismatch");
  const setEq = (a, b) => a.length === b.length && [...a].every((x) => b.includes(x));
  R(setEq(cert.plane_profile?.INTERACT ?? [], [...PLANES.INTERACT]) &&
    setEq(cert.plane_profile?.COLLAPSE_GATED ?? [], [...PLANES.COLLAPSE]), "profile-mismatch");
  R(cert.corpus?.id === corpusId, "corpus-id-mismatch");
  R(cert.corpus?.sha256 === createHash("sha256").update(JSON.stringify(vectors)).digest("hex"),
    "corpus-hash-mismatch");
  const receipts = cert.run_manifest ?? [];
  const schedSet = [...new Set(receipts.map((r) => r.scheduler))];
  R(cert.strategy?.kind === "free-choice-sample", "unknown-strategy-kind");
  R(setEq(cert.strategy?.schedulers ?? [], schedSet), "strategy-mismatch");
  for (const sn of schedSet) R(sn in schedulerTable, "unknown-scheduler:" + sn);
  // completeness: exact schedulers × terms cross product, once each, nonzero
  const termNames = vectors.map((v) => v.name);
  const want = new Set();
  for (const sn of cert.strategy?.schedulers ?? []) for (const t of termNames) want.add(t + "|" + sn);
  const got = receipts.map((r) => r.term_name + "|" + r.scheduler);
  R(receipts.length > 0 && got.length === want.size &&
    new Set(got).size === got.length && got.every((k) => want.has(k)), "incomplete-runs");
  if (reasons.length) return { ok: false, reasons };
  // DERIVED: full deterministic re-execution of EVERY receipt
  const byName = new Map(vectors.map((v) => [v.name, v]));
  const refId = new Map(vectors.map((v) => [v.name, semId(v.nf)]));
  for (const rc of receipts) {
    const v = byName.get(rc.term_name);
    const rr = certifiedRun(v.term, rc.scheduler, schedulerTable[rc.scheduler], rc.seed, cert.budget);
    rr.receipt.term_name = rc.term_name;
    rr.receipt.nf_matched = rr.receipt.nf_id != null && rr.receipt.nf_id === refId.get(rc.term_name);
    for (const f of ["steps", "interactions", "termination", "final_state_id", "nf_id", "nf_matched", "film_id", "readback"])
      R(JSON.stringify(rc[f] ?? null) === JSON.stringify(rr.receipt[f] ?? null),
        "receipt-replay-mismatch:" + rc.term_name + ":" + rc.scheduler + ":" + f);
  }
  // DERIVED: aggregates recomputed and compared EXACTLY
  R(JSON.stringify(aggregateReceipts(receipts)) === JSON.stringify(cert.evidence), "evidence-mismatch");
  // claims verified semantically against the (now verified) receipts
  for (const c of cert.claims ?? []) R(CERT_KNOWN_CLAIMS.has(c), "unknown-claim:" + c);
  const claim = new Set(cert.claims ?? []);
  if (claim.has("completion"))
    R(receipts.every((r) => r.termination === "NORMAL_FORM"), "claim-unsupported:completion");
  if (claim.has("nf-agreement-with-reference"))
    R(receipts.every((r) => r.nf_matched === true), "claim-unsupported:nf-agreement-with-reference");
  if (claim.has("readback-purity"))
    R(receipts.every((r) => r.readback && r.readback.interact === 0), "claim-unsupported:readback-purity");
  if (claim.has("interaction-count-invariance"))
    for (const t of termNames)
      R(new Set(receipts.filter((r) => r.term_name === t).map((r) => r.interactions)).size === 1,
        "claim-unsupported:interaction-count-invariance:" + t);
  if (claim.has("spec-count-equality"))
    for (const t of termNames)
      R(receipts.filter((r) => r.term_name === t).every((r) => r.interactions === byName.get(t).ref_interactions),
        "claim-unsupported:spec-count-equality:" + t);
  // law refs: known and JUSTIFIED by verified claims — authority needs evidence
  R((cert.law_refs ?? []).length > 0, "no-law-refs");
  for (const ref of cert.law_refs ?? []) {
    const req = CERT_CLAIM_REQUIREMENTS[ref];
    if (!req) { R(false, "unknown-law-ref:" + ref); continue; }
    for (const c of req) R(claim.has(c), "unjustified-law-ref:" + ref + ":requires:" + c);
  }
  // exhibits: witnesses tied into the manifest, one per exp term, replayable
  const ridSet = new Set(receipts.map((r) => r.film_id));
  R(setEq(cert.exhibit_film_ids ?? [], (cert.exhibit_films ?? []).map((e) => e.film?.film_id)),
    "exhibit-ids-mismatch");
  for (const t of CERT_EXHIBIT_TERMS)
    R((cert.exhibit_films ?? []).some((e) => e.name === t), "missing-exhibit:" + t);
  for (const ex of cert.exhibit_films ?? []) {
    R(ridSet.has(ex.film?.film_id), "exhibit-not-in-manifest:" + ex.name);
    const v = byName.get(ex.name);
    R(!!v && ex.src === v.term, "exhibit-src-mismatch:" + ex.name);
    for (const fr of ex.film?.frames ?? [])
      R(cert.plane_profile.INTERACT.includes(fr.rule) || cert.plane_profile.COLLAPSE_GATED.includes(fr.rule),
        "plane-violation:" + ex.name + ":" + fr.rule);
    const rep = replayFloat(ex.src, ex.film);
    R(rep.ok, "replay-refused:" + ex.name + ":" + (rep.reason ?? ""));
    R(ex.film?.terminal?.termination === "NORMAL_FORM", "terminal-not-nf:" + ex.name);
  }
  return { ok: reasons.length === 0, reasons };
}

// well-formedness (CLOSURE): grammar respected after every step
function wellFormed(rt, root) {
  const seen = new Set(); const st = [root];
  while (st.length) {
    const r = chase(rt, st.pop());
    if (seen.has(r)) continue; seen.add(r);
    switch (r.t) {
      case "Var": if (!(isFree(r.nam) || Number.isInteger(r.nam))) return false; break;
      case "Era": break;
      case "Lam": if (!Number.isInteger(r.nam)) return false; st.push(r.bod); break;
      case "App": st.push(r.fun, r.arg); break;
      case "Sup": if (!Number.isInteger(r.lab)) return false; st.push(r.lft, r.rgt); break;
      case "Dup": if (!(Number.isInteger(r.lft) && Number.isInteger(r.rgt))) return false; st.push(r.val, r.bod); break;
      default: return false;
    }
  }
  return true;
}

// ── embedded conformance vectors (docs/spec/conformance/vectors) ──────────
const EMBEDDED_VECTORS = [{"name": "identity", "term": "\u03bbx.x", "nf": "\u03bba.a", "ref_interactions": 0}, {"name": "K_true", "term": "\u03bba.\u03bbb.a", "nf": "\u03bba.\u03bbb.a", "ref_interactions": 0}, {"name": "K_false", "term": "\u03bba.\u03bbb.b", "nf": "\u03bba.\u03bbb.b", "ref_interactions": 0}, {"name": "apply_id", "term": "(\u03bbx.\u03bbt.(t x) \u03bby.y)", "nf": "\u03bba.(a \u03bbb.b)", "ref_interactions": 1}, {"name": "not_true", "term": "(\u03bbb.\u03bbt.\u03bbf.((b f) t) \u03bbT.\u03bbF.T)", "nf": "\u03bba.\u03bbb.b", "ref_interactions": 3}, {"name": "dup_pair", "term": "!{a,b} = {\u03bbx.x,\u03bby.y}; (a b)", "nf": "\u03bba.a", "ref_interactions": 2}, {"name": "sup_app", "term": "({\u03bbx.x,\u03bby.y} \u03bbz.z)", "nf": "&0{\u03bba.a,\u03bbb.b}", "ref_interactions": 5}, {"name": "church_not_2", "term": "((\u03bbf.\u03bbx.!{f0,f1}=f;(f0 (f1 x)) \u03bbB.\u03bbT.\u03bbF.((B F) T)) \u03bba.\u03bbb.a)", "nf": "\u03bba.\u03bbb.a", "ref_interactions": 16}, {"name": "church_apply_0", "term": "((\u03bbf.\u03bbx.x S) Z)", "nf": "Z", "ref_interactions": 2}, {"name": "church_apply_1", "term": "((\u03bbf.\u03bbx.(f x) S) Z)", "nf": "(S Z)", "ref_interactions": 2}, {"name": "church_apply_2", "term": "((\u03bbf.\u03bbx.!&1001{c0,c1}=f;(c0 (c1 x)) S) Z)", "nf": "(S (S Z))", "ref_interactions": 3}, {"name": "church_apply_3", "term": "((\u03bbf.\u03bbx.!&1002{c0,t0}=f;!&1003{c1,c2}=t0;(c0 (c1 (c2 x))) S) Z)", "nf": "(S (S (S Z)))", "ref_interactions": 4}, {"name": "church_apply_4", "term": "((\u03bbf.\u03bbx.!&1004{c0,t0}=f;!&1005{c1,t1}=t0;!&1006{c2,c3}=t1;(c0 (c1 (c2 (c3 x)))) S) Z)", "nf": "(S (S (S (S Z))))", "ref_interactions": 5}, {"name": "church_apply_5", "term": "((\u03bbf.\u03bbx.!&1007{c0,t0}=f;!&1008{c1,t1}=t0;!&1009{c2,t2}=t1;!&1010{c3,c4}=t2;(c0 (c1 (c2 (c3 (c4 x))))) S) Z)", "nf": "(S (S (S (S (S Z)))))", "ref_interactions": 6}, {"name": "church_apply_6", "term": "((\u03bbf.\u03bbx.!&1011{c0,t0}=f;!&1012{c1,t1}=t0;!&1013{c2,t2}=t1;!&1014{c3,t3}=t2;!&1015{c4,c5}=t3;(c0 (c1 (c2 (c3 (c4 (c5 x)))))) S) Z)", "nf": "(S (S (S (S (S (S Z))))))", "ref_interactions": 7}, {"name": "church_exp_2_2", "term": "((\u03bbf.\u03bbx.!&1001{c0,c1}=f;(c0 (c1 x)) \u03bbf.\u03bbx.!&1002{c0,c1}=f;(c0 (c1 x))) S)", "nf": "\u03bba.(S (S (S (S a))))", "ref_interactions": 21}, {"name": "church_exp_3_2", "term": "((\u03bbf.\u03bbx.!&1001{c0,t0}=f;!&1002{c1,c2}=t0;(c0 (c1 (c2 x))) \u03bbf.\u03bbx.!&1003{c0,c1}=f;(c0 (c1 x))) S)", "nf": "\u03bba.(S (S (S (S (S (S (S (S a))))))))", "ref_interactions": 42}, {"name": "church_exp_2_3", "term": "((\u03bbf.\u03bbx.!&1001{c0,c1}=f;(c0 (c1 x)) \u03bbf.\u03bbx.!&1002{c0,t0}=f;!&1003{c1,c2}=t0;(c0 (c1 (c2 x)))) S)", "nf": "\u03bba.(S (S (S (S (S (S (S (S (S a)))))))))", "ref_interactions": 36}, {"name": "church_exp_3_3", "term": "((\u03bbf.\u03bbx.!&1001{c0,t0}=f;!&1002{c1,c2}=t0;(c0 (c1 (c2 x))) \u03bbf.\u03bbx.!&1003{c0,t0}=f;!&1004{c1,c2}=t0;(c0 (c1 (c2 x)))) S)", "nf": "\u03bba.(S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S a)))))))))))))))))))))))))))", "ref_interactions": 91}, {"name": "church_exp_4_2", "term": "((\u03bbf.\u03bbx.!&1001{c0,t0}=f;!&1002{c1,t1}=t0;!&1003{c2,c3}=t1;(c0 (c1 (c2 (c3 x)))) \u03bbf.\u03bbx.!&1004{c0,c1}=f;(c0 (c1 x))) S)", "nf": "\u03bba.(S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S a))))))))))))))))", "ref_interactions": 71}, {"name": "church_exp_2_4", "term": "((\u03bbf.\u03bbx.!&1001{c0,c1}=f;(c0 (c1 x)) \u03bbf.\u03bbx.!&1002{c0,t0}=f;!&1003{c1,t1}=t0;!&1004{c2,c3}=t1;(c0 (c1 (c2 (c3 x))))) S)", "nf": "\u03bba.(S (S (S (S (S (S (S (S (S (S (S (S (S (S (S (S a))))))))))))))))", "ref_interactions": 55}, {"name": "church_not_parity_2", "term": "(((\u03bbf.\u03bbx.!&1001{c0,c1}=f;(c0 (c1 x)) \u03bbp.\u03bbt.\u03bbf.((p f) t)) \u03bba.\u03bbb.a) X)", "nf": "\u03bba.X", "ref_interactions": 17}, {"name": "church_not_parity_3", "term": "(((\u03bbf.\u03bbx.!&1001{c0,t0}=f;!&1002{c1,c2}=t0;(c0 (c1 (c2 x))) \u03bbp.\u03bbt.\u03bbf.((p f) t)) \u03bba.\u03bbb.a) X)", "nf": "\u03bba.a", "ref_interactions": 28}, {"name": "church_not_parity_4", "term": "(((\u03bbf.\u03bbx.!&1001{c0,t0}=f;!&1002{c1,t1}=t0;!&1003{c2,c3}=t1;(c0 (c1 (c2 (c3 x)))) \u03bbp.\u03bbt.\u03bbf.((p f) t)) \u03bba.\u03bbb.a) X)", "nf": "\u03bba.X", "ref_interactions": 39}];

// ── random closed-ish term generator (termination-biased) ─────────────────
function genTerm(rt, rnd, depth, bound, labCounter, used = new Set()) {
  const r = rnd();
  if (depth <= 0 || r < 0.22) {
    const avail = bound.filter((n) => !used.has(n));       // AFFINE: each binder used at most once
    if (avail.length && rnd() < 0.7) {
      const pick = avail[Math.floor(rnd() * avail.length)];
      used.add(pick); return Var(pick);
    }
    return Var("free:" + "SZX"[Math.floor(rnd() * 3)]);
  }
  if (r < 0.44) {                                   // Lam
    const u = rt.fresh();
    return Lam(u, genTerm(rt, rnd, depth - 1, bound.concat(u), labCounter, used));
  }
  if (r < 0.70) {                                   // App
    return App(genTerm(rt, rnd, depth - 1, bound, labCounter, used),
               genTerm(rt, rnd, depth - 1, bound, labCounter, used));
  }
  if (r < 0.85) {                                   // Sup
    return Sup(labCounter.n++,
      genTerm(rt, rnd, depth - 1, bound, labCounter, used),
      genTerm(rt, rnd, depth - 1, bound, labCounter, used));
  }
  const a = rt.fresh(), b = rt.fresh();             // Dup
  return Dup(labCounter.n++, a, b,
    genTerm(rt, rnd, depth - 1, bound, labCounter, used),
    genTerm(rt, rnd, depth - 2, bound.concat(a, b), labCounter, used));
}
// ═══ AUDIT-SEM-BUDGET: GPT's round-6B witness, reproduced pre-fix ═════════
const TERM = "(λx.x X)";
const frt = new FloatRt();
const root = extrude(frt, parse(frt, TERM));
const enabled0 = findFloatRedexes(frt, root, PLANE_POOL_FREE).length;
const film = newSemFilm();
sealSemFilm(film, frt, root, { termination: "BUDGET_EXHAUSTED", steps: 0, last_frame: "genesis",
  planes: [...PLANE_POOL_FREE], budget: 999, remaining_work: 424242 });
const id1 = film.film_id;
const r1 = replaySemFilm(TERM, film, FloatRt);
film.terminal.budget = 1; film.terminal.remaining_work = -7;   // no reseal
const id2 = semFilmIdOf(film.terminal);
const r2 = replaySemFilm(TERM, film, FloatRt);
console.log("AUDIT-SEM-BUDGET");
console.log("enabled0:", enabled0);
console.log("budget_mutation_preserves_id:", id1 === id2);
console.log("r1.ok:", r1.ok, "| r2.ok:", r2.ok);
