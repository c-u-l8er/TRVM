"""binding_run33.py -- v0.6-3 migration/packaging: forward-only, identity-preserving
ForgeProjectV1 -> ForgeProjectV2 project-document migration (AA1-AA10).

A V2 cache can READ a legacy ForgeProjectV1 project (opening is version-dispatched),
but a SAVE re-serializes the session as V2 and the store REFUSES to write a V2
document over an on-disk V1 one (a project is never silently up/down-graded on save).
So without a migration a pre-existing V1 project is effectively READ-ONLY under the
current (V2) package. v0.6-3 closes that gap with a FORWARD-ONLY (V1 -> V2, never the
reverse), IDENTITY-PRESERVING migration: it re-opens the V1 project through the SAME
validated seam a reopen uses (`open_session_from_project`, which re-lowers the
world_source and asserts it reproduces `active_world_semantic_id`) and re-serializes
that exact session as V2 (`session_to_project_v2`). It moves NO SemanticArtifactID and
preserves the project_revision (a representation upgrade, not a workspace edit).

Battery AA1-AA10 (the v0.6-3 acceptance gate):

  AA1  the pure `migrate_project_v1_to_v2` maps a V1 demo doc -> a valid V2 doc
       (validate_project_v2 passes) with the SAME project_id / name / revision;
  AA2  IDENTITY -- the V2 `active_world.semantic_id` is byte-for-byte the V1
       `active_world_semantic_id`, and its canonical_source re-lowers to it (a full
       V2 reopen via open_session_from_project_v2 succeeds);
  AA3  the V1 `scenarios` become the V2 `scenario_documents` (name+digest preserved);
  AA4  a non-trivial commit log survives verbatim (V1 `commits` -> V2 `commit_history`);
  AA5  FORWARD-ONLY -- the pure fn AND store.migrate reject a non-V1 input
       (already-V2 doc, non-dict, bad version) as a typed WRL_PROJECT_MIGRATION;
  AA6  store.migrate is an ATOMIC in-place rewrite at the SAME revision -- the
       on-disk project is now V2 (project_version(pid) == v2) at the same rev;
  AA7  the READ-ONLY GAP IS CLOSED -- a V2 cache over the same root cannot Save a V1
       project (WRL_BAD_PROJECT) BEFORE migration, and Saves normally AFTER;
  AA8  IDENTITY INVARIANT -- migration moves NO project revision and leaves the demo
       world's SemanticArtifactID + per-epoch films byte-for-byte unchanged;
  AA9  the migrated V2 project re-opens to a live session whose committed world is the
       SAME demo world (identity round-trips through the on-disk migration);
  AA10 NATIVE -- the migrated active world folds ic_ref == ic32 == the independent
       Fixture oracle.

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import os
import sys
import copy
import shutil
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import wrl_canonical as WC
import wrl_project as PJ
import spinner_bench as SB

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

DEMO = SB.DEMO_WORLD_SOURCE
DEMO_SEM = SB.DEMO_WORLD_SEMANTIC_ID


def _raises(fn, code):
    try:
        fn()
    except WC.WrlUnsupported as ex:
        return getattr(ex, "code", None) == code
    except Exception:
        return False
    return False


def _v1_store():
    """A throwaway ForgeProjectStore + a V1 ProjectSessionCache over a temp root
    with one real V1 project ("alpha") seeded with the demo world. Returns (tmp,
    store, v1_cache)."""
    tmp = tempfile.mkdtemp(prefix="wrl-run33-")
    store = PJ.ForgeProjectStore(tmp)
    v1 = PJ.ProjectSessionCache(
        store, DEMO, scenarios_for=SB._default_scenarios,
        project_version=PJ.PROJECT_VERSION)
    v1.create_new("alpha", "Alpha")
    return tmp, store, v1


def main():
    print("[BINDING wrl-v0.6-3] migration/packaging -- V1->V2 project doc (AA1-AA10)")
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

    C = PJ.WRL_PROJECT_MIGRATION

    tmp, store, v1 = _v1_store()
    try:
        v1_doc = store.load("alpha")

        # ---- AA1 pure migration yields a valid V2 doc, same id/name/revision ----
        v2_doc = PJ.migrate_project_v1_to_v2(v1_doc)
        PJ.validate_project_v2(v2_doc)              # raises typed on any violation
        aa1 = (v2_doc["project_version"] == PJ.PROJECT_V2_VERSION
               and v2_doc["project_id"] == v1_doc["project_id"] == "alpha"
               and v2_doc["name"] == v1_doc["name"] == "Alpha"
               and v2_doc["project_revision"] == v1_doc["revision"])
        rep(aa1, None, "AA1) migrate_project_v1_to_v2 -> valid V2 doc with same "
            "project_id / name / revision")

        # ---- AA2 IDENTITY: active world id preserved + canonical_source closes ---
        reopened = PJ.open_session_from_project_v2(v2_doc)   # closure re-lower
        aa2 = (v2_doc["active_world"]["semantic_id"]
               == v1_doc["active_world_semantic_id"] == DEMO_SEM
               and reopened.draft.active_semantic_id == DEMO_SEM)
        rep(aa2, None, "AA2) IDENTITY -- V2 active_world.semantic_id == the V1 "
            "active_world_semantic_id (== demo) and its source re-lowers to it")

        # ---- AA3 scenarios -> scenario_documents (name + digest preserved) -------
        v1_scen = [(s["name"], s["scenario_digest"]) for s in v1_doc["scenarios"]]
        v2_scen = [(s["name"], s["scenario_digest"])
                   for s in v2_doc["scenario_documents"]]
        aa3 = v1_scen and v1_scen == v2_scen
        rep(aa3, None, "AA3) V1 scenarios become V2 scenario_documents "
            "(name + digest preserved)")

        # ---- AA4 a non-trivial commit log survives verbatim ---------------------
        commit = {"index": 0, "semantic_revision": 1,
                  "previous_active": DEMO_SEM, "active_semantic_id": DEMO_SEM}
        d = dict(v1_doc)
        d["commits"] = [commit]
        store.save(d, 0)                            # rev 0 -> 1, still V1 + a commit
        v1_c = store.load("alpha")
        v2_c = PJ.migrate_project_v1_to_v2(v1_c)
        aa4 = (v1_c["commits"] == v2_c["commit_history"]
               and len(v2_c["commit_history"]) == 1
               and v2_c["commit_history"][0]["active_semantic_id"] == DEMO_SEM
               and v2_c["project_revision"] == 1)   # revision preserved through it
        rep(aa4, None, "AA4) a non-trivial commit log survives verbatim "
            "(V1 commits -> V2 commit_history) at the same revision")

        # ---- AA5 FORWARD-ONLY: the pure fn rejects a non-V1 input (typed) -------
        # (the store.migrate already-V2 / absent paths are checked in AA6; here we
        # only exercise the pure function so `alpha` on disk stays V1 for AA6.)
        aa5 = (_raises(lambda: PJ.migrate_project_v1_to_v2(v2_c), C)      # already V2
               and _raises(lambda: PJ.migrate_project_v1_to_v2(["x"]), C)  # non-dict
               and _raises(lambda: PJ.migrate_project_v1_to_v2(
                   dict(v1_c, project_version="forge.project.v9")), C))    # bad ver
        rep(aa5, None, "AA5) FORWARD-ONLY -- the pure fn rejects a non-V1 input "
            "(already-V2 / non-dict / bad version) as typed WRL_PROJECT_MIGRATION")

        # ---- AA6 store.migrate is an ATOMIC in-place rewrite at the same rev -----
        rev_before = PJ._revision_of(store.load("alpha"))       # == 1 (from AA4)
        migrated = store.migrate("alpha")
        on_disk = store.load("alpha")
        aa6 = (store.project_version("alpha") == PJ.PROJECT_V2_VERSION
               and PJ._revision_of(on_disk) == rev_before        # rev preserved
               and on_disk == migrated
               and _raises(lambda: store.migrate("alpha"), C)    # already V2 now
               and _raises(lambda: store.migrate("ghost"),
                           PJ.WRL_PROJECT_MISSING))
        rep(aa6, None, "AA6) store.migrate is an atomic in-place rewrite -- on-disk "
            "project is now V2 at the SAME revision; re-migrate -> typed")

        # ---- AA7 the READ-ONLY GAP is closed via a V2 cache ---------------------
        tmp2, store2, _v1b = _v1_store()             # fresh temp root, V1 "alpha"
        try:
            v2cache = PJ.ProjectSessionCache(
                store2, DEMO, scenarios_for=SB._default_scenarios,
                project_version=PJ.PROJECT_V2_VERSION)
            v2cache.open("alpha")                    # a V2 cache READS the V1 project
            before = _raises(lambda: v2cache.persist("alpha"), PJ.WRL_BAD_PROJECT)
            v2cache.migrate("alpha")                 # forward migration
            saved = v2cache.persist("alpha")         # now Save works
            after_ok = (PJ.project_version_of(saved) == PJ.PROJECT_V2_VERSION)
            aa7 = before and after_ok
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)
        rep(aa7, None, "AA7) READ-ONLY GAP closed -- a V2 cache cannot Save a V1 "
            "project (WRL_BAD_PROJECT) before migration, and Saves after")

        # ---- AA8 IDENTITY INVARIANT: migration moves no identity / films --------
        base = SB._run_payload(DEMO)
        mig_src = migrated["active_world"]["canonical_source"]
        after = SB._run_payload(mig_src)
        aa8 = (base["ok"] and after["ok"]
               and base["semantic_artifact_id"] == DEMO_SEM
               and after["semantic_artifact_id"] == DEMO_SEM
               and [e["film"] for e in base["epochs"]]
               == [e["film"] for e in after["epochs"]]
               and rev_before == PJ._revision_of(store.load("alpha")))
        rep(aa8, None, "AA8) IDENTITY INVARIANT -- migration moves no project "
            "revision and no SemanticArtifactID / per-epoch films")

        # ---- AA9 the migrated project re-opens to the same committed world ------
        sess = PJ.open_session_from_project_any(store.load("alpha"))
        aa9 = (PJ.project_version_of(store.load("alpha")) == PJ.PROJECT_V2_VERSION
               and sess.draft.active_semantic_id == DEMO_SEM)
        rep(aa9, None, "AA9) the migrated V2 project re-opens to a live session whose "
            "committed world is the SAME demo world")

        # ---- AA10 NATIVE -- the migrated active world folds ---------------------
        ver = SB._verify_payload(mig_src, oracle=True)
        aa10_ref = (ver["ok"] and ver["oracle"] and ver["oracle"].get("match") is True
                    and ver["semantic_artifact_id"] == DEMO_SEM)
        aa10_nat = None
        if not SKIP_NATIVE:
            aa10_nat = (ver.get("native") is True and ver.get("parity") is True
                        and all(e["match"] for e in ver["epochs"]))
        rep(aa10_ref, aa10_nat, "AA10) NATIVE -- the migrated active world folds "
            "ic_ref == ic32 == the Fixture oracle")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.6-3] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.6-3 closes the MIGRATION gap: a legacy ForgeProjectV1 project "
          "was effectively read-only under the V2 package (a V2 Save refuses to "
          "overwrite an on-disk V1 doc). `migrate_project_v1_to_v2` is FORWARD-ONLY "
          "and IDENTITY-PRESERVING -- it re-opens the V1 project through the same "
          "validated reopen seam and re-serializes it as V2, moving NO "
          "SemanticArtifactID (AA2/AA8) and preserving the project_revision (AA1/AA4/"
          "AA6). It carries the scenarios (AA3) and the full commit log (AA4) across, "
          "rejects any non-V1 input as a typed WRL_PROJECT_MIGRATION (AA5), rewrites "
          "the on-disk document atomically in place at the same revision (AA6), and "
          "so lets a V2 cache Save a project that was previously read-only (AA7). The "
          "migrated world re-opens to the same committed demo world (AA9) and still "
          "folds ic_ref == ic32 == the Fixture oracle (AA10). NO new identity and NO "
          "new runtime construct -- a project-DOC representation upgrade beside the "
          "durable project + recovery + last-session stores.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
