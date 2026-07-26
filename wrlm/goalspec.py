"""GoalSpecV1 -- the closed predicate AST for WRLM-0.

Build-order step 1 of `TRVM/WRLM_RESEARCH_BRIEF.md` §10. Everything else in
WRLM-0 depends on this, including the `S` baseline.

WHY A CLOSED AST AND NOT A LANGUAGE (brief §4)
----------------------------------------------
Two reasons, the second load-bearing:

1. An open predicate language accidentally becomes a second WRL -- a
   language-design project nobody authorized.
2. The restricted closed AST, *evaluated over finite bounded WRL worlds*,
   keeps satisfaction decidable BY CONSTRUCTION. The closure of the AST alone
   does not buy this; the bounded finite semantics do. Decidability is what
   makes the `S` baseline (bounded symbolic search) implementable at all. An
   open language, or unbounded world semantics, makes `S` undecidable and
   silently kills the most important baseline.

The decidability argument, stated precisely:

  * Every quantifier in this AST ranges over a set MATERIALIZED FROM THE
    SEALED ARTIFACT -- `artifact["objects"]` or `artifact["edges"]`. Both are
    finite lists fixed before evaluation begins.
  * There is no recursion, no fixpoint, no unbounded arithmetic, and no
    reachability/transitive-closure operator (see BOUNDARIES below).
  * `MAX_GOAL_DEPTH` / `MAX_GOAL_NODES` bound the AST itself, so an
    adversarial goal cannot blow up `S` even on a small world.

  Therefore evaluation is a terminating structural fold, total on every
  well-formed input, costing O(|AST| x (|O| + |E|) x |E|) in the worst case
  (the inner |E| is `degree`/`endpoint` scanning the edge list).

TWO SORTS
---------
Filters are applied to either an OBJECT or an EDGE, and the two are not
interchangeable. The validator is a static sort checker: an object-sorted atom
inside an edge domain is `WRLM_GOAL_SORT`, not a runtime surprise.

  Goal   ::= all[Goal*] | any[Goal*] | not(Goal)
           | count(domain, where:Filter, cmp, n)

  Filter ::= filter_all[Filter*] | filter_any[Filter*] | filter_not(Filter)
           | role_is(role) | id_is(object_id)            -- object-sorted
           | config_eq(field, value) | degree(...)       -- object-sorted
           | edge_kind_is(edge_kind)                     -- edge-sorted
           | endpoint(side, where:Filter[object])        -- edge-sorted

`count` is the only quantifier, and it subsumes the usual ones:

    exists P   ==  count(where=P, cmp="ge", n=1)
    forall P   ==  count(where=filter_not(P), cmp="eq", n=0)
    exactly n  ==  count(where=P, cmp="eq", n=n)

`all[]` is TRUE and `any[]` is FALSE (the identities of the respective
monoids). This is deliberate, not an accident of the fold.

IDENTITY
--------
`goal_spec_id(node)` is `goal-<sha256 of canonical bytes>`, derived exactly the
way the WRL spine derives `sem-`: `json.dumps(..., sort_keys=True,
separators=(",", ":"))`. Per brief §4 the AST MUST be sealed into task identity,
otherwise the suite is not reproducible and the sealed-objective hole reopens.

Canonicalization is ORDER + DEDUPE ONLY, on the commutative idempotent
combinators (`all`/`any`/`filter_all`/`filter_any`). It performs NO semantic
rewriting. Consequence, stated plainly because it matters for task identity:

    not(not(X)) and X are semantically equal but seal to DIFFERENT goal ids.

Goal identity is syntactic up to commutativity and duplication -- it is not a
decision procedure for goal equivalence, and must never be used as one.

BOUNDARIES OF v1 (deliberate, not oversights)
---------------------------------------------
  * STRUCTURAL ONLY. Goals are predicates over the sealed static artifact, not
    over films or trajectories. Behavioural goals would require running the
    world; that is a different (still decidable, but far more expensive) layer
    and is out of scope for WRLM-0.
  * NO reachability / path operator. Bounded and decidable, but it materially
    complicates `S`. Deferred until `S` exists and can be measured.
  * NO floats anywhere. Floats have no place on an identity spine.

This module imports nothing from `forge/` on purpose: it consumes a plain
deserialized artifact dict, so `wrlm/` stays independently importable.
"""

