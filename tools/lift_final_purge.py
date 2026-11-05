#!/usr/bin/env python3
"""Lift the nozzle before the last trip to the prime tower in a Snapmaker Orca 2.4.1 G-code.

Orca 2.4.1 stopped travelling with a Z-hop before the final purge, so the nozzle drags across the
finished top layer at print height (https://forum.snapmaker.com/t/43865). This is a workaround until
a slicer release fixes it: it adds a Z-hop around that one travel and changes nothing else.

Usage: python3 lift_final_purge.py file.gcode
Edits the file in place, so it also works as an Orca post-processing script.
Only the last tower block can change, and only if it has no tool change and starts from the part.
"""
import re
import sys

MARK = "; lift_final_purge: Z-hop around the final purge travel"
DEFAULT_HOP = 0.4
XY_MOVE = re.compile(r"^G[01]\b.*\b[XY]-?[\d.]")


def hop_height(text):
    m = re.search(r"^; z_hop = ([\d.,]+)", text, re.M)
    hops = [float(x) for x in m.group(1).split(",") if x] if m else []
    return max(hops, default=0) or DEFAULT_HOP


def process(text):
    """Return (new text, number of travels lifted)."""
    if MARK in text:
        return text, 0
    lines = text.split("\n")
    stripped = [line.strip() for line in lines]
    unloads = [i for i, line in enumerate(stripped) if line == "; CP TOOLCHANGE UNLOAD"]
    if not unloads or "; CP TOOLCHANGE END" not in stripped[unloads[-1]:]:
        return text, 0
    start = unloads[-1]
    end = stripped.index("; CP TOOLCHANGE END", start)
    block = stripped[start:end]
    if any(re.match(r"^T\d+\b", line) for line in block):
        return text, 0  # a real tool change: its own G-code lifts
    before = next((line for line in reversed(stripped[:start]) if XY_MOVE.match(line)), "")
    if " E" not in before:
        return text, 0  # the slicer already travelled to the tower before this block
    i = next((start + k for k, line in enumerate(block) if XY_MOVE.match(line)), None)
    if i is None or re.search(r"\b[ZE]-?[\d.]", stripped[i]):
        return text, 0  # no bare XY travel to protect
    hop = "%g" % hop_height(text)
    lines[i:i + 1] = [MARK, "G91", "G1 Z%s F600" % hop, "G90", lines[i], "G91", "G1 Z-%s F600" % hop, "G90"]
    return "\n".join(lines), 1


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = sys.argv[1]
    # surrogateescape and newline="" keep every other byte of the slicer's file as it was
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as f:
        text = f.read()
    new, n = process(text)
    if n:
        with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
            f.write(new)
    print("%s: %s" % (path, "added a Z-hop around the final purge travel" if n else "nothing to change"))


if __name__ == "__main__":
    main()
