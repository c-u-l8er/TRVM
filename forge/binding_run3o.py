"""binding_run3o.py -- 3b.5f-2b BUILD (persistent claim/world fold): the
single-epoch ADMIT reducer (ic_reduce, 3b.5f-2a) is folded over K epochs into
ONE interaction-calculus term that threads BOTH the persistent ClaimState
(fact vector + receipt vector) AND the WorldState (v0.6 encoded physical state)
across epochs, and is gated by a SINGLE native normalization producing the
WHOLE trajectory (one native() call yields every epoch's world + claim state).

This is the deliverable GPT-5.6's Ruling 3 named for 3b.5f-2b:
  ClaimState + WorldState + batches[0:K]  ->  ClaimState_K + WorldState_K
                                              + Films[0:K]  (single trajectory)

Composition (per epoch e, threading fv_e / rv_e / world_e):
  red_e     = ic_reduce(fv_e, rv_e, batch_srcs[e])      # TUP5(fv',rv',EC,fo,fa)
  world_e+1 = ((compile_step_v6 EC) world_e)            # v0.6 physical step
  the reducer's emitted EpochControl is fed DIRECTLY into compile_step_v6
  (3b.5f-2b MEASURE proved this equals the golden enc_config_bundle EC).
Each epoch emits (world_e+1, fv_e+1, rv_e+1, fobs, facc); the K epochs are a
flat TUP(5*K) collected in ONE term, normalized ONCE (ref) and ONCE (native).

Linearity note: ic_reduce reads its receipt input in BOTH accept and map, so it
now binds rv_in_src once and !&-dups it -- the reducer is linear in rv and thus
composable when rv is a bound variable from the previous epoch's output.

Receipt accepted_epoch is NOT carried in the IC receipt vector (a receipt is
identified by its CandidateKey; epoch is provenance). The projection recovers it
faithfully as the epoch at which each receipt FIRST appears in the trajectory --
which is exactly the epoch admit_step accepted it -- so Film v0.7 parity holds
across the whole multi-epoch trajectory, epochs included.

  O1 three-epoch persistence: rotor -> rotor+reset -> invalid-noop; claim facts
     accumulate, receipts are first-authoritative, the physical world evolves    (native)
  O2 two-epoch canonical: two rotors in epoch 1 (later-canonical commits) then a
     reset in epoch 2                                                             (native)
  O3 arrival-order independence: O2 with epoch-1 batch reversed -> IDENTICAL
     trajectory -- PERMANENT REGRESSION (Ruling 3 required class)                 (native)
  O4 first-receipt authoritative across epochs: (1,1) receipted in epoch 1 is NOT
     remapped by a re-claim in epoch 2; a fresh (2,2) still applies               (native)
  O5 Film v0.7 trajectory parity: every epoch's fold projection renders the
     IDENTICAL v0.7 film (physical + claim + receipt-with-epoch) as the golden
     admit_step + world-step trajectory                                          (native)
"""
import os, sys, time, copy
sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import binlib as BL
import admit as AD
import admit_ic as X
import compiler as C
from admit import mk_claim, film_bytes_v7
from binding_run3j import mkfx, norm, native
from fixture import init_state_v6, state_to_film_args_v6
from lower_e2a import _v, _spine, T as _T
from compiler import Alloc, TUPN

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"
FX = mkfx(8, 4)
CAP = AD.MAX_FACTS          # 6
RCAP = AD.MAX_EVENTS        # 6
CK = X.CKEY_W              # 44
WK = AD.WK                 # 4
S = lambda rot: ("SetRotor", "sp", rot)
Rf = ("ResetFault", "ob")


# ------------------------------------------------------------- fkey helpers
def _mkfkey(w, s, ck):
    return (w << (WK + CK)) | (s << CK) | ck


def _ckor(dg, pk):
    return X._cat([(dg, X.WD), (pk[0], X.WKIND), (pk[1], X.WIDX),
                   (pk[2], X.WLANE), (pk[3], X.WLANE),
                   (pk[4], X.WLANE), (pk[5], X.WLANE)])


