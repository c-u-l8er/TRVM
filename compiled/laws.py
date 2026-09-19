"""laws.py -- the WRL epoch-step laws, stated ONCE, with their renderings and their mutants (T7, `SUPER_BUILDS_LANE.md`).

Until 2026-09-19 the compiled backend carried the laws of Forge's `compile_step_v6` and `binlib.golden_rot_forge` as four
hand transcriptions (`emit_c.py`, `emit_c2.py`, `emit_bend.py`, `emit_bend2.py`) and the battery's mutants as string edits
against each emitter's Python. `OBSERVER_LAWS_PROPOSAL.md` §0 made the observation this file rests on: every mutant is a
law with one clause flipped. So here a LAW is a statement plus the clauses it owns and the flips that falsify it; a
RENDERER is one backend's text for one block of the step, reading the clauses; a MUTANT is `(law id, name)` and is the
same flip in every backend that renders the clause. The emitters keep the layout walk (slots, words, wires) and call
`render(backend, block, **fields)` for every law-bearing line. `laws_gate.py` holds every emitted byte fixed across this
change: a law's rendering is its identity, and the identities of unchanged laws did not move (`identities.json`).

What is NOT a law here: a representation choice a single emitter makes (packed words, the i64/i128 MAC paths, Bend's
biased MAC, the affine list) -- those mutants stay in the emitter's own battery list, named as representation mutants.
"""
from contextlib import contextmanager

from binlib import HAMILTON


class Law:
    def __init__(self, id, statement, mutants, blocks):
        self.id, self.statement, self.mutants, self.blocks = id, statement, mutants, blocks


def _args(fn):
    return {"args": fn}


def _clause(name, value):
    return {"clause": name, "value": value}


LAWS = [
    Law("clock-onehot", "A one-hot pulser fires in the epoch its count equals its phase; the count advances modulo the period.",
        {"onehot-phase-off-by-one": _args(lambda f: dict(f, ph=(f["ph"] + 1) % f["p"]))}, ["clock-onehot"]),
    Law("clock-binary", "A binary pulser fires when its count equals its phase; the count advances in its width and wraps to 0 at the period.",
        {"binary-phase-off-by-one": _args(lambda f: dict(f, ph=(f["ph"] + 1) % f["p"]))}, ["clock-binary"]),
    Law("clock-once", "A once pulser fires in exactly one epoch: when it has not fired and its count equals the epoch; firing latches `done`.",
        {"once-no-latch": _clause("latch", False)}, ["clock-once"]),
    Law("hot-pulser", "A pulser's hot signal is its fire.", {}, ["hot-pulser"]),
    Law("hot-relay", "A relay's hot signal is its NXT bit (the value it will present), not its CUR.",
        {"relay-hot-from-cur": _clause("relay_hot", "cur")}, ["hot-relay"]),
    Law("wire-advance", "A wire's (CUR', NXT') is (NXT, source hot): what was next is now current, and the source's hot is next.",
        {"wire-cur-stale": _clause("cur_from", "cur")}, ["wire"]),
    Law("sink-input", "A door's or relay's NXT' is the OR of its input wires' NXT; its CUR' is its NXT.", {}, ["sink"]),
    Law("commit-fault-reset", "COMMIT first: a ResetFault claim clears the orb's fault before anything reacts.",
        {"reset-ignored": _clause("reset", "ignored")}, ["commit-fault-reset"]),
    Law("orb-uncontrolled", "An orb with no controlling spinner keeps its pose; its fault is the committed one.", {}, ["orb-uncontrolled"]),
    Law("commit-rotor", "COMMIT the rotor: SetRotor replaces all four lanes, NoChange keeps the stored rotor; the committed rotor is stored.", {}, ["commit-rotor"]),
    Law("react-only-if-fires", "REACT only in an epoch where the spinner's input fires; otherwise the pose is unchanged.",
        {"react-without-fire": _clause("guard", "always")}, ["react"]),
    Law("react-uses-committed-rotor", "REACT rotates the old pose by the COMMITTED rotor of this epoch, never the stored one.",
        {"react-before-commit": _clause("rotor", "old")}, ["react"]),
    Law("sticky-fault", "A numeric fault latches: fault' = committed fault OR this epoch's overflow.",
        {"fault-not-sticky": _clause("sticky", False)}, ["react"]),
    Law("mac-exact-products", "Each Hamilton term is the exact product of two sign-extended w-bit lanes; the four terms sum exactly.", {}, ["mac"]),
    Law("mac-toward-zero-shift", "ONE quotient by 2^n, rounded toward zero (not floor), after the exact sum.",
        {"floor-shift": _clause("shift", "floor")}, ["mac"]),
    Law("mac-saturation", "ONE saturation of the quotient to the w-bit signed range; the overflow flag is whether it saturated.",
        {"no-saturation": _clause("saturate", False)}, ["mac"]),
]
BY_ID = {l.id: l for l in LAWS}
MUTANTS = [(l.id, m) for l in LAWS for m in l.mutants]           # (law id, mutant name), the battery's derived list

