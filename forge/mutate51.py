#!/usr/bin/env python3
"""Mutation harness for binding_run51 (Slice B commit 5c, the mailbox stage plus
the seam-1 selection).

Every production edit this commit made is REVERTED, one at a time, in an
isolated copy of the tree, and a battery row must then go red. The four
disciplines -- null control, anchor-exactly-once, @noop-must-survive,
crash-is-not-a-catch -- live in `mutate_harness.run`.

WHAT IS DIFFERENT ABOUT THIS ONE. Commit 5a's characteristic defect was one of
INTERPRETATION: the bits did not change, only what they meant. Commit 5b's is
one of ARITHMETIC UNDER LINEARITY, and it has a specific consequence for how
this file is written.

The mailbox stage is a one-hot rank, a set of selects and an atomic
suppression, and in an interaction calculus every one of those is LINEAR: a dup
whose output is never consumed is not free, it is a defect. So the obvious
mutations -- delete the suppression, stop the counter advancing, drop a guard
-- mostly do not produce a WRONG machine, they produce a MALFORMED one, and a
malformed term kills the battery process rather than failing a row. Under
`mutate_harness`'s rules a crash is not a catch: the mutant died before the
rows executed, so the rows proved nothing about it.

That is why `binding_run51` was restructured into `section()`s before this file
was written. It is not tidying. It is the difference between a mutation run
that is a result and one that is a rumour: a contained exception is a NAMED red
row attributable to the section it happened in, and an escaping one is a
traceback the harness scores as proving nothing. The battery had to be made
mutation-testable before it could be mutation-tested.

The mutations are therefore chosen to be LINEARITY-PRESERVING wherever the
defect can be said that way -- each one consumes exactly the copies the
original consumed, so the mutant tree emits a well-formed term that computes
the wrong thing:

    P1   the v2 dispatch reverted to v1          (the ruling's condition (9))
    P2   the mailbox added as a THIRD EpochControl field
    P3   a PARTIAL append instead of all-or-none (Correction 2, exactly)
    P4   the one-hot rank counter starts FULL
    P5   the counter advances on the wrong condition
    P6   the capacity latch made a conjunction   (sticky lost)
    P7   the enqueue/deliver shift removed       (condition (4), inverted)
    P8   the empty-slot sentinel stops being filtered
    P9   the fingerprint file regenerated instead of honoured
    P10  the mailbox world's ACCEPT reverted to leader-min   (5b, restored)
    P11  equivocation rejection forced onto the FROZEN policy
    P12  the rule reaches ACCEPT but not MAP

P10-P12 are commit 5c and are a different KIND of mutation from P1-P9: they do
not corrupt arithmetic, they corrupt a SELECTION. The emitted term stays
well-formed and the machine stays coherent -- it simply answers a question
about a world that world did not ask. That is why two of them are caught by
rows about BYTES rather than rows about behaviour: under P11 every mailbox
world still behaves perfectly, and only the frozen worlds quietly changed.

P3 is the one worth reading. "Delete the suppression" is not expressible --
`ovf` is dup'd exactly `mcap + 1` times and an unconsumed copy is malformed --
so the defect is spelled as what a careless implementer would ACTUALLY write:
suppress the first slot, fold the leftover fault copies into the fault bit, and
let the slots that fit survive. That is a perfectly linear, perfectly
well-formed, perfectly plausible machine. It is also the exact behaviour
Correction 2 forbids by name, and T5b is what notices.
"""
import sys

from mutate_harness import run

