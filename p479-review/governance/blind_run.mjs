/* ═══════════════════════════════════════════════════════════════════════════
   blind_run.mjs — v0.7.0 — THE TRANSITIONS ARE A CLI OVER A FROZEN STATE MACHINE,
   AND THE WORLD IS WHERE THIS FILE IS
   law:proof.run-selects-one-release@1 · law:proof.candidate-frozen-before-reveal@1
   law:proof.instrument-content-bound@1 · law:proof.transition-preconditions-live@1
   law:proof.state-transition-witnessed@1 · law:proof.measurement-authority-frozen@1
   law:proof.authority-bound-to-its-world@1 · law:proof.terminal-claim-witnessed@1

   v0.2.0 owned the state machine, the run identity, the receipt format and the
   transition preconditions — all in this file, which is in no digest. Four
   things followed, and GPT reproduced every one:

     * `verifyLiveRun()` re-digested `package_files` and NEVER re-hashed
       `binary_path`. Freeze a source file and a separate binary, mutate only the
       binary, call `--reveal`: REVEALED succeeded and BLIND-RUN stayed PASS.
     * `--freeze-candidate` accepted no `--binary` at all and printed
       `CANDIDATE_FROZEN … NO binary digest`, contradicting the frozen contract's
       own definition of the state.
     * receipts were OUTPUTS of transitions and INPUTS to nothing. Edit `status`
       to REVEALED, recompute `run_id` with this file's own exported `runId()`,
       write no receipt at all: BLIND-RUN PASS, and the candidate received
       H1…H10.
     * `--complete` spawned MUTABLE `holdout_score.mjs` for the summary it then
       wrote into a RESULT receipt. A candidate whose entire body was `exit 99`
       reached COMPLETE with 25/25 and interop agreement.

   So the state machine, the identity, the receipt shape, the chain rule and the
   subject checks all moved to `experiment/run_state.mjs`, inside
   `experiment_digest`, therefore inside `spec_release_id`, therefore inside the
   `instrument_digest` this run pins. What is left here is argument parsing,
   file writing and printing. Two consequences are the point:

     1. THE TRANSITION AND THE MEASUREMENT NOW SHARE ONE DEFINITION of what a
        valid run is, so they cannot drift — which is exactly how a binary could
        be refused at spawn and revealed to anyway.
     2. `--complete` spawns THE FROZEN RUNNER, whose bytes are inside the digest
        it just verified, and then checks that summary's authority block against
        what it independently recomputed. No unfrozen program produces a number
        that reaches a RESULT receipt.

   THE STATE MACHINE:

       PINNED            srel + bpkg + instrument + the reference adapter
       CANDIDATE_FROZEN  + the candidate's source digest, REQUIRED binary digest
                           and recorded environment
       REVEALED          the challenge set has been opened. REFUSED before
                           CANDIDATE_FROZEN — that is the whole point
       COMPLETE          measured, with no unclassified interop finding
       ABORTED           terminal; the tree may move on

   Each transition writes an IMMUTABLE RECEIPT naming its PREDECESSOR, and every
   later verification walks that chain back to PINNED.
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, writeFileSync, existsSync, mkdirSync, mkdtempSync, rmSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { tmpdir } from "node:os";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join, relative, resolve } from "node:path";
import { computePackage } from "./blind_package.mjs";
import { INSTRUMENT, RESULT_TYPE, RUN_TYPE, STATES, NEXT, chainProblems, digestOfPaths,
  IMPLEMENTATION_RE, instrumentDigest, observationFile, observationsDir, readEvidence, receiptBody,
  receiptBytes, receiptFile, renderRun, resolveState, resultFile, resultProblems, runCore, runId,
  tryParseEvidence, verifyRun } from "../docs/spec/proof-wire/experiment/run_state.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const SPEC = join(HERE, "..", "docs", "spec", "proof-wire");
const REPO = join(HERE, "..");
const RUNNER = join(SPEC, "experiment", "holdout_runner.mjs");
const HOLDOUT = join(HERE, "holdout");
const sha = (b) => createHash("sha256").update(b).digest("hex");

/* The state machine, the identity and the subject checks are the INSTRUMENT'S.
   Re-exported so callers keep one import site and cannot acquire a second
   definition by importing the other one. */
export { INSTRUMENT, STATES, NEXT, digestOfPaths, runCore, runId, chainProblems };
export const instrumentDigestHere = () => instrumentDigest(SPEC);

/** THE REFERENCE SUBJECT. Its package is the JavaScript implementation the
 *  adapter reaches, not merely the adapter file — an adapter is a thin shell
 *  over a checker and freezing only the shell freezes nothing. */
