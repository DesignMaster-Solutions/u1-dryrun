I reproduced this on macOS with your gist files, unchanged, on the Snapmaker Orca 2.4.1 command line (the same command as in your steps):

| run | exit | `; filament used [g]` | heads selected in the file |
|---|---|---|---|
| `process.json` + `original.3mf` | 0 | `0.00, 0.00, 0.00, 6.88` | `T3` only |
| `check-categories.json` + `original.3mf` (your workaround) | 0 | `0.00, 0.00, 5.79, 1.20` | `T2` and `T3` |

Same numbers as yours on Windows, so it is not platform specific.

Two things in the broken file that may help whoever fixes it:

- The prime tower is still there: 33 `; WIPE_TOWER_START` blocks in both files (24 of them `; CP EMPTY GRID` sparse layers in the broken one, 15 in the good one). The broken file has no `; toolchange #N` line at all, and its only `; CP TOOLCHANGE START` is the final unload at the end of the print. The good file has nine `; toolchange #N` blocks with the `; Change Tool3 -> Tool2` / `T2` sequence. So the tower was planned for more than one filament and the changes themselves are what went missing.
- The line `; total filament change = 9` of the good file is absent from the broken one.

As a control I sliced a single-colour part with the same `process.json` (`enable_prime_tower = 1`): the file has no tower at all. That makes "tower in the file, one head selected" a usable sign of this bug until it is fixed, so I added a small check for it: [`tools/dropped_toolchanges.py`](https://github.com/DesignMaster-Solutions/u1-dryrun/blob/main/tools/dropped_toolchanges.py) (`python3 dropped_toolchanges.py file.gcode`, also `.gcode.gz` and a sliced `.3mf`; exit 1 on a file like yours, 0 on the workaround file and on the single-colour control).

What I did not do: I did not rebuild the slicer, so I cannot confirm the `filament_adhesiveness_category` reading of the cause beyond the fact that your workaround fixes the output here too. Nothing was printed, I do not have a U1.
