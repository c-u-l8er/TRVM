"""make_bundle.py -- one compiled-kind job bundle for a battery world, for a caller outside Python.

The Super side (`HyperSurface.CompiledExecutor`) hands its child ONE file; this is what produces it, so an Elixir
test builds its fixture from the world's CURRENT sealed plan rather than from a committed file that can go stale
against the emitter. It is `executor_test.prepare/2` with a CLI, and it computes nothing the executor will not
re-hash for itself.

    python3 make_bundle.py --world chain30 --epoch 1 [--emitter c|c2] [--out bundle.json]
    python3 make_bundle.py --list

stdout (or `--out`) is the bundle. `--meta` prints, on stderr, a JSON line naming the world, the kind, the three
input digests and the normal-form digest the fold produces for that epoch -- what a caller asserts against.
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import fold as F                                   # noqa: E402
import battery as B                                # noqa: E402
import wrl_plan as WP                              # noqa: E402
import compiler as C                               # noqa: E402
import executor as X                               # noqa: E402
from fold import SB, P                             # noqa: E402


def build(world, epoch, emitter="c", scenario=None):
    src = B.WORLDS[world]
    prog, _ = SB._resolve_scenario(src, scenario)
    plan = P.artifact_to_compile_plan_v1(prog.sealed_artifact)
    sealed = WP.seal_compile_plan(plan, prog.sealed_artifact)
    sem, view, scen_dig, script, w, claim, seams = F._prepare(src, scenario)
    step = (F.CompiledStep if emitter == "c" else __import__("emit_c2").CompiledStep2)(view, sem)
    prev = X.render(view, w)
    for e, (_label, batch) in enumerate(script):
        claim, cfg_map, resets = F.FD.admit_step_sealed(claim, batch, 1 + e, view, seams)
        control = C.enc_config_bundle(view, cfg_map, resets)
        if 1 + e == epoch:
            req = {"er": "er-trvm.reduce", "rev": 1, "params": {
                "kind": X.KINDS[emitter], "sem": sem, "scenario_digest": scen_dig, "epoch": epoch,
                "plan_sha256": X.sha(sealed.canonical_bytes),
                "control_sha256": X.sha(control.encode()),
                "state_sha256": X.sha(prev.encode()),
                "state_bytes": len(prev.encode())}}
            nf = X.render(view, step.step(w, cfg_map, resets))
            return X.bundle_bytes(req, sealed.canonical_bytes, control, prev), {
                "world": world, "epoch": epoch, "kind": X.KINDS[emitter], "sem": sem,
                "scenario_digest": scen_dig, "nf_sha256": X.sha(nf.encode()), "nf_bytes": len(nf.encode()),
                "backend_id": step.backend_id, **req["params"]}
        w = step.step(w, cfg_map, resets)
        prev = X.render(view, w)
    raise SystemExit("world %s has no epoch %d (it has %d)" % (world, epoch, len(script)))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--world")
    ap.add_argument("--epoch", type=int, default=1)
    ap.add_argument("--emitter", default="c", choices=list(X.KINDS))
    ap.add_argument("--scenario", default=None)
    ap.add_argument("--out")
    ap.add_argument("--meta", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    if a.list:
        print("\n".join(sorted(B.WORLDS)))
        return 0
    if not a.world:
        ap.error("--world is required (or --list)")
    raw, meta = build(a.world, a.epoch, a.emitter, a.scenario)
    if a.out:
        with open(a.out, "wb") as f:
            f.write(raw)
    else:
        sys.stdout.buffer.write(raw)
    if a.meta:
        sys.stderr.write(json.dumps(meta, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
