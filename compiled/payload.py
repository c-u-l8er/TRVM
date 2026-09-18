#!/usr/bin/env python3
"""payload.py -- the compiled step's state rendered as the calculus's normal-form PAYLOAD, checked byte for byte.

    PYTHONDONTWRITEBYTECODE=1 python3 -B payload.py [--epochs N] [--out results-payload.json]

The vertical witness (`wek/b2/trvm/`) receipts a `trvm.reduce` effect by the sha256 of the exact bytes the checked host
printed for the epoch's normal form, and the harness's reference gate compares that digest to the calculus's. For the
compiled step to stand behind the SAME gate as a second executor kind, its result must be those bytes, not "a state that
decodes the same". This measures whether it can be: for every world's demo scenario, epoch by epoch, the compiled state is
re-encoded with Forge's own codec (`compiler.enc_state_v6`) and printed by the reference printer (`ic_ref.show` over
`ic_ref.parse`, the canonical `λa.λb...` renaming), and the string is compared to the line ic32 prints for the same epoch's
term `((step cfg) state)`. Also measured: the cost of that rendering, which is what the compiled executor kind would pay on
top of its microsecond step. Worlds whose epoch term exceeds ic32's 16 MiB stdin buffer are rendered through the same
`-reparse` file mode the battery uses.
"""
import argparse
import hashlib
import json
import os
import statistics as st
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import fold as F                       # noqa: E402
import battery as B                    # noqa: E402
from ic_ref import show                # noqa: E402
C, O = F.C, F.O


def ic32_line(step, ec, stt, wide):
    """The exact bytes ic32 prints for `((step ec) stt)` (LF stripped): stdin for terms under 16 MiB, file mode above."""
    if not wide:
        term = f"(({step} {ec}) {stt})"
        r = subprocess.run([O.IC32], input=term.encode(), capture_output=True, timeout=600)
        if r.returncode != 0:
            raise RuntimeError("ic32 rc=%d" % r.returncode)
        return r.stdout.decode().strip().splitlines()[0]
    os.makedirs(F.REPARSE_DIR, exist_ok=True)
    key = hashlib.sha256(step.encode()).hexdigest()
    sp = os.path.join(F.REPARSE_DIR, key + ".step.ic")
    if not os.path.exists(sp):
        with open(sp, "w") as f:
            f.write(step)
    ap = os.path.join(F.REPARSE_DIR, "payload-args.%d.txt" % os.getpid())
    with open(ap, "w") as f:
        f.write("1\n" + ec + "\n" + stt + "\n")
    r = subprocess.run([O.IC32, "-reparse", sp, ap], capture_output=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError("ic32 -reparse rc=%d" % r.returncode)
    return r.stdout.decode().strip().splitlines()[0]


def render(view, world):
    """The compiled executor's payload: Forge's encoding of the state, printed canonically."""
    O.reset_runtime()
    return show(O.parse(C.enc_state_v6(view, world)))


def one_world(name, src, epochs):
    sem, view, dig, script, world, claim, seams = F._prepare(src, None)
    cs = F.CompiledStep(view, sem)
    step, _ = C.compile_step_v6(view)
    wide = len(step.encode()) > (1 << 24) - (1 << 16)
    rows = []
    for e, (label, batch) in enumerate(script[:epochs]):
        ep = 1 + e
        claim, cfg_map, resets = F.FD.admit_step_sealed(claim, batch, ep, view, seams)
        ec, stt = C.enc_config_bundle(view, cfg_map, resets), C.enc_state_v6(view, world)
        t0 = time.perf_counter()
        line = ic32_line(step, ec, stt, wide)
        t_ic = time.perf_counter() - t0
        t0 = time.perf_counter()
        world_c = cs.step(world, cfg_map, resets)
        t_step = time.perf_counter() - t0
        t0 = time.perf_counter()
        payload = render(view, world_c)
        t_render = time.perf_counter() - t0
        rows.append({"epoch": ep, "identical": payload == line, "nf_bytes": len(line.encode()),
                     "nf_sha256": hashlib.sha256(line.encode()).hexdigest(),
                     "payload_sha256": hashlib.sha256(payload.encode()).hexdigest(),
                     "step_us": round(t_step * 1e6, 2), "render_us": round(t_render * 1e6, 1), "ic32_s": round(t_ic, 4),
                     "decoded_state_equal": C.dec_state_v6(view, O.parse(line)) == world_c})
        world = world_c                              # the compiled state is the chain; the calculus checks every epoch
    return {"world": name, "sem": sem, "backend_id": cs.backend_id, "term_bytes": len(step.encode()) + len(ec) + len(stt) + 6,
            "ic32_mode": "-reparse (file)" if wide else "stdin", "epochs": len(rows),
            "all_identical": all(r["identical"] for r in rows), "all_states_equal": all(r["decoded_state_equal"] for r in rows),
            "nf_bytes_epoch1": rows[0]["nf_bytes"], "nf_sha256_epoch1": rows[0]["nf_sha256"],
            "render_us_p50": round(st.median(r["render_us"] for r in rows), 1), "step_us_p50": round(st.median(r["step_us"] for r in rows), 2),
            "ic32_s_p50": round(st.median(r["ic32_s"] for r in rows), 4), "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=7)
    ap.add_argument("--out", default=os.path.join(HERE, "results-payload.json"))
    a = ap.parse_args()
    out = {"measured": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "loadavg": os.getloadavg(), "ic32_path": O.IC32, "worlds": []}
    ok = True
    for name, src in B.WORLDS.items():
        w = one_world(name, src, a.epochs)
        ok &= w["all_identical"] and w["all_states_equal"]
        out["worlds"].append(w)
        print("%-20s %-16s epochs %d  nf %6d B  step %7.2f us  render %8.1f us  ic32 %8.4f s  %s" % (
            name, w["ic32_mode"], w["epochs"], w["nf_bytes_epoch1"], w["step_us_p50"], w["render_us_p50"], w["ic32_s_p50"],
            "IDENTICAL" if w["all_identical"] else "DIFFER"), flush=True)
    out["all_identical"] = ok
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
    print("PAYLOAD IDENTITY:", "EVERY EPOCH OF EVERY WORLD IDENTICAL" if ok else "A PAYLOAD DIFFERED", "-> wrote", a.out)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
