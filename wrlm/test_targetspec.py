"""TargetSpecV1 battery -- build-order step 3 of WRLM_RESEARCH_BRIEF.md S10.

TS1-TS6   validation: well-formed, malformed, key discipline
TS7-TS9   tier gating: the policy that prevents leakage
TS10-TS12 canonicalization + identity
TS13-TS16 sealing: immutability, round-trip, id mismatch
TS17-TS18 scoring: exact match, identity-less rejection
TS19      LEAKAGE REGRESSION: the gate is load-bearing
"""

import hashlib
import json
import unittest

from . import targetspec, taskbundle, goalspec
from .errors import WrlmError
from .worldview import is_semantic_id

# A plausible sem- id for testing. 64 hex chars after "sem-".
_SEM_A = "sem-" + "a" * 64
_SEM_B = "sem-" + "b" * 64
_SEM_C = "sem-" + "c" * 64

# A minimal valid goal for tier-gating tests.
_GOAL = {"kind": "count", "domain": "objects",
         "where": {"kind": "role_is", "role": "Pulser"},
         "cmp": "ge", "n": 1}


class TestValidation(unittest.TestCase):
    """TS1-TS6: structural validation of TargetSpecV1."""

    def test_ts1_well_formed(self):
        """A correctly built spec validates."""
        spec = targetspec.make_target_spec(_SEM_A, 1)
        result = targetspec.validate_target_spec_v1(spec)
        self.assertIs(result, spec)

    def test_ts2_rejects_non_dict(self):
        """Non-dict input is a typed rejection."""
        with self.assertRaises(WrlmError) as cm:
            targetspec.validate_target_spec_v1("not a dict")
        self.assertEqual(cm.exception.code, targetspec.WRLM_BAD_TARGET)

    def test_ts3_rejects_extra_keys(self):
        spec = targetspec.make_target_spec(_SEM_A, 1)
        spec["extra"] = True
        with self.assertRaises(WrlmError) as cm:
            targetspec.validate_target_spec_v1(spec)
        self.assertEqual(cm.exception.code, targetspec.WRLM_BAD_TARGET)
        self.assertIn("extra", cm.exception.message)

    def test_ts4_rejects_missing_keys(self):
        spec = targetspec.make_target_spec(_SEM_A, 1)
        del spec["gate"]
        with self.assertRaises(WrlmError) as cm:
            targetspec.validate_target_spec_v1(spec)
        self.assertEqual(cm.exception.code, targetspec.WRLM_BAD_TARGET)
        self.assertIn("gate", cm.exception.message)

    def test_ts5_rejects_bad_version(self):
        spec = targetspec.make_target_spec(_SEM_A, 1)
        spec["target_spec_version"] = "wrlm.target.v99"
        with self.assertRaises(WrlmError) as cm:
            targetspec.validate_target_spec_v1(spec)
        self.assertEqual(cm.exception.code, targetspec.WRLM_BAD_TARGET)

    def test_ts6_rejects_bad_sem_id(self):
        """A target_semantic_id that is not a valid sem- id is refused."""
        spec = targetspec.make_target_spec(_SEM_A, 1)
        spec["target_semantic_id"] = "not-a-sem-id"
        with self.assertRaises(WrlmError) as cm:
            targetspec.validate_target_spec_v1(spec)
        self.assertEqual(cm.exception.code, targetspec.WRLM_BAD_TARGET)


class TestTierGating(unittest.TestCase):
    """TS7-TS9: the tier-gating policy."""

    def test_ts7_tier1_target_only_accepted(self):
        """Tier 1: target alone is sufficient."""
        gate = targetspec.validate_objective_for_tier(None, _SEM_A, 1)
        self.assertEqual(gate, "sufficient")

    def test_ts8_tier3_target_only_refused(self):
        """Tier 3: target without a goal is refused -- this is the gate."""
        with self.assertRaises(WrlmError) as cm:
            targetspec.validate_objective_for_tier(None, _SEM_A, 3)
        self.assertEqual(cm.exception.code, targetspec.WRLM_TARGET_TIER_GATE)

    def test_ts9_tier3_target_plus_goal_accepted(self):
        """Tier 3: target + goal is accepted."""
        gate = targetspec.validate_objective_for_tier(_GOAL, _SEM_A, 3)
        self.assertEqual(gate, "required")


