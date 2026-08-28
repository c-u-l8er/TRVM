/* grid_check.mjs v2.21 — GRID-CONSISTENCY-2 (law:grid.consistency@2).
   v2.21 (round 15): the derivation-boundary source locks, and TWO reads that
   round 14 said had been root-anchored and had not been — the citation scan
   and the banned-phrase tripwire. See the notes at each site; the second
   passed vacuously rather than failing.
   v1 (round 3): grep blacklist + structural spot-checks. v2 (round 4): LAW
   REGISTRY as the citation authority — every 'law:<id>@<rev>' in every
   shipped artifact must resolve; non-canonical citations only in
   superseded/history context. v2.1 (round 5) adds the ENGINE-FREE half of
   certificate verification, because the round-5 audit passed a hollow
   zero-exhibit certificate through this very checker (it looked at three
   fields): cert_id and run_manifest_hash are RECOMPUTED, evidence aggregates
   are RECOMPUTED by arithmetic over the receipts, completeness is checked,
   and representation / plane profile / corpus id / law refs / claims /
   exhibit coverage are checked against the grid's own machine-readable
   scheduler_certificate section. The kernel's checker re-EXECUTES every
   receipt (the engine half); between the two, no certificate field is
   covered by zero re-derivations. v2.1 also makes the grid's citation scan
   STRUCTURAL (values under history/changelog key-paths are history context)
   and treats all but the highest-numbered round ledger as frozen history.
   v2.3 (round 6): VERSION LOCKSTEP (grid.version must equal the kernel
   source's KERNEL_VERSION constant, and the source header must carry it —
   the engine-free half of law:kernel.identity@1), the refinement receipt's
   engine-free verification (commitment recompute + summary arithmetic over
   per_term + law refs against the grid's refinement_receipt section), the
   semantic-film refusal vocabulary presence check, and the certificate's
   declared scheduler set against the grid's strategy_schedulers.
   v2.5 (round 7): MULTI-ARTIFACT identity — grid.version is the record's
   own lineage; artifact_versions locks each executable's declared version
   constant, parsed from source (kernel.identity@2). The WORLD layer's
   artifacts join the citation scan, and world_warrant_receipt.json gets
   the engine-free half: warrant_id and footprint_id recomputed from the
   receipt's own fields, receipt_id recomputed, law refs resolved, verdict
   witnessed.
   Run: node grid_check.mjs   (exit 0 iff consistent) */
import { readFileSync, readdirSync, existsSync, statSync, mkdtempSync, rmSync, writeFileSync,
  symlinkSync, linkSync, mkdirSync, cpSync } from "node:fs";
import { tmpdir } from "node:os";
import { createHash } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import { dirname, join, relative } from "node:path";

// ── ARTIFACT ROOT (v2.19) ─────────────────────────────────────────────────
// Ambient CWD discovery is not a detail of tidiness: in an evidence system
// "which file did I read?" is part of provenance, and a checker whose answer is
// "whatever was beside the process" cannot state it. The root is now EXPLICIT —
// anchored at this module's own location, overridable by TRVM_GOV_ROOT — and
// the verdict line reports it, so a run in the wrong tree is visible in its own
// output rather than inferred. The negative battery still works unchanged
// because it copies grid_check.mjs into each scratch case, so the module's own
// directory IS the case's directory.
const ROOT = process.env.TRVM_GOV_ROOT ?? dirname(fileURLToPath(import.meta.url));
const A = (name) => join(ROOT, name);
const fails = [];
const ok = (cond, msg) => { if (!cond) fails.push(msg); };

const g = JSON.parse(readFileSync(A("invariant-grid.json"), "utf8"));

// ── A. registry self-validation ───────────────────────────────────────────
const reg = g.law_registry;
ok(reg && Array.isArray(reg.entries) && reg.entries.length > 0, "law_registry missing or empty");
ok(reg?.grid_version === g.version,
  `registry.grid_version (${reg?.grid_version}) !== grid.version (${g.version})`);
const keyOf = (e) => e.id + "@" + e.revision;
const entries = reg?.entries ?? [];
const byKey = new Map(), byId = new Map();
for (const e of entries) {
  ok(/^[a-z0-9_.\-]+$/.test(e.id ?? ""), `registry id malformed: ${e.id}`);
  ok(Number.isInteger(e.revision) && e.revision >= 1, `revision malformed on ${e.id}`);
  ok(typeof e.canonical === "boolean", `canonical flag missing on ${keyOf(e)}`);
  ok(typeof e.statement === "string" && e.statement.length > 0, `statement missing on ${keyOf(e)}`);
  ok((g.status_vocabulary ?? []).includes(e.status),
    `status '${e.status}' of ${keyOf(e)} not in status_vocabulary`);
  ok(!byKey.has(keyOf(e)), `duplicate registry entry ${keyOf(e)}`);
  byKey.set(keyOf(e), e);
  if (!byId.has(e.id)) byId.set(e.id, []);
  byId.get(e.id).push(e);
}
for (const e of entries) for (const f of ["supersedes", "superseded_by"])
  if (e[f] != null) ok(byKey.has(e[f]), `${keyOf(e)}.${f} points at unknown entry ${e[f]}`);
for (const [id, es] of byId) {
  const mx = Math.max(...es.map((x) => x.revision));
  for (const x of es) {
    // non-max revisions are never canonical; the max revision is canonical
    // exactly when nothing (same id or another law) supersedes it
    const want = x.revision === mx && x.superseded_by == null;
    ok(x.canonical === want,
      `canonical flag of ${keyOf(x)} must be ${want} (max rev ${mx}` +
      (x.superseded_by ? `, superseded_by ${x.superseded_by}` : "") + `)`);
  }
}
for (const e of entries) if (e.supersedes) {
  const t = byKey.get(e.supersedes);
  if (t?.superseded_by != null)
    ok(t.superseded_by === keyOf(e),
      `asymmetric lineage: ${keyOf(e)} supersedes ${e.supersedes}, ` +
      `but that entry's superseded_by is ${t.superseded_by}`);
}

// ── B. citation resolution across every shipped artifact ─────────────────
// Grid: STRUCTURAL scan — a citation inside a value whose key-path contains
// history|changelog is history context (changelogs are dated narrative; the
// round-4 entries legitimately cite laws that round 5 superseded). Ledgers:
// only the highest-numbered round ledger is current narrative; older ones
// are frozen history. Everything else: line context /superseded|history/i.
const CITE = /law:([a-z0-9_.\-]+)@(\d+)/g;
let citations = 0;
const citeCheck = (file, where, text, historyCtx) => {
  for (const m of text.matchAll(CITE)) {
    citations++;
    const k = `${m[1]}@${m[2]}`, e = byKey.get(k);
    if (!e) { fails.push(`${file}:${where} cites unknown law ${k}`); continue; }
    if (!e.canonical && !historyCtx && !/superseded|history/i.test(text))
      fails.push(`${file}:${where} cites non-canonical ${k} outside superseded/history context`);
  }
};
(function scanGrid(node, path) {
  const hist = /history|changelog/i.test(path);
  if (typeof node === "string") citeCheck("invariant-grid.json", path || "(root)", node, hist);
  else if (Array.isArray(node)) node.forEach((v, i) => scanGrid(v, path + "[" + i + "]"));
  else if (node && typeof node === "object")
    for (const [k, v] of Object.entries(node)) scanGrid(v, path ? path + "." + k : k);
})(g, "");
const ledgers = readdirSync(ROOT).filter((f) => /^round-\d+-ledger\.md$/.test(f))
  .sort((a, b) => parseInt(a.match(/\d+/)[0]) - parseInt(b.match(/\d+/)[0]));
const latestLedger = ledgers[ledgers.length - 1];
const ARTIFACTS = ["refinement_receipt.json", "trvm_world.mjs", "world_warrant_receipt.json", "trvm_law_kernel.mjs", "kappa_witnesses.mjs",
  "scheduler_certificate.json", "golden_prehash_vectors.json", ...ledgers];
// v2.21: these resolved against the CWD, not against ROOT. Round 14 recorded
// that ambient discovery had been replaced across grid_check; the ROOT was
// introduced and A() was applied to most reads, but the citation scan — the
// primary evidence loop, 334 citations — was still reading whatever sat beside
// the process. It failed loudly from the wrong directory, so it was invisible
// while every invocation happened to be `cd governance && node grid_check.mjs`.
for (const f of ARTIFACTS) {
  if (!existsSync(A(f))) { fails.push(`artifact missing: ${f}`); continue; }
  const frozen = /^round-\d+-ledger\.md$/.test(f) && f !== latestLedger;
  readFileSync(A(f), "utf8").split("\n").forEach((line, i) =>
    citeCheck(f, i + 1, line, frozen));
}
ok(citations > 0, "no law citations found anywhere — the registry is load-bearing only if cited");

// ── B2. artifact coverage: nothing present may be undeclared (v2.20) ──────
// The direction that matters is not "is every declared file here" — a missing
// file already fails loudly. It is "is every file here declared", because an
// artifact nobody wired into the manifest is an artifact the negative battery
// never copies into a scratch case, and therefore never tests. That failure is
// silent by construction and the roster keeps counting.
{
  const man = existsSync(A("artifacts.json"))
    ? JSON.parse(readFileSync(A("artifacts.json"), "utf8")) : null;
  ok(!!man && man.type === "TRVM-GOV-ARTIFACTS-v1", "artifacts.json missing or not v1 (v1.13)");
  if (man) {
    // B8.3+: generated_evidence is a THIRD declared category. It exists because
    // proof_bundle.json is 1.2 MB and run_case copies every case input into a
    // fresh tree per forgery; declaring it as a case input would move half a
    // gigabyte per battery run. It is still DECLARED, so the present-but-
    // undeclared refusal keeps its meaning, and the manifest states what is
    // lost by the exemption instead of leaving the omission silent.
    // TWO USES, AND THEY ARE NOT THE SAME SET. `declared` answers "may this
    // file be here?" and generated evidence may. `tracked` answers "must this
    // file be here?" and generated evidence must NOT be required, because it is
    // written by `make gov-proof` and does not exist in a scratch case tree
    // that never ran it. Conflating them made every negative-battery case fail
    // its BASELINE on a file the battery deliberately does not copy.
    const declared = new Set([...(man.case_inputs ?? []), ...(man.tools ?? []),
                              ...(man.generated_evidence ?? [])]);
    const tracked = new Set([...(man.case_inputs ?? []), ...(man.tools ?? [])]);
    const ledgerRx = new RegExp(man.ledgers_pattern);
    const probeRx = new RegExp(man.probes_pattern);
    for (const f of tracked) ok(existsSync(A(f)), `artifacts.json declares ${f}, which is absent`);
    const present = readdirSync(ROOT).filter((f) => /\.(mjs|json|sh)$/.test(f));
    for (const f of present) {
      if (declared.has(f) || ledgerRx.test(f) || probeRx.test(f)) continue;
      fails.push(`governance artifact ${f} is present but UNDECLARED in artifacts.json — ` +
        `the negative battery copies only what is declared, so an undeclared artifact is never tested`);
    }
    // and every probe must state what it witnesses
    for (const f of present.filter((x) => probeRx.test(x)))
      ok((man.probe_roles ?? {})[f], `probe ${f} has no role declared in artifacts.json probe_roles`);
  }
}

// ── C. supplementary banned-phrase tripwire ───────────────────────────────
// (retired wordings that never name a law; the registry cannot catch these)
const BANNED = [
  "CALM property that licenses",
  "selected_carrier(before) == selected_carrier(after)",
  "uninhabitable by theorem",
  "pair to publish, verbatim",
];
const gridCanonical = (() => {
  const c = JSON.parse(JSON.stringify(g));
  for (const k of Object.keys(c)) if (/history/i.test(k)) delete c[k];
  return JSON.stringify(c);
})();
for (const b of BANNED)
  ok(!gridCanonical.includes(b), `grid canonical sections contain banned phrase: ${b}`);
// v2.21: this one was worse than CWD-relative — an absent file scanned the
// EMPTY STRING and every banned-phrase check passed vacuously. From any
// directory but governance/ the tripwire reported clean while measuring
// nothing, which is the silent-pass class this record has prosecuted since
// round 9. Absent is now a failure, and the read is anchored at ROOT.
for (const f of ["trvm_law_kernel.mjs", "kappa_witnesses.mjs"]) {
  if (!existsSync(A(f))) { ok(false, `banned-phrase scan: ${f} absent, so nothing was scanned`); continue; }
  const txt = readFileSync(A(f), "utf8");
  for (const b of BANNED) ok(!txt.includes(b), `${f} contains banned phrase: ${b}`);
}

// v1.33: NO SOURCE FILE MAY CONTAIN A LITERAL NUL BYTE.
// Twice now a separator has been written as the raw byte rather than the
// six-character escape, and both times file(1) reclassified the whole module as
// `data` and every text tool — grep included — skipped it in silence. A grep
// over that file returns nothing and reads exactly like an answer. Round 27A.1
// fixed the first occurrence and DOCUMENTED the hazard; round 27A.3's new
// grouping key reintroduced it four commits later, in the same file. A rule
// that has to be remembered is a rule that will be forgotten, so it is checked.
// The string values are unaffected: "\u0000" and a raw 0x00 are the same string
// and only one of them is visible to the instruments that audit this tree.
// P4.7.7: AND THE SCOPE OF THIS SCAN WAS A HAND-TYPED DIRECTORY LIST, SO THE
// FILE IT WAS WRITTEN FOR LEFT IT. `dirs` was `["", "bridge"]` — governance and
// its bridge — and P4.6 moved `holdout_score_core.mjs` into
// `docs/spec/proof-wire/experiment/` to put the scorer inside `experiment_digest`.
// A literal NUL was sitting in that file at line 79, in the sentinel whose own
// comment says it is "written as an ESCAPE because a literal NUL makes file(1)"
// report the module as data. The rule that was checked because it would be
// forgotten was still checked, over a set the thing it checks had walked out of.
// The spec tree is scanned now, recursively, because a directory list is the
// same species of hand-maintained scope as the phrase list this file already
// refuses to keep by hand.
{
  const SCAN = [".mjs", ".js", ".sh", ".json", ".md", ".c", ".h", ".py"];
  const dirs = ["", "bridge"];
  const deep = [join(ROOT, "..", "docs", "spec", "proof-wire")];
  let scanned = 0;
  const walkDeep = (dir) => {
    if (!existsSync(dir)) return [];
    return readdirSync(dir).sort().flatMap((f) => {
      const q = join(dir, f);
      return statSync(q).isDirectory() ? walkDeep(q) : (SCAN.some((x) => f.endsWith(x)) ? [q] : []);
    });
  };
  for (const root of deep)
    for (const abs of walkDeep(root)) {
      const buf = readFileSync(abs);
      if (buf.includes(0)) {
        const at = buf.indexOf(0);
        ok(false, `${relative(ROOT, abs)} contains a literal NUL byte at offset ${at} (line ` +
          `${buf.subarray(0, at).toString("utf8").split("\n").length}) — file(1) reports the module ` +
          `as \`data\` and grep skips it silently. Write "\\u0000", which is the same string`);
      }
      scanned++;
    }
  for (const d of dirs) {
    const dir = d ? A(d) : ROOT;
    if (!existsSync(dir)) continue;
    for (const name of readdirSync(dir)) {
      if (!SCAN.some((x) => name.endsWith(x))) continue;
      const rel = d ? d + "/" + name : name;
      const buf = readFileSync(A(rel));
      if (buf.includes(0)) {
        const at = buf.indexOf(0);
        ok(false, `${rel} contains a literal NUL byte at offset ${at} (line ` +
          `${buf.subarray(0, at).toString("utf8").split("\n").length}) — file(1) reports the module ` +
          `as \`data\` and grep skips it silently. Write "\\u0000", which is the same string`);
      }
      scanned++;
    }
  }
  ok(scanned > 0, "NUL scan found no source files, so nothing was scanned");
}

// ── D. structural checks carried from v1 ─────────────────────────────────
const LINEAGE = ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "1.0.0", "1.0.1", "1.1.0", "1.2.0", "1.3.0", "1.4.0", "1.5.0", "1.6.0", "1.7.0", "1.7.1", "1.8.0", "1.9.0", "1.10.0", "1.11.0", "1.12.0", "1.13.0", "1.14.0", "1.15.0", "1.16.0", "1.17.0", "1.18.0", "1.19.0", "1.20.0", "1.21.0", "1.22.0", "1.23.0", "1.24.0", "1.25.0", "1.26.0", "1.27.0", "1.28.0", "1.29.0", "1.30.0", "1.31.0", "1.32.0", "1.33.0", "1.34.0", "1.35.0", "1.36.0", "1.37.0", "1.38.0", "1.39.0", "1.40.0", "1.41.0", "1.42.0", "1.43.0", "1.44.0", "1.45.0", "1.46.0", "1.47.0", "1.48.0", "1.49.0", "1.50.0", "1.51.0", "1.52.0", "1.53.0", "1.54.0", "1.55.0", "1.56.0", "1.57.0", "1.58.0", "1.59.0", "1.60.0", "1.61.0", "1.62.0", "1.63.0", "1.64.0", "1.65.0", "1.66.0", "1.67.0", "1.68.0", "1.69.0"];
ok(LINEAGE[LINEAGE.length - 1] === g.version,
  `grid.version (${g.version}) is not the head of the declared lineage`);
const clKey = "changelog_from_" + LINEAGE[LINEAGE.length - 2].replaceAll(".", "_");
ok(Array.isArray(g[clKey]) && g[clKey].length > 0, `latest changelog ${clKey} missing`);
// artifact-identity MAP (engine-free half of law:kernel.identity@2): every
// executable's declared version constant, parsed from source, must equal
// the grid's artifact_versions entry; each source header carries its own
// version. grid.version is the record's lineage, not any single artifact's.
{
  const av = g.artifact_versions ?? {};
  // THREE OF SIX ENTRIES WERE UNREAD BY ANY CHECK. artifact_versions carried
  // lowering.mjs, observed_execution_host.mjs and bridge/ic32_film.c, and this
  // list named only the first three — so half the map was a hand-maintained
  // record with no instrument behind it, and a version bumped in one place and
  // not the other passed. Found at B1.2.1 by bumping lowering.mjs and watching
  // grid_check say PASS with the grid still declaring the previous version;
  // the same commit had also moved the file's HEADER to v0.5.0 while leaving
  // its LOWERING_VERSION constant at 0.4.0, which is the same defect inside one
  // file. A declared version with nothing reading it is the instrument-vacuity
  // species this file exists to catch, sitting in the checker's own map.
  //
  // ic32_film.c is C and declares its version in the JSON it emits rather than
  // as a constant, so it is matched on that string — the version a consumer
  // actually receives, which is the one worth binding.
  const declared = [
    ["trvm_law_kernel.mjs", /const KERNEL_VERSION = "([^"]+)";/],
    ["trvm_world.mjs", /const WORLD_VERSION = "([^"]+)";/],
    ["derive_protocol.mjs", /const PROTOCOL_VERSION = "([^"]+)";/],
    ["lowering.mjs", /const LOWERING_VERSION = "([^"]+)";/],
    ["observed_execution_host.mjs", /const HOST_VERSION = "([^"]+)";/],
    ["bridge/ic32_film.c", /emitter_version\\":\\"([^\\"]+)\\"/],
  ];
  // every entry in the map must be READ by this loop, not merely present
  for (const file of Object.keys(av))
    ok(declared.some(([f]) => f === file),
      `artifact_versions declares ${file} and no check reads it — a version record with no ` +
      `instrument behind it is a hand-maintained number that drifts silently`);
  for (const [file, rx] of declared) {
    ok(av[file] != null, `artifact_versions missing ${file}`);
    if (!existsSync(A(file))) { ok(false, `artifact_versions declares ${file}, which is absent`); continue; }
    const s = readFileSync(A(file), "utf8");
    const m = s.match(rx);
    ok(!!m, `${file} does not declare its version constant`);
    if (m && av[file] != null) ok(m[1] === av[file],
      `${file} declares ${m[1]} but artifact_versions says ${av[file]}`);
    if (m) ok(s.slice(0, 300).includes("v" + m[1]),
      `${file} header does not carry its own version`);
  }
}
// v1 criteria must exist at v1+ and name only resolvable battery evidence
if (g.version.startsWith("1.")) {
  ok(g.v1_criteria && g.v1_criteria.criteria && Object.keys(g.v1_criteria.criteria).length >= 9,
    "v1_criteria block missing or too thin for a v1 grid");
  ok(typeof g.v1_criteria.declared_not_met_by_design === "string",
    "v1_criteria must declare what is NOT met by design");
}
ok(g.warrant?.version === 3 && g.warrant?.read_footprint,
  "canonical warrant is not v3 read-footprint shape");
ok(!!g.warrant_history?.v2_superseded, "superseded warrant not preserved in history");
ok(!JSON.stringify(g.flagship_pair ?? {}).includes("selected_carrier"),
  "flagship still contains selected_carrier precondition");
ok(!!g.flagship_history, "superseded flagship not preserved in history");
const mids = (g.meta_laws ?? []).map((m) => m.id);
ok(mids.includes("EQUIVARIANCE") && mids.includes("ADEQUACY"),
  "Equivariance/Adequacy dual incomplete");
ok((g.meta_laws ?? []).some((m) => m.id === "PROGRESS_LIVENESS" && /LOAD-BEARING/.test(m.status ?? "")),
  "Progress not promoted");
const kernelTxt = existsSync(A("trvm_law_kernel.mjs")) ? readFileSync(A("trvm_law_kernel.mjs"), "utf8") : "";
ok(!kernelTxt.includes('.digest("hex").slice(0, 16)'),
  "kernel still truncates an evidence hash to 64 bits");
ok(!kernelTxt.includes('.digest("hex").slice(0, 24)'),
  "kernel still truncates an internal hash to 96 bits");

// ── E. flagship ↔ registry binding (upgraded from v1's prefix check) ──────
const flagshipEntries = entries.filter((e) => e.grid_law_id != null);
ok(flagshipEntries.length === 1, `expected exactly one registry entry with grid_law_id, found ${flagshipEntries.length}`);
const fe = flagshipEntries[0];
ok(fe?.canonical === true, "registry flagship entry is not canonical");
ok(g.flagship_pair?.law?.id === fe?.grid_law_id,
  `flagship_pair.law.id (${g.flagship_pair?.law?.id}) !== registry flagship grid_law_id (${fe?.grid_law_id})`);

// ── F. round-4 structural requirements ────────────────────────────────────
ok((g.status_vocabulary ?? []).includes("REGRESSION-LOCKED"),
  "status_vocabulary missing REGRESSION-LOCKED");
ok(!("film_v3" in g), "film_v3 still a top-level canonical key (should live in film_history)");
ok(!!g.film_history?.v3, "film_history.v3 missing");
ok(!!g.film_v3_1?.film_id && Array.isArray(g.film_v3_1?.frame) && Array.isArray(g.film_v3_1?.terminal),
  "film_v3_1 shape incomplete");
ok((g.film_v3_1?.replay_refusals ?? []).length === 18,
  `film_v3_1 must list all 18 replay refusals (found ${(g.film_v3_1?.replay_refusals ?? []).length})`);
ok(kernelTxt.includes("TRVM-FILM-v3.1"), "kernel does not carry the TRVM-FILM-v3.1 commitment tag");
ok(kernelTxt.includes("TRVM-SEMFILM-v1"), "kernel does not carry the TRVM-SEMFILM-v1 commitment tag");
ok((g.semantic_film?.replay_refusals ?? []).length === 19,
  `semantic_film must list all 19 replay refusals (found ${(g.semantic_film?.replay_refusals ?? []).length})`);
// law:film.terminal-witness@1, grid half: the declared terminal schema must
// carry the budget-terminal witness fields, and the kernel must carry the
// v1.1 commitment domain.
ok((g.semantic_film?.terminal_fields ?? []).some((f) => String(f).startsWith("budget")),
  "semantic_film terminal_fields must declare the budget witness");
ok((g.semantic_film?.terminal_fields ?? []).some((f) => String(f).startsWith("remaining_work")),
  "semantic_film terminal_fields must declare the remaining_work witness");
ok(kernelTxt.includes("TRVM-SEMFILM-v1.1"), "kernel does not carry the TRVM-SEMFILM-v1.1 commitment domain");
for (const r of g.semantic_film?.replay_refusals ?? [])
  ok(kernelTxt.includes(`"${r}"`), `kernel lacks semantic-film refusal "${r}"`);
for (const r of g.film_v3_1?.replay_refusals ?? [])
  ok(kernelTxt.includes(`"${r}"`), `refusal '${r}' declared in grid but absent from kernel`);
ok(!!g.planes && (g.planes.INTERACT?.rules ?? []).length === 7 && (g.planes.COLLAPSE?.rules ?? []).length === 2,
  "planes section missing or rule partition wrong (7 INTERACT / 2 COLLAPSE)");
ok(/fixpoint/i.test(g.planes?.composition ?? ""), "planes.composition must record the interleaved-fixpoint finding");
ok(!!g.scheduler_certificate, "grid scheduler_certificate section missing");
ok(!!g.refinement_receipt, "grid refinement_receipt section missing (v1)");
ok(!!g.semantic_film, "grid semantic_film section missing (v1)");
ok(g.reduction_certificate?.superseded_by === "scheduler_certificate",
  "reduction_certificate not annotated superseded_by scheduler_certificate");
ok(!!g.l_prog_history, "l_prog_history (the retraction record) missing");
ok(!!g.state_identity?.open, "state_identity open-question note missing");

// ── G. certificate v2: the ENGINE-FREE half of verification ──────────────
// Mirrors the kernel's committedView/certIdOf/manifestHashOf/aggregate — a
// drift between the two shows up as one side failing, which is the point.
const SC = g.scheduler_certificate ?? {};
if (existsSync(A("scheduler_certificate.json"))) {
  const cert = JSON.parse(readFileSync(A("scheduler_certificate.json"), "utf8"));
  ok(cert.version === 2 && cert.type === "SchedulerCertificate", "shipped certificate is not v2");
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
  const certIdOf = (c) => createHash("sha256")
    .update("TRVM-SCHEDCERT-v2|" + JSON.stringify(committedView(c))).digest("hex");
  ok(certIdOf(cert) === cert.cert_id, "certificate cert_id does not recompute (commitment broken)");
  const receipts = cert.run_manifest ?? [];
  ok(createHash("sha256").update(JSON.stringify(receipts)).digest("hex") === cert.run_manifest_hash,
    "certificate run_manifest_hash does not recompute");
  // aggregates: pure arithmetic over receipts, compared EXACTLY
  const agg = (() => {
    const sch = new Set(), tm = new Set();
    let completed = 0, nf_matched = 0, readback_pure = 0, max_steps = 0;
    for (const r of receipts) {
      sch.add(r.scheduler); tm.add(r.term_name);
      if (r.termination === "NORMAL_FORM") completed++;
      if (r.nf_matched === true) nf_matched++;
      if (r.readback && r.readback.interact === 0) readback_pure++;
      max_steps = Math.max(max_steps, r.steps);
    }
    return { schedulers: sch.size, terms: tm.size, runs: receipts.length,
      completed, nf_matched, readback_pure, max_steps };
  })();
  ok(JSON.stringify(agg) === JSON.stringify(cert.evidence),
    "certificate evidence does not equal aggregates recomputed from receipts");
  // honest-key tripwire (round-4 guard, restored in v2.1 after the round-5
  // negative battery caught its omission): the coherence figure is named for
  // what it measures — readback purity — never laundered as "ref_coherent".
  ok(Object.keys(cert.evidence ?? {}).join(",") ===
     "schedulers,terms,runs,completed,nf_matched,readback_pure,max_steps",
    "certificate evidence must use exactly the seven honest keys (readback_pure, not ref_coherent)");
  ok(!gridCanonical.includes('"ref_coherent"'),
    "grid canonical sections contain the dishonest ref_coherent evidence key");
  // completeness: nonzero, exact cross product, once each
  const pairs = receipts.map((r) => r.term_name + "|" + r.scheduler);
  const schedulers = cert.strategy?.schedulers ?? [];
  ok(receipts.length > 0 && new Set(pairs).size === pairs.length &&
     receipts.length === schedulers.length * agg.terms,
    "certificate run manifest incomplete (must be schedulers x terms, once each, nonzero)");
  ok(schedulers.length === agg.schedulers &&
     schedulers.every((sn) => receipts.some((r) => r.scheduler === sn)),
    "certificate strategy.schedulers disagrees with receipts");
  // against the grid's own machine-readable section
  ok(cert.representation === SC.representation,
    `certificate representation (${cert.representation}) != grid-declared (${SC.representation})`);
  ok(cert.corpus?.id === SC.corpus_id,
    `certificate corpus id (${cert.corpus?.id}) != grid-declared (${SC.corpus_id})`);
  const setEq = (a, b) => a.length === b.length && a.every((x) => b.includes(x));
  ok(setEq(cert.plane_profile?.INTERACT ?? [], g.planes?.INTERACT?.rules ?? []) &&
     setEq(cert.plane_profile?.COLLAPSE_GATED ?? [], g.planes?.COLLAPSE?.rules ?? []),
    "certificate plane profile != grid planes partition");
  const declSched = [...(g.scheduler_certificate?.strategy_schedulers ?? [])].sort().join(",");
  const certSched = [...(cert.strategy?.schedulers ?? [])].sort().join(",");
  ok(declSched === certSched && declSched.length > 0,
    "certificate strategy schedulers != grid strategy_schedulers declaration");
  ok(setEq(cert.law_refs ?? [], SC.law_refs_expected ?? []),
    "certificate law_refs != grid-declared expected refs");
  for (const r of cert.law_refs ?? []) {
    const m = /^law:([a-z0-9_.\-]+)@(\d+)$/.exec(r);
    const e = m && byKey.get(`${m[1]}@${m[2]}`);
    ok(!!e, `certificate law_ref does not resolve: ${r}`);
    ok(!e || e.canonical, `certificate law_ref resolves to non-canonical entry: ${r}`);
    for (const c of (SC.claim_requirements ?? {})[r] ?? [])
      ok((cert.claims ?? []).includes(c), `certificate law_ref ${r} unjustified: missing claim ${c}`);
  }
  for (const c of cert.claims ?? [])
    ok((SC.claims_vocabulary ?? []).includes(c), `certificate claim outside grid vocabulary: ${c}`);
  const ridSet = new Set(receipts.map((r) => r.film_id));
  ok(setEq(cert.exhibit_film_ids ?? [], (cert.exhibit_films ?? []).map((e) => e.film?.film_id)),
    "certificate exhibit_film_ids != exhibit films");
  for (const ex of cert.exhibit_films ?? [])
    ok(ridSet.has(ex.film?.film_id), `exhibit ${ex.name} not tied into the run manifest`);
  for (const t of SC.exhibit_terms ?? [])
    ok((cert.exhibit_films ?? []).some((e) => e.name === t), `grid-required exhibit missing: ${t}`);
  ok(cert.informational?.note != null, "informational block missing its non-authoritative declaration");
}

// ── H. refinement receipt: the ENGINE-FREE half (round 6) ─────────────────
// The kernel battery re-derives the runs; this half recomputes the
// COMMITMENT and the SUMMARY ARITHMETIC from per_term, and checks the
// receipt's declarations against the grid's refinement_receipt section —
// so an inflated summary or a swapped law ref dies with no engine in sight.
if (existsSync(A("refinement_receipt.json"))) {
  const rr = JSON.parse(readFileSync(A("refinement_receipt.json"), "utf8"));
  const RS = g.refinement_receipt ?? {};
  ok(rr.type === "RefinementReceipt" && rr.version === 1, "refinement receipt is not v1");
  ok(rr.relation === RS.relation, "refinement receipt relation != grid declaration");
  ok(JSON.stringify(rr.law_refs) === JSON.stringify(RS.law_refs_expected),
    "refinement receipt law_refs != grid refinement_receipt.law_refs_expected");
  const rid = createHash("sha256").update("TRVM-REFINE-v1|" + JSON.stringify(rr.per_term) + "|" + JSON.stringify(rr.summary)).digest("hex");
  ok(rid === rr.receipt_id, "refinement receipt_id does not recompute from per_term+summary");
  const pt = rr.per_term ?? [];
  ok(pt.length === rr.terms, "refinement receipt terms count != per_term length");
  const cnt = (f) => pt.filter(f).length;
  const S = rr.summary ?? {};
  ok(S.sem_chains_equal === cnt((t) => t.sem_chain_equal === true),
    "summary.sem_chains_equal does not recompute from per_term");
  ok(S.sem_films_replayed_on_B === cnt((t) => t.sem_film_replay_on_B === "ok"),
    "summary.sem_films_replayed_on_B does not recompute from per_term");
  ok(S.exec_films_B_refused_by_A_replay === cnt((t) => String(t.exec_film_B_replay).startsWith("refused")),
    "summary.exec_films_B_refused does not recompute from per_term");
  ok(S.exec_films_identical_across_allocators === cnt((t) => t.exec_films_equal === true),
    "summary.exec_films_identical does not recompute from per_term");
  ok(S.exec_films_B_refused_by_A_replay + S.exec_films_identical_across_allocators === rr.terms,
    "refused + identical must partition the terms");
  ok(new Set(pt.map((t) => t.name)).size === pt.length, "refinement receipt has duplicate terms");
  for (const t of pt) ok(t.sem_film_id && t.exec_film_id_A && t.exec_film_id_B && t.nf_id,
    `refinement per-term entry ${t.name} missing an id field`);
} else ok(false, "refinement_receipt.json missing (v1 requires the bridge receipt)");

// ── H2. golden pre-hash vectors: the ENGINE-FREE half (round 10) ──────────
// The kernel row L-BYTES-1 proves the preimage identity by running; this half
// proves the SHIPPED FILE by arithmetic. Three independent bindings, none of
// which needs a term rewritten: re-hash every signature against its own id;
// match every normal-form nf_id against the refinement receipt (so the vectors
// cannot quietly describe a corpus the shipped receipts never ran); and re-hash
// the compaction row's reconstructed pre-compaction string against the
// compacted signature the oracle emitted. A forged byte anywhere fails one of
// the three, and each failure names which.
if (existsSync(A("golden_prehash_vectors.json"))) {
  const pv = JSON.parse(readFileSync(A("golden_prehash_vectors.json"), "utf8"));
  const PS = g.prehash_vectors ?? {};
  ok(!!g.prehash_vectors, "grid prehash_vectors section missing (v1.8)");
  ok(pv.type === PS.type_expected && pv.version === PS.version_expected,
    "pre-hash vectors are not the type/version the grid declares");
  ok(JSON.stringify(pv.law_refs) === JSON.stringify(PS.law_refs_expected),
    "pre-hash vectors law_refs != grid prehash_vectors.law_refs_expected");
  ok(pv.kernel_version === (g.artifact_versions ?? {})["trvm_law_kernel.mjs"],
    `pre-hash vectors declare kernel ${pv.kernel_version} but artifact_versions says ${(g.artifact_versions ?? {})["trvm_law_kernel.mjs"]}`);
  const pt = pv.per_term ?? [];
  ok(pt.length === PS.terms_expected, `pre-hash vectors carry ${pt.length} terms, grid declares ${PS.terms_expected}`);
  ok(new Set(pt.map((t) => t.name)).size === pt.length, "pre-hash vectors have duplicate terms");
  const vid = createHash("sha256").update("TRVM-PREHASH-VECTORS-v1|" + JSON.stringify(pv.per_term)
    + "|" + JSON.stringify(pv.compaction) + "|" + JSON.stringify(pv.corpus)).digest("hex");
  ok(vid === pv.vectors_id, "pre-hash vectors_id does not recompute from per_term+compaction+corpus");
  // binding 1 — every signature is its id's actual preimage
  const H = (s) => createHash("sha256").update(s).digest("hex");
  for (const t of pt) {
    for (const [stage, st] of [["initial", t.initial], ["normal_form", t.normal_form]]) {
      ok(typeof st?.sem_signature === "string" && typeof st?.sem_state_id === "string",
        `pre-hash vector ${t.name}/${stage} missing signature or id`);
      if (st?.sem_signature != null) ok(H(st.sem_signature) === st.sem_state_id,
        `pre-hash vector ${t.name}/${stage}: signature does not hash to its sem_state_id`);
      // §5 compaction is structural, not optional: over-threshold must be compacted
      if (typeof st?.sem_signature === "string") {
        const c = st.sem_signature.startsWith("#");
        ok(c ? st.sem_signature.length === PS.compacted_width
             : st.sem_signature.length <= PS.compaction_threshold,
          `pre-hash vector ${t.name}/${stage}: signature violates the §5 compaction rule`);
      }
    }
  }
  // binding 2 — the normal forms are the ones the shipped receipt committed
  if (existsSync(A("refinement_receipt.json"))) {
    const rr = JSON.parse(readFileSync(A("refinement_receipt.json"), "utf8"));
    ok(pv.binds?.refinement_receipt_id === rr.receipt_id,
      "pre-hash vectors cite a different refinement receipt than the one shipped");
    const byName = new Map((rr.per_term ?? []).map((r) => [r.name, r]));
    for (const t of pt) {
      const r = byName.get(t.name);
      ok(!!r, `pre-hash vector ${t.name} has no refinement receipt row to anchor to`);
      if (r) ok(r.nf_id === t.normal_form?.nf_id,
        `pre-hash vector ${t.name}: nf_id is not anchored to the refinement receipt`);
    }
  }
  // binding 3 — the compaction boundary states what was compacted, provably
  const cp = pv.compaction ?? {};
  ok(cp.last_uncompacted?.compacted === false && cp.first_compacted?.compacted === true,
    "pre-hash compaction rows are not a boundary (uncompacted then compacted)");
  ok((cp.last_uncompacted?.length ?? 0) <= PS.compaction_threshold
    && (cp.first_compacted?.length ?? 0) === PS.compacted_width,
    "pre-hash compaction boundary widths disagree with the grid's declared threshold");
  const pre = cp.first_compacted_precompaction;
  ok(!!pre?.signature, "pre-hash compaction row does not state what was compacted");
  if (pre?.signature) {
    ok(pre.length > PS.compaction_threshold,
      "pre-hash compaction: the reconstructed pre-compaction string does not exceed the threshold");
    ok("#" + H(pre.signature) === cp.first_compacted?.sem_signature,
      "pre-hash compaction: the reconstructed pre-compaction string does not hash to the emitted compacted signature");
  }
} else ok(false, "golden_prehash_vectors.json missing (v1.8 ships the pre-hash byte vectors)");

