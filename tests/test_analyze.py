import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dryrun"))
import analyze  # noqa: E402
import report  # noqa: E402


def trace(rows):
    """rows: (x, y, z, e), written as tracer lines; returns path."""
    f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
    for i, (x, y, z, e) in enumerate(rows):
        f.write("M %f %f %f %f 100 %d extruder %f\n" % (x, y, z, e, i, i * 0.1))
    f.close()
    return f.name


class DragTest(unittest.TestCase):
    GCODE = "G1 X45 Y300\nG1 E20 F360 ; prime\nG1 Z2 E1\nG1 X50 E1\n"

    def test_e_only_lines_are_the_ones_without_x_or_y(self):
        self.assertEqual(analyze.e_only_lines_from_gcode(self.GCODE), {2, 3})

    def test_head_moved_on_an_e_only_line_is_a_drag_and_a_still_prime_is_not(self):
        # tracer rows are numbered from 0: row 2 is the prime of file line 2
        still = analyze.analyze(trace([(0, 0, 2, 0), (45, 300, 2, 0), (45, 300, 2, 20)]), e_only_lines={2})
        self.assertEqual(still["drags"], [])
        # a travel issued by a macro right after the retract of line 2 (sign-orca-2.4.0, end G-code)
        macro = analyze.analyze(trace([(0, 0, 2, 0), (45, 300, 2, 0), (5, 5, 2, 0)]), e_only_lines={2})
        self.assertEqual(macro["drags"], [])
        moved = analyze.analyze(trace([(0, 0, 2, 0), (92.7, 300.5, 2, 0), (82.7, 230.5, 2, 20)]), e_only_lines={2})
        self.assertEqual([(d["line"], d["from"], d["to"], d["length_mm"], d["extruded_mm"]) for d in moved["drags"]],
                         [(2, [92.7, 300.5], [82.7, 230.5], 70.7, 20.0)])


class FilamentTest(unittest.TestCase):
    def test_each_head_counts_its_own_net_filament(self):
        # Each head keeps its own E position, so the first move after a tool change is not a push
        # of the difference between the two (a real 4 h file reported 1116 m for 23 m), and a
        # retract followed by its restore is no filament used.
        f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
        for i, (tool, e) in enumerate([("extruder", 0), ("extruder", 100), ("extruder1", 5), ("extruder1", 15),
                                       ("extruder", 100), ("extruder", 99), ("extruder", 100), ("extruder", 110)]):
            f.write("M %d 10 0.2 %f 100 %d %s %f G\n" % (i, e, i, tool, i * 0.1))
        f.close()
        tools, changes = analyze.tool_stats(analyze.parse_trace(f.name))
        self.assertEqual({t: s["extruded_mm"] for t, s in tools.items()}, {"extruder": 110.0, "extruder1": 10.0})
        self.assertEqual(changes, 2)


