#!/usr/bin/env python3
"""build_forge_release.py -- the ALLOWLISTED Forge release builder (v0.7.0-alpha.4).

GPT-5.6's v0.6.5 ruling: a distributable release must be built from an EXPLICIT
allowlist -- it copies only approved files and FAILS if any forbidden path (local
authoring state, Python bytecode, logs, historical milestone ZIPs, screenshots,
temp launch configs) ever appears in the staged tree. It then emits a manifest
that hashes every shipped file, so two builds are comparable and any drift is
visible.

The allowlist is the PRODUCTION import graph of `spinner_bench` (31 forge
modules, exercised across lower / run / verify+oracle / deep-health), plus the
reference runtime `ic_ref.py`, the native runtime SOURCE `ic32.c` (+ its note),
the three frontend assets, the launcher, the four release docs (a landing
README plus Quickstart / Architecture / Release Notes), and the repository
LICENSE. No battery (`binding_run*`), no Fixture-only test scaffold
beyond what the optional Verify Oracle mode lazily needs, no research archive,
no bytecode.

Layout of the built release (relative to the release root):

    forge-bench                    launcher (chmod +x)
    forge/<module>.py              the 31 production modules
    forge/spinner_bench.{html,js,css}
    runtime/python/ic_ref.py       reference reducer
    runtime/c/ic32.c               native reducer source (launcher builds it
                                   into an EXTERNAL cache, not this tree)
    runtime/c/IC32_RUNTIME.md
    README.md                      landing page (links the docs below)
    FORGE_QUICKSTART.md
    FORGE_ARCHITECTURE.md
    RELEASE_NOTES.md
    LICENSE
    MANIFEST.sha256                sha256 of every shipped file

v0.6.5.1: the optional `--zip` is a DETERMINISTIC archive (fixed 1980 epoch
timestamps, fixed 0644/0755 permissions, sorted entry order, DEFLATE) so two
builds of the same content produce a byte-identical ZIP -- not merely an
identical MANIFEST.

Usage:
    python3 tools/build_forge_release.py [--out DIR] [--zip PATH] [--force]

Exit status is non-zero (and nothing is published) if any required source file
is missing or any forbidden path would be shipped.
"""
import argparse
import hashlib
import os
import re
import shutil
import stat
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORGE = os.path.dirname(HERE)                       # .../TRVM/forge
TRVM = os.path.dirname(FORGE)                       # .../TRVM

# ---- the production import graph of spinner_bench (lower/run/verify+oracle) ----
# Keep this in sync with `binding_run35` RC4/RC5 (it asserts the normal Run path
# imports no binding_run* and no Fixture); the Fixture + e2_* modules below are
# shipped only because the OPTIONAL Verify-Oracle mode loads them lazily.
FORGE_MODULES = [
    "admit.py", "binlib.py", "compiler.py", "e2_model.py", "e2_run.py",
    "film.py", "fixture.py", "forge_errors.py", "forge_paths.py",
    "forge_runtime.py", "forge_state.py",
    "lower_e2a.py", "lowering_policy.py", "spinner_bench.py",
    "wrl_bundle.py", "wrl_canonical.py", "wrl_canvas.py", "wrl_complete.py",
    "wrl_converge.py", "wrl_diagnostics.py", "wrl_diff.py", "wrl_draft.py",
    "wrl_format.py", "wrl_ir.py", "wrl_jobs.py", "wrl_plan.py",
    "wrl_project.py", "wrl_scenario.py", "wrl_spans.py", "wrl_store.py",
    "wrl_sugar.py", "wrl_templates.py",
]
FRONTEND = ["spinner_bench.html", "spinner_bench.js", "spinner_bench.css"]
DOCS = ["README.md", "FORGE_QUICKSTART.md", "FORGE_ARCHITECTURE.md",
        "RELEASE_NOTES.md"]
# v0.7-3: the immutable, release-owned Template Catalog ships under forge/templates.
TEMPLATES = ["catalog.json", "golden-admit-v1.json", "acceptance-bench-v1.json",
             "blank-spinner-v1.json"]

# (src absolute, dst relative-to-release-root) pairs -- the ENTIRE allowlist.
def _allowlist():
    items = []
    for m in FORGE_MODULES:
        items.append((os.path.join(FORGE, m), os.path.join("forge", m)))
    for a in FRONTEND:
        items.append((os.path.join(FORGE, a), os.path.join("forge", a)))
    for t in TEMPLATES:
        items.append((os.path.join(FORGE, "templates", t),
                      os.path.join("forge", "templates", t)))
    items.append((os.path.join(TRVM, "runtime", "python", "ic_ref.py"),
                  os.path.join("runtime", "python", "ic_ref.py")))
    items.append((os.path.join(TRVM, "runtime", "c", "ic32.c"),
                  os.path.join("runtime", "c", "ic32.c")))
    items.append((os.path.join(TRVM, "runtime", "c", "IC32_RUNTIME.md"),
                  os.path.join("runtime", "c", "IC32_RUNTIME.md")))
    for d in DOCS:
        items.append((os.path.join(FORGE, d), d))
    items.append((os.path.join(FORGE, "forge-bench"), "forge-bench"))
    # the repository license ships at the release root (v0.6.5.1).
    items.append((os.path.join(TRVM, "LICENSE"), "LICENSE"))
    return items

