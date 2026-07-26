"""[BINDING wrlm-worldrecord-v1] the verified capture object.

Build-order step 2 of TRVM/WRLM_RESEARCH_BRIEF.md §10, first object. Before any
generator exists, because a generator that builds on an unverified world
produces a corpus whose worlds are only nominally real.

Numbering follows the step-2 R-series; R4-R17 arrive with the generators.

Run:  python3 test_worldrecord.py      (or: python3 -m wrlm.test_worldrecord)
"""

import copy
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wrlm import envelope as E
from wrlm import goalspec as G
from wrlm import taskbundle as T
from wrlm import worldrecord as R
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


POOL = load("pool.json")


def replay_lower(source):
    """A deterministic engine, restricted to sources we have already lowered.

    This is not a stub that says yes. A real engine IS a function from source to
    result; a captured pool is that same function on a finite domain. Injecting
    it exercises the genuine `prove_envelope` path with no forge import, which
    is what lets an offline battery test a proof-of-production at all."""
    for w in POOL:
        if w["source"] == source:
            return w["lower_result"]
    raise AssertionError("replay_lower asked for an uncaptured source")


def seal(world, publisher="wrlm.test", version="1"):
    return E.seal_envelope(world["source"], world["lower_result"],
                           publisher, version)


def main():
    print("[BINDING wrlm-worldrecord-v1] the verified capture object "
          "(WorldRecordV1)")

    demo = load("demo_world.artifact.json")
    lower = load("demo_lower_result.json")
    payload, source = lower["payload"], lower["source"]
    env = E.seal_envelope(source, payload, "wrlm.test", "1")

    rec = R.capture(env, demo)

    # ------------------------------------------------------------------ R1
    check("R1)  a captured record carries the DERIVED identity and reopens "
          "under its own validator",
          rec["semantic_id"] == DEMO_SEM
          and R.validate_record_v1(rec) is rec
          and R.view(rec)["semantic_id"] == DEMO_SEM,
          rec["semantic_id"])

    # ------------------------------------------------------------------ R2
    # Capture exists to make the two sides AGREE. Identity agreement is checked
    # first, content agreement second -- same sem- with different contents
    # would mean the adapter pair is broken, and a generator reading the wrong
    # side would build tasks about a world that never ran.
    wrong_id = copy.deepcopy(payload)
    wrong_id["semantic_artifact_id"] = "sem-" + "1" * 64
    ok_id, d_id = raises(R.WRLM_RECORD_UNBOUND, R.capture,
                         E.seal_envelope(source, wrong_id, "t", "1"), demo)
    # a real, valid, but DIFFERENT world: identity disagreement, cleanly
    other = copy.deepcopy(demo)
    other["objects"] = [o for o in other["objects"]
                        if o["object_id"] != "p1"]
    other["edges"] = [e for e in other["edges"] if e["src"] != "p1"]
    ok_other, d_other = raises(R.WRLM_RECORD_UNBOUND, R.capture, env, other)
    check("R2)  capture REFUSES when the engine and the artifact name "
          "different worlds (a lied payload id, and a genuinely other world)",
          ok_id and ok_other, "%s %s" % (d_id, d_other))

    # ------------------------------------------------------------------ R3
    # The binding this whole object exists for. A task's base_world pair is
    # unverifiable inside a pure validator; a record is the receipt that
    # something WITH an engine checked it.
    tampered = copy.deepcopy(rec)
    tampered["artifact"]["objects"][0]["role"] = "Relay"
    ok_t, d_t = raises(R.WRLM_RECORD_UNBOUND, R.validate_record_v1, tampered)
    swapped = copy.deepcopy(rec)
    swapped["semantic_id"] = "sem-" + "2" * 64
    ok_s, d_s = raises(R.WRLM_RECORD_UNBOUND, R.validate_record_v1, swapped)
    check("R3)  source/artifact/identity stay BOUND on reopen: tampering with "
          "the stored artifact, or with the claimed id, both refuse",
          ok_t and ok_s, "%s %s" % (d_t, d_s))

    # ------------------------------------------------------------------ R3b
    ok_e, d_e = raises(E.WRLM_BAD_ENVELOPE, E.seal_envelope, "", payload,
                       "t", "1")
    ok_ws, d_ws = raises(E.WRLM_BAD_ENVELOPE, E.seal_envelope, "   \n ",
                         payload, "t", "1")
    ok_p, d_p = raises(E.WRLM_BAD_ENVELOPE, E.seal_envelope, source, payload,
                       "", "1")
    check("R3b) a record needs the non-empty SOURCE that produced it, and a "
          "named publisher -- an asserted binding is only as good as who sealed it",
          ok_e and ok_ws and ok_p, "%s %s %s" % (d_e, d_ws, d_p))

    # ------------------------------------------------------------------ R3c
    # Invalid WRL has no sem-, so it cannot become a record. This is the scope
    # ruling made mechanical: the diagnostic-repair family CANNOT be smuggled
    # into a TaskBundleV1 by pairing bad source with a borrowed identity,
    # because the only blessed path to a base_world runs through here.
    not_lowered = {"result_version": V.ACCEPTS_LOWER_RESULT_VERSION,
                   "ok": False, "error": "no such role",
                   "diagnostics": [{"code": "WRL_UNSUPPORTED_FEATURE"}]}
    ok_nl, d_nl = raises(V.WRLM_WORLD_NOT_LOWERED, R.capture,
                         E.seal_envelope("orb x { }", not_lowered, "t", "1"),
                         demo)
    check("R3c) invalid source cannot become a record at all, so a repair task "
          "cannot borrow another world's sem- (scope ruling, mechanized)",
          ok_nl, d_nl)

    # ------------------------------------------------------------------ R3d
    hollow = copy.deepcopy(rec)
    del hollow["engine_version"]
    ok_h, d_h = raises(R.WRLM_BAD_WORLD_RECORD, R.validate_record_v1, hollow)
    fat = dict(rec, extra=1)
    ok_f, d_f = raises(R.WRLM_BAD_WORLD_RECORD, R.validate_record_v1, fat)
    ok_b, d_b = raises(R.WRLM_BAD_WORLD_RECORD, R.deserialize_record, 123)
    check("R3d) closed record: missing key, extra key and non-str/bytes input "
          "are typed rejections", ok_h and ok_f and ok_b,
          "%s %s %s" % (d_h, d_f, d_b))

    # ----------------------------------------------------------------- R3e-h
    # The hole the old R-battery did not find. `capture(result, artifact,
    # source="anything")` used to succeed, returning a record with the REAL sem-
    # beside unrelated text -- and it minted a sealed, internally consistent,
    # completely false `case-`. There is now no free `source=` to pass at all,
    # so the shape of the fix is that the crossed call cannot be SPELLED.
    ok_sig = not any(k in R.capture.__code__.co_varnames[
        :R.capture.__code__.co_argcount] for k in ("source",))
    demo_world = [w for w in POOL if w["name"] == "demo"][0]
    other_world = [w for w in POOL if w["name"] == "medium_a"][0]
    crossed = E.seal_envelope(other_world["source"], payload, "t", "1")
    ok_x, d_x = raises(E.WRLM_ENVELOPE_CROSSED, R.capture, crossed, demo,
                       replay_lower)
    check("R3e) a CROSSED envelope -- one world's source sealed beside another "
          "world's result -- is refused when the binding is proved, and there "
          "is no `source=` left to cross by hand",
          ok_sig and ok_x, "sig=%s %s" % (ok_sig, d_x))

    # R3f. Proof is available but not mandatory, and the record SAYS which.
    proved = R.capture(seal(demo_world), demo, replay_lower)
    asserted = R.capture(seal(demo_world), demo)
    check("R3f) binding.kind records `proved` vs `asserted` instead of "
          "implying the stronger one -- a corpus knows what it is made of",
          proved["binding"]["kind"] == E.BINDING_PROVED
          and asserted["binding"]["kind"] == E.BINDING_ASSERTED
          and proved["binding"]["publisher"] == "wrlm.test"
          and R.is_proved(proved) and not R.is_proved(asserted),
          "%s / %s" % (proved["binding"], asserted["binding"]))

    # R3g. The envelope is self-sealing: edit the text and the checksum tells.
    tampered_env = copy.deepcopy(env)
    tampered_env["source"] = tampered_env["source"] + "\n; sneaky\n"
    ok_te, d_te = raises(E.WRLM_BAD_ENVELOPE, E.validate_envelope_v1,
                         tampered_env)
    tampered_rec = copy.deepcopy(rec)
    tampered_rec["source"] = tampered_rec["source"] + "\n; sneaky\n"
    ok_tr, d_tr = raises(R.WRLM_RECORD_UNBOUND, R.validate_record_v1,
                         tampered_rec)
    check("R3h) editing the presented text after sealing is caught at BOTH "
          "boundaries -- `case-` keys on presented source, so this is identity "
          "corruption, not a typo", ok_te and ok_tr, "%s %s" % (d_te, d_tr))

    # ------------------------------------------------------------------ R18
    # The payoff. A captured corpus must reopen in a process that has no engine
    # and no path help -- that is what "offline generation" has to mean.
    blob = R.serialize_record(rec)
    probe = (
        "import json,sys;"
        "from wrlm import worldrecord as R, taskbundle as T, goalspec as G;"
        "rec=R.deserialize_record(sys.stdin.buffer.read());"
        "t=T.make_task_for(rec, goal=G.exactly('objects', G.role('Spinner'), 2),"
        " family='add_spinner', tier=1, difficulty='easy');"
        "T.check_task_nondegenerate(t, R.view(rec));"
        "print(json.dumps({'sem':rec['semantic_id'],'task':T.task_bundle_id(t),"
        "'case':T.case_id(t)}))")
    proc = subprocess.run([sys.executable, "-B", "-c", probe],
                          cwd=os.path.dirname(HERE), input=blob,
                          capture_output=True,
                          env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    out = {}
    if proc.returncode == 0:
        out = json.loads(proc.stdout.decode())
    local = T.make_task_for(rec, goal=G.exactly("objects", G.role("Spinner"), 2),
                            family="add_spinner", tier=1, difficulty="easy")
    check("R18) a serialized record reopens OFFLINE -- clean subprocess, no "
          "engine, no sys.path help -- and generates the byte-identical task",
          proc.returncode == 0 and out.get("sem") == DEMO_SEM
          and out.get("task") == T.task_bundle_id(local)
          and out.get("case") == T.case_id(local),
          (proc.stderr.decode() or "").strip().splitlines()[-1:])

    # ------------------------------------------------------------------ R19
    # Routing through a record is what makes base_world trustworthy, so the
    # helper must produce exactly what the loose constructor does -- otherwise
    # the safe path would also be the lossy one and nobody would take it.
    loose = T.make_task(rec["semantic_id"], rec["source"],
                        goal=G.exactly("objects", G.role("Spinner"), 2),
                        family="add_spinner", tier=1, difficulty="easy")
    bad_rec = copy.deepcopy(rec)
    bad_rec["semantic_id"] = "sem-" + "3" * 64
    ok_r, d_r = raises(R.WRLM_RECORD_UNBOUND, T.make_task_for, bad_rec,
                       goal=G.exactly("objects", G.role("Spinner"), 2))
    check("R19) make_task_for(record) == make_task(loose pair) for a VALID "
          "record, and refuses an unbound one",
          T.task_bundle_id(local) == T.task_bundle_id(loose) and ok_r, d_r)

    print()
    if FAILED:
        print("FAILED: %s" % ", ".join(FAILED))
        return 1
    print("PASS_WORLD_RECORD_V1 -- captured once, verified, offline forever "
          "after.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