const JS_PACKAGE = Object.freeze([
  "governance/js_holdout_adapter.mjs", "governance/cas.mjs", "governance/nest_bundle.mjs",
  "governance/nest_check.mjs", "governance/derive_protocol.mjs", "governance/certificate.mjs",
  "governance/schema.mjs",
]);

const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
const argv = process.argv.slice(2);
const opt = (n, d = null) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : d; };

/** WHERE THE STATE LIVES, AND IT IS NOT SELECTABLE.
 *
 *  v0.3.0 took `--state-root` so the falsifier battery could stop attacking the
 *  live record. REPRODUCED: that made the AUTHORITY selectable too — freeze a
 *  candidate canonically, never reveal it, reveal a copy of the record in /tmp,
 *  measure with `--state-root /tmp/alt`, and the CANONICAL candidate received
 *  H1…H10 while the canonical record still read CANDIDATE_FROZEN. The state root
 *  is derived from this file's own location now; a dry run gets its own whole
 *  world and runs that world's copy of this file. */
for (const dead of ["--state-root", "--repo-root"])
  if (argv.includes(dead)) {
    console.log(`BLIND-RUN: REFUSED — ${dead} is retired. It made the AUTHORITY selectable: a ` +
      `REVEALED copy of a run record in /tmp authorized the CANONICAL candidate and it received ` +
      `all ten hidden constructions while the canonical record still read CANDIDATE_FROZEN. A dry ` +
      `run gets its own WORLD — spec tree, governance state, subjects — and runs that world's copy ` +
      `of this file.`);
    process.exit(2);
  }
const STATE = resolveState(REPO);
const RUN = STATE.runPath;
const RECEIPTS = STATE.receiptsDir;

/** THE CLI READS ACROSS THE SAME BOUNDARY THE VERIFIER DOES. P4.3 caught this
 *  file's ancestor printing PASS on a duplicate-key document the byte-level
 *  checker beside it refused, because the CLI handed it a decoded string. The
 *  authority is `verifyRun`, which reads the bytes itself; this is here so the
 *  two never disagree about what the record says. */
const readRun = () => {
  if (!existsSync(RUN)) return null;
  try { return readEvidence(RUN, "blind-run.json"); }
  catch (e) {
    /* AND A REFUSAL IS A VERDICT, NOT A STACK TRACE. `--abort` reads the record
       too, and a run you cannot abort when it is broken is a trap — but a record
       whose bytes have two readings cannot be aborted meaningfully either, so
       the refusal names the byte problem and the operator repairs THAT first. */
    console.log(`BLIND-RUN: REFUSED — ${e.message}`);
    process.exit(1);
  }
};

/** A transition: re-identify, write the receipt naming its predecessor, then the
 *  record. The receipt is written FIRST, because a record whose status nothing
 *  witnesses is exactly the state this round exists to make unreachable. */
function writeRun(r, note, previous) {
  r.run_id = runId(r);
  mkdirSync(RECEIPTS, { recursive: true });
  const body = receiptBody(r, note, previous);
  const p = join(RECEIPTS, receiptFile(r));
  const bytes = receiptBytes(body);
  if (existsSync(p) && !readFileSync(p).equals(bytes))
    throw new Error(`receipt ${relative(HERE, p)} already exists with different bytes — a receipt ` +
      `records what happened and is never rewritten`);
  writeFileSync(p, bytes);
  writeFileSync(RUN, renderRun(r));
  return relative(HERE, p);
}
const prevOf = (r) => ({ run_id: r.run_id, status: r.status });

/** THE WHOLE RECORD, AGAINST THE TREE AS IT IS. The subject, instrument,
 *  release, executable and receipt-chain halves are the FROZEN instrument's;
 *  the delivered-bytes half is this file's, because `blind_package.mjs`
 *  describes what ships to the clean room rather than what is measured. */
export function verifyLiveRun(run = null, { requireChain = true } = {}) {
  /* WITH NO ARGUMENT THE FROZEN SIDE READS THE AUTHORITATIVE BYTES ITSELF. A
     record is passed only when it is not on disk yet — a transition checking
     what it is about to write — and then the bytes verified are the bytes
     written, because `renderRun` is the frozen module's own. */
  const v = verifyRun({ runBytes: run === null ? null : renderRun(run), repoRoot: REPO,
    specDir: SPEC, receiptsDir: RECEIPTS, requireChain });
  const pkg = computePackage();
  for (const l of pkg.leaks) v.problems.push(`blind package leak: ${l}`);
  /* P4.7.8. A SYMLINK OR SPECIAL FILE IN THE PACKAGE IS NOT A "LEAK" AND MUST
     STILL REDDEN THE RUN. Two channels because they are two species: forbidden
     CONTENT, and a filesystem object that has no business in a distribution
     artifact — and the second was invisible to every gate until this round. */
  for (const e of pkg.entries ?? []) v.problems.push(`blind package entry: ${e}`);
  /* AND THE RECORD COMPARED AGAINST THE PACKAGE IS THE ONE THE FROZEN SIDE READ,
     never the one this file happens to be holding. When the bytes were refused
     there is no record to compare, and the refusal is already the answer. */
  if (v.run && v.run.blind_package_id !== pkg.blind_package_id)
    v.problems.push(`blind_package_id: pinned ${String(v.run.blind_package_id).slice(0, 24)}… · this ` +
      `tree ${pkg.blind_package_id.slice(0, 24)}… — the bytes the clean room would receive are not ` +
      `the bytes this run pinned`);
  return { ...v, pkg };
}

