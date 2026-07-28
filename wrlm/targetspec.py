"""TargetSpecV1 -- the tier-gated exact-world oracle.

From the oracle ladder (WRLM_RESEARCH_BRIEF.md S2):

    Rung 2   Target identity   is it THE intended world?   total, free (sem- eq)
    Rung 3   Goal satisfaction  does it meet a property?   total, free (GoalSpecV1)

TargetSpecV1 is retained, not replaced -- it is the only *total* oracle at the
identity level. GoalSpecV1 *supplements* it and is GATED BY TIER (S4):

    tier 1   target alone is a COMPLETE objective
    tier 2   target alone is accepted; a goal is RECOMMENDED
    tier 3   target alone is REFUSED; a goal MUST accompany it

The reasoning: a tier-1 task is one edit, one requirement. An exact target is a
total, free oracle and overkill is not a problem. A tier-3 task involves ordered,
preservation-constrained edits -- asking only "is it *this* exact world" leaks
the answer through the target (the model could reconstruct the target rather than
reason about the constraints), and the underdetermined goal is what forces actual
structural reasoning.

This module formalises that tier-gating as a validator and a builder, sitting
alongside GoalSpecV1 rather than replacing it. The task bundle's objective already
carries both `goal` and `target_semantic_id`; this module says which combinations
are LEGAL at which tier.

No new identity rung. No new runtime construct.

IDENTITY
--------
`target_spec_id(spec)` is `target-<sha256 of canonical bytes>`, derived the same
way `goal-` and `task-` are: `json.dumps(..., sort_keys=True,
separators=(",", ":"))`. The canonical form rebuilds in a fixed key order with
the gate RE-DERIVED from the tier -- a stored gate that disagreed with its tier
would be a lie, and a lie that seals into identity is worse than one that doesn't.

SEALING
-------
`SealedTarget` mirrors `SealedGoal` / `SealedTask`: the canonical bytes ARE the
object, the id is derived from them, `.spec` returns a fresh copy, writes are
refused. `open_sealed_target(blob, expect_id=)` re-derives and refuses a mismatch.
"""

import hashlib
import json

from .errors import WrlmError, fail
from .worldview import is_semantic_id

WRLM_BAD_TARGET = "WRLM_BAD_TARGET"           # malformed target spec
WRLM_TARGET_TIER_GATE = "WRLM_TARGET_TIER_GATE"  # tier-gating violation

# The tier gate is a POLICY, not a knob. Changing it changes which tasks are
# legal, which changes the corpus, which changes results. Versioned with the
# spec, not configurable at runtime.
TIER_GATE = {
    1: "sufficient",     # target alone fully specifies the task
    2: "recommended",    # target accepted alone; goal improves the signal
    3: "required",       # goal is mandatory alongside a target
}

# What "required" means, precisely: a tier-3 task carrying ONLY a target and no
# goal is refused. A tier-3 task carrying BOTH is accepted. A tier-3 task
# carrying ONLY a goal (no target) is also accepted -- goal_satisfaction already
# works this way.


def gate_for_tier(tier):
    """The tier-gating policy for a given tier.

    Returns one of 'sufficient', 'recommended', 'required'.
    """
    if not isinstance(tier, int) or isinstance(tier, bool) or tier < 1:
        fail(WRLM_BAD_TARGET, "tier must be a positive integer, got %r"
             % (tier,), "tier")
    # Tiers above 3 get the strictest gate. This is forward-compatible rather
    # than a rejection: if the tier domain widens, the gate is the one that
    # forces the most learning signal, which is always the safe default.
    return TIER_GATE.get(tier, "required")


def validate_objective_for_tier(goal, target_semantic_id, tier):
    """Check that this (goal, target) combination is legal at this tier.

    This is the tier-gating rule, mechanised. The pure task validator
    (`taskbundle.validate_task_v1`) already enforces that at least one of
    goal/target is present; this adds the tier-dependent constraint.

    Returns the gate label so callers can report it.
    """
    gate = gate_for_tier(tier)

    # No objective at all is caught by the task validator, not here.
    if goal is None and target_semantic_id is None:
        return gate

    if target_semantic_id is not None:
        if not is_semantic_id(target_semantic_id):
            fail(WRLM_BAD_TARGET,
                 "not a semantic artifact id: %r" % (target_semantic_id,),
                 "target_semantic_id")

    if gate == "required" and target_semantic_id is not None and goal is None:
        fail(WRLM_TARGET_TIER_GATE,
             "tier %d requires a goal alongside a target; a target alone at "
             "this tier leaks the answer through the target world rather than "
             "forcing structural reasoning about constraints"
             % tier, "objective")

    return gate


def make_target_spec(target_semantic_id, tier):
    """Build a TargetSpecV1: the target + its tier gate.

    The spec is a record, not a class -- it carries data, nothing else. The
    gate is DERIVED from the tier rather than stored, because a stored gate
    that disagreed with the tier's contract would be an assertion.
    """
    if not is_semantic_id(target_semantic_id):
        fail(WRLM_BAD_TARGET,
             "not a semantic artifact id: %r" % (target_semantic_id,),
             "target_semantic_id")
    gate = gate_for_tier(tier)
    return {
        "target_spec_version": "wrlm.target.v1",
        "target_semantic_id": target_semantic_id,
        "tier": tier,
        "gate": gate,
    }


