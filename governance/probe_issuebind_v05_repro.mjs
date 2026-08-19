/* ═══════════════════════════════════════════════════════════════════════════
   probe_issuebind_v05_repro.mjs — issuance authenticated the grant, not the
   request; and acceptance took both of its proofs from the caller.

   The draft authority (never committed, frozen below) recorded

       request_id -> grant_id

   and derived `request_id = H(intent_id | grant_id)`. Neither binds the
   program, the inputs, or the implementation requirement — so "was this
   issued?" was answered about a *grant*, while the thing being accepted was a
   *request*. Three consequences, all reproduced:

   I-1  SWAP THE INPUTS. Take an honest request with canonical_inputs.bias = 0,
        change only bias to 1000, keep request_id and grant_id. wasIssued says
        true, the derivation returns 1005, acceptance returns committable.
        The authority accepted request content it never issued.

   I-2  INJECT THROUGH THE OPTIONS BAG. `authorize(intent, over)` applied
        `...over` AFTER every authority-created field, so the caller could
        overwrite canonical_inputs on an authority-ISSUED request. Same 1005,
        with the authority's own stamp on it.

   I-3  OMIT THE AUTHORITY ENTIRELY. `acceptForeignResult(..., issuer = null)`
        defaulted issuance checking to OFF, and took `liveReader` as a
        parameter. So a wholly self-made request with a self-made grant was
        accepted with no issuer; and after the World moved fb@1 -> fb@2, a fake
        liveReader that simply replayed the old grant turned a refusal back
        into committable. Acceptance was a pure function whose caller supplied
        both proofs of authority.

   THE SHAPE OF THE REPAIR, because it is not "add a signature". A signature
   would authenticate the authority to itself while caller and authority are the
   same party. What was missing is binding: issuance now records
   `request_id -> request_sem_id = H(canonical request)`, recomputed at
   acceptance, so any change to any field is a different request. The options
   bag is gone and only `expected_implementation_id` may be requested. The
   returned request is owned and frozen through canonicalBytes. And acceptance
   is a METHOD ON THE AUTHORITY, closing over its own issuance table and its own
   live reader — neither is a parameter any more, because a caller that can pass
   the proof is not being checked by it.

   PAIRED, and it gates. Exit 0 requires each witness to still reproduce against
   the frozen draft AND to be confined against live.
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import {
  ProgramRegistry, deriveLocally, grantId, resolveGrants, canonicalBytes,
  DerivationAuthority, requestSemId,
} from "./derive_protocol.mjs";

const results = [];
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "CONFINED" : "BREACH  "}  ${id.padEnd(24)} ${note}`); };

const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const mkWorld = () => ({
  res: { fb: { value: 5, version: 1 } },
  read(r) { const e = this.res[r]; if (!e) throw new Error("no-such-resource: " + r); return { ...e }; },
  scope(q) { return "scope:" + q; },
  write(r, v) { this.res[r] = { value: v, version: (this.res[r]?.version ?? 0) + 1 }; },
});

/* ── THE DRAFT AUTHORITY, VERBATIM ────────────────────────────────────────
   request_id from (intent_id, grant_id); issuance table keyed on grant_id;
   an options bag applied last; acceptance a free function with a defaulted
   issuer and a caller-supplied reader. Do not repair anything here. */
