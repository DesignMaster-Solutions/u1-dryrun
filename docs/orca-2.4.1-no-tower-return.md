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

## Getting here with the tower switched on (OrcaSlicer#1119)

The same file can come out of the command line with `enable_prime_tower = 1` in the process settings. [OrcaSlicer#1119](https://github.com/Snapmaker/OrcaSlicer/issues/1119) (Windows, four heads): when the filament files passed to `--load-filaments` share one preset `name`, the 2.4.1 CLI turns the tower off and still exits 0. Reproduced here on macOS with two heads, 13 Nov 2026:

| Input | `--load-filaments` names | Effective `enable_prime_tower` | Tool changes | `dock_drops` | Filament used |
| --- | --- | ---: | ---: | --- | --- |
| project .3mf, boxes on extruder 1 and 2 | both `Snapmaker PLA` | 0 | 50 | 42 of 50 (8 more are hops) | 2.16 g, 2.11 g |
| same .3mf | `Snapmaker PLA 1`, `Snapmaker PLA 2` | 1 | 50 | 0 of 50 | 4.04 g, 4.19 g |

Only the `name` and `filament_settings_id` of the two filament files differ between the rows; colours are `#FFFFFF;#000000` in both G-code files. With `--debug 4` the first row logs `map all the filaments to the same one, load_filament_count 2` and `disable_wipe_tower_after_mapping: disable prime tower for only one filament!`. Loading the two STL files with `--load-filament-ids "1,2"` instead of the project keeps the tower with either naming.

So a script that slices for the U1 can lose the tower without asking for it, and the file it gets is the one above. `python3 tools/check.py file.gcode` exits 1 on it (`dock_drops`); `; enable_prime_tower = 0` in the file's config block next to more than one `T<n>` is the other sign.

### Two more rows: same colour, and a way out on 2.4.1 (PR 1190)

[Snapmaker/OrcaSlicer PR 1190](https://github.com/Snapmaker/OrcaSlicer/pull/1190) proposes to keep the tower when the same-named filaments have different colours. Two more slices of the same project with the released 2.4.1, both filament files named `Snapmaker PLA`, 14 Nov 2026:

| Colours (filament files and project) | Extra CLI option | Effective `enable_prime_tower` | Tool changes | `dock_drops` | Filament used |
| --- | --- | ---: | ---: | --- | --- |
| `#FFFFFF`, `#FFFFFF` | none | 0 | 50 | 42 of 50 (8 more are hops) | 2.16 g, 2.11 g |
| `#FFFFFF`, `#000000` | `--filament-colour "#FFFFFF;#000000"` | 1 | 50 | 0 of 50 | 4.04 g, 4.19 g |

- **Same name and same colour still prints with two heads.** The log says "only one filament", but the file has 50 tool changes and both heads extrude. A rule based on colour keeps this row as it is, so two spools of the same filament on two heads still lose the tower the process file asked for.
- **Way out today, no new build:** passing the colours on the command line keeps the tower on 2.4.1 (`different filament colours, switch disable_wipe_tower_after_mapping back to false` in the log). Giving each filament file its own `name` does the same (table above).

## The proposed slicer fix, replayed on these files

[Snapmaker/OrcaSlicer PR 1191](https://github.com/Snapmaker/OrcaSlicer/pull/1191) changes `get_last_z_from_gcode` to follow G90/G91 from the Z the slicer is at. [`tools/last_z_replay.py`](../tools/last_z_replay.py) is a line-by-line port of that function, before and after the PR, run over the 50 tool-change blocks of each file sliced here with the released 2.4.1:

| file | 2.4.1 answer differs from the real Z | PR 1191 answer differs | released file returns at max(layer, answer + 0.4) | same rule with the PR answer |
|---|---|---|---|---|
| stock template (`examples/no-tower-return-orca-2.4.1.gcode.gz`) | 50 of 50 (says 1.5) | 0 of 50 | 50 of 50 | layer + 1.9 mm |
| `move_z = 3.0` | 50 of 50 (says 3.0) | 0 of 50 | 50 of 50 | layer + 3.4 mm |
| absolute lift (`examples/no-tower-return-orca-2.4.1-absolute-lift.gcode.gz`) | 0 of 50 | 0 of 50 | 50 of 50 | layer + 1.9 mm |

So the function of the PR gives, on the stock template, the answer the absolute-lift template gets from 2.4.1, and that file was sliced: 0 of 50 drops. This is a port of one function in Python, not a build of the PR: the slicer was not compiled and no file was sliced with it.

## Not verified


- The #1119 rows: two heads, not the four of the report; the reporter's generator was not run; no firmware run of those two files.
- PR 1190 was read, not built: the two extra rows are the released 2.4.1. They show what a colour rule leaves unchanged and what already works, not the PR itself.

- No firmware run and no print. Whether the head touches the part on the way from the dock depends on where the part is; on the reporter's print it did.
- One plate, 10 mm tall, two heads, by layer. By object uses the other branch of the template and was not touched.
- Snapmaker Orca 2.4.0 was not sliced here (the reporter did), nor 2.5.0-rc or the official OrcaSlicer.
- The changed template was sliced from the command line with a copy of the stock printer profile, not saved from the Orca window.
