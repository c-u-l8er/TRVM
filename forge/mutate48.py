#!/usr/bin/env python3
"""Mutation harness for binding_run48 (Slice B commit 3, the `~~` surface).

Every production edit made in this commit is REVERTED, one at a time, in an
isolated copy of the tree, and a battery row must then go red. A mutation that
nobody notices is a row that proves nothing.

The three disciplines carried from `mutate46`/`mutate47`, and why each exists:

  * M0 is the NULL MUTANT. `mutate46`'s first run reported 11/11 caught and all
    eleven were the isolated copy failing to import a sibling. Without a
    control, "caught" means "the copy is broken".
  * A mutation whose anchor does not appear EXACTLY ONCE is reported as NOT A
    RESULT, never as a pass. A no-op edit that reports SURVIVED is a survivor
    of the harness, not of the battery.
  * A deliberate no-op (`@noop:`) must SURVIVE. If it is scored as caught, the
    battery is red for reasons unrelated to the edit and every other CAUGHT in
    the run is worthless.

A note on GRANULARITY. `binding_run48.section()` converts an unexpected
exception into a named FAIL at SECTION granularity ("Q1) raised ValueError").
Several mutations here are caught that way rather than by the individual row
whose law they break -- because the mutation makes an earlier, eagerly
evaluated row RAISE, so the later rows never run. That is a real, named catch
and it is recorded as such; where it happens the comment says so, so nobody
reads a section-level catch as evidence that a particular row discriminates.
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
     "wrl_ir.py", '_ROUTE_KEYS = ("body",)', '_ROUTE_KEYS = ("body",)', []),

    ("M0b @noop rewrite of the body split (harness self-check)",
     "wrl_ir.py",
     '    parts = tok.split(".")\n    if len(parts) != WC.ROUTE_BODY_LANES:',
     '    parts = list(tok.split("."))\n    if len(parts) != WC.ROUTE_BODY_LANES:',
     "@noop:a rewrite that changes nothing must not be scored as caught"),

    # ------------------------------------------------- the parse branch (Q2)
    ("M1 route branch keyed on a successful MATCH, not on the texture",
     "wrl_ir.py",
     '        if "~~" in line:\n            # Tested BEFORE the edge form',
     '        if _ROUTE_RE.match(line):\n            # Tested BEFORE the edge form',
     # This is the commit-1 `mailbox` defect wearing a new construct: a route
     # with one tilde too few stops being a malformed ROUTE and becomes
     # "unrecognized WRL notation" -- a message that denies the construct
     # exists. All five Q2 rows are the same row name, so one entry.
     ["Q2"]),

    # ------------------------------------------ the required body group (Q1)
    ("M2 a missing body group silently DEFAULTED",
     "wrl_ir.py",
     '            if m.group(4) is None:\n'
     '                raise WrlValidationError(\n'
     '                    WRL_UNSUPPORTED_FEATURE,\n'
     '                    "async route %s ~~%s~~> %s has no body; the body '
     'group is "\n'
     '                    "REQUIRED (a route with an implied body would put an "\n'
     '                    "identity-bearing field in the compiler and not in '
     'the "\n'
     '                    "source)" % (src, tag, dst))\n'
     '            kv, flags = _paren_kv(m.group(4))',
     '            kv, flags = _paren_kv(m.group(4) or "(body=0.0.0.0)")',
     # The exact defect Q1 names: an identity-bearing field that lives in the
     # compiler instead of in the source. Note that it does NOT crash and does
     # NOT produce an illegal world -- it produces a legal world the author
     # did not write, which is why the row had to exist.
     ["Q1"]),

    ("M3 an EMPTY body group `()` silently DEFAULTED",
     "wrl_ir.py",
     '            if "body" not in kv:\n'
     '                raise WrlValidationError(\n'
     '                    WRL_UNSUPPORTED_FEATURE,\n'
     '                    "async route %s ~~%s~~> %s is missing `body`"\n'
     '                    % (src, tag, dst))',
     '            kv.setdefault("body", "0.0.0.0")',
     ["Q1b"]),

    ("M4 unknown keys tolerated in the body group",
     "wrl_ir.py",
     "            unknown = sorted(set(kv) - set(_ROUTE_KEYS)) + sorted(flags)",
     "            unknown = []",
     ["Q1c"]),

    ("M5 body arity forked onto the ROTOR parser",
     "wrl_ir.py",
     '                             "body": _body_dots(kv["body"])})',
     '                             "body": _rotor_dots(kv["body"])})',
     # Caught at SECTION granularity: `_rotor_dots` has no int() guard, so Q1e
     # gets a bare ValueError instead of a typed rejection and the section
     # aborts. That IS the law Q1e states ("never a bare ValueError escaping
     # the parser"), but the catch is the section's, not Q1e's -- and Q1d
     # cannot see this at all, because the rotor message happens to contain
     # the same "must have 4 lanes" while saying `rotor` about a body. Exactly
     # the drift `_body_dots`'s docstring refuses.
     ["Q1"]),

    ("M6 the parser RESTATES the seal's body range, with a global bound",
     "wrl_ir.py",
     '            g.routes.append({"source_id": src, "route_tag": tag,',
     '            if any(v > 255 for v in _body_dots(kv["body"])):\n'
     '                raise WrlValidationError(WRL_NUMERIC_RANGE, "too big")\n'
     '            g.routes.append({"source_id": src, "route_tag": tag,',
     # The duplication Q7 exists to forbid. A second copy of the range rule
     # cannot know the TARGET mailbox's width, so it must invent a global one
     # -- and a global bound makes the same body legal at w=8 and at w=16,
     # which is the negation of Q7h/Q7j. Caught at section granularity because
     # Q7g raises first.
     ["Q7"]),

    # ------------------------------------------------- the emitter (Q3, Q5)
    ("M7 the emitter stops writing routes",
     "wrl_format.py",
     "    routes = WC.routes_of(cg)\n    if routes:",
     "    routes = WC.routes_of(cg)\n    if False:",
     # NOT Q5: a formatter that drops routes leaves every route-FREE world
     # byte-identical, which is precisely why the c2 pins alone could never
     # have caught it.
     ["Q3", "Q3c", "Q3d", "Q3e"]),

    ("M8 the emitter reverses the body lanes",
     "wrl_format.py",
     '    return ".".join(str(int(v)) for v in body)',
     '    return ".".join(str(int(v)) for v in body[::-1])',
     # The dangerous shape, not the loud one: four lanes still emitted, still
     # parseable, still a LEGAL world -- a different one.
     ["Q3", "Q3b", "Q3d", "Q3e"]),

    ("M9 the route separator emitted unconditionally",
     "wrl_format.py",
     '    routes = WC.routes_of(cg)\n    if routes:\n        out.append("")',
     '    routes = WC.routes_of(cg)\n    if True:\n        out.append("")',
     # This one SURVIVED with NOTHING red, and it is the most useful thing the
     # harness found. Whitespace is non-semantic, so no identity moves and
     # Q5/Q5b stayed green; and the formatter is graph->text, not text->text,
     # so the extra blank is a FIXED POINT and Q3b stayed green too -- the
     # prediction that it would catch this was simply wrong. Meanwhile the
     # canonical BYTES of every route-free world in the tree had moved, which
     # is the exact law `wrl_format`'s own comment claims ("no blank
     # separator, no empty section") and which nothing checked. Q5d is that
     # row, and it exists because of this line.
     ["Q5d"]),

    # ------------------------------------------------ the draft guard (Q9)
    ("M10 new_draft's loss guard removed",
     "wrl_draft.py",
     "    if draft.candidate_error is not None \\\n"
     "            or draft.candidate_semantic_id != base:",
     "    if False:",
     # Reverts commit 3 to the measured defect: opening the one-route world
     # yields the route-free twin with no error at all.
     ["Q9", "Q9b"]),

    ("M11 replace_world_source's loss guard removed",
     "wrl_draft.py",
     "    loss = _draft_loss(g, new_objects, new_edges, draft.profile_id)\n"
     "    if loss is not None:",
     "    loss = None\n    if loss is not None:",
     # Q9e was expected here and stayed GREEN, which is the finding. The
     # route-free twin of Q9d's source IS the draft's current world, so a
     # missing guard falls through to the semantic-noop branch and leaves the
     # draft at revision 0 with the right candidate -- "untouched" for the
     # wrong reason. Q9i/Q9j were added to make the substitution visible by
     # pasting a source whose lost world is a DIFFERENT world.
     ["Q9d", "Q9i", "Q9j"]),

    ("M12 the loss guard stops deferring to the seal",
     "wrl_draft.py",
     "    try:\n        want = W.lower_graph(g).semantic_artifact_id\n"
     "    except WC.WrlUnsupported:\n        return None",
     "    want = W.lower_graph(g).semantic_artifact_id",
     # An ordinary illegal world (a dangling edge) now dies INSIDE the loss
     # guard instead of being diagnosed as itself. Q9g is the row; the catch
     # lands at section granularity because the exception escapes the door.
     ["Q9"]),

    # ---------------------------------------- the writer reservation (Q8)
    ("M13 the writer-15 reservation switched off",
     "wrl_scenario.py",
     "            if c.get(\"writer_id\") == WC.ROUTE_WRITER_ID:",
     "            if False:",
     ["Q8", "Q8f", "Q8g"]),

    ("M14 the reservation applied to EVERY world (the ruled-out narrowing)",
     "wrl_scenario.py",
     # The guard is spelled TWICE in this module now -- a later commit added a
     # second, entirely legitimate route-bearing check for the mailbox capacity
     # bound -- so the anchor carries the docstring line that precedes THIS one.
     # An anchor that matches twice is not a weaker result, it is no result at
     # all, and the harness says so rather than mutating the first hit.
     'here, which is how the same question ends up answered four ways."""\n'
     "    if not WC.routes_of_artifact(artifact):",
     'here, which is how the same question ends up answered four ways."""\n'
     "    if False:",
     # The ruling forbids narrowing ScenarioV1 globally. This mutation is what
     # that narrowing looks like from the outside: writer 15 stops being legal
     # against a route-FREE world, which is every world shipped so far. It was
     # first reported as "Q8 raised" -- the section guard renaming Q8b's
     # failure after its neighbour, so a reservation that had been made too
     # STRONG read as a reservation that was broken. Q8b/Q8c are callables now
     # and the row keeps its own name.
     ["Q8b"]),

    ("M15 the composed door drops the reservation half",
     "wrl_scenario.py",
     "    check_world_binding(scenario, world_semantic_id)\n"
     "    check_route_writer_reservation(scenario, artifact)",
     "    check_world_binding(scenario, world_semantic_id)",
     # Both halves still exist and are still individually correct -- Q8f/Q8g
     # call the reservation by name and stay green. Only the row that goes
     # through the door production uses can see this.
     ["Q8"]),

    ("M16 the composed door drops the BINDING half",
     "wrl_scenario.py",
     "    check_world_binding(scenario, world_semantic_id)\n"
     "    check_route_writer_reservation(scenario, artifact)",
     "    check_route_writer_reservation(scenario, artifact)",
     # The mirror of M15, and the reason Q8i exists: adding a check to a door
     # is exactly when the check already there gets displaced.
     ["Q8i"]),

    ("M17 routes_of_artifact forgets the canonical-omission rule",
     "wrl_canonical.py",
     '    return list(artifact.get("async_routes") or ())',
     '    return list(artifact["async_routes"])',
     # The accessor exists BECAUSE the artifact omits the field when empty. A
     # consumer that spells the lookup itself gets this wrong on route-free
     # worlds, which is the majority case.
     ["Q8"]),
]


