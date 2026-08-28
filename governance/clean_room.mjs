/* ═══════════════════════════════════════════════════════════════════════════
   clean_room.mjs — v0.1.0 — THE BROKER SERVES THE BYTES IT VERIFIED
   law:proof.mount-is-a-private-object@1 · law:proof.served-bytes-are-verified-bytes@1

   Every round from P4.7 to P4.7.8 hardened an artifact that no model had yet
   been shown. P4.7.9 is the first code on the other side of the door, and it
   exists because GPT proved the door does not close by checking:

       verify the mount → mount it read-only → start the model

   is INSUFFICIENT, and not by a little. A hard link to an identical-byte file
   outside the mount verifies clean — every digest is correct, because at that
   instant the bytes ARE correct — and then a write to the OUTSIDE name changes
   the verified package with no write to the mount at all. A read-only bind makes
   THAT MOUNT POINT read-only; the object underneath stays writable through every
   other name it has. `nlink === 1` (blind_package.mjs, P4.7.9) refuses the link
   this file's caller can see, and cannot refuse:

     * a second link created AFTER the check, in the window before the first
       model request — the window the check was invented to close, which means
       the check does not close it; and
     * a write file descriptor already open on the inode, which is an alias with
       NO DIRECTORY ENTRY. No walk of any filesystem can ever see one.

   So the structural checks are necessary and are not the answer. The answer is
   that a verification is only as durable as the exclusivity of the reference,
   and this program is built from that sentence in two independent ways:

     THE VIEW IS PRIVATE.   `clean_room.sh` unshares a mount namespace, mounts a
       fresh tmpfs, emits the package into it FROM THE MANIFEST (new inodes, one
       link each, exactly the pinned bpkg), remounts it read-only and only then
       execs this program. That filesystem has no name outside the namespace, no
       second mount point, and no descriptor older than itself. There is no alias
       to create, so there is nothing to check for.

     AND THE BYTES ARE SERVED, NOT THE PATH.   The first act of this program is
       `loadVerifiedPackage()`, which returns the bytes of the walk it verified.
       They are sealed into a Map and the package is never read from disk again.
       A mutation that reached the mount after this instant could not reach the
       model, because the model is not being served from the mount.

   TWO CLOSURES OF ONE SEAM, ON PURPOSE: no alias can exist, and no alias could
   reach the model if one did. That is the same argument the walk makes with its
   lstat and its independent realpath — two checks that can disagree beat one
   that cannot be wrong.

   AND THERE IS NO PATH RESOLUTION LEFT TO ATTACK. `read_file` is a Map lookup on
   a key that came from the manifest. It is not a filesystem operation, so `..`,
   an absolute path, a symlink, a case-folded name and a race are not defended
   against — they are unrepresentable. The blind implementer is served from a
   dictionary whose keys are the manifested paths, and asking for anything
   else returns a refusal naming what is available.

   AND WHAT THE IMPLEMENTER IS TOLD IS AS AUTHENTICATED AS WHAT THEY ARE SHOWN.
   This file's first draft carried the system prompt as a string literal, under a
   comment observing that doing so would be an unbound blind input — the
   `requirements/open/` defect P4.7 closed. The comment named the hazard and the
   code committed it: an instruction reading "ignore the specification and
   hardcode H1-H10" would have reached the implementer with srel, bpkg, the
   instrument digest and the run identity all unchanged. The prompt is a frozen
   document in `experiment/` now, read out of the SEALED bytes.

   WHAT THIS PROGRAM DOES NOT CLAIM. It does not defend against an operator with
   write access to the repository, which is the declared threat ceiling of the
   whole experiment (P4.7.3), and it cannot make OpenRouter honest about which
   weights answered. It removes ordinary aliasing and every TOCTOU between
   verification and use.
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve, sep } from "node:path";
import { loadVerifiedPackage, pinnedPackageId } from "./blind_package.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const sha = (b) => createHash("sha256").update(b).digest("hex");
const ENDPOINT = "https://openrouter.ai/api/v1/chat/completions";

/** THE SEAL. Verify, take the bytes, and let go of the filesystem.
 *
 *  Returns a served package: an inventory and a byte map, and NOTHING that can
 *  be resolved into a filesystem again. Anything the caller does after this
 *  point is done against memory. */
