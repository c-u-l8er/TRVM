/* ═══════════════════════════════════════════════════════════════════════════
   run_state.mjs — v0.6.0 — THE STATE MACHINE IS PART OF THE INSTRUMENT
   law:proof.state-transition-witnessed@1 · law:proof.terminal-claim-witnessed@1
   law:proof.evidence-shape-unambiguous@1
   law:proof.evidence-bytes-unambiguous@1 · law:proof.run-record-vocabulary-closed@1
   law:proof.authority-bound-to-its-world@1
   law:proof.measurement-authority-frozen@1
   law:proof.executed-subject-is-frozen-subject@1

   P4.7.1 moved the reveal gate into the frozen runner and then handed that gate
   its decisive input from OUTSIDE the freeze:

       node holdout_runner.mjs … --status <string>

   supplied by `governance/holdout_score.mjs`, which is in no digest at all.
   REPRODUCED: change that one argument to the literal "REVEALED", call nothing
   else, and a candidate sitting at CANDIDATE_FROZEN received H1…H10 while
   SPEC-RELEASE, BLIND-RUN and HOLDOUT-SCORE all printed PASS. A frozen decision
   function over an untrusted claim is not an authenticated boundary — it is the
   same function with the trust moved one argument to the left.

   AND THE STATUS ITSELF WAS NOT A FACT ABOUT ANYTHING THAT HAPPENED. P4.7.1's
   receipts were OUTPUTS of transitions and never INPUTS to verification:
   REPRODUCED by editing `status` from CANDIDATE_FROZEN to REVEALED, recomputing
   `run_id` with the tree's own exported `runId()`, and writing NO receipt —
   BLIND-RUN said PASS and the candidate received all ten constructions.

   SO THE STATE MACHINE LIVES HERE, INSIDE `experiment/`, therefore inside
   `experiment_digest`, therefore inside `spec_release_id`, therefore inside the
   `instrument_digest` the run pins. Three things follow, and they are the whole
   of this file:

     1. THE RUN IDENTITY IS COMPUTED BY FROZEN CODE. P4.7.1 computed it in
        mutable `governance/blind_run.mjs`, so the formula that decides whether a
        record identifies itself could be rewritten by the same edit that
        falsified the record.

     2. A STATUS IS A CLAIM UNTIL A RECEIPT CHAIN WITNESSES IT. `chainProblems`
        walks PINNED → … → the current state through `previous_run_id`, and a
        status no chain reaches is not a status.

     3. THE EXECUTED SUBJECT IS THE FROZEN SUBJECT, INCLUDING ITS EXECUTABLE.
        P4.7.1's `verifyLiveRun()` re-digested `package_files` and never
        re-hashed `binary_path`: REPRODUCED by freezing a source file and a
        separate binary, mutating only the binary's bytes, and watching
        `--reveal` succeed.

   AND P4.7.6 CLOSED ALL OF THAT ONE BOUNDARY TOO LATE. Its shape and uniqueness
   checks run over a value `JSON.parse` has already produced, and `JSON.parse`
   keeps the LAST of two duplicate members — so `"status":"REVEALED",
   "status":"PINNED"` in the raw bytes verified green while a first-occurrence
   reader saw the other status. Every read in this file crosses
   `evidence.mjs` now, and the run record is READ HERE FROM ITS BYTES rather than
   accepted as a value the mutable caller parsed: a frozen decision function over
   an untrusted reading is the same defect one argument to the left, which is
   what P4.7.1 was.

   THE RUN RECORD'S OWN VOCABULARY IS CLOSED TOO, WHICH IT WAS NOT. P4.7.6 gave
   the RESULT and the receipts eight closed shapes and left `blind-run.json` open:
   `verdict_override: "COMPLETE_AND_VERIFIED"` and `blindness: "DISQUALIFIED"`
   both verified, `role` was hashed rather than checked against a vocabulary, and
   `instrument_files` — excluded from `runCore` precisely because it is a
   RENDERING of `instrument_digest` — could be zeroed while the digest stayed
   honest. That is the authenticated-rendering-nobody-consumes class this file
   removed from the RESULT one round ago, still sitting in the record the RESULT
   is about. `instrument_files`, `note` and `supersedes` are gone; what remains
   is DERIVED or CHECKED.

   THE PREIMAGE IS DELIBERATELY NOT JSON. This tree has one canonical JSON
   encoder and it belongs to the protocol under test (`governance/cas.mjs`),
   which is both mutable from here and part of the reference SUBJECT — an
   instrument may not compute its own identities with the subject's encoder, and
   a second JCS implementation would be a second thing to keep in agreement. The
   run core is a closed, known shape, so it is rendered as sorted
   `field<TAB>JSON-scalar` lines: every value passes through `JSON.stringify`, so
   a tab or a newline inside a value cannot forge a line.
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, existsSync, readdirSync, statSync, realpathSync } from "node:fs";
import { createHash } from "node:crypto";
import { join, resolve, relative, isAbsolute, sep } from "node:path";
import { compareObservations, scoreRun } from "./holdout_score_core.mjs";
import { parseEvidence, readEvidence, tryReadEvidence, tryParseEvidence } from "./evidence.mjs";

export { parseEvidence, readEvidence, tryReadEvidence, tryParseEvidence };

const sha = (b) => createHash("sha256").update(b).digest("hex");

export const RUN_TYPE = "TRVM-BLIND-IMPLEMENTATION-RUN-v3";
export const RECEIPT_TYPE = "TRVM-BLIND-RUN-RECEIPT-v2";
export const RESULT_TYPE = "TRVM-BLIND-RUN-RESULT-v3";
export const CORE_TYPE = "TRVM-BLIND-RUN-CORE-v1";
export const AUTHORITY_TYPE = "TRVM-HOLDOUT-MEASUREMENT-AUTHORITY-v1";
export const SUMMARY_TYPE = "TRVM-HOLDOUT-RUN-SUMMARY-v2";

export const STATES = Object.freeze(["PINNED", "CANDIDATE_FROZEN", "REVEALED", "COMPLETE", "ABORTED"]);
export const NEXT = Object.freeze({
  PINNED: ["CANDIDATE_FROZEN", "ABORTED"],
  CANDIDATE_FROZEN: ["REVEALED", "ABORTED"],
  REVEALED: ["COMPLETE", "ABORTED"],
  COMPLETE: [], ABORTED: [],
});
/** A candidate sees the challenges at these statuses and at no other — and only
 *  when a receipt chain witnesses the status. */
export const REVEALED_STATES = Object.freeze(["REVEALED", "COMPLETE"]);
export const RUN_ID_RE = /^brun-[0-9a-f]{64}$/;

/** THE MEASURING INSTRUMENT, NAMED FILE BY FILE. Every member lives under
 *  `docs/spec/proof-wire/experiment/`, so `experiment_digest` already covers it
 *  and editing one moves `spec_release_id`. The explicit list is not redundant
 *  with that: it also catches the instrument being MOVED OUT of the experiment
 *  surface, which would silently SHRINK experiment_digest rather than move it. */
export const INSTRUMENT = Object.freeze([
  "experiment/evidence.mjs",
  "experiment/holdout_schema.mjs",
  "experiment/holdout_score_core.mjs",
  "experiment/holdout_runner.mjs",
  "experiment/run_state.mjs",
  "experiment/holdout-observation-v1.schema.json",
  "experiment/holdout-recipe-v1.schema.json",
  "experiment/fixtures",
]);

/** THE ONE DIGEST SHAPE THIS TREE USES: sorted relative paths, each contributing
 *  `path + "\n" + sha256(bytes) + "\n"`, so a RENAME moves the digest as surely
 *  as an edit does and an ABSENT member is recorded rather than skipped. */
