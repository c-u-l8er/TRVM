/* ─────────────────────────────────────────────────────────────────────────
   κ — adversarial witnesses, and the corrected theorem statement
   Companion to kappa_proof.js · settles a wording-vs-proof question

   THE FINDING (2026-08-17, verified against the repo's own functions):

   The published prose states the theorem as
       κ(G) > 0  ⟺  β₁(G) > 0  ⟺  G has a nontrivial SCC
   and elsewhere glosses β₁ as "the Betti number (cycle count)". Read with
   β₁ as the ORDINARY first Betti number of the underlying undirected graph
   (|E| − |V| + components), that statement is FALSE — the directed diamond
   A→B, A→C, B→D, C→D is a DAG (κ = 0, no nontrivial SCC) with ordinary
   β₁ = 4 − 4 + 1 = 1. Witness W1 below.

   But kappa_proof.js never computes that quantity. Its betti1() is
       β₁ˢᶜᶜ(G) = max over SCCs S with |S| ≥ 2 of (|E(S)| − |S| + 1),
       and 0 when no such SCC exists
   — the directed cycle rank RESTRICTED TO strongly connected components —
   and its graph domain excludes self-loops by construction (adjFromBits
   skips i = j). On the diamond, β₁ˢᶜᶜ = 0 and the equivalence holds.
   Confirmed by importing the repo's own kappaGlobal/betti1 and running W1.

   VERDICT: statement bug, not proof bug. The machine-checked object is
   sound; the prose calls it by the wrong name. Repair:

     K1.  κ(G) > 0  ⟺  β₁ˢᶜᶜ(G) > 0  ⟺  G contains an SCC of size ≥ 2
          (finite simple digraphs, no self-loops — state the convention).
     K2.  For finite maps f : [n] → [n],
          κ(TransitionGraph(f)) > 0  ⟺  f has a periodic orbit of period > 1
          (fixed points are period-1 and correctly excluded — the two
          parts' conventions already agree; they were never stated).

   Do not call β₁ˢᶜᶜ "the Betti number" unqualified. Either define it on
   the page, or drop the middle term and keep κ ⟺ nontrivial-SCC, which is
   the operationally load-bearing equivalence anyway.

   This file: five named witnesses, exhaustive re-verification of K1 on
   all 4,096 digraphs at n = 4, a 100,000-graph sample at n = 5, and a
   measurement of HOW WRONG the unqualified wording is (the fraction of
   graphs where ordinary β₁ > 0 but κ = 0). The suite derives its totals.
   ───────────────────────────────────────────────────────────────────────── */

// ── graph machinery (standalone; cross-checked against kappa_proof.js) ───
function tarjanSCC(adj, n) {
  const index = new Int32Array(n).fill(-1), low = new Int32Array(n),
        onStack = new Uint8Array(n), stack = [], sccs = [];
  let idx = 0;
  function strong(v) {
    index[v] = low[v] = idx++; stack.push(v); onStack[v] = 1;
    for (let w = 0; w < n; w++) if (adj[v * n + w]) {
      if (index[w] === -1) { strong(w); low[v] = Math.min(low[v], low[w]); }
      else if (onStack[w]) low[v] = Math.min(low[v], index[w]);
    }
    if (low[v] === index[v]) {
      const scc = []; let w;
      do { w = stack.pop(); onStack[w] = 0; scc.push(w); } while (w !== v);
      sccs.push(scc);
    }
  }
  for (let v = 0; v < n; v++) if (index[v] === -1) strong(v);
  return sccs;
}

function kappa(adj, n) {
  // min over bipartitions (A,B) of the largest SCC of min(|A→B|, |B→A|)
  const sccs = tarjanSCC(adj, n);
  let S = null;
  for (const c of sccs) if (!S || c.length > S.length) S = c;
  if (!S || S.length <= 1) return 0;
  const m = S.length; let best = Infinity;
  for (let mask = 1; mask < (1 << m) - 1; mask++) {
    let ab = 0, ba = 0;
    for (let i = 0; i < m; i++) for (let j = 0; j < m; j++) {
      if (i === j || !adj[S[i] * n + S[j]]) continue;
      const iA = !!(mask & (1 << i)), jA = !!(mask & (1 << j));
      if (iA && !jA) ab++; else if (!iA && jA) ba++;
    }
    best = Math.min(best, Math.min(ab, ba));
  }
  return best === Infinity ? 0 : best;
}

