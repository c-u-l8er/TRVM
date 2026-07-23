"""wrl_canonical.py -- WRL Slice 2 identity spine (Phase 3A).

The single source of truth for the FROZEN Forge Semantic IR v1 registries and
for the canonical-identity discipline GPT-5.6 named for WRL Slice 2:

    validate_graph      typed structural validation (stable error codes)
    canonicalize_graph  order-independent canonical WRL graph
    serialize_artifact  deterministic canonical bytes of the STATIC artifact
    semantic_artifact_id  Hash(canonical Forge IR + semantic policy refs)
    backend_artifact_id   Hash(SemanticArtifactID + lowering profile)

Identity split (D4): the SemanticArtifactID is a pure function of the frozen
semantic graph (objects with static_config, structural edges, semantic policy
ids) and NOTHING of the backend encoding, the run plan, or the claim batches.
The BackendArtifactID additionally folds in the lowering profile (encoding,
compiler hash, backend representation) -- so one-hot<->binary and Q-format
backend swaps move the BackendArtifactID while leaving the SemanticArtifactID
fixed, and a different numeric/admit policy or a different initial rotor moves
BOTH (the semantic id first).

This module deliberately does NOT import wrl_ir at load time (wrl_ir imports
these registries and helpers). canonicalize_graph rebuilds a graph via the
passed instance's own type, so no back-import is needed.
"""
import hashlib
import json
import re
from collections import namedtuple

# the OPERATIVE counter-encoding domain (Phase 3D.1-A): `auto` applies the
# profile's pinned `onehot_max`; `one_hot`/`binary` force the representation.
COUNTER_ENCODINGS = ("auto", "one_hot", "binary")
_SEM_ID_RE = re.compile(r"^sem-[0-9a-f]{64}$")

# ------------------------------------------------------------ frozen registry
IR_VERSION = "1.0"
PROFILE_ID = "forge.world.core.v1"          # deterministic-circuit-world
RULEPACK_ID = "forge.world.core.rules.v1"   # the transition law (Slice 2.1)
ADMIT_POLICY_ID = "admit_candidate_min_firstreceipt_v1"
FILM_SCHEMA_ID = "film.v0.7"
NUMERIC_POLICY_IDS = ("POLICY_FORGE",)
LOWERING_PROFILE_VERSION = "1.0"

ROLE_IDS = ("Pulser", "Relay", "Door", "Spinner", "Orb")
EDGE_KINDS = ("SignalWire", "SocketControl")

# frozen schema block (the only accepted artifact schemas)
SCHEMA_IDS = {
    "runtime_state_schema": "RuntimeStateV1",
    "epoch_input_schema": "EpochInputV1",
    "observable_schema": "EpochResultV1",
}
STATE_SCHEMA_REFS = {"state.%s.v1" % r.lower() for r in ROLE_IDS}

# the required non-null single-valued semantic policy ids
REQUIRED_POLICY_IDS = ("rulepack_id", "admit_policy_id", "film_schema_id")
# the required keys of a backend lowering profile (Phase 3D.1-A: `encoding` ->
# operative `counter_encoding` + a pinned `onehot_max`).
REQUIRED_LOWERING_KEYS = ("counter_encoding", "onehot_max", "numeric_backend",
                          "compiler_hash", "target", "lowering_profile_version")

# per-role port signatures (frozen)
PORTS = {
    "Pulser":  {"out": ("sig_out",), "in": ()},
    "Relay":   {"out": ("sig_out",), "in": ("sig_in",)},
    "Door":    {"out": (),           "in": ("sig_in",)},
    "Spinner": {"out": ("socket",),  "in": ("sig_in",)},
    "Orb":     {"out": (),           "in": ("pose",)},
}
# the required (src_out_port, dst_in_port) for each structural edge kind
EDGE_PORTS = {
    "SignalWire":    ("sig_out", "sig_in"),
    "SocketControl": ("socket", "pose"),
}

