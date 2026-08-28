/* ═══════════════════════════════════════════════════════════════════════════
   brief_identity.mjs — v0.1.0 — THE ROUND BRIEF'S NUMBERS ARE DERIVED
   law:evidence.derived-denominator@1

   THE P4.7.4 BRIEF SHIPPED AN IDENTITY THAT DID NOT EXIST. Its header read

       package  bpkg-d43546…09ee18e40f5   53 files

   while `blind-package.json`, `blind-run.json` and the BLIND-PACKAGE gate all
   said `bpkg-d43546…f6490e1d211` over 54 files. The prefix was right because it
   was copied from a console line truncated at eighty columns; THE TAIL WAS
   COMPLETED BY HAND, and the file count was carried over from the previous
   round's brief. The pack's manifest verified perfectly and the executable
   record was correct — a manifest authenticates BYTES, not the prose beside
   them, which is round 21's lesson arriving in the round briefs.

   This tree already forbids hand-typed counts in gates and in law totals. A
   review brief is evidence too: it is the document a reviewer reads before
   deciding whether to trust the tree. So the identity block is DERIVED here, and
   `make_review_pack.sh` REFUSES to build a pack whose brief does not contain the
   block this prints. A brief that misdescribes the pack it ships inside is worse
   than no brief, because it is the half a reader checks least.

   P4.7.7 — AND IT WORKED, AND THE NUMBER BESIDE IT WAS STILL TYPED BY HAND. The
   P4.7.6 brief said `grid v1.66.0 (134 entries / 469 citations)` in two places
   while a clean replay of the gate said `471 citations`, and `--check` passed,
   because this file derived the three IDENTITIES and nothing else. Deriving some
   fields of a document and hand-entering the adjacent one is the species this
   whole round is about, so the grid line is derived here too — from
   `invariant-grid.json`, counted the way `grid_check.mjs` counts it.

   Run: node brief_identity.mjs              print the block
        node brief_identity.mjs --check <f>  refuse if <f> does not contain it
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const SPEC = join(HERE, "..", "docs", "spec", "proof-wire");

const read = (p) => (existsSync(p) ? JSON.parse(readFileSync(p, "utf8")) : null);

export function identityBlock() {
  const rel = read(join(SPEC, "SPEC-RELEASE.json"));
  const pkg = read(join(HERE, "blind-package.json"));
  const run = read(join(HERE, "blind-run.json"));
  const problems = [];
  if (!rel) problems.push("SPEC-RELEASE.json is absent");
  if (!pkg) problems.push("blind-package.json is absent");
  if (!run) problems.push("blind-run.json is absent");
  /* THE THREE RECORDS MUST AGREE BEFORE ANY OF THEM IS QUOTED. A block derived
     from three files that disagree is a derived number that is still wrong. */
  if (rel && run && run.spec_release_id !== rel.spec_release_id)
    problems.push(`the run is against ${String(run.spec_release_id).slice(0, 20)}… and the tree's ` +
      `release is ${String(rel.spec_release_id).slice(0, 20)}…`);
  if (pkg && run && run.blind_package_id !== pkg.blind_package_id)
    problems.push(`the run binds ${String(run.blind_package_id).slice(0, 24)}… and the manifest is ` +
      `${String(pkg.blind_package_id).slice(0, 24)}…`);
  if (problems.length) return { problems, lines: [] };
  const lines = [
    `release  ${rel.spec_release_id}   exp revision ${rel.experiment_revision}`,
    `package  ${pkg.blind_package_id}   ${pkg.file_count} files`,
    `run      ${run.run_id}   ${run.status}`,
  ];
  return { problems: [], lines };
}

/** THE GRID SUMMARY, TAKEN FROM THE GATE THAT COMPUTES IT.
 *
 *  The citation total spans `invariant-grid.json` AND every shipped artifact and
 *  ledger, so re-counting it here would be a SECOND implementation of the count
 *  — and two implementations of one number is how the brief and the gate came to
 *  disagree in the first place. The gate is run, and its own summary line is the
 *  source. A gate that does not pass has no number worth quoting, so a red tree
 *  refuses rather than reporting a stale figure. */
