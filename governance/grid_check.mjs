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
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

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
    const declared = new Set([...(man.case_inputs ?? []), ...(man.tools ?? [])]);
    const ledgerRx = new RegExp(man.ledgers_pattern);
    const probeRx = new RegExp(man.probes_pattern);
    for (const f of declared) ok(existsSync(A(f)), `artifacts.json declares ${f}, which is absent`);
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
{
  const SCAN = [".mjs", ".js", ".sh", ".json", ".md", ".c", ".h", ".py"];
  const dirs = ["", "bridge"];
  let scanned = 0;
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
const LINEAGE = ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "1.0.0", "1.0.1", "1.1.0", "1.2.0", "1.3.0", "1.4.0", "1.5.0", "1.6.0", "1.7.0", "1.7.1", "1.8.0", "1.9.0", "1.10.0", "1.11.0", "1.12.0", "1.13.0", "1.14.0", "1.15.0", "1.16.0", "1.17.0", "1.18.0", "1.19.0", "1.20.0", "1.21.0", "1.22.0", "1.23.0", "1.24.0", "1.25.0", "1.26.0", "1.27.0", "1.28.0", "1.29.0", "1.30.0", "1.31.0", "1.32.0", "1.33.0", "1.34.0", "1.35.0"];
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
  const declared = [
    ["trvm_law_kernel.mjs", /const KERNEL_VERSION = "([^"]+)";/],
    ["trvm_world.mjs", /const WORLD_VERSION = "([^"]+)";/],
    ["derive_protocol.mjs", /const PROTOCOL_VERSION = "([^"]+)";/],
  ];
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
      // ── v1.24: the execution plane originates evidence ────────────────
      {
        const nf = entries.find((x) => x.id === "film.native-emission" && x.revision === 1);
        ok(!!nf && nf.canonical === true && nf.status === "PROPERTY-TESTED",
          "law film.native-emission@1 missing, non-canonical, or not PROPERTY-TESTED (v1.24)");
        ok(!!nf && /SCOPE, checked rather than assumed/.test(nf.statement ?? "")
             && /REFUSED BY NAME/.test(nf.statement ?? ""),
          "film.native-emission@1 no longer states its scope as CHECKED refusals. An emitter that " +
          "silently skipped what it cannot do would be claiming the general case with a fixture's " +
          "evidence — and v0.1.0's scope was stated by the WRONG predicate (dup presence rather than " +
          "dup enabledness), which a refusal makes visible and a silence would not have");
        ok(!!nf && /ACCIDENTALLY TRUE/.test(nf.statement ?? ""),
          "film.native-emission@1 must keep the record of the readback check that was removed for " +
          "being accidentally true. A check that passes because the fixture is trivial is not evidence, " +
          "and deleting it without saying why would leave the strongest-sounding sentence unexplained");
        ok(!!nf && /replaySemFilm/.test(nf.statement ?? "") && /WITHOUT normalization or translation/.test(nf.statement ?? ""),
          "film.native-emission@1 must name the kernel's OWN replaySemFilm and say the frame is " +
          "accepted without translation — a checker written for the occasion checks the occasion");
        ok(!!nf && /film_planes/.test(nf.statement ?? ""),
          "film.native-emission@1 must keep the two transition systems apart. The TRVM calculus film " +
          "and the derivation evidence relation share HOST infrastructure and no semantics, and round " +
          "15 §61 exists because a session could otherwise finish the second and write that the first " +
          "was done");
        for (const f of ["bridge/ic32_film.c", "bridge/film_check.mjs"])
          ok(existsSync(A(f)), `film.native-emission@1 cites ${f}, which is absent`);
        const filmSrc = existsSync(A("bridge/ic32_film.c")) ? readFileSync(A("bridge/ic32_film.c"), "utf8") : "";
        ok(/#define IC32_CANON_NO_MAIN/.test(filmSrc) && /#include "ic32_canon\.c"/.test(filmSrc),
          "ic32_film.c must INCLUDE ic32_canon.c rather than copy it — the canonicalizer beneath the " +
          "film has to be the same code the 48/48 bridge gate replays, or the film round is proving a " +
          "canonicalizer nothing else has ever checked");
        ok(/film-not-quiescent-at-terminal/.test(filmSrc) && /film-dup-rule-enabled/.test(filmSrc),
          "ic32_film.c must CHECK pool-quiescence at the terminal and refuse an ENABLED dup rule by " +
          "name. v0.1.0 refused on dup PRESENCE, which was the right refusal for the wrong reason: the " +
          "lowered add carries dups and fires none, and the blocker was never their presence");
        ok(/ACCIDENTALLY TRUE/.test(filmSrc),
          "ic32_film.c must record why the readback INTERACTION-COUNT check was removed. v0.1.0 " +
          "asserted the readback fired zero interactions and that was accidentally true on a one-step " +
          "dup-free fixture: ic32's counter is not plane-classified, so comparing it against zero " +
          "measures a different quantity from the kernel's plane-level claim, and it fires four on the " +
          "lowered term whose state is nonetheless correct");
      }
      // ── v1.27: the source language reaches the governed runtime ───────
      {
        const lowSrc = existsSync(A("lowering.mjs")) ? readFileSync(A("lowering.mjs"), "utf8") : "";
        // COMMENT-STRIPPED, for assertions about what the CODE says. B1.1
        // wrote two comments containing the literal text `implemented: false`
        // to explain the overbinding bug, and the assertion below then
        // matched THOSE while every real field had been flipped to true.
        // A check reading the prose that documents a defect, instead of the
        // field the defect is in, is the species this file exists to catch.
        const lowNoc = lowSrc.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
        ok(lowSrc !== "", "lowering.mjs absent — three laws cite it");
        for (const [id, want] of [["derivation.canonical-lowering", "PROPERTY-TESTED"],
          ["derivation.target-decoding", "PROPERTY-TESTED"],
          ["derivation.lowering-refinement", "PROPERTY-TESTED"]]) {
          const e = entries.find((x) => x.id === id && x.revision === 1);
          ok(!!e && e.canonical === true && e.status === want,
            `law ${id}@1 missing, non-canonical, or not ${want} (v1.27)`);
        }
        const cl = entries.find((x) => x.id === "derivation.canonical-lowering");
        ok(!!cl && /THE INSTRUMENT IS RE-LOWERING, NOT A FILM/.test(cl.statement ?? ""),
          "canonical-lowering@1 must rule that lowering gets NO film. A film is evidence for a " +
          "TRANSITION SYSTEM; lowering is a relation, and filming it would invent internal compiler " +
          "steps and make implementation strategy semantic — the mistake the read-order ruling refused");
        ok(!!cl && /PARAMETERIZED/.test(cl.statement ?? "") && /INSTANTIATED/.test(cl.statement ?? ""),
          "canonical-lowering@1 must keep the inputs model DEFERRED AND NAMED. target_term_sem_id is a " +
          "function of the program alone under one model and of the program AND the inputs under the " +
          "other; deciding it while implementing `input` is how an unstated variable enters an identity");
        // ── B1: the model is DECIDED, and `input` is still not built ──────
        // This required `decided: false` until B1. Two levels, two identities,
        // and — separately — two states: "not ruled" and "ruled, not written"
        // are different, and the refusal must be able to say which.
        ok(/INPUTS_MODEL = Object\.freeze\(\{\s*decided: true/.test(lowNoc) &&
           /implemented: false/.test(lowNoc) &&
           /lower-input-not-implemented/.test(lowNoc) &&
           !/lower-inputs-undecided"/.test(lowNoc),
          "lowering.mjs must record the inputs model as DECIDED and NOT IMPLEMENTED, and refuse the " +
          "input op as lower-input-not-implemented. The old lower-inputs-undecided cannot distinguish " +
          "'we have not ruled' from 'we have ruled and not written it', and a refusal that conflates " +
          "two states is a stale instrument with a delay fuse");
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
          ok(g.lowering_spike?.inputs_model?.implemented === false,
            "grid lowering_spike.inputs_model.implemented must stay false until the three port " +
            "falsifiers are written — B1 decided the model and built none of it, and a record that " +
            "loses that distinction re-creates the refusal-name problem one layer up");
        }
        {
          const fals = (lowSrc.match(/id: "I-4[abc]"/g) ?? []).length;
          ok(fals === 3 && /status: "DECLARED"/.test(lowSrc),
            `INSTANTIATION_FALSIFIERS must declare all THREE port witnesses as data (found ${fals}). ` +
            "Allocation invariance and source-name sensitivity alone prove only that a label is " +
            "copied around; the swapped binding is what proves instantiation HONOURS the identity. A " +
            "prose list would drift from the suite, which this tree has watched happen to a law " +
            "count, a case count and a rung count");
        }
        {
          const ii = entries.find((x) => x.id === "derivation.instantiation-identity" && x.revision === 2);
          ok(!!ii && ii.canonical === true && ii.status === "PROPERTY-TESTED",
            "law derivation.instantiation-identity@2 missing, non-canonical, or not PROPERTY-TESTED (v1.35)");
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
        const lr = entries.find((x) => x.id === "derivation.lowering-refinement");
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
        ok(/six-identities-stay-distinct/.test(lcSrc),
          "lowering_check.mjs must assert the six identities differ — collapsing any pair turns a " +
          "refinement statement into a renaming");
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