ACTIVE = None      # (law id, mutant name) while a mutant is installed


@contextmanager
def mutant(law_id, name):
    """Install one law's mutant for every render call in the block; nothing outside the block changes."""
    global ACTIVE
    if name not in BY_ID[law_id].mutants:
        raise KeyError("law %s has no mutant %s" % (law_id, name))
    prev, ACTIVE = ACTIVE, (law_id, name)
    try:
        yield
    finally:
        ACTIVE = prev


def clause(name, default):
    """The value of a clause: the installed mutant's, if it flips this clause, else the law's."""
    if ACTIVE:
        m = BY_ID[ACTIVE[0]].mutants[ACTIVE[1]]
        if m.get("clause") == name:
            return m["value"]
    return default


def _fields(block, f):
    if ACTIVE:
        law, m = BY_ID[ACTIVE[0]], BY_ID[ACTIVE[0]].mutants[ACTIVE[1]]
        if "args" in m and block in law.blocks:
            return m["args"](f)
    return f


def render(backend, block, **f):
    """The lines of one block of the step in one backend, under the laws (or under the installed mutant)."""
    return RENDER[backend][block](_fields(block, f))


# ---------------------------------------------------------------------------------------------- C, profile v1 (emit_c.py)
def _c_clock_onehot(f):
    o, p, ph, r = f["o"], f["p"], f["ph"], f["r"]
    return ["  /* pulser %s: one-hot period %d phase %d */" % (r, p, ph),
            "  const i64 c_%d = st[%d];" % (o, o),
            "  const int fire_%d = (c_%d == %d); /* one-hot */" % (o, o, ph),
            "  out[%d] = (c_%d + 1) %% %d;" % (o, o, p)]


def _c_clock_binary(f):
    o, p, ph, w, r = f["o"], f["p"], f["ph"], f["w"], f["r"]
    return ["  /* pulser %s: binary period %d phase %d width %d */" % (r, p, ph, w),
            "  const i64 c_%d = st[%d];" % (o, o),
            "  const int fire_%d = (c_%d == %d); /* binary */" % (o, o, ph),
            "  { const i64 sum = (c_%d + 1) & %d; out[%d] = (sum == %d) ? 0 : sum; }" % (o, (1 << w) - 1, o, p)]


def _c_clock_once(f):
    o, e, w, r = f["o"], f["e"], f["w"], f["r"]
    fire = "(!done_%d && k_%d == %d)" % (o, o, e) if clause("latch", True) else "(k_%d == %d)" % (o, e)
    return ["  /* pulser %s: once at %d width %d (done, k) */" % (r, e, w),
            "  const i64 done_%d = st[%d], k_%d = st[%d];" % (o, o, o, o + 1),
            "  const int fire_%d = %s;" % (o, fire),
            "  out[%d] = done_%d || fire_%d; out[%d] = (k_%d + 1) & %d;" % (o, o, o, o + 1, o, (1 << w) - 1)]


def _c_hot_pulser(f):
    return ["  const int hot_%s = fire_%d;" % (f["cid"], f["o"])]


def _c_hot_relay(f):
    o = f["o"] + (1 if clause("relay_hot", "nxt") == "nxt" else 0)
    return ["  const int hot_%s = (int)st[%d]; /* relay %s nxt */" % (f["cid"], o, f["r"])]


def _c_wire(f):
    o = f["o"]
    cur = o + 1 if clause("cur_from", "nxt") == "nxt" else o
    return ["  out[%d] = st[%d]; out[%d] = hot_%s; /* wire %s */" % (o, cur, o + 1, f["cid"], f["wr"])]


def _c_sink(f):
    o = f["o"]
    return ["  out[%d] = st[%d]; out[%d] = %s; /* %s %s */" % (o, o + 1, o + 1, f["merged"], f["kind"], f["name"])]


def _c_commit_fault_reset(f):
    rs, fo = f["reset_slot"], f["fo"]
    expr = "ctl[%d] ? 0 : (int)st[%d]" % (rs, fo) if clause("reset", "honoured") == "honoured" else "(ctl[%d], (int)st[%d])" % (rs, fo)
    return ["    const int fbase = %s; /* COMMIT fault reset */" % expr]


