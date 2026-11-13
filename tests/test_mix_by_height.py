import os
import sys
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import mix_by_height as mh  # noqa: E402


def layer(z, head, e):
    return ["; CHANGE_LAYER", f"T{head}", f"G1 Z{z} F600", f"G1 X10 Y10 E{e}", "G1 E-.8 F1800"]


class MixByHeightTest(unittest.TestCase):
    def test_plain_alternation_has_the_same_share_in_every_band(self):
        lines = [x for i in range(20) for x in layer(round(0.2 * (i + 1), 2), i % 2, 1)]
        rows, n = mh.shares(lines, 2)
        self.assertEqual(n, 20)
        self.assertEqual([r[2] for r in rows], [{0: 50.0, 1: 50.0}, {0: 50.0, 1: 50.0}])

    def test_fade_moves_the_share_and_start_gcode_is_ignored(self):
        lines = ["T1", "G1 X5 Y5 E99"]  # purge line before the first layer
        for i in range(10):
            z = round(0.2 * (i + 1), 2)
            a = 0.8 if i < 5 else 0.2
            lines += layer(z, 0, a) + [f"T1", f"G1 X20 Y10 E{round(1 - a, 2)}"]
        rows, _ = mh.shares(lines, 2)
        self.assertAlmostEqual(rows[0][2][0], 80.0)
        self.assertAlmostEqual(rows[1][2][0], 20.0)


if __name__ == "__main__":
    unittest.main()
