#!/usr/bin/env python3
"""Tell whether the slicer planned a multi-colour print and wrote a single-head file.

Snapmaker Orca 2.4.1 can slice a two-colour plate, exit 0 and write G-code that selects one
head for the whole print: the second colour is printed with the first filament
(https://github.com/Snapmaker/OrcaSlicer/issues/1124). The file still carries the prime tower,
and the slicer only builds a tower when it planned more than one filament: a single-colour
slice with `enable_prime_tower = 1` has none. So "tower in the file, one head selected" means
the tool changes were dropped. This reads the G-code as text, without the firmware.

Usage: python3 dropped_toolchanges.py file.gcode|file.gcode.gz|sliced.3mf
Exit code: 0 fine, 1 tower with a single head, 2 not a sliced file.
"""
import re
import sys

from dock_drops import read_lines

TOOL = re.compile(r"^T(\d+)\s*(;.*)?$")


def find(lines):
    """Return (sorted heads selected, number of prime tower blocks, the 'filament used [g]' line or None)."""
    heads, tower, used = set(), 0, None
    for line in lines:
        line = line.strip()
        m = TOOL.match(line)
        if m:
            heads.add(int(m.group(1)))
        elif line.startswith("; WIPE_TOWER_START"):
            tower += 1
        elif line.startswith("; filament used [g]"):
            used = line[2:]
    return sorted(heads), tower, used


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().split("\n\n")[-1])
        return 2
    try:
        heads, tower, used = find(read_lines(argv[1]))
    except (OSError, ValueError) as e:
        print(f"not a sliced file: {e}")
        return 2
    if not heads:
        print("not a sliced file: no tool selection (T<n>) in it")
        return 2
    names = ", ".join(f"T{h}" for h in heads)
    if used:
        print(used)
    if tower and len(heads) == 1:
        print(f"DROPPED TOOL CHANGES: {tower} prime tower blocks, but only {names} is ever selected.")
        print("The slicer planned more than one filament and wrote a single-head file: every colour")
        print("prints with that head. Known on Snapmaker Orca 2.4.1 (OrcaSlicer#1124, #1130). Do not print it.")
        return 1
    print(f"ok: heads selected {names}; prime tower blocks {tower}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
