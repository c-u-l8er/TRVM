#!/usr/bin/env python3
"""advance.py -- B6, the ADVANCING-WORLD benchmark, computation-only rung: one world advanced N dependent steps,
C against Bend, every state verified, wall time AND CPU time AND peak memory.

    PYTHONDONTWRITEBYTECODE=1 python3 -B advance.py [--worlds a,b] [--steps 10000] [--sizes 1,1000,10000]
                                                    [--reps 5] [--calculus 24] [--seed 20260925]
                                                    [--out results-advance.json]

WHAT IS MEASURED. A process that takes a world's initial state and a control script of N epochs and advances
the world N steps, each step's input being the state the previous step wrote (`st' = step(st, ctl[k])`), then
writes the final state. Four ADMITTED representations of the same step, each run as its own process:

  c1     the C step (`emit_c`, profile compiled.c.step.v1), gcc -O2 `.so`, driven by `advance_driver.c` via dlopen
  c2     the packed C step (`emit_c2`, compiled.c.step.v2), same driver, state packed in 64-bit words
  bend1  Bend 2.0.4 (`emit_bend`, compiled.bend.step.v1), one cons per slot
  bend2  Bend 2.0.4 (`emit_bend2`, compiled.bend.step.v2), state packed in 32-bit words

The step text of each is the admitted emitter's output, byte for byte. Only the DRIVER differs from what the
admission ran: `advance_driver.c` for C (the admitted `.so` itself is loaded), and for Bend the admitted source
up to `def reps(` with a new tail that reads a script file and folds it (`BEND_TAIL` below; the step text is
asserted unchanged). The Bend runtime sizes its thread pool from the affinity mask, so every backend runs
PINNED to one CPU (`taskset`), and Bend also runs unpinned (its default: every core) as a second row.

WHAT "VERIFIED" MEANS HERE. Each backend also runs once in `all` mode (every state emitted). Those four
trajectories, unpacked to the C slot vector, must be IDENTICAL at every step -- a four-way cross-check of two
languages and two representations each. But c1/c2/bend1/bend2 all render their laws from ONE source
(`laws.py`), so a law wrong in that source would be wrong in all four and they would still agree; that is why
`--calculus K` also replays K sampled steps through the interaction calculus (ic32 on `((step ec) st)` from
`compiler.compile_step_v6`, the independent lowering the admission battery uses) and requires the decoded
normal form to equal the verified state. Every timed `final` run must end in the verified trajectory's final
state. A backend whose trajectory is not verified contributes ZERO verified steps.

WHAT IT IS NOT. The controls are generated directly as control vectors (seeded; SetRotor lanes in [0, 2^w),
ResetFault), NOT through Forge's claim admission: a world's claim state holds six accepted operations for its
whole life (`admit.MAX_EVENTS`), so a long trajectory cannot be driven through claims, and the executor and
Super's `trvm.reduce` take a control vector directly anyway. Nothing here is authorized, durable or receipted;
that path is `wek/b2/trvm/ADVANCE.md`'s through-Super rung. Shared laptop, development reading.

ACCOUNTING. Each run is one child process under `advance_launch.c`, whose wait4 gives its user+system CPU and
max RSS (all its threads; a ~1 MB launcher, because Linux keeps the RSS high-water mark across exec and a child
of the Python harness reads >= 30 MB whatever it does); wall is CLOCK_MONOTONIC from fork to reap. Per-step cost is the least-squares SLOPE over the sizes (median of
the reps per size), so process start, input parsing and output are in the intercept, reported beside it.
"""
import argparse
import hashlib
import json
import os
import random
import statistics as st
import struct
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import fold as F                       # noqa: E402  (sets up the forge + runtime paths)
import battery as B                    # noqa: E402
import emit_c as EC                    # noqa: E402
import emit_c2 as EC2                  # noqa: E402
import emit_bend as EB                 # noqa: E402
import emit_bend2 as EB2               # noqa: E402
C, P, O = F.C, F.P, F.O

