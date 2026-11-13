import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import z_offset_lost as zo  # noqa: E402

# the start of a two-colour job without a prime tower, z_offset = 0.05 (Snapmaker Orca 2.4.1, macOS
# command line): the first move down is G1 Z.25, the next Z word is Z.3
LOST = [";LAYER_CHANGE", ";Z:0.25", "G1 Z.65 F30000", "G1 X100 Y100", "G1 Z.25", ";TYPE:Inner wall",
        "G1 X110 Y100 E.8", "G1 X110 Y110 E.8", "G1 X119.6 Y119.6 Z.3 F30000", ";TYPE:Outer wall",
        "G1 X100 Y119 E.8", "; z_offset = 0.05"]
KEPT = [line.replace("G1 Z.25", "G1 Z.3") for line in LOST]
ZERO = LOST[:-1] + ["; z_offset = 0"]


class ZOffsetLostTest(unittest.TestCase):
    def test_moves_printed_without_the_offset_are_counted(self):
        self.assertEqual(zo.find(LOST), (0.05, 3, [(7, 0.25, 0.25), (8, 0.25, 0.25)]))
        self.assertEqual(zo.find(KEPT), (0.05, 3, []))

    def test_no_offset_means_nothing_to_check(self):
        self.assertEqual(zo.find(ZERO), (0.0, 0, []))
        self.assertEqual(zo.find(LOST[:-1]), (0.0, 0, []))

    def test_relative_hop_is_followed(self):
        # G91 Z.4 from Z.3 is Z.7, then the absolute move down without the offset
        lines = [";Z:0.25", "G1 Z.3", "G91", "G1 Z.4", "G90", "G1 Z.25", "G1 X1 Y1 E1", "; z_offset = 0.05"]
        self.assertEqual(zo.find(lines)[2], [(7, 0.25, 0.25)])

    def test_exit_codes(self):
        for lines, want in ((LOST, 1), (KEPT, 0), (ZERO, 0)):
            with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as f:
                f.write("\n".join(lines))
            try:
                self.assertEqual(zo.main(["x", f.name]), want, lines)
            finally:
                os.unlink(f.name)
        self.assertEqual(zo.main(["x", "/nonexistent.gcode"]), 2)


if __name__ == "__main__":
    unittest.main()
