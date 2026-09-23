#!/usr/bin/env python3
"""run_resident_controls.py -- the resident compiled host's mutants (`RESIDENT.md` §5).

    python3 -B controls/run_resident_controls.py [--only NAME]

Each control is one textual edit applied to a COPY of `compiled/`, and **a patch that does not apply exactly once is
a refusal**: a mutant that silently failed to apply is a control that proves nothing and reports GREEN. The copy is
made as a SIBLING of `compiled/` inside the TRVM tree rather than under /tmp, because the harness resolves `../forge`
and `../runtime/python` relative to itself -- the first version of this script copied to a temp directory, every run
died on the import, and every control dutifully reported "failing: none", which is what a control that cannot fail
looks like from the outside.

`unmutated` must be GREEN. Every other control must turn exactly the cases it names red, except the one marked `>=`:
`worker-replies-wrong-id` breaks every case that submits a job at all, and pinning that exact list would be pinning
an accident of which cases happen to submit.
"""
import argparse
import os
import shutil
import subprocess
import sys
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
TRVM = os.path.dirname(SRC)
SUMMARY = os.path.join(HERE, "RESIDENT_SUMMARY.txt")

CONTROLS = [
    # 2026-09-23: D2 (two concurrent jobs after a replacement) needs the deadline's kill and the replacement;
    # W2 (an idle worker died) needs the replacement. Their expectations were derived, then run.
    ("unmutated", None, None, None, set(), "="),
    ("no-kill-on-deadline", "resident.py",
     "        try:\n            self.proc.kill()\n        except ProcessLookupError:\n            pass\n",
     "        try:\n            pass\n        except ProcessLookupError:\n            pass\n", {"D1", "D2"}, "="),
    ("no-replace-after-confirmed-exit", "resident.py",
     "            if len(self._live) < self.pool_size:", "            if False:", {"D1", "D2", "W1", "W2"}, "="),
    ("unbounded-queue", "resident.py",
     "            if not self._idle and self._waiting >= self.max_queue:", "            if False:", {"Q1"}, "="),
    ("worker-replies-wrong-id", "resident.py",
     '        send_frame(sock, {"id": req.get("id"), **out,', '        send_frame(sock, {"id": "foreign", **out,',
     {"I1"}, ">="),
    ("skip-object-check", "executor.py", "        if recorded != so_sha:", "        if False:", {"B1"}, "="),
    ("writable-state-allowed", "resident.py",
     "        if ndx in writable and name not in allowed:", "        if False:", {"N1b"}, "="),
]


def failing_cases(log):
    return {m.group(1) for m in re.finditer(r"(?:FAIL|ERROR): test_([A-Za-z0-9]+)_", log)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    lines = []
    for name, fname, needle, repl, expected, mode in CONTROLS:
        if a.only and a.only != name:
            continue
        work = os.path.join(TRVM, ".resident-control-%s-%d" % (name, os.getpid()))
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
                    lines.append("control=%-32s PATCH REFUSED (%d occurrences -- a mutant that does not apply proves nothing)" % (name, n))
                    continue
                open(path, "w").write(s.replace(needle, repl))
            r = subprocess.run([sys.executable, "-B", os.path.join(work, "resident_test.py")], cwd=work,
                               capture_output=True, timeout=1800,
                               env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            log = (r.stdout + r.stderr).decode(errors="replace")
            got = failing_cases(log)
            if name == "unmutated":
                lines.append("control=%-32s %s" % (name, "GREEN" if r.returncode == 0 and not got else "UNEXPECTEDLY RED: " + ",".join(sorted(got))))
            elif (got == expected) if mode == "=" else (expected <= got and got):
                lines.append("control=%-32s failing: %-28s expected%s %-16s RED-AS-EXPECTED"
                             % (name, ",".join(sorted(got)) or "none", mode, ",".join(sorted(expected))))
            else:
                lines.append("control=%-32s failing: %-28s expected%s %-16s MISMATCH"
                             % (name, ",".join(sorted(got)) or "none", mode, ",".join(sorted(expected))))
        finally:
            shutil.rmtree(work, ignore_errors=True)
        print(lines[-1], flush=True)
    with open(SUMMARY, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("->", SUMMARY)
    return 0 if all("MISMATCH" not in l and "REFUSED" not in l and "UNEXPECTEDLY" not in l for l in lines) else 1


if __name__ == "__main__":
    raise SystemExit(main())