class ScarTest(unittest.TestCase):
    def square_top(self, z):
        """Top layer: a 20 mm line printed back and forth, fully covering y=10."""
        return [(10, 10, z, 0), (30, 10, z, 1), (10, 10, z, 2)]

    def test_travel_across_finished_top_is_a_scar(self):
        rows = self.square_top(5.0) + [(40, 10, 5.0, 2)]  # no lift: the 2.4.1 pattern
        scars = analyze.analyze(trace(rows))["scars"]
        self.assertEqual(len(scars), 1)
        self.assertLessEqual(scars[0]["clearance_mm"], 0.0)
        self.assertGreater(scars[0]["length_mm"], 10)

    def test_lift_before_travel_is_clean(self):
        rows = self.square_top(5.0) + [(10, 10, 5.4, 2), (40, 10, 5.4, 2)]  # the 2.4.0 pattern
        self.assertEqual(analyze.analyze(trace(rows))["scars"], [])

    def test_travel_over_material_covered_later_is_not_a_scar(self):
        rows = [(10, 10, 5.0, 0), (30, 10, 5.0, 1), (10, 10, 5.0, 1),  # layer 1
                (30, 10, 5.0, 1),  # travel at layer height over it
                (30, 10, 5.2, 1), (10, 10, 5.2, 2)]  # layer 2 buries the mark
        self.assertEqual(analyze.analyze(trace(rows))["scars"], [])

    def test_print_stopped_by_the_firmware_does_not_scar_its_last_two_layers(self):
        # Real file from u1-klipper#22 with two objects skipped: the firmware stops the print at
        # line 319758 and the 4 "scars" were same-layer travels the next layer would have buried.
        rows = [(10, 30, 4.6, 0), (30, 30, 4.6, 1), (10, 30, 4.6, 1),  # a top surface, two layers down
                (10, 10, 5.0, 1), (30, 10, 5.0, 2), (10, 10, 5.0, 2),  # travel over the layer below the last
                (10, 50, 5.2, 2), (30, 50, 5.2, 3)]  # the layer in progress when the print stops
        path = trace(rows)
        self.assertEqual(len(analyze.analyze(path)["scars"]), 2)  # ran to the end: both are final
        with open(path, "a") as f:
            f.write("ERR 7 Move out of range\n")
        self.assertEqual([s["z"] for s in analyze.analyze(path)["scars"]], [4.6])

    def test_counts_tool_changes(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
        for i, tool in enumerate(["extruder", "extruder", "extruder1", "extruder"]):
            f.write("M %d 0 1 0 100 %d %s %f\n" % (i, i, tool, i * 1.0))
        f.close()
        result = analyze.analyze(f.name)
        self.assertEqual(result["tool_changes"], 2)
        self.assertEqual(set(result["tools"]), {"extruder", "extruder1"})


class RampTest(unittest.TestCase):
    def test_travel_that_ramps_up_as_it_leaves_is_not_a_scar(self):
        # Orca lifts while moving: Z only starts at the surface, it clears it within a millimetre
        rows = [(10, 10, 5.0, 0), (30, 10, 5.0, 1), (10, 10, 5.0, 2), (17.6, 10, 5.4, 2)]
        self.assertEqual(analyze.analyze(trace(rows))["scars"], [])


class PrimeTowerTest(unittest.TestCase):
    def test_travel_across_the_prime_tower_is_not_a_scar(self):
        # the tower is waste: line 1-2 are tower extrusion, line 3 crosses it without lifting
        rows = [(10, 10, 5.0, 0), (30, 10, 5.0, 1), (10, 10, 5.0, 2), (40, 10, 5.0, 2)]
        result = analyze.analyze(trace(rows), line_types={1: "Prime tower", 2: "Prime tower"})
        self.assertEqual(result["scars"], [])


class SupportTest(unittest.TestCase):
    ROWS = [(10, 10, 0.25, 0), (30, 10, 0.25, 1), (10, 10, 0.25, 2), (40, 10, 0.25, 2)]

    def test_travel_across_support_is_not_a_scar(self):
        # real file, u1-klipper#22: three unlifted first-layer travels over support, which is thrown away
        for kind in ("Support", "Support interface", "Support transition"):
            result = analyze.analyze(trace(self.ROWS), line_types={1: kind, 2: kind})
            self.assertEqual(result["scars"], [], kind)

    def test_travel_inside_a_support_section_still_scars_the_part(self):
        # the travel is tagged Support, the material under it is the part: still a scar
        result = analyze.analyze(trace(self.ROWS), line_types={1: "Outer wall", 2: "Outer wall", 3: "Support"})
        self.assertEqual(len(result["scars"]), 1)


class DockCrossingTest(unittest.TestCase):
    """Orca 2.4.1, forum 43745: the new head drops to layer height at its dock and crosses the part to the tower."""

    def rows(self, travel_z):
        # head 0 prints a 20 mm line at Z0.45; head 1 leaves the dock, crosses it and primes on the tower
        return [(10, 100, 0.45, 0, "extruder"), (30, 100, 0.45, 1, "extruder"),
                (0, 100, 5.0, 0, "extruder1"), (0, 100, travel_z, 0, "extruder1"),  # lifted to the dock, Z drop there
                (60, 100, travel_z, 0, "extruder1"),
                (60, 100, 0.45, 0, "extruder1"), (70, 100, 0.45, 1, "extruder1"),
                (10, 100, 0.65, 1, "extruder1"), (30, 100, 0.65, 2, "extruder1")]  # next layer covers it: no scar

    def run_rows(self, rows, types):
        f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
        for i, (x, y, z, e, tool) in enumerate(rows):
            f.write("M %f %f %f %f 100 %d %s %f\n" % (x, y, z, e, i, tool, i * 0.1))
        f.close()
        return dict(analyze.analyze(f.name, line_types=types), file="x", klippy_rc=0)

    def test_new_head_crossing_the_part_at_layer_height_on_its_way_to_the_tower(self):
        result = self.run_rows(self.rows(0.45), {6: "Prime tower"})
        self.assertEqual(result["scars"], [])
        self.assertEqual([c["line"] for c in result["crossings"]], [4])
        self.assertAlmostEqual(result["crossings"][0]["length_mm"], 20.0, delta=0.5)
        self.assertIn("CROSSING line 4", report.summary(result))
        self.assertNotIn("clean", report.summary(result))

    def test_lifted_travel_to_the_tower_is_clean(self):
        result = self.run_rows(self.rows(0.85), {6: "Prime tower"})
        self.assertEqual(result["crossings"], [])
        self.assertIn("clean", report.summary(result))

    def test_without_a_tower_the_first_travel_of_a_new_head_is_not_reported(self):
        # no prime tower: travelling to the part at layer height is what every slicer does
        self.assertEqual(self.run_rows(self.rows(0.45), {})["crossings"], [])


class LargeFileTest(unittest.TestCase):
    def test_memory_does_not_grow_with_the_number_of_moves(self):
        # a 22 h farm plate is 8 million moves; held in memory they need more than the 8 GB Docker gives
        import tracemalloc
        path = trace((i % 200, i % 190, 0.2 + i // 20000 * 0.2, i * 0.01) for i in range(100000))
        tracemalloc.start()
        result = analyze.analyze(path)
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        self.assertEqual(result["moves"], 99999)
        self.assertLess(peak, 20e6)


class TimeoutTest(unittest.TestCase):
    def test_a_run_cut_by_the_timeout_is_not_reported_clean(self):
        import report
        r = analyze.analyze(trace([(0, 0, 0.2, 0), (10, 0, 0.2, 1)]))
        r.update(file="big.gcode", klippy_rc=-1, timeout_s=900)
        text = report.summary(r)
        self.assertIn("NOT FINISHED", text)
        self.assertNotIn("clean", text)
        self.assertIn("NOT FINISHED", report.render(r))

    def test_timeout_grows_with_the_file(self):
        import run
        self.assertEqual(run.timeout_s(34368), 900)
        self.assertGreater(run.timeout_s(8830000), 3600)


class PrepGcodeTest(unittest.TestCase):
    def test_start_block_is_blanked_but_line_numbers_survive(self):
        import prep_gcode
        text = "M83\nT2\nFINELY_CLEAN_NOZZLE_STAGE_1\nG1 X5\n;LAYER_CHANGE\nG1 X1 Y1\n"
        out = prep_gcode.tag_lines(text).splitlines()
        self.assertIn("M83", out)
        self.assertNotIn("FINELY_CLEAN_NOZZLE_STAGE_1", out)
        self.assertNotIn("G1 X5 ;L4", out)
        self.assertIn("T2", out)  # last tool chosen before layer 1 is kept
        self.assertEqual(out[-1], "G1 X1 Y1 ;L6")


if __name__ == "__main__":
    unittest.main()
