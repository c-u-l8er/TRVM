"""binding_run24.py -- v0.5-1 immutable content-addressed object stores
(Forge World Library, phase 1).

GPT-5.6's v0.5 = Forge World Library / project persistence. After the v0.5-0
Source Surface Closure (binding_run23), v0.5-1 lays the IMMUTABLE substrate:
three filesystem-backed, content-addressed stores keyed by the existing identity
ladder (wrl_store.py) -- WorldObjectStore (sem-), ScenarioRuntimeStore (scen-),
ReplayBundleStore (replay-). NO new identity, NO new runtime construct.

Battery N1-N8:

  N1  WorldObjectStore round-trips a sealed world by its SemanticArtifactID
      (get reproduces byte-identical canonical bytes; has() true; re-put idempotent);
  N2  content addressing -- a reorder-equivalent world collapses to the SAME id
      and the SAME single file on disk;
  N3  hash-verified read -- a tampered on-disk world surfaces as a TYPED
      WRL_STORE_CORRUPT, never silent bad data;
  N4  a get of an absent id is a TYPED WRL_STORE_MISSING, never a raw OSError;
  N5  ScenarioRuntimeStore keys by ScenarioDigest and stores the RUNTIME DOMAIN
      only -- a label-only edit collapses to the SAME file (world-id/label excluded);
  N6  ReplayBundleStore keys by ReplayBundleID; a world edit moves the bundle id
      (new file) while the scenario store is untouched; a malformed ref is TYPED;
  N7  persistence -- a FRESH store instance over the same root reads + verifies
      what the first instance wrote (no in-memory index);
  N8  NATIVE -- a demo world routed THROUGH the WorldObjectStore (put -> get ->
      re-lowered from the stored canonical artifact) folds ic_ref == ic32 == the
      Fixture oracle over its demo scenario.

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import os
import sys
import shutil
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import wrl_ir as W
import wrl_plan as P
import compiler as C
import admit as AD
import binding_run3o as O
import wrl_canonical as WC
import wrl_scenario as SC
import wrl_sugar as SG
import wrl_store as ST
import spinner_bench as SB
from admit import film_hash_v7
from fixture import init_state_v6, state_to_film_args_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"


def _fold_films(view, reducer, initial_faults, script):
    world = init_state_v6(view)
    for o in initial_faults:
        if ("fault_" + o) in world:
            world["fault_" + o] = 1
    claim = AD.init_claimstate()
    step, _ = C.compile_step_v6(view)
    films = []
    for e, (label, batch) in enumerate(script):
        ep = 1 + e
        claim, cfg_map, resets = AD.admit_step(claim, batch, ep, view)
        ec = C.enc_config_bundle(view, cfg_map, resets)
        world = C.dec_state_v6(view, reducer(
            f"(({step} {ec}) {C.enc_state_v6(view, world)})"))
        films.append(film_hash_v7(*state_to_film_args_v6(view, world, ep),
                                  state=claim))
    return films


def _fold_fixture(fx, view, reducer, initial_faults, script):
    world = init_state_v6(fx)
    for o in initial_faults:
        if ("fault_" + o) in world:
            world["fault_" + o] = 1
    claim = AD.init_claimstate()
    step, _ = C.compile_step_v6(view)
    films = []
    for e, (label, batch) in enumerate(script):
        ep = 1 + e
        claim, cfg_map, resets = AD.admit_step(claim, batch, ep, fx)
        ec = C.enc_config_bundle(view, cfg_map, resets)
        world = C.dec_state_v6(view, reducer(
            f"(({step} {ec}) {C.enc_state_v6(view, world)})"))
        films.append(film_hash_v7(*state_to_film_args_v6(fx, world, ep),
                                  state=claim))
    return films


def _raises(fn, code):
    """True iff `fn()` raises a TYPED WrlValidationError with the given code
    (NOT a raw Python exception)."""
    try:
        fn()
        return False
    except WC.WrlValidationError as ex:
        return ex.code == code
    except Exception:
        return False


def main():
    print("[BINDING wrl-v0.5-1] Immutable content-addressed object stores (N1-N8)")
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

    root = tempfile.mkdtemp(prefix="wrl_store_")
    try:
        prog = SB._prog(SB.DEMO_WORLD_SOURCE)     # desugar -> lower -> sealed
        sem = prog.semantic_artifact_id

        # ---- N1 WorldObjectStore round-trip ---------------------------------
        ws = ST.WorldObjectStore(os.path.join(root, "worlds"))
        put_id = ws.put(prog.sealed_artifact)
        got = ws.get(put_id)
        n1 = (put_id == sem and ws.has(sem)
              and got.semantic_id == sem
              and got.canonical_bytes == prog.sealed_artifact.canonical_bytes
              # re-put is idempotent (same id, no error, still one file)
              and ws.put(prog.sealed_artifact) == sem
              and ws.ids() == [sem])
        rep(n1, None,
            "N1) WorldObjectStore round-trips a sealed world by SemanticArtifactID "
            "(byte-identical, has() true, re-put idempotent)")

        # ---- N2 content addressing collapses reorder-equivalents ------------
        # re-lower the SAME world from a source whose NODE declarations are
        # reversed (still before the edge block) -> identical sem id, so the
        # store must hold exactly ONE file.
        lines = [ln for ln in SB.DEMO_WORLD_SOURCE.strip().splitlines()
                 if ln.strip()]
        nodes = [ln for ln in lines if ln.startswith("[") and "-->" not in ln]
        edges = [ln for ln in lines if "-->" in ln]
        reordered = ("profile forge.world.core.v1\n\n"
                     + "\n".join(reversed(nodes)) + "\n\n" + "\n".join(edges)
                     + "\n")
        prog2 = SB._prog(reordered)
        id2 = ws.put(prog2.sealed_artifact)
        n2 = (prog2.semantic_artifact_id == sem and id2 == sem
              and ws.ids() == [sem])
        rep(n2, None,
            "N2) a reorder-equivalent world collapses to the SAME id and the SAME "
            "single file on disk")

        # ---- N3 hash-verified read catches tampering ------------------------
        tampered_root = os.path.join(root, "tampered")
        ws3 = ST.WorldObjectStore(tampered_root)
        ws3.put(prog.sealed_artifact)
        with open(os.path.join(tampered_root, sem + ".json"), "wb") as f:
            f.write(b'{"tampered":true}')
        n3 = _raises(lambda: ws3.get(sem), ST.WRL_STORE_CORRUPT)
        rep(n3, None,
            "N3) a tampered on-disk world surfaces as a TYPED WRL_STORE_CORRUPT "
            "(never silent bad data)")

        # ---- N4 missing get is a typed diagnostic ---------------------------
        absent = "sem-" + ("0" * 64)
        n4 = _raises(lambda: ws.get(absent), ST.WRL_STORE_MISSING)
        rep(n4, None,
            "N4) a get of an absent id is a TYPED WRL_STORE_MISSING (never a raw "
            "OSError)")

        # ---- N5 ScenarioRuntimeStore keys by ScenarioDigest, label-independent
        ss = ST.ScenarioRuntimeStore(os.path.join(root, "scenarios"))
        scen = SC.demo_scenario(sem)
        scen_id = ss.put(scen)
        canon = SC.canonicalize_scenario_v1(scen)
        domain = ss.get(scen_id)
        # a label-only edit: change the first epoch's UI label
        scen_lbl = WC._plain(scen)
        scen_lbl["epochs"][0]["label"] = "RELABELED (documentation only)"
        id_lbl = ss.put(scen_lbl)
        n5 = (scen_id == SC.scenario_digest(scen)
              and domain["initial_runtime"] == canon["initial_runtime"]
              and domain["epoch_batches"] == [e["claims"] for e in canon["epochs"]]
              and id_lbl == scen_id          # label edit does not move the digest
              and ss.ids() == [scen_id])     # ... and collapses to ONE file
        rep(n5, None,
            "N5) ScenarioRuntimeStore keys by ScenarioDigest and stores the RUNTIME "
            "DOMAIN only; a label-only edit collapses to the SAME file")

        # ---- N6 ReplayBundleStore: world edit moves the bundle --------------
        rs = ST.ReplayBundleStore(os.path.join(root, "replays"))
        ir = scen["initial_runtime"]
        rid = rs.put(sem, scen_id, ir)
        # a DIFFERENT world (drop the once-at-1 pulser + its door) -> new sem id,
        # same scenario digest -> a different replay bundle id.
        edited_src = """profile forge.world.core.v1

