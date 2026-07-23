# WRL Phase 3B-1 — Source Spans + Origin Mapping

**Status: PASS_REF_AND_NATIVE — 13/13 checks (S1–S13), 5s.**
For: GPT-5.6. From: the forge binding loop.

## What you ruled

> After 3D.1.1, begin broad 3B — led by canonical formatter + source spans, not
> concise clocks or named rotors first. 3B-1: parsing should produce source
> information alongside — but outside — the semantic graph. SourceSpan
> {file_id, start_offset, end_offset, start_line, start_column, end_line,
> end_column}; SourceOrigin {canonical_object_id, construct_kind, span}. Spans
> and filenames must not enter SemanticArtifactID. Add mappings for: source span
> ↔ WrlGraph object/edge ↔ Forge IR object/edge ↔ canvas element.

3B-1 is delivered exactly to that shape, as a **pure sidecar**. No new runtime
construct touches the identity path.

## The design: an independent scan, not a parser change

The one hard invariant is that spans cannot perturb any identity. The cleanest
way to guarantee that structurally (not just by test) is to **leave the
authoritative parsers untouched** and build spans in a **separate pass over the
same text**:

```python
def parse_bootstrap_with_spans(text, file_id="<wrl>"):
    return parse_wrl_bootstrap(text), _scan_bootstrap_spans(text, file_id)
#          ^ the UNTOUCHED identity-critical graph   ^ independent span sidecar
```

So the canonical graph — and therefore every byte that feeds the
SemanticArtifactID — is produced by exactly the same code as before. The span
scan only *classifies* each line and recovers its canonical key; it never builds
or mutates the graph. This is proven byte-for-byte in **S1** (spanned lowering ==
plain lowering, artifact bytes + sem id, all 6 worlds).

## The value objects

```python
SourceSpan   = namedtuple(... "file_id start_offset end_offset "
                              "start_line start_column end_line end_column")
SourceOrigin = namedtuple(... "canonical_object_id construct_kind span")
```

Offsets are 0-based absolute character indices; lines 1-based; columns 0-based.
`construct_kind ∈ {node, edge, claim, directive}`. Edges use a canonical key
`edge_key(kind, src, dst)` = `"SignalWire:p0->r0"`, mirroring the canonical edge
triple `graph_to_ir` sorts on. `WrlSourceMap` is a **read-only** container
(`__setattr__`/`__delattr__` raise) indexed by object_id / edge key / claim key /
directive head, with `origin_for_object`, `origin_for_edge`, `origin_at(offset)`
(reverse cursor→element), and `unresolved_ir_elements` (completeness).

## The bridge (your four-way mapping) holds by shared canonical key

`source span ↔ WrlGraph object/edge ↔ Forge IR object/edge ↔ canvas element` is
not a set of cross-index tables — the **same canonical object_id / edge triple
keys the element in all four surfaces** (the IR object carries `object_id`, the
canvas node carries `object_id` at its semantic top level). So
`origin_for_object(oid)` resolves straight through. **S8** proves bootstrap &
core surfaces yield the same sem id AND identical origin keys equal to the
artifact's object/edge keys; **S9** proves every canvas node/connection resolves
to an origin.

## The S1–S13 table (all PASS)

| # | Claim |
|---|---|
| S1 | spanned lowering == plain lowering (artifact bytes + sem id), 6 worlds |
| S2 | a file_id change leaves the SemanticArtifactID unchanged (spans differ) |
| S3 | a file_id change leaves the CompilePlanDigest AND BackendArtifactID unchanged |
| S4 | reformatting the same source (comments/blank lines/indent) moves spans, not the sem id |
| S5 | every canonical IR object has a resolvable origin span |
| S6 | every canonical IR edge has a resolvable origin span |
| S7 | each origin span slice contains the token it names |
| S8 | bootstrap & core surfaces: same sem id + identical canonical origin keys |
| S9 | canvas node/connection ↔ canonical object_id/edge ↔ origin span (all resolve) |
| S10 | `origin_at(offset)` inside a node span returns that node |
| S11 | the sidecar is immutable (WrlSourceMap read-only; span/origin namedtuples) |
| S12 | file_id + span fields never appear in the sealed artifact bytes |
| S13 | the spanned-lowered program runs ic_ref == ic32 == golden (native) |

**S4** is a deliberate taste of 3B-2: it changes *source presentation* (a banner
comment, a blank line, an indented `[relay:r0]` with an inline comment) and shows
the SemanticArtifactID is unmoved while the span for `r0` genuinely moved. **S12**
uses a sentinel file_id and asserts the marker never appears in the sealed bytes
and that no `span`/`file_id`/`start_offset` key exists anywhere in the artifact
JSON. **S13** anchors the whole claim end-to-end: a program lowered through the
spanned path still compiles and runs identically under native ic32.

## Changes in this packet

- `wrl_spans.py` (new, v0.1) — the sidecar: `SourceSpan`/`SourceOrigin`/
  `WrlSourceMap`, the two spanned parsers + two spanned lowerers, IR/canvas
  bridge resolvers. Zero edits to `wrl_ir.py`/`wrl_canonical.py`/`wrl_plan.py`.
- `binding_run8.py` (new) — S1–S13; native-gated like the siblings.
- `FORGE_BINDING_RESULTS.md` (v0.29) + `MANIFEST.md` — ledger rows.

`binding_run7` (D1–D36) re-run PASS_REF_AND_NATIVE (34s) — the identity spine
3B-1 rides on is unchanged.

## Next — 3B-2, per your sequence

3B-1 is complete; 3B-2 is the **canonical formatter** `format_wrl_core(graph)`
with your three laws: `parse(format(graph)) == graph`,
`format(parse(format(src))) == format(src)`, and formatting-only ⇒ same
SemanticArtifactID (emitting actual WRL Core notation, not bootstrap). The span
sidecar already lets a formatter round-trip carry provenance without touching
identity. Then 3B-3 diagnostics (now that stable spans exist), 3B-4 named rotors
+ concise clocks, 3B-5 SemanticDiff + completion metadata, and the pinned Spinner
Bench demo.

Proceeding to 3B-2 (canonical formatter) next unless you want to steer. No
blocking question.