import hashlib
import json

GOALSPEC_VERSION = "wrlm.goal.v1"

# Bounds. These are part of the contract: they are what keeps `S` tractable.
MAX_GOAL_DEPTH = 8
MAX_GOAL_NODES = 64
MAX_TUPLE_LEN = 8

# Mirrors of the frozen WRL v1 vocabulary. Duplicated rather than imported so
# `wrlm/` has no build-time dependency on `forge/`; `test_goalspec.py` G0 pins
# them against `wrl_canonical` when that module is importable.
ROLE_IDS = ("Pulser", "Relay", "Door", "Spinner", "Orb", "Mailbox")
EDGE_KINDS = ("SignalWire", "SocketControl")

DOMAINS = ("objects", "edges")
CMPS = ("eq", "ge", "le")
DIRECTIONS = ("in", "out")
SIDES = ("src", "dst")

OBJECT_SORT = "object"
EDGE_SORT = "edge"

# ------------------------------------------------------------------ the AST
GOAL_KINDS = ("all", "any", "not", "count")
FILTER_COMBINATORS = ("filter_all", "filter_any", "filter_not")
OBJECT_ATOMS = ("role_is", "id_is", "config_eq", "degree")
EDGE_ATOMS = ("edge_kind_is", "endpoint")
FILTER_KINDS = FILTER_COMBINATORS + OBJECT_ATOMS + EDGE_ATOMS

# Exact key set per kind. Extra or missing keys are a rejection, mirroring the
# WRL artifact validator's WRL_UNKNOWN_ARTIFACT_FIELD strictness -- a closed AST
# that tolerated stray keys would not be closed.
NODE_FIELDS = {
    "all":          ("kind", "args"),
    "any":          ("kind", "args"),
    "not":          ("kind", "arg"),
    "count":        ("kind", "domain", "where", "cmp", "n"),
    "filter_all":   ("kind", "args"),
    "filter_any":   ("kind", "args"),
    "filter_not":   ("kind", "arg"),
    "role_is":      ("kind", "role"),
    "id_is":        ("kind", "object_id"),
    "config_eq":    ("kind", "field", "value"),
    "degree":       ("kind", "direction", "edge_kind", "cmp", "n"),
    "edge_kind_is": ("kind", "edge_kind"),
    "endpoint":     ("kind", "side", "where"),
}

# The commutative, idempotent combinators -- the only nodes canonicalization
# is permitted to reorder and dedupe.
_COMMUTATIVE = ("all", "any", "filter_all", "filter_any")


# ------------------------------------------------------------------ exceptions
class GoalSpecError(Exception):
    """A typed structural rejection carrying a STABLE machine code and a dotted
    AST path (e.g. `where.args.1.role`) naming the offending node. The path is
    an AST locator, not a source span -- WRLM has no surface syntax."""

    def __init__(self, code, message, path=None):
        super().__init__("[%s] %s%s" % (code, message,
                                        "" if path is None else " at %s" % path))
        self.code = code
        self.message = message
        self.path = path


# stable error codes (the validation contract)
WRLM_BAD_GOAL = "WRLM_BAD_GOAL"              # bad shape / unknown kind / bad field
WRLM_GOAL_SORT = "WRLM_GOAL_SORT"            # object atom in edge position, or vice versa
WRLM_GOAL_BOUNDS = "WRLM_GOAL_BOUNDS"        # AST exceeds MAX_GOAL_DEPTH / MAX_GOAL_NODES
WRLM_SEALED_IMMUTABLE = "WRLM_SEALED_IMMUTABLE"   # attempted write to a seal


def _fail(code, message, path):
    raise GoalSpecError(code, message, path)


def _join(path, part):
    return part if path is None else "%s.%s" % (path, part)


# ------------------------------------------------------------------ validation
def _is_int(v):
    # bool is a subclass of int; a boolean count is a shape error, not a 0/1.
    return isinstance(v, int) and not isinstance(v, bool)


