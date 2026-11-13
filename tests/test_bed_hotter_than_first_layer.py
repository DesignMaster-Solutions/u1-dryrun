import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import bed_hotter_than_first_layer as bh  # noqa: E402

# the shape of a Snapmaker Orca 2.4.1 slice: PLA (bed 65) on head 1, a bed-80 filament on head 2 (OrcaSlicer#1073)
BLOCK = ["; curr_bed_type = High Temp Plate", "; filament_type = PLA;PETG", "; hot_plate_temp_initial_layer = 65,80"]


def gcode(bed, later=()):
    return (["M140 S%d" % bed, "T0", "M190 S%d" % bed, ";LAYER_CHANGE", "T0", "G1 X1 Y1 E1", ";LAYER_CHANGE",
             "G1 X2 Y2 E1"] + list(later) + BLOCK)


NEVER = gcode(80)                                                   # head 2 never prints
LATER = gcode(80, [";LAYER_CHANGE", "T1", "G1 X3 Y3 E1"])           # head 2 first prints on layer 3
RIGHT = gcode(65, [";LAYER_CHANGE", "T1", "G1 X3 Y3 E1"])
BOTH = ["M190 S80", ";LAYER_CHANGE", "T0", "G1 X1 Y1 E1", "T1", "G1 X2 Y2 E1", ";LAYER_CHANGE"] + BLOCK


class BedHotterTest(unittest.TestCase):
    def test_bed_set_for_a_filament_that_is_not_on_the_first_layer(self):
        self.assertEqual(bh.find(NEVER), (80.0, [65.0, 80.0], {0}, {}))
        self.assertEqual(bh.find(LATER), (80.0, [65.0, 80.0], {0}, {1: 3}))

    def test_travel_and_retraction_do_not_count_as_printing(self):
        lines = ["M190 S80", ";LAYER_CHANGE", "T0", "G1 X1 Y1 E1", "T1", "G1 X5 Y5", "G1 E-0.8", ";LAYER_CHANGE"] + BLOCK
        self.assertEqual(bh.find(lines)[2], {0})

    def test_exit_codes(self):
        for lines, want in ((NEVER, 1), (LATER, 1), (RIGHT, 0), (BOTH, 0), (NEVER[:-3], 2),
                            # head 2 prints the first layer and the block has one value: nothing to compare
                            (["M190 S80", ";LAYER_CHANGE", "T1", "G1 X1 Y1 E1"] + BLOCK[:2]
                             + ["; hot_plate_temp_initial_layer = 65"], 0)):
            with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as f:
                f.write("\n".join(lines))
            try:
                self.assertEqual(bh.main(["x", f.name]), want, lines)
            finally:
                os.unlink(f.name)
        self.assertEqual(bh.main(["x", "/nonexistent.gcode"]), 2)


if __name__ == "__main__":
    unittest.main()
