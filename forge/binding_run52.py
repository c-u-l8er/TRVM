#!/usr/bin/env python3
"""binding_run52.py -- the v0.6 state-layout DE-FORK, and the backend guard.

This battery adds no field and moves no byte. It exists because the layout order
of the v0.6 encoded state used to be written down FIVE times --

    compiler._v6_fields                      (now `state_field_names`)
    the parts loop in compiler.enc_state_v6
    the parts loop in compiler.dec_state_v6  (plus a sixth: its hand-added arity)
    wrl_plan._state_layout_signature         (slay-)
    wrl_plan.backend_layout_signature        (blay-)

-- and two of the five were DEAD. Both codecs called `_v6_fields`, used none of
what it returned, and re-walked the layout by hand. A call that looks
authoritative and decides nothing is worse than no call at all: a reader
correcting `_v6_fields` would have believed the codecs followed it.

The fix is one walk, `compiler.state_layout`, that every consumer PROJECTS. The
projections legitimately differ -- a name, a neutral record, a
representation-full record. The ORDER may not. These rows are chosen so that a
de-fork which quietly changed something would fail rather than pass, and so that
a RE-fork would be caught rather than merely discouraged by a comment.

    L0   `state_field_names` is a PROJECTION of the walk ...
    L0b  ... and it holds BY CONSTRUCTION, for an arbitrary walk
    L1   both modules walk the SAME generator
    L2   the decoder's arity IS the walk's length
    L3   the codecs round-trip over it
    L4   a consistent reorder moves enc_state_v6, slay- AND blay- TOGETHER
    L5   ... and does NOT move the film: it is a representation change
    L6   a layout that disagrees with its term fails with a NAMED field
    L7   an unhandled kind is refused LOUDLY by both codecs
    L8   one pose-width rule, not three
    L9   THE GUARD: the checked-in backend fingerprints still hold
    L10  ... and a mailbox costs the world state nothing, which is what L9
         is guarding

L9 and L10 are why this file is not purely a refactor battery.
`v6_backend_fingerprints.txt` was captured before commit 5b and predicted that
mailbox worlds would MOVE off it. They did not: 5b put the mailbox in CLAIM
state, so the world-state surface never learned a mailbox exists. The file's
role inverted from prediction to guard, and until now nothing ran it. A guard
nothing runs is not a guard.

Run:  python3 binding_run52.py
"""
import hashlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))

import admit_ic as X
import compiler as C
import forge_runtime as O
import lower_e2a as LE
import wrl_ir as W
import wrl_plan as P
import binding_run3o as B3o
import binding_run47 as B47
import tools_backend_snapshot as SNAPB
from forge_state import init_state_v6
from lower_e2a import _spine

V1 = X.PROFILE_V1

_FAILED = []


def rep(ok, label):
    if callable(ok):
        ok = bool(ok())
    print("  [%s] %s" % ("PASS" if ok else "FAIL", label))
    if not ok:
        _FAILED.append(label)


FX = B3o.FX
ROT = B3o.AD.mk_claim(1, 1, ("SetRotor", "sp", (1, 2, 3, 4))) \
    if hasattr(B3o, "AD") else None


def _reset():
    LE._VAR[0] = 0
    LE._LBL[0] = 0


def _sha(b):
    if not isinstance(b, bytes):
        b = b.encode()
    return hashlib.sha256(b).hexdigest()[:16]


def walk(v):
    return list(C.state_layout(v))


def names(v):
    """The walk projected through the SAME name table `state_field_names`
    uses -- spelled out here so L0 compares two independently written
    projections rather than a function against itself."""
    return [C._STATE_FIELD_NAME[k] % n for k, n in walk(v)]


# ------------------------------------------------------------ patching
class patched(object):
    """Swap `compiler.state_layout` for the duration of a block.

    Every consumer resolves it as a module global at call time -- both codecs,
    `_v6_fields`, and `wrl_plan` through `C.state_layout` -- so one rebinding
    reaches all five former spellings. That is itself a claim this file makes:
    if any consumer had kept a private copy, these rows would not move it.
    """

    def __init__(self, fn):
        self.fn = fn

    def __enter__(self):
        self.orig = C.state_layout
        C.state_layout = self.fn
        return self

    def __exit__(self, *a):
        C.state_layout = self.orig
        return False


