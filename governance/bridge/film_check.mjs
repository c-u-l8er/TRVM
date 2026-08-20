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
  parse, extrude, findFloatRedexes, semLocusOf, liveDiscoveryOrder, fireFloat, chase,
} from "../trvm_law_kernel.mjs";
import { ObservedExecutionHost, digestArtifactFiles } from "../observed_execution_host.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = process.env.TRVM_GOV_ROOT ?? resolve(HERE, "..");
const BIN = join(HERE, "ic32_film");
/* THE FAMILY ID CARRIES NO RELEASE VERSION, by GPT's B3 ruling. The ontology
   was already three-layered and the name was doing one of the other layers'
   jobs:

       implementation_family_id   which implementation LINEAGE is this?
       executable_artifact_id     which exact BYTES ran?
       executor_session_id        which LAUNCH was this?

   `impl-c-ic32-film-v0.1.0` sat beside a v0.3.0 binary for three releases. If
   every release is meant to change the family, the artifact digest is doing
   that job twice; if it is not, semver in the name is guaranteed to drift and
   nothing checks it. So family identity is STABLE across ordinary artifact
   releases and changes only when the meaning of the family does. Exact bytes
   belong to the digest, which moves on every build. No compensating
   `implementation_version` field either — the digest is the provenance, and a
   human-readable binary version stays descriptive metadata.

   THE FROZEN PROBES KEEP THE OLD STRING. probe_execlaunch_v09_repro.mjs names
   `impl-c-ic32-film-v0.1.0` and must go on naming it: it is a dated record of
   what the catalog said in its era, and rewriting a frozen witness to agree
   with the present would falsify the witness. Only the live catalog moved. */
const C_FAMILY = "impl-c-ic32-film";

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

/* ── V-4: MULTI-FRAME, and it is the fixture the refinement runs on ──────── */
{
  const ADD = "λm.λn.λf.λx.!&0{f0,f1}=f;((m f0) ((n f1) x))";
  const C2 = "λf.λx.!&1{a,b}=f;(a (b x))";
  const C3 = "λf.λx.!&2{a,t}=f;!&3{b,c}=t;(a (b (c x)))";
  const LOWERED = `((${ADD} ${C2}) ${C3})`;
  const m = await auth.emit(LOWERED, C_FAMILY);
  const acc = m.ok ? auth.accept(LOWERED, m.emission) : { ok: false };
  const b = m.ok ? replaySemFilm(LOWERED, m.film, DescFloatRt) : { ok: false };
  const loci = m.ok ? m.film.frames.map((f) => f.locus).join(" ") : "";
  R("multi-frame-native-film",
    m.ok && acc.ok && b.ok && m.film.terminal.steps === 6
      && loci === "t:fun t: t:bod.bod.fun t:bod.bod t:bod.bod.arg.arg.fun t:bod.bod.arg.arg"
      && acc.film_provenance === "observed",
    `the LOWERED add(const 2, const 3) — the term the refinement witness runs on — emits ` +
    `${m.film?.terminal?.steps} chained frames at ${loci}, and the kernel's replaySemFilm accepts the ` +
    `whole chain on both runtime classes. The term CARRIES dup cells and not one dup rule ever fires: ` +
    `the blocker was never their presence, it was firing them, and v0.1.0 refused on the wrong ` +
    `predicate. Provenance ${acc.film_provenance}`);
  R("dup-cells-carried-and-never-fired",
    m.ok && /!&/.test(LOWERED) && m.film.frames.every((f) => f.rule === "APP-LAM"),
    `every frame is APP-LAM even though the source term is full of !&L{…} dups — under the ` +
    `leftmost-tree-app strategy the residual dups are simply dead by the end. This case is kept ` +
    `unchanged now that the dup rules ARE implemented, and it means something different: at v0.2.0 it ` +
    `showed the emitter's LIMIT, and at v0.3.0 it shows a property of the FIXTURE. The same six frames ` +
    `either way, which is the regression half of the round — building the float plane moved nothing on ` +
    `the terms that never needed it`);
}

