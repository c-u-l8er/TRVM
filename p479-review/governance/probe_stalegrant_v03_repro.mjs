/* ═══════════════════════════════════════════════════════════════════════════
   probe_stalegrant_v03_repro.mjs — every check passed and the result was not
   committable.

   This one is not a regression witness. It is a GAP witness: v0.2.0 had no
   freshness check at all, and the shape of the hole is what makes it worth
   freezing. Review put it precisely — `footprintWithinGrant` answers a
   HISTORICAL question (was every claimed read inside the snapshot this
   derivation received?) and freshness answers a TEMPORAL one (are those
   dependencies still current NOW, at acceptance?). Both can be satisfied about
   a world that has moved.

   The witness:

       cut grant           fb@1 = 5
       derive against it   value 5, footprint [["fb",1]]
       World moves         fb@2 = 9

       checkResult                 PASS
       footprintWithinGrant        PASS
       validateForeignResult       PASS   (re-derives against the same snapshot)
       ─────────────────────────────────
       live freshness              MUST REFUSE

   All three passing checks are CORRECT. Nothing lied. The executor and the
   authority agree perfectly about a snapshot, and the snapshot is stale — so a
   protocol that stops at re-derivation commits a value the World has already
   contradicted.

   It also witnesses the negative half, which matters as much: an UNRELATED
   write must not invalidate. Freshness keys on the footprint, never on a global
   vclock — that is the whole reason the footprint is the dependency record and
   the grant is not, and a vclock rule would silently undo it.

   And the TOCTOU shape is witnessed rather than asserted: a freshness check
   that returns to the caller before the commit is a window, so acceptance is
   one call and the caller must hold the World's commit lock across it.
   ═══════════════════════════════════════════════════════════════════════════ */
import {
  ProgramRegistry, checkResult, footprintWithinGrant, validateForeignResult,
  validateFootprintFresh, deriveLocally, DerivationAuthority,
} from "./derive_protocol.mjs";

const results = [];
// "GAP" is reserved for the one row that is the finding rather than a property:
// the v0.2.0-era checks pass on a stale result, correctly, and that is the hole.
const R = (id, held, note) => { results.push({ id, held }); console.log(
  `${held ? "HOLDS" : "GAP  "}  ${id.padEnd(30)} ${note}`); };

/* a tiny mutable World: versioned resources plus one registered scope query */
const world = {
  res: { fb: { value: 5, version: 1 }, other: { value: 0, version: 1 } },
  scopes: { "kind:node": ["a", "b"] },
  read(r) { const e = this.res[r]; if (!e) throw new Error("no-such-resource: " + r); return { ...e }; },
  scope(q) { const s = this.scopes[q]; if (!s) throw new Error("no-such-scope: " + q); return [...s]; },
  write(r, value) { const e = this.res[r]; this.res[r] = { value, version: (e?.version ?? 0) + 1 }; },
};

const P = { op: "add", a: { op: "read", resource: "fb" }, b: { op: "input", name: "bias" } };
const reg = new ProgramRegistry(); const PID = reg.bind(P);
const authority = new DerivationAuthority(world, [P]);

const intent = { intent_id: "i-1", program_sem_id: PID, canonical_inputs: { bias: 0 },
  requested_resources: { exact: ["fb"], predicates: [] } };
const { request: req } = authority.authorize(intent);
const res = deriveLocally(reg, req).result;

console.log(`grant ${req.grant_id.slice(0, 20)}… cut at fb@1=5 · derived value ${res.semantic_result.value} · ` +
  `footprint ${JSON.stringify(res.semantic_result.read_footprint.exact)}`);

/* ── the World moves under the derivation ─────────────────────────────────── */
world.write("fb", 9);
console.log(`World moved: fb is now @${world.res.fb.version}=${world.res.fb.value}\n`);

