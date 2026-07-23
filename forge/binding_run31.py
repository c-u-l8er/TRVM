"""binding_run31.py -- v0.6-1 runtime-job lifecycle (Y1-Y12).

v0.6-0 (binding_run30) added the crash-recovery journal. v0.6-1 turns the long
ic-reducer folds (/api/run + /api/verify) into CANCELLABLE background jobs with an
observable state machine (queued -> running -> completed|failed|cancelled) and
progress -- and decouples the compute from the request socket so a client
disconnect neither aborts the fold nor trips a BrokenPipeError. The job registry
(`wrl_jobs.JobRegistry`) is pure orchestration over an injected executor, so the
lifecycle is driven DETERMINISTICALLY here without the HTTP server; the real
spinner_bench executor anchors result-parity + the native fold.

Battery Y1-Y12 (the v0.6-1 acceptance gate):

  Y1  a submitted job runs to `completed` and returns the executor's result
      (queued -> running -> completed);
  Y2  progress is reported monotonically and reaches (total, total);
  Y3  a job cancelled while QUEUED never runs (the executor is not invoked) and
      ends `cancelled`;
  Y4  a job cancelled while RUNNING stops at the next epoch boundary -> `cancelled`
      (partial, NO result);
  Y5  an executor exception -> `failed` with a typed message (no crash; the
      registry keeps working);
  Y6  unknown id -> WRL_JOB_MISSING; a bad kind / malformed request -> WRL_BAD_JOB;
  Y7  the registry is a BOUNDED ring: past the cap the OLDEST TERMINAL jobs are
      evicted, but a queued/running job is NEVER evicted;
  Y8  cancellation propagates PAST _run_payload's broad `except` as JobCancelled
      (the real fold maps a cancel to `cancelled`, never a `failed` result dict);
  Y9  a REAL run job over the demo world == the synchronous _run_payload byte for
      byte (same SemanticArtifactID + per-epoch films);
  Y10 a job snapshot is the exact typed contract (RUNTIME_JOB_FIELDS, versioned);
  Y11 the synchronous _run_payload/_verify_payload are UNCHANGED with no hooks
      (the added progress/cancel params default to a no-op);
  Y12 NATIVE -- a real verify job (oracle=true) folds ic_ref == ic32 == the
      independent Fixture oracle and equals the synchronous _verify_payload.

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import wrl_canonical as WC
import wrl_jobs as WJ
import spinner_bench as SB

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

DEMO = SB.DEMO_WORLD_SOURCE


def _raises(fn, code):
    try:
        fn()
    except WC.WrlUnsupported as ex:
        return getattr(ex, "code", None) == code
    except Exception:
        return False
    return False


def _synth(n, record=None, self_cancel=None, reg_ref=None, fail=None):
    """A synthetic executor: `n` epochs, cooperative cancel between them. `record`
    collects (done,total) tuples; `self_cancel` (an epoch index) cancels its own
    job mid-run via `reg_ref`; `fail` raises after 0 epochs."""
    seen = {"ran": False}

    def ex(kind, request, progress, should_cancel):
        seen["ran"] = True
        if fail is not None:
            raise fail
        for e in range(n):
            if should_cancel():
                raise WJ.JobCancelled()
            progress(e + 1, n, "p")
            if record is not None:
                record.append((e + 1, n))
            if self_cancel is not None and e == self_cancel:
                reg_ref[0].cancel(request["jid"])
        return {"ok": True, "kind": kind, "n": n}

    ex.seen = seen
    return ex


def _await(reg, job_id, timeout=180.0):
    """Poll a worker-backed registry until the job is terminal."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = reg.get(job_id)
        if s["state"] in WJ.TERMINAL_STATES:
            return s
        time.sleep(0.05)
    return reg.get(job_id)


