# E2 Addendum — the cross-log merge seam, measured (v2.2 + probe)

*Companion to E2_RESULTS.md v2.2. The 27/27 battery is reproduced and stands.
This note corrects one sentence of the results prose, on external review, with
a measurement (`probe_claim_merge.py`). Stage One code is untouched.*

## The claim under review

E2_RESULTS v2.2 closes: "The claim-set model is precisely the structure that
should merge across replicas via boundary ports — the recognition layer was
designed mergeable on purpose, so stage three inherits it rather than
reinventing it."

Half of that is proven; half was overstated. The review's counter: the stored
entry `claims[event_id][payload_digest] = (status, receipt)` is only half
mergeable — the digest keyset is a grow-only set, but the values encode a
particular log's acceptance history.

## What the probe measures

Two legitimate Stage One logs (the equivocation matrix's P3/P4: Block and Door
under one event identity, opposite cross-batch orders — log A accepts Block,
log B accepts Door):

**A. The recognition layer merges as stored.** Digest keysets identical across
the two logs; union merge order-independent. The "designed mergeable on
purpose" clause is true — of this layer.

**B. The acceptance annotations do not merge as stored.** Log A holds
`block→accepted, door→conflict`; log B the reverse. Last-writer-wins union is
merge-order-dependent (A+B ≠ B+A, demonstrated); keep-both yields two
"accepted" digests for one event with no log attribution. "The claim-set
model … should merge" is false of the entries as stored.

**C. The review's split makes both layers merge — and it is derivable from
existing state.** `ObservedClaimFact {event_id, payload_digest}` unions
order-independently; `AdmissionReceipt {log_id, event_id, accepted_digest,
policy, effect}` unions order-independently *as evidence about logs*. After
the merge: recognition of the event derives to `disputed` (unchanged), and the
store answers the settlement question directly — which log accepted which
digest (`{block: [logA], door: [logB]}`). The acceptance divergence becomes
recognizable evidence instead of a silent contradiction. No Stage One change
was needed to compute either projection.

## The corrected sentence

> The **recognition layer** of the claim-set model merges across replicas as
> stored (grow-only digest sets; proven order-independent). The **acceptance
> annotations** are log-relative and do not merge; before replication they
> must be split out as log-scoped AdmissionReceipts, which then merge as
> evidence and make cross-log acceptance divergence itself recognizable.
> Both projections are derivable from the current state, so Stage Three
> inherits the boundary, not a rewrite.

## Status

- 27/27 v2.2 battery: reproduced.
- Seam: measured (probe A/B/C above), pinned as an executable regression for
  the Stage Three boundary.
- Stage One: unchanged; its per-log determinism guarantee is unaffected.
- Next inflection (unchanged by this note, reinforced by it): the reducer
  binding — portable canonical encoding, same fixtures lowered to
  runtime/python, per-epoch film comparison. The semantic instrument is ready;
  the binding is the open frontier.

## Reproduce

```
python3 e2_run.py               # 27/27
python3 probe_claim_merge.py    # A merges / B doesn't / C split merges both
```
