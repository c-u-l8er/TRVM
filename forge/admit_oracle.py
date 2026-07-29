"""admit_oracle.py -- deterministic before/after oracle for the ADMIT reducer.

Commit 0 of the IR v1.1 / Mailbox Slice A implementation ladder.

The battery scripts (binding_run3k / 3n / 3o) are a *strong* semantic gate but
a *weak* textual oracle: their stdout embeds wall-clock timings ("(35s)"), so
byte-comparing them across a refactor is not sound.

This module is the strict oracle the seam refactor is measured against. It is
a PURE fold over `admit.admit_step` (plus the Film v0.7 claim projection) with
zero timing, zero randomness and zero I/O beyond stdout. It exercises exactly
the semantic surface that the two Slice-A seams touch:

    SEAM 1  acceptance selection   (admit.py: `acc_dig, acc_pk = cands[0]`)
    SEAM 2  MAP accumulation       (admit.py: `cfg_map[sp] = tuple(rot)`)

...plus everything upstream and downstream of them, so that a refactor which
preserves the seams but perturbs OBSERVE, capacity latching, receipt
immutability or the film projection is still caught.

Acceptance criterion for Commit 1 (behaviour-preserving two-seam refactor):

    python3 admit_oracle.py --digest      # must print the SAME digest
    python3 admit_oracle.py > after.txt   # must be byte-identical to before

Run `--dump` for the full canonical transcript.
"""
import hashlib
import itertools
import sys

import admit as A
from fixture import Fixture


# --------------------------------------------------------------- the fixture
# Two spinners so SEAM 2 (keyed collapse vs append) is observable, and so a
# non-configurable spinner exercises the `not_configurable` rejection.
# Two orbs so ResetFault has both a live and a dead target.
def mkfx_oracle():
    return Fixture(
        {"p0": ("periodic", 2, 0)},
        [],                                    # relays
        ["d0"],                                # doors
        [("p0", "spa"), ("p0", "spb"), ("p0", "d0")],
        spinners={"spa": (4, 2, (4, 0, 0, 0)),
                  "spb": (4, 2, (4, 0, 0, 0))},
        orbs=["oa", "ob"],
        sockets=[("spa", "oa"), ("spb", "ob")],
        configurable={"spa"},                  # spb is FIXED on purpose
    )


FX = mkfx_oracle()

# Constant physical projection: the oracle isolates the CLAIM plane, so the
# v0.6 physical half of the film is held fixed. Any drift in the v0.7 claim
# lines is therefore attributable to the reducer, not to world physics.
_PHYS = dict(
    t=0,
    pulsers=[("p0", "periodic", 2, 0, 1, 0, 0)],
    doors=[("d0", 0, 0)],
    relays=[],
    wires=[],
    spinners=[("spa", "legacy", 4, 2, (4, 0, 0, 0), "oa", "configurable"),
              ("spb", "legacy", 4, 2, (4, 0, 0, 0), "ob", "fixed")],
    orbs=[("oa", "legacy", 4, 2, (4, 0, 0, 0), "spa", 0),
          ("ob", "legacy", 4, 2, (4, 0, 0, 0), "spb", 0)],
)


def C(w, s, payload):
    return A.mk_claim(w, s, payload)


def SR(sp, r0, r1=0, r2=0, r3=0):
    return ("SetRotor", sp, (r0, r1, r2, r3))


def RF(ob):
    return ("ResetFault", ob)


