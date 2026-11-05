#!/usr/bin/env python3
"""A/B of a slicer fix for the Orca 2.4.1 final purge scratch (Snapmaker/OrcaSlicer#1149).

Usage: python3 ab_final_purge.py base.gcode[.gz] patched.gcode[.gz]
Slice the same model with the unpatched and the patched build, then run this. It passes (exit 0) only if
the patched file no longer has the bare travel into the final purge and every other tool change block is
unchanged, line for line. Exit 1 otherwise, with what differs.
"""
import gzip
import json
import sys

import lift_final_purge as lift

START, END = "; CP TOOLCHANGE START", "; CP TOOLCHANGE END"


def bare_final_travel(text):
    """True if the last tower block still starts with a bare XY travel from the part (the scratch)."""
    return lift.process(text)[1] == 1


def tower_blocks(text):
    """Every tool change block from START to END, as stripped lines."""
    blocks, cur = [], None
    for line in text.split("\n"):
        s = line.strip()
        if s == START:
            cur = []
        if cur is not None:
            cur.append(s)
            if s == END:
                blocks.append(cur)
                cur = None
    return blocks


def compare(base, patched):
    a, b = tower_blocks(base), tower_blocks(patched)
    n = min(len(a), len(b))
    changed = [i for i in range(n - 1) if a[i] != b[i]]
    verdict = {
        "base_bare_final_travel": bare_final_travel(base),
        "patched_bare_final_travel": bare_final_travel(patched),
        "blocks": [len(a), len(b)],
        "other_blocks_changed": changed,
    }
    verdict["ok"] = (verdict["base_bare_final_travel"] and not verdict["patched_bare_final_travel"]
                     and len(a) == len(b) and not changed)
    return verdict


def read(path):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8", errors="surrogateescape", newline="") as f:
        return f.read()


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    verdict = compare(read(sys.argv[1]), read(sys.argv[2]))
    print(json.dumps(verdict))
    sys.exit(0 if verdict["ok"] else 1)


if __name__ == "__main__":
    main()