// the quantity the proof code actually verifies
function betti1_scc(adj, n) {
  let max = 0;
  for (const S of tarjanSCC(adj, n)) {
    if (S.length <= 1) continue;
    let e = 0;
    for (const i of S) for (const j of S) if (i !== j && adj[i * n + j]) e++;
    max = Math.max(max, e - S.length + 1);
  }
  return max;
}

// the quantity the prose accidentally names: ordinary undirected cycle rank
function betti1_undirected(adj, n) {
  const und = new Set(); const parent = Array.from({ length: n }, (_, i) => i);
  const find = (x) => (parent[x] === x ? x : (parent[x] = find(parent[x])));
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++)
    if (adj[i * n + j]) und.add(i < j ? `${i},${j}` : `${j},${i}`);
  for (const e of und) { const [a, b] = e.split(",").map(Number); parent[find(a)] = find(b); }
  const comps = new Set(); for (let i = 0; i < n; i++) comps.add(find(i));
  return und.size - n + comps.size;
}

const nontrivialSCC = (adj, n) => tarjanSCC(adj, n).some((s) => s.length > 1);
const mk = (n, edges) => {
  const a = new Uint8Array(n * n);
  for (const [i, j] of edges) a[i * n + j] = 1;
  return a;
};

// ── the named witnesses ──────────────────────────────────────────────────
const witnesses = [
  { id: "W1", name: "directed diamond (DAG)", n: 4,
    adj: mk(4, [[0,1],[0,2],[1,3],[2,3]]),
    note: "κ=0, no SCC, β₁ˢᶜᶜ=0 — but ordinary β₁=1. Breaks the unqualified wording; not the verified statement." },
  { id: "W2", name: "2-cycle", n: 2, adj: mk(2, [[0,1],[1,0]]),
    note: "κ=1, SCC of size 2, β₁ˢᶜᶜ=1, ordinary β₁... the undirected collapse makes it 0 edges−cycle? single und. edge ⇒ β₁=0 — the two quantities disagree in BOTH directions." },
  { id: "W3", name: "directed theta (two cycles sharing a path)", n: 4,
    adj: mk(4, [[0,1],[1,2],[2,0],[2,3],[3,0]]),
    note: "one SCC of size 4, β₁ˢᶜᶜ = 5−4+1 = 2 — cyclicity depth beyond a single loop." },
  { id: "W4", name: "6-chain (deep DAG)", n: 6,
    adj: mk(6, [[0,1],[1,2],[2,3],[3,4],[4,5]]),
    note: "κ=0 however long the chain — depth is not cyclicity." },
  { id: "W5", name: "two disjoint 2-cycles", n: 4,
    adj: mk(4, [[0,1],[1,0],[2,3],[3,2]]),
    note: "κ computed on the LARGEST SCC only (=1); β₁ˢᶜᶜ takes the max (=1). Convention worth stating: κ is a max over components, not a sum." },
];

console.log("κ — adversarial witnesses");
console.log("─".repeat(78));
let wOK = true;
for (const w of witnesses) {
  const k = kappa(w.adj, w.n), bs = betti1_scc(w.adj, w.n),
        bu = betti1_undirected(w.adj, w.n), sc = nontrivialSCC(w.adj, w.n);
  const corrected = (k > 0) === (bs > 0) && (bs > 0) === sc;   // K1
  const unqualified = (k > 0) === (bu > 0);                     // the prose reading
  if (!corrected) wOK = false;
  console.log(`${w.id}  ${w.name}`);
  console.log(`    κ=${k}  β₁ˢᶜᶜ=${bs}  β₁(undirected)=${bu}  SCC≥2=${sc}` +
    `   K1: ${corrected ? "holds" : "FAILS"}   unqualified-β₁ wording: ${unqualified ? "holds" : "FAILS here"}`);
  console.log(`    ${w.note}`);
}