export function digestOfPaths(root, paths) {
  const files = [];
  const walk = (rel) => {
    const abs = join(root, rel);
    if (!existsSync(abs)) return files.push({ path: rel.replace(/\\/g, "/"), sha256: "ABSENT" });
    if (statSync(abs).isDirectory())
      return readdirSync(abs).sort().forEach((f) => walk(`${rel}/${f}`));
    files.push({ path: rel.replace(/\\/g, "/"), sha256: sha(readFileSync(abs)) });
  };
  for (const p of [...paths].sort()) walk(p);
  files.sort((a, b) => (a.path < b.path ? -1 : 1));
  return { digest: sha(files.map((f) => f.path + "\n" + f.sha256 + "\n").join("")), files };
}
export const packageDigest = digestOfPaths;
export const instrumentDigest = (specDir) => digestOfPaths(specDir, INSTRUMENT);

/* ── THE RUN IDENTITY ─────────────────────────────────────────────────────── */

/** What the run IS — and as of P4.7.7 that is the WHOLE record but its own id,
 *  because the three members that used to sit outside this core are gone.
 *  `instrument_files` was a rendering of `instrument_digest` that nothing
 *  consumed, so its rows could be zeroed while the digest stayed honest; `note`
 *  was prose inside a machine record, which is P3.1's retired notes seat; and
 *  `supersedes` named a run this history deliberately does not reach, so it
 *  could be checked only by requiring a receipt the chain rule explicitly does
 *  not require to exist. The superseded id is printed by `--pin`, which is a
 *  human act, and it is recorded in the ledger, which is prose on purpose.
 *
 *  Adapters are a SET keyed by their unique implementation label, so they are
 *  sorted here — reordering the array is not a different experiment, but
 *  renaming, re-pointing or re-packaging a subject is. */
export function runCore(r) {
  return {
    type: r.type, status: r.status,
    spec_release_id: r.spec_release_id, blind_package_id: r.blind_package_id,
    instrument_digest: r.instrument_digest, blind_contract_revision: r.blind_contract_revision,
    adapters: [...(r.adapters ?? [])]
      .map((a) => ({
        implementation: a.implementation, role: a.role, package_digest: a.package_digest,
        binary_digest: a.binary_digest ?? null, binary_path: a.binary_path ?? null,
        command: [...(a.command ?? [])],
        package_files: [...(a.package_files ?? [])].sort(),
        environment: a.environment
          ? { toolchain: a.environment.toolchain ?? null, model: a.environment.model ?? null,
              tool_version: a.environment.tool_version ?? null }
          : null,
      }))
      .sort((x, y) => (String(x.implementation) < String(y.implementation) ? -1 : 1)),
  };
}

/** The preimage, rendered line by line. Every scalar goes through
 *  `JSON.stringify`, which cannot emit a raw tab or newline, so the line
 *  structure is not forgeable from inside a value. */
export function preimage(core) {
  const out = [CORE_TYPE];
  const put = (k, v) => out.push(`${k}\t${JSON.stringify(v ?? null)}`);
  for (const k of ["type", "status", "spec_release_id", "blind_package_id", "instrument_digest",
    "blind_contract_revision"]) put(k, core[k]);
  put("adapters", core.adapters.length);
  core.adapters.forEach((a, i) => {
    for (const k of ["implementation", "role", "package_digest", "binary_digest", "binary_path"])
      put(`adapter[${i}].${k}`, a[k]);
    put(`adapter[${i}].command`, a.command.length);
    a.command.forEach((x, j) => put(`adapter[${i}].command[${j}]`, x));
    put(`adapter[${i}].package_files`, a.package_files.length);
    a.package_files.forEach((x, j) => put(`adapter[${i}].package_files[${j}]`, x));
    for (const k of ["toolchain", "model", "tool_version"])
      put(`adapter[${i}].environment.${k}`, a.environment ? a.environment[k] : null);
  });
  return out.join("\n") + "\n";
}
export const runId = (r) => "brun-" + sha(Buffer.from(preimage(runCore(r)), "utf8"));

/** THE BYTES A RUN RECORD IS WRITTEN AS, RENDERED BY THE SAME FILE THAT READS
 *  THEM. `blind_run.mjs` used to `JSON.stringify` the record itself, so the
 *  written shape and the verified shape were two decisions in two files, one of
 *  them mutable. */
export const renderRun = (r) => Buffer.from(JSON.stringify(r, null, 1) + "\n", "utf8");

/* ── WHERE THE STATE LIVES ────────────────────────────────────────────────── */

/** THE STATE ROOT IS NOT SELECTABLE. IT IS DERIVED FROM THE WORLD.
 *
 *  P4.7.2 gave every lifecycle program a `--state-root` flag so the falsifier
 *  battery could stop attacking the live record — which it needed to, and which
 *  it now does a different way. But a selectable state root is a selectable
 *  AUTHORITY, and REPRODUCED: freeze a candidate in the canonical run, never
 *  reveal it, copy the record and its receipt chain into `/tmp/alt`, reveal only
 *  the copy, then measure with `--state-root /tmp/alt` against the canonical
 *  repository. `HOLDOUT-AUTHORITY: PASS`, and the CANONICAL candidate binary
 *  received `H1 H2 H3 H4 H5 H6 H7 H8 H9 H10` while the canonical record still
 *  read CANDIDATE_FROZEN.
 *
 *  The `NON-CANONICAL` stamp stopped that measurement COMPLETING the real run,
 *  and that was the only thing it stopped. **Completion isolation and
 *  secret-release isolation are different invariants**, and by the time the
 *  stamp applies the irreversible event has already happened.
 *
 *  So the authority fact is bound to the SUBJECT it is exercised over, by making
 *  them come from one place: the state root is `<repoRoot>/governance`, and
 *  `repoRoot` is derived from the location of the executing program itself.
 *  A dry run gets a whole sandbox WORLD — its own spec tree, its own governance
 *  state, its own subjects — rather than a sandbox state directory pointed at
 *  the real repository. There is no argument that separates them. */
export function resolveState(repoRoot) {
  const root = join(repoRoot, "governance");
  return { root, runPath: join(root, "blind-run.json"), receiptsDir: join(root, "receipts") };
}

/** A path a run may name: relative, and resolving strictly inside the world the
 *  run belongs to. Symlinks are resolved, because a link is a path that lies. */
export function containedPath(repoRoot, p) {
  if (typeof p !== "string" || !p || isAbsolute(p)) return null;
  const rootReal = existsSync(repoRoot) ? realpathSync(repoRoot) : resolve(repoRoot);
  const abs = resolve(repoRoot, p);
  const target = existsSync(abs) ? realpathSync(abs) : abs;
  return target === rootReal || target.startsWith(rootReal + sep) ? abs : null;
}

/* ── THE EXECUTED SUBJECT ─────────────────────────────────────────────────── */

const PLACEHOLDERS = new Set(["{{CHALLENGES}}", "{{OUT}}"]);
/** The only interpreter a non-binary adapter may be launched through, resolved
 *  by the runner to THIS process's executable rather than to whatever `node`
 *  happens to mean on the path. */
export const INTERPRETERS = new Set(["node"]);

/** THE EXECUTED SUBJECT MUST BE THE FROZEN SUBJECT — checked against the bytes
 *  on disk at the moment of use, not against what the record remembers. Called
 *  by the runner immediately before spawn AND by every transition, because
 *  P4.7.1 checked it in the first place and not the second, so a mutated binary
 *  could not be measured but could still be REVEALED to. */