def _check_count_fields(node, path):
    if node["cmp"] not in CMPS:
        _fail(WRLM_BAD_GOAL, "cmp must be one of %s, got %r"
              % (list(CMPS), node["cmp"]), _join(path, "cmp"))
    if not _is_int(node["n"]) or node["n"] < 0:
        _fail(WRLM_BAD_GOAL, "n must be a non-negative int, got %r"
              % (node["n"],), _join(path, "n"))


def _check_shape(node, kinds, path):
    if not isinstance(node, dict):
        _fail(WRLM_BAD_GOAL, "node must be an object, got %s"
              % type(node).__name__, path)
    kind = node.get("kind")
    if kind not in kinds:
        _fail(WRLM_BAD_GOAL, "unknown kind %r here; expected one of %s"
              % (kind, list(kinds)), _join(path, "kind"))
    want = set(NODE_FIELDS[kind])
    got = set(node.keys())
    if got != want:
        missing = sorted(want - got)
        extra = sorted(got - want)
        _fail(WRLM_BAD_GOAL, "%s wants exactly %s (missing=%s extra=%s)"
              % (kind, sorted(want), missing, extra), path)
    return kind


def _validate_value(v, path):
    """A `config_eq` operand: bool, int, str, or a bounded list of ints (the
    artifact's tuple-valued config such as `clock` / `rotor`, which the WRL
    canonical serializer flattens to arrays). No floats -- see module docstring."""
    if isinstance(v, (bool, str)) or _is_int(v):
        return
    if isinstance(v, (list, tuple)):
        if len(v) > MAX_TUPLE_LEN:
            _fail(WRLM_GOAL_BOUNDS, "tuple value longer than MAX_TUPLE_LEN=%d"
                  % MAX_TUPLE_LEN, path)
        for i, x in enumerate(v):
            if not _is_int(x):
                _fail(WRLM_BAD_GOAL, "tuple value must hold ints, got %r"
                      % (x,), _join(path, str(i)))
        return
    _fail(WRLM_BAD_GOAL, "value must be bool/int/str/list-of-int, got %s"
          % type(v).__name__, path)


def _validate_filter(node, sort, depth, counter, path):
    if depth > MAX_GOAL_DEPTH:
        _fail(WRLM_GOAL_BOUNDS, "depth exceeds MAX_GOAL_DEPTH=%d"
              % MAX_GOAL_DEPTH, path)
    kind = _check_shape(node, FILTER_KINDS, path)
    counter[0] += 1
    if counter[0] > MAX_GOAL_NODES:
        _fail(WRLM_GOAL_BOUNDS, "node count exceeds MAX_GOAL_NODES=%d"
              % MAX_GOAL_NODES, path)

    # sort check first: a wrong-sorted atom is a sort error, never a field error
    if kind in OBJECT_ATOMS and sort != OBJECT_SORT:
        _fail(WRLM_GOAL_SORT, "%s is object-sorted but appears in %s position"
              % (kind, sort), path)
    if kind in EDGE_ATOMS and sort != EDGE_SORT:
        _fail(WRLM_GOAL_SORT, "%s is edge-sorted but appears in %s position"
              % (kind, sort), path)

    if kind in ("filter_all", "filter_any"):
        if not isinstance(node["args"], (list, tuple)):
            _fail(WRLM_BAD_GOAL, "args must be a list", _join(path, "args"))
        for i, a in enumerate(node["args"]):
            _validate_filter(a, sort, depth + 1, counter,
                             _join(_join(path, "args"), str(i)))
    elif kind == "filter_not":
        _validate_filter(node["arg"], sort, depth + 1, counter,
                         _join(path, "arg"))
    elif kind == "role_is":
        if node["role"] not in ROLE_IDS:
            _fail(WRLM_BAD_GOAL, "role must be one of %s, got %r"
                  % (list(ROLE_IDS), node["role"]), _join(path, "role"))
    elif kind == "id_is":
        if not isinstance(node["object_id"], str) or not node["object_id"]:
            _fail(WRLM_BAD_GOAL, "object_id must be a non-empty string, got %r"
                  % (node["object_id"],), _join(path, "object_id"))
    elif kind == "config_eq":
        if not isinstance(node["field"], str) or not node["field"]:
            _fail(WRLM_BAD_GOAL, "field must be a non-empty string, got %r"
                  % (node["field"],), _join(path, "field"))
        _validate_value(node["value"], _join(path, "value"))
    elif kind == "degree":
        if node["direction"] not in DIRECTIONS:
            _fail(WRLM_BAD_GOAL, "direction must be one of %s, got %r"
                  % (list(DIRECTIONS), node["direction"]),
                  _join(path, "direction"))
        if node["edge_kind"] is not None and node["edge_kind"] not in EDGE_KINDS:
            _fail(WRLM_BAD_GOAL, "edge_kind must be null or one of %s, got %r"
                  % (list(EDGE_KINDS), node["edge_kind"]),
                  _join(path, "edge_kind"))
        _check_count_fields(node, path)
    elif kind == "edge_kind_is":
        if node["edge_kind"] not in EDGE_KINDS:
            _fail(WRLM_BAD_GOAL, "edge_kind must be one of %s, got %r"
                  % (list(EDGE_KINDS), node["edge_kind"]),
                  _join(path, "edge_kind"))
    elif kind == "endpoint":
        if node["side"] not in SIDES:
            _fail(WRLM_BAD_GOAL, "side must be one of %s, got %r"
                  % (list(SIDES), node["side"]), _join(path, "side"))
        # an endpoint crosses the sort boundary: an EDGE filter whose child
        # ranges over the OBJECT the edge names.
        _validate_filter(node["where"], OBJECT_SORT, depth + 1, counter,
                         _join(path, "where"))


