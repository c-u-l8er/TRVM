#!/usr/bin/env python3
"""run_l0_sweep.py -- one command that runs the whole WRL LANGUAGE-TRACK sweep.

This exists because the previous review could not independently execute the
sweep: the packet shipped the batteries but omitted a runtime dependency
(`runtime/python/ic_ref.py`, the reference IC reducer), so every battery died at
import. A packet whose contents cannot be run is a claim, not evidence.

Usage
-----
    python3 run_l0_sweep.py                 # reference + native (needs a C compiler)
    TRVM_SKIP_NATIVE=1 python3 run_l0_sweep.py    # reference only, no compiler needed

The REFERENCE path is pure Python and needs nothing beyond the standard library.
The NATIVE path additionally compiles `runtime/c/ic32.c`; when it is unavailable
set `TRVM_SKIP_NATIVE=1` and the sweep reports `PASS_REF_ONLY`, which still
exercises every law -- native adds an independent second reducer, not new laws.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# (module, what it gates). Ordered cheapest-first so a structural break surfaces
# before the long native folds.
#
# THIS LIST IS CLOSED. L-0 was ratified and frozen at WRL Core 0.1.3, and this
# is the gate that proves the frozen thing still holds. Appending live work to
# it would quietly redefine what "the L-0 sweep is green" means: three commits
# later a Slice B failure would read as an L-0 regression, and the one number
# that is supposed to be stable would move for reasons unrelated to L-0. New
# batteries go in `SWEEP_LIVE` below.
SWEEP_L0 = [
    ("binding_run5",  "identity spine: canonical bytes, SemanticArtifactID"),
    ("binding_run6",  "canvas/text isomorphism (3C)"),
    ("binding_run7",  "backend identity closure, sealed plans (3D/3D.1)"),
    ("binding_run8",  "source spans as a pure sidecar (3B-1)"),
    ("binding_run9",  "canonical formatter + the L-0 document-boundary laws"),
    ("binding_run10", "diagnostics as a pure sidecar (3B-3)"),
    ("binding_run11", "named rotors + concise clocks (3B-4)"),
    ("binding_run12", "SemanticDiff + completion metadata (3B-5)"),
    ("binding_run13", "sealed/tolerant diff split, canonical locators"),
    ("binding_run14", "geometry-dependent named rotor projection"),
    ("binding_run44", "L-0 SUGAR TIER -- expansion + authored-coordinate tooling"),
    ("wrl_roundtrip_probe", "L-0 restatement probe + its negative control"),
]

# Work that is NOT frozen. Green here is a statement about the slice in
# progress, not about L-0.
SWEEP_LIVE = [
    ("binding_run45", "Slice B c0 -- three-way CanvasGraphV1 importer"),
    ("binding_run46", "Slice B c1 -- Mailbox WRL Core surface declaration"),
    ("binding_run47", "Slice B c2 -- canonical AsyncRouteDecl + RouteKey"),
    ("binding_run48", "Slice B c3 -- the `~~` surface (parse + format)"),
    ("binding_run49", "Slice B c4 -- the runtime fold (route -> ADMIT claim)"),
    ("binding_run50", "Slice B c5a -- the IC proof-profile split (v1/v2)"),
    ("binding_run51", "Slice B c5c -- mailbox profile + the seam-1 selection"),
    ("binding_run52", "v0.6 state-layout de-fork + the backend guard"),
    ("binding_run53", "Slice B c5d -- freeze integrity (document + API seam)"),
]

# `binding_run3o` is NOT in either list and that is deliberate: it is an ADMIT
# battery, not a WRL one, and this sweep is the LANGUAGE track's gate. Commit 4
# nevertheless gave its helpers a defaulted `fx` parameter (they closed over one
# world's fixture and silently ignored the argument callers were already
# passing), so it was re-run by hand and is unchanged. Noted here rather than
# added, because widening what this sweep covers would change what its number
# means -- the same argument the L-0/LIVE split is built on.
#
# Commit 5a gave those same helpers a defaulted `prof` parameter for the same
# reason, and it is worth being blunt about the risk that creates: this sweep
# CANNOT see a regression in `binding_run3o`, so an all-green line would still be
# printed by a tree whose ADMIT reducer had been broken by the profile split.
# It is re-run by hand alongside every sweep in this slice, and commit 5a's
# binding_run50 additionally gates the v1 term surface byte-for-byte, which is
# a tighter net than the ADMIT battery over exactly the thing that could drift.
#
# Commit 5b widened `binding_run3o` again -- `_build_fold`, `_decode_fold` and
# `_project_claims` all took an `mcap` parameter -- so the same hand re-run
# applies, and `binding_run51`'s T2b is the row that pins the new default inert
# character for character on every caller that existed before it.
#
# Commit 5c widened both once more (`_build_fold` takes a `rule`,
# `_project_claims` a `policy_id`) and the same discipline applies, with one
# addition that matters more than the re-run: `_project_claims` now RENDERS a
# ledger entry it never rendered before. `None` reproduces the old rendering
# exactly and every pre-5c caller passes `None`, which T2c pins for the term
# and `binding_run3o`'s own hand re-run pins for the projection -- but a
# defaulted parameter that changes OUTPUT is a wider blast radius than one that
# changes shape, so it is called out here rather than left to the pattern.

VERDICTS = ("PASS_REF_AND_NATIVE", "PASS_REF_ONLY", "PASS_REF",
            "REF_ONLY", "ALL PASS", "FAILURES", "FAIL")


def verdict_of(out):
    """The battery's own verdict token, read from its output.

    Deliberately scans from the END: the batteries print per-row lines and then
    trailing commentary, and several notes legitimately contain the word FAIL
    (they describe what a negative control catches). Taking the last VERDICT
    token rather than the last line avoids both mistakes.
    """
    for line in reversed(out.strip().splitlines()):
        for v in VERDICTS:
            if v in line:
                return v, line.strip()
    return "NO_VERDICT", (out.strip().splitlines() or ["(no output)"])[-1]


def ensure_native():
    """Make the native reducer available, or explain in one line why it is not.

    A source-only packet ships `runtime/c/ic32.c` but no BINARY, and the native
    path resolves a prebuilt `runtime/c/ic32`. Left alone that surfaces as a raw
    `FileNotFoundError` from deep inside `subprocess` -- a stack trace that says
    nothing about the actual situation, which is simply "nobody built it yet".

    So: build it if a compiler exists, and otherwise say so and continue in
    reference-only mode. The fallback is ANNOUNCED, never silent -- a sweep that
    quietly stops folding the second reducer while still printing green is
    exactly the kind of evidence this round is trying to stop producing.

    `TRVM_IC32_PATH` is the existing sanctioned override, so this introduces no
    new mechanism: it builds into a temp path and exports it.
    """
    if os.environ.get("TRVM_SKIP_NATIVE") == "1":
        return None, "reference only (TRVM_SKIP_NATIVE=1)"
    have = os.environ.get("TRVM_IC32_PATH")
    if have and os.path.exists(have):
        return have, "reference + native (TRVM_IC32_PATH)"
    dev = os.path.join(HERE, "..", "runtime", "c", "ic32")
    if os.path.exists(dev):
        return dev, "reference + native (prebuilt)"
    src = os.path.join(HERE, "..", "runtime", "c", "ic32.c")
    if not os.path.exists(src):
        os.environ["TRVM_SKIP_NATIVE"] = "1"
        return None, "reference only (no ic32.c in this tree)"
    cc = (os.environ.get("CC") or shutil.which("gcc") or shutil.which("clang")
          or shutil.which("cc"))
    if not cc:
        os.environ["TRVM_SKIP_NATIVE"] = "1"
        return None, "reference only (no C compiler; set CC to enable native)"
    # Build to the DEV-TREE location first, and fall back to a temp path.
    #
    # `TRVM_IC32_PATH` alone is not sufficient here, and it is worth saying why:
    # only `forge_runtime` honours it. The older `binding_run2/3i/3j` each
    # hard-code `<tree>/runtime/c/ic32` and ignore the override -- a fourth
    # independent spelling of one path (see the memo). Building to the location
    # every spelling agrees on satisfies all of them at once, and does not
    # require editing legacy batteries for a packaging concern. The env var is
    # exported too, so the `forge_runtime` path is covered either way.
    dest = os.path.abspath(dev)
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        out, where = dest, "runtime/c/ic32"
    except OSError:
        out, where = os.path.join(tempfile.mkdtemp(prefix="wrl-ic32-"),
                                  "ic32"), "a temp dir"
    p = subprocess.run([cc, "-O2", "-o", out, src], capture_output=True,
                       text=True)
    if p.returncode != 0 or not os.path.exists(out):
        os.environ["TRVM_SKIP_NATIVE"] = "1"
        return None, ("reference only (ic32.c failed to build: %s)"
                      % (p.stderr.strip().splitlines() or ["?"])[-1][:70])
    os.environ["TRVM_IC32_PATH"] = out
    return out, ("reference + native (built ic32 into %s with %s)"
                 % (where, os.path.basename(cc)))


def main():
    _bin, mode = ensure_native()
    print("[wrl-l0-sweep] %s" % mode)
    print("[wrl-l0-sweep] python %s" % sys.version.split()[0])
    print()
    t0 = time.time()
    bad = []

    def run(section, rows):
        # Sections are reported SEPARATELY on purpose. One combined count would
        # let a frozen-tier regression and an in-progress failure average into
        # the same number, and those two facts call for opposite responses:
        # a frozen row breaking means something ratified has moved.
        if not rows:
            return
        print("  -- %s" % section)
        for mod, gates in rows:
            sys.stdout.write("  %-22s " % mod)
            sys.stdout.flush()
            t1 = time.time()
            p = subprocess.run([sys.executable,
                                os.path.join(HERE, mod + ".py")],
                               capture_output=True, text=True, cwd=HERE)
            v, line = verdict_of(p.stdout + "\n" + p.stderr)
            ok = p.returncode == 0 and v.startswith(("PASS", "ALL PASS"))
            if not ok:
                bad.append((section, mod, v, line))
            print("%-20s %4ds   %s" % (v, time.time() - t1, gates))
        print()

    run("L-0 (FROZEN -- WRL Core 0.1.3 §17)", SWEEP_L0)
    run("LIVE (unfrozen slice in progress)", SWEEP_LIVE)

    total = len(SWEEP_L0) + len(SWEEP_LIVE)
    if bad:
        print("[wrl-l0-sweep] FAILURES (%d):" % len(bad))
        for section, mod, v, line in bad:
            print("    %-22s %-20s %s" % (mod, v, line[:90]))
        frozen = [b for b in bad if b[0].startswith("L-0")]
        if frozen:
            print("[wrl-l0-sweep] *** %d FROZEN-TIER row(s) failed -- a "
                  "ratified law has moved ***" % len(frozen))
    print("[wrl-l0-sweep] %s -- %d/%d green (%ds)"
          % ("ALL PASS" if not bad else "FAILURES",
             total - len(bad), total, time.time() - t0))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
