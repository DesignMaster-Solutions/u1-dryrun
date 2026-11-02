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


if __name__ == "__main__":
    unittest.main()