export function seal(mount) {
  const expected = pinnedPackageId();
  if (!expected)
    return { problems: [`there is no pinned run beside ${HERE}, so there is no identity to check ` +
      `this mount against. A mount compared with nothing is not verified.`] };
  const v = loadVerifiedPackage(mount, expected);
  if (v.problems.length) return { problems: v.problems };
  /* THE BYTES OF THE WALK THAT WAS VERIFIED, not a re-read of the same names.
     `loadVerifiedPackage` holds what it hashed; taking it here is what makes
     "served is verified" true by construction rather than by promise. */
  const served = new Map();
  for (const f of v.files) served.set(f.path, v.bytes.get(f.path));
  /* AND THE SEAL IS ITSELF MEASURED, so a transcript can state what was held
     rather than what was intended. Same preimage discipline as the run identity:
     a line-oriented digest over the manifest, not a re-encode of it. */
  const sealDigest = sha(Buffer.from(v.files.map((f) => `${f.path}\t${f.sha256}`).join("\n"), "utf8"));
  return { problems: [], blind_package_id: v.blind_package_id, realpath: v.realpath,
    files: v.files, dirs: v.dirs, served, seal_digest: sealDigest };
}

/** THE WHOLE SURFACE THE BLIND IMPLEMENTER HAS ON THE SPECIFICATION.
 *
 *  Two functions over a dictionary. There is no third, and neither of them takes
 *  a path in any sense a filesystem would recognise. */
export function brokerTools(pkg, log) {
  return {
    list_files() {
      log({ tool: "list_files" });
      return pkg.files.map((f) => `${f.path}  (${pkg.served.get(f.path).length} bytes)`).join("\n");
    },
    read_file({ path }) {
      /* STRICT. A leading "./" or "/" used to be stripped, which is a
         NORMALISATION — two spellings resolving to one object, in the round
         whose whole subject is that two names for one object is the defect.
         There is no filesystem here to be lenient on behalf of, so the key is
         a manifest path exactly, and the refusal does the teaching. */
      const key = String(path ?? "");
      const buf = pkg.served.get(key);
      log({ tool: "read_file", path: key, found: !!buf });
      if (!buf)
        return `REFUSED: "${path}" is not in the package. The package is exactly ` +
          `${pkg.files.length} files and this is a dictionary lookup, not a filesystem — there is ` +
          `no parent directory to reach and no other tree to reach it from. Call list_files().`;
      return buf.toString("utf8");
    },
  };
}

/** THE CANDIDATE'S WORKSPACE — a separate writable tree, and the only thing this
 *  program writes. It is NOT the mount: the mount is read-only, private and, by
 *  the time the model can speak, no longer being read. */
/** THE TOOLS THIS PROGRAM CAN ACTUALLY PERFORM. The package declares what the
 *  implementer is OFFERED; this is what the harness can DO, and `instruction()`
 *  refuses when they differ. */
export const TOOL_NAMES = Object.freeze(["list_files", "read_file", "write_source"]);

export function workspaceWriter(workspace, log) {
  const rootReal = resolve(workspace);
  return function write_source({ path, content }) {
    const rel = String(path ?? "");
    const to = resolve(rootReal, rel);
    /* THE SAME CONTAINMENT RULE THE PACKAGE WALK USES, in the one direction this
       program can still be attacked from: the model chooses this name. */
    if (to !== rootReal && !to.startsWith(rootReal + sep)) {
      log({ tool: "write_source", path: rel, refused: "escapes the workspace" });
      return `REFUSED: "${rel}" resolves outside the workspace.`;
    }
    mkdirSync(dirname(to), { recursive: true });
    writeFileSync(to, String(content ?? ""));
    log({ tool: "write_source", path: rel, bytes: String(content ?? "").length });
    return `wrote ${rel} (${String(content ?? "").length} bytes)`;
  };
}

