"""wrl.projection.1 -- the ingress boundary for a transmitted runtime projection.

C.4.3. This module is the Python half of WRL's §D8.18/§D8.19: it reads a
projection off a wire, establishes every claim on it independently, and hands
the V1 executor a locally derived admission.

WHY THIS IS A SEPARATE MODULE, AND NOT A LOOSENING OF THE V1 GATE
-----------------------------------------------------------------
`wrl_canonical.validate_artifact_v1` refuses an artifact carrying `relations`
with WRL_UNKNOWN_ARTIFACT_FIELD. That refusal is CORRECT and stays. A frozen V1
reader that learned to tolerate a V2 field would be a reader that no longer
tells you which encoding it just read, and the whole of §D8.15 exists to stop a
world's identity depending on who opened it.

So V2 understanding lives here, above the spine, and the spine below remains the
authority for sealing the derived V1 execution artifact. The layering is:

    wire bytes  ->  [this module: parse exactly, derive, compare]
                ->  VerifiedRuntimeAdmission
                ->  [wrl_canonical: seal the V1 execution artifact]
                ->  V1 executor

THE TRUST BOUNDARY
------------------
The ruling separates three capabilities, and this module is exactly the middle
one:

    opaque transport      may relay.   May not verify. May not execute.
    ingress verifier      may relay,   MAY verify,     prepares admission.
    V1 executor core      local only.  Does not verify. EXECUTES.

The executor never sees the sender's bytes. It receives a
`VerifiedRuntimeAdmission` built on this side, from values this side computed.
A process that cannot derive the execution artifact may still store, route or
relay a projection; it may not claim to have verified or admitted one.

PROJECTION CAPABILITY IS NOT WIRE-VERIFIER CAPABILITY
------------------------------------------------------
Worth stating because the difference is easy to under-count. The structural
V2->V1 transform is small and hash-free: drop the relation identity, keep the
topology, restore `ir_version`. Verifying a wire record is that PLUS the whole
V2 canonical identity scheme -- canonical V2 bytes, the world id, each seed
expansion and `rel-`, each canonical revision and `rev-`, the execution view id,
and the canonical binding order. Without the second half an implementation can
produce bytes to run but cannot establish that the world and the bindings on
the wire agree with each other. Only the first half would be "can run it"; both
halves are "may say it verified".
"""

import hashlib
import json

import wrl_canonical as C

PROJECTION_VERSION = "wrl.projection.1"

PROJECTION_FIELDS = ("projection_version", "semantic_world_id",
                     "semantic_artifact", "execution_view_id",
                     "relation_bindings")

V1_IR_VERSIONS = ("1.0",)
V2_IR_VERSIONS = ("2.0",)

V1_TEXTURE = "solid"
V1_DOMAIN = "signal"
DEFAULT_POLICY = "forge.world.core.rules.v1"

SEED_FIELDS = {
    "named-initial": ("relation_name",),
    "legacy-edge": ("kind", "src", "dst"),
}
ALLOCATION_FIELDS = {
    "named-initial": ("world_id", "relation_name"),
    "legacy-edge": ("world_id", "kind", "src", "dst"),
    "granted": ("grant_id", "sequence"),
}

REVISION_FIELDS = ("kind", "domain", "orientation", "texture", "endpoints",
                   "attributes", "policy")
ENDPOINT_ROLES = ("source", "target")

SAFE_INT_MAX = 2 ** 53 - 1


class ProjectionError(C.WrlUnsupported):
    """A transmitted projection is not one, or does not recompute."""

    def __init__(self, code, message, field_path=None):
        super().__init__("[%s] %s" % (code, message))
        self.code = code
        self.field_path = field_path


def _fail(code, message, field_path=None):
    raise ProjectionError(code, message, field_path)


# ------------------------------------------------- C.4.1: exact canonical JSON
#
# Python is not exposed to the defect that motivated the JS reader -- its ints
# are arbitrary precision, so `json.loads` holds 2**63-1 exactly. It IS exposed
# to the other three: duplicate keys silently keep the last, floats parse, and
# whitespace and key order are accepted on a wire that calls its bytes
# canonical. An implementation that fixed only the part its own language got
# wrong would conform by accident.
#
# One divergence is worth naming because it is Python's and not JavaScript's:
# `json.dumps` defaults to `ensure_ascii=True` and would render a non-ASCII
# string as a \u escape where `JSON.stringify` emits the character. Both are
# valid JSON and they are different bytes. `_canonical_bytes` below pins
# `ensure_ascii=False` so the two implementations agree; the round-trip gate
# then catches it if that is ever wrong.

