"""binlib.py -- fixed-width binary arithmetic circuits (slices 3b.1/3b.2).

POLICIES, specified before implementation (review round 7):
  add/sub (unsigned): WRAP modulo 2^w; carry-out / borrow exposed as
      flags. borrow = NOT(carry_out of a + NOT(b) + 1).
  ltu: a < b  :=  borrow of (a - b).
  eq: AND-fold of per-bit XNOR.
  widen (w -> W > w): zero-extend (unsigned).
  trunc (W -> w): drop high bits (wrap).
  neg (signed two's complement): NOT(a) + 1, WRAPS: neg(MIN) = MIN; the
      ovf flag is eq(a, MIN). neg(0) = 0 (carry ripples out; flag clear).
  slt (signed): signs differ -> a < b iff sign(a); signs equal ->
      unsigned compare is valid on two's complement.
  sadd/ssub (signed, SATURATING): exact w-bit sum/diff; ovf :=
      carry_into_msb XOR carry_out; on ovf clamp to MIN if the first
      operand's sign selects negative overflow direction convention:
      clamp toward the sign of the true result, i.e. ovf on add of two
      positives -> MAX, of two negatives -> MIN (selected by NOT of
      a's sign for add; by a's sign vs b's for sub via the same carry
      algebra). The ovf flag is returned alongside the clamped value.

REPRESENTATION: a w-bit value is a TUPw of Scott booleans, LSB first --
identical to the compiler's counter representation, so these circuits
are the counters' generalization, not a parallel stack.

CALLING CONVENTION: emitters take per-bit SOURCE-COPY LISTS -- each
source string is consumed exactly once (affine). For constant inputs,
copies are textual repetitions of T/F (no dups needed); for variable
inputs, callers allocate copies via compiler.Alloc. Per-bit use counts:
add: a x2, b x3, carry x4 (x5 for the carry into the MSB when exposed).
Every intermediate goes through compiler.LetChain with its fan-out dups
inside its own binder (slice-2 scoping law).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compiler import Alloc, LetChain, NOT, AND, OR, TUPN, bits_of
from lower_e2a import T, F, _v

# use-count constants
A_USES, B_USES, C_USES = 2, 3, 4

def XOR(sel, x1, x2):
    return f"(({sel} {NOT(x1)}) {x2})"

def MAJ(sel, b1, c1, b2, c2):
    return f"(({sel} {OR(b1, c1)}) {AND(b2, c2)})"

def cbits(v, w, n):
    """Constant input: n textual copies per bit, LSB first."""
    return [[T if (v >> i) & 1 else F] * n for i in range(w)]

def cnbits(v, w, n):
    """Constant input, complemented (for subtraction)."""
    return [[F if (v >> i) & 1 else T] * n for i in range(w)]

def emit_add(w, A, B, cin_copies, L, s_copies=1, cout_copies=1,
             expose_cmsb=0):
    """A[i]: >=2 copies; B[i]: >=3 copies; cin_copies: 4 copies.
    Returns (sum_copy_lists, cout_copies_list, cmsb_copies_or_None)."""
    sums = []
    c = cin_copies
    cmsb = None
    for i in range(w):
        a2, b3 = A[i], B[i]
        x = L.let(XOR(b3[0], c[0], c[1]), 2, "x")
        sums.append(L.let(XOR(a2[0], x[0], x[1]), s_copies, "s"))
        nco = C_USES if i < w - 1 else cout_copies
        if i == w - 2 and expose_cmsb:
            nco += expose_cmsb
        c = L.let(MAJ(a2[1], b3[1], c[2], b3[2], c[3]), nco, "c")
        if i == w - 2 and expose_cmsb:
            cmsb, c = c[:expose_cmsb], c[expose_cmsb:]
    return sums, c, cmsb

def emit_eq(w, A1, B1):
    """A1/B1: 1 copy per bit (a) / 2 copies per bit (b). Returns expr."""
    acc = None
    for i in range(w):
        xn = f"(({A1[i][0]} {B1[i][0]}) {NOT(B1[i][1])})"
        acc = xn if acc is None else AND(acc, xn)
    return acc if acc is not None else T

# ------------------------------------------------ constant-input cases
def add_case(w, a, b, cin=0):
    """Closed term: TUP(w sums + cout + cmsb)."""
    L = LetChain()
    s, co, cm = emit_add(w, cbits(a, w, A_USES), cbits(b, w, B_USES),
                         [T if cin else F] * 4, L, expose_cmsb=1)
    out = TUPN([x[0] for x in s] + [co[0], cm[0]])
    return L.wrap(out)

def sub_case(w, a, b):
    """a - b = a + NOT(b) + 1; borrow = NOT(cout). TUP(w diffs+borrow)."""
    L = LetChain()
    s, co, _ = emit_add(w, cbits(a, w, A_USES), cnbits(b, w, B_USES),
                        [T] * 4, L)
    out = TUPN([x[0] for x in s] + [NOT(co[0])])
    return L.wrap(out)

def ltu_case(w, a, b):
    L = LetChain()
    _, co, _ = emit_add(w, cbits(a, w, A_USES), cnbits(b, w, B_USES),
                        [T] * 4, L, s_copies=0)
    return L.wrap(TUPN([NOT(co[0])]))

def eq_case(w, a, b):
    return TUPN([emit_eq(w, cbits(a, w, 1), cbits(b, w, 2))])

def widen_case(w, W, v):
    """Zero-extend through a term (not just the encoder)."""
    return TUPN([T if (v >> i) & 1 else F for i in range(w)]
                + [F] * (W - w))

def trunc_case(W, w, v):
    return TUPN([T if (v >> i) & 1 else F for i in range(w)])

def neg_case(w, a):
    """Two's-complement negate: NOT(a)+1, wraps; ovf = eq(a, MIN)."""
    L = LetChain()
    s, _, _ = emit_add(w, cnbits(a, w, A_USES), cbits(0, w, B_USES),
                       [T] * 4, L)
    ovf = emit_eq(w, cbits(a, w, 1), cbits(1 << (w - 1), w, 2))
    return L.wrap(TUPN([x[0] for x in s] + [ovf]))

def slt_case(w, a, b):
    """Signed less-than over two's-complement bit patterns a, b."""
    sa = (a >> (w - 1)) & 1
    sb = (b >> (w - 1)) & 1
    L = LetChain()
    _, co, _ = emit_add(w, cbits(a, w, A_USES), cnbits(b, w, B_USES),
                        [T] * 4, L, s_copies=0)
    ltu = NOT(co[0])
    sel = XOR(T if sa else F, T if sb else F, T if sb else F)
    expr = f"(({sel} {T if sa else F}) {ltu})"
    return L.wrap(TUPN([expr]))

