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
| Snapmaker Orca 2.4.1, "Wall gap" off | X236.5 Y100 | 15 of 15 (first: line 2106, `G1 Z.25 F30000`) | 7 `CROSSING` (the 3 right-side entries plus 4 left-side ones, first at line 2109: 101.5 mm at Z0.25) and the same `SCAR` (line 36786), exit 1 |
| Snapmaker Orca 2.4.1, "Wall gap" off | X230.853 Y100 | 15 of 15 | 7 `CROSSING` and the same `SCAR`, exit 1 |
| Snapmaker Orca 2.4.0 | X236.5 Y100 | 0 of 15 | clean, exit 0 |

So on this plate 5.6 mm of tower position decides it: at X236.5 the detour point on the right is past the bed edge and is dropped, at X230.853 it is at X265.45, inside the bed, and the head lowers at the tower. Re-slicing the `.3mf` with the 2.4.1 command line gives the same moves as the first row (no difference outside comments and M73).

The first row is a case of `tests/e2e.sh`: the `.3mf` is read as it is and the three crossings must keep being reported.

Turning "Wall gap" off is not a workaround on 2.4.1 (rows 3 and 4, sliced 11 November 2026 from the same `.3mf` with only `wipe_tower_wall_gap` set to 0): without the park-and-detour path every tool change writes `G1 Z<layer>` before the XY move to the tower, on both sides and wherever the tower is. 2.4.0 writes the XY move first (`G1 X15.250 Y220.250 F30000`, then `G1 Z.45`). The one setting that came out clean on 2.4.1 is "Wall gap" on with the tower far enough from the bed edge (row 2). Row 3 is [`examples/tower-right-edge-orca-2.4.1-wall-gap-off.gcode.gz`](../examples/tower-right-edge-orca-2.4.1-wall-gap-off.gcode.gz) and a case of `tests/e2e.sh`.

Not verified: the project opened in the Orca window (it was sliced from the command line on macOS) and a printed part.

## The owner's two projects, re-sliced (11 November 2026)