def _canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _no_duplicate_keys(pairs):
    seen = set()
    out = {}
    for k, v in pairs:
        if k in seen:
            _fail("WRL_BAD_PROJECTION",
                  "the key %r appears twice; a reader that keeps the last one "
                  "lets two records with different bytes and different "
                  "meanings arrive as one object" % k, "projection")
        seen.add(k)
        out[k] = v
    return out


def _no_floats(token):
    _fail("WRL_BAD_PROJECTION",
          "a non-integral number %r appears; artifact scalars are integers, "
          "and a fraction or exponent is not a value this protocol can hold"
          % token, "projection")


def parse_canonical_projection_exactly(wire):
    """Read wire bytes as canonical JSON, or refuse them.

    Strict in four ways, and the fourth subsumes the rest: integers exact, no
    non-integral numbers, no duplicate keys, and the bytes must be THE
    canonical bytes -- checked by re-rendering what they denote and comparing.
    That last gate covers key order, escape spelling, `-0`, insignificant
    whitespace and every lexical variant nobody thought to enumerate.
    """
    if isinstance(wire, bytes):
        try:
            text = wire.decode("utf-8")
        except UnicodeDecodeError:
            _fail("WRL_BAD_PROJECTION",
                  "a transmitted projection is not valid UTF-8", "projection")
    elif isinstance(wire, str):
        text = wire
    else:
        _fail("WRL_BAD_PROJECTION",
              "a transmitted projection must be bytes or str, got %s"
              % type(wire).__name__, "projection")

    if text == "":
        _fail("WRL_BAD_PROJECTION", "a transmitted projection has no bytes",
              "projection")

    try:
        record = json.loads(text, object_pairs_hook=_no_duplicate_keys,
                            parse_float=_no_floats, parse_constant=_no_floats)
    except ProjectionError:
        raise
    except ValueError as e:
        _fail("WRL_BAD_PROJECTION",
              "a transmitted projection is not parseable JSON: %s" % e,
              "projection")

    if _canonical_bytes(record) != text:
        _fail("WRL_BAD_PROJECTION",
              "a transmitted projection is not in canonical form: it parses, "
              "but re-rendering what it denotes gives different bytes. This "
              "wire is identified by its bytes, so a lexical variant of a "
              "valid record is not a valid record", "projection")
    return record


# ------------------------------------------------------------------ identity

def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonicalize_revision(rev):
    """The canonical revision. Endpoints sort by ROLE then terminal, and the
    role order is fixed by ENDPOINT_ROLES rather than alphabetically -- a
    revision whose endpoints canonicalise into a different order is a different
    `rev-`, and source/target read the same length in either spelling."""
    if not isinstance(rev, dict):
        _fail("WRL_BAD_PROJECTION", "a relation revision is not an object",
              "revision")
    out = {}
    for f in REVISION_FIELDS:
        if f not in rev or rev[f] is None:
            continue
        if f == "endpoints":
            eps = []
            for e in rev["endpoints"]:
                t = e.get("terminal", {})
                eps.append({"terminal": {"object_id": t.get("object_id"),
                                         "port": t.get("port")},
                            "role": e.get("role")})
            eps.sort(key=lambda a: (
                ENDPOINT_ROLES.index(a["role"])
                if a["role"] in ENDPOINT_ROLES else len(ENDPOINT_ROLES),
                "%s.%s" % (a["terminal"]["object_id"], a["terminal"]["port"])))
            out[f] = eps
        else:
            out[f] = rev[f]
    return out


def relation_revision_id(rev):
    return "rev-" + _sha(_canonical_bytes(_canonicalize_revision(rev)))


def relation_id_from_allocation(allocation):
    variant = allocation.get("variant")
    if variant not in ALLOCATION_FIELDS:
        _fail("WRL_BAD_PROJECTION",
              "unknown allocation variant %r" % variant, "variant")
    payload = {"tag": "WRL_RELATION", "variant": variant}
    for f in ALLOCATION_FIELDS[variant]:
        payload[f] = allocation.get(f)
    return "rel-" + _sha(_canonical_bytes(payload))


