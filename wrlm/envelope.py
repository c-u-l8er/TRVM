"""LoweredSourceEnvelopeV1 -- the atomic (source, result) pair, and what binds it.

This module exists because of a hole found by review that the R-battery did not
catch. The old signature was::

    capture(lower_result, artifact, source="anything at all")

and it succeeded. The record came back carrying the *real* `sem-` next to an
*unrelated* source string, revalidated cleanly on reopen, and -- worst of all --
produced a perfectly sealed `case-` id. A crossed pair is therefore not a
cosmetic problem: `case-` keys on presented source, so a crossed record mints a
task identity that is internally consistent and externally false. The model
would be shown one world's text and scored against another world's structure,
and nothing downstream could tell.

What the old code actually proved was::

    the LowerResultV1 agrees with the artifact
    AND some non-empty string was supplied

What it *claimed* was that the source produced the result. Those are different
statements and only one of them was true.

Two honest ways to close it
---------------------------

**Asserted.** Bundle the source and the result together at the moment the engine
runs, seal the pair, and let consumers inherit the binding from whoever sealed
it. The trust boundary is the publisher. This is cheap and works with no engine
present.

**Proved.** Re-run the lowering on the envelope's own source and check that it
reproduces the same `sem-`. This *demonstrates* production rather than inheriting
someone's word for it. It needs a live engine.

Both are legitimate; they are not equally strong, and the difference must not be
papered over. So a record carries `binding.kind`, and it is either `"proved"` or
`"asserted"` -- never merely implied. A corpus built from asserted records is a
different epistemic object from one built from proved records, and a downstream
consumer is entitled to know which one it has.

`wrlm` still imports nothing from the engine. Proof arrives by *injection*: the
caller who has an engine passes `lower=forge_api.lower_source`. That keeps the
zero-dependency invariant intact while making the strong path available exactly
where it is possible -- which is the same argument `WorldRecordV1` already makes
about capture time.

On `source_sha256`
------------------

It seals the envelope against in-transit edits: change `source` and the hash
stops matching. It does **not** prove production, and this module never says it
does. It is a checksum, and it is labelled as one.

Note that the hash is stricter than semantic equality. Appending a newline to WRL
source leaves `sem-` unchanged but changes `source_sha256`. That is correct here:
`case-` keys on *presented* source, so two spellings of the same world are two
different things to ask a model, and the envelope must be able to tell them apart.
"""

import hashlib
import json

from .errors import fail

ENVELOPE_VERSION = "wrlm.envelope.v1"

WRLM_BAD_ENVELOPE = "WRLM_BAD_ENVELOPE"          # malformed / wrong shape
WRLM_ENVELOPE_CROSSED = "WRLM_ENVELOPE_CROSSED"  # source did not produce result

ENVELOPE_FIELDS = ("envelope_version", "source", "source_sha256", "lower_result",
                   "publisher", "publisher_version")

BINDING_PROVED = "proved"       # re-lowered here; production demonstrated
BINDING_ASSERTED = "asserted"   # inherited from the sealing publisher
BINDING_KINDS = (BINDING_PROVED, BINDING_ASSERTED)


def source_sha256(source):
    """The envelope checksum. Bytes in, `sha256-<hex>` out."""
    if not isinstance(source, str):
        fail(WRLM_BAD_ENVELOPE, "source must be a string, got %s"
             % type(source).__name__, "source")
    return "sha256-" + hashlib.sha256(source.encode("utf-8")).hexdigest()


def seal_envelope(source, lower_result, publisher, publisher_version):
    """Seal a source and the result of lowering IT into one atomic object.

    Call this from the code that just ran the engine, with the same `source`
    string that was passed in. Everything downstream then handles one object
    instead of two loose arguments that can drift apart.

    `publisher` names who is making the claim. It is not decoration: for an
    `"asserted"` binding it *is* the trust boundary, so it has to be recorded.
    """
    if not isinstance(source, str) or not source.strip():
        fail(WRLM_BAD_ENVELOPE,
             "an envelope needs the non-empty source that was lowered", "source")
    if not isinstance(lower_result, dict):
        fail(WRLM_BAD_ENVELOPE, "lower_result must be an object, got %s"
             % type(lower_result).__name__, "lower_result")
    for name, val in (("publisher", publisher),
                      ("publisher_version", publisher_version)):
        if not isinstance(val, str) or not val.strip():
            fail(WRLM_BAD_ENVELOPE,
                 "%s must be a non-empty string -- an asserted binding is only "
                 "as good as the named publisher" % name, name)
    return {
        "envelope_version": ENVELOPE_VERSION,
        "source": source,
        "source_sha256": source_sha256(source),
        "lower_result": lower_result,
        "publisher": publisher,
        "publisher_version": publisher_version,
    }


