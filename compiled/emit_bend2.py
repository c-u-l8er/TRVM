"""emit_bend2.py -- the Bend backend, second representation: bit-packed signal state and a branch-free MAC.

`emit_bend.py` (v1) carries one list cons per slot and a sign-magnitude MAC through helper calls; measured on 2026-09-18
(`FOUNDATION_LANE.md` §3au) the list rebuild alone was the whole cost on the wired worlds (chain120: 3.5 us of 3.0-6.6 us
per epoch, ~7 ns per cons) and the MAC helpers two thirds of the Golden demo's. This emitter keeps the LAWS and the oracle
and changes only the representation:

  * every wire, door and relay bit (cur and nxt) lives in a U32 word -- positions are assigned by walking each signal
    chain from its pulser so that a chain's `nxt' = input's nxt` and `wire' = relay's hot` laws become ONE masked shift
    per (source word, target word, displacement) run; `cur' = nxt` is a word copy. chain120's 485 slots become 17 words.
  * the wide-MAC is branch-free per term: each signed lane a is carried as ua = a + half (mod full) -- one U32 xor of
    the top bit, no division -- so a_i*b_j = ua_i*ub_j - half*(ua_i + ub_j) + half^2, and the four-term accumulator is
    two non-negative Nat sums P (the positive parts) and N (the negative parts) handed to `fin((P, N), ...)`, v1's tail
    unchanged: one sign test, one toward-zero quotient, one saturation, one re-encoding. No bias, no per-term helper,
    no division before the quotient; P <= 2^(2w+2) bounds the admitted width at 23 (v1: 24; the C step: 63). The
    (lane, overflow) unpacking uses a comparison and a subtraction instead of v1's two divisions.
Everything else -- the counters, the COMMIT-then-REACT order, the sticky fault, saturation and toward-zero rounding, the
control walk, the I/O strings -- is v1's. Identity: `bbknd2-` + sha256(SemanticArtifactID + `compiled.bend.step.v2` + source).
The slot vector the battery speaks (`emit_c.slot_map` order) is packed and unpacked on the Python side by the same layout
function the emitter uses, so the oracle sees exactly the same state dicts.
"""
import hashlib
import os

from emit_c import slot_map, control_layout
from emit_bend import lit, build, BendStep

PROFILE = "compiled.bend.step.v2"
MAX_LANE_WIDTH = 23   # P, N <= 2^(2w+2) must fit the 48-bit Nat
WORD = 32


def signal_layout(view, word=WORD):
    """Bit positions for every wire/door/relay object: chains from each pulser get consecutive positions
    (wire, relay, wire, relay, ...) so that the two wire laws are +1 / -1 displacements; leftovers follow state_layout."""
    ppl, wires, doors, relays = view.layout()
    src_of, targets_of = {}, {}
    for role in list(ppl) + list(relays):
        for wr in view.out_wires(role):
            src_of[wr] = role
    for d in list(doors) + list(relays):
        for wr in view.in_wires(d):
            targets_of.setdefault(wr, []).append(d)
    pos, order = {}, []

    def take(name):
        if name not in pos:
            pos[name] = len(order)
            order.append(name)

    def walk_wire(wr):
        if wr in pos:
            return
        take(wr)
        for d in targets_of.get(wr, []):
            if d in pos:
                continue
            take(d)
            for wr2 in view.out_wires(d) if d in relays else ():
                walk_wire(wr2)
    for p in ppl:
        for wr in view.out_wires(p):
            walk_wire(wr)
    for name in list(wires) + list(doors) + list(relays):
        take(name)
    nwords = (len(order) + word - 1) // word
    return pos, nwords


def packed_layout(view, word=WORD):
    """The packed list: [(kind, name, slot_offset_in_C_vector, nslots)] for the non-signal fields, plus the word counts.
    Order: counters, CUR words, NXT words, then pose/fault/rotor fields in state_layout order."""
    fields, width = slot_map(view)
    pos, nwords = signal_layout(view, word)
    packed = []
    for kind, name, o, n, spec in fields:
        if kind == "counter":
            packed.append((kind, name, o, n, spec))
    packed.append(("cur", None, None, nwords, None))
    packed.append(("nxt", None, None, nwords, None))
    for kind, name, o, n, spec in fields:
        if kind in ("pose", "fault", "rotor"):
            packed.append((kind, name, o, n, spec))
    return fields, width, pos, nwords, packed, word


