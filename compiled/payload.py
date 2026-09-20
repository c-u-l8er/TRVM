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

SINCE THE C PRINTER (2026-09-20) this checks TWO renderings against ic32's line, not one, because the cost it measured is
the reason the C printer exists: the Python path was 49-5,686 us against a step of 15-160 us, so a `trvm.reduce` receipt
cost 10-70x more to PRINT than to compute (`BENCHMARK_LANE.md` section B2-perf). `printer.CanonicalPrinter` walks the
compiled step's own int64 state vector straight to the same bytes in one pass. Three equalities are now asserted per
epoch and all three must hold for the run to pass: the C printer against ic32 (`identical`), the Python path against ic32
(`py_identical`, the old claim, unchanged), and the two paths against each other (`c_equals_py`). The columns are
`render_us` (C) beside `render_py_us` (Python), so one run carries its own before and after.

The `reducer` field says which calculus printed the line a world was checked against, by `battery.py`'s rule rather
than a second one of this module's (`reducer_for`); `ic32_s` is that reducer's per-epoch cost whichever it is, and
keeps its name so the column stays comparable with the records already written.
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
import printer as PR                   # noqa: E402
from ic_ref import show                # noqa: E402
C, O = F.C, F.O


def reducer_for(name):
    """WHICH calculus prints the line this world is checked against -- `battery.py`'s rule, not a second one.

    This used to be decided here, from the step term's size alone: over ic32's 16 MiB stdin buffer meant file mode,
    under it meant stdin. That is right for the two 33-lane worlds and WRONG for the 63-lane one, and the way it was
    wrong is the point. `spinner-w63-n31`'s step is 150-170 MB and its reduction overflows ic32's FIXED 16M-slot heap
    (`static uint32_t HEAPCAP = 1u<<24`, `runtime/c/ic32.c`, no env override) -- `FATAL: heap overflow`, exit 2, with
    nothing rendered. `battery.py` already knew that and gates every HUGE world onto ic_ref for exactly this reason
    (battery.py:301-305); this module classified by size and did not, so it sent w63 to a reducer that cannot take it.
    Two spellings of one rule, and the one that disagreed refused a world the other folds. There is now one spelling
    and it lives in `battery.py`.

    ic_ref is the reference implementation, so a line it prints is the calculus's line in exactly the sense this file
    claims -- it costs ~600 s per epoch on the 63-lane world, which is why that world is gated.
    """
    if name in getattr(B, "HUGE_WORLDS", {}):
        return "ic_ref"
    return "ic32-reparse" if name in B.WIDE_WORLDS else "ic32"


def calculus_line(step, ec, stt, mode):
    """The exact bytes the calculus prints for `((step ec) stt)`, LF stripped, by the reducer `mode` names."""
    term = f"(({step} {ec}) {stt})"
    if mode == "ic_ref":
        O.reset_runtime()
        return show(O.ref_reduce(term))
    if mode == "ic32":
        r = subprocess.run([O.IC32], input=term.encode(), capture_output=True, timeout=600)
        if r.returncode != 0:
            raise RuntimeError("ic32 rc=%d: %r" % (r.returncode, r.stderr[:200]))
        return r.stdout.decode().strip().splitlines()[0]
    os.makedirs(F.REPARSE_DIR, exist_ok=True)
    key = hashlib.sha256(step.encode()).hexdigest()
    sp = os.path.join(F.REPARSE_DIR, key + ".step.ic")
    if not os.path.exists(sp):
        # ATOMICALLY, as `fold.ic32_reparse` does: this file is 150+ MB, and a run interrupted while writing it would
        # otherwise leave a TRUNCATED step that every later run silently reuses -- `os.path.exists` cannot tell the
        # difference, and the symptom would be a parse error in a world that had been fine.
        tmp = sp + ".tmp.%d" % os.getpid()
        with open(tmp, "w") as f:
            f.write(step)
        os.replace(tmp, sp)
    ap = os.path.join(F.REPARSE_DIR, "payload-args.%d.txt" % os.getpid())
    with open(ap, "w") as f:
        f.write("1\n" + ec + "\n" + stt + "\n")
    r = subprocess.run([O.IC32, "-reparse", sp, ap], capture_output=True, timeout=600)
    if r.returncode != 0:
        # WITH ITS STDERR: rc=2 alone cost a re-run by hand to learn it said "FATAL: heap overflow". A refusal that
        # drops the reason is a refusal that has lost its name.
        raise RuntimeError("ic32 -reparse rc=%d: %r" % (r.returncode, r.stderr[:200]))
    return r.stdout.decode().strip().splitlines()[0]


def render_py(view, world):
    """The Python rendering this measurement exists to replace: state dict -> term text -> AST -> canonical text."""
    O.reset_runtime()
    return show(O.parse(C.enc_state_v6(view, world))).encode()


