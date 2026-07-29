"""wrl_canvas.py v0.1 -- CanvasGraphV1: the presentation surface (Phase 3C-1).

GPT-5.6's Phase 3C ruling: build CanvasGraphV1 as presentation metadata AROUND
-- not inside -- the canonical WRL graph, and prove that text, bootstrap and
canvas surfaces converge on the same artifact and runtime films.

The canvas document is a self-contained visual projection of a canonical WRL
graph. Every item carries TWO kinds of fields, kept in strictly separate places
so the boundary is structural (not merely a convention):

  * SEMANTIC (top level of each node/connection): the ONLY fields that can
    reach the SemanticArtifactID -- object_id, role, static_config (nodes);
    kind, src, dst (connections). Ports are NOT stored: they derive from the
    frozen role registry, so a canvas can never contradict a role's signature.
  * PRESENTATION (under the `presentation` key): x/y/width/height/color/
    label_style/collapsed/layer (nodes); control_points/line_length/
    texture_style/paint/label_position (connections). This block is generated
    as a deterministic default layout and is NEVER read back by
    `canvas_to_graph` -- moving a node, recoloring an edge, or corrupting the
    whole presentation block cannot change the artifact identity.

Conversions:

    graph_to_canvas(g)     canonical WRL graph -> CanvasGraphV1 (default layout)
    canvas_to_graph(canvas) CanvasGraphV1 -> canonical WRL graph (semantic only)
    graph_to_wrl_core(g)   canonical WRL graph -> WRL process-notation text
                           (re-parses via wrl_ir.parse_wrl_core identically)
    lower_canvas(canvas)   CanvasGraphV1 -> LoweredProgram (shared lower_graph)

`canvas_to_graph` reads ONLY the semantic keys; presentation is structurally
unreachable from the lowering path (Phase 3C V9). The legacy `canvas.v1` format
also carried run inputs (periods + claim batches) so a canvas could reconstruct
the runtime film; they never entered the SemanticArtifactID (D3/C3).

v0.4-0 (GPT-5.6): run inputs are now OBSOLETE in the presentation surface --
ScenarioV1 owns them. The new `CanvasLayoutV1` (`canvas-layout.v1`,
`graph_to_layout` / `validate_layout_v1`, below) is PURE PRESENTATION keyed by
object_id / edge_key, with NO periods, NO batches, NO static_config. The
`canvas.v1` functions here are RETAINED as a compatibility loader, and
`layout_from_canvas_v1` projects an old canvas down to the new layout, dropping
the run inputs.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wrl_canonical as WC
import wrl_ir as W
# Phase 3B-2: the canonical WRL Core formatter now lives in wrl_format; canvas
# re-exports graph_to_wrl_core for back-compat (its historical home).
from wrl_format import format_wrl_core, graph_to_wrl_core

CANVAS_VERSION = "canvas.v1"

# presentation-only palettes (semantically inert)
_ROLE_COLOR = {"Pulser": "#f4a259", "Relay": "#8cb369", "Door": "#5b8e7d",
               "Spinner": "#bc4b51", "Orb": "#4d5061"}
_WIRE_PAINT = {"SignalWire": "#f4d35e", "SocketControl": "#ee6c4d"}


# --------------------------------------------------- presentation defaults
def _node_presentation(i, role):
    """A deterministic default node box (grid by canonical index). Purely
    visual -- none of this is ever read back into the graph."""
    col, row = i % 4, i // 4
    return {"x": 80 + col * 200, "y": 80 + row * 140,
            "width": 140, "height": 90,
            "color": _ROLE_COLOR.get(role, "#999999"),
            "label_style": "default", "collapsed": False, "layer": 0}


def _conn_presentation(kind):
    """A deterministic default connection style. Purely visual."""
    return {"control_points": [], "line_length": 0, "texture_style": "solid",
            "paint": _WIRE_PAINT.get(kind, "#888888"), "label_position": "mid"}


# ------------------------------------------------------- semantic coercion
# The frozen v1 static_config field allowlist per role -- the ONLY semantic
# config keys IR v1 recognizes. Anything else is a typed rejection (3D-0), so
# an unknown static_config field can never silently ride into (or silently fail
# to move) the SemanticArtifactID.
_CFG_KEYS = {"Pulser": {"clock"},
             "Spinner": {"w", "n", "rotor", "configurable"},
             "Relay": set(), "Door": set(), "Orb": set()}


def _coerce_cfg(role, sc):
    """Rebuild the EXACT typed static_config a parser would produce, from the
    canvas's JSON-plain form (lists -> tuples). Reads only the frozen semantic
    config fields; an UNKNOWN key is a typed WRL_UNSUPPORTED_FEATURE rejection
    (3D-0), never a silent discard."""
    if not isinstance(sc, dict):
        WC._fail(WC.WRL_MALFORMED_ARTIFACT,
                 "static_config for role %s must be an object" % role)
    allowed = _CFG_KEYS.get(role, set())
    extra = sorted(set(sc) - allowed)
    if extra:
        WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                 "unknown static_config field(s) %s for role %s (frozen IR v1 "
                 "allows %s)" % (extra, role, sorted(allowed) or "{}"))
    if role == "Pulser":
        return {"clock": tuple(sc["clock"])}
    if role == "Spinner":
        rotor = sc.get("rotor")
        return {"w": sc.get("w"), "n": sc.get("n"),
                "rotor": tuple(rotor) if rotor is not None else None,
                "configurable": bool(sc.get("configurable", False))}
    return {}


def _coerce_payload(p):
    p = list(p)
    if p[0] == "SetRotor":
        return ("SetRotor", p[1], tuple(int(x) for x in p[2]))
    if p[0] == "ResetFault":
        return ("ResetFault", p[1])
    return tuple(p)


# --------------------------------------------------------- graph -> canvas
def graph_to_canvas(g):
    """Canonical WRL graph -> CanvasGraphV1. The graph is canonicalized first
    so the default layout is a pure function of identity (declaration order
    cannot change the produced canvas)."""
    cg = WC.canonicalize_graph(g)
    # NOTE (Slice B): this emitter has no route gate, for exactly the reason
    # binding_run46 N10c records about the Mailbox role -- canvas.v1 is retired
    # and FROZEN (§15.1.1 point 1), and adding a rejection to it would be a
    # behaviour change to a frozen module. A route gate was written here and
    # then REMOVED on that ground: the sanctioned door
    # (`wrl_legacy.export_canvas_graph_v1`) already refuses, and it refuses by
    # a COMPUTED round-trip rather than by naming a construct, so it needed no
    # edit at all to learn about routes. binding_run47 P9 states that, and
    # states honestly which of the two losses fires first.
    nodes = []
    for i, (role, name, cfg) in enumerate(cg.nodes):
        nodes.append({"object_id": name, "role": role,
                      "static_config": WC._plain(cfg),
                      "presentation": _node_presentation(i, role)})
    conns = []
    for kind, s, d in cg.edges:
        conns.append({"kind": kind, "src": s, "dst": d,
                      "presentation": _conn_presentation(kind)})
    batches = [[{"writer_id": c["writer_id"], "sequence": c["sequence"],
                 "payload": WC._plain(c["payload"])} for c in batch]
               for batch in cg.batches]
    return {"canvas_version": CANVAS_VERSION,
            "profile_id": cg.profile,
            "periods": cg.periods,
            "nodes": nodes,
            "connections": conns,
            "batches": batches}


# ------------------------------------------------------- strict canvas gate
_CANVAS_TOP = {"canvas_version", "profile_id", "periods", "nodes",
               "connections", "batches"}
_NODE_SEM = {"object_id", "role", "static_config"}
_CONN_SEM = {"kind", "src", "dst"}
_CLAIM_KEYS = {"writer_id", "sequence", "payload"}


def validate_canvas_v1(canvas):
    """Strict structural gate (Phase 3D-0). Rejects UNKNOWN SEMANTIC fields at
    every level -- top-level canvas, node, connection, static_config, and claim
    -- while the `presentation` block alone stays OPEN and inert (arbitrary keys
    allowed there). Because the semantic keys are exactly the ones that reach
    the SemanticArtifactID, an unknown semantic key or a profile mismatch can
    never silently ride into (or silently fail to move) the identity. Returns
    the canvas unchanged on success; raises a typed WrlValidationError."""
    if not isinstance(canvas, dict):
        WC._fail(WC.WRL_MALFORMED_ARTIFACT, "canvas must be an object")
    if canvas.get("canvas_version") != CANVAS_VERSION:
        WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                 "unknown canvas version %r (only %s)"
                 % (canvas.get("canvas_version"), CANVAS_VERSION))
    extra = sorted(set(canvas) - _CANVAS_TOP)
    if extra:
        WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                 "unknown canvas field(s) %s (frozen canvas.v1 allows %s)"
                 % (extra, sorted(_CANVAS_TOP)))
    prof = canvas.get("profile_id", WC.PROFILE_ID)
    if prof != WC.PROFILE_ID:
        WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                 "canvas profile %r != frozen %s" % (prof, WC.PROFILE_ID))
    if not isinstance(canvas.get("periods"), int) or canvas["periods"] < 0:
        WC._fail(WC.WRL_MALFORMED_ARTIFACT,
                 "periods must be a non-negative int")
    for n in canvas.get("nodes", []):
        if not isinstance(n, dict):
            WC._fail(WC.WRL_MALFORMED_ARTIFACT, "node must be an object")
        sem = set(n) - {"presentation"}
        if sem - _NODE_SEM:
            WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                     "unknown node semantic field(s) %s (allowed %s + "
                     "presentation)"
                     % (sorted(sem - _NODE_SEM), sorted(_NODE_SEM)))
        if not _NODE_SEM <= set(n):
            WC._fail(WC.WRL_MALFORMED_ARTIFACT,
                     "node missing semantic field(s) %s"
                     % sorted(_NODE_SEM - set(n)))
        if n["role"] not in _CFG_KEYS:
            # This gate reads `_CFG_KEYS` -- canvas.v1's OWN role table -- not
            # `WC.ROLE_IDS`. The two are not equal and the message must not
            # pretend they are: it used to say the role was "not in the frozen
            # v1 registry", which is FALSE for `Mailbox`, a registry role with
            # ports and a config schema that this retired surface simply has no
            # column for. That is the §18 defect verbatim (a rejection denying
            # the existence of a role the registry defines), found a fifth time
            # while building the Slice B importer. Correcting a message that
            # states a falsehood is not an extension of the frozen surface.
            unrepresentable = n["role"] in WC.ROLE_IDS
            WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                     ("role %r is in the frozen v1 registry but has no "
                      "canvas.v1 representation (canvas.v1 is retired; its "
                      "role table is a frozen subset)" if unrepresentable
                      else "role %r is not in the frozen v1 registry")
                     % (n["role"],))
        _coerce_cfg(n["role"], n["static_config"])   # strict field check
    for c in canvas.get("connections", []):
        if not isinstance(c, dict):
            WC._fail(WC.WRL_MALFORMED_ARTIFACT, "connection must be an object")
        sem = set(c) - {"presentation"}
        if sem - _CONN_SEM:
            WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                     "unknown connection semantic field(s) %s (allowed %s + "
                     "presentation)"
                     % (sorted(sem - _CONN_SEM), sorted(_CONN_SEM)))
        if not _CONN_SEM <= set(c):
            WC._fail(WC.WRL_MALFORMED_ARTIFACT,
                     "connection missing semantic field(s) %s"
                     % sorted(_CONN_SEM - set(c)))
    for batch in canvas.get("batches", []):
        for cl in batch:
            if not isinstance(cl, dict) or (set(cl) - _CLAIM_KEYS):
                bad = sorted(set(cl) - _CLAIM_KEYS) if isinstance(cl, dict) \
                    else repr(cl)
                WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                         "unknown/malformed claim field(s) %s (allowed %s)"
                         % (bad, sorted(_CLAIM_KEYS)))
    return canvas


# --------------------------------------------------------- canvas -> graph
def canvas_to_graph(canvas):
    """CanvasGraphV1 -> canonical WRL graph. Runs the strict 3D-0 gate first,
    then reads ONLY the semantic keys of each node/connection; the
    `presentation` block is never consulted, so no visual field can influence
    the resulting graph or its identity."""
    validate_canvas_v1(canvas)
    g = W.WrlGraph()
    g.profile = canvas.get("profile_id", WC.PROFILE_ID)
    g.periods = canvas["periods"]
    g.batches = [[] for _ in range(g.periods)]
    try:
        for n in canvas["nodes"]:
            role, name = n["role"], n["object_id"]
            g.nodes.append((role, name, _coerce_cfg(role, n["static_config"])))
        for c in canvas["connections"]:
            g.edges.append((c["kind"], c["src"], c["dst"]))
        for e, batch in enumerate(canvas.get("batches", [])):
            for c in batch:
                g.batches[e].append(
                    {"writer_id": c["writer_id"], "sequence": c["sequence"],
                     "payload": _coerce_payload(c["payload"])})
    except (KeyError, TypeError, IndexError) as ex:
        WC._fail(WC.WRL_MALFORMED_ARTIFACT, "malformed canvas record: %r" % (ex,))
    return g


# -------------------------------------------------------- graph -> WRL text
# ------------------------------------------------------------- lower canvas
def lower_canvas(canvas):
    """CanvasGraphV1 -> LoweredProgram, through the SAME lower_graph seam every
    text surface uses -- so a canvas and its text twin produce identical
    artifact bytes and runtime films (Phase 3C)."""
    return W.lower_graph(canvas_to_graph(canvas))


# =================================================== CanvasLayoutV1 (v0.4-0)
# GPT-5.6 v0.4-0 ruling #1: run inputs (periods + claim batches) are OBSOLETE in
# the presentation surface -- ScenarioV1 owns them. The new CanvasLayoutV1 is
# PURE PRESENTATION, keyed by object_id / edge_key, carrying NO periods, NO
# batches, NO static_config, NO initial faults, NO runtime state. Layout and
# semantics are separate documents (WorldDraftV1 owns objects/config/topology).
# The legacy `canvas.v1` functions above are RETAINED as a compatibility loader.
LAYOUT_VERSION = "canvas-layout.v1"

_LAYOUT_TOP = {"layout_version", "profile_id", "nodes", "edges"}
_LAYOUT_NODE = {"object_id", "presentation"}
_LAYOUT_EDGE = {"edge_key", "presentation"}


def edge_key(kind, src, dst):
    """Stable presentation key for an edge (kind + endpoints). CanvasLayoutV1
    references edges by this key rather than duplicating the semantic triple."""
    return "%s:%s->%s" % (kind, src, dst)


def graph_to_layout(g):
    """Canonical WRL graph -> CanvasLayoutV1: PRESENTATION ONLY. Keyed by
    object_id (nodes) and edge_key (edges); carries NO run inputs and NO
    semantic config -- those live in ScenarioV1 / WorldDraftV1. The default
    layout is a pure function of identity (canonicalize first), so declaration
    order cannot change the produced layout."""
    cg = WC.canonicalize_graph(g)
    nodes = [{"object_id": name, "presentation": _node_presentation(i, role)}
             for i, (role, name, _cfg) in enumerate(cg.nodes)]
    edges = [{"edge_key": edge_key(kind, s, d),
              "presentation": _conn_presentation(kind)}
             for kind, s, d in cg.edges]
    return {"layout_version": LAYOUT_VERSION,
            "profile_id": cg.profile,
            "nodes": nodes, "edges": edges}


def validate_layout_v1(layout):
    """Strict gate for a CanvasLayoutV1. Rejects run inputs (periods/batches) and
    semantic config anywhere -- those are UNKNOWN fields here -- while the
    `presentation` block alone stays OPEN and inert. Returns the layout on
    success; raises a typed WrlValidationError. This is what makes battery E1
    structural: a CanvasLayout can never smuggle periods/batches/static_config."""
    if not isinstance(layout, dict):
        WC._fail(WC.WRL_MALFORMED_ARTIFACT, "layout must be an object")
    if layout.get("layout_version") != LAYOUT_VERSION:
        WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                 "unknown layout version %r (only %s)"
                 % (layout.get("layout_version"), LAYOUT_VERSION))
    extra = sorted(set(layout) - _LAYOUT_TOP)
    if extra:
        WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                 "unknown layout field(s) %s (frozen canvas-layout.v1 allows %s; "
                 "run inputs belong to ScenarioV1, not the layout)"
                 % (extra, sorted(_LAYOUT_TOP)))
    prof = layout.get("profile_id", WC.PROFILE_ID)
    if prof != WC.PROFILE_ID:
        WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                 "layout profile %r != frozen %s" % (prof, WC.PROFILE_ID))
    for n in layout.get("nodes", []):
        if not isinstance(n, dict) or (set(n) - _LAYOUT_NODE):
            bad = sorted(set(n) - _LAYOUT_NODE) if isinstance(n, dict) else n
            WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                     "unknown/malformed layout node field(s) %r (allowed %s)"
                     % (bad, sorted(_LAYOUT_NODE)))
        if "object_id" not in n:
            WC._fail(WC.WRL_MALFORMED_ARTIFACT, "layout node missing object_id")
    for e in layout.get("edges", []):
        if not isinstance(e, dict) or (set(e) - _LAYOUT_EDGE):
            bad = sorted(set(e) - _LAYOUT_EDGE) if isinstance(e, dict) else e
            WC._fail(WC.WRL_UNSUPPORTED_FEATURE,
                     "unknown/malformed layout edge field(s) %r (allowed %s)"
                     % (bad, sorted(_LAYOUT_EDGE)))
        if "edge_key" not in e:
            WC._fail(WC.WRL_MALFORMED_ARTIFACT, "layout edge missing edge_key")
    return layout


def layout_from_canvas_v1(old_canvas):
    """Compatibility loader: project a legacy `canvas.v1` document down to the
    presentation-only CanvasLayoutV1, DROPPING its run inputs (periods/batches)
    and semantic config -- those migrate to ScenarioV1 / WorldDraftV1. The
    node/edge presentation blocks are preserved verbatim; the returned layout
    passes `validate_layout_v1`."""
    validate_canvas_v1(old_canvas)
    nodes = [{"object_id": n["object_id"],
              "presentation": n.get("presentation", {})}
             for n in old_canvas.get("nodes", [])]
    edges = [{"edge_key": edge_key(c["kind"], c["src"], c["dst"]),
              "presentation": c.get("presentation", {})}
             for c in old_canvas.get("connections", [])]
    return {"layout_version": LAYOUT_VERSION,
            "profile_id": old_canvas.get("profile_id", WC.PROFILE_ID),
            "nodes": nodes, "edges": edges}
