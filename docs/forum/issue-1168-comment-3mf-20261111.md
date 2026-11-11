Thank you for looking at it. Here is a 3mf that shows it in a small plate:

https://github.com/DesignMaster-Solutions/u1-dryrun/raw/main/examples/tower-right-edge-orca-2.4.1.3mf

It is not the forum user's project (I only have his G-code). It is a two-colour sign, 15 layers, default U1 0.20 mm profile, two Snapmaker PLA, prime tower at X236.5 Y100. I sliced it with the 2.4.1 command line on macOS; I have not opened it in the window.

The travel in this report is not the one from the tower to the model. It is the one before it, from the dock to the tower, right after the new head is picked up. In the 2.4.1 slice of this project, line 4519 to 4528:

```
T0
...
G1 Z.45 F30000
G1 E10 F1800
G1  X259.092 Y121.900 F30000
```

There is no XY move between `T0` and `G1 Z.45`, so the head lowers where the firmware left it, at the dock exit, and then goes to the tower in a straight line at layer height. 8 of the 15 tool changes do this, all the ones that enter the tower on the right.

Same model and profile, three slices, each replayed on the U1 firmware 2.1.0:

| Slicer | Prime tower | Tool changes that lower Z at the dock | Result on the firmware |
|---|---|---|---|
| 2.4.1 | X236.5 Y100 | 8 of 15 | 3 travels through the part at layer height (lines 9734, 14909, 20512: 91.0, 22.5, 91.0 mm) and one over the finished top (line 36911, 91.0 mm at Z3.05) |
| 2.4.1 | X230.853 Y100 | 0 of 15 | none; the detour is written (`G1 X265.45 Y121.9`) and Z lowers at the tower |
| 2.4.0 | X236.5 Y100 | 0 of 15 | clean |

So 5.6 mm of tower position decides it, which fits the cause in the report: at X236.5 the detour point on the right falls past X270.5, the detour is dropped, and `set_last_pos` still says the head is at the tower.

Not verified: a printed part, and a slice with "Wall gap" off.
