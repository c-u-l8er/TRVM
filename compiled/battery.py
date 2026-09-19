#!/usr/bin/env python3
"""battery.py -- admission of the compiled backend: its fold must equal the interaction-calculus fold on every world.

    PYTHONDONTWRITEBYTECODE=1 python3 -B battery.py [--quick] [--controls] [--out results-battery.json]

For every (world, scenario) pair: the production fold `spinner_bench._run_traj` under ic_ref (and ic32 on the demo
world) gives the reference films; `fold.ic_fold` gives the decoded state per epoch; `fold.compiled_fold` gives both
from the C step. The verdict per pair is film-equal AND state-equal on every epoch. Scenarios: the world's own demo
scenario, and for every spinner world seeded random scenarios (random rotors biased to the lane extremes, random
resets, random initial faults) over more epochs than any counter's period.

`--controls`: textual mutants -- twelve of the emitter and two of the fold's plumbing -- each applied to a copy loaded as
a separate module; EVERY pair is folded under every mutant and compared with the cached references, so the record says
which worlds catch a mutant, not only that one did. A mutant nothing catches fails the battery -- it means a case is
missing, not that the mutant is harmless; and the three mutants added with the 2026-09-18 widening must be caught ONLY by
the worlds that widening added (a widening whose mutant an older world already catches has not widened anything).
`--quick` skips ic_ref on the 9.2 MB demo epochs (ic32 still runs there) and folds one fuzz seed.

Widened 2026-09-18 (afternoon): two mailbox worlds with `~~` routes (one delivering, one overflowing its capacity), and a
spinner at w=33 -- the first lane width over ic32's 16 MiB stdin buffer, reduced through ic32's file mode (`fold.ic32_reparse`)
and, on its demo scenario, ic_ref (34 s per epoch on this laptop)."""
import argparse
import importlib.util
import json
import os
import random
import statistics as st
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import fold as F                       # noqa: E402
SB, O, P = F.SB, F.O, F.P
SC = SB.SC

PROFILE = "profile forge.world.core.v1\n\n"


_MAILBOX_BASE = ("[pulser:p0](every 2){sig_out}\n[relay:r0]{sig_in, sig_out}\n[spinner:sp](w=8, n=4, rotor=quarter_turn_z, configurable){sig_in, socket}\n"
                 "[orb:ob]{pose}\n[pulser:p1](once at 2){sig_out}\n[pulser:p2](once at 3){sig_out}\n[door:d0]{sig_in}\n")
_MAILBOX_EDGES = "\n[pulser:p0] --sig--> [relay:r0]\n[relay:r0] --sig--> [spinner:sp]\n[spinner:sp] --socket--> [orb:ob]\n[pulser:p1] --sig--> [door:d0]\n"


def chain(n):
    return (PROFILE + "[pulser:p0](every 2){sig_out}\n"
            + "".join(f"[relay:r{i}]{{sig_in, sig_out}}\n" for i in range(n))
            + "[door:d0]{sig_in}\n\n[pulser:p0] --sig--> [relay:r0]\n"
            + "".join(f"[relay:r{i}] --sig--> [relay:r{i+1}]\n" for i in range(n - 1))
            + f"[relay:r{n-1}] --sig--> [door:d0]\n")