def _reversed_walk(v):
    """A REAL reorder: the whole walk, backwards.

    Commit 5b's version of this helper had to reverse WITHIN a group, because
    `_v6_fields` re-grouped the walk before the compiler read it and an
    arbitrary permutation would have desynchronised the compiler from the
    codecs. That constraint was the sixth spelling, and the 5c secondary
    ruling removed it: `state_field_names` projects the walk directly, so ANY
    permutation is now consistently seen by every consumer. The simplification
    of this helper is itself evidence the regrouping is gone.
    """
    return iter(list(reversed(list(_ORIG_WALK(v)))))


def _swap_pose_fault(v):
    """Emit (fault, pose) where the walk emits (pose, fault). Same arity, same
    field set, incompatible SHAPES -- a bool where a pose is expected."""
    out = []
    for kind, name in _ORIG_WALK(v):
        out.append((kind, name))
    fixed = []
    i = 0
    while i < len(out):
        if (i + 1 < len(out) and out[i][0] == "pose"
                and out[i + 1][0] == "fault"):
            fixed.append(out[i + 1])
            fixed.append(out[i])
            i += 2
        else:
            fixed.append(out[i])
            i += 1
    return iter(fixed)


def _with_bogus_kind(v):
    out = list(_ORIG_WALK(v))
    return iter(out + [("mailbox", "mb")])


_ORIG_WALK = C.state_layout


# ------------------------------------------------------------------- L0
def l0_projection():
    fields = C.state_field_names(FX)
    rep(fields == names(FX),
        "L0) `state_field_names` is a PROJECTION of `state_layout`: its %d "
        "field names are the walk's, in the walk's order" % (len(fields),))

    # L0b USED to be a tripwire on a coincidence. Commit 5b's `_v6_fields`
    # binned each field into (base, pose/fault, rotor) and concatenated, so it
    # equalled the walk only because the walk ALREADY emitted its kinds in
    # group order -- a property of the WALK, not of the projection. A future
    # walk that interleaved kinds would have silently desynchronised the
    # compiler (reading the regrouped list) from the codecs (reading the raw
    # one), and the row could only WARN about that.
    #
    # The 5c secondary ruling removed the regrouping, so the row can now assert
    # the thing itself: the projection preserves POSITION, field by field, for
    # an ARBITRARY walk. `_interleaved` is a walk that the old `_v6_fields`
    # would have reordered and this one does not, so the row fails against the
    # regrouping and passes against the direct projection.
    def _interleaved(v):
        ws = list(_ORIG_WALK(v))
        return iter(ws[::2] + ws[1::2])

    with patched(_interleaved):
        got = C.state_field_names(FX)
        want = [C._STATE_FIELD_NAME[k] % n for k, n in C.state_layout(FX)]
    rep(got == want and got != fields,
        "L0b) ... and it holds BY CONSTRUCTION, not by the walk happening to "
        "emit kinds in group order: an interleaved walk projects position-for-"
        "position (%s) instead of being re-sorted back" % (got,))


# ------------------------------------------------------------------- L1
def l1_one_generator():
    recs = P._layout_records(FX, lambda r: list(FX.pulsers[r]))
    rep([tuple(r[:2]) for r in recs] == [(k, n) for k, n in walk(FX)],
        "L1) `wrl_plan._layout_records` walks the SAME generator the codecs "
        "do: %d records, kind-and-name identical to `compiler.state_layout`"
        % (len(recs),))

    # slay- and blay- differ in exactly ONE place -- what a counter carries --
    # and that is the only place they may differ.
    slay = P._layout_records(FX, lambda r: list(FX.pulsers[r]))
    blay = P._layout_records(FX, lambda r: list(FX.counter_spec(r)))
    diff = [i for i, (a, b) in enumerate(zip(slay, blay)) if a != b]
    rep(all(slay[i][0] == "counter" for i in diff) and diff,
        "L1b) ... and `slay-`/`blay-` diverge at counters and NOWHERE else "
        "(differing indices %s, all of kind counter)" % (diff,))


# ------------------------------------------------------------------- L2
def l2_arity():
    # `enc_state_v6` emits SOURCE (`TUPN` builds a string), so the term has to
    # be reduced to an AST before it has a spine at all. `dec_state_v6` is
    # always called on a reducer's output for the same reason.
    _reset()
    t = O.ref_reduce(C.enc_state_v6(FX, init_state_v6(FX)))
    n = len(walk(FX))
    ok = True
    try:
        _spine(t, n)
    except AssertionError:
        ok = False
    over = True
    try:
        _spine(t, n + 1)
    except AssertionError:
        over = False
    rep(ok and not over,
        "L2) the encoded spine's arity IS the walk's length (%d) -- not a "
        "hand-added sum that a new field could fail to appear in" % (n,))