CACHE = os.path.join(EC.CACHE, "advance")
BACKENDS = ("c1", "c2", "bend1", "bend2")
PIN_CPU = os.environ.get("ADVANCE_PIN_CPU", "3")

# The Bend driver tail: replaces the admitted program's `reps`/`run`/`main` (the step and helpers above it are
# kept byte for byte). `adv` folds the script tail-recursively; `trail` yields every state for `all` mode;
# `shows` is linear where the admitted `show_all` concatenates an accumulator (quadratic in the state width).
BEND_TAIL = '''def shows(xs: List<&2, Nat>) -> List<&2, String>:
  match xs:
    case Nil{}:
      Nil{}
    case Con{h, t}:
      Nat.show(h) <> shows(t)

def row(xs: List<&2, Nat>) -> String:
  String.join(shows(xs), " ")

def lines(xs: List<&2, String>) -> List<&2, List<&2, Nat>>:
  match xs:
    case Nil{}:
      Nil{}
    case Con{h, t}:
      nats(String.split(h, ' ')) <> lines(t)

def adv(cts: List<&2, List<&2, Nat>>, st: List<&2, Nat>) -> List<&2, Nat>:
  match cts:
    case Nil{}:
      st
    case Con{c, rest}:
      adv(rest, step(st, c))

def trail(cts: List<&2, List<&2, Nat>>, st: List<&2, Nat>) -> List<&2, String>:
  match cts:
    case Nil{}:
      Nil{}
    case Con{c, rest}:
      +nx = step(st, c)
      row(nx) <> trail(rest, nx)

def csum(xs: List<&2, Nat>, acc: Nat) -> Nat:
  match xs:
    case Nil{}:
      acc
    case Con{h, t}:
      csum(t, Nat.mod(Nat.add(acc, h), U32.to_nat(1000000007)))

def csum_all(cts: List<&2, List<&2, Nat>>, acc: Nat) -> Nat:
  match cts:
    case Nil{}:
      acc
    case Con{c, rest}:
      csum_all(rest, csum(c, acc))

def emit_more(+p: Nat, cts: List<&2, List<&2, Nat>>, st: List<&2, Nat>) -> String:
  match p:
    case 0n:
      String.join(trail(cts, st), "\\n")
    case 1n+q:
      Nat.show(csum_all(cts, 0n))

def emit(+m: Nat, cts: List<&2, List<&2, Nat>>, st: List<&2, Nat>) -> String:
  match m:
    case 0n:
      row(adv(cts, st))
    case 1n+p:
      emit_more(p, cts, st)

def got_text(got: File & Result<&1, &1, U32 & String, String>) -> IO(String):
  (f, r) = got
  do IO<String>:
    File.close(f)
    IO.pass(String, r)

def read_all(path: String) -> IO(String):
  do IO<String>:
    f : File <- IO.try(File, File.open(path, "r"))
    got : File & Result<&1, &1, U32 & String, String> <- File.read(f, 2000000000)
    got_text(got)

def main() -> IO(Unit):
  do IO<Unit>:
    st : String <- IO.try(String, IO.get_env("TRVM_ST"))
    path : String <- IO.try(String, IO.get_env("TRVM_SCRIPT"))
    mode : String <- IO.try(String, IO.get_env("TRVM_MODE"))
    txt : String <- read_all(path)
    IO.print(emit(nat_of(mode), lines(String.lines(txt)), nats(String.split(st, ' '))))
'''


