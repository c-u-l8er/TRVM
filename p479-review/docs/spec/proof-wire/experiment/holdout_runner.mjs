/* ═══════════════════════════════════════════════════════════════════════════
   holdout_runner.mjs — v0.6.0 — THE AUTHORITY AND THE SUBJECT COME FROM ONE WORLD
   law:proof.instrument-content-bound@1 · law:proof.interop-observed-not-scored@1
   law:proof.reveal-gates-secret-execution@1
   law:proof.executed-subject-is-frozen-subject@1
   law:proof.measurement-authority-frozen@1 · law:proof.state-transition-witnessed@1
   law:proof.authority-bound-to-its-world@1

   P4.7 put the reveal gate in the caller and a candidate frozen but unrevealed
   received H1…H10 from an ordinary `make governance` run. P4.7.1 moved the gate
   HERE, into the frozen instrument — and then handed it, from outside the
   freeze, the fact it gates on:

       node holdout_runner.mjs … --status REVEALED

   REPRODUCED: change that one argument in mutable `governance/holdout_score.mjs`,
   call `--reveal` never, and a CANDIDATE_FROZEN fake received all ten hidden
   constructions while SPEC-RELEASE, BLIND-RUN and HOLDOUT-SCORE stayed green.
   Moving a decision into frozen code and leaving its premise mutable moves the
   defect one argument to the left. THE SAME SHAPE ONE LAYER UP: `--complete`
   spawned this file's mutable CALLER for the summary it then believed, so a
   candidate whose entire body was `exit 99` reached COMPLETE and got a RESULT
   receipt claiming 25/25 and interop agreement.

   THE RULE THIS ROUND ENFORCES:

       NO UNFROZEN PROGRAM MAY DECIDE WHETHER SECRET BYTES ARE RELEASED, OR
       WHETHER THE EXPERIMENT COMPLETED SUCCESSFULLY.

   So this file no longer receives a status, an adapter list or a challenge
   array. It reads the run record and the receipt chain itself, derives the
   status from what the chain WITNESSES, verifies the whole run against the tree,
   and loads the challenges itself. The one thing it takes from the secret side
   is a DIRECTORY, and that input is self-authenticating: whatever it is handed
   is digested and must equal the `holdout_commitment` inside the release, so the
   mutable wrapper cannot lie about where the secret is without the commitment
   catching it.

       role: reference   runs at every status. It is this machine's own
                         implementation and the challenges are already on its
                         disk; withholding them from it would measure nothing.
       role: candidate   runs ONLY at a WITNESSED REVEALED or COMPLETE. Otherwise
                         it receives ZERO bytes of H* material — the challenges
                         file is not written at all — and the withholding is
                         REPORTED rather than silent.

   AND P4.7.2 LEFT THE AUTHORITY SELECTABLE. It gave every lifecycle program a
   `--state-root` so the falsifier battery could stop attacking the live record.
   REPRODUCED: freeze a candidate in the canonical run, never reveal it, copy the
   record and its receipt chain to /tmp, reveal only the copy, then measure with
   `--state-root /tmp/alt` against the canonical repository. HOLDOUT-AUTHORITY
   said PASS and the CANONICAL candidate received H1…H10 while the canonical
   record still read CANDIDATE_FROZEN. The `NON-CANONICAL` stamp stopped that
   measurement from COMPLETING the real run and stopped nothing else —
   **completion isolation and secret-release isolation are different
   invariants**, and by the time the stamp applies the disclosure has happened.

   SO THE RULE SHARPENS: an authority fact must be bound not only as tightly as
   the function consuming it, but to the SUBJECT over which it is exercised.
   Neither `--repo-root` nor `--state-root` is accepted here any more. The world
   is the tree this file sits in; the state root is `<world>/governance`; and
   every path a run names must resolve inside that same world. To measure a
   different world, run THAT world's copy of this file.
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, writeFileSync, existsSync, mkdtempSync, readdirSync, statSync }
  from "node:fs";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve, relative } from "node:path";
import { tmpdir } from "node:os";
import { scoreRun, compareObservations } from "./holdout_score_core.mjs";
import { INTERPRETERS, REVEALED_STATES, AUTHORITY_TYPE, SUMMARY_TYPE, authorizedStatus,
  commitmentOf, digestOfPaths, executionProblems, instrumentDigest, loadChallenges, packageDigest,
  readEvidence, resolveState, tryParseEvidence, verifyRun } from "./run_state.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const SPEC = join(HERE, "..");
/** The world this copy of the instrument belongs to, derived from where it is. */
const REPO = resolve(join(HERE, "..", "..", "..", ".."));
const sha = (b) => createHash("sha256").update(b).digest("hex");
/* The commitment and the challenge loader live in `run_state.mjs` so the
   TERMINAL verifier can reach them without importing this file, which imports
   it. Re-exported here because this is where callers have always found them. */