def _c_orb_uncontrolled(f):
    po, fo = f["po"], f["fo"]
    return ["    out[%d] = st[%d]; out[%d] = st[%d]; out[%d] = st[%d]; out[%d] = st[%d]; out[%d] = fbase; /* no controller */"
            % (po, po, po + 1, po + 1, po + 2, po + 2, po + 3, po + 3, fo)]


def _c_commit_rotor(f):
    ro, po, ci = f["ro"], f["po"], f["ci"]
    return ["    const i64 *old_rotor = &st[%d]; const i64 *old_pose = &st[%d];" % (ro, po),
            "    i64 eff[4]; /* COMMIT rotor config: SetRotor replaces, NoChange keeps */",
            "    for (int l = 0; l < 4; l++) eff[l] = ctl[%d] ? ctl[%d + l] : old_rotor[l];" % (ci, ci + 1),
            "    for (int l = 0; l < 4; l++) out[%d + l] = eff[l];" % ro]


def _c_react(f):
    po, fo, w, n, s = f["po"], f["fo"], f["w"], f["n"], f["s"]
    guard = "sel" if clause("guard", "fires") == "fires" else "1"
    rotor = "eff" if clause("rotor", "committed") == "committed" else "old_rotor"
    fault = "fbase | ov" if clause("sticky", True) else "ov"
    return ["    const int sel = %s; /* spinner %s merged input */" % (f["sel"], s),
            "    if (%s) { /* REACT over the committed rotor */" % guard,
            "      const int ov = rot_forge(%d, %d, %s, old_pose, &out[%d]);" % (w, n, rotor, po),
            "      out[%d] = %s; /* sticky fault */" % (fo, fault),
            "    } else {",
            "      for (int l = 0; l < 4; l++) out[%d + l] = old_pose[l];" % po,
            "      out[%d] = fbase;" % fo,
            "    }"]


def _ham(which):
    k = {"sg": 0, "i": 1, "j": 2}[which]
    return ", ".join("{%s}" % ", ".join(str(t[k]) for t in row) for row in HAMILTON)


def _c_mac(f):
    """sx, the HAMILTON tables, mac_row (exact i128 products, ONE toward-zero shift, ONE saturation) and rot_forge."""
    shift = "acc >= 0 ? (acc >> n) : -((-acc) >> n)" if clause("shift", "toward-zero") == "toward-zero" else "acc >> n"
    sat = "q < lo ? lo : (q > hi ? hi : q)" if clause("saturate", True) else "q"
    return ["/* sign-extend a w-bit lane (w <= 63) in i128 so that 1 << w never overflows i64 */",
            "static inline i128 sx(i64 v, int w) { i128 x = v; return x >= ((i128)1 << (w - 1)) ? x - ((i128)1 << w) : x; }",
            "/* HAMILTON rows from binlib: out[c] = sum sign * rotor[i] * pose[j] */",
            "static const int8_t HAM_SG[4][4] = {%s};" % _ham("sg"),
            "static const int8_t HAM_I[4][4] = {%s};" % _ham("i"),
            "static const int8_t HAM_J[4][4] = {%s};" % _ham("j"),
            "/* golden_mac: full-precision products, ONE toward-zero shift, ONE saturation; returns the overflow flag */",
            "static int mac_row(int w, int n, int c, const i64 *rotor, const i64 *pose, i64 *out) {",
            "  i128 acc = 0;",
            "  for (int k = 0; k < 4; k++) acc += (i128)HAM_SG[c][k] * (sx(rotor[HAM_I[c][k]], w) * sx(pose[HAM_J[c][k]], w)); /* i128 products */",
            "  i128 q = %s;" % shift,
            "  i128 lo = -((i128)1 << (w - 1)), hi = ((i128)1 << (w - 1)) - 1;",
            "  int ov = !(lo <= q && q <= hi);",
            "  i128 s = %s;" % sat,
            "  *out = (i64)(s & (((i128)1 << w) - 1));",
            "  return ov;",
            "}",
            "/* golden_rot_forge: (4 lanes, fault) */",
            "static int rot_forge(int w, int n, const i64 *rotor, const i64 *pose, i64 *out) {",
            "  int fault = 0;",
            "  for (int c = 0; c < 4; c++) fault |= mac_row(w, n, c, rotor, pose, &out[c]);",
            "  return fault;",
            "}"]


RENDER = {
    "c": {"clock-onehot": _c_clock_onehot, "clock-binary": _c_clock_binary, "clock-once": _c_clock_once, "hot-pulser": _c_hot_pulser,
          "hot-relay": _c_hot_relay, "wire": _c_wire, "sink": _c_sink, "commit-fault-reset": _c_commit_fault_reset,
          "orb-uncontrolled": _c_orb_uncontrolled, "commit-rotor": _c_commit_rotor, "react": _c_react, "mac": _c_mac},
}

