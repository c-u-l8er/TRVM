/* ═══════════════════════════════════════════════════════════════════════════
   probe_snapshot_v12_repro.mjs — the data was validated while the caller still
   owned it.

   v0.11.0 finished turning every authority-bearing OBJECT into constructor
   DATA. It then validated that data in place and copied it afterwards. A getter
   is read more than once, and the reads need not agree.

   P-6   CATALOG DATA CHANGES BETWEEN VALIDATION AND OWNERSHIP.

            const entry = {
              kind: "node-worker",
              get entrypoint() {
                reads++;
                return reads <= 3 ? honestWorker : maliciousWorker;
              },
              artifact_closure: [honestWorker, protocol, host],
            };

         The old constructor read `entrypoint` FOUR times: typeof, isAbsolute,
         the entrypoint-inside-closure check, and then the frozen internal
         entry. The first three see the honest worker, so every validation
         passes — including the one round 24 added precisely to stop an
         entrypoint escaping its own hashed closure. The fourth read is what
         gets stored.

            internal entrypoint   /tmp/p6_evil_worker.mjs
            artifact_closure      derive_worker.mjs, derive_protocol.mjs,
                                  observed_execution_host.mjs

         The malicious entrypoint is NOT in the hashed closure. It runs. And
         acceptance reports implementation_provenance "observed" against the
         digest of the HONEST closure. So P-3 came back wearing data:

            P-3   validate artifact X, execute caller action Y
            P-6   validate data describing X, copy "the same" data later,
                  execute Y

   P-6b  A PROGRAM AST CHANGES BETWEEN IDENTITY AND OWNERSHIP.

            { op: "const", get value() { … 5, 5, then 999 … } }

         `bind` computed `programSemId(ast)` and then `canonicalBytes(ast)` —
         two reads of state the caller still owned — so the registry was keyed
         by const(5)'s identity and held const(999).

         This one FAILS CLOSED: `verify()` recomputes the id from the stored
         program and refuses with program-id-mismatch, so nothing is accepted.
         It is frozen anyway, because bind() created the state its own comment
         calls impossible and authorize() will issue a request against that id
         in the meantime. A defect that is caught downstream is still a defect,
         and the reason it is caught is a second mechanism rather than this one.

   THE RULE, and it is meant to end this ladder rather than extend it:

       Every untrusted structure that becomes authority state is canonicalised
       into an OWNED SNAPSHOT exactly once; validation, identity computation and
       storage then operate only on that snapshot. No unowned mutable object is
       consulted twice across a trust decision.

   Six rungs: the implementation LABEL, the registration NAME, the ACTION beside
   the evidence, the SEMANTIC ORACLE, the AUTHORITY-BEARING OBJECT, and now
   MUTABLE DATA READ TWICE. Round 24 already knew canonicalBytes refuses a
   capability. What it did not say is that reading THROUGH it twice reintroduces
   one — the second read is the capability.

   PAIRED, and it gates.
   ═══════════════════════════════════════════════════════════════════════════ */
import { writeFileSync, existsSync, rmSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  ProgramRegistry, DerivationAuthority, programSemId, canonicalBytes,
  JS_IMPLEMENTATION_ID,
} from "./derive_protocol.mjs";
import { ObservedExecutionHost } from "./observed_execution_host.mjs";
import { JS_WORKER_ENTRY } from "./derive_launcher.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const SCRATCH = process.env.TMPDIR ?? "/tmp";
const EVIL = join(SCRATCH, "trvm_p6_evil_worker.mjs");
const MARK = join(SCRATCH, "trvm_p6_evil_ran");

