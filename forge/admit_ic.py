"""admit_ic.py -- IC lowering primitives for the ADMIT reducer (slice
3b.5f-2a MEASURE pass, before the full sorted-vector assembly).

The golden reducer (admit.py) decides acceptance by comparing CANDIDATE
KEYS -- CandidateKey = (payload_digest, payload_key) -- and set membership
by comparing full FACT KEYS -- (writer_id, sequence, payload_digest,
payload_key). The one representation choice the ruling left to me (the
production bridge uses full-width canonical IDs; this proof profile is a
reduced fixed-width vector) is HOW to carry those keys into pure terms.

CHOICE (measured order- and equality-faithful vs the golden Python tuple
comparison, 324/324 pairs, incl. the 0xf6 collision pair): pack each key
as ONE fixed-width unsigned integer, fields MSB->LSB in the SAME order the
golden tuple compares them. Integer `<` then IS lexicographic CandidateKey
order and integer `==` IS candidate/fact distinctness -- so `min CandidateKey`
lowers to an unsigned MIN circuit and distinctness to `dyn_case("eq")`,
both already in binlib. This module packs the keys and emits the three
load-bearing IC mechanisms; binding_run3l gates them ref==native==golden.

  ckey = digest | kind | idx | r0 | r1 | r2 | r3       (WD+WKIND+WIDX+4*WLANE)
  fkey = writer | sequence | ckey                       (2*WK + ckey width)

Field widths below are the reduced proof profile (WLANE covers the test
fixture's rotor lane width w=8). A collision under one event key differs
only in the low rotor-lane fields, so it packs to a DISTINCT ckey and stays
`disputed` -- Correction 1, now a pure-term property.
"""
import binlib as BL
from lower_e2a import _v, _lab, _spine, _dec_bool, T, F
from compiler import NOT

import admit as AD

WK = AD.WK           # writer / sequence reduced width (4)
WD = AD.WD           # payload digest reduced width (8)
WKIND = 1            # payload kind tag (SetRotor=0 | ResetFault=1)
WIDX = 3             # target index (spinner/orb), sentinel = count
WLANE = 8            # rotor lane width (reduced proof profile)

CKEY_W = WD + WKIND + WIDX + 4 * WLANE          # 44
FKEY_W = 2 * WK + CKEY_W                         # 52


# ---------------------------------------------------------------- packing
def _cat(fields):
    """fields = [(value, width), ...] MSB-first -> one unsigned integer."""
    acc = 0
    for v, wd in fields:
        v = int(v)
        assert 0 <= v < (1 << wd), "field %r overflows width %d" % (v, wd)
        acc = (acc << wd) | v
    return acc


def ckey_fields(fx, payload):
    d = AD.pdigest(payload)
    pk = AD.payload_key(fx, payload)             # (kind, idx, r0, r1, r2, r3)
    return [(d, WD), (pk[0], WKIND), (pk[1], WIDX),
            (pk[2], WLANE), (pk[3], WLANE), (pk[4], WLANE), (pk[5], WLANE)]


def pack_ckey(fx, payload):
    """Packed CandidateKey: integer `<` == golden (digest, payload_key)
    tuple order; integer `==` == golden candidate distinctness."""
    return _cat(ckey_fields(fx, payload))


def pack_fkey(fx, writer_id, sequence, payload):
    """Packed ClaimFactKey (set identity): writer | sequence | ckey."""
    return _cat([(int(writer_id), WK), (int(sequence), WK)]
                + ckey_fields(fx, payload))


# ------------------------------------------------------- IC key mechanisms
def _extract_bool(one_tuple_src):
    """A dyn_case bool result is TUPN([bool]); apply to identity to strip
    the 1-tuple wrapper and expose the bare Scott bool."""
    u = _v("u")
    return f"({one_tuple_src} λ{u}.{u})"


def ic_min2(w):
    """λA.λB. unsigned MIN of two w-bit operand tuples (LSB-first Scott
    bools). `min CandidateKey` -> ic_min2(CKEY_W) over packed ckeys. Both
    operands are consumed twice (compare + select) through fresh-label
    affine dups; T selects the FIRST branch so (a<b) picks a."""
    ltu = BL.dyn_case("ltu", w)
    A, B = _v("A"), _v("B")
    a1, a2, b1, b2 = _v("a"), _v("a"), _v("b"), _v("b")
    la, lb = _lab(), _lab()
    lt = _extract_bool(f"(({ltu} {a1}) {b1})")       # a < b
    body = f"(({lt} {a2}) {b2})"                      # (a<b) ? a : b
    return (f"λ{A}.λ{B}."
            f"!&{la}{{{a1},{a2}}}={A};"
            f"!&{lb}{{{b1},{b2}}}={B};"
            f"{body}")


