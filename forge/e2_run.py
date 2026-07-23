"""E2 falsification runner v2.2 — equivocation convergence matrix, dual-phase
fault injection, EV_CONFIG fixtures (no out-of-step mutation), content-
addressed rulepack, malformed-event handling."""

import copy
import random
from e2_model import (World, PhaseFault, StepCeiling, RandomChooser,
                      ZeroChooser, PathChooser, tariff_cost, PREFABS,
                      compute_rulepack, RULEPACK_HASH, OUT_PORTS, LEGAL_PAIRS,
                      SIG_MERGE, CONFIGURABLE, TARIFF_V03, NUMERIC_POLICY,
                      PROC_RULES_VERSION, digest_event, qnorm2, qmul, ONE,
                      QID, ROT_Z90, ROT_X90, H)

SCHEDULES = 300
RESULTS = []


def E(seq, op, writer="local", **kw):
    return dict(seq=seq, op=op, writer=writer, **kw)


def accepted_receipt(w, seq, writer="local"):
    for st, rc in w.claims[H("event", writer, seq)].values():
        if st == "accepted":
            return rc
    return None


def placed_id(w, seq, writer="local"):
    return accepted_receipt(w, seq, writer)[1]


def claimset(w):
    return {eid: tuple(sorted((dg, st) for dg, (st, _) in cl.items()))
            for eid, cl in w.claims.items()}


def global_invariant(w):
    live = sum(o["cost"] for o in w.objs.values())
    return 0 <= w.P - w.N <= w.cap and live == w.P - w.N


def run_case(name, law, build, epochs=4, schedules=SCHEDULES, check=None):
    hashes, law_ok = set(), True
    for s in range(schedules):
        ch = RandomChooser(random.Random(1000 + s))
        w, script = build()
        seq_hash = []
        for t in range(epochs):
            seq_hash.append(w.step(script.get(t, []), ch))
            law_ok &= global_invariant(w)
        hashes.add(tuple(seq_hash))
        if check:
            law_ok &= bool(check(w))
    ok = len(hashes) == 1 and law_ok
    RESULTS.append((name, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name:40s} schedules={schedules} "
          f"unique={len(hashes)} law={'ok' if law_ok else 'VIOLATED'} ({law})")


def ids_of(w, kind):
    return sorted(i for i, o in w.objs.items() if o["kind"] == kind)


SIG = dict(src_port="sig_out", dst_port="sig_in")
SOCK = dict(src_port="socket", dst_port="pose")
CFG = lambda seq, tid, f, v, writer="local": E(seq, "CONFIG", writer=writer,
                                               target=tid, field=f, value=v)

# ------------------------------------------------------------------ E2b core

def case_budget_race():
    def build():
        w = World(cap=tariff_cost("block") + 5)
        return w, {0: [E(2, "STAMP", kind="block"), E(1, "STAMP", kind="block")]}
    def check(w):
        return (len(ids_of(w, "block")) == 1 and placed_id(w, 1) in w.objs
                and (2, "local", "budget") in w.rejects)
    run_case("two stamps vs remaining budget", "lower seq wins, by id",
             build, epochs=1, check=check)


def case_multiwriter_ids():
    def build():
        w = World()
        return w, {0: [E(1, "STAMP", kind="block", writer="A"),
                       E(1, "STAMP", kind="block", writer="B")]}
    def check(w):
        return (len(ids_of(w, "block")) == 2
                and w.P - w.N == 2 * tariff_cost("block")
                and placed_id(w, 1, "A") != placed_id(w, 1, "B"))
    run_case("same seq, two writers", "writer-complete ids (M1)", build,
             epochs=1, check=check)


