"""binding_run3n.py -- 3b.5f-2a BUILD (reducer): the single-epoch ADMIT
reducer composed as ONE interaction-calculus term (ic_reduce = OBSERVE ->
ACCEPT -> MAP) and gated by a SINGLE native normalization per case
(ic_ref == ic32 == golden). This is the deliverable GPT-5.6's Ruling 3
named for 3b.5f-2a: facts + receipts flow through all three phases in one
reduction, MAP and ACCEPT both read the PRE-accept receipt vector, and the
output is TUP5(fact_vec', receipt_vec', EpochControl, fact_capacity_fault,
receipt_capacity_fault).

  R1 SetRotor + ResetFault -> EpochControl(pose, reset) + facts + receipts (native)
  R2 later-canonical-wins: two events, the canonically-later rotor is committed (native)
  R3 arrival-order independence: R2 with the batch reversed -> identical output (native)
     -- PERMANENT REGRESSION (Ruling 3 required case)
  R4 first-receipt authoritative: a pre-receipted event is NOT remapped, a fresh
     event in the same batch still applies                                  (native)
  R5 invalid target -> Rejected -> NoChange (no rotor, no reset)            (native)
  R6 collision 0xf6: two payloads share a reduced digest but pack to DISTINCT
     fkeys -> OBSERVE keeps BOTH facts (disputed), ACCEPT/MAP pick the min-ckey
     group leader -- Correction 1 through the whole reducer                 (native)
  R7 fact-capacity overflow: a batch that does not fit latches
     fact_capacity_fault, inserts NONE, emits NoChange                      (native)
  R8 fact-overflow arrival-order independence: R7 with the batch reversed ->
     identical verdict -- PERMANENT REGRESSION (Ruling 3 required case)     (native)
  R9 Film v0.7 parity: the reducer output projected to a claim state renders
     the IDENTICAL v0.7 film as the golden admit_step state (valid fresh cases)

Note (receipt-capacity fault): under MAX_EVENTS == MAX_FACTS == 6 with facts
monotone and >=1 fact per event, needed = events - R <= 6 - R = remaining, so
receipt_capacity_fault is UNREACHABLE in the composed single-epoch reducer.
The mechanism itself is gated at the ic_accept unit level in binding_run3m
(B5, 2 facts + 5 receipts = 7 event keys). Documented here, not re-forced.
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
import ic_ref as R
from admit import mk_claim
from binding_run3j import mkfx, norm, native
from fixture import init_state_v6, state_to_film_args_v6
from admit import film_bytes_v7
from lower_e2a import _dec_pair, _spine, T, F, PAIR as _PAIR

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"
CAP = AD.MAX_FACTS          # 6
RCAP = AD.MAX_EVENTS        # 6
CK = X.CKEY_W               # 44
WK = AD.WK                  # 4


# ------------------------------------------------------------- fkey helpers
def _mkfkey(w, s, ck):
    return (w << (WK + CK)) | (s << CK) | ck


def _ckey_of_receipt(dg, pk):
    return X._cat([(dg, X.WD), (pk[0], X.WKIND), (pk[1], X.WIDX),
                   (pk[2], X.WLANE), (pk[3], X.WLANE),
                   (pk[4], X.WLANE), (pk[5], X.WLANE)])


def _fact_fkeys(st):
    return sorted(X.pack_fkey(FX, f["writer_id"], f["sequence"], f["payload"])
                  for f in st["facts"])


def _receipt_fkeys(st):
    return sorted(_mkfkey(ek[0], ek[1],
                  _ckey_of_receipt(r["accepted_digest"], r["accepted_payload_key"]))
                  for ek, r in st["receipts"].items())


def _unpack_fkey(fk):
    """fkey -> (writer, seq, digest, payload_key=(kind,idx,r0,r1,r2,r3))."""
    widths = [("w", WK), ("s", WK), ("dg", X.WD), ("kind", X.WKIND),
              ("idx", X.WIDX), ("r0", X.WLANE), ("r1", X.WLANE),
              ("r2", X.WLANE), ("r3", X.WLANE)]
    vals = {}
    off = X.FKEY_W
    for name, wd in widths:
        off -= wd
        vals[name] = (fk >> off) & ((1 << wd) - 1)
    pk = (vals["kind"], vals["idx"], vals["r0"], vals["r1"], vals["r2"], vals["r3"])
    return vals["w"], vals["s"], vals["dg"], pk


# ------------------------------------------------------------- EC decoder
def _decode_ec(ec_src, runner):
    inner = _PAIR(T, "p")
    rc_elim = f"(({{rc}} {_PAIR(F, F)}) λp.{inner})".replace("{rc}", "rc")
    wrap = f"({ec_src} λrb.λfb.(rb λrc.(fb λrst.{_PAIR(rc_elim, 'rst')})))"
    t = runner(wrap)
    rcp, rstt = _dec_pair(t)
    reset = bool(X.dec_bool(rstt))
    tagt, poset = _dec_pair(rcp)
    tag = bool(X.dec_bool(tagt))
    pose = BL.dec_pose(poset, X.WLANE) if tag else None
    return pose, reset


def _decode_reduce(nf):
    """TUP5(fv', rv', ec, fobs, facc) normal form -> python values."""
    fld = _spine(nf, 5)
    fvp = sorted(X.dec_factvec(fld[0], CAP))
    rvp = sorted(X.dec_factvec(fld[1], RCAP))
    ec = _decode_ec(R.show(fld[2]), norm)          # ref-normalize the small EC
    fobs = int(X.dec_bool(fld[3]))
    facc = int(X.dec_bool(fld[4]))
    return fvp, rvp, ec, fobs, facc


# ------------------------------------------------------------- golden side
def _batch_srcs(batch):
    keys = sorted(X.pack_fkey(FX, int(c["writer_id"]), int(c["sequence"]), c["payload"])
                  for c in batch)
    return [BL.enc_operand(k, X.FKEY_W) for k in keys]


def _golden(initial, batch, epoch):
    st = copy.deepcopy(initial)
    facts_pre = _fact_fkeys(st)
    rcpt_pre = _receipt_fkeys(st)
    new_st, cfg_map, resets = AD.admit_step(st, batch, epoch, FX)
    g = (_fact_fkeys(new_st), _receipt_fkeys(new_st),
         _decode_ec(C.enc_config_bundle(FX, cfg_map, resets), norm),
         int(new_st.get("fact_capacity_fault", 0)),
         int(new_st.get("receipt_capacity_fault", 0)))
    return facts_pre, rcpt_pre, g, new_st


# ------------------------------------------------------- film reconstruction
def _reconstruct_claimstate(fv_keys, rv_keys, epoch, fobs, facc):
    """Rebuild a claim state from the reducer's decoded fkeys. Exact for
    fresh single epochs with valid targets (epoch/outcome recoverable)."""
    spins = sorted(FX.spinners)
    orbs = list(FX.orbs)

    def payload_of(pk):
        kind, idx = pk[0], pk[1]
        if kind == 0:
            sp = spins[idx] if idx < len(spins) else "?"
            return ("SetRotor", sp, (pk[2], pk[3], pk[4], pk[5]))
        ob = orbs[idx] if idx < len(orbs) else "?"
        return ("ResetFault", ob)

    facts = []
    for fk in fv_keys:
        w, s, dg, pk = _unpack_fkey(fk)
        facts.append({"writer_id": w, "sequence": s, "digest": dg,
                      "payload_key": pk, "payload": payload_of(pk)})
    receipts = {}
    for fk in rv_keys:
        w, s, dg, pk = _unpack_fkey(fk)
        payload = payload_of(pk)
        receipts[(w, s)] = {"accepted_digest": dg, "accepted_payload_key": pk,
                            "accepted_epoch": epoch,
                            "outcome": AD._op_outcome(FX, payload)}
    return {"facts": facts, "receipts": receipts,
            "fact_capacity_fault": fobs, "receipt_capacity_fault": facc}


def _film(claimstate, epoch):
    phys = init_state_v6(FX)
    return film_bytes_v7(*state_to_film_args_v6(FX, phys, epoch),
                         state=claimstate)


# ---------------------------------------------------------------- driver
FX = mkfx(8, 4)
S = lambda rot: ("SetRotor", "sp", rot)
Rf = ("ResetFault", "ob")


def main():
    print("[BINDING admit-3b5f2a-reducer] single-epoch OBSERVE->ACCEPT->MAP "
          "in ONE term")
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

    def run(initial, batch, epoch=3):
        facts_pre, rcpt_pre, gold, new_st = _golden(initial, batch, epoch)
        fv = X.enc_factvec(facts_pre, CAP)
        rv = X.enc_factvec(rcpt_pre, RCAP)
        red = X.ic_reduce(fv, rv, _batch_srcs(batch), CAP, RCAP)
        ref = _decode_reduce(norm(red))
        okr = (ref == gold)
        okn = None
        if not SKIP_NATIVE:
            okn = (_decode_reduce(native(red)) == gold)
        return okr, okn, ref, gold, new_st

    # ---- R1 SetRotor + ResetFault
    okr, okn, ref, gold, _ = run(AD.init_claimstate(),
                                 [mk_claim(1, 1, S((16, 0, 10, 0))),
                                  mk_claim(1, 2, Rf)])
    rep(okr, okn, f"R1) SetRotor+ResetFault -> EC{ref[2]} + "
                  f"{len(ref[0])} facts + {len(ref[1])} receipts")

    # ---- R2 later-canonical-wins
    okr, okn, ref, gold, _ = run(AD.init_claimstate(),
                                 [mk_claim(1, 1, S((16, 0, 10, 0))),
                                  mk_claim(2, 2, S((16, 0, 99, 0)))])
    rep(okr, okn, f"R2) later-canonical rotor committed -> pose {ref[2][0]}")

    # ---- R3 arrival-order independence (R2 reversed) -- PERMANENT REGRESSION
    okr, okn, ref_rev, gold_rev, _ = run(AD.init_claimstate(),
                                         [mk_claim(2, 2, S((16, 0, 99, 0))),
                                          mk_claim(1, 1, S((16, 0, 10, 0)))])
    rep(okr and ref_rev == ref, okn,
        "R3) arrival-order independent: reversed batch -> identical output "
        "[PERMANENT REGRESSION]")

    # ---- R4 first-receipt authoritative
    init = AD.init_claimstate()
    init, _, _ = AD.admit_step(init, [mk_claim(1, 1, S((16, 0, 10, 0)))], 1, FX)
    okr, okn, ref, gold, _ = run(init,
                                 [mk_claim(1, 1, S((16, 0, 77, 0))),
                                  mk_claim(2, 2, Rf)])
    rep(okr, okn, f"R4) first-receipt authoritative: (1,1) not remapped, "
                  f"(2,2) reset applied -> EC{ref[2]}")

    # ---- R5 invalid target -> NoChange
    okr, okn, ref, gold, _ = run(AD.init_claimstate(),
                                 [mk_claim(1, 1, ("SetRotor", "zz", (16, 0, 10, 0)))])
    rep(okr and ref[2] == (None, False), okn,
        f"R5) invalid spinner -> Rejected -> NoChange (EC{ref[2]})")

    # ---- R6 collision 0xf6: both facts kept, min-ckey leader accepted
    P1 = ("SetRotor", "sp", (16, 0, 10, 0))
    P2 = ("SetRotor", "sp", (16, 1, 5, 0))
    assert AD.pdigest(P1) == AD.pdigest(P2) == 0xf6 and P1 != P2
    okr, okn, ref, gold, _ = run(AD.init_claimstate(),
                                 [mk_claim(1, 1, P1), mk_claim(1, 1, P2)])
    rep(okr and len(ref[0]) == 2 and len(ref[1]) == 1, okn,
        f"R6) collision 0xf6 kept BOTH facts (disputed), one receipt "
        f"(min-ckey leader) -> pose {ref[2][0]}")

    # ---- R7 fact-capacity overflow: prefill 4 facts, add 3 new -> 7 > 6
    base = AD.init_claimstate()
    base, _, _ = AD.admit_step(base, [mk_claim(1, 1, S((16, 0, 1, 0))),
                                      mk_claim(2, 1, S((16, 0, 2, 0))),
                                      mk_claim(3, 1, S((16, 0, 3, 0))),
                                      mk_claim(4, 1, S((16, 0, 4, 0)))], 1, FX)
    of_batch = [mk_claim(5, 1, S((16, 0, 5, 0))),
                mk_claim(6, 1, S((16, 0, 6, 0))),
                mk_claim(7, 1, S((16, 0, 7, 0)))]
    okr, okn, ref, gold, _ = run(base, of_batch)
    rep(okr and ref[3] == 1 and ref[2] == (None, False)
        and len(ref[0]) == 4, okn,
        f"R7) fact-capacity overflow: fault={ref[3]}, inserted none "
        f"({len(ref[0])} facts kept), NoChange")

    # ---- R8 fact-overflow arrival-order independence -- PERMANENT REGRESSION
    okr, okn, ref_rev, gold_rev, _ = run(base, list(reversed(of_batch)))
    rep(okr and ref_rev == ref, okn,
        "R8) fact-overflow reversed batch -> identical reject verdict "
        "[PERMANENT REGRESSION]")

    # ---- R9 Film v0.7 parity (valid fresh cases: R1, R2, R2-reversed)
    film_ok = True
    for label, batch in [("R1", [mk_claim(1, 1, S((16, 0, 10, 0))),
                                 mk_claim(1, 2, Rf)]),
                         ("R2", [mk_claim(1, 1, S((16, 0, 10, 0))),
                                 mk_claim(2, 2, S((16, 0, 99, 0)))]),
                         ("R2rev", [mk_claim(2, 2, S((16, 0, 99, 0))),
                                    mk_claim(1, 1, S((16, 0, 10, 0)))])]:
        _, _, _, ref, gold, = (None,) * 5
        okr, okn, ref, gold, new_st = run(AD.init_claimstate(), batch, epoch=3)
        recon = _reconstruct_claimstate(ref[0], ref[1], 3, ref[3], ref[4])
        if _film(recon, 3) != _film(new_st, 3):
            film_ok = False
    rep(film_ok, None,
        "R9) Film v0.7 parity: reducer output projects to the IDENTICAL "
        "v0.7 film as golden (valid fresh cases)")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[admit-3b5f2a-reducer] {'ALL PASS' if allok else 'FAILURES'} "
          f"-- {verdict} ({dt:.0f}s)")
    print("  [note] single-epoch reducer complete; 3b.5f-2b persistent "
          "claim/world fold + single native trajectory lands in binding_run3o.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