def ic_eq(w):
    """λA.λB. unsigned equality of two w-bit operand tuples -> bare Scott
    bool. Fact/candidate distinctness -> ic_eq(FKEY_W)/ic_eq(CKEY_W)."""
    eq = BL.dyn_case("eq", w)
    A, B = _v("A"), _v("B")
    return f"λ{A}.λ{B}.{_extract_bool(f'(({eq} {A}) {B})')}"


def ic_fits(cw, cap):
    """λOCC.λNNEW. bare Scott bool = (occ + nnew) <= cap. The ATOMIC
    capacity predicate (Correction 2): OBSERVE/ACCEPT admit a whole batch
    only if all its new entries fit -- an order-independent scalar decision.
    occ, nnew each used once; the sum used once; no dups."""
    add = BL.dyn_case("add", cw)                     # TUPN(sum + [co, cm])
    take = BL.dyn_trunc(cw + 2, cw)                  # drop the two flags
    ltu = BL.dyn_case("ltu", cw)
    capc = BL.enc_operand(cap, cw)
    OCC, NNEW = _v("OCC"), _v("NNEW")
    summ = f"({take} (({add} {OCC}) {NNEW}))"
    lt = _extract_bool(f"(({ltu} {capc}) {summ})")   # cap < sum
    return f"λ{OCC}.λ{NNEW}.{NOT(lt)}"               # NOT(cap<sum) == sum<=cap


# ---------------------------------------------- occupied-prefix sorted vec
# A fact vector is TUPN of MAX_FACTS fixed-width fkey operands, sorted
# ASCENDING (golden _fact_key order == packed fkey `<`), empty slots = the
# ALL-ONES key (sinks to the bottom under ascending sort). `present` is
# DERIVED (key != ALL-ONES), never stored -- the Option A container.
from compiler import Alloc as _Alloc, LetChain as _LC
from lower_e2a import PAIR as _PAIR
from compiler import TUPN as _TUPN, NOT as _NOT

FKEY_ALLONES = (1 << FKEY_W) - 1


def enc_factvec(keys, cap=None):
    from admit import MAX_FACTS
    cap = cap or MAX_FACTS
    ks = sorted(keys)
    assert len(ks) <= cap
    slots = [BL.enc_operand(k, FKEY_W) for k in ks]
    slots += [BL.enc_operand(FKEY_ALLONES, FKEY_W)] * (cap - len(ks))
    return _TUPN(slots)


def dec_factvec(t, cap=None):
    from admit import MAX_FACTS
    cap = cap or MAX_FACTS
    xs = _spine(t, cap)
    out = []
    for x in xs:
        k = dec_operand(x, FKEY_W)
        if k != FKEY_ALLONES:
            out.append(k)
    return out


