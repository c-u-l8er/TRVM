/* ═══════════════════════════════════════════════════════════════════════════
   film_check.mjs — the vertical witness: C originates the evidence.

   For twenty-two rounds the governance plane has been proving that the evidence
   machinery does not lie about computation. Every semantic film in the tree was
   still MADE by the law kernel; the C runtime could say what state it was in
   (48/48 byte-identical signatures since round 12) and could not say that it had
   moved. So the transition evidence was always JavaScript's, and a C runtime
   appeared in the record only as a thing the record described.

   This runs the other way:

       canonical pre-state
              │
              ▼
       the host LAUNCHES the actual ic32 binary   ← hashed before it is spawned
              │
              ▼
       ONE native C rewrite   rule · canonical locus · post-state · terminal
              │
              ▼
       the law kernel's OWN replaySemFilm, on a FRESH runtime
              │
              ▼
       ACCEPT

   `replaySemFilm` is imported unmodified from trvm_law_kernel.mjs. It is the
   same function that judges the kernel's own films, and it re-derives every
   field: it re-parses the source term, recomputes the semantic pre-state,
   enumerates the live redexes and MATCHES the canonical locus against them,
   fires, recomputes the post-state, rebuilds the frame chain, and re-derives
   the terminal including semantic quiescence and the normal form. Nothing in
   the C output is taken on trust and nothing is translated on the way in.

   AND THE PROVENANCE IS THE SAME MECHANISM AS P-2'S. A film that arrives from
   outside is an execution CLAIM exactly as a DeriveResult is, so the same
   discipline applies at the same strength: the authority reads the binary's
   bytes ITSELF and hashes them, resolves the family name from its own policy,
   spawns, sends this term, takes these bytes, and records an observation keyed
   over H(source_term | canonical(the whole film)). F-6 and F-7 below are that
   closure, in the film plane.

   THE TWO TRANSITION SYSTEMS STAY SEPARATE, and this file must not be read as
   merging them (film_planes, round 15 §61). The TRVM CALCULUS film is
   pre-state → (rule + locus) → post-state over the ic32 interaction-net
   relation; the DERIVATION evidence relation is DeriveRequest → evaluate →
   DeriveResult. What is shared here is host infrastructure — hash the artifact,
   launch it, key the observation over the whole event — not semantics.

   Run: node bridge/film_check.mjs   (exit 0 iff every case holds) */
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import {
  replaySemFilm, FloatRt, DescFloatRt, semFilmIdOf, frameId31, PLANE_POOL_FREE,
} from "../trvm_law_kernel.mjs";
import { ObservedExecutionHost, digestArtifactFiles } from "../observed_execution_host.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = process.env.TRVM_GOV_ROOT ?? resolve(HERE, "..");
const BIN = join(HERE, "ic32_film");
const C_FAMILY = "impl-c-ic32-film-v0.1.0";

let fail = false, ran = 0;
const R = (id, ok, note) => { ran++; if (!ok) fail = true;
  console.log(`${ok ? "PASS" : "FAIL"}  ${id.padEnd(30)} ${note}`); };

if (!existsSync(BIN)) {
  console.log(`FILM-CHECK: SKIP — ${BIN} not built (make gov-film builds it).`);
  console.log("  A missing binary is UNBUILT, never green: this exits nonzero so a CI");
  console.log("  that lost its compiler cannot read as a passing native-film claim.");
  process.exit(1);
}

/* ── the film authority. It holds the SEMANTICS and no mechanism. ─────────
   Round 23 built the observing-host machinery twice — once here, once in
   DerivationAuthority — and reproduced P-3 in both: an `artifact_files`
   declaration beside a `run()` the caller supplied, with nothing binding them.
   Supply the real C binary and a run() that returns a previously valid film,
   and provenance came back "observed" with the genuine C digest while no C
   process had run (P-3F).

   Duplicating the SEMANTIC boundary was right and stays: the calculus film and
   the derivation relation are different transition systems (film_planes), and
   merging them lets a session finish the second and write that the first is
   done. Duplicating the MECHANISM was the defect. So the fence moved: this
   class holds what a film MEANS, and ObservedExecutionHost — shared, immutable
   catalog, no TRVM semantics at all — holds hashing, launching and observing. */
