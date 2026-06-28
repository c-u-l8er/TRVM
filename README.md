# TRVM — a coordination-free distributed interaction-calculus runtime

A correct, packed-word, **WebAssembly** reducer for the Interaction Calculus (the
calculus HVM3/HVM4 implement), and the argument and evidence that its reduction
**distributes across machines with no locks and no consensus**.

> **Start with [`FINDINGS.md`](FINDINGS.md)** — the legible synthesis: the surviving arc, what
> was demonstrated, what was investigated and falsified, and what is honestly open. Then
> [`spec/paper.md`](spec/paper.md) for the runtime in full and [`research/INCRDT.md`](research/INCRDT.md)
> for the identity/memory thread. This README is the file map and reproduction guide. Where any
> older note disagrees, `FINDINGS.md`, `spec/paper.md`, and this README are canonical.

## The thesis in one paragraph

Interaction-net reduction is confluent by construction, which makes single-net
reduction *schedule-independent*: if the order redexes fire does not change the
result, then *which machine* fires a redex and *when* does not change the result of
a fixed net either. Coordination-freedom **across machines** additionally rests on
the boundary-port discipline (owner-only rewrite over monotone, never-retracting
exports; see `spec/paper.md` §4.5) — confluence licenses the schedule-independence,
that discipline licenses the coordination-freedom. Together they let a single
computation be sharded across nodes and reduced without locks or consensus. **Reduction is the data plane and needs no
coordination; only termination is ever a control-plane question — and only in the
autonomous regime.** On a WebAssembly substrate, the same runtime runs in any
browser with no server, so "multi-node" means browser/edge/client-side — the
sovereign substrate an open agent stack wants.

## Repository layout

```
spec/                       SOURCE OF TRUTH for any new implementation
  SPEC.md                   normative 64-bit tagged-word runtime spec
  paper.md                  the runtime, in full (authoritative writeup)
  RELATED_WORK.md           prior-art map; bounds novelty honestly
  conformance/
    README.md               how an implementation proves conformance
    vectors/*.json          language-agnostic test vectors (run by any impl)

runtime/                    the reduction engine — one subdir per implementation
  python/                   reference + oracle (ic_ref, ic_float) + foundations (inet, p2)
    conformance.py          runs spec/conformance/vectors against this implementation
  c/                        ic32.c — packed-word native runtime (`./ic32 --test` → 13/13)
  wasm/                     ic32_wasm.c, ic32.wasm (9.9KB), wrun.js, build.sh
  js/                       swarm.js — ic32.wasm coordination-free across worker_threads

distribution/               coordination-free protocol artifacts
  dist_ic.py dist_real.py parallel.py dsearch.py share_win.py

research/                   the identity / computational-memory thread (the result)
  INCRDT.md incrdt*.py slotted*.py compmem*.py semilattice.py …

attic/                      superseded / forward-looking, kept for the record
  lc2.py linet.py DESIGN.md plan.py world.py
```

The clean multi-implementation axis is **the runtime**: `spec/` plus
`spec/conformance/vectors` is the contract a future Zig/Rust/Go implementation
targets; each `runtime/<lang>` proves conformance against the same vectors.

## The arc (build order — each artifact is self-validating)

```
runtime/python/ic_ref.py     correct reducer (fixes the higher-order-dup bug class)
   |
runtime/python/ic_float.py   general reducer (floating dups); the oracle
   |
runtime/c/ic32.c             packed-word native runtime (optimal sharing; ~22–34 M int/s;
   |                           self-validating via `./ic32 --test`)
   |
runtime/wasm/ic32.wasm       WebAssembly build (9.9 KB, matches the reference bit-for-bit)
   |
distribution/dist_ic.py      coordination-free distributed reduction — simulation (480 runs)
   |
distribution/dist_real.py    the same protocol on real OS processes over real IPC
   |
runtime/js/swarm.js          ic32.wasm coordination-free across real isolated workers  <- capstone
```

## Reproduce every result

```bash
# fastest: the whole battery
make test

# or piecemeal:
python3 runtime/python/ic_ref.py            # reference rules
python3 runtime/python/ic_float.py          # floating dups; 23 terms agree with the oracle
gcc -O2 -o runtime/c/ic32 runtime/c/ic32.c  # native runtime
echo 'λx.x' | runtime/c/ic32

# WebAssembly (clang-15 + lld-15; no emscripten). Rebuilds the prebuilt ic32.wasm:
bash runtime/wasm/build.sh
echo 'λx.x' | node runtime/wasm/wrun.js

# distribution
PYTHONPATH=runtime/python:distribution:research python3 distribution/dist_ic.py
node runtime/js/swarm.js                     # ic32.wasm coordination-free across worker_threads

# identity / memory (the result)
PYTHONPATH=runtime/python:research python3 research/semilattice.py   # ALL CONDITIONS HOLD
```

(`runtime/wasm/ic32.wasm` is committed prebuilt; `build.sh` rebuilds it.)

## Honesty notes (also in the paper)

- **No parallel speedup is demonstrated.** Every distribution result is
  coordination-free *correct*, not faster. Speedup needs the autonomous regime
  (re-entrant workers + the Safra detector from `runtime/python/p2.py`).
- **Recursive normaliser** overflows V8's WASM stack / Python's recursion limit on
  deeply-nested output; `ic32.c`'s parse/normalize/readback are already iterative.
- **GC (Phases 1–2):** `ic32.c` recycles consumed redex nodes via size-classed free
  lists and propagates erasers at `APP-ERA`; `--gcstats` / `--erasestats` quantify it.
  Var-indirect / affine-unused leaks remain and are precisely characterized in `FINDINGS.md`.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