class TestGateDerivation(unittest.TestCase):
    """TS10: gate is derived from tier, never asserted."""

    def test_ts10_gate_mismatch_refused(self):
        """A spec whose carried gate disagrees with its tier is refused."""
        spec = targetspec.make_target_spec(_SEM_A, 1)
        spec["gate"] = "required"  # tier 1 should derive "sufficient"
        with self.assertRaises(WrlmError) as cm:
            targetspec.validate_target_spec_v1(spec)
        self.assertEqual(cm.exception.code, targetspec.WRLM_BAD_TARGET)
        self.assertIn("derived", cm.exception.message)


class TestCanonicalizationAndIdentity(unittest.TestCase):
    """TS11-TS13: canonical serialization and identity derivation."""

    def test_ts11_canonical_deterministic(self):
        """Two builds of the same spec produce identical canonical bytes."""
        s1 = targetspec.make_target_spec(_SEM_A, 2)
        s2 = targetspec.make_target_spec(_SEM_A, 2)
        self.assertEqual(targetspec.serialize_target_spec(s1),
                         targetspec.serialize_target_spec(s2))

    def test_ts12_identity_derived_correctly(self):
        """target_spec_id matches manual sha256 over canonical bytes."""
        spec = targetspec.make_target_spec(_SEM_A, 1)
        canonical = targetspec.serialize_target_spec(spec)
        expected = "target-" + hashlib.sha256(canonical).hexdigest()
        self.assertEqual(targetspec.target_spec_id(spec), expected)

    def test_ts13_different_specs_different_ids(self):
        """Different target sem- ids produce different target spec ids."""
        id1 = targetspec.target_spec_id(targetspec.make_target_spec(_SEM_A, 1))
        id2 = targetspec.target_spec_id(targetspec.make_target_spec(_SEM_B, 1))
        self.assertNotEqual(id1, id2)


class TestSealing(unittest.TestCase):
    """TS14-TS17: SealedTarget immutability, round-trip, mismatch."""

    def test_ts14_seal_immutable(self):
        """Writing to a SealedTarget is a typed rejection."""
        sealed = targetspec.seal_target(
            targetspec.make_target_spec(_SEM_A, 1))
        with self.assertRaises(WrlmError) as cm:
            sealed.x = 1
        self.assertEqual(cm.exception.code, "WRLM_SEALED_IMMUTABLE")

    def test_ts15_seal_round_trip(self):
        """seal -> canonical_bytes -> open recovers the same id."""
        spec = targetspec.make_target_spec(_SEM_A, 2)
        sealed = targetspec.seal_target(spec)
        reopened = targetspec.open_sealed_target(
            sealed.canonical_bytes, expect_id=sealed.target_spec_id)
        self.assertEqual(reopened.target_spec_id, sealed.target_spec_id)
        self.assertEqual(reopened.spec, sealed.spec)

    def test_ts16_open_rejects_id_mismatch(self):
        """open_sealed_target refuses when expect_id disagrees."""
        spec = targetspec.make_target_spec(_SEM_A, 1)
        sealed = targetspec.seal_target(spec)
        with self.assertRaises(WrlmError) as cm:
            targetspec.open_sealed_target(
                sealed.canonical_bytes, expect_id="target-" + "0" * 64)
        self.assertEqual(cm.exception.code, targetspec.WRLM_BAD_TARGET)

    def test_ts17_spec_is_fresh_copy(self):
        """Mutating .spec does not affect the seal."""
        sealed = targetspec.seal_target(
            targetspec.make_target_spec(_SEM_A, 1))
        s = sealed.spec
        s["tier"] = 999
        self.assertEqual(sealed.spec["tier"], 1)


class TestScoring(unittest.TestCase):
    """TS18-TS19: exact sem- scoring."""

    def test_ts18_score_exact_match(self):
        """Matching sem- ids score True."""
        spec = targetspec.make_target_spec(_SEM_A, 1)
        view = {"semantic_id": _SEM_A, "objects": [], "edges": []}
        self.assertTrue(targetspec.score_target(spec, view))

    def test_ts18b_score_mismatch(self):
        """Non-matching sem- ids score False."""
        spec = targetspec.make_target_spec(_SEM_A, 1)
        view = {"semantic_id": _SEM_B, "objects": [], "edges": []}
        self.assertFalse(targetspec.score_target(spec, view))

    def test_ts19_rejects_identity_less_view(self):
        """A bare artifact without semantic_id is a typed rejection, not False.
        A false negative in a reward signal gets trained against."""
        spec = targetspec.make_target_spec(_SEM_A, 1)
        with self.assertRaises(WrlmError) as cm:
            targetspec.score_target(spec, {"objects": [], "edges": []})
        self.assertEqual(cm.exception.code, targetspec.WRLM_BAD_TARGET)


