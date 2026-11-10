@Mr.Borispol, thank you, the file was enough. Here is what is in it, with line numbers, so nobody has to guess from photos.

The plate has 27 bunnies, 229 layers and 187 tool changes. Every trip to the prime tower and back, 372 of them, is one straight line across the plate at exactly 0.40 mm above the layer being printed. Example, line 73306: from the tower at X259 Y255 straight to X27 Y51, about 308 mm, over the other bunnies. So what you saw is what the file says: the heads fly straight over the models that sit between them and the tower. In the G-code they pass 0.4 mm above them, not through them, and this profile does not route around parts (`reduce_crossing_wall = 0`, `z_hop = 0.4`).

I ran the first 31 layers through the U1 firmware code, 2.0.0 and 2.1.0. The firmware accepts them and adds no lower move of its own. The whole 22 hour file was too big for my tool's memory, so for layers 32 to 229 I only measured the tower travels with a script.

Two things for the engineers:

1. Line 8829545, the last tool change: `G1 X236.415 Y231.757` from X56.4 Y244.0 at Z45.85, the print height, with no lift and before the retraction on line 8829556. That is the final purge travel from [#1149](https://github.com/Snapmaker/OrcaSlicer/issues/1149), 180 mm long in this file.
2. 0.4 mm of clearance on a 300 mm straight travel over 26 other parts leaves no room for anything that sticks up: a curled edge, a blob, a string from the arriving head. I cannot tell from one file whether 2.4.0 lifted higher or took another path on this same plate. A 2.4.0 slice of the same project would answer that in a minute, if anyone has one.

What I cannot say is which of these marked your prints. The file shows the paths, not the plastic.

Until a fix is out, your own finding is the safest one: put the tower where the trip to it does not cross a model. A larger Z hop should also widen that 0.4 mm, but I have not tested it on a printer.
