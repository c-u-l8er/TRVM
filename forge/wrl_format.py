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

# canonical lowering vocab (reverse of wrl_ir's parse tables)
_ROLE_LOWER = {"Pulser": "pulser", "Relay": "relay", "Door": "door",
               "Spinner": "spinner", "Orb": "orb"}
_EDGE_LOWER = {"SignalWire": "sig", "SocketControl": "socket"}


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
    return "\n".join(out) + "\n"


# back-compat alias (the canvas module historically owned this name)
graph_to_wrl_core = format_wrl_core


def format_source(src, parser=W.parse_wrl_core):
    """Convenience: parse `src` with `parser` (WRL Core by default; pass
    `wrl_ir.parse_wrl_bootstrap` for the bootstrap DSL) and emit canonical WRL
    Core text. Because both surfaces lower to the SAME canonical graph, the
    formatter erases the surface distinction."""
    return format_wrl_core(parser(src))