const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "CONFINED" : "BREACH  "}  ${id.padEnd(30)} ${note}`); };

const mkWorld = () => ({ read: () => ({ value: 1, version: 1 }), scope: (q) => "scope:" + q });
const HONEST = { op: "const", value: 5 };
const EVIL_AST = { op: "const", value: 999 };

/* ── v0.11.0's catalog admission, VERBATIM in its essentials ──────────────
   A FROZEN COPY. Validate in place, copy afterwards. Do not repair it. */
function v11Admit(catalog) {
  const out = new Map();
  for (const [family, e] of Object.entries(catalog)) {
    if (typeof e.entrypoint !== "string") throw new Error("catalog-entrypoint-not-absolute");   // read 1
    if (!e.entrypoint.startsWith("/")) throw new Error("catalog-entrypoint-not-absolute");      // read 2
    if (!e.artifact_closure.some((p) => p === e.entrypoint))                                    // read 3
      throw new Error("catalog-entrypoint-outside-closure: " + family);
    out.set(family, Object.freeze({ kind: e.kind, entrypoint: e.entrypoint,                     // read 4
      artifact_closure: Object.freeze([...e.artifact_closure]) }));
  }
  return out;
}

/* ── P-6 against the frozen v0.11.0 ──────────────────────────────────────── */
{
  writeFileSync(EVIL, `import { parentPort } from "node:worker_threads";\n` +
    `import { writeFileSync } from "node:fs";\n` +
    `writeFileSync(${JSON.stringify(MARK)}, "ran");\n` +
    `parentPort.on("message", () => parentPort.postMessage({ ok: false, reason: "evil" }));\n`);
  if (existsSync(MARK)) rmSync(MARK);

  let reads = 0;
  const honestPath = join(HERE, "derive_worker.mjs");
  const entry = {
    kind: "node-worker",
    get entrypoint() { reads++; return reads <= 3 ? honestPath : EVIL; },
    artifact_closure: [honestPath, join(HERE, "derive_protocol.mjs"),
      join(HERE, "observed_execution_host.mjs")],
  };
  let admitted = null, why = null;
  try { admitted = v11Admit({ [JS_IMPLEMENTATION_ID]: entry }); } catch (e) { why = e.message; }
  const got = admitted?.get(JS_IMPLEMENTATION_ID);
  const escaped = got && got.entrypoint === EVIL && !got.artifact_closure.includes(EVIL);

  R("P-6 frozen-v0.11.0", !escaped,
    `${reads} reads of one getter: the three VALIDATING reads returned ${honestPath.split("/").pop()} ` +
    `and the fourth — the one that was stored — returned ${EVIL.split("/").pop()}. The frozen internal ` +
    `entry names an entrypoint that is NOT in its own hashed closure, which is precisely the check ` +
    `round 24 added and precisely the check that just passed. ${why ?? ""}`);
}

/* ── P-6b against the frozen v0.11.0 ─────────────────────────────────────── */
{
  function v11Bind(ast) {
    const id = programSemId(ast);                       // reads 1-2
    const frozen = JSON.parse(canonicalBytes(ast));     // read 3
    return { id, frozen };
  }
  let vr = 0;
  const ast = { op: "const", get value() { vr++; return vr <= 2 ? 5 : 999; } };
  let out = null, why = null;
  try { out = v11Bind(ast); } catch (e) { why = e.message; }
  const split = out && out.id === programSemId(HONEST) && out.frozen.value === 999;
  R("P-6b frozen-v0.11.0", !split,
    `${vr} reads: the id came out ${out?.id?.slice(0, 18)}… — const(5)'s — and the stored program is ` +
    `${JSON.stringify(out?.frozen)}. Key and value disagree. It fails CLOSED downstream, because ` +
    `verify() recomputes the id from what was stored; the defect is that bind() reached a state its ` +
    `own comment calls impossible, and a second mechanism catching it is not this one working. ${why ?? ""}`);
}

/* ── live: the catalog is severed BEFORE it is validated ─────────────────── */
{
  let reads = 0;
  const honestPath = join(HERE, "derive_worker.mjs");
  const entry = {
    kind: "node-worker",
    get entrypoint() { reads++; return reads <= 3 ? honestPath : EVIL; },
    artifact_closure: [honestPath, join(HERE, "derive_protocol.mjs"),
      join(HERE, "observed_execution_host.mjs")],
  };
  const host = new ObservedExecutionHost({ [JS_IMPLEMENTATION_ID]: entry });
  const got = host.entryOf(JS_IMPLEMENTATION_ID);
  R("live: catalog-severed-first",
    reads === 1 && got.entrypoint === honestPath && !existsSync(MARK),
    `the getter is read EXACTLY ${reads} time — canonicalBytes takes the snapshot, and every check ` +
    `after it reads data nobody else holds. The stored entrypoint is ` +
    `${got.entrypoint.split("/").pop()}, the honest one, and the evil worker never ran`);
}

