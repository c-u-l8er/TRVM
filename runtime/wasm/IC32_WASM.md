# IC32_WASM — the runtime compiled to WebAssembly

**Files:** `ic32_wasm.c` (freestanding source) · `ic32.wasm` (9.9 KB binary) ·
`wrun.js` (Node host)
**Build:** `clang-15 --target=wasm32 -O2 -nostdlib -ffreestanding -Wl,--no-entry
-Wl,--export-dynamic -Wl,-z,stack-size=16777216 -Wl,--initial-memory=67108864
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

- **Recursive `normal`/`whnf` overflow V8's WASM call stack on deeply-nested
  output.** V8 caps WASM call depth well below the native C stack: depth-8192
  readbacks (2¹³, ~25K interactions) run fine, but a 59049-deep readback (3¹⁰)
  throws `Maximum call stack size exceeded`. The native `ic32` binary handles it
  (it did 59049-deep in ~5 ms). This is a property of the **recursive tree-walk**
  under the JS engine, not of correctness or of the algorithm. The fix is to make
  `normal` (and the `whnf` recursion in `fire`/`app`) **iterative with an explicit
  work-stack in linear memory** — a known, mechanical change. Until then, WASM is
  limited to terms whose normal form nests less than ~tens of thousands deep
  (every battery term, and most realistic agent/search terms, are far shallower).
- **`-Wl,-z,stack-size` sets the linear-memory shadow stack, not V8's call-stack**,
  so raising it does not lift the depth limit above — only the iterative rewrite
  does.
- **Still single-node; GC not ported here.** The free-list recycling and eraser
  propagation added to `ic32.c` (Phases 1-2) have NOT been ported to this wasm build,
  so the 32 MB static heap still caps a single reduction's allocation in the wasm path.

## Where this goes

1. **Iterative `normal`** — remove the V8 call-depth ceiling so the WASM build
   matches the native build's depth reach. This is the most direct next
   improvement to the runtime itself.
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
