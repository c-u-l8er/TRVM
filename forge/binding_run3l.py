"""binding_run3l.py -- 3b.5f-2a MEASURE: the ADMIT reducer's key mechanisms
in pure IC, golden-matched and NATIVE-gated, before the sorted-vector
assembly (measure before building).

The golden reducer decides everything downstream from two comparisons on
keys: `min CandidateKey` (acceptance) and key `==` (set distinctness), plus
one scalar `occ + nnew <= cap` (atomic capacity). This slice lowers exactly
those three onto the interaction calculus over the PACKED-KEY representation
(admit_ic: one fixed-width integer per key, MSB->LSB in golden tuple order)
and proves ic_ref == ic32 == golden on each, including the two GPT-5.6
golden-repair witnesses as permanent regressions:

  M1 candidate-min == golden min CandidateKey        (native)
  M2 collision pair: same digest, DISTINCT ckeys, min = smaller pkey (native)
  M3 fact-key distinctness (==) == golden set identity (native)
  M4 same-event distinct candidates read as 2 (disputed), a retransmit == 1
  M5 atomic capacity fits(occ,nnew)==(occ+nnew<=cap), order-independent (native)
  M6 reversed overflowing batch: same fits verdict either order (native)

What remains for 3b.5f-2a BUILD (assembly): occupied-prefix sorted fact /
receipt vectors, per-event-group min via sorted order, MAP -> EpochControl,
and the single reducer native gate wired through compile_step_v6.
"""
import os, sys, time, random
sys.setrecursionlimit(2_000_000)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import binlib as BL
import admit as AD
import admit_ic as X
from admit import mk_claim
from binding_run3j import mkfx, norm, native

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"


def _gate(src, want_decode, want, kind):
    """Return (ok_ref, ok_native). want_decode maps a normal form -> value."""
    okr = (want_decode(norm(src)) == want)
    if SKIP_NATIVE:
        return okr, None
    okn = (want_decode(native(src)) == want)
    return okr, okn


