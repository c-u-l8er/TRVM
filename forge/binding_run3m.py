"""binding_run3m.py -- 3b.5f-2a BUILD (assembly): the ADMIT reducer's
OBSERVE and ACCEPT phases lowered onto Option A occupied-prefix sorted
structural vectors, golden-matched and NATIVE-gated (ic_ref == ic32 ==
golden). This is the assembly layer the 3b.5f-2a MEASURE (binding_run3l)
licensed: the three key mechanisms (candidate-min, key-eq, atomic-fits)
are now composed into the two atomic batch phases over sorted fkey vectors.

  B1 ic_insert_sorted: unrolled compare-shift insert-if-absent (append /
     middle / front / present-noop / invalid-noop / into-empty)     (native)
  B2 ic_observe ATOMIC: distinct-new count + capacity gate + insert-all;
     dedup (already-present + batch-internal), exact fill                (native)
  B3 OVERFLOW is arrival-order independent: the same overflowing batch,
     reversed, latches fact_capacity_fault and inserts NONE either way   (native)
  B4 COLLISION witness (0xf6): two payloads share a reduced digest but pack
     to DISTINCT fkeys, so OBSERVE keeps BOTH as distinct facts (disputed,
     never collapsed) -- Correction 1 as a pure-term property            (native)
  B5 ic_accept: accepted candidate = MIN CandidateKey = group leader of the
     sorted run; first receipt authoritative (existing event key -> no new
     receipt); receipt_capacity_fault atomic overflow                    (native)

Remaining for 3b.5f-2a: MAP -> EpochControl (rotor_bundle/fault_bundle) with
the accepted-Applied ops, the single reducer native gate wired through
compile_step_v6, and Film v0.7 parity.
"""
import os, sys, time
sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import binlib as BL
import admit as AD
import admit_ic as X
from binding_run3j import mkfx, norm, native
from lower_e2a import _dec_pair, T, F

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"
CAP = AD.MAX_FACTS          # 6
RCAP = AD.MAX_EVENTS        # 6
CK = X.CKEY_W


def ef(v):
    return BL.enc_operand(v, X.FKEY_W)


# ------------------------------------------------------------------ goldens
def g_insert(keys, nk, valid):
    ks = [k for k in keys if k != X.FKEY_ALLONES]
    if valid and nk not in ks:
        ks.append(nk)
    return sorted(ks)


def g_observe(facts, batch):
    present = set(facts)
    new = sorted(set(batch) - present)
    if len(new) > (AD.MAX_FACTS - len(facts)):
        return sorted(facts), 1
    return sorted(facts + list(new)), 0


def g_accept(facts, receipts):
    ex = {r >> CK for r in receipts}
    groups = {}
    for f in sorted(facts):
        ek = f >> CK
        if ek not in groups:
            groups[ek] = f                 # first == min ckey (group leader)
    needed = sorted(v for ek, v in groups.items() if ek not in ex)
    if len(needed) > (AD.MAX_EVENTS - len(receipts)):
        return sorted(receipts), 1
    return sorted(receipts + needed), 0


# ------------------------------------------------------------------ runners
def r_insert(keys, nk, valid, runner):
    vec = X.enc_factvec(keys, CAP)
    src = f"((({X.ic_insert_sorted(CAP)} {vec}) {ef(nk)}) {T if valid else F})"
    return sorted(X.dec_factvec(runner(src), CAP))


def r_observe(facts, batch, runner):
    vec = X.enc_factvec(facts, CAP)
    bs = [ef(k) for k in batch]
    l, r = _dec_pair(runner(X.ic_observe(vec, bs, CAP)))
    return sorted(X.dec_factvec(l, CAP)), int(X.dec_bool(r))


def r_accept(facts, receipts, runner):
    fv = X.enc_factvec(sorted(facts), CAP)
    rv = X.enc_factvec(sorted(receipts), RCAP)
    l, r = _dec_pair(runner(X.ic_accept(fv, rv, CAP, RCAP)))
    return sorted(X.dec_factvec(l, RCAP)), int(X.dec_bool(r))


