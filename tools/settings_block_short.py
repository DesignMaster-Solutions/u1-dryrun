#!/usr/bin/env python3
"""Tell whether the settings block at the end of the G-code gives one value where each head has its own.

Snapmaker Orca's command-line slices write a single value for nozzle_temperature,
nozzle_temperature_initial_layer, filament_flow_ratio, filament_max_volumetric_speed and
pressure_advance, whatever the number of filaments (Snapmaker/OrcaSlicer#1068, still there in 2.4.1).
The moves are right; a script that reads per-head values from the block gets head 1's value for
every head. This reads the G-code as text and compares the block with what the moves really set.

Usage: python3 settings_block_short.py file.gcode|file.gcode.gz|sliced.3mf
Exit code: 0 fine, 1 the block has one value and the heads differ in the moves, 2 not a sliced file.
"""
import re
import sys

from dock_drops import TOOL, read_lines

KEYS = ("nozzle_temperature", "nozzle_temperature_initial_layer", "filament_flow_ratio",
        "filament_max_volumetric_speed", "pressure_advance")
SETTING = re.compile(r"^; (\w+) = (.*)$")
HEAT = re.compile(r"^M10[49]\b")
ADVANCE = re.compile(r"^SET_PRESSURE_ADVANCE\b.*\bADVANCE=(-?\d*\.?\d+)")
PRINTING = 170  # below this an M104 is standby, preheat or cooldown, not a printing temperature


def find(lines):
    """Return (filaments, {key: values in the block} for the short keys, {head: (max temp, last advance)})."""
    block = {}
    for line in lines:
        m = SETTING.match(line.strip())
        if m:
            block[m.group(1)] = m.group(2)
    filaments = len(block["filament_type"].split(";")) if block.get("filament_type") else 0
    short = {k: block[k] for k in KEYS if k in block and len(block[k].split(",")) < filaments}
    tool, temp, advance = 0, {}, {}
    for line in lines:
        line = line.strip()
        if TOOL.match(line):
            tool = int(line.split(";")[0][1:])
        elif HEAT.match(line):
            code = line.split(";")[0]
            s, t = re.search(r"\bS(\d+\.?\d*)", code), re.search(r"\bT(\d+)", code)
            if s and float(s.group(1)) >= PRINTING:
                head = int(t.group(1)) if t else tool
                temp[head] = max(temp.get(head, 0), float(s.group(1)))
        else:
            m = ADVANCE.match(line)
            if m:
                advance[tool] = float(m.group(1))
    return filaments, short, {h: (temp.get(h), advance.get(h)) for h in sorted(set(temp) | set(advance))}


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().split("\n\n")[-1])
        return 2
    try:
        filaments, short, heads = find(read_lines(argv[1]))
    except (OSError, ValueError) as e:
        print(f"not a sliced file: {e}")
        return 2
    if not filaments:
        print("not a sliced file: no settings block (; filament_type = ...) in it")
        return 2
    if not short:
        print(f"ok: the settings block has a value per filament ({filaments}) for the per-head keys")
        return 0
    differ = len({v for v in heads.values()}) > 1
    if not differ:
        print(f"ok: the settings block has one value for {len(short)} per-head keys, and the heads print alike")
        return 0
    print(f"SETTINGS BLOCK SHORT: {filaments} filaments, but the block has one value for: "
          + ", ".join(f"{k} = {v}" for k, v in short.items()) + ".")
    print("What the moves really set: " + "; ".join(
        f"head {h + 1} up to {t:g} C" + (f", pressure advance {a:g}" if a is not None else "")
        for h, (t, a) in heads.items() if t is not None) + ".")
    print("Snapmaker/OrcaSlicer#1068: the print is right, the block is not. Read per-head values from the")
    print("project's project_settings.config, or put filament_volume_type and filament_flow_step_size in")
    print("every filament file passed to --load-filaments: the block then has a value per filament.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
