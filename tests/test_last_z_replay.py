import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import last_z_replay as lz  # noqa: E402

EX = os.path.join(HERE, "..", "examples")
LIFT = ["; Change Tool0 -> Tool1 (layer 2)", "G91", "G1 Z1.5 F600", "G90", "G1 F21000", "T1", "G90"]


class LastZReplayTest(unittest.TestCase):
    def test_relative_lift(self):
        self.assertEqual(lz.last_z(LIFT), 1.5)                  # 2.4.1: read as absolute
        self.assertAlmostEqual(lz.last_z(LIFT, 0.65), 2.15)     # PR 1191: a delta from the start Z
        self.assertIsNone(lz.last_z(["M400", "T1"], 0.65))      # no Z move: the slicer keeps its own Z
        self.assertEqual(lz.last_z(["G90", "G1 Z2.65 F600"], 0.65), 2.65)   # by object: absolute, unchanged
        self.assertIsNone(lz.last_z(["G1 Z123.456789 F600"]))   # both versions parse 8 characters at most

    def test_examples(self):
        # OrcaSlicer#1083, docs/orca-2.4.1-no-tower-return.md: (2.4.1 wrong, PR wrong, return follows the rule)
        for name, want in (("no-tower-return-orca-2.4.1.gcode.gz", (50, 0, 50)),
                           ("no-tower-return-orca-2.4.1-absolute-lift.gcode.gz", (0, 0, 50))):
            rows = lz.replay(lz.read_lines(os.path.join(EX, name)))
            self.assertEqual(len(rows), 50, name)
            got = (sum(abs(o - r) > 1e-6 for _, r, o, _, _ in rows),
                   sum(abs(n - r) > 1e-6 for _, r, _, n, _ in rows),
                   sum(abs(ret - max(la, o + lz.HOP)) < 1e-6 for la, _, o, _, ret in rows))
            self.assertEqual(got, want, name)


if __name__ == "__main__":
    unittest.main()