# ----------------------------------------- authoritative per-role config schema
# (Phase 3B.5.1) The single source of truth for a role's config keys, consumed
# by BOTH the artifact validator (`static_config_keys` -> the exact key set a
# sealed static_config may reveal) AND the surface tooling (`surface_keys` -> the
# k=v lexemes a WRL Core `(...)` group accepts, which wrl_complete offers). A
# Pulser's verbose surface (`mode/period/phase/epoch`) is folded to a single
# positional `clock` field in the artifact, so the two projections differ for it.
ROLE_CONFIG_SCHEMA = {
    "Pulser":  {"surface_keys": ("mode", "period", "phase", "epoch"),
                "static_config_keys": ("clock",)},
    "Relay":   {"surface_keys": (), "static_config_keys": ()},
    "Door":    {"surface_keys": (), "static_config_keys": ()},
    "Spinner": {"surface_keys": ("w", "n", "rotor", "configurable"),
                "static_config_keys": ("w", "n", "rotor", "configurable")},
    "Orb":     {"surface_keys": (), "static_config_keys": ()},
}

# frozen exact key sets for the sealed artifact records (Phase 3B.5.1). A sealed
# artifact must reveal EXACTLY these fields -- an unknown field is a typed
# rejection, never silently dropped, so no meaning-bearing data can smuggle past
# the identity spine unnoticed.
ARTIFACT_FIELDS = ("ir_version", "profile_id", "semantic_policies",
                   "schemas", "objects", "edges")
POLICY_FIELDS = ("rulepack_id", "numeric_policy_ids",
                 "admit_policy_id", "film_schema_id")
OBJECT_FIELDS = ("object_id", "role", "static_config",
                 "state_schema_ref", "ports")
EDGE_FIELDS = ("kind", "src", "dst")

_IDENT_OK = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


# ----------------------------------------------- canonical semantic locators
# (Phase 3B.5.1) An identity-spine locator names an offending element by its
# CANONICAL key -- NOT by a source span or filename (those stay in the 3B-1
# sidecar). wrl_diagnostics maps these through a WrlSourceMap to spans/canvas.
class ObjectKey(namedtuple("ObjectKey", "object_id")):
    __slots__ = ()

    def render(self):
        return "object %s" % (self.object_id,)


class EdgeKey(namedtuple("EdgeKey", "kind src dst")):
    __slots__ = ()

    def render(self):
        return "edge %s:%s->%s" % (self.kind, self.src, self.dst)


# ------------------------------------------------------------------ exceptions
class WrlUnsupported(Exception):
    """A construct outside the frozen IR v1 scope (never a speculative
    lowering). Base class so `except WrlUnsupported` also catches the typed
    structural rejections below."""


class WrlValidationError(WrlUnsupported):
    """A typed structural rejection carrying a STABLE machine code AND, when the
    validator can name the offending element, CANONICAL semantic locators
    (Phase 3B.5.1): `primary_locator`/`related_locator` are ObjectKey/EdgeKey (or
    None) and `field_path` is a dotted canonical path like `static_config.rotor`
    (or None). These stay on the identity spine -- no source spans or filenames
    -- so the validator never depends on the 3B-1 sidecar; wrl_diagnostics maps
    the locators through a WrlSourceMap to spans/canvas."""
    def __init__(self, code, message, primary_locator=None,
                 related_locator=None, field_path=None):
        super().__init__("[%s] %s" % (code, message))
        self.code = code
        self.message = message
        self.primary_locator = primary_locator
        self.related_locator = related_locator
        self.field_path = field_path


# stable error codes (the validation contract)
WRL_DUPLICATE_ID = "WRL_DUPLICATE_ID"
WRL_UNKNOWN_ENDPOINT = "WRL_UNKNOWN_ENDPOINT"
WRL_ILLEGAL_PORT_PAIR = "WRL_ILLEGAL_PORT_PAIR"
WRL_CONTROLLER_CONFLICT = "WRL_CONTROLLER_CONFLICT"
WRL_CLOCK_RANGE = "WRL_CLOCK_RANGE"
WRL_NUMERIC_RANGE = "WRL_NUMERIC_RANGE"
WRL_EPOCH_RANGE = "WRL_EPOCH_RANGE"
WRL_UNSUPPORTED_FEATURE = "WRL_UNSUPPORTED_FEATURE"
# Slice 2.1 sealing / lexical errata codes
WRL_UNSEALED_POLICY = "WRL_UNSEALED_POLICY"          # null/empty policy id
WRL_MALFORMED_ARTIFACT = "WRL_MALFORMED_ARTIFACT"    # bad shape / version / schema
WRL_PORT_SIGNATURE = "WRL_PORT_SIGNATURE"            # {ports} != role signature
WRL_BAD_LOWERING_PROFILE = "WRL_BAD_LOWERING_PROFILE"  # half-specified backend
# Phase 3D.1.1 sealed-object integrity code
WRL_SEALED_IMMUTABLE = "WRL_SEALED_IMMUTABLE"        # attempted write to a seal
# Phase 3B.5.1 exact-key-set code
WRL_UNKNOWN_ARTIFACT_FIELD = "WRL_UNKNOWN_ARTIFACT_FIELD"  # extra sealed field


