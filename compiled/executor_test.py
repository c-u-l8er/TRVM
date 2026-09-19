"""executor_test.py -- the compiled executor process against the witness's identities and the proposal's falsifiers (§5).
    python3 -m unittest executor_test -v
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import executor as X          # noqa: E402
import battery as B           # noqa: E402
import fold as F              # noqa: E402
from fold import SB, P, C     # noqa: E402
import wrl_canonical as WC    # noqa: E402
import wrl_plan as WP         # noqa: E402

COMPUTE = os.environ.get("B2_COMPUTE_DIR") or os.path.join(HERE, "..", "..", "wek", "b2", "compute")
CHAIN30_NF = "2318bd828467fea8f7ecb2e214a0a9fc736c23c08e62feacfa1c7d57d5118eb6"     # the witness's golden receipt
CHAIN30_FILM1 = "08d6318a20c4c830c4670730bb66cab1190452dfa3dc6385e75f3ff54f317f3f"
GOLDEN_NF = "b755abdf955c4c243c288dcabf15041a4a691021a1a1f6ade0595fcc2ccceca1"       # results-payload.json / measure.json
GOLDEN_FILM1 = "56a2980eb5530db2508483950a71f059767cf16e9ac89ddb58551f1f540621f1"     # measure.json films[0]
sha = lambda b: hashlib.sha256(b).hexdigest()


def prepare(src, scenario=None):
    """What the bridge would carry beside each epoch's request: the sealed plan's canonical bytes, and per epoch the
    control text and the previous payload -- produced by Forge's own encoders over the production admission seams."""
    prog, scen = SB._resolve_scenario(src, scenario)
    plan = P.artifact_to_compile_plan_v1(prog.sealed_artifact)
    sealed = WP.seal_compile_plan(plan, prog.sealed_artifact)
    sem, view, scen_dig, script, world, claim, seams = F._prepare(src, scenario)
    epochs = []
    prev = X.render(view, world)
    for e, (label, batch) in enumerate(script):
        claim, cfg_map, resets = F.FD.admit_step_sealed(claim, batch, 1 + e, view, seams)
        control = C.enc_config_bundle(view, cfg_map, resets)
        epochs.append({"epoch": 1 + e, "control": control, "state": prev, "cfg_map": cfg_map, "resets": resets})
        world = F.CompiledStep(view, sem).step(world, cfg_map, resets)
        prev = X.render(view, world)
    return sem, scen_dig, sealed, epochs


def request(sem, scen_dig, epoch, plan_bytes, control, state, kind="compiled.c.step.v1"):
    return {"er": "er-trvm.reduce", "rev": 1, "params": {
        "kind": kind, "sem": sem, "scenario_digest": scen_dig, "epoch": epoch,
        "plan_sha256": sha(plan_bytes), "control_sha256": sha(control.encode()), "state_sha256": sha(state.encode()),
        "state_bytes": len(state.encode())}}