def _sat_add_core(w, A, B, cin, L, neg_dir_sign_copies):
    """Shared saturating core: exact sum, ovf = cmsb XOR cout, clamp
    toward the true result's sign (encoded by neg_dir sign bit copies:
    for add, a's sign; overflow of p+p -> MAX (sign 0), n+n -> MIN)."""
    s, co, cm = emit_add(w, A, B, cin, L, s_copies=1, expose_cmsb=1)
    ovf = L.let(XOR(cm[0], co[0], co[0]) if False else
                f"(({cm[0]} {NOT(co[0])}) {co[0]})", 2, "ovf")
    maxc = TUPN([T] * (w - 1) + [F])
    minc = TUPN([F] * (w - 1) + [T])
    clamp = f"(({neg_dir_sign_copies[0]} {minc}) {maxc})"
    val = f"(({ovf[0]} {clamp}) {TUPN([x[0] for x in s])})"
    return f"{val}", ovf[1]

def sadd_case(w, a, b):
    """Saturating signed add of bit patterns; TUP(w value + ovf)."""
    L = LetChain()
    sa_c = [T if (a >> (w - 1)) & 1 else F]
    val, ovf = _sat_add_core(w, cbits(a, w, A_USES), cbits(b, w, B_USES),
                             [F] * 4, L, sa_c)
    inner = TUPN([f"__VAL__", ovf])
    # inline: value is a tuple; nest it as a single spine element
    return L.wrap(inner.replace("__VAL__", val))

def ssub_case(w, a, b):
    """Saturating signed subtract: a + NOT(b) + 1; overflow direction by
    a's sign (p - n overflowing -> MAX; n - p -> MIN)."""
    L = LetChain()
    sa_c = [T if (a >> (w - 1)) & 1 else F]
    val, ovf = _sat_add_core(w, cbits(a, w, A_USES), cnbits(b, w, B_USES),
                             [T] * 4, L, sa_c)
    inner = TUPN([f"__VAL__", ovf])
    return L.wrap(inner.replace("__VAL__", val))

# ------------------------------------------------------------- decode
from lower_e2a import _dec_bool, _spine

def dec_bits_list(ts):
    return sum((1 << i) for i, t in enumerate(ts) if _dec_bool(t))

def dec_flat(t, w, nflags):
    xs = _spine(t, w + nflags)
    return dec_bits_list(xs[:w]), [int(_dec_bool(x)) for x in xs[w:]]

def dec_val_flag(t, w):
    """For sadd/ssub: TUP(valueTuple, ovf)."""
    xs = _spine(t, 2)
    return dec_bits_list(_spine(xs[0], w)), int(_dec_bool(xs[1]))


# ================= 3b.2c: DYNAMIC OPERANDS (review round 8) =================
# The constant-input helpers above verify circuit LOGIC; these emit closed
# COMBINATOR terms λA.λB.result that destructure runtime-encoded operand
# tuples, with per-bit use-counted duplication -- the reusable-library form
# Motor8 needs. NOTE (the compose/chain lesson, third appearance): every
# occurrence of a combinator in a CHAINED term must be a FRESH instance
# (fresh dup labels); two same-labeled closed subterms are safe only when
# no dataflow connects them (independent batch cases), never when one's
# output feeds the other's destructure.
from compiler import Alloc as _Alloc, LetChain as _LC

def enc_operand(v, w):
    return TUPN([T if (v >> i) & 1 else F for i in range(w)])

def _dyn2(w, a_counts, b_counts, build):
    """λA.λB. destructure, allocate per-bit copies, build(acopies,bcopies,L)."""
    Av, Bv = _v("A"), _v("B")
    ab = [_v("a") for _ in range(w)]
    bb = [_v("b") for _ in range(w)]
    A = _Alloc()
    ac = [A.copies(ab[i], a_counts[i]) for i in range(w)]
    bc = [A.copies(bb[i], b_counts[i]) for i in range(w)]
    L = _LC()
    out = build(ac, bc, L)
    inner = "".join(A.prefix) + L.wrap(out)
    inner = f"({Bv} λ" + ".λ".join(bb) + f".{inner})"
    inner = f"({Av} λ" + ".λ".join(ab) + f".{inner})"
    return f"λ{Av}.λ{Bv}.{inner}"

def dyn_case(op, w):
    if op == "add":
        def b(ac, bc, L):
            s, co, cm = emit_add(w, ac, bc, [F] * 4, L, expose_cmsb=1)
            return TUPN([x[0] for x in s] + [co[0], cm[0]])
        return _dyn2(w, [2] * w, [3] * w, b)
    if op == "sub":
        def b(ac, bc, L):
            nb = [[NOT(c) for c in row] for row in bc]
            s, co, _ = emit_add(w, ac, nb, [T] * 4, L)
            return TUPN([x[0] for x in s] + [NOT(co[0])])
        return _dyn2(w, [2] * w, [3] * w, b)
    if op == "ltu":
        def b(ac, bc, L):
            nb = [[NOT(c) for c in row] for row in bc]
            _, co, _ = emit_add(w, ac, nb, [T] * 4, L, s_copies=0)
            return TUPN([NOT(co[0])])
        return _dyn2(w, [2] * w, [3] * w, b)
    if op == "eq":
        def b(ac, bc, L):
            return TUPN([emit_eq(w, ac, bc)])
        return _dyn2(w, [1] * w, [2] * w, b)
    if op in ("sadd", "ssub"):
        def b(ac, bc, L):
            bb = bc if op == "sadd" else [[NOT(c) for c in row]
                                          for row in bc]
            cin = [F] * 4 if op == "sadd" else [T] * 4
            sa = ac[w - 1][2]
            s, co, cm = emit_add(w, [row[:2] for row in ac], bb, cin, L,
                                 expose_cmsb=1)
            ovf = L.let(f"(({cm[0]} {NOT(co[0])}) {co[0]})", 2, "ovf")
            maxc = TUPN([T] * (w - 1) + [F])
            minc = TUPN([F] * (w - 1) + [T])
            val = (f"(({ovf[0]} (({sa} {minc}) {maxc})) "
                   f"{TUPN([x[0] for x in s])})")
            return TUPN([val, ovf[1]])
        cnt_a = [2] * (w - 1) + [3]
        return _dyn2(w, cnt_a, [3] * w, b)
    if op == "slt":
        def b(ac, bc, L):
            sa2 = ac[w - 1][2:4]
            sb2 = bc[w - 1][3:5]
            nb = [[NOT(c) for c in row[:3]] for row in bc]
            _, co, _ = emit_add(w, [row[:2] for row in ac], nb, [T] * 4,
                                L, s_copies=0)
            ltu = NOT(co[0])
            sel = f"(({sa2[0]} {NOT(sb2[0])}) {sb2[1]})"
            return TUPN([f"(({sel} {sa2[1]}) {ltu})"])
        return _dyn2(w, [2] * (w - 1) + [4], [3] * (w - 1) + [5], b)
    raise ValueError(op)