# --------------------------------------------------------------------------
# WHY THE HELPERS BELOW TAKE `fx=None`
#
# This battery was written for ONE world (`FX = mkfx(8, 4)`), so eight helpers
# closed over the module global. That was correct while this file was the only
# caller. It stopped being correct when `binding_run47._fold` began passing a
# CALLER'S fixture: the IC half honoured it and the golden half silently used
# `FX`, so the two were only ever compared because `mkfx(8, 4)` happens to be
# structurally the demo world. A driver that ignores its own argument and
# passes anyway is a green row that proves nothing, and it would have started
# LYING the moment Slice B folded a mailbox-bearing world.
#
# The fix is a defaulted parameter, not a second copy of the driver in the new
# battery. `fx=None` resolves to `FX`, so every existing call site is
# byte-identical and the frozen rows below re-run unchanged; a caller with its
# own world now gets its own world through BOTH halves.
# --------------------------------------------------------------------------
# The same argument applies a second time, to the PROFILE. These helpers packed
# keys at the module's one profile width; commit 5a gave the tree two, so a
# `prof=None` parameter defaults to `admit.ic.v1.core52` and every frozen call
# site below is byte-identical, while a caller folding a route-bearing world
# gets ITS profile through both halves. Copying the drivers into the new
# battery instead would reproduce exactly the defect this note already records.
def _fact_fkeys(st, fx=None, prof=None):
    fx = FX if fx is None else fx
    prof = X.PROFILE_V1 if prof is None else prof
    return sorted(X.pack_fkey(fx, f["writer_id"], f["sequence"], f["payload"],
                              prof)
                  for f in st["facts"])


def _rcpt_fkeys(st):
    return sorted(_mkfkey(ek[0], ek[1],
                  _ckor(r["accepted_digest"], r["accepted_payload_key"]))
                  for ek, r in st["receipts"].items())


def _unpack_fkey(fk, prof=None):
    """fkey -> (writer, seq, digest, payload_key=(kind,idx,r0,r1,r2,r3)).

    This used to re-spell the field widths and the MSB-first unpack loop.
    `admit_ic.unpack_fkey` is now the inverse of `pack_fkey` and lives beside
    it, so this is a SHAPE adapter over that one definition and nothing more --
    a second copy of the layout would be a fork that only shows up once the two
    profiles disagree, which is the one moment it would matter."""
    v = X.unpack_fkey(fk, X.PROFILE_V1 if prof is None else prof)
    pk = (v["kind"], v["idx"], v["r0"], v["r1"], v["r2"], v["r3"])
    return v["writer"], v["sequence"], v["digest"], pk


def _payload_of(pk, fx=None):
    fx = FX if fx is None else fx
    spins = sorted(fx.spinners)
    orbs = list(fx.orbs)
    kind, idx = pk[0], pk[1]
    if kind == AD.KIND_SETROTOR:
        sp = spins[idx] if idx < len(spins) else "?"
        return ("SetRotor", sp, (pk[2], pk[3], pk[4], pk[5]))
    if kind == AD.KIND_SEND:
        mbs = sorted(AD.mailboxes_of(fx))
        mb = mbs[idx] if idx < len(mbs) else "?"
        return ("Send", mb, (pk[2], pk[3], pk[4], pk[5]))
    ob = orbs[idx] if idx < len(orbs) else "?"
    return ("ResetFault", ob)


def _batch_srcs(batch, fx=None, prof=None):
    fx = FX if fx is None else fx
    prof = X.PROFILE_V1 if prof is None else prof
    keys = sorted(X.pack_fkey(fx, int(c["writer_id"]), int(c["sequence"]),
                              c["payload"], prof)
                  for c in batch)
    return [BL.enc_operand(k, prof.FKEY_W) for k in keys]


# ------------------------------------------------------ golden trajectory
def _golden_traj(claim0, world0, batches, epoch0=1, fx=None):
    """admit_step + world-step epoch-by-epoch. Returns per-epoch tuples of
    (world, claim_state, fact_fkeys, rcpt_fkeys, fobs, facc)."""
    fx = FX if fx is None else fx
    claim = copy.deepcopy(claim0)
    world = copy.deepcopy(world0)
    out = []
    for e, batch in enumerate(batches):
        claim, cfg_map, resets = AD.admit_step(claim, batch, epoch0 + e, fx)
        ec = C.enc_config_bundle(fx, cfg_map, resets)
        step, _ = C.compile_step_v6(fx)
        world = C.dec_state_v6(fx, norm(f"(({step} {ec}) {C.enc_state_v6(fx, world)})"))
        out.append((copy.deepcopy(world), copy.deepcopy(claim),
                    _fact_fkeys(claim, fx), _rcpt_fkeys(claim),
                    int(claim.get("fact_capacity_fault", 0)),
                    int(claim.get("receipt_capacity_fault", 0))))
    return out


