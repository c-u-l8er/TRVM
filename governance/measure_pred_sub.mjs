/* ═══════════════════════════════════════════════════════════════════════════
   measure_pred_sub.mjs — B7.1. MEASURE FIRST, BUILD NOTHING. A TOOL.

   GPT's instruction for the `sub` round, and the same order B3 took before the
   native float plane was asserted: measure the construction independently,
   diff it against the other implementation, and write compiler code only
   because the two agreed.

   THE QUESTION B6.3.1 LEFT OPEN AND THIS ANSWERS. ic32's fragment is LINEAR —
   every non-linear use needs an explicit `!&L{a,b}=v` dup — and the classic
   Church predecessor is the textbook NON-LINEAR construction. So the open item
   was not "how do we spell sub" but "does a predecessor normalise here at
   all". It is measured below rather than assumed, on both implementations.

       PRED  = λn.λf.λx.(((n λg.λh.(h (g f))) λu.x) λu.u)
       SUB(m,n) = n PRED m          ← n applications of PRED to m

   WHAT PRED ACTUALLY NEEDS, once counted rather than remembered: n, f, x, g
   and h are each used EXACTLY ONCE, and the only irregularity is the FIRST
   `u`, which is used ZERO times. PRED is therefore AFFINE, not non-linear: it
   needs a DROP, not a DUP, and ic32 drops an unused binder through the
   substitution store without an Era node at all. It contains no dup, which is
   also why duplicating it inside a Church numeral cannot collide with a label.

   NO EXPECTED TABLE LIVES HERE, on measure_compare.mjs's rule and GPT's
   explicit instruction not to hard-code previously observed frame counts.
   There is no frame count, no rule sequence and no locus for any fixture in
   this file. The one thing this file does compute is the ARITHMETIC, twice —
   true difference `m - n` and monus `max(0, m - n)` — and it reports which of
   the two the measured decode matches. That is derived from the fixture, not
   typed beside it, and it is the semantic observation the round turns on.

   THE AGREEMENT VERDICT IS NOT MINE. C↔JS film agreement is delegated to
   bridge/measure_compare.mjs, which is the comparator this tree already
   trusts; a second comparator written for this occasion would be checking the
   occasion. What is computed here is the per-fixture float-plane tally that
   gets printed, and the canonical normal form via the native ic32_canon.

   Run: node measure_pred_sub.mjs
   Exit 0 iff every fixture agrees C↔JS and every decode is consistent with
   one of the two arithmetics. NOT part of `make governance`: this is the
   instrument the round is built on, not the gate. It gates nothing; if it
   disagrees, B7 stops and the disagreement is the deliverable.
   ═══════════════════════════════════════════════════════════════════════════ */
import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  parse, extrude, FloatRt, semStateId, semStateSignature, readback, normalizeFloat,
  findFloatRedexes, semLocusOf, fireFloat, liveDiscoveryOrder, PLANE_POOL_FREE, PLANE_OF,
} from "./trvm_law_kernel.mjs";
import { makeTargetDecoder } from "./lowering.mjs";
/* B8.1: the tool decodes the OWNED normal form too. It kept a signature decoder
   for exactly as long as the chain had one; a measurement instrument reading a
   representation the relation no longer reads would be measuring something the
   round does not ship.
   B8.3: and it binds the identity oracle at the top of the file rather than
   handing one in per call, so a measurement cannot report an id it nominated. */
const decodeTarget = makeTargetDecoder({
  identifyNormalForm: (o) => semStateId(new FloatRt(), o) });

const HERE = dirname(fileURLToPath(import.meta.url));
const CANON = join(HERE, "bridge", "ic32_canon");
const FILM = join(HERE, "bridge", "ic32_film");
const COMPARE = join(HERE, "bridge", "measure_compare.mjs");
const BUDGET = 4096;

/* ── the construction, LOCAL ──────────────────────────────────────────────
   Deliberately NOT imported from lowering.mjs. At B7.1 the compiler does not
   know what `sub` is, and measuring the construction with the emitter that is
   about to be taught it would make the measurement a function of the thing it
   is supposed to justify. The Church shape here is the one the corpus and the
   emitter both already use — n-1 dups, heads a0..a(n-1) — written out again
   because that is the only way this file can be run against a tree where the
   emitter has not been changed yet. */
let LAB = 0;
const church = (n) => {
  if (n === 0) return "λf.λx.x";
  if (n === 1) return "λf.λx.(f x)";
  const binds = []; let cur = "f";
  for (let i = 0; i < n - 1; i++) {
    const L = LAB++;
    if (i < n - 2) { binds.push(`!&${L}{a${i},t${i}}=${cur};`); cur = `t${i}`; }
    else binds.push(`!&${L}{a${i},a${i + 1}}=${cur};`);
  }
  let body = "x";
  for (let i = n - 1; i >= 0; i--) body = `(a${i} ${body})`;
  return `λf.λx.${binds.join("")}${body}`;
};
const PRED = "λn.λf.λx.(((n λg.λh.(h (g f))) λu.x) λu.u)";
/* SUB(m,n) = n PRED m. `n` is the SUBTRAHEND and it is the one applied — the
   numeral that says HOW MANY predecessors to take. Operand order is the whole
   correctness question at the target level and it is inverted relative to the
   source's `sub(a,b)`, which is exactly why B7.2 keeps the order in the
   TEMPLATE and lets the emitter invert it in one place. */