# ---------------------------------------------------------------------------------------------- C, profile v2 (emit_c2.py)
# The packed representation: signal bits live in 64-bit words, so `wire-advance` is a word copy and `hot-relay` /
# `sink-input` are reads of the NXT words; the two laws' flips therefore touch every signal bit at once (the old
# representation mutants `cur-not-advanced` and `nxt-from-cur-words` were exactly those flips, and are now derived).
def _c2_clock_onehot(f):
    o, p, ph, r = f["o"], f["p"], f["ph"], f["r"]
    return ["  /* pulser %s: one-hot period %d phase %d */" % (r, p, ph),
            "  const int fire_%d = (st[%d] == %d); /* one-hot */" % (o, o, ph),
            "  out[%d] = (st[%d] + 1) %% %d;" % (o, o, p)]


def _c2_clock_binary(f):
    o, p, ph, w, r = f["o"], f["p"], f["ph"], f["w"], f["r"]
    return ["  /* pulser %s: binary period %d phase %d width %d */" % (r, p, ph, w),
            "  const int fire_%d = (st[%d] == %d); /* binary */" % (o, o, ph),
            "  { const i64 sum = (st[%d] + 1) & %d; out[%d] = (sum == %d) ? 0 : sum; }" % (o, (1 << w) - 1, o, p)]


def _c2_clock_once(f):
    o, e, w, r = f["o"], f["e"], f["w"], f["r"]
    fire = "(!st[%d] && st[%d] == %d)" % (o, o + 1, e) if clause("latch", True) else "(st[%d] == %d)" % (o + 1, e)
    return ["  /* pulser %s: once at %d width %d (done, k) */" % (r, e, w),
            "  const int fire_%d = %s;" % (o, fire),
            "  out[%d] = st[%d] || fire_%d; out[%d] = (st[%d] + 1) & %d;" % (o, o, o, o + 1, o + 1, (1 << w) - 1)]


def _c2_nxt_words(f):
    """The NXT words every signal read comes from (hot-relay and sink-input in packed form)."""
    base = f["nxt0"] if clause("relay_hot", "nxt") == "nxt" else f["cur0"]
    return ["  const u64 n%d = (u64)st[%d]; /* NXT word %d */" % (k, base + k, k) for k in range(f["nwords"])]


def _c2_signal_word(f):
    """Word k: CUR' = NXT (wire-advance), NXT' = the OR of the shifted runs and fires (sink-input / wire-advance)."""
    k, cur0, nxt0 = f["k"], f["cur0"], f["nxt0"]
    src = nxt0 if clause("cur_from", "nxt") == "nxt" else cur0
    return ["  out[%d] = st[%d]; /* CUR word %d <- NXT */" % (cur0 + k, src + k, k),
            "  out[%d] = (i64)(%s); /* NXT word %d */" % (nxt0 + k, f["expr"], k)]


def _c2_mac(f):
    """sx in i128, the HAMILTON tables, the MAC on two paths (i128 rows for w > 31, exact i64 rows for w <= 31), rot_forge."""
    shift128 = "acc >= 0 ? (acc >> n) : -((-acc) >> n)" if clause("shift", "toward-zero") == "toward-zero" else "acc >> n"
    shift64 = shift128
    sat128 = "q < lo ? lo : (q > hi ? hi : q)" if clause("saturate", True) else "q"
    sat64 = sat128
    return ["static inline i128 sx(i64 v, int w) { i128 x = v; return x >= ((i128)1 << (w - 1)) ? x - ((i128)1 << w) : x; }",
            "static const int8_t HAM_SG[4][4] = {%s};" % _ham("sg"),
            "static const int8_t HAM_I[4][4] = {%s};" % _ham("i"),
            "static const int8_t HAM_J[4][4] = {%s};" % _ham("j"),
            "static inline int mac_row128(int w, int n, int c, const i64 *rotor, const i64 *pose, i64 *out) {",
            "  i128 acc = 0;",
            "  for (int k = 0; k < 4; k++) acc += (i128)HAM_SG[c][k] * (sx(rotor[HAM_I[c][k]], w) * sx(pose[HAM_J[c][k]], w)); /* i128 products */",
            "  i128 q = %s;" % shift128,
            "  i128 lo = -((i128)1 << (w - 1)), hi = ((i128)1 << (w - 1)) - 1;",
            "  int ov = !(lo <= q && q <= hi);",
            "  i128 s = %s;" % sat128,
            "  *out = (i64)(s & (((i128)1 << w) - 1));",
            "  return ov;",
            "}",
            "/* w <= 31: |a*b| <= 2^(2w-2) and |acc| <= 2^(2w) <= 2^62 fit i64 exactly -- the same law in 64-bit arithmetic */",
            "static inline i64 sx64(i64 v, int w) { return v >= ((i64)1 << (w - 1)) ? v - ((i64)1 << w) : v; }",
            "static inline int mac_row64(int w, int n, int c, const i64 *rotor, const i64 *pose, i64 *out) {",
            "  i64 acc = 0;",
            "  for (int k = 0; k < 4; k++) acc += (i64)HAM_SG[c][k] * (sx64(rotor[HAM_I[c][k]], w) * sx64(pose[HAM_J[c][k]], w)); /* i64 products */",
            "  i64 q = %s;" % shift64,
            "  i64 lo = -((i64)1 << (w - 1)), hi = ((i64)1 << (w - 1)) - 1;",
            "  int ov = !(lo <= q && q <= hi);",
            "  i64 s = %s;" % sat64,
            "  *out = s & (((i64)1 << w) - 1);",
            "  return ov;",
            "}",
            "static inline int rot_forge(int w, int n, const i64 *rotor, const i64 *pose, i64 *out) {",
            "  int fault = 0;",
            "  if (w <= 31) { for (int c = 0; c < 4; c++) fault |= mac_row64(w, n, c, rotor, pose, &out[c]); }",
            "  else { for (int c = 0; c < 4; c++) fault |= mac_row128(w, n, c, rotor, pose, &out[c]); }",
            "  return fault;",
            "}"]