export function executionProblems(a, repoRoot) {
  const p = [];
  const cmd = a.command ?? [];
  if (!cmd.length) return [`${a.implementation}: no command`];
  const pkg = new Set((a.package_files ?? []).map((x) => x.replace(/\\/g, "/")));
  const pathish = (x) => x.includes("/") || /\.(mjs|cjs|js|py|sh|exe|bin|out)$/.test(x);

  /* P4.7.3. A RUN MAY ONLY AUTHORIZE SUBJECTS INSIDE ITS OWN WORLD. Every path
     the record names must be relative and must resolve, symlinks and all,
     strictly inside the repository this run belongs to. Without this, a run
     record in one place could authorize the execution of a binary in another —
     which is how a REVEALED copy in /tmp handed the real challenge set to the
     canonical candidate while the canonical run was never revealed. */
  for (const [what, path] of [["binary_path", a.binary_path],
    ...(a.package_files ?? []).map((f) => ["package file", f])]) {
    if (path == null) continue;
    if (!containedPath(repoRoot, path))
      p.push(`${a.implementation}: ${what} ${JSON.stringify(path)} does not resolve inside the ` +
        `world this run belongs to (${repoRoot}) — a run may only authorize subjects that are ` +
        `part of it, or one record could open the challenge set to a subject in another tree`);
  }

  if (a.role === "candidate" && !a.binary_path)
    p.push(`${a.implementation}: a CANDIDATE must be launched as its own frozen executable. Source ` +
      `is provenance; the executable bytes are the subject the measurement actually runs`);
  if (a.binary_path && !a.binary_digest)
    p.push(`${a.implementation}: binary_path ${JSON.stringify(a.binary_path)} with NO binary_digest ` +
      `— a path is not a freeze`);

  if (a.binary_path) {
    if (cmd[0] !== a.binary_path)
      p.push(`${a.implementation}: command[0] is ${JSON.stringify(cmd[0])} and the frozen binary is ` +
        `${JSON.stringify(a.binary_path)} — the run would execute something it did not freeze`);
    const abs = join(repoRoot, a.binary_path);
    if (!existsSync(abs)) p.push(`${a.implementation}: frozen binary ${a.binary_path} is absent`);
    else {
      const live = sha(readFileSync(abs));
      if (live !== a.binary_digest)
        p.push(`${a.implementation}: the executable's bytes are ${live.slice(0, 20)}… and the run ` +
          `froze ${String(a.binary_digest).slice(0, 20)}… — verified at the moment of use, because ` +
          `a digest checked earlier is a digest about an earlier file`);
    }
  } else {
    if (!INTERPRETERS.has(cmd[0]))
      p.push(`${a.implementation}: command[0] ${JSON.stringify(cmd[0])} is neither the frozen ` +
        `binary nor one of the permitted interpreters [${[...INTERPRETERS].join(", ")}]`);
    if (!pkg.has(String(cmd[1] ?? "")))
      p.push(`${a.implementation}: the interpreter is handed ${JSON.stringify(cmd[1])}, which is ` +
        `NOT inside the frozen package — an interpreter may only run frozen bytes`);
  }
  for (const x of cmd.slice(a.binary_path ? 1 : 2))
    if (!PLACEHOLDERS.has(x) && pathish(x) && !pkg.has(x))
      p.push(`${a.implementation}: command argument ${JSON.stringify(x)} names a path outside the ` +
        `frozen package`);
  return p;
}

/* ── THE RECEIPT CHAIN ────────────────────────────────────────────────────── */

export function receiptBody(run, note, previous) {
  return {
    type: RECEIPT_TYPE, run_id: run.run_id, status: run.status,
    previous_run_id: previous?.run_id ?? null, previous_status: previous?.status ?? null,
    spec_release_id: run.spec_release_id, blind_package_id: run.blind_package_id,
    instrument_digest: run.instrument_digest,
    adapters: (run.adapters ?? []).map((a) => ({ implementation: a.implementation, role: a.role,
      package_digest: a.package_digest, binary_digest: a.binary_digest ?? null,
      environment: a.environment ?? null })),
    note,
  };
}
export const receiptFile = (run) => `${run.run_id}.${run.status}.json`;
export const receiptBytes = (body) => Buffer.from(JSON.stringify(body, null, 1) + "\n", "utf8");

/** Every well-formed transition receipt in a directory, keyed `run_id|status`.
 *  RESULT receipts and anything that is not a `RECEIPT_TYPE` are not
 *  transitions and are not indexed — a run's history is its transitions. */
export function readReceipts(dir) {
  const index = new Map();
  const refusals = [];
  index.refusals = refusals;
  if (!existsSync(dir)) return index;
  for (const f of readdirSync(dir).sort()) {
    const m = /^(brun-[0-9a-f]{64})\.([A-Z_]+)\.json$/.exec(f);
    if (!m) continue;
    /* THE BYTE BOUNDARY, AND THE REFUSAL IS RECORDED RATHER THAN SKIPPED. A
       receipt whose bytes have two readings used to be dropped silently, and the
       chain then reported the far less useful "no receipt names this run". */
    const r = tryReadEvidence(join(dir, f), `receipt ${f}`);
    if (r.refused) { refusals.push({ file: f, run_id: m[1], status: m[2], refused: r.refused }); continue; }
    if (r.value?.type !== RECEIPT_TYPE) continue;
    index.set(`${m[1]}|${m[2]}`, { file: f, run_id: m[1], status: m[2], body: r.value });
  }
  return index;
}

/** THE STATUS MUST BE WITNESSED, NOT ASSERTED.
 *
 *  P4.7.1's receipts recorded transitions and nothing consumed them, so the
 *  status was whatever the file said. The chain required here is:
 *
 *      PINNED receipt  ←previous_run_id—  CANDIDATE_FROZEN receipt
 *                      ←previous_run_id—  REVEALED receipt   ←…—  the record
 *
 *  Each link must exist as its own immutable file, must name a predecessor whose
 *  status legally precedes it under NEXT, and the walk must terminate at a
 *  PINNED receipt with no predecessor. Receipts unreachable from the current
 *  record are history from a superseded run and are neither validated nor
 *  required to be absent — but nothing unreachable can witness anything. */
