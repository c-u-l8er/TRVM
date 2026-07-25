"""admit.py -- golden ADMIT claim-state reducer (slice 3b.5f-1, GPT-5.6
ruling 2 + the two golden repairs that precede the 3b.5f-2 IC lowering).

The GPT-5.6 ruling: ADMIT is a claim-state reducer that PRODUCES the
EpochControl the v0.6 world already consumes. The world effect (rotor /
pose / fault) is already proven; the new surface is purely:

    observed claim batch + persistent ClaimState  ->  EpochControl

RAW wrt ACCEPTANCE (the reducer receives UNACCEPTED claims and decides
recognition / acceptance / effect) but NOT raw wrt cryptographic parsing:
claims arrive as canonical typed PREHASHED envelopes; there is no
pure-term SHA-256 this slice.

TWO golden repairs GPT-5.6 required before lowering (both now permanent
regressions in the battery):

  Correction 1 -- reduced digest collisions are semantically visible.
    WD=8 collides (e.g. SetRotor("sp",(16,0,10,0)) and
    SetRotor("sp",(16,1,5,0)) share a digest). A digest-only identity would
    collapse two distinct payloads into one fact -> wrongly `unambiguous`,
    one payload silently lost, receipt cannot say which was accepted. FIX:
    a COMPLETE candidate key with an injective fixture-scoped payload key.
        CandidateKey  = (payload_digest, payload_key)
        ClaimFactKey  = (writer_id, sequence, payload_digest, payload_key)
    Same-batch acceptance selects the MINIMUM CandidateKey (digest-min stays
    primary; payload_key is the deterministic collision tie-break).
    Receipts store the complete accepted candidate; recognition counts
    distinct CANDIDATE KEYS (so a collision is still `disputed`).

  Correction 2 -- capacity exhaustion must be arrival-order independent.
    An insert-until-full loop retains different facts when the same
    overflowing batch is reversed. FIX: OBSERVE/ACCEPT are ATOMIC per epoch
    batch -- canonicalize+dedup the batch, drop already-present, sort by
    ClaimFactKey; if the new facts do not ALL fit, latch
    `fact_capacity_fault`, insert NONE, create no receipts/effects. The same
    atomic law governs receipts (`receipt_capacity_fault`). Never evict,
    never partially apply.

Acceptance policy `admit_candidate_min_firstreceipt_v1`: same-batch min
CandidateKey (order-independent); cross-batch with an existing receipt keeps
it (first receipt authoritative; a later conflicting claim flips recognition
to disputed but never undoes/retries); distinct events apply in
(sequence, writer_id, digest, payload_key) order; two accepted events writing
the same rotor the same epoch -> the later canonical event's write commits.

Phases OBSERVE -> ACCEPT -> MAP -> [COMMIT+REACT in the v0.6 world] ->
HASH/FILM. Container (approved for 3b.5f-2): occupied-prefix sorted vectors
for facts and receipts; recognition never stored.
"""
import copy
import hashlib

from film import film_bytes_v6

ACCEPTANCE_POLICY_ID = "admit_candidate_min_firstreceipt_v1"

WK = 4                       # writer_id / sequence reduced width (bits)
WD = 8                       # payload digest reduced width (bits)
MAX_FACTS = 6                # bounded canonical claim-set capacity
MAX_EVENTS = 6               # bounded receipt-log capacity
MAX_BATCH = 4                # bounded per-epoch observation batch

_HEX = (WD + 3) // 4


# ------------------------------------------------------------ payload / digest
def canon_payload(p):
    """Canonical typed serialization of a payload envelope (digest domain)."""
    kind = p[0]
    if kind == "SetRotor":
        _, sp, rot = p
        return "SetRotor|" + sp + "|" + ",".join(str(int(v)) for v in rot)
    if kind == "ResetFault":
        _, ob = p
        return "ResetFault|" + ob
    if kind == "Send":
        # IR v1.1 / Slice A, D9: tag 2. Both existing encodings are untouched,
        # so this is additive -- no pre-Slice-A payload changes digest.
        _, mb, body = p
        return "Send|" + mb + "|" + ",".join(str(int(v)) for v in body)
    raise ValueError("unknown payload kind %r" % (kind,))


def mailboxes_of(fx):
    """Mailbox declarations {mailbox_id: (width, capacity)}.

    A fixture WITHOUT the attribute has NO mailboxes. That is the safe
    default on purpose: before `MailboxDecl` exists every `Send` target is
    unknown and is therefore Rejected, never silently Applied."""
    return dict(getattr(fx, "mailboxes", None) or {})