def _c2_react(f):
    """C v2's react block: the input is one bit of a NXT word (or absent), the rest is C v1's block."""
    sel = "    const int sel = %s; /* spinner %s input fires */" % (f["sel"], f["s"]) if f["sel"] != "0" else "    const int sel = 0;"
    return [sel] + _c_react(f)[1:]


RENDER["c2"] = {"clock-onehot": _c2_clock_onehot, "clock-binary": _c2_clock_binary, "clock-once": _c2_clock_once,
                "nxt-words": _c2_nxt_words, "signal-word": _c2_signal_word, "commit-fault-reset": _c_commit_fault_reset,
                "orb-uncontrolled": _c_orb_uncontrolled, "commit-rotor": _c_commit_rotor, "react": _c2_react, "mac": _c2_mac}
# in the packed form hot-relay and sink-input are one read, wire-advance one copy: the blocks those laws own
BY_ID["hot-relay"].blocks.append("nxt-words")
BY_ID["sink-input"].blocks.append("nxt-words")
BY_ID["wire-advance"].blocks.append("signal-word")

# ---------------------------------------------------------------------------------------------- Bend, profile v1 (emit_bend.py)
# Sign-magnitude MAC over Nat: the toward-zero law is the magnitude's floor, so its flip renders as rounding the negative
# side AWAY from zero (the old `neg-round-away`); saturation's flip wraps the quotient modulo the lane instead of clamping.
def _b_lit(n):
    from emit_bend import lit
    return lit(n)


def _b_clock_onehot(f):
    o, p, ph, r = f["o"], f["p"], f["ph"], f["r"]
    return ["      # pulser %s: one-hot period %d phase %d" % (r, p, ph),
            "      +fire_%d = b2n(Nat.is_eq(s%d, %s))" % (o, o, _b_lit(ph)),
            "      o%d = Nat.mod((s%d + 1n : Nat), %s)" % (o, o, _b_lit(p))]


def _b_clock_binary(f):
    o, p, ph, w, r = f["o"], f["p"], f["ph"], f["w"], f["r"]
    return ["      # pulser %s: binary period %d phase %d width %d" % (r, p, ph, w),
            "      +fire_%d = b2n(Nat.is_eq(s%d, %s))" % (o, o, _b_lit(ph)),
            "      +sum_%d = Nat.mod((s%d + 1n : Nat), %s)" % (o, o, _b_lit(1 << w)),
            "      o%d = sel(Nat.is_eq(sum_%d, %s), 0n, sum_%d)" % (o, o, _b_lit(p), o)]


def _b_clock_once(f):
    o, e, w, r = f["o"], f["e"], f["w"], f["r"]
    fire = "b2n(Bool.and(Nat.is_eq(s%d, 0n), Nat.is_eq(s%d, %s)))" % (o, o + 1, _b_lit(e)) if clause("latch", True) else "b2n(Nat.is_eq(s%d, %s))" % (o + 1, _b_lit(e))
    return ["      # pulser %s: once at %d width %d (done, k)" % (r, e, w),
            "      +fire_%d = %s" % (o, fire),
            "      o%d = sel(nz((s%d + fire_%d : Nat)), 1n, 0n)" % (o, o, o),
            "      o%d = Nat.mod((s%d + 1n : Nat), %s)" % (o + 1, o + 1, _b_lit(1 << w))]