export function chainProblems(run, receiptsDir) {
  const p = [];
  const index = readReceipts(receiptsDir);
  /* A REFUSAL IS REPORTED WHERE THE WALK ASKS FOR IT, AND NOWHERE ELSE. Receipts
     unreachable from this record are superseded history and are not validated —
     but a receipt the chain NEEDS and cannot read unambiguously must not
     masquerade as one that does not exist. */
  const refusalFor = (id, status) =>
    (index.refusals ?? []).find((x) => x.run_id === id && x.status === status) ?? null;
  if (!index.size && !(index.refusals ?? []).length)
    return [`no transition receipts exist under ${receiptsDir} — a status is a claim until a ` +
      `receipt chain witnesses it`];

  let cur = index.get(`${run.run_id}|${run.status}`);
  if (!cur) {
    const bad = refusalFor(run.run_id, run.status);
    if (bad)
      return [`the ${run.status} receipt witnessing this run is REFUSED at the byte boundary: ` +
        `${bad.refused}`];
    return [`NO ${run.status} receipt names ${String(run.run_id).slice(0, 24)}… — this record ` +
      `claims a state that no transition ever recorded. Against P4.7.1, editing the status field ` +
      `to REVEALED and recomputing run_id was enough to open the challenge set with ZERO receipts`];
  }

  for (const [k, want] of [["spec_release_id", run.spec_release_id],
    ["blind_package_id", run.blind_package_id], ["instrument_digest", run.instrument_digest]])
    if (cur.body[k] !== want)
      p.push(`the ${run.status} receipt records ${k} ${String(cur.body[k]).slice(0, 20)}… and the ` +
        `record beside it says ${String(want).slice(0, 20)}…`);

  const seen = new Set();
  const path = [];
  for (let step = 0; step < 64; step += 1) {
    const key = `${cur.run_id}|${cur.status}`;
    if (seen.has(key)) { p.push(`the receipt chain revisits ${key} — a history is not a cycle`); break; }
    seen.add(key);
    path.push(cur.status);
    if (cur.body.run_id !== cur.run_id || cur.body.status !== cur.status)
      p.push(`receipt ${cur.file} names run ${String(cur.body.run_id).slice(0, 24)}…/` +
        `${cur.body.status} inside a file called ${cur.file}`);
    /* THE HISTORY ARTIFACT HAS THE SAME AMBIGUITY SPECIES AS THE TERMINAL ONE. */
    const shape = [
      ...shapeProblems(cur.body, RECEIPT_MEMBERS, `receipt ${cur.file}`),
      ...uniqueProblems(cur.body.adapters, `receipt ${cur.file}'s adapters`),
    ];
    for (const x of cur.body.adapters ?? []) {
      shape.push(...shapeProblems(x, RECEIPT_ADAPTER_MEMBERS,
        `receipt ${cur.file}'s adapter ${JSON.stringify(x?.implementation)}`));
      if ((x?.environment ?? null) !== null)
        shape.push(...shapeProblems(x.environment, ENVIRONMENT_MEMBERS,
          `receipt ${cur.file}'s adapter ${JSON.stringify(x?.implementation)} environment`));
    }
    if (shape.length) { p.push(...shape); break; }
    /* P4.7.3. ONE EXPERIMENT HISTORY MEANS ONE RELEASE, ONE PACKAGE AND ONE
       INSTRUMENT, ALL THE WAY BACK. P4.7.2 compared the release across the whole
       chain and the package and instrument only at the top receipt — but none of
       the three may move during a run, so all three are chain-wide now. It costs
       nothing and it makes "this is one history" mechanically true rather than
       true of its last link. */
    for (const [k, want] of [["spec_release_id", run.spec_release_id],
      ["blind_package_id", run.blind_package_id], ["instrument_digest", run.instrument_digest]])
      if (cur.body[k] !== want)
        p.push(`receipt ${cur.file} records ${k} ${String(cur.body[k]).slice(0, 20)}… and this run ` +
          `is ${String(want).slice(0, 20)}… — a run measures one release, one delivered package and ` +
          `one instrument, for the whole of its history`);
    const prevId = cur.body.previous_run_id ?? null;
    const prevStatus = cur.body.previous_status ?? null;
    if (prevId === null) {
      if (cur.status !== "PINNED")
        p.push(`the chain ends at a ${cur.status} receipt with no predecessor — only PINNED begins ` +
          `a run, so this history starts in the middle`);
      if (prevStatus !== null)
        p.push(`receipt ${cur.file} names no predecessor id but claims predecessor status ` +
          `${JSON.stringify(prevStatus)}`);
      break;
    }
    if (!RUN_ID_RE.test(String(prevId))) { p.push(`receipt ${cur.file} names a malformed predecessor`); break; }
    if (!STATES.includes(prevStatus)) {
      p.push(`receipt ${cur.file} names predecessor status ${JSON.stringify(prevStatus)}, which is ` +
        `not a state`);
      break;
    }
    if (!NEXT[prevStatus]?.includes(cur.status)) {
      p.push(`receipt ${cur.file} claims ${prevStatus} → ${cur.status}, which the state machine does ` +
        `not permit`);
      break;
    }
    const prev = index.get(`${prevId}|${prevStatus}`);
    if (!prev) {
      const bad = refusalFor(prevId, prevStatus);
      p.push(bad
        ? `receipt ${cur.file} names predecessor ${String(prevId).slice(0, 24)}…/${prevStatus}, and ` +
          `that receipt is REFUSED at the byte boundary: ${bad.refused}`
        : `receipt ${cur.file} names predecessor ${String(prevId).slice(0, 24)}…/${prevStatus}, ` +
          `and no such receipt exists — the chain is broken, so nothing witnesses this status`);
      break;
    }
    /* THE SUBJECT SET ONLY EVER GROWS, AND ONLY WHERE THE STATE TABLE SAYS.
       A subject carried across a transition must be carried UNCHANGED — same
       package digest, same binary digest — and a new one may only appear on
       PINNED -> CANDIDATE_FROZEN. Without this, a history could quietly swap
       which implementation the later receipts are about while every link still
       named a legal predecessor. */
    const before = new Map((prev.body.adapters ?? []).map((a) => [a.implementation, a]));
    const after = new Map((cur.body.adapters ?? []).map((a) => [a.implementation, a]));
    for (const [k, a] of before) {
      const b = after.get(k);
      if (!b) { p.push(`subject ${JSON.stringify(k)} is in ${prev.file} and gone from ${cur.file}`); continue; }
      const moved = [];
      if (a.role !== b.role) moved.push("role");
      if (a.package_digest !== b.package_digest) moved.push("package_digest");
      if ((a.binary_digest ?? null) !== (b.binary_digest ?? null)) moved.push("binary_digest");
      if (environmentDiffers(a.environment, b.environment)) moved.push("environment");
      if (moved.length)
        p.push(`subject ${JSON.stringify(k)} changed [${moved.join(", ")}] between ${prev.status} ` +
          `and ${cur.status} — a frozen subject is carried unchanged or it was not frozen, and ` +
          `"which agent, with what access" is part of what the result means`);
    }
    const added = [...after.keys()].filter((k) => !before.has(k));
    if (added.length && !(prev.status === "PINNED" && cur.status === "CANDIDATE_FROZEN"))
      p.push(`${added.length} subject(s) [${added.join(", ")}] first appear at ${prev.status} → ` +
        `${cur.status}, and a subject is admitted only at PINNED → CANDIDATE_FROZEN`);
    cur = prev;
  }
  if (!path.includes("PINNED") && !p.length)
    p.push(`the receipt chain from ${run.status} never reaches PINNED within 64 transitions`);
  return p;
}

/* ── THE COMMITTED CHALLENGE SET ──────────────────────────────────────────—
   These two live here rather than in `holdout_runner.mjs` because the TERMINAL
   verifier needs them and the runner imports this file; a checker that cannot
   reach the challenge set cannot replay conformance, and P4.7.4 is what that
   looked like. Neither holds a secret: one digests a directory it is handed and
   the other reads an index out of it. */
export function commitmentOf(holdoutDir, specDir) {
  if (!existsSync(holdoutDir)) return "absent";
  const walk = (d) => readdirSync(d).sort().flatMap((f) => {
    const q = join(d, f);
    return statSync(q).isDirectory() ? walk(q) : [q];
  });
  const files = walk(holdoutDir)
    .map((q) => ({ path: relative(specDir, q), sha256: sha(readFileSync(q)) }))
    .sort((a, b) => (a.path < b.path ? -1 : 1));
  return sha(files.map((f) => f.path + "\n" + f.sha256 + "\n").join(""));
}
export function loadChallenges(holdoutDir) {
  const index = readEvidence(join(holdoutDir, "INDEX.json"), "the challenge-set index");
  return index.entries.map((e) =>
    readEvidence(join(holdoutDir, e.file), `challenge ${e.file}`));
}

/* ── THE TERMINAL CLAIM ───────────────────────────────────────────────────── */

/** AN IMPLEMENTATION LABEL IS AN IDENTIFIER, NOT A PATH. P4.7.4 checked labels
 *  for uniqueness only, and the label is what names a subject's archived
 *  observation document — so `--implementation ../../../escape` froze happily
 *  through the ordinary interface and its terminal evidence would have been
 *  written outside the archive, and outside `governance/` with one more `../`.
 *  The system that had just made SUBJECTS unable to leave their world let a
 *  subject's NAME carry its EVIDENCE out: the same species one layer later. */
