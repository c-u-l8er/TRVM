/* ═══════════════════════════════════════════════════════════════════════════
   evidence.mjs — v0.1.0 — THE BYTE BOUNDARY, BEFORE ANYTHING IS A VALUE
   law:proof.evidence-bytes-unambiguous@1

   P4.7.6 CLOSED THE EQUIVOCATION ONE BOUNDARY TOO LATE. It said, correctly,
   that an authenticated evidence artifact must have exactly one reading, and it
   enforced that over PARSED OBJECTS: collections keyed by identity are checked
   for uniqueness before they are indexed, and every shape is closed. But every
   reader still began

       JSON.parse(readFileSync(path, "utf8"))

   and `JSON.parse` resolves duplicate object members by keeping the LAST one.
   By the time `shapeProblems()` and `uniqueProblems()` see a value, the second
   reading is gone.

   REPRODUCED against the shipped PINNED run, by editing the raw bytes:

       "status": "REVEALED",
       "status": "PINNED",

   A first-occurrence reader sees REVEALED. Node sees PINNED. `BLIND-RUN: PASS
   — … PINNED …`. The same in a reachable transition receipt. The same in an
   archived observation document's `implementation`, which is how a measurement
   is attributed — so a foreign implementation could emit an observation whose
   bytes name two implementations and this measurement authority would accept
   one particular reading of them, while a conforming strict reader refused the
   document outright or read the other name. That is P4.1's duplicate wire
   member, in the artifacts that were invented to hold P4.1's repair.

   SO THE ORDER IS:

       RAW BYTES  →  strict evidence boundary  →  value  →  shape and semantics

   and never

       RAW BYTES  →  JSON.parse  →  shape           (ambiguity destroyed here)

   THIS READER IS THE INSTRUMENT'S OWN, AND DELIBERATELY NOT THE SUBJECT'S.
   `governance/cas.mjs` already has a canonical encoder that makes duplicate
   rejection a consequence of canonical equality — and it is the PROTOCOL UNDER
   TEST, mutable from the governance side and part of the reference subject's
   frozen package. An instrument may not decide what its evidence says with the
   encoder belonging to the thing it is measuring; that is the same argument
   `run_state.mjs` makes for rendering the run preimage as lines rather than as
   JSON. This file imports node builtins and nothing else, so the scorer — which
   is required to know eight operators and no TRVM — can use it too.

   IT PARSES RATHER THAN VALIDATING-THEN-PARSING, ON PURPOSE. Scanning for
   duplicates and then handing the bytes to `JSON.parse` is TWO implementations
   of what the bytes mean, and two implementations of one question is the defect
   this whole line of work keeps finding. One parser both refuses and constructs,
   so an accepted artifact has exactly one reading by construction.

   THE ONE PROPERTY THAT MAKES THAT SAFE, ASSERTED BY `--selftest`: for every
   input this reader ACCEPTS, `JSON.parse` of the same bytes produces a deeply
   equal value. It is allowed to be STRICTER than JSON. It is never allowed to
   be DIFFERENT.

   WHAT IT REFUSES BEYOND JSON, AND WHY EACH ONE IS AN EQUIVOCATION:

     * duplicate object member names — two readers, two values. The headline.
     * unpaired surrogates — `"\uD800"` is a JSON string Node accepts and Go's
       encoding/json rewrites to U+FFFD, so the same authenticated bytes carry
       different characters in two conforming implementations. This one is worth
       naming ahead of the Go run: refused here, it can never surface as a
       spurious interoperability finding there.
     * invalid UTF-8, and a byte-order mark — bytes that are not a text.
     * anything after the value — a second document hiding behind the first.

   Everything else is ordinary RFC 8259: no comments, no trailing commas, no
   `NaN`/`Infinity`, no leading `+` or `0`, no raw control characters in strings.
   ═══════════════════════════════════════════════════════════════════════════ */
import { readFileSync } from "node:fs";

/** Evidence is small by construction — a run record, a receipt, a RESULT, an
 *  observation document, a challenge. The ceiling exists so a bound is applied
 *  to BYTES before any of them are interpreted, which is the order P4.2 settled
 *  for the wire: byte-like → copy → length bound → fatal decode → parse. */
export const EVIDENCE_MAX_BYTES = 8 * 1024 * 1024;
export const EVIDENCE_MAX_DEPTH = 64;

/** Refusal is a distinct condition, not a parse error: the artifact was read and
 *  found to have no single reading. */
