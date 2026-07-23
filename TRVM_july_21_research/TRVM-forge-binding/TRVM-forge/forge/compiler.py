"""compiler.py v0.2 -- graph-driven lowering with binary clock counters.

v0.2 (review round 6): arbitrary periodic periods and true once-clocks.
The representation choice -- one-hot Scott enums for periods <= 32,
ripple-carry binary counters above, a done-latch + wrapping binary
counter for once-clocks -- never changes meaning (Binding Law 5): all
periodics fire at t % period == phase forever; once fires exactly at its
epoch. The period-33 horizon bug (compiled as a saturating one-shot,
diverging from the model at t = 33) is dead by construction and pinned
by binding_run3's regression.

Binary circuits, per clock of width w (LSB-first bits):
    fire  = eq(k, phase-const)              [AND-fold of bit matches]
    j     = k + 1                           [ripple carry, carry-in T]
    k'    = eq(j, period-const) ? zeros : j [mod reset]      (periodic)
    fire  = NOT done AND eq(k, epoch)                        (once)
    done' = done OR fire; k' = k + 1 (wrapping; harmless: the latch
            suppresses any wrapped re-equality)              (once)
Every multi-use value goes through use-counted fresh-label dups; every
let's dup chain nests INSIDE its own binder (the slice-2 scoping law).
"""
from lower_e2a import _lab, _v, T, F, PAIR, OR
from fixture import Fixture

def NOT(a): return f"(({a} {F}) {T})"
def AND(a, b): return f"(({a} {b}) {F})"

def ENUM(size, i):
    vs = [_v("e") for _ in range(size)]
    return "λ" + ".λ".join(vs) + "." + vs[i]

def enum_apply(x, branches):
    s = x
    for b in branches:
        s = f"({s} {b})"
    return s

def TUPN(xs):
    f = _v("tf")
    s = f
    for x in xs:
        s = f"({s} {x})"
    return f"λ{f}.{s}"

class Alloc:
    def __init__(self):
        self.prefix = []
    def copies(self, name, n):
        if n <= 0:
            return []
        if n == 1:
            return [name]
        out = []
        cur = name
        for _ in range(n - 1):
            a, b = _v("da"), _v("db")
            self.prefix.append(f"!&{_lab()}{{{a},{b}}}={cur};")
            out.append(a)
            cur = b
        out.append(cur)
        return out

class LetChain:
    """Ordered lets; each value's fan-out dups nest inside its binder."""
    def __init__(self):
        self.lets = []            # (name, expr, [copies])
    def let(self, expr, ncopies, tag="lv"):
        nm = _v(tag)
        local = Alloc()
        cps = local.copies(nm, ncopies)
        self.lets.append((nm, expr, "".join(local.prefix)))
        return cps
    def wrap(self, inner):
        for nm, expr, dups in reversed(self.lets):
            inner = f"(λ{nm}.{dups}{inner} {expr})"
        return inner

def bits_of(n, w):
    return [(n >> i) & 1 for i in range(w)]

def eq_const(bit_srcs, const_bits):
    acc = None
    for src, cb in zip(bit_srcs, const_bits):
        m = src if cb else NOT(src)
        acc = m if acc is None else AND(acc, m)
    return acc if acc is not None else T