# ---------------------------------- the fold: ONE term over K epochs -------
# --------------------------------------------------------------------------
# ... AND THE SAME ARGUMENT A THIRD TIME, for the MAILBOX (Slice B, commit 5b).
#
# `mcap=0` is "this world declares no mailbox", which is every caller that
# existed before this line, so their terms and their decoded rows are
# byte-identical. A caller with a mailbox gets THREE extra things and no
# fourth: the reducer emits a sixth field, the fold threads the
# `mailbox_capacity_fault` LATCH across epochs (golden keeps it in claim state,
# so a per-epoch flag recomputed in the decoder would be a projection and not a
# reduction), and each epoch's row carries its own `next_inbox`.
#
# The INBOX is deliberately NOT threaded. Golden's `_roll_mailboxes` empties
# `next_inbox` at the top of EVERY `admit_step`, so `_commit_deliveries` always
# appends into an empty box: the reducer needs no mailbox INPUT at all, and
# epoch e's inbox is exactly epoch e-1's emitted bundle. That shift belongs to
# the projection, which is where D7's lifetime law -- REPLACED, not appended --
# is a one-line consequence rather than a second copy of the rule.
# --------------------------------------------------------------------------
def _build_fold(batches, fv0_src, rv0_src, w0_src, fx=None, prof=None, mcap=0,
                rule=None):
    K = len(batches)
    fx = FX if fx is None else fx
    prof = X.PROFILE_V1 if prof is None else prof
    # `rule` is the sealed world's ACCEPT rule (Slice B commit 5c). None is the
    # frozen `ACCEPT_MIN`, so every caller written before 5c builds a
    # byte-identical term. A fold does not CHOOSE it -- `admit_ic.
    # accept_rule_for_artifact` reads it off the seal and the caller passes it
    # through, the same way `prof` arrives from `profile_for_artifact`.
    rule = X.ACCEPT_MIN if rule is None else rule
    has_mb = bool(mcap) and AD.KIND_SEND in prof.KINDS

    def rec(e, fv_v, rv_v, w_v, mb_v, outacc):
        red = X.ic_reduce(fv_v, rv_v, _batch_srcs(batches[e], fx, prof),
                          CAP, RCAP, prof, mcap, rule)
        step, _ = C.compile_step_v6(fx)
        fvp, rvp, ec, fo, fa, wnew = (_v("fvp"), _v("rvp"), _v("ec"),
                                      _v("fo"), _v("fa"), _v("w"))
        stepapp = f"(({step} {ec}) {w_v})"
        # The mailbox bundle is destructured AROUND the frozen body: the slots
        # go straight to this epoch's row, and the epoch's overflow bit is
        # OR'd into the carried latch before anything else runs.
        mb_head, mb_tail, mb_out, mb_fwd = "", "", [], None
        if has_mb:
            mbb, ov, mbn = _v("mbb"), _v("ov"), _v("mbn")
            qs = [_v("q") for _ in range(mcap)]
            Am = Alloc()
            latch = [mbn] if e == K - 1 else Am.copies(mbn, 2)
            mb_fwd = None if e == K - 1 else latch[1]
            mb_out = qs + [latch[0]]
            mb_head = (f"λ{mbb}.({mbb} λ" + ".λ".join(qs + [ov])
                       + f".(λ{mbn}.{''.join(Am.prefix)}")
            mb_tail = f" (({ov} {_T}) {mb_v})))"
        if e == K - 1:
            tup = TUPN(outacc + [wnew, fvp, rvp, fo, fa] + mb_out)
            body = f"(λ{wnew}.{tup} {stepapp})"
        else:
            Aw = Alloc(); w_out, w_fwd = Aw.copies(wnew, 2)
            Af = Alloc(); fv_out, fv_fwd = Af.copies(fvp, 2)
            Ar = Alloc(); rv_out, rv_fwd = Ar.copies(rvp, 2)
            inner = rec(e + 1, fv_fwd, rv_fwd, w_fwd, mb_fwd,
                        outacc + [w_out, fv_out, rv_out, fo, fa] + mb_out)
            body = ("".join(Af.prefix) + "".join(Ar.prefix)
                    + f"(λ{wnew}.{''.join(Aw.prefix)}{inner} {stepapp})")
        return (f"({red} λ{fvp}.λ{rvp}.λ{ec}.λ{fo}.λ{fa}."
                f"{mb_head}{body}{mb_tail})")

    return rec(0, fv0_src, rv0_src, w0_src, X.F if has_mb else None, [])


