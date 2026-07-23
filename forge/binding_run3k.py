"""binding_run3k.py -- golden ADMIT semantic battery (slice 3b.5f-1).

Pins the OBSERVE -> ACCEPT -> MAP semantics of the claim-state reducer
(admit.py) against a Python golden, exactly per the GPT-5.6 ruling. The
reducer PRODUCES the EpochControl the v0.6 world already consumes, so the
world effect (COMMIT + REACT: rotor / pose / fault) is exercised through
the already-proven compile_step_v6 path (ref here; a representative native
gate confirms ic_ref == ic32 on the produced controls). The two deferred
rows -- persistent in-calculus claim-log fold and the FULL native gate on
a Scott-encoded claim SET -- are slice 3b.5f-2 (IC lowering).

Battery (16 -- adds the two GPT-5.6 golden-repair witnesses as permanent
regressions: reduced-digest collision, and reversed overflowing batch):
  1  new unambiguous claim              (receipt created, applied once)
  2  accepted retransmission            (no state / receipt / effect change)
  3  same-batch equivocation            (candidate-min winner, host-order indep)
  4  cross-batch equivocation           (first receipt authoritative)
  5  conflicting retransmission         (claim set unchanged after first obs)
  6  recognition convergence            (all arrival patterns -> same candidates)
  7  acceptance separation              (different logs retain different receipts)
  8  later conflict, no rollback        (committed effect survives dispute)
  9  rejected accepted op               (receipt persists, retransmit no retry)
  10 two distinct rotor events          (canonical order -> final committed rotor)
  11 reset claim                        (Ruling-1 reset semantics via ADMIT)
  12 reset + overflow                   (current overflow relatches)
  13 digest collision witness           (Correction 1: same digest, distinct
                                         payloads stay disputed; candidate key)
  14 fact capacity, reversed batch      (Correction 2: atomic; no evict / no
                                         partial; reversed batch == forward)
  15 receipt capacity, atomic           (Correction 2: no receipts / effects
                                         from an over-capacity accept batch)
  16 Law 6 witness                      (receipt state -> Film v0.7 divergence)
"""
import os, sys, time, copy
sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import binlib as BL
import compiler as C
from fixture import init_state_v6, state_to_film_args_v6
import admit as AD
from admit import (mk_claim, admit_step, init_claimstate, recognition,
                   film_bytes_v7, ACCEPTANCE_POLICY_ID)
from binding_run3j import mkfx, step_once, norm, native

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"


def drive(fx, step, st, state, batch, epoch, fire, runner=norm):
    state, cfg, rst = admit_step(state, batch, epoch, fx)
    st2 = step_once(fx, step, st, cfg, rst, fire, runner=runner)
    return state, cfg, rst, st2


def find_collision(fx):
    """First lexicographic pair of DISTINCT valid SetRotor payloads on 'sp'
    that share a reduced-WD digest -- a real collision the candidate key must
    survive. (GPT-5.6's example (16,0,10,0)/(16,1,5,0) is one such pair; this
    searches so the witness is robust to the exact canon formatting.)"""
    one = 16
    seen = {}
    for a in range(0, 24):
        for b in range(0, 24):
            p = ("SetRotor", "sp", (one, a, b, 0))
            d = AD.pdigest(p)
            if d in seen and seen[d] != p:
                return seen[d], p
            seen.setdefault(d, p)
    raise AssertionError("no collision found in search window")


