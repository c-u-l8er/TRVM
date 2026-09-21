#!/usr/bin/env python3
"""resident_test.py -- the resident compiled executor's harness (`RESIDENT.md` §5).

    PYTHONDONTWRITEBYTECODE=1 python3 -B resident_test.py

The letters mirror `runtime/wasm/resident/resident.test.mjs` where the case is the same question, so the two hosts
can be read side by side; where the compiled host's answer differs the case says why in its own docstring. What is
NOT mirrored is F1, the Wasm host's fresh-instance witness: there is no instance here, and N1/N2 check the stronger
statement instead.
"""
import base64
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (HERE, os.path.join(HERE, "..", "forge"), os.path.join(HERE, "..", "runtime", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.dont_write_bytecode = True
os.environ.setdefault("TRVM_BATTERY_HUGE", "1")

import emit_c as EC                                    # noqa: E402
import emit_c2 as EC2                                  # noqa: E402
import executor as X                                   # noqa: E402
import make_bundle as MB                               # noqa: E402
import battery as B                                    # noqa: E402
from fold import SB, P                                 # noqa: E402
from resident import ResidentCompiledHost, no_writable_state, send_frame, recv_frame   # noqa: E402

WORLDS = ["chain30", "golden-demo", "pulser-relay", "chain120"]
_BUNDLES = {}


def bundle(world, epoch=1, emitter="c"):
    key = (world, epoch, emitter)
    if key not in _BUNDLES:
        _BUNDLES[key] = MB.build(world, epoch, emitter)
    return _BUNDLES[key]


class Identity(unittest.TestCase):
    """I -- the warm path answers exactly what the one-shot process answers."""

    @classmethod
    def setUpClass(cls):
        cls.h = ResidentCompiledHost(pool=2, max_queue=8)
        cls.h.ready()

    @classmethod
    def tearDownClass(cls):
        cls.h.close()

    def test_I1_the_witness_world_keeps_its_recorded_digest(self):
        b, meta = bundle("chain30")
        self.assertEqual(meta["nf_sha256"][:8], "2318bd82")          # the vertical witness's golden receipt
        r = self.h.submit(b, job_id="I1")
        self.assertEqual(r["status"], "candidate")
        self.assertEqual(r["nf_sha256"], meta["nf_sha256"])
        self.assertEqual(r["nf_bytes"], 3260)

    def test_I2_every_world_warm_equals_the_same_world_one_shot_field_for_field(self):
        for w in WORLDS:
            b, _ = bundle(w)
            req, plan, ctl, st = X.read_bundle_bytes(b)
            cold = X.run(req, plan, ctl, st, "c")
            warm = self.h.submit(b, job_id="I2-" + w)
            self.assertEqual(warm["status"], "candidate", w)
            for k in cold:                                            # every field of the candidate, not just the digest
                self.assertEqual(warm[k], cold[k], "%s field %s" % (w, k))

    def test_I3_both_emitters(self):
        for em in ("c", "c2"):
            h = ResidentCompiledHost(pool=1, max_queue=2, emitter=em)
            try:
                h.ready()
                b, meta = bundle("chain30", 1, em)
                r = h.submit(b, job_id="I3")
                self.assertEqual(r["status"], "candidate", em)
                self.assertEqual(r["nf_sha256"], meta["nf_sha256"], em)
                self.assertEqual(r["kind"], X.KINDS[em])
            finally:
                h.close()


class NoInstanceState(unittest.TestCase):
    """N -- the compiled host's replacement for the Wasm host's fresh-instance discipline."""

    def test_N1_no_emitted_object_carries_a_mutable_object_of_its_own(self):
        os.environ.setdefault("TRVM_BATTERY_HUGE", "1")
        checked = 0
        for name, src in B.WORLDS.items():
            prog, _ = SB._resolve_scenario(src, None)
            view = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
            for cls in (EC.CompiledStep, EC2.CompiledStep2):
                cs = cls(view, prog.semantic_artifact_id)
                ok, detail = no_writable_state(cs.so_path)
                self.assertIsNotNone(ok, "readelf unavailable")
                self.assertTrue(ok, "%s %s: %s" % (name, cls.__name__, detail))
                checked += 1
        self.assertGreaterEqual(checked, 2 * 19)

    def test_N1b_the_check_would_catch_a_static(self):
        """A check that cannot fail is not a check: give the same compiler a `static long` and watch it refuse."""
        with tempfile.TemporaryDirectory() as td:
            c = os.path.join(td, "s.c")
            with open(c, "w") as f:
                f.write("#include <stdint.h>\nstatic int64_t carried;\n"
                        "void step_v6(const int64_t*a,const int64_t*b,int64_t*o){carried+=a[0]+b[0];o[0]=carried;}\n")
            so = os.path.join(td, "s.so")
            subprocess.run(["gcc", "-O2", "-shared", "-fPIC", "-o", so, c], check=True, capture_output=True)
            ok, detail = no_writable_state(so)
            self.assertFalse(ok, detail)
            self.assertIn("carried", [o["symbol"] for o in detail["unexpected_objects"]])

    def test_N2_worlds_held_together_do_not_contaminate_each_other(self):
        """One warm worker holds four worlds at once; each still answers its own bytes, interleaved."""
        h = ResidentCompiledHost(pool=1, max_queue=8)
        try:
            h.ready()
            want = {w: bundle(w)[1]["nf_sha256"] for w in WORLDS}
            for _round in range(3):
                for w in WORLDS:
                    r = h.submit(bundle(w)[0], job_id="N2-%s" % w)
                    self.assertEqual(r["nf_sha256"], want[w], w)
            self.assertEqual(h.stats()["served"], 3 * len(WORLDS))
            self.assertEqual(r["worker"]["worlds_held"], len(WORLDS))     # one process, four .so's, no crosstalk
        finally:
            h.close()


class Concurrency(unittest.TestCase):
    """X, P -- every reply reaches its own requester, and the pool's counters add up."""

    def test_X1_P1_many_jobs_across_workers_each_to_its_own_requester(self):
        # The queue admits all 48: this case asks whether replies reach their own requesters, and the BOUND is Q1's
        # question. Sized at 32 the last twelve were correctly refused `busy` -- the host was right and the case was
        # asking two things at once.
        h = ResidentCompiledHost(pool=4, max_queue=64)
        try:
            h.ready()
            want = {w: bundle(w)[1]["nf_sha256"] for w in WORLDS}
            got, errs = [], []
            lock = threading.Lock()

            def one(i):
                w = WORLDS[i % len(WORLDS)]
                r = h.submit(bundle(w)[0], job_id="X1-%d" % i)
                with lock:
                    if r.get("nf_sha256") != want[w] or r.get("id") != "X1-%d" % i:
                        errs.append((i, w, r.get("status"), r.get("id")))
                    got.append(i)

            ts = [threading.Thread(target=one, args=(i,)) for i in range(48)]
            for t in ts:
                t.start()
            for t in ts:
                t.join(timeout=120)
            self.assertEqual(errs, [])
            self.assertEqual(len(got), 48)
            self.assertEqual(h.stats()["served"], 48)
            self.assertEqual(h.stats()["live"], 4)
        finally:
            h.close()


class Refusals(unittest.TestCase):
    """E -- a refusal on the warm path is the one-shot's refusal, with the same reason."""

    @classmethod
    def setUpClass(cls):
        cls.h = ResidentCompiledHost(pool=1, max_queue=4)
        cls.h.ready()

    @classmethod
    def tearDownClass(cls):
        cls.h.close()

    def _mutated(self, fn):
        b, _ = bundle("chain30")
        d = json.loads(b.decode())
        fn(d)
        return json.dumps(d).encode()

    def test_E1_request_mismatch_is_refused_warm_exactly_as_cold(self):
        bad = self._mutated(lambda d: d["request"]["params"].__setitem__("state_sha256", "0" * 64))
        r = self.h.submit(bad, job_id="E1")
        self.assertEqual((r["status"], r["reason"]), ("refused", "request-mismatch"))
        self.assertEqual(r["detail"]["field"], "state_sha256")

    def test_E2_a_plan_that_does_not_bind_is_refused(self):
        bad = self._mutated(lambda d: d["request"]["params"].__setitem__("sem", "sem-" + "0" * 64))
        r = self.h.submit(bad, job_id="E2")
        self.assertEqual((r["status"], r["reason"]), ("refused", "plan-not-bound"))

    def test_E3_a_malformed_bundle_is_refused_and_the_worker_survives(self):
        r = self.h.submit(b'{"bundle": 2}', job_id="E3")
        self.assertEqual((r["status"], r["reason"]), ("refused", "bundle-malformed"))
        ok = self.h.submit(bundle("chain30")[0], job_id="E3b")
        self.assertEqual(ok["status"], "candidate")                  # a refusal must not cost the pool a worker
        self.assertEqual(self.h.stats()["live"], 1)

    def test_E4_a_refusal_carries_jobRetired_not_a_pretend_exit(self):
        bad = self._mutated(lambda d: d["request"]["params"].__setitem__("kind", "nonsense"))
        r = self.h.submit(bad, job_id="E4")
        self.assertEqual(r["reason"], "request-mismatch")
        self.assertIs(r["workerExited"], False)
        self.assertIs(r["jobRetired"], True)


class ObjectIdentity(unittest.TestCase):
    """B -- F-B is checked PER JOB on the warm path, not once at construction."""

    def test_B1_a_stale_object_is_refused(self):
        """Built in a temp directory rather than the shared cache: a test must not corrupt an object another
        session's battery is about to dlopen."""
        with tempfile.TemporaryDirectory() as td:
            c, so = os.path.join(td, "t.c"), os.path.join(td, "t.so")
            with open(c, "w") as f:
                f.write("#include <stdint.h>\nvoid step_v6(const int64_t*a,const int64_t*b,int64_t*o){o[0]=a[0]+b[0];}\n")
            subprocess.run(["gcc", "-O2", "-shared", "-fPIC", "-o", so, c], check=True, capture_output=True)
            stub = type("S", (), {"so_path": so})()
            self.assertEqual(len(X.check_object(stub)), 64)          # first call records the sidecar
            self.assertEqual(X.check_object(stub), X.check_object(stub))
            with open(so + ".sha256", "w") as f:
                f.write("0" * 64 + "\n")
            with self.assertRaises(X.Refused) as cm:
                X.check_object(stub)
            self.assertEqual(cm.exception.reason, "stale-object")

    def test_B2_the_warm_path_checks_the_object_on_every_job(self):
        """The timing the host reports is the evidence: a per-job cost that is never zero after the first job."""
        h = ResidentCompiledHost(pool=1, max_queue=4)
        try:
            h.ready()
            costs = []
            for i in range(5):
                r = h.submit(bundle("chain30")[0], job_id="B2-%d" % i)
                self.assertEqual(r["status"], "candidate")
                costs.append(r["timing"]["object_check_us"])
            self.assertTrue(all(c > 0 for c in costs), costs)
            self.assertTrue(all(r["timing"]["plan_cached"] for r in [r]))
        finally:
            h.close()


class Cancellation(unittest.TestCase):
    """C, D -- the only way to stop a native step is to kill the process that is running it."""

    def test_C1_a_queued_job_is_cancelled_without_touching_a_worker(self):
        h = ResidentCompiledHost(pool=1, max_queue=4)
        try:
            h.ready()
            ev = threading.Event()
            ev.set()
            r = h.submit(bundle("chain30")[0], job_id="C1", cancel=ev)
            self.assertEqual((r["status"], r["stage"]), ("cancelled", "queued"))
            self.assertIs(r["workerExited"], False)
            self.assertEqual(h.stats()["live"], 1)
            self.assertEqual(h.stats()["killed"], 0)
        finally:
            h.close()

    def test_D1_a_deadline_kills_the_worker_reaps_it_and_the_pool_heals(self):
        h = ResidentCompiledHost(pool=2, max_queue=4)
        try:
            h.ready()
            before = {w.proc.pid for w in h._live}
            r = h.submit(bundle("chain120")[0], job_id="D1", deadline_s=0.001)
            self.assertEqual(r["reason"], "deadline")
            self.assertIs(r["killed_confirmed"], True)               # `waitpid` RETURNED -- not merely signalled
            self.assertIs(r["workerExited"], True)
            self.assertEqual(r["status"], "refused")
            deadline = time.monotonic() + 30
            while h.stats()["live"] < 2 and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertEqual(h.stats()["live"], 2)                   # replaced
            self.assertEqual(h.stats()["replaced"], 1)
            self.assertNotEqual({w.proc.pid for w in h._live}, before)
            ok = h.submit(bundle("chain30")[0], job_id="D1b")
            self.assertEqual(ok["status"], "candidate")              # and the replacement is a REAL worker
        finally:
            h.close()

    def test_W1_a_worker_that_dies_without_replying_is_typed_and_replaced(self):
        h = ResidentCompiledHost(pool=1, max_queue=4)
        try:
            h.ready()
            h._live[0].proc.kill()
            h._live[0].proc.wait(timeout=10)
            r = h.submit(bundle("chain30")[0], job_id="W1")
            self.assertEqual(r["status"], "failed")
            self.assertIn(r["reason"], ("worker-exited", "worker-write", "worker-read"))
            self.assertIs(r["workerExited"], True)
            deadline = time.monotonic() + 30
            while h.stats()["live"] < 1 and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertEqual(h.submit(bundle("chain30")[0], job_id="W1b")["status"], "candidate")
        finally:
            h.close()


class Bounds(unittest.TestCase):
    """Q, U -- the queue bound, and what happens with no worker left."""

    def test_Q1_the_queue_bound_refuses_busy_and_close_refuses_after(self):
        h = ResidentCompiledHost(pool=1, max_queue=1)
        try:
            h.ready()
            hold = threading.Event()
            results = []

            def slow(i):
                results.append(h.submit(bundle("chain120")[0], job_id="Q1-%d" % i, queue_timeout_s=20))

            ts = [threading.Thread(target=slow, args=(i,)) for i in range(6)]
            for t in ts:
                t.start()
            for t in ts:
                t.join(timeout=120)
            busy = [r for r in results if r.get("reason") == "busy"]
            self.assertGreaterEqual(len(busy), 1, [r.get("status") for r in results])
            self.assertEqual(h.stats()["busy"], len(busy))
        finally:
            h.close()
        self.assertEqual(h.submit(bundle("chain30")[0], job_id="Q1-after")["reason"], "closed")

    def test_U1_with_no_worker_left_requests_are_refused_exhausted(self):
        h = ResidentCompiledHost(pool=1, max_queue=2)
        try:
            h.ready()
            with h._cv:
                dead = h._live.pop()
                h._idle.clear()
            dead.kill_and_reap()
            r = h.submit(bundle("chain30")[0], job_id="U1")
            self.assertEqual((r["status"], r["reason"]), ("refused", "exhausted"))
        finally:
            h.close()


class OverTheSocket(unittest.TestCase):
    """S -- the daemon: identity, pipelining, the stats frame, and a connection close aborting its jobs."""

    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp(prefix="residentd-test-")
        cls.sock = os.path.join(cls.dir, "d.sock")
        cls.proc = subprocess.Popen(
            [sys.executable, "-B", os.path.join(HERE, "residentd.py"), "--socket", cls.sock, "--pool", "2"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        line = cls.proc.stdout.readline().decode()
        cls.announce = json.loads(line)

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        try:
            cls.proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            cls.proc.kill()

    def conn(self):
        s = socket.socket(socket.AF_UNIX)
        s.connect(self.sock)
        self.addCleanup(s.close)
        return s

    def test_S0_it_announces_only_after_every_worker_is_ready(self):
        self.assertEqual(self.announce["residentd"], self.sock)
        self.assertEqual(self.announce["ready"], 2)
        self.assertEqual(self.announce["kind"], "compiled.c.step.v1")

    def test_S1_identity_over_the_wire(self):
        s = self.conn()
        b, meta = bundle("chain30")
        send_frame(s, {"id": 1, "bundle_b64": base64.b64encode(b).decode()})
        r = recv_frame(s)
        self.assertEqual(r["nf_sha256"], meta["nf_sha256"])
        self.assertIs(r["jobRetired"], True)
        self.assertIn("serverMs", r)

    def test_S2_pipelining_one_connection(self):
        s = self.conn()
        b, meta = bundle("chain30")
        n = 12
        for i in range(n):
            send_frame(s, {"id": i, "bundle_b64": base64.b64encode(b).decode()})
        seen = {}
        for _ in range(n):
            r = recv_frame(s)
            seen[r["id"]] = r["nf_sha256"]
        self.assertEqual(set(seen), set(range(n)))
        self.assertEqual(set(seen.values()), {meta["nf_sha256"]})

    def test_S3_stats_and_a_malformed_request(self):
        s = self.conn()
        send_frame(s, {"op": "stats"})
        st = recv_frame(s)
        self.assertEqual(st["op"], "stats")
        self.assertEqual(st["pool"], 2)
        send_frame(s, {"id": 99})
        self.assertEqual(recv_frame(s)["reason"], "request-shape")

    def test_S4_a_duplicate_id_is_refused(self):
        s = self.conn()
        b, _ = bundle("chain120")
        f = base64.b64encode(b).decode()
        send_frame(s, {"id": 7, "bundle_b64": f})
        send_frame(s, {"id": 7, "bundle_b64": f})
        reasons = []
        for _ in range(2):
            reasons.append(recv_frame(s).get("reason"))
        self.assertIn("duplicate-id", reasons)

    def test_S5_a_closed_connection_leaves_the_pool_whole(self):
        s = self.conn()
        b, _ = bundle("chain30")
        send_frame(s, {"id": 1, "bundle_b64": base64.b64encode(b).decode()})
        recv_frame(s)
        s.close()
        time.sleep(0.5)
        s2 = self.conn()
        send_frame(s2, {"op": "stats"})
        st = recv_frame(s2)
        self.assertEqual(st["live"], 2)
        self.assertFalse(st["closed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
