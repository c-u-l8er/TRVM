"""TaskBundleV1 -- what a WRLM-0 attempt is actually scored against.

A goal alone is not a task. A task is a goal *plus the world it starts from*,
plus enough provenance to say where it came from, sealed under one id so that
"the model solved task X" names exactly one thing forever.

The identity chain this closes:

    sem-   the starting world           (forge)
    goal-  the objective                (wrlm/goalspec)
    task-  the pair, plus provenance    (HERE)

`task-` is the last rung minted before an attempt runs; everything downstream
(`episode-`, `bundle-`) already exists in TRAAVIIS.

Two laws deserve their names:

* **An objective is mandatory.** A bundle may carry a `goal` (structural), a
  `target_semantic_id` (exact world), or both -- but not neither. A task with
  no objective is unfalsifiable, which is the failure class the whole `sem-`
  spine exists to remove.
* **A carried id is never trusted.** `goal_spec_id` is re-derived from the goal
  node and compared. Storing an id next to the thing it names is a convenience
  for readers; believing it would make the seal decorative.

Validation here is PURE -- it never looks at a world. The one property that
*does* need a world (is the task already solved at attempt 0?) lives in a
separate, explicitly impure `check_task_nondegenerate`. Keeping those apart is
what lets a task be validated offline, in a corpus, without an engine.
"""

import hashlib
import json

from . import goalspec
from .errors import fail
from .worldview import is_semantic_id, is_world_view

TASK_BUNDLE_VERSION = "wrlm.task.v1"

WRLM_BAD_TASK = "WRLM_BAD_TASK"                      # malformed / wrong shape
WRLM_TASK_NO_OBJECTIVE = "WRLM_TASK_NO_OBJECTIVE"    # nothing to satisfy
WRLM_TASK_ID_MISMATCH = "WRLM_TASK_ID_MISMATCH"      # carried id != derived id
WRLM_TASK_DEGENERATE = "WRLM_TASK_DEGENERATE"        # solved before it starts

# Exact key sets. Extra or missing keys are rejections, not warnings -- the same
# closure discipline GoalSpecV1 applies to its nodes.
TASK_FIELDS = ("task_version", "base_world", "objective", "stratum",
               "generator")
BASE_WORLD_FIELDS = ("semantic_id", "source")
OBJECTIVE_FIELDS = ("goal", "goal_spec_id", "target_semantic_id")
STRATUM_FIELDS = ("family", "tier", "difficulty")
GENERATOR_FIELDS = ("generator_id", "generator_version", "seed")

# `difficulty` is a coarse ordinal owned by the generator, NOT a latent trait.
# WRLM-0 has 2-4 examinees, where a fitted IRT parameter is unidentified; the
# honest thing is a declared stratum the analysis can condition on.
DIFFICULTIES = ("trivial", "easy", "moderate", "hard")


def _fail(code, message, path=None):
    fail(code, message, path)


def _check_keys(obj, fields, path):
    if not isinstance(obj, dict):
        _fail(WRLM_BAD_TASK, "expected an object, got %s"
              % type(obj).__name__, path)
    have, want = set(obj), set(fields)
    extra, missing = sorted(have - want), sorted(want - have)
    if extra:
        _fail(WRLM_BAD_TASK, "unknown key(s): %s" % ", ".join(extra), path)
    if missing:
        _fail(WRLM_BAD_TASK, "missing key(s): %s" % ", ".join(missing), path)


def _check_str(v, path, allow_empty=False):
    if not isinstance(v, str):
        _fail(WRLM_BAD_TASK, "expected a string, got %s"
              % type(v).__name__, path)
    if not allow_empty and not v:
        _fail(WRLM_BAD_TASK, "must not be empty", path)
    return v


def _check_sem(v, path):
    if not is_semantic_id(v):
        _fail(WRLM_BAD_TASK, "not a semantic artifact id: %r" % (v,), path)
    return v