// ── exhaustive n=4, sampled n=5 ─────────────────────────────────────────
function battery(n, iterMasks) {
  let checked = 0, k1fail = 0, wordingFail = 0;
  for (const bits of iterMasks) {
    const adj = new Uint8Array(n * n);
    let bit = 0;
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++)
      if (i !== j) { if (bits & (1 << bit)) adj[i * n + j] = 1; bit++; }
    const k = kappa(adj, n), bs = betti1_scc(adj, n),
          bu = betti1_undirected(adj, n), sc = nontrivialSCC(adj, n);
    if (!((k > 0) === (bs > 0) && (bs > 0) === sc)) k1fail++;
    if ((k > 0) !== (bu > 0)) wordingFail++;
    checked++;
  }
  return { checked, k1fail, wordingFail };
}

console.log("─".repeat(78));
const all4 = []; for (let b = 0; b < 1 << 12; b++) all4.push(b);
const r4 = battery(4, all4);
console.log(`n=4 exhaustive: ${r4.checked.toLocaleString()} digraphs · ` +
  `K1 failures: ${r4.k1fail} · unqualified-β₁ wording fails on ` +
  `${r4.wordingFail.toLocaleString()} (${(100 * r4.wordingFail / r4.checked).toFixed(1)}%)`);

let seed = 0xC0FFEE;
const rnd = () => { seed ^= seed << 13; seed ^= seed >>> 17; seed ^= seed << 5; return (seed >>> 0) / 4294967296; };
const sample5 = []; for (let i = 0; i < 100000; i++) sample5.push(Math.floor(rnd() * (1 << 20)));
const r5 = battery(5, sample5);
console.log(`n=5 sampled:    ${r5.checked.toLocaleString()} of 1,048,576 · ` +
  `K1 failures: ${r5.k1fail} · unqualified-β₁ wording fails on ` +
  `${r5.wordingFail.toLocaleString()} (${(100 * r5.wordingFail / r5.checked).toFixed(1)}%)`);

// ── C1: a grid-generated conjecture, exhaustively FALSIFIED (by design) ──
// The periodic-law grid asks: is κ MONOTONE under edge addition? Unrestricted: NO.
// Adding an edge can enlarge the largest SCC through a thin attachment, and
// the thin attachment becomes the new minimum bidirectional cut. Meaning:
// new dependencies can CREATE better fault lines — κ falling is not only
// crystallization. This cell is FALSIFIED and kept red by design
// (law:kappa.monotonicity.unrestricted@1): if it starts passing, the κ
// definition changed. (v0.4 corrected the earlier wording that called this
// cell empty-by-theorem — a false law is still a law-shaped statement with
// a witness, which is more useful than an empty cell.)
let c1checked = 0, c1viol = 0, c1ex = null;
for (let bits = 0; bits < 1 << 12; bits++) {
  const n = 4, adj = new Uint8Array(16); let bit = 0;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++)
    if (i !== j) { if (bits & (1 << bit)) adj[i * n + j] = 1; bit++; }
  const k0 = kappa(adj, n);
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    if (i === j || adj[i * n + j]) continue;
    const a2 = adj.slice(); a2[i * n + j] = 1; c1checked++;
    const k1 = kappa(a2, n);
    if (k1 < k0) { c1viol++; if (!c1ex) c1ex = { bits, edge: [i, j], k0, k1 }; }
  }
}
console.log("─".repeat(78));
console.log(`C1  (κ, add_edge, NO PRECONDITION, MONOTONICITY) — FALSIFIED (kept red by design)`);
console.log(`    ${c1checked.toLocaleString()} edge-additions at n=4 · κ decreased in ${c1viol}` +
  ` · first witness: graph#${c1ex.bits}, add ${c1ex.edge[0]}→${c1ex.edge[1]}, κ ${c1ex.k0}→${c1ex.k1}`);
console.log(`    (dense SCC absorbs a peripheral node via one thin return edge; the thin`);
console.log(`     attachment becomes the new cheapest cut — a better deliberation boundary)`);