The owner shared the two `.3mf` projects behind his photos ([forum 43745/21](https://forum.snapmaker.com/t/43745/21)). Each was sliced as it is with the Snapmaker Orca 2.4.1 command line on macOS (`--allow-newer-file --slice <plate>`) and read with [`tools/dock_drops.py`](../tools/dock_drops.py), which counts the tool changes whose first move after `T<n>` is a Z-only move. Text only: these two slices were not run through the firmware.

| Project | Saved with | Prime tower | Tool changes that lower Z at the dock |
|---|---|---|---|
| Bounding Bunny, plate 3 (229 layers) | 2.4.1 | X230.853 Y219.095, right back | 94 of 186 (first: line 129480, `G1 Z.45 F30000`); all 94 are right-side entries, as in the G-code he shared |
| KOI Fish (324 layers) | 2.4.0 | X24.407 Y229.819, left back | 222 of 453 (first: line 32661, `G1 Z.25 F30000`, last at Z49.05); all 222 are left-side entries (`G1 X29.721 ...`), the 231 others start with an XY move |

So the bunny project reproduces the shared file, and it is not only the right bed edge. The earlier advice "keep the tower about 10 mm from the left and right edges" does not hold for the KOI plate. Check a sliced file with `python3 tools/dock_drops.py file.gcode`: `0 of N` is the safe answer.

## Which detour point fails on each plate (11 November 2026)

[`tools/tower_detour.py`](../tools/tower_detour.py) is a Python port of `detour_around_wipe_tower()` and of the bed check after it. It takes the tower box from what the tower extrudes in the file, recomputes the detour of every tool change and prints the point that is outside `printable_area`. Its prediction against the files: 186 of 186 tool changes on the bunny plate, 15 of 15 on the small reproduction, 449 of 453 on the KOI plate (the other 4 are left-side entries where the head did not start from the park position; the slicer wrote a detour or a direct XY move there).

| Plate | Tower with ribs and brim | Point outside the bed (X0.5..270.5, Y1..271) |
|---|---|---|
| Bounding Bunny, plate 3 | X229.97..268.86 Y218.20..257.70 | right-side entries: the first detour point, X270.86, 0.36 mm past the right edge |
| KOI Fish | X22.63..67.81 Y228.03..273.52 | left-side entries: the back corners of the tower box, Y275.52, 4.52 mm past the back edge |

Why the back corner matters on the KOI plate: the head parks on the right of the tower (X70.82), so a left-side entry has to go round the box. The function builds two routes and takes the shorter. The forward one goes over the two back corners. The backward one, as written (`walk(false)` pushes `bbox_pts[i]` after stepping `i` back), goes from the right edge straight to the front-left corner and then to the back-left corner, so it also needs a back corner and never uses the front-right one. With the ribs reaching Y273.52 the back corners are at Y275.52, both routes fail the bed check and all left-side entries lose the detour. On this plate the ribs themselves print past Y271, the end of `printable_area`.

Checked by moving the tower only (the project's `wipe_tower_y`/`wipe_tower_x` in `Metadata/project_settings.config`, nothing else) and slicing again with the 2.4.1 command line:

| Project | Tower moved | Tool changes that lower Z at the dock |
|---|---|---|
| KOI Fish | 6 mm to the front (Y229.819 to Y223.819) | 0 of 453 (was 222); a left-side entry now reads `G1 X69.822 Y230.133`, `G1 X69.822 Y269.534`, `G1 X20.62 Y269.534`, then the entry |
| Bounding Bunny, plate 3 | 1 mm to the left (X230.853 to X229.853) | 0 of 186 (was 94); right-side entries get their detour point at X269.87, and the left-side ones now go round the back: `G1 X269.87 Y225.407`, `G1 X269.87 Y259.711`, `G1 X226.96 Y259.711`, `G1 X226.96 Y225.407` |

So the rule for 2.4.1 with "Wall gap" on is not a distance from the left and right edges: the tower box with its ribs and brim, plus 2 mm, has to be inside the bed on the right and at the back. `tower_detour.py` prints how far it is out.

For the fix, two places in `src/libslic3r/GCode.cpp` (not compiled here): when the detour is rejected, `append_tcr` should still travel to the tower entry before "Force restore layer Z" (2.4.0 wrote that XY move first); and the backward walk should push `bbox_pts[i]` before stepping back, so the front route exists, and a route should be chosen among those inside the bed.

Not done: the 2.4.0 control for the KOI project (the 2.4.0 command line crashes on it, exit 139), the firmware run of these slices, the projects opened in the Orca window, a printed part.

## A changed tool change G-code does not move the un-retract (11 November 2026)

A U1 owner posted a tool change G-code that drops `SM_PRINT_PREEXTRUDE_FILAMENT` and waits for temperature (`M109`), with "retraction length (tool change)" at 3 to 5 mm, "Wall gap" off and a rectangle prime tower ([forum 43745/24](https://forum.snapmaker.com/t/43745/24)); his test print left the excess on the tower. Sliced here with the 2.4.1 command line, same model, tower at X236.5 Y100, read with `tools/dock_drops.py`:

| Tool change G-code | Tool change retraction | Lower Z at the dock | Un-retract at the dock |
|---|---|---|---|
| stock | 10 mm | 15 of 15 | 15 of 15 (2 mm the first, 10 mm the others) |
| his | 5 mm | 15 of 15 | 15 of 15 (2 mm the first, 5 mm the others) |
| his | 3 mm | 15 of 15 | 15 of 15 (2 mm the first, 3 mm the others) |
| his, rib tower | 10 mm | 15 of 15 | 15 of 15 |

The slicer writes `G1 Z<layer>` and `G1 E<retraction>` after the template ends, so the template cannot reorder them. What the setting changes is the length pushed out at the dock.

**Correction, same day, after running them through the firmware.** The three rectangle-tower slices above are not printable: with the tower at X236.5 the rectangle tower's outer line goes to X271.41, 0.9 mm past the U1 limit (270.5), and the firmware stops at the first tower layer (`Move out of range on X axis: 271.410 95.090 0.250`, line 2247). The command-line slicer does not warn; only the rib-tower slice fits. The counts in the table are still what the files say, but the plates had to be redone. Re-sliced with the tower at X225 Y100 and run through the U1 firmware:

| Tool change G-code | Tool change retraction | Un-retract at the dock | Firmware run | Scars | Crossings |
|---|---|---|---|---|---|
| stock | 10 mm | 15 of 15 | to the end, 15 tool changes | 2 | 7 |
| stock | 5 mm | 15 of 15 | to the end | 2 | 7 |
| stock | 3 mm | 15 of 15 | to the end | 2 | 7 |
| his | 5 mm | 15 of 15 | to the end | 2 | 7 |
| his | 3 mm | 15 of 15 | to the end | 2 | 7 |

The two scars and the seven crossings are the same moves in all five (the scars: dock to tower at Z3.05 over 99.0 mm of finished surface, and part to tower at Z3.05 over 159.5 mm). Neither the template nor the retraction length changes where the head goes. Nothing printed: how much string 3, 5 or 10 mm leaves is not something the firmware run shows.

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

## The string on the side of the tower is the same bug (11 November 2026)

Owners describe a second symptom on 2.4.1 ([forum 44194](https://forum.snapmaker.com/t/filament-swap/44194)): after picking up the new head the printer pauses, extrudes, then goes to the tower and leaves a string on its side. In the files, the line after the Z drop at the dock is the un-retract: `G1 Z.45 F30000`, `G1 E10 F1800`, then `G1  X259.092 Y121.900 F30000` (small reproduction, lines 4525 to 4527). The plastic comes out in the air at the dock and rides to the tower on the nozzle. `tools/dock_drops.py` counts it:

| File | Lower Z at the dock | Un-retract at the dock |
|---|---|---|
| `examples/tower-right-edge-orca-2.4.1.3mf` ("Wall gap" on, tower at the edge) | 8 of 15 | 8 (10 mm each) |
| `examples/tower-right-edge-orca-2.4.1-wall-gap-off.gcode.gz` | 15 of 15 | 15 (2 mm the first, 10 mm the others) |
| `examples/sign-orca-2.4.1.gcode.gz` ("Wall gap" on, tower away from the edge) | 0 of 15 | 0: `G1 E10` comes after the XY move and the Z move, at the tower (line 9738) |

The un-retract is written by the slicer after the "Change filament G-code" of the printer profile ends, so editing that template cannot move it. A workaround posted on the forum ([43745/24](https://forum.snapmaker.com/t/43745/24)) differs from the stock template in three lines: `M104` became `M109` twice and `SM_PRINT_PREEXTRUDE_FILAMENT INDEX=<n>` was removed. In the U1 firmware (`klippy/extras/print_stats.py`, `cmd_SM_PRINT_PREEXTRUDE_FILAMENT`) that command does its work once per head per print (waste chute, 20 mm, cut, wipe) and returns at once on later tool changes, so removing it only skips the first prime of each head. A shorter tool change retraction pushes less plastic out at the dock; it does not move the un-retract.

Not done: a slice with that template (text comparison only), a printed part.
