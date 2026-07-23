"""probe_claim_merge.py -- the cross-log merge seam, measured.

The v2.2 equivocation matrix proves the RECOGNITION layer converges WITHIN
a world: identical observed-digest sets under every arrival pattern. The
open review question is what happens ACROSS worlds (logs): E2_RESULTS
says the claim-set model "should merge across replicas via boundary
ports"; the review counters that the stored entry

    claims[event_id][payload_digest] = (status, receipt)

is only half mergeable -- the digest KEYSET is a grow-only set, but the
VALUES encode this log's acceptance history, so two legitimate Stage One
logs that accepted different payloads carry contradictory annotations.

This probe measures both halves with the actual model (no model changes):

  A) the digest keysets of two divergent-acceptance logs are IDENTICAL,
     and their union-merge is order-independent -- recognition merges.
  B) the stored (status, receipt) values CONTRADICT across the two logs,
     and no annotation-level merge is well-defined: last-writer-wins is
     merge-order-DEPENDENT (demonstrated), and keep-both yields two
     "accepted" digests for one event with no log attribution.
  C) the review's split resolves it, derivably from existing state:
       ObservedClaimFact {event_id, payload_digest}        -- G-set, merges
       AdmissionReceipt  {log_id, event_id, accepted_digest,
                          policy, effect}                  -- G-set OF
     EVIDENCE, merges as facts-about-logs. After union: recognition of the
     event is still derived (disputed), and the merged store can answer
     the Stage Three settlement question "which log accepted which
     digest" -- the acceptance divergence becomes recognizable evidence
     instead of a silent contradiction.

Stage One is untouched; this pins the boundary Stage Three must preserve.
"""
import copy
import random
from e2_model import World, RandomChooser, H
from e2_run import E, digest_event

POLICY = "stage1-first-in-log-order"

def build_log(order):
    """A world fed the Block/Door equivocation across separate batches in
    the given order -- the matrix's P3/P4 (two legitimate Stage One logs)."""
    b = E(1, "STAMP", kind="block", writer="A")
    d = E(1, "STAMP", kind="door", writer="A")
    evs = {"block": b, "door": d}
    w = World()
    for kind in order:
        w.step([copy.deepcopy(evs[kind])], RandomChooser(random.Random(5)))
    return w

def observed_facts(w):
    """ObservedClaimFact projection: {(event_id, payload_digest)} -- what was
    claimed, with no acceptance annotation. Derivable from existing state."""
    return {(eid, dg) for eid, m in w.claims.items() for dg in m}

def admission_receipts(w, log_id):
    """AdmissionReceipt projection: which digest THIS log accepted, under
    which policy, with what effect. Log-scoped by construction."""
    out = set()
    for eid, m in w.claims.items():
        for dg, (status, receipt) in m.items():
            if status == "accepted":
                out.add((log_id, eid, dg, POLICY, str(receipt)))
    return out

def naive_annotation_merge(a, b):
    """The merge E2_RESULTS' closing line implies is free: union the claim
    dicts, values and all. Last-writer-wins on value collisions."""
    out = {}
    for src in (a, b):
        for eid, m in src.claims.items():
            out.setdefault(eid, {}).update(m)
    return out

if __name__ == "__main__":
    wA = build_log(["block", "door"])   # log A: accepts block, door conflicts
    wB = build_log(["door", "block"])   # log B: accepts door, block conflicts
    eid = H("event", "A", 1)

    # ---- A) recognition layer merges: identical keysets, order-free union
    ksA = {e: frozenset(m) for e, m in wA.claims.items()}
    ksB = {e: frozenset(m) for e, m in wB.claims.items()}
    union_AB = {e: ksA.get(e, frozenset()) | ksB.get(e, frozenset())
                for e in set(ksA) | set(ksB)}
    union_BA = {e: ksB.get(e, frozenset()) | ksA.get(e, frozenset())
                for e in set(ksA) | set(ksB)}
    assert ksA == ksB, "divergent-acceptance logs saw different claim sets?"
    assert union_AB == union_BA == ksA
    print("A) recognition layer: digest keysets IDENTICAL across the two "
          "logs; union merge order-independent.  [MERGES]")

    # ---- B) the seam: stored annotations contradict; no free merge exists
    stA = {dg: s for dg, (s, _) in wA.claims[eid].items()}
    stB = {dg: s for dg, (s, _) in wB.claims[eid].items()}
    contradiction = any(stA[dg] != stB[dg] for dg in stA)
    assert contradiction, "expected contradictory acceptance annotations"
    m1 = naive_annotation_merge(wA, wB)[eid]
    m2 = naive_annotation_merge(wB, wA)[eid]
    order_dependent = m1 != m2
    both = {dg: {stA[dg], stB[dg]} for dg in stA}
    keep_both_accepted = sum("accepted" in v for v in both.values())
    assert order_dependent and keep_both_accepted == 2
    print(f"B) acceptance annotations: log A {stA} vs log B {stB} -- "
          f"CONTRADICT. last-writer-wins merge is merge-order-DEPENDENT "
          f"(A+B != B+A: {order_dependent}); keep-both yields "
          f"{keep_both_accepted} 'accepted' digests for one event with no "
          f"log attribution.  [DOES NOT MERGE AS STORED]")

    # ---- C) the split: facts union + receipts-as-evidence union
    facts = observed_facts(wA) | observed_facts(wB)
    facts_rev = observed_facts(wB) | observed_facts(wA)
    receipts = admission_receipts(wA, "logA") | admission_receipts(wB, "logB")
    receipts_rev = (admission_receipts(wB, "logB") |
                    admission_receipts(wA, "logA"))
    assert facts == facts_rev and receipts == receipts_rev
    digests_for_eid = {dg for (e, dg) in facts if e == eid}
    derived = ("unknown" if not digests_for_eid else
               "unambiguous" if len(digests_for_eid) == 1 else "disputed")
    assert derived == "disputed"
    accept_map = {}
    for (log, e, dg, pol, eff) in receipts:
        if e == eid:
            accept_map.setdefault(dg, set()).add(log)
    settlement_disputed = len(accept_map) > 1
    assert settlement_disputed
    print(f"C) split form: ObservedClaimFact union = {len(facts)} facts, "
          f"order-independent; AdmissionReceipt union = {len(receipts)} "
          f"receipts, order-independent. Derived recognition after merge: "
          f"{derived}. Settlement view: "
          f"{ {dg[:8]: sorted(l) for dg, l in accept_map.items()} } -- the "
          f"acceptance divergence is now RECOGNIZABLE EVIDENCE, not a "
          f"silent contradiction.  [MERGES; boundary preserved]")

    print("\nseam measured: recognition merges as stored; acceptance does "
          "not; the ObservedClaimFact/AdmissionReceipt split merges both "
          "layers and keeps the divergence visible for Stage Three.")
