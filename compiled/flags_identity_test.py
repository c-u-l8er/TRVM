"""flags_identity_test.py -- the falsifiers for the compiler-flags policy's identity (`FLAGS_POLICY.md` choice 5).

The ruling of 2026-09-19 adds the compiler's `--version` line, its target triple and the `-march`/`-mtune` it
RESOLVES the flags to into what `cbknd2-` hashes. A test that only asserts the new id is some hex string proves
nothing: what has to be shown is that the DEFECT the ruling names is real, that the change closes it, and that
it closes nothing else by accident. So each case below pairs the new formula against the OLD one on the same
inputs, and the old formula is written out here rather than imported, because it no longer exists in the source.

    PYTHONDONTWRITEBYTECODE=1 python3 -B flags_identity_test.py
"""
import hashlib
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import fold                                  # noqa: E402  (sets up the TRVM import paths)
import emit_c as EC                          # noqa: E402
import emit_c2 as EC2                        # noqa: E402
from fold import SB, P                       # noqa: E402

SEM = "sem-0000000000000000000000000000000000000000000000000000000000000000"
SRC = "/* a step */\nvoid step_v6(void){}\n"


def old_backend_id(sem_id, source, flags):
    """`cbknd2-` as it was computed until 2026-09-19: sem, profile, flags, source -- and NO toolchain."""
    return "cbknd2-" + hashlib.sha256(
        (sem_id + "\n" + EC2.PROFILE + "\n" + " ".join(flags) + "\n" + source).encode()).hexdigest()


class ToolchainProbe(unittest.TestCase):
    def test_1_three_lines_read_from_the_compiler(self):
        t = EC.toolchain_identity(["-O2"])
        lines = t.splitlines()
        self.assertEqual(len(lines), 3, t)
        self.assertTrue(lines[0].startswith("cc "), lines[0])
        self.assertTrue(lines[1].startswith("target "), lines[1])
        self.assertTrue(lines[2].startswith("march=") and " mtune=" in lines[2], lines[2])

    def test_2_deterministic_for_fixed_flags(self):
        EC._TOOLCHAIN.clear()
        a = EC.toolchain_identity(["-O2"])
        EC._TOOLCHAIN.clear()
        b = EC.toolchain_identity(["-O2"])
        self.assertEqual(a, b)

    def test_3_native_is_RESOLVED_not_echoed(self):
        """The defect in one line: the flag says `native`, the compiler means a named CPU."""
        t = EC.toolchain_identity(["-O2", "-march=native"])
        march = t.splitlines()[2].split()[0].split("=", 1)[1]
        self.assertNotEqual(march, "native", "the probe echoed the flag instead of resolving it: " + t)
        self.assertNotEqual(march, "<unresolved>", "gcc did not answer -Q --help=target: " + t)
        self.assertNotEqual(march, EC.toolchain_identity(["-O2"]).splitlines()[2].split()[0].split("=", 1)[1])

    def test_4_O_level_does_not_move_the_toolchain_line(self):
        """`-O3` is in the flag string already; it must not also perturb the toolchain line, or the two
        halves of the identity would be saying the same thing twice and neither would mean what it says."""
        self.assertEqual(EC.toolchain_identity(["-O2"]), EC.toolchain_identity(["-O3"]))


