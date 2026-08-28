/* derive_launcher.mjs — v0.9.0 — CATALOG ENTRIES, and no launching at all.

   At v0.8.0 this file exported launchers: objects carrying `artifact_files`
   (which the authority hashed) beside `spawn` (which the authority called).
   Those two fields were mechanically unrelated, so declaring the genuine JS
   worker closure while spawning something else produced provenance "observed"
   for an implementation that never ran. That is P-3, frozen in
   probe_execlaunch_v09_repro.mjs.

       A launch descriptor may not carry both the evidence and an independent
       executable action.

   So nothing here is callable. These are CATALOG ENTRIES — inert data naming a
   kind, an entrypoint and the artifact closure that entrypoint belongs to — and
   ObservedExecutionHost owns the transport for each kind. The host also refuses
   an entry whose entrypoint is not inside its own hashed closure, which is the
   same defect one level in.

   A catalog is fixed at the host's construction, and the host is fixed at the
   authority's. There is no setter anywhere on the path.

   What no JS entry can cover, declared open rather than smoothed over: the node
   binary, its flags, and the standard library. For a native entry the same gap
   is every shared object the loader binds. Hash-then-launch supports "the host
   observed artifact X immediately before requesting execution of path P" and
   nothing stronger. */
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));

/** The JS worker entry. Its closure is worker-plus-protocol because
 *  derive_worker.mjs is not identified by its own bytes — what it does depends
 *  on derive_protocol.mjs too. No program list: the far side's registry image
 *  comes from the AUTHORITY's registry at execute() time, not from whoever
 *  built the catalog. */
export const JS_WORKER_ENTRY = Object.freeze({
  kind: "node-worker",
  entrypoint: join(HERE, "derive_worker.mjs"),
  artifact_closure: Object.freeze([
    join(HERE, "derive_worker.mjs"),
    join(HERE, "derive_protocol.mjs"),
    join(HERE, "observed_execution_host.mjs"),
  ]),
});

/** The catalog the batteries and the production path both use. Keyed by family
 *  name, which is what a request's expected_implementation_id names. */
export function defaultDeriveCatalog(jsFamilyId) {
  return { [jsFamilyId]: JS_WORKER_ENTRY };
}