class TestLeakageRegression(unittest.TestCase):
    """TS20-TS24: the leakage regression, exercised at two levels.

    TS20-TS24 test the gate function directly.
    TS30-TS33 test the gate through the PUBLIC TASK API (taskbundle.make_task),
    which is the path real generators take. The structural dependency is:
    taskbundle.make_task -> taskbundle.validate_task_v1 ->
    targetspec.validate_objective_for_tier. If any link in that chain is
    removed, the TS30 tests fail.
    """

    def test_ts20_tier3_target_only_task_refused(self):
        """Building a tier-3 task with target only and no goal MUST fail.

        This is the leakage regression: if this test passes with the gate
        removed, the gate is decorative and the leakage argument is false.
        The refusal comes from validate_objective_for_tier, which taskbundle
        must call (or enforce equivalently) for the gate to be real."""
        # Directly test the gate: tier-3 target-only is refused
        with self.assertRaises(WrlmError) as cm:
            targetspec.validate_objective_for_tier(None, _SEM_B, 3)
        self.assertEqual(cm.exception.code, targetspec.WRLM_TARGET_TIER_GATE)

    def test_ts21_tier3_with_goal_accepted(self):
        """A tier-3 task carrying both target and goal is accepted."""
        gate = targetspec.validate_objective_for_tier(_GOAL, _SEM_B, 3)
        self.assertEqual(gate, "required")

    def test_ts22_tier1_target_only_accepted(self):
        """A tier-1 task with target only is accepted -- the gate is
        tier-dependent, not a blanket refusal."""
        gate = targetspec.validate_objective_for_tier(None, _SEM_B, 1)
        self.assertEqual(gate, "sufficient")

    def test_ts23_tier2_target_only_accepted(self):
        """Tier 2 also accepts target-only."""
        gate = targetspec.validate_objective_for_tier(None, _SEM_B, 2)
        self.assertEqual(gate, "recommended")

    def test_ts24_sealed_target_scores_via_seal(self):
        """SealedTarget.score() works correctly through the seal."""
        sealed = targetspec.seal_target(
            targetspec.make_target_spec(_SEM_A, 1))
        view_match = {"semantic_id": _SEM_A, "objects": [], "edges": []}
        view_miss = {"semantic_id": _SEM_B, "objects": [], "edges": []}
        self.assertTrue(sealed.score(view_match))
        self.assertFalse(sealed.score(view_miss))

    # --- TS30-TS33: leakage regression through the PUBLIC TASK API ----------
    # These go through taskbundle.make_task, which is the path real generators
    # take. The structural dependency is on the PRODUCTION gate: every
    # assertion references targetspec.WRLM_TARGET_TIER_GATE (the error code)
    # or targetspec.validate_objective_for_tier (the gate function). If the
    # gate enforcement is removed from taskbundle.validate_task_v1, make_task
    # stops raising and these tests fail. If the gate constant or function is
    # deleted from targetspec.py, the test cannot even reference them.

    def test_ts30_make_task_tier3_target_only_refused(self):
        """taskbundle.make_task with tier=3, target only, no goal MUST raise
        WRLM_TARGET_TIER_GATE. This goes through the real validation path:
        make_task -> canonicalize_task_v1 -> validate_task_v1 ->
        targetspec.validate_objective_for_tier. Removing that call makes
        make_task succeed and this test fail."""
        with self.assertRaises(WrlmError) as cm:
            taskbundle.make_task(
                _SEM_A, "source",
                target_semantic_id=_SEM_B,
                family="transform", tier=3, difficulty="hard")
        # The error code MUST be the production gate's own code, not a
        # generic WRLM_BAD_TASK. This couples the test to the production
        # constant: deleting targetspec.WRLM_TARGET_TIER_GATE breaks the
        # assertion even if something else raises.
        self.assertEqual(cm.exception.code, targetspec.WRLM_TARGET_TIER_GATE)

    def test_ts31_make_task_tier3_target_plus_goal_accepted(self):
        """The corresponding goal-bearing task at tier 3 MUST be accepted.
        This proves the gate is tier-and-objective-dependent, not a blanket
        refusal of high-tier tasks."""
        task = taskbundle.make_task(
            _SEM_A, "source",
            goal=_GOAL,
            target_semantic_id=_SEM_B,
            family="transform", tier=3, difficulty="hard")
        self.assertIsNotNone(task)
        self.assertEqual(task["stratum"]["tier"], 3)
        self.assertIsNotNone(task["objective"]["goal"])
        self.assertIsNotNone(task["objective"]["target_spec_id"])

    def test_ts32_gate_is_reachable_from_taskbundle(self):
        """The production gate function must be reachable from taskbundle's
        own targetspec import. If taskbundle stops importing targetspec or
        renames the binding, this test fails -- making the leakage regression
        structurally dependent on the import chain, not just on observed
        behavior."""
        # taskbundle imports targetspec as a module attribute
        tb_ts = getattr(taskbundle, 'targetspec', None)
        self.assertIsNotNone(tb_ts,
                             "taskbundle must import targetspec")
        self.assertIs(tb_ts, targetspec,
                      "taskbundle.targetspec must be the same module")
        # The gate function must exist and be callable
        gate_fn = getattr(tb_ts, 'validate_objective_for_tier', None)
        self.assertTrue(callable(gate_fn),
                        "validate_objective_for_tier must be callable")
        # The gate error code must exist
        self.assertEqual(tb_ts.WRLM_TARGET_TIER_GATE,
                         "WRLM_TARGET_TIER_GATE")

    def test_ts33_validate_task_v1_tier3_target_only_refused(self):
        """validate_task_v1 (the validator, not just the builder) also refuses
        a tier-3 target-only task. This closes the bypass path: even if
        someone constructs a task dict by hand and calls validate_task_v1
        directly, the gate still fires."""
        # Build a valid tier-1 task, then mutate it to tier-3 with no goal.
        # This bypasses make_task's own gate check and hits validate_task_v1.
        import copy
        base = taskbundle.make_task(
            _SEM_A, "source",
            target_semantic_id=_SEM_B,
            family="transform", tier=1, difficulty="easy")
        # Mutate to tier-3, strip the goal, re-derive target_spec_id for
        # tier 3 so the id check doesn't fire first
        bad = copy.deepcopy(base)
        bad["stratum"]["tier"] = 3
        bad["objective"]["goal"] = None
        bad["objective"]["goal_spec_id"] = None
        bad["objective"]["target_spec_id"] = targetspec.target_spec_id(
            targetspec.make_target_spec(_SEM_B, 3))
        with self.assertRaises(WrlmError) as cm:
            taskbundle.validate_task_v1(bad)
        self.assertEqual(cm.exception.code, targetspec.WRLM_TARGET_TIER_GATE)


