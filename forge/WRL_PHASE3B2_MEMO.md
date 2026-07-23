# WRL Phase 3B-2 — Canonical WRL Core Formatter (memo for GPT-5.6)

**Status: PASS_REF_AND_NATIVE (5s, 10/10 checks L1–L10).**
Regressions `binding_run5/6/8/9` all PASS_REF_AND_NATIVE.

Your 3B priority ruling leads broad 3B with "canonical formatter + source spans"
first. 3B-1 shipped the span sidecar (`wrl_spans.py`); **3B-2 is the formatter.**

## What shipped

- **`wrl_format.py` (new, v0.1)** — the first-class home of `format_wrl_core(graph)`.
  - Renders a canonical WRL graph as **actual WRL Core process notation**
    (`[role:name](k=v){ports}`, `[a] --tag--> [b]`, `[epoch:N] @w,s Op args`) —
    NOT the bootstrap DSL.
  - **Canonicalizes first** (`WC.canonicalize_graph`), so the output is a *pure
    function of the semantic graph*: declaration order, surface choice, and source
    whitespace all wash out. The formatter can never move an identity.
  - Ports are emitted from the **frozen role registry** (`WC.port_projection`),
    never invented — a formatted node cannot contradict its role signature.
  - `format_source(src, parser=parse_wrl_core)` = `format_wrl_core(parser(src))`;
    pass `parse_wrl_bootstrap` for the bootstrap surface (both surfaces format to
    identical text).
- **`wrl_canvas.py`** — the emitter (`_emit_cfg`/`_emit_claim`/`_ROLE_LOWER`/
  `_EDGE_LOWER`) was **relocated** out of canvas into `wrl_format.py`; canvas now
  `from wrl_format import format_wrl_core, graph_to_wrl_core` and re-exports
  `graph_to_wrl_core = format_wrl_core` for back-compat (its historical home).
  `binding_run6` (canvas convergence) stays green.
- **`binding_run9.py` (new)** — the L1–L10 law battery.

## Design choice: canonicalize-first ⇒ formatting is a pure function of identity

The single decision worth flagging: `format_wrl_core` runs the canonicalizer
before emitting anything. That is what makes all three of your stated laws hold
*structurally* rather than by careful string construction — declaration order and
surface choice are erased before a character is written, so a formatting-only edit
provably lands on the same bytes and therefore the same SemanticArtifactID.

## Laws proven (binding_run9, over the 6 structural worlds + a bootstrap/core twin)

| # | law |
|---|---|
| L1 | `parse_wrl_core(format(graph)) == graph` (round-trip) |
| L2 | `format(parse(format(src))) == format(src)` (idempotent / stable) |
| L3 | a formatting-only edit keeps the **SemanticArtifactID** |
| L4 | a formatting-only edit keeps **CompilePlanDigest + BackendArtifactID** |
| L5 | bootstrap & core surfaces of one world format to the **IDENTICAL text** |
| L6 | output parses back as real WRL Core (ports == frozen registry) **and is rejected by the bootstrap parser** (genuinely Core, not bootstrap) |
| L7 | a declaration-order shuffle formats to the **IDENTICAL text** |
| L8 | run inputs (claims) survive `format → parse` (`epoch_inputs`/`run_plan` identical) |
| L9 | 3B-1 spans over the formatted text resolve **every** canonical object/edge (formatter ↔ span interop) |
| L10 | the formatted text runs **ic_ref == ic32 == golden** (native) |

Native gated exactly like the sibling batteries (`TRVM_SKIP_NATIVE=1` → ref-only).

## No new runtime constructs

The formatter is a pure emitter over the existing canonical graph; nothing on the
identity or reduction path changed. The Fixture oracle, `compile_step_v6`, and the
sealed-plan compile boundary are all untouched.

## Next (your 3B sequence)

**3B-3 — stable diagnostics**: error code + message + primary span + optional
related span + canonical object id, now that stable spans (3B-1) and canonical
text (3B-2) both exist. Then 3B-4 (named rotor constants + concise clocks) and
3B-5 (SemanticDiff + completion metadata), then the pinned Spinner Bench demo.

Proceeding to 3B-3 under the standing order unless you want to redirect.
