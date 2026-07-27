#!/usr/bin/env python3
"""Mutation harness for binding_run53 (Slice B commit 5d, freeze integrity).

Every API edit commit 5d made is REVERTED, one at a time, in an isolated copy
of the tree, and an F-row must then go red. The four disciplines -- null
control, anchor-exactly-once, @noop-must-survive, crash-is-not-a-catch -- live
in `mutate_harness.run`.

WHAT IS DIFFERENT ABOUT THIS ONE, and it is the thing to read before the list.

The defect 5d fixed was **a permission, not a behaviour**. `admit_step` took a
`policy_id` that no caller in the tree ever passed wrongly; every trajectory was
correct, every film was right, and every battery was green. So the mutations
below are unusual for this track: **most of them change no output at all.**
Reverting the split restores a machine that computes exactly what it computes
now. Nothing is miscomputed, and no row about bytes can see it.

That is why F7's rows assert about SIGNATURES. It is an uncomfortable kind of
row to write -- it looks like testing the spelling of the code rather than what
the code does -- and it is the only kind that works here, because the property
being frozen is *what a caller is able to ask for*, and a caller who never asks
leaves no trace. The general statement, recorded in §16.3: agreement among
implementations cannot see a shared misreading, and agreement among CALL SITES
cannot see an API that permits one.

The consequence for this file is that N1 and N4 are caught by exactly one row
each, and that is the measurement rather than a gap. A single catcher says the
row was necessary: delete F7a and N1 SURVIVES, silently, forever.

    N0   null control (must pass)
    N0b  @noop a rename that changes nothing (harness self-check)
    N1   `admit_step` regains its `policy_id` parameter
    N2   the sealed seam accepts a bare policy id again
    N3   replay reconciles a mismatch instead of refusing it
    N4   the probe accepts `None`, becoming a second spelling of `admit_step`
    N5   `verify_replay_policy` drops the field tag
    N6   binding_run49's dispatch collapsed from three cases back to two

N6 is the regression this commit actually shipped and had to fix mid-flight,
preserved as a mutant so it cannot come back unnoticed.

DOCUMENTARY ROWS ARE NOT MUTATED HERE, deliberately. `mutate_harness` copies
`forge/` and SYMLINKS its siblings, so a mutation naming `../WRL_CORE_0.2.md`
would write through the symlink into the real document -- in a tree that
several sessions edit at once. F1-F6's negative controls are therefore in
`binding_run53.fn_negative_controls`, which corrupts a parsed copy in memory
and touches no file.

Run:  python3 -u mutate53.py          (or `mutate53.py N1 N3` to resume)
"""
import sys

from mutate_harness import run

