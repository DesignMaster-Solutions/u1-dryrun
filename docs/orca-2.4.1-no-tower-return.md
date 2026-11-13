# Snapmaker Orca 2.4.1, prime tower off: the new head returns to the part at layer height

Report: [OrcaSlicer#1083](https://github.com/Snapmaker/OrcaSlicer/issues/1083) (a U1 owner, polar bear project, dots of filament on the outside of a leg; the project was too large to attach). This page is a small plate that shows the same G-code, the experiment that confirms the cause the reporter suspected, and a change to the tool-change G-code that removes it in the sliced file.

Checked on 13 November 2026 with the Snapmaker Orca 2.4.1 command line on macOS. Text only: none of these files was run through the firmware or printed.

## Small reproduction

Two 20 x 20 x 10 mm boxes, 40 mm apart, one per head, stock `Snapmaker U1 (0.4 nozzle)` and 0.20 mm profiles, two Snapmaker PLA, print by layer, **prime tower off**: 50 layers, 50 tool changes after the first layer.

| Slice | First move after `T<n>` | [`tools/dock_drops.py`](../tools/dock_drops.py) |
|---|---|---|
| stock template ([file](../examples/no-tower-return-orca-2.4.1.gcode.gz)) | `G1 Z1.9 F30000` while the layer is below 1.9 mm, then `G1 Z<layer>` from layer 10 on (Z2.05, 2.25 ... 10.05), then the XY move to the part | 50 of 50 lower Z first; 42 at the height already printed, exit 1 |
| same plate, prime tower on (X far from the edges) | XY move to the tower | 0 of 50, exit 0 |
| stock template with `move_z = 3.0` | `G1 Z3.4 F30000` while the layer is below 3.4 mm, then `G1 Z<layer>` from layer 17 on (Z3.45) | 50 of 50; 34 at the height already printed |
| lift written as an absolute move ([file](../examples/no-tower-return-orca-2.4.1-absolute-lift.gcode.gz)) | `G1 Z<layer + 1.9>`, XY move, then `G1 Z<layer>` at the part | 50 of 50 start with a Z move, all above everything printed: not counted, exit 0 |

At layer 26 (Z5.25) the stock slice writes:

```gcode
G91
G1 Z1.5 F600
G90
...
T0
G1 Z5.25 F30000
G1 X119.398 Y119.398
```

and the absolute one:

```gcode
G90
G1 Z6.75 F600
...
T0
G1 Z7.15 F30000
G1 X119.398 Y119.398
G1 Z7.15
G1 Z5.25
```

## Cause

The reporter's guess holds. The U1 tool-change template lifts with `G91` / `G1 Z1.5` / `G90`. The slicer reads that `Z1.5` as an absolute position, so after the tool change it believes the nozzle is at 1.5 mm and the return height is max(layer Z, lift + 0.4 mm Z-hop). With the lift changed to 3.0 the return height became 3.4, and the layer where the clearance disappears moved from 10 to 17. Above that height the "restore Z" move is the one that brings the head down to the layer, and it comes before the XY move, where the firmware left the head: the dock exit.

This is a different path from the prime tower case of [#1168](https://github.com/Snapmaker/OrcaSlicer/issues/1168) ([page](orca-2.4.1-dock-travel.md)): no tower and no detour are involved, and the reporter saw it on 2.4.0 too. Moving the prime tower does not apply here.

## What removed it in the sliced file

In the printer preset, Machine G-code, Change filament G-code, the by-layer branch:

```
"G91
G1 Z" + move_z + " F600
G90
";
```

changed to

```
"G90
G1 Z" + (layer_z + move_z) + " F600
";
```

(`max_layer_z + move_z` gave the same file on this plate.) The real lift before the tool change is the same 1.5 mm; the slicer now knows where the nozzle is, travels back at layer + 1.9 mm and lowers at the part. `tools/check.py` on that file: 0 of 4 checks report it.

## Not verified

- No firmware run and no print. Whether the head touches the part on the way from the dock depends on where the part is; on the reporter's print it did.
- One plate, 10 mm tall, two heads, by layer. By object uses the other branch of the template and was not touched.
- Snapmaker Orca 2.4.0 was not sliced here (the reporter did), nor 2.5.0-rc or the official OrcaSlicer.
- The changed template was sliced from the command line with a copy of the stock printer profile, not saved from the Orca window.