def _b_hot_pulser(f):
    return ["      +hot_%s = fire_%d" % (f["cid"], f["o"])]


def _b_hot_relay(f):
    o = f["o"] + (1 if clause("relay_hot", "nxt") == "nxt" else 0)
    return ["      +hot_%s = s%d  # relay %s nxt" % (f["cid"], o, f["r"])]


def _b_wire(f):
    o = f["o"]
    cur = o + 1 if clause("cur_from", "nxt") == "nxt" else o
    return ["      o%d = s%d" % (o, cur), "      o%d = hot_%s  # wire %s" % (o + 1, f["cid"], f["wr"])]


def _b_sink(f):
    o = f["o"]
    return ["      o%d = s%d" % (o, o + 1), "      o%d = %s  # %s %s" % (o + 1, f["merged"], f["kind"], f["name"])]


def _b_commit_fault_reset(f):
    fo, rs = f["fo"], f["reset_slot"]
    expr = "sel(nz(c%d), 0n, s%d)" % (rs, fo) if clause("reset", "honoured") == "honoured" else "sel(nz(c%d), s%d, s%d)" % (rs, fo, fo)
    return ["      +fbase_%d = %s  # COMMIT fault reset" % (fo, expr)]


def _b_orb_uncontrolled(f):
    po, fo = f["po"], f["fo"]
    return ["      o%d = s%d" % (po + l, po + l) for l in range(4)] + ["      o%d = fbase_%d  # no controller" % (fo, fo)]


def _b_commit_rotor(f):
    po, ro, ci, w, n = f["po"], f["ro"], f["ci"], f["w"], f["n"]
    out = ["      +full_%d = %s" % (po, _b_lit(1 << w)), "      +half_%d = %s" % (po, _b_lit(1 << (w - 1))),
           "      +hi_%d = %s" % (po, _b_lit((1 << (w - 1)) - 1)), "      +den_%d = %s" % (po, _b_lit(1 << n)),
           "      +set_%d = nz(c%d)" % (po, ci)]
    for l in range(4):
        out.append("      +eff_%d_%d = sel(set_%d, c%d, s%d)  # COMMIT rotor lane %d: SetRotor replaces, NoChange keeps" % (po, l, po, ci + 1 + l, ro + l, l))
        out.append("      o%d = eff_%d_%d" % (ro + l, po, l))
    return out


def _b_react(f):
    po, fo, ro, s, merged = f["po"], f["fo"], f["ro"], f["s"], f["sel"]
    half, full, hi, den = "half_%d" % po, "full_%d" % po, "hi_%d" % po, "den_%d" % po
    guard = "nz(%s)" % merged if clause("guard", "fires") == "fires" else "Bool.or(True{}, nz(%s))" % merged
    out = ["      +sel_%d = %s  # spinner %s merged input" % (po, guard, s)]
    committed = clause("rotor", "committed") == "committed"
    for c in range(4):
        acc = "(0n, 0n)"
        for sg, ii, jj in reversed(HAMILTON[c]):
            rotor = "eff_%d_%d" % (po, ii) if committed else "s%d" % (ro + ii)
            acc = "term(%s, sx(%s, %s, %s), sx(s%d, %s, %s), %s)" % ("True{}" if sg < 0 else "False{}", rotor, half, full, po + jj, half, full, acc)
        out.append("      +x_%d_%d = fin(%s, %s, %s, %s, %s)" % (po, c, acc, den, hi, half, full))
    out.append("      +ov_%d = nz((%s : Nat))" % (po, " + ".join("Nat.div(x_%d_%d, %s)" % (po, c, full) for c in range(4))))
    for c in range(4):
        out.append("      o%d = sel(sel_%d, Nat.mod(x_%d_%d, %s), s%d)  # REACT over the committed rotor" % (po + c, po, po, c, full, po + c))
    fault = "sel(nz((fbase_%d + b2n(ov_%d) : Nat)), 1n, 0n)" % (fo, po) if clause("sticky", True) else "b2n(ov_%d)" % po
    out.append("      o%d = sel(sel_%d, %s, fbase_%d)  # sticky fault" % (fo, po, fault, fo))
    return out