def ic_insert_sorted(cap):
    """λVEC.λNK.λVALID -> VEC'. Insert-if-absent of key NK into a sorted
    (ascending, ALL-ONES-padded) MAX_FACTS-slot vector by UNROLLED
    COMPARE-SHIFT (GPT-5.6's pinned mechanism). If NK is already present or
    VALID is false, the vector is returned unchanged. Assumes room (an empty
    ALL-ONES slot exists) -- the atomic capacity pre-check gates the caller,
    so the shifted-out carry is always ALL-ONES here.

    Per slot i (carry starts = NK): lt = carry < key_i; out_i = lt?carry:key_i;
    carry' = lt?key_i:carry. Duplicate guard: pres = OR_i eq(NK,key_i); when
    (pres OR NOT VALID) each out_i is muxed back to the ORIGINAL key_i."""
    ltu = BL.dyn_case("ltu", FKEY_W)
    eq = BL.dyn_case("eq", FKEY_W)
    VEC, NK, VALID = _v("VEC"), _v("NK"), _v("VLD")
    ks = [_v("k") for _ in range(cap)]
    A = _Alloc()
    L = _LC()
    # per-slot key copies: eq-present(1) + original-mux(1) + shift ltu(1) +
    # shift out(1) + shift carry(1) = 5
    kc = [A.copies(ks[i], 5) for i in range(cap)]
    # NK copies: cap present-eqs + 1 initial carry
    nkc = A.copies(NK, cap + 1)
    vc = A.copies(VALID, 1)

    def ext(one):                       # strip a dyn 1-tuple to bare bool
        u = _v("u")
        return f"({one} λ{u}.{u})"

    # present = OR_i eq(NK, key_i)
    pres = None
    for i in range(cap):
        e = ext(f"(({eq} {nkc[i]}) {kc[i][0]})")
        pres = e if pres is None else f"(({e} {T}) {pres})"   # OR
    # skip = pres OR (NOT valid)
    skip_cp = L.let(f"(({pres} {T}) {_NOT(vc[0])})", cap, "skip")

    # compare-shift, carry starts = NK
    carry = nkc[cap]                    # single source; each step re-lets 2 copies
    outs = []
    for i in range(cap):
        ki_lt, ki_out, ki_car = kc[i][2], kc[i][3], kc[i][4]
        cc = L.let(carry, 3, "car")     # carry: ltu + out + carry'
        lt = L.let(ext(f"(({ltu} {cc[0]}) {ki_lt})"), 2, "lt")   # carry<key_i
        out_i = f"(({lt[0]} {cc[1]}) {ki_out})"                  # lt?carry:key_i
        # mux back to original on skip
        muxed = f"(({skip_cp[i]} {kc[i][1]}) {out_i})"
        outs.append(muxed)
        carry = f"(({lt[1]} {ki_car}) {cc[2]})"                  # lt?key_i:carry
    body = _TUPN(outs)
    inner = "".join(A.prefix) + L.wrap(body)
    inner = f"({VEC} λ" + ".λ".join(ks) + f".{inner})"
    return f"λ{VEC}.λ{NK}.λ{VALID}.{inner}"


# ------------------------------------------------------------------ OBSERVE
# The ATOMIC batch admit (Correction 2). Count the DISTINCT-NEW fkeys in the
# batch (occupied AND not-already-in-vec AND first occurrence in the batch),
# capacity-gate the whole batch with ic_fits, and insert-all-if-fits else
# insert NONE and latch fact_capacity_fault -- arrival-order independent.
CNTW = 4                                   # count width (0..15; occ<=6, new<=4)


def _isallones(k, eq):
    u = _v("u")
    ao = BL.enc_operand(FKEY_ALLONES, FKEY_W)
    return f"((({eq} {k}) {ao}) λ{u}.{u})"     # bare bool: k == ALL-ONES


def _sum_bools(srcs, cw):
    """Fixed-width unsigned count of a list of bare Scott bools."""
    acc = BL.enc_operand(0, cw)
    for s in srcs:
        add = BL.dyn_case("add", cw)
        take = BL.dyn_trunc(cw + 2, cw)
        b_op = _TUPN([s] + [F] * (cw - 1))     # operand whose bit0 is the bool
        acc = f"({take} (({add} {acc}) {b_op}))"
    return acc


