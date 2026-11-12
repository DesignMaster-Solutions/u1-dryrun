import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import dock_drops as dd  # noqa: E402

EX = os.path.join(HERE, "..", "examples")


class DockDropsTest(unittest.TestCase):
    def test_counts_only_tool_changes_that_lower_z_first(self):
        lines = [
            "T0", "G1 Z.25 F30000",          # start G-code, before the first layer: not counted
            ";LAYER_CHANGE",
            "T1", "G1 E-2 F3600", "G1 Z.45 F30000", "G1  X259 Y121 F30000",   # lowered at the dock
            "T0 ; back", "G1 X15.25 Y220.25 F30000", "G1 Z.45",               # XY first: fine
            "T1", "G1 X10 Z.65",                                              # moves while it lowers: fine
        ]
        total, drops = dd.find(lines)
        self.assertEqual(total, 3)
        self.assertEqual(drops, [(6, "G1 Z.45 F30000")])

    def test_examples(self):
        # the numbers of docs/orca-2.4.1-dock-travel.md, "Small reproduction"
        for name, want in (("tower-right-edge-orca-2.4.1.3mf", (15, 8, 4525)),
                           ("tower-right-edge-orca-2.4.1-wall-gap-off.gcode.gz", (15, 15, 2106)),
                           ("sign-orca-2.4.0.gcode.gz", (15, 0, None))):
            total, drops = dd.find(dd.read_lines(os.path.join(EX, name)))
            self.assertEqual((total, len(drops), drops[0][0] if drops else None), want, name)

    def test_primes_at_the_dock(self):
        # the un-retract that follows the Z drop is pushed out before the head leaves the dock
        lines = [";LAYER_CHANGE",
                 "T1", "G1 Z.45 F30000", "G1 E10 F1800", "G1  X259 Y121 F30000",
                 "T0", "G1 Z.65 F30000", "G1 X20 Y225", "G1 E10 F1800"]      # at the tower: fine
        total, drops = dd.find(lines)
        self.assertEqual(dd.primes(lines, drops), [(4, 10.0)])
        for name, want, mms in (("tower-right-edge-orca-2.4.1.3mf", 8, {10.0}),
                                ("tower-right-edge-orca-2.4.1-wall-gap-off.gcode.gz", 15, {2.0, 10.0})):
            lines = dd.read_lines(os.path.join(EX, name))
            got = dd.primes(lines, dd.find(lines)[1])
            self.assertEqual((len(got), {mm for _, mm in got}), (want, mms), name)

    def test_exit_codes(self):
        self.assertEqual(dd.main(["x", os.path.join(EX, "tower-right-edge-orca-2.4.1.3mf")]), 1)
        self.assertEqual(dd.main(["x", os.path.join(EX, "sign-orca-2.4.0.gcode.gz")]), 0)
        self.assertEqual(dd.main(["x", os.path.join(EX, "arcs.gcode")]), 2)
        self.assertEqual(dd.main(["x", os.path.join(EX, "nope.gcode")]), 2)


if __name__ == "__main__":
    unittest.main()