export const IMPLEMENTATION_RE = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/;

/* ── ONE ARTIFACT, ONE READING ────────────────────────────────────────────—
   P4.1 killed the duplicate-JSON-member hazard in the WIRE: `JSON.parse` keeps
   the last duplicate, so bytes containing `TRVM-EVIL-v1` were authenticated as
   the honest artifact, and the answer was that a canonical equality makes
   duplicate rejection a CONSEQUENCE rather than a check. The evidence artifacts
   this plane invented since then reintroduced the same species one layer up, in
   ARRAYS keyed by identity: `new Map(res.subjects.map(x => [x.implementation, x]))`
   collapses duplicates with the LAST one winning, and nothing checked first.

   REPRODUCED against P4.7.5, on an honest fully-conforming completed run:
   insert a bogus `javascript` row BEFORE the genuine one in `RESULT.subjects`
   (role candidate, 999/999 predicates, zeroed digests) and BLIND-RUN still says
   PASS — because the verifier reads the last row and a reader resolving by first
   occurrence reads the other one. The same in `RESULT.observations`, and the
   same in a reachable transition receipt's `adapters`. THAT IS AN EQUIVOCATING
   ARTIFACT: it proves the right measurement while presenting two contradictory
   descriptions of it to two reasonable readers.

   And three members were simply never read: a subject's `role` could go
   reference → candidate, a receipt adapter's `role` and `environment` could
   change halfway through the history, and `world_root` could say anything.

   SO EVERY EVIDENCE COLLECTION IS CHECKED FOR UNIQUENESS BEFORE IT IS INDEXED,
   AND EVERY SHAPE IS CLOSED. `law:proof.semantic-vocabulary-closed@1` one plane
   over: a field inside an authenticated record is meaningless unless the
   verifier DERIVES it, CHECKS it, or classifies it NON_AUTHORITATIVE — there is
   no fourth category, and an unclassified member is a refusal. */

/** THE RUN RECORD'S OWN SHAPE, WHICH P4.7.6 LEFT OPEN. Eight closed
 *  vocabularies were written for the RESULT and the receipts and none for
 *  `blind-run.json`, so `verdict_override: "COMPLETE_AND_VERIFIED"` sat in a
 *  verifying record beside `status: "PINNED"` and `blindness: "DISQUALIFIED"`
 *  sat in a verifying adapter. `run_id` is DERIVED — it is recomputed from the
 *  rest and compared — and everything else is CHECKED. There is no
 *  NON_AUTHORITATIVE member here at all, which is the point: the three that
 *  would have been one are gone. */
export const RUN_MEMBERS = Object.freeze({
  type: "CHECKED", status: "CHECKED",
  spec_release_id: "CHECKED", blind_package_id: "CHECKED", instrument_digest: "CHECKED",
  blind_contract_revision: "CHECKED", adapters: "CHECKED", run_id: "DERIVED",
});
export const RUN_ADAPTER_MEMBERS = Object.freeze({
  implementation: "CHECKED", role: "CHECKED", command: "CHECKED",
  package_files: "CHECKED", package_digest: "CHECKED",
  binary_digest: "CHECKED", binary_path: "CHECKED", environment: "CHECKED",
});
/** A ROLE IS A VOCABULARY, NOT A STRING TO HASH. `runCore` bound `role` into the
 *  identity, so changing it moved `run_id` — and a record freshly re-identified
 *  around `role: "arbiter"` was a legal record about a subject the experiment
 *  has no word for. Which subject is the REFERENCE and which the CANDIDATE is
 *  most of what a completed run means. */
export const ROLES = Object.freeze(["reference", "candidate"]);

export const RESULT_MEMBERS = Object.freeze({
  type: "CHECKED", run_id: "CHECKED", previous_run_id: "CHECKED",
  spec_release_id: "CHECKED", blind_package_id: "CHECKED", instrument_digest: "CHECKED",
  holdout_commitment: "CHECKED", holdout_entries: "CHECKED",
  subjects: "CHECKED", observations: "CHECKED", interop: "CHECKED",
});
export const RESULT_SUBJECT_MEMBERS = Object.freeze({
  implementation: "CHECKED", role: "CHECKED", package_digest: "CHECKED",
  binary_digest: "CHECKED", observation_sha256: "CHECKED", predicates: "CHECKED",
});
export const RESULT_OBSERVATION_MEMBERS = Object.freeze({
  implementation: "CHECKED", file: "CHECKED", sha256: "CHECKED",
});
export const PREDICATE_MEMBERS = Object.freeze({
  total: "DERIVED", satisfied: "DERIVED", unsatisfied: "DERIVED", unresolved: "DERIVED",
});
export const INTEROP_MEMBERS = Object.freeze({
  measured: "CHECKED", pairs: "CHECKED", findings: "CHECKED",
});
export const RECEIPT_MEMBERS = Object.freeze({
  type: "CHECKED", run_id: "CHECKED", status: "CHECKED",
  previous_run_id: "CHECKED", previous_status: "CHECKED",
  spec_release_id: "CHECKED", blind_package_id: "CHECKED", instrument_digest: "CHECKED",
  adapters: "CHECKED", note: "NON_AUTHORITATIVE",
});
export const RECEIPT_ADAPTER_MEMBERS = Object.freeze({
  implementation: "CHECKED", role: "CHECKED", package_digest: "CHECKED",
  binary_digest: "CHECKED", environment: "CHECKED",
});
export const ENVIRONMENT_MEMBERS = Object.freeze({
  toolchain: "CHECKED", model: "CHECKED", tool_version: "CHECKED",
});

/** A closed shape: exactly these members, no more and no fewer. */
export function shapeProblems(obj, members, what) {
  if (obj === null || typeof obj !== "object" || Array.isArray(obj))
    return [`${what} is not an object`];
  const p = [];
  for (const k of Object.keys(obj))
    if (!(k in members))
      p.push(`${what} carries an undeclared member ${JSON.stringify(k)} — this shape is CLOSED, ` +
        `because a member of an authenticated record that nothing reads is where evidence hides`);
  for (const k of Object.keys(members))
    if (!(k in obj)) p.push(`${what} is missing ${JSON.stringify(k)}`);
  return p;
}

/** A collection keyed by identity, checked BEFORE it is indexed. */
export function uniqueProblems(list, what) {
  if (!Array.isArray(list)) return [`${what} is not a list`];
  const p = [];
  const seen = new Set();
  for (const x of list) {
    const k = x?.implementation;
    if (!IMPLEMENTATION_RE.test(String(k ?? "")))
      p.push(`${what} names ${JSON.stringify(k)}, which is not an implementation label`);
    else if (seen.has(k))
      p.push(`${what} names ${JSON.stringify(k)} MORE THAN ONCE — a collection keyed by an identity ` +
        `that appears twice has two readings, and an implementation resolving duplicates by first ` +
        `occurrence would describe a different measurement from one resolving by last. This is the ` +
        `duplicate-member hazard P4.1 removed from the wire, in an array instead of an object`);
    seen.add(k);
  }
  return p;
}

/** Two environments agree, member by member, over a closed shape. */
export function environmentDiffers(a, b) {
  if ((a ?? null) === null && (b ?? null) === null) return false;
  if ((a ?? null) === null || (b ?? null) === null) return true;
  return Object.keys(ENVIRONMENT_MEMBERS).some((k) => (a[k] ?? null) !== (b[k] ?? null));
}

/** THE RUN RECORD, READ BEFORE ANY OF IT IS BELIEVED. Shape and vocabulary only:
 *  whether the digests are the tree's, whether the chain witnesses the status and
 *  whether the executables are the frozen ones are `verifyRun`'s. Returned as a
 *  list so an ambiguous record can be refused WITHOUT attempting any further
 *  check — a record with two readings has no single thing to check. */
