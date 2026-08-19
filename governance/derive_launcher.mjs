/* derive_launcher.mjs — v0.8.0 — the host side of an observed execution.

   A LAUNCHER SUPPLIES MECHANISM AND NO IDENTITY. That sentence is the whole
   design, and it is what v0.7.0's `registerExecutor("impl-c-derive-…")` got
   backwards: there, a name was enough to become provenance. Here a launcher
   may say only

       artifact_files   WHICH FILES the authority should hash — paths, not bytes
       spawn()          HOW to start it and speak to it

   and the authority does the rest. It reads those files itself, hashes them
   itself, resolves the family name from its OWN policy, and records the
   observation only after it has sent a request and received a result. A
   launcher that declares itself "impl-c-derive" while pointing at the JS worker
   gets the JS worker's digest, and therefore the JS worker's name.

   `artifact_files` is a CLOSURE and not one file on purpose: derive_worker.mjs
   is not identified by its own bytes, because what it does depends on
   derive_protocol.mjs as well. What no JS launcher can cover, and what is
   declared open rather than smoothed over: the node binary, its flags, and the
   standard library. For a native executable the same gap is every shared object
   the loader will bind. Hash-then-spawn supports "the host observed artifact X
   immediately before requesting execution of path P" and nothing stronger.

   Run: imported. It has no battery of its own; derive_realm_battery.mjs is
   where the launch contract is exercised. */
import { Worker } from "node:worker_threads";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));

/** The JS worker launcher. `programs` is the registry image the far side binds
 *  from data — resolving a program by id is the worker's job and the caller
 *  cannot ship code, so this is a list of canonical ASTs, not callables. */
export function jsWorkerLauncher(programs) {
  const worker_path = join(HERE, "derive_worker.mjs");
  return Object.freeze({
    // The two files whose bytes decide what this executor does. Ordered, and
    // the order is part of the digest.
    artifact_files: Object.freeze([worker_path, join(HERE, "derive_protocol.mjs")]),
    async spawn() {
      const w = new Worker(worker_path, { workerData: { programs } });
      let settled = false;
      await new Promise((res, rej) => {
        w.once("online", () => { settled = true; res(); });
        w.once("error", (e) => { if (!settled) rej(e); });
      });
      return Object.freeze({
        /** ONE request, ONE result. A session that could be fed a second
         *  request while the first was outstanding would let two executions
         *  share one observation, and the observation is per-event. */
        send(req) {
          return new Promise((res, rej) => {
            const onErr = (e) => { w.off("message", onMsg); rej(e); };
            const onMsg = (m) => { w.off("error", onErr); res(m); };
            w.once("error", onErr);
            w.once("message", onMsg);
            try { w.postMessage(req); }
            catch (e) { w.off("message", onMsg); w.off("error", onErr); rej(e); }
          });
        },
        close() { return w.terminate(); },
      });
    },
  });
}

/** A launcher pointing at ARBITRARY files, used by the batteries to show what
 *  the authority does with an artifact it has no name for, and to demonstrate
 *  that declaring a different closure changes the digest. Exported because a
 *  falsifier that has to reach into a module's internals is testing the test. */
export function fileClosureLauncher(files, spawnFn) {
  return Object.freeze({
    artifact_files: Object.freeze([...files]),
    spawn: spawnFn,
  });
}