MUTATIONS = [
    ("N0 NULL MUTANT (control: this one must PASS)",
     "admit.py",
     "    return _admit_step_with_policy(state, batch, epoch, fx, None)",
     "    return _admit_step_with_policy(state, batch, epoch, fx, None)", []),

    ("N0b @noop the private reduction's parameter renamed (self-check)",
     "wrl_fold.py",
     "def verify_replay_policy(artifact, recorded_policy_id):",
     "def verify_replay_policy(artifact, recorded_policy_id):  # noqa: E501",
     # A trailing comment changes the bytes of the file and nothing else. If
     # the harness scored this as caught, every CAUGHT below would be worthless.
     "@noop:a comment is not a semantics"),

    # ------------------------------------------------- the production seam
    ("N1 `admit_step` regains its policy parameter",
     "admit.py",
     "def admit_step(state, batch, epoch, fx):",
     "def admit_step(state, batch, epoch, fx, policy_id=None):",
     # THE defect, restored exactly as it stood through 0.2.0: a default of
     # None, so every existing caller behaves identically and every trajectory
     # in the tree is byte-for-byte what it was. Nothing miscomputes. The world
     # is simply once again executable under semantics it did not seal, by any
     # caller who passes a fifth argument.
     #
     # Only F7a catches it, and only because F7a reads the SIGNATURE. That is
     # the whole argument of this commit compressed into one mutant: the row
     # that looks like it is testing spelling is the row standing between the
     # freeze and a machine that contradicts it. Every behavioural row in the
     # entire tree stays green under this mutation -- which is precisely how
     # the defect survived 0.2.0's review in the first place.
     ["F7a"]),

    ("N2 the sealed seam accepts a bare policy id again",
     "wrl_fold.py",
     "    if not isinstance(seams, RuntimeSeamsV1):",
     "    if False:",
     # The type precondition removed. `seams.admit_policy_id` would then fail
     # on a bare string, so the mutation also has to be reachable -- it is,
     # because F7c passes `AD.MAILBOX_POLICY_ID` and a string has no such
     # attribute, giving an AttributeError inside the row rather than the
     # typed refusal the law promises. `rep`'s callable form contains it as a
     # NAMED red row, which is why F7c is written with a lambda: an escaping
     # exception would be scored as proving nothing.
     ["F7c"]),

    # ------------------------------------------------- the replay refusal
    ("N3 replay reconciles a policy mismatch instead of refusing it",
     "wrl_fold.py",
     "    if recorded_policy_id != sealed:",
     "    if False:",
     # §8c consequence 2 inverted. The bundle's recorded policy is silently
     # replaced by the seal, which is the plausible-looking wrong fix: it
     # "repairs" the bundle and reproduces frames that the recorded trajectory
     # never produced. Both F8b and F8c catch it, and they are listed together
     # because they fail for different inputs -- a wrong policy and a missing
     # one -- and a fix that special-cased only the first would flip one.
     ["F8b", "F8c"]),

    ("N4 the probe accepts `None`, becoming a second spelling of admit_step",
     "admit.py",
     "    if policy_id is None:\n        raise ValueError(",
     "    if False:\n        raise ValueError(",
     # The seam stops being greppable. With None admitted, `admit_policy_probe`
     # and `admit_step` are two names for one function, and the property §8c
     # actually buys -- that every probe call site is a place where someone
     # chose a policy BY HAND -- silently stops holding. No trajectory moves.
     ["F9c"]),

    ("N5 the replay refusal drops its field tag",
     "wrl_fold.py",
     '                 field_path="policy_ids.admit_policy_id")',
     "                 )",
     # The refusal still fires and still names the right code; only the
     # structured locator is gone, so a diagnostic consumer must parse English
     # to find out which of the two disagreeing sources to point at. F8d is the
     # only row that can see this, and it can only see it because it asserts on
     # `e.field_path` rather than on `str(e)` -- the first cut asserted on the
     # message and would have SURVIVED this mutant.
     ["F8d"]),

    # ------------------------------------------------- the dispatch itself
    ("N6 binding_run49's dispatch collapsed from three cases back to two",
     "binding_run49.py",
     "        elif policy is None:\n"
     "            claim, cfg, resets = AD.admit_step(claim, batch, epoch0 + e, fx)\n"
     "        else:",
     "        elif False:\n"
     "            claim, cfg, resets = AD.admit_step(claim, batch, epoch0 + e, fx)\n"
     "        else:",
     # The regression this commit shipped and fixed mid-flight, kept as a
     # mutant. `policy=None` NAMES the frozen policy; routing it to the probe,
     # which refuses None by contract, turns a legitimate caller into a
     # ValueError. It broke T4, R7 and R11 when it happened, and F9d is the row
     # that now stands where the accident was.
     ["F9d"]),
]


def main():
    picked = sys.argv[1:]
    muts = ([m for m in MUTATIONS if m[0].split()[0] in picked] if picked
            else MUTATIONS)
    if picked and len(muts) != len(picked):
        print("no such mutant: %s" % ", ".join(
            sorted(set(picked) - {m[0].split()[0] for m in muts})))
        return 2
    return run("binding_run53.py", muts, prefix="F")


if __name__ == "__main__":
    sys.exit(main())