def _decode_fold(nf, K, fx=None, prof=None, mcap=0):
    fx = FX if fx is None else fx
    prof = X.PROFILE_V1 if prof is None else prof
    has_mb = bool(mcap) and AD.KIND_SEND in prof.KINDS
    w = 5 + (mcap + 1 if has_mb else 0)
    fld = _spine(nf, w * K)
    out = []
    for e in range(K):
        b = w * e
        row = (C.dec_state_v6(fx, fld[b + 0]),
               sorted(X.dec_factvec(fld[b + 1], CAP, prof)),
               sorted(X.dec_factvec(fld[b + 2], RCAP, prof)),
               int(X.dec_bool(fld[b + 3])),
               int(X.dec_bool(fld[b + 4])))
        if has_mb:
            # The slots are a SET (see ic_map): every golden observation point
            # re-sorts, so the projection sorts too rather than pretending the
            # packing order was meaningful.
            ks = [X.dec_operand(fld[b + 5 + k], prof.FKEY_W)
                  for k in range(mcap)]
            row += (tuple(sorted(k for k in ks if k != prof.FKEY_ALLONES)),
                    int(X.dec_bool(fld[b + 5 + mcap])))
        out.append(row)
    return out


def _mk_message(fk, fx, prof=None):
    """A decoded mailbox slot -> golden's message record.

    `admit._message` builds this from an accepted OPERATION; there is no
    operation on this side of the boundary, only the ClaimFactKey the message
    arrived under -- which is the whole of its identity (Slice A §1). So this
    is the same record reached from the other end, and it is a FUNCTION of the
    key so a slot cannot carry a field the key does not determine."""
    wq, sq, dg, pk = _unpack_fkey(fk, prof)
    _, mb, body = _payload_of(pk, fx)
    return {"writer_id": wq, "sequence": sq, "digest": dg, "payload_key": pk,
            "mailbox": mb, "body": tuple(int(v) for v in body)}


def _reject_entries(claim, epoch, policy_id):
    """The epoch's `MailboxReject` ledger entries, read off reduced state.

    A projection, not a second reducer. The reduced trajectory already
    contains everything the entry names: an event key that is IN the facts and
    NOT in the receipts had no receipt minted for it, and its candidates are
    the distinct (digest, payload_key) pairs of its facts. Under the frozen
    policy this set is always empty -- an equivocal key still mints a receipt
    for its minimum -- so the reconstruction is self-selecting and every
    pre-5c caller renders byte-identically.

    The VERDICT comes from golden's own `resolve_candidates`, called on the
    reconstructed candidate list, rather than from a reason string respelled
    here. `_project_claims` already reaches into `AD._op_outcome` to rebuild a
    receipt's outcome for exactly this reason: the projection may re-derive
    golden's pure functions, but it may not paraphrase them.

    Order is golden's: it resolves `sorted({event keys in facts}) - receipts`,
    so ascending event key IS the emission order, not a re-sort imposed here.

    The reconstruction reads POST-epoch state, and that is exact rather than
    lucky. Golden resolves against post-OBSERVE facts (identical to the stored
    ones) and appends a receipt only for an ACCEPTED key -- so a key still
    absent from `receipts` after the epoch is precisely a key this epoch
    refused, and a key present is precisely one it did not.

    BOUNDARY, stated rather than hidden: golden abandons the WHOLE ACCEPT
    stage on EITHER capacity overflow -- no receipts and no rejects -- but
    both fault bits are STICKY LATCHES, so from reduced state alone "this
    epoch abandoned ACCEPT" and "an earlier epoch did, and this one ran
    normally" are not distinguishable. A batch that overflows facts skips
    ACCEPT; a later empty batch under the same still-set latch does not. This
    projection therefore renders NO rejects for any epoch in a faulted
    trajectory. That direction is deliberate: it can omit an entry golden
    emitted (a LOUD film mismatch) but can never invent one golden did not (a
    QUIET false pass). Every row that pins reject rendering runs a fault-free
    trajectory, where the two readings coincide.
    """
    if (not policy_id or claim["receipt_capacity_fault"]
            or claim["fact_capacity_fault"]):
        return []
    resolve = AD.get_policy(policy_id)["resolve_candidates"]
    cands = {}
    for f in claim["facts"]:
        ek = (f["writer_id"], f["sequence"])
        if ek in claim["receipts"]:
            continue
        cands.setdefault(ek, set()).add((f["digest"], f["payload_key"]))
    out = []
    for ek in sorted(cands):
        cs = sorted(cands[ek])
        verdict = resolve(ek, cs)
        if verdict[0] != "Accepted":
            out.append(("MailboxReject", ek, epoch, verdict[1], tuple(cs)))
    return out


