import gzip
import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import ab_final_purge as ab  # noqa: E402
import lift_final_purge as lift  # noqa: E402


def example(name):
    with gzip.open(os.path.join(HERE, "..", "examples", name), "rt", encoding="utf-8", errors="surrogateescape") as f:
        return f.read()


BASE = example("sign-orca-2.4.1.gcode.gz")  # official 2.4.1: the final purge travel has no lift


class AbTest(unittest.TestCase):
    def test_official_241_still_has_the_bare_final_travel(self):
        self.assertTrue(ab.bare_final_travel(BASE))

    def test_a_fix_that_only_lifts_the_final_purge_passes(self):
        fixed, n = lift.process(BASE)
        self.assertEqual(n, 1)
        verdict = ab.compare(BASE, fixed)
        self.assertTrue(verdict["ok"], verdict)
        self.assertEqual(verdict["other_blocks_changed"], [])

    def test_a_fix_that_leaves_the_bare_travel_fails(self):
        verdict = ab.compare(BASE, BASE)
        self.assertFalse(verdict["ok"])
        self.assertTrue(verdict["patched_bare_final_travel"])

    def test_a_fix_that_also_changes_another_tool_change_fails(self):
        fixed, _ = lift.process(BASE)
        first = fixed.index("; CP TOOLCHANGE UNLOAD")
        broken = fixed[:first] + "; CP TOOLCHANGE UNLOAD\nG1 Z9 F600" + fixed[first + len("; CP TOOLCHANGE UNLOAD"):]
        verdict = ab.compare(BASE, broken)
        self.assertFalse(verdict["ok"])
        self.assertEqual(verdict["other_blocks_changed"], [0])

    def test_a_patched_file_with_an_extra_tool_change_fails(self):
        fixed, _ = lift.process(BASE)
        last = fixed.rindex(ab.START)
        end = fixed.index(ab.END, last) + len(ab.END)
        extra = fixed[:end] + "\n" + fixed[last:end] + fixed[end:]
        verdict = ab.compare(BASE, extra)
        self.assertFalse(verdict["ok"])
        self.assertEqual(verdict["blocks"][1], verdict["blocks"][0] + 1)

    def test_a_base_without_the_scratch_proves_nothing(self):
        fixed, _ = lift.process(BASE)
        verdict = ab.compare(fixed, fixed)
        self.assertFalse(verdict["ok"])
        self.assertFalse(verdict["base_bare_final_travel"])


if __name__ == "__main__":
    unittest.main()
