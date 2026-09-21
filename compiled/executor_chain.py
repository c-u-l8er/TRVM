#!/usr/bin/env python3
"""executor_chain.py -- the production loop, closed: the executor's own output is its next input, every world.

    PYTHONDONTWRITEBYTECODE=1 python3 -B executor_chain.py [--epochs N] [--emitter c|c2] [--resident]
                                                          [--out results-executor-chain.json]

WHAT THIS CHECKS THAT NOTHING ELSE DID. `payload.py` chains the COMPILED STATE and renders it at each epoch, so the
printer is checked against the calculus on every epoch of every world -- but the rendered bytes are never fed back
in. `executor_test.py` and `resident_test.py` run single jobs on four worlds. **Nobody ran the loop the witness
actually runs**, where epoch N's `output` becomes epoch N+1's `state`, so the C printer's bytes become the C
reader's input in production form and any disagreement between the two compounds instead of being seen once.

That loop is what this drives, over every world in the battery, for as many epochs as the world's demo scenario
has, with TWO independent trajectories compared at every step:

  * the FOLD's, which is `fold.compiled_fold`'s own chain over the state DICT -- no text, no executor; and
  * the EXECUTOR's, which starts from the rendered initial payload and thereafter reads only what it last wrote.

They must agree on every epoch's `nf_sha256`, and the executor's trajectory must not drift from the fold's even
once -- a divergence at epoch k would show as every epoch after k differing, which is why the FIRST divergence is
reported rather than a count.

It is affordable only because of the reader: a warm job is 0.17-0.36 ms (`RESIDENT.md` §4), so the whole battery is
a few hundred jobs and a couple of seconds of executor time. Through the one-shot kind at 82 ms it would have been
the sort of thing one runs once and then stops running, which is the sort of check that rots.

This is not the admission battery (`battery.py`) and does not replace it: the calculus is not in this loop at all.
It checks that the EXECUTOR PATH -- bundle, reader, step, printer -- is a fixed point of the fold it is supposed to
reproduce. `--resident` runs the same jobs through `ResidentCompiledHost` so the warm path is covered too.
"""
import argparse
import json
import os
import statistics as st
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (HERE, os.path.join(HERE, "..", "forge"), os.path.join(HERE, "..", "runtime", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.dont_write_bytecode = True
os.environ.setdefault("TRVM_BATTERY_HUGE", "1")          # the gated world is a chain like any other here

import battery as B                                      # noqa: E402
import executor as X                                     # noqa: E402
import fold as F                                         # noqa: E402
import wrl_plan as WP                                    # noqa: E402
from fold import SB, P, C                                # noqa: E402


def one_world(name, src, epochs, emitter, host):
    prog, scen = SB._resolve_scenario(src, None)
    sealed = WP.seal_compile_plan(P.artifact_to_compile_plan_v1(prog.sealed_artifact), prog.sealed_artifact)
    sem, view, scen_dig, script, world, claim, seams = F._prepare(src, None)
    cs = (F.CompiledStep if emitter == "c" else __import__("emit_c2").CompiledStep2)(view, sem)
    plan_bytes = sealed.canonical_bytes
    pr = X.PR.CanonicalPrinter(view)

    state_text = pr.render(cs.encode(world)).decode()     # the payload the witness would start from
    rows, lat, first_div = [], [], None
    for e, (_label, batch) in enumerate(script[:epochs]):
        ep = 1 + e
        claim, cfg_map, resets = F.FD.admit_step_sealed(claim, batch, ep, view, seams)
        control = C.enc_config_bundle(view, cfg_map, resets)
        req = {"er": "er-trvm.reduce", "rev": 1, "params": {
            "kind": X.KINDS[emitter], "sem": sem, "scenario_digest": scen_dig, "epoch": ep,
            "plan_sha256": X.sha(plan_bytes), "control_sha256": X.sha(control.encode()),
            "state_sha256": X.sha(state_text.encode()), "state_bytes": len(state_text.encode())}}
        bundle = X.bundle_bytes(req, plan_bytes, control, state_text)
        t0 = time.perf_counter()
        if host is not None:
            out = host.submit(bundle, job_id="%s-%d" % (name, ep))
        else:
            r, pb, ct, stt = X.read_bundle_bytes(bundle)
            out = X.run(r, pb, ct, stt, emitter)
        lat.append((time.perf_counter() - t0) * 1e3)
        if out.get("status") != "candidate":
            return {"world": name, "epochs": len(rows), "agree": False,
                    "refused": {"epoch": ep, "reason": out.get("reason"), "detail": out.get("detail")}, "rows": rows}
        # the fold's own trajectory, over the state dict, with no text anywhere in it
        world = cs.step(world, cfg_map, resets)
        want = pr.render(cs.encode(world))
        same = out["nf_sha256"] == X.sha(want)
        if not same and first_div is None:
            first_div = ep
        rows.append({"epoch": ep, "agree": same, "nf_sha256": out["nf_sha256"], "nf_bytes": out["nf_bytes"],
                     "reader": out.get("reader"), "state_bytes": len(state_text.encode())})
        state_text = out["output"]                        # THE CHAIN: it reads only what it last wrote
    return {"world": name, "sem": sem, "epochs": len(rows), "agree": all(r["agree"] for r in rows),
            "first_divergence": first_div, "backend_id": cs.backend_id, "printer_id": pr.printer_id,
            "readers": sorted({r["reader"] for r in rows}),
            "nf_sha256_last": rows[-1]["nf_sha256"] if rows else None,
            "job_ms_p50": round(st.median(lat), 3) if lat else None, "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=7)
    ap.add_argument("--emitter", default="c", choices=list(X.KINDS))
    ap.add_argument("--resident", action="store_true", help="drive the same jobs through the resident host's warm path")
    ap.add_argument("--out", default=os.path.join(HERE, "results-executor-chain.json"))
    a = ap.parse_args()
    host = None
    if a.resident:
        from resident import ResidentCompiledHost
        host = ResidentCompiledHost(pool=4, max_queue=32, emitter=a.emitter)
        host.ready()
    rec = {"measured": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "loadavg": os.getloadavg(), "emitter": a.emitter,
           "kind": X.KINDS[a.emitter], "path": "resident" if a.resident else "in-process one-shot",
           "reader_check": bool(os.environ.get("TRVM_READER_CHECK")), "worlds": []}
    ok = True
    try:
        for name, src in B.WORLDS.items():
            w = one_world(name, src, a.epochs, a.emitter, host)
            ok &= w["agree"]
            rec["worlds"].append(w)
            print("%-22s epochs %2d  %-9s reader %-12s job %7.3f ms  nf %s" % (
                name, w["epochs"], "AGREE" if w["agree"] else "DIVERGED@%s" % w.get("first_divergence"),
                ",".join(w.get("readers") or []) or "-", w.get("job_ms_p50") or 0,
                (w.get("nf_sha256_last") or "")[:12]), flush=True)
    finally:
        if host is not None:
            host.close()
    rec["all_agree"] = ok
    rec["epochs_total"] = sum(w["epochs"] for w in rec["worlds"])
    with open(a.out, "w") as f:
        json.dump(rec, f, indent=1)
    print("\nEXECUTOR CHAIN: %s (%d worlds, %d epochs, each epoch's input the last epoch's output) -> %s" % (
        "EVERY EPOCH OF EVERY WORLD AGREES WITH THE FOLD" if ok else "A TRAJECTORY DIVERGED",
        len(rec["worlds"]), rec["epochs_total"], a.out))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
