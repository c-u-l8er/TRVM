> **SUPERSEDED 2026-09-19 — Travis ruled "adopt as recommended". The policy is `FLAGS_POLICY.md` beside
> this file; it is what to read and what to cite. This page is kept unaltered as the packet that was ruled
> on, because a ruling is only as good as the alternatives it was given.**

# The C backend's compiler flags — a RECOMMENDATION for Travis's ruling, not a policy (2026-09-18, night)

The handoff lists "a compiler-flags policy for the C backend" as Travis's decision. This is the one page that lets it be
ruled with a word per line. Nothing here changes what is admitted: the battery's admission stays at plain `-O2`
(README §2d) until a ruling says otherwise. Written by the backend's author; a self-review is not a review.

## 1. What is already true, and measured

- **Flags are in the identity.** The C v2 step's id is `cbknd2-` + sha256(sem, profile, flags, source) (`emit_c2.py`),
  so a step built with different flags is a different artifact and needs its own admission. The C v1 id (`cbknd-`) does
  NOT carry flags; v1 is built at `-O2` only and has no `TRVM_CFLAGS` hook.
- **The identity does not carry the compiler's version or the target.** gcc 16.2.1 here (`gcc --version`); `-march=native`
  resolves to this laptop's CPU at build time and the flag string says only "native", so two machines can share an id and
  disagree in machine code. The executor proposal measured byte-reproducibility of the build on this toolchain only
  (`wek/b2/trvm/COMPILED_EXECUTOR_PROPOSAL.md`: three builds, one sha).
- **Measured, README §2d, one run:** `-O3 -march=native` on v1 ≈ 2× on the MAC worlds — and the width-split MAC got the
  same 2× at `-O2` portably (it was the i128 codegen); on v2, `-O3 -march=native` reads as `-O2` on the MAC worlds and a
  little worse on the packed chains. There is no measured win left for the flags on v2.
- **The emitted C leans on two GCC-defined behaviours the C standard leaves implementation-defined**, and both are what
  the MAC needs: signed `>>` on a negative value is an arithmetic (sign-extending) shift, and an out-of-range conversion
  to a signed type reduces modulo 2^N without a signal (GCC "Integers implementation", quoted below). Neither is changed
  by `-O` level or `-march`; both would be a question for any OTHER compiler (clang documents the same; MSVC does not
  matter here). No signed-overflow UB is reachable by construction (|acc| ≤ 2^(2w) ≤ 2^126 in i128, ≤ 2^62 in i64), so
  `-fwrapv` is not needed and would only hide a bound bug the battery is meant to catch.

## 2. The choices, one line each

| # | choice | recommendation | why |
|---|---|---|---|
| 1 | The admitted baseline | **`-O2`, as now** | the only flags the battery has admitted on every pair; no measured win above it on v2 |
| 2 | `-march=native` in an admitted identity | **never** | binds the object to the build CPU while the identity string says "native"; two machines, one id, two codes. Keep it as a BENCH row only (`C_VARIANTS`), labelled with the CPU |
| 3 | A portable wider target | **allow ONE named level, `-march=x86-64-v3 -mtune=generic`, as a second admitted identity — only after its own full battery run with controls** | the named levels (GCC ≥ 11) are neutral and reproducible: the flag string names the ISA, not the machine; `-mtune=generic` keeps the code the same on any v3 CPU. Not adopted here: there is no measured need (choice 1) |
| 4 | `-O3` | **not admitted** | measured no gain on v2, slightly worse on chains; more code motion for the same laws |
| 5 | The identity | **add the compiler's `--version` line and the effective target (`gcc -Q --help=target` for `-march`/`-mtune`, or `-dumpmachine` + the resolved `-march`) to what `cbknd2-` hashes** | closes the gap in §1: today a rebuild with a new gcc keeps the old id. A code change, small, in `emit_c2.py`; needs a battery re-run because every id changes |
| 6 | Recording flags in the object (`-frecord-gcc-switches`) | **no** | it embeds the command line in the `.so` and breaks the byte-reproducibility the executor proposal relies on; the identity already carries the flags |

## 3. What a ruling starts

- Rule 1–2 and 4–6 as recommended: `emit_c2.py` gains the compiler line and target in the id (choice 5), `battery_bend.py
  --emitter c2 --controls` is re-run once so `results-c2-backend.json` carries the new ids, `-march=native` stays a bench
  row. One session.
- Rule 3 "yes": a second results file, `results-c2-v3-backend.json`, from `TRVM_CFLAGS="-O2 -march=x86-64-v3 -mtune=generic"
  battery_bend.py --emitter c2 --controls`, and the executor proposal's identity gains the target. Nothing is faster for it
  on this laptop by §1's measurement; it exists for a machine class, not for speed.
- Rule anything else: say which line.

## 4. Sources

- GCC, "Integers implementation" (implementation-defined behaviour): *"Signed '>>' acts on negative numbers by sign
  extension."* and *"For conversion to a type of width N, the value is reduced modulo 2^N to be within range of the type;
  no signal is raised."* — https://gcc.gnu.org/onlinedocs/gcc/Integers-implementation.html
- x86-64 microarchitecture levels (v2/v3/v4), the ABI proposal and GCC 11 / LLVM 12 support; `-march=<level>` implies
  `-mtune=generic`: https://groups.google.com/g/x86-64-abi/c/8tcCaulD7dc , https://maskray.me/blog/2022-08-28-march-mcpu-mtune ,
  https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html
- `-frecord-gcc-switches` embeds the command line in the object and defeats local determinism:
  https://blog.conan.io/2019/09/02/Deterministic-builds-with-C-C++.html
