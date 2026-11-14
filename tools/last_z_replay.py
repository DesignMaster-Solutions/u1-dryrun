#!/usr/bin/env python3
"""Replay the slicer's get_last_z_from_gcode over the tool-change blocks of a sliced file.

OrcaSlicer#1083: after the change-filament G-code, the slicer asks this function where Z is.
The 2.4.1 version reads the U1's relative lift (G91 / G1 Z1.5 / G90) as "Z is 1.5 mm", so
without a prime tower the new head returns to the part at the layer height. Snapmaker/OrcaSlicer
PR 1191 makes the function follow G90/G91 from a start Z. Both versions are ported here line by
line, so a file sliced by the released build shows what each one answers at every tool change.

usage: last_z_replay.py file.gcode[.gz]
shortcut: a port of one function, not a build of the slicer; the return height it implies is
the rule read off the released file, re-slice with a real build of the PR to confirm.
"""
import gzip
import re
import sys

NUM = re.compile(r"[-+]?(\d+\.?\d*|\.\d+)")
RET = re.compile(r"G1 Z([-+.\d]+)")
HOP = 0.4   # z_hop of the U1 profile: what the released file adds to the answer before the travel back


def last_z(block, start_z=None):
    """start_z None = 2.4.1 (every Z is absolute); a number = PR 1191 (G90/G91 tracked)."""
    z, rel, changed = start_z, False, False
    for raw in block:
        s = raw.lstrip(" ").rstrip(";").rstrip(" ")
        if start_z is not None and re.match(r"G9[01]([ \t\r;]|$)", s):
            rel = s[2] == "1"
        if len(s) > 5 and s[:3] in ("G0 ", "G1 ", "G2 ", "G3 "):
            i = s.find(" Z")
            m = NUM.match(s[i + 2:i + 10]) if i >= 0 else None      # the C++ reads 8 chars at most
            rest = s[i + 2:i + 10][m.end():] if m else ""
            if m and (rest == "" and len(s) <= i + 10 or rest[:1] in (" ", "\t", "\r", ";")):
                z = z + float(m.group()) if rel else float(m.group())
                changed = True
    return z if changed else None


def track(s, z, rel):
    """Plain G-code reading of one line, independent of the port above: (z, relative)."""
    if re.match(r"G9[01]\b", s):
        rel = s[2] == "1"
    m = re.match(r"G[0-3] .*?Z([-+.\d]+)", s)
    if m:
        z = z + float(m.group(1)) if rel else float(m.group(1))
    return z, rel


def replay(lines):
    """One row per tool change after the first layer: layer, real Z, 2.4.1 answer, PR answer, Z the file returns at."""
    rows, z, rel, layer = [], 0.0, False, None
    for i, raw in enumerate(lines):
        s = raw.strip()
        if s.startswith(";Z:"):
            layer = float(s[3:])
        if s.startswith("; Change Tool") and layer is not None:
            j = i
            while not re.match(r"T\d+$", lines[j].strip()):
                j += 1
            while lines[j].strip() != "G90":
                j += 1
            block = [x.rstrip("\n") for x in lines[i:j + 1]]
            real, r = z, rel
            for x in block:
                real, r = track(x.strip(), real, r)
            ret = next(float(m.group(1)) for m in map(RET.match, lines[j + 1:]) if m)
            rows.append((layer, real, last_z(block), last_z(block, z), ret))
        z, rel = track(s, z, rel)
    return rows


def read_lines(path):
    with (gzip.open if path.endswith(".gz") else open)(path, "rt", errors="replace") as f:
        return f.readlines()


def main(path):
    rows = replay(read_lines(path))
    print("layer_z  real_z  2.4.1_says  pr1191_says  file_returns_at")
    for r in rows:
        print("%7.2f %7.2f %11.2f %12.2f %16.2f" % r)
    wrong = sum(abs(old - real) > 1e-6 for _, real, old, _, _ in rows)
    rule = sum(abs(ret - max(layer, old + HOP)) < 1e-6 for layer, _, old, _, ret in rows)
    print("%d tool changes: 2.4.1 answer differs from the real Z in %d, PR 1191 answer in %d"
          % (len(rows), wrong, sum(abs(n - real) > 1e-6 for _, real, _, n, _ in rows)))
    print("the file returns at max(layer, 2.4.1 answer + %.1f) in %d of %d; the same rule with the "
          "PR 1191 answer clears the layer by %.2f mm at least"
          % (HOP, rule, len(rows), min(max(layer, n + HOP) - layer for layer, _, _, n, _ in rows)))
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