export { packageDigest, executionProblems, REVEALED_STATES, commitmentOf, loadChallenges };

/* ── THE SECRET, AUTHENTICATED BY ITS OWN COMMITMENT ───────────────────────── */


/* ── EXECUTION ────────────────────────────────────────────────────────────── */

function scratchDir() {
  try { return mkdtempSync(join(tmpdir(), "trvm-holdout-")); }
  catch { return mkdtempSync(join(HERE, ".holdout-scratch-")); }
}

export function runAdapters({ challenges, adapters, release, repoRoot, revealed, out = scratchDir() }) {
  const runs = [], problems = [], withheld = [];
  const challengesPath = join(out, "challenges.json");

  const seen = new Set();
  for (const a of adapters) {
    if (seen.has(a.implementation))
      problems.push(`two adapters both call themselves ${JSON.stringify(a.implementation)} — an ` +
        `implementation label is how an observation is attributed, so it must be unique`);
    seen.add(a.implementation);
  }

  /* THE SECRET IS NOT EVEN WRITTEN WHERE A WITHHELD CANDIDATE COULD READ IT. */
  const permitted = adapters.filter((a) => {
    if (a.role !== "candidate" || revealed) return true;
    withheld.push(a.implementation);
    return false;
  });
  if (permitted.length) writeFileSync(challengesPath, JSON.stringify(challenges, null, 1) + "\n");

  for (const a of permitted) {
    if (!a.package_digest) {
      problems.push(`${a.implementation}: no package_digest — an adapter that is not content-bound ` +
        `cannot be the subject of a frozen experiment`);
      continue;
    }
    const live = packageDigest(repoRoot, a.package_files ?? []);
    if (live.digest !== a.package_digest) {
      problems.push(`${a.implementation}: package digest ${live.digest.slice(0, 20)}… does not ` +
        `match the ${a.package_digest.slice(0, 20)}… this run pinned — the implementation moved ` +
        `after it was frozen, so it is not the one under measurement`);
      continue;
    }
    const ep = executionProblems(a, repoRoot);
    if (ep.length) { problems.push(...ep); continue; }

    const obsPath = join(out, `observations.${a.implementation}.json`);
    const argv = a.command.map((x) => x === "{{CHALLENGES}}" ? challengesPath
      : x === "{{OUT}}" ? obsPath : x);
    if (INTERPRETERS.has(argv[0])) argv[0] = process.execPath;
    else argv[0] = join(repoRoot, argv[0]);
    const proc = spawnSync(argv[0], argv.slice(1), { encoding: "utf8", cwd: repoRoot });
    if (proc.status !== 0 || !existsSync(obsPath)) {
      problems.push(`${a.implementation}: adapter exited ${proc.status} without an observation ` +
        `document — ${(proc.stderr || proc.stdout || "").trim().split("\n").slice(-1)[0] ?? ""}`);
      continue;
    }
    const bytes = readFileSync(obsPath);
    /* THE MEASUREMENT'S OWN BYTE BOUNDARY, AND THE ONE THAT MATTERS MOST FOR A
       FOREIGN IMPLEMENTATION. An observation whose bytes contain
       `"implementation":"evil","implementation":"honest"` names two subjects;
       `JSON.parse` picks the last and the attribution check then passes. It is
       REFUSED before it is scored, so parser permissiveness stops being an
       accidental property of whichever implementation happens to be measuring. */
    const read = tryParseEvidence(bytes, `${a.implementation}'s observation document`);
    if (read.refused) { problems.push(read.refused); continue; }
    const doc = read.value;
    const scored = scoreRun(challenges, doc,
      { expectRelease: release, expectImplementation: a.implementation });
    if (scored.refused) { problems.push(`${a.implementation}: ${scored.refused}`); continue; }
    /* THE PATH TRAVELS WITH THE DIGEST. A digest identifies an artifact and does
       not make an absent one re-checkable, so completion archives these exact
       bytes beside the RESULT rather than recording a hash of a scratch file
       that is about to be forgotten. */
    runs.push({ implementation: a.implementation, role: a.role, doc,
      observation_sha256: sha(bytes), observation_path: obsPath,
      package_digest: a.package_digest,
      binary_digest: a.binary_digest ?? null, ...scored });
  }
  return { runs, problems, withheld, revealed, out };
}

