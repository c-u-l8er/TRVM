/* ═══════════════════════════════════════════════════════════════════════════
   observed_execution_host.mjs — v0.5.0 — the only thing here that runs anything

   P-3: THE AUTHORITY HASHED ONE THING AND EXECUTED ANOTHER.

   v0.8.0 closed P-2 by making the authority read and hash the artifact itself
   instead of believing a name. It then called a function the same caller had
   supplied alongside the declaration:

       {
         artifact_files: X,   ← the EVIDENCE, which the authority hashes
         spawn: Y             ← an INDEPENDENT caller-controlled ACTION
       }

   Two fields of one object, mechanically unrelated. Declare the genuine JS
   worker closure, name that digest "impl-c-derive-v0.8.0", and hand over a
   spawn() that evaluates the request in-process and stamps the result C:

       execute  → ok
       accept   → ok, implementation_provenance "observed",
                  implementation_id "impl-c-derive-v0.8.0",
                  executable_artifact_id <digest of the real JS closure>

   with no C anywhere. So the proposition "authority read bytes X, therefore
   authority launched X" did not follow; what held was "authority read bytes X,
   then invoked callback Y". Frozen as P-3 (derivation plane) and P-3F (film
   plane) in probe_execlaunch_v09_repro.mjs.

   THE LAW:

       Artifact observation does not establish execution provenance unless the
       mechanism that is invoked is mechanically DERIVED FROM the artifact that
       was observed. A launch descriptor may not carry both the evidence and an
       independent executable action.

   So this module exists, and the repair is structural rather than another
   handle: an IMMUTABLE EXECUTOR CATALOG, fixed at construction, from which the
   entrypoint AND the launch mechanism are both consequences of the same entry.
   Nothing a caller passes to run() is ever invoked — the invocation is DATA,
   checked to be data, and the transport for each `kind` is written here.

       family name  →  catalog entry  →  artifact closure  →  hash
                                      →  entrypoint + kind  →  launch
                                                            →  send, receive
                                                            →  observe

   WHY IT IS SHARED, AND WHAT IT DELIBERATELY DOES NOT KNOW. Round 23 built this
   mechanism twice — once in DerivationAuthority, once in film_check's
   FilmAuthority — because the two SEMANTIC boundaries must stay apart
   (film_planes: the calculus film and the derivation relation are different
   transition systems, and merging them lets a session finish the second and
   write that the first is done). Duplicating the semantics was right;
   duplicating the mechanism reproduced P-3 in both. So the fence moves: the
   authorities stay separate and share this, which holds catalog, hashing,
   launching, transport, sessions and the observation table, and holds NO TRVM
   semantics at all. It cannot re-derive a result, replay a film, or say what
   any of it means.

   DECLARED OPEN, unchanged and stated conservatively on purpose: hashing a path
   and then launching that path supports "the host observed artifact X
   immediately before requesting execution of path P". It is not a proof that
   the OS executed those exact bytes under every filesystem race, and it is not
   hardware-attested executable identity. The node binary, its flags and the
   standard library are uncovered for a JS entry; every shared object the loader
   binds is uncovered for a native one.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { basename, isAbsolute, resolve } from "node:path";
import { Worker } from "node:worker_threads";
import { execFile } from "node:child_process";

export const HOST_VERSION = "0.5.0";

/** H over an artifact CLOSURE, length-framed and keyed by BASENAME so the
 *  digest is a property of the bytes rather than of where they were extracted —
 *  the review pack unpacks to an arbitrary directory and must reach the same
 *  identity there. A closure and not one file because an executable that loads
 *  another module is not identified by its own bytes. */
export function digestArtifactFiles(paths) {
  const h = createHash("sha256").update("TRVM-ARTIFACT-CLOSURE-v1");
  for (const p of paths) {
    const bytes = readFileSync(p);
    h.update("|" + basename(p) + "|" + bytes.length + "|");
    h.update(bytes);
  }
  return h.digest("hex");
}

/** Canonical bytes, for keying an execution event. A local copy rather than an
 *  import: this module must not depend on the derivation protocol, because the
 *  film plane uses it too and the whole point of the split is that the host
 *  holds no semantics. The rule is identical and the batteries assert it. */
