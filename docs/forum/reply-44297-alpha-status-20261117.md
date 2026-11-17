Both are easy to check on a sliced file, so I ran them on the 2.4.2-alpha that Snapmaker published today (official macOS build, command line, nothing printed).

**2. Nozzle scratches the print at the final tool change: fixed in 2.4.2-alpha.** It is bug fix no. 2 in the release notes. I sliced the plate that showed it on 2.4.1 and the last travel across the finished top is gone, and the file replays clean on the firmware. Details in [OrcaSlicer#1149](https://github.com/Snapmaker/OrcaSlicer/issues/1149), now closed.

**1. "No sparse layers" crash: not fixed in 2.4.2-alpha.** Same test as in the other topic, a 38 mm block that changes colour at Z38:

| | tower Z at that tool change | part height |
|---|---|---|
| 2.4.1 | `G1 Z.2` | Z37.85 |
| 2.4.2-alpha | `G1 Z.2` | Z37.85 |

So the new head is still sent down 37.65 mm beside the part, and the slicer gives no warning. With the setting off, the same project is fine on the alpha. The issue is [OrcaSlicer#966](https://github.com/Snapmaker/OrcaSlicer/issues/966), where the developers said in October that the fix would be merged in the November version; I added today's result there.

Until it lands, the safe choice is to leave "No sparse layers" off. If you want to check a file you already sliced, `python3 tools/tower_below_print.py file.gcode` from [U1 Dry Run](https://github.com/DesignMaster-Solutions/u1-dryrun) says whether the tower is printed far below the part. The table of what else changed or did not change in the alpha is [here](https://github.com/DesignMaster-Solutions/u1-dryrun/blob/main/docs/orca-2.4.2-alpha-status.md).

Limits: my own test block, not the mask from the other topic, and macOS only.
