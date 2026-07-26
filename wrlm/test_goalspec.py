"""[BINDING wrlm-goalspec-v1] the closed predicate AST.

Build-order step 1 of TRVM/WRLM_RESEARCH_BRIEF.md §10.

Run:  python3 test_goalspec.py
"""

import ast
import os
import sys

# Run either way: `python3 test_x.py` from inside wrlm/, or
# `python3 -m wrlm.test_x` from TRVM/. The library itself uses
# package-relative imports, so the PARENT dir is what must be on the path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wrlm import goalspec as G

FAILED = []


def check(label, ok, detail=""):
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", label,
                           "" if ok else "  <-- %s" % detail))
    if not ok:
        FAILED.append(label)


def raises(code, fn, *a, **kw):
    """Assert fn raises GoalSpecError with exactly `code`. Returns (ok, detail)."""
    try:
        fn(*a, **kw)
    except G.GoalSpecError as e:
        if e.code == code:
            return True, ""
        return False, "raised %s, wanted %s" % (e.code, code)
    except Exception as e:                                    # noqa: BLE001
        return False, "raised untyped %s: %s" % (type(e).__name__, e)
    return False, "did not raise"


# ------------------------------------------------------------------ the world
# A small sealed-artifact-shaped world: p1 -> s1 (SignalWire), s1 -> o1
# (SocketControl), plus a lone Relay with no edges.
WORLD = {
    "ir_version": "1.0",
    "profile_id": "forge.world.core.v1",
    "objects": [
        {"object_id": "p1", "role": "Pulser",
         "static_config": {"clock": [0, 4, 0, 0]}},
        {"object_id": "s1", "role": "Spinner",
         "static_config": {"w": 8, "n": 4, "rotor": [1, 0, 0, 0],
                           "configurable": True}},
        {"object_id": "o1", "role": "Orb", "static_config": {}},
        {"object_id": "r1", "role": "Relay", "static_config": {}},
    ],
    "edges": [
        {"kind": "SignalWire", "src": "p1", "dst": "s1"},
        {"kind": "SocketControl", "src": "s1", "dst": "o1"},
    ],
}

SPINNER = G.role("Spinner")
PULSER = G.role("Pulser")
ORB = G.role("Orb")