WORLDS = {
    "golden-demo": SB.DEMO_WORLD_SOURCE,
    "chain10": chain(10), "chain30": chain(30), "chain120": chain(120),
    "pulser-relay": PROFILE + "[pulser:p0](every 2){sig_out}\n[relay:r0]{sig_in, sig_out}\n\n[pulser:p0] --sig--> [relay:r0]\n",
    "pulser-door": PROFILE + "[pulser:p1](once at 1){sig_out}\n[door:d0]{sig_in}\n\n[pulser:p1] --sig--> [door:d0]\n",
    "relay-only": PROFILE + "[relay:r0]{sig_in, sig_out}\n",
    "spinner-w4-n2": PROFILE + "[pulser:p0](every 2){sig_out}\n[spinner:sp](w=4, n=2, rotor=quarter_turn_z, configurable){sig_in, socket}\n[orb:ob]{pose}\n\n[pulser:p0] --sig--> [spinner:sp]\n[spinner:sp] --socket--> [orb:ob]\n",
    "spinner-w8-n4": PROFILE + "[pulser:p0](every 2){sig_out}\n[spinner:sp](w=8, n=4, rotor=quarter_turn_z, configurable){sig_in, socket}\n[orb:ob]{pose}\n\n[pulser:p0] --sig--> [spinner:sp]\n[spinner:sp] --socket--> [orb:ob]\n",
    "spinner-w16-n8-fixed": PROFILE + "[pulser:p0](every 2){sig_out}\n[spinner:sp](w=16, n=8, rotor=quarter_turn_z){sig_in, socket}\n[orb:ob]{pose}\n\n[pulser:p0] --sig--> [spinner:sp]\n[spinner:sp] --socket--> [orb:ob]\n",
    "binary-40-phase-3": PROFILE + "[pulser:p0](every 40, phase 3){sig_out}\n[relay:r0]{sig_in, sig_out}\n[door:d0]{sig_in}\n\n[pulser:p0] --sig--> [relay:r0]\n[relay:r0] --sig--> [door:d0]\n",
    "once-at-5": PROFILE + "[pulser:p1](once at 5){sig_out}\n[relay:r0]{sig_in, sig_out}\n[door:d0]{sig_in}\n\n[pulser:p1] --sig--> [relay:r0]\n[relay:r0] --sig--> [door:d0]\n",
    "fanout": PROFILE + "[pulser:p0](every 2){sig_out}\n[pulser:p1](every 3, phase 1){sig_out}\n[relay:r0]{sig_in, sig_out}\n[spinner:sp](w=8, n=4, rotor=quarter_turn_z, configurable){sig_in, socket}\n[orb:ob]{pose}\n[door:d0]{sig_in}\n[door:d1]{sig_in}\n\n[pulser:p0] --sig--> [relay:r0]\n[relay:r0] --sig--> [spinner:sp]\n[relay:r0] --sig--> [door:d0]\n[pulser:p1] --sig--> [door:d1]\n[spinner:sp] --socket--> [orb:ob]\n",
    "two-spinners": PROFILE + "[pulser:p0](every 2){sig_out}\n[pulser:p1](every 3){sig_out}\n[spinner:s1](w=8, n=4, rotor=quarter_turn_z, configurable){sig_in, socket}\n[spinner:s2](w=12, n=6, rotor=quarter_turn_z, configurable){sig_in, socket}\n[orb:o1]{pose}\n[orb:o2]{pose}\n\n[pulser:p0] --sig--> [spinner:s1]\n[pulser:p1] --sig--> [spinner:s2]\n[spinner:s1] --socket--> [orb:o1]\n[spinner:s2] --socket--> [orb:o2]\n",
    # ---- widened 2026-09-18 (afternoon). A mailbox is claim state, not world state (D8: it contributes nothing physical),
    # so the compiled STEP never sees it; what these worlds admit is the compiled FOLD's plumbing -- the route claims
    # `_script_for` folds in and the mailbox block `film_hash_v7` renders -- against the production loop's. A route's
    # source must be a `once` pulser; its Send is minted under the reserved writer 15.
    "mailbox-routes": PROFILE + _MAILBOX_BASE + "[mailbox:mb](w=8, cap=2){}\n" + _MAILBOX_EDGES + "[p1] ~~msg~~> [mb] (body=1.2.3.4)\n[p2] ~~late~~> [mb] (body=0.0.0.255)\n",
    "mailbox-overflow": PROFILE + _MAILBOX_BASE + "[mailbox:mb](w=8, cap=1){}\n" + _MAILBOX_EDGES + "[p1] ~~a~~> [mb] (body=1.2.3.4)\n[p1] ~~b~~> [mb] (body=5.6.7.8)\n",
    # The first lane width over 32: its epoch term is 39 MB, over ic32's 16 MiB stdin buffer, so the calculus runs through
    # ic32's file mode (`-reparse`, the same text) and ic_ref on the demo scenario. Lanes to 2^33 make the i128 product
    # law observable: an i64 product wraps here and nowhere else in the battery.
    "spinner-w33-n16": PROFILE + "[pulser:p0](every 2){sig_out}\n[spinner:sp](w=33, n=16, rotor=quarter_turn_z, configurable){sig_in, socket}\n[orb:ob]{pose}\n\n[pulser:p0] --sig--> [spinner:sp]\n[spinner:sp] --socket--> [orb:ob]\n",
    # ---- widened 2026-09-18 (night): a second world on the i128 path, and the first with BOTH MAC paths in one step (a
    # w=8 spinner beside a w=33 one). What it admits is the C v2 step's per-spinner path selection: a selector that
    # takes the WORLD's narrowest width (`path-from-min-width`, battery_bend.py MUTANTS_C2) is right on every
    # single-width world and on two-spinners (w=8, w=12: both narrow) and wrong here alone. For the C v1 step, which has
    # one MAC path, this world catches nothing of its own: it is a second wide world, not a widening of v1's claims.
    "mixed-w8-w33": PROFILE + "[pulser:p0](every 2){sig_out}\n[pulser:p1](every 3){sig_out}\n[spinner:s1](w=8, n=4, rotor=quarter_turn_z, configurable){sig_in, socket}\n[spinner:s2](w=33, n=16, rotor=quarter_turn_z, configurable){sig_in, socket}\n[orb:o1]{pose}\n[orb:o2]{pose}\n\n[pulser:p0] --sig--> [spinner:s1]\n[pulser:p1] --sig--> [spinner:s2]\n[spinner:s1] --socket--> [orb:o1]\n[spinner:s2] --socket--> [orb:o2]\n",
}
# ---- the top of the admitted width range (2026-09-18, night). A w=63 spinner's STEP term is 150 MB and Forge lowers it
# in ~500 s, so this world is not in the standing battery: it is folded only under TRVM_BATTERY_HUGE=1, on the demo
# scenario and one three-epoch `extremes` scenario (lanes at the top of the range from epoch 1), never the 24-epoch fuzz.
# What it admits is the emitter's ORIGINAL bound: `sx` sign-extends by subtracting `(i128)1 << w`, and a subtrahend formed
# in i64 (`sx-subtrahend-i64`) is exact for every w <= 62 and wrong at 63 alone -- no narrower world can see it.
HUGE_WORLDS = {
    "spinner-w63-n31": PROFILE + "[pulser:p0](every 2){sig_out}\n[spinner:sp](w=63, n=31, rotor=quarter_turn_z, configurable){sig_in, socket}\n[orb:ob]{pose}\n\n[pulser:p0] --sig--> [spinner:sp]\n[spinner:sp] --socket--> [orb:ob]\n",
}
if os.environ.get("TRVM_BATTERY_HUGE"):
    WORLDS.update(HUGE_WORLDS)