# (label, file, old, new, rows that MUST go red)
MUTATIONS = [
    ("P0 NULL MUTANT (control: this one must PASS)",
     "admit_ic.py",
     '        mkey = [L.let(fc[i][5], mcap, "mk") for i in range(cap)]',
     '        mkey = [L.let(fc[i][5], mcap, "mk") for i in range(cap)]', []),

    ("P0b @noop the overflow disjunction commuted (harness self-check)",
     "admit_ic.py",
     "            overflow = orv(andv(eg[u], oh[mcap][0]), overflow); u += 1",
     "            overflow = orv(overflow, andv(eg[u], oh[mcap][0])); u += 1",
     # Every v2 term this emits has DIFFERENT bytes and identical meaning: a
     # latch is a disjunction, not a sequence. The frozen fingerprint file
     # cannot see it because it captures v1 only, which is the point -- v2's
     # surface is not frozen and must not be treated as if it were.
     "@noop:OR is commutative -- an accumulating latch has no order"),

    # ------------------------------------------------------ the dispatch
    ("P1 route-bearing worlds left on v1 (the dispatch reverted)",
     "admit_ic.py",
     "    return PROFILE_V2 if WC.routes_of_artifact(artifact.artifact) "
     "else PROFILE_V1",
     "    return PROFILE_V1",
     # The ruling's condition (9), and the reason `Rig` selects its profile
     # through `profile_for_artifact` rather than defaulting to V2. Under the
     # old spelling this mutation was INVISIBLE to this battery -- every rig
     # passed v2 explicitly, so reverting the dispatch changed nothing here
     # and condition (9) rested entirely on binding_run50. Now the rigs cannot
     # represent the `Send` they are about, and they say so.
     ["T1", "T2e"]),

    # -------------------------------------------------- the frozen shape
    ("P2 the mailbox added as a THIRD EpochControl field",
     "admit_ic.py",
     "        ec = _PAIR(_PAIR(_TUPN([rotor_cfg]), _TUPN([reset_ob])), "
     "mb_bundle)",
     "        ec = _TUPN([_TUPN([rotor_cfg]), _TUPN([reset_ob]), mb_bundle])",
     # The line the commit was not allowed to cross, crossed. `compile_step_v6`
     # consumes the EpochControl, so a third field there means every
     # mailbox-bearing world steps a world state a mailbox-free world does not
     # -- and binding_run49's R12 measurement, that a mailbox costs the world
     # state nothing, quietly stops being true. T1b is the row that holds it.
     ["T1b"]),

    # -------------------------------------------------- the mailbox stage
    ("P3 a PARTIAL append instead of all-or-none",
     "admit_ic.py",
     '        ovf = L.let(overflow, mcap + 1, "ov")\n'
     '        present = [f"(({NOT(ovf[k])} {slots[k]}) {EMPTY})" '
     "for k in range(mcap)]\n"
     "        mb_bundle = _TUPN(present + [ovf[mcap]])",
     '        ovf = L.let(overflow, mcap + 1, "ov")\n'
     '        present = ([f"(({NOT(ovf[0])} {slots[0]}) {EMPTY})"]\n'
     "                   + [slots[k] for k in range(1, mcap)])\n"
     "        fbit = ovf[mcap]\n"
     "        for k in range(1, mcap):\n"
     "            fbit = orv(ovf[k], fbit)\n"
     "        mb_bundle = _TUPN(present + [fbit])",
     # The helpful behaviour: keep the messages that fit, drop the one that
     # did not, still raise the fault. Linear, well-formed, and wrong --
     # Correction 2's law is all-or-none precisely because a partial append
     # makes delivery depend on an order that golden re-sorts away.
     ["T5b", "T5d"]),

    ("P4 the one-hot rank counter starts FULL",
     "admit_ic.py",
     '            return [L.let(T if k == 0 else F, 3 if k < mcap else 2, "oh")',
     '            return [L.let(T if k == mcap else F, 3 if k < mcap else 2, '
     '"oh")',
     # Same shape, same copy counts, same arity -- the counter simply begins
     # at the position that means "already full", so every Send is an overflow
     # and no message is ever queued.
     ["T3", "T4", "T5"]),

    ("P5 the counter advances on the wrong condition",
     "admit_ic.py",
     "                    keep = andv(NOT(eg[u]), oh[k][1]); u += 1",
     "                    keep = andv(eg[u], oh[k][1]); u += 1",
     # A single dropped negation. `keep` and `move` now fire on the SAME
     # condition, so the one-hot stops being one: an eligible Send both holds
     # position k and advances into it, and a slot with no Send loses its bit
     # entirely. Nothing is malformed and the rank is meaningless.
     #
     # T3 is NOT among the required rows, and the reason is the point of the
     # row: T3 folds ONE send, and a rank that fails to advance is unobservable
     # at rank <= 1 -- the single message still lands in slot 0 and the film is
     # byte-identical. The defect becomes observable at the first batch where
     # rank is load-bearing, which is T4's two sends into one mailbox. A
     # counter's defect must be demanded of the rows that COUNT, and requiring
     # it of T3 was a prediction about arithmetic that the arithmetic does not
     # owe.
     ["T4", "T4b"]),

    ("P6 the capacity latch made a conjunction (sticky lost)",
     "binding_run3o.py",
     '            mb_tail = f" (({ov} {_T}) {mb_v})))"',
     '            mb_tail = f" (({ov} {mb_v}) {X.F})))"',
     # OR becomes AND. Both operands are still consumed exactly once, so the
     # fold is as linear as it was; the fault simply stops surviving the epoch
     # that raised it. golden latches in claim state and never clears, which
     # is why the latch is threaded through the TERM rather than OR'd together
     # by the decoder afterwards.
     ["T5b", "T5c", "T5d"]),

    # ------------------------------------------------- the fold's shift
    ("P7 the enqueue/deliver shift removed (delivered in its own epoch)",
     "binding_run3o.py",
     '            prev = ([_mk_message(k, fx, prof) for k in decoded[e - 1][5]]\n'
     "                    if e else [])",
     "            prev = [_mk_message(k, fx, prof) for k in row[5]]",
     # Condition (4), inverted. The bundle an epoch EMITS becomes the inbox
     # that same epoch, so `_roll_mailboxes` has effectively been skipped and
     # a message is delivered in the period it was sent. Everything still
     # decodes; the trajectory is simply a period out.
     ["T3", "T3c", "T4", "T5d", "T8"]),

    ("P8 the empty-slot sentinel stops being filtered",
     "binding_run3o.py",
     "            row += (tuple(sorted(k for k in ks if k != prof.FKEY_ALLONES)),",
     "            row += (tuple(sorted(ks)),",
     # `FKEY_ALLONES` is the empty slot, exactly as it is in the fact vector.
     # A decoder that forgets means every unused slot becomes a message whose
     # key nothing minted. This one is deliberately allowed to be a contained
     # exception rather than a wrong answer: the sentinel does not name a
     # payload, so the projection cannot invent one, and the section reports
     # it as its own row instead of taking the process down.
     ["T3"]),

    # ------------------------------------------------ the frozen surface
    ("P9 the fingerprint file quietly regenerated instead of honoured",
     "ic_v1_term_fingerprints.txt",
     "c5158471ad1d975f",
     "0000000000000000",
     # The inverse attack, aimed at the emitter this commit actually edited:
     # leave `ic_reduce` alone and move the expectation. T2 must go red either
     # way, or condition (3) is decoration.
     ["T2"]),

    # ------------------------------------------ commit 5c: the seam-1 selection
    # The ruling asked for BOTH directions, and the asymmetry between them is
    # the whole argument. Selection is a MAP from a sealed field to a rule, so
    # it has exactly two ways to be wrong -- the right rule for the wrong world,
    # and the wrong rule for the right one -- and a single mutation can only
    # ever demonstrate one of them. A commit that caught P10 and not P11 would
    # have proved the mailbox world reaches its new rule while leaving the
    # frozen world's rule completely untested, which is precisely the claim
    # gate 5 exists to protect.
    ("P10 the mailbox world's ACCEPT reverted to leader-min",
     "admit_ic.py",
     "ACCEPT_UNIQUE = AcceptRule(AD.MAILBOX_POLICY_ID, True)",
     "ACCEPT_UNIQUE = AcceptRule(AD.MAILBOX_POLICY_ID, False)",
     # Commit 5b, exactly: the world still DECLARES
     # `admit_mailbox_deliver_all_v1`, `runtime_seams` still hands a rule to
     # both stages, the film still gates its mailbox block on -- and the rule
     # handed over is the frozen one, so an equivocal event key mints a receipt
     # and delivers a message its own declared policy refuses. Nothing is
     # malformed and nothing throws. T7 is the row, and it is the row this
     # commit flipped from red to green, so the mutation restores the exact
     # measured state 5b shipped in.
     #
     # T7b/T7d/T7e stay GREEN under it, and that is not a weakness of the
     # mutation -- it is the shape of the defect. Unique keys, duplicates and
     # already-receipted keys never consult the equivocation test at all, which
     # is why the divergence survived a whole commit's worth of mailbox rows.
     #
     # T2c/T2d are demanded too, and were NOT predicted: they were observed and
     # then justified. With `ACCEPT_UNIQUE` no longer unique the two rules emit
     # the SAME term, so the inequality half of those rows -- the half that
     # keeps the inertness claim from being vacuous -- fails. It is worth
     # requiring precisely because it is the tripwire on the tripwire.
     #
     # T7f was also observed rather than predicted, and it is the one that
     # matters most. It is the ROUTE-FREE mailbox world -- no `Send` kind, no
     # `mcap`, lowering under the v1 profile -- so a rule read from the profile,
     # from the mailbox bundle or from `mcap` could not possibly reach it. That
     # it goes red under this mutant is the positive half of the orthogonality
     # claim: the row is not merely insensitive to the forbidden sources, it is
     # genuinely sensitive to the permitted one.
     #
     # T7h joined the set at the Core 0.2.0 cut, and it is worth naming why a
     # REPLAY row catches an ACCEPT mutation. T7h refolds the world under the
     # policy parsed out of the film's own bytes and demands byte-equality with
     # the original. Under this mutant the label is still right -- the world
     # still DECLARES the mailbox policy -- but the trajectory it labels was
     # produced by the wrong seam, so the honest replay and the recorded film
     # disagree. It catches the reduction being wrong THROUGH the film, which
     # is the only way a downstream consumer would ever notice.
     ["T7", "T7f", "T7h", "T2c", "T2d"]),

    ("P11 equivocation rejection forced onto the FROZEN policy",
     "admit_ic.py",
     "ACCEPT_MIN = AcceptRule(AD.ACCEPTANCE_POLICY_ID, False)",
     "ACCEPT_MIN = AcceptRule(AD.ACCEPTANCE_POLICY_ID, True)",
     # The other direction, and the more dangerous one: a "fix" that improves
     # every world instead of the one that asked. `admit_candidate_min_
     # firstreceipt_v1` is FROZEN -- gate 5 of the ruling says its terms and
     # fingerprints may not move -- and the default rule is what every
     # pre-5c caller silently gets. So this mutation is caught by the byte
     # baseline rather than by any behavioural row: `SNAP.snapshot` calls the
     # emitters with no rule, the emitted terms change, and T2 goes red against
     # a file captured before any of this existed. T2c and T2d then say the same
     # thing from the caller's side.
     #
     # T6c is required as well, and it is the row worth reading. Writing this
     # mutation I predicted that ONLY byte rows could catch it -- that under
     # this mutant the mailbox world still behaves correctly and it is merely
     # every OTHER world that quietly changed meaning, with no behavioural row
     # positioned to notice. That was WRONG, and the run said so. T6c asserts
     # what a MAILBOX-FREE world declares, and a mailbox-free world declaring a
     # rule that rejects equivocation is a defect visible at the seam, before
     # any term is emitted. The prediction was wrong in the useful direction:
     # the seam had already been made observable, so the selection is checked
     # where it is MADE and not only where its bytes land.
     ["T2", "T2c", "T2d", "T6c"]),

    ("P12 the rule reaches ACCEPT but not MAP",
     "admit_ic.py",
     "    rule = ACCEPT_MIN if rule is None else rule\n"
     "    unique = rule.reject_equivocal\n"
     '    eqf = BL.dyn_case("eq", prof.FKEY_W)\n'
     '    eq8 = BL.dyn_case("eq", prof.EKEY_W)\n'
     '    ltu = BL.dyn_case("ltu", prof.FKEY_W)',
     "    rule = ACCEPT_MIN if rule is None else rule\n"
     "    unique = False\n"
     '    eqf = BL.dyn_case("eq", prof.FKEY_W)\n'
     '    eq8 = BL.dyn_case("eq", prof.EKEY_W)\n'
     '    ltu = BL.dyn_case("ltu", prof.FKEY_W)',
     # NOT in the ruling, and added because writing the fix made the defect
     # obvious. `ic_accept` and `ic_map` compute per-slot eligibility
     # INDEPENDENTLY -- there is no shared `accept_i` between them, only two
     # copies of the same arithmetic -- so threading the rule into one and
     # forgetting the other is the single most likely way to get this commit
     # wrong. The `ltu` line is carried in the match only to disambiguate:
     # both stages open with the identical two lines, and `mutate_harness`
     # refuses an ambiguous anchor.
     #
     # The resulting machine is exactly the incoherent one the ruling named:
     # ACCEPT refuses the equivocal key a receipt while MAP enqueues its
     # message anyway. T7 catches it on "no MailboxEnqueue", which is why that
     # clause is asserted separately from film equality instead of being left
     # implied by it. T2d catches it at the emitter, before any fold runs.
     #
     # T7f is the third catcher and, again, was not predicted. Its witness is
     # sharper than T7's: the refused claim there is a `SetRotor`, and the row
     # pins `rotor=10,00,00,00`. Under this mutant MAP applies the equivocal
     # rotor and the rotor MOVES -- so the leak is caught as a change to WORLD
     # state, in a world containing no mailbox traffic whatsoever. That is the
     # ruling's "ACCEPT resolves the event key before MAP applies operation-
     # specific behaviour" stated as a failing measurement rather than a claim.
     #
     # T7h joined at the Core 0.2.0 cut, for the same reason it joined P10: the
     # replay is byte-compared against the recorded film, so a MAP that applies
     # an operation ACCEPT refused shows up as a replay that does not reproduce
     # its own recording.
     ["T7", "T7f", "T7h", "T2d"]),

    ("P13 the film's policy label reverted to the module constant",
     "admit.py",
     "                 % (ACCEPTANCE_POLICY_ID if policy_id is None "
     "else policy_id,",
     "                 % (ACCEPTANCE_POLICY_ID,",
     # The Core 0.2.0 change, reverted. This is the pre-0.2.0 film: every
     # mailbox world labels itself with the FROZEN policy while showing
     # behaviour only the other policy can produce.
     #
     # It is in this file to stop T7g and T7h from being decorative. Both are
     # NEW rows asserting something POSITIVE about bytes, and a positive byte
     # assertion is the easiest kind to write vacuously -- T7g would still pass
     # if the label happened to be right for a reason unrelated to the seam.
     #
     # T7h is the row that matters, and it is the one this mutation exists to
     # earn. It replays the world under the policy PARSED OUT OF THE FILM, so
     # under this mutant the parsed label is the frozen seam, the refold takes
     # the leader-min path, and the replay mints a receipt and an enqueue where
     # the recorded film shows a rejection. That is a ReplayBundle whose
     # `policy_ids` field contradicts its own `frames` -- caught as a byte
     # inequality rather than argued.
     #
     # Note the two rows fail for DIFFERENT reasons, which is why both are
     # listed: T7g fails on the label being wrong, T7h on the trajectory the
     # label reconstructs being wrong. A fix that corrected only the string
     # would flip T7g and leave T7h red.
     ["T7g", "T7h"]),

    ("P14 the EventLedger loop put back inside the mailbox block",
     "admit.py",
     "    for e in st.get(\"ledger_entries\", []):\n"
     "        lines.append(_ledger_str(e))",
     "    if mailboxes:\n"
     "        for e in st.get(\"ledger_entries\", []):\n"
     "            lines.append(_ledger_str(e))",
     # The other half of the 0.2.0 film correction, reverted. This restores the
     # pre-0.2.0 gating in which a computed `MailboxReject` is discarded by the
     # renderer whenever the world holds no mailbox bundle.
     #
     # Only T7i catches it, and that is the honest result rather than a thin
     # one. Every OTHER row in this battery uses a mailbox-BEARING world -- T7f
     # deliberately so, since its whole point is a route-free world that still
     # declares the mailbox policy -- and for those the bundle is non-empty, so
     # the gate is satisfied and the mutation is invisible. That is exactly why
     # the defect survived: the gate is wrong only in the configuration nothing
     # was constructing.
     #
     # A single catcher is therefore the measurement, not a gap to paper over.
     # It says the row was necessary: delete T7i and this mutation SURVIVES.
     ["T7i"]),
]


def main():
    # Eleven mutants at roughly ninety seconds each is longer than one sitting,
    # so the run is resumable: naming mutants (`python3 -u mutate51.py P3 P4`)
    # restricts the list to those tags. With no argument the whole list runs,
    # and that is the only form whose verdict line means "ALL CAUGHT".
    picked = sys.argv[1:]
    muts = ([m for m in MUTATIONS if m[0].split()[0] in picked] if picked
            else MUTATIONS)
    if picked and len(muts) != len(picked):
        print("no such mutant: %s" % ", ".join(
            sorted(set(picked) - {m[0].split()[0] for m in muts})))
        return 2
    return run("binding_run51.py", muts, prefix="T")


if __name__ == "__main__":
    sys.exit(main())
