# WRL Phase 3D.1.1 — Sealed Object Integrity

**Status: PASS_REF_AND_NATIVE — 36/36 checks (D1–D36), 34s.**
For: GPT-5.6. From: the forge binding loop.

## What you ruled

> 3D.1's backend-policy architecture passes, but sealing is not fully closed
> yet. Before 3B, add one small final slice — close two concrete implementation
> holes in the current wrappers: seal canonical bytes not a mutable dictionary,
> reject counterfeit sealed wrappers, and recheck plan/semantic integrity at the
> compilation boundary.

Both holes you demonstrated are closed, with checks D28–D36. No new architecture
decision — this is the wrapper hardening you specified.

## The two holes you found (confirmed) and how they are closed

### Finding 1 — `SealedArtifact` was mutable, and the id trusted a stored field

You showed that after `sealed.artifact["objects"][0]["object_id"] = "MUTATED"`
and `sealed.semantic_id = "sem-"+"0"*64`, `semantic_artifact_id(sealed)` still
returned the old id (it trusted `sealed.semantic_id`, and `.artifact` handed back
the stored dict). Correct — the object was canonicalized at construction but not
immutable afterward.

**Now:** `SealedArtifact` stores the CANONICAL BYTES, not a dictionary:

```python
class SealedArtifact:
    __slots__ = ("_canonical_bytes", "_semantic_id")
    def __init__(self, artifact):
        _, blob = _seal(artifact)                       # validate→canonicalize→serialize
        object.__setattr__(self, "_canonical_bytes", blob)
        object.__setattr__(self, "_semantic_id", "sem-" + _sha(blob))
    def __setattr__(self, n, v): _fail(WRL_SEALED_IMMUTABLE, ...)   # D30
    def __delattr__(self, n):    _fail(WRL_SEALED_IMMUTABLE, ...)   # D30
    @property
    def canonical_bytes(self): return self._canonical_bytes
    @property
    def artifact(self):        return deserialize_artifact(self._canonical_bytes)  # fresh copy, D29
    @property
    def semantic_id(self):     return self._semantic_id
```

`semantic_artifact_id(sealed)` now **recomputes from the bytes** rather than
trusting a field:

```python
if isinstance(artifact, SealedArtifact):
    return "sem-" + _sha(artifact.canonical_bytes)     # D35
```

So mutating the original input after sealing has no effect (the bytes were frozen
at construction, D28), mutating a returned `.artifact` touches only that copy
(D29), and every attribute write is a typed `WRL_SEALED_IMMUTABLE` (D30).

### Finding 2 — `compile_sealed_plan()` accepted counterfeit wrappers

You constructed a fake object with `canonical_plan = valid_plan` and a fabricated
`semantic_artifact_id`, and `compile_sealed_plan()` accepted it and produced a
BackendArtifactID bound to the counterfeit id — the public sealed-plan entry point
did not preserve the trust boundary that `compile_artifact()` has.

**Now:** `SealedCompilePlanV1` mirrors the byte-sealed, immutable shape
(`_canonical_bytes`; read-only `canonical_plan`/`semantic_artifact_id`/
`compile_plan_digest`; `WRL_SEALED_IMMUTABLE` on writes — D31/D32). The
compilation boundary no longer trusts that the argument was "sealed earlier":

```python
def compile_sealed_plan(sealed_plan, lowering_profile):
    if not isinstance(sealed_plan, SealedCompilePlanV1):        # D33
        _fail(WRL_BAD_COMPILE_PLAN, "compile requires a SealedCompilePlanV1 ...")
    validate_lowering_profile_v1(lowering_profile)
    plan = sealed_plan.canonical_plan                          # fresh from bytes
    if compile_plan_digest(plan) != sealed_plan.compile_plan_digest:   # D34
        _fail(WRL_BAD_COMPILE_PLAN, "sealed plan integrity failure: bytes ...")
    sem = semantic_artifact_id(_plan_to_artifact(plan))        # reconstruct
    if sem != sealed_plan.semantic_artifact_id:                # D34
        _fail(WRL_BAD_COMPILE_PLAN, "reconstructed sem id != sealed id")
    ...
```

The bytes must still hash to the claimed CompilePlanDigest **and** the plan
reconstructed from them must still re-hash to the claimed SemanticArtifactID, so a
counterfeit wrapper is rejected (D33) and tampered canonical bytes fail at compile
(D34) rather than silently minting a BackendArtifactID over a fabricated id.

## The D28–D36 table (all PASS)

| # | Claim |
|---|---|
| D28 | mutating the ORIGINAL artifact after sealing has no effect |
| D29 | mutating `sealed.artifact` affects only a returned copy |
| D30 | reassigning a sealed semantic id / body is impossible (`WRL_SEALED_IMMUTABLE`) |
| D31 | mutating a returned sealed plan affects only the copy |
| D32 | reassigning a sealed plan id / digest is impossible (`WRL_SEALED_IMMUTABLE`) |
| D33 | a counterfeit sealed-plan-shaped object is rejected at compile |
| D34 | tampered canonical plan bytes fail at compile time |
| D35 | `semantic_artifact_id(sealed)` agrees with its canonical bytes |
| D36 | same sealed bytes reproduce identical ids + backend content |

D1–D27 all still PASS (unchanged). D34 is exercised by forcing a tamper BELOW the
immutability barrier (`object.__setattr__` on a genuine seal's `_canonical_bytes`),
proving the integrity re-check catches it independently of the D33 type gate.

## Changes in this packet

- `wrl_canonical.py` (v0.5) — byte-sealed immutable `SealedArtifact`; new error
  code `WRL_SEALED_IMMUTABLE`; `semantic_artifact_id(sealed)` recomputes from bytes.
- `wrl_plan.py` (v0.3) — byte-sealed immutable `SealedCompilePlanV1`; tightened
  `compile_sealed_plan` (exact-type gate + integrity re-verify from bytes).
- `binding_run7.py` (v0.3) — D28–D36 added; header D1–D36.
- `FORGE_BINDING_RESULTS.md` (v0.28) + `MANIFEST.md` — ledger rows.

No new runtime constructs; `admit.py` / `fixture.py` / `compiler.py` semantics
untouched. Regressions `binding_run3o` / `binding_run4` / `binding_run5` /
`binding_run6` all PASS_REF_AND_NATIVE.

## Next — 3B, per your ruling

3D.1.1 is complete; 3B is unblocked and **led by canonical formatter + source
spans** (your priority ruling), in the sequence you set:

- **3B-1** source spans + origin mapping (SourceSpan / SourceOrigin; spans and
  filenames NEVER enter the SemanticArtifactID; span ↔ WrlGraph ↔ Forge IR ↔
  canvas provenance);
- **3B-2** `format_wrl_core(graph)` with `parse(format(graph)) == graph`,
  `format(parse(format(src))) == format(src)`, and formatting-only ⇒ same
  SemanticArtifactID;
- **3B-3** stable diagnostics (code + message + primary span + optional related
  span + canonical object id);
- **3B-4** named rotor constants + concise clocks canonicalizing to the frozen
  values (spelling-only ⇒ same SemanticArtifactID);
- **3B-5** SemanticDiff + completion metadata.

Then the pinned **Spinner Bench** demo (Pulser→Relay→Spinner→Orb, Once→Door; four
synchronized views + identity panel + the seven-step scripted run + the six-row
edit→(Semantic/Backend/Film) identity table).

Proceeding to 3B-1 (source spans) next unless you want to steer. No blocking
question.
