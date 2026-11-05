import gzip
import os
import re
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


# The same plate sliced headless on Linux (tools/slice_sign_linux.sh): the official 2.4.1 AppImage, and the fork's
# build of the fix (https://github.com/DesignMaster-Solutions/OrcaSlicer/actions/runs/41959375186).
LINUX_241, LINUX_PATCHED = "sign-orca-2.4.1-linux.gcode.gz", "sign-orca-2.4.1-patched-linux.gcode.gz"


def final_purge_entry(text):
    """(Z the final purge runs at, whether anything unretracts after the last object) for the last tower block."""
    head = text[:text.rindex(ab.START)]
    zs = re.findall(r"^G[0-3] [^;\n]*Z([0-9.]+)", head, re.M)
    after_object = head[head.rindex("EXCLUDE_OBJECT_END"):]
    return float(zs[-1]), bool(re.search(r"^G1 E[0-9.]+ ", after_object, re.M))


class RealBuildTest(unittest.TestCase):
    def test_the_patched_build_passes_against_the_official_build(self):
        verdict = ab.compare(example(LINUX_241), example(LINUX_PATCHED))
        self.assertTrue(verdict["ok"], verdict)
        self.assertEqual(verdict["blocks"], [16, 16])

    def test_241_purges_on_the_last_tower_layer_still_retracted_and_the_fix_does_not(self):
        self.assertEqual(final_purge_entry(example(LINUX_241)), (3.05, False))
        self.assertEqual(final_purge_entry(example(LINUX_PATCHED)), (3.25, True))


if __name__ == "__main__":
    unittest.main()