def expand_seed(world_id, seed):
    variant = seed.get("variant")
    if variant not in SEED_FIELDS:
        _fail("WRL_BAD_PROJECTION",
              "a relation carries an unknown identity seed variant %r; a seed "
              "is the whole preimage of a relation_id, so an unknown variant "
              "is a name this side cannot mint" % variant, "identity_seed")
    allocation = {"variant": variant, "world_id": world_id}
    for f in SEED_FIELDS[variant]:
        allocation[f] = seed.get(f)
    return allocation


def canonicalize_v2_artifact(artifact):
    """Canonical V2 bytes: relations sorted by their seed's canonical bytes,
    and every seed unique. Two relations under one seed expand to one
    allocation and therefore one `relation_id`, so the world could not say
    which of the two a later revision revises."""
    if not isinstance(artifact, dict):
        _fail("WRL_BAD_PROJECTION", "a semantic artifact is not an object",
              "semantic_artifact")
    if artifact.get("ir_version") not in V2_IR_VERSIONS:
        _fail("WRL_BAD_PROJECTION",
              "canonicalize_v2_artifact was handed ir_version %r"
              % artifact.get("ir_version"), "ir_version")
    rels = artifact.get("relations")
    if not isinstance(rels, list):
        _fail("WRL_BAD_PROJECTION",
              "a V2 artifact states no relations", "relations")

    seen = {}
    canon = []
    for rel in rels:
        seed = rel.get("identity_seed")
        key = _canonical_bytes(seed)
        if key in seen:
            _fail("WRL_DUPLICATE_RELATION_SEED",
                  "two relations carry the identity seed %s" % key,
                  "relations")
        seen[key] = True
        canon.append({"identity_seed": seed,
                      "revision": _canonicalize_revision(rel.get("revision"))})
    canon.sort(key=lambda r: _canonical_bytes(r["identity_seed"]))

    out = dict(artifact)
    out["relations"] = canon
    return out


def v2_world_id(artifact):
    return "sem-" + _sha(_canonical_bytes(canonicalize_v2_artifact(artifact)))


def project_revision_to_v1_edge(rev):
    """The revision read back as the V1 edge it came from. A real inverse, not
    a plausible one: endpoints are found BY ROLE and never by position, because
    canonicalisation reorders a set whose order was never meaning, and a
    positional read produces a reversed edge that still round-trips through
    itself."""
    r = _canonicalize_revision(rev)
    kind = r.get("kind")
    if kind not in C.EDGE_PORTS:
        _fail("WRL_UNSUPPORTED_FEATURE",
              "relation kind %r has no V1 edge form" % kind, "kind")
    if r.get("orientation") != "directed":
        _fail("WRL_UNSUPPORTED_FEATURE",
              "a V1 edge is directed; a %r relation has no V1 form"
              % r.get("orientation"), "orientation")
    if r.get("domain") != V1_DOMAIN:
        _fail("WRL_UNSUPPORTED_FEATURE",
              "a V1 edge encodes the %s domain" % V1_DOMAIN, "domain")
    if r.get("texture") != V1_TEXTURE:
        _fail("WRL_UNSUPPORTED_FEATURE",
              "a V1 edge encodes only the %s texture" % V1_TEXTURE, "texture")
    if r.get("attributes"):
        _fail("WRL_UNSUPPORTED_FEATURE",
              "a V1 edge carries no attributes", "attributes")
    eps = r.get("endpoints") or []
    if len(eps) != 2:
        _fail("WRL_UNSUPPORTED_FEATURE",
              "a V1 edge has exactly two endpoints; this relation has %d"
              % len(eps), "endpoints")
    src = next((e for e in eps if e["role"] == "source"), None)
    dst = next((e for e in eps if e["role"] == "target"), None)
    if src is None or dst is None:
        _fail("WRL_INCOMPLETE_ORIENTATION",
              "a V1 edge needs one source and one target endpoint",
              "endpoints")

    # the ports are recoverable from the kind, so they are CHECKED rather than
    # carried -- writing them down twice would let the two copies disagree
    want_src, want_dst = C.EDGE_PORTS[kind]
    if src["terminal"]["port"] != want_src or dst["terminal"]["port"] != want_dst:
        _fail("WRL_PORT_SIGNATURE",
              "a %s edge runs %s -> %s; this relation names %s -> %s"
              % (kind, want_src, want_dst,
                 src["terminal"]["port"], dst["terminal"]["port"]), "endpoints")

    return {"kind": kind,
            "src": src["terminal"]["object_id"],
            "dst": dst["terminal"]["object_id"]}