def dyn_neg(w):
    Av = _v("A")
    ab = [_v("a") for _ in range(w)]
    A = _Alloc()
    ac = [A.copies(ab[i], 3) for i in range(w)]
    L = _LC()
    na = [[NOT(row[0]), NOT(row[1])] for row in ac]
    s, _, _ = emit_add(w, na, cbits(0, w, B_USES), [T] * 4, L)
    ovf = emit_eq(w, [[row[2]] for row in ac],
                  cbits(1 << (w - 1), w, 2))
    inner = "".join(A.prefix) + L.wrap(
        TUPN([x[0] for x in s] + [ovf]))
    return f"λ{Av}.({Av} λ" + ".λ".join(ab) + f".{inner})"

def dyn_widen(w, W):
    Av = _v("A")
    ab = [_v("a") for _ in range(w)]
    return (f"λ{Av}.({Av} λ" + ".λ".join(ab) + "."
            + TUPN(ab + [F] * (W - w)) + ")")

def dyn_trunc(W, w):
    Av = _v("A")
    ab = [_v("a") for _ in range(W)]
    return (f"λ{Av}.({Av} λ" + ".λ".join(ab) + "."
            + TUPN(ab[:w]) + ")")


def dyn_take_value(w, nflags):
    """NAMED flag-policy adapter (review round 9): extracts the w value
    bits from a result tuple, DISCARDING nflags flag bits BY POLICY.
    Silent flag loss in composed pipelines is banned; a raw dyn_trunc
    between ALU stages hides an overflow-handling decision. This adapter
    is that decision, named."""
    return dyn_trunc(w + nflags, w)

CONVENTION = "(T X Y) -> X : Scott booleans select the FIRST branch"

def convention_witness(run):
    """Executable convention pin: run() must be parse+normalize. Returns
    True iff the runtime selects the first branch for T -- the reading
    under which every clamp in this library is correct. A reviewer
    assuming second-branch-true predicts exactly (-128, ovf=1) for
    dynamic ssub(127, -1); the shipped runtime yields (+127, ovf=1)."""
    from lower_e2a import _dec_bool
    t = run(f"(({T} {T}) {F})")
    return _dec_bool(t) is True


# ================= 3b.3: SIGNED FIXED-POINT MULTIPLY (round 9) =============
# Pipeline, in the review's load-bearing order: wide signed product ->
# arithmetic shift by n with TOWARD-ZERO correction (floor-shift plus
# (sign AND dropped-bits-OR), the named Forge rounding) -> saturate to w
# with overflow flag. Wide product: sign-extend both operands to 2w and
# shift-add mod 2^(2w); the exact signed product fits, so no cout is
# consumed. Constant-operand circuits (the gates run on the reducer; the
# harness folds nothing); the dynamic form follows the proven 3b.2c
# pattern and is the next slice's first task.

def _lit(x):
    return T if x else F

def _chk_mul(w, n, a, b):
    if not (isinstance(w, int) and w > 0):
        raise ValueError(f"mul: width must be a positive int, got {w!r}")
    if not (isinstance(n, int) and 0 <= n <= w):
        raise ValueError(f"mul: fractional shift n must satisfy "
                         f"0 <= n <= w (Wq = 2w-n must cover w); got "
                         f"n={n!r} at w={w}")
    for nm, v in (("a", a), ("b", b)):
        if not (isinstance(v, int) and 0 <= v < (1 << w)):
            raise ValueError(f"mul: operand {nm}={v!r} outside "
                             f"[0, 2^{w})")

def mul_wide_case(w, a, b):
    """Signed w x w -> 2w product circuit, constant operands.
    Returns (source_of_TUP2w, LetChain) unwrapped for pipeline reuse."""
    _chk_mul(w, 0, a, b)
    L = LetChain()
    W = 2 * w
    sa = (a >> (w - 1)) & 1
    sb = (b >> (w - 1)) & 1
    se_a = [(a >> i) & 1 for i in range(w)] + [sa] * w
    se_b = [(b >> i) & 1 for i in range(w)] + [sb] * w
    def addend(j, ncop):
        out = []
        for i in range(W):
            bit = se_a[i - j] if i >= j else 0
            out.append(L.let(AND(_lit(se_b[j]), _lit(bit)), ncop, "pp"))
        return out
    acc = addend(0, 2)
    for j in range(1, W):
        rows_b = addend(j, 3)
        scop = 2 if j < W - 1 else 1
        s, _, _ = emit_add(W, acc, rows_b, [F] * 4, L, s_copies=scop)
        acc = s
    return acc, L

def qmul_case(w, n, a, b):
    """Full 3b.3 pipeline: product -> >>n toward zero -> saturate to w.
    Closed term TUP(valueTuple, ovf) -- the nested SADD-family shape."""
    _chk_mul(w, n, a, b)
    acc, L = mul_wide_case(w, a, b)
    W = 2 * w
    Wq = W - n
    # per-bit uses of the product: low n bits -> dropped-OR (1);
    # bits n..W-1 -> shifted value rows (2 for the corr-add A slot);
    # sign p[W-1] additionally -> corr AND (1)
    p = []
    for i in range(W):
        need = (1 if i < n else 2) + (1 if i == W - 1 else 0)
        cps = L.let(acc[i][0], need, "p")
        p.append(cps)
    if n:
        dropped = p[0][0]
        for i in range(1, n):
            dropped = OR(dropped, p[i][0])
        corr = L.let(AND(p[W - 1][2], dropped), 4, "corr")
    else:
        corr = L.let(F, 4, "corr")
    srows = [p[n + i][:2] for i in range(Wq)]
    q, _, _ = emit_add(Wq, srows, [[F] * 3 for _ in range(Wq)], corr, L,
                       s_copies=2)
    # saturate Wq -> w: in-range iff bits w-1..Wq-1 all equal
    # in-range iff bits w-1..Wq-2 all equal the sign bit q[Wq-1].
    # Each XNOR consumes TWO sign copies (raw + negated) -- a single
    # copy reused twice is an affine violation (caught in first smoke).
    n_cmp = Wq - w                       # compares over bits w-1..Wq-2
    sgn = L.let(q[Wq - 1][0], 2 * n_cmp + 1, "sg")
    inr = None
    for k, i in enumerate(range(w - 1, Wq - 1)):
        s1, s2 = sgn[2 * k], sgn[2 * k + 1]
        xn = f"(({q[i][1]} {s1}) {NOT(s2)})"
        inr = xn if inr is None else AND(inr, xn)
    ovf = L.let(NOT(inr) if inr is not None else F, 2, "ov")
    maxc = TUPN([T] * (w - 1) + [F])
    minc = TUPN([F] * (w - 1) + [T])
    cand = TUPN([q[i][0] for i in range(w)])
    val = f"(({ovf[0]} (({sgn[-1]} {minc}) {maxc})) {cand})"
    return L.wrap(TUPN([val, ovf[1]]))