def validate_task_v1(task):
    """Structural + identity validation. Pure: consults no world.

    Returns the task unchanged so it can be used inline."""
    _check_keys(task, TASK_FIELDS, "task")
    if task["task_version"] != TASK_BUNDLE_VERSION:
        _fail(WRLM_BAD_TASK, "unsupported task version %r; this module is %r"
              % (task["task_version"], TASK_BUNDLE_VERSION), "task_version")

    base = task["base_world"]
    _check_keys(base, BASE_WORLD_FIELDS, "base_world")
    _check_sem(base["semantic_id"], "base_world.semantic_id")
    _check_str(base["source"], "base_world.source")

    obj = task["objective"]
    _check_keys(obj, OBJECTIVE_FIELDS, "objective")
    goal, goal_id, target = (obj["goal"], obj["goal_spec_id"],
                             obj["target_semantic_id"])
    if goal is None and target is None:
        _fail(WRLM_TASK_NO_OBJECTIVE,
              "a task must carry a goal, a target world, or both", "objective")
    if goal is None:
        if goal_id is not None:
            _fail(WRLM_BAD_TASK, "goal_spec_id present without a goal",
                  "objective.goal_spec_id")
    else:
        # Delegate: the goal's OWN validator owns goal shape. Re-implementing it
        # here would let the two drift.
        goalspec.validate_goal_v1(goal)
        derived = goalspec.goal_spec_id(goal)
        if goal_id is None:
            _fail(WRLM_BAD_TASK, "goal present without its goal_spec_id",
                  "objective.goal_spec_id")
        if goal_id != derived:
            _fail(WRLM_TASK_ID_MISMATCH,
                  "carried goal_spec_id %s but the goal derives %s"
                  % (goal_id, derived), "objective.goal_spec_id")
    if target is not None:
        _check_sem(target, "objective.target_semantic_id")
        if target == base["semantic_id"]:
            # Not a shape error: a well-formed task that is solved by doing
            # nothing. It would silently inflate every arm's success rate.
            _fail(WRLM_TASK_DEGENERATE,
                  "target world equals the base world; the task is solved at "
                  "attempt 0", "objective.target_semantic_id")

    st = task["stratum"]
    _check_keys(st, STRATUM_FIELDS, "stratum")
    _check_str(st["family"], "stratum.family")
    if not isinstance(st["tier"], int) or isinstance(st["tier"], bool):
        _fail(WRLM_BAD_TASK, "tier must be an integer", "stratum.tier")
    if st["tier"] < 0:
        _fail(WRLM_BAD_TASK, "tier must not be negative", "stratum.tier")
    if st["difficulty"] not in DIFFICULTIES:
        _fail(WRLM_BAD_TASK, "difficulty must be one of %s, got %r"
              % (", ".join(DIFFICULTIES), st["difficulty"]),
              "stratum.difficulty")

    gen = task["generator"]
    _check_keys(gen, GENERATOR_FIELDS, "generator")
    _check_str(gen["generator_id"], "generator.generator_id")
    _check_str(gen["generator_version"], "generator.generator_version")
    if not isinstance(gen["seed"], int) or isinstance(gen["seed"], bool):
        _fail(WRLM_BAD_TASK, "seed must be an integer", "generator.seed")
    return task


def canonicalize_task_v1(task):
    """Validate, then rebuild in a fixed key order with the goal canonicalized
    by its own layer. There is nothing commutative at this level -- a task is a
    record, not an algebra -- so this only fixes ordering."""
    validate_task_v1(task)
    goal = task["objective"]["goal"]
    goal = None if goal is None else goalspec.canonicalize_goal_v1(goal)
    return {
        "task_version": TASK_BUNDLE_VERSION,
        "base_world": {"semantic_id": task["base_world"]["semantic_id"],
                       "source": task["base_world"]["source"]},
        "objective": {"goal": goal,
                      "goal_spec_id": task["objective"]["goal_spec_id"],
                      "target_semantic_id":
                          task["objective"]["target_semantic_id"]},
        "stratum": {"family": task["stratum"]["family"],
                    "tier": task["stratum"]["tier"],
                    "difficulty": task["stratum"]["difficulty"]},
        "generator": {"generator_id": task["generator"]["generator_id"],
                      "generator_version":
                          task["generator"]["generator_version"],
                      "seed": task["generator"]["seed"]},
    }