def case_multiwriter_order():
    cap = tariff_cost("door") + 1
    def outcome(order):
        w = World(cap=cap)
        a = E(1, "STAMP", kind="block", writer="A")
        b = E(1, "STAMP", kind="door", writer="B")
        h = w.step([a, b] if order == "AB" else [b, a],
                   RandomChooser(random.Random(9)))
        return h, bool(ids_of(w, "block")), bool(ids_of(w, "door"))
    ab, ba = outcome("AB"), outcome("BA")
    ok = ab == ba and ab[1] and not ab[2]
    RESULTS.append(("tied seq, host order", ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {'tied seq, host order':40s} "
          f"AB==BA={ab == ba}; writer A wins both (M2)")


def case_equivocation_matrix():
    """Round six's required permanent test: same event identity, Block and
    Door payloads, every arrival order and retransmission pattern."""
    b = E(1, "STAMP", kind="block", writer="A")
    d = E(1, "STAMP", kind="door", writer="A")
    smaller = "block" if digest_event(b) < digest_event(d) else "door"

    def run(script):
        w = World()
        ch = RandomChooser(random.Random(5))
        hs = [w.step(evs, ch) for evs in script]
        return w, hs

    # P1/P2: same batch, opposite host orders -> digest policy decides
    w1, h1 = run([[b, d]])
    w2, h2 = run([[d, b]])
    same_batch_ok = (h1 == h2
                     and ids_of(w1, smaller) and not ids_of(
                         w1, "door" if smaller == "block" else "block"))
    # P3/P4: cross batch, opposite log orders -> log order decides
    w3, _ = run([[b], [d]])
    w4, _ = run([[d], [b]])
    log_ok = (ids_of(w3, "block") and not ids_of(w3, "door")
              and ids_of(w4, "door") and not ids_of(w4, "block"))
    # RECOGNITION layer converges across ALL four arrival patterns:
    # identical observed-digest sets and disputed status. The ACCEPTANCE
    # layer is log-relative by design (Stage One policy) — P1/P2 share one
    # canonical log (same batch, digest-tiebroken) and must fully agree;
    # P3/P4 are different logs and legitimately accept different payloads.
    eid = H("event", "A", 1)
    digest_sets = {frozenset(x.claims[eid].keys()) for x in (w1, w2, w3, w4)}
    claims_ok = (len(digest_sets) == 1
                 and len(w1.claims[eid]) == 2
                 and all(x.recognition(eid) == "disputed"
                         for x in (w1, w2, w3, w4))
                 and claimset(w1) == claimset(w2))
    # retransmission of EITHER claim after dispute: zero state change
    idem_ok = True
    for w in (w3, w4):
        before = w.canonical_hash()
        w.step([copy.deepcopy(b)], RandomChooser(random.Random(6)))
        w.step([copy.deepcopy(d)], RandomChooser(random.Random(6)))
        after = w.canonical_hash()
        idem_ok &= (before != after) is False or True
        # hashes advance t; compare state minus t: easier — replay same t?
    # t advances even on idempotent epochs, so compare claims/objs/budget only
    def core(w):
        return (frozenset(claimset(w).items()), tuple(sorted(w.objs)),
                w.P, w.N, tuple(sorted(map(str, w.rejects))))
    w5, _ = run([[b], [d]])
    pre = core(w5)
    w5.step([copy.deepcopy(d)], RandomChooser(random.Random(6)))
    w5.step([copy.deepcopy(b)], RandomChooser(random.Random(6)))
    idem_ok = core(w5) == pre
    ok = same_batch_ok and log_ok and claims_ok and idem_ok
    RESULTS.append(("equivocation convergence matrix", ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {'equivocation convergence matrix':40s} "
          f"same-batch orders agree (digest policy, winner={smaller}); "
          f"cross-batch follows log order; claim sets identical over all 4 "
          f"patterns; recognition=disputed; retransmit either claim = no "
          f"core-state change (Q1/Q2)")


def case_noncommutative_rotations():
    expected = qmul(ROT_Z90, qmul(ROT_X90, QID))
    def build():
        w = World()
        w.step([E(1, "STAMP", kind="block")], ZeroChooser())
        bid = placed_id(w, 1)
        return w, {0: [E(3, "ROTATE", target=bid, rotor=ROT_Z90),
                       E(2, "ROTATE", target=bid, rotor=ROT_X90)]}
    def check(w):
        return tuple(w.objs[placed_id(w, 1)]["pose"][0:4]) == expected
    run_case("noncommuting rotations, one pose", "seq order picks Z∘X",
             build, epochs=1, check=check)


def case_move_delete():
    def build():
        w = World()
        w.step([E(1, "STAMP", kind="block")], ZeroChooser())
        bid = placed_id(w, 1)
        return w, {0: [E(2, "DELETE", target=bid),
                       E(3, "MOVE", target=bid, dpos=[ONE, 0, 0])]}
    def check(w):
        return not ids_of(w, "block") and (3, "local", "dangling") in w.rejects
    run_case("move after delete", "tombstone REJECT", build, epochs=1,
             check=check)


def case_link_delete():
    def build():
        w = World()
        w.step([E(1, "STAMP", kind="pulser"), E(2, "STAMP", kind="door")],
               ZeroChooser())
        return w, {0: [E(3, "DELETE", target=placed_id(w, 2)),
                       E(4, "LINK", target=placed_id(w, 1),
                         dst=placed_id(w, 2), **SIG)]}
    def check(w):
        return len(w.wires) == 0 and any(r[0] == 4 for r in w.rejects)
    run_case("link after delete", "deterministic REJECT", build, epochs=1,
             check=check)


def make_gate_world(n):
    w = World()
    evs = [E(i + 1, "STAMP", kind="pulser") for i in range(n)]
    evs.append(E(9, "STAMP", kind="door"))
    w.step(evs, ZeroChooser())
    d = placed_id(w, 9)
    batch = []
    for i in range(n):
        p = placed_id(w, i + 1)
        batch += [CFG(20 + 3 * i, p, "period", 1000),
                  CFG(21 + 3 * i, p, "phase", 3),
                  E(22 + 3 * i, "LINK", target=p, dst=d, **SIG)]
    w.step(batch, ZeroChooser())
    w._d = d
    return w


def case_gate_truth_table():
    timelines, hashes_ok = {}, True
    for n in (0, 1, 2):
        seen = set()
        for s in range(SCHEDULES):
            w = make_gate_world(n)
            ch = RandomChooser(random.Random(3000 + s))
            seen.add(tuple(w.step([], ch) and w.objs[w._d]["open"]
                           for _ in range(5)))
        hashes_ok &= len(seen) == 1
        timelines[n] = seen.pop()
    law = (timelines[0] == (0,) * 5 and timelines[1] == (0, 0, 0, 1, 0)
           and timelines[2] == timelines[1])
    ok = hashes_ok and law
    RESULTS.append(("gate OR truth table", ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {'gate OR truth table':40s} "
          f"0={timelines[0]} 1={timelines[1]} 2={timelines[2]} "
          f"(fixtures via EV_CONFIG, no out-of-step mutation)")


def case_spinner_fanin():
    def build():
        w = World()
        w.step([E(1, "STAMP", kind="pulser"), E(2, "STAMP", kind="pulser"),
                E(3, "STAMP", kind="spinner")], ZeroChooser())
        s = placed_id(w, 3)
        return w, {0: [E(4, "LINK", target=placed_id(w, 1), dst=s, **SIG),
                       E(5, "LINK", target=placed_id(w, 2), dst=s, **SIG)]}
    def check(w):
        return len(w.wires) == 1 and (5, "local", "fanin") in w.rejects
    run_case("two wires into spinner", "merge=none REJECT", build, epochs=1,
             check=check)


def case_controller_exclusive():
    def build():
        w = World()
        w.step([E(1, "STAMP", kind="spinner"), E(2, "STAMP", kind="spinner"),
                E(3, "STAMP", kind="orb")], ZeroChooser())
        o = placed_id(w, 3)
        return w, {0: [E(4, "LINK", target=placed_id(w, 1), dst=o, **SOCK),
                       E(5, "LINK", target=placed_id(w, 2), dst=o, **SOCK)]}
    def check(w):
        return (w.objs[placed_id(w, 3)]["controller"] == placed_id(w, 1)
                and (5, "local", "controlled") in w.rejects)
    run_case("two spinners, one pose", "lower-seq owns", build, epochs=1,
             check=check)


def case_controller_release():
    def build():
        w = World()
        w.step([E(1, "STAMP", kind="spinner"), E(2, "STAMP", kind="spinner"),
                E(3, "STAMP", kind="orb")], ZeroChooser())
        o = placed_id(w, 3)
        w.step([E(4, "LINK", target=placed_id(w, 1), dst=o, **SOCK)],
               ZeroChooser())
        return w, {0: [E(5, "DELETE", target=placed_id(w, 1))],
                   1: [E(6, "LINK", target=placed_id(w, 2), dst=o, **SOCK)]}
    def check(w):
        return (w.objs[placed_id(w, 3)]["controller"] == placed_id(w, 2)
                and not any(r[0] == 6 for r in w.rejects))
    run_case("delete controller, relink", "capability released", build,
             epochs=2, check=check)


def latency_world():
    w = World()
    w.step([E(1, "STAMP", kind="pulser"), E(2, "STAMP", kind="door")],
           ZeroChooser())
    p, d = placed_id(w, 1), placed_id(w, 2)
    w.step([CFG(3, p, "period", 1000), CFG(4, p, "phase", 3),
            E(5, "LINK", target=p, dst=d, **SIG)], ZeroChooser())
    w._d = d
    return w


def case_two_tick_latency():
    seen = set()
    for s in range(SCHEDULES):
        w = latency_world()
        ch = RandomChooser(random.Random(2000 + s))
        seen.add(tuple(w.step([], ch) and w.objs[w._d]["open"]
                       for _ in range(5)))
    ok = seen == {(0, 0, 0, 1, 0)}
    RESULTS.append(("commit vs gate signal", ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {'commit vs gate signal':40s} "
          f"timelines={seen}")


def case_wire_timeline():
    def build():
        w = World()
        w.step([E(1, "STAMP", kind="pulser"), E(2, "STAMP", kind="door")],
               ZeroChooser())
        p, d = placed_id(w, 1), placed_id(w, 2)
        w.step([CFG(3, p, "period", 1), CFG(4, p, "phase", 0),
                E(5, "LINK", target=p, dst=d, **SIG)], ZeroChooser())
        w._d = d
        return w
    seen = set()
    for s in range(SCHEDULES):
        w = build()
        ch = RandomChooser(random.Random(4000 + s))
        seen.add(tuple(w.step([], ch) and w.objs[w._d]["open"]
                       for _ in range(6)))
    ok = seen == {(0, 1, 1, 1, 1, 1)}
    RESULTS.append(("commit vs wire write", ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {'commit vs wire write':40s} "
          f"timelines={seen}")


def case_delete_refund_once():
    def build():
        w = World()
        w.step([E(1, "STAMP", kind="block")], ZeroChooser())
        b = placed_id(w, 1)
        return w, {0: [E(2, "DELETE", target=b)], 1: [E(3, "DELETE", target=b)]}
    def check(w):
        c = tariff_cost("block")
        return w.P == c and w.N == c and (3, "local", "dangling") in w.rejects
    run_case("delete twice", "exactly one refund", build, epochs=2, check=check)


def case_duplicate_then_delete():
    def build():
        w = World()
        w.step([E(1, "STAMP", kind="block")], ZeroChooser())
        a = placed_id(w, 1)
        return w, {0: [E(2, "STAMP", kind="block",
                         pose=(ONE, 0, 0, 0, ONE, 0, 0))],
                   1: [E(3, "DELETE", target=a)]}
    def check(w):
        return (len(ids_of(w, "block")) == 1
                and w.P - w.N == tariff_cost("block")
                and "tombstone" in w.handles.values())
    run_case("duplicate then delete original", "no double refund", build,
             epochs=2, check=check)


def case_type_battery():
    def build():
        w = World()
        w.step([E(1, "STAMP", kind="block"), E(2, "STAMP", kind="door"),
                E(3, "STAMP", kind="pulser"), E(4, "STAMP", kind="orb"),
                E(5, "STAMP", kind="spinner")], ZeroChooser())
        b, d, p, o, s = (placed_id(w, i) for i in range(1, 6))
        return w, {0: [
            E(10, "LINK", target=b, dst=d, **SIG),
            E(11, "LINK", target=p, dst=o, **SOCK),
            E(12, "LINK", target=p, dst=o, src_port="sig_out", dst_port="pose"),
            E(13, "LINK", target=s, dst=d, src_port="socket", dst_port="sig_in"),
            E(14, "LINK", target=p, dst=o, **SIG),
            E(15, "LINK", target=p, dst=d, **SIG),
            E(16, "LINK", target=s, dst=o, **SOCK),
        ]}
    def check(w):
        r = w.rejects
        return (len(w.wires) == 1
                and (10, "local", "nosrcport") in r
                and (11, "local", "nosrcport") in r
                and (12, "local", "type") in r and (13, "local", "type") in r
                and (14, "local", "notyped") in r
                and w.objs[placed_id(w, 4)]["controller"] == placed_id(w, 5))
    run_case("typed linking battery", "src port + pair + dst law", build,
             epochs=1, check=check)


def case_config_battery():
    def build():
        w = World()
        w.step([E(1, "STAMP", kind="pulser"), E(2, "STAMP", kind="spinner"),
                E(3, "STAMP", kind="block")], ZeroChooser())
        p, s, b = placed_id(w, 1), placed_id(w, 2), placed_id(w, 3)
        return w, {0: [CFG(10, p, "period", 7),
                       CFG(11, s, "rotor", ROT_X90),
                       CFG(12, p, "period", 0),      # below min -> reject
                       CFG(13, b, "period", 5),      # block: not configurable
                       CFG(14, p, "phase", "x")]}    # wrong type -> reject
    def check(w):
        p, s = placed_id(w, 1), placed_id(w, 2)
        r = w.rejects
        return (w.objs[p]["period"] == 7
                and tuple(w.objs[s]["rotor"]) == ROT_X90
                and (12, "local", "config") in r
                and (13, "local", "config") in r
                and (14, "local", "config") in r)
    run_case("EV_CONFIG battery", "typed tunables; no out-of-step mutation "
             "(Q5)", build, epochs=1, check=check)


def case_malformed():
    def build():
        w = World()
        return w, {0: [E(1, "STAMP", kind="block"),
                       dict(seq="one", op="STAMP", writer="A", kind="door"),
                       dict(seq=2, op="NOPE", writer="A")]}
    def check(w):
        return (len(ids_of(w, "block")) == 1 and not ids_of(w, "door")
                and sum(1 for r in w.rejects if r[0] == "malformed") == 2)
    run_case("malformed events", "schema-rejected deterministically (Q6)",
             build, epochs=1, check=check)


def ceiling_negative():
    w = World(ceiling=3)
    try:
        w.step([E(1, "STAMP", kind="block")], ZeroChooser())
        ok = False
    except StepCeiling:
        ok = True
    RESULTS.append(("ceiling covers ADMIT/graft", ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {'ceiling covers ADMIT/graft':40s} "
          f"detected (metric = charged semantic steps; membership scans are "
          f"uncharged bookkeeping, stated) (Q7)")


def rulepack_content_test():
    same = compute_rulepack(PREFABS, OUT_PORTS, LEGAL_PAIRS, SIG_MERGE,
                            CONFIGURABLE, TARIFF_V03, NUMERIC_POLICY,
                            PROC_RULES_VERSION)
    t2 = dict(TARIFF_V03); t2["T_node"] = 5
    p2 = copy.deepcopy(PREFABS); p2["door"]["mut"] = 3
    m2 = dict(SIG_MERGE); m2["spinner"] = "or"
    diffs = {compute_rulepack(PREFABS, OUT_PORTS, LEGAL_PAIRS, SIG_MERGE,
                              CONFIGURABLE, t2, NUMERIC_POLICY,
                              PROC_RULES_VERSION),
             compute_rulepack(p2, OUT_PORTS, LEGAL_PAIRS, SIG_MERGE,
                              CONFIGURABLE, TARIFF_V03, NUMERIC_POLICY,
                              PROC_RULES_VERSION),
             compute_rulepack(PREFABS, OUT_PORTS, LEGAL_PAIRS, m2,
                              CONFIGURABLE, TARIFF_V03, NUMERIC_POLICY,
                              PROC_RULES_VERSION)}
    ok = same == RULEPACK_HASH and RULEPACK_HASH not in diffs \
        and len(diffs) == 3
    RESULTS.append(("content-addressed rulepack", ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {'content-addressed rulepack':40s} "
          f"stable under identity; moves under tariff/schema/merge edits; "
          f"procedural rules enter via version commitment (full addressing "
          f"queued with portable encoding) (Q4)")


def oracle_sensitivity():
    w = World()
    w.step([E(1, "STAMP", kind="pulser"), E(2, "STAMP", kind="spinner"),
            E(3, "STAMP", kind="orb"), E(4, "STAMP", kind="door")],
           ZeroChooser())
    w.step([E(5, "LINK", target=placed_id(w, 1), dst=placed_id(w, 4), **SIG),
            E(6, "LINK", target=placed_id(w, 2), dst=placed_id(w, 3), **SOCK)],
           ZeroChooser())
    base = w.canonical_hash()
    muts = {
        "lineage": lambda v: setattr(v, "lineage", "mapB"),
        "ceiling": lambda v: setattr(v, "ceiling", 7),
        "wire src_id": lambda v: list(v.wires.values())[0].update(src_id="X"),
        "spinner rotor": lambda v: v.objs[placed_id(v, 2)].update(
            rotor=(1, 2, 3, 4)),
        "registry drop": lambda v: v.registry.pop(sorted(v.registry)[0]),
        "object cost": lambda v: v.objs[placed_id(v, 3)].update(cost=999),
        "pose lane": lambda v: v.objs[placed_id(v, 3)]["pose"].__setitem__(4, 7),
        "budget P": lambda v: setattr(v, "P", v.P + 1),
        "handle state": lambda v: v.handles.update(
            {placed_id(v, 3): "tombstone"}),
        "claims": lambda v: v.claims.update(
            {"evX": {"d": ("accepted", ("placed", "x"))}}),
        "claim status": lambda v: v.claims[H("event", "local", 1)].update(
            {"d2": ("conflict", ("conflict",))}),
        "reject log": lambda v: v.rejects.append((99, "local", "x")),
        "gate next_open": lambda v: v.objs[placed_id(v, 4)].update(next_open=1),
        "clk phase": lambda v: v.objs[placed_id(v, 1)].update(phase=7),
        "controller": lambda v: v.objs[placed_id(v, 3)].update(controller="z"),
    }
    blind = []
    for name, fn in muts.items():
        v = copy.deepcopy(w)
        fn(v)
        if v.canonical_hash() == base:
            blind.append(name)
    covered = set(w.state_dict()) - {"rulepack_hash", "numeric"}
    auto_ok = covered == set(vars(w)) - World.TRANSIENT
    ok = not blind and auto_ok
    RESULTS.append(("oracle sensitivity", ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {'oracle sensitivity':40s} "
          f"{len(muts)} mutations, blind={blind or 'none'}; auto-coverage="
          f"{auto_ok}")


def phase_fault_negatives():
    def fresh():
        return latency_world()
    faults = ["commit-dup", "commit-omit", "commit-stale",
              "react-dup", "react-omit", "react-stale"]
    outcomes = {}
    for f in faults:
        w = fresh()
        try:
            w.step([], RandomChooser(random.Random(7)), fault=f)
            outcomes[f] = "UNDETECTED"
        except PhaseFault:
            outcomes[f] = "detected"
    # sig faults need a hot wire: advance to the firing epochs (t=2,3,4)
    for f in ("sig-dup", "sig-omit"):
        w = fresh()
        try:
            for _ in range(3):
                w.step([], RandomChooser(random.Random(7)), fault=f)
            outcomes[f] = "UNDETECTED"
        except PhaseFault:
            outcomes[f] = "detected"
    w = fresh()
    try:
        w.step([], RandomChooser(random.Random(7)),
               drop_registry=sorted(w.registry)[0])
        outcomes["unregistered"] = "UNDETECTED"
    except PhaseFault:
        outcomes["unregistered"] = "detected"
    ok = all(v == "detected" for v in outcomes.values())
    RESULTS.append(("phase-fault negatives (both phases)", ok))
    print(f"[{'PASS' if ok else 'FAIL'}] "
          f"{'phase-fault negatives (both phases)':40s} "
          f"{sum(v == 'detected' for v in outcomes.values())}/"
          f"{len(outcomes)} detected: {outcomes} (Q3)")


def exhaust_window(name, base_builder, epoch_events, cap=60_000):
    base = base_builder()
    unique, leaves, complete, path = set(), 0, False, []
    while True:
        w = copy.deepcopy(base)
        ch = PathChooser(path)
        film = tuple(w.step(evs, ch) for evs in epoch_events)
        unique.add(film)
        leaves += 1
        if leaves >= cap:
            break
        if not ch.advance():
            complete = True
            break
        path = ch.path
    ok = len(unique) == 1
    RESULTS.append((f"exhaustive: {name}", ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {'exhaustive: ' + name:40s} "
          f"schedules={'ALL ' if complete else '>='}{leaves} "
          f"unique_per-epoch_films={len(unique)}")


def exhaustive_suite():
    print("\n== Exhaustive DFS (per-epoch films; ALL = complete) ==")
    def lat():
        w = latency_world()
        for _ in range(2):
            w.step([], ZeroChooser())
        return w
    exhaust_window("delivery+commit epochs", lat, [[], []])

    def gate2():
        w = make_gate_world(2)
        for _ in range(2):
            w.step([], ZeroChooser())
        return w
    exhaust_window("two signals -> gate (merge)", gate2, [[], []])

    def spin():
        w = World()
        w.step([E(1, "STAMP", kind="pulser"), E(2, "STAMP", kind="spinner"),
                E(3, "STAMP", kind="orb")], ZeroChooser())
        p, s, o = placed_id(w, 1), placed_id(w, 2), placed_id(w, 3)
        w.step([CFG(4, p, "period", 1000), CFG(5, p, "phase", 3),
                E(6, "LINK", target=p, dst=s, **SIG),
                E(7, "LINK", target=s, dst=o, **SOCK)], ZeroChooser())
        for _ in range(2):
            w.step([], ZeroChooser())
        return w
    exhaust_window("signal -> spinner rotation", spin, [[], []])


def build_e2a():
    w = World()
    w.step([E(1, "STAMP", kind="pulser"), E(2, "STAMP", kind="pulser"),
            E(3, "STAMP", kind="door"), E(4, "STAMP", kind="spinner"),
            E(5, "STAMP", kind="orb"), E(6, "STAMP", kind="relay"),
            E(7, "STAMP", kind="relay"), E(8, "STAMP", kind="pulser")],
           ZeroChooser())
    p3, p5, seed = placed_id(w, 1), placed_id(w, 2), placed_id(w, 8)
    d, s, o = placed_id(w, 3), placed_id(w, 4), placed_id(w, 5)
    r1, r2 = placed_id(w, 6), placed_id(w, 7)
    w.step([CFG(10, p3, "period", 3), CFG(11, p5, "period", 5),
            CFG(12, seed, "mode", "once"), CFG(13, seed, "epoch", 3),
            E(14, "LINK", target=p3, dst=d, **SIG),
            E(15, "LINK", target=p5, dst=s, **SIG),
            E(16, "LINK", target=s, dst=o, **SOCK),
            E(17, "LINK", target=r1, dst=r2, **SIG),
            E(18, "LINK", target=r2, dst=r1, **SIG),
            E(19, "LINK", target=seed, dst=r1, **SIG)], ZeroChooser())
    w._orb, w._r1, w._d = o, r1, d
    return w


def e2a(seeds=40, epochs=2000, long_epochs=100_000):
    print("\n== E2a (fixture fully in-model: seed pulser primes the ring; "
          "zero out-of-step mutation) ==")
    seqs = set()
    for s in range(seeds):
        w = build_e2a()
        ch = RandomChooser(random.Random(5000 + s))
        seqs.add(tuple(w.step([], ch) for _ in range(epochs)))
    ok = len(seqs) == 1
    RESULTS.append(("E2a cross-seed", ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {seeds} seeds x {epochs} epochs -> "
          f"unique hash sequences = {len(seqs)}")
    w = build_e2a()
    ch = RandomChooser(random.Random(31337))
    q0 = qnorm2(tuple(w.objs[w._orb]["pose"][0:4]))
    maxi, violations = 0, 0
    pose_changes = []
    prev_q = tuple(w.objs[w._orb]["pose"][0:4])
    for _ in range(long_epochs):
        w.step([], ch)
        tc = w.t - 1
        maxi = max(maxi, w.last_steps)
        if w.objs[w._r1]["cur_out"] != (1 if tc >= 5 and (tc - 5) % 4 == 0
                                        else 0):
            violations += 1
        if w.objs[w._d]["open"] != (1 if tc >= 5 and (tc - 5) % 3 == 0 else 0):
            violations += 1
        if maxi > 30:
            violations += 1
        if tc < 62:
            q = tuple(w.objs[w._orb]["pose"][0:4])
            if q != prev_q:
                pose_changes.append(tc)
            prev_q = q
    exp_changes = [t for t in range(2, 62) if t >= 6 and (t - 6) % 5 == 0]
    ok = violations == 0 and pose_changes == exp_changes
    drift = (qnorm2(tuple(w.objs[w._orb]["pose"][0:4])) - q0) / ONE
    RESULTS.append(("E2a long run asserted", ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {long_epochs} epochs: relay "
          f"period-4 (from t=5, seed-primed) and door period-3 closed forms "
          f"asserted every epoch (violations={violations}); spinner rotation "
          f"epochs verified ({pose_changes == exp_changes}); max charged "
          f"steps/epoch={maxi} (bound 30)")
    print(f"observational: quaternion-PROXY drift |q|^2-1 = {drift:+.6e}")


def case_native_once():
    print("\n== native Once acceptance (proc-e2.3 errata) ==")
    def mini(cfgs):
        w = World()
        w.step([E(1, "STAMP", kind="pulser")], ZeroChooser())
        p = placed_id(w, 1)
        w.step(cfgs(p) + [E(60, "LINK", target=p, dst=p, **SIG)]
               if False else cfgs(p), ZeroChooser())
        return w, p
    ok = True
    # (a) Once(40): fires exactly once, wire hot exactly at t=41
    w = World()
    w.step([E(1, "STAMP", kind="pulser"), E(2, "STAMP", kind="door")],
           ZeroChooser())
    p, d = placed_id(w, 1), placed_id(w, 2)
    w.step([CFG(10, p, "mode", "once"), CFG(11, p, "epoch", 40),
            E(12, "LINK", target=p, dst=d, **SIG)], ZeroChooser())
    wid = next(iter(w.wires))
    hots = []
    for _ in range(2, 92):
        w.step([], ZeroChooser())
        if w.wires[wid]["cur"]:
            hots.append(w.t - 1)
    okA = hots == [41]
    ok &= okA
    print(f"[{'PASS' if okA else 'FAIL'}] Once(40) fires exactly once "
          f"(wire hot epochs {hots})")
    # (b) silence at extreme t: the round-8 falsifier, inverted
    st = w.objs[p]
    w.t = 10 ** 9
    w.step([], ZeroChooser())
    w.step([], ZeroChooser())
    okB = w.wires[wid]["cur"] == 0 and st["done"] == 1
    ok &= okB
    print(f"[{'PASS' if okB else 'FAIL'}] no firing at t=10^9 "
          f"(sentinel gone; done={st['done']})")
    # (c) Once(1) primes during construction (the binding init recipe)
    w = World()
    w.step([E(1, "STAMP", kind="pulser"), E(2, "STAMP", kind="door")],
           ZeroChooser())
    p, d = placed_id(w, 1), placed_id(w, 2)
    w.step([CFG(10, p, "mode", "once"), CFG(11, p, "epoch", 1),
            E(12, "LINK", target=p, dst=d, **SIG)], ZeroChooser())
    wid = next(iter(w.wires))
    okC = w.wires[wid]["nxt"] == 1 and w.objs[p]["done"] == 1
    ok &= okC
    print(f"[{'PASS' if okC else 'FAIL'}] Once(1) primes its wire during "
          f"construction (nxt={w.wires[wid]['nxt']}, done latched)")
    # (d) late config never fires and latches done immediately
    w = World()
    w.step([E(1, "STAMP", kind="pulser"), E(2, "STAMP", kind="door")],
           ZeroChooser())
    p, d = placed_id(w, 1), placed_id(w, 2)
    w.step([CFG(10, p, "mode", "once"), CFG(11, p, "epoch", 0),
            E(12, "LINK", target=p, dst=d, **SIG)], ZeroChooser())
    wid = next(iter(w.wires))
    fired = w.wires[wid]["nxt"] == 1
    done0 = w.objs[p]["done"]
    for _ in range(60):
        w.step([], ZeroChooser())
        fired |= w.wires[wid]["cur"] == 1
    okD = (not fired) and done0 == 1
    ok &= okD
    print(f"[{'PASS' if okD else 'FAIL'}] Once(0) configured late never "
          f"fires; done latched at admit-epoch commit (done={done0})")
    RESULTS.append(("native Once acceptance", ok))


if __name__ == "__main__":
    print("== E2b v2.2 ==")
    case_budget_race()
    case_native_once()
    case_multiwriter_ids()
    case_multiwriter_order()
    case_equivocation_matrix()
    case_noncommutative_rotations()
    case_move_delete()
    case_link_delete()
    case_gate_truth_table()
    case_spinner_fanin()
    case_controller_exclusive()
    case_controller_release()
    case_two_tick_latency()
    case_wire_timeline()
    case_delete_refund_once()
    case_duplicate_then_delete()
    case_type_battery()
    case_config_battery()
    case_malformed()
    print()
    ceiling_negative()
    rulepack_content_test()
    oracle_sensitivity()
    phase_fault_negatives()
    exhaustive_suite()
    e2a()
    fails = [r for r in RESULTS if not r[1]]
    print(f"\n{'=' * 66}\nTOTAL: {len(RESULTS)} checks, "
          f"{len(RESULTS) - len(fails)} pass, {len(fails)} FAIL")
    for f in fails:
        print("  FAIL:", f[0])
    raise SystemExit(1 if fails else 0)
