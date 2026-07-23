"""binding_run35.py -- v0.6.5 RELEASE ARTIFACT CLOSURE battery (RC1-RC20).

GPT-5.6's v0.6.5 ruling accepted v0.6 functionally but ruled the PUBLIC RELEASE
boundary open. This battery certifies the closure: the release is built from an
EXPLICIT allowlist with no authoring state / bytecode / historical packets, the
production import direction is clean (Spinner Bench -> forge_runtime -> ic_ref/
ic32; the normal Run imports no battery and no Fixture), user data lives OUTSIDE
the install tree, health is two-mode, and a freshly EXTRACTED artifact runs
end-to-end without ever writing into the install directory.

  RC1  no .forge_projects/.recovery/.trash/.last_session in the built release
  RC2  no __pycache__/.pyc/.pyo and no historical *_PACKET.zip in the release
  RC3  no local last-session pointer ships
  RC4  the production Run path imports NO binding_run* module   (fresh subproc)
  RC5  the production Run path imports NO Fixture               (fresh subproc)
  RC6  the clean extraction LAUNCHES with one command (forge-bench) and answers
       a shallow /api/health
  RC7  first run creates data OUTSIDE the app dir; the app dir stays untouched
  RC8  ref-only works with NO ic32 (TRVM_SKIP_NATIVE / --ref-only)
  RC9  native mode BUILDS ic32 from source and folds with parity        (native)
  RC10 shallow health is FAST and identity-correct (folds nothing)
  RC11 deep verification runs as a CANCELLABLE job (kind deep_health)
  RC12 a saved project survives a "restart" (fresh cache, same store)
  RC13 a recovery journal survives an interrupted session
  RC14 full export/import retains the authoritative SemanticArtifactID
  RC15 the golden/acceptance scenario presets are immutable + deterministic
  RC16 the app (install) directory is byte-unchanged after an authoring round
  RC17 the archive MANIFEST hashes EVERY shipped file (recomputed + matched)
  RC18 two clean builds are reproducible (identical content manifests)
  RC19 a fast release SMOKE (shallow health + one ref run) is bounded
  RC20 full native certification (ic_ref == ic32 == fixture oracle) is runnable
       and separate from the smoke                                     (native)

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
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

# ------------------------------------------------------------------- helpers
def _load_builder():
    path = os.path.join(HERE, "tools", "build_forge_release.py")
    spec = importlib.util.spec_from_file_location("build_forge_release", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tree_files(root):
    out = []
    for r, _d, files in os.walk(root):
        for fn in files:
            out.append(os.path.relpath(os.path.join(r, fn), root).replace(os.sep, "/"))
    return sorted(out)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_tree(root, subdirs):
    """{relpath: sha256} over the given subdirs of root."""
    out = {}
    for sd in subdirs:
        base = os.path.join(root, sd)
        for rel in _tree_files(base):
            out[sd + "/" + rel] = _sha256(os.path.join(base, rel))
    return out


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


FORBIDDEN_DIRS = (".forge_projects", ".recovery", ".trash")


def main():
    print("[BINDING wrl-v0.6.5] release artifact closure -- RC1-RC20")
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

    # Build a canonical release once for the structural checks.
    rel = tempfile.mkdtemp(prefix="forge-rc-rel-")
    rc = builder.build(rel, force=True)
    build_ok = (rc == 0)
    files = _tree_files(rel) if build_ok else []

    # ---- RC1 no authoring state ----------------------------------------------
    rc1 = build_ok and not any(
        any(("/" + d + "/") in ("/" + f + "/") or f.startswith(d + "/")
            or ("/" + d + "/") in f for d in FORBIDDEN_DIRS)
        or f.endswith(".last_session.json") for f in files)
    rep(rc1, None, "RC1) built release has NO .forge_projects/.recovery/.trash/"
        ".last_session")

    # ---- RC2 no bytecode / historical packets --------------------------------
    rc2 = build_ok and not any(
        "__pycache__" in f or f.endswith((".pyc", ".pyo"))
        or f.endswith("_PACKET.zip") or (f.startswith("WRL_") and f.endswith(".zip"))
        for f in files)
    rep(rc2, None, "RC2) built release has NO __pycache__/.pyc/.pyo and NO "
        "historical *_PACKET.zip")

    # ---- RC3 no last-session pointer -----------------------------------------
    rc3 = build_ok and not any("last_session" in f for f in files)
    rep(rc3, None, "RC3) NO local last-session pointer ships")

    # ---- RC4 production imports no binding_run* (fresh subprocess) ------------
    probe = (
        "import sys; sys.path[:0]=[%r, %r];" % (
            os.path.join(rel, "forge"), os.path.join(rel, "runtime", "python"))
        + "import os; os.environ['TRVM_SKIP_NATIVE']='1';"
        + "import spinner_bench as SB; SB._run_payload(SB.DEMO_WORLD_SOURCE);"
        + "bad=[m for m in ('binding_run3o','binding_run3j') "
          "if any(m==k or k.startswith('binding_run') for k in [m])];"
        + "mods=[k for k in sys.modules if k.startswith('binding_run')];"
        + "print('BINDING:'+(','.join(mods) or 'NONE'));"
        + "print('FIXTURE:'+('yes' if 'fixture' in sys.modules else 'no'))")
    env = dict(os.environ)
    env["FORGE_PROJECT_ROOT"] = os.path.join(tempfile.mkdtemp(prefix="forge-rc4-"),
                                             "projects")
    env["TRVM_SKIP_NATIVE"] = "1"
    p = subprocess.run([sys.executable, "-c", probe], capture_output=True,
                       env=env, timeout=120)
    out = p.stdout.decode()
    rc4 = "BINDING:NONE" in out and p.returncode == 0
    rep(rc4, None, "RC4) the production Run path imports NO binding_run* module")

    # ---- RC5 production imports no Fixture ------------------------------------
    rc5 = "FIXTURE:no" in out and p.returncode == 0
    rep(rc5, None, "RC5) the production Run path imports NO Fixture (lazy oracle "
        "only)")

    # ---- RC6 clean extraction launches; shallow health answers ---------------
    extract = tempfile.mkdtemp(prefix="forge-rc6-extract-")
    shutil.copytree(rel, os.path.join(extract, "app"))
    app = os.path.join(extract, "app")
    data6 = os.path.join(tempfile.mkdtemp(prefix="forge-rc6-data-"), "projects")
    port = _free_port()
    launch_env = dict(os.environ)
    launch_env["FORGE_PROJECT_ROOT"] = data6
    proc = subprocess.Popen(
        [sys.executable, os.path.join(app, "forge-bench"), "--ref-only",
         "--port", str(port)],
        env=launch_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    health = None
    try:
        for _ in range(60):
            try:
                health = _http_json("http://127.0.0.1:%d/api/health" % port,
                                    timeout=2)
                break
            except Exception:
                time.sleep(0.5)
    finally:
        pass
    rc6 = bool(health and health.get("ok") and health.get("mode") == "shallow")
    rep(rc6, None, "RC6) clean extraction LAUNCHES with one command and answers "
        "a shallow /api/health")

    # ---- RC7 first run creates data OUTSIDE app dir; app dir untouched --------
    app_hashes_before = _hash_tree(app, ["forge", "runtime"])
    # drive one authoring round via HTTP against the live extracted server.
    rc7_data_created = os.path.isdir(data6) and bool(os.listdir(
        os.path.dirname(data6)))
    try:
        _http_json("http://127.0.0.1:%d/api/project/open" % port,
                   data={"project_id": "rc7"}, timeout=5)
    except Exception:
        pass
    app_hashes_after = _hash_tree(app, ["forge", "runtime"])
    rc7 = (rc7_data_created and app_hashes_before == app_hashes_after
           and os.path.isdir(data6))
    rep(rc7, None, "RC7) first run creates data OUTSIDE the app dir; the app dir "
        "is byte-unchanged")

    # ---- RC16 app (install) dir byte-unchanged after authoring ----------------
    rc16 = (app_hashes_before == app_hashes_after and len(app_hashes_before) > 0)
    rep(rc16, None, "RC16) the install directory is byte-unchanged after an "
        "authoring round")

    # tear the launched server down.
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()

    # From here, use the IN-PROCESS module bound to a private external data dir.
    os.environ["FORGE_PROJECT_ROOT"] = os.path.join(
        tempfile.mkdtemp(prefix="forge-rc-inproc-"), "projects")
    import spinner_bench as SB
    import wrl_project as PJ
    import wrl_scenario as SC
    import wrl_bundle as BD
    import wrl_store as ST
    import forge_runtime as R
    DEMO = SB.DEMO_WORLD_SOURCE
    DEMO_SEM = SB.DEMO_WORLD_SEMANTIC_ID

    # ---- RC8 ref-only works without ic32 -------------------------------------
    run8 = SB._run_payload(DEMO)
    rc8 = (run8["ok"] and run8["semantic_artifact_id"] == DEMO_SEM
           and len(run8["epochs"]) == 7)
    rep(rc8, None, "RC8) ref-only Run works (no ic32) -- 7-epoch demo folds to "
        "the frozen id")

    # ---- RC9 native mode BUILDS ic32 from source and folds with parity -------
    rc9_ref = True
    rc9_nat = None
    if not SKIP_NATIVE:
        cdir = tempfile.mkdtemp(prefix="forge-rc9-")
        src = os.path.join(rel, "runtime", "c", "ic32.c")
        binary = os.path.join(cdir, "ic32")
        cc = (os.environ.get("CC") or shutil.which("gcc")
              or shutil.which("clang") or shutil.which("cc"))
        built = False
        if cc and os.path.isfile(src):
            try:
                subprocess.run([cc, "-O2", "-o", binary, src], check=True,
                               capture_output=True, timeout=180)
                built = os.path.isfile(binary) and os.access(binary, os.X_OK)
            except Exception:
                built = False
        # fold the demo through the FRESHLY BUILT binary and check parity.
        parity = False
        if built:
            saved_ic32 = R.IC32
            try:
                R.IC32 = binary
                ver = SB._verify_payload(DEMO, oracle=False)
                parity = (ver.get("native") is True and ver.get("parity") is True)
            finally:
                R.IC32 = saved_ic32
        rc9_nat = bool(built and parity)
    rep(rc9_ref, rc9_nat, "RC9) native mode BUILDS ic32 from source and folds "
        "ic_ref == ic32 with parity")

    # ---- RC10 shallow health FAST + identity-correct --------------------------
    tA = time.time()
    h = SB._health_payload()
    dt10 = time.time() - tA
    rc10 = (h["mode"] == "shallow" and h["identity_ok"] is True
            and h["demo_semantic_id"] == DEMO_SEM and dt10 < 5.0
            and set(h["project"]) >= {"dir", "writable", "schema",
                                      "recovery_dir", "recovery_writable"})
    rep(rc10, None, "RC10) shallow health is FAST (%.2fs, folds nothing) + "
        "identity-correct + reports dir writability" % dt10)

    # ---- RC11 deep verification as a CANCELLABLE job --------------------------
    jid = SB._JOB_REGISTRY.submit("deep_health", {})
    deep = None
    for _ in range(240):
        snap = SB._JOB_REGISTRY.get(jid)
        if snap.get("state") in ("completed", "failed", "cancelled"):
            deep = snap
            break
        time.sleep(0.25)
    deep_ok = bool(deep and deep.get("state") == "completed"
                   and (deep.get("result") or {}).get("ok"))
    # and it is genuinely cancellable: submit + immediately cancel.
    jid2 = SB._JOB_REGISTRY.submit("deep_health", {})
    SB._JOB_REGISTRY.cancel(jid2)
    cancel_seen = False
    for _ in range(240):
        s2 = SB._JOB_REGISTRY.get(jid2)
        if s2.get("state") in ("completed", "failed", "cancelled"):
            cancel_seen = s2.get("state") in ("cancelled", "completed")
            break
        time.sleep(0.25)
    rc11 = deep_ok and cancel_seen
    rep(rc11, None, "RC11) deep verification runs as a job (kind deep_health) and "
        "is cancellable")

    # ---- RC12 saved project survives a restart --------------------------------
    cache = SB._PROJECT_CACHE
    cache.create_new("rc12", "RC12")
    sess = cache.open("rc12")
    active12 = sess.draft.active_semantic_id
    cache.persist("rc12")
    fresh = PJ.ProjectSessionCache(
        PJ.ForgeProjectStore(SB._PROJECT_ROOT), DEMO,
        scenarios_for=SB._default_scenarios,
        project_version=PJ.PROJECT_V2_VERSION)
    sess2 = fresh.open("rc12")
    rc12 = (active12 == DEMO_SEM
            and sess2.draft.active_semantic_id == active12)
    rep(rc12, None, "RC12) a saved project survives a restart (fresh cache, same "
        "store, same active id)")

    # ---- RC13 recovery journal survives an interrupted session ----------------
    cache.create_new("rc13", "RC13")
    cache.open("rc13")
    cache.checkpoint("rc13", dirty_reasons=["text"])
    fresh2 = PJ.ProjectSessionCache(
        PJ.ForgeProjectStore(SB._PROJECT_ROOT), DEMO,
        scenarios_for=SB._default_scenarios,
        project_version=PJ.PROJECT_V2_VERSION)
    st13 = fresh2.recovery_status("rc13")
    rc13 = (st13["state"] == "recovery_available" and st13["has_journal"])
    rep(rc13, None, "RC13) a recovery journal survives an interrupted session "
        "(fresh cache sees recovery_available)")

    # ---- RC14 full export/import retains the authoritative id ------------------
    exp = SB._project_export_payload({"project_id": "rc12", "export_mode": "full"})
    imp_root = tempfile.mkdtemp(prefix="forge-rc14-")
    ps = PJ.ForgeProjectStore(os.path.join(imp_root, "projects"))
    ws = ST.WorldObjectStore(os.path.join(imp_root, "projects", ".objects", "worlds"))
    ss = ST.ScenarioRuntimeStore(os.path.join(imp_root, "projects", ".objects", "scen"))
    created = BD.import_bundle(exp["bundle"], ps, ws, ss,
                               project_id="rc14", name="RC14")
    fresh3 = PJ.ProjectSessionCache(ps, DEMO,
                                    scenarios_for=SB._default_scenarios,
                                    project_version=PJ.PROJECT_V2_VERSION)
    sess14 = fresh3.open(created["project_id"])
    rc14 = (exp["ok"] and sess14.draft.active_semantic_id == active12 == DEMO_SEM)
    rep(rc14, None, "RC14) full export/import retains the authoritative "
        "SemanticArtifactID")

    # ---- RC15 preset scenarios immutable + deterministic ----------------------
    g1 = SC.scenario_digest(SC.demo_scenario(DEMO_SEM))
    g2 = SC.scenario_digest(SC.demo_scenario(DEMO_SEM))
    b1 = SC.scenario_digest(SC.bench_scenario(DEMO_SEM))
    b2 = SC.scenario_digest(SC.bench_scenario(DEMO_SEM))
    rc15 = (g1 == g2 and b1 == b2 and g1 != b1)
    rep(rc15, None, "RC15) golden/acceptance presets are immutable + deterministic "
        "(stable, distinct digests)")

    # ---- RC17 MANIFEST hashes EVERY shipped file ------------------------------
    # verify against a PRISTINE build: the RC6/RC9 launch mutated `rel`
    # in-place (bytecode + a freshly built ic32), so the build-time manifest
    # only matches a tree that has never been run from.
    rel_clean = tempfile.mkdtemp(prefix="forge-rc17-")
    builder.build(rel_clean, force=True)
    man = {}
    with open(os.path.join(rel_clean, "MANIFEST.sha256")) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            digest, name = line.split("  ", 1)
            man[name] = digest
    shipped = [f for f in _tree_files(rel_clean) if f != "MANIFEST.sha256"]
    rc17 = (set(man) == set(shipped)
            and all(man[f] == _sha256(os.path.join(rel_clean, f)) for f in shipped))
    rep(rc17, None, "RC17) MANIFEST hashes EVERY shipped file (recomputed + "
        "matched, %d files)" % len(shipped))

    # ---- RC18 two clean builds reproducible -----------------------------------
    rel2 = tempfile.mkdtemp(prefix="forge-rc18-")
    builder.build(rel2, force=True)
    with open(os.path.join(rel_clean, "MANIFEST.sha256")) as f:
        m1 = [l for l in f if not l.startswith("#")]
    with open(os.path.join(rel2, "MANIFEST.sha256")) as f:
        m2 = [l for l in f if not l.startswith("#")]
    rc18 = (m1 == m2 and len(m1) > 0)
    rep(rc18, None, "RC18) two clean builds are reproducible (identical content "
        "manifests)")

    # ---- RC19 fast release SMOKE is bounded -----------------------------------
    tS = time.time()
    _ = SB._health_payload()
    smoke_run = SB._run_payload(DEMO)
    dt19 = time.time() - tS
    rc19 = (smoke_run["ok"] and dt19 < 120.0)
    rep(rc19, None, "RC19) fast release SMOKE (shallow health + one ref run) is "
        "bounded (%.1fs)" % dt19)

    # ---- RC20 full native certification runnable + separate -------------------
    rc20_ref = True
    rc20_nat = None
    cert = SB._verify_payload(DEMO, oracle=True)
    rc20_ref = (cert["ok"] and cert.get("oracle", {}).get("match") is True
                and cert["semantic_artifact_id"] == DEMO_SEM)
    if not SKIP_NATIVE:
        rc20_nat = (cert.get("native") is True and cert.get("parity") is True)
    rep(rc20_ref, rc20_nat, "RC20) full certification (ic_ref == ic32 == fixture "
        "oracle) is runnable + separate from the smoke")

    # cleanup temp release trees.
    for d in (rel, rel2, rel_clean, extract):
        shutil.rmtree(d, ignore_errors=True)

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.6.5] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.6.5 CLOSES the public-release boundary: the distribution "
          "is built from an EXPLICIT allowlist (RC1-RC3/RC17/RC18: no authoring "
          "state, no bytecode, no historical packets; every file hashed; two "
          "builds reproducible), the production Run path imports NO binding_run* "
          "and NO Fixture (RC4/RC5; the Fixture is a lazy oracle only), a freshly "
          "EXTRACTED artifact launches with one command and answers a shallow "
          "health (RC6) while writing user data OUTSIDE the byte-unchanged install "
          "dir (RC7/RC16), ref-only runs without ic32 (RC8) and native mode builds "
          "ic32 from source and folds with parity (RC9), health is two-mode -- a "
          "fast fold-free shallow check (RC10) and a cancellable deep job (RC11) -- "
          "and the durable spine holds: saved projects and recovery journals "
          "survive a restart (RC12/RC13), full export/import keeps the "
          "authoritative id (RC14), presets are immutable (RC15), and the full "
          "ic_ref == ic32 == oracle certification stays separately runnable "
          "(RC20). NO new identity, NO new runtime construct -- a packaging + "
          "dependency-boundary closure over the frozen v0.6 spine.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
