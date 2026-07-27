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

# ------------------------------------------------------------- PROFILES
# There are now TWO proof profiles, because there had to be. `WKIND` was one
# bit, sized for exactly `SetRotor=0 | ResetFault=1`, and D9's `Send` carries
# kind tag 2 -- which does not fit in one bit. Widening `WKIND` in place was
# rejected: it is not merely a size change, it silently rewrites what every
# already-sealed 52-bit term MEANS.
#
# Concretely, and this is the reason the split exists rather than a widen:
# `_cat` packs MSB-first, so growing the kind field pushes its HIGH bit up to
# b[36] and leaves b[35] -- the only bit the v1 decoder reads -- at ZERO for a
# Send. A naively widened v1 would therefore decode a Send as a SetRotor, not
# as the ResetFault one might guess, and the message body would land squarely
# in the pose lanes r0..r3. The failure mode of an in-place widen is not a
# misclassified message; it is a silently moved rotor. So v1 is frozen and v2
# is a separate, named, artifact-selected profile.
#
# A profile is a passive record of widths. Every term-former takes one, and
# `PROFILE_V1`'s widths are exactly the previously-hardcoded globals, so v1
# terms are byte-identical across the split (gated: `ic_v1_term_fingerprints`).
class Profile(object):
    """Immutable width record for one IC proof profile."""

    __slots__ = ("name", "WK", "WD", "WKIND", "WIDX", "WLANE",
                 "CKEY_W", "FKEY_W", "EKEY_W", "FKEY_ALLONES", "KINDS")

    def __init__(self, name, wkind, widx, wlane, kinds):
        self.name = name
        self.WK = AD.WK                 # writer / sequence reduced width (4)
        self.WD = AD.WD                 # payload digest reduced width (8)
        self.WKIND = wkind              # payload kind tag width
        self.WIDX = widx                # target index, sentinel = count
        self.WLANE = wlane              # rotor lane width
        self.KINDS = kinds              # decoded kind tags, ascending
        self.CKEY_W = self.WD + wkind + widx + 4 * wlane
        self.FKEY_W = 2 * self.WK + self.CKEY_W
        self.EKEY_W = 2 * self.WK       # event key (writer|seq)
        self.FKEY_ALLONES = (1 << self.FKEY_W) - 1
        assert max(kinds) < (1 << wkind), (
            "profile %s: kind tag %d does not fit in WKIND=%d"
            % (name, max(kinds), wkind))

    # THE layout. `_cat` packs MSB-first, so this tuple -- read left to right
    # -- is the fkey's bit order, and it is the only place that order is
    # written down. It used to be written down three times (the packer's field
    # list, the unpacker's width table, and a set of hand-added LSB offsets),
    # which is the same forked-vocabulary defect this commit exists to fix one
    # level down: three spellings agree until they don't, and the one that
    # disagrees is a field silently read at another field's address.
    @property
    def FIELDS(self):
        return (("writer", self.WK), ("sequence", self.WK),
                ("digest", self.WD), ("kind", self.WKIND), ("idx", self.WIDX),
                ("r0", self.WLANE), ("r1", self.WLANE),
                ("r2", self.WLANE), ("r3", self.WLANE))

    @property
    def CKEY_FIELDS(self):
        """The ckey is the fkey minus its writer/sequence prefix."""
        return self.FIELDS[2:]

    def lo(self, name):
        """LSB bit offset of a named fkey field, DERIVED from `FIELDS`.

        The lanes occupy the bottom, so every offset above them moves when
        WKIND moves. Deriving them is what makes a second profile safe: a
        literal offset is right for v1 and quietly wrong for v2.
        """
        off = self.FKEY_W
        for n, w in self.FIELDS:
            off -= w
            if n == name:
                return off
        raise KeyError(name)

    @property
    def IDX_LO(self):
        return self.lo("idx")

    @property
    def KIND_LO(self):
        return self.lo("kind")

    @property
    def DIGEST_LO(self):
        return self.lo("digest")

    def __repr__(self):
        return "<Profile %s ckey=%d fkey=%d>" % (self.name, self.CKEY_W,
                                                 self.FKEY_W)


# The frozen one. Route-free worlds stay here, byte-for-byte.
PROFILE_V1 = Profile("admit.ic.v1.core52", wkind=1, widx=3, wlane=8,
                     kinds=(AD.KIND_SETROTOR, AD.KIND_RESETFAULT))

# The Send-capable one. `WKIND` 1->2 is the ONLY width that moves: CKEY_W
# 44->45 and FKEY_W 52->53 follow from it, and EKEY_W stays 8 because it is
# 2*WK and WK does not move. `WIDX` deliberately does NOT shrink to 2 to pay
# for it -- see binding_run49 R12f/R12g, which builds a legal six-mailbox
# world whose sentinel index needs WIDX >= 3.
PROFILE_V2 = Profile("admit.ic.v2.mailbox53", wkind=2, widx=3, wlane=8,
                     kinds=(AD.KIND_SETROTOR, AD.KIND_RESETFAULT, AD.KIND_SEND))

PROFILES = {PROFILE_V1.name: PROFILE_V1, PROFILE_V2.name: PROFILE_V2}


