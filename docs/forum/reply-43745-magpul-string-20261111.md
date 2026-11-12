@magpul, I compared your tool change G-code with the stock one of the U1 profile and looked for the string in sliced files. The string is the same bug as the head coming down at the dock (#1168), and the slicer writes it after the tool change G-code ends, so the template cannot move it.

Your version differs from stock in three lines: `M104` became `M109` twice, and `SM_PRINT_PREEXTRUDE_FILAMENT` is gone. In the U1 firmware that command does its work once per head per print (waste chute, 20 mm, cut, wipe) and returns at once on every later tool change. So removing it does not touch the string. It only skips the first prime of each head.

Where the string comes from: in 2.4.1, when the slicer lowers the new head at the dock, the next line is the un-retract. My small example, lines 4525 to 4527:

```
G1 Z.45 F30000
G1 E10 F1800
G1  X259.092 Y121.900 F30000
```

The 10 mm comes out in the air at the dock and rides to the tower on the nozzle. This is the "move forward, pause, extrude, then go to the tower" you described. Counted on the same model, 15 tool changes each:

- "Wall gap" on, tower at the right bed edge: 8 of 15 un-retract at the dock.
- "Wall gap" off, same tower: 15 of 15.
- "Wall gap" on, tower away from the edge: 0 of 15. The un-retract comes after the move, at the tower.

A shorter tool change retraction pushes less plastic out at the dock, but it is still pushed out there. And the sequence you pasted in the Filament Swap topic (`G1 E-2`, `G1 Z2.92`, `G1 E2`, then the travel) is line for line what I get with "Wall gap" off, so I would check that setting first.

What gave zero on the plates I have: "Wall gap" on, and the prime tower with its ribs and brim at least 2 mm inside the bed on the right and at the back. @Zoe_M, this is the opposite of the "Wall gap off, tower at the edge" advice in the Filament Swap topic: on my example that setting gives 15 of 15. The table is in #1168.

The checker now prints both numbers: https://github.com/DesignMaster-Solutions/u1-dryrun/blob/main/tools/dock_drops.py
`python3 dock_drops.py file.gcode`, and "0 of N" is the safe answer.

What I did not do: slice with your G-code (I compared the text only), and print anything.
