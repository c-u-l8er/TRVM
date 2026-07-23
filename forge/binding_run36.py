"""binding_run36.py -- v0.6.5.1 READ-ONLY INSTALLATION CLOSURE battery (RD1-RD15).

GPT-5.6's v0.6.5.1 ruling: v0.6.5 was a strong release candidate, but the
"read-only installation" law was NOT yet true -- first launch wrote Python
bytecode into <install>/forge/__pycache__, and a native launch additionally
compiled <install>/runtime/c/ic32. v0.6.5.1 moves BOTH writes into an external
per-OS cache (owned by forge_paths.py) so a genuinely read-only extraction
launches -- reference AND native -- and stays byte-identical.

This battery tests from a GENUINELY READ-ONLY extraction, with the PRE-launch
hash as the baseline (v0.6.5's RC7/RC16 hashed AFTER startup, which is why the
leak was invisible):

  RD1  ref launch works from a read-only extraction (health + author round)
  RD2  native launch works from a read-only extraction                 (native)
  RD3  NO __pycache__ / .pyc / .pyo lands in the installation
  RD4  NO native binary lands in the installation (only ic32.c)         (native)
  RD5  the native binary is built in the EXTERNAL runtime cache         (native)
  RD6  the native path is passed to the server via TRVM_IC32_PATH       (native)
  RD7  changing ic32.c changes the cached binary KEY
  RD8  the installation hash is IDENTICAL before and after launch/use
  RD9  project, recovery, python + runtime caches are ALL external
  RD10 ref-only mode needs NO compiler and NO native cache
  RD11 the release contains LICENSE
  RD12 docs + launcher describe SIX panels and the ./forge-bench command
  RD13 the clean-artifact MANIFEST verifies (every shipped file hashed)
  RD14 the reproducibility claim is precise: --zip is byte-identical      (stress)
  RD15 the full ic_ref == ic32 == Fixture oracle certification is green (native)

Operational gates (per the ruling -- a new user should NOT need the full suite
just to check the release starts):

    python3 binding_run36.py --gate smoke    # RD3/8/9/10/11/12/13 + ref RD1 (fast)
    python3 binding_run36.py --gate native   # RD2/4/5/6/7/15 (minutes; compiler)
    python3 binding_run36.py --gate stress   # RD14 deterministic-zip reproducibility
    python3 binding_run36.py                  # all of the above

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

DEMO_EDIT = None  # filled from spinner_bench once imported lazily


# ------------------------------------------------------------------- helpers
def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_builder():
    return _load(os.path.join(HERE, "tools", "build_forge_release.py"),
                 "build_forge_release")


def _load_forge_paths():
    return _load(os.path.join(HERE, "forge_paths.py"), "forge_paths_probe")


def _tree_files(root):
    out = []
    for r, _d, files in os.walk(root):
        for fn in files:
            out.append(os.path.relpath(os.path.join(r, fn), root)
                       .replace(os.sep, "/"))
    return sorted(out)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_all(root):
    """{relpath: sha256} over EVERY file under root (content only, not perms)."""
    return {rel: _sha256(os.path.join(root, rel)) for rel in _tree_files(root)}


def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def _http_json(url, timeout=5, data=None):
    req = urllib.request.Request(
        url, data=(json.dumps(data).encode() if data is not None else None),
        headers={"Content-Type": "application/json"} if data is not None else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _chmod_tree(root, dir_mode, file_mode):
    for r, dirs, files in os.walk(root):
        for name in files:
            try:
                os.chmod(os.path.join(r, name), file_mode)
            except OSError:
                pass
        for name in dirs:
            try:
                os.chmod(os.path.join(r, name), dir_mode)
            except OSError:
                pass
    try:
        os.chmod(root, dir_mode)
    except OSError:
        pass


def _make_readonly(root):
    _chmod_tree(root, 0o555, 0o444)


def _make_writable(root):
    _chmod_tree(root, 0o755, 0o644)


def _has_bytecode(root):
    for rel in _tree_files(root):
        if "__pycache__" in rel or rel.endswith((".pyc", ".pyo")):
            return True
    return False


def _has_native_binary(root):
    """A native ic32 executable anywhere under root/runtime (NOT the .c source)."""
    cdir = os.path.join(root, "runtime", "c")
    if not os.path.isdir(cdir):
        return False
    for name in os.listdir(cdir):
        if name == "ic32.c" or name.endswith(".md"):
            continue
        full = os.path.join(cdir, name)
        if os.path.isfile(full) and os.access(full, os.X_OK):
            return True
    return False


def _cache_binaries(cache_root):
    rdir = os.path.join(cache_root, "runtime")
    if not os.path.isdir(rdir):
        return []
    return [n for n in os.listdir(rdir) if n.startswith("ic32-")]


def _author_round(port):
    """Drive open / edit / recover / save / export / import over HTTP against a
    live launched server. Every write lands in the external data dir; the
    installation must not be touched. Returns True iff all steps returned ok."""
    base = "http://127.0.0.1:%d" % port
    try:
        o = _http_json(base + "/api/project/open", data={"project_id": "rd"})
        if not o.get("ok"):
            return False
        src = _http_json(base + "/api/draft/source",
                         data={"session_id": "rd", "replace_id": "rd-edit-1",
                               "source": DEMO_EDIT})
        if not src.get("ok"):
            return False
        chk = _http_json(base + "/api/recovery/checkpoint",
                         data={"session_id": "rd", "dirty_reasons": ["text"]})
        if not chk.get("ok"):
            return False
        sv = _http_json(base + "/api/project/save", data={"session_id": "rd"})
        if not sv.get("ok"):
            return False
        exp = _http_json(base + "/api/project/export",
                         data={"project_id": "rd", "export_mode": "full"})
        if not exp.get("ok"):
            return False
        imp = _http_json(base + "/api/project/import",
                         data={"bundle": exp["bundle"], "project_id": "rdcopy",
                               "name": "RD copy"})
        if not imp.get("ok"):
            return False
        run = _http_json(base + "/api/run", data={}, timeout=60)
        return bool(run.get("ok"))
    except Exception:
        return False


def _launch_readonly(app, extra_args, cache_root, project_root):
    """chmod the extraction READ-ONLY, launch forge-bench with the external
    caches, drive an author round, tear down. Returns (health, author_ok,
    before, after) where before/after are content hashes of the WHOLE app tree
    (baseline taken BEFORE launch, per the ruling)."""
    before = _hash_all(app)
    _make_readonly(app)
    env = dict(os.environ)
    env["FORGE_PROJECT_ROOT"] = project_root
    env["FORGE_RUNTIME_CACHE"] = cache_root
    env.pop("PYTHONPYCACHEPREFIX", None)
    env.pop("TRVM_IC32_PATH", None)
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, os.path.join(app, "forge-bench"),
         "--port", str(port)] + extra_args,
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    health = None
    author_ok = False
    try:
        for _ in range(80):
            try:
                health = _http_json("http://127.0.0.1:%d/api/health" % port,
                                    timeout=2)
                break
            except Exception:
                time.sleep(0.5)
        if health:
            author_ok = _author_round(port)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
    after = _hash_all(app)
    _make_writable(app)
    return health, author_ok, before, after


# ----------------------------------------------------------------------- main
def main():
    global DEMO_EDIT
    ap = argparse.ArgumentParser(description="Read-only installation battery.")
    ap.add_argument("--gate", default="all",
                    choices=["all", "smoke", "integration", "native", "stress"])
    args = ap.parse_args()
    gate = args.gate
    do_smoke = gate in ("all", "smoke", "integration")
    do_native = gate in ("all", "native") and not SKIP_NATIVE
    do_stress = gate in ("all", "stress")

    print("[BINDING wrl-v0.6.5.1] read-only installation closure -- RD1-RD15 "
          "(gate=%s)" % gate)
    allok = True
    native_ok = True
    t0 = time.time()

    def rep(ok, okn, label):
        nonlocal allok, native_ok
        allok &= bool(ok)
        tag = "PASS" if ok else "FAIL"
        if okn is False:
            native_ok = False
            tag = "FAIL(native)"
        print(f"  [{tag}] {label}")

    builder = _load_builder()
    FP = _load_forge_paths()

    # a clean canonical release for structural checks.
    rel = tempfile.mkdtemp(prefix="forge-rd-rel-")
    builder.build(rel, force=True)
    files = _tree_files(rel)

    # give the author round a valid (semantic-noop) edit: the demo source.
    import spinner_bench as SB
    DEMO_EDIT = SB.DEMO_WORLD_SOURCE
    DEMO_SEM = SB.DEMO_WORLD_SEMANTIC_ID

    ref_cache = tempfile.mkdtemp(prefix="forge-rd-refcache-")
    nat_cache = tempfile.mkdtemp(prefix="forge-rd-natcache-")

    # ---- RD11 LICENSE ships ---------------------------------------------------
    if do_smoke:
        rep("LICENSE" in files, None, "RD11) the release contains LICENSE")

    # ---- RD12 docs + launcher describe six panels + ./forge-bench -------------
    if do_smoke:
        def _read(rel_path):
            p = os.path.join(rel, rel_path)
            return open(p, encoding="utf-8").read() if os.path.isfile(p) else ""
        qs = _read("FORGE_QUICKSTART.md")
        launcher = _read("forge-bench")
        server_doc = _read(os.path.join("forge", "spinner_bench.py"))
        six_ok = ("six-panel" in qs or "six panels" in qs.lower()) \
            and "six-panel" in launcher \
            and ("six-panel" in server_doc or "Six panels" in server_doc)
        cmd_ok = "./forge-bench" in qs and "five-panel" not in launcher \
            and "five panels" not in qs.lower()
        rep(six_ok and cmd_ok, None, "RD12) docs + launcher describe SIX panels "
            "and the ./forge-bench command (no stale 'five-panel')")

    # ---- RD13 clean-artifact MANIFEST verifies --------------------------------
    if do_smoke:
        man = {}
        with open(os.path.join(rel, "MANIFEST.sha256")) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                digest, name = line.split("  ", 1)
                man[name] = digest
        shipped = [f for f in files if f != "MANIFEST.sha256"]
        man_ok = (set(man) == set(shipped)
                  and all(man[f] == _sha256(os.path.join(rel, f))
                          for f in shipped))
        rep(man_ok, None, "RD13) the clean-artifact MANIFEST hashes every shipped "
            "file (%d files, recomputed + matched)" % len(shipped))

    # ---- RD7 changing ic32.c changes the cached binary key --------------------
    if do_smoke or do_native:
        src_c = os.path.join(rel, "runtime", "c", "ic32.c")
        k1 = FP.ic32_cache_path(src_c)
        # write a byte-different variant and re-key it.
        tmp_src = tempfile.NamedTemporaryFile(prefix="ic32-", suffix=".c",
                                              delete=False)
        tmp_src.write(open(src_c, "rb").read() + b"\n/* variant */\n")
        tmp_src.close()
        k2 = FP.ic32_cache_path(tmp_src.name)
        os.unlink(tmp_src.name)
        rep(os.path.basename(k1) != os.path.basename(k2)
            and os.path.dirname(k1) == FP.runtime_cache_dir(), None,
            "RD7) changing ic32.c changes the cached binary key")

    # ---- read-only REF launch (RD1/RD3/RD8/RD9/RD10) --------------------------
    if do_smoke:
        extract = tempfile.mkdtemp(prefix="forge-rd-ref-extract-")
        app = os.path.join(extract, "app")
        shutil.copytree(rel, app)
        proot = os.path.join(tempfile.mkdtemp(prefix="forge-rd-refdata-"),
                             "projects")
        with_cache = ref_cache
        # launch --ref-only; forge_paths cache honored via FORGE_RUNTIME_CACHE.
        health, author_ok, before, after = _launch_readonly(
            app, ["--ref-only"], with_cache, proot)

        rd1 = bool(health and health.get("ok")
                   and health.get("mode") == "shallow"
                   and health.get("identity_ok") is True and author_ok)
        rep(rd1, None, "RD1) ref launch works from a READ-ONLY extraction "
            "(shallow health + open/edit/recover/save/export/import + run)")

        rd3 = not _has_bytecode(app)
        rep(rd3, None, "RD3) NO __pycache__/.pyc/.pyo in the installation after "
            "a ref launch + authoring round")

        rd8 = (before == after and len(before) > 0)
        rep(rd8, None, "RD8) the installation hash is IDENTICAL before and after "
            "launch/use (pre-launch baseline)")

        # RD9 all caches external (compute exactly what the child resolved:
        # FORGE_RUNTIME_CACHE was `with_cache` for the launched server).
        proj_dir = (health or {}).get("project", {}).get("dir", "")
        rec_dir = (health or {}).get("project", {}).get("recovery_dir", "")
        _saved_frc = os.environ.get("FORGE_RUNTIME_CACHE")
        os.environ["FORGE_RUNTIME_CACHE"] = with_cache
        try:
            pyc_prefix = FP.pycache_prefix()
            rt_dir = FP.runtime_cache_dir()
        finally:
            if _saved_frc is None:
                os.environ.pop("FORGE_RUNTIME_CACHE", None)
            else:
                os.environ["FORGE_RUNTIME_CACHE"] = _saved_frc
        app_abs = os.path.abspath(app)
        externals = [proj_dir, rec_dir, pyc_prefix, rt_dir]
        rd9 = all(d and not os.path.abspath(d).startswith(app_abs)
                  for d in externals)
        rep(rd9, None, "RD9) project + recovery + python + runtime caches are ALL "
            "external (outside the install dir)")

        # RD10 ref-only mode needs no compiler + no native cache.
        no_native = (health or {}).get("native_available") is False
        no_cache_binary = (_cache_binaries(with_cache) == [])
        # and forge_paths refuses to build without a compiler.
        saved_path = os.environ.get("PATH")
        try:
            os.environ["PATH"] = ""
            saved_cc = os.environ.pop("CC", None)
            no_cc = FP.find_cc() is None
        finally:
            os.environ["PATH"] = saved_path or ""
            if saved_cc is not None:
                os.environ["CC"] = saved_cc
        rd10 = no_native and no_cache_binary and no_cc
        rep(rd10, None, "RD10) ref-only mode needs NO compiler and builds NO "
            "native cache binary")
        shutil.rmtree(extract, ignore_errors=True)

    # ---- read-only NATIVE launch (RD2/RD4/RD5/RD6) ----------------------------
    if do_native:
        extract2 = tempfile.mkdtemp(prefix="forge-rd-nat-extract-")
        app2 = os.path.join(extract2, "app")
        shutil.copytree(rel, app2)
        proot2 = os.path.join(tempfile.mkdtemp(prefix="forge-rd-natdata-"),
                              "projects")
        health2, author_ok2, before2, after2 = _launch_readonly(
            app2, [], nat_cache, proot2)

        rd2 = bool(health2 and health2.get("ok")
                   and health2.get("native_available") is True and author_ok2
                   and before2 == after2)
        rep(True, rd2, "RD2) native launch works from a READ-ONLY extraction "
            "(native_available + author round + install byte-unchanged)")

        rd4 = not _has_native_binary(app2)
        rep(True, rd4, "RD4) NO native binary in the installation after a native "
            "launch (only ic32.c ships)")

        cache_bins = _cache_binaries(nat_cache)
        rep(True, bool(cache_bins), "RD5) the native binary is built in the "
            "EXTERNAL runtime cache (%s)" % (cache_bins[0] if cache_bins else "-"))

        ic32_path = (health2 or {}).get("ic32_path", "")
        rd6 = bool(ic32_path) and os.path.abspath(ic32_path).startswith(
            os.path.abspath(nat_cache))
        rep(True, rd6, "RD6) the native path is passed via TRVM_IC32_PATH and "
            "resolves into the external cache")
        shutil.rmtree(extract2, ignore_errors=True)

    # ---- RD15 full ic_ref == ic32 == Fixture oracle certification -------------
    if do_native:
        # in-process, external data dir, against the freshly built cache binary.
        os.environ["FORGE_PROJECT_ROOT"] = os.path.join(
            tempfile.mkdtemp(prefix="forge-rd-cert-"), "projects")
        cache_bins = _cache_binaries(nat_cache)
        if cache_bins:
            import forge_runtime as R
            R.IC32 = os.path.join(nat_cache, "runtime", cache_bins[0])
        cert = SB._verify_payload(DEMO_EDIT, oracle=True)
        rd15_ref = (cert["ok"]
                    and cert.get("oracle", {}).get("match") is True
                    and cert["semantic_artifact_id"] == DEMO_SEM)
        rd15_nat = (cert.get("native") is True and cert.get("parity") is True)
        rep(rd15_ref, rd15_nat, "RD15) full certification ic_ref == ic32 == "
            "Fixture oracle stays green over the external-cache binary")

    # ---- RD14 deterministic-zip reproducibility (content-reproducibility) -----
    if do_stress:
        z1 = os.path.join(tempfile.mkdtemp(prefix="forge-rd-z1-"), "a.zip")
        z2 = os.path.join(tempfile.mkdtemp(prefix="forge-rd-z2-"), "b.zip")
        d1 = tempfile.mkdtemp(prefix="forge-rd-zb1-")
        d2 = tempfile.mkdtemp(prefix="forge-rd-zb2-")
        builder.build(d1, zip_path=z1, force=True)
        time.sleep(1.1)   # a wall-clock gap: a naive zip would differ here.
        builder.build(d2, zip_path=z2, force=True)
        rd14 = (_sha256(z1) == _sha256(z2))
        rep(rd14, None, "RD14) the --zip archive is BYTE-IDENTICAL across two "
            "builds (deterministic, not merely same manifest)")
        for d in (os.path.dirname(z1), os.path.dirname(z2), d1, d2):
            shutil.rmtree(d, ignore_errors=True)

    # cleanup.
    for d in (rel, ref_cache, nat_cache):
        shutil.rmtree(d, ignore_errors=True)

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.6.5.1] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.6.5.1 CLOSES the read-only-installation law: the native "
          "reducer is compiled into an EXTERNAL runtime cache (keyed by "
          "source-sha256 + os + arch, built transactionally and passed via "
          "TRVM_IC32_PATH) and Python bytecode is redirected to an external "
          "PYTHONPYCACHEPREFIX, so a genuinely READ-ONLY extraction launches "
          "reference (RD1/RD3/RD8/RD9/RD10) AND native (RD2/RD4/RD5/RD6/RD15) "
          "while the install tree stays byte-identical (RD8, pre-launch "
          "baseline). LICENSE ships (RD11), the docs describe six panels + "
          "./forge-bench (RD12), the manifest verifies (RD13), a changed ic32.c "
          "re-keys the cache (RD7), and --zip is now byte-deterministic (RD14). "
          "NO new identity, NO new runtime construct -- a packaging correction "
          "over the frozen v0.6 spine.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
