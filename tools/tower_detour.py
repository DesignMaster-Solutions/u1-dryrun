#!/usr/bin/env python3
"""Say why Snapmaker Orca 2.4.1 dropped the "return to wipe tower" detour in a sliced file.

Port of WipeTowerIntegration::detour_around_wipe_tower() and of the bed check after it
(Snapmaker/OrcaSlicer v2.4.1, src/libslic3r/GCode.cpp, append_tcr). When one detour point is
outside printable_area the slicer writes no detour and lowers the new head where the firmware
left it, at the dock (https://github.com/Snapmaker/OrcaSlicer/issues/1168). For every tool
change this recomputes the detour from the tower in the file and prints the point that failed,
and compares the prediction with what the file does (tools/dock_drops.py rule).

Usage: python3 tower_detour.py file.gcode|file.gcode.gz|sliced.3mf
Exit code: 0 every detour fits the bed, 1 at least one does not, 2 not a usable file.
"""
import re
import sys
from collections import Counter

from dock_drops import AXIS, MOVE, TOOL, read_lines

NUM = r"(-?[\d.]+)"
MARGIN = 2.0  # avoid_bbx.offset(scaled(2.0))
PARK = 3.0  # get_wipe_avoid_pos_x(wt_min, wt_max, 3.0f, ...)


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def seg_isect(a1, b1, a2, b2):
    v1, v2 = (b1[0] - a1[0], b1[1] - a1[1]), (b2[0] - a2[0], b2[1] - a2[1])
    den = cross(v1, v2)
    if abs(den) < 1e-9:
        return None
    d = (a1[0] - a2[0], a1[1] - a2[1])
    t1, t2 = cross(v2, d) / den, cross(v1, d) / den
    if 0 <= t1 <= 1 and 0 <= t2 <= 1:
        return (a1[0] + t1 * v1[0], a1[1] + t1 * v1[1])
    return None


def detour(start, target, tower):
    """Points the slicer would travel through, the last one being the tower entry."""
    x0, y0, x1, y1 = tower[0] - MARGIN, tower[1] - MARGIN, tower[2] + MARGIN, tower[3] + MARGIN
    if start == target:
        return [target]
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    v = -1.0 if target[0] < (x0 + x1) / 2 else 1.0
    idx1 = pt1 = None
    for i in range(4):  # horizontal ray from the entry to the box
        a, b = pts[i], pts[(i + 1) % 4]
        sd = (b[0] - a[0], b[1] - a[1])
        den = cross((v, 0.0), sd)
        if abs(den) < 1e-9:
            continue
        d = (target[0] - a[0], target[1] - a[1])
        t, u = cross(sd, d) / den, cross((v, 0.0), d) / den
        if t >= 0 and 0 <= u <= 1:
            idx1, pt1 = i, (target[0] + t * v, target[1])
            break
    if idx1 is None:
        return [target]
    idx2 = pt2 = None
    for i in range(4):
        if i == idx1:
            continue
        hit = seg_isect(start, pt1, pts[i], pts[(i + 1) % 4])
        if hit:
            idx2, pt2 = i, hit
            break
    if idx2 is None:
        return [pt1, target]

    def walk(step):  # as written upstream: the backward walk pushes pts[i], not pts[i + 1]
        p, i = [pt2], idx2
        while i != idx1:
            i = (i + step) % 4
            p.append(pts[i])
        return p + [pt1]

    def length(p):
        return sum(((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5 for a, b in zip(p, p[1:]))

    fwd, back = walk(1), walk(-1)
    return (fwd if length(fwd) <= length(back) else back) + [target]


def outside(p, bed):
    return not (bed[0] <= p[0] <= bed[2] and bed[1] <= p[1] <= bed[3])


def read(lines):
    """Return (bed, tower, [(line, entry point, lowered at the dock)])."""
    bed = tower = None
    xs, ys, changes = [], [], []
    in_tower = started = False
    x = y = None
    waiting = None  # [line of T, first move is Z only, entry]
    for n, line in enumerate(lines, 1):
        raw, line = line, line.strip()
        if line.startswith("; printable_area ="):
            c = [float(v) for v in re.findall(NUM, line.split("=")[1])]
            bed = (min(c[0::2]), min(c[1::2]), max(c[0::2]), max(c[1::2]))
        elif line.startswith("; WIPE_TOWER_START"):
            in_tower = True
        elif line.startswith("; WIPE_TOWER_END"):
            in_tower = False
        elif line.startswith(";LAYER_CHANGE"):
            started = True
        elif started and TOOL.match(line):
            waiting = [n, None]
        elif MOVE.match(line):
            code = line.split(";")[0]
            mx, my = re.search(r"X" + NUM, code), re.search(r"Y" + NUM, code)
            x, y = (float(mx.group(1)) if mx else x), (float(my.group(1)) if my else y)
            if in_tower and (mx or my) and re.search(r"E[\d.]", code) and x is not None and y is not None:
                xs.append(x)
                ys.append(y)
            if waiting:
                axes = set(AXIS.findall(code))
                if axes and waiting[1] is None:
                    waiting[1] = axes == {"Z"}
                # the tower block writes its moves as "G1  X.. Y..": the first one is the entry
                if raw.startswith("G1  X") and mx and my:
                    changes.append((waiting[0], (x, y), waiting[1]))
                    waiting = None
    if xs:
        # shortcut: tower box = extent of what the tower extrudes (0.02 mm from the slicer's own
        # box in the files checked); read the box from the project instead if that ever matters
        tower = (min(xs), min(ys), max(xs), max(ys))
    return bed, tower, changes


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        bed, tower, changes = read(read_lines(argv[1]))
    except (OSError, ValueError) as e:
        print(f"{argv[1]}: {e}", file=sys.stderr)
        return 2
    if not (bed and tower and changes):
        print(f"{argv[1]}: no printable_area, prime tower or tool change found", file=sys.stderr)
        return 2
    right = min(tower[2] + PARK, bed[2])
    park_x = right if right > tower[2] else max(tower[0] - PARK, bed[0])
    print(f"bed X{bed[0]:g}..{bed[2]:g} Y{bed[1]:g}..{bed[3]:g}; tower with ribs and brim "
          f"X{tower[0]:.2f}..{tower[2]:.2f} Y{tower[1]:.2f}..{tower[3]:.2f}; head parks at X{park_x:.2f}")
    why, agree, dropped = Counter(), 0, 0
    for n, entry, lowered in changes:
        bad = [p for p in detour((park_x, entry[1]), entry, tower) if outside(p, bed)]
        dropped += bool(bad)
        agree += bool(bad) == bool(lowered)
        if bad:
            side = "left" if entry[0] < (tower[0] + tower[2]) / 2 else "right"
            why[(side, round(bad[0][0], 2), round(bad[0][1], 2))] += 1
    print(f"{dropped} of {len(changes)} tool changes lose the detour "
          f"(the file agrees in {agree} of {len(changes)})")
    for (side, px, py), k in sorted(why.items(), key=lambda kv: -kv[1]):
        over = max(bed[0] - px, px - bed[2], bed[1] - py, py - bed[3])
        print(f"  {k} {side}-side entries: detour point X{px:g} Y{py:g} is {over:.2f} mm outside the bed")
    return 1 if dropped else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