def _fail(code, message, primary_locator=None, related_locator=None,
          field_path=None):
    raise WrlValidationError(code, message, primary_locator,
                             related_locator, field_path)


def _reject_unknown(present, allowed, where, primary_locator=None,
                    path_prefix=None):
    """Reject any field NOT in the frozen `allowed` set. `where` names the record
    for the message; `primary_locator`/`path_prefix` carry the canonical locator
    onto the raised error so wrl_diagnostics can point at the extra field."""
    extra = sorted(set(present) - set(allowed))
    if extra:
        fp = extra[0] if path_prefix is None else "%s.%s" % (path_prefix,
                                                             extra[0])
        _fail(WRL_UNKNOWN_ARTIFACT_FIELD,
              "%s has unknown field(s) %s (frozen set: %s)"
              % (where, extra, sorted(allowed)),
              primary_locator=primary_locator, field_path=fp)


# --------------------------------------------------------------- port helpers
def object_ports(role):
    """The frozen non-empty port groups of a role (adapter/artifact form)."""
    return {k: list(v) for k, v in PORTS[role].items() if v}


def port_projection(role):
    """The full frozen port SET of a role -- the checked projection that a WRL
    `{...}` brace group must reveal exactly (Slice 2.1)."""
    return set(PORTS[role]["in"]) | set(PORTS[role]["out"])


def validate_port_projection(role, tokens):
    """A WRL `{ports}` brace group is a CHECKED projection of the role's frozen
    ports: it must reveal the role signature exactly. `{}` or a bogus token is
    rejected -- visible source is never silently ignored (Slice 2.1)."""
    want = port_projection(role)
    got = set(tokens)
    if got != want:
        _fail(WRL_PORT_SIGNATURE,
              "%s ports %s do not match the frozen signature %s"
              % (role, sorted(got), sorted(want)))


# ------------------------------------------------------------ payload helpers
def _rotor4(tok):
    """Coerce a rotor spec to a length-4 int tuple, or raise NUMERIC_RANGE."""
    if not (isinstance(tok, (tuple, list)) and len(tok) == 4):
        _fail(WRL_NUMERIC_RANGE, "rotor must have 4 lanes, got %r" % (tok,))
    try:
        return tuple(int(v) for v in tok)
    except (TypeError, ValueError):
        _fail(WRL_NUMERIC_RANGE, "rotor lanes must be integers: %r" % (tok,))


def _canon_payload_key(payload):
    """A deterministic sort key for a claim payload (surface-independent)."""
    kind = payload[0]
    if kind == "SetRotor":
        return (0, payload[1], tuple(int(v) for v in payload[2]))
    if kind == "ResetFault":
        return (1, payload[1], ())
    return (9, str(payload), ())


