"""binding_run29.py -- v0.5.1 Workspace Persistence Closure (W1-W22).

v0.5-5 (binding_run28) made a COMMITTED project portable. v0.5.1 closes the gap
GPT-5.6 flagged: the Library must persist the COMPLETE authoring workspace, not
just the last committed world. A ForgeProjectV2 document carries the exact draft
(valid OR invalid), the raw editor buffer with its parse status + diagnostics,
the paired semantic/layout undo stacks, the idempotency ledgers, the retained
active-world source (so the sealed active world stays runnable beside an invalid
draft), the scenario selection + compatibility, and the commit log. SAVE persists
all of it without activating a candidate; COMMIT still moves the active id only on
a validated, id-matched candidate (and also saves).

Battery W1-W22 (the v0.5.1 acceptance gate). A fresh ProjectSessionCache over the
same store root is a RESTART: it reconstructs the workspace from disk alone.

  W1  valid uncommitted draft survives restart (candidate id + validity restored;
      the active id is untouched -- an uncommitted edit is not activated);
  W2  invalid draft survives restart (candidate is None, the typed candidate_error
      is restored byte-for-byte);
  W3  a syntax-error raw source survives (the draft is untouched but the buffer the
      author is repairing + its parse_status come back);
  W4  the active sealed world stays runnable beside an invalid draft (its retained
      canonical source re-lowers to the active id while the draft is invalid);
  W5  the candidate id AND the source_document (diagnostics included) restore
      exactly;
  W6  the semantic revision AND the canvas layout restore exactly;
  W7  the accepted replace-id idempotency ledger survives -- a retry after restart
      still no-ops (no new revision);
  W8  the undo depth survives a restart;
  W9  undo AFTER a reopen restores the exact prior (semantic id, layout) pair;
  W10 the selected scenario document restores;
  W11 a detached / incompatible scenario compatibility status restores;
  W12 a label (display-name) change restores WITHOUT moving any ScenarioDigest;
  W13 Fork Saved reproduces the COMPLETE saved workspace (invalid draft included);
  W14 unsaved edits are EXCLUDED from Fork Saved (the fork reflects the SAVE);
  W15 a trashed project is restorable from its tombstone;
  W16 restoring over a live id is a typed WRL_PROJECT_EXISTS (non-destructive:
      the live project is untouched; a new id restores cleanly);
  W17 a FULL bundle carries every history-referenced world;
  W18 a FULL bundle that cannot resolve a history world fails WRL_BUNDLE_UNRESOLVED
      (never a silent downgrade);
  W19 a THIN bundle is explicitly marked (shallow_history) and drops history worlds
      while staying self-closed;
  W20 export -> import preserves an invalid, still-editable draft;
  W21 NATIVE -- a reopened/imported active world folds ic_ref == ic32 == the
      independent Fixture oracle;
  W22 the golden scenario presets are immutable (a fresh project carries the exact
      canonical golden + bench presets).

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import copy
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
import wrl_draft as D
import wrl_converge as CG
import wrl_project as PR
import wrl_store as ST
import wrl_bundle as B
import spinner_bench as SB
from admit import film_hash_v7
from fixture import init_state_v6, state_to_film_args_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

# a valid EDITED world (drop the once-at-1 pulser + door)
EDITED_SRC = """profile forge.world.core.v1

[pulser:p0](every 2){sig_out}
[relay:r0]{sig_in, sig_out}
[spinner:sp](w=16, n=8, rotor=quarter_turn_z, configurable){sig_in, socket}
[orb:ob]{pose}

[pulser:p0] --sig--> [relay:r0]
[relay:r0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]
"""

# a SECOND, distinct valid world (n=4) -- to build undo depth 2
EDITED2_SRC = """profile forge.world.core.v1

[pulser:p0](every 2){sig_out}
[relay:r0]{sig_in, sig_out}
[spinner:sp](w=16, n=4, rotor=quarter_turn_z, configurable){sig_in, socket}
[orb:ob]{pose}

[pulser:p0] --sig--> [relay:r0]
[relay:r0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]
"""

# a PARSEABLE but SEMANTICALLY INVALID world (two orb controllers)
INVALID_SRC = """profile forge.world.core.v1

[pulser:p0](every 2){sig_out}
[relay:r0]{sig_in, sig_out}
[spinner:sp](w=16, n=8, rotor=quarter_turn_z, configurable){sig_in, socket}
[spinner:sq](w=16, n=8, rotor=quarter_turn_z, configurable){sig_in, socket}
[orb:ob]{pose}

