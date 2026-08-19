/* ═══════════════════════════════════════════════════════════════════════════
   probe_execlaunch_v09_repro.mjs — the authority hashed one thing and executed
   another.

   v0.8.0 closed P-2 by refusing to believe a NAME: the authority read the
   artifact's bytes itself and hashed them. Then it called a function the same
   caller had supplied beside the declaration.

       {
         artifact_files: X,   ← the EVIDENCE, which the authority hashes
         spawn: Y             ← an INDEPENDENT caller-controlled ACTION
       }

   Two fields of one object, mechanically unrelated.

   P-3  DECLARED ARTIFACT != SPAWNED EXECUTOR.

            1. hand the authority the GENUINE derive_worker.mjs +
               derive_protocol.mjs as artifact_files
            2. name that digest "impl-c-derive-v0.8.0"
            3. hand execute() a spawn() that does NOT run those files —
               it evaluates the request in-process and changes only the
               returned implementation claim
            4. the authority hashes the declared files, calls the unrelated
               callback, records the observation, and accepts

              → { ok: true, validated: true, fresh_at_check: true,
                  implementation_provenance: "observed",
                  implementation_id: "impl-c-derive-v0.8.0",
                  executable_artifact_id: <digest of the real JS closure> }

        with no C anywhere, and no worker either. So

            authority read bytes X  →  authority launched X

        did not follow. What held was

            authority read bytes X  →  authority invoked callback Y.

   P-3F THE SAME BREACH IN THE FILM PLANE. Supply the real C binary as
        artifact_files — genuine digest, genuine family — and replace run()
        with a callback returning a previously valid film. No C process runs
        and `film_provenance` is still "observed" against the real C artifact
        id. Useful because it separates two truths cleanly: the film IS
        semantically valid, `replaySemFilm` proves it, and the claimed C
        execution provenance is false.

   THE LAW:

       Artifact observation does not establish execution provenance unless the
       mechanism that is invoked is mechanically DERIVED FROM the artifact that
       was observed. A launch descriptor may not carry both the evidence and an
       independent executable action.

   Freezing the naming policy does not fix this and neither does another handle.
   The repair is that the caller no longer supplies a mechanism at all: an
   immutable executor catalog, fixed at the host's construction, from which the
   entrypoint AND the transport are both consequences of one entry.

   PAIRED, and it gates.
   ═══════════════════════════════════════════════════════════════════════════ */
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import {
  ProgramRegistry, DerivationAuthority, deriveLocally, validateForeignResult,
  JS_IMPLEMENTATION_ID, requestSemId, canonicalBytes,
} from "./derive_protocol.mjs";
import { ObservedExecutionHost, digestArtifactFiles } from "./observed_execution_host.mjs";
import { JS_WORKER_ENTRY, defaultDeriveCatalog } from "./derive_launcher.mjs";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";

const TERM_1STEP = "(\u03bbx.\u03bbt.(t x) \u03bby.y)";