const FILM_DOMAIN = "TRVM-FILM-EXEC-v1";

class FilmAuthority {
  #host;
  /** CATALOG DATA, and the host is BUILT. Taking a ready-made host behind an
   *  `instanceof` guard is P-5: a two-method subclass satisfies it while
   *  overriding both run() and observationOf(), so nothing executes and
   *  provenance comes back "observed" anyway. `new` here binds the imported
   *  class, which no caller can substitute. */
  constructor(executorCatalog) {
    this.#host = new ObservedExecutionHost(executorCatalog);
    Object.freeze(this);
  }
  /** No launcher, no run(). The family names a catalog entry and the host owns
   *  both the entrypoint and the transport. */
  async emit(term, family) {
    const r = await this.#host.run(family, FILM_DOMAIN, { argv: [term] });
    if (!r.ok) return { ok: false, reason: r.reason };
    if (!r.output?.ok) return { ok: false, reason: r.output?.reason ?? "emitter-returned-nothing" };
    return { ok: true, emission: r.output, film: r.output.film,
      executor_session_id: r.executor_session_id, executable_artifact_id: r.executable_artifact_id };
  }
  /** ACCEPTANCE TAKES NO PROVENANCE ARGUMENT. Replay first — a film that does
   *  not replay is not evidence whoever produced it — then the observation,
   *  looked up under the whole execution event.
   *
   *  The two verdicts are reported SEPARATELY and on purpose. A film can be
   *  semantically perfect and its claimed provenance false; that is the whole
   *  distinction this project has been building, and collapsing them into one
   *  boolean would lose it. */
  accept(term, emission, RtClass = FloatRt) {
    // PROVENANCE IS OVER EVERYTHING THE EXECUTOR EMITTED, not over a subset a
    // caller chose to present. So acceptance takes the emission and reads the
    // film out of it, rather than taking a film and hoping it came from one.
    const r = replaySemFilm(term, emission?.film, RtClass);
    if (!r.ok) return { ok: false, reason: r.reason, at: r.at };
    const obs = this.#host.observationOf(FILM_DOMAIN, { argv: [term] }, emission);
    return obs
      ? { ok: true, replayed: true, film_provenance: "observed",
          implementation_id: obs.implementation_family_id,
          executable_artifact_id: obs.executable_artifact_id,
          executor_sessions: obs.executor_sessions }
      : { ok: true, replayed: true, film_provenance: "unavailable" };
  }
  observationOf(term, emission) {
    return this.#host.observationOf(FILM_DOMAIN, { argv: [term] }, emission);
  }
}

const FILM_ENTRY = Object.freeze({
  kind: "native-exec",
  entrypoint: BIN,
  artifact_closure: Object.freeze([BIN]),
});
const FILM_CATALOG = Object.freeze({ [C_FAMILY]: FILM_ENTRY });

/* ── the frozen fixture ───────────────────────────────────────────────────
   apply_id, vector 3 of the conformance corpus: ref_interactions = 1, so its
   whole reduction IS one rewrite. Chosen for exactly that reason — its
   pre-state is the corpus vector's `initial` and its post-state is the corpus
   vector's `normal_form`, and the bridge gate has already proved C and JS agree
   on both, byte for byte. So the only thing this round adds to the record is
   the TRANSITION between two states whose canonicalization was never in doubt. */
const TERM = "(λx.λt.(t x) λy.y)";
const BIN_DIGEST = digestArtifactFiles([BIN]);

const auth = new FilmAuthority(FILM_CATALOG);
const emitted = await auth.emit(TERM, C_FAMILY);
if (!emitted.ok) { console.log("FILM-CHECK: FAIL — emitter refused: " + emitted.reason); process.exit(1); }
const EMISSION = emitted.emission;
const FILM = EMISSION.film;
const reEmit = (film) => ({ ...EMISSION, film });
const F0 = FILM.frames[0];

