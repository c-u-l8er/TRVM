#!/usr/bin/env python3
"""batch_price.py -- what a multi-step `trvm.reduce` would pay PER STEP inside the executor, operation by operation.

    PYTHONDONTWRITEBYTECODE=1 python3 -B batch_price.py [--worlds a,b] [--steps 20000] [--reps 7]
                                                         [--out results-batch-price.json]

GPT's B6 review (§3): the batching arithmetic K / (F + K*s) took s from the bare step and so left out the work a
verified multi-step effect adds -- input decoding, canonicalisation, per-step digests, the receipt. This prices those
operations separately, in wall AND thread-CPU nanoseconds, on each world's own trajectory (the B6 control script, the
same seed), with the admitted C step (`emit_c`, compiled.c.step.v1 -- the kind Super's compiled route admits) and
the admitted printer (`print_state.c`, cprn-). `batch_price.c` does the timing in-process (no FFI in any loop); this
builds its input, checks the final state against the C step run from Python, and writes the record.

It measures OPERATIONS, not a batched route: nothing here is an effect, and no fixed per-effect cost is measured
here (that is test A's, through Super). The model that combines them is in `wek/b2/trvm/BATCH_CONTRACT.md`.
"""
import argparse
import json
import os
import struct
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import advance as A                     # noqa: E402
import battery as B                     # noqa: E402
import printer as PR                    # noqa: E402

WORLDS = "relay-only,chain30,chain120,golden-demo,two-spinners,spinner-w16-n8-fixed,mailbox-routes"


def build():
    src = os.path.join(HERE, "batch_price.c")
    with open(src, "rb") as f:
        key = A.sha(f.read())[:16]
    os.makedirs(A.CACHE, exist_ok=True)
    exe = os.path.join(A.CACHE, "batch_price-%s" % key)
    if not os.path.exists(exe):
        subprocess.run(["gcc", "-O2", "-Wno-deprecated-declarations", "-o", exe + ".tmp", src, "-ldl", "-lcrypto",
                        "-lblake3"], check=True)
        os.replace(exe + ".tmp", exe)
    return exe, key


def one(name, src, a, exe, tmp):
    w = A.World(name, src, a.steps, a.seed)
    cs = w.c1
    pr = PR.CanonicalPrinter(w.view)
    desc = list(pr._desc)
    widths = list(pr._widths)
    texts = []
    for c in w.ctls:
        t = pr.render_control((cs._Ctl)(*c) if c else cs._Ctl())
        assert list(pr.read_control(t)) == list(c), "control text round trip"
        texts.append(t)
    off = [0]
    for t in texts:
        off.append(off[-1] + len(t))
    blob = b"".join(texts)
    inp = os.path.join(tmp, "in-%s.bin" % name)
    with open(inp, "wb") as f:
        f.write(struct.pack("<8q", cs.width, w.cw, pr.nfields, len(desc), pr.nctrl, pr.norbs, a.steps, len(blob)))
        f.write(struct.pack("<%dq" % len(desc), *desc))
        f.write(struct.pack("<%dq" % len(widths), *widths))
        f.write(struct.pack("<%dq" % cs.width, *w.a0))
        f.write(struct.pack("<%dq" % (a.steps * w.cw), *[x for c in w.ctls for x in c]))
        f.write(struct.pack("<%dq" % len(off), *off))
        f.write(blob)
    # the final state from Python, the same step object, for the checksum
    st = cs._Arr(*w.a0)
    for c in w.ctls:
        st = cs.step_raw(st, cs._Ctl(*c) if c else cs._Ctl())
    h = 1469598103934665603
    for v in st:
        h ^= v & 0xFFFFFFFFFFFFFFFF
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    r = subprocess.run(["taskset", "-c", A.PIN_CPU, exe, cs.so_path, pr.so_path, inp, str(a.reps)],
                       capture_output=True, text=True, check=True)
    out = json.loads(r.stdout)
    out["final_state_agrees"] = out["final_fnv"] == "%016x" % h
    out.update({"world": name, "slots": cs.width, "backend_id": cs.backend_id, "printer_id": pr.printer_id})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds", default=WORLDS)
    ap.add_argument("--steps", type=int, default=20_000)
    ap.add_argument("--reps", type=int, default=7)
    ap.add_argument("--seed", type=int, default=20260925)
    ap.add_argument("--out", default=os.path.join(HERE, "results-batch-price.json"))
    a = ap.parse_args()
    exe, key = build()
    rec = {"benchmark": "B6 follow-up -- per-step price of a K-step trvm.reduce's operations (in-process C)",
           "measured": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "loadavg_start": os.getloadavg(), "pin_cpu": A.PIN_CPU,
           "steps": a.steps, "reps": a.reps, "seed": a.seed, "batch_price_c_sha256_16": key,
           "openssl": subprocess.run(["openssl", "version"], capture_output=True, text=True).stdout.strip(),
           "worlds": []}
    with tempfile.TemporaryDirectory(prefix="batch-price-") as tmp:
        for name in a.worlds.split(","):
            r = one(name, B.WORLDS[name], a, exe, tmp)
            rec["worlds"].append(r)
            o = r["ops"]
            print("%-22s slots %4d raw %5d B  text %7.0f B  ctl %6.0f B  %s | step %6.1f  sha %6.1f  chain %6.1f  b3 %6.1f  "
                  "render %7.1f  +sha %7.1f  rctl %7.1f  rstate %7.1f | vec+chain %7.1f  txt+chain %7.1f  txt+canon %8.1f ns (cpu)"
                  % (name, r["slots"], r["state_bytes_raw"], r["render_bytes_mean"], r["control_text_bytes_mean"],
                     "ok" if r["final_state_agrees"] else "FINAL STATE DISAGREES",
                     o["step"]["cpu_ns"], o["sha256_raw"]["cpu_ns"], o["chain_raw"]["cpu_ns"], o["blake3_raw"]["cpu_ns"],
                     o["render"]["cpu_ns"], o["render_sha256"]["cpu_ns"], o["read_control"]["cpu_ns"],
                     o["read_state"]["cpu_ns"], o["loop_vec_chain"]["cpu_ns"], o["loop_txt_chain"]["cpu_ns"],
                     o["loop_txt_canon"]["cpu_ns"]), flush=True)
    rec["loadavg_end"] = os.getloadavg()
    with open(a.out, "w") as f:
        json.dump(rec, f, indent=1)
    print("-> %s" % a.out)
    return 0 if all(r["final_state_agrees"] for r in rec["worlds"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
