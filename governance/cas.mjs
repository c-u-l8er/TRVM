/* ═══════════════════════════════════════════════════════════════════════════
   cas.mjs — v0.3.0 — THE WIRE IS BYTES, AND STILL NOT A WARRANT
   law:proof.content-address-is-not-a-warrant@1 · law:proof.canonical-wire@1

   P4 said the root was an address. IT WAS NOT AN ADDRESS, and the counterexample
   is two lines. `artifactRoot` hashed the PARSED object, so any byte string that
   parsed to that object resolved under that root. Reproduced against the shipped
   P4 pack before this file changed:

       honest bytes   4880          pretty-printed, as stored
       compact bytes  4509          JSON.stringify(sameObject)
       different      true
       resolveArtifact(root) → ok   BOTH

   and then, adversarially:

       {"protocol":"TRVM-EVIL-v1", … ,"protocol":"TRVM-NESTED-COMPOSITION-v1", …}

   `JSON.parse` keeps the LAST duplicate, so the parsed object — and therefore
   the root — is the honest one, and the hostile bytes were AUTHENTICATED as the
   honest artifact: `resolveArtifact → ok`, `checkNestBundle → VERIFIED`, zero
   refusals, with `TRVM-EVIL-v1` sitting in the bytes the store served.

   THAT IS A CROSS-IMPLEMENTATION HAZARD, NOT A FORMATTING ONE. RFC 8259 says
   behaviour on duplicate member names is unpredictable across parsers; I-JSON
   prohibits them outright; RFC 8785's canonicalisation scheme requires I-JSON
   input and therefore forbids them. A second implementation of this protocol —
   the next axis of work — could reasonably keep the FIRST duplicate and disagree
   with this one about which object a root names, while both believed they had
   verified the same artifact.

   SO THE CAS SPEAKS ONE LANGUAGE. Resolution is:

       raw bytes
         → strict parse
         → canonicalise the parsed object
         → REQUIRE raw === canonical      ← duplicate keys, alternate number
         → hash the canonical bytes         spellings, key reordering and
         → compare to the cited root        whitespace all die here at once
                                            rather than one special case each

   Duplicate-key rejection is a CONSEQUENCE of that equality rather than a check
   of its own: canonical output emits every key once, so bytes containing a
   repeat can never equal the canonical form of what they parse to. Pretty JSON
   remains the export and presentation format — `proof_bundle.json` on disk is
   still indented — but what goes into the store is boring canonical bytes.

   AND THE TREE HAS ONE CANONICAL ENCODER, NOT TWO. `canonicalWire` IS
   `canonicalBytes`, the encoder every semantic id in this tree already runs
   through. Introducing a second one would mean two things called canonical that
   nothing compared. `jcs_vectors.mjs` measures it against published RFC 8785
   data instead of against inspection.

   THREE THINGS THIS MODULE KEEPS APART, unchanged from v0.1.0:

       identity      a content hash               WHAT this artifact IS
       availability  a store resolves it          WHERE the bytes came from
       warrant       a verifier-owned issuance    THAT it was ACCEPTED

   There is still no `verify()` here, no verdict field and no accepted-set. A
   store may be asked one question and may give one kind of answer.

   AND v0.2.0 STILL WASN'T BYTES. `canonicalWire` returned a JavaScript STRING,
   `directoryStore` read files with the forgiving `"utf8"` decoder before any
   validity decision, and every budget counted `String.length`. Reproduced
   against the shipped P4.1 pack:

       canonical UTF-8   7b 22 78 22 3a 22 ef bf bd 22 7d      {"x":"\uFFFD"}
       stored on disk    7b 22 78 22 3a 22 ff       22 7d      a raw 0xFF
       resolveArtifact → ok

   Node substituted U+FFFD for the invalid byte before the equality ran, so two
   different byte strings were again accepted as one wire artifact — the exact
   defect v0.2.0 existed to close, one layer lower. And the budget:

       canonical JS string length  15      actual UTF-8 bytes  29
       limit 16  →  resolveArtifact → ok

   RFC 8785 constrains its input to I-JSON, requires lone surrogates to
   terminate canonicalisation with an error, and says the canonical form is
   UTF-8 BYTES. So the wire is bytes here too: stores return `Buffer`, the size
   bound is applied to those bytes, decoding is FATAL, the canonical form is
   re-encoded to UTF-8 and compared with `Buffer.compare`, and the hash consumes
   the bytes. `hash.update(string)` already encoded as UTF-8 implicitly, so no
   root and no semantic id moves — asserted rather than assumed.

   AND AN UNTRUSTED CITATION MAY NOT STEER A FILESYSTEM READ. `directoryStore`
   used to do `join(dir, root + ".json")` with whatever string arrived, so
   `get("../proof_bundle")` READ THE 1.31 MB PROOF BUNDLE from outside the store
   before the root comparison rejected it. Integrity caught the wrong artifact;
   nothing caught the traversal. Root syntax is validated before any path is
   built, and `ROOT_SYNTAX` is the grammar.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, existsSync, mkdirSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { canonicalBytes } from "./derive_protocol.mjs";

export const ARTIFACT_ROOT_PROTOCOL = "TRVM-ARTIFACT-ROOT-v2";
const TAG = Buffer.from(ARTIFACT_ROOT_PROTOCOL + "|", "utf8");
/** FATAL. The whole point: an invalid byte is a refusal, not a U+FFFD. */
const UTF8 = new TextDecoder("utf-8", { fatal: true });
const H = (s) => createHash("sha256").update(s).digest("hex");

