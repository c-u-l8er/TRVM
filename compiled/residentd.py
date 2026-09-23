#!/usr/bin/env python3
"""residentd.py -- the resident compiled executor behind a socket, so a client that is not Python pays no Python
startup per job (and no Forge import, which is most of the 82 ms the one-shot kind costs).

    python3 -B residentd.py (--socket PATH | --port N [--bind ADDR]) [--pool P] [--max-queue Q] [--emitter c|c2]
                            [--deadline-s S]

Wire, both directions: 4-byte big-endian length + UTF-8 JSON -- the framing `runtime/wasm/resident/residentd.mjs`
uses, so a client written for one is a short edit from the other.

    {"id": n, "bundle_b64": "..."}   -> {"id": n, ...result, "serverMs": x}
    {"id": n, "cancel": true}        -> aborts job n of THIS connection (its reply is `cancelled`)
    {"op": "stats"}                  -> {"op": "stats", ...host.stats()}

`bundle_b64` is `executor.bundle_bytes(...)` base64'd -- the same one file the guardian's fixed-argv form takes, and
base64 for the same reason: `plan_sha256` and the other two are taken over exact bytes, and a transport that can
normalise a newline is a transport that can move a hash.

Closing a connection aborts every in-flight job it submitted; a job already RUNNING is aborted the only way a native
step can be (SIGKILL of its worker, `waitpid` for the witness), so a client that disconnects mid-step costs the pool
a worker. That is the compiled kind's cancellation story and `resident.py`'s docstring is where it is argued.

It listens only after every worker has announced itself: a pool that cannot start says so and exits 3, rather than
accepting a connection it cannot serve. The port it prints is the port the kernel BOUND, so `--port 0` is usable --
the Wasm daemon had a bug here once (it echoed the requested port, announcing ":0"), and this does not repeat it.
"""
import argparse
import base64
import json
import os
import signal
import socket
import socketserver
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True

from resident import ResidentCompiledHost, send_frame, recv_frame, MAX_FRAME   # noqa: E402

HOST = None
DEADLINE = 10.0


class _Handler(socketserver.BaseRequestHandler):
    def handle(self):
        sock = self.request
        inflight = {}                     # id -> threading.Event (the cancel flag for that job)
        lock = threading.Lock()
        threads = []

        def reply(obj):
            with lock:
                try:
                    send_frame(sock, obj)
                except OSError:
                    pass

        def run_job(req):
            jid = req.get("id")
            ev = threading.Event()
            with lock:
                if jid in inflight:
                    send_frame(sock, {"id": jid, "status": "refused", "reason": "duplicate-id"})
                    return
                inflight[jid] = ev
            t0 = time.perf_counter()
            try:
                raw = base64.b64decode(req["bundle_b64"], validate=True)
                res = HOST.submit(raw, deadline_s=DEADLINE, job_id=jid, cancel=ev)
            except Exception as e:
                res = {"status": "refused", "reason": "request-shape", "id": jid,
                       "detail": {"error": "%s: %s" % (type(e).__name__, str(e)[:200])}}
            finally:
                with lock:
                    inflight.pop(jid, None)
            res["serverMs"] = round((time.perf_counter() - t0) * 1e3, 3)
            reply(res)

        while True:
            try:
                req = recv_frame(sock)
            except ValueError:            # an oversized frame closes the connection, as the Wasm daemon does
                break
            except OSError:
                break
            if req is None:
                break
            if not isinstance(req, dict):
                reply({"id": None, "status": "refused", "reason": "request-shape"})
                continue
            if req.get("op") == "stats":
                reply({"op": "stats", **HOST.stats()})
                continue
            if req.get("cancel") is True:
                with lock:
                    ev = inflight.get(req.get("id"))
                if ev is not None:
                    ev.set()
                continue
            if not isinstance(req.get("bundle_b64"), str) or "id" not in req:
                reply({"id": req.get("id"), "status": "refused", "reason": "request-shape"})
                continue
            t = threading.Thread(target=run_job, args=(req,), daemon=True)
            threads.append(t)
            t.start()

        with lock:                        # the connection closed: every job it submitted is cancelled
            for ev in inflight.values():
                ev.set()
        for t in threads:
            t.join(timeout=30)


class _Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class _UnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


def main(argv=None):
    global HOST, DEADLINE
    ap = argparse.ArgumentParser()
    ap.add_argument("--socket")
    ap.add_argument("--port", type=int)
    ap.add_argument("--bind", default="127.0.0.1")
    ap.add_argument("--pool", type=int, default=4)
    ap.add_argument("--max-queue", type=int, default=16)
    ap.add_argument("--emitter", default="c", choices=["c", "c2"])
    ap.add_argument("--deadline-s", type=float, default=10.0)
    a = ap.parse_args(argv)
    if not a.socket and a.port is None:
        ap.error("one of --socket or --port")
    DEADLINE = a.deadline_s
    HOST = ResidentCompiledHost(pool=a.pool, max_queue=a.max_queue, emitter=a.emitter)
    try:
        HOST.ready()                      # no connection is accepted before every worker has announced itself
    except Exception as e:
        print(json.dumps({"residentd": "refused", "reason": "startup", "error": str(e)[:300]}), flush=True)
        HOST.close()
        return 3
    if a.socket:
        try:
            os.unlink(a.socket)
        except FileNotFoundError:
            pass
        srv = _UnixServer(a.socket, _Handler)
        where = a.socket
    else:
        srv = _Server((a.bind, a.port), _Handler)
        where = "%s:%d" % srv.server_address[:2]          # the port the kernel BOUND, not the one requested
    print(json.dumps({"residentd": where, "pid": os.getpid(), "pool": a.pool, "max_queue": a.max_queue,
                      "emitter": a.emitter, "kind": HOST.stats()["kind"], "ready": HOST.stats()["idle"]}), flush=True)

    # OWNERSHIP ENDS WITH THE OWNER. A SIGTERM used to end this process at once, `finally` never ran, and every
    # worker was left to its own devices: an idle one exits on EOF, a HELD one (SIGSTOP, as the lifecycle cases
    # hold them) does not, and a worker that had already died stayed a zombie of a parent that no longer waited.
    # Measured 2026-09-23 by a consumer's teardown that asserts confirmed absence: it found exactly such a zombie.
    # TERM now takes the same road as ^C: the loop ends, `HOST.close()` SIGKILLs and `waitpid`s every worker.
    def _term(signum, _frame):
        raise KeyboardInterrupt("SIGTERM")

    signal.signal(signal.SIGTERM, _term)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
        HOST.close()
        if a.socket:
            try:
                os.unlink(a.socket)
            except FileNotFoundError:
                pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