# ----------------------------------------------------------------- scenarios
# Each scenario is (name, [batch_per_epoch, ...]). Every scenario is folded
# from a fresh init_claimstate() so scenarios never contaminate one another.
SCENARIOS = [
    # -- 1. baseline: a single well-formed accepted SetRotor.
    ("accept_setrotor",
     [[C(1, 1, SR("spa", 1, 2, 3, 0))]]),

    # -- 2. baseline: a single well-formed accepted ResetFault.
    ("accept_resetfault",
     [[C(1, 1, RF("oa"))]]),

    # -- 3. retransmit: the identical claim replayed for 3 epochs. Facts must
    #    stay at 1, the receipt must keep epoch 0 (first receipt
    #    authoritative), and MAP must fire exactly ONCE.
    ("retransmit_idempotent",
     [[C(1, 1, SR("spa", 1, 0, 0, 0))],
      [C(1, 1, SR("spa", 1, 0, 0, 0))],
      [C(1, 1, SR("spa", 1, 0, 0, 0))]]),

    # -- 4. SEAM 1, same batch: two distinct payloads under ONE event key.
    #    recognition -> disputed; acceptance -> MIN CandidateKey.
    ("equivocation_same_batch",
     [[C(1, 1, SR("spa", 1, 0, 0, 0)), C(1, 1, SR("spa", 2, 0, 0, 0))]]),

    # -- 5. SEAM 1, same batch REVERSED. Must be identical to #4 (the
    #    acceptance rule is order-independent, not arrival-order-dependent).
    ("equivocation_same_batch_rev",
     [[C(1, 1, SR("spa", 2, 0, 0, 0)), C(1, 1, SR("spa", 1, 0, 0, 0))]]),

    # -- 6. SEAM 1, cross batch: the receipt is minted in epoch 0 and must
    #    SURVIVE the epoch-1 equivocation. recognition flips to disputed;
    #    the accepted candidate never changes; no second MAP effect.
    ("equivocation_cross_batch",
     [[C(1, 1, SR("spa", 2, 0, 0, 0))],
      [C(1, 1, SR("spa", 1, 0, 0, 0))]]),

    # -- 7. cross batch where the LATER claim is the smaller CandidateKey and
    #    the earlier receipt must still win (first-receipt authoritative).
    ("equivocation_cross_batch_min_later",
     [[C(2, 3, SR("spa", 9, 0, 0, 0))],
      [C(2, 3, SR("spa", 0, 0, 0, 0))]]),

    # -- 8. rejection: unknown spinner. Receipt persists as Rejected; the
    #    film must render the INVALID_TARGET sentinel, not "zz".
    ("reject_unknown_spinner",
     [[C(1, 1, SR("zz", 1, 0, 0, 0))]]),

    # -- 9. rejection: a FIXED spinner refuses a runtime rotor write.
    ("reject_not_configurable",
     [[C(1, 1, SR("spb", 1, 0, 0, 0))]]),

    # -- 10. rejection: rotor lane out of range (w=4 -> lanes < 16).
    ("reject_rotor_out_of_range",
     [[C(1, 1, SR("spa", 99, 0, 0, 0))]]),

    # -- 11. rejection: unknown orb; film renders the sentinel.
    ("reject_unknown_orb",
     [[C(1, 1, RF("zz"))]]),

    # -- 12. mixed batch: applied + rejected in one epoch. A rejection must
    #    not suppress the sibling's effect.
    ("mixed_applied_and_rejected",
     [[C(1, 1, SR("spa", 1, 0, 0, 0)), C(1, 2, SR("spb", 1, 0, 0, 0)),
       C(1, 3, RF("oa")), C(1, 4, RF("zz"))]]),

    # -- 13. SEAM 2: two accepted events write the SAME spinner in ONE epoch.
    #    The later canonical event's write is the committed value.
    ("map_same_rotor_collision",
     [[C(1, 1, SR("spa", 1, 0, 0, 0)), C(1, 2, SR("spa", 2, 0, 0, 0))]]),

    # -- 14. SEAM 2 reversed arrival. Must equal #13.
    ("map_same_rotor_collision_rev",
     [[C(1, 2, SR("spa", 2, 0, 0, 0)), C(1, 1, SR("spa", 1, 0, 0, 0))]]),

    # -- 15. SEAM 2: same spinner written by two DIFFERENT writers at the
    #    same sequence -- ordering falls through to writer_id.
    ("map_same_rotor_two_writers",
     [[C(2, 1, SR("spa", 5, 0, 0, 0)), C(1, 1, SR("spa", 6, 0, 0, 0))]]),

    # -- 16. SEAM 2: distinct spinners in one epoch -- both writes survive.
    ("map_distinct_spinners",
     [[C(1, 1, SR("spa", 1, 0, 0, 0)), C(1, 2, RF("oa")),
       C(1, 3, RF("ob"))]]),

    # -- 17. fact capacity: MAX_FACTS=6 reached exactly, then a batch that
    #    cannot ALL fit -> atomic latch, insert NONE, no effects.
    ("fact_capacity_atomic",
     [[C(1, 1, SR("spa", 1, 0, 0, 0)), C(1, 2, SR("spa", 2, 0, 0, 0)),
       C(1, 3, SR("spa", 3, 0, 0, 0)), C(1, 4, SR("spa", 4, 0, 0, 0))],
      [C(1, 5, SR("spa", 5, 0, 0, 0)), C(1, 6, SR("spa", 6, 0, 0, 0))],
      [C(1, 7, SR("spa", 7, 0, 0, 0))]]),

    # -- 18. fact capacity: an OVERFLOWING batch reversed. Correction 2 says
    #    the outcome must not depend on arrival order.
    ("fact_capacity_atomic_rev",
     [[C(1, 4, SR("spa", 4, 0, 0, 0)), C(1, 3, SR("spa", 3, 0, 0, 0)),
       C(1, 2, SR("spa", 2, 0, 0, 0)), C(1, 1, SR("spa", 1, 0, 0, 0))],
      [C(1, 6, SR("spa", 6, 0, 0, 0)), C(1, 5, SR("spa", 5, 0, 0, 0))],
      [C(1, 7, SR("spa", 7, 0, 0, 0))]]),

    # -- 19. the fact/receipt capacity boundary reached EXACTLY: 6 facts, 6
    #    receipts, both latches clear. NOTE: `receipt_capacity_fault` is
    #    structurally UNREACHABLE at MAX_FACTS == MAX_EVENTS == 6, because
    #    every event key requires at least one fact, so needed <= len(facts)
    #    <= MAX_FACTS == MAX_EVENTS. That branch is therefore exercised
    #    separately below under an explicit, restored MAX_EVENTS override.
    ("capacity_boundary_exact",
     [[C(1, 1, SR("spa", 1, 0, 0, 0)), C(1, 2, SR("spa", 2, 0, 0, 0)),
       C(1, 3, SR("spa", 3, 0, 0, 0)), C(1, 4, SR("spa", 4, 0, 0, 0))],
      [C(1, 5, SR("spa", 5, 0, 0, 0)), C(1, 6, SR("spa", 6, 0, 0, 0))]]),

    # -- 20. sequence-major ordering across writers over several epochs, with
    #    a retransmit interleaved.
    ("multi_writer_multi_epoch",
     [[C(1, 1, SR("spa", 1, 0, 0, 0)), C(2, 1, RF("oa"))],
      [C(2, 2, SR("spa", 3, 0, 0, 0))],
      [C(1, 1, SR("spa", 1, 0, 0, 0)), C(3, 1, RF("ob"))],
      []]),

    # -- 21. an empty batch must be a total no-op at every phase.
    ("empty_batch_noop",
     [[], [C(1, 1, SR("spa", 1, 0, 0, 0))], []]),

    # -- 22. Correction 1, THE load-bearing case: two payloads that genuinely
    #    COLLIDE under the reduced WD=8 digest (both hash to 0x94) under one
    #    event key. A digest-only identity would collapse them into one fact
    #    and read `unambiguous`, silently losing a payload; the complete
    #    CandidateKey must keep two facts and read `disputed`, with the
    #    payload_key acting as the deterministic tie-break for acceptance.
    ("digest_collision_disputed",
     [[C(1, 1, SR("spa", 0, 0, 14, 0)), C(1, 1, SR("spa", 0, 1, 3, 0))]]),

    # -- 23. the same collision pair arriving reversed: acceptance must pick
    #    the same candidate (payload_key tie-break is order-independent).
    ("digest_collision_disputed_rev",
     [[C(1, 1, SR("spa", 0, 1, 3, 0)), C(1, 1, SR("spa", 0, 0, 14, 0))]]),

    # -- 24. the collision pair split ACROSS epochs: the epoch-0 receipt is
    #    authoritative even though the epoch-1 claim shares its digest and
    #    carries the smaller payload_key.
    ("digest_collision_cross_batch",
     [[C(1, 1, SR("spa", 0, 1, 3, 0))],
      [C(1, 1, SR("spa", 0, 0, 14, 0))]]),
]