/** INTEROP. Every unordered pair of adapters, compared over OBSERVATIONS. */
export function interop(runs) {
  if (runs.length < 2)
    return { measured: false, pairs: 0, findings: [],
      why: `${runs.length} frozen implementation(s) executed — interoperability is a question about ` +
        `TWO, and with fewer it is NOT MEASURED rather than satisfied` };
  const findings = [];
  for (let i = 0; i < runs.length; i += 1)
    for (let j = i + 1; j < runs.length; j += 1)
      for (const f of compareObservations(runs[i].doc, runs[j].doc))
        findings.push({ ...f, between: [runs[i].implementation, runs[j].implementation] });
  return { measured: true, pairs: (runs.length * (runs.length - 1)) / 2, findings };
}

/* ── THE AUTHORITY ────────────────────────────────────────────────────────── */

/** Everything between "here is a directory that may hold the secret" and a
 *  summary document. Nothing in this path is supplied as a CLAIM: the release is
 *  read from the spec tree, the commitment is recomputed, the run record and its
 *  receipt chain are read from the state root, the status is whatever the chain
 *  witnesses, and the challenges are loaded here. */
export function measure({ repoRoot = REPO, holdoutDir = join(repoRoot ?? REPO, "governance", "holdout"),
  specDir = SPEC } = {}) {
  const state = resolveState(repoRoot);
  const relPath = join(specDir, "SPEC-RELEASE.json");
  if (!existsSync(relPath))
    return { fatal: `there is no SPEC-RELEASE.json in ${specDir}`, state };
  let rel;
  try { rel = readEvidence(relPath, "SPEC-RELEASE.json"); }
  catch (e) { return { fatal: e.message, state }; }

  const live = commitmentOf(holdoutDir, specDir);
  if (live !== rel.holdout_commitment)
    return { fatal: `the tree at ${holdoutDir} does not match the commitment in ` +
      `${rel.spec_release_id}. committed ${String(rel.holdout_commitment).slice(0, 20)}…, present ` +
      `${String(live).slice(0, 20)}…. A challenge set altered after it was committed is not a ` +
      `challenge set, and scoring is REFUSED rather than run on it`, state, rel };

  if (!existsSync(state.runPath))
    return { fatal: `there is no run record at ${state.runPath}, so no subject is pinned`, state, rel };
  /* THE FROZEN SIDE READS THE RECORD ITSELF, ACROSS THE BYTE BOUNDARY. */
  const verified = verifyRun({ repoRoot, specDir, receiptsDir: state.receiptsDir });
  if (verified.run === null)
    return { blocking: verified.problems, run: null, rel, state,
      auth: { problems: verified.problems, revealed: false } };
  const run = verified.run;
  const auth = authorizedStatus(run, state.receiptsDir);

  /* THE INSTRUMENT'S OWN FALSIFIER, BEFORE THE MEASUREMENT. A scorer that
     returned true unconditionally passes the satisfied arm of the synthetic
     fixture and dies on the failing one. */
  const fx = spawnSync(process.execPath, [join(HERE, "holdout_score_core.mjs"), "--fixture"],
    { encoding: "utf8" });
  const fixtureOk = fx.status === 0;

  const authority = {
    type: AUTHORITY_TYPE,
    instrument_digest: instrumentDigest(specDir).digest,
    run_id: run.run_id, status: run.status,
    witnessed: auth.problems.length === 0, revealed: auth.revealed,
    spec_release_id: rel.spec_release_id,
    holdout_commitment: rel.holdout_commitment, holdout_entries: rel.holdout_entries,
    /* P4.7.3. THE WORLD, NOT A SELECTED STATE DIRECTORY. `--state-root` is
       gone: the state root is derived from this file's own location, so the
       authority and the subjects it authorizes necessarily come from one tree. */
    world_root: repoRoot, state_root: state.root,
    fixture_ok: fixtureOk,
  };

  const blocking = [...verified.problems, ...(fixtureOk ? []
    : ["the frozen scorer does not reproduce its own declared synthetic result, so nothing it says " +
       "about a real challenge set means anything"])];
  if (blocking.length) return { blocking, authority, run, rel, state, auth, fx };

  let challenges;
  try { challenges = loadChallenges(holdoutDir); }
  catch (e) { return { blocking: [e.message], authority, run, rel, state, auth, fx }; }
  const executed = runAdapters({ challenges, adapters: run.adapters ?? [],
    release: run.spec_release_id, repoRoot, revealed: auth.revealed });
  return { authority, run, rel, state, auth, challenges, executed, io: interop(executed.runs) };
}

