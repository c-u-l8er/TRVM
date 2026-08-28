/* ═══════════════════════════════════════════════════════════════════════════
   holdout_score.mjs — v0.6.0 — THE MUTABLE SIDE SUPPLIES A PATH, AND NOTHING ELSE
   law:proof.measurement-authority-frozen@1 · law:proof.authority-bound-to-its-world@1

   v0.4.0 said it held the secret and delegated everything else. IT DID NOT. It
   also supplied, from outside every digest:

       --status <string>     the fact the frozen reveal gate gates on
       --adapters  <file>    the subject list
       --challenges <file>   the assembled secret
       and, via `blind_run.mjs --complete`, THE SUMMARY THE RESULT RECEIPT
       BELIEVES

   REPRODUCED, both halves. Change `run.status` to the literal "REVEALED" in this
   file and a CANDIDATE_FROZEN fake received H1…H10 with `--reveal` never called.
   Replace this file with a nine-line program that writes `{harness_ok: true,
   25/25, interop agreed}` and a candidate whose entire body is `exit 99` reached
   COMPLETE and got a RESULT receipt saying so. Both left SPEC-RELEASE and
   BLIND-RUN green, because neither reads this file and no digest contains it.

   THE RULE: no unfrozen program may decide whether secret bytes are released, or
   whether the experiment completed successfully. What is left here is the one
   thing that genuinely cannot be frozen — WHERE THE SECRET IS — and even that is
   not trusted: the frozen instrument re-digests whatever directory it is handed
   and requires it to equal the `holdout_commitment` inside the release. A
   wrapper that lied about the path would fail HOLDOUT-COMMITMENT.

   AND v0.5.0 STILL SUPPLIED TWO FACTS, NOT ONE. It forwarded `--state-root`,
   which is not "where the secret is" — it is *which authority universe decides
   whether to release it*. REPRODUCED: a candidate frozen in the canonical run
   and never revealed received H1…H10 because a REVEALED copy of the record sat
   in /tmp and this file passed the flag through. The flag is gone from every
   program; a dry run gets its own whole WORLD, and runs that world's copy of the
   instrument. This file now takes no arguments at all, which is what makes its
   own claim literally true.

   `grid_check` asserts that this file reads no run record, names no status and
   assembles no challenges — a delegation that could be quietly un-delegated is
   not a delegation, and the last three rounds are what that sentence cost.
   ═══════════════════════════════════════════════════════════════════════════ */
import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = join(HERE, "..");
const RUNNER = join(REPO, "docs", "spec", "proof-wire", "experiment", "holdout_runner.mjs");
/** THE SECRET. The only fact this file contributes, and it is self-authenticating
 *  at the far end. */
const HOLDOUT = join(HERE, "holdout");

const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN) {
  if (!existsSync(RUNNER)) {
    console.log(`HOLDOUT-SCORE: FAIL — the frozen instrument is not at ${RUNNER}. An instrument ` +
      `outside the experiment surface is an instrument outside experiment_digest.`);
    process.exit(1);
  }
  const extra = process.argv.slice(2).filter((a) => a.startsWith("--"));
  if (extra.length) {
    console.log(`HOLDOUT-SCORE: REFUSED — this gate takes NO arguments, and was given ` +
      `[${extra.join(", ")}]. v0.5.0 forwarded --state-root, which is not "where the secret is" ` +
      `but which authority decides whether to release it, and a REVEALED copy of the record in ` +
      `/tmp then handed the canonical candidate all ten hidden constructions. Ignoring a retired ` +
      `flag silently would let a caller believe it had selected something.`);
    process.exit(2);
  }
  /* ONE ARGUMENT TO THE INSTRUMENT, AND IT NAMES THE SECRET. Not the repository, not the state
     root: those are the world, and the world is wherever the instrument being
     run lives. */
  const p = spawnSync(process.execPath, [RUNNER, "--holdout", HOLDOUT], { encoding: "utf8" });
  process.stdout.write(p.stdout ?? "");
  if (p.stderr?.trim()) process.stderr.write(p.stderr);
  console.log(p.status === 0
    ? `HOLDOUT-SCORE: PASS — this file named a directory and the FROZEN instrument did everything ` +
      `else: it recomputed the commitment over that directory, read the run record and its receipt ` +
      `chain itself, derived the status from what the chain WITNESSES rather than from anything ` +
      `said here, verified that every subject resolves INSIDE this world, and measured. Against ` +
      `P4.7.1 this file passed the status word the reveal gate gates on; against P4.7.2 it ` +
      `forwarded --state-root, which is not where the secret is but which authority decides to ` +
      `release it, and a REVEALED copy in /tmp handed the canonical candidate all ten hidden ` +
      `constructions while the canonical run was never revealed`
    : `HOLDOUT-SCORE: FAIL — the frozen instrument refused, or found a disagreement`);
  process.exit(p.status === 0 ? 0 : 1);
}