# -------------------------------------------------------------- canonicalize
def _fact_line(f):
    return ("  fact w=%d s=%d dg=%02x pk=%s payload=%s"
            % (f["writer_id"], f["sequence"], f["digest"],
               A._pk_str(f["payload_key"]), A.canon_payload(f["payload"])))


def _receipt_line(ek, r):
    return ("  receipt w=%d s=%d acc_dg=%02x acc_pk=%s epoch=%d outcome=%s"
            % (ek[0], ek[1], r["accepted_digest"],
               A._pk_str(r["accepted_payload_key"]), r["accepted_epoch"],
               A._outcome_str(r["outcome"])))


def state_lines(st):
    out = ["  faults fact=%d receipt=%d combined=%d"
           % (int(st.get("fact_capacity_fault", 0)),
              int(st.get("receipt_capacity_fault", 0)),
              A.capacity_fault(st))]
    for f in sorted(st.get("facts", []), key=A._fact_key):
        out.append(_fact_line(f))
    for ek in sorted(st.get("receipts", {})):
        out.append(_receipt_line(ek, st["receipts"][ek]))
    for ek in sorted({(f["writer_id"], f["sequence"])
                      for f in st.get("facts", [])}):
        out.append("  recognition w=%d s=%d -> %s"
                   % (ek[0], ek[1], A.recognition(st, ek)))
    # Slice A mailbox plane. GATED on a world that actually declares one, so
    # every pre-Slice-A transcript line -- and therefore BASELINE_DIGEST --
    # is bit-for-bit unchanged.
    if st.get("mailbox_states"):
        out.append("  mbfault %d" % int(st.get("mailbox_capacity_fault", 0)))
        for mb in sorted(st["mailbox_states"]):
            ms = st["mailbox_states"][mb]
            out.append("  mailbox %s inbox=%s next=%s"
                       % (mb, A._msgs_str(ms.get("inbox", [])),
                          A._msgs_str(ms.get("next_inbox", []))))
    for e in st.get("ledger_entries", []):
        out.append("  " + A._ledger_str(e))
    return out