export function runProblems(run) {
  const p = [
    ...shapeProblems(run, RUN_MEMBERS, "the run record"),
    ...uniqueProblems(run?.adapters, "the run record's adapters"),
  ];
  for (const a of run?.adapters ?? []) {
    const who = `run adapter ${JSON.stringify(a?.implementation)}`;
    p.push(...shapeProblems(a, RUN_ADAPTER_MEMBERS, who));
    if ((a?.environment ?? null) !== null)
      p.push(...shapeProblems(a.environment, ENVIRONMENT_MEMBERS, `${who}'s environment`));
    if (!ROLES.includes(a?.role))
      p.push(`${who} has role ${JSON.stringify(a?.role)}, and a subject of this experiment is a ` +
        `${ROLES.join(" or a ")} — the role was bound into the run identity and never checked ` +
        `against a vocabulary, so re-identifying the record around any word at all made it legal`);
    if (!Array.isArray(a?.command)) p.push(`${who}'s command is not a list`);
    if (!Array.isArray(a?.package_files)) p.push(`${who}'s package_files is not a list`);
  }
  return p;
}

export const resultFile = (id) => `${id}.RESULT.json`;
export const observationsDir = (receiptsDir, id) => join(receiptsDir, id, "observations");
/** The archive destination, or null if it does not land strictly beneath the
 *  observation directory. Positive containment, verified rather than inferred
 *  from the label having matched a pattern — two checks that can disagree are
 *  better than one that cannot be wrong. */
export function observationFile(receiptsDir, id, impl) {
  const dir = observationsDir(receiptsDir, id);
  const abs = resolve(join(dir, `${impl}.json`));
  const root = resolve(dir);
  return abs.startsWith(root + sep) && !relative(root, abs).includes(sep) ? abs : null;
}

/** A COMPLETE RUN MUST BE WITNESSED BY THE MEASUREMENT THAT GIVES THE WORD ITS
 *  MEANING, NOT ONLY BY THE TRANSITION THAT ASSERTED IT.
 *
 *  P4.7.3's `chainProblems()` consumed transition receipts and nothing else, so
 *  a COMPLETE run did not have to show a RESULT at all. REPRODUCED: freeze a
 *  candidate whose entire implementation is `exit 99`, reveal it legitimately,
 *  then synthesize ONLY the legal REVEALED → COMPLETE transition receipt with
 *  this file's own `runId()` and `receiptBody()` — no measurement, no RESULT —
 *  and BLIND-RUN printed `PASS … COMPLETE, WITNESSED by a receipt chain that
 *  reaches PINNED` over two subjects. The mundane half is worse than the forgery
 *  half: after an HONEST completion, deleting or truncating the RESULT left
 *  BLIND-RUN saying PASS, so ordinary evidence loss was invisible — which defeats
 *  the entire reason P4.7.1 introduced a RESULT artifact.
 *
 *  AND A DIGEST IS NOT AN ARTIFACT. The RESULT recorded each observation
 *  document's `observation_sha256` while the documents themselves were written
 *  into the runner's scratch directory and never archived, so a later reviewer
 *  could not reconstruct the observation-level interoperability comparison from
 *  the hashes alone. The bytes are archived beside the RESULT now, and the
 *  interop comparison is REPLAYED from them here rather than believed. */
