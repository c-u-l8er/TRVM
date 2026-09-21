"""executor.py -- the compiled `trvm.reduce` executor PROCESS (T8's substrate side; `wek/b2/trvm/COMPILED_EXECUTOR_PROPOSAL.md`
§3): one epoch of one sealed WRL world, from the plan, the epoch's control and the previous normal form -- never from a
term -- to the calculus's canonical normal-form bytes, so `nf_sha256` and the film oracle are the witness's, unchanged.

    python3 executor.py --request R.json --plan PLAN.json --control CONTROL.ic --state STATE.ic [--emitter c|c2]
    python3 executor.py <c|c2> BUNDLE.json                  # the FIXED-ARGV form, for a guardian-owned one-shot job

The second form exists because of a constraint measured on the Super side rather than assumed: the node guardian
(`super` `tools/hypersurface/node_guardian.rs`) runs `Command::new(argv[0]).args(argv[1..4])` and says of itself
"Never accepts request-selected argv" -- so a guardian-owned child gets exactly one free argument and one input path,
which is why `reduce-file.mjs` takes one file too. The four inputs therefore travel as ONE bundle, each base64'd so
that the transport cannot alter a byte of what is hashed:

    {"bundle": 1, "request": {...}, "plan_b64": "...", "control_b64": "...", "state_b64": "..."}

The checks, the refusals and the candidate are identical in both forms; only the reading differs. `bundle_bytes`
builds one (it is what the bridge's fixture preparation calls).

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
import base64
import hashlib
import json
import os
import sys
import time

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
import printer as PR                 # noqa: E402

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
    """The reference rendering, kept: state dict -> term text -> AST -> canonical text, all in Python.

    `printer.CanonicalPrinter` is what the process actually uses (one pass from the step's own state
    vector, 10-240x faster); this stays as the thing that path is checked against, by `payload.py` on
    every world of every epoch and by `executor_test.py` on the two witness terms.
    """
    reset_runtime()
    return show(parse(C.enc_state_v6(view, world)))


# ------------------------------------------------------------------ the process
def prepare(plan_bytes, emitter="c"):
    """Everything that depends ONLY on the plan bytes: the D22 seal, the view, the built step, the printer.

    Split out so a RESIDENT host can keep it across jobs (`resident.py`) without a second copy of anything. It is
    keyed by the sha256 of the exact plan bytes, so a cached seal is the seal OF THOSE BYTES and F-P is preserved
    on the warm path exactly as on the cold one: same bytes, same seal, same SemanticArtifactID to compare against
    the request's claim. The `.so` check is NOT in here -- it is a check on a file that can change under a live
    process, so it runs per job (`check_object`).
    """
    try:
        plan = WC.deserialize_artifact(plan_bytes)
        sealed = P.seal_compile_plan(plan)           # D22: the plan must re-hash to the id it claims
    except Exception as e:
        raise Refused("plan-not-bound", {"error": "%s: %s" % (type(e).__name__, str(e)[:200])})
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
    return {"sealed": sealed, "view": view, "cs": cs, "flags": flags, "pr": PR.CanonicalPrinter(view)}


def check_object(cs):
    """F-B, and it runs PER JOB even on a resident host's warm path.

    Residency must not mean checking the object once and trusting it forever: the `.so` is a file, and a file can be
    replaced under a process that has already mapped it. What this proves is what it always proved -- that the bytes
    on disk still hash to what was recorded beside them when they were built -- no more (the mapped pages are not
    re-read), and the one-shot executor makes exactly the same check, so the warm path is not weaker than the cold one.
    """
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
    return so_sha


def run(request, plan_bytes, control_text, state_text, emitter="c", cache=None, timing=None):
    """One job. `cache` (a dict) lets a resident host keep `prepare`'s result across jobs; `timing` (a dict) is
    filled with this job's phase costs in microseconds if one is passed. Neither changes a single check."""
    params = request["params"]
    if len(plan_bytes) > PLAN_BYTES or len(control_text.encode()) + len(state_text.encode()) > INPUT_BYTES:
        raise Refused("input-limit", {"plan_bytes": len(plan_bytes), "control_bytes": len(control_text.encode()), "state_bytes": len(state_text.encode())})
    hashes = {"plan_sha256": sha(plan_bytes), "control_sha256": sha(control_text.encode()), "state_sha256": sha(state_text.encode())}
    for k, v in hashes.items():
        if params.get(k) != v:
            raise Refused("request-mismatch", {"field": k, "request": params.get(k), "read": v})
    if params.get("kind") != KINDS[emitter]:
        raise Refused("request-mismatch", {"field": "kind", "request": params.get("kind"), "executor": KINDS[emitter]})
    t = timing if timing is not None else {}
    t0 = time.perf_counter()
    key = (hashes["plan_sha256"], emitter)
    p = cache.get(key) if cache is not None else None
    t["plan_cached"] = p is not None
    if p is None:
        p = prepare(plan_bytes, emitter)
        if cache is not None:
            cache[key] = p
    sealed, view, cs, flags, pr = p["sealed"], p["view"], p["cs"], p["flags"], p["pr"]
    t["prepare_us"] = round((time.perf_counter() - t0) * 1e6, 1)
    if sealed.semantic_artifact_id != params.get("sem"):
        raise Refused("plan-not-bound", {"claims": sealed.semantic_artifact_id, "request": params.get("sem")})
    t0 = time.perf_counter()
    so_sha = check_object(cs)
    t["object_check_us"] = round((time.perf_counter() - t0) * 1e6, 1)
    t0 = time.perf_counter()
    # The STATE comes in through the C reader (`printer.CanonicalPrinter.read`) -- `print_state.c`'s own walk run
    # backwards, so it cannot disagree with the printer. It was 86-93 % of a warm job on the resident host
    # (`RESIDENT.md` §4b): 805-3,422 us of `ic_ref.parse` plus 52-286 us of `dec_state_v6`, to undo bytes this
    # process had just written.
    #
    # THE ACCEPTANCE SET IS DELIBERATELY UNCHANGED. The C reader accepts a string iff the printer could have
    # written it for this layout, which is TIGHTER than `dec_state_v6(parse(...))`: a semantically equal term
    # spelled non-canonically parses in Python and is refused by the reader. In this protocol the state IS the
    # previous normal form and is canonical by construction, so the tighter rule would almost certainly do -- but
    # narrowing what an executor accepts is a contract change and is not one to make in passing. So a refusal from
    # the reader FALLS BACK to the Python path and the result says which ran (`reader`), because a fallback nobody
    # can see is a fallback that hides both a contract surprise and a defect in the reader.
    reader = "c"
    a_in = None
    try:
        a_in = pr.read(state_text)
    except ValueError:
        reader = "python"
    if a_in is None or os.environ.get("TRVM_READER_CHECK"):
        try:
            reset_runtime()
            py_in = cs.encode(C.dec_state_v6(view, parse(state_text)))
        except Exception as e:
            raise Refused("input-decoding", {"error": "%s: %s" % (type(e).__name__, str(e)[:200])})
        if a_in is None:
            a_in = py_in
        elif list(py_in) != list(a_in):
            # TRVM_READER_CHECK=1 runs both and compares. It is off by default because it costs the whole saving,
            # and on in the harness, where a disagreement must be a refusal rather than a quieter wrong answer.
            raise Refused("input-decoding", {"error": "reader disagreement", "c": list(a_in)[:8], "python": list(py_in)[:8]})
    # The CONTROL goes the same way, and it is the last Python conversion on this path. Its text is NOT canonical
    # -- it is `enc_config_bundle`'s raw output with Forge's own binder names -- so that walk binds names rather
    # than assuming them; `print_state.c` says why in its own comment. On the spinner worlds the control carries a
    # rotor pose per controlling spinner and `ic_ref.parse` alone was 312-638 us a job.
    c_ctl = None
    try:
        c_ctl = pr.read_control(control_text)
    except ValueError:
        reader = "python" if reader == "c" else reader
    if c_ctl is None or os.environ.get("TRVM_READER_CHECK"):
        try:
            reset_runtime()
            cfg_map, resets = dec_config_bundle(view, parse(control_text))
            py_ctl = cs.control(cfg_map, resets)
        except Exception as e:
            raise Refused("input-decoding", {"error": "%s: %s" % (type(e).__name__, str(e)[:200])})
        if c_ctl is None:
            c_ctl = py_ctl
        elif list(py_ctl) != list(c_ctl):
            raise Refused("input-decoding", {"error": "control reader disagreement",
                                             "c": list(c_ctl)[:8], "python": list(py_ctl)[:8]})
    t["decode_us"] = round((time.perf_counter() - t0) * 1e6, 1)
    t["reader"] = reader
    # The step's own state vector goes straight to the canonical bytes: no dict, no term text, no AST.
    # The printer is a SEPARATE object from the step (`printer.py`), so its identity is recorded beside
    # the step's rather than folded into it -- the receipt names both pieces of code that ran.
    t0 = time.perf_counter()
    a_out = cs.step_raw(a_in, c_ctl)
    t["step_us"] = round((time.perf_counter() - t0) * 1e6, 1)
    t0 = time.perf_counter()
    nfb = pr.render(a_out)
    t["render_us"] = round((time.perf_counter() - t0) * 1e6, 1)
    nf = nfb.decode()
    return {
        "status": "candidate", "kind": KINDS[emitter],
        "sem": sealed.semantic_artifact_id, "scenario_digest": params.get("scenario_digest"), "epoch": params.get("epoch"),
        **hashes,
        "nf_sha256": sha(nfb), "nf_bytes": len(nfb), "output": nf,
        "backend_id": cs.backend_id, "source_sha256": cs.source_sha256, "so_sha256": so_sha, "flags": flags,
        "printer_id": pr.printer_id, "printer_source_sha256": pr.source_sha256, "reader": reader,
        "state_width": cs.width, "compile_plan_digest": sealed.compile_plan_digest,
    }