def serialize_task(task):
    return json.dumps(canonicalize_task_v1(task), sort_keys=True,
                      separators=(",", ":")).encode()


def deserialize_task(blob):
    if not isinstance(blob, (str, bytes, bytearray)):
        _fail(WRLM_BAD_TASK, "task bytes must be str or bytes, got %s"
              % type(blob).__name__)
    try:
        task = json.loads(blob.decode() if isinstance(blob, bytes) else blob)
    except (ValueError, UnicodeDecodeError) as exc:
        _fail(WRLM_BAD_TASK, "not decodable JSON: %s" % exc)
    return canonicalize_task_v1(task)


def task_bundle_id(task):
    return "task-" + hashlib.sha256(serialize_task(task)).hexdigest()


# ------------------------------------------------- the dedup unit vs the row
# `task-` covers provenance, which is right for a receipt and WRONG for a
# statistical unit. A generator that emits the same actual problem under 20
# seeds mints 20 distinct `task-` ids; counting those as 20 independent trials
# would silently multiply n by 20 and shrink every confidence interval by ~4.5x
# on nothing.
#
# So split the two questions:
#
#     case-   what the model is ASKED         base sem- + presented source
#                                             + canonical objective
#     task-   that case, plus HOW it arose    + family, difficulty, generator,
#                                             version, seed
#
# Analysis and coverage deduplicate on `case-`. Receipts and provenance carry
# `task-`. Both are DERIVED from the bundle's own bytes, never stored -- there
# is nothing here for a generator to misreport.
#
# Note both `semantic_id` and `source` belong in a case: sugar and its numeric
# twin seal to the SAME `sem-` while presenting DIFFERENT text to the model, so
# they are genuinely different questions about the same world.
CASE_FIELDS = ("case_version", "base_semantic_id", "base_source", "objective")


def case_document(task):
    """The canonical content of a case: exactly what is being asked, with every
    trace of who generated it and how hard they thought it was removed."""
    t = canonicalize_task_v1(task)
    return {"case_version": TASK_BUNDLE_VERSION,
            "base_semantic_id": t["base_world"]["semantic_id"],
            "base_source": t["base_world"]["source"],
            "objective": t["objective"]}


def case_id(task):
    """`case-<sha256>`. Two bundles differing only in seed, generator or
    declared difficulty share a `case_id` and are ONE observation."""
    blob = json.dumps(case_document(task), sort_keys=True,
                      separators=(",", ":")).encode()
    return "case-" + hashlib.sha256(blob).hexdigest()


class SealedTask(object):
    """Immutable task: the canonical bytes ARE the task; the id is derived from
    them. Same discipline as `SealedGoal` and `SealedArtifact`."""

    __slots__ = ("_bytes", "_id")

    def __init__(self, task):
        object.__setattr__(self, "_bytes", serialize_task(task))
        object.__setattr__(
            self, "_id", "task-" + hashlib.sha256(self._bytes).hexdigest())

    def __setattr__(self, name, value):
        _fail(goalspec.WRLM_SEALED_IMMUTABLE,
              "SealedTask is immutable; cannot set %r" % (name,))

    def __delattr__(self, name):
        _fail(goalspec.WRLM_SEALED_IMMUTABLE,
              "SealedTask is immutable; cannot delete %r" % (name,))

    @property
    def canonical_bytes(self):
        return self._bytes

    @property
    def task_bundle_id(self):
        return self._id

    @property
    def task(self):
        """A FRESH mutable copy."""
        return json.loads(self._bytes.decode())

    @property
    def case_id(self):
        """The dedup unit. Many sealed tasks may share one `case_id`."""
        return case_id(self.task)

    @property
    def sealed_goal(self):
        """The objective as its own seal, or None for a target-only task. Built
        from these bytes, so its `goal-` id cannot drift from this `task-`."""
        goal = self.task["objective"]["goal"]
        return None if goal is None else goalspec.seal_goal(goal)

    def __eq__(self, other):
        return isinstance(other, SealedTask) and other._bytes == self._bytes

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._bytes)

    def __repr__(self):
        return "SealedTask(%s)" % self._id