def pdigest(p):
    """Reduced-width canonical payload digest (a prehashed envelope field).
    A pure function of the canonical payload string; the calculus never
    parses bytes -- the envelope arrives carrying this value."""
    h = hashlib.sha256(canon_payload(p).encode()).digest()
    return int.from_bytes(h, "big") & ((1 << WD) - 1)


def payload_key(fx, payload):
    """Injective FIXTURE-SCOPED payload key -- the collision-free tie-break
    (Correction 1). Not another truncated hash: a typed encoding of kind
    tag + target index + rotor lane bits, length-6 for both kinds.
        SetRotor:   (0, spinner_index, r0, r1, r2, r3)
        ResetFault: (1, orb_index,     0,  0,  0,  0)
        Send:       (2, mailbox_index, b0, b1, b2, b3)   ; IR v1.1 D9
    An out-of-fixture target packs to the canonical sentinel index
    `len(targets)`, which is what lets Film v0.7 render `INVALID_TARGET`
    without two otherwise-identical films falsely diverging.
    (The production bridge uses full canonical payload bytes after the full
    digest; this proof profile is collision-free by construction.)"""
    spins = sorted(fx.spinners)
    orbs = list(fx.orbs)
    if payload[0] == "SetRotor":
        _, sp, rot = payload
        si = spins.index(sp) if sp in spins else len(spins)
        return (0, si) + tuple(int(v) for v in rot)
    if payload[0] == "ResetFault":
        _, ob = payload
        oi = orbs.index(ob) if ob in orbs else len(orbs)
        return (1, oi, 0, 0, 0, 0)
    if payload[0] == "Send":
        _, mb, body = payload
        mbs = sorted(mailboxes_of(fx))
        mi = mbs.index(mb) if mb in mbs else len(mbs)
        return (2, mi) + tuple(int(v) for v in body)
    raise ValueError("unknown payload kind %r" % (payload[0],))


def mk_claim(writer_id, sequence, payload):
    """Build a canonical prehashed claim envelope."""
    return {"writer_id": int(writer_id), "sequence": int(sequence),
            "payload": payload, "digest": pdigest(payload)}


# ---------------------------------------------------------------- claim state
def init_claimstate(fx=None):
    """Persistent runtime state threaded across epochs.

    IR v1.1 / Slice A, D6: `mailbox_states` and `mailbox_capacity_fault` are
    NEW SIBLING FIELDS of `RuntimeStateV1_1`. Messages are NOT stored in
    `claim_facts` and receipts are NOT reused as message storage -- v1 §6
    reserves v2 for any change to the meaning of an existing field, and a
    second implementation must never silently reinterpret v1 fields. What is
    borrowed from ADMIT is identity, canonicalization, deduplication,
    capacity discipline and policy structure; NOT storage.

    The shape is SCHEMA-SENSITIVE, not unconditionally widened. A world that
    declares no mailbox gets EXACTLY `RuntimeStateV1` -- the two D6 sibling
    fields are absent, not merely empty -- so `RuntimeStateV1` still means in
    memory what the artifact says it means. Declaring a mailbox is what
    produces `RuntimeStateV1_1`, and it pre-declares each mailbox's state.

    `ledger_entries` stays in the base shape deliberately: D6 named exactly two
    new sibling fields, and the ledger predates the mailbox roles that write to
    it, so gating it would change `RuntimeStateV1` rather than preserve it."""
    st = {"facts": [], "receipts": {},
          "fact_capacity_fault": 0, "receipt_capacity_fault": 0,
          "ledger_entries": []}
    decls = mailboxes_of(fx) if fx is not None else {}
    if decls:
        st["mailbox_states"] = {mb: {"inbox": [], "next_inbox": []}
                                for mb in sorted(decls)}
        st["mailbox_capacity_fault"] = 0
    return st


def capacity_fault(state):
    """Derived combined convenience flag (presentation only). Unchanged for
    any world without a mailbox, since the new latch is then always 0."""
    return int(bool(state.get("fact_capacity_fault", 0)
                    or state.get("receipt_capacity_fault", 0)
                    or state.get("mailbox_capacity_fault", 0)))


def _fact_key(f):
    """ClaimFactKey = canonical set-identity (Correction 1)."""
    return (f["writer_id"], f["sequence"], f["digest"], f["payload_key"])


def _candidates(state, event_key):
    return sorted({(f["digest"], f["payload_key"]) for f in state["facts"]
                   if (f["writer_id"], f["sequence"]) == event_key})