const H = (s) => createHash("sha256").update(s).digest("hex");
class DraftIssuer {
  #issued = new Map();
  #reader;
  constructor(reader) { this.#reader = reader; Object.freeze(this); }
  authorize(intent, over = {}) {
    const g = resolveGrants(this.#reader, intent.requested_resources);
    const req = {
      request_id: "req-" + H("TRVM-REQUEST-v1|" + intent.intent_id + "|" + g.grant_id),
      program_sem_id: intent.program_sem_id,
      canonical_inputs: intent.canonical_inputs,
      read_grants: g.read_grants, grant_id: g.grant_id, ...over,   // <<< I-2 LIVES HERE
    };
    this.#issued.set(req.request_id, g.grant_id);                  // <<< I-1: binds the GRANT only
    return { ok: true, request: req };
  }
  wasIssued(request_id, grant_id) { return this.#issued.get(request_id) === grant_id; }
}
function draftAccept(registry, req, res, liveReader, issuer = null) {   // <<< I-3: both are parameters
  if (issuer && !issuer.wasIssued(req.request_id, req.grant_id))
    return { ok: false, reason: "grant-not-issued-by-this-authority" };
  const mine = deriveLocally(registry, req);
  if (!mine.ok) return mine;
  if (canonicalBytes(mine.result) !== canonicalBytes(res)) return { ok: false, reason: "foreign-result-divergence" };
  for (const [r, ver] of res.semantic_result.read_footprint.exact ?? []) {
    const cur = liveReader.read(r);
    if (cur?.version !== ver) return { ok: false, reason: "stale-read: " + r + " granted@" + ver + " live@" + cur?.version };
  }
  return { ok: true, committable: true };
}

const reg = new ProgramRegistry(); const PID = reg.bind(P);
const intent = { intent_id: "i-1", program_sem_id: PID, canonical_inputs: { bias: 0 },
  requested_resources: { exact: ["fb"], predicates: [] } };

/* ── I-1 against the draft: swap the inputs, keep the ids ─────────────────── */
{
  const world = mkWorld(); const iss = new DraftIssuer(world);
  const { request: req } = iss.authorize(intent);
  const forged = { ...req, canonical_inputs: { bias: 1000 } };
  const res = deriveLocally(reg, forged).result;
  const acc = draftAccept(reg, forged, res, world, iss);
  R("I-1 frozen-draft", !(iss.wasIssued(forged.request_id, forged.grant_id) && acc.ok),
    `bias 0 -> 1000 with request_id and grant_id untouched: wasIssued ${iss.wasIssued(forged.request_id, forged.grant_id)}, ` +
    `value ${res.semantic_result.value}, accept ok=${acc.ok} committable=${acc.committable} — the authority accepted ` +
    `request content it never issued, because issuance was keyed on the GRANT`);
}
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request: req } = auth.authorize(intent);
  const forged = { ...req, canonical_inputs: { bias: 1000 } };
  const res = deriveLocally(reg, forged).result;
  const acc = auth.accept(reg, forged, res);
  R("I-1 live", !acc.ok && acc.reason === "request-not-as-issued",
    `the same swap is refused: ${acc.reason}. Issuance records request_id -> ` +
    `requestSemId = H(canonical request), recomputed at acceptance, so any change to any field is a ` +
    `different request rather than the same one with different content`);
}

/* ── I-2: the options bag overwrote authority-created fields ──────────────── */
{
  const world = mkWorld(); const iss = new DraftIssuer(world);
  const { request } = iss.authorize(intent, { canonical_inputs: { bias: 1000 } });
  const res = deriveLocally(reg, request).result;
  const acc = draftAccept(reg, request, res, world, iss);
  R("I-2 frozen-draft", !(acc.ok && res.semantic_result.value === 1005),
    `authorize(intent, {canonical_inputs:{bias:1000}}) produced an AUTHORITY-ISSUED request evaluating ` +
    `to ${res.semantic_result.value}, accepted (committable ${acc.committable}) — \`...over\` was spread after every ` +
    `field the authority had just decided`);
}
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const bad = auth.authorize(intent, { canonical_inputs: { bias: 1000 } });
  const okImpl = auth.authorize(intent, { expected_implementation_id: "impl-c-derive-v0.5.0" });
  R("I-2 live", !bad.ok && /authorize-options-unknown/.test(bad.reason)
      && okImpl.ok && okImpl.request.expected_implementation_id === "impl-c-derive-v0.5.0",
    `${bad.reason} — the options bag is gone; exactly one field may be REQUESTED by a caller, and it is ` +
    `a requirement on the executor rather than authority content`);
}