def validate_envelope_v1(envelope):
    """Closed shape, and the checksum re-derived rather than believed."""
    if not isinstance(envelope, dict):
        fail(WRLM_BAD_ENVELOPE, "expected an object, got %s"
             % type(envelope).__name__, "envelope")
    have, want = set(envelope), set(ENVELOPE_FIELDS)
    extra, missing = sorted(have - want), sorted(want - have)
    if extra:
        fail(WRLM_BAD_ENVELOPE, "unknown key(s): %s" % ", ".join(extra),
             "envelope")
    if missing:
        fail(WRLM_BAD_ENVELOPE, "missing key(s): %s" % ", ".join(missing),
             "envelope")
    if envelope["envelope_version"] != ENVELOPE_VERSION:
        fail(WRLM_BAD_ENVELOPE, "unsupported envelope version %r"
             % (envelope["envelope_version"],), "envelope_version")
    if not isinstance(envelope["source"], str) or not envelope["source"].strip():
        fail(WRLM_BAD_ENVELOPE, "source must be a non-empty string", "source")
    if not isinstance(envelope["lower_result"], dict):
        fail(WRLM_BAD_ENVELOPE, "lower_result must be an object, got %s"
             % type(envelope["lower_result"]).__name__, "lower_result")
    derived = source_sha256(envelope["source"])
    if derived != envelope["source_sha256"]:
        fail(WRLM_BAD_ENVELOPE,
             "the sealed source hashes to %s but the envelope claims %s; the "
             "source was edited after sealing" % (derived,
                                                  envelope["source_sha256"]),
             "source_sha256")
    return envelope


def prove_envelope(envelope, lower):
    """Demonstrate that the envelope's source really does produce its result.

    `lower` is the engine entry point, INJECTED rather than imported -- `wrlm`
    depends on no engine, and the one caller who has one can hand it over.

    The comparison is on `semantic_artifact_id`, which is exactly the claim being
    checked: *this source names this world*. It deliberately does not compare
    whole payloads. A newer engine may report a different `engine_version` for
    the same world, and refusing that would punish the honest case; `sem-` is
    version-stable by construction, which is the entire point of a frozen
    identity spine.
    """
    validate_envelope_v1(envelope)
    if not callable(lower):
        fail(WRLM_BAD_ENVELOPE, "lower must be callable, got %s"
             % type(lower).__name__, "lower")
    fresh = lower(envelope["source"])
    if not isinstance(fresh, dict):
        fail(WRLM_BAD_ENVELOPE, "lower returned %s, not a LowerResultV1"
             % type(fresh).__name__, "lower")
    claimed = envelope["lower_result"].get("semantic_artifact_id")
    got = fresh.get("semantic_artifact_id")
    if got != claimed:
        fail(WRLM_ENVELOPE_CROSSED,
             "re-lowering the sealed source produces %s, but the sealed result "
             "reports %s; this source did not produce this result" % (got,
                                                                      claimed),
             "source")
    return envelope


def binding_block(envelope, kind):
    """The provenance block a `WorldRecordV1` stores.

    Kept as one nested block rather than scattered flat fields because these are
    precisely the epistemically loaded values -- how strong is this record, and
    on whose say-so -- and they should be read together or not at all.
    """
    if kind not in BINDING_KINDS:
        fail(WRLM_BAD_ENVELOPE, "binding kind must be one of %s, got %r"
             % (list(BINDING_KINDS), kind), "binding.kind")
    return {"kind": kind,
            "source_sha256": envelope["source_sha256"],
            "publisher": envelope["publisher"],
            "publisher_version": envelope["publisher_version"]}


def serialize_envelope(envelope):
    validate_envelope_v1(envelope)
    return json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode()


def deserialize_envelope(blob):
    if not isinstance(blob, (str, bytes, bytearray)):
        fail(WRLM_BAD_ENVELOPE, "envelope bytes must be str or bytes, got %s"
             % type(blob).__name__)
    try:
        env = json.loads(blob.decode() if isinstance(blob, bytes) else blob)
    except (ValueError, UnicodeDecodeError) as exc:
        fail(WRLM_BAD_ENVELOPE, "not decodable JSON: %s" % exc)
    return validate_envelope_v1(env)
