#!/usr/bin/env python3
"""Find tool changes that bring a head in to print almost nothing on the part.

Snapmaker Orca changes heads for any amount of support, support interface or model on a layer, however
small. A head can then spend a full prime on the tower and leave a few tiny dots of interface that cool
and fall off before the next head comes back (Snapmaker/OrcaSlicer#1214: 0.48 mm of PLA interface on a
layer after ~43 mm on the tower). This reads the G-code as text: for every visit of a head (from its
T<n> to the next head) the filament it pushes on the prime tower and the filament it pushes anywhere
else, by feature type.

Usage: python3 thin_toolchanges.py file.gcode|file.gcode.gz|sliced.3mf [min_mm]
min_mm: a visit that prints less than this many mm of filament off the tower is flagged (default 1.0).
Exit code: 0 fine, 1 at least one visit prints less than min_mm off the tower, 2 not a sliced file.
"""
import re
import sys

from dock_drops import TOOL, read_lines

EXTRUDE = re.compile(r"^G[123]\s.*[XY].*\bE(\d*\.?\d+)")  # a move in X/Y that pushes filament
Z = re.compile(r"^;Z:(\d*\.?\d+)")


def visits(lines):
    """Return [(layer, z, head, mm on the tower, {feature type: mm off the tower})], one per head visit."""
    out, cur = [], None
    layer, z, kind, tower, absolute = 0, 0.0, "", False, False
    for raw in lines:
        line = raw.strip()
        if line.startswith(";LAYER_CHANGE"):
            layer += 1
        elif Z.match(line):
            z = float(Z.match(line).group(1))
        elif line.startswith(";TYPE:"):
            kind = line[6:]
        elif line.startswith("; WIPE_TOWER_START"):
            tower = True
        elif line.startswith("; WIPE_TOWER_END"):
            tower = False
        elif line.startswith("M82"):
            absolute = True
        elif line.startswith("M83"):
            absolute = False
        elif TOOL.match(line):
            head = int(line.split(";")[0][1:])
            if cur is None or cur[2] != head:
                cur = [layer, z, head, 0.0, {}]
                out.append(cur)
        elif layer and cur is not None:
            m = EXTRUDE.match(line.split(";")[0])
            if m and float(m.group(1)) > 0:
                if absolute:
                    raise ValueError("absolute extrusion (M82): only relative E is read")
                mm = float(m.group(1))
                if tower or kind == "Prime tower":
                    cur[3] += mm
                else:
                    cur[4][kind] = cur[4].get(kind, 0.0) + mm
    return [tuple(v) for v in out]


def main(argv):
    if len(argv) not in (2, 3):
        print(__doc__.strip().split("\n\n")[-1])
        return 2
    limit = float(argv[2]) if len(argv) == 3 else 1.0
    try:
        found = visits(read_lines(argv[1]))
    except (OSError, ValueError) as e:
        print(f"not a sliced file: {e}")
        return 2
    if not found:
        print("not a sliced file: no tool change and no layer")
        return 2
    # the first visit of the print starts the job; only later visits are tool changes
    thin = [v for v in found[1:] if v[0] and 0 < sum(v[4].values()) < limit]
    changes = len(found) - 1
    if not thin:
        print(f"ok: {changes} tool change(s), each prints at least {limit:g} mm of filament off the tower")
        return 0
    print(f"THIN TOOL CHANGES: {len(thin)} of {changes} tool change(s) print less than {limit:g} mm of filament "
          "off the prime tower.")
    for layer, z, head, on_tower, off in thin:
        what = ", ".join(f"{k or 'untyped'} {mm:.3f} mm" for k, mm in sorted(off.items()))
        print(f"  layer {layer} (Z {z:g}): head {head + 1} prints {what}; {on_tower:.2f} mm on the tower")
    print("Snapmaker/OrcaSlicer#1214: so little filament on the part tends to cool and fall off before the next")
    print("head prints on it, while the tower takes a full prime. Until the slicer has a minimum, raise the")
    print("support interface layers/density, or print support interface with the model's filament.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
