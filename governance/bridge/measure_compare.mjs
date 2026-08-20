/* ═══════════════════════════════════════════════════════════════════════════
   measure_compare.mjs — the C↔JS float-plane measurement diff. A TOOL.

   GPT's instruction for the church_exp_2_2 round, and round 26's lesson twice
   over: measure what the implementation actually does BEFORE writing down what
   a test expects it to do. `measure_exp22.mjs` measured the JS reference
   relation on one fixture. `ic32_film --measure` measures the native C
   relation. This runs both and DISCOVERS whether they match.

   WHAT IT COMPARES, and why the split matters
   ───────────────────────────────────────────
   SEMANTIC — a difference here is a difference in the relation:

       frame ordering · rule · plane · canonical locus · pre_sem_id
       post_sem_id · terminal class · steps · final_sem_id · normal form
       · normal_form_id

   DIAGNOSTIC — compared because a difference is informative about ENUMERATION,
   NOT because the number belongs in portable evidence:

       the whole ENABLED SET per frame (every live locus:rule, not its cardinality)
       · rule tally · locus-family tally · signature length

   The set of simultaneously enabled alternatives is extremely useful for
   localising an enumeration divergence and is deliberately NOT a semantic-film
   field. It is reported and diffed here, in a tool that commits nothing, and it
   does not travel in a frame. The SET rather than the COUNT, because two
   enumerations can agree on every chosen redex and every state across a whole
   corpus while disagreeing about what else was available — a divergence that
   stays invisible until the day the strategy changes.

   NOT COMPARED, and stated rather than quietly dropped: ic32's `interactions`
   counter is not plane-classified — it counts every fire(), APP-LAM and
   DUP-VAR alike — while the kernel's readback purity claim is about
   INTERACT-plane rules specifically. Comparing them would be comparing two
   different quantities that happen to agree on easy cases. Both are printed.

   NO EXPECTED TABLE LIVES HERE. There is no frame count, no rule sequence and
   no locus for any fixture in this file. Both sides are measured; the
   comparator only says whether the two measurements are the same measurement.

   The one thing the comparator must translate is OUTCOME CLASS: the C emitter
   answers an out-of-scope fixture with a typed refusal on stdout, and the JS
   reference relation just keeps going or stops. That mapping is a single
   visible table (`jsOutcome`), not a scattering of special cases.

   Run: node bridge/measure_compare.mjs                 corpus + exp_2_2 + film fixtures
        node bridge/measure_compare.mjs "<term>"        one term
   Exit 0 iff every measured pair agrees. NOT part of `make governance`:
   this is the instrument the conformance round is built on, not the gate. */
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import {
  parse, extrude, FloatRt, semStateId, semStateSignature, readback, semId,
  findFloatRedexes, semLocusOf, fireFloat, liveDiscoveryOrder, PLANE_POOL_FREE, PLANE_OF,
} from "../trvm_law_kernel.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
/* TRVM_FILM_BIN points the comparator at a DIFFERENT native emitter. This is a
   measurement instrument, not a verifier, and the distinction is the one round
   B2.1.2 drew: a verifier may not expose a "choose your judge" parameter, but a
   comparator whose whole job is "do these two implementations agree?" must be
   able to be handed the implementation. It exists so the comparator can be
   shown to FAIL — a perturbed C build must come back DIFFER, or agreement is
   not evidence of anything (law:evidence.instrument-nonvacuity@1). */
const BIN = process.env.TRVM_FILM_BIN ?? join(HERE, "ic32_film");
const BUDGET = 4096;

/* The rules the native emitter declares OUT OF SCOPE this round. Named once,
   here, because the comparator has to know what a refusal means — not because
   the JS relation has any such notion. exp_2_2 exercises neither, which is the
   measured fact that put them out of scope. */
const NATIVE_UNIMPLEMENTED = new Set(["APP-ERA", "DUP-ERA"]);

/* ── the JS reference measurement ─────────────────────────────────────────
   The kernel's own enumeration, its own locus construction, its own fire.
   LEFTMOST over findFloatRedexes, which lists every tree app redex before any
   dup redex — recorded as a choice, because a different strategy is a
   different film. */