def _project_claims(decoded, epoch0, fx=None, prof=None, policy_id=None):
    """Rebuild the per-epoch claim states from the decoded trajectory.
    accepted_epoch = epoch of a receipt's FIRST appearance (== golden).

    When the rows carry a mailbox (7 fields, `_decode_fold(..., mcap>0)`), the
    D6 sibling fields are rebuilt too. `inbox` at epoch e is epoch e-1's
    emitted bundle and `next_inbox` is epoch e's -- D7's lifetime law read off
    a shift, with epoch 0's inbox empty because there is no previous epoch, not
    because a rule says so.

    `policy_id` (commit 5c) is the sealed world's declared acceptance policy.
    It is what lets the projection render a refused event key: see
    `_reject_entries`. None reproduces the pre-5c rendering exactly."""
    fx = FX if fx is None else fx
    first_seen = {}
    claims = []
    mb_ids = sorted(AD.mailboxes_of(fx))
    for e, row in enumerate(decoded):
        w, fv, rv, fo, fa = row[:5]
        for fk in rv:
            wq, sq, _, _ = _unpack_fkey(fk, prof)
            first_seen.setdefault((wq, sq), e)
        facts = []
        for fk in fv:
            wq, sq, dg, pk = _unpack_fkey(fk, prof)
            facts.append({"writer_id": wq, "sequence": sq, "digest": dg,
                          "payload_key": pk, "payload": _payload_of(pk, fx)})
        receipts = {}
        for fk in rv:
            wq, sq, dg, pk = _unpack_fkey(fk, prof)
            payload = _payload_of(pk, fx)
            receipts[(wq, sq)] = {"accepted_digest": dg, "accepted_payload_key": pk,
                                  "accepted_epoch": epoch0 + first_seen[(wq, sq)],
                                  "outcome": AD._op_outcome(fx, payload)}
        claim = {"facts": facts, "receipts": receipts,
                 "fact_capacity_fault": fo, "receipt_capacity_fault": fa}
        # D11 ledger order, read off the same three events golden emits and in
        # the same order it emits them -- which is the order of `admit_step`
        # itself, not a sort chosen here:
        #   COMMIT of the PREVIOUS epoch's sends (`_roll_mailboxes`) runs at
        #     the TOP, so every MailboxDeliver comes first;
        #   ACCEPT resolves in the middle, appending one MailboxReject per
        #     unresolved key;
        #   `_commit_deliveries` runs LAST, so every MailboxEnqueue is after
        #     both.
        #
        # The rejects are computed OUTSIDE the mailbox-row branch, and that is
        # the correction rather than a tidy-up. A reject is not a mailbox
        # event: it is seam 1 refusing an event key, BEFORE MAP has looked at
        # what operation the key carried. Gating it on the presence of a
        # mailbox bundle silently made it Send-specific, which is exactly what
        # the ruling forbade -- and the world that proves it is real is a
        # mailbox-bearing, ROUTE-FREE one. Such a world DECLARES the mailbox
        # policy (chosen by mailbox presence) but lowers under the v1 profile
        # (chosen by routes), so `mcap` is 0 and the reduced row has five
        # fields; an equivocal SetRotor in it is refused by the reduction and
        # rendered by nothing.
        rejects = _reject_entries(claim, epoch0 + e, policy_id)
        if len(row) > 5:
            nxt = [_mk_message(k, fx, prof) for k in row[5]]
            prev = ([_mk_message(k, fx, prof) for k in decoded[e - 1][5]]
                    if e else [])
            inbox = sorted(prev, key=AD._msg_key)
            claim["mailbox_states"] = {
                mb: {"inbox": [m for m in inbox if m["mailbox"] == mb],
                     "next_inbox": sorted((m for m in nxt
                                           if m["mailbox"] == mb),
                                          key=AD._msg_key)}
                for mb in mb_ids}
            claim["mailbox_capacity_fault"] = row[6]
            claim["ledger_entries"] = (
                [("MailboxDeliver", m["mailbox"], epoch0 + e, m)
                 for m in inbox]
                + rejects
                + [("MailboxEnqueue", m["mailbox"], epoch0 + e, m)
                   for m in sorted(nxt, key=AD._msg_key)])
        elif rejects:
            # Deliberately conditional. Golden sets `ledger_entries`
            # unconditionally, and matching that here would be more faithful
            # but would add a key to EVERY claim this projection has ever
            # produced -- and `policy_id` defaults to None precisely so that
            # pre-5c callers render exactly as they did. An empty list and an
            # absent key are indistinguishable to `film_bytes_v7`, which reads
            # `st.get("ledger_entries", [])`, so the faithful spelling buys
            # nothing and costs the inertness claim.
            claim["ledger_entries"] = rejects
        claims.append(claim)
    return claims


