"""emit_bend.py -- a FIFTH representation of a WRL world: the same CompilePlanV1 view lowered to a Bend 2 program.

Bend 2.0.4 (bend-lang.com; `FOUNDATION_LANE.md` §3ao) is a compiled affine language whose native target is one C file built
by clang. This emitter writes the SAME laws `emit_c.py` writes in C -- `compiler.state_layout` order, the clock/wire/door/
relay laws of `compile_step_v6`, COMMIT-then-REACT per orb, the wide-MAC rotor law of `binlib.golden_rot_forge` from the
same HAMILTON table -- as one Bend `step(xs, cs)` over a list of Nats, so that the battery can admit (or refuse) Bend as a
backend by the one oracle every backend answers to: film- and state-equality with the interaction calculus, world by world.

What Bend 2.0.4's numerics impose (measured 2026-09-18, `~/.cache/trvm-compiled/bend/*.bend`):
  * `Nat` is a 48-bit machine word at runtime (a program aborts past 2^48-1) with add/sub(saturating)/mul/divmod as
    machine ops (1 M mul+mod iterations in 6 ms as a binary); `U32` is 32-bit with shifts. There is no I64/U64, no signed
    type and no shift on Nat, so the MAC is done in sign-magnitude over Nat: products of magnitudes, two accumulators
    (positive and negative), a toward-zero quotient by `Nat.div` of a power of two, one saturation, one re-encoding.
    The four-term accumulator is bounded by 2^(2w), so lane widths over 24 are REFUSED here (the C step admits 63).
  * a Nat literal is expanded by the checker (`65536n` overflows its stack), so constants over 255 are `U32.to_nat(N)`.
  * a `match` may not scrutinize a computed value, and neither may a destructuring let -- so a helper returning a pair is
    given the pair to destructure as a PARAMETER, and the MAC row's (lane, overflow) result is packed into ONE Nat
    (`lane + full * ov`) and unpacked with `Nat.mod` / `Nat.div`.
  * an `Array<U32>` read is a computed scrutinee too, so the state is a `List<&2, Nat>` unpacked by ONE nested `Con`
    pattern (depth 500 checks in 0.4 s) and the output is a list literal.
Input and output are strings: `TRVM_ST` / `TRVM_CTL` (space-separated Nats, the slot orders of `emit_c.slot_map` and
`control_layout`), `TRVM_REPS` (fold the step K times under the same control, for timing); stdout is the state after.
Identity: `bbknd-` + sha256(SemanticArtifactID + `compiled.bend.step.v1` + the emitted source).
"""
import hashlib
import os
import subprocess

from compiler import pose_width
from binlib import HAMILTON
from emit_c import slot_map, control_layout, _cid, CompiledStep

PROFILE = "compiled.bend.step.v1"
CACHE = os.environ.get("TRVM_COMPILED_CACHE") or os.path.expanduser("~/.cache/trvm-compiled")
BEND = os.environ.get("BEND", os.path.expanduser("~/.bend/bin/bend"))
MAX_LANE_WIDTH = 24   # |pos| and |neg| accumulators <= 4 * 2^(2w-2) = 2^(2w) must fit Bend's 48-bit Nat


def lit(n):
    """A Nat constant Bend's checker will accept: a literal to 255, else built from a U32."""
    n = int(n)
    if n <= 255:
        return "{%dn : Nat}" % n        # annotated: a bare literal in a let cannot be inferred
    if n < (1 << 32):
        return "U32.to_nat(%d)" % n
    raise ValueError("emit_bend: constant %d does not fit a U32 literal" % n)