def _validate_goal(node, depth, counter, path):
    if depth > MAX_GOAL_DEPTH:
        _fail(WRLM_GOAL_BOUNDS, "depth exceeds MAX_GOAL_DEPTH=%d"
              % MAX_GOAL_DEPTH, path)
    kind = _check_shape(node, GOAL_KINDS, path)
    counter[0] += 1
    if counter[0] > MAX_GOAL_NODES:
        _fail(WRLM_GOAL_BOUNDS, "node count exceeds MAX_GOAL_NODES=%d"
              % MAX_GOAL_NODES, path)

    if kind in ("all", "any"):
        if not isinstance(node["args"], (list, tuple)):
            _fail(WRLM_BAD_GOAL, "args must be a list", _join(path, "args"))
        for i, a in enumerate(node["args"]):
            _validate_goal(a, depth + 1, counter,
                           _join(_join(path, "args"), str(i)))
    elif kind == "not":
        _validate_goal(node["arg"], depth + 1, counter, _join(path, "arg"))
    elif kind == "count":
        if node["domain"] not in DOMAINS:
            _fail(WRLM_BAD_GOAL, "domain must be one of %s, got %r"
                  % (list(DOMAINS), node["domain"]), _join(path, "domain"))
        _check_count_fields(node, path)
        sort = OBJECT_SORT if node["domain"] == "objects" else EDGE_SORT
        _validate_filter(node["where"], sort, depth + 1, counter,
                         _join(path, "where"))


def validate_goal_v1(node):
    """Raise `GoalSpecError` unless `node` is a well-formed, well-sorted,
    in-bounds GoalSpecV1. Returns None."""
    _validate_goal(node, 1, [0], None)


# ------------------------------------------------- canonicalization + identity
def _plain(v):
    """Tuples to lists, recursively. Mirrors the WRL spine's `_plain`."""
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    if isinstance(v, dict):
        return {k: _plain(x) for k, x in v.items()}
    return v


def _canon(node):
    kind = node["kind"]
    out = {"kind": kind}
    for f in NODE_FIELDS[kind]:
        if f == "kind":
            continue
        v = node[f]
        if f == "args":
            kids = [_canon(a) for a in v]
            if kind in _COMMUTATIVE:
                # Commutative AND idempotent: sort by canonical bytes, then drop
                # duplicates. This is the ONLY rewriting canonicalization does.
                seen, uniq = set(), []
                for k in sorted(kids, key=_bytes_of):
                    b = _bytes_of(k)
                    if b not in seen:
                        seen.add(b)
                        uniq.append(k)
                kids = uniq
            out[f] = kids
        elif f in ("arg", "where"):
            out[f] = _canon(v)
        else:
            out[f] = _plain(v)
    return out


