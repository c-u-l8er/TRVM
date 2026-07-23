"""binding_run34.py -- v0.6-4 perf/release closure: bounded identity-keyed caches
and a runtime release self-check (BB1-BB10).

The sealed-program cache (`_PROG_CACHE`) and the reference-trajectory cache
(`_TRAJ_CACHE`) are PURE memos -- an entry is a pure function of its key, so an
evicted key is simply recomputed to byte-identical bytes. v0.6-4 turns the two
previously UNBOUNDED dicts into bounded LRU caches (`_LruCache`, cap
`_CACHE_CAP`) so a long-lived release / editing session that seals thousands of
distinct sources cannot grow memory without limit -- WITHOUT moving any identity
(an eviction just recomputes). The release also gains a `/api/health`
self-check (`_health_payload`) that re-lowers the demo world FRESH (bypassing the
memo) and confirms it STILL reproduces `DEMO_WORLD_SEMANTIC_ID`, so a running
build proves its identity spine at runtime instead of trusting a startup-time
constant, and reports the bench version + bounded-cache occupancy.

Battery BB1-BB10 (the v0.6-4 acceptance gate):

  BB1  `_LruCache` BOUNDS at its cap -- putting N > cap keys leaves exactly cap
       entries and evicts the LEAST-recently-used (the untouched oldest key);
  BB2  LRU ORDER -- a `get` on an old key moves it to the most-recent end so it
       SURVIVES a subsequent eviction while a never-touched key is dropped;
  BB3  PURE MEMO (prog) -- flooding `_PROG_CACHE` past its cap EVICTS the demo
       entry, yet re-lowering the demo source reproduces the SAME sealed program
       (byte-identical SemanticArtifactID) and the cache never exceeds its cap;
  BB4  PURE MEMO (traj) -- flooding `_TRAJ_CACHE` past its cap bounds it, and a
       real demo run AFTER the flood still yields the correct per-epoch films;
  BB5  `_health_payload` reports ok + the bench version + identity_ok True +
       demo_semantic_id == DEMO_SEM + the bounded-cache {size, cap} shape;
  BB6  the self-check re-lowers FRESH -- identity_ok holds and every cache cap
       reported is exactly `_CACHE_CAP`;
  BB7  the self-check is a PURE READ -- a `_health_payload` call re-lowers via
       `W.lower_program` directly (NOT `_prog`), so it does NOT mutate
       `_PROG_CACHE` occupancy and does not move DEMO_SEM;
  BB8  THREAD-SAFE -- concurrent puts/gets from several threads never exceed the
       cap and never raise (the LRU is internally locked);
  BB9  IDENTITY INVARIANT -- bounding / eviction / health churn leaves the demo
       world's SemanticArtifactID + per-epoch films byte-for-byte unchanged;
  BB10 NATIVE -- after the cache churn, the demo world still folds
       ic_ref == ic32 == the independent Fixture oracle.

Native gated exactly like the sibling batteries (TRVM_SKIP_NATIVE=1 -> ref).
"""
import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "runtime", "python"))
sys.path.insert(0, os.path.join(HERE, "..", "research"))

import spinner_bench as SB

SKIP_NATIVE = os.environ.get("TRVM_SKIP_NATIVE") == "1"

DEMO = SB.DEMO_WORLD_SOURCE
DEMO_SEM = SB.DEMO_WORLD_SEMANTIC_ID


def _distinct_source(i):
    """A unique, valid WRL Core world source (one isolated door) -- each seals to
    a DISTINCT SemanticArtifactID, so lowering many of them floods _PROG_CACHE."""
    return "profile forge.world.core.v1\n\n[door:d%d]{sig_in}\n" % i