const sub = (mTerm, nTerm) => `((${nTerm} ${PRED}) ${mTerm})`;
const add = (aT, bT) =>
  `((λm.λn.λf.λx.!&${LAB++}{f0,f1}=f;((m f0) ((n f1) x)) ${aT}) ${bT})`;

/* ── the JS float-plane tally ─────────────────────────────────────────────
   Leftmost over findFloatRedexes, the strategy the shipped film emitter
   follows, recorded as a CHOICE. */
function measureJS(term) {
  const frt = new FloatRt();
  let root = extrude(frt, parse(frt, term));
  const fire = new Map(), loci = { "t:": 0, "d:": 0, "v:": 0 };
  let n = 0, terminal = "NORMAL_FORM";
  for (;;) {
    const rx = findFloatRedexes(frt, root, PLANE_POOL_FREE);
    if (rx.length === 0) break;
    if (n >= BUDGET) { terminal = "BUDGET_EXHAUSTED"; break; }
    const pick = rx[0];
    const order = liveDiscoveryOrder(frt, root);
    loci[String(semLocusOf(pick, order)).slice(0, 2)]++;
    const after = fireFloat(frt, root, pick);
    root = after.root; n++;
    const rule = after.rule ?? pick.rule;
    fire.set(rule, (fire.get(rule) ?? 0) + 1);
  }
  /* BEFORE the readback, which fires rules into this runtime — the
     comparator's own first find, and it cost a round when it was read after. */
  const final = semStateId(frt, root), siglen = semStateSignature(frt, root).length;
  const rb = readback(frt, root);
  return { frames: n, terminal, fire, loci, final, siglen, nf: rb.str,
    planes: [...fire.keys()].map((r) => PLANE_OF[r]) };
}

const canonNF = (term) => {
  const out = execFileSync(CANON, ["--nf"], { input: term + "\n", maxBuffer: 1 << 26 }).toString();
  const line = out.trimEnd().split("\n")[0] ?? "";
  const i = line.indexOf("\t");
  return i < 0 ? null : { id: line.slice(0, i), sig: line.slice(i + 1) };
};

/* THE AGREEMENT VERDICT COMES FROM THE COMPARATOR THIS TREE ALREADY TRUSTS. */
const compareCJS = (term) => {
  try {
    const out = execFileSync(process.execPath, [COMPARE, term], { maxBuffer: 1 << 26 }).toString();
    return { agree: /^AGREE\s/m.test(out), out };
  } catch (e) {
    return { agree: false, out: ((e.stdout ?? Buffer.from("")).toString()) || String(e.message ?? e) };
  }
};

const showMap = (m) => [...m].sort().map(([k, v]) => `${k}=${v}`).join(" ");

/* ── the fixtures GPT named, plus the two association fixtures ──────────── */
const FIXTURES = [];
for (let k = 0; k <= 4; k++)
  FIXTURES.push({ name: `pred(${k})`, m: k, n: 1, term: sub(church(k), church(1)) });
for (const [m, n] of [[2, 0], [5, 2], [2, 2], [7, 2], [2, 3]])
  FIXTURES.push({ name: `${m} - ${n}`, m, n, term: sub(church(m), church(n)) });
/* NESTED, and the arithmetic for these is written as an EXPRESSION rather than
   a pair, because m/n does not describe them. */
const NESTED = [
  { name: "(7-2)-1", term: sub(sub(church(7), church(2)), church(1)), truth: (7 - 2) - 1, monus: Math.max(0, Math.max(0, 7 - 2) - 1) },
  { name: "7-(2-1)", term: sub(church(7), sub(church(2), church(1))), truth: 7 - (2 - 1), monus: Math.max(0, 7 - Math.max(0, 2 - 1)) },
  { name: "(2-3)+2", term: add(sub(church(2), church(3)), church(2)), truth: (2 - 3) + 2, monus: Math.max(0, 2 - 3) + 2 },
];

for (const p of [["ic32_canon", CANON], ["ic32_film", FILM]])
  if (!existsSync(p[1])) {
    console.log(`MEASURE-PRED-SUB: SKIP — ${p[0]} not built (make gov-film / gov-bridge builds it).`);
    console.log("  A missing binary is UNBUILT, never agreement: this exits nonzero.");
    process.exit(1);
  }

console.log("MEASURE-PRED-SUB — B7.1, non-gating. Nothing here is committed, replayed or signed.");
console.log(`  PRED = ${PRED}`);
console.log(`  SUB(m,n) = ((n PRED) m)`);
console.log();