if (IS_MAIN && argv.includes("--pin")) {
  const rel = readEvidence(join(SPEC, "SPEC-RELEASE.json"));
  const pkg = computePackage();
  const inst = instrumentDigest(SPEC);
  const prior = readRun();
  if (prior && !["ABORTED", "COMPLETE"].includes(prior.status)) {
    console.log(`BLIND-RUN: REFUSED — ${prior.run_id} is ${prior.status} and a run in flight is not ` +
      `replaced silently. Abort it first with \`--abort --reason "<why>"\`.`);
    process.exit(1);
  }
  if (pkg.leaks.length) {
    console.log(`BLIND-RUN: REFUSED — the blind package contains ${pkg.leaks.length} forbidden path(s)`);
    process.exit(1);
  }
  if (!existsSync(join(SPEC, "releases", `${rel.spec_release_id}.json`))) {
    console.log(`BLIND-RUN: REFUSED — ${rel.spec_release_id} is not an archived release`);
    process.exit(1);
  }
  const r = {
    type: RUN_TYPE, status: "PINNED",
    spec_release_id: rel.spec_release_id,
    blind_package_id: pkg.blind_package_id,
    instrument_digest: inst.digest,
    blind_contract_revision: rel.experiment_revision,
    adapters: [{ implementation: "javascript", role: "reference",
      command: ["node", "governance/js_holdout_adapter.mjs", "{{CHALLENGES}}", "{{OUT}}"],
      package_files: [...JS_PACKAGE],
      package_digest: digestOfPaths(REPO, JS_PACKAGE).digest,
      binary_digest: null, binary_path: null, environment: null }],
    run_id: null,
  };
  const where = writeRun(r, "pinned", null);
  /* THE SUPERSEDED RUN IS PRINTED, NOT PERSISTED. `supersedes` was a member of an
     authenticated record naming a run this history deliberately does not reach,
     so the only honest check for it — that its receipt exists — is one the chain
     rule expressly declines to require of unreachable history. Pinning is a
     human act; the id belongs in the operator's hands and in the ledger. */
  console.log(`BLIND-RUN: PINNED — ${r.run_id}\n  release    ${r.spec_release_id}\n  package    ` +
    `${r.blind_package_id} (${pkg.manifest.file_count} files)\n  instrument ${inst.digest.slice(0, 24)}… ` +
    `over ${inst.files.length} files\n  reference  javascript ` +
    `${r.adapters[0].package_digest.slice(0, 24)}…\n  supersedes ` +
    `${prior ? `${prior.run_id} (${prior.status})` : "nothing — this is the first run"}\n` +
    `  receipt    ${where}\nTHIS IS A HUMAN ACT and no gate performs it.`);
  process.exit(0);
}