def _bytes_of(node):
    return json.dumps(node, sort_keys=True, separators=(",", ":")).encode()


def canonicalize_goal_v1(node):
    """Validate, then return the canonical plain-dict form. Order and duplicates
    in commutative combinators are removed; nothing else is rewritten."""
    validate_goal_v1(node)
    return _canon(node)


def serialize_goal(node):
    """Deterministic canonical bytes. Keys sorted, tuples flattened, compact
    separators -- byte-for-byte the same discipline as `serialize_artifact`."""
    return _bytes_of(canonicalize_goal_v1(node))


def deserialize_goal(blob):
    try:
        node = json.loads(blob.decode() if isinstance(blob, bytes) else blob)
    except (ValueError, UnicodeDecodeError) as e:
        _fail(WRLM_BAD_GOAL, "goal bytes are not valid JSON: %s" % (e,), None)
    validate_goal_v1(node)
    return node


def goal_spec_id(node):
    """`goal-<sha256>` over the canonical bytes. This is the value a
    TaskBundleV1 seals into task identity (brief §4)."""
    return "goal-" + hashlib.sha256(serialize_goal(node)).hexdigest()


# ------------------------------------------------------------------ the seal
class SealedGoal(object):
    """An immutable goal: canonical BYTES plus the id derived from them. Mirrors
    `SealedArtifact` -- the bytes are the object, `.node` deserializes fresh on
    every access, and writes are refused."""

    __slots__ = ("_bytes", "_id")

    def __init__(self, node):
        object.__setattr__(self, "_bytes", serialize_goal(node))
        object.__setattr__(
            self, "_id",
            "goal-" + hashlib.sha256(self._bytes).hexdigest())

    def __setattr__(self, name, value):
        _fail(WRLM_SEALED_IMMUTABLE,
              "SealedGoal is immutable; cannot set %r" % (name,), None)

    def __delattr__(self, name):
        _fail(WRLM_SEALED_IMMUTABLE,
              "SealedGoal is immutable; cannot delete %r" % (name,), None)

    @property
    def canonical_bytes(self):
        return self._bytes

    @property
    def goal_spec_id(self):
        return self._id

    @property
    def node(self):
        """A FRESH mutable copy. Mutating it cannot affect the seal."""
        return json.loads(self._bytes.decode())

    def evaluate(self, artifact):
        return _eval_goal(self.node, _world(artifact))

    def __eq__(self, other):
        return isinstance(other, SealedGoal) and other._bytes == self._bytes

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._bytes)

    def __repr__(self):
        return "SealedGoal(%s)" % self._id


def seal_goal(node):
    return SealedGoal(node)


def open_sealed_goal(blob, expect_id=None):
    """Reopen from bytes, re-deriving the id from the bytes themselves. If
    `expect_id` is given and does not match, the goal is rejected -- a seal that
    trusted a caller-supplied id would not be a seal."""
    sealed = SealedGoal(deserialize_goal(blob))
    if expect_id is not None and sealed.goal_spec_id != expect_id:
        _fail(WRLM_BAD_GOAL, "goal id mismatch: bytes yield %s, expected %s"
              % (sealed.goal_spec_id, expect_id), None)
    return sealed


# ------------------------------------------------------------------ evaluation
class _World(object):
    """The finite bounded domain evaluation ranges over. Materialized once, up
    front -- this is the object that makes satisfaction decidable."""

    __slots__ = ("objects", "edges", "by_id")

    def __init__(self, artifact):
        art = artifact if isinstance(artifact, dict) else {}
        objs = art.get("objects") or ()
        edges = art.get("edges") or ()
        self.objects = [o for o in objs if isinstance(o, dict)]
        self.edges = [e for e in edges if isinstance(e, dict)]
        self.by_id = {}
        for o in self.objects:
            oid = o.get("object_id")
            if isinstance(oid, str):
                self.by_id.setdefault(oid, o)


def _world(artifact):
    return artifact if isinstance(artifact, _World) else _World(artifact)


