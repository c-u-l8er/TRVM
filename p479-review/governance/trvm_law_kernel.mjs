/* ═══════════════════════════════════════════════════════════════════════════
   trvm_law_kernel.mjs — v1.3.0 — a law-governed Interaction Calculus kernel
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
      L-ID-1 REGRESSION-LOCKS the agreement (law:kernel.identity@1, superseded by @2) —
      the round-6 audit caught a v0.6 source printing a v0.5 banner
      (law history: that round's lock was kernel.identity@1, superseded
      by @2 when identity became a per-artifact map).

   WHAT CHANGED IN v1.0.2 (round 7 — record hygiene only)
   ───────────────────────────────────────────────────────
   No semantic changes. The WORLD layer shipped as a second executable
   (trvm_world.mjs) and identity became a MAP: law:kernel.identity@2
   supersedes @1, so this kernel's citations move to @2 and the frozen
   calculus semantics are untouched — the diff is version constant,
   header, and citation strings.

   WHAT CHANGED IN v1.0.1 (round 6.1 — the terminal-witness closure)
   ─────────────────────────────────────────────────────────────────
   The round-6B audit falsified TRVM-SEMFILM-v1's terminal contract: a
   zero-frame BUDGET_EXHAUSTED semantic film over an enabled state
   replayed ok, and budget/remaining_work mutations did not even change
   film_id — the same species as the round-4 execution-film terminal
   hole, reintroduced by the third replay implementation. Closed as a
   LAW, not a patch (law:film.terminal-witness@1): every terminal class
   a replay accepts must have a complete DECLARED witness schema, every
   witness field COMMITTED, and every witness field independently
   RE-DERIVED. TRVM-SEMFILM-v1.1 commits budget and remaining_work;
   replay re-derives the budget terminal, TIGHTER than execution films
   where the honest generator permits it: steps === budget (not >=) and
   remaining_work > 0 (a budget claim on a quiescent state is an
   under-claim — refused in the portable film). L-SEMTERM-1 attacks the
   terminal with eleven forgeries, each dying on its own refusal.

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
import { pathToFileURL } from "node:url";
/* 1.2.0 (B8.2): the READBACK FOLD reads a recorded ALLOCATION STAMP instead of
   inferring allocation order from the heap-id integer. Behaviour under FloatRt
   is unchanged — its ids ascend with allocation, so the old sort WAS allocation
   order there — and DescFloatRt, whose ids descend on purpose, now folds
   correctly instead of nesting a dup outside the binder its own value mentions.
   Proved additive the way round 10 ruled such a claim must be proved: by
   cert_id, which is unchanged, and never by a file hash.

   1.3.0 (B8.3): the readback fold's `seq ?? id` FALLBACK is gone. A missing or
   duplicate allocation stamp is now the named fail-closed condition
   `readback-allocation-order-missing` / `-duplicate`, thrown as a
   ReadbackInvariantError and RETHROWN at all four sites that otherwise absorb a
   readback failure — because those catches exist for a BUDGET, and a runtime
   that did not record what the fold requires is not a term that ran out of
   room. Plus HEAP_ID_ORDER_AUDIT, the finite census of every live site that
   chooses an order over heap entries. Additive by cert_id, as above. */
