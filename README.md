# TRVM — a coordination-free distributed interaction-calculus runtime

A correct, packed-word, **WebAssembly** reducer for the Interaction Calculus (the
calculus HVM3/HVM4 implement), and the argument and evidence that its reduction
**distributes across machines with no locks and no consensus**.

> **Start with [`FINDINGS.md`](FINDINGS.md)** — the legible synthesis: the surviving arc, what
> was demonstrated, what was investigated and falsified, and what is honestly open. Then
> [`docs/spec/paper.md`](docs/spec/paper.md) for the runtime in full and [`research/INCRDT.md`](research/INCRDT.md)
> for the identity/memory thread. This README is the file map and reproduction guide. Where any
> older note disagrees, `FINDINGS.md`, `docs/spec/paper.md`, and this README are canonical.

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
docs/spec/                  SOURCE OF TRUTH for any new implementation
  SPEC.md                   normative 64-bit tagged-word runtime spec
  paper.md                  the runtime, in full (authoritative writeup)
  RELATED_WORK.md           prior-art map; bounds novelty honestly
  conformance/
    README.md               how an implementation proves conformance
    vectors/*.json          language-agnostic test vectors (run by any impl)

runtime/                    the reduction engine — one subdir per implementation
  python/                   reference + oracle (ic_ref, ic_float) + foundations (inet, p2)
    conformance.py          runs docs/spec/conformance/vectors against this implementation
  c/                        ic32.c — packed-word native runtime (`./ic32 --test` → 13/13)
  wasm/                     ic32_wasm.c, ic32.wasm (9.9KB), wrun.js, build.sh
  js/                       swarm.js — ic32.wasm coordination-free across worker_threads
  zig/                      ic32.zig — third native implementation
  mojo/                     ic32.mojo — fourth native implementation

bench/                      cross-runtime benchmark over famous math problems
  bench.py terms.py nf_equiv.py results.json README.md

distribution/               coordination-free protocol artifacts
  dist_ic.py dist_real.py parallel.py dsearch.py share_win.py

forge/                      WRL Forge — the world authoring/sealing toolchain that sits
                            on top of the runtime (identity spine, Spinner Bench, project
                            store); see forge/README.md and forge/FORGE_ARCHITECTURE.md

wrlm/                       WRLM — the proposer above the sealed substrate (see below)

research/                   the identity / computational-memory thread (the result)
  INCRDT.md incrdt*.py slotted*.py compmem*.py semilattice.py …

site/                       trvm.dev static site
tools/                      laws_check.py — citation-consistency checker for LAWS.md

attic/                      superseded / forward-looking, kept for the record
  lc2.py linet.py DESIGN.md plan.py world.py
```

The clean multi-implementation axis is **the runtime**: `docs/spec/` plus
`docs/spec/conformance/vectors` is the contract a future Rust/Go implementation
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

## The layers above the runtime

The reducer is the bottom of a four-layer stack. Two of those layers live in this
repository:

| Layer | What it does | Where |
|---|---|---|
| **WRLM** | *proposes* worlds — the only statistical component | `wrlm/` (this repo) |
| **WRL** | *seals* worlds into a `sem-` identity | [`WRL/`](../WRL) · `forge/` (this repo) |
| **TRVM** | *reduces* them deterministically | `runtime/` (this repo) |
| **TRAAVIIS** | *admits* episodes as evidence | [`TRAAVIIS/`](../TRAAVIIS) |

Read that as one sentence: **WRLM proposes, WRL seals, TRVM reduces, TRAAVIIS admits.**

### WRLM — the proposer

Everything below WRLM is deliberately dumb: total, deterministic, content-addressed,
non-statistical. **WRLM is the only statistical component in the stack** — an *admitted
generative transducer*, a probabilistic proposer over deterministic sealed worlds. It is
not a world model, not a memory system, and not a replacement for anything already
shipped. TRAAVIIS *holds, seals, replays and admits* worlds; WRLM *authors* them under
supervision. Substrate vs. cortex — neither absorbs the other.

The architecture is **Arm D′**, and the trick is that the edit ops are *derived, not
generated*:

```
model emits full WRL text
  → host parses into an isolated candidate buffer
  → diagnose_core
  → seal  (candidate_sem_id)
  → wrl_diff.semantic_diff(base, candidate)
  → derived GraphEditV1 op sequence
  → apply_edit(base, derived_ops)
  → assert resulting_sem_id == candidate_sem_id
```

The model writes prose-like text (its strongest modality), but nothing reaches the world
except through the six frozen typed ops and the existing `apply_edit` seam. **No new
runtime construct, no new identity rung.**

Correctness is a ladder of four rungs — validity (does it parse, seal and lower),
target identity (`sem-` equality), goal satisfaction (`GoalSpecV1` evaluation), and
subjective quality. The first three are *total and free*. The fourth is **out of scope**
and must never be smuggled in via an LLM judge.

**Status: build-order steps 1 and 2 are shipped and closed; steps 3–10 are paper only.**
What exists in `wrlm/` today is `GoalSpecV1` (a closed serialized AST, not a language —
decidable over bounded finite worlds by construction), `TaskBundleV1`, `WorldRecordV1`,
the `worldview.py` engine adapter, `envelope.py`, a derived coverage domain
(`wrlm.coverage.v1.2`, 320 published cells) and a 58-world proved pool inhabiting 298 of
them. There is no model arm yet.

Design of record: [`WRLM_RESEARCH_BRIEF.md`](WRLM_RESEARCH_BRIEF.md). It supersedes
nothing — WRL, TRVM, TRAAVIIS and Forge remain authoritative for their own layers.

## Honesty notes (also in the paper)

- **No parallel speedup is demonstrated.** Every distribution result is
  coordination-free *correct*, not faster. Speedup needs the autonomous regime
  (re-entrant workers + the Safra detector from `runtime/python/p2.py`).
- **Iterative normaliser/readback** in both `ic32.c` and `ic32_wasm.c`; the WASM
  build reaches depth 2^21 (2,097,152) matching the native runtimes. The WASM
  *parser* is still recursive (deep input, not deep output, is the remaining
  limit). Python's `ic_float` is still recursive and depth-limited.
- **GC (Phases 1–2):** `ic32.c` recycles consumed redex nodes via size-classed free
  lists and propagates erasers at `APP-ERA`; `--gcstats` / `--erasestats` quantify it.
  Var-indirect / affine-unused leaks remain and are precisely characterized in `FINDINGS.md`.

## License

Apache-2.0. See [`LICENSE`](LICENSE).