NATIVE_WORLDS = ("golden-demo", "chain30", "spinner-w16-n8-fixed")   # the calculus twin runs on ic32 here
LARGE_WORLDS = ("golden-demo", "spinner-w16-n8-fixed")                # ~9 MB epoch terms: ic32 is the reference; ic_ref only on the demo scenario
WIDE_WORLDS = ("spinner-w33-n16", "mixed-w8-w33", "spinner-w63-n31")  # > 16 MiB epoch terms: ic32 -reparse is the reference and the twin; ic_ref only on the demo scenario
MAILBOX_WORLDS = ("mailbox-routes", "mailbox-overflow")
FUZZ_SEEDS = (20260918, 20260919, 20260920)
FUZZ_EPOCHS = 24


def random_scenario(view, sem, seed, epochs=FUZZ_EPOCHS):
    rng = random.Random(seed)
    spins, orbs = sorted(view.spinners), list(view.orbs)
    seq, eps = 0, []
    # writer_id and sequence are 4-bit in ScenarioV1; writer 15 is `WC.ROUTE_WRITER_ID`, reserved for a world's own
    # routes, and a scenario writing under it is refused against a route-bearing world -- so writers run 1..14 (a
    # scenario here never reaches seq 224, where the old `% 15` would first have minted writer 15; the fuzz digests of
    # the 2026-09-18 morning record are unchanged).

    def lane(w):
        r = rng.random()
        if r < 0.35:
            return rng.choice([0, (1 << (w - 1)) - 1, 1 << (w - 1), (1 << w) - 1, 1 << view.spinners[s][1], ((1 << w) - 1) ^ (1 << view.spinners[s][1])])
        return rng.randrange(1 << w)

    for ep in range(1, epochs + 1):
        claims = []
        for s in spins:
            if rng.random() < 0.45:
                seq += 1
                w = view.spinners[s][0]
                claims.append({"writer_id": 1 + (seq // 16) % 14, "sequence": seq % 16, "operation": "SetRotor", "target": s,
                               "payload": {"rotor": [lane(w) for _ in range(4)]}})
        for o in orbs:
            if rng.random() < 0.2:
                seq += 1
                claims.append({"writer_id": 1 + (seq // 16) % 14, "sequence": seq % 16, "operation": "ResetFault", "target": o, "payload": {}})
        eps.append({"epoch": ep, "label": "fuzz %d" % ep, "claims": claims})
    return {"scenario_version": SC.SCENARIO_VERSION, "world_semantic_id": sem,
            "initial_runtime": {"numeric_faults": [o for o in orbs if rng.random() < 0.5]}, "epochs": eps}


def gentle_scenario(view, sem, seed, epochs=FUZZ_EPOCHS):
    """A wide world's rotors near the unit, so the pose never saturates and the products carry remainders below 2^n.
    Added 2026-09-18 (night) when the C step's MAC was split by width: on `spinner-w33-n16` the random scenarios' rotors
    (up to 2^32) saturate the pose to +-2^32 in one reaction, after which every product is a multiple of 2^32 and a
    floor shift is indistinguishable from the toward-zero one -- `floor-shift-128` survived until this scenario existed."""
    rng = random.Random(seed)
    spins, orbs = sorted(view.spinners), list(view.orbs)
    seq, eps = 0, []
    for ep in range(1, epochs + 1):
        claims = []
        for s in spins:
            if rng.random() < 0.45:
                seq += 1
                w, n = view.spinners[s][0], view.spinners[s][1]
                unit, full = 1 << n, 1 << w
                claims.append({"writer_id": 1 + (seq // 16) % 14, "sequence": seq % 16, "operation": "SetRotor", "target": s,
                               "payload": {"rotor": [(rng.randrange(-unit // 2, unit // 2 + 1) + (unit if l == 0 else 0)) % full for l in range(4)]}})
        for o in orbs:
            if rng.random() < 0.2:
                seq += 1
                claims.append({"writer_id": 1 + (seq // 16) % 14, "sequence": seq % 16, "operation": "ResetFault", "target": o, "payload": {}})
        eps.append({"epoch": ep, "label": "gentle %d" % ep, "claims": claims})
    return {"scenario_version": SC.SCENARIO_VERSION, "world_semantic_id": sem,
            "initial_runtime": {"numeric_faults": []}, "epochs": eps}


def extremes_scenario(view, sem, epochs=3):
    """Every spinner's rotor at the top of its lane range from epoch 1 (the sign bit, the all-ones lane, the unit, the
    largest positive), then the complement pattern, then a fault reset: three epochs that put a lane >= 2^(w-1) through
    `sx` at once. The HUGE worlds' only scenario besides the demo (their fuzz would cost hours of calculus per world)."""
    spins, orbs = sorted(view.spinners), list(view.orbs)
    eps, seq = [], 0
    for ep in range(1, epochs + 1):
        claims = []
        for s in spins:
            w, n = view.spinners[s][0], view.spinners[s][1]
            top, full, unit = 1 << (w - 1), (1 << w) - 1, 1 << n
            rotor = [top, full, unit, top - 1] if ep % 2 == 1 else [full ^ unit, top, 1, top]
            seq += 1
            claims.append({"writer_id": 1 + (seq // 16) % 14, "sequence": seq % 16, "operation": "SetRotor", "target": s, "payload": {"rotor": rotor}})
        if ep == epochs:
            for o in orbs:
                seq += 1
                claims.append({"writer_id": 1 + (seq // 16) % 14, "sequence": seq % 16, "operation": "ResetFault", "target": o, "payload": {}})
        eps.append({"epoch": ep, "label": "extremes %d" % ep, "claims": claims})
    return {"scenario_version": SC.SCENARIO_VERSION, "world_semantic_id": sem, "initial_runtime": {"numeric_faults": []}, "epochs": eps}


def pairs(quick):
    """[(world_name, src, scenario_label, scenario_or_None)]"""
    out = []
    for name, src in WORLDS.items():
        out.append((name, src, "demo", None))
        prog, _ = SB._resolve_scenario(src, None)
        view = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
        if name in HUGE_WORLDS:
            out.append((name, src, "extremes", extremes_scenario(view, prog.semantic_artifact_id)))
            continue
        if view.spinners or any(view.counter_spec(r)[0] != "onehot" for r in view.pulsers):
            for seed in FUZZ_SEEDS[: (1 if quick else 3)]:
                out.append((name, src, "fuzz-%d" % seed, random_scenario(view, prog.semantic_artifact_id, seed)))
        if name in WIDE_WORLDS:
            out.append((name, src, "gentle-%d" % FUZZ_SEEDS[0], gentle_scenario(view, prog.semantic_artifact_id, FUZZ_SEEDS[0])))
    return out


def compare(name, label, rows_c, films_ref, rows_ic=None):
    """Per pair: film equality against the production reference, and state equality against the calculus twin."""
    verdict = {"world": name, "scenario": label, "epochs": len(rows_c), "films_equal": True, "states_equal": True, "first_divergence": None}
    for r, f in zip(rows_c, films_ref):
        if r["film"] != f:
            verdict["films_equal"] = False
            verdict["first_divergence"] = verdict["first_divergence"] or {"epoch": r["t"], "kind": "film"}
            break
    if len(rows_c) != len(films_ref):
        verdict["films_equal"] = False
    if rows_ic is not None:
        for rc, ri in zip(rows_c, rows_ic):
            if rc["state"] != ri["state"]:
                diff = sorted(k for k in set(rc["state"]) | set(ri["state"]) if rc["state"].get(k) != ri["state"].get(k))
                verdict["states_equal"] = False
                verdict["first_divergence"] = verdict["first_divergence"] or {"epoch": rc["t"], "kind": "state", "fields": diff[:8]}
                break
    return verdict



# ------------------------------------------------------------- a receipt must not be replaced by a narrower one
def receipt_coverage(receipt):
    """The (world, scenario) pairs a receipt says it folded. This is what "how much was admitted" means; the
    `quick` / `worlds_subset` / `huge` flags only describe how that set was arrived at."""
    return {(p.get("world"), p.get("scenario")) for p in receipt.get("pairs", []) if p.get("world")}


def refuse_narrowing(out_path, planned, force=False):
    """Refuse, BEFORE folding anything, to overwrite a receipt that covers strictly more than this run will.

    A results file is the admission record -- it is what `README.md` and `FOUNDATION_LANE.md` quote when they say
    how many pairs agreed. `--quick` and `--worlds` default to the SAME `--out` as a full run, so a development
    smoke silently replaced the record of the run that was actually admitted, and the only evidence was a smaller
    number nobody had reason to re-read. (Measured 2026-09-19: a `--quick` run wrote 33 pairs over a 59-pair
    record and was caught by hand, not by anything here.)

    The comparison is the pair SET, not a flag or a count, so it catches every way of narrowing at once: quick
    over full, a `--worlds` subset over the standing battery, and a non-HUGE run over a gated one. A run that
    covers as much, or more, or something disjoint, writes as before. `--force` writes anyway and the receipt
    then says what it replaced, because a deliberate narrowing is a decision and should read like one.

    Returns the note to put on the receipt (`None` when nothing was replaced). Raises SystemExit on a refusal.
    """
    if not os.path.exists(out_path):
        return None
    try:
        with open(out_path) as f:
            existing = json.load(f)
    except (ValueError, OSError):
        return None                      # not a receipt this function can reason about; leave it to the writer
    had = receipt_coverage(existing)
    missing = had - set(planned)
    if not missing:
        return None
    detail = "%s covers %d pairs; this run covers %d and would drop %d (e.g. %s)" % (
        os.path.basename(out_path), len(had), len(planned), len(missing),
        ", ".join("%s/%s" % p for p in sorted(missing)[:3]))
    if not force:
        raise SystemExit(
            "REFUSED: this run would NARROW the record it writes.\n  %s\n"
            "  Write it somewhere of its own (--out results-battery-<what-this-is>.json), or --force to replace\n"
            "  the broader record deliberately." % detail)
    return {"replaced_broader": detail, "replaced_pairs": len(had)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--controls", action="store_true")
    ap.add_argument("--out", default=os.path.join(HERE, "results-battery.json"))
    ap.add_argument("--worlds", default=None, help="comma-separated subset of WORLDS (a development smoke, not the admission)")
    ap.add_argument("--force", action="store_true", help="replace a BROADER record deliberately; the receipt then says what it replaced")
    a = ap.parse_args()
    if a.worlds:
        keep = set(a.worlds.split(","))
        unknown = keep - set(WORLDS)
        if unknown:
            raise SystemExit("unknown worlds: %s" % sorted(unknown))
        for k in list(WORLDS):
            if k not in keep:
                del WORLDS[k]
    plan = [(name, label) for name, _src, label, _scen in pairs(a.quick)]
    replaced = refuse_narrowing(a.out, plan, a.force)
    t_start = time.time()
    # `huge` was NOT on the receipt until 2026-09-19: a 61-pair/19-world gated run and a 59-pair/18-world
    # standing run were distinguishable only by counting, in the file that IS the admission record.
    receipt = {"measured": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "quick": a.quick, "worlds_subset": a.worlds,
               "huge": bool(os.environ.get("TRVM_BATTERY_HUGE")), "replaced": replaced,
               "loadavg": os.getloadavg(), "ic32_path": O.IC32,
               "pairs": [], "worlds": {}, "controls": None}
    refs = {}       # (name, label) -> reference films (production _run_traj, ic_ref)
    all_ok = True
    for name, src, label, scen in pairs(a.quick):
        t0 = time.perf_counter()
        sem, dig, rows_c, cs = F.compiled_fold(src, scen)
        t_c = time.perf_counter() - t0
        t0 = time.perf_counter()
        wide = name in WIDE_WORLDS
        huge = name in HUGE_WORLDS
        native_name = "ic32-reparse" if wide else "ic32"
        # A HUGE world's calculus runs on ic_ref only: its step term is 150-170 MB depending on the process's binder
        # history (README §2b), and at 170 MB ic32's fixed 16M-slot heap (`static uint32_t HEAPCAP = 1u<<24`,
        # runtime/c/ic32.c -- the checked-host lane's file, not changed) overflows where 150 MB had fit. ic_ref has no
        # such cap; it costs ~700 s per epoch here, which is why the world is gated and carries no fuzz scenario.
        use_native_only = (name in LARGE_WORLDS or wide) and (a.quick or label != "demo") and not huge
        films_ref, _cached = F.cached_reference_films(src, native_name if use_native_only else "ic_ref", scen)
        t_ref = time.perf_counter() - t0
        refs[(name, label)] = films_ref
        # the calculus twin for states (+ term sizes): ic32 on the native worlds, ic32's file mode on the wide ones, ic_ref elsewhere
        t0 = time.perf_counter()
        if huge:
            _, _, rows_ic = F.ic_fold(src, O.ref_reduce, scen)
        elif wide:
            _, _, rows_ic = F.ic_fold(src, None, scen, split=F.ic32_reparse)
        else:
            _, _, rows_ic = F.ic_fold(src, O.native_reduce if name in NATIVE_WORLDS else O.ref_reduce, scen)
        t_ic = time.perf_counter() - t0
        v = compare(name, label, rows_c, films_ref, rows_ic)
        if (name in NATIVE_WORLDS or wide) and not use_native_only and not huge:
            _, _, films_nat = F.reference_films(src, native_name, scen)
            v["films_equal_ic32"] = films_nat == films_ref and len(films_nat) == len(rows_c)
            if not v["films_equal_ic32"]:
                all_ok = False
        v.update({"sem": sem, "scenario_digest": dig, "backend_id": cs.backend_id, "term_bytes_epoch1": rows_ic[0]["term_bytes"] if rows_ic else None,
                  "compiled_step_us_p50": round(st.median(r["step_s"] for r in rows_c) * 1e6, 2),
                  "ic_step_s_p50": round(st.median(r["step_s"] for r in rows_ic), 4),
                  "ic_reduce_s_p50": round(st.median(r["reduce_s"] for r in rows_ic), 4),
                  "ic_reducer": "ic_ref" if huge else ("ic32-reparse" if wide else ("ic32" if name in NATIVE_WORLDS else "ic_ref")),
                  "reference": native_name if use_native_only else "ic_ref",
                  "wall_s": {"compiled_fold": round(t_c, 3), "reference_fold": round(t_ref, 3), "ic_twin_fold": round(t_ic, 3)}})
        ok = v["films_equal"] and v["states_equal"] and v.get("films_equal_ic32", True)
        all_ok &= ok
        receipt["pairs"].append(v)
        print("%-22s %-14s epochs %3d  term %9s B  ic %-6s %8.4f s/epoch (reduce %8.4f)  compiled %7.2f us/epoch  %s" % (
            name, label, v["epochs"], v["term_bytes_epoch1"], v["ic_reducer"], v["ic_step_s_p50"], v["ic_reduce_s_p50"], v["compiled_step_us_p50"],
            "AGREE" if ok else "DIVERGE %s" % v["first_divergence"]), flush=True)
        receipt["worlds"].setdefault(name, {"sem": sem, "backend_id": cs.backend_id, "source_sha256": cs.source_sha256, "state_width": cs.width})
    receipt["all_agree"] = all_ok
    print("BATTERY:", "ALL AGREE" if all_ok else "DIVERGENCE", "(%d pairs, %.0f s)" % (len(receipt["pairs"]), time.time() - t_start))

    if a.controls:
        receipt["controls"] = run_controls(refs, a.quick)
        caught = all(c["caught"] and c["as_expected"] for c in receipt["controls"])
        print("CONTROLS:", "ALL CAUGHT, EACH BY THE WORLDS EXPECTED" if caught else "A MUTANT SURVIVED OR WAS CAUGHT BY THE WRONG WORLD")
        all_ok &= caught
    receipt["loadavg_after"] = os.getloadavg()
    with open(a.out, "w") as f:
        json.dump(receipt, f, indent=1)
    print("wrote", a.out)
    return 0 if all_ok else 1


# ----------------------------------------------------------------------------------------------- mutants
# Since 2026-09-19 (T7) the LAW mutants are DERIVED from `laws.py`: a mutant is (law id, name), one clause of one law
# flipped, and it is the same flip in every backend that renders the clause (`laws.mutant`). What remains as a textual
# edit is a REPRESENTATION mutant -- a choice one emitter makes that is not a law (the i128 product law's rendering, the
# emitter's width bound, the fold's plumbing) -- and it is scoped to one function of one file so that the same text in
# another backend's renderer is not touched. Names, files and the worlds that alone may catch a widening's mutant are
# below; the law mutants' names come from the law table.
import laws as LAW

LAW_MUTANTS = [(name, law) for law, name in LAW.MUTANTS]           # (mutant name, law id) -- eleven today
# (name, file, function the edit is scoped to, old, new, only_by)
REPRESENTATION_MUTANTS = [
    ("narrow-product-i64", "laws.py", "_c_mac",
     "acc += (i128)HAM_SG[c][k] * (sx(rotor[HAM_I[c][k]], w) * sx(pose[HAM_J[c][k]], w)); /* i128 products */",
     "acc += (i128)HAM_SG[c][k] * (i64)((uint64_t)sx(rotor[HAM_I[c][k]], w) * (uint64_t)sx(pose[HAM_J[c][k]], w)); /* i64 products */",
     WIDE_WORLDS),
    ("film-without-mailboxes", "fold.py", None, "state=claim, mailboxes=seams.film_mailboxes)", "state=claim, mailboxes=None)", MAILBOX_WORLDS),
    ("script-without-routes", "fold.py", None, "initial_faults, script = SB._script_for(prog, scen)", "initial_faults, script = SB.SC.scenario_to_script(scen)", MAILBOX_WORLDS),
    # the emitter's original bound (README §2b): a sign-extension subtrahend formed in i64 is exact for w <= 62; at w = 63
    # `(i64)1 << 63` is INT64_MIN and the lane comes back 2^63 too large. Only the HUGE world can see it, so this control
    # runs (and is required) only when that world is folded.
    ("sx-subtrahend-i64", "laws.py", "_c_mac", "x - ((i128)1 << w) : x; }", "x - (i128)((i64)1 << w) : x; }", tuple(HUGE_WORLDS)),
]
if not os.environ.get("TRVM_BATTERY_HUGE"):
    REPRESENTATION_MUTANTS = [m for m in REPRESENTATION_MUTANTS if m[0] != "sx-subtrahend-i64"]


def scoped_replace(src, fn, old, new):
    """`old` -> `new` exactly once inside `def fn(` ... the next top-level `def`/`RENDER` (or anywhere when fn is None)."""
    if fn is None:
        lo, hi = 0, len(src)
    else:
        lo = src.index("def %s(" % fn)
        nxt = [i for i in (src.find("\ndef ", lo + 1), src.find("\nRENDER", lo + 1)) if i > 0]
        hi = min(nxt) if nxt else len(src)
    body = src[lo:hi]
    if body.count(old) != 1:
        raise RuntimeError("pattern found %d times in %s (%s), refusing" % (body.count(old), fn or "file", old[:40]))
    return src[:lo] + body.replace(old, new) + src[hi:]


def load_mutant(name, fname, fn, old, new):
    """A copy of `fname` with the scoped edit, loaded as its own module."""
    src = scoped_replace(open(os.path.join(HERE, fname)).read(), fn, old, new)
    path = os.path.join(os.path.expanduser("~/.cache/trvm-compiled"), "mutant_%s.py" % name.replace("-", "_"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(src)
    spec = importlib.util.spec_from_file_location("mutant_" + name.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class installed:
    """Install one mutant for the duration: a law mutant through laws.mutant; a laws.py edit by swapping the emitter's
    LAW module; a fold.py edit by folding through the mutated module (the caller uses `.fold`)."""

    def __init__(self, kind, spec):
        self.kind, self.spec, self.fold = kind, spec, F.compiled_fold

    def __enter__(self):
        import emit_c
        if self.kind == "law":
            self.cm = LAW.mutant(self.spec[1], self.spec[0])
            self.cm.__enter__()
        else:
            name, fname, fn, old, new, _ = self.spec
            mod = load_mutant(name, fname, fn, old, new)
            if fname == "laws.py":
                self.saved, emit_c.LAW = emit_c.LAW, mod
            else:
                self.fold = mod.compiled_fold
        return self

    def __exit__(self, *a):
        import emit_c
        if self.kind == "law":
            self.cm.__exit__(*a)
        elif self.spec[1] == "laws.py":
            emit_c.LAW = self.saved


def all_mutants():
    """[(name, kind, spec, only_by)] -- the law mutants (from the table) then the representation mutants."""
    out = [(name, "law", (name, law), None) for name, law in LAW_MUTANTS]
    out += [(m[0], "text", m, m[5]) for m in REPRESENTATION_MUTANTS]
    return out


def run_controls(refs, quick):
    """Every mutant over EVERY pair: the record carries the full set of catching worlds, the first catch, and whether a
    pair was caught by a film divergence or by a typed refusal raised inside the fold (a refusal is a catch: the mutant
    could not produce a film at all). The widening's mutants must be caught by their own worlds and by no other."""
    results = []
    plist = pairs(quick)
    for name, kind, mspec, only in all_mutants():
        first, catches, folded = None, [], 0
        with installed(kind, mspec) as inst:
            fold_fn = inst.fold
            for wname, src, label, scen in plist:
                folded += 1
                try:
                    _, _, rows_c, _ = fold_fn(src, scen)
                except Exception as e:                      # a typed refusal inside the fold: the mutant made no film
                    hit = {"world": wname, "scenario": label, "epoch": None, "kind": "refused", "error": "%s: %s" % (type(e).__name__, str(e)[:120])}
                    catches.append(hit)
                    first = first or hit
                    continue
                for r, f in zip(rows_c, refs[(wname, label)]):
                    if r["film"] != f:
                        hit = {"world": wname, "scenario": label, "epoch": r["t"], "kind": "film"}
                        catches.append(hit)
                        first = first or hit
                        break
        worlds = sorted({c["world"] for c in catches})
        ok = bool(catches) and (only is None or (set(worlds) <= set(only)))
        fname = "laws.py:%s" % mspec[1] if kind == "law" else mspec[1]
        results.append({"mutant": name, "file": fname, "kind": kind, "caught": bool(catches), "caught_at": first, "caught_by_worlds": worlds,
                        "caught_pairs": len(catches), "pairs_folded": folded, "only_by": list(only) if only else None, "as_expected": ok})
        print("control=%-26s %s %s  by %s%s" % (name, "CAUGHT" if catches else "NOT CAUGHT", json.dumps(first) if first else "(%d pairs folded)" % folded,
                                              worlds, "" if ok else ("  ** NOT AS EXPECTED (only %s may catch this)" % list(only) if only else "  ** NOT CAUGHT")), flush=True)
    return results


if __name__ == "__main__":
    raise SystemExit(main())
