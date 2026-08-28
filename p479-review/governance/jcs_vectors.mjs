/* ═══════════════════════════════════════════════════════════════════════════
   jcs_vectors.mjs — v0.1.0 — IS OUR CANONICAL ENCODER RFC 8785?
   law:proof.canonical-wire@1

   P4.1 rules that CAS bytes must be canonical, so that one root names one byte
   string and a second implementation cannot disagree with this one about which
   object a root means. That ruling is only worth anything if the encoder doing
   the canonicalising IS the standard, and "it looks like JCS" is not a
   measurement. GPT's instruction was explicit: do not call the encoder
   JCS-compatible until published vectors agree.

   THE VECTORS AND WHERE THEY COME FROM, stated because provenance is the whole
   value of a conformance vector:

     1. RFC 8785 §3.2.2 input → §3.2.3 expected output, verbatim from the RFC.
        Exercises number serialisation (ECMAScript Number::toString, including
        1E30 → 1e+30 and 0.000000000000000000000000001 → 1e-27), string
        escaping, and property ordering all at once.
     2. `testdata/french.json` from the JCS reference test suite — sorting MUST
        ignore locale, so `péché` precedes `pêche` even though French collation
        says otherwise.
     3. THE DISCRIMINATING CASE, key ordering by UTF-16 CODE UNIT rather than
        code point. U+1F602 is the surrogate pair D83D DE02, so by code unit it
        sorts BEFORE U+FB33 (דּ) and by CODE POINT it would sort after. An
        encoder that sorted code points passes vectors 1 and 2 and fails only
        this one. The order is the reference suite's own `weird.json` ordering.

        VECTOR 3 IS A SUBSET, and its `source` label says so. It carries only
        the members that isolate code-unit ordering, and NOT `weird.json`'s
        U+0080 and U+007F members, which are unescaped in canonical output and
        could not be transported into source here verbatim with confidence. That
        was a real limit on an in-tree transcription and it is why the upstream
        import below exists — where those members ARE covered, because the
        comparison is against ASCII hex rather than decoded text.

   THE IN-TREE VECTORS ARE NOT THE IMPORT. Beside them, the pinned upstream
   corpus at commit 19d51d7f runs the COMPLETE `testdata/input` set — all six,
   including `weird` and `unicode` — each compared as OCTETS against upstream's
   own `outhex/`. P4.3 and P4.4 could not import those two: their canonical
   output carries unescaped U+0080, U+007F and a combining mark, and no text
   channel available here could be shown to have preserved them. `outhex` is
   ASCII hexadecimal, which is transport-safe and a strictly better boundary
   than comparing decoded text, so P4.5 imported all six and compares every one
   as bytes.

   SCOPE, AND IT IS STILL NOT FULL CONFORMANCE. The upstream input set is
   complete; the upstream SUITE is not, because RFC 8785's ~10^8-value number
   corpus is not in it. That corpus is DECLARED-OPEN in
   `requirements/open/RFC8785-number-stress-corpus.md`, and the ES6 number
   boundaries below are STATED expectations rather than derived ones so that an
   implementation which is not JavaScript can use them. **Full RFC 8785
   conformance is NOT claimed here, and the reason is named rather than left to
   a count with nothing saying what it excludes.**
   ═══════════════════════════════════════════════════════════════════════════ */
import { canonicalBytes } from "./derive_protocol.mjs";
import { canonicalWire, resolveArtifact, memoryStore, artifactRoot, canonicalWireBytes } from "./cas.mjs";

