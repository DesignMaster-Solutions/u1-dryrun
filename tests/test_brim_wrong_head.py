import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import brim_wrong_head as bw  # noqa: E402


def brim(x):
    return [";TYPE:Brim", f"G1 X{x} Y120 F6000", f"G1 X{x + 25} Y120 E.5"]


def part(name, head, x):
    return [f"T{head}", f"; printing object {name} id:0 copy 0", ";TYPE:Outer wall", f"G1 X{x + 5} Y125 F6000",
            f"G1 X{x + 20} Y125 E.5", f"G1 X{x + 20} Y140 E.5", f"; stop printing object {name} id:0 copy 0"]


# the shape of three 15 mm blocks, one filament each, "by object" with an outer brim (macOS command line):
# Snapmaker Orca 2.4.1 prints the three brims first with T0; OrcaSlicer 2.5.0-rc prints each before its object
ALL_FIRST = ["T0"] + brim(15) + brim(123) + brim(231) + part("a", 0, 15) + part("b", 1, 123) + part("c", 2, 231)
OWN_HEAD = ["T0"] + brim(15) + part("a", 0, 15) + ["T1"] + brim(123) + part("b", 1, 123) + ["T2"] + brim(231) + \
    part("c", 2, 231)


class BrimWrongHeadTest(unittest.TestCase):
    def test_brims_printed_first_by_one_head_are_reported_per_object(self):
        self.assertEqual(bw.find(ALL_FIRST), (3, [("b", 1, 0, 7, 1), ("c", 2, 0, 10, 2)]))
        self.assertEqual(bw.find(OWN_HEAD), (3, []))

    def test_relative_moves_do_not_move_the_brim(self):
        # the Z hop block is G91: read as absolute, X200 would put this brim next to b
        lines = ["T0", ";TYPE:Brim", "G1 X15 Y120", "G91", "G1 X200 Z1", "G90", "G1 X40 Y120 E.5"] + \
            part("a", 0, 15) + part("b", 1, 123)
        self.assertEqual(bw.find(lines), (1, []))

    def test_real_slices(self):
        ex = os.path.join(HERE, "..", "examples")
        seen, wrong = bw.find(bw.read_lines(os.path.join(ex, "brim-by-object-orca-2.4.1.gcode.gz")))
        self.assertEqual([r[:3] + r[4:] for r in wrong], [("b.stl", 1, 0, 1), ("c.stl", 2, 0, 2)])
        self.assertEqual(bw.find(bw.read_lines(os.path.join(ex, "brim-by-object-orcaslicer-2.5.0-rc.gcode.gz")))[1], [])

    def test_exit_codes(self):
        for lines, want in ((ALL_FIRST, 1), (OWN_HEAD, 0), (part("a", 0, 15), 0)):
            with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as f:
                f.write("\n".join(lines))
            try:
                self.assertEqual(bw.main(["x", f.name]), want, lines)
            finally:
                os.unlink(f.name)
        self.assertEqual(bw.main(["x", "/nonexistent.gcode"]), 2)


if __name__ == "__main__":
    unittest.main()