def profile_for_artifact(artifact):
    """Select the proof profile from the artifact's OWN declared semantics.

    The choice of profile changes what a packed key MEANS, so it cannot be a
    parameter the caller supplies -- a caller that picks v1 for a route-bearing
    world does not get a refusal, it gets a rotor moved by a message body. The
    only safe source is content that has already been through the sealing gate.

    So a raw dict is SEALED here rather than read: sealing validates, and a
    caller cannot shortcut it by handing over something that merely looks
    canonical. The discriminator is whether the world declares async routes,
    because routes are the only thing that mints a kind-2 `Send` -- scenario-
    authored sends are out of scope and writer 15 is reserved. A world with
    mailboxes but no routes therefore stays on v1, which is deliberate: it
    keeps the frozen byte-identical surface as wide as it can honestly be.
    """
    import wrl_canonical as WC
    if not isinstance(artifact, WC.SealedArtifact):
        artifact = WC.seal_artifact(artifact)
    return PROFILE_V2 if WC.routes_of_artifact(artifact.artifact) else PROFILE_V1


# ---------------------------------------------------------- ACCEPT RULES
# Slice B commit 5c. The proof PROFILE and the acceptance POLICY are two
# different semantic axes, and until this commit the lowering had only the
# first of them.
#
# THE DEFECT, stated exactly. `ic_accept` computed ONE ACCEPT rule -- leader,
# i.e. the minimum CandidateKey of each event key -- no matter what the sealed
# world declared. `ic_map` computed the SAME rule a second time to decide which
# operations were eligible. So a world whose seal says
#
#     semantic_policies["admit_policy_id"] = "admit_mailbox_deliver_all_v1"
#
# was reduced under `admit_candidate_min_firstreceipt_v1`. On a UNIQUE event
# key the two rules agree, which is why every row before commit 5c was green;
# on an EQUIVOCAL one they disagree completely -- golden mints no receipt and
# delivers nothing, the lowering picked a winner, minted a receipt and
# enqueued a message. A world's own routes cannot mint two candidates under one
# event key, but an authored ScenarioV1 batch is a legal run input and can, so
# the divergence was reachable rather than theoretical.
#
# WHY IT IS SELECTED FROM THE SEAL AND NOTHING ELSE. The ruling names five
# sources this must NOT be derived from -- the v2 proof profile, mailbox
# presence, `mcap`, the existence of a `Send`, and any unsealed caller option
# -- and they are forbidden for one reason each time: they CORRELATE with the
# policy today. Every one of them would work, would need no test to change, and
# would be wrong the first time a world declared the other combination. The
# only honest source is the field the world sealed.
#
# WHY A RECORD RATHER THAN A FLAG. `Profile` above is a passive record for the
# same reason: a rule is a NAME with laws, and a boolean parameter threaded
# through four call frames is a name nobody has to say out loud. The table is
# keyed by `admit`'s OWN policy ids, imported not respelled, so a policy that
# exists in golden and not here is a KeyError at selection rather than a
# silently defaulted reduction.
class AcceptRule(object):
    """Immutable record naming one ADMIT seam-1 (`resolve_candidates`) rule,
    as the IC lowering implements it.

    `reject_equivocal` is the whole of the difference between the two ruled
    policies at ACCEPT: whether an event key carrying more than one distinct
    candidate is resolved to its minimum (False -- the frozen behaviour) or
    refused outright (True). Everything downstream -- no receipt, no MAP
    eligibility, no mailbox enqueue, the retained facts -- follows from that
    one bit, exactly as it does in golden's `_resolve_candidates_unique`.
    """

    def __init__(self, policy_id, reject_equivocal):
        self.policy_id = policy_id
        self.reject_equivocal = bool(reject_equivocal)

    def __repr__(self):
        return "<AcceptRule %s reject_equivocal=%s>" % (self.policy_id,
                                                        self.reject_equivocal)


# The frozen one. Its terms, fingerprints and leader/min-candidate behaviour
# are un-moved by commit 5c and binding_run51 T7e measures that.
ACCEPT_MIN = AcceptRule(AD.ACCEPTANCE_POLICY_ID, False)
ACCEPT_UNIQUE = AcceptRule(AD.MAILBOX_POLICY_ID, True)

ACCEPT_RULES = {r.policy_id: r for r in (ACCEPT_MIN, ACCEPT_UNIQUE)}


def accept_rule_for_policy(policy_id):
    """The IC ACCEPT rule for a declared `admit_policy_id`.

    `None` selects the frozen rule, matching `admit.get_policy`, so that every
    caller written before commit 5c reduces byte-identically. An UNKNOWN id is
    refused: golden's `get_policy` refuses it too, and a lowering that quietly
    fell back to leader-min would reintroduce exactly the divergence this
    commit closes -- one layer lower and with no film to show it.
    """
    if policy_id is None:
        return ACCEPT_MIN
    if policy_id not in ACCEPT_RULES:
        raise KeyError("no IC ACCEPT rule for admit_policy_id %r; known: %s"
                       % (policy_id, sorted(ACCEPT_RULES)))
    return ACCEPT_RULES[policy_id]