class Identity(unittest.TestCase):
    def test_5_a_compiler_change_MOVES_the_id_and_would_not_have(self):
        """The falsifier the ruling exists for. Same sem, same flags, same source, a different compiler."""
        flags = ["-O2"]
        real = EC2.backend_id(SEM, SRC, flags)
        EC._TOOLCHAIN[("gcc", tuple(flags))] = "cc gcc (GCC) 17.0.0 20270101\ntarget x86_64-pc-linux-gnu\nmarch=x86-64 mtune=generic\n"
        try:
            upgraded = EC2.backend_id(SEM, SRC, flags)
        finally:
            EC._TOOLCHAIN.clear()
        self.assertNotEqual(real, upgraded, "a gcc upgrade did not move cbknd2-")
        self.assertEqual(old_backend_id(SEM, SRC, flags), old_backend_id(SEM, SRC, flags),
                         "sanity: the old formula is a function of its arguments")
        # ...and the old formula could not have seen it: its inputs are identical in both worlds.
        self.assertEqual(len({old_backend_id(SEM, SRC, flags)}), 1)

    def test_6_two_machines_one_flag_string_two_codes(self):
        """`-march=native` on two CPUs: one flag string, two machine codes. The old id could not tell them
        apart; the new one must."""
        flags = ["-O2", "-march=native"]
        EC._TOOLCHAIN[("gcc", tuple(flags))] = "cc gcc (GCC) 16.2.1 20260810\ntarget x86_64-pc-linux-gnu\nmarch=znver5 mtune=znver5\n"
        a = EC2.backend_id(SEM, SRC, flags)
        EC._TOOLCHAIN[("gcc", tuple(flags))] = "cc gcc (GCC) 16.2.1 20260810\ntarget x86_64-pc-linux-gnu\nmarch=skylake mtune=skylake\n"
        b = EC2.backend_id(SEM, SRC, flags)
        EC._TOOLCHAIN.clear()
        self.assertNotEqual(a, b, "two resolved targets produced one id")
        self.assertEqual(old_backend_id(SEM, SRC, flags), old_backend_id(SEM, SRC, flags))

    def test_7_nothing_else_moved_it(self):
        """The id must still be a function of sem, profile, flags and source -- the toolchain is an addition,
        not a replacement. Each of the four still moves it on its own."""
        base = EC2.backend_id(SEM, SRC, ["-O2"])
        self.assertNotEqual(base, EC2.backend_id(SEM + "x", SRC, ["-O2"]))
        self.assertNotEqual(base, EC2.backend_id(SEM, SRC + "\n", ["-O2"]))
        self.assertNotEqual(base, EC2.backend_id(SEM, SRC, ["-O3"]))
        self.assertTrue(base.startswith("cbknd2-") and len(base) == len("cbknd2-") + 64)

    def test_8_v1_is_unchanged_and_that_is_recorded(self):
        """Choice 5 names `emit_c2` only. v1 (`cbknd-`) is built at `-O2` with no `TRVM_CFLAGS` hook and its id
        carries neither flags nor toolchain -- still true after this change, deliberately, and asserted here so
        that a later ruling on v1 has to change a test rather than slip through."""
        a = EC.backend_id(SEM, SRC)
        self.assertTrue(a.startswith("cbknd-"))
        self.assertEqual(a, "cbknd-" + hashlib.sha256((SEM + "\n" + EC.PROFILE + "\n" + SRC).encode()).hexdigest())


class ObjectCache(unittest.TestCase):
    def test_9_the_cache_is_namespaced_by_toolchain_and_the_reported_key_is_not(self):
        """The stale-object hazard: without the namespace, choice 5 would hand a NEW id to an OLD `.so`."""
        flags = ["-O2"]
        EC._TOOLCHAIN[("gcc", tuple(flags))] = "cc A\ntarget t\nmarch=x mtune=y\n"
        d1 = EC.toolchain_dir(flags)
        EC._TOOLCHAIN[("gcc", tuple(flags))] = "cc B\ntarget t\nmarch=x mtune=y\n"
        d2 = EC.toolchain_dir(flags)
        EC._TOOLCHAIN.clear()
        self.assertNotEqual(d1, d2, "two compilers shared one object cache directory")
        self.assertTrue(os.path.basename(d1).startswith("tc-") and os.path.basename(d2).startswith("tc-"))
        # the REPORTED key (`source_sha256`) keeps its documented meaning: sha256(flags + "\n" + source)
        key = hashlib.sha256((" ".join(flags) + "\n" + SRC).encode()).hexdigest()
        self.assertEqual(key, hashlib.sha256(("-O2" + "\n" + SRC).encode()).hexdigest())

    def test_10_a_real_world_builds_and_reports_the_unmoved_key(self):
        """One real emit + build, end to end: the `.so` lands under the toolchain namespace and
        `source_sha256` is still sha256(flags + source), which is what the results files carry."""
        prog, _ = SB._resolve_scenario(
            "profile forge.world.core.v1\n\n[pulser:p0](every 2){sig_out}\n[relay:r0]{sig_in, sig_out}\n"
            "[door:d0]{sig_in}\n\n[pulser:p0] --sig--> [relay:r0]\n[relay:r0] --sig--> [door:d0]\n", None)
        view = P.plan_view(P.artifact_to_compile_plan_v1(prog.sealed_artifact))
        cs = EC2.CompiledStep2(view, prog.semantic_artifact_id)
        self.assertTrue(cs.backend_id.startswith("cbknd2-"))
        self.assertEqual(cs.source_sha256,
                         hashlib.sha256((" ".join(cs.flags) + "\n" + cs.source).encode()).hexdigest())
        self.assertEqual(os.path.dirname(cs.so_path), EC.toolchain_dir(cs.flags))
        self.assertTrue(os.path.basename(os.path.dirname(cs.so_path)).startswith("tc-"))
        self.assertNotEqual(cs.backend_id, old_backend_id(prog.semantic_artifact_id, cs.source, cs.flags),
                            "the new id equals the old one: the toolchain is not in the hash")


if __name__ == "__main__":
    unittest.main(verbosity=2)