class Golden(unittest.TestCase):
    def test_G1c_chain30_epoch1_is_the_witness_receipt(self):
        sem, dig, sealed, eps = prepare(B.WORLDS["chain30"])
        e = eps[0]
        r = X.run(request(sem, dig, 1, sealed.canonical_bytes, e["control"], e["state"]), sealed.canonical_bytes, e["control"], e["state"])
        self.assertEqual(r["status"], "candidate")
        self.assertEqual((r["nf_sha256"], r["nf_bytes"]), (CHAIN30_NF, 3260))
        self.assertEqual(r["backend_id"], json.load(open(os.path.join(HERE, "results-payload.json")))["worlds"][[w["world"] for w in json.load(open(os.path.join(HERE, "results-payload.json")))["worlds"]].index("chain30")]["backend_id"])
        # the receipted bytes are the payload file the witness carries
        self.assertEqual(r["output"].encode(), open(os.path.join(COMPUTE, "terms", "chain30-epoch-1.nf.payload"), "rb").read())

    def test_G2c_golden_demo_epoch1_the_world_the_calculus_kind_cannot_run(self):
        sem, dig, sealed, eps = prepare(B.WORLDS["golden-demo"])
        e = eps[0]
        r = X.run(request(sem, dig, 1, sealed.canonical_bytes, e["control"], e["state"]), sealed.canonical_bytes, e["control"], e["state"])
        self.assertEqual(r["status"], "candidate")
        self.assertEqual(r["nf_sha256"], GOLDEN_NF)

    def test_films_of_the_executor_are_the_production_films(self):
        """Fold every epoch of chain30 and the demo world THROUGH the process's own step+render, decode the payloads back,
        and film them: the films must be the calculus's cached production films, epoch 1 the two the witness quotes."""
        for name, film1 in (("chain30", CHAIN30_FILM1), ("golden-demo", GOLDEN_FILM1)):
            src = B.WORLDS[name]
            sem, dig, sealed, eps = prepare(src)
            refs, _ = F.cached_reference_films(src, "ic_ref", None)
            view = P.plan_view(sealed.canonical_plan)
            state = eps[0]["state"]
            films = []

            def step_fn(v, world, cfg_map, resets, _s={"state": state}):
                e = next(x for x in eps if x["cfg_map"] == cfg_map and x["resets"] == resets and x["state"] == _s["state"])
                r = X.run(request(sem, dig, e["epoch"], sealed.canonical_bytes, e["control"], _s["state"]), sealed.canonical_bytes, e["control"], _s["state"])
                self.assertEqual(r["status"], "candidate", r)
                _s["state"] = r["output"]
                X.reset_runtime()
                return C.dec_state_v6(v, X.parse(r["output"]))
            _, _, rows = F._loop(src, None, step_fn)
            films = [row["film"] for row in rows]
            self.assertEqual(films, refs[:len(films)], name)
            self.assertEqual(films[0], film1, name)

    def test_determinism_two_processes_one_identity(self):
        sem, dig, sealed, eps = prepare(B.WORLDS["chain30"])
        e = eps[0]
        with tempfile.TemporaryDirectory() as d:
            paths = {k: os.path.join(d, k) for k in ("request", "plan", "control", "state")}
            open(paths["plan"], "wb").write(sealed.canonical_bytes)
            open(paths["control"], "w").write(e["control"]); open(paths["state"], "w").write(e["state"])
            json.dump(request(sem, dig, 1, sealed.canonical_bytes, e["control"], e["state"]), open(paths["request"], "w"))
            outs = [subprocess.run([sys.executable, os.path.join(HERE, "executor.py"), "--request", paths["request"], "--plan", paths["plan"], "--control", paths["control"], "--state", paths["state"]], capture_output=True, text=True) for _ in range(2)]
            self.assertTrue(all(o.returncode == 0 for o in outs), [o.stderr[-300:] for o in outs])
            a, b = (json.loads(o.stdout) for o in outs)
            self.assertEqual(a, b)
            self.assertEqual(a["nf_sha256"], CHAIN30_NF)