/** THE INSTRUCTION IS IN THE PACKAGE, AND THIS FILE'S FIRST DRAFT PUT IT HERE.
 *
 *  `SYSTEM` was a string literal in this source, and this comment sat above it
 *  saying that a system prompt written here would be an unbound blind input —
 *  the exact species of defect P4.7 closed when `requirements/open/` turned out
 *  to be one. The comment identified the hazard and the code committed it. An
 *  instruction reading "ignore the specification and hardcode H1-H10" could have
 *  been delivered to the implementer with `srel`, `bpkg`, the instrument digest
 *  and the run identity all unchanged, because none of them covers this file.
 *
 *  **WHAT THE IMPLEMENTER IS TOLD MUST BE AS AUTHENTICATED AS WHAT THEY ARE
 *  SHOWN.** So the prompt is a frozen document inside `experiment/` — therefore
 *  inside `experiment_digest`, therefore inside `srel` — and it is read out of
 *  the SEALED BYTES after verification, not off the disk and not from here.
 *  Editing it moves the release and reddens the run, exactly as editing the
 *  scorer does.
 *
 *  THE EXTRACTION IS DELIBERATELY TRIVIAL, and refuses rather than repairing:
 *  everything strictly between a lone `## SYSTEM` line and a lone `## END
 *  SYSTEM` line. Two markers, or none, is a refusal — a document with two
 *  readings is the P4.7.6 defect, and a lenient parser is how a second one
 *  appears. */
export const PROMPT_FILE = "experiment/CLEAN-ROOM-PROMPT-v1.md";

/** ONE BLOCK, ONE READING. Everything strictly between a lone `## <NAME>` line
 *  and a lone `## END <NAME>` line. Two of either marker, or none, is a REFUSAL
 *  — a document with two readings is the P4.7.6 defect and a lenient parser is
 *  how the second reading arrives. */
function block(text, name, file) {
  const lines = text.split("\n");
  const at = (m) => lines.reduce((a, l, i) => (l.trim() === m ? [...a, i] : a), []);
  const open = at(`## ${name}`), close = at(`## END ${name}`);
  if (open.length !== 1 || close.length !== 1 || close[0] < open[0])
    return { problems: [`${file} must contain exactly one "## ${name}" line followed by exactly ` +
      `one "## END ${name}" line; it has ${open.length} and ${close.length}. An instruction with ` +
      `two readings is not an instruction.`] };
  const body = lines.slice(open[0] + 1, close[0]).join("\n").trim();
  if (!body) return { problems: [`${file} declares an empty ${name} block`] };
  return { problems: [], body };
}

/** EVERY BYTE OF NATURAL LANGUAGE THE IMPLEMENTER RECEIVES, TAKEN FROM `bpkg`.
 *
 *  The system message, the opening turn AND the tool schemas — because a tool
 *  `description` is prose the model reads and reasons from, and leaving those in
 *  the harness while moving the system prompt out would be an exception register
 *  with its fourth entry already missing.
 *
 *  A tool RESULT is not authored here and is deliberately not covered: a listing
 *  is the package describing itself, a byte count is arithmetic, and a refusal
 *  names the key the model asked for. The line is stated in the document rather
 *  than assumed, and it is the one thing in this round I have asked GPT to rule
 *  on rather than decided. */
export function instruction(pkg, implemented) {
  const buf = pkg.served.get(PROMPT_FILE);
  if (!buf) return { problems: [`${PROMPT_FILE} is not in the package, so there is no authenticated ` +
    `instruction to give the implementer. The harness does not carry one of its own.`] };
  const raw = buf.toString("utf8");
  const sys = block(raw, "SYSTEM", PROMPT_FILE);
  const usr = block(raw, "USER", PROMPT_FILE);
  const tls = block(raw, "TOOLS", PROMPT_FILE);
  const problems = [...sys.problems, ...usr.problems, ...tls.problems];
  if (problems.length) return { problems };
  const fence = tls.body.match(/^```json\n([\s\S]*?)\n```$/);
  if (!fence) return { problems: [`${PROMPT_FILE}'s TOOLS block must be one \`\`\`json fence`] };
  let tools;
  try { tools = JSON.parse(fence[1]); }
  catch (e) { return { problems: [`${PROMPT_FILE}'s TOOLS block is not valid JSON: ${e.message}`] }; }
  if (!Array.isArray(tools) || !tools.length)
    return { problems: [`${PROMPT_FILE} declares no tools`] };
  /* AND THE TWO SIDES MAY NOT DRIFT. The document says what the implementer is
     offered; this program says what it can actually do. A tool declared and not
     implemented is a promise the model will spend turns on; a tool implemented
     and not declared is a surface the package never described. */
  const declared = tools.map((t) => t?.function?.name).sort();
  const have = [...implemented].sort();
  if (declared.join("|") !== have.join("|"))
    return { problems: [`${PROMPT_FILE} declares tools [${declared.join(", ")}] and the harness ` +
      `implements [${have.join(", ")}]. The document is what the implementer is offered and this ` +
      `program is what it can do; they are one thing or they are a drift.`] };
  return { problems: [], system: sys.body, user: usr.body, tools,
    sha256: sha(Buffer.from(raw, "utf8")) };
}

