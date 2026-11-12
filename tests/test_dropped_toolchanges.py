import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import dropped_toolchanges as dt  # noqa: E402

EX = os.path.join(HERE, "..", "examples")
# the shape of the two slices of OrcaSlicer#1124 (Snapmaker Orca 2.4.1, macOS command line)
BROKEN = ["T3", "T3", "; Change Tool3 -> Tool3 (layer -1)", "T3",
          "; WIPE_TOWER_START", "; CP EMPTY GRID START", "; CP EMPTY GRID END", "; WIPE_TOWER_END",
          "; filament used [g] = 0.00, 0.00, 0.00, 6.88"]
GOOD = ["T3", "; CP TOOLCHANGE START", "; WIPE_TOWER_START", "; Change Tool3 -> Tool2 (layer 0)", "T2 ; change",
        "; WIPE_TOWER_END", "; filament used [g] = 0.00, 0.00, 5.79, 1.20"]


class DroppedToolChangesTest(unittest.TestCase):
    def test_tower_with_one_head_is_reported(self):
        self.assertEqual(dt.find(BROKEN), ([3], 1, "filament used [g] = 0.00, 0.00, 0.00, 6.88"))
        self.assertEqual(dt.find(GOOD)[:2], ([2, 3], 1))

    def test_exit_codes(self):
        import tempfile
        for lines, want in ((BROKEN, 1), (GOOD, 0), (["T0", "G1 X1"], 0), (["G1 X1"], 2)):
            with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as f:
                f.write("\n".join(lines))
            try:
                self.assertEqual(dt.main(["x", f.name]), want, lines)
            finally:
                os.unlink(f.name)

    def test_real_multicolour_examples_are_fine(self):
        for name in ("tower-right-edge-orca-2.4.1.3mf", "sign-orca-2.4.0.gcode.gz", "ring-orcaslicer-2.4.2.gcode.gz"):
            heads, tower, _ = dt.find(dt.read_lines(os.path.join(EX, name)))
            self.assertFalse(tower and len(heads) == 1, name)


if __name__ == "__main__":
    unittest.main()