/* ── V-5: THE DUP/SUP FRONTIER — church_exp_2_2 ──────────────────────────
   Every native film before this one was APP-plane: applications of lambdas at
   tree loci, which a term-rewriting relation models perfectly well. This is the
   first native evidence for the dynamics that make an interaction net one —
   duplication commuting through lambdas and superpositions, projections
   collapsing on free variables and stuck applications, and redexes that live
   INSIDE a floating dup cell rather than anywhere in the tree.

   NOTHING BELOW IS A TRANSCRIBED TABLE. There is no frame count here and no
   locus sequence; the emitter contains neither. What is asserted is derived
   from the film the emitter produced — which rules occur in it, which locus
   families occur in it, which planes occur in it — plus endpoints that come
   from the corpus and were agreed by the 48/48 bridge long before this round.
   The transition claim itself is made by replaySemFilm, which re-derives every
   frame from a fresh runtime and would not care what this file expected. */
const EXP22 = "((λf.λx.!&1001{c0,c1}=f;(c0 (c1 x)) λf.λx.!&1002{c0,c1}=f;(c0 (c1 x))) S)";
const NEW_SURFACES = ["APP-SUP", "DUP-LAM", "DUP-SUP=", "DUP-SUP!", "DUP-VAR", "DUP-APP"];
const e22 = await auth.emit(EXP22, C_FAMILY);
if (!e22.ok) { console.log("FILM-CHECK: FAIL — exp_2_2 emitter refused: " + e22.reason); process.exit(1); }
const FILM22 = e22.film;
const RULES22 = new Set(FILM22.frames.map((f) => f.rule));
const FAMS22 = new Set(FILM22.frames.map((f) => f.locus.slice(0, 2)));
{
  const acc = auth.accept(EXP22, e22.emission, FloatRt);
  const b = replaySemFilm(EXP22, FILM22, DescFloatRt);
  const planes = new Set(FILM22.frames.map((f) => f.plane));
  const declared = new Set(FILM22.terminal.planes);
  const golden = JSON.parse(readFileSync(join(ROOT, "golden_prehash_vectors.json"), "utf8"));
  const gv = golden.per_term.find((t) => t.name === "church_exp_2_2");
  const missing = NEW_SURFACES.filter((r) => !RULES22.has(r));
  R("dup-plane-native-film",
    acc.ok && b.ok && acc.film_provenance === "observed" && missing.length === 0
      && FAMS22.has("t:") && FAMS22.has("d:") && FAMS22.has("v:")
      && planes.has("INTERACT") && planes.has("COLLAPSE")
      && FILM22.terminal.termination === "NORMAL_FORM"
      && FILM22.frames[0].pre === gv.initial.sem_state_id
      && FILM22.terminal.final_sem_id === gv.normal_form.sem_state_id
      && FILM22.terminal.normal_form_id === gv.normal_form.nf_id,
    `ic32 emits ${FILM22.terminal.steps} chained frames for church_exp_2_2 covering ` +
    `${[...RULES22].sort().join(", ")} across locus families ${[...FAMS22].sort().join(" ")} and BOTH ` +
    `semantic planes, and the kernel's own replaySemFilm accepts the whole chain on FloatRt and on ` +
    `DescFloatRt. The endpoints are the corpus vector's own initial state and normal form, which the ` +
    `48/48 bridge already agreed byte-for-byte, so the new claim is exactly the ${FILM22.terminal.steps} ` +
    `TRANSITIONS between them. Provenance ${acc.film_provenance}`);
  R("era-declared-in-pool-and-in-no-frame",
    declared.has("APP-ERA") && declared.has("DUP-ERA")
      && !RULES22.has("APP-ERA") && !RULES22.has("DUP-ERA"),
    `both ERA rules are in the film's DECLARED pool and in none of THIS fixture's frames — and that ` +
    `is now a fact about the fixture rather than a limit of the emitter, since E-1 and E-2 below give ` +
    `each of them a minimal witness of its own. The pool membership stays load-bearing in one ` +
    `direction: a rule left OUT of the pool would make "no enabled work" mean "no work of the kinds I ` +
    `implement", which is how a false normal form gets written down. Keeping this case is the point — ` +
    `coverage by CONSTRUCTION means the big fixture is not asked to carry rules it never fires, and ` +
    `APP-ERA's absence here was not predicted by anyone, only measured`);
}

/* ── the multi-frame forgery kit ──────────────────────────────────────────
   The single-frame `recommit` above cannot express a mid-chain edit: change
   frame 9 and every frame after it needs its `prev` and `frame_id` rebuilt, or
   the forgery dies on bookkeeping before it reaches the calculus. A forger who
   cannot fix up the hashes is not the adversary worth defending against. */