export function resultProblems(run, receiptsDir, { release = null, repoRoot = null,
  specDir = null } = {}) {
  const want = resultFile(run.run_id);
  const present = existsSync(receiptsDir)
    ? readdirSync(receiptsDir).filter((f) => f.endsWith(".RESULT.json")) : [];
  if (!present.includes(want))
    return [`this run is COMPLETE and NO RESULT receipt named ${want} exists — COMPLETE means a ` +
      `successful measurement happened, so the verifier must consume the artifact that says so. ` +
      `Against P4.7.3 a hand-written COMPLETE transition alone, over a candidate that only ran ` +
      `\`exit 99\`, verified green; so did deleting the RESULT after an honest completion`];
  const p = [];
  /* THE BYTE BOUNDARY BEFORE THE SHAPE BOUNDARY. A RESULT carrying a duplicate
     semantic member is refused here, before `shapeProblems` — which could not
     have seen it, because by then `JSON.parse` had already chosen one. */
  const got = tryReadEvidence(join(receiptsDir, want), `RESULT receipt ${want}`);
  if (got.refused)
    return [`${got.refused} — a terminal claim with two readings is not a terminal claim`];
  const res = got.value;

  /* THE SHAPE AND THE READING FIRST. An artifact with two readings has no single
     thing to check, so nothing below runs until it has exactly one. */
  const ambiguous = [
    ...shapeProblems(res, RESULT_MEMBERS, "the RESULT"),
    ...uniqueProblems(res.subjects, "RESULT.subjects"),
    ...uniqueProblems(res.observations, "RESULT.observations"),
  ];
  for (const x of res.subjects ?? [])
    ambiguous.push(...shapeProblems(x, RESULT_SUBJECT_MEMBERS,
      `RESULT subject ${JSON.stringify(x?.implementation)}`),
      ...shapeProblems(x?.predicates, PREDICATE_MEMBERS,
        `RESULT subject ${JSON.stringify(x?.implementation)}'s predicates`));
  for (const x of res.observations ?? [])
    ambiguous.push(...shapeProblems(x, RESULT_OBSERVATION_MEMBERS,
      `RESULT observation ${JSON.stringify(x?.implementation)}`));
  ambiguous.push(...shapeProblems(res.interop, INTEROP_MEMBERS, "RESULT.interop"));
  if (ambiguous.length) return ambiguous;

  if (res.type !== RESULT_TYPE) p.push(`RESULT type ${JSON.stringify(res.type)} is not ${RESULT_TYPE}`);
  if (res.run_id !== run.run_id)
    p.push(`RESULT ${want} names run ${String(res.run_id).slice(0, 24)}… — a result belonging to ` +
      `another run does not witness this one`);
  for (const [k, v] of [["spec_release_id", run.spec_release_id],
    ["blind_package_id", run.blind_package_id], ["instrument_digest", run.instrument_digest]])
    if (res[k] !== v)
      p.push(`RESULT records ${k} ${String(res[k]).slice(0, 20)}… and this run is ` +
        `${String(v).slice(0, 20)}…`);
  if (release && res.holdout_commitment !== release.holdout_commitment)
    p.push(`RESULT records a holdout commitment the release does not`);

  const trans = readReceipts(receiptsDir).get(`${run.run_id}|COMPLETE`);
  if (trans && (res.previous_run_id ?? null) !== (trans.body.previous_run_id ?? null))
    p.push(`RESULT names predecessor ${String(res.previous_run_id).slice(0, 20)}… and the COMPLETE ` +
      `transition names ${String(trans.body.previous_run_id).slice(0, 20)}…`);

  /* THE SUBJECT SET IS EXACT, IN BOTH DIRECTIONS. */
  const frozen = new Map((run.adapters ?? []).map((a) => [a.implementation, a]));
  const measured = new Map((res.subjects ?? []).map((x) => [x.implementation, x]));
  for (const k of frozen.keys())
    if (!measured.has(k)) p.push(`RESULT does not report frozen subject ${JSON.stringify(k)}`);
  for (const [k, m] of measured) {
    const f = frozen.get(k);
    if (!f) { p.push(`RESULT reports a subject ${JSON.stringify(k)} this run never froze`); continue; }
    if (m.role !== f.role)
      p.push(`RESULT calls ${k} a ${JSON.stringify(m.role)} and this run froze it as a ` +
        `${JSON.stringify(f.role)} — which subject is the REFERENCE and which is the CANDIDATE is ` +
        `most of what a completed run means`);
    if (m.package_digest !== f.package_digest)
      p.push(`RESULT's package digest for ${k} is not the one this run froze`);
    if ((m.binary_digest ?? null) !== (f.binary_digest ?? null))
      p.push(`RESULT's binary digest for ${k} is not the one this run froze`);
  }
  if (res.interop?.measured !== true)
    p.push(`RESULT does not record a MEASURED interoperability result`);
  if ((res.interop?.findings ?? -1) !== 0)
    p.push(`RESULT records ${res.interop?.findings} outstanding finding(s)`);

  if (release && res.holdout_entries !== release.holdout_entries)
    p.push(`RESULT records ${res.holdout_entries} committed challenge(s) and the release commits ` +
      `${release.holdout_entries}`);

  /* EVERY FIELD IS EITHER VERIFIED OR IT IS NOT IN THE ARTIFACT. `observations[]`
     was a rendering nothing consumed, which is the unhashed-`notes`-seat species
     P3.1 retired one plane down: an unchecked member of an authenticated record
     is where evidence hides. */
  const listed = new Map((res.observations ?? []).map((o) => [o.implementation, o]));
  for (const k of measured.keys())
    if (!listed.has(k)) p.push(`RESULT lists no archived observation for ${JSON.stringify(k)}`);
  for (const [k, o] of listed) {
    const m = measured.get(k);
    if (!m) { p.push(`RESULT lists an archived observation for a subject it does not report: ${k}`); continue; }
    if (o.sha256 !== m.observation_sha256)
      p.push(`RESULT's observation list and its subject list disagree about ${k}'s digest`);
    if (o.file !== `${run.run_id}/observations/${k}.json`)
      p.push(`RESULT's archived path for ${k} is ${JSON.stringify(o.file)}, which is not where a ` +
        `subject of this run stores its observation`);
  }

  /* THE OBSERVATION BYTES, ARCHIVED AND RE-CHECKED. */
  const dir = observationsDir(receiptsDir, run.run_id);
  const docs = [];
  for (const [k, m] of measured) {
    const f = observationFile(receiptsDir, run.run_id, k);
    if (f === null) {
      p.push(`subject label ${JSON.stringify(k)} does not name a file inside the observation ` +
        `archive — a label is an identifier, not a path`);
      continue;
    }
    if (!existsSync(f)) {
      p.push(`the observation document for ${k} is not archived at ` +
        `${k}.json beside the RESULT — a digest identifies an artifact, it does not make an absent ` +
        `one re-checkable`);
      continue;
    }
    const bytes = readFileSync(f);
    if (sha(bytes) !== m.observation_sha256) {
      p.push(`the archived observation for ${k} digests ${sha(bytes).slice(0, 20)}… and the RESULT ` +
        `records ${String(m.observation_sha256).slice(0, 20)}…`);
      continue;
    }
    /* AND THE FOREIGN ARTIFACT CROSSES THE SAME BOUNDARY. A digest authenticates
       BYTES, not their READING: an archived observation naming two
       implementations re-digests perfectly and attributes the measurement
       differently to two conforming readers. This is the check that has to hold
       when the document was produced by a Go implementation rather than by the
       reference. */
    const o = tryParseEvidence(bytes, `the archived observation for ${k}`);
    if (o.refused) p.push(o.refused);
    else docs.push({ implementation: k, doc: o.value });
  }
  if (existsSync(dir))
    for (const f of readdirSync(dir))
      if (!measured.has(f.replace(/\.json$/, "")))
        p.push(`${f} is archived beside the RESULT and names no subject of this run`);

  /* AND CONFORMANCE IS REPLAYED, NOT ONLY AGREEMENT.
   *
   *  P4.7.4 retained enough evidence to reproduce the measurement and then
   *  reproduced HALF of it. Two archived documents whose `observations` member
   *  is `{}` agree with each other perfectly: the interop replay finds zero
   *  disagreements, every digest matches, and the RESULT's `25/25` was simply
   *  read. Scoring those same documents against the committed challenge set
   *  gives `missing: 10, pass: 0`. So the terminal verifier now runs the FROZEN
   *  scorer over every archived observation and DERIVES the totals — the
   *  challenge set and the scorer supply the denominator, and no number in this
   *  file is written down. */
  if (!p.length) {
    const holdoutDir = repoRoot ? join(repoRoot, "governance", "holdout") : null;
    const spec = specDir ?? (repoRoot ? join(repoRoot, "docs", "spec", "proof-wire") : null);
    if (!holdoutDir || !existsSync(holdoutDir))
      p.push(`the committed challenge set is not present, so this COMPLETE run's conformance claim ` +
        `cannot be replayed — a terminal claim that cannot be re-derived is not verified`);
    else if (release && commitmentOf(holdoutDir, spec) !== release.holdout_commitment)
      p.push(`the challenge set present does not match the release's holdout commitment, so ` +
        `replaying conformance against it would measure a different experiment`);
    else {
      /* A REFUSAL IS REPORTED, NOT THROWN. `loadChallenges` crosses the byte
         boundary, and a committed challenge with two readings must draw a
         problem a reviewer can read rather than a stack trace from the gate. */
      let challenges;
      try { challenges = loadChallenges(holdoutDir); }
      catch (e) { return [...p, `the committed challenge set cannot be read unambiguously, so this ` +
        `COMPLETE run's conformance claim cannot be replayed: ${e.message}`]; }
      if (release && challenges.length !== release.holdout_entries)
        p.push(`${challenges.length} challenge(s) are present and the release commits ` +
          `${release.holdout_entries}`);
      for (const { implementation, doc } of docs) {
        const m = measured.get(implementation);
        const got = scoreRun(challenges, doc,
          { expectRelease: run.spec_release_id, expectImplementation: implementation });
        if (got.refused) {
          p.push(`replaying ${implementation}'s archived observation against the committed ` +
            `challenge set: ${got.refused}`);
          continue;
        }
        if (got.missing.length)
          p.push(`${implementation}: ${got.missing.length} committed challenge(s) ` +
            `[${got.missing.slice(0, 6).join(" ")}] are UNOBSERVED in the archived document, and ` +
            `the RESULT claims a complete measurement`);
        if (got.fail) p.push(`${implementation}: ${got.fail} predicate(s) are UNSATISFIED on replay`);
        if (got.unresolved)
          p.push(`${implementation}: ${got.unresolved} predicate(s) are UNRESOLVED on replay`);
        /* THE DENOMINATOR IS DERIVED, AND THE RESULT MUST AGREE WITH IT EXACTLY. */
        const want = { total: got.total, satisfied: got.pass, unsatisfied: got.fail,
          unresolved: got.unresolved };
        const said = m?.predicates ?? {};
        for (const k of Object.keys(want))
          if (said[k] !== want[k])
            p.push(`${implementation}: the RESULT claims ${k} ${JSON.stringify(said[k])} and ` +
              `replaying the frozen scorer over the archived bytes derives ${want[k]}`);
      }
    }
  }

  /* AND THE INTEROP CLAIM IS REPLAYED FROM THOSE BYTES, not believed. */
  if (!p.length && docs.length >= 2) {
    const findings = [];
    for (let i = 0; i < docs.length; i += 1)
      for (let j = i + 1; j < docs.length; j += 1)
        findings.push(...compareObservations(docs[i].doc, docs[j].doc));
    if (findings.length)
      p.push(`replaying interoperability over the ARCHIVED observation bytes finds ` +
        `${findings.length} disagreement(s) and the RESULT records zero — the terminal claim is ` +
        `re-checkable, so it is re-checked`);
    const pairs = (docs.length * (docs.length - 1)) / 2;
    if (res.interop?.pairs !== pairs)
      p.push(`RESULT records ${res.interop?.pairs} interop pair(s) and ${docs.length} archived ` +
        `observations make ${pairs}`);
  } else if (!p.length && docs.length < 2) {
    p.push(`only ${docs.length} observation document(s) are archived — completion asserts that two ` +
      `frozen implementations were measured and agreed`);
  }
  return p;
}