def recognition(state, event_key):
    """DERIVED recognition by distinct CANDIDATE KEYS (Correction 1): a
    reduced-digest collision under one event key still reads `disputed`."""
    c = _candidates(state, event_key)
    if not c:
        return "unknown"
    return "unambiguous" if len(c) == 1 else "disputed"


def _op_outcome(fx, payload):
    """Applied unless the accepted op's target is invalid under the
    fixture. A Rejected receipt still persists (idempotent, no retry)."""
    kind = payload[0]
    if kind == "SetRotor":
        _, sp, rot = payload
        if sp not in fx.spinners:
            return ("Rejected", "unknown_spinner")
        if not fx.is_configurable(sp):
            return ("Rejected", "not_configurable")
        w_, _n, _rq = fx.spinners[sp]
        if not (isinstance(rot, tuple) and len(rot) == 4
                and all(isinstance(v, int) and 0 <= v < (1 << w_)
                        for v in rot)):
            return ("Rejected", "rotor_out_of_range")
        return ("Applied",)
    if kind == "ResetFault":
        _, ob = payload
        if ob not in fx.orbs:
            return ("Rejected", "unknown_orb")
        return ("Applied",)
    if kind == "Send":
        # SILENT-FAILURE GUARD 1 (Slice A §6). Without this branch the
        # `unknown_kind` fallback below would Reject EVERY send and no
        # delivery would ever occur -- a total behavioural failure that
        # never raises. The branch must exist BEFORE the mailbox policy.
        _, mb, body = payload
        mbs = mailboxes_of(fx)
        if mb not in mbs:
            return ("Rejected", "unknown_mailbox")
        w_, _cap = mbs[mb]
        if not (isinstance(body, tuple) and len(body) == 4
                and all(isinstance(v, int) and 0 <= v < (1 << w_)
                        for v in body)):
            return ("Rejected", "body_out_of_range")
        return ("Applied",)
    return ("Rejected", "unknown_kind")


# --------------------------------------------------------- D10 policy seams
# IR v1.1 / Mailbox Slice A, decision D10: the reducer is COMMON and exposes
# exactly two policy operations. Do NOT scatter policy conditionals through
# the reducer.
#
#     resolve_candidates(event_key, candidates)
#         -> ("Accepted", candidate) | ("Rejected", reason, evidence)
#
#     accumulate_map(accumulator, accepted_operation)
#         -> updated accumulator
#
# The COMMON reducer retains ownership of: grouping, exact-fact dedup,
# canonical ordering, fact capacity, receipt capacity, receipt creation,
# ledger emission, THE ACCUMULATOR SEED, and atomic commit behaviour.
# The POLICY chooses only: (1) how one event key resolves; (2) how accepted
# operations accumulate.
#
# RULING Q3 (GPT-5.6): `empty_accumulator` is NOT a policy operation and is
# NOT in the registry. The common reducer owns the FIXED accumulator seed
# `_empty_control_accumulator()` and seeds every fold with it. The registry
# therefore contains EXACTLY the two ruled operations, so "exactly two
# policy operations" is true by inspection rather than by argument. Both
# seam-2 implementations already returned the same uniform shape, so this
# closes a way for a future policy to redefine the seed -- which would have
# let policy leak into a structure the reducer must be able to reason about.
#
# SEAM 1 MUST BE PURE. Ruling Q4 resolves every event key BEFORE testing
# receipt capacity, so `resolve_candidates` is called on state that may yet
# be rolled back. It must not mutate state, emit ledger entries, or depend
# on call order.
#
# `candidates` is the canonically sorted list of distinct CandidateKeys
# (digest, payload_key) under one event key -- see `_candidates`.
# `accepted_operation` is the record below.

def _accepted_operation(event_key, digest, pkey, payload, outcome, epoch):
    return {"event_key": event_key, "digest": digest, "payload_key": pkey,
            "payload": payload, "outcome": outcome, "epoch": epoch}


def _resolve_candidates_min(event_key, candidates):
    """`admit_candidate_min_firstreceipt_v1` seam 1 -- CANONICAL MINIMUM.

    The accepted candidate is the minimum CandidateKey (digest-min primary,
    payload_key the deterministic collision tie-break, Correction 1). This
    policy NEVER rejects an event key for equivocation: an equivocal key
    still mints a receipt for its minimum candidate, and recognition
    separately reads `disputed`. Exactly the behaviour of the pre-Slice-A
    `acc_dig, acc_pk = cands[0]`."""
    return ("Accepted", candidates[0])