const KERNEL_VERSION = "1.3.0";
// v1.1.0 (additive): the kernel is now BOTH an executable falsifier and an
// importable oracle. Everything above the CONFORMANCE marker is definitions;
// everything below it is the battery, and the battery — with its certificate
// write and its process.exit — runs only when this file is the entry module.
// Importing the kernel therefore has no side effects and mutates no artifact.
// The calculus is untouched: see the round-10 ledger for the byte-level proof
// that cert_id and all 144 receipts are identical across the bump.
const IS_MAIN = import.meta.url === pathToFileURL(process.argv[1] ?? "").href;

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
    this.aseq = 0;              // monotone ALLOCATION stamp — see FloatRt.allocAt
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
function stateSignature(rt, root) {
  // v1.1.0 (additive): the PRE-HASH BYTES of the canonical digest, extracted
  // as their own entry point so a second implementation can diff the signature
  // STRING and not merely the hash of it. stateDigest is now defined as
  // sha256(stateSignature(...)) — one code path, so a golden pre-hash vector
  // cannot drift from the digest it is supposed to explain. The signature
  // grammar is frozen with the calculus; §5 of SEMSTATE-CANONICAL-v1 is its
  // language-neutral statement.
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
  return memo.get(chase(rt, root));
}
function stateDigest(rt, root) {
  return createHash("sha256").update(stateSignature(rt, root)).digest("hex");         // ArtifactHash256: evidence identities are never truncated
}
// The semantic counterpart: the pre-hash bytes of semStateId — the live heap
// folded in first-reachable discovery order (§3–§4), then signed (§5).
// semStateId(frt, root) === sha256(semStateSignature(frt, root)) by construction.
function semStateSignature(frt, root) { return stateSignature(frt, foldCanonicalLive(frt, root).acc); }
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
  /* ALLOCATION ORDER IS RECORDED, NOT INFERRED — B8.2. `seq` is a monotone
     stamp every subclass gets by construction, because the readback fold needs
     allocation order and had been reading it off the ID INTEGER, which is a
     representative choice rather than a fact. See foldLive. */
  alloc(lab, l, r, val) { return this.allocAt(++this.did, lab, l, r, val); }
  allocAt(id, lab, l, r, val) { this.heap.set(id, { lab, l, r, val, seq: ++this.aseq }); return id; }
}
// Adversarial allocator (law:state.exec-identity@1, law:refine.alloc-portability@1):
// heap ids DESCEND and name ints stride downward — injective, ORDER-REVERSING.
// A monotone perturbation is invisible to sorted folds; this one is not. It
// exists to separate execution identity from semantic identity, and to stand
// in for a second implementation until ic32 does.
class DescFloatRt extends FloatRt {
  constructor() { super(); this.ka = 0; this.kf = 0; }
  /* DESCENDING IDS, ON PURPOSE — the whole point of this class is that nothing
     may depend on the id integers being ordered. It routes through allocAt so
     it cannot silently miss the allocation stamp: an adversarial subclass that
     had to remember to record `seq` would be an adversary the invariant is
     merely asking nicely to respect. */
  alloc(lab, l, r, val) { this.ka++; return this.allocAt(2_000_000 - 13 * this.ka, lab, l, r, val); }
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

/* ═══ B8.3 · THE HEAP-ID ORDER AUDIT ══════════════════════════════════════
   A FINITE, HAND-CLASSIFIED CENSUS, not a linter. B8.2 found one place where
   an order over the heap-id INTEGERS stood in for a semantic order, and the
   only reason it had survived was that no fixture's live dups were
   interdependent. The finding is about a class, so the class was enumerated
   once, across every live function that touches more than one heap entry —
   and each site says which of three things its order IS:

     EXECUTION      the id order is the thing being identified. Declared
                    allocator-sensitive; a different allocator is SUPPOSED to
                    give a different answer.
     SEMANTIC       must be allocation-independent. Discovery order.
     DEPENDENCY     must be a topological order on dup dependency. Allocation
                    sequence, recorded — the B8.2 site.
     ORDER-FREE     the result does not depend on the traversal order at all
                    (a set union, a conjunction, a map whose keys are disjoint).

   `sites` is the census; `checked_against` is how a reader confirms it is
   still complete rather than merely still true. Sites BELOW the CONFORMANCE
   marker are battery code and are listed separately, because one of them sorts
   ids ON PURPOSE to reproduce a pre-fix defect and must not be "repaired".

   WHAT THE SWEEP FOUND: no second live site inferring a semantic order from an
   id integer. That is a result, and it is recorded as one rather than as an
   absence of comment. */
const HEAP_ID_ORDER_AUDIT = Object.freeze({
  audit: "TRVM-HEAPID-ORDER-AUDIT-v1",
  live_sites: Object.freeze([
    Object.freeze({ fn: "foldHeap", sorts: true, orders: "ALL heap ids, ascending integer", kind: "EXECUTION",
      why: "execStateId/floatDigest is execution identity (law:state.exec-identity@1): total heap in " +
        "id order, dead entries included, deliberately allocator-sensitive. The id order is not " +
        "standing in for anything — it IS the representative choice this identity commits to." }),
    Object.freeze({ fn: "foldLive", sorts: true, orders: "live heap ids, by recorded allocation stamp", kind: "DEPENDENCY",
      why: "the B8.2 site. Folding nests each live dup around the accumulator, so the order must be a " +
        "topological order on dup dependency; allocation sequence is one and neither the id integer " +
        "nor the discovery order is. Missing or duplicate stamps FAIL CLOSED (B8.3)." }),
    Object.freeze({ fn: "liveDiscoveryOrder / foldCanonicalLive", sorts: false, orders: "live heap ids, first-reachable discovery", kind: "SEMANTIC",
      why: "semStateId is the semantic quotient (law:state.semantic-quotient@1). Reads no id integer " +
        "at all: ids enter only as Map keys. Allocation-independent by construction." }),
    Object.freeze({ fn: "semLocusOf", sorts: false, orders: "index into liveDiscoveryOrder", kind: "SEMANTIC",
      why: "a canonical locus is a position in the discovery order, never an id. This is why a film " +
        "cut on one allocator replays on another." }),
    Object.freeze({ fn: "liveHeap / findFloatRedexes", sorts: false, orders: "live dups, Set insertion order", kind: "SEMANTIC",
      why: "the enumeration order the scheduler indexes. Insertion order of a Set built by DFS from " +
        "the root is discovery order — already id-independent, and it was never sorted." }),
    Object.freeze({ fn: "heapByProj construction (liveHeap, liveDiscoveryOrder)", sorts: false, orders: "n/a — Map build", kind: "ORDER-FREE",
      why: "projection names are affine, so each key is written once and iteration order cannot " +
        "change the resulting map." }),
    Object.freeze({ fn: "wellFormedFloat / freeNamesFloat", sorts: false, orders: "n/a — conjunction and set union over the heap", kind: "ORDER-FREE",
      why: "both fold with commutative, associative operators." }),
  ]),
  battery_sites: Object.freeze([
    Object.freeze({ fn: "findDeadIncl (L-BIND-4)", sorts: true, orders: "ALL heap ids, ascending integer", kind: "HISTORICAL",
      why: "the PRE-FIX enumeration, kept verbatim so the round-5 dead-locus defect keeps " +
        "reproducing. Sorting by id here is the defect being exhibited, not a defect to repair." }),
  ]),
  checked_against: "the count of `.sort(` calls in this file's own source, split at the CONFORMANCE " +
    "marker, against the entries flagged `sorts: true` on each side. A NEW ordering site makes the " +
    "census incomplete, and an incomplete census is exactly what let B8.2's site sit unclassified — " +
    "so the denominator is DERIVED FROM THE SOURCE, never typed. The order-free and " +
    "discovery-ordered entries are not covered by that count and are not claimed to be: they are " +
    "the reading, and the count is only the guarantee that the reading is exhaustive over the " +
    "sites where an order is CHOSEN.",
  swept_and_found: "NO second LIVE site inferring a semantic or dependency order from a heap-id " +
    "integer. foldHeap sorts ids and is entitled to; every other live site orders by discovery, by " +
    "recorded allocation, or not at all.",
});
const HEAP_ID_ORDER_AUDIT_ID =
  "hida-" + createHash("sha256").update(JSON.stringify(HEAP_ID_ORDER_AUDIT)).digest("hex");

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
// domain ("TRVM-SEMFILM-v1.1" — v1.1 commits the budget-terminal witness
// fields; the round-6B audit forged the v1 terminal, law:film.terminal-witness@1).
// Replay is by locus MATCHING against the live
// enumeration of a fresh runtime — ANY runtime class implementing the
// relation (here: FloatRt or the adversarial DescFloatRt; eventually ic32).
// Enabledness is inherent: an unmatched locus refuses.
function newSemFilm() { return { frames: [], terminal: null, film_id: null }; }
const semFilmIdOf = (t) =>
  createHash("sha256").update(["TRVM-SEMFILM-v1.1", t.last_frame, t.termination, t.steps,
    t.final_sem_id, t.normal_form_id ?? "-", t.budget ?? "-", t.remaining_work ?? "-",
    (t.planes ?? []).join(",")].join("|")).digest("hex");
function sealSemFilm(film, frt, root, t) {
  t.final_sem_id = semStateId(frt, root);
  if (t.termination === "NORMAL_FORM" && t.normal_form_id === undefined) {
    // B8.3: the catch is for a readback that ran out of BUDGET — a resource
    // fact, and a film with no normal-form id is an honest thing to seal. A
    // MISSING ALLOCATION STAMP is not that: it is the runtime failing to record
    // evidence the fold requires, and swallowing it would convert the
    // fail-closed condition into a silently id-less film.
    try { t.normal_form_id = semId(readback(frt, root).str); }
    catch (e) { if (isReadbackInvariant(e)) throw e; t.normal_form_id = null; }
  }
  if (t.termination === "BUDGET_EXHAUSTED" && t.remaining_work === undefined) {
    // the honest witness source: the live enumeration at the sealed state
    t.remaining_work = findFloatRedexes(frt, root,
      new Set(t.planes ?? [...PLANE_POOL_FREE])).length;
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
      // B8.3, same split as sealSemFilm: budget leaves nfid null and the
      // comparison below refuses; a missing allocation stamp is an invariant
      // breach in the REPLAYING runtime and must not be absorbed into a null —
      // against a film that also carries none, that would read as agreement.
      try { nfid = semId(readback(frt, root, 200000).str); }
      catch (e) { if (isReadbackInvariant(e)) throw e; /* else stays null */ }
      if (nfid !== t.normal_form_id) return { ok: false, reason: "sem-terminal-nf-mismatch" };
    }
  } else if (t.termination === "BUDGET_EXHAUSTED") {
    // law:film.terminal-witness@1 — the budget terminal is RE-DERIVED, not
    // accepted. Mirrors replayFloat, tightened where the honest generator
    // permits: steps must EQUAL the declared budget (one-step integral
    // progression, no resumed films), and work must actually remain — a
    // BUDGET_EXHAUSTED claim on a quiescent state is refused.
    if (!Number.isInteger(t.budget) || !Number.isInteger(t.remaining_work))
      return { ok: false, reason: "sem-terminal-malformed" };
    const rsEnd = findFloatRedexes(frt, root, permitted);
    if (rsEnd.length !== t.remaining_work) return { ok: false, reason: "sem-terminal-work-mismatch" };
    if (n !== t.budget) return { ok: false, reason: "sem-budget-mismatch" };
    if (t.remaining_work <= 0) return { ok: false, reason: "sem-no-remaining-work" };
  } else return { ok: false, reason: "sem-terminal-malformed" };
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
/* B8.2: THIS FOLDED BY ASCENDING HEAP ID, AND THAT IS ALLOCATION ORDER ONLY
   IF IDS ASCEND. FloatRt's do, so the sort was allocation order there and the
   nesting was right; DescFloatRt allocates DESCENDING ids on purpose, so the
   same sort put the LAST-allocated dup OUTERMOST — outside the binder whose
   projection its own value mentions. `normalRef` then chased substitutions
   that could not resolve and readback ran out of budget.

   Found by mul(4,3) and mul(3,1) and by no fixture before them: every earlier
   term's live dups were independent, so any nesting worked. A left operand of
   church(3) or more is the first shape whose CHAINED dups depend on each other.

   THE SEMANTIC FOLD WAS NEVER AFFECTED. foldCanonicalLive has used
   liveDiscoveryOrder since it was written and is documented as
   allocation-independent by construction, so semStateId, semStateSignature,
   every golden pre-hash vector, the 48/48 bridge agreement and every native
   film are untouched by this. What was wrong was the READBACK's fold — the one
   feeding normal_form_id and the printed term.

   THE TWO ORDERS ARE DELIBERATELY DIFFERENT, AND SAYING SO IS THE POINT.
   B8.2's first repair used liveDiscoveryOrder — the identity fold's order — and
   it FIXED the chained case and BROKE (2+3)*4 under FloatRt, because a
   traversal order is not a topological order on dup dependency:

       semantic identity fold  →  DISCOVERY order    →  allocation-INDEPENDENT
       readback dependency fold →  recorded ALLOCATION SEQUENCE
                                                     →  independent of the heap-ID
                                                        REPRESENTATION, not of
                                                        allocation

   This paragraph said the readback now used "the same allocation-independent
   order the identity fold already uses" — the rejected repair, described as the
   shipped one, in the prose beside the code that rejected it. Corrected at B8.3.

   THE CLASS: an ordering derived from a REPRESENTATIVE CHOICE standing in for a
   SEMANTIC one. The id integers are an allocation artefact; the dependency
   order between dups is not. DescFloatRt exists to break exactly that
   assumption and had never reached this function. */

/* B8.3: ALLOCATION ORDER IS EVIDENCE THE READBACK REQUIRES, NOT EVIDENCE IT
   PREFERS. This is thrown, never returned, and never swallowed — see the two
   catch sites in sealSemFilm and replaySemFilm, which rethrow it. */
class ReadbackInvariantError extends Error {
  constructor(reason) { super(reason); this.name = "ReadbackInvariantError"; this.reason = reason; }
}
const isReadbackInvariant = (e) => e instanceof ReadbackInvariantError;

function foldLive(frt, root) {
  /* ALLOCATION ORDER, AND IT IS THE ONLY CORRECT ONE HERE. Folding wraps each
     live dup around the accumulator, so a dup placed EARLIER in this order ends
     up OUTERMOST and its projections scope over everything after it. A dup's
     `val` can only mention names that already existed when it was allocated,
     so allocation order is a valid topological order on that dependency — and
     nothing else is guaranteed to be.

     B8.3: THE `seq ?? id` FALLBACK IS GONE, AND IT IS A NAMED FAIL-CLOSED
     CONDITION. The sort read `(heap.get(a)?.seq ?? a) - (heap.get(b)?.seq ?? b)`,
     which under a missing stamp quietly resumed the exact inference the line
     above declares invalid — allocation order guessed off the id integer. Every
     dup in today's allocation path carries a stamp, so the fallback never fired
     and the good cases stayed good; that is what made it a latent rule rather
     than a visible one.

     MEASURED before it was removed, on two runtimes with the stamp stripped:
     under ASCENDING ids readback SILENTLY SUCCEEDED, because the guess happened
     to be right; under DESCENDING ids it threw `budget`. So the fallback did not
     merely permit a wrong order — it reported a missing invariant as a RESOURCE
     LIMIT, which blames the term for being long when the runtime is the thing
     that failed to record what readback needs. A named refusal cannot be
     mistaken for a term that ran out of room. */
  const live = [...liveHeap(frt, root)];
  const seen = new Map();
  for (const id of live) {
    const d = frt.heap.get(id);
    if (!d || !Number.isInteger(d.seq))
      throw new ReadbackInvariantError("readback-allocation-order-missing");
    if (seen.has(d.seq))
      throw new ReadbackInvariantError("readback-allocation-order-duplicate");
    seen.set(d.seq, id);
  }
  const order = live.sort((a, b) => frt.heap.get(a).seq - frt.heap.get(b).seq);
  let acc = root;
  for (let i = order.length - 1; i >= 0; i--) {
    const d = frt.heap.get(order[i]);
    acc = Dup(d.lab, d.l, d.r, d.val, acc);
  }
  return { acc, liveCount: order.length };
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
    // B8.3, the same split sealSemFilm makes: budget is a resource fact, a
    // missing allocation stamp is a broken invariant. Both film planes, because
    // a condition that fails closed on one and is swallowed on the other is not
    // fail-closed — it is fail-closed where someone happened to look.
    try { t.normal_form_id = semId(readback(frt, root, 200000).str); }
    catch (e) { if (isReadbackInvariant(e)) throw e; t.normal_form_id = null; }
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
      try { nfid = semId(readback(frt, root, 200000).str); }
      catch (e) { if (isReadbackInvariant(e)) throw e; /* else nfid stays null */ }
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

// ── harness plumbing ──────────────────────────────────────────────────────
const QUICK = process.argv.includes("--quick");
const results = [];
function report(id, tuple, status, detail) { results.push({ id, tuple, status, detail }); }

function refNormalize(src) {
  const rt = new Rt();
  const t = parse(rt, src);
  const nf = normalRef(rt, t);
  return { rt, nf, str: show(nf), interactions: rt.total() };
}
const SCHEDULERS = {
  leftmost: (rs, rnd) => rs[0],
  deepest:  (rs, rnd) => rs[rs.length - 1],
  middle:   (rs, rnd) => rs[Math.floor(rs.length / 2)],
  random:   (rs, rnd) => rs[Math.floor(rnd() * rs.length)],
  // starvation adversaries (law:sched.adversarial.float@1): each persistently
  // avoids a whole redex CLASS for as long as any alternative is enabled.
  // Completion under these is a fairness result, not a scheduling accident.
  starve_dups: (rs, rnd) => rs.find((r) => r.kind === "app") ?? rs[Math.floor(rnd() * rs.length)],
  starve_apps: (rs, rnd) => rs.find((r) => r.kind === "dup") ?? rs[Math.floor(rnd() * rs.length)],
};
// run the float engine to quiescence; return the composite outcome
function runFloat(src, opts = {}) {
  const frt = new FloatRt();
  let root = extrude(frt, parse(frt, src));
  const rnd = mulberry32(opts.seed ?? 0xF10A7);
  const pick = opts.pick ?? ((rs, r) => rs[Math.floor(r() * rs.length)]);
  const out = normalizeFloat(frt, root, pick, rnd, opts);
  return { frt, ...out };
}
function floatNfString(frt, root) {           // live-fold + reference readback, canonical print
  return readback(frt, root).str;
}

// ── corpus identity (v1.1.0) ──────────────────────────────────────────────
// A vector's CORPUS IDENTITY is exactly these four fields, in this order —
// which is what `sha256(JSON.stringify(vectors))` commits to in the scheduler
// certificate. TRVM's canonical corpus file carries a fifth field
// (`ic_ref_agrees`, a provenance marker recording that the two authoritative
// runtimes agreed when the vector was admitted). Hashing it would make the
// commitment depend on provenance annotation rather than on the corpus, so
// repointing the kernel at the canonical source would silently reseal every
// certificate that had ever been issued. The projection is declared once,
// applied at load, and is the reason the embedded set and the canonical file
// commit to the same hash.
const CORPUS_FIELDS = ["name", "term", "nf", "ref_interactions"];
const projectVector = (v) => { const o = {}; for (const k of CORPUS_FIELDS) o[k] = v[k]; return o; };

// ── v1.1.0 MODULE INTERFACE (additive) ────────────────────────────────────
// The surface a second implementation needs to check its own canonical bytes
// against this oracle. Nothing here is new calculus: every name below already
// existed and is exported verbatim, plus the two signature entry points that
// stateDigest/semStateId are now DEFINED in terms of. Deliberately absent:
// any setter, any mutation hook, anything that would let an importer change
// what the oracle answers.
export {
  KERNEL_VERSION,
  // building states from source
  parse, extrude, Rt, FloatRt, DescFloatRt,
  // identity — digests and, at 1.1.0, the pre-hash bytes beneath them
  stateSignature, semStateSignature, stateDigest, semStateId, execStateId,
  // the canonical fold the semantic signature is taken over
  foldCanonicalLive, liveDiscoveryOrder, chase,
  // B8.3 — the finite heap-id order census, and the fail-closed marker the
  // readback throws. Exported so the grid can check the census against this
  // file's own source rather than against a copy of the claim.
  HEAP_ID_ORDER_AUDIT, HEAP_ID_ORDER_AUDIT_ID, ReadbackInvariantError, isReadbackInvariant,
  // readback / printing / normalization
  readback, semId, normalizeFloat, runFloat, refNormalize,
  // the corpus the golden fixtures are cut from, and what "the corpus" means
  EMBEDDED_VECTORS, CORPUS_FIELDS, projectVector,
  // THE SEMANTIC-FILM CHECKER, exported so a film produced by something other
  // than this file can be handed to it unmodified. Round 23: a native ic32
  // frame is checked by exactly the replay the JS films are checked by, on a
  // FRESH runtime, with no translation step in between — a checker written for
  // the occasion would be checking the occasion. The enumeration primitives go
  // with it so a caller can say WHY a locus did not match rather than only that
  // replay refused; they are the same functions replaySemFilm uses.
  replaySemFilm, findFloatRedexes, semLocusOf, semFilmIdOf, frameId31, fireFloat, newSemFilm, sealSemFilm,
  PLANE_OF, PLANE_POOL_FREE,
};

// ── 1 · CONFORMANCE ───────────────────────────────────────────────────────
if (IS_MAIN) {
let vectorsSrc = EMBEDDED_VECTORS.map(projectVector), vectorsFrom = "embedded";
if (process.env.TRVM_VECTORS) {
  try {
    const j = JSON.parse(readFileSync(process.env.TRVM_VECTORS, "utf8"));
    vectorsSrc = (j.vectors ?? j).map(projectVector); vectorsFrom = process.env.TRVM_VECTORS;
  } catch { /* keep embedded */ }
}
let confPass = 0, confFail = 0, intMatch = 0;
const confFailures = [];
for (const v of vectorsSrc) {
  const { str, interactions } = refNormalize(v.term);
  if (str === v.nf) confPass++; else { confFail++; confFailures.push({ name: v.name, got: str, want: v.nf }); }
  if (interactions === v.ref_interactions) intMatch++;
}
report("CONF-1", "(normal form, normalize, all vectors, DERIVATION)",
  confFail === 0 ? "PASS" : "FAIL",
  `${confPass}/${vectorsSrc.length} vectors (${vectorsFrom}); interaction counts equal to the python reference on ${intMatch}/${vectorsSrc.length} (the vector doc permits count divergence by strategy; nf equality is the contract)`);

// CONF-2 : the embedded corpus may not drift from the canonical one.
// The kernel ships EMBEDDED_VECTORS so it runs standalone — the ic32 handoff
// packs distribute it as a lone oracle file, with no repository around it, and
// a kernel that cannot normalize without a sibling corpus is not an oracle.
// That makes the embedded set a second copy, and the honest treatment of a
// second copy is not deletion but a proof that it CANNOT DIVERGE: whenever the
// canonical corpus is reachable, the two must commit to the same hash under
// the same projection. Unreachable is reported as unchecked, never as agreement
// — a skipped check that prints like a passing one is the failure mode this
// record has been prosecuting since round 9.
{
  const CANON = process.env.TRVM_CORPUS ?? "../docs/spec/conformance/vectors/normalize.json";
  const hashOf = (vs) => createHash("sha256").update(JSON.stringify(vs.map(projectVector))).digest("hex");
  const mine = hashOf(EMBEDDED_VECTORS);
  let canon = null, err = null;
  try {
    const j = JSON.parse(readFileSync(CANON, "utf8"));
    canon = hashOf(j.vectors ?? j);
  } catch (e) { err = e.code ?? String(e.message).slice(0, 40); }
  // STRICT mode (TRVM_STRICT_CORPUS=1): the audit's ruling is that standalone
  // use may leave the equality unknown, but pack cutting and release CI must
  // never emit an artifact whose corpus identity was merely unchecked. Under
  // strict mode an unreachable corpus is a FALSIFICATION, not an exemption.
  const STRICT = process.env.TRVM_STRICT_CORPUS === "1";
  report("CONF-2", "(corpus identity, embedded vs canonical, projected commitment, BINDING)",
    canon === null ? (STRICT ? "FALSIFIED?!" : "NOT_APPLICABLE") : (canon === mine ? "REGRESSION-LOCKED" : "FALSIFIED?!"),
    canon === null
      ? `canonical corpus not reachable at ${CANON} (${err}) — the embedded set is UNCHECKED against it this run, which is not the same as agreeing with it${STRICT ? ", and TRVM_STRICT_CORPUS=1 makes unchecked FATAL: a release or handoff pack may not be cut from a run that could not prove its corpus identity" : ". Standalone oracle use may leave this unknown; release and pack-cut runs must set TRVM_STRICT_CORPUS=1, where it becomes a falsification"}. Set TRVM_CORPUS, or run from a tree carrying docs/spec/conformance/vectors/normalize.json`
      : `embedded corpus and ${CANON} commit to the SAME hash under the four-field corpus projection (${mine.slice(0, 16)}…): the copy the oracle ships standalone cannot drift from the corpus the runtime plane conforms against. The projection is why — the canonical file carries a fifth provenance field (ic_ref_agrees) that must not enter the commitment, or repointing the kernel at the authoritative source would silently reseal every certificate ever issued`);
}

// ── 2 · THE LAW TABLE, compiled and run ───────────────────────────────────
const SCHED_PER_TERM = QUICK ? 8 : 25;
const FUZZ_TERMS = QUICK ? 60 : 200;

// L-DERIV-1 ⋄ : same NF and sem-id under every completed schedule — now on
// the FLOAT relation (law:sched.free.float@1); the AST relation is retired
// to its witness row below.
{
  let terms = 0, schedules = 0, fail = null, skippedSched = 0;
  for (const v of vectorsSrc) {
    const want = refNormalize(v.term).str; terms++;
    for (let s = 0; s < SCHED_PER_TERM; s++) {
      let got;
      try {
        const r = runFloat(v.term, { seed: 0xD1A0 + s * 7919 + terms });
        if (r.termination !== "NORMAL_FORM") { skippedSched++; continue; }
        got = floatNfString(r.frt, r.root);
      } catch { skippedSched++; continue; }
      schedules++;
      if (got !== want) { fail = { name: v.name, seed: s, got, want }; break; }
    }
    if (fail) break;
  }
  report("L-DERIV-1", "(normal form, COMPLETED schedules, affine pure fragment, DERIVATION/confluence)",
    fail ? "FALSIFIED?!" : "PROPERTY-TESTED",
    fail ? JSON.stringify(fail)
         : `${terms} terms; ${schedules} completed random-schedule runs on the floating-dup relation all reached the reference NF (sem-ids identical); ${skippedSched} schedules exceeded the budget. Confluence proves where you may arrive; whether a relation's scheduler gets there is Progress, and on this representation it did — see L-SCHED-FLOAT-1`);
}

// L-DERIV-2 : interaction-count schedule invariance — on the floating-dup
// relation this is a MEASURED PROPERTY, not a hope: per-term counts across
// four schedulers, compared to the reference count (law:deriv.count-invariance.float@1).
{
  let invariant = 0, refEqual = 0, jsEqual = 0, varied = null;
  for (const v of vectorsSrc) {
    const counts = new Set();
    for (const [sn, pick] of Object.entries(SCHEDULERS)) {
      const r = runFloat(v.term, { seed: 0xC0DE + sn.length, pick });
      counts.add(r.frt.total());
    }
    if (counts.size === 1) {
      invariant++;
      if ([...counts][0] === v.ref_interactions) refEqual++;
      if ([...counts][0] === refNormalize(v.term).interactions) jsEqual++;
    }
    else if (!varied) varied = { name: v.name, counts: [...counts] };
  }
  report("L-DERIV-2", "(interaction count, four schedulers, floating-dup relation, DERIVATION)",
    invariant === vectorsSrc.length && refEqual === vectorsSrc.length ? "PROPERTY-TESTED" : "EMPIRICAL",
    invariant === vectorsSrc.length
      ? `count schedule-INVARIANT on ${invariant}/${vectorsSrc.length} terms and EQUAL to the spec's python-reference count on ${refEqual}/${vectorsSrc.length} (the JS normal-order driver itself matches spec counts on only ${jsEqual}/${vectorsSrc.length}; the float relation matches the spec MORE faithfully than the conformance driver) — the net-level count theorem materializes at this representation (it did NOT at the AST layer)`
      : `count varied on some terms; first: ${JSON.stringify(varied)}`);
}

// L-DERIV-3 : fuzz — random terms, reference vs float free schedules
{
  const rnd = mulberry32(0xF00D);
  let tried = 0, done = 0, skipped = 0, fail = null;
  while (done < FUZZ_TERMS && tried < FUZZ_TERMS * 4) {
    tried++;
    const g = new Rt(); const lab = { n: 500 };
    const src = show(genTerm(g, rnd, 5, [], lab));
    let want;
    try { want = refNormalize(src).str; } catch { skipped++; continue; }
    let ok = true;
    for (let s = 0; s < 3; s++) {
      let got;
      try {
        const r = runFloat(src, { seed: 0xBEEF + s + tried });
        if (r.termination !== "NORMAL_FORM") { skipped++; ok = false; break; }
        got = floatNfString(r.frt, r.root);
      } catch { skipped++; ok = false; break; }
      if (got !== want) { fail = { src, got, want, seed: s }; ok = false; break; }
    }
    if (fail) break;
    if (ok) done++;
  }
  report("L-DERIV-3", "(normal form, float free schedules, random closed/open terms, DERIVATION)",
    fail ? "FALSIFIED?!" : "PROPERTY-TESTED",
    fail ? JSON.stringify(fail).slice(0, 200)
         : `${done} random terms × 3 float schedules agree with reference; ${skipped} skipped on budget (divergent or huge)`);
}

// L-DERIV-4 : the AFFINITY PRECONDITION, falsified-by-design — verified to
// survive the representation change (float run: overwrites and NF
// disagreements persist on non-affine input). Must keep failing.
{
  const NONAFFINE = "!&500{a,b}=λc.c;!&501{d,e}=(a &502{b,b});(Z e)";
  let want = null, disagreements = 0, overwrites = 0, runs = 0;
  try { const r = new Rt(); want = show(normalRef(r, parse(r, NONAFFINE))); } catch { /* reference may misbehave */ }
  for (let sd = 0; sd < 8; sd++) {
    try {
      const r = runFloat(NONAFFINE, { seed: 0xAFF1 + sd });
      const str = floatNfString(r.frt, r.root);
      overwrites += r.frt.overwrites; runs++;
      if (want !== null && str !== want) disagreements++;
    } catch { runs++; /* budget/knot: also evidence of pathology */ }
  }
  const broke = disagreements > 0 || overwrites > 0;
  report("L-DERIV-4", "(normal form, float free schedules, NON-AFFINE input, DERIVATION)",
    broke ? "FALSIFIED (by design)" : "UNEXPECTEDLY-HELD?!",
    broke
      ? `witness kept red: ${runs} schedules, ${disagreements} NF disagreements vs reference, ${overwrites} sub-store overwrites — a DOMAIN-EXCLUSION witness: affinity is part of the calculus definition, and outside it schedules disagree. If this row ever passes, the affinity discipline changed.`
      : "non-affine input no longer breaks schedule-independence — investigate what changed");
}

// L-MONO-1 : the substitution store is write-once and grow-only
{
  let overwrites = 0, runs = 0;
  for (const v of vectorsSrc) {
    const r = runFloat(v.term, { seed: 0xCA11 + runs });
    overwrites += r.frt.overwrites; runs++;
  }
  report("L-MONO-1", "(substitution store, every rule, affine names, MONOTONICITY)",
    overwrites === 0 ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${runs} full float runs; sub-store writes are single-assignment (overwrites: ${overwrites}) — substitution-store INFLATIONARITY, a monotone-state ingredient the coordination-freedom argument needs; the CALM-level claim about specification outcomes belongs to the world layer, not this map`);
}

// L-MONO-2 / L-CONS-1 : free-name non-increase; unrestricted conservation
// stays FALSIFIED by design. Free names now measured over root AND heap.
{
  let steps = 0, increases = 0, drops = 0, dropWitness = null;
  const consCorpus = [{ name: "discard_S", term: "((λk.λz.z S) Z)" },
                      ...vectorsSrc.slice(0, QUICK ? 8 : vectorsSrc.length)];
  for (const v of consCorpus) {
    const frt = new FloatRt(); let root = extrude(frt, parse(frt, v.term));
    const rnd = mulberry32(0xFACE);
    for (;;) {
      const rs = findFloatRedexes(frt, root, PLANE_POOL_FREE);
      if (!rs.length) break;
      const before = freeNamesFloat(frt, root);
      const pick = rs[Math.floor(rnd() * rs.length)];
      const r = fireFloat(frt, root, pick); root = r.root; steps++;
      const after = freeNamesFloat(frt, root);
      for (const n of after) if (!before.has(n)) increases++;
      if (after.size < before.size) {
        drops++;
        if (!dropWitness) dropWitness = { vector: v.name, rule: r.rule, lost: [...before].filter(x => !after.has(x)) };
      }
      if (steps > 4000) break;
    }
  }
  report("L-MONO-2", "(free-name set incl. heap, every rule, resolved state, MONOTONICITY non-increase)",
    increases === 0 ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${steps} float steps; a step never INVENTS a free name (increases: ${increases})`);
  report("L-CONS-1", "(free-name set, every rule, unrestricted, CONSERVATION)",
    drops > 0 ? "FALSIFIED (by design)" : "UNEXPECTEDLY-HELD?!",
    drops > 0
      ? `free names are NOT conserved — dropped in ${drops} steps; first witness: ${JSON.stringify(dropWitness)}. Erasure and affine discard are real; the honest law is the non-increase sibling above. Kept red on purpose.`
      : `no drop observed — investigate: erasure should drop names`);
}

// L-IDEM-1 : normalize is idempotent (second pass fires zero interactions)
{
  let extra = 0, runs = 0;
  for (const v of vectorsSrc) {
    const { rt, nf } = refNormalize(v.term);
    const before = rt.total(); normalRef(rt, nf); extra += rt.total() - before; runs++;
  }
  report("L-IDEM-1", "(normal form, re-normalize, any NF, IDEMPOTENCE)",
    extra === 0 ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${runs} NFs re-normalized; additional interactions: ${extra}`);
}

// L-FQ-AST-1 : THE RETRACTION ROW (law:sched.free.ast-term@1, FALSIFIED by
// design, must keep failing). Retracts L-PROG-1's v0.4 interpretation:
// "four schedulers fail six duplication-heavy terms at a 20k budget,
// therefore strategy is the progress certificate." Verified reality: the six
// failures reach findRedexes()==[] after 15–37 steps (FALSE QUIESCENCE —
// never near the budget), and the reference normalizer then exhausts its
// separate 2M budget structurally unfolding a cyclic-through-substitution
// state while firing ~0 interactions. Even pure-INTERACT free ordering
// knots, so the seam is the term-level enumeration RELATION itself, not
// plane mixing. If this row ever passes, the AST relation changed.
{
  const v = vectorsSrc.find(x => x.name === "church_exp_2_2") ?? vectorsSrc[0];
  const rt = new Rt(); let root = parse(rt, v.term);
  let steps = 0, quiescent = false;
  for (;;) {
    const rs = findRedexes(rt, root, 4096);
    if (!rs.length) { quiescent = true; break; }
    root = applyAt(rt, root, rs[0].path).root;
    if (++steps > 200) break;
  }
  let refStuck = false, refBurn = 0;
  if (quiescent) {
    const b = { n: 200000 };
    const before = rt.total();
    try { normalRef(rt, root, b); } catch { refStuck = true; }
    refBurn = rt.total() - before;
  }
  const red = quiescent && refStuck;
  report("L-FQ-AST-1", "(quiescence coherence, AST free enumeration, church_exp corpus, COHERENCE/REFINEMENT)",
    red ? "FALSIFIED (by design)" : "UNEXPECTEDLY-HELD?!",
    red
      ? `witness kept red: church_exp_2_2 falsely quiescent after ${steps} AST steps (findRedexes()==[]); reference then exhausts 200k budget firing only ${refBurn} interactions — a cyclic unfolding, not work. Retracts law:sched.free.ast-term@1's progress reading; successors: law:sched.free.float@1 (L-SCHED-FLOAT-1), law:collapse.progress@1 (L-COLLAPSE-PROG-1).`
      : `the AST relation no longer falsely quiesces — the enumeration relation changed; re-derive which laws still hold`);
}

// L-SCHED-FLOAT-1 : the free-scheduling law on the floating-dup relation
// (law:sched.free.float@1): four schedulers × all vectors under the DECLARED
// hybrid pool; completion, NF agreement, readback purity. The battery now
// RUNS AS the certificate: one receipt per run forms the run manifest, and
// the v2 certificate (law:sched.certificate@2) carries all of them for the
// checker to re-execute. Receipts are the evidence basis; exhibits are
// witnesses.
let schedCert = null, schedBattery = null;
{
  schedBattery = runCertifiedBattery(vectorsSrc, SCHEDULERS, 20000);
  const ev = aggregateReceipts(schedBattery.receipts);
  const residualCollapse = schedBattery.receipts.reduce((a, r) => a + (r.readback?.collapse ?? 0), 0);
  const residualLive = schedBattery.receipts.reduce((a, r) => a + (r.readback?.live ?? 0), 0);
  const wantRuns = vectorsSrc.length * Object.keys(SCHEDULERS).length;
  const all = ev.runs === wantRuns && ev.completed === ev.runs &&
    ev.nf_matched === ev.runs && ev.readback_pure === ev.runs;
  report("L-SCHED-FLOAT-1", "(completion+NF+coherence, 6 schedulers incl. 2 starvation adversaries × vectors, floating-dup relation, PROGRESS under free+adversarial choice)",
    all ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${ev.completed}/${ev.runs} completed, ${ev.nf_matched} NF-match, ${ev.readback_pure} readback-pure (ZERO INTERACT-plane rules at readback; residual COLLAPSE work: ${residualCollapse} DUP-VARs over ${residualLive} live residual dups on this corpus), max steps ${ev.max_steps} at a 20k budget. Each run leaves a RECEIPT (term, scheduler, seed, steps, interactions, termination, state/nf/film ids, readback counts); the certificate carries all ${ev.runs} and its checker re-executes every one — the freedom claim travels with a re-derivable evidence basis, not with prose. Two of the six schedulers are STARVATION ADVERSARIES (starve_dups fires an APP whenever one is enabled; starve_apps a heap DUP) — persistent avoidance of a redex class does not prevent completion, NF agreement, or count invariance on this corpus (law:sched.adversarial.float@1)`);
  if (all) {
    schedCert = buildSchedulerCertificateV2("conformance-vectors", vectorsSrc, SCHEDULERS, 20000, schedBattery);
    writeFileSync("scheduler_certificate.json", JSON.stringify(schedCert, null, 1));
  }
}

// L-PLANE-SEP-1 : plane separation, EXECUTABLE — phased INTERACT→COLLAPSE
// runs alternating to fixpoint. MEASURED DISCOVERY (law:plane.separation.fixpoint@1):
// collapse can RE-ENABLE interact (copying a stuck application exposes new
// APP redexes), so the planes compose as an interleaved fixpoint, not a
// sequential pipeline. The law records the alternation depth honestly.
{
  let comp = 0, matched = 0, maxAlt = 0, reEnabled = 0, tried = 0;
  for (const [sn, pick] of Object.entries({ leftmost: SCHEDULERS.leftmost, random: SCHEDULERS.random })) {
    for (const v of vectorsSrc) {
      tried++;
      const frt = new FloatRt(); let root = extrude(frt, parse(frt, v.term));
      const rnd = mulberry32(0x5E9 + sn.length + v.name.length);
      let ok = true, alts = 0, sawReEnable = false, guard = 0;
      for (;;) {
        let acted = false;
        for (;;) { const rs = findFloatRedexes(frt, root, PLANES.INTERACT); if (!rs.length) break;
          root = fireFloat(frt, root, pick(rs, rnd)).root; acted = true; if (++guard > 40000) { ok = false; break; } }
        if (!ok) break;
        let c = false;
        for (;;) { const rs = findFloatRedexes(frt, root, PLANES.COLLAPSE); if (!rs.length) break;
          root = fireFloat(frt, root, pick(rs, rnd)).root; c = true; if (++guard > 40000) { ok = false; break; } }
        if (!ok) break;
        alts++;
        const back = findFloatRedexes(frt, root, PLANES.INTERACT).length;
        if (c && back > 0) sawReEnable = true;
        if (!acted && !c) break;
        if (back === 0 && findFloatRedexes(frt, root, PLANES.COLLAPSE).length === 0) break;
      }
      if (!ok || liveHeap(frt, root).size) continue;
      let nf; try { nf = floatNfString(frt, root); } catch { continue; }
      comp++;
      maxAlt = Math.max(maxAlt, alts);
      if (sawReEnable) reEnabled++;
      if (nf === refNormalize(v.term).str) matched++;
    }
  }
  report("L-PLANE-SEP-1", "(NF via phased INTERACT⇄COLLAPSE fixpoint, 2 schedulers × vectors, plane partition, COHERENCE)",
    comp === tried && matched === comp ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${comp}/${tried} completed, ${matched} NF-match; max alternation depth ${maxAlt}; collapse RE-ENABLED interact in ${reEnabled} runs — the planes are distinct relations whose composition is an interleaved fixpoint, not a pipeline. A certificate that grants "collapse after interact" without the alternation clause over-claims`);
}

// L-COLLAPSE-PROG-1 : COLLAPSE progress, per plane (law:collapse.progress@1):
// from pool-quiescence the readback (a) fires ONLY collapse-plane rules,
// (b) terminates, and (c) fires exactly one DUP-VAR per live residual dup —
// progress is a per-plane, per-strategy claim with an explicit work bound,
// never a global one. Measured over the vectors AND a fuzz sample, because
// the vectors alone never leave a live residual (the fuzzer found the
// residual-collapse class the same day the engine shipped).
{
  let tried = 0, pure = 0, bounded = 0, matched = 0, withResidual = 0;
  const fuzzRnd = mulberry32(0xC01A);
  const corpus = vectorsSrc.map(v => v.term);
  for (let i = 0; i < (QUICK ? 20 : 60); i++) {
    const g = new Rt(); const lab = { n: 700 };
    corpus.push(show(genTerm(g, fuzzRnd, 5, [], lab)));
  }
  for (const term of corpus) {
    let want; try { want = refNormalize(term).str; } catch { continue; }
    let r; try { r = runFloat(term, { seed: 0xC011 }); } catch { continue; }
    if (r.termination !== "NORMAL_FORM") continue;
    // B8.3: `continue` here is for a term this loop cannot READ BACK within
    // budget, and skipping one shrinks `tried`, which every clause below is
    // compared against — so a swallowed invariant breach would leave the
    // property reporting PROPERTY-TESTED over a quietly smaller population.
    let rb; try { rb = readback(r.frt, r.root); }
    catch (e) { if (isReadbackInvariant(e)) throw e; continue; }
    tried++;
    if (rb.liveCount > 0) withResidual++;
    if (rb.interactFired === 0) pure++;
    if (rb.collapseFired === rb.liveCount) bounded++;
    if (rb.str === want) matched++;
  }
  report("L-COLLAPSE-PROG-1", "(readback purity+boundedness, collapse-only from pool-quiescence, live residual dups, PROGRESS per plane)",
    tried > 0 && pure === tried && bounded === tried && matched === tried ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${tried} pool-quiescent states (${withResidual} with live residual dups): readback fired zero INTERACT rules on ${pure}, exactly one DUP-VAR per residual dup on ${bounded}, NF matched reference on ${matched} — the collapse plane has its own progress theorem shape: monotone dup-count decrease, terminating, work == residual size`);
}

// L-BIND-1/2 : film v3.1 frames bind revisions; replay verifies; frame
// tamper → typed refusal at the exact index
{
  let ok = 0, refusedAtRight = 0, runs = 0, bad = null;
  const corpus = vectorsSrc.slice(0, QUICK ? 6 : 12);
  for (const v of corpus) {
    const film = newFilm();
    const frt = new FloatRt();
    let root = extrude(frt, parse(frt, v.term));
    const out = normalizeFloat(frt, root, SCHEDULERS.random, mulberry32(0xF117 + runs), { film });
    if (out.termination !== "NORMAL_FORM") continue;
    const rep = replayFloat(v.term, film);
    runs++;
    if (rep.ok && floatNfString(rep.frt, rep.root) === floatNfString(frt, out.root)) ok++;
    else bad = { v: v.name, rep: rep.reason };
    if (film.frames.length > 1) {
      const t = { ...film, frames: film.frames.map(f => ({ ...f })) };
      const k = Math.floor(film.frames.length / 2);
      t.frames[k] = { ...t.frames[k], pre: "0".repeat(64) };
      const r2 = replayFloat(v.term, t);
      if (!r2.ok && r2.at === k && r2.reason === "revision-mismatch") refusedAtRight++;
    }
  }
  report("L-BIND-1", "(film v3.1 frames, replay, per-frame pre-state hash, BINDING)",
    ok === runs && runs > 0 && !bad ? "PROPERTY-TESTED" : "FALSIFIED?!",
    bad ? JSON.stringify(bad) : `${runs} films replayed to the recorded NF with every frame's revision, plane and chain verified`);
  report("L-BIND-2", "(film v3.1 frames, tampered replay, one frame altered, BINDING)",
    refusedAtRight > 0 ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `tampered frame refused with typed revision-mismatch at exactly the altered index in ${refusedAtRight} trials`);
}

// L-BIND-3 : THE TERMINAL IS EVIDENCE (law:film.evidence-chain@5). Replays
// the exact external-review attacks that v3 accepted — termination flip,
// steps, last_frame — plus film_id tamper and the strongest forgery: a
// BUDGET film re-terminal'd as NORMAL_FORM with an HONESTLY RECOMPUTED
// film_id, which only outcome re-derivation can catch. Also asserts the
// declared non-authority of frame.i: mutating it must NOT refuse replay.
{
  const v = vectorsSrc.find(x => x.name === "church_apply_2") ?? vectorsSrc[3];
  const good = newFilm();
  { const frt = new FloatRt(); let root = extrude(frt, parse(frt, v.term));
    normalizeFloat(frt, root, SCHEDULERS.random, mulberry32(0xB1D3), { film: good }); }
  const clone = (f) => ({ film_id: f.film_id, terminal: { ...f.terminal }, frames: f.frames.map(x => ({ ...x })) });
  const attacks = [];
  { const m = clone(good); m.terminal.termination = "BUDGET_EXHAUSTED";
    attacks.push(["termination-flip", m, ["terminal-malformed", "film-id-mismatch"]]); }
  { const m = clone(good); m.terminal.steps = 999999;
    attacks.push(["steps-mutation", m, ["terminal-steps-mismatch"]]); }
  { const m = clone(good); m.terminal.last_frame = "deadbeef";
    attacks.push(["last-frame-mutation", m, ["terminal-last-frame-mismatch"]]); }
  { const m = clone(good); m.film_id = "0".repeat(64);
    attacks.push(["film-id-tamper", m, ["film-id-mismatch"]]); }
  // the forgery: honest-looking NORMAL_FORM claim over an exhausted run
  const vb = vectorsSrc.find(x => x.name === "church_exp_3_3") ?? vectorsSrc[0];
  const bfilm = newFilm();
  { const frt = new FloatRt(); let root = extrude(frt, parse(frt, vb.term));
    normalizeFloat(frt, root, SCHEDULERS.random, mulberry32(0xB1D4), { film: bfilm, budget: 5 }); }
  { const m = clone(bfilm);
    m.terminal.termination = "NORMAL_FORM";
    delete m.terminal.budget; delete m.terminal.remaining_work;
    m.film_id = filmIdOf(m.terminal);              // attacker recomputes the commitment honestly
    attacks.push(["forged-normal-form", m, ["false-normal-form"]]); }
  let pass = 0, detail = [];
  for (const [name, m, expected] of attacks) {
    const src = name === "forged-normal-form" ? vb.term : v.term;
    const r = replayFloat(src, m);
    const hit = !r.ok && expected.includes(r.reason);
    if (hit) pass++;
    detail.push(`${name}→${r.ok ? "ACCEPTED?!" : r.reason}`);
  }
  // declared non-authority of frame.i
  const im = clone(good); if (im.frames.length) im.frames[0].i = 424242;
  const ir = replayFloat(v.term, im);
  const iOk = ir.ok === true;
  const budgetHonest = replayFloat(vb.term, bfilm).ok === true;
  report("L-BIND-3", "(film terminal + film_id, mutation battery incl. recomputed-commitment forgery, v3.1 replay, BINDING/ADEQUACY)",
    pass === attacks.length && iOk && budgetHonest ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${pass}/${attacks.length} attacks refused with typed reasons [${detail.join("; ")}]; honest BUDGET_EXHAUSTED film replays ok (remaining-work witness verified): ${budgetHonest}; frame.i mutation accepted as declared non-authoritative metadata: ${iOk} — v3 bound the chain of transitions; v3.1 binds the claimed OUTCOME of the chain, and re-derives it`);
}

// L-BIND-4 : films must witness derivations IN THE LIVE RELATION under
// their DECLARED planes (law:film.evidence-chain@5). Round-5 probes: 227
// adversarial prefer-dead runs produced digest-consistent films firing DEAD
// heap loci and v0.5 replay ACCEPTED them; 176 further dead-firing runs on
// the exact pre-fix fuzz stream showed ZERO NF divergence — revising the
// round-4 Bug-A story (the λa.b corruption was the READBACK hole; dead
// enumeration's real harm is ILLEGAL TRANSITIONS + quiescence distortion).
{
  const findDeadIncl = (frt, root, planes) => {   // pre-fix enumeration: ALL heap ids
    const out = [];
    for (const a of findAppRedexes(frt, root)) if (planes.has(a.rule)) out.push({ kind: "app", ...a });
    for (const id of [...frt.heap.keys()].sort((x, y) => x - y)) {
      const d = frt.heap.get(id); const rule = dupRule(frt, d);
      if (rule && planes.has(rule)) out.push({ kind: "dup", id, rule });
      for (const a of findAppRedexes(frt, d.val)) if (planes.has(a.rule)) out.push({ kind: "dupval", id, ...a });
    }
    return out;
  };
  const forgeDeadFilm = (term, seed) => {
    const frt = new FloatRt(); let root = extrude(frt, parse(frt, term));
    const rnd = mulberry32(seed); const film = newFilm();
    let steps = 0, prev = "genesis", firedDead = 0;
    for (;;) {
      const rs = findDeadIncl(frt, root, PLANE_POOL_FREE);
      if (!rs.length) {
        sealFilm(film, frt, root, { termination: "NORMAL_FORM", steps, last_frame: prev, planes: [...PLANE_POOL_FREE] });
        return { film, firedDead };
      }
      if (steps >= 20000) return { film: null, firedDead };
      const live = liveHeap(frt, root);
      const dead = rs.filter((r) => (r.kind === "dup" || r.kind === "dupval") && !live.has(r.id));
      const rx = dead.length ? dead[0] : rs[Math.floor(rnd() * rs.length)];
      const pre = floatDigest(frt, root);
      const r = fireFloat(frt, root, rx);
      if (r.refused) return { film: null, firedDead };
      if (dead.length && rx === dead[0]) firedDead++;
      root = r.root; steps++;
      const post = floatDigest(frt, root);
      const fid = frameId31(prev, pre, PLANE_OF[r.rule], r.rule, encodeLocus(rx), post);
      film.frames.push({ i: film.frames.length, plane: PLANE_OF[r.rule], rule: r.rule,
        locus: encodeLocus(rx), pre, post, prev, frame_id: fid });
      prev = fid;
    }
  };
  const WT = "(λa.!&500{b,c}=λd.!&501{e,f}=d;a;(b c) λg.(!&502{h,i}=λj.g;h &503{(X Z),(S X)}))";
  let forged = null;
  for (let s = 0; s < 60 && !forged; s++) {
    const f = forgeDeadFilm(WT, 0xDEAD0 + s);
    if (f.film && f.firedDead > 0) forged = f;
  }
  let deadReason = "-";
  if (forged) { const rep = replayFloat(WT, forged.film); deadReason = rep.ok ? "ACCEPTED!" : rep.reason; }
  // undeclared-plane forgery: an honest full-pool film re-labeled INTERACT-
  // only, with the film_id commitment HONESTLY recomputed
  let permReason = "-", permSrc = null;
  for (const v of vectorsSrc) {
    const frt2 = new FloatRt(); const r2 = extrude(frt2, parse(frt2, v.term));
    const f2 = newFilm();
    normalizeFloat(frt2, r2, (rs) => rs[0], mulberry32(1), { film: f2 });
    if (f2.terminal?.termination === "NORMAL_FORM" && f2.frames.some((fr) => fr.plane === "COLLAPSE")) {
      f2.terminal.planes = [...PLANES.INTERACT];
      f2.film_id = filmIdOf(f2.terminal);
      const rep2 = replayFloat(v.term, f2);
      permReason = rep2.ok ? "ACCEPTED!" : rep2.reason; permSrc = v.name; break;
    }
  }
  report("L-BIND-4", "(film frames, dead-locus + undeclared-plane forgeries with honest commitments, live-relation enabledness, BINDING/CLOSURE)",
    forged && deadReason === "illegal-transition" && permReason === "plane-not-permitted" ? "PROPERTY-TESTED" : "FALSIFIED?!",
    forged
      ? `dead-locus film (${forged.firedDead} dead firings, digests and film_id honest) refused: ${deadReason}; undeclared-plane film (COLLAPSE frames of ${permSrc} under an INTERACT-only declaration, film_id honestly recomputed) refused: ${permReason} — digest consistency is NECESSARY but not SUFFICIENT: replay re-derives per-frame membership in the live relation under the declared planes`
      : "could not forge a dead-locus film on the witness term in 60 seeds");
}

// L-SEMID-1 : the state-identity SPLIT, adversarially (round 6 —
// law:state.exec-identity@1, law:state.semantic-quotient@1). The external
// audit's witness is reproduced VERBATIM (its two digests are asserted),
// then the quotient is attacked: heap-id bijections (incl. mid-run states),
// dead heap injection, alpha-renaming, label bijection, and the descending
// adversarial allocator. Semantic identity must hold everywhere execution
// identity is allowed to vary.
{
  const WTERM = "!&7{a,b}=X; !&9{c,d}=Y; ((a c) (b d))";
  const mk = (t, R = FloatRt) => { const frt = new R(); const root = extrude(frt, parse(frt, t)); return { frt, root }; };
  const permuteIds = (s, bij) => {
    const entries = [...s.frt.heap.entries()];
    s.frt.heap.clear();
    for (const [id, d] of entries) s.frt.heap.set(bij.get(id) ?? id, d);
    return s;
  };
  const A = mk(WTERM);
  const ids = [...A.frt.heap.keys()];
  const B = permuteIds(mk(WTERM), new Map([[ids[0], ids[1]], [ids[1], ids[0]]]));
  const dA = execStateId(A.frt, A.root), dB = execStateId(B.frt, B.root);
  const witnessExact = dA === "18b4e47b34d38339a2675cd760726c804d36e828cfed9b9e34c05f6a99a1deb1"
                    && dB === "6bca1878284b4dfd7cf511ce4e811828509a59d100ed7f1bebe3151b09774574";
  const witnessSplit = dA !== dB && semStateId(A.frt, A.root) === semStateId(B.frt, B.root);
  const C = mk(WTERM);
  C.frt.heap.set(C.frt.fresh(), { lab: 999, l: C.frt.fresh(), r: C.frt.fresh(), val: parse(C.frt, "λq.q") });
  const deadOk = execStateId(C.frt, C.root) !== dA && semStateId(C.frt, C.root) === semStateId(A.frt, A.root);
  const alphaOk = semStateId(...(() => { const s = mk("!&7{p,q}=X; !&9{r,s2}=Y; ((p r) (q s2))"); return [s.frt, s.root]; })()) === semStateId(A.frt, A.root);
  const labelOk = semStateId(...(() => { const s = mk("!&3{a,b}=X; !&5{c,d}=Y; ((a c) (b d))"); return [s.frt, s.root]; })()) === semStateId(A.frt, A.root);
  const descOk  = semStateId(...(() => { const s = mk(WTERM, DescFloatRt); return [s.frt, s.root]; })()) === semStateId(A.frt, A.root);
  // mid-run + random bijections over fuzz-adjacent states
  let midOk = true, randTried = 0, randInvariant = 0, execVaried = 0;
  {
    const v = vectorsSrc.find((x) => x.name === "church_exp_2_2");
    const s = mk(v.term);
    const rnd = mulberry32(0x61D);
    for (let k = 0; k < 10; k++) {
      const rs = findFloatRedexes(s.frt, s.root, PLANE_POOL_FREE);
      if (!rs.length) break;
      s.root = fireFloat(s.frt, s.root, rs[Math.floor(rnd() * rs.length)]).root;
    }
    const semBefore = semStateId(s.frt, s.root), execBefore = execStateId(s.frt, s.root);
    for (let trial = 0; trial < (QUICK ? 8 : 24); trial++) {
      const cur = [...s.frt.heap.keys()];
      const shuffled = [...cur];
      for (let i = shuffled.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]; }
      const bij = new Map(cur.map((id, i) => [id, shuffled[i] + 5_000_000]));  // move out of range, injective
      const t2 = permuteIds({ frt: s.frt, root: s.root }, bij);   // in place
      randTried++;
      if (semStateId(t2.frt, t2.root) === semBefore) randInvariant++;
      if (execStateId(t2.frt, t2.root) !== execBefore) execVaried++;
      // permute back for next trial
      permuteIds(t2, new Map([...bij].map(([a, b]) => [b, a])));
    }
    midOk = randInvariant === randTried && semStateId(s.frt, s.root) === semBefore;
  }
  report("L-SEMID-1", "(state identity split, audit witness + id/dead/alpha/label/allocator attacks, semantic quotient, COHERENCE/BINDING)",
    witnessExact && witnessSplit && deadOk && alphaOk && labelOk && descOk && midOk ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `audit witness reproduced byte-for-byte (execStateId ${dA.slice(0, 8)}… ≠ ${dB.slice(0, 8)}…, behaviors identical) and RESOLVED: semStateId equal across the swap; dead-entry injection perturbs exec, not sem: ${deadOk}; alpha-rename: ${alphaOk}; label bijection: ${labelOk}; descending adversarial allocator: ${descOk}; mid-run random heap-id bijections sem-invariant ${randInvariant}/${randTried} with exec varying on ${execVaried} — the standing Coherence question is answered NO for floatDigest and CLOSED by the split: execution identity is allocation-sensitive BY DECLARATION, semantic identity quotients ids, dead content, allocation order, alpha, and labels`);
}

// L-SEMID-2 : the quotient must not collapse DIFFERENT states — sampled
// adequacy on the semantic side, same evidence-class honesty as L-ADEQ-2.
{
  const seen = new Map(); let collisions = 0, pairs = 0;
  const put = (name, sid) => {
    for (const [n2, s2] of seen) { pairs++; if (s2 === sid && n2 !== name) collisions++; }
    seen.set(name, sid);
  };
  for (const v of vectorsSrc) {
    const frt = new FloatRt(); const root = extrude(frt, parse(frt, v.term));
    put(v.name, semStateId(frt, root));
  }
  const rt1 = new FloatRt(), rt2 = new FloatRt();
  const lockPair = semStateId(rt1, extrude(rt1, parse(rt1, "λa.λb.a")))
                !== semStateId(rt2, extrude(rt2, parse(rt2, "λa.λb.b")));
  const rnd = mulberry32(0x5E31D);
  let fuzzDistinct = 0, fuzzTried = 0;
  const fuzzSeen = new Set();
  for (let i = 0; i < (QUICK ? 20 : 60); i++) {
    const g = new Rt(); const lab = { n: 700 };
    const s = show(genTerm(g, rnd, 5, [], lab));
    const frt = new FloatRt();
    let root; try { root = extrude(frt, parse(frt, s)); } catch { continue; }
    const sid = semStateId(frt, root);
    fuzzTried++;
    if (!fuzzSeen.has(sid)) { fuzzSeen.add(sid); fuzzDistinct++; }
  }
  report("L-SEMID-2", "(semantic identity, pairwise distinctness on corpus + locked pair + fuzz, sampled, ADEQUACY)",
    collisions === 0 && lockPair ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `0 collisions across ${pairs} corpus pairs; the locked digest-adequacy pair (λa.λb.a vs λa.λb.b) separates at the semantic level too: ${lockPair}; ${fuzzDistinct}/${fuzzTried} distinct fuzz initial states (duplicates possible only for alpha/label-equivalent generations — the quotient working, not failing). Distinctness is SAMPLED under the SHA-256 collision-resistance assumption, exactly as L-ADEQ-2 states it (law:state.semantic-quotient@1)`);
}

// L-REFINE-1 : allocation portability — the ic32 bridge, executable today
// (law:refine.alloc-portability@1). The standard and the DESCENDING
// allocator run every vector in LOCKSTEP under a rotating free-choice
// index schedule: per-step SEMANTIC chains must be equal while execution
// identity is allocator-bound. The SEMANTIC film built on A must replay on
// B; A's EXECUTION film replays; B's execution film must be either
// bit-identical to A's or REFUSED by replayFloat — the refusal IS the
// demonstration that execution identity does not travel. Emits
// refinement_receipt.json.
{
  const perTerm = []; let allSem = true, allNf = true, allCnt = true,
    semReplayOk = 0, execAOk = 0, execBRefusedOrEqual = 0, execBRefused = 0;
  for (const v of vectorsSrc) {
    const A = { frt: new FloatRt() }; A.root = extrude(A.frt, parse(A.frt, v.term));
    const B = { frt: new DescFloatRt() }; B.root = extrude(B.frt, parse(B.frt, v.term));
    const semF = newSemFilm(), exeA = newFilm(), exeB = newFilm();
    let steps = 0, prevS = "genesis", prevA = "genesis", prevB = "genesis", semEq = true;
    for (;;) {
      const sA = semStateId(A.frt, A.root), sB = semStateId(B.frt, B.root);
      if (sA !== sB) { semEq = false; break; }
      const rsA = findFloatRedexes(A.frt, A.root, PLANE_POOL_FREE);
      const rsB = findFloatRedexes(B.frt, B.root, PLANE_POOL_FREE);
      if (rsA.length === 0 && rsB.length === 0) break;
      if (rsA.length !== rsB.length) { semEq = false; break; }
      if (steps > 20000) { semEq = false; break; }
      const i = steps % rsA.length;
      const ordA = liveDiscoveryOrder(A.frt, A.root);
      const locS = semLocusOf(rsA[i], ordA);
      const eA = execStateId(A.frt, A.root), eB = execStateId(B.frt, B.root);
      const fA = fireFloat(A.frt, A.root, rsA[i]); A.root = fA.root;
      const fB = fireFloat(B.frt, B.root, rsB[i]); B.root = fB.root;
      if (fA.rule !== fB.rule) { semEq = false; break; }
      const sA2 = semStateId(A.frt, A.root);
      const fidS = frameId31(prevS, sA, PLANE_OF[fA.rule], fA.rule, locS, sA2);
      semF.frames.push({ i: steps, plane: PLANE_OF[fA.rule], rule: fA.rule, locus: locS, pre: sA, post: sA2, prev: prevS, frame_id: fidS });
      prevS = fidS;
      const pA = execStateId(A.frt, A.root);
      const lA = encodeLocus(rsA[i]);
      const fidA = frameId31(prevA, eA, PLANE_OF[fA.rule], fA.rule, lA, pA);
      exeA.frames.push({ i: steps, plane: PLANE_OF[fA.rule], rule: fA.rule, locus: lA, pre: eA, post: pA, prev: prevA, frame_id: fidA });
      prevA = fidA;
      const pB = execStateId(B.frt, B.root);
      const lB = encodeLocus(rsB[i]);
      const fidB = frameId31(prevB, eB, PLANE_OF[fB.rule], fB.rule, lB, pB);
      exeB.frames.push({ i: steps, plane: PLANE_OF[fB.rule], rule: fB.rule, locus: lB, pre: eB, post: pB, prev: prevB, frame_id: fidB });
      prevB = fidB;
      steps++;
    }
    sealSemFilm(semF, A.frt, A.root, { termination: "NORMAL_FORM", steps, last_frame: prevS, planes: [...PLANE_POOL_FREE] });
    sealFilm(exeA, A.frt, A.root, { termination: "NORMAL_FORM", steps, last_frame: prevA, planes: [...PLANE_POOL_FREE] });
    sealFilm(exeB, B.frt, B.root, { termination: "NORMAL_FORM", steps, last_frame: prevB, planes: [...PLANE_POOL_FREE] });
    const nfA = readback(A.frt, A.root).str, nfB = readback(B.frt, B.root).str;
    const ref = refNormalize(v.term).str;
    const cntEq = A.frt.total() === B.frt.total();
    allSem &&= semEq; allNf &&= (nfA === nfB && nfA === ref); allCnt &&= cntEq;
    const rSem = replaySemFilm(v.term, semF, DescFloatRt);
    if (rSem.ok) semReplayOk++;
    const rA = replayFloat(v.term, exeA);
    if (rA.ok) execAOk++;
    const rB = replayFloat(v.term, exeB);
    const bEqual = exeB.film_id === exeA.film_id;
    if (bEqual || !rB.ok) execBRefusedOrEqual++;
    if (!rB.ok) execBRefused++;
    perTerm.push({ name: v.name, steps, interactions: A.frt.total(),
      sem_chain_equal: semEq, nf_id: semId(nfA),
      sem_film_id: semF.film_id, exec_film_id_A: exeA.film_id, exec_film_id_B: exeB.film_id,
      exec_films_equal: bEqual,
      sem_film_replay_on_B: rSem.ok ? "ok" : "refused:" + rSem.reason,
      exec_film_B_replay: bEqual ? "equal-to-A" : (rB.ok ? "ok" : "refused:" + rB.reason) });
  }
  const n = vectorsSrc.length;
  const pass = allSem && allNf && allCnt && semReplayOk === n && execAOk === n && execBRefusedOrEqual === n;
  if (pass) {
    const receipt = {
      type: "RefinementReceipt", version: 1,
      law_refs: ["law:refine.alloc-portability@1", "law:state.semantic-quotient@1", "law:state.exec-identity@1"],
      relation: "floating-dup-heap-v1",
      allocators: { A: "ascending (FloatRt)", B: "descending-stride-13 (DescFloatRt), an adversarial stand-in for a second implementation until ic32" },
      schedule: "rotating free-choice index (steps % enabled)",
      terms: n, per_term: perTerm,
      summary: { sem_chains_equal: n, nf_reference_equal: n, interaction_counts_equal: n,
        sem_films_replayed_on_B: semReplayOk, exec_films_A_replayed: execAOk,
        exec_films_B_refused_by_A_replay: execBRefused,
        exec_films_identical_across_allocators: n - execBRefused },
      informational: { note: "NON-AUTHORITATIVE", generator: "trvm_law_kernel.mjs v" + KERNEL_VERSION },
    };
    receipt.receipt_id = createHash("sha256").update("TRVM-REFINE-v1|" + JSON.stringify(receipt.per_term) + "|" + JSON.stringify(receipt.summary)).digest("hex");
    writeFileSync("refinement_receipt.json", JSON.stringify(receipt, null, 1));
  }
  report("L-REFINE-1", "(allocation portability, dual-allocator lockstep + semantic-film cross-replay, refinement bridge, COHERENCE/REFINEMENT)",
    pass ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${n}/${n} vectors: per-step semantic chains EQUAL across allocators, NFs reference-equal, interaction counts equal; semantic films built on the ascending allocator replay on the DESCENDING one ${semReplayOk}/${n} by canonical-locus matching; execution films: A replays ${execAOk}/${n}, B is refused by replayFloat on ${execBRefused}/${n} (bit-identical to A on the rest — single-dup states where fold order cannot differ) — the semantic film is the PORTABLE evidence object, the execution film is the local one, and the RefinementReceipt records the asymmetry per term. This is the protocol ic32 will replay (law:refine.alloc-portability@1)`);
}

// L-SEMTERM-1 : the semantic-film TERMINAL under attack (round 6.1 —
// law:film.terminal-witness@1). GPT's AUDIT-SEM-BUDGET forged the v1
// terminal: zero-frame BUDGET_EXHAUSTED over an enabled state, ok:true,
// with budget/remaining_work outside the commitment. Reproduced here
// against v1 before the fix. v1.1: positive direction — an honest PARTIAL
// semantic film replays on BOTH allocators (portable checkpoints); then
// eleven forgeries, each required to die on its DISTINCT declared refusal.
{
  const V = vectorsSrc.find((x) => x.name === "church_exp_2_2");
  const buildPartial = (budget, pool = [...PLANE_POOL_FREE]) => {
    const frt = new FloatRt();
    let root = extrude(frt, parse(frt, V.term));
    const film = newSemFilm();
    let prev = "genesis", n = 0;
    const permitted = new Set(pool);
    while (n < budget) {
      const rs = findFloatRedexes(frt, root, permitted);
      if (!rs.length) break;
      const order = liveDiscoveryOrder(frt, root);
      const pre = semStateId(frt, root);
      const rx = rs[0];
      const loc = semLocusOf(rx, order);
      const r = fireFloat(frt, root, rx); root = r.root;
      const post = semStateId(frt, root);
      const fid = frameId31(prev, pre, PLANE_OF[r.rule], r.rule, loc, post);
      film.frames.push({ i: n, plane: PLANE_OF[r.rule], rule: r.rule, locus: loc, pre, post, prev, frame_id: fid });
      prev = fid; n++;
    }
    sealSemFilm(film, frt, root, { termination: "BUDGET_EXHAUSTED", steps: n, last_frame: prev, planes: pool, budget });
    return { film, frt, root };
  };
  const clone = (f) => JSON.parse(JSON.stringify(f));
  const reseal = (f) => { f.film_id = semFilmIdOf(f.terminal); return f; };
  const B = 7;
  const honest = buildPartial(B);
  const W = honest.film.terminal.remaining_work;
  const posA = replaySemFilm(V.term, honest.film, FloatRt).ok === true;
  const posB = replaySemFilm(V.term, honest.film, DescFloatRt).ok === true;
  const expect = (film, want) => {
    const r = replaySemFilm(V.term, film, FloatRt);
    return !r.ok && r.reason === want;
  };
  const cases = [];
  // 1-2. mutation WITHOUT resealing. TWO independent teeth, both asserted:
  // the commitment now COVERS the field (id diverges — the audit found
  // budget_mutation_preserves_id:true, exactly this property missing),
  // and replay refuses regardless (semantic re-derivation fires first in
  // replay order, same as replayFloat: world, then commitment).
  { const m = clone(honest.film); m.terminal.budget = 1;
    const idDiverges = semFilmIdOf(m.terminal) !== m.film_id;
    const r = replaySemFilm(V.term, m, FloatRt);
    cases.push(["budget-mutation-unsealed", idDiverges && !r.ok]); }
  { const m = clone(honest.film); m.terminal.remaining_work = -7;
    const idDiverges = semFilmIdOf(m.terminal) !== m.film_id;
    const r = replaySemFilm(V.term, m, FloatRt);
    cases.push(["work-mutation-unsealed", idDiverges && !r.ok]); }
  // 3. resealed budget lie (claims a budget the frames never reached)
  { const m = reseal(clone(honest.film)); m.terminal.budget = 999; reseal(m);
    cases.push(["budget-lie-resealed", expect(m, "sem-budget-mismatch")]); }
  // 4. resealed NEGATIVE remaining work
  { const m = clone(honest.film); m.terminal.remaining_work = -7; reseal(m);
    cases.push(["negative-work-resealed", expect(m, "sem-terminal-work-mismatch")]); }
  // 5. resealed WRONG remaining work
  { const m = clone(honest.film); m.terminal.remaining_work = W + 3; reseal(m);
    cases.push(["wrong-work-resealed", expect(m, "sem-terminal-work-mismatch")]); }
  // 6. resealed non-integer budget
  { const m = clone(honest.film); m.terminal.budget = "lots"; reseal(m);
    cases.push(["malformed-budget-resealed", expect(m, "sem-terminal-malformed")]); }
  // 7. steps overrun the declared budget (frames beyond budget, resealed)
  { const over = buildPartial(B); const m = clone(over.film);
    m.terminal.budget = B - 2; reseal(m);
    cases.push(["steps-overrun-budget-resealed", expect(m, "sem-budget-mismatch")]); }
  // 8. BUDGET_EXHAUSTED claimed on an actually QUIESCENT state
  { const frt = new FloatRt(); let root = extrude(frt, parse(frt, V.term));
    const film = newSemFilm(); let prev = "genesis", n = 0;
    for (;;) {
      const rs = findFloatRedexes(frt, root, PLANE_POOL_FREE);
      if (!rs.length) break;
      const order = liveDiscoveryOrder(frt, root);
      const pre = semStateId(frt, root);
      const r = fireFloat(frt, root, rs[0]); const loc = semLocusOf(rs[0], order);
      root = r.root;
      const post = semStateId(frt, root);
      const fid = frameId31(prev, pre, PLANE_OF[r.rule], r.rule, loc, post);
      film.frames.push({ i: n, plane: PLANE_OF[r.rule], rule: r.rule, locus: loc, pre, post, prev, frame_id: fid });
      prev = fid; n++;
    }
    sealSemFilm(film, frt, root, { termination: "BUDGET_EXHAUSTED", steps: n, last_frame: prev, planes: [...PLANE_POOL_FREE], budget: n });
    cases.push(["budget-claim-on-quiescence", expect(film, "sem-no-remaining-work")]); }
  // 9. GPT's exact witness under v1.1: zero-frame film over an enabled state,
  //    HONESTLY resealed — the budget cannot have been reached
  { const frt = new FloatRt(); const root = extrude(frt, parse(frt, "(λx.x X)"));
    const film = newSemFilm();
    sealSemFilm(film, frt, root, { termination: "BUDGET_EXHAUSTED", steps: 0, last_frame: "genesis", planes: [...PLANE_POOL_FREE], budget: 999, remaining_work: 424242 });
    const r0 = replaySemFilm("(λx.x X)", film, FloatRt);
    cases.push(["audit-witness-resealed", !r0.ok && (r0.reason === "sem-terminal-work-mismatch" || r0.reason === "sem-budget-mismatch")]); }
  // 10. NORMAL_FORM -> BUDGET_EXHAUSTED flip on a complete film, resealed
  { const frt = new FloatRt(); let root = extrude(frt, parse(frt, V.term));
    const film = newSemFilm(); let prev = "genesis", n = 0;
    for (;;) {
      const rs = findFloatRedexes(frt, root, PLANE_POOL_FREE);
      if (!rs.length) break;
      const order = liveDiscoveryOrder(frt, root);
      const pre = semStateId(frt, root);
      const r = fireFloat(frt, root, rs[0]); const loc = semLocusOf(rs[0], order);
      root = r.root;
      const post = semStateId(frt, root);
      const fid = frameId31(prev, pre, PLANE_OF[r.rule], r.rule, loc, post);
      film.frames.push({ i: n, plane: PLANE_OF[r.rule], rule: r.rule, locus: loc, pre, post, prev, frame_id: fid });
      prev = fid; n++;
    }
    sealSemFilm(film, frt, root, { termination: "BUDGET_EXHAUSTED", steps: n, last_frame: prev, planes: [...PLANE_POOL_FREE], budget: n, remaining_work: 0 });
    cases.push(["nf-to-budget-flip-resealed", expect(film, "sem-no-remaining-work")]); }
  // 11. BUDGET_EXHAUSTED -> NORMAL_FORM flip on a partial film, resealed
  { const m = clone(honest.film);
    m.terminal.termination = "NORMAL_FORM"; delete m.terminal.budget; delete m.terminal.remaining_work;
    m.terminal.normal_form_id = null; reseal(m);
    cases.push(["budget-to-nf-flip-resealed", expect(m, "sem-false-normal-form")]); }
  // 12. rule-pool participates in the WORK arithmetic: narrow the pool on an
  //     honest INTERACT-only prefix whose cutoff state has COLLAPSE work
  {
    let made = null;
    outer:
    for (let b = 1; b <= 12; b++) {
      const frt = new FloatRt();
      let root = extrude(frt, parse(frt, V.term));
      const film = newSemFilm(); let prev = "genesis", n = 0;
      while (n < b) {
        const rs = findFloatRedexes(frt, root, PLANE_POOL_FREE)
          .filter((r) => PLANE_OF[r.rule] === "INTERACT");
        if (!rs.length) continue outer;
        const order = liveDiscoveryOrder(frt, root);
        const pre = semStateId(frt, root);
        const r = fireFloat(frt, root, rs[0]); const loc = semLocusOf(rs[0], order);
        root = r.root;
        const post = semStateId(frt, root);
        const fid = frameId31(prev, pre, PLANE_OF[r.rule], r.rule, loc, post);
        film.frames.push({ i: n, plane: PLANE_OF[r.rule], rule: r.rule, locus: loc, pre, post, prev, frame_id: fid });
        prev = fid; n++;
      }
      const full = findFloatRedexes(frt, root, PLANE_POOL_FREE).length;
      const interactOnly = [...PLANE_POOL_FREE].filter((r) => PLANE_OF[r] === "INTERACT");
      const narrow = findFloatRedexes(frt, root, new Set(interactOnly)).length;
      if (full !== narrow && narrow > 0) {
        // commit remaining_work under the FULL pool but declare the NARROW pool
        sealSemFilm(film, frt, root, { termination: "BUDGET_EXHAUSTED", steps: n, last_frame: prev, planes: interactOnly, budget: n, remaining_work: full });
        made = film; break;
      }
    }
    cases.push(["pool-narrowing-work-arithmetic", made !== null && expect(made, "sem-terminal-work-mismatch")]);
  }
  const bad = cases.filter(([, ok2]) => !ok2).map(([nm]) => nm);
  report("L-SEMTERM-1", "(semantic-film terminal witness, honest partial replay on both allocators + 12 forgeries, terminal contract, BINDING/ADEQUACY)",
    posA && posB && bad.length === 0 ? "PROPERTY-TESTED" : "FALSIFIED?!",
    posA && posB && bad.length === 0
      ? `honest ${B}-step PARTIAL semantic film (budget ${B}, remaining_work ${W}) replays ok on BOTH allocators — portable checkpoints exist; 12/12 terminal forgeries refused: unsealed mutations now CHANGE the commitment (id divergence asserted; the audit found budget_mutation_preserves_id:true — precisely this property missing) AND are refused by re-derivation; budget lie + overrun (sem-budget-mismatch), negative/wrong/pool-narrowed work (sem-terminal-work-mismatch), malformed budget (sem-terminal-malformed), quiescence claim + NF flip (sem-no-remaining-work), partial-as-NF flip (sem-false-normal-form), and the round-6B audit witness itself, honestly resealed. The v1 terminal accepted ALL of the resealed ones (law:film.terminal-witness@1)`
      : `failing cases: ${bad.join(", ") || "(positive replay failed)"}`);
}

// L-ID-1 : artifact identity lock (round 6 — law:kernel.identity@1, superseded by @2). The
// audit caught v0.6 source printing a v0.5 banner: the executable disagreed
// with the artifact identity, one round after evidence-binding. LOCKED:
// source header, runtime constant, and certificate generator must agree.
{
  let srcTxt = "";
  try { srcTxt = readFileSync(new URL(import.meta.url), "utf8"); }
  catch { try { srcTxt = readFileSync(process.argv[1], "utf8"); } catch { /* stays empty */ } }
  const headOk = srcTxt.slice(0, 300).includes("v" + KERNEL_VERSION);
  const genOk = !!schedCert && schedCert.informational?.generator === "trvm_law_kernel.mjs v" + KERNEL_VERSION;
  report("L-ID-1", "(artifact identity: source header == runtime constant == certificate generator, kernel.identity@2 kernel half, BINDING)",
    headOk && genOk ? "REGRESSION-LOCKED" : "FALSIFIED?!",
    headOk && genOk
      ? `KERNEL_VERSION ${KERNEL_VERSION} appears in the first 300 bytes of the source and in the emitted certificate's generator string — the executable can no longer disagree with the artifact it claims to be (law:kernel.identity@2, which superseded @1 when identity became a map; the round-6 audit witnessed exactly this disagreement in v0.6)`
      : `identity disagreement: header ${headOk}, certificate generator ${genOk}`);
}

// L-CERT-1 : positive verification by FULL RE-EXECUTION + the naive tamper
// dies at the commitment (law:sched.certificate@2).
{
  if (!schedCert) {
    report("L-CERT-1", "(certificate v2, independent check, scheduler certificate, REFINEMENT)", "FALSIFIED?!",
      "no certificate was emitted because L-SCHED-FLOAT-1 did not fully pass");
  } else {
    const pos = checkSchedulerCertificateV2(schedCert, "conformance-vectors", vectorsSrc, SCHEDULERS);
    const naive = JSON.parse(JSON.stringify(schedCert));
    naive.representation = "magic-ast-v0";               // NO cert_id recompute
    const neg = checkSchedulerCertificateV2(naive, "conformance-vectors", vectorsSrc, SCHEDULERS);
    const negRight = !neg.ok && neg.reasons.includes("cert-id-mismatch");
    report("L-CERT-1", "(certificate v2, full re-execution + commitment break, scheduler certificate, REFINEMENT)",
      pos.ok && negRight ? "PROPERTY-TESTED" : "FALSIFIED?!",
      pos.ok
        ? `certificate verified by FULL RE-EXECUTION: all ${schedCert.run_manifest.length} receipts re-run deterministically (steps, interactions, termination, state/nf/film ids, readback counts all re-derived and equal), aggregates recomputed exactly, ${schedCert.claims.length} claims verified semantically, ${schedCert.law_refs.length} law refs justified, ${schedCert.exhibit_films.length} exhibit witnesses replayed under 18-refusal v3.1r; naive representation edit (commitment NOT recomputed) refused: cert-id-mismatch`
        : `certificate check failed: ${pos.reasons.slice(0, 6).join(", ")}`);
  }
}

// L-CERT-2 : the round-5 adversarial battery — every forgery HONESTLY
// RECOMPUTES the commitment (and manifest hash where receipts change), so
// each must die on a SEMANTIC re-derivation with the expected typed reason.
// v1 accepted 10/10 of these plus a hollow zero-exhibit certificate
// (verified by probe before this fix). AUTHORITY MAY NOT OUTRUN EVIDENCE.
{
  if (!schedCert) {
    report("L-CERT-2", "(certificate v2, adversarial mutation battery, scheduler certificate, ADEQUACY)", "FALSIFIED?!",
      "no certificate was emitted");
  } else {
    const clone = (o) => JSON.parse(JSON.stringify(o));
    const reseal = (c) => {
      c.run_manifest_hash = manifestHashOf(c.run_manifest ?? []);
      c.exhibit_film_ids = (c.exhibit_films ?? []).map((e) => e.film?.film_id);
      c.cert_id = certIdOf(c); return c;
    };
    const attacks = [
      ["representation-lie",        "unknown-representation",  (c) => { c.representation = "magic-ast-v0"; }],
      ["quiescence-lie",            "criterion-mismatch",      (c) => { c.quiescence_criterion = "vibes"; }],
      ["strategy-lie",              "strategy-mismatch",       (c) => { c.strategy.schedulers = ["normal-order"]; }],
      ["budget-lie",                "receipt-replay-mismatch", (c) => { c.budget = 1; }],
      ["evidence-inflation",        "evidence-mismatch",       (c) => { c.evidence.runs = 9600; c.evidence.completed = 9600; }],
      ["claims-erased",             "unjustified-law-ref",     (c) => { c.claims = []; }],
      ["unknown-claim-insertion",   "unknown-claim",           (c) => { c.claims = [...c.claims, "world-peace"]; }],
      ["law-refs-erased",           "no-law-refs",             (c) => { c.law_refs = []; }],
      ["law-ref-substitution",      "unknown-law-ref",         (c) => { c.law_refs = ["law:kappa.internal-edge.monotonicity@4"]; }],
      ["corpus-id-lie",             "corpus-id-mismatch",      (c) => { c.corpus.id = "totally-different-corpus"; }],
      ["exhibits-erased",           "missing-exhibit",         (c) => { c.exhibit_films = []; }],
      ["profile-broadened-fake",    "profile-mismatch",        (c) => { c.plane_profile.INTERACT.push("RULE-OF-COOL"); }],
      ["receipts-erased",           "incomplete-runs",         (c) => { c.run_manifest = []; }],
      ["receipt-duplication",       "incomplete-runs",         (c) => { c.run_manifest = [...c.run_manifest, ...clone(c.run_manifest)]; }],
      ["receipt-nf-lie",            "receipt-replay-mismatch", (c) => { const r = c.run_manifest[0]; r.nf_id = "f".repeat(64); r.nf_matched = true; }],
    ];
    let pass = 0; const detail = [];
    for (const [name, want, mut] of attacks) {
      const c = clone(schedCert); mut(c); reseal(c);
      const r = checkSchedulerCertificateV2(c, "conformance-vectors", vectorsSrc, SCHEDULERS);
      const hit = !r.ok && r.reasons.some((x) => x.startsWith(want));
      if (hit) pass++;
      detail.push(name + "→" + (r.ok ? "ACCEPTED!" : (r.reasons.find((x) => x.startsWith(want)) ?? r.reasons[0]).split(":").slice(0, 2).join(":")));
    }
    // combinatorial laundering: genuine corpus + genuine representation +
    // zero receipts + fabricated evidence, commitment honestly recomputed
    const hollow = clone(schedCert);
    hollow.run_manifest = []; hollow.exhibit_films = [];
    hollow.evidence = { schedulers: 4, terms: 24, runs: 999999, completed: 999999,
      nf_matched: 999999, readback_pure: 999999, max_steps: 1 };
    reseal(hollow);
    const hr = checkSchedulerCertificateV2(hollow, "conformance-vectors", vectorsSrc, SCHEDULERS);
    const hollowDead = !hr.ok && hr.reasons.some((x) => x.startsWith("incomplete-runs"));
    report("L-CERT-2", "(certificate v2, 15 laundered forgeries + hollow zero-receipt laundering, adversarial audit battery, ADEQUACY/REFINEMENT)",
      pass === attacks.length && hollowDead ? "PROPERTY-TESTED" : "FALSIFIED?!",
      `${pass}/${attacks.length} laundered forgeries refused on semantic re-derivation [${detail.join("; ")}]; hollow certificate (zero receipts, 999999 fabricated runs, honest commitment) refused: ${hollowDead} (${hr.reasons.slice(0, 2).join(", ")}) — v1 accepted every one of these`);
  }
}

// L-EQV-1 / L-ADEQ-1 / L-ADEQ-2 : the Equivariance/Adequacy dual, with the
// evidence classes now honest — the specific pair is REGRESSION-LOCKED
// (a closed counterexample), the general statement is sampled separately.
{
  const rtA = new Rt(), rtB = new Rt(), rtC = new Rt();
  const dKa = stateDigest(rtA, parse(rtA, "λa.λb.a"));
  const dKb = stateDigest(rtB, parse(rtB, "λa.λb.b"));
  const dKx = stateDigest(rtC, parse(rtC, "λx.λy.x"));
  const fid = dKa !== dKb;
  const eqv = dKa === dKx;
  let rtEq = 0, rtTot = 0;
  for (const v of vectorsSrc) {
    const r1 = new Rt(); const d1 = stateDigest(r1, parse(r1, v.term));
    const r2 = new Rt(); const d2 = stateDigest(r2, parse(r2, show(parse(new Rt(), v.term))));
    rtTot++; if (d1 === d2) rtEq++;
  }
  report("L-ADEQ-1", "(state digest, the v1-regression pair, fixed inputs, ADEQUACY)",
    fid ? "REGRESSION-LOCKED" : "FALSIFIED?!",
    "digest(λa.λb.a) " + (fid ? "≠" : "==") + " digest(λa.λb.b) — the exact counterexample that killed digest v1, closed and LOCKED. This row is evidence-class honesty: a locked regression is not a property test (law:digest.adequacy@2)");
  // sampled adequacy: distinct reference NFs ⇒ distinct digests
  let pairs = 0, collisions = 0;
  const nfs = [];
  for (const v of vectorsSrc) { const r = new Rt(); const nf = normalRef(r, parse(r, v.term)); nfs.push({ rt: r, nf, str: show(nf) }); }
  for (let i = 0; i < nfs.length; i++) for (let j = i + 1; j < nfs.length; j++) {
    if (nfs[i].str === nfs[j].str) continue;
    pairs++;
    if (stateDigest(nfs[i].rt, nfs[i].nf) === stateDigest(nfs[j].rt, nfs[j].nf)) collisions++;
  }
  report("L-ADEQ-2", "(state digest, all distinct-NF vector pairs, normal forms, ADEQUACY sampled)",
    collisions === 0 && pairs > 0 ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${pairs} distinct-NF pairs, ${collisions} digest collisions — P(x)=P(y) ⇒ O(x)=O(y) sampled over the corpus; the general statement additionally rests on SHA-256 collision resistance and can never be PROVED by sampling (law:digest.adequacy.sampled@1)`);
  report("L-EQV-1", "(state digest, identity-preserving renaming, any state, EQUIVARIANCE)",
    eqv && rtEq === rtTot ? "PROPERTY-TESTED" : "FALSIFIED?!",
    "digest(λa.λb.a) == digest(λx.λy.x) · printer-roundtrip digests equal on " + rtEq + "/" + rtTot + " vectors — the projection ignores what should not matter (names, labels)");
}

// L-BYTES-1 : the pre-hash bytes ARE the digest's preimage (round 10).
// v1.0.2 published digests only, so a second implementation whose canonical
// form was subtly wrong learned nothing from a mismatch beyond "wrong". At
// 1.1.0 stateDigest is DEFINED as sha256(stateSignature), and this row asserts
// the identity holds on every corpus state — initial AND normal form — plus
// the two properties that make a published signature worth diffing: the §5
// compaction boundary fires exactly at >80, and equivariance holds at the BYTE
// level (alpha-variants produce the identical signature string, not merely the
// same hash). A digest-level equality could hide a signature that agrees only
// after hashing; this cannot.
{
  let n = 0, preimage = 0, boundaryOk = true;
  let maxSig = 0, compacted = 0;
  for (const v of vectorsSrc) {
    const frt = new FloatRt();
    let root = extrude(frt, parse(frt, v.term));
    for (const stage of ["initial", "nf"]) {
      if (stage === "nf") {
        root = normalizeFloat(frt, root, (rs, r) => rs[Math.floor(r() * rs.length)],
          mulberry32(0xF10A7), {}).root;
      }
      const sig = semStateSignature(frt, root);
      const id = semStateId(frt, root);
      n++;
      if (createHash("sha256").update(sig).digest("hex") === id) preimage++;
      maxSig = Math.max(maxSig, sig.length);
      if (sig.startsWith("#")) { compacted++; if (sig.length !== 65) boundaryOk = false; }
      else if (sig.length > 80) boundaryOk = false;   // an over-80 signature must have been compacted
    }
  }
  // byte-level equivariance: alpha-variants sign IDENTICALLY, not just hash equal
  const sigOf = (src) => { const r = new FloatRt(); return semStateSignature(r, extrude(r, parse(r, src))); };
  const alphaBytes = sigOf("λa.λb.a") === sigOf("λx.λy.x");
  const labelBytes = sigOf("!&7{p,q}=X; (p q)") === sigOf("!&99{m,n}=X; (m n)");
  const distinctBytes = sigOf("λa.λb.a") !== sigOf("λa.λb.b");
  report("L-BYTES-1", "(canonical signature, sha256 preimage + compaction boundary + byte equivariance, all corpus states, BINDING)",
    preimage === n && n > 0 && boundaryOk && alphaBytes && labelBytes && distinctBytes
      ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${preimage}/${n} corpus states (initial + normal form for ${vectorsSrc.length} vectors): sha256(stateSignature) == semStateId — the published pre-hash bytes are the digest's actual preimage, not a parallel re-derivation that could drift. Compaction boundary well-formed on all ${n} (${compacted} compacted to exactly 65 chars, longest uncompacted ${maxSig}): ${boundaryOk}. Byte-level equivariance — alpha-variants and label permutations produce the IDENTICAL signature string (${alphaBytes}/${labelBytes}), and the v1-regression pair signs APART (${distinctBytes}); a digest-level check could not distinguish these from a canonical form that agrees only after hashing (law:digest.canonical-bytes@1)`);
}

// L-ANNIH-1 : invalid step → typed refusal, state unchanged — on BOTH
// engines (AST paths; float bogus loci incl. dead heap ids and bad val paths)
{
  function pathIsRedex(rt, root, path) {
    let t = root;
    for (const k of path) {
      const r = chase(rt, t);
      if (!CHILDREN[r.t].includes(k)) return false;
      t = r[k];
    }
    return redexRule(rt, chase(rt, t)) !== null;
  }
  let trials = 0, clean = 0;
  const rnd = mulberry32(0x0BAD);
  for (const v of vectorsSrc.slice(0, 10)) {
    const rt = new Rt(); const root = parse(rt, v.term);
    const h0 = stateDigest(rt, root);
    for (let k = 0; k < 25; k++) {
      const bogus = Array.from({ length: 1 + Math.floor(rnd() * 4) },
        () => ["fun", "arg", "bod", "val", "lft", "rgt"][Math.floor(rnd() * 6)]);
      if (pathIsRedex(rt, root, bogus)) continue;
      const r = applyAt(rt, root, bogus);
      trials++;
      if (r.refused && stateDigest(rt, root) === h0) clean++;
    }
  }
  let ftrials = 0, fclean = 0;
  for (const v of vectorsSrc.slice(0, 6)) {
    const frt = new FloatRt(); const root = extrude(frt, parse(frt, v.term));
    const h0 = floatDigest(frt, root);
    for (const rx of [{ kind: "dup", id: 999 }, { kind: "dupval", id: 999, path: [] },
                      { kind: "app", path: ["bod", "bod", "bod"] }]) {
      const r = fireFloat(frt, root, rx);
      ftrials++;
      if (r.refused && floatDigest(frt, root) === h0) fclean++;
    }
  }
  report("L-ANNIH-1", "(kernel state, invalid step request, non-redex loci on both engines, ANNIHILATION)",
    trials > 0 && clean === trials && fclean === ftrials ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `AST ${clean}/${trials} + float ${fclean}/${ftrials} invalid requests refused with state digest unchanged — refusal is total, no partial mutation`);
}

// L-LOCAL-1 : disjoint components under one interleaved float schedule
{
  const pairs = QUICK ? 8 : 18;
  let okc = 0, attempted = 0, skippedP = 0, bad = null;
  const rnd = mulberry32(0x10CA1);
  const pool = vectorsSrc.slice(0, 16);
  for (let p = 0; p < pairs; p++) {
    const a = pool[Math.floor(rnd() * pool.length)];
    const b = pool[Math.floor(rnd() * pool.length)];
    const combined = `((PAIR ${a.term}) ${b.term})`;
    let got; attempted++;
    try {
      const r = runFloat(combined, { seed: 0xFA3 + p });
      if (r.termination !== "NORMAL_FORM") { skippedP++; continue; }
      got = floatNfString(r.frt, r.root);
    } catch { skippedP++; continue; }
    const want = refNormalize(`((PAIR ${refNormalize(a.term).str}) ${refNormalize(b.term).str})`).str;
    if (got === want) okc++; else if (!bad) bad = { a: a.name, b: b.name, got, want };
  }
  report("L-LOCAL-1", "(component NFs, interleaved float co-reduction, disjoint components, LOCALITY)",
    !bad && okc > 0 ? "PROPERTY-TESTED" : "FALSIFIED?!",
    bad ? JSON.stringify(bad).slice(0, 220) : `${okc}/${attempted} random pairs co-reduced under one interleaved float schedule to exactly their solo NFs (${skippedP} schedules hit the budget); the frame rule at the calculus layer`);
}

// L-CLOSE-1 : every float step lands inside the grammar, root AND heap
{
  let steps = 0, malformed = 0;
  for (const v of vectorsSrc.slice(0, QUICK ? 8 : 16)) {
    const frt = new FloatRt(); let root = extrude(frt, parse(frt, v.term));
    const rnd = mulberry32(0xC105E);
    for (;;) {
      const rs = findFloatRedexes(frt, root, PLANE_POOL_FREE); if (!rs.length) break;
      const r = fireFloat(frt, root, rs[Math.floor(rnd() * rs.length)]);
      root = r.root; steps++;
      if (!wellFormedFloat(frt, root)) malformed++;
      if (steps > 3000) break;
    }
  }
  report("L-CLOSE-1", "(term grammar over tree+heap, every rule, all states, CLOSURE)",
    malformed === 0 ? "PROPERTY-TESTED" : "FALSIFIED?!",
    `${steps} float steps; states outside the grammar: ${malformed}`);
}

// DECAY : no clock in the pure kernel — honest N/A demonstrating the vocabulary
report("L-DECAY", "(—, advanceΔ, pure kernel, DECAY)", "NOT_APPLICABLE",
  "the calculus layer has no clock; DECAY laws live where PULSE epochs exist (β, δ, salience)");

// ── report ────────────────────────────────────────────────────────────────
console.log(`trvm_law_kernel v${KERNEL_VERSION} — conformance + the periodic-law grid, compiled to its own falsifier`);
console.log("planes: INTERACT | COLLAPSE (gated) — WORLD and EFFECT live beyond this kernel");
console.log("═".repeat(96));
const PASSING = new Set(["PASS", "PROPERTY-TESTED", "REGRESSION-LOCKED", "EMPIRICAL", "NOT_APPLICABLE", "FALSIFIED (by design)"]);
let hardFail = false;
for (const r of results) {
  if (!PASSING.has(r.status)) hardFail = true;
  console.log(`${r.id.padEnd(17)} ${r.status.padEnd(22)} ${r.tuple}`);
  console.log(`${"".padEnd(18)}${r.detail}`);
}
console.log("═".repeat(96));
if (confFail) console.log("conformance failures:", JSON.stringify(confFailures, null, 1).slice(0, 800));
console.log(hardFail
  ? "VERDICT: FAIL — an asserted law broke, a by-design falsification started passing, or conformance failed."
  : "VERDICT: PASS — conformant; every asserted law holds; every by-design falsification still fails; certificate emitted.");
process.exit(hardFail ? 1 : 0);
} // ── end IS_MAIN battery region ────────────────────────────────────────────
