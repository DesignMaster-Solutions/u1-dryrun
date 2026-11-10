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


class MapTest(unittest.TestCase):
    def test_map_is_sent_to_the_firmware_before_homing(self):
        out = prep_gcode.tag_lines(LAYER, prep_gcode.parse_maps(["T4=T3", "5=1"])).splitlines()
        self.assertEqual(out[:3], ["SET_PRINT_EXTRUDER_MAP CONFIG_EXTRUDER=4 MAP_EXTRUDER=3",
                                   "SET_PRINT_EXTRUDER_MAP CONFIG_EXTRUDER=5 MAP_EXTRUDER=1", "G28"])

    def test_bad_map_is_refused_not_ignored(self):
        for spec in ("T4", "T4=T4", "x=1", "T4=T3,T5=T1"):
            self.assertRaises(ValueError, prep_gcode.parse_maps, [spec])

    def test_filaments_above_t3_without_a_head_are_named(self):
        text = "T1\nT4 ; change\nM104 S220 T6\nT5\n" + LAYER
        self.assertEqual(prep_gcode.unmapped_filaments(text), [4, 5])
        self.assertEqual(prep_gcode.unmapped_filaments(text, [(4, 3)]), [5])
        import report
        r = {"file": "f", "moves": 1, "tool_changes": 0, "motion_time_s": None, "tools": {}, "errors": [],
             "scars": [], "unmapped_filaments": [4, 5]}
        self.assertIn("head not known for T4, T5: this run printed them on head 0", report.summary(r))


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


class SkipTest(unittest.TestCase):
    FILE = "EXCLUDE_OBJECT_DEFINE NAME=part_1.stl_id_0 CENTER=1,1\n" + LAYER + "G1 X1 Y1\nG1 X2 Y2\n"

    def test_skip_goes_before_its_line_and_line_tags_stay(self):
        n = len(self.FILE.splitlines())
        skips = prep_gcode.parse_skips(["part_1.stl_id_0@%d" % n], self.FILE)
        out = prep_gcode.tag_lines(self.FILE, skips=skips).splitlines()
        i = out.index("EXCLUDE_OBJECT NAME=part_1.stl_id_0")
        self.assertEqual((out[i - 1], out[i + 1]), ("DRYRUN_LINE N=%d" % n, "G1 X2 Y2 ;L%d" % n))

    def test_unknown_object_or_line_is_refused_with_the_names_the_file_has(self):
        with self.assertRaisesRegex(ValueError, "it has: part_1.stl_id_0"):
            prep_gcode.parse_skips(["B@2"], self.FILE)
        for bad in ("part_1.stl_id_0", "part_1.stl_id_0@0", "part_1.stl_id_0@999", "@3"):
            with self.assertRaises(ValueError):
                prep_gcode.parse_skips([bad], self.FILE)


if __name__ == "__main__":
    unittest.main()
