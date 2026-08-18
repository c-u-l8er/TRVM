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