if (IS_MAIN && argv.includes("--freeze-candidate")) {
  const r = readRun();
  if (!r) { console.log("BLIND-RUN: REFUSED — no run to freeze a candidate into"); process.exit(1); }
  if (!NEXT[r.status]?.includes("CANDIDATE_FROZEN")) {
    console.log(`BLIND-RUN: REFUSED — a candidate may be frozen from PINNED, and this run is ` +
      `${r.status}`);
    process.exit(1);
  }
  const pre = verifyLiveRun().problems;
  if (pre.length) {
    console.log(`BLIND-RUN: REFUSED — the run does not verify as it stands, so nothing may be ` +
      `frozen into it:`);
    for (const x of pre.slice(0, 6)) console.log(`  ${x}`);
    process.exit(1);
  }
  const impl = opt("--implementation", "go");
  const files = (opt("--files") ?? "").split(",").map((s) => s.trim()).filter(Boolean);
  const binary = opt("--binary");
  /* AN IMPLEMENTATION LABEL IS AN IDENTIFIER, NOT A PATH. It names the subject's
     archived observation document, and P4.7.4 checked labels for uniqueness
     alone: `--implementation ../../../escape` froze through this very interface,
     and its terminal evidence would have been written outside the archive. */
  if (!IMPLEMENTATION_RE.test(impl)) {
    console.log(`BLIND-RUN: REFUSED — ${JSON.stringify(impl)} is not an implementation label. A ` +
      `label must match ${IMPLEMENTATION_RE.source}: it is how an observation is attributed AND ` +
      `how its archived document is named, so a label carrying a path separator would carry the ` +
      `run's own terminal evidence out of the archive.`);
    process.exit(1);
  }
  if ((r.adapters ?? []).some((a) => a.implementation === impl)) {
    console.log(`BLIND-RUN: REFUSED — this run already has an adapter called ` +
      `${JSON.stringify(impl)}. An implementation label is how an observation is attributed, so ` +
      `two subjects may not share one.`);
    process.exit(1);
  }
  /* WHICH AGENT, WITH WHAT ACCESS, IS PART OF WHAT THE RESULT MEANS — the
     contract §3a says so, and P4.7 then accepted toolchain:null, model:null,
     tool_version:null and printed CANDIDATE_FROZEN. A provenance field that may
     be empty is a provenance field that will be. */
  const env = { toolchain: opt("--toolchain"), model: opt("--model"),
    tool_version: opt("--tool-version") };
  const blank = Object.entries(env).filter(([, v]) => !v || !String(v).trim()).map(([k]) => k);
  if (blank.length) {
    console.log(`BLIND-RUN: REFUSED — clean-room provenance is REQUIRED and ` +
      `[${blank.join(", ")}] ${blank.length === 1 ? "is" : "are"} empty. BLIND-IMPLEMENTATION-` +
      `CONTRACT §3a makes "which agent, with what access" part of what the result means, so a run ` +
      `that cannot say it has not frozen a candidate — it has named one.`);
    process.exit(1);
  }
  if (!files.length) {
    console.log("BLIND-RUN: REFUSED — --files is required. A candidate with no source digest is " +
      "not frozen; it is merely named, which is what v0.1.0's `status: FROZEN` meant.");
    process.exit(1);
  }
  /* P4.7.2. THE EXECUTABLE IS THE SUBJECT, SO IT IS NOT OPTIONAL. v0.2.0 printed
     `CANDIDATE_FROZEN … NO binary digest` and let the reveal proceed, while the
     frozen contract's own definition of the state names a binary digest. A state
     the machine can enter but the contract does not describe is not a state. */
  if (!binary) {
    console.log("BLIND-RUN: REFUSED — --binary is required. Source is provenance; the EXECUTABLE " +
      "bytes are the subject the measurement actually runs, and CANDIDATE_FROZEN is defined as " +
      "the candidate's source digest, binary digest and recorded environment. `CANDIDATE_FROZEN " +
      "… NO binary digest` was a reachable state and is not one now.");
    process.exit(1);
  }
  if (!existsSync(join(REPO, binary))) {
    console.log(`BLIND-RUN: REFUSED — the declared binary ${binary} does not exist`);
    process.exit(1);
  }
  const pd = digestOfPaths(REPO, files);
  const missing = pd.files.filter((f) => f.sha256 === "ABSENT").map((f) => f.path);
  if (missing.length) {
    console.log(`BLIND-RUN: REFUSED — ${missing.length} declared candidate path(s) do not exist: ` +
      `${missing.slice(0, 4).join(", ")}`);
    process.exit(1);
  }
  const previous = prevOf(r);
  r.adapters.push({
    implementation: impl, role: "candidate",
    command: (opt("--command") ?? `${binary},{{CHALLENGES}},{{OUT}}`).split(",").map((s) => s.trim()),
    package_files: files,
    package_digest: pd.digest,
    binary_digest: sha(readFileSync(join(REPO, binary))),
    binary_path: binary,
    environment: { ...env },
  });
  r.status = "CANDIDATE_FROZEN";
  /* THE POST-CHECK. The freeze must produce a record that verifies, including
     the executable it just bound — otherwise a candidate could be frozen into a
     state from which the reveal is refused, which is a trap rather than a gate. */
  const post = verifyRun({ runBytes: renderRun({ ...r, run_id: runId(r) }), repoRoot: REPO,
    specDir: SPEC, receiptsDir: RECEIPTS, requireChain: false }).problems;
  if (post.length) {
    console.log(`BLIND-RUN: REFUSED — freezing this candidate would produce a record that does not ` +
      `verify:`);
    for (const x of post.slice(0, 6)) console.log(`  ${x}`);
    process.exit(1);
  }
  const where = writeRun(r, `candidate ${impl} frozen`, previous);
  const a = r.adapters.at(-1);
  console.log(`BLIND-RUN: CANDIDATE_FROZEN — ${r.run_id} — ${impl} at ${pd.digest.slice(0, 24)}… over ` +
    `${pd.files.length} file(s), binary ${a.binary_path} ${a.binary_digest.slice(0, 16)}…. The ` +
    `reveal is now permitted and was refused before this. Receipt ${where}, naming ` +
    `${previous.status} ${previous.run_id.slice(0, 20)}… as its predecessor.`);
  process.exit(0);
}