def control_lines(cfg_map, resets):
    out = []
    for sp in sorted(cfg_map):
        out.append("  cfg %s <- %s"
                   % (sp, ".".join(str(int(v)) for v in cfg_map[sp])))
    for ob in sorted(resets):
        out.append("  reset %s <- %d" % (ob, int(bool(resets[ob]))))
    if not out:
        out.append("  (no controls)")
    return out


def film_lines(st, mailboxes=None):
    b = A.film_bytes_v7(state=st, mailboxes=mailboxes, **_PHYS)
    return ["  film|" + ln for ln in b.decode().rstrip("\n").split("\n")]


def fold(name, epochs, fx=None, policy=None):
    """Fold admit_step across a scenario. Returns canonical transcript lines.

    `fx`/`policy` default to the frozen pre-Slice-A pair, so the baseline
    transcript is produced by the identical code path it always was.

    This is an ORACLE, so a named `policy` goes through the conformance probe
    (Core 0.2.1 §8c). That is the correct classification and not a workaround:
    the oracle's job is to state what a policy TABLE does, independently of
    any world that might seal it -- it is handed a fixture and a policy, never
    an artifact, and it is precisely the second opinion a sealed fold is
    checked against."""
    fx = FX if fx is None else fx
    lines = ["== scenario %s" % name]
    st = A.init_claimstate(fx if fx is not FX else None)
    mbs = [(m, w, c) for m, (w, c) in sorted(A.mailboxes_of(fx).items())]
    for i, batch in enumerate(epochs):
        st, cfg_map, resets = (
            A.admit_step(st, batch, i, fx) if policy is None
            else A.admit_policy_probe(st, batch, i, fx, policy))
        lines.append("-- epoch %d  batch=%d" % (i, len(batch)))
        lines.extend(control_lines(cfg_map, resets))
        lines.extend(state_lines(st))
    lines.append("-- final film")
    lines.extend(film_lines(st, mailboxes=mbs or None))
    return lines


