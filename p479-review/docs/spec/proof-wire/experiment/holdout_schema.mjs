/* ═══════════════════════════════════════════════════════════════════════════
   holdout_schema.mjs — v0.1.0 — THE BOUNDARY IS EXECUTED, NOT DESCRIBED
   law:proof.observation-boundary-enforced@1

   P4.6 published `holdout-observation-v1.schema.json` and never ran it.
   REPRODUCED: adding `SMUGGLED_TOP_LEVEL` to the envelope, an unknown member to
   an observation, and an unknown member to a node record — all three forbidden
   by `additionalProperties: false` — left the document ACCEPTED and the result
   an unchanged 8/8/3. A schema that documents a boundary the scorer does not
   execute is prose, and this experiment has a law about prose.

   So this is a validator for the SUBSET of JSON Schema those two documents use,
   written here rather than imported, because the instrument must not acquire a
   dependency the clean-room implementer cannot audit in an afternoon:

       type · required · properties · additionalProperties:false
       propertyNames{pattern|enum} · pattern · minLength · enum · const
       minimum · items · uniqueItems · $ref into $defs

   AND ONE KEYWORD THAT IS NOT JSON SCHEMA. `x-sorted: true` requires an array to
   be in non-decreasing order. `refusal_set` is compared for EXACT SET EQUALITY
   by byte comparison of a sorted array, so sortedness is not cosmetic — it is
   what makes byte equality and set equality the same operation. Vanilla JSON
   Schema cannot say it, so it is said here, named as an extension rather than
   smuggled in as though it were standard.

   IT IS A VALIDATOR AND NOT A PARSER. It reports EVERY violation with a path,
   because "the document is invalid" is a verdict and this experiment wants a
   diagnosis.
   ═══════════════════════════════════════════════════════════════════════════ */

const typeOf = (v) => v === null ? "null" : Array.isArray(v) ? "array"
  : Number.isInteger(v) ? "integer" : typeof v === "number" ? "number" : typeof v;

/** JSON Schema `type: "number"` admits integers; `"integer"` does not admit
 *  fractions. Everything else is exact. */
const typeOk = (v, t) => t === "number" ? (typeOf(v) === "integer" || typeOf(v) === "number")
  : typeOf(v) === t;

export function validate(doc, schema, { root = schema, path = "$", out = [] } = {}) {
  const fail = (msg) => out.push(`${path}: ${msg}`);
  if (!schema || typeof schema !== "object") return out;

  if (schema.$ref) {
    const m = /^#\/\$defs\/(.+)$/.exec(schema.$ref);
    if (!m || !root.$defs?.[m[1]]) { fail(`unresolvable $ref ${schema.$ref}`); return out; }
    return validate(doc, root.$defs[m[1]], { root, path, out });
  }
  if (schema.const !== undefined && doc !== schema.const)
    fail(`must be ${JSON.stringify(schema.const)}, got ${JSON.stringify(doc)}`);
  if (schema.enum && !schema.enum.some((e) => e === doc))
    fail(`must be one of ${JSON.stringify(schema.enum)}, got ${JSON.stringify(doc)}`);
  if (schema.type && !typeOk(doc, schema.type)) {
    fail(`must be ${schema.type}, got ${typeOf(doc)}`);
    return out;                                   // no point checking members
  }
  if (typeof doc === "string") {
    if (schema.pattern && !new RegExp(schema.pattern).test(doc))
      fail(`does not match ${schema.pattern}: ${JSON.stringify(doc.slice(0, 48))}`);
    if (schema.minLength !== undefined && doc.length < schema.minLength)
      fail(`shorter than minLength ${schema.minLength}`);
  }
  if (typeof doc === "number" && schema.minimum !== undefined && doc < schema.minimum)
    fail(`below minimum ${schema.minimum}`);

  if (Array.isArray(doc)) {
    if (schema.items) doc.forEach((v, i) => validate(v, schema.items, { root, path: `${path}[${i}]`, out }));
    if (schema.uniqueItems) {
      const seen = new Set();
      for (const v of doc) {
        const k = JSON.stringify(v);
        if (seen.has(k)) { fail(`duplicate item ${k}`); break; }
        seen.add(k);
      }
    }
    /* THE EXTENSION, AND WHY IT IS LOAD-BEARING. */
    if (schema["x-sorted"]) {
      for (let i = 1; i < doc.length; i += 1)
        if (String(doc[i - 1]) > String(doc[i])) {
          fail(`must be SORTED — ${JSON.stringify(doc[i - 1])} precedes ${JSON.stringify(doc[i])}. ` +
            `A refusal set is compared for exact SET equality by comparing sorted arrays, so an ` +
            `unsorted one is not a differently-presented set, it is a set that will compare unequal ` +
            `to itself`);
          break;
        }
    }
  }

  if (doc !== null && typeof doc === "object" && !Array.isArray(doc)) {
    for (const k of schema.required ?? [])
      if (!(k in doc)) fail(`missing required member ${JSON.stringify(k)}`);
    const props = schema.properties ?? {};
    for (const [k, v] of Object.entries(doc)) {
      const child = `${path}.${k}`;
      if (schema.propertyNames?.pattern && !new RegExp(schema.propertyNames.pattern).test(k))
        fail(`member name ${JSON.stringify(k)} does not match ${schema.propertyNames.pattern}`);
      if (schema.propertyNames?.enum && !schema.propertyNames.enum.includes(k))
        fail(`member name ${JSON.stringify(k)} is not one of ` +
          `${JSON.stringify(schema.propertyNames.enum)}`);
      if (k in props) validate(v, props[k], { root, path: child, out });
      else if (schema.additionalProperties === false)
        fail(`member ${JSON.stringify(k)} is not permitted — additionalProperties is false, and an ` +
          `unknown member is where an implementation smuggles a claim the boundary never agreed to`);
      else if (schema.additionalProperties && typeof schema.additionalProperties === "object")
        validate(v, schema.additionalProperties, { root, path: child, out });
    }
  }
  return out;
}

export const validateOrProblems = (doc, schema, label) =>
  validate(doc, schema).map((p) => `${label} ${p}`);
