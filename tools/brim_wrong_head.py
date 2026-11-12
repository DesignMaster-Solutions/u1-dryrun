#!/usr/bin/env python3
"""Tell whether an object's brim is printed by another head than the object itself.

Snapmaker Orca 2.4.1 prints every brim on the plate in one block with the first head, before any
object. With one filament per object the brim comes out in the wrong colour, and with "Print sequence:
by object" the brims of the later objects have cooled for the whole time the earlier objects took
(https://forum.snapmaker.com/t/44193, confirmed by Snapmaker staff). This reads the G-code as text,
without the firmware: every brim extrusion is given to the nearest object on the plate, and its head
is compared with the head that starts that object.

Usage: python3 brim_wrong_head.py file.gcode|file.gcode.gz|sliced.3mf
Exit code: 0 fine, 1 a brim printed by another head, 2 not a sliced file.
"""
import re
import sys

from dock_drops import read_lines

MOVE = re.compile(r"^G[01]\s")
WORD = re.compile(r"([XYE])(-?\d*\.?\d+)")
TOOL = re.compile(r"^T(\d+)\s*(;.*)?$")
OBJECT = re.compile(r"^; printing object (.+?) id:\d+ copy \d+")


def find(lines):
    """Return (brim extrusions seen, [(object, its head, brim head, first brim line, objects finished in between)])."""
    x = y = 0.0
    tool, feature, obj, relative = 0, "", None, False
    brims, objs = [], {}  # objs: name -> [first line, head, last line, x0, y0, x1, y1]
    for n, line in enumerate(lines, 1):
        line = line.strip()
        if line.startswith(";TYPE:"):
            feature = line[6:]
        elif line.startswith("; printing object"):
            m = OBJECT.match(line)
            obj = m.group(1) if m else None
        elif line.startswith("; stop printing object"):
            obj = None
        elif line.startswith("G90"):
            relative = False
        elif line.startswith("G91"):
            relative = True
        elif TOOL.match(line):
            tool = int(TOOL.match(line).group(1))
        elif MOVE.match(line) and not relative:
            w = {k: float(v) for k, v in WORD.findall(line.split(";")[0])}
            x, y = w.get("X", x), w.get("Y", y)
            if w.get("E", 0) > 0 and ("X" in w or "Y" in w):
                if feature == "Brim":
                    brims.append((n, tool, x, y))
                elif obj:
                    o = objs.setdefault(obj, [n, tool, n, x, y, x, y])
                    o[2:] = [n, min(o[3], x), min(o[4], y), max(o[5], x), max(o[6], y)]
    wrong = {}
    for n, head, bx, by in brims if objs else ():
        # nearest object by distance to its bounding box: a brim hugs its own object
        name = min(objs, key=lambda k: max(objs[k][3] - bx, 0, bx - objs[k][5]) ** 2
                   + max(objs[k][4] - by, 0, by - objs[k][6]) ** 2)
        if head != objs[name][1] and name not in wrong:
            between = sum(1 for o in objs.values() if n < o[0] and o[2] < objs[name][0])
            wrong[name] = (name, objs[name][1], head, n, between)
    return len(brims), sorted(wrong.values(), key=lambda r: r[3:] + r[:1])


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().split("\n\n")[-1])
        return 2
    try:
        seen, wrong = find(read_lines(argv[1]))
    except (OSError, ValueError) as e:
        print(f"not a sliced file: {e}")
        return 2
    if not seen:
        print("ok: no brim in this file")
        return 0
    if wrong:
        print(f"BRIM ON ANOTHER HEAD: {len(wrong)} object(s)")
        for name, head, brim_head, n, between in wrong:
            late = f"; {between} other object(s) are printed in full before this one starts" if between else ""
            print(f"  {name}: printed by T{head}, its brim by T{brim_head} (line {n}){late}")
        print("Seen on Snapmaker Orca 2.4.1 (forum topic 44193, confirmed by staff; OrcaSlicer 2.5.0-rc prints")
        print("each brim with the object's own head). An object whose first layer uses several heads is")
        print("compared with the head that starts it.")
        return 1
    print(f"ok: {seen} brim extrusions, each printed by the head of its own object")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
