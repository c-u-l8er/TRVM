# ic32 Handoff Pack — Lane B boundary objects
*Emitted by Lane A at round 9 (2026-08-18). The two-lane split is now in effect.*

## The lanes

- **Lane A — World/Warrant/maintenance** (the session that emitted this pack):
  round 9 shipped supervised maintenance; next is CP5–CP7 via a
  kernel-computation warrant (kernel module interface at 1.1.0, additive).
- **Lane B — ic32**: an independent runtime against the frozen calculus.
  **This pack is Lane B's entire inbound interface.** No mutable source files
  are shared between the lanes; the shared objects are laws, vectors, schemas,
  the canonicalization spec, and golden fixtures.

## Mission (verbatim contract for the ic32 session)

Build an independent ic32 implementation of the frozen TRVM calculus contract.
Treat the JS v1.0.2 kernel as a conformance oracle, not as source code to
transliterate. The implementation must satisfy the existing 24-vector corpus,
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
   golden digests, never by copying the JS hasher
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
| `trvm_law_kernel.mjs` | the conformance **oracle**, frozen at v1.0.2 — run it, diff against it, never edit it or transliterate it |
| `invariant-grid.json` | v1.5.0 — the law registry (41 entries) and every schema/commitment-domain declaration (`TRVM-SEMFILM-v1.1`, film refusal vocabulary, state_identity, refinement_receipt sections) |
| `scheduler_certificate.json` | 144 golden receipts (24 vectors × 6 schedulers): per-run nf_id (semantic — must match), final_state_id (execution — expected to differ), film ids, corpus commitment |
| `refinement_receipt.json` | 24 golden per-term entries: nf_id, sem_film_id, exec A/B film ids, the A/B allocator split with sem-chain equality |
| `SEMSTATE-CANONICAL-v1.md` | the language-neutral canonical-form spec for milestone #5, extracted from the oracle at v1.0.2, with worked examples verified against shipped oracle output |
| `golden_sem_ids.json` | convenience projection: the 24 vectors (source term, expected nf, reference interaction count) joined with their refinement-receipt rows, with provenance digests — derived; the receipt is authoritative |
| `MANIFEST.json` | sha256 of every file above — verify before starting; a drifted pack is not this pack |

## Known gap, owned by Lane A

Golden **pre-hash byte** vectors (the canonical signature strings themselves,
not just their digests) require the kernel to gain a module interface at
1.1.0 (additive; the calculus stays frozen). That extraction is Lane A's
committed next-round deliverable, recorded in the round-9 ledger. Until then,
milestone #5's conformance target is digest equality against the shipped
golden digests plus the spec's §12 falsifier battery, climbing the spec's §11
conformance ladder (the rotating-schedule `sem_film_id` rung is the strongest
single number available today).

## House rules that travel with the pack

Falsifiers before implementation, and every by-design falsification stays red
in a battery. Every refusal is declared and named; batteries assert exact
refusal strings. Receipts are deterministic across double runs. Frozen means
frozen: the kernel and this pack's laws do not move from Lane B; mismatches
come back as witnesses.
