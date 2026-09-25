#!/usr/bin/env python3
"""advance_chain.py -- the fixture for B6's THROUGH-SUPER rung: one world's verified trajectory, as the inputs a chain
of `trvm.reduce` effects needs and the digests each of them must produce.

    PYTHONDONTWRITEBYTECODE=1 python3 -B advance_chain.py --world chain30 --steps 2000 [--seed 20260925]
                                                          [--calculus 24] --out fixture.json

A chained effect k is performed with state = effect k-1's OUTPUT (the receipted normal form, never a value from
this file) and control = epoch k's control text below; its output must hash to `epochs[k].nf_sha256`. So this
file supplies what a caller cannot derive -- the plan, the initial state, the controls -- and what the caller
checks against, and nothing a step would read.

The expected digests come from a trajectory VERIFIED the way `advance.py` verifies: the C step (`emit_c`) folded
in-process, the packed C step (`emit_c2`) folded beside it and required equal at EVERY step, and `--calculus K`
sampled steps replayed through the interaction calculus (ic32 on `compiler.compile_step_v6`'s term) and required
equal. Each state is rendered by the C canonical printer -- the executor's own -- and the Python reference
renderer (`executor.render`) is checked against it on the first and last epoch.

The controls are generated as control vectors (`advance.control_script`, the same generator and seed), rendered by
`compiler.enc_config_bundle` -- the text the executor's control reader takes. Not through Forge's claim admission:
a world's claim state admits six operations in its life (`admit.MAX_EVENTS`).
"""
import argparse
import base64
import hashlib
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import advance as A                    # noqa: E402
import battery as B                    # noqa: E402
import emit_c2 as EC2                  # noqa: E402
import executor as X                   # noqa: E402
import wrl_plan as WP                  # noqa: E402
from fold import SB, P, C              # noqa: E402
import lower_e2a as LE                 # noqa: E402


def sha(b):
    return hashlib.sha256(b).hexdigest()


def build(world, steps, seed, calculus, emitter="c"):
    src = B.WORLDS[world]
    w = A.World(world, src, steps, seed)
    prog, _ = SB._resolve_scenario(src, None)
    sealed = WP.seal_compile_plan(P.artifact_to_compile_plan_v1(prog.sealed_artifact), prog.sealed_artifact)
    assert sealed.semantic_artifact_id == w.sem
    plan_bytes = sealed.canonical_bytes
    c1, c2 = w.c1, EC2.CompiledStep2(w.view, w.sem)
    pr = X.PR.CanonicalPrinter(w.view)
    a1, a2 = c1._Arr(*w.a0), c1._Arr(*w.a0)
    traj, epochs, controls = [], [], {}
    t0 = time.perf_counter()
    for k, ((cfg, rs), ctl) in enumerate(zip(w.script, w.ctls)):
        cv = c1._Ctl(*ctl)
        a1 = c1.step_raw(a1, cv)
        a2 = c2.step_raw(a2, cv)
        if list(a1) != list(a2):
            raise SystemExit("c1 and c2 diverge at step %d -- not a verified trajectory" % (k + 1))
        traj.append(list(a1))
        # Forge names binders from a process-global counter (`lower_e2a._VAR`), so the same control would be
        # different bytes every call. Start each control's names at 1: the text is closed and read alone, so the
        # executor sees the same bytes for the same control and the fixture is reproducible.
        LE._VAR[0] = 0
        text = C.enc_config_bundle(w.view, cfg, rs)
        csha = sha(text.encode())
        controls.setdefault(csha, text)
        nf = pr.render(a1)
        epochs.append({"epoch": k + 1, "control_sha256": csha, "nf_sha256": sha(nf), "nf_bytes": len(nf)})
    fold_s = time.perf_counter() - t0
    LE._VAR[0] = 10 ** 9                  # every name the calculus check mints from here on is fresh
    n = len(traj)
    idx = sorted({0, n - 1} | {round(i * (n - 1) / max(1, calculus - 1)) for i in range(calculus)}) if calculus else []
    cc = A.calculus_check(w, traj, idx)
    if not all(r["agree"] for r in cc):
        raise SystemExit("the calculus disagrees with the trajectory: %s" % [r for r in cc if not r["agree"]][:2])
    init_text = pr.render(c1._Arr(*w.a0)).decode()
    # the reference renderer, on the first and last states: the executor's printer is the one checked
    for k in (0, n - 1):
        ref = X.render(w.view, c1.decode(c1._Arr(*traj[k]))).encode()
        if sha(ref) != epochs[k]["nf_sha256"]:
            raise SystemExit("printer and reference renderer disagree at epoch %d" % (k + 1))
    if sha(X.render(w.view, w.world0).encode()) != sha(init_text.encode()):
        raise SystemExit("printer and reference renderer disagree on the initial state")
    biggest = max(len(t.encode()) for t in controls.values()) + max(e["nf_bytes"] for e in epochs)
    if biggest > X.INPUT_BYTES:
        raise SystemExit("control + state reach %d bytes, over the executor's %d" % (biggest, X.INPUT_BYTES))
    return {
        "fixture": "B6 advancing world -- through-Super chain", "world": world, "sem": w.sem,
        "kind": X.KINDS[emitter], "backend_id": c1.backend_id, "printer_id": pr.printer_id,
        "plan_b64": base64.b64encode(plan_bytes).decode(), "plan_sha256": sha(plan_bytes),
        "scenario_digest": "b6-script-" + w.script_sha256, "seed": seed, "steps": n,
        "initial_state_text": init_text, "initial_state_sha256": sha(init_text.encode()),
        "controls": controls, "epochs": epochs,
        "verification": {"c1_c2_every_step": True, "calculus_sampled": len(cc), "calculus_rows": cc,
                         "fold_s": round(fold_s, 3),
                         "rotor_writes": sum(len(c) for c, _ in w.script), "resets": sum(len(r) for _, r in w.script)},
        "max_input_bytes": biggest,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--steps", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260925)
    ap.add_argument("--calculus", type=int, default=24)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    fx = build(a.world, a.steps, a.seed, a.calculus)
    with open(a.out, "w") as f:
        json.dump(fx, f)
    v = fx["verification"]
    print(json.dumps({"world": fx["world"], "steps": fx["steps"], "sem": fx["sem"], "kind": fx["kind"],
                      "distinct_controls": len(fx["controls"]), "max_input_bytes": fx["max_input_bytes"],
                      "calculus": "%d/%d" % (sum(r["agree"] for r in v["calculus_rows"]), v["calculus_sampled"]),
                      "last_nf": fx["epochs"][-1]["nf_sha256"][:16], "out": a.out}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