def sha(b):
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------------------------------ the world and its script
def control_script(view, seed, n, p_rotor=0.3, p_reset=0.1):
    """N epochs of (cfg_map, resets), seeded. SetRotor lanes in [0, 2^w) -- the range admission accepts
    (`admit._op_outcome`) -- biased to the lane extremes a third of the time, as `battery.random_scenario` is."""
    rng = random.Random(seed)
    ctrl, orbs = EC.control_layout(view)
    out = []
    for _ in range(n):
        cfg = {}
        for s in ctrl:
            if rng.random() < p_rotor:
                w, nfrac, _ = view.spinners[s]

                def lane():
                    if rng.random() < 0.35:
                        return rng.choice([0, (1 << (w - 1)) - 1, 1 << (w - 1), (1 << w) - 1, 1 << nfrac,
                                           ((1 << w) - 1) ^ (1 << nfrac)])
                    return rng.randrange(1 << w)
                cfg[s] = tuple(lane() for _ in range(4))
        resets = {o: True for o in orbs if rng.random() < p_reset}
        out.append((cfg, resets))
    return out


class World:
    def __init__(self, name, src, n, seed):
        self.name, self.src = name, src
        self.sem, self.view, _dig, _script, self.world0, _claim, _seams = F._prepare(src, None)
        self.c1 = EC.CompiledStep(self.view, self.sem)
        self.script = control_script(self.view, seed, n)
        self.a0 = list(self.c1.encode(self.world0))                         # the C slot vector: the common currency
        self.ctls = [list(self.c1.control(cfg, rs)) for cfg, rs in self.script]
        self.cw = 5 * len(self.c1.ctrl) + len(self.c1.orbs)
        self.script_sha256 = sha(json.dumps(self.ctls).encode())


# ------------------------------------------------------------------------------------------ the four backends
def _built(name):
    """A helper binary from this directory, content-addressed under the cache (never in the tree)."""
    path = os.path.join(HERE, name + ".c")
    with open(path, "rb") as f:
        src = f.read()
    os.makedirs(CACHE, exist_ok=True)
    exe = os.path.join(CACHE, "%s-%s" % (name, sha(src)[:16]))
    if not os.path.exists(exe):
        subprocess.run(["gcc", "-O2", "-o", exe + ".tmp", path, "-ldl"], check=True)
        os.replace(exe + ".tmp", exe)
    return exe, sha(src)


class Backend:
    """pack/unpack between the C slot vector and this representation; run(n-prefix, mode) as a child process."""

    def __init__(self, kind, w):
        self.kind, self.w = kind, w
        v = w.view
        if kind == "c1":
            self.cs = w.c1
            self.pack = lambda a: list(a)
            self.unpack = lambda a: list(a)
            self.width = self.cs.width
            self.obj, self.code_sha256 = self.cs.so_path, self.cs.source_sha256
            self.toolchain = "gcc -O2 (emit_c.build)"
        elif kind == "c2":
            self.cs = EC2.CompiledStep2(v, w.sem)
            self.pack, self.unpack = self.cs.pack, self.cs.unpack
            self.width = self.cs.packed_width
            self.obj, self.code_sha256 = self.cs.so_path, self.cs.source_sha256
            self.toolchain = "gcc %s (emit_c2.build)" % " ".join(self.cs.flags)
        else:
            if kind == "bend1":
                step_cls, src = EB.BendStep, EB.emit_step_bend(v)
                self.pack, self.unpack, self.width = (lambda a: list(a)), (lambda a: list(a)), None
            else:
                step_cls, (src, pw) = EB2.BendStep2, EB2.emit_step_bend2(v)
                lay = EB2.packed_layout(v)
                self.pack = lambda a: EB2.pack_vector(v, list(a), lay)
                self.unpack = lambda a: EB2.unpack_vector(v, list(a), lay)
                self.width = pw
            self.cs = step_cls(v, w.sem)                     # the ADMITTED program, built as the battery builds it
            assert self.cs.source == src
            cut = src.index("def reps(")
            self.driver_source = src[:cut] + BEND_TAIL
            assert self.driver_source[:cut] == self.cs.source[:cut], "the step text must be the admitted one"
            self.obj, self.code_sha256, _ = EB.build(self.driver_source)
            self.admitted_source_sha256 = self.cs.source_sha256
            self.toolchain = "bend 2.0.4 -> clang -O3"
        if self.width is None:
            self.width = w.c1.width
        self.backend_id = self.cs.backend_id

    def run(self, n, mode, pin, tmp):
        """The same protocol for all four: TRVM_ST (this representation's initial words), TRVM_SCRIPT (one text
        file per n, shared by every backend), TRVM_MODE (0 final, 1 every state, 2 decode only)."""
        w = self.w
        scr = os.path.join(tmp, "script-%s-%d.txt" % (w.name, n))
        if not os.path.exists(scr):
            with open(scr, "w") as f:
                f.write("\n".join(" ".join(str(x) for x in c) if c else "0" for c in w.ctls[:n]))
        argv = [DRIVER, self.obj] if self.kind in ("c1", "c2") else [self.obj]
        env = dict(os.environ, TRVM_ST=" ".join(str(int(x)) for x in self.pack(w.a0)), TRVM_SCRIPT=scr,
                   TRVM_MODE={"final": "0", "all": "1", "decode": "2"}[mode], BEND_NO_TELEMETRY="1")
        outp = None
        if pin:
            argv = ["taskset", "-c", PIN_CPU] + argv
        so = open(os.path.join(tmp, "stdout"), "w+b")
        se = open(os.path.join(tmp, "stderr"), "w+b")
        report = os.path.join(tmp, "rusage.json")
        rc = subprocess.run([LAUNCH, report] + argv, stdout=so, stderr=se, env=env).returncode
        with open(report) as f:
            ru = json.load(f)
        so.seek(0), se.seek(0)
        out_b, err_b = so.read(), se.read()
        so.close(), se.close()
        return rc, out_b, err_b, ru["wall_s"], outp, ru