if (IS_MAIN && argv.includes("--reveal")) {
  const r = readRun();
  if (!r) { console.log("BLIND-RUN: REFUSED — no run"); process.exit(1); }
  if (r.status !== "CANDIDATE_FROZEN") {
    console.log(`BLIND-RUN: REVEAL REFUSED — this run is ${r.status}. The challenge set is opened ` +
      `only after the candidate's bytes are frozen; opening it first is how an implementation comes ` +
      `to be adjusted in the light of the thing it is about to be measured on, and it is the one ` +
      `transition this state machine exists to guard.`);
    process.exit(1);
  }
  const pre = verifyLiveRun().problems;
  if (pre.length) {
    console.log(`BLIND-RUN: REVEAL REFUSED — the run does not verify as it stands. A reveal is ` +
      `irreversible and its receipt is immutable, so it may not record that invariants held when ` +
      `they did not:`);
    for (const x of pre.slice(0, 6)) console.log(`  ${x}`);
    process.exit(1);
  }
  const previous = prevOf(r);
  r.status = "REVEALED";
  const where = writeRun(r, opt("--reason", "challenge set opened"), previous);
  console.log(`BLIND-RUN: REVEALED — ${r.run_id}. Receipt ${where}, naming ${previous.status} ` +
    `${previous.run_id.slice(0, 20)}… as its predecessor, so the frozen runner can WITNESS this ` +
    `status rather than read it. Nothing in the holdout may be edited from here; a change to a ` +
    `committed challenge set is a change to the experiment.`);
  process.exit(0);
}

