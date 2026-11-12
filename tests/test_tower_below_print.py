import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import tower_below_print as tb  # noqa: E402

# the shape of the tool change at layer 189 of a 38 mm part sliced with "No sparse layers"
# (Snapmaker Orca 2.4.1, macOS command line): the part is at Z37.85 and the tower is printed at Z0.2
PART = [";TYPE:Outer wall", "G1 Z37.85 F30000", "G1 X80 Y80 E.5 F1800"]
LOW = PART + [";TYPE:Prime tower", "G91", "G1 Z1.5 F600", "G90", "T1", "G1 Z.2 F30000",
              "G1  X34.809  E0.1140 F990", "G1  X20.309  E0.5511 F990"]
LEVEL = PART + [";TYPE:Prime tower", "T1", "G1 Z37.85 F30000", "G1  X34.809  E0.1140 F990"]


class TowerBelowPrintTest(unittest.TestCase):
    def test_tower_far_below_the_part_is_reported_once(self):
        self.assertEqual(tb.find(LOW), (2, [(10, 0.2, 37.85)]))
        self.assertEqual(tb.find(LEVEL), (1, []))

    def test_relative_z_hop_is_followed(self):
        # the hop is G91 Z1.5: read as absolute it would put the tower at Z1.5 and hide a 1.2 mm drop
        lines = [";TYPE:Outer wall", "G1 Z2.7", "G1 X1 E1", ";TYPE:Prime tower", "G91", "G1 Z1.5", "G90",
                 "G1 Z1.5", "G1 X2 E1"]
        self.assertEqual(tb.find(lines)[1], [(9, 1.5, 2.7)])
        self.assertEqual(tb.find(lines, max_drop=2)[1], [])

    def test_exit_codes(self):
        for lines, want in ((LOW, 1), (LEVEL, 0), (PART, 0)):
            with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as f:
                f.write("\n".join(lines))
            try:
                self.assertEqual(tb.main(["x", f.name]), want, lines)
            finally:
                os.unlink(f.name)
        self.assertEqual(tb.main(["x", "/nonexistent.gcode"]), 2)


if __name__ == "__main__":
    unittest.main()
