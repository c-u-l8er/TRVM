"""Emit the shared negative corpus for the projection wire (C.5.4).

`probe4` proved these tampers are refused by the PYTHON verifier, but it holds
them as Python lambdas on a Forge branch, where the JS suite cannot see them.
This lifts them into a committed file both implementations read, so that
"Forge refuses a reordered binding" and "the browser refuses a reordered
binding" become the same claim about the same bytes rather than two similar
claims about two records.

TWO DECISIONS, both about not repeating a mistake this corpus already made.

  * Each vector stores the FINAL TAMPERED BYTES, not an edit recipe. A recipe
    is a program, and a recipe that silently matches nothing is exactly the
    broken fixture that has now cost me three times -- most recently when a
    duplicate-key tamper searched for `{"projection_version"` on a wire whose
    keys are sorted. Bytes cannot fail to apply.

  * A stored literal can still be a no-op against its base, so every vector
    names its `base` and this generator REFUSES TO EMIT one whose wire equals
    that base. The check is recorded in the file as well, so a consumer can
    re-run it rather than trust that I ran it.

On the refusal CODE: each vector carries the codes the Python verifier actually
produced. Whether a code is normative -- whether an implementation that refuses
correctly but names the refusal differently is conformant -- is the open
question in the handoff, and this file does not presume the answer. It records
what was observed; the consumers assert the REFUSAL and report code agreement
separately.

Run from a COPY of forge/:
    PYTHONDONTWRITEBYTECODE=1 python3 gen_negative_vectors.py <out.json>
"""
import copy
import json
import os
import sys

sys.dont_write_bytecode = True

import wrl_projection as P

HERE = os.path.dirname(os.path.abspath(__file__))

SET_ID = "wrl.projection-negative-vectors.1"


def flip_hex(s):
    """Change one hex digit of a `sem-`/`rel-`/`rev-` id, keeping its shape.

    Shape-preserving on purpose: a malformed id would be refused by the shape
    gate and would never reach the recomputation that is the thing under test.
    """
    i = len(s) - 1
    return s[:i] + ("b" if s[i] != "b" else "c")


def build(base_wire, big_wire):
    """Return the corpus as (name, why, base_key, wire) tuples."""
    rec = P.parse_canonical_projection_exactly(base_wire)
    out = []

    def structural(name, why, mutate):
        r = copy.deepcopy(rec)
        mutate(r)
        out.append((name, why, "named-relations", P._canonical_bytes(r)))

    def literal(name, why, base_key, wire):
        out.append((name, why, base_key, wire))

    # -- lying claims ------------------------------------------------------
    structural(
        "a-lying-semantic-world-id",
        "The record asserts a world id its own artifact does not hash to.",
        lambda r: r.__setitem__("semantic_world_id",
                                flip_hex(r["semantic_world_id"])))

    structural(
        "a-lying-execution-view-id",
        "The V2->V1 projection is derived, so a sender's view id is a claim "
        "and not a fact; this one is false.",
        lambda r: r.__setitem__("execution_view_id",
                                flip_hex(r["execution_view_id"])))

    # -- the bindings ------------------------------------------------------
    structural(
        "reordered-relation-bindings",
        "THE TAMPER THAT MOVES NO IDENTIFIER. Every id stays correct and "
        "every binding stays individually true; only the ORDER lies. Order is "
        "derived from the semantic artifact, so canonical bytes catch it -- "
        "but nothing that checked the bindings as a SET would.",
        lambda r: r["relation_bindings"].reverse())

    structural(
        "a-changed-relation-id",
        "A relation id is derived from its allocation, never transmitted as "
        "authority.",
        lambda r: r["relation_bindings"][0].__setitem__(
            "relation_id", flip_hex(r["relation_bindings"][0]["relation_id"])))

    structural(
        "a-changed-revision-id",
        "Likewise a revision id, which is derived from the canonical "
        "revision.",
        lambda r: r["relation_bindings"][0].__setitem__(
            "revision_id", flip_hex(r["relation_bindings"][0]["revision_id"])))

    structural(
        "a-changed-legacy-edge",
        "The legacy edge is the JOIN KEY between a binding and the derived V1 "
        "artifact -- the field that must not be zipped by index.",
        lambda r: r["relation_bindings"][0]["legacy_edge"].__setitem__(
            "dst", "nowhere"))

    # -- the record's shape ------------------------------------------------
    structural(
        "an-extra-field",
        "`execution_artifact` is the field the ruling kept OFF the wire. A "
        "receiver that accepted one has stopped deriving it.",
        lambda r: r.__setitem__("execution_artifact", {}))

    structural(
        "a-missing-field",
        "All five fields are required; absence is not a default.",
        lambda r: r.pop("execution_view_id"))

    structural(
        "an-unknown-projection-version",
        "An unknown version must refuse rather than be read hopefully.",
        lambda r: r.__setitem__("projection_version", "wrl.projection.2"))

    # -- the bytes themselves ----------------------------------------------
    # A duplicate key: `JSON.parse` and `json.loads` both keep the LAST, so a
    # permissive reader sees a world id overwritten after the fact and throws
    # away the honest first occurrence.
    literal(
        "a-duplicate-json-key",
        "A permissive reader keeps the last of two keys and discards the "
        "honest one; the exact reader refuses the bytes.",
        "named-relations",
        base_wire.replace('{"execution_view_id"',
                          '{"semantic_world_id":"sem-0","execution_view_id"',
                          1))

    literal(
        "insignificant-whitespace",
        "No whitespace is insignificant when the bytes ARE the identity.",
        "named-relations",
        base_wire.replace(",", ", ", 1))

    literal(
        "trailing-bytes",
        "A record is the whole input, not a prefix of it.",
        "named-relations",
        base_wire + "\n")

    plain = json.loads(base_wire)
    literal(
        "noncanonical-key-order",
        "Denotes exactly the honest record, and is still not the record.",
        "named-relations",
        json.dumps({k: plain[k] for k in reversed(list(plain))},
                   separators=(",", ":"), ensure_ascii=False))

    # -- exactness ---------------------------------------------------------
    literal(
        "an-unsafe-integer-rounded",
        "What a lossy reader WOULD have produced from a 2^63-1 rotor lane. "
        "The record stays well-formed and canonical; it is simply a different "
        "world, and now says a world id that is false. This is the C.4.1 "
        "defect turned into a test.",
        "bigint-rotor",
        big_wire.replace("9223372036854775807", "9223372036854776000", 1))

    literal(
        "a-non-integral-number",
        "A rotor lane is an integer; a fraction is not a narrower integer.",
        "bigint-rotor",
        big_wire.replace("9223372036854775807", "92233720368547758.07", 1))

    return out