async function turn(key, model, messages, tools, seed) {
  const res = await fetch(ENDPOINT, {
    method: "POST",
    headers: { "Authorization": `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({ model, messages, tools, seed,
      max_tokens: 8192, temperature: 0 }),
  });
  if (!res.ok) throw new Error(`OpenRouter ${res.status}: ${(await res.text()).slice(0, 400)}`);
  const body = await res.json();
  if (body.error) throw new Error(`OpenRouter: ${JSON.stringify(body.error).slice(0, 400)}`);
  return body;
}

const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN) {
  const argv = process.argv.slice(2);
  const flag = (n, d = null) => { const i = argv.indexOf(n); return i >= 0 ? argv[i + 1] : d; };
  /* P4.7.3'S RULE: A FLAG SILENTLY IGNORED IS A SILENT NO-OP. */
  const KNOWN = ["--mount", "--workspace", "--transcript", "--model", "--max-turns", "--seed",
    "--selftest"];
  for (const a of argv)
    if (a.startsWith("--") && !KNOWN.includes(a)) {
      console.log(`CLEAN-ROOM: REFUSED — unknown flag ${a}. Known: ${KNOWN.join(" ")}`);
      process.exit(2);
    }
  const mount = flag("--mount");
  if (!mount) { console.log("CLEAN-ROOM: --mount <dir> is required"); process.exit(2); }

  /* ── THE FIRST ACT, BEFORE ANYTHING ELSE CAN HAPPEN ──────────────────────── */
  const pkg = seal(mount);
  if (pkg.problems.length) {
    console.log(`CLEAN-ROOM: SEAL REFUSED — ${pkg.problems.length} problem(s) at ${mount}:`);
    for (const p of pkg.problems.slice(0, 10)) console.log(`  ${p}`);
    process.exit(1);
  }
  console.log(`CLEAN-ROOM: SEALED ${pkg.blind_package_id}\n` +
    `  ${pkg.files.length} files · ${pkg.dirs.length} directories · seal ${pkg.seal_digest.slice(0, 24)}…\n` +
    `  verified at ${pkg.realpath} and READ INTO MEMORY. The package is not read from disk again,\n` +
    `  so the bytes served to the model are the bytes that were verified — which is the only form\n` +
    `  of that promise a hard link cannot break.`);

  if (argv.includes("--selftest")) {
    const p = instruction(pkg, TOOL_NAMES);
    console.log(p.problems.length ? `  INSTRUCTION REFUSED — ${p.problems[0]}`
      : `  instruction ${PROMPT_FILE} sha ${p.sha256.slice(0, 24)}… — system ${p.system.length} ` +
        `chars, opening turn ${p.user.length}, ${p.tools.length} tool(s) ` +
        `[${p.tools.map((t) => t.function.name).join(", ")}], all read from the sealed bytes. The ` +
        `harness sends no natural language of its own.`);
    /* THE DRY RUN IS A FIRST-CLASS CONTROL IN THIS TREE (P4.7.3, falsifier Q).
       It stops before the network, so the sealed inventory can be compared with
       the manifest without spending a token or contacting anyone. */
    console.log(pkg.files.map((f) => `${f.path}\t${f.sha256}`).join("\n"));
    process.exit(0);
  }

  const key = process.env.OPENROUTER_API_KEY;
  if (!key) {
    console.log(`CLEAN-ROOM: REFUSED — OPENROUTER_API_KEY is not set. It is passed through the\n` +
      `  environment and never written to the transcript, the workspace or this repository.`);
    process.exit(2);
  }
  const model = flag("--model", "qwen/qwen3.8-27b");
  const workspace = flag("--workspace");
  if (!workspace) { console.log("CLEAN-ROOM: --workspace <dir> is required"); process.exit(2); }
  if (existsSync(workspace)) {
    /* The same rule the mount has: a workspace assembled on top of whatever was
       already there is not the candidate's own work. */
    console.log(`CLEAN-ROOM: REFUSED — ${workspace} already exists. The candidate's workspace must ` +
      `be a fresh directory, or the implementation is not provably its own.`);
    process.exit(1);
  }
  mkdirSync(workspace, { recursive: true });
  const transcriptPath = flag("--transcript", join(workspace, "TRANSCRIPT.json"));
  const maxTurns = Number(flag("--max-turns", "80"));
  const seed = Number(flag("--seed", "1"));

  const access = [];
  const log = (e) => access.push(e);
  const tools = { ...brokerTools(pkg, log), write_source: workspaceWriter(workspace, log) };

  const instr = instruction(pkg, Object.keys(tools));
  if (instr.problems.length) {
    console.log(`CLEAN-ROOM: REFUSED — ${instr.problems[0]}`);
    process.exit(1);
  }
  console.log(`  instruction ${PROMPT_FILE} sha ${instr.sha256.slice(0, 24)}… — system message, ` +
    `opening turn and all ${instr.tools.length} tool schemas read from the SEALED bytes, so what ` +
    `the implementer is TOLD is inside srel exactly as what they are SHOWN is.`);
  const messages = [{ role: "system", content: instr.system },
    { role: "user", content: instr.user }];
  const usage = { prompt_tokens: 0, completion_tokens: 0 };
  let turns = 0, stop = "max-turns";
  try {
    while (turns < maxTurns) {
      turns++;
      const body = await turn(key, model, messages, instr.tools, seed);
      if (body.usage) {
        usage.prompt_tokens += body.usage.prompt_tokens ?? 0;
        usage.completion_tokens += body.usage.completion_tokens ?? 0;
      }
      const msg = body.choices?.[0]?.message;
      if (!msg) { stop = "no message returned"; break; }
      messages.push(msg);
      const calls = msg.tool_calls ?? [];
      if (!calls.length) { stop = "the model stopped calling tools"; break; }
      for (const c of calls) {
        const fn = tools[c.function?.name];
        let out;
        if (!fn) out = `REFUSED: there is no tool named "${c.function?.name}".`;
        else {
          let args = {};
          try { args = JSON.parse(c.function.arguments || "{}"); }
          catch { out = `REFUSED: arguments were not valid JSON.`; }
          if (out === undefined) { try { out = fn(args); } catch (e) { out = `ERROR: ${e.message}`; } }
        }
        messages.push({ role: "tool", tool_call_id: c.id, content: String(out) });
      }
      process.stdout.write(`  turn ${turns}: ${calls.map((c) => c.function?.name).join(", ")}\n`);
    }
  } catch (e) {
    stop = `ERROR: ${e.message}`;
  }

  /* THE RECORD OF WHAT WAS SERVED, WHICH IS THE EVIDENCE THAT THE BOUNDARY HELD.
     It states the seal, every access, and the messages — so a reviewer can check
     that the model was shown the package and nothing else, rather than take it
     on the word of the program that shielded it. */
  const written = access.filter((a) => a.tool === "write_source" && a.bytes !== undefined);
  const transcript = {
    type: "TRVM-CLEAN-ROOM-TRANSCRIPT-v1",
    blind_package_id: pkg.blind_package_id,
    seal_digest: pkg.seal_digest,
    served_file_count: pkg.files.length,
    instruction_path: PROMPT_FILE,
    instruction_sha256: instr.sha256,
    model, seed, turns, stop, usage,
    files_read: [...new Set(access.filter((a) => a.tool === "read_file" && a.found)
      .map((a) => a.path))].sort(),
    refused_reads: [...new Set(access.filter((a) => a.tool === "read_file" && !a.found)
      .map((a) => a.path))].sort(),
    files_written: written.map((a) => a.path),
    access, messages,
  };
  mkdirSync(dirname(resolve(transcriptPath)), { recursive: true });
  writeFileSync(transcriptPath, JSON.stringify(transcript, null, 1) + "\n");
  console.log(`CLEAN-ROOM: ${stop === "the model stopped calling tools" ? "DONE" : "STOPPED"} — ` +
    `${turns} turn(s), ${transcript.files_read.length}/${pkg.files.length} package files read, ` +
    `${written.length} source file(s) written, ` +
    `${usage.prompt_tokens}+${usage.completion_tokens} tokens. Reason: ${stop}.\n` +
    `  workspace   ${resolve(workspace)}\n  transcript  ${resolve(transcriptPath)}`);
  /* A HARNESS THAT RAN OUT OF TURNS DID NOT FINISH, AND AN EXIT CODE IS WHAT A
     SCRIPT READS. Only a model that stopped calling tools of its own accord is
     a completed session; everything else is reported as one. */
  process.exit(stop === "the model stopped calling tools" ? 0 : 1);
}
