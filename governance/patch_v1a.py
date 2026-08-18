# patch_v1a.py — stage A of the v1.0.0 build: identity, allocator, schedulers,
# and the semantic state-identity library. Applied to build_v1.py in place.
import io, sys

src = open("build_v1.py", encoding="utf-8").read()
def rep(a, b, n=1):
    global src
    assert src.count(a) == n, f"anchor not unique ({src.count(a)}x): {a[:80]!r}"
    src = src.replace(a, b)

# ── R0: build-script self-description (GPT's identity nit) ────────────────
rep("# Assembles trvm_law_kernel.mjs v0.5 from verbatim v0.4 segments + new sections.",
    "# Assembles trvm_law_kernel.mjs v1.0.0 from verbatim v0.4 blocks + new sections.")

# ── R1: header — v1.0.0 title + new round block; retitle v0.6 block ───────
rep('''HEADER = \'\'\'/* ═══════════════════════════════════════════════════════════════════════════
   trvm_law_kernel.mjs — v0.6 — a law-governed Interaction Calculus kernel''',
    '''HEADER = \'\'\'/* ═══════════════════════════════════════════════════════════════════════════
   trvm_law_kernel.mjs — v1.0.0 — a law-governed Interaction Calculus kernel''')

rep('''   into the runtime's own falsifier — and, this round, evidence artifacts
   whose AUTHORITY cannot outrun the evidence they carry.

   WHAT CHANGED IN v0.6 (round 5 — the evidence-binding round)''',
    '''   into the runtime's own falsifier — with evidence artifacts whose
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

   CARRIED FROM v0.6 (round 5 — the evidence-binding round)''')

# ── R2: KERNEL_VERSION const after the imports at the end of HEADER ───────
rep('''import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
\'\'\'''',
    '''import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
const KERNEL_VERSION = "1.0.0";
\'\'\'''')

# ── R3: banner uses the constant ──────────────────────────────────────────
rep('console.log("trvm_law_kernel v0.5 — conformance + the periodic-law grid, compiled to its own falsifier");',
    'console.log(`trvm_law_kernel v${KERNEL_VERSION} — conformance + the periodic-law grid, compiled to its own falsifier`);')

# ── R4: adversarial descending allocator (after FloatRt) ──────────────────
rep('''class FloatRt extends Rt {
  constructor() { super(); this.heap = new Map(); this.did = 0; } // id -> {lab,l,r,val}
  alloc(lab, l, r, val) { this.heap.set(++this.did, { lab, l, r, val }); return this.did; }
}''',
    '''class FloatRt extends Rt {
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
}''')

# ── R5: semantic state identity library, after floatDigest ────────────────
rep('''function floatDigest(frt, root) { return stateDigest(frt, foldHeap(frt, root)); }''',
    '''function floatDigest(frt, root) { return stateDigest(frt, foldHeap(frt, root)); }

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
function semFilmIdOf(t) {
  return h31("TRVM-SEMFILM-v1|" + t.last_frame + "|" + t.termination + "|" + t.steps + "|" +
    t.final_sem_id + "|" + (t.normal_form_id ?? "-") + "|" + (t.planes ?? []).join(","));
}
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
    if (!permitted.has(frame.plane)) return { ok: false, at: n, reason: "sem-plane-not-permitted" };
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
}''')

# ── R6: two starvation schedulers ─────────────────────────────────────────
rep('''const SCHEDULERS = {
  leftmost: (rs, rnd) => rs[0],
  deepest:  (rs, rnd) => rs[rs.length - 1],
  middle:   (rs, rnd) => rs[Math.floor(rs.length / 2)],
  random:   (rs, rnd) => rs[Math.floor(rnd() * rs.length)],
};''',
    '''const SCHEDULERS = {
  leftmost: (rs, rnd) => rs[0],
  deepest:  (rs, rnd) => rs[rs.length - 1],
  middle:   (rs, rnd) => rs[Math.floor(rs.length / 2)],
  random:   (rs, rnd) => rs[Math.floor(rnd() * rs.length)],
  // starvation adversaries (law:sched.adversarial.float@1): each persistently
  // avoids a whole redex CLASS for as long as any alternative is enabled.
  // Completion under these is a fairness result, not a scheduling accident.
  starve_dups: (rs, rnd) => rs.find((r) => r.kind === "app") ?? rs[Math.floor(rnd() * rs.length)],
  starve_apps: (rs, rnd) => rs.find((r) => r.kind === "dup") ?? rs[Math.floor(rnd() * rs.length)],
};''')

open("build_v1.py", "w", encoding="utf-8").write(src)
print("stage A applied:", len(src.splitlines()), "lines")
