# ic32 Handoff Pack v3 — evidence-enable the runtime that exists
*Emitted by Lane A at round 12 (2026-08-18), superseding packs v1 and v2, which remain frozen and valid.*

## Read this first: v1 and v2 briefed the wrong task

Both earlier packs told Lane B to **build an independent ic32** — parser, floating-dup
heap, INTERACT + collapse, canonical readback — treating the JS kernel as an oracle to
diff against. That brief was written without `TRVM/runtime/` in view.

**`ic32` already exists, in four languages, in this repository:**

| implementation | status |
|---|---|
| `runtime/c/ic32.c` | packed-word native runtime, `./ic32 --test` → 13/13, normalizes a 500 000-deep term, ~22–34M interactions/s |
| `runtime/zig/ic32.zig` | third native implementation |
| `runtime/mojo/ic32.mojo` | fourth native implementation |
| `runtime/wasm/ic32.wasm` | 9.9 KB WebAssembly build, matching the reference bit-for-bit |
| `runtime/js/swarm.js` | ic32.wasm reduced coordination-free across real worker threads |

So milestones 1–4 and 6–8 of the old list are substantially **already built and passing**.
What none of the four carried was an identity layer: they compute, and could not say what
semantic state they had computed into. **That — and only that — is Lane B's work.**

## The mission, restated

Give the existing ic32 implementations the identity and evidence protocol, so the
execution plane and the evidence plane are joined by something a runtime computes rather
than by a shared directory. Do not build another evaluator. Do not transliterate the JS
kernel. Implement from `SEMSTATE-CANONICAL-v1.md` against each runtime's own
representation — the point of the exercise is that a *different* representation reaches
the *same* canonical bytes, which is what makes the canonical form a property of the
calculus rather than an artifact of one implementation.

**C is already done and is the worked example.** `ic32_canon.c` (shipped in this pack)
includes `ic32.c` verbatim with its main renamed — the runtime under test is the runtime
that ships — and implements §2–§5 over ic32's packed words: chase, live discovery order
over dup *cells* (ic32 has no Dup node; a dup is a heap cell reached through `T_DP0`/
`T_DP1` projections), the canonical fold, the two-phase signature with §5 compaction, and
SHA-256. Result: **48/48 states byte-identical to the JS oracle** — all 24 vectors, initial
state and normal form, signature *strings* not merely digests. `bridge_check.mjs` is the
gate, wired into `make test` as `gov-bridge`.

## Milestones (in order)

1. **Zig** — port §2–§5 to `ic32.zig`'s representation. 48/48 byte equality.
2. **Mojo** — same, against `ic32.mojo`. 48/48.
3. **WASM** — same, against `ic32_wasm.c`; this one additionally proves the canonical
   form survives a 32-bit/streaming target.
4. **Semantic film emission** (§10) from a native runtime — the first portable evidence
   object produced outside JavaScript.
5. **Cross-replay** (§10.5): films emitted by C/Zig/Mojo replayed by the JS oracle and
   vice versa. Every refusal must be one of §10.5's nineteen, and every refusal is a
   falsifier deliverable back to Lane A.
6. **Refinement receipts** (§11): a fast runtime proving refinement against the reference
   semantics. At this point the optimized evaluator and the governance system are one
   system rather than two that agree.

Only then optimize. A faster canonicalizer that changes a byte is a defect, not a win.

## Conformance targets — and one correction to the old packs

**Semantic conformance (binding on every implementation):**
- normal-form string equality against the corpus `nf` (24 targets);
- `semId` of it equal to `refinement_receipt.json`'s `nf_id` (24 targets);
- **canonical signature bytes** equal to `golden_prehash_vectors.json`, character for
  character, for the initial and normal-form state of every vector (48 targets);
- `sem_state_id` equal to SHA-256 of those bytes.

**Strategy conformance (binding only within a reduction strategy):**
`ref_interactions` is **not** a universal target, and packs v1/v2 were wrong to list
"24-vector count parity" as milestone #7. This repository's own conformance spec already
ruled it, at `docs/spec/conformance/README.md` §10.1:

> "The `ref_interactions` field records `ic_float`'s interaction count. This count is
> normative only for runtimes that claim to implement the same reduction strategy as
> `ic_float`. Other runtimes (native, optimal-sharing) are bound only by normal-form
> agreement."

The JS kernel matches on 18/24 and reports exactly that. An interaction count is
comparable only against a declared strategy identity; without one it is informational
evidence, never semantic identity. **Do not punish a faster evaluator for being faster.**

## Falsifiers before implementation

Ascending vs descending allocator (equal sem id); random heap-ID bijections including
mid-run (invariant); dead-entry injection (exec differs, sem equal); alpha-renaming
(equal — and equal at the BYTE level, not merely after hashing); label permutation
(equal); the same semantic state reached through different allocator histories (equal);
intentionally wrong DUP behaviour (bytes apart); the §5 compaction boundary at exactly
80 and 81 characters; one altered canonical locus in a film (replay refuses).

## Pack inventory (sha256 manifest in MANIFEST.json)

| file | role |
|---|---|
| `ic32_canon.c` | **the worked example** — C reaching the golden bytes over packed words. Read it for the representation mapping, not for the algorithm; the algorithm is the spec |
| `bridge_check.mjs` | the cross-plane gate: byte equality first, digest second, and a missing binary exits nonzero rather than reading as green |
| `golden_prehash_vectors.json` | the 48 byte-level targets, plus the §5 compaction boundary with a self-proving pre-compaction reconstruction |
| `SEMSTATE-CANONICAL-v1.md` | the language-neutral canonical-form spec — §§2–5 are what you implement |
| `trvm_law_kernel.mjs` | the conformance oracle, v1.1.0. Importable with no side effects; exports `stateSignature`/`semStateSignature` so you can diff without reading it as an implementation |
| `refinement_receipt.json` | 24 golden per-term rows: `nf_id`, `sem_film_id`, exec A/B film ids, the allocator split |
| `scheduler_certificate.json` | 144 golden receipts (24 vectors x 6 schedulers); `nf_id` must match, `final_state_id` is execution identity and is expected to differ |
| `invariant-grid.json` | v1.8.0 law registry (46 entries) and every schema/commitment-domain declaration |
| `golden_sem_ids.json` | convenience projection; derived — the receipt is authoritative |

**The corpus is not in this pack.** It lives at `docs/spec/conformance/vectors/normalize.json`
and is the repository's single authoritative copy. The kernel's embedded set is a fallback
for standalone use and is bound to it by `CONF-2`: both must commit to the same hash under
the four-field corpus projection, and "unreachable" is reported as unchecked, never as
agreement.

## House rules that travel with the pack

Falsifiers before implementation, and every by-design falsification stays red in a
battery. Every refusal is declared and named; batteries assert exact refusal strings.
Receipts are deterministic across double runs. Frozen means frozen: the calculus and this
pack's laws do not move from Lane B; mismatches come back as witnesses. And a skipped
check is never a passing one — say "unchecked" and exit nonzero.
