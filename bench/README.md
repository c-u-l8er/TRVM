# bench — cross-runtime benchmark for the TRVM runtimes

Runs the same bytes — one IC surface term — through **all six TRVM runtimes** and
compares them on correctness first, then cost.

```bash
python3 bench/bench.py                      # full suite (~6 min)
python3 bench/bench.py --quick              # small sizes
python3 bench/bench.py --json results.json  # machine-readable
```

| file | what it is |
|---|---|
| `terms.py` | workload generator — famous problems in explicitly-linear IC syntax |
| `pyrun.py` | adapter putting `ic_ref`/`ic_float` behind the conformance CLI |
| `bench.py` | the runner: correctness gate, throughput tier, depth ceiling |

Backends are discovered, never assumed; an unbuilt one is reported as skipped
with the missing path named, never silently counted as passing.

## What is measured, and what it means

Three quantities, which are **not** interchangeable:

- **normal form** — the only thing normative across runtimes
  (`spec/conformance/README.md` §1). Every IC32-model backend must produce
  identical bytes. A disagreement is a conformance bug.
- **interactions** — machine-independent work. *Not* normative across runtimes
  (a different strategy may legitimately take a different count), so it is
  reported and cross-checked, never asserted.
- **wall time** — machine-dependent, and the easiest of the three to measure
  wrongly. See "Methodology" below.

Correctness is checked against ground truth computed in ordinary Python
arithmetic — not against another runtime — so all six can be wrong together and
it still shows.

## The workloads

Church-encoded, in **explicitly linear** form: IC binders are linear, so every
second use of a variable goes through an explicit `!&L{a,b}=v;` duplicator, and
independent duplicators get distinct labels (reusing a label reduces incorrectly
*by design* — that is the Lamping labelling discipline, not a runtime defect).

| group | workloads |
|---|---|
| arithmetic | multiplication, exponentiation `b^a`, tetration `b^^h`, Gauss triangular numbers |
| recursion | Fibonacci, factorial, Kleene predecessor, Ackermann — all via Church-pair iteration |
| sharing | parity of 2^N (up to 2^24), raw duplication depth |
| throughput | the same problems sized so reduction dominates process startup |

The recursion group is the one that genuinely stresses the machinery: the step
function *itself* contains a duplicator, so iterating it duplicates a
duplicator.

## Methodology notes

**Minimum, not mean.** Timing noise from process launch is one-sided —
preemption, page faults and cache misses only ever make a run slower. The
fastest observed run is the best estimate and by far the most stable.

**Startup is subtracted, and it is not small.** Each backend's cost on a
zero-interaction term (`λx.x`) is measured and subtracted, because otherwise a
30 ms interpreter launch swamps a 0.05 ms reduction and the table ranks `execve`
rather than the runtime.

**Only large reductions are ranked.** A rate is trustworthy only when the
reduction is large compared to the startup subtracted from it. Rates that do not
clear that error bar are shown parenthesised and excluded from the ranking.
Skipping this step inverts the result: on the small workloads Zig appears to beat
C, which is an artifact of subtracting Zig's 34 ms baseline, not a real
difference.

## Findings

**1. The IC32 family agrees, exactly.** All five runtimes implementing the IC32
typed-node floating-dup model — C, Zig, Mojo, WASM, `ic_float` — produce
byte-identical normal forms on every workload they complete, *and* identical
interaction counts. Agreement on counts is stronger than conformance requires
and indicates they are genuinely running the same reduction strategy, not merely
landing on the same answer.

**2. Optimal sharing is real and measurable.** Parity of 2^N, computed as `NOT`
applied 2^N times:

| 2^N | interactions |
|---|---|
| 2^4 = 16 | 78 |
| 2^12 = 4,096 | 238 |
| 2^20 = 1,048,576 | 398 |
| 2^24 = 16,777,216 | 478 |

Interactions grow **linearly in N** (`20N − 2`) while the semantics grows
exponentially: parity of 16.7 million negations in 478 interactions. This is the
optimal-λ-evaluation speedup, falling out of the runtime unforced.

**3. Throughput** (geometric mean over the throughput tier):

| runtime | interactions/sec | vs best | startup |
|---|---|---|---|
| ic32 (C) | 34.9 M/s | 1.0× | 0.45 ms |
| ic32 (Zig) | 30.9 M/s | 1.1× | 34 ms |
| ic32 (Mojo) | 15.8 M/s | 2.2× | 48 ms |
| ic_ref (py) | 0.47 M/s | 75× | 29 ms |
| ic_float (py) | 0.15 M/s | 235× | 13 ms |
| ic32.wasm | unranked — cannot reach the scale | | 20 ms |