def rows_failed(out):
    return sorted({m.group(1) for m in
                   re.finditer(r"\[FAIL\] (Q\d+[a-z]?)\)", out)},
                  key=lambda s: (int(re.match(r"Q(\d+)", s).group(1)), s))


def main():
    base = tempfile.mkdtemp(prefix="mut48-")
    ok = True
    for label, fname, old, new, want in MUTATIONS:
        tag = label.split()[0]
        # The battery reaches OUT of forge/ (runtime/python/ic_ref.py), so the
        # copy keeps the surrounding tree shape: only forge/ is duplicated,
        # the siblings are symlinked.
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
        r = subprocess.run([sys.executable, "binding_run48.py"], cwd=tree,
                           capture_output=True, text=True, env=env)
        out = r.stdout + r.stderr
        got = rows_failed(out)
        crash = "Traceback" in out
        clean = r.returncode == 0 and not got and not crash
        if isinstance(want, str) and want.startswith("@noop:"):
            good = clean
            note = ("survived, as a no-op must" if clean
                    else "a NO-OP was 'caught' -- this run proves nothing")
        elif not want:                     # the null mutant
            good = clean
            note = "battery green" if clean else "CONTROL BROKEN"
        else:
            # A crash is NOT a pass: the mutant never reached the rows, so the
            # rows proved nothing about it. `section()` is what keeps an
            # exception NAMED rather than a traceback, and a traceback that
            # escapes even that is a broken copy.
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
