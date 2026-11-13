import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import small_area_flow as sa  # noqa: E402

MODEL = r'0,0;"\n0.2,0.4444";"\n0.4,0.6145";"\n0.6,0.7059";"\n0.8,0.7619";"\n1.5,0.8571";"\n2,0.8889";"\n3,0.9231";"\n5,0.9520";"\n10,1"'


def gcode(short_factor, on="1", role="Internal solid infill", model=MODEL, far=20):
    """Four 1 mm lines and four 20 mm lines of one role, width and layer; the short ones carry short_factor of the flow."""
    out = ["T0", "M83", ";LAYER_CHANGE", ";HEIGHT:0.2", ";TYPE:" + role, ";WIDTH:0.42", "G1 X0 Y0 F30000"]
    for i in range(4):
        out += ["G1 X%d Y1 E%.5f" % (i, .04 * short_factor), "G1 X%d Y0 F30000" % (i + 1)]
    for i in range(4):
        out += ["G1 X%d Y%d E%.5f" % (i + 5, far, .04 * far), "G1 X%d Y0 F30000" % (i + 6)]
    return out + ["; small_area_infill_flow_compensation = " + on, "; small_area_infill_flow_compensation_model = " + model]


class SmallAreaFlowTest(unittest.TestCase):
    def test_model_is_read_and_interpolated(self):
        m = sa.model(MODEL)
        self.assertEqual(m[0], (0.0, 0.0))
        self.assertAlmostEqual(sa.factor(m, 1.0), 0.7619 + (0.8571 - 0.7619) * 0.2 / 0.7, places=4)
        self.assertEqual(sa.factor(m, 50), 1.0)

    def test_measures_short_against_long_lines(self):
        on, groups = sa.find(gcode(1.0))
        self.assertTrue(on)
        (length, ratio, want, n), = groups
        self.assertAlmostEqual(length, 1.0, places=2)
        self.assertAlmostEqual(ratio, 1.0, places=3)
        self.assertAlmostEqual(want, 0.789, places=2)
        self.assertEqual(n, 4)

    def test_exit_codes(self):
        for lines, want in ((gcode(1.0), 1),                                 # OrcaSlicer#1064: switch on, flow untouched
                            (gcode(0.79), 0),                                # compensated as the model says
                            (gcode(1.0, on="0"), 0),                         # switch off
                            (gcode(1.0, role="Sparse infill"), 0),           # a role the feature never touches
                            (gcode(1.0, model="0,0;10,1")[:11] + gcode(1.0)[-2:], 0),  # too few short lines
                            (gcode(1.0, far=5), 0),                          # no long line to compare with
                            (gcode(1.0, model='0,1;"\n10,1"'), 0),           # a flat model asks for nothing
                            (gcode(1.0)[:-2], 2)):
            with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as f:
                f.write("\n".join(lines))
            try:
                self.assertEqual(sa.main(["x", f.name]), want, lines[-2:])
            finally:
                os.unlink(f.name)
        self.assertEqual(sa.main(["x", "/nonexistent.gcode"]), 2)


if __name__ == "__main__":
    unittest.main()
