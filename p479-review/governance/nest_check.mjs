/* ═══════════════════════════════════════════════════════════════════════════
   nest_check.mjs — v0.3.0 — THE NESTED COMPOSITION CHECKER
   law:proof.reference-is-not-claim@1 · law:proof.verifier-policy-owned@1
   law:proof.content-address-is-not-a-warrant@1 · law:proof.canonical-wire@1

   THREE PHASES, AND THE SPLIT IS THE ROUND:

     1. RESOLVE   ask an untrusted store for every root reachable from this
                  artifact, require canonical wire bytes, re-derive each root,
                  and build a SNAPSHOT THIS VERIFIER OWNS. Nothing after this
                  point touches the store.
     2. JUDGE     hand each DISTINCT artifact in the snapshot to the checker of
                  its own protocol, ONCE.
     3. WALK      verify every edge of the DAG against those judgments.

   WHY THAT IS NOT A WARRANT, and P4 got this wrong in the cautious direction.
   P4 ran the child checker once per CITATION — eight times over four artifacts
   — and published the four redundant runs as the price of not having issued a
   warrant. GPT's ruling is that a memo which is created inside one top-level
   verification, populated only by this verifier, keyed by an immutable snapshot
   this verifier owns, never persisted and never transmitted, is DERIVATION
   REUSE: common-subexpression elimination inside one derivation, not somebody
   else's verdict being believed. Nobody is trusted. Nothing survives the call.

   The distinction that matters is not how long a cached verdict lives — it is
   whether anything crossed an authority boundary. Bazel's remote ACTION cache
   is the counter-example precisely because a client believes an entry another
   party wrote. A verifier reusing its own arithmetic is not that, and running
   the same pure check four extra times was never soundness, only ceremony.

   SO BOTH STRATEGIES ARE IMPLEMENTED AND THE EQUIVALENCE IS MEASURED, not
   assumed: `derivation_reuse` is a policy field, and `nest_forgeries.mjs`
   requires the verdict and the refusal set to be IDENTICAL with it on and off.
   `persistent_warrant_hits` is reported and is 0, because there is no object in
   this tree that could produce one.

   THE POLICY IS THE CHECKER'S, AND P4's WAS THE CALLER'S. `checkNestBundle`
   took `{ max_depth = NEST_MAX_DEPTH }` and the header said a caller may lower
   it and never raise it. The code did not say that:

       checkNestBundle(chain40, { store })                 → REFUSED
       checkNestBundle(chain40, { store, max_depth: 1000 }) → VERIFIED

   Five rounds of "the checker owns the scope / the absence vocabulary / the
   citation semantics / the grammar", and the API caller could redefine the
   checker-owned resource policy by passing a number. A caller may now only
   TIGHTEN: every field is compared against the shipped policy and anything
   looser is refused by name. The EFFECTIVE policy's identity is reported beside
   the verdict, so a reader can tell which policy accepted an artifact.

   REFUSAL CODES

     nest-protocol-mismatch          not a nested composition
     nest-vocabulary-unknown         a key this checker's grammar does not have
     nest-scope-mismatch             scope is not the one this checker implements
     nest-reference-contract-mismatch  the transport contract is not this one
     nest-connective-unsupported     a connective this checker cannot evaluate
     nest-operand-malformed          an operand missing a field a citation needs
     nest-operand-duplicated         the same certificate cited twice at one node
     nest-reference-mismatch         references and operands do not name the same set
     nest-artifact-unresolvable      the store has no bytes under a cited root
     nest-artifact-malformed         the bytes do not parse, or have no canonical form
     nest-artifact-non-canonical     the bytes are not the canonical encoding of what
                                     they parse to — duplicate keys land here
     nest-artifact-invalid-utf8      the bytes are not valid UTF-8 at all
     nest-ingress-refused            the artifact handed in has no canonical form
     nest-artifact-root-mismatch     the bytes are NOT the artifact that was cited
     nest-artifact-root-malformed    a citation that is not a well-formed root
     nest-child-protocol-unsupported a child protocol with no checker here
     nest-child-refused              a child's OWN checker did not return VERIFIED
     nest-certificate-stale          the recomputed certificate id is not the one cited
     nest-citation-cross-wired       the id is right and the claim or aggregate it names is not
     nest-chain-ids-mismatch         the stored chain set is not the one the children give
     nest-claim-id-mismatch          nested_claim_sem_id is not over these operands
     nest-structure-mismatch         a structural measurement this checker derives otherwise
     nest-count-inconsistent         an aggregate field this checker derives otherwise
     nest-depth-exceeded             a citation chain past the policy ceiling
     nest-budget-exceeded            resolutions or bytes past the policy ceiling
     nest-cycle                      a root cited by one of its own ancestors
     nest-policy-weakened            a caller asked for a policy looser than the shipped one
     nest-checker-threw              the checker raised instead of refusing
   ═══════════════════════════════════════════════════════════════════════════ */