export function canonicalBytes(v, path = "$", onPath = new Set()) {
  if (v === null) return "null";
  const t = typeof v;
  if (t === "boolean") return v ? "true" : "false";
  if (t === "number") {
    if (!Number.isFinite(v)) throw new Error("not-canonical: non-finite number at " + path);
    return JSON.stringify(v);
  }
  if (t === "string") return JSON.stringify(v);
  if (t === "object") {
    if (onPath.has(v)) throw new Error("not-canonical: cycle at " + path);
    onPath.add(v);
    let out;
    if (Array.isArray(v)) out = "[" + v.map((x, i) => canonicalBytes(x, path + "[" + i + "]", onPath)).join(",") + "]";
    else if (Object.getPrototypeOf(v) === Object.prototype || Object.getPrototypeOf(v) === null)
      out = "{" + Object.keys(v).sort().map((k) => JSON.stringify(k) + ":" +
        canonicalBytes(v[k], path + "." + k, onPath)).join(",") + "}";
    else throw new Error("not-canonical: non-plain object (" + (v.constructor?.name ?? "anonymous") + ") at " + path);
    onPath.delete(v);
    return out;
  }
  throw new Error("not-canonical: " + t + " at " + path);
}

const KINDS = ["node-worker", "native-exec"];

function checkEntry(family, e) {
  if (typeof family !== "string" || !family.startsWith("impl-"))
    return "catalog-family-malformed: " + String(family);
  if (!e || typeof e !== "object") return "catalog-entry-malformed: " + family;
  if (!KINDS.includes(e.kind)) return "catalog-kind-unknown: " + family + " -> " + String(e.kind);
  if (typeof e.entrypoint !== "string" || !isAbsolute(e.entrypoint))
    return "catalog-entrypoint-not-absolute: " + family;
  if (!Array.isArray(e.artifact_closure) || e.artifact_closure.length === 0 ||
      !e.artifact_closure.every((p) => typeof p === "string" && isAbsolute(p)))
    return "catalog-closure-malformed: " + family;
  // THE ENTRYPOINT MUST BE INSIDE THE CLOSURE THAT IS HASHED. A catalog that
  // could hash one set of files and launch a path outside it would be P-3 with
  // the descriptor moved indoors, which is not a repair.
  if (!e.artifact_closure.some((p) => resolve(p) === resolve(e.entrypoint)))
    return "catalog-entrypoint-outside-closure: " + family;
  for (const k of Object.keys(e))
    if (!["kind", "entrypoint", "artifact_closure"].includes(k))
      return "catalog-entry-extra-field: " + family + "." + k;
  return null;
}

/** MULTIPLICITY MUST PRESERVE CORRELATION.
 *
 *  Round 24 discovered that the observation key is over BYTES, so two launches
 *  producing byte-identical output share it — and made `executor_sessions`
 *  plural to stop one id being reported as though it named the launch in hand.
 *  It left `executable_artifact_id` singular over that same plural list, taking
 *  `list[0]`. Those fields are not independent:
 *
 *      run the same issued request
 *      append one comment to derive_worker.mjs
 *      run it again
 *
 *      S1 → artifact 0e34c127… → 5
 *      S2 → artifact d07dc1d9… → 5
 *
 *      reported:  executable_artifact_id 0e34c127…
 *                 executor_sessions      [S1, S2]
 *
 *  Nothing false was accepted — both executions genuinely happened and genuinely
 *  produced these bytes — but the shape implies both sessions ran artifact
 *  0e34c127…, and the evidence says otherwise. One of those artifact versions
 *  could differ arbitrarily and coincide only on this request's result. It is
 *  round 24's own bug surviving in the field round 24 did not make plural.
 *
 *      Evidence fields that vary together may not be independently collapsed
 *      into singular summaries.
 *
 *  So the tuple is the unit. Observations are grouped by the evidence that
 *  actually co-occurred, and every singular field is DERIVED — emitted only
 *  when it is genuinely unique, and null otherwise, which is what the family id
 *  has done since round 24 and what the artifact id should have done with it. */
export function summariseObservations(tuples) {
  const groups = new Map();
  for (const t of tuples) {
    const k = t.implementation_family_id + " " + t.executable_artifact_id;
    const g = groups.get(k) ?? { implementation_family_id: t.implementation_family_id,
      executable_artifact_id: t.executable_artifact_id, executor_sessions: [] };
    for (const s of t.executor_sessions)
      if (!g.executor_sessions.includes(s)) g.executor_sessions.push(s);
    groups.set(k, g);
  }
  const execution_observations = [...groups.values()].map((g) => Object.freeze({
    ...g, executor_sessions: Object.freeze(g.executor_sessions) }));
  const families = [...new Set(execution_observations.map((g) => g.implementation_family_id))];
  const artifacts = [...new Set(execution_observations.map((g) => g.executable_artifact_id))];
  return {
    implementation_family_id: families.length === 1 ? families[0] : null,
    implementation_families: families,
    executable_artifact_id: artifacts.length === 1 ? artifacts[0] : null,
    executable_artifact_ids: artifacts,
    executor_sessions: execution_observations.flatMap((g) => [...g.executor_sessions]),
    // the correlated form, which is the evidence; everything above is a summary
    execution_observations,
  };
}

/** THE HOST. Its catalog is fixed at construction and its observation table has
 *  exactly one writer, which is run(). */
