#!/usr/bin/env python3
"""Share of the extruded filament per head in equal height bands of a sliced file.

    python3 tools/mix_by_height.py file.gcode [bands]

A mixed filament that is meant to fade from one colour to the other should show the share moving band by band;
the same share in every band is a plain alternation (Snapmaker forum topic 44226). A measurement, not a check:
always exits 0.
"""
import collections
import gzip
import re
import sys


def read_lines(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", errors="replace") as f:
        return f.read().splitlines()


def shares(lines, bands=5):
    """[(z_lo, z_hi, {head: percent})] and the number of distinct extruding Z heights."""
    # shortcut: relative E only (M83, what the U1 profiles write), upgrade if an absolute-E file shows up
    head, z, started, e_at = 0, 0.0, False, collections.defaultdict(float)
    for line in lines:
        if line.startswith(("; CHANGE_LAYER", ";LAYER_CHANGE")):
            started = True
        m = re.match(r"T(\d+)\s*$", line)
        if m:
            head = int(m.group(1))
            continue
        if not started or not line.startswith("G1"):
            continue
        mz = re.search(r" Z([\d.]+)", line)
        if mz:
            z = float(mz.group(1))
        me = re.search(r" E(-?[\d.]+)", line)
        if me and (" X" in line or " Y" in line) and float(me.group(1)) > 0:
            e_at[(round(z, 3), head)] += float(me.group(1))
    heights = sorted({k[0] for k in e_at})
    if not heights:
        return [], 0
    top, out = heights[-1], []
    for b in range(bands):
        lo, hi = top * b / bands, top * (b + 1) / bands
        s = collections.defaultdict(float)
        for (zz, t), e in e_at.items():
            if lo < zz <= hi:
                s[t] += e
        total = sum(s.values())
        out.append((lo, hi, {t: 100 * v / total for t, v in sorted(s.items())} if total else {}))
    return out, len(heights)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    rows, n = shares(read_lines(argv[1]), int(argv[2]) if len(argv) > 2 else 5)
    print(f"{n} distinct extruding Z heights")
    for lo, hi, s in rows:
        print(f"Z {lo:5.1f}-{hi:5.1f} mm: " + "  ".join(f"T{t} {p:5.1f}%" for t, p in s.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