def _b_mac(f):
    """emit_bend.py's HELPERS: sel/b2n/nz, sign-magnitude sx, the term accumulator, and fin (ONE quotient, ONE saturation)."""
    sat = "pack(Nat.min(q, hi), Nat.is_gt(q, hi), full)" if clause("saturate", True) else "pack(Nat.mod(q, full), Nat.is_gt(q, hi), full)"
    neg = "sat_neg(Nat.div((neg - pos : Nat), den), lomag, full)" if clause("shift", "toward-zero") == "toward-zero" else "sat_neg(Nat.div((neg - pos + den - 1n : Nat), den), lomag, full)"
    return """
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
  %s

def enc_neg(+qq: Nat, +full: Nat) -> Nat:
  sel(Nat.is_eq(qq, 0n), 0n, (full - qq : Nat))

def sat_neg(+q: Nat, +lomag: Nat, +full: Nat) -> Nat:
  pack(enc_neg(Nat.min(q, lomag), full), Nat.is_gt(q, lomag), full)

def fin_if(negside: Bool, pos: Nat, neg: Nat, +den: Nat, +hi: Nat, +lomag: Nat, +full: Nat) -> Nat:
  match negside:
    case True{}:
      %s
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
""" % (sat, neg)


RENDER["bend"] = {"clock-onehot": _b_clock_onehot, "clock-binary": _b_clock_binary, "clock-once": _b_clock_once, "hot-pulser": _b_hot_pulser,
                  "hot-relay": _b_hot_relay, "wire": _b_wire, "sink": _b_sink, "commit-fault-reset": _b_commit_fault_reset,
                  "orb-uncontrolled": _b_orb_uncontrolled, "commit-rotor": _b_commit_rotor, "react": _b_react, "mac": _b_mac}

# ---------------------------------------------------------------------------------------------- Bend, profile v2 (emit_bend2.py)
# Packed signal words (as C v2) and the biased branch-free MAC; `fin` -- the toward-zero and saturation laws -- is v1's.
def _b2_clock_onehot(f):
    o, p, ph, r = f["o"], f["p"], f["ph"], f["r"]
    return ["      # pulser %s: one-hot period %d phase %d" % (r, p, ph),
            "      +fb_%d = Nat.is_eq(s%d, %s)" % (o, o, _b_lit(ph)),
            "      o%d = Nat.mod((s%d + 1n : Nat), %s)" % (o, o, _b_lit(p))]


def _b2_clock_binary(f):
    o, p, ph, w, r = f["o"], f["p"], f["ph"], f["w"], f["r"]
    return ["      # pulser %s: binary period %d phase %d width %d" % (r, p, ph, w),
            "      +fb_%d = Nat.is_eq(s%d, %s)" % (o, o, _b_lit(ph)),
            "      +sum_%d = Nat.mod((s%d + 1n : Nat), %s)" % (o, o, _b_lit(1 << w)),
            "      o%d = sel(Nat.is_eq(sum_%d, %s), 0n, sum_%d)" % (o, o, _b_lit(p), o)]


def _b2_clock_once(f):
    o, e, w, r = f["o"], f["e"], f["w"], f["r"]
    fire = "Bool.and(Nat.is_eq(s%d, 0n), Nat.is_eq(s%d, %s))" % (o, o + 1, _b_lit(e)) if clause("latch", True) else "Nat.is_eq(s%d, %s)" % (o + 1, _b_lit(e))
    return ["      # pulser %s: once at %d width %d (done, k)" % (r, e, w),
            "      +fb_%d = %s" % (o, fire),
            "      o%d = sel(Bool.or(nz(s%d), fb_%d), 1n, 0n)" % (o, o, o),
            "      o%d = Nat.mod((s%d + 1n : Nat), %s)" % (o + 1, o + 1, _b_lit(1 << w))]


def _b2_nxt_words(f):
    base = f["nxt0"] if clause("relay_hot", "nxt") == "nxt" else f["cur0"]
    return ["      +n%d = U32.from_nat(s%d)  # NXT word %d" % (k, base + k, k) for k in range(f["nwords"])]


def _b2_signal_word(f):
    k, cur0, nxt0 = f["k"], f["cur0"], f["nxt0"]
    src = nxt0 if clause("cur_from", "nxt") == "nxt" else cur0
    return ["      o%d = s%d  # CUR word %d <- NXT" % (cur0 + k, src + k, k),
            "      o%d = U32.to_nat(%s)  # NXT word %d" % (nxt0 + k, f["expr"], k)]