def accept_rule_for_artifact(artifact):
    """Select the ACCEPT rule from the artifact's OWN sealed declaration.

    The same shape as `profile_for_artifact` and for the same reason: a raw
    dict is SEALED here rather than read, so a caller cannot shortcut the
    validating gate by handing over something that merely looks canonical.

    The policy id is fetched through `wrl_fold.admit_policy_of` -- the ONE
    spelling of "what policy did this world declare" -- rather than re-read
    from `semantic_policies` here. A second reader of one sealed field is the
    fork this whole slice keeps finding, and it is invisible until the two
    disagree.
    """
    import wrl_canonical as WC
    import wrl_fold as WF
    if not isinstance(artifact, WC.SealedArtifact):
        artifact = WC.seal_artifact(artifact)
    return accept_rule_for_policy(WF.admit_policy_of(artifact.artifact))


# Module-level names are the V1 profile's widths, unchanged. Existing readers
# (binding_run3l/3m/3n/3o, binding_run49) keep resolving `X.FKEY_W` to 52.
WK = PROFILE_V1.WK
WD = PROFILE_V1.WD
WKIND = PROFILE_V1.WKIND
WIDX = PROFILE_V1.WIDX
WLANE = PROFILE_V1.WLANE

CKEY_W = PROFILE_V1.CKEY_W                       # 44
FKEY_W = PROFILE_V1.FKEY_W                       # 52


# ---------------------------------------------------------------- packing
def _cat(fields):
    """fields = [(value, width), ...] MSB-first -> one unsigned integer."""
    acc = 0
    for v, wd in fields:
        v = int(v)
        assert 0 <= v < (1 << wd), "field %r overflows width %d" % (v, wd)
        acc = (acc << wd) | v
    return acc


def ckey_fields(fx, payload, prof=PROFILE_V1):
    d = AD.pdigest(payload)
    pk = AD.payload_key(fx, payload)             # (kind, idx, r0, r1, r2, r3)
    # Keyed by NAME, not by position: the point of driving the packer from the
    # layout table is that reordering the table reorders the packed bits, and a
    # positional zip would instead pair a value with the next field's WIDTH.
    vals = {"digest": d, "kind": pk[0], "idx": pk[1],
            "r0": pk[2], "r1": pk[3], "r2": pk[4], "r3": pk[5]}
    return [(vals[n], w) for n, w in prof.CKEY_FIELDS]


def pack_ckey(fx, payload, prof=PROFILE_V1):
    """Packed CandidateKey: integer `<` == golden (digest, payload_key)
    tuple order; integer `==` == golden candidate distinctness."""
    return _cat(ckey_fields(fx, payload, prof))


def pack_fkey(fx, writer_id, sequence, payload, prof=PROFILE_V1):
    """Packed ClaimFactKey (set identity): writer | sequence | ckey."""
    return _cat([(int(writer_id), prof.WK), (int(sequence), prof.WK)]
                + ckey_fields(fx, payload, prof))


def unpack_fkey(k, prof=PROFILE_V1):
    """Inverse of `pack_fkey` -> (writer, sequence, digest, kind, idx,
    r0, r1, r2, r3). The packer had no inverse, which was fine while every
    consumer was a comparison circuit; it is not fine now, because "kind 2
    survives the round trip" is a claim that cannot be checked without one."""
    out, off = {}, prof.FKEY_W
    for name, w in prof.FIELDS:                  # MSB-first, as `_cat` packs
        off -= w
        out[name] = (k >> off) & ((1 << w) - 1)
    assert off == 0, "fkey field widths do not tile FKEY_W"
    return out


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

FKEY_ALLONES = PROFILE_V1.FKEY_ALLONES


def enc_factvec(keys, cap=None, prof=PROFILE_V1):
    from admit import MAX_FACTS
    cap = cap or MAX_FACTS
    ks = sorted(keys)
    assert len(ks) <= cap
    slots = [BL.enc_operand(k, prof.FKEY_W) for k in ks]
    slots += [BL.enc_operand(prof.FKEY_ALLONES, prof.FKEY_W)] * (cap - len(ks))
    return _TUPN(slots)


def dec_factvec(t, cap=None, prof=PROFILE_V1):
    from admit import MAX_FACTS
    cap = cap or MAX_FACTS
    xs = _spine(t, cap)
    out = []
    for x in xs:
        k = dec_operand(x, prof.FKEY_W)
        if k != prof.FKEY_ALLONES:
            out.append(k)
    return out


def ic_insert_sorted(cap, prof=PROFILE_V1):
    """λVEC.λNK.λVALID -> VEC'. Insert-if-absent of key NK into a sorted
    (ascending, ALL-ONES-padded) MAX_FACTS-slot vector by UNROLLED
    COMPARE-SHIFT (GPT-5.6's pinned mechanism). If NK is already present or
    VALID is false, the vector is returned unchanged. Assumes room (an empty
    ALL-ONES slot exists) -- the atomic capacity pre-check gates the caller,
    so the shifted-out carry is always ALL-ONES here.

    Per slot i (carry starts = NK): lt = carry < key_i; out_i = lt?carry:key_i;
    carry' = lt?key_i:carry. Duplicate guard: pres = OR_i eq(NK,key_i); when
    (pres OR NOT VALID) each out_i is muxed back to the ORIGINAL key_i."""
    ltu = BL.dyn_case("ltu", prof.FKEY_W)
    eq = BL.dyn_case("eq", prof.FKEY_W)
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


def _isallones(k, eq, prof=PROFILE_V1):
    u = _v("u")
    ao = BL.enc_operand(prof.FKEY_ALLONES, prof.FKEY_W)
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


