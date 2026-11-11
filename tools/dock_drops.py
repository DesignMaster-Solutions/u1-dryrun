#!/usr/bin/env python3
"""Count the tool changes where the new head is lowered to layer height before it moves.

After `T<n>` the U1 leaves the new head at its dock exit. Snapmaker Orca 2.4.1 sometimes writes
`G1 Z<layer>` as the first move after it, so the head comes down at the dock and travels to the
prime tower at the height of the layer in progress, through whatever is in the way
(https://github.com/Snapmaker/OrcaSlicer/issues/1168, docs/orca-2.4.1-dock-travel.md).
This reads the G-code as text, in a second, without the firmware. It tells you whether the file
has such tool changes, not whether the head touches the part: that needs the dry run.

Usage: python3 dock_drops.py file.gcode|file.gcode.gz|sliced.3mf
Exit code: 0 none, 1 at least one, 2 not a sliced file.
"""
import gzip
import re
import sys
import zipfile

TOOL = re.compile(r"^T\d+\s*(;.*)?$")
MOVE = re.compile(r"^G[0-3]\s")
AXIS = re.compile(r"\b([XYZ])-?[\d.]")


def read_lines(path):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            names = sorted(n for n in z.namelist() if re.match(r"Metadata/plate_\d+\.gcode$", n))
            if not names:
                raise ValueError("no sliced plate in this .3mf (slice it and export the plate first)")
            return z.read(names[0]).decode("utf-8", "replace").split("\n")
    with open(path, "rb") as f:
        raw = f.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return raw.decode("utf-8", "replace").split("\n")


def find(lines):
    """Return (tool changes, [(line number of the Z move, text)] for those that lower Z first).

    Tool changes are counted from the first layer change on: the head selected in the start
    G-code is primed by the start macro, not sent to the tower.
    """
    total, drops, waiting, started = 0, [], False, False
    for n, line in enumerate(lines, 1):
        line = line.strip()
        if line.startswith(";LAYER_CHANGE"):
            started = True
        elif started and TOOL.match(line):
            total, waiting = total + 1, True
        elif waiting and MOVE.match(line):
            axes = set(AXIS.findall(line.split(";")[0]))
            if not axes:
                continue  # extruder only
            if axes == {"Z"}:
                drops.append((n, line))
            waiting = False
    return total, drops


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip())
        return 2
    try:
        lines = read_lines(argv[1])
    except (OSError, ValueError) as e:
        print("dock_drops: %s" % e)
        return 2
    total, drops = find(lines)
    if not total:
        print("dock_drops: no tool change after the first layer in this file")
        return 2
    print("%d of %d tool changes lower Z before the first XY move" % (len(drops), total))
    for n, line in drops[:5]:
        print("  line %d: %s" % (n, line))
    if len(drops) > 5:
        print("  ... and %d more, last at line %d" % (len(drops) - 5, drops[-1][0]))
    return 1 if drops else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