HELPERS = '''
def sel(b: Bool, x: Nat, y: Nat) -> Nat:
  match b:
    case True{}:
      x
    case False{}:
      y

def b2n(b: Bool) -> Nat:
  match b:
    case True{}:
      1n
    case False{}:
      0n

def nz(x: Nat) -> Bool:
  Nat.is_ne(x, 0n)

# sign-magnitude of a w-bit two's-complement lane: (negative?, magnitude)
def sx_if(neg: Bool, v: Nat, full: Nat) -> Bool & Nat:
  match neg:
    case True{}:
      (True{}, (full - v : Nat))
    case False{}:
      (False{}, v)

def sx(+v: Nat, +half: Nat, +full: Nat) -> Bool & Nat:
  sx_if(Bool.not(Nat.is_lt(v, half)), v, full)

# one HAMILTON term added to the (positive, negative) accumulators
def acc_if(neg: Bool, m: Nat, pn: Nat & Nat) -> Nat & Nat:
  match neg:
    case True{}:
      (p, n) = pn
      (p, (n + m : Nat))
    case False{}:
      (p, n) = pn
      ((p + m : Nat), n)

def term(sg_neg: Bool, ra: Bool & Nat, pb: Bool & Nat, pn: Nat & Nat) -> Nat & Nat:
  (na, ma) = ra
  (nb, mb) = pb
  acc_if(Bool.xor(sg_neg, Bool.xor(na, nb)), (ma * mb : Nat), pn)

# golden_mac's tail: ONE toward-zero quotient, ONE saturation, the lane re-encoded; packed as lane + full * overflow
def pack(lane: Nat, ov: Bool, +full: Nat) -> Nat:
  (lane + full * b2n(ov) : Nat)

def sat_pos(+q: Nat, +hi: Nat, +full: Nat) -> Nat:
  pack(Nat.min(q, hi), Nat.is_gt(q, hi), full)

def enc_neg(+qq: Nat, +full: Nat) -> Nat:
  sel(Nat.is_eq(qq, 0n), 0n, (full - qq : Nat))

def sat_neg(+q: Nat, +lomag: Nat, +full: Nat) -> Nat:
  pack(enc_neg(Nat.min(q, lomag), full), Nat.is_gt(q, lomag), full)

def fin_if(negside: Bool, pos: Nat, neg: Nat, +den: Nat, +hi: Nat, +lomag: Nat, +full: Nat) -> Nat:
  match negside:
    case True{}:
      sat_neg(Nat.div((neg - pos : Nat), den), lomag, full)
    case False{}:
      sat_pos(Nat.div((pos - neg : Nat), den), hi, full)

def fin(pn: Nat & Nat, +den: Nat, +hi: Nat, +lomag: Nat, +full: Nat) -> Nat:
  (p, n) = pn
  +pos = p
  +neg = n
  fin_if(Nat.is_lt(pos, neg), pos, neg, den, hi, lomag, full)

def nat_of(s: String) -> Nat:
  Maybe.default(&2, Nat, Nat.read(s), 0n)

def nats(xs: List<&2, String>) -> List<&2, Nat>:
  match xs:
    case Nil{}:
      Nil{}
    case Con{h, t}:
      nat_of(h) <> nats(t)

def show_all(xs: List<&2, Nat>, acc: String) -> String:
  match xs:
    case Nil{}:
      acc
    case Con{h, t}:
      show_all(t, acc ++ Nat.show(h) ++ " ")
'''


