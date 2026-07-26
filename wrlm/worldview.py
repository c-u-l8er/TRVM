"""WorldViewV1 -- the ONE adapter between the Forge engine and WRLM.

WRLM evaluates `GoalSpecV1` over a world's finite object and edge sets. Those
sets can arrive from two places, and they are NOT the same shape:

  * `forge_api.lower_source(src)` -> LowerResultV1, whose `graph.nodes[*]` key
    the object as **`id`**, and which carries `ports` but not
    `state_schema_ref`.
  * a canonical semantic artifact, whose `objects[*]` key it as **`object_id`**.

Accepting both shapes inside the evaluator would be the beginning of an
identity bug: two spellings of "the same" world, silently interchangeable, is
exactly the ambiguity the `sem-` spine exists to prevent. So the rename happens
HERE, once, explicitly, under test -- and `goalspec` keeps reading exactly one
shape.

This module is the only place in `wrlm/` that knows anything about the engine's
payload format, and it still imports nothing from `forge/`: it consumes a
LowerResultV1 that a caller obtained, so `wrlm/` remains independently
importable and testable against vendored fixtures.

A view always carries `semantic_id`, so a set of objects is never floating free
of the sealed world it came from. That identity is **derived**, never accepted
on a caller's word -- see `from_artifact`.

This module is a verifier, and verifiers are attack surface. The hardening here
(closed containers, no silent dropping, derived identity, typed rejections) is
deliberate and predates any generator: bugs in a reward verifier get *learned*
by whatever trains against it, so they have to be closed before the first task
exists, not after.
"""

import hashlib
import json

from .errors import WrlmError, fail

WORLD_VIEW_VERSION = "wrlm.worldview.v1"

# The engine payload version this adapter is written against. Pinned on purpose:
# if the engine bumps its contract, the adapter must FAIL LOUDLY rather than
# quietly mis-evaluate a goal against a shape it no longer understands.
ACCEPTS_LOWER_RESULT_VERSION = "forge.lower-result.v1"

WRLM_BAD_WORLD_VIEW = "WRLM_BAD_WORLD_VIEW"          # malformed / wrong version
WRLM_WORLD_NOT_LOWERED = "WRLM_WORLD_NOT_LOWERED"    # ok:False -- no world to view

_SEM_PREFIX = "sem-"
_SEM_HEXLEN = 64


def is_semantic_id(v):
    return (isinstance(v, str) and v.startswith(_SEM_PREFIX)
            and len(v) == len(_SEM_PREFIX) + _SEM_HEXLEN
            and all(c in "0123456789abcdef" for c in v[len(_SEM_PREFIX):]))


class NotLoweredError(WrlmError):
    """The engine rejected the source, so there is no world to view. Carries the
    engine's own typed diagnostics -- WRLM never re-derives or paraphrases them
    (brief §3 law 2: every rejection keeps its typed code)."""

    def __init__(self, message, diagnostics):
        WrlmError.__init__(self, WRLM_WORLD_NOT_LOWERED, message)
        self.diagnostics = list(diagnostics or ())


def _view(semantic_id, objects, edges):
    return {"world_view_version": WORLD_VIEW_VERSION,
            "semantic_id": semantic_id,
            "objects": objects,
            "edges": edges}


def _check_list(v, path):
    """A container that is not a list is a REJECTION, not something to coerce.

    `or ()` would turn `objects: 1` into an empty world -- a corrupt artifact
    silently becoming a small valid-looking one. On a verifier that is a
    false-positive generator: a goal like "no Spinner exists" would pass."""
    if not isinstance(v, list):
        fail(WRLM_BAD_WORLD_VIEW, "must be a list, got %s"
             % type(v).__name__, path)
    return v


def is_world_view(v):
    """Does this carry world *identity*, or is it just objects and edges?

    Callers that need to compare against a target `sem-` must be able to tell
    the difference, because a bare artifact silently answers "no" to every
    identity question."""
    return (isinstance(v, dict)
            and v.get("world_view_version") == WORLD_VIEW_VERSION
            and is_semantic_id(v.get("semantic_id")))


