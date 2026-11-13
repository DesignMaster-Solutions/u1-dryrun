import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import toolchange_retraction as tr  # noqa: E402


def gcode(pull_1, pull_4, own="5,nil,nil,7", printer="3,4,6,8"):
    """The shape of a Snapmaker Orca 2.4.1 tower change: the leaving head retracts in two moves after UNLOAD."""
    def change(new, mm):
        return ["G1 E-1.5 F1800", "; CP TOOLCHANGE UNLOAD", "G1 E-%g F1800" % (mm - .24), "G1 X20 Y233 E-.24",
                "T%d" % new, "G1 E2 F1200", "; CP TOOLCHANGE WIPE", "G1 E-1.5 F1200", "G1 X1 Y1 E1"]
    return (["T0", "G1 X1 Y1 E1"] + change(3, pull_1) + change(0, pull_4) + change(3, pull_1)
            + ["; filament_retract_length_toolchange = " + own, "; retract_length_toolchange = " + printer])


class ToolchangeRetractionTest(unittest.TestCase):
    def test_measures_the_leaving_head_only_inside_the_unload(self):
        want, seen = tr.find(gcode(5, 3))
        self.assertEqual(want, {0: 5.0, 1: 4.0, 2: 6.0, 3: 7.0})  # the filament's own value, else the printer's
        self.assertEqual(seen, {0: [5.0], 3: [3.0]})

    def test_exit_codes(self):
        for lines, want in ((gcode(5, 3), 1),                      # OrcaSlicer#1085: head 4 parked with head 1's 3 mm
                            (gcode(5, 7), 0),
                            (gcode(3, 8, own="nil,nil,nil,nil"), 0),
                            (gcode(3, 8)[:-2] + ["; retract_length_toolchange = 3,4,6,8"], 0),  # no filament key
                            (["T0", "G1 X1 Y1 E1", "T1", "; retract_length_toolchange = 2,2"], 0),  # no tower
                            (gcode(5, 3)[:-2], 2)):
            with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as f:
                f.write("\n".join(lines))
            try:
                self.assertEqual(tr.main(["x", f.name]), want, lines[-2:])
            finally:
                os.unlink(f.name)
        self.assertEqual(tr.main(["x", "/nonexistent.gcode"]), 2)


if __name__ == "__main__":
    unittest.main()
