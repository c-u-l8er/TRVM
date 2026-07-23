"""forge_runtime.py -- the PRODUCTION runtime adapter (v0.6.5 release closure).

The Spinner Bench release depends on exactly TWO reducers over the frozen
interaction-calculus runtime, and nothing else:

  * ref_reduce(src)     -- the reference reducer (ic_ref, pure Python)
  * native_reduce(src)  -- the native reducer (the compiled `runtime/c/ic32`)

Before v0.6.5 these lived in `binding_run3j` (a TEST battery module that also
imports the Fixture oracle), and `spinner_bench` reached them through
`binding_run3o` -- so the production server transitively imported the whole
battery + Fixture stack. This module is the clean extraction GPT-5.6's v0.6.5
ruling required: the production import direction is now

    spinner_bench  ->  forge_runtime  ->  ic_ref / ic32

with NO `binding_run*` and NO `fixture` on the normal Run path. The reducer
BODIES are byte-for-byte the same computation as `binding_run3j.norm` /
`binding_run3j.native` (this is a dependency-boundary correction, not a
behavior change): ref_reduce resets the runtime and normalizes the parsed term;
native_reduce shells out to ic32, checks the return, resets, and parses the
single output line.
"""
import os
import sys
import subprocess

# The reference reducer (ic_ref.normal) is deeply recursive; the batteries used
# to raise this limit as a side effect of importing binding_run3j. Now that the
# production path imports NO battery, the reducer adapter owns the limit.
sys.setrecursionlimit(2_000_000)

HERE = os.path.dirname(os.path.abspath(__file__))

# The native reducer binary. The launcher (`forge-bench`) is responsible for
# locating / building it (into an EXTERNAL cache, never the install tree) and
# passing the result through TRVM_IC32_PATH. Here we only record the path and
# answer availability so the server can degrade to ref-only when it is absent.
#   * TRVM_IC32_PATH (launcher-injected external cache binary) wins, so a
#     read-only installation never needs a writable runtime/c/;
#   * otherwise fall back to the dev-tree binary (keeps the batteries working).
IC32 = os.environ.get("TRVM_IC32_PATH") \
    or os.path.join(HERE, "..", "runtime", "c", "ic32")

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

# ic_ref is the frozen reference runtime (pure Python); import it directly --
# NOT via any battery module.
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
from ic_ref import parse, normal, reset_runtime


def native_available():
    """True iff the native reducer binary exists and is executable AND native
    is not gated off. A shallow check -- it does not fold anything."""
    return (not SKIP_NATIVE) and os.path.isfile(IC32) and os.access(IC32, os.X_OK)


def ref_reduce(src, budget=2_000_000_000):
    """Reference reducer: reset the runtime and normalize the parsed term.
    Identical computation to binding_run3j.norm."""
    reset_runtime()
    return normal(parse(src), budget=budget)


def native_reduce(src, timeout=600):
    """Native reducer: fold `src` through the compiled ic32 binary, then parse
    its single output line. Identical computation to binding_run3j.native.
    Raises RuntimeError on a non-zero return or empty output."""
    r = subprocess.run([IC32], input=src.encode(), capture_output=True,
                       timeout=timeout)
    out = r.stdout.decode().strip().splitlines()
    if r.returncode != 0 or not out:
        raise RuntimeError("ic32 rc=%s" % r.returncode)
    reset_runtime()
    return parse(out[0])
