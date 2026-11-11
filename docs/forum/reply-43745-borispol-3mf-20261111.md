@Mr.Borispol, thank you for the two projects. I sliced both as they are with the 2.4.1 command line and counted the tool changes where the first move after picking up the new head is a Z-only move, which is the head coming down at the dock.

Bounding Bunny, plate 3: 94 of 186, all on the right side of the tower. That is the same as the G-code you shared, so the project reproduces it.

KOI Fish: 222 of 453, from Z0.25 to Z49.05, all on the left side of the tower (first one: line 32661, `G1 Z.25 F30000`, then `G1 X29.721 Y245.333`). I have to correct myself again here: your tower on that plate is at X24.4, 24 mm from the left edge, so my advice "keep the tower about 10 mm from the edges" does not hold. It is not only the right bed edge, and I do not know yet which point of the detour fails the bed check on this plate.

@Zoe_M, for the engineers: both projects show it straight from the 2.4.1 command line with `--slice`, no change to the files.

Anyone can check a sliced file in a second with this small script (Python 3, nothing to install): https://github.com/DesignMaster-Solutions/u1-dryrun/blob/main/tools/dock_drops.py
`python3 dock_drops.py file.gcode` prints "0 of N" when the file is safe from this.

What I did not do: run these two slices through the firmware (text only this time), slice the KOI project with 2.4.0 as a control (the 2.4.0 command line crashes on it), or find a tower position that gives 0 on these plates. Numbers: https://github.com/DesignMaster-Solutions/u1-dryrun/blob/main/docs/orca-2.4.1-dock-travel.md
