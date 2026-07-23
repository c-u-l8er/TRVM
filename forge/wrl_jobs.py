"""wrl_jobs.py v0.6-1 -- ephemeral runtime-job lifecycle (Forge World Library,
phase 8: release hardening step 1).

GPT-5.6's v0.6 sequence puts a runtime-JOB lifecycle after the v0.6-0
crash-recovery journal: the long ic-reducer folds (/api/run + /api/verify,
especially the native ic32 verify) become cancellable background jobs with an
observable state machine and progress -- and a client that navigates away no
longer aborts the computation (nor trips a BrokenPipeError writing to a dead
socket), because the compute is decoupled from the request that observes it.

    queued -> running -> completed
                      -> failed
                      -> cancelled            (from queued OR running)

This module is PURE orchestration. It knows nothing about the reducer, the
identity ladder, or the HTTP server: the caller injects an `execute(kind,
request, progress, should_cancel)` callable that does the actual fold, and an
optional serialization `lock` (the server passes its ic-reducer pipeline lock so
a job cannot interleave the interpreter's module-global state with a legacy
synchronous /api/run). Because the registry takes an injected executor, the
acceptance battery drives the FULL lifecycle deterministically -- queue, run,
cancel-while-queued, cancel-between-epochs, failure, bounded eviction -- without
starting the HTTP server or touching a real reducer.

Design decisions (autonomous, flagged for GPT-5.6):
  * Jobs are EPHEMERAL / in-memory. A job is compute, not authored workspace
    state -- the v0.6-0 recovery journal owns durability. A restart drops
    in-flight jobs (nothing the author wrote is lost); it never persists a job.
  * Cooperative cancellation is checked at EPOCH BOUNDARIES. A single-epoch
    reducer fold is atomic and uninterruptible; the executor calls
    `should_cancel()` before each epoch (native ic32 at the same granularity).
  * The synchronous /api/run + /api/verify endpoints STAY (batteries, the
    Fixture-oracle path, backward compat); jobs are an ADDITIVE async lane.
  * NO new identity and NO new runtime construct: a job carries an opaque
    request + a result payload produced by the same lowering/fold as before.
"""
import queue
import threading
import time
import uuid

import wrl_canonical as WC

RUNTIME_JOB_VERSION = "forge.runtime_job.v1"

JOB_KINDS = ("run", "verify", "deep_health")

# the observable state machine
JOB_QUEUED = "queued"
JOB_RUNNING = "running"
JOB_COMPLETED = "completed"
JOB_FAILED = "failed"
JOB_CANCELLED = "cancelled"
JOB_STATES = (JOB_QUEUED, JOB_RUNNING, JOB_COMPLETED, JOB_FAILED, JOB_CANCELLED)
TERMINAL_STATES = (JOB_COMPLETED, JOB_FAILED, JOB_CANCELLED)

# the typed snapshot contract (JSON-safe; exactly these keys, always)
RUNTIME_JOB_FIELDS = ("runtime_job_version", "job_id", "kind", "state",
                      "progress", "request", "result", "error",
                      "cancel_requested", "created_at", "started_at",
                      "finished_at")

# typed diagnostics (never a raw KeyError/ValueError crosses the boundary)
WRL_JOB_MISSING = "WRL_JOB_MISSING"    # get/cancel of an unknown job id
WRL_BAD_JOB = "WRL_BAD_JOB"            # bad kind / malformed request


class JobCancelled(Exception):
    """Raised by an executor (via `should_cancel()`) to abandon a running fold at
    an epoch boundary. Distinct from a failure -- the registry maps it to the
    `cancelled` terminal state, NOT `failed`. Executors that wrap the fold in a
    broad `except Exception` MUST re-raise this so cancellation is not silently
    turned into a failed result."""


class _Job(object):
    """The internal MUTABLE job record. Never handed out directly -- callers only
    ever see an immutable `_snapshot` dict."""
    __slots__ = ("job_id", "kind", "request", "state", "progress", "result",
                 "error", "created_at", "started_at", "finished_at", "seq",
                 "_cancel")

    def __init__(self, job_id, kind, request, seq, now):
        self.job_id = job_id
        self.kind = kind
        self.request = request
        self.seq = seq
        self.state = JOB_QUEUED
        self.progress = {"done": 0, "total": 0, "phase": None}
        self.result = None
        self.error = None
        self.created_at = now
        self.started_at = None
        self.finished_at = None
        self._cancel = threading.Event()


def _snapshot(job):
    """A JSON-safe, immutable view of a job -- exactly RUNTIME_JOB_FIELDS."""
    return {
        "runtime_job_version": RUNTIME_JOB_VERSION,
        "job_id": job.job_id,
        "kind": job.kind,
        "state": job.state,
        "progress": dict(job.progress),
        "request": job.request,
        "result": job.result,
        "error": job.error,
        "cancel_requested": job._cancel.is_set(),
        "created_at": job.created_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
    }