def _b2_commit_rotor(f):
    """COMMIT the rotor, and bias both operands of the MAC (the rotor operand is the COMMITTED one: react-uses-committed-rotor)."""
    po, ro, ci, w, n = f["po"], f["ro"], f["ci"], f["w"], f["n"]
    half, full, hi, den = 1 << (w - 1), 1 << w, (1 << (w - 1)) - 1, 1 << n
    out = ["      +half_%d = %s" % (po, _b_lit(half)), "      +hu_%d = {%d : U32}" % (po, half), "      +full_%d = %s" % (po, _b_lit(full)),
           "      +hi_%d = %s" % (po, _b_lit(hi)), "      +den_%d = %s" % (po, _b_lit(den)), "      +hsq_%d = (half_%d * half_%d : Nat)" % (po, po, po),
           "      +set_%d = nz(c%d)" % (po, ci)]
    committed = clause("rotor", "committed") == "committed"
    for l in range(4):
        out.append("      +eff_%d_%d = sel(set_%d, c%d, s%d)  # COMMIT rotor lane %d" % (po, l, po, ci + 1 + l, ro + l, l))
        out.append("      o%d = eff_%d_%d" % (ro + l, po, l))
        out.append("      +ua_%d_%d = biased(%s, hu_%d)  # rotor lane + half" % (po, l, "eff_%d_%d" % (po, l) if committed else "s%d" % (ro + l), po))
        out.append("      +ub_%d_%d = biased(s%d, hu_%d)  # pose lane + half" % (po, l, po + l, po))
    return out


def _b2_react(f):
    po, fo, s, sel = f["po"], f["fo"], f["s"], f["sel"]
    if sel is None:
        out = ["      +sel_%d = False{}" % po]
    else:
        guard = "bit(%s)" % sel if clause("guard", "fires") == "fires" else "Bool.or(True{}, bit(%s))" % sel
        out = ["      +sel_%d = %s  # spinner %s input fires" % (po, guard, s)]
    for c in range(4):
        plus = [(ii, jj) for sg, ii, jj in HAMILTON[c] if sg > 0]
        minus = [(ii, jj) for sg, ii, jj in HAMILTON[c] if sg < 0]
        P = ["ua_%d_%d * ub_%d_%d" % (po, ii, po, jj) for ii, jj in plus] + \
            ["half_%d * (ua_%d_%d + ub_%d_%d : Nat)" % (po, po, ii, po, jj) for ii, jj in minus] + ["hsq_%d * %s" % (po, _b_lit(len(plus)))]
        N = ["ua_%d_%d * ub_%d_%d" % (po, ii, po, jj) for ii, jj in minus] + \
            ["half_%d * (ua_%d_%d + ub_%d_%d : Nat)" % (po, po, ii, po, jj) for ii, jj in plus] + ["hsq_%d * %s" % (po, _b_lit(len(minus)))]
        out.append("      +p_%d_%d = (%s : Nat)" % (po, c, " + ".join(P)))
        out.append("      +m_%d_%d = (%s : Nat)" % (po, c, " + ".join(N)))
        out.append("      +x_%d_%d = fin((p_%d_%d, m_%d_%d), den_%d, hi_%d, half_%d, full_%d)  # row %d: sign, toward-zero, saturate, encode" % (po, c, po, c, po, c, po, po, po, po, c))
    out.append("      +ov_%d = %s" % (po, "Bool.or(Bool.or(ov_of(x_%d_0, full_%d), ov_of(x_%d_1, full_%d)), Bool.or(ov_of(x_%d_2, full_%d), ov_of(x_%d_3, full_%d)))" % ((po, po) * 4)))
    for c in range(4):
        out.append("      o%d = sel(sel_%d, lane_of(x_%d_%d, full_%d), s%d)  # REACT over the committed rotor" % (po + c, po, po, c, po, po + c))
    fault = "sel(Bool.or(nz(fbase_%d), ov_%d), 1n, 0n)" % (fo, po) if clause("sticky", True) else "b2n(ov_%d)" % po
    out.append("      o%d = sel(sel_%d, %s, fbase_%d)  # sticky fault" % (fo, po, fault, fo))
    return out


def _b2_mac(f):
    return _b_mac(f) + """
def bit(w: U32, b: Nat) -> Bool:
  U32.is_ne(U32.and(U32.shrn(w, b), 1), 0)

# a + half (mod full) for a w-bit two's-complement lane: flip its top bit
def biased(v: Nat, +half: U32) -> Nat:
  U32.to_nat(U32.xor(U32.from_nat(v), half))

# x = lane + full * ov  ->  (lane, ov) without a division
def lane_of(+x: Nat, +full: Nat) -> Nat:
  sel(Nat.is_lt(x, full), x, (x - full : Nat))

def ov_of(x: Nat, +full: Nat) -> Bool:
  Bool.not(Nat.is_lt(x, full))
"""


RENDER["bend2"] = {"clock-onehot": _b2_clock_onehot, "clock-binary": _b2_clock_binary, "clock-once": _b2_clock_once,
                   "nxt-words": _b2_nxt_words, "signal-word": _b2_signal_word, "commit-fault-reset": _b_commit_fault_reset,
                   "orb-uncontrolled": _b_orb_uncontrolled, "commit-rotor": _b2_commit_rotor, "react": _b2_react, "mac": _b2_mac}