def _message(op):
    """A delivered message. Its identity is the ClaimFactKey it arrived
    under -- Slice A borrows ADMIT identity wholesale (§1) rather than
    inventing a message id."""
    ek = op["event_key"]
    _, mb, body = op["payload"]
    return {"writer_id": ek[0], "sequence": ek[1], "digest": op["digest"],
            "payload_key": op["payload_key"], "mailbox": mb,
            "body": tuple(int(v) for v in body)}


def _msg_key(m):
    """Canonical message order == the canonical MAP order. This is what buys
    WRL §12 scheduler invariance: worker arrival order is never semantic."""
    return (m["sequence"], m["writer_id"], m["digest"], m["payload_key"])


def _empty_control_accumulator():
    """THE accumulator seed: (cfg_map, resets, deliveries).

    RULING Q3: this is owned by the COMMON REDUCER, not by any policy, and
    is deliberately NOT registered in `POLICIES`. Every seam-2 operation
    folds over this one fixed shape, so `deliveries` is always a canonical
    list of messages and the reducer can always destructure the result."""
    return ({}, {}, [])


def _accumulate_keyed_collapse(accumulator, op):
    """`admit_candidate_min_firstreceipt_v1` seam 2 -- KEYED COLLAPSE.

    LOSSY BY DESIGN: assignment is keyed on the target, so when two accepted
    events write the same rotor in one epoch the later canonical event's
    write collapses the earlier one. Non-Applied outcomes contribute
    nothing. Exactly the behaviour of the pre-Slice-A `cfg_map[sp] = ...`.

    A `Send` collapses on the SAME rule -- keyed on the mailbox, one message
    per mailbox per epoch. That is what makes this policy the wrong one for
    a mailbox world, and it is DELIBERATELY not a silent drop: the message
    is still delivered, just collapsed exactly as a rotor write would be."""
    cfg_map, resets, deliveries = accumulator
    if op["outcome"][0] != "Applied":
        return accumulator
    payload = op["payload"]
    if payload[0] == "SetRotor":
        _, sp, rot = payload
        cfg_map[sp] = tuple(rot)
    elif payload[0] == "ResetFault":
        _, ob = payload
        resets[ob] = True
    elif payload[0] == "Send":
        msg = _message(op)
        deliveries = [m for m in deliveries if m["mailbox"] != msg["mailbox"]]
        deliveries.append(msg)
    return (cfg_map, resets, deliveries)


MAILBOX_POLICY_ID = "admit_mailbox_deliver_all_v1"


def _resolve_candidates_unique(event_key, candidates):
    """`admit_mailbox_deliver_all_v1` seam 1 -- REJECT IF NOT UNIQUE.

    Policy definition (§6): *deliver every accepted event key exactly once;
    never deliver more than one candidate for an event key.* "Deliver all"
    is across the set of SURVIVING event keys, never across candidates
    within one key.

    `cands[0]` cannot be reused here: silently choosing a winner from an
    equivocal send is exactly the failure this policy exists to prevent. An
    equivocal key yields no receipt, no delivery, and retains all of its
    distinct candidate facts -- the evidence of the dispute."""
    if len(candidates) != 1:
        return ("Rejected", "equivocal_send", tuple(candidates))
    return ("Accepted", candidates[0])


def _accumulate_ordered_append(accumulator, op):
    """`admit_mailbox_deliver_all_v1` seam 2 -- ORDERED APPEND.

    LOSSLESS: no accepted event key is collapsed. Two sends to the SAME
    mailbox under DIFFERENT event keys in one epoch both survive -- which is
    exactly what the default policy's keyed collapse would destroy.

    Control kinds keep their frozen v0.6 collapse semantics: a mailbox
    policy must not silently change rotor or fault behaviour."""
    cfg_map, resets, deliveries = accumulator
    if op["outcome"][0] != "Applied":
        return accumulator
    payload = op["payload"]
    if payload[0] == "Send":
        deliveries.append(_message(op))
        return (cfg_map, resets, deliveries)
    return _accumulate_keyed_collapse(accumulator, op)


# RULING Q3: EXACTLY the two ruled operations. A seam table with any other
# key is a policy reaching past D10 -- `get_policy` rejects it.
POLICY_OPERATIONS = ("resolve_candidates", "accumulate_map")

POLICIES = {
    ACCEPTANCE_POLICY_ID: {
        "resolve_candidates": _resolve_candidates_min,
        "accumulate_map": _accumulate_keyed_collapse,
    },
    MAILBOX_POLICY_ID: {
        "resolve_candidates": _resolve_candidates_unique,
        "accumulate_map": _accumulate_ordered_append,
    },
}


