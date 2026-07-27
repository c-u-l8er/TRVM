/* probe6.mjs -- C.5.2 verifier half: the JS side receives PYTHON's bytes.
 *
 * probe3 was JS-produced bytes read by Python. This is the return leg, and it
 * is the one that actually costs something: the two implementations share no
 * code, no serializer and no hash routine, and the wire is canonical, so
 * agreement has to be exact rather than merely semantic.
 *
 * Nothing here compares against the committed vectors. The JS verifier is
 * given Python's bytes and asked to establish every claim on them from the
 * semantic artifact alone -- which is the whole contract. It then re-serialises
 * what it derived and requires the SAME bytes back, which is the part that
 * would catch a divergence the ids happened to survive.
 *
 * Run:  node probe6.mjs        (after PYTHONDONTWRITEBYTECODE=1 python3 probe6.py)
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const V2 = await import(process.env.WRL_V2 ||
  "/home/travis/ProjectAmp2/WRL/relation-v2.js");

let passed = 0, failed = 0;
const ok = (name, cond, detail = "") => {
  if (cond) { passed++; console.log(`  ok   ${name.padEnd(46)} ${detail}`); }
  else { failed++; console.log(`  FAIL ${name.padEnd(46)} ${detail}`); }
};

const doc = JSON.parse(readFileSync(join(HERE, "python-wire.json"), "utf8"));
console.log(`producer: ${doc.producer}\n`);

for (const { name, wire } of doc.wires) {
  let adm;
  try {
    adm = await V2.verifyRuntimeProjection(wire);
  } catch (e) {
    ok(`${name}/verifies`, false, `${e.code || ""} ${e.message}`);
    continue;
  }
  ok(`${name}/verifies`, true, adm.semantic_world_id.slice(0, 28) + "...");

  /* The bytes Python sent are re-derived here and must render identically.
   * An id can agree while the record does not; this is the check that notices. */
  const again = V2.serializeRuntimeProjection(adm);
  ok(`${name}/re-renders-identically`, again === wire,
     again === wire ? "" : `${again.length} vs ${wire.length} bytes`);

  /* The exactness case: this world's rotor lane is 2^63-1, and it has to have
   * survived Python -> JSON -> JS as itself. `JSON.parse` would have rounded
   * it here, so this assertion is the reason C.4.1 exists. */
  if (name === "bigint-rotor") {
    const sp = adm.semantic_artifact.objects.find((o) => o.role === "Spinner");
    const lane = sp.static_config.rotor[0];
    ok("bigint-rotor/lane-is-exact",
       BigInt(lane) === 9223372036854775807n,
       `${lane} (${typeof lane})`);
    ok("bigint-rotor/an-ordinary-reader-would-have-lost-it",
       JSON.parse(`{"v":9223372036854775807}`).v === 9223372036854776000,
       "JSON.parse rounds it");
  }
}

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
