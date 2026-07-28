# IC32 Benchmark Results

**Date:** 2026-07-27
**Hardware:** AMD Ryzen AI 9 HX 370 (Zen 5, 12C/24T, boost to 5.16 GHz), 32 GB DDR5
**OS:** Arch Linux, kernel 6.18.6-arch1-1
**Compiler:** GCC 15.2.1

## Summary

Best observed throughput: **93.6 M interactions/s** (PGO+LTO on fib_25).
Geometric mean across workloads: ~65 M interactions/s (varies by flag).

No single flag configuration dominates all workloads. The results are
workload-sensitive due to different branch patterns and memory access profiles.

## Optimization Flags Tested

| Flag | Command |
|---|---|
| `-O2` | `gcc -O2 -o ic32 ic32.c` |
| `-O3 -march=native` | `gcc -O3 -march=native -o ic32 ic32.c` |
| `-Ofast -march=native` | `gcc -Ofast -march=native -o ic32 ic32.c` |
| `-O3 -march=native -flto` | `gcc -O3 -march=native -flto -o ic32 ic32.c` |
| `-O3 -march=native` + PGO | profile-generate, train on mult/fib/exp/tetration, profile-use |
| `-O3 -march=native -flto` + PGO | same PGO training + LTO |

All builds pass the full self-test battery (13/13).

## Throughput by Workload (M interactions/s, min of 7 runs)

Higher is better. Each cell shows `wall_ms  M/s`.

| Workload | Interactions | -O2 | -O3 native | -Ofast native | -O3 LTO | PGO | PGO+LTO |
|---|---|---|---|---|---|---|---|
| mult 300x300 | 180,600 | 3.3 ms / 54.8 | 3.1 ms / 57.8 | 2.9 ms / 63.3 | 2.9 ms / 62.8 | 3.0 ms / 60.2 | 3.2 ms / 57.1 |
| mult 700x700 | 981,400 | 14.3 ms / 68.6 | 15.9 ms / 61.7 | 17.5 ms / 56.1 | 15.6 ms / 63.1 | 14.6 ms / 67.4 | 15.4 ms / 63.7 |
| fib(22) | 197,126 | 2.2 ms / 89.8 | 2.8 ms / 70.2 | 2.9 ms / 67.5 | 2.4 ms / 83.2 | 2.6 ms / 76.6 | 2.8 ms / 69.5 |
| fib(25) | 832,606 | 12.3 ms / 67.9 | 13.4 ms / 62.0 | **9.1 ms / 92.0** | **8.9 ms / 93.1** | 11.0 ms / 75.5 | **8.9 ms / 93.6** |
| exp 2^16 | 131,266 | 1.9 ms / 67.5 | 2.2 ms / 60.3 | **1.5 ms / 88.5** | 2.2 ms / 60.7 | 1.7 ms / 76.1 | 2.2 ms / 58.9 |
| exp 2^20 | 2,097,378 | **34.0 ms / 61.6** | 38.6 ms / 54.3 | 37.2 ms / 56.4 | 38.3 ms / 54.8 | 35.3 ms / 59.4 | 39.7 ms / 52.8 |
| tetration 2^^4 | 131,204 | 2.1 ms / 62.2 | **1.9 ms / 70.1** | 2.2 ms / 61.0 | 2.0 ms / 65.1 | 2.0 ms / 66.5 | 2.1 ms / 62.9 |

## Winner Per Workload

| Workload | Best Flag | M/s |
|---|---|---|
| mult 300x300 | -Ofast -march=native | 63.3 |
| mult 700x700 | -O2 | 68.6 |
| fib(22) | -O2 | 89.8 |
| fib(25) | PGO+LTO | 93.6 |
| exp 2^16 | -Ofast -march=native | 88.5 |
| exp 2^20 | -O2 | 61.6 |
| tetration 2^^4 | -O3 -march=native | 70.1 |

## Key Observations

1. **No clear winner across all workloads.** The reduction engine's hot loop
   (`whnf`) is a tight switch over 7 tag values with pointer chasing through the
   heap. Different workloads exercise different branches and memory access
   patterns, so aggressive optimization helps some and hurts others.

2. **-O2 is competitive or best on 3/7 workloads.** GCC's -O3 adds
   vectorization and more aggressive inlining that can actually hurt this
   pointer-chasing, branch-heavy code. The heap is accessed through unpredictable
   indices, so SIMD and prefetching provide little benefit.

3. **-Ofast and LTO shine on fib(25) / exp 2^16** — workloads with deep
   duplication chains where `-ffast-math` relaxations and cross-TU inlining help
   the DUP-LAM/DUP-SUP paths.

4. **PGO provides modest (~5-15%) improvement on some workloads** but not
   uniformly. The training set (4 workloads) covers the main code paths but the
   branch patterns are workload-specific.

5. **Process startup is negligible** (0.34 ms via `calloc` lazy-zero). The
   reduction itself dominates even at the smallest workload sizes tested.

## Cross-Runtime Comparison (from bench.py --quick)

On the throughput tier (startup-subtracted):

| Runtime | mult 300x300 | fib(22) | tetration 2^^4 | exp 2^14 |
|---|---|---|---|---|
| ic32 (C, -O3 native) | 6.2 ms | 3.6 ms | 4.2 ms | 1.1 ms |
| ic_float (py) | 1370 ms | 976 ms | 585 ms | 97 ms |
| ic_ref (py) | 686 ms | 140 ms | 7.2 ms | 64 ms |

**ic32 is 90-220x faster than ic_float (Python) on these workloads.**

## HVM4 Comparison

`hvm4_throughput.py` exists but requires `hvm4` binary at `/tmp/hvm4` and
pre-generated corpus files at `/tmp/cnot/`. Not run in this session (HVM4 binary
not available). The script is designed to compare interaction-per-second rates on
identical programs (cnot_N family) where both engines perform the same number of
interactions, isolating engine speed from encoding differences.

## Recommended Build

For general use: `gcc -O2 -o ic32 ic32.c` — simplest, competitive everywhere.

For maximum throughput on heavy dup workloads: `gcc -O3 -march=native -flto -o ic32 ic32.c`
with PGO training on representative inputs (93.6 M/s peak on fib(25)).
