# TRVM conformance

How a new implementation of the TRVM runtime proves it is correct. This is the
contract `spec/SPEC.md §6` defines, made executable.

## What an implementation must do

1. **Reproduce every vector.** `vectors/normalize.json` is a list of
   `{ term, nf, ref_interactions }`. Each `term` is in the surface IC/lambda syntax
   (`λ`, application `(f x)`, superposition `&L{a,b}`, duplication `!&L{a,b}=v; body`,
   eraser `*`). Your runtime MUST normalize `term` to exactly `nf` (canonical naming:
   bound variables renamed `a, b, c, …` in first-encounter order; free names
   preserved). `ref_interactions` is the Python reference reducer's interaction count
   — a *native/optimal-sharing* runtime may take a different number of interactions,
   so only the **normal form** is normative across runtimes; the interaction count is
   pinned only for the reference reducer it was recorded from.

   The vectors are **cross-validated at authoring time**: a term is only included if
   `ic_float` (Python reference) and `ic32` (C) already agree on its normal form, so
   you can diff against `nf` directly.

2. **Pass the behavioral batteries** (SPEC §6.1–§6.3):
   - **§6.1 Confluence** — for a battery of nets, N random reduction orders MUST yield
     the identical normal form *and* identical interaction count.
   - **§6.2 Distributed == sequential** — reduction under random partitions and random
     message-delivery order MUST match the single-node normal form and interaction count.
   - **§6.3 Exactly-once boundary** — boundary exports MUST equal boundary rewrites in
     every run.

## Coverage status (honest)

| Check | Status | Where it runs |
|---|---|---|
| Cross-runtime normal-form vectors | **covered** | `runtime/python/conformance.py` (ic_float, ic_ref, ic32, ic32.wasm) |
| §6.1 confluence (300 random orders) | **covered** | `runtime/python/inet.py` battery |
| §6.2 distributed == sequential | **covered** | `distribution/dist_ic.py` (480 runs) |
| §6.3 exactly-once boundary | **covered** | `inet.py` / `dist_ic.py` |
| §6.4 snapshot round-trip | **GAP** | no `snapshot()`/`restore()` in the reference yet |
| §6.5 REF unfolding | **GAP** | recursive supercombinator REFs not exercised |

The two gaps are intentional and tracked — see `FINDINGS.md` "Honest limits / standing
gaps". Do not claim full §6 conformance until they are wired.

## Running it

```bash
make test                              # everything below
python3 runtime/python/conformance.py  # just the conformance runner
```

The runner auto-detects which backends are present: it always checks the Python
reference, additionally checks `ic32` if `runtime/c/ic32` is built, and additionally
checks `ic32.wasm` if `node` is available.

## Adding vectors

Regenerate / extend by running candidate terms through *both* the Python reference and
the native runtime and keeping only those where they agree — that invariant is what
makes the file safe to diff against from any language. Keep terms within the labeling
discipline interaction-net reduction requires (linear binders, distinct fan labels for
independent duplicators); naively-shared labels reduce incorrectly *by design* and are
not valid vectors.
