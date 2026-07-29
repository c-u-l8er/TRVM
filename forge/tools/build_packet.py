#!/usr/bin/env python3
"""build_packet.py -- build a review packet from a COMPUTED import closure.

A review packet is the zip a memo tells the reader to unzip: it must contain
everything needed to reproduce the memo's numbers, and nothing else. Previous
packets were assembled by hand, which failed twice in ways worth recording:

  * one packet shipped the batteries but omitted `runtime/python/ic_ref.py`, so
    every battery in it died on import;
  * `WRL_SLICE_B_COMMIT4_PACKET.zip` was described in a memo -- "every number is
    reproducible from the zip alone" -- and never actually existed on disk.

So the file list here is DERIVED, not written down. Given entry-point modules,
this walks the import graph with `ast`, resolves each name against the forge
package dir and the reference-runtime dir, and FAILS if any non-stdlib import
cannot be resolved. A packet that cannot be built is better than a packet that
unzips into a broken tree.

Layout produced (matching what the memos instruct):

    forge/<module>.py           the computed closure
    runtime/python/ic_ref.py    reference reducer (pulled in by the closure)
    runtime/c/ic32.c            native reducer SOURCE; the sweep builds it
    <extra docs>                memos/results named on the command line

Usage:
    python3 tools/build_packet.py NAME --entry run_l0_sweep.py --entry mutate49.py \
        [--doc ../SOME_MEMO.md] [--verify]

`--verify` extracts the finished zip into an empty temp dir and runs the sweep
there, which is the only way the phrase "verified from a clean extraction"
earns its place in a memo.
"""
import argparse
import ast
import os
import subprocess
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
FORGE = os.path.dirname(HERE)
TRVM = os.path.dirname(FORGE)
RT_PY = os.path.join(TRVM, "runtime", "python")
RT_C = os.path.join(TRVM, "runtime", "c")

# Search roots for a resolved import, in order, mapped to their zip destination.
SEARCH = [(FORGE, "forge"), (RT_PY, os.path.join("runtime", "python"))]


def _imports_of(path):
    """Top-level module names imported by one file."""
    names = set()
    try:
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)
    except (OSError, SyntaxError):
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            # level > 0 is a relative import; forge is a flat dir, so ignore.
            if node.level == 0 and node.module:
                names.add(node.module.split(".")[0])
    return names


def _subprocess_entries(path):
    """Local module names a file launches as SUBPROCESSES rather than imports.

    `run_l0_sweep.py` registers its batteries as bare strings -- ("binding_run6",
    "canvas/text isomorphism") -- and runs them with `subprocess`. An import walk
    cannot see them, so a closure built from imports alone ships the sweep without
    the batteries it sweeps: it would unzip, start, and die on the second entry.
    Any string literal that names a module file on the search path is therefore
    treated as an entry point. Over-inclusion is harmless here (the name really is
    a module in the tree); under-inclusion ships a broken packet.
    """
    names = set()
    try:
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)
    except (OSError, SyntaxError):
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value.strip()
            if v and "/" not in v and "\n" not in v and _resolve(v):
                names.add(v)
    return names


def _data_files(path):
    """Non-Python assets a file opens, named as literals beside it.

    `binding_run50.py` reads `os.path.join(HERE, "ic_v1_term_fingerprints.txt")`.
    That is neither an import nor a subprocess target, so both walks above miss it
    and the packet extracts into a tree where the battery dies on `open`. This was
    caught by `--verify`, not by reasoning: the in-tree run passes because the file
    is simply there. Any string literal that names an existing non-.py file in the
    forge dir is shipped.
    """
    names = set()
    try:
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=path)
    except (OSError, SyntaxError):
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value.strip()
            if (v and "/" not in v and "\n" not in v and "." in v
                    and not v.endswith(".py")
                    and os.path.isfile(os.path.join(FORGE, v))):
                names.add(v)
    return names