def _traj_summary(decoded):
    """Comparable trajectory fingerprint: per-epoch (fact_fkeys, rcpt_fkeys,
    fobs, facc, world-rotor, world-fault)."""
    out = []
    for row in decoded:
        w, fv, rv, fo, fa = row[:5]
        out.append((tuple(fv), tuple(rv), fo, fa,
                    w.get("rotor_sp"), w.get("fault_ob")))
    return out


def _golden_summary(gold):
    out = []
    for w, claim, fv, rv, fo, fa in gold:
        out.append((tuple(fv), tuple(rv), fo, fa,
                    w.get("rotor_sp"), w.get("fault_ob")))
    return out


def _film(world, claim, t, fx=None, mailboxes=None, policy_id=None):
    """The projection's Film v0.7 rendering.

    `policy_id` is the SEALED policy the trajectory ran under, and it is passed
    through rather than left to default because Core 0.2.0 made the film's
    `admit:policy=` line report the seam that produced the receipts below it.
    Defaulting it here would relabel a mailbox world's film with the frozen
    policy -- which is what the pre-0.2.0 film did, and what T7g measured."""
    fx = FX if fx is None else fx
    return film_bytes_v7(*state_to_film_args_v6(fx, world, t), state=claim,
                         mailboxes=mailboxes, policy_id=policy_id)


