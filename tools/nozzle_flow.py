#!/usr/bin/env python3
"""Say which nozzle type (Standard or High Flow) a sliced file expects on each head it uses.

Snapmaker Orca shows "Nozzle 4: High Flow installed. G-code specifies Standard Flow." next to a
Send button that stays enabled (Snapmaker/OrcaSlicer#1103). The file itself carries what it was
sliced for, one value per head, in "; nozzle_volume_type = standard,standard,standard,high_flow".
This reads it as text, so the question can be asked before sending, from a script or by hand.

Usage: python3 nozzle_flow.py file.gcode|file.gcode.gz|sliced.3mf [installed]
  installed: what is on the printer, head 1 to 4, s = Standard, h = High Flow, e.g. s,s,s,h
Exit code: 0 fine (or nothing to compare with), 1 a head the file uses has the other nozzle type,
2 not a sliced file or the file does not say.
"""
import re
import sys

from dock_drops import TOOL, read_lines

BLOCK = re.compile(r"^; nozzle_volume_type = (.+)$")
NAMES = {"standard": "Standard", "high_flow": "High Flow"}
SHORT = {"s": "standard", "h": "high_flow"}


def find(lines):
    """Return ({head: type in the block} for the heads the file selects, how many values the block has)."""
    types, used = [], set()
    for line in lines:
        line = line.strip()
        m = BLOCK.match(line)
        if m:
            types = [t.strip().lower() for t in m.group(1).split(",")]
        elif TOOL.match(line):
            used.add(int(line.split(";")[0][1:]))
    return {h: types[h] for h in sorted(used) if h < len(types)}, len(types), len(used)


def main(argv):
    if len(argv) not in (2, 3):
        print(__doc__.strip().split("\n\n")[-1])
        return 2
    try:
        heads, values, used = find(read_lines(argv[1]))
    except (OSError, ValueError) as e:
        print(f"not a sliced file: {e}")
        return 2
    if not used:
        print("not a sliced file: no tool selection (T<n>) in it")
        return 2
    if len(heads) < used:
        # the 2.4.1 command line writes a single value when the project has a type it does not know
        print(f"cannot tell: the file selects {used} heads and the settings block has {values} nozzle_volume_type value(s)")
        return 2
    print("the file was sliced for: " + ", ".join(f"head {h + 1} {NAMES.get(t, t)}" for h, t in heads.items()))
    if len(argv) == 2:
        return 0
    installed = [SHORT.get(x.strip().lower()[:1]) for x in argv[2].split(",")]
    if None in installed or any(h >= len(installed) for h in heads):
        print("installed: one letter per head, s or h, covering every head the file uses, e.g. s,s,s,h")
        return 2
    wrong = [(h, t) for h, t in heads.items() if installed[h] != t]
    if not wrong:
        print("ok: every head the file uses has the nozzle type it was sliced for")
        return 0
    for h, t in wrong:
        print(f"NOZZLE FLOW MISMATCH: head {h + 1} has {NAMES[installed[h]]} installed, the file was sliced for "
              f"{NAMES.get(t, t)}.")
    print("Slice again with the installed type on that head, or send it knowing the difference")
    print("(Snapmaker/OrcaSlicer#1103 asks the slicer to stop and ask at Send).")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