# ------------------------------------------------------------------- L3
def l3_roundtrip():
    st = init_state_v6(FX)
    _reset()
    back = C.dec_state_v6(FX, O.ref_reduce(C.enc_state_v6(FX, st)))
    rep(back == st,
        "L3) the codecs round-trip over the shared walk: %d fields encode and "
        "decode to the identical state dict" % (len(st),))


# ------------------------------------------------------------------- L4
def l4_reorder_moves_all():
    _reset()
    base_state = _sha(C.enc_state_v6(FX, init_state_v6(FX)))
    base_slay = P._state_layout_signature(FX)
    base_blay = P.backend_layout_signature(FX)

    with patched(_reversed_walk):
        _reset()
        r_state = _sha(C.enc_state_v6(FX, init_state_v6(FX)))
        r_slay = P._state_layout_signature(FX)
        r_blay = P.backend_layout_signature(FX)

    rep(r_state != base_state and r_slay != base_slay
        and r_blay != base_blay,
        "L4) the de-fork is LOAD-BEARING: reordering the one walk moves the "
        "encoding (%s->%s), `slay-` and `blay-` TOGETHER. Before it, the two "
        "signatures would have moved and the encoding would not -- three "
        "fingerprints disagreeing with the thing they fingerprint"
        % (base_state, r_state))

    # and the restore is exact, so nothing below inherits a patched layout
    _reset()
    rep(_sha(C.enc_state_v6(FX, init_state_v6(FX))) == base_state
        and P.backend_layout_signature(FX) == base_blay,
        "L4b) ... and the patch restores exactly, so no row below is reading "
        "a reordered layout")


# ------------------------------------------------------------------- L5
def l5_reorder_is_representation():
    """A CONSISTENT reorder must move bytes and not meaning. The state dict is
    keyed by NAME, so which offset a field sits at is representation -- and if
    the film moved, the reorder would have changed the machine instead."""
    def films():
        _reset()
        fv0 = X.enc_factvec([], B3o.CAP, V1)
        rv0 = X.enc_factvec([], B3o.RCAP, V1)
        w0 = C.enc_state_v6(FX, init_state_v6(FX))
        batches = [[], []]
        term = B3o._build_fold(batches, fv0, rv0, w0)
        dec = B3o._decode_fold(O.ref_reduce(term), len(batches))
        cl = B3o._project_claims(dec, 1)
        return [B3o._film(dec[e][0], cl[e], 1 + e) for e in range(len(dec))]

    a = films()
    with patched(_reversed_walk):
        b = films()
    rep(a == b and a,
        "L5) ... and the FILM does not move: a consistent reorder is a pure "
        "representation change, because the state dict is keyed by name. "
        "%d films byte-identical across the reorder" % (len(a),))


# ------------------------------------------------------------------- L6
def l6_named_field():
    _reset()
    t = O.ref_reduce(C.enc_state_v6(FX, init_state_v6(FX)))   # the REAL walk
    msg = ""
    with patched(_swap_pose_fault):
        try:
            C.dec_state_v6(FX, t)                     # decoded with a WRONG one
        except AssertionError as ex:
            msg = str(ex)
    # Which HALF of the swapped pair trips first is the decoder's business,
    # not this row's: reading a pose term as a bool fails just as loudly as the
    # reverse. Pinning it to `pose` would have been a row about the arbitrary
    # order of a two-element swap. What must hold is that the failure names the
    # field it was reading.
    rep("dec_state_v6: field" in msg
        and ("(pose " in msg or "(fault " in msg)
        and "does not match this layout" in msg,
        "L6) a layout that disagrees with its term fails with a NAMED field "
        "rather than a bare `assert isinstance(cur, App)` six frames down: %r"
        % (msg[:96],))

    # Why the message matters, and not only for readability: `mutate_harness`
    # scores a mutant that dies on a bare traceback as a CRASH, not a CATCH.
    # An unnamed failure here would turn mutations that should be caught into
    # mutations nothing proved anything about.
    rep(msg.startswith("dec_state_v6: field"),
        "L6b) ... and it is an AssertionError raised BY the decoder, so a "
        "mutant that breaks the layout is scored as CAUGHT rather than as a "
        "crash the harness learns nothing from")


# ------------------------------------------------------------------- L7
def l7_unhandled_kind_is_loud():
    enc_msg = dec_msg = ""
    with patched(_with_bogus_kind):
        try:
            C.enc_state_v6(FX, init_state_v6(FX))
        except AssertionError as ex:
            enc_msg = str(ex)
    try:
        C._dec_field_v6(FX, {}, None, "mailbox", "mb", __import__("binlib"))
    except AssertionError as ex:
        dec_msg = str(ex)
    rep("unhandled field kind" in enc_msg and "unhandled field kind" in dec_msg
        and "mailbox" in enc_msg and "mailbox" in dec_msg,
        "L7) BOTH codecs refuse an unhandled kind LOUDLY (enc: %r / dec: %r). "
        "Falling through silently would encode a state SHORTER than its own "
        "layout, and the decoder -- reading arity from that same layout -- "
        "would then fail somewhere unrelated"
        % (enc_msg[:44], dec_msg[:44]))