def main():
    print("[BINDING admit-3b5f2a-build] OBSERVE + ACCEPT over sorted vectors")
    allok = True
    native_ok = True
    t0 = time.time()
    fx = mkfx(8, 4)

    def rep(ok, okn, label):
        nonlocal allok, native_ok
        allok &= ok
        tag = "PASS" if ok else "FAIL"
        if okn is False:
            native_ok = False
            tag = "FAIL(native)"
        print(f"  [{tag}] {label}")

    def gate_insert(keys, nk, valid):
        okr = (r_insert(keys, nk, valid, norm) == g_insert(keys, nk, valid))
        okn = None if SKIP_NATIVE else \
            (r_insert(keys, nk, valid, native) == g_insert(keys, nk, valid))
        return okr, okn

    def gate_observe(facts, batch):
        okr = (r_observe(facts, batch, norm) == g_observe(facts, batch))
        okn = None if SKIP_NATIVE else \
            (r_observe(facts, batch, native) == g_observe(facts, batch))
        return okr, okn

    def gate_accept(facts, receipts):
        okr = (r_accept(facts, receipts, norm) == g_accept(facts, receipts))
        okn = None if SKIP_NATIVE else \
            (r_accept(facts, receipts, native) == g_accept(facts, receipts))
        return okr, okn

    # ---- B1 insert-sorted
    ins_cases = [([10, 20], 30, True), ([10, 30], 20, True),
                 ([20, 30], 10, True), ([10, 20], 20, True),
                 ([10, 20], 30, False), ([], 15, True)]
    bad = 0
    okn_all = True
    for keys, nk, v in ins_cases:
        okr, okn = gate_insert(keys, nk, v)
        bad += (not okr)
        if okn is False:
            okn_all = False
    rep(bad == 0, (okn_all if not SKIP_NATIVE else None),
        "B1) insert-if-absent compare-shift (append/mid/front/present/inval/empty)")

    # ---- B2 observe atomic (fits + dedup + exact fill)
    obs_cases = [([10, 20], [30, 40]), ([10, 20], [20, 30]),
                 ([10, 20], [30, 30]), ([10, 20, 30, 40], [50, 60]),
                 ([], [15, 5, 25]), ([10, 20], [10, 20])]
    bad = 0
    okn_all = True
    for facts, batch in obs_cases:
        okr, okn = gate_observe(facts, batch)
        bad += (not okr)
        if okn is False:
            okn_all = False
    rep(bad == 0, (okn_all if not SKIP_NATIVE else None),
        "B2) OBSERVE atomic: distinct-new count + capacity gate + dedup")

    # ---- B3 overflow order-independent (reversed batch, same verdict)
    facts = [10, 20, 30, 40]
    batch = [50, 60, 70]                     # 3 new into 2 free -> reject all
    fwd = r_observe(facts, batch, norm)
    rev = r_observe(facts, list(reversed(batch)), norm)
    g = g_observe(facts, batch)
    okr = (fwd == rev == g and g[1] == 1)
    okn = None
    if not SKIP_NATIVE:
        fwn = r_observe(facts, batch, native)
        rvn = r_observe(facts, list(reversed(batch)), native)
        okn = (fwn == rvn == g)
    rep(okr, okn, "B3) OVERFLOW order-independent: reject whole batch either order")

    # ---- B4 collision witness (0xf6): distinct fkeys, both kept
    P1 = ("SetRotor", "sp", (16, 0, 10, 0))
    P2 = ("SetRotor", "sp", (16, 1, 5, 0))
    assert AD.pdigest(P1) == AD.pdigest(P2) == 0xf6 and P1 != P2
    f1 = X.pack_fkey(fx, 1, 1, P1)
    f2 = X.pack_fkey(fx, 1, 1, P2)
    assert f1 != f2
    g = g_observe([], [f1, f2])
    okr = (r_observe([], [f1, f2], norm) == g and len(g[0]) == 2)
    okn = None if SKIP_NATIVE else (r_observe([], [f1, f2], native) == g)
    rep(okr, okn,
        "B4) collision 0xf6 packs distinct -> OBSERVE keeps BOTH facts (disputed)")

    # ---- B5 accept: group-leader min + first-receipt authoritative + overflow
    def fk(ek, ck):
        return (ek << CK) | ck
    acc_cases = [
        ([fk(1, 50), fk(1, 20), fk(2, 5)], []),               # min-ckey leader
        ([fk(1, 50), fk(1, 20)], [fk(1, 99)]),                # already receipted
        ([fk(3, 10), fk(1, 20), fk(2, 5)], [fk(2, 7)]),       # mixed
        ([fk(6, 1), fk(7, 1)],
         [fk(1, 1), fk(2, 1), fk(3, 1), fk(4, 1), fk(5, 1)]),  # receipt overflow
    ]
    bad = 0
    okn_all = True
    for facts, receipts in acc_cases:
        okr, okn = gate_accept(facts, receipts)
        bad += (not okr)
        if okn is False:
            okn_all = False
    rep(bad == 0, (okn_all if not SKIP_NATIVE else None),
        "B5) ACCEPT: group-leader min + first-receipt + atomic receipt overflow")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[admit-3b5f2a-build] {'ALL PASS' if allok else 'FAILURES'} "
          f"-- {verdict} ({dt:.0f}s)")
    print("  [note] remaining: MAP -> EpochControl + single reducer native "
          "gate via compile_step_v6 + Film v0.7 parity.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