def _mailbox_states(state, fx):
    """Ensure every declared mailbox has runtime state. Undeclared mailboxes
    never materialize -- an unknown Send target is Rejected upstream.

    It must not materialize the D6 sibling FIELD either. A world that declares
    no mailbox is `RuntimeStateV1`, and merely stepping it must not quietly
    promote it to `RuntimeStateV1_1` by installing an empty `mailbox_states`;
    the schema a state satisfies is decided by the artifact, not by having been
    run."""
    decls = sorted(mailboxes_of(fx))
    if not decls and "mailbox_states" not in state:
        return {}
    mbs = state.setdefault("mailbox_states", {})
    for mb in decls:
        mbs.setdefault(mb, {"inbox": [], "next_inbox": []})
    return mbs


def _roll_mailboxes(state, fx, epoch):
    """COMMIT the previous epoch's sends -- D7's lifetime law:

        inbox' = admitted(next_inbox)      next_inbox' = []

    REPLACED, not appended. A message delivered in period k+1 is gone at the
    following commit whether or not anything observed it. This keeps the
    mailbox analogous to Relay (`cur_out' = next_out`) and keeps state
    bounded; persistence requires explicit promotion into another state
    form. Emits one MailboxDeliver per message actually becoming
    observable."""
    entries = []
    for mb in sorted(_mailbox_states(state, fx)):
        st = state["mailbox_states"][mb]
        pending = sorted(st.get("next_inbox", []), key=_msg_key)
        st["inbox"] = pending
        st["next_inbox"] = []
        for m in pending:
            entries.append(("MailboxDeliver", mb, epoch, m))
    return entries


def _commit_deliveries(state, fx, deliveries, epoch):
    """MAP's mailbox stage (D9 two-stage capacity):

        canonically order accepted deliveries
            -> test MAILBOX capacity
            -> append all or none

    A SEPARATE atomic capacity from `fact_capacity_fault`, over a DIFFERENT
    semantic set. Fact capacity bounds monotone evidence and therefore DOES
    count equivocating candidates; mailbox capacity bounds valid deliveries
    observable next period and therefore does NOT -- an equivocation never
    reaches this stage at all. Correction 2's law still governs: never
    evict, never partially apply."""
    entries = []
    if not deliveries:
        return entries
    mbs = _mailbox_states(state, fx)
    decls = mailboxes_of(fx)
    ordered = sorted(deliveries, key=_msg_key)
    want = {}
    for m in ordered:
        want.setdefault(m["mailbox"], []).append(m)
    # Atomic across the WHOLE epoch: if any one mailbox would overflow,
    # latch and deliver NOTHING anywhere.
    for mb, msgs in want.items():
        cap = decls[mb][1]
        if len(mbs[mb]["next_inbox"]) + len(msgs) > cap:
            state["mailbox_capacity_fault"] = 1
            return []
    for mb, msgs in want.items():
        mbs[mb]["next_inbox"] = sorted(mbs[mb]["next_inbox"] + msgs,
                                       key=_msg_key)
        for m in msgs:
            entries.append(("MailboxEnqueue", mb, epoch, m))
    return entries


def get_policy(policy_id=None):
    """Resolve an acceptance policy's seam table. None selects the frozen
    default so every pre-Slice-A caller is bit-for-bit unchanged."""
    pid = ACCEPTANCE_POLICY_ID if policy_id is None else policy_id
    try:
        policy = POLICIES[pid]
    except KeyError:
        raise ValueError("unknown acceptance policy %r" % (pid,))
    # RULING Q3: enforce the D10 arity here rather than trusting the table.
    if tuple(sorted(policy)) != tuple(sorted(POLICY_OPERATIONS)):
        raise ValueError("policy %r must define exactly %r" %
                         (pid, POLICY_OPERATIONS))
    return policy


