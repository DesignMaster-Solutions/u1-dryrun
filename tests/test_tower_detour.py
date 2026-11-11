import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import tower_detour as td  # noqa: E402

EX = os.path.join(HERE, "..", "examples")
BED = (0.5, 1.0, 270.5, 271.0)
# tower boxes measured in the two projects of forum 43745/21 sliced with Snapmaker Orca 2.4.1
KOI = (22.633, 228.032, 67.809, 273.523)
BUNNY = (229.97, 218.20, 268.86, 257.70)


def near(a, b):
    return len(a) == len(b) and all(abs(p[0] - q[0]) < 0.02 and abs(p[1] - q[1]) < 0.02 for p, q in zip(a, b))


class TowerDetourTest(unittest.TestCase):
    def test_koi_left_entry_walks_round_the_back_corner_outside_the_bed(self):
        entry = (29.721, 236.133)
        d = td.detour((70.809, 236.133), entry, KOI)
        self.assertTrue(near(d, [(69.809, 236.133), (69.809, 275.523), (20.633, 275.523), (20.633, 236.133), entry]), d)
        self.assertEqual([p for p in d if td.outside(p, BED)], d[1:3])

    def test_koi_tower_6_mm_forward_fits(self):
        # the slicer wrote G1 X69.822 Y230.133 / X69.822 Y269.534 / X20.62 Y269.534 for this one
        tower = (KOI[0], KOI[1] - 6, KOI[2], KOI[3] - 6)
        d = td.detour((70.809, 230.133), (29.721, 230.133), tower)
        self.assertTrue(near(d[:3], [(69.822, 230.133), (69.822, 269.534), (20.62, 269.534)]), d)
        self.assertFalse([p for p in d if td.outside(p, BED)])

    def test_bunny_right_entry_fails_by_the_bed_edge_and_left_entry_fits(self):
        d = td.detour((270.5, 237.607), (262.665, 237.607), BUNNY)
        self.assertTrue(near(d, [(270.86, 237.607), (262.665, 237.607)]), d)
        self.assertTrue(td.outside(d[0], BED))
        d = td.detour((270.5, 237.607), (236.165, 237.607), BUNNY)  # file: G1 X227.96 Y237.607
        self.assertTrue(near(d, [(227.96, 237.607), (236.165, 237.607)]), d)
        self.assertFalse([p for p in d if td.outside(p, BED)])

    def test_example_prediction_matches_the_file(self):
        bed, tower, changes = td.read(td.read_lines(os.path.join(EX, "tower-right-edge-orca-2.4.1.3mf")))
        self.assertEqual(bed, BED)
        park = min(tower[2] + td.PARK, bed[2])
        got = [bool([p for p in td.detour((park, e[1]), e, tower) if td.outside(p, bed)]) for _, e, _ in changes]
        self.assertEqual(got, [bool(low) for _, _, low in changes])
        self.assertEqual((len(got), sum(got)), (15, 8))

    def test_exit_codes(self):
        self.assertEqual(td.main(["x", os.path.join(EX, "tower-right-edge-orca-2.4.1.3mf")]), 1)
        self.assertEqual(td.main(["x", os.path.join(EX, "arcs.gcode")]), 2)
        self.assertEqual(td.main(["x", os.path.join(EX, "nope.gcode")]), 2)


if __name__ == "__main__":
    unittest.main()