def ic_observe(vec_src, batch_srcs, cap):
    """Term computing TUP(new_fact_vec, fact_capacity_fault) for one atomic
    batch OBSERVE. vec_src is an occupied-prefix sorted fkey vector (cap
    slots); batch_srcs is a python list of encoded batch fkeys."""
    bcap = len(batch_srcs)
    eq = BL.dyn_case("eq", FKEY_W)

    VEC = _v("VEC")
    oA = _Alloc()
    vnov, vins = oA.copies(VEC, 2)             # novelty scan vs insertion pass

    ks = [_v("k") for _ in range(cap)]
    A = _Alloc()
    kc = [A.copies(ks[i], 1 + bcap) for i in range(cap)]   # present(1)+notinvec(bcap)
    L = _LC()
    ncopy = cap + bcap + 1
    bc = [L.let(batch_srcs[j], ncopy, "b") for j in range(bcap)]
    # bc[j] index map: 0=occupied, 1..cap=notinvec, cap+1..cap+bcap-1=firstinbatch,
    #                  cap+bcap=insert operand

    def orv(a, b):
        return f"(({a} {T}) {b})"              # Scott OR

    # occupied_j = NOT(batch slot j is ALL-ONES); used in novel_j + valid_j
    occ_bools = [L.let(NOT(_isallones(bc[j][0], eq)), 2, "occ") for j in range(bcap)]

    # present_i = NOT(vec slot i is ALL-ONES)   -> occ count
    pres_bools = [NOT(_isallones(kc[i][0], eq)) for i in range(cap)]
    occ_op = _sum_bools(pres_bools, CNTW)

    # novel_j = occupied_j AND notinvec_j AND firstinbatch_j
    fb_ptr = [cap + 1] * bcap                  # per-slot firstinbatch copy cursor
    novel_bools = []
    for j in range(bcap):
        def strip(one):
            u = _v("u")
            return f"({one} λ{u}.{u})"
        notinvec = None
        for i in range(cap):
            e = strip(f"(({eq} {bc[j][1 + i]}) {kc[i][1 + j]})")
            notinvec = e if notinvec is None else orv(e, notinvec)
        notinvec = NOT(notinvec) if notinvec is not None else T
        first = None
        for k in range(j):
            e = strip(f"(({eq} {bc[j][fb_ptr[j]]}) {bc[k][fb_ptr[k]]})")
            fb_ptr[j] += 1
            fb_ptr[k] += 1
            first = e if first is None else orv(e, first)
        first = NOT(first) if first is not None else T
        novel = f"(({occ_bools[j][0]} (({notinvec} {first}) {F})) {F})"
        novel_bools.append(novel)
    new_op = _sum_bools(novel_bools, CNTW)

    # fits = (occ + new) <= MAX_FACTS ; fault = NOT fits
    from admit import MAX_FACTS
    fits_raw = f"(({ic_fits(CNTW, MAX_FACTS)} {occ_op}) {new_op})"
    fits = L.let(fits_raw, bcap + 1, "fits")
    fault = NOT(fits[bcap])

    # valid_j = fits AND occupied_j ; sequential insert into vins
    cur = vins
    for j in range(bcap):
        valid = f"(({fits[j]} {occ_bools[j][1]}) {F})"
        cur = f"((({ic_insert_sorted(cap)} {cur}) {bc[j][cap + bcap]}) {valid})"
    body = _PAIR(cur, fault)

    inner = "".join(A.prefix) + L.wrap(body)
    inner = f"({vnov} λ" + ".λ".join(ks) + f".{inner})"
    body_all = "".join(oA.prefix) + inner
    return f"(λ{VEC}.{body_all} {vec_src})"


# ------------------------------------------------------------------- ACCEPT
# The accepted candidate for an event key is the MIN CandidateKey among its
# facts. Because the fact vector is sorted by ClaimFactKey = writer|seq|ckey,
# facts sharing an event key (writer|seq) are CONTIGUOUS and the FIRST of the
# run carries the min ckey -- the accepted candidate is the GROUP LEADER.
# A receipt's identity is its event key; store the accepted fact's own fkey
# (writer|seq|min-ckey) as the receipt operand (epoch/outcome are reconstructed
# at projection). First receipt authoritative -> only event keys WITHOUT an
# existing receipt are `needed`; atomic (all-or-none) with receipt_capacity_fault.
EKEY_W = 2 * WK                                # event key width (writer|seq)


def _ekey_of(fkey_src):
    """Extract the top EKEY_W bits (event key) of an fkey operand -> EKEY_W op."""
    a = [_v("a") for _ in range(FKEY_W)]
    return f"({fkey_src} λ" + ".λ".join(a) + f".{_TUPN(a[CKEY_W:])})"


