/* MEASURE FIRST, BUILD NOTHING. GPT's instruction for the church_exp_2_2 round,
   and round 26's own lesson: the film emitter's blocker was mis-stated because
   nobody had measured which rules actually FIRE on the fixture.

   This prints what the reference kernel actually does on the canonical
   church_exp_2_2 state — frame count, rule sequence, locus sequence, pre/post
   ids, which rules fire, which locus families appear — so the next round builds
   only what the measurement requires. It asserts nothing and gates nothing. */
import {
  parse, extrude, FloatRt, semStateId, semStateSignature, readback,
  findFloatRedexes, semLocusOf, fireFloat, liveDiscoveryOrder, PLANE_POOL_FREE, PLANE_OF,
} from "./trvm_law_kernel.mjs";

const TERM = "((λf.λx.!&1001{c0,c1}=f;(c0 (c1 x)) λf.λx.!&1002{c0,c1}=f;(c0 (c1 x))) S)";
const EXPECTED_NF = "λa.(S (S (S (S a))))";
const CORPUS_REF_INTERACTIONS = 21;

const rt = new FloatRt();
let st = extrude(rt, parse(rt, TERM));

console.log("church_exp_2_2");
console.log("  term  :", TERM);
console.log("  corpus nf              :", EXPECTED_NF);
console.log("  corpus ref_interactions:", CORPUS_REF_INTERACTIONS,
  "  <- an AST-reference count, NOT a promise about frame count");
console.log("  initial semStateId     :", semStateId(rt, st).slice(0, 24));
console.log();

const rules = new Map(), loci = new Map(), frames = [];
let step = 0;
const BUDGET = 500;
let terminal = "NORMAL_FORM";

for (;;) {
  const rx = findFloatRedexes(rt, st, PLANE_POOL_FREE);
  if (rx.length === 0) break;
  if (step >= BUDGET) { terminal = "BUDGET_EXHAUSTED"; break; }
  // LEFTMOST, the strategy the shipped film emitter follows. Recorded as a
  // choice rather than assumed: a different strategy is a different film, and
  // that is the thing this measurement exists to pin down before anyone builds.
  const pick = rx[0];
  const order = liveDiscoveryOrder(rt, st);
  const pre = semStateId(rt, st);
  const locus = semLocusOf(pick, order);
  const after = fireFloat(rt, st, pick);
  st = after.root;
  const post = semStateId(rt, st);
  pick.rule = after.rule ?? pick.rule;
  rules.set(pick.rule, (rules.get(pick.rule) ?? 0) + 1);
  const fam = String(locus).split(":")[0] + ":";
  loci.set(fam, (loci.get(fam) ?? 0) + 1);
  frames.push({ n: ++step, rule: pick.rule, plane: PLANE_OF[pick.rule], locus: String(locus),
    pre: pre.slice(0, 10), post: post.slice(0, 10), enabled: rx.length });
}

console.log(`FRAMES: ${frames.length}   terminal: ${terminal}`);
console.log("  n  rule        plane      locus                    pre→post          enabled");
for (const f of frames)
  console.log(`  ${String(f.n).padStart(2)}  ${f.rule.padEnd(11)} ${String(f.plane).padEnd(10)} ` +
    `${f.locus.padEnd(24)} ${f.pre}→${f.post}  ${f.enabled}`);

console.log("\nRULES THAT ACTUALLY FIRE:");
for (const [r, c] of [...rules].sort()) console.log(`  ${r.padEnd(12)} ${c}`);
console.log("\nRULES THAT NEVER FIRE (of the declared pool):");
for (const r of [...PLANE_POOL_FREE].sort()) if (!rules.has(r)) console.log(`  ${r}`);
console.log("\nLOCUS FAMILIES:");
for (const [l, c] of [...loci].sort()) console.log(`  ${l.padEnd(4)} ${c}`);

// readback returns a RECORD, not a string — comparing it to the corpus string
// silently reported "false" against a normal form that matches exactly.
const nf = readback(rt, st);
console.log("\nFINAL");
console.log("  readback.str     :", nf.str);
console.log("  matches corpus nf:", nf.str === EXPECTED_NF);
console.log("  interactFired    :", nf.interactFired, " collapseFired:", nf.collapseFired,
  " liveCount:", nf.liveCount);
console.log("  final semStateId :", semStateId(rt, st).slice(0, 24));
console.log("  signature len    :", semStateSignature(rt, st).length,
  "(>80 is §5-COMPACTED and the decoder refuses it)");