export class EvidenceRefused extends Error {
  constructor(message) { super(message); this.name = "EvidenceRefused"; }
}

const WS = new Set([0x20, 0x09, 0x0a, 0x0d]);
const HEX = /^[0-9a-fA-F]{4}$/;

/** THE STRICT READER. Returns the value, or throws `EvidenceRefused` naming both
 *  what was wrong and where. `what` is the artifact's name, because a refusal a
 *  reviewer cannot locate is a refusal they will work around. */
export function parseEvidence(bytes, what = "evidence") {
  if (!Buffer.isBuffer(bytes) && !(bytes instanceof Uint8Array))
    throw new EvidenceRefused(`${what} was handed to the evidence reader as a ` +
      `${typeof bytes} — the boundary is over BYTES, and a string has already been decoded by ` +
      `someone else's rules`);
  /* A COPY, so nothing a caller retains can change under the parse. */
  const buf = Buffer.from(bytes);
  if (buf.length === 0) throw new EvidenceRefused(`${what} is empty`);
  if (buf.length > EVIDENCE_MAX_BYTES)
    throw new EvidenceRefused(`${what} is ${buf.length} bytes and the evidence ceiling is ` +
      `${EVIDENCE_MAX_BYTES} — a bound on bytes is applied before they are interpreted`);
  if (buf[0] === 0xef && buf[1] === 0xbb && buf[2] === 0xbf)
    throw new EvidenceRefused(`${what} begins with a UTF-8 byte-order mark, which is not JSON and ` +
      `which some readers strip and others do not`);

  let text;
  try { text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(buf); }
  catch {
    throw new EvidenceRefused(`${what} is not valid UTF-8 — a replacement character substituted by ` +
      `a lenient decoder is a character the producer never wrote`);
  }

  let i = 0;
  const at = (p) => {
    const line = text.slice(0, p).split("\n").length;
    const col = p - (text.lastIndexOf("\n", p - 1) + 1) + 1;
    return `line ${line} column ${col}`;
  };
  const refuse = (msg, p = i) => { throw new EvidenceRefused(`${what}: ${msg} (${at(p)})`); };
  const ws = () => { while (i < text.length && WS.has(text.charCodeAt(i))) i += 1; };
  const lit = (s, v) => {
    if (text.startsWith(s, i)) { i += s.length; return { v }; }
    return null;
  };

  function parseString() {
    const start = i;
    i += 1; /* the opening quote */
    let out = "";
    for (;;) {
      if (i >= text.length) refuse("a string is never closed", start);
      const c = text.charCodeAt(i);
      if (c === 0x22) { i += 1; return out; }
      if (c === 0x5c) {
        i += 1;
        const e = text[i];
        if (e === undefined) refuse("a string ends inside an escape", start);
        if (e === "u") {
          const hex = text.slice(i + 1, i + 5);
          if (!HEX.test(hex)) refuse(`\\u must be followed by four hex digits, and here it is ` +
            `${JSON.stringify(hex)}`);
          const cp = parseInt(hex, 16);
          i += 5;
          if (cp >= 0xd800 && cp <= 0xdbff) {
            /* A HIGH SURROGATE MUST BE FOLLOWED BY ITS LOW HALF, IN THIS TEXT.
               Node keeps a lone surrogate; Go's encoding/json substitutes
               U+FFFD. Same authenticated bytes, different characters. */
            const lo = text.slice(i, i + 2) === "\\u" ? text.slice(i + 2, i + 6) : null;
            const loCp = lo && HEX.test(lo) ? parseInt(lo, 16) : NaN;
            if (!(loCp >= 0xdc00 && loCp <= 0xdfff))
              refuse(`an unpaired high surrogate \\u${hex} — Node keeps it and other conforming ` +
                `readers replace it with U+FFFD, so these bytes name two different strings`);
            i += 6;
            out += String.fromCharCode(cp, loCp);
            continue;
          }
          if (cp >= 0xdc00 && cp <= 0xdfff)
            refuse(`an unpaired low surrogate \\u${hex} — see above; it is not a character`);
          out += String.fromCharCode(cp);
          continue;
        }
        const simple = { '"': '"', "\\": "\\", "/": "/", b: "\b", f: "\f", n: "\n", r: "\r", t: "\t" };
        if (!(e in simple)) refuse(`\\${e} is not a JSON escape`);
        out += simple[e];
        i += 1;
        continue;
      }
      if (c < 0x20) refuse(`a raw control character U+${c.toString(16).padStart(4, "0")} inside a ` +
        `string — JSON requires it escaped, and readers that accept it disagree about what it is`);
      /* Lone surrogates can also arrive UNESCAPED only via ill-formed UTF-8,
         which the fatal decoder above has already refused. */
      out += text[i];
      i += 1;
    }
  }

  function parseNumber() {
    const start = i;
    if (text[i] === "-") i += 1;
    if (text[i] === "0") i += 1;
    else if (text[i] >= "1" && text[i] <= "9") { while (text[i] >= "0" && text[i] <= "9") i += 1; }
    else refuse(`${JSON.stringify(text.slice(start, start + 8))} is not a number`, start);
    if (text[i] === ".") {
      i += 1;
      if (!(text[i] >= "0" && text[i] <= "9")) refuse("a fraction with no digits", start);
      while (text[i] >= "0" && text[i] <= "9") i += 1;
    }
    if (text[i] === "e" || text[i] === "E") {
      i += 1;
      if (text[i] === "+" || text[i] === "-") i += 1;
      if (!(text[i] >= "0" && text[i] <= "9")) refuse("an exponent with no digits", start);
      while (text[i] >= "0" && text[i] <= "9") i += 1;
    }
    const raw = text.slice(start, i);
    const n = Number(raw);
    if (!Number.isFinite(n))
      refuse(`${raw} is outside the range this reader will carry — an evidence number that becomes ` +
        `Infinity has no single value`, start);
    return n;
  }

  function parseValue(depth) {
    if (depth > EVIDENCE_MAX_DEPTH)
      refuse(`nesting deeper than ${EVIDENCE_MAX_DEPTH} — evidence is a record, not a structure`);
    if (i >= text.length) refuse("the document ends where a value was expected");
    const c = text[i];
    if (c === "{") {
      i += 1;
      const obj = {};
      const seen = new Map();
      ws();
      if (text[i] === "}") { i += 1; return obj; }
      for (;;) {
        ws();
        if (text[i] !== '"') refuse("an object member name must be a string");
        const keyAt = i;
        const key = parseString();
        if (seen.has(key))
          refuse(`the member ${JSON.stringify(key)} appears TWICE in one object — it was already ` +
            `given at ${at(seen.get(key))}. A reader resolving duplicates by FIRST occurrence and ` +
            `one resolving by LAST read two different artifacts out of these authenticated bytes, ` +
            `which is the hazard P4.1 removed from the wire and P4.7.6 removed from parsed ` +
            `collections. An artifact with two readings is refused before anything is checked ` +
            `about it`, keyAt);
        seen.set(key, keyAt);
        ws();
        if (text[i] !== ":") refuse(`the member ${JSON.stringify(key)} has no ":"`);
        i += 1;
        ws();
        const v = parseValue(depth + 1);
        /* DefineOwnProperty, exactly as JSON.parse does it, so `__proto__` is an
           ordinary own member here and this reader and Node agree about it. */
        Object.defineProperty(obj, key,
          { value: v, writable: true, enumerable: true, configurable: true });
        ws();
        if (text[i] === ",") { i += 1; continue; }
        if (text[i] === "}") { i += 1; return obj; }
        refuse(`expected "," or "}" after the member ${JSON.stringify(key)}`);
      }
    }
    if (c === "[") {
      i += 1;
      const arr = [];
      ws();
      if (text[i] === "]") { i += 1; return arr; }
      for (;;) {
        ws();
        arr.push(parseValue(depth + 1));
        ws();
        if (text[i] === ",") { i += 1; continue; }
        if (text[i] === "]") { i += 1; return arr; }
        refuse(`expected "," or "]" in an array`);
      }
    }
    if (c === '"') return parseString();
    const t = lit("true", true) ?? lit("false", false) ?? lit("null", null);
    if (t) return t.v;
    if (c === "-" || (c >= "0" && c <= "9")) return parseNumber();
    refuse(`${JSON.stringify(text.slice(i, i + 12))} is not a JSON value`);
    return undefined; /* unreachable; `refuse` throws */
  }

  ws();
  const value = parseValue(0);
  ws();
  if (i !== text.length)
    refuse(`${text.length - i} byte(s) follow the document — a file holding two documents has two ` +
      `readings, and readers disagree about which one it is`);
  return value;
}