def main():
    dest = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        HERE, "projection-negative-vectors.json")

    pos = json.load(open(os.path.join(HERE, "_vectors.json")))
    bases = {v["name"]: v["wire"] for v in pos["vectors"]}

    rows = build(bases["named-relations"], bases["bigint-rotor"])

    vectors = []
    broken = []
    for name, why, base_key, wire in rows:
        # THE NO-OP GATE. A tamper that did not change the bytes is a broken
        # fixture, and a broken fixture emitted into a corpus is worse than a
        # failing test: it is a case that passes while asserting nothing.
        if wire == bases[base_key]:
            broken.append(name)
            continue

        # Record the refusal this verifier actually produced. Observed, not
        # asserted -- see the module docstring on the open question.
        try:
            P.verify_runtime_projection(wire)
        except P.ProjectionError as e:
            codes = [getattr(e, "code", "?")]
        except Exception as e:  # noqa
            broken.append("%s (untyped %s)" % (name, type(e).__name__))
            continue
        else:
            broken.append("%s (ADMITTED)" % name)
            continue

        vectors.append({
            "name": name,
            "why": why,
            "base": base_key,
            "wire": wire,
            "refusal_codes": codes,
        })

    if broken:
        print("REFUSING TO EMIT -- %d broken fixture(s):" % len(broken))
        for b in broken:
            print("  %s" % b)
        return 1

    doc = {
        "vector_set": SET_ID,
        "note": (
            "Negative vectors for the D8.19 projection wire. Each entry is a "
            "complete tampered record, stored as final bytes rather than as "
            "an edit recipe, because a recipe that matches nothing is a "
            "fixture that passes while asserting nothing. A consumer MUST "
            "check that `wire` differs from the named `base` in "
            "projection-vectors.json before trusting a refusal, and MUST "
            "require a refusal for every vector. `refusal_codes` records what "
            "the reference verifier produced; whether a code is normative is "
            "an open question, so a consumer should report code disagreement "
            "separately from the refusal itself."),
        "base_vectors": "projection-vectors.json",
        "vectors": vectors,
    }
    with open(dest, "w") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s -- %d negative vectors" % (dest, len(vectors)))
    for v in vectors:
        print("  %-34s %-16s %s" % (v["name"], v["base"],
                                    ",".join(v["refusal_codes"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
