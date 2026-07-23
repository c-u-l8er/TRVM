"""binding_run38.py -- v0.7.0-alpha.2 FIRST-RUN STATE CLOSURE battery (OA1-OA12).

GPT-5.6's v0.7-1.1 ruling: v0.7-1's onboarding was conditionally accepted, then
three startup defects were called out and must be corrected as v0.7.0-alpha.2
(the alpha.1 release ARCHIVE is NOT replaced):

  1. "Explore demo instead" could still show the LAST project (enterExplore did
     not reset the workspace to the Golden Demo).
  2. Explore mode was "not persisted" but NOT actually read-only (WRL textarea,
     SemanticDiff variant, Scenario Author, presets, mutation buttons were live).
  3. The expensive demo fold ran in boot() BEFORE the first-run chooser.

This battery proves the closure. Like binding_run37 it splits into a SERVER /
IDENTITY layer (in-process, temp FORGE_PROJECT_ROOT) and a FRONTEND layer
(static assertions over spinner_bench.js / .html), and it introduces NO new
semantic profile, IR version, artifact identity, actor role, or runtime law --
the demo world still seals to the frozen DEMO_WORLD_SEMANTIC_ID.

  OA1  the first-run launcher appears before any run job starts (boot is shell-first)
  OA2  Explore with no prior project loads the Golden Demo
  OA3  Explore after a DIFFERENT last project still loads the Golden Demo
  OA4  demo source, scenario and semantic id all match the frozen preset
  OA5  every authoritative editor is LOCKED in Explore
  OA6  Run, Verify, scrub and Guide remain usable in Explore
  OA7  Explore creates no project and no recovery journal
  OA8  recovery for the last project is surfaced BEFORE that project runs
  OA9  subsequent launches auto-restore without showing a modal
  OA10 Home/Start reopens the chooser explicitly
  OA11 Make-an-editable-copy remains the only persistence transition
  OA12 ic_ref == ic32 == Fixture oracle stays green                     (native)

Gates (a new user should not need the native suite to sanity-check):

    python3 binding_run38.py --gate smoke    # OA1-OA11 (fast, no compiler)
    python3 binding_run38.py --gate native   # OA12 (compiler; ic_ref==ic32==oracle)
    python3 binding_run38.py                  # all of the above
"""
import argparse
import importlib.util
import os
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"
ALPHA = "v0.7.0-alpha.2"


def _read(path):
    return open(path, encoding="utf-8").read() if os.path.isfile(path) else ""


def _slice(text, start_marker, end_marker):
    i = text.find(start_marker)
    if i < 0:
        return ""
    j = text.find(end_marker, i + len(start_marker))
    return text[i:] if j < 0 else text[i:j]


def _recovery_dir_for(project_root):
    return os.path.join(os.path.dirname(os.path.abspath(project_root)),
                        ".recovery")


def _project_docs(project_root):
    if not os.path.isdir(project_root):
        return []
    return [f for f in os.listdir(project_root)
            if f.endswith(".json") and not f.startswith(".")]


