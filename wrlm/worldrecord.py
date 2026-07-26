"""WorldRecordV1 -- a sealed world, captured once, verified, then usable offline.

This is the object that closes a hole `TaskBundleV1` cannot close by itself.

A task says `base_world = {semantic_id, source}`. Nothing inside a *pure*
validator can check that those two agree: deciding whether this source lowers to
that `sem-` requires the engine. So the pair is, on its own, an unverifiable
claim sitting at the base of every task -- and "invalid source paired with some
other world's `sem-`" is precisely the internally-contradictory bundle the
repair-family discussion warned about.

The fix is not to weaken `base_world`. It is to move verification to the one
moment someone *does* have the engine: capture time.

    live Forge caller  --lower_source-->  LowerResultV1
                                              |
                                     capture + verify  (HERE, once)
                                              |
                                        WorldRecordV1
                                              |
                        offline generation, no engine present, forever after

A record is only constructible if every binding holds:

  1. the artifact's own bytes derive `semantic_id`             (identity)
  2. the engine's LowerResultV1 reports that same `semantic_id` (agreement)
  3. both paths produce an identical WorldViewV1                (convergence)
  4. the source arrives sealed to the result it produced        (production)
  5. object/edge collections are closed                         (well-formed)

Binding 4 was originally weaker than this docstring said, and review caught it.
`capture` used to accept a free `source=` argument, so a caller could pair a real
result with an entirely unrelated string; the record revalidated and minted a
sealed -- and false -- `case-`. The source now arrives only inside a
`LoweredSourceEnvelopeV1`, and the record records whether production was *proved*
(re-lowered here, engine injected) or *asserted* (inherited from the publisher
that sealed the envelope). See `envelope.py`; the distinction is deliberate and
is stored, not implied.

After that, `record.view()` is a world a generator may trust without an engine,
and `record.base_world()` is a `base_world` block whose two fields are known to
belong together.

Scope ruling, recorded here because this is where it bites: **`base_world` means
a sealed VALID world.** Invalid WRL has no `sem-`, so the diagnostic-repair
family cannot be honestly expressed as a `TaskBundleV1` and is out of scope for
WRLM-0 step 2. It gets its own object (`DraftRepairTaskV1`, keyed on draft
source + diagnostics rather than on a semantic id) when its turn comes. Pairing
invalid source with a borrowed `sem-` is the one workaround that must not
happen, and this module is what makes it impossible rather than merely
discouraged.
"""

import json

from .errors import fail
from . import envelope as E
from . import worldview as V

WORLD_RECORD_VERSION = "wrlm.worldrecord.v1"

WRLM_BAD_WORLD_RECORD = "WRLM_BAD_WORLD_RECORD"      # malformed / wrong shape
WRLM_RECORD_UNBOUND = "WRLM_RECORD_UNBOUND"          # source/artifact/id disagree

RECORD_FIELDS = ("record_version", "semantic_id", "source", "formatted_source",
                 "artifact", "lower_result_version", "engine_version", "binding")

BINDING_FIELDS = ("kind", "source_sha256", "publisher", "publisher_version")


def _fail(code, message, path=None):
    fail(code, message, path)


def capture(envelope, artifact, lower=None):
    """Build a verified WorldRecordV1 from a sealed envelope and its artifact.

    `envelope` is a `LoweredSourceEnvelopeV1` -- source and LowerResultV1 sealed
    together. `artifact` is the canonical sealed artifact the engine produced for
    that same source. Both are required precisely because the check that matters
    is that they AGREE; a record built from either alone would just be restating
    one side's claim.

    `lower` is optional and, when supplied, upgrades the source binding from
    *asserted* to *proved*: the envelope's own source is re-lowered here and must
    reproduce the same `sem-`. Pass `forge_api.lower_source`. Omitting it is not
    an error -- it produces an honest record that says `binding.kind ==
    "asserted"` and names the publisher it is trusting.

    There is no `source=` parameter any more, and that removal is the point. A
    free source argument let a caller pair a real result with unrelated text and
    still mint a sealed `case-`.
    """
    E.validate_envelope_v1(envelope)
    kind = E.BINDING_ASSERTED
    if lower is not None:
        E.prove_envelope(envelope, lower)
        kind = E.BINDING_PROVED

    lower_result = envelope["lower_result"]
    view_low = V.from_lower_result(lower_result)          # raises if not lowered
    view_art = V.from_artifact(artifact)                  # DERIVES its own sem-

    # (1) and (2): the artifact's bytes and the engine's report must name the
    # same world. from_artifact already derived rather than trusted, so this
    # compares two independently-obtained values.
    if view_art["semantic_id"] != view_low["semantic_id"]:
        _fail(WRLM_RECORD_UNBOUND,
              "the artifact derives %s but the engine reported %s; these are "
              "not the same world" % (view_art["semantic_id"],
                                      view_low["semantic_id"]), "semantic_id")

    # (3) convergence. Same identity is necessary but not sufficient: the two
    # adapters could still disagree on what the world CONTAINS, and a generator
    # reading the wrong one would build tasks about a world that never ran.
    if (view_art["objects"] != view_low["objects"]
            or view_art["edges"] != view_low["edges"]):
        _fail(WRLM_RECORD_UNBOUND,
              "the artifact and the engine payload agree on identity but not "
              "on content; the adapter pair is broken", "objects")

    return {
        "record_version": WORLD_RECORD_VERSION,
        "semantic_id": view_art["semantic_id"],
        "source": envelope["source"],
        # The engine's canonical rendering, kept separate: presenting sugar vs
        # its formatted twin is a DIFFERENT question about the SAME world, and
        # `case-` is keyed on presented source, so the distinction must survive.
        "formatted_source": lower_result.get("formatted"),
        "artifact": artifact,
        "lower_result_version": lower_result.get("result_version"),
        "engine_version": lower_result.get("engine_version"),
        # How strong is this record, and on whose say-so. Stored, never implied.
        "binding": E.binding_block(envelope, kind),
    }