C's 34.9 M/s sits inside the 22–34 M/s that `IC32_RUNTIME.md` claims, measured
independently.

**4. The 100× startup gap is a fixable defect, not a language difference.** All
three native runtimes reserve the same 16M-slot (128 MB) heap, but:

```
ic32 (C)     calloc()                      -> kernel lazy zero pages, untouched   0.45 ms
ic32 (Zig)   gpa.alloc + @memset(heap, 0)  -> eagerly writes all 128 MB             34 ms
ic32 (Mojo)  List[UInt64](.., fill=0)      -> eagerly writes all 128 MB             48 ms
```

A workload touching a few thousand slots pays to zero 128 MB it never reads.
Invisible in interactions/sec, but the dominant term for short reductions —
which is most of them. Zig's `@memset` and Mojo's `fill=0` are the whole gap;
neither is required for correctness, since the runtimes bump-allocate and
initialise slots on use.

**5. Runtimes differ far more in *reach* than in speed.** Maximum readback depth,
found by doubling `exp 2^k`:

| runtime | deepest normal form read back | bound by |
|---|---|---|
| C / Zig / Mojo | ≥ 2,097,152 | not reached at 2^21 |
| ic_float (py) | 524,288 | time, not depth |
| ic_ref (py) | 65,536 | `whnf` step budget |
| ic32.wasm | 8,192 | V8 WASM call-depth cap |

The WASM ceiling reproduces the limitation `IC32_WASM.md` documents: recursive
`normal`/`whnf` overflow V8's call stack, and `-Wl,-z,stack-size` cannot lift it
because that sets the linear-memory shadow stack, not V8's. **This is the single
biggest gap between the WASM build and the native ones** — it is bit-identical
where it completes, but completes only 33 of 48 workloads.

**6. `ic_ref` fails silently, which is the worst failure mode.** On nested
exponentiation (tetration) `ic_ref` does not hang and does not error — it returns
a residual superposition, e.g. `(s (s &81{a,b}))` for `2^^3`, which reads back as
`s^2` instead of `s^16`. A caller counting `s` gets a plausible, wrong number.
This is outside the fragment `IC_REF.md` scopes it to (it validates single-level
higher-order duplication; tetration nests it), so it is a model limit rather than
a conformance bug — but it argues for `ic_ref` returning a stuck-term error
instead of a readable normal form.

**7. Ackermann marks the edge of the safe fragment.** `ack(m,n)` for m ≤ 1
reduces correctly on all six runtimes. At m ≥ 2 the iteration duplicates a term
that itself contains a duplicator, two independent duplicators end up sharing a
label, and reduction diverges — **on all six runtimes identically**. Kept as a
workload precisely to check that they agree on diverging.

## Head-to-head with HVM4

The files above compare TRVM's six runtimes to each other. These four compare
TRVM to **HVM4**, a separate Interaction Calculus runtime, by carrying *the same
bytes* to both engines:

| file | what it is |
|---|---|
| `hvm4_translate.py` | translates the pure-IC subset of HVM4 surface syntax into TRVM's |
| `nf_equiv.py` | alpha-equivalence for normal forms printed by the two engines |
| `hvm4_families.py` | generates the two scaling families, in HVM4 syntax |
| `hvm4_corpus.py` | runs HVM4's own 217-program test corpus through both engines |
| `hvm4_throughput.py` | wall-time comparison on programs with identical interaction counts |

```bash
clang -O2 -o /tmp/hvm4 $HVM4_SRC/src/hvm.c   # build HVM4 outside its repo
python3 bench/hvm4_families.py /tmp/cnot
python3 bench/hvm4_corpus.py
python3 bench/hvm4_throughput.py
```

The translator doubles as the portability classifier: a program is in the shared
fragment iff it translates. Anything using `#Ctr` constructors, pattern-matching
lambdas, native u32 or string sugar fails translation and is reported as
out-of-fragment, never silently skipped. It refuses to translate a term it
cannot consume entirely — an early version silently truncated `1 + 2 + 3 + 4` to
`1` and scored it as a pass.

### 8. Given the same term, the two engines agree exactly

Of HVM4's 217 test programs, 36 are in the shared pure-IC fragment and 29 run on
both engines. Of those, **23 produce alpha-equivalent normal forms, 6 differ only
in how a residual superposition is read back, and 0 genuinely disagree** — and
the interaction count is **identical on every single one**.

That agreement extends across four orders of magnitude. On HVM4's own `cnot_N`
family (an N-level doubling chain, every level reusing one label):