def golden_qmul(w, n, a, b):
    def s_of(v):
        return v - (1 << w) if v >= (1 << (w - 1)) else v
    P = s_of(a) * s_of(b)
    q = P >> n if P >= 0 else -((-P) >> n)      # toward zero
    lo, hi = -(1 << (w - 1)), (1 << (w - 1)) - 1
    return (max(lo, min(hi, q)), int(not lo <= q <= hi))


# ============== round 10: ALUResult registry + per-stage + dynamic mul ======
# RESULT SHAPES, formalized (review round 10): every op's output shape is
# registered; projections are emitted FROM THE REGISTRY, so a flat
# adapter can no longer be applied to a nested result by accident -- the
# misuse the review demonstrated is now unconstructible through the
# named API. dyn_take_value remains, documented FLAT-ONLY.
#   flat:   TUP(w value bits + flag bits)        add/sub/neg/ltu/eq/slt
#   nested: TUP(valueTuple, ovf)                 sadd/ssub/qmul/sat
RESULT_SHAPES = {
    "add":  ("flat", ["carry", "cmsb"]),
    "sub":  ("flat", ["borrow"]),
    "neg":  ("flat", ["overflow"]),
    "ltu":  ("flat_bool", []),
    "eq":   ("flat_bool", []),
    "slt":  ("flat_bool", []),
    "sadd": ("nested", ["overflow"]),
    "ssub": ("nested", ["overflow"]),
    "qmul": ("nested", ["overflow"]),
    "sat":  ("nested", ["overflow"]),
}

def take_value_of(op, w):
    """Shape-correct value projection for op's registered result."""
    kind, flags = RESULT_SHAPES[op]
    if kind == "flat":
        return dyn_take_value(w, len(flags))
    if kind == "nested":
        R, v, f = _v("R"), _v("rv"), _v("rf")
        return f"λ{R}.({R} λ{v}.λ{f}.{v})"
    raise ValueError(f"{op}: boolean results have no value tuple")

def take_flag_of(op, w, flag):
    kind, flags = RESULT_SHAPES[op]
    i = flags.index(flag)
    if kind == "flat":
        R = _v("R")
        bs = [_v("fb") for _ in range(w + len(flags))]
        return (f"λ{R}.({R} λ" + ".λ".join(bs) + "."
                + TUPN([bs[w + i]]) + ")")
    if kind == "nested":
        R, v, f = _v("R"), _v("rv"), _v("rf")
        return f"λ{R}.({R} λ{v}.λ{f}.{TUPN([f])})"
    raise ValueError(op)

# ---------------- per-stage constant oracle terms (round 10) ---------------
def mul_wide_term(w, a, b):
    acc, L = mul_wide_case(w, a, b)
    return L.wrap(TUPN([x[0] for x in acc]))

def golden_mul_wide(w, a, b):
    def s(v):
        return v - (1 << w) if v >= (1 << (w - 1)) else v
    return (s(a) * s(b)) & ((1 << (2 * w)) - 1)

def shift_tz_case(W, n, p):
    """Constant p (W-bit two's complement pattern) -> TUP(W-n): shift
    right n with toward-zero correction."""
    L = LetChain()
    Wq = W - n
    pc = []
    for i in range(W):
        need = (1 if i < n else 2) + (1 if i == W - 1 else 0)
        pc.append([T if (p >> i) & 1 else F] * need)
    if n:
        dropped = pc[0][0]
        for i in range(1, n):
            dropped = OR(dropped, pc[i][0])
        corr = L.let(AND(pc[W - 1][-1], dropped), 4, "corr")
    else:
        corr = L.let(F, 4, "corr")
    srows = [pc[n + i][:2] for i in range(Wq)]
    q, _, _ = emit_add(Wq, srows, [[F] * 3 for _ in range(Wq)], corr, L,
                       s_copies=1)
    return L.wrap(TUPN([x[0] for x in q]))

def golden_shift_tz(W, n, p):
    def s(v):
        return v - (1 << W) if v >= (1 << (W - 1)) else v
    P = s(p)
    q = P >> n if P >= 0 else -((-P) >> n)
    return q & ((1 << (W - n)) - 1)

def sat_case(Wq, w, q):
    """Constant q (Wq-bit pattern) -> nested TUP(valueTuple(w), ovf)."""
    L = LetChain()
    n_cmp = Wq - w
    qc = []
    for i in range(Wq):
        if i < w - 1:
            need = 1
        elif i == w - 1:
            need = 2
        elif i < Wq - 1:
            need = 1
        else:
            need = 2 * n_cmp + 1
        qc.append([T if (q >> i) & 1 else F] * need)
    inr = None
    for k, i in enumerate(range(w - 1, Wq - 1)):
        s1, s2 = qc[Wq - 1][2 * k], qc[Wq - 1][2 * k + 1]
        xn = f"(({qc[i][-1]} {s1}) {NOT(s2)})"
        inr = xn if inr is None else AND(inr, xn)
    ovf = L.let(NOT(inr) if inr is not None else F, 2, "ov")
    maxc = TUPN([T] * (w - 1) + [F])
    minc = TUPN([F] * (w - 1) + [T])
    cand = TUPN([qc[i][0] for i in range(w)])
    val = f"(({ovf[0]} (({qc[Wq - 1][-1] if n_cmp else qc[Wq-1][0]} {minc}) {maxc})) {cand})"
    return L.wrap(TUPN([val, ovf[1]]))

def golden_sat(Wq, w, q):
    def s(v):
        return v - (1 << Wq) if v >= (1 << (Wq - 1)) else v
    Q = s(q)
    lo, hi = -(1 << (w - 1)), (1 << (w - 1)) - 1
    return (max(lo, min(hi, Q)) & ((1 << w) - 1),
            int(not lo <= Q <= hi))

# ------------------------- dynamic multiply stages -------------------------
def dyn_mul_wide(w):
    """λA.λB -> TUP(2w): signed wide product, runtime operands."""
    W = 2 * w
    Av, Bv = _v("A"), _v("B")
    ab = [_v("a") for _ in range(w)]
    bb = [_v("b") for _ in range(w)]
    A = _Alloc()
    tri = (w + 1) * (w + 2) // 2
    ac = [A.copies(ab[m], (2 * w - m) if m < w - 1 else tri)
          for m in range(w)]
    bc = [A.copies(bb[j], (2 * w - j) if j < w - 1 else tri)
          for j in range(w)]
    ai = [0] * w
    bi = [0] * w
    def a_src(m):
        mm = min(m, w - 1)
        s = ac[mm][ai[mm]]
        ai[mm] += 1
        return s
    def b_src(j):
        jj = min(j, w - 1)
        s = bc[jj][bi[jj]]
        bi[jj] += 1
        return s
    L = _LC()
    def addend(j, ncop):
        out = []
        for i in range(W):
            if i >= j:
                out.append(L.let(AND(b_src(j), a_src(i - j)), ncop, "pp"))
            else:
                out.append(L.let(F, ncop, "pz"))
        return out
    acc = addend(0, 2)
    for j in range(1, W):
        rows_b = addend(j, 3)
        scop = 2 if j < W - 1 else 1
        s, _, _ = emit_add(W, acc, rows_b, [F] * 4, L, s_copies=scop)
        acc = s
    inner = "".join(A.prefix) + L.wrap(TUPN([x[0] for x in acc]))
    inner = f"({Bv} λ" + ".λ".join(bb) + f".{inner})"
    inner = f"({Av} λ" + ".λ".join(ab) + f".{inner})"
    return f"λ{Av}.λ{Bv}.{inner}"