/** Read a file across the byte boundary. */
export function readEvidence(path, what = path) {
  let bytes;
  try { bytes = readFileSync(path); }
  catch (e) { throw new EvidenceRefused(`${what} could not be read: ${e.code ?? e.message}`); }
  return parseEvidence(bytes, what);
}

/** The same, as a value rather than an exception, for the many callers that
 *  accumulate problems instead of throwing. */
export function tryReadEvidence(path, what = path) {
  try { return { value: readEvidence(path, what), refused: null }; }
  catch (e) {
    if (e instanceof EvidenceRefused) return { value: null, refused: e.message };
    throw e;
  }
}
export function tryParseEvidence(bytes, what = "evidence") {
  try { return { value: parseEvidence(bytes, what), refused: null }; }
  catch (e) {
    if (e instanceof EvidenceRefused) return { value: null, refused: e.message };
    throw e;
  }
}

/* ── THE READER'S OWN FALSIFIER ───────────────────────────────────────────—
   Two claims, and the second is the one that matters. ACCEPT vectors must parse
   AND must agree with `JSON.parse` — a reader that is stricter than JSON is
   doing its job, and a reader that reads accepted bytes DIFFERENTLY from every
   other implementation has replaced one equivocation with a worse one. REFUSE
   vectors must be refused, and the corpus records which of them `JSON.parse`
   accepts, because those are exactly the ambiguities this file exists for. */