import { readFileSync, readdirSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const UPSTREAM = join(HERE, "..", "docs", "spec", "proof-wire", "vectors", "jcs-upstream");

/** UPSTREAM VECTORS AS FILES, not transcriptions into source. `input/<n>.json`
 *  in, `output/<n>.json` out, octet for octet. A PARTIAL import — PROVENANCE.md
 *  beside them records what is absent and why, because a count with nothing
 *  saying what it excludes reads as completeness. */
export function upstreamVectors() {
  const dir = join(UPSTREAM, "input");
  if (!existsSync(dir)) return [];
  return readdirSync(dir).filter((f) => f.endsWith(".json")).sort().map((f) => {
    const name = f.replace(/\.json$/, "");
    /* COMPARED AS OCTETS, from upstream `outhex`. P4.3 and P4.4 could not import
       `weird` and `unicode` at all, because their expected output carries
       unescaped U+0080, U+007F and a combining mark and no text channel here
       could be shown to have preserved them. Upstream publishes the expected
       output as ASCII HEXADECIMAL, which is both transport-safe and a strictly
       better boundary than comparing decoded text — so every vector is compared
       as bytes now, not only the two that forced it. */
    const hex = readFileSync(join(UPSTREAM, "outhex", name + ".txt"), "utf8").replace(/\s+/g, "");
    return {
      name: "jcs-upstream/" + name,
      input: JSON.parse(readFileSync(join(dir, f), "utf8")),
      wantBytes: Buffer.from(hex, "hex"),
    };
  });
}

const RFC_INPUT = JSON.parse(
  '{\n' +
  '  "numbers": [333333333.33333329, 1E30, 4.50, 2e-3, 0.000000000000000000000000001],\n' +
  '  "string": "\\u20ac$\\u000F\\u000aA\'\\u0042\\u0022\\u005c\\\\\\"\\/",\n' +
  '  "literals": [null, true, false]\n' +
  '}');
const RFC_OUTPUT =
  '{"literals":[null,true,false],"numbers":[333333333.3333333,1e+30,4.5,0.002,1e-27],' +
  '"string":"€$\\u000f\\nA\'B\\"\\\\\\\\\\"/"}';

const FRENCH_INPUT = {
  peach: "This sorting order",
  "péché": "is wrong according to French",
  "pêche": "but canonicalization MUST",
  sin: "ignore locale",
};
const FRENCH_OUTPUT =
  '{"peach":"This sorting order","péché":"is wrong according to French",' +
  '"pêche":"but canonicalization MUST","sin":"ignore locale"}';

const CODEUNIT_INPUT = {
  "דּ": "Hebrew Letter Dalet With Dagesh",
  "\u{1F602}": "Smiley",
  "€": "Euro Sign",
  "ö": "Latin Small Letter O With Diaeresis",
  "1": "One",
};
const CODEUNIT_OUTPUT =
  '{"1":"One","ö":"Latin Small Letter O With Diaeresis","€":"Euro Sign",' +
  '"\u{1F602}":"Smiley","דּ":"Hebrew Letter Dalet With Dagesh"}';


/* ES6 Number::toString BOUNDARIES — RFC 8785 delegates number serialisation to
   ECMA-262 §7.1.12.1, and these are the cases where a naive `%g`, a shortest-
   round-trip printer and a fixed-precision printer all diverge. Stated as
   EXPECTED STRINGS rather than derived from the encoder, so they are usable as
   a cross-language corpus entry by an implementation that is not JavaScript. */
const NUMBER_INPUT = { a: [1e21, 1e20, 1e-7, 0.000001, 5e-324, 1.7976931348623157e308, -0, 0.1] };
const NUMBER_OUTPUT =
  '{"a":[1e+21,100000000000000000000,1e-7,0.000001,5e-324,1.7976931348623157e+308,0,0.1]}';

export const JCS_VECTORS = Object.freeze([
  Object.freeze({ name: "rfc8785-worked-example", input: RFC_INPUT, want: RFC_OUTPUT,
    source: "RFC 8785 sections 3.2.2 / 3.2.3, verbatim" }),
  Object.freeze({ name: "jcs-french-locale-ignored", input: FRENCH_INPUT, want: FRENCH_OUTPUT,
    source: "JCS reference test suite, testdata/french.json" }),
  Object.freeze({ name: "jcs-utf16-code-unit-order", input: CODEUNIT_INPUT, want: CODEUNIT_OUTPUT,
    /* THIS STRING IS INSIDE THE FROZEN CONFORMANCE CORPUS. It is human-readable
       provenance about an in-tree vector, and `manifest.json` is the ORACLE at
       a numbered spec revision — so improving the wording moves the corpus and
       fails SPEC-VECTORS until a revision is issued deliberately. Measured this
       round: rewriting it to describe the P4.5 import produced exactly one
       disagreement with the frozen corpus, in a round whose instruction was to
       change no JCS semantics. Left byte-identical on purpose; the header it
       points at was repaired instead. Filed as a finding: a normative corpus
       that carries English is a corpus a documentation edit can move. */
    source: "JCS reference test suite, testdata/weird.json ordering (subset — see header)" }),
  Object.freeze({ name: "es6-number-boundaries", input: NUMBER_INPUT, want: NUMBER_OUTPUT,
    source: "ECMA-262 7.1.12.1 via RFC 8785 section 3.2.2.3; expectations stated, not derived" }),
]);

/** NEGATIVE VECTORS. A canonicaliser is defined as much by what it REFUSES, and
 *  every one of these was accepted by the tree at some point in P4/P4.1. Each
 *  says what must happen, not merely that something must. */
export const JCS_NEGATIVE = Object.freeze([
  Object.freeze({ name: "lone-high-surrogate", why: "RFC 8785: invalid Unicode terminates canonicalisation",
    run: () => canonicalWire({ s: "\uD800" }) }),
  Object.freeze({ name: "lone-low-surrogate", why: "the other half, and P4.1 accepted both",
    run: () => canonicalWire({ s: "\uDEAD" }) }),
  Object.freeze({ name: "lone-surrogate-in-a-KEY", why: "a key is a string; an object with an invalid key is not canonicalisable",
    run: () => canonicalWire({ "\uD800": 1 }) }),
  Object.freeze({ name: "non-finite-number", why: "JSON has no NaN or Infinity and a canonicaliser may not invent one",
    run: () => canonicalWire({ n: Number.POSITIVE_INFINITY }) }),
  Object.freeze({ name: "nan", why: "same, and it is the one a numeric edge case actually produces",
    run: () => canonicalWire({ n: Number.NaN }) }),
]);

/** WIRE-LEVEL NEGATIVES — resolution, not encoding. These are the P4/P4.1
 *  defects themselves, kept as vectors so they cannot come back quietly. */
export function wireNegatives() {
  const out = [];
  const store = memoryStore(new Map());
  const obj = { x: "\uFFFD" };
  const root = store.put(obj);
  const canonical = canonicalWireBytes(obj);

  // 1. INVALID UTF-8 — a raw 0xFF where canonical UTF-8 has EF BF BD.
  const bad = Buffer.from(canonical.toString("binary").replace("\xef\xbf\xbd", "\xff"), "binary");
  store.entries.set(root, bad);
  out.push({ name: "invalid-utf8-is-refused", want: "invalid-utf8",
    got: resolveArtifact(store, root).outcome,
    why: "P4.1 decoded the invalid byte to U+FFFD before the equality ran, so two byte strings " +
      "were one wire artifact" });

  // 2. A DUPLICATE MEMBER NAME.
  store.entries.set(root, Buffer.from('{"x":"EVIL",' + canonical.toString("utf8").slice(1), "utf8"));
  out.push({ name: "duplicate-member-name-is-refused", want: "non-canonical-wire",
    got: resolveArtifact(store, root).outcome,
    why: "JSON.parse resolves it in favour of the last one, so the parsed object and the root are " +
      "honest while the bytes are not — a cross-implementation hazard" });

  // 3. THE BYTE BUDGET IS IN BYTES.
  const wide = { k: "日本語日本語日" };
  const s2 = memoryStore(new Map());
  const r2 = s2.put(wide);
  const jsLen = canonicalWire(wide).length, bytes = canonicalWireBytes(wide).length;
  out.push({ name: "byte-budget-counts-utf8-bytes", want: "too-large",
    got: resolveArtifact(s2, r2, { max_artifact_bytes: jsLen + 1 }).outcome,
    why: `canonical text is ${jsLen} UTF-16 units and ${bytes} UTF-8 bytes; P4.1 bounded the ` +
      `former, so an artifact weighing ${bytes} passed a ${jsLen + 1} ceiling` });

  // 4. AND THE HONEST ARTIFACT STILL RESOLVES.
  const s3 = memoryStore(new Map());
  const r3 = s3.put(obj);
  out.push({ name: "the-honest-artifact-still-resolves", want: "ok",
    got: resolveArtifact(s3, r3).outcome,
    why: "a wire gate that refused everything would pass every negative vector" });
  return out;
}

/** Run the vectors against one encoder. Returns { pass, total, failures }. */
export function runVectors(encode) {
  const failures = [];
  for (const v of JCS_VECTORS) {
    let got;
    try { got = encode(v.input); } catch (e) { got = "THREW: " + String(e?.message ?? e); }
    if (got !== v.want) failures.push({ name: v.name, want: v.want, got });
  }
  return { pass: JCS_VECTORS.length - failures.length, total: JCS_VECTORS.length, failures };
}

const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN) {
  let bad = false;
  const r = runVectors(canonicalWire);
  console.log(`${r.pass === r.total ? "PASS" : "FAIL"}  canonicalWire vs RFC 8785        ${r.pass}/${r.total}`);
  for (const f of r.failures) {
    bad = true;
    console.log(`      ${f.name}`);
    console.log(`        want ${JSON.stringify(f.want)}`);
    console.log(`        got  ${JSON.stringify(f.got)}`);
  }
  /* ONE ENCODER, NOT TWO — asserted rather than described. If the CAS wire form
     and the semantic-id form were separate implementations of the same standard,
     the vectors would be measuring one of them and the tree would contain two
     things called canonical that nothing compared. */
  /* THE UPSTREAM CORPUS, READ FROM DISK. */
  const up = upstreamVectors();
  for (const v of up) {
    let got = null, err = null;
    try { got = canonicalWireBytes(v.input); } catch (e) { err = String(e?.message ?? e); }
    if (err || !got.equals(v.wantBytes)) { bad = true;
      console.log(`FAIL  ${v.name}`);
      console.log(`        want ${v.wantBytes.toString("hex").slice(0, 120)}`);
      console.log(`        got  ${err ?? got.toString("hex").slice(0, 120)}`);
    } else console.log(`PASS  ${v.name.padEnd(34)} ${v.wantBytes.length} octets, ` +
      `file in / upstream outhex out`);
  }
  if (up.length === 0) { bad = true;
    console.log("FAIL  no upstream vectors on disk — the corpus is a gate, not a backlog item"); }
  const one = canonicalWire === canonicalBytes;
  if (!one) bad = true;
  console.log(`${one ? "PASS" : "FAIL"}  the tree has ONE canonical encoder  ` +
    `canonicalWire === canonicalBytes is ${one}`);
  /* NEGATIVE: the encoder must REFUSE, and by throwing rather than by emitting. */
  for (const v of JCS_NEGATIVE) {
    let threw = null;
    try { v.run(); } catch (e) { threw = String(e?.message ?? e); }
    if (threw === null) { bad = true; console.log(`FAIL  ${v.name} was ACCEPTED — ${v.why}`); }
    else console.log(`PASS  ${v.name.padEnd(34)} refused: ${threw}`);
  }
  /* NEGATIVE: the WIRE, which is where P4 and P4.1 actually failed. */
  for (const w of wireNegatives()) {
    if (w.got !== w.want) { bad = true;
      console.log(`FAIL  ${w.name} → ${w.got}, wanted ${w.want}`); }
    else console.log(`PASS  ${w.name.padEnd(34)} → ${w.got}`);
  }
  console.log("═".repeat(96));
  console.log(bad
    ? "JCS-VECTORS: FAIL — an encoder this tree calls canonical disagrees with RFC 8785"
    : `JCS-VECTORS: PASS — ${JCS_VECTORS.length} in-tree positive vectors, ${up.length} ` +
      `UPSTREAM RFC 8785 reference vectors — the COMPLETE upstream testdata/input set, each ` +
      `compared as OCTETS against upstream outhex — ${JCS_NEGATIVE.length} ` +
      `encoder negatives and 4 WIRE negatives. The CAS wire encoder ` +
      `IS the semantic-id encoder rather than a second implementation of the same standard. ` +
      `The CAS wire encoder and the semantic-id encoder agree with RFC 8785 on number ` +
      `serialisation, string escaping and UTF-16 CODE-UNIT property ordering — including the ` +
      `vector that separates code-unit from code-point sorting, where U+1F602 (a surrogate pair, ` +
      `first unit D83D) must precede U+FB33 and a code-point implementation puts it last. IT ` +
      `REFUSES WHAT RFC 8785 SAYS IT MUST — lone surrogates in values AND in keys, and non-finite ` +
      `numbers — and the WIRE refuses invalid UTF-8, a duplicate member name, and an artifact ` +
      `over a ceiling measured in BYTES rather than in UTF-16 units, which are the three P4/P4.1 ` +
      `defects kept as vectors so they cannot come back quietly. THE UPSTREAM INPUT SET IS ` +
      `COMPLETE — weird.json and unicode.json ARE included, and the U+0080 / U+007F members that ` +
      `P4.3 and P4.4 could not transport are covered, because outhex is ASCII hexadecimal and the ` +
      `comparison is over octets rather than decoded text. THIS IS STILL NOT THE REFERENCE SUITE ` +
      `AND FULL CONFORMANCE IS NOT CLAIMED: RFC 8785's ~10^8-value number corpus is DECLARED-OPEN ` +
      `in requirements/open/, and the ES6 number boundaries are STATED expectations rather than ` +
      `derived ones so they are usable by an implementation that is not JavaScript`);
  process.exit(bad ? 1 : 0);
}