if (IS_MAIN && argv.includes("--complete")) {
  /* Completion is not a status word a human types: it is a measurement that must
     succeed, and it writes what it measured. P4.7.1 got that right and then
     spawned the MUTABLE wrapper for the summary it believed. */
  const r = readRun();
  if (!r) { console.log("BLIND-RUN: REFUSED — no run"); process.exit(1); }
  if (!NEXT[r.status]?.includes("COMPLETE")) {
    console.log(`BLIND-RUN: COMPLETE REFUSED — a run completes from REVEALED, and this one is ` +
      `${r.status}. Completion asserts that two frozen implementations were measured against an ` +
      `opened challenge set; from ${r.status} there is no such measurement to assert.`);
    process.exit(1);
  }
  const pre = verifyLiveRun().problems;
  if (pre.length) {
    console.log(`BLIND-RUN: COMPLETE REFUSED — the run does not verify as it stands:`);
    for (const x of pre.slice(0, 6)) console.log(`  ${x}`);
    process.exit(1);
  }
  /* THE MEASUREMENT IS RE-RUN BY THE FROZEN INSTRUMENT ITSELF — not remembered,
     and not delegated to anything outside `instrument_digest`. The runner's
     bytes are inside the digest `verifyLiveRun` just checked against this tree. */
  let scratch;
  try { scratch = mkdtempSync(join(tmpdir(), "trvm-complete-")); }
  catch { scratch = mkdtempSync(join(HERE, ".complete-scratch-")); }
  const summaryPath = join(scratch, "summary.json");
  const m = spawnSync(process.execPath, [RUNNER, "--holdout", HOLDOUT, "--summary", summaryPath],
    { encoding: "utf8" });
  if (!existsSync(summaryPath)) {
    console.log(`BLIND-RUN: COMPLETE REFUSED — the measurement produced no summary.`);
    console.log((m.stdout ?? "").trim().split("\n").slice(-3).join("\n"));
    process.exit(1);
  }
  const summaryRead = tryParseEvidence(readFileSync(summaryPath), "the measurement summary");
  if (summaryRead.refused) {
    console.log(`BLIND-RUN: COMPLETE REFUSED — ${summaryRead.refused}`);
    process.exit(1);
  }
  const sum = summaryRead.value;
  const bad = [];

  /* THE AUTHORITY BLOCK. Every field is compared against something this process
     recomputed or read from the record — not accepted because the summary says
     so. Against P4.7.1 a nine-line fake producer asserting `harness_ok: true,
     25/25, interop agreed` completed a candidate that only ever called
     `exit 99`. */
  const auth = sum.authority ?? {};
  const expectInstrument = instrumentDigest(SPEC).digest;
  const relRec = readEvidence(join(SPEC, "SPEC-RELEASE.json"));
  const idCheck = [
    ["authority.instrument_digest", auth.instrument_digest, expectInstrument],
    ["authority.run_id", auth.run_id, r.run_id],
    ["authority.status", auth.status, r.status],
    ["authority.spec_release_id", auth.spec_release_id, r.spec_release_id],
    ["authority.holdout_commitment", auth.holdout_commitment, relRec.holdout_commitment],
    ["release", sum.release, r.spec_release_id],
    ["status", sum.status, r.status],
  ];
  for (const [k, got, want] of idCheck)
    if (got !== want)
      bad.push(`${k} is ${String(got).slice(0, 24)}… and this run says ${String(want).slice(0, 24)}…`);
  if (auth.witnessed !== true) bad.push("the measurement did not witness the run's status by receipt chain");
  if (auth.revealed !== true) bad.push("the measurement did not run at a witnessed REVEALED status");
  if (auth.fixture_ok !== true) bad.push("the frozen scorer did not reproduce its synthetic fixture");
  /* THE MEASUREMENT MUST BE OF THIS RUN, IN THIS WORLD. */
  if (resolve(String(auth.world_root ?? "")) !== resolve(REPO))
    bad.push(`the measurement was taken in world ${auth.world_root} and this transition belongs to ` +
      `${REPO} — a measurement of another world cannot complete this run`);
  if (resolve(String(auth.state_root ?? "")) !== resolve(STATE.root))
    bad.push(`the measurement was taken against state root ${auth.state_root} and this transition ` +
      `operates on ${STATE.root}`);

  if (!sum.harness_ok) bad.push("the harness did not pass");
  if (sum.withheld?.length) bad.push(`${sum.withheld.length} adapter(s) were withheld`);

  /* SUBJECT IDENTITIES, NOT SUBJECT COUNTS. */
  const frozen = new Map((r.adapters ?? []).map((a) => [a.implementation, a]));
  const measured = new Map((sum.adapters ?? []).map((a) => [a.implementation, a]));
  for (const k of frozen.keys()) if (!measured.has(k)) bad.push(`frozen subject ${k} was not measured`);
  for (const [k, a] of measured) {
    const f = frozen.get(k);
    if (!f) { bad.push(`the summary reports a subject ${JSON.stringify(k)} this run never froze`); continue; }
    if (a.package_digest !== f.package_digest)
      bad.push(`${k}: measured package digest is not the frozen one`);
    if ((a.binary_digest ?? null) !== (f.binary_digest ?? null))
      bad.push(`${k}: measured binary digest is not the frozen one`);
    if (!/^[0-9a-f]{64}$/.test(String(a.observation_sha256)))
      bad.push(`${k}: no observation document digest, so the measurement cannot be re-checked`);
    if (a.fail) bad.push(`${k}: ${a.fail} unsatisfied predicate(s)`);
    if (a.unresolved) bad.push(`${k}: ${a.unresolved} unresolved predicate(s)`);
    if (a.missing?.length) bad.push(`${k}: ${a.missing.length} unobserved challenge(s)`);
    if (!a.total) bad.push(`${k}: zero predicates evaluated`);
  }
  if (!sum.interop?.measured)
    bad.push("interoperability was NOT MEASURED — completion claims two implementations agreed, " +
      "and with fewer than two there is nothing to claim");
  if ((sum.interop?.findings ?? []).length)
    bad.push(`${sum.interop.findings.length} outstanding UNCLASSIFIED_FINDING(S) — a disagreement ` +
      `is classified by a human before a run completes, never underneath a PASS`);
  if (sum.problems?.length) bad.push(`${sum.problems.length} problem(s) reported by the instrument`);

  if (bad.length) {
    console.log(`BLIND-RUN: COMPLETE REFUSED — ${bad.length} condition(s) unmet:`);
    for (const x of bad.slice(0, 8)) console.log(`  ${x}`);
    process.exit(1);
  }
  const previous = prevOf(r);
  r.status = "COMPLETE";
  r.run_id = runId(r);
  mkdirSync(RECEIPTS, { recursive: true });

  /* THE MEASURED BYTES ARE ARCHIVED, NOT JUST HASHED. P4.7.3 recorded each
     observation's digest while the document itself stayed in the runner's
     scratch directory, so the interoperability comparison the RESULT asserts
     could not be reconstructed once that directory was gone. A digest
     identifies an artifact; it does not make an absent artifact re-checkable. */
  const obsDir = observationsDir(RECEIPTS, r.run_id);
  mkdirSync(obsDir, { recursive: true });
  const archived = [];
  for (const a of sum.adapters ?? []) {
    if (!a.observation_path || !existsSync(a.observation_path)) {
      console.log(`BLIND-RUN: COMPLETE REFUSED — the measurement did not leave an observation ` +
        `document for ${a.implementation} where it said it had.`);
      rmSync(join(RECEIPTS, r.run_id), { recursive: true, force: true });
      process.exit(1);
    }
    const ob = readFileSync(a.observation_path);
    /* AND THE FOREIGN DOCUMENT CROSSES THE BYTE BOUNDARY BEFORE IT IS ARCHIVED,
       so an observation with two readings is refused at the moment of
       completion rather than becoming permanent evidence that re-digests
       perfectly and attributes the measurement differently to two readers. */
    const obRead = tryParseEvidence(ob, `${a.implementation}'s observation document`);
    if (obRead.refused) {
      console.log(`BLIND-RUN: COMPLETE REFUSED — ${obRead.refused}`);
      rmSync(join(RECEIPTS, r.run_id), { recursive: true, force: true });
      process.exit(1);
    }
    if (sha(ob) !== a.observation_sha256) {
      console.log(`BLIND-RUN: COMPLETE REFUSED — ${a.implementation}'s observation document does ` +
        `not digest to what the measurement recorded.`);
      rmSync(join(RECEIPTS, r.run_id), { recursive: true, force: true });
      process.exit(1);
    }
    const dest = observationFile(RECEIPTS, r.run_id, a.implementation);
    if (dest === null) {
      console.log(`BLIND-RUN: COMPLETE REFUSED — ${JSON.stringify(a.implementation)} does not name ` +
        `a file inside the observation archive.`);
      rmSync(join(RECEIPTS, r.run_id), { recursive: true, force: true });
      process.exit(1);
    }
    writeFileSync(dest, ob);
    archived.push({ implementation: a.implementation,
      file: `${r.run_id}/observations/${a.implementation}.json`, sha256: a.observation_sha256 });
  }

  const result = {
    type: RESULT_TYPE, run_id: r.run_id, previous_run_id: previous.run_id,
    spec_release_id: r.spec_release_id, blind_package_id: r.blind_package_id,
    instrument_digest: r.instrument_digest,
    holdout_commitment: relRec.holdout_commitment, holdout_entries: relRec.holdout_entries,
    subjects: (sum.adapters ?? []).map((a) => ({ implementation: a.implementation, role: a.role,
      package_digest: a.package_digest, binary_digest: a.binary_digest,
      observation_sha256: a.observation_sha256,
      predicates: { total: a.total, satisfied: a.pass, unsatisfied: a.fail,
        unresolved: a.unresolved } })),
    observations: archived,
    interop: { measured: sum.interop.measured, pairs: sum.interop.pairs, findings: 0 },
  };
  /* TWO SEATS REMOVED RATHER THAN CHECKED.
     `world_root` was an absolute path on the machine that produced the RESULT, so
     requiring a verifier to agree with it would make the artifact fail on every
     other machine — the environment-coupled-oracle defect P4.4 found in
     `spec_vectors`, which is repaired in the TEST PLANE and never by putting the
     environment into the identity. A verifier already knows which world it is in:
     it is the one the instrument it is running belongs to.
     `note` was prose in a machine-evidence object. P3.1 retired exactly that seat
     one plane down — an unchecked field nested in an authenticated record is
     where evidence hides — and the reasoning belongs in the source and the
     ledger, where it can be read without being mistaken for a claim the verifier
     checked. The RESULT shape is closed, so neither can come back quietly. */
  const rp = join(RECEIPTS, resultFile(r.run_id));
  const bytes = Buffer.from(JSON.stringify(result, null, 1) + "\n", "utf8");
  if (existsSync(rp) && !readFileSync(rp).equals(bytes)) {
    console.log(`BLIND-RUN: COMPLETE REFUSED — a result receipt for ${r.run_id} already exists ` +
      `with different bytes.`);
    process.exit(1);
  }
  writeFileSync(rp, bytes);

  /* THE TERMINAL CLAIM IS VERIFIED BEFORE IT IS ASSERTED. Nothing has been
     announced yet: the COMPLETE transition receipt is what makes this a claim,
     and it is written below. Removing an unannounced RESULT is not rewriting
     history — writing a transition receipt over a RESULT that does not verify
     would be, and P4.7.1 is the round that learned it. */
  const terminal = resultProblems(r, RECEIPTS, { release: relRec, repoRoot: REPO, specDir: SPEC });
  if (terminal.length) {
    console.log(`BLIND-RUN: COMPLETE REFUSED — the result this completion would record does not ` +
      `verify, so no transition asserts it:`);
    for (const x of terminal.slice(0, 6)) console.log(`  ${x}`);
    rmSync(rp, { force: true });
    rmSync(join(RECEIPTS, r.run_id), { recursive: true, force: true });
    process.exit(1);
  }
  const where = writeRun(r, "completed", previous);
  console.log(`BLIND-RUN: COMPLETE — ${r.run_id} — ${result.subjects.length} frozen subject(s) ` +
    `measured over ${relRec.holdout_entries} committed challenges, interoperability MEASURED across ` +
    `${sum.interop.pairs} pair(s) with ZERO outstanding findings. Result receipt ` +
    `${relative(HERE, rp)} with ${archived.length} observation document(s) archived beside it, ` +
    `transition receipt ${where}. Every later verification re-reads those bytes, recomputes their ` +
    `digests and REPLAYS the interoperability comparison from them.`);
  process.exit(0);
}