def emit_binary_counter(spec, binders, need_fire, L: LetChain, A: Alloc):
    """binders: the destructured field binders for this clock.
    Returns (fire_copies_or_None, newfield_src). Lets go into L."""
    if spec[0] == "binp":
        _, p, ph, w = spec
        kb = binders                       # w bit binders
        cps = [A.copies(b, 3) for b in kb]    # eq / sum-sel / carry-sel
        fire_cp = None
        if need_fire:
            fire_cp = L.let(eq_const([c[0] for c in cps],
                                     bits_of(ph, w)), 1, "fire")
        # ripple inc, carry-in T
        sums = []
        carry = None                       # copies list of current carry
        for i in range(w):
            b_sum, b_car = cps[i][1], cps[i][2]
            if i == 0:
                s_expr = NOT(b_sum)
                next_carry_expr = b_car
            else:
                s_expr = f"(({b_sum} {NOT(carry[0])}) {carry[1]})"
                next_carry_expr = f"(({b_car} {carry[2]}) {F})"
            sums.append(L.let(s_expr, 2, "s"))
            if i < w - 1:
                carry = L.let(next_carry_expr, 3, "c")
        rst = L.let(eq_const([s[0] for s in sums], bits_of(p, w)), 1, "rst")
        zeros = TUPN([F] * w)
        cand = TUPN([s[1] for s in sums])
        newfield = f"(({rst[0]} {zeros}) {cand})"
        return fire_cp, newfield
    # once
    _, e, w = spec
    done, kb = binders[0], binders[1:]
    d_cp = A.copies(done, 2)
    cps = [A.copies(b, 3) for b in kb]
    eq_cp = L.let(eq_const([c[0] for c in cps], bits_of(e, w)), 1, "eqo")
    n_fire = (1 if need_fire else 0) + 1          # hot + done-latch
    fire_cp = L.let(AND(NOT(d_cp[0]), eq_cp[0]), n_fire, "fireo")
    sums = []
    carry = None
    for i in range(w):
        b_sum, b_car = cps[i][1], cps[i][2]
        if i == 0:
            s_expr = NOT(b_sum)
            next_carry_expr = b_car
        else:
            s_expr = f"(({b_sum} {NOT(carry[0])}) {carry[1]})"
            next_carry_expr = f"(({b_car} {carry[2]}) {F})"
        sums.append(L.let(s_expr, 1, "s"))
        if i < w - 1:
            carry = L.let(next_carry_expr, 3, "c")
    newfield = TUPN([OR(d_cp[1], fire_cp[-1])] + [s[0] for s in sums])
    hot = fire_cp[0] if need_fire else None
    return ([hot] if hot else None), newfield

def field_binder_count(spec):
    if spec[0] == "onehot":
        return 1
    if spec[0] == "binp":
        return spec[3]
    return 1 + spec[2]                    # done + k bits

def compile_step(fx: Fixture):
    ppl, wires, doors, relays = fx.layout()
    orbs = list(getattr(fx, "orbs", []))
    fields = (["c_" + r for r in ppl] + list(wires) + list(doors)
              + list(relays) + ["pose_" + o for o in orbs])
    s = _v("st")
    tops = {f: _v("b") for f in fields}       # one binder per tuple slot
    # one-hot counters ARE the slot value (an enum); binary/once counters
    # are inner tuples destructured into bit binders
    cbinders = {}
    for r in ppl:
        spec = fx.counter_spec(r)
        if spec[0] == "onehot":
            cbinders[r] = None
        else:
            cbinders[r] = [_v("k")
                           for _ in range(field_binder_count(spec))]
    pa = {f: (_v("x"), _v("y")) for f in wires + doors + relays}
    # pose slots stay whole (TUP4 of TUPw): the rotation is applied by
    # Scott FUNCTION-selection -- ((sel λP.ROT) λP.P) slot -- so the
    # pose is consumed exactly once and the dead branch erases before
    # its interior reduces (non-firing epochs stay cheap; round 12)
    A = Alloc()
    L = LetChain()
    counter_new, fire_expr = {}, {}
    for r in ppl:
        spec = fx.counter_spec(r)
        outdeg = len(fx.out_wires(r))
        if spec[0] == "onehot":
            _, p, fi = spec
            cc = A.copies(tops["c_" + r], 1 + (1 if outdeg else 0))
            counter_new[r] = enum_apply(cc[0], [ENUM(p, (i + 1) % p)
                                                for i in range(p)])
            if outdeg:
                fire_expr[r] = enum_apply(cc[1], [T if i == fi else F
                                                  for i in range(p)])
        else:
            fire_cp, newf = emit_binary_counter(spec, cbinders[r],
                                                outdeg > 0, L, A)
            counter_new[r] = newf
            if outdeg:
                fire_expr[r] = fire_cp[0]
    relay_nc = {}
    for r in relays:
        outdeg = len(fx.out_wires(r))
        relay_nc[r] = A.copies(pa[r][1], 1 + (1 if outdeg else 0))
    hot_binds, hot_of = [], {}
    for role in list(ppl) + list(relays):
        outdeg = len(fx.out_wires(role))
        if not outdeg:
            continue
        hn = _v("hot")
        expr = fire_expr[role] if role in fire_expr else relay_nc[role][1]
        local = Alloc()
        hot_of[role] = local.copies(hn, outdeg)
        hot_binds.append((hn, expr, "".join(local.prefix)))
    wire_nc = {wr: A.copies(pa[wr][1], 2) for wr in wires}
    wire_hot = {}
    for role in list(ppl) + list(relays):
        for i, wr in enumerate(fx.out_wires(role)):
            wire_hot[wr] = hot_of[role][i]
    def merge_in(role):
        ins = fx.in_wires(role)
        if not ins:
            return F
        expr = wire_nc[ins[0]][1]
        for wr in ins[1:]:
            expr = OR(expr, wire_nc[wr][1])
        return expr
    new = {}
    import binlib as _BL
    for o in orbs:
        s = fx.controller_of(o)
        if s:
            w_, n_, rq = fx.spinners[s]
            sel = merge_in(s)
            idv = _v("pid")
            new["pose_" + o] = (f"((({sel} "
                                f"{_BL.dyn_rot_step(w_, n_, rq)}) "
                                f"λ{idv}.{idv}) {tops['pose_' + o]})")
        else:
            new["pose_" + o] = tops["pose_" + o]
    for r in ppl:
        new["c_" + r] = counter_new[r]
    for wr in wires:
        new[wr] = PAIR(wire_nc[wr][0], wire_hot[wr])
    for d in doors:
        new[d] = PAIR(pa[d][1], merge_in(d))
    for r in relays:
        new[r] = PAIR(relay_nc[r][0], merge_in(r))
    inner = TUPN([new[f] for f in fields])
    for (hn, expr, hdups) in reversed(hot_binds):
        inner = f"(λ{hn}.{hdups}{inner} {expr})"
    inner = L.wrap(inner)      # clock lets outside hot lets: hot exprs
                               # may reference fire lets
    inner = "".join(A.prefix) + inner
    for f in reversed(wires + doors + relays):
        x, y = pa[f]
        inner = f"({tops[f]} λ{x}.λ{y}.{inner})"
    for r in reversed(ppl):
        if cbinders[r] is not None:
            bs = cbinders[r]
            inner = (f"({tops['c_' + r]} λ" + ".λ".join(bs)
                     + f".{inner})")
    lam_args = ".λ".join(tops[f] for f in fields)
    return f"λ{s}.({s} λ{lam_args}.{inner})", fields