class Falsifiers(unittest.TestCase):
    def setUp(self):
        self.sem, self.dig, self.sealed, self.eps = prepare(B.WORLDS["chain30"])
        self.e = self.eps[0]
        self.plan = self.sealed.canonical_bytes

    def go(self, plan=None, control=None, state=None, req=None, emitter="c"):
        plan = self.plan if plan is None else plan
        control = self.e["control"] if control is None else control
        state = self.e["state"] if state is None else state
        req = req or request(self.sem, self.dig, 1, plan, control, state)
        try:
            return X.run(req, plan, control, state, emitter)
        except X.Refused as r:
            return {"status": "refused", "reason": r.reason, "detail": r.detail}

    def test_FP_a_plan_edited_by_one_relay_does_not_rehash(self):
        plan = WC.deserialize_artifact(self.plan)
        plan["signal_edges"][3] = list(reversed(plan["signal_edges"][3]))     # one wire turned around; `sem` unchanged
        tampered = json.dumps(plan, sort_keys=True, separators=(",", ":")).encode()
        r = self.go(plan=tampered)
        self.assertEqual((r["status"], r["reason"]), ("refused", "plan-not-bound"))

    def test_FP_a_plan_that_claims_another_world(self):
        other_sem, _, other_sealed, _ = prepare(B.WORLDS["chain10"])
        req = request(self.sem, self.dig, 1, other_sealed.canonical_bytes, self.e["control"], self.e["state"])   # request names chain30, plan is chain10's
        r = self.go(plan=other_sealed.canonical_bytes, req=req)
        self.assertEqual((r["status"], r["reason"]), ("refused", "plan-not-bound"))

    def test_FS_a_state_that_does_not_decode(self):
        for bad in (self.e["state"][: len(self.e["state"]) // 2], self.eps[0]["state"].replace("λ", "", 1), "λa.a"):
            r = self.go(state=bad)
            self.assertEqual((r["status"], r["reason"]), ("refused", "input-decoding"), bad[:40])

    def test_FS_a_control_that_does_not_decode(self):
        r = self.go(control="λa.a")
        self.assertEqual((r["status"], r["reason"]), ("refused", "input-decoding"))

    def test_request_mismatch_on_any_of_the_three_hashes_and_the_kind(self):
        good = request(self.sem, self.dig, 1, self.plan, self.e["control"], self.e["state"])
        for field in ("plan_sha256", "control_sha256", "state_sha256"):
            req = json.loads(json.dumps(good)); req["params"][field] = "0" * 64
            r = self.go(req=req)
            self.assertEqual((r["status"], r["reason"], r["detail"]["field"]), ("refused", "request-mismatch", field))
        r = self.go(emitter="c2")           # a v1 request handed to the v2 executor
        self.assertEqual((r["status"], r["reason"], r["detail"]["field"]), ("refused", "request-mismatch", "kind"))

    def test_FB_a_stale_object_is_refused_before_the_call(self):
        r = self.go(); self.assertEqual(r["status"], "candidate")
        import emit_c
        so = emit_c.build(emit_c.emit_step_c(P.plan_view(self.sealed.canonical_plan)))[0]
        # the object is mapped in THIS process: never truncate it (SIGBUS); corrupt a copy and swap directory entries
        shutil.copy2(so, so + ".bak")
        try:
            with open(so + ".bak", "rb") as f:
                corrupt = f.read() + b"\0"
            with open(so + ".tmp", "wb") as f:
                f.write(corrupt)
            os.replace(so + ".tmp", so)                       # the object on disk is no longer the one recorded beside it
            r = self.go()
            self.assertEqual((r["status"], r["reason"]), ("refused", "stale-object"))
        finally:
            os.replace(so + ".bak", so)
        self.assertEqual(self.go()["status"], "candidate")

    def test_FW_a_world_outside_the_shapes_is_refused_by_the_emitter(self):
        src = B.PROFILE + "[pulser:p0](every 2){sig_out}\n[spinner:sp](w=64, n=31, rotor=quarter_turn_z, configurable){sig_in, socket}\n[orb:ob]{pose}\n\n[pulser:p0] --sig--> [spinner:sp]\n[spinner:sp] --socket--> [orb:ob]\n"
        prog, _ = SB._resolve_scenario(src, None)
        plan = P.artifact_to_compile_plan_v1(prog.sealed_artifact)
        sealed = WP.seal_compile_plan(plan, prog.sealed_artifact)
        view = P.plan_view(sealed.canonical_plan)
        state = X.render(view, F.init_state_v6(view))
        control = C.enc_config_bundle(view, {}, {})
        req = request(sealed.semantic_artifact_id, "scen-x", 1, sealed.canonical_bytes, control, state)
        r = self.go(plan=sealed.canonical_bytes, control=control, state=state, req=req)
        self.assertEqual((r["status"], r["reason"]), ("refused", "outside-shapes"))

    def test_FZ_the_input_bound(self):
        r = self.go(state=self.e["state"] + " " * 70000)
        self.assertEqual((r["status"], r["reason"]), ("refused", "input-limit"))

    def test_the_v2_executor_produces_the_same_bytes_under_its_own_identity(self):
        req = request(self.sem, self.dig, 1, self.plan, self.e["control"], self.e["state"], kind="compiled.c.step.v2")
        r = self.go(req=req, emitter="c2")
        self.assertEqual(r["status"], "candidate")
        self.assertEqual(r["nf_sha256"], CHAIN30_NF)
        self.assertTrue(r["backend_id"].startswith("cbknd2-") and r["flags"] == ["-O2"])


class GuardianArgv(unittest.TestCase):
    """The fixed-argv (bundle) form, and WHY it exists.

    Measured on the Super side, not assumed: `tools/hypersurface/node_guardian.rs` runs
    `Command::new(argv[0]).args(argv[1..4])` and states "Never accepts request-selected argv" -- so a guardian-owned
    child is handed exactly one free argument and one input path (which is why `reduce-file.mjs` takes one file).
    `COMPILED_EXECUTOR_PROPOSAL.md` §3 says the plan, the control and the state travel "beside the request" and does
    not say in how many files; on this executor host the answer is one. These cases pin that the bundle form is the
    SAME executor -- identical bytes out -- and that a bad bundle is refused before any step, like every other input.
    """

    def setUp(self):
        self.sem, self.dig, self.sealed, self.eps = prepare(B.WORLDS["chain30"])
        self.e = self.eps[0]
        self.plan = self.sealed.canonical_bytes
        self.req = request(self.sem, self.dig, 1, self.plan, self.e["control"], self.e["state"])

    def spawn(self, argv):
        return subprocess.run([sys.executable, os.path.join(HERE, "executor.py")] + argv, capture_output=True, text=True)

    def test_bundle_form_is_byte_identical_to_the_four_file_form(self):
        with tempfile.TemporaryDirectory() as d:
            paths = {k: os.path.join(d, k) for k in ("request", "plan", "control", "state")}
            open(paths["plan"], "wb").write(self.plan)
            open(paths["control"], "w").write(self.e["control"])
            open(paths["state"], "w").write(self.e["state"])
            json.dump(self.req, open(paths["request"], "w"))
            four = self.spawn(["--request", paths["request"], "--plan", paths["plan"],
                               "--control", paths["control"], "--state", paths["state"]])
            bpath = os.path.join(d, "bundle.json")
            open(bpath, "wb").write(X.bundle_bytes(self.req, self.plan, self.e["control"], self.e["state"]))
            one = self.spawn(["c", bpath])
        self.assertEqual((four.returncode, one.returncode), (0, 0), (four.stderr[-300:], one.stderr[-300:]))
        self.assertEqual(four.stdout, one.stdout, "the bundle form is a different executor")
        self.assertEqual(json.loads(one.stdout)["nf_sha256"], CHAIN30_NF)

    def test_the_child_takes_exactly_the_guardian_s_two_arguments(self):
        """`args(argv[1..4])` after `argv[0]` = the interpreter means the script sees two arguments and no more."""
        with tempfile.TemporaryDirectory() as d:
            bpath = os.path.join(d, "bundle.json")
            open(bpath, "wb").write(X.bundle_bytes(self.req, self.plan, self.e["control"], self.e["state"]))
            self.assertEqual(len(["c", bpath]), 2)
            self.assertEqual(self.spawn(["c", bpath]).returncode, 0)
            self.assertEqual(json.loads(self.spawn(["c2", bpath]).stdout)["reason"], "request-mismatch")

    def test_base64_carries_the_exact_bytes_the_hashes_are_over(self):
        """A plan whose bytes end in a newline must hash as those bytes on the far side of the transport."""
        plan = self.plan + b"\n"
        req = request(self.sem, self.dig, 1, plan, self.e["control"], self.e["state"])
        r, p, c, s = X.read_bundle_bytes(X.bundle_bytes(req, plan, self.e["control"], self.e["state"]))
        self.assertEqual(p, plan)
        self.assertEqual(sha(p), req["params"]["plan_sha256"])
        self.assertEqual((c, s), (self.e["control"], self.e["state"]))

    def test_a_malformed_bundle_is_refused_before_any_step(self):
        import base64 as B64
        good = json.loads(X.bundle_bytes(self.req, self.plan, self.e["control"], self.e["state"]).decode())
        cases = {
            "not json": b"{",
            "wrong version": json.dumps(dict(good, bundle=2)).encode(),
            "missing field": json.dumps({k: v for k, v in good.items() if k != "control_b64"}).encode(),
            "not base64": json.dumps(dict(good, state_b64="not base64!!")).encode(),
            "not utf-8": json.dumps(dict(good, control_b64=B64.b64encode(b"\xff\xfe").decode())).encode(),
            "no request": json.dumps(dict(good, request={})).encode(),
        }
        with tempfile.TemporaryDirectory() as d:
            for name, raw in cases.items():
                bpath = os.path.join(d, "b.json")
                open(bpath, "wb").write(raw)
                out = self.spawn(["c", bpath])
                self.assertEqual(out.returncode, 3, name)
                self.assertEqual(json.loads(out.stdout)["reason"], "bundle-malformed", name)

    def test_the_outcome_is_written_beside_the_bundle_so_a_refusal_keeps_its_reason(self):
        """`node_guardian.rs` forwards stdout only on exit 0, and a refusal exits 3 -- so without this file the
        owner sees `executor_failed` and never which check refused. Both a candidate and a refusal write it."""
        with tempfile.TemporaryDirectory() as d:
            bpath = os.path.join(d, "b.json")
            open(bpath, "wb").write(X.bundle_bytes(self.req, self.plan, self.e["control"], self.e["state"]))
            out = self.spawn(["c", bpath])
            self.assertEqual(out.returncode, 0)
            self.assertEqual(json.load(open(bpath + ".outcome")), json.loads(out.stdout))

            bad = dict(self.req)
            bad["params"] = dict(self.req["params"], plan_sha256="0" * 64)
            open(bpath, "wb").write(X.bundle_bytes(bad, self.plan, self.e["control"], self.e["state"]))
            os.remove(bpath + ".outcome")
            out = self.spawn(["c", bpath])
            self.assertEqual(out.returncode, 3)
            side = json.load(open(bpath + ".outcome"))
            self.assertEqual((side["status"], side["reason"], side["detail"]["field"]),
                             ("refused", "request-mismatch", "plan_sha256"))
            self.assertEqual(side, json.loads(out.stdout))

    def test_the_four_file_form_writes_no_sidecar(self):
        """Only the guardian's form needs it; the four-file form's caller already has stdout."""
        with tempfile.TemporaryDirectory() as d:
            paths = {k: os.path.join(d, k) for k in ("request", "plan", "control", "state")}
            open(paths["plan"], "wb").write(self.plan)
            open(paths["control"], "w").write(self.e["control"])
            open(paths["state"], "w").write(self.e["state"])
            json.dump(self.req, open(paths["request"], "w"))
            self.spawn(["--request", paths["request"], "--plan", paths["plan"],
                        "--control", paths["control"], "--state", paths["state"]])
            self.assertEqual([f for f in os.listdir(d) if f.endswith(".outcome")], [])

    def test_a_bundle_whose_hashes_do_not_match_is_still_request_mismatch(self):
        """The bundle changes the reading, not the checks: §3's re-hash of what the process actually read."""
        with tempfile.TemporaryDirectory() as d:
            bpath = os.path.join(d, "b.json")
            open(bpath, "wb").write(X.bundle_bytes(self.req, self.plan, self.e["control"], self.e["state"] + " "))
            out = self.spawn(["c", bpath])
            self.assertEqual(out.returncode, 3)
            body = json.loads(out.stdout)
            self.assertEqual((body["reason"], body["detail"]["field"]), ("request-mismatch", "state_sha256"))


if __name__ == "__main__":
    unittest.main()