const HERE = dirname(fileURLToPath(import.meta.url));
const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "CONFINED" : "BREACH  "}  ${id.padEnd(30)} ${note}`); };

const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const mkWorld = () => ({ res: { fb: { value: 5, version: 1 } },
  read(r) { return { ...this.res[r] }; }, scope(q) { return "scope:" + q; } });
const reg = new ProgramRegistry(); const PID = reg.bind(P);
const C_ID = "impl-c-derive-v0.8.0";
const JS_CLOSURE = [join(HERE, "derive_worker.mjs"), join(HERE, "derive_protocol.mjs")];

/* ── v0.8.0's execute/accept, VERBATIM in their essentials ────────────────
   A FROZEN COPY. It is wrong on purpose and must stay wrong. Do not repair it:
   the value of this file is that the breach keeps reproducing, and a future
   edit that fixes the frozen side instead of the live one fails here. */
class V8Authority {
  #observed = new Map();
  #names = new Map();
  #sessions = 0;
  nameArtifact(digest, family) { this.#names.set(digest, family); return { ok: true }; }
  async execute(req, launcher) {
    // 1. THE AUTHORITY hashes the artifact — genuinely, and it is genuinely
    //    the declared one. That was never the hole.
    const executable_artifact_id = digestArtifactFiles(launcher.artifact_files);
    const implementation_family_id = this.#names.get(executable_artifact_id);
    if (implementation_family_id === undefined)
      return { ok: false, reason: "artifact-unnamed" };
    const executor_session_id = "xs-" + createHash("sha256")
      .update(executable_artifact_id + "|" + String(this.#sessions++)).digest("hex");
    // 2. …and then calls a function that has nothing to do with it.
    const session = await launcher.spawn();
    const envelope = await session.send(req);
    await session.close();
    if (!envelope?.ok) return { ok: false, reason: envelope?.reason ?? "nothing" };
    const key = "xk-" + createHash("sha256")
      .update("v8|" + requestSemId(req) + "|" + canonicalBytes(envelope.result)).digest("hex");
    this.#observed.set(key, { implementation_family_id, executable_artifact_id, executor_session_id });
    return { ok: true, result: envelope.result };
  }
  accept(registry, req, res) {
    const v = validateForeignResult(registry, req, res);
    if (!v.ok) return v;
    const key = "xk-" + createHash("sha256")
      .update("v8|" + requestSemId(req) + "|" + canonicalBytes(res)).digest("hex");
    const o = this.#observed.get(key);
    if (o === undefined) return { ok: false, reason: "implementation-provenance-unavailable" };
    if ("expected_implementation_id" in req && o.implementation_family_id !== req.expected_implementation_id)
      return { ok: false, reason: "implementation-mismatch" };
    return { ok: true, validated: true, fresh_at_check: true,
      implementation_provenance: "observed", implementation_id: o.implementation_family_id,
      executable_artifact_id: o.executable_artifact_id };
  }
}

/* ── P-3 against the frozen v0.8.0 ───────────────────────────────────────── */
{
  const issuer = new DerivationAuthority(mkWorld(), [P]);
  const v8 = new V8Authority();
  v8.nameArtifact(digestArtifactFiles(JS_CLOSURE), C_ID);
  const { request: req } = issuer.authorize({ intent_id: "p3", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } },
    { expected_implementation_id: C_ID });

  let launchedTheDeclaredFiles = false;
  const liar = {
    artifact_files: JS_CLOSURE,                    // the real thing, honestly declared
    async spawn() {                                // and never run
      return { async send(r) {
        const { expected_implementation_id: _w, ...bare } = r;
        const res = deriveLocally(reg, bare).result;
        return { ok: true, result: { ...res, request_id: r.request_id,
          execution_evidence: { ...res.execution_evidence, implementation_id: C_ID } } };
      }, async close() {} };
    },
  };
  const x = await v8.execute(req, liar);
  const acc = x.ok ? v8.accept(reg, req, x.result) : { ok: false };
  R("P-3 frozen-v0.8.0",
    !(acc.ok && acc.implementation_provenance === "observed" && acc.implementation_id === C_ID),
    `the declared files were never launched (${launchedTheDeclaredFiles}); an unrelated callback ` +
    `evaluated the request in-process and stamped it ${C_ID} — and acceptance returned ok=${acc.ok}, ` +
    `provenance ${acc.implementation_provenance}, id ${acc.implementation_id}, artifact ` +
    `${String(acc.executable_artifact_id).slice(0, 12)}… which is the digest of the REAL JS closure. ` +
    `The hash was honest and answered a question nobody had asked`);
}

/* ── P-3F: the same breach in the film plane, RUN rather than described ───
   A frozen copy of v0.8.0's FilmAuthority, reduced to its essentials. It is
   given the real C binary as artifact_files and a run() that returns a film
   that binary produced EARLIER — so the digest is genuinely C's, and nothing
   C-shaped executes during this observation. */
class V8FilmAuthority {
  #observed = new Map();
  #names = new Map();
  nameArtifact(digest, family) { this.#names.set(digest, family); return { ok: true }; }
  emit(term, launcher) {
    const artifact = digestArtifactFiles(launcher.artifact_files);   // honest, and really C's
    const family = this.#names.get(artifact);
    if (family === undefined) return { ok: false, reason: "artifact-unnamed" };
    const out = JSON.parse(launcher.run(term));                      // …and unrelated to it
    if (!out.ok) return { ok: false, reason: out.reason };
    this.#observed.set("fk-" + createHash("sha256")
      .update("v8f|" + term + "|" + canonicalBytes(out.film)).digest("hex"),
      { family, artifact });
    return { ok: true, film: out.film };
  }
  accept(term, film) {
    const o = this.#observed.get("fk-" + createHash("sha256")
      .update("v8f|" + term + "|" + canonicalBytes(film)).digest("hex"));
    return o ? { ok: true, film_provenance: "observed", implementation_id: o.family,
                 executable_artifact_id: o.artifact }
             : { ok: true, film_provenance: "unavailable" };
  }
}
{
  const BIN = join(HERE, "bridge", "ic32_film");
  let digest = null;
  try { digest = digestArtifactFiles([BIN]); } catch { /* unbuilt: see below */ }
  if (digest === null) {
    R("P-3F frozen-v0.8.0", false,
      "bridge/ic32_film is not built, so this witness measured NOTHING. A probe that cannot run its " +
      "own attack is vacuous, and reporting it as confined would be worse than not having it " +
      "(law:evidence.instrument-nonvacuity@1). Build it: make gov-film");
  } else {
    // one honest C run FIRST, purely to obtain a film C really did make
    const realFilm = JSON.parse(execFileSync(BIN, [TERM_1STEP]).toString()).film;
    const v8f = new V8FilmAuthority();
    v8f.nameArtifact(digest, "impl-c-ic32-film-v0.1.0");
    let ranC = false;
    const smuggled = { artifact_files: [BIN],
      run: () => { /* no exec here */ return JSON.stringify({ ok: true, film: realFilm }); } };
    const e = v8f.emit(TERM_1STEP, smuggled);
    const acc = e.ok ? v8f.accept(TERM_1STEP, e.film) : { ok: false };
    R("P-3F frozen-v0.8.0",
      !(acc.ok && acc.film_provenance === "observed" && acc.executable_artifact_id === digest),
      `ranC during the observation: ${ranC}. The declaration named the REAL C binary so the digest is ` +
      `genuinely ${String(acc.executable_artifact_id).slice(0, 12)}…, the film came from a caller ` +
      `callback, and acceptance returned film_provenance ${acc.film_provenance} for ` +
      `${acc.implementation_id}. This is the useful separation: the film IS semantically valid — ` +
      `replaySemFilm would accept it — and the claimed C execution provenance is FALSE`);
  }
}

/* ── live: there is no launcher parameter, on either path ─────────────────── */
{
  const host = new ObservedExecutionHost(defaultDeriveCatalog(JS_IMPLEMENTATION_ID));
  const auth = new DerivationAuthority(mkWorld(), [P], host);
  const { request: req } = auth.authorize({ intent_id: "l1", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  let ranMine = false;
  const liar = { artifact_files: JS_CLOSURE,
    spawn: () => { ranMine = true; return { send: () => ({ ok: true, result: null }), close() {} }; } };
  const x = await auth.execute(req, liar);
  const acc = x.ok ? auth.accept(req, x.result) : { ok: false };
  R("live: no-launcher-parameter",
    !ranMine && x.ok && acc.ok && acc.implementation_id === JS_IMPLEMENTATION_ID
      && DerivationAuthority.prototype.execute.length === 1
      && typeof auth.nameArtifact === "undefined",
    `execute takes ${DerivationAuthority.prototype.execute.length} parameter (req) and a ` +
    `second carrying artifact_files beside spawn() is inert — the callback never ran (${ranMine}) and ` +
    `the catalogued worker did. nameArtifact is gone too: the catalog IS the naming policy`);
}

/* ── live: the launch mechanism is a consequence of the catalog entry ─────── */
{
  const host = new ObservedExecutionHost(defaultDeriveCatalog(JS_IMPLEMENTATION_ID));
  const entry = host.entryOf(JS_IMPLEMENTATION_ID);
  const fields = Object.keys(entry).sort().join(",");
  const withAction = (() => { try {
    new ObservedExecutionHost({ [JS_IMPLEMENTATION_ID]: { ...JS_WORKER_ENTRY, spawn: () => {} } });
    return "ACCEPTED"; } catch (e) { return e.message; } })();
  const outside = (() => { try {
    new ObservedExecutionHost({ [JS_IMPLEMENTATION_ID]: { kind: "node-worker",
      entrypoint: join(HERE, "derive_worker.mjs"), artifact_closure: [join(HERE, "grid_check.mjs")] } });
    return "ACCEPTED"; } catch (e) { return e.message; } })();
  R("live: catalog-carries-no-action",
    fields === "artifact_closure,entrypoint,kind" && /^catalog-entry-extra-field: /.test(withAction)
      && /^catalog-entrypoint-outside-closure: /.test(outside),
    `a catalog entry is {${fields}} — a KIND, whose transport is written in the host, and an entrypoint ` +
    `that must lie inside the closure being hashed. An entry carrying a function is refused ` +
    `(${withAction.split(":")[0]}) and an entrypoint outside its own closure is refused ` +
    `(${outside.split(":")[0]}), which is P-3 with the descriptor moved indoors`);
}

/* ── live: nothing a caller passes to run() is ever invoked ───────────────── */
{
  const host = new ObservedExecutionHost(defaultDeriveCatalog(JS_IMPLEMENTATION_ID));
  let called = false;
  const r = await host.run(JS_IMPLEMENTATION_ID, "probe", { init: {}, message: {},
    sneak: () => { called = true; } });
  R("live: invocation-is-data",
    !called && !r.ok && /^invocation-not-canonical: /.test(r.reason),
    `${r.reason} — the invocation goes through canonicalBytes, which refuses a function outright, so ` +
    `there is no way to smuggle an action through the one argument a caller still controls. That is ` +
    `mechanical rather than a convention: the same rule the message domain has enforced since v0.1.0`);
}

/* ── live: the catalog is immutable after construction ───────────────────── */
{
  const catalog = { [JS_IMPLEMENTATION_ID]: { ...JS_WORKER_ENTRY } };
  const host = new ObservedExecutionHost(catalog);
  // mutate the object the caller still holds
  catalog[JS_IMPLEMENTATION_ID].entrypoint = join(HERE, "grid_check.mjs");
  catalog["impl-c-smuggled-v1"] = JS_WORKER_ENTRY;
  const after = host.entryOf(JS_IMPLEMENTATION_ID);
  const frozenHost = Object.isFrozen(host);
  const fams = host.families();
  R("live: catalog-immutable-after-construction",
    after.entrypoint.endsWith("derive_worker.mjs") && fams.length === 1 && frozenHost === true,
    `editing the caller's own catalog object after construction changes nothing the host will do — the ` +
    `entrypoint is still ${after.entrypoint.split("/").pop()} and the host still holds ` +
    `${fams.length} family. Entries are copied and frozen, the host is frozen, and there is no setter`);
}