# ------------------------------------------- batch-permutation invariance law
# Correction 2 in executable form: for every scenario, permuting the arrival
# order WITHIN each epoch must not change the folded result. This is recorded
# in the transcript as a verdict so the oracle also fails loudly on a
# regression that only shows up under reordering.
_PERM_CAP = 24          # skip permuting epochs whose factorial explodes


def perm_verdict(name, epochs, fx=None, policy=None):
    if any(len(b) > 4 for b in epochs):
        return "SKIP(batch>4)"
    base = fold(name, epochs, fx, policy)
    checked = 0
    for combo in itertools.product(*[list(itertools.permutations(b))
                                     for b in epochs]):
        checked += 1
        if checked > _PERM_CAP:
            return "OK(capped@%d)" % _PERM_CAP
        if fold(name, [list(b) for b in combo], fx, policy) != base:
            return "VIOLATION"
    return "OK(%d)" % checked


# ---------------------------------------------- receipt-capacity reachability
# `receipt_capacity_fault` cannot be latched at MAX_FACTS == MAX_EVENTS,
# because every event key needs at least one fact:
#     needed <= len(facts) <= MAX_FACTS == MAX_EVENTS.
# The branch is real code the seam refactor could still break, so it is
# exercised here under an explicit override that is ALWAYS restored. This is
# the only place in the oracle that touches module state, and it is
# deliberately quarantined outside the scenario fold.
_RECEIPT_CAP_EPOCHS = [
    [C(1, 1, SR("spa", 1, 0, 0, 0)), C(1, 2, SR("spa", 2, 0, 0, 0))],
    [C(1, 3, SR("spa", 3, 0, 0, 0))],
]


def receipt_capacity_lines():
    lines = ["== receipt capacity latch (MAX_EVENTS override 2)",
             "  note: unreachable at MAX_FACTS==MAX_EVENTS==%d; "
             "needed <= len(facts) <= MAX_FACTS" % A.MAX_FACTS]
    saved = A.MAX_EVENTS
    try:
        A.MAX_EVENTS = 2
        st = A.init_claimstate()
        for i, batch in enumerate(_RECEIPT_CAP_EPOCHS):
            st, cfg_map, resets = A.admit_step(st, batch, i, FX)
            lines.append("-- epoch %d  batch=%d" % (i, len(batch)))
            lines.extend(control_lines(cfg_map, resets))
            lines.extend(state_lines(st))
    finally:
        A.MAX_EVENTS = saved
    assert A.MAX_EVENTS == saved, "MAX_EVENTS not restored"
    return lines


# ------------------------------------------------------- Slice A: tag-2 Send
# Commit 2 adds the `Send` payload kind and the three silent-failure guards.
# These scenarios are held in a SEPARATE section so the frozen Commit 0/1
# baseline digest stays verifiable forever via `--baseline`.
#
# NOTE: at Commit 2 no fixture declares mailboxes yet (`MailboxDecl` is
# Commit 3), so `mailboxes_of(fx)` is empty and EVERY send is correctly
# Rejected `unknown_mailbox` rather than silently Applied. That is the
# guard working, not a defect.
def SEND(mb, b0, b1=0, b2=0, b3=0):
    return ("Send", mb, (b0, b1, b2, b3))


