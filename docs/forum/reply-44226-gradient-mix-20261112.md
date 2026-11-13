I could reproduce this without a printer, and there is a setting that changes it.

**What I sliced** (Snapmaker Orca 2.4.1, macOS command line, 0.20 mm U1 profile): a 20 mm cube, two PLA filaments, the whole cube assigned to one mixed filament in gradient mode, 80% of filament 1 at the bottom to 20% at the top. Then I added up what each head extrudes in five height bands of the G-code:

| settings | layers | head 1 share, bottom to top |
|---|---|---|
| defaults | 100 | 57, 50, 50, 50, 44 % |
| "Subdivide Mix Layer" on | 100 | 57, 50, 50, 50, 44 % |
| "Full domain" on | 199 | 65, 56, 50, 44, 38 % |
| "Full domain" + "Subdivide Mix Layer" + "Apply subdivision to infill" | 199 | 78, 62, 50, 38, 25 % |

So with the defaults the slicer does what your preview and print show: one filament per 0.2 mm layer, alternating 1:1, the same halfway up as near the bottom. That is not the gradient you asked for.

With "Full domain" on, every layer is split in two thin passes, one per filament, and the thickness of each pass follows the gradient (about 0.16 mm + 0.04 mm at the bottom, the reverse at the top). The preview will still show the two colours alternating, because every layer still has both; what changes is how thick each stripe is. With only "Full domain" the infill stays 1:1, which is why the third row is weaker than the fourth. On a part with two walls it is the walls you see, so the third row may already be enough.

The option's own description says the thin passes are otherwise limited to painted areas, so painting the mixed filament on the model instead of assigning it to the whole object may also give the gradient. I did not test painting.

One more thing I ran into: "Height-weighted cadence" on its own printed my whole cube with the second filament only. I would leave it off.

**Limits:** my cube, not your model; command line, not the window, so I set these options by their config keys and took the names from the source code; I did not look up which tab shows them (the settings search should find "Full domain"). Nothing printed. I do not know which version you are on.

The band table comes from a small script I added to U1 Dry Run for this: `python3 tools/mix_by_height.py file.gcode`. If you export the G-code of your part after turning "Full domain" on, it tells you in a second whether the share moves with height before you spend the filament: https://github.com/DesignMaster-Solutions/u1-dryrun/blob/main/tools/mix_by_height.py
