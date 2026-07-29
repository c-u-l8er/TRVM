#!/usr/bin/env python3
"""Mutation harness for binding_run50 (Slice B commit 5a, the profile split).

Every production edit this commit made is REVERTED, one at a time, in an
isolated copy of the tree, and a battery row must then go red. The four
disciplines (null control, anchor-exactly-once, @noop-must-survive,
crash-is-not-a-catch) live in `mutate_harness.run` -- they used to be copied
into every one of these files, which is a fork in the instrument that decides
whether every other result is true.

WHAT IS DIFFERENT ABOUT THIS ONE. Commit 4's fold had a quiet characteristic
defect: a green run that answers a different question. Commit 5a's is quieter
still, because it is a defect of INTERPRETATION. The bits do not change. A
mutated tree here packs the identical key, normalizes to a well-formed term,
folds ic_ref == ic32, and reports a perfectly consistent trajectory -- of a
world where a message moved a rotor. Nothing crashes and nothing is malformed.

So the mutations below are weighted towards edits that a type checker, a
crash-based harness, and a parity check between two reducers would ALL miss:

    N4   the valid_target selector as a v1 literal  (right for v1, wrong for v2)
    N5   the kind flags made complementary again    (no third case)
    N6   the bit offsets written back as literals   (a NO-OP, and pinning that
                                                     it is one is the point)
    N6c  the fkey layout reordered consistently     (only the frozen bytes see)
    N9   the profile taken from a caller argument   (correct until misused)
    N10  route-bearing worlds left on v1            (a loud refusal, but the
                                                     ruling's condition (9))

N4 and N6/N6b/N6c are spellings of ONE defect -- an address that is right under
v1 and wrong under v2 -- at three different altitudes: a tuple slot, a bit
offset, and the field order itself. Two of them turn out to be no-ops, and that
is a result rather than a gap: IDX_LO and KIND_LO are genuinely profile-
independent, so the defect CANNOT be reintroduced there, and a row that says so
is worth more than a row that catches something.

THREE MUTATIONS WERE REWRITTEN AFTER THEY MERELY CRASHED, which is the reason
this file's first run was not its result. Under `mutate_harness`'s rules a
crash is not a catch: the mutant died before the rows executed, so the rows
proved nothing about it. In each case the obvious edit was killing the battery
on ARITY rather than exercising the defect:

  * v2 forced down v1's one-bit decode branch emits a 3-tuple where v2's
    consumers project 4 fields. The aliasing defect is not merely absent under
    v2, it is UNREPRESENTABLE -- now pinned by S8e, and N4 says the sayable
    version of it instead.
  * `wkind=1` written into PROFILE_V2 is refused by the constructor at IMPORT.
    The refusal is correct and the mutation is useless, so N2 now deletes the
    CHECK and lets S1d -- which builds an undersized profile on purpose -- be
    what goes red. Mutate the guard, not the guarded value.
  * widening the selector name string produces a 5-binder lambda projecting a
    4-field tuple, whose reduction is not a bool at all. N12 moves a selector
    that exists instead.

And one of them found a real hole rather than a stated one: N4 survived at
first because S10 and S10d compared the Send-bearing fold against the Send-FREE
fold, and the defect broke both arms identically. A differential row is blind
to a defect common to both sides of the difference. S10 now names the
SetRotor's own pose, and S10e cross-checks the v1 and v2 folds against each
other -- the ruling's condition (3) restated at the fold instead of the bytes.
"""
import sys

from mutate_harness import run