const B = (s) => Buffer.from(s, "utf8");
export const VECTORS = Object.freeze([
  ["accept", "an object", B(`{"a":1,"b":[true,false,null]}`)],
  ["accept", "nesting and escapes", B(`{"a":{"b":["\\u00e9\\n\\t\\"","\\ud83d\\ude00"]}}`)],
  ["accept", "numbers", B(`[0,-0,1,1.5,1e3,-1.5E-3,123456789012345]`)],
  ["accept", "an empty object and array", B(`{"a":{},"b":[]}`)],
  ["accept", "whitespace everywhere", B(` {\n "a" :\t1 ,\r\n "b" : [ 2 ] }\n`)],
  ["accept", "a bare string document", B(`"just a string"`)],
  ["accept", "a solidus escape", B(`{"a":"\\/"}`)],
  ["accept", "a member named __proto__", B(`{"__proto__":1,"a":2}`)],
  ["accept", "non-ASCII UTF-8 in the raw", B(`{"k":"café 日本語"}`)],
  /* A RAW ASTRAL CHARACTER IS TWO UTF-16 UNITS AND THIS READER WALKS UNITS. The
     fatal decoder guarantees both halves arrive in order, so they reform — but
     "it must reform" is exactly the kind of claim that is reasoned and not
     measured until it is a vector. */
  ["accept", "a raw astral character", B(`{"k":"a😀b","j":"𝄞"}`)],
  /* THE ESCAPE, NOT THE BYTE — and getting that wrong once while WRITING this
     vector produced a literal NUL in this file, which is exactly the defect the
     grid's NUL law exists for and which this round found sitting in the scorer. */
  ["accept", "an ESCAPED NUL, which is a legal JSON string", B(`{"k":"\\u0000ABSENT"}`)],
  ["accept", "a raw DEL and other non-control non-ASCII", B(`{"k":"a\u007fb"}`)],
  ["accept", "a real run-shaped record", B(`{"type":"T","status":"PINNED","adapters":[{"i":"js"}]}`)],

  ["refuse", "DUPLICATE member names", B(`{"status":"REVEALED","status":"PINNED"}`), "JSON.parse ACCEPTS"],
  ["refuse", "duplicate members, nested", B(`{"a":{"x":1,"x":2}}`), "JSON.parse ACCEPTS"],
  ["refuse", "duplicate members, three deep in an array", B(`{"a":[{"i":"evil","i":"good"}]}`),
    "JSON.parse ACCEPTS"],
  ["refuse", "an unpaired high surrogate", B(`{"a":"\\ud800"}`), "JSON.parse ACCEPTS"],
  ["refuse", "an unpaired low surrogate", B(`{"a":"\\udc00x"}`), "JSON.parse ACCEPTS"],
  ["refuse", "a high surrogate followed by a plain escape", B(`{"a":"\\ud83d\\n"}`), "JSON.parse ACCEPTS"],
  ["refuse", "invalid UTF-8", Buffer.from([0x7b, 0x22, 0x61, 0x22, 0x3a, 0x22, 0xff, 0x22, 0x7d])],
  ["refuse", "a truncated UTF-8 sequence", Buffer.from([0x22, 0xe6, 0x97, 0x22])],
  ["refuse", "a byte-order mark", Buffer.concat([Buffer.from([0xef, 0xbb, 0xbf]), B(`{"a":1}`)])],
  ["refuse", "a raw NUL inside a string", Buffer.from([0x22, 0x00, 0x22])],
  ["refuse", "a raw newline inside a string", B(`"a\nb"`)],
  ["refuse", "trailing content", B(`{"a":1} {"a":2}`)],
  ["refuse", "trailing content that is not JSON", B(`{"a":1}garbage`)],
  ["refuse", "a trailing comma in an object", B(`{"a":1,}`)],
  ["refuse", "a trailing comma in an array", B(`[1,2,]`)],
  ["refuse", "a comment", B(`{"a":1 /* hi */}`)],
  ["refuse", "a single-quoted string", B(`{'a':1}`)],
  ["refuse", "an unquoted member name", B(`{a:1}`)],
  ["refuse", "NaN", B(`{"a":NaN}`)],
  ["refuse", "Infinity", B(`{"a":Infinity}`)],
  ["refuse", "a leading plus", B(`{"a":+1}`)],
  ["refuse", "a leading zero", B(`{"a":01}`)],
  ["refuse", "a bare fraction", B(`{"a":.5}`)],
  ["refuse", "a hex number", B(`{"a":0x10}`)],
  ["refuse", "an unterminated object", B(`{"a":1`)],
  ["refuse", "an unterminated string", B(`{"a":"x}`)],
  ["refuse", "an empty document", B(``)],
  ["refuse", "whitespace only", B(`   \n`)],
  ["refuse", "a string handed in instead of bytes", `{"a":1}`],
  ["refuse", "nesting past the ceiling", B("[".repeat(80) + "]".repeat(80))],
]);

