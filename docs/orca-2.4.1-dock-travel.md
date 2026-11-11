# Snapmaker Orca 2.4.1: after a tool change the new head drops to layer height at the dock and crosses the plate

File: a U1 owner's plate shared on the forum (https://forum.snapmaker.com/t/43745/12), Snapmaker Orca 2.4.1, sliced 2026-10-31, 27 objects, 229 layers, 187 tool changes, prime tower at X230.853 Y219.095 (right back corner), `wipe_tower_wall_gap = 1` (the default).

Run: the whole file through the U1 firmware 2.1.0 (Klipper exited normally at 72284 s of print time), then `tools/tower_travels.py` on the trace. When this was written the standard report was clean, because these crossings are covered by the next layers; this script counts any material printed so far.

## What happens

- 94 of the 187 tool changes enter the tower on its right side (X262.665). In all 94 the slicer writes `G1 Z<layer> F30000` right after `T<n>`, before any XY move. The firmware has just left the new head at its dock exit (X43.5, X94.2 or X161.7, Y250), so the Z drop happens there, and the tower block's first move (`G1  X262.665 Y...`) crosses the plate at the height of the layer just printed.
- 92 enter on the left (X236.165). There the slicer first writes the "return to wipe tower" detour (`G1 X227.96 Y237.607`, `G1 X236.165 Y237.607`) at the lifted height and only then lowers Z at the tower.
- 74 of the 94 pass over 24 to 133 mm of part with the nozzle at the height of the layer in progress, from Z0.45 to Z42.85 (head 0: 33, head 1: 23, head 2: 18), and each touches it (0.00 mm) somewhere. Full list below; "over" in it is the whole length above the part, not the length in contact.
- In 52 of the 74 the contact at 0.00 mm is 5.0 to 40.5 mm long (head 0: 16, head 1: 23, head 2: 13): where the path runs over what the current layer has already printed. Since 10 November 2026 the standard report lists these as `CROSSING line N` and exits 1. In the other 22 the contact is shorter than 5 mm; the rest of every path is over earlier layers, below the nozzle.
- Corrected 10 November 2026: this page first said "74 cross 24 to 133 mm of part at 0.00 mm". 24 to 133 mm is the length over the part; the length in contact is the line above. Line 8829545 (the final purge, #1149, the 187th) is a separate move.

## Why (Snapmaker/OrcaSlicer v2.4.1, src/libslic3r/GCode.cpp, WipeTowerIntegration::append_tcr)

New in 2.4.1 (absent in v2.4.0): with `wipe_tower_wall_gap` on, the head parks beside the tower before the tool change and returns through `detour_around_wipe_tower()`. If any detour point is outside `printable_area`, `use_avoid` is false and no detour move is written, but `gcodegen.set_last_pos(target_obj)` still runs, so the slicer believes the head is at the tower. "Force restore layer Z" then lowers it where it really is: the dock.

In this file the detour starts 8.205 mm outside the entry point (left: 236.165 - 8.205 = 227.96). On the right that is 262.665 + 8.205 = 270.87, past the bed edge at X270.5, so every right-side entry loses the detour.

## Small reproduction (11 November 2026)

[`examples/tower-right-edge-orca-2.4.1.3mf`](../examples/tower-right-edge-orca-2.4.1.3mf) is a project that shows it in a 2 hour, 15 layer plate instead of a 22 hour one: the two-colour sign from `examples/` (ring.stl + inlay.stl), default U1 0.20 mm profile, two Snapmaker PLA, prime tower at X236.5 Y100. Open it in Snapmaker Orca and slice. Same model and profile, three slices, each run through the U1 firmware 2.1.0:

| Slicer | Prime tower | Tool changes that lower Z at the dock | Dry Run |
|---|---|---|---|
| Snapmaker Orca 2.4.1 | X236.5 Y100 | 8 of 15 (first: line 4525, `G1 Z.45 F30000` right after `T0`) | 3 `CROSSING` (lines 9734, 14909, 20512: 91.0, 22.5 and 91.0 mm through the part at layer height) and `SCAR line 36911` (91.0 mm of the finished top at Z3.05), exit 1 |
| Snapmaker Orca 2.4.1 | X230.853 Y100 | 0 of 15 (detour written: `G1 X265.45 ...`) | no crossing; only the final purge travel of #1149 |
| Snapmaker Orca 2.4.0 | X236.5 Y100 | 0 of 15 | clean, exit 0 |

So on this plate 5.6 mm of tower position decides it: at X236.5 the detour point on the right is past the bed edge and is dropped, at X230.853 it is at X265.45, inside the bed, and the head lowers at the tower. Re-slicing the `.3mf` with the 2.4.1 command line gives the same moves as the first row (no difference outside comments and M73).

Not verified: the project opened in the Orca window (it was sliced from the command line on macOS), a slice with "Wall gap" off, and a printed part.

## The 74 travels

```
130636 gcode extruder z0=0.45 z=0.45 (43.5, 250.0) -> (262.7, 237.6) over 84.5 mm, min clearance 0.00
224119 gcode extruder1 z0=0.65 z=0.65 (94.2, 250.0) -> (262.7, 226.8) over 64.0 mm, min clearance 0.00
391923 gcode extruder z0=1.25 z=1.25 (43.5, 250.0) -> (262.7, 237.6) over 96.0 mm, min clearance 0.00
474774 gcode extruder1 z0=1.45 z=1.45 (94.2, 250.0) -> (262.7, 226.8) over 68.5 mm, min clearance 0.00
642246 gcode extruder z0=2.05 z=2.05 (43.5, 250.0) -> (262.7, 237.6) over 101.0 mm, min clearance 0.00
728671 gcode extruder1 z0=2.25 z=2.25 (94.2, 250.0) -> (262.7, 226.8) over 76.5 mm, min clearance 0.00
908093 gcode extruder z0=2.85 z=2.85 (43.5, 250.0) -> (262.7, 237.6) over 108.0 mm, min clearance 0.00
994344 gcode extruder1 z0=3.05 z=3.05 (94.2, 250.0) -> (262.7, 226.8) over 78.5 mm, min clearance 0.00
1199669 gcode extruder z0=3.65 z=3.65 (43.5, 250.0) -> (262.7, 237.6) over 111.0 mm, min clearance 0.00
1287842 gcode extruder1 z0=3.85 z=3.85 (94.2, 250.0) -> (262.7, 226.8) over 81.0 mm, min clearance 0.00
1508523 gcode extruder z0=4.45 z=4.45 (43.5, 250.0) -> (262.7, 237.6) over 112.0 mm, min clearance 0.00
1603585 gcode extruder1 z0=4.65 z=4.65 (94.2, 250.0) -> (262.7, 226.8) over 81.5 mm, min clearance 0.00
1802925 gcode extruder z0=5.25 z=5.25 (43.5, 250.0) -> (262.7, 237.6) over 112.5 mm, min clearance 0.00
1903453 gcode extruder1 z0=5.45 z=5.45 (94.2, 250.0) -> (262.7, 226.8) over 82.5 mm, min clearance 0.00
2094344 gcode extruder z0=6.05 z=6.05 (43.5, 250.0) -> (262.7, 237.6) over 116.5 mm, min clearance 0.00
2192317 gcode extruder1 z0=6.25 z=6.25 (94.2, 250.0) -> (262.7, 226.8) over 83.5 mm, min clearance 0.00
2357532 gcode extruder z0=6.85 z=6.85 (43.5, 250.0) -> (262.7, 237.6) over 119.5 mm, min clearance 0.00
2460431 gcode extruder1 z0=7.05 z=7.05 (94.2, 250.0) -> (262.7, 226.8) over 85.0 mm, min clearance 0.00
2621383 gcode extruder z0=7.65 z=7.65 (43.5, 250.0) -> (262.7, 237.6) over 120.0 mm, min clearance 0.00
2722274 gcode extruder1 z0=7.85 z=7.85 (94.2, 250.0) -> (262.7, 226.8) over 85.5 mm, min clearance 0.00
2870740 gcode extruder z0=8.45 z=8.45 (43.5, 250.0) -> (262.7, 237.6) over 121.0 mm, min clearance 0.00
2974410 gcode extruder1 z0=8.65 z=8.65 (94.2, 250.0) -> (262.7, 226.8) over 85.5 mm, min clearance 0.00
3126901 gcode extruder z0=9.25 z=9.25 (43.5, 250.0) -> (262.7, 237.6) over 122.5 mm, min clearance 0.00
3237510 gcode extruder1 z0=9.45 z=9.45 (94.2, 250.0) -> (262.7, 226.8) over 87.5 mm, min clearance 0.00
3392486 gcode extruder z0=10.05 z=10.05 (43.5, 250.0) -> (262.7, 237.6) over 125.0 mm, min clearance 0.00
3500942 gcode extruder1 z0=10.25 z=10.25 (94.2, 250.0) -> (262.7, 226.8) over 89.5 mm, min clearance 0.00
3635912 gcode extruder z0=10.85 z=10.85 (43.5, 250.0) -> (262.7, 237.6) over 127.5 mm, min clearance 0.00
3737338 gcode extruder1 z0=11.05 z=11.05 (94.2, 250.0) -> (262.7, 226.8) over 89.5 mm, min clearance 0.00
3866948 gcode extruder z0=11.65 z=11.65 (43.5, 250.0) -> (262.7, 237.6) over 128.0 mm, min clearance 0.00
3965527 gcode extruder1 z0=11.85 z=11.85 (94.2, 250.0) -> (262.7, 226.8) over 90.5 mm, min clearance 0.00
4082340 gcode extruder z0=12.45 z=12.45 (43.5, 250.0) -> (262.7, 237.6) over 128.5 mm, min clearance 0.00
4182748 gcode extruder1 z0=12.65 z=12.65 (94.2, 250.0) -> (262.7, 226.8) over 91.0 mm, min clearance 0.00
4301376 gcode extruder z0=13.25 z=13.25 (43.5, 250.0) -> (262.7, 237.6) over 129.0 mm, min clearance 0.00
4401160 gcode extruder1 z0=13.45 z=13.45 (94.2, 250.0) -> (262.7, 226.8) over 91.0 mm, min clearance 0.00
4527956 gcode extruder z0=14.05 z=14.05 (43.5, 250.0) -> (262.7, 237.6) over 129.5 mm, min clearance 0.00
4634224 gcode extruder1 z0=14.25 z=14.25 (94.2, 250.0) -> (262.7, 226.8) over 91.5 mm, min clearance 0.00
4764095 gcode extruder z0=14.85 z=14.85 (43.5, 250.0) -> (262.7, 237.6) over 129.5 mm, min clearance 0.00
4866042 gcode extruder1 z0=15.05 z=15.05 (94.2, 250.0) -> (262.7, 226.8) over 91.5 mm, min clearance 0.00
5004882 gcode extruder z0=15.65 z=15.65 (43.5, 250.0) -> (262.7, 237.6) over 129.5 mm, min clearance 0.00
5100826 gcode extruder1 z0=15.85 z=15.85 (94.2, 250.0) -> (262.7, 226.8) over 91.5 mm, min clearance 0.00
5326618 gcode extruder1 z0=16.65 z=16.65 (94.2, 250.0) -> (262.7, 226.8) over 92.5 mm, min clearance 0.00
5548726 gcode extruder1 z0=17.45 z=17.45 (94.2, 250.0) -> (262.7, 226.8) over 94.0 mm, min clearance 0.00
6388872 gcode extruder2 z0=21.25 z=21.25 (161.7, 250.0) -> (262.7, 237.6) over 32.0 mm, min clearance 0.00
6506725 gcode extruder2 z0=22.05 z=22.05 (161.7, 250.0) -> (262.7, 237.6) over 32.0 mm, min clearance 0.00
6613441 gcode extruder2 z0=22.85 z=22.85 (161.7, 250.0) -> (262.7, 237.6) over 32.0 mm, min clearance 0.00
6722169 gcode extruder2 z0=23.65 z=23.65 (161.7, 250.0) -> (262.7, 237.6) over 32.0 mm, min clearance 0.00
7290700 gcode extruder1 z0=29.25 z=29.25 (94.2, 250.0) -> (262.7, 251.4) over 64.0 mm, min clearance 0.00
7543513 gcode extruder2 z0=32.45 z=32.45 (161.7, 250.0) -> (262.7, 244.6) over 24.0 mm, min clearance 0.00
7548558 gcode extruder z0=32.65 z=32.65 (43.5, 250.0) -> (262.7, 233.8) over 133.0 mm, min clearance 0.00
7625238 gcode extruder2 z0=33.25 z=33.25 (161.7, 250.0) -> (262.7, 244.6) over 24.0 mm, min clearance 0.00
7637058 gcode extruder z0=33.45 z=33.45 (43.5, 250.0) -> (262.7, 233.8) over 133.0 mm, min clearance 0.00
7714192 gcode extruder2 z0=34.05 z=34.05 (161.7, 250.0) -> (262.7, 244.6) over 24.0 mm, min clearance 0.00
7724936 gcode extruder z0=34.25 z=34.25 (43.5, 250.0) -> (262.7, 233.8) over 133.0 mm, min clearance 0.00
7816778 gcode extruder2 z0=34.85 z=34.85 (161.7, 250.0) -> (262.7, 244.6) over 24.0 mm, min clearance 0.00
7830725 gcode extruder z0=35.05 z=35.05 (43.5, 250.0) -> (262.7, 233.8) over 133.0 mm, min clearance 0.00
7923578 gcode extruder2 z0=35.65 z=35.65 (161.7, 250.0) -> (262.7, 244.6) over 24.0 mm, min clearance 0.00
7938367 gcode extruder z0=35.85 z=35.85 (43.5, 250.0) -> (262.7, 233.8) over 133.0 mm, min clearance 0.00
8015559 gcode extruder2 z0=36.45 z=36.45 (161.7, 250.0) -> (262.7, 244.6) over 24.0 mm, min clearance 0.00
8029530 gcode extruder z0=36.65 z=36.65 (43.5, 250.0) -> (262.7, 233.8) over 133.0 mm, min clearance 0.00
8108648 gcode extruder2 z0=37.25 z=37.25 (161.7, 250.0) -> (262.7, 244.6) over 24.0 mm, min clearance 0.00
8123368 gcode extruder z0=37.45 z=37.45 (43.5, 250.0) -> (262.7, 233.8) over 133.0 mm, min clearance 0.00
8195341 gcode extruder2 z0=38.05 z=38.05 (161.7, 250.0) -> (262.7, 244.6) over 24.0 mm, min clearance 0.00
8208198 gcode extruder z0=38.25 z=38.25 (43.5, 250.0) -> (262.7, 233.8) over 133.0 mm, min clearance 0.00
8278520 gcode extruder2 z0=38.85 z=38.85 (161.7, 250.0) -> (262.7, 244.6) over 24.0 mm, min clearance 0.00
8291535 gcode extruder z0=39.05 z=39.05 (43.5, 250.0) -> (262.7, 233.8) over 133.0 mm, min clearance 0.00
8362060 gcode extruder2 z0=39.65 z=39.65 (161.7, 250.0) -> (262.7, 244.6) over 24.0 mm, min clearance 0.00
8374757 gcode extruder z0=39.85 z=39.85 (43.5, 250.0) -> (262.7, 233.8) over 133.0 mm, min clearance 0.00
8447067 gcode extruder2 z0=40.45 z=40.45 (161.7, 250.0) -> (262.7, 244.6) over 24.0 mm, min clearance 0.00
8460068 gcode extruder z0=40.65 z=40.65 (43.5, 250.0) -> (262.7, 233.8) over 133.0 mm, min clearance 0.00
8531808 gcode extruder2 z0=41.25 z=41.25 (161.7, 250.0) -> (262.7, 244.6) over 24.0 mm, min clearance 0.00
8544491 gcode extruder z0=41.45 z=41.45 (43.5, 250.0) -> (262.7, 233.8) over 133.0 mm, min clearance 0.00
8617122 gcode extruder2 z0=42.05 z=42.05 (161.7, 250.0) -> (262.7, 244.6) over 24.0 mm, min clearance 0.00
8630084 gcode extruder z0=42.25 z=42.25 (43.5, 250.0) -> (262.7, 233.8) over 133.0 mm, min clearance 0.00
8698565 gcode extruder2 z0=42.85 z=42.85 (161.7, 250.0) -> (262.7, 244.6) over 24.0 mm, min clearance 0.00
```