# --------------------------------------------------------------- validation
def validate_graph(g):
    """Typed structural validation of a canonical WRL graph against the
    frozen IR v1 registries. Raises WrlValidationError with a stable code.
    The IR validator -- not the Fixture constructor -- owns these errors."""
    if g.profile != PROFILE_ID:
        _fail(WRL_UNSUPPORTED_FEATURE,
              "unknown profile %r; this compiler only serves %s"
              % (g.profile, PROFILE_ID))

    # ---- objects: closed roles, unique ids, well-formed identifiers
    role_of = {}
    first_decl = {}
    for role, name, cfg in g.nodes:
        if role not in ROLE_IDS:
            _fail(WRL_UNSUPPORTED_FEATURE,
                  "role %r not in the frozen v1 registry %s" % (role, ROLE_IDS),
                  primary_locator=ObjectKey(name), field_path="role")
        if name in role_of:
            _fail(WRL_DUPLICATE_ID, "duplicate object id %r" % (name,),
                  primary_locator=ObjectKey(name),
                  related_locator=first_decl.get(name))
        if not name or set(name) - _IDENT_OK or "__" in name:
            _fail(WRL_UNSUPPORTED_FEATURE,
                  "bad object id %r (alnum/_ only, no '__')" % (name,),
                  primary_locator=ObjectKey(name), field_path="object_id")
        role_of[name] = role
        first_decl[name] = ObjectKey(name)
        _validate_config(role, name, cfg)

    # ---- edges: closed kinds, declared endpoints, legal port pairs
    sig_in_count, socket_in_count = {}, {}
    first_ctrl = {}
    for edge in g.edges:
        kind, s, d = edge
        ekey = EdgeKey(kind, s, d)
        if kind not in EDGE_KINDS:
            _fail(WRL_UNSUPPORTED_FEATURE,
                  "edge kind %r not in frozen v1 edges %s" % (kind, EDGE_KINDS),
                  primary_locator=ekey, field_path="kind")
        if s not in role_of:
            _fail(WRL_UNKNOWN_ENDPOINT, "edge source %r not declared" % (s,),
                  primary_locator=ekey, field_path="src")
        if d not in role_of:
            _fail(WRL_UNKNOWN_ENDPOINT,
                  "edge destination %r not declared" % (d,),
                  primary_locator=ekey, field_path="dst")
        out_port, in_port = EDGE_PORTS[kind]
        if out_port not in PORTS[role_of[s]]["out"]:
            _fail(WRL_ILLEGAL_PORT_PAIR,
                  "%s (%s) has no out-port %s for a %s"
                  % (s, role_of[s], out_port, kind),
                  primary_locator=ekey, related_locator=ObjectKey(s))
        if in_port not in PORTS[role_of[d]]["in"]:
            _fail(WRL_ILLEGAL_PORT_PAIR,
                  "%s (%s) has no in-port %s for a %s"
                  % (d, role_of[d], in_port, kind),
                  primary_locator=ekey, related_locator=ObjectKey(d))
        if kind == "SignalWire":
            sig_in_count[d] = sig_in_count.get(d, 0) + 1
        else:
            socket_in_count[d] = socket_in_count.get(d, 0) + 1
        first_ctrl.setdefault((kind, d), ekey)

    for d, c in sig_in_count.items():
        if c > 1:
            _fail(WRL_CONTROLLER_CONFLICT,
                  "%s has %d signal-wire inputs (a spinner admits one)"
                  % (d, c),
                  primary_locator=ObjectKey(d),
                  related_locator=first_ctrl.get(("SignalWire", d)))
    for d, c in socket_in_count.items():
        if c > 1:
            _fail(WRL_CONTROLLER_CONFLICT,
                  "%s has %d controllers (an orb admits one)" % (d, c),
                  primary_locator=ObjectKey(d),
                  related_locator=first_ctrl.get(("SocketControl", d)))

    # ---- run plan / epoch inputs (range only; targets are runtime-checked)
    if not isinstance(g.periods, int) or g.periods < 0:
        _fail(WRL_EPOCH_RANGE, "periods must be a non-negative integer")
    for e, batch in enumerate(g.batches):
        epoch = e + 1
        if not (1 <= epoch <= g.periods):
            _fail(WRL_EPOCH_RANGE,
                  "epoch %d out of range [1, %d]" % (epoch, g.periods))
    return g