def _resolve(name):
    """Return (abs_src, zip_dst) for a local module, or None if not ours."""
    for root, dst in SEARCH:
        cand = os.path.join(root, name + ".py")
        if os.path.exists(cand):
            return cand, os.path.join(dst, name + ".py")
    return None


def closure(entries):
    """Transitive local-import closure over the entry files."""
    seen, out, queue = set(), {}, []
    for e in entries:
        src = e if os.path.isabs(e) else os.path.join(FORGE, e)
        if not os.path.exists(src):
            sys.exit(f"FAIL: entry point not found: {src}")
        out[os.path.join("forge", os.path.basename(src))] = src
        queue.append(src)
    unresolved = set()
    while queue:
        cur = queue.pop()
        if cur in seen:
            continue
        seen.add(cur)
        for name in sorted(_imports_of(cur)):
            if name in sys.stdlib_module_names or name in sys.builtin_module_names:
                continue
            hit = _resolve(name)
            if hit is None:
                unresolved.add((name, os.path.relpath(cur, TRVM)))
                continue
            src, dst = hit
            if dst not in out:
                out[dst] = src
                queue.append(src)
        # Data assets this file opens by name (see _data_files).
        for asset in sorted(_data_files(cur)):
            out.setdefault(os.path.join("forge", asset), os.path.join(FORGE, asset))
        # Modules this file shells out to (see _subprocess_entries).
        for name in sorted(_subprocess_entries(cur)):
            hit = _resolve(name)
            if hit is None:
                continue
            src, dst = hit
            if dst not in out:
                out[dst] = src
                queue.append(src)
    return out, unresolved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="packet name, e.g. WRL_SLICE_B_COMMIT4")
    ap.add_argument("--entry", action="append", required=True,
                    help="entry-point module (repeatable)")
    ap.add_argument("--doc", action="append", default=[],
                    help="extra file to ship at the zip root (repeatable)")
    ap.add_argument("--verify", action="store_true",
                    help="extract into a clean temp dir and run the sweep there")
    args = ap.parse_args()

    files, unresolved = closure(args.entry)
    if unresolved:
        print("FAIL -- unresolved non-stdlib imports (packet would not run):")
        for name, where in sorted(unresolved):
            print(f"    {name!r} imported by {where}")
        return 1

    # The native reducer ships as SOURCE; the sweep compiles it on first use.
    ic32c = os.path.join(RT_C, "ic32.c")
    if os.path.exists(ic32c):
        files[os.path.join("runtime", "c", "ic32.c")] = ic32c
    for d in args.doc:
        src = d if os.path.isabs(d) else os.path.join(FORGE, d)
        if not os.path.exists(src):
            sys.exit(f"FAIL: doc not found: {src}")
        files[os.path.basename(src)] = src

    out_dir = os.path.join(FORGE, "packets")
    os.makedirs(out_dir, exist_ok=True)
    out_zip = os.path.join(out_dir, args.name + "_PACKET.zip")
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for dst in sorted(files):
            z.write(files[dst], dst)
    print(f"built {os.path.relpath(out_zip, TRVM)}  ({len(files)} files)")
    for dst in sorted(files):
        print(f"    {dst}")

    if args.verify:
        print("\n-- verifying from a clean extraction --")
        tmp = tempfile.mkdtemp(prefix="packet-verify-")
        with zipfile.ZipFile(out_zip) as z:
            z.extractall(tmp)
        sweep = os.path.join(tmp, "forge", "run_l0_sweep.py")
        if not os.path.exists(sweep):
            print("    (no run_l0_sweep.py in packet -- skipping sweep)")
            return 0
        r = subprocess.run([sys.executable, "run_l0_sweep.py"],
                           cwd=os.path.join(tmp, "forge"),
                           capture_output=True, text=True)
        tail = [ln for ln in r.stdout.strip().splitlines() if ln.strip()][-1:]
        print("    " + (tail[0] if tail else "(no output)"))
        if r.returncode != 0:
            print("    STDERR:", r.stderr.strip()[:500])
            return 1
        print(f"    extraction verified at {tmp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
