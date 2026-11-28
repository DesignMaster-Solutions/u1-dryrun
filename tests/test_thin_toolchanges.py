import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import thin_toolchanges as tt  # noqa: E402

# the shape of layer 241 in Snapmaker/OrcaSlicer#1214: PETG model on head 3, a PLA interface visit of 0.48 mm on head 1
START = ["M83", "T2", ";LAYER_CHANGE", ";Z:0.2", ";TYPE:Outer wall", "G1 X1 Y1 E5"]


def change(head, tower_mm, kind, part_mm):
    return ["; WIPE_TOWER_START", "T%d" % head, "G1 E5 F1800", ";TYPE:Prime tower", "G1 X10 Y10 E%g" % tower_mm,
            "; WIPE_TOWER_END", ";TYPE:" + kind, "G1 X2 Y2 E%g" % part_mm, "G1 E-0.8", "G1 X3 Y3"]


THIN = START + [";LAYER_CHANGE", ";Z:48.2"] + change(0, 42.7, "Support interface", 0.477) \
    + change(2, 37.0, "Outer wall", 12.0)
FINE = START + [";LAYER_CHANGE", ";Z:48.2"] + change(0, 20.0, "Support interface", 6.5) \
    + change(2, 20.0, "Outer wall", 12.0)


class ThinToolchangesTest(unittest.TestCase):
    def test_measures_each_visit_on_and_off_the_tower(self):
        v = tt.visits(THIN)
        self.assertEqual([(x[0], x[2]) for x in v], [(0, 2), (2, 0), (2, 2)])
        self.assertAlmostEqual(v[1][3], 42.7)
        self.assertEqual(v[1][4], {"Support interface": 0.477})
        self.assertEqual(v[1][1], 48.2)

    def test_prime_push_and_retraction_do_not_count(self):
        self.assertNotIn("Prime tower", tt.visits(THIN)[1][4])
        self.assertAlmostEqual(sum(tt.visits(THIN)[2][4].values()), 12.0)

    def test_exit_codes(self):
        cases = ((THIN, [], 1), (FINE, [], 0), (THIN, ["0.4"], 0), (FINE, ["7"], 1),
                 (["M82", "T0", ";LAYER_CHANGE", "G1 X1 Y1 E1"], [], 2), (["G1 X1 Y1"], [], 2))
        for lines, extra, want in cases:
            with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as f:
                f.write("\n".join(lines))
            try:
                self.assertEqual(tt.main(["x", f.name] + extra), want, (lines, extra))
            finally:
                os.unlink(f.name)
        self.assertEqual(tt.main(["x", "/nonexistent.gcode"]), 2)

    def test_real_slice_with_a_late_interface_visit_is_fine(self):
        path = os.path.join(HERE, "..", "examples", "bed-for-late-interface-orca-2.4.1.gcode.gz")
        self.assertEqual(tt.main(["x", path]), 0)


if __name__ == "__main__":
    unittest.main()