def _validate_config(role, name, cfg):
    loc = ObjectKey(name)
    if role == "Pulser":
        clock = cfg.get("clock")
        # a JSON round-trip (deserialize_artifact) yields lists, not tuples
        if not (isinstance(clock, (tuple, list)) and clock):
            _fail(WRL_CLOCK_RANGE, "pulser %s: missing clock" % (name,),
                  primary_locator=loc, field_path="static_config.clock")
        if clock[0] == "periodic":
            _, p, ph = clock
            if not (isinstance(p, int) and p >= 1):
                _fail(WRL_CLOCK_RANGE, "pulser %s: period >= 1" % (name,),
                      primary_locator=loc, field_path="static_config.clock")
            if not (isinstance(ph, int) and 0 <= ph < p):
                _fail(WRL_CLOCK_RANGE,
                      "pulser %s: phase in [0, period)" % (name,),
                      primary_locator=loc, field_path="static_config.clock")
        elif clock[0] == "once":
            _, e = clock
            if not (isinstance(e, int) and e >= 0):
                _fail(WRL_CLOCK_RANGE, "pulser %s: once epoch >= 0" % (name,),
                      primary_locator=loc, field_path="static_config.clock")
        else:
            _fail(WRL_UNSUPPORTED_FEATURE,
                  "pulser %s: clock mode %r (only periodic|once)"
                  % (name, clock[0]),
                  primary_locator=loc, field_path="static_config.clock")
    elif role == "Spinner":
        for key in ("w", "n", "rotor"):
            if cfg.get(key) is None:
                _fail(WRL_UNSUPPORTED_FEATURE,
                      "spinner %s: missing %r" % (name, key),
                      primary_locator=loc, field_path="static_config.%s" % key)
        w_, n_ = cfg["w"], cfg["n"]
        if not (isinstance(w_, int) and w_ > 0 and
                isinstance(n_, int) and 0 <= n_ <= w_):
            _fail(WRL_NUMERIC_RANGE, "spinner %s: bad lane geometry" % (name,),
                  primary_locator=loc, field_path="static_config.n")
        rot = _rotor4(cfg["rotor"])
        if not all(0 <= v < (1 << w_) for v in rot):
            _fail(WRL_NUMERIC_RANGE,
                  "spinner %s: rotor lanes out of [0, 2^%d)" % (name, w_),
                  primary_locator=loc, field_path="static_config.rotor")


# --------------------------------------------------------------- canonicalize
def canonicalize_graph(g):
    """Return a NEW graph with an order-independent canonical form: objects
    sorted IDENTITY-FIRST by (object_id, role), edges sorted by (kind, src,
    dst), rotor lanes normalized to int tuples, and each epoch's claim batch
    sorted by a surface-independent payload key. Declaration order and surface
    syntax no longer affect the bytes. Identity-first ordering is stable even
    if the role registry expands (Slice 2.1)."""
    cg = type(g)()
    cg.profile = g.profile
    cg.periods = g.periods
    cg.nodes = sorted(((role, name, _canon_config(role, cfg))
                       for role, name, cfg in g.nodes),
                      key=lambda t: (t[1], t[0]))
    cg.edges = sorted((kind, s, d) for (kind, s, d) in g.edges)
    cg.batches = []
    for batch in g.batches:
        cg.batches.append(sorted(
            ({"writer_id": c["writer_id"], "sequence": c["sequence"],
              "payload": _canon_payload(c["payload"])} for c in batch),
            key=lambda c: (_canon_payload_key(c["payload"]),
                           -1 if c["writer_id"] is None else c["writer_id"],
                           -1 if c["sequence"] is None else c["sequence"])))
    return cg


def _canon_config(role, cfg):
    out = dict(cfg)
    if role == "Spinner" and cfg.get("rotor") is not None:
        out["rotor"] = _rotor4(cfg["rotor"])
        out["configurable"] = bool(cfg.get("configurable", False))
    return out


def _canon_payload(payload):
    if payload[0] == "SetRotor":
        return ("SetRotor", payload[1], _rotor4(payload[2]))
    if payload[0] == "ResetFault":
        return ("ResetFault", payload[1])
    return payload