def run_measured(be, n, mode, pin, tmp):
    """One child, reaped by wait4 so its own rusage is exact (user, system, max RSS of all its threads)."""
    rc, out_b, err_b, wall, outp, ru = be.run(n, mode, pin, tmp)
    cpu_u, cpu_s = ru["cpu_user_s"], ru["cpu_sys_s"]
    if rc != 0:
        raise RuntimeError("%s n=%d %s rc=%d: %s" % (be.kind, n, mode, rc, (out_b + err_b)[-400:]))
    inner = None
    if be.kind in ("c1", "c2"):
        inner = json.loads(err_b.decode().strip().splitlines()[-1])
    text = out_b.decode().strip()
    if mode == "decode":
        return {"wall_s": wall, "cpu_user_s": cpu_u, "cpu_sys_s": cpu_s, "cpu_s": cpu_u + cpu_s,
                "maxrss_kb": ru["maxrss_kb"], "inner": inner, "checksum": int(text)}, None
    rows = [[int(x) for x in line.split()] for line in text.split("\n")]
    for r in rows:
        if len(r) != be.width:
            raise RuntimeError("%s returned a state of %d words, expected %d" % (be.kind, len(r), be.width))
    return {"wall_s": wall, "cpu_user_s": cpu_u, "cpu_sys_s": cpu_s, "cpu_s": cpu_u + cpu_s,
            "maxrss_kb": ru["maxrss_kb"], "inner": inner,
            "faults_minor": ru["minflt"], "ctx_voluntary": ru["nvcsw"], "ctx_involuntary": ru["nivcsw"]}, rows


