#!/usr/bin/env python3
"""binding_run51.py -- Slice B, Commit 5b: the mailbox-capable native profile.

Commit 5a split the profile and stopped there, on purpose: `admit.ic.v2.mailbox53`
could CARRY a `Send` across the IC boundary and was deliberately inert on it.
The commit-5a ruling named what remained --

    "53 bits makes `Send` packable; it does not make the native reducer
     mailbox-capable"

-- and authorised exactly this: a narrowly scoped mailbox-capable profile,
proved on nine conditions, before Slice B may freeze and `~~` may be promoted
in Core §14.

WHAT THIS COMMIT ADDS, AND WHERE. Three places, and no fourth:

  * `ic_map` grows a MAILBOX STAGE and returns PAIR(EpochControl, bundle). The
    EpochControl is the frozen two-field one, unchanged -- a mailbox lives in
    CLAIM state, not world state (binding_run49 R12), so the world's input must
    not grow a field. T1 is the row that holds that line.
  * `ic_reduce` splits that pair and emits TUP6 instead of TUP5.
  * `_build_fold` threads the `mailbox_capacity_fault` LATCH across epochs and
    carries each epoch's bundle out.

The INBOX is deliberately not threaded, and that is a reading of golden rather
than an economy: `_roll_mailboxes` empties `next_inbox` at the top of EVERY
`admit_step`, so `_commit_deliveries` always appends into an empty box. Epoch
e's inbox is exactly epoch e-1's emitted bundle, and D7's lifetime law --
REPLACED, not appended -- falls out of a shift in the projection.

    T0   the ruled widths and the kind-2 codec            (conditions 1, 2)
    T1   the reducer's output grew; EpochControl did NOT
    T2   route-free v1 terms are still byte-identical     (condition 3)
    T3   enqueue at epoch N, delivery at N+1              (condition 4)
    T4   two sends to ONE mailbox both survive            (condition 5)
    T5   mailbox capacity and fault match golden          (condition 6)
    T6   the DECLARED policy and the Film v0.7 projection (condition 7)
    T7   THE BOUNDARY: where this reducer still disagrees with the declared
         policy, measured rather than asserted absent
    T8   the route-bearing twin folds film-by-film == golden   (condition 8)
    T9   NATIVE: ic_ref == ic32 == golden                      (condition 8)

Condition (9) -- reverting v2 dispatch to v1 is mutation-caught -- is `mutate51`.

T7 is this file's S7. A battery that only records what works is a brochure, and
the one thing a reader of a closure packet needs is the edge of the closure.

Run:  python3 binding_run51.py      (TRVM_SKIP_NATIVE=1 for reference only)
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
import compiler as C
import forge_runtime as O
import lower_e2a as LE
import wrl_fold as FD
import wrl_ir as W
import binding_run3o as B3o
import binding_run47 as B47
import binding_run49 as B49
import tools_ic_snapshot as SNAP
from forge_state import init_state_v6
from lower_e2a import _spine, _v

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

V1, V2 = X.PROFILE_V1, X.PROFILE_V2

_FAILED = []


def rep(ok, label):
    if callable(ok):
        ok = bool(ok())
    print("  [%s] %s" % ("PASS" if ok else "FAIL", label))
    if not ok:
        _FAILED.append(label)


# --------------------------------------------------------------- the rigs
# Two route-bearing worlds. They differ ONLY in the mailbox's declared
# capacity, because capacity is the one thing a battery cannot vary from the
# outside -- and `MAX_BATCH` is 4, so a cap-4 mailbox cannot be overflowed by
# any legal single batch. The cap-2 world is what makes condition (6)
# reachable at all rather than argued.
MB_CAP4 = B47.MB1                                   # [mailbox:mb](w=8, cap=4)
MB_CAP2 = "[mailbox:mb](w=8, cap=2){}\n"


class Rig(object):
    def __init__(self, mbline, routes=None):
        # `routes` defaults to the one route every rig below wants. It is a
        # parameter because commit 5c needs a world with a MAILBOX and NO
        # ROUTE: the acceptance policy is chosen by mailbox presence and the
        # proof profile by routes, so that world is the only one in which the
        # two axes visibly disagree, and disagreeing is the whole claim.
        self.lp = B47.lower(B47.world2(mbline),
                            [B47.route()] if routes is None else routes)
        self.artifact = self.lp.artifact
        self.fx = W.ir_to_fixture(self.artifact)
        # RULING: `runtime_seams` is normative and a caller must not
        # independently default any part. So every part comes from here, and
        # nothing in this file spells a policy id, a mailbox record, or an
        # ACCEPT rule. `self.arule` (commit 5c) is what carries the world's
        # DECLARED seam 1 into the reduction, so golden and IC refuse the same
        # event keys because they read the same sealed field -- not because
        # this harness passed matching flags to each.
        self.policy, self.mbrec, self.arule = FD.runtime_seams(self.artifact,
                                                               self.fx)
        self.mcap = AD.mailboxes_of(self.fx)["mb"][1]
        # And the profile is SELECTED, not chosen. Every fold below rides on
        # the artifact's own declared semantics, so the dispatch this battery
        # depends on is the dispatch the ruling made normative -- rather than a
        # `prof=V2` default, which is precisely the unsealed caller flag the
        # ruling forbade as a source.
        self.prof = X.profile_for_artifact(self.artifact)
        # The mailbox capacity the FOLD actually carries, which is the declared
        # one only when the selected profile can represent a `Send`. Exposed
        # rather than left inside `fold` so T7g can assert it is 0 on the world
        # whose two axes disagree -- a rule read from `mcap` would be the frozen
        # rule exactly there.
        self.mcap_used = (self.mcap if AD.KIND_SEND in self.prof.KINDS else 0)

    def fold(self, batches, prof=None, reduce=None, rule=None):
        prof = self.prof if prof is None else prof
        rule = self.arule if rule is None else rule
        reduce = O.ref_reduce if reduce is None else reduce
        fv0 = X.enc_factvec([], B3o.CAP, prof)
        rv0 = X.enc_factvec([], B3o.RCAP, prof)
        w0 = C.enc_state_v6(self.fx, init_state_v6(self.fx))
        mcap = self.mcap if AD.KIND_SEND in prof.KINDS else 0
        term = B3o._build_fold(batches, fv0, rv0, w0, self.fx, prof, mcap, rule)
        return B3o._decode_fold(reduce(term), len(batches), self.fx, prof, mcap)

    def claims(self, dec, epoch0=1):
        return B3o._project_claims(dec, epoch0, self.fx, self.prof, self.policy)

    def films(self, dec, epoch0=1):
        cl = self.claims(dec, epoch0)
        return [B3o._film(dec[e][0], cl[e], epoch0 + e, self.fx, self.mbrec,
                          self.policy)
                for e in range(len(dec))]

    def golden(self, batches, epoch0=1, **kw):
        kw.setdefault("policy", self.policy)
        kw.setdefault("mailboxes", self.mbrec)
        return B49.gfilms(self.artifact, self.fx, batches, epoch0, **kw)

    def ic_films(self, batches, reduce=None):
        return self.films(self.fold(batches, reduce=reduce))


def snd(w, s, body, mb="mb"):
    return AD.mk_claim(w, s, ("Send", mb, body))


ROT = AD.mk_claim(1, 1, ("SetRotor", "sp", (1, 2, 3, 4)))
RST = AD.mk_claim(2, 1, ("ResetFault", "ob"))


def boxes(claim, which):
    """The mailbox's `which` list, as payload bodies -- the shape a row can
    read without re-deriving the film."""
    ms = claim.get("mailbox_states", {}).get("mb", {})
    return [m["body"] for m in ms.get(which, [])]


def _arity(term, n):
    try:
        _spine(term, n)
        return True
    except AssertionError:
        return False


# The batches every section folds. Module level because the sections below are
# ISOLATED -- an exception inside one is a NAMED red row rather than a
# traceback -- and isolation must not mean each section inventing its own
# trajectory.
B3 = [[snd(15, 0, (5, 5, 5, 5))], [], []]
TWO = [[snd(15, 0, (1, 1, 1, 1)), snd(15, 1, (2, 2, 2, 2))], []]
AT_CAP = [[snd(15, 0, (1, 0, 0, 0)), snd(15, 1, (2, 0, 0, 0))]]
OVER = [[snd(15, i, (i, 0, 0, 0)) for i in range(3)]]
RESUME = [[snd(15, i, (i, 0, 0, 0)) for i in range(3)],
          [snd(15, 9, (7, 7, 7, 7))], []]
EQUIV = [[snd(15, 0, (1, 1, 1, 1)), snd(15, 0, (2, 2, 2, 2))]]

S = {}


def section(fn):
    """Run one section; an exception becomes a NAMED red row, not a traceback.

    This is `binding_run49`'s discipline, here for a reason specific to this
    commit: `mutate51` scores a mutant that dies before the rows execute as
    having proved NOTHING. A battery that aborts on the first malformed
    reduction cannot be mutation-tested at all, and the mailbox stage is
    exactly the kind of code whose defects are malformed reductions.
    """
    try:
        return fn()
    except BaseException as ex:                       # noqa: BLE001
        if isinstance(ex, (SystemExit, KeyboardInterrupt)):
            raise
        rep(False, "%s) raised %s: %s -- the section aborted before its "
                   "remaining rows could run"
            % (fn.__name__.split("_")[0].upper(), type(ex).__name__, ex))
        return False


# ------------------------------------------------------------------- T0
# Conditions (1) and (2), restated here rather than cited, so a reader of THIS
# packet does not have to hold binding_run50 open to know the profile it is
# about is the profile that was ruled.
def t0_profile_and_codec():
    S["r4"] = Rig(MB_CAP4)
    S["r2"] = Rig(MB_CAP2)
    rep(V2.name == "admit.ic.v2.mailbox53" and V2.WKIND == 2
        and V2.CKEY_W == 45 and V2.FKEY_W == 53 and V2.EKEY_W == 8,
        "T0) the profile under test is %s: WKIND=%d CKEY_W=%d FKEY_W=%d "
        "EKEY_W=%d -- the ruled widths, unmoved by this commit"
        % (V2.name, V2.WKIND, V2.CKEY_W, V2.FKEY_W, V2.EKEY_W))

    pay = ("Send", "mb", (9, 8, 7, 6))
    k = X.pack_fkey(S["r4"].fx, 15, 3, pay, V2)
    v = X.unpack_fkey(k, V2)
    rep(v["kind"] == AD.KIND_SEND and v["writer"] == 15 and v["sequence"] == 3
        and (v["r0"], v["r1"], v["r2"], v["r3"]) == (9, 8, 7, 6)
        and v["digest"] == AD.pdigest(pay),
        "T0b) ... and the kind-2 codec is still lossless end to end "
        "(w15.s3 %s -> 0x%x -> back)" % (pay[2], k))


# ------------------------------------------------------------------- T1
# The line this commit must not cross. `compile_step_v6` consumes the
# EpochControl; if the mailbox had been added as a THIRD field there, every
# mailbox-bearing world would be stepping a world state that a mailbox-free
# world does not, and binding_run49's R12 measurement -- a mailbox costs the
# world state nothing -- would have quietly stopped being true.
def t1_epoch_control():
    r2 = S["r2"]
    ev = X.enc_factvec([], B3o.CAP, V2)
    ec_free = O.ref_reduce(X.ic_map(ev, X.enc_factvec([], B3o.RCAP, V2),
                                    B3o.CAP, B3o.RCAP, V2, 0))
    rep(_arity(ec_free, 2) and not _arity(ec_free, 3),
        "T1) with no mailbox the reducer's MAP emits the frozen 2-field "
        "EpochControl and nothing else")

    ec_mb = O.ref_reduce(X.ic_map(ev, X.enc_factvec([], B3o.RCAP, V2),
                                  B3o.CAP, B3o.RCAP, V2, r2.mcap))
    pair = _spine(ec_mb, 2) if _arity(ec_mb, 2) else None
    rep(pair is not None and _arity(pair[0], 2) and not _arity(pair[0], 3)
        and _arity(pair[1], r2.mcap + 1),
        "T1b) ... and WITH one it emits PAIR(EpochControl, bundle): the "
        "EpochControl still has exactly 2 fields and the bundle has %d "
        "(%d slots + the overflow bit). The field that grew is the REDUCER's "
        "output, not the WORLD's input" % (r2.mcap + 1, r2.mcap))

    v2row = r2.fold([[snd(15, 0, (1, 1, 1, 1))]])[0]
    v1row = r2.fold([[ROT]], prof=V1)[0]
    rep(len(v2row) == 7 and len(v1row) == 5,
        "T1c) ... which the fold reads as a SIXTH reducer field: a v2 "
        "mailbox row decodes %d fields against v1's %d, and the extra two are "
        "the epoch's bundle and the carried latch" % (len(v2row), len(v1row)))


# ------------------------------------------------------------------- T2
# Condition (3). This commit edited `ic_map` and `ic_reduce`, which are the two
# emitters most likely to have moved, so the pre-split capture is re-checked
# here and not merely inherited from binding_run50.
def t2_frozen_surface():
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
        "T2) all %d v1 term emitters are STILL byte-identical to the "
        "pre-split capture after the mailbox stage landed (drift: %s)"
        % (len(want), drift or "none"))

    # The fingerprint file covers the emitters; it does not cover the FOLD,
    # which this commit also edited. The fold has no pre-commit capture to
    # compare against, so the statement available is the one that matters: the
    # new parameter's default is inert, character for character.
    def _fold_term(**kw):
        LE._VAR[0] = 0
        LE._LBL[0] = 0
        return B3o._build_fold(
            [[ROT], [RST]], X.enc_factvec([], B3o.CAP, V1),
            X.enc_factvec([], B3o.RCAP, V1),
            C.enc_state_v6(B3o.FX, init_state_v6(B3o.FX)), **kw)

    rep(_fold_term() == _fold_term(mcap=0) == _fold_term(fx=None, prof=None,
                                                         mcap=0),
        "T2b) ... and a v1 fold emits the CHARACTER-identical term whether "
        "`mcap` is defaulted, passed as 0, or passed alongside the other two "
        "defaults -- the new parameter is inert on every pre-existing caller")

    # GATE (5) of the commit-5c ruling: `admit_candidate_min_firstreceipt_v1`
    # must not move. T2 above already pins the thirteen v1 EMITTERS against the
    # pre-split capture, and `SNAP.snapshot` calls them with no rule -- so that
    # row is now also the statement that the DEFAULT rule is the frozen one.
    # What it cannot say is that the rule parameter is inert when passed
    # EXPLICITLY, which is how every 5c caller passes it. Both halves here, and
    # the second is what keeps the first from being vacuous: an inertness claim
    # that would still hold if the parameter did nothing at all proves nothing.
    frozen = _fold_term()
    rep(frozen == _fold_term(rule=X.ACCEPT_MIN)
        and frozen == _fold_term(rule=None)
        and _fold_term(rule=X.ACCEPT_UNIQUE) != frozen,
        "T2c) ... and so is the new ACCEPT rule: naming the frozen "
        "first-receipt rule EXPLICITLY emits the character-identical term, "
        "while naming the other one does not -- so the parameter is inert by "
        "DEFAULT rather than inert by being ignored")

    def _acc(**kw):
        LE._VAR[0] = 0
        LE._LBL[0] = 0
        return X.ic_accept(_v("fv"), _v("rv"), B3o.CAP, B3o.RCAP, V1, **kw)

    def _mp(**kw):
        LE._VAR[0] = 0
        LE._LBL[0] = 0
        return X.ic_map(_v("fv"), _v("rv"), B3o.CAP, B3o.RCAP, V1, **kw)

    rep(_acc() == _acc(rule=X.ACCEPT_MIN) != _acc(rule=X.ACCEPT_UNIQUE)
        and _mp() == _mp(rule=X.ACCEPT_MIN) != _mp(rule=X.ACCEPT_UNIQUE),
        "T2d) ... at BOTH stages. `ic_accept` and `ic_map` each recompute "
        "per-slot eligibility independently, so a rule threaded into one and "
        "not the other would refuse a receipt and enqueue the message anyway "
        "-- the row is a pair because the defect it guards is a pair")

    # And the profile every row below folds under is SELECTED from the sealed
    # world, not supplied. This is the ruling's "never from an unsealed caller
    # flag" made load-bearing rather than merely honoured: if the dispatch were
    # reverted to v1, these rigs would not quietly keep working -- they would
    # stop being able to represent the `Send` they are about.
    rep(S["r4"].prof is V2 and S["r2"].prof is V2
        and X.profile_for_artifact(
            B47.lower(B47.world2(""), []).artifact) is V1,
        "T2e) ... and every fold below rides on `profile_for_artifact`: the "
        "route-bearing rigs SELECT %s from their sealed world and a "
        "route-free one selects %s" % (S["r4"].prof.name, V1.name))


# ------------------------------------------------------------------- T3
# CONDITION (4). One Send observed at epoch 1, three epochs folded.
def t3_enqueue_and_delivery():
    cl = S["r4"].claims(S["r4"].fold(B3))
    seq = [(boxes(c, "inbox"), boxes(c, "next_inbox")) for c in cl]
    rep(seq == [([], [(5, 5, 5, 5)]), ([(5, 5, 5, 5)], []), ([], [])],
        "T3) enqueue at epoch N, delivery at N+1: (inbox, next_inbox) runs "
        "%s -- the message is enqueued in epoch 1, becomes OBSERVABLE in "
        "epoch 2, and is gone in epoch 3" % (seq,))

    rep(seq[2] == ([], []),
        "T3b) ... and gone is D7's lifetime law and not an accident: the "
        "inbox is REPLACED at each commit, not appended to, so a message "
        "delivered in period k+1 is absent at the following boundary whether "
        "or not anything observed it")

    ldg = [[e[0] for e in c.get("ledger_entries", [])] for c in cl]
    rep(ldg == [["MailboxEnqueue"], ["MailboxDeliver"], []],
        "T3c) ... and the EventLedger says the same thing twice, once per "
        "boundary: %s" % (ldg,))


# ------------------------------------------------------------------- T4
# CONDITION (5). Two sends, ONE mailbox, one epoch, DIFFERENT event keys.
def t4_two_sends():
    r4 = S["r4"]
    cl2 = r4.claims(r4.fold(TWO))
    rep(sorted(boxes(cl2[0], "next_inbox")) == [(1, 1, 1, 1), (2, 2, 2, 2)]
        and sorted(boxes(cl2[1], "inbox")) == [(1, 1, 1, 1), (2, 2, 2, 2)],
        "T4) two sends to ONE mailbox under different event keys BOTH "
        "survive: next_inbox %s at epoch 1, inbox %s at epoch 2"
        % (sorted(boxes(cl2[0], "next_inbox")),
           sorted(boxes(cl2[1], "inbox"))))

    # The row that makes T4 a measurement of the DECLARED policy rather than
    # of arithmetic. binding_run49 R7g proved the two policies differ on
    # exactly this shape; here the reducer is shown to have landed on the
    # declared side of that difference, which is the only side that is right.
    dflt = r4.golden(TWO, policy=None)
    decl = r4.golden(TWO)
    rep(dflt != decl and r4.films(r4.fold(TWO)) == decl,
        "T4b) ... and this is the DECLARED policy and not a coincidence: the "
        "same batch under `admit_candidate_min_firstreceipt_v1` collapses to "
        "one message (R7g), and the fold matches the DECLARED "
        "`admit_mailbox_deliver_all_v1` film, not the default one")


# ------------------------------------------------------------------- T5
# CONDITION (6), on the cap-2 world. Three shapes: at capacity, over it, and
# over-then-clean.
def t5_capacity():
    r2 = S["r2"]
    c_at = r2.claims(r2.fold(AT_CAP))
    rep(len(boxes(c_at[0], "next_inbox")) == r2.mcap
        and c_at[0]["mailbox_capacity_fault"] == 0,
        "T5) exactly `capacity` (%d) messages fit and do NOT latch"
        % (r2.mcap,))

    c_ov = r2.claims(r2.fold(OVER))
    rep(boxes(c_ov[0], "next_inbox") == []
        and c_ov[0]["mailbox_capacity_fault"] == 1,
        "T5b) ... and one more than capacity delivers NOTHING AT ALL and "
        "latches: %s messages queued, fault=%d. Correction 2's law is "
        "all-or-none, so an overflow is not a drop of the excess -- a partial "
        "append is the helpful behaviour golden forbids"
        % (boxes(c_ov[0], "next_inbox"), c_ov[0]["mailbox_capacity_fault"]))

    c_rs = r2.claims(r2.fold(RESUME))
    faults = [c["mailbox_capacity_fault"] for c in c_rs]
    rep(faults == [1, 1, 1]
        and boxes(c_rs[1], "next_inbox") == [(7, 7, 7, 7)]
        and boxes(c_rs[2], "inbox") == [(7, 7, 7, 7)],
        "T5c) ... and the latch is STICKY without being a gate: fault runs "
        "%s across the three epochs while epoch 2 still delivers %s. A latch "
        "that suppressed later epochs would be a different machine"
        % (faults, boxes(c_rs[1], "next_inbox")))

    rep(r2.films(r2.fold(OVER)) == r2.golden(OVER)
        and r2.films(r2.fold(RESUME)) == r2.golden(RESUME)
        and r2.films(r2.fold(AT_CAP)) == r2.golden(AT_CAP),
        "T5d) ... and all three capacity shapes render BYTE-identical films "
        "to golden, so the boundary is golden's boundary and not one this "
        "reducer chose")


# ------------------------------------------------------------------- T6
# CONDITION (7). Both halves of `runtime_seams`, and the Film v0.7 gate.
def t6_seams_and_film():
    r4 = S["r4"]
    rep(r4.policy == AD.MAILBOX_POLICY_ID
        and r4.mbrec == [("mb", 8, r4.mcap)]
        and r4.arule is X.ACCEPT_UNIQUE,
        "T6) the fold reads EVERY seam off the sealed world -- policy %s, "
        "mailbox records %s, ACCEPT rule %s -- through `runtime_seams`, which "
        "the ruling made normative precisely so a caller cannot default one "
        "part" % (r4.policy, r4.mbrec, r4.arule))
    rep(r4.arule is X.accept_rule_for_policy(r4.policy)
        and X.accept_rule_for_artifact(r4.artifact) is r4.arule,
        "T6a) ... and the ACCEPT rule is a function of the SEALED "
        "`admit_policy_id` ALONE: the artifact route reaches the same object "
        "as the policy-id route, because the artifact route only reads that "
        "field")

    f1 = r4.ic_films(B3)[1].decode().split("\n")
    mb_lines = [ln for ln in f1 if ln.startswith(("admit_mailbox:", "mailbox:",
                                                  "ledger:"))]
    rep(len(mb_lines) == 3
        and mb_lines[0] == "admit_mailbox:policy_capable=1,"
                           "mailbox_capacity_fault=0"
        and mb_lines[1].startswith("mailbox:mb:w=8,capacity=%d," % r4.mcap)
        and "inbox=(w15.s0." in mb_lines[1]
        and mb_lines[2].startswith("ledger:MailboxDeliver,mailbox=mb,epoch=2"),
        "T6b) ... and the Film v0.7 mailbox projection is emitted in full "
        "from the REDUCED trajectory: %s" % (mb_lines,))

    # The gate. A mailbox-free world must render exactly as it did before this
    # commit existed, which is the film-level restatement of condition (3).
    free_lp = B47.lower(B47.world2(""), [])
    free_fx = W.ir_to_fixture(free_lp.artifact)
    free_pol, free_mb, free_rule = FD.runtime_seams(free_lp.artifact, free_fx)
    rep(free_mb == [] and free_pol == AD.ACCEPTANCE_POLICY_ID
        and free_rule is X.ACCEPT_MIN and not free_rule.reject_equivocal
        and not [ln for ln in B49.gfilms(free_lp.artifact, free_fx,
                                         [[ROT]])[0].decode().split("\n")
                 if ln.startswith(("admit_mailbox:", "mailbox:", "ledger:"))],
        "T6c) ... and a mailbox-free world declares the ORIGINAL policy, the "
        "ORIGINAL first-receipt ACCEPT rule and an empty mailbox list, so Film "
        "v0.7 gates the whole block off and its film is the one it always was")


# ------------------------------------------------------------------- T7
# THE BOUNDARY, CLOSED. This was commit 5b's stated edge and is commit 5c's
# subject.
#
# `admit_mailbox_deliver_all_v1` replaces seam 1 as well as seam 2: an
# EQUIVOCAL event key (two facts, same writer and sequence, different
# candidate) yields no receipt, no delivery, and a MailboxReject. At 5b the IC
# ACCEPT stage implemented the FROZEN seam 1 -- leader-wins, which is
# `_resolve_candidates_min` -- so it minted a receipt and delivered, and a
# sealed world's reduction contradicted the policy that world DECLARED.
#
# The rows below used to record that divergence. They now record its closure,
# which is the point of having written them as measurements: the commit that
# fixed it FLIPPED a known row instead of quietly changing what the reducer
# means. The rule is selected from the sealed `admit_policy_id` through
# `runtime_seams` (T6/T6a) and reaches BOTH ACCEPT stages (T2d).
def t7_boundary():
    r2 = S["r2"]
    ic_eq = r2.ic_films(EQUIV)
    gd_eq = r2.golden(EQUIV)
    ic_txt = ic_eq[0].decode()
    rep(ic_eq == gd_eq
        and "ledger:MailboxReject,w=15,s=0,epoch=1,reason=equivocal_send"
            in ic_txt
        and "MailboxEnqueue" not in ic_txt
        and "receipt:w=15,s=0" not in ic_txt
        and "recognition:w=15,s=0,state=disputed" in ic_txt,
        "T7) CLOSED: on an EQUIVOCAL event key the reduction now refuses "
        "exactly where the declared policy refuses -- ic_ref == golden, one "
        "MailboxReject naming equivocal_send, NO MailboxEnqueue and NO "
        "receipt, with both disputed candidates retained as facts")

    rep(r2.ic_films(AT_CAP) == r2.golden(AT_CAP),
        "T7b) ... and it is EXACTLY that shape and no wider: the same world, "
        "same policy and same mailbox with UNIQUE event keys folds identical "
        "films, so what changed is seam 1's resolution rule and not the "
        "mailbox")

    # A route's own claims cannot reach an equivocal key. `route_claim_identity`
    # numbers by canonical RouteKey, so two routes are two event keys. At 5b
    # this bounded the damage; at 5c it is no longer an excuse for anything, and
    # it is kept because it is TRUE and load-bearing in its own right -- it is
    # why a world's own routes never depend on which seam 1 is selected.
    many = B47.lower(B47.world2(MB_CAP4),
                     [B47.route(tag="aa", body=(0, 0, 0, 1)),
                      B47.route(tag="zz", body=(0, 0, 0, 2))]).artifact
    eks = [(c["writer_id"], c["sequence"]) for _, c in FD.route_claims(many)]
    rep(len(eks) == len(set(eks)) == 2,
        "T7c) ... and route identity is why a world's OWN routes never reach "
        "the rule at all: two routes mint two DISTINCT event keys %s, because "
        "`sequence` is the canonical RouteKey ordinal" % (eks,))

    # ---- The control. "Equivocal" means DISTINCT candidates, and the whole
    # rule turns on that word. A repeated IDENTICAL fact is one candidate, so it
    # must still be accepted exactly once -- otherwise the rule would be
    # rejecting RETRANSMISSION, which is the opposite of what a mailbox needs.
    # Structurally this holds because `ic_insert_sorted` is insert-if-absent and
    # the fact vector is a SET; the row is here because "holds structurally" is
    # a claim about code and this is a claim about behaviour.
    dup = [[snd(15, 0, (1, 1, 1, 1)), snd(15, 0, (1, 1, 1, 1))], []]
    ic_dup = r2.ic_films(dup)
    dtxt = ic_dup[0].decode()
    rep(ic_dup == r2.golden(dup)
        and dtxt.count("claim:w=15,s=0") == 1
        and "receipt:w=15,s=0" in dtxt
        and "recognition:w=15,s=0,state=unambiguous" in dtxt
        and "MailboxReject" not in dtxt,
        "T7d) CONTROL: a repeated IDENTICAL fact is ONE candidate, not an "
        "equivocation -- it deduplicates to a single claim, is accepted once, "
        "reads unambiguous and is never rejected. The rule refuses "
        "DISAGREEMENT, not retransmission")

    # ---- The other control, in the other direction. An equivocal key arriving
    # AFTER its event key already holds a receipt changes nothing: `needed`
    # excludes receipted keys, so seam 1 is never consulted and the rival fact
    # is retained as evidence without disturbing the delivery that already
    # happened. Pinned against golden rather than asserted, because "the receipt
    # is authoritative across batches" is precisely the frozen behaviour a new
    # seam 1 could break without any equivocal-key test noticing.
    late = [[snd(15, 0, (1, 1, 1, 1))],
            [snd(15, 0, (2, 2, 2, 2))],
            []]
    ic_late = r2.ic_films(late)
    l1, l2 = ic_late[0].decode(), ic_late[1].decode()
    rep(ic_late == r2.golden(late)
        and "receipt:w=15,s=0" in l1 and "receipt:w=15,s=0" in l2
        and "MailboxReject" not in l2
        and "recognition:w=15,s=0,state=disputed" in l2
        and "MailboxEnqueue" in l1,
        "T7e) PRIOR RECEIPT: an equivocating fact that arrives after the key "
        "is already receipted is NOT re-resolved -- no reject, the receipt and "
        "its delivery stand, and the rival is kept as a fact so the film still "
        "reads disputed. First receipt stays authoritative across batches")

    # ---- THE ORTHOGONALITY ROW, and the sharpest one in the file. The ruling
    # forbade deriving ACCEPT from the v2 proof profile, from mailbox presence,
    # from `mcap`, or from the existence of a `Send`, on the grounds that all of
    # those merely CORRELATE with the declared policy. Every row above is
    # consistent with all five shortcuts, because in the rigs above they agree.
    #
    # This world is the one where they do not. The acceptance policy is chosen
    # by MAILBOX PRESENCE at lowering time; the proof profile is chosen by
    # ROUTES. A mailbox-bearing, ROUTE-FREE world therefore declares
    # `admit_mailbox_deliver_all_v1` while lowering under `admit.ic.v1.core52`
    # with `mcap == 0` and no `Send` in the profile's kinds at all -- so a rule
    # taken from the profile, from `mcap`, or from Send-capability would be the
    # frozen one, and only a rule taken from the SEALED POLICY is correct.
    #
    # And the claim it refuses is a SetRotor, which closes the ruling's other
    # clause in the same breath: ACCEPT resolves the event key BEFORE MAP
    # applies operation-specific behaviour, so equivocation rejection is not a
    # Send feature.
    free = Rig(MB_CAP4, routes=[])
    equiv_rot = [[AD.mk_claim(1, 1, ("SetRotor", "sp", (1, 2, 3, 4))),
                  AD.mk_claim(1, 1, ("SetRotor", "sp", (4, 3, 2, 1)))], []]
    ic_rot = free.ic_films(equiv_rot)
    rtxt = ic_rot[0].decode()
    rep(free.policy == AD.MAILBOX_POLICY_ID and free.prof is V1
        and free.arule is X.ACCEPT_UNIQUE and free.mcap_used == 0
        and AD.KIND_SEND not in V1.KINDS
        and ic_rot == free.golden(equiv_rot)
        and "reason=equivocal_send" in rtxt
        and "receipt:w=1,s=1" not in rtxt
        and "rotor=10,00,00,00" in rtxt,
        "T7f) ORTHOGONALITY: a mailbox-bearing ROUTE-FREE world declares %s "
        "but lowers under %s with mcap=0 and no Send kind -- and its equivocal "
        "SetRotor is still refused, ic_ref == golden, with the rotor "
        "UNMOVED. The rule comes from the sealed policy, not from the profile, "
        "the mailbox, `mcap` or the existence of a Send"
        % (free.policy, V1.name))

    # ---- CLOSED at the promotion, which is where 5c said it belonged.
    # `film_bytes_v7` rendered `admit:policy=` from the module constant, so
    # every film above labelled itself with the FROZEN policy while showing
    # behaviour only the OTHER policy can produce -- a film that rejects an
    # equivocal send and calls itself `admit_candidate_min_firstreceipt_v1`.
    #
    # 5c left it because both runtimes rendered the same wrong label, so
    # ic == golden held either way, and the fix MOVES declared film bytes for
    # every mailbox world. Core 0.2.0 is the cut where film bytes may move, so
    # the row now asserts the opposite of what it measured.
    #
    # The inequality half is not decoration. A label that is merely PRESENT
    # proves nothing -- the frozen name must be ABSENT too, or a film emitting
    # both would pass. And T6c re-asserts the frozen world still renders the
    # frozen name, so this is a relabelling and not a global rename.
    rep("admit:policy=%s," % r2.policy in ic_txt
        and r2.policy == AD.MAILBOX_POLICY_ID
        and "admit:policy=%s," % AD.ACCEPTANCE_POLICY_ID not in ic_txt,
        "T7g) CLOSED (Core 0.2.0): the film's `admit:policy=` line is now the "
        "SEALED declaration -- a world declaring %s renders a film labelled %s "
        "and NOT %s. The film names the seam that produced the receipts below "
        "it, so a rejection and the policy that authorised it can no longer "
        "contradict each other on the same page"
        % (r2.policy, r2.policy, AD.ACCEPTANCE_POLICY_ID))

    # ---- WHY THAT LABEL IS NOT COSMETIC -- which is what 5c called it, and
    # what I called it. Core 0.1.x §8b freezes the replay package as
    #
    #     ReplayBundle { initial_artifact, initial_state, event_ledger,
    #                    frames, policy_ids }
    #
    # and `policy_ids` is a FROZEN field. The film is where `event_ledger` and
    # `policy_ids` are serialized together: the `admit:policy=` line is the
    # ONLY place a trajectory records which seam produced the receipts beneath
    # it. So a mailbox world's film did not have a cosmetic defect. It could
    # not serve as the EventLedger half of a ReplayBundle at all, because the
    # `policy_ids` it carried would not reproduce the `frames` it carried.
    #
    # This row closes that by REPLAYING FROM THE FILM'S OWN LABEL rather than
    # from the rig: parse `admit:policy=` back out of the rendered bytes, fold
    # the same world and batches under exactly that policy, and require the
    # result to be byte-identical. Before the fix the label named the frozen
    # seam, so this refold produced a receipt and an enqueue where the original
    # recorded a rejection -- a replay contradicting its own recording.
    #
    # Deliberately parsed from BYTES rather than read from `r2.policy`. Taking
    # it from the rig would assert that the rig agrees with itself, which was
    # never in doubt; the question is whether a consumer holding only the film
    # can recover the seam that made it.
    label = [ln.split("admit:policy=")[1].split(",")[0]
             for ln in ic_txt.split("\n") if ln.startswith("admit:policy=")]
    replay = r2.golden(EQUIV, policy=label[0]) if len(label) == 1 else None
    rep(len(label) == 1 and label[0] == r2.policy
        and replay == gd_eq and replay == ic_eq,
        "T7h) REPLAY EXACTNESS (§8b `policy_ids`): re-folding the world under "
        "the policy PARSED OUT OF THE FILM'S OWN BYTES reproduces that film "
        "exactly. The label is a frozen ReplayBundle field, not decoration -- "
        "before 0.2.0 a mailbox film named a seam that would have replayed a "
        "receipt where the film recorded a rejection")

    # ---- THE OTHER 0.2.0 CORRECTION TO GOLDEN, which had no row until now.
    # `film_bytes_v7` rendered its EventLedger loop INSIDE `if mailboxes:`, so
    # a trajectory that computed a `MailboxReject` and held no mailbox bundle
    # dropped the entry silently while still printing `state=disputed`. That is
    # the same "a reject is not a mailbox event" defect the 5c ruling forbade,
    # sitting in golden while I was fixing my own copy of it in the projection.
    #
    # T6c is the INERTNESS half: a mailbox-free world under its own declared
    # policy still renders no ledger line at all. This is the POSITIVE half,
    # and it needs a configuration the sealed path cannot currently produce --
    # a mailbox-free world driven under the MAILBOX policy. `admit_step` and
    # `gfilms` both take the policy explicitly, so a caller reaches it today
    # even though `semantic_surface_for_roles` never selects it.
    #
    # Stated plainly: this is a GOLDEN row about the FILM, not about the
    # reduction. The IC side selects `ACCEPT_MIN` for this world from its seal
    # (T6c) and would not reject at all, so there is no ic == golden claim
    # here and pretending otherwise would be the correlation error again.
    # What it pins is narrower and real: when golden computes a refusal, the
    # film shows it, and whether a mailbox exists has nothing to do with it.
    nomb_lp = B47.lower(B47.world2(""), [])
    nomb_fx = W.ir_to_fixture(nomb_lp.artifact)
    nomb = B49.gfilms(nomb_lp.artifact, nomb_fx,
                      [[AD.mk_claim(1, 1, ("SetRotor", "sp", (1, 2, 3, 4))),
                        AD.mk_claim(1, 1, ("SetRotor", "sp", (4, 3, 2, 1)))]],
                      policy=AD.MAILBOX_POLICY_ID)[0].decode()
    rep(FD.film_mailboxes(nomb_fx) == []
        and "ledger:MailboxReject,w=1,s=1,epoch=1,reason=equivocal_send"
            in nomb
        and "recognition:w=1,s=1,state=disputed" in nomb
        and "receipt:w=1,s=1" not in nomb
        and "admit_mailbox:" not in nomb and "mailbox:sp" not in nomb,
        "T7i) the EventLedger is not part of the mailbox block: a world with "
        "NO mailbox, driven under the mailbox policy, renders its "
        "MailboxReject. Before 0.2.0 the entry was computed and then dropped "
        "by `if mailboxes:`, leaving a film that asserted a dispute and "
        "withheld the refusal causing it")


# ------------------------------------------------------------------- T8
# CONDITION (8), reference half. A matrix rather than one trajectory: the twin
# is only a twin if it stays one across the shapes that make the stages
# interact.
def t8_twin():
    r4, r2 = S["r4"], S["r2"]
    matrix = [
        ("the world's own route, three epochs",
         r4, FD.fold_batches(r4.artifact, [[] for _ in range(3)])),
        ("sends beside a rotor and a fault reset",
         r4, [[snd(15, 0, (1, 1, 1, 1)), ROT, RST], []]),
        ("sends from DIFFERENT writers in one epoch",
         r4, [[snd(3, 7, (5, 5, 5, 5)), snd(15, 0, (1, 1, 1, 1))], []]),
        ("the SAME event key re-observed a later epoch",
         r4, [[snd(15, 0, (1, 1, 1, 1))], [snd(15, 0, (1, 1, 1, 1))], []]),
        ("sends spread one per epoch",
         r4, [[snd(15, 0, (1, 0, 0, 0))], [snd(15, 1, (2, 0, 0, 0))],
              [snd(15, 2, (3, 0, 0, 0))]]),
        ("an empty epoch between two sends",
         r2, [[], [snd(15, 0, (4, 4, 4, 4))], []]),
    ]
    bad = []
    for name, rig, batches in matrix:
        if rig.ic_films(batches) != rig.golden(batches):
            bad.append(name)
    rep(not bad,
        "T8) the route-bearing twin folds FILM-BY-FILM identical to golden "
        "across %d shapes -- own-route, mixed kinds, mixed writers, "
        "re-observation, spread and gap (failures: %s)"
        % (len(matrix), bad or "none"))

    # A twin is worth nothing if the two sides are the same computation. The
    # golden side runs `admit_step` and a world step; the IC side normalizes
    # ONE term and projects. The row that proves they are different machines
    # is the one where a defect would show: mailbox state that golden holds
    # and the IC term must RECONSTRUCT.
    rep("mailbox_states" not in r4.fold(B3)[0][0],
        "T8b) ... and the two sides really are different machines: the "
        "reduced world state carries no mailbox at all, so every mailbox line "
        "in a matched film was rebuilt from the bundle the term emitted")


# ------------------------------------------------------------------- T9
def t9_native():
    r4, r2 = S["r4"], S["r2"]
    nb = [[snd(15, 0, (1, 1, 1, 1)), snd(15, 1, (2, 2, 2, 2))],
          [], [snd(15, 2, (9, 9, 9, 9)), snd(15, 3, (8, 8, 8, 8)),
               snd(15, 4, (7, 7, 7, 7))]]
    ref = r2.fold(nb)
    nat = r2.fold(nb, reduce=O.native_reduce)
    gold = r2.golden(nb)
    rep(ref == nat and r2.films(ref) == gold and r2.films(nat) == gold,
        "T9) NATIVE: a route-bearing, mailbox-bearing, overflow-bearing "
        "3-epoch fold gives ic_ref == ic32, and BOTH render the golden "
        "films. This is the §16.3 gate commit 4 could not reach and "
        "commit 5a could only prepare")

    # The commit-5c gate in full. T7 established ic_ref == golden on the
    # equivocal key; the ruling asked for ic_ref == ic32 == golden, and the
    # native half is not a formality here. The rule adds a SECOND comparison per
    # slot and one extra `copies` fan-out per fact, so it changes the emitted
    # term's shape -- exactly the kind of edit where the reference reducer and
    # the 32-bit machine can disagree.
    eq_ref = r2.fold(EQUIV)
    eq_nat = r2.fold(EQUIV, reduce=O.native_reduce)
    eq_gold = r2.golden(EQUIV)
    rep(eq_ref == eq_nat and r2.films(eq_ref) == eq_gold
        and r2.films(eq_nat) == eq_gold
        and "MailboxReject" in r2.films(eq_nat)[0].decode(),
        "T9c) ... and the EQUIVOCAL key closes the same way natively: "
        "ic_ref == ic32 == golden, the reject is in the ic32 film too. The "
        "seam-1 selection is a property of the reduction, not of the "
        "reference reducer")

    # Its control, natively. A rule that rejected everything would also make
    # T9c pass, so the unique-key trajectory has to survive the same reducer.
    rep(r2.films(r2.fold(AT_CAP, reduce=O.native_reduce)) == r2.golden(AT_CAP),
        "T9d) ... while UNIQUE event keys still fold ic32 == golden through "
        "the same rule, so what the reduction learned is refusal of "
        "disagreement and not refusal")

    r4nat = r4.fold(B3, reduce=O.native_reduce)
    rep(r4.films(r4nat) == r4.golden(B3),
        "T9b) ... and the enqueue/deliver shift itself survives the "
        "native reducer: the epoch-N-to-N+1 trajectory of T3 folds "
        "ic32 == golden too, which is the half that makes `~~` a runtime "
        "construct rather than a spelling")


SECTIONS = (t0_profile_and_codec, t1_epoch_control, t2_frozen_surface,
            t3_enqueue_and_delivery, t4_two_sends, t5_capacity,
            t6_seams_and_film, t7_boundary, t8_twin)


def main():
    t0 = time.time()
    print("[BINDING wrl-sliceB-c5c] the mailbox-capable native profile "
          "(admit.ic.v2.mailbox53 carries mailbox state)")

    for fn in SECTIONS:
        section(fn)

    mode = "PASS_REF_ONLY"
    if not SKIP_NATIVE:
        section(t9_native)
        if not _FAILED:
            mode = "PASS_REF_AND_NATIVE"

    dt = int(time.time() - t0)
    print()
    if _FAILED:
        print("[wrl-sliceB-c5c] %d FAILED (%ds)" % (len(_FAILED), dt))
        for f in _FAILED:
            print("   - %s" % f)
        return 1
    print("[wrl-sliceB-c5c] ALL PASS -- %s (%ds)" % (mode, dt))
    print("  [note] conditions 1-8 of the commit-5a ruling, plus commit 5c: "
          "ACCEPT is now")
    print("         SELECTED from the sealed `admit_policy_id` through "
          "`runtime_seams`")
    print("         (T6/T6a) and reaches BOTH stages (T2d), so T7 has FLIPPED "
          "from a")
    print("         measured divergence to ic_ref == ic32 == golden (T7, "
          "T9c). The")
    print("         frozen first-receipt policy is byte-identical (T2, T2c). "
          "Mutation")
    print("         coverage -- v2->v1 dispatch, and BOTH directions of the "
          "seam-1")
    print("         selection -- is mutate51.")
    print("         The two axes are pulled APART by T7f: a mailbox-bearing "
          "ROUTE-FREE")
    print("         world declares the mailbox policy while lowering under "
          "the v1")
    print("         profile with mcap=0, and its equivocal SetRotor is "
          "refused anyway.")
    print("         T7g, left MEASURED by 5c, is now CLOSED by the Core 0.2.0 "
          "cut: the")
    print("         film's `admit:policy=` line reports the SEALED declaration "
          "rather")
    print("         than the module constant, so a mailbox world no longer "
          "renders a")
    print("         film labelled with the frozen policy. That moves declared "
          "film")
    print("         bytes for mailbox worlds ONLY -- T6c re-asserts the frozen "
          "world's")
    print("         film is the one it always was.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
