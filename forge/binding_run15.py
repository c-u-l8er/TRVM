"""binding_run15.py -- ScenarioV1 + ScenarioDigest (Spinner Bench v0.3 slice 1).

GPT-5.6's scenario-authoring ruling: the RUN INPUTS become a first-class,
identity-bearing document (ScenarioV1) that is orthogonal to the world's
SemanticArtifactID. This battery proves the v0.3 acceptance items that the
scenario layer is responsible for:

  S1  validate_scenario_v1 is a typed structural gate: unknown version, missing/
      extra top keys, bad world_semantic_id, non-contiguous epochs, over-MAX_BATCH
      epoch, unknown operation, and malformed payloads all raise WRL_BAD_SCENARIO;
      a well-formed scenario (INCLUDING an out-of-world target, the Rejected path)
      passes.
  S2  canonicalization is claim-order- AND fault-order-independent: two scenarios
      differing only in intra-epoch claim order (or numeric_faults order)
      canonicalize identically and share a ScenarioDigest.
  S3  (acceptance 1 & 2) a scenario edit MOVES the ScenarioDigest but the world's
      SemanticArtifactID is untouched; a world edit MOVES the SemanticArtifactID
      but the ScenarioDigest for the same run inputs is untouched.
  S4  world_semantic_id is EXCLUDED from the digest domain: two scenarios with
      identical run inputs but different world_semantic_id share a ScenarioDigest
      (the digest is the identity of the INPUTS, not the world).
  S5  ReplayBundleID binds world + scenario + initial runtime: it moves when ANY
      of the three moves and is stable when none do.
  S6  scenario_to_script lowers demo_scenario to the (initial_faults, script) the
      admit driver folds, and its claim ENVELOPES are byte-identical to the
      historical hard-coded SCRIPT (labels are UI-only and may differ).
  S7  demo_scenario folded through the production plan/view path reproduces the
      hard-coded SCRIPT's films byte-for-byte, ic_ref == ic32 == golden  (native)
  S8  (v0.3 slice 2) spinner_bench._admit_projection -- the read-only structure
      the upgraded Film panel renders -- mirrors the golden admit claim-state
      exactly (e4 ResetFault ob; e7 6 facts, 5 Applied + 1 Rejected, all
      unambiguous) AND is a pure sidecar: the film hash is byte-identical whether
      or not it is computed (the film seal never reads it).
  S9  (v0.3 slice 3) the editable scenario table's data path: spinner_bench.
      _scenario_payload validates + digests an authored ScenarioV1 (typed
      WRL_BAD_SCENARIO on junk, no runtime lock); the RETRANSMIT gesture (exact
      envelope copy in a later epoch) adds no fact/receipt and applies no
      EpochControl (item 3, no 2nd effect); the EQUIVOCATE gesture (same event
      key, different payload, with fact headroom) makes w1s1 recognition
      `disputed` over 2 observed facts while the FIRST receipt stays immutable
      (item 4). On the fact-saturated golden preset EQUIVOCATE overflows instead
      -- an honest capacity fault, not a dispute.
  S10 (v0.3 slice 4) the ADMIT Acceptance Bench: a SECOND immutable preset
      (SC.bench_scenario, additional to the Golden ADMIT Demo) that walks all
      SEVEN roadmap acceptance behaviours on the SAME demo world with NO new
      runtime construct -- each behaviour given its own headroom: accept ->
      Applied; exact retransmit -> no fact/effect; conflicting same-key payload
      -> disputed with the first receipt immutable and NO capacity fault;
      saturating full-scale rotor -> orb fault latches on overflow; a reset in a
      safe (non-firing) epoch clears it; a reset on a firing epoch is re-latched
      by the same-epoch overflow; idle/replay stays latched + deterministic. The
      whole 9-epoch fold is ic_ref == ic32 == golden Film v0.7.

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import wrl_ir as W
import wrl_sugar as SG
import wrl_plan as P
import compiler as C
import admit as AD
import binding_run3o as O
import wrl_canonical as WC
import wrl_scenario as SC
import spinner_bench as SB
from admit import film_hash_v7
from fixture import init_state_v6, state_to_film_args_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"


def _fold_films(view, reducer, initial_faults, script):
    """Fold a (initial_faults, script) through the compiled step over the plan
    VIEW -- the exact production contract spinner_bench._run_traj uses -- and
    return (films, worlds). No Fixture is reconstructed."""
    world = init_state_v6(view)
    for o in initial_faults:
        if ("fault_" + o) in world:
            world["fault_" + o] = 1
    claim = AD.init_claimstate()
    step, _ = C.compile_step_v6(view)
    films, worlds = [], []
    for e, (label, batch) in enumerate(script):
        ep = 1 + e
        claim, cfg_map, resets = AD.admit_step(claim, batch, ep, view)
        ec = C.enc_config_bundle(view, cfg_map, resets)
        world = C.dec_state_v6(view, reducer(
            f"(({step} {ec}) {C.enc_state_v6(view, world)})"))
        films.append(film_hash_v7(*state_to_film_args_v6(view, world, ep),
                                  state=claim))
        worlds.append({k: (list(v) if isinstance(v, tuple) else v)
                       for k, v in world.items()})
    return films, worlds


def main():
    print("[BINDING wrl-scenario] ScenarioV1 + ScenarioDigest (v0.3 slice 1)")
    allok = True
    native_ok = True
    t0 = time.time()

    def rep(ok, okn, label):
        nonlocal allok, native_ok
        allok &= bool(ok)
        tag = "PASS" if ok else "FAIL"
        if okn is False:
            native_ok = False
            tag = "FAIL(native)"
        print(f"  [{tag}] {label}")

    # the world under test and its (constant) identity
    prog = SB._prog(SB.DEMO_WORLD_SOURCE)
    sem = prog.semantic_artifact_id
    view = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))

    # ---- S1 typed structural gate ------------------------------------------
    good = SC.demo_scenario(sem)
    s1 = True
    try:
        SC.validate_scenario_v1(good)           # well-formed (incl. `zz` target)
    except Exception:
        s1 = False

    def _rejects(mutate):
        sc = SC.demo_scenario(sem)
        mutate(sc)
        try:
            SC.validate_scenario_v1(sc)
            return False
        except WC.WrlValidationError as e:
            return e.code == SC.WRL_BAD_SCENARIO

    def _bad_version(sc):
        sc["scenario_version"] = "scenario.v2"

    def _extra_key(sc):
        sc["extra"] = 1

    def _missing_key(sc):
        del sc["epochs"]

    def _bad_world(sc):
        sc["world_semantic_id"] = "not-a-sem-id"

    def _gap_epochs(sc):
        sc["epochs"][2]["epoch"] = 9        # breaks the 1..N contiguity

    def _overflow_batch(sc):
        c = sc["epochs"][0]["claims"][0]
        sc["epochs"][0]["claims"] = [dict(c, sequence=i)
                                     for i in range(SC.MAX_BATCH + 1)]

    def _bad_op(sc):
        sc["epochs"][0]["claims"][0]["operation"] = "Detonate"

    def _bad_payload(sc):
        sc["epochs"][0]["claims"][0]["payload"] = {"rotor": [1, 2, 3]}  # 3 ints

    for m in (_bad_version, _extra_key, _missing_key, _bad_world, _gap_epochs,
              _overflow_batch, _bad_op, _bad_payload):
        if not _rejects(m):
            s1 = False
    rep(s1, None, "S1) validate: well-formed (incl. out-of-world target) passes; "
                  "version/keys/world-id/epoch-gap/over-batch/op/payload -> "
                  "typed WRL_BAD_SCENARIO")

    # ---- S2 canonical is claim- AND fault-order-independent -----------------
    # epoch 7 has two claims -> reversing them must canonicalize identically.
    base = SC.demo_scenario(sem)
    shuf = SC.demo_scenario(sem)
    shuf["epochs"][6]["claims"] = list(reversed(shuf["epochs"][6]["claims"]))
    shuf["initial_runtime"]["numeric_faults"] = list(reversed(
        shuf["initial_runtime"]["numeric_faults"]))  # 1 elt, but still exercised
    s2 = (SC.canonicalize_scenario_v1(base) == SC.canonicalize_scenario_v1(shuf)
          and SC.scenario_digest(base) == SC.scenario_digest(shuf))
    rep(s2, None, "S2) canonicalization + ScenarioDigest are claim-order- and "
                  "fault-order-independent")

    # ---- S3 acceptance 1 & 2 -----------------------------------------------
    dig0 = SC.scenario_digest(base)
    # (2) a scenario edit moves the ScenarioDigest ...
    edited = SC.demo_scenario(sem)
    edited["epochs"][1]["claims"] = [        # was an idle epoch; add a claim
        {"writer_id": 7, "sequence": 7, "operation": "SetRotor",
         "target": "sp", "payload": {"rotor": [200, 0, 0, 0]}}]
    dig1 = SC.scenario_digest(edited)
    # ... while the world's SemanticArtifactID is untouched (same DEMO_WORLD_SOURCE).
    sem_after = SB._prog(SB.DEMO_WORLD_SOURCE).semantic_artifact_id
    acc2 = (dig1 != dig0) and (sem_after == sem)
    # (1) a world edit moves the SemanticArtifactID while the ScenarioDigest for
    #     the same run inputs is untouched (world_semantic_id excluded).
    src2 = SB.DEMO_WORLD_SOURCE.replace("rotor=quarter_turn_z", "rotor=identity")
    prog2 = W.lower_program(SG.desugar_core(src2), W.parse_wrl_core)
    sem2 = prog2.semantic_artifact_id
    retargeted = SC.demo_scenario(sem2)      # same inputs, new world id
    acc1 = (sem2 != sem) and (SC.scenario_digest(retargeted) == dig0)
    rep(acc1 and acc2, None, "S3) scenario edit moves ScenarioDigest (world id "
                             "fixed); world edit moves SemanticArtifactID "
                             "(ScenarioDigest fixed)  [acceptance 1 & 2]")

    # ---- S4 world_semantic_id excluded from the digest domain ---------------
    a = SC.demo_scenario(sem)
    b = SC.demo_scenario(sem2)               # different world, identical inputs
    s4 = SC.scenario_digest(a) == SC.scenario_digest(b)
    rep(s4, None, "S4) world_semantic_id is excluded from the digest domain "
                  "(identical inputs, different world -> same ScenarioDigest)")

    # ---- S5 ReplayBundleID binds world + scenario + initial runtime ---------
    ir = {"numeric_faults": ["ob"]}
    r0 = SC.replay_bundle_id(sem, dig0, ir)
    r_world = SC.replay_bundle_id(sem2, dig0, ir)          # world changed
    r_scen = SC.replay_bundle_id(sem, dig1, ir)            # scenario changed
    r_ir = SC.replay_bundle_id(sem, dig0, {"numeric_faults": []})  # ir changed
    r_same = SC.replay_bundle_id(sem, dig0, {"numeric_faults": ["ob"]})
    s5 = (r0 == r_same and len({r0, r_world, r_scen, r_ir}) == 4
          and r0.startswith("replay-"))
    rep(s5, None, "S5) ReplayBundleID moves on world/scenario/initial-runtime "
                  "change, stable otherwise")

    # ---- S6 scenario_to_script == the hard-coded SCRIPT envelopes -----------
    initial_faults, script = SC.scenario_to_script(SC.demo_scenario(sem))
    s6 = (initial_faults == ("ob",)
          and len(script) == len(SB.SCRIPT)
          and [b for _, b in script] == [b for _, b in SB.SCRIPT])
    rep(s6, None, "S6) scenario_to_script(demo) claim envelopes == hard-coded "
                  "SCRIPT (initial_faults=('ob',); labels are UI-only)")

    # ---- S7 demo_scenario reproduces the SCRIPT films (native) --------------
    ref_films, ref_worlds = _fold_films(view, O.norm, ("ob",), SB.SCRIPT)
    scn_films, scn_worlds = _fold_films(view, O.norm, initial_faults, script)
    s7r = (scn_films == ref_films and scn_worlds == ref_worlds)
    s7n = None
    if not SKIP_NATIVE:
        nat_films, nat_worlds = _fold_films(view, O.native,
                                            initial_faults, script)
        s7n = (nat_films == ref_films and nat_worlds == ref_worlds)
    rep(s7r, s7n, "S7) demo_scenario folded via plan/view reproduces the SCRIPT "
                  "films byte-for-byte, ic_ref == ic32 == golden")

    # ---- S8 admit projection (Film panel v0.3 sidecar) is faithful ----------
    # spinner_bench._admit_projection is the read-only structure the upgraded
    # Film panel renders. It must mirror the golden admit claim-state exactly
    # AND perturb no identity: the film hash is byte-identical whether or not it
    # is computed (it is an additive row field the film seal never reads).
    claim = AD.init_claimstate()
    step, _ = C.compile_step_v6(view)
    world = init_state_v6(view)
    for o in initial_faults:
        if ("fault_" + o) in world:
            world["fault_" + o] = 1
    projs, side_films = [], []
    for e, (label, batch) in enumerate(script):
        ep = 1 + e
        claim, cfg_map, resets = AD.admit_step(claim, batch, ep, view)
        ec = C.enc_config_bundle(view, cfg_map, resets)
        world = C.dec_state_v6(view, O.norm(
            f"(({step} {ec}) {C.enc_state_v6(view, world)})"))
        side_films.append(film_hash_v7(*state_to_film_args_v6(view, world, ep),
                                       state=claim))
        projs.append(SB._admit_projection(view, claim, cfg_map, resets))
    # projection never touches the film seal -> byte-identical to S7's ref fold.
    s8_side = (side_films == ref_films)
    # epoch 4 (idx 3): a ResetFault ob is the applied EpochControl.
    p4 = projs[3]
    s8_reset = (p4["epoch_control"]["reset_fault"] == ["ob"])
    # epoch 7 (idx 6): 6 observed facts; the out-of-world `zz` claim canonical-
    # ized to an INVALID_TARGET SetRotor -> Rejected(unknown_spinner); every
    # other writer Applied; every writer's recognition unambiguous; the applied
    # rotor for sp is 10.0.0.0.
    p7 = projs[6]
    outcomes = sorted(r["outcome"] for r in p7["receipts"])
    s8_e7 = (len(p7["facts"]) == 6
             and outcomes == sorted(["Applied"] * 5
                                    + ["Rejected(unknown_spinner)"])
             and all(g["state"] == "unambiguous" for g in p7["recognition"])
             and p7["epoch_control"]["set_rotor"].get("sp") == [10, 0, 0, 0]
             and p7["policy"] == AD.ACCEPTANCE_POLICY_ID
             and p7["capacity_fault"] == 0)
    rep(s8_side and s8_reset and s8_e7, None,
        "S8) _admit_projection mirrors the golden admit state (e4 ResetFault ob; "
        "e7 6 facts, 5 Applied + 1 Rejected(unknown_spinner), all unambiguous, "
        "sp<-10.0.0.0, no overflow) and is a pure sidecar (film hash unchanged)")

    # ---- S9 (v0.3 slice 3) the Author editor's data path -------------------
    # The editable scenario table posts every edit to spinner_bench._scenario_
    # payload (pure validate + digest, NO runtime lock) and advertises two
    # structural gestures -- retransmit and equivocate -- whose ADMIT semantics
    # this asserts at the data level (the same _admit_projection the panel shows).
    def _fold_projections(scn):
        """Fold a ScenarioV1 through the SAME plan/view admit path the panel
        renders; return the per-epoch _admit_projection list (no Fixture)."""
        ifaults, scr = SC.scenario_to_script(scn)
        claim = AD.init_claimstate()
        out = []
        for e, (label, batch) in enumerate(scr):
            claim, cfg_map, resets = AD.admit_step(claim, batch, 1 + e, view)
            out.append(SB._admit_projection(view, claim, cfg_map, resets))
        return out

    # (a) _scenario_payload mirrors the pure identity module and rejects junk.
    good_sc = SC.demo_scenario(sem)
    pay = SB._scenario_payload(SB.DEMO_WORLD_SOURCE, good_sc)
    junk = SB._scenario_payload(SB.DEMO_WORLD_SOURCE,
                                dict(good_sc, scenario_version="scenario.v2"))
    s9a = (pay.get("ok")
           and pay["world_semantic_id"] == sem
           and pay["scenario_digest"] == SC.scenario_digest(good_sc)
           and pay["replay_bundle_id"] == SC.replay_bundle_id(
               sem, SC.scenario_digest(good_sc), good_sc["initial_runtime"])
           and (junk.get("ok") is False)
           and (SC.WRL_BAD_SCENARIO in junk.get("error", "")))

    # (b) RETRANSMIT (acceptance item 3, no 2nd effect): appending an EXACT copy
    # of epoch-1's claim in a later epoch adds NO fact and NO receipt -- the
    # first-receipt policy already sealed w1s1 -- so the observed-fact and
    # receipt sets are identical to the un-retransmitted fold, the retransmit
    # epoch applies NO EpochControl, w1s1 stays unambiguous, and no fault latches.
    base_last = _fold_projections(good_sc)[-1]
    retx = SC.demo_scenario(sem)
    dup = dict(retx["epochs"][0]["claims"][0])          # exact envelope copy
    retx["epochs"].append({"epoch": 8, "label": "retransmit w1s1",
                           "claims": [dict(dup)]})
    SC.validate_scenario_v1(retx)
    retx_last = _fold_projections(retx)[-1]

    def _rk(p):        # comparable immutable-receipt view
        return sorted((r["writer"], r["sequence"], r["accepted_digest"],
                       r["accepted_epoch"], r["outcome"]) for r in p["receipts"])

    def _fk(p):
        return sorted((f["writer"], f["sequence"], f["digest"])
                      for f in p["facts"])
    r_w1 = next(g for g in retx_last["recognition"] if g["writer"] == 1)
    s9b = (_rk(retx_last) == _rk(base_last)
           and _fk(retx_last) == _fk(base_last)
           and retx_last["capacity_fault"] == 0
           and r_w1["state"] == "unambiguous"
           and retx_last["epoch_control"]["set_rotor"] == {}
           and retx_last["epoch_control"]["reset_fault"] == [])

    # (c) EQUIVOCATE (acceptance item 4): the SAME event key (w1s1) with a
    # DIFFERENT payload -- shown on a SMALL scenario WITH fact headroom (the
    # golden preset is deliberately fact-SATURATED, so there the conflicting
    # fact overflows instead of disputing; the button honestly surfaces that).
    # With room the conflicting fact IS observed -> w1s1 recognition becomes
    # `disputed`, yet the receipt stays the FIRST, immutable acceptance.
    small = {"scenario_version": SC.SCENARIO_VERSION, "world_semantic_id": sem,
             "initial_runtime": {"numeric_faults": []},
             "epochs": [
                 {"epoch": 1, "label": "claim v1",
                  "claims": [{"writer_id": 1, "sequence": 1,
                              "operation": "SetRotor", "target": "sp",
                              "payload": {"rotor": [40, 0, 0, 0]}}]},
                 {"epoch": 2, "label": "equivocate w1s1",
                  "claims": [{"writer_id": 1, "sequence": 1,
                              "operation": "SetRotor", "target": "sp",
                              "payload": {"rotor": [41, 0, 0, 0]}}]}]}
    SC.validate_scenario_v1(small)
    eq_last = _fold_projections(small)[-1]
    g_w1 = next(g for g in eq_last["recognition"] if g["writer"] == 1)
    rc_w1 = next(r for r in eq_last["receipts"] if r["writer"] == 1)
    s9c = (g_w1["state"] == "disputed"
           and eq_last["capacity_fault"] == 0
           and rc_w1["outcome"] == "Applied"
           and len([f for f in eq_last["facts"] if f["writer"] == 1]) == 2)

    rep(s9a and s9b and s9c, None,
        "S9) Author editor data path: _scenario_payload validates+digests (typed "
        "WRL_BAD_SCENARIO on junk); RETRANSMIT of an exact envelope adds no "
        "fact/receipt and applies no EpochControl (item 3, no 2nd effect); "
        "EQUIVOCATE (same key, diff payload, with headroom) -> w1s1 disputed "
        "with 2 observed facts while the first receipt stays Applied (item 4)")

    # ---- S10 (v0.3 slice 4) the ADMIT Acceptance Bench preset ---------------
    # SC.bench_scenario is a SECOND immutable preset (additional to the Golden
    # ADMIT Demo) that walks the seven roadmap acceptance behaviours on the SAME
    # demo world, each with its own headroom, using ONLY existing physics (no new
    # runtime construct). This asserts all seven at the projection AND world-fault
    # level, that the disputed step is a true recognition split (never a capacity
    # fault), and that the whole 9-epoch fold is ic_ref == ic32 == golden Film v0.7.
    bench = SC.bench_scenario(sem)
    SC.validate_scenario_v1(bench)                 # the preset is well-formed
    b_faults, b_script = SC.scenario_to_script(bench)
    b_projs = _fold_projections(bench)
    b_films, b_worlds = _fold_films(view, O.norm, b_faults, b_script)
    fault_at = [w["fault_ob"] for w in b_worlds]   # per-epoch orb fault latch

    def _recog(p, w, s):
        return next((g["state"] for g in p["recognition"]
                     if g["writer"] == w and g["sequence"] == s), None)

    def _nfacts(p):
        return len(p["facts"])

    def _clean(p):                                  # never a capacity fault
        return p["capacity_fault"] == 0

    # 1 accept SetRotor: ep1 sets the full-scale rotor, w1s1 receipt Applied.
    p1 = b_projs[0]
    s10_1 = (_nfacts(p1) == 1 and _recog(p1, 1, 1) == "unambiguous"
             and p1["epoch_control"]["set_rotor"].get("sp") == [(1 << 15) - 1, 0, 0, 0]
             and any(r["writer"] == 1 and r["outcome"] == "Applied"
                     for r in p1["receipts"]) and _clean(p1))
    # 2 exact retransmit: ep2 is the SAME envelope -> NO new fact, NO EpochControl.
    p2 = b_projs[1]
    s10_2 = (_nfacts(p2) == 1
             and p2["epoch_control"]["set_rotor"] == {}
             and p2["epoch_control"]["reset_fault"] == [] and _clean(p2))
    # 3 conflicting payload, same event key: ep3 emits w3s3 twice (diff payload)
    # -> recognition disputed, first receipt stays; 3 facts total, NO overflow.
    p3 = b_projs[2]
    s10_3 = (_recog(p3, 3, 3) == "disputed" and _nfacts(p3) == 3 and _clean(p3)
             and any(r["writer"] == 3 and r["outcome"] == "Applied"
                     for r in p3["receipts"]))
    # 4 saturating rotor -> fault LATCHES: fault is clear through ep5, latches at
    # ep6 (the overflow epoch), with NO ResetFault in play.
    s10_4 = (fault_at[:5] == [0, 0, 0, 0, 0] and fault_at[5] == 1
             and b_projs[5]["epoch_control"]["reset_fault"] == [])
    # 5 reset in a safe (non-firing) epoch -> CLEARS: ep7 applies ResetFault ob
    # and the fault drops to 0 (no same-epoch overflow to re-latch).
    p7b = b_projs[6]
    s10_5 = (p7b["epoch_control"]["reset_fault"] == ["ob"] and fault_at[6] == 0)
    # 6 reset + same-epoch overflow -> STAYS latched: ep8 applies ResetFault ob on
    # a firing epoch; COMMIT clears the old fault but REACT re-latches -> fault 1.
    p8b = b_projs[7]
    s10_6 = (p8b["epoch_control"]["reset_fault"] == ["ob"] and fault_at[7] == 1)
    # 7 idle / replay verify: ep9 is idle, the fault remains latched, and folding
    # the SAME scenario again is byte-identical (deterministic replay).
    b_films2, _ = _fold_films(view, O.norm, b_faults, b_script)
    s10_7 = (fault_at[8] == 1 and b_films2 == b_films)
    s10r = all([s10_1, s10_2, s10_3, s10_4, s10_5, s10_6, s10_7])
    s10n = None
    if not SKIP_NATIVE:
        nat_bfilms, nat_bworlds = _fold_films(view, O.native, b_faults, b_script)
        s10n = (nat_bfilms == b_films
                and [w["fault_ob"] for w in nat_bworlds] == fault_at)
    rep(s10r, s10n,
        "S10) ADMIT Acceptance Bench preset walks all 7 behaviours on the demo "
        "world (no new construct): 1 accept -> Applied; 2 retransmit -> no fact/"
        "effect; 3 conflicting key -> disputed, receipt stays, no overflow; 4 "
        "saturating rotor -> fault latches @ep6; 5 safe reset -> clears; 6 reset+"
        "overflow -> stays latched; 7 idle/replay -> latched + deterministic; "
        "9-epoch fold ic_ref == ic32 == golden Film v0.7")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-scenario] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] ScenarioV1 is a pure DATA document; it introduces NO runtime "
          "construct. Its identity (ScenarioDigest) is computed over the "
          "canonical run inputs ONLY (initial_runtime + epochs), so it is "
          "orthogonal to the world's SemanticArtifactID. The golden demo "
          "expressed as a ScenarioV1 lowers to the exact same admit script and "
          "reproduces byte-identical films.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
