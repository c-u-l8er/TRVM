#!/usr/bin/env python3
"""resident.py -- the compiled `trvm.reduce` executor kept RESIDENT: the built `.so`, the sealed plan and the printer
held across jobs, in a pool of worker processes the parent can kill.

    from resident import ResidentCompiledHost
    h = ResidentCompiledHost(pool=4, max_queue=16, emitter="c")
    h.ready(); h.submit(bundle_bytes, deadline_s=10.0); h.close()

WHY THIS EXISTS, measured rather than assumed. `wek/b2/trvm/COMPILED_EXECUTOR_PROPOSAL.md` §6: "As a process per job,
the compiled kind buys nothing: Python starting is ~50 ms ... so a 10 us step behind a 50 ms process is the executor
span the witness already has." B5 measured that one-shot executor at **82 ms p50, flat on both chain30 and the Golden
demo** -- flat because the step is 10-60 us and everything else is Python starting and Forge importing. This holds the
expensive things still and answers job frames, which is the shape `runtime/wasm/resident/residentd.mjs` gives the
checked Wasm host.

IT IS NOT WIRED INTO SUPER AND THIS FILE DOES NOT ASK IT TO BE. §6's ruling -- whether a retired job id is an
acceptable barrier for `local_mutate` on a resident host -- is Codex's and is still open; the Wasm resident host was
built, measured and tested in this lane under exactly that condition and says so in its own README §6. This is the
same position. What HyperSurface would have to admit is stated in `RESIDENT.md` §6 and nothing in `super/` changes.

THE FOUR BOUNDARIES the development plan requires of any reuse, stated rather than assumed:

* **Ownership.** The process that constructs the host owns its workers and is the only thing that can write to them.
  `close()` kills every worker and refuses afterwards. Workers are SPAWNED (`subprocess`), not forked from a threaded
  parent: a fork from a thread inherits whatever locks were held at the instant of the fork, and the parent here is
  threaded by construction. A worker is a separate address space, which is also what lets its `.so` cache be owned by
  its own Carrier rather than shared (§6's harder-here requirement number one).

* **Invalidation, and it is STRONGER here than on the Wasm host rather than weaker.** The Wasm host must build a fresh
  instance per job because its guest owns 256 MiB of linear memory that could carry state, and it witnesses freshness
  by reading the guest's own counters. **The compiled step has no guest state to carry.** `step_v6(const i64 *st,
  const i64 *ctl, i64 *out)` is a pure function over three caller-owned buffers, and the emitted translation unit
  declares no mutable object at all -- so there is no instance, nothing to reset, and nothing to witness as reset.
  That is not an assertion here: `no_writable_state()` reads the object's own symbol table and refuses any mutable
  object that is not named C-runtime scaffolding, and the harness runs it over every world under both C emitters.
  It is checked by SYMBOL because the object does carry 16 writable bytes -- `__dso_handle` and the run-once
  destructor guard `completed.0`, which gcc emits for every shared object -- and a section-level check that was
  widened to tolerate those would also tolerate a `static int` the emitter might one day grow. The `.so` itself is
  content-addressed by the sha256 of its source, so a repinned emitter is a different object and a different
  `backend_id` -- there is no reload path, on purpose -- and `executor.check_object` re-checks the file against the
  identity recorded beside it **per job, on the warm path too**.

* **Cancellation, and this is the one that is genuinely harder here (§6's number two).** A native step cannot be
  interrupted: there is no `Worker.terminate()`, no check-for-abort inside a `while` loop in someone else's compiled
  code. **SIGKILL followed by `waitpid` is the only witness**, and it costs the worker. So a deadline or a cancel on a
  RUNNING job kills that worker, reaps it (the confirmed-absence witness, `killed_confirmed`), and replaces it; a
  queued job leaves the queue without touching a worker. A runaway step therefore loses the pool one worker, exactly
  as §6 said it would.

* **Resource boundaries.** `pool` worker processes; `max_queue` jobs may wait; beyond that `refused: busy`. With no
  worker left, `refused: exhausted`. No CPU, RSS or memory limit is claimed -- the same position the one-shot
  executor and the Wasm host take.

THE CONTRACT WORD, stated as plainly as the Wasm host states it. On the warm path the worker does not exit, so a
result says **`workerExited: false, jobRetired: true`**: the reply was written by the worker after `run` returned, the
job id is retired, and a later frame under that id changes nothing. Where a worker really was killed --
deadline, cancel, or a worker that died on its own -- `workerExited: true` appears **only after `waitpid` returned**,
and if the reap cannot be confirmed the result is `indeterminate` and the pool is one worker smaller, not "cleaned up".
A consumer holding the one-shot contract has to decide whether a retired job id is an acceptable barrier for it. This
file cannot make that decision either.

Wire, parent <-> worker and (via `residentd.py`) client <-> daemon: 4-byte big-endian length + UTF-8 JSON, the same
framing `residentd.mjs` uses.
"""
import base64
import json
import os
import signal
import socket
import struct
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (HERE, os.path.join(HERE, "..", "forge"), os.path.join(HERE, "..", "runtime", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

MAX_FRAME = (1 << 20) + 4096
KINDS = {"c": "compiled.c.step.v1", "c2": "compiled.c.step.v2"}


# ------------------------------------------------------------------------------------------------ framing
def send_frame(sock, obj):
    body = json.dumps(obj, sort_keys=True).encode("utf-8")
    sock.sendall(struct.pack(">I", len(body)) + body)


def recv_exactly(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def recv_frame(sock):
    head = recv_exactly(sock, 4)
    if head is None:
        return None
    (n,) = struct.unpack(">I", head)
    if n > MAX_FRAME:
        raise ValueError("frame of %d bytes exceeds %d" % (n, MAX_FRAME))
    body = recv_exactly(sock, n)
    if body is None:
        return None
    return json.loads(body.decode("utf-8"))


# ------------------------------------------------------------------------------------ the invalidation witness
def no_writable_state(so_path):
    """(ok, detail) -- does this object carry any mutable object OF ITS OWN?

    The claim "there is no instance state to carry between jobs" is the compiled host's replacement for the Wasm
    host's fresh-instance discipline, and unlike that discipline it can be CHECKED rather than witnessed. It is
    checked BY SYMBOL and not by section, which matters: the built `.so` does carry 16 writable bytes, and the first
    version of this check reported them and was right to. They are `__dso_handle` (`.data`, 8 B -- the handle the C
    runtime passes to `__cxa_atexit`) and `completed.0` (`.bss`, 1 B padded to 8 -- the guard in
    `__do_global_dtors_aux` that makes destructors run once). Both are emitted by the compiler for every shared
    object whatever its source. Widening a SECTION skip-list to cover them would also hide a real `static int` the
    emitter might one day grow, so the allow-list is of NAMES, and anything else in a writable allocated section is
    a refusal.
    """
    import re
    # C-runtime scaffolding present in every shared object; nothing here holds program state.
    allowed = {"__dso_handle", "completed.0", "__TMC_END__", "_DYNAMIC", "_GLOBAL_OFFSET_TABLE_", "__FRAME_END__",
               "__do_global_dtors_aux_fini_array_entry", "__frame_dummy_init_array_entry", "__GNU_EH_FRAME_HDR"}
    try:
        secs = subprocess.run(["readelf", "-SW", so_path], capture_output=True, timeout=30)
        syms = subprocess.run(["readelf", "-sW", so_path], capture_output=True, timeout=30)
    except FileNotFoundError:
        return None, {"error": "readelf not available"}
    if secs.returncode != 0 or syms.returncode != 0:
        return None, {"error": "readelf rc=%d/%d" % (secs.returncode, syms.returncode)}
    writable = {}                                          # section index -> (name, bytes)
    for line in secs.stdout.decode(errors="replace").splitlines():
        m = re.match(r"\s*\[\s*(\d+)\]\s+(\S+)\s+\S+\s+\S+\s+\S+\s+([0-9a-f]+)\s+\S+\s+(\S*)\s", line)
        if m and "W" in m.group(4) and "A" in m.group(4) and int(m.group(3), 16) > 0:
            writable[m.group(1)] = (m.group(2), int(m.group(3), 16))
    foreign = []
    for line in syms.stdout.decode(errors="replace").splitlines():
        f = line.split()
        if len(f) < 8 or f[3] != "OBJECT":
            continue
        ndx, name = f[6], f[7]
        if ndx in writable and name not in allowed:
            foreign.append({"symbol": name, "section": writable[ndx][0], "bytes": int(f[2])})
    return (not foreign), {"writable_sections": sorted(v[0] for v in writable.values()),
                           "writable_bytes": sum(v[1] for v in writable.values()),
                           "unexpected_objects": foreign}


# ------------------------------------------------------------------------------------------------ the worker
def _worker_main(fd, emitter):
    """One warm worker. Holds `executor.prepare`'s result per (plan bytes, emitter) and runs the SAME `executor.run`
    the one-shot process runs -- the checks are not reimplemented here, they are the same lines."""
    sock = socket.socket(fileno=fd)
    import executor as X                                  # the expensive import, paid once per worker
    cache, served = {}, 0
    send_frame(sock, {"worker": "ready", "pid": os.getpid()})
    while True:
        try:
            req = recv_frame(sock)
        except (ValueError, OSError):
            break
        if req is None:
            break
        t0 = time.perf_counter()
        timing = {}
        try:
            raw = base64.b64decode(req["bundle_b64"], validate=True)
            r, plan, control, state = X.read_bundle_bytes(raw)
            out = X.run(r, plan, control, state, req.get("emitter", emitter), cache=cache, timing=timing)
        except X.Refused as e:
            out = {"status": "refused", "reason": e.reason, "detail": e.detail}
        except Exception as e:                            # a worker must answer, not die, on a malformed frame
            out = {"status": "refused", "reason": "executor-error",
                   "detail": {"error": "%s: %s" % (type(e).__name__, str(e)[:200])}}
        served += 1
        send_frame(sock, {"id": req.get("id"), **out,
                          "workerExited": False, "jobRetired": True,
                          "worker": {"pid": os.getpid(), "jobs": served, "worlds_held": len(cache)},
                          "timing": dict(timing, total_us=round((time.perf_counter() - t0) * 1e6, 1))})
    sock.close()


# ------------------------------------------------------------------------------------------------ the pool
class _Worker:
    __slots__ = ("sock", "proc", "idx", "jobs")

    def __init__(self, idx, emitter):
        parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        self.proc = subprocess.Popen(
            [sys.executable, "-B", os.path.join(HERE, "resident.py"), "--worker", str(child.fileno()), "--emitter", emitter],
            pass_fds=(child.fileno(),), env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        child.close()
        self.sock, self.idx, self.jobs = parent, idx, 0

    def kill_and_reap(self, timeout=5.0):
        """SIGKILL then `waitpid`. The RETURN OF THE WAIT is the witness -- not the signal, which only asks."""
        try:
            self.proc.kill()
        except ProcessLookupError:
            pass
        try:
            self.proc.wait(timeout=timeout)
            confirmed = True
        except subprocess.TimeoutExpired:
            confirmed = False
        try:
            self.sock.close()
        except OSError:
            pass
        return confirmed


class Exhausted(Exception):
    pass


class ResidentCompiledHost:
    def __init__(self, pool=4, max_queue=16, emitter="c", start_timeout_s=60.0):
        if emitter not in KINDS:
            raise ValueError("emitter %r" % emitter)
        self.pool_size, self.max_queue, self.emitter = pool, max_queue, emitter
        self._cv = threading.Condition()
        self._idle, self._live = [], []
        self._waiting = 0
        self._closed = False
        self._next_idx = 0
        self._counts = {"served": 0, "replaced": 0, "unconfirmed": 0, "busy": 0, "exhausted": 0, "killed": 0}
        self._ready_err = None
        for _ in range(pool):
            self._spawn()
        self._start_timeout = start_timeout_s
        self._ready = False

    # ---- lifecycle
    def _spawn(self):
        w = _Worker(self._next_idx, self.emitter)
        self._next_idx += 1
        self._live.append(w)
        self._idle.append(w)
        return w

    def ready(self):
        """Block until every worker has announced itself. A pool that cannot start says so rather than serving."""
        if self._ready:
            return True
        deadline = time.monotonic() + self._start_timeout
        for w in list(self._live):
            w.sock.settimeout(max(0.1, deadline - time.monotonic()))
            try:
                hello = recv_frame(w.sock)
            except (OSError, ValueError) as e:
                raise RuntimeError("worker %d did not announce itself: %s" % (w.idx, e))
            finally:
                w.sock.settimeout(None)
            if not hello or hello.get("worker") != "ready":
                raise RuntimeError("worker %d announced %r" % (w.idx, hello))
        self._ready = True
        return True

    def close(self):
        with self._cv:
            self._closed = True
            live = list(self._live)
            self._live, self._idle = [], []
            self._cv.notify_all()
        for w in live:
            w.kill_and_reap()

    # ---- dispatch
    def _acquire(self, queue_timeout_s):
        with self._cv:
            if self._closed:
                return "closed"
            if not self._live:
                self._counts["exhausted"] += 1
                return "exhausted"
            if not self._idle and self._waiting >= self.max_queue:
                self._counts["busy"] += 1
                return "busy"
            self._waiting += 1
            try:
                end = time.monotonic() + queue_timeout_s
                while not self._idle:
                    if self._closed:
                        return "closed"
                    if not self._live:
                        self._counts["exhausted"] += 1
                        return "exhausted"
                    if not self._cv.wait(timeout=max(0.0, end - time.monotonic())):
                        return "queue-timeout"
                return self._idle.pop()
            finally:
                self._waiting -= 1

    def _release(self, w):
        with self._cv:
            if not self._closed and w in self._live:
                self._idle.append(w)
                self._cv.notify()

    def _retire(self, w, confirmed):
        """A worker that was killed or died leaves the pool; a replacement is spawned only when its absence is CONFIRMED."""
        with self._cv:
            if w in self._live:
                self._live.remove(w)
            if w in self._idle:
                self._idle.remove(w)
            closed = self._closed
        if not confirmed:
            self._counts["unconfirmed"] += 1
            return
        if closed:
            return
        with self._cv:
            if len(self._live) < self.pool_size:
                w2 = self._spawn()
                self._counts["replaced"] += 1
            else:
                w2 = None
        if w2 is not None:
            w2.sock.settimeout(self._start_timeout)
            try:
                hello = recv_frame(w2.sock)
                ok = bool(hello) and hello.get("worker") == "ready"
            except (OSError, ValueError):
                ok = False
            finally:
                w2.sock.settimeout(None)
            if ok:
                self._release(w2)
            else:
                with self._cv:
                    if w2 in self._live:
                        self._live.remove(w2)
                w2.kill_and_reap()

    def submit(self, bundle, deadline_s=10.0, queue_timeout_s=30.0, job_id=None, cancel=None):
        """One job. `bundle` is `executor.bundle_bytes(...)`. `cancel` is a `threading.Event`; setting it while the
        job is RUNNING kills its worker, because a native step cannot be asked to stop."""
        if not self._ready:
            self.ready()
        w = self._acquire(queue_timeout_s)
        if isinstance(w, str):
            return {"status": "refused", "reason": w, "id": job_id}
        if cancel is not None and cancel.is_set():
            self._release(w)
            return {"status": "cancelled", "id": job_id, "stage": "queued", "workerExited": False}
        t0 = time.perf_counter()
        try:
            send_frame(w.sock, {"id": job_id, "bundle_b64": base64.b64encode(bundle).decode(), "emitter": self.emitter})
        except OSError as e:
            confirmed = w.kill_and_reap()
            self._retire(w, confirmed)
            return {"status": "failed", "reason": "worker-write", "detail": str(e)[:200], "id": job_id,
                    "workerExited": confirmed, "indeterminate": not confirmed}
        end = time.monotonic() + deadline_s
        while True:
            remaining = end - time.monotonic()
            if remaining <= 0:
                break
            w.sock.settimeout(min(remaining, 0.05 if cancel is not None else remaining))
            try:
                reply = recv_frame(w.sock)
            except socket.timeout:
                if cancel is not None and cancel.is_set():
                    self._counts["killed"] += 1
                    confirmed = w.kill_and_reap()
                    self._retire(w, confirmed)
                    return {"status": "cancelled", "id": job_id, "stage": "running",
                            "workerExited": confirmed, "killed_confirmed": confirmed, "indeterminate": not confirmed}
                continue
            except (OSError, ValueError) as e:
                confirmed = w.kill_and_reap()
                self._retire(w, confirmed)
                return {"status": "failed", "reason": "worker-read", "detail": str(e)[:200], "id": job_id,
                        "workerExited": confirmed, "indeterminate": not confirmed}
            finally:
                try:
                    w.sock.settimeout(None)
                except OSError:
                    pass
            if reply is None:                              # the worker died without replying
                self._counts["killed"] += 1
                confirmed = w.kill_and_reap()
                self._retire(w, confirmed)
                return {"status": "failed", "reason": "worker-exited", "id": job_id,
                        "workerExited": confirmed, "indeterminate": not confirmed}
            if reply.get("id") != job_id:
                # A reply under a foreign or retired id changes nothing: it is not this job's answer, and a worker
                # that answers out of order is a worker that cannot be trusted to answer in order.
                self._counts["killed"] += 1
                confirmed = w.kill_and_reap()
                self._retire(w, confirmed)
                return {"status": "failed", "reason": "foreign-job-id", "id": job_id, "read": reply.get("id"),
                        "workerExited": confirmed, "indeterminate": not confirmed}
            w.jobs += 1
            with self._cv:
                self._counts["served"] += 1
            self._release(w)
            reply["hostMs"] = round((time.perf_counter() - t0) * 1e3, 3)
            return reply
        # deadline: the ONLY way to stop a native step
        self._counts["killed"] += 1
        confirmed = w.kill_and_reap()
        self._retire(w, confirmed)
        return {"status": "refused" if confirmed else "indeterminate", "reason": "deadline", "id": job_id,
                "deadline_s": deadline_s, "workerExited": confirmed, "killed_confirmed": confirmed,
                "indeterminate": not confirmed}

    def stats(self):
        with self._cv:
            return {"pool": self.pool_size, "live": len(self._live), "idle": len(self._idle),
                    "waiting": self._waiting, "max_queue": self.max_queue, "emitter": self.emitter,
                    "kind": KINDS[self.emitter], "closed": self._closed, **self._counts}


def _main(argv):
    if argv and argv[0] == "--worker":
        fd = int(argv[1])
        emitter = argv[argv.index("--emitter") + 1] if "--emitter" in argv else "c"
        _worker_main(fd, emitter)
        return 0
    print(__doc__.strip().splitlines()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
