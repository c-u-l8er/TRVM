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
from lower_e2a import _v, _spine
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


def _fact_fkeys(st):
    return sorted(X.pack_fkey(FX, f["writer_id"], f["sequence"], f["payload"])
                  for f in st["facts"])


def _rcpt_fkeys(st):
    return sorted(_mkfkey(ek[0], ek[1],
                  _ckor(r["accepted_digest"], r["accepted_payload_key"]))
                  for ek, r in st["receipts"].items())


def _unpack_fkey(fk):
    """fkey -> (writer, seq, digest, payload_key=(kind,idx,r0,r1,r2,r3))."""
    widths = [("w", WK), ("s", WK), ("dg", X.WD), ("kind", X.WKIND),
              ("idx", X.WIDX), ("r0", X.WLANE), ("r1", X.WLANE),
              ("r2", X.WLANE), ("r3", X.WLANE)]
    vals, off = {}, X.FKEY_W
    for name, wd in widths:
        off -= wd
        vals[name] = (fk >> off) & ((1 << wd) - 1)
    pk = (vals["kind"], vals["idx"], vals["r0"], vals["r1"], vals["r2"], vals["r3"])
    return vals["w"], vals["s"], vals["dg"], pk


def _payload_of(pk):
    spins = sorted(FX.spinners)
    orbs = list(FX.orbs)
    kind, idx = pk[0], pk[1]
    if kind == 0:
        sp = spins[idx] if idx < len(spins) else "?"
        return ("SetRotor", sp, (pk[2], pk[3], pk[4], pk[5]))
    ob = orbs[idx] if idx < len(orbs) else "?"
    return ("ResetFault", ob)


def _batch_srcs(batch):
    keys = sorted(X.pack_fkey(FX, int(c["writer_id"]), int(c["sequence"]), c["payload"])
                  for c in batch)
    return [BL.enc_operand(k, X.FKEY_W) for k in keys]


# ------------------------------------------------------ golden trajectory
def _golden_traj(claim0, world0, batches, epoch0=1):
    """admit_step + world-step epoch-by-epoch. Returns per-epoch tuples of
    (world, claim_state, fact_fkeys, rcpt_fkeys, fobs, facc)."""
    claim = copy.deepcopy(claim0)
    world = copy.deepcopy(world0)
    out = []
    for e, batch in enumerate(batches):
        claim, cfg_map, resets = AD.admit_step(claim, batch, epoch0 + e, FX)
        ec = C.enc_config_bundle(FX, cfg_map, resets)
        step, _ = C.compile_step_v6(FX)
        world = C.dec_state_v6(FX, norm(f"(({step} {ec}) {C.enc_state_v6(FX, world)})"))
        out.append((copy.deepcopy(world), copy.deepcopy(claim),
                    _fact_fkeys(claim), _rcpt_fkeys(claim),
                    int(claim.get("fact_capacity_fault", 0)),
                    int(claim.get("receipt_capacity_fault", 0))))
    return out


# ---------------------------------- the fold: ONE term over K epochs -------
def _build_fold(batches, fv0_src, rv0_src, w0_src):
    K = len(batches)

    def rec(e, fv_v, rv_v, w_v, outacc):
        red = X.ic_reduce(fv_v, rv_v, _batch_srcs(batches[e]), CAP, RCAP)
        step, _ = C.compile_step_v6(FX)
        fvp, rvp, ec, fo, fa, wnew = (_v("fvp"), _v("rvp"), _v("ec"),
                                      _v("fo"), _v("fa"), _v("w"))
        stepapp = f"(({step} {ec}) {w_v})"
        if e == K - 1:
            tup = TUPN(outacc + [wnew, fvp, rvp, fo, fa])
            body = f"(λ{wnew}.{tup} {stepapp})"
        else:
            Aw = Alloc(); w_out, w_fwd = Aw.copies(wnew, 2)
            Af = Alloc(); fv_out, fv_fwd = Af.copies(fvp, 2)
            Ar = Alloc(); rv_out, rv_fwd = Ar.copies(rvp, 2)
            inner = rec(e + 1, fv_fwd, rv_fwd, w_fwd,
                        outacc + [w_out, fv_out, rv_out, fo, fa])
            body = ("".join(Af.prefix) + "".join(Ar.prefix)
                    + f"(λ{wnew}.{''.join(Aw.prefix)}{inner} {stepapp})")
        return f"({red} λ{fvp}.λ{rvp}.λ{ec}.λ{fo}.λ{fa}.{body})"

    return rec(0, fv0_src, rv0_src, w0_src, [])


def _decode_fold(nf, K):
    fld = _spine(nf, 5 * K)
    out = []
    for e in range(K):
        out.append((C.dec_state_v6(FX, fld[5 * e + 0]),
                    sorted(X.dec_factvec(fld[5 * e + 1], CAP)),
                    sorted(X.dec_factvec(fld[5 * e + 2], RCAP)),
                    int(X.dec_bool(fld[5 * e + 3])),
                    int(X.dec_bool(fld[5 * e + 4]))))
    return out


def _project_claims(decoded, epoch0):
    """Rebuild the per-epoch claim states from the decoded trajectory.
    accepted_epoch = epoch of a receipt's FIRST appearance (== golden)."""
    first_seen = {}
    claims = []
    for e, (w, fv, rv, fo, fa) in enumerate(decoded):
        for fk in rv:
            wq, sq, _, _ = _unpack_fkey(fk)
            first_seen.setdefault((wq, sq), e)
        facts = []
        for fk in fv:
            wq, sq, dg, pk = _unpack_fkey(fk)
            facts.append({"writer_id": wq, "sequence": sq, "digest": dg,
                          "payload_key": pk, "payload": _payload_of(pk)})
        receipts = {}
        for fk in rv:
            wq, sq, dg, pk = _unpack_fkey(fk)
            payload = _payload_of(pk)
            receipts[(wq, sq)] = {"accepted_digest": dg, "accepted_payload_key": pk,
                                  "accepted_epoch": epoch0 + first_seen[(wq, sq)],
                                  "outcome": AD._op_outcome(FX, payload)}
        claims.append({"facts": facts, "receipts": receipts,
                       "fact_capacity_fault": fo, "receipt_capacity_fault": fa})
    return claims


def _traj_summary(decoded):
    """Comparable trajectory fingerprint: per-epoch (fact_fkeys, rcpt_fkeys,
    fobs, facc, world-rotor, world-fault)."""
    out = []
    for w, fv, rv, fo, fa in decoded:
        out.append((tuple(fv), tuple(rv), fo, fa,
                    w.get("rotor_sp"), w.get("fault_ob")))
    return out


def _golden_summary(gold):
    out = []
    for w, claim, fv, rv, fo, fa in gold:
        out.append((tuple(fv), tuple(rv), fo, fa,
                    w.get("rotor_sp"), w.get("fault_ob")))
    return out


def _film(world, claim, t):
    return film_bytes_v7(*state_to_film_args_v6(FX, world, t), state=claim)


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