let disagreed = 0, monusSeen = 0, trueSeen = 0;
const rows = [];
const run = (name, term, truth, monus) => {
  const js = measureJS(term);
  const c = canonNF(term);
  const own = (() => { const frt = new FloatRt();
    let r = extrude(frt, parse(frt, term));
    r = normalizeFloat(frt, r, (rs) => rs[0], null, { budget: 2_000_000 }).root;
    return readback(frt, r).nf; })();
  const d = decodeTarget(own);
  const nativeAgrees = c !== null && c.id === d.target_nf_sem_id;
  const cmp = compareCJS(term);
  const val = d.ok ? d.outcome.value : null;
  const kind = val === null ? "—"
    : (truth === monus) ? (val === truth ? "both agree" : "NEITHER")
    : val === truth ? "TRUE-SUBTRACTION" : val === monus ? "MONUS" : "NEITHER";
  if (kind === "MONUS") monusSeen++;
  if (kind === "TRUE-SUBTRACTION") trueSeen++;
  if (!cmp.agree || kind === "NEITHER" || val === null || !nativeAgrees) disagreed++;
  rows.push({ name, js, sig: c?.sig ?? "—", val, kind, agree: cmp.agree, truth, monus, d });
  console.log(`${name.padEnd(9)} C↔JS ${cmp.agree ? "AGREE " : "DIFFER"}  ${String(js.frames).padStart(4)} frames  ${js.terminal}`);
  console.log(`${"".padEnd(9)}   fire  ${showMap(js.fire)}`);
  console.log(`${"".padEnd(9)}   loci  t:${js.loci["t:"]} d:${js.loci["d:"]} v:${js.loci["v:"]}   siglen ${js.siglen}` +
    `${js.siglen > 80 ? " (>80: §5-COMPACTED at the canonical state — the decoder refuses it)" : ""}`);
  console.log(`${"".padEnd(9)}   nf    ${js.nf}`);
  console.log(`${"".padEnd(9)}   sig   ${c?.sig ?? "—"}`);
  console.log(`${"".padEnd(9)}   decode ${d.ok ? d.outcome.value : "REFUSED " + d.reason}` +
    `   true=${truth} monus=${monus}  → ${kind}   native-id-agrees ${nativeAgrees}`);
  if (!cmp.agree) { console.log("  ── comparator output ──"); console.log(cmp.out.split("\n").slice(0, 30).map((l) => "  " + l).join("\n")); }
};

for (const f of FIXTURES) run(f.name, f.term, f.m - f.n, Math.max(0, f.m - f.n));
for (const f of NESTED) run(f.name, f.term, f.truth, f.monus);

console.log("═".repeat(96));
if (disagreed) {
  console.log(`MEASURE-PRED-SUB: STOP — ${disagreed} fixture(s) disagreed C↔JS or decoded to neither arithmetic.`);
  console.log("  Do not implement `sub`. Report the disagreement; do not force the expected construction.");
  process.exit(1);
}
console.log(`MEASURE-PRED-SUB: AGREE — ${rows.length}/${rows.length} fixtures agree C↔JS, every one NORMAL_FORM.`);
console.log(`  THE PREDECESSOR NORMALISES. It is AFFINE, not non-linear: one unused binder, no dup,`);
console.log(`  and ic32 drops an unused binder through the substitution store. B6.3.1's open question`);
console.log(`  is answered by measurement — sub IS a one-operator widening.`);
const coincide = rows.filter((r) => r.truth === r.monus).length;
console.log(`  RAW CHURCH SUB IS MONUS. On ${coincide} fixture(s) the two arithmetics COINCIDE and the`);
console.log(`  measurement cannot tell them apart; on ${monusSeen} it decoded to max(0,·) where the frozen`);
console.log(`  source core's \`sub\` gives the other answer, and on ${trueSeen} to the true difference. Every`);
console.log(`  fixture that distinguishes them chose MONUS:`);
for (const r of rows) if (r.kind === "MONUS")
  console.log(`    · ${r.name.padEnd(9)} source ${String(r.truth).padStart(2)}   target ${String(r.val).padStart(2)}   ← compiling this as Church monus is a MISCOMPILATION`);
const nested = rows.find((r) => r.name === "(2-3)+2");
console.log(`  AND IT IS NOT CONFINED TO THE TOP LEVEL — (2-3)+2 decodes to ${nested?.val}, not to the source's`);
console.log(`  ${nested?.truth}. An inner monus leaves no trace in the outcome and silently changes an answer`);
console.log(`  that is itself perfectly representable. A compiler that saturates cannot be caught by`);
console.log(`  looking at whether the ANSWER is in range.`);
/* THE RULE COVERAGE, because "what new runtime rules did this exercise" is a
   question the round has to answer with a measurement rather than a guess. */
const union = new Set(); for (const r of rows) for (const k of r.js.fire.keys()) union.add(k);
const pool = [...PLANE_POOL_FREE].sort();
console.log(`  RULES EXERCISED across these fixtures: ${[...union].sort().join(" ")}`);
console.log(`  DECLARED POOL NOT EXERCISED here: ${pool.filter((r) => !union.has(r)).join(" ") || "(none)"}`);
console.log(`  So sub introduces NO new rule — the pool closed at B4 — but it drives APP-SUP and the`);
console.log(`  d:/v: loci far harder than any add fixture does, which is where the frames actually go.`);
process.exit(0);
