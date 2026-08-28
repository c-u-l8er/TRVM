/* ═══════════════════════════════════════════════════════════════════════════
   spec_release.mjs — v0.3.0 — THE RELEASE MUST NAME ITSELF
   law:proof.spec-release-bound@1 · law:proof.release-manifest-owned@1
   law:proof.release-identity-binds-all-commitments@1
   law:proof.release-id-canonically-encoded@1 · law:proof.release-archive-immutable@1

   P4.6 (A). THE IDENTITY FORMULA DID NOT BIND WHAT THE INVARIANT SAID IT BOUND.
   v0.2.0 computed the preimage with

       JSON.stringify(core, Object.keys(core).sort())

   and a JSON.stringify replacer ARRAY is an allowlist applied RECURSIVELY. The
   allowlist held the fourteen top-level core keys and none of `wire`,
   `verified_claim`, `nested_composition` — so the nested protocol map serialised
   as

       "protocols":{}

   Reproduced: take the honest release, set all three protocol identifiers to
   EVIL-A / EVIL-B / EVIL-C, recompute — the preimage is BYTE-IDENTICAL and the
   id stays srel-3ac8f6fc…. NOT a passing forgery, because the protocol names are
   separately CHECKED against the normative schema below; the defect is that the
   ID FORMULA ITSELF binds fourteen fields while the invariant grid claims it
   binds fifteen, and that P4.1–P4.3 spent three passes eliminating exactly this
   class — a canonicalisation that only a JavaScript host reproduces — before
   this file reinvented one. A second runtime cannot recompute `srel` without
   knowing a `JSON.stringify` quirk.

   The preimage is `canonicalWire(core)` now: the SAME RFC 8785 encoder the wire
   protocol uses, gated against six upstream vectors as octets by
   `jcs_vectors.mjs`. That is not circular — the encoder's conformance is
   established against published data, not against this file.

   AND THE REPAIR IS AUDITED MECHANICALLY, BOTH HALVES. Every leaf of the release
   core is perturbed one at a time and MUST move the identity; every field
   outside the core is perturbed and MUST NOT. A one-way sweep would have passed
   over `protocols` in v0.2.0 as happily as the invariant did.

   P4.6 (B). AND THE GRID CLAIMED AN ARCHIVE THAT DID NOT EXIST. Its evidence
   said `releases/<spec_release_id>.json written on issuance` and `releases are
   immutable objects`; `--update` wrote SPEC-RELEASE.json and nothing else, there
   was no `releases/` directory, and reissuing after a procedural edit left NO
   copy of the previous release anywhere. The claim was aspirational in the file
   whose subject is claims matching executable evidence. Issuance writes the
   archive under the identity, REFUSES to overwrite differing bytes, and every
   verification run requires SPEC-RELEASE.json to byte-match its own archived
   copy — which also makes the NON_AUTHORITATIVE fields immutable per identity,
   though they are outside it.

   P4.3 froze the corpus and left the PROSE unbound. There are three normative
   surfaces — the Markdown documents, the machine-readable schema, and the
   vector corpus — and nothing tied them together. Reproduced: change the
   normative formula in `TRVM-VERIFIED-CLAIM-v1.md` from

       "TRVM-VERIFIED-CLAIM-v1|"   to   "TRVM-VERIFIED-CLAIM-EVIL|"

   touching no JavaScript, no schema and no vector, and both gates still pass:

       SPEC-AGREEMENT: PASS          it compares the checker with the SCHEMA
       SPEC-VECTORS:   PASS          it compares the checker with the CORPUS

   `spec_vectors`'s tree digest proved only that verification did not WRITE
   during the run. It never proved that the tree being verified was the tree the
   corpus was issued against. So a normative sentence could be edited before a
   run and nothing would notice — which matters most for the one document a
   blind implementer reads and no gate executes.


   AND v0.1.0's RELEASE RECORD WAS CLAIMANT-OWNED. It checked four digests and
   let the record say what those digests MEANT. Reproduced by editing only
   `SPEC-RELEASE.json`, leaving every component digest honest:

       release_type   -> TRVM-EVIL-RELEASE-v999
       protocols.*    -> …-EVIL
       revisions      -> 999
       jcs vectors    -> 999
       holdout_entries-> 0
       note           -> "THIS RELEASE PROVES EVERYTHING"

       SPEC-RELEASE: PASS

   and it PRINTED the forged revision, the forged vector count and the forged
   holdout count while congratulating itself. That is B6.3 — *a field is not
   evidence merely because it sits beside one that is* — arriving in the release
   layer. Every field is now DERIVED, CHECKED, DECLARED_AND_BOUND or
   NON_AUTHORITATIVE, audited mechanically, with no fifth category.

   AND THE RELEASE HAD NO IDENTITY OF ITS OWN. Four digests sat side by side
   with nothing over them, so changing one hidden holdout file and reissuing at
   the same revision numbers produced a second, different experiment still
   advertised as "spec revision 1 (a11e066a…)". `spec_release_id` binds every
   committed component — protocols, both revision labels, the spec digest, the
   corpus digest, the pinned JCS source and digest, the experiment digest and
   the holdout commitment — and it is what a conformance report cites.

   AND PROCEDURE IS NOT PROTOCOL. `BLIND-IMPLEMENTATION-CONTRACT.md` says of
   itself *PROCEDURAL, not normative*, and v0.1.0 hashed it into `spec_digest`
   and called it one of five normative files — so editing how the experiment is
   RUN reported that the wire protocol had changed. It has its own revision and
   digest now, and `spec_release_id` binds both.

   SO A RELEASE IS AN OBJECT. `SPEC-RELEASE.json` binds, by digest, every
   normative document, the schema, the public corpus, the pinned upstream JCS
   provenance, and the COMMITMENT to a hidden holdout set. The file set and the
   ordering are defined here and the release object EXCLUDES ITSELF from its own
   preimage, because a digest over a file containing that digest has no
   fixpoint.

   AND REVISION NUMBERS ARE LABELS; DIGESTS ARE IDENTITIES. Three counters move
   independently:

       protocol_version         the wire semantics changed
       spec_revision            the normative text or schema changed
       public_corpus_revision   tests grew without the protocol meaning changing

   `--update --spec-revision 1` twice can produce two different releases both
   calling themselves revision 1. Only the digest tells them apart, so the digest
   is what a conformance report cites.
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync, writeFileSync, existsSync, readdirSync, statSync, mkdirSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import { dirname, join, relative } from "node:path";
/* THE PROOF-WIRE CANONICAL ENCODER, not a second one written here. `cas.mjs`
   re-exports it as `canonicalWire`; `jcs_vectors.mjs` gates it against the
   pinned upstream RFC 8785 corpus as octets. A release identity a second
   implementation cannot recompute is not an identity, it is a local habit. */
