"""probe4 -- the negative corpus for the projection wire (C.5.4, run here
against the Python verifier).

A positive vector proves a verifier can agree. It does not prove the verifier
is CHECKING: a function that returned the record unread would pass every
positive vector in the set. Each case below takes an honest record, changes
exactly one thing, and requires a refusal.

Two classes are worth naming.

  * The reordered bindings. Every id in the list stays correct and every
    binding stays individually true; only the ORDER lies. Order is derived
    from the semantic artifact, so the canonical bytes catch it -- but nothing
    that checked bindings as a SET would.

  * The rounding attempt. A receiver whose reader narrows a 2^63-1 rotor lane
    does not silently admit a different world; it computes a different world
    id and is refused. The exactness rule is not only about fidelity, it is
    about what an inexact peer is able to claim.

Run from a COPY of forge/:  PYTHONDONTWRITEBYTECODE=1 python3 probe4.py
"""
import copy
import json
import os
import sys

sys.dont_write_bytecode = True

import wrl_projection as P

HERE = os.path.dirname(os.path.abspath(__file__))

passed = 0
failed = 0


def refuses(name, wire, expect_codes):
    """Require a typed refusal, and require the CODE to be one of the ones
    named. A refusal in the wrong vocabulary is how the exactness defect hid:
    it was loud, and it said WRL_NUMERIC_RANGE about a number that was in
    range."""
    global passed, failed
    try:
        P.verify_runtime_projection(wire)
    except P.ProjectionError as e:
        code = getattr(e, "code", "?")
        if code in expect_codes:
            passed += 1
            print("  ok   %-42s %s" % (name, code))
        else:
            failed += 1
            print("  FAIL %-42s refused as %s, wanted one of %s"
                  % (name, code, "/".join(expect_codes)))
        return
    except Exception as e:  # noqa
        failed += 1
        print("  FAIL %-42s untyped %s: %s" % (name, type(e).__name__, e))
        return
    failed += 1
    print("  FAIL %-42s ADMITTED" % name)


def admits(name, wire):
    global passed, failed
    try:
        P.verify_runtime_projection(wire)
        passed += 1
        print("  ok   %-42s admitted" % name)
    except Exception as e:  # noqa
        failed += 1
        print("  FAIL %-42s refused: %s" % (name, e))


