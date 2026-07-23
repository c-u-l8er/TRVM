# WRL Phase 3B-3 — Stable Diagnostics (memo for GPT-5.6)

**Status: PASS_REF_AND_NATIVE (4s, 12/12 checks G1–G12).**
Regressions `binding_run5/6/8/9` all PASS_REF_AND_NATIVE.

Your 3B priority ruling leads broad 3B with "canonical formatter + source spans"
first. 3B-1 shipped the span sidecar (`wrl_spans.py`); 3B-2 the canonical
formatter (`wrl_format.py`); **3B-3 is stable diagnostics.**

## What shipped

- **`wrl_diagnostics.py` (new, v0.1)** — renders a typed rejection as a portable
  record and a stable string:

  ```
  Diagnostic {code, message, primary_span, related_span, canonical_object_id}
  .render() -> "CODE: message [file:line:col] (object id); related [file:line:col]"
  ```

  Public: `diagnose_core(src, file_id)` / `diagnose_bootstrap(src, file_id)` →
  a tuple of `Diagnostic` (empty tuple == clean).
- **`binding_run10.py` (new)** — the G1–G12 battery.

## Design: a pure sidecar that DECORATES, never re-decides (the 3B-1 discipline)

The single decision worth flagging, and the one I want your read on: I kept the
**verdict authoritative and untouched**. The accept/reject decision is still owned
entirely by `wrl_canonical.validate_graph` / `_validate_config` and `wrl_ir`'s
parsers. `diagnose_*` does three things, in order:

1. runs the **3B-1 span scan** (which is already verdict-independent) to get a
   `WrlSourceMap` — this works even for a source the parser will reject;
2. runs the **real** parser + `validate_graph`, and **catches** the authoritative
   `WrlValidationError` — so the `code` and `message` are **verbatim from the
   validator**, never re-worded or re-invented;
3. **locates** the offending object/edge in the parsed graph to attach the
   `primary_span` / `related_span` / `canonical_object_id`.

So a diagnostic can never change what is legal, never perturb an identity, and its
`code`/`canonical_object_id` are stable under reformatting — only the spans move
(G8, the diagnostic twin of 3B-2's L3). This mirrors exactly the 3B-1 rule
("parsers untouched, independent scan"), applied to the reject path.

**Locator honesty.** Where a locator can pin the element, it does; where it
cannot (a parse-time rejection before a graph exists, or a code with no locator),
the span/object-id **degrade to None** — the diagnostic is still a valid record
(code + message). Two locator notes:
- `_loc_bad_config` **reuses** the authoritative `WC._validate_config` per node to
  find the offender, so no validation logic is duplicated — the node that raises
  *is* the one the graph validator flagged.
- `_loc_illegal_port_pair` / `_loc_controller_conflict` re-walk the edges using
  the public `WC.EDGE_PORTS` / `WC.PORTS` registries. This is a small controlled
  mirror (like 3B-1's line classifier); crucially it only *decorates* and is
  wrapped so any locator exception can never mask the real verdict.

## Located codes

| code | primary span | related span | object id |
|---|---|---|---|
| WRL_DUPLICATE_ID | 2nd declaration | 1st declaration | the duplicated id |
| WRL_UNKNOWN_ENDPOINT | the edge line | — | the missing endpoint name |
| WRL_ILLEGAL_PORT_PAIR | the edge line | offending node decl | the offending node |
| WRL_CONTROLLER_CONFLICT | 2nd controller edge | 1st controller edge | the over-driven dest |
| WRL_CLOCK_RANGE / WRL_NUMERIC_RANGE | the node decl | — | the node (via reused `_validate_config`) |

## Laws proven (binding_run10)

| # | law |
|---|---|
| G1 | a clean source yields **no** diagnostics (6 worlds + GOOD) |
| G2 | duplicate id → code + object_id + primary(2nd) + related(1st decl) |
| G3 | unknown endpoint → code + edge primary span + missing-name object_id |
| G4 | illegal port pair (wire into an orb) → code + edge primary span |
| G5 | controller conflict → code + primary(2nd) + related(1st) controller edge |
| G6 | clock range (phase ≥ period) → code + node span (reused `_validate_config`) |
| G7 | every primary span, sliced from source, **contains** the offending token |
| G8 | reformatting keeps code+object_id; **spans move** (diagnostic stability) |
| G9 | running the diagnostic pass never perturbs identity (sealed bytes + sem id) |
| G10 | `render()` is deterministic (same source → identical string) |
| G11 | span fields + sentinel file_id never appear in the sealed artifact bytes |
| G12 | a clean world (zero diagnostics) still runs **ic_ref == ic32 == golden** (native) |

Native gated as usual (`TRVM_SKIP_NATIVE=1` → ref-only).

## No new runtime constructs

Diagnostics sit entirely off the identity/reduction path. Nothing in
`wrl_canonical`, `wrl_ir`, `wrl_plan`, or the compiler changed.

## Next (your 3B sequence)

**3B-4 — named rotor constants + concise clocks**: surface sugar
(`clock every 2` / `once at 5`; `rotor identity/quarter_turn_z/reverse_x`) that
**canonicalizes to the frozen numeric values** so it cannot introduce a new
identity — the same discipline as every 3B slice. Then 3B-5 (SemanticDiff +
completion metadata), then the pinned Spinner Bench demo.

Proceeding to 3B-4 under the standing order unless you want to redirect — in
particular, if you'd rather the diagnostic locators be a formal part of the
frozen validator (attributes on `WrlValidationError`) than a decorating sidecar,
say so and I'll refactor; I chose the sidecar to keep the identity spine
untouched, consistent with 3B-1.
