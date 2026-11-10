"""Travels to or from the prime tower and the lowest nozzle clearance over part material printed so far.

Usage: python3 tools/tower_travels.py dryrun/ file.gcode u1-dryrun-report/trace.txt [rows]
Unlike analyze.find_scars, material covered later counts too: this finds the head crossing the layer it just printed.
shortcut: the tower box below is the one from the 43745 file; read it from wipe_tower_x/y and the width if this becomes a check.
"""
import sys, math, collections
sys.path.insert(0, sys.argv[1]); import analyze, prep_gcode
text = prep_gcode.read_gcode(sys.argv[2]); types = analyze.line_types_from_gcode(text); del text
moves = analyze.parse_trace(sys.argv[3]); cell = analyze.CELL
tx0, tx1, ty0, ty1 = 224, 268, 212, 258  # tower + brim, from wipe_tower_x/y and the tower's G1 extents
at_tower = lambda x, y: tx0 <= x <= tx1 and ty0 <= y <= ty1
now = {}; rows = []
for m in moves:
    if analyze.is_extrusion(m):
        if types.get(m["line"]) != "Prime tower":
            for c in analyze.cells_on_segment(m["x0"], m["y0"], m["x"], m["y"], cell):
                now[c] = max(now.get(c, 0.0), max(m["z0"], m["z"]))
        continue
    if math.hypot(m["x"]-m["x0"], m["y"]-m["y0"]) < 5: continue
    if not (at_tower(m["x"], m["y"]) or at_tower(m["x0"], m["y0"])): continue
    over = []
    for c, s in analyze.cells_with_fraction(m["x0"], m["y0"], m["x"], m["y"], cell):
        h = now.get(c)
        if h is not None: over.append(m["z0"] + (m["z"]-m["z0"])*s - h)
    if len(over)*cell < 5: continue
    rows.append((min(over), len(over)*cell, m))
print("tower travels crossing >=5 mm of part:", len(rows))
print("min clearance histogram:", sorted(collections.Counter(round(r[0], 2) for r in rows).items()))
for g, L, m in sorted(rows, key=lambda r: r[0])[:int(sys.argv[4])]:
    print(m["line"], m["source"], m["tool"], "z0=%.2f z=%.2f" % (m["z0"], m["z"]), (round(m["x0"],1), round(m["y0"],1)), "->", (round(m["x"],1), round(m["y"],1)), "over %.1f mm, min clearance %.2f" % (L, g))
