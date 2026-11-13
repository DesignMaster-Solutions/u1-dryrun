import contextlib
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import check  # noqa: E402

EX = os.path.join(HERE, "..", "examples")


def run(name):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        rc = check.main(["check", os.path.join(EX, name)])
    return rc, out.getvalue()


class CheckTest(unittest.TestCase):
    def test_clean_file_reports_nothing(self):
        rc, out = run("sign-orca-2.4.0.gcode.gz")
        self.assertEqual(rc, 0, out)
        self.assertIn("== 0 of 9 checks report this file", out)

    def test_each_reported_file_names_its_check(self):
        for name, who in (
            ("brim-by-object-orca-2.4.1.gcode.gz", "brim_wrong_head"),
            ("no-sparse-layers-orca-2.4.1.gcode.gz", "tower_below_print"),
            ("tower-right-edge-orca-2.4.1.3mf", "dock_drops"),
            ("bed-for-late-interface-orca-2.4.1.gcode.gz", "bed_hotter_than_first_layer"),
            ("small-area-flow-orca-2.4.1.gcode.gz", "small_area_flow"),
        ):
            rc, out = run(name)
            self.assertEqual(rc, 1, out)
            self.assertIn(who, out.strip().splitlines()[-1], name)

    def test_one_colour_file_is_clean_not_an_error(self):
        rc, out = run("ring-orcaslicer-2.4.2.gcode.gz")
        self.assertEqual(rc, 0, out)
        self.assertIn("== 0 of 9", out)

    def test_by_object_hop_above_the_print_is_not_a_dock_drop(self):
        # OrcaSlicer 2.5.0-rc lowers the new head to 0.4 mm above the finished object; 2.4.1 to its top
        self.assertEqual(run("brim-by-object-orcaslicer-2.5.0-rc.gcode.gz")[0], 0)
        rc, out = run("brim-by-object-orca-2.4.1.gcode.gz")
        self.assertIn("dock_drops", out.strip().splitlines()[-1])

    def test_missing_file_is_an_error_not_clean(self):
        rc, out = run("no-such-file.gcode")
        self.assertEqual(rc, 2, out)
        self.assertNotIn("checks report", out)
        self.assertEqual(run("arcs.gcode")[0], 2)  # G-code, but not a slice


if __name__ == "__main__":
    unittest.main()