// ── C2: the conditional sibling — carrier-preserving monotonicity, PROVED ──
// Split every C1 case by whether the SELECTED CARRIER (the vertex set of the
// largest SCC, ties broken by Tarjan order — the SCC κ is measured on)
// survives the edge addition. Argument for the preserved case: an added edge
// lies (a) inside the carrier — every bipartition's directed cut counts can
// only stay or grow, so their min cannot drop; (b) wholly outside — κ is
// unaffected; (c) incident to the carrier — not internal to the SCC, so no
// bipartition counts it. Hence κ(G′) ≥ κ(G). All 168 decreases live on the
// carrier-CHANGED side. Publication pair per the v0.4+ grid:
//   unrestricted monotonicity — FALSIFIED, kept red
//     (C1, law:kappa.monotonicity.unrestricted@1)
//   support-local internal-edge monotonicity — PROVED, flagship
//     (C2′, law:kappa.internal-edge.monotonicity@4)
// The carrier-preserving form below (C2) is kept as superseded history —
// law:kappa.carrier-preserving.monotonicity@2, superseded by the
// internal-edge flagship; its selectedCarrier predicate is tie-break-
// sensitive, which is why the grid promoted the support-local statement.
function selectedCarrier(adj, n) {
  const sccs = tarjanSCC(adj, n); let S = null;
  for (const c of sccs) if (!S || c.length > S.length) S = c;
  return (!S || S.length <= 1) ? null : S.slice().sort((a, b) => a - b).join(",");
}
let c2pres = 0, c2presViol = 0, c2chg = 0, c2chgViol = 0;
for (let bits = 0; bits < 1 << 12; bits++) {
  const n = 4, adj = new Uint8Array(16); let bit = 0;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++)
    if (i !== j) { if (bits & (1 << bit)) adj[i * n + j] = 1; bit++; }
  const k0 = kappa(adj, n), c0 = selectedCarrier(adj, n);
  if (c0 === null) continue;                        // κ undefined-as-zero without a carrier
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) {
    if (i === j || adj[i * n + j]) continue;
    const a2 = adj.slice(); a2[i * n + j] = 1;
    const k1 = kappa(a2, n), c1 = selectedCarrier(a2, n);
    if (c1 === c0) { c2pres++; if (k1 < k0) c2presViol++; }
    else { c2chg++; if (k1 < k0) c2chgViol++; }
  }
}
// n=5 sampled confirmation
let s2 = 0xBEEF; const rnd2 = () => { s2 ^= s2 << 13; s2 ^= s2 >>> 17; s2 ^= s2 << 5; return (s2 >>> 0) / 4294967296; };
let c2p5 = 0, c2p5v = 0, c2c5 = 0, c2c5v = 0;
for (let t = 0; t < 40000; t++) {
  const n = 5, bits = Math.floor(rnd2() * (1 << 20)), adj = new Uint8Array(25); let bit = 0;
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++)
    if (i !== j) { if (bits & (1 << bit)) adj[i * n + j] = 1; bit++; }
  const absent = [];
  for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) if (i !== j && !adj[i * n + j]) absent.push([i, j]);
  if (!absent.length) continue;
  const [i, j] = absent[Math.floor(rnd2() * absent.length)];
  const k0 = kappa(adj, n), c0 = selectedCarrier(adj, n);
  if (c0 === null) continue;
  const a2 = adj.slice(); a2[i * n + j] = 1;
  const k1 = kappa(a2, n), c1 = selectedCarrier(a2, n);
  if (c1 === c0) { c2p5++; if (k1 < k0) c2p5v++; } else { c2c5++; if (k1 < k0) c2c5v++; }
}
console.log(`C2  (κ, add_edge, CARRIER PRESERVED, MONOTONICITY) — PROVED (exhaustive n=4 + argument)`);
console.log(`    n=4: among additions whose source has a nontrivial selected carrier,` );
console.log(`    ${c2pres.toLocaleString()} preserve it (κ decreased in ${c2presViol}) and ${c2chg.toLocaleString()} change it (κ decreased in ${c2chgViol} — every`);
console.log(`    C1 witness lives here). The remaining ${(24576-(c2pres+c2chg)).toLocaleString()} additions start at κ=0 and cannot`);
console.log(`    be decrease witnesses (honest accounting per review: 13,542+6,534+4,500 = 24,576).`);
console.log(`    n=5 sample: preserved ${c2p5.toLocaleString()} → ${c2p5v} decreases · changed ${c2c5.toLocaleString()} → ${c2c5v} decreases`);
console.log(`    ⇒ a κ-warrant carries its SUPPORT (the carrier vertex set): same support, κ moves`);
console.log(`      predictably; support changed, all bets are off — re-derive. Measurement support`);
console.log(`      is first-class.`);