class JobRegistry(object):
    """A single-worker runtime-job registry.

    `execute(kind, request, progress, should_cancel) -> result_dict` performs the
    actual fold. It should call `progress(done, total, phase)` as it advances and
    check `should_cancel()` at each epoch boundary, raising `JobCancelled` when it
    returns True. Any other exception marks the job `failed` with a typed message;
    a normal return marks it `completed` and stores the returned payload.

    `lock` (optional) is held for the duration of `execute` so a job serializes
    against any other reducer work sharing that lock (the server passes its
    ic-reducer pipeline lock). `worker=False` disables the background thread so a
    test can drive the queue synchronously via `run_pending()`.
    """

    def __init__(self, execute, lock=None, max_jobs=64, clock=None, worker=True):
        self._execute = execute
        self._lock = lock or threading.Lock()      # serializes the fold itself
        self._reg = threading.Lock()               # guards _jobs / _order
        self._jobs = {}
        self._order = []                           # insertion order (ring)
        self._q = queue.Queue()
        self._clock = clock or time.time
        self._max = int(max_jobs)
        self._seq = 0
        self._worker = None
        self._stop = object()
        if worker:
            self.start()

    # ------------------------------------------------------------ worker thread
    def start(self):
        if self._worker is not None:
            return
        t = threading.Thread(target=self._worker_loop, name="wrl-jobs",
                             daemon=True)
        self._worker = t
        t.start()

    def stop(self):
        """Signal the worker to drain and exit (used only at shutdown/tests)."""
        if self._worker is None:
            return
        self._q.put(self._stop)

    def _worker_loop(self):
        while True:
            job = self._q.get()
            if job is self._stop:
                return
            self._execute_job(job)

    # ------------------------------------------------------------- public API
    def submit(self, kind, request):
        """Enqueue a job; returns its id. The job starts `queued`."""
        if kind not in JOB_KINDS:
            WC._fail(WRL_BAD_JOB,
                     "unknown job kind %r (allowed: %s)" % (kind,
                                                            list(JOB_KINDS)))
        if not isinstance(request, dict):
            WC._fail(WRL_BAD_JOB, "job request must be an object")
        now = self._clock()
        with self._reg:
            self._seq += 1
            job_id = "job-%s-%d" % (uuid.uuid4().hex[:12], self._seq)
            job = _Job(job_id, kind, request, self._seq, now)
            self._jobs[job_id] = job
            self._order.append(job_id)
            self._evict_locked()
        self._q.put(job)
        return job_id

    def get(self, job_id):
        with self._reg:
            job = self._jobs.get(job_id)
            if job is None:
                WC._fail(WRL_JOB_MISSING, "no runtime job %r" % (job_id,))
            return _snapshot(job)

    def cancel(self, job_id):
        """Request cancellation. Terminal jobs are unchanged (idempotent). A
        `queued` job is cancelled immediately (the worker skips it); a `running`
        job has its cancel flag set and stops at the next epoch boundary."""
        with self._reg:
            job = self._jobs.get(job_id)
            if job is None:
                WC._fail(WRL_JOB_MISSING, "no runtime job %r" % (job_id,))
            if job.state in TERMINAL_STATES:
                return _snapshot(job)
            job._cancel.set()
            if job.state == JOB_QUEUED:
                job.state = JOB_CANCELLED
                job.finished_at = self._clock()
            return _snapshot(job)

    def list(self, limit=None):
        """Snapshots, NEWEST first."""
        with self._reg:
            ids = list(reversed(self._order))
            if limit is not None:
                ids = ids[:int(limit)]
            return [_snapshot(self._jobs[i]) for i in ids]

    def run_pending(self, block=False, timeout=None):
        """SYNCHRONOUS drive (worker=False mode, for tests): pull one queued job
        and execute it on the CALLING thread. Returns True if a job ran, False if
        the queue was empty. `block=True` waits up to `timeout` for a job."""
        try:
            job = self._q.get(block=block, timeout=timeout)
        except queue.Empty:
            return False
        if job is self._stop:
            return False
        self._execute_job(job)
        return True

    # --------------------------------------------------------------- internals
    def _evict_locked(self):
        """Bound the registry: drop the OLDEST terminal jobs past the cap. Never
        evict a queued/running job (its result is still pending). Caller holds
        _reg."""
        if len(self._jobs) <= self._max:
            return
        keep = []
        over = len(self._jobs) - self._max
        for jid in self._order:
            job = self._jobs.get(jid)
            if job is None:
                continue
            if over > 0 and job.state in TERMINAL_STATES:
                del self._jobs[jid]
                over -= 1
                continue
            keep.append(jid)
        self._order = keep

    def _set_state(self, job, state, **fields):
        with self._reg:
            job.state = state
            for k, v in fields.items():
                setattr(job, k, v)

    def _execute_job(self, job):
        # A job cancelled while still queued never runs.
        with self._reg:
            if job.state == JOB_CANCELLED:
                return
            job.state = JOB_RUNNING
            job.started_at = self._clock()

        def progress(done, total, phase=None):
            with self._reg:
                job.progress = {"done": int(done), "total": int(total),
                                "phase": phase}

        def should_cancel():
            return job._cancel.is_set()

        try:
            with self._lock:
                if should_cancel():
                    raise JobCancelled()
                result = self._execute(job.kind, job.request, progress,
                                       should_cancel)
        except JobCancelled:
            self._set_state(job, JOB_CANCELLED, finished_at=self._clock())
        except Exception as ex:            # noqa: BLE001 -- typed at boundary
            self._set_state(job, JOB_FAILED,
                            error="%s: %s" % (type(ex).__name__, ex),
                            finished_at=self._clock())
        else:
            self._set_state(job, JOB_COMPLETED, result=result,
                            finished_at=self._clock())
