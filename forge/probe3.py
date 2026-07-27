"""probe3 -- C.4.3: the committed WRL projection vectors through Forge's
independent Python spine, via the new `wrl_projection` ingress adapter.

This is the "JS emit -> Python receive" leg. It asserts nothing about how the
bytes were produced; it re-establishes every transmitted claim locally, which
is the whole point of the wire form.

Run from a COPY of forge/:  PYTHONDONTWRITEBYTECODE=1 python3 probe3.py
"""
import json
import os
import sys

sys.dont_write_bytecode = True

import vector_files
import wrl_projection as P

HERE = os.path.dirname(os.path.abspath(__file__))

passed = 0
failed = 0


def ok(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("  ok   %-46s %s" % (name, detail))
    else:
        failed += 1
        print("  FAIL %-46s %s" % (name, detail))


def main():
    doc = vector_files.load("_vectors.json")
    print("vector set %s -- %d vectors\n" % (doc["vector_version"],
                                             len(doc["vectors"])))

    for vec in doc["vectors"]:
        name = vec["name"]
        wire = vec["wire"]
        print("[%s]" % name)

        # 1. the record parses exactly and is in canonical form
        try:
            rec = P.parse_canonical_projection_exactly(wire)
            ok("%s/parses-exactly" % name, True,
               rec["semantic_world_id"][:20] + "...")
        except P.ProjectionError as e:
            ok("%s/parses-exactly" % name, False, "%s %s" % (e.code, e))
            continue
        except Exception as e:  # noqa
            ok("%s/parses-exactly" % name, False,
               "%s: %s" % (type(e).__name__, e))
            continue

        # 2. full verification: every claim re-established locally
        try:
            adm = P.verify_runtime_projection(wire)
        except P.ProjectionError as e:
            ok("%s/verifies" % name, False, "%s %s" % (e.code, e))
            continue
        except Exception as e:  # noqa
            import traceback
            traceback.print_exc()
            ok("%s/verifies" % name, False,
               "%s: %s" % (type(e).__name__, e))
            continue

        ok("%s/verifies" % name, True, "")
        ok("%s/world-id-agrees" % name,
           adm.semantic_world_id == rec["semantic_world_id"],
           adm.semantic_world_id)
        ok("%s/view-id-agrees" % name,
           adm.execution_view_id == rec["execution_view_id"],
           adm.execution_view_id)
        ok("%s/bindings-count" % name,
           len(adm.relation_bindings) == len(rec["relation_bindings"]),
           "%d bindings" % len(adm.relation_bindings))
        ok("%s/executable" % name,
           isinstance(adm.execution_artifact, dict)
           and "edges" in adm.execution_artifact,
           "%d edges" % len(adm.execution_artifact.get("edges", [])))

        # 3. re-serialising the admission reproduces the wire byte-exactly
        try:
            again = P.serialize_runtime_projection(adm)
            ok("%s/round-trips" % name, again == wire,
               "" if again == wire else "%d vs %d bytes" % (len(again),
                                                            len(wire)))
        except Exception as e:  # noqa
            ok("%s/round-trips" % name, False,
               "%s: %s" % (type(e).__name__, e))
        print("")

    print("\n%d passed, %d failed" % (passed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
