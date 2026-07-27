"""probe6 -- C.5.2 producer half: Python emits projections from SOURCE.

probe3 verified bytes that JS produced. That direction alone can be satisfied
by a careful reader, so it does not establish that Forge can SPEAK the wire --
only that it can listen. Here Forge starts from WRL text, lowers it with its
own frozen parser, derives the projection with the new adapter, and serialises.

The output is written to `python-wire.json` for the JS side to verify
(`probe6.mjs`). It is deliberately NOT compared against the committed vectors
here: this file's job is to produce, and letting the producer grade itself is
how two implementations agree on being wrong together.

Only V1 sources appear. Forge's parser has no V2 surface, and inventing one
here to widen a test would be building the thing the ruling asked to keep out
of the frozen reader.

Run from a COPY of forge/:  PYTHONDONTWRITEBYTECODE=1 python3 probe6.py
"""
import json
import os
import sys

sys.dont_write_bytecode = True

import wrl_ir as WI
import wrl_projection as P
import wrl_sugar as SG

HERE = os.path.dirname(os.path.abspath(__file__))

V1_SOURCES = ("pinned-fixture", "starter-world", "bigint-rotor")


def main():
    doc = json.load(open(os.path.join(HERE, "_vectors.json")))
    by_name = {v["name"]: v for v in doc["vectors"]}

    out = {"producer": "forge/wrl_projection.py (python)", "wires": []}
    for name in V1_SOURCES:
        src = by_name[name]["source"]
        prog = WI.lower_program(SG.desugar_core(src), WI.parse_wrl_core)
        adm = P.derive_runtime_projection(prog.artifact)
        wire = P.serialize_runtime_projection(adm)
        out["wires"].append({"name": name, "source": src, "wire": wire})
        print("  emitted %-16s %s (%d bytes)"
              % (name, adm.semantic_world_id[:24] + "...", len(wire)))

    path = os.path.join(HERE, "python-wire.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote %s -- verify it with:  node probe6.mjs" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