if (IS_MAIN && argv.includes("--abort")) {
  const r = readRun();
  if (!r) { console.log("BLIND-RUN: REFUSED — no run to abort"); process.exit(1); }
  if (["ABORTED", "COMPLETE"].includes(r.status)) {
    console.log(`BLIND-RUN: REFUSED — already ${r.status}`); process.exit(1);
  }
  const previous = prevOf(r);
  r.status = "ABORTED";
  /* THE REASON GOES IN THE RECEIPT, WHICH HAS A DECLARED SEAT FOR IT, AND NOT IN
     THE RECORD, WHICH DOES NOT. `abort_reason` was a member of an authenticated
     record with no place in its vocabulary — the same species as the `note` and
     `instrument_files` this round retired, found while retiring them. The
     receipt is immutable and its `note` is classified NON_AUTHORITATIVE, so the
     reason is preserved exactly where a reviewer looks for what happened. */
  const reason = opt("--reason", "unspecified");
  const where = writeRun(r, `aborted: ${reason}`, previous);
  console.log(`BLIND-RUN: ABORTED — ${r.run_id} — ${reason}. Receipt ${where}. The release ` +
    `mechanism is untouched; what ended is one experiment's selection.`);
  process.exit(0);
}

if (IS_MAIN) {
  if (!existsSync(RUN)) {
    console.log(`BLIND-RUN: NOT STARTED — no run record, so no implementation is pinned. This is ` +
      `reported rather than silently passed. Pin one with \`node blind_run.mjs --pin\`.`);
    process.exit(0);
  }
  const { problems, inst, chain, result, run } = verifyLiveRun();
  for (const p of problems.slice(0, 12)) console.log(`  ${p}`);
  console.log(problems.length === 0
    ? `BLIND-RUN: PASS — ${run.run_id} — ${run.status}, WITNESSED by a receipt chain that reaches ` +
      `PINNED through previous_run_id; against P4.7.1 editing the status field and recomputing ` +
      `run_id was green with ZERO receipts. RELEASE ${run.spec_release_id.slice(0, 24)}… is ` +
      `archived and is this tree; PACKAGE ${run.blind_package_id.slice(0, 24)}… is the bytes the ` +
      `clean room receives, with governance, the holdout, the ledgers and the briefs PROVEN absent; ` +
      `INSTRUMENT ${inst.digest.slice(0, 16)}… over ${inst.files.length} files inside the experiment ` +
      `surface — including the STATE MACHINE that computed this identity and checked that chain, so ` +
      `the transitions and the measurement share one definition and cannot drift; and ` +
      `${(run.adapters ?? []).length} subject(s) [${(run.adapters ?? []).map((a) => `${a.implementation}:${a.role}`).join(", ")}] ` +
      `each verified against the package digest AND the executable bytes this run froze` +
      (run.status === "COMPLETE"
        ? `; and the TERMINAL CLAIM is witnessed by a RESULT whose archived observation documents ` +
          `re-digest correctly, whose CONFORMANCE is re-scored by the frozen scorer against the ` +
          `committed challenge set with every predicate total DERIVED rather than read, and whose ` +
          `interoperability comparison REPLAYS to zero findings — against P4.7.3 a hand-written ` +
          `COMPLETE transition with no RESULT at all verified green, and against P4.7.4 two ` +
          `archived observations containing {} agreed perfectly while missing all ten challenges`
        : "")
    : `BLIND-RUN: FAIL — ${problems.length} problem(s) with the run` +
      (chain.length ? ` (${chain.length} in the receipt chain)` : "") +
      (result?.length ? ` (${result.length} in the terminal result)` : ""));
  process.exit(problems.length === 0 ? 0 : 1);
}