def ic_observe(vec_src, batch_srcs, cap, prof=PROFILE_V1):
    """Term computing TUP(new_fact_vec, fact_capacity_fault) for one atomic
    batch OBSERVE. vec_src is an occupied-prefix sorted fkey vector (cap
    slots); batch_srcs is a python list of encoded batch fkeys."""
    bcap = len(batch_srcs)
    eq = BL.dyn_case("eq", prof.FKEY_W)

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
    occ_bools = [L.let(NOT(_isallones(bc[j][0], eq, prof)), 2, "occ")
                 for j in range(bcap)]

    # present_i = NOT(vec slot i is ALL-ONES)   -> occ count
    pres_bools = [NOT(_isallones(kc[i][0], eq, prof)) for i in range(cap)]
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
        cur = f"((({ic_insert_sorted(cap, prof)} {cur}) {bc[j][cap + bcap]}) {valid})"
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
EKEY_W = PROFILE_V1.EKEY_W                     # event key width (writer|seq)


def _successor_shares_ekey(mine, nxt, next_present_src, isallones, prefeq,
                           andv):
    """THE equivocation test, written once.

    `ic_accept` and `ic_map` both compute per-slot ACCEPT eligibility, and they
    have to agree exactly -- a slot that mints no receipt must also drive no
    operation, or an equivocal Send would be refused a receipt and enqueued
    anyway. Commit 5b already carried that duplication for the leader rule;
    adding a second duplicated rule beside it is how the two drift. The
    POINTER bookkeeping stays at each call site (their `ekf` use-counts differ)
    but the RULE is this one expression.

    True when the next slot is OCCUPIED and carries the SAME event key -- i.e.
    this slot is not the last of its group, so its event key has more than one
    distinct candidate. Occupancy is part of the test rather than assumed from
    ALL-ONES padding sorting last: an event key of all-ones bits is legal
    arithmetic, and a padding slot must not be mistaken for a rival candidate.
    """
    return andv(NOT(isallones(next_present_src)), prefeq(mine, nxt))


def _ekey_of(fkey_src, prof=PROFILE_V1):
    """Extract the top EKEY_W bits (event key) of an fkey operand -> EKEY_W op."""
    a = [_v("a") for _ in range(prof.FKEY_W)]
    return f"({fkey_src} λ" + ".λ".join(a) + f".{_TUPN(a[prof.CKEY_W:])})"