def seal_task(task):
    return SealedTask(task)


def open_sealed_task(blob, expect_id=None):
    sealed = SealedTask(deserialize_task(blob))
    if expect_id is not None and sealed.task_bundle_id != expect_id:
        _fail(WRLM_BAD_TASK, "task id mismatch: bytes yield %s, expected %s"
              % (sealed.task_bundle_id, expect_id))
    return sealed


def make_task_for(record, **kw):
    """Build a task whose `base_world` came from a VERIFIED `WorldRecordV1`.

    This is the path generators should take. `make_task` accepts a loose
    `(semantic_id, source)` pair, and no pure validator can tell whether those
    two belong together -- deciding that needs the engine. A record is the
    receipt that something with an engine already checked, so routing through
    one turns an unverifiable claim into a verified one. Making the safe path
    the convenient path is the only norm-enforcement that actually works."""
    from . import worldrecord
    base = worldrecord.base_world(worldrecord.validate_record_v1(record))
    return make_task(base["semantic_id"], base["source"], **kw)


def make_task(base_semantic_id, base_source, goal=None,
              target_semantic_id=None, family="unspecified", tier=0,
              difficulty="moderate", generator_id="handwritten",
              generator_version="0", seed=0):
    """Assemble and validate a bundle, deriving `goal_spec_id` rather than
    asking the caller for it. The validator still re-derives it -- a builder
    that could be bypassed is not a law."""
    return canonicalize_task_v1({
        "task_version": TASK_BUNDLE_VERSION,
        "base_world": {"semantic_id": base_semantic_id, "source": base_source},
        "objective": {
            "goal": goal,
            "goal_spec_id": None if goal is None else goalspec.goal_spec_id(goal),
            "target_semantic_id": target_semantic_id},
        "stratum": {"family": family, "tier": tier, "difficulty": difficulty},
        "generator": {"generator_id": generator_id,
                      "generator_version": generator_version, "seed": seed},
    })


# --------------------------------------------------------------- world-facing
def satisfied_by(task, view):
    """Is this task's objective met by `view`? Both clauses must hold.

    The GOAL clause is total: a malformed world yields False rather than
    raising, so a scoring loop cannot be crashed by a bad world.

    The TARGET clause is NOT total, and deliberately so. Comparing `sem-`
    requires the thing being scored to carry identity, and a bare artifact does
    not -- it would answer "no" to every identity question, silently scoring a
    SOLVED episode as failed. A false negative in a reward signal is worse than
    a crash: a crash gets noticed, a silently unrewarded success gets trained
    against. So an identity-less world is a TYPED rejection here, and callers
    must pass a `WorldViewV1` (use `worldview.from_artifact`, which derives the
    identity rather than taking it on trust)."""
    obj = canonicalize_task_v1(task)["objective"]
    ok = True
    if obj["goal"] is not None:
        ok = ok and goalspec.evaluate_goal(obj["goal"], view)
    if obj["target_semantic_id"] is not None:
        if not is_world_view(view):
            _fail(WRLM_BAD_TASK,
                  "this task is scored against a target world, so it needs a "
                  "WorldViewV1 carrying `semantic_id`; got %s. Wrap it with "
                  "worldview.from_artifact()." % type(view).__name__,
                  "objective.target_semantic_id")
        ok = ok and (view["semantic_id"] == obj["target_semantic_id"])
    return ok


def check_task_nondegenerate(task, base_view):
    """IMPURE companion to `validate_task_v1`: refuse a task whose objective the
    BASE world already satisfies.

    Structural degeneracy (`target == base`) is caught by the pure validator
    because it needs no world. Goal degeneracy cannot be -- deciding whether a
    goal holds requires the objects and edges. So it lives here, called by a
    generator that has the world in hand, and never by an offline reader.
    """
    if satisfied_by(task, base_view):
        _fail(WRLM_TASK_DEGENERATE,
              "the base world already satisfies the objective; there is "
              "nothing for an attempt to do", "objective")
    return task