def dyn_shift_tz(W, n):
    Pv = _v("P")
    pb = [_v("p") for _ in range(W)]
    A = _Alloc()
    pc = [A.copies(pb[i], (1 if i < n else 2) + (1 if i == W - 1 else 0))
          for i in range(W)]
    L = _LC()
    Wq = W - n
    if n:
        dropped = pc[0][0]
        for i in range(1, n):
            dropped = OR(dropped, pc[i][0])
        corr = L.let(AND(pc[W - 1][-1], dropped), 4, "corr")
    else:
        corr = L.let(F, 4, "corr")
    srows = [pc[n + i][:2] for i in range(Wq)]
    q, _, _ = emit_add(Wq, srows, [[F] * 3 for _ in range(Wq)], corr, L,
                       s_copies=1)
    inner = "".join(A.prefix) + L.wrap(TUPN([x[0] for x in q]))
    return f"λ{Pv}.({Pv} λ" + ".λ".join(pb) + f".{inner})"

def dyn_sat(Wq, w):
    """λQ -> nested TUP(valueTuple(w), ovf)."""
    Qv = _v("Q")
    qb = [_v("q") for _ in range(Wq)]
    A = _Alloc()
    n_cmp = Wq - w
    def need(i):
        if i < w - 1:
            return 1
        if i == w - 1:
            return 2
        if i < Wq - 1:
            return 1
        return 2 * n_cmp + 1 + 1     # xnor pairs + clamp select + value?
    qc = [A.copies(qb[i], need(i)) for i in range(Wq)]
    L = _LC()
    inr = None
    for k, i in enumerate(range(w - 1, Wq - 1)):
        s1, s2 = qc[Wq - 1][2 * k], qc[Wq - 1][2 * k + 1]
        xn = f"(({qc[i][-1]} {s1}) {NOT(s2)})"
        inr = xn if inr is None else AND(inr, xn)
    ovf = L.let(NOT(inr) if inr is not None else F, 2, "ov")
    maxc = TUPN([T] * (w - 1) + [F])
    minc = TUPN([F] * (w - 1) + [T])
    cand = TUPN([qc[i][0] for i in range(w)])
    sel_sign = qc[Wq - 1][2 * n_cmp] if n_cmp else qc[Wq - 1][0]
    val = f"(({ovf[0]} (({sel_sign} {minc}) {maxc})) {cand})"
    inner = "".join(A.prefix) + L.wrap(TUPN([val, ovf[1]]))
    return f"λ{Qv}.({Qv} λ" + ".λ".join(qb) + f".{inner})"

def dyn_qmul(w, n):
    """Composed dynamic pipeline, fresh instances per stage."""
    _chk_mul(w, n, 0, 0)
    A2, B2 = _v("QA"), _v("QB")
    body = (f"({dyn_sat(2 * w - n, w)} ({dyn_shift_tz(2 * w, n)} "
            f"(({dyn_mul_wide(w)} {A2}) {B2})))")
    return f"λ{A2}.λ{B2}.{body}"

def dyn_sext(V, Vm):
    Av = _v("E")
    ab = [_v("e") for _ in range(V)]
    A = _Alloc()
    top = A.copies(ab[V - 1], Vm - V + 1)
    body = TUPN(ab[:V - 1] + [top[0]] + top[1:])
    return (f"λ{Av}.({Av} λ" + ".λ".join(ab) + "."
            + "".join(A.prefix) + body + ")")

# ------------------------------- wide MAC ---------------------------------
def golden_mac(w, n, terms):
    """terms: [(sign, a, b)] -- wide products accumulated at full
    precision, ONE toward-zero shift, ONE saturation (round 10 policy)."""
    def s(v, ww):
        return v - (1 << ww) if v >= (1 << (ww - 1)) else v
    acc = 0
    for sg, a, b in terms:
        acc += sg * (s(a, w) * s(b, w))
    q = acc >> n if acc >= 0 else -((-acc) >> n)
    lo, hi = -(1 << (w - 1)), (1 << (w - 1)) - 1
    return (max(lo, min(hi, q)) & ((1 << w) - 1),
            int(not lo <= q <= hi))

def mac_wide_case(w, n, terms):
    """Constant 4-term MAC: products at 2w, sign-extended to Wm=2w+2,
    add/sub chained, ONE shift_tz, ONE saturation. Nested result."""
    assert len(terms) >= 1
    _chk_mul(w, n, 0, 0)
    W = 2 * w
    Wm = W + 2
    L = LetChain()
    exts = []
    for (sg, a, b) in terms:
        acc, Lm = mul_wide_case(w, a, b)
        # merge product lets into ours, then extend
        L.lets.extend(Lm.lets)
        top = L.let(acc[W - 1][0], Wm - W + 1, "sx")
        bits = [acc[i][0] for i in range(W - 1)] + [top[0]] + top[1:]
        exts.append((sg, bits))
    sg0, acc_bits = exts[0]
    accc = [L.let(b if sg0 > 0 else b, 2, "m0") for b in acc_bits]
    if sg0 < 0:
        # negate first term: ~x + 1 via add
        na = [[NOT(c[0]), NOT(c[1])] for c in accc]
        accc2, _, _ = emit_add(Wm, na, [[F] * 3 for _ in range(Wm)],
                               [T] * 4, L, s_copies=2)
        accc = accc2
    for (sg, bits) in exts[1:]:
        rows_b = [L.let(b, 3, "mt") for b in bits]
        if sg > 0:
            nb = rows_b
            cin = [F] * 4
        else:
            nb = [[NOT(c) for c in row] for row in rows_b]
            cin = [T] * 4
        rows_b2 = [[r[0], r[1], r[2]] for r in nb]
        accc, _, _ = emit_add(Wm, [c[:2] for c in accc], rows_b2, cin, L,
                              s_copies=2)
    # one shift, one saturation -- inline (constant-free, uses copies)
    Wq = Wm - n
    pc = []
    for i in range(Wm):
        needc = (1 if i < n else 2) + (1 if i == Wm - 1 else 0)
        pc.append(L.let(accc[i][0], needc, "mp"))
    if n:
        dropped = pc[0][0]
        for i in range(1, n):
            dropped = OR(dropped, pc[i][0])
        corr = L.let(AND(pc[Wm - 1][-1], dropped), 4, "mc")
    else:
        corr = L.let(F, 4, "mc")
    srows = [pc[n + i][:2] for i in range(Wq)]
    q, _, _ = emit_add(Wq, srows, [[F] * 3 for _ in range(Wq)], corr, L,
                       s_copies=1)
    n_cmp = Wq - w
    qc = []
    for i in range(Wq):
        if i < w - 1:
            needq = 1
        elif i == w - 1:
            needq = 2
        elif i < Wq - 1:
            needq = 1
        else:
            needq = 2 * n_cmp + 2
        qc.append(L.let(q[i][0], needq, "mq"))
    inr = None
    for k, i in enumerate(range(w - 1, Wq - 1)):
        s1, s2 = qc[Wq - 1][2 * k], qc[Wq - 1][2 * k + 1]
        xn = f"(({qc[i][-1]} {s1}) {NOT(s2)})"
        inr = xn if inr is None else AND(inr, xn)
    ovf = L.let(NOT(inr) if inr is not None else F, 2, "mo")
    maxc = TUPN([T] * (w - 1) + [F])
    minc = TUPN([F] * (w - 1) + [T])
    cand = TUPN([qc[i][0] for i in range(w)])
    val = f"(({ovf[0]} (({qc[Wq - 1][2 * n_cmp]} {minc}) {maxc})) {cand})"
    return L.wrap(TUPN([val, ovf[1]]))