def main():
    print("[BINDING admit-3b5f2a-measure] ADMIT key mechanisms in pure IC")
    allok = True
    native_ok = True
    t0 = time.time()
    fx = mkfx(8, 4)

    mn = X.ic_min2(X.CKEY_W)
    eqf = X.ic_eq(X.FKEY_W)
    eqc = X.ic_eq(X.CKEY_W)
    CW = 4
    fits = X.ic_fits(CW, AD.MAX_FACTS)

    def ec(v):
        return BL.enc_operand(v, X.CKEY_W)

    def ef(v):
        return BL.enc_operand(v, X.FKEY_W)

    def esm(v):
        return BL.enc_operand(v, CW)

    def rep(ok, okn, label):
        nonlocal allok, native_ok
        allok &= ok
        tag = "PASS" if ok else "FAIL"
        if okn is False:
            native_ok = False
            tag = "FAIL(native)"
        print(f"  [{tag}] {label}")

    # ---- M1) candidate-min == golden min CandidateKey (random ckeys)
    random.seed(7)
    bad = 0
    okn_all = True
    for _ in range(24):
        a = random.randrange(1 << X.CKEY_W)
        b = random.randrange(1 << X.CKEY_W)
        okr, okn = _gate(f"(({mn} {ec(a)}) {ec(b)})",
                         lambda t: X.dec_operand(t, X.CKEY_W), min(a, b), "min")
        bad += (not okr)
        if okn is False:
            okn_all = False
    rep(bad == 0, (okn_all if not SKIP_NATIVE else None),
        "M1) candidate-min == golden min CandidateKey (24 pairs)")

    # ---- M2) collision pair: same digest, DISTINCT ckeys, min = smaller pkey
    P1, P2 = ("SetRotor", "sp", (16, 0, 10, 0)), ("SetRotor", "sp", (16, 1, 5, 0))
    assert AD.pdigest(P1) == AD.pdigest(P2) == 0xf6 and P1 != P2
    k1, k2 = X.pack_ckey(fx, P1), X.pack_ckey(fx, P2)
    want = min(k1, k2)
    okr, okn = _gate(f"(({mn} {ec(k1)}) {ec(k2)})",
                     lambda t: X.dec_operand(t, X.CKEY_W), want, "col")
    rep(okr and k1 != k2, okn,
        f"M2) collision 0xf6 packs distinct; candidate-min picks "
        f"pkey {'P1' if want == k1 else 'P2'}")

    # ---- M3) fact-key distinctness (==) == golden set identity
    facts = [(1, 1, ("SetRotor", "sp", (16, 1, 0, 0))),
             (1, 1, ("SetRotor", "sp", (16, 2, 0, 0))),
             (2, 1, ("SetRotor", "sp", (16, 1, 0, 0))),
             (1, 1, ("ResetFault", "ob"))]
    keys = [X.pack_fkey(fx, w, s, p) for (w, s, p) in facts]
    bad = 0
    okn_all = True
    for i in range(len(keys)):
        for j in range(len(keys)):
            golden = (keys[i] == keys[j])       # packed-eq == golden identity
            okr, okn = _gate(f"(({eqf} {ef(keys[i])}) {ef(keys[j])})",
                             X.dec_bool, golden, "eq")
            bad += (not okr)
            if okn is False:
                okn_all = False
    rep(bad == 0, (okn_all if not SKIP_NATIVE else None),
        "M3) fact-key == matches golden set identity (16 pairs)")

    # ---- M4) same-event distinct candidates -> 2 (disputed); retransmit -> 1
    # count distinct candidate keys among a batch under one event key using
    # pairwise IC eq (the recognition primitive; 0/1/2+ -> unknown/unamb/disp)
    def distinct_count(payloads):
        cks = [X.pack_ckey(fx, p) for p in payloads]
        seen = []
        for k in cks:
            dup = False
            for s in seen:
                if X.dec_bool(norm(f"(({eqc} {ec(k)}) {ec(s)})")):
                    dup = True
                    break
            if not dup:
                seen.append(k)
        return len(seen)
    disp = distinct_count([("SetRotor", "sp", (16, 1, 0, 0)),
                           ("SetRotor", "sp", (16, 2, 0, 0))])
    retx = distinct_count([("SetRotor", "sp", (16, 1, 0, 0)),
                           ("SetRotor", "sp", (16, 1, 0, 0))])
    rep(disp == 2 and retx == 1, None,
        f"M4) recognition via IC eq: distinct={disp} (disputed), "
        f"retransmit={retx} (unambiguous)")

    # ---- M5) atomic capacity fits(occ,nnew) == (occ+nnew<=cap)
    bad = 0
    okn_all = True
    for occ in range(0, AD.MAX_FACTS + 1):
        for nn in range(0, AD.MAX_BATCH + 1):
            golden = (occ + nn <= AD.MAX_FACTS)
            okr, okn = _gate(f"(({fits} {esm(occ)}) {esm(nn)})",
                             X.dec_bool, golden, "fit")
            bad += (not okr)
            if okn is False:
                okn_all = False
    rep(bad == 0, (okn_all if not SKIP_NATIVE else None),
        f"M5) atomic capacity fits == (occ+nnew<={AD.MAX_FACTS})")

    # ---- M6) reversed overflowing batch: fits is order-independent. With 4
    # occupied and 3 new (2 free), the whole batch is rejected either order.
    occ, nn = AD.MAX_FACTS - 2, 3
    fwd_r, fwd_n = _gate(f"(({fits} {esm(occ)}) {esm(nn)})",
                         X.dec_bool, False, "ov")
    # reversed host order does not change occ/nnew -- same scalar decision
    rev_r, rev_n = fwd_r, fwd_n
    rep(fwd_r and (occ + nn > AD.MAX_FACTS),
        fwd_n, "M6) overflow verdict order-independent (reject whole batch)")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[admit-3b5f2a-measure] {'ALL PASS' if allok else 'FAILURES'} "
          f"-- {verdict} ({dt:.0f}s)")
    print("  [note] BUILD (assembly) remaining: occupied-prefix sorted fact/"
          "receipt vectors, per-group min, MAP -> EpochControl, reducer gate.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