function measureJS(term) {
  const frt = new FloatRt();
  let root;
  try { root = extrude(frt, parse(frt, term)); }
  catch (e) { return { outcome: "parse-error", detail: String(e.message ?? e) }; }

  const rows = [], fire = new Map();
  const loci = { "t:": 0, "d:": 0, "v:": 0 };
  const initial = semStateId(frt, root);

  for (let n = 0; ; n++) {
    const rx = findFloatRedexes(frt, root, PLANE_POOL_FREE);
    if (rx.length === 0) {
      if (n === 0) return { outcome: "no-redex-at-source" };
      break;
    }
    if (n >= BUDGET) return { outcome: "budget-exhausted", at: n };
    const pick = rx[0];
    if (NATIVE_UNIMPLEMENTED.has(pick.rule)) return { outcome: "era-rule-required", at: n, rule: pick.rule };

    const order = liveDiscoveryOrder(frt, root);
    const pre = semStateId(frt, root);
    const locus = String(semLocusOf(pick, order));
    /* THE WHOLE ENABLED SET, not its cardinality. A count says the two
       enumerations found the same NUMBER of alternatives; the set says they
       found the same ones. Two enumerations can agree on every chosen redex
       and every state for a whole corpus while disagreeing about what else was
       available — and the difference only becomes visible the first time a
       strategy changes. Diagnostic, not a film field: see the header. */
    const enabledSet = rx.map((r) => `${String(semLocusOf(r, order))}:${r.rule}`).join(" ");
    const after = fireFloat(frt, root, pick);
    root = after.root;
    const rule = after.rule ?? pick.rule;
    const post = semStateId(frt, root);
    rows.push({ n: n + 1, rule, plane: PLANE_OF[rule], locus, pre, post, enabled: rx.length, enabledSet });
    fire.set(rule, (fire.get(rule) ?? 0) + 1);
    loci[locus.slice(0, 2)]++;
  }

  /* THE TERMINAL STATE IS READ BEFORE THE READBACK, and the order is the
     whole point. `readback` folds the live heap and runs the reference driver
     over it — it FIRES RULES and writes substitutions into this runtime. Read
     `semStateId`/`semStateSignature` after it and you are measuring a state
     the film never reached. The native side computes its final signature
     before calling normal() for exactly this reason, so reading them in the
     other order here made the two sides disagree on `lowered_add_2_3` — where
     the readback resolves four residual projections — while every frame in the
     film matched. The comparator's first find was a defect in the comparator. */
  const remaining = findFloatRedexes(frt, root, PLANE_POOL_FREE).length;
  const final = semStateId(frt, root);
  const siglen = semStateSignature(frt, root).length;
  const rb = readback(frt, root);
  return {
    outcome: "film", initial, rows,
    terminal: { termination: "NORMAL_FORM", steps: rows.length, final, remaining },
    nf: rb.str, nfid: semId(rb.str), siglen,
    fire, loci,
    note: `readback interactFired=${rb.interactFired} collapseFired=${rb.collapseFired} liveCount=${rb.liveCount}`,
  };
}

/* ── the native C measurement, parsed back out of its own row format ─────── */
function measureC(term) {
  let out;
  try {
    out = execFileSync(BIN, ["--measure", "-v", term], { maxBuffer: 1 << 26 }).toString();
  } catch (e) {
    const text = (e.stdout ?? Buffer.from("")).toString();
    const m = /^REFUSED (\S+)/m.exec(text);
    if (m) return { outcome: "refused", reason: m[1] };
    return { outcome: "crash", detail: text.trim() || String(e.message ?? e) };
  }
  const rows = [], fire = new Map(), never = [], enabledBy = new Map();
  const loci = { "t:": 0, "d:": 0, "v:": 0 };
  let initial = null, terminal = null, nf = null, nfid = null, siglen = null, note = null;
  for (const line of out.split("\n")) {
    const p = line.split(" ");
    if (p[0] === "INITIAL") initial = p[1];
    else if (p[0] === "ENABLED") {
      const k = +p[1];
      if (!enabledBy.has(k)) enabledBy.set(k, []);
      enabledBy.get(k).push(`${p[2]}:${p[3]}`);
    }
    else if (p[0] === "FRAME")
      rows.push({ n: +p[1], rule: p[2], plane: p[3], locus: p[4], pre: p[5], post: p[6], enabled: +p[7] });
    else if (p[0] === "TERMINAL") terminal = { termination: p[1], steps: +p[2], final: p[3], remaining: +p[4] };
    else if (p[0] === "NF") nf = line.slice(3);
    else if (p[0] === "NFID") nfid = p[1];
    else if (p[0] === "SIGLEN") siglen = +p[1];
    else if (p[0] === "FIRE") fire.set(p[1], +p[2]);
    else if (p[0] === "NEVER") never.push(p[1]);
    else if (p[0] === "INTERACTIONS") note = line;
    else if (p[0] === "LOCUS") loci[p[1]] = +p[2];
  }
  for (const r of rows) r.enabledSet = (enabledBy.get(r.n) ?? []).join(" ");
  return { outcome: "film", initial, rows, terminal, nf, nfid, siglen, fire, never, loci, note };
}