def main():
    global passed, failed
    doc = json.load(open(os.path.join(HERE, "_vectors.json")))
    by_name = {v["name"]: v for v in doc["vectors"]}

    # A V2 vector, so the tampers reach named relations and revisions, and a
    # BigInt vector for the rounding case.
    base = by_name["named-relations"]["wire"]
    big = by_name["bigint-rotor"]["wire"]
    rec = P.parse_canonical_projection_exactly(base)

    def wire_of(mutate):
        r = copy.deepcopy(rec)
        mutate(r)
        return P._canonical_bytes(r)

    print("control\n")
    admits("the-untouched-record", base)
    admits("the-untouched-bigint-record", big)

    print("\nlying claims\n")

    def flip_hex(s):
        """Change one hex digit of a `sem-`/`rel-`/`rev-` id, keeping shape."""
        i = len(s) - 1
        return s[:i] + ("b" if s[i] != "b" else "c")

    refuses("a-lying-semantic-world-id",
            wire_of(lambda r: r.__setitem__(
                "semantic_world_id", flip_hex(r["semantic_world_id"]))),
            {"WRL_SEMANTIC_ID_MISMATCH"})

    refuses("a-lying-execution-view-id",
            wire_of(lambda r: r.__setitem__(
                "execution_view_id", flip_hex(r["execution_view_id"]))),
            {"WRL_PROJECTION_MISMATCH"})

    print("\nthe bindings\n")

    refuses("reordered-relation-bindings",
            wire_of(lambda r: r["relation_bindings"].reverse()),
            {"WRL_PROJECTION_MISMATCH"})

    refuses("a-changed-relation-id",
            wire_of(lambda r: r["relation_bindings"][0].__setitem__(
                "relation_id", flip_hex(r["relation_bindings"][0]["relation_id"]))),
            {"WRL_PROJECTION_MISMATCH"})

    refuses("a-changed-revision-id",
            wire_of(lambda r: r["relation_bindings"][0].__setitem__(
                "revision_id", flip_hex(r["relation_bindings"][0]["revision_id"]))),
            {"WRL_PROJECTION_MISMATCH"})

    refuses("a-changed-legacy-edge",
            wire_of(lambda r: r["relation_bindings"][0]["legacy_edge"].__setitem__(
                "dst", "nowhere")),
            {"WRL_PROJECTION_MISMATCH"})

    print("\nthe record's shape\n")

    refuses("an-extra-field",
            wire_of(lambda r: r.__setitem__("execution_artifact", {})),
            {"WRL_BAD_PROJECTION"})

    refuses("a-missing-field",
            wire_of(lambda r: r.pop("execution_view_id")),
            {"WRL_BAD_PROJECTION"})

    refuses("an-unknown-projection-version",
            wire_of(lambda r: r.__setitem__("projection_version",
                                            "wrl.projection.2")),
            {"WRL_BAD_PROJECTION"})

    print("\nthe bytes themselves\n")

    def edited(name, before, after, wire=None):
        """A byte-level tamper that REFUSES TO BE A NO-OP.

        The first version of this file wrote a duplicate key by replacing
        `{"projection_version"` -- and the keys on this wire are sorted, so
        the record begins with `execution_view_id`, the replace matched
        nothing, and the case handed the verifier the honest record and asked
        it to refuse. It reported a failure, which was luck: the same mistake
        pointed the other way is a negative test that passes while asserting
        nothing, and that one has now cost me twice. A tamper that did not
        change the bytes is a broken fixture, and a broken fixture must be a
        named red rather than a verdict about the code under test.
        """
        src = base if wire is None else wire
        out = src.replace(before, after, 1)
        if out == src:
            global failed
            failed += 1
            print("  FAIL %-42s broken fixture: %r is not in the record"
                  % (name, before[:40]))
            return None
        return out

    # A duplicate key. `json.loads` keeps the LAST one, so a permissive reader
    # sees a record whose world id was overwritten after the fact -- and the
    # honest first occurrence is the one it discards.
    dup = edited("a-duplicate-json-key", '{"execution_view_id"',
                 '{"semantic_world_id":"sem-0","execution_view_id"')
    if dup:
        refuses("a-duplicate-json-key", dup, {"WRL_BAD_PROJECTION"})

    ws = edited("insignificant-whitespace", ",", ", ")
    if ws:
        refuses("insignificant-whitespace", ws, {"WRL_BAD_PROJECTION"})

    refuses("trailing-bytes", base + "\n", {"WRL_BAD_PROJECTION"})

    # Key order. Re-render the same record with keys in a different order:
    # it denotes exactly the honest record and is still not the record.
    plain = json.loads(base)
    reordered = json.dumps({k: plain[k] for k in reversed(list(plain))},
                           separators=(",", ":"), ensure_ascii=False)
    if reordered == base:
        failed += 1
        print("  FAIL %-42s broken fixture: reorder was a no-op"
              % "noncanonical-key-order")
    else:
        refuses("noncanonical-key-order", reordered, {"WRL_BAD_PROJECTION"})

    print("\nexactness\n")

    # The rounding attempt: replace the exact lane with what a lossy reader
    # would have produced. The record stays well-formed and canonical; it is
    # simply a different world, and says a world id that is now false.
    rounded = big.replace("9223372036854775807", "9223372036854776000")
    refuses("an-unsafe-integer-rounded", rounded,
            {"WRL_SEMANTIC_ID_MISMATCH", "WRL_NUMERIC_RANGE"})

    refuses("a-non-integral-number",
            big.replace("9223372036854775807", "92233720368547758.07"),
            {"WRL_BAD_PROJECTION"})

    print("\n%d passed, %d failed" % (passed, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
