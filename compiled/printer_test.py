#!/usr/bin/env python3
"""printer_test.py -- the C canonical printer alone (README section 2j).

    PYTHONDONTWRITEBYTECODE=1 python3 -B printer_test.py

`payload.py` is the printer's ORACLE and this file is not a second one: where a rendering is checked here it is
checked against `ic_ref.show(ic_ref.parse(compiler.enc_state_v6(...)))`, the same reference payload.py uses, or
against bytes derived BY HAND from `ic_ref.show`'s rule and written out in the assertion. No re-implementation of
the grammar lives in this file, because a printer checked against a second printer written by the same author on
the same afternoon is checked against nothing.

What it pins that a scenario run does not:
  * random states rather than a scenario's, so lanes hit their extremes and bit patterns hit all-zeros/all-ones
  * the 63-bit lane, where a signed right shift and a two's-complement bit disagree if you get it wrong
  * the name crossover at 26 (`z` -> `v26`), which a small world never reaches
  * the buffer-growth path, which is otherwise only hit once per world and never observed
  * the refusals: an unknown kind, a width outside 1..63, an enum index outside its size
"""
import ctypes
import os
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
os.environ.setdefault("TRVM_BATTERY_HUGE", "1")      # the 63-lane world is emitted and printed; only its FOLD is gated

import fold as F                                      # noqa: E402
import battery as B                                   # noqa: E402
import printer as PR                                  # noqa: E402
from ic_ref import show                                # noqa: E402
C, O = F.C, F.O

L = "λ"


def reference(view, st):
    """The rendering the C printer must reproduce -- payload.py's, byte for byte."""
    O.reset_runtime()
    return show(O.parse(C.enc_state_v6(view, st))).encode()


def random_slots(desc, nfields, width, rnd):
    """A state vector that is random but VALID for its descriptor: an enum index is in range, a flag is a flag,
    a lane is inside its width. Extremes are drawn deliberately -- 0, -1, and both ends of the signed range --
    because a bit loop is wrong at the ends or nowhere."""
    a = [0] * width
    for i in range(nfields):
        kind, arg, off = desc[3 * i], desc[3 * i + 1], desc[3 * i + 2]
        if kind == PR.K_ONEHOT:
            a[off] = rnd.randrange(arg)
        elif kind == PR.K_BINP:
            a[off] = rnd.randrange(1 << arg)
        elif kind == PR.K_ONCE:
            a[off], a[off + 1] = rnd.randrange(2), rnd.randrange(1 << arg)
        elif kind == PR.K_PAIR:
            a[off], a[off + 1] = rnd.randrange(2), rnd.randrange(2)
        elif kind == PR.K_FAULT:
            a[off] = rnd.randrange(2)
        else:                                          # pose / rotor: four lanes of `arg` bits, signed
            hi = 1 << (arg - 1)
            pool = [0, -1, 1, hi - 1, -hi, hi - 1, -hi + 1]
            for l in range(4):
                a[off + l] = rnd.choice(pool) if rnd.random() < 0.5 else rnd.randrange(-hi, hi)
    return a


class Shapes(unittest.TestCase):
    """The grammar and the naming order, on bytes derived by hand from `ic_ref.show`'s rule."""

    def setUp(self):
        self.lib = PR._lib()[0]

    def call(self, desc, nfields, width, slots, cap=4096):
        d = (ctypes.c_int64 * len(desc))(*desc)
        a = (ctypes.c_int64 * width)(*slots)
        buf = ctypes.create_string_buffer(cap)
        n = self.lib.trvm_print_state(d, nfields, a, buf, cap)
        return n, (buf.raw[:n] if 0 <= n <= cap else None)

    def test_pair_exact_bytes(self):
        # one wire field, (cur, nxt) = (1, 0).  show names in first-encounter order: the state TUP's binder is
        # `a`, the pair's is `b`, then T's two binders are `c`,`d` and F's are `e`,`f`.
        n, got = self.call([PR.K_PAIR, 0, 0], 1, 2, [1, 0])
        self.assertEqual(got.decode(), f"{L}a.(a {L}b.((b {L}c.{L}d.c) {L}e.{L}f.f))")
        self.assertEqual(n, len(got))

    def test_fault_and_empty_tuple(self):
        self.assertEqual(self.call([PR.K_FAULT, 0, 0], 1, 1, [0])[1].decode(), f"{L}a.(a {L}b.{L}c.c)")
        self.assertEqual(self.call([PR.K_FAULT, 0, 0], 1, 1, [7])[1].decode(), f"{L}a.(a {L}b.{L}c.b)")
        self.assertEqual(self.call([], 0, 0, [])[1].decode(), f"{L}a.a")      # TUP of nothing is the identity

    def test_enum_picks_the_indexed_binder(self):
        # ENUM(4, 2): binders b,c,d,e after the state TUP's a; the body is the third of them.
        got = self.call([PR.K_ONEHOT, 4, 0], 1, 1, [2])[1].decode()
        self.assertEqual(got, f"{L}a.(a {L}b.{L}c.{L}d.{L}e.d)")

    def test_bits_are_lsb_first(self):
        # BINP width 3, value 1 -> bits [T, F, F]
        got = self.call([PR.K_BINP, 3, 0], 1, 1, [1])[1].decode()
        self.assertEqual(got, f"{L}a.(a {L}b.(((b {L}c.{L}d.c) {L}e.{L}f.f) {L}g.{L}h.h))")

    def test_name_crossover_at_26(self):
        # 20 bits = 40 bool binders after two TUP binders, so the counter runs a..z then v26...
        got = self.call([PR.K_BINP, 20, 0], 1, 1, [0b10101010101010101010], cap=1 << 14)[1].decode()
        self.assertIn(f"{L}z.", got)
        self.assertIn(f"{L}v26.", got)
        self.assertLess(got.index(f"{L}z."), got.index(f"{L}v26."))
        self.assertNotIn(f"{L}v25.", got)              # 25 is `z`, never `v25`
        self.assertIn(f"{L}v41.", got)                 # 2 + 2*20 - 1 = 41 binders in all
        self.assertNotIn(f"{L}v42.", got)

    def test_refusals(self):
        self.assertEqual(self.call([99, 0, 0], 1, 1, [0])[0], -1)          # unknown kind
        self.assertEqual(self.call([PR.K_POSE, 64, 0], 1, 4, [0] * 4)[0], -2)   # width over 63
        self.assertEqual(self.call([PR.K_BINP, 0, 0], 1, 1, [0])[0], -2)   # width under 1
        self.assertEqual(self.call([PR.K_ONEHOT, 4, 0], 1, 1, [4])[0], -3)  # index outside the enum
        self.assertEqual(self.call([PR.K_ONEHOT, 4, 0], 1, 1, [-1])[0], -3)

    def test_too_small_a_buffer_reports_the_need_and_writes_nothing_usable(self):
        want = self.call([PR.K_BINP, 20, 0], 1, 1, [123], cap=1 << 14)[1]
        n, got = self.call([PR.K_BINP, 20, 0], 1, 1, [123], cap=8)
        self.assertIsNone(got)
        self.assertEqual(n, len(want))                 # snprintf's contract: the length NEEDED