def admit_step(state, batch, epoch, fx, policy_id=None):
    """One ADMIT reduction. Returns (new_state, cfg_map, resets).

    cfg_map {spinner_role: rotor4} and resets {orb_role: bool} together are
    exactly the EpochControl the v0.6 world consumes (via
    compiler.enc_config_bundle). state is the persistent claim log threaded
    across epochs; batch is the ordered observation for THIS epoch. The
    result is order-independent, INCLUDING at the capacity boundary.

    `policy_id` selects the D10 seam table. It defaults to
    ACCEPTANCE_POLICY_ID, so every pre-existing caller is unchanged."""
    assert len(batch) <= MAX_BATCH, "batch exceeds MAX_BATCH=%d" % MAX_BATCH
    policy = get_policy(policy_id)
    state = copy.deepcopy(state)
    facts = state["facts"]
    receipts = state["receipts"]

    # ---- COMMIT the PREVIOUS epoch's sends first (D7). This is the epoch
    # boundary, so it happens regardless of what this epoch's batch does --
    # including when a capacity latch below aborts the batch. `ledger` is
    # this epoch's EventLedger output (D11); it lives in `ledger_entries`
    # rather than in the return tuple so the frozen 3-tuple signature every
    # pre-Slice-A caller relies on is preserved.
    ledger = _roll_mailboxes(state, fx, epoch)
    state["ledger_entries"] = ledger

    # ---- OBSERVE (ATOMIC, Correction 2): canonicalize + dedup the batch,
    # drop already-present facts, sort by ClaimFactKey; if the new facts do
    # not ALL fit, latch fact_capacity_fault and insert NONE (no receipts /
    # effects from a rejected batch). Never evict, never partially apply.
    present = {_fact_key(f) for f in facts}
    seen = {}
    for c in batch:
        dg = int(c.get("digest", pdigest(c["payload"])))
        assert dg == pdigest(c["payload"]), "digest mismatch"
        f = {"writer_id": int(c["writer_id"]),
             "sequence": int(c["sequence"]),
             "digest": dg,
             "payload_key": payload_key(fx, c["payload"]),
             "payload": c["payload"]}
        seen[_fact_key(f)] = f
    new = sorted((f for k, f in seen.items() if k not in present),
                 key=_fact_key)
    if len(new) > (MAX_FACTS - len(facts)):
        state["fact_capacity_fault"] = 1
        return state, {}, {}
    facts.extend(new)
    facts.sort(key=_fact_key)

    # ---- ACCEPT (ATOMIC): every event key without a receipt needs one;
    # if they do not ALL fit, latch receipt_capacity_fault and create NONE
    # (facts stay -- monotone). accepted candidate = MIN (digest, payload_key)
    # among the event key's facts (first receipt authoritative across batches).
    keys_in_facts = sorted({(f["writer_id"], f["sequence"]) for f in facts})
    needed = [ek for ek in keys_in_facts if ek not in receipts]

    # ---- SEAM 1 (D10) runs FIRST, PURELY, over EVERY key needing a
    # receipt. RULING Q4: receipt capacity is tested AFTER resolution,
    # against the keys that actually MINT a receipt, so a rejected event key
    # no longer reserves a receipt that will never exist. The previous
    # conservative pre-check reserved one slot per key needing resolution,
    # which under `admit_mailbox_deliver_all_v1` made the reducer latch
    # receipt_capacity_fault for receipts an equivocal key never creates.
    #
    # Resolution stays PURE and capacity stays owned by the common reducer:
    # the policy still never sees a bound, it only says Accepted/Rejected.
    resolved = [(ek, _candidates(state, ek)) for ek in needed]
    resolved = [(ek, cands, policy["resolve_candidates"](ek, cands))
                for ek, cands in resolved]
    accepted = [r for r in resolved if r[2][0] == "Accepted"]
    if len(accepted) > (MAX_EVENTS - len(receipts)):
        # ATOMIC (Correction 2): the whole ACCEPT stage is abandoned -- no
        # receipts AND no MailboxReject entries, since emitting the rejects
        # from a stage that did not happen would be a partial application.
        # Facts stay (monotone), so every key re-resolves next epoch.
        state["receipt_capacity_fault"] = 1
        return state, {}, {}
    newly = []
    for ek, cands, verdict in resolved:
        if verdict[0] != "Accepted":
            # Equivocal event key -- frozen behaviour (§6):
            #   acceptance receipt : none
            #   delivery           : none
            #   MailboxReject      : exactly ONE canonical entry PER
            #                        UNRESOLVED KEY PER RESOLUTION EPOCH
            #   stored claim facts : all distinct candidates retained
            # The entry names the event key and the CANONICALLY ORDERED
            # candidate identities -- never one rejection per arrival, which
            # would make the film sensitive to transport multiplicity.
            #
            # "PER RESOLUTION EPOCH" is exact and is NOT a redundant re-emission
            # bug: a key with no receipt is still in `needed` next epoch, so it
            # is re-resolved and rejected again, emitting one entry each epoch
            # it remains unresolved. The ledger records an epoch's RESOLUTION
            # ATTEMPT, not a one-shot lifetime event -- so a dispute that is
            # never repaired stays visible in every subsequent film instead of
            # silently vanishing after its first epoch. Multiplicity within an
            # epoch is what is suppressed; recurrence across epochs is intended.
            ledger.append(("MailboxReject", ek, epoch, verdict[1],
                           tuple(sorted(cands))))
            continue
        acc_dig, acc_pk = verdict[1]
        payload = next(f["payload"] for f in facts
                       if (f["writer_id"], f["sequence"]) == ek
                       and f["digest"] == acc_dig
                       and f["payload_key"] == acc_pk)
        outcome = _op_outcome(fx, payload)
        receipts[ek] = {"accepted_digest": acc_dig,
                        "accepted_payload_key": acc_pk,
                        "accepted_epoch": epoch, "outcome": outcome}
        newly.append(_accepted_operation(ek, acc_dig, acc_pk, payload,
                                         outcome, epoch))

    # ---- MAP: newly-accepted ops accumulate in canonical
    # (sequence, writer_id, digest, payload_key) order. Canonical ORDER is
    # owned by the common reducer; how operations COMBINE is SEAM 2.
    acc = _empty_control_accumulator()   # RULING Q3: reducer-owned seed
    order = sorted(newly, key=lambda o: (o["event_key"][1], o["event_key"][0],
                                         o["digest"], o["payload_key"]))
    for op in order:
        # ---- SEAM 2 (D10): how accepted operations accumulate.
        acc = policy["accumulate_map"](acc, op)

    cfg_map, resets, deliveries = acc
    ledger.extend(_commit_deliveries(state, fx, deliveries, epoch))
    return state, cfg_map, resets


