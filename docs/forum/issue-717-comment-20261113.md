A measured data point for this, on Snapmaker Orca 2.4.1 (command line, macOS, U1 0.20 mm profile, English): a 20 mm cube, two PLA filaments, the whole object assigned to one mixed filament in gradient mode, 80% of filament 1 at the bottom to 20% at the top. Share of filament 1 extruded in five height bands of the G-code:

| settings | distinct Z heights | share of filament 1, bottom to top |
|---|---|---|
| defaults | 100 | 57, 50, 50, 50, 44 % |
| "Subdivide Mix Layer" only | 100 | 57, 50, 50, 50, 44 % |
| "Subdivide Mix Layer" + "Full domain" | 199 | 65, 56, 50, 44, 38 % |
| the same + "Apply subdivision to infill" | 199 | 78, 62, 50, 38, 25 % |

So in 2.4.1 the default is still 1:1. The two options recommended above do give a ramp on a whole object without painting, but about half the range asked for, because the infill stays 1:1; with "Apply subdivision to infill" it comes close to the 80 → 20 requested. If the options are going to be turned on automatically for gradient mode, the infill one seems to belong in that set.

Another user ran into this yesterday on the forum, with a print that came out as one flat blended colour: https://forum.snapmaker.com/t/44226

The numbers come from [`tools/mix_by_height.py`](https://github.com/DesignMaster-Solutions/u1-dryrun/blob/main/tools/mix_by_height.py), which adds up the extrusion per head by height. Limits: one cube of mine, nothing printed, painted regions not tested, only the English locale.
