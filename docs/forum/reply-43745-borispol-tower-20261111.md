@Mr.Borispol, I found what your two plates have in common, and a tower position that gives zero on each. Both checked by slicing your projects again with the 2.4.1 command line, changing only the prime tower position.

KOI Fish: move the prime tower 6 mm to the front (Y229.8 to Y223.8, same X). 0 of 453 tool changes lower the head at the dock, it was 222.

Bounding Bunny, plate 3: move the prime tower 1 mm to the left (X230.85 to X229.85). 0 of 186, it was 94.

The reason: in 2.4.1 the head goes round the prime tower after each tool change, and the slicer drops that whole path when one point of it is outside the bed. The box it goes round is the tower with its ribs and brim plus 2 mm. On the bunny plate that box is 0.36 mm past the right edge. On the KOI plate the ribs reach Y273.5 at the back, the box corner is at Y275.5 and the bed ends at Y271, so every tool change that enters the tower from the left loses the path. So it is not a distance from the left and right edges, as I said before: the tower with its ribs has to be 2 mm inside the bed on the right and at the back.

@Zoe_M, for the engineers, the two places in the code are in the issue: https://github.com/Snapmaker/OrcaSlicer/issues/1168

To get the number for another plate: https://github.com/DesignMaster-Solutions/u1-dryrun/blob/main/tools/tower_detour.py (Python 3, needs dock_drops.py from the same folder). `python3 tower_detour.py file.gcode` prints which point is outside the bed and by how many mm.

What I did not do: run these slices through the firmware or print them, and open the projects in the Orca window (command line only). After moving the tower, please check the sliced file with dock_drops.py before a long print: "0 of N" is the safe answer.