SEND_SCENARIOS = [
    # -- guard 1: a Send must NOT fall through to ("Rejected","unknown_kind").
    #    With no mailbox declared the correct verdict is `unknown_mailbox`.
    ("send_unknown_mailbox",
     [[C(1, 1, SEND("mb0", 1, 2, 3, 4))]]),

    # -- tag 2 is additive: a Send coexists with both legacy kinds in one
    #    batch and perturbs neither of their effects.
    ("send_coexists_with_legacy",
     [[C(1, 1, SR("spa", 1, 0, 0, 0)), C(1, 2, RF("oa")),
       C(1, 3, SEND("mb0", 7, 0, 0, 0))]]),

    # -- payload_key tag 2 keeps distinct sends distinct, and a same-key
    #    equivocation over two sends still reads `disputed`.
    ("send_equivocation_disputed",
     [[C(1, 1, SEND("mb0", 1, 0, 0, 0)), C(1, 1, SEND("mb0", 2, 0, 0, 0))]]),

    # -- ordering: sends interleave with legacy kinds under the SAME
    #    canonical (sequence, writer_id, digest, payload_key) rule.
    ("send_canonical_ordering",
     [[C(2, 1, SEND("mb0", 3, 0, 0, 0)), C(1, 1, SEND("mb0", 4, 0, 0, 0)),
       C(1, 2, SR("spa", 5, 0, 0, 0))]]),
]


def guard_lines():
    """Direct unit witnesses for the three silent-failure guards. Each of
    these can fail WITHOUT crashing the reducer, so each is pinned here."""
    out = ["== silent-failure guards (Slice A section 6)"]

    # Guard 1 -- `_op_outcome` must have a Send branch.
    p = SEND("mb0", 1, 0, 0, 0)
    o = A._op_outcome(FX, p)
    out.append("  guard1 _op_outcome(Send) -> %s" % (A._outcome_str(o),))
    out.append("  guard1 is_unknown_kind_fallback=%s"
               % (o == ("Rejected", "unknown_kind")))

    # Guard 2 -- `_payload_str` must not render a Send as a ResetFault, and
    # must RAISE on a genuinely unrecognised kind.
    out.append("  guard2 _payload_str(Send, live) -> %s"
               % A._payload_str(p, {"spa", "spb"}, {"oa", "ob"}, {"mb0"}))
    try:
        A._payload_str(("Bogus", "x"), set(), set(), set())
        out.append("  guard2 unknown_kind_raises=False")
    except ValueError:
        out.append("  guard2 unknown_kind_raises=True")

    # Guard 3 -- INVALID_TARGET sentinel discipline extends to mailbox ids,
    # and the fixture-scoped payload_key packs an unknown id to the sentinel
    # index so the two renderings cannot falsely diverge.
    out.append("  guard3 _payload_str(Send, undeclared) -> %s"
               % A._payload_str(p, {"spa", "spb"}, {"oa", "ob"}, set()))
    out.append("  guard3 payload_key(Send, undeclared) -> %s"
               % A._pk_str(A.payload_key(FX, p)))
    out.append("  guard3 sentinel_index=%d n_mailboxes=%d"
               % (A.payload_key(FX, p)[1], len(A.mailboxes_of(FX))))

    # Tag additivity -- the two legacy tags are untouched by tag 2.
    out.append("  tags SetRotor=%d ResetFault=%d Send=%d"
               % (A.payload_key(FX, SR("spa", 0, 0, 0, 0))[0],
                  A.payload_key(FX, RF("oa"))[0],
                  A.payload_key(FX, p)[0]))
    return out


