#!/usr/bin/env python3
"""Tell whether a head pulls back the wrong length of filament before it is parked at a tool change.

When the first filament has two flow variants (filament_flow_step_size = 2,1,1,1), Snapmaker Orca reads
a later filament's "retraction length when switching tool" from the wrong slot, and the head is parked
with another length than the one set for its filament (Snapmaker/OrcaSlicer#1085, still there in 2.4.1).
This reads the G-code as text: the length each leaving head pulls back in the prime tower's unload,
against the value the settings block gives for that head (the filament's own, else the printer's).

Usage: python3 toolchange_retraction.py file.gcode|file.gcode.gz|sliced.3mf
Exit code: 0 fine, 1 a head pulls back another length than its setting, 2 not a sliced file.
"""
import re
import sys

from dock_drops import TOOL, read_lines

SETTING = re.compile(r"^; (\w+) = (.*)$")
PULL = re.compile(r"^G1\b[^;]*\bE(-\d*\.?\d+)")
UNLOAD = "; CP TOOLCHANGE UNLOAD"  # only the prime tower marks where the leaving head retracts
SLACK = 0.05


def find(lines):
    """Return ({head: mm set for it} or None without the keys, {head: sorted mm it really pulls back})."""
    block, tool, unload, pulled, seen = {}, None, False, 0.0, {}
    for line in lines:
        line = line.strip()
        m = SETTING.match(line)
        if m:
            block[m.group(1)] = m.group(2)
        elif line.startswith(UNLOAD):
            unload, pulled = True, 0.0
        elif TOOL.match(line):
            new = int(line.split(";")[0][1:])
            if unload and tool is not None and new != tool:
                seen.setdefault(tool, set()).add(round(pulled, 3))
            tool, unload = new, False
        elif unload:
            m = PULL.match(line)
            if m:
                pulled -= float(m.group(1))
    try:
        printer = [float(v) for v in block["retract_length_toolchange"].split(",")]
        own = block.get("filament_retract_length_toolchange", "").split(",")
        want = {h: float(own[h]) if h < len(own) and own[h] not in ("", "nil") else v for h, v in enumerate(printer)}
    except (KeyError, ValueError):
        want = None
    return want, {h: sorted(v) for h, v in seen.items()}


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().split("\n\n")[-1])
        return 2
    try:
        want, seen = find(read_lines(argv[1]))
    except (OSError, ValueError) as e:
        print(f"not a sliced file: {e}")
        return 2
    if want is None:
        print("not a sliced file: no settings block (; retract_length_toolchange = ...) in it")
        return 2
    if not seen:
        print("ok: no prime tower unload in this file, nothing to compare")
        return 0
    wrong = {h: v for h, v in seen.items() if h in want and any(abs(x - want[h]) > SLACK for x in v)}
    if not wrong:
        print("ok: each head pulls back its own length before it is parked ("
              + ", ".join(f"head {h + 1}: {want[h]:g} mm" for h in sorted(seen) if h in want) + ")")
        return 0
    for h, v in sorted(wrong.items()):
        print(f"TOOL CHANGE RETRACTION: head {h + 1} is set to pull back {want[h]:g} mm before it is parked, "
              f"the file pulls back {', '.join(f'{x:g}' for x in v)} mm.")
    print("Snapmaker/OrcaSlicer#1085: with two flow variants on the first filament, a later filament's length")
    print("is read from the wrong slot, so a head can be parked with another head's length. Measured")
    print("on 2.4.1: with one flow variant on every filament (filament_flow_step_size = 1,1,1,1) it is right.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