# ------------------------------------------------------------------ Film v0.7
# Film v0.7 renders a claim's TARGET NAME as non-authoritative diagnostic
# metadata: the authoritative identity of a claim is its ClaimFactKey
# (writer, sequence, digest, payload_key) -- the payload_key already packs an
# out-of-fixture target to a canonical sentinel index. So a rejected claim
# whose target does not exist in the fixture (e.g. SetRotor "zz") and a claim
# whose name has been lost in a lossy projection (rendered "?") MUST canonicalize
# to the SAME rendered target here; otherwise two films that are identical up to
# a non-authoritative name would falsely diverge. The sentinel is emitted
# whenever the target is not a live fixture object.
INVALID_TARGET = "#?"


def _payload_str(p, spinners=None, orbs=None, mailboxes=None):
    """SILENT-FAILURE GUARD 2 + 3 (Slice A §6).

    Guard 2: this function used to end in an UNGUARDED else that did
    `ob = p[1]` and rendered ANY non-SetRotor payload as a ResetFault. A
    `Send` would therefore have been projected into Film v0.7 as a
    ResetFault -- a film-correctness defect that never crashes. Every kind
    is now dispatched explicitly and an unrecognised kind RAISES rather
    than silently mis-rendering.

    Guard 3: `payload_key` is fixture-scoped and already packs an
    out-of-fixture target to a sentinel index, so the `INVALID_TARGET`
    discipline MUST extend to unknown mailbox ids -- otherwise two films
    that are identical up to a non-authoritative name would falsely
    diverge."""
    kind = p[0]
    if kind == "SetRotor":
        _, sp, rot = p
        name = sp if (spinners is None or sp in spinners) else INVALID_TARGET
        return "SetRotor:%s:%s" % (name, ".".join(str(int(v)) for v in rot))
    if kind == "ResetFault":
        _, ob = p
        name = ob if (orbs is None or ob in orbs) else INVALID_TARGET
        return "ResetFault:%s" % (name,)
    if kind == "Send":
        _, mb, body = p
        name = (mb if (mailboxes is None or mb in mailboxes)
                else INVALID_TARGET)
        return "Send:%s:%s" % (name, ".".join(str(int(v)) for v in body))
    raise ValueError("unknown payload kind %r in Film v0.7 projection"
                     % (kind,))


def _pk_str(pk):
    return ".".join(str(int(v)) for v in pk)


def _outcome_str(o):
    return o[0] if o[0] == "Applied" else "Rejected(%s)" % (o[1],)