# ---------------------------------------------------------------- driver
def main():
    print("[BINDING admit-3b5f2b-fold] persistent claim/world fold over K "
          "epochs in ONE term (single native trajectory)")
    allok = True
    native_ok = True
    t0 = time.time()

    def rep(ok, okn, label):
        nonlocal allok, native_ok
        allok &= ok
        tag = "PASS" if ok else "FAIL"
        if okn is False:
            native_ok = False
            tag = "FAIL(native)"
        print(f"  [{tag}] {label}")

    def run(world0, batches, epoch0=1):
        gold = _golden_traj(AD.init_claimstate(), world0, batches, epoch0)
        fv0 = X.enc_factvec([], CAP)
        rv0 = X.enc_factvec([], RCAP)
        term = _build_fold(batches, fv0, rv0, C.enc_state_v6(FX, world0))
        K = len(batches)
        ref = _decode_fold(norm(term), K)
        gsum = _golden_summary(gold)
        okr = (_traj_summary(ref) == gsum)
        okn = None
        refn = None
        if not SKIP_NATIVE:
            refn = _decode_fold(native(term), K)
            okn = (_traj_summary(refn) == gsum)
        return okr, okn, ref, refn, gold, epoch0

    faultw = init_state_v6(FX)
    faultw["fault_ob"] = 1                     # a pre-existing physical fault

    # ---- O1 three-epoch persistence
    okr, okn, ref, _, gold, _ = run(faultw, [
        [mk_claim(1, 1, S((16, 0, 10, 0)))],
        [mk_claim(2, 2, S((16, 0, 20, 0))), mk_claim(3, 3, Rf)],
        [mk_claim(4, 4, ("SetRotor", "zz", (16, 0, 5, 0)))],
    ])
    rep(okr, okn, f"O1) 3-epoch persistence: facts {[len(g[2]) for g in gold]}, "
                  f"world rotor {ref[-1][0].get('rotor_sp')} fault "
                  f"{ref[-1][0].get('fault_ob')}")

    # ---- O2 two-epoch canonical
    okr, okn, ref2, _, gold2, _ = run(init_state_v6(FX), [
        [mk_claim(1, 1, S((16, 0, 10, 0))), mk_claim(2, 2, S((16, 0, 99, 0)))],
        [mk_claim(3, 3, Rf)],
    ])
    rep(okr, okn, f"O2) 2-epoch canonical: epoch-1 later-canonical commits "
                  f"rotor {ref2[0][0].get('rotor_sp')}, epoch-2 reset")

    # ---- O3 arrival-order independence (O2 epoch-1 batch reversed) REGRESSION
    okr, okn, ref3, _, gold3, _ = run(init_state_v6(FX), [
        [mk_claim(2, 2, S((16, 0, 99, 0))), mk_claim(1, 1, S((16, 0, 10, 0)))],
        [mk_claim(3, 3, Rf)],
    ])
    rep(okr and _traj_summary(ref3) == _traj_summary(ref2), okn,
        "O3) arrival-order independent: reversed epoch-1 batch -> IDENTICAL "
        "trajectory [PERMANENT REGRESSION]")

    # ---- O4 first-receipt authoritative across epochs
    okr, okn, ref4, _, gold4, _ = run(init_state_v6(FX), [
        [mk_claim(1, 1, S((16, 0, 10, 0)))],
        [mk_claim(1, 1, S((16, 0, 77, 0))), mk_claim(2, 2, Rf)],
    ])
    # (1,1) receipt from epoch 1 keeps its epoch-1 digest; (2,2) applied epoch 2
    r0 = ref4[0][2]; r1 = ref4[1][2]
    keep_11 = any(_unpack_fkey(fk)[:2] == (1, 1) and _unpack_fkey(fk)[2] == 0xf6
                  for fk in r1)
    rep(okr and keep_11, okn,
        "O4) first-receipt authoritative across epochs: (1,1) not remapped in "
        "epoch 2, (2,2) reset applied")

    # ---- O5 Film v0.7 trajectory parity (valid-target trajectories)
    # NOTE: a rejected SetRotor at an INVALID target keeps only its packed
    # CandidateKey (kind|idx) in the IC fact vector -- the original target NAME
    # is not carried, so its rendered claim line cannot round-trip (idx has no
    # spinner => "?"). The fact/receipt/world TRAJECTORY is nonetheless exact
    # (see O1). Film parity is therefore asserted over VALID-target trajectories
    # (same discipline as binding_run3n R9), including a fault-carrying 3-epoch
    # world so the physical reset renders too.
    film_ok = True
    for world0, batches in [(copy.deepcopy(faultw), [
                                [mk_claim(1, 1, S((16, 0, 10, 0)))],
                                [mk_claim(2, 2, S((16, 0, 20, 0))), mk_claim(3, 3, Rf)],
                                [mk_claim(4, 4, S((16, 0, 30, 0)))]]),
                            (init_state_v6(FX), [
                                [mk_claim(1, 1, S((16, 0, 10, 0))), mk_claim(2, 2, S((16, 0, 99, 0)))],
                                [mk_claim(3, 3, Rf)]])]:
        epoch0 = 1
        gold = _golden_traj(AD.init_claimstate(), world0, batches, epoch0)
        fv0 = X.enc_factvec([], CAP); rv0 = X.enc_factvec([], RCAP)
        term = _build_fold(batches, fv0, rv0, C.enc_state_v6(FX, world0))
        decoded = _decode_fold(norm(term), len(batches))
        claims = _project_claims(decoded, epoch0)
        for e in range(len(batches)):
            g_film = _film(gold[e][0], gold[e][1], epoch0 + e)
            f_film = _film(decoded[e][0], claims[e], epoch0 + e)
            if g_film != f_film:
                film_ok = False
    rep(film_ok, None,
        "O5) Film v0.7 trajectory parity: every epoch's fold projection renders "
        "the IDENTICAL v0.7 film (physical + claim + receipt-with-epoch)")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[admit-3b5f2b-fold] {'ALL PASS' if allok else 'FAILURES'} "
          f"-- {verdict} ({dt:.0f}s)")
    print("  [note] persistent ClaimState+WorldState fold complete; the whole "
          "K-epoch trajectory is one native normalization.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