def validate_record_v1(record):
    """Re-verify a record read back from disk. Pure: no engine needed.

    A stored record is still only bytes, so the identity binding is checked
    again rather than assumed to have survived the round trip."""
    if not isinstance(record, dict):
        _fail(WRLM_BAD_WORLD_RECORD, "expected an object, got %s"
              % type(record).__name__, "record")
    have, want = set(record), set(RECORD_FIELDS)
    extra, missing = sorted(have - want), sorted(want - have)
    if extra:
        _fail(WRLM_BAD_WORLD_RECORD, "unknown key(s): %s" % ", ".join(extra),
              "record")
    if missing:
        _fail(WRLM_BAD_WORLD_RECORD, "missing key(s): %s" % ", ".join(missing),
              "record")
    if record["record_version"] != WORLD_RECORD_VERSION:
        _fail(WRLM_BAD_WORLD_RECORD, "unsupported record version %r"
              % (record["record_version"],), "record_version")
    if not isinstance(record["source"], str) or not record["source"].strip():
        _fail(WRLM_BAD_WORLD_RECORD, "source must be a non-empty string",
              "source")

    # The binding block, re-derived. The stored checksum must still match the
    # stored source, or the record's text was edited after capture -- which is
    # exactly the crossed-source failure, arriving one step later.
    b = record["binding"]
    if not isinstance(b, dict):
        _fail(WRLM_BAD_WORLD_RECORD, "binding must be an object, got %s"
              % type(b).__name__, "binding")
    b_extra = sorted(set(b) - set(BINDING_FIELDS))
    b_missing = sorted(set(BINDING_FIELDS) - set(b))
    if b_extra or b_missing:
        _fail(WRLM_BAD_WORLD_RECORD, "binding keys wrong: %s"
              % ", ".join(["+%s" % k for k in b_extra]
                          + ["-%s" % k for k in b_missing]), "binding")
    if b["kind"] not in E.BINDING_KINDS:
        _fail(WRLM_BAD_WORLD_RECORD, "binding kind must be one of %s, got %r"
              % (list(E.BINDING_KINDS), b["kind"]), "binding.kind")
    got = E.source_sha256(record["source"])
    if got != b["source_sha256"]:
        _fail(WRLM_RECORD_UNBOUND,
              "the stored source hashes to %s but the binding claims %s; the "
              "text was changed after capture" % (got, b["source_sha256"]),
              "binding.source_sha256")

    # The whole point of the object: this must still hold on reopen.
    derived = V.semantic_id_of_artifact(record["artifact"])
    if derived != record["semantic_id"]:
        _fail(WRLM_RECORD_UNBOUND,
              "stored artifact derives %s but the record claims %s"
              % (derived, record["semantic_id"]), "semantic_id")
    V.from_artifact(record["artifact"])     # closed containers, typed members
    return record


def is_proved(record):
    """Was production DEMONSTRATED for this record, or merely inherited?

    Offered as a first-class question because a consumer building a training
    corpus should be able to filter on it, and because a predicate is harder to
    forget than a docstring."""
    return record.get("binding", {}).get("kind") == E.BINDING_PROVED


def view(record):
    """The WorldViewV1 a generator evaluates goals against. Cheap to call; the
    record is already verified, so this is a projection, not a re-check."""
    return V.from_artifact(record["artifact"])


def base_world(record):
    """The `base_world` block for a `TaskBundleV1`.

    Going through a record is what makes that block trustworthy: the two fields
    are known to belong together because something with an engine proved it."""
    return {"semantic_id": record["semantic_id"], "source": record["source"]}


def serialize_record(record):
    validate_record_v1(record)
    return json.dumps(record, sort_keys=True, separators=(",", ":")).encode()


def deserialize_record(blob):
    if not isinstance(blob, (str, bytes, bytearray)):
        _fail(WRLM_BAD_WORLD_RECORD, "record bytes must be str or bytes, got %s"
              % type(blob).__name__)
    try:
        record = json.loads(blob.decode() if isinstance(blob, bytes) else blob)
    except (ValueError, UnicodeDecodeError) as exc:
        _fail(WRLM_BAD_WORLD_RECORD, "not decodable JSON: %s" % exc)
    return validate_record_v1(record)