/* ── V-1: THE VERTICAL WITNESS ───────────────────────────────────────────── */
{
  const a = auth.accept(TERM, EMISSION, FloatRt);
  R("native-frame-accepted",
    a.ok && a.film_provenance === "observed" && a.implementation_id === C_FAMILY
      && a.executable_artifact_id === BIN_DIGEST,
    `ic32 parsed ${JSON.stringify(TERM)}, found ONE enabled redex, fired ${F0.rule} at canonical locus ` +
    `"${F0.locus}", reached ${F0.post.slice(0, 12)}… and verified quiescence — and the law kernel's own ` +
    `replaySemFilm accepts the frame unmodified. Provenance ${a.film_provenance}: family ` +
    `${a.implementation_id}, artifact ${a.executable_artifact_id.slice(0, 12)}…`);
}

/* ── V-2: and on a runtime of a DIFFERENT class ──────────────────────────── */
{
  const b = replaySemFilm(TERM, FILM, DescFloatRt);
  R("replays-across-allocators", b.ok === true,
    `the same native film replays on DescFloatRt — a deliberately adversarial allocator discipline — ` +
    `which is what "semantic" in semantic film is for: the locus is a canonical path and a discovery ` +
    `index, so it names the same redex on a heap laid out differently`);
}

/* ── V-3: the frame's endpoints are the corpus's own, independently agreed ── */
{
  const golden = JSON.parse(readFileSync(join(ROOT, "golden_prehash_vectors.json"), "utf8"));
  const v = golden.per_term.find((t) => t.name === "apply_id");
  R("endpoints-are-the-bridge's",
    v && F0.pre === v.initial.sem_state_id && F0.post === v.normal_form.sem_state_id
      && FILM.terminal.normal_form_id === v.normal_form.nf_id && v.steps === 1,
    `pre === the corpus vector's initial state and post === its normal form, both of which the 48/48 ` +
    `bridge gate has already shown C and JS agree on byte-for-byte. The new claim is therefore exactly ` +
    `the TRANSITION between them, and nothing is smuggled in through the endpoints`);
}

/* ── the forgeries. Each is RE-COMMITTED — frame_id and film_id recomputed —
      so it dies on a semantic check rather than on a bookkeeping hash. A
      forger who cannot also fix up the hashes is not the adversary worth
      defending against. ───────────────────────────────────────────────────── */
const recommit = (frame, over = {}) => {
  const f = { ...F0, ...frame };
  f.frame_id = frameId31(f.prev, f.pre, f.plane, f.rule, f.locus, f.post);
  const t = { ...FILM.terminal, last_frame: f.frame_id, ...over };
  return { frames: [f], terminal: t, film_id: semFilmIdOf(t) };
};
const forge = (id, film, want, note, term = TERM) => {
  const r = replaySemFilm(term, film, FloatRt);
  R(id, !r.ok && r.reason === want, `${r.ok ? "ACCEPTED" : r.reason} — ${note}`);
};

forge("F-1 wrong pre-state",
  recommit({ pre: "0".repeat(64) }), "sem-revision-mismatch",
  `a frame whose declared pre-state is not the state replay is in. Replay recomputes the semantic id ` +
  `of the freshly extruded source rather than reading the frame's word for it`);

forge("F-2 wrong post-state",
  recommit({ post: "1".repeat(64) }, { final_sem_id: "1".repeat(64) }), "sem-post-mismatch",
  `the rule really fires at the stated locus and the frame lies about where it lands. Replay fires the ` +
  `redex itself and compares its OWN post-state`);

forge("F-3 real rule at wrong locus",
  recommit({ locus: "t:arg" }), "sem-locus-not-enabled",
  `APP-LAM named at t:arg, where the term is λy.y and no application stands. Enabledness is inherent: ` +
  `the locus must MATCH one of the live enumeration's redexes, so an unmatched locus refuses without ` +
  `any separate "is it enabled" flag to forge`);