# ------------------------------------------ Slice A: declared mailbox worlds
# Commits 3-5 add `MailboxDecl`, the second acceptance policy, and the
# commit/ledger behaviour. This section folds the SAME oracle machinery over a
# fixture that DECLARES mailboxes, under `admit_mailbox_deliver_all_v1`. It is
# strictly additive: `--baseline` still stops before it.
FX_MB = Fixture(
    {"p0": ("periodic", 2, 0)},
    [],
    ["d0"],
    [("p0", "spa"), ("p0", "spb"), ("p0", "d0")],
    spinners={"spa": (4, 2, (4, 0, 0, 0)),
              "spb": (4, 2, (4, 0, 0, 0))},
    orbs=["oa", "ob"],
    sockets=[("spa", "oa"), ("spb", "ob")],
    configurable={"spa"},
    mailboxes={"mb0": (4, 2), "mb1": (4, 1)},
)

MAILBOX_SCENARIOS = [
    # -- D7 lifetime law: enqueued at k, observable at k+1, GONE at k+2.
    #    Three epochs so the disappearance is in the transcript, not implied.
    ("mb_lifetime_replace_not_append",
     [[C(1, 1, SEND("mb0", 7, 0, 0, 0))], [], []]),

    # -- two writers, one mailbox: BOTH survive under the deliver-all policy.
    #    This is the whole point of the second seam -- the frozen keyed-collapse
    #    policy would have kept only one.
    ("mb_deliver_all_two_writers",
     [[C(1, 1, SEND("mb0", 1, 0, 0, 0)), C(2, 1, SEND("mb0", 2, 0, 0, 0))],
      []]),

    # -- D9 stage 2: mb1 has capacity 1, so two sends to it overflow. Atomic
    #    across the WHOLE epoch -- the co-batched mb0 send is not delivered
    #    either, and `fact_capacity_fault` stays clear (a DIFFERENT set).
    ("mb_capacity_atomic_latch",
     [[C(1, 1, SEND("mb1", 1, 0, 0, 0)), C(2, 1, SEND("mb1", 2, 0, 0, 0)),
       C(3, 1, SEND("mb0", 3, 0, 0, 0))], []]),

    # -- equivocal event key under the mailbox policy: exactly ONE canonical
    #    MailboxReject, no receipt, no delivery, both facts retained.
    ("mb_equivocal_send_rejected",
     [[C(1, 1, SEND("mb0", 1, 0, 0, 0)), C(1, 1, SEND("mb0", 2, 0, 0, 0))],
      []]),

    # -- an undeclared target is still Rejected `unknown_mailbox` even in a
    #    world that HAS mailboxes, and reaches no mailbox state.
    ("mb_unknown_target_in_mailbox_world",
     [[C(1, 1, SEND("nope", 1, 0, 0, 0)), C(2, 1, SEND("mb0", 4, 0, 0, 0))],
      []]),

    # -- body domain: mb0 has width 4, so 16 is out of range. The receipt is
    #    Rejected and persists; nothing is enqueued.
    ("mb_body_out_of_range",
     [[C(1, 1, SEND("mb0", 16, 0, 0, 0))], []]),

    # -- tag 2 remains additive in a mailbox world: controls still commit while
    #    a send rides the same batch.
    ("mb_coexists_with_controls",
     [[C(1, 1, SR("spa", 5, 0, 0, 0)), C(1, 2, RF("oa")),
       C(1, 3, SEND("mb0", 6, 0, 0, 0))], []]),

    # -- capacity BOUNDARY: exactly `capacity` sends fit and all are delivered;
    #    the latch stays clear. The complement of mb_capacity_atomic_latch.
    ("mb_capacity_boundary_exact",
     [[C(1, 1, SEND("mb0", 1, 0, 0, 0)), C(2, 1, SEND("mb0", 2, 0, 0, 0))],
      []]),
]