/* ── OUTCOME CLASS: the one translation, in one place ─────────────────────
   The native emitter answers an out-of-scope fixture with a typed refusal; the
   JS relation has no such vocabulary because nothing is out of scope for it.
   This maps the JS outcome onto what the C contract says the answer should be,
   so a refusal can be checked as an AGREEMENT rather than reported as a
   difference. Everything else is compared field for field. */
const jsOutcome = (js) => ({
  "no-redex-at-source": "film-no-redex-at-source",
  "era-rule-required": "film-era-rule-not-implemented",
  "budget-exhausted": "film-budget-exhausted",
}[js.outcome] ?? null);

const eqMap = (a, b) => {
  const ks = new Set([...a.keys(), ...b.keys()]);
  for (const k of ks) if ((a.get(k) ?? 0) !== (b.get(k) ?? 0)) return false;
  return true;
};
const showMap = (m) => [...m].sort().map(([k, v]) => `${k}=${v}`).join(" ") || "—";

function compare(name, term) {
  const js = measureJS(term), c = measureC(term);
  const diffs = [];

  if (js.outcome !== "film") {
    const want = jsOutcome(js);
    if (c.outcome === "refused" && want && c.reason === want)
      return { name, term, agree: true, note: `both refuse: ${want}` };
    diffs.push(`JS outcome ${js.outcome}${js.rule ? ` (${js.rule})` : ""} vs C ${c.outcome}${c.reason ? ` ${c.reason}` : ""}`);
    return { name, term, agree: false, diffs, js, c };
  }
  if (c.outcome !== "film") {
    diffs.push(`JS produced a ${js.rows.length}-frame film; C answered ${c.outcome}${c.reason ? ` ${c.reason}` : ""}${c.detail ? ` — ${c.detail}` : ""}`);
    return { name, term, agree: false, diffs, js, c };
  }

  if (js.initial !== c.initial) diffs.push(`initial sem_state_id: JS ${js.initial.slice(0, 16)}… vs C ${String(c.initial).slice(0, 16)}…`);
  if (js.rows.length !== c.rows.length) diffs.push(`frame count: JS ${js.rows.length} vs C ${c.rows.length}`);
  const nrow = Math.max(js.rows.length, c.rows.length);
  for (let i = 0; i < nrow; i++) {
    const a = js.rows[i], b = c.rows[i];
    if (!a) { diffs.push(`frame ${i + 1}: JS has none; C ${b.rule} @ ${b.locus}`); continue; }
    if (!b) { diffs.push(`frame ${i + 1}: C has none; JS ${a.rule} @ ${a.locus}`); continue; }
    for (const f of ["rule", "plane", "locus", "pre", "post", "enabled", "enabledSet"])
      if (String(a[f]) !== String(b[f]))
        diffs.push(`frame ${i + 1} ${f}: JS ${a[f]} vs C ${b[f]}`);
  }
  for (const f of ["termination", "steps", "final", "remaining"])
    if (String(js.terminal[f]) !== String(c.terminal?.[f]))
      diffs.push(`terminal ${f}: JS ${js.terminal[f]} vs C ${c.terminal?.[f]}`);
  if (js.nf !== c.nf) diffs.push(`normal form: JS ${JSON.stringify(js.nf)} vs C ${JSON.stringify(c.nf)}`);
  if (js.nfid !== c.nfid) diffs.push(`normal_form_id: JS ${js.nfid} vs C ${c.nfid}`);
  if (js.siglen !== c.siglen) diffs.push(`signature length: JS ${js.siglen} vs C ${c.siglen}`);
  if (!eqMap(js.fire, c.fire)) diffs.push(`rule tally: JS [${showMap(js.fire)}] vs C [${showMap(c.fire)}]`);
  for (const k of ["t:", "d:", "v:"])
    if (js.loci[k] !== c.loci[k]) diffs.push(`locus family ${k}: JS ${js.loci[k]} vs C ${c.loci[k]}`);

  return { name, term, agree: diffs.length === 0, diffs, js, c };
}

