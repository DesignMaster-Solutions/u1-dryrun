import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import nozzle_flow as nf  # noqa: E402

# the block line is what Snapmaker Orca 2.4.1 wrote for a 4-filament project with head 4 set to High Flow
MOVES = ["T0", "G1 X1 Y1 E1", "T3", "G1 X2 Y2 E1"]
MIXED = MOVES + ["; nozzle_volume_type = standard,standard,standard,high_flow"]
ONE_VALUE = MOVES + ["; nozzle_volume_type = standard"]  # what the CLI writes for a type it does not know


class NozzleFlowTest(unittest.TestCase):
    def test_types_of_the_heads_the_file_uses(self):
        self.assertEqual(nf.find(MIXED), ({0: "standard", 3: "high_flow"}, 4, 2))
        self.assertEqual(nf.find(ONE_VALUE), ({0: "standard"}, 1, 2))

    def test_exit_codes(self):
        cases = ((MIXED, None, 0), (MIXED, "s,s,s,h", 0), (MIXED, "s,s,s,s", 1), (MIXED, "h,s,s,h", 1),
                 (MIXED, "s,h,h,h", 0),  # heads 2 and 3 are not used by the file
                 (MIXED, "s,s", 2), (MIXED, "s,s,s,x", 2), (ONE_VALUE, "s,s,s,s", 2), (MOVES, None, 2),
                 (["; nozzle_volume_type = standard"], None, 2))
        for lines, installed, want in cases:
            with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as f:
                f.write("\n".join(lines))
            try:
                argv = ["x", f.name] + ([installed] if installed else [])
                self.assertEqual(nf.main(argv), want, (lines[-1], installed))
            finally:
                os.unlink(f.name)
        self.assertEqual(nf.main(["x", "/nonexistent.gcode"]), 2)


if __name__ == "__main__":
    unittest.main()
