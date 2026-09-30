# IC32 checked invocation ABI v2

Additive checked entry point over the existing IC32 reducer. `ic32_checked.wasm`
is a separate artifact; the legacy `ic32.wasm`, `wrun.js` and search demo remain
unchanged. The common C source retains `run(length)` for legacy consumers.
Valid corpus output/count compatibility is tested; identical behavior for every
previously malformed or resource-exhausting input is not claimed.

## Interface

- `abi_version() -> 2`
- `input_ptr()`, `input_capacity()` — guest input area; callers must check the
  length before copying and reserve one byte for the terminator.
- `run_checked(length, max_interactions, max_output_bytes) -> status`
- `last_status()`, `output_length()`, `output_ptr()`, `output_capacity()`
- `last_interactions()` — successful budgeted interaction count for this run.

| Status | Meaning |
|---|---|
| 0 | Reduction/readback completed; result is candidate text. |
| 1 | Input length is zero, negative or outside the buffer. |
| 2 | Parse/affinity error, including unconsumed input, NUL, overlong names or labels. |
| 3 | The next counted interaction would exceed the allowance. |
| 4 | Complete readback would exceed the output allowance. |
| 5 | A checked implementation resource bound was exhausted. |
| 6 | Invalid interaction or output allowance. |

Failures expose `output_length() == 0`; old bytes may remain in guest memory and
are not a result. `ABORTED` has no special text meaning in this interface.
Maximum interactions must be 0..50,000,000. Maximum output must be
0..output_capacity()-1. Exact-fit output succeeds, including UTF-8 byte accounting.
An interaction allowance is not a CPU-time/fuel bound on parsing or every loop.
The host deadline and Wasm-trap path remain necessary.

The checked parser consumes the complete input except trailing whitespace,
requires labels in 0..134217727, accepts at most 39 ASCII name bytes and enforces
affine uses. Unused binders remain permitted. The affinity requirement comes
from `docs/spec/paper.md` §2 and the existing calculus, not a new policy.
Recursive parsing is limited to 512 entries and recursive weak-head reduction
to 1024. Existing scope/name/work-stack/heap capacities also have explicit guards.
Resource bounds are implementation limits, not claims about all valid terms.

The typed status is trustworthy only after the call returns normally. A Wasm
trap, host failure or interrupted worker remains a separate host outcome; none
is translated into a successful guest status. This is not full TRVM conformance,
distributed execution, or semantic admission into Super.

## Build and pinning

The old build script requests 64 MiB despite the source's larger static memory.
The new script uses 256 MiB and writes only `ic32_checked.wasm`:

```sh
WASM_LD=/usr/lib/llvm21/bin/wasm-ld bash runtime/wasm/build-checked.sh
node --test --test-isolation=none runtime/wasm/experimental/host.test.mjs runtime/wasm/experimental/abi.test.mjs
```

Measured toolchain: clang 22.1.8 and LLVM 21 wasm-ld. A repeated build under that
same toolchain was byte-identical. Other toolchains may produce different bytes.
`experimental/host.mjs` intentionally pins the checked binary digest; a changed
artifact requires reviewed repinning and rerunning compatibility/failure tests.
The script does not silently rewrite that pin.

`oracle-corpus.json` contains 26 expected outputs and interaction counts generated
with the existing Python `ic_float` reference, including Church numerals and
composition. It is a bounded compatibility corpus, not the full conformance
suite. Tests also exercise parser rejection, exact output limits, step budgets,
parser-depth/name-table exhaustion and recovery after failed runs. The 8193-name
case directly exercises the ABI; it exceeds the host's smaller request policy.