def ic_accept(fvec_src, rvec_src, cap, rcap):
    """Term computing TUP(new_receipt_vec, receipt_capacity_fault) for one
    atomic ACCEPT. fvec_src = sorted fact vector (cap slots); rvec_src =
    sorted receipt vector (rcap slots of accepted-fact fkeys)."""
    from admit import MAX_EVENTS
    eqf = BL.dyn_case("eq", FKEY_W)
    eq8 = BL.dyn_case("eq", EKEY_W)

    def strip(one):
        u = _v("u")
        return f"({one} λ{u}.{u})"

    def isallones(k):
        ao = BL.enc_operand(FKEY_ALLONES, FKEY_W)
        return strip(f"(({eqf} {k}) {ao})")

    def prefeq(a, b):
        return strip(f"(({eq8} {a}) {b})")

    def orv(a, b):
        return f"(({a} {T}) {b})"

    def andv(a, b):
        return f"(({a} {b}) {F})"

    RV = _v("RV")
    oA = _Alloc()
    rscan, rins = oA.copies(RV, 2)

    fs = [_v("f") for _ in range(cap)]
    rs = [_v("r") for _ in range(rcap)]
    A = _Alloc()
    # f_i: present(1) + ekey-extract(1) + insert-operand(1)
    fc = [A.copies(fs[i], 3) for i in range(cap)]
    # r_j: present(1) + ekey-extract(1)
    rc = [A.copies(rs[j], 2) for j in range(rcap)]
    L = _LC()

    # receipt presents (each used cap times in inrcpt + 1 in rocc) and ekeys
    pr = [L.let(NOT(isallones(rc[j][0])), cap + 1, "pr") for j in range(rcap)]
    ekr = [L.let(_ekey_of(rc[j][1]), cap, "ekr") for j in range(rcap)]
    rocc = _sum_bools([pr[j][cap] for j in range(rcap)], CNTW)

    # fact ekeys: current(i>=1) + previous(i<cap-1) + inrcpt(rcap)
    ek_uses = [(1 if i >= 1 else 0) + (1 if i < cap - 1 else 0) + rcap
               for i in range(cap)]
    ekf = [L.let(_ekey_of(fc[i][1]), ek_uses[i], "ekf") for i in range(cap)]
    ekf_ptr = [0] * cap

    needed = []
    for i in range(cap):
        present_i = NOT(isallones(fc[i][0]))
        if i == 0:
            notprev = T
        else:
            cur = ekf[i][ekf_ptr[i]]; ekf_ptr[i] += 1
            prev = ekf[i - 1][ekf_ptr[i - 1]]; ekf_ptr[i - 1] += 1
            notprev = NOT(prefeq(cur, prev))
        leader = andv(present_i, notprev)
        inr = None
        for j in range(rcap):
            e = andv(pr[j][i], prefeq(ekf[i][ekf_ptr[i]], ekr[j][i]))
            ekf_ptr[i] += 1
            inr = e if inr is None else orv(e, inr)
        inr = inr if inr is not None else F
        needed.append(L.let(andv(leader, NOT(inr)), 2, "nd"))
    n_needed = _sum_bools([needed[i][0] for i in range(cap)], CNTW)

    fits_raw = f"(({ic_fits(CNTW, MAX_EVENTS)} {rocc}) {n_needed})"
    fits = L.let(fits_raw, cap + 1, "fr")
    fault = NOT(fits[cap])

    cur = rins
    for i in range(cap):
        valid = andv(fits[i], needed[i][1])
        cur = f"((({ic_insert_sorted(rcap)} {cur}) {fc[i][2]}) {valid})"
    body = _PAIR(cur, fault)

    inner = "".join(A.prefix) + L.wrap(body)
    inner = f"({rscan} λ" + ".λ".join(rs) + f".{inner})"
    inner = f"({fvec_src} λ" + ".λ".join(fs) + f".{inner})"
    body_all = "".join(oA.prefix) + inner
    return f"(λ{RV}.{body_all} {rvec_src})"


# ---------------------------------------------------------------------- MAP
# Newly-accepted Applied ops -> EpochControl = TUP(rotor_bundle, fault_bundle).
# For the proof fixture (1 configurable spinner "sp", 1 orb "ob", WLANE==w):
# Applied <=> target index valid (idx==0); a SetRotor targets sp, a ResetFault
# targets ob. rotor_bundle = TUPN([rotor_config_sp]); the committed rotor is
# the CANONICALLY-LAST (sequence, writer, digest, payload_key) accepted-Applied
# SetRotor -- an argmax by canon key = fkey with the writer/seq fields swapped.
# fault_bundle = TUPN([reset_ob]) = OR of accepted-Applied ResetFault ob.
#
# fkey bit layout (LSB-first, 52 bits): r3[0:8] r2[8:16] r1[16:24] r0[24:32]
#   idx[32:35] kind[35] digest[36:44] seq[44:48] writer[48:52].
def _kindidx_of(fkey_src):
    """-> TUP(is_setrotor, is_resetfault, valid_target)."""
    b = [_v("b") for _ in range(FKEY_W)]
    s1, s2 = _v("s"), _v("s")
    la = _lab()
    valid = f"(({NOT(b[32])} (({NOT(b[33])} {NOT(b[34])}) {F})) {F})"   # idx==0
    body = (f"!&{la}{{{s1},{s2}}}={b[35]};"
            + _TUPN([NOT(s1), s2, valid]))                # kind==0 -> SetRotor
    return f"({fkey_src} λ" + ".λ".join(b) + f".{body})"


