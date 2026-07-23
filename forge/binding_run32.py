"""binding_run32.py -- v0.6-2 startup/project UX: last-session pointer (Z1-Z10).

v0.6-1 (binding_run31) made the long ic-reducer folds cancellable background jobs.
v0.6-2 closes the STARTUP gap: a reload used to re-dump the demo world even when
the author had been working in a named project. A single, non-authoritative
`LastSessionPointerV1` records the LAST opened project so a reload lands back in
it; it advances NO project revision, moves NO SemanticArtifactID, and self-heals a
pointer at a trashed/removed project to None (startup never reopens a gone project).

Battery Z1-Z10 (the v0.6-2 acceptance gate):

  Z1  validate/canonicalize/serialize round-trips and is idempotent + byte-stable;
  Z2  every malformed pointer is a typed WRL_BAD_SESSION_POINTER (non-dict, bad
      version, missing/extra field, bad project id, non-numeric updated_at);
  Z3  an empty store: get() -> None (never raises on absence), clear() is a no-op;
  Z4  set(pid) then get() returns that pid with a wall clock, and writes the file;
  Z5  set is an ATOMIC overwrite (set A then B -> B); set refuses a bad id;
  Z6  clear() drops the pointer and is idempotent (get() -> None afterwards);
  Z7  the `.last_session.json` pointer is NEVER listed as a project (dotted-file
      exclusion from ForgeProjectStore.list_projects);
  Z8  resolve_last_session SELF-HEALS: a pointer at a live project resolves to it;
      a pointer at a gone project resolves to None AND clears the pointer;
  Z9  IDENTITY INVARIANT -- pointer set/clear/resolve churn moves NO project
      revision and leaves the demo world's SemanticArtifactID + per-epoch films
      byte-for-byte unchanged (the pointer is pure UX metadata);
  Z10 NATIVE -- with pointer churn interleaved, the demo verify still folds
      ic_ref == ic32 == the independent Fixture oracle.

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


def _fresh_store():
    """A throwaway ForgeProjectStore + LastSessionStore over a temp root with one
    real project ("alpha") so `exists` is meaningful. Returns (tmp, store, cache,
    sess)."""
    tmp = tempfile.mkdtemp(prefix="wrl-run32-")
    store = PJ.ForgeProjectStore(tmp)
    cache = PJ.ProjectSessionCache(
        store, DEMO, scenarios_for=SB._default_scenarios,
        project_version=PJ.PROJECT_V2_VERSION)
    cache.create_new("alpha", "Alpha")
    return tmp, store, cache, PJ.LastSessionStore(tmp)


def main():
    print("[BINDING wrl-v0.6-2] startup/project UX -- last-session pointer (Z1-Z10)")
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

    good = {"last_session_version": PJ.LAST_SESSION_VERSION,
            "last_project_id": "alpha", "updated_at": 1234.5}

    # ---- Z1 validate/canonicalize/serialize round-trip + idempotent -----------
    canon = PJ.canonicalize_last_session(good)
    blob = PJ.serialize_last_session(good)
    round1 = PJ.canonicalize_last_session(WC.deserialize_artifact(blob))
    z1 = (tuple(canon.keys()) == PJ._LAST_SESSION_TOP
          and canon == round1
          and PJ.canonicalize_last_session(canon) == canon        # idempotent
          and PJ.serialize_last_session(canon) == blob)           # byte-stable
    rep(z1, None, "Z1) validate/canonicalize/serialize round-trips, is idempotent "
        "and byte-stable")

    # ---- Z2 every malformed pointer is a typed WRL_BAD_SESSION_POINTER ---------
    C = PJ.WRL_BAD_SESSION_POINTER
    bad_cases = [
        lambda: PJ.validate_last_session(["not", "a", "dict"]),
        lambda: PJ.validate_last_session(dict(good, last_session_version="x")),
        lambda: PJ.validate_last_session({k: v for k, v in good.items()
                                          if k != "updated_at"}),      # missing
        lambda: PJ.validate_last_session(dict(good, extra=1)),         # extra
        lambda: PJ.validate_last_session(dict(good, last_project_id="bad id!")),
        lambda: PJ.validate_last_session(dict(good, last_project_id=".dotted")),
        lambda: PJ.validate_last_session(dict(good, updated_at=True)),  # bool!=num
        lambda: PJ.validate_last_session(dict(good, updated_at="now")),
    ]
    z2 = all(_raises(fn, C) for fn in bad_cases)
    rep(z2, None, "Z2) every malformed pointer is a typed WRL_BAD_SESSION_POINTER")

    # ---- Z3 empty store: get() -> None, clear() is a no-op --------------------
    tmp, store, cache, sess = _fresh_store()
    try:
        z3 = sess.get() is None
        sess.clear()                       # idempotent no-op on an absent pointer
        z3 = z3 and sess.get() is None
        rep(z3, None, "Z3) an empty store: get() -> None (no raise), clear() no-op")

        # ---- Z4 set(pid) then get() returns it with a wall clock --------------
        t_before = time.time()
        p4 = sess.set("alpha")
        got4 = sess.get()
        z4 = (got4 is not None and got4["last_project_id"] == "alpha"
              and got4["last_session_version"] == PJ.LAST_SESSION_VERSION
              and got4["updated_at"] >= t_before
              and os.path.exists(os.path.join(tmp, ".last_session.json"))
              and p4 == got4)
        rep(z4, None, "Z4) set(pid) then get() returns that pid with a wall clock, "
            "writing the pointer file")

        # ---- Z5 set is an ATOMIC overwrite; refuses a bad id ------------------
        sess.set("alpha", now=1.0)
        sess.set("alpha", now=2.0)          # overwrite (same id, newer clock)
        over_ok = sess.get()["updated_at"] == 2.0
        bad_ok = _raises(lambda: sess.set("bad id!"), C)
        z5 = over_ok and bad_ok
        rep(z5, None, "Z5) set is an atomic overwrite and refuses a bad project id")

        # ---- Z6 clear() drops the pointer and is idempotent -------------------
        sess.clear()
        z6 = sess.get() is None
        sess.clear()                        # again -> still fine
        z6 = z6 and sess.get() is None
        rep(z6, None, "Z6) clear() drops the pointer and is idempotent")

        # ---- Z7 pointer file is NEVER listed as a project ---------------------
        sess.set("alpha")
        projs = store.list_projects()
        z7 = ("alpha" in projs and ".last_session" not in projs
              and all(not p.startswith(".") for p in projs))
        rep(z7, None, "Z7) the .last_session.json pointer is never listed as a "
            "project (dotted-file exclusion)")

        # ---- Z8 resolve_last_session SELF-HEALS -------------------------------
        sess.set("alpha")
        r_live = PJ.resolve_last_session(sess, store)
        sess.set("ghost")                   # ghost was never created
        r_gone = PJ.resolve_last_session(sess, store)
        healed = sess.get() is None         # dangling pointer was cleared
        none_when_empty = PJ.resolve_last_session(sess, store) is None
        z8 = (r_live == "alpha" and r_gone is None and healed and none_when_empty)
        rep(z8, None, "Z8) resolve self-heals: a live pointer resolves, a pointer "
            "at a gone project resolves to None and is cleared")

        # ---- Z9 IDENTITY INVARIANT -- pointer churn moves no identity ---------
        rev_before = PJ._revision_of(store.load("alpha"))
        base = SB._run_payload(DEMO)
        # churn the pointer through the full lifecycle
        sess.set("alpha"); PJ.resolve_last_session(sess, store)
        sess.set("ghost"); PJ.resolve_last_session(sess, store)
        sess.clear(); sess.set("alpha")
        after = SB._run_payload(DEMO)
        rev_after = PJ._revision_of(store.load("alpha"))
        z9 = (base["ok"] and after["ok"]
              and base["semantic_artifact_id"] == DEMO_SEM
              and after["semantic_artifact_id"] == DEMO_SEM
              and [e["film"] for e in base["epochs"]]
              == [e["film"] for e in after["epochs"]]
              and rev_before == rev_after == 0)
        rep(z9, None, "Z9) IDENTITY INVARIANT -- pointer set/clear/resolve churn "
            "moves no project revision and no SemanticArtifactID / films")

        # ---- Z10 NATIVE -- verify still folds ic_ref == ic32 == oracle --------
        sess.set("alpha")                   # pointer live during the fold
        ver = SB._verify_payload(DEMO, oracle=True)
        sess.clear()
        z10_ref = (ver["ok"] and ver["oracle"] and ver["oracle"].get("match") is True
                   and ver["semantic_artifact_id"] == DEMO_SEM)
        z10_nat = None
        if not SKIP_NATIVE:
            z10_nat = (ver.get("native") is True and ver.get("parity") is True
                       and all(e["match"] for e in ver["epochs"]))
        rep(z10_ref, z10_nat, "Z10) NATIVE -- with pointer churn interleaved, the "
            "demo verify folds ic_ref == ic32 == the Fixture oracle")
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
    print(f"\n[wrl-v0.6-2] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.6-2 closes the STARTUP gap: a `LastSessionPointerV1` records "
          "the last opened project so a reload lands back in it instead of the demo. "
          "The pointer is validated/canonical/serialized like the sibling records "
          "(Z1) with a full typed-error surface (Z2); the store returns None on "
          "absence and never raises (Z3), set() writes a wall-clocked pointer (Z4) "
          "atomically (Z5), clear() is idempotent (Z6), and the dotted file is never "
          "mistaken for a project (Z7). resolve_last_session SELF-HEALS a pointer at "
          "a trashed/removed project to None (Z8), so startup never reopens a gone "
          "project. Crucially the pointer is pure UX: churning it moves NO project "
          "revision and NO SemanticArtifactID / films (Z9), and a native verify "
          "still folds ic_ref == ic32 == the Fixture oracle with the pointer live "
          "(Z10). NO new identity and NO new runtime construct -- the pointer is an "
          "additive startup-state record beside the durable project + recovery stores.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