# ================= 3b.4: quaternion proxy (round 11) =======================
# THE ORACLE'S POLICY, extracted and matched (drift-as-regression-input):
# e2_model computes each Hamilton component as a +/- sum of FOUR
# INDIVIDUALLY toward-zero-truncated products (tmul = trunc0((a*b)>>SHIFT))
# with NO saturation and unbounded accumulation. This is the
# per-product-rounded side of round 10's ULP separator -- the wide-MAC is
# the numerically tighter policy Forge COULD adopt, but the frozen oracle
# governs: the lowering below implements per-product rounding exactly.
HAMILTON = [  # (out component) = sum of sign * a[i] * b[j]
    [(+1, 0, 0), (-1, 1, 1), (-1, 2, 2), (-1, 3, 3)],
    [(+1, 0, 1), (+1, 1, 0), (+1, 2, 3), (-1, 3, 2)],
    [(+1, 0, 2), (-1, 1, 3), (+1, 2, 0), (+1, 3, 1)],
    [(+1, 0, 3), (+1, 1, 2), (-1, 2, 1), (+1, 3, 0)],
]

def tz_shift_py(p, n):
    q = abs(p) >> n
    return q if p >= 0 else -q

def oracle_qmul_py(w, n, A, B):
    """Parametric replication of e2_model.qmul at any (width, shift):
    per-product trunc0 shift, signed sum, NO saturation. Raises if a
    component leaves w-bit two's-complement range (a proxy-width
    artifact, not an oracle behavior)."""
    def s(v):
        return v - (1 << w) if v >= (1 << (w - 1)) else v
    out = []
    for row in HAMILTON:
        acc = 0
        for sg, i, j in row:
            acc += sg * tz_shift_py(s(A[i]) * s(B[j]), n)
        lo, hi = -(1 << (w - 1)), (1 << (w - 1)) - 1
        if not lo <= acc <= hi:
            raise OverflowError(f"component {acc} outside w={w}")
        out.append(acc & ((1 << w) - 1))
    return tuple(out)

def hcomp_case(w, n, terms):
    """Constant Hamilton COMPONENT under the ORACLE policy: each product
    shifted toward zero FIRST, then +/- accumulated at Wacc = 2w-n+2.
    Output: TUP( TUPw low bits , inrange flag ). No clamping ever."""
    _chk_mul(w, n, 0, 0)
    L = LetChain()
    Wp = 2 * w - n
    Wacc = Wp + 2
    exts = []
    for (sg, a, b) in terms:
        acc, Lm = mul_wide_case(w, a, b)
        L.lets.extend(Lm.lets)
        # per-product toward-zero shift (inline, copies from acc lets)
        pc = []
        for i in range(2 * w):
            needc = (1 if i < n else 2) + (1 if i == 2 * w - 1 else 0)
            pc.append(L.let(acc[i][0], needc, "hp"))
        if n:
            dropped = pc[0][0]
            for i in range(1, n):
                dropped = OR(dropped, pc[i][0])
            corr = L.let(AND(pc[2 * w - 1][-1], dropped), 4, "hc")
        else:
            corr = L.let(F, 4, "hc")
        srows = [pc[n + i][:2] for i in range(Wp)]
        q, _, _ = emit_add(Wp, srows, [[F] * 3 for _ in range(Wp)], corr,
                           L, s_copies=1)
        top = L.let(q[Wp - 1][0], Wacc - Wp + 1, "hx")
        bits = [q[i][0] for i in range(Wp - 1)] + [top[0]] + top[1:]
        exts.append((sg, bits))
    sg0, bits0 = exts[0]
    accc = [L.let(b, 2, "ha") for b in bits0]
    if sg0 < 0:
        na = [[NOT(c[0]), NOT(c[1])] for c in accc]
        accc, _, _ = emit_add(Wacc, na, [[F] * 3 for _ in range(Wacc)],
                              [T] * 4, L, s_copies=2)
    for (sg, bits) in exts[1:]:
        rows = [L.let(b, 3, "ht") for b in bits]
        if sg > 0:
            nb = rows
            cin = [F] * 4
        else:
            nb = [[NOT(c) for c in row] for row in rows]
            cin = [T] * 4
        accc, _, _ = emit_add(Wacc, [c[:2] for c in accc],
                              [[r[0], r[1], r[2]] for r in nb], cin, L,
                              s_copies=2)
    # low-w value + in-range flag (bits w-1..Wacc-1 all equal): NO clamp
    n_cmp = Wacc - w
    qc = []
    for i in range(Wacc):
        if i < w - 1:
            needq = 1
        elif i == w - 1:
            needq = 2
        elif i < Wacc - 1:
            needq = 1
        else:
            needq = 2 * n_cmp
        qc.append(L.let(accc[i][0], needq, "hq"))
    inr = None
    for k, i in enumerate(range(w - 1, Wacc - 1)):
        s1, s2 = qc[Wacc - 1][2 * k], qc[Wacc - 1][2 * k + 1]
        xn = f"(({qc[i][-1]} {s1}) {NOT(s2)})"
        inr = xn if inr is None else AND(inr, xn)
    val = TUPN([qc[i][0] for i in range(w)])
    return L.wrap(TUPN([val, inr]))

def rot_step_case(w, n, rotor, pose):
    """Constant full rotation step (oracle policy): TUP4 of TUPw."""
    comps = []
    for row in HAMILTON:
        terms = [(sg, rotor[i], pose[j]) for sg, i, j in row
                 if rotor[i] != 0]
        comps.append(f"({TAKE0} {hcomp_case(w, n, terms)})")
    return TUPN(comps)

