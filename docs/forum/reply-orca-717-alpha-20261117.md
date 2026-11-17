I re-ran the same cube on the official 2.4.2-alpha (`Snapmaker_Orca_Mac_universal_V2.4.2-alpha.dmg`, command line, macOS, English), since release notes 9, 10, 12 and 13 touch sub-layer mixing and someone may read them as covering this issue. For the gradient case they do not change the sliced file: every row is identical to 2.4.1.

Same input as my table above: 20 mm cube, two PLA filaments, whole object on one mixed filament in gradient mode, 80% of filament 1 at the bottom to 20% at the top. Share of filament 1 in five height bands:

| settings | distinct Z heights | 2.4.1 | 2.4.2-alpha |
|---|---|---|---|
| defaults | 100 | 57, 50, 50, 50, 44 % | 57, 50, 50, 50, 44 % |
| "Subdivide Mix Layer" only | 100 | 57, 50, 50, 50, 44 % | 57, 50, 50, 50, 44 % |
| "Subdivide Mix Layer" + "Full domain" | 199 | 65, 56, 50, 44, 38 % | 65, 56, 50, 44, 38 % |
| the same + "Apply subdivision to infill" | 199 | 78, 62, 50, 38, 25 % | 78, 62, 50, 38, 25 % |

So on the alpha the default is still 1:1, and the options are not switched on automatically yet, at least on the command line: the settings block of the default file still has `dithering_local_z_mode = 0`, `dithering_local_z_whole_objects = 0` and `dithering_local_z_infill = 0`. The only mixing default I see changed between the two versions is `dithering_local_z_direct_multicolor`, 0 in 2.4.1 and 1 in the alpha, and it does not change these numbers.

Limits: one cube of mine, whole object and not a painted area, nothing printed, command line only, so I cannot say what the GUI of the alpha switches on by itself, and I did not test the fixed-ratio case that note 9 describes or a non-English language. Measured with [`tools/mix_by_height.py`](https://github.com/DesignMaster-Solutions/u1-dryrun/blob/main/tools/mix_by_height.py).