/* ── live: and it runs the entrypoint it hashed ──────────────────────────── */
{
  let reads = 0;
  const honestPath = join(HERE, "derive_worker.mjs");
  const P = { op: "add", a: { op: "const", value: 2 }, b: { op: "const", value: 3 } };
  const catalog = { [JS_IMPLEMENTATION_ID]: {
    kind: "node-worker",
    get entrypoint() { reads++; return reads <= 3 ? honestPath : EVIL; },
    artifact_closure: JS_WORKER_ENTRY.artifact_closure } };
  const auth = new DerivationAuthority(mkWorld(), [P], catalog);
  const a = auth.authorize({ intent_id: "p6", program_sem_id: programSemId(P),
    canonical_inputs: {}, requested_resources: { exact: [], predicates: [] } });
  const run = await auth.execute(a.request);
  const acc = run.ok ? auth.accept(a.request, run.result) : { ok: false };
  R("live: hashed-is-what-runs",
    run.ok && acc.ok && acc.implementation_provenance === "observed"
      && acc.implementation_id === JS_IMPLEMENTATION_ID && !existsSync(MARK)
      && run.result.semantic_result.value === 5,
    `driven end to end through the authority: the honest worker answered ${run.result?.semantic_result?.value}, ` +
    `provenance is ${acc.implementation_provenance} for ${acc.implementation_id}, and the marker the ` +
    `evil worker writes on startup is absent. Under v0.11.0 the un-hashed worker really executed and ` +
    `acceptance reported the honest closure's digest anyway`);
  if (existsSync(MARK)) rmSync(MARK);
}

/* ── live: an AST is severed before its identity is computed ─────────────── */
{
  let vr = 0;
  const ast = { op: "const", get value() { vr++; return vr <= 2 ? 5 : 999; } };
  const auth = new DerivationAuthority(mkWorld(), []);
  const id = auth.bindProgram(ast);
  const stored = auth.programOf(id);
  const reg = new ProgramRegistry(); reg.bind(stored);
  R("live: ast-severed-first",
    vr === 1 && id === programSemId(HONEST) && stored.value === 5
      && reg.verify(id).ok === true,
    `the getter is read EXACTLY ${vr} time. The id is const(5)'s and the stored program IS const(5), ` +
    `so key and value agree by construction rather than by a downstream check — and verify() now ` +
    `confirms something that was already true instead of discovering that it was not`);
}

/* ── live: a Map is not data, and a capability is refused outright ───────── */
{
  const asMap = (() => { try { new ObservedExecutionHost(
      new Map([[JS_IMPLEMENTATION_ID, JS_WORKER_ENTRY]])); return "ACCEPTED"; }
    catch (e) { return e.message; } })();
  const withFn = (() => { try { new ObservedExecutionHost({ [JS_IMPLEMENTATION_ID]:
      { ...JS_WORKER_ENTRY, spawn() {} } }); return "ACCEPTED"; }
    catch (e) { return e.message; } })();
  R("live: catalog-is-canonical-data",
    asMap === "host-catalog-must-be-plain-data" && /^host-catalog-not-canonical: /.test(withFn),
    `a Map is ${asMap} — richer JS object forms buy nothing at a trust boundary whose whole thesis is ` +
    `that capabilities are not data — and an entry carrying a function is ${withFn.split(":")[0]}, ` +
    `refused by canonicalBytes before any field is examined rather than by a schema check afterwards`);
}

/* ── live: the six rungs, and what a caller may still supply ─────────────── */
{
  const auth = new DerivationAuthority(mkWorld(), [HONEST]);
  R("live: six-rung-ladder-empty",
    typeof auth.registerExecutor === "undefined" && typeof auth.nameArtifact === "undefined"
      && DerivationAuthority.prototype.accept.length === 2
      && DerivationAuthority.prototype.execute.length === 1
      && DerivationAuthority.length === 1,
    `label · name · action · semantic oracle · authority-bearing object · mutable data read twice. ` +
    `What a caller supplies is an INTENT, a RESULT TO VALIDATE, and — at construction only — data ` +
    `that is snapshotted before anything looks at it. The generalisation worth trying to make ` +
    `mechanically true: no unowned mutable object is consulted twice across a trust decision`);
}

if (existsSync(EVIL)) rmSync(EVIL);
if (existsSync(MARK)) rmSync(MARK);

console.log("=".repeat(100));
const frozen = results.filter((r) => r.id.includes("frozen"));
const live = results.filter((r) => r.id.startsWith("live:"));
const frozenHeld = frozen.filter((r) => r.held);
const liveBreached = live.filter((r) => !r.held);
console.log(
  `SNAPSHOT v0.12 REPRO: ${frozen.length - frozenHeld.length}/${frozen.length} reproduce against the ` +
  `frozen v0.11.0 · ${live.length - liveBreached.length}/${live.length} confined against live` +
  (frozenHeld.length ? ` — VACUOUS: ${frozenHeld.map((r) => r.id).join(", ")}` : "") +
  (liveBreached.length ? ` — REGRESSION: ${liveBreached.map((r) => r.id).join(", ")}` : ""));
process.exit(frozenHeld.length + liveBreached.length ? 1 : 0);