/** THE ONE QUESTION THE RUNNER ASKS BEFORE IT WRITES THE SECRET ANYWHERE. */
export function authorizedStatus(run, receiptsDir) {
  const problems = chainProblems(run, receiptsDir);
  return { status: problems.length ? null : run.status,
    revealed: problems.length === 0 && REVEALED_STATES.includes(run.status), problems };
}

/* ── THE WHOLE RECORD ─────────────────────────────────────────────────────── */

/** Every invariant a transition or a measurement depends on, checked against the
 *  tree as it is. `requireChain` is false only for `--pin`, which creates the
 *  first link, and for `--abort`, because a run you cannot abort when it is
 *  broken is a trap. */
export function verifyRun({ runBytes = null, repoRoot, specDir, receiptsDir, requireChain = true }) {
  const inst = instrumentDigest(specDir);
  const relPath = join(specDir, "SPEC-RELEASE.json");
  const relRead = existsSync(relPath)
    ? tryReadEvidence(relPath, "SPEC-RELEASE.json") : { value: null, refused: null };
  const rel = relRead.value;
  const stop = (problems, run = null) => ({ problems, chain: [], result: [], inst, rel, run });
  if (relRead.refused) return stop([relRead.refused]);

  /* THE RECORD IS READ HERE, FROM ITS BYTES, AND BY DEFAULT FROM THE DISK.
     P4.7.1's lesson was that moving a decision into frozen code and leaving its
     premise mutable moves the defect one argument to the left; taking an
     already-parsed object from `blind_run.mjs` left the READING of the record —
     the one thing duplicate members make ambiguous — outside the freeze. So
     with no bytes supplied this reads the authoritative record itself. A caller
     holding a record that is NOT on disk yet passes `renderRun(r)` and thereby
     verifies the exact bytes it is about to write. */
  const runPath = resolveState(repoRoot).runPath;
  const bytes = runBytes ?? (existsSync(runPath) ? readFileSync(runPath) : null);
  if (bytes === null) return stop([`there is no run record at ${runPath}, so no subject is pinned`]);
  const parsed = tryParseEvidence(bytes, "the run record");
  if (parsed.refused) return stop([parsed.refused]);
  const run = parsed.value;

  /* SHAPE AND VOCABULARY BEFORE SEMANTICS, AND NOTHING BELOW RUNS UNTIL THE
     RECORD HAS EXACTLY ONE MEANING. */
  const shape = runProblems(run);
  if (shape.length) return stop(shape, run);

  const problems = [];
  if (run.type !== RUN_TYPE) problems.push(`type ${JSON.stringify(run.type)} is not ${RUN_TYPE}`);
  if (!STATES.includes(run.status)) problems.push(`status ${JSON.stringify(run.status)} is unknown`);
  if (run.run_id !== runId(run))
    problems.push(`run_id does not identify the record beside it — a subject, the instrument, the ` +
      `release, the package or the status moved without the identity moving`);

  if (!existsSync(join(specDir, "releases", `${run.spec_release_id}.json`)))
    problems.push(`the selected release ${run.spec_release_id} is NOT in the immutable archive`);

  for (const m of INSTRUMENT)
    if (!existsSync(join(specDir, m)))
      problems.push(`instrument member ${m} is MISSING from the experiment surface — an instrument ` +
        `outside experiment/ is an instrument outside experiment_digest, and moving it there ` +
        `SHRINKS that digest rather than moving it`);
  if (run.instrument_digest !== inst.digest)
    problems.push(`instrument_digest: pinned ${String(run.instrument_digest).slice(0, 20)}… · this ` +
      `tree ${inst.digest.slice(0, 20)}… — the scorer, runner, state machine, schemas or fixtures ` +
      `moved after the run was pinned, and a measuring instrument that changes mid-experiment ` +
      `measures nothing`);

  const labels = new Set();
  for (const a of run.adapters ?? []) {
    if (labels.has(a.implementation))
      problems.push(`two adapters both call themselves ${JSON.stringify(a.implementation)} — an ` +
        `implementation label is how an observation is attributed, so it must be unique`);
    labels.add(a.implementation);
    if (!IMPLEMENTATION_RE.test(String(a.implementation ?? "")))
      problems.push(`implementation label ${JSON.stringify(a.implementation)} is not an identifier ` +
        `(${IMPLEMENTATION_RE.source}) — the label names the subject's archived observation ` +
        `document, and a label containing a path separator carries that evidence out of the archive`);
    if (!a.package_digest) { problems.push(`adapter ${a.implementation} has no package_digest`); continue; }
    const live = digestOfPaths(repoRoot, a.package_files ?? []);
    if (live.digest !== a.package_digest)
      problems.push(`adapter ${a.implementation} [${a.role}]: package digest ` +
        `${live.digest.slice(0, 20)}… does not match the pinned ${a.package_digest.slice(0, 20)}… ` +
        `— the implementation moved after it was frozen`);
    /* P4.7.2. THE EXECUTABLE IS PART OF THE FREEZE AT EVERY TRANSITION, not only
       immediately before spawn. Against P4.7.1, freezing a source file and a
       separate binary and then mutating only the binary left `--reveal`
       succeeding and BLIND-RUN green. */
    problems.push(...executionProblems(a, repoRoot));
  }

  const candidates = (run.adapters ?? []).filter((a) => a.role === "candidate");
  if (REVEALED_STATES.includes(run.status) && candidates.length === 0)
    problems.push(`this run is ${run.status} with NO frozen candidate — the challenge set was ` +
      `opened against nothing`);

  if (!["ABORTED", "COMPLETE"].includes(run.status) && rel?.spec_release_id !== run.spec_release_id)
    problems.push(`this run is ${run.status} against ${String(run.spec_release_id).slice(0, 20)}… ` +
      `and this tree is ${String(rel?.spec_release_id).slice(0, 20)}…. A later release does not ` +
      `silently move a run: ABORT and pin a new record, or restore the tree`);
  /* AND THE CONTRACT REVISION WAS THE LAST MEMBER NOTHING READ. It is bound into
     the run identity and was never compared with the release it claims to be a
     revision of, so a record could be re-identified around
     `blind_contract_revision: 999` and verify — the same authenticated-member-
     nobody-consumes class as `instrument_files`, one line above it. */
  if (!["ABORTED", "COMPLETE"].includes(run.status) && rel
    && run.blind_contract_revision !== rel.experiment_revision)
    problems.push(`this run pins blind contract revision ` +
      `${JSON.stringify(run.blind_contract_revision)} and the release it names is at experiment ` +
      `revision ${JSON.stringify(rel.experiment_revision)} — the revision of the contract a blind ` +
      `implementer was handed is part of what the run measured`);

  const chain = requireChain ? chainProblems(run, receiptsDir) : [];
  problems.push(...chain);
  /* A TERMINAL CLAIM IS WITNESSED BY ITS MEASUREMENT ARTIFACT, ALWAYS — not only
     when the chain is being walked, because losing the RESULT is exactly the
     ordinary accident this is here to make visible. */
  const result = run.status === "COMPLETE"
    ? resultProblems(run, receiptsDir, { release: rel, repoRoot, specDir }) : [];
  problems.push(...result);
  return { problems, chain, result, inst, rel, run };
}