def emit_step_bend(view):
    """The Bend source for one world's epoch step. Deterministic in the plan view."""
    fields, width = slot_map(view)
    off = {(k, n): o for k, n, o, _, _ in fields}
    spec = {n: s for k, n, _, _, s in fields if k == "counter"}
    ppl, wires, doors, relays = view.layout()
    orbs = list(view.orbs)
    ctrl, _ = control_layout(view)
    for s in view.spinners:
        w_ = view.spinners[s][0]
        if not (1 <= w_ <= MAX_LANE_WIDTH):
            raise ValueError("emit_bend: lane width %d of spinner %s is outside 1..%d (Bend's Nat is 48 bits)" % (w_, s, MAX_LANE_WIDTH))
    cw = 5 * len(ctrl) + len(orbs)
    L = ["# generated by TRVM compiled/emit_bend.py -- profile %s -- do not edit" % PROFILE, "import Base", HELPERS]
    emit = L.append
    s_pat = "".join("Con{+s%d, " % i for i in range(width)) + "_" + "}" * width      # + : a slot may be read more than once
    c_pat = ("".join("Con{+c%d, " % i for i in range(cw)) + "_" + "}" * cw) if cw else "_"
    emit("def step(xs: List<&2, Nat>, cs: List<&2, Nat>) -> List<&2, Nat>:")
    emit("  match xs cs:")
    emit("    case %s %s:" % (s_pat, c_pat))
    out = {}          # slot -> expression name

    def const(name, val):
        emit("      +%s = %s" % (name, lit(val)))
        return name

    # ---- clocks
    for r in ppl:
        sp, o = spec[r], off[("counter", r)]
        if sp[0] == "onehot":
            _, p, ph = sp
            emit("      # pulser %s: one-hot period %d phase %d" % (r, p, ph))
            emit("      +fire_%d = b2n(Nat.is_eq(s%d, %s))" % (o, o, lit(ph)))
            emit("      o%d = Nat.mod((s%d + 1n : Nat), %s)" % (o, o, lit(p)))
        elif sp[0] == "binp":
            _, p, ph, w_ = sp
            emit("      # pulser %s: binary period %d phase %d width %d" % (r, p, ph, w_))
            emit("      +fire_%d = b2n(Nat.is_eq(s%d, %s))" % (o, o, lit(ph)))
            emit("      +sum_%d = Nat.mod((s%d + 1n : Nat), %s)" % (o, o, lit(1 << w_)))
            emit("      o%d = sel(Nat.is_eq(sum_%d, %s), 0n, sum_%d)" % (o, o, lit(p), o))
        else:
            _, e, w_ = sp
            emit("      # pulser %s: once at %d width %d (done, k)" % (r, e, w_))
            emit("      +fire_%d = b2n(Bool.and(Nat.is_eq(s%d, 0n), Nat.is_eq(s%d, %s)))" % (o, o, o + 1, lit(e)))
            emit("      o%d = sel(nz((s%d + fire_%d : Nat)), 1n, 0n)" % (o, o, o))
            emit("      o%d = Nat.mod((s%d + 1n : Nat), %s)" % (o + 1, o + 1, lit(1 << w_)))
        out[o] = out.get(o, True)
    # ---- hot signals
    for r in ppl:
        if view.out_wires(r):
            emit("      +hot_%s = fire_%d" % (_cid(r), off[("counter", r)]))
    for r in relays:
        if view.out_wires(r):
            emit("      +hot_%s = s%d  # relay %s nxt" % (_cid(r), off[("relay", r)] + 1, r))

    def merge_in(role):
        ins = view.in_wires(role)
        if not ins:
            return "{0n : Nat}"
        return " + ".join("s%d" % (off[("wire", wr)] + 1) for wr in ins) if len(ins) == 1 else "Nat.min(1n, (%s : Nat))" % " + ".join("s%d" % (off[("wire", wr)] + 1) for wr in ins)

    src_of = {}
    for role in list(ppl) + list(relays):
        for wr in view.out_wires(role):
            src_of[wr] = role
    for wr in wires:
        o = off[("wire", wr)]
        emit("      o%d = s%d" % (o, o + 1))
        emit("      o%d = hot_%s  # wire %s" % (o + 1, _cid(src_of[wr]), wr))
    for d in doors:
        o = off[("door", d)]
        emit("      o%d = s%d" % (o, o + 1))
        emit("      o%d = %s  # door %s" % (o + 1, merge_in(d), d))
    for r in relays:
        o = off[("relay", r)]
        emit("      o%d = s%d" % (o, o + 1))
        emit("      o%d = %s  # relay %s" % (o + 1, merge_in(r), r))
    # ---- orbs: COMMIT the fault reset and the rotor config, then REACT
    for i, ob in enumerate(orbs):
        po, fo = off[("pose", ob)], off[("fault", ob)]
        reset_slot = 5 * len(ctrl) + i
        emit("      # orb %s" % ob)
        emit("      +fbase_%d = sel(nz(c%d), 0n, s%d)  # COMMIT fault reset" % (fo, reset_slot, fo))
        s = view.controller_of(ob)
        if not s:
            for l in range(4):
                emit("      o%d = s%d" % (po + l, po + l))
            emit("      o%d = fbase_%d  # no controller" % (fo, fo))
            continue
        w_, n_, _ = view.spinners[s]
        ro, ci = off[("rotor", s)], 5 * ctrl.index(s)
        full = const("full_%d" % po, 1 << w_)
        half = const("half_%d" % po, 1 << (w_ - 1))
        hi = const("hi_%d" % po, (1 << (w_ - 1)) - 1)
        den = const("den_%d" % po, 1 << n_)
        emit("      +set_%d = nz(c%d)" % (po, ci))
        for l in range(4):
            emit("      +eff_%d_%d = sel(set_%d, c%d, s%d)  # COMMIT rotor lane %d: SetRotor replaces, NoChange keeps" % (po, l, po, ci + 1 + l, ro + l, l))
            emit("      o%d = eff_%d_%d" % (ro + l, po, l))
        emit("      +sel_%d = nz(%s)  # spinner %s merged input" % (po, merge_in(s), s))
        for c in range(4):
            acc = "(0n, 0n)"
            for sg, ii, jj in reversed(HAMILTON[c]):
                acc = "term(%s, sx(eff_%d_%d, %s, %s), sx(s%d, %s, %s), %s)" % ("True{}" if sg < 0 else "False{}", po, ii, half, full, po + jj, half, full, acc)
            emit("      +x_%d_%d = fin(%s, %s, %s, %s, %s)" % (po, c, acc, den, hi, half, full))
        emit("      +ov_%d = nz((%s : Nat))" % (po, " + ".join("Nat.div(x_%d_%d, %s)" % (po, c, full) for c in range(4))))
        for c in range(4):
            emit("      o%d = sel(sel_%d, Nat.mod(x_%d_%d, %s), s%d)  # REACT over the committed rotor" % (po + c, po, po, c, full, po + c))
        emit("      o%d = sel(sel_%d, sel(nz((fbase_%d + b2n(ov_%d) : Nat)), 1n, 0n), fbase_%d)  # sticky fault" % (fo, po, fo, po, fo))
    emit("      [%s]" % ", ".join("o%d" % i for i in range(width)))
    emit("    case _ _:")
    emit("      Nil{}")
    emit("")
    emit("def reps(+n: Nat, st: List<&2, Nat>, +cs: List<&2, Nat>) -> List<&2, Nat>:")
    emit("  match n:")
    emit("    case 0n:")
    emit("      st")
    emit("    case 1n+p:")
    emit("      reps(p, step(st, cs), cs)")
    emit("")
    emit("def run(st: String, ct: String, k: String) -> String:")
    emit("  show_all(reps(nat_of(k), nats(String.split(st, ' ')), nats(String.split(ct, ' '))), \"\")")
    emit("")
    emit("def main() -> IO(Unit):")
    emit("  do IO<Unit>:")
    emit("    st : String <- IO.try(String, IO.get_env(\"TRVM_ST\"))")
    emit("    ct : String <- IO.try(String, IO.get_env(\"TRVM_CTL\"))")
    emit("    k : String <- IO.try(String, IO.get_env(\"TRVM_REPS\"))")
    emit("    IO.print(run(st, ct, k))")
    return "\n".join(L) + "\n"


