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
    raise ValueError("unknown payload kind %r" % (kind,))


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
    raise ValueError("unknown payload kind %r" % (payload[0],))


def mk_claim(writer_id, sequence, payload):
    """Build a canonical prehashed claim envelope."""
    return {"writer_id": int(writer_id), "sequence": int(sequence),
            "payload": payload, "digest": pdigest(payload)}


# ---------------------------------------------------------------- claim state
def init_claimstate():
    return {"facts": [], "receipts": {},
            "fact_capacity_fault": 0, "receipt_capacity_fault": 0}


def capacity_fault(state):
    """Derived combined convenience flag (presentation only)."""
    return int(bool(state.get("fact_capacity_fault", 0)
                    or state.get("receipt_capacity_fault", 0)))


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
    return ("Rejected", "unknown_kind")


def admit_step(state, batch, epoch, fx):
    """One ADMIT reduction. Returns (new_state, cfg_map, resets).

    cfg_map {spinner_role: rotor4} and resets {orb_role: bool} together are
    exactly the EpochControl the v0.6 world consumes (via
    compiler.enc_config_bundle). state is the persistent claim log threaded
    across epochs; batch is the ordered observation for THIS epoch. The
    result is order-independent, INCLUDING at the capacity boundary."""
    assert len(batch) <= MAX_BATCH, "batch exceeds MAX_BATCH=%d" % MAX_BATCH
    state = copy.deepcopy(state)
    facts = state["facts"]
    receipts = state["receipts"]

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
    if len(needed) > (MAX_EVENTS - len(receipts)):
        state["receipt_capacity_fault"] = 1
        return state, {}, {}
    newly = []
    for ek in needed:
        cands = _candidates(state, ek)
        acc_dig, acc_pk = cands[0]
        payload = next(f["payload"] for f in facts
                       if (f["writer_id"], f["sequence"]) == ek
                       and f["digest"] == acc_dig
                       and f["payload_key"] == acc_pk)
        outcome = _op_outcome(fx, payload)
        receipts[ek] = {"accepted_digest": acc_dig,
                        "accepted_payload_key": acc_pk,
                        "accepted_epoch": epoch, "outcome": outcome}
        newly.append((ek, acc_dig, acc_pk, payload, outcome))

    # ---- MAP: newly-accepted Applied ops -> EpochControl, applied in
    # canonical (sequence, writer_id, digest, payload_key) order; the later
    # canonical event's write of a rotor is the committed value.
    cfg_map = {}
    resets = {}
    order = sorted(newly, key=lambda t: (t[0][1], t[0][0], t[1], t[2]))
    for ek, _dig, _pk, payload, outcome in order:
        if outcome[0] != "Applied":
            continue
        if payload[0] == "SetRotor":
            _, sp, rot = payload
            cfg_map[sp] = tuple(rot)
        elif payload[0] == "ResetFault":
            _, ob = payload
            resets[ob] = True

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


def _payload_str(p, spinners=None, orbs=None):
    if p[0] == "SetRotor":
        _, sp, rot = p
        name = sp if (spinners is None or sp in spinners) else INVALID_TARGET
        return "SetRotor:%s:%s" % (name, ".".join(str(int(v)) for v in rot))
    ob = p[1]
    name = ob if (orbs is None or ob in orbs) else INVALID_TARGET
    return "ResetFault:%s" % (name,)


def _pk_str(pk):
    return ".".join(str(int(v)) for v in pk)


def _outcome_str(o):
    return o[0] if o[0] == "Applied" else "Rejected(%s)" % (o[1],)


def film_bytes_v7(t, pulsers, doors, relays, wires, spinners=None, orbs=None,
                  state=None):
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
                        _payload_str(f["payload"], sp_names, ob_names)))
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
    return ("\n".join(lines) + "\n").encode()


def film_hash_v7(*a, **k):
    return hashlib.sha256(film_bytes_v7(*a, **k)).hexdigest()