{
  const a = checkResult(res, req);
  const b = footprintWithinGrant(res.semantic_result.read_footprint, req.read_grants);
  const c = validateForeignResult(reg, req, res);
  R("containment-era checks", false,
    `checkResult ${a.ok ? "PASS" : a.reason} · footprintWithinGrant ${b.ok ? "PASS" : b.reason} · ` +
    `validateForeignResult ${c.ok ? "PASS" : c.reason} — all three CORRECT, and the value 5 is now wrong ` +
    `in a World where fb is 9. Re-derivation against the same snapshot can never notice this`);

  const f = validateFootprintFresh(world, res.semantic_result.read_footprint);
  R("live freshness", !f.ok && /^stale-read: fb granted@1 live@2/.test(f.reason),
    `${f.reason} — the temporal question, asked against the LIVE world and keyed on the footprint`);

  const acc = authority.accept(req, res);
  R("acceptance refuses", !acc.ok && /^stale-read: fb/.test(acc.reason),
    `${acc.reason} — issuance, validation and freshness in ONE call on the AUTHORITY, which closes over ` +
    `its own reader and issuance table so neither proof can arrive as an argument`);
}

/* ── the negative half: an unrelated write must NOT invalidate ────────────── */
{
  world.res.fb = { value: 5, version: 1 };          // restore the granted state
  world.write("other", 999);                        // a write the derivation never read
  const acc = authority.accept(req, res);
  R("unrelated-write-ignored", acc.ok && acc.fresh_at_check === true && acc.committable === undefined,
    `other@${world.res.other.version} moved and acceptance still passes (fresh_at_check ${acc.fresh_at_check}, ` +
    `and NO committable field — one call cannot make a result committable, only observed fresh) — ` +
    `freshness keys on the FOOTPRINT, not on a global vclock. A vclock rule would invalidate every ` +
    `derivation on every unrelated write and quietly undo the grant/footprint separation`);
}

/* ── a scope whose result set moved, with no exact read touched ───────────── */
{
  const S = { op: "len", a: { op: "scope", query: "kind:node" } };
  const reg2 = new ProgramRegistry(); const SID = reg2.bind(S);
  const auth2 = new DerivationAuthority(world, [S]);
  const { request: r2 } = auth2.authorize({ intent_id: "i-2", program_sem_id: SID,
    canonical_inputs: {}, requested_resources: { exact: [], predicates: ["kind:node"] } });
  const s2 = deriveLocally(reg2, r2).result;
  world.scopes["kind:node"] = ["a", "b", "c"];       // the phantom: a node joins
  const acc = auth2.accept(r2, s2);
  R("scope-digest-staleness", !acc.ok && acc.reason === "stale-scope: kind:node",
    `${acc.reason} — value ${s2.semantic_result.value} was derived over 2 nodes and the query now answers 3, with no ` +
    `exact read having moved. This is the World's phantom-scope case (law:warrant.phantom-scope@1) ` +
    `reaching the derivation boundary`);
}

/* ── issuance: grant_id proves integrity, not authority ───────────────────── */
{
  const forged = { ...req, request_id: "req-self-made" };
  const acc = new DerivationAuthority(world, [P]).accept(req, res);
  const accForged = authority.accept(forged, { ...res, request_id: "req-self-made" });
  R("grant-id-is-not-issuance", !acc.ok && acc.reason === "grant-not-issued-by-this-authority"
      && !accForged.ok && accForged.reason === "grant-not-issued-by-this-authority",
    `a DIFFERENT authority instance refuses the same well-formed request (${acc.reason}), and a ` +
    `self-made request_id is refused by the issuing one. grant_id = H(read_grants) authenticates ` +
    `content to itself and proves nothing about who cut it; the issuance table is what does`);
}

console.log("=".repeat(100));
const bad = results.filter((r) => r.id === "containment-era checks" ? r.held : !r.held);
console.log(`STALE-GRANT v0.3 WITNESS: ${results.filter((r) => r.id !== "containment-era checks" && r.held).length}/5 ` +
  `hold; the three containment-era checks pass on a stale result BY DESIGN, which is the finding` +
  (bad.length ? ` — FAILURES: ${bad.map((r) => r.id).join(", ")}` : ""));
process.exit(bad.length ? 1 : 0);
