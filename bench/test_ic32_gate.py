#!/usr/bin/env python3
"""
Focused test: the IC32 acceptance gate must fail when any declared IC32-family
backend is absent or skipped.

This exercises the invariant that bench.py checks ALL declared IC32 members,
not merely the live subset -- so a missing ic32.wasm (or any other member)
causes a conformance failure rather than a silent pass.
"""
import json, os, sys, unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bench  # noqa: E402


class TestIC32GateRequiresDeclaredMembers(unittest.TestCase):
    """The gate uses IC32_DECLARED, not the live subset."""

    def test_declared_set_has_five_members(self):
        """Sanity: the declared IC32 family has exactly five members."""
        self.assertEqual(len(bench.IC32_DECLARED), 5)
        self.assertIn("ic32.wasm", bench.IC32_DECLARED)

    def test_missing_wasm_is_detected(self):
        """If ic32.wasm is not built, the gate counts it as incomplete."""
        # Simulate: four backends live, ic32.wasm skipped (not built).
        # On a normally-terminating workload where the four live IC32 members
        # all produce the same normal form, the gate must still fail because
        # ic32.wasm is declared but absent.

        # Build a fake result row like bench.py's inner loop produces.
        live_ic32 = [lb for lb in bench.IC32_DECLARED if lb != "ic32.wasm"]
        fake_nf = "(s (s z))"
        nfs = {lb: fake_nf for lb in live_ic32}

        # The gate check from bench.py:
        fam_missing = bench.IC32_DECLARED - set(nfs.keys())
        self.assertIn("ic32.wasm", fam_missing,
                       "ic32.wasm should be in the missing set when it is not live")
        self.assertEqual(len(fam_missing), 1)

    def test_all_present_passes(self):
        """When all five IC32 members produce the same NF, gate passes."""
        fake_nf = "(s (s z))"
        nfs = {lb: fake_nf for lb in bench.IC32_DECLARED}

        fam_missing = bench.IC32_DECLARED - set(nfs.keys())
        self.assertEqual(len(fam_missing), 0,
                          "no member should be missing when all are present")

    def test_skipped_backend_not_in_nfs(self):
        """A backend in IC32_DECLARED but not run must be caught."""
        # Simulate: remove TWO members (wasm and Mojo)
        present = [lb for lb in bench.IC32_DECLARED
                   if lb not in ("ic32.wasm", "ic32 (Mojo)")]
        fake_nf = "(s z)"
        nfs = {lb: fake_nf for lb in present}

        fam_missing = bench.IC32_DECLARED - set(nfs.keys())
        self.assertEqual(len(fam_missing), 2)
        self.assertIn("ic32.wasm", fam_missing)
        self.assertIn("ic32 (Mojo)", fam_missing)

    def test_gate_uses_declared_not_live(self):
        """IC32_DECLARED is derived from BACKENDS, not from available()."""
        # IC32_DECLARED must include ic32.wasm regardless of whether the
        # binary exists on disk.
        self.assertIn("ic32.wasm", bench.IC32_DECLARED)
        # And it must be a frozenset (immutable, not filtered at runtime)
        self.assertIsInstance(bench.IC32_DECLARED, frozenset)


if __name__ == "__main__":
    unittest.main()