def main():
    print("[BINDING wrlm-goalspec-v1] the closed predicate AST "
          "(GoalSpecV1, %s)" % G.GOALSPEC_VERSION)

    # ---------------------------------------------------------------- G0
    # The v1 vocabulary is DUPLICATED in wrlm/ so the layer has no build-time
    # dependency on forge/. That duplication is only safe if it is pinned. Pin
    # it by PARSING wrl_canonical.py -- never by importing it (forge is a live
    # working tree) and never by grepping it.
    forge = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "forge", "wrl_canonical.py")
    if os.path.exists(forge):
        with open(forge) as f:
            tree = ast.parse(f.read())
        found = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name) \
                    and node.targets[0].id in ("ROLE_IDS", "EDGE_KINDS"):
                found[node.targets[0].id] = ast.literal_eval(node.value)
        check("G0)  vocabulary pinned against forge/wrl_canonical.py (parsed, "
              "not imported)",
              found.get("ROLE_IDS") == G.ROLE_IDS
              and found.get("EDGE_KINDS") == G.EDGE_KINDS,
              "forge says %r / %r" % (found.get("ROLE_IDS"),
                                      found.get("EDGE_KINDS")))
    else:
        check("G0)  vocabulary pin skipped (forge/wrl_canonical.py absent)", True)

    # ---------------------------------------------------------------- G1
    g = G.exists("objects", SPINNER)
    G.validate_goal_v1(g)
    G.validate_goal_v1(G.forall("objects", G.role("Orb")))
    G.validate_goal_v1(G.exactly("edges", {"kind": "edge_kind_is",
                                           "edge_kind": "SignalWire"}, 1))
    G.validate_goal_v1(G.wired("SignalWire", PULSER, SPINNER))
    check("G1)  builders emit well-formed nodes of the SAME closed AST", True)

    # ---------------------------------------------------------------- G2
    ok1, d1 = raises(G.WRLM_BAD_GOAL, G.validate_goal_v1,
                     {"kind": "reachable", "args": []})
    ok2, d2 = raises(G.WRLM_BAD_GOAL, G.validate_goal_v1,
                     {"kind": "all", "args": [], "extra": 1})
    ok3, d3 = raises(G.WRLM_BAD_GOAL, G.validate_goal_v1,
                     {"kind": "count", "domain": "objects", "where": SPINNER,
                      "cmp": "ge"})
    check("G2)  closed: unknown kind, extra key and missing key all rejected",
          ok1 and ok2 and ok3, "%s %s %s" % (d1, d2, d3))

    # ---------------------------------------------------------------- G3
    ok1, d1 = raises(G.WRLM_GOAL_SORT, G.validate_goal_v1,
                     G.exists("edges", SPINNER))
    ok2, d2 = raises(G.WRLM_GOAL_SORT, G.validate_goal_v1,
                     G.exists("objects", {"kind": "edge_kind_is",
                                          "edge_kind": "SignalWire"}))
    # endpoint is the ONE legal sort crossing: an edge filter over an object
    G.validate_goal_v1(G.exists("edges", {"kind": "endpoint", "side": "src",
                                          "where": PULSER}))
    ok3, d3 = raises(G.WRLM_GOAL_SORT, G.validate_goal_v1,
                     G.exists("edges", {"kind": "endpoint", "side": "src",
                                        "where": {"kind": "edge_kind_is",
                                                  "edge_kind": "SignalWire"}}))
    check("G3)  two-sorted: object atom in edge domain (and vice versa) is a "
          "SORT error; endpoint is the one legal crossing",
          ok1 and ok2 and ok3, "%s %s %s" % (d1, d2, d3))

    # ---------------------------------------------------------------- G4
    deep = SPINNER
    for _ in range(G.MAX_GOAL_DEPTH + 2):
        deep = {"kind": "filter_not", "arg": deep}
    ok1, d1 = raises(G.WRLM_GOAL_BOUNDS, G.validate_goal_v1,
                     G.exists("objects", deep))
    wide = {"kind": "all", "args": [G.exists("objects", SPINNER)
                                    for _ in range(G.MAX_GOAL_NODES)]}
    ok2, d2 = raises(G.WRLM_GOAL_BOUNDS, G.validate_goal_v1, wide)
    check("G4)  bounded: depth and node count both refuse -- this is what keeps "
          "the S baseline tractable", ok1 and ok2, "%s %s" % (d1, d2))

    # ---------------------------------------------------------------- G5
    a = G.exists("objects", SPINNER)
    b = G.exists("objects", PULSER)
    id_ab = G.goal_spec_id({"kind": "all", "args": [a, b]})
    id_ba = G.goal_spec_id({"kind": "all", "args": [b, a]})
    id_dup = G.goal_spec_id({"kind": "all", "args": [a, b, a, b, a]})
    notnot = {"kind": "not", "arg": {"kind": "not", "arg": a}}
    check("G5)  canonical identity: commutative reorder AND duplication seal to "
          "the SAME goal- id; double negation does NOT (documented caveat)",
          id_ab == id_ba == id_dup and G.goal_spec_id(notnot) != G.goal_spec_id(a),
          "%s / %s / %s" % (id_ab, id_ba, id_dup))

    # ---------------------------------------------------------------- G6
    ev = lambda node: G.evaluate_goal(node, WORLD)                # noqa: E731
    r = {
        "exists spinner": ev(G.exists("objects", SPINNER)) is True,
        "no mailbox": ev(G.none("objects", G.role("Mailbox"))) is True,
        "exactly 1 orb": ev(G.exactly("objects", ORB, 1)) is True,
        "forall obj has id": ev(G.forall("objects", {
            "kind": "filter_any", "args": [
                G.role(x) for x in ("Pulser", "Spinner", "Orb", "Relay")]})) is True,
        "pulser wired to spinner": ev(G.wired("SignalWire", PULSER, SPINNER)) is True,
        "orb NOT wired to pulser": ev(G.wired("SignalWire", ORB, PULSER)) is False,
        "spinner w=8": ev(G.exists("objects", {"kind": "filter_all", "args": [
            SPINNER, {"kind": "config_eq", "field": "w", "value": 8}]})) is True,
        "spinner w=9 absent": ev(G.exists("objects", {"kind": "filter_all", "args": [
            SPINNER, {"kind": "config_eq", "field": "w", "value": 9}]})) is False,
        "tuple config rotor": ev(G.exists("objects", {
            "kind": "config_eq", "field": "rotor", "value": [1, 0, 0, 0]})) is True,
        "relay has no edges": ev(G.exists("objects", {"kind": "filter_all", "args": [
            G.role("Relay"),
            {"kind": "degree", "direction": "out", "edge_kind": None,
             "cmp": "eq", "n": 0},
            {"kind": "degree", "direction": "in", "edge_kind": None,
             "cmp": "eq", "n": 0}]})) is True,
        "spinner in-degree 1 on SignalWire": ev(G.exists("objects", {
            "kind": "filter_all", "args": [SPINNER,
                {"kind": "degree", "direction": "in",
                 "edge_kind": "SignalWire", "cmp": "eq", "n": 1}]})) is True,
    }
    bad = [k for k, v in r.items() if not v]
    check("G6)  evaluation over the finite bounded world: %d/%d structural "
          "predicates correct" % (len(r) - len(bad), len(r)), not bad, str(bad))

    # ---------------------------------------------------------------- G7
    check("G7)  monoid identities: all[] is TRUE, any[] is FALSE",
          ev({"kind": "all", "args": []}) is True
          and ev({"kind": "any", "args": []}) is False)

    # ---------------------------------------------------------------- G8
    tw = {"object_id": "s1", "role": "Spinner",
          "static_config": {"configurable": True}}
    w2 = {"objects": [tw], "edges": []}
    as_bool = G.evaluate_goal(G.exists("objects", {
        "kind": "config_eq", "field": "configurable", "value": True}), w2)
    as_one = G.evaluate_goal(G.exists("objects", {
        "kind": "config_eq", "field": "configurable", "value": 1}), w2)
    check("G8)  strict scalar equality: True does NOT match 1 (Python's "
          "bool-is-int must not leak onto an identity spine)",
          as_bool is True and as_one is False)

    # ---------------------------------------------------------------- G9
    dangling = {"objects": [{"object_id": "p1", "role": "Pulser",
                             "static_config": {}}],
                "edges": [{"kind": "SignalWire", "src": "p1", "dst": "GONE"}]}
    try:
        tot = G.evaluate_goal(G.wired("SignalWire", PULSER, SPINNER),
                              dangling) is False
        # and total on junk shapes too
        G.evaluate_goal(G.exists("objects", SPINNER), {})
        G.evaluate_goal(G.exists("objects", SPINNER), {"objects": None})
        G.evaluate_goal(G.exists("objects", SPINNER), "not a world")
        err = None
    except Exception as e:                                        # noqa: BLE001
        tot, err = False, "%s: %s" % (type(e).__name__, e)
    check("G9)  evaluation is TOTAL: dangling endpoint and malformed worlds "
          "yield False, never an exception", tot, err or "")

    # ---------------------------------------------------------------- G10
    sealed = G.seal_goal(G.wired("SignalWire", PULSER, SPINNER))
    ok_imm, d_imm = raises(G.WRLM_SEALED_IMMUTABLE,
                           setattr, sealed, "_id", "goal-0")
    fresh = sealed.node
    fresh["kind"] = "any"
    reopened = G.open_sealed_goal(sealed.canonical_bytes,
                                  expect_id=sealed.goal_spec_id)
    ok_mis, d_mis = raises(G.WRLM_BAD_GOAL, G.open_sealed_goal,
                           sealed.canonical_bytes, expect_id="goal-" + "0" * 64)
    check("G10) sealed: immutable, id derived FROM the bytes, .node is a fresh "
          "copy, round-trip stable, wrong expect_id refused",
          ok_imm and ok_mis
          and sealed.node["kind"] == "count"
          and reopened == sealed
          and sealed.evaluate(WORLD) is True,
          "%s %s" % (d_imm, d_mis))

    # ---------------------------------------------------------------- G11
    ok1, d1 = raises(G.WRLM_BAD_GOAL, G.validate_goal_v1,
                     G.exactly("objects", SPINNER, True))
    ok2, d2 = raises(G.WRLM_BAD_GOAL, G.validate_goal_v1,
                     G.exactly("objects", SPINNER, -1))
    ok3, d3 = raises(G.WRLM_BAD_GOAL, G.validate_goal_v1, G.exists("objects", {
        "kind": "config_eq", "field": "w", "value": 1.5}))
    ok4, d4 = raises(G.WRLM_BAD_GOAL, G.validate_goal_v1,
                     G.exists("objects", G.role("Wizard")))
    check("G11) operand hygiene: bool-as-n, negative n, float value and unknown "
          "role all rejected", ok1 and ok2 and ok3 and ok4,
          "%s %s %s %s" % (d1, d2, d3, d4))

    # ---------------------------------------------------------------- G12
    g12 = {"kind": "all", "args": [G.wired("SignalWire", PULSER, SPINNER),
                                   G.exactly("objects", ORB, 1)]}
    b1, b2 = G.serialize_goal(g12), G.serialize_goal(g12)
    gid = G.goal_spec_id(g12)
    ok_bad, d_bad = raises(G.WRLM_BAD_GOAL, G.deserialize_goal, b"{not json")
    check("G12) deterministic: repeated serialization is byte-identical, id is "
          "stable, non-JSON bytes are a TYPED rejection",
          b1 == b2 and gid == "goal-" + __import__("hashlib").sha256(b1).hexdigest()
          and ok_bad, d_bad)

    # ---------------------------------------------------------------- G13
    # The battery above runs on a hand-written world, which only proves the
    # evaluator is self-consistent. This check runs it against the REAL frozen
    # Forge demo artifact, and first proves the fixture IS that world by
    # re-deriving `sem-` from its own bytes -- pure json+hashlib, no forge
    # import. `sem-` is sha256 over exactly these canonical bytes, so wrlm can
    # verify the fixture without depending on the layer that produced it.
    import hashlib
    import json
    fx = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "fixtures", "demo_world.artifact.json")
    demo = json.load(open(fx))
    canon = json.dumps(demo, sort_keys=True, separators=(",", ":")).encode()
    sem = "sem-" + hashlib.sha256(canon).hexdigest()
    dv = lambda node: G.evaluate_goal(node, demo)                 # noqa: E731
    RELAY, DOOR = G.role("Relay"), G.role("Door")
    real = {
        "2 pulsers": dv(G.exactly("objects", PULSER, 2)) is True,
        "1 spinner": dv(G.exactly("objects", SPINNER, 1)) is True,
        "1 orb": dv(G.exactly("objects", ORB, 1)) is True,
        "no mailbox": dv(G.none("objects", G.role("Mailbox"))) is True,
        "pulser -> relay": dv(G.wired("SignalWire", PULSER, RELAY)) is True,
        "relay -> spinner": dv(G.wired("SignalWire", RELAY, SPINNER)) is True,
        "spinner -> orb (socket)":
            dv(G.wired("SocketControl", SPINNER, ORB)) is True,
        "pulser -> door": dv(G.wired("SignalWire", PULSER, DOOR)) is True,
        # the demo drives the spinner THROUGH the relay, never directly
        "no direct pulser -> spinner":
            dv(G.wired("SignalWire", PULSER, SPINNER)) is False,
        "every door has exactly one signal in": dv(G.forall("objects", {
            "kind": "filter_any", "args": [
                {"kind": "filter_not", "arg": DOOR},
                {"kind": "degree", "direction": "in",
                 "edge_kind": "SignalWire", "cmp": "eq", "n": 1}]})) is True,
        # an Orb has no `out` port at all, so nothing may originate there
        "no edge originates at an Orb": dv(G.none("edges", {
            "kind": "endpoint", "side": "src", "where": ORB})) is True,
    }
    bad = [k for k, v in real.items() if not v]
    check("G13) against the REAL frozen demo artifact (%s, fixture verified by "
          "re-deriving sem- from its own bytes): %d/%d"
          % (sem[:16] + "...", len(real) - len(bad), len(real)),
          not bad and sem == ("sem-8ae91fe9cbc5fd086ce4356d587c40"
                              "3211e5c7b2b3ebdd316496367429ecfe4a"),
          "%s sem=%s" % (bad, sem))

    print()
    if FAILED:
        print("FAILED: %s" % ", ".join(FAILED))
        return 1
    print("PASS_GOALSPEC_V1 -- closed AST, two-sorted, bounded, sealed, total.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
