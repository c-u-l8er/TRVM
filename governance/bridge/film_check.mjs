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
import { digestArtifactFiles } from "../derive_protocol.mjs";

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

/* ── the host side, and it supplies MECHANISM AND NO IDENTITY ─────────────
   The same shape as derive_launcher.mjs: WHERE the bytes are, and HOW to run
   them. It does not get a field in which to say what it is. */
const ic32FilmLauncher = Object.freeze({
  artifact_files: Object.freeze([BIN]),
  run(term) { return execFileSync(BIN, [term], { maxBuffer: 1 << 26 }).toString(); },
});

/* ── the film authority. Its observation table has exactly one writer. ───── */
const canon = (v) => {
  if (v === null) return "null";
  if (Array.isArray(v)) return "[" + v.map(canon).join(",") + "]";
  if (typeof v === "object") return "{" + Object.keys(v).sort()
    .map((k) => JSON.stringify(k) + ":" + canon(v[k])).join(",") + "}";
  return JSON.stringify(v);
};
const filmExecutionKey = (term, film) =>
  "fk-" + createHash("sha256").update("TRVM-FILM-OBSERVED-v1|" + term + "|" + canon(film)).digest("hex");

class FilmAuthority {
  #observed = new Map();
  #names = new Map();
  #sessions = 0;
  nameArtifact(digest, family) {
    if (!/^[0-9a-f]{64}$/.test(digest)) throw new Error("artifact-digest-malformed");
    const bound = this.#names.get(digest);
    if (bound !== undefined && bound !== family) throw new Error("artifact-already-named");
    this.#names.set(digest, family);
    return { ok: true };
  }
  /** THE AUTHORITY runs the emitter: hash first, spawn second. */
  emit(term, launcher) {
    let executable_artifact_id;
    try { executable_artifact_id = digestArtifactFiles(launcher.artifact_files); }
    catch (e) { return { ok: false, reason: "artifact-unreadable: " + e.message }; }
    const implementation_family_id = this.#names.get(executable_artifact_id);
    if (implementation_family_id === undefined)
      return { ok: false, reason: "artifact-unnamed: " + executable_artifact_id.slice(0, 12) + "…" };
    const executor_session_id = "fs-" + createHash("sha256")
      .update(executable_artifact_id + "|" + term + "|" + this.#sessions++).digest("hex").slice(0, 24);
    let out;
    try { out = JSON.parse(launcher.run(term)); }
    catch (e) { return { ok: false, reason: "emitter-failed: " + String(e.message).split("\n")[0] }; }
    if (!out.ok) return { ok: false, reason: out.reason };
    this.#observed.set(filmExecutionKey(term, out.film), Object.freeze({
      implementation_family_id, executable_artifact_id, executor_session_id }));
    return { ok: true, ...out, executor_session_id };
  }
  /** ACCEPTANCE TAKES NO PROVENANCE ARGUMENT. Replay first — a film that does
   *  not replay is not evidence whoever produced it — then the observation,
   *  looked up under the whole execution event. */
  accept(term, film, RtClass = FloatRt) {
    const r = replaySemFilm(term, film, RtClass);
    if (!r.ok) return { ok: false, reason: r.reason, at: r.at };
    const obs = this.#observed.get(filmExecutionKey(term, film));
    return obs
      ? { ok: true, replayed: true, film_provenance: "observed",
          implementation_id: obs.implementation_family_id,
          executable_artifact_id: obs.executable_artifact_id,
          executor_session_id: obs.executor_session_id }
      : { ok: true, replayed: true, film_provenance: "unavailable" };
  }
  observationOf(term, film) { const o = this.#observed.get(filmExecutionKey(term, film)); return o ? { ...o } : null; }
}

/* ── the frozen fixture ───────────────────────────────────────────────────
   apply_id, vector 3 of the conformance corpus: ref_interactions = 1, so its
   whole reduction IS one rewrite. Chosen for exactly that reason — its
   pre-state is the corpus vector's `initial` and its post-state is the corpus
   vector's `normal_form`, and the bridge gate has already proved C and JS agree
   on both, byte for byte. So the only thing this round adds to the record is
   the TRANSITION between two states whose canonicalization was never in doubt. */
const TERM = "(λx.λt.(t x) λy.y)";
const BIN_DIGEST = digestArtifactFiles([BIN]);

const auth = new FilmAuthority();
auth.nameArtifact(BIN_DIGEST, C_FAMILY);
const emitted = auth.emit(TERM, ic32FilmLauncher);
if (!emitted.ok) { console.log("FILM-CHECK: FAIL — emitter refused: " + emitted.reason); process.exit(1); }
const FILM = emitted.film;
const F0 = FILM.frames[0];

/* ── V-1: THE VERTICAL WITNESS ───────────────────────────────────────────── */
{
  const a = auth.accept(TERM, FILM, FloatRt);
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

/* ── F-6 / F-7: THE PROVENANCE FORGERIES ─────────────────────────────────── */
{
  // F-6: a genuine C film paired with an observation of something else. There
  // is nothing to pair: the observation is keyed over the whole event.
  const other = new FilmAuthority();
  other.nameArtifact(BIN_DIGEST, C_FAMILY);
  const otherRun = other.emit("(λx.x Q)", ic32FilmLauncher);
  const borrowed = other.accept(TERM, FILM);
  R("F-6 observation-cannot-be-repointed",
    otherRun.ok && borrowed.ok && borrowed.film_provenance === "unavailable"
      && !("implementation_id" in borrowed) && other.observationOf(TERM, FILM) === null,
    `an authority holding a REAL C observation for another term reports ${borrowed.film_provenance} for ` +
    `this film, with no implementation_id. Under a handle-shaped design ("this executor exists, and here ` +
    `it is") the two would have been interchangeable — which is P-2, in the film plane`);

  // F-7: relabel. The film is C's, byte for byte, and one field is edited.
  const jsAuth = new FilmAuthority();
  jsAuth.nameArtifact(BIN_DIGEST, C_FAMILY);
  const run = jsAuth.emit(TERM, ic32FilmLauncher);
  const edited = { ...run.film, terminal: { ...run.film.terminal, planes: [...run.film.terminal.planes] } };
  edited.frames = [{ ...run.film.frames[0], i: 1 }];   // one non-authoritative field
  const acc = jsAuth.accept(TERM, edited);
  R("F-7 relabel-loses-the-observation",
    acc.ok && acc.film_provenance === "unavailable" && jsAuth.observationOf(TERM, run.film) !== null,
    `changing even the frame's DECLARED-NON-AUTHORITATIVE index i drops provenance to ` +
    `${acc.film_provenance}, while the untouched film keeps its observation. The film still REPLAYS — ` +
    `i is metadata replay counts for itself — and that is the point: replay and provenance are ` +
    `different verdicts, and the second is over the bytes as they were observed`);

  // and an artifact the authority has no name for does not run at all
  const unnamed = new FilmAuthority();
  const x = unnamed.emit(TERM, ic32FilmLauncher);
  R("unnamed-emitter-refused", !x.ok && /^artifact-unnamed: /.test(x.reason),
    `${x.reason} — hash first, spawn second. The strongest honest reading of that order is "the host ` +
    `observed artifact X immediately before requesting execution of path P"; it is NOT a proof that the ` +
    `OS executed those bytes, and it is not attestation. Declared open`);
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
