#!/usr/bin/env python3
"""resident_spans.py -- what one `trvm.reduce` epoch costs through the compiled kind, one-shot against resident.

    PYTHONDONTWRITEBYTECODE=1 python3 -B resident_spans.py [--jobs N] [--out results-resident-compiled.json]

The row that matters is the FLOOR: `wek/b2/trvm/COMPILED_EXECUTOR_PROPOSAL.md` §6 predicted that as a process per
job the compiled kind buys nothing, because Python starting is ~50 ms against a step of 10-60 us, and B5 measured
exactly that -- **82 ms p50, flat on both chain30 and golden-demo**. This measures the same jobs through a host that
keeps the built `.so`, the sealed plan and the printer.

A DEVELOPMENT READING on a shared laptop, not a benchmark: `BENCHMARK_LANE.md` §1's B2/B3 split applies to this file
exactly as it applies to the battery's timing columns. Every row asserts the payload digest, so what is compared is
the same computation.
"""
import argparse
import base64
import json
import os
import socket
import statistics as st
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (HERE, os.path.join(HERE, "..", "forge"), os.path.join(HERE, "..", "runtime", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.dont_write_bytecode = True

import make_bundle as MB                                            # noqa: E402
from resident import ResidentCompiledHost, send_frame, recv_frame   # noqa: E402

WORLDS = ["chain30", "golden-demo", "chain120", "spinner-w33-n16"]


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))]


def summarise(name, lat, wall_ms, extra=None):
    """`jobs_per_s` is WALL-CLOCK throughput and nothing else.

    It was `len(lat) / sum(lat)` -- the inverse of the mean latency -- which is right only when jobs do not overlap.
    On the C=8 rows it counted eight threads' overlapping waits as eight times the elapsed time and reported a
    throughput below the C=1 row's while actually being faster. Latency is per job (queue wait included, because a
    caller waits for it); throughput is jobs divided by the time the batch actually took.
    """
    return dict({"row": name, "jobs": len(lat), "p50_ms": round(st.median(lat), 3), "p99_ms": round(pct(lat, 0.99), 3),
                 "min_ms": round(min(lat), 3), "mean_ms": round(st.mean(lat), 3), "wall_ms": round(wall_ms, 1),
                 "jobs_per_s": round(len(lat) / (wall_ms / 1000.0), 1)}, **(extra or {}))


def one_shot(bundle_path, jobs):
    """The floor: a fresh `python3 executor.py c BUNDLE` per job -- what a guardian runs today."""
    lat = []
    w0 = time.perf_counter()
    for _ in range(jobs):
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "executor.py"), "c", bundle_path],
                           capture_output=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        lat.append((time.perf_counter() - t0) * 1e3)
        out = json.loads(r.stdout.decode())
        assert out["status"] == "candidate", out
    return lat, out["nf_sha256"], (time.perf_counter() - w0) * 1e3


def in_process(bundle, jobs, conc, phases=None):
    h = ResidentCompiledHost(pool=max(conc, 1), max_queue=jobs + 8)
    try:
        h.ready()
        h.submit(bundle, job_id="warm")                             # the cold job is measured separately
        lat, digs = [], set()
        lock = threading.Lock()
        w0 = time.perf_counter()

        def one(i):
            t0 = time.perf_counter()
            r = h.submit(bundle, job_id=i)
            dt = (time.perf_counter() - t0) * 1e3
            with lock:
                lat.append(dt)
                digs.add(r.get("nf_sha256"))
                if phases is not None and r.get("timing"):
                    phases.append(r["timing"])

        if conc == 1:
            for i in range(jobs):
                one(i)
        else:
            ts = [threading.Thread(target=one, args=(i,)) for i in range(jobs)]
            for t in ts:
                t.start()
            for t in ts:
                t.join()
        wall = (time.perf_counter() - w0) * 1e3
        assert len(digs) == 1, digs
        return lat, digs.pop(), wall
    finally:
        h.close()


