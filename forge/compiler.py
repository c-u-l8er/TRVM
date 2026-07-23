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
# NOTE (Phase 3D.1-D): `compile_step*` accept ANY object that duck-types the
# small read interface (the production `_PlanView` OR the Fixture oracle), so
# the compiler no longer imports the Fixture class -- keeping the production
# compile path (wrl_plan -> compiler) genuinely Fixture-free (D25).

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

def compile_step(fx, pose_policy="legacy"):
    """pose_policy selects the rotor-step numeric law for the compiled
    pose authority: "legacy" = legacy_spinner_pp_tz_nosat_v1 (per-product
    trunc0, matches proc-e2.3 e2_model.qmul VALUE); "forge" =
    forge_motor_widemac_tz_sat_v1 (wide-MAC, the shipping Spinner policy,
    the 3b.5c Q32.32 pose authority). The two agree at small widths but
    diverge at Q32.32 by the certified separator (slice 3b.5c)."""
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
            step = (_BL.dyn_rot_step_forge(w_, n_, rq)
                    if pose_policy == "forge"
                    else _BL.dyn_rot_step(w_, n_, rq))
            new["pose_" + o] = (f"((({sel} "
                                f"{step}) "
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

# ===================================================================
# Film v0.6 -- rotor-as-state, authoritative sticky numeric fault,
# same-epoch config-before-rotation (slice 3b.5d-2, GPT ruling 1A).
#
# The rotor is no longer a compiled-in fixture constant; it is canonical
# runtime STATE (a TUP4xTUPw field per controlling spinner).  Each epoch
# the compiled transition:
#   (1) COMMITs an already-accepted RotorConfigInput to the rotor state
#       field (NoChange keeps it, SetRotor(r) replaces it) -- this is the
#       "config write" phase, ordered BEFORE the reaction;
#   (2) REACTs: if the spinner's merged hot signal fires, it applies the
#       fully-dynamic forge step (dyn_rot_step_forge_dyn_f) reading the
#       JUST-COMMITTED rotor, producing (pose', overflow); the pose field
#       takes pose', and the numeric_fault field latches old OR overflow
#       (STICKY); if it does not fire, pose and fault are unchanged and
#       the committed rotor is still the new rotor state.
# "fixed" vs "configurable" is a PERMISSION distinction enforced at the
# config-acceptance layer (accept_rotor_config below), NOT two state
# layouts: every v0.6 spinner carries its rotor as state and reads it
# from state.  Raw ADMIT/claim-set lowering stays DEFERRED -- this slice
# applies an ALREADY-ACCEPTED config to compiled world state.

def enc_rotor_config(cfg, w):
    """RotorConfigInput encoder. cfg is None (NoChange) or a 4-tuple
    (SetRotor).  Scott sum: NoChange = λf.λg.f ; SetRotor(r) = λf.λg.(g r).
    Eliminated by eff = ((cfg rotor_state) λr.r)."""
    if cfg is None:
        return "λcnc.λcsr.cnc"
    import binlib as _BL
    return f"λcnc.λcsr.(csr {_BL.enc_pose(tuple(cfg), w)})"

def enc_config_bundle(fx, cfgs, resets=None):
    """The v0.6 EpochControl = TUP(rotor_bundle, fault_bundle) (GPT-5.6
    fault-reset ruling: rotor config targets a Spinner, fault control targets
    an Orb -- two independent families).
      rotor_bundle: per controlling spinner (orb order) NoChange | SetRotor.
      fault_bundle: per orb (orb order) KeepFault (F) | ResetFault (T).
    cfgs: {spinner_role: None | 4-tuple}; resets: {orb_role: True} (default
    None = every orb KeepFault). A global reset is user syntax that expands to
    a set of per-orb ResetFault flags here -- it is not a canonical primitive."""
    resets = resets or {}
    orbs = list(getattr(fx, "orbs", []))
    ctrl = [fx.controller_of(o) for o in orbs if fx.controller_of(o)]
    rparts = []
    for s in ctrl:
        w_, n_, _ = fx.spinners[s]
        rparts.append(enc_rotor_config(cfgs.get(s), w_))
    fparts = [T if resets.get(o) else F for o in orbs]
    return TUPN([TUPN(rparts), TUPN(fparts)])

def _v6_fields(fx):
    ppl, wires, doors, relays = fx.layout()
    orbs = list(getattr(fx, "orbs", []))
    base = ["c_" + r for r in ppl] + list(wires) + list(doors) \
        + list(relays)
    posef = []
    for o in orbs:
        posef += ["pose_" + o, "fault_" + o]
    rotorf = ["rotor_" + fx.controller_of(o) for o in orbs
              if fx.controller_of(o)]
    return base, posef, rotorf, (base + posef + rotorf)

def compile_step_v6(fx):
    """The v0.6 transition: λcfg.λst -> st'. cfg is enc_config_bundle(...);
    the forge dynamic-fault operator is the DEFAULT (and only) rotor law.
    Everything discrete (counters, wires, doors, relays) is identical to
    compile_step; only the spinner/orb reaction differs (rotor-as-state,
    committed config, sticky fault)."""
    import binlib as _BL
    ppl, wires, doors, relays = fx.layout()
    orbs = list(getattr(fx, "orbs", []))
    _, _, _, fields = _v6_fields(fx)
    s = _v("st")
    tops = {f: _v("b") for f in fields}
    cbinders = {}
    for r in ppl:
        spec = fx.counter_spec(r)
        cbinders[r] = None if spec[0] == "onehot" else \
            [_v("k") for _ in range(field_binder_count(spec))]
    pa = {f: (_v("x"), _v("y")) for f in wires + doors + relays}
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

    def fire_branch(w_, n_):
        fr, fp, fo = _v("fr"), _v("fp"), _v("fo")
        res = f"(({_BL.dyn_rot_step_forge_dyn_f(w_, n_)} {fr}) {fp})"
        la = Alloc()
        ra, rb = la.copies(res, 2)
        pv, ov = _v("pv"), _v("ov")
        pw, ow = _v("pv"), _v("ov")
        pose_part = f"({ra} λ{pv}.λ{ov}.{pv})"
        ovf_part = f"({rb} λ{pw}.λ{ow}.{ow})"
        body = "".join(la.prefix) + TUPN([pose_part, OR(fo, ovf_part)])
        return f"λ{fr}.λ{fp}.λ{fo}.{body}"

    def nofire_branch():
        fr, fp, fo = _v("fr"), _v("fp"), _v("fo")
        return f"λ{fr}.λ{fp}.λ{fo}.{TUPN([fp, fo])}"

    ctrl = [fx.controller_of(o) for o in orbs if fx.controller_of(o)]
    cfg_bind = {s2: _v("cfg") for s2 in ctrl}
    # per-orb fault-control binder (GPT-5.6 ruling): fault belongs to the Orb,
    # so ResetFault is a separate per-orb input (T = reset, F = keep). COMMIT
    # clears the historical fault first (fault_base); REACT then ORs in this
    # epoch's overflow -- a reset can never hide a same-epoch failure.
    fault_bind = {o: _v("frst") for o in orbs}
    new = {}
    for o in orbs:
        # COMMIT the fault reset: fault_base = ((reset F) old_fault)
        fbase = f"(({fault_bind[o]} {F}) {tops['fault_' + o]})"
        s2 = fx.controller_of(o)
        if not s2:
            new["pose_" + o] = tops["pose_" + o]
            new["fault_" + o] = fbase         # no controller: reset only
            continue
        w_, n_, _ = fx.spinners[s2]
        # (1) COMMIT config to rotor state: eff = ((cfg rotor_state) λr.r)
        rid = _v("rid")
        eff = f"(({cfg_bind[s2]} {tops['rotor_' + s2]}) λ{rid}.{rid})"
        effc = A.copies(eff, 2)          # [0] reacts, [1] new rotor state
        # (2) REACT: firing selection over the committed rotor, folding the
        # current overflow into the RESET (fault_base), not the old fault.
        sel = merge_in(s2)
        branch = f"(({sel} {fire_branch(w_, n_)}) {nofire_branch()})"
        pf = (f"((({branch} {effc[0]}) {tops['pose_' + o]}) {fbase})")
        pfc = A.copies(pf, 2)
        pp, pfl = _v("pp"), _v("pfl")
        qp, qfl = _v("pp"), _v("pfl")
        new["pose_" + o] = f"({pfc[0]} λ{pp}.λ{pfl}.{pp})"
        new["fault_" + o] = f"({pfc[1]} λ{qp}.λ{qfl}.{qfl})"
        new["rotor_" + s2] = effc[1]
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
    inner = L.wrap(inner)
    inner = "".join(A.prefix) + inner
    for f in reversed(wires + doors + relays):
        x, y = pa[f]
        inner = f"({tops[f]} λ{x}.λ{y}.{inner})"
    for r in reversed(ppl):
        if cbinders[r] is not None:
            bs = cbinders[r]
            inner = (f"({tops['c_' + r]} λ" + ".λ".join(bs)
                     + f".{inner})")
    # destructure the EpochControl = TUP(rotor_bundle, fault_bundle) OUTSIDE
    # the state destructuring so every control binder is in scope. rotor
    # bundle -> per controlling spinner (orb order); fault bundle -> per orb.
    cfgv = _v("ec")
    rbv, fbv = _v("rb"), _v("fb")
    lam_args = ".λ".join(tops[f] for f in fields)
    body = f"({s} λ{lam_args}.{inner})"
    if orbs:
        fb_args = ".λ".join(fault_bind[o] for o in orbs)
        body = f"({fbv} λ{fb_args}.{body})"
    if ctrl:
        rb_args = ".λ".join(cfg_bind[s2] for s2 in ctrl)
        body = f"({rbv} λ{rb_args}.{body})"
    body = f"({cfgv} λ{rbv}.λ{fbv}.{body})"
    return f"λ{cfgv}.λ{s}.{body}", fields

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

# ---------------------------------------------------- v0.6 state codec
def enc_state_v6(fx, st):
    """v0.6 layout: base (counters/wires/doors/relays) then per orb
    (pose, fault) then per controlling spinner (rotor)."""
    import binlib as _BL
    base, posef, rotorf, fields = _v6_fields(fx)
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
            parts.append(TUPN([T if done else F] + enc_bits(k, spec[2])))
    for f in list(wires) + list(doors) + list(relays):
        a, b = st[f]
        parts.append(PAIR(T if a else F, T if b else F))
    for o in fx.orbs:
        s = fx.controller_of(o)
        w_, n_, _ = fx.spinners[s] if s else (8, 4, None)
        parts.append(_BL.enc_pose(st["pose_" + o], w_))
        parts.append(T if st.get("fault_" + o) else F)
    for o in fx.orbs:
        s = fx.controller_of(o)
        if not s:
            continue
        w_, n_, _ = fx.spinners[s]
        parts.append(_BL.enc_pose(st["rotor_" + s], w_))
    return TUPN(parts)

def dec_state_v6(fx, t):
    import binlib as _BL
    base, posef, rotorf, fields = _v6_fields(fx)
    ppl, wires, doors, relays = fx.layout()
    orbs = list(fx.orbs)
    ctrl = [fx.controller_of(o) for o in orbs if fx.controller_of(o)]
    n = (len(ppl) + len(wires) + len(doors) + len(relays)
         + 2 * len(orbs) + len(ctrl))
    xs = _spine(t, n)
    st, i = {}, 0
    for r in ppl:
        spec = fx.counter_spec(r)
        if spec[0] == "onehot":
            st["c_" + r] = _dec_enum(xs[i], spec[1])
        elif spec[0] == "binp":
            st["c_" + r] = dec_bits(_spine(xs[i], spec[3]))
        else:
            pp = _spine(xs[i], 1 + spec[2])
            st["c_" + r] = (int(_dec_bool(pp[0])), dec_bits(pp[1:]))
        i += 1
    for f in list(wires) + list(doors) + list(relays):
        a, b = _dec_pair(xs[i])
        st[f] = (_dec_bool(a), _dec_bool(b))
        i += 1
    for o in orbs:
        s = fx.controller_of(o)
        w_, n_, _ = fx.spinners[s] if s else (8, 4, None)
        st["pose_" + o] = _BL.dec_pose(xs[i], w_)
        i += 1
        st["fault_" + o] = int(_dec_bool(xs[i]))
        i += 1
    for o in orbs:
        s = fx.controller_of(o)
        if not s:
            continue
        w_, n_, _ = fx.spinners[s]
        st["rotor_" + s] = _BL.dec_pose(xs[i], w_)
        i += 1
    return st

class RotorConfigError(ValueError):
    """Typed rejection at the config-acceptance layer (v0.6)."""

def accept_rotor_config(fx, s, cfg):
    """Permission + type gate for a rotor SetRotor on spinner s. Returns
    the accepted config (None for NoChange, a 4-tuple for SetRotor) or
    raises RotorConfigError. 'fixed' spinners reject any SetRotor; type
    mismatches (wrong lane count / geometry / out-of-range) are rejected.
    This is the ALREADY-ACCEPTED gate; the compiled circuit only APPLIES
    an accepted config."""
    if cfg is None:
        return None
    w_, n_, _ = fx.spinners[s]
    if not fx.is_configurable(s):
        raise RotorConfigError(
            f"{s}: fixed spinner rejects rotor write")
    if not (isinstance(cfg, tuple) and len(cfg) == 4):
        raise RotorConfigError(f"{s}: rotor must be a 4-tuple")
    for v in cfg:
        if not (isinstance(v, int) and 0 <= v < (1 << w_)):
            raise RotorConfigError(
                f"{s}: rotor lane {v!r} out of range for w={w_}")
    return cfg
