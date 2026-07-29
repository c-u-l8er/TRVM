#!/usr/bin/env python3
"""binding_run50.py -- Slice B, Commit 5a: the profile split.

Commit 4 closed the golden layer and then MEASURED, rather than asserted, that
the native layer could not follow: `WKIND` is one bit, `Send` carries kind tag
2, and one bit does not hold three tags. The commit-4 ruling authorised a
versioned Send-capable profile and forbade widening the frozen one in place.

This battery is the split, and only the split. It does NOT give the native
reducer mailbox state -- that is the next commit, and pretending otherwise
would repeat exactly the "provably ignored at runtime" admission that commit 4
existed to end. What it does establish is the ground that commit has to stand
on:

    S1   the two profiles exist and their widths are the ruled ones
    S2   `EKEY_W` did not move, and WHY it did not have to
    S3   the v1 term surface is byte-identical across the split
    S4   v1 still REFUSES a `Send` loudly rather than truncating it
    S5   v2 packs and unpacks all three kinds losslessly
    S6   the v1 decoder is a two-way partition -- there is no third case
    S7   THE ALIASING MEASUREMENT: what an in-place widen would have done
    S8   the v2 decoder is a genuine three-way decode, and is inert on a tag
         it does not recognise
    S9   the profile is selected from SEALED CONTENT, never a caller flag
    S10  a `Send` is carried through the v2 reducer without moving the rotor

S7 is the row that changes the ruling. The ruling states that "the IC decoder
currently interprets every nonzero kind as `ResetFault`", and the direction is
wrong -- `_cat` packs MSB-first, so a widened kind field leaves the ONE bit the
v1 decoder reads at zero for a `Send`. The failure of a naive widen is not a
message misfiled as a fault-reset; it is a message body driving the rotor. The
row builds it rather than describing it, because a memo cannot go red.

Run:  python3 binding_run50.py      (TRVM_SKIP_NATIVE=1 for reference only)
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import admit as AD
import admit_ic as X
import binlib as BL
import forge_runtime as O
import wrl_canonical as WC
import wrl_ir as W
import binding_run3o as B3o
import binding_run47 as B47
import tools_ic_snapshot as SNAP
from lower_e2a import _spine, _dec_bool

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

V1, V2 = X.PROFILE_V1, X.PROFILE_V2
world2, MB1, route, lower = B47.world2, B47.MB1, B47.route, B47.lower

_FAILED = []


def rep(ok, label):
    if callable(ok):
        ok = bool(ok())
    print("  [%s] %s" % ("PASS" if ok else "FAIL", label))
    if not ok:
        _FAILED.append(label)


def kinds_of(prof, payload, fx):
    """Reduce `_kindidx_of` on a packed fkey -> the decoded flag list."""
    k = X.pack_fkey(fx, 3, 5, payload, prof)
    t = X._kindidx_of(BL.enc_operand(k, prof.FKEY_W), prof)
    return [_dec_bool(f) for f in _spine(O.ref_reduce(t), len(prof.KINDS) + 1)]


# ------------------------------------------------------------ the fixtures
FX = B3o.FX                                  # 1 spinner "sp", 1 orb "ob"


class _FxWithMailbox(object):
    """The ADMIT fixture plus a mailbox, so `payload_key` will mint a kind-2
    `Send` at a VALID target index. `mailboxes_of` returns {} for a fixture
    without the attribute -- that is the safe default (D8: an unwired mailbox
    makes every Send Rejected), and it also means a Send against the bare
    fixture would only ever exercise the sentinel path."""

    def __init__(self, fx):
        self._fx = fx
        self.mailboxes = {"mb": {}}

    def __getattr__(self, n):
        return getattr(self._fx, n)


FXM = _FxWithMailbox(FX)
SETR = ("SetRotor", "sp", (1, 2, 3, 4))
RSTF = ("ResetFault", "ob")
SEND = ("Send", "mb", (9, 8, 7, 6))


def main():
    t0 = time.time()
    print("[BINDING wrl-sliceB-c5a] the profile split "
          "(admit.ic.v1.core52 / admit.ic.v2.mailbox53)")

    # ---------------------------------------------------------------- S1
    rep(V1.name == "admit.ic.v1.core52" and V1.WKIND == 1 and V1.WIDX == 3
        and V1.CKEY_W == 44 and V1.FKEY_W == 52 and V1.EKEY_W == 8,
        "S1) the frozen profile is %s: WKIND=%d WIDX=%d CKEY_W=%d FKEY_W=%d "
        "EKEY_W=%d" % (V1.name, V1.WKIND, V1.WIDX, V1.CKEY_W, V1.FKEY_W,
                       V1.EKEY_W))

    rep(V2.name == "admit.ic.v2.mailbox53" and V2.WKIND == 2 and V2.WIDX == 3
        and V2.CKEY_W == 45 and V2.FKEY_W == 53 and V2.EKEY_W == 8,
        "S1b) the Send-capable profile is %s: WKIND=%d WIDX=%d CKEY_W=%d "
        "FKEY_W=%d EKEY_W=%d -- exactly the ruled widths"
        % (V2.name, V2.WKIND, V2.WIDX, V2.CKEY_W, V2.FKEY_W, V2.EKEY_W))

    # WKIND is the ONLY width that moves. Stated as a difference over the
    # whole record rather than as four separate equalities, so a width added
    # later cannot slip through by not having a row.
    moved = [f for f in ("WK", "WD", "WKIND", "WIDX", "WLANE")
             if getattr(V1, f) != getattr(V2, f)]
    rep(moved == ["WKIND"],
        "S1c) ... and WKIND is the ONLY primitive width that differs between "
        "the profiles (moved: %s) -- CKEY_W and FKEY_W follow from it rather "
        "than being independently chosen" % (moved,))

    # The constructor is the gate that stops a profile's kind SET and its kind
    # WIDTH from disagreeing, and it needs a row of its own. Profiles are built
    # at module scope, so if that gate ever stops firing there is no later row
    # in a position to notice: the undersized profile would simply be accepted
    # and every subsequent row would go on to measure it.
    def _undersized():
        try:
            X.Profile("undersized.probe", wkind=1, widx=3, wlane=8,
                      kinds=V2.KINDS)
            return False
        except AssertionError:
            return True

    rep(_undersized(),
        "S1d) ... and a profile whose declared kind SET does not fit its "
        "declared WKIND is refused at construction (wkind=1 carrying tag %d) "
        "-- the width and the tag set cannot silently disagree"
        % (max(V2.KINDS),))

    # ---------------------------------------------------------------- S2
    rep(V2.EKEY_W == 2 * V2.WK and V2.WK == V1.WK,
        "S2) EKEY_W stays %d because it is 2*WK and WK did not move -- the "
        "event key is writer|seq and neither field is a payload field, which "
        "is the whole reason a kind widening does not disturb it" % (V2.EKEY_W,))

    # The commit-4 refusal to pay for WKIND out of WIDX, restated against the
    # profiles themselves rather than against a memo paragraph.
    rep(V2.WIDX == V1.WIDX == 3,
        "S2b) ... and WIDX did NOT shrink to 2 to keep CKEY_W at 44 "
        "(binding_run49 R12f/R12g builds the legal six-mailbox world whose "
        "sentinel index needs WIDX >= 3)")

    # ---------------------------------------------------------------- S3
    # The ruling's condition (3). The fingerprints were captured from the tree
    # immediately BEFORE the split; there is no way to recover them afterwards,
    # so they are a checked-in file and this row is what makes them load-bearing
    # instead of decorative.
    fp_path = os.path.join(HERE, "ic_v1_term_fingerprints.txt")
    want = {}
    with open(fp_path) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                n, h = line.split()
                want[n] = h
    got = dict(SNAP.snapshot(None))
    drift = sorted(n for n in want if want[n] != got.get(n))
    rep(not drift and len(got) == len(want),
        "S3) all %d v1 term emitters are BYTE-IDENTICAL to the pre-split "
        "capture (drift: %s)" % (len(want), drift or "none"))

    # The default profile IS v1, so every existing caller that never heard of
    # profiles is still emitting the frozen terms.
    got_v1 = dict(SNAP.snapshot(V1))
    rep(all(got[n] == got_v1[n] for n in got),
        "S3b) ... and passing PROFILE_V1 explicitly emits the same bytes as "
        "passing nothing -- the default is the frozen profile, not a third one")

    rep(X.FKEY_W == V1.FKEY_W and X.CKEY_W == V1.CKEY_W
        and X.WKIND == V1.WKIND and X.EKEY_W == V1.EKEY_W
        and X.FKEY_ALLONES == V1.FKEY_ALLONES,
        "S3c) ... and the module-level names still resolve to v1, so readers "
        "that spell `X.FKEY_W` (binding_run3l/3m/3n/3o, binding_run49) did not "
        "move either")

    # ---------------------------------------------------------------- S4
    # A refusal is only worth anything if it is LOUD. Silent truncation of the
    # kind tag is the failure this whole commit exists to prevent, so the row
    # checks that v1 raises rather than that it returns something wrong.
    def _v1_send():
        try:
            X.pack_fkey(FXM, 3, 5, SEND, V1)
            return False
        except AssertionError:
            return True
    rep(_v1_send(),
        "S4) v1 REFUSES to pack a Send (kind 2 overflows WKIND=1) -- it "
        "raises rather than truncating the tag to 0 and minting a SetRotor")

    rep(AD.payload_key(FXM, SEND)[0] == AD.KIND_SEND == 2
        and max(V1.KINDS) == 1 and max(V2.KINDS) == 2,
        "S4b) ... and the tag it cannot hold is AD.KIND_SEND=%d, declared "
        "once in admit.py and read by both profiles -- the profile's kind set "
        "and the field width are derived from the same place"
        % (AD.KIND_SEND,))

    # ---------------------------------------------------------------- S5
    # The ruling's condition (1). `unpack_fkey` is new: the packer had no
    # inverse, and "kind 2 survives the round trip" is not checkable without one.
    rt_ok, rt_detail = True, []
    for pay in (SETR, RSTF, SEND):
        k = X.pack_fkey(FXM, 3, 5, pay, V2)
        v = X.unpack_fkey(k, V2)
        want_pk = AD.payload_key(FXM, pay)
        got_pk = (v["kind"], v["idx"], v["r0"], v["r1"], v["r2"], v["r3"])
        ok = (got_pk == want_pk and v["writer"] == 3 and v["sequence"] == 5
              and v["digest"] == AD.pdigest(pay))
        rt_ok = rt_ok and ok
        rt_detail.append("%s:%s" % (pay[0], "ok" if ok else "DRIFT"))
    rep(rt_ok,
        "S5) v2 pack/unpack is LOSSLESS for every declared kind, writer, "
        "sequence and digest (%s)" % (", ".join(rt_detail),))

    # Boundary values, because a field that is one bit too narrow round-trips
    # every small value correctly and fails only at the top.
    big = ("Send", "mb", (255, 255, 255, 255))
    kb = X.pack_fkey(FXM, 15, 15, big, V2)
    vb = X.unpack_fkey(kb, V2)
    rep(vb["r0"] == vb["r1"] == vb["r2"] == vb["r3"] == 255
        and vb["writer"] == 15 and vb["sequence"] == 15
        and kb < (1 << V2.FKEY_W),
        "S5b) ... including a full-width body (255,255,255,255) at writer 15 "
        "-- the reserved route writer -- and the key still fits in FKEY_W=%d"
        % (V2.FKEY_W,))

    # ---------------------------------------------------------------- S6
    f_set = kinds_of(V1, SETR, FXM)
    f_rst = kinds_of(V1, RSTF, FXM)
    rep(f_set == [True, False, True] and f_rst == [False, True, True],
        "S6) the v1 decoder reads (is_setrotor, is_resetfault, valid): "
        "SetRotor -> %s, ResetFault -> %s" % (f_set, f_rst))

    rep(f_set[0] != f_set[1] and f_rst[0] != f_rst[1],
        "S6b) ... and the two kind flags are exact COMPLEMENTS on every input "
        "-- one bit, two outputs, no third case for an unrecognised kind to "
        "fall into. That is safe with two kinds and is precisely what makes "
        "widening the field in place unsafe")

    # ---------------------------------------------------------------- S7
    # THE ALIASING MEASUREMENT, built rather than argued.
    #
    # Simulate the rejected repair: keep the v1 decoder exactly as it is, but
    # pack with a 2-bit kind field. `_cat` is MSB-first, so the kind's HIGH bit
    # lands ABOVE the bit the decoder reads and the decoder's bit stays 0.
    naive = X.Profile("naive.widen.v1+1bit", wkind=2, widx=3, wlane=8,
                      kinds=V2.KINDS)
    kn = X.pack_fkey(FXM, 3, 5, SEND, naive)
    bits = [(kn >> i) & 1 for i in range(naive.FKEY_W)]
    read_bit = V1.KIND_LO                      # the ONE bit v1 looks at
    rep(bits[read_bit] == 0 and bits[read_bit + 1] == 1,
        "S7) under a naive in-place widen a Send's kind field is bits "
        "[%d:%d] = (lo=%d, hi=%d) -- the HIGH bit carries the 2 and the bit "
        "the v1 decoder reads stays ZERO"
        % (read_bit, read_bit + 2, bits[read_bit], bits[read_bit + 1]))

    # Decode that key with the FROZEN v1 rule (kind==0 -> SetRotor) and read
    # what the reducer would have believed.
    aliased = "SetRotor" if bits[read_bit] == 0 else "ResetFault"
    lanes = tuple((kn >> (i * naive.WLANE)) & ((1 << naive.WLANE) - 1)
                  for i in (3, 2, 1, 0))
    rep(aliased == "SetRotor" and lanes == (9, 8, 7, 6),
        "S7b) ... so the v1 rule decodes that Send as a %s, and the message "
        "body lands in the POSE lanes r0..r3 = %s. The ruling states the "
        "decoder 'interprets every nonzero kind as ResetFault'; the direction "
        "is inverted, and the real failure is worse -- not a misfiled message "
        "but a rotor silently driven by a message body"
        % (aliased, lanes))

    # The sharpest statement of why this is a NAMING problem and not a sizing
    # one: the naive widen and v2 produce the IDENTICAL integer. Same width,
    # same bits, same key. Everything that differs between "rotor silently
    # driven by a message body" and "Send recognised and inert" lives in which
    # decoder is pointed at those bits -- which is exactly what a profile name
    # selects, and exactly what a caller-supplied flag would get to choose.
    rep(naive.FKEY_W == V2.FKEY_W and kn == X.pack_fkey(FXM, 3, 5, SEND, V2),
        "S7c) ... and the naive widen packs the IDENTICAL %d-bit key as v2 "
        "(0x%x). The bits were never the dangerous part -- the decoder reading "
        "them is, which is why the fix is a NAMED profile and not a width"
        % (naive.FKEY_W, kn))

    # ---------------------------------------------------------------- S8
    g_set = kinds_of(V2, SETR, FXM)
    g_rst = kinds_of(V2, RSTF, FXM)
    g_snd = kinds_of(V2, SEND, FXM)
    rep(g_set == [True, False, False, True]
        and g_rst == [False, True, False, True]
        and g_snd == [False, False, True, True],
        "S8) the v2 decoder is a genuine THREE-way decode "
        "(is_set, is_rst, is_send, valid): SetRotor -> %s, ResetFault -> %s, "
        "Send -> %s" % (g_set, g_rst, g_snd))

    rep(g_snd[0] is False,
        "S8b) ... and the row that matters: under v2 a Send is NOT a SetRotor. "
        "This is the defect S7b measured, closed")

    # An unrecognised tag. Two bits admit a 4th pattern `payload_key` never
    # mints; the decode is exclusive-but-not-exhaustive so it sets no flag.
    kx = X._cat([(3, V2.WK), (5, V2.WK), (31, V2.WD), (3, V2.WKIND),
                 (0, V2.WIDX)] + [(0, V2.WLANE)] * 4)
    t = X._kindidx_of(BL.enc_operand(kx, V2.FKEY_W), V2)
    fx_flags = [_dec_bool(f) for f in _spine(O.ref_reduce(t), len(V2.KINDS) + 1)]
    rep(not any(fx_flags[:3]) and fx_flags[3] is True,
        "S8c) ... and an UNMINTED kind tag (3) sets no kind flag at all -> %s. "
        "An op the profile does not understand is inert, not executed as some "
        "other op that it does" % (fx_flags,))

    # Out-of-fixture target still reaches the sentinel and reads INVALID.
    bogus = kinds_of(V2, ("Send", "nowhere", (1, 1, 1, 1)), FXM)
    rep(bogus[2] is True and bogus[3] is False,
        "S8d) ... and a Send to an undeclared mailbox decodes as a Send with "
        "valid_target FALSE -> %s (the sentinel index, D8: never silently "
        "Applied)" % (bogus,))

    # The decoded tuple's ARITY is tied to len(KINDS), and that is load-bearing
    # in a way worth pinning: it is why v2 cannot quietly fall back to v1's
    # one-bit decoder. That aliasing defect is not merely absent here, it is
    # UNREPRESENTABLE -- a v1-shaped decode emits three fields where v2's
    # consumers project four, so the term does not typecheck as a v2 decode
    # rather than decoding wrongly. A mutation that tries it dies on arity
    # instead of returning a plausible answer, which is the outcome to want.
    def _arity(prof, n):
        try:
            t = X._kindidx_of(BL.enc_operand(
                X.pack_fkey(FXM, 3, 5, SETR, prof), prof.FKEY_W), prof)
            _spine(O.ref_reduce(t), n)
            return True
        except AssertionError:
            return False

    rep(_arity(V1, len(V1.KINDS) + 1) and _arity(V2, len(V2.KINDS) + 1)
        and not _arity(V2, len(V1.KINDS) + 1),
        "S8e) ... and the decoded tuple's ARITY is len(KINDS)+1 under each "
        "profile (v1 -> %d, v2 -> %d), so a v1-shaped decode is not a wrong "
        "v2 decode -- it is not a v2 decode at all"
        % (len(V1.KINDS) + 1, len(V2.KINDS) + 1))

    # ---------------------------------------------------------------- S9
    free = lower(world2(""), [])
    bear = lower(world2(MB1), [route(src="p0", tag="aa", mb="mb")])
    sealed_free = WC.seal_artifact(free.artifact)
    sealed_bear = WC.seal_artifact(bear.artifact)
    rep(X.profile_for_artifact(sealed_free) is V1,
        "S9) a sealed ROUTE-FREE world selects %s -- so every world that could "
        "already be proved keeps the byte-identical terms" % (V1.name,))
    rep(X.profile_for_artifact(sealed_bear) is V2,
        "S9b) a sealed ROUTE-BEARING world selects %s -- chosen from the "
        "artifact's own declared routes, not from an argument"
        % (V2.name,))

    # The selector takes CONTENT, and content only. A raw dict is put through
    # the sealing gate rather than trusted, so there is no unsealed path in.
    rep(X.profile_for_artifact(bear.artifact) is V2
        and X.profile_for_artifact(free.artifact) is V1,
        "S9c) ... and a RAW artifact dict is SEALED before it is read, so it "
        "cannot select a profile without first passing validation")

    # A world that declares a mailbox but wires no route mints no Send, so it
    # stays on the frozen profile. That is a deliberate widening of the frozen
    # surface, not an oversight -- worth a row so a later change cannot quietly
    # move it.
    mb_only = WC.seal_artifact(lower(world2(MB1), []).artifact)
    rep(X.profile_for_artifact(mb_only) is V1,
        "S9d) ... and a world with a MAILBOX but no route stays on v1: routes "
        "are the only thing that mints a kind-2 Send, so the frozen surface "
        "stays as wide as it honestly can")

    # ---------------------------------------------------------------- S10
    # The end-to-end shape of "recognised, inert". A Send is carried through
    # the WHOLE v2 reducer alongside a SetRotor, and the rotor must land on the
    # SetRotor's pose -- unmoved by the message body sitting in the same lanes.
    batch_plain = [AD.mk_claim(1, 1, SETR)]
    batch_send = [AD.mk_claim(1, 1, SETR), AD.mk_claim(15, 1, SEND)]

    def fold(batches, prof):
        fv0 = X.enc_factvec([], B3o.CAP, prof)
        rv0 = X.enc_factvec([], B3o.RCAP, prof)
        w0 = B3o.C.enc_state_v6(FXM, B3o.init_state_v6(FXM))
        term = B3o._build_fold(batches, fv0, rv0, w0, FXM, prof)
        return B3o._decode_fold(O.ref_reduce(term), len(batches), FXM, prof)

    tr_plain = fold([batch_plain], V2)
    tr_send = fold([batch_send], V2)
    # Stated against the SetRotor's OWN pose, not merely against the Send-free
    # fold. The relative form ("same as without the Send") is what this row
    # used to say, and it is too weak by exactly one failure mode: a defect
    # that suppresses the SetRotor in BOTH folds keeps the two sides equal and
    # the row green. An absolute anchor is what makes the row a measurement.
    rep(tr_plain[0][0].get("rotor_sp") == tr_send[0][0].get("rotor_sp")
        == SETR[2],
        "S10) folding a Send ALONGSIDE a SetRotor through the v2 reducer "
        "leaves the rotor on the SetRotor's OWN pose %s (Send-free fold: %s) "
        "-- unmoved by the message body sitting in the same lanes"
        % (tr_send[0][0].get("rotor_sp"), tr_plain[0][0].get("rotor_sp")))

    rep(len(tr_send[0][1]) == 2 and len(tr_plain[0][1]) == 1,
        "S10b) ... and the Send is CARRIED, not dropped: the fact vector holds "
        "%d keys against %d without it -- it crossed the IC boundary, which is "
        "the half commit 4 measured as impossible under v1"
        % (len(tr_send[0][1]), len(tr_plain[0][1])))

    snd_keys = [k for k in tr_send[0][1]
                if X.unpack_fkey(k, V2)["kind"] == AD.KIND_SEND]
    rep(len(snd_keys) == 1
        and B3o._payload_of(B3o._unpack_fkey(snd_keys[0], V2)[3], FXM) == SEND,
        "S10c) ... and it survives the round trip through the reducer intact: "
        "the recovered payload is %s"
        % (B3o._payload_of(B3o._unpack_fkey(snd_keys[0], V2)[3], FXM)
           if snd_keys else None,))

    rep(tr_send[0][0].get("fault_ob") == tr_plain[0][0].get("fault_ob"),
        "S10d) ... and it did not trip the fault line either (%s) -- inert "
        "means inert in BOTH directions, which is what makes the next commit "
        "an addition rather than a correction"
        % (tr_send[0][0].get("fault_ob"),))

    # The ruling's condition (3) again, but at the FOLD rather than at the
    # emitted bytes. S3 pins that v1 emits the same terms as before the split;
    # this pins that route-free CONTENT means the same thing under either
    # profile, which is the property an author actually depends on. Whole
    # decoded state, not a projection of it -- a row that names three fields
    # only covers three fields, and the interesting defect is in the fourth.
    # Compared as CONTENT, not as bytes. The packed fact keys are 52 bits under
    # v1 and 53 under v2, so the raw integers differ by construction and always
    # will -- that is the widening, not a defect. What must not differ is the
    # world the fold arrives at and the payloads it carries there.
    def content(batches, prof):
        def pays(ks):
            return sorted(repr(B3o._payload_of(
                B3o._unpack_fkey(k, prof)[3], FXM)) for k in ks)

        return [(st, pays(fv), pays(rv), f0, f1)
                for st, fv, rv, f0, f1 in fold(batches, prof)]

    rep(content([batch_plain], V1) == content([batch_plain], V2),
        "S10e) ... and a route-free batch folds to the IDENTICAL state and the "
        "IDENTICAL carried payloads under BOTH profiles -- widening the kind "
        "field changed what can be said, not what the already-sayable things "
        "mean (the packed keys differ, at 52 bits against 53; the meaning "
        "does not)")

    # ------------------------------------------------------------- native
    mode = "PASS_REF_ONLY"
    if not SKIP_NATIVE:
        term = B3o._build_fold([batch_send],
                               X.enc_factvec([], B3o.CAP, V2),
                               X.enc_factvec([], B3o.RCAP, V2),
                               B3o.C.enc_state_v6(FXM,
                                                  B3o.init_state_v6(FXM)),
                               FXM, V2)
        nat = B3o._decode_fold(O.native_reduce(term), 1, FXM, V2)
        rep(nat == tr_send,
            "S11) NATIVE: the v2 route-bearing fold folds ic_ref == ic32 -- "
            "the 53-bit profile is not a paper widening, it normalizes")
        if not _FAILED:
            mode = "PASS_REF_AND_NATIVE"

    dt = int(time.time() - t0)
    print()
    if _FAILED:
        print("[wrl-sliceB-c5a] %d FAILED (%ds)" % (len(_FAILED), dt))
        for f in _FAILED:
            print("   - %s" % f)
        return 1
    print("[wrl-sliceB-c5a] ALL PASS -- %s (%ds)" % (mode, dt))
    print("  [note] the split only. The v2 reducer RECOGNISES a Send and is "
          "inert on it;")
    print("         mailbox state, delayed delivery and mailbox faults are the "
          "next commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