class TestDeserialize(unittest.TestCase):
    """TS25-TS26: deserialization edge cases."""

    def test_ts25_deserialize_rejects_non_bytes(self):
        with self.assertRaises(WrlmError) as cm:
            targetspec.deserialize_target_spec(42)
        self.assertEqual(cm.exception.code, targetspec.WRLM_BAD_TARGET)

    def test_ts26_deserialize_rejects_bad_json(self):
        with self.assertRaises(WrlmError) as cm:
            targetspec.deserialize_target_spec(b"not json")
        self.assertEqual(cm.exception.code, targetspec.WRLM_BAD_TARGET)


class TestGateForTier(unittest.TestCase):
    """TS27-TS28: gate_for_tier edge cases."""

    def test_ts27_rejects_zero(self):
        with self.assertRaises(WrlmError):
            targetspec.gate_for_tier(0)

    def test_ts28_rejects_bool(self):
        with self.assertRaises(WrlmError):
            targetspec.gate_for_tier(True)

    def test_ts29_high_tier_gets_required(self):
        """Tiers above 3 default to the strictest gate."""
        self.assertEqual(targetspec.gate_for_tier(4), "required")
        self.assertEqual(targetspec.gate_for_tier(100), "required")


if __name__ == "__main__":
    unittest.main()