const deepEqual = (a, b) => {
  if (a === b) return true;
  if (typeof a !== typeof b || a === null || b === null || typeof a !== "object") return false;
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  const ka = Object.keys(a), kb = Object.keys(b);
  if (ka.length !== kb.length) return false;
  return ka.every((k) => kb.includes(k) && deepEqual(a[k], b[k]));
};

/** Returns `{ problems, accepted, refused, alsoRefusedByJson }`. */
export function selftest() {
  const problems = [];
  let accepted = 0, refused = 0, jsonAccepts = 0;
  for (const [want, name, bytes, note] of VECTORS) {
    const r = tryParseEvidence(bytes, name);
    if (want === "accept") {
      if (r.refused) { problems.push(`${name}: REFUSED and should be accepted — ${r.refused}`); continue; }
      accepted += 1;
      /* THE PROPERTY: stricter than JSON, never different from it. */
      let node;
      try { node = JSON.parse(Buffer.from(bytes).toString("utf8")); }
      catch (e) { problems.push(`${name}: this reader accepted bytes JSON.parse rejects (${e.message})`); continue; }
      if (!deepEqual(r.value, node))
        problems.push(`${name}: ACCEPTED, and reads DIFFERENTLY from JSON.parse — ` +
          `${JSON.stringify(r.value)?.slice(0, 60)} vs ${JSON.stringify(node)?.slice(0, 60)}. A ` +
          `reader that is stricter than JSON is doing its job; one that disagrees with JSON about ` +
          `what it accepted has replaced one equivocation with a worse one`);
      continue;
    }
    if (!r.refused) { problems.push(`${name}: ACCEPTED and must be refused`); continue; }
    refused += 1;
    if (note === "JSON.parse ACCEPTS") {
      jsonAccepts += 1;
      let ok = true;
      try { JSON.parse(Buffer.from(bytes).toString("utf8")); } catch { ok = false; }
      if (!ok)
        problems.push(`${name}: declared as something JSON.parse accepts, and JSON.parse rejects ` +
          `it — the corpus is describing a hazard that is not there`);
    }
  }
  return { problems, accepted, refused, jsonAccepts };
}

const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN && process.argv.includes("--selftest")) {
  const { problems, accepted, refused, jsonAccepts } = selftest();
  if (problems.length) {
    console.log(`EVIDENCE-READER: FAIL — ${problems.length} problem(s):`);
    for (const p of problems) console.log(`  ${p}`);
    process.exit(1);
  }
  console.log(`EVIDENCE-READER: PASS — ${accepted} accepted and ${refused} refused over ` +
    `${VECTORS.length} vectors. Every ACCEPTED vector reads deeply-equal to JSON.parse, so this ` +
    `reader is STRICTER than JSON and never DIFFERENT from it; ${jsonAccepts} of the refusals are ` +
    `documents JSON.parse accepts — duplicate member names and unpaired surrogates — and those are ` +
    `the ones the boundary exists for.`);
  process.exit(0);
}