def main():
    print(f"[BINDING admit-3b5f1] golden claim-state reducer "
          f"({AD.ACCEPTANCE_POLICY_ID})")
    allok = True
    native_status = "PASS_REF_AND_NATIVE"
    t0 = time.time()
    w, n = 8, 4
    one = 1 << n
    big = (1 << (w - 1)) - 1
    fx = mkfx(w, n)
    step, _ = C.compile_step_v6(fx)
    st0 = init_state_v6(fx)

    rotA = (one, 1, 0, 0)
    rotB = (one, 2, 0, 0)
    setA = ("SetRotor", "sp", rotA)
    setB = ("SetRotor", "sp", rotB)
    rstOb = ("ResetFault", "ob")

    # ---- 1) new unambiguous claim: one receipt, Applied, rotor committed
    s = init_claimstate()
    s1, cfg1, rst1, w1 = drive(fx, step, st0, s, [mk_claim(1, 1, setA)], 0,
                               {"sp": True})
    r1 = s1["receipts"][(1, 1)]
    ok1 = (len(s1["facts"]) == 1 and r1["outcome"] == ("Applied",)
           and recognition(s1, (1, 1)) == "unambiguous"
           and cfg1 == {"sp": rotA} and rst1 == {}
           and tuple(w1["rotor_sp"]) == rotA)
    allok &= ok1
    print(f"  [{'PASS' if ok1 else 'FAIL'}] 1) new unambiguous claim "
          f"(receipt Applied, rotor->{tuple(w1['rotor_sp'])})")

    # ---- 2) accepted retransmission: no new fact / receipt / effect
    s2, cfg2, rst2, _ = drive(fx, step, w1, s1, [mk_claim(1, 1, setA)], 1,
                              {"sp": True})
    ok2 = (s2["facts"] == s1["facts"] and s2["receipts"] == s1["receipts"]
           and cfg2 == {} and rst2 == {})
    allok &= ok2
    print(f"  [{'PASS' if ok2 else 'FAIL'}] 2) accepted retransmission "
          f"(no new fact/receipt; cfg empty)")

    # ---- 3) same-batch equivocation: digest-min winner, order-independent
    dA, dB = AD.pdigest(setA), AD.pdigest(setB)
    lo = rotA if dA <= dB else rotB
    sab, cfgab, _, _ = drive(fx, step, st0, init_claimstate(),
                             [mk_claim(2, 1, setA), mk_claim(2, 1, setB)], 0,
                             {"sp": True})
    sba, cfgba, _, _ = drive(fx, step, st0, init_claimstate(),
                             [mk_claim(2, 1, setB), mk_claim(2, 1, setA)], 0,
                             {"sp": True})
    rec3 = recognition(sab, (2, 1))
    acc3 = sab["receipts"][(2, 1)]["accepted_digest"]
    ok3 = (sab["facts"] == sba["facts"] and cfgab == cfgba
           and rec3 == "disputed" and acc3 == min(dA, dB)
           and cfgab == {"sp": lo})
    allok &= ok3
    print(f"  [{'PASS' if ok3 else 'FAIL'}] 3) same-batch equivocation "
          f"(disputed; digest-min={min(dA, dB):02x}; order-indep)")

    # ---- 4) cross-batch equivocation: first receipt authoritative
    sc = init_claimstate()
    sc, _, _, wc = drive(fx, step, st0, sc, [mk_claim(3, 1, setA)], 0,
                         {"sp": True})
    acc_first = sc["receipts"][(3, 1)]["accepted_digest"]
    sc, cfg4, _, _ = drive(fx, step, wc, sc, [mk_claim(3, 1, setB)], 1,
                           {"sp": True})
    ok4 = (sc["receipts"][(3, 1)]["accepted_digest"] == acc_first == dA
           and recognition(sc, (3, 1)) == "disputed" and cfg4 == {})
    allok &= ok4
    print(f"  [{'PASS' if ok4 else 'FAIL'}] 4) cross-batch equivocation "
          f"(first receipt {dA:02x} kept; later obs disputes, no re-apply)")

    # ---- 5) conflicting retransmission: claim set unchanged after first obs
    before5 = copy.deepcopy(sc["facts"])
    sc2, cfg5, _, _ = drive(fx, step, st0, sc, [mk_claim(3, 1, setB)], 2,
                            {"sp": False})
    ok5 = (sc2["facts"] == before5 and cfg5 == {})
    allok &= ok5
    print(f"  [{'PASS' if ok5 else 'FAIL'}] 5) conflicting retransmission "
          f"(monotone set unchanged)")

    # ---- 6) recognition convergence: every arrival pattern -> same digests
    def digs(state, ek):
        return sorted({f["digest"] for f in state["facts"]
                       if (f["writer_id"], f["sequence"]) == ek})
    p_together = admit_step(init_claimstate(),
                            [mk_claim(4, 1, setA), mk_claim(4, 1, setB)], 0,
                            fx)[0]
    p_split = admit_step(admit_step(init_claimstate(),
                                    [mk_claim(4, 1, setA)], 0, fx)[0],
                         [mk_claim(4, 1, setB)], 1, fx)[0]
    p_rev = admit_step(admit_step(init_claimstate(),
                                  [mk_claim(4, 1, setB)], 0, fx)[0],
                       [mk_claim(4, 1, setA)], 1, fx)[0]
    ok6 = (digs(p_together, (4, 1)) == digs(p_split, (4, 1))
           == digs(p_rev, (4, 1)) == sorted({dA, dB}))
    allok &= ok6
    print(f"  [{'PASS' if ok6 else 'FAIL'}] 6) recognition convergence "
          f"(3 arrival patterns -> digest set {sorted({dA, dB})})")

    # ---- 7) acceptance separation: different logs, different receipts
    log1 = admit_step(admit_step(init_claimstate(),
                                 [mk_claim(5, 1, setA)], 0, fx)[0],
                      [mk_claim(5, 1, setB)], 1, fx)[0]
    log2 = admit_step(admit_step(init_claimstate(),
                                 [mk_claim(5, 1, setB)], 0, fx)[0],
                      [mk_claim(5, 1, setA)], 1, fx)[0]
    a1 = log1["receipts"][(5, 1)]["accepted_digest"]
    a2 = log2["receipts"][(5, 1)]["accepted_digest"]
    ok7 = (a1 == dA and a2 == dB and a1 != a2
           and digs(log1, (5, 1)) == digs(log2, (5, 1)))
    allok &= ok7
    print(f"  [{'PASS' if ok7 else 'FAIL'}] 7) acceptance separation "
          f"(log1 accepts {a1:02x}, log2 accepts {a2:02x}; facts agree)")

    # ---- 8) later conflict, no rollback: committed rotor survives dispute
    s8 = init_claimstate()
    s8, _, _, w8 = drive(fx, step, st0, s8, [mk_claim(6, 1, setA)], 0,
                         {"sp": True})
    committed = tuple(w8["rotor_sp"])
    s8, cfg8, _, w8b = drive(fx, step, w8, s8, [mk_claim(6, 1, setB)], 1,
                             {"sp": False})
    ok8 = (committed == rotA and cfg8 == {}
           and tuple(w8b["rotor_sp"]) == rotA
           and recognition(s8, (6, 1)) == "disputed")
    allok &= ok8
    print(f"  [{'PASS' if ok8 else 'FAIL'}] 8) later conflict, no rollback "
          f"(committed rotor {tuple(w8b['rotor_sp'])} survives dispute)")

    # ---- 9) rejected accepted op: receipt persists, retransmit no retry
    bad = ("SetRotor", "nope", rotA)
    s9 = init_claimstate()
    s9, cfg9, _, w9 = drive(fx, step, st0, s9, [mk_claim(7, 1, bad)], 0,
                            {"sp": True})
    r9 = s9["receipts"][(7, 1)]
    s9b, cfg9b, _, _ = drive(fx, step, w9, s9, [mk_claim(7, 1, bad)], 1,
                             {"sp": True})
    ok9 = (r9["outcome"] == ("Rejected", "unknown_spinner") and cfg9 == {}
           and tuple(w9["rotor_sp"]) == tuple(st0["rotor_sp"])
           and s9b["receipts"] == s9["receipts"] and cfg9b == {})
    allok &= ok9
    print(f"  [{'PASS' if ok9 else 'FAIL'}] 9) rejected accepted op "
          f"(receipt {r9['outcome'][0]} persists; retransmit no retry)")

    # ---- 10) two distinct rotor events: canonical order -> final rotor
    e1 = mk_claim(1, 2, setA)                 # (w=1,s=2)
    e2 = mk_claim(2, 2, setB)                 # (w=2,s=2)
    order = sorted([(e1["sequence"], e1["writer_id"], e1["digest"], rotA),
                    (e2["sequence"], e2["writer_id"], e2["digest"], rotB)])
    winner = order[-1][3]
    s10, cfg10, _, w10 = drive(fx, step, st0, init_claimstate(),
                               [e1, e2], 0, {"sp": True})
    ok10 = (cfg10 == {"sp": winner} and tuple(w10["rotor_sp"]) == winner
            and len(s10["receipts"]) == 2)
    allok &= ok10
    print(f"  [{'PASS' if ok10 else 'FAIL'}] 10) two rotor events "
          f"(canonical-last wins -> {tuple(w10['rotor_sp'])})")

    # ---- 11) reset claim: Ruling-1 reset semantics through ADMIT
    st_f = copy.deepcopy(st0); st_f["fault_ob"] = 1
    s11, cfg11, rst11, w11 = drive(fx, step, st_f, init_claimstate(),
                                   [mk_claim(8, 1, rstOb)], 0, {"sp": False})
    ok11 = (rst11 == {"ob": True} and cfg11 == {}
            and w11["fault_ob"] == 0
            and s11["receipts"][(8, 1)]["outcome"] == ("Applied",))
    allok &= ok11
    print(f"  [{'PASS' if ok11 else 'FAIL'}] 11) reset claim "
          f"(ResetFault accepted -> fault {w11['fault_ob']})")

    # ---- 12) reset + overflow same epoch: current overflow relatches
    st_big = copy.deepcopy(st0); st_big["pose_ob"] = (big, big, 0, 0)
    st_big["fault_ob"] = 1
    setBig = ("SetRotor", "sp", (big, big, 0, 0))
    s12, cfg12, rst12, w12 = drive(fx, step, st_big, init_claimstate(),
                                   [mk_claim(9, 1, rstOb),
                                    mk_claim(9, 2, setBig)], 0, {"sp": True})
    _, gflt = BL.golden_rot_forge(w, n, (big, big, 0, 0), (big, big, 0, 0))
    ok12 = (rst12 == {"ob": True} and cfg12 == {"sp": (big, big, 0, 0)}
            and w12["fault_ob"] == 1 == gflt)
    allok &= ok12
    print(f"  [{'PASS' if ok12 else 'FAIL'}] 12) reset + overflow "
          f"(reset cannot hide same-epoch fault -> {w12['fault_ob']})")

    # ---- 13) digest collision witness (Correction 1): two DISTINCT payloads
    # that share a reduced digest under one event key stay DISPUTED; the
    # candidate key (digest, payload_key) is the collision tie-break.
    P1, P2 = find_collision(fx)
    assert AD.pdigest(P1) == AD.pdigest(P2) and P1 != P2, "no real collision"
    dcol = AD.pdigest(P1)
    pk1, pk2 = AD.payload_key(fx, P1), AD.payload_key(fx, P2)
    s13, cfg13, _ = admit_step(init_claimstate(),
                               [mk_claim(12, 1, P1), mk_claim(12, 1, P2)], 0, fx)
    r13 = s13["receipts"][(12, 1)]
    ok13 = (len(s13["facts"]) == 2                     # both facts retained
            and recognition(s13, (12, 1)) == "disputed"
            and r13["accepted_digest"] == dcol
            and r13["accepted_payload_key"] == min(pk1, pk2)
            and cfg13 == {"sp": (P1 if pk1 <= pk2 else P2)[2]})
    allok &= ok13
    print(f"  [{'PASS' if ok13 else 'FAIL'}] 13) digest collision "
          f"(digest {dcol:02x} shared; disputed; candidate-min pkey wins)")

    # ---- 14) fact capacity, ATOMIC + reversed (Correction 2): an overflowing
    # batch is rejected WHOLE; a reversed overflowing batch retains the SAME
    # facts (no eviction, no partial apply, order-independent at the boundary).
    fill = [mk_claim(20, i, ("SetRotor", "sp", (one, i, 0, 0)))
            for i in range(1, AD.MAX_FACTS - 1)]     # MAX_FACTS-2 = 4 facts
    base14, _, _ = admit_step(init_claimstate(), fill, 0, fx)
    ov = [mk_claim(20, i, ("SetRotor", "sp", (one, i, 0, 0)))
          for i in range(AD.MAX_FACTS - 1, AD.MAX_FACTS + 2)]   # 3 new > 2 free
    sfwd, cfwd, _ = admit_step(base14, ov, 1, fx)
    srev, crev, _ = admit_step(base14, list(reversed(ov)), 1, fx)
    ok14 = (sfwd["fact_capacity_fault"] == 1 and srev["fact_capacity_fault"] == 1
            and len(sfwd["facts"]) == len(base14["facts"]) == AD.MAX_FACTS - 2
            and sfwd["facts"] == srev["facts"] == base14["facts"]
            and cfwd == {} and crev == {})
    allok &= ok14
    print(f"  [{'PASS' if ok14 else 'FAIL'}] 14) fact capacity atomic "
          f"(reject whole batch; reversed==forward; facts stay "
          f"{len(sfwd['facts'])}, no evict)")

    # ---- 15) receipt capacity, ATOMIC (Correction 2): when the accept batch's
    # new receipts do not all fit, create NONE and emit no controls (facts stay
    # -- monotone). Exercised with a lowered MAX_EVENTS proof parameter.
    saved_ME = AD.MAX_EVENTS
    AD.MAX_EVENTS = 1
    try:
        s15, cfg15, rst15 = admit_step(
            init_claimstate(),
            [mk_claim(30, 1, setA), mk_claim(31, 1, setB)], 0, fx)
    finally:
        AD.MAX_EVENTS = saved_ME
    ok15 = (s15["receipt_capacity_fault"] == 1 and len(s15["receipts"]) == 0
            and len(s15["facts"]) == 2 and cfg15 == {} and rst15 == {})
    allok &= ok15
    print(f"  [{'PASS' if ok15 else 'FAIL'}] 15) receipt capacity atomic "
          f"(facts kept={len(s15['facts'])}; 0 receipts, no controls)")

    # ---- 16) Law 6 witness: receipt state -> Film v0.7 divergence
    E = mk_claim(11, 1, setA)
    stateA = init_claimstate()                         # no receipt for E
    stateB = admit_step(init_claimstate(), [E], 0, fx)[0]   # has receipt
    args = state_to_film_args_v6(fx, st0, 5)
    filmA = film_bytes_v7(*args, state=stateA)
    filmB = film_bytes_v7(*args, state=stateB)
    # retransmit E into each; A applies (rotor changes), B no-ops
    _, cfgA, _ = admit_step(stateA, [E], 6, fx)
    _, cfgB, _ = admit_step(stateB, [E], 6, fx)
    ok16 = (filmA != filmB and cfgA == {"sp": rotA} and cfgB == {})
    allok &= ok16
    print(f"  [{'PASS' if ok16 else 'FAIL'}] 16) Law 6 witness "
          f"(films differ pre-input; retransmit A applies, B no-op)")

    # ---- native gate (representative): ic_ref == ic32 on produced controls
    if SKIP_NATIVE:
        native_status = "PASS_REF_ONLY (native skipped)"
        print("  [SKIP] native gate skipped (TRVM_SKIP_NATIVE=1)")
    else:
        # case 1 (SetRotor) and case 12 (reset+overflow) trajectories
        _, c1, r1n = admit_step(init_claimstate(), [mk_claim(1, 1, setA)],
                                0, fx)
        n1r = step_once(fx, step, st0, c1, r1n, {"sp": True}, runner=norm)
        n1c = step_once(fx, step, st0, c1, r1n, {"sp": True}, runner=native)
        _, c12, r12 = admit_step(init_claimstate(),
                                 [mk_claim(9, 1, rstOb),
                                  mk_claim(9, 2, setBig)], 0, fx)
        n12r = step_once(fx, step, st_big, c12, r12, {"sp": True},
                         runner=norm)
        n12c = step_once(fx, step, st_big, c12, r12, {"sp": True},
                         runner=native)
        okN = (n1r == n1c and n12r == n12c)
        allok &= okN
        if not okN:
            native_status = "REF_ONLY (native MISMATCH)"
        print(f"  [{'PASS' if okN else 'FAIL'}] native gate: ADMIT controls "
              f"ic_ref == ic32 (SetRotor + reset/overflow)")

    dt = time.time() - t0
    verdict = native_status if allok else "FAIL"
    print(f"\n[admit-3b5f1] {'ALL PASS' if allok else 'FAILURES'} -- "
          f"{verdict} ({dt:.0f}s)")
    print("  [note] persistent in-calculus claim-log fold + full native "
          "gate on the Scott-encoded claim SET are slice 3b.5f-2.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