// ── I. world warrant receipt: the ENGINE-FREE half (round 7) ──────────────
ok(!!g.world, "grid world section missing (v1.1)");
ok(!!g.warrant?.executable, "grid warrant.executable subsection missing (v1.1)");
ok((g.warrant?.executable?.replay_refusals ?? []).length === 10,
  `warrant.executable must list all 10 replay refusals (found ${(g.warrant?.executable?.replay_refusals ?? []).length})`);
ok(!!g.warrant?.executable?.support_discipline, "grid missing warrant.executable.support_discipline (v1.4)");
ok(!!g.warrant?.executable?.composition && !!g.sigma_profile,
  "grid missing warrant.executable.composition or sigma_profile (v1.2)");
// write-mediation (v1.3): the grid must declare the canonical domain and
// tombstones, and the world artifact must carry the refusal + value domain
ok(typeof g.world?.canonical_value_domain === "string" && typeof g.world?.deletions === "string",
  "grid world section missing canonical_value_domain or deletions (v1.3)");
{
  const wsrc2 = readFileSync(A("trvm_world.mjs"), "utf8");
  ok(wsrc2.includes("world-value-not-canonical") && wsrc2.includes("TRVM-VALUE-v1"),
    "trvm_world.mjs missing the canonical-domain refusal or value-hash domain");
  ok(wsrc2.includes("deleted: true"), "trvm_world.mjs missing tombstoned deletion");
}
{
  const wsrc = readFileSync(A("trvm_world.mjs"), "utf8");
  for (const r of g.warrant?.executable?.replay_refusals ?? [])
    ok(wsrc.includes(`"${r}"`), `trvm_world.mjs lacks warrant refusal "${r}"`);
  for (const v of g.warrant?.executable?.freshness_verdicts ?? [])
    ok(wsrc.includes(`"${v}"`), `trvm_world.mjs lacks freshness verdict "${v}"`);
  ok(wsrc.includes("TRVM-WARRANT-v3") && wsrc.includes("TRVM-FOOTPRINT-v1") && wsrc.includes("TRVM-SCOPE-v1"),
    "trvm_world.mjs missing a commitment domain tag");
}
if (existsSync(A("world_warrant_receipt.json"))) {
  const wr = JSON.parse(readFileSync(A("world_warrant_receipt.json"), "utf8"));
  ok(wr.type === "WorldWarrantReceipt" && wr.version === 3, "world receipt is not v3");
  ok(!!wr.world_spec && Array.isArray(wr.world_spec.nodes) && Array.isArray(wr.world_spec.edges) && typeof wr.world_spec.seed === "string",
    "world receipt missing committed world_spec (the engine half's rebuild input)");
  // support canonical-form (engine-free-possible): sorted + deduplicated,
  // for BOTH warrants; support truth itself is the engine half
  for (const [tag, ww] of [["ground", wr.warrant], ["composite", wr.composite?.warrant]]) {
    const s = ww?.support ?? [];
    ok(JSON.stringify(s) === JSON.stringify([...new Set(s)].sort()),
      `${tag} warrant support is not canonical (sorted, deduplicated)`);
  }
  const w = wr.warrant ?? {};
  // mirrors of the warrant commitment (engine-free recompute)
  const wCommitted = (x) => [
    ["measure", x.measure], ["predicate", x.predicate], ["value", x.value],
    ["witness", x.witness], ["support", [...(x.support ?? [])].sort()],
    ["read_footprint", { exact: [...(x.read_footprint?.exact ?? [])].sort(),
                         predicates: [...(x.read_footprint?.predicates ?? [])].sort() }],
    ["derivation_id", x.derivation_id], ["at_vclock", x.at_vclock],
  ];
  const wid = createHash("sha256").update("TRVM-WARRANT-v3|" + JSON.stringify(wCommitted(w))).digest("hex");
  ok(wid === w.warrant_id, "warrant_id does not recompute from committed fields");
  const fid = createHash("sha256").update("TRVM-FOOTPRINT-v1|" + JSON.stringify([...(w.read_footprint?.exact ?? [])].sort()) + "|" + JSON.stringify([...(w.read_footprint?.predicates ?? [])].sort())).digest("hex");
  ok(fid === wr.footprint_id, "footprint_id does not recompute from the warrant's footprint");
  const rid = createHash("sha256").update("TRVM-WORLDRECEIPT-v3|" + JSON.stringify(wr.world_spec) + "|" + JSON.stringify(wr.warrant) + "|" + wr.footprint_id
    + "|" + JSON.stringify(wr.composite?.warrant) + "|" + wr.composite?.footprint_id).digest("hex");
  ok(rid === wr.receipt_id, "world receipt_id does not recompute");
  // composite: warrant_id + footprint_id recompute, and the PAIRING RULE —
  // every publication read is paired with its freshness scope
  {
    const c2 = wr.composite?.warrant ?? {};
    const cwid = createHash("sha256").update("TRVM-WARRANT-v3|" + JSON.stringify(wCommitted(c2))).digest("hex");
    ok(cwid === c2.warrant_id, "composite warrant_id does not recompute");
    const cfid = createHash("sha256").update("TRVM-FOOTPRINT-v1|" + JSON.stringify([...(c2.read_footprint?.exact ?? [])].sort()) + "|" + JSON.stringify([...(c2.read_footprint?.predicates ?? [])].sort())).digest("hex");
    ok(cfid === wr.composite?.footprint_id, "composite footprint_id does not recompute");
    const scopes = new Set((c2.read_footprint?.predicates ?? []).map(([q]) => q));
    for (const [n] of c2.read_footprint?.exact ?? []) if (n.startsWith("warrant:"))
      ok(scopes.has("warrant-fresh:" + n.slice(8)),
        `composite reads ${n} without its paired warrant-fresh scope (staleness laundering)`);
    ok((c2.read_footprint?.exact ?? []).some(([n]) => n.startsWith("warrant:")),
      "shipped composite cites no publication — pairing rule untestable");
    ok(wr.composite_freshness_at_emit?.verdict === "fresh",
      "composite must be emitted fresh, with a verdict witness");
  }
  for (const lr of wr.law_refs ?? []) {
    const m = lr.match(/^law:([a-z0-9_.\-]+)@(\d+)$/);
    const e = m && byKey.get(m[1] + "@" + m[2]);
    ok(!!e && e.canonical === true, `world receipt cites unknown or non-canonical ${lr}`);
  }
  ok(wr.freshness_at_emit?.verdict === "fresh" && wr.freshness_at_emit?.witness != null,
    "world receipt must be emitted fresh, with a verdict witness");
  ok((w.support ?? []).every((s) => (w.read_footprint?.exact ?? []).some(([n]) => n === s)),
    "world receipt warrant: support is not a subset of the exact footprint");
} else ok(false, "world_warrant_receipt.json missing (v1.1 requires the world receipt)");

