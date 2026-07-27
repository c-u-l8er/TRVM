#!/usr/bin/env python3
"""Adapter that puts the two Python runtimes behind the same CLI contract the
native backends use: term on stdin, normal form on stdout, `interactions=N` on
stderr.

    echo 'TERM' | python3 pyrun.py ic_float

Both Python reducers walk the term recursively, so a deep readback (`s^65536`)
blows the default 1000-frame limit long before it hits any interaction-count
difference. That is an artifact of the host, not of the calculus, so this
adapter gives them the same headroom a native stack has: a big recursion limit
inside a thread with a large stack. Without this the Python backends would look
like they "fail" workloads they can actually reduce.
"""
import sys, os, threading

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "runtime", "python"))

which = sys.argv[1] if len(sys.argv) > 1 else "ic_float"
mod = __import__(which)

term = sys.stdin.read().strip()

sys.setrecursionlimit(4_000_000)
threading.stack_size(512 * 1024 * 1024)

result = {}


def go():
    try:
        nf, inter, _ = mod.run(term)
        result["nf"] = nf
        result["inter"] = inter
    except RecursionError:
        result["err"] = "RECURSION"
    except Exception as e:                    # noqa: BLE001 - report, don't mask
        result["err"] = f"{type(e).__name__}: {e}"


t = threading.Thread(target=go)
t.start()
t.join()

if "err" in result:
    sys.stderr.write("error=" + result["err"] + "\n")
    sys.exit(3)

sys.stdout.write(result["nf"] + "\n")
sys.stderr.write(f"interactions={result['inter']}\n")
