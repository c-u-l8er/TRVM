"""mutate_harness.py -- the shared mutation-harness driver.

`mutate46` through `mutate49` each carried their own copy of this driver. That
was survivable while the copies agreed. It stopped being survivable at
`mutate50`, and for a reason worth stating plainly: this file is not a helper,
it is the DEFINITION of what "CAUGHT" means in this track. Four disciplines
live in `run()` and every mutation verdict in the slice depends on all four:

  * M0 is a NULL MUTANT. Without a control, "caught" can just mean "the copy of
    the tree is broken" -- which is what `mutate46`'s first run actually
    reported.
  * A mutation whose anchor does not appear EXACTLY ONCE is NOT A RESULT. It is
    reported as a harness failure, never as a catch and never as a survival.
  * A deliberate `@noop:` mutation must SURVIVE. If a rewrite that changes
    nothing is scored as caught, every other CAUGHT in the run is worthless.
  * A CRASH IS NOT A CATCH. A mutant that dies before the rows execute has been
    proved nothing about; the rows must go red on their own terms.
  * A MUTANT IS CAPPED. Under interaction-calculus reduction the characteristic
    defect of a shape mutation is not an arity error, it is unbounded
    duplication -- `mutate51`'s P2 reached 22.9 GB of RSS and 21 GB of swap
    before it was killed by hand, having taken the machine down with it three
    times. An honest battery in this track peaks near half a gigabyte, so every
    mutant runs under an address-space cap: a diverging mutant dies in seconds
    with `MemoryError`, `section()` turns that into a NAMED red row, and the run
    continues. Without the cap a divergent mutant is not a slow result, it is
    the absence of one.

If those four rules are spelled five times they will disagree exactly once,
quietly, and the run that disagrees will be the one whose result is believed.
So they are spelled here, once, and each `mutate*.py` supplies only what is
actually specific to it: which battery to run, what its rows are called, and
the mutation list.

The extraction is checkable rather than asserted: converting `mutate49` to this
driver must leave its report byte-identical, since the driver is supposed to be
what it was already doing.
"""
import os
import re
import resource
import shutil
import subprocess
import sys
import tempfile

# An honest battery in this track peaks near 0.54 GB, so this is roughly
# fifteenfold headroom -- large enough that no correct mutant is ever capped,
# small enough that a diverging one dies while the machine is still usable.
MEM_CAP_GB = float(os.environ.get("TRVM_MUTANT_MEM_GB", "8"))


def _cap_memory():
    """Cap the mutant's address space (child-side, after fork)."""
    lim = int(MEM_CAP_GB * (1 << 30))
    resource.setrlimit(resource.RLIMIT_AS, (lim, lim))


def tree_root():
    """(ROOT, SRC) for both the developed tree and a flat extraction."""
    root = os.environ.get("TRVM_ROOT") or os.path.dirname(
        os.path.abspath(__file__))
    src = os.path.join(root, "forge") if os.path.isdir(
        os.path.join(root, "forge")) else root
    if src == root:                # unpacked flat: the tree root is the parent
        root = os.path.dirname(src)
    return root, src


def rows_failed(out, prefix="R"):
    """The battery rows that went red, in row order."""
    pat = re.compile(r"\[FAIL\] (%s\d+[a-z]?)\)" % prefix)
    return sorted({m.group(1) for m in pat.finditer(out)},
                  key=lambda s: (int(re.match(r"%s(\d+)" % prefix,
                                              s).group(1)), s))


def run(battery, mutations, prefix="R", tag=None):
    """Apply each mutation to an isolated copy of the tree and run `battery`.

    `mutations` is a list of (label, file, old, new, want) where `want` is the
    rows that MUST go red -- `[]` for the null mutant, or a string beginning
    "@noop:" for a rewrite that must survive.
    """
    root, src = tree_root()
    tag = tag or os.path.splitext(os.path.basename(battery))[0]
    base = tempfile.mkdtemp(prefix="%s-" % tag)
    ok = True
    for label, fname, old, new, want in mutations:
        mtag = label.split()[0]
        # The batteries reach OUT of forge/ (runtime/python/ic_ref.py), so the
        # copy keeps the surrounding tree shape: only forge/ is duplicated,
        # the siblings are symlinked.
        home = os.path.join(base, mtag)
        os.makedirs(home)
        tree = os.path.join(home, "forge")
        shutil.copytree(src, tree,
                        ignore=shutil.ignore_patterns("__pycache__",
                                                      ".forge_projects",
                                                      ".objects", "dist"))
        for sib in os.listdir(root):
            if sib != "forge":
                os.symlink(os.path.join(root, sib), os.path.join(home, sib))
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
        r = subprocess.run([sys.executable, battery], cwd=tree,
                           capture_output=True, text=True, env=env,
                           preexec_fn=_cap_memory)
        out = r.stdout + r.stderr
        got = rows_failed(out, prefix)
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
