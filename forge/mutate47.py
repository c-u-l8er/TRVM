#!/usr/bin/env python3
"""Mutation harness for binding_run47 (Slice B commit 2).

Every production edit made in this commit is REVERTED, one at a time, in an
isolated copy of the tree. A battery row must then fail. A mutation that nobody
notices is a row that proves nothing.

Two lessons from `mutate46.py` are carried forward and are the reason M0 and the
anchor check exist:

  * M0 is the NULL MUTANT. Its first run reported 11/11 caught, and all eleven
    were the isolated copy failing to import a sibling package. Without a
    control, "caught" means "the copy is broken".
  * A mutation whose anchor does not appear EXACTLY ONCE is reported as
    NOT A RESULT, never as a pass. A no-op edit that reports SURVIVED is a
    survivor of the harness, not of the battery.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.environ.get("TRVM_ROOT") or os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "forge") if os.path.isdir(os.path.join(ROOT, "forge")) \
    else ROOT
if SRC == ROOT:                    # unpacked flat: the tree root is the parent
    ROOT = os.path.dirname(SRC)

# (label, file, old, new, rows that MUST go red)
MUTATIONS = [
    ("M0 NULL MUTANT (control: this one must PASS)",
     "wrl_canonical.py", "MAX_ASYNC_ROUTES = 6", "MAX_ASYNC_ROUTES = 6", []),

    # ---------------------------------------------- the derived constants (P0)
    ("M1 route budget decoupled from the claim-fact budget",
     "wrl_canonical.py", "MAX_ASYNC_ROUTES = 6", "MAX_ASYNC_ROUTES = 7",
     # ONLY P0. P6e/P6f build their route lists FROM `WC.MAX_ASYNC_ROUTES`, so
     # they are relative laws -- "the bound, whatever it is, is enforced" --
     # and cannot see the bound move. That is the correct division of labour
     # and not a weakness: spelling `7` in the battery would fork the constant
     # a third time. P0 is the only row that can catch this, which is exactly
     # why the derivation pin had to exist.
     ["P0"]),

    ("M2 reserved writer moved off the top of the namespace",
     "wrl_canonical.py", "ROUTE_WRITER_ID = 15", "ROUTE_WRITER_ID = 14",
     # Same shape as M1: P5c checks that the sequence numbering is stable
     # under `WC.ROUTE_WRITER_ID`, not that the writer is 15.
     ["P0b"]),

    ("M3 body domain off by one at the top of the lane",
     "wrl_canonical.py",
     "and 0 <= v < (1 << width) for v in body))",
     "and 0 <= v <= (1 << width) for v in body))",
     ["P0c", "P4c"]),

    ("M4 bools admitted as body lanes",
     "wrl_canonical.py",
     "and all(isinstance(v, int) and not isinstance(v, bool)",
     "and all(isinstance(v, int)",
     ["P0c"]),

    ("M5 body lane count widened past the Send payload",
     "wrl_canonical.py", "ROUTE_BODY_LANES = 4", "ROUTE_BODY_LANES = 5",
     ["P0c", "P0d"]),

    # ------------------------------------------------ the projection (P1-P3)
    ("M6 routes never reach the artifact (the projection dropped)",
     "wrl_ir.py",
     '        art["async_routes"] = [dict(r) for r in\n'
     '                               sorted(routes, key=WC.route_key)]',
     "        pass",
     # NOT P3: a dropped projection leaves route-FREE worlds untouched, which
     # is precisely why P3 alone could never have caught it.
     ["P1", "P2d", "P4"]),

    ("M7 the empty projection is EMITTED instead of omitted",
     "wrl_canonical.py",
     "        if croutes:\n            cart[\"async_routes\"] = croutes",
     "        cart[\"async_routes\"] = croutes",
     # This is the mutation P3 exists for: it moves the bytes of every
     # route-free world in the tree without touching a single route. Only P2
     # and P3 are required because `_seal` re-validates the canonical form, so
     # the emitted `[]` raises and the SECTION guard reports the section name
     # -- P3b/P3c never get to run. A section-level catch is still a named
     # catch; demanding the later rows would be demanding that the battery
     # keep running after the identity spine has started refusing its own
     # output.
     ["P2", "P3"]),

    ("M8 `async_routes: []` tolerated as a second spelling",
     "wrl_canonical.py",
     "        if not routes:\n            _fail(WRL_MALFORMED_ARTIFACT,",
     "        if False:\n            _fail(WRL_MALFORMED_ARTIFACT,",
     ["P2b"]),

    # ----------------------------------------------- the locator + order (P4-P5)
    ("M9 RouteKey overloaded to include the body (ruling Q2 reverted)",
     "wrl_canonical.py",
     'class RouteKey(namedtuple("RouteKey", "source_id route_tag mailbox_id")):',
     'class RouteKey(namedtuple("RouteKey", "source_id route_tag mailbox_id body")):',
     # A four-field RouteKey makes `route_key()` raise on a three-field call,
     # so this is caught by ARITY rather than by the law P4b states -- P4b
     # cannot run, because building the key is the first thing it does. The
     # catch is real and it is NAMED (the P4 section), and it is recorded as
     # arity here so nobody reads it as evidence that P4b discriminates a
     # body-bearing locator from a body-free one.
     ["P4"]),

    ("M10 canonical route order left to the author",
     "wrl_canonical.py",
     "    cg.routes = sorted((_canon_route(r) for r in routes_of(g)), "
     "key=route_key)",
     "    cg.routes = [_canon_route(r) for r in routes_of(g)]",
     # This one SURVIVED the first run, with nothing red at all, and it is the
     # most useful thing the harness found. `graph_to_ir` sorts again on its
     # own path and `route_claim_identity` sorts internally, so world identity
     # AND claim identity both survived -- the canonicalizer's sort had no
     # observable whatsoever. The answer was not to delete it (commit 3's
     # formatter reads exactly this list) but to state the law it belongs to:
     # a canonical form is a NORMAL FORM. P5d is that row, and it exists
     # because of this line.
     ["P5d"]),

    # --------------------------------------------------- the rejections (P6)
    ("M11 duplicate RouteKey rule switched off",
     "wrl_canonical.py", "        if key in seen:", "        if False:",
     ["P6", "P6b", "P6c", "P6d"]),

    ("M12 budget judged BEFORE duplicates",
     "wrl_canonical.py",
     "    if len(routes) > MAX_ASYNC_ROUTES:",
     "    if True:\n        pass\n    if len(routes) > MAX_ASYNC_ROUTES:",
     # A no-op by construction -- included as a HARNESS self-check: it must
     # report NOT A RESULT or SURVIVED, never CAUGHT. See the note in main().
     "@noop:reordering that changes nothing must not be scored as caught"),

    ("M13 source-role rule switched off",
     "wrl_canonical.py",
     '        if role_of[src] != "Pulser":', "        if False:",
     ["P6j"]),

    # Both anchors below were RE-SPELLED: the one-shot test used to be written
    # inline against `clock`, and a later commit moved it behind the shared
    # `once_epoch()` accessor -- "written once and read twice" -- so the old
    # spellings matched nothing and both rows reported NOT A RESULT. The rules
    # they attack are unchanged; only the words are.
    ("M14 one-shot rule switched off (a recurring route admitted)",
     "wrl_canonical.py",
     "        if fires_at is None:", "        if False:",
     # UNVERIFIED on a quiet tree: the only run of the re-spelled anchor gave
     # P6 rather than P6k, and that run was contaminated. P6k is the original
     # intent and stands until it is re-measured.
     ["P6k"]),

    ("M15 `once(0)` route admitted (a world dead by construction)",
     "wrl_canonical.py", "        if fires_at < 1:", "        if False:",
     ["P6l"]),

    ("M16 target-role rule switched off",
     "wrl_canonical.py",
     "        if role_of[mb] != MAILBOX_ROLE:", "        if False:",
     ["P6i"]),

    ("M17 body bound read from a global instead of the target mailbox",
     "wrl_canonical.py",
     '        width = cfg_of[mb].get("w")',
     "        width = 32",
     # P4c/P4d are the exact negation: the same body must be legal at w=16 and
     # illegal at w=8. A global bound makes both legal.
     ["P4c"]),

    ("M17b width guard removed from route_body_in_range",
     "wrl_canonical.py",
     "    return (isinstance(width, int) and not isinstance(width, bool)\n"
     "            and width > 0\n            and isinstance(body,",
     "    return (isinstance(body,",
     # The guard exists ONLY to keep a weakened role rule reportable, so on an
     # otherwise-correct tree it is invisible -- it is a defensive branch, and
     # a defensive branch that no test can reach is a claim. P0c reaches it by
     # passing a non-int width directly.
     ["P0c"]),

    # ------------------------------------------------------- the plan (P7-P8)
    ("M18 the plan stops carrying routes",
     "wrl_plan.py", '        "async_routes": routes,', '        "async_routes": [],',
     ["P7", "P7b"]),

    ("M19 the plan reconstruction forgets routes",
     "wrl_plan.py",
     '    if plan.get("async_routes"):\n'
     '        art["async_routes"] = [dict(r) for r in plan["async_routes"]]',
     "    pass",
     # The load-bearing one: without it NO route-bearing world compiles at all.
     ["P7b", "P7c"]),

    ("M20 the artifact entry point stops passing routes to the builder",
     "wrl_plan.py",
     '                            mailboxes, art.get("async_routes"))',
     "                            mailboxes, None)",
     ["P7", "P7b"]),

    ("M21 plan route order left unchecked",
     "wrl_plan.py",
     "    if keys != sorted(keys):",
     "    if False:",
     ["P7f-order"]),

    ("M22 plan route duplicates left unchecked",
     "wrl_plan.py",
     "    if len(set(keys)) != len(keys):",
     "    if False:",
     ["P7f-dup"]),

    ("M23 plan route endpoints left unchecked",
     "wrl_plan.py",
     '        if r["mailbox_id"] not in mb_ids:',
     "        if False:",
     ["P7f-target"]),

    ("M24 plan route bodies left unchecked",
     "wrl_plan.py",
     '        if not WC.route_body_in_range(widths.get(r["mailbox_id"]), '
     'r["body"]):',
     "        if False:",
     ["P7f-body"]),

    ("M25 async_routes dropped from the strict plan key set",
     "wrl_plan.py", '              "async_routes",\n', "",
     # The plan's EXACT-key-set gate turns the now-unknown field into a typed
     # rejection at the FIRST plan built, so the P7 section aborts and its
     # later rows never run. Named catch, section granularity.
     ["P7"]),

    # -------------------------------------------------------- the oracle (P8)
    ("M26 commit 4's route-refusal lift reverted (the oracle refuses again)",
     "wrl_ir.py",
     # RE-SPELLED. The original mutation switched OFF the refusal that
     # `ir_to_fixture` used to raise on a route-bearing artifact -- and commit 4
     # deleted that refusal outright, as the ruling authorized, so the anchor
     # matched nothing and the row was reported NOT A RESULT rather than as a
     # catch or a survival. A mutation whose subject no longer exists is dead
     # weight that reads as coverage, so it is re-aimed at what replaced it.
     #
     # What replaced the refusal is a CLAIM: a route is not structure, so the
     # Fixture of a route-bearing world is exactly its route-free twin's. P8d
     # measures that claim by collapsing every variant's Fixture to one plan
     # digest. Restoring the refusal is therefore the sharpest attack on it --
     # the inverse of the authorized lift, and the exact mirror of `mutate51`'s
     # P1. `rep`'s callable form catches the typed raise and keeps the row named
     # as itself, so this is a named catch and not an aborted section.
     "    pulsers, relays, doors, spinners, orbs, configurable = \\",
     '    if art.get("async_routes"):\n'
     "        raise WrlValidationError(WRL_UNSUPPORTED_FEATURE,\n"
     '                                 "adapter refuses a route-bearing world")\n'
     "    pulsers, relays, doors, spinners, orbs, configurable = \\",
     # UNVERIFIED on a quiet tree. A clean run gave P8d, a run taken while
     # another session was editing `forge/` gave P8 and P10; the row list below
     # is the clean one. Re-measure before this suite's verdict is quoted.
     ["P8d"]),
]


def rows_failed(out):
    return sorted({m.group(1) for m in
                   re.finditer(r"\[FAIL\] (P\d+[a-z]?(?:-[a-z]+)?)\)", out)},
                  key=lambda s: (int(re.match(r"P(\d+)", s).group(1)), s))


def main():
    base = tempfile.mkdtemp(prefix="mut47-")
    ok = True
    for label, fname, old, new, want in MUTATIONS:
        tag = label.split()[0]
        # The battery reaches OUT of forge/ (runtime/python/ic_ref.py,
        # runtime/c/ic32), so the copy keeps the surrounding tree shape: only
        # forge/ is duplicated, the siblings are symlinked.
        home = os.path.join(base, tag)
        os.makedirs(home)
        tree = os.path.join(home, "forge")
        shutil.copytree(SRC, tree,
                        ignore=shutil.ignore_patterns("__pycache__",
                                                      ".forge_projects",
                                                      ".objects", "dist"))
        for sib in os.listdir(ROOT):
            if sib != "forge":
                os.symlink(os.path.join(ROOT, sib), os.path.join(home, sib))
        p = os.path.join(tree, fname)
        with open(p) as f:
            txt = f.read()
        if txt.count(old) != 1:
            print("  [HARNESS] %-62s anchor x%d in %s -- NOT A RESULT"
                  % (label, txt.count(old), fname))
            ok = False
            continue
        with open(p, "w") as f:
            f.write(txt.replace(old, new))
        env = dict(os.environ, TRVM_SKIP_NATIVE="1")
        r = subprocess.run([sys.executable, "binding_run47.py"], cwd=tree,
                           capture_output=True, text=True, env=env)
        out = r.stdout + r.stderr
        got = rows_failed(out)
        crash = "Traceback" in out
        clean = r.returncode == 0 and not got and not crash
        if isinstance(want, str) and want.startswith("@noop:"):
            # A deliberate no-op. It must SURVIVE. If it is reported as caught,
            # the battery is failing for a reason unrelated to the edit, and
            # every other "CAUGHT" in this run is suspect.
            good = clean
            note = ("survived, as a no-op must" if clean
                    else "a NO-OP was 'caught' -- this run proves nothing")
        elif not want:                     # the null mutant
            good = clean
            note = "battery green" if clean else "CONTROL BROKEN"
        else:
            # A crash is NOT a pass: the mutant never reached the rows, so the
            # rows proved nothing about it. The battery has to NAME the
            # property that broke.
            good = bool(got) and all(w in got for w in want) and not crash
            note = ("crashed -- rows never ran" if crash
                    else ", ".join(got) or "nothing")
        ok = ok and good
        print("  [%s] %-62s -> %s"
              % ("CAUGHT  " if good else "SURVIVED", label, note))
        if want and not isinstance(want, str) and got \
                and not all(w in got for w in want):
            print("            expected at least %s" % ", ".join(want))
    print()
    print("MUTATION VERDICT: %s" % ("ALL CAUGHT" if ok else "SURVIVORS"))
    shutil.rmtree(base, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
