"""tools_ic_snapshot.py -- per-emitter byte fingerprint of the IC term surface.

Slice B commit 5a introduces a SECOND proof profile (`admit.ic.v2.mailbox53`)
alongside the frozen one (`admit.ic.v1.core52`). The ruling's condition (3) is
that route-free v1 terms stay byte-identical across that change. That is a
claim about bytes, and bytes are only comparable against a baseline captured
BEFORE the edit -- afterwards there is nothing left to compare to.

So this emits every public term-former in a FIXED order with the fresh-name
counters reset before each one, and prints `name sha256`. The counters are
process-global (`lower_e2a._VAR`, `_LBL`), so resetting makes each emitter's
fingerprint independent of the ones before it: a diff points at the emitter
that moved rather than at everything downstream of it.

Usage:  python3 tools_ic_snapshot.py [--profile v1|v2]
"""
import hashlib
import sys

import admit_ic as X
import binlib as BL
import lower_e2a as LE


def _reset():
    LE._VAR[0] = 0
    LE._LBL[0] = 0


def _fp(s):
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def emitters(P=None):
    """(name, thunk) pairs. `P` is a profile record or None for the default
    (which IS v1 -- that identity is itself one of the things being gated)."""
    kw = {} if P is None else {"prof": P}
    W = X.FKEY_W if P is None else P.FKEY_W
    C = X.CKEY_W if P is None else P.CKEY_W

    def op(v, w):
        return BL.enc_operand(v, w)

    return [
        ("ic_min2/ckey", lambda: X.ic_min2(C)),
        ("ic_eq/fkey", lambda: X.ic_eq(W)),
        ("ic_eq/ckey", lambda: X.ic_eq(C)),
        ("ic_fits", lambda: X.ic_fits(X.CNTW, 6)),
        ("ic_insert_sorted", lambda: X.ic_insert_sorted(6, **kw)),
        ("_ekey_of", lambda: X._ekey_of(op(0, W), **kw)),
        ("_kindidx_of", lambda: X._kindidx_of(op(0, W), **kw)),
        ("_pose_of", lambda: X._pose_of(op(0, W), **kw)),
        ("_canon_of", lambda: X._canon_of(op(0, W), **kw)),
        ("ic_observe", lambda: X.ic_observe(op(0, W), [op(1, W), op(2, W)], 6,
                                            **kw)),
        ("ic_accept", lambda: X.ic_accept(op(0, W), op(0, W), 6, 6, **kw)),
        ("ic_map", lambda: X.ic_map(op(0, W), op(0, W), 6, 6, **kw)),
        ("ic_reduce", lambda: X.ic_reduce(op(0, W), op(0, W),
                                          [op(1, W)], 6, 6, **kw)),
    ]


def snapshot(P=None):
    out = []
    for name, thunk in emitters(P):
        _reset()
        out.append((name, _fp(thunk())))
    return out


if __name__ == "__main__":
    P = None
    if "--profile" in sys.argv:
        which = sys.argv[sys.argv.index("--profile") + 1]
        P = {"v1": X.PROFILE_V1, "v2": X.PROFILE_V2}[which]
    for name, fp in snapshot(P):
        print("%-22s %s" % (name, fp))
