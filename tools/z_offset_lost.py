#!/usr/bin/env python3
"""Tell whether part of the print comes out without the printer profile's Z offset.

With a non-zero Z offset (z_offset) Snapmaker Orca shifts every Z word, except the move down onto a
part after a travel from an unknown position: the start of the print and each tool change when
there is no prime tower (Snapmaker/OrcaSlicer#1066, still there in 2.4.1). Everything extruded
before the next Z word is then z_offset too low (or too high). This reads the G-code as text,
without the firmware: it compares the Z of every extruding move with the layer's own `;Z:` plus the
`z_offset` written in the file's settings block.

Usage: python3 z_offset_lost.py file.gcode|file.gcode.gz|sliced.3mf
Exit code: 0 fine (or z_offset is 0), 1 moves printed without the offset, 2 not a sliced file.
"""
import re
import sys

from dock_drops import read_lines

MOVE = re.compile(r"^G[01]\s")
WORD = re.compile(r"([XYZE])(-?\d*\.?\d+)")
OFFSET = re.compile(r"^; z_offset = (-?\d*\.?\d+)")


def find(lines):
    """Return (z_offset, extruding moves checked, [(line number, layer Z, actual Z)] printed without it)."""
    offset = next((float(m.group(1)) for m in map(OFFSET.match, reversed(lines)) if m), 0.0)
    if not offset:
        return 0.0, 0, []
    z, layer, relative, checked, lost = 0.0, None, False, 0, []
    for n, line in enumerate(lines, 1):
        line = line.strip()
        if line.startswith(";Z:"):
            layer = float(line[3:])
        elif line.startswith("G90"):
            relative = False
        elif line.startswith("G91"):
            relative = True
        elif MOVE.match(line):
            w = {k: float(v) for k, v in WORD.findall(line.split(";")[0])}
            if "Z" in w:
                z = z + w["Z"] if relative else w["Z"]
            if w.get("E", 0) > 0 and ("X" in w or "Y" in w) and layer is not None:
                checked += 1
                # only the exact unshifted height: spiral vase and Z contouring move Z inside a layer
                if abs(z - layer) < 1e-4:
                    lost.append((n, layer, z))
    return offset, checked, lost


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().split("\n\n")[-1])
        return 2
    try:
        offset, checked, lost = find(read_lines(argv[1]))
    except (OSError, ValueError) as e:
        print(f"not a sliced file: {e}")
        return 2
    if not offset:
        print("ok: z_offset is 0 in this file, nothing to lose")
        return 0
    if lost:
        n, layer, z = lost[0]
        layers = sorted({l for _, l, _ in lost})
        print(f"Z OFFSET LOST: {len(lost)} of {checked} extruding moves are printed at the layer height without "
              f"z_offset {offset:+g}; first at line {n} (Z{z:g}, should be Z{layer + offset:g}); "
              f"{len(layers)} layer(s), from Z{layers[0]:g} to Z{layers[-1]:g}.")
        print("Snapmaker/OrcaSlicer#1066: the move down after the start or after a tool change with no prime")
        print("tower skips z_offset (fixed upstream in OrcaSlicer#11011, not in Snapmaker Orca 2.4.1).")
        return 1
    print(f"ok: {checked} extruding moves, all at layer height {offset:+g}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