def ic_accept(fvec_src, rvec_src, cap, rcap, prof=PROFILE_V1, rule=None):
    """Term computing TUP(new_receipt_vec, receipt_capacity_fault) for one
    atomic ACCEPT. fvec_src = sorted fact vector (cap slots); rvec_src =
    sorted receipt vector (rcap slots of accepted-fact fkeys).

    `rule` is the `AcceptRule` the sealed world DECLARES (commit 5c). It
    defaults to `ACCEPT_MIN`, whose emitted term is byte-identical to every
    pre-5c caller's: the additions below are all inside `if unique:` branches
    placed AFTER the statements they follow, so under the frozen rule not one
    allocation, let-binding or gensym moves.

    Under `ACCEPT_UNIQUE` a slot must also be the LAST of its event key, not
    merely the first. The fact vector is sorted and ALL-ONES padded, so an
    event key's candidates are adjacent: `leader` already means "no predecessor
    shares my event key", and the added test means "no successor does either".
    Together they are `len(candidates) == 1` -- golden's `_resolve_candidates_
    unique` -- without a pairwise scan the term cannot afford.

    The successor comparison is recomputed from FRESH ekey copies rather than
    shared with slot i+1's own `notprev`. Sharing would be cheaper by one
    equality per adjacency and would have reordered the frozen path's let
    chain, and gate 5 of the ruling says that path may not move.
    """
    from admit import MAX_EVENTS
    rule = ACCEPT_MIN if rule is None else rule
    unique = rule.reject_equivocal
    eqf = BL.dyn_case("eq", prof.FKEY_W)
    eq8 = BL.dyn_case("eq", prof.EKEY_W)

    def strip(one):
        u = _v("u")
        return f"({one} λ{u}.{u})"

    def isallones(k):
        ao = BL.enc_operand(prof.FKEY_ALLONES, prof.FKEY_W)
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
    # f_i: present(1) + ekey-extract(1) + insert-operand(1), and under the
    # equivocation-rejecting rule a SECOND present, read by slot i-1 asking
    # whether its successor is occupied at all (index 3).
    fc = [A.copies(fs[i], 3 + (1 if unique and i >= 1 else 0))
          for i in range(cap)]
    # r_j: present(1) + ekey-extract(1)
    rc = [A.copies(rs[j], 2) for j in range(rcap)]
    L = _LC()

    # receipt presents (each used cap times in inrcpt + 1 in rocc) and ekeys
    pr = [L.let(NOT(isallones(rc[j][0])), cap + 1, "pr") for j in range(rcap)]
    ekr = [L.let(_ekey_of(rc[j][1], prof), cap, "ekr") for j in range(rcap)]
    rocc = _sum_bools([pr[j][cap] for j in range(rcap)], CNTW)

    # fact ekeys: current(i>=1) + previous(i<cap-1) + inrcpt(rcap), and under
    # the unique rule one more as the successor test's `mine` (i<cap-1) and one
    # more as its `nxt` (i>=1).
    ek_uses = [(1 if i >= 1 else 0) + (1 if i < cap - 1 else 0) + rcap
               + ((1 if i < cap - 1 else 0) + (1 if i >= 1 else 0)
                  if unique else 0)
               for i in range(cap)]
    ekf = [L.let(_ekey_of(fc[i][1], prof), ek_uses[i], "ekf")
           for i in range(cap)]
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
        accept_i = andv(leader, NOT(inr))
        if unique and i < cap - 1:
            mine = ekf[i][ekf_ptr[i]]; ekf_ptr[i] += 1
            nxt = ekf[i + 1][ekf_ptr[i + 1]]; ekf_ptr[i + 1] += 1
            accept_i = andv(accept_i, NOT(_successor_shares_ekey(
                mine, nxt, fc[i + 1][3], isallones, prefeq, andv)))
        needed.append(L.let(accept_i, 2, "nd"))
    # RULING Q4 / gate: capacity is tested against the keys that actually MINT
    # a receipt, so an event key REFUSED for equivocation reserves no slot.
    # That falls out for free here -- `needed` is already the accepted set
    # under either rule -- and it is the same order golden runs in.
    n_needed = _sum_bools([needed[i][0] for i in range(cap)], CNTW)

    fits_raw = f"(({ic_fits(CNTW, MAX_EVENTS)} {rocc}) {n_needed})"
    fits = L.let(fits_raw, cap + 1, "fr")
    fault = NOT(fits[cap])

    cur = rins
    for i in range(cap):
        valid = andv(fits[i], needed[i][1])
        cur = f"((({ic_insert_sorted(rcap, prof)} {cur}) {fc[i][2]}) {valid})"
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
# fkey bit layout (LSB-first). Under v1 (52 bits) this is
#   r3[0:8] r2[8:16] r1[16:24] r0[24:32] idx[32:35] kind[35] digest[36:44]
#   seq[44:48] writer[48:52]
# and under v2 (53 bits) everything from `kind` up shifts by one. The offsets
# used to be written here as literals, which is exactly the property that made
# a second profile dangerous: a wider kind field silently reinterprets bits
# that the reader still addresses by their old numbers. They are derived now.
def _kindidx_of(fkey_src, prof=PROFILE_V1):
    """-> TUP(is_setrotor, is_resetfault[, is_send], valid_target).

    The v1 shape is a two-way partition read off a SINGLE bit: `is_setrotor`
    and `is_resetfault` are literal complements, so there is no third case for
    an unrecognised kind to land in -- every kind is one of the two, by
    construction rather than by check. That is safe only while exactly two
    kinds exist, and it is the precise mechanism by which a widened kind field
    would have decoded a `Send` as a `SetRotor`.

    The v2 shape therefore decodes each kind by matching its FULL tag, so the
    cases are mutually exclusive by construction and are NOT exhaustive: an
    unrecognised tag (2 bits admit a 4th pattern that `payload_key` never
    mints) sets no flag at all and is inert. Inert is the correct failure --
    an op the profile does not understand must not be executed as some other
    op that it does.
    """
    b = [_v("b") for _ in range(prof.FKEY_W)]
    A = _Alloc()

    # valid_target = idx == 0, as a right-folded AND over the WIDX bits.
    ix = [b[prof.IDX_LO + i] for i in range(prof.WIDX)]
    valid = NOT(ix[-1])
    for src in reversed(ix[:-1]):
        valid = f"(({NOT(src)} {valid}) {F})"

    kb = [b[prof.KIND_LO + i] for i in range(prof.WKIND)]

    if prof.WKIND == 1:
        # v1, preserved verbatim: one bit, two complementary outputs.
        s1, s2 = _v("s"), _v("s")
        la = _lab()
        body = (f"!&{la}{{{s1},{s2}}}={kb[0]};"
                + _TUPN([NOT(s1), s2, valid]))            # kind==0 -> SetRotor
        return f"({fkey_src} λ" + ".λ".join(b) + f".{body})"

    # v2+: one flag per DECLARED kind, each an equality against the whole tag.
    # Each kind bit is consumed once per declared kind, so it is dup'd first.
    kc = [A.copies(kb[i], len(prof.KINDS)) for i in range(prof.WKIND)]
    flags = []
    for n, tag in enumerate(prof.KINDS):
        lits = []
        for i in range(prof.WKIND):
            src = kc[i][n]
            lits.append(src if (tag >> i) & 1 else NOT(src))
        acc = lits[-1]
        for src in reversed(lits[:-1]):
            acc = f"(({src} {acc}) {F})"
        flags.append(acc)
    body = "".join(A.prefix) + _TUPN(flags + [valid])
    return f"({fkey_src} λ" + ".λ".join(b) + f".{body})"


def _pose_of(fkey_src, prof=PROFILE_V1):
    """-> enc_pose((r0,r1,r2,r3), WLANE) extracted from the fkey ckey lanes."""
    b = [_v("b") for _ in range(prof.FKEY_W)]
    w = prof.WLANE
    pose = _TUPN([_TUPN(b[3 * w:4 * w]), _TUPN(b[2 * w:3 * w]),
                  _TUPN(b[w:2 * w]), _TUPN(b[0:w])])
    return f"({fkey_src} λ" + ".λ".join(b) + f".{pose})"


