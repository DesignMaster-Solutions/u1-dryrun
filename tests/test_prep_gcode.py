import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dryrun"))
import prep_gcode  # noqa: E402

# The U1 start G-code ships with Chinese comments; the slicer copies them into every file.
START = "PRINT_START\n;===== 床面异物检测 ========\nG28 X Y\nT0\nG1 X10 Y10 F3000\n"
LAYER = ";LAYER_CHANGE\n;Z:0.2\nG1 X20 Y20 Z0.2\nG1 X30 Y20 E1\n"


def klipper_chunks(data, size=4096):
    """What Klipper's batch reader does: os.read 4096 bytes, decode each chunk on its own."""
    return [data[i:i + size].decode() for i in range(0, len(data), size)]


class PrepTest(unittest.TestCase):
    def test_no_chunk_splits_a_character(self):
        # A header of any length (a slicer's thumbnail block, in the real report) can put a
        # Chinese character across a 4096-byte read. Klipper drops such chunks silently,
        # taking the injected G28 with them: every later move fails with "Must home".
        for n in range(4096):
            out = prep_gcode.tag_lines(";" + " " * n + "\n" + START + LAYER).encode("utf-8")
            klipper_chunks(out)  # raises UnicodeDecodeError if a chunk is cut mid-character

    def test_homes_before_anything_and_keeps_line_numbers(self):
        out = prep_gcode.tag_lines("G1 X5 Y5 F3000\n" + LAYER).splitlines()
        self.assertEqual(out[0], "G28")
        self.assertIn("G1 X20 Y20 Z0.2 ;L4", out)

    def test_empty_file_does_not_crash(self):
        self.assertEqual(prep_gcode.tag_lines(""), "G28\n\n")


class StartMarginTest(unittest.TestCase):
    # The stock U1 purge line (machine start G-code), the move forum topic 44046 saw refused.
    STOCK = "T0\nG91\nG1 Y-50\nG90\nG1 Z1.5\nG0 X85 Y1 Z2 F18000\nG1 X185 E15 F360\n"

    def test_stock_purge_line_leaves_one_mm_in_y(self):
        m = prep_gcode.start_block_margin((self.STOCK + LAYER).splitlines())
        self.assertEqual((m["line"], m["axis"], m["target"], m["room_mm"], m["side"]), (6, "Y", 1.0, 1.0, "-"))

    def test_relative_moves_and_files_without_layers_are_not_guessed(self):
        self.assertIsNone(prep_gcode.start_block_margin("G91\nG1 Y-50\n;LAYER_CHANGE\n".splitlines()))
        self.assertIsNone(prep_gcode.start_block_margin(self.STOCK.splitlines()))

    def test_summary_names_the_offset_that_is_refused(self):
        import report
        m = prep_gcode.start_block_margin((self.STOCK + LAYER).splitlines())
        r = {"file": "f.gcode", "moves": 1, "tool_changes": 0, "motion_time_s": None, "tools": {},
             "errors": [], "scars": [], "start_margin": m}
        self.assertIn("line 6 (G0 X85 Y1 Z2 F18000) leaves 1.00 mm to the Y limit: a head with a Y offset "
                      "below -1.00 mm is refused there if it starts the print", report.summary(r))


if __name__ == "__main__":
    unittest.main()
