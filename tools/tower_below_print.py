#!/usr/bin/env python3
"""Tell whether the prime tower is printed far below the top of the part.

With "No sparse layers" (wipe_tower_no_sparse_layers, marked beta in Snapmaker Orca 2.4.1) the tower
only grows on layers that have a tool change. When the next tool change comes many layers later, the
slicer sends the head down to the tower's own height (`G1 Z.2` in the sample here) while the part
already stands tens of millimetres tall on the same bed. A U1 owner reported the head ending up next
to the print at bed height and a crash (https://forum.snapmaker.com/t/44225). This reads the G-code
as text, without the firmware: it compares the Z of every prime tower extrusion with the highest Z
the part has been printed at so far.

Usage: python3 tower_below_print.py file.gcode|file.gcode.gz|sliced.3mf [max drop in mm, default 1]
Exit code: 0 fine, 1 tower printed below the part, 2 not a sliced file.
"""
import re
import sys

from dock_drops import read_lines

MOVE = re.compile(r"^G[01]\s")
WORD = re.compile(r"([XYZE])(-?\d*\.?\d+)")


def find(lines, max_drop=1.0):
    """Return (tower extrusions seen, [(line number, tower Z, part top Z)] where the tower is below the part)."""
    z, top, relative, feature, seen, drops = 0.0, 0.0, False, "", 0, []
    for n, line in enumerate(lines, 1):
        line = line.strip()
        if line.startswith(";TYPE:"):
            feature = line[6:]
        elif line.startswith("G90"):
            relative = False
        elif line.startswith("G91"):
            relative = True
        elif MOVE.match(line):
            w = {k: float(v) for k, v in WORD.findall(line.split(";")[0])}
            if "Z" in w:
                z = z + w["Z"] if relative else w["Z"]
            if w.get("E", 0) > 0 and ("X" in w or "Y" in w) and feature:
                if feature != "Prime tower":
                    top = max(top, z)
                else:
                    seen += 1
                    # one entry per descent: skip while still at the Z already reported
                    if top - z > max_drop and (not drops or drops[-1][1:] != (z, top)):
                        drops.append((n, z, top))
    return seen, drops


def main(argv):
    if len(argv) not in (2, 3):
        print(__doc__.strip().split("\n\n")[-1])
        return 2
    try:
        seen, drops = find(read_lines(argv[1]), float(argv[2]) if len(argv) == 3 else 1.0)
    except (OSError, ValueError) as e:
        print(f"not a sliced file: {e}")
        return 2
    if not seen:
        print("ok: no prime tower in this file")
        return 0
    if drops:
        n, z, top = max(drops, key=lambda d: d[2] - d[1])
        print(f"TOWER BELOW PRINT: {len(drops)} time(s); worst at line {n}: the tower is printed at Z{z:g} "
              f"while the part is already printed up to Z{top:g} ({top - z:.2f} mm lower).")
        print("The head goes down beside a part that tall. Seen with \"No sparse layers\" on Snapmaker Orca")
        print("2.4.1 (forum topic 44225, a crash on a real U1). Slice with the regular prime tower instead.")
        return 1
    print(f"ok: {seen} prime tower extrusions, none more than the limit below the part")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
