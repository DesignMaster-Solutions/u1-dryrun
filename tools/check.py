#!/usr/bin/env python3
"""Every text check in one go, no Docker: python3 tools/check.py file.gcode (.gcode.gz, sliced .3mf)

Runs dock_drops, tower_below_print, brim_wrong_head, dropped_toolchanges, z_offset_lost, settings_block_short and
bed_hotter_than_first_layer on the same file and
prints what each one says. Exit 0 when none reports, 1 when any does, 2 when a file cannot be read.
These read the file as text; the firmware run (README, "Run it") is still what shows a scar.
"""
import sys

import bed_hotter_than_first_layer
import brim_wrong_head
import dock_drops
import dropped_toolchanges
import settings_block_short
import tower_below_print
import z_offset_lost

CHECKS = (dock_drops, tower_below_print, brim_wrong_head, dropped_toolchanges, z_offset_lost, settings_block_short,
          bed_hotter_than_first_layer)


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[0], file=sys.stderr)
        return 2
    try:
        lines = dock_drops.read_lines(argv[1])
    except (OSError, ValueError) as e:
        print(f"check: {e}")
        return 2
    if not any(dock_drops.TOOL.match(line.strip()) for line in lines):
        print("check: not a sliced file, no tool selection (T<n>) in it")
        return 2
    reported = []
    for check in CHECKS:
        name = check.__name__
        print(f"== {name}")
        if check.main([name, argv[1]]) == 1:  # 2 here = this check has nothing to look at (one colour)
            reported.append(name)
    print(f"== {len(reported)} of {len(CHECKS)} checks report this file" + (": " + ", ".join(reported) if reported else ""))
    return 1 if reported else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
