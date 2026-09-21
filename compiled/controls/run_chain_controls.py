#!/usr/bin/env python3
"""run_chain_controls.py -- can `executor_chain.py` fail? (`README.md` §2m)

    python3 -B controls/run_chain_controls.py

A battery that has only ever been green is a battery nobody has shown can go red. Two mutants over a copy of
`compiled/`, chosen to be a matched pair rather than a list:

  * `reader-swaps-the-two-bool-binders` MUST diverge -- it is a real, quiet corruption of every bit the reader
    takes in, the exact failure the chain exists to catch, and it is invisible to a check that only looks at one
    job's output because the printer would still print whatever the step was handed.
  * `reader-allows-a-trailing-byte` MUST NOT -- dropping the E_TRAIL check loosens what the reader ACCEPTS without
    changing what it computes for input it already accepted. A battery that went red on this one would be a
    tripwire for any edit rather than a check on the trajectory, and would tell us nothing when it fired.

The copy is a sibling of `compiled/` inside the TRVM tree, because the harness resolves `../forge` relative to
itself -- the resident controls' runner learned that the expensive way.
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
TRVM = os.path.dirname(SRC)
SUMMARY = os.path.join(HERE, "CHAIN_SUMMARY.txt")

CONTROLS = [
    ("unmutated", None, None, None, "AGREE"),
    ("reader-swaps-the-two-bool-binders", "print_state.c",
     "        if (got == n0) return 1;\n        if (got == n1) return 0;",
     "        if (got == n0) return 0;\n        if (got == n1) return 1;", "DIVERGE"),
    ("reader-allows-a-trailing-byte", "print_state.c",
     "    if (w.pos != w.in_len) return E_TRAIL;      /* it matched, and then there was more */",
     "    if (0) return E_TRAIL;", "AGREE"),
]


def main():
    lines = []
    for name, fname, needle, repl, expect in CONTROLS:
        work = os.path.join(TRVM, ".chain-control-%d" % os.getpid())
        shutil.rmtree(work, ignore_errors=True)
        os.makedirs(work)
        try:
            for f in os.listdir(SRC):
                if f.endswith((".py", ".c", ".json")):
                    shutil.copy2(os.path.join(SRC, f), work)
            if fname:
                path = os.path.join(work, fname)
                s = open(path).read()
                n = s.count(needle)
                if n != 1:
                    lines.append("control=%-38s PATCH REFUSED (%d occurrences)" % (name, n))
                    print(lines[-1], flush=True)
                    continue
                open(path, "w").write(s.replace(needle, repl))
            r = subprocess.run([sys.executable, "-B", os.path.join(work, "executor_chain.py"),
                                "--out", os.path.join(work, "out.json")], cwd=work,
                               capture_output=True, timeout=1800,
                               env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            log = (r.stdout + r.stderr).decode(errors="replace")
            agreed = "EVERY EPOCH OF EVERY WORLD AGREES" in log
            got = "AGREE" if agreed else "DIVERGE"
            div = sorted({m.group(1) for m in re.finditer(r"DIVERGED@(\d+)", log)})
            lines.append("control=%-38s %-8s expected %-8s %s%s" % (
                name, got, expect, "AS-EXPECTED" if got == expect else "MISMATCH",
                ("   first divergence at epoch " + ",".join(div)) if div else ""))
        finally:
            shutil.rmtree(work, ignore_errors=True)
        print(lines[-1], flush=True)
    with open(SUMMARY, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("->", SUMMARY)
    return 0 if all("MISMATCH" not in l and "REFUSED" not in l for l in lines) else 1


if __name__ == "__main__":
    raise SystemExit(main())
