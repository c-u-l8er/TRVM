"""binding_run39.py -- v0.7-2 ERROR AND PROGRESS UX battery (PB1-PB20).

GPT-5.6's v0.7-2 ruling: v0.7.0-alpha.2 closed the first-run STATE surface; v0.7-2
closes the ERROR + PROGRESS surface. It introduces NO new semantic profile, IR
version, artifact identity, actor role, or runtime law -- the demo world still
seals to the frozen DEMO_WORLD_SEMANTIC_ID and ic_ref == ic32 == Fixture oracle
stays green (PB18/PB20). It is a PRESENTATION closure:

  * every API failure carries a stable typed ErrorPresentationV1 sidecar
    (`forge.error.v1`), and a raw Python exception NEVER crosses to the browser;
  * source / canvas errors locate a span / object to highlight;
  * runtime/native failures distinguish native-unavailable, build-failure and
    parity-mismatch, and offer a reference-only fallback;
  * a persistent job-progress component shows monotonic queued -> running ->
    completed | failed | cancelled, keeps a settled result inspectable, and
    styles cancellation distinctly from failure;
  * the primary project / recovery flows use in-app accessible dialogs -- no
    browser prompt() / alert() / confirm() remain.

Like binding_run37/38 it splits into a SERVER / IDENTITY layer (in-process, temp
FORGE_PROJECT_ROOT) and a FRONTEND layer (static assertions over
spinner_bench.js / .html / .css).

  PB1  a stable typed code on every API failure
  PB2  no raw Python exception (traceback / repr / internal leak) in the browser
  PB3  a malformed request body becomes a structured 400
  PB4  a source error carries a source_span to highlight
  PB5  a canvas/object error carries an object_id to highlight
  PB6  an invalid draft stays typed+editable while the active world still runs
  PB7  a stale revision offers Reload (not silent overwrite)
  PB8  a project-id collision preserves the entered form (re-prompt, not discard)
  PB9  native-unavailable offers a reference-only fallback
  PB10 native-build-failure reports compiler/cache guidance and is retryable
  PB11 job progress is monotonic (queued -> running -> completed)
  PB12 cancelled is presented distinctly from failed
  PB13 a completed job's result is inspectable
  PB14 a browser disconnect writes no traceback (BrokenPipe/ConnReset guarded)
  PB15 a recovery-stale journal offers Open-as-copy
  PB16 bundle corruption and bundle unresolved are distinct codes
  PB17 the primary flows use in-app accessible dialogs (no prompt/alert/confirm)
  PB18 the error/progress UX moves NO Forge identity (demo still seals frozen id)
  PB19 the alpha artifact is deterministic and ships forge_errors.py
  PB20 ic_ref == ic32 == Fixture oracle stays green                     (native)

Gates:

    python3 binding_run39.py --gate smoke    # PB1-PB19 (fast, no compiler)
    python3 binding_run39.py --gate native   # PB20 (compiler; ic_ref==ic32==oracle)
    python3 binding_run39.py                  # all of the above
"""
import argparse
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
ALPHA = "v0.7.0-alpha.3"

# a world source that double-drives relay r0 -> WRL_CONTROLLER_CONFLICT on r0,
# with a source_span AND an object_id (PB4/PB5).
CONFLICT_SRC = """profile forge.world.core.v1

[pulser:p0](every 2){sig_out}
[relay:r0]{sig_in, sig_out}
[spinner:sp](w=16, n=8, rotor=quarter_turn_z, configurable){sig_in, socket}
[orb:ob]{pose}
[pulser:p1](once at 1){sig_out}

[pulser:p0] --sig--> [relay:r0]
[relay:r0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]
[pulser:p1] --sig--> [relay:r0]
"""


def _read(path):
    return open(path, encoding="utf-8").read() if os.path.isfile(path) else ""


def _slice(text, start_marker, end_marker):
    i = text.find(start_marker)
    if i < 0:
        return ""
    j = text.find(end_marker, i + len(start_marker))
    return text[i:] if j < 0 else text[i:j]