[pulser:p0] --sig--> [relay:r0]
[relay:r0] --sig--> [spinner:sp]
[spinner:sp] --socket--> [orb:ob]
[spinner:sq] --socket--> [orb:ob]
"""

# an UNPARSEABLE raw source (syntax error)
SYNTAX_BAD = "this is }{ not valid wrl at all @@@"

_SEQ = [0]


def _lower(src):
    return W.lower_program(SG.desugar_core(src), W.parse_wrl_core)


def _apply_text(sess, src, rid=None):
    _SEQ[0] += 1
    req = {"replace_version": D.REPLACE_VERSION,
           "replace_id": rid or ("e-%d-%d" % (int(time.time()), _SEQ[0])),
           "draft_id": sess.draft.draft_id,
           "base_revision": sess.draft.semantic_revision,
           "source": src}
    return sess.apply_text(req)


def _raises(fn, code):
    try:
        fn()
    except WC.WrlUnsupported as ex:
        return getattr(ex, "code", None) == code
    except Exception:
        return False
    return False


def _v2_cache(root):
    return PR.ProjectSessionCache(
        PR.ForgeProjectStore(os.path.join(root, "projects")),
        SB.DEMO_WORLD_SOURCE, scenarios_for=SB._default_scenarios,
        project_version=PR.PROJECT_V2_VERSION)


def _stores(root, tag):
    return (PR.ForgeProjectStore(os.path.join(root, tag, "projects")),
            ST.WorldObjectStore(os.path.join(root, tag, "worlds")),
            ST.ScenarioRuntimeStore(os.path.join(root, tag, "scen")))


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


def main():
    print("[BINDING wrl-v0.5.1] workspace persistence closure (W1-W22)")
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

    root = tempfile.mkdtemp(prefix="wrl_wsclose_")
    try:
        demo_sem = SB.DEMO_WORLD_SEMANTIC_ID
        edited_sem = _lower(EDITED_SRC).semantic_artifact_id
        edited2_sem = _lower(EDITED2_SRC).semantic_artifact_id

        # ---- W1 valid uncommitted draft survives restart -------------------
        c = _v2_cache(root)
        s = c.open("w1")
        _apply_text(s, EDITED_SRC)
        c.persist("w1")
        s1 = _v2_cache(root).open("w1")
        w1 = (s1.candidate_semantic_id == edited_sem
              and s1.candidate_error is None
              and s1.draft.active_semantic_id == demo_sem)   # NOT activated
        rep(w1, None,
            "W1) a VALID uncommitted draft survives a restart (candidate id + "
            "validity restored; the active world is NOT activated)")

        # ---- W2 invalid draft survives restart -----------------------------
        c = _v2_cache(root)
        s = c.open("w2")
        _apply_text(s, INVALID_SRC)
        err2 = s.draft.candidate_error
        srcdoc2 = copy.deepcopy(s.source_document)
        c.persist("w2")
        s2 = _v2_cache(root).open("w2")
        w2 = (s2.candidate_semantic_id is None
              and s2.candidate_error == err2
              and err2 and err2.startswith("WRL_CONTROLLER_CONFLICT"))
        rep(w2, None,
            "W2) an INVALID draft survives a restart (candidate None; the typed "
            "candidate_error is restored verbatim)")

        # ---- W3 syntax-error raw source survives ---------------------------
        c = _v2_cache(root)
        s = c.open("w3")
        _apply_text(s, SYNTAX_BAD)
        c.persist("w3")
        s3 = _v2_cache(root).open("w3")
        w3 = (s3.source_document["raw_source"] == SYNTAX_BAD
              and s3.source_document["parse_status"] == "syntax_error"
              and s3.draft.candidate_semantic_id == demo_sem   # draft untouched
              and s3.draft.candidate_error is None)
        rep(w3, None,
            "W3) a SYNTAX-ERROR raw source survives (the draft is untouched but "
            "the editor buffer + its parse_status come back)")

        # ---- W4 active sealed world runnable beside an invalid draft -------
        relowered = _lower(s2.active_world_source).semantic_artifact_id
        w4 = (relowered == demo_sem
              and s2.draft.active_semantic_id == demo_sem
              and s2.draft.candidate_error is not None)
        rep(w4, None,
            "W4) the active sealed world stays runnable beside an INVALID draft "
            "(its retained source re-lowers to the active id)")

        # ---- W5 candidate id + source_document (diagnostics) restore -------
        w5 = (s1.candidate_semantic_id == edited_sem
              and s2.source_document == srcdoc2
              and isinstance(srcdoc2["diagnostics"], list)
              and len(srcdoc2["diagnostics"]) >= 1)
        rep(w5, None,
            "W5) the candidate id AND the source_document (diagnostics included) "
            "restore exactly")

        # ---- W6 semantic revision + layout restore exactly -----------------
        c = _v2_cache(root)
        s = c.open("w6")
        _apply_text(s, EDITED_SRC)
        rev6 = s.draft.semantic_revision
        layout6 = copy.deepcopy(s.layout)
        c.persist("w6")
        s6 = _v2_cache(root).open("w6")
        w6 = (s6.draft.semantic_revision == rev6 and s6.layout == layout6)
        rep(w6, None,
            "W6) the semantic revision AND the canvas layout restore exactly")

        # ---- W7 accepted replace-id ledger survives (idempotent retry) -----
        c = _v2_cache(root)
        s = c.open("w7")
        _apply_text(s, EDITED_SRC, rid="fixed-replace-7")
        ledger7 = D.draft_state(s.draft)["accepted_replace_ids"]
        c.persist("w7")
        s7 = _v2_cache(root).open("w7")
        rev_before = s7.draft.semantic_revision
        # a retry of the SAME replace id must no-op across the restart
        res7 = _apply_text(s7, EDITED_SRC, rid="fixed-replace-7")
        w7 = (D.draft_state(s7.draft)["accepted_replace_ids"] == ledger7
              and "fixed-replace-7" in ledger7
              and s7.draft.semantic_revision == rev_before)   # no new revision
        rep(w7, None,
            "W7) the accepted replace-id idempotency ledger survives a restart -- "
            "a retry still no-ops (no new revision)")

        # ---- W8 undo depth survives ----------------------------------------
        c = _v2_cache(root)
        s = c.open("w8")
        _apply_text(s, EDITED_SRC)
        # a reference layout of the world AFTER the first edit (for W9)
        ref_after_edit = CG.new_session(_lower(SB.DEMO_WORLD_SOURCE), "main")
        _apply_text(ref_after_edit, EDITED_SRC)
        layout_after_edit = copy.deepcopy(ref_after_edit.layout)
        _apply_text(s, EDITED2_SRC)
        c.persist("w8")
        s8 = _v2_cache(root).open("w8")
        w8 = (s8.history()["undo_depth"] == 2
              and s8.draft.candidate_semantic_id == edited2_sem)
        rep(w8, None,
            "W8) the undo depth survives a restart (two edits -> depth 2)")

        # ---- W9 undo AFTER reopen restores the prior (id, layout) pair -----
        u9 = s8.undo()
        w9 = (u9["candidate_semantic_id"] == edited_sem
              and u9["candidate_valid"]
              and s8.layout == layout_after_edit)
        rep(w9, None,
            "W9) undo AFTER a reopen restores the exact prior (semantic id, "
            "layout) pair")

        # ---- W10 selected scenario restores --------------------------------
        c = _v2_cache(root)
        s = c.open("w10")
        s.select_scenario("golden")
        c.persist("w10")
        s10 = _v2_cache(root).open("w10")
        w10 = (s10.selected_scenario == "golden")
        rep(w10, None, "W10) the selected scenario document restores")

        # ---- W11 detached/incompatible scenario status restores ------------
        compat = {"compatible": False, "reason": "detached from active world"}
        c = _v2_cache(root)
        s = c.open("w11")
        s.select_scenario("bench", compat)
        c.persist("w11")
        s11 = _v2_cache(root).open("w11")
        w11 = (s11.selected_scenario == "bench"
               and s11.scenario_compatibility == compat)
        rep(w11, None,
            "W11) a detached / incompatible scenario compatibility status restores")

        # ---- W12 label change restores WITHOUT moving a ScenarioDigest -----
        c = _v2_cache(root)
        c.open("w12")
        store = PR.ForgeProjectStore(os.path.join(root, "projects"))
        digests_before = [sd["scenario_digest"]
                          for sd in PR._scenarios_of(store.load("w12"))]
        c.rename("w12", "Renamed Workspace")
        c.persist("w12")
        s12doc = _v2_cache(root)._store.load("w12")
        digests_after = [sd["scenario_digest"]
                         for sd in PR._scenarios_of(s12doc)]
        w12 = (s12doc["name"] == "Renamed Workspace"
               and digests_after == digests_before)
        rep(w12, None,
            "W12) a display-name change restores WITHOUT moving any ScenarioDigest")

        # ---- W13 Fork Saved reproduces the COMPLETE saved workspace --------
        # w2 was SAVED with an invalid draft: its fork must reproduce it exactly.
        c = _v2_cache(root)
        c.open("w2")                       # ensure loadable
        fork13 = c.fork("w2", "w2fork")
        base13 = c.open("w2")
        w13 = (CG.session_state(fork13) == CG.session_state(base13)
               and fork13.candidate_error == err2)
        rep(w13, None,
            "W13) Fork Saved reproduces the COMPLETE saved workspace (invalid "
            "draft included)")

        # ---- W14 unsaved edits are EXCLUDED from Fork Saved ----------------
        c = _v2_cache(root)
        s = c.open("w14")
        c.persist("w14")                   # SAVE a clean demo workspace
        _apply_text(s, EDITED_SRC)         # edit but do NOT persist
        fork14 = c.fork("w14", "w14fork")
        w14 = (fork14.candidate_semantic_id == demo_sem     # reflects the SAVE
               and s.candidate_semantic_id == edited_sem)   # live edit intact
        rep(w14, None,
            "W14) unsaved edits are EXCLUDED from Fork Saved (the fork reflects "
            "the SAVE, not the live uncommitted edit)")

        # ---- W15 trashed project is restorable -----------------------------
        c = _v2_cache(root)
        c.open("w15")
        c.persist("w15")
        c.trash("w15")
        trash_list = c.list_trash()
        tid15 = next(t["trash_id"] for t in trash_list
                     if t["original_project_id"] == "w15")
        restored15 = c.restore(tid15)
        w15 = (any(t["original_project_id"] == "w15" for t in trash_list)
               and restored15.draft.active_semantic_id == demo_sem
               and c._store.exists("w15"))
        rep(w15, None,
            "W15) a trashed project is restorable from its tombstone")

        # ---- W16 restore collision is typed + non-destructive --------------
        c = _v2_cache(root)
        c.open("w16")
        c.persist("w16")
        store16 = c._store
        store16.trash("w16")
        tid16 = next(t["trash_id"] for t in store16.list_trash()
                     if t["original_project_id"] == "w16")
        c.create_new("w16", "Live Again")    # a NEW live project at the same id
        live_rev = c._store.load("w16")["project_revision"]
        collide = _raises(lambda: store16.restore(tid16), PR.WRL_PROJECT_EXISTS)
        moved = store16.restore(tid16, "w16b")     # a new id restores cleanly
        w16 = (collide
               and moved["project_id"] == "w16b"
               and c._store.load("w16")["name"] == "Live Again"   # untouched
               and c._store.load("w16")["project_revision"] == live_rev)
        rep(w16, None,
            "W16) restoring over a LIVE id is a typed WRL_PROJECT_EXISTS "
            "(non-destructive: the live project is untouched; a new id restores)")

        # ---- W17/W18/W19 export modes over a committed workspace -----------
        c = _v2_cache(root)
        s = c.open("w17")
        _apply_text(s, EDITED_SRC)
        commit = {"commit_version": D.COMMIT_VERSION,
                  "draft_id": s.draft.draft_id,
                  "base_revision": s.draft.semantic_revision,
                  "expected_candidate_semantic_id": s.draft.candidate_semantic_id}
        s.commit(commit)
        saved17 = c.persist("w17")

        # a source world store carrying the historical (demo) world
        srcw = ST.WorldObjectStore(os.path.join(root, "srcw"))
        srcw.put(_lower(SB.DEMO_WORLD_SOURCE).sealed_artifact)

        full17 = B.build_bundle(saved17, world_store=srcw, export_mode="full")
        prev_actives = set(c17["previous_active"]
                           for c17 in saved17["commit_history"]
                           if c17["previous_active"])
        w17 = (saved17["active_world"]["semantic_id"] == edited_sem
               and edited_sem in full17["worlds"]
               and prev_actives == {demo_sem}
               and demo_sem in full17["worlds"]          # history carried
               and B.verify_bundle_v2_closure(full17) == edited_sem
               and full17["shallow_history"] is False)
        rep(w17, None,
            "W17) a FULL bundle carries every history-referenced world")

        # W18 -- same commit history, but the historical world is unresolvable.
        # Clear the (self-derivable) undo snapshots so `previous_active` is only
        # referenced by the commit log, then a full export with NO world store
        # cannot resolve it (never a silent downgrade).
        doc18 = copy.deepcopy(saved17)
        doc18["draft"]["undo_history"] = []
        doc18["draft"]["layout_undo_history"] = []
        doc18 = PR.canonicalize_project_v2(doc18)
        w18 = _raises(lambda: B.build_bundle(doc18, export_mode="full"),
                      B.WRL_BUNDLE_UNRESOLVED)
        rep(w18, None,
            "W18) a FULL bundle that cannot resolve a history world fails "
            "WRL_BUNDLE_UNRESOLVED (never a silent downgrade)")

        # W19 -- thin export is explicitly marked and drops history worlds.
        thin19 = B.build_bundle(saved17, export_mode="thin")
        w19 = (thin19["export_mode"] == "thin"
               and thin19["shallow_history"] is True
               and edited_sem in thin19["worlds"]
               and demo_sem not in thin19["worlds"]      # history dropped
               and B.verify_bundle_v2_closure(thin19) == edited_sem)
        rep(w19, None,
            "W19) a THIN bundle is explicitly marked (shallow_history) and drops "
            "history worlds while staying self-closed")

        # ---- W20 export -> import preserves an invalid, editable draft -----
        inv_doc = _v2_cache(root)._store.load("w2")     # the saved invalid draft
        bundle20 = B.build_bundle(inv_doc, export_mode="full")
        tp20, tw20, ts20 = _stores(root, "tgt20")
        imported20 = B.import_bundle(bundle20, tp20, tw20, ts20)
        s20 = PR.open_session_from_project_any(imported20)
        w20a = (s20.candidate_semantic_id is None
                and s20.candidate_error == err2)
        # the imported draft is still EDITABLE: a valid edit makes it valid again
        _apply_text(s20, EDITED_SRC)
        w20 = (w20a
               and s20.candidate_semantic_id == edited_sem
               and s20.candidate_error is None)
        rep(w20, None,
            "W20) export -> import preserves an INVALID, still-editable draft")

        # ---- W21 NATIVE: reopened/imported active world folds --------------
        sealed21 = tw20.get(demo_sem)                   # imported active world obj
        view21 = P.plan_view(P.artifact_to_compile_plan_v1(sealed21))
        fx21 = _lower(SB.DEMO_WORLD_SOURCE).as_fixture_for_test()
        scen21 = SC.demo_scenario(demo_sem)
        ifa21, scr21 = SC.scenario_to_script(scen21)
        ref21 = _fold_films(view21, O.norm, ifa21, scr21)
        orc21 = _fold_fixture(fx21, view21, O.norm, ifa21, scr21)
        n21r = (sealed21.semantic_id == demo_sem and ref21 == orc21)
        n21n = None
        if not SKIP_NATIVE:
            n21n = (_fold_films(view21, O.native, ifa21, scr21) == ref21)
        rep(n21r, n21n,
            "W21) NATIVE -- a reopened/imported active world folds "
            "ic_ref == ic32 == the independent Fixture oracle")

        # ---- W22 golden scenario presets are immutable ---------------------
        fresh22 = _v2_cache(root)._store.load("w1")     # any fresh V2 project
        got22 = PR._scenarios_of(fresh22)
        want22 = [PR.make_scenario_entry("golden", SC.demo_scenario(demo_sem)),
                  PR.make_scenario_entry("bench", SC.bench_scenario(demo_sem))]
        by_name = {s["name"]: s for s in got22}
        w22 = (set(by_name) == {"golden", "bench"}
               and all(by_name[e["name"]]["scenario_digest"] == e["scenario_digest"]
                       and by_name[e["name"]]["scenario"] == e["scenario"]
                       for e in want22))
        rep(w22, None,
            "W22) the golden scenario presets are immutable (a fresh project "
            "carries the exact canonical golden + bench presets)")

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
    print(f"\n[wrl-v0.5.1] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.5.1 makes the Library persist the COMPLETE authoring "
          "workspace: the exact draft (valid OR invalid, W1/W2), the syntax-error "
          "editor buffer (W3), the retained active-world source runnable beside "
          "an invalid draft (W4), the candidate id + diagnostics (W5), the "
          "semantic + layout revisions (W6), the idempotency ledger (W7), the "
          "paired undo stacks (W8/W9), the scenario selection + compatibility "
          "(W10/W11) and a display-name change (W12) all survive a restart. Fork "
          "Saved reproduces the SAVE and only the SAVE (W13/W14); trash is "
          "restorable + non-destructive (W15/W16); FULL export closes over "
          "history while THIN is explicitly shallow (W17/W18/W19); an invalid "
          "draft round-trips editable (W20); a reopened world stays natively "
          "runnable (W21); the golden presets are immutable (W22). This moves NO "
          "SemanticArtifactID and adds NO runtime construct -- ForgeProjectV2 is "
          "a project-doc version, pure workspace projection.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