TAKE0 = "λhr.(hr λhv.λhf.hv)"     # component value, flag dropped (the
                                   # constant path asserts flags via the
                                   # dedicated hcomp battery)

def dyn_rot_step(w, n, rotor):
    """DYNAMIC pose, constant rotor: λP -> TUP4 of TUPw under the oracle
    policy. Products with a ZERO rotor component are skipped at emit
    time (fixture constants compile in); nonzero rotor components enter
    as encoded operands through the general verified dyn_mul_wide (the
    constant-B row-skipping multiplier is a measured 3b.5 optimization,
    not taken on faith here)."""
    _chk_mul(w, n, 0, 0)
    Pv = _v("P")
    cvs = [_v("pc") for _ in range(4)]
    uses = [sum(1 for row in HAMILTON for sg, i, j in row
                if j == k and rotor[i] != 0) for k in range(4)]
    A = _Alloc()
    ccs = [A.copies(cvs[k], uses[k]) for k in range(4)]
    idx = [0, 0, 0, 0]
    Wacc = 2 * w - n + 2
    comps = []
    for row in HAMILTON:
        exts = []
        for sg, i, j in row:
            if rotor[i] == 0:
                continue
            pcopy = ccs[j][idx[j]]
            idx[j] += 1
            prod = (f"(({dyn_mul_wide(w)} {enc_operand(rotor[i], w)}) "
                    f"{pcopy})")
            shifted = f"({dyn_shift_tz(2 * w, n)} {prod})"
            e = f"({dyn_sext(2 * w - n, Wacc)} {shifted})"
            if sg < 0:
                e = (f"({take_value_of('neg', Wacc)} "
                     f"({dyn_neg(Wacc)} {e}))")
            exts.append(e)
        s = exts[0]
        for e in exts[1:]:
            s = (f"({take_value_of('add', Wacc)} "
                 f"(({dyn_case('add', Wacc)} {s}) {e}))")
        comps.append(f"({dyn_trunc(Wacc, w)} {s})")
    inner = "".join(A.prefix) + TUPN(comps)
    inner = (f"({Pv} λ" + ".λ".join(cvs) + f".{inner})")
    return f"λ{Pv}.{inner}"

def golden_rot_forge(w, n, rotor, pose):
    """FORGE wide-MAC quaternion rotor step -- the SHIPPING pose-authority
    policy forge_motor_widemac_tz_sat_v1. Each Hamilton component is a
    SINGLE wide-MAC: full-precision products, ONE toward-zero shift, ONE
    saturation. Returns (4 lanes, fault). Contrast oracle_qmul_py, the
    frozen proc-e2.3 LEGACY policy (per-product trunc0, no saturation):
    the two agree at small widths but DIVERGE at Q32.32 by the certified
    ULP separator. This is the authority side of the 3b.5c typed bridge."""
    out = []
    fault = 0
    for row in HAMILTON:
        terms = [(sg, rotor[i], pose[j]) for sg, i, j in row]
        v, ov = golden_mac(w, n, terms)
        out.append(v)
        fault |= ov
    return tuple(out), fault

def dyn_rot_step_forge(w, n, rotor):
    """DYNAMIC pose, constant rotor, FORGE wide-MAC policy: λP -> TUP4 of
    TUPw. Each lane is one dyn_mac(w, n, signs) (exact w x w products,
    sign-extend to mac_headroom, +/- accumulate, ONE shift, ONE
    saturation). The ovf flag is dropped for the TUP4 pose shape -- the
    3b.5c certificate asserts fault == 0 at authority width (unit rotors
    cannot overflow; overflow is exercised by the golden battery). Rotor
    components enter as encoded constants; pose components are the dynamic
    argument, replicated per use via the affine allocator."""
    _chk_mul(w, n, 0, 0)
    Pv = _v("P")
    cvs = [_v("pc") for _ in range(4)]
    uses = [sum(1 for row in HAMILTON for sg, i, j in row if j == k)
            for k in range(4)]
    A = _Alloc()
    ccs = [A.copies(cvs[k], uses[k]) for k in range(4)]
    idx = [0, 0, 0, 0]
    comps = []
    for row in HAMILTON:
        signs = [sg for sg, i, j in row]
        app = dyn_mac(w, n, signs)
        for sg, i, j in row:
            pcopy = ccs[j][idx[j]]
            idx[j] += 1
            app = f"(({app} {enc_operand(rotor[i], w)}) {pcopy})"
        comps.append(f"({TAKE0} {app})")
    inner = "".join(A.prefix) + TUPN(comps)
    inner = (f"({Pv} λ" + ".λ".join(cvs) + f".{inner})")
    return f"λ{Pv}.{inner}"

def dyn_rot_step_forge_dyn(w, n):
    """FULLY DYNAMIC forge wide-MAC quaternion step -- the DYNAMIC Spinner
    (slice 3b.5d): λR.λP -> TUP4 of TUPw, both rotor R and pose P runtime
    TUP4 inputs. The rotor flows as data, so a rotor change needs no
    recompilation (contrast dyn_rot_step_forge, which bakes a constant
    rotor). Same forge policy per lane (one dyn_mac: exact products,
    sign-extend, +/- accumulate, ONE shift, ONE saturation); the ovf flag
    is dropped for the TUP4 pose shape (unit rotors cannot overflow; the
    golden battery exercises saturation). Each rotor and pose lane is
    replicated per use by the affine allocator."""
    _chk_mul(w, n, 0, 0)
    Rv, Pv = _v("R"), _v("P")
    rvs = [_v("rc") for _ in range(4)]
    pvs = [_v("pc") for _ in range(4)]
    ruses = [sum(1 for row in HAMILTON for sg, i, j in row if i == k)
             for k in range(4)]
    puses = [sum(1 for row in HAMILTON for sg, i, j in row if j == k)
             for k in range(4)]
    A = _Alloc()
    rcs = [A.copies(rvs[k], ruses[k]) for k in range(4)]
    pcs = [A.copies(pvs[k], puses[k]) for k in range(4)]
    ridx = [0, 0, 0, 0]
    pidx = [0, 0, 0, 0]
    comps = []
    for row in HAMILTON:
        signs = [sg for sg, i, j in row]
        app = dyn_mac(w, n, signs)
        for sg, i, j in row:
            rc = rcs[i][ridx[i]]
            ridx[i] += 1
            pc = pcs[j][pidx[j]]
            pidx[j] += 1
            app = f"(({app} {rc}) {pc})"
        comps.append(f"({TAKE0} {app})")
    inner = "".join(A.prefix) + TUPN(comps)
    inner = f"({Pv} λ" + ".λ".join(pvs) + f".{inner})"
    inner = f"({Rv} λ" + ".λ".join(rvs) + f".{inner})"
    return f"λ{Rv}.λ{Pv}.{inner}"