def runnable_v1_artifact(v2artifact, ir_version=V1_IR_VERSIONS[0]):
    """The small, purely structural, hash-free half: drop relation identity,
    keep the topology, restore `ir_version`. Edges come out in V1's canonical
    order -- sorted by (kind, src, dst) -- and NOT in the V2 relation order,
    which sorts by seed bytes. The two orders disagree on real worlds."""
    canonical = canonicalize_v2_artifact(v2artifact)
    edges = sorted((project_revision_to_v1_edge(r["revision"])
                    for r in canonical["relations"]),
                   key=lambda e: (e["kind"], e["src"], e["dst"]))
    out = {k: v for k, v in canonical.items()
           if k not in ("ir_version", "relations")}
    out["ir_version"] = ir_version
    out["edges"] = edges
    return out


def v1_world_id(artifact):
    """The frozen spine is the authority here, not this module. `seal_artifact`
    validates before it hashes, so an artifact that is neither family is
    refused by the V1 gate rather than by a second opinion kept in step by
    hand."""
    return C.semantic_artifact_id(C.seal_artifact(artifact))


# ----------------------------------------------------------- the projection

class VerifiedRuntimeAdmission(object):
    """What the ingress verifier hands the executor.

    Every field was computed on THIS side. The sender's record is not carried
    forward -- it was evidence, and it has been spent. An executor holding one
    of these is not trusting a projection; it is trusting its own verifier,
    which is a capability it chose to have.
    """

    __slots__ = ("semantic_world_id", "semantic_artifact", "execution_view_id",
                 "execution_artifact", "relation_bindings", "coincident")

    def __init__(self, semantic_world_id, semantic_artifact,
                 execution_view_id, execution_artifact, relation_bindings):
        self.semantic_world_id = semantic_world_id
        self.semantic_artifact = semantic_artifact
        self.execution_view_id = execution_view_id
        self.execution_artifact = execution_artifact
        self.relation_bindings = relation_bindings
        self.coincident = execution_view_id == semantic_world_id

    def __repr__(self):
        return ("VerifiedRuntimeAdmission(world=%s, view=%s, bindings=%d, "
                "coincident=%s)" % (self.semantic_world_id[:20],
                                    self.execution_view_id[:20],
                                    len(self.relation_bindings),
                                    self.coincident))


def derive_runtime_projection(artifact, claimed_semantic_id=None):
    """§D8.18, total over both encodings.

    Totality is the point rather than a convenience: law 1 says
    `semantic_world_id` is authoritative, and a V2-only deriver would make that
    need an *unless*, so every consumer would branch on family before knowing
    which id is the world's -- which is precisely the site where the wrong id
    gets used. A V1 world is the coincident case and says so.
    """
    is_v2 = (isinstance(artifact, dict)
             and artifact.get("ir_version") in V2_IR_VERSIONS)

    if is_v2:
        semantic_artifact = canonicalize_v2_artifact(artifact)
        semantic_world_id = v2_world_id(semantic_artifact)
        execution_artifact = runnable_v1_artifact(semantic_artifact)
        relations = [
            {"identity_seed": r["identity_seed"], "revision": r["revision"]}
            for r in semantic_artifact["relations"]]
    else:
        semantic_artifact = artifact
        semantic_world_id = v1_world_id(artifact)
        execution_artifact = artifact
        # A V1 world's relations are not IN the artifact; the projection
        # invents them from `edges`, one legacy-edge seed apiece.
        canon = C.canonicalize_artifact_v1(artifact)
        relations = []
        for e in canon["edges"]:
            kind, src, dst = e["kind"], e["src"], e["dst"]
            ports = C.EDGE_PORTS[kind]
            relations.append({
                "identity_seed": {"variant": "legacy-edge", "kind": kind,
                                  "src": src, "dst": dst},
                "revision": {
                    "kind": kind, "domain": V1_DOMAIN,
                    "orientation": "directed", "texture": V1_TEXTURE,
                    "attributes": {}, "policy": DEFAULT_POLICY,
                    "endpoints": [
                        {"role": "source",
                         "terminal": {"object_id": src, "port": ports[0]}},
                        {"role": "target",
                         "terminal": {"object_id": dst, "port": ports[1]}}]}})

    if claimed_semantic_id is not None and claimed_semantic_id != semantic_world_id:
        _fail("WRL_SEMANTIC_ID_MISMATCH",
              "the supplied artifact hashes to %s, and the caller claims %s. "
              "A projection is derived from the seal, so the seal is "
              "recomputed rather than believed"
              % (semantic_world_id, claimed_semantic_id),
              "semantic_artifact_id")

    # Law 2: this id names the projected bytes and nothing else. The danger was
    # never that it would be wrong; it was that it would be RIGHT and be
    # mistaken for the world.
    execution_view_id = v1_world_id(execution_artifact)

    bindings = []
    for rel in relations:
        allocation = expand_seed(semantic_world_id, rel["identity_seed"])
        bindings.append({
            "relation_id": relation_id_from_allocation(allocation),
            "revision_id": relation_revision_id(rel["revision"]),
            "legacy_edge": project_revision_to_v1_edge(rel["revision"]),
        })

    return VerifiedRuntimeAdmission(semantic_world_id, semantic_artifact,
                                    execution_view_id, execution_artifact,
                                    bindings)