def _cmp_ok(actual, cmp, n):
    if cmp == "eq":
        return actual == n
    if cmp == "ge":
        return actual >= n
    return actual <= n


def _scalar_eq(a, b):
    """Strict equality. `True == 1` in Python; on an identity spine it must not."""
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        if not (isinstance(a, (list, tuple)) and isinstance(b, (list, tuple))):
            return False
        return len(a) == len(b) and all(_scalar_eq(x, y) for x, y in zip(a, b))
    return a == b


def _degree(world, obj, direction, edge_kind):
    oid = obj.get("object_id")
    side = "src" if direction == "out" else "dst"
    total = 0
    for e in world.edges:
        if edge_kind is not None and e.get("kind") != edge_kind:
            continue
        if e.get(side) == oid:
            total += 1
    return total


def _eval_filter(node, world, elem):
    """Total: never raises on a malformed world. A goal is validated before it
    reaches here, so every `kind` below is reachable and exhaustive."""
    kind = node["kind"]
    if kind == "filter_all":
        return all(_eval_filter(a, world, elem) for a in node["args"])
    if kind == "filter_any":
        return any(_eval_filter(a, world, elem) for a in node["args"])
    if kind == "filter_not":
        return not _eval_filter(node["arg"], world, elem)
    if kind == "role_is":
        return elem.get("role") == node["role"]
    if kind == "id_is":
        return elem.get("object_id") == node["object_id"]
    if kind == "config_eq":
        cfg = elem.get("static_config")
        if not isinstance(cfg, dict) or node["field"] not in cfg:
            return False
        return _scalar_eq(_plain(cfg[node["field"]]), _plain(node["value"]))
    if kind == "degree":
        return _cmp_ok(_degree(world, elem, node["direction"], node["edge_kind"]),
                       node["cmp"], node["n"])
    if kind == "edge_kind_is":
        return elem.get("kind") == node["edge_kind"]
    # endpoint
    target = world.by_id.get(elem.get(node["side"]))
    if target is None:
        # A sealed artifact cannot have a dangling endpoint (WRL_UNKNOWN_ENDPOINT
        # rejects it upstream), but evaluation stays total regardless.
        return False
    return _eval_filter(node["where"], world, target)


def _eval_goal(node, world):
    kind = node["kind"]
    if kind == "all":
        return all(_eval_goal(a, world) for a in node["args"])
    if kind == "any":
        return any(_eval_goal(a, world) for a in node["args"])
    if kind == "not":
        return not _eval_goal(node["arg"], world)
    # count
    domain = world.objects if node["domain"] == "objects" else world.edges
    where = node["where"]
    hits = 0
    for elem in domain:
        if _eval_filter(where, world, elem):
            hits += 1
    return _cmp_ok(hits, node["cmp"], node["n"])


def evaluate_goal(node, artifact):
    """Does `artifact` satisfy `node`? Validates first; total and terminating
    thereafter. `artifact` is a plain deserialized WRL semantic artifact."""
    validate_goal_v1(node)
    return _eval_goal(node, _world(artifact))


# --------------------------------------------------------- convenience builders
# Sugar over the SAME closed AST -- these emit ordinary nodes and add no
# expressive power whatsoever. They exist so task generators read clearly.
def exists(domain, where):
    return {"kind": "count", "domain": domain, "where": where,
            "cmp": "ge", "n": 1}


def forall(domain, where):
    return {"kind": "count", "domain": domain,
            "where": {"kind": "filter_not", "arg": where},
            "cmp": "eq", "n": 0}


def exactly(domain, where, n):
    return {"kind": "count", "domain": domain, "where": where,
            "cmp": "eq", "n": n}


def none(domain, where):
    return exactly(domain, where, 0)


def wired(edge_kind, src_where, dst_where):
    """At least one `edge_kind` edge from an object matching `src_where` to an
    object matching `dst_where`."""
    return exists("edges", {"kind": "filter_all", "args": [
        {"kind": "edge_kind_is", "edge_kind": edge_kind},
        {"kind": "endpoint", "side": "src", "where": src_where},
        {"kind": "endpoint", "side": "dst", "where": dst_where},
    ]})


def role(name):
    return {"kind": "role_is", "role": name}
