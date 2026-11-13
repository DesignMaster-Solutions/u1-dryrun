import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import settings_block_short as sb  # noqa: E402

# what a two-filament Snapmaker Orca 2.4.1 command-line slice looks like, head 2 hotter (OrcaSlicer#1068)
MOVES = ["M104 T0 S140", "M109 S220", "M104 S230 T1 ; preheat T1 time: 40s", "T0",
         "SET_PRESSURE_ADVANCE ADVANCE=0.02; Override pressure advance value", "G1 X1 Y1 E1",
         "M104 S70 T0 ; cooldown", "T1", "M104 S235 T1", "SET_PRESSURE_ADVANCE ADVANCE=0.15", "G1 X2 Y2 E1"]
SHORT = MOVES + ["; filament_type = PLA;PLA", "; hot_plate_temp = 65,35", "; nozzle_temperature = 215",
                 "; pressure_advance = 0.02"]
FULL = MOVES + ["; filament_type = PLA;PLA", "; nozzle_temperature = 215,230", "; pressure_advance = 0.02,0.15"]
ALIKE = ["T0", "M109 S220", "G1 X1 Y1 E1", "T1", "M109 S220 T1", "G1 X2 Y2 E1",
         "; filament_type = PLA;PLA", "; nozzle_temperature = 215"]


class SettingsBlockShortTest(unittest.TestCase):
    def test_short_keys_and_what_the_moves_set(self):
        self.assertEqual(sb.find(SHORT), (2, {"nozzle_temperature": "215", "pressure_advance": "0.02"},
                                          {0: (220.0, 0.02), 1: (235.0, 0.15)}))
        self.assertEqual(sb.find(FULL)[1], {})

    def test_standby_and_cooldown_temperatures_are_not_printing_temperatures(self):
        self.assertEqual(sb.find(["T0", "M104 S140", "M104 S70 T1", "; filament_type = PLA;PLA"])[2], {})

    def test_exit_codes(self):
        for lines, want in ((SHORT, 1), (FULL, 0), (ALIKE, 0), (MOVES, 2)):
            with tempfile.NamedTemporaryFile("w", suffix=".gcode", delete=False) as f:
                f.write("\n".join(lines))
            try:
                self.assertEqual(sb.main(["x", f.name]), want, lines)
            finally:
                os.unlink(f.name)
        self.assertEqual(sb.main(["x", "/nonexistent.gcode"]), 2)


if __name__ == "__main__":
    unittest.main()