export class ObservedExecutionHost {
  #catalog = new Map();     // family -> { kind, entrypoint, artifact_closure }
  #observed = new Map();    // execution key -> [observation, …]
  #sessions = 0;

  constructor(catalog) {
    if (!catalog || typeof catalog !== "object")
      throw new Error("host-requires-an-executor-catalog");
    // SEVER FIRST, then validate. v0.1.0 validated the caller's object and
    // copied it afterwards — four separate reads of `entrypoint`, three of them
    // validating. A getter answering honestly for those three and maliciously
    // for the fourth put an entrypoint OUTSIDE its own hashed closure into the
    // supposedly immutable internal catalog, and the un-hashed worker really
    // ran while acceptance reported the honest closure's digest (P-6).
    //
    // canonicalBytes is the same rule the message domain has enforced since
    // v0.1.0, and it is doing two jobs here: it refuses a capability outright,
    // and — because the snapshot is taken ONCE — it makes every later read a
    // read of data nobody else holds. A Map is no longer accepted: this is a
    // trust boundary whose whole thesis is that capabilities are not data, and
    // there is no value in admitting richer JS object forms at it.
    if (catalog instanceof Map) throw new Error("host-catalog-must-be-plain-data");
    let owned;
    try { owned = JSON.parse(canonicalBytes(catalog)); }
    catch (e) { throw new Error("host-catalog-not-canonical: " + e.message); }
    const src = Object.entries(owned);
    if (src.length === 0) throw new Error("host-catalog-empty");
    const seen = new Map();
    for (const [family, e] of src) {
      const bad = checkEntry(family, e);
      if (bad) throw new Error(bad);
      const entry = Object.freeze({ kind: e.kind, entrypoint: e.entrypoint,
        artifact_closure: Object.freeze([...e.artifact_closure]) });
      // the family→closure map is injective, so two names cannot mean one
      // executable and one name cannot mean two.
      //   AS AN ESCAPE, not as a literal byte. Until round 27A.1 this separator
      // was a raw NUL in the source, which made file(1) classify the whole
      // module as `data` and made every text tool — grep included — skip it in
      // silence. A grep over this file returned nothing and read like an answer.
      // The string is identical; what changed is that the module is visible to
      // the instruments that audit it.
      const key = entry.artifact_closure.join("\u0000");
      if (seen.has(key)) throw new Error("catalog-closure-aliased: " + family + " and " + seen.get(key));
      seen.set(key, family);
      this.#catalog.set(family, entry);
    }
    Object.freeze(this);
  }