def bundle_bytes(request, plan_bytes, control_text, state_text):
    """The one file a guardian-owned child is handed. Base64, not inline text: `plan_sha256` and the other two are
    taken over exact bytes, and a transport that can normalise a newline is a transport that can move a hash."""
    return json.dumps({
        "bundle": 1, "request": request,
        "plan_b64": base64.b64encode(plan_bytes).decode(),
        "control_b64": base64.b64encode(control_text.encode()).decode(),
        "state_b64": base64.b64encode(state_text.encode()).decode(),
    }, sort_keys=True).encode()


def read_bundle(path):
    try:
        raw = open(path, "rb").read()
    except Exception as e:
        raise Refused("bundle-malformed", {"error": type(e).__name__})
    return read_bundle_bytes(raw)


def read_bundle_bytes(raw):
    """Refuse a malformed bundle the way every other input is refused: before any step, with a reason."""
    try:
        b = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise Refused("bundle-malformed", {"error": type(e).__name__})
    if not isinstance(b, dict) or b.get("bundle") != 1:
        raise Refused("bundle-malformed", {"field": "bundle", "read": b.get("bundle") if isinstance(b, dict) else None})
    out = [b.get("request")]
    for k in ("plan_b64", "control_b64", "state_b64"):
        v = b.get(k)
        if not isinstance(v, str):
            raise Refused("bundle-malformed", {"field": k})
        try:
            out.append(base64.b64decode(v, validate=True))
        except Exception:
            raise Refused("bundle-malformed", {"field": k, "error": "base64"})
    if not isinstance(out[0], dict) or not isinstance(out[0].get("params"), dict):
        raise Refused("bundle-malformed", {"field": "request"})
    try:
        return out[0], out[1], out[2].decode("utf-8"), out[3].decode("utf-8")
    except UnicodeDecodeError:
        raise Refused("bundle-malformed", {"field": "control_b64/state_b64", "error": "utf-8"})


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    bundle = None
    try:
        if len(argv) == 2 and argv[0] in KINDS:                     # the guardian's fixed-argv form
            bundle = argv[1]
            req, plan, control, state = read_bundle(bundle)
            out = run(req, plan, control, state, argv[0])
        else:
            ap = argparse.ArgumentParser()
            ap.add_argument("--request", required=True)
            ap.add_argument("--plan", required=True)
            ap.add_argument("--control", required=True)
            ap.add_argument("--state", required=True)
            ap.add_argument("--emitter", default="c", choices=list(KINDS))
            a = ap.parse_args(argv)
            req = json.load(open(a.request))
            out = run(req, open(a.plan, "rb").read(), open(a.control, encoding="utf-8").read(), open(a.state, encoding="utf-8").read(), a.emitter)
    except Refused as r:
        out = {"status": "refused", "reason": r.reason, "detail": r.detail}
    body = json.dumps(out, sort_keys=True)
    if bundle is not None:
        # The guardian forwards this process's stdout ONLY when it exits 0 (`node_guardian.rs`: a non-zero child is
        # status 67 and no bytes). A refusal is a non-zero exit by design -- and a refusal whose REASON is lost is a
        # refusal the harness cannot tell from any other, so the outcome is also written beside the bundle, in the
        # scratch directory the owner made and removes. Best effort: an unwritable scratch must not change the verdict.
        try:
            with open(bundle + ".outcome", "w") as f:
                f.write(body + "\n")
        except OSError:
            pass
    sys.stdout.write(body + "\n")
    return 0 if out["status"] == "candidate" else 3


if __name__ == "__main__":
    raise SystemExit(main())