def from_lower_result(payload):
    """LowerResultV1 -> WorldViewV1.

    Raises `NotLoweredError` (carrying the engine's diagnostics) when the source
    did not lower. Invalid WRL is a data outcome at the engine boundary; it
    becomes a typed rejection here so a caller cannot accidentally evaluate a
    goal against a world that does not exist."""
    if not isinstance(payload, dict):
        fail(WRLM_BAD_WORLD_VIEW, "LowerResult must be an object, got %s"
             % type(payload).__name__)
    rv = payload.get("result_version")
    if rv != ACCEPTS_LOWER_RESULT_VERSION:
        fail(WRLM_BAD_WORLD_VIEW,
             "unsupported engine payload %r; this adapter is written against %r"
             % (rv, ACCEPTS_LOWER_RESULT_VERSION), "result_version")
    if not payload.get("ok"):
        raise NotLoweredError(payload.get("error") or "source did not lower",
                              payload.get("diagnostics"))

    sem = payload.get("semantic_artifact_id")
    if not is_semantic_id(sem):
        fail(WRLM_BAD_WORLD_VIEW, "not a semantic artifact id: %r" % (sem,),
             "semantic_artifact_id")
    graph = payload.get("graph")
    if not isinstance(graph, dict):
        fail(WRLM_BAD_WORLD_VIEW, "graph must be an object", "graph")

    objects = []
    for i, n in enumerate(_check_list(graph.get("nodes"), "graph.nodes")):
        if not isinstance(n, dict):
            fail(WRLM_BAD_WORLD_VIEW, "node must be an object",
                 "graph.nodes.%d" % i)
        if "id" not in n:
            fail(WRLM_BAD_WORLD_VIEW, "node has no `id`", "graph.nodes.%d" % i)
        # THE RENAME. LowerResultV1 says `id`; the artifact -- and therefore
        # GoalSpecV1's `id_is` -- says `object_id`.
        objects.append({"object_id": n["id"],
                        "role": n.get("role"),
                        "static_config": n.get("static_config") or {}})
    edges = []
    for i, e in enumerate(_check_list(graph.get("edges"), "graph.edges")):
        if not isinstance(e, dict):
            fail(WRLM_BAD_WORLD_VIEW, "edge must be an object",
                 "graph.edges.%d" % i)
        edges.append({"kind": e.get("kind"), "src": e.get("src"),
                      "dst": e.get("dst")})
    return _view(sem, objects, edges)


def from_artifact(artifact, semantic_id=None):
    """Canonical semantic artifact -> WorldViewV1. No rename needed; this path
    exists so a stored artifact and a freshly lowered source produce the SAME
    view shape.

    The identity is **DERIVED from the artifact's own bytes**. `semantic_id` is
    an optional *assertion*: supply it and a mismatch is refused; omit it and
    the derived value is used. It is never simply believed.

    This is the difference between a view and a claim. A trusted `semantic_id`
    would let `{"objects": [], "edges": []}` present itself as any world in the
    corpus -- and since a target-bearing task is scored by comparing `sem-`,
    that is a direct false-positive path: an empty world claiming to be the
    solution."""
    if not isinstance(artifact, dict):
        fail(WRLM_BAD_WORLD_VIEW, "artifact must be an object, got %s"
             % type(artifact).__name__)
    if semantic_id is not None and not is_semantic_id(semantic_id):
        fail(WRLM_BAD_WORLD_VIEW, "not a semantic artifact id: %r"
             % (semantic_id,), "semantic_id")

    objects = []
    for i, o in enumerate(_check_list(artifact.get("objects"), "objects")):
        # Filtering non-dict members (the old behaviour) would let a corrupt
        # artifact shrink into a smaller world that still validates.
        if not isinstance(o, dict):
            fail(WRLM_BAD_WORLD_VIEW, "object must be an object, got %s"
                 % type(o).__name__, "objects.%d" % i)
        objects.append({"object_id": o.get("object_id"), "role": o.get("role"),
                        "static_config": o.get("static_config") or {}})
    edges = []
    for i, e in enumerate(_check_list(artifact.get("edges"), "edges")):
        if not isinstance(e, dict):
            fail(WRLM_BAD_WORLD_VIEW, "edge must be an object, got %s"
                 % type(e).__name__, "edges.%d" % i)
        edges.append({"kind": e.get("kind"), "src": e.get("src"),
                      "dst": e.get("dst")})

    derived = semantic_id_of_artifact(artifact)
    if semantic_id is not None and semantic_id != derived:
        fail(WRLM_BAD_WORLD_VIEW,
             "artifact derives %s but %s was claimed" % (derived, semantic_id),
             "semantic_id")
    return _view(derived, objects, edges)


def semantic_id_of_artifact(artifact):
    """Re-derive `sem-` from an artifact's own canonical bytes.

    `sem-` is sha256 over exactly `json.dumps(artifact, sort_keys=True,
    separators=(",",":"))`, so a consumer can verify a stored artifact without
    importing the layer that produced it. This is a VERIFIER, not a sealer: it
    does not validate or canonicalize, so it is only meaningful on bytes that
    the forge spine already canonicalized. An artifact carrying an extra key, or
    otherwise off the canonical form, derives a DIFFERENT id -- which is the
    correct outcome: it is a different artifact."""
    try:
        blob = json.dumps(artifact, sort_keys=True,
                          separators=(",", ":")).encode()
    except (TypeError, ValueError) as exc:
        fail(WRLM_BAD_WORLD_VIEW,
             "artifact is not JSON-serializable, so it has no canonical bytes "
             "and therefore no identity: %s" % exc)
    return _SEM_PREFIX + hashlib.sha256(blob).hexdigest()
