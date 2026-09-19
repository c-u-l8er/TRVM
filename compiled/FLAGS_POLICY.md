# The C backend's compiler flags — the POLICY (ruled by Travis, 2026-09-19)

**This supersedes `FLAGS_POLICY_RECOMMENDATION.md`**, which stays beside it as the packet that was ruled on. The
recommendation offered six lines and a recommendation for each; Travis ruled **"adopt as recommended"** on
2026-09-19. What follows is therefore policy, and the last section records what the ruling changed and what was
measured after it changed.

## 1. The policy

| # | line | ruling |
|---|---|---|
| 1 | The admitted baseline | **`-O2`.** Every admission in `results-battery.json` / `results-c2-backend.json` is at `-O2`; another flag string is another artifact and needs its own battery run with controls. |
| 2 | `-march=native` in an admitted identity | **Never.** It binds the object to the build CPU while the flag string says only "native". It stays a BENCH row (`C_VARIANTS`), labelled with the CPU it was measured on. |
| 3 | A portable wider target (`-march=x86-64-v3 -mtune=generic`) | **Not adopted.** There is no measured need: `-O3 -march=native` reads as `-O2` on the v2 MAC worlds and slightly worse on the packed chains (README §2d). The door stays open on the same terms as line 1 — a second admitted identity after its own full run. |
| 4 | `-O3` | **Not admitted.** Measured no gain on v2, slightly worse on chains; more code motion for the same laws. |
| 5 | The identity | **Adopted: the compiler and the resolved target are part of `cbknd2-`.** See §2. |
| 6 | `-frecord-gcc-switches` | **No.** It embeds the command line in the `.so` and defeats the byte-reproducibility the executor proposal rests on; the identity already carries the flags. |

Lines 2 and 4 are prohibitions on what may be *admitted*, not on what may be measured. Benching `-O3
-march=native` is fine and is how lines 3 and 4 would ever be revisited; what is refused is an admission
record carrying those flags.

## 2. What choice 5 changed, exactly

`cbknd2-` was `sha256(sem ‖ profile ‖ flags ‖ source)`. It is now

```
cbknd2- + sha256(sem ‖ profile ‖ flags ‖ TOOLCHAIN ‖ source)
```

where `TOOLCHAIN` is three lines, each one read back **from the compiler with these flags applied**
(`emit_c.toolchain_identity`), never assumed:

```
cc gcc (GCC) 16.2.1 20260810
target x86_64-pc-linux-gnu
march=x86-64 mtune=generic
```

The third line is the point. `gcc -Q --help=target` is what *resolves* `native`: on this laptop
`-march=native` resolves to `march=znver5 mtune=znver5`, while the flag string — all that the identity used to
carry — says the six letters `native`. Two machines could therefore share one `cbknd2-` id over two different
machine codes, and a gcc upgrade left the id untouched entirely.

**A consequence that had to be handled with it.** The object cache was keyed by `sha256(flags ‖ source)` alone,
so a gcc upgrade served the *old* `.so` under the *new* id — which would have made choice 5 worse than no
change: a new identity on old bytes. The cache is now **namespaced by the toolchain**
(`~/.cache/trvm-compiled/tc-<16 hex of sha256(TOOLCHAIN)>/<key>.so`) while the key itself is untouched, so the
`source_sha256` the results files report keeps its documented meaning — `sha256(flags + "\n" + source)` for v2,
`sha256(source)` for v1 — and did not move for a single world.

**What was deliberately NOT changed.** Choice 5 names `emit_c2` only, and v1 (`cbknd-`) is left as it is: built
at `-O2` with no `TRVM_CFLAGS` hook, its id carrying neither flags nor toolchain. That is a real remaining gap
and it is asserted as such in `flags_identity_test.py` test 8, so a later ruling on v1 has to change a test
rather than slip in. v1's *object cache* is namespaced like v2's, because the stale-object hazard is the same
one and it is a correctness hazard, not an identity nicety.

## 3. What was measured after the ruling, on the day

- **`laws_gate.py --check` HELD, before and after** — 19 worlds × 4 emitters byte-identical. The identity moved;
  not one byte of any emitted program did. That is the property that makes this change safe to make at all.
- **`flags_identity_test.py` 10/10** (new). It is written against the *defect*, not the feature: each case
  computes the pre-ruling formula alongside the new one on the same inputs and asserts the old one could not
  have seen the difference. Test 5 simulates a gcc upgrade; test 6 simulates the same `-march=native` on two
  CPUs; test 3 asserts the probe *resolves* `native` instead of echoing it; test 4 asserts the `-O` level does
  not also perturb the toolchain line (it is already in the flag string, and the two halves must not say the
  same thing twice); test 9 is the stale-object hazard; test 10 builds a real world end to end.
- **`battery_bend.py --emitter c2 --controls` re-run: ALL AGREE, 59 pairs, 0 worlds refused; CONTROLS: ALL
  CAUGHT, AS PREDICTED.** All **18** `cbknd2-` identities moved; **0** `source_sha256` moved; the 267 objects
  were rebuilt into the new toolchain namespace. The reference side was served from the battery's reference
  cache, correctly: the calculus is not what this change touches, and the compiled side is what was rebuilt and
  re-compared.
- **`executor_test.py` 13/13** (T8's substrate half) — it asserts `cbknd2-` and `flags == ["-O2"]`, both still
  true, and its v1 identity assertion against `results-payload.json` is untouched because `payload.py` uses v1.

## 4. What a future ruling would have to move

- Line 3 (`-march=x86-64-v3 -mtune=generic` as a second admitted identity) costs one battery run with controls
  and a second results file. It buys nothing on this laptop; it exists for a machine class.
- v1's identity (§2, last paragraph). It needs a `TRVM_CFLAGS` hook first, which it does not have.
- A compiler that does not answer `-Q --help=target` (clang does not) records `march=<unresolved>`. The two
  lines it does answer still move the id on a compiler change, so the identity degrades rather than breaks —
  but it degrades, and that is said here rather than discovered later. Nothing in the stack builds with clang
  today.

## 5. Sources (carried over from the recommendation, which cites them in full)

GCC "Integers implementation" (sign-extending `>>`, modulo conversion — the two implementation-defined
behaviours the emitted MAC leans on); the x86-64 microarchitecture levels and `-march=<level>` implying
`-mtune=generic`; `-frecord-gcc-switches` defeating local determinism.
