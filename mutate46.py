#!/usr/bin/env python3
"""Mutation harness for binding_run46 (Slice B commit 1).

Every production edit made in this commit is REVERTED, one at a time, in an
isolated copy of the tree. A battery row must then fail. A mutation that nobody
notices is a row that proves nothing -- the same check that caught the vacuous
ordering law in commit 0.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

# Resolved relative to THIS FILE, so the harness runs wherever the packet is
# unpacked. An absolute developer path here would make the packet unrunnable
# for its reviewer, which is the failure `run_l0_sweep.py`'s own docstring
# names: a packet whose contents cannot be run is a claim, not evidence.
ROOT = os.environ.get("TRVM_ROOT") or os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "forge")

# (label, file, old, new, rows that MUST go red)
#
# The FIRST entry is the null mutant. Every "CAUGHT" below is meaningless
# unless an UNMUTATED copy of the tree passes in the same harness -- the first
# run of this harness reported 11/11 caught, and all eleven were the copy
# failing to import `ic_ref` from a sibling directory it did not have.
MUTATIONS = [
    ("M0 NULL MUTANT (control: this one must PASS)",
     "wrl_format.py", "FORMAT_VERSION", "FORMAT_VERSION", []),

    ("M1 drop the validator-owned locator (finding 5.2 reverted)",
     "wrl_canonical.py",
     "primary_locator=ObjectKey(object_id) if object_id else None,",
     "",
     # NOT N4: the omitted-block rule is a SEPARATE rejection site in wrl_ir
     # that builds its own locator, so it survives this mutation. Two sites,
     # two conditions -- worth knowing, and now known.
     ["N8e", "N8f"]),

    ("M2 required `{}` rule switched off",
     "wrl_ir.py",
     "        elif not port_projection(role):",
     "        elif False:",
     ["N4"]),

    ("M3 required `{}` rule widened to every role",
     "wrl_ir.py",
     "        elif not port_projection(role):",
     "        elif True:",
     # N4d is the exact negation of this mutation, so N4d is the row that must
     # name it. It previously could not: its own setup raised and the whole
     # section aborted under N4's name.
     ["N4d"]),

    ("M4 mailbox cfg folds w and cap into one field",
     "wrl_ir.py",
     '"cap": int(kv["cap"]) if "cap" in kv else None}',
     '"cap": int(kv["w"]) if "w" in kv else None}',
     # NOT N2b: an exact fold leaves the swapped pair (8,8)/(4,4) still
     # distinct. N1b (read-back) and N2 (six distinct) are the real catchers.
     ["N1b", "N2"]),

    ("M5 mailbox cfg silently defaults instead of letting the seal judge",
     "wrl_ir.py",
     'cfg = {"w": int(kv["w"]) if "w" in kv else None,\n'
     '                   "cap": int(kv["cap"]) if "cap" in kv else None}',
     'cfg = {"w": int(kv.get("w", 1)), "cap": int(kv.get("cap", 1))}',
     ["N5"]),

    ("M6 emitter vocabulary re-forked (the sixth instance restored)",
     "wrl_format.py",
     "_ROLE_LOWER = {rid: tok for tok, rid in W._ROLE_TOKEN.items()}",
     '_ROLE_LOWER = {"Pulser": "pulser", "Relay": "relay", "Door": "door",\n'
     '               "Spinner": "spinner", "Orb": "orb"}',
     # Caught at IMPORT by wrl_format's own injectivity assertion, strictly
     # before any row runs -- a production invariant, not a battery row. That
     # is the stronger defense, so it is recorded as its own outcome rather
     # than scored against N7c (which would also catch it, given the chance).
     "@import-assert:role lexemes are not injective"),

    ("M7 mailbox emitted without its cap",
     "wrl_format.py",
     'return "(w=%d, cap=%d)" % (cfg["w"], cfg["cap"])',
     'return "(w=%d)" % (cfg["w"],)',
     ["N7"]),

    ("M8 bootstrap tells the old lie about `mailbox`",
     "wrl_ir.py",
     "        elif head in _ROLE_TOKEN:",
     '        elif head in ("__never__",):',
     # NOT N9: the two messages still DIFFER under the lie, they are just both
     # wrong about which situation this is. N9b is the load-bearing row.
     ["N9b"]),

    ("M9 Mailbox given a structural port (D8 stops being a table fact)",
     "wrl_canonical.py",
     '"Mailbox": {"out": (),           "in": ()},',
     '"Mailbox": {"out": ("sig_out",), "in": ()},',
     ["N6", "N6c"]),

    ("M10 mailbox dropped from the plan view (ignored becomes invisible)",
     "wrl_plan.py",
     # The first spelling of this was `{} or {...}`, which is a NO-OP: `{}` is
     # falsy, so `or` returns the original comprehension. It reported SURVIVED
     # and the survivor was the mutation, not the battery.
     "self.mailboxes = {m[\"id\"]: (m[\"w\"], m[\"cap\"])\n"
     "                          for m in plan.get(\"mailboxes\") or ()}",
     "self.mailboxes = {}",
     ["N11b"]),

    ("M11 mailbox lexeme removed from the Core surface table",
     "wrl_ir.py",
     '"orb": "Orb", "mailbox": "Mailbox"}',
     '"orb": "Orb"}',
     ["N1"]),
]


def rows_failed(out):
    return sorted({m.group(1) for m in
                   re.finditer(r"\[FAIL\] (N\d+[a-z]?)\)", out)},
                  key=lambda s: (int(re.match(r"N(\d+)", s).group(1)), s))


def main():
    base = tempfile.mkdtemp(prefix="mut46-")
    ok = True
    for label, fname, old, new, want in MUTATIONS:
        tag = label.split()[0]
        # The battery reaches OUT of forge/ (runtime/python/ic_ref.py,
        # runtime/c/ic32), so the copy has to keep the surrounding tree shape.
        # Only forge/ is duplicated; the siblings are symlinked, which is
        # enough because nothing under test writes to them.
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
            print("  [HARNESS] %-58s anchor x%d in %s -- NOT A RESULT"
                  % (label, txt.count(old), fname))
            ok = False
            continue
        with open(p, "w") as f:
            f.write(txt.replace(old, new))
        env = dict(os.environ, TRVM_SKIP_NATIVE="1")
        r = subprocess.run([sys.executable, "binding_run46.py"], cwd=tree,
                           capture_output=True, text=True, env=env)
        out = r.stdout + r.stderr
        got = rows_failed(out)
        crash = "Traceback" in out
        clean = r.returncode == 0 and not got and not crash
        if isinstance(want, str) and want.startswith("@import-assert:"):
            probe = want.split(":", 1)[1]
            good = probe in out and not got
            note = ("stopped at import by a production assertion (%r)" % probe
                    if good else "expected the import assertion %r" % probe)
        elif not want:                     # the null mutant
            good = clean
            note = "battery green" if clean else "CONTROL BROKEN"
        else:
            # A crash is NOT a pass. It means the mutant never reached the
            # rows, so the rows proved nothing about it; the battery has to
            # NAME the property that broke.
            good = bool(got) and all(w in got for w in want) and not crash
            note = ("crashed -- rows never ran" if crash
                    else ", ".join(got) or "nothing")
        ok = ok and good
        print("  [%s] %-58s -> %s"
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