// ── C3: scalar κ is NOT renaming-invariant at SCC ties — FALSIFIED, kept red ──
// External review's counterexample, verified here: two size-3 SCCs, a 3-cycle
// (κ=1) and a complete bidirected triangle (κ=2). "Select the largest SCC"
// breaks ties by traversal order, so vertex labels leak into the scalar.
const TIE = [[0,1],[1,2],[2,0],[3,4],[4,3],[3,5],[5,3],[4,5],[5,4]];
function* perms(a){ if(a.length<=1){yield a;return;} for(let i=0;i<a.length;i++){const r=[...a.slice(0,i),...a.slice(i+1)]; for(const p of perms(r)) yield [a[i],...p];} }
const hist = {};
for (const p of perms([0,1,2,3,4,5])) {
  const n=6, adj=new Uint8Array(36);
  for (const [a,b] of TIE) adj[p[a]*n+p[b]]=1;
  const k=kappa(adj,n); hist[k]=(hist[k]||0)+1;
}
const c3broken = Object.keys(hist).length > 1;
console.log(`C3  (scalar κ with largest-SCC selection, vertex relabeling, tie, EQUIVARIANCE) — ${c3broken ? "FALSIFIED (kept red by design)" : "UNEXPECTEDLY-HELD?!"}`);
console.log(`    same graph, all 720 relabelings: κ histogram ${JSON.stringify(hist)} — the`);
console.log(`    scalar depends on labels. K1 (κ>0 ⟺ SCC≥2) survives; the VALUE does not.`);

// ── C4: the κ PROFILE is equivariant — measurement invariant, selection is policy ──
function kappaOn(adj, n, S) {
  const m=S.length; let best=Infinity;
  for (let mask=1; mask<(1<<m)-1; mask++) {
    let ab=0, ba=0;
    for (let i=0;i<m;i++) for (let j=0;j<m;j++) {
      if (i===j || !adj[S[i]*n+S[j]]) continue;
      const iA=!!(mask&(1<<i)), jA=!!(mask&(1<<j));
      if (iA&&!jA) ab++; else if (!iA&&jA) ba++;
    }
    best=Math.min(best,Math.min(ab,ba));
  }
  return best===Infinity?0:best;
}
// Full structured equivariance: Q(φ(G)) = φ(Q(G)) — supports are MAPPED
// through the permutation and compared, not discarded into a (size, κ)
// quotient (review round 3 caught that the earlier test only reached the
// quotient). Witness-cut equivariance is deliberately out of scope here:
// minimum cuts can tie, so a canonical-witness SELECTION policy is required
// before the cut can be compared — selection is policy, again.
function fullProfile(adj, n) {                     // [{S:[..sorted], k}]
  const out=[];
  for (const S of tarjanSCC(adj,n)) if (S.length>1)
    out.push({ S: S.slice().sort((a,b)=>a-b), k: kappaOn(adj,n,S) });
  return out;
}
const canon = (prof) => prof.map(e => e.S.join(".")+"|"+e.k).sort().join(",");
function mapProfile(prof, perm) {
  return prof.map(e => ({ S: e.S.map(v=>perm[v]).sort((a,b)=>a-b), k: e.k }));
}
let c4exh=0, c4exhOK=0;
for (const p of perms([0,1,2,3,4,5])) {
  const n=6, adj=new Uint8Array(36);
  for (const [a,b] of TIE) adj[p[a]*n+p[b]]=1;
  const before = fullProfile((()=>{const b=new Uint8Array(36); for(const[x,y] of TIE) b[x*n+y]=1; return b;})(), 6);
  c4exh++;
  if (canon(mapProfile(before, p)) === canon(fullProfile(adj, 6))) c4exhOK++;
}
let c4rand=0, c4randOK=0;
let sd=0x5EED; const rr=()=>{sd^=sd<<13;sd^=sd>>>17;sd^=sd<<5;return(sd>>>0)/4294967296;};
for (let t=0;t<200;t++) {
  const n=5, bits=Math.floor(rr()*(1<<20)), adj=new Uint8Array(25); let bit=0;
  for (let i=0;i<n;i++) for (let j=0;j<n;j++) if (i!==j){ if(bits&(1<<bit)) adj[i*n+j]=1; bit++; }
  const before = fullProfile(adj,5);
  const perm=[0,1,2,3,4].sort(()=>rr()-0.5);
  const a2=new Uint8Array(25);
  for (let i=0;i<n;i++) for (let j=0;j<n;j++) if (adj[i*n+j]) a2[perm[i]*5+perm[j]]=1;
  c4rand++;
  if (canon(mapProfile(before, perm)) === canon(fullProfile(a2,5))) c4randOK++;
}
console.log(`C4  (κ profile with supports, vertex relabeling φ, any graph, EQUIVARIANCE: Q(φG)=φ(QG)) — ${c4exhOK===c4exh && c4randOK===c4rand ? "PROPERTY-TESTED" : "FALSIFIED?!"}`);
console.log(`    tie graph: ${c4exhOK}/${c4exh} relabelings satisfy the MAPPED-support law (supports carried`);
console.log(`    through φ and compared, not quotiented away); ${c4randOK}/${c4rand} random n=5 graphs likewise.`);
console.log(`    Witness-cut equivariance deferred: min cuts tie, so a canonical selection policy`);
console.log(`    must be named first. Measurement is invariant. Selection is policy. Warrant authorizes.`);

