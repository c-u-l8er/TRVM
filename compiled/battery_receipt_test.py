"""battery_receipt_test.py -- a battery receipt must not be replaced by a narrower one (T7, `dt_0087`).

The defect, found by hitting it on 2026-09-19: `battery.py --quick` and `--worlds` default to the SAME `--out`
as a full run, so a development smoke silently overwrote `results-battery.json` -- the file `README.md` and
`FOUNDATION_LANE.md` quote when they say how many pairs agreed -- replacing a 59-pair `quick: false` record with
a 33-pair `quick: true` one. Nothing refused it, nothing warned, and the only evidence was a smaller number
nobody had reason to re-read. It was caught by hand and the file restored with `git checkout`.

That is a gate going quiet AND a measurement-identity fault: the record stops saying what was actually admitted.
These cases are written against the defect, not the feature -- each one constructs the situation that used to
pass silently and asserts it now refuses, and the last two assert the refusal does NOT over-reach.

    PYTHONDONTWRITEBYTECODE=1 python3 -B battery_receipt_test.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import fold                                   # noqa: E402  (sets up the TRVM import paths)
import battery as B                           # noqa: E402


def receipt(pairs, **kw):
    r = {"pairs": [{"world": w, "scenario": s} for w, s in pairs]}
    r.update(kw)
    return r


def write(path, r):
    with open(path, "w") as f:
        json.dump(r, f)


FULL = [("chain30", "demo"), ("chain30", "fuzz-a"), ("golden-demo", "demo"), ("golden-demo", "fuzz-a")]
QUICK = [("chain30", "demo"), ("golden-demo", "demo")]


class Narrowing(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.p = os.path.join(self.d.name, "results-battery.json")
        self.addCleanup(self.d.cleanup)

    def test_1_a_quick_run_REFUSES_to_replace_a_full_record(self):
        """The exact situation of 2026-09-19: 33 pairs over 59."""
        write(self.p, receipt(FULL, quick=False))
        with self.assertRaises(SystemExit) as e:
            B.refuse_narrowing(self.p, QUICK)
        msg = str(e.exception)
        self.assertIn("NARROW", msg)
        self.assertIn("covers 4 pairs", msg)
        self.assertIn("this run covers 2", msg)
        self.assertIn("would drop 2", msg)
        # and it names one, so the refusal is actionable rather than a number
        self.assertIn("chain30/fuzz-a", msg)

    def test_2_the_file_is_NOT_touched_by_a_refusal(self):
        write(self.p, receipt(FULL, quick=False))
        before = open(self.p).read()
        with self.assertRaises(SystemExit):
            B.refuse_narrowing(self.p, QUICK)
        self.assertEqual(open(self.p).read(), before)

    def test_3_a_worlds_subset_over_the_standing_battery_is_the_same_refusal(self):
        """`--worlds chain30` is a development smoke and defaults to the admission's own file too."""
        write(self.p, receipt(FULL))
        with self.assertRaises(SystemExit):
            B.refuse_narrowing(self.p, [("chain30", "demo"), ("chain30", "fuzz-a")])

    def test_4_a_non_gated_run_over_a_GATED_one_is_caught_without_reading_a_flag(self):
        """The comparison is the pair SET, so `TRVM_BATTERY_HUGE` needs no special case."""
        gated = FULL + [("spinner-w63", "demo")]
        write(self.p, receipt(gated, huge=True))
        with self.assertRaises(SystemExit) as e:
            B.refuse_narrowing(self.p, FULL)
        self.assertIn("spinner-w63/demo", str(e.exception))

    def test_5_force_writes_and_the_receipt_SAYS_what_it_replaced(self):
        """A deliberate narrowing is a decision; it should read like one in the record."""
        write(self.p, receipt(FULL, quick=False))
        note = B.refuse_narrowing(self.p, QUICK, force=True)
        self.assertIsNotNone(note)
        self.assertEqual(note["replaced_pairs"], 4)
        self.assertIn("would drop 2", note["replaced_broader"])


class DoesNotOverReach(unittest.TestCase):
    """A refusal that fires when nothing is being lost is worse than no refusal: it teaches --force."""

    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.p = os.path.join(self.d.name, "results-battery.json")
        self.addCleanup(self.d.cleanup)

    def test_6_an_equal_run_writes(self):
        write(self.p, receipt(FULL))
        self.assertIsNone(B.refuse_narrowing(self.p, FULL))

    def test_7_a_BROADER_run_writes(self):
        write(self.p, receipt(QUICK, quick=True))
        self.assertIsNone(B.refuse_narrowing(self.p, FULL))

    def test_8_a_run_that_adds_and_drops_nothing_of_the_old_writes(self):
        write(self.p, receipt(QUICK))
        self.assertIsNone(B.refuse_narrowing(self.p, QUICK + [("new-world", "demo")]))

    def test_9_no_file_yet_writes(self):
        self.assertIsNone(B.refuse_narrowing(self.p, QUICK))

    def test_10_a_file_that_is_not_a_receipt_is_left_to_the_writer(self):
        """Refusing on unparseable bytes would make an unrelated stray file block the battery."""
        with open(self.p, "w") as f:
            f.write("not json{")
        self.assertIsNone(B.refuse_narrowing(self.p, QUICK))
        write(self.p, {"note": "a receipt with no pairs key"})
        self.assertIsNone(B.refuse_narrowing(self.p, QUICK))


class AgainstTheRealRecords(unittest.TestCase):
    """The committed receipts are the regression fixture: the real full run must refuse the real quick run."""

    def load(self, name):
        with open(os.path.join(HERE, name)) as f:
            return json.load(f)

    def test_11_the_real_quick_record_would_have_been_refused(self):
        full, quick = self.load("results-battery.json"), self.load("results-battery-quick-t7.json")
        self.assertEqual((len(full["pairs"]), full["quick"]), (59, False))
        self.assertEqual((len(quick["pairs"]), quick["quick"]), (33, True))
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "results-battery.json")
            write(p, full)
            with self.assertRaises(SystemExit):
                B.refuse_narrowing(p, sorted(B.receipt_coverage(quick)))

    def test_12_the_gated_record_refuses_the_standing_one(self):
        huge, full = self.load("results-battery-huge.json"), self.load("results-battery.json")
        self.assertEqual((len(huge["pairs"]), len(full["pairs"])), (61, 59))
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "results-battery.json")
            write(p, huge)
            with self.assertRaises(SystemExit):
                B.refuse_narrowing(p, sorted(B.receipt_coverage(full)))

    def test_13_each_real_record_accepts_itself(self):
        for name in ("results-battery.json", "results-battery-huge.json", "results-c2-backend.json"):
            r = self.load(name)
            with tempfile.TemporaryDirectory() as d:
                p = os.path.join(d, name)
                write(p, r)
                self.assertIsNone(B.refuse_narrowing(p, sorted(B.receipt_coverage(r))), name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
