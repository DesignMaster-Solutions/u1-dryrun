#!/usr/bin/env python3
"""Tell whether "Small area flow compensation" is on in the settings but left out of the moves.

Snapmaker Orca 2.4.0 and 2.4.1 write the same moves with the switch on or off (Snapmaker/OrcaSlicer#1064).
This reads the G-code as text: in internal solid infill and top surface, the filament per millimetre of the
short lines against the long lines of the same width and layer height, next to what the model in the
settings block asks for at that length.

Usage: python3 small_area_flow.py file.gcode|file.gcode.gz|sliced.3mf
Exit code: 0 fine or nothing to compare, 1 the switch is on and short lines carry the full flow, 2 not a sliced file.
"""
import math
import re
import statistics
import sys

from dock_drops import read_lines

SETTING = re.compile(r"^; (small_area_infill_flow_compensation(?:_model)?) = (.*)$")
MOVE = re.compile(r"^G([0-3])\b([^;]*)")
WORD = re.compile(r"([XYE])(-?\d*\.?\d+)")
ROLES = ("Internal solid infill", "Top surface")  # first-layer roles are compensated too; left out, they vary more
SHORT, LONG, FEW = 2.0, 10.0, 4


def model(text):
    """[(length mm, flow factor)] from the settings block value, sorted by length."""
    return sorted((float(a), float(b)) for a, b in re.findall(r"(\d*\.?\d+),(\d*\.?\d+)", text))


def factor(points, length):
    """Flow factor the model asks for at this line length (straight line between its points)."""
    if not points or length >= points[-1][0]:
        return 1.0
    for (l0, f0), (l1, f1) in zip(points, points[1:]):
        if length <= l1:
            return f0 + (f1 - f0) * (length - l0) / (l1 - l0) if l1 > l0 else f1
    return points[0][1]


def find(lines):
    """Return (switch on, or None without the key; [(median short length, short/long flow, model factor, short lines)])."""
    block, role, width, height, x, y, lens = {}, None, None, None, None, None, {}
    for line in lines:  # shortcut: reads E as relative (M83), which is what the U1 profiles use
        line = line.strip()
        m = SETTING.match(line)
        if m:
            block[m.group(1)] = m.group(2)
        elif line.startswith(";TYPE:"):
            role = line[6:]
        elif line.startswith(";WIDTH:"):
            width = line[7:]
        elif line.startswith(";HEIGHT:"):
            height = line[8:]
        else:
            m = MOVE.match(line)
            if not m:
                continue
            w = {k: float(v) for k, v in WORD.findall(m.group(2))}
            nx, ny = w.get("X", x), w.get("Y", y)
            if m.group(1) == "1" and role in ROLES and w.get("E", 0) > 0 and None not in (x, y, nx, ny):
                d = math.hypot(nx - x, ny - y)
                if d > 0.05:
                    lens.setdefault((role, width, height), []).append((d, w["E"] / d))
            x, y = nx, ny
    if "small_area_infill_flow_compensation" not in block:
        return None, []
    points, groups = model(block.get("small_area_infill_flow_compensation_model", "")), []
    for moves in lens.values():
        short = [m for m in moves if m[0] <= SHORT]
        long_ = [e for d, e in moves if d >= LONG]
        if len(short) >= FEW and len(long_) >= FEW:
            length = statistics.median(d for d, _ in short)
            groups.append((length, statistics.median(e for _, e in short) / statistics.median(long_),
                           factor(points, length), len(short)))
    return block["small_area_infill_flow_compensation"] == "1", groups


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().split("\n\n")[-1])
        return 2
    try:
        on, groups = find(read_lines(argv[1]))
    except (OSError, ValueError) as e:
        print(f"not a sliced file: {e}")
        return 2
    if on is None:
        print("not a sliced file: no settings block (; small_area_infill_flow_compensation = ...) in it")
        return 2
    if not on:
        print("ok: small area flow compensation is off in this file")
        return 0
    groups = [g for g in groups if g[2] < 0.97]  # a model that asks for (almost) nothing leaves nothing to see
    if not groups:
        print("ok: small area flow compensation is on, but no solid infill here has both short and long lines to compare")
        return 0
    full = [g for g in groups if g[1] > (1 + g[2]) / 2]
    if not full:
        print("ok: short solid infill lines carry less flow, as the model asks ("
              + ", ".join(f"{r:.0%} at {d:.1f} mm" for d, r, _, _ in groups) + ")")
        return 0
    n = sum(g[3] for g in full)
    d, r, want, _ = max(full, key=lambda g: g[3])
    print(f"SMALL AREA FLOW: the switch is on, but {n} solid infill lines of 2 mm or less carry the full flow "
          f"({r:.0%} of the long lines at {d:.1f} mm; the model asks for {want:.0%}).")
    print("Snapmaker/OrcaSlicer#1064: Snapmaker Orca 2.4.0 and 2.4.1 write the same moves with the switch on or off;")
    print("OrcaSlicer 2.4.2 compensates the same model. Small solid areas get the full flow.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
