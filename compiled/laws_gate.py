"""laws_gate.py -- the identity gate for the compiled backend's emitters (T7, `SUPER_BUILDS_LANE.md`).

Every world in the battery is EMITTED (text only: no build, no fold) under the four emitters, and the sha256 of each
emitted source is compared to `identities.json`. A refactor of how the laws are stated -- one law table read by all four
emitters instead of four hand transcriptions -- must leave every byte of every emitted program unchanged, because the
program's bytes are the identity (`cbknd-`/`cbknd2-`/`bbknd-`/`bbknd2-` hash the source). A world an emitter refuses
(Bend over w=24 / w=23) is recorded as `refused` with the message, and a refusal that appears or disappears is drift too.

    python3 laws_gate.py --record     # write identities.json from the emitters as they are NOW (done once, before T7)
    python3 laws_gate.py --check      # exit 1 on any drift, naming the (world, emitter) pairs that moved
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("TRVM_BATTERY_HUGE", "1")          # the gated world is emitted too: emission is cheap, only its fold is not
import battery as B                                     # noqa: E402
import emit_c as EC                                     # noqa: E402
import emit_c2 as EC2                                   # noqa: E402
import emit_bend as EB                                  # noqa: E402
import emit_bend2 as EB2                                # noqa: E402
from fold import SB, P                                  # noqa: E402

EMITTERS = {
    "c": lambda v: EC.emit_step_c(v),
    "c2": lambda v: EC2.emit_step_c2(v)[0],
    "bend": lambda v: EB.emit_step_bend(v),
    "bend2": lambda v: EB2.emit_step_bend2(v)[0],
}
PATH = os.path.join(HERE, "identities.json")


def emit_all():
    out = {}
    for name, src in sorted(B.WORLDS.items()):
        prog, _ = SB._resolve_scenario(src, None)
        view = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
        row = {"sem": prog.semantic_artifact_id}
        for e, fn in EMITTERS.items():
            try:
                text = fn(view)
                row[e] = {"source_sha256": hashlib.sha256(text.encode()).hexdigest(), "bytes": len(text.encode())}
            except ValueError as ex:
                row[e] = {"refused": str(ex)}
        out[name] = row
    return out


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--record", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    now = emit_all()
    if a.record:
        with open(PATH, "w") as f:
            json.dump({"note": "sha256 of each world's emitted source under each emitter; laws_gate.py --check refuses drift", "worlds": now}, f, indent=1, sort_keys=True)
        print("recorded %d worlds x %d emitters -> %s" % (len(now), len(EMITTERS), PATH))
        return 0
    base = json.load(open(PATH))["worlds"]
    drift = []
    for w in sorted(set(base) | set(now)):
        for e in EMITTERS:
            b, n = base.get(w, {}).get(e), now.get(w, {}).get(e)
            if b != n:
                drift.append((w, e, b, n))
    for w, e, b, n in drift:
        print("DRIFT %-22s %-5s was %s now %s" % (w, e, json.dumps(b)[:70], json.dumps(n)[:70]))
    print("LAWS GATE:", "HELD (%d worlds x %d emitters byte-identical)" % (len(now), len(EMITTERS)) if not drift else "DRIFT in %d pairs" % len(drift))
    return 1 if drift else 0


if __name__ == "__main__":
    raise SystemExit(main())
