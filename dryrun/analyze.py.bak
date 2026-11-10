"""Turn a dry-run trace into findings: scars on finished surfaces and tool-change stats.

A "scar" is a non-extruding move that crosses printed material which never gets covered
again, with the nozzle tip within CLEARANCE of it. Material that is printed over later
does not count, because the mark would be buried.
"""
import json
import math

CELL = 0.5  # mm per height-map cell; about one line width
CLEARANCE = 0.05  # mm; below this the nozzle tip is touching or dragging on the surface
MIN_LENGTH = 5.0  # mm; shorter crossings are the connectors between neighbouring infill lines
WASTE_TYPES = {"Prime tower"}  # material nobody keeps, so a mark on it does not matter


def parse_trace(path):
    """Return moves as dicts, with the position before and after each move."""
    moves, prev = [], None
    with open(path) as f:
        for raw in f:
            p = raw.split()
            if not p or p[0] != "M":
                continue
            x, y, z, e = float(p[1]), float(p[2]), float(p[3]), float(p[4])
            cur = {"x": x, "y": y, "z": z, "e": e, "v": float(p[5]),
                   "line": int(p[6]), "tool": p[7], "t": float(p[8]),
                   "source": "firmware" if p[9:] == ["F"] else "gcode"}
            if prev is not None:
                cur.update(x0=prev["x"], y0=prev["y"], z0=prev["z"], de=e - prev["e"])
                moves.append(cur)
            prev = cur
    return moves


def cells_with_fraction(x0, y0, x1, y1, cell=CELL):
    """Grid cells under a straight XY segment, each with how far along the segment it is (0-1)."""
    length = math.hypot(x1 - x0, y1 - y0)
    steps = max(1, int(length / (cell / 2)))
    out = []
    for i in range(steps + 1):
        s = i / steps
        c = (int((x0 + (x1 - x0) * s) / cell), int((y0 + (y1 - y0) * s) / cell))
        if not out or out[-1][0] != c:
            out.append((c, s))
    return out


def cells_on_segment(x0, y0, x1, y1, cell=CELL):
    return [c for c, _ in cells_with_fraction(x0, y0, x1, y1, cell)]


def is_extrusion(m):
    return m["de"] > 1e-6 and math.hypot(m["x"] - m["x0"], m["y"] - m["y0"]) > 1e-6


def line_types_from_gcode(text):
    """Map each G-code line number to the slicer's ;TYPE: in force on that line."""
    types, current = {}, None
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith(";TYPE:"):
            current = line[6:].strip()
        types[number] = current
    return types


def find_scars(moves, clearance=CLEARANCE, min_length=MIN_LENGTH, cell=CELL, line_types=None):
    line_types = line_types or {}
    waste = lambda m: line_types.get(m["line"]) in WASTE_TYPES  # noqa: E731
    final = {}
    for m in moves:
        if is_extrusion(m) and not waste(m):
            for c in cells_on_segment(m["x0"], m["y0"], m["x"], m["y"], cell):
                final[c] = max(final.get(c, 0.0), max(m["z0"], m["z"]))
    now, scars = {}, []
    for m in moves:
        if is_extrusion(m):
            if not waste(m):
                for c in cells_on_segment(m["x0"], m["y0"], m["x"], m["y"], cell):
                    now[c] = max(now.get(c, 0.0), max(m["z0"], m["z"]))
            continue
        if math.hypot(m["x"] - m["x0"], m["y"] - m["y0"]) < cell:
            continue
        hit, worst = 0, None
        for c, s in cells_with_fraction(m["x0"], m["y0"], m["x"], m["y"], cell):
            h = now.get(c)
            # finished = this cell already reached its final height, so a mark stays visible
            if h is None or h < final[c] - 1e-6:
                continue
            gap = m["z0"] + (m["z"] - m["z0"]) * s - h  # Z moves with XY on a ramped lift
            if gap < clearance:
                hit += 1
                worst = gap if worst is None else min(worst, gap)
        if hit * cell >= min_length:
            scars.append({
                "line": m["line"], "tool": m["tool"], "z": round(m["z"], 3),
                "source": m["source"],
                "from": [round(m["x0"], 2), round(m["y0"], 2)],
                "to": [round(m["x"], 2), round(m["y"], 2)],
                "length_mm": round(hit * cell, 1), "clearance_mm": round(worst, 3),
            })
    return scars


def read_end(path):
    """Klipper's own end-of-print time, firmware errors and the commands stubbed out."""
    end, errors, skipped = None, [], []
    with open(path) as f:
        for raw in f:
            if raw.startswith("END "):
                end = float(raw.split()[1])
            elif raw.startswith("SKIP "):
                skipped.append(raw.split()[1])
            elif raw.startswith("ERR "):
                _, line, msg = raw.rstrip("\n").split(" ", 2)
                errors.append({"line": int(line), "message": msg})
    return end, errors, skipped


def firmware_motion_time(moves, accel=5000.0):
    """Rough seconds of motion the firmware added (tool changes): trapezoid per move, no heating."""
    total = 0.0
    for m in moves:
        if m["source"] != "firmware" or m["v"] <= 0:
            continue
        d = math.dist((m["x0"], m["y0"], m["z0"]), (m["x"], m["y"], m["z"]))
        ramp = m["v"] ** 2 / accel
        total += 2 * m["v"] / accel + (d - ramp) / m["v"] if d > ramp else 2 * math.sqrt(d / accel)
    return total


def tool_stats(moves):
    stats, last, changes = {}, None, 0
    for m in moves:
        s = stats.setdefault(m["tool"], {"extruded_mm": 0.0, "moves": 0})
        s["moves"] += 1
        if m["de"] > 0:
            s["extruded_mm"] += m["de"]
        if last is not None and m["tool"] != last:
            changes += 1
        last = m["tool"]
    for s in stats.values():
        s["extruded_mm"] = round(s["extruded_mm"], 1)
    return stats, changes


def footprint(moves, line_types=None, cell=2.0):
    """Coarse top-view cells of the kept part, for the report's picture."""
    line_types = line_types or {}
    cells = set()
    for m in moves:
        if is_extrusion(m) and line_types.get(m["line"]) not in WASTE_TYPES:
            cells.update(cells_on_segment(m["x0"], m["y0"], m["x"], m["y"], cell))
    return sorted(cells)


def analyze(trace_path, clearance=CLEARANCE, line_types=None):
    moves = parse_trace(trace_path)
    tools, changes = tool_stats(moves)
    scars = find_scars(moves, clearance=clearance, line_types=line_types)
    end, errors, skipped = read_end(trace_path)
    return {
        "moves": len(moves),
        "tool_changes": changes,
        "tools": tools,
        "motion_time_s": round(end, 1) if end else None,
        "firmware_motion_s": round(firmware_motion_time(moves), 1),
        "errors": errors,
        "skipped_commands": skipped,
        "footprint": footprint(moves, line_types),
        "scars": scars,
    }


def main(argv):
    print(json.dumps(analyze(argv[1]), indent=2))


if __name__ == "__main__":
    import sys
    main(sys.argv)