| N | negations | HVM4 | TRVM | |
|---|---|---|---|---|
| 12 | 4,096 | 57,396 | 57,396 | exact |
| 16 | 65,536 | 917,572 | 917,572 | exact |
| 18 | 262,144 | 3,670,092 | 3,670,092 | exact |

### 9. The famous "478 vs 234 million" gap was an encoding difference, not an engine one

An earlier version of this write-up compared TRVM's parity workload (478
interactions for 2^24 negations) against HVM4's `devs/bench/cnot_24.hvm`
(234,881,124) and concluded that ic32 achieves an optimal-sharing collapse HVM4
misses. **That was wrong: it compared two different programs.** The two encodings
have genuinely different sharing structure, and either engine given either
encoding reproduces the other's number:

| encoding | 2^24 negations | HVM4 | TRVM |
|---|---|---|---|
| doubling chain (`cnot_24`) | 16,777,216 | 234,881,124 | same (heap-capped locally) |
| Church exponentiation (`par_24`) | 16,777,216 | **478** | **478** |

`(A B)` computes `B^A`, so `(N 2)` builds 2^N by exponentiation and shares; an
explicit N-level doubling chain does not. The `20N − 2` collapse is a property of
the **encoding**, and HVM4 achieves it just as completely as TRVM does.

### 10. On identical work, HVM4 is ~3x faster per interaction

Because the counts match exactly, wall time on `cnot_N` is a pure engine
comparison — nothing about encoding or strategy is folded in:

| engine | M interactions/s | startup | fit R² | range |
|---|---|---|---|---|
| HVM4 | 67.0 | 134 ms | 0.9997 | N=18..22 |
| TRVM ic32 | 23.4 | ~0 ms | 0.9996 | N=14..19 |

The 2.9× ratio held across separate runs whose absolute numbers drifted (90 vs
31 M/s in another). Note this is *below* the ~56 M/s ic32 reaches on the
workloads in `bench.py` — this family is duplicator-heavy with a single reused
label, so it is a harder interaction mix, not a contradiction.

Each engine is fitted only over sizes where its own reduction dominates its own
startup. Fitting both over the same sizes reports HVM4 at 754 M/s, because its
115 ms launch exceeds the entire reduction at every size TRVM can reach. The
script prints R² and a reduce/startup ratio and flags any fit that fails them.

**TRVM's startup remains ~200× better** (0.5 ms vs 115 ms), so it wins outright
on short reductions, which is most of them.

### 11. ic32 segfaults on deep reduction — an unguarded C stack overflow

At `cnot_16` (~9×10⁵ interactions) ic32 **segfaults** on the default 8 MB stack.
It is not the heap: with `ulimit -s 65536` the same term completes correctly, and
it crashes identically with readback disabled, so it is the reduction recursion
rather than the printer.

This is distinct from ic32's *clean* `FATAL: heap overflow` (exit 2), which is
what `cnot_20` correctly produces at 1.5×10⁷ interactions against the 16M-slot
heap. So there are two ceilings, and only one of them is diagnosed:

| ceiling | where | behaviour |
|---|---|---|
| C stack | ~10⁶ interactions, 8 MB stack | **segfault, no diagnostic** |
| heap | 1.5×10⁷ interactions | clean `FATAL: heap overflow` |

HVM4 has neither ceiling here and reaches 2.3×10⁸ interactions. The stack limit
is the more serious of the two because it is silent, and it is reachable by
ordinary programs. It also echoes the WASM finding in §5: the same recursive
`normal`/`whnf` structure is what V8's call-depth cap truncates at 8,192.

### Caveats specific to this comparison

- `-C` matters. HVM4's default run stops at a residual term with unresolved
  duplicators (`cmul_c4_c4` prints `λa.λb.A₀;!A&C=B₀;...`), while TRVM's `normal`
  always performs the full readback. Comparing plain HVM4 output to TRVM
  compares two different questions, so `hvm4_corpus.py` runs both modes and
  reports each.
- The 6 "superposition" rows are a readback-contract difference, not a
  disagreement: `-C` enumerates a superposition into one result per branch,
  TRVM prints the superposition itself.
- One engine, one machine, one build (`clang -O2`). Ratios port, absolute
  numbers do not.

## Standing caveats

- Single machine, single run; absolute times are not portable, ratios are.
- `runtime/js/swarm.js` is excluded: it is a distributed multi-worker harness,
  not a term-on-stdin reducer, so it does not share this contract.
- The throughput tier includes readback (stringify + pipe) in wall time, since
  not every backend has a `-q` equivalent. It is paid by all of them equally.