def _pose_of(fkey_src):
    """-> enc_pose((r0,r1,r2,r3), WLANE) extracted from the fkey ckey lanes."""
    b = [_v("b") for _ in range(FKEY_W)]
    pose = _TUPN([_TUPN(b[24:32]), _TUPN(b[16:24]),
                  _TUPN(b[8:16]), _TUPN(b[0:8])])
    return f"({fkey_src} λ" + ".λ".join(b) + f".{pose})"


def _canon_of(fkey_src):
    """Canonical MAP key operand: (seq, writer, ckey) == fkey with the
    writer/seq 4-bit fields swapped -> integer `<` is golden canonical order."""
    b = [_v("b") for _ in range(FKEY_W)]
    canon = _TUPN(b[0:44] + b[48:52] + b[44:48])
    return f"({fkey_src} λ" + ".λ".join(b) + f".{canon})"


def ic_map(fvec_src, rvec_src, cap, rcap):
    """Term -> EpochControl TUP(rotor_bundle, fault_bundle) for the fixture."""
    eqf = BL.dyn_case("eq", FKEY_W)
    eq8 = BL.dyn_case("eq", EKEY_W)
    ltu = BL.dyn_case("ltu", FKEY_W)

    def strip(one):
        u = _v("u")
        return f"({one} λ{u}.{u})"

    def isallones(k):
        return strip(f"(({eqf} {k}) {BL.enc_operand(FKEY_ALLONES, FKEY_W)})")

    def prefeq(a, b):
        return strip(f"(({eq8} {a}) {b})")

    def orv(a, b):
        return f"(({a} {T}) {b})"

    def andv(a, b):
        return f"(({a} {b}) {F})"

    fs = [_v("f") for _ in range(cap)]
    rs = [_v("r") for _ in range(rcap)]
    A = _Alloc()
    # f_i: present(1)+ekey(1)+kindidx(1)+pose(1)+canon(1)
    fc = [A.copies(fs[i], 5) for i in range(cap)]
    rc = [A.copies(rs[j], 2) for j in range(rcap)]
    L = _LC()

    pr = [L.let(NOT(isallones(rc[j][0])), cap, "pr") for j in range(rcap)]
    ekr = [L.let(_ekey_of(rc[j][1]), cap, "ekr") for j in range(rcap)]

    ek_uses = [(1 if i >= 1 else 0) + (1 if i < cap - 1 else 0) + rcap
               for i in range(cap)]
    ekf = [L.let(_ekey_of(fc[i][1]), ek_uses[i], "ekf") for i in range(cap)]
    ekf_ptr = [0] * cap

    # per-slot needed_i (== ACCEPT), kind/idx tuple, canon, pose
    # each kind/idx 3-tuple is consumed once per field selection: is_set(1) +
    # is_reset(1) + valid(2, used in both eligibles) = 4 tuple copies.
    ki = [L.let(_kindidx_of(fc[i][2]), 4, "ki") for i in range(cap)]
    needed = []
    elig_set = []
    elig_rst = []
    for i in range(cap):
        present_i = NOT(isallones(fc[i][0]))
        if i == 0:
            notprev = T
        else:
            cur = ekf[i][ekf_ptr[i]]; ekf_ptr[i] += 1
            prev = ekf[i - 1][ekf_ptr[i - 1]]; ekf_ptr[i - 1] += 1
            notprev = NOT(prefeq(cur, prev))
        leader = andv(present_i, notprev)
        inr = None
        for j in range(rcap):
            e = andv(pr[j][i], prefeq(ekf[i][ekf_ptr[i]], ekr[j][i]))
            ekf_ptr[i] += 1
            inr = e if inr is None else orv(e, inr)
        inr = inr if inr is not None else F
        nd = L.let(andv(leader, NOT(inr)), 2, "nd")     # SetRotor + ResetFault
        needed.append(nd)
    # decompose each kind/idx tuple: (is_set, is_reset, valid); valid used 2x
    is_set = []
    is_rst = []
    val0 = []
    val1 = []
    for i in range(cap):
        is_set.append(f"({ki[i][0]} λa.λb.λc.a)")
        is_rst.append(f"({ki[i][1]} λa.λb.λc.b)")
        val0.append(f"({ki[i][2]} λa.λb.λc.c)")
        val1.append(f"({ki[i][3]} λa.λb.λc.c)")
    # eligible flags
    for i in range(cap):
        es = L.let(andv(needed[i][0], andv(is_set[i], val0[i])), 2, "es")
        er = andv(needed[i][1], andv(is_rst[i], val1[i]))
        elig_set.append(es)
        elig_rst.append(er)

    reset_ob = None
    for i in range(cap):
        reset_ob = elig_rst[i] if reset_ob is None else orv(elig_rst[i], reset_ob)
    reset_ob = reset_ob if reset_ob is not None else F

    # rotor argmax by canon: thread (best_canon, best_pose, have)
    canon = [L.let(_canon_of(fc[i][3]), 2, "cn") for i in range(cap)]
    pose = [_pose_of(fc[i][4]) for i in range(cap)]
    best_c = BL.enc_operand(0, FKEY_W)
    best_p = BL.enc_pose((0, 0, 0, 0), WLANE)
    have = F
    for i in range(cap):
        bc = L.let(best_c, 2, "bc")
        hv = L.let(have, 2, "hv")
        gt = strip(f"(({ltu} {bc[0]}) {canon[i][0]})")     # best < canon_i
        upd = L.let(andv(elig_set[i][0], orv(NOT(hv[0]), gt)), 2, "up")
        best_c = f"(({upd[0]} {canon[i][1]}) {bc[1]})"
        best_p = f"(({upd[1]} {pose[i]}) {best_p})"
        have = orv(elig_set[i][1], hv[1])
    have_f = L.let(have, 1, "hf")
    csr = _v("csr")
    cnc = _v("cnc")
    rotor_cfg = (f"λ{cnc}.λ{csr}."
                 f"(({have_f[0]} ({csr} {best_p})) {cnc})")
    ec = _PAIR(_TUPN([rotor_cfg]), _TUPN([reset_ob]))

    inner = "".join(A.prefix) + L.wrap(ec)
    inner = f"({rvec_src} λ" + ".λ".join(rs) + f".{inner})"
    inner = f"({fvec_src} λ" + ".λ".join(fs) + f".{inner})"
    return inner