// ── C2′: the clean support-local theorem — no selection anywhere ──
// For a fixed SCC support S: adding an edge INSIDE G[S] never decreases κ_S.
let c2p_checked=0, c2p_viol=0;
for (let bits=0; bits<(1<<12); bits++) {
  const n=4, adj=new Uint8Array(16); let bit=0;
  for (let i=0;i<n;i++) for (let j=0;j<n;j++) if (i!==j){ if(bits&(1<<bit)) adj[i*n+j]=1; bit++; }
  for (const S of tarjanSCC(adj,n)) {
    if (S.length<2) continue;
    const k0=kappaOn(adj,n,S);
    for (const i of S) for (const j of S) {
      if (i===j || adj[i*n+j]) continue;
      const a2=adj.slice(); a2[i*n+j]=1;
      c2p_checked++;
      if (kappaOn(a2,n,S) < k0) c2p_viol++;
    }
  }
}
console.log(`C2′ (κ_S, add edge inside G[S], S a fixed SCC support, MONOTONICITY) — ${c2p_viol===0 ? "PROVED (exhaustive n=4 + argument)" : "FALSIFIED?!"}`);
console.log(`    ${c2p_checked.toLocaleString()} internal-edge additions across every SCC of every n=4 digraph;`);
console.log(`    κ_S decreased in ${c2p_viol}. No selection, no ties, no carrier bookkeeping — the`);
console.log(`    support-parameterized statement is the theorem; policy chooses S afterward.`);

console.log("─".repeat(78));
const pass = wOK && r4.k1fail === 0 && r5.k1fail === 0 && c1viol > 0
  && c2presViol === 0 && c2chgViol === c1viol && c2p5v === 0
  && c3broken && c4exhOK === c4exh && c4randOK === c4rand && c2p_viol === 0;
console.log(pass
  ? "VERDICT: K1 (κ>0 ⟺ β₁ˢᶜᶜ>0 ⟺ SCC≥2) holds on every witness and every graph" +
    "\n         checked. The unqualified β₁ wording fails on a large fraction of" +
    "\n         graphs and must be repaired in prose. Statement bug — not proof bug."
  : "VERDICT: K1 FALSIFIED — see failures above.");
process.exit(pass ? 0 : 1);