def over_socket(bundle, jobs, conc, sock_path):
    """A client in another process: what a guardian speaking the frame protocol would see."""
    def worker(n, out, lock):
        s = socket.socket(socket.AF_UNIX)
        s.connect(sock_path)
        b64 = base64.b64encode(bundle).decode()
        mine = []
        for i in range(n):
            t0 = time.perf_counter()
            send_frame(s, {"id": i, "bundle_b64": b64})
            r = recv_frame(s)
            mine.append((time.perf_counter() - t0) * 1e3)
            assert r["status"] == "candidate", r
        s.close()
        with lock:
            out.append((mine, r["nf_sha256"]))

    out, lock = [], threading.Lock()
    per = max(1, jobs // conc)
    ts = [threading.Thread(target=worker, args=(per, out, lock)) for _ in range(conc)]
    t0 = time.perf_counter()
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    wall = (time.perf_counter() - t0) * 1e3
    lat = [x for m, _ in out for x in m]
    return lat, out[0][1], wall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=40)
    ap.add_argument("--out", default=os.path.join(HERE, "results-resident-compiled.json"))
    a = ap.parse_args()
    rec = {"measured": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "loadavg": os.getloadavg(), "jobs": a.jobs,
           "note": "a development reading on a shared laptop, not a benchmark (BENCHMARK_LANE.md section 1, B2 vs B3)",
           "worlds": []}
    tmp = tempfile.mkdtemp(prefix="resident-spans-")
    for w in WORLDS:
        bundle, meta = MB.build(w, 1, "c")
        bp = os.path.join(tmp, w + ".json")
        with open(bp, "wb") as f:
            f.write(bundle)
        rows, phases = [], []
        lat, dig, wall = one_shot(bp, max(6, a.jobs // 5))
        assert dig == meta["nf_sha256"]
        rows.append(summarise("one-shot: a Python process per job (the guardian's shape today)", lat, wall))
        for c in (1, 8):
            lat, dig, wall = in_process(bundle, a.jobs, c, phases if c == 1 else None)
            assert dig == meta["nf_sha256"]
            rows.append(summarise("resident, in-process, C=%d" % c, lat, wall))
        proc = subprocess.Popen([sys.executable, "-B", os.path.join(HERE, "residentd.py"),
                                 "--socket", os.path.join(tmp, "d.sock"), "--pool", "8", "--max-queue", "64"],
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        try:
            json.loads(proc.stdout.readline().decode())
            for c in (1, 8):
                lat, dig, wall = over_socket(bundle, a.jobs, c, os.path.join(tmp, "d.sock"))
                assert dig == meta["nf_sha256"]
                rows.append(summarise("resident over a Unix socket, C=%d" % c, lat, wall))
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()
            try:
                os.unlink(os.path.join(tmp, "d.sock"))
            except FileNotFoundError:
                pass
        ph = {k: round(st.median([p[k] for p in phases if k in p]), 1)
              for k in ("prepare_us", "object_check_us", "decode_us", "step_us", "render_us", "total_us")} if phases else {}
        rec["worlds"].append({"world": w, "nf_sha256": meta["nf_sha256"], "nf_bytes": meta.get("nf_bytes"),
                              "warm_phases_us_p50": ph, "rows": rows})
        print("\n%s  (nf %s)" % (w, meta["nf_sha256"][:12]))
        for r in rows:
            print("  %-58s p50 %8.2f ms  p99 %8.2f  jobs/s %8.1f (wall %.0f ms)" % (r["row"], r["p50_ms"], r["p99_ms"], r["jobs_per_s"], r["wall_ms"]))
        if ph:
            print("  warm phases (us, p50): " + "  ".join("%s %.1f" % (k.replace("_us", ""), v) for k, v in ph.items()))
    with open(a.out, "w") as f:
        json.dump(rec, f, indent=1)
    print("\nwrote", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