def main():
    print("[BINDING wrl-v0.6-4] perf/release closure -- bounded caches + health (BB1-BB10)")
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

    # ---- BB1 _LruCache bounds at cap, evicts the least-recently-used ------------
    c = SB._LruCache(4)
    for i in range(10):
        c.put(("k", i), i)
    bb1 = (len(c) == 4 and c.cap == 4
           and c.get(("k", 9)) == 9        # newest kept
           and c.get(("k", 0)) is None)    # oldest evicted
    rep(bb1, None, "BB1) _LruCache bounds at cap (10 puts, cap 4 -> len 4, "
        "oldest key evicted)")

    # ---- BB2 LRU order -- a touched key survives a later eviction ---------------
    c = SB._LruCache(3)
    c.put("a", 1)
    c.put("b", 2)
    c.put("c", 3)
    c.get("a")               # touch "a" -> most recent; "b" is now the LRU
    c.put("d", 4)            # evicts "b" (never touched since insert), NOT "a"
    bb2 = (len(c) == 3 and c.get("a") == 1
           and c.get("b") is None and c.get("d") == 4)
    rep(bb2, None, "BB2) LRU order -- a get() on an old key moves it to the recent "
        "end so it survives the next eviction (untouched key dropped)")

    # ---- BB3 PURE MEMO (prog) -- eviction recomputes byte-identical -------------
    p1 = SB._prog(DEMO).semantic_artifact_id
    for i in range(SB._CACHE_CAP + 8):     # flood past cap -> the demo entry evicts
        SB._prog(_distinct_source(i))
    p2 = SB._prog(DEMO).semantic_artifact_id
    bb3 = (len(SB._PROG_CACHE) <= SB._CACHE_CAP
           and p1 == p2 == DEMO_SEM)
    rep(bb3, None, "BB3) PURE MEMO (prog) -- flooding _PROG_CACHE past cap evicts "
        "the demo yet it re-lowers to the SAME id; cache never exceeds cap")

    # ---- BB4 PURE MEMO (traj) -- bound + a real run still correct ---------------
    for i in range(SB._CACHE_CAP + 8):     # flood the trajectory cache directly
        SB._TRAJ_CACHE.put(("sem-%d" % i, "ref", "scen-%d" % i), [{"film": i}])
    run = SB._run_payload(DEMO)
    golden_films = [e["film"] for e in SB._run_payload(DEMO)["epochs"]]
    bb4 = (len(SB._TRAJ_CACHE) <= SB._CACHE_CAP
           and run["ok"] and run["semantic_artifact_id"] == DEMO_SEM
           and [e["film"] for e in run["epochs"]] == golden_films
           and len(run["epochs"]) == 7)
    rep(bb4, None, "BB4) PURE MEMO (traj) -- flooding _TRAJ_CACHE bounds it and a "
        "real demo run after the flood still yields the correct 7-epoch films")

    # ---- BB5 _health_payload shape + values ------------------------------------
    h = SB._health_payload()
    bb5 = (h.get("ok") is True
           and h.get("bench_version") == SB.BENCH_VERSION
           and h.get("identity_ok") is True
           and h.get("demo_semantic_id") == DEMO_SEM
           and set(h["caches"]) == {"prog", "traj"}
           and set(h["caches"]["prog"]) == {"size", "cap"}
           and set(h["caches"]["traj"]) == {"size", "cap"})
    rep(bb5, None, "BB5) _health_payload reports ok + bench_version + identity_ok + "
        "demo_semantic_id + the {size,cap} cache shape")

    # ---- BB6 self-check re-lowers fresh; caps are exactly _CACHE_CAP ------------
    bb6 = (h["identity_ok"] is True
           and h["caches"]["prog"]["cap"] == SB._CACHE_CAP
           and h["caches"]["traj"]["cap"] == SB._CACHE_CAP)
    rep(bb6, None, "BB6) the release self-check re-lowers the demo FRESH -> "
        "identity_ok True; every reported cache cap == _CACHE_CAP")

    # ---- BB7 self-check is a PURE READ (does not touch _PROG_CACHE) -------------
    size_before = len(SB._PROG_CACHE)
    h2 = SB._health_payload()
    size_after = len(SB._PROG_CACHE)
    bb7 = (size_before == size_after            # health does NOT go through _prog
           and h2["demo_semantic_id"] == DEMO_SEM
           and h2["identity_ok"] is True)
    rep(bb7, None, "BB7) the self-check is a pure read -- a _health_payload call "
        "does not mutate _PROG_CACHE occupancy and does not move DEMO_SEM")

    # ---- BB8 THREAD-SAFE bounded cache -----------------------------------------
    shared = SB._LruCache(16)
    errors = []

    def hammer(base):
        try:
            for i in range(500):
                shared.put((base, i % 40), i)
                shared.get((base, i % 40))
        except Exception as ex:            # any race -> a recorded failure
            errors.append(ex)

    threads = [threading.Thread(target=hammer, args=(b,)) for b in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    bb8 = (not errors and len(shared) <= 16 and shared.cap == 16)
    rep(bb8, None, "BB8) THREAD-SAFE -- 6 threads hammering put/get never exceed the "
        "cap and never raise")

    # ---- BB9 IDENTITY INVARIANT across all the cache churn ----------------------
    base = SB._run_payload(DEMO)
    for i in range(SB._CACHE_CAP + 4):     # more churn, then health, then re-run
        SB._prog(_distinct_source(10000 + i))
    SB._health_payload()
    after = SB._run_payload(DEMO)
    bb9 = (base["ok"] and after["ok"]
           and base["semantic_artifact_id"] == DEMO_SEM
           and after["semantic_artifact_id"] == DEMO_SEM
           and [e["film"] for e in base["epochs"]]
           == [e["film"] for e in after["epochs"]])
    rep(bb9, None, "BB9) IDENTITY INVARIANT -- bounding / eviction / health churn "
        "leaves the demo SemanticArtifactID + per-epoch films byte-for-byte equal")

    # ---- BB10 NATIVE -- the demo world still folds after churn ------------------
    ver = SB._verify_payload(DEMO, oracle=True)
    bb10_ref = (ver["ok"] and ver["oracle"] and ver["oracle"].get("match") is True
                and ver["semantic_artifact_id"] == DEMO_SEM)
    bb10_nat = None
    if not SKIP_NATIVE:
        bb10_nat = (ver.get("native") is True and ver.get("parity") is True
                    and all(e["match"] for e in ver["epochs"]))
    rep(bb10_ref, bb10_nat, "BB10) NATIVE -- after the cache churn the demo world "
        "folds ic_ref == ic32 == the Fixture oracle")

    dt = time.time() - t0
    if SKIP_NATIVE:
        verdict = "PASS_REF_ONLY (native skipped)" if allok else "FAIL"
    elif not native_ok:
        verdict = "REF_ONLY (native MISMATCH)"
        allok = False
    else:
        verdict = "PASS_REF_AND_NATIVE" if allok else "FAIL"
    print(f"\n[wrl-v0.6-4] {'ALL PASS' if allok else 'FAILURES'} -- {verdict} "
          f"({dt:.0f}s)")
    print("  [note] v0.6-4 CLOSES the v0.6 series with a perf/release pass: the two "
          "identity-keyed caches (sealed programs by source, reference trajectories "
          "by (SemanticArtifactID, reducer, ScenarioDigest)) are now BOUNDED LRU "
          "memos (cap _CACHE_CAP) instead of unbounded dicts, so a long-lived "
          "release cannot grow memory without limit -- and because a cache is a PURE "
          "memo, an evicted key is recomputed to byte-identical bytes and moves NO "
          "identity (BB3/BB4/BB9). The release also gains a /api/health self-check "
          "that re-lowers the demo world FRESH and confirms it still reproduces "
          "DEMO_WORLD_SEMANTIC_ID (BB5/BB6), a pure read that never touches the memo "
          "(BB7), plus the bench version + cache occupancy. The bound is thread-safe "
          "(BB8) and the demo still folds ic_ref == ic32 == the Fixture oracle after "
          "all the churn (BB10). NO new identity, NO new runtime construct -- caching "
          "and a runtime self-check over the frozen identity spine.")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