def _canon_of(fkey_src, prof=PROFILE_V1):
    """Canonical MAP key operand: (seq, writer, ckey) == fkey with the
    writer/seq 4-bit fields swapped -> integer `<` is golden canonical order."""
    b = [_v("b") for _ in range(prof.FKEY_W)]
    c, k = prof.CKEY_W, prof.WK
    canon = _TUPN(b[0:c] + b[c + k:c + 2 * k] + b[c:c + k])
    return f"({fkey_src} λ" + ".λ".join(b) + f".{canon})"


def ic_map(fvec_src, rvec_src, cap, rcap, prof=PROFILE_V1, mcap=0, rule=None):
    """Term -> EpochControl for the fixture.

    Without a mailbox the result is TUP(rotor_bundle, fault_bundle) -- exactly
    the frozen EpochControl `compile_step_v6` consumes, byte for byte. With one
    (`mcap` > 0 under a Send-capable profile) the result is
    PAIR(EpochControl, mailbox_bundle): the frozen EpochControl UNCHANGED,
    beside a second field.

    Beside, and deliberately not inside. binding_run49's R12 measured that a
    mailbox costs the world state nothing -- a mailbox lives in CLAIM state,
    not world state -- so the world's input must not grow a third field. That
    is also what makes this commit an ADDITION rather than a correction, which
    is the whole reason commit 5a left `is_send` decoded-but-inert.

    The mailbox stage mirrors golden `_commit_deliveries`:

        canonically order accepted deliveries
            -> test MAILBOX capacity
            -> append ALL or NONE

    The stage needs a RANK, not a sort, and that is not an approximation of
    golden's `sorted(..., key=_msg_key)`. A mailbox's contents are a SET: every
    point at which golden can observe them -- `_roll_mailboxes`, `_msgs_str`,
    the ledger -- re-sorts by `_msg_key` first, and capacity is all-or-none so
    no ordering decides who is dropped. Which slot holds which message is
    therefore a packing detail with no observable consequence, and the rank is
    a one-hot counter threaded across the slots, shifted by one every time an
    eligible Send is passed.

    Slot k holds the WHOLE ClaimFactKey of the fact ranked k, not its pose. A
    message renders as `w.s.digest.payload_key->mailbox[body]`, so a bundle
    carrying only the body could not reproduce the film; the fkey already IS
    the message identity (Slice A §1 borrows ADMIT identity wholesale rather
    than inventing a message id), and `FKEY_ALLONES` is the empty slot exactly
    as it is in the fact vector.

    Capacity is ATOMIC, per Correction 2 -- never evict, never partially
    apply. So overflow is not a per-message drop: if the accepted sends exceed
    `mcap`, `mb_fault` latches and EVERY slot is suppressed. A partial append
    would be the more "helpful" behaviour and is precisely the one the golden
    model forbids.

    `rule` (commit 5c) is the sealed world's `AcceptRule`, and it must be the
    SAME one `ic_accept` was given. MAP recomputes per-slot ACCEPT eligibility
    rather than receiving it, so a rule threaded into one and not the other is
    a world where an equivocal Send is refused a receipt and enqueued anyway --
    which is the ruling's "rejected sends never reach mailbox enqueue" gate,
    failing. `ic_reduce` is what guarantees they agree; nothing else builds
    both terms.

    Note this is deliberately NOT a Send-specific refusal. ACCEPT resolves the
    event key BEFORE MAP applies operation-specific behaviour, so under the
    equivocation-rejecting policy an equivocal SetRotor is refused on exactly
    the same rule -- as it is in golden, whose `resolve_candidates` never sees
    a payload kind.
    """
    rule = ACCEPT_MIN if rule is None else rule
    unique = rule.reject_equivocal
    eqf = BL.dyn_case("eq", prof.FKEY_W)
    eq8 = BL.dyn_case("eq", prof.EKEY_W)
    ltu = BL.dyn_case("ltu", prof.FKEY_W)

    def strip(one):
        u = _v("u")
        return f"({one} λ{u}.{u})"

    def isallones(k):
        return strip(f"(({eqf} {k}) "
                     f"{BL.enc_operand(prof.FKEY_ALLONES, prof.FKEY_W)})")

    def prefeq(a, b):
        return strip(f"(({eq8} {a}) {b})")

    def orv(a, b):
        return f"(({a} {T}) {b})"

    def andv(a, b):
        return f"(({a} {b}) {F})"

    # A mailbox stage exists only when the world declares one AND the profile
    # can carry a Send. Both halves are required: `mcap` alone would mean
    # emitting a bundle a v1 term has no kind tag to fill.
    has_mb = bool(mcap) and AD.KIND_SEND in prof.KINDS

    fs = [_v("f") for _ in range(cap)]
    rs = [_v("r") for _ in range(rcap)]
    A = _Alloc()
    # f_i: present(1)+ekey(1)+kindidx(1)+pose(1)+canon(1), +1 pose for the
    # mailbox stage, which reads the SAME body lanes the rotor stage reads,
    # and under the equivocation-rejecting rule +1 present read by slot i-1's
    # successor test (the LAST index, which is why it is computed rather than
    # written down).
    _npres = 6 if has_mb else 5
    fc = [A.copies(fs[i], _npres + (1 if unique and i >= 1 else 0))
          for i in range(cap)]
    rc = [A.copies(rs[j], 2) for j in range(rcap)]
    L = _LC()

    pr = [L.let(NOT(isallones(rc[j][0])), cap, "pr") for j in range(rcap)]
    ekr = [L.let(_ekey_of(rc[j][1], prof), cap, "ekr") for j in range(rcap)]

    ek_uses = [(1 if i >= 1 else 0) + (1 if i < cap - 1 else 0) + rcap
               + ((1 if i < cap - 1 else 0) + (1 if i >= 1 else 0)
                  if unique else 0)
               for i in range(cap)]
    ekf = [L.let(_ekey_of(fc[i][1], prof), ek_uses[i], "ekf")
           for i in range(cap)]
    ekf_ptr = [0] * cap

    # per-slot needed_i (== ACCEPT), kind/idx tuple, canon, pose
    # each kind/idx tuple is consumed once per field selection: is_set(1) +
    # is_reset(1) + valid(2, used in both eligibles) = 4 tuple copies.
    # 4 tuple copies without a mailbox (is_set, is_reset, valid x2); 6 with one
    # (+ is_send, + the valid that gates it).
    ki = [L.let(_kindidx_of(fc[i][2], prof), 6 if has_mb else 4, "ki")
          for i in range(cap)]
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
        accept_i = andv(leader, NOT(inr))
        if unique and i < cap - 1:
            mine = ekf[i][ekf_ptr[i]]; ekf_ptr[i] += 1
            nxt = ekf[i + 1][ekf_ptr[i + 1]]; ekf_ptr[i + 1] += 1
            accept_i = andv(accept_i, NOT(_successor_shares_ekey(
                mine, nxt, fc[i + 1][_npres], isallones, prefeq, andv)))
        # SetRotor + ResetFault, and under a mailbox profile Send as well.
        nd = L.let(accept_i, 3 if has_mb else 2, "nd")
        needed.append(nd)
    # Decompose each kind/idx tuple. Its arity is one flag per DECLARED kind
    # plus `valid`, so it is `len(KINDS)+1` under every profile -- 3 under v1,
    # which is why the v1 selectors below still read `λa.λb.λc.<field>`.
    #
    # Commit 5a decoded `is_send` and then deliberately dropped it: a Send drove
    # neither the rotor argmax nor the fault OR, so it was inert rather than
    # aliased onto a rotor move. This commit selects it -- into the mailbox
    # stage ONLY. It still must not reach the rotor argmax or the fault OR,
    # and the battery asserts that separately rather than trusting the wiring.
    names = "abcdefgh"[:len(prof.KINDS) + 1]
    binders = "λ" + ".λ".join(names) + "."

    def sel(src, field):
        return f"({src} {binders}{names[field]})"

    i_set = prof.KINDS.index(AD.KIND_SETROTOR)
    i_rst = prof.KINDS.index(AD.KIND_RESETFAULT)
    i_val = len(prof.KINDS)
    is_set = []
    is_rst = []
    val0 = []
    val1 = []
    is_snd = []
    val2 = []
    for i in range(cap):
        is_set.append(sel(ki[i][0], i_set))
        is_rst.append(sel(ki[i][1], i_rst))
        val0.append(sel(ki[i][2], i_val))
        val1.append(sel(ki[i][3], i_val))
        if has_mb:
            is_snd.append(sel(ki[i][4], prof.KINDS.index(AD.KIND_SEND)))
            val2.append(sel(ki[i][5], i_val))
    # eligible flags
    elig_snd = []
    for i in range(cap):
        es = L.let(andv(needed[i][0], andv(is_set[i], val0[i])), 2, "es")
        er = andv(needed[i][1], andv(is_rst[i], val1[i]))
        elig_set.append(es)
        elig_rst.append(er)
        if has_mb:
            # Same acceptance gate as the control kinds -- an eligible Send is
            # a LEADER (not an equivocation, not already receipted) whose
            # target index resolves. `needed` therefore does the identical
            # work here; only the kind flag differs.
            #
            # The copy count is exact and per-slot, because a dup whose output
            # is never consumed is not free here. Every slot spends `mcap` on
            # the rank selections and 1 on the overflow test; every slot but
            # the LAST also spends (mcap+1) keeps and mcap moves on the shift.
            # The last slot performs no shift -- its result would be dead.
            n_snd = mcap + 1 + ((2 * mcap + 1) if i < cap - 1 else 0)
            elig_snd.append(L.let(andv(needed[i][2], andv(is_snd[i], val2[i])),
                                  n_snd, "eg"))

    reset_ob = None
    for i in range(cap):
        reset_ob = elig_rst[i] if reset_ob is None else orv(elig_rst[i], reset_ob)
    reset_ob = reset_ob if reset_ob is not None else F

    # rotor argmax by canon: thread (best_canon, best_pose, have)
    canon = [L.let(_canon_of(fc[i][3], prof), 2, "cn") for i in range(cap)]
    pose = [_pose_of(fc[i][4], prof) for i in range(cap)]
    best_c = BL.enc_operand(0, prof.FKEY_W)
    best_p = BL.enc_pose((0, 0, 0, 0), prof.WLANE)
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
    if not has_mb:
        ec = _PAIR(_TUPN([rotor_cfg]), _TUPN([reset_ob]))
    else:
        # ---- mailbox stage: rank by one-hot, then atomic capacity ----------
        # `oh` is a one-hot counter over 0..mcap of eligible Sends seen so far.
        # Position mcap means "already full", so a Send passed while oh[mcap]
        # is set is the one that breaks capacity -- that is the overflow test,
        # and it needs no adder and no comparator.
        EMPTY = BL.enc_operand(prof.FKEY_ALLONES, prof.FKEY_W)
        # oh[k] is consumed once as a rank selector (or, at k == mcap, as the
        # overflow test) and once as the shift's `keep`; every position but the
        # top is additionally the NEXT position's `move` source. Hence 3 copies
        # below the top and 2 at it.
        def _oh_init():
            return [L.let(T if k == 0 else F, 3 if k < mcap else 2, "oh")
                    for k in range(mcap + 1)]

        oh = _oh_init()
        mkey = [L.let(fc[i][5], mcap, "mk") for i in range(cap)]
        slots = [EMPTY] * mcap
        overflow = F
        for i in range(cap):
            eg = elig_snd[i]
            u = 0
            # slot k takes fact i's KEY when i is eligible and its rank is k
            for k in range(mcap):
                take = andv(eg[u], oh[k][0]); u += 1
                slots[k] = f"(({take} {mkey[i][k]}) {slots[k]})"
            # a Send arriving at full capacity latches overflow
            overflow = orv(andv(eg[u], oh[mcap][0]), overflow); u += 1
            if i < cap - 1:
                # shift the one-hot iff this slot was an eligible Send
                nxt = []
                for k in range(mcap + 1):
                    keep = andv(NOT(eg[u]), oh[k][1]); u += 1
                    move = (andv(eg[u], oh[k - 1][2]) if k > 0 else F)
                    if k > 0:
                        u += 1
                    nxt.append(L.let(orv(keep, move),
                                     3 if k < mcap else 2, "oh"))
                oh = nxt
            assert u == len(eg), (u, len(eg), i, mcap)
        # Atomic all-or-none: one fault latch suppresses EVERY slot. A partial
        # append is the failure mode Correction 2 names by name.
        ovf = L.let(overflow, mcap + 1, "ov")
        present = [f"(({NOT(ovf[k])} {slots[k]}) {EMPTY})" for k in range(mcap)]
        mb_bundle = _TUPN(present + [ovf[mcap]])
        ec = _PAIR(_PAIR(_TUPN([rotor_cfg]), _TUPN([reset_ob])), mb_bundle)

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
#
# Under a mailbox profile (`mcap` > 0, Send-capable) the result is TUP6, with
# the epoch's mailbox bundle as an ADDED sixth field. `epoch_control` keeps its
# frozen two-field shape in BOTH arities -- the field that grows is the
# reducer's own output, not the world's input, because that is where a mailbox
# lives (binding_run49 R12).
def ic_reduce(fv_in_src, rv_in_src, batch_srcs, cap, rcap, prof=PROFILE_V1,
              mcap=0, rule=None):
    # ONE rule object reaches BOTH stages. `ic_accept` decides who gets a
    # receipt and `ic_map` decides who drives an operation, from the same
    # per-slot eligibility computed twice; this line is the only thing making
    # the two copies say the same thing. Threading it into one and defaulting
    # the other is the exact shape of the defect commit 5c closes.
    rule = ACCEPT_MIN if rule is None else rule
    obs = ic_observe(fv_in_src, batch_srcs, cap, prof)   # TUP(fv', fobs)
    fvp = _v("fvp"); fobs = _v("fobs")
    A = _Alloc()
    fv_a, fv_m, fv_o = A.copies(fvp, 3)               # accept / map / output
    # rv_in_src is read by BOTH accept and map; bind once and !&-dup so the
    # reducer is linear in its receipt input (composable when rv is a bound
    # variable from a prior epoch's output, not just a literal vector).
    rvin = _v("rvin")
    R = _Alloc()
    rv_a, rv_m = R.copies(rvin, 2)                    # accept / map
    acc = ic_accept(fv_a, rv_a, cap, rcap, prof, rule)      # TUP(rv', facc)
    ecc = ic_map(fv_m, rv_m, cap, rcap, prof, mcap, rule)   # EpochControl
    rvp = _v("rvp"); facc = _v("facc")
    if mcap and AD.KIND_SEND in prof.KINDS:
        # ic_map handed back PAIR(EpochControl, mailbox_bundle); split it so
        # the world still receives exactly the frozen EpochControl.
        ecv, mbv = _v("ecv"), _v("mbv")
        out = f"({ecc} λ{ecv}.λ{mbv}.{_TUPN([fv_o, rvp, ecv, fobs, facc, mbv])})"
    else:
        out = _TUPN([fv_o, rvp, ecc, fobs, facc])
    inner = "".join(A.prefix) + "".join(R.prefix) + f"({acc} λ{rvp}.λ{facc}.{out})"
    inner = f"(λ{rvin}.{inner} {rv_in_src})"
    return f"({obs} λ{fvp}.λ{fobs}.{inner})"


# ------------------------------------------------------------- IC decoders
def dec_operand(t, w):
    return sum((1 << i) for i, b in enumerate(_spine(t, w)) if _dec_bool(b))


def dec_bool(t):
    return _dec_bool(t)
