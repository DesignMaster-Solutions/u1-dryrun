#!/usr/bin/env python3
"""Make the prime tower an object the U1 can skip, in a Snapmaker Orca / OrcaSlicer G-code.

The slicer labels the models (EXCLUDE_OBJECT_DEFINE) but not the prime tower, so when the tower
comes off the bed mid-print there is nothing to skip on the screen and the print is lost
(https://forum.snapmaker.com/t/44109). This labels the tower as the object `prime_tower`: every
tower block is wrapped in EXCLUDE_OBJECT_START/END and nothing else changes. Until you skip it the
print is the same. After you skip it the tool changes still happen, without priming on the tower.

Usage: python3 skippable_tower.py file.gcode
Edits the file in place, so it also works as an Orca post-processing script.
"""
import re
import sys

NAME = "prime_tower"
MARK = "; skippable_tower: the prime tower is the object %s" % NAME
XY = re.compile(r"\b([XY])(-?[\d.]+)")
MOVE = re.compile(r"^G[0-3]\b")


def process(text):
    """Return (new text, number of tower blocks labelled)."""
    if MARK in text:
        return text, 0
    lines = text.split("\n")
    out, xs, ys, n, i = [], [], [], 0, 0
    while i < len(lines):
        if lines[i].strip() != "; WIPE_TOWER_START":
            out.append(lines[i])
            i += 1
            continue
        end = next((k for k in range(i + 1, len(lines)) if lines[k].strip() == "; WIPE_TOWER_END"), None)
        if end is None:
            out.extend(lines[i:])
            break
        block = lines[i:end]
        # A tool-change block opens with the wipe on the model and ends that object inside the
        # block: the tower starts after it (Klipper has one current object, no nesting).
        closes = [k for k, line in enumerate(block) if line.startswith("EXCLUDE_OBJECT_END")]
        cut = closes[-1] + 1 if closes else 1
        for line in block[cut:]:
            if MOVE.match(line):
                for axis, value in XY.findall(line.split(";")[0]):
                    (xs if axis == "X" else ys).append(float(value))
        out += block[:cut] + ["EXCLUDE_OBJECT_START NAME=" + NAME] + block[cut:] + ["EXCLUDE_OBJECT_END NAME=" + NAME]
        n += 1
        i = end
    if not n or not xs or not ys:
        return text, 0
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    define = "EXCLUDE_OBJECT_DEFINE NAME=%s CENTER=%g,%g POLYGON=[[%g,%g],[%g,%g],[%g,%g],[%g,%g],[%g,%g]]" % (
        NAME, (x0 + x1) / 2, (y0 + y1) / 2, x0, y0, x1, y0, x1, y1, x0, y1, x0, y0)
    defines = [k for k, line in enumerate(out) if line.startswith("EXCLUDE_OBJECT_DEFINE")]
    at = defines[-1] + 1 if defines else out.index("EXCLUDE_OBJECT_START NAME=" + NAME)
    out[at:at] = [MARK, define]
    return "\n".join(out), n


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    # surrogateescape and newline="" keep every other byte of the slicer's file as it was
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as f:
        text = f.read()
    new, n = process(text)
    if n:
        with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
            f.write(new)
    print("%s: %s" % (path, "prime tower labelled as %s in %d blocks" % (NAME, n) if n else "nothing to change"))


if __name__ == "__main__":
    main()