import { createHash } from "node:crypto";
import { readFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { grammar, publicResult, ownSnapshot } from "./schema.mjs";
import { verifiedClaimSemId, certificateOf } from "./certificate.mjs";
import {
  artifactRoot, artifactBytes, canonicalWireBytes, resolveArtifact, directoryStore,
  isRoot, WIRE_LIMITS,
} from "./cas.mjs";
import { checkBundle } from "./proof_check.mjs";
import { checkDomainBundle } from "./domain_check.mjs";
import {
  NEST_PROTOCOL, nestedClaimSemId, nestAggregateId, nestStructureSemId,
} from "./nest_bundle.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const H = (s) => createHash("sha256").update(s).digest("hex");

/* ── THE VERIFIER POLICY, AND IT IS THIS CHECKER'S ──────────────────────────
   An untrusted content store supplies not only wrong artifacts but arbitrarily
   deep, arbitrarily wide and arbitrarily large ones, so every one of these is a
   bound something hostile would otherwise choose. `max_depth` is the one P4 had
   and gave away.

   B5.1's rule, now enforced rather than written down: a caller may impose a
   STRICTER policy and may not weaken the shipped one. `derivation_reuse: false`
   counts as stricter — it does more work, not less. */
export const SHIPPED_POLICY = Object.freeze({
  max_depth: 32,
  max_artifact_bytes: WIRE_LIMITS.max_artifact_bytes,
  max_total_resolved_bytes: 64 * 1024 * 1024,
  max_operands_per_node: 64,
  max_artifact_resolutions: 4096,
  derivation_reuse: true,
});
/** Retained under its P4 name because the depth ceiling is cited by number in
 *  the ledger and the battery; it is the policy's field, not a second source. */
export const NEST_MAX_DEPTH = SHIPPED_POLICY.max_depth;
const NUMERIC_POLICY = Object.freeze(
  Object.keys(SHIPPED_POLICY).filter((k) => typeof SHIPPED_POLICY[k] === "number"));
export const policyId = (p) => "nestpol-" + H(NEST_PROTOCOL + "|" +
  Object.keys(p).sort().map((k) => k + "=" + JSON.stringify(p[k])).join("|"));

/** Resolve a requested policy against the shipped one. Returns the effective
 *  policy, or a refusal naming the field that was loosened. */
export function effectivePolicy(requested = {}) {
  const eff = { ...SHIPPED_POLICY };
  for (const [k, v] of Object.entries(requested)) {
    if (!(k in SHIPPED_POLICY))
      return { refusal: `${k} is not a field of this verifier's policy` };
    if (NUMERIC_POLICY.includes(k)) {
      if (typeof v !== "number" || !Number.isFinite(v))
        return { refusal: `${k} must be a finite number` };
      if (v > SHIPPED_POLICY[k])
        return { refusal: `${k}=${v} is LOOSER than this verifier's ${SHIPPED_POLICY[k]}. A ` +
          `caller may tighten a resource policy and may not weaken the checker-owned one while ` +
          `still claiming this verifier's verdict` };
      eff[k] = v;
    } else if (k === "derivation_reuse") {
      if (typeof v !== "boolean") return { refusal: "derivation_reuse must be a boolean" };
      // false is MORE work, so it is a tightening and is allowed.
      eff[k] = v;
    }
  }
  return { policy: Object.freeze(eff) };
}

/** DECLARED HERE, NOT IMPORTED — sixth round running. */
export const IMPLEMENTED_CHILD_PROTOCOLS = Object.freeze({
  "TRVM-BOUNDED-PROOF-v1": Object.freeze({
    claim_field: "bounded_claim_sem_id", check: checkBundle, composed: false }),
  "TRVM-BOUNDED-DOMAIN-PROOF-v1": Object.freeze({
    claim_field: "domain_claim_sem_id", check: checkDomainBundle, composed: false }),
  [NEST_PROTOCOL]: Object.freeze({
    claim_field: "nested_claim_sem_id", check: null, composed: true }),
});
export const IMPLEMENTED_CONNECTIVES = Object.freeze(["CONJUNCTION"]);
export const IMPLEMENTED_NEST_SCOPE = Object.freeze({
  kind: "NESTED_COMPOSED_VERIFIED_CLAIM_CONJUNCTION",
  quantifier: "OVER_CITED_CHILD_CERTIFICATES",
  generalizes_beyond_children: false,
  children_rechecked_by_their_own_checkers: true,
  parent_rederives_leaf_evidence: false,
});
/** The transport plane's semantics, declared where the transport lives rather
 *  than inside the claim — because how bytes are fetched is not what is proved. */
export const IMPLEMENTED_REFERENCE_CONTRACT = Object.freeze({
  resolution: "CONTENT_ADDRESSED",
  wire: "CANONICAL",
  address_is_a_warrant: false,
});
const CITATION_FIELDS = Object.freeze(
  ["protocol", "claim_sem_id", "aggregate_id", "verified_claim_sem_id"]);

/** EXPORTED so `field_audit.mjs` can derive its denominator from the checker's
 *  OWN vocabulary rather than from a hand-kept list. A field added here is a
 *  field the audit immediately demands a classification for. */
export const GRAMMAR = Object.freeze({
  bundle: { required: ["protocol", "claim", "chain_ids", "references", "aggregate", "structure"],
            optional: ["type", "version", "annotations"] },
  claim: { required: ["connective", "scope", "operands", "nested_claim_sem_id"], optional: [] },
  scope: { required: Object.keys(IMPLEMENTED_NEST_SCOPE), optional: [] },
  operand: { required: [...CITATION_FIELDS], optional: [] },
  references: { required: ["contract", "operands"], optional: [] },
  reference_contract: { required: Object.keys(IMPLEMENTED_REFERENCE_CONTRACT), optional: [] },
  reference: { required: ["verified_claim_sem_id", "artifact_root"], optional: [] },
  chain_ids: { required: ["leaf_chains"], optional: [] },
  aggregate: { required: ["operands", "child_verdicts", "leaf_receipts_rederived_by_parent",
                          "films_replayed_by_parent", "nested_verdict", "aggregate_id"],
               optional: [] },
  structure: { required: ["edges", "unique_artifacts", "max_depth_below", "bytes_if_inlined",
                          "unique_bytes", "films_below_by_edge_multiplicity",
                          "films_below_distinct", "cases_below_by_edge_multiplicity",
                          "cases_below_distinct", "structure_sem_id"],
               optional: [] },
});

const THREW = Symbol("threw");
const safe = (f) => { try { return f(); } catch { return THREW; } };

/** Comparison, and it is this file's own — `derive_protocol.mjs` is on the list
 *  of modules a composition checker asserts it does NOT hold, and comparing two
 *  values it derived itself does not need the derivation protocol's encoder. */
function stable(v) {
  if (v === null || typeof v !== "object") return JSON.stringify(v) ?? "undefined";
  if (Array.isArray(v)) return "[" + v.map(stable).join(",") + "]";
  return "{" + Object.keys(v).sort().map((k) => JSON.stringify(k) + ":" + stable(v[k])).join(",") + "}";
}

/** THE PUBLIC BOUNDARY IS BYTES. A verifier handed a live JavaScript object is
 *  handed something the caller can still change: measured against the shipped
 *  P4.1 pack, a getter on `references.contract.address_is_a_warrant` returned
 *  false to the checker's one read and true to everyone afterwards, and the
 *  same object serialised with `address_is_a_warrant: true` immediately after
 *  VERIFIED came back. Bytes cannot do that. */
export function checkNestBytes(raw, opts = {}) {
  /* THE ORDER IS THE PROTOCOL — law:proof.byte-budget-before-parse@1.
     P4.2 bounded the root's CANONICAL size, which is a size you only learn by
     decoding, parsing and re-encoding the thing you were trying not to spend
     that much work on. An 8 MiB+1 buffer of invalid UTF-8 reported
     `nest-ingress-refused` because the decode ran first. Bound the OCTETS THAT
     ARRIVED, before anything looks at them. */
  const { store, ...requested } = opts;
  const pol = effectivePolicy(requested);
  if (pol.refusal)
    return publicResult({ measured: { verifier_policy_id: policyId(SHIPPED_POLICY) },
      refusals: [{ code: "nest-policy-weakened", detail: pol.refusal }] });

  if (!Buffer.isBuffer(raw) && !(raw instanceof Uint8Array))
    return publicResult({ measured: {}, refusals: [{ code: "nest-ingress-refused",
      detail: `this boundary takes octets; it was handed a ${typeof raw}` }] });
  /* COPIED, ALWAYS. Retaining the caller's Buffer would leave the verifier's
     "own" bytes in storage somebody else can still write to — the getter
     defect of P4.2 in the one place P4.2 said was safe from it. */
  const bytes = Buffer.from(raw);
  if (bytes.length > pol.policy.max_artifact_bytes)
    return publicResult({ measured: { verifier_policy_id: policyId(pol.policy),
      reference_bundle_bytes: bytes.length },
      refusals: [{ code: "nest-budget-exceeded",
        detail: `${bytes.length} octets handed to this verifier, over its ` +
          `${pol.policy.max_artifact_bytes}-octet per-artifact ceiling. Bounded BEFORE decoding, ` +
          `because the size of an artifact must not be a thing you learn by processing it` }] });

  let bundle;
  try {
    bundle = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
    if (!canonicalWireBytes(bundle).equals(bytes))
      return publicResult({ measured: {}, refusals: [{ code: "nest-ingress-refused",
        detail: "the octets handed to this verifier are not the canonical UTF-8 encoding of what " +
          "they parse to" }] });
  } catch (e) {
    return publicResult({ measured: {}, refusals: [{ code: "nest-ingress-refused",
      detail: `the octets handed to this verifier are not a canonical artifact: ` +
        `${String(e?.message ?? e)}` }] });
  }
  return checkOwned(bundle, opts);
}

/** The object convenience API. It canonicalises ONCE — which reads every field
 *  exactly once, and it is that read the verdict is about — and then uses only
 *  the owned snapshot. law:proof.verifier-input-owned@1. */
export function checkNestBundle(bundle, opts = {}) {
  let owned;
  try { owned = ownSnapshot(bundle); }
  catch (e) {
    return publicResult({ measured: {}, refusals: [{ code: "nest-ingress-refused",
      detail: `the artifact has no canonical form and cannot be taken into this verifier's ` +
        `ownership: ${String(e?.message ?? e)}` }] });
  }
  return checkOwned(owned, opts);
}

function checkOwned(bundle, { store, ...requested } = {}) {
  const pol = effectivePolicy(requested);
  if (pol.refusal)
    return publicResult({ measured: { verifier_policy_id: policyId(SHIPPED_POLICY) },
      refusals: [{ code: "nest-policy-weakened", detail: pol.refusal }] });
  const policy = pol.policy;
  try {
    /* THE ROOT ARTIFACT IS SUBJECT TO THE SAME POLICY AS A RESOLVED CHILD.
       P4.1 applied `max_artifact_bytes` only to things fetched through the CAS,
       so the one artifact handed in directly could be any size at all: a 9.4 MB
       root verified under an 8 MiB ceiling. */
    const ownBytes = safe(() => artifactBytes(bundle));
    if (ownBytes === THREW)
      return publicResult({ measured: { verifier_policy_id: policyId(policy) },
        refusals: [{ code: "nest-ingress-refused", detail: "the artifact has no canonical form" }] });
    if (ownBytes > policy.max_artifact_bytes)
      return publicResult({ measured: { verifier_policy_id: policyId(policy),
        reference_bundle_bytes: ownBytes },
        refusals: [{ code: "nest-budget-exceeded",
          detail: `the artifact handed to this verifier is ${ownBytes} bytes, over its ` +
            `${policy.max_artifact_bytes}-byte per-artifact ceiling — the ROOT is not exempt ` +
            `from a policy its children are held to` }] });
    const ctx = {
      store, policy,
      snapshot: new Map(),        // root -> artifact          (phase 1, verifier-owned)
      heights: new Map(),         // root -> subtree height    (phase 1)
      judgments: new Map(),       // root -> {verdict, codes, films, cases}  (phase 2/3)
      resolutions: 0, resolvedBytes: 0, evaluations: 0, reuses: 0, edges: 0,
      resolveRefusals: [],
    };
    /* PHASE 1. Every root reachable from this artifact, resolved once, canonical
       -checked, re-hashed, and put into a map nothing else may write. */
    resolveClosure(bundle, ctx, 0, []);
    /* PHASES 2 AND 3, interleaved per node and memoised per ROOT when the
       policy allows reuse. */
    const frame = verify(bundle, ctx, null);
    const m = frame.measured;
    Object.assign(m, {
      verifier_policy_id: policyId(policy),
      verifier_policy: policy,
      // THE EXECUTION PLANE. `edges_if_fully_unfolded` is the DAG unfolded into
      // a tree — what a verifier with no reuse walks, and a property of the
      // artifact rather than of this run. `edge_traversals` is what THIS run
      // walked, and it always equals evaluations + reuses.
      edges_if_fully_unfolded: frame.sub.edges,
      edge_traversals: ctx.edges,
      unique_artifact_resolutions: ctx.resolutions,
      checker_evaluations: ctx.evaluations,
      derivation_reuses: ctx.reuses,
      // THERE IS NO OBJECT IN THIS TREE THAT COULD MAKE THIS NON-ZERO.
      persistent_warrant_hits: 0,
      resolved_bytes: ctx.resolvedBytes,
      reference_bundle_bytes: safe(() => artifactBytes(bundle)),
      /* PHASE 1's REFUSALS BELONG IN THE TRANSITIVE SET TOO. They are raised
         before any node is verified, so `verifyInner` never sees them — and a
         40-deep chain refused by the resolver reported a transitive code set
         that did not contain `nest-depth-exceeded`, which is the same
         verdict-versus-diagnosis gap P4 fixed one phase later. */
      refusal_codes_transitive: [...new Set([
        ...(frame.measured.refusal_codes_transitive ?? []),
        ...ctx.resolveRefusals.map((r) => r.code)])].sort(),
    });
    return publicResult({ refusals: [...ctx.resolveRefusals, ...frame.refusals], measured: m });
  } catch (e) {
    return publicResult({ measured: { verifier_policy_id: policyId(policy) },
      refusals: [{ code: "nest-checker-threw",
        detail: `the checker raised instead of refusing: ${String(e?.message ?? e)}` }] });
  }
}

/* ── PHASE 1: THE VERIFIER-OWNED SNAPSHOT ───────────────────────────────────
   The only phase that touches the store. Depth, cycles and every budget are
   decided here, so nothing downstream can be reached by making the DAG bigger.
   Returns the subtree HEIGHT, which is what the depth ceiling is actually about
   — and being a property of a node rather than of a path, it composes with
   reuse: a node resolved once at depth 1 and cited again at depth 2 is checked
   against `depth + height` both times. */
function resolveClosure(artifact, ctx, depth, ancestors) {
  const refuse = (code, detail) => ctx.resolveRefusals.push({ code, detail });
  if (depth > ctx.policy.max_depth) {
    refuse("nest-depth-exceeded",
      `a citation chain deeper than this verifier's ceiling of ${ctx.policy.max_depth}; the walk ` +
      `stops here rather than recursing until something else does`);
    return null;
  }
  const refs = artifact?.references?.operands;
  if (!Array.isArray(refs)) return 0;
  if (refs.length > ctx.policy.max_operands_per_node) {
    refuse("nest-budget-exceeded",
      `${refs.length} operands at one node, over this verifier's ${ctx.policy.max_operands_per_node}`);
    return null;
  }
  let height = 0;
  for (const r of refs) {
    const root = r?.artifact_root;
    if (!isRoot(root)) {
      refuse("nest-artifact-root-malformed",
        `${JSON.stringify(String(root)).slice(0, 60)} is not a well-formed artifact root`);
      continue;
    }
    if (ancestors.includes(root)) {
      refuse("nest-cycle", `${root.slice(0, 24)}… is cited by one of its own ancestors`);
      continue;
    }
    if (ctx.snapshot.has(root)) {
      // ALREADY OWNED. Availability dedup — but the ceiling is still checked
      // against THIS path, because the same node deeper down is a longer chain.
      height = Math.max(height, 1 + tall(ctx, refuse, depth, ctx.heights.get(root) ?? 0));
      continue;
    }
    if (ctx.resolutions >= ctx.policy.max_artifact_resolutions) {
      refuse("nest-budget-exceeded",
        `more than ${ctx.policy.max_artifact_resolutions} distinct artifacts in one DAG`);
      return null;
    }
    const res = resolveArtifact(ctx.store, root,
      { max_artifact_bytes: ctx.policy.max_artifact_bytes });
    if (res.outcome !== "ok") {
      refuse(res.outcome === "unresolvable" ? "nest-artifact-unresolvable"
           : res.outcome === "bad-root-syntax" ? "nest-artifact-root-malformed"
           : res.outcome === "non-canonical-wire" ? "nest-artifact-non-canonical"
           // NAMED SEPARATELY. Invalid UTF-8 and non-canonical-but-valid bytes
           // are different faults with different fixes, and folding the first
           // into `malformed` would hide the one P4.1 was blind to.
           : res.outcome === "invalid-utf8" ? "nest-artifact-invalid-utf8"
           : res.outcome === "root-mismatch" ? "nest-artifact-root-mismatch"
           : res.outcome === "too-large" ? "nest-budget-exceeded"
           : "nest-artifact-malformed", res.detail);
      continue;
    }
    ctx.resolutions += 1;
    ctx.resolvedBytes += res.bytes.length;
    if (ctx.resolvedBytes > ctx.policy.max_total_resolved_bytes) {
      refuse("nest-budget-exceeded",
        `${ctx.resolvedBytes} bytes resolved, over this verifier's ` +
        `${ctx.policy.max_total_resolved_bytes}`);
      return null;
    }
    ctx.snapshot.set(root, res.artifact);
    let h = 0;
    if (res.artifact?.protocol === NEST_PROTOCOL)
      h = resolveClosure(res.artifact, ctx, depth + 1, [...ancestors, root]) ?? 0;
    ctx.heights.set(root, h);
    height = Math.max(height, 1 + tall(ctx, refuse, depth, h));
  }
  return height;
}

/** THE CEILING IS ABOUT THE DAG'S HEIGHT, NOT THE RECURSION'S DEPTH — and the
 *  first draft compared the wrong one. `resolveClosure` only recurses into
 *  COMPOSED artifacts, so on the shipped DAG (D → C2 → C1 → A) it reaches depth
 *  2 while the height is 3, and `max_depth: 2` accepted a DAG one taller than
 *  it. Checking `depth + 1 + height(child)` at every edge measures the longest
 *  path through that edge, which is what a ceiling on citation chains means —
 *  and being a property of a node rather than of a path, it composes with reuse
 *  and is checked again at every citation of an already-resolved artifact. */
function tall(ctx, refuse, depth, h) {
  if (depth + 1 + h > ctx.policy.max_depth)
    refuse("nest-depth-exceeded",
      `a citation chain of ${depth + 1 + h} through this edge, past this verifier's ceiling of ` +
      `${ctx.policy.max_depth} (depth ${depth + 1} plus a subtree of height ${h})`);
  return h;
}

/* ── PHASES 2 AND 3 ─────────────────────────────────────────────────────────
   `verify` walks a node from the SNAPSHOT — never the store — and memoises its
   judgment by root when the policy allows. */
function verify(bundle, ctx, root) {
  if (root !== null && ctx.policy.derivation_reuse && ctx.judgments.has(root)) {
    ctx.reuses += 1;
    return ctx.judgments.get(root);
  }
  /* A COMPOSED CHILD IS AN EVALUATION TOO. The first draft counted only leaf
     checker calls, so `checker_evaluations + derivation_reuses` did not equal
     the edges actually walked and the accounting could not be checked against
     itself. Every traversed edge now does exactly one of two things: evaluate
     an artifact this run had not seen, or reuse a judgment this verifier
     already derived. */
  if (root !== null) ctx.evaluations += 1;
  const frame = verifyInner(bundle, ctx);
  if (root !== null) ctx.judgments.set(root, frame);
  return frame;
}

function verifyInner(bundle, ctx) {
  const refusals = [];
  const refuse = (code, detail) => { refusals.push({ code, detail }); };
  const measured = { leaf_receipts_rederived_here: 0, films_replayed_here: 0 };
  const sub = { unique: new Map(), edges: 0, inlined: 0, height: 0,
                filmsByEdge: 0, casesByEdge: 0, codes: new Set() };
  const done = (verdict) => {
    for (const r of refusals) sub.codes.add(r.code);
    measured.refusal_codes_transitive = [...sub.codes].sort();
    return { refusals, measured, sub, verdict };
  };

  if (bundle?.protocol !== NEST_PROTOCOL) {
    refusals.push({ code: "nest-protocol-mismatch", detail: String(bundle?.protocol) });
    return done("REFUSED");
  }
  const vocab = (record, spec, where) => {
    for (const v of grammar(record, spec, where)) refuse("nest-vocabulary-unknown", v.detail);
  };
  vocab(bundle, GRAMMAR.bundle, "bundle");
  if (bundle.annotations !== undefined) {
    const flat = (v) => typeof v === "string"
      || (Array.isArray(v) && v.every((x) => typeof x === "string"))
      || (v && typeof v === "object" && !Array.isArray(v)
          && Object.values(v).every((x) => typeof x === "string"
            || (Array.isArray(x) && x.every((y) => typeof y === "string"))));
    if (bundle.annotations === null || typeof bundle.annotations !== "object"
        || Array.isArray(bundle.annotations) || !Object.values(bundle.annotations).every(flat))
      refuse("nest-vocabulary-unknown",
        "annotations is the NON-AUTHORITATIVE seat and holds prose only");
  }

  const claim = bundle.claim ?? {};
  vocab(claim, GRAMMAR.claim, "claim");
  const scope = claim.scope;
  vocab(scope, GRAMMAR.scope, "claim.scope");
  for (const k of Object.keys(IMPLEMENTED_NEST_SCOPE))
    if (scope?.[k] !== IMPLEMENTED_NEST_SCOPE[k])
      refuse("nest-scope-mismatch",
        `scope.${k} is ${JSON.stringify(scope?.[k])}, this checker implements ` +
        `${JSON.stringify(IMPLEMENTED_NEST_SCOPE[k])}`);
  for (const [k, v] of Object.entries(scope ?? {}))
    if (typeof v === "string" && /\s/.test(v))
      refuse("nest-scope-mismatch", `scope.${k} holds prose; explanatory text belongs in scope_notes`);
  if (!IMPLEMENTED_CONNECTIVES.includes(claim.connective))
    refuse("nest-connective-unsupported",
      `connective ${JSON.stringify(claim.connective)}; this checker evaluates ` +
      `[${IMPLEMENTED_CONNECTIVES.join(", ")}]`);
  vocab(bundle.chain_ids, GRAMMAR.chain_ids, "chain_ids");

  /* THE REFERENCE PLANE, CHECKED AS A PLANE. Its contract is the transport's
     semantics and this checker owns it; an artifact declaring its addresses are
     warrants is refused here rather than in the claim, because that is where
     the statement belongs. */
  const references = bundle.references ?? {};
  vocab(references, GRAMMAR.references, "references");
  vocab(references.contract, GRAMMAR.reference_contract, "references.contract");
  for (const k of Object.keys(IMPLEMENTED_REFERENCE_CONTRACT))
    if (references.contract?.[k] !== IMPLEMENTED_REFERENCE_CONTRACT[k])
      refuse("nest-reference-contract-mismatch",
        `references.contract.${k} is ${JSON.stringify(references.contract?.[k])}, this checker ` +
        `implements ${JSON.stringify(IMPLEMENTED_REFERENCE_CONTRACT[k])}`);

  const operands = Array.isArray(claim.operands) ? claim.operands : [];
  const refs = Array.isArray(references.operands) ? references.operands : [];
  /* BOUNDED BEFORE ITERATED, AND ON BOTH PLANES. Phase 1 bounds
     `references.operands` because that is what it walks; nothing bounded
     `claim.operands`, which this phase walks four times. */
  for (const [what, arr] of [["claim.operands", operands], ["references.operands", refs]])
    if (arr.length > ctx.policy.max_operands_per_node) {
      refusals.push({ code: "nest-budget-exceeded",
        detail: `${arr.length} entries in ${what}, over this verifier's ` +
          `${ctx.policy.max_operands_per_node}` });
      return done("REFUSED");
    }
  if (operands.length === 0) {
    refusals.push({ code: "nest-operand-malformed", detail: "no operands" });
    return done("REFUSED");
  }
  for (const [i, o] of operands.entries()) {
    vocab(o, GRAMMAR.operand, `operand ${i}`);
    for (const f of CITATION_FIELDS) if (typeof o?.[f] !== "string" || o[f].length === 0)
      refuse("nest-operand-malformed", `operand ${i}: ${f} is ${JSON.stringify(o?.[f])}`);
  }
  for (const [i, r] of refs.entries()) vocab(r, GRAMMAR.reference, `references.operands[${i}]`);

  const seen = new Map();
  for (const [i, o] of operands.entries()) {
    if (seen.has(o?.verified_claim_sem_id))
      refuse("nest-operand-duplicated",
        `${o.verified_claim_sem_id} cited at operands ${seen.get(o.verified_claim_sem_id)} and ${i}`);
    else seen.set(o?.verified_claim_sem_id, i);
  }

  /* THE TWO PLANES MUST NAME THE SAME SET. Separating claim from reference
     creates the one thing separation always creates — a way for the halves to
     disagree — so exactly one reference per operand, matched by certificate. */
  const byCert = new Map();
  for (const r of refs) {
    if (byCert.has(r?.verified_claim_sem_id))
      refuse("nest-reference-mismatch", `two references for ${r?.verified_claim_sem_id}`);
    byCert.set(r?.verified_claim_sem_id, r);
  }
  for (const c of byCert.keys()) if (!seen.has(c))
    refuse("nest-reference-mismatch", `a reference for ${String(c).slice(0, 28)}… that no operand cites`);

  let verified = 0;
  const verdicts = {};
  const resolvedChildren = [];
  for (const [i, o] of operands.entries()) {
    const ref = byCert.get(o?.verified_claim_sem_id);
    if (!ref) {
      refuse("nest-reference-mismatch",
        `operand ${i} cites ${String(o?.verified_claim_sem_id).slice(0, 28)}… and no reference ` +
        `says where its bytes are`);
      continue;
    }
    const child = ctx.snapshot.get(ref.artifact_root);
    if (!child) continue;   // phase 1 already refused it, by name
    ctx.edges += 1;
    sub.edges += 1;
    const bytes = safe(() => artifactBytes(child)) || 0;
    sub.inlined += bytes;

    const spec = IMPLEMENTED_CHILD_PROTOCOLS[child?.protocol];
    if (!spec) {
      refuse("nest-child-protocol-unsupported",
        `operand ${i}: child protocol ${JSON.stringify(child?.protocol)}; this checker implements ` +
        `[${Object.keys(IMPLEMENTED_CHILD_PROTOCOLS).join(", ")}]`);
      continue;
    }
    resolvedChildren.push(child);

    let verdict, films = 0, cases = 0;
    if (spec.composed) {
      const childFrame = verify(child, ctx, ref.artifact_root);
      verdict = childFrame.refusals.length === 0 ? "VERIFIED" : "REFUSED";
      for (const c of childFrame.sub.codes) sub.codes.add(c);
      for (const [r, v] of childFrame.sub.unique) sub.unique.set(r, v);
      sub.unique.set(ref.artifact_root, { bytes, films: 0, cases: 0 });
      sub.edges += childFrame.sub.edges;
      sub.inlined += childFrame.sub.inlined;
      films = childFrame.sub.filmsByEdge; cases = childFrame.sub.casesByEdge;
      sub.height = Math.max(sub.height, 1 + childFrame.sub.height);
      if (verdict !== "VERIFIED")
        refuse("nest-child-refused",
          `operand ${i} (${child.protocol}): its own checker returns REFUSED` +
          (childFrame.refusals.length
            ? ` [${[...new Set(childFrame.refusals.map((x) => x.code))].join(", ")}]` : ""));
    } else {
      /* A LEAF IS JUDGED ONCE PER DISTINCT ARTIFACT when the policy allows
         reuse, and once per citation when it does not. The VERDICT is identical
         either way — measured in nest_forgeries.mjs, not assumed here. */
      let j = ctx.policy.derivation_reuse ? ctx.judgments.get(ref.artifact_root) : undefined;
      if (j) ctx.reuses += 1;
      else {
        const r = safe(() => spec.check(child));
        ctx.evaluations += 1;
        j = r === THREW
          ? { leaf: true, verdict: "THREW", codes: [], films: 0, cases: 0 }
          : { leaf: true, verdict: r?.verdict,
              codes: [...new Set((r.refusals ?? []).map((x) => x.code))],
              films: r?.measured?.films_replayed_on_two_classes ?? 0,
              cases: r?.measured?.derived_cases ?? 0,
              bad: !(r.ok === true && r.verdict === "VERIFIED") };
        if (ctx.policy.derivation_reuse) ctx.judgments.set(ref.artifact_root, j);
      }
      verdict = j.verdict;
      films = j.films; cases = j.cases;
      for (const c of j.codes) sub.codes.add(c);
      sub.unique.set(ref.artifact_root, { bytes, films, cases });
      sub.height = Math.max(sub.height, 1);
      if (j.verdict !== "VERIFIED" || j.bad)
        refuse("nest-child-refused",
          `operand ${i} (${child.protocol}): its own checker returns ${verdict}` +
          (j.codes.length ? ` [${j.codes.join(", ")}]` : ""));
    }
    sub.filmsByEdge += films;
    sub.casesByEdge += cases;
    verdicts[o.verified_claim_sem_id] = verdict;
    if (verdict === "VERIFIED") verified++;

    const own = certificateOf(child, spec.claim_field);
    const recomputed = safe(() => verifiedClaimSemId(own));
    if (recomputed === THREW)
      refuse("nest-operand-malformed",
        `operand ${i}: the resolved artifact is missing a field the certificate identity binds ` +
        `— a ${child.protocol} that cannot be NAMED cannot be cited`);
    else if (recomputed !== o.verified_claim_sem_id)
      refuse("nest-certificate-stale",
        `operand ${i}: cites ${o.verified_claim_sem_id.slice(0, 24)}…, the resolved artifact ` +
        `computes ${recomputed.slice(0, 24)}…`);
    for (const f of ["protocol", "claim_sem_id", "aggregate_id"])
      if (o[f] !== own[f])
        refuse("nest-citation-cross-wired",
          `operand ${i}: cites ${f} ${JSON.stringify(o[f])}, the resolved artifact's own is ` +
          `${JSON.stringify(own[f])}`);
  }

  const derivedChains = safe(() => deriveChainIds(resolvedChildren));
  const chainSet = (v) => (Array.isArray(v?.leaf_chains) ? v.leaf_chains : null)
    ?.map(stable).sort().join("|");
  if (derivedChains === THREW
      || chainSet(derivedChains) !== safe(() => chainSet(bundle.chain_ids)))
    refuse("nest-chain-ids-mismatch",
      `chain_ids does not identify the compilers of the artifacts this checker resolved — ` +
      `a composition's chain is DERIVED from its children and may not be declared`);

  if (safe(() => nestedClaimSemId(claim.connective, scope, operands)) !== claim.nested_claim_sem_id)
    refuse("nest-claim-id-mismatch",
      "nested_claim_sem_id does not identify (connective, quantifier semantics, operands). It " +
      "does NOT bind an artifact_root: a locator may rename the artifact carrying a proof and " +
      "may not rename the proof");

  /* THE EVIDENCE PLANE — inside the certificate identity. */
  const agg = bundle.aggregate ?? {};
  vocab(agg, GRAMMAR.aggregate, "aggregate");
  /* `nested_verdict` WAS HASHED AND UNREAD — B6.3 for the thirteenth time, in a
     protocol written two rounds after the law that forbids it. Setting it to
     REFUSED and resealing `aggregate_id` left this checker at ok:true,
     VERIFIED, zero refusals, over an artifact that said of itself that it was
     refused. It is derived from the verdicts this checker computed, exactly as
     the producer derives it. `field_audit.mjs` now mutates EVERY field of EVERY
     record mechanically, so the fourteenth cannot be found by hand either. */
  const derivedVerdict =
    Object.values(verdicts).filter((v) => v === "VERIFIED").length === operands.length
    && operands.length > 0 ? "VERIFIED" : "REFUSED";
  const derivedAgg = {
    operands: operands.length,
    child_verdicts: verdicts,
    leaf_receipts_rederived_by_parent: 0,
    films_replayed_by_parent: 0,
    nested_verdict: derivedVerdict,
  };
  for (const [k, v] of Object.entries(derivedAgg))
    if (stable(v) !== safe(() => stable(agg[k])))
      refuse("nest-count-inconsistent",
        `aggregate.${k} says ${JSON.stringify(agg[k])}, this checker derives ${JSON.stringify(v)}`);
  if (safe(() => nestAggregateId(agg)) !== agg.aggregate_id)
    refuse("nest-count-inconsistent", "aggregate_id does not identify the aggregate beside it");

  /* THE STRUCTURE PLANE — authenticated inside the artifact root, OUTSIDE the
     certificate. Every field is derived and compared, so it cannot lie; none of
     it renames the theorem, so a DAG that grew a node is a different ARTIFACT
     rather than a different CLAIM. And nothing here depends on how many times
     the verifier evaluated anything. */
  const st = bundle.structure ?? {};
  vocab(st, GRAMMAR.structure, "structure");
  const derivedStructure = {
    edges: sub.edges,
    unique_artifacts: sub.unique.size,
    max_depth_below: sub.height,
    bytes_if_inlined: sub.inlined,
    unique_bytes: [...sub.unique.values()].reduce((a, b) => a + b.bytes, 0),
    films_below_by_edge_multiplicity: sub.filmsByEdge,
    films_below_distinct: [...sub.unique.values()].reduce((a, b) => a + b.films, 0),
    cases_below_by_edge_multiplicity: sub.casesByEdge,
    cases_below_distinct: [...sub.unique.values()].reduce((a, b) => a + b.cases, 0),
  };
  for (const [k, v] of Object.entries(derivedStructure))
    if (stable(v) !== safe(() => stable(st[k])))
      refuse("nest-structure-mismatch",
        `structure.${k} says ${JSON.stringify(st[k])}, this checker derives ${JSON.stringify(v)}`);
  if (safe(() => nestStructureSemId(st)) !== st.structure_sem_id)
    refuse("nest-structure-mismatch", "structure_sem_id does not identify the structure beside it");

  if (claim.connective === "CONJUNCTION" && verified !== operands.length)
    refuse("nest-child-refused",
      `the claim is a CONJUNCTION of ${operands.length} child claims and ${verified} are verified`);

  Object.assign(measured, derivedStructure, {
    dedup_ratio: derivedStructure.unique_bytes > 0
      ? +(derivedStructure.bytes_if_inlined / derivedStructure.unique_bytes).toFixed(4) : null,
  });
  return done(refusals.length === 0 ? "VERIFIED" : "REFUSED");
}

export function deriveChainIds(children) {
  const byBytes = new Map();
  for (const child of children) {
    const c = child?.chain_ids;
    const recs = c && typeof c === "object" && Array.isArray(c.leaf_chains)
      ? c.leaf_chains : (c === undefined || c === null ? [] : [c]);
    for (const rec of recs) byBytes.set(stable(rec), rec);
  }
  return { leaf_chains: [...byBytes.keys()].sort().map((k) => byBytes.get(k)) };
}

const IS_MAIN = import.meta.url === (await import("node:url")).pathToFileURL(process.argv[1] ?? "").href;
if (IS_MAIN) {
  const path = process.argv[2] ?? join(HERE, "nest_bundle.json");
  if (!existsSync(path)) {
    console.log(`NEST-CHECK: FAIL — no bundle at ${path}`);
    process.exit(1);
  }
  /* THE EXECUTABLE AND THE LIBRARY MUST AGREE. This read `JSON.parse(readFileSync
     (path, "utf8"))` and handed the OBJECT to the object API, so the CLI
     destroyed the evidence of a duplicate member name before the canonical-wire
     checker could see it: `checkNestBytes(raw)` REFUSED a root carrying
     `"protocol":"TRVM-EVIL-v1"` while `node nest_check.mjs` on the same file
     printed PASS and exited 0 — with a sentence in its own output explaining
     that duplicate names are refused. The artifact an executable verifies goes
     through exactly the boundary the protocol says is authoritative. */
  const raw = readFileSync(path);
  const store = directoryStore(join(HERE, "cas"));
  const r = checkNestBytes(raw, { store });
  const bundle = r.ok ? JSON.parse(raw.toString("utf8")) : null;
  const m = r.measured;
  if (!r.ok) {
    console.log(`NEST-CHECK: FAIL — ${r.refusals.length} refusal(s)`);
    for (const x of r.refusals) console.log(`  ${x.code}: ${x.detail}`);
    process.exit(1);
  }
  console.log(`NEST-CHECK: PASS — NESTED COMPOSITION VERIFIED. ${m.operands ?? bundle.claim.operands.length}` +
    `-operand CONJUNCTION at the root of a DAG of height ${m.max_depth_below}. NO CHILD TRAVELS ` +
    `INSIDE THIS ARTIFACT: it is ${m.reference_bundle_bytes.toLocaleString()} canonical bytes and ` +
    `every operand is paired with a REFERENCE naming its child by content address. THE STORE IS ` +
    `NOT TRUSTED AND NEITHER IS THE CITATION: a root must match ^root-[0-9a-f]{64}$ before it ` +
    `reaches a path, the bytes returned must BE the canonical encoding of what they parse to — ` +
    `so a duplicate member name, another key order or a different number spelling is refused ` +
    `rather than silently reparsed — and the root is re-derived from those bytes. ` +
    `${m.unique_artifact_resolutions} distinct artifacts resolved; the DAG unfolds to ` +
    `${m.edges_if_fully_unfolded} edges and this run walked ${m.edge_traversals}. Carrying ` +
    `each cited child inline would be ${m.bytes_if_inlined.toLocaleString()} ` +
    `bytes against ${m.unique_bytes.toLocaleString()} stored once, ${m.dedup_ratio}×. AND A ` +
    `CONTENT ADDRESS IS STILL NOT A WARRANT: every distinct artifact was judged by the checker ` +
    `of its own protocol — ${m.checker_evaluations} evaluations + ${m.derivation_reuses} reuses ` +
    `= ${m.edge_traversals} edges walked, every reuse being a judgment ` +
    `THIS verifier derived, in THIS run, over a snapshot it owns, and ` +
    `${m.persistent_warrant_hits} verdicts believed from anywhere else. That reuse is ` +
    `common-subexpression elimination inside one derivation and the verdict is identical with it ` +
    `off, which the forgery suite measures rather than assumes. REFERENCE IS NOT CLAIM: ` +
    `artifact_root lives in the reference plane and NOT in nested_claim_sem_id, so rewording a ` +
    `leaf's prose moves this artifact's bytes and leaves the theorem's name alone. THE PARENT ` +
    `STILL DOES NOT FLATTEN: ${m.films_below_by_edge_multiplicity} films would be replayed by a ` +
    `walk of every edge and ${m.films_below_distinct} are held by the distinct artifacts — both ` +
    `STRUCTURAL — while this checker replayed ${m.films_replayed_here}. THE POLICY IS THIS ` +
    `CHECKER'S: depth ${m.verifier_policy.max_depth}, ${m.verifier_policy.max_artifact_bytes} ` +
    `bytes per artifact, ${m.verifier_policy.max_total_resolved_bytes} total, under ` +
    `${m.verifier_policy_id.slice(0, 22)}… — a caller may tighten it and is refused if it asks ` +
    `for anything looser.`);
  console.log(`  nested claim ${bundle.claim.nested_claim_sem_id}`);
  for (const o of bundle.claim.operands) {
    const ref = bundle.references.operands.find((x) => x.verified_claim_sem_id === o.verified_claim_sem_id);
    console.log(`    ∧ ${o.protocol.padEnd(30)} ${o.verified_claim_sem_id.slice(0, 22)}… ` +
      `@ ${ref.artifact_root.slice(0, 18)}… → ${m.child_verdicts?.[o.verified_claim_sem_id] ?? "VERIFIED"}`);
  }
}