  families() { return [...this.#catalog.keys()].sort(); }
  entryOf(family) { const e = this.#catalog.get(family); return e ? { ...e } : null; }

  /** The identity of an EXECUTION EVENT as a whole: which input went out, and
   *  which bytes came back. Round 17's lesson two levels up. */
  static executionKey(domain, inputCanonical, output) {
    return "xk-" + createHash("sha256")
      .update("TRVM-EXEC-OBSERVED-v2|" + domain + "|" + inputCanonical + "|" + canonicalBytes(output))
      .digest("hex");
  }

  /** THE ONLY THING THAT RUNS ANYTHING.
   *
   *  `invocation` is DATA and is checked to be data — canonicalBytes refuses a
   *  function outright, which is the mechanical reason a caller cannot smuggle
   *  an action in beside the declaration the way P-3 did. What gets launched is
   *  read from the catalog entry, never from the argument.
   *
   *  Order is hash, THEN launch, and it is the conservative reading. */
  async run(family, domain, invocation) {
    const entry = this.#catalog.get(family);
    if (!entry) return { ok: false, reason: "executor-not-in-catalog: " + String(family) };
    // SEVERED ONCE, AND WHAT RUNS IS THE SNAPSHOT. v0.2.1 canonicalised the
    // invocation for the observation key and then handed the SAME live object
    // to the transport, so a caller-owned invocation whose `message` answers
    // honestly on read 1 and hostilely on read 2 was KEYED under one request and
    // EXECUTED as another — and the observation table then held an entry saying
    // the honest bytes produced that output. That is worse than being unable to
    // find a forged observation: it is a true-looking one for an execution that
    // did not happen, in the table round 23 built so that relabelling would move
    // the key. Unreachable through DerivationAuthority.execute, whose invocation
    // is built from owned parts — but the host is exported and FilmAuthority and
    // lowering_check drive it directly, so it is an authority operation in its
    // own right and carries the obligation itself (P-7c).
    let inputCanonical, owned;
    try { inputCanonical = canonicalBytes(invocation); owned = JSON.parse(inputCanonical); }
    catch (e) { return { ok: false, reason: "invocation-not-canonical: " + e.message }; }

    let executable_artifact_id;
    try { executable_artifact_id = digestArtifactFiles(entry.artifact_closure); }
    catch (e) { return { ok: false, reason: "artifact-unreadable: " + e.message }; }

    const executor_session_id = "xs-" + createHash("sha256")
      .update(executable_artifact_id + "|" + inputCanonical + "|" + this.#sessions++).digest("hex");

    let output;
    try {
      output = entry.kind === "node-worker"
        ? await runNodeWorker(entry, owned)
        : await runNativeExec(entry, owned);
    } catch (e) { return { ok: false, reason: "execution-failed: " + String(e.message).split("\n")[0] }; }

    let key;
    try { key = ObservedExecutionHost.executionKey(domain, inputCanonical, output); }
    catch (e) { return { ok: false, reason: "output-not-canonical: " + e.message }; }

    // MULTIPLICITY, because the key is over bytes and two launches producing
    // byte-identical output share it. v0.8.0 overwrote, and then reported one
    // executor_session_id as if it named the launch that produced the copy in
    // hand. It names A recorded session known to have produced these bytes; if
    // there were several, they are all here.
    const list = this.#observed.get(key) ?? [];
    list.push(Object.freeze({ family, executable_artifact_id, executor_session_id,
      kind: entry.kind, entrypoint: basename(entry.entrypoint) }));
    this.#observed.set(key, list);
    // input_canonical is returned so a caller can record WHAT ACTUALLY CROSSED.
    // Without it the only way to ask this table about a past execution is to
    // rebuild the invocation from present state, and present state moves —
    // bindProgram() grows the registry image, the rebuilt invocation stops
    // matching, and a genuine observation vanishes. Historical fact is not a
    // function of current configuration.
    return { ok: true, output, executable_artifact_id, executor_session_id,
      input_canonical: inputCanonical };
  }

  /** Provenance for an input/output pair, or null. Returns a COPY. */
  observationOf(domain, invocation, output) {
    let ic;
    try { ic = canonicalBytes(invocation); } catch { return null; }
    return this.observationOfCanonical(domain, ic, output);
  }

  /** The same question asked with the invocation bytes THE HOST KEYED, for a
   *  caller that recorded them at run() time rather than reconstructing them
   *  from state that has moved since. */
  observationOfCanonical(domain, inputCanonical, output) {
    let key;
    try { key = ObservedExecutionHost.executionKey(domain, inputCanonical, output); }
    catch { return null; }
    const list = this.#observed.get(key);
    if (!list?.length) return null;
    return summariseObservations(list.map((o) => ({
      implementation_family_id: o.family,
      executable_artifact_id: o.executable_artifact_id,
      executor_sessions: [o.executor_session_id],
    })));
  }
}
Object.freeze(ObservedExecutionHost.prototype);
Object.freeze(ObservedExecutionHost);

/* ── the transports. One per catalog `kind`, and both live HERE, because a
      transport a caller could supply is the defect this module exists to
      remove. ───────────────────────────────────────────────────────────────── */

function runNodeWorker(entry, invocation) {
  return new Promise((res, rej) => {
    const w = new Worker(entry.entrypoint, { workerData: invocation.init ?? {} });
    let done = false;
    const finish = (fn, v) => { if (done) return; done = true; w.terminate().then(() => fn(v), () => fn(v)); };
    w.once("error", (e) => finish(rej, e));
    w.once("exit", (c) => { if (!done) finish(rej, new Error("worker exited " + c + " before answering")); });
    w.once("online", () => {
      w.once("message", (m) => finish(res, m));
      try { w.postMessage(invocation.message); } catch (e) { finish(rej, e); }
    });
  });
}

function runNativeExec(entry, invocation) {
  const argv = invocation.argv ?? [];
  if (!Array.isArray(argv) || !argv.every((a) => typeof a === "string"))
    return Promise.reject(new Error("native-argv-not-strings"));
  // stdin is DATA like everything else in the invocation — it went through
  // canonicalBytes before we got here, so it cannot be a stream, a handle, or
  // anything else that would be a capability rather than a value.
  const stdin = invocation.stdin;
  if (stdin !== undefined && typeof stdin !== "string")
    return Promise.reject(new Error("native-stdin-not-a-string"));
  return new Promise((res, rej) => {
    const child = execFile(entry.entrypoint, argv, { maxBuffer: 1 << 26 }, (err, stdout) => {
      // A refusing emitter prints its reason as JSON and exits nonzero. That is
      // a RESULT, not a transport failure, and collapsing the two would let a
      // refusal read as a crash.
      const text = String(stdout ?? "");
      if (err && !text.trim()) return rej(err);
      if (invocation.raw_output === true) return res({ ok: true, stdout: text });
      try { res(JSON.parse(text)); } catch (e) { rej(new Error("native-output-not-json: " + e.message)); }
    });
    if (stdin !== undefined) { child.stdin.end(stdin); }
  });
}