/* ── the fixture set ──────────────────────────────────────────────────────
   The whole conformance corpus, so agreement is not a one-fixture coincidence;
   church_exp_2_2 by name because it is this round's subject; and the two
   fixtures the existing film gate already runs, so a regression in the
   APP-plane path shows up here too. */
const corpusPath = process.env.TRVM_VECTORS ?? join(ROOT, "..", "docs", "spec", "conformance", "vectors", "normalize.json");
const fixtures = [];
if (process.argv[2]) fixtures.push({ name: "argv", term: process.argv[2] });
else {
  if (existsSync(corpusPath))
    for (const v of JSON.parse(readFileSync(corpusPath, "utf8")).vectors)
      fixtures.push({ name: `corpus/${v.name}`, term: v.term });
  const ADD = "λm.λn.λf.λx.!&0{f0,f1}=f;((m f0) ((n f1) x))";
  const C2 = "λf.λx.!&1{a,b}=f;(a (b x))";
  const C3 = "λf.λx.!&2{a,t}=f;!&3{b,c}=t;(a (b (c x)))";
  fixtures.push({ name: "film/apply_id", term: "(λx.λt.(t x) λy.y)" });
  fixtures.push({ name: "film/lowered_add_2_3", term: `((${ADD} ${C2}) ${C3})` });
  fixtures.push({ name: "film/dup_sup_enabled", term: "!{a,b} = {λx.x,λy.y}; (a b)" });
}

if (!existsSync(BIN)) {
  console.log(`MEASURE-COMPARE: SKIP — ${BIN} not built (make gov-film builds it).`);
  console.log("  A missing binary is UNBUILT, never agreement: this exits nonzero.");
  process.exit(1);
}

let differed = 0, agreed = 0;
const interesting = [];
for (const f of fixtures) {
  const r = compare(f.name, f.term);
  if (r.agree) {
    agreed++;
    const rows = r.js?.rows?.length ?? 0;
    if (rows) {
      const dv = (r.js.loci["d:"] ?? 0) + (r.js.loci["v:"] ?? 0);
      if (dv) interesting.push(`${f.name} (${rows} frames, ${dv} dup-plane loci)`);
    }
    console.log(`AGREE   ${f.name.padEnd(28)} ${r.note ?? `${r.js.rows.length} frames · ${showMap(r.js.fire)}`}`);
  } else {
    differed++;
    console.log(`DIFFER  ${f.name.padEnd(28)} ${r.diffs.length} difference(s)`);
    for (const d of r.diffs.slice(0, 40)) console.log(`          · ${d}`);
    if (r.diffs.length > 40) console.log(`          · … ${r.diffs.length - 40} more`);
    if (r.js?.outcome === "film" && r.c?.outcome === "film") {
      console.log(`        ${"n".padStart(4)}  ${"JS rule".padEnd(10)} ${"JS locus".padEnd(22)} ${"C rule".padEnd(10)} ${"C locus".padEnd(22)} pre(JS/C)`);
      const n = Math.max(r.js.rows.length, r.c.rows.length);
      for (let i = 0; i < n; i++) {
        const a = r.js.rows[i] ?? {}, b = r.c.rows[i] ?? {};
        const same = a.rule === b.rule && a.locus === b.locus && a.pre === b.pre && a.post === b.post;
        console.log(`      ${same ? " " : "✗"} ${String(i + 1).padStart(3)}  ${String(a.rule ?? "—").padEnd(10)} ` +
          `${String(a.locus ?? "—").padEnd(22)} ${String(b.rule ?? "—").padEnd(10)} ${String(b.locus ?? "—").padEnd(22)} ` +
          `${String(a.pre ?? "—").slice(0, 8)}/${String(b.pre ?? "—").slice(0, 8)}`);
      }
    }
  }
}

console.log("═".repeat(96));
if (differed) {
  console.log(`MEASURE-COMPARE: DIFFER — ${agreed} agreed, ${differed} differed. STOP: the C relation and the`);
  console.log("  JS oracle do not measure the same thing yet. Do not write conformance assertions, and do not");
  console.log("  adjust C toward the remembered table — diagnose the divergence.");
} else {
  console.log(`MEASURE-COMPARE: AGREE — ${agreed}/${agreed} fixtures. The native C float-plane relation and the`);
  console.log("  law kernel's reference relation produce the same frames, loci, semantic ids and terminals.");
  console.log("  Dup-plane coverage among them:");
  for (const s of interesting) console.log(`    · ${s}`);
  console.log("  This is a MEASUREMENT, not a conformance claim: nothing here is committed, replayed or signed.");
}
process.exit(differed ? 1 : 0);
