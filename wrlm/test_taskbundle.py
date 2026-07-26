"""[BINDING wrlm-task-v1] the world adapter and the task seal.

Build-order step 1 of TRVM/WRLM_RESEARCH_BRIEF.md §10, second half: "sealing
into task identity". Step 1's first half (`GoalSpecV1`) is `test_goalspec.py`.

W-checks cover `worldview.py` -- the ONE place the engine's LowerResultV1 shape
is renamed into the artifact's shape. T-checks cover `taskbundle.py` -- the
`task-` rung.

Run:  python3 test_taskbundle.py
"""

import copy
import hashlib
import json
import os
import sys

# Run either way: `python3 test_x.py` from inside wrlm/, or
# `python3 -m wrlm.test_x` from TRVM/. The library itself uses
# package-relative imports, so the PARENT dir is what must be on the path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wrlm import goalspec as G
from wrlm import taskbundle as T
from wrlm import worldview as V
from wrlm.errors import WrlmError

HERE = os.path.dirname(os.path.abspath(__file__))
DEMO_SEM = ("sem-8ae91fe9cbc5fd086ce4356d587c403211e5c7b2b3ebdd3164963674"
            "29ecfe4a")

FAILED = []


def check(label, ok, detail=""):
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", label,
                           "" if ok else "  <-- %s" % detail))
    if not ok:
        FAILED.append(label)