# ------------------------------------------------------- encode / decode
from lower_e2a import _dec_bool, _dec_enum, _spine, _dec_pair

def enc_bits(n, w):
    return [T if (n >> i) & 1 else F for i in range(w)]

def enc_state(fx, st):
    ppl, wires, doors, relays = fx.layout()
    parts = []
    for r in ppl:
        spec = fx.counter_spec(r)
        if spec[0] == "onehot":
            parts.append(ENUM(spec[1], st["c_" + r]))
        elif spec[0] == "binp":
            parts.append(TUPN(enc_bits(st["c_" + r], spec[3])))
        else:
            done, k = st["c_" + r]
            parts.append(TUPN([T if done else F]
                              + enc_bits(k, spec[2])))
    for f in list(wires) + list(doors) + list(relays):
        a, b = st[f]
        parts.append(PAIR(T if a else F, T if b else F))
    import binlib as _BL
    for o in getattr(fx, "orbs", []):
        s = fx.controller_of(o)
        w_, n_, _ = fx.spinners[s] if s else (8, 4, None)
        parts.append(_BL.enc_pose(st["pose_" + o], w_))
    return TUPN(parts)

def dec_bits(ts):
    return sum((1 << i) for i, t in enumerate(ts) if _dec_bool(t))

def dec_state(fx, t):
    ppl, wires, doors, relays = fx.layout()
    orbs = list(getattr(fx, "orbs", []))
    n = len(ppl) + len(wires) + len(doors) + len(relays) + len(orbs)
    xs = _spine(t, n)
    st, i = {}, 0
    for r in ppl:
        spec = fx.counter_spec(r)
        if spec[0] == "onehot":
            st["c_" + r] = _dec_enum(xs[i], spec[1])
        elif spec[0] == "binp":
            st["c_" + r] = dec_bits(_spine(xs[i], spec[3]))
        else:
            parts = _spine(xs[i], 1 + spec[2])
            st["c_" + r] = (int(_dec_bool(parts[0])),
                            dec_bits(parts[1:]))
        i += 1
    for f in list(wires) + list(doors) + list(relays):
        a, b = _dec_pair(xs[i])
        st[f] = (_dec_bool(a), _dec_bool(b))
        i += 1
    import binlib as _BL
    for o in orbs:
        s = fx.controller_of(o)
        w_, n_, _ = fx.spinners[s] if s else (8, 4, None)
        st["pose_" + o] = _BL.dec_pose(xs[i], w_)
        i += 1
    return st