def serialize_runtime_projection(admission):
    """The one route to the wire. It takes an admission and not an artifact:
    a serializer that derived the projection itself would be a second route,
    and two routes can disagree about a world while both look right.

    It does not PROVE its argument came from the deriver, and nothing here
    could -- provenance is not transmissible. That is exactly why the receiver
    establishes every claim rather than trusting any.
    """
    if not isinstance(admission, VerifiedRuntimeAdmission):
        _fail("WRL_BAD_PROJECTION",
              "serialize_runtime_projection takes an admission from "
              "derive_runtime_projection, and was given %s"
              % type(admission).__name__, "projection")
    return _canonical_bytes({
        "projection_version": PROJECTION_VERSION,
        "semantic_world_id": admission.semantic_world_id,
        "semantic_artifact": admission.semantic_artifact,
        "execution_view_id": admission.execution_view_id,
        "relation_bindings": admission.relation_bindings,
    })


def verify_runtime_projection(wire):
    """The ingress boundary. Returns a VerifiedRuntimeAdmission or refuses.

    Nothing the sender wrote survives into the return value. The record is
    read, every claim on it is recomputed from the semantic artifact alone,
    and what comes back is what this side derived.
    """
    record = (parse_canonical_projection_exactly(wire)
              if isinstance(wire, (bytes, str)) else wire)

    if not isinstance(record, dict):
        _fail("WRL_BAD_PROJECTION",
              "a transmitted projection is not an object", "projection")

    # Exact key set, both directions. An extra key is refused rather than
    # ignored: the whole record is claims, so a field this side does not know
    # how to check is a field the far side may be relying on.
    got = sorted(record.keys())
    want = sorted(PROJECTION_FIELDS)
    if got != want:
        _fail("WRL_BAD_PROJECTION",
              "a transmitted projection carries the keys %s, and a projection "
              "is exactly %s" % (", ".join(got), ", ".join(want)),
              "projection")

    if record["projection_version"] != PROJECTION_VERSION:
        _fail("WRL_BAD_PROJECTION",
              "a transmitted projection declares version %r, and this reader "
              "speaks %s" % (record["projection_version"], PROJECTION_VERSION),
              "projection_version")

    if not isinstance(record["semantic_world_id"], str):
        _fail("WRL_BAD_PROJECTION",
              "a transmitted projection states no semantic_world_id",
              "semantic_world_id")

    # The claimed world id goes IN, so a lying world id is refused by the
    # deriver before anything else here is inspected.
    mine = derive_runtime_projection(record["semantic_artifact"],
                                     record["semantic_world_id"])

    if record["execution_view_id"] != mine.execution_view_id:
        _fail("WRL_PROJECTION_MISMATCH",
              "a transmitted projection claims execution_view_id %s, and this "
              "world projects to %s. The bytes a world runs as are a function "
              "of the world, so this is a disagreement about projection and "
              "not a stale field"
              % (record["execution_view_id"], mine.execution_view_id),
              "execution_view_id")

    if _canonical_bytes(record["relation_bindings"]) != \
            _canonical_bytes(mine.relation_bindings):
        _fail("WRL_PROJECTION_MISMATCH",
              "a transmitted projection's relation_bindings are not the ones "
              "this world derives. Every binding is recomputable from the "
              "semantic artifact alone, and the ORDER is derived too -- a "
              "reordered list leaves every id correct and every binding "
              "individually true, and is still a different claim about which "
              "relation runs as which edge", "relation_bindings")

    return mine