forge("F-4 rule not enabled at locus",
  recommit({ rule: "DUP-SUP=" }), "sem-rule-mismatch",
  `a real redex at a real locus, misdescribed as a dup rule. The redex is found, fired, and the rule ` +
  `that actually fired is compared against the claim — so naming a permitted rule is not enough`);

forge("F-5 transition from another state",
  FILM, "sem-revision-mismatch",
  `the HONEST film, replayed against a different source term. A film commits its own pre-state, so it ` +
  `is evidence about one state and cannot be re-attached to another`,
  "(λx.x Q)");

/* the un-recommitted variants: the chain still catches the lazy forger */
{
  const lazy = { frames: [{ ...F0, post: "2".repeat(64) }], terminal: FILM.terminal, film_id: FILM.film_id };
  const r = replaySemFilm(TERM, lazy, FloatRt);
  const lazyTerm = { frames: FILM.frames, terminal: { ...FILM.terminal, steps: 2 }, film_id: FILM.film_id };
  const r2 = replaySemFilm(TERM, lazyTerm, FloatRt);
  R("chain-catches-the-lazy-forger",
    !r.ok && r.reason === "sem-post-mismatch" && !r2.ok && r2.reason === "sem-terminal-steps-mismatch",
    `editing a field without recomputing the commitments dies too (${r.reason}, ${r2.reason}) — the ` +
    `re-committed forgeries above are the interesting ones because they get past the bookkeeping and ` +
    `still fail on the calculus`);
}

/* ── F-6 / F-7 / P-3F: THE PROVENANCE FORGERIES ──────────────────────────── */
{
  // F-6: a genuine C film paired with an observation of something else. There
  // is nothing to pair: the observation is keyed over the whole event.
  const other = new FilmAuthority(FILM_CATALOG);
  const otherRun = await other.emit("(λx.x Q)", C_FAMILY);
  const borrowed = other.accept(TERM, EMISSION);
  R("F-6 observation-cannot-be-repointed",
    otherRun.ok && borrowed.ok && borrowed.film_provenance === "unavailable"
      && !("implementation_id" in borrowed) && other.observationOf(TERM, EMISSION) === null,
    `an authority holding a REAL C observation for another term reports ${borrowed.film_provenance} for ` +
    `this film, with no implementation_id. Under a handle-shaped design ("this executor exists, and here ` +
    `it is") the two would have been interchangeable — which is P-2, in the film plane`);

  // F-7a: a replay-preserving mutation. NOT "JS relabelled as C" — there is no
  // JS film emitter, and manufacturing an implementation solely to manufacture
  // an adversary would be building the wrong thing. What this proves is
  // narrower and worth having: provenance is over the observed film BYTES,
  // including fields replay deliberately treats as non-authoritative.
  const jsAuth = new FilmAuthority(FILM_CATALOG);
  const run = await jsAuth.emit(TERM, C_FAMILY);
  const edited = { ...run.film, terminal: { ...run.film.terminal, planes: [...run.film.terminal.planes] } };
  edited.frames = [{ ...run.film.frames[0], i: 1 }];   // one non-authoritative field
  const acc = jsAuth.accept(TERM, { ...run.emission, film: edited });
  R("F-7a replay-preserving mutation",
    acc.ok && acc.replayed === true && acc.film_provenance === "unavailable"
      && jsAuth.observationOf(TERM, run.emission) !== null,
    `changing the frame's DECLARED-NON-AUTHORITATIVE index i drops provenance to ` +
    `${acc.film_provenance} while the film still REPLAYS (replayed ${acc.replayed}) and the untouched ` +
    `film keeps its observation. Replay and provenance are different verdicts, and the second is over ` +
    `the bytes as they were observed`);

  // P-3F: the film-plane half of P-3. Declare the REAL C binary — genuine
  // digest, genuine family — and supply a run() that returns a film C did not
  // produce this time. Under v0.8.0 this returned film_provenance "observed"
  // with the real C artifact id and no C process having run.
  let ranC = false;
  const smuggled = {
    artifact_files: [BIN],
    run() { ranC = true; return JSON.stringify(EMISSION); },
  };
  const p3f = new FilmAuthority(FILM_CATALOG);
  // there is no argument that accepts it. The catalog names the entrypoint and
  // the host owns the transport, so the closest a caller can get is a family
  // name — and a name is not an action.
  const viaExtraArg = await p3f.emit(TERM, C_FAMILY, smuggled);
  const uncatalogued = await p3f.emit(TERM, "impl-c-smuggled-v0.1.0");
  const accP3F = viaExtraArg.ok ? p3f.accept(TERM, viaExtraArg.emission) : { ok: false };
  R("P-3F no-run-function-to-supply",
    !ranC && viaExtraArg.ok && accP3F.film_provenance === "observed"
      && accP3F.executable_artifact_id === BIN_DIGEST
      && !uncatalogued.ok && /^executor-not-in-catalog: /.test(uncatalogued.reason)
      && FilmAuthority.prototype.emit.length === 2,
    `a third argument carrying artifact_files beside a run() is inert: the callback never fired ` +
    `(${ranC}), the real binary did, and the observation carries ITS digest. emit takes ` +
    `${FilmAuthority.prototype.emit.length} parameters (term, family), and a family the catalog does ` +
    `not hold is ${uncatalogued.reason.split(":")[0]} — a name is not an action. At v0.8.0 this same ` +
    `object WAS the API and returned film_provenance "observed" for a C binary that never ran`);

  // and a host whose catalog does not name this binary cannot run it
  const wrongCat = await new FilmAuthority({ "impl-x-v1": { kind: "native-exec",
    entrypoint: join(HERE, "ic32_canon"), artifact_closure: [join(HERE, "ic32_canon")] } })
    .emit(TERM, C_FAMILY);
  R("uncatalogued-emitter-refused", !wrongCat.ok && /^executor-not-in-catalog: /.test(wrongCat.reason),
    `${wrongCat.reason} — hash first, launch second, and BOTH from the same catalog entry. The ` +
    `strongest honest reading of that order is "the host observed artifact X immediately before ` +
    `requesting execution of path P"; it is NOT a proof that the OS executed those bytes, and it is ` +
    `not attestation. Declared open`);
}