# ------------------------------------------------------------------------------------------ verification
def calculus_check(w, traj, k_indices):
    """Replay sampled steps through the interaction calculus: ic32 reduces ((step ec_k) st_{k-1}) and the decoded
    normal form must equal the verified state after step k. Independent of laws.py: the term is
    compiler.compile_step_v6's lowering, the same one the admission battery folds."""
    step_term, _ = C.compile_step_v6(w.view)
    res = []
    for k in k_indices:
        prev = w.a0 if k == 0 else traj[k - 1]
        cfg, rs = w.script[k]
        ec = C.enc_config_bundle(w.view, cfg, rs)
        stt = C.enc_state_v6(w.view, w.c1.decode(w.c1._Arr(*prev)))
        term = "((%s %s) %s)" % (step_term, ec, stt)
        t0 = time.perf_counter()
        if O.native_available() and len(term) < (16 << 20):
            nf, red = O.native_reduce(term), "ic32"
        else:
            nf, red = O.ref_reduce(term), "ic_ref"
        dt = time.perf_counter() - t0
        got = list(w.c1.encode(C.dec_state_v6(w.view, nf)))
        res.append({"step": k + 1, "agree": got == list(traj[k]), "reducer": red, "term_bytes": len(term),
                    "reduce_s": round(dt, 4)})
    return res


def fit(points):
    """Least squares y = a + b x over (x, y); returns (a, b)."""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    return my - b * mx, b


