# ic32 Handoff Pack v2 — Lane B boundary objects
*Emitted by Lane A at round 10 (2026-08-18), superseding pack v1. The two-lane split is in effect. v1 remains frozen and valid; v2 adds the pre-hash byte vectors that closed its one declared gap, and moves the kernel to v1.1.0 (additive — same calculus, now importable).*

## The lanes

- **Lane A — World/Warrant/maintenance** (the session that emitted this pack):
  round 9 shipped supervised maintenance; round 10 shipped the kernel's
  additive module interface at 1.1.0 and the pre-hash byte vectors below.
  Next is CP5–CP7 via a kernel-computation warrant, now unblocked.
- **Lane B — ic32**: an independent runtime against the frozen calculus.
  **This pack is Lane B's entire inbound interface.** No mutable source files
  are shared between the lanes; the shared objects are laws, vectors, schemas,
  the canonicalization spec, and golden fixtures.

## Mission (verbatim contract for the ic32 session)

Build an independent ic32 implementation of the frozen TRVM calculus contract.
Treat the JS v1.1.0 kernel as a conformance oracle, not as source code to
transliterate — including its exports, which exist so you can diff against it
without reading it as an implementation. The implementation must satisfy the existing 24-vector corpus,
semantic-state identity contract, interaction counts, normal forms, scheduler
behavior, and `TRVM-SEMFILM-v1.1` portable replay interface. **Do not change
the frozen calculus laws to make ic32 pass.** Any mismatch must first be
classified as implementation bug, underspecified contract, or genuine
refinement failure and recorded with an executable witness — falsifiers flow
back to Lane A; semantics never change silently.

## Milestones (in order; do not optimize before #12)

1. Parser / term representation
2. Floating-dup heap representation
3. INTERACT + collapse relation
4. Canonical readback
5. `semStateId`-compatible canonical serialization — **the load-bearing one**;
   implement from `SEMSTATE-CANONICAL-v1.md`, verify against the shipped
   golden **signature bytes** in `golden_prehash_vectors.json` (48 targets,
   character for character) and their digests, never by copying the JS hasher
6. 24-vector deterministic normal-order parity
7. 24-vector count parity (interaction counts)
8. free/adversarial scheduler parity
9. semantic-film emission
10. JS ↔ ic32 cross-replay
11. refinement receipts
12. only then optimize

## Falsifiers before implementation

Ascending vs descending allocator; random heap-ID bijections (including
mid-run); dead heap injection; alpha-renaming; label permutations; alternate
internal memory layouts; same semantic state reached through different
allocator histories; intentionally wrong DUP behavior; intentionally wrong
interaction counting; a semantic film with one altered canonical locus;
JS-generated film replayed by ic32 and vice versa.

## Pack inventory (all frozen; sha256 manifest in MANIFEST.json)

| file | role |
|---|---|
| `trvm_law_kernel.mjs` | the conformance **oracle**, v1.1.0 — run it, import it, diff against it; never edit it or transliterate it. The calculus is identical to v1.0.2; 1.1.0 adds only the module interface and the signature entry points |
| `golden_prehash_vectors.json` | **new in v2** — the canonical signature STRINGS for all 24 vectors, initial and normal-form states, plus the §5 compaction boundary with a self-proving pre-compaction reconstruction. Every signature sha256s to its own id; every `nf_id` is anchored to `refinement_receipt.json` |
| `invariant-grid.json` | v1.8.0 — the law registry (46 entries, including `digest.canonical-bytes@1`) and every schema/commitment-domain declaration (`TRVM-SEMFILM-v1.1`, film refusal vocabulary, state_identity, refinement_receipt sections) |
| `scheduler_certificate.json` | 144 golden receipts (24 vectors × 6 schedulers): per-run nf_id (semantic — must match), final_state_id (execution — expected to differ), film ids, corpus commitment |
| `refinement_receipt.json` | 24 golden per-term entries: nf_id, sem_film_id, exec A/B film ids, the A/B allocator split with sem-chain equality |
| `SEMSTATE-CANONICAL-v1.md` | the language-neutral canonical-form spec for milestone #5, extracted from the oracle at v1.0.2 and unchanged by the 1.1.0 bump (the canonical form did not move — only its publication did), with worked examples verified against shipped oracle output and, at v2, §5.1/§11 pointing at the byte vectors |
| `golden_sem_ids.json` | convenience projection: the 24 vectors (source term, expected nf, reference interaction count) joined with their refinement-receipt rows, with provenance digests — derived; the receipt is authoritative |
| `MANIFEST.json` | sha256 of every file above — verify before starting; a drifted pack is not this pack |

## The v1 gap, closed (round 10)

Pack v1 shipped with one declared gap: golden **pre-hash byte** vectors — the
canonical signature strings themselves, not just their digests — which required
the kernel to gain a module interface at 1.1.0. **That is done and this pack
carries them.** Kernel v1.1.0 is additive: the calculus is untouched, and the
proof is that `cert_id` and all 144 scheduler receipts are byte-identical across
the bump (round-10 ledger, item 4). `stateDigest` is now *defined* as
`sha256(stateSignature)`, so the shipped bytes are the digest's actual preimage
rather than a parallel re-derivation that could disagree with the hasher.

For milestone #5 this changes the target from digest equality to **byte
equality** (spec §11 rung 3, 48 targets). When your canonical form is wrong you
now see *where*, which is the difference between a conformance oracle and a
debugger.

Two things the kernel's new interface gives you directly: importing it has no
side effects and rewrites no artifact (the battery runs only when the file is
the entry module), and `stateSignature`/`semStateSignature` are exported, so you
can diff against the oracle without transliterating it. The house rule stands
unchanged — **implement §§2–10 yourself; the oracle is for diffing, never for
copying.**

## Still owned by Lane A

Worker-domain isolation for derivations (declared v-next since round 9.2), and
CP5–CP7 via kernel-computation warrants whose witnesses are semantic films —
the round that unifies the two portable evidence objects. Neither blocks any
milestone in this pack.

## House rules that travel with the pack

Falsifiers before implementation, and every by-design falsification stays red
in a battery. Every refusal is declared and named; batteries assert exact
refusal strings. Receipts are deterministic across double runs. Frozen means
frozen: the kernel and this pack's laws do not move from Lane B; mismatches
come back as witnesses.