def _pres_ok(pres):
    """A well-formed ErrorPresentationV1: the frozen version + the mandatory keys,
    with domain-shaped values (no traceback marker in the message)."""
    if not isinstance(pres, dict):
        return False
    for k in ("error_presentation_version", "code", "title", "message",
              "severity", "retryable", "action_label", "category"):
        if k not in pres:
            return False
    return (pres["error_presentation_version"] == "forge.error.v1"
            and isinstance(pres["code"], str) and pres["code"]
            and pres["severity"] in ("error", "warning", "info")
            and "Traceback" not in pres["message"])


def main():
    ap = argparse.ArgumentParser(description="Error and progress UX battery.")
    ap.add_argument("--gate", default="all", choices=["all", "smoke", "native"])
    args = ap.parse_args()
    do_smoke = args.gate in ("all", "smoke")
    do_native = args.gate in ("all", "native") and not SKIP_NATIVE

    print("[BINDING wrl-%s] error and progress UX -- PB1-PB20 (gate=%s)"
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

    data_root = tempfile.mkdtemp(prefix="forge-pb-data-")
    project_root = os.path.join(data_root, "projects")
    os.environ["FORGE_PROJECT_ROOT"] = project_root
    import spinner_bench as SB
    import forge_errors as FE
    DEMO_SRC = SB.DEMO_WORLD_SOURCE
    DEMO_SEM = SB.DEMO_WORLD_SEMANTIC_ID

    js = _read(os.path.join(HERE, "spinner_bench.js"))
    css = _read(os.path.join(HERE, "spinner_bench.css"))
    py = _read(os.path.join(HERE, "spinner_bench.py"))
    htmldoc = _read(os.path.join(HERE, "spinner_bench.html"))

    new_block = _slice(js, "async function doNewProject", "async function doForkProject")
    fork_block = _slice(js, "async function doForkProject", "async function doRenameProject")
    import_block = _slice(js, "async function doImportProject", "// ------")
    runjob_block = _slice(js, "async function runJob", "async function doCancel")
    showerr_block = _slice(js, "function showError", "function clearError")
    highlight_block = _slice(js, "function highlightError", "function runErrorAction")
    action_block = _slice(js, "function runErrorAction", "// ===")
    recover_block = _slice(js, "async function promptRecovery", "// ---")

    if do_smoke:
        # ---- PB1 stable typed code on every API failure ----------------------
        p = SB._lower_payload("this is not a valid world {{{")
        pb1 = (p.get("ok") is False and _pres_ok(p.get("error_presentation"))
               and p["error_presentation"]["code"].startswith("WRL_"))
        rep(pb1, None, "PB1) a failing API call returns ok:false + a well-formed "
            "ErrorPresentationV1 with a stable code")

        # ---- PB2 no raw Python exception in the browser ----------------------
        leaked = SB._err(KeyError("secret_internal_detail"))
        pres = leaked.get("error_presentation", {})
        blob = json.dumps(leaked)
        pb2 = (_pres_ok(pres)
               and pres["code"] == FE.FORGE_INTERNAL
               and pres.get("error_id")                 # correlation id present
               and "secret_internal_detail" not in blob  # payload not leaked
               and "KeyError" not in blob
               and "Traceback" not in blob)
        rep(pb2, None, "PB2) an unknown exception is sanitized to FORGE_INTERNAL "
            "with an error_id -- the repr/traceback never reach the browser")

        # ---- PB3 malformed request -> structured 400 -------------------------
        pb3 = ('pres = FE.bad_request(' in py
               and '"error_presentation": pres}, 400)' in py
               and FE.bad_request()["code"] == "WRL_BAD_REQUEST"
               and FE.category_of("WRL_BAD_REQUEST") == FE.CAT_REQUEST)
        rep(pb3, None, "PB3) an unparseable request body returns a structured 400 "
            "carrying the WRL_BAD_REQUEST presentation")

        # ---- PB4 source error carries a span ---------------------------------
        cp = SB._lower_payload(CONFLICT_SRC)
        cpres = cp.get("error_presentation", {})
        sp = cpres.get("source_span")
        pb4 = (cp.get("ok") is False
               and cpres.get("code") == "WRL_CONTROLLER_CONFLICT"
               and isinstance(sp, dict)
               and isinstance(sp.get("start_line"), int)
               and cpres.get("category") == FE.CAT_SOURCE
               and "highlightError" in showerr_block
               and "source_span" in highlight_block
               and "setSelectionRange" in highlight_block)
        rep(pb4, None, "PB4) a source error carries a source_span and the editor "
            "highlights it (setSelectionRange from start_line/column)")

        # ---- PB5 canvas/object error carries an object_id --------------------
        pb5 = (cpres.get("object_id") == "r0"
               and 'data-object-id' in highlight_block
               and 'setAttribute("data-object-id"' in js)  # canvas nodes tagged
        rep(pb5, None, "PB5) an object error carries an object_id and the canvas "
            "node (data-object-id) is highlighted")

        # ---- PB6 invalid draft stays typed+editable; active world still runs --
        bad = SB._lower_payload(CONFLICT_SRC)
        good = SB._run_payload(DEMO_SRC)
        inv = FE._REGISTRY["WRL_INVALID_CANDIDATE"]  # (title,sev,retry,action,cat)
        pb6 = (bad.get("ok") is False
               and _pres_ok(bad.get("error_presentation"))
               and good.get("ok") and good.get("semantic_artifact_id") == DEMO_SEM
               and inv[1] == FE.WARNING and inv[2] is True)   # editable, retryable
        rep(pb6, None, "PB6) an invalid world is a typed (retryable) error while "
            "the active demo world still folds to its frozen id")

        # ---- PB7 stale revision offers Reload, not overwrite -----------------
        stale = FE._REGISTRY["WRL_PROJECT_STALE"]
        pb7 = (stale[2] is True and stale[3] == "Reload latest revision"
               and stale[4] == FE.CAT_PROJECT
               and 'code === "WRL_PROJECT_STALE"' in action_block
               and "openSession(state.session)" in action_block)
        rep(pb7, None, "PB7) a stale revision is retryable with a 'Reload latest "
            "revision' action that re-opens the session (never a silent overwrite)")

        # ---- PB8 project-id collision preserves the entered form -------------
        # server refuses a duplicate id with WRL_PROJECT_EXISTS ...
        SB._project_new_payload({"project_id": "pb8", "name": "pb8"})
        dup = SB._project_new_payload({"project_id": "pb8", "name": "again"})
        server_ok = (dup.get("ok") is False
                     and dup["error_presentation"]["code"] == "WRL_PROJECT_EXISTS")
        # ... and each create/fork/import loop re-opens the form pre-filled.
        def _preserves(block):
            return ("for (;;)" in block
                    and 'code === "WRL_PROJECT_EXISTS"' in block
                    and "continue;" in block
                    and "value:" in block)
        pb8 = (server_ok and _preserves(new_block) and _preserves(fork_block)
               and _preserves(import_block))
        rep(pb8, None, "PB8) a duplicate project id is refused (WRL_PROJECT_EXISTS) "
            "and create/fork/import re-prompt with the entered values preserved")

        # ---- PB9 native-unavailable offers reference-only --------------------
        nu = FE._REGISTRY[FE.NATIVE_UNAVAILABLE]
        pb9 = (nu[3] == "Run reference-only" and nu[4] == FE.CAT_RUNTIME
               and "FE.NATIVE_UNAVAILABLE if not O.native_available()" in py
               and 'code === "NATIVE_UNAVAILABLE"' in action_block
               and "doRun()" in action_block)
        rep(pb9, None, "PB9) native-unavailable presents a 'Run reference-only' "
            "action that re-runs the reference fold")

        # ---- PB10 native-build-failure reports guidance + retryable ----------
        nb = FE._REGISTRY[FE.NATIVE_BUILD_FAILED]
        pb10 = (nb[2] is True and nb[3] == "Retry native build"
                and nb[4] == FE.CAT_RUNTIME
                and "else FE.NATIVE_BUILD_FAILED" in py)
        rep(pb10, None, "PB10) native-build-failure is a distinct, retryable code "
            "with a 'Retry native build' action")

        # ---- PB11 job progress is monotonic ----------------------------------
        jid = SB._JOB_REGISTRY.submit("run", {"src": DEMO_SRC})
        states, dones, result = [], [], None
        deadline = time.time() + 30
        while time.time() < deadline:
            snap = SB._JOB_REGISTRY.get(jid)
            st = snap["state"]
            if not states or states[-1] != st:
                states.append(st)
            dones.append((snap.get("progress") or {}).get("done", 0) or 0)
            if st in ("completed", "failed", "cancelled"):
                result = snap.get("result")
                break
            time.sleep(0.03)
        rank = {"queued": 0, "running": 1, "completed": 2, "failed": 2,
                "cancelled": 2}
        mono_state = all(rank[states[i]] <= rank[states[i + 1]]
                         for i in range(len(states) - 1))
        mono_done = all(dones[i] <= dones[i + 1] for i in range(len(dones) - 1))
        pb11 = (states[-1] == "completed" and mono_state and mono_done
                and "state.job = null" not in runjob_block.split("finally")[0]
                and "renderJobProgress(kind, s)" in runjob_block)
        rep(pb11, None, "PB11) a run job walks a monotonic queued->running->"
            "completed with non-decreasing progress, re-rendered each poll")

        # ---- PB12 cancelled distinct from failed -----------------------------
        jc = FE._REGISTRY[FE.JOB_CANCELLED]
        jf = FE._REGISTRY[FE.JOB_FAILED]
        pb12 = (jc[1] == FE.INFO and jf[1] == FE.ERROR
                and 'cancelled: "cancelled"' in js and 'failed: "failed ✗"' in js
                and '"job-progress " + st' in js)   # per-state CSS class
        # cancelled and failed carry different CSS treatments
        pb12 = (pb12 and ".job-progress.cancelled" in css
                and ".job-progress.failed" in css)
        rep(pb12, None, "PB12) cancelled is a distinct state+code+style from failed "
            "(INFO vs ERROR; separate label + CSS class)")

        # ---- PB13 completed job result inspectable ---------------------------
        pb13 = (result is not None and result.get("ok")
                and result.get("semantic_artifact_id") == DEMO_SEM
                and 'if (s.state === "completed") { state.lastJob = s;' in js
                and "stays visible after the job settles" in js)
        rep(pb13, None, "PB13) a completed job keeps an inspectable result "
            "(state.lastJob) and the panel persists after it settles")

        # ---- PB14 disconnect writes no traceback -----------------------------
        pb14 = ("except (BrokenPipeError, ConnectionResetError):" in py
                and "self.close_connection = True" in py)
        rep(pb14, None, "PB14) a mid-response client disconnect is swallowed "
            "(BrokenPipe/ConnReset) and never tracebacks")

        # ---- PB15 recovery-stale offers Open-as-copy -------------------------
        rs = FE._REGISTRY["WRL_RECOVERY_STALE"]
        pb15 = (rs[3] == "Open as copy" and rs[4] == FE.CAT_PROJECT
                and "promptRecovery(true)" in js
                and '"Open as copy"' in recover_block
                and 'value: "copy"' in recover_block)
        rep(pb15, None, "PB15) a stale recovery journal offers an 'Open as copy' "
            "choice rather than silently applying or discarding it")

        # ---- PB16 bundle corrupt vs unresolved are distinct ------------------
        bc = FE._REGISTRY["WRL_BUNDLE_CORRUPT"]
        bu = FE._REGISTRY["WRL_BUNDLE_UNRESOLVED"]
        pb16 = (bc[0] != bu[0] and bc[1] != bu[1]
                and FE.category_of("WRL_BUNDLE_CORRUPT") == FE.CAT_BUNDLE
                and FE.category_of("WRL_BUNDLE_UNRESOLVED") == FE.CAT_BUNDLE)
        rep(pb16, None, "PB16) bundle corruption (ERROR) and bundle unresolved "
            "(WARNING) are distinct codes with distinct presentations")

        # ---- PB17 primary flows use in-app accessible dialogs ----------------
        no_native = not any(("%s(" % w) in js for w in
                            ("window.prompt", "window.alert", "window.confirm"))
        # raw prompt/alert/confirm calls (not our dialog* helpers) are gone
        import re as _re
        raw = _re.findall(r"(?<![\w.])(prompt|alert|confirm)\s*\(", js)
        accessible = ('setAttribute("role", "dialog")' in js
                      and 'setAttribute("aria-modal", "true")' in js
                      and 'ev.key === "Escape"' in js
                      and 'ev.key === "Tab"' in js)   # focus trap
        flows_wired = all(fn in js for fn in
                          ("doMakeCopy", "doNewProject", "doForkProject",
                           "doRenameProject", "doTrashProject", "doRestoreProject",
                           "doImportProject", "promptRecovery"))
        uses_dialogs = all(h in js for h in ("dialogForm", "dialogConfirm",
                                             "dialogChoice", "dialogAlert"))
        has_root = 'id="dialog-root"' in htmldoc and ".dlg-backdrop" in css
        pb17 = (no_native and not raw and accessible and flows_wired
                and uses_dialogs and has_root)
        rep(pb17, None, "PB17) no prompt/alert/confirm remain; the primary flows "
            "use an accessible role=dialog (aria-modal, Escape, focus trap)")

        # ---- PB18 the UX moves no Forge identity -----------------------------
        low = SB._lower_payload(DEMO_SRC)
        hp = SB._health_payload()
        pb18 = (low.get("semantic_artifact_id") == DEMO_SEM
                and hp.get("identity_ok") is True
                and hp.get("demo_semantic_id") == DEMO_SEM)
        rep(pb18, None, "PB18) the error/progress surface recomputes NO identity: "
            "the demo still seals the frozen id and the self-check is green")

        # ---- PB19 alpha artifact deterministic + ships forge_errors ----------
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "bfr", os.path.join(HERE, "tools", "build_forge_release.py"))
        bfr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bfr)
        out_a = os.path.join(data_root, "rel-a")
        out_b = os.path.join(data_root, "rel-b")
        zip_a = os.path.join(data_root, "a.zip")
        zip_b = os.path.join(data_root, "b.zip")
        rc_a = bfr.build(out_a, zip_path=zip_a, force=True)
        rc_b = bfr.build(out_b, zip_path=zip_b, force=True)
        ships_err = "forge_errors.py" in bfr.FORGE_MODULES
        byte_equal = (os.path.isfile(zip_a) and os.path.isfile(zip_b)
                      and open(zip_a, "rb").read() == open(zip_b, "rb").read())
        man_a = _read(os.path.join(out_a, "MANIFEST.sha256"))
        pb19 = (rc_a == 0 and rc_b == 0 and ships_err and byte_equal
                and "forge/forge_errors.py" in man_a)
        rep(pb19, None, "PB19) the release builds twice to a byte-identical zip and "
            "ships forge_errors.py (deterministic + read-only)")

    # ---- PB20 ic_ref == ic32 == Fixture oracle ------------------------------
    if do_native:
        cert = SB._verify_payload(DEMO_SRC, oracle=True)
        pb20_ref = (cert["ok"]
                    and cert.get("oracle", {}).get("match") is True
                    and cert["semantic_artifact_id"] == DEMO_SEM)
        pb20_nat = (cert.get("native") is True and cert.get("parity") is True)
        rep(pb20_ref, pb20_nat, "PB20) ic_ref == ic32 == Fixture oracle stays "
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
    print("  [note] v0.7-2 is the Error and Progress UX closure: every API failure "
          "returns a stable, browser-safe ErrorPresentationV1 (PB1) that never "
          "leaks a Python exception (PB2); malformed requests become a structured "
          "400 (PB3); source and object errors locate a span (PB4) / object (PB5) "
          "to highlight; an invalid world stays typed+editable while the active "
          "world runs (PB6); stale revisions Reload (PB7); id collisions re-prompt "
          "with the form intact (PB8); native failures distinguish unavailable "
          "(reference-only, PB9) from build-failure (retryable, PB10); job "
          "progress is monotonic (PB11) with cancelled distinct from failed (PB12) "
          "and results inspectable (PB13); a disconnect never tracebacks (PB14); "
          "recovery-stale offers Open-as-copy (PB15); bundle corrupt vs unresolved "
          "are distinct (PB16); the primary flows use accessible in-app dialogs "
          "(PB17). It moves NO Forge identity (PB18), builds a deterministic "
          "read-only artifact (PB19) and stays ic_ref==ic32==oracle green (PB20).")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