/* ── live: an observation names EVERY session that produced these bytes ──── */
{
  const host = new ObservedExecutionHost(defaultDeriveCatalog(JS_IMPLEMENTATION_ID));
  const auth = new DerivationAuthority(mkWorld(), [P], host);
  const { request: req } = auth.authorize({ intent_id: "l5", program_sem_id: PID,
    canonical_inputs: { bias: 0 }, requested_resources: { exact: ["fb"], predicates: [] } });
  const a = await auth.execute(req);
  const b = await auth.execute(req);        // same bytes out, second launch
  const acc = auth.accept(req, b.result);
  R("live: sessions-are-plural",
    a.ok && b.ok && a.executor_session_id !== b.executor_session_id
      && Array.isArray(acc.executor_sessions) && acc.executor_sessions.length === 2
      && acc.executor_sessions.includes(a.executor_session_id)
      && acc.executor_sessions.includes(b.executor_session_id),
    `two launches produced byte-identical results and therefore share one execution key; acceptance ` +
    `reports ${acc.executor_sessions.length} sessions rather than one. v0.8.0 stored a single record ` +
    `per key, so the second overwrote the first, and it then reported one executor_session_id as if it ` +
    `named the launch that produced the copy in hand. It never did`);
}

console.log("=".repeat(100));
const frozen = results.filter((r) => r.id.includes("frozen"));
const live = results.filter((r) => r.id.startsWith("live:"));
const frozenHeld = frozen.filter((r) => r.held);
const liveBreached = live.filter((r) => !r.held);
console.log(
  `EXEC-LAUNCH v0.9 REPRO: ${frozen.length - frozenHeld.length}/${frozen.length} reproduce against the ` +
  `frozen v0.8.0 · ${live.length - liveBreached.length}/${live.length} confined against live` +
  (frozenHeld.length ? ` — VACUOUS: ${frozenHeld.map((r) => r.id).join(", ")}` : "") +
  (liveBreached.length ? ` — REGRESSION: ${liveBreached.map((r) => r.id).join(", ")}` : ""));
process.exit(frozenHeld.length + liveBreached.length ? 1 : 0);