const rechain = (frames, tOver = {}) => {
  let prev = "genesis";
  const out = frames.map((f, i) => {
    const g = { ...f, i, prev };
    g.frame_id = frameId31(prev, g.pre, g.plane, g.rule, g.locus, g.post);
    prev = g.frame_id;
    return g;
  });
  const t = { ...FILM22.terminal, steps: out.length, last_frame: prev, ...tOver };
  return { frames: out, terminal: t, film_id: semFilmIdOf(t) };
};
const mutate = (k, over, tOver = {}) =>
  rechain(FILM22.frames.map((f, i) => (i === k ? { ...f, ...over } : f)), tOver);
const firstFrame = (pred) => FILM22.frames.findIndex(pred);

/* THE LIVE ENUMERATION AT FRAME k, from the kernel's own machinery. Needed for
   the one forgery that is not "name something that is not there" but "name a
   DIFFERENT REDEX THAT REALLY IS THERE" — the only forgery that can tell
   whether the locus identifies THE redex or merely A redex. */
function enabledAt(term, film, k) {
  const frt = new FloatRt();
  let root = extrude(frt, parse(frt, term));
  for (let i = 0; i < k; i++) {
    const rs = findFloatRedexes(frt, root, PLANE_POOL_FREE);
    const order = liveDiscoveryOrder(frt, root);
    const rx = rs.find((r) => String(semLocusOf(r, order)) === film.frames[i].locus);
    root = fireFloat(frt, root, rx).root;
  }
  const order = liveDiscoveryOrder(frt, root);
  return findFloatRedexes(frt, root, PLANE_POOL_FREE)
    .map((r) => ({ locus: String(semLocusOf(r, order)), rule: r.rule }));
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

/* ── D-1 … D-7: THE FORGERIES ON THE NEW SURFACES ────────────────────────
   The F-series above forged the APP-plane frame. These forge the things this
   round added and nothing else could have exercised: a discovery-index locus, a
   redex living inside a dup cell, the six dup/sup rules, the COLLAPSE plane,
   and a terminal on a fixture whose whole historical significance is false
   quiescence. Every index below is FOUND from the film rather than written
   down — `firstFrame(...)`, not `frames[6]`. */
{
  const kd = firstFrame((f) => f.locus.startsWith("d:"));
  const kv = firstFrame((f) => f.locus.startsWith("v:"));
  const kEq = firstFrame((f) => f.rule === "DUP-SUP=");
  const kSup = firstFrame((f) => f.rule === "APP-SUP");
  const kCol = firstFrame((f) => f.plane === "COLLAPSE");
  const n = FILM22.frames.length;

  forge("D-1 d: locus, index moved",
    mutate(kd, { locus: "d:99" }), "sem-locus-not-enabled",
    `frame ${kd + 1} really is ${FILM22.frames[kd].rule} at ${FILM22.frames[kd].locus}, renamed to a ` +
    `discovery index no live cell carries. A d: locus is an INDEX INTO THE LIVE DISCOVERY ORDER, not a ` +
    `heap address, which is exactly what lets the film replay on an allocator that lays the heap out ` +
    `backwards — and it means a wrong index is refused by the enumeration rather than by a lookup`,
    EXP22);

  forge("D-2 v: locus, path moved",
    mutate(kv, { locus: `${FILM22.frames[kv].locus}fun` }), "sem-locus-not-enabled",
    `frame ${kv + 1} is an application redex INSIDE a live dup cell's value — ${FILM22.frames[kv].locus} ` +
    `— with its structural path extended to a position where no application stands. A v: locus is a ` +
    `discovery index AND a path, and both halves have to name the same thing`,
    EXP22);

  forge("D-3 dup rule mismatch",
    mutate(kEq, { rule: "DUP-SUP!" }), "sem-rule-mismatch",
    `a real DUP-SUP= at a real locus, relabelled as its own sibling rule. The two differ only by ` +
    `whether the dup's label EQUALS the superposition's — annihilate versus commute — so this is the ` +
    `closest possible lie about a dup interaction. Replay fires the redex and compares the rule that ` +
    `ACTUALLY fired, so naming a permitted rule that is enabled elsewhere is not enough`,
    EXP22);

  forge("D-4 APP-SUP mismatch",
    mutate(kSup, { rule: "APP-LAM" }), "sem-rule-mismatch",
    `the application of a SUPERPOSITION to an argument, relabelled as the application of a lambda. ` +
    `Both are INTERACT-plane and both are in the declared pool; what separates them is the chased head ` +
    `of the application, which replay recomputes`,
    EXP22);

  forge("D-5 collapse frame claimed as interact",
    mutate(kCol, { plane: "INTERACT" }), "sem-plane-mismatch",
    `${FILM22.frames[kCol].rule} is a COLLAPSE-plane rule (law:plane.rule-partition@1) and this frame ` +
    `says INTERACT. Until this round every native frame was INTERACT and the plane field could not be ` +
    `forged into a lie; a hybrid-plane film is the first one where the partition is checkable — and ` +
    `plane is part of the frame commitment, so the chain is rebuilt around the lie and it still dies`,
    EXP22);

  /* THE HISTORICAL ONE. l_prog_history.round_4_diagnosis names church_exp_2_2
     as the FALSE QUIESCENCE witness that falsified law:sched.free.ast-term@1 —
     the retracted AST relation reached a state it could neither fire nor
     escape and called it done. This is that disease, manufactured against the
     float-plane film and against the SAME fixture: stop one frame early and
     declare a normal form, with the terminal honestly recomputed for the state
     it really stopped in, so nothing bookkeeping-shaped catches it. */
  forge("D-6 terminal false quiescence",
    rechain(FILM22.frames.slice(0, n - 1), { final_sem_id: FILM22.frames[n - 2].post }),
    "sem-false-normal-form",
    `the honest film with its last frame removed and its terminal recomputed for the state it stops ` +
    `in — steps, last_frame and final_sem_id all internally consistent, so every bookkeeping check ` +
    `passes. Replay refuses it because it RE-ENUMERATES the pool at the terminal and finds work. This ` +
    `is the same fixture that falsified the AST scheduling relation at step 15 for exactly this ` +
    `disease, now refused by the contract rather than discovered by an audit`,
    EXP22);

  /* THE STRONGEST ONE, and the only one that distinguishes "the locus names A
     redex" from "the locus names THE redex". Every forgery above names
     something that is not enabled or misdescribes what is; this names a real,
     live, enabled alternative that the emitter did not fire. */
  const cand = FILM22.frames
    .map((f, k) => ({ k, f, alts: enabledAt(EXP22, FILM22, k).filter((e) => e.locus !== f.locus && e.rule === f.rule) }))
    .find((c) => c.alts.length > 0);
  if (!cand) {
    R("D-7 a different enabled redex", false,
      "no frame of this film had a second enabled redex of the same rule, so the strongest locus " +
      "forgery could not be built. That is a fact about the fixture and it must be reported, not " +
      "quietly skipped — a forgery that could not be constructed is not a forgery that was refused");
  } else {
    const r = replaySemFilm(EXP22, mutate(cand.k, { locus: cand.alts[0].locus }), FloatRt);
    R("D-7 a different enabled redex",
      !r.ok && r.reason === "sem-post-mismatch",
      `${r.ok ? "ACCEPTED" : r.reason} — frame ${cand.k + 1} fired ${cand.f.rule} at ${cand.f.locus}; ` +
      `${cand.alts[0].locus} was ALSO live and ALSO ${cand.alts[0].rule} at that moment. Replay finds ` +
      `the named redex, fires it, and lands somewhere else. Every other locus forgery here dies on ` +
      `enabledness; this one gets past enabledness entirely and dies on the post-state, which is what ` +
      `makes a canonical locus an IDENTIFICATION of a redex rather than a description of one`);
  }
}

/* ── E-1 … E-5: THE ERA WITNESSES ────────────────────────────────────────
   The last two rules of the declared pool. TWO PURPOSE-BUILT MINIMAL TERMS,
   not one contrived term that happens to contain both — coverage by
   construction rather than coverage because a large program terminated. The
   conformance corpus contains NO ERA at all, which is exactly why all 24
   vectors could agree while two of nine rules had never run natively, and why
   these had to be built rather than found.

   The measurement came first here too: the kernel was run on each candidate
   before the emitter was asked, and the fixtures were chosen from what it
   showed — `(* x)` is one APP-ERA frame, and `!{a,b} = *; λz.a` is one DUP-ERA
   frame in which only ONE projection is live, which also exercises the
   single-projection path in find_projections. */
const ERA_FIXTURES = [
  { id: "E-1 APP-ERA", term: "(* x)", rule: "APP-ERA",
    why: "an eraser applied to an argument. One frame, no dups, no context — the smallest term in " +
         "which this rule can fire at all" },
  { id: "E-2 DUP-ERA", term: "!{a,b} = *; λz.a", rule: "DUP-ERA",
    why: "a dup cell over an eraser, with only the LEFT projection reachable. One frame, and the " +
         "single-live-projection path through find_projections that the two-projection fixtures never " +
         "take" },
  { id: "E-3 DUP-ERA both projections", term: "!{a,b} = *; (a b)", rule: "DUP-ERA",
    why: "both projections live, so the sibling resolves through the substitution ic32 writes into " +
         "heap[D] rather than through a slot the walk replaced. Fires APP-ERA afterwards, which is a " +
         "consequence of the fixture and not the reason for it" },
];
const ERA_FILMS = {};
for (const f of ERA_FIXTURES) {
  const e = await auth.emit(f.term, C_FAMILY);
  const acc = e.ok ? auth.accept(f.term, e.emission, FloatRt) : { ok: false };
  const b = e.ok ? replaySemFilm(f.term, e.film, DescFloatRt) : { ok: false };
  const rules = new Set(e.ok ? e.film.frames.map((x) => x.rule) : []);
  ERA_FILMS[f.rule] = ERA_FILMS[f.rule] ?? e.film;
  R(f.id,
    e.ok && acc.ok && b.ok && acc.film_provenance === "observed"
      && rules.has(f.rule) && e.film.terminal.termination === "NORMAL_FORM",
    `${e.ok ? `${e.film.terminal.steps} frame(s) — ${e.film.frames.map((x) => `${x.rule}@${x.locus}`).join(" ")} — ` +
      `terminal ${e.film.terminal.termination}, normal form ${JSON.stringify(e.emission.normal_form)}; ` +
      `replayed on FloatRt and DescFloatRt, provenance ${acc.film_provenance}` : `emitter refused: ${e.reason}`}. ${f.why}`);
}
const ALL_WITNESSED = new Set([...RULES22, ...Object.entries(ERA_FILMS)
  .flatMap(([, film]) => film?.frames.map((x) => x.rule) ?? [])]);

/* ── E-4 / E-5: forgeries on the ERA surfaces ────────────────────────────── */
{
  const eraChain = (film, frames, tOver = {}) => {
    let prev = "genesis";
    const out = frames.map((f, i) => {
      const g = { ...f, i, prev };
      g.frame_id = frameId31(prev, g.pre, g.plane, g.rule, g.locus, g.post);
      prev = g.frame_id;
      return g;
    });
    const t = { ...film.terminal, steps: out.length, last_frame: prev, ...tOver };
    return { frames: out, terminal: t, film_id: semFilmIdOf(t) };
  };
  const appEraFilm = ERA_FILMS["APP-ERA"], dupEraFilm = ERA_FILMS["DUP-ERA"];

  forge("E-4 APP-ERA misdescribed",
    eraChain(appEraFilm, appEraFilm.frames.map((f) => ({ ...f, rule: "APP-LAM" }))),
    "sem-rule-mismatch",
    `the eraser application relabelled as a lambda application. Both are INTERACT-plane and both are ` +
    `in the declared pool; what separates them is the chased head, which replay recomputes. Until ` +
    `this round APP-ERA could not be forged because it had never been emitted`,
    ERA_FIXTURES[0].term);

  forge("E-5 DUP-ERA locus moved",
    eraChain(dupEraFilm, dupEraFilm.frames.map((f, i) =>
      (i === 0 ? { ...f, locus: "d:7" } : f))),
    "sem-locus-not-enabled",
    `the dup-over-eraser named at a discovery index no live cell carries. This fixture has exactly ` +
    `ONE live cell, so d:0 is the only index that can name anything — which makes it the cleanest ` +
    `possible demonstration that a d: locus is resolved against the live discovery order rather than ` +
    `accepted as a label`,
    ERA_FIXTURES[1].term);
}

/* ── W-1: THE PRECONDITION WITNESS BEHIND THE ONE-INTERACTION GUARD ──────
   GPT's B3 ruling §(b): KEEP the post-hoc `interactions - before == 1` check —
   it measures what the shipped runtime actually did, including any future
   change inside fire() or whnf(), where a structural pre-check could only
   measure what we predict. But measure the prediction separately instead of
   leaving it as prose in a comment.

   `fire(D,L,k)` opens with `whnf(heap[D])`. The argument that this costs
   nothing is that dup_rule_name has already established BY CHASING that the
   value is one of the admitted head classes, and whnf returns each of those
   without an interaction. This asks the runtime, for every class the ONE
   classifier admits: interaction delta 0, and canonical semantic state
   unchanged.

   THE SECOND CLAUSE IS THE ONE A COUNTER WOULD MISS. whnf memoizes — it writes
   a stuck application's reduced head back into its slot — without counting an
   interaction. That is fine precisely because the canonical state does not
   move, and "fine" is a thing to check rather than assume.

   It does NOT re-classify anything. A second inline recognizer beside
   dup_rule_name would be two semantic recognizers that can drift, which is the
   mechanism-duplication defect this tree has already paid for twice. */
{
  const HEADS = [
    ["DUP-LAM",  "!{a,b} = λx.x; (a b)"],
    ["DUP-SUP=", "!&1{a,b} = &1{λx.x,λy.y}; (a b)"],
    ["DUP-SUP!", "!&1{a,b} = &2{λx.x,λy.y}; (a b)"],
    ["DUP-ERA",  "!{a,b} = *; (a b)"],
    ["DUP-VAR",  "!{a,b} = S; (a b)"],
    ["DUP-APP",  "!{a,b} = (S y); (a b)"],
  ];
  const seen = [], bad = [];
  for (const [want, term] of HEADS) {
    let rows = [];
    try {
      rows = execFileSync(BIN, ["--probe-whnf", term], { maxBuffer: 1 << 26 }).toString()
        .split("\n").filter((l) => l.startsWith("WHNF ")).map((l) => l.split(" "));
    } catch { /* rows stays empty and the class is reported missing */ }
    const row = rows.find((r) => r[1] === want);
    if (!row) { bad.push(`${want}: classifier admitted no such head`); continue; }
    seen.push(want);
    if (row[2] !== "delta=0") bad.push(`${want}: ${row[2]}`);
    if (row[3] !== "state=same") bad.push(`${want}: ${row[3]}`);
  }
  R("W-1 whnf is inert on every admitted dup head",
    bad.length === 0 && seen.length === HEADS.length,
    `${seen.length}/${HEADS.length} admitted head classes measured — ${seen.join(", ")} — each with ` +
    `interaction delta 0 and the canonical semantic state unchanged` +
    `${bad.length ? `; VIOLATIONS: ${bad.join(" · ")}` : ""}. This is the PREDICTION behind the ` +
    `emitter's one-interaction guard, measured rather than argued. The guard itself stays post-hoc ` +
    `and stays the final instrument: it sees what the runtime DID, and a violated precondition ` +
    `becomes a refusal before any frame is committed. That soundness relies on the emitter being ` +
    `FAIL-STOP — the mutated in-process heap never becomes accepted evidence because the process ` +
    `exits. If ic32_film ever becomes a persistent service, this needs transactional scratch state`);
}

/* ── I-1: CANONICAL LOCUS INJECTIVITY, on the kernel's side ──────────────
   GPT's B3 ruling §(c). The emitter refuses `film-locus-alias` on its own
   physical identities; physical identity is not comparable across
   implementations, so this is the same property computed on the kernel's node
   graph. Reported even though it is zero: a diagnostic that only speaks when
   it fires is indistinguishable from one that was never wired in. */
{
  const frt = new FloatRt();
  let root = extrude(frt, parse(frt, EXP22));
  let states = 0, aliases = 0, groups = 0;
  for (const frame of FILM22.frames) {
    const rs = findFloatRedexes(frt, root, PLANE_POOL_FREE);
    const order = liveDiscoveryOrder(frt, root);
    const byId = new Map();
    for (const r of rs) {
      const id = r.kind === "dup" ? `dup:${r.id}` : (() => {
        let t = chase(frt, r.kind === "app" ? root : frt.heap.get(r.id).val);
        for (const k of r.path) t = chase(frt, t[k]);
        return t;
      })();
      if (!byId.has(id)) byId.set(id, new Set());
      byId.get(id).add(String(semLocusOf(r, order)));
    }
    groups += byId.size;
    for (const [, locs] of byId) if (locs.size > 1) aliases++;
    states++;
    root = fireFloat(frt, root, rs.find((r) => String(semLocusOf(r, order)) === frame.locus)).root;
  }
  R("I-1 one redex, at most one canonical locus",
    aliases === 0 && states === FILM22.frames.length,
    `${groups} distinct enabled redexes across ${states} states of church_exp_2_2, and ${aliases} of ` +
    `them carry more than one canonical locus. The representation makes an alias EXPRESSIBLE — each ` +
    `findAppRedexes call carries its own visited set, so a node reachable both from the root and from ` +
    `inside a dup value is enumerated under a t: AND a v: locus — and the locus is committed into ` +
    `frame_id, so two spellings of one transition would be two canonical frame identities for the ` +
    `same pre, rule and post. Nothing in the measured corpus produces one; the emitter refuses ` +
    `film-locus-alias rather than blessing both spellings, because precedence between them is UNRULED`);
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
  const nf = tryEmit("λx.x");
  const budget = (() => {
    try { execFileSync(BIN, ["--budget", "3", EXP22], { maxBuffer: 1 << 26 }); return "ACCEPTED"; }
    catch (e) { try { return JSON.parse(e.stdout.toString()).reason; } catch { return "CRASH"; } }
  })();
  const unhandled = FILM22.terminal.planes.filter((r) => !ALL_WITNESSED.has(r));
  R("scope-is-stated-by-refusal",
    nf === "film-no-redex-at-source" && budget === "film-budget-exhausted" && unhandled.length === 0,
    `an already-normal term -> ${nf}; a 21-frame film under --budget 3 -> ${budget}, NOT a normal ` +
    `form; and of the ${FILM22.terminal.planes.length} declared rules ` +
    `${unhandled.length === 0 ? "every one now has a positive native witness" : `${unhandled.join(" and ")} still have none`}. ` +
    // DERIVED from the union of the fixtures' own films, so this cannot claim
    // coverage a fixture stopped providing. The scope predicate has been wrong
    // twice already: v0.1.0 refused on dup PRESENCE (the lowered add carries
    // dups and fires none) and v0.2.0 on dup ENABLEDNESS, which became a
    // ratchet the moment the dup rules were built.
    `The emitter still says where it stops by REFUSING rather than by emitting a film whose scope a ` +
    `reader has to infer — a rule with no handler is film-rule-not-implemented, and a budget reached ` +
    `while work remains is a typed refusal rather than a fall-through to NORMAL_FORM`);
}

console.log("═".repeat(96));
console.log(fail
  ? `FILM-CHECK: FAIL — ${ran} cases ran, at least one failed`
  : `FILM-CHECK: PASS — ${ran}/${ran}. The native ic32 runtime ORIGINATED semantic-film evidence for ` +
    `the DUP/SUP interaction-net dynamics themselves: church_exp_2_2 emits ${FILM22.terminal.steps} ` +
    `chained frames covering ${[...RULES22].sort().join(", ")} across locus families ` +
    `${[...FAMS22].sort().join(" ")} and both semantic planes, and the law kernel's own replaySemFilm ` +
    `accepted the whole chain on two runtime classes without translation. Every field forged ` +
    `individually is refused — including a locus naming a DIFFERENT LIVE ENABLED REDEX, which gets ` +
    `past enabledness and dies on the post-state — and the film's provenance is an execution the host ` +
    `drove rather than a label anyone may attach. ` +
    // DERIVED from the film's own declared pool minus the rules it fired, so
    // this sentence cannot outlive the gap it describes. Every hand-typed
    // version of a "still open" list in this tree has gone stale in the
    // flattering direction at least once.
    // DERIVED from the UNION of every fixture's own film, so the sentence
    // cannot outlive the gap it describes and cannot claim coverage a fixture
    // stopped providing. Every hand-typed "still open" list in this tree has
    // gone stale in the flattering direction at least once.
    `The two ERA rules now have their own minimal witnesses — ${ERA_FIXTURES.map((f) => f.term).join("  and  ")} — ` +
    `so of the ${FILM22.terminal.planes.length} declared rules ` +
    `${FILM22.terminal.planes.filter((r) => !ALL_WITNESSED.has(r)).length === 0
        ? "EVERY ONE has a positive native witness"
        : `${FILM22.terminal.planes.filter((r) => !ALL_WITNESSED.has(r)).join(" and ")} still have none`}. ` +
    `SCOPE: C→JS only; BUDGET_EXHAUSTED is a typed refusal rather than native film evidence, and a ` +
    `canonical-locus alias is refused rather than resolved.`);
process.exit(fail ? 1 : 0);