def mailbox_lines():
    out = ["== declared-mailbox worlds (Slice A, policy %s)"
           % A.MAILBOX_POLICY_ID,
           "  mailboxes %s" % sorted(A.mailboxes_of(FX_MB).items())]
    for name, epochs in MAILBOX_SCENARIOS:
        out.append("")
        out.extend(fold(name, epochs, FX_MB, A.MAILBOX_POLICY_ID))
    out.append("")
    out.append("== permutation invariance (mailbox scenarios)")
    for name, epochs in MAILBOX_SCENARIOS:
        out.append("  perm %-34s %s"
                   % (name, perm_verdict(name, epochs, FX_MB,
                                         A.MAILBOX_POLICY_ID)))
    return out


def transcript(baseline_only=False):
    lines = ["ADMIT ORACLE v1 -- Commit 0 baseline (pre-Slice-A)",
             "policy=%s" % A.ACCEPTANCE_POLICY_ID,
             "WK=%d WD=%d MAX_FACTS=%d MAX_EVENTS=%d MAX_BATCH=%d"
             % (A.WK, A.WD, A.MAX_FACTS, A.MAX_EVENTS, A.MAX_BATCH),
             "fixture spinners=%s orbs=%s configurable=%s"
             % (sorted(FX.spinners), sorted(FX.orbs),
                sorted(FX.configurable)),
             ""]
    for name, epochs in SCENARIOS:
        lines.extend(fold(name, epochs))
        lines.append("")
    lines.extend(receipt_capacity_lines())
    lines.append("")
    lines.append("== permutation invariance (Correction 2)")
    for name, epochs in SCENARIOS:
        lines.append("  perm %-34s %s" % (name, perm_verdict(name, epochs)))
    lines.append("")
    if baseline_only:
        # The frozen pre-Send transcript. Its digest is the Commit 0/1
        # acceptance criterion and must NEVER move again.
        return "\n".join(lines) + "\n"
    lines.extend(guard_lines())
    lines.append("")
    for name, epochs in SEND_SCENARIOS:
        lines.extend(fold(name, epochs))
        lines.append("")
    lines.append("== permutation invariance (Send scenarios)")
    for name, epochs in SEND_SCENARIOS:
        lines.append("  perm %-34s %s" % (name, perm_verdict(name, epochs)))
    lines.append("")
    lines.extend(mailbox_lines())
    lines.append("")
    return "\n".join(lines) + "\n"


BASELINE_DIGEST = ("2d6d50a0920f068a4de44860e16cc64f"
                   "eb3d28bbf8288ceeb51a4b3793d66f35")

# The Slice A golden: baseline + guards + Send scenarios + declared-mailbox
# worlds. UNLIKE BASELINE_DIGEST this one is EXPECTED to move when Slice A
# semantics are deliberately extended (Slice B will move it). It exists so an
# ACCIDENTAL move is loud. Update it only alongside a reviewed behaviour change.
SLICE_A_DIGEST = ("5dbaeddcbed28c79f65d008b3a5f93dc"
                  "0caffdfa37efffde51c2fb117d84ef77")


def digest(baseline_only=False):
    return hashlib.sha256(transcript(baseline_only).encode()).hexdigest()


def main(argv):
    baseline_only = "--baseline" in argv
    text = transcript(baseline_only)
    if "VIOLATION" in text:
        sys.stdout.write(text)
        print("ORACLE FAIL: permutation invariance violated")
        return 1
    base = digest(True)
    if base != BASELINE_DIGEST:
        sys.stdout.write(text)
        print("ORACLE FAIL: pre-Send baseline moved\n  expected %s\n  got      %s"
              % (BASELINE_DIGEST, base))
        return 1
    full = digest(False)
    drift = full != SLICE_A_DIGEST
    if "--digest" in argv:
        print(digest(baseline_only))
        return 1 if (drift and not baseline_only) else 0
    sys.stdout.write(text)
    print("baseline_digest=%s (FROZEN, matches)" % base)
    print("oracle_digest=%s%s"
          % (full, "" if not drift else
             "\nORACLE WARN: Slice A golden moved\n  expected %s\n  got      %s"
             "\n  update SLICE_A_DIGEST only with a reviewed behaviour change"
             % (SLICE_A_DIGEST, full)))
    return 1 if drift else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