/** THE CAS WIRE ENCODER. Deliberately the SAME FUNCTION as the semantic-id
 *  encoder rather than a second implementation of the same standard — see the
 *  header — and measured against RFC 8785 vectors in `jcs_vectors.mjs`.
 *  Returns canonical JSON TEXT; `canonicalWireBytes` is the wire form. */
export const canonicalWire = canonicalBytes;
/** THE WIRE FORM: canonical text encoded as UTF-8 bytes. Everything that
 *  measures, compares or hashes an artifact goes through this. */
export const canonicalWireBytes = (v) => Buffer.from(canonicalWire(v), "utf8");

/** THE GRAMMAR OF A ROOT, checked before a root reaches a path, a store or a
 *  hash. A citation is untrusted input and `../proof_bundle` is a perfectly
 *  good string. */
export const ROOT_SYNTAX = /^root-[0-9a-f]{64}$/;
export const isRoot = (s) => typeof s === "string" && ROOT_SYNTAX.test(s);

/** RESOURCE BOUNDS THE STORE OWNS. An untrusted CAS supplies not only wrong
 *  artifacts but arbitrarily large ones, and a verifier that parsed whatever
 *  arrived would have its memory decided by the thing it is checking. The
 *  ceiling is comfortably above the largest artifact this tree produces (P1's
 *  bundle canonicalises to ~1.27 MB) and is a POLICY value, not a fact. */
export const WIRE_LIMITS = Object.freeze({ max_artifact_bytes: 8 * 1024 * 1024 });

/** The identity of an artifact: the hash of its canonical bytes. */
export function artifactRoot(obj) {
  return rootOfBytes(canonicalWireBytes(obj));
}
/** The identity of a byte string that has ALREADY been validated as canonical.
 *  Separated so the resolver hashes the bytes it compared rather than
 *  re-deriving from an object, which is the same value and a shorter argument. */
export const rootOfBytes = (bytes) =>
  "root-" + createHash("sha256").update(Buffer.concat([TAG, bytes])).digest("hex");

/** The canonical byte length — UTF-8 BYTES, not `String.length`. v0.2.0 used
 *  the latter, so a multibyte artifact measured 15 where it weighed 29 and
 *  every budget in the protocol was denominated in the wrong unit. */
export const artifactBytes = (obj) => canonicalWireBytes(obj).length;

/* ── A STORE IS A FUNCTION FROM A ROOT TO BYTES OR NOTHING ────────────────── */

/** A directory of `<root>.json` holding CANONICAL bytes. The filename is the
 *  root; a store filing bytes under the wrong name is caught by the caller's
 *  re-derivation rather than by anything here. Syntax is validated BEFORE the
 *  path is built — that is the traversal fix, and it is in the store rather
 *  than only in the resolver because the store is the thing holding a
 *  filesystem. */
export function directoryStore(dir) {
  return {
    kind: "directory",
    where: dir,
    /** RETURNS BYTES. Reading with `"utf8"` handed the resolver a string in
     *  which an invalid byte had already become U+FFFD — a decision the store
     *  is not entitled to make, taken before anything could refuse it. */
    get(root) {
      if (!isRoot(root)) return null;
      const p = join(dir, root + ".json");
      if (!existsSync(p)) return null;
      if (statSync(p).size > WIRE_LIMITS.max_artifact_bytes) return null;
      return readFileSync(p);
    },
    roots() {
      if (!existsSync(dir)) return [];
      return readdirSync(dir).filter((f) => f.endsWith(".json")).map((f) => f.slice(0, -5));
    },
  };
}

/** A store held in memory, for generators and for adversaries. Nothing requires
 *  the mapping to be honest, and the forgery suite depends on it not being. */
export function memoryStore(entries = new Map()) {
  return {
    kind: "memory",
    where: "(memory)",
    /** IDENTICAL BYTE SEMANTICS TO `directoryStore`. Two stores that disagreed
     *  about what a wire artifact is would make every measurement taken through
     *  one of them a fact about the store rather than about the protocol. */
    get(root) {
      if (!isRoot(root) || !entries.has(root)) return null;
      const v = entries.get(root);
      return Buffer.isBuffer(v) ? v : Buffer.from(v, "utf8");
    },
    roots() { return [...entries.keys()]; },
    put(obj) {
      const bytes = canonicalWireBytes(obj);
      const root = rootOfBytes(bytes);
      entries.set(root, bytes);
      return root;
    },
    entries,
  };
}

/** Write an artifact into a directory store and return its root. Producers
 *  only; a checker never writes. CANONICAL BYTES, no trailing newline — the
 *  file IS the wire form, and a byte a reader would not miss is still a byte
 *  the equality check would. */