def main():
    print("[BINDING wrl-v0.6-1] runtime-job lifecycle (Y1-Y12)")
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

    # ---- Y1 lifecycle queued -> running -> completed --------------------------
    ex1 = _synth(4)
    r1 = WJ.JobRegistry(ex1, worker=False)
    j1 = r1.submit("run", {"src": "S"})
    q_ok = r1.get(j1)["state"] == WJ.JOB_QUEUED
    r1.run_pending()
    s1 = r1.get(j1)
    rep(q_ok and s1["state"] == WJ.JOB_COMPLETED
        and s1["result"] == {"ok": True, "kind": "run", "n": 4}
        and s1["progress"] == {"done": 4, "total": 4, "phase": "p"},
        None, "Y1) a submitted job runs queued -> completed and returns the "
        "executor result")

    # ---- Y2 progress monotone, reaches (total,total) --------------------------
    rec = []
    r2 = WJ.JobRegistry(_synth(5, record=rec), worker=False)
    r2.run_pending() if r2.submit("run", {}) and r2.run_pending() else None
    mono = all(rec[i][0] <= rec[i + 1][0] for i in range(len(rec) - 1))
    rep(rec == [(1, 5), (2, 5), (3, 5), (4, 5), (5, 5)] and mono, None,
        "Y2) progress is reported monotonically and reaches (total, total)")

    # ---- Y3 cancel while QUEUED -> never runs ---------------------------------
    ex3 = _synth(4)
    r3 = WJ.JobRegistry(ex3, worker=False)
    j3 = r3.submit("run", {})
    c3 = r3.cancel(j3)
    ran_after = r3.run_pending()               # drains the queue (skips it)
    s3 = r3.get(j3)
    rep(c3["state"] == WJ.JOB_CANCELLED and ex3.seen["ran"] is False
        and s3["state"] == WJ.JOB_CANCELLED and s3["result"] is None,
        None, "Y3) a job cancelled while QUEUED never runs (executor not "
        "invoked) and ends cancelled")

    # ---- Y4 cancel while RUNNING -> stops at epoch boundary -------------------
    reg_ref = [None]
    ex4 = _synth(10, self_cancel=1, reg_ref=reg_ref)
    r4 = WJ.JobRegistry(ex4, worker=False)
    reg_ref[0] = r4
    j4 = r4.submit("run", {})
    r4._jobs[j4].request["jid"] = j4
    r4.run_pending()
    s4 = r4.get(j4)
    rep(s4["state"] == WJ.JOB_CANCELLED and s4["result"] is None
        and s4["progress"]["done"] == 2 and s4["progress"]["total"] == 10,
        None, "Y4) a job cancelled while RUNNING stops at the next epoch "
        "boundary -> cancelled (partial, no result)")

    # ---- Y5 executor exception -> failed (typed, non-fatal) -------------------
    r5 = WJ.JobRegistry(_synth(3, fail=ValueError("boom")), worker=False)
    j5 = r5.submit("verify", {})
    r5.run_pending()
    s5 = r5.get(j5)
    # registry keeps working afterwards
    r5._execute = _synth(2)
    j5b = r5.submit("run", {})
    r5.run_pending()
    rep(s5["state"] == WJ.JOB_FAILED and "boom" in (s5["error"] or "")
        and s5["result"] is None
        and r5.get(j5b)["state"] == WJ.JOB_COMPLETED,
        None, "Y5) an executor exception -> failed with a typed message; the "
        "registry keeps working")

    # ---- Y6 typed misses ------------------------------------------------------
    r6 = WJ.JobRegistry(_synth(1), worker=False)
    y6 = (_raises(lambda: r6.get("nope"), WJ.WRL_JOB_MISSING)
          and _raises(lambda: r6.cancel("nope"), WJ.WRL_JOB_MISSING)
          and _raises(lambda: r6.submit("bogus", {}), WJ.WRL_BAD_JOB)
          and _raises(lambda: r6.submit("run", "notadict"), WJ.WRL_BAD_JOB))
    rep(y6, None, "Y6) unknown id -> WRL_JOB_MISSING; bad kind / malformed "
        "request -> WRL_BAD_JOB")

    # ---- Y7 bounded ring evicts oldest TERMINAL, never queued/running ---------
    r7 = WJ.JobRegistry(_synth(1), worker=False, max_jobs=2)
    ids = []
    for _ in range(4):
        ids.append(r7.submit("run", {}))
        r7.run_pending()
    cap_ok = (len(r7.list()) == 2
              and all(s["state"] == WJ.JOB_COMPLETED for s in r7.list()))
    # a QUEUED job is never evicted -- even when that means EXCEEDING the cap:
    # submit 3 jobs past the cap but never run them, so all stay queued. The
    # eviction pass refuses to drop a non-terminal job, so the ring holds all 3.
    r7b = WJ.JobRegistry(_synth(1), worker=False, max_jobs=2)
    qids = [r7b.submit("run", {}) for _ in range(3)]   # left UNRUN (all queued)
    snap = r7b.list()
    keep_ok = (len(snap) == 3
               and all(s["state"] == WJ.JOB_QUEUED for s in snap)
               and set(s["job_id"] for s in snap) == set(qids))
    rep(cap_ok and keep_ok, None,
        "Y7) bounded ring evicts the oldest TERMINAL jobs past the cap but "
        "never a queued/running job")

    # ---- Y8 cancellation re-raises PAST _run_payload's broad except ----------
    def _cancel_now():
        return True

    counter = {"e": 0}

    def _cancel_at2():
        counter["e"] += 1
        return counter["e"] > 2

    y8a = False
    try:
        SB._run_payload(DEMO, cancel=_cancel_now)
    except WJ.JobCancelled:
        y8a = True
    y8b = False
    try:
        SB._run_payload(DEMO, cancel=_cancel_at2)
    except WJ.JobCancelled:
        y8b = True
    rep(y8a and y8b, None,
        "Y8) cancellation propagates PAST _run_payload's broad except as "
        "JobCancelled (a cancel is `cancelled`, never a failed result)")

    # ---- Y9 real run job == synchronous _run_payload --------------------------
    demo_sem = SB.DEMO_WORLD_SEMANTIC_ID
    lock = threading.Lock()
    rr = WJ.JobRegistry(SB._job_execute, lock=lock, max_jobs=16)
    jr = rr.submit("run", {"src": DEMO})
    sr = _await(rr, jr)
    sync_run = SB._run_payload(DEMO)
    y9 = (sr["state"] == WJ.JOB_COMPLETED and sr["result"]["ok"]
          and sr["result"]["semantic_artifact_id"] == demo_sem
          and sr["result"]["semantic_artifact_id"]
          == sync_run["semantic_artifact_id"]
          and [e["film"] for e in sr["result"]["epochs"]]
          == [e["film"] for e in sync_run["epochs"]])
    rep(y9, None, "Y9) a real run job == synchronous _run_payload (same "
        "SemanticArtifactID + per-epoch films)")

    # ---- Y10 snapshot is the exact typed contract ----------------------------
    snap = sr
    y10 = (tuple(snap.keys()) == WJ.RUNTIME_JOB_FIELDS
           and snap["runtime_job_version"] == WJ.RUNTIME_JOB_VERSION
           and snap["kind"] == "run"
           and snap["state"] in WJ.JOB_STATES
           and set(snap["progress"].keys()) == {"done", "total", "phase"})
    rep(y10, None, "Y10) a job snapshot is the exact typed contract "
        "(RUNTIME_JOB_FIELDS, versioned)")

    # ---- Y11 synchronous fold UNCHANGED with no hooks ------------------------
    base_run = SB._run_payload(DEMO)
    y11 = (base_run["ok"] and base_run["semantic_artifact_id"] == demo_sem
           and len(base_run["epochs"]) == 7
           and [e["film"] for e in base_run["epochs"]]
           == [e["film"] for e in sync_run["epochs"]])
    rep(y11, None, "Y11) the synchronous _run_payload is unchanged with no "
        "hooks (default no-op progress/cancel)")

    # ---- Y12 NATIVE verify job folds ic_ref == ic32 == Fixture oracle --------
    jv = rr.submit("verify", {"src": DEMO, "oracle": True})
    sv = _await(rr, jv)
    sync_ver = SB._verify_payload(DEMO, oracle=True)
    res = sv["result"]
    y12_ref = (sv["state"] == WJ.JOB_COMPLETED and res["ok"]
               and res["oracle"] and res["oracle"].get("match") is True
               and res["semantic_artifact_id"] == demo_sem
               and res.get("native") == sync_ver.get("native")
               and res.get("skipped") == sync_ver.get("skipped"))
    y12_nat = None
    if not SKIP_NATIVE:
        y12_nat = (res.get("native") is True and res.get("parity") is True
                   and [e["film_native"] for e in res["epochs"]]
                   == [e["film_native"] for e in sync_ver["epochs"]]
                   and all(e["match"] for e in res["epochs"]))
    rep(y12_ref, y12_nat,
        "Y12) NATIVE -- a real verify job (oracle=true) folds ic_ref == ic32 "
        "== the independent Fixture oracle, == synchronous _verify_payload")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.6-1] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.6-1 makes the long ic-reducer folds CANCELLABLE background "
          "jobs (queued -> running -> completed|failed|cancelled) with progress, "
          "over a bounded in-memory ring. The registry is pure orchestration "
          "(injected executor), so the full lifecycle -- run (Y1), progress "
          "(Y2), cancel-queued (Y3), cancel-running (Y4), failure (Y5), typed "
          "misses (Y6), bounded eviction (Y7) -- is deterministic without the "
          "HTTP server. Cancellation re-raises past _run_payload's broad except "
          "(Y8) so a cancel is `cancelled`, never `failed`. A real job matches "
          "the synchronous fold byte for byte (Y9), the snapshot is the typed "
          "contract (Y10), the synchronous endpoints are unchanged with no hooks "
          "(Y11), and a native verify job still folds ic_ref == ic32 == the "
          "Fixture oracle (Y12). NO new identity and NO new runtime construct; "
          "the synchronous /api/run + /api/verify endpoints and the frozen "
          "lowering/fold are unchanged -- jobs are an additive async lane, and a "
          "client disconnect can no longer trip a BrokenPipeError.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
