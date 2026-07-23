"""binding_run30.py -- v0.6-0 RecoveryJournalV1 crash-recovery closure (X1-X18).

v0.5.1 (binding_run29) made the Library persist the COMPLETE authoring workspace
via an explicit Save (ForgeProjectV2). v0.6-0 adds a SEPARATE, atomic,
NON-AUTHORITATIVE crash-recovery journal (RecoveryJournalV1) that checkpoints the
UNSAVED workspace WITHOUT modifying ForgeProjectV2 or weakening Save. A journal is
an emergency overlay stored in its own `.recovery/` root (a SIBLING of `projects/`,
never nested in a bundle); it reuses the exact `wrl_converge.session_state`
serialization, never advances `project_revision`, never moves a semantic identity,
never activates a candidate, and is NEVER auto-applied on reopen.

Battery X1-X18 (the v0.6-0 acceptance gate). A fresh ProjectSessionCache over the
same store root is a RESTART: it finds the on-disk journal but reconstructs the
SAVED workspace, offering (not applying) recovery.

  X1  an unsaved VALID draft creates a journal (status -> recovery_available);
  X2  an unsaved INVALID draft creates a journal (inspect: draft_valid False, the
      typed candidate_error preserved);
  X3  a SYNTAX-ERROR editor buffer is captured in the journal's session_state;
  X4  a recovery write does NOT advance the saved project_revision;
  X5  a recovery write does NOT move the active semantic id (journal + saved
      project both keep the committed active world);
  X6  a RESTART detects the journal but does NOT auto-apply it (the reopened
      session reflects the SAVE; recovery is only OFFERED);
  X7  Recover restores the EXACT workspace as an unsaved, dirty session
      (session_state == the journal's session_state; revision NOT advanced);
  X8  Recover does NOT activate the candidate (active stays the committed world;
      the uncommitted candidate simply returns);
  X9  Discard removes the journal and leaves the SAVED workspace intact;
  X10 Save clears the journal ONLY after a durable project write;
  X11 Commit clears the journal ONLY after a durable project write;
  X12 a FAILED Save (stale CAS) PRESERVES the journal (no torn recovery);
  X13 a journal whose base != the saved revision is typed WRL_RECOVERY_STALE
      (Recover refuses it; status -> recovery_stale);
  X14 a stale journal opens as a BRAND-NEW recovered copy (no auto-merge; the
      original journal is consumed, the diverged saved project untouched);
  X15 Fork Saved EXCLUDES the journal (the fork reflects the SAVE, and the source
      journal is untouched -- forking is not recovery);
  X16 normal FULL and THIN exports EXCLUDE the journal (a bundle carries no
      recovery data; the on-disk journal is not consumed by export);
  X17 the persisted indicator state tracks the ACTUAL on-disk state across
      saved -> recovery_available -> saved;
  X18 NATIVE -- a RECOVERED session's active sealed world still folds
      ic_ref == ic32 == the independent Fixture oracle.

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


def _commit(sess):
    sess.commit({"commit_version": D.COMMIT_VERSION,
                 "draft_id": sess.draft.draft_id,
                 "base_revision": sess.draft.semantic_revision,
                 "expected_candidate_semantic_id":
                     sess.draft.candidate_semantic_id})


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
    print("[BINDING wrl-v0.6-0] recovery journal closure (X1-X18)")
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

    root = tempfile.mkdtemp(prefix="wrl_recovery_")
    try:
        demo_sem = SB.DEMO_WORLD_SEMANTIC_ID
        edited_sem = _lower(EDITED_SRC).semantic_artifact_id

        # ---- X1 unsaved VALID draft creates a journal ----------------------
        c = _v2_cache(root)
        s = c.open("x1")
        c.persist("x1")                    # a clean SAVED baseline
        _apply_text(s, EDITED_SRC)         # dirty (valid, uncommitted)
        c.checkpoint("x1", dirty_reasons=["text"])
        st1 = c.recovery_status("x1")
        x1 = (c._recovery.exists("x1")
              and st1["state"] == "recovery_available"
              and st1["dirty_reasons"] == ["text"])
        rep(x1, None,
            "X1) an unsaved VALID draft creates a recovery journal "
            "(status -> recovery_available)")

        # ---- X2 unsaved INVALID draft creates a journal --------------------
        c = _v2_cache(root)
        s = c.open("x2")
        c.persist("x2")
        _apply_text(s, INVALID_SRC)
        err2 = s.draft.candidate_error
        c.checkpoint("x2", dirty_reasons=["text"])
        insp2 = c.inspect_recovery("x2")
        x2 = (c._recovery.exists("x2")
              and insp2["draft_valid"] is False
              and insp2["candidate_error"] == err2
              and err2 and err2.startswith("WRL_CONTROLLER_CONFLICT"))
        rep(x2, None,
            "X2) an unsaved INVALID draft creates a journal (inspect: draft_valid "
            "False; the typed candidate_error preserved)")

        # ---- X3 syntax-error editor buffer captured ------------------------
        c = _v2_cache(root)
        s = c.open("x3")
        c.persist("x3")
        _apply_text(s, SYNTAX_BAD)
        j3 = c.checkpoint("x3", dirty_reasons=["text"])
        ss3 = j3["session_state"]
        x3 = (ss3["source_document"]["raw_source"] == SYNTAX_BAD
              and ss3["source_document"]["parse_status"] == "syntax_error"
              # the underlying draft is untouched by a syntax-error buffer
              and ss3["draft"]["candidate_semantic_id"] == demo_sem)
        rep(x3, None,
            "X3) a SYNTAX-ERROR editor buffer is captured in the journal's "
            "session_state (the draft itself stays untouched)")

        # ---- X4 recovery write does NOT advance project_revision -----------
        c = _v2_cache(root)
        s = c.open("x4")
        c.persist("x4")
        rev_before = PR._revision_of(c._store.load("x4"))
        _apply_text(s, EDITED_SRC)
        c.checkpoint("x4", dirty_reasons=["text"])
        rev_after = PR._revision_of(c._store.load("x4"))
        x4 = (rev_before == rev_after == 1)
        rep(x4, None,
            "X4) a recovery write does NOT advance the saved project_revision")

        # ---- X5 recovery write does NOT move the active semantic id --------
        j5 = c.checkpoint("x4", dirty_reasons=["text"])
        saved5 = c._store.load("x4")
        x5 = (j5["session_state"]["draft"]["active_semantic_id"] == demo_sem
              and saved5["active_world"]["semantic_id"] == demo_sem)
        rep(x5, None,
            "X5) a recovery write does NOT move the active semantic id (journal "
            "+ saved project both keep the committed active world)")

        # ---- X6 RESTART detects but does NOT auto-apply --------------------
        c = _v2_cache(root)
        s = c.open("x6")
        c.persist("x6")
        _apply_text(s, EDITED_SRC)
        c.checkpoint("x6", dirty_reasons=["text"])
        # a fresh cache over the same root == a restart
        c2 = _v2_cache(root)
        s6 = c2.open("x6")
        st6 = c2.recovery_status("x6")
        x6 = (st6["state"] == "recovery_available"
              # the reopened session reflects the SAVE, NOT the journal
              and s6.candidate_semantic_id == demo_sem
              and s6.draft.active_semantic_id == demo_sem)
        rep(x6, None,
            "X6) a RESTART detects the journal but does NOT auto-apply it (the "
            "reopened session reflects the SAVE; recovery is only OFFERED)")

        # ---- X7 Recover restores the EXACT workspace as dirty --------------
        j6 = c2._recovery.load("x6")
        rev_pre_recover = c2._revisions["x6"]
        rec6, jj6 = c2.recover("x6")
        x7 = (CG.session_state(rec6) == j6["session_state"]
              and c2._revisions["x6"] == rev_pre_recover        # NOT advanced
              and c2._store.load("x6")["project_revision"] == rev_pre_recover)
        rep(x7, None,
            "X7) Recover restores the EXACT workspace as an unsaved dirty session "
            "(session_state == journal; revision NOT advanced)")

        # ---- X8 Recover does NOT activate the candidate --------------------
        x8 = (rec6.draft.active_semantic_id == demo_sem       # active untouched
              and rec6.candidate_semantic_id == edited_sem    # candidate returns
              and rec6.candidate_error is None)
        rep(x8, None,
            "X8) Recover does NOT activate the candidate (active stays the "
            "committed world; the uncommitted candidate simply returns)")

        # ---- X9 Discard removes journal + leaves SAVED intact --------------
        c = _v2_cache(root)
        s = c.open("x9")
        c.persist("x9")
        _apply_text(s, EDITED_SRC)
        c.checkpoint("x9", dirty_reasons=["text"])
        c.discard_recovery("x9")
        st9 = c.recovery_status("x9")
        saved9 = c._store.load("x9")
        x9 = (not c._recovery.exists("x9")
              and st9["state"] == "saved"
              and saved9["active_world"]["semantic_id"] == demo_sem
              and saved9["project_revision"] == 1)
        rep(x9, None,
            "X9) Discard removes the journal and leaves the SAVED workspace intact")

        # ---- X10 Save clears the journal ONLY after a durable write --------
        c = _v2_cache(root)
        s = c.open("x10")
        c.persist("x10")
        _apply_text(s, EDITED_SRC)
        c.checkpoint("x10", dirty_reasons=["text"])
        had10 = c._recovery.exists("x10")
        c.persist("x10")                   # SAVE
        x10 = (had10 and not c._recovery.exists("x10")
               and c.recovery_status("x10")["state"] == "saved")
        rep(x10, None,
            "X10) Save clears the journal ONLY after a durable project write")

        # ---- X11 Commit clears the journal ONLY after a durable write ------
        c = _v2_cache(root)
        s = c.open("x11")
        c.persist("x11")
        _apply_text(s, EDITED_SRC)
        c.checkpoint("x11", dirty_reasons=["text"])
        had11 = c._recovery.exists("x11")
        _commit(s)                         # promote candidate -> active
        saved11 = c.persist("x11")         # Commit also Saves durably
        x11 = (had11 and not c._recovery.exists("x11")
               and saved11["active_world"]["semantic_id"] == edited_sem)
        rep(x11, None,
            "X11) Commit clears the journal ONLY after a durable project write")

        # ---- X12 a FAILED Save PRESERVES the journal -----------------------
        c = _v2_cache(root)
        s = c.open("x12")
        c.persist("x12")
        _apply_text(s, EDITED_SRC)
        c.checkpoint("x12", dirty_reasons=["text"])
        # force a stale CAS: bump the on-disk revision out of band
        c._store.rename("x12", "bumped out of band", 1)
        # the cache still believes it is at rev 1 -> Save must fail STALE
        failed12 = _raises(lambda: c.persist("x12"), PR.WRL_PROJECT_STALE)
        x12 = (failed12 and c._recovery.exists("x12"))
        rep(x12, None,
            "X12) a FAILED Save (stale CAS) PRESERVES the journal (no torn "
            "recovery)")

        # ---- X13 base != saved revision is typed WRL_RECOVERY_STALE --------
        c = _v2_cache(root)
        s = c.open("x13")
        c.persist("x13")                   # rev 1, journal base will be 1
        _apply_text(s, EDITED_SRC)
        c.checkpoint("x13", dirty_reasons=["text"])
        # bump the SAVED revision out of band so the journal's base diverges
        c._store.rename("x13", "diverged", 1)
        c13 = _v2_cache(root)              # restart
        c13.open("x13")
        st13 = c13.recovery_status("x13")
        stale13 = _raises(lambda: c13.recover("x13"), PR.WRL_RECOVERY_STALE)
        x13 = (st13["state"] == "recovery_stale" and st13["stale"] is True
               and stale13)
        rep(x13, None,
            "X13) a journal whose base != the saved revision is typed "
            "WRL_RECOVERY_STALE (Recover refuses it; status -> recovery_stale)")

        # ---- X14 a stale journal opens as a BRAND-NEW recovered copy -------
        copy14 = c13.open_as_recovered_copy("x13", "x13copy")
        saved_orig14 = c13._store.load("x13")
        x14 = (copy14.candidate_semantic_id == edited_sem     # the recovered work
               and c13._store.exists("x13copy")
               and not c13._recovery.exists("x13")            # journal consumed
               and saved_orig14["name"] == "diverged"         # original untouched
               and saved_orig14["active_world"]["semantic_id"] == demo_sem)
        rep(x14, None,
            "X14) a stale journal opens as a BRAND-NEW recovered copy (no "
            "auto-merge; original journal consumed, diverged project untouched)")

        # ---- X15 Fork Saved EXCLUDES the journal ---------------------------
        c = _v2_cache(root)
        s = c.open("x15")
        c.persist("x15")
        _apply_text(s, EDITED_SRC)         # dirty, uncommitted
        c.checkpoint("x15", dirty_reasons=["text"])
        fork15 = c.fork("x15", "x15fork")
        x15 = (fork15.candidate_semantic_id == demo_sem        # reflects the SAVE
               and not c._recovery.exists("x15fork")           # no forked journal
               and c._recovery.exists("x15"))                  # source untouched
        rep(x15, None,
            "X15) Fork Saved EXCLUDES the journal (the fork reflects the SAVE; the "
            "source journal is untouched -- forking is not recovery)")

        # ---- X16 FULL + THIN exports EXCLUDE the journal -------------------
        c = _v2_cache(root)
        s = c.open("x16")
        _apply_text(s, EDITED_SRC)
        _commit(s)
        saved16 = c.persist("x16")         # a committed, saved workspace
        _apply_text(s, INVALID_SRC)        # a new dirty overlay
        c.checkpoint("x16", dirty_reasons=["text"])
        srcw = ST.WorldObjectStore(os.path.join(root, "srcw16"))
        srcw.put(_lower(SB.DEMO_WORLD_SOURCE).sealed_artifact)
        full16 = B.build_bundle(saved16, world_store=srcw, export_mode="full")
        thin16 = B.build_bundle(saved16, export_mode="thin")
        x16 = ("recovery" not in full16 and "recovery_version" not in full16
               and "recovery" not in thin16 and "recovery_version" not in thin16
               and c._recovery.exists("x16"))                  # export didn't eat it
        rep(x16, None,
            "X16) normal FULL and THIN exports EXCLUDE the journal (a bundle "
            "carries no recovery data; the on-disk journal is not consumed)")

        # ---- X17 persisted indicator tracks actual on-disk state -----------
        c = _v2_cache(root)
        s = c.open("x17")
        c.persist("x17")
        st17a = c.recovery_status("x17")["state"]              # saved
        _apply_text(s, EDITED_SRC)
        c.checkpoint("x17", dirty_reasons=["text"])
        st17b = c.recovery_status("x17")["state"]              # recovery_available
        c.persist("x17")                                       # Save
        st17c = c.recovery_status("x17")["state"]              # saved again
        x17 = (st17a == "saved" and st17b == "recovery_available"
               and st17c == "saved")
        rep(x17, None,
            "X17) the persisted indicator state tracks the ACTUAL on-disk state "
            "across saved -> recovery_available -> saved")

        # ---- X18 NATIVE: a RECOVERED session's active world folds ----------
        c = _v2_cache(root)
        s = c.open("x18")
        c.persist("x18")                   # active = demo, committed + saved
        _apply_text(s, EDITED_SRC)         # dirty candidate (uncommitted)
        c.checkpoint("x18", dirty_reasons=["text"])
        c2 = _v2_cache(root)               # restart
        c2.open("x18")
        rec18, _ = c2.recover("x18")
        # the recovered ACTIVE sealed world (demo) must still be runnable
        lp18 = _lower(rec18.active_world_source)
        sealed18 = lp18.sealed_artifact
        view18 = P.plan_view(P.artifact_to_compile_plan_v1(sealed18))
        fx18 = lp18.as_fixture_for_test()
        scen18 = SC.demo_scenario(demo_sem)
        ifa18, scr18 = SC.scenario_to_script(scen18)
        ref18 = _fold_films(view18, O.norm, ifa18, scr18)
        orc18 = _fold_fixture(fx18, view18, O.norm, ifa18, scr18)
        n18r = (sealed18.semantic_id == demo_sem
                and rec18.candidate_semantic_id == edited_sem   # still dirty
                and ref18 == orc18)
        n18n = None
        if not SKIP_NATIVE:
            n18n = (_fold_films(view18, O.native, ifa18, scr18) == ref18)
        rep(n18r, n18n,
            "X18) NATIVE -- a RECOVERED session's active sealed world folds "
            "ic_ref == ic32 == the independent Fixture oracle")

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
    print(f"\n[wrl-v0.6-0] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.6-0 adds RecoveryJournalV1 -- a SEPARATE, atomic, "
          "non-authoritative crash-recovery overlay in its own .recovery/ root. "
          "It captures the exact unsaved workspace (valid X1, invalid X2, "
          "syntax-error buffer X3) WITHOUT advancing project_revision (X4) or "
          "moving any active id (X5). A restart OFFERS but never auto-applies it "
          "(X6); Recover restores the exact dirty workspace (X7) without "
          "activating the candidate (X8); Discard drops it cleanly (X9). Save "
          "(X10) and Commit (X11) clear it only after a durable write, while a "
          "failed Save preserves it (X12). A diverged base is typed "
          "WRL_RECOVERY_STALE (X13) and opens as a fresh copy, never an "
          "auto-merge (X14). Fork Saved (X15) and normal FULL/THIN export (X16) "
          "both exclude the journal; the indicator tracks the real on-disk state "
          "(X17); and a recovered active world stays natively runnable (X18). "
          "This moves NO SemanticArtifactID, adds NO runtime construct, and "
          "leaves ForgeProjectV2 + explicit Save unchanged.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
