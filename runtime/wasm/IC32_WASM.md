# IC32_WASM — the runtime compiled to WebAssembly

**Files:** `ic32_wasm.c` (freestanding source) · `ic32.wasm` (10 KB binary) ·
`wrun.js` (Node host)
**Build:** `clang --target=wasm32 -O2 -nostdlib -ffreestanding -Wl,--no-entry
-Wl,--export-dynamic -Wl,-z,stack-size=16777216 -Wl,--initial-memory=268435456
-o ic32.wasm ic32_wasm.c`
**Validates against:** `ic_float.py` (and transitively `ic_ref.py` / native `ic32`).
**Status:** ✅ 28/28 battery terms match the Python oracle (including the cases
`ic_ref` diverges on); interaction counts identical to native; ~34 M
interactions/sec in-process.

This is the sovereignty/edge substrate: the same reduction core, compiled to a
tiny dependency-free WebAssembly module that runs in any browser or JS runtime.

## How it was built (and what it deliberately avoids)

The `emscripten` apt package wouldn't resolve in this sandbox (its bundled JS
helpers pin an ancient Node that conflicts with the installed Node 22, and the
upstream `emsdk` downloads from non-whitelisted hosts). Rather than fight that,
the runtime was compiled **freestanding** with `clang-15` + `wasm-ld-15`:

- **No libc.** No `emscripten`, no `wasi-libc`, no JS glue runtime. The heap is a
  static array in linear memory (the bump allocator I already had), and the few
  libc bits used (string compare/copy, integer-to-decimal) are ~10 lines of C.
- **A tiny explicit ABI** instead of stdio:
  - `input_ptr()` / `output_ptr()` — offsets of byte buffers in linear memory
  - `run(in_len) -> out_len` — parse + normalize + stringify; UTF-8 in, UTF-8 out
  - `last_interactions()` — interaction count of the last run

The result is a **9.9 KB** `.wasm` with five exports (`memory`, `input_ptr`,
`output_ptr`, `run`, `last_interactions`). The host (`wrun.js`, ~25 lines) writes
the term into memory, calls `run`, and reads the result back. The same module
loads unchanged in a browser via `WebAssembly.instantiate`.

## Validation — identical to the Python oracle

`wrun.js` is driven over the same battery used for `ic_float`/`ic_ref`:

- **28/28 terms match `ic_float` exactly** — README examples, Church identity
  n=0..6, exponentiation `(a b)=bᵃ`, Church-N applied to `NOT`, **and the four
  divergent-pattern cases `ic_ref` loops on** (which the floating-dup core, and
  therefore this WASM build, handle correctly).
- **Interaction counts are identical to the native C build** (e.g. `(9 2)`: 1128
  in both; `(3 3)`: 91 in both) — the reduction strategy survives compilation
  unchanged.
- **Optimal sharing survives the compile:** parity of 2ᴺ stays linear in N
  (80, 160, 240, 320, 400 for N=4..20) in the WASM module.

## Throughput

In-process (Node startup amortized over 500 runs, 2¹¹ readback):

```
0.187 ms/run   ->   34.4 M interactions/sec
```

That's native-comparable (the native C build measured ~22–33 M/s). A one-shot
`node wrun.js` invocation costs ~45 ms, but that is Node startup + module
instantiation, not reduction — it amortizes to zero for a long-lived runtime
(instantiate once, reduce many times), which is exactly the browser/edge agent
use case.

## Honest limitations

- **Still single-node; GC not ported here.** The free-list recycling and eraser
  propagation added to `ic32.c` (Phases 1-2) have NOT been ported to this wasm build.
  The heap has been raised to 16M slots (128 MB, matching `ic32.c`) to compensate,
  bringing initial-memory to 256 MB. This is fine for a long-lived in-process
  runtime (instantiate once, reduce many times) but is larger than ideal for a
  browser cold-start. Porting the free-list recycling would let the heap shrink
  back down.
- **The parser is still recursive.** Deeply nested *input* terms (as opposed to
  deep *output* from shallow input) will overflow V8's WASM call stack in the
  parser. The benchmark workloads are all shallow input (Church numerals with
  explicit dups), so this does not limit the benchmark set. The ic32.c iterative
  parser could be ported if deeply nested input becomes needed.

## Where this goes

1. **Free-list recycling** — port the intrusive free lists from `ic32.c` so the
   heap can shrink back to 4M slots and the module instantiates on less memory.
2. **Browser harness** — load `ic32.wasm` from a page (the ABI is browser-ready as
   is) so agents run client-side; this is the concrete "browser security model is
   the new BEAM" step.
3. **Distribution** — the boundary-port model (`SPEC.md` §4 / `p2.py`) over many
   WASM instances (Web Workers, WebRTC peers) for coordination-free multi-node
   reduction — the distributed version of HVM's destination, now on a sovereign
   client-side substrate.

Arc: correct simple core (`ic_ref`) → monotone workload distributed without
coordination (`dsearch`) → correct general core (`ic_float`) → packed-word native
runtime (`ic32.c`) → **WebAssembly build** (`ic32.wasm`, this file) → iterative
core + browser + boundary-port distribution → [&]/OpenSentience unification.