/* ── I-3: acceptance took both of its proofs from the caller ──────────────── */
{
  const world = mkWorld();
  const g = { exact: { fb: { value: 5, version: 1 } }, predicates: {} };
  const self = { request_id: "req-self-made", program_sem_id: PID, canonical_inputs: { bias: 1000 },
    read_grants: g, grant_id: grantId(g) };
  const res = deriveLocally(reg, self).result;
  const noIssuer = draftAccept(reg, self, res, world);          // issuer omitted entirely
  const iss = new DraftIssuer(world);
  const { request: honest } = iss.authorize(intent);
  const hres = deriveLocally(reg, honest).result;
  world.write("fb", 9);
  const real = draftAccept(reg, honest, hres, world, iss);
  const fake = draftAccept(reg, honest, hres,
    { read: () => ({ value: 5, version: 1 }), scope: (q) => "scope:" + q }, iss);
  R("I-3 frozen-draft", !(noIssuer.ok && !real.ok && fake.ok),
    `a wholly self-made request accepted with the issuer OMITTED (ok=${noIssuer.ok}, value ${res.semantic_result.value}); ` +
    `and after fb@1->fb@2 the real reader refuses (${real.reason}) while a fake reader replaying the ` +
    `grant returns committable=${fake.committable}. Acceptance was a pure function whose caller ` +
    `supplied both proofs of authority`);
}
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const g = { exact: { fb: { value: 5, version: 1 } }, predicates: {} };
  const self = { request_id: "req-self-made", program_sem_id: PID, canonical_inputs: { bias: 1000 },
    read_grants: g, grant_id: grantId(g) };
  const res = deriveLocally(reg, self).result;
  const selfMade = auth.accept(reg, self, res);
  const { request: honest } = auth.authorize(intent);
  const hres = deriveLocally(reg, honest).result;
  const before = auth.accept(reg, honest, hres);
  world.write("fb", 9);
  const after = auth.accept(reg, honest, hres);
  R("I-3 live", !selfMade.ok && selfMade.reason === "grant-not-issued-by-this-authority"
      && before.ok && before.fresh_at_check === true && before.committable === undefined
      && !after.ok && /^stale-read: fb granted@1 live@2/.test(after.reason),
    `self-made request -> ${selfMade.reason}; honest request -> ok with fresh_at_check ` +
    `${before.fresh_at_check} and NO committable field; after fb moves -> ${after.reason}. ` +
    `accept() is a method: the issuance table and the live reader are closed over, not passed in, ` +
    `and there is no argument a caller can supply to switch either off`);
}

/* ── and the request the authority hands back is owned and frozen ─────────── */
{
  const world = mkWorld(); const auth = new DerivationAuthority(world);
  const { request } = auth.authorize(intent);
  let froze = false;
  try { request.canonical_inputs.bias = 1000; } catch { froze = true; }
  const acc = auth.accept(reg, request, deriveLocally(reg, request).result);
  R("issued-request-is-owned", froze && request.canonical_inputs.bias === 0 && acc.ok
      && requestSemId(request) === requestSemId(JSON.parse(canonicalBytes(request))),
    `mutating the issued request throws and it still reads bias ${request.canonical_inputs.bias}. ` +
    `Defence in depth rather than the boundary: the binding is what refuses a modified request, and ` +
    `the freeze is what stops one being modified by accident in the authority's own process`);
}

console.log("=".repeat(100));
const frozenHeld = results.filter((r) => r.id.includes("frozen") && r.held);
const liveBreached = results.filter((r) => !r.id.includes("frozen") && !r.held);
console.log(
  `ISSUE-BIND v0.5 REPRO: ${results.filter((r) => r.id.includes("frozen") && !r.held).length}/3 reproduce ` +
  `against the frozen draft · ${results.filter((r) => !r.id.includes("frozen") && r.held).length}/4 confined against live` +
  (frozenHeld.length ? ` — VACUOUS: ${frozenHeld.map((r) => r.id).join(", ")}` : "") +
  (liveBreached.length ? ` — REGRESSION: ${liveBreached.map((r) => r.id).join(", ")}` : ""));
process.exit(frozenHeld.length + liveBreached.length ? 1 : 0);
