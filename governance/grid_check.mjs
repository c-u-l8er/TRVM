/* grid_check.mjs v2.20 — GRID-CONSISTENCY-2 (law:grid.consistency@2).
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
for (const f of ARTIFACTS) {
  if (!existsSync(f)) { fails.push(`artifact missing: ${f}`); continue; }
  const frozen = /^round-\d+-ledger\.md$/.test(f) && f !== latestLedger;
  readFileSync(f, "utf8").split("\n").forEach((line, i) =>
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
for (const f of ["trvm_law_kernel.mjs", "kappa_witnesses.mjs"]) {
  const txt = existsSync(f) ? readFileSync(f, "utf8") : "";
  for (const b of BANNED) ok(!txt.includes(b), `${f} contains banned phrase: ${b}`);
}

// ── D. structural checks carried from v1 ─────────────────────────────────
const LINEAGE = ["0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "1.0.0", "1.0.1", "1.1.0", "1.2.0", "1.3.0", "1.4.0", "1.5.0", "1.6.0", "1.7.0", "1.7.1", "1.8.0", "1.9.0", "1.10.0", "1.11.0", "1.12.0", "1.13.0", "1.14.0", "1.15.0"];
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
  ];
  for (const [file, rx] of declared) {
    ok(av[file] != null, `artifact_versions missing ${file}`);
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