export function gridSummary() {
  const r = spawnSync(process.execPath, [join(HERE, "grid_check.mjs")],
    { encoding: "utf8", cwd: HERE });
  const line = (r.stdout ?? "").split("\n").find((l) => l.startsWith("GRID-CONSISTENCY-2:"));
  if (!line) return { problems: ["the grid gate produced no GRID-CONSISTENCY-2 verdict"], line: null };
  if (!/^GRID-CONSISTENCY-2: PASS/.test(line))
    return { problems: [`the grid gate does not pass, so its totals are not quotable: ` +
      `${line.slice(0, 120)}`], line: null };
  /* THE VERSION PATTERN IS ANCHORED TO THREE COMPONENTS, not `[0-9.]+`, which
     swallowed the full stop that ends the sentence and derived `v1.67.0.` — a
     hand-typed number's failure mode reproduced inside the machinery built to
     remove hand-typed numbers. */
  const m = /registry valid \((\d+) entries\), (\d+) citations resolved across (\d+) artifacts.*?structure coherent with v(\d+\.\d+\.\d+)/
    .exec(line);
  if (!m) return { problems: [`the grid verdict does not have the shape this file reads: ` +
    `${line.slice(0, 160)}`], line: null };
  const [, entries, cites, artifacts, version] = m;
  return { problems: [],
    line: `grid     v${version}   ${entries} entries / ${cites} citations across ${artifacts} artifacts`,
    entries: Number(entries), citations: Number(cites), version };
}

/** ANY HAND-TYPED GRID PAIR IN THE BRIEF MUST AGREE WITH THE TREE. Carrying the
 *  derived line is necessary and not sufficient: the P4.7.6 brief would have
 *  carried it and still said `134 entries / 469 citations` twice in prose beside
 *  it. Every `N entries / M citations` in the document is checked. */
export function gridClaimProblems(text, g) {
  const bad = [];
  for (const m of text.matchAll(/(\d+)\s+entries\s*\/\s*(\d+)\s+citations/g))
    if (Number(m[1]) !== g.entries || Number(m[2]) !== g.citations)
      bad.push(`the brief says "${m[0]}" and this tree is ${g.entries} entries / ${g.citations} ` +
        `citations`);
  for (const m of text.matchAll(/\bgrid\s+v([0-9]+\.[0-9]+\.[0-9]+)/gi))
    if (m[1] !== g.version)
      bad.push(`the brief says "grid v${m[1]}" and this tree is v${g.version}`);
  return [...new Set(bad)];
}

const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN) {
  const { problems, lines } = identityBlock();
  const grid = gridSummary();
  const all = [...problems, ...grid.problems];
  if (all.length) {
    console.log(`BRIEF-IDENTITY: FAIL — ${all.length} problem(s):`);
    for (const p of all) console.log(`  ${p}`);
    process.exit(1);
  }
  const block = [...lines, grid.line];
  const i = process.argv.indexOf("--check");
  if (i < 0) { console.log(block.join("\n")); process.exit(0); }
  const path = process.argv[i + 1];
  if (!path || !existsSync(path)) {
    console.log(`BRIEF-IDENTITY: FAIL — no brief at ${path}`);
    process.exit(1);
  }
  const text = readFileSync(path, "utf8");
  const missing = block.filter((l) => !text.includes(l));
  const disagreeing = gridClaimProblems(text, grid);
  if (missing.length || disagreeing.length) {
    console.log(`BRIEF-IDENTITY: FAIL — ${missing.length} derived line(s) absent and ` +
      `${disagreeing.length} hand-typed grid claim(s) disagree with the tree:`);
    for (const l of block) console.log(`  ${text.includes(l) ? " " : ">"} ${l}`);
    for (const d of disagreeing) console.log(`  ! ${d}`);
    process.exit(1);
  }
  console.log(`BRIEF-IDENTITY: PASS — the brief carries the release, package, run and grid summary ` +
    `this tree actually has; all three records agree with each other; and every "N entries / M ` +
    `citations" written anywhere in the brief matches what the gate derives. The P4.7.6 brief said ` +
    `469 citations twice while a clean replay said 471, and passed this check, because only the ` +
    `identities were derived.`);
  process.exit(0);
}
