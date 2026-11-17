# Snapmaker Orca 2.4.2-alpha: which of these problems are still in the sliced file

Checked on 17 Nov 2026 with the official `Snapmaker_Orca_Mac_universal_V2.4.2-alpha.dmg` (command line, macOS, Apple silicon),
re-running the same inputs that were sliced with 2.4.1. Sliced files read as text; nothing was printed.

| Issue | What the file shows | 2.4.1 | 2.4.2-alpha | Check |
|---|---|---|---|---|
| [#1064](https://github.com/Snapmaker/OrcaSlicer/issues/1064) | "Small area flow compensation" on, moves identical to off | 444 short lines at full flow | same, 444 | `tools/small_area_flow.py` |
| [#1066](https://github.com/Snapmaker/OrcaSlicer/issues/1066) | `z_offset` 0.05 lost on the first move down (no tower / tower) | 204 of 4,512 / 4 of 25,338 moves | same counts | `tools/z_offset_lost.py` |
| [#1073](https://github.com/Snapmaker/OrcaSlicer/issues/1073) | bed heated for a support filament that is not on the first layer | `M190 S80` in both cases | same | `tools/bed_hotter_than_first_layer.py` |
| [#1083](https://github.com/Snapmaker/OrcaSlicer/issues/1083) | no tower: the new head comes down before the XY move | 50 of 50 tool changes | same, 50 of 50 | `tools/dock_drops.py` |
| [#1119](https://github.com/Snapmaker/OrcaSlicer/issues/1119) | project + two filament files with one name: tower switched off | `enable_prime_tower = 0`, 2.16 / 2.11 g | same | settings block |
| [#1124](https://github.com/Snapmaker/OrcaSlicer/issues/1124) | reporter's gist: two colours, one head selected | `0, 0, 0, 6.88` g, `T3` only | same; workaround file gives 5.91 / 1.09 g on `T2`, `T3` | `tools/dropped_toolchanges.py` |
| [#1085](https://github.com/Snapmaker/OrcaSlicer/issues/1085) | tool-change retraction taken from another slot | 3 wrong rows | 2 of the 3 fixed (the filament's own value is used); a nil value on a shifted slot is still wrong, and a head with no filament value now gets head 1's printer value (new) | `tools/toolchange_retraction.py` |
| [#1149](https://github.com/Snapmaker/OrcaSlicer/issues/1149) | final purge travel without a lift | present | gone | `tools/lift_final_purge.py` |

Example files from the alpha: `examples/small-area-flow-orca-2.4.2-alpha.gcode.gz`, `examples/dropped-toolchanges-orca-2.4.2-alpha.gcode.gz`,
`examples/toolchange-retraction-printer-value-orca-2.4.2-alpha.gcode.gz`, `examples/sign-orca-2.4.2-alpha-linux.gcode.gz`.

Not checked on the alpha: #1068, #1103, #1117, #1118, #1130, the forum topics on brim, mixed filament and "No sparse layers", Windows and Linux builds (except the sign), and the GUI.
