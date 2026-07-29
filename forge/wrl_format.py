"""wrl_format.py v0.1 -- Phase 3B-2: the canonical WRL Core formatter.

GPT-5.6's 3B priority ruling leads broad 3B with "canonical formatter + source
spans". 3B-1 shipped the span sidecar (wrl_spans.py); 3B-2 is the formatter.

`format_wrl_core(graph)` renders a canonical WRL graph as WRL Core process
notation -- the actual surface (`[role:name](k=v){ports}`, `[a] --tag--> [b]`,
`[epoch:N] @w,s Op args`), never the bootstrap DSL. It CANONICALIZES first, so
formatting is a pure function of the semantic graph: declaration order, surface
choice, and source whitespace all wash out.

Laws (proven in binding_run9, L1-L10):

  * parse_wrl_core(format(graph)) == graph                 (round-trip)
  * format(parse(format(src)))    == format(src)           (idempotent/stable)
  * formatting-only edits          ==> same SemanticArtifactID

Ports are emitted from the frozen role registry (`port_projection`), never
invented, so a formatted node can never contradict its role signature. This
module is the authoritative home of the emitter; `wrl_canvas.graph_to_wrl_core`
re-exports `format_wrl_core` for back-compat.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wrl_canonical as WC
import wrl_ir as W

FORMAT_VERSION = "wrlfmt.v1"

# The emitter vocabulary is the parse tables INVERTED, not retyped.
#
# These two were hand-written mirrors of `wrl_ir._ROLE_TOKEN` / `_EDGE_TAG`.
# That is the same defect the L-0 round found four times and §18 names: a
# second spelling of one definition, which does not stay a copy. It was already
# live -- adding `mailbox` to the Core surface would have left this table one
# entry short, and the failure mode is a `KeyError` from inside the formatter
# on a world that parses, seals and runs perfectly well.
#
# Inverting is safe precisely because the forward tables are injective (each
# role has at most one lexeme); if that ever stops being true the inversion
# silently picks one, so the assertion below states the assumption rather than
# trusting it. `wrl_complete` already inverts `_ROLE_TOKEN` this way -- this
# module was simply the copy that had not been converted yet.
_ROLE_LOWER = {rid: tok for tok, rid in W._ROLE_TOKEN.items()}
_EDGE_LOWER = {kind: tag for tag, kind in W._EDGE_TAG.items()}
assert len(_ROLE_LOWER) == len(W._ROLE_TOKEN), "role lexemes are not injective"
assert len(_EDGE_LOWER) == len(W._EDGE_TAG), "edge tags are not injective"


def _emit_cfg(role, cfg):
    if role == "Pulser":
        clock = cfg["clock"]
        if clock[0] == "periodic":
            return "(mode=periodic, period=%d, phase=%d)" % (clock[1], clock[2])
        return "(mode=once, epoch=%d)" % (clock[1],)
    if role == "Spinner":
        rotor = ".".join(str(int(x)) for x in cfg["rotor"])
        items = ["w=%d" % cfg["w"], "n=%d" % cfg["n"], "rotor=%s" % rotor]
        if cfg.get("configurable"):
            items.append("configurable")
        return "(%s)" % ", ".join(items)
    if role == WC.MAILBOX_ROLE:
        # Both keys always, in declaration order -- never "omit cap when it
        # happens to be 1". A default that the emitter knows and the surface
        # does not is how an identity-bearing field goes missing from the one
        # artifact a human reads.
        return "(w=%d, cap=%d)" % (cfg["w"], cfg["cap"])
    return ""


def format_wrl_core(g):
    """Canonical WRL graph -> canonical WRL Core notation text. Canonicalizes
    first, so the output is a pure function of the semantic graph. Re-parsing
    the result with `wrl_ir.parse_wrl_core` yields the same canonical graph (and
    identical artifact bytes). Ports are emitted from the frozen role registry,
    never invented.

    v0.4-0 (GPT-5.6): canonical WORLD formatting omits RUN INPUTS -- the
    `periods N` run-duration line and inline `[epoch:N]` claim batches are NOT
    emitted, because those now belong to ScenarioV1, not the world source. The
    parser still ACCEPTS a legacy `periods` line + inline claims for
    compatibility; the formatter just no longer produces them. Run inputs never
    entered the SemanticArtifactID (D3), so omitting them is identity-preserving:
    the emitted text re-parses to the same canonical graph and the same sealed
    bytes."""
    cg = WC.canonicalize_graph(g)
    out = ["profile %s" % cg.profile, ""]
    for role, name, cfg in cg.nodes:
        ports = "{%s}" % ", ".join(sorted(WC.port_projection(role)))
        out.append("[%s:%s]%s%s"
                   % (_ROLE_LOWER[role], name, _emit_cfg(role, cfg), ports))
    out.append("")
    for kind, s, d in cg.edges:
        out.append("[%s] --%s--> [%s]" % (s, _EDGE_LOWER[kind], d))
    # Slice B commit 3: routes emit AFTER the edges, in canonical RouteKey order
    # (`canonicalize_graph` already sorted them). A route-free world therefore
    # emits EXACTLY the pre-Slice-B text -- no blank separator, no empty
    # section -- so no existing world's formatted bytes move.
    #
    # A route is not folded in among the edges even though it reads like one,
    # because sorting a route into edge order would require one comparison key
    # spanning two vocabularies (EdgeKey and RouteKey), and the two orderings
    # are canonical for different reasons: an edge's order is presentational,
    # while a route's order IS its minted ADMIT `sequence` (Q4). Interleaving
    # them would make an identity-bearing order look like a formatting choice.
    routes = WC.routes_of(cg)
    if routes:
        out.append("")
        for r in routes:
            out.append("[%s] ~~%s~~> [%s] (body=%s)"
                       % (r["source_id"], r["route_tag"], r["mailbox_id"],
                          _emit_body(r["body"])))
    return "\n".join(out) + "\n"


def _emit_body(body):
    """The four route body lanes, dot-separated -- the exact spelling
    `wrl_ir._body_dots` parses. Arity is not asserted here: the emitter renders
    whatever canonical form it was handed, and a body of the wrong arity cannot
    reach a canonical graph (`_validate_routes` rejects it at the seal). A
    length check here would be a second place that decides what a body is."""
    return ".".join(str(int(v)) for v in body)


# back-compat alias (the canvas module historically owned this name)
graph_to_wrl_core = format_wrl_core


def format_source(src, parser=W.parse_wrl_core):
    """Convenience: parse `src` with `parser` (WRL Core by default; pass
    `wrl_ir.parse_wrl_bootstrap` for the bootstrap DSL) and emit canonical WRL
    Core text. Because both surfaces lower to the SAME canonical graph, the
    formatter erases the surface distinction."""
    return format_wrl_core(parser(src))