class AgainstTheReference(unittest.TestCase):
    """Random states of every world in the battery, against `show(parse(enc_state_v6(...)))`."""

    def test_every_world_on_random_states(self):
        rnd = random.Random(20260920)
        checked = 0
        for name, src in B.WORLDS.items():
            sem, view, dig, script, world, claim, seams = F._prepare(src, None)
            cs = F.CompiledStep(view, sem)
            pr = PR.CanonicalPrinter(view)
            desc, nfields, width = PR.descriptor(view)
            self.assertEqual(width, cs.width, name)
            for _ in range(8):
                vals = random_slots(desc, nfields, width, rnd)
                a = (ctypes.c_int64 * width)(*vals)
                self.assertEqual(pr.render(a), reference(view, cs.decode(a)), "%s on a random state" % name)
                checked += 1
        self.assertGreaterEqual(checked, 8 * 19)
        print("\n  %d random states over %d worlds, every one byte-identical" % (checked, len(B.WORLDS)))

    def test_the_63_bit_lane_at_its_extremes(self):
        """w=63 is where a signed right shift and a two's-complement bit part company."""
        wide = [n for n in B.WORLDS if "w63" in n]
        self.assertTrue(wide, "the 63-lane world must be present under TRVM_BATTERY_HUGE")
        sem, view, dig, script, world, claim, seams = F._prepare(B.WORLDS[wide[0]], None)
        cs, pr = F.CompiledStep(view, sem), PR.CanonicalPrinter(view)
        desc, nfields, width = PR.descriptor(view)
        lanes = [i for i in range(nfields) if desc[3 * i] in (PR.K_POSE, PR.K_ROTOR) and desc[3 * i + 1] == 63]
        self.assertTrue(lanes, "the 63-lane world must have a 63-bit pose or rotor")
        for v in (0, -1, 1, (1 << 62) - 1, -(1 << 62), (1 << 62) - 2, -(1 << 62) + 1):
            vals = [0] * width
            for i in lanes:
                for l in range(4):
                    vals[desc[3 * i + 2] + l] = v
            a = (ctypes.c_int64 * width)(*vals)
            self.assertEqual(pr.render(a), reference(view, cs.decode(a)), "63-bit lane at %d" % v)


class Identity(unittest.TestCase):

    def test_the_printer_has_its_own_identity_and_it_is_not_a_backend_id(self):
        self.assertTrue(PR.printer_id().startswith("cprn-"))
        self.assertEqual(len(PR.printer_id()), 5 + 64)

    def test_the_object_speaks_this_module_s_abi(self):
        self.assertEqual(PR._lib()[0].trvm_print_abi(), PR.ABI)

    def test_the_descriptor_is_read_off_slot_map(self):
        """Not re-walked: a field count or a width that disagrees with the step's is the whole failure mode."""
        import emit_c as EC
        for name, src in list(B.WORLDS.items())[:4]:
            sem, view, *_ = F._prepare(src, None)
            desc, nfields, width = PR.descriptor(view)
            fields, w = EC.slot_map(view)
            self.assertEqual((nfields, width), (len(fields), w), name)
            for i, (kind, nm, off, n, spec) in enumerate(fields):
                self.assertEqual(desc[3 * i + 2], off, "%s field %d offset" % (name, i))


if __name__ == "__main__":
    unittest.main(verbosity=2)
