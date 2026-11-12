@CrazyIvan, thanks. Yes, but much less than Snapmaker Orca, so I ran one more this morning.

Before today there were two files from the official OrcaSlicer: yours (post 19, clean) and a one-colour 2.4.2 slice that runs on every change. Neither has a prime tower, so neither could show the two problems above.

Today I sliced the two-colour test plate with OrcaSlicer 2.5.0-rc and its own U1 profile, prime tower on, with the tower in the same place where Snapmaker Orca 2.4.1 fails (X236.5 Y100, right edge):

| Same plate, same tower place | Head lowered at the dock | On the firmware (2.1.0) |
|---|---|---|
| Snapmaker Orca 2.4.1 | 8 of 15 tool changes | 3 crossings |
| OrcaSlicer 2.5.0-rc | 0 of 15 | clean |

With the tower in its default place OrcaSlicer 2.5.0-rc is also 0 of 15 and clean, and there is no travel across the top layer at the final tool change, which is the other 2.4.1 problem.

What this does not show: it is one small plate with 15 tool changes, not printed. The two U1 profiles are not the same (OrcaSlicer's tower is 35 mm wide without the longer ribs, Snapmaker Orca's is 30 mm), so it says OrcaSlicer does not do it here, not that it never does. OrcaSlicer 2.4.2 crashed in the command line on my Mac as soon as the prime tower was on, and I did not look for the cause, so 2.4.2 with a tower is not checked.

The file is in the repository and runs on every change now: https://github.com/DesignMaster-Solutions/u1-dryrun/blob/main/examples/tower-right-edge-orcaslicer-2.5.0-rc.gcode.gz

If you have a multicolour file from OrcaSlicer that you printed, `python3 dock_drops.py yourfile.gcode` gives the first column in a second, and I would like to run it through the firmware.