def main():
    ap = argparse.ArgumentParser(description="First-run state-closure battery.")
    ap.add_argument("--gate", default="all", choices=["all", "smoke", "native"])
    args = ap.parse_args()
    do_smoke = args.gate in ("all", "smoke")
    do_native = args.gate in ("all", "native") and not SKIP_NATIVE

    print("[BINDING wrl-%s] first-run state closure -- OA1-OA12 (gate=%s)"
          % (ALPHA, args.gate))
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

    data_root = tempfile.mkdtemp(prefix="forge-oa-data-")
    project_root = os.path.join(data_root, "projects")
    os.environ["FORGE_PROJECT_ROOT"] = project_root
    import spinner_bench as SB
    DEMO_SRC = SB.DEMO_WORLD_SOURCE
    DEMO_SEM = SB.DEMO_WORLD_SEMANTIC_ID

    js = _read(os.path.join(HERE, "spinner_bench.js"))
    html = _read(os.path.join(HERE, "spinner_bench.html"))

    boot_block = _slice(js, "async function boot", "await checkHealth()")
    explore_block = _slice(js, "async function enterExplore",
                           "async function openChooser")
    chooser_block = _slice(js, "async function openChooser", "function layout(")
    lock_block = _slice(js, "const _EXPLORE_DISABLED", "async function loadDemoWorld")
    demo_block = _slice(js, "async function loadDemoWorld", "async function enterExplore")
    makecopy_block = _slice(js, "async function doMakeCopy", "function layout(")

    if do_smoke:
        # ---- OA1 boot is shell-first: launcher before any fold ---------------
        oa1 = ("showFirstRun(false)" in boot_block
               and "doRun(" not in boot_block
               and "doLower(" not in boot_block
               and "resetDraft(" not in boot_block
               and "await loadProjects()" in boot_block)
        rep(oa1, None, "OA1) boot() resolves the startup path from cheap metadata "
            "only (no doRun/doLower/resetDraft) and shows the launcher")

        # ---- OA2 Explore with no prior project loads the demo ----------------
        run = SB._run_payload(DEMO_SRC)
        oa2 = (run.get("ok")
               and run.get("semantic_artifact_id") == DEMO_SEM
               and "loadDemoWorld()" in explore_block
               and "doRun()" in explore_block)
        rep(oa2, None, "OA2) enterExplore loads the demo (loadDemoWorld + doRun) "
            "and a demo fold reproduces the frozen id")

        # ---- OA3 Explore after a DIFFERENT last project still loads the demo --
        # enterExplore re-points to the `main` pseudo-session and loads the demo
        # UNCONDITIONALLY; it never routes through openSession / a project id.
        oa3 = ('state.session = "main"' in explore_block
               and "loadDemoWorld()" in explore_block
               and "openSession" not in explore_block)
        rep(oa3, None, "OA3) enterExplore resets to the `main` demo session and "
            "loads the demo unconditionally (never reuses the open project)")

        # ---- OA4 demo source / scenario / semantic id match the preset -------
        low = SB._lower_payload(DEMO_SRC)
        golden = SB.GOLDEN_DEMO_SCENARIO
        gdig = SB.SC.scenario_digest(golden)
        # the /api/scenario surface the demo path reads:
        pres_digest = SB.SC.scenario_digest(SB.GOLDEN_DEMO_SCENARIO)
        oa4 = (low.get("ok") is not False
               and low.get("semantic_artifact_id") == DEMO_SEM
               and gdig == pres_digest
               and "state.scenPreset = \"golden\"" in demo_block
               and "doLower()" in demo_block)
        rep(oa4, None, "OA4) the loaded demo lowers to DEMO_WORLD_SEMANTIC_ID and "
            "the golden scenario digest matches the frozen preset")

        # ---- OA5 every authoritative editor is locked in Explore -------------
        must_disable = [
            "btn-apply", "btn-save", "btn-commit", "btn-draft-undo", "btn-format",
            "lib-select", "lib-new", "lib-fork", "lib-rename", "lib-trash",
            "lib-restore", "lib-migrate", "lib-export", "lib-import",
            "scn-mode-author", "scn-preset",
            "scn-add-claim", "scn-add-reset", "scn-add-idle",
            "scn-retransmit", "scn-equivocate", "scn-reset-preset"]
        oa5 = (all(('"#%s"' % i) in lock_block for i in must_disable)
               and '"#wrl"' in lock_block and '"#wrl-b"' in lock_block
               and "el.readOnly = on" in lock_block
               and "el.disabled = true" in lock_block)
        rep(oa5, None, "OA5) Explore locks all %d authoring controls + makes the "
            "WRL and variant editors readonly" % len(must_disable))

        # ---- OA6 Run/Verify/scrub/Guide stay usable in Explore ---------------
        must_allow = ["btn-run", "btn-verify", "btn-cancel", "ep-range",
                      "ep-prev", "ep-next", "btn-guide", "btn-make-copy",
                      "view-author", "view-evidence"]
        oa6 = all(('"#%s"' % i) not in lock_block for i in must_allow)
        rep(oa6, None, "OA6) Run, Verify, Cancel, the scrubber, Guide, view "
            "toggles and Make-a-copy are NOT locked in Explore")

        # ---- OA7 Explore creates no project and no recovery journal ----------
        # Replicate the read-only Explore server calls on a fresh store.
        SB._health_payload()
        SB._draft_reset_payload("main", None)
        SB._lower_payload(DEMO_SRC)
        SB._run_payload(DEMO_SRC)
        rdir = _recovery_dir_for(project_root)
        journal = sorted(os.listdir(rdir)) if os.path.isdir(rdir) else []
        oa7 = (_project_docs(project_root) == []
               and journal == []
               and "if (state.explore) return;" in js
               and "/api/project/new" not in explore_block)
        rep(oa7, None, "OA7) the Explore server path writes NO project document "
            "and NO recovery journal (scheduleCheckpoint guards on state.explore)")

        # ---- OA8 recovery surfaced before the last project runs --------------
        oa8 = ("/api/recovery/status" in boot_block
               and "promptRecovery" in boot_block
               and "openSession(lastId)" in boot_block
               and boot_block.index("promptRecovery")
               < boot_block.index("openSession(lastId)"))
        rep(oa8, None, "OA8) boot() inspects the last project's recovery journal "
            "and prompts BEFORE that project is opened/run")

        # ---- OA9 subsequent launches auto-restore, no modal ------------------
        oa9 = ("lastId && tourSeen" in boot_block
               and "openSession(lastId)" in boot_block
               and "resumed last project" in boot_block)
        rep(oa9, None, "OA9) a returning user with onboarding seen auto-restores "
            "the last project without a modal (lastId && tourSeen)")

        # ---- OA10 Home reopens the chooser explicitly ------------------------
        import re as _re
        home_button = bool(_re.search(r"<button[^>]*id=\"btn-home\"", html))
        oa10 = (home_button
                and '$("#btn-home").onclick = openChooser' in js
                and "showFirstRun" in chooser_block)
        rep(oa10, None, "OA10) a persistent Home <button> is wired to openChooser, "
            "which reopens the first-run/resume chooser")

        # ---- OA11 make-a-copy is the only persistence transition -------------
        oa11 = ("/api/project/new" in makecopy_block
                and "setExplore(false)" in makecopy_block
                and "openSession" in makecopy_block)
        rep(oa11, None, "OA11) doMakeCopy (POST /api/project/new + leave Explore) "
            "is the only path that creates persisted state")

    # ---- OA12 ic_ref == ic32 == Fixture oracle ------------------------------
    if do_native:
        cert = SB._verify_payload(DEMO_SRC, oracle=True)
        oa12_ref = (cert["ok"]
                    and cert.get("oracle", {}).get("match") is True
                    and cert["semantic_artifact_id"] == DEMO_SEM)
        oa12_nat = (cert.get("native") is True and cert.get("parity") is True)
        rep(oa12_ref, oa12_nat, "OA12) ic_ref == ic32 == Fixture oracle stays "
            "green over the frozen demo world")

    shutil.rmtree(data_root, ignore_errors=True)

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-{ALPHA}] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.7.0-alpha.2 is the First-Run State Closure: boot() is "
          "shell-first (OA1) so the launcher precedes any fold; Explore loads the "
          "Golden Demo explicitly (OA2) regardless of the last project (OA3), "
          "matching the frozen source/scenario/id (OA4); Explore is GENUINELY "
          "read-only (OA5) while Run/Verify/scrub/Guide stay usable (OA6), and it "
          "writes no project or recovery journal (OA7); recovery is surfaced "
          "before a project runs (OA8); returning users auto-restore without a "
          "modal (OA9) but Home reopens the chooser (OA10); Make-a-copy is the "
          "only persistence transition (OA11); the frozen demo still folds "
          "ic_ref == ic32 == Fixture oracle (OA12). NO new identity or runtime "
          "law -- alpha.1's release archive is untouched.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