// ── J. maintenance receipt: reconstruction arithmetic (round 9) ───────────
ok(!!g.maintenance, "grid maintenance section missing (v1.5)");
ok(!!g.maintenance?.confinement, "grid maintenance.confinement missing (v1.6)");
{
  const wsrc3 = readFileSync(A("trvm_world.mjs"), "utf8");
  for (const s of ["world-write-during-maintenance", "world-lock-capability-refused", "world-already-locked"])
    ok(wsrc3.includes(s), `trvm_world.mjs missing confinement refusal "${s}"`);
  // key confinement (v1.7): private state, crypto key, frozen surfaces
  for (const s of ["#lockKey", "randomBytes(32)", "Object.freeze(World.prototype)", "Object.freeze(this)"])
    ok(wsrc3.includes(s), `trvm_world.mjs missing key-confinement construct "${s}"`);
  ok(!!g.maintenance?.confinement?.key_confinement, "grid maintenance.confinement.key_confinement missing (v1.7)");
  // coordinator confinement (v1.9): the object holding the lock is a surface too
  for (const s of ["Object.freeze(Maintainer.prototype)", "#inPass", "maintainer-reentrancy-refused"])
    ok(wsrc3.includes(s), `trvm_world.mjs missing coordinator-confinement construct "${s}"`);
  ok(!!g.maintenance?.confinement?.coordinator_confinement,
    "grid maintenance.confinement.coordinator_confinement missing (v1.9)");
  // write mediation (v1.10): the reachable authority graph, not just the object
  for (const s of ["class GuardedStore", "const RAW = new WeakMap()", "ownSpec", "coordinator_diverged"])
    ok(wsrc3.includes(s), `trvm_world.mjs missing write-mediation construct "${s}"`);
  ok(!!g.maintenance?.confinement?.write_mediation,
    "grid maintenance.confinement.write_mediation missing (v1.10)");
  // transitive ownership + the declared realm limit (v1.11)
  for (const s of ["function ownCanonical", "SPEC_FIELDS", "spec-field-unknown", "deepFreeze"])
    ok(wsrc3.includes(s), `trvm_world.mjs missing transitive-ownership construct "${s}"`);
  ok(wsrc3.includes("-not-canonical: "),
    'trvm_world.mjs missing total-ownership construct "-not-canonical: "');
  ok(!wsrc3.includes("catch { return v; }"),
    "trvm_world.mjs still contains the fail-open ownership path `catch { return v; }`");
  // the declared boundary failure must stay declared. If someone closes it the
  // registry entry has to be revised deliberately — it may not quietly become
  // green, and it may not quietly disappear either.
  {
    const e = (g.law_registry?.entries ?? []).find((x) => x.id === "derivation.environment-confinement");
    ok(!!e, "law derivation.environment-confinement@1 missing — the closure-authority boundary must stay on the record");
    ok(e && e.status === "FALSIFIED",
      `derivation.environment-confinement@1 is ${e && e.status}, not FALSIFIED — same-realm arbitrary closures are not confined, and the record may not say otherwise without a deliberate revision`);
    ok(!!g.realm_roadmap && Array.isArray(g.realm_roadmap.order),
      "grid realm_roadmap missing (v1.13) — the replacement path must be declared alongside the falsified law");
  }
  ok(!!g.artifact_roots, "grid artifact_roots missing (v1.14)");
  {
    const man2 = existsSync(A("artifacts.json")) ? JSON.parse(readFileSync(A("artifacts.json"), "utf8")) : {};
    ok(!!man2.derivation_boundary && !!man2.derivation_boundary.not_claimed,
      "artifacts.json derivation_boundary missing, or missing its not_claimed scope note (v1.15) — " +
      "the serialized boundary closes OBJECT confinement only, and the record must keep saying so");
    ok(!!man2.derivation_boundary?.two_evidence_objects && !!man2.derivation_boundary?.granting_model,
      "artifacts.json derivation_boundary missing two_evidence_objects or granting_model (v1.16) — " +
      "the grant/footprint distinction and the snapshot-vs-RPC decision are what round 15 corrected");
  }
  // ── the serialized derivation boundary at v0.2.0 (v1.16) ────────────────
  // Both v0.1.0 defects were reachable through ONE LINE of the worker each, and
  // both are the kind that reads as harmless: a convenient place to put the read
  // table, and a field passed through from the request. Locked at the source.
  {
    const dsrc = existsSync(A("derive_protocol.mjs")) ? readFileSync(A("derive_protocol.mjs"), "utf8") : "";
    const wsrcD = existsSync(A("derive_worker.mjs")) ? readFileSync(A("derive_worker.mjs"), "utf8") : "";
    ok(dsrc.length > 0 && wsrcD.length > 0, "derive_protocol.mjs or derive_worker.mjs absent (v1.16)");
    // comments stripped first: these files DOCUMENT the defect they must not
    // contain, and a scan that cannot tell the code from the account of the code
    // fires on its own record. Scoped to this check rather than made general —
    // a naive strip is wrong on a string carrying "//", and neither file has one.
    const codeOnly = (s) => s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/[^\n]*/g, "");
    ok(!/canonical_inputs\.__reads|canonical_inputs\["__reads"\]/.test(codeOnly(dsrc) + codeOnly(wsrcD)),
      "the derivation boundary sources the read table from canonical_inputs again (W-1) — the language " +
      "has {op:'input', name:…}, so anything reachable as an input is reachable with NO tracked read, " +
      "which is what made the v0.1.0 read footprint bypassable");
    ok(wsrcD.includes("evaluate(ast, req.read_grants, req.canonical_inputs)"),
      "derive_worker.mjs does not evaluate against req.read_grants — reads must come from the authority's " +
      "grant snapshot and from nowhere else");
    ok(wsrcD.includes("implementation_id: JS_IMPLEMENTATION_ID") && !/implementation_id:\s*req\./.test(wsrcD),
      "derive_worker.mjs must ASSERT its own implementation_id and must not echo the request's (W-2) — " +
      "a field the caller sets and no executor checks is decoration, not provenance");
    for (const s of ["export function grantId", "export function footprintWithinGrant",
      "export const SEMANTIC_RESULT_FIELDS", "footprint-ungranted-read", "request-grant-id-mismatch",
      "implementation-mismatch: want"])
      ok(dsrc.includes(s), `derive_protocol.mjs missing v0.2.0 construct "${s}"`);
    ok(/SEMANTIC_RESULT_FIELDS = \["request_id", "program_sem_id", "grant_id", "semantic_result"\]/.test(dsrc) &&
       /EXECUTION_ENVELOPE = \["implementation_id", "read_trace"\]/.test(dsrc),
      "derive_protocol.mjs must keep implementation_id and read_trace in an execution_evidence envelope " +
      "OUTSIDE the semantic projection — the first would make cross-implementation validation fail by " +
      "construction; the second would make access ORDER a semantic identity, so two correct " +
      "implementations visiting {a,b} in different orders would diverge over a field neither considers " +
      "semantic");
    // ── v1.20: outside the projection is not the same as unchecked ──────
    ok(dsrc.includes("export function validateTraceConformance") &&
       /trace-nonconforming/.test(dsrc),
      "derive_protocol.mjs missing validateTraceConformance — v0.5.0 excluded read_trace from the " +
      "semantic projection and then checked NOTHING about it, so a reversed trace with an untouched " +
      "footprint and value validated and was accepted (probe_traceforge_v06_repro.mjs T-1)");
    ok(/semantic_agreement: true, trace_conforms: false/.test(dsrc),
      "validateForeignResult must report semantic agreement and trace conformance SEPARATELY — " +
      "'same meaning, different strategy' and 'wrong answer' are different diagnoses");
    {
      const ee = entries.find((x) => x.id === "derivation.execution-evidence");
      ok(!!ee && ee.canonical === true && ee.status === "PROPERTY-TESTED",
        "law derivation.execution-evidence@1 missing, non-canonical, or not PROPERTY-TESTED");
      ok(!!ee && /NON-SEMANTIC DOES NOT MEAN UNVERIFIED/.test(ee.statement ?? ""),
        "derivation.execution-evidence@1 no longer states that non-semantic does not mean unverified — " +
        "that sentence is the whole round");
      const man5 = existsSync(A("artifacts.json")) ? JSON.parse(readFileSync(A("artifacts.json"), "utf8")) : {};
      ok(!!man5.derivation_boundary?.two_envelopes,
        "artifacts.json derivation_boundary missing two_envelopes (v1.20)");
    }
    // ── v1.17: the frozen core ───────────────────────────────────────────
    for (const s2 of ["export const CORE_SPEC", "export const CORE_SEM_ID", "export function validateProgram"])
      ok(dsrc.includes(s2), `derive_protocol.mjs missing v0.4.0 construct "${s2}"`);
    ok(/H\("TRVM-DERIVE-CORE-SPEC-v1\|" \+ canonicalBytes\(CORE_SPEC\)\)/.test(dsrc),
      "CORE_SEM_ID must be H(canonical CORE_SPEC) — a bare label is the caller-selected identity the " +
      "primitive ruling already refuses for componentReachability");
    ok(/H\("TRVM-PROGRAM-v2\|" \+ CORE_SEM_ID \+ "\|" \+ canonicalBytes\(ast\)\)/.test(dsrc),
      "program_sem_id must commit CORE_SEM_ID — without it the id binds SYNTAX while the record claims " +
      "it binds semantics, and four behaviours can differ behind one id (probe_coresem_v03_repro.mjs)");
    ok(/export function programSemId[\s\S]{0,220}validateProgram\(ast\)/.test(dsrc),
      "programSemId must validate the grammar BEFORE hashing — v0.2.0 issued an id to " +
      '{op:"exec", cmd:"rm -rf /"}, which failed only later at evaluation');
    ok(dsrc.includes('throw new Error("program-type: " + op + " of non-number")') &&
       dsrc.includes('throw new Error("program-arith-non-finite: " + op)'),
      "arithmetic must refuse non-number operands and non-finite results on add/sub/mul alike");
    ok(!!g.derivation_language?.frozen,
      "grid derivation_language.frozen missing (v1.17) — the core is frozen and the record must say so");
    {
      const cs = entries.find((x) => x.id === "derivation.core-semantics");
      ok(!!cs && cs.canonical === true && cs.status === "REGRESSION-LOCKED",
        "law derivation.core-semantics@1 missing, non-canonical, or not REGRESSION-LOCKED");
      ok(!!cs && /DEPENDENCY SET/.test(cs.statement ?? "") && /NOT semantic identity/.test(cs.statement ?? ""),
        "derivation.core-semantics@1 no longer states the footprint is a dependency SET whose order is " +
        "not semantic identity — declaring the order semantic makes two correct implementations diverge");
    }
    // ── v1.18: the derivation authority ─────────────────────────────────
    {
      // Comment-stripped, for assertions about what the CODE does. The header
      // of derive_protocol.mjs names registerExecutor in its own history, and
      // a check that cannot tell a mention from a declaration would force the
      // record to stop naming what it deleted.
      const dnoc = dsrc.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
      // …and the same argument one step further. v1.30 added SUPPLIER_LADDER, a
      // machine-readable record of the ladder, and a record that names the
      // deleted registerExecutor as rung @2 is a MENTION in a string literal,
      // not a declaration. The comment above already made this distinction for
      // comments; a check that cannot make it for data would force the record
      // to stop naming what it deleted, which is the same defect one quote
      // character to the right. Absence checks run against this.
      const dnostr = dnoc.replace(/`(?:[^`\\]|\\.)*`/g, "``")
        .replace(/"(?:[^"\\]|\\.)*"/g, '""').replace(/'(?:[^'\\]|\\.)*'/g, "''");
      for (const s2 of ["export function validateFootprintFresh", "export function requestSemId",
        "export class DerivationAuthority", "export function checkIntent"])
        ok(dsrc.includes(s2), `derive_protocol.mjs missing v0.5.0 construct "${s2}"`);
      ok(/this\.#issued\.set\(request_id, Object\.freeze\(\{ request_sem_id: requestSemId\(req\), request: req \}\)\)/.test(dsrc),
        "issuance must bind request_sem_id, not grant_id — binding the grant answers 'was this issued?' " +
        "about a GRANT while the thing being accepted is a REQUEST, and an input swap under an " +
        "untouched request_id passes (probe_issuebind_v05_repro.mjs I-1). AND IT MUST KEEP THE REQUEST " +
        "ITSELF, not only the hash: a table holding hashes can answer 'were these bytes issued?' and " +
        "cannot answer 'what did I issue?', so every method needing the second question re-read the " +
        "caller's object and P-7 followed (probe_reread_v13_repro.mjs)");
      ok(/accept\(req, res\) \{/.test(dsrc) && !/export function acceptForeignResult/.test(dsrc),
        "acceptance must be a METHOD on the authority taking EXACTLY (req, res). A free function " +
        "taking `issuer` and `liveReader` lets the caller supply both proofs of its own authority " +
        "(I-3); v0.7.0's fourth `executor` parameter was the same defect one level up (P-2b); and " +
        "v0.9.0's FIRST parameter was a `registry` — the mapping from semantic identity to semantic " +
        "program, supplied by the claimant (P-4, probe_semoracle_v10_repro.mjs)");
      // ── v1.26: acceptance takes no semantic oracle either ─────────────
      ok(/constructor\(reader, programImage = \[\], executorCatalog = null\)/.test(dnoc) &&
         /for \(const ast of programImage\) this\.#registry\.bind\(ast\)/.test(dnoc),
        "the authority must BUILD its registry at construction from canonical program DATA. Accepting " +
        "a ready-made ProgramRegistry satisfies any type check and leaves ownership exactly where P-4 " +
        "found it — a Proxy, or a real registry the caller populated differently, both pass instanceof");
      // ── v1.28: an instanceof guard is satisfied by a subclass ─────────
      ok(/new ObservedExecutionHost\(executorCatalog\)/.test(dnoc) &&
         !/instanceof ObservedExecutionHost/.test(dnoc),
        "the authority must BUILD its execution host from CATALOG DATA, not accept one. v0.10.0 " +
        "guarded with `host instanceof ObservedExecutionHost`, which a two-method subclass satisfies " +
        "while overriding run() and observationOf() — nothing executes and provenance still reads " +
        "'observed' (P-5, probe_hostown_v11_repro.mjs)");
      ok(!/getPrototypeOf\(\s*host/.test(dnoc),
        "and NOT with a tighter type check. Object.getPrototypeOf(host) === ObservedExecutionHost." +
        "prototype excludes the subclass and admits a Proxy; it asks what the object IS DESCENDED " +
        "FROM when the question is WHO BUILT IT");
      {
        const filmSrc2 = existsSync(A("bridge/film_check.mjs"))
          ? readFileSync(A("bridge/film_check.mjs"), "utf8") : "";
        ok(/constructor\(executorCatalog\)/.test(filmSrc2) &&
           /this\.#host = new ObservedExecutionHost\(executorCatalog\)/.test(filmSrc2),
          "FilmAuthority must build its host from catalog data too — P-5 is a property of the " +
          "PARAMETER, so it reappears in every authority that has one");
        const ip6 = entries.find((x) => x.id === "derivation.host-ownership" && x.revision === 1);
        ok(!!ip6 && ip6.canonical === true && ip6.status === "PROPERTY-TESTED",
          "law derivation.host-ownership@1 missing, non-canonical, or not PROPERTY-TESTED (v1.28)");
        ok(!!ip6 && /WHO BUILT IT/.test(ip6.statement ?? ""),
          "derivation.host-ownership@1 must say that the question is who built the object rather than " +
          "what it descends from — a law reading 'check the type harder' invites the wrong repair");
      }
      // ── v1.28: the record must not contradict the registry ────────────
      ok(!/^DECLARED, not built/.test(g.lowering_spike?.status ?? ""),
        "grid lowering_spike.status still says the spike is not built while the three lowering laws " +
        "above it are PROPERTY-TESTED. A machine-readable state contradicting the registry in the same " +
        "file is the round-21 prose-versus-record class, and it survived the round that built it");
      ok((g.lowering_spike?.execution_grade ?? "").includes("OBSERVED") &&
         (g.lowering_spike?.film_grade ?? "").includes("OPEN"),
        "grid lowering_spike must carry the two execution grades separately — an execution the host " +
        "observed and one the kernel replayed are different claims");
      ok(/#registry = new ProgramRegistry\(\)/.test(dnoc) &&
         /validateForeignResultOwned\(this\.#registry, issued, ownRes\)/.test(dnoc),
        "acceptance must re-derive through the authority's OWN registry. Re-derivation was never the " +
        "defect: it re-derived against the program the CLAIMANT nominated and agreed with itself. " +
        "AND IT MUST RE-DERIVE OVER OWNED OPERANDS — `issued` is the authority's copy of what it " +
        "issued and `ownRes` is the one snapshot of the result; passing the live (req, res) is P-7, " +
        "where re-derivation agreed perfectly about bytes that arrived after authentication");
      ok(/async execute\(req\) \{/.test(dnoc) &&
         /init: \{ programs: this\.#registry\.image\(\) \}/.test(dnoc),
        "execute must take EXACTLY (req), and the far side's program image must be the AUTHORITY's " +
        "registry — v0.9.0 let the caller pass the registry that became the worker's whole world");
      {
        const ip5 = entries.find((x) => x.id === "derivation.acceptance-authority" && x.revision === 1);
        ok(!!ip5 && ip5.canonical === true && ip5.status === "PROPERTY-TESTED",
          "law derivation.acceptance-authority@1 missing, non-canonical, or not PROPERTY-TESTED (v1.26)");
        ok(!!ip5 && /PROGRAM RESOLVER SUPPLIED BY THE CLAIMANT/.test(ip5.statement ?? ""),
          "derivation.acceptance-authority@1 no longer states that an authority cannot validate a " +
          "semantic claim using a program resolver supplied by the claimant — that sentence is the round");
        ok(!!ip5 && /instanceof/.test(ip5.statement ?? ""),
          "derivation.acceptance-authority@1 must say why a type check does not close it. The repair " +
          "is OWNERSHIP, and a law that reads as 'check the type' invites exactly the wrong fix");
        ok(!!ip5 && /INTENT/.test(ip5.statement ?? "") && /RESULT/.test(ip5.statement ?? ""),
          "derivation.acceptance-authority@1 must name what a caller may still supply — an intent and " +
          "a result to validate — because the supplier ladder is only closed if the list is finite");
      }
      ok(!/committable/.test(dsrc.replace(/\/\*[\s\S]*?\*\//g, "")),
        "acceptance must not return `committable` — one call cannot establish committability, because " +
        "the World can move between it returning and the caller applying");
      ok(/AUTHORIZE_OPTIONS = \["expected_implementation_id"\]/.test(dsrc) &&
         /authorize-options-unknown/.test(dsrc),
        "authorize() must whitelist its options — the draft spread `...over` after every authority-decided " +
        "field, so a caller could write authority content onto an authority-ISSUED request (I-2)");
      for (const [id, want] of [["derivation.footprint-freshness", "PROPERTY-TESTED"],
        ["derivation.grant-issuance", "PROPERTY-TESTED"]]) {
        const e = entries.find((x) => x.id === id);
        ok(!!e && e.canonical === true && e.status === want,
          `law ${id}@1 missing, non-canonical, or not ${want}`);
      }
      const fr = entries.find((x) => x.id === "derivation.footprint-freshness");
      ok(!!fr && /never on a global vclock/.test(fr.statement ?? ""),
        "derivation.footprint-freshness@1 no longer says freshness keys on the footprint and never on " +
        "a global vclock — a vclock rule invalidates every derivation on every unrelated write");
      ok(!!fr && /DOES NOT ESTABLISH COMMITTABILITY/.test(fr.statement ?? ""),
        "derivation.footprint-freshness@1 no longer states that acceptance does not establish " +
        "committability — a freshness check that returns before the commit is a TOCTOU window");
      const gi = entries.find((x) => x.id === "derivation.grant-issuance");
      ok(!!gi && /THE WHOLE REQUEST/.test(gi.statement ?? "") && /takes no proof from/.test(gi.statement ?? ""),
        "derivation.grant-issuance@1 no longer states that issuance binds the whole request and that " +
        "acceptance takes no proof from its caller");
      // ── v1.23: an execution claim is not provenance ───────────────────
      ok(/export function deriveLocallyOwned\(registry, req\) \{/.test(dsrc),
        "deriveLocally must take NO implementation parameter — v0.6.0 took one and a caller could run " +
        "the JS evaluator while stamping its output impl-c-derive-… (P-1, probe_execclaim_v07_repro.mjs)");
      ok(/implementation-claim-contradicts-observation/.test(dsrc) &&
         /implementation-provenance-unavailable/.test(dsrc),
        "the authority must observe what the host launched and compare the claim against it — a " +
        "conforming trace does not prove C executed anything, and neither does a string");
      // ── v1.25: the authority hashed one thing and executed another ────
      // P-3. The two halves of a launch descriptor were independent fields of
      // one caller-supplied object; hashing X and invoking Y is not observation.
      const hostSrc = existsSync(A("observed_execution_host.mjs"))
        ? readFileSync(A("observed_execution_host.mjs"), "utf8") : "";
      const hostNoc = hostSrc.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
      ok(hostSrc !== "", "observed_execution_host.mjs absent — launching must live in ONE place that " +
        "holds no TRVM semantics, or the mechanism gets rebuilt per plane and P-3 is rebuilt with it");
      ok(!/async execute\([^)]*launcher/.test(dnoc),
        "execute must take no `launcher`. v0.8.0's carried artifact_files beside spawn(), two " +
        "mechanically unrelated fields, so the authority hashed X and invoked Y (P-3, " +
        "probe_execlaunch_v09_repro.mjs). Its exact parameter list is asserted at v1.26 below");
      ok(!/nameArtifact/.test(dnoc),
        "nameArtifact must be gone from the authority — the catalog IS the naming policy and it is " +
        "fixed at the host's construction. An authority whose identity policy moves during its " +
        "lifetime makes its own historical observations hard to read");
      ok(/catalog-entrypoint-outside-closure/.test(hostNoc),
        "the host must refuse a catalog entry whose entrypoint is not inside the closure it hashes — " +
        "that is P-3 with the descriptor moved indoors, which is not a repair");
      ok(/catalog-entry-extra-field/.test(hostNoc),
        "the host must refuse a catalog entry carrying any field beyond {kind, entrypoint, " +
        "artifact_closure} — an extra field is exactly where a spawn() would reappear");
      // ── v1.29: sever before validating ────────────────────────────────
      ok(/const owned = ownCanonical\(ast\);/.test(dnoc) &&
         /const id = programSemId\(owned\);/.test(dnoc),
        "ProgramRegistry.bind must SEVER the AST before computing its identity. Hashing the caller's " +
        "object and cloning it afterwards is two reads of state the caller owns, so a getter can give " +
        "the id one program and the store another (P-6b, probe_snapshot_v12_repro.mjs)");
      ok(/JSON\.parse\(canonicalBytes\(catalog\)\)/.test(hostNoc) &&
         /host-catalog-must-be-plain-data/.test(hostNoc),
        "the executor catalog must be snapshotted ONCE before validation, and must be canonical plain " +
        "data. v0.1.0 read `entrypoint` four times and stored the fourth, so a getter put an " +
        "entrypoint outside its own hashed closure into the immutable catalog (P-6)");
      {
        const os = entries.find((x) => x.id === "derivation.owned-snapshot" && x.revision === 1);
        ok(!!os && os.canonical === true && os.status === "PROPERTY-TESTED",
          "law derivation.owned-snapshot@1 missing, non-canonical, or not PROPERTY-TESTED (v1.29)");
        ok(!!os && /CONSULTED TWICE ACROSS A TRUST DECISION/.test(os.statement ?? ""),
          "derivation.owned-snapshot@1 must state the general rule and not only the two instances — " +
          "the value of this one is that it is meant to END the supplier ladder rather than extend it");
        ok(!!os && /THE MILDER OUTCOME IS NOT A DEFENCE/.test(os.statement ?? ""),
          "derivation.owned-snapshot@1 must say why P-6b counts even though it fails closed. A second " +
          "mechanism catching the first is not the first working");
      }
      // ── v1.30: the law was right and it stopped at the constructor ────
      // v1.29 asserted the snapshot rule wherever authority state was BUILT.
      // P-7 lived in the space those assertions did not reach: method
      // arguments. These check the same rule at the other boundary.
      ok(/export function ownCanonical\(v\) \{/.test(dnoc) &&
         /return deepFreeze\(JSON\.parse\(canonicalBytes\(v\)\)\);/.test(dnoc),
        "the snapshot must be ONE exported function, not a discipline repeated at each entrypoint. " +
        "v0.12.0 stated the rule correctly and applied it only where it had been written down; a rule " +
        "that must be remembered at each new method is one that will be forgotten at the next");
      for (const [m, pat] of [
        ["authorize/intent", /ownIntent = ownCanonical\(intent\)/],
        ["authorize/options", /ownOptions = ownCanonical\(options\)/],
        ["wasIssued/req", /snapshot = ownCanonical\(req\)/],
        ["accept/res", /ownRes = ownCanonical\(res\)/],
        ["observationOf", /ownReq = ownCanonical\(req\); ownRes = ownCanonical\(res\)/],
      ]) ok(pat.test(dnoc),
        `${m} must be snapshotted at method entry — the law covers every non-root data argument, not ` +
        "only the constructor data a witness happened to be written against");
      ok(/const issued = iss\.request;/.test(dnoc) &&
         (dnoc.match(/const issued = iss\.request;/g) ?? []).length === 2,
        "execute() and accept() must both bind the AUTHORITY'S OWN copy of the request out of " +
        "wasIssued() and read that. Authenticating the caller's object and then continuing to read it " +
        "is P-7: the bytes that passed are one read, and the next read need not agree with them");
      ok(/message: issued \}/.test(dnoc) && !/message: req \}/.test(dnoc),
        "the invocation the host runs must carry the ISSUED request. Passing the live argument is the " +
        "exact forgery: const(5) answered wasIssued and const(999) answered the host and the worker");
      // the reusable exports must snapshot, and the internals must be ...Owned
      for (const n of ["checkRequest", "checkIntent", "checkResult", "deriveLocally",
        "validateForeignResult"])
        ok(new RegExp("export function " + n + "Owned\\(").test(dnoc) &&
           new RegExp("export const " + n + " = \\(").test(dnoc),
          `${n} must exist as ${n}Owned (the implementation, whose precondition is that its argument ` +
          "is already owned) and as a snapshotting public export. These rereading validators are " +
          "exported, so a second authority built on them would recreate P-7 with no new trust logic");
      // acceptance must not rebuild a historical invocation from present state
      ok(/#executions = new Map\(\)/.test(dnoc) &&
         /this\.#executions\.get\(ownReq\?\.request_id\)/.test(dnoc) &&
         !/observationOf\(DERIVE_EXEC_DOMAIN,\s*$/m.test(dnoc.replace(/\s+/g, " ")) &&
         /observationOfCanonical\(DERIVE_EXEC_DOMAIN, ic,/.test(dnoc),
        "acceptance must ask the observation table about the invocation THAT ACTUALLY CROSSED, " +
        "recorded at execute() time, rather than rebuilding one from this.#registry.image(). " +
        "bindProgram() legitimately grows that image, so rebuilding made the provenance of an earlier " +
        "genuine execution disappear — fail-closed, and still wrong: unrelated future installation " +
        "must not erase evidence of what previously ran");
      ok(/input_canonical: inputCanonical/.test(hostNoc),
        "the host must return the invocation bytes it keyed, so a caller can record what crossed " +
        "instead of reconstructing it later from state that has since moved");
      ok(/\? \{ ok: true, request: stored\.request \}/.test(dnoc),
        "wasIssued() must return the issued request and not only a boolean. 'Yes' forces its caller to " +
        "go on using the object it just authenticated, and an object that is authenticated is not " +
        "thereby owned");
      {
        const es = entries.find((x) => x.id === "derivation.entry-snapshot" && x.revision === 1);
        ok(!!es && es.canonical === true && es.status === "PROPERTY-TESTED",
          "law derivation.entry-snapshot@1 missing, non-canonical, or not PROPERTY-TESTED (v1.30)");
        ok(!!es && /AUTHENTICATES ONE READ OF EXTERNAL STATE AND EXERCISES AUTHORITY USING ANOTHER/
          .test(es.statement ?? ""),
          "derivation.entry-snapshot@1 must state the rule over AUTHORITY OPERATIONS, not over " +
          "constructors. The v1.29 law was already true and already written down when P-7 was found " +
          "underneath it; what was missing was its reach, not its content");
        ok(!!es && /MAY INVOKE JavaScript accessor and Proxy behaviour/.test(es.statement ?? ""),
          "derivation.entry-snapshot@1 must DECLARE OPEN that canonicalisation runs caller accessor " +
          "and Proxy code while capturing its snapshot. 'canonicalBytes refuses a capability' is true " +
          "of a capability as a VALUE and not of a getter, and the honest claim is that no such " +
          "behaviour SURVIVES the boundary — the stronger one needs a serialized-wire ingestion this " +
          "tree does not have");
        ok(!!es && /REGRESSION DETECTOR AND NOT A TERMINATING PROOF/.test(es.statement ?? ""),
          "derivation.entry-snapshot@1 must say that the read-count enumeration does not terminate the " +
          "question. Object.keys(x) twice leaves an accessor's count at zero, so a field-read counter " +
          "sees only the `get` category; calling it a proof would be the stale-instrument class with " +
          "the instrument being the one this round added");
        ok(!!es && /HISTORICAL FACT IS NOT A FUNCTION OF CURRENT CONFIGURATION/.test(es.statement ?? ""),
          "derivation.entry-snapshot@1 must record that acceptance may not rebuild a past invocation " +
          "from present state. bindProgram() legitimately grows the registry image, and rebuilding " +
          "made a genuine execution's provenance vanish — fail-closed, and still wrong");
        ok(!!es && /ONE ARGUMENT TO THE RIGHT/.test(es.statement ?? ""),
          "derivation.entry-snapshot@1 must record why the RESULT side was closed in the same round " +
          "rather than waiting for its own witness — seven rungs have each been found in the parameter " +
          "next to the one that was just repaired");
      }
      ok(/canonicalBytes\(invocation\)/.test(hostNoc),
        "the host must canonicalise the invocation, which refuses a function outright. That is the " +
        "mechanical reason an action cannot ride along with a declaration, rather than a convention");
      // ── v1.30: …and must RUN the snapshot it keyed (P-7c) ─────────────
      ok(/owned = JSON\.parse\(inputCanonical\)/.test(hostNoc) &&
         /runNodeWorker\(entry, owned\)/.test(hostNoc) &&
         /runNativeExec\(entry, owned\)/.test(hostNoc),
        "the host must launch the SNAPSHOT it keyed, not the caller's object. v0.2.1 canonicalised " +
        "the invocation for the observation key and handed the live object to the transport, so an " +
        "invocation honest on read 1 and hostile on read 2 was keyed under one request and executed " +
        "as another — leaving a TRUE-LOOKING observation for an execution that did not happen, in the " +
        "table built so that relabelling would move the key. The obligation belongs to the " +
        "ENTRYPOINT: DerivationAuthority.execute passes owned parts, but the host is exported and " +
        "FilmAuthority and lowering_check drive it directly (P-7c, probe_reread_v13_repro.mjs)");
      ok((hostNoc.match(/this\.#observed\.set\(/g) ?? []).length === 1 &&
         /list\.push\(Object\.freeze/.test(hostNoc),
        "the host's observation table must have exactly one writer, and must keep ALL sessions per " +
        "key: the key is over BYTES, so two launches producing identical output share it. v0.8.0 " +
        "overwrote and then reported one executor_session_id as if it named this copy's launch");
      ok(/executor_sessions: observed\.executor_sessions/.test(dnoc),
        "acceptance must report executor_sessionS. Reporting one id overclaims uniqueness the key " +
        "cannot support");
      // ── v1.32: …and the plural fields must stay CORRELATED ────────────
      ok(/export function summariseObservations\(tuples\)/.test(hostNoc) &&
         /executable_artifact_id: artifacts\.length === 1 \? artifacts\[0\] : null/.test(hostNoc) &&
         /execution_observations,/.test(hostNoc),
        "the observation shape must be built from TUPLES, in one place, with every singular id " +
        "derived and null unless unique. Round 24 made executor_sessions plural and left " +
        "executable_artifact_id as list[0] over the same list, so two sessions that ran DIFFERENT " +
        "artifact bytes were reported under one artifact id — selecting one column from the first row " +
        "and another from all rows, then presenting the pair as a record");
      ok(/return summariseObservations\(hits\.flatMap\(\(o\) => o\.execution_observations\)\)/.test(dnoc),
        "the authority's cross-invocation merge must go through the host's summariser rather than " +
        "recombining families, artifacts and sessions field by field. The first version of that merge " +
        "rewrote the same correlation bug one level up, which is how a mechanism gets duplicated and " +
        "its semantics drift apart");
      ok(/execution_observations: observed\.execution_observations/.test(dnoc) &&
         /executable_artifact_ids: observed\.executable_artifact_ids/.test(dnoc),
        "acceptance must surface the correlated evidence, not only the summaries — a caller shown " +
        "one artifact id beside two sessions has been told something the evidence does not say");
      {
        const om = entries.find((x) => x.id === "derivation.observation-multiplicity" && x.revision === 1);
        ok(!!om && om.canonical === true && om.status === "PROPERTY-TESTED",
          "law derivation.observation-multiplicity@1 missing, non-canonical, or not PROPERTY-TESTED (v1.32)");
        ok(!!om && /EVIDENCE FIELDS THAT VARY TOGETHER MAY NOT BE INDEPENDENTLY COLLAPSED/
          .test(om.statement ?? ""),
          "derivation.observation-multiplicity@1 must state the general rule. 'Report the artifact id " +
          "as well' would be the instance without the principle, and the principle is what stops the " +
          "next pair of correlated fields being averaged into a sentence");
        // SEVERITY IS A FIELD, NOT A SENTENCE. This asserted the presence of the
        // exact English phrase "not a forgery but a PROVENANCE SHAPE defect"
        // until v1.33, which made editorial wording load-bearing: the prose
        // could not be improved without the checker reading it as a change of
        // meaning. The distinction is worth mechanising and the sentence is not
        // the mechanism.
        ok(!!om && om.defect_class === "provenance-shape" &&
           om.accepted_false_verdict === false && om.underlying_observations_genuine === true,
          "derivation.observation-multiplicity@1 must carry its severity as STRUCTURED metadata: " +
          "defect_class provenance-shape, accepted_false_verdict false, " +
          "underlying_observations_genuine true. Both executions happened and both produced these " +
          "bytes; what overclaimed was the SHAPE, and filing it as a forgery would misdescribe the " +
          "severity in the flattering direction");
        const es2 = entries.find((x) => x.id === "derivation.entry-snapshot" && x.revision === 1);
        ok(!!es2 && es2.defect_class === "authority-forgery" &&
           es2.accepted_false_verdict === true,
          "and the contrast must be expressed in DATA: derivation.entry-snapshot@1 is an " +
          "authority-forgery where a false verdict really was reachable. A severity distinction that " +
          "exists only in one law's prose is not a distinction the record can be queried about");
      }
      // every entry that declares a defect_class must declare a KNOWN one, and
      // must answer both severity questions rather than one of them
      for (const e of entries) {
        if (e.defect_class === undefined) continue;
        ok((g.defect_class_vocabulary ?? []).includes(e.defect_class),
          `defect_class '${e.defect_class}' of ${e.id}@${e.revision} not in defect_class_vocabulary`);
        ok(typeof e.accepted_false_verdict === "boolean" &&
           typeof e.underlying_observations_genuine === "boolean",
          `${e.id}@${e.revision} declares a defect_class without answering both severity questions — ` +
          "a class name alone re-creates the prose problem with fewer characters");
      }
      {
        const ip4 = entries.find((x) => x.id === "derivation.implementation-provenance" && x.revision === 4);
        ok(!!ip4 && ip4.canonical === true,
          "law derivation.implementation-provenance@4 missing or non-canonical (v1.25)");
        ok(!!ip4 && /may not carry both the evidence and an independent executable action/.test(ip4.statement ?? ""),
          "derivation.implementation-provenance@4 no longer carries the launch-descriptor rule — that " +
          "sentence is the whole round");
        ok(!!ip4 && /not hardware-attested/i.test(ip4.statement ?? ""),
          "@4 must keep the conservative reading of hash-then-launch. 'The host observed artifact X " +
          "immediately before requesting execution of path P' is not 'the OS executed those bytes'");
        const ip3b = entries.find((x) => x.id === "derivation.implementation-provenance" && x.revision === 3);
        ok(!!ip3b && ip3b.canonical === false && /superseded/i.test(ip3b.revision_note ?? ""),
          "derivation.implementation-provenance@3 must stay on the record as history — it said the " +
          "authority reads the artifact itself, and that was true and not sufficient");
      }
      // ── v1.24: executor existence is not execution provenance ─────────
      ok(!/registerExecutor/.test(dnostr),
        "registerExecutor must be DELETED, not deprecated — it took a name, launched nothing, observed " +
        "nothing, and returned a handle whose private Symbol proved only that this authority minted it " +
        "(P-2, probe_execreg_v08_repro.mjs)");
      // v1.25 moved the launching machinery into ObservedExecutionHost, so the
      // v1.24 assertions about it are asserted THERE, above. What stays here is
      // the property that outlives the move: the authority must not hold a
      // second way to become provenanced.
      ok(/digestArtifactFiles/.test(hostNoc) && !/digestArtifactFiles\(/.test(dnoc),
        "artifact hashing must live in the host and be reachable from the authority only THROUGH it — " +
        "an authority that can hash on its own has a second path to an observation");
      ok(/executionKey\(domain, inputCanonical, output\)/.test(hostNoc) &&
         /canonicalBytes\(output\)/.test(hostNoc),
        "the observation must be keyed over the WHOLE execution event — H(domain | input | " +
        "canonical(output)) — so relabelling moves the key rather than being compared against it");
      ok(!/#observed/.test(dnoc),
        "the authority must hold NO observation table of its own; there is exactly one, in the host");
      {
        const ip3 = entries.find((x) => x.id === "derivation.implementation-provenance" && x.revision === 3);
        ok(!!ip3, "law derivation.implementation-provenance@3 missing (v1.24)");
        ok(!!ip3 && /EXECUTOR EXISTENCE IS NOT EXECUTION PROVENANCE/.test(ip3.statement ?? ""),
          "derivation.implementation-provenance@3 no longer opens with 'executor existence is not " +
          "execution provenance' — that sentence is the whole round");
        ok(!!ip3 && /not hardware-attested/i.test(ip3.statement ?? ""),
          "derivation.implementation-provenance@3 must state conservatively what hash-then-spawn " +
          "proves. 'The host observed artifact X immediately before requesting execution of path P' is " +
          "not 'the OS executed those bytes', and turning the first into the second is exactly the " +
          "overclaim @1 and @2 were each superseded for");
        const ip2b = entries.find((x) => x.id === "derivation.implementation-provenance" && x.revision === 2);
        ok(!!ip2b && ip2b.canonical === false && /SUPERSEDED/i.test(ip2b.revision_note ?? ""),
          "derivation.implementation-provenance@2 must stay on the record as history — it claimed the " +
          "host observed what it launched while registration launched nothing");
      }
      // ── v1.45: EMISSION_CONFORMANCE-v1 ────────────────────────────────
      // The same source discipline the film emitter is held to: no expected
      // table, and the oracle passed in rather than chosen. A conformance
      // battery carrying its own answers is a transcription theorem.
      {
        const ec = entries.find((x) => x.id === "derivation.emission-conformance" && x.canonical === true);
        ok(!!ec && ec.status === "PROPERTY-TESTED",
          "derivation.emission-conformance has no canonical PROPERTY-TESTED revision (v1.45)");
        ok(!!ec && /FUNCTION OF THE CLOSED TEMPLATE AND NOT OF THE PROGRAM/.test(ec.statement ?? ""),
          "emission-conformance must record that emission's domain is the CLOSED TEMPLATE. Two " +
          "different programs reaching one closed template and emitting identically is the property, " +
          "and an emitter that distinguished them would be reading what instantiation already erased");
        ok(!!ec && /THREE IDENTITIES FORM A LADDER, AND EMISSION PROVES THE MIDDLE ONE/.test(ec.statement ?? ""),
          "emission-conformance must state the identity LADDER — bytes, target term, outcome — and " +
          "which rung it proves. Framed as a PAIR it hides that target_term_sem_id sits BETWEEN " +
          "bytes and meaning, and a receipt carrying no byte digest would look like it proved the " +
          "bytes");
        ok(!!ec && /MUST NOT claim 'these exact bytes were produced'/.test(ec.statement ?? ""),
          "emission-conformance must state what the receipt does NOT prove. Its codomain deliberately " +
          "erases the spelling, so a byte claim would be one the fields cannot support");
        const lowSrcE = existsSync(A("lowering.mjs")) ? readFileSync(A("lowering.mjs"), "utf8") : "";
        // B6.2 — THE PROJECTION, not merely the prose. B6.1 ruled label spelling
        // nonsemantic and left the semantic ids hashing it, so the dual
        // property held in one direction only. These assert the SPLIT, which
        // is the structural form of "must stay put".
        ok(/export const CANONICAL_EMITTER_PROFILE = Object\.freeze/.test(lowSrcE) &&
           /export const CANONICAL_EMITTER_PROFILE_ID =/.test(lowSrcE),
          "the canonical emitter's SERIALIZATION profile must be its own object with its own " +
          "identity. Counter start, traversal, binder spelling and exact bytes are representative " +
          "choices the codomain quotients away, and an identity that hashes them moves for changes " +
          "its own output cannot see");
        ok(/label_counter_start: \d+/.test(lowSrcE) &&
           /const labels = \{ n: profile\.label_counter_start, next\(\)/.test(lowSrcE),
          "emit() must READ label_counter_start from the profile rather than hard-coding it beside " +
          "an English description. Before B6.2 the prose was hashed and the constant was not, so " +
          "REWORDING the policy moved EMISSION_SEM_ID while CHANGING it did not — the dual property " +
          "failing in both directions at once");
        // ── B6.3: THE PROFILE IS INTERPRETED IN EVERY FIELD, NOT ONE ──────
        // B6.2 shipped one knob beside five sentences and hashed all six, so
        // the defect it fixed for label_counter_start survived one field over
        // in BOTH directions — reword binder_spelling and the id moved for
        // nothing; change the actual binder spelling and it stood still while
        // 6 of 9 fixtures' bytes changed. Asserted structurally, because a
        // rule that only forbids today's five sentences invites a sixth.
        ok(/label_alloc_order: "/.test(lowSrcE) && /binder_names: Object\.freeze/.test(lowSrcE) &&
           /function labelAllocPreOrder\(order\)/.test(lowSrcE) &&
           /emitter-profile-unknown-label-alloc-order/.test(lowSrcE),
          "the profile must hold the allocation ORDER and the binder NAMES as interpreted VALUES, " +
          "with an unknown order a NAMED refusal rather than a silent default. B6.2 held both as " +
          "English beside hard-coded behaviour, and `depth-first, operands in declared field order` " +
          "is true of two orders that emit different bytes on 5 of 9 fixtures — a sentence that did " +
          "not even DETERMINE what it was hashed to identify");
        ok(/export const CANONICAL_EMITTER_PROFILE_NOTES = Object\.freeze/.test(lowSrcE) &&
           !/CANONICAL_EMITTER_PROFILE_NOTES\)/.test(lowSrcE),
          "the profile's PROSE must live in an unhashed NOTES sibling — same pattern as " +
          "INSTANTIATION_STATUS beside INSTANTIATION_SEMANTICS. Deleting the sentences would lose " +
          "the reasoning; hashing them moves an identity for a reword, which B6.2 did on all five");
        ok(/export const CANONICAL_EMITTER_ARTIFACT_ID =/.test(lowSrcE) &&
           /export const emitterArtifactId =/.test(lowSrcE) &&
           /export const EMITTER_ARTIFACT_MEMBERS = Object\.freeze/.test(lowSrcE),
          "the emitter IMPLEMENTATION must carry its own identity, derived from the source of every " +
          "function that produces bytes. A profile is CONFIGURATION and cannot bind an implementation " +
          "that declines to read it: B6.2's byte-reproducibility theorem named the profile as its " +
          "whole precondition and survived {f0,f1} -> {q0,q1} inside the combinator, which moved the " +
          "bytes on 6 of 9 fixtures");
        // ── B6.3.1: THE BUNDLE MUST BE THE WHOLE CLOSURE ──────────────────
        // GPT's falsifier against B6.3: emit() read a module-level enum table
        // that cema- did not hash, so one boolean flipped in it moved the bytes
        // on 5 of 9 fixtures while template, profile id AND artifact id stood
        // still. Repairing that one table alone would leave the next helper
        // exactly as exposed, which is why membership is DERIVED.
        ok(/export const EMITTER_ARTIFACT_INERT = Object\.freeze/.test(lowSrcE) &&
           /export const emitterArtifactBundle =/.test(lowSrcE) &&
           !/^const LABEL_ALLOC_ORDERS/m.test(lowSrcE),
          "the artifact bundle must name its members, DECLARE what may be referenced without being " +
          "bundled and why, and hold no module-level table the emitter reads from outside it. If " +
          "changing a piece of implementation can change emitted bytes while the template and profile " +
          "stay fixed, that piece belongs to the artifact identity");
        {
          const esrc3 = existsSync(A("emission_conformance.mjs")) ? readFileSync(A("emission_conformance.mjs"), "utf8") : "";
          ok(/E-2e the artifact bundle is the WHOLE byte-producing closure/.test(esrc3)
             && /moduleNames/.test(esrc3) && /EMITTER_ARTIFACT_INERT/.test(esrc3),
            "the bundle's completeness must be DERIVED from lowering.mjs's own module-level bindings, " +
            "not maintained by hand. artifact_versions was a hand-kept map with three of six entries " +
            "no check read — correct the day it was written and silently short afterwards, which is " +
            "the same failure one artifact down");
          // ANCHORED ON THE DECLARATION, per B6.2 §353 — `/betaEmit/` matches
          // the call site too, so renaming the declaration leaves it green.
          // The convention existed; this assertion was written without it and
          // its own negative case said so on the first run.
          ok(/E-8 a GENERIC structural alternate/.test(esrc3) && /const betaEmit = /.test(esrc3)
             && /E-8b the add-specific ALGEBRAIC alternate/.test(esrc3),
            "E-8's meaning-preserving alternate must be GENERIC — a beta redex around the term — and " +
            "the add-specific operand swap must be kept beside it as a measurement rather than as the " +
            "carrier of the theorem. Riding on add's commutativity made E-8 cover 6 of 9 fixtures and " +
            "guaranteed it would lose its adversary the day `sub` arrived, for a reason having " +
            "nothing to do with what E-8 proves");
        }
        ok(!/three_grades:/.test(lowSrcE),
          "the bytes -> target term -> outcome LADDER must be GONE from TARGET_ENCODING. It is an " +
          "accurate account of the proof architecture and not a property of the executable encoding, " +
          "and rewording it moved xenc and, through it, esem, while every emitted byte and all 11 " +
          "conformance cases stood still — B1.1's defect family, EXPLANATORY rather than governance " +
          "prose. It is stated in three unhashed places instead");
        ok(/SUPERSEDED_EXPLANATORY_PROSE_SEM_IDS/.test(lowSrcE),
          "the B6.2 xenc, esem and profile ids must be KEPT on the record, with which of the three " +
          "moves were corrections and which was a redefinition named rather than left to a reader " +
          "diffing two packs");
        ok(!/dup_label_policy:/.test(lowSrcE),
          "dup_label_policy must be GONE from the semantic target encoding. It is a serialization " +
          "choice and it now lives in CANONICAL_EMITTER_PROFILE; leaving it in place beside the " +
          "profile would be the two-artifacts-one-hash defect it was moved to fix");
        ok(!/TARGET_ENCODING\.dup_label_policy — a counter from 0/.test(lowSrcE),
          "TARGET_TEMPLATE_ENCODING must not name a downstream counter start. A layer whose whole " +
          "claim is that no allocation exists in it cannot also commit to how one is performed two " +
          "layers down — hashing it meant an emitter allocation change re-cut the TEMPLATE, LOWERING " +
          "and INSTANTIATION identities");
        {
          const esrc2 = existsSync(A("emission_conformance.mjs")) ? readFileSync(A("emission_conformance.mjs"), "utf8") : "";
          ok(/E-1a SEMANTIC relation determinism/.test(esrc2) && /E-1b CANONICAL byte reproducibility/.test(esrc2)
             && /E-2b the profile is SEPARATE, INTERPRETED, and PROSE-FREE/.test(esrc2),
            "emission_conformance.mjs must test the two determinisms SEPARATELY — semantic relation " +
            "determinism belongs to EMISSION_SEM_ID and byte reproducibility to " +
            "CANONICAL_EMITTER_PROFILE_ID plus CANONICAL_EMITTER_ARTIFACT_ID — and must assert the " +
            "profile is separate, interpreted AND prose-free. Checked as one theorem, byte " +
            "reproducibility re-cuts the semantic relation");
          // B6.3: the knob falsifier must RUN. B6.2 stated its counter result
          // in the ledger because a frozen module constant cannot be varied by
          // the battery meant to falsify it — the shape three round-10
          // instruments were found in, reporting without measuring.
          ok(/E-2c a KNOB moves bytes and the profile id, and NO semantic id/.test(esrc2)
             && /E-2d the IMPLEMENTATION moves the artifact id, and NO semantic id/.test(esrc2)
             && /emit\(r\.closed, alt\.profile\)/.test(esrc2),
            "both serialization directions must be MEASURED here rather than narrated in a ledger: a " +
            "knob change moving bytes and the profile id and no semantic id, and an implementation " +
            "change moving the artifact id and no semantic id. The first requires emit() to take the " +
            "profile as a PARAMETER — a property this tree states and cannot run is the shape three " +
            "instruments at round 10 were found in");
        }
        // THE LABEL ONTOLOGY, in the encoding that owns it.
        ok(/label_semantics:/.test(lowSrcE) && /EQUALITY STRUCTURE, NOT THE SPELLING/.test(lowSrcE),
          "TARGET_ENCODING must separate label EQUALITY/FRESHNESS structure (semantic — collapsing " +
          "two dups onto one label changes whether DUP-SUP= or DUP-SUP! fires) from the integers " +
          "chosen to represent it (not semantic). B6 justified the allocation as semantic because " +
          "'the label reaches the canonical signature', which its own conformance battery measured " +
          "false on every fixture");
        ok(!/would otherwise be an allocation detail hiding inside a semantic id/.test(lowSrcE),
          "the superseded label justification must be GONE from dup_label_policy rather than sitting " +
          "beside its correction. Two justifications for one field, one of them measured false, is " +
          "the prose-versus-record drift this tree keeps paying for");
        ok(/SUPERSEDED_LABEL_SEMANTICS_SEM_IDS/.test(lowSrcE),
          "the B6 emission and executable-encoding ids must be KEPT on the record. They were the " +
          "honest ids of the projection B6 shipped, and a record that silently replaced them would " +
          "be doing the thing this correction is about");
        ok(!!ec && /byte-equivariant under alpha-renaming and label permutation/.test(ec.statement ?? ""),
          "emission-conformance must record that an ALPHA-EQUIVALENT alternate emitter produces the " +
          "IDENTICAL target_term_sem_id, so renaming cannot witness the alternate-emitter property and " +
          "the adversary must be structural. That was measured against a stated expectation that it " +
          "would differ, and a law that loses the correction invites the same draft again");
        const esrc = existsSync(A("emission_conformance.mjs")) ? readFileSync(A("emission_conformance.mjs"), "utf8") : "";
        ok(esrc.length > 0 && /makeEmissionVerifier\(\{ canonicaliseTarget/.test(esrc),
          "emission_conformance.mjs must obtain its verifier by BINDING a canonicaliser it supplies, " +
          "never by letting the relation's own module choose the oracle that judges it");
        // NO EXPECTED TABLE, the same encoding the film side uses: a
        // target_term_sem_id literal in the battery would be a transcription
        // theorem wearing a conformance name.
        ok(!/(ctmpl|esem)-[0-9a-f]{16}/.test(esrc) && !/target_term_sem_id\s*[:=]\s*"[0-9a-f]{16}/.test(esrc),
          "emission_conformance.mjs must contain NO expected identity literals. Every id it compares " +
          "is computed in the run; a conformance theorem whose expected values were transcribed from " +
          "a previous run of the thing under test proves only that nothing changed");
        // AND THE REVIEW PACK MUST RUN IT. It shipped the file and the
        // Makefile target for one build without ever calling it — a
        // shipped-but-unrun gate, which is worse than a skipped one because a
        // skip is at least visible in the count.
        {
          const mrp = existsSync(A("make_review_pack.sh")) ? readFileSync(A("make_review_pack.sh"), "utf8") : "";
          ok(/run "emission conformance" governance node emission_conformance\.mjs/.test(mrp),
            "make_review_pack.sh's verify.sh must RUN emission_conformance.mjs. And OUTSIDE the gcc " +
            "block: placed beside the film gate, a reviewer without a compiler would see it SKIPPED, " +
            "which reads as 'emission conformance needs the runtime' — the layer collapse the " +
            "battery exists to refuse");
        }
        ok(/const MEASURED = \{\}/.test(esrc) && /MEASURED\.alpha_identical/.test(esrc)
             && !/REFUSED on all \d/.test(esrc),
          "emission_conformance.mjs's PASS headline must be DERIVED from fields the cases write. B6's " +
          "summary asserted that allocation drift is refused on all eight and that an alpha-equivalent " +
          "emitter differs in id — both contradicted by the cases printed immediately above them in " +
          "the same run, and the summary is what lands in RESULTS.txt");
        // MATCH THE DECLARATION, NOT THE NAME. The first version tested
        // /driftEmit/, which `notTheDriftEmitter` satisfies as a substring —
        // the same defect as counting MENTIONS of phase_pin_lint.py instead of
        // INVOCATIONS, twice in one session, and both times the negative case
        // written beside the assertion is what caught it.
        ok(/const driftEmit = /.test(esrc) && /const equivEmit = /.test(esrc),
          "the canonical-drift adversary and the semantic-equivalence adversary must be SEPARATE. " +
          "Fused, E-F1 would lose its adversary the moment a non-commutative operator arrived, for a " +
          "reason having nothing to do with what E-F1 proves");
        ok(/two-port collapse/.test(esrc) && /ADD\(IN\("x"\), ADD\(IN\("x"\), IN\("y"\)\)\)/.test(esrc),
          "the emission fixture family must carry the ACTUAL I-4c (x + (x + y)), and must not call " +
          "add(x,y) by that name — 2+3 == 3+2, so it is the symmetric fixture I-4c exists to reject");
        ok(/INTEGRATION/.test(esrc) && /labelled/i.test(esrc),
          "the downstream composition must be LABELLED an integration theorem. Emission correctness " +
          "defined by what the emitted term computes puts the runtime inside the compiler's contract");
      }
      // ── v1.44: M-10, the phase-pinned live target ─────────────────────
      // The guard must be WIRED, not merely present. A lint that exists in the
      // tree and is called by nothing is the instrument-nonvacuity species
      // wearing a new noun, and this law is about instruments that have
      // stopped measuring.
      {
        const pp = entries.find((x) => x.id === "evidence.phase-pinned-target" && x.canonical === true);
        ok(!!pp && pp.status === "PROPERTY-TESTED",
          "evidence.phase-pinned-target has no canonical PROPERTY-TESTED revision (v1.44)");
        ok(!!pp && /HISTORY MAY BE PINNED\. LIVE STATE MUST BE DERIVED\./.test(pp.statement ?? ""),
          "evidence.phase-pinned-target@1 must state the rule in the form that makes it usable. The " +
          "distinguishing question is what the instrument's SUBJECT is, not whether a number appears " +
          "in it — a law phrased as 'avoid literals' would force nine history cases to stop testing " +
          "history");
        const nbSrc = existsSync(A("negative_battery.sh")) ? readFileSync(A("negative_battery.sh"), "utf8") : "";
        const hsSrc = existsSync(A("harness_selftest.sh")) ? readFileSync(A("harness_selftest.sh"), "utf8") : "";
        // COUNT INVOCATIONS, NOT MENTIONS. The first version of this matched
        // /phase_pin_lint\.py/ — so replacing `python3` with `true` disarmed
        // the guard while the string count stayed at 2 and this assertion
        // stayed green. Caught by its own negative case on the first run,
        // which is the whole argument for writing the forgery beside the
        // assertion rather than after it.
        const calls = (nbSrc.match(/python3 "\$BASE\/phase_pin_lint\.py"/g) ?? []).length;
        ok(existsSync(A("phase_pin_lint.py")) && calls >= 2,
          `phase_pin_lint.py must exist and be INVOKED by both negative runners (found ${calls} ` +
          "invocations). run_case has two variants and a guard wired into one of them leaves the " +
          "other blind — which is exactly how $SCRATCH went unassigned in one runner for four rounds");
        ok(/HISTORY_PIN_OK/.test(nbSrc) && /HISTORY_PIN_OK/.test(readFileSync(A("phase_pin_lint.py"), "utf8")),
          "the history exemption must be BOTH implemented in the lint and USED in the battery. An " +
          "exemption nothing claims is either unnecessary or the rule is being satisfied by cases " +
          "that quietly stopped testing history");
        ok(/M-10/.test(hsSrc) && /phase-pin-goes-blind/.test(hsSrc),
          "harness_selftest must carry M-10 INCLUDING the blindness measurement. Asserting that the " +
          "lint fires is not the claim; the claim is that every OTHER apparatus check passes on a " +
          "phase-pinned case, which is why it needed a guard of its own");
      }
      // ── v1.24 / v1.41: the execution plane originates evidence ────────
      {
        /* THE CANONICAL REVISION, FOUND BY CANONICITY AND NOT BY NUMBER. This
           was `revision === 3` and, before that, 2, and before that 1 — edited
           by hand every time the law superseded, which is the same ratchet the
           contiguity check below is about and which B5 found in three other
           places in one round. Every content assertion under it applies to
           WHATEVER IS CANONICAL, so a new revision must carry the durable
           sentences forward rather than inheriting them by being newer. That is
           the convention this law line already follows — each revision restates
           the whole law — and now it is enforced instead of remembered. */
        const nf = entries.find((x) => x.id === "film.native-emission" && x.canonical === true);
        ok(!!nf && nf.status === "PROPERTY-TESTED",
          "film.native-emission has no canonical PROPERTY-TESTED revision. Found " +
          `[${entries.filter((x) => x.id === "film.native-emission")
                     .map((x) => `@${x.revision}${x.canonical ? "*" : ""}`).join(", ")}]`);
        const nf1 = entries.find((x) => x.id === "film.native-emission" && x.revision === 1);
        /* GENERALISED at v1.42 rather than extended to name @2 as well. This
           law line has superseded twice in three rounds and each time this
           check had to be edited to name one more revision — a smaller version
           of the ratchet directly below: an assertion that enumerates the
           current revisions goes stale on the next one. What holds durably is
           the SHAPE — exactly one canonical revision, every superseded one
           still on the record and saying so. None of them is WRONG about what
           it claims; each is narrower than what came after, and @1 in
           particular carries the readback interaction-count record that no
           later revision repeats (asserted separately below). */
        const nfAll = entries.filter((x) => x.id === "film.native-emission");
        const nfCanon = nfAll.filter((x) => x.canonical === true);
        const nfStale = nfAll.filter((x) => x.canonical !== true);
        /* CONTIGUITY IS PART OF IT, and leaving it out was a real weakening the
           battery caught in one run. The first version of this generalisation
           asserted only "one canonical, all stale annotated" — under which
           DELETING @1 outright passes, because what remains is still one
           canonical and one annotated stale. The forgery for it went on being
           caught, but by a DIFFERENT assertion further down that happens to
           require @1 to exist (the ACCIDENTALLY TRUE record). That is the
           coincidental-second-occurrence species this tree has now hit four
           times: an assertion satisfied by something other than the property it
           was written for. Revisions must run 1..N with none missing, so a
           withdrawn round cannot hide behind a survivor. */
        const nfRevs = nfAll.map((x) => x.revision).sort((a, b) => a - b);
        const contiguous = nfRevs.every((r, i) => r === i + 1);
        ok(nfAll.length >= 2 && nfCanon.length === 1 && contiguous
             && nfCanon[0].revision === nfRevs[nfRevs.length - 1]
             && nfStale.every((x) => /SUPERSEDED|history/i.test(x.revision_note ?? "")),
          `film.native-emission must have EXACTLY ONE canonical revision, that revision must be the ` +
          `LATEST, and every superseded one must still be on the record saying so — found revisions ` +
          `[${nfRevs.join(", ")}], ${nfCanon.length} canonical` +
          `${nfCanon.length === 1 ? ` (@${nfCanon[0].revision})` : ""}, ` +
          `${nfStale.filter((x) => /SUPERSEDED|history/i.test(x.revision_note ?? "")).length}/${nfStale.length} ` +
          `annotated${contiguous ? "" : ", NOT CONTIGUOUS"}. Withdrawing a superseded revision loses ` +
          `the round it recorded; leaving two canonical leaves a reader no way to know which binds`);
        /* THE FLOAT-PLANE CLAIM, and the three sentences of it that a later
           round could quietly lose. The locus families and the two-order
           distinction are not decoration: a `d:` index is what makes the film
           replay on a different allocator, and the two orders being DIFFERENT
           orders is the property a maintainer is most likely to "simplify"
           away, because collapsing them still produces a locus that names a
           real redex. */
        ok(!!nf && /t: a structural path/.test(nf.statement ?? "")
             && /DISCOVERY INDEX over live cells/.test(nf.statement ?? ""),
          "the canonical film.native-emission revision must state the three canonical locus families and say what a d: " +
          "locus IS. An index into the live discovery order and a heap address are indistinguishable " +
          "on one allocator and only one of them replays on another");
        ok(!!nf && /BOTH ARE LOAD-BEARING/.test(nf.statement ?? ""),
          "the canonical film.native-emission revision must keep the record that the ENUMERATION order and the LOCUS INDEX " +
          "order are different traversals. Collapsing them is the cheapest available 'simplification' " +
          "and it yields a locus that names a real redex which is not the redex that fired — measured, " +
          "not feared: the perturbation differs on 12 corpus fixtures");
        ok(!!nf && /TRANSCRIPTION THEOREM/.test(nf.statement ?? "")
             && /MEASURED BEFORE IT WAS ASSERTED/.test(nf.statement ?? ""),
          "the canonical film.native-emission revision must record that the relation was measured before it was asserted " +
          "and that no expected table lives in the emitter. A conformance theorem whose expected " +
          "values came from the other implementation is a transcription theorem, and nothing in the " +
          "artifact would show it");
        ok(!!nf && /FRESH FULL-POOL ENUMERATION/.test(nf.statement ?? ""),
          "the canonical film.native-emission revision must state that the terminal is concluded only after a fresh " +
          "full-pool enumeration. 'The loop ended' and 'the rules I implement are exhausted' are the " +
          "two ways a false normal form gets written down, and this fixture is the tree's own witness " +
          "for the second");
        ok(!!nf && /SCOPE, CHECKED RATHER THAN ASSUMED/i.test(nf.statement ?? "")
             && /REFUSED BY NAME/.test(nf.statement ?? ""),
          "the canonical film.native-emission revision no longer states its scope as CHECKED refusals. An emitter that " +
          "silently skipped what it cannot do would be claiming the general case with a fixture's " +
          "evidence — and v0.1.0's scope was stated by the WRONG predicate (dup presence rather than " +
          "dup enabledness), which a refusal makes visible and a silence would not have");
        /* THE RECORD MOVED WITH THE ROUND THAT OWNS IT, and the assertion moved
           with the record rather than being dropped or duplicated. The removed
           readback interaction-count check is a v0.1.0 fact; @2 would be padding
           itself to restate it, and deleting the assertion because the canonical
           statement no longer carries the phrase is how a property gets lost in
           a revision bump. So it is asserted where it lives — on @1, which is
           retained as history — AND independently in ic32_film.c below, which
           is the artifact a future reader is actually looking at. */
        ok(!!nf1 && /ACCIDENTALLY TRUE/.test(nf1.statement ?? ""),
          "film.native-emission@1 must keep the record of the readback check that was removed for " +
          "being accidentally true. A check that passes because the fixture is trivial is not evidence, " +
          "and deleting it without saying why would leave the strongest-sounding sentence unexplained");
        ok(!!nf && /replaySemFilm/.test(nf.statement ?? "") && /WITHOUT normalization or translation/.test(nf.statement ?? ""),
          "the canonical film.native-emission revision must name the kernel's OWN replaySemFilm and say the frame is " +
          "accepted without translation — a checker written for the occasion checks the occasion");
        ok(!!nf && /film_planes/.test(nf.statement ?? ""),
          "the canonical film.native-emission revision must keep the two transition systems apart. The TRVM calculus film " +
          "and the derivation evidence relation share HOST infrastructure and no semantics, and round " +
          "15 §61 exists because a session could otherwise finish the second and write that the first " +
          "was done");
        for (const f of ["bridge/ic32_film.c", "bridge/film_check.mjs"])
          ok(existsSync(A(f)), `film.native-emission@3 cites ${f}, which is absent`);
        const filmSrc = existsSync(A("bridge/ic32_film.c")) ? readFileSync(A("bridge/ic32_film.c"), "utf8") : "";
        ok(/#define IC32_CANON_NO_MAIN/.test(filmSrc) && /#include "ic32_canon\.c"/.test(filmSrc),
          "ic32_film.c must INCLUDE ic32_canon.c rather than copy it — the canonicalizer beneath the " +
          "film has to be the same code the 48/48 bridge gate replays, or the film round is proving a " +
          "canonicalizer nothing else has ever checked");
        /* THE SCOPE PREDICATE HAS MOVED FOUR TIMES AND EVERY MOVE WAS A
           CORRECTION: v0.1.0 refused on dup PRESENCE (wrong — the lowered add
           carries dups and fires none), v0.2.0 on dup ENABLEDNESS (right then,
           a RATCHET the moment the dup rules were built), v0.3.0 on the two
           ERA rules the church_exp_2_2 measurement identified, v0.4.0 on
           nothing rule-shaped at all, because every rule of the pool now has a
           witness. So this assertion no longer names ANY RULE. What it pins is
           the DURABLE property those four spellings were each an instance of:
           a rule the emitter cannot fire must refuse BY NAME rather than be
           silently skipped, and the terminal must be re-derived. Pinning a
           rule name here would have blocked each of the three rounds that
           closed a gap — which is the ratchet species B1.2.1 named, and this
           check has now been on the wrong side of it twice. */
        ok(/film-not-quiescent-at-terminal/.test(filmSrc) && /film-rule-not-implemented/.test(filmSrc),
          "ic32_film.c must CHECK pool-quiescence at the terminal and refuse an unhandled enumerated " +
          "rule BY NAME (film-rule-not-implemented). An emitter that silently skipped what it cannot " +
          "fire would be claiming the general case with a fixture's evidence, and the gap would be " +
          "invisible in the artifact");
        ok(/film-locus-alias/.test(filmSrc),
          "ic32_film.c must REFUSE a canonical-locus alias. A node reachable both from the root and " +
          "from inside a dup value is enumerable under a t: AND a v: locus; the locus is committed " +
          "into frame_id, so two spellings of one transition would be two canonical frame identities " +
          "for the same pre, rule and post. Precedence between them is UNRULED, and refusing is the " +
          "honest answer to an unruled question — picking one silently decides a rule nobody wrote");
        ok(/film-projection-not-unique/.test(filmSrc),
          "ic32_film.c must REFUSE rather than choose when a dup cell's projection is not unique. ic32 " +
          "fires a dup from a DEMANDED SIDE and replaces the projection where it stands, so the film " +
          "has to find that occurrence; a linear net has exactly one, and 'exactly one' is a property " +
          "to check, not a fact to rely on");
        /* B5.1 — THE ARGUMENT BOUNDARY, which B5 left permissive. `strtol(arg,
           NULL, 10)` is the C idiom that reads as far as it can and reports
           nothing about the rest, so `--budget abc` emitted a perfectly valid
           zero-frame film under a policy nobody set, and an ERANGE overflow
           silently became NO budget and returned a COMPLETE film for a
           malformed request. Both checked in the SOURCE as well as behaviourally
           in film_check, because the failure mode is a green artifact: nothing
           about the emitted film looks wrong. Reported by GPT. */
        ok(/strtol\(s, &end, 10\)/.test(filmSrc) && /end == s \|\| \*end/.test(filmSrc),
          "ic32_film.c must parse --budget with strtol's ENDPTR checked. Without it a trailing-junk " +
          "argument is silently truncated to whatever prefix parsed, and the emitter answers a " +
          "question the caller did not ask — with a film that is valid in every field");
        ok(/errno == ERANGE/.test(filmSrc),
          "ic32_film.c must check ERRNO on the budget parse. endptr and errno catch different things: " +
          "endptr catches what was not consumed, errno catches what was consumed and did not fit, and " +
          "the overflow case is the one that returned a COMPLETE normal-form film for a malformed " +
          "request rather than a refusal");
        ok(/film-budget-invalid/.test(filmSrc) && /film-budget-negative/.test(filmSrc),
          "ic32_film.c must keep MALFORMED and OUT-OF-RANGE budgets as separate refusal names. '-1' " +
          "is a number and the caller's POLICY is refused; '3junk' is not a number and the caller's " +
          "INTENT cannot be recovered — one code for both hands a reader a refusal that cannot say " +
          "whether to fix a value or fix a spelling, which is what lower-inputs-undecided lost");
        ok(/film-unknown-flag/.test(filmSrc) && /film-multiple-terms/.test(filmSrc) &&
           /film-budget-missing-value/.test(filmSrc),
          "ic32_film.c must refuse an argument it cannot use rather than silently repurposing it. A " +
          "trailing --budget used to fall through and BECOME the term, so the parser reported a " +
          "syntax error about the calculus for what was an argument error about the CLI");
        /* And the ceilings stay overridable, so the frames guard can be
           witnessed WITHOUT raising a production bound to suit a test. */
        ok(/#ifndef MAXFRAMES/.test(filmSrc) && /#ifndef MAXPATH/.test(filmSrc) &&
           /LIMITS ic32_film/.test(filmSrc),
          "ic32_film.c must keep its resource ceilings compile-time overridable and REPORT the ones " +
          "it was built with (--limits). Raising a production bound to make another production bound " +
          "reachable in a test changes the implementation under test to improve the test surface; and " +
          "a grep of the #define cannot answer the configuration question, because under an override " +
          "the source and the running program disagree");
        /* NO EXPECTED TABLE. The strongest cheap encoding of it: the fixture's
           own distinctive label may appear in the CHECK, which is where a
           fixture belongs, and in neither the emitter nor the comparator, which
           is where an expected answer would have to live to do any harm. */
        for (const f of ["bridge/ic32_film.c", "bridge/measure_compare.mjs"]) {
          ok(existsSync(A(f)), `film.native-emission@3 cites ${f}, which is absent`);
          const src = existsSync(A(f)) ? readFileSync(A(f), "utf8") : "";
          ok(!/&1001\{c0,c1\}/.test(src),
            `${f} contains the church_exp_2_2 fixture term. The FIXTURE belongs in film_check.mjs; an ` +
            `expected answer for it inside the emitter or inside the comparator is how a conformance ` +
            `theorem becomes a transcription theorem, and nothing downstream could tell the difference`);
        }
        ok(/film-budget-exhausted/.test(filmSrc),
          "ic32_film.c must have a TYPED REFUSAL for the budget. A step budget reached while work " +
          "remains is not a normal form, and falling through to NORMAL_FORM is precisely the false " +
          "quiescence church_exp_2_2 falsified law:sched.free.ast-term@1 with at step 15. Portable " +
          "BUDGET_EXHAUSTED film evidence is a later witness; refusing is what is required now");
        ok(/ACCIDENTALLY TRUE/.test(filmSrc),
          "ic32_film.c must record why the readback INTERACTION-COUNT check was removed. v0.1.0 " +
          "asserted the readback fired zero interactions and that was accidentally true on a one-step " +
          "dup-free fixture: ic32's counter is not plane-classified, so comparing it against zero " +
          "measures a different quantity from the kernel's plane-level claim, and it fires four on the " +
          "lowered term whose state is nonetheless correct");
      }
      // ── v1.27: the source language reaches the governed runtime ───────
      {
        /* ── B2.1.1: THE ASSERTION-STRENGTH HIERARCHY, GPT's ruling ────────
           RUNTIME DATA  >  BEHAVIOURAL API  >  PARSED AST  >  RAW TEXT
           and raw-text matching MAY NOT STAND IN FOR STRUCTURE.

           Three consecutive rounds produced an assertion satisfied by a
           coincidental second occurrence of its own search text: `implemented:
           false` matched a COMMENT explaining the overbinding bug;
           `consumed_inputs:` was answered by instantiate()'s RETURN FIELD rather
           than the semantic record it guards; and `"ctmpl-"` matched
           codomain_identity_domain while the real constructor's prefix had been
           renamed. Each was caught by the negative battery, which is the
           instrument working — but the battery should not be the only thing
           standing between a regex and a coincidence.

           So this block IMPORTS the module. A record's contents are read as
           DATA; an API's shape is read by CALLING it; and text matching is
           reserved for properties that are genuinely textual — a version
           constant, a forbidden phrase, a NUL byte — or for code-shape
           obligations that would need a JS parser this tree does not have, which
           are marked TEXT-TIER below so a reader knows which rung they are on.

           AND THE COROLLARY, which B2.1.1 learned by shipping it: REPRESENTATION
           STRENGTH DOES NOT IMPLY ASSERTION COMPLETENESS. Moving an assertion up
           the hierarchy can make it SILENTLY WEAKER — `typeof f === "function"`
           cannot see that a parameter was deleted, so two arity obligations were
           lost in the conversion and only the negative battery noticed. The rule
           is therefore: prefer the strongest representation available, AND
           separately enumerate every property the old check actually
           established. */
        /* A STATE WHOSE SIGNATURE CROSSES §5's BOUNDARY, built rather than
           typed: nested applications of a free name until the signature is
           long. 30 applications is far past 80 characters and the term needs
           no runtime rules to reach its own signature. */
        const N_APP_PROBE = (() => { let t = "Z"; for (let i = 0; i < 30; i++) t = `(S ${t})`; return t; })();
        let KERNEL = null;
        try { KERNEL = await import(pathToFileURL(A("trvm_law_kernel.mjs")).href); } catch { KERNEL = null; }
        let LOW = null, lowImport = null;
        try { LOW = await import(pathToFileURL(A("lowering.mjs")).href); }
        catch (e) { lowImport = e.message; }
        ok(LOW !== null,
          `lowering.mjs could not be imported, so every DATA and BEHAVIOURAL assertion below is ` +
          `unmeasurable: ${lowImport}. An unimportable module is a failure, never a skip`);
        // a no-op stand-in so one import failure reports once rather than
        // throwing N times and hiding behind its own stack trace
        const L = LOW ?? {};
        // B7 needs the SOURCE evaluator too, to establish that the language
        // still computes what the compiler declines to emit. Imported the same
        // way and with the same rule: an unimportable module is a failure.
        let DERIVE = null, deriveImport = null;
        try { DERIVE = await import(pathToFileURL(A("derive_protocol.mjs")).href); }
        catch (e) { deriveImport = e.message; }
        ok(DERIVE !== null,
          `derive_protocol.mjs could not be imported, so the source side of the B7 codomain ` +
          `assertions is unmeasurable: ${deriveImport}`);
        const D = DERIVE ?? {};
        const lowSrc = existsSync(A("lowering.mjs")) ? readFileSync(A("lowering.mjs"), "utf8") : "";
        // COMMENT-STRIPPED, for assertions about what the CODE says. B1.1
        // wrote two comments containing the literal text `implemented: false`
        // to explain the overbinding bug, and the assertion below then
        // matched THOSE while every real field had been flipped to true.
        // A check reading the prose that documents a defect, instead of the
        // field the defect is in, is the species this file exists to catch.
        const lowNoc = lowSrc.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
        ok(lowSrc !== "", "lowering.mjs absent — three laws cite it");
        // BY CANONICAL, NOT BY REVISION NUMBER. These pinned `revision === 1`
        // and `cl` took the FIRST entry with a matching id, so the assertions
        // below read whichever revision happened to sit earliest in the array
        // — which is how a check keeps testing a superseded statement without
        // saying so. Two of these three were revised at B1.2.1.
        const canonical = (id) => entries.find((x) => x.id === id && x.canonical === true);
        for (const id of ["derivation.canonical-lowering", "derivation.target-decoding",
          "derivation.lowering-refinement"]) {
          const e = canonical(id);
          ok(!!e && e.status === "PROPERTY-TESTED",
            `law ${id} has no canonical PROPERTY-TESTED revision (v1.27)`);
        }
        const cl = canonical("derivation.canonical-lowering");
        ok(!!cl && /THE INSTRUMENT IS RE-LOWERING, NOT A FILM/.test(cl.statement ?? ""),
          "canonical-lowering must rule that lowering gets NO film. A film is evidence for a " +
          "TRANSITION SYSTEM; lowering is a relation, and filming it would invent internal compiler " +
          "steps and make implementation strategy semantic — the mistake the read-order ruling refused");
        // WAS: "must keep the inputs model DEFERRED AND NAMED", requiring only
        // that the words PARAMETERIZED and INSTANTIATED appear. B1 decided the
        // model and B1.1 ruled the framing a FALSE CHOICE, and this assertion
        // went on requiring the deferred wording for three passes — a check
        // that had become a ratchet holding a stale record in place. It now
        // requires the DECISION, and refuses the statement that defers it.
        ok(!!cl && /FALSE CHOICE/.test(cl.statement ?? "") &&
           !/DEFERRED AND NAMED: whether lowering is/.test(cl.statement ?? "") &&
           /LoweringReceipt \{program_sem_id, lowering_sem_id, target_template_sem_id\}/
             .test(cl.statement ?? ""),
          "canonical-lowering must record the inputs model as DECIDED and print the CURRENT " +
          "LoweringReceipt shape. Revision 1 called parameterized-versus-instantiated DEFERRED three " +
          "passes after B1 decided it, and printed the pre-B1.2 receipt ending at target_term_sem_id " +
          "— the domain B1.2 moved onto the template — while this very assertion required the stale " +
          "wording to stay");
        ok(!!cl && (cl.statement ?? "").includes(
             "A RELATION'S IDENTITY MUST COMMIT, BY CONTENT AND NOT BY NAME, TO EXACTLY THE " +
             "ENCODINGS OF ITS OWN DOMAIN AND CODOMAIN"),
          "canonical-lowering must state the B1.2.1 rule: a relation's identity commits BY CONTENT to " +
          "exactly its own domain and codomain encodings, no more and no fewer. Under-binding hides a " +
          "semantic dependency behind a symbol name; over-binding re-identifies a relation when " +
          "something it does not perform changes. Both were present at B1.2, facing opposite ways");
        // ── B1: the model is DECIDED, and `input` is still not built ──────
        // This required `decided: false` until B1. Two levels, two identities,
        // and — separately — two states: "not ruled" and "ruled, not written"
        // are different, and the refusal must be able to say which.
        // B2: DECIDED **AND** IMPLEMENTED. This required `implemented: false`
        // and the presence of lower-input-not-implemented, which was right for
        // three passes and is exactly the shape of assertion that becomes a
        // ratchet once the state it pins is reached — the canonical-lowering
        // "keep it DEFERRED" defect, one file over. `input` lowers now, so the
        // refusal is GONE rather than repointed, and neither of the two dead
        // refusal names may come back.
        // DATA + BEHAVIOURAL. The dead-refusal half stays TEXT-TIER on purpose:
        // "this string appears nowhere" IS a text property.
        // B7: THE LIST WAS PINNED BY EQUALITY AND THAT WAS A RATCHET. It read
        // `join() === "const,add,input"`, so the assertion whose subject is
        // "`input` is built" also silently forbade the fragment from ever
        // growing — and B7 adding `sub` failed it. The subject is MEMBERSHIP,
        // so membership is what it asserts now; the SIZE of the fragment
        // belongs to IMPLEMENTED_LOWERED_OPS and is reported by the checks that
        // derive from it. Pin neither polarity: `input` must be there, and
        // nothing here may say what else may be.
        ok(L.INPUTS_MODEL?.decided === true && L.INPUTS_MODEL?.implemented === true &&
           (L.IMPLEMENTED_LOWERED_OPS ?? []).includes("input") &&
           L.lower?.({ op: "input", name: "x" })?.ok === true &&
           !/lower-input-not-implemented/.test(lowNoc) &&
           !/lower-inputs-undecided/.test(lowNoc),
          "lowering.mjs must record the inputs model as DECIDED and IMPLEMENTED, with `input` in the " +
          "implemented op list and BOTH dead refusal names gone. lower-inputs-undecided could not " +
          "distinguish 'we have not ruled' from 'we have ruled and not written it'; " +
          "lower-input-not-implemented said the second, and at B2 neither is true — a refusal kept " +
          "past the state it describes is a stale instrument with a delay fuse");
        // ── B1.2: the template layer, which B1 presumed and did not have ──
        ok(/export const TARGET_TEMPLATE_ENCODING = Object\.freeze/.test(lowNoc) &&
           /export const TARGET_TEMPLATE_ENCODING_SEM_ID =/.test(lowNoc) &&
           // the profile joined the signature at B6.3 — anchored on the first
           // parameter so the layer is still asserted and the knob is not
           // asserted to be absent
           /export function emit\(template(,|\))/.test(lowNoc) &&
           /export const targetTemplateSemId =/.test(lowNoc),
          "lowering must have a TARGET TEMPLATE layer. B1 ruled that a port lives at the canonical " +
          "target-AST layer BEFORE variable allocation, and lower() emitted an ic32 STRING — so a " +
          "port could only have been a placeholder like $input_x, putting spelling back into " +
          "semantics. The template is that layer and emit() is the allocation step");
        ok(/target_template_sem_id: targetTemplateSemId\(template\)/.test(lowNoc) &&
           /export function loweringReceipt\(program_sem_id, target_template_sem_id\)/.test(lowNoc) &&
           !/lowering_sem_id: LOWERING_SEM_ID, target_term_sem_id/.test(lowNoc),
          "lowering's codomain is the TEMPLATE and the LoweringReceipt must end there. A receipt " +
          "ending in target_term_sem_id keeps asserting that lowering produced the executable term, " +
          "which is exactly what the two-level ruling denies");
        ok(/no_names_no_labels:/.test(lowSrc) &&
           /there is no field it could occupy/i.test(lowSrc),   // case-insensitive: B6.2 capitalised it for emphasis
          "the template encoding must record WHY allocation cannot be semantic: a template has no " +
          "binder names and no dup labels, so I-4a is a property of the data structure rather than a " +
          "convention the emitter is asked to respect");
        // DATA. Was a regex over source text for the exact literal, then an
        // EQUALITY on the whole list — the same ratchet as the line above, and
        // B7 tripped both in one run. What this assertion is about is that the
        // SPECIFIED list and the IMPLEMENTED list agree and that `input` is in
        // them; neither is a place to freeze the fragment's size.
        ok((L.LOWERING_SEMANTICS?.lowered_ops ?? []).includes("input") &&
           [...(L.LOWERING_SEMANTICS?.lowered_ops ?? [])].sort().join() ===
             [...(L.IMPLEMENTED_LOWERED_OPS ?? [])].sort().join(),
          "the hashed lowering semantics must include `input`. B1 left it out, so B2 adding it would " +
          "have moved LOWERING_SEM_ID — implementing a frozen rule re-identifying the relation, " +
          "which is the whole thing B1.1 set out to prevent");
        ok(/input_lowering_rule:/.test(lowSrc) && /carried through UNCHANGED/.test(lowSrc),
          "the `input` lowering rule must be frozen in the SEMANTICS even though the implementation " +
          "is absent — that is what makes 'decided, not built' a checkable state rather than a " +
          "sentence");
        ok(!/"lower-input-not-implemented"/.test(
             lowNoc.slice(lowNoc.indexOf("refusal_semantics"), lowNoc.indexOf("totality:"))),
          "lower-input-not-implemented must NOT be a semantic refusal. It says the code is unwritten, " +
          "not that the language refuses the op, and hashing it makes writing the frozen rule a " +
          "semantic event");
        // ── B7: `sub`, AND THE REFUSAL THAT BELONGS TO THE CODOMAIN ───────
        // The whole risk of this widening is that the refusal drifts to a layer
        // that cannot hold it. Each assertion below pins one layer AGAINST one
        // of the three tempting wrong homes, and all of them are DATA or
        // BEHAVIOURAL rather than text — B2.1.1's hierarchy.
        {
          // 1. IT IS AN ENCODING/EMISSION REFUSAL AND NOT A LOWERING ONE.
          // B7.1r: THE OWNER IS THE MAP, NOT THE CODOMAIN. B7 put this refusal
          // in TARGET_ENCODING.refusals and this assertion required it there,
          // which is the same over-binding one layer up — an assertion pinning
          // a map fact to the codomain's record. It is EMISSION_RULES' now,
          // and the DOMAIN RULE that produces it must be a value too, so the
          // acceptance semantics are content-bound without earning a separate
          // identity (GPT's Q3 ruling).
          const subDomain = L.EMISSION_RULES?.domain?.value_rules?.sub;
          const inMap = (L.EMISSION_RULES?.refusals ?? []).includes("emit-sub-underflow")
            && subDomain?.refusal === "emit-sub-underflow" && subDomain?.require === "a>=b"
            && (L.EMISSION_SEMANTICS?.semantic_refusals ?? []).includes("emit-sub-underflow")
            && L.EMISSION_SEMANTICS?.rules_sem_id === L.EMISSION_RULES_SEM_ID;
          const notLowering = !(L.LOWERING_SEMANTICS?.refusal_semantics ?? [])
            .some((r) => /sub-underflow|negative-sub|lower-negative-/.test(r));
          // 2. AND IT IS NOT A LOWERING PRECONDITION EITHER, which is the form
          //    it would take if someone tried to catch it one layer early. It
          //    CANNOT be one: sub(input x, input y) has no underflow fact until
          //    an invocation binds the ports.
          const subRule = L.LOWERING_SEMANTICS?.op_lowering_rules?.sub;
          const noPrecondition = !L.IMPLEMENTED_LOWERED_OPS?.includes("sub")
            || (subRule && Array.isArray(subRule.preconditions) && subRule.preconditions.length === 0);
          ok(!L.IMPLEMENTED_LOWERED_OPS?.includes("sub") || (inMap && notLowering && noPrecondition),
            "once `sub` is lowered, emit-sub-underflow must be a refusal of the EMISSION MAP — in " +
            "EMISSION_RULES.refusals AND as the named refusal of its own domain rule, with " +
            "EMISSION_SEMANTICS citing EMISSION_RULES_SEM_ID — must not appear in lowering's refusal " +
            "vocabulary under any spelling, " +
            "and op_lowering_rules.sub must carry NO precondition. A lowering precondition cannot " +
            "even be written: sub(input x, input y) has no underflow fact until an invocation binds " +
            "the ports, so one template emits under {x:5,y:2} and refuses under {x:2,y:5}");

          // 3. BEHAVIOURAL, AND EVERY PROBE IS WRAPPED. This rung RUNS
          //    ADVERSARY-INFLUENCED CODE — B2.1.2's finding, which cost a
          //    forgery that made grid_check exit with a stack trace instead of
          //    a diagnostic. The first draft of THIS block repeated it: under
          //    the sub-refusal-moved-to-lowering forgery, lower() refuses, so
          //    `good.closed_template` is undefined and the unwrapped emit()
          //    below threw template-malformed out of grid_check entirely. Two
          //    rounds apart, same species, and the case written to catch the
          //    forgery caught the instrument instead.
          const compile = (P, inputs = {}, profile = undefined) => {
            try {
              const low = L.lower?.(P);
              if (!low?.ok) return { stage: "lower", reason: String(low?.reason ?? "no-result").split(":")[0] };
              const inst = L.instantiate?.(low.template, inputs);
              if (!inst?.ok) return { stage: "instantiate", reason: String(inst?.reason ?? "no-result").split(":")[0], low };
              const bytes = profile === undefined ? L.emit(inst.closed_template)
                                                  : L.emit(inst.closed_template, profile);
              return { stage: "emit", ok: true, bytes, low, inst };
            } catch (e) { return { stage: "emit", reason: String(e?.message ?? e).split(":")[0] }; }
          };
          const srcValue = (P, inputs = {}) => {
            try { return D.evaluate?.(P, { exact: {}, predicates: {} }, inputs)?.value; }
            catch { return null; }
          };
          if (L.IMPLEMENTED_LOWERED_OPS?.includes("sub")) {
            const C0 = (v) => ({ op: "const", value: v });
            const SUBP = (a, b) => ({ op: "sub", a, b });
            const P23 = SUBP(C0(2), C0(3));
            const r23 = compile(P23);
            ok(r23.stage === "emit" && !r23.ok && r23.reason === "emit-sub-underflow" && srcValue(P23) === -1,
              "sub(2,3) must LOWER, INSTANTIATE, and then be refused at EMISSION as " +
              "emit-sub-underflow while the SOURCE evaluator still returns -1. All four halves " +
              "matter: refusing earlier would make it a source or lowering fact, saturating would " +
              "answer 0 for a program whose value is -1, and a core that stopped returning -1 would " +
              "have changed the language to suit the compiler and moved CORE_SEM_ID");

            // 3b. THE NESTED FALSIFIER, AND IT IS THE ONE THAT MATTERS. The
            //     first draft of this block checked sub(2,3) alone, and a
            //     forgery reducing the walk to a ROOT-ONLY check passed
            //     grid_check clean: (2-3)+2 has root value 1, which is
            //     perfectly emittable, and the inner monus then answers 2. An
            //     underflow leaves NO trace in the outcome, so a check on the
            //     result cannot see it and neither could this assertion.
            const NESTED = { op: "add", a: SUBP(C0(2), C0(3)), b: C0(2) };
            const rn = compile(NESTED);
            ok(rn.stage === "emit" && !rn.ok && rn.reason === "emit-sub-underflow" && srcValue(NESTED) === 1,
              "(2-3)+2 must be refused at EMISSION even though its ROOT value is 1 and 1 is " +
              "emittable. The representability walk is RECURSIVE for exactly this reason: a " +
              "root-only check accepts this program, raw Church monus then answers 2 against the " +
              "source's 1, and nothing downstream can tell — which is why the check may not be a " +
              "test on the RESULT");

            // 4. THE REFUSAL DOES NOT DEPEND ON THE PROFILE. Emission takes a
            //    profile since B6.3, so which templates are emittable COULD have
            //    become configurable by accident. Run it under a profile that is
            //    fatal to a good template and check the domain refusal still wins.
            const broken = { ...(L.CANONICAL_EMITTER_PROFILE ?? {}), binder_names: null };
            const P52 = SUBP(C0(5), C0(2));
            const underBroken = compile(P23, {}, broken);
            const goodUnderBroken = compile(P52, {}, broken);
            ok(underBroken.reason === "emit-sub-underflow"
               && goodUnderBroken.ok !== true && goodUnderBroken.reason !== "emit-sub-underflow",
              "the domain refusal must be decided BEFORE the serialization profile is read, so no " +
              "profile can turn it into an acceptance or into a different refusal. NON-VACUOUS: the " +
              "same broken profile handed a REPRESENTABLE template must fail with a profile error " +
              `(it answered ${goodUnderBroken.reason ?? "EMITTED"}), or the invariance above would ` +
              "be the profile being harmless rather than the order of the checks");

            // 5. EMISSION MUST NOT FOLD. The representability walk computes the
            //    value a constant folder would return; one line from there and
            //    the compiler stops compiling while every integration theorem
            //    still passes. So the BYTES are checked, not the answer.
            const good = compile(P52);
            const church3 = (() => { try { return L.emit({ t: "church", n: 3 }); } catch { return null; } })();
            ok(good.ok === true && church3 !== null
               && good.bytes !== church3 && good.bytes.length > church3.length,
              "emit(sub(5,2)) must not be emit(church(3)). The representability walk computes exactly " +
              "the value a folder would return and discards it; folding would make the refinement " +
              "theorem a statement about the compiler's own arithmetic rather than about the runtime");
          }

          // 6. AND THE OPEN ITEM MUST STAY OPEN. emit-sub-underflow is not
          //    source-refusal to target-refusal preservation and may not be
          //    recorded as progress on it — for sub(2,3) the source does not
          //    refuse at all.
          ok(/^SOURCE-REFUSAL <-> INSTANTIATION-REFUSAL/.test(L.REFINEMENT_SCOPE?.declared_open ?? "")
             && /NOT REFUSAL PRESERVATION|THIS IS NOT REFUSAL PRESERVATION/i
                  .test(L.REFINEMENT_SCOPE?.representable_only ?? ""),
            "REFINEMENT_SCOPE must keep source-refusal to instantiation-refusal DECLARED OPEN and " +
            "must state separately that the representability boundary is NOT that item. Conflating " +
            "them would book a refusal the source never makes as evidence for a theorem about " +
            "refusals the source does make");
        }

        // ── B8.2: THE READBACK FOLD USES RECORDED ALLOCATION ORDER ────────
        // Found by mul(4,3) and mul(3,1) and by no fixture before them.
        // foldLive nested live dups by ASCENDING HEAP ID and called that
        // allocation order — true only because FloatRt's ids ascend. DescFloatRt
        // allocates DESCENDING ids precisely so that nothing may depend on that,
        // and under it the last-allocated dup was nested OUTSIDE the binder its
        // own value mentions, so readback chased substitutions it could not
        // resolve and ran out of budget.
        //
        // A dup's value can only mention names that already existed when it was
        // allocated, so ALLOCATION ORDER is a valid topological order on that
        // dependency and nothing else is guaranteed to be — an intermediate
        // repair using the discovery order fixed DescFloatRt and broke
        // (2+3)*4 under FloatRt, which is how the general claim was measured
        // rather than argued. The order is a RECORDED STAMP now.
        {
          const K = KERNEL ?? {};
          const probe = (f) => { try { return f(); } catch (e) { return "THREW:" + String(e.message ?? e); } };
          // BEHAVIOURAL, on the shape that exposed it: a left operand of
          // church(3) or more is the first whose CHAINED dups depend on
          // each other, so every earlier fixture's dups were independent and
          // any nesting worked.
          const nfUnder = (Cls, bytes) => probe(() => {
            const frt = new Cls();
            let root = K.extrude(frt, K.parse(frt, bytes));
            root = K.normalizeFloat(frt, root, (rs) => rs[0], null, { budget: 500000 }).root;
            return K.semId(K.readback(frt, root, 500000).str);
          });
          // TWO SHAPES, because the two wrong orders fail on DIFFERENT ONES and
          // the first draft of this assertion tested only the first. CHAINED
          // dups (a church(3+) left operand) break under ID order in the
          // descending class; a NESTED combinator whose operand is itself an
          // operator breaks under DISCOVERY order in the ascending one. An
          // assertion carrying one of them passes the other's forgery.
          const hasMul = L.IMPLEMENTED_LOWERED_OPS?.includes("mul");
          const chained = hasMul
            ? probe(() => L.emit(L.T.mul(L.T.church(4), L.T.church(3))))
            : probe(() => L.emit(L.T.add(L.T.church(4), L.T.church(3))));
          const nested = hasMul
            ? probe(() => L.emit(L.T.mul(L.T.add(L.T.church(2), L.T.church(3)), L.T.church(4))))
            : probe(() => L.emit(L.T.add(L.T.add(L.T.church(2), L.T.church(3)), L.T.church(4))));
          const rows = [chained, nested].map((b) => ({
            asc: nfUnder(K.FloatRt, b), desc: nfUnder(K.DescFloatRt, b) }));
          const agree = rows.every((r) => typeof r.asc === "string" && r.asc.startsWith("sem-")
            && r.asc === r.desc);
          // AND THE ADVERSARY MUST STILL BE ADVERSARIAL. A DescFloatRt that
          // allocated ascending ids would agree with FloatRt about everything
          // and prove nothing — a green check with no content, which is the
          // instrument-vacuity species this tree has an explicit law for.
          const descIds = probe(() => {
            const frt = new K.DescFloatRt();
            K.extrude(frt, K.parse(frt, chained));
            return [...frt.heap.keys()];
          });
          const stillDescends = Array.isArray(descIds) && descIds.length >= 2
            && descIds.some((v, i) => i > 0 && v < descIds[i - 1]);
          // and the STAMP must exist, or the fold is back to inferring order
          // from a representative choice
          const stamped = probe(() => {
            const frt = new K.FloatRt();
            K.extrude(frt, K.parse(frt, chained));
            return [...frt.heap.values()].every((d) => Number.isInteger(d.seq));
          });
          // AND THE DOMAIN ARITHMETIC IS A CLOSED VOCABULARY, RUN rather than
          // narrated: representableValue takes the rules as a PARAMETER since
          // B8.2, for B6.2's reason — a module-level frozen constant cannot be
          // varied by the battery meant to falsify it.
          const unknownOp = probe(() => {
            const bad = { ...L.EMISSION_RULES,
              domain: { ...L.EMISSION_RULES.domain,
                value_rules: { ...L.EMISSION_RULES.domain.value_rules, add: { operator: "%" } } } };
            L.representableValue(L.T.add(L.T.church(2), L.T.church(3)), bad);
            return "ACCEPTED";
          });
          const namedOperatorRefusal = String(unknownOp).startsWith("THREW:emission-rule-unknown-operator");
          // EVERY LOWERED OP MUST HAVE AN EMISSION RULE FOR THE TAG IT PRODUCES.
          // Derived from the two records rather than listed: a lowering rule
          // whose target tag has no node_rule produces a template nothing can
          // emit, and the program would lower and instantiate cleanly and then
          // die as template-malformed — a fragment claiming an op it cannot
          // finish.
          const tagsNeeded = (L.IMPLEMENTED_LOWERED_OPS ?? [])
            .map((op) => L.LOWERING_SEMANTICS?.op_lowering_rules?.[op]?.target?.t)
            .filter((t) => typeof t === "string");
          const tagsMissing = tagsNeeded.filter((t) => (L.EMISSION_RULES?.node_rules ?? {})[t] === undefined);
          ok(tagsNeeded.length >= 4 && tagsMissing.length === 0,
            `every implemented lowered op must have an EMISSION rule for the template tag it ` +
            `produces. ${tagsNeeded.length} tags derived from op_lowering_rules over ` +
            `[${(L.IMPLEMENTED_LOWERED_OPS ?? []).join(", ")}], ${tagsMissing.length} without a ` +
            `node_rule${tagsMissing.length ? ": " + tagsMissing.join(", ") : ""}. Without this a ` +
            `program lowers and instantiates cleanly and then dies as template-malformed — a ` +
            `fragment claiming an operator it cannot finish`);
          ok(agree && stamped === true && stillDescends && namedOperatorRefusal,
            "readback must fold live dups in RECORDED ALLOCATION ORDER, so the two runtime classes " +
            "reach the same normal form. Sorting by heap ID is allocation order only while ids " +
            "ascend, and DescFloatRt's descend on purpose — under it the last-allocated dup was " +
            "nested outside the binder its own value mentions and readback ran out of budget on a " +
            "term whose left operand has CHAINED dups. Every heap entry must carry a monotone " +
            "allocation stamp and the fold must read it. TWO SHAPES ARE CHECKED, because a " +
            "discovery order fixes the chained case and breaks a NESTED combinator under the " +
            "ascending class — an assertion carrying one shape passes the other's forgery. AND THE " +
            "ADVERSARY MUST STILL ADVERSE: DescFloatRt's ids must not ascend " +
            `(${stillDescends}), or it agrees with FloatRt about everything and proves nothing. AND ` +
            "an unknown domain OPERATOR must be a NAMED refusal " +
            `(${namedOperatorRefusal}), run against a mutated rules object rather than narrated`);
        }

        // ── B8.3: THE ALLOCATION STAMP IS REQUIRED EVIDENCE, NOT PREFERRED ─
        // B8.2 repaired the fold and left the sort reading
        //     (heap.get(a)?.seq ?? a) - (heap.get(b)?.seq ?? b)
        // so a missing stamp quietly RESUMED the inference the repair had just
        // declared invalid — allocation order guessed off the id integer.
        //
        // MEASURED before it was removed, on two runtimes with the stamp
        // stripped: under ASCENDING ids readback SILENTLY SUCCEEDED (the guess
        // happened to be right), and under DESCENDING ids it threw `budget`. So
        // the fallback did not merely permit a wrong order — it reported a
        // MISSING INVARIANT AS A RESOURCE LIMIT, which blames the term for being
        // long when the runtime is what failed to record what readback needs.
        //
        // Both halves are checked BEHAVIOURALLY, by stripping the stamp off a
        // subclass of each shipped class and requiring the NAMED refusal, so
        // this cannot be satisfied by a comment.
        {
          const K = KERNEL ?? {};
          const probe = (f) => { try { return f(); } catch (e) { return "THREW:" + String(e.message ?? e); } };
          const bytes = probe(() => L.emit(L.T.mul(L.T.church(4), L.T.church(3))));
          const readUnder = (Cls) => probe(() => {
            const frt = new Cls();
            let root = K.extrude(frt, K.parse(frt, bytes));
            root = K.normalizeFloat(frt, root, (rs) => rs[0], null, { budget: 500000 }).root;
            return K.readback(frt, root, 500000).str.slice(0, 12);
          });
          const strip = (Base) => class extends Base {
            allocAt(id, lab, l, r, val) { this.heap.set(id, { lab, l, r, val }); return id; }
          };
          const dup = (Base) => class extends Base {
            allocAt(id, lab, l, r, val) { this.heap.set(id, { lab, l, r, val, seq: 1 }); return id; }
          };
          const missingAsc = readUnder(strip(K.FloatRt));
          const missingDesc = readUnder(strip(K.DescFloatRt));
          const duplicated = readUnder(dup(K.FloatRt));
          const named = (r, code) => String(r) === "THREW:" + code;
          // AND THE FAIL-CLOSED CONDITION MUST NOT BE ABSORBED BY THE CATCHES
          // THAT EXIST FOR A BUDGET. sealSemFilm and replaySemFilm both wrap
          // readback in a try; swallowing this would seal a NORMAL_FORM film
          // with no normal-form id and call that honest.
          const sealSwallows = probe(() => {
            const Cls = strip(K.FloatRt), frt = new Cls();
            let root = K.extrude(frt, K.parse(frt, bytes));
            root = K.normalizeFloat(frt, root, (rs) => rs[0], null, { budget: 500000 }).root;
            K.sealSemFilm(K.newSemFilm(), frt, root,
              { termination: "NORMAL_FORM", steps: 0, last_frame: "genesis", planes: [...K.PLANE_POOL_FREE] });
            return "SEALED";
          });
          const audit = K.HEAP_ID_ORDER_AUDIT;
          ok(named(missingAsc, "readback-allocation-order-missing")
             && named(missingDesc, "readback-allocation-order-missing")
             && named(duplicated, "readback-allocation-order-duplicate")
             && named(sealSwallows, "readback-allocation-order-missing")
             && typeof readUnder(K.FloatRt) === "string" && !String(readUnder(K.FloatRt)).startsWith("THREW:"),
            "a MISSING or DUPLICATE allocation stamp must be a NAMED FAIL-CLOSED condition in " +
            "readback, never a fallback to the heap-ID integer. B8.2's repair kept `seq ?? id`, which " +
            "under a missing stamp resumed the exact inference it had just declared invalid — and " +
            "MEASURED, that fallback silently SUCCEEDED under ascending ids and threw `budget` under " +
            "descending ones, so a broken invariant was reported as a term that ran out of room. " +
            `Stripped-stamp subclasses of both shipped classes must refuse by name (asc ${missingAsc}, ` +
            `desc ${missingDesc}), a duplicate stamp likewise (${duplicated}), the unstripped class ` +
            "must still read back, AND sealSemFilm must RETHROW rather than absorb it into a " +
            `normal-form id of null (${sealSwallows}) — the catch there is for a BUDGET, and a ` +
            "runtime that did not record what the fold requires is not a term that is too long");

          // ── B8.3: THE HEAP-ID ORDER CENSUS IS COMPLETE ────────────────────
          // GPT asked for a mechanical inspection recorded as a finite audit and
          // explicitly NOT for a general linter. So the classification is
          // HAND-WRITTEN — four kinds, one per site, with the reason — and the
          // only thing derived is the DENOMINATOR: the number of places in the
          // kernel's own source where an order over heap entries is CHOSEN.
          // That is the part that goes stale silently, and going stale silently
          // is exactly how B8.2's site sat unclassified through eight passes.
          const srcRaw = readFileSync(join(ROOT, "trvm_law_kernel.mjs"), "utf8");
          /* THE CENSUS'S FIRST RUN WAS ANSWERED BY ITS OWN DESCRIPTION OF
             ITSELF. HEAP_ID_ORDER_AUDIT.checked_against contains the literal
             `.sort(` while explaining what is counted, so the derived
             denominator came back 3 against 2 declared and the case failed —
             correctly, and for the wrong reason. Seventh coincidental second
             occurrence of a search text in this line.
             THE CURE IS THIS TREE'S OWN: cut the region by its DECLARATIONS,
             not by a line range and not by rewording the prose so this one
             instance stops matching. The audit is a frozen data record with no
             code in it, so nothing countable is lost by excising it. */
          const AUDIT_FROM = "const HEAP_ID_ORDER_AUDIT = Object.freeze({";
          const AUDIT_TO = "const HEAP_ID_ORDER_AUDIT_ID =";
          const aFrom = srcRaw.indexOf(AUDIT_FROM), aTo = srcRaw.indexOf(AUDIT_TO);
          const excised = aFrom > 0 && aTo > aFrom;
          const src = excised ? srcRaw.slice(0, aFrom) + srcRaw.slice(aTo) : srcRaw;
          const marker = src.indexOf("if (IS_MAIN) {");
          const live = src.slice(0, marker), battery = src.slice(marker);
          const sortsIn = (t) => (t.match(/\.sort\(/g) ?? []).length;
          const declaredLive = (audit?.live_sites ?? []).filter((e) => e.sorts).length;
          const declaredBattery = (audit?.battery_sites ?? []).filter((e) => e.sorts).length;
          const kinds = new Set((audit?.live_sites ?? []).map((e) => e.kind));
          ok(marker > 0 && excised && audit?.audit === "TRVM-HEAPID-ORDER-AUDIT-v1"
             && sortsIn(live) === declaredLive && sortsIn(battery) === declaredBattery
             && declaredLive === 2 && declaredBattery === 1
             && (audit.live_sites ?? []).length >= 7
             && (audit.live_sites ?? []).every((e) => typeof e.why === "string" && e.why.length > 40)
             && kinds.has("EXECUTION") && kinds.has("SEMANTIC") && kinds.has("DEPENDENCY")
             && kinds.has("ORDER-FREE")
             && typeof K.HEAP_ID_ORDER_AUDIT_ID === "string"
             && K.HEAP_ID_ORDER_AUDIT_ID.startsWith("hida-"),
            `the heap-id order census must stay COMPLETE over the sites where an order is chosen. ` +
            `${sortsIn(live)} sorting sites in the kernel's live half and ${sortsIn(battery)} in its ` +
            `battery half, against ${declaredLive} and ${declaredBattery} declared — DERIVED FROM THE ` +
            `SOURCE, because a census whose denominator is typed cannot notice a new site, and an ` +
            `unnoticed site is precisely what B8.2's defect was — and on its FIRST RUN this count ` +
            `came back 3 against 2, because the audit's own prose explains what is counted by ` +
            `NAMING it, so the census was answered by its own description of itself (${excised} — the ` +
            `record is excised by its DECLARATIONS, not by rewording the sentence that matched). ` +
            `${(audit?.live_sites ?? []).length} ` +
            `live sites classified across ${[...kinds].sort().join("/")}, each with a stated reason. ` +
            `The battery site sorts ids ON PURPOSE — it is the pre-fix enumeration kept verbatim so ` +
            `the round-5 dead-locus defect keeps reproducing — and listing it separately is what ` +
            `stops a later sweep from "repairing" the defect it exists to exhibit`);
        }

        // ── B8.1: THE DECODER READS THE OBJECT, NOT THE OBJECT'S IDENTITY ─
        // The defect this guards against is the one B8.1 fixed and the one it
        // must not reintroduce: a decoder whose DOMAIN is a serialization built
        // for identification inherits that serialization's lossiness, and §5
        // makes the canonical signature deliberately lossy above 80 characters.
        // The ceiling was the decoder's, so the fix is the decoder's — and the
        // compaction bound is NOT to be moved, because it is frozen into
        // SEMSTATE-CANONICAL-v1, the golden pre-hash vectors, the 48/48 bridge
        // agreement and every native film.
        {
          const spec = L.DECODER_SPEC ?? {};
          // DATA: the spec must name the OBJECT and must not mention the
          // retired refusal ANYWHERE, including in a note about having retired
          // it — a refusal that can never fire is a stale instrument, and a
          // spec that still lists it is a reader's licence to look for it.
          const readsObject = /OWNED target normal-form semantic object/.test(spec.reads ?? "")
            && !JSON.stringify(spec).includes("decode-signature-compacted")
            && (spec.refusals ?? []).includes("decode-not-a-church-numeral");
          // DATA: the supersession is recorded, and the id genuinely moved.
          const sup = L.SUPERSEDED_SIGNATURE_DECODER_SEM_ID ?? {};
          const superseded = typeof sup.decode_sem_id_b7 === "string"
            && sup.decode_sem_id_b7.startsWith("dsem-")
            && sup.decode_sem_id_b7 !== L.DECODE_SEM_ID;
          // BEHAVIOURAL, and WRAPPED — this rung runs adversary-influenced code.
          const probe = (f, fallback = null) => { try { return f(); } catch (e) { return fallback ?? String(e.message ?? e); } };
          const Lam = (nam, bod) => ({ t: "Lam", nam, bod });
          const V = (nam) => ({ t: "Var", nam });
          const num = (n) => { let b = V(2); for (let i = 0; i < n; i++) b = { t: "App", fun: V(1), arg: b }; return Lam(1, Lam(2, b)); };
          // THE CEILING IS GONE. 12 is the first value the signature decoder
          // could not read, and it is what mul(4,3) produces.
          const twelve = probe(() => L.decodeNormalFormOwned?.(num(12)));
          const twenty = probe(() => L.decodeNormalFormOwned?.(num(20)));
          const past = twelve?.ok === true && twelve.outcome?.value === 12
            && twenty?.ok === true && twenty.outcome?.value === 20;
          // ALPHA-INVARIANCE BY RECOGNITION: different binder identities, same
          // shape, same answer — the decoder never reads a name.
          const renamed = probe(() => L.decodeNormalFormOwned?.(
            { t: "Lam", nam: 71, bod: { t: "Lam", nam: 72, bod: { t: "App", fun: V(71), arg: V(72) } } }));
          const alphaOk = renamed?.ok === true && renamed.outcome?.value === 1;
          // ONE SNAPSHOT, TWO CONSUMERS: the parametric decoder must REFUSE to
          // run without an identity oracle, so a caller cannot decode an object
          // whose identity nobody computed.
          const noOracle = probe(() => { L.decodeOwnedAgainst?.(num(1)); return "BUILT"; });
          ok(readsObject && superseded && past && alphaOk && noOracle === "decode-oracle-required",
            "the decoder must read the OWNED normal-form OBJECT and not its canonical signature. A " +
            "signature is an identity serialization that §5 replaces with a hash above 80 " +
            "characters, so a decoder reading one inherits a ceiling the runtime does not have — " +
            "measured at Church 11 (76 chars, decodes) against Church 12 (82 chars, compacted), " +
            "where 12 is exactly what mul(4,3) produces. Church 12 and 20 must decode, recognition " +
            "must be by BINDING IDENTITY rather than by name, the parametric decoder must refuse " +
            "without an identity oracle, and decode-signature-compacted must be GONE from the spec rather " +
            "than repointed");

          // AND THE COMPACTION BOUND ITSELF IS NOT TO MOVE. This is the thing
          // the decoder fix exists to avoid touching: 80 is frozen into
          // SEMSTATE-CANONICAL-v1, the golden pre-hash vectors, the bridge
          // agreement, every semantic state id and every native film. Pinned by
          // BEHAVIOUR — build a state whose signature crosses the boundary and
          // require compaction — rather than by grepping for the literal, so an
          // override or a second code path cannot satisfy it.
          const K = KERNEL ?? {};
          const sigLenOf = probe(() => {
            const frt = new K.FloatRt();
            return K.semStateSignature(frt, K.extrude(frt, K.parse(frt, N_APP_PROBE)));
          }, null);
          // §5 COMPACTION IS INTERNAL, not whole-signature: an inner node whose
          // own signature exceeds the bound is replaced by its full-width hash,
          // so the ROOT can stay short and readable while a subtree is elided.
          // The first draft of this assertion required the whole signature to
          // start with "#" and failed on a 30-deep term whose root signature is
          // A(Ffree:S,#…) at 76 characters — the check was wrong about the
          // mechanism it was pinning, which is the only kind of wrong worth
          // finding here.
          const compactedAt = typeof sigLenOf === "string" && /#[0-9a-f]{64}/.test(sigLenOf);
          const shortSig = probe(() => {
            const frt = new K.FloatRt();
            return K.semStateSignature(frt, K.extrude(frt, K.parse(frt, "(S Z)")));
          }, null);
          ok(compactedAt && typeof shortSig === "string" && !shortSig.includes("#")
             && shortSig.length <= 80,
            "§5's 80-character compaction must still fire. B8.1 fixed a DECODER ceiling and " +
            "deliberately did not move this bound: it is frozen into SEMSTATE-CANONICAL-v1, the " +
            "golden pre-hash vectors, the 48/48 bridge agreement, every semantic state id and every " +
            "native film, and raising it because the decoder chose the wrong input representation " +
            "would re-cut all of that for no semantic reason. Checked by BEHAVIOUR on a deep state " +
            "and a shallow one, not by grepping for the literal 80 — and the elision is a FULL-WIDTH " +
            "sha256, because a truncated inner node would undercut the outer commitment");

          // ── B8.3: THE DECODER'S TRUST BOUNDARY ──────────────────────────
          // B2.1.2 found emission's verdict was RELATIVE and spelled ABSOLUTE.
          // B8.1's decoder reproduced the shape one relation downstream, at the
          // OUTPUT end of the chain: a caller passing its own oracle got back
          // ok:true carrying the id it had nominated. Correct decoding, and an
          // identity claim that is the caller's own.
          //
          // Reproduced BEHAVIOURALLY, and the bound decoder's arity is read off
          // the FUNCTION OBJECT — B2.1.1's cost was that `typeof f ===
          // "function"` cannot see a missing parameter, and a stronger
          // representation is not automatically a stronger assertion.
          const zeroNf = probe(() => {
            const frt = new K.FloatRt();
            let r = K.extrude(frt, K.parse(frt, L.emit(L.T.church(0))));
            r = K.normalizeFloat(frt, r, (rs) => rs[0], null, { budget: 500000 }).root;
            return K.readback(frt, r, 500000).nf;
          }, null);
          const complicit = probe(() => L.decodeOwnedAgainst?.(zeroNf, () => "nf-DEADBEEF"));
          const boundDec = probe(() => L.makeTargetDecoder?.(
            { identifyNormalForm: (o) => K.semStateId(new K.FloatRt(), o) }));
          const boundOut = typeof boundDec === "function" ? probe(() => boundDec(zeroNf)) : null;
          const unbindable = probe(() => { L.makeTargetDecoder?.({}); return "BOUND"; });
          ok(complicit?.ok === true && complicit.outcome?.value === 0
             && complicit.target_nf_sem_id === "nf-DEADBEEF"
             && typeof boundDec === "function" && boundDec.length === 1
             && boundOut?.ok === true && boundOut.outcome?.value === 0
             && boundOut.target_nf_sem_id !== "nf-DEADBEEF"
             // this block's `probe` returns the bare message; the B8.2 block's
             // prefixes "THREW:". Two conventions for one helper name in one
             // file, and the first draft of this clause used the other one.
             && String(unbindable) === "target-decoder-no-oracle"
             && L.decodeOwned === undefined
             && typeof L.decodeOwnedAgainst === "function" && L.decodeOwnedAgainst.length === 2
             && L.DECODE_SEM_ID === L.DECODE_SEM_ID_UNMOVED_AT_B83?.id,
            "the decoder's identity oracle must be BOUND AT A COMPOSITION ROOT, not chosen by the " +
            "caller of an absolutely-spelled verdict. The parametric entry point returns ok:true, " +
            `value 0 and target_nf_sem_id "${complicit?.target_nf_sem_id}" against an oracle a caller ` +
            "invented — B2.1.2's finding at the OUTPUT end of the chain instead of the input end. So " +
            "`Against` is in the name, makeTargetDecoder binds the trusted oracle once, the bound " +
            `decoder takes ${typeof boundDec === "function" ? boundDec.length : "?"} argument and has ` +
            "NO PARAMETER FOR A JUDGE (read off the function object, because typeof cannot see a " +
            `missing parameter), an unbindable root refuses by name (${unbindable}), and NO ALIAS ` +
            "survives for the old spelling. AND DECODE_SEM_ID MUST NOT MOVE FOR ANY OF IT: who " +
            "nominates the judge is a COMPOSITION fact and not an encoding one, so the id is " +
            "asserted EQUAL to the value B8.1 minted, which is declared in the module beside its " +
            "reason rather than typed into this checker");

          // ── B8.3+: THE PROOF CHECKER MUST BE INDEPENDENT OF ITS GENERATOR ─
          // The first bounded proof bundle's whole value is that a checker
          // trusting none of the generator can accept or refuse it. Two ways
          // that dissolves quietly, and both are checked on the SOURCE because
          // neither is visible in a passing run:
          //
          //   the checker IMPORTS the generator's `cartesian`, and "the cases
          //   cover the domain" becomes a tautology about one function;
          //
          //   the checker READS `bounded_claim_verdict` instead of computing
          //   one, and the aggregate certifies itself — the defect B2 removed
          //   from instantiate() and B2.1.1 from the verifiers, in the one
          //   place where the whole chain's output is summarised.
          const pcSrc = existsSync(A("proof_check.mjs"))
            ? readFileSync(A("proof_check.mjs"), "utf8") : "";
          const pbSrc = existsSync(A("proof_bundle.mjs"))
            ? readFileSync(A("proof_bundle.mjs"), "utf8") : "";
          const pcNoc = pcSrc.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
          // the import list from the generator, DERIVED from the source rather
          // than assumed: the checker may share the protocol's HASH functions —
          // they are the format — but not its enumeration of the domain.
          const gm = pcNoc.match(/import\s*\{([^}]*)\}\s*from\s*"\.\/proof_bundle\.mjs"/);
          const imported = gm ? gm[1].split(",").map((x) => x.trim()).filter(Boolean) : [];
          // BOUNDED_CLAIM_SCOPE joins the ban at P1.1: a checker that imports
          // the scope it is supposed to REQUIRE compares the bundle's claim to
          // the bundle's own idea of that claim. The forgery that swaps the
          // literal for the import passed the first draft of this case, because
          // `impl[k] === scope[k]` is trivially true when impl IS scope.
          const BANNED_IMPORTS = ["cartesian", "PROPOSITION", "VARIABLE_DOMAINS", "buildBundle",
            "buildSide", "BOUNDED_CLAIM_SCOPE", "BOUNDED_CLAIM_SCOPE_NOTES"];
          const leaked = imported.filter((n) => BANNED_IMPORTS.includes(n));
          // ANCHORED ON THE CALL SHAPE, not the name. This was
          // /function productByIndex/ and its own forgery renames the function
          // to productByIndexUnused -- which that regex MATCHES AS A PREFIX, so
          // the case reported the forgery uncaught. Eighth time in this line
          // that an assertion has been answered by a coincidental occurrence of
          // its own search text, and B6.2's convention -- match the DECLARATION
          // -- had to be applied to a function name as well as to a const.
          const derivesOwn = /function productByIndex\(variables, domains\)/.test(pcNoc)
            && /const derived = productByIndex\(variables, domains\);/.test(pcNoc);
          // AND THE SCOPE IS IN THE ARTIFACT, not only in a ledger sentence.
          // A bundle whose claim reads as unbounded is a different claim.
          // READ AS DATA, NOT AS TEXT. The first draft grepped this file's
          // SOURCE for the scope sentence, which is written as two
          // concatenated fragments and therefore matched nothing — the check
          // failed correctly and for entirely the wrong reason, which is the
          // raw-text rung of B2.1.1's hierarchy behaving exactly as that
          // ruling says it does. The scope is an exported frozen record now.
          let PB = null, PC = null;
          try { PB = await import(pathToFileURL(A("proof_bundle.mjs")).href); } catch { /* stays null */ }
          try { PC = await import(pathToFileURL(A("proof_check.mjs")).href); } catch { /* stays null */ }
          /* P1.1: THE SCOPE MUST BE STRUCTURAL AND THE CHECKER MUST READ IT.
             P1 shipped scope as prose and proof_check.mjs read none of it:
             deleting claim.scope, and rewriting it to an unbounded all-naturals
             claim, BOTH left checkBundle at ok:true with zero refusals. The
             evidence established a bounded fact and nothing connected that fact
             to the sentence beside it.
             Three requirements, and the third is what makes the first two
             load-bearing: the scope is machine-readable VALUES (B6.3's rule —
             no hashed field holds prose, checked structurally by requiring no
             whitespace rather than by promising to keep sentences out); a
             bounded-claim identity binds proposition, domain and quantifier
             semantics so they stop being adjacent unauthenticated pieces; and
             the CHECKER declares the scope IT implements rather than importing
             the generator's, because comparing a bundle's claim to the bundle's
             own idea of that claim is the tautology productByIndex exists to
             avoid one field over. */
          const scope = PB?.BOUNDED_CLAIM_SCOPE;
          const notes = PB?.BOUNDED_CLAIM_SCOPE_NOTES;
          const impl = PC?.IMPLEMENTED_SCOPE;
          const scopeStated = scope?.kind === "BOUNDED_EXHAUSTIVE_VERIFICATION"
            && scope.quantifier === "FOR_ALL_ASSIGNMENTS_IN_DECLARED_DOMAINS"
            && scope.generalizes_beyond_domain === false
            // no prose in the hashed seat, and the prose that exists is elsewhere
            && Object.values(scope).every((v) => typeof v !== "string" || !/\s/.test(v))
            && Array.isArray(notes?.not_claimed) && notes.not_claimed.length >= 4
            && notes.not_claimed.some((x) => /NOT a proof of distributivity over the naturals/.test(x))
            && notes.not_claimed.some((x) => /nothing here generalises past 3/.test(x))
            // and the checker requires exactly that, from its OWN declaration
            && impl && Object.keys(impl).length === Object.keys(scope).length
            && Object.keys(impl).every((k) => impl[k] === scope[k])
            && /refuse\("proof-scope-mismatch"/.test(pcNoc)
            && /boundedClaimSemId/.test(pcNoc)
            && /IMPLEMENTED_SCOPE = Object\.freeze\(\{/.test(pcNoc)
            // and same-target-term must NOT be a validity condition (GPT's
            // ruling): a canonicalisation collapsing two source programs at one
            // assignment makes that case easy, not empty
            && !/both sides reach the SAME target term/.test(pcNoc);
          /* AND IT MUST REFUSE HOSTILE INPUT RATHER THAN THROW ON IT, checked
             BEHAVIOURALLY. The first draft grepped for the string
             "proof-checker-threw", which survives happily in code that no
             longer runs — the raw-text rung again, and its own forgery walked
             straight through it. A proof checker's entire input is
             adversary-supplied; a stack trace is not a verdict. The probe is
             wrapped for B2.1.2's reason: this rung runs adversary-influenced
             code, and a grid_check that dies with a trace instead of a
             diagnostic is the defect one level up. */
          let SCH = null;
          try { SCH = await import(pathToFileURL(A("schema.mjs")).href); } catch { /* null */ }
          /* COMPUTES ITS OWN VERDICT — BEHAVIOURALLY, AND P3.1 IS WHY.
             This was two regexes over the source, one of them matching a LOCAL
             VARIABLE NAME (`const computed = refusals.length === 0`). Renaming
             that variable to `evidence_verdict` while making the result
             STRONGER turned the gate red — the eleventh time in this line that
             a check has been anchored on text rather than on behaviour, and the
             second in two rounds caused by an improvement rather than a
             regression.
             Behavioural now, and it gates the invariant P3.1 added rather than
             the shape of a line: a refusal list must produce ok:false AND
             verdict:"REFUSED" together. All three checkers used to be able to
             answer {ok:false, verdict:"VERIFIED"} — the evidence computed to
             VERIFIED and the stored verdict was forged — which is harmless
             inside one checker and a trap under nesting, where a parent asking
             `verdict` and a parent asking `ok` disagree about the same child. */
          const coherent = probe(() => {
            if (typeof SCH?.publicResult !== "function") return false;
            const refused = SCH.publicResult(
              { refusals: [{ code: "x", detail: "y" }], measured: {}, evidence_verdict: "VERIFIED" });
            const verified = SCH.publicResult(
              { refusals: [], measured: {}, evidence_verdict: "VERIFIED" });
            return refused.ok === false && refused.verdict === "REFUSED"
              && verified.ok === true && verified.verdict === "VERIFIED";
          }, false) === true;
          /* AND IT MUST COMPUTE THE VERDICT RATHER THAN READ IT, DISCRIMINATED
             BEHAVIOURALLY. The cheap witness is a bundle that FAILS while
             asserting VERIFIED: an honest checker derives REFUSED from its own
             refusals and adds one more saying so, and a checker that assigned
             `evidence_verdict = agg.bounded_claim_verdict` agrees with the
             bundle and never raises it. No real evidence needed — the
             discriminating fact is whether the checker CONTRADICTS the
             artifact's own verdict field, which only requires the artifact to
             have one. */
          const contradictsForgedVerdict = typeof PC?.checkBundle === "function" && probe(() => {
            const IN = { op: "input", name: "x" };
            const r = PC.checkBundle({ protocol: "TRVM-BOUNDED-PROOF-v1",
              claim: { proposition: { variables: ["x"], lhs: IN, rhs: IN }, proposition_sem_id: "x",
                variable_domains: { x: [0] }, domain_sem_id: "x", expected_cases: 1,
                scope: { kind: "k", quantifier: "q", generalizes_beyond_domain: false },
                bounded_claim_sem_id: "x", declared_properties: {} },
              chain_ids: {}, port_names: { lhs: [], rhs: [] }, cases: [],
              aggregate: { bounded_claim_verdict: "VERIFIED" } });
            return r?.ok === false
              && (r.refusals ?? []).some((x) => /computes REFUSED/.test(String(x.detail)));
          }, false) === true;
          const computesVerdict = coherent && contradictsForgedVerdict;
          /* AND THE GRAMMAR IS EXACT — law:proof.semantic-vocabulary-closed@1,
             tested on the primitive itself because it is a pure function and
             every checker in the tree rests on it. An unknown key must be
             REPORTED, not tolerated: that one branch is the whole difference
             between owning the values of known fields and owning the
             vocabulary. */
          const grammarOwnsKeys = probe(() => {
            if (typeof SCH?.grammar !== "function") return false;
            const unknown = SCH.grammar({ a: 1, surprise: true }, { required: ["a"], optional: [] }, "r");
            const missing = SCH.grammar({}, { required: ["a"], optional: [] }, "r");
            const clean = SCH.grammar({ a: 1 }, { required: ["a"], optional: ["b"] }, "r");
            return unknown.length === 1 && unknown[0].problem === "unknown"
              && unknown[0].key === "surprise"
              && missing.length === 1 && missing[0].problem === "missing"
              && clean.length === 0;
          }, false) === true;

          const hostile = [
            { protocol: "TRVM-BOUNDED-PROOF-v1", claim: {} },
            { protocol: "TRVM-BOUNDED-PROOF-v1",
              claim: { proposition: { variables: ["x"] }, variable_domains: { x: [0] } } },
            { protocol: "TRVM-BOUNDED-PROOF-v1",
              claim: { proposition: { variables: ["x"] }, variable_domains: { x: [0] },
                       expected_cases: 1 }, cases: [null], aggregate: {} },
          ];
          const refusedNotThrown = typeof PC?.checkBundle === "function" && hostile.every((h) => {
            const r = probe(() => PC.checkBundle(h), null);
            return r && typeof r === "object" && r.ok === false && Array.isArray(r.refusals)
              && r.refusals.length > 0;
          });
          ok(pcSrc.length > 0 && pbSrc.length > 0 && derivesOwn && leaked.length === 0
             && computesVerdict && grammarOwnsKeys && scopeStated && refusedNotThrown,
            `the bounded-proof checker must be INDEPENDENT of the generator that wrote the bundle. ` +
            `It imports [${imported.join(", ") || "nothing"}] from proof_bundle.mjs — the protocol's ` +
            `hash functions, which ARE the format — and none of ` +
            `[${BANNED_IMPORTS.join(", ")}] (${leaked.length} leaked). It derives the Cartesian ` +
            `product itself in productByIndex (${derivesOwn}), by mixed-radix index arithmetic ` +
            `rather than the generator's iterative expansion, so "the cases cover the domain" is two ` +
            `implementations agreeing and not one function agreeing with itself. It COMPUTES a ` +
            `verdict and compares the bundle's to it (${computesVerdict}) rather than reading one — ` +
            `probed on publicResult itself, because the check that stood here grepped the source for ` +
            `a LOCAL VARIABLE NAME and went red when a rename made the result stronger. AND THE ` +
            `SEMANTIC VOCABULARY IS CLOSED (${grammarOwnsKeys}): grammar() reports an unknown key ` +
            `as a violation, which is the one branch separating "the checker owns the values of the ` +
            `fields it knows" from "the checker owns the field set" — P1, P2 and P3 all shipped ` +
            `accepting a resealed scope.proves_all_naturals, and no value any of them read was ` +
            `wrong. ` +
            `an aggregate that certifies itself is B2's instantiate() defect at the end of the chain ` +
            `instead of the start. And the BOUNDED scope is stated in the ARTIFACT ` +
            `(${scopeStated}) as three machine-readable VALUES — kind, quantifier and ` +
            `generalizes_beyond_domain, none of them holding whitespace — bound together with the ` +
            `proposition and domain by a bounded-claim identity, REQUIRED by the checker against a ` +
            `scope the CHECKER declares for itself, and with the English warning left unhashed in ` +
            `scope_notes. P1 shipped this as prose and read none of it: deleting the scope, and ` +
            `rewriting it to an unbounded all-naturals claim, both verified with ZERO refusals. And ` +
            `the checker must REFUSE hostile input rather than throw on it, and must NOT treat two ` +
            `sides sharing a target term as invalid — a canonicalisation that collapsed them at one ` +
            `assignment would make that case easy, not empty. THE HOSTILE-INPUT CHECK IS ` +
            `BEHAVIOURAL (${refusedNotThrown}): ${hostile.length} malformed bundles must each come ` +
            `back as a refusal object rather than a stack trace, because grepping for the refusal ` +
            `code left it satisfiable by a string in code that no longer runs`);

          /* ── P2: THE DOMAIN CHECKER MUST NOT ASK THE COMPILER ───────────
             P1's checker had to avoid importing the generator's ENUMERATION.
             P2's has a sharper version of the same trap: if it asked
             `representableValue` whether the compiler was right to refuse, it
             would establish that the compiler agrees with itself — and unlike
             the enumeration case, that tautology would be invisible in a
             passing run, because the answers would all be correct.
             AND IT MUST NOT DECIDE FROM THE RESULT, which is checked
             BEHAVIOURALLY on the case that separates the two: (0-1)+2 has the
             final value 1, a perfectly representable natural, and must still be
             REFUSED. A checker deciding from the answer accepts five of this
             workload's six refusals. */
          let DC = null;
          try { DC = await import(pathToFileURL(A("domain_check.mjs")).href); } catch { /* stays null */ }
          const dcSrc = existsSync(A("domain_check.mjs"))
            ? readFileSync(A("domain_check.mjs"), "utf8") : "";
          const dcNoc = dcSrc.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
          const dcLowImports = (dcNoc.match(/import\s*\{([^}]*)\}\s*from\s*"\.\/lowering\.mjs"/) ?? [])[1] ?? "";
          const asksCompiler = /representableValue/.test(dcLowImports);
          // the separating case, run rather than described
          const ev = probe(() => DC?.evalForTargetDomain(
            { op: "add", a: { op: "sub", a: { op: "input", name: "x" }, b: { op: "input", name: "y" } },
              b: { op: "const", value: 2 } }, { x: 0, y: 1 }), null);
          const structural = ev?.disposition === "REFUSED" && ev.value === 1
            && ev.final_value_is_representable === true;
          /* ── P2.1: ABSENCE, BEHAVIOURALLY — AND THE CHECK THAT WAS HERE HAD
                NEVER RUN THE CODE ──────────────────────────────────────────
             `enforcesAbsence` was /domain-refusal-carries-evidence/ &&
             /downstream_of_emission/ over the source text. BOTH REGEXES MATCH A
             FILE WHOSE ENFORCEMENT HAS BEEN DELETED, because each string occurs
             more than once. And the negative-battery case aimed at it turned
             `refuse("domain-refusal-carries-evidence",` into `noop_absence(,`
             — the trailing comma survives the replacement — which is a SYNTAX
             ERROR, so the module never loaded and what actually reported the
             catch was `structural` going null against a null import. The case
             passed for four rounds without once exercising absence enforcement.
             That is the NINTH coincidental-satisfaction finding in this line and
             the first where the forgery itself was inert.
             Behavioural now, and on the attack that made P2.1 exist. */
          let DB = null, LWM = null, PBM = null;
          try { DB = await import(pathToFileURL(A("domain_bundle.mjs")).href); } catch { /* null */ }
          try { LWM = await import(pathToFileURL(A("lowering.mjs")).href); } catch { /* null */ }
          try { PBM = await import(pathToFileURL(A("proof_bundle.mjs")).href); } catch { /* null */ }
          /* THE EVIDENCE IS SYNTHESISED HERE, NOT READ FROM domain_bundle.json.
             That file is `generated_evidence` and the battery deliberately does
             not copy it — 200 KB × 371 cases — so a probe that read it would be
             satisfied-by-absence in every scratch tree and would gate nothing.
             A one-case certificate is enough: the checker accumulates refusals
             rather than stopping, so the other codes it raises about the missing
             fifteen assignments are noise, and the question is only whether the
             ONE code this property owns appears. */
          const synthRefusal = (contract) => {
            const asgn = { x: 0, y: 1 };
            const psid = LWM.programSemId(DB.PROGRAM.ast);
            const dsid = DB.domainSemId2(DB.VARIABLE_DOMAINS);
            const c = {
              case_index: 0, assignment: asgn, assignment_sem_id: DB.assignmentSemId2(asgn),
              source_value: 1, disposition: "REFUSED",
              refusal: { program_sem_id: psid,
                refusal_phase: contract.phase, refusal_code: "emit-sub-underflow",
                refusal_witness: { minuend: 0, subtrahend: 1 },
                absent: contract.downstream_absent,
                // THE ARTIFACT THE REFUSAL SAYS DOES NOT EXIST, present anyway.
                film: { frames: [], terminal: { termination: "NORMAL_FORM" } } },
              case_evidence_id: null };
            c.case_evidence_id = DB.domainCaseId(c);
            return { protocol: DB.DOMAIN_PROTOCOL,
              claim: { program: DB.PROGRAM, program_sem_id: psid,
                variable_domains: DB.VARIABLE_DOMAINS, domain_sem_id: dsid, expected_cases: 16,
                scope: DB.DOMAIN_CLAIM_SCOPE, refusal_contract: contract,
                domain_claim_sem_id: DB.domainClaimSemId(psid, dsid, DB.DOMAIN_CLAIM_SCOPE, contract) },
              chain_ids: PBM.chainIds(), cases: [c], aggregate: {} };
          };
          const answer = (contract) => probe(() => {
            if (!DC || !DB || !LWM || !PBM) return null;
            const r = DC.checkDomainBundle(synthRefusal(contract));
            return Array.isArray(r?.refusals)
              ? { ok: r.ok, codes: [...new Set(r.refusals.map((x) => x.code))] } : null;
          }, null);
          const HONEST_CONTRACT = DB?.REFUSAL_CONTRACT;
          // GPT'S ATTACK: the claimant shortens the contract, the case's declared
          // absence follows it, and the claim id is resealed over the new one.
          const NARROWED = HONEST_CONTRACT && { ...HONEST_CONTRACT,
            downstream_absent: HONEST_CONTRACT.downstream_absent.filter((f) => f !== "film") };
          const plain = HONEST_CONTRACT ? answer(HONEST_CONTRACT) : null;
          const attack = NARROWED ? answer(NARROWED) : null;
          const enforcesAbsence = plain?.ok === false
            && plain.codes.includes("domain-refusal-carries-evidence");
          // AND THE CONTRACT IS THE CHECKER'S. Narrowed and resealed, the attack
          // must still be refused — by the contract comparison, by the
          // checker-owned enumeration, or by both. Two barriers, and the case is
          // only closed if at least one of them is standing.
          const contractOwned = attack?.ok === false
            && (attack.codes.includes("domain-refusal-contract-mismatch")
             || attack.codes.includes("domain-refusal-carries-evidence"));
          // AND CHANGING IT MOVES THE CLAIM'S IDENTITY, which under P2 it did
          // not. Stated as a DIFFERENCE between two recomputations rather than
          // against a stored id, so a case that perturbs the hash function is
          // caught by THIS property rather than by a stale artifact beside it.
          const contractBindsClaimId = probe(() => {
            if (!DB || !LWM || !NARROWED) return false;
            const psid = LWM.programSemId(DB.PROGRAM.ast);
            const dsid = DB.domainSemId2(DB.VARIABLE_DOMAINS);
            const one = DB.domainClaimSemId(psid, dsid, DB.DOMAIN_CLAIM_SCOPE, HONEST_CONTRACT);
            const two = DB.domainClaimSemId(psid, dsid, DB.DOMAIN_CLAIM_SCOPE, NARROWED);
            return typeof one === "string" && one.length > 8 && one !== two;
          }, false) === true;
          // ANCHORED ON THE ARITHMETIC, not on the sentence explaining it. This
          // was /the disposition is not total/ and matched nothing, because the
          // phrase is two fragments of a template literal — the THIRD time in
          // this pass that a check has grepped source for a string assembled at
          // runtime. B6.1's convention is to match the DECLARATION; here the
          // declaration is the condition itself. Totality is also exercised
          // behaviourally by domain_forgeries' disposition-neither-branch case,
          // which is the gate; this only requires the condition to exist.
          const totalPartition = /emitted \+ refusedCount !== derived\.length/.test(dcNoc);
          ok(dcSrc.length > 0 && !asksCompiler && structural && enforcesAbsence
             && contractOwned && contractBindsClaimId && totalPartition,
            `the bounded DOMAIN checker must derive the compiler's expected disposition WITHOUT ` +
            `asking the compiler. It imports [${dcLowImports.split(",").map((x) => x.trim()).filter(Boolean).join(", ")}] ` +
            `from lowering.mjs and NOT representableValue (${!asksCompiler}) — a checker that asked ` +
            `the compiler's own domain predicate whether the compiler was right to refuse would ` +
            `establish only that it agrees with itself, and unlike the enumeration tautology that ` +
            `one is INVISIBLE in a passing run because every answer would be correct. AND IT MUST ` +
            `DECIDE FROM THE COMPUTATION, NOT THE RESULT, run on the case that separates them: ` +
            `(0-1)+2 evaluates to ${ev?.value}, which IS a representable natural ` +
            `(${ev?.final_value_is_representable}), and the disposition must still be ` +
            `${ev?.disposition} — a checker deciding from the answer accepts five of this workload's ` +
            `six refusals. A REFUSAL IS EVIDENCE INCLUDING ITS ABSENCE (${enforcesAbsence}), RUN ` +
            `RATHER THAN GREPPED: a REFUSED case is handed a real film and the checker must answer ` +
            `domain-refusal-carries-evidence [${plain?.codes?.join(", ") ?? "no answer"}]. AND THE ` +
            `ABSENCE CONTRACT IS THE CHECKER'S, NOT THE CERTIFICATE'S (${contractOwned}): the same ` +
            `film with the contract narrowed, every case's absent-set narrowed to match and the ` +
            `claim id resealed — the attack P2 ACCEPTED at ok:true with zero refusals — must still ` +
            `be refused [${attack?.codes?.join(", ") ?? "no answer"}]. AND THE CONTRACT BINDS THE ` +
            `CLAIM'S IDENTITY (${contractBindsClaimId}): dropping one field from downstream_absent ` +
            `must move domain_claim_sem_id, which under P2 left it byte-identical. AND THE ` +
            `PARTITION IS TOTAL (${totalPartition}): every ` +
            `derived assignment falls in exactly one branch, so "neither" is not a case`);

          /* ── P3: THE COMPOSITION CHECKER MUST NOT FLATTEN ITS CHILDREN ───
             P1's checker must not import the generator's enumeration; P2's must
             not import the compiler's domain predicate; P3's must not import
             the MACHINE. A composition that re-derived its children's receipts
             would be a bigger leaf wearing a composition's name, and the whole
             claim of the artifact is that a verified proof object can be an
             input to another one WITHOUT being flattened.
             Asserted on the import list rather than on a comment, because
             "0 films replayed" is only structural if replaying one is
             impossible in this file. And asserted BEHAVIOURALLY too: the
             parent must refuse a child its own checker refuses, which is the
             property that stops a citation becoming a warrant. */
          let CC = null;
          try { CC = await import(pathToFileURL(A("compose_check.mjs")).href); } catch { /* null */ }
          const ccSrc = existsSync(A("compose_check.mjs"))
            ? readFileSync(A("compose_check.mjs"), "utf8") : "";
          const ccNoc = ccSrc.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
          const ccImports = [...ccNoc.matchAll(/from\s*"\.\/([\w.-]+)"/g)].map((m) => m[1]);
          const FLATTENING = ["trvm_law_kernel.mjs", "lowering.mjs", "scrambled_rt.mjs",
                              "observed_execution_host.mjs", "derive_protocol.mjs"];
          const flattens = ccImports.filter((f) => FLATTENING.includes(f));
          /* A CHILD ITS OWN CHECKER REFUSES, UNDER A PARENT WHOSE EVERY HASH IS
             CORRECT. Synthesised for the same reason as above — compose_bundle.json
             is generated evidence and is not in a scratch tree — and the child
             reused here is the one-case certificate the P2 probe already builds,
             which its own checker refuses. The citation over it is computed
             honestly, so nothing in the PARENT is wrong: if the parent treated a
             verified_claim_sem_id as a warrant, this would pass. */
          let CB = null, CERT = null;
          try { CB = await import(pathToFileURL(A("compose_bundle.mjs")).href); } catch { /* null */ }
          try { CERT = await import(pathToFileURL(A("certificate.mjs")).href); } catch { /* null */ }
          const parentOverBrokenChild = probe(() => {
            if (!CC || !CB || !CERT || !DB || !LWM || !PBM || !HONEST_CONTRACT) return null;
            const child = synthRefusal(HONEST_CONTRACT);
            child.aggregate = { aggregate_id: "agg-" + "f".repeat(64) };
            const op = CB.operandFor(child, "domain_claim_sem_id");
            const claim = { statement: "one child", connective: CB.CONNECTIVE,
              scope: CB.COMPOSE_CLAIM_SCOPE, operands: [op], composed_claim_sem_id: null };
            claim.composed_claim_sem_id =
              CB.composedClaimSemId(claim.connective, claim.scope, claim.operands);
            const agg = { operands: 1, children_carried: 1, children_verified: 0,
              child_verdicts: {}, leaf_receipts_rederived_by_parent: 0,
              composed_verdict: "REFUSED", aggregate_id: null };
            agg.aggregate_id = CB.composeAggregateId(agg);
            const r = CC.checkComposeBundle({ protocol: CB.COMPOSE_PROTOCOL, claim,
              children: [{ verified_claim_sem_id: op.verified_claim_sem_id, bundle: child }], aggregate: agg });
            return r.ok === false && r.refusals.some((x) => x.code === "compose-child-refused");
          }, null) === true;
          ok(ccSrc.length > 0 && flattens.length === 0 && parentOverBrokenChild,
            `the COMPOSITION checker must treat a child as an object with a checker, not as a pile ` +
            `of receipts. It DIRECTLY imports [${ccImports.join(", ")}] and none of the flattening ` +
            `modules [${FLATTENING.join(", ")}] (${flattens.length === 0}) — so "0 films replayed ` +
            `by the parent" is STRUCTURAL: that file holds no BINDING for a runtime, so replaying a ` +
            `film there is not something it could do wrongly but something it cannot express. THE ` +
            `KERNEL IS STILL IN THE PROCESS and this does not claim otherwise — the child checkers ` +
            `load it, necessarily, because they are what replays the films. The narrower property ` +
            `is the one that matters: the kernel is reachable only THROUGH A CHILD CHECKER, never ` +
            `from the parent's own reasoning. AND A CITATION IS NOT A WARRANT ` +
            `(${parentOverBrokenChild}): a ` +
            `child broken so its OWN checker refuses it, carried under a parent whose every hash is ` +
            `untouched and correct, must still be refused — nothing the parent knows about could ` +
            `catch that, which is exactly why the parent RUNS the child's checker rather than ` +
            `trusting the name it cites`);

          /* ── P4.1: FOUR PLANES, AND NONE OF THEM STANDS IN FOR ANOTHER ──
             P4 mixed them and the review found each mixture separately:
             `artifact_root` was inside the CLAIM, so a prose edit renamed the
             theorem; the root hashed the PARSED object, so pretty bytes,
             respelled numbers and DUPLICATE MEMBER NAMES all shared one
             address; the depth ceiling was a caller's argument; and an
             untrusted citation reached a filesystem `join()`.

             EVERY PROBE IS BEHAVIOURAL AND SYNTHESISES ITS OWN WORLD, because
             nest_bundle.json and cas/ are generated evidence and are not in a
             scratch tree. Modules are bound BEFORE the probes that use them —
             P3.1 lost two attempts each to a `let` referenced above its
             declaration, and a gate that returns false for its own bug reads
             exactly like one that returns false for a defect. */
          let NB = null, NC = null, CAS = null, RELID = null;
          try { NB = await import(pathToFileURL(A("nest_bundle.mjs")).href); } catch { /* null */ }
          try { NC = await import(pathToFileURL(A("nest_check.mjs")).href); } catch { /* null */ }
          try { CAS = await import(pathToFileURL(A("cas.mjs")).href); } catch { /* null */ }
          /* P4.6. THIS IMPORT WAS IMPOSSIBLE UNTIL THIS ROUND: spec_release.mjs
             ran its whole CLI at module scope and called process.exit, so
             importing it to probe the release identity would have terminated the
             grid. It carries the IS_MAIN guard its siblings already had. */
          try { RELID = await import(pathToFileURL(A("spec_release.mjs")).href); } catch { /* null */ }
          /* P4.7.2. THE STATE MACHINE IS PART OF THE INSTRUMENT, so the grid
             probes it by importing it from where the freeze reaches — not from
             `governance/`, which is where P4.7.1 computed run identities and
             checked transition preconditions with nothing holding it still. */
          let RST = null;
          try { RST = await import(pathToFileURL(join(ROOT, "..", "docs", "spec", "proof-wire",
            "experiment", "run_state.mjs")).href); } catch { /* null */ }
          const dir0 = A("receipts");
          let SCORE = null;
          try { SCORE = await import(pathToFileURL(join(ROOT, "..", "docs", "spec", "proof-wire",
            "experiment", "holdout_score_core.mjs")).href); } catch { /* null */ }
          let HRUN = null;
          try { HRUN = await import(pathToFileURL(join(ROOT, "..", "docs", "spec", "proof-wire",
            "experiment", "holdout_runner.mjs")).href); } catch { /* null */ }
          /* THE PACKAGE MACHINERY, so the mount probe measures the real
             primitives rather than a description of them. */
          let PKG = null;
          try { PKG = await import(pathToFileURL(A("blind_package.mjs")).href); } catch { /* null */ }
          const readSrc = (f) => existsSync(A(f)) ? readFileSync(A(f), "utf8") : "";
          const ncSrc = existsSync(A("nest_check.mjs"))
            ? readFileSync(A("nest_check.mjs"), "utf8") : "";
          const ncNoc = ncSrc.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
          const ncImports = [...ncNoc.matchAll(/from\s*"\.\/([\w.-]+)"/g)].map((m) => m[1]);
          const ncFlattens = ncImports.filter((f) => FLATTENING.includes(f));
          const usable = !!(NB && NC && CAS);

          /** One synthetic world: a child of a protocol whose OWN checker
           *  refuses it, cited honestly, stored under its own real root in
           *  CANONICAL bytes. `tweak` may corrupt any plane before sealing. */
          const synthDag = (tweak) => {
            const child = {
              protocol: "TRVM-BOUNDED-DOMAIN-PROOF-v1",
              claim: { domain_claim_sem_id: "dclaim-" + "a".repeat(64) },
              chain_ids: { lowering_version: "0.0.0-probe" },
              aggregate: { aggregate_id: "agg-" + "f".repeat(64) },
              cases: [],
            };
            const store = CAS.memoryStore(new Map());
            const root = store.put(child);
            const op = NB.operandFor(child, "domain_claim_sem_id");
            const claim = { connective: "CONJUNCTION", scope: NB.NEST_CLAIM_SCOPE,
              operands: [op], nested_claim_sem_id: null };
            const bytes = CAS.artifactBytes(child);
            const agg = { operands: 1, child_verdicts: {},
              leaf_receipts_rederived_by_parent: 0, films_replayed_by_parent: 0,
              nested_verdict: "REFUSED", aggregate_id: null };
            const structure = { edges: 1, unique_artifacts: 1, max_depth_below: 1,
              bytes_if_inlined: bytes, unique_bytes: bytes,
              films_below_by_edge_multiplicity: 0, films_below_distinct: 0,
              cases_below_by_edge_multiplicity: 0, cases_below_distinct: 0,
              structure_sem_id: null };
            const bundle = { protocol: NB.NEST_PROTOCOL, claim,
              chain_ids: { leaf_chains: [child.chain_ids] },
              references: { contract: NB.REFERENCE_CONTRACT,
                operands: [{ verified_claim_sem_id: op.verified_claim_sem_id, artifact_root: root }] },
              aggregate: agg, structure };
            const opts = tweak?.({ child, store, root, op, bundle }) ?? {};
            claim.nested_claim_sem_id =
              NB.nestedClaimSemId(claim.connective, claim.scope, claim.operands);
            agg.aggregate_id = NB.nestAggregateId(agg);
            structure.structure_sem_id = NB.nestStructureSemId(structure);
            const r = NC.checkNestBundle(bundle, { store, ...opts });
            return { ok: r.ok, codes: [...new Set(r.refusals.map((x) => x.code))] };
          };
          const draws = (code, tweak) => usable && probe(() => {
            const r = synthDag(tweak);
            return r.ok === false && r.codes.includes(code);
          }, null) === true;

          // AN ADDRESS THAT RESOLVES IS NOT AN ARTIFACT THAT CHECKS OUT.
          const addressIsNotAWarrant = draws("nest-child-refused", null);
          // THE STORE IS NOT TRUSTED: right name, wrong bytes.
          const storeIsNotTrusted = draws("nest-artifact-root-mismatch",
            ({ store, root, child }) =>
              store.entries.set(root, CAS.canonicalWire({ ...child, smuggled: true })));
          /* THE WIRE IS CANONICAL. A DUPLICATE MEMBER NAME is the vector that
             matters: JSON.parse resolves it in favour of the LAST one, so the
             parsed object and therefore the root are the honest ones while the
             bytes say something else — and a second implementation keeping the
             FIRST would verify a different object under the same root. */
          const wireIsCanonical = draws("nest-artifact-non-canonical",
            ({ store, root, child }) => store.entries.set(root,
              '{"protocol":"TRVM-EVIL-v1",' + CAS.canonicalWire(child).slice(1)));
          // AN UNTRUSTED CITATION MAY NOT STEER A FILESYSTEM READ. Guarded at
          // TWO layers — the checker refuses a malformed citation before the
          // store is asked, and the store refuses a name that is not a root
          // before it builds a path — so the two are probed separately.
          const rootGrammarEnforced = draws("nest-artifact-root-malformed",
            ({ bundle }) => { bundle.references.operands[0].artifact_root = "../proof_bundle"; });
          /* THE STORE'S OWN CONFINEMENT, at one layer so a falsifier can reach
             it. `artifacts.json` is a case input and is therefore present in
             every scratch tree, and `cas/` need not exist for the question to
             mean anything: a store pointed at ROOT/cas must not answer
             "../artifacts" with the file one directory up. P4's did — with
             `proof_bundle` it returned 1.31 MB. */
          const storeIsConfined = !!CAS && probe(() => {
            const st = CAS.directoryStore(A("cas"));
            return st.get("../artifacts") === null && st.get("../../artifacts") === null;
          }, null) === true;
          // THE POLICY IS THE CHECKER'S: a caller may tighten and not weaken.
          const policyIsCheckerOwned = draws("nest-policy-weakened",
            () => ({ max_depth: (NC.SHIPPED_POLICY?.max_depth ?? 32) + 1 }));
          // THE VOCABULARY IS CLOSED AT THIS LAYER TOO.
          const warrantVocabularyRefused = draws("nest-vocabulary-unknown",
            ({ op }) => { op.already_verified = true; op.warrant = "resolved"; });
          /* THE WIRE IS UTF-8 BYTES, NOT A DECODED HOST STRING. P4.1 read files
             with the forgiving decoder, so a raw 0xFF became U+FFFD before the
             canonical equality could see it. */
          const wireIsBytes = draws("nest-artifact-invalid-utf8", ({ store, root, child }) => {
            const canonical = CAS.canonicalWireBytes(child);
            const bad = Buffer.from(canonical);
            const i = bad.findIndex((b) => b >= 0x80);
            bad[i >= 0 ? i : 1] = 0xff;
            store.entries.set(root, bad);
          });
          /* THE ROOT ARTIFACT IS HELD TO THE POLICY ITS CHILDREN ARE HELD TO.
             The ceiling must sit BETWEEN the child and the padded root: a limit
             low enough to catch both is caught by the CHILD's resolution, which
             draws the same code and makes the probe agree with itself rather
             than measure anything. */
          const rootIsBounded = draws("nest-budget-exceeded",
            ({ bundle }) => { bundle.annotations = { pad: "x".repeat(8192) };
              return { max_artifact_bytes: 4096 }; });
          /* THE VERIFIER OWNS ITS INPUT — law:proof.verifier-input-owned@1.
             Probed as the property that makes it true: a live getter is read
             EXACTLY ONCE, so there is no later read to disagree with. Against
             P4.1 this read 2 on P4 and 3 on P1, and both returned VERIFIED over
             an object that afterwards said something else. */
          const inputReadOnce = usable && probe(() => {
            const counts = [];
            for (const [fn, build] of [
              [NC.checkNestBundle, () => {
                const b = { protocol: NB.NEST_PROTOCOL, claim: {}, chain_ids: {},
                  references: { contract: { ...NB.REFERENCE_CONTRACT }, operands: [] },
                  aggregate: {}, structure: {} };
                return [b, b.references.contract, "address_is_a_warrant"];
              }],
              [PC?.checkBundle, () => {
                const b = { protocol: "TRVM-BOUNDED-PROOF-v1", claim: { scope: { x: false } } };
                return [b, b.claim.scope, "x"];
              }],
            ]) {
              if (typeof fn !== "function") return false;
              const [obj, rec, key] = build();
              let reads = 0;
              const real = rec[key];
              delete rec[key];
              Object.defineProperty(rec, key, { enumerable: true, configurable: true,
                get() { reads += 1; return reads <= 1 ? real : "MUTATED-AFTER-THE-READ"; } });
              fn(obj, { store: CAS.memoryStore(new Map()) });
              counts.push(reads);
            }
            return counts.every((n) => n === 1);
          }, null) === true;

          /* REFERENCE IS NOT CLAIM, ENFORCED WHERE IT IS ENFORCEABLE. The claim
             id hashes the operand record, so it is blind to `artifact_root`
             only because an operand MAY NOT CARRY ONE — the grammar is what
             makes the separation real, and probing the hash function alone
             would measure that adding a field changes a hash, which is not the
             property. So: an operand carrying an address is refused, and the
             claim id still MOVES when the certificate does, which is the
             non-degeneracy half. The end-to-end version — reword a leaf, watch
             every ancestor's claim id hold — is measured in nest_forgeries. */
          const referenceNotInClaimId = draws("nest-vocabulary-unknown",
            ({ op }) => { op.artifact_root = "root-" + "c".repeat(64); });
          const claimIdStillMovesWithTheCertificate = usable && probe(() => {
            const op = { protocol: "P", claim_sem_id: "c", aggregate_id: "a",
              verified_claim_sem_id: "vclaim-" + "1".repeat(64) };
            return NB.nestedClaimSemId("CONJUNCTION", NB.NEST_CLAIM_SCOPE, [op])
              !== NB.nestedClaimSemId("CONJUNCTION", NB.NEST_CLAIM_SCOPE,
                [{ ...op, verified_claim_sem_id: "vclaim-" + "2".repeat(64) }]);
          }, null) === true;

          /* CITABILITY, matched on the EXACT refusal and over TWO shapes. The
             first draft tested /chain_ids/ against the message and was ANSWERED
             BY A DIFFERENT EXCEPTION — with the requirement disabled an absent
             chain still throws, from canonicalBytes, as `not-canonical:
             undefined at $.chain_ids`. Fourteenth coincidental search-text hit
             in this line and the first inside an exception message. Two shapes,
             because the explicit check is load-bearing for `chain_ids: null`,
             which canonicalises to "null" happily. */
          const chainlessIsNotCitable = !!CERT && probe(() => {
            const refusedExactly = (chain_ids) => {
              try {
                CERT.verifiedClaimSemId({ protocol: "X", claim_sem_id: "c", aggregate_id: "a",
                  ...(chain_ids === undefined ? {} : { chain_ids }) });
                return false;
              } catch (e) { return String(e.message) === "certificate-incomplete: chain_ids"; }
            };
            return refusedExactly(undefined) && refusedExactly(null);
          }, null) === true;

          /* ── P4.3: THE SPEC IS ALLOWED TO DISAGREE ───────────────────────
             Two properties the grid can check itself, independently of the
             gates that also check them — because a conformance corpus the
             implementation regenerates, and an audit whose denominator is the
             implementation's own grammar, are both circles. */
          const specDir = A("../docs/spec/proof-wire");
          const readJson = (p) => { try { return JSON.parse(readFileSync(p, "utf8")); } catch { return null; } };
          /* THE ORACLE IS FROZEN AND THIS IMPLEMENTATION STILL MATCHES IT. The
             frozen root is read from the committed corpus and compared with what
             the live code computes for the same input. Changing an
             implementation-only constant while touching no specification moved
             every expected root and still reported PASS, before this existed. */
          const frozen = readJson(join(specDir, "vectors", "public", "manifest.json"));
          const oracleFrozen = !!CAS && !!frozen && typeof frozen.spec_revision === "string"
            && probe(() => frozen.wire_positive.every((v) => CAS.artifactRoot(v.input) === v.artifact_root),
              null) === true;
          /* THE NORMATIVE GRAMMAR AND THE CHECKER'S OWN GRAMMAR AGREE. Deleting a
             field from the checker AND its enforcement AND the producer leaves
             field_audit.mjs reporting 45/45 PASS while the protocol has 46
             fields — measured, not hypothesised. */
          const normative = readJson(join(specDir, "schema", "nested-composition-v2.json"));
          const specGrammarAgrees = usable && !!normative && probe(() => {
            const impl = NC.GRAMMAR;
            const keys = (o) => Object.keys(o ?? {}).sort().join(",");
            if (keys(normative.grammar) !== keys(impl)) return false;
            return Object.keys(normative.grammar).every((rec) =>
              [...(normative.grammar[rec].required ?? [])].sort().join(",")
                === [...(impl[rec]?.required ?? [])].sort().join(",")
              && [...(normative.grammar[rec].optional ?? [])].sort().join(",")
                === [...(impl[rec]?.optional ?? [])].sort().join(","));
          }, null) === true;

          /* THE NORMATIVE PROSE IS BOUND TO THE RELEASE. Editing the formula in
             a Markdown document — the one surface a blind implementer reads and
             no gate executes — left SPEC-AGREEMENT and SPEC-VECTORS both green.
             Probed here as the property, not the runner: the release object
             exists, names a digest, and that digest is the one this tree has. */
          const release = readJson(join(specDir, "SPEC-RELEASE.json"));
          const specBound = !!release && typeof release.spec_digest === "string"
            && typeof release.holdout_commitment === "string" && probe(() => {
              const walk = (d) => readdirSync(d).sort().flatMap((f) => {
                const p2 = join(d, f);
                return statSync(p2).isDirectory() ? walk(p2) : [p2];
              });
              const files = walk(specDir)
                // The same file set spec_release.mjs defines: the corpus, the
                // open-requirements register, the immutable release archive and
                // the release object itself are out, and so is everything under
                // experiment/ — procedure is not protocol. P4.6 made that last
                // one a DIRECTORY rule rather than a filename set, because the
                // recipe grammar, the observation grammar, the observation
                // schema and the synthetic fixture are all experiment surface
                // and an exception list forgets the fourth thing.
                .filter((p2) => { const r = relative(specDir, p2).replace(/\\/g, "/");
                  return !r.startsWith("vectors") && !r.startsWith("requirements")
                    && !r.startsWith("releases") && r !== "SPEC-RELEASE.json"
                    && !r.startsWith("experiment/"); })
                .map((p2) => ({ path: relative(specDir, p2),
                  sha256: createHash("sha256").update(readFileSync(p2)).digest("hex") }))
                .sort((a, b) => (a.path < b.path ? -1 : 1));
              const d = createHash("sha256")
                .update(files.map((f) => f.path + "\n" + f.sha256 + "\n").join("")).digest("hex");
              return d === release.spec_digest;
            }, null) === true;

          /* P4.6 (B). THE ARCHIVE, MEASURED. This grid's own evidence claimed
             `releases/<spec_release_id>.json written on issuance` and `releases
             are immutable objects` while no such directory existed and --update
             overwrote one file — an aspirational invariant in the register whose
             subject is claims matching executable evidence. Probed as the
             property: the archive exists under the identity and holds the SAME
             BYTES as the pointer beside it. */
          const releaseArchived = !!release && probe(() => {
            const a = join(specDir, "releases", `${release.spec_release_id}.json`);
            return existsSync(a)
              && readFileSync(a).equals(readFileSync(join(specDir, "SPEC-RELEASE.json")));
          }, null) === true;

          /* P4.6 (A). THE IDENTITY BINDS THE PROTOCOL IDENTIFIERS — falsified,
             not asserted. v0.2.0 built its preimage with a JSON.stringify
             replacer ARRAY, which is an allowlist applied RECURSIVELY, so the
             nested protocol map serialised as {} and renaming all three
             protocols left `srel` byte-identical. Reproduced here by renaming
             them and requiring the identity to MOVE. */
          const releaseIdBindsProtocols = !!release && !!RELID && probe(() => {
            const evil = JSON.parse(JSON.stringify(release));
            evil.protocols.wire = "EVIL-A";
            evil.protocols.verified_claim = "EVIL-B";
            evil.protocols.nested_composition = "EVIL-C";
            return RELID.releaseId(evil) !== RELID.releaseId(release)
              && RELID.releaseId(release) === release.spec_release_id;
          }, null) === true;

          /* P4.6 (G) / P4.7. THE SCORER LOADS NO TRVM — a structural fact about
             an import CLOSURE, the same shape as `flattening-imports` above.
             P4.5 printed "THE SCORER KNOWS EIGHT OPERATORS AND NO TRVM" while
             the executable imported cas, nest_bundle and nest_check and could
             only ever score itself. */
          const readSpec = (rel) => existsSync(join(specDir, rel))
            ? readFileSync(join(specDir, rel), "utf8") : "";
          const importsOf = (src) => [...src.matchAll(/^import[^;]*from\s+"([^"]+)"/gm)].map((m) => m[1]);
          const SCORER = readSpec("experiment/holdout_score_core.mjs");
          const SCHEMA_MOD = readSpec("experiment/holdout_schema.mjs");
          const scorerImports = importsOf(SCORER);
          /* P4.7.7 adds the EVIDENCE READER as a second permitted sibling. The
             property is unchanged and is the reason that file exists at all: the
             scorer may not load the implementation it scores, so the strict JSON
             reader is the INSTRUMENT'S own rather than `governance/cas.mjs`,
             whose canonical equality would do the same job and belongs to the
             subject. Both siblings are required to import node builtins only,
             which is what keeps "one sibling deep" from becoming a closure. */
          const SCORER_SIBLINGS = ["./holdout_schema.mjs", "./evidence.mjs"];
          const EVIDENCE_MOD = readSpec("experiment/evidence.mjs");
          const scorerIsImplementationFree = SCORER.length > 0 && SCHEMA_MOD.length > 0
            && EVIDENCE_MOD.length > 0
            && scorerImports.every((s) => s.startsWith("node:") || SCORER_SIBLINGS.includes(s))
            && importsOf(SCHEMA_MOD).length === 0
            && importsOf(EVIDENCE_MOD).every((s) => s.startsWith("node:"));

          /* P4.7. THE INSTRUMENT IS CONTENT-BOUND. The decisive P4.6 falsifier:
             forcing every real predicate true left the synthetic fixture, the
             holdout, the release AND the pinned run all green, because the
             scorer was in no digest at all. Probed as the property — the
             instrument lives where experiment_digest reaches, and the run pins
             its digest. Moving it OUT would SHRINK that digest rather than move
             it, which is why membership is asserted and not merely the bytes. */
          /* P4.7.2 adds the STATE MACHINE. It is the instrument in the strictest
             sense: it decides whether the secret is released and whether the
             experiment completed, and P4.7.1 had both of those living in
             `governance/`, outside every digest. */
          /* THIS LIST IS DELIBERATELY TYPED OUT HERE AND NOT IMPORTED — it is
             this register's own statement of what the measuring instrument is,
             and a probe that reads the list from the file it is auditing cannot
             notice a member being dropped from it. P4.7.7 makes the two compare:
             the frozen `INSTRUMENT` must EQUAL this, so a divergence is reported
             rather than quietly shrinking what "the instrument" means. Before
             this they could drift, and adding `evidence.mjs` to one of them is
             exactly the edit that would have done it. */
          const INSTRUMENT_MEMBERS = ["experiment/evidence.mjs", "experiment/holdout_schema.mjs",
            "experiment/holdout_score_core.mjs", "experiment/holdout_runner.mjs",
            "experiment/run_state.mjs",
            "experiment/holdout-observation-v1.schema.json",
            "experiment/holdout-recipe-v1.schema.json", "experiment/fixtures"];
          const instrumentListAgrees = !!RST && Array.isArray(RST.INSTRUMENT)
            && [...RST.INSTRUMENT].sort().join("|") === [...INSTRUMENT_MEMBERS].sort().join("|");
          const runRec = readJson(A("blind-run.json"));
          const instrumentIsFrozen = !!runRec && instrumentListAgrees
            && INSTRUMENT_MEMBERS.every((m) => existsSync(join(specDir, m)))
            && typeof runRec.instrument_digest === "string"
            && probe(() => {
              const walk = (rel) => { const abs = join(specDir, rel);
                if (!existsSync(abs)) return [];
                return statSync(abs).isDirectory()
                  ? readdirSync(abs).sort().flatMap((f) => walk(`${rel}/${f}`))
                  : [{ path: rel, sha256: createHash("sha256").update(readFileSync(abs)).digest("hex") }];
              };
              const files = INSTRUMENT_MEMBERS.flatMap(walk).sort((a, b) => (a.path < b.path ? -1 : 1));
              const d = createHash("sha256")
                .update(files.map((f) => f.path + "\n" + f.sha256 + "\n").join("")).digest("hex");
              return d === runRec.instrument_digest;
            }, null) === true;

          /* P4.7. THE DELIVERED BYTES HAVE AN IDENTITY OF THEIR OWN, and the
             forbidden classes are PROVEN absent. `requirements/open/` is handed
             to the implementer and excluded from spec_digest by construction, so
             editing it left SPEC-RELEASE and BLIND-RUN green with identical
             identities. */
          const pkgRec = readJson(A("blind-package.json"));
          const blindPackageBound = !!pkgRec && !!runRec
            && runRec.blind_package_id === pkgRec.blind_package_id
            && Array.isArray(pkgRec.files)
            && pkgRec.files.some((f) => f.path.startsWith("requirements/"))
            /* THE SAME BLUNT-BLOCKLIST MISTAKE, ONE FILE OVER, AND IT FAILED
               LOUDLY HERE. A first draft of this probe forbade any path matching
               /holdout/ — which flags holdout_score_core.mjs and
               holdout_schema.mjs, the frozen MEASURING INSTRUMENT, whose whole
               point is to be IN the package. A name cannot tell the scorer from
               the challenges it scores. The path rules keep only the classes
               whose NAME is the whole of what they are, and the challenge set is
               excluded by SHAPE: a hidden challenge has an H* id, a public
               synthetic fixture has an S*. */
            && !pkgRec.files.some((f) => /governance\/|ledger|brief|review|node_modules/i.test(f.path))
            && !pkgRec.files.some((f) => /(^|\/)H[0-9]+-/.test(f.path));

          /* P4.7. THE GATE THAT HOLDS THE SECRET DELEGATES, AND CANNOT QUIETLY
             UN-DELEGATE. A delegation that could be replaced by a local scorer
             is not a delegation. */
          const SCORE_GATE = readSrc("holdout_score.mjs");
          const scoreGateDelegates = SCORE_GATE.length > 0
            /* ANCHORED ON A LITERAL, NOT ON AN ASSEMBLED PATH. A first draft
               tested /experiment[\\/]+holdout_runner\.mjs/ and read FALSE,
               because the gate builds that path with join(SPEC, "experiment",
               "holdout_runner.mjs") and the concatenated string exists only at
               runtime. That is this tree's coincidental-search-text species in
               its other direction — a probe answered by the ABSENCE of text it
               had no reason to expect — and it reads exactly like a real defect. */
            && /holdout_runner\.mjs/.test(SCORE_GATE) && /"experiment"/.test(SCORE_GATE)
            && !/function\s+score\b|const\s+score\s*=/.test(SCORE_GATE)
            && importsOf(SCORE_GATE).every((s) => s.startsWith("node:"));

          /* P4.7.2 (A). THE RUN IDENTITY IS COMPUTED BY FROZEN CODE. P4.7.1
             computed it in `governance/blind_run.mjs`, so one edit could falsify
             a record AND move the formula that decides whether the record
             identifies itself. MEASURED, not read: the frozen module is imported
             and asked to re-derive the pinned run's own id. */
          const runStateFrozen = !!RST && !!runRec
            && existsSync(join(specDir, "experiment/run_state.mjs"))
            && probe(() => RST.runId(runRec) === runRec.run_id, null) === true;

          /* P4.7.2 (B). A STATUS IS A CLAIM UNTIL A RECEIPT CHAIN WITNESSES IT.
             MEASURED BOTH WAYS, which is the half that catches a checker that
             simply always complains: the record as it stands must draw ZERO
             chain problems, and the same record with `status` moved to REVEALED
             and `run_id` recomputed by the tree's own exported function — the
             exact attack, which was green against P4.7.1 — must draw at least
             one. */
          /* NOT MEASURABLE IS NOT THE SAME AS TRUE, AND IT IS NOT THE SAME AS
             FALSE EITHER. The negative battery stages each case into its own
             tree from artifacts.json, which does not carry `receipts/` — and no
             forgery among the 392 perturbs it — so this probe read FALSE in
             every case tree and the UNPERTURBED BASELINE failed: a gate
             reporting a defect for its own missing fixture, the species that put
             the spec tree and ../Makefile into the staging in the first place.
             The absence is NAMED rather than passed silently; the canonical
             gov-grid run measures it, and a `receipts/` that went missing for
             real fails BLIND-RUN on the line above this one. */
          const receiptsHere = existsSync(A("receipts"));
          const statusIsWitnessed = !receiptsHere ? null : (!!RST && !!runRec && probe(() => {
            const dir = A("receipts");
            const honest = RST.chainProblems(runRec, dir).length === 0;
            const forged = { ...runRec, status: "REVEALED" };
            forged.run_id = RST.runId(forged);
            return honest && RST.chainProblems(forged, dir).length > 0;
          }, null) === true);

          /* P4.7.3. AN AUTHORITY FACT IS BOUND TO THE SUBJECT IT IS EXERCISED
             OVER. P4.7.2 gave every lifecycle program a --state-root so the
             falsifier battery could stop attacking the live record — and a
             SELECTABLE STATE ROOT IS A SELECTABLE AUTHORITY: a REVEALED copy of
             the record in /tmp authorized the CANONICAL candidate, which
             received all ten hidden constructions while the canonical record
             read CANDIDATE_FROZEN. Measured on both halves of the repair: the
             state root is derived from the world and ignores any override, and a
             path that escapes the world is refused while one inside it is not. */
          const gridRepo = join(ROOT, "..");
          const authorityBoundToWorld = !!RST && probe(() => {
            const want = join(gridRepo, "governance");
            const derived = RST.resolveState(gridRepo).root === want;
            const unselectable = RST.resolveState(gridRepo, "/tmp/some-other-authority").root === want;
            const inside = !!RST.containedPath(gridRepo, "governance/cas.mjs");
            const escapes = RST.containedPath(gridRepo, "../etc/passwd") === null
              && RST.containedPath(gridRepo, "/etc/passwd") === null;
            return derived && unselectable && inside && escapes;
          }, null) === true;

          /* P4.7.4. A TERMINAL CLAIM IS WITNESSED BY THE MEASUREMENT ARTIFACT
             THAT GIVES IT MEANING, not only by the transition that asserted it.
             P4.7.3's chain consumed transition receipts and nothing else, so a
             COMPLETE run never had to show a RESULT: a hand-written COMPLETE
             transition over a candidate that only ran `exit 99` verified green,
             and so did deleting the RESULT after an HONEST completion — which is
             the half that matters, because ordinary evidence loss was invisible.
             MEASURED BOTH WAYS on the live record: whatever status it is in, the
             terminal verifier must be silent about it if it is not COMPLETE, and
             a record forged to COMPLETE without a RESULT must draw a problem. */
          const terminalWitnessed = !!RST && !!runRec && probe(() => {
            const dir = A("receipts");
            const honest = RST.resultProblems({ ...runRec, status: "COMPLETE" }, dir).length > 0
              || runRec.status === "COMPLETE";
            const quiet = runRec.status === "COMPLETE"
              || RST.verifyRun({ runBytes: RST.renderRun(runRec), repoRoot: gridRepo, specDir,
                receiptsDir: dir, requireChain: false }).result.length === 0;
            return honest && quiet;
          }, null) === true;

          /* P4.7.5. THE TERMINAL VERIFIER REPLAYS BOTH THINGS COMPLETE CLAIMS.
             P4.7.4 archived the observation bytes and then re-derived only
             AGREEMENT from them: two documents whose `observations` member is
             `{}` agree perfectly, every digest matches, and `25/25` was read off
             the RESULT — while scoring those same documents against the
             committed challenge set gives `missing: 10, pass: 0`. Measured as
             the property, on the frozen scorer rather than on the record: an
             EMPTY observation must score zero satisfied and every committed
             challenge missing, and the honest reference document must not. And a
             label is an identifier, not a path — the archive destination is
             refused outright for one that would leave the directory. */
          const conformanceReplayed = !!RST && !!SCORE && !!release && probe(() => {
            const hold = A("holdout");
            if (!existsSync(hold)) return null;          /* not staged here; see below */
            const chs = RST.loadChallenges(hold);
            const empty = SCORE.scoreRun(chs, { type: "TRVM-HOLDOUT-OBSERVATION-v1",
              implementation: "x", spec_release_id: release.spec_release_id, observations: {} },
              { expectRelease: release.spec_release_id, expectImplementation: "x" });
            const emptyIsEmpty = !empty.refused && empty.pass === 0
              && empty.missing.length === chs.length && chs.length > 0;
            const labelIsNotAPath = RST.observationFile(dir0, "brun-x", "../../../escape") === null
              && RST.observationFile(dir0, "brun-x", "javascript") !== null
              && RST.IMPLEMENTATION_RE.test("javascript")
              && !RST.IMPLEMENTATION_RE.test("../../../escape");
            return emptyIsEmpty && labelIsNotAPath;
          }, null);

          /* P4.7.6. AN AUTHENTICATED EVIDENCE ARTIFACT HAS EXACTLY ONE READING.
             `new Map(list.map(x => [x.implementation, x]))` collapses duplicates
             with the LAST one winning, and nothing checked first — so a bogus
             `javascript` row inserted BEFORE the genuine one in RESULT.subjects
             left BLIND-RUN saying PASS while a reader resolving by FIRST
             occurrence read a different measurement out of the same
             authenticated bytes. P4.1's duplicate-wire-member hazard in an
             array. Measured on the frozen primitives, both directions. */
          const evidenceUnambiguous = !!RST && probe(() => {
            const one = [{ implementation: "javascript" }, { implementation: "go" }];
            const two = [{ implementation: "javascript" }, { implementation: "javascript" }];
            const uniqueHolds = RST.uniqueProblems(one, "x").length === 0
              && RST.uniqueProblems(two, "x").length > 0
              && RST.uniqueProblems([{ implementation: "../escape" }], "x").length > 0
              && RST.uniqueProblems("not a list", "x").length > 0;
            const shape = { ...Object.fromEntries(Object.keys(RST.RESULT_OBSERVATION_MEMBERS)
              .map((k) => [k, "x"])) };
            const shapeHolds = RST.shapeProblems(shape, RST.RESULT_OBSERVATION_MEMBERS, "x").length === 0
              && RST.shapeProblems({ ...shape, sneaked: 1 }, RST.RESULT_OBSERVATION_MEMBERS, "x").length > 0
              && RST.shapeProblems({}, RST.RESULT_OBSERVATION_MEMBERS, "x").length > 0;
            /* NON_AUTHORITATIVE exists and is used, so the vocabulary has three
               categories and not a silent fourth. */
            const classified = Object.values(RST.RECEIPT_MEMBERS)
              .every((v) => ["CHECKED", "DERIVED", "NON_AUTHORITATIVE"].includes(v))
              && Object.values(RST.RESULT_MEMBERS).every((v) => v === "CHECKED")
              && !("world_root" in RST.RESULT_MEMBERS) && !("note" in RST.RESULT_MEMBERS);
            return uniqueHolds && shapeHolds && classified;
          }, null) === true;

          /* P4.7.7. THE BYTE BOUNDARY, MEASURED ON THE READER'S OWN PRIMITIVES
             AND IN BOTH DIRECTIONS. The reader's two claims are that it is
             STRICTER than JSON and never DIFFERENT from it, so the probe asserts
             both: bytes JSON.parse accepts and the reader refuses (a duplicate
             member, an unpaired surrogate, invalid UTF-8), and bytes both accept
             and read the same way. Against P4.7.6 the same duplicate-member
             bytes verified green, because the shape checks ran over a value
             JSON.parse had already collapsed. */
          const evidenceBytesUnambiguous = !!RST && probe(() => {
            const b = (x) => Buffer.from(x, "utf8");
            const refuses = (bytes) => RST.tryParseEvidence(bytes, "probe").refused !== null;
            const jsonTakes = (bytes) => { try { JSON.parse(Buffer.from(bytes).toString("utf8")); return true; }
              catch { return false; } };
            const dup = b('{"status":"REVEALED","status":"PINNED"}');
            const sur = b('{"a":"\\ud800"}');
            const bad = Buffer.from([0x7b, 0x22, 0x61, 0x22, 0x3a, 0x22, 0xff, 0x22, 0x7d]);
            const stricter = [dup, sur].every((x) => refuses(x) && jsonTakes(x)) && refuses(bad);
            const good = b('{"a":1,"b":[true,null,"\\u00e9"],"c":{"d":2}}');
            const r = RST.tryParseEvidence(good, "probe");
            const agrees = r.refused === null
              && JSON.stringify(r.value) === JSON.stringify(JSON.parse(good.toString("utf8")));
            /* AND THE SELFTEST IS THE READER'S OWN FALSIFIER, RUN. */
            const self = RST.tryParseEvidence(b("["), "probe").refused !== null;
            return stricter && agrees && self;
          }, null) === true;

          /* P4.7.7. AND THE RUN RECORD'S OWN VOCABULARY IS CLOSED — the one
             evidence shape P4.7.6 left open, in the record the RESULT is about.
             Measured on the frozen primitives and on the LIVE record: the record
             as it stands draws zero shape problems, and the same record with
             `verdict_override` added draws one; the three retired seats cannot
             return; and `role` is a vocabulary rather than a string to hash. */
          const runVocabularyClosed = !!RST && !!runRec && probe(() => {
            const classified = Object.values(RST.RUN_MEMBERS)
              .every((v) => ["CHECKED", "DERIVED"].includes(v))
              && ["instrument_files", "note", "supersedes", "abort_reason"]
                .every((k) => !(k in RST.RUN_MEMBERS))
              && Object.values(RST.RUN_ADAPTER_MEMBERS).every((v) => v === "CHECKED")
              && [...RST.ROLES].sort().join("|") === "candidate|reference";
            const honest = RST.runProblems(runRec).length === 0;
            const seats = ["instrument_files", "note", "supersedes", "abort_reason",
              "verdict_override"]
              .every((k) => RST.runProblems({ ...runRec, [k]: "x" }).length > 0);
            const role = RST.runProblems({ ...runRec,
              adapters: (runRec.adapters ?? []).map((a) => ({ ...a, role: "arbiter" })) }).length > 0;
            return classified && honest && seats && role;
          }, null) === true;

          /* P4.7.8. THE MOUNT IS A CLOSED ARTIFACT, MEASURED ON THE PACKAGE
             PRIMITIVES AND IN BOTH DIRECTIONS. The honest spec tree must walk to
             zero non-regular entries; a scratch tree containing a symlink must
             draw one, INCLUDING a link that points inside itself; and
             verifyPackageAt must refuse a mount that gained a file. Against
             P4.7.7 the walk followed links, so a symlink to a round ledger was
             manifested with a digest and delivered into the clean room. */
          const mountIsClosed = !!PKG && probe(() => {
            const live = PKG.walkPackage(specDir);
            if (live.entries.length !== 0 || live.files.length === 0) return false;
            const scratch = mkdtempSync(join(tmpdir(), "grid-mount-"));
            try {
              writeFileSync(join(scratch, "real.md"), "# a regular file\n");
              const clean = PKG.walkPackage(scratch);
              symlinkSync("real.md", join(scratch, "inside.md"));
              const linkedIn = PKG.walkPackage(scratch);
              symlinkSync("/etc/hostname", join(scratch, "outside.md"));
              const linkedOut = PKG.walkPackage(scratch);
              /* AND THE CHANNEL IS SEPARATE FROM `leaks`, because a filesystem
                 object that does not belong is not forbidden CONTENT. */
              const separate = "entries" in PKG.computePackageAt(scratch)
                && typeof PKG.verifyPackageAt === "function";
              const mountRefusesAnExtra = (() => {
                const before = PKG.computePackageAt(scratch).blind_package_id;
                return PKG.verifyPackageAt(scratch, before).length > 0;   /* links present */
              })();
              return clean.entries.length === 0 && clean.files.length === 1
                && linkedIn.entries.length === 1 && linkedOut.entries.length === 2
                && separate && mountRefusesAnExtra;
            } finally { rmSync(scratch, { recursive: true, force: true }); }
          }, null) === true;

          /* P4.7.9. AND A CLOSED FILE SET IS NOT A PRIVATE OBJECT. Measured on
             the primitives, in both directions: an honest scratch package walks
             clean; an EMPTY directory no manifested file lives in is refused
             (its bytes are none, so every digest passed over it); a HARD LINK to
             identical bytes is refused though the digest is correct; a SYMLINK
             standing in for the root is refused before the tree is read; and two
             paths differing only by case are refused, because on a
             case-insensitive filesystem they are ONE object. */
          const mountIsPrivate = !!PKG && probe(() => {
            const scratch = mkdtempSync(join(tmpdir(), "grid-priv-"));
            const outside = mkdtempSync(join(tmpdir(), "grid-priv-out-"));
            try {
              mkdirSync(join(scratch, "sub"));
              writeFileSync(join(scratch, "sub", "real.md"), "# a regular file\n");
              const clean = PKG.walkPackage(scratch);
              if (clean.entries.length !== 0 || clean.files.length !== 1
                || clean.dirs.length !== 1) return false;
              /* AN EMPTY DIRECTORY. */
              mkdirSync(join(scratch, "IGNORE_THE_SPEC"));
              const withDir = PKG.walkPackage(scratch);
              rmSync(join(scratch, "IGNORE_THE_SPEC"), { recursive: true });
              /* A HARD LINK TO IDENTICAL BYTES. */
              const victim = join(scratch, "sub", "real.md");
              cpSync(victim, join(outside, "shared"));
              rmSync(victim);
              linkSync(join(outside, "shared"), victim);
              const linked = PKG.walkPackage(scratch);
              rmSync(victim);
              writeFileSync(victim, "# a regular file\n");
              /* A CASE-FOLD COLLISION. */
              writeFileSync(join(scratch, "sub", "REAL.md"), "# a regular file\n");
              const folded = PKG.walkPackage(scratch);
              rmSync(join(scratch, "sub", "REAL.md"));
              /* A SYMLINK AS THE ROOT. */
              const link = join(outside, "root-alias");
              symlinkSync(scratch, link);
              const aliasRoot = PKG.walkPackage(link);
              /* AND THE VERIFIER HANDS BACK THE BYTES IT VERIFIED, so a caller
                 need not re-open by name — the half no structural check can do. */
              const loaded = PKG.loadVerifiedPackage(scratch, null);
              const servesBytes = loaded.problems.length === 0
                && loaded.bytes instanceof Map
                && loaded.bytes.get("sub/real.md")?.toString("utf8") === "# a regular file\n"
                && typeof loaded.realpath === "string";
              return withDir.entries.some((e) => /no manifested file lives in/.test(e))
                && linked.entries.some((e) => /filesystem links/.test(e))
                && folded.entries.some((e) => /differ only by case/.test(e))
                && aliasRoot.entries.some((e) => /root .* is itself a SYMBOLIC LINK/.test(e))
                && aliasRoot.files.length === 0
                && servesBytes;
            } finally {
              rmSync(scratch, { recursive: true, force: true });
              rmSync(outside, { recursive: true, force: true });
            }
          }, null) === true;

          /* P4.7.2 (C). THE ONE FACT THE UNFROZEN SIDE STILL SUPPLIES IS
             SELF-AUTHENTICATING. `holdout_score.mjs` names a directory and
             nothing else; the frozen instrument re-digests whatever it is handed
             and compares it with the release's commitment, so a wrapper that
             lied about where the secret lives fails at HOLDOUT-COMMITMENT rather
             than measuring something else. Measured both ways.

             THE CHALLENGE SET IS NOT STAGED INTO 392 SCRATCH TREES, and that is
             deliberate: it is the secret this whole round exists to keep, and
             copying it into a case tree for a probe no forgery perturbs would
             spread it for nothing. Absent here means NOT MEASURED, named; the
             canonical run measures it, and so does HOLDOUT-COMMITMENT on every
             `make governance`. */
          const holdoutHere = existsSync(A("holdout"));
          const secretPathSelfAuthenticating = !holdoutHere ? null
            : (!!HRUN && !!release && probe(() => {
              const right = HRUN.commitmentOf(A("holdout"), specDir);
              const wrong = HRUN.commitmentOf(join(specDir, "vectors"), specDir);
              return right === release.holdout_commitment && wrong !== release.holdout_commitment;
            }, null) === true);

          ok(ncSrc.length > 0 && ncFlattens.length === 0 && addressIsNotAWarrant
             && oracleFrozen && specGrammarAgrees && specBound
             && releaseArchived && releaseIdBindsProtocols && scorerIsImplementationFree
             && instrumentIsFrozen && blindPackageBound && scoreGateDelegates
             && runStateFrozen && authorityBoundToWorld && terminalWitnessed
             && conformanceReplayed !== false && evidenceUnambiguous
             && evidenceBytesUnambiguous && runVocabularyClosed && mountIsClosed
             && mountIsPrivate
             && statusIsWitnessed !== false
             && secretPathSelfAuthenticating !== false
             && storeIsNotTrusted && wireIsCanonical && rootGrammarEnforced
             && policyIsCheckerOwned && warrantVocabularyRefused && referenceNotInClaimId
             && storeIsConfined && claimIdStillMovesWithTheCertificate && chainlessIsNotCitable
             && wireIsBytes && rootIsBounded && inputReadOnce,
            `NESTED COMPOSITION must keep CLAIM, REFERENCE, EVIDENCE, STRUCTURE and VERIFIER ` +
            `EXECUTION apart, and never let one stand in for another. THE PARENT CANNOT FLATTEN ` +
            `[flattening-imports=${ncFlattens.length === 0}]: nest_check.mjs directly imports ` +
            `[${ncImports.join(", ")}] and none of [${FLATTENING.join(", ")}]. A CONTENT ADDRESS ` +
            `IS NOT A WARRANT [nest-child-refused=${addressIsNotAWarrant}]: a child whose own ` +
            `checker refuses it, cited honestly and stored under its own real root, must still be ` +
            `refused. THE STORE IS NOT TRUSTED ` +
            `[nest-artifact-root-mismatch=${storeIsNotTrusted}]. THE WIRE IS CANONICAL ` +
            `[nest-artifact-non-canonical=${wireIsCanonical}]: a DUPLICATE member name, which ` +
            `JSON.parse resolves in favour of the last one, must be refused rather than ` +
            `reparsed — P4 AUTHENTICATED such bytes as the honest artifact, and a second ` +
            `implementation keeping the first duplicate would disagree about which object a root ` +
            `names. AN UNTRUSTED CITATION MAY NOT STEER A READ ` +
            `[nest-artifact-root-malformed=${rootGrammarEnforced}] and the STORE ITSELF is confined ` +
            `[store-answers-only-roots=${storeIsConfined}]: P4's store built a path from ` +
            `whatever string arrived and read a megabyte from outside itself. THE POLICY IS THE ` +
            `CHECKER'S [nest-policy-weakened=${policyIsCheckerOwned}]: a caller asking for a ` +
            `LOOSER bound is refused, where P4 obeyed max_depth:1000 and verified a chain its own ` +
            `ceiling rejects. THE VOCABULARY IS CLOSED ` +
            `[nest-vocabulary-unknown:warrant=${warrantVocabularyRefused}]. REFERENCE IS NOT CLAIM ` +
            `[nest-vocabulary-unknown:artifact_root=${referenceNotInClaimId}]: an operand may not ` +
            `carry an address at all, which is what keeps nested_claim_sem_id blind to one — and ` +
            `it must still move when the CERTIFICATE moves ` +
            `[claim-id-moves-with-certificate=${claimIdStillMovesWithTheCertificate}]. Against ` +
            `P4, rewording one annotation on a leaf renamed the theorem at every level above it. AND ` +
            `A COMPOSITION MUST BE CITABLE AT ALL ` +
            `[certificate-incomplete:chain_ids=${chainlessIsNotCitable}]. THE RELEASE IDENTITY ` +
            `BINDS THE PROTOCOL IDENTIFIERS, MEASURED ` +
            `[release-id-binds-protocols=${releaseIdBindsProtocols}]: renaming all three protocols ` +
            `must MOVE spec_release_id, and until P4.6 it did not — the preimage was built by a ` +
            `JSON.stringify replacer ARRAY, an allowlist applied RECURSIVELY, so the nested ` +
            `protocol map serialised as {} and the forged release kept the honest identity, ` +
            `byte for byte. AND A RELEASE IS AN IMMUTABLE OBJECT, MEASURED RATHER THAN DECLARED ` +
            `[release-archived=${releaseArchived}]: releases/<spec_release_id>.json exists and ` +
            `holds the SAME BYTES as the pointer beside it. This register's own evidence claimed ` +
            `that archive for a full round while no such directory existed and issuance overwrote ` +
            `one file. AND THE SCORER LOADS NO IMPLEMENTATION ` +
            `[scorer-implementation-free=${scorerIsImplementationFree}]: holdout_score_core.mjs ` +
            `imports [${scorerImports.join(", ") || "nothing"}] — node builtins and one sibling ` +
            `that imports nothing, so no canonicaliser, no store, no bundle builder, no checker. ` +
            `P4.5 printed that the scorer knew no TRVM while the executable imported three of its ` +
            `modules and could only ever score itself. AND THE INSTRUMENT IS CONTENT-BOUND ` +
            `[instrument-frozen=${instrumentIsFrozen}, list-agrees=${instrumentListAgrees}]: the ` +
            `evidence reader, the scorer, the runner, both schemas and ` +
            `the synthetic fixtures live INSIDE the experiment surface, so editing one scorer byte ` +
            `moves experiment_digest, therefore spec_release_id, therefore the pinned run. Against ` +
            `P4.6, forcing every real predicate true left the fixture, the holdout, the release and ` +
            `the run ALL GREEN. THE DELIVERED BYTES HAVE THEIR OWN IDENTITY ` +
            `[blind-package-bound=${blindPackageBound}]: requirements/open/ is handed to the ` +
            `implementer and excluded from spec_digest by construction, so editing it moved nothing ` +
            `at all until bpkg existed — and governance, the holdout, the ledgers and the briefs ` +
            `are PROVEN absent from the package rather than promised to be. AND THE GATE THAT HOLDS ` +
            `THE SECRET DELEGATES [score-gate-delegates=${scoreGateDelegates}]: it defines no ` +
            `scorer of its own, because a delegation that can be quietly un-delegated is not one. ` +
            `AND THE MEASUREMENT AUTHORITY IS FROZEN WHOLE ` +
            `[run-state-frozen=${runStateFrozen}]: the state machine, the run identity, the ` +
            `transition preconditions and the receipt chain live INSIDE the experiment surface, and ` +
            `this probe re-derives the pinned run's own id with the FROZEN function. P4.7.1 moved ` +
            `the reveal gate into the frozen runner and then handed it, from mutable governance/, ` +
            `the very fact it gates on: one edit passing the literal "REVEALED" gave a ` +
            `CANDIDATE_FROZEN candidate all ten hidden constructions with --reveal never called. A ` +
            `STATUS IS A CLAIM UNTIL A RECEIPT CHAIN WITNESSES IT ` +
            `[status-witnessed=${statusIsWitnessed ?? "NOT MEASURED — receipts/ is not staged into this tree"}], measured BOTH WAYS: the record as it stands ` +
            `draws zero chain problems, and the same record with status moved to REVEALED and ` +
            `run_id recomputed by the tree's own exported function — the exact attack, green ` +
            `against P4.7.1 with ZERO receipts in existence — draws at least one. AND THE ONE FACT ` +
            `THE UNFROZEN SIDE STILL SUPPLIES IS SELF-AUTHENTICATING ` +
            `[secret-path-self-authenticating=${secretPathSelfAuthenticating ?? "NOT MEASURED — the challenge set is not staged into this tree"}]: the wrapper names a ` +
            `DIRECTORY, the frozen instrument re-digests whatever it is handed, and a different ` +
            `directory does not reproduce the release's holdout commitment. ` +
            `AND AN AUTHORITY FACT IS BOUND TO THE SUBJECT IT IS EXERCISED OVER ` +
            `[authority-bound-to-world=${authorityBoundToWorld}]: the state root is DERIVED from ` +
            `the world and ignores an override, and every path a run names must resolve inside ` +
            `that world. Against P4.7.2 a --state-root flag made the authority selectable, so a ` +
            `REVEALED copy of the record in /tmp authorized the CANONICAL candidate and it received ` +
            `all ten hidden constructions while the canonical run read CANDIDATE_FROZEN — the ` +
            `NON-CANONICAL stamp stopped that measurement COMPLETING the real run and stopped ` +
            `nothing else, because completion isolation and secret-release isolation are different ` +
            `invariants. AND A TERMINAL CLAIM IS WITNESSED BY ITS MEASUREMENT ARTIFACT ` +
            `[terminal-witnessed=${terminalWitnessed}]: a COMPLETE run must show a RESULT that ` +
            `names it, whose subject set is exactly the run's, whose archived observation documents ` +
            `re-digest from their stored bytes, and whose interoperability comparison REPLAYS from ` +
            `those bytes to zero findings. Against P4.7.3 a hand-written COMPLETE transition over a ` +
            `candidate that only ran \`exit 99\` verified green with no RESULT anywhere — and so ` +
            `did deleting the RESULT after an honest completion, which is the half that matters, ` +
            `because a digest identifies an artifact and does not make an absent one re-checkable. ` +
            `AND THE TERMINAL VERIFIER REPLAYS BOTH THINGS COMPLETION CLAIMS ` +
            `[conformance-replayed=${conformanceReplayed ?? "NOT MEASURED — the challenge set is not staged into this tree"}]: ` +
            `P4.7.4 replayed interoperability and NOT conformance, so two archived observations ` +
            `containing {} agreed perfectly, every digest matched, and the RESULT's predicate ` +
            `totals were simply read — while the frozen scorer says all ten committed challenges ` +
            `are unobserved. Every total is DERIVED from the challenge set and the scorer now, and ` +
            `an implementation label is an identifier rather than a path, because the label is what ` +
            `names the subject's archived evidence. AND AN AUTHENTICATED EVIDENCE ARTIFACT HAS ` +
            `AND THE CLEAN-ROOM MOUNT IS A CLOSED ARTIFACT ` +
            `[mount-is-closed=${mountIsClosed}, mount-is-private=${mountIsPrivate}]: the package ` +
            `walk is over lstat and REFUSES a ` +
            `symbolic link, a FIFO, a socket or a device — including a link pointing INSIDE the ` +
            `package, because a special case is a place to hide — and every file's realpath must ` +
            `lie inside the package root. Against P4.7.7, innocent.md -> ../../../governance/` +
            `round-11-ledger.md drew ZERO leaks, was manifested with a digest, and read back through ` +
            `the emitted mount as the round ledger, because the walk, the leak detector and the ` +
            `post-emission re-walk all used statSync and agreed by sharing one wrong answer; and ` +
            `BLIND-PACKAGE.json was written INSIDE the mount and EXEMPTED from the equality check, ` +
            `so 59 files were manifested and 60 delivered. EXACTLY ONE READING AT THE BYTE BOUNDARY ` +
            `[evidence-bytes-unambiguous=${evidenceBytesUnambiguous}]: the instrument's own strict ` +
            `reader refuses a duplicate object member, an unpaired surrogate and invalid UTF-8 — all ` +
            `three of which JSON.parse takes — and reads everything it ACCEPTS exactly as JSON.parse ` +
            `does, so it is STRICTER than JSON and never DIFFERENT from it. Against P4.7.6, ` +
            `"status":"REVEALED","status":"PINNED" in the shipped record verified green, because the ` +
            `uniqueness and shape checks ran over a value JSON.parse had already collapsed to the ` +
            `LAST duplicate while a first-occurrence reader saw the other status. AND THE RUN ` +
            `RECORD'S OWN VOCABULARY IS CLOSED [run-vocabulary-closed=${runVocabularyClosed}]: ` +
            `every member DERIVED or CHECKED with no NON_AUTHORITATIVE seat at all, role a ` +
            `vocabulary rather than a string bound into a hash, and instrument_files, note, ` +
            `supersedes and abort_reason unable to return — P4.7.6 gave the RESULT and the receipts ` +
            `eight closed shapes and left blind-run.json, the record they are about, accepting ` +
            `verdict_override beside status PINNED. AND EVERY COLLECTION [evidence-unambiguous=${evidenceUnambiguous}]: every collection ` +
            `keyed by an identity is checked for UNIQUENESS before it is indexed, and every shape ` +
            `is CLOSED with each member DERIVED, CHECKED or NON_AUTHORITATIVE. Against P4.7.5 a ` +
            `bogus subject row inserted BEFORE the genuine one collapsed under Map construction ` +
            `with the last one winning, so the artifact proved the right measurement while showing ` +
            `a reader who resolves duplicates by first occurrence a different one — P4.1's ` +
            `duplicate wire member, in an array. ` +
            `THE WIRE IS UTF-8 BYTES ` +
            `[nest-artifact-invalid-utf8=${wireIsBytes}]: P4.1 decoded a raw 0xFF to U+FFFD before ` +
            `the canonical equality could see it, so two byte strings were one artifact again. THE ` +
            `ROOT IS NOT EXEMPT FROM ITS OWN POLICY [nest-budget-exceeded=${rootIsBounded}]: P4.1 ` +
            `bounded only what came through the CAS, and verified a 9.4 MB root under an 8 MiB ` +
            `ceiling. AND THE VERIFIER OWNS ITS INPUT [input-read-once=${inputReadOnce}]: a live ` +
            `getter is read EXACTLY ONCE by each checker, so no later read can disagree with the ` +
            `one the verdict is about — against P4.1 it was read 2 and 3 times on two protocols, ` +
            `both VERIFIED, both objects afterwards saying something the checker never accepted. THE ` +
            `CONFORMANCE ORACLE IS FROZEN AND STILL MATCHED ` +
            `[conformance-oracle-frozen=${oracleFrozen}]: the expected roots are READ from the ` +
            `committed corpus at spec revision ${frozen?.spec_revision ?? "?"} and compared with ` +
            `what this implementation computes — an implementation that regenerates its own answer ` +
            `key has not been tested against anything. AND THE NORMATIVE GRAMMAR AGREES WITH THE ` +
            `CHECKER'S OWN [spec-grammar-agrees=${specGrammarAgrees}]: deleting a field from the ` +
            `checker, its enforcement and the producer leaves the field audit reporting 45/45 while ` +
            `the protocol still has 46 fields. AND THE NORMATIVE PROSE IS BOUND TO A RELEASE ` +
            `[spec-release-bound=${specBound}]: every normative document is digested into ` +
            `SPEC-RELEASE.json, so editing the citation formula in a Markdown file — the one ` +
            `surface a blind implementer reads and no gate executes — fails here, where before it ` +
            `failed nowhere`);
        }

        // ── B1.2.1: emit() must not be a HIDDEN semantic relation ─────────
        // B1.2 named instantiation's codomain in PROSE ("… via emit()"), so
        // changing the add combinator changed the executable term's bytes and
        // left INSTANTIATION_SEM_ID, the template id and the template-encoding
        // id all standing still. A semantic dependency behind a symbol name.
        // DATA for the bindings; TEXT-TIER for the one thing data cannot show —
        // that the id is hashed over TARGET_ENCODING's BYTES rather than a label.
        ok(L.TARGET_EXECUTABLE_ENCODING_SEM_ID?.startsWith("xenc-") &&
           L.EMISSION_SEMANTICS?.codomain_encoding_sem_id === L.TARGET_EXECUTABLE_ENCODING_SEM_ID &&
           /TRVM-TARGET-EXECUTABLE-ENC-v1\|" \+ canonicalBytes\(TARGET_ENCODING\)/.test(lowNoc),
          "the EXECUTABLE target encoding must be CONTENT-BOUND and named as instantiation's codomain " +
          "by id. Naming it 'TRVM-TERM-CANON-v1 … via emit()' in prose is a label anyone may claim — " +
          "the objection the primitive ruling already raised against a bare componentReachability — " +
          "and it let the rule deciding how church(n) and add(a,b) become interaction-net terms change " +
          "with the identity of the relation that produces them intact");
        // …AND THE DUAL. Lowering carried the whole TARGET_ENCODING, a
        // pre-template leftover: an emitter change re-identified every
        // LoweringReceipt ever issued, for a relation lowering does not perform.
        // Same class as the receipt still ending at target_term_sem_id, which
        // B1.2 fixed one declaration away and missed here.
        // DATA.
        ok(!("target_encoding" in (L.LOWERING_SEMANTICS ?? {})) &&
           typeof L.LOWERING_SEMANTICS?.op_lowering_rules === "object",
          "LOWERING_SEMANTICS must NOT bind the executable encoding, and must state its per-op map " +
          "instead. Lowering's codomain is the TEMPLATE; binding it to an encoding two layers " +
          "downstream makes an emitter change re-identify a relation that did not change. Removing " +
          "the binding exposed that the map was never written down — `lowered_ops` says WHICH ops " +
          "lower and the template encoding says what the nodes ARE, but nothing said a const becomes " +
          "a church node, so const(n) -> church(n+1) contradicted no sentence in the hashed semantics");
        // THE REFUSAL VOCABULARIES WERE CROSSED. TARGET_ENCODING listed four
        // `lower-*` source-fragment refusals that cannot arise while emitting,
        // and lowering claimed emit's two, neither reachable from lower().
        {
          // DATA. This was two hand-sliced source windows — the device that let
          // consumed_inputs be answered by the wrong field one round later.
          // B7.1r MOVED THE OWNER, so this assertion moved with it. The
          // emission refusals sat in TARGET_ENCODING and that was the leak
          // GPT ruled on: a LANGUAGE does not refuse, a MAP INTO it refuses.
          // They live in EMISSION_RULES now, and the codomain record must hold
          // NO refusal list at all — a stronger form of "no source refusals
          // here", and one that cannot be satisfied by a list with the right
          // prefixes in it.
          const mapR = L.EMISSION_RULES?.refusals ?? [];
          const lowR = L.LOWERING_SEMANTICS?.refusal_semantics ?? [];
          ok(L.TARGET_ENCODING?.refusals === undefined &&
             !mapR.some((r) => r.startsWith("lower-")) && mapR.includes("emit-unbound-port") &&
             !lowR.some((r) => r === "emit-unbound-port" || r === "template-malformed") &&
             lowR.length > 0 && lowR.every((r) => r.startsWith("lower-")),
            "the refusal vocabularies must belong to the records that own them, and after B7.1r the " +
            "EXECUTABLE ENCODING OWNS NONE: a language does not refuse, a MAP into it refuses when " +
            "something in its domain has no image. TARGET_ENCODING must carry no refusal list at " +
            "all and EMISSION_RULES must carry emission's. The EXECUTABLE " +
            "encoding's refusals are EMISSION's; a source-fragment refusal such as lower-negative " +
            "cannot arise while emitting, and once these bytes carry an identity, renaming one would " +
            "move the executable encoding's id without touching the encoding. Symmetrically lowering " +
            "may not claim emit-unbound-port or template-malformed: lower() emits only zero-port " +
            "templates it built itself, so neither is reachable from it");
        }
        ok(/export const SUPERSEDED_CODOMAIN_SEM_IDS/.test(lowNoc) &&
           /lsem-d95ee1cbc0e8f37806adf8fc9db377afc1e448ac05087254841e920651d76814/.test(lowSrc),
          "the B1.2 identities must be KEPT, like B1.1's. They were bound to the wrong CODOMAIN " +
          "rather than to lifecycle — the same family, not the same instance — and a record that " +
          "quietly replaced them would be the record-rewriting these corrections are about");
        ok(/export const IMPLEMENTED_LOWERED_OPS/.test(lowNoc) && !/\bLOWERED_OPS\b/.test(
             lowNoc.replace(/IMPLEMENTED_LOWERED_OPS/g, "").replace(/lowered_ops/g, "")),
          "the implemented op list must be named IMPLEMENTED_LOWERED_OPS. `LOWERED_OPS` read as the " +
          "fragment itself while sitting beside LOWERING_SEMANTICS.lowered_ops holding a DIFFERENT " +
          "and larger list — and distinguishing SPECIFIED from IMPLEMENTED is the whole conceptual " +
          "content of B1.2, so the one name that blurred them was the wrong name to keep");
        // THE MECHANISM, NOT A VALUE. This required `exercised: false` and a
        // `why_not:` to exist — true while two nodes were unexercised and false
        // the moment B2 exercised them, so the assertion would have failed for
        // the round that FIXED what it was guarding. Requiring an exercised
        // flag on EVERY node, and a why_not on every node that lacks one, holds
        // in both states and is what the check actually means.
        // DATA. Counting two regex families against each other was a proxy for
        // "every node has a flag"; the array says so directly.
        ok(Array.isArray(L.REFINEMENT_CHAIN) && L.REFINEMENT_CHAIN.length > 0 &&
           L.REFINEMENT_CHAIN.every((n) => typeof n.id === "string" &&
             typeof n.exercised === "boolean" &&
             (n.exercised || typeof n.why_not === "string")),
          "the identity chain must be MACHINE-READABLE with an exercised flag per node, so the " +
          "anti-collapse set is derived rather than hand-typed. B1.2 added target_template_sem_id to " +
          "the chain and not to the set, and the check went on proving a six-way claim about a " +
          "seven-node chain — green, and one node short of its own name");
        // ── B2: the inputs relation becomes executable ────────────────────
        // THE RULES ARE STRUCTURAL AND lower() INTERPRETS THEM. GPT's B2 ruling:
        // a normative English sentence beside a hand-coded implementation is
        // TWO artifacts that can disagree, and only one of them is hashed. The
        // table is now what runs, so a rule cannot be edited without changing
        // behaviour and behaviour cannot change without moving LOWERING_SEM_ID.
        ok(/op_lowering_rules: Object\.freeze\(\{\s*const: Object\.freeze/.test(lowNoc) &&
           /from_field: "value"/.test(lowNoc) && /recurse_field: "a"/.test(lowNoc) &&
           /transform: "identity"/.test(lowNoc) &&
           /LOWERING_SEMANTICS\.op_lowering_rules\[node\.op\]/.test(lowNoc),
          "op_lowering_rules must be STRUCTURAL and lower() must INTERPRET it. English rules beside a " +
          "hand-coded implementation are two artifacts that can disagree while only one is hashed — " +
          "the same defect as naming a codomain in prose, one layer in. `transform: \"identity\"` is " +
          "the no-normalization ruling made structural: a source name reaches the port unchanged " +
          "because there is no other transform the table can name");
        // lower() MUST NOT RETURN AN EXECUTABLE TERM. Keeping the convenience
        // field would leave an official path beside a shortcut, with every
        // future reader having to remember which carried the semantics.
        // SCOPED TO lower()'s BODY. The first version of this tested the whole
        // file for `target_term: emit(` and matched instantiate()'s own
        // emission — a check that would have refused the correct architecture
        // while claiming lowering still had a shortcut.
        // BEHAVIOURAL. Call it and look at what comes back, rather than slicing
        // the source — the version that sliced the WHOLE file matched
        // instantiate()'s own emission and would have refused the correct shape.
        ok(!("target_term" in (L.lower?.({ op: "const", value: 1 }) ?? { target_term: 1 })) &&
           typeof L.instantiate === "function",
          "lower() must not return a target_term. Once emission belongs to the instantiation " +
          "relation, a convenience field emitting closed templates is a SECOND PATH to an executable " +
          "term — the official one through instantiate() and a shortcut through lowering. That is how " +
          "a hidden second mechanism comes back, and the equality belongs in a regression theorem " +
          "rather than in an API");
        // AND instantiate() MUST NOT MINT THE ID OF ITS OWN OUTPUT.
        {
          // BEHAVIOURAL: instantiate a real template and inspect the result.
          const probe = L.lower?.({ op: "const", value: 2 });
          const inst = probe?.ok ? L.instantiate(probe.template, {}) : null;
          ok(inst?.ok === true && !("target_term_sem_id" in inst) && !("target_term" in inst) &&
             (L.INSTANTIATION_RECEIPT_FIELDS ?? []).join() ===
               "target_template_sem_id,instantiation_sem_id,inputs_sem_id,closed_template_sem_id" &&
             (L.EMISSION_RECEIPT_FIELDS ?? []).join() ===
               "closed_template_sem_id,emission_sem_id,target_term_sem_id" &&
             (() => { try { L.instantiationReceipt("a", "b", undefined); return false; }
               catch (e) { return /^instantiation-receipt-incomplete/.test(e.message); } })() &&
             // and the same obligation on EMISSION's receipt, which the first
             // conversion left unmeasured — the battery found it immediately
             L.emissionReceipt?.length === 2 &&
             (() => { try { L.emissionReceipt("a", undefined); return false; }
               catch (e) { return /^emission-receipt-incomplete/.test(e.message); } })(),
            "instantiate() must not compute target_term_sem_id. An instantiator that emitted bytes " +
            "AND certified their semantic id would produce the artifact and the certificate from one " +
            "source, so a wrong emission would carry a matching id and verify against itself. The " +
            "kernel canonicalises the bytes and the receipt is built around that id — the same " +
            "discipline that keeps a LoweringReceipt from minting the term's identity");
        }
        // DATA for WHICH record holds it, TEXT-TIER for the four conditions it
        // must name — those are normative prose and prose is a text property.
        ok(typeof L.INSTANTIATION_STATUS?.emission_split_trigger === "string" &&
           !("emission_split_trigger" in (L.INSTANTIATION_SEMANTICS ?? {})) &&
           /independently VERSIONED or REPLACEABLE/.test(
             L.INSTANTIATION_STATUS?.emission_split_trigger ?? "") &&
           /EXTERNALLY OBSERVED/.test(L.INSTANTIATION_STATUS?.emission_split_trigger ?? ""),
          "the emission SPLIT TRIGGER must live in STATUS and carry all four conditions. B1.2.1 put a " +
          "two-condition version inside INSTANTIATION_SEMANTICS, which re-committed B1.1's own " +
          "finding: a governance note inside a relation identity re-identifies the relation when it " +
          "is reworded. GPT added independently-versionable and externally-observed-intermediate at " +
          "B2, and those are the two that fire first — the moment two emitters are compared over one " +
          "closed template, an emitter upgrade re-cutting the identity of PORT SUBSTITUTION is wrong");
        // ── B2.1: the split trigger fired, and two defects behind it ──────
        ok(/entry_snapshot:/.test(lowNoc) &&
           /const own = ownCanonical\(inputs\)/.test(lowNoc) &&
           /const tmpl = ownCanonical\(template\)/.test(lowNoc) &&
           /inputsSemId\(own\)/.test(lowNoc),
          "instantiate() must SNAPSHOT both arguments at entry and read only the snapshot. It read " +
          "the caller's inputs twice — once to bind values and once to compute inputs_sem_id — so a " +
          "getter answering 2 then 999 produced a term meaning x=2 beside an identity committing to " +
          "{x:999}. The relation misbound its own input identity while nothing about the runtime was " +
          "wrong: round 27A.1's entry-snapshot rule arriving in the compiler layer");
        // DATA for the vocabulary's shape, BEHAVIOURAL for the refusals it must
        // still produce, TEXT-TIER for the one code-shape obligation — that the
        // interpreter READS the record — which would need a JS parser.
        ok(typeof L.LOWERING_SEMANTICS?.predicate_semantics === "object" &&
           Object.values(L.LOWERING_SEMANTICS?.predicate_semantics ?? {})
             .every((d) => typeof d === "object" && typeof d.kind === "string") &&
           Object.values(L.LOWERING_SEMANTICS?.transform_semantics ?? {})
             .every((d) => typeof d === "object" && typeof d.kind === "string") &&
           L.lower?.({ op: "const", value: 1.5 })?.reason === "lower-non-integer-constant" &&
           L.lower?.({ op: "const", value: -1 })?.reason === "lower-negative" &&
           /LOWERING_SEMANTICS\.predicate_semantics\[p\.holds\]/.test(lowNoc),
          "the rule vocabulary's MEANING must be content-bound, not a table of bare names bound to " +
          "JavaScript functions. Redefining `integer` as always-true changed behaviour — const(1.5) " +
          "lowered instead of refusing — and moved no identity; `identity` could have been made to " +
          "normalize a source input name, silently undoing the port ruling. The vocabulary stays " +
          "CLOSED and its definitions are DATA");
        // DATA + BEHAVIOURAL. The previous version tested for the STRING
        // "ctmpl-", which also appears in codomain_identity_domain — so renaming
        // the real constructor's prefix left it green. Calling the constructor
        // cannot be fooled that way.
        ok(typeof L.EMISSION_SEMANTICS === "object" &&
           L.EMISSION_SEM_ID?.startsWith("esem-") &&
           L.closedTemplateSemId?.(L.T.church(1))?.startsWith("ctmpl-") &&
           L.closedTemplateSemId?.(L.T.church(1)) !== L.targetTemplateSemId?.(L.T.church(1)) &&
           L.INSTANTIATION_SEMANTICS?.codomain_encoding_sem_id ===
             L.TARGET_TEMPLATE_ENCODING_SEM_ID,
          "EMISSION must be its own relation with its own identity, and instantiation must END AT " +
          "THE CLOSED TEMPLATE. B1.2.1 declared four conditions for this split and B2 tripped all " +
          "four: emit() is independently reused, I-4a is a theorem about emission alone, the " +
          "executable encoding is independently versioned, and instantiate() returns the closed " +
          "template to its caller. The closed template gets its OWN identity domain (ctmpl-) even " +
          "where its bytes equal an open template's, because what the compiler produced and what an " +
          "invocation closed are different things");
        // BEHAVIOURAL, plus B2.1.1's owned entry points.
        // B2.1.1: THE VERIFIER MAY NOT AUTHENTICATE A SECOND SNAPSHOT.
        // TEXT-TIER, and marked as such: this is a code-shape obligation — "the
        // owned verifier never reaches back to a caller object" — which needs a
        // JS parser to assert properly. The behavioural half is the witness in
        // lowering_check, which drives a hostile template through and requires
        // one traversal.
        ok(/return verifyInstantiationReceiptOwned\(\.\.\.owned\)/.test(lowNoc) &&
           /export function verifyInstantiationReceiptOwned/.test(lowNoc) &&
           /export function verifyEmissionReceiptOwnedAgainst/.test(lowNoc) &&
           !/targetTemplateSemId\(ownCanonical\(template\)\)/.test(lowNoc) &&
           !/closedTemplateSemId\(ownCanonical\(closed_template\)\)/.test(lowNoc) &&
           /ownCanonical\(receipt\)/.test(lowNoc),
          "the verifiers must OWN what they authenticate. B2.1 fixed the RELATION binding one " +
          "snapshot and identifying another, then shipped a verifier that verified one snapshot and " +
          "authenticated another: instantiate() snapshots the template internally and the verifier " +
          "then called targetTemplateSemId(ownCanonical(template)) on the caller's object again, so a " +
          "template answering \"x\" then \"y\" satisfied a receipt no immutable template satisfies. " +
          "The receipt is snapshot too — it arrives from whoever is asking to be believed");
        // B2.1.2: the emission verdict is RELATIVE and must be named so.
        // BEHAVIOURAL: bind a complicit oracle and require the parametric form
        // to accept it (that is what parametric MEANS), while requiring the
        // bound form to have no parameter in which one could be passed.
        {
          // A BEHAVIOURAL ASSERTION THAT CAN THROW TAKES THE WHOLE CHECKER DOWN,
          // and a stack trace is not a diagnostic — the battery sees a nonzero
          // exit with no message and reports the wrong reason. Found by a
          // forgery that made emissionReceipt refuse: calling the API is
          // stronger than reading its source AND it runs adversary-influenced
          // code, so every probe on this rung is wrapped.
          const probe = (f, fallback = null) => { try { return f(); } catch { return fallback; } };
          const bogus = probe(() => L.emissionReceipt(L.closedTemplateSemId(L.T.church(2)), "deadbeef"));
          const complicit = probe(() =>
            L.verifyEmissionReceiptAgainst(L.T.church(2), bogus, () => "deadbeef"));
          const bound = probe(() =>
            L.makeEmissionVerifier({ canonicaliseTarget: (t) => "k:" + t.length }));
          ok(bogus !== null &&typeof L.verifyEmissionReceiptAgainst === "function" &&
             typeof L.verifyEmissionReceiptOwnedAgainst === "function" &&
             L.verifyEmissionReceipt === undefined &&
             complicit?.ok === true &&
             typeof bound === "function" && bound.length === 2 &&
             probe(() => bound(L.T.church(2), bogus))?.ok === false &&
             (() => { try { L.makeEmissionVerifier({}); return false; }
               catch (e) { return e.message === "emission-verifier-no-canonicaliser"; } })(),
            "the emission verifier must NAME its relativity and offer a BOUND form. A receipt " +
            "claiming the term's identity is \"deadbeef\" verifies against an oracle that says " +
            "deadbeef — which is what a parametric verifier means, and is a dangerous thing to spell " +
            "as `verifyEmissionReceipt` returning a bare ok:true, in a tree whose recurring finding " +
            "is that a claimant must not nominate the oracle certifying the claim. `Against` in the " +
            "name; makeEmissionVerifier binds the trusted canonicaliser at a composition root so " +
            "ordinary callers have NO PARAMETER for a judge; and no alias keeps the weaker spelling " +
            "reachable, because an alias is a second path to one relation");
        }
        ok(typeof L.verifyInstantiationReceipt === "function" &&
           typeof L.verifyEmissionReceiptAgainst === "function" &&
           typeof L.verifyInstantiationReceiptOwned === "function" &&
           typeof L.verifyEmissionReceiptOwnedAgainst === "function" &&
           // ARITY, on the function object. Deleting the canonicaliser parameter
           // leaves every behavioural probe passing — undefined is not a
           // function either way — so `typeof` alone could not see it.
           L.verifyEmissionReceiptAgainst?.length === 3 && L.verifyInstantiationReceipt?.length === 3 &&
           L.verifyEmissionReceiptAgainst?.(L.T.church(1), {}, "not-a-function")?.reason ===
             "verify-emission-no-canonicaliser",
          "receipt VERIFICATION must be a production function, not test code. A relation whose only " +
          "implementation of 'does this receipt hold?' lives in its own suite is a relation nobody " +
          "else can check. Verifying instantiation needs no runtime canonicaliser now that the " +
          "relation ends at a structure this module owns; emission TAKES one as a parameter, because " +
          "the module defining a relation must not also choose the oracle that judges it");
        ok(/export const SUPERSEDED_B2_SEM_IDS/.test(lowNoc) &&
           /lsem-2014bdc8add9981442b9bbf42672a00bc477eb2b23c38918b93fdc8d9f1a99a2/.test(lowSrc),
          "the B2 identities must be kept. The witness that used to reproduce them was retired when " +
          "its premise expired, and a generation whose only evidence was a deleted test should at " +
          "least name its values");
        ok(/export const SUPERSEDED_PROSE_RULE_SEM_IDS/.test(lowNoc) &&
           /NOT A DEFECT/.test(lowSrc) &&
           /lsem-84c9344790a0403975430d270e6d567f4124cf7f848761cf19e4f997bc330244/.test(lowSrc),
          "the B1.2.1 identities must be kept AND distinguished from the two corrected generations. " +
          "B1's were overbound to lifecycle and B1.2's to the wrong codomain; these were bound " +
          "correctly to an ENGLISH expression of a correct map, so the record must say NO DEFECT is " +
          "claimed. A reader deserves to know which generation was a correction and which a refinement");
        {
          const lcSrc2 = existsSync(A("lowering_check.mjs")) ? readFileSync(A("lowering_check.mjs"), "utf8") : "";
          for (const [id, why] of [
            ["migration-preserves-the-old-bytes",
              "instantiate(template, {}) must reproduce the exact bytes the removed lower().target_term " +
              "returned. Removing a shortcut is only safe if the surviving path is proved to mean the same"],
            ["receipt-is-not-self-certified",
              "the InstantiationReceipt must be built from an id the kernel minted, and verified by " +
              "independent re-instantiation and re-canonicalization"],
            ["I-4a-allocation-is-not-semantic",
              "I-4a needs a SECOND emitter with genuinely different allocation. Asserting allocation " +
              "invariance about one emitter measures nothing"],
            ["I-4b-the-source-name-is-semantic",
              "I-4b must show the quotient did not take the source key with it, Unicode included"],
            ["I-4c-binding-has-force",
              "I-4c must run the ASYMMETRIC fixture end to end — 7 against 8 through native execution — " +
              "and the correct receipt must accept only the 7-producing term"],
            // implementing-moved-neither-id was required here until B2.1, when
            // its premise expired: it reverted the two fields B2 changed, and
            // B2.1 changed more, so keeping it would have meant growing an
            // embedded copy of the module inside its own test. The live
            // property is measured by semantic-ids-track-semantics-only.
            ["instantiation-snapshots-its-inputs",
              "instantiate() must read its arguments ONCE. Reading the caller's inputs twice let a " +
              "getter bind x=2 into the term while inputs_sem_id committed to x=999 — the relation " +
              "misbinding its own input identity, with the runtime blameless"],
            ["rule-vocabulary-is-content-bound",
              "redefining what `integer` or `identity` MEANS must move LOWERING_SEM_ID. A closed set " +
              "of bare names left the meaning in a JavaScript function body, where changing it " +
              "changed behaviour and moved nothing"],
            ["emission-is-its-own-relation",
              "an emitter change must move EMISSION's id and neither of the other two, and a " +
              "substitution change must move instantiation's and not emission's"],
            ["emission-verdict-names-its-oracle",
              "the emission verdict is relative to a caller-supplied canonicaliser, and the witness " +
              "must show the parametric form accepting a complicit oracle while the BOUND form has " +
              "no parameter in which one could be passed"],
            ["verifiers-own-what-they-authenticate",
              "a hostile template answering \"x\" then \"y\" must be traversed ONCE and its hybrid " +
              "receipt refused. B2.1's verifiers verified one snapshot and authenticated another, " +
              "which is the defect B2.1 itself closed one layer down"],
          ]) ok(new RegExp(id).test(lcSrc2), `lowering_check.mjs must carry ${id} — ${why}`);
        }
        // SCOPED TO THE SEMANTICS RECORD. Unscoped, this was satisfied by
        // instantiate()'s RETURN field of the same name once B2 wrote it — the
        // assertion guards a semantic commitment and was being answered by an
        // implementation detail. Found by the battery: consumed-inputs-collapsed
        // renamed the semantics field and grid_check still passed.
        // DATA for the field, TEXT-TIER for the phrase the record must keep.
        ok(typeof L.INSTANTIATION_SEMANTICS?.consumed_inputs === "string" &&
           L.INSTANTIATION_SEMANTICS.consumed_inputs.includes("grant-versus-footprint"),
          "instantiation must keep SUPPLIED and CONSUMED inputs distinct. That is grant-versus-" +
          "footprint from round 15 one layer down, and collapsing it now would lose the distinction " +
          "before the invocation environments get large enough to need it");
        ok(/export const INSTANTIATION_SEM_ID =/.test(lowSrc) &&
           /export const inputsSemId =/.test(lowSrc) &&
           /export const portSemId =/.test(lowSrc),
          "instantiation must have its OWN relation identity, separate from lowering's, with " +
          "inputs_sem_id for the invocation data and portSemId for the source-name-bound port. A " +
          "correct template can be instantiated with \"x\" bound to the port for \"y\", so the two " +
          "relations are independently falsifiable and must be independently identifiable");
        // ── B1.1: SEMANTICS ARE HASHED, LIFECYCLE IS NOT ──────────────────
        // B1 hashed the whole spec: flipping `implemented` moved
        // LOWERING_SEM_ID from lsem-5673108765b4… to lsem-63f98923ed13…, so B2
        // becoming BUILT would have re-identified a relation B1 froze. Round 16
        // inside the compiler specification. These are structural rather than
        // prose assertions on purpose — checking English is what the severity
        // invariant was corrected for two rounds ago.
        ok(/export const LOWERING_SEMANTICS = Object\.freeze/.test(lowSrc) &&
           /export const LOWERING_STATUS = Object\.freeze/.test(lowSrc) &&
           /export const INSTANTIATION_SEMANTICS = Object\.freeze/.test(lowSrc) &&
           /export const INSTANTIATION_STATUS = Object\.freeze/.test(lowSrc),
          "lowering.mjs must separate SEMANTICS (what the relation does) from STATUS (what the " +
          "project has done about it). One record hashed into an identity and one not");
        ok(/canonicalBytes\(LOWERING_SEMANTICS\)/.test(lowSrc) &&
           /canonicalBytes\(INSTANTIATION_SEMANTICS\)/.test(lowSrc) &&
           !/canonicalBytes\(LOWERING_SPEC\)/.test(lowSrc) &&
           !/canonicalBytes\(INSTANTIATION_SPEC\)/.test(lowSrc),
          "the semantic ids must hash the SEMANTICS records and never the combined spec. Hashing " +
          "the spec puts `implemented`, round numbers and evidence grades inside a relation's " +
          "identity, so implementing a frozen relation re-identifies it");
        ok(/TRVM-LOWERING-SEM-v2/.test(lowSrc) && /TRVM-INSTANTIATION-SEM-v2/.test(lowSrc),
          "the corrected projections must carry a NEW domain tag. Reusing v1 over different bytes " +
          "would make two different projections indistinguishable by their own labels");
        ok(/export const OVERBOUND_TRANSITIONAL_SEM_IDS/.test(lowSrc) &&
           /lsem-5673108765b400bc9abff5a7b7b8fcb4375cf9894c5dbd50201efec3df79ccbc/.test(lowSrc),
          "the overbound B1 identities must be KEPT, not erased. They were the honest ids of the " +
          "projection B1 shipped, and quietly replacing them is the record-rewriting this correction " +
          "is about");
        {
          // structural, not prose: no invocation data may appear in the relation id
          const inv = ["inputs_sem_id", "canonical_inputs", "x=5", "invocation"];
          const semBlock = lowSrc.slice(lowSrc.indexOf("export const INSTANTIATION_SEMANTICS"),
            lowSrc.indexOf("export const INSTANTIATION_STATUS"));
          ok(!inv.some((k) => new RegExp("^\\s*" + k + ":", "m").test(semBlock)) &&
             /export const inputsSemId =/.test(lowSrc),
            "INSTANTIATION_SEMANTICS must carry no invocation data — the moment `x=5` is inside the " +
            "relation id, every invocation is a different relation. The invocation gets its own " +
            "inputsSemId");
        }
        // ── B1.1: extras are IGNORED, because the source ignores them ─────
        ok(/extra_input: "IGNORED\./.test(lowSrc) && /many-to-one/.test(lowSrc) &&
           /BY CONSTRUCTION/.test(lowSrc),
          "extra canonical inputs must be IGNORED by instantiation. The SOURCE evaluator returns 2 " +
          "for input(\"x\") with {x:2, y:999}, so refusing extras at the target breaks refinement BY " +
          "CONSTRUCTION on the first program with a spare input. B1's justification — that a " +
          "many-to-one map would stop the receipt 'being a function' — is false about functions, and " +
          "the record must say so rather than quietly changing the rule");
        ok(!/instantiate-extra-input"/.test(lowSrc.slice(
             lowSrc.indexOf("semantic_refusals"), lowSrc.indexOf("INSTANTIATION_STATUS"))),
          "instantiate-extra-input must not be a SEMANTIC refusal — it was removed because it " +
          "contradicted the source language, and an instantiator may not narrow the source's input " +
          "discipline unilaterally. Doing so would need a new CORE_SEM_ID");
        ok(/REFINEMENT_SCOPE = Object\.freeze/.test(lowSrc) &&
           /program-input-missing/.test(lowSrc) && /instantiate-missing-input/.test(lowSrc),
          "the refinement claim must state its DOMAIN before B2 builds anything: fully bound input " +
          "environments, with source-refusal <-> instantiation-refusal DECLARED OPEN. The source " +
          "refuses a missing input during evaluation and instantiation refuses it before a term " +
          "exists — different layers, different codes, and refusal preservation is a separate theorem");
        ok(/fixture_is_mandatory:/.test(lowSrc) && /2\+3 == 3\+2/.test(lowSrc),
          "I-4c must MANDATE an asymmetric fixture. add(input x, input y) with x=2,y=3 gives 5 under " +
          "the correct binding and 5 under the swap, so a symmetric witness is green whether or not " +
          "the binding was honoured — a test whose output cannot reveal the defect it is named for");
        ok(/no_normalization:/.test(lowSrc) && /NOT Unicode-normalized/.test(lowSrc),
          "the port spec must refuse Unicode normalization of source input names. If the frozen core " +
          "distinguishes two code-point sequences, normalizing at the encoding layer is a " +
          "language-semantic change made where the source cannot see it");
        // THE RECORD MUST NOT CONTRADICT THE CODE. lowering_spike.status said
        // "inputs model UNDECIDED" for as long as it took to notice, which is
        // the same prose-versus-record drift its own record_correction is
        // about. Bound to the source now, in both directions.
        {
          const decidedInSrc = /INPUTS_MODEL = Object\.freeze\(\{\s*decided: true/.test(lowSrc);
          const st = g.lowering_spike?.status ?? "";
          ok(decidedInSrc === (g.lowering_spike?.inputs_model?.decided === true),
            "grid lowering_spike.inputs_model.decided must agree with INPUTS_MODEL.decided in " +
            "lowering.mjs — a machine-readable state contradicting the mechanism in the same tree is " +
            "the class this section's own record_correction is about");
          ok(!(decidedInSrc && /inputs model UNDECIDED/.test(st)),
            "grid lowering_spike.status still says the inputs model is UNDECIDED while lowering.mjs " +
            "records it as decided. That sentence outlived the round that decided it");
          // DERIVED, IN BOTH DIRECTIONS, AND NOT PINNED. This assertion used to
          // read `implemented === false`, with the note "must stay false until
          // the three port falsifiers are written". B2 wrote them. The
          // assertion did not notice, because it was never watching the
          // falsifiers — it was watching a constant, and a constant cannot
          // stop being true. So the record said `input` was unbuilt for four
          // passes after it was built, and the one check whose whole purpose is
          // to catch the record contradicting the code was the thing enforcing
          // the contradiction. That is the ratchet species, third instance in
          // this file: an assertion correct while a feature is open, which
          // becomes the mechanism preventing the record from acknowledging that
          // the feature closed. The cure is the same one this tree keeps
          // arriving at — derive it, never hard-code either polarity.
          ok(g.lowering_spike?.inputs_model?.implemented === (L.INPUTS_MODEL?.implemented === true),
            "grid lowering_spike.inputs_model.implemented must EQUAL INPUTS_MODEL.implemented in " +
            "lowering.mjs, in both directions and pinned to neither. It was pinned to false, which " +
            "was right for exactly as long as the port was open and then became a ratchet — the " +
            "record could not be repaired without deleting the assertion that was supposed to " +
            "protect it");
          // And the same in PROSE, because a machine-readable `true` beside a
          // sentence saying NOT IMPLEMENTED is the drift this section's own
          // record_correction is about, in the other field.
          ok(!(L.INPUTS_MODEL?.implemented === true && /NOT IMPLEMENTED/.test(st)),
            "grid lowering_spike.status still says `input` is NOT IMPLEMENTED while lowering.mjs " +
            "records it as implemented. The flag and the sentence are two statements of one fact " +
            "and both are checked, because the flag was repaired once already while the sentence " +
            "beside it was not");
          // The falsifier status is a REPORT OF A SUITE, so it is read off the
          // suite. "DECLARED, none written; B2 writes them" survived B2, B2.1,
          // B3 and B4 as a hand-typed string.
          {
            const fs = g.lowering_spike?.inputs_model?.falsifier_status ?? "";
            const allWitnessed = (L.INSTANTIATION_FALSIFIERS ?? []).length === 3 &&
              (L.INSTANTIATION_FALSIFIERS ?? []).every((f) => f.status === "WITNESSED");
            ok(allWitnessed === /WITNESSED/.test(fs) && !(allWitnessed && /none written/.test(fs)),
              "grid lowering_spike.inputs_model.falsifier_status must agree with the STATUS FIELDS " +
              "of INSTANTIATION_FALSIFIERS. A prose report of a suite's state, hand-typed beside the " +
              "suite, is the law-count/case-count/rung-count species with a different noun");
          }
        }
        // ── THE CHAIN IS DATA, AND THE PROSE MUST MATCH IT ────────────────
        // Both chain strings in lowering_spike were stale, each frozen at a
        // different round: identities.chain ran lowering straight to
        // target_term_sem_id (the B1 shape, from before a template layer
        // existed) and inputs_model.chain stopped at target_term_sem_id
        // without closed_template_sem_id or emission_sem_id (the B1.2 shape,
        // from before the emission split fired at B2.1). Neither could fail,
        // because nothing compared them to REFINEMENT_CHAIN, which is the
        // executable one. Now the NODE SEQUENCE is extracted from each string
        // in order and must equal it — prose stays readable, and a node added
        // in code forces both strings.
        {
          const want = (L.REFINEMENT_CHAIN ?? []).map((n) => n.id);
          const nodesOf = (s) => (String(s).match(/[a-z_]*sem_id/g) ?? []);
          for (const [where, s] of [["identities.chain", g.lowering_spike?.identities?.chain],
                                    ["inputs_model.chain", g.lowering_spike?.inputs_model?.chain]]) {
            const got = nodesOf(s);
            ok(want.length > 0 && got.join(",") === want.join(","),
              `grid lowering_spike.${where} names the chain nodes [${got.join(", ")}] but ` +
              `REFINEMENT_CHAIN in lowering.mjs is [${want.join(", ")}]. The prose chain and the ` +
              "data chain are two artifacts that can disagree while only one is executable, and " +
              "both of these had — one by two nodes, one by four");
          }
        }
        // THE FILM SCOPE, BOUND TO THE LAW THAT OWNS IT. lowering_spike carries
        // a prose account of what the native emitter can and cannot evidence,
        // and it has been stale twice: it recorded the dup rules open after
        // B3.2 closed them, and it recorded the budget as a typed refusal.
        // Neither could fail, because nothing compared this section's account
        // of the emitter to the emitter's own canonical law. Now it is: if the
        // law says the budget seals a terminal, this section may not say it
        // refuses. Bound to the LAW rather than to the C source, because the
        // law is what a reader of the grid is being pointed at.
        {
          const nfLaw = (g.law_registry?.entries ?? [])
            .find((x) => x.id === "film.native-emission" && x.canonical === true);
          const budgetIsTerminal = /SEALED TERMINAL AND NO LONGER A REFUSAL/.test(nfLaw?.statement ?? "");
          const spikeSays = (g.lowering_spike?.status ?? "") + " " + (g.lowering_spike?.film_grade ?? "");
          ok(!(budgetIsTerminal && /BUDGET_EXHAUSTED as (native )?film evidence rather than a typed refusal/.test(spikeSays)),
            "grid lowering_spike still lists BUDGET_EXHAUSTED as an OPEN gap while the canonical " +
            "film.native-emission revision records it as a sealed terminal. This section's account of " +
            "the emitter's reach must not outlive the law it is an account of — it already did once, " +
            "for the dup rules");
        }
        // The op list, same treatment, same reason.
        {
          const ops = (L.IMPLEMENTED_LOWERED_OPS ?? []);
          const sc = g.lowering_spike?.scope ?? "";
          ok(ops.length > 0 && new RegExp("BUILT: " + ops.join(", ") + "\\b").test(sc),
            `grid lowering_spike.scope must name the BUILT ops as IMPLEMENTED_LOWERED_OPS has them ` +
            `[${ops.join(", ")}] — it read "const and add first, then input/sub/mul/len" for four ` +
            "passes after input was built");
        }
        {
          // DATA.
          const fals = (L.INSTANTIATION_FALSIFIERS ?? []).length;
          ok(fals === 3 &&
             (L.INSTANTIATION_FALSIFIERS ?? []).every((f) => f.status === "WITNESSED") &&
             ["I-4a", "I-4b", "I-4c"].every((id) =>
               (L.INSTANTIATION_FALSIFIERS ?? []).some((f) => f.id === id)),
            `INSTANTIATION_FALSIFIERS must declare all THREE port witnesses as data (found ${fals}). ` +
            "Allocation invariance and source-name sensitivity alone prove only that a label is " +
            "copied around; the swapped binding is what proves instantiation HONOURS the identity. A " +
            "prose list would drift from the suite, which this tree has watched happen to a law " +
            "count, a case count and a rung count");
        }
        {
          const ii = canonical("derivation.instantiation-identity");
          ok(!!ii && ii.canonical === true && ii.status === "PROPERTY-TESTED",
            "derivation.instantiation-identity has no canonical PROPERTY-TESTED revision (v1.35)");
          ok(!!ii && /FALSE CHOICE/.test(ii.statement ?? ""),
            "instantiation-identity@1 must record that PARAMETERIZED versus INSTANTIATED was a false " +
            "choice — the template is parameterized AND the executed term is necessarily closed. A " +
            "law that picks one of them re-opens the question the next time inputs are discussed");
          ok(!!ii && /IDENTIFIES THE RELATION AND NOT THE INVOCATION/.test(ii.statement ?? ""),
            "instantiation-identity@1 must separate the relation id from the invocation data. The " +
            "moment x=5 is inside instantiation_sem_id, every invocation is a different relation and " +
            "the receipt stops being able to say anything general");
          ok(!!ii && /INVERSE OF ROUND 16/.test(ii.statement ?? ""),
            "instantiation-identity@1 must state the quotient as round 16's inverse: there, identity " +
            "depended on a spelling that should not matter; here the danger is depending on an " +
            "allocation that should not matter while losing the source name that must");
          ok(!!ii && /NOT UNICODE-NORMALIZED/.test(ii.statement ?? ""),
            "instantiation-identity@1 must refuse Unicode normalization of source input names — a " +
            "quotient introduced at the encoding layer is a language-semantic change made where the " +
            "source cannot see it");
          ok(!!ii && /NO CLAIM ABOUT INSTANTIATION BEHAVIOUR|NO claim about instantiation behaviour/
            .test(ii.evidence ?? ""),
            "instantiation-identity@1's evidence must say that the three falsifiers are DECLARED and " +
            "none is written, so the law is PROPERTY-TESTED for the DECISION and claims nothing about " +
            "behaviour that does not exist yet. This is the one place a frozen architecture can " +
            "quietly start reading as a working feature");
        }
        const lr = canonical("derivation.lowering-refinement");
        ok(!!lr && /TWO GRADES OF EVIDENCE FOR THE EXECUTION LEG/.test(lr.statement ?? ""),
          "lowering-refinement@1 must separate OBSERVED execution from FILM-EVIDENCED execution and " +
          "claim only the first. An execution the host observed and one the kernel replayed are " +
          "different claims, and every lowered addition carries a dup cell that ic32_film v0.1.0 refuses");
        ok(!!lr && /DUP-\* rule actually becomes enabled/.test(lr.statement ?? ""),
          "lowering-refinement@1 must name exactly WHAT is still open on the execution leg. 'Later " +
          "work' is not a scope, and neither is a gap that has moved without the statement moving");
        const lcSrc = existsSync(A("lowering_check.mjs")) ? readFileSync(A("lowering_check.mjs"), "utf8") : "";
        ok(/execution-leg-is-film-evidenced/.test(lcSrc),
          "lowering_check.mjs must assert the execution leg's evidence grade at the fixture the " +
          "refinement runs on, whichever grade it is. Round 25 asserted the film REFUSAL there; round " +
          "26 asserts the film REPLAY. What must never happen is the grade being stated only in prose");
        // WAS `six-identities-stay-distinct`, and the number in the name was
        // itself the bug: the chain grew a seventh node at B1.2 and the set did
        // not. The assertion now requires the DERIVATION, not a count.
        ok(/chain-identities-stay-distinct/.test(lcSrc) &&
           /REFINEMENT_CHAIN\.filter\(\(n\) => n\.exercised\)/.test(lcSrc) &&
           !/six-identities/.test(lcSrc),
          "lowering_check.mjs must assert the chain's identities differ and DERIVE the set from " +
          "REFINEMENT_CHAIN. Collapsing any pair turns a refinement statement into a renaming — and a " +
          "hand-typed count is how the set fell a node behind the chain it was counting");
        ok(/emit-is-not-a-hidden-relation/.test(lcSrc),
          "lowering_check.mjs must MEASURE the three-way separation: an emitter change moves the " +
          "instantiation id alone, a per-op lowering-rule change moves lowering's alone, and a " +
          "template-grammar change moves both because it is the boundary they share. The two-relation " +
          "ruling is worth nothing if the ids do not sort changes between the relations");
      }
      // ── v1.24: a skipped gate is not a green one ──────────────────────
      {
        const pack = existsSync(A("make_review_pack.sh")) ? readFileSync(A("make_review_pack.sh"), "utf8") : "";
        ok(/--allow-skip-bridge/.test(pack) && /verdict downgraded to PARTIAL/.test(pack),
          "make_review_pack.sh must make the native gates REQUIRED by default and downgrade to PARTIAL " +
          "when they are skipped. Round 22's pack let a missing gcc SKIP the bridge without setting " +
          "FAILED, and then printed 'every gate replayed green'");
        ok(/checks attempted/.test(pack) && /ATTEMPTED=\$\(\(ATTEMPTED \+ 1\)\)/.test(pack),
          "the review pack must COUNT what it ran. Its prose said 'all eighteen gates' while the script " +
          "ran a different number, which is the hand-typed 44/44 defect in a different file");
        ok(/aborting before running anything/.test(pack),
          "a failed manifest must ABORT the review pack. Continuing executes files whose integrity has " +
          "already failed and reports their output as evidence");
        // ── the gating set is DATA, and nothing may keep a second copy ────
        const reg2 = existsSync(A("artifacts.json"))
          ? JSON.parse(readFileSync(A("artifacts.json"), "utf8")) : {};
        const gating = reg2.gating_probes ?? [];
        ok(Array.isArray(gating) && gating.length > 0,
          "artifacts.json must declare gating_probes — WHICH probes gate is not derivable from the " +
          "filename. The paired ones gate; the rest freeze a DECLARED-OPEN boundary and exit nonzero " +
          "by design, so globbing probe_*_repro.mjs reports failures for witnesses behaving correctly");
        for (const p2 of gating) ok(existsSync(A(p2)), `gating_probes names ${p2}, which is absent`);
        ok(/json\.load\(open\('artifacts\.json'\)\)\['gating_probes'\]/.test(pack),
          "the review pack must READ gating_probes rather than glob or re-type it");
        {
          const mk2 = existsSync(join(ROOT, "..", "Makefile"))
            ? readFileSync(join(ROOT, "..", "Makefile"), "utf8") : "";
          ok(!!mk2, "../Makefile absent, so the gating-list cross-check measured nothing");
          if (mk2) {
            const inMake = [...mk2.matchAll(/\$\(NODE\) (probe_\w+\.mjs)\)/g)].map((m2) => m2[1]).sort();
            ok(JSON.stringify(inMake) === JSON.stringify([...gating].sort()),
              "the Makefile's gating probe list and artifacts.json's gating_probes disagree — Makefile " +
              `runs [${inMake.join(", ")}], registry declares [${[...gating].sort().join(", ")}]. Two ` +
              "hand-maintained copies of one list is how a probe gets added in one place and gates in " +
              "neither");
          }
        }
      }
      ok(/implementation_claimed: impl/.test(dsrc) &&
         !/expected_implementation_id" in req && impl !== req\.expected_implementation_id/.test(dsrc),
        "validateForeignResult must report implementation_claimed and must NOT compare the request's " +
        "expectation against the result's own label — that is a claim against a claim, which is P-1");
      {
        const ip2 = entries.find((x) => x.id === "derivation.implementation-provenance" && x.revision === 2);
        ok(!!ip2 && /AN EXECUTION CLAIM IS NOT PROVENANCE/.test(ip2.statement ?? ""),
          "derivation.implementation-provenance@2 no longer opens with 'an execution claim is not " +
          "provenance' — that sentence is the whole of round 22 and survives into @3");
        const ip1 = entries.find((x) => x.id === "derivation.implementation-provenance" && x.revision === 1);
        ok(!!ip1 && /record of a FALSE claim/i.test(ip1.revision_note ?? ""),
          "derivation.implementation-provenance@1 must stay on the record AS a false claim — it said " +
          "impersonation was closed and shipped that for seven rounds");
        ok(!!g.clean_baseline?.review_pack && existsSync(A("make_review_pack.sh")),
          "grid clean_baseline.review_pack missing, or make_review_pack.sh absent (v1.23) — a review " +
          "pack of captured output is a transcript, and round 21's shipped one contained a make error " +
          "under a README asserting 105/105, with a manifest that verified perfectly");
        ok(!!g.clean_baseline?.runner_contract,
          "grid clean_baseline.runner_contract missing (v1.23) — the runner half is executable now");
        const rc = existsSync(A("runner_contract.sh")) ? readFileSync(A("runner_contract.sh"), "utf8") : "";
        ok(/out=\$\$\(\$\(NODE\) derive_battery\.mjs\)/.test(rc),
          "runner_contract.sh must extract the ACTUAL governance recipe form from the Makefile, or it " +
          "tests a paraphrase of the thing that was broken");
        ok(/outcome_sem_id MUST NOT hash a human-readable reason/.test(
             g.lowering_spike?.identities?.outcome_encoding ?? ""),
          "lowering_spike must rule that outcome_sem_id encodes refusal STRUCTURALLY — hashing a " +
          "rendered English reason recreates round 16's 'identity bound a spelling' one layer up");
      }
      const man4 = existsSync(A("artifacts.json")) ? JSON.parse(readFileSync(A("artifacts.json"), "utf8")) : {};
      ok(!!man4.derivation_boundary?.acceptance_is_not_commitment,
        "artifacts.json derivation_boundary missing acceptance_is_not_commitment (v1.18)");
      // ── v1.19: the apparatus has a gate of its own ────────────────────
      const hs = entries.find((x) => x.id === "evidence.harness-selftest");
      ok(!!hs && hs.canonical === true && hs.status === "REGRESSION-LOCKED",
        "law evidence.harness-selftest@1 missing, non-canonical, or not REGRESSION-LOCKED — six rounds " +
        "found the instrument wrong rather than the engine, and the known species have a gate");
      ok(!!hs && /UNPERTURBED case tree/.test(hs.statement ?? ""),
        "evidence.harness-selftest@1 no longer requires the clean-baseline meta-case — a contaminated " +
        "baseline is the one failure a battery of forgeries structurally cannot see");
      ok((man4.tools ?? []).includes("harness_selftest.sh"),
        "artifacts.json does not declare harness_selftest.sh (v1.19)");
      // ── v1.21: a perturbation result needs a declared clean baseline ───
      const cb = entries.find((x) => x.id === "evidence.clean-baseline");
      ok(!!cb && cb.canonical === true && cb.status === "REGRESSION-LOCKED",
        "law evidence.clean-baseline@1 missing, non-canonical, or not REGRESSION-LOCKED");
      ok(!!cb && /DECLARED, not silent/.test(cb.statement ?? ""),
        "evidence.clean-baseline@1 no longer says the baseline is DECLARED rather than silence — " +
        "'the instrument must print nothing' is the wrong generalisation and would fail every " +
        "positive gate that legitimately prints its result");
      ok(!!g.clean_baseline?.declared_baselines && Array.isArray(g.clean_baseline?.phases),
        "grid clean_baseline missing its phase list or its per-family declared baselines (v1.21)");
      ok(/^establish_baseline$/.test((g.clean_baseline?.phases ?? [])[0] ?? ""),
        "grid clean_baseline.phases must begin with establish_baseline");
      ok(!!g.lowering_spike?.decision_rule && !!g.lowering_spike?.target_encoding &&
         !!g.lowering_spike?.identities?.why_outcome_not_value,
        "grid lowering_spike missing, or missing its target encoding / decision rule / outcome identity " +
        "(v1.22) — this section was LOST in the round-16 split while a review brief claimed it was " +
        "recorded, which is the exact species this checker exists to make impossible");
      ok(!!g.clean_baseline?.gate_must_be_able_to_fail && /A GATE MUST BE ABLE TO FAIL/.test(cb?.statement ?? ""),
        "evidence.clean-baseline@1 no longer carries its runner half (v1.22) — `cmd | tail -1` takes " +
        "the PIPE's exit status, so a gate whose subject crashed prints a stack trace and reports success");
      {
        // v1.24: an ABSENT Makefile used to skip both of these silently, which
        // is the vacuity class this file exists to prosecute — a checker that
        // reports clean while measuring nothing. The case trees carry a copy at
        // ../Makefile now, so absence is a failure.
        ok(existsSync(join(ROOT, "..", "Makefile")),
          "../Makefile absent, so the governance-recipe checks scanned nothing and passed vacuously");
        const mk = existsSync(join(ROOT, "..", "Makefile"))
          ? readFileSync(join(ROOT, "..", "Makefile"), "utf8") : "";
        if (mk) ok(!/^\t@cd \$\(GOV\) && (?!out=).*\| tail -/m.test(mk),
          "a governance recipe still pipes its subject straight into tail — the recipe then fails on " +
          "TAIL's status and a crashing gate reports success");
      }
      {
        const nb = existsSync(A("negative_battery.sh")) ? readFileSync(A("negative_battery.sh"), "utf8") : "";
        ok(nb.includes("establish_baseline ()") && /establish_baseline \|\| exit 1/.test(nb),
          "negative_battery.sh does not establish and enforce its baseline — between rounds 14 and 17 " +
          "every case found its diagnostic among four unrelated failures, which is not isolated-cause " +
          "evidence even though nothing was falsely green");
        ok(/FIXTURE DRIFT/.test(nb),
          "negative_battery.sh does not verify that each case's fixture IS the baselined one — " +
          "establishing a baseline once and assuming every later tree matches it is the assumption " +
          "this law exists to remove");
      }
    }
    {
      const man3 = existsSync(A("artifacts.json")) ? JSON.parse(readFileSync(A("artifacts.json"), "utf8")) : {};
      ok(!!man3.derivation_boundary?.footprint_is_a_set && !!man3.derivation_boundary?.frozen_core,
        "artifacts.json derivation_boundary missing frozen_core or footprint_is_a_set (v1.17)");
    }
    ok(!!g.derivation_language && g.derivation_language.not_built != null,
      "grid derivation_language missing (v1.16) — small total core plus named semantic primitives is a " +
      "RULING made before the expressiveness round, and it must not quietly become a general language");
    ok(!!g.film_planes?.ruling,
      "grid film_planes missing (v1.16) — the ic32 interaction-net film and the derivation evidence " +
      "relation are two transition systems, and cross-replay of one may not be reported as the other");
    const gf = entries.find((x) => x.id === "derivation.grant-footprint-separation");
    ok(!!gf && gf.canonical === true,
      "law derivation.grant-footprint-separation@1 missing or non-canonical — collapsing the grant into " +
      "the footprint breaks freshness, and the record has already made that mistake once");
    const ip = entries.find((x) => x.id === "derivation.implementation-provenance");
    ok(!!ip && /DECLARED OPEN/.test(ip.statement ?? ""),
      "law derivation.implementation-provenance@1 missing, or no longer declares its open half — " +
      "implementation_id is a constant, so IMPERSONATION is closed and PROVENANCE is not, and that " +
      "limit may not fall off the record");
  }
  ok(!!g.film_identity_forward_declaration,
    "grid film_identity_forward_declaration missing (v1.12) — the program_sem_id/implementation_id split must be decided before the film round, not during it");
  ok(!!g.maintenance?.confinement?.realm_limit,
    "grid maintenance.confinement.realm_limit missing (v1.11) — the primordial witness must stay declared, not quietly dropped");
}
if (existsSync(A("maintenance_receipt.json"))) {
  const mr = JSON.parse(readFileSync(A("maintenance_receipt.json"), "utf8"));
  ok(mr.type === "MaintenanceReceipt" && mr.version === 1, "maintenance receipt is not v1");
  const pid = createHash("sha256").update("TRVM-MAINTPASS-v1|" + mr.vclock_before + "|" + mr.vclock_after + "|" + JSON.stringify(mr.before) + "|" + JSON.stringify(mr.after) + "|" + JSON.stringify(mr.steps)).digest("hex");
  ok(pid === mr.pass_id, "maintenance pass_id does not recompute");
  const names = (mr.steps ?? []).map((s) => s.name);
  ok(new Set(names).size === names.length, "maintenance pass visited a node twice");
  // COVERAGE, both directions (the erased-step forgery lives exactly here):
  // every step names a known publication, AND — for a completed pass —
  // every publication is named by exactly one step. Aborted/refused passes
  // may be partial, but then every UNNAMED publication must be untouched
  // (before == after), or the receipt hides a transition.
  ok(names.every((n) => n in mr.before && n in mr.after),
    "maintenance steps name unknown publications");
  {
    const named = new Set(names);
    for (const n of Object.keys(mr.before)) {
      if (named.has(n)) continue;
      if (!mr.aborted && !mr.refused)
        ok(false, `maintenance receipt hides publication ${n}: no step covers it in a completed pass`);
      else ok(JSON.stringify(mr.before[n]) === JSON.stringify(mr.after[n]),
        `maintenance receipt: unnamed publication ${n} moved in a partial pass`);
    }
    ok(Object.keys(mr.before).sort().join(",") === Object.keys(mr.after).sort().join(","),
      "maintenance before/after maps cover different publication sets");
  }
  // AFTER must equal BEFORE transformed by STEPS — the receipt PROVES the pass
  for (const s of mr.steps ?? []) {
    const b = mr.before[s.name], a2 = mr.after[s.name];
    ok(!!b && !!a2, `maintenance step ${s.name} missing from before/after maps`);
    if (!b || !a2) continue;
    ok(b.warrant_id === s.warrant_id_before && b.pub_version === s.pub_before,
      `maintenance step ${s.name}: before-map disagrees with the step record`);
    if (!mr.torn)
      ok(a2.warrant_id === s.warrant_id_after && a2.pub_version === s.pub_after,
        `maintenance step ${s.name}: after-map disagrees with the step record`);
    if (s.action === "none" || s.action === "quarantined")
      ok(s.warrant_id_before === s.warrant_id_after && s.pub_before === s.pub_after,
        `maintenance step ${s.name}: ${s.action} must not move the publication`);
    else if (s.action === "refreshed" || s.action === "rederived") {
      ok(s.pub_after > s.pub_before && s.warrant_id_after !== s.warrant_id_before,
        `maintenance step ${s.name}: ${s.action} must advance the publication and reseal`);
      // TORN receipts (v1.7.1): the after-map tells the truth per prefix —
      // applied names match the step's after-side, unapplied the before-side
      if (mr.torn) {
        const appliedSet = new Set(mr.applied ?? []);
        if (appliedSet.has(s.name))
          ok(a2.warrant_id === s.warrant_id_after,
            `torn receipt: applied ${s.name} must show the step's after-side`);
        else
          ok(a2.warrant_id === s.warrant_id_before && a2.pub_version === s.pub_before,
            `torn receipt: unapplied ${s.name} must show the before-side`);
      }
    }
    else ok(false, `maintenance step ${s.name}: unknown action ${s.action}`);
  }
  const allNone = (mr.steps ?? []).every((s) => s.action === "none");
  if (mr.torn) ok(mr.aborted === true && Array.isArray(mr.applied),
    "torn receipts must be aborted and carry the applied prefix");
  ok(mr.no_op === (!mr.refused && !mr.aborted && allNone && mr.vclock_before === mr.vclock_after),
    "maintenance no_op flag does not recompute from steps and vclocks");
  for (const lr of mr.law_refs ?? []) {
    const m = lr.match(/^law:([a-z0-9_.\-]+)@(\d+)$/);
    const e = m && byKey.get(m[1] + "@" + m[2]);
    ok(!!e && e.canonical === true, `maintenance receipt cites unknown or non-canonical ${lr}`);
  }
} else ok(false, "maintenance_receipt.json missing (v1.5 requires the maintenance receipt)");

console.log(fails.length === 0
  ? `GRID-CONSISTENCY-2: PASS — registry valid (${entries.length} entries), ` +
    `${citations} citations resolved across ${ARTIFACTS.length} artifacts, ` +
    `no banned stale claims, structure coherent with v${g.version}. [root ${ROOT}]`
  : "GRID-CONSISTENCY-2: FAIL\n - " + fails.join("\n - "));
process.exit(fails.length === 0 ? 0 : 1);
