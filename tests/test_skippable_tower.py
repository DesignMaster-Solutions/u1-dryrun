import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import skippable_tower as st  # noqa: E402

# Shape of an Orca tool change on the tower: the wipe on the model and the end of that object
# come inside the tower block.
GCODE = "\n".join([
    "EXCLUDE_OBJECT_DEFINE NAME=ring CENTER=105,105 POLYGON=[[5,5],[205,5],[205,205],[5,205],[5,5]]",
    "EXCLUDE_OBJECT_START NAME=ring",
    "G1 X6.884 Y204.02 E.04522",
    "; WIPE_TOWER_START",
    "G1 X6.181 Y203.317 E-.56783",
    "EXCLUDE_OBJECT_END NAME=ring",
    "G91",
    "G1 Z1.5 F1800",
    "G90",
    "T1",
    "G1 X241.842 Y105.35 Z.65",
    "G1  X259.092  E0.9580 ; X999 in a comment is not a move",
    "; WIPE_TOWER_END",
    "; WIPE_TOWER_START",
    "G1  Y122.000  E0.1160",
    "; WIPE_TOWER_END",
    "G1 X50 Y50",
])


class SkippableTowerTest(unittest.TestCase):
    def test_wraps_each_tower_block_after_the_model_ends(self):
        out, n = st.process(GCODE)
        self.assertEqual(n, 2)
        lines = out.split("\n")
        start = "EXCLUDE_OBJECT_START NAME=prime_tower"
        self.assertEqual(lines.count(start), 2)
        self.assertEqual(lines.count("EXCLUDE_OBJECT_END NAME=prime_tower"), 2)
        # the wipe on the model stays in the model's object; the lift and the tool change stay outside
        # the tower's, so skipping the tower cannot drop them (the dock scar measured on 11 Nov 2026)
        self.assertEqual(lines[lines.index("T1") + 1], start)
        self.assertLess(lines.index("G1 Z1.5 F1800"), lines.index(start))
        self.assertEqual(lines[lines.index("; WIPE_TOWER_END") - 1], "EXCLUDE_OBJECT_END NAME=prime_tower")

    def test_defines_the_tower_from_its_own_moves_only(self):
        out, _ = st.process(GCODE)
        define = next(line for line in out.split("\n") if line.startswith("EXCLUDE_OBJECT_DEFINE NAME=prime_tower"))
        self.assertIn("POLYGON=[[241.842,105.35],[259.092,105.35],[259.092,122],[241.842,122],[241.842,105.35]]", define)

    def test_without_the_labels_every_line_is_the_slicers(self):
        out, _ = st.process(GCODE)
        kept = [line for line in out.split("\n") if "prime_tower" not in line]
        self.assertEqual(kept, GCODE.split("\n"))

    def test_second_run_and_file_without_tower_change_nothing(self):
        out, _ = st.process(GCODE)
        self.assertEqual(st.process(out), (out, 0))
        self.assertEqual(st.process("G1 X1 Y1\n"), ("G1 X1 Y1\n", 0))


if __name__ == "__main__":
    unittest.main()