import { canonicalWire } from "./cas.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const SPEC = join(HERE, "..", "docs", "spec", "proof-wire");
const RELEASE = join(SPEC, "SPEC-RELEASE.json");
const ARCHIVE = join(SPEC, "releases");
const HOLDOUT = join(HERE, "holdout");
const sha = (b) => createHash("sha256").update(b).digest("hex");
const archivePath = (id) => join(ARCHIVE, `${id}.json`);
/** ONE SERIALISATION FOR THE STORED OBJECT, so `SPEC-RELEASE.json` and its
 *  archived copy are compared by BYTES rather than by re-parsing. */
const releaseBytes = (r) => Buffer.from(JSON.stringify(r, null, 1) + "\n", "utf8");

/** THE FILE SET AND THE ORDER ARE DEFINED, not discovered by accident. Every
 *  member is listed as a repository-relative path, sorted lexically, and each
 *  contributes `path + "\n" + sha256(bytes) + "\n"` to the preimage — so a
 *  RENAME changes the digest as surely as an edit does. */
function digestOf(dir, filter = () => true) {
  if (!existsSync(dir)) return { digest: "absent", files: [] };
  const walk = (d) => readdirSync(d).sort().flatMap((f) => {
    const p = join(d, f);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
  const files = walk(dir).filter((p) => filter(relative(dir, p)))
    .map((p) => ({ path: relative(SPEC, p), sha256: sha(readFileSync(p)) }))
    .sort((a, b) => (a.path < b.path ? -1 : 1));
  return { digest: sha(files.map((f) => f.path + "\n" + f.sha256 + "\n").join("")), files };
}

/** NORMATIVE DOCUMENTS AND SCHEMA — everything under the spec root that is not
 *  the corpus, not the release object itself, and not the open-requirements
 *  register (which is declared-open by definition and must be free to grow). */
/** PROCEDURE IS NOT PROTOCOL. The blind-implementation contract describes how
 *  the experiment is CONDUCTED; it says of itself that it is procedural, and
 *  hashing it into the normative digest made a change to the experiment report
 *  that the wire protocol had moved.
 *
 *  P4.6 (F) MAKES THIS A DIRECTORY RULE RATHER THAN A FILENAME SET. v0.2.0 named
 *  one file, so the recipe grammar, the observation grammar and the observation
 *  schema — all of which are experiment surface — would each have had to be
 *  remembered into an exception list, and the failure mode of an exception list
 *  is that the fourth thing is forgotten and silently reports the wire protocol
 *  as having moved. Everything under `experiment/` is procedural; nothing else
 *  is; there is no exception. */
export const isProcedural = (rel) => rel.replace(/\\/g, "/").startsWith("experiment/");
const specSurface = () => digestOf(SPEC, (rel) =>
  !rel.startsWith("vectors") && !rel.startsWith("requirements")
  && !rel.startsWith("releases") && rel !== "SPEC-RELEASE.json" && !isProcedural(rel));
const experimentSurface = () => digestOf(SPEC, (rel) => isProcedural(rel));
const corpusSurface = () => digestOf(join(SPEC, "vectors", "public"));
const jcsSurface = () => digestOf(join(SPEC, "vectors", "jcs-upstream"));
/** THE HOLDOUT IS COMMITTED, NOT PUBLISHED. Its contents live outside the spec
 *  tree so shipping the spec to a blind implementer cannot leak it; only this
 *  digest travels. */
const holdoutSurface = () => digestOf(HOLDOUT);

/** THE RELEASE IDENTITY. Every committed component, and nothing that is
 *  NON_AUTHORITATIVE. Excludes itself, because a digest over a record holding
 *  that digest has no fixpoint. */

/** EVERY RELEASE FIELD IS CLASSIFIED, AND THERE IS NO FIFTH CATEGORY.
 *
 *    DERIVED             this file computes it from the tree
 *    CHECKED             compared against a normative declaration
 *    DECLARED_AND_BOUND  a label the issuer chooses, bound by spec_release_id
 *    NON_AUTHORITATIVE   nothing depends on it
 *
 *  v0.1.0 checked four digests and let the record say what they MEANT, so a
 *  forged release_type, forged protocol names, forged revisions and a forged
 *  holdout count all passed — and were PRINTED. */
export const RELEASE_FIELD_PLANES = Object.freeze({
  release_type: "CHECKED", protocols: "CHECKED",
  spec_revision: "DECLARED_AND_BOUND", spec_digest: "DERIVED", spec_files: "DERIVED",
  experiment_revision: "DECLARED_AND_BOUND", experiment_digest: "DERIVED",
  experiment_files: "DERIVED",
  public_corpus_revision: "DECLARED_AND_BOUND", public_corpus_digest: "DERIVED",
  jcs_upstream: "DERIVED", holdout_commitment: "DERIVED", holdout_entries: "DERIVED",
  spec_release_id: "DERIVED", note: "NON_AUTHORITATIVE",
});
const RELEASE_TYPE = "TRVM-PROOF-WIRE-SPEC-RELEASE-v1";
/** Protocol identifiers are CHECKED against the normative schema, which is
 *  itself inside spec_digest — so a release cannot rename a protocol. */
function normativeProtocols() {
  const p2 = join(SPEC, "schema", "nested-composition-v2.json");
  if (!existsSync(p2)) return null;
  const n = JSON.parse(readFileSync(p2, "utf8"));
  return { wire: "TRVM-PROOF-WIRE-v1", verified_claim: n.constants.certificate_protocol,
    nested_composition: n.constants.protocol };
}

/** THE RELEASE CORE — every committed component, projected explicitly so that a
 *  field ADDED to the release object does not silently join the identity, and a
 *  field REMOVED from it fails the audit below rather than quietly leaving. The
 *  nesting mirrors the record; v0.2.0 hand-flattened `jcs_upstream` into four
 *  scalars, which is the same instinct that produced the replacer array. */
export function releaseCore(r) {
  return {
    release_type: r.release_type,
    protocols: {
      wire: r.protocols?.wire,
      verified_claim: r.protocols?.verified_claim,
      nested_composition: r.protocols?.nested_composition,
    },
    spec_revision: r.spec_revision,
    spec_digest: r.spec_digest,
    experiment_revision: r.experiment_revision,
    experiment_digest: r.experiment_digest,
    public_corpus_revision: r.public_corpus_revision,
    public_corpus_digest: r.public_corpus_digest,
    jcs_upstream: {
      repository: r.jcs_upstream?.repository,
      commit: r.jcs_upstream?.commit,
      digest: r.jcs_upstream?.digest,
      vectors: r.jcs_upstream?.vectors,
    },
    holdout_commitment: r.holdout_commitment,
    holdout_entries: r.holdout_entries,
  };
}

export function releaseId(r) {
  return "srel-" + createHash("sha256")
    .update(Buffer.from(RELEASE_TYPE + "|" + canonicalWire(releaseCore(r)), "utf8"))
    .digest("hex");
}

/** THE IDENTITY IS AUDITED IN BOTH DIRECTIONS, MECHANICALLY.
 *
 *  POSITIVE  every leaf of the core, perturbed one at a time, MUST move `srel`.
 *            v0.2.0 failed this on three leaves and the grid said otherwise.
 *  NEGATIVE  every field of the release OUTSIDE the core, perturbed, MUST NOT
 *            move it — the half that catches an identity quietly growing to
 *            cover prose. `note` is NON_AUTHORITATIVE; the two file listings are
 *            the inputs to digests that ARE in the core, so binding them twice
 *            would make a rename look like two different changes.
 *
 *  The denominator is derived by walking the core, not typed here. */
const NON_CORE = Object.freeze(["note", "spec_files", "experiment_files"]);
const leafPaths = (o, prefix = []) =>
  (o !== null && typeof o === "object" && !Array.isArray(o))
    ? Object.keys(o).flatMap((k) => leafPaths(o[k], [...prefix, k]))
    : [prefix.join(".")];
const perturb = (v) => typeof v === "number" ? v + 1
  : typeof v === "boolean" ? !v
  : typeof v === "string" ? v + "-FALSIFIER"
  : "FALSIFIER";
const setAt = (o, path, v) => {
  const ks = path.split(".");
  let cur = o;
  for (const k of ks.slice(0, -1)) cur = cur[k];
  cur[ks[ks.length - 1]] = v;
};
const readAt = (o, path) => path.split(".").reduce((x, k) => (x == null ? x : x[k]), o);
export function auditIdentity(r) {
  const id = releaseId(r), moved = [], stuck = [], leaked = [];
  for (const path of leafPaths(releaseCore(r))) {
    const c = JSON.parse(JSON.stringify(r));
    setAt(c, path, perturb(readAt(r, path)));
    (releaseId(c) === id ? stuck : moved).push(path);
  }
  for (const k of NON_CORE) {
    if (!(k in r)) continue;
    const c = JSON.parse(JSON.stringify(r));
    c[k] = Array.isArray(c[k]) ? [...c[k], { path: "FALSIFIER", sha256: "0".repeat(64) }]
                               : perturb(c[k]);
    if (releaseId(c) !== id) leaked.push(k);
  }
  return { checked: moved.length + stuck.length, moved: moved.length, stuck, leaked };
}

export function computeRelease(existing = {}) {
  const spec = specSurface(), corpus = corpusSurface(), jcs = jcsSurface(), hold = holdoutSurface();
  const exp = experimentSurface();
  /* DERIVED, NOT COUNTED CASUALLY. v0.1.0 said `files.length / 2` and reported
     3.5 upstream vectors, because PROVENANCE.md made the file count odd. A
     release field that is arithmetic on a directory listing is a release field
     that can be wrong quietly. */
  const jcsInputs = existsSync(join(SPEC, "vectors", "jcs-upstream", "input"))
    ? readdirSync(join(SPEC, "vectors", "jcs-upstream", "input")).filter((f) => f.endsWith(".json")).length
    : 0;
  const r = {
    release_type: "TRVM-PROOF-WIRE-SPEC-RELEASE-v1",
    protocols: {
      wire: "TRVM-PROOF-WIRE-v1",
      verified_claim: "TRVM-VERIFIED-CLAIM-v1",
      nested_composition: "TRVM-NESTED-COMPOSITION-v2",
    },
    note: "Revision numbers are LABELS. Digests are IDENTITIES. Two releases may both call " +
      "themselves spec revision 1; only the digest distinguishes them, so a conformance report " +
      "cites the digest. This object excludes itself from its own preimage. The holdout is " +
      "COMMITTED here and its contents are NOT in this tree.",
    spec_revision: existing.spec_revision ?? 1,
    spec_digest: spec.digest,
    spec_files: spec.files,
    experiment_revision: existing.experiment_revision ?? 1,
    experiment_digest: exp.digest,
    experiment_files: exp.files,
    public_corpus_revision: existing.public_corpus_revision ?? 1,
    public_corpus_digest: corpus.digest,
    jcs_upstream: {
      repository: "github.com/cyberphone/json-canonicalization",
      path: "testdata/",
      commit: "19d51d7fe467d4706a3ff08adf8a748f29fc21e0",
      digest: jcs.digest,
      vectors: jcsInputs,
    },
    holdout_commitment: hold.digest,
    holdout_entries: holdoutEntries(hold).count,
    spec_release_id: null,
  };
  r.spec_release_id = releaseId(r);
  return r;
}

/** DERIVED FROM THE INDEX AND CROSS-CHECKED AGAINST THE TREE, not arithmetic on
 *  a directory listing. v0.2.0 said `files.length - 1` — subtract the index —
 *  which is the same shape as v0.1.0's `files.length / 2` that reported 3.5
 *  upstream vectors. One file appearing beside the entries that is not an entry
 *  and not the index would have made it wrong quietly; now the two counts have
 *  to agree and the disagreement is the finding. */
function holdoutEntries(hold) {
  const idx = join(HOLDOUT, "INDEX.json");
  if (!existsSync(idx)) return { count: 0, problem: null, source: "absent" };
  const entries = JSON.parse(readFileSync(idx, "utf8")).entries ?? [];
  const expected = entries.length + 1;
  return { count: entries.length, source: "INDEX.json entries[]",
    problem: hold.files.length === expected ? null
      : `holdout_entries: INDEX.json lists ${entries.length} entries, so the committed tree must ` +
        `hold ${expected} files (the entries and the index); it holds ${hold.files.length}` };
}

/* P4.6, FOUND WHILE BUILDING THE FALSIFIER: THIS MODULE EXITED ITS HOST ON
   IMPORT. Everything below ran at import time, so `import { releaseCore }` from
   any other file performed a full verification run and then called
   `process.exit` — the reproduction script for defect (A) died on the module it
   was reproducing against, printing the verifier's output twice. `nest_check`,
   `holdout_score` and `field_audit` all carry this guard; this one did not, and
   nothing had imported it before. */
const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
const argv = process.argv.slice(2);
const UPDATE = IS_MAIN && argv.includes("--update");
/** P4.7.9. A REVISION FLAG WITH NO VALUE USED TO CRASH A WRITE COMMAND.
 *
 *  `Number(argv[i + 1])` of `undefined` is NaN, which travelled two modules down
 *  and died inside `canonicalBytes` as `not-canonical: non-finite number at
 *  $.experiment_revision` — a stack trace, from `--update`, naming neither the
 *  flag nor the fix. That is the species P4.7.7 found three times over
 *  (`loadChallenges`, the runner's release read, `readRun()`): a refusal path
 *  that THROWS where every other refusal in this tree REPORTS. It matters more
 *  here than there, because this one is on the write path, and an operator whose
 *  release command dies in an unrelated file has no way to know whether it wrote
 *  anything. (It had not — the throw is before the write — but that is a fact
 *  about the ordering, not a thing the message says.) */
const bump = (name) => {
  const i = argv.indexOf(name);
  if (i < 0) return null;
  const raw = argv[i + 1];
  const n = Number(raw);
  if (raw === undefined || !/^[0-9]+$/.test(String(raw)) || !Number.isInteger(n) || n < 1) {
    console.log(`SPEC-RELEASE: REFUSED — ${name} needs a positive integer and got ` +
      `${raw === undefined ? "nothing" : `"${raw}"`}. A revision is DECLARED_AND_BOUND: it is not ` +
      `derived from the tree, so nothing downstream can correct a typo in it, and NOTHING WAS ` +
      `WRITTEN.`);
    process.exit(2);
  }
  return n;
};

if (!IS_MAIN) { /* imported for releaseCore / releaseId / auditIdentity */ }
else if (UPDATE) {
  const existing = existsSync(RELEASE) ? JSON.parse(readFileSync(RELEASE, "utf8")) : {};
  const r = computeRelease({
    spec_revision: bump("--spec-revision") ?? existing.spec_revision ?? 1,
    experiment_revision: bump("--experiment-revision") ?? existing.experiment_revision ?? 1,
    public_corpus_revision: bump("--corpus-revision") ?? existing.public_corpus_revision ?? 1,
  });
  const bytes = releaseBytes(r);
  /* ISSUANCE MUST NOT MINT A RELEASE WHOSE IDENTITY DOES NOT BIND ITS OWN
     COMMITMENTS. The audit that repairs the v0.2.0 defect runs here too, so a
     future edit to `releaseCore` that drops a member is refused at the moment it
     would otherwise be signed. */
  const audit = auditIdentity(r);
  if (audit.stuck.length || audit.leaked.length) {
    console.log(`SPEC-RELEASE: REFUSED TO ISSUE — spec_release_id does not bind ` +
      `[${audit.stuck.join(", ")}]` +
      (audit.leaked.length ? ` and wrongly binds [${audit.leaked.join(", ")}]` : ""));
    process.exit(1);
  }
  const hp = holdoutEntries(holdoutSurface()).problem;
  if (hp) { console.log(`SPEC-RELEASE: REFUSED TO ISSUE — ${hp}`); process.exit(1); }
  /* A RELEASE IS AN IMMUTABLE OBJECT WRITTEN UNDER ITS OWN IDENTITY. The
     conventional filename is a CURRENT pointer; the archive is the history. Two
     issuances that agree on every core field but differ in prose share an
     identity and DIFFER in bytes — refused here rather than silently
     overwritten, which is what makes a NON_AUTHORITATIVE field immutable per
     identity without being inside it. */
  mkdirSync(ARCHIVE, { recursive: true });
  const at = archivePath(r.spec_release_id);
  if (existsSync(at) && !readFileSync(at).equals(bytes)) {
    console.log(`SPEC-RELEASE: REFUSED TO ISSUE — ${r.spec_release_id} is already archived with ` +
      `DIFFERENT bytes. A release is immutable under its identity: the core fields agree, so some ` +
      `NON_AUTHORITATIVE field moved. Archived releases are never overwritten`);
    process.exit(1);
  }
  writeFileSync(at, bytes);
  writeFileSync(RELEASE, bytes);
  console.log(`SPEC-RELEASE: ISSUED — ${r.spec_release_id} — protocol ` +
    `${r.protocols.nested_composition}, spec revision ${r.spec_revision} ` +
    `(${r.spec_digest.slice(0, 16)}…), experiment revision ${r.experiment_revision} ` +
    `(${r.experiment_digest.slice(0, 16)}…), public corpus revision ` +
    `${r.public_corpus_revision} (${r.public_corpus_digest.slice(0, 16)}…), ` +
    `${r.holdout_entries} holdout entries committed as ${r.holdout_commitment.slice(0, 16)}…, ` +
    `archived at releases/${r.spec_release_id}.json, identity audited over ${audit.checked} core ` +
    `leaves. THIS IS A NORMATIVE ACT and no gate performs it.`);
  process.exit(0);
}

else if (!existsSync(RELEASE)) {
  console.log("SPEC-RELEASE: FAIL — no SPEC-RELEASE.json. Issue one deliberately with " +
    "`node spec_release.mjs --update --spec-revision <N>`; a verification run will not mint a " +
    "release for itself.");
  process.exit(1);
}
else {
  const stored = JSON.parse(readFileSync(RELEASE, "utf8"));
  const live = computeRelease(stored);
  const problems = [];

  /* ── THE FIELD AUDIT, MECHANICALLY ─────────────────────────────────────── */
  for (const k of Object.keys(stored))
    if (!(k in RELEASE_FIELD_PLANES))
      problems.push(`release field ${k} is UNCLASSIFIED — every field is DERIVED, CHECKED, ` +
        `DECLARED_AND_BOUND or NON_AUTHORITATIVE, and there is no fifth category`);
  for (const [k, plane] of Object.entries(RELEASE_FIELD_PLANES)) {
    if (plane === "NON_AUTHORITATIVE") continue;
    if (!(k in stored)) { problems.push(`release field ${k} [${plane}] is missing`); continue; }
    if (plane === "DERIVED" && JSON.stringify(stored[k]) !== JSON.stringify(live[k]))
      problems.push(`${k} [DERIVED]: released ${JSON.stringify(stored[k]).slice(0, 56)}… · this tree ` +
        `${JSON.stringify(live[k]).slice(0, 56)}…`);
  }
  if (stored.release_type !== RELEASE_TYPE)
    problems.push(`release_type [CHECKED]: ${JSON.stringify(stored.release_type)}, this verifier ` +
      `implements ${JSON.stringify(RELEASE_TYPE)}`);
  const np = normativeProtocols();
  if (!np) problems.push("no normative schema to check the protocol identifiers against");
  else for (const k of Object.keys(np))
    if (stored.protocols?.[k] !== np[k])
      problems.push(`protocols.${k} [CHECKED]: released ${JSON.stringify(stored.protocols?.[k])}, ` +
        `the normative schema says ${JSON.stringify(np[k])}`);
  if (stored.spec_release_id !== releaseId(stored))
    problems.push(`spec_release_id does not identify the release beside it — a revision label, a ` +
      `protocol name or a commitment moved without the identity moving`);
  /* THE IDENTITY FORMULA IS AUDITED ON EVERY RUN, NOT ONLY AT ISSUANCE. P4.6 (A):
     v0.2.0's `srel` was invariant under renaming all three protocols, so the
     statement "the release identity binds the protocol identifiers" was false at
     the formula. A one-way sweep is not enough — the negative half catches the
     identity growing to cover prose. */
  const audit = auditIdentity(stored);
  for (const path of audit.stuck)
    problems.push(`spec_release_id [IDENTITY]: perturbing core member ${path} does NOT move the ` +
      `identity — the formula does not bind what the invariant says it binds`);
  for (const k of audit.leaked)
    problems.push(`spec_release_id [IDENTITY]: perturbing NON-core field ${k} MOVES the identity — ` +
      `the identity has grown to cover something declared outside it`);
  /* THE ARCHIVE IS THE HISTORY; SPEC-RELEASE.json IS A POINTER INTO IT. Absent is
     NOT a normal state here, unlike the holdout: issuance writes the archive, so a
     missing one means the pointer was written by something that is not issuance. */
  const at = archivePath(stored.spec_release_id);
  if (!existsSync(at))
    problems.push(`releases/${stored.spec_release_id}.json is MISSING — a release is an immutable ` +
      `object written under its own identity and SPEC-RELEASE.json is a pointer to it, not the only ` +
      `copy. Reissue with --update, which writes both`);
  else if (!readFileSync(at).equals(readFileSync(RELEASE)))
    problems.push(`releases/${stored.spec_release_id}.json and SPEC-RELEASE.json DISAGREE by bytes ` +
      `while sharing an identity — a NON_AUTHORITATIVE field was edited in place after issuance`);
  const holdoutProblem = holdoutEntries(holdoutSurface()).problem;
  if (holdoutProblem) problems.push(holdoutProblem);
  for (const k of ["spec_digest", "experiment_digest", "public_corpus_digest"])
    if (stored[k] !== live[k])
      problems.push(`${k}: released ${String(stored[k]).slice(0, 20)}… · this tree ` +
        `${String(live[k]).slice(0, 20)}…`);
  /* THE HOLDOUT HAS THREE STATES, NOT TWO. Its contents are deliberately absent
     from anything the specification is shipped in, so a tree without them is the
     NORMAL distribution rather than a defect — but "I could not check it" must
     never print as "I checked it". Absent is reported and does not fail; present
     and different is a failure, because that is somebody having altered a
     challenge set after it was committed. */
  const holdoutState = live.holdout_commitment === "absent" ? "NOT PRESENT IN THIS TREE"
    : stored.holdout_commitment === live.holdout_commitment ? "VERIFIED" : "MISMATCH";
  if (holdoutState === "MISMATCH")
    problems.push(`holdout_commitment: released ${String(stored.holdout_commitment).slice(0, 20)}… ` +
      `· this tree ${String(live.holdout_commitment).slice(0, 20)}… — a committed challenge set was ` +
      `altered after it was committed`);
  if (stored.jcs_upstream?.digest !== live.jcs_upstream.digest)
    problems.push(`jcs_upstream.digest: released ${String(stored.jcs_upstream?.digest).slice(0, 20)}… ` +
      `· this tree ${live.jcs_upstream.digest.slice(0, 20)}…`);
  /* WHICH FILE MOVED, because "the spec digest differs" is a verdict. */
  if (problems.length) {
    const was = new Map((stored.spec_files ?? []).map((f) => [f.path, f.sha256]));
    for (const f of live.spec_files) {
      if (!was.has(f.path)) problems.push(`  NEW normative file: ${f.path}`);
      else if (was.get(f.path) !== f.sha256) problems.push(`  EDITED since the release: ${f.path}`);
    }
    for (const p of was.keys())
      if (!live.spec_files.some((f) => f.path === p)) problems.push(`  REMOVED since the release: ${p}`);
  }

  for (const p of problems.slice(0, 12)) console.log(`  ${p}`);
  console.log(problems.length === 0
    ? `SPEC-RELEASE: PASS — ${stored.spec_release_id} — this tree IS that release. ` +
      `${stored.spec_files.length} normative files bound by digest ` +
      `${stored.spec_digest.slice(0, 16)}… at spec revision ${stored.spec_revision}; public corpus ` +
      `revision ${stored.public_corpus_revision} at ${stored.public_corpus_digest.slice(0, 16)}…; ` +
      `${stored.jcs_upstream.vectors} pinned upstream JCS vectors; and ${stored.holdout_entries} ` +
      `HOLDOUT entries committed as ${stored.holdout_commitment.slice(0, 16)}…, whose contents are ` +
      `${holdoutState} — absent is the NORMAL state for a distributed specification and is reported ` +
      `rather than silently passed, because a commitment that cannot be checked here must not print ` +
      `as one that was. Before this object existed, editing the normative formula in a Markdown ` +
      `document — the one surface a blind implementer reads and no gate executes — left both ` +
      `SPEC-AGREEMENT and SPEC-VECTORS green. EVERY RELEASE FIELD IS DERIVED, CHECKED, ` +
      `DECLARED_AND_BOUND OR NON_AUTHORITATIVE and the audit is mechanical: a release that forged ` +
      `its own release_type, protocol names, revisions and holdout count while leaving every ` +
      `component digest honest used to PASS and PRINT the forgery. AND spec_release_id IS THE ` +
      `IDENTITY, MEASURED RATHER THAN ASSERTED — the preimage is canonicalWire(core) under the same ` +
      `RFC 8785 encoder the wire protocol uses, and all ${audit.checked} core leaves were perturbed ` +
      `one at a time and all ${audit.moved} moved it, while ${NON_CORE.length} declared non-core ` +
      `fields were perturbed and none did. Until this run the preimage was built by a JSON.stringify ` +
      `replacer ARRAY, which is an allowlist applied RECURSIVELY, so the nested protocol map ` +
      `serialised as {} and renaming all three protocols left the identity byte-identical. PROCEDURE ` +
      `IS NOT PROTOCOL: everything under experiment/ carries its own revision ` +
      `${stored.experiment_revision} and digest — a directory rule, not a filename set, because the ` +
      `recipe grammar, the observation grammar and the observation schema are all experiment ` +
      `surface. AND A RELEASE IS AN IMMUTABLE OBJECT: this one is archived at ` +
      `releases/${stored.spec_release_id}.json, byte-identical to the pointer beside it, and ` +
      `issuance refuses to overwrite an archived identity with different bytes`
    : `SPEC-RELEASE: FAIL — this tree is NOT the released normative specification ` +
      `(${problems.length} difference(s)). Either a normative byte changed without a release being ` +
      `issued, or the release is stale. Issue a numbered revision deliberately`);
  process.exit(problems.length === 0 ? 0 : 1);
}