/* ── the emitter's own preconditions are refusals, not silence ───────────── */
{
  const tryEmit = (t) => { try { execFileSync(BIN, [t], { maxBuffer: 1 << 26 }); return "ACCEPTED"; }
    catch (e) { try { return JSON.parse(e.stdout.toString()).reason; } catch { return "CRASH"; } } };
  const dup = tryEmit("!{a,b} = {λx.x,λy.y}; (a b)");
  const nf = tryEmit("λx.x");
  const many = tryEmit("((λx.x A) (λy.y B))");
  R("emitter-refuses-out-of-scope",
    dup === "film-dup-cell-present" && nf === "film-no-redex-at-source"
      && many === "film-source-redex-ambiguous",
    `a dup-carrying term -> ${dup}; an already-normal term -> ${nf}; a term with two enabled redexes -> ` +
    `${many}. v0.1.0 handles the dup-free one-step fragment and says so by refusing, rather than by ` +
    `emitting a frame whose scope a reader has to infer`);
}

console.log("═".repeat(96));
console.log(fail
  ? `FILM-CHECK: FAIL — ${ran} cases ran, at least one failed`
  : `FILM-CHECK: PASS — ${ran}/${ran}. The native ic32 runtime ORIGINATED a semantic-film frame ` +
    `(${F0.rule} at "${F0.locus}", ${F0.pre.slice(0, 8)}… → ${F0.post.slice(0, 8)}…) and the law ` +
    `kernel's own replaySemFilm accepted it on two runtime classes without translation. Every field ` +
    `forged individually is refused, and the film's provenance is an execution the host drove rather ` +
    `than a label anyone may attach. SCOPE: one frame, the dup-free fragment, C→JS only.`);
process.exit(fail ? 1 : 0);