[pulser:p0](every 2){sig_out}
[relay:r0]{sig_in, sig_out}
[spinner:sp](w=16, n=8, rotor=quarter_turn_z, configurable){sig_in, socket}
[orb:ob]{pose}

[pulser:p0] --sig--> [relay:r0]
[relay:r0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]
"""
        # desugar-then-lower so the concise clock / named rotor are canonical
        prog_e = W.lower_program(SG.desugar_core(edited_src), W.parse_wrl_core)
        sem_e = prog_e.semantic_artifact_id
        rid_e = rs.put(sem_e, scen_id, ir)
        bundle = rs.get(rid)
        n6 = (rid == SC.replay_bundle_id(sem, scen_id, ir)
              and rid_e == SC.replay_bundle_id(sem_e, scen_id, ir)
              and sem_e != sem and rid_e != rid          # world edit moved the bundle
              and sorted(rs.ids()) == sorted([rid, rid_e])
              and bundle == [sem, scen_id, {"numeric_faults": sorted(
                  ir["numeric_faults"])}]
              # a malformed ref is a TYPED diagnostic, not a hash surprise
              and _raises(lambda: rs.put("not-a-sem", scen_id, ir),
                          ST.WRL_STORE_BAD_REF)
              and _raises(lambda: rs.put(sem, "not-a-scen", ir),
                          ST.WRL_STORE_BAD_REF))
        rep(n6, None,
            "N6) ReplayBundleStore keys by ReplayBundleID; a world edit moves the "
            "bundle id while the scenario store is untouched; malformed refs TYPED")

        # ---- N7 persistence: a fresh instance reads what the first wrote -----
        ws_reopened = ST.WorldObjectStore(os.path.join(root, "worlds"))
        ss_reopened = ST.ScenarioRuntimeStore(os.path.join(root, "scenarios"))
        n7 = (ws_reopened.get(sem).semantic_id == sem
              and ws_reopened.ids() == [sem]
              and ss_reopened.get(scen_id)["initial_runtime"]
              == canon["initial_runtime"])
        rep(n7, None,
            "N7) a FRESH store instance over the same root reads + verifies what the "
            "first instance wrote (no in-memory index)")

        # ---- N8 NATIVE: a world routed through the store still folds ---------
        got8 = ws.get(sem)                       # the world, re-read from disk
        view8 = P.plan_view(P.artifact_to_compile_plan_v1(got8))
        fx8 = prog.as_fixture_for_test()         # independent oracle
        scen8 = SC.demo_scenario(sem)
        ifa8, scr8 = SC.scenario_to_script(scen8)
        ref8 = _fold_films(view8, O.norm, ifa8, scr8)
        orc8 = _fold_fixture(fx8, view8, O.norm, ifa8, scr8)
        n8r = (got8.semantic_id == sem and ref8 == orc8)
        n8n = None
        if not SKIP_NATIVE:
            n8n = (_fold_films(view8, O.native, ifa8, scr8) == ref8)
        rep(n8r, n8n,
            "N8) NATIVE -- a demo world routed THROUGH the WorldObjectStore "
            "(put -> get -> re-lowered) folds ic_ref == ic32 == the Fixture oracle")
    finally:
        shutil.rmtree(root, ignore_errors=True)

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.5-1] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.5-1 lays the IMMUTABLE substrate of the Forge World "
          "Library: three filesystem-backed content-addressed stores keyed by "
          "the existing identity ladder (sem-/scen-/replay-), each idempotent on "
          "write and HASH-VERIFIED on read (tampering -> typed WRL_STORE_CORRUPT). "
          "Persistence is the atomic-write law (temp -> fsync -> rename). NO new "
          "identity, NO new runtime construct; a world routed through the store "
          "stays natively runnable ic_ref == ic32 == oracle (N8).")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