def one_world(name, src, a, tmp):
    w = World(name, src, max(a.sizes), a.seed)
    rec = {"world": name, "sem": w.sem, "slots": w.c1.width, "control_width": w.cw,
           "script": {"seed": a.seed, "steps": max(a.sizes), "sha256": w.script_sha256,
                      "rotor_writes": sum(len(c) for c, _ in w.script), "resets": sum(len(r) for _, r in w.script)},
           "backends": {}, "refused": {}}
    bes = {}
    for kind in a.backends:
        try:
            bes[kind] = Backend(kind, w)
        except ValueError as e:                              # an emitter's own width refusal
            rec["refused"][kind] = str(e)[:200]
    n = max(a.sizes)
    # ---- verification. The two C representations emit EVERY state to n; the Bend ones every state to a prefix
    # bounded by the state's width (a Bend String is a cons list of chars: 100k states of 485 words would be GBs),
    # and every timed run's final state -- at every size, to n -- must equal the verified trajectory's.
    trajs, spans = {}, {}
    for kind, be in bes.items():
        nv = n if kind in ("c1", "c2") else max(1, min(n, a.verify_words // max(1, be.width)))
        m, rows = run_measured(be, nv, "all", True, tmp)
        trajs[kind] = [be.unpack(r) for r in rows]
        spans[kind] = nv
        rec["backends"][kind] = {"backend_id": be.backend_id, "code_sha256": be.code_sha256,
                                 "toolchain": be.toolchain, "state_words": be.width, "all_mode": m,
                                 "every_state_checked_to_step": nv}
        if kind.startswith("bend"):
            rec["backends"][kind]["admitted_source_sha256"] = be.admitted_source_sha256
    ref_kind = "c1" if "c1" in trajs else next(iter(trajs))
    ref = trajs[ref_kind]
    agree = {}
    for kind, t in trajs.items():
        first = next((i + 1 for i, (x, y) in enumerate(zip(t, ref)) if x != y), None)
        if first is None and len(t) != spans[kind]:
            first = len(t) + 1
        agree[kind] = first
    rec["cross_check"] = {"reference": ref_kind, "first_divergence": agree, "every_state_to": spans,
                          "all_agree": all(v is None for v in agree.values())}
    # the calculus on sampled steps of the reference trajectory, spread over all n (step 1 and step n always)
    k = max(0, min(a.calculus, n))
    idx = sorted({0, n - 1} | {round(i * (n - 1) / max(1, k - 1)) for i in range(k)}) if k else []
    cc = calculus_check(w, ref, idx) if idx else []
    rec["calculus"] = {"sampled": len(cc), "agree": all(r["agree"] for r in cc), "rows": cc}
    verified = rec["cross_check"]["all_agree"] and rec["calculus"]["agree"]
    rec["verified"] = verified
    final_ref = ref[-1]
    # ---- timing: final mode, every size, reps interleaved across backends so drift lands on all of them
    rows = []
    rows_by, dec_by = {}, {}
    checksums = {size: sum(x for c in w.ctls[:size] for x in (c or [0])) % 1000000007 for size in a.sizes}
    for rep in range(a.reps):
        for size in a.sizes:
            for kind, be in bes.items():
                for pin in ((True, False) if kind.startswith("bend") else (True,)):
                    m, out = run_measured(be, size, "final", pin, tmp)
                    ended = be.unpack(out[-1])
                    want = ref[size - 1]                          # the VERIFIED trajectory, every size
                    m.update({"backend": kind, "mode": "final", "pinned": pin, "steps": size, "rep": rep,
                              "final_is_verified_state": ended == list(want)})
                    rows.append(m)
                    rows_by.setdefault((kind, pin), []).append(m)
                m, _ = run_measured(be, size, "decode", True, tmp)       # the script decode alone, same bytes
                m.update({"backend": kind, "mode": "decode", "pinned": True, "steps": size, "rep": rep,
                          "checksum_ok": m["checksum"] == checksums[size]})
                rows.append(m)
                dec_by.setdefault(kind, []).append(m)
    summ = {}
    for (kind, pin), ms in rows_by.items():
        per = {}
        for size in a.sizes:
            sel = [m for m in ms if m["steps"] == size]
            per[size] = {"wall_s": st.median(m["wall_s"] for m in sel), "cpu_s": st.median(m["cpu_s"] for m in sel),
                         "maxrss_kb": max(m["maxrss_kb"] for m in sel)}
        aw, bw = fit([(s, per[s]["wall_s"]) for s in a.sizes])
        ac, bc = fit([(s, per[s]["cpu_s"]) for s in a.sizes])
        inner = [m["inner"]["steps_ns"] / m["steps"] for m in ms if m["inner"] and m["steps"] == n]
        # (the C driver's own clock: the step loop alone, script already decoded -- the process's inner view)
        ok = verified and all(m["final_is_verified_state"] for m in ms)
        top = per[n]
        dec = dec_by.get(kind, [])
        dper = {size: (st.median(m["wall_s"] for m in dec if m["steps"] == size),
                       st.median(m["cpu_s"] for m in dec if m["steps"] == size)) for size in a.sizes}
        _dw, dbw = fit([(s2, dper[s2][0]) for s2 in a.sizes])
        _dc, dbc = fit([(s2, dper[s2][1]) for s2 in a.sizes])
        ok = ok and all(m["checksum_ok"] for m in dec)
        summ["%s%s" % (kind, "" if pin else "-unpinned")] = {
            "backend": kind, "pinned": pin, "verified": ok,
            "per_step_wall_us": round(bw * 1e6, 4), "per_step_cpu_us": round(bc * 1e6, 4),
            "intercept_wall_ms": round(aw * 1e3, 3), "intercept_cpu_ms": round(ac * 1e3, 3),
            "cpu_per_wall_at_n": round(top["cpu_s"] / top["wall_s"], 3) if top["wall_s"] else None,
            "steady_steps_per_s": round(1 / bw) if ok and bw > 0 else 0,
            "steady_steps_per_cpu_s": round(1 / bc) if ok and bc > 0 else 0,
            "whole_run_at_n": {"steps": n, "wall_s": round(top["wall_s"], 5), "cpu_s": round(top["cpu_s"], 5),
                               "steps_per_s": round(n / top["wall_s"]) if ok else 0,
                               "steps_per_cpu_s": round(n / top["cpu_s"]) if ok and top["cpu_s"] else 0,
                               "maxrss_mb": round(top["maxrss_kb"] / 1024, 1)},
            "driver_inner_step_ns_p50": round(st.median(inner), 2) if inner else None,
            "decode_per_step_wall_us": round(dbw * 1e6, 4), "decode_per_step_cpu_us": round(dbc * 1e6, 4),
            "step_only_per_step_cpu_us_derived": round((bc - dbc) * 1e6, 4),
            "per_size": {str(s): {k2: round(v2, 6) if isinstance(v2, float) else v2 for k2, v2 in per[s].items()}
                         for s in a.sizes}}
    rec["summary"] = summ
    rec["runs"] = rows
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--worlds", default=None)
    ap.add_argument("--sizes", default="1,1000,10000")
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--calculus", type=int, default=24, help="sampled steps replayed through the calculus per world")
    ap.add_argument("--seed", type=int, default=20260925)
    ap.add_argument("--verify-words", type=int, default=2_000_000,
                    help="the Bend backends emit every state up to this many state words (steps x width)")
    ap.add_argument("--backends", default=",".join(BACKENDS))
    ap.add_argument("--out", default=os.path.join(HERE, "results-advance.json"))
    a = ap.parse_args()
    a.sizes = sorted({int(x) for x in a.sizes.split(",")})
    a.backends = a.backends.split(",")
    worlds = {k: v for k, v in B.WORLDS.items() if k not in B.WIDE_WORLDS}
    if a.worlds:
        worlds = {k: B.WORLDS[k] for k in a.worlds.split(",")}
    global DRIVER, LAUNCH
    DRIVER, driver_sha = _built("advance_driver")
    LAUNCH, launch_sha = _built("advance_launch")
    bend_ver = subprocess.run([EB.BEND, "--version"], capture_output=True, text=True,
                              env=dict(os.environ, BEND_NO_TELEMETRY="1",
                                       PATH=os.path.expanduser("~/.bun/bin") + ":" + os.environ["PATH"])).stdout.strip()
    rec = {"benchmark": "B6 advancing world -- computation-only rung", "measured": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "loadavg_start": os.getloadavg(), "nproc": os.cpu_count(), "pin_cpu": PIN_CPU, "sizes": a.sizes,
           "reps": a.reps, "seed": a.seed, "driver_c_sha256": driver_sha, "launch_c_sha256": launch_sha, "bend_tail_sha256": sha(BEND_TAIL.encode()),
           "bend": bend_ver, "ic32": O.IC32, "ic32_sha256": sha(open(O.IC32, "rb").read()) if O.native_available() else None,
           "worlds": []}
    ok = True
    with tempfile.TemporaryDirectory(prefix="advance-") as tmp:
        for name, src in worlds.items():
            t0 = time.time()
            r = one_world(name, src, a, tmp)
            ok &= r["verified"]
            rec["worlds"].append(r)
            print("%-22s slots %4d  %s  calculus %d/%d  (%.0f s)" % (
                name, r["slots"], "VERIFIED" if r["verified"] else "NOT VERIFIED %s" % r["cross_check"]["first_divergence"],
                sum(x["agree"] for x in r["calculus"]["rows"]), r["calculus"]["sampled"], time.time() - t0), flush=True)
            for k2, s in r["summary"].items():
                print("    %-15s %9.4f us/step wall %9.4f us/step cpu  x%.2f cpu/wall  %11s steps/s  %11s steps/cpu-s  "
                      "intercept %7.2f ms  rss %6.1f MB  decode %7.4f us/step cpu" % (
                          k2, s["per_step_wall_us"], s["per_step_cpu_us"], s["cpu_per_wall_at_n"] or 0,
                          s["steady_steps_per_s"], s["steady_steps_per_cpu_s"], s["intercept_wall_ms"],
                          s["whole_run_at_n"]["maxrss_mb"], s["decode_per_step_cpu_us"]), flush=True)
                if s["driver_inner_step_ns_p50"] is not None:
                    print("    %-15s driver's own clock: %.2f ns/step (decoded script, no process start)" % (
                        "", s["driver_inner_step_ns_p50"]), flush=True)
            with open(a.out, "w") as f:
                json.dump(rec, f, indent=1)
    rec["loadavg_end"] = os.getloadavg()
    rec["all_verified"] = ok
    with open(a.out, "w") as f:
        json.dump(rec, f, indent=1)
    print("\nB6 computation-only: %s -> %s" % ("EVERY WORLD VERIFIED" if ok else "A WORLD WAS NOT VERIFIED", a.out))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