def validate_target_spec_v1(spec):
    """Structural validation of a TargetSpecV1."""
    if not isinstance(spec, dict):
        fail(WRLM_BAD_TARGET, "target spec must be an object, got %s"
             % type(spec).__name__, "target_spec")
    want = {"target_spec_version", "target_semantic_id", "tier", "gate"}
    have = set(spec)
    extra, missing = sorted(have - want), sorted(want - have)
    if extra:
        fail(WRLM_BAD_TARGET, "unknown key(s): %s" % ", ".join(extra),
             "target_spec")
    if missing:
        fail(WRLM_BAD_TARGET, "missing key(s): %s" % ", ".join(missing),
             "target_spec")
    if spec["target_spec_version"] != "wrlm.target.v1":
        fail(WRLM_BAD_TARGET,
             "unsupported target spec version %r" % (spec["target_spec_version"],),
             "target_spec_version")
    if not is_semantic_id(spec["target_semantic_id"]):
        fail(WRLM_BAD_TARGET,
             "not a semantic artifact id: %r" % (spec["target_semantic_id"],),
             "target_semantic_id")
    derived_gate = gate_for_tier(spec["tier"])
    if spec["gate"] != derived_gate:
        fail(WRLM_BAD_TARGET,
             "carried gate %r but tier %d derives %r; the gate is derived, "
             "never asserted" % (spec["gate"], spec["tier"], derived_gate),
             "target_spec.gate")
    return spec


def score_target(spec, view):
    """Does this view satisfy the target oracle? Returns bool.

    The view MUST carry `semantic_id` (use `worldview.from_artifact`). An
    identity-less world is a typed rejection, not a False -- the same rule
    `taskbundle.satisfied_by` enforces, for the same reason: a false negative
    in a reward signal gets trained against.
    """
    validate_target_spec_v1(spec)
    if not isinstance(view, dict) or "semantic_id" not in view:
        fail(WRLM_BAD_TARGET,
             "scoring a target requires a view with `semantic_id`; got %s"
             % type(view).__name__, "view")
    return view["semantic_id"] == spec["target_semantic_id"]


# ------------------------------------------------- canonicalization + identity
TARGETSPEC_VERSION = "wrlm.target.v1"

# Fixed key order for canonical form. A target spec is a record, not an algebra
# -- there is nothing commutative to normalise. This only fixes ordering.
_TARGET_SPEC_FIELDS = ("target_spec_version", "target_semantic_id", "tier",
                       "gate")


def canonicalize_target_spec_v1(spec):
    """Validate, then rebuild in a fixed key order with the gate RE-DERIVED
    from the tier. Returns a new dict."""
    validate_target_spec_v1(spec)
    return {
        "target_spec_version": TARGETSPEC_VERSION,
        "target_semantic_id": spec["target_semantic_id"],
        "tier": spec["tier"],
        "gate": gate_for_tier(spec["tier"]),
    }


def serialize_target_spec(spec):
    """Deterministic canonical bytes. Same discipline as `serialize_goal` and
    `serialize_task`: sort_keys, compact separators, UTF-8."""
    return json.dumps(canonicalize_target_spec_v1(spec), sort_keys=True,
                      separators=(",", ":")).encode()


def deserialize_target_spec(blob):
    if not isinstance(blob, (str, bytes, bytearray)):
        fail(WRLM_BAD_TARGET,
             "target spec bytes must be str or bytes, got %s"
             % type(blob).__name__, None)
    try:
        spec = json.loads(blob.decode() if isinstance(blob, bytes) else blob)
    except (ValueError, UnicodeDecodeError) as e:
        fail(WRLM_BAD_TARGET,
             "target spec bytes are not valid JSON: %s" % (e,), None)
    return canonicalize_target_spec_v1(spec)


def target_spec_id(spec):
    """`target-<sha256>` over the canonical bytes."""
    return "target-" + hashlib.sha256(serialize_target_spec(spec)).hexdigest()


# ------------------------------------------------------------------ the seal
class SealedTarget(object):
    """An immutable target spec: canonical BYTES plus the id derived from them.
    Mirrors `SealedGoal` / `SealedTask` -- the bytes are the object, `.spec`
    deserializes fresh on every access, writes are refused."""

    __slots__ = ("_bytes", "_id")

    def __init__(self, spec):
        object.__setattr__(self, "_bytes", serialize_target_spec(spec))
        object.__setattr__(
            self, "_id",
            "target-" + hashlib.sha256(self._bytes).hexdigest())

    def __setattr__(self, name, value):
        raise WrlmError(
            "WRLM_SEALED_IMMUTABLE",
            "SealedTarget is immutable; cannot set %r" % (name,))

    def __delattr__(self, name):
        raise WrlmError(
            "WRLM_SEALED_IMMUTABLE",
            "SealedTarget is immutable; cannot delete %r" % (name,))

    @property
    def canonical_bytes(self):
        return self._bytes

    @property
    def target_spec_id(self):
        return self._id

    @property
    def spec(self):
        """A FRESH mutable copy. Mutating it cannot affect the seal."""
        return json.loads(self._bytes.decode())

    def score(self, view):
        """Convenience: score using this sealed spec."""
        return score_target(self.spec, view)

    def __eq__(self, other):
        return isinstance(other, SealedTarget) and other._bytes == self._bytes

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._bytes)

    def __repr__(self):
        return "SealedTarget(%s)" % self._id


def seal_target(spec):
    return SealedTarget(spec)


def open_sealed_target(blob, expect_id=None):
    """Reopen from bytes, re-deriving the id. If `expect_id` is given and
    does not match, the target is rejected -- a seal that trusted a
    caller-supplied id would not be a seal."""
    sealed = SealedTarget(deserialize_target_spec(blob))
    if expect_id is not None and sealed.target_spec_id != expect_id:
        fail(WRLM_BAD_TARGET,
             "target id mismatch: bytes yield %s, expected %s"
             % (sealed.target_spec_id, expect_id), None)
    return sealed
