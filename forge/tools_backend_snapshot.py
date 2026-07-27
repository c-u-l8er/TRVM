#!/usr/bin/env python3
"""Per-world byte fingerprint of the v6 BACKEND surface (state + step term).

The companion to `tools_ic_snapshot.py`, and it exists for the same reason at a
different altitude. Commit 5a had to prove the v1 IC term surface did not move;
this tool was built to prove the v6 ENCODED-STATE surface did not move for
worlds declaring no mailbox. Both are claims about bytes, so both need a
baseline captured BEFORE the change -- afterwards there is nothing left to
compare against, and "it still passes" is not the same statement as "it is
unchanged".

WHAT COMMIT 5b ACTUALLY DID, versus what this tool was built expecting. The
baseline predicted that mailbox worlds would move off it and mailbox-free ones
would not. 5b shipped green and NOTHING moved: it put the mailbox in CLAIM
state, not world state, so this surface never learned a mailbox exists. These
columns measure world state and could not have seen it either way. The tool's
role therefore inverted from baseline to GUARD -- all five rows must now stay
identical, and a mailbox world that moves one has been smuggled into world
state. `binding_run52` L9/L10 is what runs it; see the header of
`v6_backend_fingerprints.txt` for the full retraction.

What is snapshotted, per world:

    blay-   `backend_layout_signature` -- the representation-FULL field list
    bcnt-   `backend_content_hash`     -- the alpha-canonicalized step term
    bknd-   `backend_artifact_id`      -- the sealed pair of the two
    state   sha256[:16] of `enc_state_v6(fx, init_state_v6(fx))`

The first three come from `compile_artifact`, so they measure the PRODUCTION
path. The fourth is added because the first three are computed by
`backend_layout_signature`, which walks the field order in its own words --
a second spelling of `_v6_fields`. Two independent walks of one layout agree
until they don't, and the one that disagrees is a field encoded at another
field's offset. Hashing the actual encoded state closes that: it is produced by
`enc_state_v6` itself, so a layout change that only one of the two walks learns
about shows up as a disagreement between rows rather than as nothing at all.

Run:  PYTHONPATH=../runtime/python python3 tools_backend_snapshot.py
"""
import hashlib
import sys

import wrl_ir as W
import compiler as C
import lower_e2a as LE
import forge_state as FS
import binding_run47 as B47

LP = {"counter_encoding": "one_hot", "onehot_max": 32, "numeric_backend": "ic",
      "compiler_hash": "a" * 64, "target": "ic32",
      "lowering_profile_version": "1.0"}

# All five worlds are under the byte-identity obligation now. The mailbox-
# bearing rows were added when they were the ones ALLOWED to move -- a baseline
# covering only the frozen half could not tell "the mailbox world changed" from
# "nothing happened" -- and they are kept because after 5b they carry the
# stronger statement: declaring a mailbox costs the world state nothing.
#
# `mailbox_routed` remains the most valuable row, for the OPPOSITE reason it was
# added. It was added to discriminate between two incompatible commits: one
# giving every mailbox-DECLARING world backend state, and one giving it only to
# worlds a route can reach. 5b turned out to be neither -- no world gets backend
# mailbox state. So this row now supplies the guarantee's strongest form: a
# world that routes into its mailbox, SELECTS admit.ic.v2.mailbox53 from its
# sealed content, and folds real sends natively still moves none of the columns.
WORLDS = [
    ("bare",            lambda: B47.world2(""),               ()),
    ("mailbox_w8c4",    lambda: B47.world2(B47.MB1),          ()),
    ("mailbox_w16c9",   lambda: B47.world2(B47.MB2),          ()),
    ("mailbox_two",     lambda: B47.world2(B47.MB1 + B47.MB2), ()),
    ("mailbox_routed",  lambda: B47.world2(B47.MB1),          (B47.route(),)),
]


def _sha(b):
    if not isinstance(b, bytes):
        b = b.encode()
    return hashlib.sha256(b).hexdigest()[:16]


def _reset():
    """`enc_state_v6` emits gensym'd binder names from process-global counters
    (`lower_e2a._VAR`, `_LBL`), so its bytes depend on how many terms were built
    earlier in the process. Left alone, this tool would report a different hash
    for the same world depending on its POSITION in the list -- a fingerprint
    that measures call order rather than layout. Resetting before each world is
    what makes the rows independent, and it is the same correction
    `tools_ic_snapshot` already carries."""
    LE._VAR[0] = 0
    LE._LBL[0] = 0


def snapshot():
    out = []
    for name, mk, routes in WORLDS:
        prog = B47.lower(mk(), routes)
        cp = W.compile_program(prog, LP)
        fx = prog.as_fixture_for_test()
        _reset()
        st = _sha(C.enc_state_v6(fx, FS.init_state_v6(fx)))
        out.append((name, cp.backend_layout_signature[5:21],
                    cp.backend_content_hash[5:21], st))
    return out


def main():
    for row in snapshot():
        print("%-16s %s %s %s" % row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