def pack_vector(view, a, layout=None):
    """C slot vector -> packed Nat list."""
    fields, width, pos, nwords, packed, word = layout or packed_layout(view)
    cur, nxt = [0] * nwords, [0] * nwords
    for kind, name, o, n, spec in fields:
        if kind in ("wire", "door", "relay"):
            p = pos[name]
            cur[p // word] |= int(a[o]) << (p % word)
            nxt[p // word] |= int(a[o + 1]) << (p % word)
    out = []
    for kind, name, o, n, spec in packed:
        if kind == "cur":
            out += cur
        elif kind == "nxt":
            out += nxt
        else:
            out += [int(a[o + i]) for i in range(n)]
    return out


def unpack_vector(view, vals, layout=None):
    """Packed Nat list -> C slot vector (a list of ints)."""
    fields, width, pos, nwords, packed, word = layout or packed_layout(view)
    a, i = [0] * width, 0
    cur = nxt = None
    for kind, name, o, n, spec in packed:
        if kind == "cur":
            cur = vals[i:i + n]
        elif kind == "nxt":
            nxt = vals[i:i + n]
        else:
            for k in range(n):
                a[o + k] = int(vals[i + k])
        i += n
    for kind, name, o, n, spec in fields:
        if kind in ("wire", "door", "relay"):
            p = pos[name]
            a[o] = (cur[p // word] >> (p % word)) & 1
            a[o + 1] = (nxt[p // word] >> (p % word)) & 1
    return a


import laws as LAW

HELPERS = LAW.render("bend2", "mac")   # the unmutated text, for readers; emit_step_bend2 renders it afresh


def emit_step_bend2(view):
    fields, width, pos, nwords, packed, _word = packed_layout(view)
    spec = {n: s for k, n, _, _, s in fields if k == "counter"}
    ppl, wires, doors, relays = view.layout()
    orbs = list(view.orbs)
    ctrl, _ = control_layout(view)
    for s in view.spinners:
        w_ = view.spinners[s][0]
        if not (1 <= w_ <= MAX_LANE_WIDTH):
            raise ValueError("emit_bend2: lane width %d of spinner %s is outside 1..%d (the biased accumulator must fit 48 bits)" % (w_, s, MAX_LANE_WIDTH))
    # packed slot indices
    idx, i = {}, 0
    for kind, name, o, n, sp in packed:
        idx[(kind, name)] = i
        i += n
    pw = i
    cw = 5 * len(ctrl) + len(orbs)
    L = ["# generated by TRVM compiled/emit_bend2.py -- profile %s -- do not edit" % PROFILE, "import Base", LAW.render("bend2", "mac")]
    emit = L.append
    s_pat = "".join("Con{+s%d, " % k for k in range(pw)) + "_" + "}" * pw
    c_pat = ("".join("Con{+c%d, " % k for k in range(cw)) + "_" + "}" * cw) if cw else "_"
    emit("def step(xs: List<&2, Nat>, cs: List<&2, Nat>) -> List<&2, Nat>:")
    emit("  match xs cs:")
    emit("    case %s %s:" % (s_pat, c_pat))
    cur0, nxt0 = idx[("cur", None)], idx[("nxt", None)]
    L += LAW.render("bend2", "nxt-words", nwords=nwords, cur0=cur0, nxt0=nxt0)
    # ---- clocks: a Bool fire per pulser, its U32 bit, the next count (laws.py)
    fire_u = {}
    for r in ppl:
        sp, o = spec[r], idx[("counter", r)]
        if sp[0] == "onehot":
            _, p, ph = sp
            L += LAW.render("bend2", "clock-onehot", o=o, p=p, ph=ph, r=r)
        elif sp[0] == "binp":
            _, p, ph, w_ = sp
            L += LAW.render("bend2", "clock-binary", o=o, p=p, ph=ph, w=w_, r=r)
        else:
            _, e, w_ = sp
            L += LAW.render("bend2", "clock-once", o=o, e=e, w=w_, r=r)
        if view.out_wires(r):
            emit("      +fu_%d = Bool.to_u32(fb_%d)" % (o, o))
            fire_u[r] = "fu_%d" % o
    # ---- the signal words: NXT' from runs of (source word, target word, displacement); CUR' = NXT
    edges = []       # (src_word, src_bit, dst_word, dst_bit)
    fires = []       # (dst_word, dst_bit, fire expr)
    src_of = {}
    for role in list(ppl) + list(relays):
        for wr in view.out_wires(role):
            src_of[wr] = role
    for wr in wires:
        p = pos[wr]
        s = src_of[wr]
        if s in ppl:
            fires.append((p // WORD, p % WORD, fire_u[s]))
        else:
            q = pos[s]
            edges.append((q // WORD, q % WORD, p // WORD, p % WORD))
    for d in list(doors) + list(relays):
        ins = view.in_wires(d)
        for wr in ins:                      # WRL admits one signal wire per object; a second would OR in
            q, p = pos[wr], pos[d]
            edges.append((q // WORD, q % WORD, p // WORD, p % WORD))
    runs = {}
    for sw, sb, dw, db in edges:
        runs.setdefault((sw, dw, db - sb), 0)
        runs[(sw, dw, db - sb)] |= 1 << sb
    for k in range(nwords):
        parts = []
        for (sw, dw, disp), mask in sorted(runs.items()):
            if dw != k:
                continue
            if disp >= 0:
                parts.append("U32.shln(U32.and(n%d, %d), %dn)" % (sw, mask, disp))
            else:
                parts.append("U32.shrn(U32.and(n%d, %d), %dn)" % (sw, mask, -disp))
        for dw, db, fexpr in fires:
            if dw == k:
                parts.append("U32.shln(%s, %dn)" % (fexpr, db))
        expr = "0" if not parts else parts[0]
        for p_ in parts[1:]:
            expr = "U32.or(%s, %s)" % (expr, p_)
        L += LAW.render("bend2", "signal-word", k=k, cur0=cur0, nxt0=nxt0, expr=expr if parts else "{0 : U32}")
    # ---- orbs: COMMIT reset and rotor, then the biased MAC, REACT if the spinner's input fires
    for i_, ob in enumerate(orbs):
        po, fo = idx[("pose", ob)], idx[("fault", ob)]
        reset_slot = 5 * len(ctrl) + i_
        emit("      # orb %s" % ob)
        L += LAW.render("bend2", "commit-fault-reset", fo=fo, reset_slot=reset_slot)
        s = view.controller_of(ob)
        if not s:
            L += LAW.render("bend2", "orb-uncontrolled", po=po, fo=fo)
            continue
        w_, n_, _ = view.spinners[s]
        ro, ci = idx[("rotor", s)], 5 * ctrl.index(s)
        L += LAW.render("bend2", "commit-rotor", po=po, ro=ro, ci=ci, w=w_, n=n_)
        ins = view.in_wires(s)
        sel = "n%d, %dn" % (pos[ins[0]] // WORD, pos[ins[0]] % WORD) if ins else None
        L += LAW.render("bend2", "react", po=po, fo=fo, s=s, sel=sel)
    emit("      [%s]" % ", ".join("o%d" % k for k in range(pw)))
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
    return "\n".join(L) + "\n", pw


def backend_id(sem_id, source):
    return "bbknd2-" + hashlib.sha256((sem_id + "\n" + PROFILE + "\n" + source).encode()).hexdigest()


class BendStep2(BendStep):
    """v2: the packed representation on the wire, the C slot vector to the battery."""

    def __init__(self, view, sem_id=""):
        self.view = view
        self.fields, self.width = slot_map(view)
        self.ctrl, self.orbs = control_layout(view)
        self.layout = packed_layout(view)
        self.source, self.packed_width = emit_step_bend2(view)
        self.backend_id = backend_id(sem_id, self.source)
        self.bin_path, self.source_sha256, self.built_now = build(self.source)
        import ctypes
        self._Arr = ctypes.c_int64 * self.width
        self._Ctl = ctypes.c_int64 * (5 * len(self.ctrl) + len(self.orbs))
        self.last_wall_s = None

    def run_raw(self, st_list, ctl_list, reps=1):
        """Takes and returns C slot vectors; packs and unpacks around the process."""
        return unpack_vector(self.view, self._run_packed(pack_vector(self.view, st_list, self.layout), ctl_list, reps), self.layout)

    def _run_packed(self, packed, ctl_list, reps):
        import subprocess, time
        env = dict(os.environ, TRVM_ST=" ".join(str(int(v)) for v in packed), TRVM_CTL=" ".join(str(int(v)) for v in ctl_list) or "0", TRVM_REPS=str(reps))
        t0 = time.perf_counter()
        r = subprocess.run([self.bin_path], capture_output=True, text=True, env=env, timeout=600)
        self.last_wall_s = time.perf_counter() - t0
        if r.returncode != 0:
            raise RuntimeError("bend step failed rc=%d: %s" % (r.returncode, (r.stdout + r.stderr)[:300]))
        vals = [int(x) for x in r.stdout.split()]
        if len(vals) != self.packed_width:
            raise RuntimeError("bend step returned %d packed slots, expected %d" % (len(vals), self.packed_width))
        return vals