# (label, file, old, new, rows that MUST go red)
MUTATIONS = [
    ("N0 NULL MUTANT (control: this one must PASS)",
     "admit_ic.py", "PROFILE_V1 = Profile(", "PROFILE_V1 = Profile(", []),

    ("N0b @noop reordering of the PROFILES registry (harness self-check)",
     "admit_ic.py",
     "PROFILES = {PROFILE_V1.name: PROFILE_V1, PROFILE_V2.name: PROFILE_V2}",
     "PROFILES = dict([(PROFILE_V2.name, PROFILE_V2),\n"
     "                 (PROFILE_V1.name, PROFILE_V1)])",
     "@noop:a registry built in the other order is the same registry"),

    # ------------------------------------------------- the widths (S1, S2)
    ("N1 v2 pays for WKIND out of WIDX (the rejected option (b))",
     "admit_ic.py",
     'PROFILE_V2 = Profile("admit.ic.v2.mailbox53", wkind=2, widx=3, wlane=8,',
     'PROFILE_V2 = Profile("admit.ic.v2.mailbox53", wkind=2, widx=2, wlane=8,',
     # Holds CKEY_W at 44 and FKEY_W at 52, so it honours the letter of the
     # earlier prohibition -- and caps a world at 3 mailboxes while the route
     # budget permits 6. binding_run49 R12f/R12g is the row that costed this.
     ["S1b", "S2b"]),

    ("N2 the width/tag-set agreement check removed from the constructor",
     "admit_ic.py",
     "        assert max(kinds) < (1 << wkind), (",
     "        assert max(kinds) < (1 << wkind) or True, (",
     # This mutates the GUARD, not the guarded value, and that is the point.
     # Writing `wkind=1` into PROFILE_V2 directly does refuse -- but it refuses
     # at IMPORT, so the battery dies before a single row runs and the mutation
     # proves nothing about the rows. A crash is not a catch. The checkable
     # form of "the width and the tag set cannot disagree" is therefore to
     # delete the check and let S1d, which constructs an undersized profile on
     # purpose, be the thing that goes red.
     ["S1d"]),

    ("N3 the frozen profile silently widened instead of split",
     "admit_ic.py",
     'PROFILE_V1 = Profile("admit.ic.v1.core52", wkind=1, widx=3, wlane=8,',
     'PROFILE_V1 = Profile("admit.ic.v1.core52", wkind=2, widx=3, wlane=8,',
     # This is the whole prohibition, in one line: every route-free world in
     # the tree keeps working, and every term it emits has moved. NOT S3c --
     # the module-level names are aliases OF PROFILE_V1, so widening v1 widens
     # them too and they still agree with it. S3c pins that the aliases track
     # v1; it cannot pin what v1 itself is, and expecting it to was an error.
     ["S1", "S3"]),

    # --------------------------------------------- the decoder (S6, S7, S8)
    ("N4 the valid_target SELECTOR written as a v1 literal",
     "admit_ic.py",
     "    i_val = len(prof.KINDS)",
     "    i_val = 2",
     # The addressing defect moved up a level, from bit offsets to tuple
     # slots, and it is the same trap N6 sets: 2 is the correct slot under v1
     # and the WRONG one under v2, where it selects `is_send` instead of
     # `valid_target`. The term is well-formed, the arity is right, nothing
     # raises -- the reducer simply asks "is this a Send?" every time it means
     # to ask "does this target exist?". v1 stays byte-identical, which is
     # what makes it the kind of edit a v1 regression suite cannot see.
     #
     # This REPLACES the obvious spelling (forcing v2 down the one-bit v1
     # branch). That one dies on arity rather than decoding wrongly -- see
     # S8e -- and a crash is not a catch, so it was proving nothing.
     #
     # It also found a real hole. S10 and S10d used to compare the Send-bearing
     # fold against the Send-FREE fold, and this defect breaks both sides
     # identically, so both rows stayed green while the rotor never moved. A
     # differential row cannot see a defect that is common to both arms. S10
     # now names the SetRotor's own pose and S10e cross-checks v1 against v2.
     ["S10", "S10e"]),

    ("N5 the v2 kind flags made COMPLEMENTARY (exhaustive, so no inert case)",
     "admit_ic.py",
     "            lits.append(src if (tag >> i) & 1 else NOT(src))",
     "            lits.append(src if (tag >> i) & 1 or i else NOT(src))",
     # Subtler than N4: three flags are still emitted, but they stop being
     # mutually exclusive matches on the FULL tag, so an unminted tag stops
     # being inert and starts being something.
     ["S8", "S8c"]),

    ("N6 the fkey bit offsets written back as v1 literals",
     "admit_ic.py",
     "    ix = [b[prof.IDX_LO + i] for i in range(prof.WIDX)]",
     "    ix = [b[32 + i] for i in range(prof.WIDX)]",
     # Correct for v1 and correct for v2's idx, which is why this one is a
     # trap: the literal that is RIGHT here sits next to the one that is not.
     "@noop:IDX_LO is 32 under both profiles -- this literal is still correct"),

    ("N6b ... and the kind offset, which is NOT profile-independent",
     "admit_ic.py",
     "    kb = [b[prof.KIND_LO + i] for i in range(prof.WKIND)]",
     "    kb = [b[35 + i] for i in range(prof.WKIND)]",
     # KIND_LO is 35 under v1 and 35 under v2 as well -- the kind field starts
     # in the same place and GROWS upward. So this one is also a no-op, and
     # that is worth pinning: it means the addressing defect cannot be
     # reintroduced by a literal at the kind field. It can only be introduced
     # ABOVE it, which is N6c.
     "@noop:KIND_LO is 35 under both profiles -- the field grows upward"),

    ("N6c the fkey LAYOUT reordered consistently (digest below kind)",
     "admit_ic.py",
     '                ("digest", self.WD), ("kind", self.WKIND), '
     '("idx", self.WIDX),',
     '                ("kind", self.WKIND), ("digest", self.WD), '
     '("idx", self.WIDX),',
     # The sharpest mutation in the file, and the reason `Profile.FIELDS` is
     # now the single definition of the bit order. Packer, unpacker and every
     # derived offset move TOGETHER, so the tree stays perfectly
     # self-consistent: keys pack, terms normalize, the decoder reads the kind
     # at the kind's (new) address, ic_ref == ic32, the trajectory is coherent.
     # Nothing is wrong except that every v1 term has different bytes. Only the
     # frozen fingerprint file can see it -- which is what "byte-for-byte" in
     # the ruling actually costs, stated as a mutation.
     ["S3"]),

    # ----------------------------------------------- pack/unpack (S4, S5)
    ("N7 the unpacker's field order reversed (LSB-first instead of MSB)",
     "admit_ic.py",
     "    for name, w in prof.FIELDS:                  # MSB-first, as `_cat` packs",
     "    for name, w in reversed(prof.FIELDS):        # MSB-first, as `_cat` packs",
     # `_cat` packs MSB-first. An unpacker that walks the other way returns
     # plausible small integers for every field and is wrong about all of them.
     ["S5", "S5b", "S10c"]),

    ("N8 v1 allowed to truncate a Send instead of refusing it",
     "admit_ic.py",
     '        assert 0 <= v < (1 << wd), "field %r overflows width %d" % (v, wd)',
     "        v = v & ((1 << wd) - 1)",
     # The silent-truncation failure. v1 stops raising and starts minting a
     # SetRotor from a Send, which is exactly the outcome S4 exists to forbid.
     ["S4"]),

    # ------------------------------------------------- the dispatch (S9)
    ("N9 the profile taken from a caller argument instead of the artifact",
     "admit_ic.py",
     "    import wrl_canonical as WC\n"
     "    if not isinstance(artifact, WC.SealedArtifact):\n"
     "        artifact = WC.seal_artifact(artifact)",
     "    import wrl_canonical as WC\n"
     "    if not isinstance(artifact, WC.SealedArtifact):\n"
     "        return PROFILE_V1",
     # The ruling's "never from an unsealed caller flag", inverted: an
     # unsealed artifact now silently gets the frozen profile, which is the
     # one that cannot represent its routes.
     ["S9c"]),

    ("N10 route-bearing worlds left on v1 (the dispatch reverted)",
     "admit_ic.py",
     "    return PROFILE_V2 if WC.routes_of_artifact(artifact.artifact) else PROFILE_V1",
     "    return PROFILE_V1",
     # The ruling's condition (9), stated as a mutation: reverting v2 dispatch
     # to v1 must be caught.
     ["S9b"]),

    ("N11 the dispatch fires for MAILBOXES rather than for routes",
     "admit_ic.py",
     "    return PROFILE_V2 if WC.routes_of_artifact(artifact.artifact) else PROFILE_V1",
     "    return PROFILE_V2 if (artifact.artifact.get('objects') and any(\n"
     "        o.get('role') == 'Mailbox' for o in artifact.artifact['objects'])\n"
     "    ) else PROFILE_V1",
     # Not wrong in a way that breaks anything -- it is CONSERVATIVE, and that
     # is the point. It quietly narrows the byte-identical frozen surface for
     # no gain, and S9d is the row that notices.
     ["S9d"]),

    # ------------------------------------------ the v1 surface (S3) itself
    ("N12 the fault selector reads the SetRotor flag instead",
     "admit_ic.py",
     "    i_rst = prof.KINDS.index(AD.KIND_RESETFAULT)",
     "    i_rst = prof.KINDS.index(AD.KIND_SETROTOR)",
     # Legal under both profiles (both declare SETROTOR), so no arity change
     # and no crash: terms still normalize, and every v1 term that reads a
     # kind tuple now has different bytes. Together with N6c and N13 this is
     # the third angle on the fingerprint file -- N6c moves the layout, N13
     # moves the expectation, and this moves a selector.
     #
     # It REPLACES widening the selector name string, which produced a lambda
     # of five binders projecting a four-field tuple. That does not emit
     # different bytes, it emits a term whose reduction is not a bool at all.
     ["S3"]),

    ("N13 the fingerprint file quietly regenerated instead of honoured",
     "ic_v1_term_fingerprints.txt",
     "ic_map                 b525c584ee8831b8",
     "ic_map                 0000000000000000",
     # The inverse attack: leave the code alone and move the expectation. S3
     # must go red either way, or the file is decoration.
     ["S3"]),
]


def main():
    return run("binding_run50.py", MUTATIONS, prefix="S")


if __name__ == "__main__":
    sys.exit(main())