# ------------------------------------------------------------------- L8
def l8_one_width_rule():
    orbs = list(getattr(FX, "orbs", []))
    ok = True
    for o in orbs:
        s = FX.controller_of(o)
        want = FX.spinners[s][0] if s else 8
        if C.pose_width(FX, o) != want:
            ok = False
    recs = {tuple(r[:2]): r for r in P._layout_records(
        FX, lambda r: list(FX.pulsers[r]))}
    agree = all(recs[("pose", o)][2] == C.pose_width(FX, o) for o in orbs)
    rep(ok and agree and orbs,
        "L8) ONE pose-width rule: `compiler.pose_width` is what both codecs "
        "and `wrl_plan`'s layout records read for all %d orbs. A width read "
        "three ways is a field decoded at the wrong size two of them"
        % (len(orbs),))


# ------------------------------------------------------------------- L9
def l9_backend_guard():
    path = os.path.join(HERE, "v6_backend_fingerprints.txt")
    want = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                want.append(tuple(line.split()))
    got = [(n, a, b, c) for n, a, b, c in SNAPB.snapshot()]
    rep(want and [tuple(r) for r in got] == want,
        "L9) THE GUARD: all %d worlds still hash to the checked-in backend "
        "fingerprints. Until now this file was read by nothing -- a guard "
        "nothing runs is not a guard" % (len(want),))


# ------------------------------------------------------------------- L10
def l10_mailbox_costs_world_state_nothing():
    layouts = {}
    for name, mk, routes in SNAPB.WORLDS:
        prog = B47.lower(mk(), routes)
        layouts[name] = walk(prog.as_fixture_for_test())
    uniq = set(tuple(v) for v in layouts.values())
    rep(len(uniq) == 1,
        "L10) ... and what it guards: a mailbox costs the WORLD state "
        "nothing. All %d worlds -- bare, three mailbox shapes, and one that "
        "ROUTES into its mailbox and selects admit.ic.v2.mailbox53 -- walk "
        "the identical %d-field layout" % (len(layouts), len(walk(FX))))

    rep(layouts["bare"] == layouts["mailbox_routed"],
        "L10b) ... which is why `v6_backend_fingerprints.txt` predicted wrong "
        "and now guards instead: commit 5b put the mailbox in CLAIM state "
        "(run51 T1b, T8b), so this surface never learned a mailbox exists. "
        "If these rows ever move, a mailbox has been smuggled into world "
        "state and the frozen EpochControl has grown")


SECTIONS = (l0_projection, l1_one_generator, l2_arity, l3_roundtrip,
            l4_reorder_moves_all, l5_reorder_is_representation,
            l6_named_field, l7_unhandled_kind_is_loud, l8_one_width_rule,
            l9_backend_guard, l10_mailbox_costs_world_state_nothing)


def section(fn):
    try:
        return fn()
    except BaseException as ex:                       # noqa: BLE001
        if isinstance(ex, (SystemExit, KeyboardInterrupt)):
            raise
        rep(False, "%s) raised %s: %s -- the section aborted before its "
                   "remaining rows could run"
            % (fn.__name__.split("_")[0].upper(), type(ex).__name__, ex))
        return False


def main():
    t0 = time.time()
    print("[BINDING wrl-v6-defork] the v0.6 state-layout de-fork "
          "(one walk, five former spellings) + the backend guard")
    for fn in SECTIONS:
        section(fn)
    dt = int(time.time() - t0)
    print()
    if _FAILED:
        print("[wrl-v6-defork] %d FAILED (%ds)" % (len(_FAILED), dt))
        for f in _FAILED:
            print("   - %s" % f)
        return 1
    print("[wrl-v6-defork] ALL PASS -- PASS_REF_ONLY (%ds)" % (dt,))
    print("  [note] this battery adds no field and moves no byte. L4/L5 are "
          "the pair that")
    print("         make the de-fork load-bearing rather than cosmetic; L0b "
          "is now equality BY")
    print("         CONSTRUCTION rather than a coincidence; L9/L10 run the "
          "backend")
    print("         fingerprint file, which commit 5b turned from a "
          "prediction into a guard.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
