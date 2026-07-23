"""lower_e2a.py -- lowering the E2a clocked subsystem onto the interaction
calculus (binding slice v0.1).

WHAT IS LOWERED. The autonomous COMMIT+REACT epoch of the reduced E2a
fixture (pulser p3 -> door; one-shot seed pulser -> relay r1; relay ring
r1 <-> r2), i.e. the part of the eighteen rules that executes every epoch
on a static graph. For a static graph the model's epoch -- an order-free
COMMIT over disjoint state followed by a confluent REACT token cascade
(uniqueness proven exhaustively by e2_run's DFS windows) -- is a pure
function of the boundary state, so it compiles to one closed IC term:

    fire3  = (t mod 3 == 0)             # p3 arming rule at commit
    fireS  = (seed one-shot at t == 3)  # period 10^9, phase 3
    c3'    = (c3+1) mod 3 ; cs' = saturating count to DONE
    w.cur' = w.nxt                      # wire commit
    w.nxt' = hot(src)                   # SIGW from a hot source at react
    door.open'      = door.next_open    # gate commit
    door.next_open' = w_pd.nxt          # SIG delivery from a hot wire
    r.cur_out'      = r.next_out        # relay commit
    r.next_out'     = OR(in-wires .nxt) # SIG delivery, or-merge
    armed' = 0                          # arm at commit, consume at react

ENCODINGS. Scott booleans (T=λt.λf.t), one-hot Scott enums for the two
counters (c3 in {C0,C1,C2}; cs in {S0..S3,SD}), pairs and a 9-tuple as
single-use selectors. Every field consumed twice goes through an explicit
!&L{a,b}= dup with a GLOBALLY FRESH label per syntactic site -- the label
discipline the runtime's own self-test uses -- so no dup can meet a
foreign sup of its own label. Unused fields are simply not referenced
(the calculus is affine: at most one occurrence).

DEFERRED, stated: ADMIT (events, claims, grafting), budget metering, the
spinner/orb quaternion branch (Motor8 fixed point), faults. This slice is
the every-epoch dynamics; the deferrals are the next slices.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_LBL = [200]
def _lab():
    _LBL[0] += 1
    return _LBL[0]

_VAR = [0]
def _v(p="v"):
    _VAR[0] += 1
    return f"{p}{_VAR[0]}"

# ---- closed constants (each textual occurrence is its own closed term)
T = "λbt.λbf.bt"
F = "λbt.λbf.bf"
C = ["λca.λcb.λcc.ca", "λca.λcb.λcc.cb", "λca.λcb.λcc.cc"]          # c3 enum
S = ["λs0.λs1.λs2.λs3.λsd.s0", "λs0.λs1.λs2.λs3.λsd.s1",
     "λs0.λs1.λs2.λs3.λsd.s2", "λs0.λs1.λs2.λs3.λsd.s3",
     "λs0.λs1.λs2.λs3.λsd.sd"]                                       # cs enum
NIL = "λnu.λnv.nu"        # list terminator; structurally distinct from PAIR

def PAIR(x, y):
    f = _v("pf")
    return f"λ{f}.(({f} {x}) {y})"

def TUP9(xs):
    f = _v("tf")
    s = f
    for x in xs:
        s = f"({s} {x})"
    return f"λ{f}.{s}"

def OR(a, b):   return f"(({a} {T}) {b})"
def INC3(x):    return f"((({x} {C[1]}) {C[2]}) {C[0]})"
def IS0_3(x):   return f"((({x} {T}) {F}) {F})"
def INCS(x):    return f"((((({x} {S[1]}) {S[2]}) {S[3]}) {S[4]}) {S[4]})"
def FIRES(x):   return f"((((({x} {F}) {F}) {F}) {T}) {F})"

def step_src(ring_swap=False):
    """One epoch as a closed IC term λstate.state'. Fresh dup labels per
    call so composed copies never collide. ring_swap=True mis-wires the
    ring (w_12 fed by r2, w_21 by r1) -- a structural mutation for the
    harness's sensitivity negatives; a textual name swap is only an
    alpha-rename and mutates nothing."""
    s = _v("st")
    c3, cs = _v("c3_"), _v("cs_")
    wpd, wsr, w12, w21 = _v("wpd"), _v("wsr"), _v("w12"), _v("w21")
    dr, r1, r2 = _v("dr"), _v("r1_"), _v("r2_")
    # destructure binders for pair fields
    pdc, pdn = _v("pdc"), _v("pdn")
    src_, srn = _v("src"), _v("srn")
    c12, n12 = _v("c12"), _v("n12")
    c21, n21 = _v("c21"), _v("n21")
    do, dn = _v("do"), _v("dn")
    r1c, r1n = _v("r1c"), _v("r1n")
    r2c, r2n = _v("r2c"), _v("r2n")
    # dup outputs for twice-used fields
    d = {}
    for nm in ("c3", "cs", "pdn", "srn", "n12", "n21", "r1n", "r2n"):
        d[nm] = (_v(nm + "a"), _v(nm + "b"), _lab())
    ring_a = d["r2n"][1] if ring_swap else d["r1n"][1]
    ring_b = d["r1n"][1] if ring_swap else d["r2n"][1]
    body = TUP9([
        INC3(d["c3"][1]), INCS(d["cs"][1]),
        PAIR(d["pdn"][0], IS0_3(d["c3"][0])),          # w_pd'
        PAIR(d["srn"][0], FIRES(d["cs"][0])),          # w_sr'
        PAIR(d["n12"][0], ring_a),                     # w_12'
        PAIR(d["n21"][0], ring_b),                     # w_21'
        PAIR(dn, d["pdn"][1]),                         # door'
        PAIR(d["r1n"][0], OR(d["srn"][1], d["n21"][1])),  # r1'
        PAIR(d["r2n"][0], d["n12"][1]),                # r2'
    ])
    dups = "".join(
        f"!&{lab}{{{a},{b}}}={val};"
        for (a, b, lab), val in [
            (d["c3"], c3), (d["cs"], cs), (d["pdn"], pdn), (d["srn"], srn),
            (d["n12"], n12), (d["n21"], n21), (d["r1n"], r1n),
            (d["r2n"], r2n)])
    inner = dups + body
    for (pv, a, b) in [(r2, r2c, r2n), (r1, r1c, r1n), (dr, do, dn),
                       (w21, c21, n21), (w12, c12, n12), (wsr, src_, srn),
                       (wpd, pdc, pdn)]:
        inner = f"({pv} λ{a}.λ{b}.{inner})"
    return (f"λ{s}.({s} λ{c3}.λ{cs}.λ{wpd}.λ{wsr}.λ{w12}.λ{w21}."
            f"λ{dr}.λ{r1}.λ{r2}.{inner})")

# ---- state <-> source / AST
def enc_bool(b):  return T if b else F

def enc_state(st):
    """st = dict(c3, cs, w_pd, w_sr, w_12, w_21, door, r1, r2) with pairs
    as (x, y) bool tuples, c3 in 0..2, cs in 0..4."""
    return TUP9([
        C[st["c3"]], S[st["cs"]],
        PAIR(enc_bool(st["w_pd"][0]), enc_bool(st["w_pd"][1])),
        PAIR(enc_bool(st["w_sr"][0]), enc_bool(st["w_sr"][1])),
        PAIR(enc_bool(st["w_12"][0]), enc_bool(st["w_12"][1])),
        PAIR(enc_bool(st["w_21"][0]), enc_bool(st["w_21"][1])),
        PAIR(enc_bool(st["door"][0]), enc_bool(st["door"][1])),
        PAIR(enc_bool(st["r1"][0]), enc_bool(st["r1"][1])),
        PAIR(enc_bool(st["r2"][0]), enc_bool(st["r2"][1])),
    ])

def compose_src(k, s0_src):
    """K fresh-label STEP copies chained inside ONE term, emitting the list
    PAIR(state1, PAIR(state2, ... PAIR(stateK, NIL))). Every intermediate
    state is consumed twice (film + next input) through a fresh-label dup:
    the reducer chains the epochs itself; the film is read from one normal
    form."""
    def chain(i, in_src):
        si = _v("sv")
        sa, sb, lab = _v("sa"), _v("sb"), _lab()
        nxt = (f"!&{lab}{{{sa},{sb}}}={si};"
               + PAIR(sa, chain(i + 1, sb))) if i < k else si
        if i < k:
            return f"(λ{si}.{nxt} ({step_src()} {in_src}))"
        return f"(λ{si}.{PAIR(si, NIL)} ({step_src()} {in_src}))"
    return chain(1, s0_src)

# ---- structural decoders (fully-normalized ASTs from ic_ref)
from ic_ref import Var, Lam, App

def _dec_bool(t):
    assert isinstance(t, Lam) and isinstance(t.bod, Lam) \
        and isinstance(t.bod.bod, Var), f"not a bool: {t}"
    if t.bod.bod.nam == t.nam: return True
    if t.bod.bod.nam == t.bod.nam: return False
    raise AssertionError("bool var mismatch")

def _dec_enum(t, k):
    ns = []
    cur = t
    for _ in range(k):
        assert isinstance(cur, Lam), "not an enum"
        ns.append(cur.nam); cur = cur.bod
    assert isinstance(cur, Var)
    return ns.index(cur.nam)

def _spine(t, n):
    assert isinstance(t, Lam)
    f = t.nam; cur = t.bod; out = []
    for _ in range(n):
        assert isinstance(cur, App)
        out.append(cur.arg); cur = cur.fun
    assert isinstance(cur, Var) and cur.nam == f
    return list(reversed(out))

def _dec_pair(t):
    a, b = _spine(t, 2)
    return a, b

def dec_state(t):
    xs = _spine(t, 9)
    def pb(x):
        a, b = _dec_pair(x)
        return (_dec_bool(a), _dec_bool(b))
    return dict(c3=_dec_enum(xs[0], 3), cs=_dec_enum(xs[1], 5),
                w_pd=pb(xs[2]), w_sr=pb(xs[3]), w_12=pb(xs[4]),
                w_21=pb(xs[5]), door=pb(xs[6]), r1=pb(xs[7]), r2=pb(xs[8]))

def dec_list(t):
    out = []
    cur = t
    while True:
        if isinstance(cur, Lam) and isinstance(cur.bod, Lam) \
                and isinstance(cur.bod.bod, Var) \
                and cur.bod.bod.nam == cur.nam:
            return out                       # NIL
        a, b = _dec_pair(cur)
        out.append(dec_state(a)); cur = b

def state_to_film_args(st, t):
    """Map the IC state dict + epoch index to portable film arguments.
    Static config fields (periods, phases) are fixture constants; armed is
    computed (always consumed within the epoch) and asserted 0 model-side."""
    pulsers = [("p3", 3, 0, 0), ("seed", 10 ** 9, 3, 0)]
    doors = [("door", st["door"][0], st["door"][1])]
    relays = [("r1", st["r1"][0], st["r1"][1]),
              ("r2", st["r2"][0], st["r2"][1])]
    wires = [("w_pd", *st["w_pd"]), ("w_sr", *st["w_sr"]),
             ("w_12", *st["w_12"]), ("w_21", *st["w_21"])]
    return t, pulsers, doors, relays, wires
