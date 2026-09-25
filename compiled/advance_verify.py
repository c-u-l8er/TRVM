#!/usr/bin/env python3
"""advance_verify.py -- B6's verification, strengthened: EVERY state of EVERY backend's trajectory compared, streamed,
plus a transient-error control that endpoint-only checking passes and the full comparison catches.

    PYTHONDONTWRITEBYTECODE=1 python3 -B advance_verify.py [--worlds a,b] [--steps 100000]
                                                           [--window-words 2000000] [--out results-advance-verify.json]

WHY. `advance.py` checked c1 and c2 at every step to N, but the two Bend backends only over a width-bounded prefix
(a Bend String is a cons list of chars; 100,000 states of 485 words cannot be printed in one run) and at every timed
endpoint. GPT's B6 review: a wrong intermediate Bend transition that later reconverges is not excluded by that. This
closes it without keeping millions of words in memory and without re-running the timing campaign:

  * REFERENCE -- c1 emits every state to N; each state is reduced to a per-step sha256 of its C slot vector rendered
    as decimal words (N x 32 bytes held, never the states). c2 is unpacked and compared step by step.
  * BEND, WINDOWED -- the Bend program is the admitted step text (byte for byte, up to `def reps(`) with a
    verification tail (`VERIFY_TAIL`) that advances the world from ITS OWN initial state through the first `hi`
    epochs and prints only the states after steps lo+1..hi. Windows [lo, hi) of `window_words / width` steps tile
    1..N. Every run recomputes the trajectory from step 0 -- no window starts from a C state -- so what is compared is
    Bend's own continuous trajectory, every state of it. Cost is O(N^2 / W) Bend steps; the widest world needs 25
    windows.
  * THE TRANSIENT-ERROR CONTROL -- a reconverging fault: at step T the state is replaced by one that differs in one
    slot, chosen (by search with the C step, in-process) so the world's own dynamics overwrite it within a few steps.
    The same verification binary is run with the fault injected (`TRVM_FA`, `TRVM_FS`). REQUIRED: the endpoint check
    (the final state at N against the reference) PASSES, and the full comparison FAILS at exactly step T.
    If the endpoint check caught it, the control would not separate the two contracts, and it says so.

The timed programs are NOT these: the timing tail (`advance.BEND_TAIL`) is unchanged, so `results-advance.json`'s
timings stand. What ties them: the step text is byte-identical in both programs (asserted), and every timed run's
final state at every size equals the verified trajectory (advance.py). The calculus check is not repeated here; it
stays SAMPLED (24 steps per world, advance.py) and is reported as sampled.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import advance as A                     # noqa: E402  (World, Backend, the drivers, the timing tail)
import battery as B                     # noqa: E402
import emit_bend as EB                  # noqa: E402

VERIFY_DEFS = '''def put(b: Bool, nx: List<&2, Nat>, fs: List<&2, Nat>) -> List<&2, Nat>:
  match b:
    case True{}:
      fs
    case False{}:
      nx

def keep(b: Bool, nx: List<&2, Nat>, rest: List<&2, String>) -> List<&2, String>:
  match b:
    case True{}:
      row(nx) <> rest
    case False{}:
      rest

def win(cts: List<&2, List<&2, Nat>>, st: List<&2, Nat>, +k: Nat, +lo: Nat, +fa: Nat, +fs: List<&2, Nat>) -> List<&2, String>:
  match cts:
    case Nil{}:
      Nil{}
    case Con{c, rest}:
      +k1 = (k + 1n : Nat)
      +nx = put(Nat.is_eq(k1, fa), step(st, c), fs)
      keep(Nat.is_gt(k1, lo), nx, win(rest, nx, k1, lo, fa, fs))

def main() -> IO(Unit):
  do IO<Unit>:
    st : String <- IO.try(String, IO.get_env("TRVM_ST"))
    path : String <- IO.try(String, IO.get_env("TRVM_SCRIPT"))
    lo : String <- IO.try(String, IO.get_env("TRVM_LO"))
    fa : String <- IO.try(String, IO.get_env("TRVM_FA"))
    fs : String <- IO.try(String, IO.get_env("TRVM_FS"))
    txt : String <- read_all(path)
    IO.print(String.join(win(lines(String.lines(txt)), nats(String.split(st, ' ')), 0n, nat_of(lo), nat_of(fa), nats(String.split(fs, ' '))), "\\n"))
'''
# the timing tail's helpers (shows/row/lines/adv/trail/.../read_all) kept byte for byte; only `main` is replaced
VERIFY_TAIL = A.BEND_TAIL[:A.BEND_TAIL.index("def main()")] + VERIFY_DEFS


def sha(b):
    return hashlib.sha256(b).hexdigest()


def dig(vec):
    """The per-step digest: sha256 of the C slot vector as decimal words, one space apart."""
    return hashlib.sha256(" ".join(str(int(x)) for x in vec).encode()).digest()


def launch(argv, env, tmp, pin=True):
    """One child under advance_launch.c (rusage exact); stdout to a file, streamed back line by line."""
    if pin:
        argv = ["taskset", "-c", A.PIN_CPU] + argv
    outp, report = os.path.join(tmp, "v-stdout"), os.path.join(tmp, "v-rusage.json")
    with open(outp, "wb") as so, open(os.path.join(tmp, "v-stderr"), "wb") as se:
        rc = subprocess.run([A.LAUNCH, report] + argv, stdout=so, stderr=se, env=env).returncode
    with open(report) as f:
        ru = json.load(f)
    if rc != 0:
        with open(os.path.join(tmp, "v-stderr"), "rb") as f:
            raise RuntimeError("rc=%d: %s" % (rc, f.read()[-400:]))
    return outp, ru


def script_file(w, hi, tmp):
    p = os.path.join(tmp, "vscript-%s-%d.txt" % (w.name, hi))          # keyed by world AND length (trap 4)
    if not os.path.exists(p):
        with open(p, "w") as f:
            f.write("\n".join(" ".join(str(x) for x in c) if c else "0" for c in w.ctls[:hi]))
    return p


def rows_of(path, width):
    with open(path, "rb") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = [int(x) for x in line.split()]
            if len(r) != width:
                raise RuntimeError("a state of %d words, expected %d" % (len(r), width))
            yield r


def c_all(be, w, n, tmp):
    env = dict(os.environ, TRVM_ST=" ".join(str(int(x)) for x in be.pack(w.a0)), TRVM_SCRIPT=script_file(w, n, tmp),
               TRVM_MODE="1")
    outp, ru = launch([A.DRIVER, be.obj], env, tmp)
    return [dig(be.unpack(r)) for r in rows_of(outp, be.width)], ru


class BendVerify:
    def __init__(self, be):
        self.be = be
        src = be.cs.source
        cut = src.index("def reps(")
        self.source = src[:cut] + VERIFY_TAIL
        assert self.source[:cut] == be.driver_source[:cut] == src[:cut], "the step text must be the admitted one"
        self.bin, self.code_sha256, self.built_now = EB.build(self.source)

    def window(self, w, lo, hi, tmp, fault=None):
        """States after steps lo+1..hi of Bend's own trajectory from the world's initial state (1-based steps)."""
        be = self.be
        fa, fs = (0, [0]) if fault is None else (fault[0], be.pack(fault[1]))
        env = dict(os.environ, TRVM_ST=" ".join(str(int(x)) for x in be.pack(w.a0)), TRVM_SCRIPT=script_file(w, hi, tmp),
                   TRVM_LO=str(lo), TRVM_FA=str(fa), TRVM_FS=" ".join(str(int(x)) for x in fs), BEND_NO_TELEMETRY="1")
        outp, ru = launch([self.bin], env, tmp)
        return [dig(be.unpack(r)) for r in rows_of(outp, be.width)], ru


def windows(n, width, words):
    step = max(1, min(n, words // max(1, width)))
    return [(lo, min(n, lo + step)) for lo in range(0, n, step)]


def full_check(bv, w, ref, n, words, tmp, fault=None, stop_at_first=False):
    first, checked, cpu, wall, runs, peak = None, 0, 0.0, 0.0, 0, 0
    for lo, hi in windows(n, bv.be.width, words):
        got, ru = bv.window(w, lo, hi, tmp, fault)
        runs += 1
        cpu += ru["cpu_user_s"] + ru["cpu_sys_s"]
        wall += ru["wall_s"]
        peak = max(peak, ru["maxrss_kb"])
        if len(got) != hi - lo:
            first = first or (lo + len(got) + 1)
            break
        for i, d in enumerate(got):
            if d != ref[lo + i] and first is None:
                first = lo + i + 1
        checked += len(got)
        if first is not None and stop_at_first:
            break
    return {"first_divergence": first, "every_state_checked_to_step": checked, "windows": runs,
            "cpu_s": round(cpu, 3), "wall_s": round(wall, 3), "maxrss_mb": round(peak / 1024, 1)}


def find_reconverging_fault(w, t, horizon=64):
    """A one-slot perturbation of the state after step t that the C step's own dynamics erase within `horizon` steps.
    Candidate values for a slot are values that slot takes elsewhere in the trajectory (so representable in every
    backend's packing), then 0/1. Returns (step t, faulty C vector, steps until reconverged, slot) or None."""
    cs = w.c1
    arr, ctl = cs._Arr, cs._Ctl
    traj = []
    a = arr(*w.a0)
    for c in w.ctls[: t + horizon + 1]:
        a = cs.step_raw(a, ctl(*c) if c else ctl())
        traj.append(list(a))
    ref_t = traj[t - 1]                                                   # the state after step t (1-based)
    seen = [sorted({traj[k][j] for k in range(0, len(traj), max(1, len(traj) // 64))} | {0, 1})
            for j in range(cs.width)]
    for j in range(cs.width):
        for v in seen[j]:
            if v == ref_t[j]:
                continue
            bad = list(ref_t)
            bad[j] = v
            b = arr(*bad)
            for d in range(1, horizon + 1):
                c = w.ctls[t + d - 1]
                b = cs.step_raw(b, ctl(*c) if c else ctl())
                if list(b) == traj[t + d - 1]:
                    return t, bad, d, j, ref_t[j]
    return None


def one_world(name, src, a, tmp):
    n = a.steps
    w = A.World(name, src, n, a.seed)
    rec = {"world": name, "slots": w.c1.width, "steps": n, "script_sha256": w.script_sha256, "backends": {}}
    t0 = time.time()
    bes = {k: A.Backend(k, w) for k in A.BACKENDS}
    ref, ru = c_all(bes["c1"], w, n, tmp)
    rec["reference"] = {"backend": "c1", "states": len(ref), "cpu_s": round(ru["cpu_user_s"] + ru["cpu_sys_s"], 3),
                        "trajectory_sha256": sha(b"".join(ref))}
    assert len(ref) == n
    got2, ru2 = c_all(bes["c2"], w, n, tmp)
    first2 = next((i + 1 for i, (x, y) in enumerate(zip(got2, ref)) if x != y), None)
    rec["backends"]["c2"] = {"first_divergence": first2 if first2 or len(got2) == n else len(got2) + 1,
                             "every_state_checked_to_step": len(got2), "windows": 1}
    ok = rec["backends"]["c2"]["first_divergence"] is None
    fault = find_reconverging_fault(w, n // 2)
    rec["fault"] = None if fault is None else {"after_step": fault[0], "slot": fault[3], "reconverges_after_steps": fault[2],
                                               "reference_value": fault[4], "faulty_value": fault[1][fault[3]]}
    for kind in ("bend1", "bend2"):
        bv = BendVerify(bes[kind])
        r = full_check(bv, w, ref, n, a.window_words, tmp)
        r.update({"verify_code_sha256": bv.code_sha256, "admitted_source_sha256": bes[kind].admitted_source_sha256,
                  "timed_code_sha256": bes[kind].code_sha256})
        ok &= r["first_divergence"] is None and r["every_state_checked_to_step"] == n
        if fault is not None:
            t, bad, d, j, _v = fault
            ws = windows(n, bv.be.width, a.window_words)
            wt = next(x for x in ws if x[0] < t <= x[1])
            got_t, _ = bv.window(w, wt[0], wt[1], tmp, (t, bad))               # the window holding step t
            lo_n, hi_n = ws[-1]
            got_n, _ = bv.window(w, lo_n, hi_n, tmp, (t, bad))                 # the window holding step n
            endpoint_passes = got_n[-1] == ref[n - 1]
            first = next((wt[0] + i + 1 for i, x in enumerate(got_t) if x != ref[wt[0] + i]), None)
            r["transient_fault_control"] = {
                "fault_after_step": t, "slot": j, "reconverges_after_steps": d,
                "endpoint_check": "PASS" if endpoint_passes else "FAIL",
                "full_check_first_divergence": first,
                "separates_the_contracts": endpoint_passes and first == t}
            ok &= r["transient_fault_control"]["separates_the_contracts"]
        rec["backends"][kind] = r
    rec["all_states_agree"] = all(rec["backends"][k]["first_divergence"] is None for k in ("c2", "bend1", "bend2"))
    rec["ok"] = ok
    rec["seconds"] = round(time.time() - t0, 1)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds", default=None)
    ap.add_argument("--steps", type=int, default=100_000)
    ap.add_argument("--seed", type=int, default=20260925)       # advance.py's default: the SAME scripts it timed
    ap.add_argument("--window-words", type=int, default=2_000_000)
    ap.add_argument("--out", default=os.path.join(HERE, "results-advance-verify.json"))
    a = ap.parse_args()
    worlds = {k: v for k, v in B.WORLDS.items() if k not in B.WIDE_WORLDS}
    if a.worlds:
        worlds = {k: B.WORLDS[k] for k in a.worlds.split(",")}
    A.DRIVER, driver_sha = A._built("advance_driver")
    A.LAUNCH, launch_sha = A._built("advance_launch")
    bend_link = os.path.realpath(os.path.expanduser("~/.bend/current"))
    assert "/2.0.4/" in bend_link, "the admission is Bend 2.0.4; ~/.bend/current -> %s" % bend_link
    rec = {"benchmark": "B6 advancing world -- full-trajectory verification (every state, every backend)",
           "measured": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "loadavg_start": os.getloadavg(), "steps": a.steps,
           "seed": a.seed, "window_words": a.window_words, "bend_current": bend_link,
           "driver_c_sha256": driver_sha, "launch_c_sha256": launch_sha,
           "timing_tail_sha256": sha(A.BEND_TAIL.encode()), "verify_tail_sha256": sha(VERIFY_TAIL.encode()),
           "worlds": []}
    ok = True
    with tempfile.TemporaryDirectory(prefix="advance-verify-") as tmp:
        for name, src in worlds.items():
            r = one_world(name, src, a, tmp)
            ok &= r["ok"]
            rec["worlds"].append(r)
            b1, b2 = r["backends"]["bend1"], r["backends"]["bend2"]
            fc = lambda b: ("control %s/%s@%s" % (b["transient_fault_control"]["endpoint_check"],
                                                 b["transient_fault_control"]["full_check_first_divergence"],
                                                 b["transient_fault_control"]["fault_after_step"])
                            if "transient_fault_control" in b else "no reconverging fault found")
            print("%-22s slots %4d  %s  c2 %s  bend1 %s to %d (%d windows, %.1f cpu-s; %s)  bend2 %s to %d (%d windows; %s)  %.0f s"
                  % (name, r["slots"], "OK" if r["ok"] else "NOT OK", r["backends"]["c2"]["first_divergence"] or "agree",
                     b1["first_divergence"] or "agree", b1["every_state_checked_to_step"], b1["windows"], b1["cpu_s"], fc(b1),
                     b2["first_divergence"] or "agree", b2["every_state_checked_to_step"], b2["windows"], fc(b2),
                     r["seconds"]), flush=True)
            with open(a.out, "w") as f:
                json.dump(rec, f, indent=1)
    rec["loadavg_end"] = os.getloadavg()
    rec["all_ok"] = ok
    with open(a.out, "w") as f:
        json.dump(rec, f, indent=1)
    print("\nB6 full-trajectory verification: %s -> %s" % ("EVERY STATE OF EVERY BACKEND AGREES; every control separates"
                                                          if ok else "SOMETHING FAILED", a.out))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
