"""executor.py -- the compiled `trvm.reduce` executor PROCESS (T8's substrate side; `wek/b2/trvm/COMPILED_EXECUTOR_PROPOSAL.md`
§3): one epoch of one sealed WRL world, from the plan, the epoch's control and the previous normal form -- never from a
term -- to the calculus's canonical normal-form bytes, so `nf_sha256` and the film oracle are the witness's, unchanged.

    python3 executor.py --request R.json --plan PLAN.json --control CONTROL.ic --state STATE.ic [--emitter c|c2]

`stdout` is ONE JSON object: `{"status": "candidate", ...}` or `{"status": "refused", "reason": ...}`. Every refusal
happens BEFORE any step and names its reason; a candidate carries the re-hashes of the three inputs it actually read,
the identity of the code that ran (`backend_id`, `source_sha256`, `so_sha256`, `flags`), the rendered payload and its
digest. What this process does not do: mint authority, know about grants, receipts or the bridge; it is what the guardian
would run once per job (or a resident host would keep). The kind is `compiled.c.step.v1` (`emit_c`) or `.v2` (`emit_c2`).

Checks, in order (the falsifiers of §5):
  input-limit       plan > 1 MiB, or control + state > 64 KiB (the bridge's term bound, restated for the three inputs)
  request-mismatch  a sha256 in the request differs from the bytes handed to the process (plan, control, state)
  plan-not-bound    the plan does not re-hash to the SemanticArtifactID it claims, or claims one the request did not (F-P)
  outside-shapes    the emitter refuses the world (a lane width over 63; Bend's bound does not apply here) (F-W)
  stale-object      the cached `.so` for this source no longer has the sha it had when it was built (F-B)
  input-decoding    the previous payload or the control text does not parse/decode against this plan (F-S)
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "forge"), os.path.join(HERE, "..", "runtime", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

import wrl_canonical as WC            # noqa: E402
import wrl_plan as P                  # noqa: E402
import compiler as C                  # noqa: E402
import binlib as BL                   # noqa: E402
from lower_e2a import _spine, _dec_bool   # noqa: E402
from ic_ref import parse, show, reset_runtime, Lam, App, Var   # noqa: E402

PLAN_BYTES = 1 << 20
INPUT_BYTES = 65536
KINDS = {"c": "compiled.c.step.v1", "c2": "compiled.c.step.v2"}


def sha(b):
    return hashlib.sha256(b).hexdigest()


class Refused(Exception):
    def __init__(self, reason, detail=None):
        super().__init__(reason)
        self.reason, self.detail = reason, detail


# ------------------------------------------------------------------ decoding the control text against the plan
def dec_config_bundle(view, term):
    """Inverse of `compiler.enc_config_bundle`: TUP(rotor_bundle, fault_bundle) -> (cfg_map, resets)."""
    rb, fb = _spine(term, 2)
    orbs = list(view.orbs)
    ctrl = [view.controller_of(o) for o in orbs if view.controller_of(o)]
    cfg_map = {}
    for s, t in zip(ctrl, _spine(rb, len(ctrl)) if ctrl else []):
        # NoChange = λcnc.λcsr.cnc ; SetRotor(r) = λcnc.λcsr.(csr r)
        assert isinstance(t, Lam) and isinstance(t.bod, Lam), "rotor config shape"
        body = t.bod.bod
        if isinstance(body, Var) and body.nam == t.nam:
            cfg_map[s] = None
        elif isinstance(body, App) and isinstance(body.fun, Var) and body.fun.nam == t.bod.nam:
            cfg_map[s] = BL.dec_pose(body.arg, view.spinners[s][0])
        else:
            raise AssertionError("rotor config is neither NoChange nor SetRotor")
    resets = {o: True for o, t in zip(orbs, _spine(fb, len(orbs)) if orbs else []) if _dec_bool(t)}
    return cfg_map, resets


def render(view, world):
    reset_runtime()
    return show(parse(C.enc_state_v6(view, world)))


# ------------------------------------------------------------------ the process
def run(request, plan_bytes, control_text, state_text, emitter="c"):
    params = request["params"]
    if len(plan_bytes) > PLAN_BYTES or len(control_text.encode()) + len(state_text.encode()) > INPUT_BYTES:
        raise Refused("input-limit", {"plan_bytes": len(plan_bytes), "control_bytes": len(control_text.encode()), "state_bytes": len(state_text.encode())})
    hashes = {"plan_sha256": sha(plan_bytes), "control_sha256": sha(control_text.encode()), "state_sha256": sha(state_text.encode())}
    for k, v in hashes.items():
        if params.get(k) != v:
            raise Refused("request-mismatch", {"field": k, "request": params.get(k), "read": v})
    if params.get("kind") != KINDS[emitter]:
        raise Refused("request-mismatch", {"field": "kind", "request": params.get("kind"), "executor": KINDS[emitter]})
    try:
        plan = WC.deserialize_artifact(plan_bytes)
        sealed = P.seal_compile_plan(plan)           # D22: the plan must re-hash to the id it claims
    except Exception as e:
        raise Refused("plan-not-bound", {"error": "%s: %s" % (type(e).__name__, str(e)[:200])})
    if sealed.semantic_artifact_id != params.get("sem"):
        raise Refused("plan-not-bound", {"claims": sealed.semantic_artifact_id, "request": params.get("sem")})
    view = P.plan_view(sealed.canonical_plan)
    try:
        if emitter == "c":
            import emit_c as E
            cs = E.CompiledStep(view, sealed.semantic_artifact_id)
            flags = ["-O2"]
        else:
            import emit_c2 as E
            cs = E.CompiledStep2(view, sealed.semantic_artifact_id)
            flags = list(cs.flags)
    except ValueError as e:
        raise Refused("outside-shapes", {"error": str(e)[:200]})
    # F-B: the object's identity is recorded beside it when it is built; a later mismatch is a stale object
    with open(cs.so_path, "rb") as f:
        so_sha = sha(f.read())
    sidecar = cs.so_path + ".sha256"
    if os.path.exists(sidecar):
        with open(sidecar) as f:
            recorded = f.read().strip()
        if recorded != so_sha:
            raise Refused("stale-object", {"so": cs.so_path, "recorded": recorded, "found": so_sha})
    else:
        with open(sidecar, "w") as f:
            f.write(so_sha + "\n")
    try:
        reset_runtime()
        world = C.dec_state_v6(view, parse(state_text))
        cfg_map, resets = dec_config_bundle(view, parse(control_text))
    except Exception as e:
        raise Refused("input-decoding", {"error": "%s: %s" % (type(e).__name__, str(e)[:200])})
    world2 = cs.step(world, cfg_map, resets)
    nf = render(view, world2)
    nfb = nf.encode()
    return {
        "status": "candidate", "kind": KINDS[emitter],
        "sem": sealed.semantic_artifact_id, "scenario_digest": params.get("scenario_digest"), "epoch": params.get("epoch"),
        **hashes,
        "nf_sha256": sha(nfb), "nf_bytes": len(nfb), "output": nf,
        "backend_id": cs.backend_id, "source_sha256": cs.source_sha256, "so_sha256": so_sha, "flags": flags,
        "state_width": cs.width, "compile_plan_digest": sealed.compile_plan_digest,
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--request", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--control", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--emitter", default="c", choices=list(KINDS))
    a = ap.parse_args(argv)
    try:
        req = json.load(open(a.request))
        out = run(req, open(a.plan, "rb").read(), open(a.control, encoding="utf-8").read(), open(a.state, encoding="utf-8").read(), a.emitter)
    except Refused as r:
        out = {"status": "refused", "reason": r.reason, "detail": r.detail}
    sys.stdout.write(json.dumps(out, sort_keys=True) + "\n")
    return 0 if out["status"] == "candidate" else 3


if __name__ == "__main__":
    raise SystemExit(main())
