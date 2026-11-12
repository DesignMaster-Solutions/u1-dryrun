I tried to reproduce this without your file and could not, so here is what I ruled out and what would help.

Going by the number on the slider in your three screenshots (the file names are shifted by one): 18 at 3.65 mm is fine, 19 at 3.85 mm is the wrong one, and 20 at 4.05 mm, the top, is fine again. On the wrong layer the outline of the centre still looks white and only the fill inside it is red. So the slicer seems to have the right shape for the white body there and hands its solid fill to the other filament, on the one layer right under the top surface.

I built test projects with the same idea (a white base, a red frame and a white centre as separate parts of one object, each part with its own filament) and sliced them with Snapmaker Orca 2.4.1 on the command line with the stock "0.20mm Standard @Snapmaker U1" process. 8 variants: red inlay 3, 5 and 10 layers deep, parts touching and parts overlapping, 5 and 2 top shell layers, and a part face lying exactly on a slicing plane. In all 8 the centre is printed by the white head on every layer. So it is not simply "two colours side by side under a top surface". Something in your model or in one setting is needed.

Could you attach the project (File > Save Project As, the .3mf, zipped) or the STEP file, and say which Snapmaker Orca version you are on? With the file I can look for the setting that flips it, so you can keep slicing in batches without editing G-code by hand.

I maintain [u1-dryrun](https://github.com/DesignMaster-Solutions/u1-dryrun), which checks sliced U1 files before printing. If your file shows the pattern, a fill that changes head for a single layer is something it could report.