def backend_id(sem_id, source):
    return "bbknd-" + hashlib.sha256((sem_id + "\n" + PROFILE + "\n" + source).encode()).hexdigest()


def build(source):
    """Content-addressed build: the binary is keyed by the sha256 of the source; a failed check is a refusal with the message."""
    d = os.path.join(CACHE, "bend")
    os.makedirs(d, exist_ok=True)
    key = hashlib.sha256(source.encode()).hexdigest()
    binp = os.path.join(d, key + ".bin")
    if os.path.exists(binp):
        return binp, key, False
    src = os.path.join(d, key + ".bend")
    with open(src, "w") as f:
        f.write(source)
    env = dict(os.environ, BEND_NO_TELEMETRY="1", PATH=os.path.expanduser("~/.bun/bin") + ":" + os.environ.get("PATH", ""))
    r = subprocess.run([BEND, src, "-o", binp + ".tmp"], capture_output=True, text=True, env=env, cwd=d, timeout=600)
    if r.returncode != 0 or not os.path.exists(binp + ".tmp"):
        raise RuntimeError("bend refused the emitted program: %s" % (r.stdout + r.stderr)[:600])
    os.replace(binp + ".tmp", binp)
    return binp, key, True


class BendStep(CompiledStep):
    """One world's Bend epoch step; the same encode/decode/control as CompiledStep, the step run as a process per call."""

    def __init__(self, view, sem_id=""):
        self.view = view
        self.fields, self.width = slot_map(view)
        self.ctrl, self.orbs = control_layout(view)
        self.source = emit_step_bend(view)
        self.backend_id = backend_id(sem_id, self.source)
        self.bin_path, self.source_sha256, self.built_now = build(self.source)
        import ctypes
        self._Arr = ctypes.c_int64 * self.width
        self._Ctl = ctypes.c_int64 * (5 * len(self.ctrl) + len(self.orbs))
        self.last_wall_s = None

    def run_raw(self, st_list, ctl_list, reps=1):
        env = dict(os.environ, TRVM_ST=" ".join(str(int(v)) for v in st_list), TRVM_CTL=" ".join(str(int(v)) for v in ctl_list) or "0", TRVM_REPS=str(reps))
        import time
        t0 = time.perf_counter()
        r = subprocess.run([self.bin_path], capture_output=True, text=True, env=env, timeout=600)
        self.last_wall_s = time.perf_counter() - t0
        if r.returncode != 0:
            raise RuntimeError("bend step failed rc=%d: %s" % (r.returncode, (r.stdout + r.stderr)[:300]))
        vals = [int(x) for x in r.stdout.split()]
        if len(vals) != self.width:
            raise RuntimeError("bend step returned %d slots, expected %d" % (len(vals), self.width))
        return vals

    def step(self, st, cfg_map, resets=None):
        a, c = self.encode(st), self.control(cfg_map, resets)
        vals = self.run_raw(list(a), list(c))
        out = self._Arr()
        for i, v in enumerate(vals):
            out[i] = v
        return self.decode(out)