def film_bytes_v7(t, pulsers, doors, relays, wires, spinners=None, orbs=None,
                  state=None, mailboxes=None):
    """FILM v0.7 (slice 3b.5f-1): the v0.6 physical film PLUS the claim /
    acceptance projection -- acceptance_policy_id, both capacity faults, the
    canonical claim fact set (ClaimFactKey order), the immutable acceptance
    receipts (with accepted candidate + outcome), and derived recognition
    (convenience; the fact set is authoritative). The mandatory Law-6 witness
    rides here: two worlds with identical physical state but a different
    receipt log for an event E already produce different v0.7 films BEFORE E
    is retransmitted, licensing the divergent future effect."""
    base = film_bytes_v6(t, pulsers, doors, relays, wires, spinners,
                         orbs).decode()
    lines = base.rstrip("\n").split("\n")
    lines[0] = "FILM v0.7"
    st = state or init_claimstate()
    # live fixture object names (role at tuple index 0); used to canonicalize
    # non-authoritative target names on claim lines (see _payload_str).
    sp_names = {r[0] for r in (spinners or [])}
    ob_names = {r[0] for r in (orbs or [])}
    # Guard 3: an undeclared mailbox is not a live fixture object, so it
    # canonicalizes to INVALID_TARGET exactly like an undeclared spinner.
    mb_names = {r[0] for r in (mailboxes or [])}
    lines.append("admit:policy=%s,fact_capacity_fault=%d,"
                 "receipt_capacity_fault=%d,capacity_fault=%d"
                 % (ACCEPTANCE_POLICY_ID,
                    int(st.get("fact_capacity_fault", 0)),
                    int(st.get("receipt_capacity_fault", 0)),
                    capacity_fault(st)))
    for f in sorted(st.get("facts", []), key=_fact_key):
        lines.append("claim:w=%d,s=%d,digest=%0*x,pkey=%s,payload=%s"
                     % (f["writer_id"], f["sequence"], _HEX, f["digest"],
                        _pk_str(f["payload_key"]),
                        _payload_str(f["payload"], sp_names, ob_names,
                                     mb_names)))
    for ek in sorted(st.get("receipts", {})):
        r = st["receipts"][ek]
        lines.append("receipt:w=%d,s=%d,accepted=%0*x,apkey=%s,epoch=%d,"
                     "outcome=%s"
                     % (ek[0], ek[1], _HEX, r["accepted_digest"],
                        _pk_str(r["accepted_payload_key"]),
                        r["accepted_epoch"], _outcome_str(r["outcome"])))
    ekeys = sorted({(f["writer_id"], f["sequence"])
                    for f in st.get("facts", [])})
    for ek in ekeys:
        lines.append("recognition:w=%d,s=%d,state=%s"
                     % (ek[0], ek[1], recognition(st, ek)))
    # ---- IR v1.1 / Slice A mailbox projection. GATED: emitted only when the
    # world actually declares a mailbox, so every pre-v1.1 film is
    # byte-identical. `inbox` is what is observable THIS period; `next_inbox`
    # is what commits at the next boundary -- the same cur/next idiom the
    # v0.6 film already uses for relays and doors.
    if mailboxes:
        lines.append("admit_mailbox:policy_capable=1,mailbox_capacity_fault=%d"
                     % int(st.get("mailbox_capacity_fault", 0)))
        mstates = st.get("mailbox_states", {})
        for rec in sorted(mailboxes):
            mb, w_, cap = rec[0], rec[1], rec[2]
            ms = mstates.get(mb, {"inbox": [], "next_inbox": []})
            lines.append("mailbox:%s:w=%d,capacity=%d,inbox=%s,next_inbox=%s"
                         % (mb, w_, cap,
                            _msgs_str(ms.get("inbox", [])),
                            _msgs_str(ms.get("next_inbox", []))))
        for e in st.get("ledger_entries", []):
            lines.append(_ledger_str(e))
    return ("\n".join(lines) + "\n").encode()


def _msg_str(m):
    return ("w%d.s%d.%0*x.%s->%s[%s]"
            % (m["writer_id"], m["sequence"], _HEX, m["digest"],
               _pk_str(m["payload_key"]), m["mailbox"],
               ".".join(str(int(v)) for v in m["body"])))


def _msgs_str(ms):
    return "(" + ";".join(_msg_str(m) for m in sorted(ms, key=_msg_key)) + ")"


def _ledger_str(e):
    """EventLedger rendering (D11). These are ledger_entries -- the
    claim-aware Film v0.7 family -- NOT world_frame, which is the physical
    Film v0.6 family."""
    kind = e[0]
    if kind == "MailboxReject":
        _, ek, epoch, reason, cands = e
        return ("ledger:MailboxReject,w=%d,s=%d,epoch=%d,reason=%s,"
                "candidates=%s"
                % (ek[0], ek[1], epoch, reason,
                   "(" + ";".join("%0*x.%s" % (_HEX, d, _pk_str(pk))
                                  for d, pk in cands) + ")"))
    _, mb, epoch, m = e
    return "ledger:%s,mailbox=%s,epoch=%d,msg=%s" % (kind, mb, epoch,
                                                     _msg_str(m))


def film_hash_v7(*a, **k):
    return hashlib.sha256(film_bytes_v7(*a, **k)).hexdigest()