# ------------------------------------------------- serialization / identity
def _plain(obj):
    """Recursively convert tuples to lists so the JSON form is stable and
    round-trips (json.loads yields lists; re-serialization must match)."""
    if isinstance(obj, (tuple, list)):
        return [_plain(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    return obj


def serialize_artifact(artifact):
    """Deterministic canonical bytes of the STATIC semantic artifact. Keys
    sorted; tuples flattened to arrays; compact separators. The object and
    edge LISTS are pre-sorted by graph_to_ir; sort_keys covers dict order."""
    return json.dumps(_plain(artifact), sort_keys=True,
                      separators=(",", ":")).encode()


def deserialize_artifact(blob):
    return json.loads(blob.decode())


def _sha(blob):
    return hashlib.sha256(blob).hexdigest()


# ---------------------------------------------------- sealing / validation
def _nonempty_str(v):
    return isinstance(v, str) and v != ""


def validate_artifact_v1(artifact):
    """Full structural validation of a STATIC semantic artifact before it may
    be given an identity (Slice 2.1). Rejects null/empty policy ids, unknown
    schema ids, unsupported ir/profile versions, and malformed object/edge
    records. `deserialize_artifact` yields arbitrary JSON, so the hash path
    MUST run this first -- an unsealed policy can never be hashed into an
    official-looking SemanticArtifactID."""
    if not isinstance(artifact, dict):
        _fail(WRL_MALFORMED_ARTIFACT, "artifact must be an object")
    _reject_unknown(artifact, ARTIFACT_FIELDS, "artifact")
    if artifact.get("ir_version") != IR_VERSION:
        _fail(WRL_MALFORMED_ARTIFACT,
              "unsupported ir_version %r (only %s)"
              % (artifact.get("ir_version"), IR_VERSION))
    if artifact.get("profile_id") != PROFILE_ID:
        _fail(WRL_UNSUPPORTED_FEATURE,
              "unknown profile %r; this compiler only serves %s"
              % (artifact.get("profile_id"), PROFILE_ID))

    pol = artifact.get("semantic_policies")
    if not isinstance(pol, dict):
        _fail(WRL_MALFORMED_ARTIFACT, "missing semantic_policies block")
    _reject_unknown(pol, POLICY_FIELDS, "semantic_policies",
                    path_prefix="semantic_policies")
    for key in REQUIRED_POLICY_IDS:
        if not _nonempty_str(pol.get(key)):
            _fail(WRL_UNSEALED_POLICY,
                  "semantic policy %r is null/empty; a sealed artifact must "
                  "name the law that gives it meaning" % (key,))
    npi = pol.get("numeric_policy_ids")
    if not (isinstance(npi, list) and npi and all(_nonempty_str(x)
                                                  for x in npi)):
        _fail(WRL_UNSEALED_POLICY,
              "numeric_policy_ids must be a non-empty list of ids")

    if artifact.get("schemas") != SCHEMA_IDS:
        _fail(WRL_MALFORMED_ARTIFACT,
              "unknown schema block %r (only %s)"
              % (artifact.get("schemas"), SCHEMA_IDS))

    objects = artifact.get("objects")
    edges = artifact.get("edges")
    if not isinstance(objects, list) or not isinstance(edges, list):
        _fail(WRL_MALFORMED_ARTIFACT, "objects/edges must be lists")

    try:
        for o in objects:
            role = o["role"]
            oid = o.get("object_id")
            _reject_unknown(o, OBJECT_FIELDS, "object %r" % (oid,),
                            primary_locator=ObjectKey(oid))
            if role in ROLE_CONFIG_SCHEMA:
                sc = o.get("static_config") or {}
                _reject_unknown(
                    sc, ROLE_CONFIG_SCHEMA[role]["static_config_keys"],
                    "object %r static_config" % (oid,),
                    primary_locator=ObjectKey(oid),
                    path_prefix="static_config")
            if o["state_schema_ref"] != "state.%s.v1" % str(role).lower():
                _fail(WRL_MALFORMED_ARTIFACT,
                      "object %r: state_schema_ref %r != role %r"
                      % (oid, o.get("state_schema_ref"), role),
                      primary_locator=ObjectKey(oid),
                      field_path="state_schema_ref")
            if role in ROLE_IDS and o.get("ports") != object_ports(role):
                _fail(WRL_MALFORMED_ARTIFACT,
                      "object %r: ports %r != frozen %r"
                      % (oid, o.get("ports"), object_ports(role)),
                      primary_locator=ObjectKey(oid), field_path="ports")
        for e in edges:
            _reject_unknown(e, EDGE_FIELDS, "edge record")
        gnodes = [(o["role"], o["object_id"], o["static_config"])
                  for o in objects]
        gedges = [(e["kind"], e["src"], e["dst"]) for e in edges]
    except (KeyError, TypeError) as ex:
        _fail(WRL_MALFORMED_ARTIFACT, "malformed object/edge record: %r" % (ex,))

    # reuse the graph structural validator (roles, ports, controller conflict)
    scratch = _ArtifactGraph(artifact.get("profile_id"), gnodes, gedges)
    validate_graph(scratch)
    return artifact


class _ArtifactGraph:
    """A minimal graph view over an artifact for reuse of validate_graph
    (no run inputs live in the static artifact)."""
    def __init__(self, profile, nodes, edges):
        self.profile = profile
        self.nodes = nodes
        self.edges = edges
        self.periods = 0
        self.batches = []


def canonicalize_artifact_v1(artifact):
    """Normalize a valid-shaped artifact to its CANONICAL form so that any two
    reorder-equivalent artifacts serialize to identical bytes (Phase 3C-0).
    Normalizes: objects by (object_id, role), edges by (kind, src, dst),
    numeric_policy_ids (ordering carries no meaning), each port array, and the
    tuple/list/dict representation via the plain-form conversion. Rotor lanes
    and clock fields are POSITIONAL and are never reordered. Tolerant of shape
    (the returned value is re-validated by the caller)."""
    if not isinstance(artifact, dict):
        _fail(WRL_MALFORMED_ARTIFACT, "artifact must be an object")
    try:
        pol = artifact["semantic_policies"]
        cobjs = sorted(
            ({"object_id": o["object_id"], "role": o["role"],
              "static_config": _plain(o["static_config"]),
              "state_schema_ref": o["state_schema_ref"],
              "ports": {k: sorted(v) for k, v in o["ports"].items()}}
             for o in artifact["objects"]),
            key=lambda o: (o["object_id"], o["role"]))
        cedges = sorted(
            ({"kind": e["kind"], "src": e["src"], "dst": e["dst"]}
             for e in artifact["edges"]),
            key=lambda e: (e["kind"], e["src"], e["dst"]))
        cpol = {
            "rulepack_id": pol["rulepack_id"],
            "numeric_policy_ids": sorted(pol["numeric_policy_ids"]),
            "admit_policy_id": pol["admit_policy_id"],
            "film_schema_id": pol["film_schema_id"],
        }
        cart = {
            "ir_version": artifact["ir_version"],
            "profile_id": artifact["profile_id"],
            "semantic_policies": cpol,
            "schemas": _plain(artifact["schemas"]),
            "objects": cobjs,
            "edges": cedges,
        }
    except (KeyError, TypeError, AttributeError) as ex:
        _fail(WRL_MALFORMED_ARTIFACT, "malformed artifact: %r" % (ex,))
    return _plain(cart)


def _seal(artifact):
    """The public identity path: validate shape -> canonicalize -> validate
    canonical -> serialize. Returns (canonical_isolated_artifact, bytes). The
    canonical value is a fresh, isolated structure (plain-form deep copy), so
    later caller mutation cannot change an issued identity."""
    validate_artifact_v1(artifact)
    canon = canonicalize_artifact_v1(artifact)
    validate_artifact_v1(canon)
    return canon, serialize_artifact(canon)


def validate_lowering_profile_v1(profile):
    """A backend lowering profile must be fully specified AND in-domain before
    it may earn a BackendArtifactID (Phase 3D.1-A). The profile is now
    OPERATIVE: `counter_encoding` (auto|one_hot|binary) + a positive int
    `onehot_max` actually select the counter representation the compiler emits.
    `lowering_profile_version` must be the supported version; the remaining
    fields stay open strings until the compiler/target registries freeze. A
    half-specified or out-of-domain backend must not receive an official-looking
    identity."""
    if not isinstance(profile, dict):
        _fail(WRL_BAD_LOWERING_PROFILE, "lowering profile must be an object")
    for key in REQUIRED_LOWERING_KEYS:
        if key == "onehot_max":
            continue
        if not _nonempty_str(profile.get(key)):
            _fail(WRL_BAD_LOWERING_PROFILE,
                  "lowering profile missing/empty %r" % (key,))
    if profile["counter_encoding"] not in COUNTER_ENCODINGS:
        _fail(WRL_BAD_LOWERING_PROFILE,
              "unknown counter_encoding %r (only %s)"
              % (profile["counter_encoding"], COUNTER_ENCODINGS))
    om = profile.get("onehot_max")
    if not (isinstance(om, int) and not isinstance(om, bool) and om >= 1):
        _fail(WRL_BAD_LOWERING_PROFILE,
              "onehot_max must be a positive integer, got %r" % (om,))
    if profile["lowering_profile_version"] != LOWERING_PROFILE_VERSION:
        _fail(WRL_BAD_LOWERING_PROFILE,
              "unsupported lowering_profile_version %r (only %s)"
              % (profile["lowering_profile_version"], LOWERING_PROFILE_VERSION))
    return profile


def validate_semantic_id(semantic_id):
    """A BackendArtifactID must fold in a WELL-FORMED SemanticArtifactID:
    `sem-` followed by exactly 64 lowercase hex digits (Phase 3C-0)."""
    if not (isinstance(semantic_id, str) and _SEM_ID_RE.match(semantic_id)):
        _fail(WRL_BAD_LOWERING_PROFILE,
              "malformed semantic id %r (expect sem-<64 lowercase hex>)"
              % (semantic_id,))
    return semantic_id


class SealedArtifact:
    """A validated + CANONICAL static artifact carrying its SemanticArtifactID.
    Constructing one is the sealing gate -- it fails on any unsealed policy or
    malformed record, and normalizes reorder-equivalent inputs to one identity.

    Phase 3D.1.1 -- SEALED OBJECT INTEGRITY. The seal stores the CANONICAL BYTES,
    not a mutable dictionary. `.artifact` deserializes a FRESH copy on every read
    (mutating it can never touch the seal); `.semantic_id` is DERIVED from the
    bytes inside the constructor and is not a caller-writable field. The object
    is immutable: any attribute assignment or deletion raises WRL_SEALED_IMMUTABLE
    (D30). Mutating the original input after sealing has no effect because the
    bytes were already frozen (D28)."""
    __slots__ = ("_canonical_bytes", "_semantic_id")

    def __init__(self, artifact):
        _, blob = _seal(artifact)
        object.__setattr__(self, "_canonical_bytes", blob)
        object.__setattr__(self, "_semantic_id", "sem-" + _sha(blob))

    def __setattr__(self, name, value):
        _fail(WRL_SEALED_IMMUTABLE,
              "SealedArtifact is immutable; cannot assign %r" % (name,))

    def __delattr__(self, name):
        _fail(WRL_SEALED_IMMUTABLE,
              "SealedArtifact is immutable; cannot delete %r" % (name,))

    @property
    def canonical_bytes(self):
        """The frozen canonical serialization the SemanticArtifactID is over."""
        return self._canonical_bytes

    @property
    def artifact(self):
        """A FRESH isolated copy of the canonical artifact on every read."""
        return deserialize_artifact(self._canonical_bytes)

    @property
    def semantic_id(self):
        return self._semantic_id


def seal_artifact(artifact):
    """Validate, canonicalize, then seal a static artifact. Rejects null/empty
    policy ids, unknown schemas, unsupported versions, and malformed records;
    reorder-equivalent artifacts seal to identical bytes and identity."""
    return SealedArtifact(artifact)


def semantic_artifact_id(artifact):
    """SemanticArtifactID = Hash(CANONICAL Forge IR + semantic policy refs). A
    pure function of the frozen semantic graph -- independent of backend
    encoding, run plan, claim batches, AND object/edge/policy ORDER. The
    artifact is validated and canonicalized before it is hashed (Phase 3C-0):
    an unsealed policy can never earn an identity, and two reorder-equivalent
    artifacts get the same id. Accepts a raw artifact dict or a SealedArtifact.

    Phase 3D.1.1: for a SealedArtifact the id is recomputed straight from the
    seal's CANONICAL BYTES rather than trusting a stored field, so the returned
    id always agrees with the sealed bytes (D35)."""
    if isinstance(artifact, SealedArtifact):
        return "sem-" + _sha(artifact.canonical_bytes)
    _, blob = _seal(artifact)
    return "sem-" + _sha(blob)


def backend_artifact_id(semantic_id, lowering_profile):
    """BackendArtifactID = Hash(SemanticArtifactID + lowering profile). Both the
    SemanticArtifactID (well-formed `sem-<64 hex>`) and the lowering profile
    (encoding/version domain) are VALIDATED before hashing (Phase 3C-0). Two
    profiles that differ ONLY in a backend representation share the
    SemanticArtifactID but not this one; a semantic change already moved the
    SemanticArtifactID."""
    validate_semantic_id(semantic_id)
    validate_lowering_profile_v1(lowering_profile)
    body = {"semantic": semantic_id,
            "lowering": _plain(lowering_profile)}
    return "bknd-" + _sha(json.dumps(body, sort_keys=True,
                                     separators=(",", ":")).encode())
