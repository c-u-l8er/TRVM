"""binding_run37.py -- v0.7.0-alpha.1 GUIDED FIRST RUN + ALPHA CUT battery (PA1-PA20).

GPT-5.6's v0.7-1 ruling: the "Guided First Run + Alpha Version Cut" milestone is
PRODUCT-FACING UI/UX ONLY -- NO new semantic profile, IR version, artifact
identity, actor role, or runtime law. The demo world still seals to the frozen
DEMO_WORLD_SEMANTIC_ID and every fold is byte-identical to v0.6-4. This battery
proves exactly that: the onboarding surfaces are added, the version cut is
consistent across every reported surface, and NONE of it moves a Forge identity
or perturbs a fold.

The onboarding logic splits cleanly into two enforcement layers:

  * SERVER / IDENTITY / ARTIFACT (in-process, temp FORGE_PROJECT_ROOT):
      PA1  a fresh store has no projects -> the client shows the launcher
      PA2  merely reading the demo (health/session) creates NO project
      PA3  no project + no edit -> no recovery journal on disk
      PA4  a demo Run reproduces the frozen id + exactly 7 epochs
      PA7  the last-session pointer round-trips (restoration works)
      PA9  "make an editable copy" creates a real project EXPLICITLY
      PA10 a fresh copy shares the preset's immutable active id initially
      PA11 a guided rotor edit moves the CANDIDATE id, not the ACTIVE id
      PA12 Undo restores the EXACT original candidate id
      PA13 a commit follows the scenario-compatibility law (digest invariant)
      PA17 GET /api/health reports v0.7.0-alpha.1 (the server surface)
      PA18 the dist ZIP / clean build ships the root README.md
      PA19 every authoring write lands EXTERNAL to the install (project dir)
      PA20 ic_ref == ic32 == Fixture oracle certification stays green    (native)

  * FRONTEND (static assertions over spinner_bench.js / .html, following the
    prior-slice pattern where browser-only UI is verified statically + live):
      PA5  the guided tour stores its state in localStorage, not the API
      PA6  dismissing the tour persists only a presentation preference
      PA8  the recovery prompt takes precedence over the first-run landing
      PA14 switching Author/Evidence view calls no API and folds nothing
      PA15 every onboarding control is a focusable <button> (keyboard-reachable)
      PA16 the tour highlights labelled panels (ARIA)
      PA17 the browser header + docs + archive name report v0.7.0-alpha.1

Operational gates (a new user should not need the native suite to sanity-check):

    python3 binding_run37.py --gate smoke    # PA1-3,5-19 (fast, no compiler)
    python3 binding_run37.py --gate native   # PA20 (compiler; ic_ref==ic32==oracle)
    python3 binding_run37.py                  # all of the above

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import argparse
import importlib.util
import json
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
# The alpha-cut consistency battery tracks the CURRENT source version. Each prior
# release ARCHIVE is unchanged; v0.7.0-alpha.2 was the First-Run State Closure
# (binding_run38.py, OA1-OA12), v0.7.0-alpha.3 was the Error and Progress UX
# Closure (binding_run39.py, PB1-PB20), v0.7.0-alpha.4 was the Immutable
# Template Catalog (binding_run40.py, PC1-PC24) + v0.7-3.1 reopen closure
# (binding_run41.py, PC25-PC30), and v0.7.0-alpha.5 is the Visual / Responsive
# Closure (binding_run42.py, PC31-PC38).
ALPHA = "v0.7.0-alpha.5"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_builder():
    return _load(os.path.join(HERE, "tools", "build_forge_release.py"),
                 "build_forge_release")


def _read(path):
    return open(path, encoding="utf-8").read() if os.path.isfile(path) else ""


def _recovery_dir_for(project_root):
    return os.path.join(os.path.dirname(os.path.abspath(project_root)),
                        ".recovery")


def main():
    ap = argparse.ArgumentParser(description="Guided first-run + alpha-cut battery.")
    ap.add_argument("--gate", default="all",
                    choices=["all", "smoke", "native"])
    args = ap.parse_args()
    gate = args.gate
    do_smoke = gate in ("all", "smoke")
    do_native = gate in ("all", "native") and not SKIP_NATIVE

    print("[BINDING wrl-%s] guided first run + alpha cut -- PA1-PA20 "
          "(gate=%s)" % (ALPHA, gate))
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

    # ---- an isolated external data dir; import the server against it ----------
    data_root = tempfile.mkdtemp(prefix="forge-pa-data-")
    project_root = os.path.join(data_root, "projects")
    os.environ["FORGE_PROJECT_ROOT"] = project_root
    import spinner_bench as SB
    DEMO_SRC = SB.DEMO_WORLD_SOURCE
    DEMO_SEM = SB.DEMO_WORLD_SEMANTIC_ID
    # a rotor edit: swap the named rotor -> a DIFFERENT numeric rotor -> the
    # world's SemanticArtifactID moves (a real identity edit, not presentation).
    ROTOR_EDIT = DEMO_SRC.replace("rotor=quarter_turn_z", "rotor=identity")
    assert ROTOR_EDIT != DEMO_SRC

    js = _read(os.path.join(HERE, "spinner_bench.js"))
    html = _read(os.path.join(HERE, "spinner_bench.html"))

    # =====================================================================
    # SERVER / IDENTITY / ARTIFACT
    # =====================================================================
    if do_smoke:
        # ---- PA1 fresh store has no projects (client shows the launcher) ------
        projects0 = SB._projects_payload()["projects"]
        # the frontend boot() shows the launcher when there is no last project:
        pa1 = (projects0 == []
               and "showFirstRun(false)" in js)
        rep(pa1, None, "PA1) a fresh store lists NO projects and boot() shows the "
            "first-run launcher (showFirstRun(false))")

        # ---- PA2 reading the demo creates NO project --------------------------
        # The store may ensure its (empty) root exists at construction; the true
        # "creates NO project" invariant is that no project DOCUMENT is written --
        # the project list stays empty and no project .json lands on disk.
        _ = SB._health_payload()
        _ = SB._session_payload()
        proj_docs = ([f for f in os.listdir(project_root)
                      if f.endswith(".json") and not f.startswith(".")]
                     if os.path.isdir(project_root) else [])
        pa2 = (SB._projects_payload()["projects"] == [] and proj_docs == [])
        rep(pa2, None, "PA2) reading health/session (the read-only Explore path) "
            "creates NO project document (empty list + no project .json)")

        # ---- PA3 no project + no edit -> no recovery journal ------------------
        rdir = _recovery_dir_for(project_root)
        journal_files = (sorted(os.listdir(rdir))
                         if os.path.isdir(rdir) else [])
        # the client guard that keeps Explore from checkpointing:
        pa3 = (journal_files == []
               and "if (state.explore) return;" in js)
        rep(pa3, None, "PA3) no project + no edit writes NO recovery journal "
            "(scheduleCheckpoint guards on state.explore)")

        # ---- PA4 a demo Run reproduces the frozen id + exactly 7 epochs -------
        run = SB._run_payload(DEMO_SRC)
        pa4 = (run.get("ok")
               and run.get("semantic_artifact_id") == DEMO_SEM
               and len(run.get("epochs", [])) == 7)
        rep(pa4, None, "PA4) a guided demo Run reproduces the frozen "
            "DEMO_WORLD_SEMANTIC_ID over exactly 7 epochs")

        # ---- PA9 "make an editable copy" creates a real project EXPLICITLY ----
        made = SB._project_new_payload({"project_id": "copy1", "name": "Copy 1"})
        pa9 = (made.get("ok")
               and "copy1" in [p["project_id"]
                               for p in SB._projects_payload()["projects"]]
               and "doMakeCopy" in js
               and "/api/project/new" in js)
        rep(pa9, None, "PA9) Make-an-editable-copy creates a real persisted "
            "project explicitly (doMakeCopy -> POST /api/project/new)")

        # ---- PA10 a fresh copy shares the preset's immutable active id --------
        view = made["view"]
        pa10 = (view["active_semantic_id"] == DEMO_SEM
                and view["candidate_semantic_id"] == DEMO_SEM)
        rep(pa10, None, "PA10) a freshly made copy shares the preset's immutable "
            "active + candidate id (== DEMO_WORLD_SEMANTIC_ID) initially")

        # ---- PA11 a guided rotor edit moves CANDIDATE not ACTIVE --------------
        src_res = SB._draft_source_payload(
            {"session_id": "copy1", "replace_id": "pa-rotor-1",
             "source": ROTOR_EDIT})
        v2 = src_res["view"]
        pa11 = (src_res.get("ok")
                and v2["candidate_valid"] is True
                and v2["candidate_semantic_id"] != DEMO_SEM
                and v2["active_semantic_id"] == DEMO_SEM)
        rep(pa11, None, "PA11) a guided rotor edit moves the CANDIDATE id "
            "(%s) while the ACTIVE id stays the preset's"
            % (v2["candidate_semantic_id"][:16] + "..."))

        # ---- PA12 Undo restores the EXACT original candidate id --------------
        und = SB._draft_undo_payload("copy1")
        v3 = und["view"]
        pa12 = (und.get("ok") and und.get("undone") is True
                and v3["candidate_semantic_id"] == DEMO_SEM
                and v3["active_semantic_id"] == DEMO_SEM)
        rep(pa12, None, "PA12) Undo restores the EXACT original candidate id "
            "(back to the preset) and never touched the active id")

        # ---- PA13 a commit follows the scenario-compatibility law -------------
        # re-apply the rotor edit, then commit; the compat block must report a
        # world change whose ScenarioDigest is INVARIANT (only ReplayBundleID
        # moves) -- the frozen identity law, surfaced not violated.
        SB._draft_source_payload(
            {"session_id": "copy1", "replace_id": "pa-rotor-2",
             "source": ROTOR_EDIT})
        com = SB._draft_commit_payload({"session_id": "copy1"})
        compat = com.get("scenario_compat", {})
        pa13 = (com.get("ok")
                and com["commit"]["active_semantic_id"] != DEMO_SEM
                and com["commit"]["previous_active"] == DEMO_SEM
                and compat.get("changed") is True
                and compat.get("digest_invariant") is True
                and compat.get("replay_bundle_moved") is True)
        rep(pa13, None, "PA13) a commit follows the scenario-compat law: world "
            "moved, ScenarioDigest INVARIANT, only ReplayBundleID moved")

        # ---- PA7 the last-session pointer round-trips (restoration) -----------
        # committing/opening set the pointer; resolve_last_session returns it.
        SB._project_open_payload({"project_id": "copy1"})
        sess = SB._session_payload()
        pa7 = sess.get("ok") and sess.get("last_project_id") == "copy1"
        rep(pa7, None, "PA7) the last-session pointer round-trips so startup "
            "restores the last project (last_project_id == copy1)")

        # ---- PA19 every authoring write lands EXTERNAL to the install ---------
        h = SB._health_payload()
        pdir = os.path.abspath(h["project"]["dir"])
        rdir2 = os.path.abspath(h["project"]["recovery_dir"])
        install = os.path.abspath(HERE)
        pa19 = (h["project"]["writable"] is True
                and not pdir.startswith(install)
                and not rdir2.startswith(install))
        rep(pa19, None, "PA19) authoring writes land EXTERNAL to the install "
            "(project + recovery dirs outside %s)" % install)

        # ---- PA17 (server) GET /api/health reports the alpha version ---------
        pa17_srv = (h.get("bench_version") == ALPHA
                    and SB.BENCH_VERSION == ALPHA
                    and h.get("identity_ok") is True
                    and h.get("demo_semantic_id") == DEMO_SEM)
        rep(pa17_srv, None, "PA17a) GET /api/health + BENCH_VERSION report %s "
            "with identity_ok over the frozen demo id" % ALPHA)

    # =====================================================================
    # FRONTEND (static) -- PA5/PA6/PA8/PA14/PA15/PA16 + PA17 doc/header/zip
    # =====================================================================
    if do_smoke:
        # ---- PA5 the tour stores state in localStorage, not the API ----------
        # GUIDE_STEPS + guideRender/guideGoto touch LS.* and body classes only;
        # they must not call api(...) for a run/commit/source.
        guide_block = _slice(js, "const GUIDE_STEPS", "function showFirstRun")
        pa5 = ("forge.tour.step" in js and "forge.tour.seen" in js
               and "LS.set" in guide_block
               and "api(" not in guide_block)
        rep(pa5, None, "PA5) the guided tour persists to localStorage "
            "(forge.tour.*) and calls NO API in its render/navigation block")

        # ---- PA6 dismissing the tour persists only a presentation pref -------
        dismiss_block = _slice(js, "function guideDismiss", "function guideNext")
        pa6 = ("LS.set(TOUR_SEEN" in dismiss_block
               and "api(" not in dismiss_block)
        rep(pa6, None, "PA6) dismissing the tour writes only the "
            "forge.tour.seen presentation preference (no API, no project doc)")

        # ---- PA8 recovery prompt takes precedence over first-run -------------
        boot_block = _slice(js, "async function boot", "checkHealth()")
        pa8 = ("recoveryPending" in boot_block
               and boot_block.index("recoveryPending") <
               boot_block.index("showFirstRun"))
        rep(pa8, None, "PA8) boot() checks recoveryPending BEFORE the first-run "
            "landing (recovery journal precedence)")

        # ---- PA14 switching Author/Evidence calls no API, folds nothing ------
        setview_block = _slice(js, "function setView", "function restoreView")
        pa14 = ("data-view" in setview_block
                and "api(" not in setview_block
                and "aria-pressed" in setview_block)
        rep(pa14, None, "PA14) setView() toggles a body[data-view] presentation "
            "attribute + aria-pressed only -- no API call, no fold")

        # ---- PA15 every onboarding control is a focusable <button> -----------
        for bid in ("btn-guide", "btn-make-copy",
                    "fr-open", "fr-open-last", "fr-explore-alt", "fr-choose",
                    "gr-dismiss", "gr-back", "gr-next", "view-author",
                    "view-evidence"):
            assert ('id="%s"' % bid) in html, bid
        # each is declared as a <button ... id="..."> (keyboard-focusable).
        import re as _re
        onboarding_ids = ["btn-guide", "btn-make-copy",
                          "fr-open", "fr-open-last",
                          "fr-explore-alt", "fr-choose", "gr-dismiss",
                          "gr-back", "gr-next", "view-author", "view-evidence"]
        pa15 = all(_re.search(r"<button[^>]*id=\"%s\"" % bid, html)
                   for bid in onboarding_ids)
        rep(pa15, None, "PA15) all %d onboarding controls are focusable "
            "<button> elements (keyboard-reachable)" % len(onboarding_ids))

        # ---- PA16 the tour highlights labelled panels (ARIA) -----------------
        step_panels = ["panel-canvas", "panel-scenario", "panel-world",
                       "panel-film", "panel-diff"]
        panels_exist = all(('id="%s"' % p) in html for p in step_panels)
        rail_labelled = ('id="guide-rail"' in html
                         and 'aria-label="Guided demo"' in html)
        first_run_dialog = ('id="first-run"' in html
                            and 'role="dialog"' in html
                            and 'aria-modal="true"' in html)
        pa16 = panels_exist and rail_labelled and first_run_dialog
        rep(pa16, None, "PA16) the tour targets existing panels + the rail and "
            "first-run overlay carry ARIA labels/roles")

        # ---- PA17 (browser header + docs + archive) --------------------------
        header_ok = ('<title>Spinner Bench %s</title>' % ALPHA) in html \
            and ('>%s<' % ALPHA) in html
        rn = _read(os.path.join(HERE, "RELEASE_NOTES.md"))
        qs = _read(os.path.join(HERE, "FORGE_QUICKSTART.md"))
        readme = _read(os.path.join(HERE, "README.md"))
        docs_ok = (ALPHA in rn and ALPHA in qs and ALPHA in readme)
        pa17_ui = header_ok and docs_ok
        rep(pa17_ui, None, "PA17b) the browser header + Release Notes + "
            "Quickstart + README all report %s" % ALPHA)

    # ---- PA18 the dist build / ZIP ships the root README.md -------------------
    if do_smoke:
        builder = _load_builder()
        rel = tempfile.mkdtemp(prefix="forge-pa-rel-")
        zip_path = os.path.join(tempfile.mkdtemp(prefix="forge-pa-zip-"),
                                "forge-spinner-bench-%s.zip" % ALPHA)
        rc = builder.build(rel, zip_path=zip_path, force=True)
        readme_shipped = os.path.isfile(os.path.join(rel, "README.md"))
        # the README hash is present in the manifest (it is a shipped file).
        man = _read(os.path.join(rel, "MANIFEST.sha256"))
        import zipfile
        with zipfile.ZipFile(zip_path) as z:
            names = z.namelist()
        pa18 = (rc == 0 and readme_shipped and "README.md" in man
                and "README.md" in names)
        rep(pa18, None, "PA18) the clean build + deterministic ZIP ship the root "
            "README.md (manifest + archive both list it)")
        shutil.rmtree(rel, ignore_errors=True)
        shutil.rmtree(os.path.dirname(zip_path), ignore_errors=True)

    # =====================================================================
    # NATIVE -- PA20 ic_ref == ic32 == Fixture oracle
    # =====================================================================
    if do_native:
        cert = SB._verify_payload(DEMO_SRC, oracle=True)
        pa20_ref = (cert["ok"]
                    and cert.get("oracle", {}).get("match") is True
                    and cert["semantic_artifact_id"] == DEMO_SEM)
        pa20_nat = (cert.get("native") is True and cert.get("parity") is True)
        rep(pa20_ref, pa20_nat, "PA20) ic_ref == ic32 == Fixture oracle "
            "certification stays green over the frozen demo world")

    # cleanup.
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
    print("  [note] v0.7-1 is PRODUCT-FACING UI/UX ONLY: a first-run landing "
          "launcher (PA1), a read-only Explore path that creates no project "
          "(PA2) and writes no recovery journal (PA3), a guided demo tour whose "
          "state is browser-local (PA5/PA6) and never precedes recovery (PA8), "
          "Author/Evidence progressive disclosure that folds nothing (PA14), and "
          "a Make-an-editable-copy flow that creates a real project explicitly "
          "(PA9), shares the preset's immutable id (PA10), and guides a rotor "
          "edit that moves the CANDIDATE not the ACTIVE id (PA11), reversible by "
          "Undo (PA12) and committable under the scenario-compat law (PA13). The "
          "alpha version cut is consistent across the server (PA17a), the "
          "browser header + docs + archive (PA17b/PA18), while every write stays "
          "external to the install (PA19) and the frozen demo still folds "
          "ic_ref == ic32 == Fixture oracle (PA20). NO new semantic profile, IR "
          "version, artifact identity, actor role, or runtime law.")
    return 0 if allok else 1


# -- tiny string helpers (keep the assertions readable, no deps) --------------
def _slice(text, start_marker, end_marker):
    """The substring of `text` from the first `start_marker` to the next
    `end_marker` after it (or end of text). Empty string if start is absent."""
    i = text.find(start_marker)
    if i < 0:
        return ""
    j = text.find(end_marker, i + len(start_marker))
    return text[i:] if j < 0 else text[i:j]


if __name__ == "__main__":
    sys.exit(main())
