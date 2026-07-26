"""Build the captured world pool the generator batteries run against.

This is the ONLY script in `wrlm/` that touches the engine, and it is not part of
the package: it runs once, with a live Forge, and writes fixtures. Everything
else -- generator, coverage, families -- consumes what this produces and never
imports forge at all. That separation is the whole architecture of step 2: an
engine is needed to *capture* a world, never to *use* one.

Run from anywhere:

    PYTHONDONTWRITEBYTECODE=1 python3 -B wrlm/tools/build_pool.py

It writes `wrlm/fixtures/pool.json`: a list of `{source, lower_result, artifact}`
triples spanning the size buckets and topologies the coverage spec cares about.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WRLM = os.path.dirname(HERE)
TRVM = os.path.dirname(WRLM)
sys.path.insert(0, os.path.join(TRVM, "forge"))

HEAD = "profile forge.world.core.v1\n\n"


def chain(n_pulser, n_relay, spinners=0, doors=0, orbs=0):
    """A world built from independent pulser->relay->... chains.

    Kept mechanical rather than clever: the pool needs to span sizes and shapes
    predictably, and a generator that is being *tested* should not also be the
    thing that invented its own inputs.
    """
    decl, wire = [], []
    for i in range(n_pulser):
        decl.append("[pulser:p%d](every %d){sig_out}" % (i, 2 + (i % 3)))
    for i in range(n_relay):
        decl.append("[relay:r%d]{sig_in, sig_out}" % i)
    for i in range(spinners):
        decl.append("[spinner:s%d](w=16, n=8, rotor=quarter_turn_z, "
                    "configurable){sig_in, socket}" % i)
    for i in range(orbs):
        decl.append("[orb:o%d]{pose}" % i)
    for i in range(doors):
        decl.append("[door:d%d]{sig_in}" % i)

    # Each sink takes at most one signal in, so wire strictly one-to-one.
    srcs = ["p%d" % i for i in range(n_pulser)]
    sinks = (["r%d" % i for i in range(n_relay)]
             + ["s%d" % i for i in range(spinners)]
             + ["d%d" % i for i in range(doors)])
    for s, d in zip(srcs, sinks):
        wire.append("[%s] --sig--> [%s]" % (s, d))
    # relays feed whatever is left over after the pulsers ran out
    left = sinks[len(srcs):]
    for i, d in enumerate(left):
        if i < n_relay:
            wire.append("[r%d] --sig--> [%s]" % (i, d))
    for i in range(min(spinners, orbs)):
        wire.append("[s%d] --socket--> [o%d]" % (i, i))
    return HEAD + "\n".join(decl) + "\n\n" + "\n".join(wire) + "\n"


DEMO = (HEAD
        + "[pulser:p0](every 2){sig_out}\n"
        + "[relay:r0]{sig_in, sig_out}\n"
        + "[spinner:sp](w=16, n=8, rotor=quarter_turn_z, configurable)"
          "{sig_in, socket}\n"
        + "[orb:ob]{pose}\n"
        + "[pulser:p1](once at 1){sig_out}\n"
        + "[door:d0]{sig_in}\n\n"
        + "[pulser:p0] --sig--> [relay:r0]\n"
        + "[relay:r0] --sig--> [spinner:sp]\n"
        + "[spinner:sp] --socket--> [orb:ob]\n"
        + "[pulser:p1] --sig--> [door:d0]\n")

def edit_variants():
    """Worlds that differ from a pool sibling by exactly one or two edits.

    Without these the pool spans sizes but not *distances*, and the budget-1 and
    budget-2 cells would sit empty forever -- not because they are hard, but
    because no two captured worlds happened to be that close together. A pool is
    an input to coverage, so gaps in the pool become gaps in the corpus."""
    base = chain(1, 0, doors=1)                      # p0(every 2) -> d0
    return [
        # +1 config edit
        ("v_cfg1", base.replace("(every 2)", "(every 3)")),
        # +1 object (an unwired orb is legal and changes nothing else)
        ("v_add1", base.replace("\n\n[p0]", "\n[orb:o9]{pose}\n\n[p0]")),
        # +2: config and object together
        ("v_two", base.replace("(every 2)", "(every 4)")
                      .replace("\n\n[p0]", "\n[orb:o9]{pose}\n\n[p0]")),
        # a small world one wire away from a sibling
        ("v_small_cfg", chain(2, 2, doors=2).replace("(every 2)", "(every 5)")),
        ("v_small_orb", chain(2, 2, doors=2).replace(
            "\n\n[p0]", "\n[orb:o9]{pose}\n\n[p0]")),
        ("v_med_cfg", chain(3, 3, spinners=2, orbs=2, doors=2).replace(
            "(every 2)", "(every 6)")),
        ("v_med_orb", chain(3, 3, spinners=2, orbs=2, doors=2).replace(
            "\n\n[p0]", "\n[orb:o9]{pose}\n\n[p0]")),
        ("v_large_cfg", chain(6, 6, spinners=3, orbs=3, doors=4).replace(
            "(every 2)", "(every 7)")),
        ("v_large_orb", chain(6, 6, spinners=3, orbs=3, doors=4).replace(
            "\n\n[p0]", "\n[orb:o9]{pose}\n\n[p0]")),
    ]


CANDIDATES = [
    ("demo", DEMO),
    # tiny 2-4
    ("tiny_pd", chain(1, 0, doors=1)),
    ("tiny_prd", chain(1, 1, doors=1)),
    ("tiny_pso", chain(1, 0, spinners=1, orbs=1)),
    # small 5-8
    ("small_2chain", chain(2, 2, doors=2)),
    ("small_spin2", chain(2, 1, spinners=1, orbs=1, doors=1)),
    ("small_relays", chain(2, 3, doors=2)),
    # medium 9-16
    ("medium_a", chain(3, 3, spinners=2, orbs=2, doors=2)),
    ("medium_b", chain(4, 4, spinners=1, orbs=1, doors=3)),
    ("medium_c", chain(5, 5, doors=5)),
    # large 17-32
    ("large_a", chain(6, 6, spinners=3, orbs=3, doors=4)),
    ("large_b", chain(8, 8, spinners=2, orbs=2, doors=6)),
]


def main():
    import forge_api
    import spinner_bench as SB
    sys.path.insert(0, TRVM)
    from wrlm import envelope as E
    from wrlm import worldrecord as R

    pool, records, skipped = [], [], []
    for name, src in CANDIDATES + edit_variants():
        payload = forge_api.lower_source(src)
        if not payload.get("ok"):
            skipped.append((name, payload.get("error"),
                            [d.get("code") for d in payload.get("diagnostics")
                             or []]))
            continue
        artifact = SB._prog(src).sealed_artifact.artifact
        n = len(artifact["objects"])
        pool.append({"name": name, "n_objects": n, "source": src,
                     "lower_result": payload, "artifact": artifact})
        # Capture with the binding PROVED: the engine is right here, so there is
        # no reason to ship a corpus that only inherits someone's word for it.
        env = E.seal_envelope(src, payload, "wrlm.tools.build_pool",
                              forge_api.ENGINE_API_VERSION)
        records.append(R.capture(env, artifact, forge_api.lower_source))
        print("  ok   %-14s %2d objects  %s" % (name, n,
                                                payload["semantic_artifact_id"]))
    for name, err, codes in skipped:
        print("  SKIP %-14s %s %s" % (name, err, codes))

    seen, uniq = set(), []
    for r in records:
        if r["semantic_id"] not in seen:
            seen.add(r["semantic_id"])
            uniq.append(r)

    out = os.path.join(WRLM, "fixtures", "pool.json")
    with open(out, "w") as fh:
        json.dump(pool, fh, sort_keys=True, indent=1)
    rout = os.path.join(WRLM, "fixtures", "pool_records.json")
    with open(rout, "w") as fh:
        json.dump(uniq, fh, sort_keys=True, indent=1)
    print("\nwrote %s  (%d worlds)" % (out, len(pool)))
    print("wrote %s  (%d records, all binding=proved)" % (rout, len(uniq)))
    return 0 if len(uniq) >= 10 else 1


if __name__ == "__main__":
    sys.exit(main())