def one_world(name, src, epochs):
    sem, view, dig, script, world, claim, seams = F._prepare(src, None)
    cs = F.CompiledStep(view, sem)
    pr = PR.CanonicalPrinter(view)
    step, _ = C.compile_step_v6(view)
    mode = reducer_for(name)
    rows = []
    for e, (label, batch) in enumerate(script[:epochs]):
        ep = 1 + e
        claim, cfg_map, resets = F.FD.admit_step_sealed(claim, batch, ep, view, seams)
        ec, stt = C.enc_config_bundle(view, cfg_map, resets), C.enc_state_v6(view, world)
        # THE CALCULUS RUNS LAST, and that ordering is load-bearing rather than tidy. It used to run first, and on
        # `spinner-w63-n31` -- the one world whose reducer is IN-PROCESS ic_ref rather than an ic32 subprocess -- the
        # Python render timed immediately after a 547 s reduction read 901,299 us against 2,297 us measured on a clean
        # heap: a 392x confound, and it would have been quoted as a 9,408x speed-up for the C printer. A subprocess
        # frees its heap on exit, so the ic32 worlds were never affected and the records taken under the old order are
        # sound; ic_ref is not a subprocess. Both renderings now run before the reducer allocates anything.
        t0 = time.perf_counter()
        a_in, ctl = cs.encode(world), cs.control(cfg_map, resets)
        t_enc = time.perf_counter() - t0
        t0 = time.perf_counter()
        a_out = cs.step_raw(a_in, ctl)
        t_c = time.perf_counter() - t0
        t0 = time.perf_counter()
        world_c = cs.decode(a_out)
        t_dec = time.perf_counter() - t0
        # the rendering, both ways: the C printer over the step's own vector, and the Python path it replaces
        t0 = time.perf_counter()
        payload = pr.render(a_out)
        t_render = time.perf_counter() - t0
        t0 = time.perf_counter()
        payload_py = render_py(view, world_c)
        t_render_py = time.perf_counter() - t0
        t0 = time.perf_counter()
        line = calculus_line(step, ec, stt, mode).encode()
        t_ic = time.perf_counter() - t0
        rows.append({"epoch": ep, "identical": payload == line, "py_identical": payload_py == line,
                     "c_equals_py": payload == payload_py, "nf_bytes": len(line),
                     "nf_sha256": hashlib.sha256(line).hexdigest(),
                     "payload_sha256": hashlib.sha256(payload).hexdigest(),
                     "step_us": round((t_enc + t_c + t_dec) * 1e6, 2), "step_c_us": round(t_c * 1e6, 2),
                     "render_us": round(t_render * 1e6, 1), "render_py_us": round(t_render_py * 1e6, 1),
                     "ic32_s": round(t_ic, 4),
                     "decoded_state_equal": C.dec_state_v6(view, O.parse(line.decode())) == world_c})
        world = world_c                              # the compiled state is the chain; the calculus checks every epoch
    return {"world": name, "sem": sem, "backend_id": cs.backend_id, "printer_id": pr.printer_id,
            "term_bytes": len(step.encode()) + len(ec) + len(stt) + 6,
            "reducer": mode, "ic32_mode": {"ic32": "stdin", "ic32-reparse": "-reparse (file)"}.get(mode, "n/a (ic_ref)"),
            "epochs": len(rows),
            "all_identical": all(r["identical"] for r in rows), "all_states_equal": all(r["decoded_state_equal"] for r in rows),
            "all_py_identical": all(r["py_identical"] for r in rows), "all_c_equals_py": all(r["c_equals_py"] for r in rows),
            "nf_bytes_epoch1": rows[0]["nf_bytes"], "nf_sha256_epoch1": rows[0]["nf_sha256"],
            "render_us_p50": round(st.median(r["render_us"] for r in rows), 1),
            "render_py_us_p50": round(st.median(r["render_py_us"] for r in rows), 1),
            "step_us_p50": round(st.median(r["step_us"] for r in rows), 2),
            "step_c_us_p50": round(st.median(r["step_c_us"] for r in rows), 2),
            "ic32_s_p50": round(st.median(r["ic32_s"] for r in rows), 4), "rows": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=7)
    ap.add_argument("--out", default=os.path.join(HERE, "results-payload.json"))
    a = ap.parse_args()
    out = {"measured": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "loadavg": os.getloadavg(), "ic32_path": O.IC32,
           "printer_id": PR.printer_id(), "worlds": []}
    ok = True
    for name, src in B.WORLDS.items():
        w = one_world(name, src, a.epochs)
        ok &= w["all_identical"] and w["all_states_equal"] and w["all_py_identical"] and w["all_c_equals_py"]
        out["worlds"].append(w)
        print("%-20s %-16s epochs %d  nf %6d B  step %7.2f us  render C %7.1f us  py %8.1f us  %5.0fx  calc %8.4f s  %s" % (
            name, w["reducer"], w["epochs"], w["nf_bytes_epoch1"], w["step_us_p50"], w["render_us_p50"],
            w["render_py_us_p50"], w["render_py_us_p50"] / max(w["render_us_p50"], 1e-9), w["ic32_s_p50"],
            "IDENTICAL" if w["all_identical"] and w["all_py_identical"] and w["all_c_equals_py"] else "DIFFER"), flush=True)
    out["all_identical"] = ok
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
    print("PAYLOAD IDENTITY:", "EVERY EPOCH OF EVERY WORLD IDENTICAL" if ok else "A PAYLOAD DIFFERED", "-> wrote", a.out)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