export function putArtifact(dir, obj) {
  mkdirSync(dir, { recursive: true });
  const bytes = canonicalWireBytes(obj);
  const root = rootOfBytes(bytes);
  writeFileSync(join(dir, root + ".json"), bytes);
  return root;
}

/* ── RESOLUTION, AND ITS SEVEN OUTCOMES ─────────────────────────────────────
   Named rather than thrown, because every one of them is something an untrusted
   store or an untrusted citation can do, and a checker that raised would be
   refusing by stack trace. */

export const RESOLVE_OUTCOMES = Object.freeze(
  ["ok", "bad-root-syntax", "unresolvable", "too-large", "invalid-utf8", "malformed",
   "non-canonical-wire", "root-mismatch"]);

/** Ask a store for a root, and DO NOT BELIEVE IT — nor the citation that named
 *  the root.
 *
 *  `ok` means exactly three things and no more: the cited name is a well-formed
 *  root, the bytes returned are the canonical encoding of the object they parse
 *  to, and that object's root is the one that was asked for. It does NOT mean
 *  the artifact is valid, checked or accepted — nothing in this file has an
 *  opinion about that. */
export function resolveArtifact(store, root, { max_artifact_bytes } = {}) {
  const limit = max_artifact_bytes ?? WIRE_LIMITS.max_artifact_bytes;
  const no = (outcome, detail, extra = {}) =>
    ({ outcome, artifact: null, bytes: null, derived_root: null, detail, ...extra });

  /* FIRST, AND BEFORE THE STORE IS TOUCHED AT ALL. `../proof_bundle` reached a
     `join()` in v0.1.0 and read a megabyte from outside the store. */
  if (!isRoot(root))
    return no("bad-root-syntax",
      `${JSON.stringify(String(root)).slice(0, 60)} is not a root — a citation is untrusted input ` +
      `and must satisfy ${ROOT_SYNTAX} before it reaches a path, a store or a hash`);

  let bytes = null;
  try { bytes = store?.get?.(root) ?? null; } catch { bytes = null; }
  if (typeof bytes === "string") bytes = Buffer.from(bytes, "utf8");
  if (!Buffer.isBuffer(bytes) && !(bytes instanceof Uint8Array))
    return no("unresolvable", `no bytes in ${store?.where ?? "the store"} under ${root}`);
  /* COPIED, ALWAYS. An untrusted store handing back its own Buffer leaves the
     verifier reasoning about storage the store can still write to. "The
     verifier owns the bytes" has to be literally true. */
  bytes = Buffer.from(bytes);

  /* THE BOUND IS ON BYTES. v0.2.0 measured `String.length`, so a multibyte
     artifact weighing 29 bytes passed a 16-byte ceiling. */
  if (bytes.length > limit)
    return no("too-large",
      `${bytes.length} bytes under ${root}, over this verifier's ${limit}-byte ceiling — an ` +
      `untrusted store does not get to choose how much memory a check costs`);

  /* FATAL DECODE. The forgiving decoder turns an invalid byte into U+FFFD, and
     a substitution performed before the equality is a substitution the equality
     cannot see: two byte strings, one artifact. */
  let text;
  try { text = UTF8.decode(bytes); }
  catch (e) {
    return no("invalid-utf8",
      `the ${bytes.length} bytes under ${root.slice(0, 24)}… are not valid UTF-8 ` +
      `(${String(e?.message ?? e)}). A decoder that substituted U+FFFD here would let two ` +
      `different byte strings be one wire artifact`, { bytes });
  }

  let artifact;
  try { artifact = JSON.parse(text); }
  catch (e) {
    return no("malformed",
      `${bytes.length} bytes under ${root} do not parse: ${String(e?.message ?? e)}`, { bytes });
  }

  /* THE WIRE IS CANONICAL OR IT IS REFUSED, compared as BYTES. A lone surrogate
     arriving as a `\uD800` escape makes the canonical form UNDEFINED rather
     than different — RFC 8785 says it terminates canonicalisation — so it
     lands here as malformed rather than as a mismatch. */
  let canonical;
  try { canonical = canonicalWireBytes(artifact); }
  catch (e) {
    return no("malformed",
      `the object under ${root} has no canonical form: ${String(e?.message ?? e)}`, { bytes });
  }
  if (!canonical.equals(bytes))
    return no("non-canonical-wire",
      `the bytes under ${root.slice(0, 24)}… are not the canonical UTF-8 encoding of what they ` +
      `parse to (${bytes.length} received, ${canonical.length} canonical). Duplicate member ` +
      `names, a different key order, another number spelling and any whitespace all land here — ` +
      `and the first of those is a cross-implementation hazard, not a formatting preference`,
      { bytes });

  const derived = rootOfBytes(canonical);
  if (derived !== root)
    return no("root-mismatch",
      `the store answered ${root.slice(0, 24)}… with bytes whose own root is ` +
      `${derived.slice(0, 24)}… — a store may be wrong or hostile and this is where that stops`,
      { bytes, derived_root: derived });

  return { outcome: "ok", artifact, bytes, derived_root: derived, detail: null };
}