# --------------------------------------------------------------- REDUCER
# The single-epoch ADMIT reducer as ONE term (GPT-5.6 3b.5f-2a): compose
# OBSERVE -> ACCEPT -> MAP so a single native normalization gates the whole
# step. ACCEPT and MAP both read the PRE-accept receipt vector (rv_in is pure
# data, so it is inlined into both); facts are monotone, so the post-observe
# fact vector fv' feeds ACCEPT, MAP, and the output (dup'd three ways). The
# result is TUP5(fact_vec', receipt_vec', epoch_control,
#                fact_capacity_fault, receipt_capacity_fault).
def ic_reduce(fv_in_src, rv_in_src, batch_srcs, cap, rcap):
    obs = ic_observe(fv_in_src, batch_srcs, cap)      # TUP(fv', fobs)
    fvp = _v("fvp"); fobs = _v("fobs")
    A = _Alloc()
    fv_a, fv_m, fv_o = A.copies(fvp, 3)               # accept / map / output
    # rv_in_src is read by BOTH accept and map; bind once and !&-dup so the
    # reducer is linear in its receipt input (composable when rv is a bound
    # variable from a prior epoch's output, not just a literal vector).
    rvin = _v("rvin")
    R = _Alloc()
    rv_a, rv_m = R.copies(rvin, 2)                    # accept / map
    acc = ic_accept(fv_a, rv_a, cap, rcap)            # TUP(rv', facc)
    ecc = ic_map(fv_m, rv_m, cap, rcap)              # EpochControl
    rvp = _v("rvp"); facc = _v("facc")
    out = _TUPN([fv_o, rvp, ecc, fobs, facc])
    inner = "".join(A.prefix) + "".join(R.prefix) + f"({acc} λ{rvp}.λ{facc}.{out})"
    inner = f"(λ{rvin}.{inner} {rv_in_src})"
    return f"({obs} λ{fvp}.λ{fobs}.{inner})"


# ------------------------------------------------------------- IC decoders
def dec_operand(t, w):
    return sum((1 << i) for i, b in enumerate(_spine(t, w)) if _dec_bool(b))


def dec_bool(t):
    return _dec_bool(t)