def raises(code, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except WrlmError as e:
        if e.code == code:
            return True, ""
        return False, "raised %s, wanted %s" % (e.code, code)
    except Exception as e:                                    # noqa: BLE001
        return False, "raised untyped %s: %s" % (type(e).__name__, e)
    return False, "did not raise"


def load(name):
    with open(os.path.join(HERE, "fixtures", name)) as fh:
        return json.load(fh)


def main():
    print("[BINDING wrlm-task-v1] world adapter + task seal "
          "(WorldViewV1, TaskBundleV1)")

    demo = load("demo_world.artifact.json")
    lower = load("demo_lower_result.json")
    payload, source = lower["payload"], lower["source"]

    # ------------------------------------------------------------------ W0
    # This battery inserts the parent dir on sys.path, so it CANNOT prove the
    # layer is importable as a package -- it would pass either way. Ask a clean
    # subprocess with no path help, from a directory that is not wrlm/.
    #
    # It matters because step 2 (and eventually TRAAVIIS) imports these modules
    # rather than running them, and a directory-local module layout would work
    # in the battery right up until the day it had to integrate.
    import subprocess
    parent = os.path.dirname(HERE)
    probe = ("import wrlm, wrlm.goalspec, wrlm.taskbundle, wrlm.worldview, "
             "wrlm.errors; print(wrlm.WRLM_VERSION)")
    proc = subprocess.run([sys.executable, "-B", "-c", probe], cwd=parent,
                          capture_output=True, text=True,
                          env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    check("W0)  the layer imports as a PACKAGE from a clean subprocess with no "
          "sys.path help (this file's own path insert cannot prove that)",
          proc.returncode == 0 and proc.stdout.strip() == "0",
          (proc.stderr or proc.stdout).strip().splitlines()[-1:])

    # ------------------------------------------------------------------ W1
    # The whole reason worldview.py exists: the engine and the artifact spell
    # the object key DIFFERENTLY. If this ever stops being true the adapter is
    # dead weight -- so assert the mismatch, not just the fix.
    node_keys = set(payload["graph"]["nodes"][0])
    art_keys = set(demo["objects"][0])
    check("W1)  the shape mismatch is REAL: LowerResultV1 says `id`, the "
          "artifact says `object_id`",
          "id" in node_keys and "object_id" not in node_keys
          and "object_id" in art_keys and "id" not in art_keys,
          "node=%s artifact=%s" % (sorted(node_keys), sorted(art_keys)))

    # ------------------------------------------------------------------ W2
    # Both paths must converge, or "the same world" would mean two things.
    v_low = V.from_lower_result(payload)
    v_art = V.from_artifact(demo, DEMO_SEM)
    same = (v_low["objects"] == v_art["objects"]
            and v_low["edges"] == v_art["edges"]
            and v_low["semantic_id"] == v_art["semantic_id"] == DEMO_SEM)
    check("W2)  both paths converge: a lowered source and the stored artifact "
          "produce the SAME view", same,
          "low=%s art=%s" % (v_low["objects"][:1], v_art["objects"][:1]))

    # ------------------------------------------------------------------ W3
    # A view is worthless if the evaluator can't read it. Every G13 predicate
    # must give the same answer on the view as on the artifact.
    preds = {
        "2 pulsers": G.exactly("objects", G.role("Pulser"), 2),
        "1 spinner": G.exactly("objects", G.role("Spinner"), 1),
        "pulser -> relay": G.wired("SignalWire", G.role("Pulser"),
                                   G.role("Relay")),
        "spinner -> orb": G.wired("SocketControl", G.role("Spinner"),
                                  G.role("Orb")),
        "no direct pulser -> spinner": G.wired("SignalWire", G.role("Pulser"),
                                               G.role("Spinner")),
    }
    disagree = [k for k, g in preds.items()
                if G.evaluate_goal(g, v_low) != G.evaluate_goal(g, demo)]
    check("W3)  the view is goal-evaluable: %d/%d predicates agree with the "
          "artifact" % (len(preds) - len(disagree), len(preds)),
          not disagree, str(disagree))

    # ------------------------------------------------------------------ W4
    # A version bump must FAIL LOUDLY. Silently evaluating a goal against a
    # shape the adapter no longer understands is the bug this pin prevents.
    bumped = dict(payload, result_version="forge.lower-result.v2")
    ok_v, d_v = raises(V.WRLM_BAD_WORLD_VIEW, V.from_lower_result, bumped)
    ok_t, d_t = raises(V.WRLM_BAD_WORLD_VIEW, V.from_lower_result, "nope")
    ok_s, d_s = raises(V.WRLM_BAD_WORLD_VIEW, V.from_lower_result,
                       dict(payload, semantic_artifact_id="sem-nope"))
    check("W4)  the engine payload version is PINNED: a bump, a non-object and "
          "a bad sem- are all typed rejections",
          ok_v and ok_t and ok_s, "%s %s %s" % (d_v, d_t, d_s))

    # ------------------------------------------------------------------ W5
    # A failed lowering is a DATA outcome at the engine boundary. It becomes a
    # typed rejection here so nobody evaluates a goal against a world that does
    # not exist -- and it keeps the engine's own diagnostics rather than
    # paraphrasing them.
    diags = [{"code": "WRL_UNSUPPORTED_FEATURE", "message": "no such role"}]
    rejected = {"result_version": V.ACCEPTS_LOWER_RESULT_VERSION, "ok": False,
                "error": "did not lower", "diagnostics": diags}
    kept = None
    try:
        V.from_lower_result(rejected)
    except V.NotLoweredError as e:
        kept = (e.code == V.WRLM_WORLD_NOT_LOWERED and e.diagnostics == diags)
    check("W5)  a source that did not lower is a typed rejection that KEEPS "
          "the engine's own diagnostics", kept is True, repr(kept))

    # ------------------------------------------------------------------ W6
    # The verifier that lets wrlm trust a fixture without importing forge.
    derived = V.semantic_id_of_artifact(demo)
    tampered = copy.deepcopy(demo)
    tampered["objects"][0]["role"] = "Relay"
    check("W6)  sem- is re-derivable from the artifact's own bytes (and a "
          "one-field tamper moves it)",
          derived == DEMO_SEM
          and V.semantic_id_of_artifact(tampered) != DEMO_SEM, derived)

    # ------------------------------------------------------------------ W7
    # The identity law, and the most important check in this file. W1 protects
    # SHAPE; this protects IDENTITY. A trusted semantic_id lets an empty world
    # present itself as any world in the corpus -- and since a target-bearing
    # task is scored by comparing sem-, that is a direct false-positive path.
    ok_c, d_c = raises(V.WRLM_BAD_WORLD_VIEW, V.from_artifact,
                       {"objects": [], "edges": []}, "sem-" + "0" * 64)
    ok_w, d_w = raises(V.WRLM_BAD_WORLD_VIEW, V.from_artifact, demo,
                       "sem-" + "f" * 64)
    derived_only = V.from_artifact(demo)          # no claim at all
    check("W7)  from_artifact DERIVES its own sem-: an empty world claiming an "
          "id, and a real world claiming the wrong one, are both refused",
          ok_c and ok_w and derived_only["semantic_id"] == DEMO_SEM,
          "%s %s" % (d_c, d_w))

    # ------------------------------------------------------------------ W8
    # Silently dropping a corrupt member shrinks a broken artifact into a
    # smaller VALID-LOOKING world -- which can make a goal like "no Spinner
    # exists" pass. Containers and members are both typed rejections.
    art_bad = [lbl for art, lbl in (
        ({"objects": 1, "edges": []}, "objects not a list"),
        ({"objects": [], "edges": 1}, "edges not a list"),
        ({"objects": [{"object_id": "a", "role": "Orb", "static_config": {}},
                      "junk"], "edges": []}, "non-dict member"),
    ) if not raises(V.WRLM_BAD_WORLD_VIEW, V.from_artifact, art)[0]]
    low_bad = []
    for key in ("nodes", "edges"):
        bad = dict(payload, graph=dict(payload["graph"], **{key: 1}))
        if not raises(V.WRLM_BAD_WORLD_VIEW, V.from_lower_result, bad)[0]:
            low_bad.append("graph." + key)
    check("W8)  malformed containers are TYPED rejections, never silently "
          "coerced or filtered (a corrupt world must not shrink into a valid "
          "one)", not art_bad and not low_bad, "%s %s" % (art_bad, low_bad))

    # ------------------------------------------------------------------ W9
    # Totality is claimed for the EVALUATOR, so it must hold there even for
    # shapes the adapter would have refused upstream.
    g_none = G.none("objects", G.role("Spinner"))
    evaluator_total = all(
        G.evaluate_goal(g_none, w) in (True, False)
        for w in ({"objects": 1, "edges": []}, {"objects": [], "edges": 1},
                  {"objects": None, "edges": None}, 7, "world"))
    ok_dg, d_dg = raises(G.WRLM_BAD_GOAL, G.deserialize_goal, 123)
    ok_dt, d_dt = raises(T.WRLM_BAD_TASK, T.deserialize_task, 123)
    check("W9)  the evaluator is total even on shapes the adapter refuses, and "
          "both deserializers TYPE-reject non-str/bytes input",
          evaluator_total and ok_dg and ok_dt, "%s %s" % (d_dg, d_dt))

    # ------------------------------------------------------------------ T1
    goal = G.exactly("objects", G.role("Spinner"), 2)
    task = T.make_task(DEMO_SEM, source, goal=goal, family="add_spinner",
                       tier=1, difficulty="easy", generator_id="handwritten",
                       generator_version="0", seed=7)
    tid = T.task_bundle_id(task)
    check("T1)  a well-formed bundle validates and mints a task- id",
          T.validate_task_v1(task) is task and tid.startswith("task-")
          and len(tid) == len("task-") + 64, tid)

    # ------------------------------------------------------------------ T2
    # The load-bearing law. A task with nothing to satisfy is unfalsifiable --
    # exactly the failure class the sem- spine exists to remove.
    empty = copy.deepcopy(task)
    empty["objective"] = {"goal": None, "goal_spec_id": None,
                          "target_semantic_id": None}
    ok, d = raises(T.WRLM_TASK_NO_OBJECTIVE, T.validate_task_v1, empty)
    check("T2)  an objective is MANDATORY: neither a goal nor a target world "
          "is a typed rejection", ok, d)

    # ------------------------------------------------------------------ T3
    # A carried id is a convenience for readers. Believing it would make the
    # seal decorative.
    lied = copy.deepcopy(task)
    lied["objective"]["goal_spec_id"] = "goal-" + "0" * 64
    ok_l, d_l = raises(T.WRLM_TASK_ID_MISMATCH, T.validate_task_v1, lied)
    swapped = copy.deepcopy(task)
    swapped["objective"]["goal"] = G.exactly("objects", G.role("Spinner"), 3)
    ok_s, d_s = raises(T.WRLM_TASK_ID_MISMATCH, T.validate_task_v1, swapped)
    check("T3)  the carried goal_spec_id is RE-DERIVED, never trusted: a lied "
          "id and a swapped goal both refuse", ok_l and ok_s,
          "%s %s" % (d_l, d_s))

    # ------------------------------------------------------------------ T4
    # Two flavours of "already solved". The structural one needs no world; the
    # goal one does -- which is exactly why the check is split in two.
    degen = copy.deepcopy(task)
    degen["objective"] = {"goal": None, "goal_spec_id": None,
                          "target_semantic_id": DEMO_SEM}
    ok_d, d_d = raises(T.WRLM_TASK_DEGENERATE, T.validate_task_v1, degen)

    solved = T.make_task(DEMO_SEM, source,
                         goal=G.exactly("objects", G.role("Spinner"), 1),
                         family="noop", tier=0, difficulty="trivial")
    # pure validation accepts it -- it is well-formed; only the WORLD says no
    pure_ok = T.validate_task_v1(solved) is solved
    ok_n, d_n = raises(T.WRLM_TASK_DEGENERATE, T.check_task_nondegenerate,
                       solved, v_low)
    # ...and the real task is NOT degenerate against the same world
    live = T.check_task_nondegenerate(task, v_low) is task
    check("T4)  degeneracy: target==base refuses PURELY; an already-satisfied "
          "goal refuses only against the world (and a real task survives)",
          ok_d and pure_ok and ok_n and live, "%s %s" % (d_d, d_n))

    # ------------------------------------------------------------------ T5
    exact = {k: v for k, v in task.items() if k != "stratum"}
    ok_m, d_m = raises(T.WRLM_BAD_TASK, T.validate_task_v1, exact)
    extra = dict(task, note="hello")
    ok_x, d_x = raises(T.WRLM_BAD_TASK, T.validate_task_v1, extra)
    badv = dict(task, task_version="wrlm.task.v2")
    ok_vv, d_vv = raises(T.WRLM_BAD_TASK, T.validate_task_v1, badv)
    badsem = copy.deepcopy(task)
    badsem["base_world"]["semantic_id"] = "sem-XYZ"
    ok_bs, d_bs = raises(T.WRLM_BAD_TASK, T.validate_task_v1, badsem)
    check("T5)  closed record: missing key, extra key, wrong version and a "
          "malformed sem- are all typed rejections",
          ok_m and ok_x and ok_vv and ok_bs,
          "%s %s %s %s" % (d_m, d_x, d_vv, d_bs))

    # ------------------------------------------------------------------ T6
    bad_tier = copy.deepcopy(task)
    bad_tier["stratum"]["tier"] = True          # bool is an int in Python
    ok_bt, d_bt = raises(T.WRLM_BAD_TASK, T.validate_task_v1, bad_tier)
    neg_tier = copy.deepcopy(task)
    neg_tier["stratum"]["tier"] = -1
    ok_nt, d_nt = raises(T.WRLM_BAD_TASK, T.validate_task_v1, neg_tier)
    bad_diff = copy.deepcopy(task)
    bad_diff["stratum"]["difficulty"] = "impossible"
    ok_bd, d_bd = raises(T.WRLM_BAD_TASK, T.validate_task_v1, bad_diff)
    bad_seed = copy.deepcopy(task)
    bad_seed["generator"]["seed"] = "7"
    ok_bsd, d_bsd = raises(T.WRLM_BAD_TASK, T.validate_task_v1, bad_seed)
    check("T6)  stratum/generator hygiene: bool tier, negative tier, unknown "
          "difficulty and a string seed all refuse",
          ok_bt and ok_nt and ok_bd and ok_bsd,
          "%s %s %s %s" % (d_bt, d_nt, d_bd, d_bsd))

    # ------------------------------------------------------------------ T7
    # task- inherits goal-'s canonicalization: a commutatively-reordered goal
    # must not mint a different task.
    g_a = {"kind": "filter_any", "args": [G.role("Spinner"), G.role("Orb")]}
    g_b = {"kind": "filter_any", "args": [G.role("Orb"), G.role("Spinner")]}
    t_a = T.make_task(DEMO_SEM, source, goal=G.exactly("objects", g_a, 1))
    t_b = T.make_task(DEMO_SEM, source, goal=G.exactly("objects", g_b, 1))
    diff_seed = T.make_task(DEMO_SEM, source, goal=goal, seed=8)
    check("T7)  task identity inherits goal canonicalization (reorder is the "
          "same task) but provenance is IN the id (a different seed is not)",
          T.task_bundle_id(t_a) == T.task_bundle_id(t_b)
          and T.task_bundle_id(diff_seed) != tid,
          "%s %s" % (T.task_bundle_id(t_a), T.task_bundle_id(t_b)))

    # ------------------------------------------------------------------ T8
    sealed = T.seal_task(task)
    fresh = sealed.task
    fresh["stratum"]["tier"] = 99
    ok_i, d_i = raises(G.WRLM_SEALED_IMMUTABLE, setattr, sealed, "_id", "x")
    reopened = T.open_sealed_task(sealed.canonical_bytes,
                                  expect_id=sealed.task_bundle_id)
    ok_e, d_e = raises(T.WRLM_BAD_TASK, T.open_sealed_task,
                       sealed.canonical_bytes, "task-" + "0" * 64)
    check("T8)  sealed: id derived FROM the bytes, .task is a fresh copy, "
          "writes refused, round-trip stable, wrong expect_id refused",
          sealed.task_bundle_id == tid
          and sealed.task_bundle_id == "task-" + hashlib.sha256(
              sealed.canonical_bytes).hexdigest()
          and sealed.task["stratum"]["tier"] == 1
          and ok_i and reopened == sealed and ok_e,
          "%s %s" % (d_i, d_e))

    # ------------------------------------------------------------------ T9
    # The seal's goal must come from the SAME bytes, or task- and goal- could
    # name different objectives.
    sg = sealed.sealed_goal
    target_only = T.make_task(DEMO_SEM, source,
                              target_semantic_id="sem-" + "a" * 64)
    check("T9)  a sealed task re-derives its goal- from its OWN bytes; a "
          "target-only task has no goal seal",
          sg is not None and sg.goal_spec_id == G.goal_spec_id(goal)
          and T.seal_task(target_only).sealed_goal is None,
          repr(sg))

    # ------------------------------------------------------------------ T10
    # Scoring must be total: a scoring loop cannot be crashed by a bad world.
    both = T.make_task(DEMO_SEM, source, goal=goal,
                       target_semantic_id="sem-" + "b" * 64)
    junk = [{}, {"objects": None}, "not a world", {"objects": [], "edges": []}]
    total = all(T.satisfied_by(task, w) is False for w in junk)
    hit = T.satisfied_by(
        T.make_task(DEMO_SEM, source,
                    goal=G.exactly("objects", G.role("Spinner"), 1)), v_low)
    check("T10) satisfied_by is TOTAL and conjunctive on the GOAL clause: "
          "malformed worlds yield False, a both-clause task needs BOTH, a met "
          "goal is True",
          total and hit is True and T.satisfied_by(both, v_low) is False,
          "total=%s hit=%s" % (total, hit))

    # ------------------------------------------------------------------ T11
    b1, b2 = T.serialize_task(task), T.serialize_task(copy.deepcopy(task))
    ok_j, d_j = raises(T.WRLM_BAD_TASK, T.deserialize_task, b"{not json")
    check("T11) deterministic: repeated serialization is byte-identical, "
          "round-trip preserves the id, non-JSON is a TYPED rejection",
          b1 == b2 and T.deserialize_task(b1) == T.canonicalize_task_v1(task)
          and ok_j, d_j)

    # ------------------------------------------------------------------ T12
    # The end-to-end shape a WRLM-0 episode actually takes: engine payload ->
    # view -> task -> "is it solved?", with the goal proven UNMET at attempt 0.
    e2e_goal = G.exactly("objects", G.role("Spinner"), 2)
    e2e = T.make_task(payload["semantic_artifact_id"], source, goal=e2e_goal,
                      family="add_spinner", tier=1, difficulty="easy")
    base_view = V.from_lower_result(payload)
    T.check_task_nondegenerate(e2e, base_view)
    solved_view = copy.deepcopy(base_view)
    solved_view["objects"].append({"object_id": "sp2", "role": "Spinner",
                                   "static_config": {}})
    check("T12) end to end: engine payload -> view -> task-, UNSOLVED at "
          "attempt 0 and SOLVED once the world gains the second spinner",
          T.satisfied_by(e2e, base_view) is False
          and T.satisfied_by(e2e, solved_view) is True
          and e2e["base_world"]["semantic_id"] == DEMO_SEM)

    # ------------------------------------------------------------------ T13
    # The costliest failure direction in the whole layer. A target clause is
    # decided by comparing sem-, and a bare artifact carries none -- so before
    # this closure, scoring a SOLVED episode against an artifact instead of a
    # view returned False. A crash gets noticed; a silently unrewarded success
    # gets trained against.
    solved_task = T.make_task("sem-" + "c" * 64, "src",
                              target_semantic_id=DEMO_SEM)
    ok_bare, d_bare = raises(T.WRLM_BAD_TASK, T.satisfied_by, solved_task, demo)
    ok_junk, d_junk = raises(T.WRLM_BAD_TASK, T.satisfied_by, solved_task,
                             {"objects": [], "edges": []})
    check("T13) a target-bearing task REFUSES an identity-less world instead "
          "of silently scoring a solved episode as failed",
          T.satisfied_by(solved_task, V.from_artifact(demo)) is True
          and ok_bare and ok_junk, "%s %s" % (d_bare, d_junk))

    # ------------------------------------------------------------------ T14
    # task- is a receipt; case- is the statistical unit. A generator emitting
    # one problem under 20 seeds would otherwise present 20 "independent"
    # observations, multiplying n by 20 and shrinking every interval on nothing.
    seeds = [T.make_task(DEMO_SEM, source, goal=goal, seed=s, tier=1,
                         difficulty="easy", family="add_spinner")
             for s in range(5)]
    labels = T.make_task(DEMO_SEM, source, goal=goal, seed=0, tier=1,
                         difficulty="hard", family="relabelled",
                         generator_id="other", generator_version="9")
    one_case = len({T.case_id(t) for t in seeds}) == 1
    many_tasks = len({T.task_bundle_id(t) for t in seeds}) == 5
    label_free = T.case_id(labels) == T.case_id(seeds[0])
    # ...but a different QUESTION is a different case
    other_goal = T.make_task(DEMO_SEM, source,
                             goal=G.exactly("objects", G.role("Spinner"), 3))
    other_src = T.make_task(DEMO_SEM, source + "  ; a comment", goal=goal)
    distinct = (T.case_id(other_goal) != T.case_id(seeds[0])
                and T.case_id(other_src) != T.case_id(seeds[0]))
    check("T14) case- is the DEDUP unit and task- the provenance unit: 5 seeds "
          "= 5 tasks but 1 case; difficulty/generator relabels do not move "
          "case-; a different goal or presented source does",
          one_case and many_tasks and label_free and distinct
          and T.seal_task(seeds[0]).case_id == T.case_id(seeds[0]),
          "one_case=%s many=%s label_free=%s distinct=%s"
          % (one_case, many_tasks, label_free, distinct))

    print()
    if FAILED:
        print("FAILED: %s" % ", ".join(FAILED))
        return 1
    print("PASS_TASK_V1 -- one adapter, one task rung, both sealed and total.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