/* ── CLI ─────────────────────────────────────────────────────────────────── */
const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN) {
  const arg = (n, d = null) => { const i = process.argv.indexOf(n); return i >= 0 ? process.argv[i + 1] : d; };
  /* THE WORLD IS WHERE THIS FILE IS. Neither --repo-root nor --state-root is
     accepted any more: a caller that could name either could combine one world's
     authority with another world's subjects, and that is exactly what handed the
     canonical candidate all ten constructions from a REVEALED copy in /tmp. To
     measure a different world you must run THAT world's copy of this file. */
  const repoRoot = REPO;
  /* A RETIRED FLAG THAT IS SILENTLY IGNORED IS A SILENT NO-OP, and a caller that
     believes it selected a world would be wrong without being told. `--status`,
     `--repo-root`, `--state-root`, `--adapters` and `--challenges` each named a
     bypass; naming them in the refusal is why this is a message and not a
     shrug. */
  const ALLOWED = new Set(["--holdout", "--summary"]);
  const RETIRED = { "--status": "a status is WITNESSED by the receipt chain, never asserted by a caller",
    "--repo-root": "the world is where this file is", "--state-root": "the state root is <world>/governance",
    "--adapters": "the subjects are read from the run record",
    "--challenges": "the challenge set is loaded here, from a directory checked against its commitment",
    "--revealed": "disclosure is decided by the chain" };
  for (let i = 2; i < process.argv.length; i += 1) {
    const a = process.argv[i];
    if (!a.startsWith("--")) continue;
    if (ALLOWED.has(a)) { i += 1; continue; }
    console.log(`HOLDOUT-RUNNER: REFUSED — ${a} is not an argument of this instrument` +
      (RETIRED[a] ? `; it was retired because ${RETIRED[a]}` : "") +
      `. The only inputs are [${[...ALLOWED].join(", ")}].`);
    process.exit(2);
  }
  const holdoutDir = resolve(arg("--holdout", join(repoRoot, "governance", "holdout")));
  const summaryPath = arg("--summary");

  const m = measure({ repoRoot, holdoutDir });
  if (m.fatal) {
    console.log(`HOLDOUT-COMMITMENT: FAIL — ${m.fatal}`);
    process.exit(1);
  }
  console.log(`HOLDOUT-COMMITMENT: PASS — ${m.rel.holdout_commitment.slice(0, 16)}… verified ` +
    `against release ${m.rel.spec_release_id.slice(0, 20)}…, recomputed by the FROZEN instrument ` +
    `over the directory it was handed. The secret side supplies a path and nothing else: a wrapper ` +
    `that lied about where the challenges are would fail this line`);

  if (m.blocking) {
    for (const p of m.blocking.slice(0, 12)) console.log(`  ${p}`);
    console.log(`HOLDOUT-AUTHORITY: FAIL — ${m.blocking.length} problem(s); the run this measurement ` +
      `would belong to does not verify, so there is nothing coherent to score`);
    process.exit(1);
  }

  const { authority, run, executed, io } = m;
  console.log(`HOLDOUT-AUTHORITY: PASS — ${run.run_id.slice(0, 24)}… is ${run.status}, WITNESSED by ` +
    `a receipt chain reaching PINNED; the instrument, the release, every subject's package and ` +
    `every subject's executable bytes verify against this tree, and every subject RESOLVES INSIDE ` +
    `the world this run belongs to (${authority.world_root})`);

  for (const r of executed.runs) {
    for (const x of r.results) if (x.pass !== true)
      console.log(`  ${r.implementation} ${x.id} ${x.op} ${x.path}: ${x.detail}`);
    for (const id of r.missing) console.log(`  ${r.implementation} ${id}: NO OBSERVATION`);
    if (r.fail || r.unresolved || r.missing.length)
      executed.problems.push(`${r.implementation}: ${r.fail} unsatisfied, ${r.unresolved} unresolved, ` +
        `${r.missing.length} unobserved of ${r.total}`);
  }
  for (const p of executed.problems) console.log(`  ${p}`);
  for (const f of io.findings.slice(0, 20))
    console.log(`  INTEROP ${f.between.join(" vs ")} ${f.path}: ${f.a} vs ${f.b} — ${f.classification}`);

  const expected = (run.adapters ?? []).length - executed.withheld.length;
  const harnessOk = executed.problems.length === 0 && executed.runs.length === expected
    && executed.runs.length > 0;
  const totals = executed.runs.reduce((n, x) => n + x.total, 0);
  const passes = executed.runs.reduce((n, x) => n + x.pass, 0);

  if (summaryPath) writeFileSync(summaryPath, JSON.stringify({
    type: SUMMARY_TYPE, authority,
    release: run.spec_release_id, status: run.status, revealed: authority.revealed,
    harness_ok: harnessOk, withheld: executed.withheld,
    adapters: executed.runs.map((r) => ({ implementation: r.implementation, role: r.role,
      package_digest: r.package_digest, binary_digest: r.binary_digest,
      observation_sha256: r.observation_sha256, observation_path: r.observation_path,
      total: r.total, pass: r.pass, fail: r.fail, unresolved: r.unresolved, missing: r.missing })),
    interop: { measured: io.measured, pairs: io.pairs, findings: io.findings },
    problems: executed.problems,
  }, null, 1) + "\n");

  console.log(harnessOk
    ? `HOLDOUT-HARNESS: PASS — ${executed.runs.length} content-bound adapter(s) ` +
      `[${executed.runs.map((x) => `${x.implementation}:${x.role}`).join(", ")}] satisfied ` +
      `${passes}/${totals} FROZEN predicates across ${m.challenges.length} hidden constructions, ` +
      `every observation document VALIDATED against its published schema and ATTRIBUTED to the ` +
      `adapter that produced it, and every adapter's package digest AND executable bytes verified ` +
      `immediately before spawn`
    : `HOLDOUT-HARNESS: FAIL — ${executed.problems.length} problem(s) across ` +
      `${executed.runs.length}/${expected} permitted adapter(s)`);
  if (executed.withheld.length)
    console.log(`HOLDOUT-REVEAL-GATE: WITHHELD — the challenge set was NOT written where ` +
      `[${executed.withheld.join(", ")}] could read it, because the receipt chain witnesses ` +
      `${run.status} and a candidate sees H* material only at ${REVEALED_STATES.join(" or ")}. ` +
      `Against P4.7 an unrevealed candidate received all ten constructions; against P4.7.1 the ` +
      `caller could simply SAY "REVEALED", and this file no longer accepts that word from anyone`);
  console.log(!io.measured
    ? `HOLDOUT-INTEROP: NOT MEASURED — ${io.why}. This is reported rather than passed, because a ` +
      `green interoperability result over one implementation is a claim nobody measured`
    : io.findings.length === 0
      ? `HOLDOUT-INTEROP: PASS — ${io.pairs} pair(s) agree on EVERY member of EVERY observation, ` +
        `not merely on what the frozen predicates happen to read`
      : `HOLDOUT-INTEROP: ${io.findings.length} UNCLASSIFIED_FINDING(S) across ${io.pairs} pair(s) ` +
        `— a disagreement is a finding to be classified by a human, and it BLOCKS completion ` +
        `rather than printing underneath a PASS`);
  process.exit(harnessOk && (!io.measured || io.findings.length === 0) ? 0 : 1);
}
