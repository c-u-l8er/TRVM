"""binding_run17.py -- v0.4-1 WorldDraftV1 draft store (Spinner Bench v0.4).

v0.4-0 drew the three-document boundary at the IDENTITY layer. v0.4-1 makes the
WORLD editable through a revisioned draft (`wrl_draft.WorldDraft`) WITHOUT ever
silently replacing the active sealed world. GPT-5.6's frozen v0.4 edit semantics
admit exactly ONE operation kind in this slice -- `SetObjectConfig` -- and require
an EXPLICIT, content-checked commit to promote a candidate. This battery proves
the five load-bearing rules of that contract plus two native gates (F1-F10):

  F1  Opening a draft over a sealed world starts at revision 0 with base == active
      == candidate == the world's EXACT SemanticArtifactID; the draft carries the
      world's 6 objects + 4 edges and a valid candidate; `to_document()` projects
      the frozen WorldDraftV1 public shape (no private history/ledger).
  F2  A `SetObjectConfig` edit (spinner rotor) MOVES the candidate id to exactly
      the independently-lowered edited world, advances the monotone revision to 1,
      and leaves `active_semantic_id` UNCHANGED -- editing never touches the
      committed world.
  F3  Idempotent `edit_id`: replaying the SAME edit_id returns the ORIGINAL result
      verbatim and does NOT advance the revision a second time (the idempotency
      check runs BEFORE the CAS, so a retry of an already-applied edit no-ops even
      though the revision has moved on).
  F4  Exact CAS: an edit whose `base_revision` != the current `semantic_revision`
      is refused `WRL_STALE_DRAFT` with NO auto-merge; a correctly-based edit
      applies.
  F5  Monotone undo: `undo` restores the working graph to its pre-edit bytes so
      the candidate returns to the EXACT prior SemanticArtifactID, but the
      revision still INCREMENTS (it never decrements); undo with nothing to undo
      raises WRL_BAD_DRAFT.
  F6  An invalid candidate stays EDITABLE but never commits: a `SetObjectConfig`
      that injects an unknown config key seals invalid (candidate id None + typed
      candidate_error), the revision still advances, the draft accepts further
      edits, `commit_draft` refuses it `WRL_INVALID_CANDIDATE`, and an `undo`
      repairs the candidate back to valid.
  F7  `validate_edit_v1` is a typed structural gate: unknown edit_version, a
      missing field, a wrong-draft edit, an unknown op kind, and a DEFERRED op
      (`AddObject`) all raise WRL_BAD_EDIT (the deferred-op error names the
      deferral honestly), as does a `SetObjectConfig` whose target is not in the
      draft.
  F8  Explicit, content-checked commit: `commit_draft` requires the CAS
      base_revision (WRL_STALE_DRAFT) AND an `expected_candidate_semantic_id`
      equal to the current candidate (WRL_COMMIT_MISMATCH) before it advances
      `active_semantic_id`; on success the active id becomes the candidate and the
      draft stays open for further edits atop the same revision.
  F9  Native golden gate: committing an identity-preserving NO-OP edit over the
      demo world leaves active == the demo SemanticArtifactID; the committed
      sealed artifact drives the plan/view fold and reproduces the historical
      hard-coded golden SCRIPT films byte-for-byte, with ic_ref == ic32 (native).
  F10 Native edited-world gate: committing a genuine rotor edit yields a NEW active
      SemanticArtifactID; a demo-shaped scenario bound to that new world folds
      through the plan/view path with ic_ref == ic32 -- a world BORN from the
      editing path is natively runnable, not just the frozen demo.

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import copy
import os
import sys
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
import wrl_draft as D
import spinner_bench as SB
from admit import film_hash_v7
from fixture import init_state_v6, state_to_film_args_v6

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"


def _fold_films(view, reducer, initial_faults, script):
    """Fold (initial_faults, script) through the compiled step over a plan VIEW
    -- the production _run_traj contract -- returning the per-epoch films. No
    Fixture is reconstructed."""
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


def _edit(edit_id, base_revision, target, static_config, draft_id="dr"):
    return {"edit_version": D.EDIT_VERSION, "edit_id": edit_id,
            "draft_id": draft_id, "base_revision": base_revision,
            "operation": {"kind": "SetObjectConfig", "target": target,
                          "static_config": static_config}}


def _commit(base_revision, expected, draft_id="dr"):
    return {"commit_version": D.COMMIT_VERSION, "draft_id": draft_id,
            "base_revision": base_revision,
            "expected_candidate_semantic_id": expected}


def _raises(code, thunk):
    try:
        thunk()
        return False
    except WC.WrlValidationError as e:
        return e.code == code
    except WC.WrlUnsupported as e:
        return getattr(e, "code", None) == code


def main():
    print("[BINDING wrl-v0.4-1] WorldDraftV1 draft store (F1-F10)")
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

    prog = SB._prog(SB.DEMO_WORLD_SOURCE)
    sem = prog.semantic_artifact_id

    def _spinner_cfg(draft):
        return copy.deepcopy(
            [o for o in draft.objects if o["object_id"] == "sp"][0]
            ["static_config"])

    # ---- F1 open a draft: base==active==candidate==exact SemanticArtifactID ---
    d = D.new_draft(prog, "dr")
    f1_ids = (d.base_semantic_id == sem and d.active_semantic_id == sem
              and d.candidate_semantic_id == sem and d.semantic_revision == 0
              and d.candidate_error is None)
    f1_shape = (len(d.objects) == 6 and len(d.edges) == 4)
    doc = d.to_document()
    f1_doc = (set(doc) == {"draft_version", "draft_id", "semantic_revision",
                           "base_semantic_id", "active_semantic_id",
                           "candidate_semantic_id", "candidate_valid",
                           "profile_id", "objects", "edges"}
              and doc["draft_version"] == D.DRAFT_VERSION
              and doc["candidate_valid"] is True
              and "history" not in doc and "applied" not in doc)
    rep(f1_ids and f1_shape and f1_doc, None,
        "F1) new_draft starts at revision 0 with base==active==candidate=="
        "exact SemanticArtifactID; 6 objects/4 edges; to_document() is the "
        "frozen WorldDraftV1 shape (no private history/ledger)")

    # ---- F2 SetObjectConfig moves the candidate; active is untouched ---------
    cfg = _spinner_cfg(d)
    cfg["rotor"] = [181, 0, 0, 182]
    D.apply_edit(d, _edit("e1", 0, "sp", cfg))
    # the candidate must equal the SAME world lowered independently
    indep = W.lower_graph(
        D._graph_from(copy.deepcopy(d.objects), copy.deepcopy(d.edges),
                      d.profile_id)).semantic_artifact_id
    cand_edited = d.candidate_semantic_id
    f2 = (cand_edited != sem and cand_edited == indep
          and d.semantic_revision == 1
          and d.active_semantic_id == sem)     # editing NEVER moves active
    rep(f2, None,
        "F2) SetObjectConfig moves the candidate to the independently-lowered "
        "edited world (revision->1); active_semantic_id stays the committed "
        "world -- editing never touches it")

    # ---- F3 idempotent edit_id: a retry no-ops (checked BEFORE the CAS) ------
    res_first = dict(d._applied["e1"])
    res_retry = D.apply_edit(d, _edit("e1", 0, "sp", cfg))   # SAME edit_id
    f3 = (res_retry == res_first and d.semantic_revision == 1
          and d.candidate_semantic_id == cand_edited)
    rep(f3, None,
        "F3) idempotent edit_id: replaying the same edit_id returns the "
        "original result and does not advance the revision a second time")

    # ---- F4 exact CAS: a stale base_revision is refused, no auto-merge -------
    cfg2 = _spinner_cfg(d)
    cfg2["rotor"] = [181, 0, 0, 183]
    f4_stale = _raises(D.WRL_STALE_DRAFT,
                       lambda: D.apply_edit(d, _edit("e2", 0, "sp", cfg2)))
    # a correctly-based edit (base_revision == current 1) applies
    D.apply_edit(d, _edit("e2", 1, "sp", cfg2))
    f4_ok = (d.semantic_revision == 2)
    rep(f4_stale and f4_ok, None,
        "F4) exact CAS: an edit based on a stale revision -> WRL_STALE_DRAFT "
        "(no auto-merge); a correctly-based edit applies")

    # ---- F5 monotone undo restores the EXACT prior id; revision increments ---
    before_rev = d.semantic_revision                    # 2
    before_cand = d.candidate_semantic_id               # the e2 world
    D.undo(d)                                            # undo e2 -> back to e1
    f5_restore = (d.candidate_semantic_id == cand_edited     # e1 world exactly
                  and d.candidate_semantic_id != before_cand)
    f5_monotone = (d.semantic_revision == before_rev + 1)    # 3, never decrements
    # a second undo returns to the original DEMO world id exactly
    D.undo(d)
    f5_orig = (d.candidate_semantic_id == sem and d.semantic_revision == 4)
    # nothing left to undo now that we are back to the base graph? history still
    # holds the very first snapshot; drain it, then undo must raise.
    while d._history:
        D.undo(d)
    f5_empty = _raises(D.WRL_BAD_DRAFT, lambda: D.undo(d))
    rep(f5_restore and f5_monotone and f5_orig and f5_empty, None,
        "F5) monotone undo restores the exact prior SemanticArtifactID while "
        "the revision increments (never decrements); undo with empty history "
        "-> WRL_BAD_DRAFT")

    # ---- F6 invalid candidate stays editable but never commits ---------------
    d6 = D.new_draft(prog, "dr")
    bad_cfg = _spinner_cfg(d6)
    bad_cfg["bogus_key"] = 1
    D.apply_edit(d6, _edit("bad", 0, "sp", bad_cfg))
    f6_invalid = (d6.candidate_semantic_id is None
                  and d6.candidate_error is not None
                  and d6.semantic_revision == 1)         # revision still advanced
    # the draft is STILL editable (a further edit applies atop the invalid one)
    ok_cfg = _spinner_cfg(d6)                             # unchanged-config copy
    # NOTE _spinner_cfg reads the CURRENT (invalid) object, which carries the
    # bogus key, so strip it to author a repairing edit.
    ok_cfg.pop("bogus_key", None)
    D.apply_edit(d6, _edit("fix", 1, "sp", ok_cfg))
    f6_editable = (d6.candidate_semantic_id == sem
                   and d6.candidate_error is None and d6.semantic_revision == 2)
    # re-break it, then confirm commit refuses an invalid candidate
    D.apply_edit(d6, _edit("bad2", 2, "sp", bad_cfg))
    f6_commit = _raises(D.WRL_INVALID_CANDIDATE,
                        lambda: D.commit_draft(
                            d6, _commit(d6.semantic_revision, "anything")))
    # and an undo repairs the candidate back to valid
    D.undo(d6)
    f6_repaired = (d6.candidate_error is None and d6.candidate_semantic_id == sem)
    rep(f6_invalid and f6_editable and f6_commit and f6_repaired, None,
        "F6) an invalid candidate stays editable (revision advances, further "
        "edits apply, undo repairs) but commit refuses it WRL_INVALID_CANDIDATE")

    # ---- F7 validate_edit_v1 typed structural gate ---------------------------
    good = _edit("g", 0, "sp", _spinner_cfg(d6))
    f7_ver = _raises(D.WRL_BAD_EDIT,
                     lambda: D.validate_edit_v1({**good, "edit_version": "x"}))
    f7_miss = _raises(D.WRL_BAD_EDIT,
                      lambda: D.validate_edit_v1(
                          {k: v for k, v in good.items() if k != "operation"}))
    d7 = D.new_draft(prog, "dr")
    f7_draft = _raises(D.WRL_BAD_EDIT,
                       lambda: D.apply_edit(d7, {**good, "draft_id": "other"}))
    f7_unknown = _raises(D.WRL_BAD_EDIT, lambda: D.validate_edit_v1(
        {**good, "operation": {"kind": "Nope"}}))
    f7_deferred = _raises(D.WRL_BAD_EDIT, lambda: D.validate_edit_v1(
        {**good, "operation": {"kind": "AddObject"}}))
    f7_target = _raises(D.WRL_BAD_EDIT, lambda: D.apply_edit(
        d7, _edit("t", 0, "no_such_object", {})))
    rep(f7_ver and f7_miss and f7_draft and f7_unknown and f7_deferred
        and f7_target, None,
        "F7) validate_edit_v1 rejects unknown version / missing field / wrong "
        "draft / unknown op / DEFERRED op (AddObject) / missing target -- all "
        "typed WRL_BAD_EDIT")

    # ---- F8 explicit, content-checked commit ---------------------------------
    d8 = D.new_draft(prog, "dr")
    c8 = _spinner_cfg(d8)
    c8["rotor"] = [181, 0, 0, 190]
    D.apply_edit(d8, _edit("e", 0, "sp", c8))
    cand8 = d8.candidate_semantic_id
    rev8 = d8.semantic_revision
    # (a) content mismatch is refused
    f8_content = _raises(D.WRL_COMMIT_MISMATCH,
                         lambda: D.commit_draft(d8, _commit(rev8, "sem-wrong")))
    # (b) a stale base is refused
    f8_stale = _raises(D.WRL_STALE_DRAFT,
                       lambda: D.commit_draft(d8, _commit(rev8 - 1, cand8)))
    # (c) the correct commit advances active to the candidate
    res8 = D.commit_draft(d8, _commit(rev8, cand8))
    f8_ok = (d8.active_semantic_id == cand8
             and res8["active_semantic_id"] == cand8
             and isinstance(res8["sealed_artifact"], WC.SealedArtifact)
             and res8["sealed_artifact"].semantic_id == cand8)
    # (d) the draft stays open: a further edit applies atop the same revision
    c8b = _spinner_cfg(d8)
    c8b["rotor"] = [181, 0, 0, 191]
    D.apply_edit(d8, _edit("e2", d8.semantic_revision, "sp", c8b))
    f8_open = (d8.candidate_semantic_id != cand8
               and d8.active_semantic_id == cand8)   # active held until next commit
    rep(f8_content and f8_stale and f8_ok and f8_open, None,
        "F8) commit requires CAS + expected_candidate match (WRL_COMMIT_MISMATCH"
        " / WRL_STALE_DRAFT) then advances active to the candidate; the draft "
        "stays open for further edits")

    # ---- F9 native golden gate: committed NO-OP reproduces the golden films ---
    d9 = D.new_draft(prog, "dr")
    noop = _spinner_cfg(d9)                        # identical config = no-op edit
    D.apply_edit(d9, _edit("noop", 0, "sp", noop))
    f9_noop = (d9.candidate_semantic_id == sem)
    res9 = D.commit_draft(d9, _commit(d9.semantic_revision, sem))
    sealed9 = res9["sealed_artifact"]
    view9 = P.plan_view(P.artifact_to_compile_plan_v1(sealed9))
    demo9 = SC.demo_scenario(sealed9.semantic_id)
    ifa9, scr9 = SC.scenario_to_script(demo9)
    ref_films = _fold_films(view9, O.norm, ("ob",), SB.SCRIPT)
    got9 = _fold_films(view9, O.norm, ifa9, scr9)
    f9r = (f9_noop and d9.active_semantic_id == sem and got9 == ref_films)
    f9n = None
    if not SKIP_NATIVE:
        f9n = (_fold_films(view9, O.native, ifa9, scr9) == got9)
    rep(f9r, f9n,
        "F9) committing an identity-preserving no-op leaves active == the demo "
        "SemanticArtifactID; the committed sealed artifact drives the plan/view "
        "fold and reproduces the golden SCRIPT films, ic_ref == ic32")

    # ---- F10 native edited-world gate: a world BORN from editing is runnable --
    d10 = D.new_draft(prog, "dr")
    c10 = _spinner_cfg(d10)
    c10["rotor"] = [181, 0, 0, 182]
    D.apply_edit(d10, _edit("e", 0, "sp", c10))
    cand10 = d10.candidate_semantic_id
    res10 = D.commit_draft(d10, _commit(d10.semantic_revision, cand10))
    sealed10 = res10["sealed_artifact"]
    f10_new = (sealed10.semantic_id == cand10 and cand10 != sem)
    view10 = P.plan_view(P.artifact_to_compile_plan_v1(sealed10))
    demo10 = SC.demo_scenario(sealed10.semantic_id)
    ifa10, scr10 = SC.scenario_to_script(demo10)
    got10 = _fold_films(view10, O.norm, ifa10, scr10)
    f10r = f10_new
    f10n = None
    if not SKIP_NATIVE:
        f10n = (_fold_films(view10, O.native, ifa10, scr10) == got10)
    rep(f10r, f10n,
        "F10) committing a genuine rotor edit yields a NEW active "
        "SemanticArtifactID; a scenario bound to that world folds through the "
        "plan/view path with ic_ref == ic32 (a world born from editing is "
        "natively runnable)")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.4-1] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.4-1 makes the WORLD editable through a revisioned "
          "WorldDraftV1 without ever silently replacing the active sealed "
          "world: exact CAS + idempotent edit_id, every edit re-seals a typed "
          "candidate, an explicit content-checked commit is the ONLY promotion, "
          "and undo is monotone. A committed world -- no-op OR edited -- folds "
          "through the unchanged plan/view path at ic_ref == ic32. No new "
          "runtime construct was introduced; the draft store is pure data over "
          "the existing identity spine.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