def dyn_rot_step_forge_dyn_f(w, n):
    """FULLY DYNAMIC forge wide-MAC quaternion step WITH authoritative
    fault (slice 3b.5d-2 -- the v0.6 Spinner operator): λR.λP ->
    TUP(pose4, overflow). Same fully-dynamic λR.λP shape and per-lane
    forge policy as dyn_rot_step_forge_dyn (exact products, sign-extend,
    +/- accumulate, ONE shift, ONE saturation), but here each lane's
    wide-MAC overflow flag is KEPT and the four are OR-reduced into a
    SINGLE authoritative overflow bit alongside the pose tuple. The world
    transition latches this bit into a STICKY numeric_fault (old OR new)
    and Film v0.6 records it; a runtime-configured saturating rotor is
    what exercises it. Contrast dyn_rot_step_forge_dyn, which drops the
    flags for the bare TUP4 pose shape (unit rotors cannot overflow)."""
    _chk_mul(w, n, 0, 0)
    Rv, Pv = _v("R"), _v("P")
    rvs = [_v("rc") for _ in range(4)]
    pvs = [_v("pc") for _ in range(4)]
    ruses = [sum(1 for row in HAMILTON for sg, i, j in row if i == k)
             for k in range(4)]
    puses = [sum(1 for row in HAMILTON for sg, i, j in row if j == k)
             for k in range(4)]
    A = _Alloc()
    rcs = [A.copies(rvs[k], ruses[k]) for k in range(4)]
    pcs = [A.copies(pvs[k], puses[k]) for k in range(4)]
    ridx = [0, 0, 0, 0]
    pidx = [0, 0, 0, 0]
    vals = []
    flags = []
    for row in HAMILTON:
        signs = [sg for sg, i, j in row]
        app = dyn_mac(w, n, signs)
        for sg, i, j in row:
            rc = rcs[i][ridx[i]]; ridx[i] += 1
            pc = pcs[j][pidx[j]]; pidx[j] += 1
            app = f"(({app} {rc}) {pc})"
        # dup the nested MAC result so we can read BOTH its value tuple
        # and its overflow flag (each is consumed exactly once).
        av, af = A.copies(app, 2)
        vv, vf = _v("mv"), _v("mf")
        fv, ff = _v("mv"), _v("mf")
        vals.append(f"({av} λ{vv}.λ{vf}.{vv})")
        flags.append(f"({af} λ{fv}.λ{ff}.{ff})")
    ovf = flags[-1]
    for fl in reversed(flags[:-1]):
        ovf = OR(fl, ovf)
    body = TUPN([TUPN(vals), ovf])
    inner = "".join(A.prefix) + body
    inner = f"({Pv} λ" + ".λ".join(pvs) + f".{inner})"
    inner = f"({Rv} λ" + ".λ".join(rvs) + f".{inner})"
    return f"λ{Rv}.λ{Pv}.{inner}"

def enc_pose(pose, w):
    return TUPN([enc_operand(c, w) for c in pose])

def dec_pose(t, w):
    xs = _spine(t, 4)
    return tuple(dec_bits_list(_spine(x, w)) for x in xs)


# ============ round-11 registry completions (reviewer conditions) ==========
RESULT_SHAPES.update({
    "mul_wide": ("flat", []),      # TUP(2w), no flags
    "shift_tz": ("flat", []),      # TUP(W-n), no flags
    "mac":      ("nested", ["overflow"]),
})

def mac_headroom(w, k):
    """Impossible-by-construction check, executable: k products of
    w-bit signed operands, each |p| <= 2^(2w-2), accumulate at
    Wacc = 2w + ceil(log2(k)): |sum| <= k * 2^(2w-2) < 2^(Wacc-1).
    Returns Wacc and asserts the bound strictly."""
    import math
    Wacc = 2 * w + max(1, math.ceil(math.log2(k)))
    assert k * (1 << (2 * w - 2)) < (1 << (Wacc - 1)), \
        "MAC accumulator width cannot wrap by construction"
    return Wacc

def dyn_mac4(w, n, signs):
    """PROMOTED from the 3b.3b battery: fully dynamic 4-term MAC
    (frozen Forge policy: exact products, sign-extend, +/- accumulate,
    ONE toward-zero shift, ONE saturation). λA0.λB0...λA3.λB3 ->
    nested TUP(valueTuple(w), ovf). Fresh instances per stage."""
    assert len(signs) == 4
    Wm = mac_headroom(w, 4)
    avs = [_v("MA") for _ in range(4)]
    bvs = [_v("MB") for _ in range(4)]
    exts = []
    for k in range(4):
        e = (f"({dyn_sext(2 * w, Wm)} (({dyn_mul_wide(w)} {avs[k]}) "
             f"{bvs[k]}))")
        if signs[k] < 0:
            e = f"({take_value_of('neg', Wm)} ({dyn_neg(Wm)} {e}))"
        exts.append(e)
    s = exts[0]
    for e in exts[1:]:
        s = (f"({take_value_of('add', Wm)} (({dyn_case('add', Wm)} {s}) "
             f"{e}))")
    body = f"({dyn_sat(Wm - n, w)} ({dyn_shift_tz(Wm, n)} {s}))"
    lam = "".join(f"λ{a}.λ{b}." for a, b in zip(avs, bvs))
    return lam + body


def dyn_mac(w, n, signs):
    """General k-term wide-MAC (k = len(signs)), the arbitrary-arity
    generalization of dyn_mac4 that Motor8 lanes need. Same frozen Forge
    policy: exact w x w products, sign-extend to Wm = mac_headroom(w, k),
    +/- accumulate, ONE toward-zero shift, ONE saturation.
    λA0.λB0...λA{k-1}.λB{k-1} -> nested TUP(valueTuple(w), ovf).
    Fresh stage instances per term (the compose/chain law)."""
    k = len(signs)
    assert k >= 1
    Wm = mac_headroom(w, k)
    avs = [_v("MA") for _ in range(k)]
    bvs = [_v("MB") for _ in range(k)]
    exts = []
    for t in range(k):
        e = (f"({dyn_sext(2 * w, Wm)} (({dyn_mul_wide(w)} {avs[t]}) "
             f"{bvs[t]}))")
        if signs[t] < 0:
            e = f"({take_value_of('neg', Wm)} ({dyn_neg(Wm)} {e}))"
        exts.append(e)
    s = exts[0]
    for e in exts[1:]:
        s = (f"({take_value_of('add', Wm)} (({dyn_case('add', Wm)} {s}) "
             f"{e}))")
    body = f"({dyn_sat(Wm - n, w)} ({dyn_shift_tz(Wm, n)} {s}))"
    lam = "".join(f"λ{a}.λ{b}." for a, b in zip(avs, bvs))
    return lam + body


# ============ round-12 numeric-policy identities (versioned) ==============
POLICY_LEGACY = "legacy_spinner_pp_tz_nosat_v1"   # proc-e2.3 oracle policy
POLICY_FORGE  = "forge_motor_widemac_tz_sat_v1"   # frozen Forge MAC law