# ---- forbidden path patterns -- a staged file matching ANY fails the build ----
FORBIDDEN = [
    re.compile(r"(^|/)\.forge_projects(/|$)"),
    re.compile(r"(^|/)\.recovery(/|$)"),
    re.compile(r"(^|/)\.trash(/|$)"),
    re.compile(r"(^|/)\.last_session\.json$"),
    re.compile(r"(^|/)__pycache__(/|$)"),
    re.compile(r"\.pyc$"), re.compile(r"\.pyo$"),
    re.compile(r"\.log$"),
    re.compile(r"_PACKET\.zip$"),
    re.compile(r"WRL_.*\.zip$"),
    re.compile(r"\.(png|jpg|jpeg|gif|webp)$"),   # local screenshots
    re.compile(r"(^|/)launch\.json$"),           # temp launch config
    re.compile(r"(^|/)binding_run.*\.py$"),      # test batteries never ship
]


def _forbidden(relpath):
    p = relpath.replace(os.sep, "/")
    for pat in FORBIDDEN:
        if pat.search(p):
            return pat.pattern
    return None


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build(out_dir, zip_path=None, force=False):
    items = _allowlist()

    # 1) every source must exist BEFORE we touch the output.
    missing = [src for src, _ in items if not os.path.isfile(src)]
    if missing:
        print("BUILD FAILED -- missing required source files:")
        for m in missing:
            print("  -", m)
        return 1

    # 2) no allowlisted DESTINATION may match a forbidden pattern (defensive).
    for _, dst in items:
        bad = _forbidden(dst)
        if bad:
            print("BUILD FAILED -- allowlisted destination is forbidden: %s "
                  "(pattern %s)" % (dst, bad))
            return 1

    out_dir = os.path.abspath(out_dir)
    if os.path.exists(out_dir):
        if not force:
            print("BUILD FAILED -- output dir exists (use --force): %s" % out_dir)
            return 1
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    # 3) copy only the allowlist.
    for src, dst in items:
        dpath = os.path.join(out_dir, dst)
        os.makedirs(os.path.dirname(dpath), exist_ok=True)
        shutil.copy2(src, dpath)
    # launcher is executable.
    lp = os.path.join(out_dir, "forge-bench")
    if os.path.isfile(lp):
        os.chmod(lp, os.stat(lp).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # 4) SWEEP the staged tree -- a build fails if ANYTHING forbidden slipped in.
    shipped = []
    for root, dirs, files in os.walk(out_dir):
        for fn in files:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, out_dir)
            bad = _forbidden(rel)
            if bad:
                print("BUILD FAILED -- forbidden path in staged tree: %s "
                      "(pattern %s)" % (rel, bad))
                shutil.rmtree(out_dir, ignore_errors=True)
                return 1
            shipped.append(rel)

    # 5) manifest: sha256 of every shipped file (sorted, excluding the manifest).
    shipped.sort()
    lines = ["# Forge Release MANIFEST (sha256)  --  %d files\n" % len(shipped)]
    for rel in shipped:
        digest = _sha256(os.path.join(out_dir, rel))
        lines.append("%s  %s\n" % (digest, rel.replace(os.sep, "/")))
    with open(os.path.join(out_dir, "MANIFEST.sha256"), "w") as f:
        f.writelines(lines)

    print("BUILD OK -- %d files staged in %s" % (len(shipped) + 1, out_dir))

    # 6) optional DETERMINISTIC zip -- fixed timestamps/permissions/order so two
    #    builds of the same content are byte-identical (not just same MANIFEST).
    if zip_path:
        import zipfile
        zip_path = os.path.abspath(zip_path)
        entries = sorted(shipped + ["MANIFEST.sha256"])
        exec_bits = 0o755
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for rel in entries:
                full = os.path.join(out_dir, rel)
                arc = rel.replace(os.sep, "/")
                zi = zipfile.ZipInfo(arc, date_time=(1980, 1, 1, 0, 0, 0))
                zi.compress_type = zipfile.ZIP_DEFLATED
                # 0755 for the launcher, 0644 otherwise -- never the host perms.
                mode = exec_bits if arc == "forge-bench" else 0o644
                zi.external_attr = (mode & 0o7777) << 16
                with open(full, "rb") as f:
                    z.writestr(zi, f.read())
        print("       zipped (deterministic) -> %s" % zip_path)
    return 0


def main():
    ap = argparse.ArgumentParser(description="Build an allowlisted Forge release.")
    ap.add_argument("--out", default=os.path.join(FORGE, "dist", "forge-release"),
                    help="output directory (default forge/dist/forge-release)")
    ap.add_argument("--zip", default=None, help="also write a zip at this path")
    ap.add_argument("--force", action="store_true",
                    help="overwrite an existing output dir")
    args = ap.parse_args()
    return build(args.out, zip_path=args.zip, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
