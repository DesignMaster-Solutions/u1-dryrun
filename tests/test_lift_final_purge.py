import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import lift_final_purge as lift  # noqa: E402

TOWER = "; CP TOOLCHANGE START\nM220 B\nM220 S100\n; CP TOOLCHANGE UNLOAD\n"
# The end of the file that really scratched on a U1 (Snapmaker Orca 2.4.1).
FINAL = (
    "G1 X132.503 Y137.672 E.56932\n" + TOWER +
    ";WIDTH:1\nG4 S0\nM220 R\nG1  X17.984 Y139.987 F30000\nG4 S0\nG92 E0\n; CP TOOLCHANGE END\n"
    "G1 E-1.5 F1800\nPRINT_END\n"
)
CONFIG = "; z_hop = 0.4,0.4,0.4,0.4\n"


class LiftTest(unittest.TestCase):
    def test_lifts_before_the_travel_and_comes_back(self):
        out, n = lift.process(FINAL + CONFIG)
        self.assertEqual(n, 1)
        lines = out.splitlines()
        i = lines.index("G1  X17.984 Y139.987 F30000")
        self.assertEqual(lines[i - 4:i], [lift.MARK, "G91", "G1 Z0.4 F600", "G90"])
        self.assertEqual(lines[i + 1:i + 4], ["G91", "G1 Z-0.4 F600", "G90"])

    def test_only_adds_lines(self):
        out, _ = lift.process(FINAL + CONFIG)
        added = out.splitlines()
        for line in (FINAL + CONFIG).splitlines():
            added.remove(line)  # raises if a line of the slicer's file went missing
        self.assertEqual(len(added), 7)

    def test_a_real_tool_change_keeps_its_own_path(self):
        change = TOWER + "G1 X5 Y5 F30000\n[change]\nT1\nG1 X6 Y6 F30000\n; CP TOOLCHANGE END\nG1 X1 Y1 E1\n"
        out, n = lift.process(change + FINAL + CONFIG)
        self.assertEqual(n, 1)
        self.assertTrue(out.startswith(change), "only the last block may change")

    def test_a_last_block_with_a_tool_change_is_not_the_final_purge(self):
        text = "G1 X9 Y9 E1\n" + TOWER + "G1 X5 Y5 F30000\nT1\n; CP TOOLCHANGE END\nG1 X1 Y1 E1\n" + CONFIG
        self.assertEqual(lift.process(text), (text, 0))

    def test_a_file_that_already_lifts_is_left_alone(self):
        text = FINAL.replace("G1  X17.984 Y139.987 F30000", "G1 X17.984 Y139.987 Z12.45 F30000") + CONFIG
        self.assertEqual(lift.process(text), (text, 0))

    def test_a_file_that_already_travelled_is_left_alone(self):
        # what Orca 2.4.0 writes: the travel comes before the block, and it is lifted
        text = "G1 X32.75 Y238.85 Z3.65 F30000\nG1 Z3.25 F30000\nG1 E2 F1800\n" + TOWER + \
            "G4 S0\nG1 X33 Y239 F30000\nG1 X40 Y239 E1\n; CP TOOLCHANGE END\n" + CONFIG
        self.assertEqual(lift.process(text), (text, 0))

    def test_running_it_twice_changes_nothing(self):
        once, _ = lift.process(FINAL + CONFIG)
        self.assertEqual(lift.process(once), (once, 0))

    def test_a_cut_off_last_block_is_left_alone(self):
        text = "G1 X9 Y9 E1\n" + TOWER + "G4 S0\n; CP TOOLCHANGE END\nG1 X1 Y1 E1\n" + TOWER + "G1 X5 Y5 F30000\n"
        self.assertEqual(lift.process(text), (text, 0))

    def test_no_tower_no_change(self):
        text = "G1 X1 Y1 E1\nPRINT_END\n"
        self.assertEqual(lift.process(text), (text, 0))

    def test_height_comes_from_the_file_then_the_default(self):
        self.assertEqual(lift.hop_height("; z_hop = 0.6,0.4\n"), 0.6)
        self.assertEqual(lift.hop_height("; z_hop = 0,0\n"), lift.DEFAULT_HOP)
        self.assertEqual(lift.hop_height("nothing here\n"), lift.DEFAULT_HOP)

    def test_edits_in_place_when_called_like_a_slicer_post_processor(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "a b.gcode")  # the slicer's temp path can have spaces
            with open(path, "w") as f:
                f.write(FINAL + CONFIG)
            script = os.path.join(HERE, "..", "tools", "lift_final_purge.py")
            subprocess.run([sys.executable, script, path], check=True, capture_output=True)
            with open(path) as f:
                self.assertIn(lift.MARK, f.read())


if __name__ == "__main__":
    unittest.main()
