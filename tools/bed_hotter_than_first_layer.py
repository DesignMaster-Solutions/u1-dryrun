#!/usr/bin/env python3
"""Tell whether the bed is heated for a filament that does not print on the first layer.

Snapmaker Orca takes the highest bed temperature over every filament of the print for the start
M140/M190, even one that only prints a support interface hours later, or one named as support
filament when no support is generated (Snapmaker/OrcaSlicer#1073, still there in 2.4.1). PLA then
starts on a PETG bed. This reads the G-code as text: the bed temperature the start sets, each
filament's first-layer bed temperature for the plate in the settings block, and which heads extrude
on the first layer.

Usage: python3 bed_hotter_than_first_layer.py file.gcode|file.gcode.gz|sliced.3mf
Exit code: 0 fine, 1 the start heats the bed above every filament of the first layer, 2 not a sliced file.
"""
import re
import sys

from dock_drops import TOOL, read_lines

PLATE = {"Cool Plate": "cool_plate", "Engineering Plate": "eng_plate", "High Temp Plate": "hot_plate",
         "Textured PEI Plate": "textured_plate", "Textured Cool Plate": "textured_cool_plate",
         "Supertack Plate": "supertack_plate"}
SETTING = re.compile(r"^; (\w+) = (.*)$")
BED = re.compile(r"^M1[49]0\s+S(\d+\.?\d*)")
EXTRUDE = re.compile(r"^G[123]\s.*[XY].*\bE(\d*\.?\d+)")  # a move in X/Y that pushes filament


def find(lines):
    """Return (start bed temp, first-layer bed temp per filament, heads on layer 1, {other head: its first layer})."""
    block = {}
    for line in lines:
        m = SETTING.match(line.strip())
        if m:
            block[m.group(1)] = m.group(2)
    key = PLATE.get(block.get("curr_bed_type", ""))
    temps = [float(t) for t in block.get(f"{key}_temp_initial_layer", "").split(",") if t.strip()] if key else []
    bed, tool, layer, first, later = None, 0, 0, set(), {}
    for line in lines:
        line = line.strip()
        if line.startswith(";LAYER_CHANGE"):
            layer += 1
        elif TOOL.match(line):
            tool = int(line.split(";")[0][1:])
        elif bed is None and layer == 0 and BED.match(line):
            bed = float(BED.match(line).group(1))
        elif layer and EXTRUDE.match(line.split(";")[0]) and float(EXTRUDE.match(line.split(";")[0]).group(1)) > 0:
            if layer == 1:
                first.add(tool)
            else:
                later.setdefault(tool, layer)
    return bed, temps, first, {t: n for t, n in later.items() if t not in first}


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().split("\n\n")[-1])
        return 2
    try:
        bed, temps, first, later = find(read_lines(argv[1]))
    except (OSError, ValueError) as e:
        print(f"not a sliced file: {e}")
        return 2
    if bed is None or not temps or not first:
        print("not a sliced file: no start bed temperature, first layer or bed temperatures in the settings block")
        return 2
    if max(first) >= len(temps):  # shortcut: a block shorter than the heads cannot be judged, treat as fine
        print("ok: the settings block has no bed temperature for every head of the first layer, nothing to compare")
        return 0
    want = max(temps[t] for t in first)
    if bed <= want:
        print(f"ok: the start sets the bed to {bed:g} C, no more than the first layer's filaments ask for")
        return 0
    heads = ", ".join(f"head {t + 1} ({temps[t]:g} C)" for t in sorted(first))
    print(f"BED HOTTER THAN FIRST LAYER: the start heats the bed to {bed:g} C; the first layer prints only {heads}.")
    for t, v in enumerate(temps):
        if v > want and t not in first:
            print(f"Filament {t + 1} asks for {v:g} C and "
                  + (f"first prints on layer {later[t]}." if t in later else "never prints in this file."))
    print("Snapmaker/OrcaSlicer#1073: the slicer takes the highest bed temperature over every filament of the")
    print("print. Until it is fixed, set that filament's bed temperature to the first layer's, or point")
    print("support / support interface at a filament that prints on the first layer.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
